#!/usr/bin/env bash
# Qualify the locally locked derived ROM bytes against an exact hosted Linux run.
set -euo pipefail

usage() {
  echo "usage: $0 --qualify-or-record-open|--verify-only --head SHA --branch BRANCH --local-dir DIR [--artifact-dir DIR]" >&2
  exit 2
}

mode=${1:-}
shift || usage
[[ "$mode" == --qualify-or-record-open || "$mode" == --verify-only ]] || usage
head_sha=''
branch=''
local_arg=''
artifact_arg=''
while (($#)); do
  case "$1" in
    --head) (($# >= 2)) || usage; head_sha=$2; shift 2 ;;
    --branch) (($# >= 2)) || usage; branch=$2; shift 2 ;;
    --local-dir) (($# >= 2)) || usage; local_arg=$2; shift 2 ;;
    --artifact-dir) (($# >= 2)) || usage; artifact_arg=$2; shift 2 ;;
    *) usage ;;
  esac
done
[[ "$head_sha" =~ ^[0-9a-f]{40}$ && -n "$branch" && -n "$local_arg" ]] || usage

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"
lock=fixtures/mooneye/candidate-digests.json
sources=fixtures/mooneye/SOURCES.md
workflow_path=.github/workflows/fixture-repro.yml
expected_branch=gsd/phase-02-dmg-cpu-bus-and-time
expected_run_path=.github/workflows/fixture-repro.yml
status_local=open
status_hosted=open
status_protocol=open
status_provenance=open
run_id=''
run_url=''
run_lock_sha=''
reason=''
gate='hosted'
comparison_json=''

sha256_file() { shasum -a 256 "$1" | cut -d ' ' -f 1; }

write_record() {
  local qualification=$1
  python3 - "$lock" "$sources" "$head_sha" "$run_id" "$run_url" "$qualification" \
    "$status_local" "$status_hosted" "$status_protocol" "$status_provenance" \
    "$gate" "$reason" "$run_lock_sha" "$comparison_json" "$local_arg" "$repo_root" <<'PY'
import hashlib
import json
import pathlib
import sys

(lock_path, sources_path) = map(pathlib.Path, sys.argv[1:3])
(head, run_id, run_url, qualification, local_status, hosted_status,
 protocol_status, provenance_status, gate, reason, lock_sha,
 comparison_path, local_arg, root) = sys.argv[3:]
root = pathlib.Path(root)
record = json.loads(lock_path.read_text())
record.update({
    'qualification_status': qualification,
    'head_sha': head or None,
    'run_id': int(run_id) if run_id.isdigit() else None,
    'run_url': run_url or None,
    'local_status': local_status,
    'hosted_status': hosted_status,
    'protocol_status': protocol_status,
    'provenance_status': provenance_status,
    'qualification_gate': gate,
    'open_reason': None if qualification == 'qualified' else reason,
})
if lock_sha:
    record['committed_lock_sha256'] = lock_sha
if comparison_path and pathlib.Path(comparison_path).exists():
    record['hosted_comparison'] = json.loads(pathlib.Path(comparison_path).read_text())
try:
    record['local_output'] = pathlib.Path(local_arg).as_posix()
except Exception:
    record['local_output'] = 'build/mooneye-candidate-local'
target = lock_path.with_suffix('.json.tmp')
target.write_text(json.dumps(record, indent=2) + '\n')
target.replace(lock_path)

sources_path = pathlib.Path(sources_path)
text = sources_path.read_text()
start = '<!-- BEGIN PLAN 02-17 candidate qualification -->'
end = '<!-- END PLAN 02-17 candidate qualification -->'
run = f'[{run_id}]({run_url})' if run_id.isdigit() and run_url else 'not available'
details = [
    start,
    '## Derived candidate cross-host qualification',
    '',
    f'- Gate: `{qualification}`; failed or pending gate: `{gate}`.',
    f'- Exact pushed source revision: `{head or "unavailable"}`.',
    f'- Hosted `fixture-repro.yml` run: {run}.',
    f'- Local candidate comparison: `{local_status}`; protocol probes: `{protocol_status}`; provenance/rights review: `{provenance_status}`; hosted Linux comparison: `{hosted_status}`.',
]
if qualification == 'qualified':
    details += ['- All three 32,768-byte candidate ROMs matched byte-for-byte between local Darwin/arm64 and the retained hosted Linux artifact at the exact source revision. The immutable original ROM digests and the one-CPU/two-timer denominator remain recorded separately.']
else:
    details += [f'- Open reason: {reason or "qualification has not completed"}. The checked-in ROMs, required manifest, and denominator remain at the captured pre-admission baseline.']
details += [end]
block = '\n'.join(details)
if start in text and end in text:
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    text = before.rstrip() + '\n\n' + block + after
else:
    text = text.rstrip() + '\n\n' + block + '\n'
sources_path.write_text(text)
PY
}

fail_open() {
  reason=$2
  gate=$1
  write_record open
  printf 'qualification_status=open gate=%s reason=%s\n' "$gate" "$reason" >&2
  exit 1
}

record_workflow_success() {
  run_id=$1
  run_url=$2
  status_hosted=qualified
  status_local=qualified
  status_protocol=qualified
  status_provenance=qualified
  gate=none
  reason=''
  write_record qualified
  echo "qualification_status=qualified head_sha=$head_sha run_id=$run_id"
}

[[ -s "$lock" ]] || { gate=recipe; reason='candidate digest lock is missing'; write_record open; exit 1; }
lock_status=$(jq -r '.recipe_status' "$lock")
if [[ "$mode" == --verify-only ]]; then
  run_id=$(jq -r '.run_id // empty' "$lock")
  run_url=$(jq -r '.run_url // empty' "$lock")
  run_lock_sha=$(jq -r '.committed_lock_sha256 // empty' "$lock")
fi
if [[ "$lock_status" != qualified ]]; then
  status_local=open
  fail_open recipe "local repeat recipe is $lock_status"
fi
[[ "$branch" == "$expected_branch" ]] || fail_open hosted "branch argument does not match the authorized Phase GB-02 branch"
[[ -f "$workflow_path" ]] || fail_open hosted 'fixture-repro workflow is missing from the worktree'

base_local="$local_arg"
if [[ "$base_local" == /* ]]; then
  [[ "$base_local" == "$repo_root/"* ]] || fail_open local 'local evidence path is outside the repository'
else
  base_local="$repo_root/$base_local"
fi
mkdir -p "$base_local"
if [[ -n "$(find "$base_local" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  local_dir=$(mktemp -d "$base_local/run.XXXXXXXX")
else
  local_dir=$base_local
fi
touch "$local_dir/.gabbaboy-plan17-evidence"
local_arg=$(python3 - "$local_dir" "$repo_root" <<'PY'
import pathlib, sys
path, root = map(pathlib.Path, sys.argv[1:])
print(path.relative_to(root).as_posix())
PY
)

if [[ "$mode" == --qualify-or-record-open ]]; then
  actual_head=$(git rev-parse HEAD)
  actual_branch=$(git symbolic-ref --quiet --short HEAD || echo DETACHED)
  [[ "$actual_head" == "$head_sha" ]] || fail_open hosted "requested head $head_sha is not current HEAD $actual_head"
  [[ "$actual_branch" == "$branch" ]] || fail_open hosted "current branch $actual_branch does not match requested branch $branch"
fi

export GBB_WLA_ORDERING_STRATEGY=source-order
if GBB_REPRO_OUTPUT_DIR="$local_dir" bash tests/scripts/reproduce-mooneye.sh --candidate-compare fixtures/mooneye > "$local_dir/local-reproduction.log" 2>&1; then
  status_local=qualified
else
  status_local=open
  fail_open local "local candidate comparison failed; inspect ${local_arg}/local-reproduction.log"
fi
if bash tests/scripts/probe-mooneye-candidate.sh > "$local_dir/protocol-probe.log" 2>&1; then
  status_protocol=qualified
else
  status_protocol=open
  fail_open protocol "positive or induced-negative protocol probe failed; inspect ${local_arg}/protocol-probe.log"
fi

if ! python3 - "$repo_root" "$local_dir" "$lock" <<'PY'
import hashlib
import json
import pathlib
import sys

root, work, lock_path = map(pathlib.Path, sys.argv[1:])
manifest_path = root / 'fixtures/mooneye/manifest.json'
manifest = json.loads(manifest_path.read_text())
lock = json.loads(lock_path.read_text())
eligible = [item for item in manifest['fixtures'] if item.get('eligible') is True]
if [item['id'] for item in eligible] != [item.get('id') for item in lock.get('candidates', [])]:
    raise SystemExit('eligible candidate IDs differ from the fixed candidate lock')
if len(eligible) != 3 or sum(item['category'] == 'cpu' for item in eligible) != 1 or sum(item['category'] == 'timer' for item in eligible) != 2:
    raise SystemExit('eligible denominator is not one CPU and two timers')
for filename in ('LICENSE.txt', 'FONT-LICENSE.txt', 'SOURCES.md', 'ELIGIBILITY.md', 'headless-report.patch'):
    if not (root / 'fixtures/mooneye' / filename).is_file():
        raise SystemExit(f'missing rights or source evidence: {filename}')
if 'MIT' not in (root / 'fixtures/mooneye/LICENSE.txt').read_text() or 'font' not in (root / 'fixtures/mooneye/FONT-LICENSE.txt').read_text().lower():
    raise SystemExit('upstream or replacement-font rights notice is incomplete')
patch = (root / 'fixtures/mooneye/headless-report.patch').read_text()
paths = set()
for line in patch.splitlines():
    if line.startswith('+++ b/'):
        paths.add(line[6:])
if paths != {'common/common.s', 'common/lib/quit.s'}:
    raise SystemExit(f'candidate patch changes unexpected source paths: {sorted(paths)}')
if hashlib.sha256((root / 'fixtures/mooneye/headless-report.patch').read_bytes()).hexdigest() != lock.get('harness_patch_sha256'):
    raise SystemExit('candidate harness patch digest differs from lock')
if lock.get('builder', {}).get('revision') != manifest['builder']['source_revision'] or lock.get('builder', {}).get('git_archive_sha256') != manifest['builder']['git_archive_sha256']:
    raise SystemExit('pinned builder identity differs from manifest')
if lock.get('suite', {}).get('revision') != manifest['suite']['revision'] or lock.get('suite', {}).get('tree_sha1') != manifest['suite']['tree_sha1']:
    raise SystemExit('pinned source identity differs from manifest')
source_tree = work / 'mooneye-source'
for fixture in eligible:
    if fixture.get('model') != 'DMG-CPU-B' or 'bootless' not in fixture.get('boot', '').lower() or fixture.get('timeout_half_dots', 0) <= 0:
        raise SystemExit(f'incomplete model, boot, or finite-budget metadata for {fixture["id"]}')
    for relative in fixture.get('source_closure', []):
        if not (source_tree / relative).is_file():
            raise SystemExit(f'source closure file missing at pinned source: {relative}')
for source_path, digest in lock.get('acceptance_source_sha256', {}).items():
    actual = hashlib.sha256((source_tree / source_path).read_bytes()).hexdigest()
    if actual != digest:
        raise SystemExit(f'upstream acceptance source changed: {source_path}')
if lock.get('replacement_asset', {}).get('rights_notice') != 'FONT-LICENSE.txt':
    raise SystemExit('replacement font rights notice is not bound to the lock')
PY
then
  status_provenance=open
  fail_open provenance 'source closure, rights, model, finite budget, or immutable source identity review failed'
fi
status_provenance=qualified

if [[ "$mode" == --verify-only ]]; then
  recorded_head=$(jq -r '.head_sha // empty' "$lock")
  run_id=$(jq -r '.run_id // empty' "$lock")
  run_url=$(jq -r '.run_url // empty' "$lock")
  run_lock_sha=$(jq -r '.committed_lock_sha256 // empty' "$lock")
  [[ "$recorded_head" == "$head_sha" ]] || fail_open hosted 'recorded qualification head does not match requested exact head'
  [[ "$run_id" =~ ^[0-9]+$ && "$run_lock_sha" =~ ^[0-9a-f]{64}$ ]] || fail_open hosted 'candidate lock lacks an exact hosted run or immutable lock digest'
fi

if ! command -v gh >/dev/null 2>&1 || ! gh auth status >/dev/null 2>&1; then
  status_hosted=open
  fail_open hosted 'GitHub CLI authentication is unavailable'
fi
repo_slug=$(gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null) || {
  status_hosted=open; fail_open hosted 'GitHub repository metadata could not be read';
}

get_exact_runs() {
  gh api -X GET "repos/$repo_slug/actions/workflows/fixture-repro.yml/runs" \
    -f branch="$branch" -f head_sha="$head_sha" -F per_page=100 2>/dev/null |
    jq -c --arg sha "$head_sha" --arg path "$expected_run_path" \
      '[.workflow_runs[] | select(.head_sha == $sha and .path == $path and (.event == "push" or .event == "workflow_dispatch"))] | sort_by(.created_at)'
}
get_run_by_id() {
  gh api "repos/$repo_slug/actions/runs/$1" 2>/dev/null
}

if [[ "$mode" == --qualify-or-record-open ]]; then
  if ! git push origin "$head_sha:refs/heads/$branch" > "$local_dir/push.log" 2>&1; then
    status_hosted=open
    fail_open hosted "exact revision push failed; inspect ${local_arg}/push.log"
  fi
  pushed_head=$(git ls-remote origin "refs/heads/$branch" 2>/dev/null | awk 'NR == 1 {print $1}')
  [[ "$pushed_head" == "$head_sha" ]] || fail_open hosted 'origin branch did not resolve to the exact pushed head'
  wait_seconds=${GBB_HOSTED_WAIT_SECONDS:-900}
  deadline=$(( $(date +%s) + wait_seconds ))
  dispatch_attempted=false
  while (( $(date +%s) < deadline )); do
    runs=$(get_exact_runs) || runs='[]'
    run=$(jq -c 'last // empty' <<< "$runs")
    if [[ -n "$run" ]]; then
      run_id=$(jq -r '.id' <<< "$run")
      run_url=$(jq -r '.html_url' <<< "$run")
      run_status=$(jq -r '.status' <<< "$run")
      run_conclusion=$(jq -r '.conclusion // empty' <<< "$run")
      if [[ "$run_status" == completed ]]; then break; fi
    elif [[ "$dispatch_attempted" == false && $(( $(date +%s) + wait_seconds - deadline )) -ge 60 ]]; then
      remote_head=$(git ls-remote origin "refs/heads/$branch" 2>/dev/null | awk 'NR == 1 {print $1}')
      [[ "$remote_head" == "$head_sha" ]] || fail_open hosted 'remote branch advanced before workflow dispatch'
      dispatch_attempted=true
      if ! gh workflow run fixture-repro.yml --ref "$branch" > "$local_dir/dispatch.log" 2>&1; then
        fail_open hosted 'workflow dispatch failed after the exact branch push'
      fi
    fi
    sleep 15
  done
  [[ -n "$run_id" ]] || fail_open hosted 'no exact-SHA fixture-repro workflow run appeared before timeout'
else
  run_id=$(jq -r '.run_id' "$lock")
  run_url=$(jq -r '.run_url' "$lock")
  run=$(get_run_by_id "$run_id") || fail_open hosted 'recorded hosted workflow run is unavailable'
  actual_run_head=$(jq -r '.head_sha // empty' <<< "$run")
  actual_run_path=$(jq -r '.path // empty' <<< "$run")
  actual_run_event=$(jq -r '.event // empty' <<< "$run")
  run_status=$(jq -r '.status // empty' <<< "$run")
  run_conclusion=$(jq -r '.conclusion // empty' <<< "$run")
  [[ "$actual_run_head" == "$head_sha" && "$actual_run_path" == "$expected_run_path" && ( "$actual_run_event" == push || "$actual_run_event" == workflow_dispatch ) ]] || fail_open hosted 'recorded hosted run event, path, or exact head SHA no longer matches'
fi

actual_run_head=${actual_run_head:-$(jq -r '.head_sha // empty' <<< "$run")}
actual_run_path=${actual_run_path:-$(jq -r '.path // empty' <<< "$run")}
if [[ "$actual_run_head" != "$head_sha" || "$actual_run_path" != "$expected_run_path" ]]; then
  fail_open hosted 'selected workflow run does not match the exact revision and workflow path'
fi
if [[ "${run_status:-}" != completed || "${run_conclusion:-}" != success ]]; then
  fail_open hosted "exact-SHA workflow did not complete successfully (status=${run_status:-unknown}, conclusion=${run_conclusion:-unknown})"
fi

artifact_dir=${artifact_arg:-$local_dir/hosted-artifact}
if [[ "$artifact_dir" != /* ]]; then artifact_dir="$repo_root/$artifact_dir"; fi
mkdir -p "$artifact_dir"
if ! gh run download "$run_id" --name mooneye-candidate-evidence --dir "$artifact_dir" > "$local_dir/artifact-download.log" 2>&1; then
  fail_open hosted 'mooneye-candidate-evidence artifact is unavailable for the exact run'
fi
artifact_lock="$artifact_dir/candidate-digests.json"
artifact_report="$artifact_dir/candidate-comparison.json"
[[ -s "$artifact_lock" && -s "$artifact_report" ]] || fail_open hosted 'candidate artifact is missing its digest lock or comparison report'

if [[ "$mode" == --qualify-or-record-open ]]; then
  run_lock_sha=$(sha256_file "$lock")
else
  run_lock_sha=$(jq -r '.committed_lock_sha256' "$lock")
fi

comparison_json="$local_dir/hosted-comparison.json"
if ! python3 - "$repo_root" "$local_dir" "$artifact_dir" "$artifact_lock" "$artifact_report" "$head_sha" "$run_lock_sha" "$run_id" "$comparison_json" <<'PY'
import hashlib
import json
import pathlib
import sys

root, local_dir, artifact_dir, artifact_lock_path, artifact_report_path = map(pathlib.Path, sys.argv[1:6])
head, expected_lock_sha, run_id, output_path = sys.argv[6:]
lock_path = root / 'fixtures/mooneye/candidate-digests.json'
expected_lock = json.loads(lock_path.read_text())
hosted_lock_bytes = artifact_lock_path.read_bytes()
if hashlib.sha256(hosted_lock_bytes).hexdigest() != expected_lock_sha:
    raise SystemExit('retained artifact candidate lock is not the exact committed lock used by the run')
hosted_lock = json.loads(hosted_lock_bytes)
hosted_report = json.loads(artifact_report_path.read_text())
if hosted_report.get('head_sha') != head or hosted_report.get('local_status') != 'qualified' or hosted_report.get('host') != 'Linux/x86_64':
    raise SystemExit('hosted comparison report does not bind the exact Linux revision or pass status')
if hosted_lock.get('recipe_status') != 'qualified' or hosted_lock.get('candidates') != expected_lock.get('candidates'):
    raise SystemExit('hosted candidate lock differs from the committed local candidate lock')
provenance = artifact_dir / 'provenance'
for filename in ('manifest.json', 'pre-admission-baseline.json', 'headless-report.patch', 'font-source.c', 'LICENSE.txt', 'FONT-LICENSE.txt', 'ELIGIBILITY.md', 'SOURCES.md'):
    if not (provenance / filename).is_file():
        raise SystemExit(f'hosted artifact is missing provenance file {filename}')
if hashlib.sha256((provenance / 'headless-report.patch').read_bytes()).hexdigest() != expected_lock.get('harness_patch_sha256'):
    raise SystemExit('hosted harness patch digest mismatch')
if hashlib.sha256((provenance / 'font-source.c').read_bytes()).hexdigest() != expected_lock.get('replacement_asset', {}).get('font_source_sha256'):
    raise SystemExit('hosted replacement font source digest mismatch')
inputs = {}
for line in (artifact_dir / 'inputs.txt').read_text().splitlines():
    if '=' in line:
        key, value = line.split('=', 1)
        inputs[key] = value
identity = {
    'run_revision': head,
    'suite_revision': expected_lock['suite']['revision'],
    'suite_tree': expected_lock['suite']['tree_sha1'],
    'tool_revision': expected_lock['builder']['revision'],
    'tool_tree': expected_lock['builder']['tree_sha1'],
    'tool_archive_sha256': expected_lock['builder']['git_archive_sha256'],
    'font_source_sha256': expected_lock['replacement_asset']['font_source_sha256'],
    'font_sha256': expected_lock['replacement_asset']['font_sha256'],
    'candidate_patch_sha256': expected_lock['harness_patch_sha256'],
    'deterministic_strategy': expected_lock['strategy_id'],
    'deterministic_tool_patch_sha256': 'none',
}
for key, value in identity.items():
    if inputs.get(key) != value:
        raise SystemExit(f'hosted recipe identity mismatch for {key}: {inputs.get(key)} != {value}')
if inputs.get('link_flags') != '-nS -d -S <link> <rom>':
    raise SystemExit('hosted linker flags differ from the deterministic candidate recipe')
source_lines = {}
for line in (artifact_dir / 'acceptance-sources.sha256').read_text().splitlines():
    source, digest = line.split(' ', 1)
    source_lines[source] = digest
if source_lines != expected_lock.get('acceptance_source_sha256'):
    raise SystemExit('hosted upstream acceptance source digests differ from the lock')
cases = []
for item in expected_lock.get('candidates', []):
    name = item['rom']
    local_rom = local_dir / name.removesuffix('.gb') / 'rebuilt.gb'
    hosted_rom = artifact_dir / name.removesuffix('.gb') / 'rebuilt.gb'
    if not local_rom.is_file() or not hosted_rom.is_file():
        cases.append({'rom': name, 'byte_identical': False, 'reason': 'local or hosted ROM missing'})
        continue
    for evidence_file in ('rebuilt.sym', 'comparison.json', 'source.txt'):
        if not (artifact_dir / name.removesuffix('.gb') / evidence_file).is_file():
            raise SystemExit(f'hosted candidate evidence is missing {name}/{evidence_file}')
    local_bytes, hosted_bytes = local_rom.read_bytes(), hosted_rom.read_bytes()
    offsets = [i for i in range(max(len(local_bytes), len(hosted_bytes))) if i >= len(local_bytes) or i >= len(hosted_bytes) or local_bytes[i] != hosted_bytes[i]]
    local_sha, hosted_sha = hashlib.sha256(local_bytes).hexdigest(), hashlib.sha256(hosted_bytes).hexdigest()
    same = local_bytes == hosted_bytes and local_sha == item['sha256'] and hosted_sha == item['sha256'] and len(local_bytes) == item['size_bytes'] and len(hosted_bytes) == item['size_bytes']
    case = {
        'rom': name, 'local_sha256': local_sha, 'hosted_sha256': hosted_sha,
        'local_size_bytes': len(local_bytes), 'hosted_size_bytes': len(hosted_bytes),
        'byte_identical': same, 'different_byte_count': len(offsets),
        'first_difference': offsets[0] if offsets else None,
    }
    cases.append(case)
    (artifact_dir / name.removesuffix('.gb') / 'local-byte-comparison.json').write_text(json.dumps(case, indent=2) + '\n')
record = {
    'head_sha': head, 'run_id': int(run_id), 'host': hosted_report.get('host'),
    'workflow_path': '.github/workflows/fixture-repro.yml', 'cases': cases,
    'byte_identical': len(cases) == 3 and all(case.get('byte_identical') for case in cases),
}
pathlib.Path(output_path).write_text(json.dumps(record, indent=2) + '\n')
if not record['byte_identical']:
    raise SystemExit('one or more hosted candidate ROM byte streams differ from the local builds')
PY
then
  status_hosted=open
  fail_open hosted 'hosted candidate bytes, recipe identity, or retained source provenance did not match the local evidence'
fi

if [[ "$mode" == --verify-only ]]; then
  record_workflow_success "$run_id" "$run_url"
else
  record_workflow_success "$run_id" "$run_url"
fi
