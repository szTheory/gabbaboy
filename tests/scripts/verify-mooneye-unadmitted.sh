#!/usr/bin/env bash
# Verify or restore the exact pre-admission Mooneye fixture baseline.
set -euo pipefail

mode=${1:-}
shift || { echo 'missing mode' >&2; exit 2; }
repo_root=$(git rev-parse --show-toplevel)
baseline_arg=''
root_arg='.'
stage_arg=''
while (($#)); do
  case "$1" in
    --baseline) (($# >= 2)) || exit 2; baseline_arg=$2; shift 2 ;;
    --root) (($# >= 2)) || exit 2; root_arg=$2; shift 2 ;;
    --stage) (($# >= 2)) || exit 2; stage_arg=$2; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
[[ -n "$baseline_arg" ]] || { echo '--baseline is required' >&2; exit 2; }
case "$mode" in
  --assert-baseline|--restore-and-verify|--self-test-rollback|--self-test-hosted-binding|--verify-hosted-binding) ;;
  --stage-validate-and-promote) [[ -n "$stage_arg" ]] || { echo '--stage is required' >&2; exit 2; } ;;
  *) echo 'usage: verify-mooneye-unadmitted.sh --assert-baseline|--restore-and-verify|--self-test-rollback|--self-test-hosted-binding|--verify-hosted-binding|--stage-validate-and-promote --baseline PATH --root DIR [--stage DIR]' >&2; exit 2 ;;
esac

if [[ "$root_arg" == /* ]]; then root=$root_arg; else root="$repo_root/$root_arg"; fi
if [[ "$baseline_arg" == /* ]]; then baseline=$baseline_arg; else baseline="$repo_root/$baseline_arg"; fi
if [[ -n "$stage_arg" ]]; then
  if [[ "$stage_arg" == /* ]]; then stage=$stage_arg; else stage="$repo_root/$stage_arg"; fi
else
  stage=''
fi

python3 - "$mode" "$repo_root" "$root" "$baseline" "$stage" <<'PY'
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

mode, repo_text, root_text, baseline_text, stage_text = sys.argv[1:]
repo = pathlib.Path(repo_text).resolve()
root = pathlib.Path(root_text).resolve()
baseline_path = pathlib.Path(baseline_text).resolve()
stage_base = pathlib.Path(stage_text).resolve() if stage_text else None
baseline = json.loads(baseline_path.read_text())

def sha(data):
    return hashlib.sha256(data).hexdigest()

def verify_hosted_candidate_binding(lock, local_output, committed_lock_bytes):
    expected_lock_sha = lock.get('committed_lock_sha256')
    if not isinstance(expected_lock_sha, str) or len(expected_lock_sha) != 64 or sha(committed_lock_bytes) != expected_lock_sha:
        raise SystemExit('candidate lock digest does not match the exact qualified Git revision')

    artifact_dir = local_output / 'hosted-artifact'
    artifact_lock_path = artifact_dir / 'candidate-digests.json'
    artifact_report_path = artifact_dir / 'candidate-comparison.json'
    local_report_path = local_output / 'hosted-comparison.json'
    if not artifact_lock_path.is_file() or not artifact_report_path.is_file() or not local_report_path.is_file():
        raise SystemExit('retained exact-hosted candidate evidence is incomplete')
    artifact_lock_bytes = artifact_lock_path.read_bytes()
    if artifact_lock_bytes != committed_lock_bytes:
        raise SystemExit('retained artifact candidate lock is not the exact lock from the qualified Git revision')

    committed_lock = json.loads(committed_lock_bytes)
    if lock.get('candidates') != committed_lock.get('candidates'):
        raise SystemExit('mutable candidate digests differ from the exact qualified Git lock')
    candidates = committed_lock.get('candidates', [])
    expected_roms = {'daa.gb', 'tim00.gb', 'tim00_div_trigger.gb'}
    if len(candidates) != 3 or {item.get('rom') for item in candidates} != expected_roms:
        raise SystemExit('exact hosted candidate lock does not contain the fixed three-ROM set')

    head = lock.get('head_sha')
    run_id = lock.get('run_id')
    if not isinstance(head, str) or len(head) != 40 or not isinstance(run_id, int):
        raise SystemExit('candidate lock lacks an exact hosted revision or run ID')
    local_report = json.loads(local_report_path.read_bytes())
    if (local_report.get('head_sha') != head or local_report.get('run_id') != run_id or
            local_report.get('host') != 'Linux/x86_64' or
            local_report.get('workflow_path') != '.github/workflows/fixture-repro.yml' or
            local_report.get('byte_identical') is not True):
        raise SystemExit('local exact-hosted verification receipt does not bind this head and run')
    hosted_report = json.loads(artifact_report_path.read_bytes())
    if (hosted_report.get('head_sha') != head or hosted_report.get('host') != 'Linux/x86_64' or
            hosted_report.get('local_status') != 'qualified'):
        raise SystemExit('retained hosted comparison report does not bind the exact Linux revision')

    local_cases = {item.get('rom'): item for item in local_report.get('cases', [])}
    hosted_cases = {item.get('rom'): item for item in hosted_report.get('cases', [])}
    if set(local_cases) != expected_roms or set(hosted_cases) != expected_roms:
        raise SystemExit('exact-hosted reports do not cover all three candidate ROMs')
    for candidate in candidates:
        rom_name = candidate['rom']
        stem = pathlib.Path(rom_name).stem
        local_rom = local_output / stem / 'rebuilt.gb'
        hosted_rom = artifact_dir / stem / 'rebuilt.gb'
        if not local_rom.is_file() or not hosted_rom.is_file():
            raise SystemExit(f'exact-hosted candidate bytes are missing: {rom_name}')
        local_bytes = local_rom.read_bytes()
        hosted_bytes = hosted_rom.read_bytes()
        expected_sha = candidate.get('sha256')
        expected_size = candidate.get('size_bytes')
        if (local_bytes != hosted_bytes or len(local_bytes) != expected_size or
                sha(local_bytes) != expected_sha or sha(hosted_bytes) != expected_sha):
            raise SystemExit(f'local candidate bytes are not identical to the exact hosted artifact: {rom_name}')
        local_case = local_cases[rom_name]
        hosted_case = hosted_cases[rom_name]
        if (local_case.get('byte_identical') is not True or
                local_case.get('local_sha256') != expected_sha or
                local_case.get('hosted_sha256') != expected_sha or
                hosted_case.get('lock_match') is not True or
                hosted_case.get('expected_sha256') != expected_sha or
                hosted_case.get('actual_sha256') != expected_sha):
            raise SystemExit(f'exact-hosted byte comparison receipt is invalid: {rom_name}')

def self_test_hosted_candidate_binding():
    with tempfile.TemporaryDirectory(prefix='gabbaboy-hosted-binding-') as temp_text:
        base = pathlib.Path(temp_text)
        local_output = base / 'local'
        artifact_dir = local_output / 'hosted-artifact'
        artifact_dir.mkdir(parents=True)
        head = 'a' * 40
        candidates = []
        for index, rom_name in enumerate(('daa.gb', 'tim00.gb', 'tim00_div_trigger.gb'), start=1):
            raw = bytes([index]) * 32768
            candidates.append({
                'id': rom_name.removesuffix('.gb'), 'rom': rom_name,
                'sha256': sha(raw), 'size_bytes': len(raw),
            })
            stem = pathlib.Path(rom_name).stem
            for directory in (local_output / stem, artifact_dir / stem):
                directory.mkdir(parents=True, exist_ok=True)
                (directory / 'rebuilt.gb').write_bytes(raw)
        committed_lock = json.dumps({'recipe_status': 'qualified', 'candidates': candidates}, indent=2).encode()
        (artifact_dir / 'candidate-digests.json').write_bytes(committed_lock)
        local_report = {
            'head_sha': head, 'run_id': 12345, 'host': 'Linux/x86_64',
            'workflow_path': '.github/workflows/fixture-repro.yml', 'byte_identical': True,
            'cases': [
                {'rom': item['rom'], 'byte_identical': True,
                 'local_sha256': item['sha256'], 'hosted_sha256': item['sha256']}
                for item in candidates
            ],
        }
        hosted_report = {
            'head_sha': head, 'host': 'Linux/x86_64', 'local_status': 'qualified',
            'cases': [
                {'rom': item['rom'], 'lock_match': True,
                 'expected_sha256': item['sha256'], 'actual_sha256': item['sha256']}
                for item in candidates
            ],
        }
        (local_output / 'hosted-comparison.json').write_text(json.dumps(local_report))
        (artifact_dir / 'candidate-comparison.json').write_text(json.dumps(hosted_report))
        lock = {
            'head_sha': head, 'run_id': 12345,
            'committed_lock_sha256': sha(committed_lock), 'candidates': candidates,
        }
        verify_hosted_candidate_binding(lock, local_output, committed_lock)

        changed_lock = json.loads(json.dumps(lock))
        changed_lock['candidates'][0]['sha256'] = '0' * 64
        try:
            verify_hosted_candidate_binding(changed_lock, local_output, committed_lock)
        except SystemExit:
            pass
        else:
            raise SystemExit('hosted-binding self-test accepted a tampered mutable candidate digest')

        local_rom = local_output / 'daa' / 'rebuilt.gb'
        original = local_rom.read_bytes()
        local_rom.write_bytes(bytes([0xff]) + original[1:])
        try:
            verify_hosted_candidate_binding(lock, local_output, committed_lock)
        except SystemExit:
            pass
        else:
            raise SystemExit('hosted-binding self-test accepted local bytes differing from the hosted artifact')

def safe_relative(value):
    path = pathlib.PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts:
        raise SystemExit(f'unsafe baseline path: {value}')
    return path

def source_blob(relative):
    return subprocess.check_output(['git', '-C', str(repo), 'show', f"{baseline['source_head']}:{relative}"])

def current_denominator(manifest):
    eligible = [fixture for fixture in manifest.get('fixtures', []) if fixture.get('eligible') is True]
    ids = [fixture.get('id') for fixture in eligible]
    counts = {}
    for fixture in eligible:
        category = fixture.get('category')
        counts[category] = counts.get(category, 0) + 1
    return ids, counts, manifest.get('required_roms', [])

def verify_baseline(tree_root):
    manifest_relative = safe_relative(baseline['manifest_path'])
    manifest_file = tree_root / manifest_relative
    raw_manifest = manifest_file.read_bytes()
    if sha(raw_manifest) != baseline['manifest_sha256']:
        raise SystemExit('raw manifest SHA-256 differs from the captured baseline')
    manifest = json.loads(raw_manifest)
    ids, counts, required = current_denominator(manifest)
    if ids != baseline['eligible_ids'] or counts != baseline['category_counts'] or required != baseline['required_roms']:
        raise SystemExit('eligible IDs, category counts, or required ROM list differs from the captured baseline')
    for rom in baseline['roms']:
        relative = safe_relative(rom['path'])
        content = (tree_root / relative).read_bytes()
        if len(content) != rom['size_bytes'] or sha(content) != rom['git_blob_sha256'] or rom['git_blob_sha256'] != rom['manifest_sha256']:
            raise SystemExit(f"baseline ROM mismatch: {rom['path']}")
        source = source_blob(rom['path'])
        if source != content:
            raise SystemExit(f"working ROM does not equal the captured Git blob: {rom['path']}")
    if source_blob(baseline['manifest_path']) != raw_manifest:
        raise SystemExit('working raw manifest does not equal the captured Git blob')
    return manifest

def atomic_write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.mooneye-restore-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    except BaseException:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise

def restore_baseline(tree_root):
    paths = [baseline['manifest_path']] + [item['path'] for item in baseline['roms']]
    for value in paths:
        relative = safe_relative(value)
        atomic_write(tree_root / relative, source_blob(value))
    return verify_baseline(tree_root)

def check_source_and_rights(manifest, lock, local_output):
    fixture_dir = root / 'fixtures/mooneye'
    for name in ('LICENSE.txt', 'FONT-LICENSE.txt', 'SOURCES.md', 'ELIGIBILITY.md', 'headless-report.patch', 'font-source.c'):
        if not (fixture_dir / name).is_file():
            raise SystemExit(f'missing candidate provenance file: {name}')
    if 'MIT' not in (fixture_dir / 'LICENSE.txt').read_text():
        raise SystemExit('Mooneye MIT notice is missing')
    if 'font' not in (fixture_dir / 'FONT-LICENSE.txt').read_text().lower():
        raise SystemExit('replacement-font notice is missing')
    patch = (fixture_dir / 'headless-report.patch').read_text()
    changed_paths = {line[6:] for line in patch.splitlines() if line.startswith('+++ b/')}
    if changed_paths != {'common/common.s', 'common/lib/quit.s'}:
        raise SystemExit(f'candidate harness patch changes unexpected source files: {sorted(changed_paths)}')
    if sha((fixture_dir / 'headless-report.patch').read_bytes()) != lock['harness_patch_sha256']:
        raise SystemExit('candidate harness patch digest mismatch')
    if sha((fixture_dir / 'font-source.c').read_bytes()) != lock['replacement_asset']['font_source_sha256']:
        raise SystemExit('replacement-font source digest mismatch')
    if lock['suite']['revision'] != manifest['suite']['revision'] or lock['suite']['tree_sha1'] != manifest['suite']['tree_sha1']:
        raise SystemExit('Mooneye source pin mismatch')
    if lock['builder']['revision'] != manifest['builder']['source_revision'] or lock['builder']['tree_sha1'] != manifest['builder']['source_tree_sha1'] or lock['builder']['git_archive_sha256'] != manifest['builder']['git_archive_sha256']:
        raise SystemExit('WLA-DX source or archive pin mismatch')
    source_tree = local_output / 'mooneye-source'
    for fixture in (item for item in manifest['fixtures'] if item.get('eligible') is True):
        if fixture.get('model') != 'DMG-CPU-B' or 'bootless' not in fixture.get('boot', '').lower() or not isinstance(fixture.get('timeout_half_dots'), int) or fixture['timeout_half_dots'] <= 0:
            raise SystemExit(f"missing model, boot, or bounded protocol budget: {fixture['id']}")
        if not fixture.get('protocol'):
            raise SystemExit(f"missing explicit result protocol: {fixture['id']}")
        for source_path in fixture.get('source_closure', []):
            if not (source_tree / source_path).is_file():
                raise SystemExit(f'pinned source closure is incomplete: {source_path}')
    for source_path, digest in lock['acceptance_source_sha256'].items():
        if sha((source_tree / source_path).read_bytes()) != digest:
            raise SystemExit(f'upstream acceptance source changed: {source_path}')
    probe_log = local_output / 'protocol-probe.log'
    if not probe_log.is_file():
        raise SystemExit('local protocol probe evidence is missing')
    lines = probe_log.read_text().splitlines()
    if sum('ppu_access=0' in line for line in lines) != 4 or any('ppu_access=' in line and 'ppu_access=0' not in line for line in lines):
        raise SystemExit('positive/negative probes did not all prove zero PPU accesses')

def stage_candidate_set():
    if root != repo:
        raise SystemExit('candidate admission root must be the repository root')
    lock_path = root / 'fixtures/mooneye/candidate-digests.json'
    lock = json.loads(lock_path.read_text())
    if any(lock.get(key) != 'qualified' for key in ('recipe_status', 'local_status', 'hosted_status', 'protocol_status', 'provenance_status', 'qualification_status')):
        raise SystemExit('candidate qualification gate is not fully qualified')
    if not lock.get('head_sha') or not isinstance(lock.get('run_id'), int) or not lock.get('committed_lock_sha256'):
        raise SystemExit('exact hosted revision, run, or committed lock digest is missing')
    hosted = lock.get('hosted_comparison', {})
    if hosted.get('head_sha') != lock['head_sha'] or hosted.get('workflow_path') != '.github/workflows/fixture-repro.yml' or hosted.get('host') != 'Linux/x86_64' or hosted.get('byte_identical') is not True:
        raise SystemExit('exact hosted candidate comparison evidence is incomplete')
    cases = hosted.get('cases', [])
    if len(cases) != 3 or any(case.get('byte_identical') is not True for case in cases):
        raise SystemExit('hosted exact-byte comparison did not pass for all three cases')
    live_manifest = verify_baseline(root)
    baseline_manifest_digest = baseline['manifest_sha256']
    local_relative = safe_relative(lock.get('local_output', ''))
    local_output = root / local_relative
    if not local_output.is_dir():
        raise SystemExit('reverified local candidate output directory is missing')
    try:
        committed_lock_bytes = subprocess.check_output([
            'git', '-C', str(repo), 'show',
            f"{lock['head_sha']}:fixtures/mooneye/candidate-digests.json",
        ])
    except subprocess.CalledProcessError as exc:
        raise SystemExit('qualified candidate lock revision is unavailable in local Git history') from exc
    verify_hosted_candidate_binding(lock, local_output, committed_lock_bytes)
    check_source_and_rights(live_manifest, lock, local_output)

    ids, counts, required_roms = current_denominator(live_manifest)
    if ids != baseline['eligible_ids'] or counts != {'cpu': 1, 'timer': 2} or required_roms != baseline['required_roms']:
        raise SystemExit('fixed pre-admission denominator changed before staging')
    candidate_by_id = {candidate['id']: candidate for candidate in lock['candidates']}
    if set(candidate_by_id) != set(ids):
        raise SystemExit('candidate digest lock does not cover the exact fixed eligible IDs')
    stage_base.mkdir(parents=True, exist_ok=True)
    staged = pathlib.Path(tempfile.mkdtemp(prefix='candidate-set-', dir=stage_base))
    staged_fixture_dir = staged / 'fixtures/mooneye'
    staged_fixture_dir.mkdir(parents=True)
    staged_manifest = json.loads((root / 'fixtures/mooneye/manifest.json').read_text())
    base_by_id = {item['id']: item for item in staged_manifest['fixtures'] if item.get('eligible') is True}
    if set(base_by_id) != set(ids):
        raise SystemExit('manifest IDs changed while staging')

    staged_roms = []
    for candidate_id in ids:
        candidate = candidate_by_id[candidate_id]
        fixture = base_by_id[candidate_id]
        rom_name = fixture['rom']
        if candidate.get('rom') != rom_name:
            raise SystemExit(f'candidate ROM mapping changed for {candidate_id}')
        local_rom = local_output / pathlib.Path(rom_name).stem / 'rebuilt.gb'
        raw = local_rom.read_bytes()
        if len(raw) != candidate['size_bytes'] or sha(raw) != candidate['sha256']:
            raise SystemExit(f'local candidate bytes differ from the lock: {rom_name}')
        fixture['sha256'] = candidate['sha256']
        fixture['size_bytes'] = candidate['size_bytes']
        fixture['build_recipe'] = [
            f"fetch Mooneye suite revision {lock['suite']['revision']} and verify tree {lock['suite']['tree_sha1']}",
            'generate the pinned 2032-byte zero replacement asset from fixtures/mooneye/font-source.c',
            f"apply the reviewed source-only headless report patch (SHA-256 {lock['harness_patch_sha256']})",
            f"assemble {fixture['source_path']} with pinned WLA-DX {lock['builder']['version']}",
            'link with wlalink -nS -d -S; -nS preserves source section order',
        ]
        fixture['candidate_derivation'] = {
            'original_rom_sha256': next(item['git_blob_sha256'] for item in baseline['roms'] if item['id'] == candidate_id),
            'harness_patch_sha256': lock['harness_patch_sha256'],
            'deterministic_linker_strategy': lock['strategy'],
            'deterministic_tool_patch_sha256': lock['builder'].get('deterministic_tool_patch_sha256'),
            'qualified_head_sha': lock['head_sha'],
            'hosted_run_id': lock['run_id'],
        }
        staged_path = staged_fixture_dir / rom_name
        staged_path.write_bytes(raw)
        staged_roms.append({'id': candidate_id, 'path': f'fixtures/mooneye/{rom_name}', 'sha256': sha(raw), 'size_bytes': len(raw)})
        fixture['preparation_outcome'] = 'Derived candidate passed the positive source callback and LD B,B result protocol; the induced DAA failure control also returned the six-0x42 result, with zero PPU bus accesses. This protocol probe is not full CPU-05 runner qualification.'

    staged_manifest['candidate_admission'] = {
        'status': 'qualified',
        'recipe_status': lock['recipe_status'],
        'qualification_status': lock['qualification_status'],
        'qualified_head_sha': lock['head_sha'],
        'hosted_run_id': lock['run_id'],
        'hosted_run_url': lock['run_url'],
        'candidate_lock_sha256': sha(lock_path.read_bytes()),
        'pre_admission_manifest_sha256': baseline_manifest_digest,
        'harness_patch_sha256': lock['harness_patch_sha256'],
        'deterministic_linker_strategy': lock['strategy'],
        'local_host': 'Darwin/arm64',
        'hosted_host': 'Linux/x86_64',
        'byte_identical_all_candidates': True,
        'eligible_ids': ids,
        'category_counts': {'cpu': 1, 'timer': 2},
    }
    raw_manifest = json.dumps(staged_manifest, indent=2, ensure_ascii=False) + '\n'
    staged_manifest_path = staged_fixture_dir / 'manifest.json'
    staged_manifest_path.write_bytes(raw_manifest.encode())
    staged_manifest_sha = sha(staged_manifest_path.read_bytes())

    parsed = json.loads(staged_manifest_path.read_bytes())
    staged_ids, staged_counts, staged_required = current_denominator(parsed)
    if staged_ids != ids or staged_counts != {'cpu': 1, 'timer': 2} or staged_required != required_roms:
        raise SystemExit('staged manifest changed the exact eligible IDs or one-CPU/two-timer denominator')
    admission = parsed.get('candidate_admission', {})
    if admission.get('candidate_lock_sha256') != sha(lock_path.read_bytes()):
        raise SystemExit('staged manifest candidate lock digest does not bind the qualification record')
    for staged_file in staged_roms:
        content = (staged / staged_file['path']).read_bytes()
        if sha(content) != staged_file['sha256'] or len(content) != staged_file['size_bytes']:
            raise SystemExit(f"staged ROM digest validation failed: {staged_file['path']}")
        live = next(item for item in parsed['fixtures'] if item.get('id') == staged_file['id'])
        if live.get('sha256') != staged_file['sha256'] or live.get('size_bytes') != staged_file['size_bytes']:
            raise SystemExit(f"staged manifest ROM metadata mismatch: {staged_file['path']}")
    if parsed['suite']['revision'] != lock['suite']['revision'] or parsed['builder']['source_revision'] != lock['builder']['revision'] or parsed['builder']['git_archive_sha256'] != lock['builder']['git_archive_sha256']:
        raise SystemExit('staged source/tool identity differs from the immutable lock')
    if sha((root / 'fixtures/mooneye/headless-report.patch').read_bytes()) != parsed['candidate_admission']['harness_patch_sha256']:
        raise SystemExit('staged manifest harness patch identity mismatch')
    if not (root / 'fixtures/mooneye/LICENSE.txt').is_file() or not (root / 'fixtures/mooneye/FONT-LICENSE.txt').is_file():
        raise SystemExit('staged candidate rights notices are missing')

    # Recheck the live baseline immediately before promotion; never overwrite a drifted corpus.
    verify_baseline(root)
    for staged_file in staged_roms:
        source = staged / staged_file['path']
        destination = root / staged_file['path']
        atomic_write(destination, source.read_bytes())
    atomic_write(root / baseline['manifest_path'], staged_manifest_path.read_bytes())
    print(json.dumps({
        'candidate_gate': 'admitted', 'qualification_head_sha': lock['head_sha'],
        'hosted_run_id': lock['run_id'], 'staged_manifest_sha256': staged_manifest_sha,
        'candidates': staged_roms, 'denominator': staged_counts,
        'stage_dir': staged.relative_to(root).as_posix(),
    }, indent=2))

if mode == '--assert-baseline':
    manifest = verify_baseline(root)
    print(json.dumps({'baseline': 'intact', 'manifest_sha256': baseline['manifest_sha256'], 'eligible_ids': baseline['eligible_ids'], 'category_counts': baseline['category_counts']}, indent=2))
elif mode == '--restore-and-verify':
    restore_baseline(root)
    print(json.dumps({'rollback': 'restored-and-verified', 'source_head': baseline['source_head'], 'manifest_sha256': baseline['manifest_sha256'], 'eligible_ids': baseline['eligible_ids'], 'category_counts': baseline['category_counts']}, indent=2))
elif mode == '--self-test-hosted-binding':
    self_test_hosted_candidate_binding()
    print(json.dumps({'hosted_binding_self_test': 'passed', 'tampered_lock_rejected': True, 'local_hosted_byte_mismatch_rejected': True}, indent=2))
elif mode == '--verify-hosted-binding':
    lock_path = root / 'fixtures/mooneye/candidate-digests.json'
    lock = json.loads(lock_path.read_bytes())
    local_output = root / safe_relative(lock.get('local_output', ''))
    try:
        committed_lock_bytes = subprocess.check_output([
            'git', '-C', str(repo), 'show',
            f"{lock['head_sha']}:fixtures/mooneye/candidate-digests.json",
        ])
    except (KeyError, subprocess.CalledProcessError) as exc:
        raise SystemExit('qualified candidate lock revision is unavailable in local Git history') from exc
    verify_hosted_candidate_binding(lock, local_output, committed_lock_bytes)
    print(json.dumps({'hosted_candidate_binding': 'verified', 'head_sha': lock['head_sha'], 'run_id': lock['run_id'], 'roms': 3}, indent=2))
elif mode == '--self-test-rollback':
    verify_baseline(root)
    self_test_hosted_candidate_binding()
    with tempfile.TemporaryDirectory(prefix='gabbaboy-mooneye-rollback-') as temp_text:
        temp_root = pathlib.Path(temp_text)
        for value in [baseline['manifest_path']] + [item['path'] for item in baseline['roms']]:
            relative = safe_relative(value)
            target = temp_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((root / relative).read_bytes())
        # Simulate a partial post-promotion mutation of manifest and all three ROM blobs.
        (temp_root / safe_relative(baseline['manifest_path'])).write_bytes(b'{"simulated":"post-promotion verifier failure"}\n')
        for item in baseline['roms']:
            target = temp_root / safe_relative(item['path'])
            raw = bytearray(target.read_bytes())
            raw[0] ^= 0xff
            target.write_bytes(raw)
        restore_baseline(temp_root)
    print(json.dumps({'rollback_self_test': 'passed', 'hosted_binding_self_test': 'passed', 'simulated_files': 4, 'manifest_sha256': baseline['manifest_sha256'], 'eligible_ids': baseline['eligible_ids'], 'category_counts': baseline['category_counts']}, indent=2))
elif mode == '--stage-validate-and-promote':
    stage_candidate_set()
PY
