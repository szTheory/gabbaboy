#!/usr/bin/env bash
# Opt-in, pinned-tool fixture reproduction. Normal builds use checked-in bytes.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(cd "$script_dir/../.." && pwd -P)
cd "$repo_root"

work_dir=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-visible-demo.XXXXXXXX")
cleanup() {
  rm -rf -- "$work_dir"
}
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

rgbasm -o "$work_dir/demo.o" fixtures/visible-demo/demo.asm
rgblink -o "$work_dir/demo.gb" "$work_dir/demo.o"
rgbfix -f hg -p 0 -m 0 -r 0 "$work_dir/demo.gb"

python3 - "$repo_root" "$work_dir/demo.gb" <<'PY'
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

root = pathlib.Path(sys.argv[1])
rebuilt_path = pathlib.Path(sys.argv[2])
fixture = root / 'fixtures/visible-demo'
manifest_path = fixture / 'manifest.json'
manifest = json.loads(manifest_path.read_text())
tracer = json.loads((root / 'fixtures/tracer/manifest.json').read_text())

def fail(message):
    raise SystemExit(message)

build = manifest['build']
tracer_build = tracer['build']
if manifest.get('id') != 'original-visible-interactive-dmg':
    fail('manifest does not identify the original visible demo fixture')
if manifest.get('source') != 'demo.asm' or manifest.get('rom') != 'demo.gb':
    fail('visible demo manifest source and ROM paths must stay within their fixture directory')
source_path = fixture / manifest['source']
checked_in_path = fixture / manifest['rom']

if manifest.get('source_identity') != 'Original GabbaBoy project-authored assembly':
    fail('visible demo source identity is not the reviewed project-owned fixture')
if not manifest.get('license', '').startswith('MIT;'):
    fail('visible demo manifest is missing its MIT rights declaration')
if not (fixture / 'LICENSE.txt').is_file():
    fail('visible demo rights notice is missing')
if build.get('assembler') != 'RGBDS' or build.get('version') != '1.0.1':
    fail('manifest must pin RGBDS v1.0.1')
if build.get('version') != tracer_build.get('version'):
    fail('visible demo RGBDS version differs from the established tracer pin')
if (build.get('archive'), build.get('archive_sha256')) != (
        tracer_build.get('archive'), tracer_build.get('archive_sha256')):
    fail('visible demo macOS RGBDS archive pin differs from the established tracer pin')
if build.get('ci_archive') != 'rgbds-linux-x86_64.tar.xz':
    fail('visible demo CI archive name differs from the reviewed Linux RGBDS release')
if build.get('ci_archive_sha256') != '80a5cad8dae27e24e46a93041352c47cadbc165103983f41c2b3082c42f6dad9':
    fail('visible demo CI RGBDS archive digest differs from the reviewed release pin')
if not build.get('recipe'):
    fail('manifest build recipe must be nonempty')
if manifest.get('profile', {}).get('name') != 'DMG-CPU-B':
    fail('visible demo applicability must name the bootless DMG-CPU-B profile')
if 'not physical hardware evidence' not in manifest['profile'].get('applicability', ''):
    fail('visible demo manifest must keep fixture applicability separate from hardware evidence')
if not manifest.get('protocol') or not manifest.get('scope_limits'):
    fail('visible demo protocol and scope limits must be recorded')

source_bytes = source_path.read_bytes()
source_sha = hashlib.sha256(source_bytes).hexdigest()
if source_sha != manifest.get('source_sha256'):
    fail(f'assembly source SHA-256 mismatch: manifest={manifest.get("source_sha256")} actual={source_sha}')

rebuilt = rebuilt_path.read_bytes()
checked_in = checked_in_path.read_bytes()
expected_size = manifest.get('size_bytes')
expected_sha = manifest.get('sha256')
actual_sha = hashlib.sha256(rebuilt).hexdigest()
if expected_size != 32768 or len(rebuilt) != expected_size:
    fail(f'rebuilt ROM size mismatch: expected={expected_size} actual={len(rebuilt)}')
if len(checked_in) != expected_size:
    fail(f'checked-in ROM size mismatch: expected={expected_size} actual={len(checked_in)}')
if actual_sha != expected_sha:
    fail(f'rebuilt ROM SHA-256 mismatch: expected={expected_sha} actual={actual_sha}')
if hashlib.sha256(checked_in).hexdigest() != expected_sha:
    fail('checked-in ROM does not match the manifest SHA-256')
