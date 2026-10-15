#!/usr/bin/env bash
# Offline admission checks and pinned RGBDS v0.6.1 reproduction for MagenTests.
# --self-check | --self-test | --compare (PATH tools) | --compare-pinned (private cache)
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(cd "$script_dir/../.." && pwd -P)
fixture="$repo_root/fixtures/magentests"
upstream_url=https://github.com/alloncm/MagenTests.git
upstream_commit=3f9c090f16e5a721db776febb9ba7d773e1c819c
hardware_url=https://github.com/gbdev/hardware.inc.git
hardware_commit=21ef22d01ac55151160f3d98110c2da8846a96b2
rgbds_version=v0.6.1

# output name | source directory | exact upstream rgbfix options
rom_table() {
  cat <<'TABLE'
mbc_oob_sram_mbc1|src/mbc_oob_sram|--color-compatible --mbc-type MBC1+RAM --ram-size 2
mbc_oob_sram_mbc3|src/mbc_oob_sram|--color-compatible --mbc-type MBC3+RAM --ram-size 2
mbc_oob_sram_mbc5|src/mbc_oob_sram|--color-compatible --mbc-type MBC5+RAM --ram-size 2
bg_oam_priority|src/color_bg_oam_priority|--color-only --mbc-type ROM
oam_internal_priority|src/oam_internal_priority|--color-only --mbc-type ROM
ppu_disabled_state|src/ppu_disabled_state|--color-compatible --mbc-type ROM
hblank_vram_dma|src/hblank_vram_dma|--color-only --mbc-type ROM
TABLE
}

sha256_file() {
  python3 -I - "$1" <<'PY'
import hashlib, pathlib, sys
print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())
PY
}

self_check_at() {
  local checked_fixture=${1:-$fixture}
  python3 -I - "$checked_fixture" "$upstream_commit" "$hardware_commit" "$(rom_table)" <<'PY'
import hashlib, json, pathlib, re, sys
fixture = pathlib.Path(sys.argv[1])
commit, hardware, table_text = sys.argv[2:5]
def fail(message): raise SystemExit('self-check failed: ' + message)
try:
    manifest = json.loads((fixture / 'manifest.json').read_text())
except (OSError, json.JSONDecodeError) as exc:
    fail('cannot read manifest: ' + str(exc))
suite = manifest.get('suite', {})
if suite.get('revision') != commit: fail('manifest revision differs from the pin')
if suite.get('release') != '0.5.0': fail('manifest release differs from 0.5.0')
table = {}
for line in table_text.splitlines():
    name, source_dir, options = line.split('|')
    table[name + '.gbc'] = (source_dir, options)
entries = manifest.get('fixtures', [])
names = [entry.get('file') for entry in entries]
if sorted(names) != sorted(table):
    fail('manifest rows and rebuild table name different files: %s vs %s' % (sorted(names), sorted(table)))
for entry in entries:
    name = entry.get('file')
    if name not in table: fail('unexpected manifest row ' + str(name))
    if (entry.get('source_dir'), entry.get('rgbfix_options')) != table[name]:
        fail('manifest source_dir/rgbfix_options differ from the rebuild table for ' + name)
    try: data = (fixture / name).read_bytes()
    except OSError: fail('missing fixture ' + name)
    if len(data) != entry.get('size_bytes') or hashlib.sha256(data).hexdigest() != entry.get('sha256'):
        fail('digest mismatch for ' + name)
try: sources = (fixture / 'SOURCES.md').read_text()
except OSError: fail('missing source record SOURCES.md')
for needle, label in ((commit, 'MagenTests source commit'), (hardware, 'hardware.inc submodule pin'),
                      ('RGBDS v0.6.1', 'RGBDS version')):
    if needle not in sources: fail('SOURCES.md is missing ' + label)
toolchain = manifest.get('toolchain', {}).get('rgbds', {})
if toolchain.get('version') != '0.6.1': fail('manifest RGBDS version differs from v0.6.1')
pins = (
    ('linux-x86_64', 'rgbds-0.6.1-linux-x86_64.tar.xz', 'cfaff18e0db0006863de921d6f5a10eb5fb04dba453f967955a8b0f30bc7ba5b'),
    ('macos-x86-64', 'rgbds-0.6.1-macos-x86-64.zip', '65929a5483c89b20955df0d78ceb87744d8ad0cf7c80919f6ee9ef90fc55c08d'),
)
for key, asset, digest in pins:
    pin = toolchain.get('archives', {}).get(key, {})
    if pin.get('asset') != asset or pin.get('sha256') != digest:
        fail('manifest RGBDS archive pin differs for ' + key)
    if not re.search(re.escape(asset) + r' sha256 ' + re.escape(digest), sources):
        fail('SOURCES.md is missing the RGBDS archive pin for ' + key)
hdma = next((entry for entry in entries if entry.get('file') == 'hblank_vram_dma.gbc'), None)
if hdma is None: fail('manifest is missing hblank_vram_dma.gbc')
if hdma.get('sha256') != 'e8124ce687d37a2402e20af92af1299610bfbda0871d605084c0bba2bf57135c':
    fail('release digest pin differs for hblank_vram_dma.gbc')
rom = (fixture / hdma['file']).read_bytes()
if rom[0x147] != 0x00 or rom[0x143] != 0xC0:
    fail('hblank_vram_dma.gbc header does not match ROM/CGB-only metadata')
if hdma.get('release') != '0.5.0' or hdma.get('evidence_class') != 'SameBoy-assisted differential':
    fail('hblank_vram_dma.gbc release or evidence class is missing')
source_files = hdma.get('source_files', [])
expected_paths = {'Makefile', 'LICENSE', 'src/common.asm', 'src/hblank_vram_dma/main.asm',
                  'src/hblank_vram_dma/graphics_data.asm', 'hardware.inc/hardware.inc', 'hardware.inc/LICENSE'}
if {item.get('path') for item in source_files} != expected_paths:
    fail('hblank_vram_dma.gbc source/include closure differs from the pinned build closure')
for item in source_files:
    if not re.fullmatch(r'[0-9a-f]{64}', item.get('sha256', '')):
        fail('invalid source closure digest for ' + str(item.get('path')))
    if item['path'] not in sources: fail('SOURCES.md is missing source closure path ' + item['path'])
if hdma.get('rgbfix_options') != '--color-only --mbc-type ROM':
    fail('hblank_vram_dma.gbc build options are not the upstream Makefile options')
license_path = fixture / 'LICENSE.txt'
if not license_path.is_file(): fail('missing license closure LICENSE.txt')
license_text = license_path.read_text()
if 'Copyright (c) 2022 alloncm' not in license_text or 'MIT License' not in license_text:
    fail('LICENSE.txt is missing the MagenTests MIT notice')
if 'SPDX-License-Identifier: CC0-1.0' not in license_text or 'publicdomain/zero/1.0' not in license_text:
    fail('LICENSE.txt is missing the hardware.inc CC0-1.0 notice')
if 'hardware.inc/LICENSE' not in sources or 'CC0-1.0' not in sources:
    fail('SOURCES.md is missing the hardware.inc license closure')
print('self-check=pass')
PY
}

