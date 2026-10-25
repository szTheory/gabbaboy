#!/usr/bin/env bash
# One-off Phase 8 differential (D-10): old (5673bed) versus current gabbaboy.c.
# Not a CTest. Usage: run-differential.sh [--exclude-types HEX[,HEX...]]
# Plans 08-02 and 08-03 pass their intentionally new type bytes to --exclude-types.
set -euo pipefail

BASE_REV=5673bed
exclude=""
if [[ "${1:-}" == "--exclude-types" ]]; then
  exclude="${2:?--exclude-types needs a comma-separated hex list}"
elif [[ $# -ne 0 ]]; then
  echo "usage: $0 [--exclude-types HEX[,HEX...]]" >&2
  exit 2
fi

repo_root="$(git rev-parse --show-toplevel)"
here="$repo_root/.planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/differential"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

git -C "$repo_root" show "$BASE_REV:src/core/gabbaboy.c" > "$work/old_core.c"

build() { # name core-source
  cc -std=c17 -O2 -I "$repo_root/include" -DGBB_CORE_SOURCE="\"$2\"" \
     "$here/loader-mapper-diff.c" -o "$work/$1"
}
build old "$work/old_core.c"
build new "$repo_root/src/core/gabbaboy.c"

args=()
if [[ -n "$exclude" ]]; then args=(--exclude-types "$exclude"); fi
# strtok edits its argument, so give each run its own argv copy.
"$work/old" ${args[@]+"${args[@]}"} > "$work/old.txt"
"$work/new" ${args[@]+"${args[@]}"} > "$work/new.txt"

sha() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1"; else shasum -a 256 "$1"; fi | awk '{print $1}'; }
cells="$(awk '/^CELLS /{split($2,a,"=");print a[2]}' "$work/new.txt")"
lines="$(wc -l < "$work/new.txt" | tr -d ' ')"
differences="$(diff "$work/old.txt" "$work/new.txt" | grep -cE '^[<>]' || true)"
echo "cells=$cells lines=$lines old_sha256=$(sha "$work/old.txt") new_sha256=$(sha "$work/new.txt") differences=$differences"
[[ "$differences" -eq 0 ]] || exit 1
