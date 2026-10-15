#!/usr/bin/env bash
# Rebuild manifest-listed AGE ROMs from their pinned source with digest-pinned RGBDS.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(cd "$script_dir/../.." && pwd -P)
fixture="$repo_root/fixtures/age"
upstream_url=https://github.com/c-sp/age-test-roms.git
upstream_commit=1f5bc10e2cb60b86c19f8d0287ff78f410c4f639
upstream_tree=2fece1a678edb18c1664efd7328a430a79c70be4
mode=${1:---self-check}

python_check() {
  local check_mode=${1:-$mode}
  python3 -I - "$repo_root" "$check_mode" "${2:-}" "${3:-}" "${4:-}" "$upstream_commit" "$upstream_tree" <<'PY'
import hashlib
import json
import pathlib
import re
import subprocess
import sys

root = pathlib.Path(sys.argv[1])
mode = sys.argv[2]
rebuilt_dir = pathlib.Path(sys.argv[3]) if sys.argv[3] else None
source_root = pathlib.Path(sys.argv[4]) if sys.argv[4] else None
out = pathlib.Path(sys.argv[5]) if sys.argv[5] else None
commit, tree = sys.argv[6:8]
fixture = root / 'fixtures/age'
manifest_path = fixture / 'manifest.json'

def fail(message):
    print('self-check=fail ' + message)
    raise SystemExit(1)

def error(message):
    print('result=error ' + message)
    raise SystemExit(2)

try:
    manifest = json.loads(manifest_path.read_text())
    entries = manifest['fixtures']
    sources = (fixture / 'SOURCES.md').read_text()
except (OSError, KeyError, ValueError) as exc:
    fail('manifest-or-sources-unreadable ' + str(exc))
if not entries:
    fail('manifest-has-no-fixtures')
if commit not in sources or tree not in sources:
    fail('SOURCES-pins-differ-from-script')
if manifest.get('source', {}).get('commit') != commit or manifest.get('source', {}).get('tree') != tree:
    fail('manifest-source-pins-differ-from-script')
file_re = re.compile(r'^[A-Za-z0-9_-]+\.gb$')
source_re = re.compile(r'^src/(speed-switch|speed-switch/caution|stat-mode|stat-mode-sprites|stat-mode-window)/[A-Za-z0-9_-]+\.asm$')
expected_build = {
    'version': '1.0.1',
    'archive': 'rgbds-macos.zip',
    'archive_sha256': '2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645',
    'ci_archive': 'rgbds-linux-x86_64.tar.xz',
    'ci_archive_sha256': '80a5cad8dae27e24e46a93041352c47cadbc165103983f41c2b3082c42f6dad9',
    'recipe': 'rgbasm -Weverything -I src -I src/_include; rgblink -t; rgbfix -v -p 255',
}
m3_expected = {
    'm3-bg-lcdc-cgbBCE.gb': {
        'source_path': 'src/m3-bg-lcdc/m3-bg-lcdc.asm',
        'source_size_bytes': 287,
        'source_sha256': '2f2ba3ecd5135265e9b8033ce967135df928d649fc17ad83c6aea073851e54c7',
        'size_bytes': 32768,
        'sha256': 'fabdfd1c3f21df7543186a7303ad645a6b342f9c1ea7c1a4b26b4bb9b821b9f4',
        'header_143': '80',
        'model': 'CPU CGB E - CPU-CGB-06',
        'mode': 'native-cgb',
        'speed': 'normal',
        'expected_role': 'pass-target',
        'cgb_e_verified': '2021-11-29: CPU CGB E - CPU-CGB-06',
        'reference': {
            'file': 'references/m3-bg-lcdc-cgbBCE.png',
            'source_path': 'src/m3-bg-lcdc/m3-bg-lcdc-cgbBCE.png',
            'size_bytes': 587,
            'sha256': '69a0b85a82eddc884ec225a3c6353622876afe589125809d6517439cbeb91cef',
        },
    },
    'm3-bg-lcdc-nocgb-ncmBCE.gb': {
        'source_path': 'src/m3-bg-lcdc/m3-bg-lcdc-nocgb.asm',
        'source_size_bytes': 328,
        'source_sha256': '5c726a8548fd254d5826888d692b6bca51e8d05a35b985d4a491cbda55effb1a',
        'size_bytes': 32768,
        'sha256': 'c7f6a09a69eb2ea550b497f0aea9910b30561623dec0aefbe9b16fd0d622b460',
        'header_143': '00',
        'model': 'CPU CGB E - CPU-CGB-06',
        'mode': 'dmg-compatibility',
        'speed': 'normal',
        'expected_role': 'pass-target',
        'cgb_e_verified': '2021-11-29: CPU CGB E - CPU-CGB-06 (non-CGB mode)',
        'reference': {
            'file': 'references/m3-bg-lcdc-nocgb-ncmBCE.png',
            'source_path': 'src/m3-bg-lcdc/m3-bg-lcdc-nocgb-ncmBCE.png',
            'size_bytes': 689,
            'sha256': 'f4dbb03aff6fbd95c69eb85d264712b28727a1403f81b28ebba357bceb02f908',
        },
    },
    'm3-bg-lcdc-ds-cgbBCE.gb': {
        'source_path': 'src/m3-bg-lcdc/m3-bg-lcdc-ds.asm',
        'source_size_bytes': 260,
        'source_sha256': '579a3764a5a1a2d5fe70a63833ac9884ff9e06c86a1561d09f7c2a548bc3c9f8',
        'size_bytes': 32768,
        'sha256': 'e84cb10803c49197e4197347ffca138883fb628121d16308ccf4e5b6f657c55c',
        'header_143': 'C0',
        'model': 'CPU CGB E - CPU-CGB-06',
        'mode': 'native-cgb',
        'speed': 'double',
        'expected_role': 'pass-target',
        'cgb_e_verified': '2021-11-29: CPU CGB E - CPU-CGB-06',
        'reference': {
            'file': 'references/m3-bg-lcdc-ds-cgbBCE.png',
            'source_path': 'src/m3-bg-lcdc/m3-bg-lcdc-ds-cgbBCE.png',
            'size_bytes': 559,
            'sha256': '804f5692b2d4897a6edcf2691004f1484cfbf9b77f5f779923aba91237a5abba',
        },
    },
    'm3-bg-scx-cgbBCE.gb': {
        'source_path': 'src/m3-bg-scx/m3-bg-scx.asm',
        'source_size_bytes': 285,
        'source_sha256': '9b9bce116583ca1700c5d0b178002d0be665e52974f531224a10effd44dd51f5',
        'size_bytes': 32768,
        'sha256': 'ac6726b81af5e3d3a88aa8b9ba80f9b72b629b408f3d5ebc6824ec1a3e22852e',
        'header_143': '80',
        'model': 'CPU CGB E - CPU-CGB-06',
        'mode': 'native-cgb',
        'speed': 'normal',
        'expected_role': 'pass-target',
        'cgb_e_verified': '2021-12-01: CPU CGB E - CPU-CGB-06',
        'reference': {
            'file': 'references/m3-bg-scx-cgbBCE.png',
            'source_path': 'src/m3-bg-scx/m3-bg-scx-cgbBCE.png',
            'size_bytes': 448,
            'sha256': '6895b6111d432ea5f0422991a1d7143f1fe133481e018b3c8652616af759085d',
        },
    },
    'm3-bg-scx-nocgb-ncmBCE.gb': {
        'source_path': 'src/m3-bg-scx/m3-bg-scx-nocgb.asm',
        'source_size_bytes': 326,
        'source_sha256': '22375b480fae68a6af3b63fd71c77213967851a8eb537b35f17ee8bb11f43a9b',
        'size_bytes': 32768,
        'sha256': 'bf76542319c2a0bf0f428cdde7f9a9ec3dd50e7cac86dc57783005b2e79dcdf3',
        'header_143': '00',
        'model': 'CPU CGB E - CPU-CGB-06',
        'mode': 'dmg-compatibility',
        'speed': 'normal',
        'expected_role': 'pass-target',
        'cgb_e_verified': '2021-12-01: CPU CGB E - CPU-CGB-06 (non-CGB mode)',
        'reference': {
            'file': 'references/m3-bg-scx-nocgb-ncmBCE.png',
            'source_path': 'src/m3-bg-scx/m3-bg-scx-nocgb-ncmBCE.png',
            'size_bytes': 449,
            'sha256': '1224f9f27644355067bec6e17f3db619926b85fbcd90ec8b06e5fa93ec536114',
        },
    },
    'm3-bg-scx-ds-cgbBCE.gb': {
        'source_path': 'src/m3-bg-scx/m3-bg-scx-ds.asm',
        'source_size_bytes': 258,
        'source_sha256': '8f6e0301f6aff5122c16c9a1c483e4852ea3bb2e0dd34ef26728f60096d29e88',
        'size_bytes': 32768,
        'sha256': '0756e38b86bef3ac4ce183b982f4f228c73f8e9bb5a5212e3bd1b48527e9759e',
        'header_143': 'C0',
        'model': 'CPU CGB E - CPU-CGB-06',
        'mode': 'native-cgb',
        'speed': 'double',
        'expected_role': 'pass-target',
        'cgb_e_verified': '2021-12-01: CPU CGB E - CPU-CGB-06',
        'reference': {
            'file': 'references/m3-bg-scx-ds-cgbBCE.png',
            'source_path': 'src/m3-bg-scx/m3-bg-scx-ds-cgbBCE.png',
            'size_bytes': 448,
            'sha256': '6895b6111d432ea5f0422991a1d7143f1fe133481e018b3c8652616af759085d',
        },
    },
}
build = manifest.get('build', {})
if any(build.get(field) != value for field, value in expected_build.items()):
    fail('RGBDS-build-pin-mismatch')
m3_entries = {
    entry.get('file'): entry
    for entry in entries
    if entry.get('fixture_class') == 'age-m3-reference'
}
if set(m3_entries) != set(m3_expected):
    fail('m3-manifest-membership-mismatch')
rows = []
seen_names = set()
for entry in entries:
    name = entry.get('file', '')
    source = entry.get('source_path', '')
    digest = entry.get('sha256', '')
    if name in seen_names:
        fail('duplicate-file-entry-' + name)
    seen_names.add(name)
    if not file_re.fullmatch(name):
        fail('file-outside-allow-list')
    expected_m3 = m3_expected.get(name)
    if not source_re.fullmatch(source) and expected_m3 is None:
        fail('source_path-outside-allow-list')
    if not re.fullmatch(r'[0-9a-f]{64}', digest):
        fail('invalid-sha256-' + name)
    if expected_m3 is not None:
        for field in ('source_path', 'source_size_bytes', 'source_sha256', 'size_bytes', 'sha256', 'header_143', 'model', 'mode', 'speed', 'expected_role'):
            if entry.get(field) != expected_m3[field]:
                fail('m3-' + field.replace('_', '-') + '-mismatch-' + name)
        if entry.get('qualification_status') != 'admitted-not-executed':
            fail('m3-qualification-status-mismatch-' + name)
        if expected_m3['cgb_e_verified'] not in entry.get('verified', []):
            fail('m3-author-attestation-mismatch-' + name)
        reference = entry.get('reference', {})
        for field, value in expected_m3['reference'].items():
            if reference.get(field) != value:
                fail('m3-reference-' + field.replace('_', '-') + '-mismatch-' + name)
    committed_path = fixture / name
    try:
        committed = committed_path.read_bytes()
    except OSError:
        fail('committed-file-missing-' + name)
    if len(committed) != entry.get('size_bytes') or hashlib.sha256(committed).hexdigest() != digest:
        fail('committed-digest-mismatch-' + name)
    if expected_m3 is not None:
        if committed[0x143] != int(expected_m3['header_143'], 16):
            fail('m3-header-143-mismatch-' + name)
        reference_path = fixture / expected_m3['reference']['file']
        try:
            reference_bytes = reference_path.read_bytes()
        except OSError:
            fail('committed-reference-missing-' + name)
        reference_expected = expected_m3['reference']
        if (len(reference_bytes) != reference_expected['size_bytes']
                or hashlib.sha256(reference_bytes).hexdigest() != reference_expected['sha256']):
            fail('committed-reference-digest-mismatch-' + name)
    rows.append((entry, name, source))
if mode == '--self-check':
    print('self-check=pass')
    raise SystemExit(0)
if mode == '--compare-built':
    if rebuilt_dir is None or not rebuilt_dir.is_dir():
        error('rebuilt-directory-missing')
    mismatch = False
    for entry, name, _ in rows:
        rebuilt_path = rebuilt_dir / name
        if not rebuilt_path.is_file():
            error('missing-rebuilt-file-' + name)
        rebuilt = rebuilt_path.read_bytes()
        committed = (fixture / name).read_bytes()
        if rebuilt != committed:
            mismatch = True
            print('result=differs %s %s %s' % (name, hashlib.sha256(rebuilt).hexdigest(), hashlib.sha256(committed).hexdigest()))
    if mismatch:
        raise SystemExit(1)
    print('result=byte-identical')
    raise SystemExit(0)

if mode != '--compare':
    error('usage: reproduce-age.sh [--self-check|--compare|--compare-built DIR]')

build = manifest.get('build', {})
if build.get('version') != '1.0.1':
    error('manifest-does-not-pin-rgbds-1.0.1')
archive_path = pathlib.Path(__import__('os').environ['GBB_RGBDS_ARCHIVE']) if __import__('os').environ.get('GBB_RGBDS_ARCHIVE') else None
if archive_path:
    if not archive_path.is_file():
        error('GBB_RGBDS_ARCHIVE-not-a-file')
    archive_digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    if archive_digest not in (build.get('archive_sha256'), build.get('ci_archive_sha256')):
        error('RGBDS-archive-digest-not-pinned')
    supplied = __import__('os').environ.get('GBB_RGBDS_ARCHIVE_SHA256')
    if supplied and supplied != archive_digest:
        error('RGBDS-archive-digest-differs-from-supplied-pin')
for tool in ('rgbasm', 'rgblink', 'rgbfix'):
    try:
        version = subprocess.run([tool, '--version'], check=True, capture_output=True, text=True).stdout.splitlines()[0]
    except (OSError, subprocess.CalledProcessError, IndexError) as exc:
        error('RGBDS-tool-unavailable-' + tool + '-' + str(exc))
    if version != tool + ' v1.0.1':
        error('RGBDS-version-mismatch-' + tool + '-' + version)

if mode == '--compare' and (source_root is None or out is None):
    error('internal-source-or-output-path-missing')
if mode == '--compare':
    for entry, name, source in rows:
        expected_m3 = m3_expected.get(name)
        if expected_m3 is not None:
            source_path = source_root / expected_m3['source_path']
            reference_path = source_root / expected_m3['reference']['source_path']
            try:
                source_bytes = source_path.read_bytes()
                source_text = source_bytes.decode('utf-8')
                reference_bytes = reference_path.read_bytes()
            except (OSError, UnicodeDecodeError) as exc:
                error('upstream-source-or-reference-missing-' + name + '-' + str(exc))
            if (len(source_bytes) != expected_m3['source_size_bytes']
                    or hashlib.sha256(source_bytes).hexdigest() != expected_m3['source_sha256']):
                error('upstream-source-digest-mismatch-' + name)
            if expected_m3['cgb_e_verified'] not in source_text:
                error('upstream-cgb-e-attestation-missing-' + name)
            reference_expected = expected_m3['reference']
            if (len(reference_bytes) != reference_expected['size_bytes']
                    or hashlib.sha256(reference_bytes).hexdigest() != reference_expected['sha256']):
                error('upstream-reference-digest-mismatch-' + name)
            committed_reference = (fixture / reference_expected['file']).read_bytes()
            if reference_bytes != committed_reference:
                print('result=reference-differs ' + reference_expected['file'])
                raise SystemExit(1)
            print('result=reference-source-identical ' + reference_expected['file'])
        obj = out / (name + '.o')
        rom = out / name
        steps = [
            ['rgbasm', '-Weverything', '-I', str(source_root / 'src'), '-I', str(source_root / 'src/_include'), '-o', str(obj), str(source_root / source)],
            ['rgblink', '-t', '-n', str(out / (name + '.sym')), '-m', str(out / (name + '.map')), '-o', str(rom), str(obj)],
            ['rgbfix', '-v', '-p', '255', str(rom)],
        ]
        for command in steps:
            done = subprocess.run(command, cwd=root, capture_output=True, text=True)
            if done.returncode:
                error('tool-failed-' + command[0] + '-' + name + '-' + (done.stderr or done.stdout).strip()[:240])
PY
}

