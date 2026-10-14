#!/usr/bin/env bash
# Verify and reproduce the original CGB HDMA guest with the project's pinned RGBDS release.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(cd "$script_dir/../.." && pwd -P)
mode=${1:-}
shift || true
exec python3 -I - "$repo_root" "$mode" "$@" <<'PY'
import copy
import hashlib
import json
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

root = pathlib.Path(sys.argv[1]).resolve()
mode = sys.argv[2]
args = sys.argv[3:]
fixture_dir = root / "fixtures/cgb-hdma"
source_path = fixture_dir / "hblank.asm"
rom_path = fixture_dir / "hblank.gb"
manifest_path = fixture_dir / "manifest.json"
license_path = fixture_dir / "LICENSE.txt"
reference_path = root / "fixtures/cgb-colour/manifest.json"
PIN_KEYS = ("assembler", "version", "archive", "archive_sha256",
            "ci_archive", "ci_archive_sha256")


def fail(message, status=1):
    print(f"result={'differs' if status == 1 else 'error'} reason={message}")
    raise SystemExit(status)


def read_manifest(candidate=None):
    if candidate is not None:
        return candidate
    try:
        return json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        fail(f"manifest-unreadable-{type(error).__name__}", 2)


def header_checksum(data):
    value = 0
    for byte in data[0x134:0x14D]:
        value = (value - byte - 1) & 0xFF
    return value


def checksummed_twin(data):
    twin = bytearray(data)
    signature = bytes.fromhex("e055")
    replacement = bytes.fromhex("0000")
    count = twin.count(signature)
    if count != 2:
        fail(f"control-ff55-signature-count-{count}-expected-2", 2)
    twin = twin.replace(signature, replacement)
    twin[0x14D] = header_checksum(twin)
    total = sum(twin[:0x14E]) + sum(twin[0x150:])
    twin[0x14E] = (total >> 8) & 0xFF
    twin[0x14F] = total & 0xFF
    return bytes(twin)


