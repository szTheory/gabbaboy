#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "Usage: $0 <junit-report> <expected-tests-file> [--core-only|--installed]" >&2
  exit 2
fi

report=$1
expected_file=$2
inventory=${3:---core-only}
[[ -s "$report" ]] || { echo "Missing or empty CTest report: $report" >&2; exit 1; }
[[ -s "$expected_file" ]] || { echo "Missing or empty expected inventory: $expected_file" >&2; exit 1; }

if grep -Eq '<skipped([[:space:]>]|/)' "$report"; then
  echo "CTest report contains skipped cases" >&2
  exit 1
fi

expected=$(mktemp)
actual=$(mktemp)
trap 'rm -f "$expected" "$actual"' EXIT
awk '{ sub(/\r$/, ""); print }' "$expected_file" > "$expected"
if [[ "$inventory" == "--core-only" ]]; then
  sed -i.bak '/^installed_/d' "$expected"
  rm -f "$expected.bak"
elif [[ "$inventory" != "--installed" ]]; then
  echo "Unknown inventory mode: $inventory" >&2
  exit 2
fi

sed -nE 's/.*<testcase[^>]*name="([^"]+)".*/\1/p' "$report" | LC_ALL=C sort > "$actual"
LC_ALL=C sort -o "$expected" "$expected"
if ! diff -u "$expected" "$actual"; then
  echo "Executed CTest inventory differs from the required inventory" >&2
  exit 1
fi

echo "Verified $(wc -l < "$actual" | tr -d ' ') executed CTest cases; none skipped."
