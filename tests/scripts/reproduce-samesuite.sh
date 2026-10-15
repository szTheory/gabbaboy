#!/usr/bin/env bash
# Verify and rebuild the four approved SameSuite CGB DMA ROMs at the immutable
# Phase 13 source revision. Rebuilt bytes stay in an isolated temporary folder.
#
#   no arguments                 offline checks, mutation controls, pinned rebuild
#   --self-check [--case NAME]   offline manifest, rights, source and ROM pins
#   --self-test [--case NAME]    offline positive and provenance-negative checks
#   --compare-pinned [--case NAME]
#                                exact source plus digest-pinned RGBDS 1.0.1 rebuild
#   --compare-built DIR [--case NAME]
#                                compare an independently supplied build
#
# The --case selector is only for admission-stage work. Default and CI always
# require the full four-case set.
set -euo pipefail

script_dir=$(cd "$(dirname "$0")" && pwd -P)
repo_root=$(cd "$script_dir/../.." && pwd -P)
fixture_dir=$(printenv GBB_SAMESUITE_FIXTURE_DIR || true)
[[ -n "$fixture_dir" ]] || fixture_dir="$repo_root/fixtures/samesuite"
mode=default
case_name=
built_dir=

while (($#)); do
  case "$1" in
    --self-check|--self-test|--compare-pinned)
      [[ "$mode" == default ]] || { echo "select exactly one operation" >&2; exit 2; }
      mode=$(printf '%s' "$1" | cut -c3-)
      shift
      ;;
    --compare-built)
      [[ "$mode" == default && $# -ge 2 ]] || { echo "usage: $0 --compare-built DIR [--case NAME]" >&2; exit 2; }
      mode=compare-built
      built_dir=$2
      shift 2
      ;;
    --case)
      [[ -z "$case_name" && $# -ge 2 ]] || { echo "--case requires one name and may be used once" >&2; exit 2; }
      case_name=$2
      shift 2
      ;;
    -h|--help)
      sed -n '1,18p' "$0"
      exit 0
      ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -n "$case_name" ]] && [[ "$case_name" != gbc_dma_cont && "$case_name" != gdma_addr_mask && "$case_name" != hdma_lcd_off && "$case_name" != hdma_mode0 && "$case_name" != apu/channel_3/channel_3_first_sample ]]; then
  echo "unapproved SameSuite case: $case_name" >&2
  exit 2
fi

