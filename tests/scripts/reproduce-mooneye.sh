#!/usr/bin/env bash
# Explicit, networked fixture preparation. Ordinary CTest uses checked-in ROMs.
set -euo pipefail

if [[ $# != 2 || ( $1 != --diagnose && $1 != --compare && $1 != --candidate &&
    $1 != --capture-baseline && $1 != --candidate-repeat-check &&
    $1 != --candidate-compare ) ]]; then
  echo "usage: $0 --diagnose|--compare|--candidate|--capture-baseline|--candidate-repeat-check|--candidate-compare fixtures/mooneye" >&2
  exit 2
fi
mode=$1
fixture_dir=$(cd "$2" && pwd -P)
repo_root=$(git rev-parse --show-toplevel)
[[ "$fixture_dir" == "$repo_root/fixtures/mooneye" ]] || { echo 'unexpected fixture directory' >&2; exit 2; }

sha256_file() { shasum -a 256 "$1" | cut -d ' ' -f 1; }

if [[ "$mode" == --capture-baseline ]]; then
  python3 - "$repo_root" "$fixture_dir" <<'PY'
import hashlib
import json
import pathlib
import subprocess
import sys

root, fixture_dir = map(pathlib.Path, sys.argv[1:])
head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
manifest_path = 'fixtures/mooneye/manifest.json'
manifest_bytes = subprocess.check_output(['git', '-C', str(root), 'show', f'{head}:{manifest_path}'])
manifest = json.loads(manifest_bytes)
eligible = [fixture for fixture in manifest['fixtures'] if fixture.get('eligible') is True]
ids = [fixture['id'] for fixture in eligible]
counts = {}
for fixture in eligible:
    counts[fixture['category']] = counts.get(fixture['category'], 0) + 1
expected_ids = [
    'mooneye-acceptance-instr-daa',
    'mooneye-acceptance-timer-tim00',
    'mooneye-acceptance-timer-tim00-div-trigger',
]
if ids != expected_ids or counts != {'cpu': 1, 'timer': 2}:
    raise SystemExit(f'unexpected eligible denominator: ids={ids}, category_counts={counts}')
if (fixture_dir / 'manifest.json').read_bytes() != manifest_bytes:
    raise SystemExit('working manifest differs from committed source HEAD')
roms = []
for fixture in eligible:
    path = f"fixtures/mooneye/{fixture['rom']}"
    content = subprocess.check_output(['git', '-C', str(root), 'show', f'{head}:{path}'])
    if (root / path).read_bytes() != content:
        raise SystemExit(f'working ROM differs from committed source HEAD: {path}')
    digest = hashlib.sha256(content).hexdigest()
    if digest != fixture['sha256'] or len(content) != fixture['size_bytes']:
        raise SystemExit(f'ROM does not match committed manifest: {path}')
    roms.append({
        'id': fixture['id'], 'category': fixture['category'], 'path': path,
        'size_bytes': len(content), 'git_blob_sha256': digest,
        'manifest_sha256': fixture['sha256'],
    })
baseline = {
    'schema_version': 1, 'source_head': head, 'manifest_path': manifest_path,
    'manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(),
    'eligible_ids': ids, 'category_counts': counts,
    'required_roms': manifest['required_roms'], 'roms': roms,
}
target = fixture_dir / 'pre-admission-baseline.json'
temp = target.with_suffix('.json.tmp')
temp.write_text(json.dumps(baseline, indent=2) + '\n')
temp.replace(target)
print(json.dumps(baseline, indent=2))
PY
  exit 0
fi

work_dir=${GBB_REPRO_OUTPUT_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-mooneye.XXXXXXXX")}
mkdir -p "$work_dir"
work_dir=$(cd "$work_dir" && pwd -P)
echo "Evidence directory: $work_dir"
manifest="$fixture_dir/manifest.json"
candidate_lock="$fixture_dir/candidate-digests.json"
is_candidate=false
strategy=${GBB_WLA_ORDERING_STRATEGY:-source-order}
REPEAT_LOCK_WRITTEN=false
case "$mode" in
  --candidate|--candidate-repeat-check|--candidate-compare) is_candidate=true ;;
esac
if [[ "$is_candidate" == true && "$strategy" != source-order && "$strategy" != stable-total-order-patch ]]; then
  echo "unknown deterministic WLA-DX strategy: $strategy" >&2
  exit 2
fi

