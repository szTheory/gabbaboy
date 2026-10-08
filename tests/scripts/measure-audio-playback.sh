#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
BUILD_ROOT="${ROOT_DIR}/build/phase3-player"
APP_BUILD="${BUILD_ROOT}/gabbaboy"
PLAYER_BIN="${GBB_PLAYER_BIN:-${APP_BUILD}/gabbaboy-player}"
DEMO_ROM="${ROOT_DIR}/fixtures/visible-demo/demo.gb"
MANIFEST="${ROOT_DIR}/fixtures/visible-demo/manifest.json"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

[[ -x "$PLAYER_BIN" ]] || fail "player executable is missing: $PLAYER_BIN; run tests/scripts/verify-phase3-player.sh first"
[[ -s "$DEMO_ROM" && -s "$MANIFEST" ]] || fail 'the original visible-demo ROM or rights manifest is missing'
[[ -s "$APP_BUILD/CMakeCache.txt" ]] || fail 'the pinned player build cache is missing'
command -v python3 >/dev/null 2>&1 || fail 'python3 is required to hash PCM and validate the receipt'

python3 - "$ROOT_DIR" "$BUILD_ROOT" "$APP_BUILD" "$PLAYER_BIN" \
  "$DEMO_ROM" "$MANIFEST" "${GBB_AUDIO_MEASURE_TIMEOUT_SECONDS:-30}" <<'PY'
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile

root, build_root, app_build, player_bin, demo_rom, manifest_path, timeout_text = sys.argv[1:]
root = pathlib.Path(root)
build_root = pathlib.Path(build_root)
app_build = pathlib.Path(app_build)
player_bin = pathlib.Path(player_bin)
demo_rom = pathlib.Path(demo_rom)
timeout_seconds = int(timeout_text)
if timeout_seconds < 1 or timeout_seconds > 300:
    raise SystemExit('measurement timeout must be between 1 and 300 seconds per player route')

def require(condition, message):
    if not condition:
        raise SystemExit(message)

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def run(args, *, timeout, env, stdout=None, stderr=None):
    try:
        return subprocess.run(args, check=False, timeout=timeout, env=env,
                              stdout=stdout, stderr=stderr,
                              text=stdout == subprocess.PIPE or stdout is None)
    except subprocess.TimeoutExpired as error:
        raise SystemExit(f"player measurement timed out after {timeout}s: {' '.join(map(str, args))}") from error