def validate(source_bytes=None, rom_bytes=None, candidate_manifest=None):
    manifest = read_manifest(candidate_manifest)
    try:
        source_data = source_path.read_bytes() if source_bytes is None else source_bytes
        rom_data = rom_path.read_bytes() if rom_bytes is None else rom_bytes
        reference = json.loads(reference_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        return f"input-unreadable-{type(error).__name__}"

    if manifest.get("id") != "cgb-hdma":
        return "manifest-id-not-cgb-hdma"
    if manifest.get("source_identity") != "Original GabbaBoy project-authored assembly":
        return "source-identity-not-project-owned"
    if manifest.get("source") != ["hblank.asm"]:
        return "manifest-source-list-differs"
    if not manifest.get("license", "").startswith("MIT;") or not license_path.is_file():
        return "missing-original-mit-license-notice"
    license_text = license_path.read_text(errors="replace")
    if "original CGB HBlank-DMA guest" not in license_text or "not derived" not in license_text:
        return "license-does-not-identify-original-guest"
    if "not hardware evidence" not in manifest.get("protocol", {}).get("summary", "") and \
       "not hardware evidence" not in manifest.get("profile", {}).get("applicability", "") and \
       "not hardware evidence" not in manifest.get("protocol", {}).get("evidence_class", ""):
        if "not physical hardware evidence" not in manifest.get("profile", {}).get("applicability", ""):
            return "evidence-scope-does-not-exclude-hardware"

    build = manifest.get("build", {})
    reference_build = reference.get("build", {})
    for key in PIN_KEYS:
        if not build.get(key):
            return f"build-pin-{key}-missing"
        if build.get(key) != reference_build.get(key):
            return f"build-pin-{key}-differs-from-cgb-colour"
    if build.get("version") != "1.0.1" or build.get("assembler") != "RGBDS":
        return "manifest-must-pin-rgbds-1.0.1"

    source_digest = manifest.get("source_sha256", {}).get("hblank.asm")
    actual_source_digest = hashlib.sha256(source_data).hexdigest()
    if actual_source_digest != source_digest:
        return "source-sha256-mismatch-hblank.asm"
    source_text = source_data.decode("utf-8", errors="replace")
    if source_text.count("ldh [rHDMA5], a") != 2:
        return "source-ff55-start-count-differs-from-two"
    if "SECTION \"DMA source\", ROM0[$0400]" not in source_text:
        return "source-dma-data-offset-differs"
    for required in ("RGB555 001F", "RGB555 03E0", "RGB555 7C00", "RGB555 7FFF",
                     "ld a, $A5", "ld a, $EE",
                     "ld [$C000], a", "ld [$C001], a", "ld [$C002], a",
                     "ld [$C003], a", "ld [$C004], a", "ld [$C005], a"):
        if required not in source_text:
            return "source-guest-contract-missing-" + re.sub(r"[^A-Za-z0-9]+", "-", required).strip("-")

    rows = manifest.get("fixtures", [])
    if len(rows) != 1 or rows[0].get("file") != "hblank.gb":
        return "fixture-list-differs"
    row = rows[0]
    if row.get("recipe", {}).get("source") != "hblank.asm" or \
       row.get("recipe", {}).get("defines") != [] or \
       row.get("recipe", {}).get("rgbfix_flags") != ["-c", "-v", "-p", "0"]:
        return "fixture-build-recipe-differs"
    if len(rom_data) != 32768 or row.get("size_bytes") != 32768:
        return "rom-size-mismatch-hblank.gb"
    if rom_data[0x143] != 0x80 or rom_data[0x147] != 0x00 or rom_data[0x148] != 0x00 or \
       rom_data[0x149] != 0x00:
        return "rom-header-profile-mismatch"

    protocol = manifest.get("protocol", {})
    markers = protocol.get("guest_markers", {})
    if not all(markers.get(address) for address in ("C000", "C001", "C002", "C003", "C004", "C005")):
        return "guest-marker-contract-incomplete"
    pixels = protocol.get("pixels", {})
    expected_pixels = (pixels.get("success_quadrants_rgb555"), pixels.get("failure_rgb555"))
    if expected_pixels != ({"top_left": "0x001F", "top_right": "0x03E0",
                            "bottom_left": "0x7C00", "bottom_right": "0x7FFF"}, "0x7FFF"):
        return "source-derived-pixel-contract-differs"
    if "every 8x8 tile repeats" not in pixels.get("success_regions", "") or \
       "four 4x4 quadrants" not in pixels.get("success_regions", "") or \
       "every pixel white RGB555 0x7FFF" not in pixels.get("failure_regions", ""):
        return "source-derived-pixel-regions-incomplete"
    if any(value not in source_text for value in ("RGB555 001F", "RGB555 03E0",
                                                   "RGB555 7C00", "RGB555 7FFF")):
        return "source-derived-pixel-comments-missing"

    source_data_pin = protocol.get("source_data", {})
    if source_data_pin.get("rom_offset") != "0x0400":
        return "source-data-offset-pin-differs"
    bank0 = bytes.fromhex(source_data_pin.get("bank0_tile0_hex", ""))
    bank1 = bytes.fromhex(source_data_pin.get("bank1_tile0_hex", ""))
    if bank0 != bytes([0xF0, 0x0F] * 4 + [0xF0, 0xF0] * 4) or \
       bank1 != bytes([0x0F, 0x0F] * 8):
        return "source-data-pattern-pin-differs"
    if "db $F0, $0F" not in source_text or "db $0F, $0F" not in source_text:
        return "source-data-pattern-not-in-assembly"
    if rom_data[0x400:0x410] != bank0 or rom_data[0x410:0x420] != bank1:
        return "rom-source-data-pattern-mismatch"

    control = protocol.get("no_transfer_control", {})
    if control.get("patch_signature_hex") != "e055" or \
       control.get("replacement_hex") != "0000" or \
       control.get("expected_unique_sites") != 2:
        return "no-transfer-control-pin-differs"
    if rom_data.count(bytes.fromhex("e055")) != 2:
        return "rom-ff55-signature-count-differs-from-two"
    expected_control = control.get("expected_marker", "")
    if "C000=0xEE" not in expected_control or "C001=0xFF" not in expected_control or \
       "C005=0x01" not in expected_control:
        return "no-transfer-control-marker-contract-differs"

    if rom_data[0x14D] != header_checksum(rom_data):
        return "rom-header-checksum-invalid"
    actual_rom_digest = hashlib.sha256(rom_data).hexdigest()
    if actual_rom_digest != row.get("sha256"):
        return "rom-sha256-mismatch-hblank.gb"
    return None


def pinned_archive(build):
    system = platform.system()
    if system == "Darwin":
        name, digest = build["archive"], build["archive_sha256"]
    elif system == "Linux":
        name, digest = build["ci_archive"], build["ci_archive_sha256"]
    else:
        fail(f"unsupported-host-{system}", 2)
    supplied = os.environ.get("GBB_RGBDS_ARCHIVE")
    if supplied:
        archive = pathlib.Path(supplied).expanduser()
        if not archive.is_absolute():
            archive = root / archive
        if not archive.is_file():
            fail("GBB_RGBDS_ARCHIVE-not-a-regular-file", 2)
    else:
        cache_root = pathlib.Path(os.environ.get("XDG_CACHE_HOME", pathlib.Path.home() / ".cache"))
        archive = cache_root / "gabbaboy/rgbds-v1.0.1" / name
        archive.parent.mkdir(parents=True, exist_ok=True)
        if not archive.is_file():
            partial = archive.with_name(archive.name + f".part.{os.getpid()}")
            url = f"https://github.com/gbdev/rgbds/releases/download/v1.0.1/{name}"
            try:
                subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error",
                                url, "-o", str(partial)], check=True)
                partial.replace(archive)
            finally:
                partial.unlink(missing_ok=True)
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != digest:
        fail(f"rgbds-archive-sha256-mismatch-expected-{digest}-actual-{actual}")
    supplied_digest = os.environ.get("GBB_RGBDS_ARCHIVE_SHA256")
    if supplied_digest and supplied_digest != digest:
        fail("supplied-rgbds-archive-digest-differs-from-pin")
    return archive, name, digest


