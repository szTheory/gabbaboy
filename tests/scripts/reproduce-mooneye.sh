#!/usr/bin/env bash
# Explicit, networked fixture preparation. Ordinary CTest uses checked-in ROMs.
set -euo pipefail

if [[ $# != 2 || ( $1 != --diagnose && $1 != --compare ) ]]; then
  echo "usage: $0 --diagnose|--compare fixtures/mooneye" >&2
  exit 2
fi
mode=$1
fixture_dir=$(cd "$2" && pwd -P)
repo_root=$(git rev-parse --show-toplevel)
[[ "$fixture_dir" == "$repo_root/fixtures/mooneye" ]] || { echo 'unexpected fixture directory' >&2; exit 2; }
work_dir=${GBB_REPRO_OUTPUT_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-mooneye.XXXXXXXX")}
mkdir -p "$work_dir"
work_dir=$(cd "$work_dir" && pwd -P)
echo "Evidence directory: $work_dir"

sha256_file() { shasum -a 256 "$1" | cut -d ' ' -f 1; }
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

manifest="$fixture_dir/manifest.json"
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
pin_sha "$fixture_dir/font-source.c" 5e5b21a1ff66f226e0e3d3ea1630ad4e2d16edbc9fcbb76b70a26b44c2271f52
fetch_source wla-dx https://github.com/vhelin/wla-dx.git "$tool_rev" "$tool_tree"
pin_sha "$work_dir/wla-dx-source.tar" "$tool_archive"
fetch_source mooneye https://github.com/Gekkio/mooneye-test-suite.git "$suite_rev" "$suite_tree"

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
{
  printf 'host=%s\n' "$(uname -s)/$(uname -m)"
  printf 'run_revision=%s\n' "$(git rev-parse HEAD)"
  printf 'suite_revision=%s\nsuite_tree=%s\n' "$suite_rev" "$suite_tree"
  printf 'tool_revision=%s\ntool_tree=%s\ntool_archive_sha256=%s\n' "$tool_rev" "$tool_tree" "$tool_archive"
  printf 'font_source_sha256=%s\nfont_sha256=%s\n' "$(sha256_file "$fixture_dir/font-source.c")" "$font_digest"
  printf 'assembler=%s\nlinker=%s\n' "$assembler_version" "$linker_version"
  printf 'cmake_flags=-DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=<workspace>/wla-dx-install\n'
  printf 'font_flags=cc -std=c17 -O2\nassembly_flags=-I <suite>/common -o <object> <source>\nlink_flags=-d -S <link> <rom>\n'
} > "$work_dir/inputs.txt"
cat "$work_dir/inputs.txt"

for case_name in daa tim00 tim00_div_trigger; do
  case "$case_name" in
    daa) source_path=acceptance/instr/daa.s ;;
    *) source_path="acceptance/timer/$case_name.s" ;;
  esac
  case_dir="$work_dir/$case_name"
  mkdir -p "$case_dir"
  object="$case_dir/$case_name.o"
  link_file="$case_dir/$case_name.link"
  rom="$case_dir/rebuilt.gb"
  cp "$fixture_dir/$case_name.gb" "$case_dir/expected.gb"
  "$assembler" -I "$common_dir" -o "$object" "$source_dir/$source_path" > "$case_dir/assembler.log" 2>&1
  printf '[objects]\n%s\n' "$object" > "$link_file"
  "$linker" -d -S "$link_file" "$rom" > "$case_dir/linker.log" 2>&1
  printf 'source_path=%s\nsource_sha256=%s\n' "$source_path" "$(sha256_file "$source_dir/$source_path")" > "$case_dir/source.txt"
done

python3 - "$fixture_dir" "$work_dir" "$mode" <<'PY'
import hashlib
import json
import pathlib
import sys

fixture_dir, work_dir = map(pathlib.Path, sys.argv[1:3])
mode = sys.argv[3]
manifest = json.loads((fixture_dir / 'manifest.json').read_text())
expected_by_name = {entry['rom']: entry for entry in manifest['fixtures']}
names = ('daa', 'tim00', 'tim00_div_trigger')
failed = False
for name in names:
    case_dir = work_dir / name
    expected = (case_dir / 'expected.gb').read_bytes()
    rebuilt = (case_dir / 'rebuilt.gb').read_bytes()
    expected_sha = hashlib.sha256(expected).hexdigest()
    rebuilt_sha = hashlib.sha256(rebuilt).hexdigest()
    pin = expected_by_name[name + '.gb']
    if expected_sha != pin['sha256'] or len(expected) != pin['size_bytes']:
        raise SystemExit(f'checked-in {name} fixture fails manifest pin')
    offsets = [i for i in range(max(len(expected), len(rebuilt)))
               if i >= len(expected) or i >= len(rebuilt) or expected[i] != rebuilt[i]]
    first = offsets[0] if offsets else None
    lines = [f'case={name}.gb', f'expected_length={len(expected)}',
             f'rebuilt_length={len(rebuilt)}', f'manifest_sha256={pin["sha256"]}',
             f'expected_sha256={expected_sha}', f'rebuilt_sha256={rebuilt_sha}',
             f'differing_offsets_count={len(offsets)}',
             'differing_offsets_all=' + ','.join(map(str, offsets)),
             f'first_difference={first if first is not None else "none"}']
    if name == 'daa':
        lines += [f'byte_335_expected={expected[335]:02x}',
                  f'byte_335_rebuilt={rebuilt[335]:02x}']
    if first is not None:
        lo, hi = max(0, first - 16), min(max(len(expected), len(rebuilt)), first + 17)
        lines += [f'window_range=[{lo},{hi})',
                  f'expected_window={expected[lo:hi].hex(" ")}',
                  f'rebuilt_window={rebuilt[lo:hi].hex(" ")}']
    report = '\n'.join(lines) + '\n'
    (case_dir / 'comparison.txt').write_text(report)
    print(report, flush=True)
    failed |= first is not None or rebuilt_sha != pin['sha256']
if failed and mode == '--compare':
    raise SystemExit(1)
PY