if rebuilt != checked_in:
    fail('rebuilt ROM bytes differ from the checked-in visible demo')

archive_path = os.environ.get('GBB_RGBDS_ARCHIVE')
archive_sha = build['ci_archive_sha256']
if archive_path:
    archive = pathlib.Path(archive_path)
    if not archive.is_file():
        fail('GBB_RGBDS_ARCHIVE does not name a regular file')
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    allowed_pins = {build['archive_sha256'], build['ci_archive_sha256']}
    if archive_sha not in allowed_pins:
        fail(f'RGBDS release archive SHA-256 is not pinned: {archive_sha}')
if os.environ.get('GBB_RGBDS_ARCHIVE_SHA256') and os.environ['GBB_RGBDS_ARCHIVE_SHA256'] != archive_sha:
    fail('downloaded RGBDS archive digest differs from the fixture manifest')

expected_revision = os.environ.get('GBB_EXPECTED_SOURCE_REVISION')
receipt_path = os.environ.get('GBB_REPRO_RECEIPT')
if receipt_path:
    if not expected_revision or not re.fullmatch(r'[0-9a-f]{40}', expected_revision):
        fail('receipt generation requires a full expected source revision')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    if head != expected_revision:
        fail(f'checkout revision mismatch: expected={expected_revision} actual={head}')
    for path in (
        'fixtures/visible-demo/demo.asm', 'fixtures/visible-demo/demo.gb',
        'fixtures/visible-demo/manifest.json', 'fixtures/visible-demo/LICENSE.txt',
        'tests/scripts/reproduce-visible-demo.sh', 'tests/expected-tests.txt',
    ):
        subprocess.run(['git', 'ls-files', '--error-unmatch', path], cwd=root,
                       check=True, stdout=subprocess.DEVNULL)
    subprocess.run(['git', 'diff', '--quiet', expected_revision, '--',
                    'fixtures/visible-demo', 'tests/scripts/reproduce-visible-demo.sh',
                    'tests/expected-tests.txt'], cwd=root, check=True)
    subprocess.run(['git', 'diff', '--cached', '--quiet', expected_revision, '--',
                    'fixtures/visible-demo', 'tests/scripts/reproduce-visible-demo.sh',
                    'tests/expected-tests.txt'], cwd=root, check=True)
    expected_test = os.environ.get('GBB_EXPECTED_TEST', '')
    reproduction_command = os.environ.get('GBB_REPRO_COMMAND', '')
    if not expected_test.strip() or not reproduction_command.strip():
        fail('receipt requires nonempty expected-test and reproduction-command identities')
    inventory = root / 'tests/expected-tests.txt'
    if not inventory.is_file() or not inventory.read_bytes().strip():
        fail('expected-test inventory is missing or empty')
    run_id = os.environ.get('GITHUB_RUN_ID', '')
    run_attempt = os.environ.get('GITHUB_RUN_ATTEMPT', '')
    if not re.fullmatch(r'[0-9]+', run_id) or not re.fullmatch(r'[0-9]+', run_attempt):
        fail('run-scoped receipt requires numeric GitHub run ID and attempt')
    receipt = {
        'schema_version': 1,
        'result': 'passed',
        'source_revision': head,
        'github_run_id': run_id,
        'github_run_attempt': run_attempt,
        'expected_test': expected_test,
        'reproduction_command': reproduction_command,
        'tool': 'RGBDS',
        'tool_version': build['version'],
        'archive': build['ci_archive'],
        'archive_sha256': archive_sha,
        'source': f"fixtures/visible-demo/{manifest['source']}",
        'source_sha256': source_sha,
        'rom': f"fixtures/visible-demo/{manifest['rom']}",
        'rom_size_bytes': len(rebuilt),
        'rom_sha256': actual_sha,
    }
    target = pathlib.Path(receipt_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=target.parent,
                                     prefix=f'.{target.name}.', delete=False) as stream:
        temp_path = pathlib.Path(stream.name)
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write('\n')
    try:
        temp_path.replace(target)
    finally:
        temp_path.unlink(missing_ok=True)
    print(f"receipt={target.name}")

print(f"rgbds={build['version']}")
print(f"source_sha256={source_sha}")
print(f"rom_size_bytes={len(rebuilt)}")
print(f"rom_sha256={actual_sha}")
print('result=byte-identical')
PY
