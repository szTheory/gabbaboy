#!/usr/bin/env bash
# Rebuild rtc3test at the pinned upstream commit with RGBDS v0.4.2 and compare the bytes with the
# committed release ROM (Phase 9, D-11). Never copies rebuilt bytes over committed fixtures.
#
#   --self-check   offline: manifest, SOURCES.md pins and committed digests (default)
#   --compare      networked: rebuild with rgbasm/rgblink/rgbfix v0.4.2 on PATH and compare
#
# Prints self-check=pass, result=byte-identical, or result=differs <file> <rebuilt> <committed>.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(cd "$script_dir/../.." && pwd -P)
fixture="$repo_root/fixtures/rtc3test"

upstream_url=https://github.com/aaaaaa123456789/rtc3test.git
upstream_commit=80ae792bf1b3c3387929b912e6df001af3511e24
rgbds_version=v0.4.2
rgbds_commit=ede982b50a68a6253ffbab17dc4184710b08032f
rom_sha256=a271013fb37ea1d927b854798401320b220d57abb3ca77f3d318ceb8a9def30d

mode=${1:---self-check}
work_dir=

self_check() {
  python3 -I - "$fixture" "$upstream_commit" "$rgbds_commit" "$rom_sha256" <<'PY'
import hashlib
import json
import pathlib
import sys

fixture = pathlib.Path(sys.argv[1])
commit, rgbds_commit, rom_sha = sys.argv[2:5]

def fail(message):
    raise SystemExit('self-check failed: ' + message)

manifest = json.loads((fixture / 'manifest.json').read_text())
if manifest['suite'].get('revision') != commit or manifest['suite'].get('release') != 'v004':
    fail('manifest revision or release differs from the pin')
entries = manifest.get('fixtures', [])
if not entries:
    fail('manifest has no fixtures')
for entry in entries:
    data = (fixture / entry['file']).read_bytes()
    if len(data) != entry['size_bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
        fail('digest mismatch for ' + entry['file'])
rom = (fixture / 'rtc3test.gb').read_bytes()
if hashlib.sha256(rom).hexdigest() != rom_sha or len(rom) != 32768 or rom[0x147:0x14a] != bytes([0x0f, 0, 0]):
    fail('committed ROM identity or header differs')
sources = (fixture / 'SOURCES.md').read_text()
for needle in (commit, rgbds_commit, 'RGBDS v0.4.2', rom_sha):
    if needle not in sources:
        fail('SOURCES.md is missing ' + needle)
print('self-check=pass')
PY
}

compare() {
  local tool version_line
  for tool in rgbasm rgblink rgbfix; do
    command -v "$tool" >/dev/null || {
      echo "required RGBDS tool is not installed: $tool (expected $rgbds_version)" >&2
      exit 1
    }
    version_line=$("$tool" --version | sed -n '1p')
    # A source build from a shallow checkout reports the abbreviated commit instead of the tag.
    [[ "$version_line" == *"$rgbds_version" || "$version_line" == *" ${rgbds_commit:0:7}" ]] || {
      echo "$tool version mismatch: expected $rgbds_version, got ${version_line:-<empty>}" >&2
      exit 1
    }
  done
  work_dir=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-rtc3test.XXXXXXXX")
  trap '[[ -z "$work_dir" ]] || rm -rf -- "$work_dir"' EXIT
  git -C "$work_dir" init -q src
  git -C "$work_dir/src" fetch -q --depth 1 "$upstream_url" "$upstream_commit"
  git -C "$work_dir/src" checkout -q FETCH_HEAD
  [[ "$(git -C "$work_dir/src" rev-parse HEAD)" == "$upstream_commit" ]] || {
    echo "fetched upstream commit differs from the pin" >&2
    exit 1
  }
  # Upstream Makefile recipe, spelled out so the flags are visible and pinned here.
  (
    cd "$work_dir/src/src"
    rgbasm -E -Wno-truncation -Wextra -Wshift-amount -p 0xff -h -o ../rtc3test.o ../src/rom.asm
  )
  (
    cd "$work_dir/src"
    rgblink -m rtc3test.map -n rtc3test.sym -o rtc3test.gb -p 0xff rtc3test.o
    rgbfix -c -i RTC3 -j -k XX -m 0x0f -n 1 -p 0xff -r 0 -t MBC3RTCTEST -v rtc3test.gb
  )
  python3 -I - "$fixture/rtc3test.gb" "$work_dir/src/rtc3test.gb" <<'PY'
import hashlib
import pathlib
import sys

committed = pathlib.Path(sys.argv[1]).read_bytes()
rebuilt = pathlib.Path(sys.argv[2]).read_bytes()
if committed == rebuilt:
    print('result=byte-identical')
else:
    print('result=differs rtc3test.gb %s %s' % (
        hashlib.sha256(rebuilt).hexdigest(), hashlib.sha256(committed).hexdigest()))
    raise SystemExit(1)
PY
}

case "$mode" in
  --self-check) self_check ;;
  --compare) self_check >/dev/null; compare ;;
  *) echo "usage: $0 [--self-check|--compare]" >&2; exit 2 ;;
esac
