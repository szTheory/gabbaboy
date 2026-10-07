#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

script_dir=$(cd "$(dirname "$0")" && pwd)
repo_root=$(cd "$script_dir/../.." && pwd)
cd "$repo_root"

command -v gh >/dev/null 2>&1 || fail "GitHub CLI is required."
command -v jq >/dev/null 2>&1 || fail "jq is required to inspect exact-revision run evidence."
gh auth status >/dev/null 2>&1 || fail "GitHub CLI authentication is unavailable."

repository=$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null) ||
  fail "The current checkout is not associated with an accessible GitHub repository."
origin=$(git remote get-url origin 2>/dev/null) || fail "No origin remote is configured."
case "$origin" in
  "https://github.com/$repository"|"https://github.com/$repository.git"|"git@github.com:$repository"|"git@github.com:$repository.git"|"ssh://git@github.com/$repository.git") ;;
  *) fail "Origin does not point to the authenticated repository $repository." ;;
esac

pr_json=$(gh pr view --json number,state,url,headRefName,headRefOid 2>/dev/null) ||
  fail "No accessible pull request is open for the current branch."
pr_number=$(jq -r '.number' <<<"$pr_json")
pr_state=$(jq -r '.state' <<<"$pr_json")
pr_url=$(jq -r '.url' <<<"$pr_json")
pr_branch=$(jq -r '.headRefName' <<<"$pr_json")
pr_sha=$(jq -r '.headRefOid' <<<"$pr_json")
local_branch=$(git branch --show-current)
local_sha=$(git rev-parse HEAD)
[ "$pr_state" = OPEN ] || fail "PR #$pr_number is not open."
[ "$local_branch" = "$pr_branch" ] || fail "Current branch $local_branch does not match PR head $pr_branch."
[ "$local_sha" = "$pr_sha" ] || fail "Local HEAD $local_sha differs from PR head $pr_sha."

required_json=$(gh pr checks "$pr_number" --required --json name,bucket 2>/dev/null) ||
  fail "Unable to inspect required PR contexts."
required_count=$(jq 'length' <<<"$required_json")
[ "$required_count" -gt 0 ] || fail "The PR has no required check contexts."
jq -e 'all(.[]; .bucket == "pass")' <<<"$required_json" >/dev/null ||
  fail "At least one required PR context is missing, queued, skipped, cancelled, failed, or stale."
required_names=$(jq -r '.[].name' <<<"$required_json" | sort -u | paste -sd, -)

find_successful_run() {
  local workflow=$1
  local runs
  runs=$(gh run list --workflow "$workflow" --event pull_request --commit "$pr_sha" --limit 100 \
    --json databaseId,workflowName,event,status,conclusion,headSha 2>/dev/null) ||
    fail "Unable to list exact-SHA pull-request runs for $workflow."
  jq -r --arg sha "$pr_sha" --arg workflow "$workflow" \
    '.[] | select(.headSha == $sha and .workflowName == $workflow and .event == "pull_request" and .status == "completed" and .conclusion == "success") | .databaseId' \
    <<<"$runs" | sed -n '1p'
}

assert_run() {
  local run_id=$1
  local workflow=$2
  local required_jobs_json=$3
  local description=$4
  local run_json
  run_json=$(gh run view "$run_id" --json workflowName,headSha,event,conclusion,jobs 2>/dev/null) ||
    fail "Unable to inspect $description run $run_id."
  jq -e --arg sha "$pr_sha" --arg workflow "$workflow" --argjson required "$required_jobs_json" '
    . as $run
    | $run.workflowName == $workflow
      and $run.headSha == $sha
      and $run.event == "pull_request"
      and $run.conclusion == "success"
      and all($required[]; . as $name | any($run.jobs[]; .name == $name and .conclusion == "success"))
  ' <<<"$run_json" >/dev/null ||
    fail "$description run $run_id is stale, incomplete, or missing a successful required job."
  local jobs
  jobs=$(jq -r '[.jobs[] | "\(.name)=\(.conclusion)"] | sort | join(",")' <<<"$run_json")
  printf '%s run=%s workflow=%s jobs=%s\n' "$description" "$run_id" "$workflow" "$jobs"
}

ci_run_id=$(find_successful_run ci)
[ -n "$ci_run_id" ] || fail "No completed successful pull-request CI run exists for $pr_sha."
assert_run "$ci_run_id" ci '["native-linux-x64","native-macos-arm64","native-windows-x64","linux-asan-ubsan","cmake-floor-3.25.3","required-native"]' "CI"

fixture_run_id=$(find_successful_run fixture-repro)
[ -n "$fixture_run_id" ] || fail "No completed successful pull-request fixture-repro run exists for $pr_sha."
assert_run "$fixture_run_id" fixture-repro '["fixture-repro","mooneye-original-repro","mooneye-candidate-repro"]' "Fixture reproduction"

printf 'PASS repository=%s pr=%s source_sha=%s required_contexts=%s ci_run=%s fixture_run=%s pr_url=%s\n' \
  "$repository" "$pr_number" "$pr_sha" "$required_names" "$ci_run_id" "$fixture_run_id" "$pr_url"
