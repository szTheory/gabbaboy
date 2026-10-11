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

args=("-DGBB_MODE=$mode" "-DGBB_SOURCE_DIR=$root")
if [[ "$mode" != junit ]]; then
  runner=$(find_tool gabbaboy-runner) || { echo "gabbaboy-runner not found in $build_dir; build first" >&2; exit 2; }
  measure=$(find_tool measure_core) || { echo "measure_core not found in $build_dir; build first" >&2; exit 2; }
  args+=("-DGBB_RUNNER=$runner" "-DGBB_MEASURE=$measure")
else
  args+=("-DGBB_JUNIT=$junit" "-DGBB_INVENTORY=$inventory")
fi

exec "${CMAKE:-cmake}" "${args[@]}" -P "$root/cmake/VerifyDmgBaseline.cmake"
