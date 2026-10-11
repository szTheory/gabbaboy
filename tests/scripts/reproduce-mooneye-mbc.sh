#!/usr/bin/env bash
# Explicit, networked rebuild of the 15 Mooneye emulator-only mbc2/mbc5 derivatives (Phase 8, D-24).
# Ordinary CTest uses the checked-in ROMs. Adapted from reproduce-mooneye.sh: same Mooneye and WLA-DX
# pins, same headless-report patch and zero font, read from the frozen parent fixtures by digest.
#
#   --build OUTDIR          build the 15 ROMs (and their .sym files) into OUTDIR
#   --compare FIXTURE_DIR   build into a fresh temp dir and compare byte for byte with FIXTURE_DIR
#   --facts OUTDIR          print per-ROM header and symbol facts from a prior --build
#
# Evidence, .sym, .lnk and .log files never belong in the repository (Pitfall P20); OUTDIR and the
# evidence directory must therefore be outside the working tree.
set -euo pipefail

usage() { echo "usage: $0 --build OUTDIR | --compare fixtures/mooneye-mbc | --facts OUTDIR" >&2; exit 2; }
[[ $# == 2 ]] || usage
mode=$1
case "$mode" in --build|--compare|--facts) ;; *) usage ;; esac

repo_root=$(git rev-parse --show-toplevel)
parent_dir="$repo_root/fixtures/mooneye"
sha256_file() { shasum -a 256 "$1" | cut -d ' ' -f 1; }
pin_sha() {
  local actual
  actual=$(sha256_file "$1")
  [[ "$actual" == "$2" ]] || { echo "SHA-256 pin failure: $1 expected $2 actual $actual" >&2; exit 1; }
}
outside_repo() {
  case "$1/" in "$repo_root"/*) echo "refusing to write build products inside the working tree: $1" >&2; exit 2 ;; esac
}

# alias = <category>_<stem>; source path inside the pinned Mooneye tree.
roms=(
  mbc2_bits_ramg mbc2_bits_romb mbc2_bits_unused mbc2_ram mbc2_rom_512kb mbc2_rom_1Mb mbc2_rom_2Mb
  mbc5_rom_512kb mbc5_rom_1Mb mbc5_rom_2Mb mbc5_rom_4Mb mbc5_rom_8Mb mbc5_rom_16Mb mbc5_rom_32Mb mbc5_rom_64Mb
)
source_of() { local category=${1%%_*} stem=${1#*_}; printf 'emulator-only/%s/%s.s' "$category" "$stem"; }

if [[ "$mode" == --facts ]]; then
  out_dir=$(cd "$2" && pwd -P)
  outside_repo "$out_dir"
  python3 -I - "$out_dir" "${roms[@]}" <<'PY'
import pathlib
import re
import sys

out = pathlib.Path(sys.argv[1])
for alias in sys.argv[2:]:
    rom = (out / f'{alias}.gb').read_bytes()
    pass_label = (out / f'{alias}.pass-label').read_text().strip()
    labels = {}
    for line in (out / f'{alias}.sym').read_text().splitlines():
        match = re.match(r'^([0-9a-fA-F]{2}):([0-9a-fA-F]{4}) (\S+)$', line.strip())
        if match:
            labels.setdefault(match.group(3), []).append(int(match.group(2), 16))
    result = labels.get('quit@serial_dump', [])
    sites = {name: pcs[0] for name, pcs in labels.items() if '@quit_inline_' in name}
    passes = [pc for name, pc in sites.items() if name.startswith(pass_label + '@')]
    assert len(passes) == 1, (alias, pass_label, sites)
    fails = sorted(pc for pc in sites.values() if pc != passes[0])
    print(f'{alias} size={len(rom)} header147={rom[0x147]:02x} header148={rom[0x148]:02x} '
          f'header149={rom[0x149]:02x} result_pc={",".join(f"{x:04x}" for x in result)} '
          f'pass_callback_pc={passes[0]:04x} fail_callback_pcs={",".join(f"{x:04x}" for x in fails)} '
          f'rom_ldbb_ok={all(rom[x] == 0x40 for x in result if x < len(rom)) if result else False}')
PY
  exit 0
fi

# ---- pins, read from the frozen parent fixtures and checked by digest before the build ----------------
pin_sha "$parent_dir/manifest.json" 98a1799b8be9c022ac13467a552890fb12bdd706017e42e12c944ec618d60527
pin_sha "$parent_dir/headless-report.patch" c3679ab53b59da14a0f6af1fdd552316ba922762c3a91988f7f8ac4440516e5d
pin_sha "$parent_dir/font-source.c" 5e5b21a1ff66f226e0e3d3ea1630ad4e2d16edbc9fcbb76b70a26b44c2271f52
manifest="$parent_dir/manifest.json"
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
  echo 'parent manifest input pin differs from reviewed recipe' >&2; exit 1;
}
# D-27 contingency: a sibling-owned patch is applied after the parent patch only when it exists.
mbc_patch="$repo_root/fixtures/mooneye-mbc/headless-report-mbc.patch"

if [[ "$mode" == --build ]]; then
  mkdir -p "$2"
  build_dir=$(cd "$2" && pwd -P)
else
  fixture_dir=$(cd "$2" && pwd -P)
  [[ "$fixture_dir" == "$repo_root/fixtures/mooneye-mbc" ]] || { echo 'unexpected fixture directory' >&2; exit 2; }
  build_dir=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-mooneye-mbc-roms.XXXXXXXX")
  build_dir=$(cd "$build_dir" && pwd -P)
fi
outside_repo "$build_dir"
work_dir=${GBB_REPRO_OUTPUT_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-mooneye-mbc.XXXXXXXX")}
mkdir -p "$work_dir"
work_dir=$(cd "$work_dir" && pwd -P)
outside_repo "$work_dir"
echo "Evidence directory: $work_dir"
strategy=${GBB_WLA_ORDERING_STRATEGY:-source-order}
[[ "$strategy" == source-order ]] || { echo "unknown deterministic WLA-DX strategy: $strategy" >&2; exit 2; }

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
cc -std=c17 -O2 "$parent_dir/font-source.c" -o "$work_dir/font-source"
"$work_dir/font-source" "$common_dir/font.bin"
pin_sha "$common_dir/font.bin" "$font_digest"
(cd "$source_dir" && patch --batch --fuzz=0 -p1 < "$parent_dir/headless-report.patch") > "$work_dir/patch.log"
if [[ -f "$mbc_patch" ]]; then
  (cd "$source_dir" && patch --batch --fuzz=0 -p1 < "$mbc_patch") > "$work_dir/patch-mbc.log"
fi
{
  printf 'host=%s\n' "$(uname -s)/$(uname -m)"
  printf 'suite_revision=%s\nsuite_tree=%s\n' "$suite_rev" "$suite_tree"
  printf 'tool_revision=%s\ntool_tree=%s\ntool_archive_sha256=%s\n' "$tool_rev" "$tool_tree" "$tool_archive"
  printf 'assembler=%s\nlinker=%s\n' "$assembler_version" "$linker_version"
  printf 'link_flags=-nS -d -S <link> <rom>\n'
} > "$work_dir/inputs.txt"
cat "$work_dir/inputs.txt"

for alias in "${roms[@]}"; do
  source_path=$(source_of "$alias")
  object="$work_dir/$alias.o"
  link_file="$work_dir/$alias.link"
  printf '[objects]\n%s\n' "$object" > "$link_file"
  "$assembler" -I "$common_dir" -o "$object" "$source_dir/$source_path" > "$work_dir/$alias-assembler.log" 2>&1
  "$linker" -nS -d -S "$link_file" "$build_dir/$alias.gb" > "$work_dir/$alias-linker.log" 2>&1
  # The single quit_ok invocation (in the test or in the shared harness) names the pass callback by its
  # enclosing label; every other quit_inline site is a fail callback.
  harness="$source_dir/common/harness/${alias%%_*}_rom.s"
  for candidate in "$source_dir/$source_path" "$harness"; do
    pass_label=$(awk '/^[A-Za-z_][A-Za-z0-9_]*:?[ \t]*(;.*)?$/{l=$1; sub(":$","",l)} /(^|[ \t])quit_ok([ \t]|$)/{print l}' "$candidate")
    [[ -z "$pass_label" ]] || break
  done
  [[ -n "$pass_label" && "$pass_label" != *$'\n'* ]] || { echo "no single quit_ok for $alias" >&2; exit 1; }
  printf '%s\n' "$pass_label" > "$build_dir/$alias.pass-label"
done

if [[ "$mode" == --build ]]; then
  for alias in "${roms[@]}"; do
    printf '%s %s %s\n' "$alias" "$(wc -c < "$build_dir/$alias.gb" | tr -d ' ')" "$(sha256_file "$build_dir/$alias.gb")"
  done
  exit 0
fi

# --compare: every committed ROM must equal the fresh build byte for byte, and no ROM may be missing or extra.
failed=0
committed_count=$(find "$fixture_dir" -maxdepth 1 -name '*.gb' | wc -l | tr -d ' ')
[[ "$committed_count" == "${#roms[@]}" ]] || { echo "committed ROM count $committed_count differs from ${#roms[@]}" >&2; failed=1; }
for alias in "${roms[@]}"; do
  if [[ ! -f "$fixture_dir/$alias.gb" ]]; then echo "missing committed ROM: $alias.gb" >&2; failed=1; continue; fi
  fresh=$(sha256_file "$build_dir/$alias.gb")
  committed=$(sha256_file "$fixture_dir/$alias.gb")
  if cmp -s "$build_dir/$alias.gb" "$fixture_dir/$alias.gb" && [[ "$fresh" == "$committed" ]]; then
    printf 'match %s %s\n' "$alias" "$fresh"
  else
    printf 'DIFFERENT %s fresh=%s committed=%s\n' "$alias" "$fresh" "$committed" >&2
    failed=1
  fi
done
rm -rf "$build_dir"
exit "$failed"