record_repeat_failure() {
  local status=$?
  if [[ "$mode" != --candidate-repeat-check || $status == 0 || "$REPEAT_LOCK_WRITTEN" == true ]]; then
    return
  fi
  python3 - "$candidate_lock" "$status" "${GBB_LAST_FAILED_COMMAND:-recipe setup/build failed}" <<'PY'
import json
import pathlib
import sys
path, status, command = sys.argv[1:]
record = {
    'schema_version': 1, 'strategy': 'wlalink -nS source-order',
    'recipe_status': 'open', 'local_status': 'open',
    'hosted_status': 'open', 'protocol_status': 'open',
    'provenance_status': 'open', 'qualification_status': 'open',
    'open_reason': f'Local deterministic recipe command failed (status {status}): {command}',
    'candidates': [],
}
target = pathlib.Path(path)
temp = target.with_suffix('.json.tmp')
temp.write_text(json.dumps(record, indent=2) + '\n')
temp.replace(target)
PY
  trap - EXIT ERR
  exit 0
}
trap record_repeat_failure EXIT
trap 'GBB_LAST_FAILED_COMMAND=$BASH_COMMAND' ERR

suite_rev=$(jq -r '.suite.revision' "$manifest")
suite_tree=$(jq -r '.suite.tree_sha1' "$manifest")
tool_rev=$(jq -r '.builder.source_revision' "$manifest")
tool_tree=$(jq -r '.builder.source_tree_sha1' "$manifest")
tool_archive=$(jq -r '.builder.git_archive_sha256' "$manifest")
font_digest=$(jq -r '.replacement_asset.sha256' "$manifest")
[[ "$suite_rev" == 31510e12eea6286d36eea060a6adde755e1067aa &&
   "$suite_tree" == 2b8c52424a49a2a7466cf631fd8992c53d0de2fa &&
   "$tool_rev" == 91c52b1f4ef3cc8ba3c0638f7536539579af6a9f &&
   "$tool_tree" == 8495d61b96847950e65b1809bf9c7daaccdbd20b &&
   "$tool_archive" == 24a95d77a79feeb70d1de87d66749c006e37337308ce9c00e44efac4c46ab976 &&
   "$font_digest" == 23ba65cb93433b65e7ddcae5f8a7dd2ca232491793848644e625875c6dd6ae43 ]] || {
  echo 'manifest input pin differs from reviewed recipe' >&2; exit 1;
}
pin_sha() {
  local actual
  actual=$(sha256_file "$1")
  [[ "$actual" == "$2" ]] || { echo "SHA-256 pin failure: $1 expected $2 actual $actual" >&2; exit 1; }
}
fetch_source() {
  local name=$1 url=$2 revision=$3 tree=$4
  local git_dir="$work_dir/$name-git" source_dir="$work_dir/$name-source"
  git init -q "$git_dir"
  git -C "$git_dir" remote add origin "$url"
  git -C "$git_dir" fetch -q --depth=1 origin "$revision"
  [[ $(git -C "$git_dir" rev-parse FETCH_HEAD) == "$revision" ]]
  git -C "$git_dir" checkout -q --detach FETCH_HEAD
  [[ $(git -C "$git_dir" rev-parse HEAD^{tree}) == "$tree" ]] || { echo "$name tree pin failure" >&2; exit 1; }
  git -C "$git_dir" archive --output="$work_dir/$name-source.tar" HEAD
  mkdir -p "$source_dir"
  tar -xf "$work_dir/$name-source.tar" -C "$source_dir"
}
pin_sha "$fixture_dir/font-source.c" 5e5b21a1ff66f226e0e3d3ea1630ad4e2d16edbc9fcbb76b70a26b44c2271f52
fetch_source wla-dx https://github.com/vhelin/wla-dx.git "$tool_rev" "$tool_tree"
pin_sha "$work_dir/wla-dx-source.tar" "$tool_archive"
fetch_source mooneye https://github.com/Gekkio/mooneye-test-suite.git "$suite_rev" "$suite_tree"

tool_patch_digest=none
if [[ "$is_candidate" == true && "$strategy" == stable-total-order-patch ]]; then
  patch_file="$fixture_dir/wla-dx-deterministic.patch"
  tool_patch_digest=$(sha256_file "$patch_file")
  (cd "$work_dir/wla-dx-source" && patch --batch --fuzz=0 -p1 < "$patch_file") > "$work_dir/tool-patch.log"