def compare_pinned():
    reason = validate()
    if reason:
        fail(reason)
    manifest = read_manifest()
    archive, archive_name, archive_digest = pinned_archive(manifest["build"])
    with tempfile.TemporaryDirectory(prefix="gabbaboy-cgb-hdma-") as temporary:
        work = pathlib.Path(temporary)
        tools = work / "tools"
        tools.mkdir()
        if archive_name.endswith(".zip"):
            subprocess.run(["unzip", "-q", str(archive), "-d", str(tools)], check=True)
        else:
            with tarfile.open(archive, "r:xz") as bundle:
                bundle.extractall(tools, filter="data")
        executable_dir = tools
        for name in ("rgbasm", "rgblink", "rgbfix"):
            executable = executable_dir / name
            if not executable.is_file() or not os.access(executable, os.X_OK):
                fail(f"pinned-rgbds-archive-missing-{name}", 2)
            first_line = subprocess.run([str(executable), "--version"], check=True,
                                        capture_output=True, text=True).stdout.splitlines()[0]
            if first_line != f"{name} v1.0.1":
                fail(f"{name}-version-mismatch-{first_line}", 2)
        obj = work / "hblank.o"
        rebuilt = work / "hblank.gb"
        steps = [
            [str(executable_dir / "rgbasm"), "-I", str(fixture_dir) + os.sep,
             "-o", str(obj), str(source_path)],
            [str(executable_dir / "rgblink"), "-o", str(rebuilt), str(obj)],
            [str(executable_dir / "rgbfix"), "-c", "-v", "-p", "0", str(rebuilt)],
        ]
        for command in steps:
            done = subprocess.run(command, cwd=root, capture_output=True, text=True)
            if done.returncode:
                detail = (done.stderr or done.stdout).strip().replace("\n", " | ")[:240]
                fail(f"tool-failed-{pathlib.Path(command[0]).name}-{detail}", 2)
        rebuilt_data = rebuilt.read_bytes()
        checked_data = rom_path.read_bytes()
        structural_reason = validate(rom_bytes=rebuilt_data)
        if structural_reason not in (None, "rom-sha256-mismatch-hblank.gb"):
            fail(f"rebuilt-{structural_reason}")
        if len(rebuilt_data) != 32768:
            fail("rebuilt-size-mismatch-hblank.gb")
        actual_digest = hashlib.sha256(rebuilt_data).hexdigest()
        if actual_digest != manifest["fixtures"][0]["sha256"]:
            fail(f"rebuilt-sha256-mismatch-hblank.gb-expected-{manifest['fixtures'][0]['sha256']}-actual-{actual_digest}")
        if rebuilt_data != checked_data:
            fail("rebuilt-rom-differs-from-checked-in-hblank.gb")
    print(f"rom=hblank.gb size_bytes=32768 sha256={actual_digest}")
    print(f"rgbds=1.0.1 archive_sha256={archive_digest}")
    print("result=byte-identical roms=1")