self_check() { self_check_at "$fixture"; }

mutate_copy() {
  python3 -I - "$1" "$2" <<'PY'
import json, pathlib, sys
fixture, mutation = pathlib.Path(sys.argv[1]), sys.argv[2]
if mutation == 'source-pin':
    path = fixture / 'SOURCES.md'
    path.write_text(path.read_text().replace('3f9c090f16e5a721db776febb9ba7d773e1c819c', '0' * 40, 1))
elif mutation == 'license':
    (fixture / 'LICENSE.txt').unlink()
else:
    path = fixture / 'manifest.json'
    manifest = json.loads(path.read_text())
    row = next(item for item in manifest['fixtures'] if item['file'] == 'hblank_vram_dma.gbc')
    if mutation == 'release-digest': row['sha256'] = '0' * 64
    elif mutation == 'missing-row': manifest['fixtures'].remove(row)
    elif mutation == 'build-options': row['rgbfix_options'] = '--color-only --mbc-type MBC1'
    else: raise SystemExit('unknown self-test mutation ' + mutation)
    path.write_text(json.dumps(manifest, indent=2) + '\n')
PY
}

expect_rejected_copy() {
  local copy=$1 mutation=$2 expected=$3 output
  mutate_copy "$copy" "$mutation"
  if output=$(self_check_at "$copy" 2>&1); then
    echo "self-test failed: $mutation mutation was accepted" >&2; return 1
  fi
  if [[ "$output" != *"$expected"* ]]; then
    echo "self-test failed: $mutation expected '$expected', got: $output" >&2; return 1
  fi
  printf 'self-test-rejected=%s reason=%s\n' "$mutation" "$expected"
}