run_python() {
  python3 -I - "$@" <<'PY'
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

REV = "f15645fb049a47ea235f6d2c9a033e72d8087901"
MAC_ARCHIVE = ("rgbds-macos.zip", "2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645")
LINUX_ARCHIVE = ("rgbds-linux-x86_64.tar.xz", "80a5cad8dae27e24e46a93041352c47cadbc165103983f41c2b3082c42f6dad9")
LICENSE_SHA = "0ec39366cbff2aeed9f06f43941c98974355db52d72940ba1ddc5b7e0de925af"
UPSTREAM_LICENSE_SHA = "1ee622ea2140114dc0615b33bf1f3bb02ba0223215741f20fd6b29d875ab3b52"
INCLUDES = ["include/base.inc", "include/common.inc", "include/config.inc", "include/hardware.inc", "include/hexdigits.2bpp"]
SOURCE = {
    "dma/gbc_dma_cont.asm": (1988, "136048e8b882e7d71c03587ed48c2ac3db6cfc059b846ed14b3101e52c374d92", "ROM source", "X11"),
    "dma/gdma_addr_mask.asm": (2214, "8b745a069332ae4052376e873bfaf7cb0c04c960535062ab24fbd5202287f183", "ROM source", "X11"),
    "dma/hdma_lcd_off.asm": (2468, "2dcb5c71564905ec054cfef09296632cf8d02c0275ca69c5d87409bd139451a2", "ROM source", "X11"),
    "dma/hdma_mode0.asm": (2814, "ee249f2430c45ebdfa7c6bb23f9fe3af5f82384c0cc3d8b503b34114f5158828", "ROM source", "X11"),
    "include/base.inc": (5750, "9283500f9c2ebac16b52ffa2f1e497212a72425439a89e57fa1ee9fe7c820847", "included source", "X11"),
    "include/common.inc": (2401, "73a06345d63e29c8031ecf9fc844c275685e838b688d1d5e98954f02c3316c0b", "included source", "X11"),
    "include/config.inc": (44, "1fc948486e59c3c8003dec05d1cba59bc05733beec1e752403d516de10a58ec9", "included source", "X11"),
    "include/hardware.inc": (28763, "f0fe34491c902f7f98cddd26676448403dcdd44ac7190894e7f820b78df063cc", "included source", "CC0-1.0"),
    "include/hexdigits.2bpp": (512, "601ca4f503393d2ec9db5a595f3cbf1fa78f1be39ca8378aaa2f2540d650a34d", "included asset", "X11"),
    "apu/channel_3/channel_3_first_sample.asm": (1159, "15d6651df694adb54f77247752457f387ec3abf1b8a19e551b6e5ef94b47be32", "ROM source", "X11"),
}
CASES = [
    ("gbc_dma_cont", "cd20f67ff24d4cc90815bdd9b2c41bbeec5ec9a8abedb949f2fc704ff6d61512", "Two consecutive one-block GDMA starts copy contiguous expected bytes into VRAM.", "CGB-mode guest test; starts transfers with LCD off and observes source-derived VRAM bytes."),
    ("gdma_addr_mask", "d409c95ddf291c2d9debc0fc3f9bf0d49b24adbcef7f560aa2ae8f6e8299e5f3", "Low address nibbles written to HDMA1-4 are ignored and one block copies the expected WRAM bytes.", "CGB-mode guest test; checks masked source and destination address programming with LCD off."),
    ("hdma_lcd_off", "637a3612dcb99bd5f2b0739fb31ad26ce390361e6878b193b894b40f882e44eb", "The author-encoded result expects one block on an LCD-off HBlank-DMA start, then verifies the remaining/cancel status sequence.", "CGB-mode guest test; LCD is off at the start and the ROM records HDMA5 before and after cancellation."),
    ("hdma_mode0", "53f8d643548cecfc8ba5bd03721e4609571fa6a5ac383c96a2342b058fb5f2a1", "After waiting for a visible Mode 0 period, the author-encoded result expects one block and verifies the remaining/cancel status sequence.", "CGB-mode guest test; enters visible LCD operation, starts in Mode 0, and turns the LCD off before the test ends."),
]
APU_CASES = [
    ("apu/channel_3/channel_3_first_sample", "464b7139b6c2147fa0984006d32507559972404f538e53408369c1c337b1b6e7",
     "Pinned channel-3 first-sample test records eight wave-PCM observations.",
     "CGB-mode guest test; source encodes its expected result bytes and pass sentinel."),
]
ALL = [row[0] for row in CASES] + [row[0] for row in APU_CASES]
LICENSES = [
    {"path": "include/hexdigits.2bpp", "spdx": "X11", "basis": "covered by the SameSuite repository X11 license under G7"},
    {"path": "include/hardware.inc", "spdx": "CC0-1.0", "basis": "the pinned file carries its CC0-1.0 waiver and SPDX notice"},
]
BUILD = {
    "assembler": "RGBDS", "version": "1.0.1",
    "archive": MAC_ARCHIVE[0], "archive_sha256": MAC_ARCHIVE[1],
    "ci_archive": LINUX_ARCHIVE[0], "ci_archive_sha256": LINUX_ARCHIVE[1],
    "rgbasm_options": ["-I", "include/"],
    "rgblink_options": ["-n", "<work>/<name>.sym"],
    "rgbfix_options": ["-jv"],
    "command": "rgbasm -I include/ -o <work>/<name>.o <source> && rgblink -o <work>/<name>.gb -n <work>/<name>.sym <work>/<name>.o && rgbfix -jv <work>/<name>.gb",
}


def fail(message):
    raise SystemExit("provenance error: " + message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def selected(case_name):
    if case_name:
        if case_name not in ALL:
            fail("unapproved case: " + case_name)
        return [case_name]
    return ALL


def source_rows(names):
    source_paths = [(name + ".asm") if name.startswith("apu/") else ("dma/" + name + ".asm")
                    for name in names]
    files = [path for path in source_paths if not path.startswith("apu/")]
    files += INCLUDES
    files += [path for path in source_paths if path.startswith("apu/")]
    return [
        {"path": path, "size_bytes": SOURCE[path][0], "sha256": SOURCE[path][1], "role": SOURCE[path][2], "spdx": SOURCE[path][3]}
        for path in files
    ]


def fixture_row(name):
    if name.startswith("apu/"):
        case = next(row for row in APU_CASES if row[0] == name)
        source_path = name + ".asm"
        return {
            "alias": name,
            "file": name + ".gb",
            "original_filename": name + ".gb",
            "size_bytes": 32768,
            "sha256": case[1],
            "source_path": source_path,
            "source_size_bytes": SOURCE[source_path][0],
            "source_sha256": SOURCE[source_path][1],
            "includes": INCLUDES,
            "expectation": case[2],
            "applicability": case[3],
            "target_revision": "CGB-E",
            "model": "CGB-CPU-E selected software model",
            "bootless_applicability": True,
            "author_test_evidence": "Pinned SameSuite APU README reports CPU-CGB-E passes all tests; this source independently encodes eight expected bytes and a guest pass sentinel. No independent physical CGB-E measurement is supplied.",
            "author_expected_results": ["00", "00", "00", "00", "00", "0e", "0e", "0e"],
        }
    case = next(row for row in CASES if row[0] == name)
    source_path = next(path for path in SOURCE if path == "dma/" + name + ".asm")
    return {
        "alias": name,
        "file": name + ".gb",
        "original_filename": source_path[:-4] + ".gb",
        "size_bytes": 32768,
        "sha256": case[1],
        "source_path": source_path,
        "source_size_bytes": SOURCE[source_path][0],
        "source_sha256": SOURCE[source_path][1],
        "includes": INCLUDES,
        "expectation": case[2],
        "applicability": case[3],
        "target_revision": "CGB-E",
        "model": "CGB-CPU-E selected software model",
        "bootless_applicability": True,
        "author_test_evidence": "SameSuite is an author test suite developed to aid SameBoy; the pinned DMA source encodes the expected byte/status sequence. The upstream material supplies no independent per-ROM physical CGB-E measurement.",
    }


def manifest(fixture):
    if not fixture.is_dir():
        fail("fixture directory is missing")
    path = fixture / "manifest.json"
    if not path.is_file():
        fail("missing manifest.json")
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        fail("manifest.json is unreadable: " + str(error))


def check_eligibility(fixture):
    path = fixture / "ELIGIBILITY.md"
    if not path.is_file():
        fail("missing ELIGIBILITY.md for the complete admitted set")
    text = " ".join(path.read_text().split())
    for token in [REV, *ALL, "G7", "CC0-1.0", "D-06", "Pan Docs", "physical CGB-E evidence", "G1", "CGB-C"]:
        if token not in text:
            fail("eligibility ledger is missing required provenance: " + token)


def self_check(fixture, case_name, script):
    repo_root = script.resolve().parents[2]
    for path in (
        "fixtures/cgb-hdma/hblank.asm", "fixtures/cgb-hdma/manifest.json",
        "fixtures/cgb-hdma/LICENSE.txt", "fixtures/samesuite/manifest.json",
        "fixtures/samesuite/LICENSE.txt", "fixtures/samesuite/ELIGIBILITY.md",
        "fixtures/magentests/manifest.json", "fixtures/magentests/LICENSE.txt",
        "fixtures/magentests/SOURCES.md", "fixtures/magentests/ELIGIBILITY.md",
    ):
        attribute = subprocess.run(
            ["git", "-C", str(repo_root), "check-attr", "eol", "--", path],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if attribute.returncode != 0 or attribute.stdout.strip() != path + ": eol: lf":
            fail("digest-pinned text closure lacks LF checkout policy: " + path)
    for path in (
        "fixtures/cgb-hdma/hblank.gb", "fixtures/samesuite/gbc_dma_cont.gb",
        "fixtures/magentests/hblank_vram_dma.gbc",
    ):
        attribute = subprocess.run(
            ["git", "-C", str(repo_root), "check-attr", "text", "--", path],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if attribute.returncode != 0 or attribute.stdout.strip() != path + ": text: unset":
            fail("digest-pinned binary fixture lacks binary checkout policy: " + path)
    names = selected(case_name)
    data = manifest(fixture)
    suite = {"name": "SameSuite", "revision": REV, "upstream": "https://github.com/LIJI32/SameSuite/tree/" + REV, "license": "X11; see LICENSE.txt"}
    license_row = {"notice_file": "LICENSE.txt", "notice_sha256": LICENSE_SHA, "spdx": "X11", "rights_basis": "G7", "included_material": LICENSES}
    if data.get("suite") != suite:
        fail("source revision or SameSuite identity differs from the pinned commit")
    if data.get("license") != license_row:
        fail("license/rights metadata differs from the adopted G7 and CC0 basis")
    license_path = fixture / "LICENSE.txt"
    if not license_path.is_file():
        fail("missing license notice LICENSE.txt")
    if digest(license_path.read_bytes()) != LICENSE_SHA:
        fail("X11/CC0 license notice SHA-256 mismatch: LICENSE.txt")
    if data.get("build") != BUILD:
        fail("RGBDS tool version/archive digest/options differ from the pinned 1.0.1 toolchain")
    expected_sources = source_rows(names)
    if data.get("source_files") != expected_sources:
        observed = {row.get("path"): row for row in data.get("source_files", []) if isinstance(row, dict)}
        for row in expected_sources:
            if observed.get(row["path"]) != row:
                fail("source pin mismatch: " + row["path"])
        if not case_name:
            fail("source-file inventory differs from the selected pinned source closure")
    rows = data.get("fixtures")
    aliases = [row.get("alias") for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    if (case_name and not set(names) <= set(aliases)) or (not case_name and aliases != names):
        fail("fixture rows differ from selected cases: expected " + repr(names) + ", got " + repr(aliases))
    expected_files = {name + ".gb" for name in names}
    found_files = {path.relative_to(fixture).as_posix() for path in fixture.rglob("*.gb") if path.is_file()}
    if not expected_files <= found_files or (not case_name and found_files != expected_files):
        fail("committed ROM files differ from selected cases: expected " + repr(sorted(expected_files)) + ", got " + repr(sorted(found_files)))
    rows_by_alias = {row.get("alias"): row for row in rows if isinstance(row, dict)}
    for name in names:
        row = rows_by_alias.get(name)
        if row != fixture_row(name):
            fail("fixture source/model/license metadata differs from the pin: " + name)
        rom = fixture / (name + ".gb")
        if not rom.is_file():
            fail("missing committed ROM: " + rom.name)
        rom_bytes = rom.read_bytes()
        if len(rom_bytes) != 32768 or digest(rom_bytes) != row["sha256"]:
            fail("ROM SHA-256/size mismatch: " + rom.name)
    if not case_name:
        check_eligibility(fixture)
    print("self-check=pass cases=" + ",".join(names))


def call_script(script, fixture, args):
    env = os.environ.copy()
    env["GBB_SAMESUITE_FIXTURE_DIR"] = str(fixture)
    launcher = env.get("GBB_SAMESUITE_BASH") or shutil.which("bash")
    if not launcher:
        fail("Bash executable is not available for recursive self-check")

    def bash_path(value):
        if os.name == "nt" and len(value) >= 3 and value[1] == ":" and value[2] in "\\/":
            return "/" + value[0].lower() + value[2:].replace("\\", "/")
        return value

    command = [launcher, bash_path(str(script)), *(bash_path(str(arg)) for arg in args)]
    return subprocess.run(command, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def copy_fixture(source, target, names):
    target.mkdir(parents=True)
    for filename in ["manifest.json", "LICENSE.txt", "ELIGIBILITY.md"]:
        path = source / filename
        if path.is_file():
            shutil.copy2(path, target / filename)
    for name in names:
        path = source / (name + ".gb")
        if path.is_file():
            (target / path.relative_to(source)).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target / path.relative_to(source))


def self_test(fixture, script, case_name):
    names = selected(case_name)
    manifest(fixture)
    with tempfile.TemporaryDirectory(prefix="gabbaboy-samesuite-selftest-") as temporary:
        root = Path(temporary)
        clean = root / "clean"
        copy_fixture(fixture, clean, names)
        check_args = ["--self-check"] + (["--case", case_name] if case_name else [])
        result = call_script(script, clean, check_args)
        if result.returncode != 0 or "self-check=pass" not in result.stdout:
            fail("clean temporary copy did not pass self-check: " + result.stdout.strip())
        print("positive-control=pass id=clean-copy")

        def mutate(label, diagnostic, change):
            target = root / label
            copy_fixture(fixture, target, names)
            change(target)
            result = call_script(script, target, check_args)
            if result.returncode == 0 or diagnostic not in result.stdout:
                fail("negative control escaped or reported the wrong reason: " + label + " expected=" + diagnostic + " actual=" + result.stdout.strip())
            print("negative-control=pass id=" + label + " diagnostic=" + diagnostic)

        def missing_license(target):
            (target / "LICENSE.txt").unlink()

        def crlf_license(target):
            path = target / "LICENSE.txt"
            content = path.read_bytes().replace(b"\r\n", b"\n")
            path.write_bytes(content.replace(b"\n", b"\r\n"))

        def changed_rom(target):
            path = target / (names[0] + ".gb")
            content = bytearray(path.read_bytes())
            content[0] ^= 1
            path.write_bytes(content)

        def changed_source_hash(target):
            path = target / "manifest.json"
            data = json.loads(path.read_text())
            source_path = (names[0] + ".asm") if names[0].startswith("apu/") else "dma/" + names[0] + ".asm"
            for row in data["source_files"]:
                if row["path"] == source_path:
                    row["sha256"] = "0" * 64
                    break
            path.write_text(json.dumps(data, indent=2) + "\n")

        def wrong_revision(target):
            path = target / "manifest.json"
            data = json.loads(path.read_text())
            data["suite"]["revision"] = "0" * 40
            path.write_text(json.dumps(data, indent=2) + "\n")

        def wrong_tool(target):
            path = target / "manifest.json"
            data = json.loads(path.read_text())
            data["build"]["version"] = "1.0.4"
            path.write_text(json.dumps(data, indent=2) + "\n")

        def extra_row(target):
            path = target / "manifest.json"
            data = json.loads(path.read_text())
            row = copy.deepcopy(data["fixtures"][0])
            row["alias"] = "unapproved_dma_case"
            row["file"] = "unapproved_dma_case.gb"
            data["fixtures"].append(row)
            path.write_text(json.dumps(data, indent=2) + "\n")

        def changed_d06_expectation(target):
            path = target / "manifest.json"
            data = json.loads(path.read_text())
            row = next(row for row in data["fixtures"] if row["alias"] == "hdma_lcd_off")
            row["expectation"] = "Changed expected HDMA5 value: $82."
            path.write_text(json.dumps(data, indent=2) + "\n")

        mutate("missing-license", "missing license notice LICENSE.txt", missing_license)
        mutate("crlf-license-notice", "X11/CC0 license notice SHA-256 mismatch: LICENSE.txt", crlf_license)
        mutate("changed-rom-digest", "ROM SHA-256/size mismatch", changed_rom)
        mutate("changed-source-digest", "source pin mismatch", changed_source_hash)
        mutate("wrong-source-revision", "source revision or SameSuite identity differs", wrong_revision)
        mutate("wrong-tool-pin", "RGBDS tool version/archive digest/options differ", wrong_tool)
        mutate("extra-unapproved-row", "fixture rows differ from selected cases", extra_row)
        if "hdma_lcd_off" in names:
            mutate("changed-d06-expectation", "fixture source/model/license metadata differs from the pin: hdma_lcd_off", changed_d06_expectation)

        rebuilt = root / "rebuilt"
        rebuilt.mkdir()
        for name in names:
            output = rebuilt / (name + ".gb")
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fixture / (name + ".gb"), output)
        compare_args = ["--compare-built", str(rebuilt)] + (["--case", case_name] if case_name else [])
        result = call_script(script, clean, compare_args)
        if result.returncode != 0 or "result=byte-identical" not in result.stdout:
            fail("clean compare-built copy did not pass: " + result.stdout.strip())
        (rebuilt / (names[0] + ".gb")).write_bytes(b"tampered")
        result = call_script(script, clean, compare_args)
        if result.returncode == 0 or "rebuilt ROM differs" not in result.stdout:
            fail("compare-built tamper control escaped: " + result.stdout.strip())
        print("negative-control=pass id=compare-built-tampered diagnostic=rebuilt ROM differs")
    print("self-test=pass cases=" + ",".join(names))


def compare_built(fixture, directory, case_name):
    names = selected(case_name)
    if not directory.is_dir():
        fail("rebuilt ROM directory is missing: " + str(directory))
    expected = {name + ".gb" for name in names}
    actual = {path.relative_to(directory).as_posix() for path in directory.rglob("*.gb") if path.is_file()}
    if actual != expected:
        fail("rebuilt ROM set differs: expected " + repr(sorted(expected)) + ", got " + repr(sorted(actual)))
    for name in names:
        committed, rebuilt = fixture / (name + ".gb"), directory / (name + ".gb")
        if not committed.is_file() or not rebuilt.is_file():
            fail("missing committed or rebuilt ROM: " + name + ".gb")
        if committed.read_bytes() != rebuilt.read_bytes():
            fail("rebuilt ROM differs: " + name + ".gb")
    print("result=byte-identical cases=" + ",".join(names))


def source_check(fixture, source_dir):
    data = manifest(fixture)
    if data["suite"]["revision"] != REV:
        fail("source revision differs from the pinned commit")
    for row in data["source_files"]:
        path = row["path"]
        try:
            content = subprocess.check_output(["git", "-C", str(source_dir), "show", REV + ":" + path])
        except subprocess.CalledProcessError:
            fail("pinned upstream source path is missing: " + path)
        expected = SOURCE.get(path)
        if expected is None or len(content) != expected[0] or digest(content) != expected[1]:
            fail("fetched upstream source digest differs from the pin: " + path)
    upstream_license = subprocess.check_output(["git", "-C", str(source_dir), "show", REV + ":LICENSE"])
    if digest(upstream_license) != UPSTREAM_LICENSE_SHA:
        fail("pinned upstream X11 license digest differs")
    notice = (fixture / "LICENSE.txt").read_bytes()
    if not notice.startswith(upstream_license) or b"SPDX-License-Identifier: CC0-1.0" not in notice:
        fail("committed license notices do not preserve the pinned X11 and CC0 notices")
    hardware = subprocess.check_output(["git", "-C", str(source_dir), "show", REV + ":include/hardware.inc"])
    if b"SPDX-License-Identifier: CC0-1.0" not in hardware:
        fail("pinned hardware.inc is missing its CC0-1.0 notice")


def main():
    action = sys.argv[1]
    fixture = Path(sys.argv[2])
    case_name = sys.argv[3] or None
    script = Path(sys.argv[4])
    if action == "self-check":
        self_check(fixture, case_name, script)
    elif action == "self-test":
        self_test(fixture, script, case_name)
    elif action == "compare-built":
        self_check(fixture, case_name, script)
        compare_built(fixture, Path(sys.argv[5]), case_name)
    elif action == "source-check":
        source_check(fixture, Path(sys.argv[5]))
    else:
        fail("unknown internal operation: " + action)


if __name__ == "__main__":
    main()
PY
}

download_or_find_archive() {
  local archive_name=$1 expected=$2 archive
  archive=$(printenv GBB_RGBDS_ARCHIVE || true)
  if [[ -n "$archive" ]]; then
    [[ -f "$archive" ]] || { echo "RGBDS archive is missing: $archive" >&2; return 1; }
  else
    local cache_root cache_dir home_dir partial
    cache_root=$(printenv XDG_CACHE_HOME || true)
    if [[ -z "$cache_root" ]]; then
      home_dir=$(printenv HOME || printf '/tmp')
      cache_root="$home_dir/.cache"
    fi
    cache_dir="$cache_root/gabbaboy/rgbds-v1.0.1"
    mkdir -p "$cache_dir"
    archive="$cache_dir/$archive_name"
    if [[ ! -f "$archive" ]]; then
      partial="$archive.part.$$"
      trap 'rm -f -- "$partial"' RETURN
      curl --fail --location --silent --show-error \
        "https://github.com/gbdev/rgbds/releases/download/v1.0.1/$archive_name" -o "$partial"
      mv "$partial" "$archive"
      trap - RETURN
    fi
  fi
  local actual supplied
  actual=$(python3 -I -c 'import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$archive")
  [[ "$actual" == "$expected" ]] || { echo "RGBDS archive SHA-256 mismatch: expected $expected, got $actual" >&2; return 1; }
  supplied=$(printenv GBB_RGBDS_ARCHIVE_SHA256 || true)
  if [[ -n "$supplied" && "$supplied" != "$expected" ]]; then
    echo "supplied RGBDS archive digest differs from the pinned 1.0.1 digest" >&2
    return 1
  fi
  printf '%s\n' "$archive"
}

compare_pinned() {
  local archive_name archive_sha archive work_dir source_dir tools_dir build_dir version_line tool name tmp_base
  case "$(uname -s)" in
    Darwin) archive_name="rgbds-macos.zip"; archive_sha="2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645" ;;
    Linux) archive_name="rgbds-linux-x86_64.tar.xz"; archive_sha="80a5cad8dae27e24e46a93041352c47cadbc165103983f41c2b3082c42f6dad9" ;;
    *) echo "unsupported host for pinned RGBDS 1.0.1 reproduction: $(uname -s)" >&2; return 1 ;;
  esac
  archive=$(download_or_find_archive "$archive_name" "$archive_sha")
  tmp_base=$(printenv TMPDIR || printf '/tmp')
  work_dir=$(mktemp -d "$tmp_base/gabbaboy-samesuite.XXXXXXXX")
  trap 'rm -rf -- "$work_dir"' RETURN
  source_dir="$work_dir/source"
  tools_dir="$work_dir/tools"
  mkdir -p "$source_dir" "$tools_dir"
  git -C "$source_dir" init -q
  git -C "$source_dir" fetch -q --depth 1 https://github.com/LIJI32/SameSuite.git f15645fb049a47ea235f6d2c9a033e72d8087901
  git -C "$source_dir" checkout -q --detach FETCH_HEAD
  [[ "$(git -C "$source_dir" rev-parse HEAD)" == "f15645fb049a47ea235f6d2c9a033e72d8087901" ]] || {
    echo "fetched SameSuite commit differs from the pin" >&2
    return 1
  }
  run_python source-check "$fixture_dir" "$case_name" "$script_dir/reproduce-samesuite.sh" "$source_dir"
  if [[ "$archive_name" == *.zip ]]; then
    unzip -q "$archive" -d "$tools_dir"
  else
    tar -xJf "$archive" -C "$tools_dir"
  fi
  for tool in rgbasm rgblink rgbfix; do
    [[ -x "$tools_dir/$tool" ]] || { echo "pinned RGBDS archive does not contain executable $tool at its root" >&2; return 1; }
    version_line=$("$tools_dir/$tool" --version | sed -n '1p')
    [[ "$version_line" == "$tool v1.0.1" ]] || { echo "$tool version mismatch: expected v1.0.1, got $version_line" >&2; return 1; }
  done
  build_dir=$(printenv GBB_SAMESUITE_BUILD_DIR || true)
  if [[ -n "$build_dir" ]]; then
    [[ ! -e "$build_dir" || -z "$(find "$build_dir" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]] || {
      echo "requested SameSuite build directory is not empty: $build_dir" >&2
      return 1
    }
    mkdir -p "$build_dir"
  else
    build_dir="$work_dir/build"
    mkdir -p "$build_dir"
  fi
  while IFS= read -r name; do
    [[ -n "$name" ]] || continue
    mkdir -p "$build_dir/$(dirname "$name")"
    local source_path
    if [[ "$name" == apu/* ]]; then source_path="$name.asm"; else source_path="dma/$name.asm"; fi
    (cd "$source_dir" && "$tools_dir/rgbasm" -I include/ -o "$build_dir/$name.o" "$source_path") 2>"$build_dir/$name.rgbasm.log"
    "$tools_dir/rgblink" -o "$build_dir/$name.gb" -n "$build_dir/$name.sym" "$build_dir/$name.o"
    "$tools_dir/rgbfix" -jv "$build_dir/$name.gb"
  done < <(python3 -I -c 'import json,sys; m=json.load(open(sys.argv[1])); case=sys.argv[2]; print("\n".join(row["alias"] for row in m["fixtures"] if not case or row["alias"] == case))' "$fixture_dir/manifest.json" "$case_name")
  run_python compare-built "$fixture_dir" "$case_name" "$script_dir/reproduce-samesuite.sh" "$build_dir"
  echo "reproduction=source:f15645fb049a47ea235f6d2c9a033e72d8087901 tool:RGBDS-1.0.1 archive:$archive_sha"
}

case "$mode" in
  self-check) run_python self-check "$fixture_dir" "$case_name" "$script_dir/reproduce-samesuite.sh" "" ;;
  self-test) run_python self-test "$fixture_dir" "$case_name" "$script_dir/reproduce-samesuite.sh" "" ;;
  compare-built) run_python compare-built "$fixture_dir" "$case_name" "$script_dir/reproduce-samesuite.sh" "$built_dir" ;;
  compare-pinned)
    run_python self-check "$fixture_dir" "$case_name" "$script_dir/reproduce-samesuite.sh" ""
    compare_pinned
    ;;
  default)
    run_python self-check "$fixture_dir" "" "$script_dir/reproduce-samesuite.sh" ""
    run_python self-test "$fixture_dir" "" "$script_dir/reproduce-samesuite.sh" ""
    compare_pinned
    ;;
esac
