#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
cd "$root"
relative=fixtures/mooneye/manifest.json

describe() {
  local name=$1 file=$2 size digest cr lf
  size=$(wc -c < "$file" | tr -d ' ')
  digest=$(sha256sum "$file" | cut -d ' ' -f 1)
  cr=$(LC_ALL=C tr -cd '\r' < "$file" | wc -c | tr -d ' ')
  lf=$(LC_ALL=C tr -cd '\n' < "$file" | wc -c | tr -d ' ')
  printf '%s size=%s sha256=%s cr=%s lf=%s\n' "$name" "$size" "$digest" "$cr" "$lf"
}

if [[ ${1:-} == --capture ]]; then
  [[ $# == 2 ]] || { echo 'usage: inspect-windows-manifest.sh --capture <evidence-dir>' >&2; exit 2; }
  output=$2
  mkdir -p "$output"
  git show "HEAD:$relative" > "$output/blob.json"
  cp "$relative" "$output/checkout.json"
  cp build/runner-missing-fixture/manifest.json "$output/missing-control.json"
  cp build/runner-bad-digest/manifest.json "$output/digest-control.json"
  {
    printf 'run_id=%s\nevent_sha=%s\ncheckout_head=%s\nblob_oid=%s\n' \
      "${GITHUB_RUN_ID:-unset}" "${GITHUB_SHA:-unset}" "$(git rev-parse HEAD)" \
      "$(git rev-parse "HEAD:$relative")"
    for name in blob checkout missing-control digest-control; do
      describe "$name" "$output/$name.json"
    done
    for name in checkout missing-control digest-control; do
      if cmp -s "$output/blob.json" "$output/$name.json"; then
        printf '%s_equals_blob=yes\n' "$name"
      else
        printf '%s_equals_blob=no\n' "$name"
      fi
    done
  } | tee "$output/report.txt"
  if grep -q '_equals_blob=no' "$output/report.txt"; then
    echo 'Windows manifest bytes differ from the pinned Git blob' >&2
    exit 1
  fi
  exit 0
fi

[[ $# == 0 ]] || { echo 'usage: inspect-windows-manifest.sh' >&2; exit 2; }
command -v gh >/dev/null
command -v jq >/dev/null
head=$(git rev-parse HEAD)
branch=$(git branch --show-current)
run=$(gh run list --workflow ci.yml --branch "$branch" --event push --limit 30 \
  --json databaseId,headSha,status,conclusion | jq -r --arg head "$head" \
  '[.[] | select(.headSha == $head and .status == "completed")] | first | .databaseId // empty')
[[ -n "$run" ]] || { echo "No completed ci.yml push run at HEAD $head" >&2; exit 1; }
evidence=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-windows-manifest.XXXXXXXX")
gh run download "$run" -n windows-manifest-bytes -D "$evidence"
for name in blob checkout missing-control digest-control; do
  [[ -f "$evidence/$name.json" ]] || { echo "Missing $name raw-byte artifact in run $run" >&2; exit 1; }
done
[[ -f "$evidence/report.txt" ]] || { echo "Missing metadata artifact in run $run" >&2; exit 1; }
grep -Fx "checkout_head=$head" "$evidence/report.txt"
grep -Fx "run_id=$run" "$evidence/report.txt"
git show "$head:$relative" | cmp - "$evidence/blob.json"
printf 'Hosted Windows run=%s head=%s evidence=%s\n' "$run" "$head" "$evidence"
cat "$evidence/report.txt"
for name in checkout missing-control digest-control; do
  if cmp -s "$evidence/blob.json" "$evidence/$name.json"; then
    printf '%s: byte-identical to Git blob\n' "$name"
  else
    printf '%s: differs from Git blob\n' "$name"
    cmp "$evidence/blob.json" "$evidence/$name.json" || true
  fi
done