self_test() {
  local test_root clean mutation_dir mutation expected
  test_root=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-magentests-self-test.XXXXXXXX")
  trap 'rm -rf -- "$test_root"' RETURN
  clean="$test_root/clean"
  cp -R "$fixture" "$clean"
  self_check_at "$clean" >/dev/null
  echo 'self-test-accepted=clean-copy'
  for mutation in release-digest missing-row source-pin license build-options; do
    mutation_dir="$test_root/$mutation"
    cp -R "$fixture" "$mutation_dir"
    case "$mutation" in
      release-digest) expected='digest mismatch for hblank_vram_dma.gbc' ;;
      missing-row) expected='manifest rows and rebuild table name different files' ;;
      source-pin) expected='SOURCES.md is missing MagenTests source commit' ;;
      license) expected='missing license closure LICENSE.txt' ;;
      build-options) expected='manifest source_dir/rgbfix_options differ from the rebuild table for hblank_vram_dma.gbc' ;;
    esac
    expect_rejected_copy "$mutation_dir" "$mutation" "$expected"
  done
  echo 'self-test=pass'
}

check_source_tree() {
  python3 -I - "$fixture/manifest.json" "$1" <<'PY'
import hashlib, json, pathlib, sys
manifest = json.loads(pathlib.Path(sys.argv[1]).read_text())
source = pathlib.Path(sys.argv[2])
entry = next(item for item in manifest['fixtures'] if item['file'] == 'hblank_vram_dma.gbc')
for item in entry['source_files']:
    path = source / item['path']
    try: actual = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError: raise SystemExit('pinned source closure file missing: ' + item['path'])
    if actual != item['sha256']: raise SystemExit('pinned source closure digest differs: ' + item['path'])
print('source-closure=pass')
PY
}

run_tool() {
  if [[ "${GBB_MAGEN_ROSETTA:-0}" == 1 ]]; then arch -x86_64 "$@"; else "$@"; fi
}

compare_build() {
  local source_dir=$1 build_dir=$2 rgbasm_cmd=$3 rgblink_cmd=$4 rgbfix_cmd=$5
  local name dir options
  check_source_tree "$source_dir"
  mkdir -p "$build_dir"
  while IFS='|' read -r name dir options; do
    [[ -n "$name" ]] || continue
    (cd "$source_dir" && run_tool "$rgbasm_cmd" -L -i "$dir" -i hardware.inc/ \
      -o "$build_dir/$name.o" "$dir/main.asm") 2>"$build_dir/$name.rgbasm.log"
    run_tool "$rgblink_cmd" -o "$build_dir/$name.gbc" "$build_dir/$name.o"
    # rgbfix options come from the literal repository-owned rebuild table.
    # shellcheck disable=SC2086
    run_tool "$rgbfix_cmd" -v -p 0 $options "$build_dir/$name.gbc"
  done < <(rom_table)
  python3 -I - "$fixture" "$build_dir" "$(rom_table)" <<'PY'
import hashlib, pathlib, sys
fixture, build = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
bad = False
for line in sys.argv[3].splitlines():
    name = line.split('|', 1)[0] + '.gbc'
    committed, rebuilt = (fixture / name).read_bytes(), (build / name).read_bytes()
    if committed != rebuilt:
        print('result=differs %s %s %s' % (name, hashlib.sha256(rebuilt).hexdigest(), hashlib.sha256(committed).hexdigest()))
        bad = True
if bad: raise SystemExit(1)
print('result=byte-identical')
PY
}

fetch_source() {
  local source_dir=$1 work_dir=$2
  mkdir -p "$source_dir"
  git -C "$source_dir" init -q
  git -C "$source_dir" fetch -q --depth 1 "$upstream_url" "$upstream_commit"
  git -C "$source_dir" checkout -q --detach FETCH_HEAD
  [[ "$(git -C "$source_dir" rev-parse HEAD)" == "$upstream_commit" ]] || {
    echo 'fetched upstream commit differs from the pin' >&2; return 1;
  }
  git -C "$work_dir" init -q hardware
  git -C "$work_dir/hardware" fetch -q --depth 1 "$hardware_url" "$hardware_commit"
  git -C "$work_dir/hardware" checkout -q --detach FETCH_HEAD
  [[ "$(git -C "$work_dir/hardware" rev-parse HEAD)" == "$hardware_commit" ]] || {
    echo 'fetched hardware.inc commit differs from the pin' >&2; return 1;
  }
  rm -rf -- "$source_dir/hardware.inc"
  mv "$work_dir/hardware" "$source_dir/hardware.inc"
}

