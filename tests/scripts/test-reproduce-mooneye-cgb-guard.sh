#!/usr/bin/env bash
# Offline check of reproduce-mooneye-cgb.sh --compare (Phase 10 WR-03): a fixture directory without its
# manifest.json must fail before any network fetch, because the manifest is the trust anchor for the
# original_sha256 binding and --compare must never print byte-identical without it.
#
# usage: test-reproduce-mooneye-cgb-guard.sh REPO_ROOT
set -euo pipefail
repo=$(cd "$1" && pwd -P)
script="$repo/tests/scripts/reproduce-mooneye-cgb.sh"
scratch=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-cgb-guard.XXXXXXXX")
trap 'rm -rf -- "$scratch"' EXIT

# A throwaway repository holding only the frozen parent pins the script digest-checks first, and an
# mooneye-cgb fixture directory with no manifest.json.
mkdir -p "$scratch/r/fixtures/mooneye" "$scratch/r/fixtures/mooneye-cgb"
for f in manifest.json headless-report.patch font-source.c; do
  cp "$repo/fixtures/mooneye/$f" "$scratch/r/fixtures/mooneye/$f"
done
git -C "$scratch/r" init -q

set +e
out=$(cd "$scratch/r" && bash "$script" --compare fixtures/mooneye-cgb 2>&1)
rc=$?
set -e
printf '%s\n' "$out"
[[ $rc == 1 ]] || { echo "expected exit 1, got $rc" >&2; exit 1; }
[[ "$out" == *"missing fixture manifest"* ]] || { echo "missing-manifest reason not reported" >&2; exit 1; }
[[ "$out" != *"result=byte-identical"* ]] || { echo "byte-identical printed without a manifest" >&2; exit 1; }
echo "reproduce-mooneye-cgb guard ok"
