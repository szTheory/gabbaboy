#!/usr/bin/env bash
# Reproduce the project-authored MBC1 continuation ROM with the pinned RGBDS.
# Normal build and test runs consume the checked-in, digest-verified bytes.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(cd "$script_dir/../.." && pwd -P)
cd "$repo_root"

work_dir=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-mbc1-continuation.XXXXXXXX")
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

rgbasm -o "$work_dir/continuation.o" fixtures/mbc1-continuation/continuation.asm
rgblink -o "$work_dir/continuation.gb" "$work_dir/continuation.o"
rgbfix -f hg -p 0 -m 3 -r 2 "$work_dir/continuation.gb"

python3 - "$repo_root" "$work_dir/continuation.gb" <<'PY'
import hashlib
import json
import os
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
rebuilt_path = pathlib.Path(sys.argv[2])
fixture = root / 'fixtures/mbc1-continuation'
manifest = json.loads((fixture / 'manifest.json').read_text())
tracer = json.loads((root / 'fixtures/tracer/manifest.json').read_text())
visible = json.loads((root / 'fixtures/visible-demo/manifest.json').read_text())

def fail(message):
    raise SystemExit(message)

build = manifest.get('build', {})
for other in (tracer.get('build', {}), visible.get('build', {})):
    if build.get('version') != other.get('version'):
        fail('continuation fixture RGBDS version differs from the established v1.0.1 pin')
    if (build.get('archive'), build.get('archive_sha256')) != (
            other.get('archive'), other.get('archive_sha256')):
        fail('continuation fixture macOS RGBDS archive differs from the established pin')
if manifest.get('id') != 'original-mbc1-battery-continuation':
    fail('manifest does not identify the original MBC1 continuation fixture')
if manifest.get('source') != 'continuation.asm' or manifest.get('rom') != 'continuation.gb':
    fail('manifest source and ROM must stay within the fixture directory')
if manifest.get('source_identity') != 'Original GabbaBoy project-authored assembly':
    fail('fixture source identity is not project-owned')
if not manifest.get('license', '').startswith('MIT;') or not (fixture / 'LICENSE.txt').is_file():
    fail('fixture redistribution notice or MIT license declaration is missing')
if build.get('assembler') != 'RGBDS' or build.get('version') != '1.0.1':
    fail('manifest must pin RGBDS v1.0.1')
if build.get('ci_archive') != 'rgbds-linux-x86_64.tar.xz' or build.get('ci_archive_sha256') != (
        '80a5cad8dae27e24e46a93041352c47cadbc165103983f41c2b3082c42f6dad9'):
    fail('Linux RGBDS archive name/digest differs from the reviewed v1.0.1 pin')
if build.get('recipe') != (
        'rgbasm -o <work>/continuation.o fixtures/mbc1-continuation/continuation.asm && '
        'rgblink -o <work>/continuation.gb <work>/continuation.o && '
        'rgbfix -f hg -p 0 -m 3 -r 2 <work>/continuation.gb'):
    fail('fixture build recipe is missing or differs from the executed command')
if manifest.get('profile', {}).get('name') != 'DMG-CPU-B' or 'not physical hardware evidence' not in (
        manifest.get('profile', {}).get('applicability', '')):
    fail('fixture applicability must name the bootless profile and exclude hardware proof')
if not manifest.get('protocol') or not manifest.get('scope_limits'):
    fail('fixture protocol and scope limits must be recorded')
cartridge = manifest.get('cartridge', {})
if cartridge.get('type') != '0x03 (MBC1 + RAM + battery)' or cartridge.get('ram_size_code') != '0x02 (8 KiB)':
    fail('fixture must declare the supported type $03 / 8 KiB battery cartridge')

source_bytes = (fixture / manifest['source']).read_bytes()
source_sha = hashlib.sha256(source_bytes).hexdigest()
if source_sha != manifest.get('source_sha256'):
    fail(f'assembly source SHA-256 mismatch: manifest={manifest.get("source_sha256")} actual={source_sha}')
rebuilt = rebuilt_path.read_bytes()
checked_in = (fixture / manifest['rom']).read_bytes()
actual_sha = hashlib.sha256(rebuilt).hexdigest()
if manifest.get('size_bytes') != 32768 or len(rebuilt) != 32768 or len(checked_in) != 32768:
    fail('rebuilt and checked-in continuation ROMs must be exactly 32 KiB')
if actual_sha != manifest.get('sha256'):
    fail(f'rebuilt ROM SHA-256 mismatch: manifest={manifest.get("sha256")} actual={actual_sha}')
if hashlib.sha256(checked_in).hexdigest() != manifest.get('sha256') or rebuilt != checked_in:
    fail('rebuilt ROM differs from the checked-in bytes or manifest digest')
if rebuilt[0x147] != 0x03 or rebuilt[0x148] != 0x00 or rebuilt[0x149] != 0x02:
    fail('rebuilt ROM header is not MBC1 type $03, 32 KiB ROM, 8 KiB RAM')

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
print(f"rom_size_bytes={len(rebuilt)}")
print(f"rom_sha256={actual_sha}")
print('result=byte-identical')
PY