fi
cmake -S "$work_dir/wla-dx-source" -B "$work_dir/wla-dx-build" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$work_dir/wla-dx-install" > "$work_dir/cmake-configure.log"
cmake --build "$work_dir/wla-dx-build" --config Release --target wla-gb wlalink -j4 > "$work_dir/cmake-build.log"
assembler="$work_dir/wla-dx-build/binaries/wla-gb"
linker="$work_dir/wla-dx-build/binaries/wlalink"
assembler_version=$("$assembler" 2>&1 | grep -F '$VER:' | head -n 1 || true)
linker_version=$("$linker" 2>&1 | grep -F '$VER:' | head -n 1 || true)
[[ "$assembler_version" == *'wla-gb 10.7 (28.6.2026)'* &&
   "$linker_version" == *'wlalink 5.22 (28.6.2026)'* ]] || { echo 'WLA-DX version pin failure' >&2; exit 1; }

source_dir="$work_dir/mooneye-source"
common_dir="$source_dir/common"
cc -std=c17 -O2 "$fixture_dir/font-source.c" -o "$work_dir/font-source"
"$work_dir/font-source" "$common_dir/font.bin"
pin_sha "$common_dir/font.bin" "$font_digest"
patch_digest=none
if [[ "$is_candidate" == true ]]; then
  patch_file="$fixture_dir/headless-report.patch"
  patch_digest=$(sha256_file "$patch_file")
  (cd "$source_dir" && patch --batch --fuzz=0 -p1 < "$patch_file") > "$work_dir/patch.log"
  for source_path in acceptance/instr/daa.s acceptance/timer/tim00.s acceptance/timer/tim00_div_trigger.s; do
    upstream_sha=$(git -C "$work_dir/mooneye-git" show "HEAD:$source_path" | shasum -a 256 | cut -d ' ' -f 1)
    local_sha=$(sha256_file "$source_dir/$source_path")
    [[ "$upstream_sha" == "$local_sha" ]] || { echo "acceptance source changed: $source_path" >&2; exit 1; }
    printf '%s %s\n' "$source_path" "$upstream_sha" >> "$work_dir/acceptance-sources.sha256"
  done
fi

link_flags=(-d -S)
if [[ "$is_candidate" == true ]]; then
  if [[ "$strategy" == source-order ]]; then link_flags=(-nS -d -S); fi
  printf 'candidate_patch_sha256=%s\n' "$patch_digest" > "$work_dir/candidate.txt"
  printf 'candidate_source_revision=%s\n' "$suite_rev" >> "$work_dir/candidate.txt"
fi
{
  printf 'host=%s\n' "$(uname -s)/$(uname -m)"
  printf 'run_revision=%s\n' "$(git rev-parse HEAD)"
  printf 'suite_revision=%s\nsuite_tree=%s\n' "$suite_rev" "$suite_tree"
  printf 'tool_revision=%s\ntool_tree=%s\ntool_archive_sha256=%s\n' "$tool_rev" "$tool_tree" "$tool_archive"
  printf 'font_source_sha256=%s\nfont_sha256=%s\n' "$(sha256_file "$fixture_dir/font-source.c")" "$font_digest"
  if [[ "$is_candidate" == true ]]; then
    printf 'candidate_patch_sha256=%s\n' "$patch_digest"
    printf 'deterministic_strategy=%s\ndeterministic_tool_patch_sha256=%s\n' "$strategy" "$tool_patch_digest"
  fi
  printf 'assembler=%s\nlinker=%s\n' "$assembler_version" "$linker_version"
  printf 'cmake_flags=-DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=<workspace>/wla-dx-install\n'
  printf 'font_flags=cc -std=c17 -O2\nassembly_flags=-I <suite>/common -o <object> <source>\n'
  if [[ "$is_candidate" == true ]]; then
    printf 'link_flags=%s\n' "${link_flags[*]} <link> <rom>"
  else
    printf 'link_flags=-d -S <link> <rom>\n'
  fi
} > "$work_dir/inputs.txt"
cat "$work_dir/inputs.txt"

build_set() {
  local output_root=$1
  mkdir -p "$output_root"
  for case_name in daa tim00 tim00_div_trigger; do
    if [[ "$case_name" == daa ]]; then source_path=acceptance/instr/daa.s; else source_path="acceptance/timer/$case_name.s"; fi
    case_dir="$output_root/$case_name"
    mkdir -p "$case_dir"
    object="$case_dir/$case_name.o"
    link_file="$case_dir/$case_name.link"
    rom="$case_dir/rebuilt.gb"
    "$assembler" -I "$common_dir" -o "$object" "$source_dir/$source_path" > "$case_dir/assembler.log" 2>&1
    printf '[objects]\n%s\n' "$object" > "$link_file"
    "$linker" "${link_flags[@]}" "$link_file" "$rom" > "$case_dir/linker.log" 2>&1
    printf 'source_path=%s\nsource_sha256=%s\n' "$source_path" "$(sha256_file "$source_dir/$source_path")" > "$case_dir/source.txt"
  done
}