def self_test():
    reason = validate()
    if reason:
        fail(f"clean-input-{reason}")
    source_data = source_path.read_bytes()
    rom_data = rom_path.read_bytes()
    manifest = read_manifest()
    source_reason = validate(source_bytes=source_data + b"\n")
    if source_reason != "source-sha256-mismatch-hblank.asm":
        fail(f"source-negative-control-not-detected-{source_reason}")
    mutated_rom = bytearray(rom_data)
    mutated_rom[0x3FFF] ^= 1
    rom_reason = validate(rom_bytes=bytes(mutated_rom))
    if rom_reason != "rom-sha256-mismatch-hblank.gb":
        fail(f"rom-negative-control-not-detected-{rom_reason}")
    mutated_data = bytearray(rom_data)
    mutated_data[0x400] ^= 1
    data_reason = validate(rom_bytes=bytes(mutated_data))
    if data_reason != "rom-source-data-pattern-mismatch":
        fail(f"source-data-negative-control-not-detected-{data_reason}")
    mutated_manifest = copy.deepcopy(manifest)
    mutated_manifest["build"]["archive_sha256"] = "0" * 64
    pin_reason = validate(candidate_manifest=mutated_manifest)
    if pin_reason != "build-pin-archive_sha256-differs-from-cgb-colour":
        fail(f"pin-negative-control-not-detected-{pin_reason}")
    twin = checksummed_twin(rom_data)
    signature = bytes.fromhex("e055")
    if twin.count(signature) != 0 or twin[0x14D] != header_checksum(twin):
        fail("no-transfer-negative-control-mutation-invalid")
    print("result=self-test-pass controls=source-sha256,rom-sha256,source-data-pattern,rgbds-pin,no-transfer-signature")


def write_no_transfer():
    if len(args) != 1:
        fail("--write-no-transfer-requires-output-path", 2)
    reason = validate()
    if reason:
        fail(reason)
    output = pathlib.Path(args[0]).expanduser().resolve()
    try:
        relative = output.relative_to(root)
    except ValueError:
        fail("no-transfer-output-must-be-inside-project-build-tree", 2)
    if not relative.parts or relative.parts[0] not in ("build", "build-player"):
        fail("no-transfer-output-must-be-inside-project-build-tree", 2)
    if output == rom_path.resolve() or not output.parent.is_dir():
        fail("no-transfer-output-path-invalid", 2)
    twin = checksummed_twin(rom_path.read_bytes())
    output.write_bytes(twin)
    print(f"control=disabled-transfer sites=2 output={relative.as_posix()}")


if mode == "--self-check":
    reason = validate()
    if reason:
        fail(reason)
    print(f"result=clean source_sha256={hashlib.sha256(source_path.read_bytes()).hexdigest()} "
          f"rom_sha256={hashlib.sha256(rom_path.read_bytes()).hexdigest()}")
elif mode == "--self-test":
    self_test()
elif mode == "--compare-pinned":
    compare_pinned()
elif mode == "--write-no-transfer":
    write_no_transfer()
else:
    fail("usage-expected---self-check---self-test---compare-pinned-or---write-no-transfer", 2)
PY
