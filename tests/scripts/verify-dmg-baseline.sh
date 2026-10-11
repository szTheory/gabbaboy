#!/usr/bin/env bash
# Single entry point for the EVID-02 DMG baseline check (D-35). It only locates the built tools and
# hands everything to cmake/VerifyDmgBaseline.cmake through `cmake -P`, which keeps the comparison
# logic in one portable place; there is no comparison logic here.
#
#   verify-dmg-baseline.sh [--build-dir DIR]                       check the frozen ledger
#   verify-dmg-baseline.sh [--build-dir DIR] --print-candidate     print a candidate ledger to stdout
#   verify-dmg-baseline.sh --junit FILE --inventory core|player    check a JUnit report's inventory
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
build_dir="$root/build"
mode=check
junit=""
inventory=""

usage() {
  echo "Usage: $0 [--build-dir DIR] [--print-candidate | --junit FILE --inventory core|player]" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --build-dir) [[ $# -ge 2 ]] || usage; build_dir=$2; shift 2 ;;
    --print-candidate) mode=print-candidate; shift ;;
    --junit) [[ $# -ge 2 ]] || usage; mode=junit; junit=$2; shift 2 ;;
    --inventory) [[ $# -ge 2 ]] || usage; inventory=$2; shift 2 ;;
    *) usage ;;
  esac
done
if [[ "$mode" == junit && -z "$inventory" ]]; then usage; fi

find_tool() {
  local name=$1 candidate
  for candidate in "$build_dir/$name" "$build_dir/$name.exe"; do
    if [[ -f "$candidate" ]]; then echo "$candidate"; return 0; fi
  done
  return 1
}

# Git Bash on Windows hands native cmake MSYS-style paths (/d/a/...) that cmake's EXISTS cannot see,
# so convert every path cmake receives to the mixed C:/... form there. Elsewhere this is a no-op.
native_path() {
  if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s\n' "$1"; fi
}

args=("-DGBB_MODE=$mode" "-DGBB_SOURCE_DIR=$(native_path "$root")")
if [[ "$mode" != junit ]]; then
  runner=$(find_tool gabbaboy-runner) || { echo "gabbaboy-runner not found in $build_dir; build first" >&2; exit 2; }
  measure=$(find_tool measure_core) || { echo "measure_core not found in $build_dir; build first" >&2; exit 2; }
  args+=("-DGBB_RUNNER=$(native_path "$runner")" "-DGBB_MEASURE=$(native_path "$measure")")
else
  args+=("-DGBB_JUNIT=$(native_path "$junit")" "-DGBB_INVENTORY=$inventory")
fi

exec "${CMAKE:-cmake}" "${args[@]}" -P "$(native_path "$root")/cmake/VerifyDmgBaseline.cmake"