if [[ "$mode" == --candidate-repeat-check ]]; then
  build_set "$work_dir/repeat-1"
  build_set "$work_dir/repeat-2"
  python3 - "$repo_root" "$fixture_dir" "$work_dir" "$strategy" "$tool_rev" "$tool_tree" "$tool_archive" "$suite_rev" "$suite_tree" "$font_digest" "$patch_digest" "$tool_patch_digest" <<'PY'
import hashlib
import json
import pathlib
import subprocess
import sys

(root, fixture_dir, work_dir) = map(pathlib.Path, sys.argv[1:4])
strategy, tool_rev, tool_tree, tool_archive, suite_rev, suite_tree, font_sha, harness_sha, tool_patch_sha = sys.argv[4:]
manifest = json.loads((fixture_dir / 'manifest.json').read_text())
original = []
by_rom = {item['rom']: item for item in manifest['fixtures']}
source_hashes = {}
for name in ('daa', 'tim00', 'tim00_div_trigger'):
    fixture = by_rom[name + '.gb']
    path = f"fixtures/mooneye/{name}.gb"
    raw = subprocess.check_output(['git', '-C', str(root), 'show', f"HEAD:{path}"])
    original.append({'id': fixture['id'], 'rom': name + '.gb', 'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw)})
    source_path = {'daa': 'acceptance/instr/daa.s'}.get(name, f'acceptance/timer/{name}.s')
    source_hashes[source_path] = (work_dir / 'acceptance-sources.sha256').read_text().split(source_path + ' ', 1)[1].splitlines()[0]

candidates = []
comparison = []
for name in ('daa', 'tim00', 'tim00_div_trigger'):
    one = (work_dir / 'repeat-1' / name / 'rebuilt.gb').read_bytes()
    two = (work_dir / 'repeat-2' / name / 'rebuilt.gb').read_bytes()
    sha_one, sha_two = hashlib.sha256(one).hexdigest(), hashlib.sha256(two).hexdigest()
    same = one == two
    candidates.append({'id': by_rom[name + '.gb']['id'], 'rom': name + '.gb', 'sha256': sha_one, 'size_bytes': len(one), 'repeat_sha256': sha_two, 'repeat_size_bytes': len(two)})
    offsets = [i for i in range(max(len(one), len(two))) if i >= len(one) or i >= len(two) or one[i] != two[i]]
    case_report = {'rom': name + '.gb', 'first_sha256': sha_one, 'repeat_sha256': sha_two, 'first_size_bytes': len(one), 'repeat_size_bytes': len(two), 'byte_identical': same, 'different_byte_count': len(offsets), 'first_difference': offsets[0] if offsets else None}
    comparison.append(case_report)
    (work_dir / 'repeat-1' / name / 'repeat-comparison.json').write_text(json.dumps(case_report, indent=2) + '\n')
    (work_dir / 'repeat-1' / name / 'repeat-2.gb').write_bytes(two)
    print(json.dumps(case_report, sort_keys=True))

recipe_status = 'qualified' if all(case['byte_identical'] for case in comparison) else 'open'
reason = None if recipe_status == 'qualified' else 'One or more candidate ROMs differ between two complete local builds.'
script_sha = hashlib.sha256((root / 'tests/scripts/reproduce-mooneye.sh').read_bytes()).hexdigest()
lock = {
    'schema_version': 1,
    'strategy': ('wlalink -nS preserves input appearance order' if strategy == 'source-order' else 'pinned total-order linker patch'),
    'strategy_id': strategy,
    'recipe_status': recipe_status,
    'local_status': recipe_status,
    'hosted_status': 'open',
    'protocol_status': 'open',
    'provenance_status': 'open',
    'qualification_status': 'open',
    'open_reason': reason or 'Hosted exact-SHA comparison and protocol/provenance gates are pending.',
    'source_head': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
    'recipe_script_sha256': script_sha,
    'suite': {'revision': suite_rev, 'tree_sha1': suite_tree, 'license': manifest['suite']['license']},
    'builder': {'revision': tool_rev, 'tree_sha1': tool_tree, 'git_archive_sha256': tool_archive, 'version': manifest['builder']['version'], 'deterministic_tool_patch_sha256': None if tool_patch_sha == 'none' else tool_patch_sha},
    'replacement_asset': {'font_source_sha256': hashlib.sha256((fixture_dir / 'font-source.c').read_bytes()).hexdigest(), 'font_sha256': font_sha, 'rights_notice': 'FONT-LICENSE.txt'},
    'harness_patch_sha256': harness_sha,
    'acceptance_source_sha256': source_hashes,
    'original_candidates': original,
    'local_comparison': comparison,
    'candidates': candidates,
}
(work_dir / 'candidate-digests.json').write_text(json.dumps(lock, indent=2) + '\n')
target = fixture_dir / 'candidate-digests.json'
temp = target.with_suffix('.json.tmp')
temp.write_text(json.dumps(lock, indent=2) + '\n')
temp.replace(target)
print(f'recipe_status={recipe_status}')
PY
  REPEAT_LOCK_WRITTEN=true
  # An open deterministic recipe is a recorded outcome, not an execution error.
  trap - EXIT ERR
  jq . "$candidate_lock"
  exit 0
fi

build_set "$work_dir"
if [[ "$is_candidate" == true ]]; then
  case "$mode" in
    --candidate)
      for case_name in daa tim00 tim00_div_trigger; do
        printf 'candidate=%s sha256=%s\n' "$case_name" "$(sha256_file "$work_dir/$case_name/rebuilt.gb")"
      done
      exit 0
      ;;
    --candidate-compare)
      [[ -s "$candidate_lock" ]] || { echo 'missing provisional candidate digest lock' >&2; exit 1; }
      python3 - "$repo_root" "$fixture_dir" "$work_dir" "$candidate_lock" <<'PY'