case "$mode" in
  --self-check)
    python_check --self-check
    ;;
  --compare-built)
    [ "$#" -eq 2 ] || { echo "usage: $0 --compare-built DIR" >&2; exit 2; }
    python_check --compare-built "$2"
    ;;
  --compare)
    python_check --self-check >/dev/null
    work_dir=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-age.XXXXXXXX")
    trap 'rm -rf -- "$work_dir"' EXIT
    mkdir "$work_dir/upstream" "$work_dir/out"
    git -C "$work_dir/upstream" init -q
    git -C "$work_dir/upstream" fetch -q --depth 1 "$upstream_url" "$upstream_commit"
    git -C "$work_dir/upstream" checkout -q FETCH_HEAD
    [[ "$(git -C "$work_dir/upstream" rev-parse HEAD)" == "$upstream_commit" ]] || { echo 'upstream HEAD differs from pin' >&2; exit 1; }
    [[ "$(git -C "$work_dir/upstream" rev-parse 'HEAD^{tree}')" == "$upstream_tree" ]] || { echo 'upstream tree differs from pin' >&2; exit 1; }
    python_check --compare '' "$work_dir/upstream" "$work_dir/out"
    python_check --compare-built "$work_dir/out"
    ;;
  *) echo "usage: $0 [--self-check|--compare|--compare-built DIR]" >&2; exit 2 ;;
esac