revision = subprocess.check_output(
    ['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
require(len(revision) == 40 and all(c in '0123456789abcdef' for c in revision),
        'Git did not return a full lowercase source revision')
source_status = subprocess.check_output(
    ['git', '-C', str(root), 'status', '--porcelain', '--untracked-files=all', '--',
     'src', 'include', 'tests', 'docs', 'README.md', '.github'], text=True)
source_tree_state = 'dirty' if source_status.strip() else 'clean'
cache = (app_build / 'CMakeCache.txt').read_text(errors='replace').splitlines()
build_modes = [line.split('=', 1)[1] for line in cache
               if line.startswith('CMAKE_BUILD_TYPE:STRING=')]
require(len(build_modes) == 1 and build_modes[0] == 'Release',
        'the player must use the pinned Release build mode')
manifest = json.loads(pathlib.Path(manifest_path).read_text())
fixture_sha = digest(demo_rom)
require(demo_rom.stat().st_size == 32768 and manifest.get('size_bytes') == 32768 and
        manifest.get('sha256') == fixture_sha and manifest.get('license') ==
        'MIT; see LICENSE.txt and repository LICENSE',
        'the authored visible-demo fixture bytes or documented MIT rights do not match the manifest')

run_root = build_root / 'audio-measurement'
run_root.mkdir(parents=True, exist_ok=True)
work_dir = pathlib.Path(tempfile.mkdtemp(prefix=f'{revision[:12]}-', dir=run_root))
dummy_env = os.environ.copy()
dummy_env['SDL_AUDIO_DRIVER'] = 'dummy'

dummy = run([str(player_bin), '--audio-dummy-smoke'], timeout=timeout_seconds,
            env=dummy_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
dummy_output = dummy.stdout or ''
require(dummy.returncode == 0 and
        'audio dummy smoke passed: driver=dummy open/stream/close/recovery' in dummy_output,
        'the pinned dummy backend did not prove open/stream/close/recovery:\n' + dummy_output)

def parse_metrics(path):
    lines = path.read_text(errors='replace').splitlines()
    records = [line for line in lines if line.startswith('audio_measure ')]
    require(len(records) == 1, f'expected one audio_measure record in {path}')
    record = {}
    for field in records[0].split()[1:]:
        require('=' in field, f'malformed measurement field: {field}')
        key, value = field.split('=', 1)
        require(key not in record, f'duplicate measurement field: {key}')
        record[key] = value
    return record

required = {
    'model', 'workload', 'driver', 'duration_video_frames', 'duration_half_dots',
    'elapsed_half_dots', 'sample_rate_hz', 'pcm_format', 'sample_count',
    'ring_target_frames', 'ring_ceiling_frames', 'ring_high_water_frames',
    'app_pcm_underflow_frames', 'app_pcm_underflow_events',
    'producer_backpressure_events', 'intentionally_discarded_host_frames',
    'intentionally_discarded_host_partial_bytes', 'audio_stream_write_failures',
    'audio_stream_write_failure_pcm_bytes', 'sdl_queued_input_bytes',
}
target_half_dots = 300 * 140448
measured_runs = []
for partition in ('frame', '792'):
    pcm_path = work_dir / f'{partition}.pcm'
    metrics_path = work_dir / f'{partition}.metrics.txt'
    env = dummy_env.copy()
    env['GBB_AUDIO_BUILD_MODE'] = 'Release'
    with pcm_path.open('wb') as pcm, metrics_path.open('w') as metrics:
        result = run([str(player_bin), '--audio-measure', partition, str(demo_rom)],
                     timeout=timeout_seconds, env=env, stdout=pcm, stderr=metrics)
    require(result.returncode == 0,
            f'{partition} measurement route failed:\n{metrics_path.read_text(errors="replace")}')
    fields = parse_metrics(metrics_path)
    missing = required - fields.keys()
    require(not missing, f'{partition} receipt is missing fields: {sorted(missing)}')
    require(fields['model'] == 'DMG-CPU-B' and
            fields['workload'] == 'authored-pulse-control-loop-v1' and
            fields['driver'] == 'dummy' and fields['sample_rate_hz'] == '48000' and
            fields['pcm_format'] == 's16le_stereo',
            f'{partition} receipt mislabels the model, workload, sink, or PCM format')
    require(int(fields['duration_video_frames']) == 300 and
            int(fields['duration_half_dots']) == target_half_dots,
            f'{partition} measurement duration differs from the declared 300-frame workload')
    elapsed = int(fields['elapsed_half_dots'])
    require(target_half_dots <= elapsed <= target_half_dots + 40,
            f'{partition} guest elapsed time is outside the target plus 40-half-dot instruction bound')
    count = int(fields['sample_count'])
    byte_count = pcm_path.stat().st_size
    require(byte_count % 4 == 0 and count == byte_count // 4 and
            200000 <= count <= 260000,
            f'{partition} PCM byte length/count is inconsistent or outside 200000..260000 frames')
    require(int(fields['ring_target_frames']) == 1606 and
            int(fields['ring_ceiling_frames']) == 3214,
            f'{partition} receipt does not report the configured two/four-frame queue values')
    high_water = int(fields['ring_high_water_frames'])
    require(1 <= high_water <= 3214,
            f'{partition} ring high-water is outside 1..3214 frames')
    underflow_frames = int(fields['app_pcm_underflow_frames'])
    underflow_events = int(fields['app_pcm_underflow_events'])
    require(0 <= underflow_frames <= 48000 and 0 <= underflow_events <= 30000,
            f'{partition} application PCM underflow is outside the declared 0..48000 frames / 0..30000 callback events')
    backpressure = int(fields['producer_backpressure_events'])
    require(1 <= backpressure <= 30000,
            f'{partition} producer backpressure count is outside the declared 1..30000 event range')
    discarded = int(fields['intentionally_discarded_host_frames'])
    partial = int(fields['intentionally_discarded_host_partial_bytes'])
    require(0 <= discarded <= count and 0 <= partial <= 3,
            f'{partition} intentionally discarded host data exceeds produced PCM bounds')
    stream_failures = int(fields['audio_stream_write_failures'])
    stream_failure_bytes = int(fields['audio_stream_write_failure_pcm_bytes'])
    require(stream_failures == 0 and stream_failure_bytes == 0,
            f'{partition} SDL stream rejected writes: {stream_failures} failures / {stream_failure_bytes} PCM bytes')
    queued_bytes = int(fields['sdl_queued_input_bytes'])
    require(0 <= queued_bytes <= 65536,
            f'{partition} SDL queued-input byte count is outside the declared 0..65536 range')
    measured_runs.append({
        'partition': partition,
        'pcm_sha256': digest(pcm_path),
        'sample_count': count,
        'elapsed_half_dots': elapsed,
        'metrics': {key: int(value) if value.isdigit() else value
                    for key, value in fields.items()},
        'pcm_file': str(pcm_path),
    })

require(measured_runs[0]['pcm_sha256'] == measured_runs[1]['pcm_sha256'] and
        measured_runs[0]['sample_count'] == measured_runs[1]['sample_count'] and
        measured_runs[0]['elapsed_half_dots'] == measured_runs[1]['elapsed_half_dots'],
        'PCM digest, exact sample count, or elapsed guest time differs across frame and 792-half-dot partitions')

default_env = os.environ.copy()
default_env.pop('SDL_AUDIO_DRIVER', None)
default_env.pop('SDL_AUDIODRIVER', None)
default = run([str(player_bin), '--audio-device-status'], timeout=timeout_seconds,
              env=default_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
default_output = default.stdout or ''
require(default.returncode == 0 and 'default_audio_device=' in default_output,
        'default-device availability probe did not report its status:\n' + default_output)
default_status = next((part.split('=', 1)[1] for part in default_output.split()
                       if part.startswith('default_audio_device=')), None)
require(default_status in ('available', 'unavailable'),
        'default-device probe returned an unknown availability status')

source_receipt = {
    'schema_version': 1,
    'result': 'passed',
    'source_revision': revision,
    'source_tree_state': source_tree_state,
    'build_mode': build_modes[0],
    'platform': 'macos-arm64',
    'model': 'DMG-CPU-B scoped software model',
    'workload': {
        'id': 'authored-pulse-control-loop-v1',
        'duration_video_frames': 300,
        'duration_half_dots': target_half_dots,
        'source_fixture': 'fixtures/visible-demo/demo.gb',
        'source_fixture_sha256': fixture_sha,
        'fixture_license': 'MIT',
        'in_memory_program': 'originally authored NR52/NR50/NR51/pulse-one register setup followed by a bounded two-byte loop',
    },
    'sample_rate_hz': 48000,
    'pcm_format': 'signed 16-bit little-endian interleaved stereo',
    'pcm_sha256': measured_runs[0]['pcm_sha256'],
    'sample_count': measured_runs[0]['sample_count'],
    'ring_target_frames': 1606,
    'ring_ceiling_frames': 3214,
    'ring_high_water_frames': max(run['metrics']['ring_high_water_frames']
                                  for run in measured_runs),
    'application_pcm_underflow_frames_by_partition': {
        run['partition']: run['metrics']['app_pcm_underflow_frames']
        for run in measured_runs
    },
    'application_pcm_underflow_events_by_partition': {
        run['partition']: run['metrics']['app_pcm_underflow_events']
        for run in measured_runs
    },
    'producer_backpressure_events_by_partition': {
        run['partition']: run['metrics']['producer_backpressure_events']
        for run in measured_runs
    },
    'intentionally_discarded_host_frames_by_partition': {
        run['partition']: run['metrics']['intentionally_discarded_host_frames']
        for run in measured_runs
    },
    'audio_stream_write_failures_by_partition': {
        run['partition']: run['metrics']['audio_stream_write_failures']
        for run in measured_runs
    },
    'audio_stream_write_failure_pcm_bytes_by_partition': {
        run['partition']: run['metrics']['audio_stream_write_failure_pcm_bytes']
        for run in measured_runs
    },
    'sdl_queued_input_bytes_by_partition': {
        run['partition']: run['metrics']['sdl_queued_input_bytes']
        for run in measured_runs
    },
    'partition_runs': measured_runs,
    'dummy_backend_open_stream_close_recovery': 'passed',
    'default_audio_device_availability': default_status,
    'evidence_boundary': (
        'Dummy SDL and deterministic software counters only; queued input bytes are not latency, '
        'application PCM underflow is not hardware starvation, and no physical hotplug or '
        'perceptual audio result is claimed.'
    ),
}
receipt_path = work_dir / 'receipt.json'
source_receipt['receipt_path'] = str(receipt_path)
receipt_path.write_text(json.dumps(source_receipt, indent=2, sort_keys=True) + '\n')
print(json.dumps(source_receipt, indent=2, sort_keys=True))
PY
