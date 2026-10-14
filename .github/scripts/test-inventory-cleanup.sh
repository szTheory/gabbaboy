#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <verify-test-inventory.sh>" >&2
  exit 2
fi

source_script=$1
source_script="$(cd -- "$(dirname -- "$source_script")" && pwd)/$(basename -- "$source_script")"
scratch=$(mktemp -d "${TMPDIR:-/tmp}/gbb-inventory-cleanup.XXXXXX")
trap 'rm -rf -- "$scratch"' EXIT

marker="$scratch/injected"
evil_tmpdir="${scratch}/prefix' \$(touch ${marker}) 'suffix"
mkdir -p "$scratch/prefix" "$evil_tmpdir"

if TMPDIR="$evil_tmpdir" bash "$source_script" --self-test-core > "$scratch/fixed.log" 2>&1; then
  fixed_status=0
else
  fixed_status=$?
fi
if [[ $fixed_status -ne 0 ]]; then
  cat "$scratch/fixed.log" >&2
  echo "inventory self-test failed under a hostile TMPDIR (exit $fixed_status)" >&2
  exit 1
fi
if [[ -e "$marker" ]]; then
  echo 'fixed inventory cleanup executed the TMPDIR injection marker' >&2
  exit 1
fi
if compgen -G "$evil_tmpdir/*" >/dev/null; then
  echo 'fixed inventory cleanup left its scratch directory behind' >&2
  exit 1
fi

mutant_script="$scratch/verify-test-inventory-mutant.sh"
sed "s|^  trap 'rm -rf -- \"\$inventory_selftest_dir\"' EXIT$|  trap \"rm -rf -- '\$inventory_selftest_dir'\" EXIT|" \
  "$source_script" > "$mutant_script"
if cmp -s "$source_script" "$mutant_script"; then
  echo 'could not find the fixed inventory EXIT trap to build the negative control' >&2
  exit 1
fi
mkdir -p "$scratch/prefix"

if TMPDIR="$evil_tmpdir" bash -x "$mutant_script" --self-test-core > "$scratch/mutant.log" 2>&1; then
  mutant_status=0
else
  mutant_status=$?
fi
if [[ ! -e "$marker" ]]; then
  echo 'unsafe-trap negative control did not execute its benign marker payload' >&2
  cat "$scratch/mutant.log" >&2
  exit 1
fi
if ! compgen -G "$evil_tmpdir/*" >/dev/null; then
  echo 'unsafe-trap negative control unexpectedly cleaned the injected scratch path' >&2
  exit 1
fi

echo "inventory cleanup trap regression passed; fixed_status=$fixed_status unsafe_mutant_status=$mutant_status marker_control=detected"
