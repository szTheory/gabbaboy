#!/bin/sh
set -eu

fail() {
  printf '%s\n' "ERROR: $*" >&2
  exit 1
}

script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd)
repo_root=$(CDPATH= cd "$script_dir/../.." && pwd)
cd "$repo_root"
umask 077

if ! gh auth status >/dev/null 2>&1; then
  fail "GitHub CLI authentication is unavailable; authenticate with gh and rerun."
fi
if ! command -v cmake >/dev/null 2>&1; then
  fail "CMake is required to verify downloaded preview packages."
fi

repository=$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null) ||
  fail "The current checkout is not associated with an accessible GitHub repository."
origin=$(git remote get-url origin 2>/dev/null) ||
  fail "No origin remote is configured."
case "$origin" in
  "https://github.com/$repository"|"https://github.com/$repository.git"|"git@github.com:$repository"|"git@github.com:$repository.git"|"ssh://git@github.com/$repository.git") ;;
  *) fail "Origin does not point to the authenticated repository $repository." ;;
esac

pr_state=$(gh pr view --json state --jq '.state' 2>/dev/null) ||
  fail "No accessible pull request is open for the current branch."
[ "$pr_state" = OPEN ] || fail "The current pull request is not open."
pr_number=$(gh pr view --json number --jq '.number')
pr_url=$(gh pr view --json url --jq '.url')
pr_branch=$(gh pr view --json headRefName --jq '.headRefName')
pr_base=$(gh pr view --json baseRefName --jq '.baseRefName')
pr_sha=$(gh pr view --json headRefOid --jq '.headRefOid')
local_branch=$(git branch --show-current)
local_sha=$(git rev-parse HEAD)
[ "$local_branch" = "$pr_branch" ] ||
  fail "Current branch $local_branch does not match PR head $pr_branch."
[ "$pr_base" = main ] || fail "PR base must be main; found $pr_base."
[ "$local_sha" = "$pr_sha" ] ||
  fail "Local HEAD $local_sha differs from PR head $pr_sha."

all_required_pass=$(gh pr checks "$pr_number" --required --json name,bucket \
  --jq 'length > 0 and all(.[]; .bucket == "pass")' 2>/dev/null) ||
  fail "Unable to evaluate required PR checks."
[ "$all_required_pass" = true ] ||
  fail "Required PR checks are empty or at least one required context has not passed."
check_names=$(gh pr checks "$pr_number" --required --json name,bucket --jq '.[].name') ||
  fail "Unable to list required PR check contexts."
for required_context in required-native preview-package-smoke; do
  printf '%s\n' "$check_names" | grep -Fxq "$required_context" ||
    fail "Required PR context is missing: $required_context."
done
fixture_contexts=$(printf '%s\n' "$check_names" | awk 'index($0, "fixture-repro") && $0 ~ /fixture-repro$/ { print }' | sort -u)
fixture_context_count=$(printf '%s\n' "$fixture_contexts" | awk 'NF { count++ } END { print count + 0 }')
[ "$fixture_context_count" -eq 1 ] ||
  fail "Could not resolve exactly one required fixture-repro status context from observed PR checks."
fixture_context=$(printf '%s\n' "$fixture_contexts" | sed -n '1p')

find_successful_run() {
  find_workflow=$1
  filter='.[] | select(.headSha == "'"$pr_sha"'" and .workflowName == "'"$find_workflow"'" and .event == "pull_request" and .status == "completed" and .conclusion == "success") | .databaseId'
  gh run list --commit "$pr_sha" --limit 100 \
    --json databaseId,workflowName,event,status,conclusion,headSha \
    --jq "$filter" | sed -n '1p'
}

assert_run() {
  assert_id=$1
  assert_description=$2
  assert_filter=$3
  gh run view "$assert_id" --exit-status >/dev/null 2>&1 ||
    fail "$assert_description run $assert_id did not complete successfully."
  assert_result=$(gh run view "$assert_id" \
    --json headSha,event,conclusion,jobs --jq "$assert_filter") ||
    fail "Could not inspect $assert_description run $assert_id."
  [ "$assert_result" = true ] ||
    fail "$assert_description run $assert_id is stale or missing its required successful job."
}

ci_run_id=$(find_successful_run ci)
[ -n "$ci_run_id" ] || fail "No completed successful pull-request CI run exists for $pr_sha."
assert_run "$ci_run_id" "CI" '.headSha == "'"$pr_sha"'" and .event == "pull_request" and .conclusion == "success" and any(.jobs[]; .name == "required-native" and .conclusion == "success")'

fixture_run_id=$(find_successful_run fixture-repro)
[ -n "$fixture_run_id" ] || fail "No completed successful pull-request fixture-repro run exists for $pr_sha."
assert_run "$fixture_run_id" "Fixture reproduction" '.headSha == "'"$pr_sha"'" and .event == "pull_request" and .conclusion == "success" and any(.jobs[]; .name == "fixture-repro" and .conclusion == "success")'

preview_run_id=$(find_successful_run preview-package-smoke)
[ -n "$preview_run_id" ] || fail "No completed successful pull-request preview-package-smoke run exists for $pr_sha."
assert_run "$preview_run_id" "Preview package" '.headSha == "'"$pr_sha"'" and .event == "pull_request" and .conclusion == "success" and any(.jobs[]; .name == "installed-package-smoke-linux-x64" and .conclusion == "success") and any(.jobs[]; .name == "installed-package-smoke-macos-arm64" and .conclusion == "success") and any(.jobs[]; .name == "preview-package-smoke" and .conclusion == "success")'

