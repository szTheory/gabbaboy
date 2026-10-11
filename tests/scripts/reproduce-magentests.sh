#!/usr/bin/env bash
# Rebuild the three MagenTests mbc_oob_sram ROMs at the pinned upstream commit with RGBDS v0.6.1 and
# compare the bytes with the committed release ROMs (Phase 9, D-04). Never copies rebuilt bytes over
# committed fixtures.
#
#   --self-check   offline: manifest, SOURCES.md pins and committed digests (default)
#   --compare      networked: rebuild with rgbasm/rgblink/rgbfix v0.6.1 on PATH and compare
#
# Prints self-check=pass, result=byte-identical, or result=differs <file> <rebuilt> <committed>.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(cd "$script_dir/../.." && pwd -P)
fixture="$repo_root/fixtures/magentests"

upstream_url=https://github.com/alloncm/MagenTests.git
upstream_commit=3f9c090f16e5a721db776febb9ba7d773e1c819c
hardware_url=https://github.com/gbdev/hardware.inc.git
hardware_commit=21ef22d01ac55151160f3d98110c2da8846a96b2
rgbds_version=v0.6.1

mode=${1:---self-check}
work_dir=

self_check() {
  python3 -I - "$fixture" "$upstream_commit" "$hardware_commit" <<'PY'
import hashlib
import json
import pathlib
import re
import sys

fixture = pathlib.Path(sys.argv[1])
commit, hardware = sys.argv[2:4]

def fail(message):
    raise SystemExit('self-check failed: ' + message)

manifest = json.loads((fixture / 'manifest.json').read_text())
if manifest['suite'].get('revision') != commit:
    fail('manifest revision differs from the pin')
entries = manifest.get('fixtures', [])
if len(entries) != 3:
    fail('expected three MagenTests fixtures')
for entry in entries:
    data = (fixture / entry['file']).read_bytes()
    if len(data) != entry['size_bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
        fail('digest mismatch for ' + entry['file'])
sources = (fixture / 'SOURCES.md').read_text()
for needle in (commit, hardware[:7], 'RGBDS v0.6.1'):
    if needle not in sources:
        fail('SOURCES.md is missing ' + needle)
if not re.search(r'rgbds-0\.6\.1-linux-x86_64\.tar\.xz sha256 [0-9a-f]{64}', sources):
    fail('SOURCES.md is missing the RGBDS 0.6.1 archive pin')
print('self-check=pass')
PY
}

compare() {
  local tool version_line name
  for tool in rgbasm rgblink rgbfix; do
    command -v "$tool" >/dev/null || {
      echo "required RGBDS tool is not installed: $tool (expected $rgbds_version)" >&2
      exit 1
    }
    version_line=$("$tool" --version | sed -n '1p')
    [[ "$version_line" == *"$rgbds_version" ]] || {
      echo "$tool version mismatch: expected $rgbds_version, got ${version_line:-<empty>}" >&2
      exit 1
    }
  done
  work_dir=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-magentests.XXXXXXXX")
  trap '[[ -z "$work_dir" ]] || rm -rf -- "$work_dir"' EXIT
  git -C "$work_dir" init -q src
  git -C "$work_dir/src" fetch -q --depth 1 "$upstream_url" "$upstream_commit"
  git -C "$work_dir/src" checkout -q FETCH_HEAD
  [[ "$(git -C "$work_dir/src" rev-parse HEAD)" == "$upstream_commit" ]] || {
    echo "fetched upstream commit differs from the pin" >&2
    exit 1
  }
  # The upstream Makefile includes hardware.inc/ (a submodule path) via -i hardware.inc/.
  git -C "$work_dir" init -q hw
  git -C "$work_dir/hw" fetch -q --depth 1 "$hardware_url" "$hardware_commit"
  git -C "$work_dir/hw" checkout -q FETCH_HEAD
  [[ "$(git -C "$work_dir/hw" rev-parse HEAD)" == "$hardware_commit" ]] || {
    echo "fetched hardware.inc commit differs from the pin" >&2
    exit 1
  }
  rm -rf -- "$work_dir/src/hardware.inc"
  mv "$work_dir/hw" "$work_dir/src/hardware.inc"
  # Upstream Makefile create_target recipe: ASMFLAGS=-L, FIXFLAGS=-v -p 0, COLORCOMP.
  (
    cd "$work_dir/src"
    mkdir -p build
    while read -r name mbc; do
      rgbasm -L -i src/mbc_oob_sram -i hardware.inc/ -o "build/$name.o" src/mbc_oob_sram/main.asm
      rgblink -o "build/$name.gbc" "build/$name.o"
      rgbfix -v -p 0 --color-compatible --mbc-type "$mbc" --ram-size 2 "build/$name.gbc"
    done <<'LIST'
mbc_oob_sram_mbc1 MBC1+RAM
mbc_oob_sram_mbc3 MBC3+RAM
mbc_oob_sram_mbc5 MBC5+RAM
LIST
  )
  python3 -I - "$fixture" "$work_dir/src/build" <<'PY'
import hashlib
import pathlib
import sys

fixture = pathlib.Path(sys.argv[1])
build = pathlib.Path(sys.argv[2])
bad = False
for name in ('mbc_oob_sram_mbc1.gbc', 'mbc_oob_sram_mbc3.gbc', 'mbc_oob_sram_mbc5.gbc'):
    committed = (fixture / name).read_bytes()
    rebuilt = (build / name).read_bytes()
    if committed != rebuilt:
        print('result=differs %s %s %s' % (
            name, hashlib.sha256(rebuilt).hexdigest(), hashlib.sha256(committed).hexdigest()))
        bad = True
if bad:
    raise SystemExit(1)
print('result=byte-identical')
PY
}

case "$mode" in
  --self-check) self_check ;;
  --compare) self_check >/dev/null; compare ;;
  *) echo "usage: $0 [--self-check|--compare]" >&2; exit 2 ;;
esac
