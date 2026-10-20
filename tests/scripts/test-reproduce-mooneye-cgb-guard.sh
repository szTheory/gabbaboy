#!/usr/bin/env bash
# Offline check of reproduce-mooneye-cgb.sh --compare (Phase 10 WR-03): a fixture directory without its
# manifest.json must fail before any network fetch, because the manifest is the trust anchor for the
# original_sha256 binding and --compare must never print byte-identical without it.
#
# usage: test-reproduce-mooneye-cgb-guard.sh REPO_ROOT
set -euo pipefail
repo=$(cd "$1" && pwd -P)
script=${2:-"$repo/tests/scripts/reproduce-mooneye-cgb.sh"}
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
# Refused paths must not leave directories behind, including through symlinks and .. .
ln -s "$scratch/r" "$scratch/repo-link"
for destination in "$scratch/r/rejected/nested" "$scratch/repo-link/rejected/nested" "$scratch/r/fixtures/../rejected/nested"; do
  set +e
  out=$(cd "$scratch/r" && bash "$script" --build "$destination" 2>&1)
  rc=$?
  set -e
  [[ $rc == 2 && "$out" == *"refusing to write build products"* ]] || {
    echo "in-tree output was not refused: $out" >&2; exit 1;
  }
  [[ ! -e "$scratch/r/rejected" ]] || { echo "refused output created a directory" >&2; exit 1; }
done
# Validate both destinations before creating either, including the evidence override.
set +e
out=$(cd "$scratch/r" && GBB_REPRO_OUTPUT_DIR="$scratch/r/rejected-evidence/nested" bash "$script" --build "$scratch/allowed-output" 2>&1)
rc=$?
set -e
[[ $rc == 2 && "$out" == *"refusing to write build products"* ]] || { echo "evidence override not refused: $out" >&2; exit 1; }
[[ ! -e "$scratch/r/rejected-evidence" && ! -e "$scratch/allowed-output" ]] || { echo "refused evidence path left directories" >&2; exit 1; }
# Default temporary destinations must be validated before mktemp as well.
mkdir -p "$scratch/r/tmp"
for operation in --build --compare; do
  if [[ "$operation" == --build ]]; then
    destination="$scratch/default-output"
  else
    printf '{}\n' > "$scratch/r/fixtures/mooneye-cgb/manifest.json"
    destination=fixtures/mooneye-cgb
  fi
  set +e
  out=$(cd "$scratch/r" && TMPDIR="$scratch/r/tmp" bash "$script" "$operation" "$destination" 2>&1)
  rc=$?
  set -e
  [[ $rc == 2 && "$out" == *"refusing to write build products"* ]] || { echo "in-tree TMPDIR not refused: $out" >&2; exit 1; }
  [[ -z $(ls -A "$scratch/r/tmp") && ! -e "$scratch/default-output" ]] || { echo "refused TMPDIR left directories" >&2; exit 1; }
done
# Valid, not-yet-existing external paths reach the next guard without fetching sources.
set +e
out=$(cd "$scratch/r" && GBB_REPRO_OUTPUT_DIR="$scratch/allowed-evidence/nested" GBB_WLA_ORDERING_STRATEGY=guard-stop bash "$script" --build "$scratch/allowed-output/nested" 2>&1)
rc=$?
set -e
[[ $rc == 2 && "$out" == *"unknown deterministic WLA-DX strategy"* ]] || { echo "valid external paths rejected: $out" >&2; exit 1; }
[[ -d "$scratch/allowed-output/nested" && -d "$scratch/allowed-evidence/nested" ]] || { echo "external destinations not created" >&2; exit 1; }
echo "reproduce-mooneye-cgb guard ok"