retention_days=$(awk '$1 == "PREVIEW_RETENTION_DAYS:" { print $2; exit }' .github/workflows/preview.yml)
[ -n "$retention_days" ] || fail "Could not read configured PREVIEW_RETENTION_DAYS from preview.yml."
artifact_api="repos/$repository/actions/runs/$preview_run_id/artifacts"
evidence_root="${TMPDIR:-/tmp}/gabbaboy-pr-evidence-$$"
mkdir -p "$evidence_root"
cleanup() {
  rm -rf "$evidence_root"
}
trap cleanup 0
trap 'exit 1' HUP INT TERM

verify_artifact() {
  artifact_name=$1
  package_name=$2
  artifact_count=$(gh api "$artifact_api" --jq '[.artifacts[] | select(.name == "'"$artifact_name"'")] | length') ||
    fail "Could not inspect artifact API entry for $artifact_name."
  [ "$artifact_count" = 1 ] || fail "Expected one API artifact named $artifact_name; found $artifact_count."
  artifact_digest=$(gh api "$artifact_api" --jq '.artifacts[] | select(.name == "'"$artifact_name"'") | .digest') ||
    fail "Could not read artifact API digest for $artifact_name."
  artifact_created=$(gh api "$artifact_api" --jq '.artifacts[] | select(.name == "'"$artifact_name"'") | .created_at') ||
    fail "Could not read artifact API creation time for $artifact_name."
  artifact_expires=$(gh api "$artifact_api" --jq '.artifacts[] | select(.name == "'"$artifact_name"'") | .expires_at') ||
    fail "Could not read artifact API expiry for $artifact_name."
  artifact_expired=$(gh api "$artifact_api" --jq '.artifacts[] | select(.name == "'"$artifact_name"'") | .expired') ||
    fail "Could not read artifact API expiry state for $artifact_name."
  [ -n "$artifact_digest" ] && [ "$artifact_digest" != null ] ||
    fail "Artifact API digest is empty for $artifact_name."
  [ -n "$artifact_created" ] && [ "$artifact_created" != null ] ||
    fail "Artifact API creation time is empty for $artifact_name."
  [ -n "$artifact_expires" ] && [ "$artifact_expires" != null ] ||
    fail "Artifact API expiry is empty for $artifact_name."
  [ "$artifact_expired" = false ] || fail "Artifact $artifact_name is expired."

  artifact_dir="$evidence_root/$artifact_name"
  mkdir -p "$artifact_dir"
  gh run download "$preview_run_id" --name "$artifact_name" --dir "$artifact_dir" >/dev/null ||
    fail "Could not download exact-run artifact $artifact_name."
  sidecar="$artifact_dir/artifact-metadata.json"
  package_file="$artifact_dir/$package_name"
  [ -f "$sidecar" ] || fail "Downloaded artifact $artifact_name has no artifact-metadata.json."
  [ -f "$package_file" ] || fail "Downloaded artifact $artifact_name has no $package_name."

  package_extract="$artifact_dir/extracted"
  mkdir -p "$package_extract"
  cmake -E tar tzf "$package_file" | awk '
    /^\// { unsafe = 1 }
    {
      count = split($0, parts, "/")
      for (i = 1; i <= count; i++) if (parts[i] == "..") unsafe = 1
    }
    END { exit unsafe }
  ' || fail "Package $package_name contains an unsafe archive path."
  (
    cd "$package_extract"
    cmake -E tar xzf "$package_file"
  ) || fail "Could not extract package $package_name."
  extracted_prefix="$package_extract/installed-prefix"
  [ -d "$extracted_prefix" ] || fail "Extracted package $package_name has no installed-prefix tree."
  [ -f "$extracted_prefix/include/gabbaboy/gabbaboy.h" ] || fail "Extracted package $package_name is missing its public header."
  [ -x "$extracted_prefix/bin/gabbaboy-runner" ] || fail "Extracted package $package_name is missing an executable runner."
  [ -f "$extracted_prefix/share/gabbaboy/fixtures/tracer/tracer.gb" ] || fail "Extracted package $package_name is missing the tracer fixture."
  cmake \
    -DGBB_SIDECAR_FILE="$sidecar" \
    -DGBB_PACKAGE_FILE="$package_file" \
    -DGBB_EXPECTED_SOURCE_SHA="$pr_sha" \
    -DGBB_EXPECTED_RETENTION_DAYS="$retention_days" \
    -P cmake/VerifyArtifactSidecar.cmake ||
    fail "Sidecar validation failed for exact-run artifact $artifact_name."

  package_sha=$(cmake -E sha256sum "$package_file" | awk '{ print $1; exit }')
  printf 'artifact=%s api_digest=%s created_at=%s expires_at=%s package_sha256=%s\n' \
    "$artifact_name" "$artifact_digest" "$artifact_created" "$artifact_expires" "$package_sha"
}

verify_artifact preview-linux-x64 gabbaboy-preview-linux-x64.tar.gz
verify_artifact preview-macos-arm64 gabbaboy-preview-macos-arm64.tar.gz

printf 'PASS repository=%s pr=%s source_sha=%s ci_run=%s fixture_run=%s fixture_context=%s preview_run=%s pr_url=%s\n' \
  "$repository" "$pr_number" "$pr_sha" "$ci_run_id" "$fixture_run_id" \
  "$fixture_context" "$preview_run_id" "$pr_url"