import hashlib
import json
import pathlib
import sys

root, fixture_dir, work_dir, lock_path = map(pathlib.Path, sys.argv[1:])
lock = json.loads(lock_path.read_text())
manifest = json.loads((fixture_dir / 'manifest.json').read_text())
if lock.get('recipe_status') != 'qualified' or lock.get('strategy_id') not in ('source-order', 'stable-total-order-patch'):
    raise SystemExit('candidate recipe is not locally qualified')
if lock.get('strategy_id') != __import__('os').environ.get('GBB_WLA_ORDERING_STRATEGY', 'source-order'):
    raise SystemExit('candidate ordering strategy differs from the provisional digest lock')
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
if lock.get('recipe_script_sha256') != sha(root / 'tests/scripts/reproduce-mooneye.sh'):
    raise SystemExit('reproduction script identity differs from the provisional digest lock')
if lock.get('harness_patch_sha256') != sha(fixture_dir / 'headless-report.patch'):
    raise SystemExit('candidate harness patch identity differs from the provisional digest lock')
if lock.get('replacement_asset', {}).get('font_source_sha256') != sha(fixture_dir / 'font-source.c') or lock.get('replacement_asset', {}).get('font_sha256') != manifest.get('replacement_asset', {}).get('sha256'):
    raise SystemExit('font source or replacement asset identity differs from the provisional digest lock')
if lock.get('suite', {}).get('revision') != manifest.get('suite', {}).get('revision') or lock.get('suite', {}).get('tree_sha1') != manifest.get('suite', {}).get('tree_sha1'):
    raise SystemExit('Mooneye suite identity differs from the provisional digest lock')
if lock.get('builder', {}).get('revision') != manifest.get('builder', {}).get('source_revision') or lock.get('builder', {}).get('tree_sha1') != manifest.get('builder', {}).get('source_tree_sha1') or lock.get('builder', {}).get('git_archive_sha256') != manifest.get('builder', {}).get('git_archive_sha256'):
    raise SystemExit('WLA-DX source/archive identity differs from the provisional digest lock')
locked_sources = lock.get('acceptance_source_sha256', {})
actual_sources = {}
for line in (work_dir / 'acceptance-sources.sha256').read_text().splitlines():
    source_path, digest = line.split(' ', 1)
    actual_sources[source_path] = digest
if actual_sources != locked_sources:
    raise SystemExit('upstream acceptance source digests differ from the provisional digest lock')
