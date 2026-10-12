#!/usr/bin/env bash
# Reproduce the project-authored CGB banking ROMs (banking-cgb.gb, banking-dmg.gb) with the pinned RGBDS.
# Normal build and test runs consume the checked-in, digest-verified bytes.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(cd "$script_dir/../.." && pwd -P)
cd "$repo_root"

work_dir=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-cgb-banking.XXXXXXXX")
cleanup() { rm -rf -- "$work_dir"; }
trap cleanup EXIT

for tool in rgbasm rgblink rgbfix; do
  command -v "$tool" >/dev/null || {
    echo "required RGBDS tool is not installed: $tool (expected v1.0.1)" >&2
    exit 1
  }
  version_line=$("$tool" --version | sed -n '1p')
  [[ "$version_line" == "$tool v1.0.1" ]] || {
    echo "$tool version mismatch: expected v1.0.1, got ${version_line:-<empty>}" >&2
    exit 1
  }
done

rgbasm -o "$work_dir/banking.o" fixtures/cgb-banking/banking.asm
rgblink -n "$work_dir/banking.sym" -o "$work_dir/banking.gb" "$work_dir/banking.o"
cp "$work_dir/banking.gb" "$work_dir/banking-cgb.gb"
cp "$work_dir/banking.gb" "$work_dir/banking-dmg.gb"
rgbfix -c -v -p 0 "$work_dir/banking-cgb.gb"
rgbfix -v -p 0 "$work_dir/banking-dmg.gb"

python3 -I - "$repo_root" "$work_dir" <<'PY'
import hashlib
import json
import os
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
work = pathlib.Path(sys.argv[2])
fixture = root / 'fixtures/cgb-banking'
manifest = json.loads((fixture / 'manifest.json').read_text())
reference = json.loads((root / 'fixtures/mbc5-banking/manifest.json').read_text())

def fail(message):
    raise SystemExit(message)

build = manifest.get('build', {})
ref = reference.get('build', {})
for key in ('assembler', 'version', 'archive', 'archive_sha256', 'ci_archive', 'ci_archive_sha256'):
    if build.get(key) != ref.get(key):
        fail(f'CGB banking build pin {key} differs from the established MBC5 banking pin')
if build.get('version') != '1.0.1':
    fail('manifest must pin RGBDS v1.0.1')
if manifest.get('id') != 'original-cgb-banking' or manifest.get('source') != 'banking.asm':
    fail('manifest does not identify the original CGB banking fixture source')
if manifest.get('source_identity') != 'Original GabbaBoy project-authored assembly':
    fail('fixture source identity is not project-owned')
if not manifest.get('license', '').startswith('MIT;') or not (fixture / 'LICENSE.txt').is_file():
    fail('fixture redistribution notice or MIT license declaration is missing')
if 'not hardware evidence' not in manifest.get('evidence_class', ''):
    fail('fixture evidence class must exclude hardware proof')
if not manifest.get('protocol') or not manifest.get('scope_limits'):
    fail('fixture protocol and scope limits must be recorded')
if 'rgbfix -c -v -p 0' not in build.get('recipe', '') or 'rgbfix -v -p 0' not in build.get('recipe', ''):
    fail('fixture build recipe is missing the two rgbfix invocations')

source_sha = hashlib.sha256((fixture / manifest['source']).read_bytes()).hexdigest()
if source_sha != manifest.get('source_sha256'):
    fail(f'assembly source SHA-256 mismatch: manifest={manifest.get("source_sha256")} actual={source_sha}')

entries = manifest.get('fixtures', [])
if [e.get('file') for e in entries] != ['banking-cgb.gb', 'banking-dmg.gb']:
    fail('manifest fixtures[] must list banking-cgb.gb then banking-dmg.gb')
cgb_flag = {'banking-cgb.gb': 0x80, 'banking-dmg.gb': 0x00}
for entry in entries:
    name = entry['file']
    rebuilt = (work / name).read_bytes()
    checked_in = (fixture / name).read_bytes()
    actual_sha = hashlib.sha256(rebuilt).hexdigest()
    if entry.get('size_bytes') != 32768 or len(rebuilt) != 32768 or len(checked_in) != 32768:
        fail(f'{name}: rebuilt and checked-in ROMs must be exactly 32 KiB')
    if actual_sha != entry.get('sha256'):
        fail(f'{name}: rebuilt SHA-256 mismatch: manifest={entry.get("sha256")} actual={actual_sha}')
    if hashlib.sha256(checked_in).hexdigest() != entry['sha256'] or rebuilt != checked_in:
        fail(f'{name}: rebuilt ROM differs from the checked-in bytes or manifest digest')
    if rebuilt[0x143] != cgb_flag[name] or rebuilt[0x147] != 0x00 or rebuilt[0x148] != 0x00:
        fail(f'{name}: header is not the expected ROM-only 32 KiB image with CGB flag {cgb_flag[name]:#04x}')

# The negative-control patch offsets recorded in the manifest must match the linker symbols.
symbols = {}
for line in (work / 'banking.sym').read_text().splitlines():
    if line and not line.startswith(';'):
        address, name = line.split(' ', 1)
        symbols[name] = int(address.split(':')[1], 16)
offsets = manifest['protocol']['patch_offsets']
if int(offsets['expect_vbk0_compare'], 16) != symbols['Start.expectVbk0']:
    fail('manifest expect_vbk0_compare offset differs from the Start.expectVbk0 symbol')
if int(offsets['svbk_write_markers'], 16) != symbols['Start.svbkWriteMarkers']:
    fail('manifest svbk_write_markers offset differs from the Start.svbkWriteMarkers symbol')

archive_path = os.environ.get('GBB_RGBDS_ARCHIVE')
if archive_path:
    archive = pathlib.Path(archive_path)
    if not archive.is_file():
        fail('GBB_RGBDS_ARCHIVE does not name a regular file')
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    if archive_sha not in {build['archive_sha256'], build['ci_archive_sha256']}:
        fail(f'RGBDS archive SHA-256 is not pinned: {archive_sha}')
    expected_archive_sha = os.environ.get('GBB_RGBDS_ARCHIVE_SHA256')
    if expected_archive_sha and expected_archive_sha != archive_sha:
        fail('downloaded RGBDS archive digest differs from the supplied pin')

print(f"rgbds={build['version']}")
print(f"source_sha256={source_sha}")
for entry in entries:
    print(f"rom={entry['file']} size_bytes={entry['size_bytes']} sha256={entry['sha256']}")
print('result=byte-identical roms=2')
PY