compare_path() {
  local tool version work_dir source_dir
  for tool in rgbasm rgblink rgbfix; do
    command -v "$tool" >/dev/null || { echo "required RGBDS tool missing: $tool ($rgbds_version)" >&2; return 1; }
    version=$("$tool" --version | sed -n '1p')
    [[ "$version" == "$tool $rgbds_version" ]] || { echo "$tool version mismatch: $version" >&2; return 1; }
  done
  work_dir=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-magentests.XXXXXXXX")
  trap 'rm -rf -- "$work_dir"' RETURN
  source_dir="$work_dir/source"
  fetch_source "$source_dir" "$work_dir"
  compare_build "$source_dir" "$work_dir/build" "$(command -v rgbasm)" "$(command -v rgblink)" "$(command -v rgbfix)"
}

compare_pinned() {
  local host arch asset digest key cache archive tools_root tools_dir source_dir build_dir tool version
  host=$(uname -s); arch=$(uname -m); GBB_MAGEN_ROSETTA=0
  if [[ "$host" == Darwin ]]; then
    key=macos-x86-64
    asset=rgbds-0.6.1-macos-x86-64.zip
    digest=65929a5483c89b20955df0d78ceb87744d8ad0cf7c80919f6ee9ef90fc55c08d
    [[ "$arch" != arm64 ]] || GBB_MAGEN_ROSETTA=1
  elif [[ "$host" == Linux && "$arch" == x86_64 ]]; then
    key=linux-x86_64
    asset=rgbds-0.6.1-linux-x86_64.tar.xz
    digest=cfaff18e0db0006863de921d6f5a10eb5fb04dba453f967955a8b0f30bc7ba5b
  else
    echo "unsupported host for pinned RGBDS v0.6.1 reproduction: $host/$arch" >&2; return 1
  fi
  cache="$repo_root/build/magentests-rgbds-cache"
  mkdir -p "$cache"
  archive="$cache/$asset"
  if [[ ! -f "$archive" || "$(sha256_file "$archive")" != "$digest" ]]; then
    rm -f -- "$archive" "$archive.part"
    curl --fail --location --silent --show-error \
      "https://github.com/gbdev/rgbds/releases/download/v0.6.1/$asset" -o "$archive.part"
    version=$(sha256_file "$archive.part")
    [[ "$version" == "$digest" ]] || { rm -f -- "$archive.part"; echo "RGBDS archive SHA-256 mismatch: expected $digest got $version" >&2; return 1; }
    mv "$archive.part" "$archive"
  fi
  tools_root="$cache/tools-$key-$digest"
  if [[ ! -x "$tools_root/rgbasm" || ! -x "$tools_root/rgblink" || ! -x "$tools_root/rgbfix" ]]; then
    tools_dir="$cache/extract-$key-$$"
    mkdir -p "$tools_dir"
    if [[ "$asset" == *.zip ]]; then unzip -q "$archive" -d "$tools_dir"; else tar -xJf "$archive" -C "$tools_dir"; fi
    for tool in rgbasm rgblink rgbfix; do
      [[ -f "$tools_dir/$tool" ]] || { echo "pinned RGBDS archive is missing $tool" >&2; return 1; }
      chmod 755 "$tools_dir/$tool"
      version=$(run_tool "$tools_dir/$tool" --version | sed -n '1p')
      [[ "$version" == "$tool $rgbds_version" ]] || { echo "$tool version mismatch in archive: $version" >&2; return 1; }
    done
    mv "$tools_dir" "$tools_root"
  fi
  for tool in rgbasm rgblink rgbfix; do
    version=$(run_tool "$tools_root/$tool" --version | sed -n '1p')
    [[ "$version" == "$tool $rgbds_version" ]] || { echo "$tool version mismatch in cache: $version" >&2; return 1; }
  done
  source_dir="$cache/source-$upstream_commit"
  if [[ ! -d "$source_dir/.git" || ! -d "$source_dir/hardware.inc/.git" ]]; then
    rm -rf -- "$source_dir"
    fetch_source "$source_dir" "$cache"
  fi
  build_dir=$(mktemp -d "$cache/build.XXXXXXXX")
  trap 'rm -rf -- "$build_dir"' RETURN
  compare_build "$source_dir" "$build_dir" "$tools_root/rgbasm" "$tools_root/rgblink" "$tools_root/rgbfix"
  echo "reproduction=source:$upstream_commit tool:RGBDS-$rgbds_version archive:$digest host:$key"
}

mode=${1:---self-check}
case "$mode" in
  --self-check) self_check ;;
  --self-test) self_check && self_test ;;
  --compare) self_check && compare_path ;;
  --compare-pinned) self_check && compare_pinned ;;
  *) echo "usage: $0 [--self-check|--self-test|--compare|--compare-pinned]" >&2; exit 2 ;;
esac
