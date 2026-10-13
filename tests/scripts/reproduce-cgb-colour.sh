#!/usr/bin/env bash
# Reproduce every project-authored CGB colour fixture ROM listed in fixtures/cgb-colour/manifest.json
# with the pinned RGBDS. Each manifest row carries its own recipe (source, -D defines, rgbfix flags),
# so adding a ROM means adding a row, not editing this script. Normal build and test runs consume the
# checked-in, digest-verified bytes; this script never writes into the repository.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(cd "$script_dir/../.." && pwd -P)
cd "$repo_root"

work_dir=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-cgb-colour.XXXXXXXX")
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

# Recipe fields become tool arguments, so they are validated and passed as argument lists, never
# through a shell.
python3 -I - "$repo_root" "$work_dir" <<'PY'
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

root = pathlib.Path(sys.argv[1])
work = pathlib.Path(sys.argv[2])
fixture = root / 'fixtures/cgb-colour'
manifest = json.loads((fixture / 'manifest.json').read_text())
reference = json.loads((root / 'fixtures/cgb-banking/manifest.json').read_text())

def fail(message):
    print(f'result=differs reason={message}')
    raise SystemExit(1)

NAME = re.compile(r'^[A-Za-z0-9_][A-Za-z0-9_.-]*$')
DEFINE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
FLAG = re.compile(r'^[-A-Za-z0-9_.]+$')

build = manifest.get('build', {})
ref = reference.get('build', {})
for key in ('assembler', 'version', 'archive', 'archive_sha256', 'ci_archive', 'ci_archive_sha256'):
    if build.get(key) != ref.get(key):
        fail(f'build-pin-{key}-differs-from-cgb-banking')
if build.get('version') != '1.0.1':
    fail('manifest-must-pin-rgbds-1.0.1')
if manifest.get('source_identity') != 'Original GabbaBoy project-authored assembly':
    fail('source-identity-not-project-owned')
if not manifest.get('license', '').startswith('MIT;') or not (fixture / 'LICENSE.txt').is_file():
    fail('missing-license-notice')
if 'not hardware evidence' not in manifest.get('evidence_class', ''):
    fail('evidence-class-must-exclude-hardware')
if not manifest.get('protocol') or not manifest.get('scope_limits'):
    fail('protocol-and-scope-limits-required')

for source_name, expected in manifest.get('source_sha256', {}).items():
    if not NAME.match(source_name):
        fail(f'bad-source-name-{source_name}')
    actual = hashlib.sha256((fixture / source_name).read_bytes()).hexdigest()
    if actual != expected:
        fail(f'source-sha256-mismatch-{source_name}')

entries = manifest.get('fixtures', [])
if not entries:
    fail('no-fixtures')
for entry in entries:
    name = entry.get('file', '')
    recipe = entry.get('recipe')
    if not NAME.match(name):
        fail(f'bad-rom-name-{name}')
    if not isinstance(recipe, dict):
        fail('missing-recipe')
    source = recipe.get('source', '')
    defines = recipe.get('defines')
    flags = recipe.get('rgbfix_flags')
    if not NAME.match(source) or not (fixture / source).is_file():
        fail(f'bad-recipe-source-{name}')
    if source not in manifest.get('source_sha256', {}):
        fail(f'recipe-source-has-no-digest-{name}')
    if not isinstance(defines, list) or not all(isinstance(d, str) and DEFINE.match(d) for d in defines):
        fail(f'bad-recipe-defines-{name}')
    if not isinstance(flags, list) or not all(isinstance(f, str) and FLAG.match(f) for f in flags):
        fail(f'bad-recipe-rgbfix-flags-{name}')

    obj = work / (name + '.o')
    rom = work / name
    define_args = [arg for d in defines for arg in ('-D', d)]
    steps = [
        ['rgbasm', '-I', str(fixture) + '/', *define_args, '-o', str(obj), str(fixture / source)],
        ['rgblink', '-o', str(rom), str(obj)],
        ['rgbfix', *flags, str(rom)],
    ]
    for step in steps:
        done = subprocess.run(step, cwd=root, capture_output=True, text=True)
        if done.returncode != 0:
            fail(f'tool-failed-{step[0]}-{name}')

    rebuilt = rom.read_bytes()
    checked_in = (fixture / name).read_bytes()
    actual_sha = hashlib.sha256(rebuilt).hexdigest()
    if entry.get('size_bytes') != len(rebuilt) or len(rebuilt) != len(checked_in):
        fail(f'size-mismatch-{name}')
    if actual_sha != entry.get('sha256'):
        fail(f'rebuilt-sha256-mismatch-{name}-manifest={entry.get("sha256")}-actual={actual_sha}')
    if hashlib.sha256(checked_in).hexdigest() != entry['sha256'] or rebuilt != checked_in:
        fail(f'rebuilt-rom-differs-from-checked-in-{name}')
    print(f"rom={name} size_bytes={len(rebuilt)} sha256={actual_sha}")

archive_path = os.environ.get('GBB_RGBDS_ARCHIVE')
if archive_path:
    archive = pathlib.Path(archive_path)
    if not archive.is_file():
        fail('GBB_RGBDS_ARCHIVE-not-a-regular-file')
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    if archive_sha not in {build['archive_sha256'], build['ci_archive_sha256']}:
        fail(f'rgbds-archive-sha256-not-pinned-{archive_sha}')
    expected_archive_sha = os.environ.get('GBB_RGBDS_ARCHIVE_SHA256')
    if expected_archive_sha and expected_archive_sha != archive_sha:
        fail('downloaded-archive-digest-differs-from-supplied-pin')

print(f"rgbds={build['version']}")
print(f'result=byte-identical roms={len(entries)}')
PY