by_name = {item['rom']: item for item in lock.get('candidates', [])}
comparison = []
failed = False
for name in ('daa', 'tim00', 'tim00_div_trigger'):
    case_dir = work_dir / name
    actual = (case_dir / 'rebuilt.gb').read_bytes()
    expected = by_name.get(name + '.gb')
    actual_sha = hashlib.sha256(actual).hexdigest()
    match = expected is not None and len(actual) == expected.get('size_bytes') and actual_sha == expected.get('sha256')
    offsets = []
    if expected is not None:
        # The lock's candidate bytes are transported separately in the same task workspace.
        reference_path = work_dir / 'expected' / (name + '.gb')
        if reference_path.exists():
            reference = reference_path.read_bytes()
            offsets = [i for i in range(max(len(actual), len(reference))) if i >= len(actual) or i >= len(reference) or actual[i] != reference[i]]
        else:
            offsets = [] if match else [-1]
    report = {
        'rom': name + '.gb', 'expected_sha256': expected.get('sha256') if expected else None,
        'actual_sha256': actual_sha, 'expected_size_bytes': expected.get('size_bytes') if expected else None,
        'actual_size_bytes': len(actual), 'lock_match': match,
        'different_byte_count': len(offsets) if offsets and offsets[0] >= 0 else (0 if match else None),
        'first_difference': offsets[0] if offsets and offsets[0] >= 0 else None,
    }
    comparison.append(report)
    (case_dir / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, sort_keys=True))
    failed |= not match
comparison_record = {
    'schema_version': 1,
    'head_sha': __import__('subprocess').check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
    'host': __import__('platform').system() + '/' + __import__('platform').machine(),
    'strategy_id': lock['strategy_id'], 'recipe_status': lock['recipe_status'],
    'local_status': 'open' if failed else 'qualified', 'cases': comparison,
}
(work_dir / 'candidate-comparison.json').write_text(json.dumps(comparison_record, indent=2) + '\n')
(work_dir / 'candidate-digests.json').write_bytes(lock_path.read_bytes())
if failed:
    raise SystemExit('candidate bytes do not match the provisional digest lock')
PY
      exit 0
      ;;
  esac
fi

python3 - "$repo_root" "$fixture_dir" "$work_dir" "$mode" <<'PY'
import hashlib
import json
import pathlib
import sys
import subprocess

root, fixture_dir, work_dir = map(pathlib.Path, sys.argv[1:4])
mode = sys.argv[4]
manifest = json.loads((fixture_dir / 'manifest.json').read_text())
lock_path = fixture_dir / 'candidate-digests.json'
if lock_path.exists():
    lock = json.loads(lock_path.read_text())
    expected_by_name = {entry['rom']: entry for entry in lock.get('original_candidates', [])}
else:
    expected_by_name = {entry['rom']: entry for entry in manifest['fixtures']}
failed = False
for name in ('daa', 'tim00', 'tim00_div_trigger'):
    case_dir = work_dir / name
    expected_entry = expected_by_name[name + '.gb']
    if lock_path.exists() and lock.get('source_head'):
        expected = subprocess.check_output(['git', '-C', str(root), 'show', f"{lock['source_head']}:fixtures/mooneye/{name}.gb"])
    else:
        expected = (fixture_dir / (name + '.gb')).read_bytes()
    rebuilt = (case_dir / 'rebuilt.gb').read_bytes()
    expected_sha = hashlib.sha256(expected).hexdigest()
    rebuilt_sha = hashlib.sha256(rebuilt).hexdigest()
    pin_sha = expected_entry['sha256']
    offsets = [i for i in range(max(len(expected), len(rebuilt)))
               if i >= len(expected) or i >= len(rebuilt) or expected[i] != rebuilt[i]]
    first = offsets[0] if offsets else None
    lines = [f'case={name}.gb', f'expected_length={len(expected)}',
             f'rebuilt_length={len(rebuilt)}', f'original_sha256={pin_sha}',
             f'expected_sha256={expected_sha}', f'rebuilt_sha256={rebuilt_sha}',
             f'differing_offsets_count={len(offsets)}',
             'differing_offsets_all=' + ','.join(map(str, offsets)),
             f'first_difference={first if first is not None else "none"}']
    if first is not None:
        lo, hi = max(0, first - 16), min(max(len(expected), len(rebuilt)), first + 17)
        lines += [f'window_range=[{lo},{hi})',
                  f'expected_window={expected[lo:hi].hex(" ")}',
                  f'rebuilt_window={rebuilt[lo:hi].hex(" ")}']
    report = '\n'.join(lines) + '\n'
    (case_dir / 'original-comparison.txt').write_text(report)
    print(report, flush=True)
    failed |= rebuilt_sha != pin_sha or len(rebuilt) != expected_entry['size_bytes']
if failed and mode == '--compare':
    raise SystemExit(1)
PY
