#!/usr/bin/env python3
"""Fail-closed admission adapter and original synthetic acid2 tracer control."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import math
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
ADMISSION_CHECKER_PATH = "tests/scripts/verify-diagnostic-admission.py"
PHASE20_CHECKER_PATH = "tests/scripts/verify-fixture-admission.py"
PHASE20_POLICY_PATH = "cmake/FixtureAdmissionPolicy.json"
PHASE20 = ROOT / "tests/scripts/verify-fixture-admission.py"
CANDIDATE_CHECKER_PATH = "tests/scripts/verify-cgb-candidates.py"
CANDIDATE_CLOSEOUT_PATH = "tests/data/v04-closeout.json"
DIAGNOSTIC_CLOSEOUT_PATH = "tests/external/diagnostic-closeout.json"
GBMICROTEST_INVENTORY_PATH = "tests/external/gbmicrotest-inventory.json"
DIAGNOSTIC_RIGHTS_REVISION = "508f37f191ec76506d75921e97430148f4909209"
DIAGNOSTIC_RIGHTS_SHA256 = "e44695dc2b5efebdbc01aed9179466d25ac8f5a55bc99a8ce94217b4adf262f9"
DIAGNOSTIC_RIGHTS_SIZE = 39813
CANDIDATE_CONTRACT_PATHS = (
    CANDIDATE_CHECKER_PATH,
    PHASE20_CHECKER_PATH,
    "tests/cmake/game-evidence.cmake",
    "docs/cgb-game-candidates.md",
    CANDIDATE_CLOSEOUT_PATH,
)
ACID2_TOOL = ROOT / "tests/scripts/run-acid2-local.py"
CONTROL_SOURCE = ROOT / "tests/acid2/control.asm"
SCANNER = ROOT / "cmake/ScanForbiddenFixtures.cmake"
BASELINE_COMMIT = "7cc6495e64f3645caa120e7458f754585b788985"
MAX_SOURCE_BYTES = 64 * 1024
MAX_ROM_BYTES = 32 * 1024
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_INVENTORY_BYTES = 2 * 1024 * 1024
MAX_PROCESS_OUTPUT = 64 * 1024
CONTROL_BUDGET_HALF_DOTS = 350_000
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
IDENTITY_FIELDS = ("rom", "reference", "source", "layout", "glyph", "allowlist", "mask", "overlay")
SOURCE_CELL_ALLOWLIST = ((2, 3),)
CONTROL_GLYPH_BYTES = b"\x80" + bytes(15)
GBMICROTEST_COMMIT = "463eb6bc0fe31d61781ef63060ad6d74090c0255"
GBMICROTEST_TREE = "9b692d1a028beea00a9fc08b89bc6160dd268efa"
GBMICROTEST_CASE_COUNT = 513
GBMICROTEST_PROTOCOL_COUNTS = {
    "shared-verdict-macros": 480,
    "inline-ff80-ff82": 2,
    "no-verdict-protocol": 31,
}
GBMICROTEST_ROSTER_PROJECTION_SHA256 = "29c610580ee8d953ac9a85a80db7d46bba80908e888cb91d65e327ce25a3651b"
GBMICROTEST_SELECTED_CASE = "div_inc_timing_a"
GBMICROTEST_SELECTED_SOURCE_BLOB = "8b6d36902ca5ff2fee6f98c308639dfb309272cc"
GBMICROTEST_SELECTED_SOURCE_SIZE = 268
GBMICROTEST_SELECTED_SOURCE_SHA256 = "ea6017487ac860fa29e54c43d2d1a73659ed3662b7ba3c7c91cc41faf5ef6deb"
GBMICROTEST_MACROS_BLOB = "085c7d472fbaa724756968936ea84861962af8f1"
GBMICROTEST_MACROS_SIZE = 6175
GBMICROTEST_MACROS_SHA256 = "d3964ffc94d5ef110b3536b7bb9448840ef88d718ebca1ee662670680164c3a3"
GBMICROTEST_SELECTED_ROM_BLOB = "8ff913924540b1bbc4363744f020b38e96c94a3a"
GBMICROTEST_SELECTED_ROM_SHA256 = "1530b5a34af78e182c8b1f5f9043f8e5ae3e9f2fac13d43f3c5714eece282706"
GBMICROTEST_SELECTED_DERIVATIVE_SHA256 = "53b0624af64524fe7cdf9b0aed3456ca60c7b30fe25cd5202b6b77855f57ffa8"
GBMICROTEST_REVIEW_DIR = pathlib.Path("build/phase24/source-review/gbmicrotest")
GBMICROTEST_FIXTURE_DIR = pathlib.Path("fixtures/gbmicrotest")
GBMICROTEST_ADMISSION_COMMIT = "3c31824e61e5f2b0b88912e8e7e29acf42a5a8ab"
GBMICROTEST_MANIFEST_SHA256 = "d3aedaa5d89f583bea2951a9a58a3190ff2314fafbfa53b7e63e98ed6349cb7c"
GBMICROTEST_BUNDLE_SHA256 = "b810271e7bde4ffb05104c5d3aa772731118b45be3c93f38d2bb797e66e59780"
GBMICROTEST_IDENTITY_SHA256 = "c18a7118c6172a3202893db5212f00eea67d015b309248da50884e4f4f6059e3"
GBMICROTEST_LOGO_START, GBMICROTEST_LOGO_END = 0x0104, 0x0133
GBMICROTEST_CHECKSUM_START, GBMICROTEST_CHECKSUM_END = 0x014E, 0x014F
GBMICROTEST_LICENSE_BLOB = "ca05fdbac9ec607636037171ee3856ea2a3378dd"
GBMICROTEST_LICENSE_SHA256 = "0b3557142dfcce65428fafb9c8254d9d59c027a008af4810867efd7342b77c25"
GBMICROTEST_README_BLOB = "e184a72ed5f6f1b76f5124762c6ed3f79f139e4e"
GBMICROTEST_README_SHA256 = "15610d3e922658503b5250f1e9e0106d3ad6bdee7ff43003147f5871a81a3b92"
GBMICROTEST_LICENSE_ISSUE = {
    "number": 1,
    "title": "License?",
    "body": "Under what license are these provided?",
    "url": "https://github.com/aappleby/gbmicrotest/issues/1",
    "comment_id": 2080090499,
    "comment_author": "aappleby",
    "comment_body": "License added.",
    "comment_url": "https://github.com/aappleby/gbmicrotest/issues/1#issuecomment-2080090499",
}
GBMICROTEST_LICENSE_COMMIT = {
    "sha": GBMICROTEST_COMMIT,
    "subject": "Create LICENSE",
    "changed_paths": ["LICENSE"],
}
GBMICROTEST_HEADER_BLOB = "aba48b4af33aabedc8e86adad5e5e692f6f4a348"
GBMICROTEST_HEADER_SHA256 = "380ab2e41fee82c23881b13650e6301b79809e7baa1d3c828363156a70ba9afd"
GBMICROTEST_BUILD_BLOB = "eb0ddc1368e3a777ef9787dc056d756e95c19102"
GBMICROTEST_BUILD_SHA256 = "c726ca6214cb3861fef0da43da2eebc69f7c63e944b61746be5ec028db977488"
GBMICROTEST_INLINE_CASES = frozenset(("mbc1_ram_banks", "mbc1_rom_banks"))
ACID2_FIXTURE_MANIFEST = "fixtures/acid2/manifest.json"
ACID2_FIXTURE_ADMISSION_PIN = "fixtures/acid2/admission.commit"
ACID2_FIXTURE_BUNDLE = "fixtures/acid2/derivatives.tar"
ACID2_FIXTURE_NOTICE = "fixtures/acid2/LICENSE.txt"
ACID2_FIXTURE_SOURCES = "fixtures/acid2/SOURCES.md"
ACID2_FIXTURE_ADMISSION_COMMIT = "3d0587d49e7d88815c6af7dc36f4810579a8dc48"
ACID2_FIXTURE_MANIFEST_SHA256 = "7f198d5964a8547d1a122d5d64d395547ba6f365264cdb00abf190a5880c5da6"
ACID2_FIXTURE_BUNDLE_SHA256 = "bd7f78881d6964e9396128814c769f93ef661030290c5e66b9b8fda5b040f5cb"
ACID2_FIXTURE_BUNDLE_SIZE = 296960
ACID2_FIXTURE_NOTICE_SHA256 = "2b5ed6f8abbded3913a08ebe8f4eedb340735efc3b024570244d6efa73418044"
ACID2_DERIVATIVES = {
    "dmg": ("derivatives/dmg-acid2.gb",
            "6d3e5aca5f6d2ba31337ae61c1994e56f1780196c96cc645d54de378d39bbe82",
            "dmg-cpu-b"),
    "cgb": ("derivatives/cgb-acid2.gbc",
            "62a93fce12ef60938eefce81d02113a75e1a52b2631aa3d6f16388dc697837e2",
            "cgb-cpu-e"),
}
ACID2_COMPARISON_PROFILES = ("dmg", "dmg-on-cgb", "cgb")
ACID2_PROFILE_EXPECTATIONS = {
    "dmg": {"rom_kind": "dmg", "runner_model": "dmg-cpu-b", "mode": "dmg",
            "reference_path": "source/dmg/img/reference-dmg.png",
            "reference_sha256": "ca966d50895c7efef05838590d148c2cbfd7fba57dab986f25b35b4da71abb57",
            "reference_size_bytes": 787,
            "mask_path": "masks/dmg.bin",
            "mask_sha256": "bfc6ae61c3ab4753ac5c11f5c5bac8a7d6d6873767737a72e6c5d31ae0937098",
            "masked_pixels": 3200, "compared_pixels": 19840},
    "dmg-on-cgb": {"rom_kind": "dmg", "runner_model": "cgb-cpu-e", "mode": "dmg",
                    "reference_path": "source/dmg/img/reference-cgb.png",
                    "reference_sha256": "cbf039fd613a6db3c3d830a6a1d887efbc892aea4578ffc569b61f66a9e07ced",
                    "reference_size_bytes": 882,
                    "mask_path": "masks/dmg.bin",
                    "mask_sha256": "bfc6ae61c3ab4753ac5c11f5c5bac8a7d6d6873767737a72e6c5d31ae0937098",
                    "masked_pixels": 3200, "compared_pixels": 19840},
    "cgb": {"rom_kind": "cgb", "runner_model": "cgb-cpu-e", "mode": "cgb",
            "reference_path": "source/cgb/img/reference.png",
            "reference_sha256": "9ea9c262c5383353e77d715d021a0f7c5ccbe438f88082cb225756e50c4fdf01",
            "reference_size_bytes": 870,
            "mask_path": "masks/cgb.bin",
            "mask_sha256": "95219a5b1d6d5df70de9af7896cb9bc9c2194e133e1070c67e4414aa58d227a9",
            "masked_pixels": 3328, "compared_pixels": 19712},
}
ACID2_RUNTIME_EVIDENCE_PATH = "build/phase24/acid2-runtime.json"
DIAGNOSTIC_RUNTIME_PREFLIGHT_PATH = "build/phase24/diagnostic-runtime-preflight.json"
DIAGNOSTIC_RUNTIME_FINAL_PATH = "build/phase24/diagnostic-runtime.json"
GBMICROTEST_RUNTIME_PREFLIGHT_PATH = "build/phase24/gbmicrotest-runtime-preflight.json"
GBMICROTEST_RUNTIME_FINAL_PATH = "build/phase24/gbmicrotest-runtime.json"
LEGACY_GBMICROTEST_PREFLIGHT_SHA256 = "6ce0c3d8a7164ca993802251ec9f3197bcf190a224777b45d6e18c6de03c470f"
GBMICROTEST_INITIAL_EXCLUSIONS = frozenset((
    "000-oam_lock", "000-write_to_x8000", "001-vram_unlocked", "002-vram_locked",
    "004-tima_boot_phase", "004-tima_cycle_timer", "007-lcd_on_stat", "400-dma",
    "500-scx-timing", "800-ppu-latch-scx", "801-ppu-latch-scy",
    "802-ppu-latch-tileselect", "803-ppu-latch-bgdisplay", "audio_testbench",
    "cpu_bus_1", "dma_basic", "flood_vram", "lcdon_write_timing", "ly_while_lcd_off",
    "minimal", "mode2_stat_int_to_oam_unlock", "oam_sprite_trashing", "poweron",
    "ppu_scx_vs_bgp", "ppu_sprite_testbench", "ppu_spritex_vs_scx", "ppu_win_vs_wx",
    "ppu_wx_early", "temp", "toggle_lcdc", "wave_write_to_0xC003",
))
REQUIRED_GATE_IDS = (
    "acid2_source_and_gitlink_identity",
    "acid2_derivative_build_reproducibility",
    "acid2_component_rights_and_output_scope",
    "acid2_profile_applicability",
    "gbmicrotest_complete_roster_identity",
    "gbmicrotest_component_rights_and_output_scope",
    "gbmicrotest_prebuilt_rom_sha256",
    "gbmicrotest_case_applicability",
    "gbmicrotest_independent_oracle",
)
REQUIRED_COMPONENT_IDS = (
    "acid2_source_code",
    "acid2_footer_graphics",
    "acid2_reference_images",
    "mgblib_font_data",
    "project_font_replacement",
    "gbmicrotest_source_code",
    "gbmicrotest_prebuilt_roms",
    "gbmicrotest_nintendo_logo",
    "diagnostic_notices_and_derivative_outputs",
)


class AdmissionRefused(ValueError):
    pass


def _git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _header_checksum(rom: bytes) -> int:
    result = 0
    for offset in range(0x134, 0x14D):
        result = (result - rom[offset] - 1) & 0xFF
    return result


def build_bootless_derivative(original: bytes) -> bytes:
    """Reproduce the selected, source-reviewed logo removal and checksum update."""
    if (len(original) != 32768 or sha256(original) != GBMICROTEST_SELECTED_ROM_SHA256
            or _git_blob_sha1(original) != GBMICROTEST_SELECTED_ROM_BLOB):
        raise AdmissionRefused("gbmicrotest-original-identity-mismatch")
    if _header_checksum(original) != original[0x14D]:
        raise AdmissionRefused("gbmicrotest-original-header-checksum-invalid")
    original_checksum = (original[0x14E] << 8) | original[0x14F]
    if (sum(original[:0x14E] + original[0x150:]) & 0xFFFF) != original_checksum or original_checksum != 0x2C3E:
        raise AdmissionRefused("gbmicrotest-original-global-checksum-invalid")
    result = bytearray(original)
    result[GBMICROTEST_LOGO_START:GBMICROTEST_LOGO_END + 1] = bytes(GBMICROTEST_LOGO_END - GBMICROTEST_LOGO_START + 1)
    result[GBMICROTEST_CHECKSUM_START:GBMICROTEST_CHECKSUM_END + 1] = b"\0\0"
    checksum = sum(result[:0x14E] + result[0x150:]) & 0xFFFF
    result[0x14E], result[0x14F] = checksum >> 8, checksum & 0xFF
    output = bytes(result)
    allowed = set(range(GBMICROTEST_LOGO_START, GBMICROTEST_LOGO_END + 1)) | {0x14E, 0x14F}
    changed = {i for i, (before, after) in enumerate(zip(original, output, strict=True)) if before != after}
    if not changed or not changed <= allowed:
        raise AdmissionRefused("gbmicrotest-derivative-change-allowlist-failed")
    if (any(output[i] for i in range(GBMICROTEST_LOGO_START, GBMICROTEST_LOGO_END + 1))
            or output[0x14D] != original[0x14D] or _header_checksum(output) != output[0x14D]):
        raise AdmissionRefused("gbmicrotest-derivative-header-checksum-invalid")
    derived_checksum = (output[0x14E] << 8) | output[0x14F]
    if ((sum(output[:0x14E] + output[0x150:]) & 0xFFFF) != derived_checksum
            or derived_checksum != 0x16F8 or sha256(output) != GBMICROTEST_SELECTED_DERIVATIVE_SHA256):
        raise AdmissionRefused("gbmicrotest-derivative-identity-invalid")
    return output


def _deterministic_tar(members: dict[str, bytes]) -> bytes:
    target = io.BytesIO()
    with tarfile.open(fileobj=target, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name, data in sorted(members.items()):
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.uid, info.gid, info.mtime = len(data), 0o644, 0, 0, 0
            info.uname = info.gname = ""
            archive.addfile(info, io.BytesIO(data))
    return target.getvalue()


def prepare_gbmicrotest_fixture(root: pathlib.Path) -> None:
    root = root.resolve(strict=True)
    review, fixture = root / GBMICROTEST_REVIEW_DIR, root / GBMICROTEST_FIXTURE_DIR
    ignored = subprocess.run(["git", "check-ignore", "-q", str(GBMICROTEST_REVIEW_DIR / "local-review.json")],
                             cwd=root, check=False, timeout=5)
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(GBMICROTEST_REVIEW_DIR / "bin/div_inc_timing_a.gb")],
                             cwd=root, capture_output=True, check=False, timeout=5)
    if ignored.returncode != 0 or tracked.returncode == 0 or review.is_symlink() or not review.is_dir():
        raise AdmissionRefused("gbmicrotest-review-area-not-ignored-or-bounded")
    if sum(p.stat().st_size for p in review.rglob("*") if p.is_file() and not p.is_symlink()) > 1024 * 1024:
        raise AdmissionRefused("gbmicrotest-review-area-size-limit")
    fixture.mkdir(parents=True, exist_ok=True)
    names = ("cohort.tar", "LICENSE.txt", "SOURCES.md", "identity.json", "manifest.json", "admission.commit")
    if any((fixture / name).exists() or (fixture / name).is_symlink() for name in names):
        raise AdmissionRefused("gbmicrotest-fixture-output-already-exists")

    specs = {
        "tests/div_inc_timing_a.s": (GBMICROTEST_SELECTED_SOURCE_BLOB, GBMICROTEST_SELECTED_SOURCE_SHA256, 268),
        "tests/macros.inc": (GBMICROTEST_MACROS_BLOB, GBMICROTEST_MACROS_SHA256, 6175),
        "tests/header.inc": (GBMICROTEST_HEADER_BLOB, GBMICROTEST_HEADER_SHA256, 956),
        "README.md": (GBMICROTEST_README_BLOB, GBMICROTEST_README_SHA256, 1616),
        "LICENSE": (GBMICROTEST_LICENSE_BLOB, GBMICROTEST_LICENSE_SHA256, 1065),
    }
    content: dict[str, bytes] = {}
    for path, (expected_blob, expected_hash, expected_size) in specs.items():
        item = review / path
        if item.is_symlink() or not item.is_file():
            raise AdmissionRefused(f"gbmicrotest-review-member-unavailable:{path}")
        data = item.read_bytes()
        if (len(data) != expected_size or sha256(data) != expected_hash
                or _git_blob_sha1(data) != expected_blob):
            raise AdmissionRefused(f"gbmicrotest-review-member-identity-mismatch:{path}")
        content[path] = data
    original_path = review / "bin/div_inc_timing_a.gb"
    derivative_path = review / "derived/div_inc_timing_a.bootless.gb"
    if original_path.is_symlink() or derivative_path.is_symlink():
        raise AdmissionRefused("gbmicrotest-review-rom-symlink-refused")
    original = original_path.read_bytes()
    derivative = build_bootless_derivative(original)
    if not derivative_path.is_file() or derivative_path.read_bytes() != derivative:
        raise AdmissionRefused("gbmicrotest-local-derivative-differs-from-transform")

    identity = {
        "schema": "gabbaboy-gbmicrotest-one-case-identity-v1",
        "source": {"repository": "https://github.com/aappleby/gbmicrotest", "commit": GBMICROTEST_COMMIT,
                   "tree": GBMICROTEST_TREE},
        "case": {"name": GBMICROTEST_SELECTED_CASE, "source_blob_sha1": GBMICROTEST_SELECTED_SOURCE_BLOB,
                 "source_sha256": GBMICROTEST_SELECTED_SOURCE_SHA256,
                 "original_rom_blob_sha1": GBMICROTEST_SELECTED_ROM_BLOB,
                 "original_rom_sha256": GBMICROTEST_SELECTED_ROM_SHA256, "original_rom_size_bytes": len(original)},
        "output": {"kind": "bootless header derivative", "sha256": sha256(derivative),
                   "size_bytes": len(derivative), "original_rom_in_bundle": False,
                   "nintendo_logo_bytes_in_bundle": False},
        "transform": {"zero_bytes_inclusive": ["0x0104", "0x0133"],
                      "recompute_global_checksum_inclusive": ["0x014E", "0x014F"],
                      "allowed_changed_ranges": ["0x0104-0x0133", "0x014E-0x014F"],
                      "changed_offset_count": 44, "header_checksum_0x014D_preserved": True,
                      "header_checksum_valid": True, "global_checksum": "0x16F8",
                      "global_checksum_valid": True},
        "model_scope": "DMG-CPU-B software diagnostic only; no hardware, DMG-CPU-08, or CGB claim",
        "output_rights_interpretation": {
            "status": "bounded-inference-for-this-modified-copy-only",
            "basis": ["pinned root MIT grant applies to Software without a source-only restriction",
                      "OSI OSD permits compiled-form distribution and derived works",
                      "complete pinned MIT notice is included"],
            "limit": "The upstream README does not explicitly state a binary-output license. This interpretation covers only this source-bound bootless derivative; it excludes the original ROM, removed logo, other 512 ROMs, and other sources, and is not legal certainty.",
            "references": ["https://opensource.org/license/mit", "https://opensource.org/osd"]},
    }
    identity_bytes = (json.dumps(identity, indent=2, sort_keys=True) + "\n").encode("utf-8")
    archive_bytes = _deterministic_tar({
        "LICENSE": content["LICENSE"], "README.md": content["README.md"], "identity.json": identity_bytes,
        "tests/div_inc_timing_a.s": content["tests/div_inc_timing_a.s"],
        "tests/header.inc": content["tests/header.inc"], "tests/macros.inc": content["tests/macros.inc"],
        "bin/div_inc_timing_a.bootless.gb": derivative,
    })
    source_doc = (
        "# gbmicrotest div_inc_timing_a source and output\n\n"
        f"Pinned source: https://github.com/aappleby/gbmicrotest/tree/{GBMICROTEST_COMMIT} "
        f"(tree {GBMICROTEST_TREE}).\n\n"
        f"The only runtime payload is the bootless derivative SHA-256 {sha256(derivative)}.\n\n"
        "The case declares pass - dmg, resets DIV, executes 60 NOPs, and requires DIV=0. "
        "This supports DMG-CPU-B software diagnostic scope only.\n\n"
        "The complete pinned root MIT notice is included. The pinned README lists prebuilt ROMs in bin/ "
        "but does not explicitly state binary-output terms. Applying the MIT Software grant and OSI "
        "compiled-form/derived-work language to this single modified copy is a bounded interpretation, "
        "not an upstream explicit ROM-output statement or legal certainty. It excludes the original ROM, "
        "removed Nintendo logo bytes, the other 512 ROMs, and other sources.\n\n"
        "The original ROM and all Nintendo logo bytes are excluded. No WLA-DX build or hardware claim is made.\n"
    ).encode("utf-8")
    files_data = {"cohort.tar": archive_bytes, "LICENSE.txt": content["LICENSE"],
                  "SOURCES.md": source_doc, "identity.json": identity_bytes}
    fixture_files = {str(GBMICROTEST_FIXTURE_DIR / name): data for name, data in files_data.items()}
    for name, data in files_data.items():
        (fixture / name).write_bytes(data)
    file_records = [{"path": path, "size_bytes": len(data), "sha256": sha256(data)}
                    for path, data in sorted(fixture_files.items())]
    file_index = {item["path"]: item for item in file_records}
    license_path = str(GBMICROTEST_FIXTURE_DIR / "LICENSE.txt")
    code_paths = [str(GBMICROTEST_FIXTURE_DIR / name) for name in ("cohort.tar", "SOURCES.md", "identity.json")]
    tool_revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
                                   check=True, timeout=5).stdout.decode("ascii").strip()
    manifest = {
        "schema_version": 1, "fixture_kind": "gbmicrotest-bootless-diagnostic",
        "decision": {"status": "approved", "reviewer_role": "project-maintainer",
                     "rationale": "One source-selected DMG-CPU-B software diagnostic with a logo-free output and a narrowly bounded MIT compiled-copy interpretation.",
                     "component_rationale": {"code": "Only the pinned case source and one bootless derivative are included.",
                                             "notices": "The complete pinned upstream MIT notice accompanies the derivative."}},
        "permissions": {"repository": True, "public_ci": True},
        "source": {"repository": "https://github.com/aappleby/gbmicrotest", "revision": GBMICROTEST_COMMIT},
        "inputs": [file_index[str(GBMICROTEST_FIXTURE_DIR / "cohort.tar")]], "files": file_records,
        "build": {"recipe": "No upstream WLA-DX build is claimed. The supplied ROM was transformed only by zeroing 0x0104-0x0133 and recomputing 0x014E-0x014F; exact output identity and changed-offset proof are in identity.json.",
                  "tools": [{"name": "verify-diagnostic-admission.py bootless-header-transform", "version": "1",
                             "terms": "GabbaBoy MIT", "source_repository": "https://github.com/szTheory/gabbaboy",
                             "revision": tool_revision, "disposition": "build_only", "component": None,
                             "covered_paths": []}]},
        "components": {
            "code": {"presence": "present", "terms": "MIT; bounded interpretation for this one modified copy only",
                     "evidence": {"path": license_path, "sha256": file_index[license_path]["sha256"]},
                     "covered_paths": code_paths, "scope": {"repository": True, "public_ci": True}},
            "art": {"presence": "absent", "reason": "Nintendo logo bytes are removed; no reference art is included."},
            "audio_driver": {"presence": "absent", "reason": "The selected DIV diagnostic has no audio driver."},
            "build_inputs": {"presence": "absent", "reason": "No unpinned WLA-DX build closure or reproducible build is claimed."},
            "notices": {"presence": "present", "terms": "MIT",
                         "evidence": {"path": license_path, "sha256": file_index[license_path]["sha256"]},
                         "covered_paths": [license_path], "scope": {"repository": True, "public_ci": True}},
        },
        "notices": {"local_path": license_path, "sha256": file_index[license_path]["sha256"],
                    "index_path": "THIRD_PARTY_NOTICES.md"},
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    (fixture / "manifest.json").write_bytes(manifest_bytes)
    notice_index = root / "THIRD_PARTY_NOTICES.md"
    current = notice_index.read_text(encoding="utf-8")
    if "| `gbmicrotest` |" in current:
        raise AdmissionRefused("gbmicrotest-notice-row-already-exists")
    marker = "| Fixture directory | `manifest.json` SHA-256 | `LICENSE.txt` SHA-256 |\n|---|---|---|\n"
    if marker not in current:
        raise AdmissionRefused("gbmicrotest-notice-table-shape-invalid")
    row = f"| `gbmicrotest` | `{sha256(manifest_bytes)}` | `{sha256(content['LICENSE'])}` |\n"
    notice_index.write_text(current.replace(marker, marker + row, 1), encoding="utf-8")
    print(f"prepared gbmicrotest one-case bundle derivative_sha256={sha256(derivative)} tar_sha256={sha256(archive_bytes)}")


def validate_identity_bundle(expected: dict[str, str], candidate: dict[str, str]) -> None:
    """Compare receipt identities to independently computed inputs and fixed controls."""
    if not isinstance(expected, dict) or not isinstance(candidate, dict):
        raise AdmissionRefused("identity-bundle-invalid")
    if set(expected) != set(IDENTITY_FIELDS) or set(candidate) != set(IDENTITY_FIELDS):
        raise AdmissionRefused("identity-field-set-invalid")
    for name in IDENTITY_FIELDS:
        expected_digest, candidate_digest = expected[name], candidate[name]
        if (not isinstance(expected_digest, str) or not HEX64.fullmatch(expected_digest)
                or not isinstance(candidate_digest, str) or not HEX64.fullmatch(candidate_digest)):
            raise AdmissionRefused(f"identity-invalid:{name}")
        if candidate_digest != expected_digest:
            raise AdmissionRefused(f"identity-mismatch:{name}")


def composition_identity_bundle(source: bytes, rom: bytes, reference: bytes,
                                cells: list[tuple[int, int]], mask: bytes, overlay: bytes) -> dict[str, str]:
    if tuple(cells) != SOURCE_CELL_ALLOWLIST:
        raise AdmissionRefused("source-cell-allowlist-mismatch")
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")
    layout = canonical({"width": 160, "height": 144, "cell_size": 8,
                        "cells": [[column, row] for column, row in cells]})
    allowlist = canonical([[column, row] for column, row in SOURCE_CELL_ALLOWLIST])
    return {
        "rom": sha256(rom),
        "reference": sha256(reference),
        "source": sha256(source),
        "layout": sha256(layout),
        "glyph": sha256(CONTROL_GLYPH_BYTES),
        "allowlist": sha256(allowlist),
        "mask": sha256(mask),
        "overlay": sha256(overlay),
    }


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_limited(path: pathlib.Path, limit: int, label: str) -> bytes:
    try:
        with path.open("rb") as handle:
            data = handle.read(limit + 1)
    except OSError:
        raise AdmissionRefused(f"{label}-unreadable") from None
    if len(data) > limit:
        raise AdmissionRefused(f"{label}-size-limit")
    return data


def _load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module-unavailable: {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bounded_run(argv: list[str], *, cwd: pathlib.Path, timeout: int = 30) -> tuple[int, bytes, bytes]:
    try:
        result = subprocess.run(argv, cwd=cwd, capture_output=True, check=False, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError("subprocess-timeout") from None
    except OSError as error:
        raise RuntimeError(f"subprocess-start-failed:{error.__class__.__name__}") from None
    if len(result.stdout) > MAX_PROCESS_OUTPUT or len(result.stderr) > MAX_PROCESS_OUTPUT:
        raise RuntimeError("subprocess-output-limit")
    return result.returncode, result.stdout, result.stderr


def _git(root: pathlib.Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    try:
        result = subprocess.run(["git", *args], cwd=root, input=input_bytes, capture_output=True,
                                check=False, timeout=30)
    except subprocess.TimeoutExpired:
        raise RuntimeError("git-timeout") from None
    except OSError as error:
        raise RuntimeError(f"git-start-failed:{error.__class__.__name__}") from None
    if len(result.stdout) > MAX_JSON_BYTES or len(result.stderr) > MAX_PROCESS_OUTPUT:
        raise RuntimeError("git-output-limit")
    if result.returncode:
        detail = result.stderr.decode("utf-8", "replace")[-500:]
        raise RuntimeError(f"git-failed:{args[0]}:{detail.strip()}")
    return result.stdout


def repository_relative_path(root: pathlib.Path, path: pathlib.Path) -> str:
    root = root.resolve(strict=True)
    path = pathlib.Path(path)
    if path.is_symlink():
        raise AdmissionRefused("scope-resolution-required: source path is a symlink")
    try:
        resolved = path.resolve(strict=True)
        relative = resolved.relative_to(root).as_posix()
    except (OSError, ValueError):
        raise AdmissionRefused("scope-resolution-required: source path is outside or absent") from None
    if (not relative or relative.startswith("/") or "\\" in relative
            or any(part in ("", ".", "..") or not re.fullmatch(r"[A-Za-z0-9._+-]+", part)
                   for part in relative.split("/"))):
        raise AdmissionRefused("scope-resolution-required: source path is invalid")
    return relative


def read_source_file(repo_root: pathlib.Path, source_revision: str, relative: str) -> bytes:
    """Read a regular file from one immutable source commit, never from the worktree."""
    if not HEX40.fullmatch(source_revision):
        raise AdmissionRefused("source-revision-invalid")
    if (not relative or relative.startswith("/") or "\\" in relative
            or any(part in ("", ".", "..") or not re.fullmatch(r"[A-Za-z0-9._+-]+", part)
                   for part in relative.split("/"))):
        raise AdmissionRefused("scope-resolution-required: source path is invalid")
    repo_root = repo_root.resolve(strict=True)
    try:
        tree_rows = [row for row in _git(repo_root, "ls-tree", "-z", source_revision, "--", relative).split(b"\0")
                     if row]
        if len(tree_rows) != 1:
            raise AdmissionRefused(f"scope-resolution-required: source file absent: {relative}")
        metadata, returned_path = tree_rows[0].split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split()
        if returned_path.decode("utf-8", "strict") != relative or kind != "blob" or mode not in ("100644", "100755"):
            raise AdmissionRefused(f"scope-resolution-required: source file is not regular: {relative}")
        raw = _git(repo_root, "cat-file", "blob", oid)
    except (RuntimeError, UnicodeError, ValueError) as error:
        if isinstance(error, AdmissionRefused):
            raise
        raise AdmissionRefused(f"scope-resolution-required: immutable source unavailable: {relative}") from None
    limit = MAX_INVENTORY_BYTES if relative.endswith("gbmicrotest-inventory.json") else MAX_JSON_BYTES
    if len(raw) > limit:
        raise AdmissionRefused(f"scope-resolution-required: source file size limit: {relative}")
    return raw


def require_worktree_source_file(repo_root: pathlib.Path, source_revision: str,
                                 relative: str, path: pathlib.Path) -> None:
    """Refuse execution when a policy/manifest file differs from its committed bytes."""
    expected = read_source_file(repo_root, source_revision, relative)
    try:
        if path.is_symlink() or not path.is_file() or read_limited(path, len(expected), relative) != expected:
            raise AdmissionRefused(f"scope-resolution-required: source file differs from commit: {relative}")
    except AdmissionRefused:
        raise


def _json_without_duplicates(raw: bytes, label: str) -> dict[str, Any]:
    def object_pairs(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise AdmissionRefused(f"{label}-duplicate-key:{key}")
            value[key] = item
        return value

    def reject_constant(value: str):
        raise AdmissionRefused(f"{label}-invalid-constant:{value}")

    try:
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=object_pairs,
                           parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        raise AdmissionRefused(f"{label}-invalid") from None
    if not isinstance(value, dict):
        raise AdmissionRefused(f"{label}-invalid")
    return value


def _read_json_record(root: pathlib.Path, relative: str, limit: int, label: str) -> dict[str, Any]:
    path = root / relative
    if path.is_symlink() or not path.is_file():
        raise AdmissionRefused(f"{label}-missing-or-unsafe")
    return _json_without_duplicates(read_limited(path, limit, label), label)


def _inventory_projection(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "name": case["name"],
        "source_path": case["source"]["path"],
        "source_size_bytes": case["source"]["size_bytes"],
        "source_git_blob_sha1": case["source"]["git_blob_sha1"],
        "rom_path": case["prebuilt_rom"]["path"],
        "rom_size_bytes": case["prebuilt_rom"]["size_bytes"],
        "rom_git_blob_sha1": case["prebuilt_rom"]["git_blob_sha1"],
        "protocol_kind": case["protocol"]["kind"],
    } for case in cases]


def _ordered_names(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(name, str) for name in value):
        raise AdmissionRefused(f"{label}-invalid")
    if value != sorted(set(value), key=lambda name: name.encode("utf-8")):
        raise AdmissionRefused(f"{label}-not-unique-bytewise-sorted")
    return value


def validate_gbmicrotest_inventory(root: pathlib.Path) -> dict[str, Any]:
    record = _read_json_record(root, "tests/external/gbmicrotest-inventory.json",
                               MAX_INVENTORY_BYTES, "diagnostic-inventory")
    if record.get("schema") != "gabbaboy-gbmicrotest-inventory-v1":
        raise AdmissionRefused("diagnostic-inventory-schema-invalid")
    upstream = record.get("upstream")
    if (not isinstance(upstream, dict) or upstream.get("repository") != "https://github.com/aappleby/gbmicrotest"
            or upstream.get("commit") != GBMICROTEST_COMMIT
            or upstream.get("root_tree_sha1") != GBMICROTEST_TREE
            or upstream.get("tree_entry_count") != 1034
            or upstream.get("tree_truncated") is not False):
        raise AdmissionRefused("diagnostic-inventory-source-pin-mismatch")
    cases = record.get("cases")
    if not isinstance(cases, list) or len(cases) != GBMICROTEST_CASE_COUNT:
        raise AdmissionRefused("diagnostic-inventory-case-count-mismatch")
    names: list[str] = []
    protocol_counts = {kind: 0 for kind in GBMICROTEST_PROTOCOL_COUNTS}
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("name"), str):
            raise AdmissionRefused("diagnostic-inventory-case-invalid")
        name = case["name"]
        if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
            raise AdmissionRefused("diagnostic-inventory-case-name-invalid")
        names.append(name)
        source, rom, protocol = case.get("source"), case.get("prebuilt_rom"), case.get("protocol")
        if not all(isinstance(item, dict) for item in (source, rom, protocol)):
            raise AdmissionRefused(f"diagnostic-inventory-case-identity-invalid:{name}")
        if (source.get("path") != f"tests/{name}.s" or rom.get("path") != f"bin/{name}.gb"
                or not isinstance(source.get("size_bytes"), int) or source["size_bytes"] <= 0
                or not isinstance(rom.get("size_bytes"), int) or not 0 < rom["size_bytes"] <= 32 * 1024 * 1024
                or not HEX40.fullmatch(str(source.get("git_blob_sha1", "")))
                or not HEX40.fullmatch(str(rom.get("git_blob_sha1", "")))):
            raise AdmissionRefused(f"diagnostic-inventory-case-identity-invalid:{name}")
        for identity, label in ((source, "source"), (rom, "rom")):
            digest, digest_status = identity.get("sha256"), identity.get("sha256_status")
            if digest is None:
                if not isinstance(digest_status, str) or not digest_status.startswith("not-computed;"):
                    raise AdmissionRefused(f"diagnostic-inventory-digest-status-invalid:{name}:{label}")
            elif not HEX64.fullmatch(str(digest)) or digest_status != "verified-against-pinned-git-blob":
                raise AdmissionRefused(f"diagnostic-inventory-digest-invalid:{name}:{label}")
        protocol_kind = protocol.get("kind")
        if protocol_kind not in protocol_counts:
            raise AdmissionRefused(f"diagnostic-inventory-protocol-invalid:{name}")
        expected_kind = ("no-verdict-protocol" if name in GBMICROTEST_INITIAL_EXCLUSIONS else
                         "inline-ff80-ff82" if name in GBMICROTEST_INLINE_CASES else
                         "shared-verdict-macros")
        if protocol_kind != expected_kind:
            raise AdmissionRefused(f"diagnostic-inventory-protocol-mismatch:{name}")
        protocol_evidence = protocol.get("evidence")
        expected_evidence_path = "tests/macros.inc" if protocol_kind == "shared-verdict-macros" else f"tests/{name}.s"
        if (not isinstance(protocol_evidence, dict)
                or protocol_evidence.get("repository") != "https://github.com/aappleby/gbmicrotest"
                or protocol_evidence.get("commit") != GBMICROTEST_COMMIT
                or protocol_evidence.get("path") != expected_evidence_path
                or not isinstance(protocol_evidence.get("basis"), str)
                or not protocol_evidence["basis"].strip()
                or not isinstance(protocol.get("detail"), str) or not protocol["detail"].strip()):
            raise AdmissionRefused(f"diagnostic-inventory-protocol-evidence-invalid:{name}")
        protocol_counts[protocol_kind] += 1
        applicability = case.get("model_applicability")
        if (not isinstance(applicability, dict) or applicability.get("status") != "unresolved"
                or applicability.get("suite_claim") != "DMG-CPU-08 (uncertain, suite-wide only)"
                or applicability.get("per_case_evidence") is not None):
            raise AdmissionRefused(f"diagnostic-inventory-applicability-mutated:{name}")
    if names != sorted(set(names), key=lambda name: name.encode("utf-8")):
        raise AdmissionRefused("diagnostic-inventory-roster-not-unique-bytewise-sorted")
    if protocol_counts != GBMICROTEST_PROTOCOL_COUNTS:
        raise AdmissionRefused("diagnostic-inventory-protocol-count-mismatch")
    canonical = json.dumps(_inventory_projection(cases), sort_keys=True, separators=(",", ":")).encode("ascii")
    if sha256(canonical) != GBMICROTEST_ROSTER_PROJECTION_SHA256:
        raise AdmissionRefused("diagnostic-inventory-projection-pin-mismatch")
    counts = record.get("counts")
    expected_counts = {"named_cases": 513, "shared_macro_verdict": 480, "inline_verdict": 2,
                       "initial_no_protocol_exclusions": 31, "protocol_candidates": 482}
    if counts != expected_counts:
        raise AdmissionRefused("diagnostic-inventory-summary-counts-mismatch")
    accounting = record.get("accounting")
    if not isinstance(accounting, dict):
        raise AdmissionRefused("diagnostic-inventory-accounting-invalid")
    candidate_names = [name for name in names if name not in GBMICROTEST_INITIAL_EXCLUSIONS]
    exclusions = [name for name in names if name in GBMICROTEST_INITIAL_EXCLUSIONS]
    if (_ordered_names(accounting.get("protocol_candidate_names"), "protocol-candidates") != candidate_names
            or _ordered_names(accounting.get("admitted_eligible_names"), "admitted-eligible") != []
            or _ordered_names(accounting.get("executed_names"), "executed") != []
            or _ordered_names(accounting.get("excluded_names"), "excluded") != exclusions
            or _ordered_names(accounting.get("blocked_not_observed_names"), "blocked-not-observed") != candidate_names
            or accounting.get("final_suite_accounting_complete") is not False
            or accounting.get("status") != "blocked-before-real-byte-use"):
        raise AdmissionRefused("diagnostic-inventory-eligibility-accounting-mismatch")
    interpretation = accounting.get("interpretation")
    if (not isinstance(interpretation, str)
            or any(phrase not in interpretation.casefold() for phrase in (
                "eligibility is a predicate", "executed and excluded are disjoint terminal outcomes",
                "every eligible case must execute", "blocked and not observed"))):
        raise AdmissionRefused("diagnostic-inventory-accounting-interpretation-invalid")
    return record


def validate_assessment(root: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any]]:
    record = _read_json_record(root, "tests/external/diagnostic-assessment.json",
                               MAX_JSON_BYTES, "diagnostic-assessment")
    if record.get("origin") in ("synthetic", "test-only") or str(record.get("fixture_kind", "")).startswith("synthetic"):
        raise AdmissionRefused("synthetic-only-record-refused")
    if (record.get("schema") != "gabbaboy-diagnostic-assessment-v1"
            or record.get("origin") != "pinned-upstream-evidence"
            or not isinstance(record.get("source_revision"), str)
            or not HEX40.fullmatch(record["source_revision"])):
        raise AdmissionRefused("diagnostic-assessment-schema-invalid")
    gates = record.get("required_gates")
    if not isinstance(gates, list):
        raise AdmissionRefused("diagnostic-assessment-gates-invalid")
    by_gate = {gate.get("id"): gate for gate in gates if isinstance(gate, dict)}
    if len(by_gate) != len(gates) or tuple(by_gate) != REQUIRED_GATE_IDS:
        raise AdmissionRefused("diagnostic-assessment-gate-set-invalid")
    for gate_id in REQUIRED_GATE_IDS:
        gate = by_gate[gate_id]
        if gate.get("status") not in ("supported", "unresolved"):
            raise AdmissionRefused(f"diagnostic-assessment-gate-status-invalid:{gate_id}")
        evidence = gate.get("evidence")
        if (not isinstance(evidence, list) or not evidence
                or any(not isinstance(item, str) or not item for item in evidence)):
            raise AdmissionRefused(f"diagnostic-assessment-gate-evidence-invalid:{gate_id}")
        if gate["status"] == "unresolved" and (not isinstance(gate.get("blocker"), str) or not gate["blocker"].strip()):
            raise AdmissionRefused(f"diagnostic-assessment-blocker-missing:{gate_id}")
        if gate["status"] == "supported" and gate.get("blocker") is not None:
            raise AdmissionRefused(f"diagnostic-assessment-supported-gate-has-blocker:{gate_id}")
        if gate["status"] == "supported" and not any(item.startswith(("https://github.com/", "https://api.github.com/"))
                                                        for item in evidence):
            raise AdmissionRefused(f"diagnostic-assessment-supported-gate-not-source-backed:{gate_id}")
    components = record.get("components")
    if not isinstance(components, list):
        raise AdmissionRefused("diagnostic-assessment-components-invalid")
    by_component = {item.get("id"): item for item in components if isinstance(item, dict)}
    if len(by_component) != len(components) or tuple(by_component) != REQUIRED_COMPONENT_IDS:
        raise AdmissionRefused("diagnostic-assessment-component-set-invalid")
    for component_id in REQUIRED_COMPONENT_IDS:
        component = by_component[component_id]
        status = component.get("status")
        if status not in ("supported", "unresolved", "excluded-by-design", "not-created"):
            raise AdmissionRefused(f"diagnostic-assessment-component-status-invalid:{component_id}")
        if status == "supported":
            scope = component.get("scope")
            evidence = component.get("evidence")
            if (not isinstance(scope, dict) or scope.get("repository") is not True
                    or scope.get("public_ci") is not True or not isinstance(evidence, list) or not evidence
                    or any(not isinstance(item, str) or not item for item in evidence)):
                raise AdmissionRefused(f"diagnostic-assessment-positive-scope-incomplete:{component_id}")
            if component.get("blocker") is not None:
                raise AdmissionRefused(f"diagnostic-assessment-supported-component-has-blocker:{component_id}")
            if not any(item.startswith(("https://github.com/", "https://api.github.com/")) for item in evidence):
                raise AdmissionRefused(f"diagnostic-assessment-supported-component-not-source-backed:{component_id}")
        elif status == "unresolved" and (not isinstance(component.get("blocker"), str)
                                           or not component["blocker"].strip()):
            raise AdmissionRefused(f"diagnostic-assessment-component-blocker-missing:{component_id}")
    inventory = validate_gbmicrotest_inventory(root)
    applicability = record.get("model_applicability")
    if not isinstance(applicability, dict) or not isinstance(applicability.get("gbmicrotest"), dict):
        raise AdmissionRefused("diagnostic-assessment-model-applicability-invalid")
    case_applicability = applicability["gbmicrotest"]
    case_gate = next(gate for gate in gates if gate["id"] == "gbmicrotest_case_applicability")
    if case_gate["status"] == "supported":
        per_case = case_applicability.get("per_case_source_evidence")
        if (not isinstance(per_case, list) or len(per_case) != GBMICROTEST_CASE_COUNT
                or any(not isinstance(item, dict) or not isinstance(item.get("case"), str)
                       or not isinstance(item.get("source"), str) or not item["source"].startswith("https://github.com/")
                       for item in per_case)):
            raise AdmissionRefused("diagnostic-assessment-case-applicability-evidence-incomplete")
    unresolved = any(gate["status"] != "supported" for gate in gates)
    unresolved = unresolved or any(item["status"] == "unresolved" for item in components)
    expected_status = "blocked" if unresolved else "approved"
    if record.get("status") != expected_status:
        raise AdmissionRefused("diagnostic-assessment-status-gate-mismatch")
    return record, inventory


def _diagnostic_source_by_id(record: dict[str, Any], source_id: str) -> dict[str, Any]:
    sources = record.get("sources")
    if not isinstance(sources, list):
        raise AdmissionRefused("diagnostic-rights-sources-invalid")
    matches = [source for source in sources if isinstance(source, dict) and source.get("id") == source_id]
    if len(matches) != 1:
        raise AdmissionRefused(f"diagnostic-rights-source-missing-or-duplicate:{source_id}")
    return matches[0]


def _diagnostic_component(source: dict[str, Any], component_id: str) -> dict[str, Any]:
    components = source.get("components")
    if not isinstance(components, list):
        raise AdmissionRefused("diagnostic-rights-components-invalid")
    matches = [item for item in components if isinstance(item, dict) and item.get("id") == component_id]
    if len(matches) != 1:
        raise AdmissionRefused(f"diagnostic-rights-component-missing-or-duplicate:{component_id}")
    return matches[0]


def _git_revision_is_ancestor(root: pathlib.Path, ancestor: str, descendant: str) -> bool:
    if not HEX40.fullmatch(ancestor) or not HEX40.fullmatch(descendant):
        return False
    try:
        result = subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, descendant],
                                cwd=root, capture_output=True, check=False, timeout=10)
    except (OSError, subprocess.SubprocessError):
        raise AdmissionRefused("diagnostic-runtime-revision-ancestry-unavailable") from None
    if result.returncode not in (0, 1):
        raise AdmissionRefused("diagnostic-runtime-revision-ancestry-check-failed")
    return result.returncode == 0


def _validate_gbmicrotest_runtime_result(results: object, *, root: pathlib.Path | None = None,
                                         expected_source_revision: str | None = None,
                                         require_evidence: bool = False) -> dict[str, Any]:
    if not isinstance(results, list) or len(results) != 1 or not isinstance(results[0], dict):
        raise AdmissionRefused("diagnostic-closeout-gbmicrotest-runtime-result-invalid")
    result = results[0]
    required = {
        "case", "runner_case_id", "source_revision", "closeout_record_sha256",
        "fixture_admission_commit", "manifest_sha256",
        "source_sha256", "original_rom_sha256", "derivative_sha256", "model", "verdict", "actual",
        "expected", "terminal", "instruction_count", "event_count", "end_half_dots", "elapsed_seconds",
        "runner_exit_code", "reason", "runner_sha256", "qualification_sha256", "evidence_path", "evidence_sha256",
    }
    if set(result) != required:
        raise AdmissionRefused("diagnostic-closeout-gbmicrotest-runtime-result-fields-invalid")
    for field in ("closeout_record_sha256", "manifest_sha256", "source_sha256", "original_rom_sha256", "derivative_sha256",
                  "runner_sha256", "qualification_sha256", "evidence_sha256"):
        if not isinstance(result[field], str) or not HEX64.fullmatch(result[field]):
            raise AdmissionRefused(f"diagnostic-closeout-gbmicrotest-runtime-digest-invalid:{field}")
    for field in ("source_revision", "fixture_admission_commit"):
        if not isinstance(result[field], str) or not HEX40.fullmatch(result[field]):
            raise AdmissionRefused(f"diagnostic-closeout-gbmicrotest-runtime-revision-invalid:{field}")
    if (result["case"] != GBMICROTEST_SELECTED_CASE or result["runner_case_id"] != "div-inc-a"
            or result["fixture_admission_commit"] != GBMICROTEST_ADMISSION_COMMIT
            or result["manifest_sha256"] != GBMICROTEST_MANIFEST_SHA256
            or result["source_sha256"] != GBMICROTEST_SELECTED_SOURCE_SHA256
            or result["original_rom_sha256"] != GBMICROTEST_SELECTED_ROM_SHA256
            or result["derivative_sha256"] != GBMICROTEST_SELECTED_DERIVATIVE_SHA256
            or result["model"] != "dmg-cpu-b"
            or not isinstance(result["instruction_count"], int) or isinstance(result["instruction_count"], bool)
            or not 0 <= result["instruction_count"] <= 512
            or not isinstance(result["event_count"], int) or isinstance(result["event_count"], bool)
            or not 0 <= result["event_count"] <= 4096
            or not isinstance(result["end_half_dots"], int) or isinstance(result["end_half_dots"], bool)
            or not 0 <= result["end_half_dots"] <= 8192
            or not isinstance(result["elapsed_seconds"], (int, float))
            or isinstance(result["elapsed_seconds"], bool) or not math.isfinite(result["elapsed_seconds"])
            or not 0 < result["elapsed_seconds"] <= 25
            or result["evidence_path"] not in (
                "build/phase24/diagnostic-runtime-preflight.json",
                GBMICROTEST_RUNTIME_PREFLIGHT_PATH, GBMICROTEST_RUNTIME_FINAL_PATH)):
        raise AdmissionRefused("diagnostic-closeout-gbmicrotest-runtime-result-mismatch")
    if result["verdict"] == "pass":
        if (not isinstance(result["runner_exit_code"], int) or isinstance(result["runner_exit_code"], bool)
                or result["runner_exit_code"] != 0 or result["reason"] is not None
                or result["actual"] != "00" or result["expected"] != "00" or result["terminal"] != "01"
                or result["instruction_count"] == 0 or result["event_count"] == 0 or result["end_half_dots"] == 0):
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-runtime-pass-invalid")
    elif result["verdict"] == "source-failure":
        if (not isinstance(result["runner_exit_code"], int) or isinstance(result["runner_exit_code"], bool)
                or result["runner_exit_code"] != 1
                or result["reason"] not in ("observed-mismatch", "source-protocol", "source-verdict-inconsistent")
                or not all(isinstance(result[key], str) and re.fullmatch(r"[0-9a-f]{2}", result[key])
                           for key in ("actual", "expected", "terminal"))
                or result["instruction_count"] == 0 or result["event_count"] == 0
                or result["end_half_dots"] == 0):
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-runtime-mismatch-invalid")
    elif result["verdict"] == "bounded-failure":
        if (not isinstance(result["runner_exit_code"], int) or isinstance(result["runner_exit_code"], bool)
                or result["runner_exit_code"] != 3
                or result["reason"] not in ("iteration-guard", "guest-stopped", "no-progress",
                                             "instruction-limit", "event-limit", "guest-deadline")
                or result["actual"] is not None
                or result["expected"] is not None or result["terminal"] is not None):
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-runtime-bounded-failure-invalid")
    else:
        raise AdmissionRefused("diagnostic-closeout-gbmicrotest-runtime-verdict-invalid")
    if (expected_source_revision is not None and result["source_revision"] != expected_source_revision
            and (root is None or not _git_revision_is_ancestor(root, result["source_revision"],
                                                                expected_source_revision))):
        raise AdmissionRefused("diagnostic-closeout-gbmicrotest-runtime-source-revision-mismatch")
    if root is not None:
        if expected_source_revision is not None and not _git_revision_is_ancestor(
                root, result["source_revision"], expected_source_revision):
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-runtime-source-not-ancestor")
        source_record_raw = read_source_file(root, result["source_revision"], DIAGNOSTIC_CLOSEOUT_PATH)
        if sha256(source_record_raw) != result["closeout_record_sha256"]:
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-runtime-closeout-source-mismatch")
        evidence_path = root / result["evidence_path"]
        if evidence_path.is_symlink():
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-runtime-evidence-unsafe")
        if evidence_path.exists():
            evidence_raw = read_limited(evidence_path, MAX_JSON_BYTES, "gbmicrotest-runtime-evidence")
            if sha256(evidence_raw) != result["evidence_sha256"]:
                raise AdmissionRefused("diagnostic-closeout-gbmicrotest-runtime-evidence-digest-mismatch")
            evidence = _json_without_duplicates(evidence_raw, "gbmicrotest-runtime-evidence")
            for evidence_field, result_field in (
                    ("schema", None),
                    ("source_revision", "source_revision"),
                    ("closeout_record_sha256", "closeout_record_sha256"),
                    ("fixture_admission_commit", "fixture_admission_commit"),
                    ("manifest_sha256", "manifest_sha256"),
                    ("runner_sha256", "runner_sha256"),
                    ("qualification_sha256", "qualification_sha256"),
                    ("qualified_artifact_sha256", "runner_sha256"),
                    ("case", "case"), ("runner_case_id", "runner_case_id"),
                    ("model", "model"),
                    ("verdict", "verdict"), ("runner_exit_code", "runner_exit_code"),
                    ("reason", "reason"), ("actual", "actual"), ("expected", "expected"),
                    ("terminal", "terminal"), ("instruction_count", "instruction_count"),
                    ("event_count", "event_count"), ("end_half_dots", "end_half_dots"),
                    ("elapsed_seconds", "elapsed_seconds")):
                expected_evidence_value = (
                    "gabbaboy-gbmicrotest-runtime-evidence-v1" if result_field is None
                    else result[result_field])
                if evidence.get(evidence_field) != expected_evidence_value:
                    raise AdmissionRefused(f"diagnostic-closeout-gbmicrotest-runtime-evidence-binding-mismatch:{evidence_field}")
        elif require_evidence:
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-runtime-evidence-missing")
    return result


def _validate_acid2_runtime_result(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AdmissionRefused("diagnostic-closeout-acid2-runtime-result-invalid")
    if value.get("status") == "pending":
        expected_pending = {
            "status": "pending", "source_revision": None, "closeout_record_sha256": None,
            "fixture_admission_commit": ACID2_FIXTURE_ADMISSION_COMMIT,
            "manifest_sha256": ACID2_FIXTURE_MANIFEST_SHA256,
            "bundle_sha256": ACID2_FIXTURE_BUNDLE_SHA256, "runner_sha256": None,
            "qualification_sha256": None, "evidence_path": None, "evidence_sha256": None,
            "comparisons": [],
        }
        if value != expected_pending:
            raise AdmissionRefused("diagnostic-closeout-acid2-runtime-pending-mutated")
        return value

    expected_fields = {
        "status", "source_revision", "closeout_record_sha256", "fixture_admission_commit",
        "manifest_sha256", "bundle_sha256", "runner_sha256", "qualification_sha256",
        "evidence_path", "evidence_sha256", "comparisons",
    }
    if set(value) != expected_fields:
        raise AdmissionRefused("diagnostic-closeout-acid2-runtime-result-fields-invalid")
    for field in ("closeout_record_sha256", "manifest_sha256", "bundle_sha256", "runner_sha256",
                  "qualification_sha256", "evidence_sha256"):
        if not isinstance(value[field], str) or not HEX64.fullmatch(value[field]):
            raise AdmissionRefused(f"diagnostic-closeout-acid2-runtime-digest-invalid:{field}")
    if (not isinstance(value["source_revision"], str) or not HEX40.fullmatch(value["source_revision"])
            or value["fixture_admission_commit"] != ACID2_FIXTURE_ADMISSION_COMMIT
            or value["manifest_sha256"] != ACID2_FIXTURE_MANIFEST_SHA256
            or value["bundle_sha256"] != ACID2_FIXTURE_BUNDLE_SHA256
            or value["evidence_path"] not in (ACID2_RUNTIME_EVIDENCE_PATH,
                                               DIAGNOSTIC_RUNTIME_PREFLIGHT_PATH)):
        raise AdmissionRefused("diagnostic-closeout-acid2-runtime-result-identity-invalid")
    comparisons = value["comparisons"]
    if (not isinstance(comparisons, list) or len(comparisons) != len(ACID2_COMPARISON_PROFILES)
            or [row.get("profile") if isinstance(row, dict) else None for row in comparisons]
            != list(ACID2_COMPARISON_PROFILES)):
        raise AdmissionRefused("diagnostic-closeout-acid2-comparison-set-invalid")
    for row, profile in zip(comparisons, ACID2_COMPARISON_PROFILES, strict=True):
        expected = ACID2_PROFILE_EXPECTATIONS[profile]
        kind = expected["rom_kind"]
        derivative_path, derivative_sha, _derivative_model = ACID2_DERIVATIVES[kind]
        model = expected["runner_model"]
        rom = row.get("rom") if isinstance(row, dict) else None
        reference = row.get("reference") if isinstance(row, dict) else None
        mask = row.get("mask") if isinstance(row, dict) else None
        if (not isinstance(row, dict) or row.get("rom_kind") != kind
                or row.get("runner_model") != model or row.get("mode") != expected["mode"]
                or row.get("hardware_claim") is not False
                or row.get("verdict") not in ("pass", "mismatch")
                or not isinstance(row.get("differing_unmasked_pixels"), int)
                or isinstance(row.get("differing_unmasked_pixels"), bool)
                or not 0 <= row["differing_unmasked_pixels"] <= expected["compared_pixels"]
                or not isinstance(rom, dict) or rom.get("path") != derivative_path
                or rom.get("sha256") != derivative_sha or rom.get("size_bytes") != 32768
                or not isinstance(reference, dict)
                or reference.get("path") != expected["reference_path"]
                or reference.get("sha256") != expected["reference_sha256"]
                or reference.get("size_bytes") != expected["reference_size_bytes"]
                or not isinstance(mask, dict)
                or mask.get("path") != expected["mask_path"]
                or mask.get("sha256") != expected["mask_sha256"]
                or mask.get("masked_pixels") != expected["masked_pixels"]
                or mask.get("compared_pixels") != expected["compared_pixels"]
                or not isinstance(row.get("runner_sha256"), str)
                or not HEX64.fullmatch(row["runner_sha256"])
                or row["runner_sha256"] != value["runner_sha256"]
                or row.get("guest_budget_half_dots") != 4213440
                or not isinstance(row.get("elapsed_seconds"), (int, float))
                or isinstance(row.get("elapsed_seconds"), bool)
                or not math.isfinite(row["elapsed_seconds"])
                or not 0 < row["elapsed_seconds"] <= 25
                or not isinstance(row.get("detail"), str) or len(row["detail"]) > 1024):
            raise AdmissionRefused(f"diagnostic-closeout-acid2-comparison-mutated:{profile}")
        if (row["verdict"] == "pass") != (row["differing_unmasked_pixels"] == 0):
            raise AdmissionRefused(f"diagnostic-closeout-acid2-comparison-verdict-invalid:{profile}")
    expected_status = "pass" if all(row["verdict"] == "pass" for row in comparisons) else "mismatch"
    if value["status"] != expected_status:
        raise AdmissionRefused("diagnostic-closeout-acid2-runtime-status-invalid")
    return value


def _validate_acid2_runtime_evidence(root: pathlib.Path, runtime: dict[str, Any],
                                     current_source_revision: str) -> None:
    if runtime["status"] == "pending":
        return
    source_revision = runtime["source_revision"]
    if not _git_revision_is_ancestor(root, source_revision, current_source_revision):
        raise AdmissionRefused("diagnostic-closeout-acid2-runtime-source-not-ancestor")
    source_record = read_source_file(root, source_revision, DIAGNOSTIC_CLOSEOUT_PATH)
    if sha256(source_record) != runtime["closeout_record_sha256"]:
        raise AdmissionRefused("diagnostic-closeout-acid2-runtime-source-record-mismatch")
    path = root / runtime["evidence_path"]
    if path.is_symlink():
        raise AdmissionRefused("diagnostic-closeout-acid2-runtime-evidence-unsafe")
    if not path.exists():
        return
    raw = read_limited(path, MAX_JSON_BYTES, "acid2-runtime-evidence")
    if sha256(raw) != runtime["evidence_sha256"]:
        raise AdmissionRefused("diagnostic-closeout-acid2-runtime-evidence-digest-mismatch")
    evidence = _json_without_duplicates(raw, "acid2-runtime-evidence")
    if runtime["evidence_path"] == ACID2_RUNTIME_EVIDENCE_PATH:
        matches_runtime = (
            evidence.get("schema") == "gabbaboy-acid2-runtime-evidence-v1"
            and evidence.get("source_revision") == source_revision
            and evidence.get("closeout_record_sha256") == runtime["closeout_record_sha256"]
            and evidence.get("status") == runtime["status"]
            and evidence.get("comparisons") == runtime["comparisons"]
            and evidence.get("runner_sha256") == runtime["runner_sha256"]
            and evidence.get("qualification_sha256") == runtime["qualification_sha256"]
        )
    else:
        matches_runtime = (
            evidence.get("schema") == "gabbaboy-diagnostic-runtime-evidence-v1"
            and evidence.get("source_revision") == source_revision
            and evidence.get("closeout_record_sha256") == runtime["closeout_record_sha256"]
            and evidence.get("acid2", {}).get("status") == runtime["status"]
            and evidence.get("acid2", {}).get("comparisons") == runtime["comparisons"]
            and evidence.get("runner_sha256") == runtime["runner_sha256"]
            and evidence.get("qualification_sha256") == runtime["qualification_sha256"]
        )
    if not matches_runtime:
        raise AdmissionRefused("diagnostic-closeout-acid2-runtime-evidence-binding-mismatch")


def validate_diagnostic_closeout_record(record: dict[str, Any], rights_record: dict[str, Any],
                                         kind: str,
                                         inventory: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate current diagnostic outcomes without treating blockers as approval."""
    if kind not in ("acid2", "gbmicrotest", "all"):
        raise AdmissionRefused("diagnostic-closeout-kind-invalid")
    if (record.get("schema") != "gabbaboy-diagnostic-closeout-v1"
            or record.get("rights_input") != {
                "commit": DIAGNOSTIC_RIGHTS_REVISION,
                "path": CANDIDATE_CLOSEOUT_PATH,
                "size_bytes": DIAGNOSTIC_RIGHTS_SIZE,
                "sha256": DIAGNOSTIC_RIGHTS_SHA256,
            }):
        raise AdmissionRefused("diagnostic-closeout-input-identity-invalid")
    if rights_record.get("schema") != "gabbaboy-v04-closeout-v1":
        raise AdmissionRefused("diagnostic-closeout-rights-schema-invalid")

    blockers: list[str] = []
    if kind in ("acid2", "all"):
        acid2 = record.get("acid2")
        if not isinstance(acid2, dict) or acid2.get("status") not in (
                "admitted-before-runtime", "executed", "runtime-failed"):
            raise AdmissionRefused("diagnostic-closeout-acid2-outcome-invalid")
        if acid2.get("font_data") != "excluded-by-design":
            raise AdmissionRefused("diagnostic-closeout-acid2-font-scope-invalid")
        expected_fixture = {
            "manifest_path": ACID2_FIXTURE_MANIFEST,
            "manifest_sha256": ACID2_FIXTURE_MANIFEST_SHA256,
            "admission_commit": ACID2_FIXTURE_ADMISSION_COMMIT,
            "bundle_path": ACID2_FIXTURE_BUNDLE,
            "bundle_sha256": ACID2_FIXTURE_BUNDLE_SHA256,
            "bundle_size_bytes": ACID2_FIXTURE_BUNDLE_SIZE,
            "notice_path": ACID2_FIXTURE_NOTICE,
            "notice_sha256": ACID2_FIXTURE_NOTICE_SHA256,
            "rights_decision_commit": "169c062cd97764e2cea4052ce285209e8a886ff0",
            "rights_input_commit": DIAGNOSTIC_RIGHTS_REVISION,
        }
        if acid2.get("fixture") != expected_fixture:
            raise AdmissionRefused("diagnostic-closeout-acid2-fixture-record-invalid")
        cases = acid2.get("cases")
        expected_acid2 = (
            ("dmg-acid2-v1.0", "dc2295408f881637ff69f784d8d93f3d2db30181",
             "a59741f15579a82205fff557dd000a5ebb6d7f6e", "dmg", "dmg-cpu-b"),
            ("cgb-acid2-v1.1", "fa5b7f86d6fb599f79e55169494d981a7af75a31",
             "a541bf54356809dc04cc050f8fc14d9620649f88", "cgb", "cgb-cpu-e"),
        )
        if not isinstance(cases, list) or len(cases) != len(expected_acid2):
            raise AdmissionRefused("diagnostic-closeout-acid2-case-set-invalid")
        for item, (source_id, commit, tree, derivative_kind, model) in zip(cases, expected_acid2, strict=True):
            derivative_path, derivative_sha, _model = ACID2_DERIVATIVES[derivative_kind]
            if (not isinstance(item, dict) or item.get("id") != source_id
                    or item.get("commit") != commit or item.get("root_tree_sha1") != tree
                    or item.get("blocked_by") != []
                    or item.get("derivative") != {"status": "admitted", "member": derivative_path,
                                                   "sha256": derivative_sha, "size_bytes": 32768}
                    or item.get("admission") != {"status": "admitted", "commit": ACID2_FIXTURE_ADMISSION_COMMIT}
                    or item.get("model_scope") != {"runner_model": model, "hardware_claim": False}):
                raise AdmissionRefused(f"diagnostic-closeout-acid2-case-mutated:{source_id}")
            source = _diagnostic_source_by_id(rights_record, source_id)
            if source.get("commit") != commit or source.get("root_tree_sha1") != tree:
                raise AdmissionRefused(f"diagnostic-closeout-rights-pin-mismatch:{source_id}")
            image_component = _diagnostic_component(source, "footer-and-reference-images")
            code_component = _diagnostic_component(source, "source-code")
            if image_component.get("outcome") != "supported":
                raise AdmissionRefused(f"diagnostic-closeout-rights-mismatch:{source_id}:footer-and-reference-images")
            if code_component.get("outcome") != "supported":
                raise AdmissionRefused(f"diagnostic-closeout-rights-mismatch:{source_id}:source-code")
            for component_id, component in (("source-code", code_component),
                                            ("footer-and-reference-images", image_component)):
                scope = component.get("scope")
                if (not isinstance(scope, dict) or scope.get("repository") != "supported"
                        or scope.get("public_ci") != "supported"):
                    raise AdmissionRefused(f"diagnostic-closeout-rights-scope-mismatch:{source_id}:{component_id}")
            font_component = _diagnostic_component(source, "mgblib-font-data")
            if font_component.get("outcome") != "excluded-by-design":
                raise AdmissionRefused(f"diagnostic-closeout-font-rights-mutated:{source_id}")
        runtime = _validate_acid2_runtime_result(acid2.get("runtime"))
        if acid2.get("status") == "admitted-before-runtime" and runtime["status"] != "pending":
            raise AdmissionRefused("diagnostic-closeout-acid2-runtime-status-mismatch")
        if acid2.get("status") == "executed" and runtime["status"] != "pass":
            raise AdmissionRefused("diagnostic-closeout-acid2-runtime-status-mismatch")
        if acid2.get("status") == "runtime-failed" and runtime["status"] not in ("mismatch", "bounded-failure"):
            raise AdmissionRefused("diagnostic-closeout-acid2-runtime-status-mismatch")
    if kind in ("gbmicrotest", "all"):
        gbmicrotest = record.get("gbmicrotest")
        if not isinstance(gbmicrotest, dict) or inventory is None:
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-stage-missing")
        source = _diagnostic_source_by_id(rights_record, "gbmicrotest-463eb6b")
        if (source.get("commit") != GBMICROTEST_COMMIT
                or source.get("root_tree_sha1") != GBMICROTEST_TREE):
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-rights-pin-mismatch")
        source_component = _diagnostic_component(source, "source-code")
        rom_component = _diagnostic_component(source, "prebuilt-roms")
        logo_component = _diagnostic_component(source, "embedded-logo")
        if source_component.get("outcome") != "supported":
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-source-scope-mismatch")
        if rom_component.get("outcome") != "unresolved" or logo_component.get("outcome") != "unresolved":
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-rights-mismatch")
        runtime_complete = gbmicrotest.get("status") == "executed"
        runtime_failed = gbmicrotest.get("status") == "runtime-failed"
        rights_blocked = gbmicrotest.get("status") == "blocked-before-admission"
        runtime_result = None
        if runtime_complete or runtime_failed:
            accounting = gbmicrotest.get("accounting")
            runtime_results = accounting.get("runtime_results") if isinstance(accounting, dict) else None
            runtime_result = _validate_gbmicrotest_runtime_result(runtime_results)
            if (runtime_complete and runtime_result["verdict"] != "pass"
                    or runtime_failed and runtime_result["verdict"] not in ("source-failure", "bounded-failure")):
                raise AdmissionRefused("diagnostic-closeout-gbmicrotest-runtime-status-mismatch")
        if gbmicrotest.get("status") not in ("blocked-before-admission", "admitted-before-runtime",
                                              "executed", "runtime-failed"):
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-status-mutated")
        runtime_status = ("not-run" if rights_blocked else "pending" if runtime_result is None else
                          "pass" if runtime_result["verdict"] == "pass" else runtime_result["verdict"])
        expected_source_review = {
            "selected_case": GBMICROTEST_SELECTED_CASE,
            "selection_basis": "One DIV-counter software diagnostic selected from the pinned shared-macro protocol group before any emulator outcome was observed.",
            "review_bundle": {
                "status": "committed-review-bundle-one-case-output-scope-supported",
                "manifest_path": "fixtures/gbmicrotest/manifest.json",
                "manifest_sha256": GBMICROTEST_MANIFEST_SHA256,
                "commit": GBMICROTEST_ADMISSION_COMMIT,
                "bundle_path": "fixtures/gbmicrotest/cohort.tar",
                "bundle_sha256": GBMICROTEST_BUNDLE_SHA256,
                "identity_path": "fixtures/gbmicrotest/identity.json",
                "identity_sha256": GBMICROTEST_IDENTITY_SHA256,
                "original_rom_bundled": False,
                "logo_bytes_bundled": False,
            },
            "build_script": {
                "commit": GBMICROTEST_COMMIT,
                "git_blob_sha1": GBMICROTEST_BUILD_BLOB,
                "path": "build.sh",
                "repository": "https://github.com/aappleby/gbmicrotest",
                "sha256": GBMICROTEST_BUILD_SHA256,
                "size_bytes": 308,
                "execution_status": "not-run; WLA-DX version is not pinned",
            },
            "header": {
                "repository": "https://github.com/aappleby/gbmicrotest",
                "commit": GBMICROTEST_COMMIT,
                "path": "tests/header.inc",
                "git_blob_sha1": GBMICROTEST_HEADER_BLOB,
                "size_bytes": 956,
                "sha256": GBMICROTEST_HEADER_SHA256,
                "url": f"https://raw.githubusercontent.com/aappleby/gbmicrotest/{GBMICROTEST_COMMIT}/tests/header.inc",
            },
            "local_rom_review": {
                "review_area": "build/phase24/source-review/gbmicrotest (ignored local review only)",
                "source_commit": GBMICROTEST_COMMIT,
                "admission_status": "admitted-one-case" if not rights_blocked else "not-admitted-output-scope-unresolved",
                "staging_status": "selected-derivative-only" if not rights_blocked else "review-bundle-committed-before-rights-reassessment",
                "runtime_status": runtime_status,
                "original": {
                    "path": "bin/div_inc_timing_a.gb",
                    "git_blob_sha1": GBMICROTEST_SELECTED_ROM_BLOB,
                    "sha256": GBMICROTEST_SELECTED_ROM_SHA256,
                    "size_bytes": 32768,
                    "header_checksum_0x014D": "0x07",
                    "header_checksum_valid": True,
                    "global_checksum_0x014E_0x014F": "0x2C3E",
                    "global_checksum_valid": True,
                    "logo_range_sha256": "daf4cabdc852baa0291849203f0b41fd0b4ecd58e0d7aff4a509f5de4d7f9a2e",
                },
                "derivative": {
                    "path": "derived/div_inc_timing_a.bootless.gb",
                    "sha256": GBMICROTEST_SELECTED_DERIVATIVE_SHA256,
                    "size_bytes": 32768,
                    "kind": "one-case bootless header derivative; original ROM remains local-only",
                },
                "transform": {
                    "zero_range": ["0x0104", "0x0133"],
                    "recomputed_global_checksum_range": ["0x014E", "0x014F"],
                    "changed_offset_count": 44,
                    "changed_offset_ranges": [
                        ["0x0104", "0x0109"], ["0x010B", "0x010D"],
                        ["0x010F", "0x010F"], ["0x0111", "0x0111"],
                        ["0x0113", "0x0113"], ["0x0115", "0x0119"],
                        ["0x011B", "0x0133"], ["0x014E", "0x014F"],
                    ],
                    "all_changed_offsets_allowlisted": True,
                    "all_other_bytes_identical": True,
                    "header_checksum_0x014D_preserved": True,
                    "logo_range_zeroed": True,
                    "derivative_global_checksum_0x014E_0x014F": "0x16F8",
                    "derivative_global_checksum_valid": True,
                },
            },
            "source": {
                "repository": "https://github.com/aappleby/gbmicrotest",
                "commit": GBMICROTEST_COMMIT,
                "path": "tests/div_inc_timing_a.s",
                "git_blob_sha1": GBMICROTEST_SELECTED_SOURCE_BLOB,
                "size_bytes": GBMICROTEST_SELECTED_SOURCE_SIZE,
                "sha256": GBMICROTEST_SELECTED_SOURCE_SHA256,
                "url": f"https://raw.githubusercontent.com/aappleby/gbmicrotest/{GBMICROTEST_COMMIT}/tests/div_inc_timing_a.s",
            },
            "macros": {
                "repository": "https://github.com/aappleby/gbmicrotest",
                "commit": GBMICROTEST_COMMIT,
                "path": "tests/macros.inc",
                "git_blob_sha1": GBMICROTEST_MACROS_BLOB,
                "size_bytes": GBMICROTEST_MACROS_SIZE,
                "sha256": GBMICROTEST_MACROS_SHA256,
                "url": f"https://raw.githubusercontent.com/aappleby/gbmicrotest/{GBMICROTEST_COMMIT}/tests/macros.inc",
            },
            "output_scope": {
                "status": "supported-bounded-selected-derivative",
                "component": "selected prebuilt ROM and its source-bound bootless derivative; Nintendo logo excluded from the bundle",
                "root_license": {
                    "path": "LICENSE",
                    "git_blob_sha1": GBMICROTEST_LICENSE_BLOB,
                    "size_bytes": 1065,
                    "sha256": GBMICROTEST_LICENSE_SHA256,
                    "url": f"https://raw.githubusercontent.com/aappleby/gbmicrotest/{GBMICROTEST_COMMIT}/LICENSE",
                },
                "readme": {
                    "path": "README.md",
                    "git_blob_sha1": GBMICROTEST_README_BLOB,
                    "size_bytes": 1616,
                    "sha256": GBMICROTEST_README_SHA256,
                    "url": f"https://raw.githubusercontent.com/aappleby/gbmicrotest/{GBMICROTEST_COMMIT}/README.md",
                },
                "finding": "Pinned issue #1 asks under what license the files are provided; author aappleby replies 'License added.' The pinned source commit is titled 'Create LICENSE' and changes only the root LICENSE. Together with the README's prebuilt ROM inventory and the included full MIT notice, this supports a bounded MIT output scope for the selected prebuilt ROM and its source-bound bootless derivative. The original logo range remains excluded from the bundle under T5's separate unresolved embedded-logo fact.",
                "rights_evidence": {
                    "issue": GBMICROTEST_LICENSE_ISSUE,
                    "license_commit": GBMICROTEST_LICENSE_COMMIT,
                },
                "scope_limit": "This one-case inference covers only div_inc_timing_a's pinned prebuilt ROM and its source-bound bootless derivative with the full MIT notice. The bundle includes only the derivative after logo removal; it excludes original ROM bytes, all Nintendo logo bytes, the other 512 ROMs, and other sources. It does not change T5's unresolved source-wide prebuilt-ROM or embedded-logo outcomes.",
                "references": ["https://opensource.org/license/mit", "https://opensource.org/osd"],
                "status": "supported-bounded-selected-derivative",
            },
            "logo_scope": {
                "t5_upstream_component_outcome": "unresolved",
                "current_derivative_status": "selected derivative has logo bytes removed; no logo bytes are bundled",
                "source_header_path": "tests/header.inc",
                "source_header_git_blob_sha1": GBMICROTEST_HEADER_BLOB,
                "source_header_sha256": GBMICROTEST_HEADER_SHA256,
                "source_directive": ".nintendologo",
                "original_logo_range_sha256": "daf4cabdc852baa0291849203f0b41fd0b4ecd58e0d7aff4a509f5de4d7f9a2e",
                "zeroed_range": ["0x0104", "0x0133"],
                "derivative_range_all_zero": True,
            },
            "protocol": {
                "initial_operations": ["clear DIV", "execute 60 NOPs", "read DIV"],
                "expected_div": 0,
                "report_registers": {"actual": "FF80", "expected": "FF81", "status": "FF82"},
                "status_values": {"pass": "01", "fail": "FF"},
                "terminal_behavior": "The report macro enters a VRAM display loop; a runner must stop on the terminal marker under explicit bounded guest execution.",
                "source_oracle": "source-defined DIV expectation and pass/fail result are explicit in the pinned assembly and macros",
                "runtime_status": runtime_status,
            },
            "model_applicability": {
                "status": "supported",
                "candidate_scope": "DMG-CPU-B software diagnostic only",
                "evidence": [
                    f"https://github.com/aappleby/gbmicrotest/blob/{GBMICROTEST_COMMIT}/tests/div_inc_timing_a.s",
                    f"https://github.com/aappleby/gbmicrotest/blob/{GBMICROTEST_COMMIT}/tests/header.inc",
                    f"https://github.com/aappleby/gbmicrotest/blob/{GBMICROTEST_COMMIT}/tests/macros.inc",
                ],
                "reason": "The exact case says pass - dmg, selects a DMG header with .romdmg, and declares DIV=0 after its stated operations. This supports using the source-defined vector against the project's DMG-CPU-B software model only. The README's uncertain DMG-CPU-08 statement is suite-wide and is not used as case-level hardware evidence.",
                "hardware_applicability": "not-established; no hardware or DMG-CPU-08 claim",
                "cgb_applicability": "not-established",
            },
        }
        if gbmicrotest.get("source") != {
                "repository": "https://github.com/aappleby/gbmicrotest",
                "commit": GBMICROTEST_COMMIT, "root_tree_sha1": GBMICROTEST_TREE,
                "tree_entry_count": 1034, "tree_truncated": False}:
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-source-mutated")
        if gbmicrotest.get("source_review") != expected_source_review:
            actual_review = gbmicrotest.get("source_review")
            if isinstance(actual_review, dict):
                changed_review_fields = sorted(
                    key for key in set(actual_review) | set(expected_source_review)
                    if actual_review.get(key) != expected_source_review.get(key))
            else:
                changed_review_fields = ["<record>"]
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-source-review-mutated:" +
                                   ",".join(changed_review_fields))
        expected_gb_blockers = (
            ["prebuilt-rom-output-scope-unresolved"] if rights_blocked else
            ["selected-case-" + runtime_result["verdict"]] if runtime_failed else [])
        if gbmicrotest.get("blocked_by") != expected_gb_blockers:
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-blockers-mutated")
        if rights_blocked:
            blockers.append("gbmicrotest-prebuilt-rom-output-scope-unresolved")
        elif runtime_failed:
            blockers.append("gbmicrotest-selected-case-" + runtime_result["verdict"])
        expected_cohort_status = ("executed" if runtime_complete else
                                  "runtime-failed" if runtime_failed else
                                  "blocked-before-admission" if rights_blocked else "admitted-before-runtime")
        if gbmicrotest.get("cohort_status") != expected_cohort_status:
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-cohort-status-mutated")
        roster = inventory.get("cases")
        cohort_cases = gbmicrotest.get("cases")
        if (not isinstance(roster, list) or len(roster) != GBMICROTEST_CASE_COUNT
                or not isinstance(cohort_cases, list) or len(cohort_cases) != GBMICROTEST_CASE_COUNT):
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-roster-count-mismatch")
        expected_rows: list[dict[str, Any]] = []
        excluded_names: list[str] = []
        for item in roster:
            name = item["name"]
            source_identity = item["source"]
            rom_identity = item["prebuilt_rom"]
            if name == GBMICROTEST_SELECTED_CASE:
                disposition = ({
                    "status": "blocked-candidate",
                    "blocked_by": ["prebuilt-rom-output-scope-unresolved"],
                    "reason": "Pinned source/model/oracle and bootless transform were reviewed, but the T6 source/output/header component-term gate remains unresolved. No diagnostic payload runtime is authorized.",
                } if rights_blocked else {
                    "status": "eligible-for-one-case-cohort",
                    "reason": "Selected before observing emulator outcomes from the pinned shared-macro protocol group; the scoped derivative has an approved output scope.",
                })
            else:
                excluded_names.append(name)
                reason = ("unsupported-verdict-protocol" if item["protocol"]["kind"] == "no-verdict-protocol"
                          else "not-selected-for-the-source-review-question")
                disposition = {"status": "excluded-from-cohort", "reason": reason}
            expected_rows.append({
                "name": name,
                "source": {"path": source_identity["path"],
                           "git_blob_sha1": source_identity["git_blob_sha1"],
                           "size_bytes": source_identity["size_bytes"]},
                "prebuilt_rom": {"path": rom_identity["path"],
                                 "git_blob_sha1": rom_identity["git_blob_sha1"],
                                 "size_bytes": rom_identity["size_bytes"],
                                 "sha256": (GBMICROTEST_SELECTED_ROM_SHA256
                                            if name == GBMICROTEST_SELECTED_CASE else None)},
                "protocol_kind": item["protocol"]["kind"],
                "disposition": disposition,
                **({"derivative": {"kind": "bootless header derivative",
                                    "bundle": "fixtures/gbmicrotest/cohort.tar#bin/div_inc_timing_a.bootless.gb",
                                    "sha256": GBMICROTEST_SELECTED_DERIVATIVE_SHA256,
                                    "size_bytes": 32768}}
                   if name == GBMICROTEST_SELECTED_CASE else {}),
            })
        cohort = gbmicrotest.get("accounting")
        expected_accounting = {
                "roster_projection_sha256": GBMICROTEST_ROSTER_PROJECTION_SHA256,
                "roster_count": GBMICROTEST_CASE_COUNT,
                "roster_accounting_complete": True,
                "admitted_eligible_names": [] if rights_blocked else [GBMICROTEST_SELECTED_CASE],
                "executed_names": [GBMICROTEST_SELECTED_CASE] if runtime_complete else [],
                "blocked_candidate_names": [GBMICROTEST_SELECTED_CASE] if rights_blocked else [],
                "excluded_names": excluded_names,
                "runtime_results": [runtime_result] if runtime_result is not None else [],
                "final_execution_accounting_complete": runtime_complete,
            }
        if cohort != expected_accounting:
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-accounting-mutated")
        if cohort_cases != expected_rows:
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-case-accounting-mutated")
        if runtime_complete:
            _validate_gbmicrotest_runtime_result(cohort["runtime_results"])
        if record.get("status") not in ("admitted-before-runtime", "runtime-pass", "runtime-failed"):
            raise AdmissionRefused("diagnostic-closeout-status-mutated")
    if kind == "acid2" and record.get("status") not in ("admitted-before-runtime", "runtime-pass", "runtime-failed"):
        raise AdmissionRefused("diagnostic-closeout-status-mutated")
    acid2_record = record.get("acid2")
    gb_record = record.get("gbmicrotest")
    if isinstance(acid2_record, dict) and isinstance(gb_record, dict):
        acid2_runtime = _validate_acid2_runtime_result(acid2_record.get("runtime"))
        gb_runtime = None
        if gb_record.get("status") in ("executed", "runtime-failed"):
            accounting = gb_record.get("accounting")
            gb_runtime = _validate_gbmicrotest_runtime_result(
                accounting.get("runtime_results") if isinstance(accounting, dict) else None)
        expected_closeout_status = "admitted-before-runtime"
        if acid2_runtime["status"] != "pending":
            expected_closeout_status = (
                "runtime-pass" if acid2_runtime["status"] == "pass"
                and gb_runtime is not None and gb_runtime["verdict"] == "pass"
                else "runtime-failed")
        if record.get("status") != expected_closeout_status:
            raise AdmissionRefused("diagnostic-closeout-combined-status-mismatch")
    record["_blockers"] = blockers
    return record


def validate_acid2_fixture(root: pathlib.Path, source_revision: str) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Validate the exact admitted Acid2 snapshot, rights record, and bounded archive."""
    fixture_paths = (
        ACID2_FIXTURE_MANIFEST, ACID2_FIXTURE_ADMISSION_PIN, ACID2_FIXTURE_BUNDLE,
        ACID2_FIXTURE_NOTICE, ACID2_FIXTURE_SOURCES, "THIRD_PARTY_NOTICES.md",
        PHASE20_CHECKER_PATH, PHASE20_POLICY_PATH, "tests/scripts/verify-acid2-masks.py",
        "tests/scripts/run-acid2-local.py",
    )
    for relative in fixture_paths:
        require_worktree_source_file(root, source_revision, relative, root / relative)

    manifest_raw = read_source_file(root, source_revision, ACID2_FIXTURE_MANIFEST)
    pointer_raw = read_source_file(root, source_revision, ACID2_FIXTURE_ADMISSION_PIN)
    archive_raw = read_source_file(root, source_revision, ACID2_FIXTURE_BUNDLE)
    notice = read_source_file(root, source_revision, ACID2_FIXTURE_NOTICE)
    if (sha256(manifest_raw) != ACID2_FIXTURE_MANIFEST_SHA256
            or pointer_raw != (ACID2_FIXTURE_ADMISSION_COMMIT + "\n").encode("ascii")
            or sha256(archive_raw) != ACID2_FIXTURE_BUNDLE_SHA256
            or len(archive_raw) != ACID2_FIXTURE_BUNDLE_SIZE
            or sha256(notice) != ACID2_FIXTURE_NOTICE_SHA256):
        raise AdmissionRefused("diagnostic-closeout-acid2-fixture-identity-mismatch")

    phase20 = root / PHASE20_CHECKER_PATH
    code, stdout, stderr = _bounded_run(
        [sys.executable, "-I", str(phase20), "--check-manifest",
         ACID2_FIXTURE_MANIFEST, "--repo-root", str(root)], cwd=root, timeout=10)
    if code != 0 or b"PASS: fixture admission" not in stdout:
        detail = (stdout + stderr).decode("utf-8", "replace")[:240]
        raise AdmissionRefused("diagnostic-closeout-acid2-manifest-refused:" + detail)

    masks = _load_module("phase24_acid2_masks", root / "tests/scripts/verify-acid2-masks.py")
    manifest_raw_inner = masks._extract_inner_manifest(archive_raw)
    manifest = masks._json_no_duplicate_keys(manifest_raw_inner, "acid2-inner-manifest")
    members = masks.read_bundle(
        archive_raw, manifest, expected_bundle_sha256=ACID2_FIXTURE_BUNDLE_SHA256,
        expected_bundle_size_bytes=ACID2_FIXTURE_BUNDLE_SIZE)
    masks.validate_bundle_manifest(root, manifest, members)
    derivatives = {row.get("kind"): row for row in manifest.get("derivatives", [])
                   if isinstance(row, dict)}
    if set(derivatives) != set(ACID2_DERIVATIVES):
        raise AdmissionRefused("diagnostic-closeout-acid2-derivative-set-invalid")
    for kind, (path, expected_sha, model) in ACID2_DERIVATIVES.items():
        row = derivatives[kind]
        content = members.get(path)
        scope = manifest.get("model_scope", {}).get(kind)
        if (not isinstance(content, bytes) or row.get("path") != path
                or row.get("sha256") != expected_sha or sha256(content) != expected_sha
                or row.get("size_bytes") != 32768 or len(content) != 32768
                or scope != {"excluded_claims": ["glyph-accuracy", "mode-3-timing", "hardware-qualification"],
                             "hardware_claim": False, "runner_model": model}):
            raise AdmissionRefused(f"diagnostic-closeout-acid2-derivative-or-model-mismatch:{kind}")
    return members, manifest


def validate_gbmicrotest_fixture(root: pathlib.Path, source_revision: str) -> dict[str, bytes]:
    """Bind the exact committed one-case manifest, notice, and safe deterministic archive."""
    fixture_paths = (
        "fixtures/gbmicrotest/manifest.json", "fixtures/gbmicrotest/admission.commit",
        "fixtures/gbmicrotest/cohort.tar", "fixtures/gbmicrotest/LICENSE.txt",
        "fixtures/gbmicrotest/SOURCES.md", "fixtures/gbmicrotest/identity.json",
        "THIRD_PARTY_NOTICES.md", PHASE20_CHECKER_PATH, PHASE20_POLICY_PATH,
    )
    for relative in fixture_paths:
        require_worktree_source_file(root, source_revision, relative, root / relative)
    manifest_raw = read_source_file(root, source_revision, "fixtures/gbmicrotest/manifest.json")
    archive_raw = read_source_file(root, source_revision, "fixtures/gbmicrotest/cohort.tar")
    identity_raw = read_source_file(root, source_revision, "fixtures/gbmicrotest/identity.json")
    notice = read_source_file(root, source_revision, "fixtures/gbmicrotest/LICENSE.txt")
    pin_raw = read_source_file(root, source_revision, "fixtures/gbmicrotest/admission.commit")
    if sha256(manifest_raw) != GBMICROTEST_MANIFEST_SHA256 or sha256(archive_raw) != GBMICROTEST_BUNDLE_SHA256:
        raise AdmissionRefused("diagnostic-closeout-gbmicrotest-fixture-digest-mismatch")
    if sha256(identity_raw) != GBMICROTEST_IDENTITY_SHA256 or sha256(notice) != GBMICROTEST_LICENSE_SHA256:
        raise AdmissionRefused("diagnostic-closeout-gbmicrotest-identity-or-notice-mismatch")
    if pin_raw != (GBMICROTEST_ADMISSION_COMMIT + "\n").encode("ascii"):
        raise AdmissionRefused("diagnostic-closeout-gbmicrotest-admission-pin-mismatch")
    phase20 = root / PHASE20_CHECKER_PATH
    code, stdout, stderr = _bounded_run(
        [sys.executable, "-I", str(phase20), "--check-manifest",
         "fixtures/gbmicrotest/manifest.json", "--repo-root", str(root)], cwd=root, timeout=10)
    if code != 0 or b"PASS: fixture admission" not in stdout:
        detail = (stdout + stderr).decode("utf-8", "replace")[:240]
        raise AdmissionRefused("diagnostic-closeout-gbmicrotest-manifest-refused:" + detail)

    expected_names = {
        "LICENSE", "README.md", "identity.json", "tests/div_inc_timing_a.s",
        "tests/header.inc", "tests/macros.inc", "bin/div_inc_timing_a.bootless.gb",
    }
    try:
        with tarfile.open(fileobj=io.BytesIO(archive_raw), mode="r:") as bundle:
            members = bundle.getmembers()
            names = [member.name for member in members]
            if (len(members) != 7 or set(names) != expected_names or len(set(names)) != 7
                    or sum(member.size for member in members) > 128 * 1024):
                raise AdmissionRefused("diagnostic-closeout-gbmicrotest-archive-inventory-invalid")
            content: dict[str, bytes] = {}
            for member in members:
                path = pathlib.PurePosixPath(member.name)
                if (not member.isfile() or path.is_absolute() or ".." in path.parts
                        or member.size < 0 or member.size > MAX_ROM_BYTES):
                    raise AdmissionRefused("diagnostic-closeout-gbmicrotest-archive-member-invalid")
                stream = bundle.extractfile(member)
                if stream is None:
                    raise AdmissionRefused("diagnostic-closeout-gbmicrotest-archive-read-failed")
                data = stream.read(member.size + 1)
                if len(data) != member.size:
                    raise AdmissionRefused("diagnostic-closeout-gbmicrotest-archive-size-mismatch")
                content[member.name] = data
    except (tarfile.TarError, OSError):
        raise AdmissionRefused("diagnostic-closeout-gbmicrotest-archive-invalid") from None
    if "bin/div_inc_timing_a.gb" in content or "NintendoLogo" in content:
        raise AdmissionRefused("diagnostic-closeout-gbmicrotest-original-or-logo-member-present")
    if (sha256(content["LICENSE"]) != GBMICROTEST_LICENSE_SHA256
            or content["LICENSE"] != notice
            or sha256(content["README.md"]) != GBMICROTEST_README_SHA256
            or _git_blob_sha1(content["README.md"]) != GBMICROTEST_README_BLOB
            or sha256(content["tests/div_inc_timing_a.s"]) != GBMICROTEST_SELECTED_SOURCE_SHA256
            or _git_blob_sha1(content["tests/div_inc_timing_a.s"]) != GBMICROTEST_SELECTED_SOURCE_BLOB
            or sha256(content["tests/macros.inc"]) != GBMICROTEST_MACROS_SHA256
            or _git_blob_sha1(content["tests/macros.inc"]) != GBMICROTEST_MACROS_BLOB
            or sha256(content["tests/header.inc"]) != GBMICROTEST_HEADER_SHA256
            or _git_blob_sha1(content["tests/header.inc"]) != GBMICROTEST_HEADER_BLOB):
        raise AdmissionRefused("diagnostic-closeout-gbmicrotest-source-member-mismatch")
    assembly = content["tests/div_inc_timing_a.s"]
    macros = content["tests/macros.inc"]
    if not all(item in assembly for item in (b"pass - dmg", b"ldh (DIV), a", b"nops 60", b"test_finish_div 0")):
        raise AdmissionRefused("diagnostic-closeout-gbmicrotest-oracle-source-mismatch")
    if not all(item in macros for item in (b"ldh ($80), a", b"ldh ($81), a", b"ldh ($82), a",
                                           b"PASS_PATTERN $01", b"FAIL_PATTERN $FF")):
        raise AdmissionRefused("diagnostic-closeout-gbmicrotest-protocol-source-mismatch")
    derivative = content["bin/div_inc_timing_a.bootless.gb"]
    if (len(derivative) != 32768 or sha256(derivative) != GBMICROTEST_SELECTED_DERIVATIVE_SHA256
            or any(derivative[0x104:0x134]) or _header_checksum(derivative) != derivative[0x14D]
            or ((derivative[0x14E] << 8) | derivative[0x14F]) != 0x16F8
            or (sum(derivative[:0x14E] + derivative[0x150:]) & 0xFFFF) != 0x16F8):
        raise AdmissionRefused("diagnostic-closeout-gbmicrotest-derivative-invalid")
    identity = _json_without_duplicates(identity_raw, "gbmicrotest-fixture-identity")
    if content["identity.json"] != identity_raw:
        raise AdmissionRefused("diagnostic-closeout-gbmicrotest-identity-member-mismatch")
    rights = identity.get("output_rights_interpretation")
    if (identity.get("schema") != "gabbaboy-gbmicrotest-one-case-identity-v1"
            or identity.get("case", {}).get("original_rom_sha256") != GBMICROTEST_SELECTED_ROM_SHA256
            or identity.get("output", {}).get("sha256") != GBMICROTEST_SELECTED_DERIVATIVE_SHA256
            or identity.get("output", {}).get("original_rom_in_bundle") is not False
            or identity.get("output", {}).get("nintendo_logo_bytes_in_bundle") is not False
            or identity.get("model_scope") != "DMG-CPU-B software diagnostic only; no hardware, DMG-CPU-08, or CGB claim"
            or not isinstance(rights, dict)
            or rights.get("status") != "bounded-inference-for-this-modified-copy-only"
            or rights.get("references") != ["https://opensource.org/license/mit", "https://opensource.org/osd"]):
        raise AdmissionRefused("diagnostic-closeout-gbmicrotest-identity-scope-invalid")
    return content


def validate_current_runner_qualification(root: pathlib.Path, source_revision: str,
                                         runner: pathlib.Path,
                                         qualification_path: pathlib.Path,
                                         invocation_started: float | None = None,
                                         deadline_seconds: int = 25) -> dict[str, Any]:
    root = root.resolve(strict=True)
    if runner.is_symlink() or qualification_path.is_symlink():
        raise AdmissionRefused("diagnostic-runtime-runner-or-qualification-unavailable")
    runner = runner.resolve(strict=True)
    qualification_path = qualification_path.resolve(strict=True)
    if (not runner.is_file() or not qualification_path.is_file()
            or qualification_path != root / "build/phase21-evidence/current-runner-qualification.json"):
        raise AdmissionRefused("diagnostic-runtime-runner-or-qualification-unavailable")
    qualification_raw = read_limited(qualification_path, 64 * 1024, "runner-qualification")
    qualification = _json_without_duplicates(qualification_raw, "runner-qualification")
    runner_sha = sha256(read_limited(runner, 64 * 1024 * 1024, "runner-binary"))
    if (qualification.get("source_revision") != source_revision
            or qualification.get("build_qualified") is not True
            or qualification.get("artifact_path") != str(runner)
            or qualification.get("artifact_sha256") != runner_sha):
        raise AdmissionRefused("diagnostic-runtime-qualification-binding-mismatch")
    remaining = (deadline_seconds - (time.monotonic() - invocation_started)
                 if invocation_started is not None else 10)
    if remaining <= 0:
        raise AdmissionRefused("diagnostic-runtime-deadline-expired-before-qualification")
    check_code, check_out, check_err = _bounded_run(
        [sys.executable, "-I", str(root / CANDIDATE_CHECKER_PATH), "--check-build-qualification",
         "--repo-root", str(root), "--source-revision", source_revision,
         "--runner", str(runner), "--current-build-qualification", str(qualification_path)],
        cwd=root, timeout=min(10, remaining))
    if check_code != 0 or b"PASS: current runner qualification" not in check_out:
        detail = (check_out + check_err).decode("utf-8", "replace")[:240]
        raise AdmissionRefused("diagnostic-runtime-qualification-refused:" + detail)
    if invocation_started is not None and time.monotonic() - invocation_started >= deadline_seconds:
        raise AdmissionRefused("diagnostic-runtime-deadline-expired-after-qualification")
    return {"runner": runner, "qualification_path": qualification_path,
            "runner_sha256": runner_sha, "qualification_sha256": sha256(qualification_raw),
            "qualification": qualification}


def run_acid2_runtime(root: pathlib.Path, source_revision: str, runner: pathlib.Path,
                      deadline_seconds: int, invocation_started: float,
                      members: dict[str, bytes], manifest: dict[str, Any],
                      qualified_runner: dict[str, Any],
                      evidence_path: pathlib.Path | None = None) -> dict[str, Any]:
    if deadline_seconds != 25:
        raise AdmissionRefused("diagnostic-runtime-deadline-must-be-25-seconds")
    if time.monotonic() - invocation_started >= deadline_seconds:
        raise AdmissionRefused("diagnostic-runtime-deadline-expired-before-acid2")
    if (qualified_runner.get("runner") != runner.resolve(strict=True)
            or qualified_runner.get("runner_sha256") is None):
        raise AdmissionRefused("diagnostic-runtime-runner-qualification-not-reused")
    module = _load_module("phase24_admitted_acid2_runtime", root / "tests/scripts/run-acid2-local.py")
    results: list[dict[str, Any]] = []
    for profile in ACID2_COMPARISON_PROFILES:
        remaining = deadline_seconds - (time.monotonic() - invocation_started)
        if remaining <= 0:
            raise AdmissionRefused("diagnostic-runtime-deadline-expired-before-acid2-comparison")
        comparison_started = time.monotonic()
        try:
            result = module.run_admitted_comparison(
                members, manifest, runner, profile, remaining)
        except (module.Refused, RuntimeError, subprocess.SubprocessError) as error:
            raise AdmissionRefused(f"diagnostic-runtime-acid2-comparison-refused:{profile}:{error}") from None
        if result.get("runner_sha256") != qualified_runner["runner_sha256"]:
            raise AdmissionRefused("diagnostic-runtime-acid2-runner-qualification-binding-mismatch")
        result["elapsed_seconds"] = round(time.monotonic() - comparison_started, 6)
        results.append(result)
    status = "pass" if all(item.get("verdict") == "pass" for item in results) else "mismatch"
    closeout_raw = read_source_file(root, source_revision, DIAGNOSTIC_CLOSEOUT_PATH)
    evidence = {
        "schema": "gabbaboy-acid2-runtime-evidence-v1",
        "source_revision": source_revision,
        "closeout_record_sha256": sha256(closeout_raw),
        "fixture_admission_commit": ACID2_FIXTURE_ADMISSION_COMMIT,
        "manifest_sha256": ACID2_FIXTURE_MANIFEST_SHA256,
        "bundle_sha256": ACID2_FIXTURE_BUNDLE_SHA256,
        "runner_sha256": qualified_runner["runner_sha256"],
        "qualification_sha256": qualified_runner["qualification_sha256"],
        "comparisons": results,
        "status": status,
    }
    if evidence_path is not None:
        target = evidence_path if evidence_path.is_absolute() else root / evidence_path
        try:
            relative = target.resolve(strict=False).relative_to(root).as_posix()
        except ValueError:
            raise AdmissionRefused("diagnostic-runtime-acid2-evidence-path-outside-repository") from None
        if (relative != ACID2_RUNTIME_EVIDENCE_PATH or target.is_symlink() or target.exists()):
            raise AdmissionRefused("diagnostic-runtime-acid2-evidence-path-invalid-or-exists")
        ignored = subprocess.run(["git", "check-ignore", "-q", relative], cwd=root,
                                 check=False, timeout=5)
        if ignored.returncode != 0:
            raise AdmissionRefused("diagnostic-runtime-acid2-evidence-path-not-ignored")
        raw = (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode("utf-8")
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("xb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        except OSError as error:
            raise AdmissionRefused("diagnostic-runtime-acid2-evidence-write-failed:" +
                                   (error.strerror or "write")) from None
        evidence["evidence_path"] = relative
        evidence["evidence_sha256"] = sha256(raw)
    return evidence


def run_gbmicrotest_runtime(root: pathlib.Path, source_revision: str, runner: pathlib.Path,
                            qualification_path: pathlib.Path, deadline_seconds: int,
                            evidence_path: pathlib.Path, invocation_started: float,
                            bundle: dict[str, bytes],
                            qualified_runner: dict[str, Any] | None = None) -> dict[str, Any]:
    if deadline_seconds != 25:
        raise AdmissionRefused("diagnostic-runtime-deadline-must-be-25-seconds")
    if time.monotonic() - invocation_started >= deadline_seconds:
        raise AdmissionRefused("diagnostic-runtime-deadline-expired-before-runner")
    root = root.resolve(strict=True)
    closeout_raw = read_source_file(root, source_revision, DIAGNOSTIC_CLOSEOUT_PATH)
    closeout_sha = sha256(closeout_raw)
    if read_limited(root / DIAGNOSTIC_CLOSEOUT_PATH, MAX_JSON_BYTES, "diagnostic-closeout") != closeout_raw:
        raise AdmissionRefused("diagnostic-runtime-closeout-json-differs-from-committed-source")
    qualified = qualified_runner or validate_current_runner_qualification(
        root, source_revision, runner, qualification_path, invocation_started, deadline_seconds)
    runner = qualified["runner"]
    qualification = qualified["qualification"]
    runner_sha = qualified["runner_sha256"]
    qualification_sha = qualified["qualification_sha256"]

    derivative = bundle["bin/div_inc_timing_a.bootless.gb"]
    case_line = (
        "id=div-inc-a rom=div_inc_timing_a.bootless.gb rom_sha256=" + sha256(derivative)
        + " rom_size=32768 oracle=diagnostic-shared-ff80-ff82 diagnostic_expected=00"
        + " budget_half_dots=8192 instruction_limit=512 event_limit=4096 model_pass=dmg-cpu-b\n"
    ).encode("ascii")
    temporary_root: pathlib.Path | None = None
    runner_output = b""
    runner_code = 3
    try:
        with tempfile.TemporaryDirectory(prefix="gbb-gbmicrotest-one-case-") as temporary:
            temporary_root = pathlib.Path(temporary)
            (temporary_root / "div_inc_timing_a.bootless.gb").write_bytes(derivative)
            (temporary_root / "cases.txt").write_bytes(case_line)
            remaining = deadline_seconds - (time.monotonic() - invocation_started)
            if remaining <= 0:
                raise AdmissionRefused("diagnostic-runtime-deadline-expired-before-runner")
            runner_code, runner_output, runner_error = _bounded_run(
                [str(runner), "--acceptance", "cases.txt", "--case", "div-inc-a"],
                cwd=temporary_root, timeout=remaining)
            if runner_error:
                raise AdmissionRefused("diagnostic-runtime-runner-stderr:" + runner_error.decode("utf-8", "replace")[:200])
    except RuntimeError as error:
        raise AdmissionRefused("diagnostic-runtime-runner-bounded-failure:" + str(error)) from None
    elapsed = time.monotonic() - invocation_started
    if elapsed > deadline_seconds:
        raise AdmissionRefused("diagnostic-runtime-deadline-exceeded")

    try:
        output_text = runner_output.decode("ascii", "strict").strip()
    except UnicodeDecodeError:
        raise AdmissionRefused("diagnostic-runtime-output-not-ascii") from None
    lines = [line for line in output_text.splitlines() if line.startswith("acceptance id=div-inc-a ")]
    if len(lines) != 1:
        raise AdmissionRefused("diagnostic-runtime-result-line-missing-or-duplicate")
    fields = dict(token.split("=", 1) for token in lines[0].split()[1:] if "=" in token)
    verdict = fields.get("status")
    if fields.get("model") != "dmg-cpu-b":
        raise AdmissionRefused("diagnostic-runtime-model-or-protocol-mismatch")
    if verdict not in ("pass", "fail", "bounded-failure"):
        raise AdmissionRefused("diagnostic-runtime-verdict-fields-invalid")
    if verdict == "bounded-failure":
        required_fields = ("reason", "instructions", "events", "end_half_dots")
        if any(key not in fields for key in required_fields) or any(
                key in fields for key in ("actual", "expected", "terminal", "class", "protocol")):
            raise AdmissionRefused("diagnostic-runtime-bounded-failure-fields-invalid")
        if fields["reason"] not in ("iteration-guard", "guest-stopped", "no-progress",
                                     "instruction-limit", "event-limit", "guest-deadline"):
            raise AdmissionRefused("diagnostic-runtime-bounded-failure-reason-invalid")
        result_verdict = "bounded-failure"
        result_reason: str | None = fields["reason"]
        actual = expected = terminal = None
        expected_exit_code = 3
    else:
        required_fields = ("actual", "expected", "terminal", "instructions", "events", "end_half_dots")
        if any(key not in fields for key in required_fields):
            raise AdmissionRefused("diagnostic-runtime-verdict-fields-invalid")
        if verdict == "pass":
            if fields.get("class") != "diagnostic" or fields.get("protocol") != "shared-ff80-ff82":
                raise AdmissionRefused("diagnostic-runtime-model-or-protocol-mismatch")
            result_verdict = "pass"
            result_reason = None
            expected_exit_code = 0
        else:
            if fields.get("reason") not in ("observed-mismatch", "source-protocol",
                                             "source-verdict-inconsistent"):
                raise AdmissionRefused("diagnostic-runtime-source-failure-reason-invalid")
            if fields.get("class") not in (None, "diagnostic") or fields.get("protocol") not in (
                    None, "shared-ff80-ff82"):
                raise AdmissionRefused("diagnostic-runtime-model-or-protocol-mismatch")
            result_verdict = "source-failure"
            result_reason = fields["reason"]
            expected_exit_code = 1
        actual, expected, terminal = fields["actual"], fields["expected"], fields["terminal"]
    try:
        instruction_count = int(fields["instructions"])
        event_count = int(fields["events"])
        end_half_dots = int(fields["end_half_dots"])
    except ValueError:
        raise AdmissionRefused("diagnostic-runtime-count-invalid") from None
    if (runner_code != expected_exit_code or not 0 <= instruction_count <= 512
            or not 0 <= event_count <= 4096 or not 0 <= end_half_dots <= 8192):
        raise AdmissionRefused("diagnostic-runtime-exit-or-budget-mismatch")
    if result_verdict != "bounded-failure" and (instruction_count == 0 or event_count == 0 or end_half_dots == 0):
        raise AdmissionRefused("diagnostic-runtime-source-outcome-missing-execution")
    if result_verdict == "pass" and (actual != "00" or expected != "00" or terminal != "01"):
        raise AdmissionRefused("diagnostic-runtime-source-oracle-mismatch")

    evidence = {
        "schema": "gabbaboy-gbmicrotest-runtime-evidence-v1",
        "source_revision": source_revision,
        "closeout_record_sha256": closeout_sha,
        "fixture_admission_commit": GBMICROTEST_ADMISSION_COMMIT,
        "manifest_sha256": GBMICROTEST_MANIFEST_SHA256,
        "runner_sha256": runner_sha,
        "qualification_sha256": qualification_sha,
        "qualified_artifact_sha256": qualification["artifact_sha256"],
        "case": GBMICROTEST_SELECTED_CASE,
        "runner_case_id": "div-inc-a",
        "model": fields["model"],
        "verdict": result_verdict,
        "runner_exit_code": runner_code,
        "reason": result_reason,
        "actual": actual,
        "expected": expected,
        "terminal": terminal,
        "instruction_count": instruction_count,
        "event_count": event_count,
        "end_half_dots": end_half_dots,
        "elapsed_seconds": round(elapsed, 6),
        "runner_output": output_text,
    }
    evidence_target = pathlib.Path(evidence_path)
    if not evidence_target.is_absolute():
        evidence_target = root / evidence_target
    try:
        relative_evidence = evidence_target.resolve(strict=False).relative_to(root).as_posix()
    except ValueError:
        raise AdmissionRefused("diagnostic-runtime-evidence-path-outside-repository") from None
    if (relative_evidence not in ("build/phase24/diagnostic-runtime-preflight.json",
                                  GBMICROTEST_RUNTIME_PREFLIGHT_PATH,
                                  GBMICROTEST_RUNTIME_FINAL_PATH)
            or evidence_target.is_symlink() or evidence_target.exists()):
        raise AdmissionRefused("diagnostic-runtime-evidence-path-invalid-or-exists")
    ignored = subprocess.run(["git", "check-ignore", "-q", relative_evidence], cwd=root,
                             check=False, timeout=5)
    if ignored.returncode != 0:
        raise AdmissionRefused("diagnostic-runtime-evidence-path-not-ignored")
    evidence_bytes = (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode("utf-8")
    evidence_target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with evidence_target.open("xb") as stream:
            stream.write(evidence_bytes)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as error:
        raise AdmissionRefused("diagnostic-runtime-evidence-write-failed:" + (error.strerror or "write")) from None
    evidence_sha = sha256(read_limited(evidence_target, MAX_JSON_BYTES, "diagnostic-runtime-evidence"))
    if evidence_sha != sha256(evidence_bytes):
        raise AdmissionRefused("diagnostic-runtime-evidence-digest-mismatch")
    runtime_result = {
        "case": GBMICROTEST_SELECTED_CASE,
        "runner_case_id": "div-inc-a",
        "source_revision": source_revision,
        "closeout_record_sha256": closeout_sha,
        "fixture_admission_commit": GBMICROTEST_ADMISSION_COMMIT,
        "manifest_sha256": GBMICROTEST_MANIFEST_SHA256,
        "source_sha256": GBMICROTEST_SELECTED_SOURCE_SHA256,
        "original_rom_sha256": GBMICROTEST_SELECTED_ROM_SHA256,
        "derivative_sha256": GBMICROTEST_SELECTED_DERIVATIVE_SHA256,
        "model": "dmg-cpu-b",
        "verdict": result_verdict,
        "runner_exit_code": runner_code,
        "reason": result_reason,
        "actual": actual,
        "expected": expected,
        "terminal": terminal,
        "instruction_count": instruction_count,
        "event_count": event_count,
        "end_half_dots": end_half_dots,
        "elapsed_seconds": round(elapsed, 6),
        "runner_sha256": runner_sha,
        "qualification_sha256": qualification_sha,
        "evidence_path": relative_evidence,
        "evidence_sha256": evidence_sha,
    }
    _validate_gbmicrotest_runtime_result([runtime_result], root=root,
                                         expected_source_revision=source_revision,
                                         require_evidence=True)
    return runtime_result


def _write_ignored_json(root: pathlib.Path, relative: str, evidence: dict[str, Any],
                        *, expected_previous_sha256: str | None = None) -> tuple[pathlib.Path, str]:
    target = root / relative
    if target.is_symlink():
        raise AdmissionRefused("diagnostic-runtime-evidence-path-invalid-or-exists")
    if target.exists():
        prior_raw = read_limited(target, MAX_JSON_BYTES, "prior-runtime-evidence")
        prior_sha = sha256(prior_raw)
        if relative != DIAGNOSTIC_RUNTIME_PREFLIGHT_PATH:
            raise AdmissionRefused("diagnostic-runtime-evidence-path-invalid-or-exists")
        if expected_previous_sha256 is not None and prior_sha != expected_previous_sha256:
            raise AdmissionRefused("diagnostic-runtime-prior-evidence-binding-mismatch")
        if expected_previous_sha256 is None:
            if prior_sha != LEGACY_GBMICROTEST_PREFLIGHT_SHA256:
                raise AdmissionRefused("diagnostic-runtime-unknown-prior-evidence-refused")
            preserved = root / f"build/phase24/diagnostic-runtime-preflight-archive-{prior_sha}.json"
            if preserved.is_symlink():
                raise AdmissionRefused("diagnostic-runtime-prior-evidence-preservation-path-unsafe")
            if preserved.exists():
                if sha256(read_limited(preserved, MAX_JSON_BYTES, "archived-prior-runtime-evidence")) != prior_sha:
                    raise AdmissionRefused("diagnostic-runtime-prior-evidence-preservation-mismatch")
                target.unlink()
            else:
                target.rename(preserved)
            ignored_archive = subprocess.run(["git", "check-ignore", "-q", preserved.relative_to(root).as_posix()],
                                             cwd=root, check=False, timeout=5)
            if ignored_archive.returncode != 0:
                raise AdmissionRefused("diagnostic-runtime-prior-evidence-archive-not-ignored")
        else:
            preserved = root / "build/phase24/diagnostic-runtime-preflight.legacy-gbmicrotest.json"
            if preserved.exists() or preserved.is_symlink():
                raise AdmissionRefused("diagnostic-runtime-prior-evidence-preservation-path-exists")
            target.rename(preserved)
    ignored = subprocess.run(["git", "check-ignore", "-q", relative], cwd=root,
                             check=False, timeout=5)
    if ignored.returncode != 0:
        raise AdmissionRefused("diagnostic-runtime-evidence-path-not-ignored")
    raw = (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode("utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as error:
        raise AdmissionRefused("diagnostic-runtime-evidence-write-failed:" +
                               (error.strerror or "write")) from None
    if sha256(read_limited(target, MAX_JSON_BYTES, "diagnostic-runtime-evidence")) != sha256(raw):
        raise AdmissionRefused("diagnostic-runtime-evidence-digest-mismatch")
    return target, sha256(raw)


def _stable_gbmicrotest_result(result: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items()
            if key not in {"source_revision", "closeout_record_sha256", "evidence_path",
                           "evidence_sha256", "elapsed_seconds"}}


def _stable_acid2_comparisons(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: value for key, value in result.items() if key != "elapsed_seconds"}
            for result in results]


def _record_combined_preflight_result(root: pathlib.Path, source_revision: str,
                                      closeout_sha256: str, acid2_runtime: dict[str, Any],
                                      gb_runtime: dict[str, Any], evidence_path: str,
                                      evidence_sha256: str) -> None:
    root = root.resolve(strict=True)
    record_path = root / DIAGNOSTIC_CLOSEOUT_PATH
    source_raw = read_source_file(root, source_revision, DIAGNOSTIC_CLOSEOUT_PATH)
    current_raw = read_limited(record_path, MAX_JSON_BYTES, "diagnostic-closeout")
    if current_raw != source_raw or sha256(current_raw) != closeout_sha256:
        raise AdmissionRefused("diagnostic-runtime-closeout-changed-before-preflight-record")
    if (acid2_runtime.get("source_revision") != source_revision
            or acid2_runtime.get("closeout_record_sha256") != closeout_sha256
            or acid2_runtime.get("status") not in ("pass", "mismatch")
            or gb_runtime.get("source_revision") != source_revision
            or gb_runtime.get("closeout_record_sha256") != closeout_sha256
            or gb_runtime.get("verdict") not in ("pass", "source-failure", "bounded-failure")):
        raise AdmissionRefused("diagnostic-runtime-preflight-result-not-complete")
    record = _json_without_duplicates(current_raw, "diagnostic-closeout")
    acid2 = record.get("acid2")
    gb = record.get("gbmicrotest")
    if (not isinstance(acid2, dict) or acid2.get("status") != "admitted-before-runtime"
            or not isinstance(gb, dict) or gb.get("status") != "admitted-before-runtime"):
        raise AdmissionRefused("diagnostic-runtime-preflight-closeout-state-invalid")
    acid2["runtime"] = {
        "status": acid2_runtime["status"], "source_revision": source_revision,
        "closeout_record_sha256": closeout_sha256,
        "fixture_admission_commit": ACID2_FIXTURE_ADMISSION_COMMIT,
        "manifest_sha256": ACID2_FIXTURE_MANIFEST_SHA256,
        "bundle_sha256": ACID2_FIXTURE_BUNDLE_SHA256,
        "runner_sha256": acid2_runtime["runner_sha256"],
        "qualification_sha256": acid2_runtime["qualification_sha256"],
        "evidence_path": evidence_path, "evidence_sha256": evidence_sha256,
        "comparisons": acid2_runtime["comparisons"],
    }
    acid2["status"] = "executed" if acid2_runtime["status"] == "pass" else "runtime-failed"
    gb_passed = gb_runtime["verdict"] == "pass"
    gb["status"] = "executed" if gb_passed else "runtime-failed"
    gb["cohort_status"] = gb["status"]
    gb["blocked_by"] = [] if gb_passed else ["selected-case-" + gb_runtime["verdict"]]
    accounting = gb.get("accounting")
    if (not isinstance(accounting, dict) or accounting.get("runtime_results") != []
            or accounting.get("executed_names") != []):
        raise AdmissionRefused("diagnostic-runtime-preflight-accounting-invalid")
    accounting["executed_names"] = [GBMICROTEST_SELECTED_CASE] if gb_passed else []
    accounting["final_execution_accounting_complete"] = gb_passed
    accounting["runtime_results"] = [gb_runtime]
    source_review = gb.get("source_review")
    if isinstance(source_review, dict):
        local_review = source_review.get("local_rom_review")
        if isinstance(local_review, dict):
            local_review["runtime_status"] = "pass" if gb_passed else gb_runtime["verdict"]
        protocol = source_review.get("protocol")
        if isinstance(protocol, dict):
            protocol["runtime_status"] = "pass" if gb_passed else gb_runtime["verdict"]
    record["status"] = ("runtime-pass" if gb_passed and acid2_runtime["status"] == "pass"
                         else "runtime-failed")
    updated = (json.dumps(record, indent=2) + "\n").encode("utf-8")
    temporary = record_path.with_name(record_path.name + ".preflight.tmp")
    if temporary.exists() or temporary.is_symlink():
        raise AdmissionRefused("diagnostic-runtime-closeout-temporary-path-exists")
    try:
        with temporary.open("xb") as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, record_path)
    except OSError as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise AdmissionRefused("diagnostic-runtime-closeout-write-failed:" +
                               (error.strerror or "write")) from None


def _verify_combined_runtime_stable(record: dict[str, Any], acid2_runtime: dict[str, Any],
                                    gb_runtime: dict[str, Any]) -> None:
    acid2 = record.get("acid2")
    gb = record.get("gbmicrotest")
    if not isinstance(acid2, dict) or not isinstance(gb, dict):
        raise AdmissionRefused("diagnostic-runtime-preflight-record-missing")
    baseline = _validate_acid2_runtime_result(acid2.get("runtime"))
    if (baseline["status"] != "pass"
            or acid2_runtime.get("status") != "pass"
            or _stable_acid2_comparisons(baseline["comparisons"])
            != _stable_acid2_comparisons(acid2_runtime.get("comparisons", []))
            or acid2_runtime.get("status") != "pass"):
        raise AdmissionRefused("diagnostic-runtime-acid2-preflight-outcome-changed")
    accounting = gb.get("accounting")
    baseline_rows = accounting.get("runtime_results") if isinstance(accounting, dict) else None
    baseline_gb = _validate_gbmicrotest_runtime_result(baseline_rows)
    if (baseline_gb["verdict"] != "pass" or gb_runtime.get("verdict") != "pass"
            or _stable_gbmicrotest_result(baseline_gb) != _stable_gbmicrotest_result(gb_runtime)):
        raise AdmissionRefused("diagnostic-runtime-gbmicrotest-preflight-outcome-changed")


def record_gbmicrotest_runtime_result(root: pathlib.Path, source_revision: str,
                                       runtime_result: dict[str, Any]) -> None:
    """Promote the immutable pre-run record to a truthful post-run receipt."""
    root = root.resolve(strict=True)
    record_path = root / DIAGNOSTIC_CLOSEOUT_PATH
    if record_path.is_symlink() or not record_path.is_file():
        raise AdmissionRefused("diagnostic-runtime-closeout-path-unsafe")
    original = read_source_file(root, source_revision, DIAGNOSTIC_CLOSEOUT_PATH)
    current = read_limited(record_path, MAX_JSON_BYTES, "diagnostic-closeout")
    if sha256(current) != runtime_result["closeout_record_sha256"] or current != original:
        raise AdmissionRefused("diagnostic-runtime-closeout-changed-after-preflight")
    _validate_gbmicrotest_runtime_result([runtime_result], root=root,
                                         expected_source_revision=source_revision,
                                         require_evidence=True)
    record = _json_without_duplicates(current, "diagnostic-closeout")
    gbmicrotest = record.get("gbmicrotest")
    if (not isinstance(gbmicrotest, dict) or gbmicrotest.get("status") != "admitted-before-runtime"
            or gbmicrotest.get("accounting", {}).get("runtime_results") != []):
        raise AdmissionRefused("diagnostic-runtime-closeout-state-not-pending")
    passed = runtime_result["verdict"] == "pass"
    new_state = "executed" if passed else "runtime-failed"
    gbmicrotest["status"] = new_state
    gbmicrotest["cohort_status"] = new_state
    gbmicrotest["blocked_by"] = ([] if passed else ["selected-case-" + runtime_result["verdict"]])
    gbmicrotest["accounting"]["executed_names"] = [GBMICROTEST_SELECTED_CASE] if passed else []
    gbmicrotest["accounting"]["final_execution_accounting_complete"] = passed
    gbmicrotest["accounting"]["runtime_results"] = [runtime_result]
    runtime_status = "pass" if passed else runtime_result["verdict"]
    gbmicrotest["source_review"]["local_rom_review"]["runtime_status"] = runtime_status
    gbmicrotest["source_review"]["protocol"]["runtime_status"] = runtime_status
    updated = (json.dumps(record, indent=2) + "\n").encode("utf-8")
    temporary = record_path.with_name(record_path.name + ".runtime.tmp")
    if temporary.exists() or temporary.is_symlink():
        raise AdmissionRefused("diagnostic-runtime-closeout-temporary-path-exists")
    try:
        with temporary.open("xb") as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, record_path)
    except OSError as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise AdmissionRefused("diagnostic-runtime-closeout-write-failed:" + (error.strerror or "write")) from None


def check_diagnostic_closeout(root: pathlib.Path, source_revision: str, kind: str,
                              *, require_approved: bool = False) -> dict[str, Any]:
    """Read the immutable current record and its pinned T5 rights input."""
    if not HEX40.fullmatch(source_revision):
        raise AdmissionRefused("diagnostic-closeout-source-revision-invalid")
    root = root.resolve(strict=True)
    require_worktree_source_file(root, source_revision, ADMISSION_CHECKER_PATH,
                                 root / ADMISSION_CHECKER_PATH)
    require_worktree_source_file(root, source_revision, DIAGNOSTIC_CLOSEOUT_PATH,
                                 root / DIAGNOSTIC_CLOSEOUT_PATH)
    if kind in ("acid2", "all"):
        for relative in (ACID2_FIXTURE_MANIFEST, ACID2_FIXTURE_ADMISSION_PIN,
                         ACID2_FIXTURE_BUNDLE, ACID2_FIXTURE_NOTICE):
            require_worktree_source_file(root, source_revision, relative, root / relative)
    if kind in ("gbmicrotest", "all"):
        require_worktree_source_file(root, source_revision, GBMICROTEST_INVENTORY_PATH,
                                     root / GBMICROTEST_INVENTORY_PATH)
    record_raw = read_source_file(root, source_revision, DIAGNOSTIC_CLOSEOUT_PATH)
    record = _json_without_duplicates(record_raw, "diagnostic-closeout")
    rights_input = record.get("rights_input")
    if (not isinstance(rights_input, dict)
            or rights_input.get("commit") != DIAGNOSTIC_RIGHTS_REVISION):
        raise AdmissionRefused("diagnostic-closeout-input-identity-invalid")
    rights_raw = read_source_file(root, DIAGNOSTIC_RIGHTS_REVISION, CANDIDATE_CLOSEOUT_PATH)
    if len(rights_raw) != DIAGNOSTIC_RIGHTS_SIZE or sha256(rights_raw) != DIAGNOSTIC_RIGHTS_SHA256:
        raise AdmissionRefused("diagnostic-closeout-rights-input-digest-mismatch")
    rights_record = _json_without_duplicates(rights_raw, "diagnostic-rights-input")
    inventory = validate_gbmicrotest_inventory(root) if kind in ("gbmicrotest", "all") else None
    validated = validate_diagnostic_closeout_record(record, rights_record, kind, inventory)
    if require_approved and validated["_blockers"]:
        raise AdmissionRefused("scope-resolution-required: " + ",".join(validated["_blockers"]))
    if kind in ("acid2", "all"):
        acid2_bundle, acid2_manifest = validate_acid2_fixture(root, source_revision)
        validated["_acid2_bundle_content"] = acid2_bundle
        validated["_acid2_manifest"] = acid2_manifest
        _validate_acid2_runtime_evidence(root, validated["acid2"]["runtime"], source_revision)
    bundle = None
    if (kind in ("gbmicrotest", "all")
            and validated["gbmicrotest"].get("status") != "blocked-before-admission"):
        bundle = validate_gbmicrotest_fixture(root, source_revision)
    if kind in ("gbmicrotest", "all") and validated["gbmicrotest"].get("status") in ("executed", "runtime-failed"):
        _validate_gbmicrotest_runtime_result(validated["gbmicrotest"]["accounting"]["runtime_results"],
                                             root=root, expected_source_revision=source_revision,
                                             require_evidence=False)
    if kind in ("gbmicrotest", "all") and bundle is not None:
        validated["_gbmicrotest_bundle_content"] = bundle
    return validated


def _instruction_size(instruction: str) -> int:
    text = re.sub(r"\s+", " ", instruction.strip().upper())
    if text in {"DI", "XOR A", "LD (HL+), A", "DEC B", "DEC C", "LD B, B"}:
        return 1
    if (re.fullmatch(r"LDH \(0X[0-9A-F]{2}\), A", text)
            or re.fullmatch(r"LDH A, \(0X[0-9A-F]{2}\)", text)
            or re.fullmatch(r"LD [BC], 0X[0-9A-F]{2}", text)
            or re.fullmatch(r"LD A, 0X[0-9A-F]{2}", text)
            or re.fullmatch(r"CP 0X[0-9A-F]{2}", text)):
        return 2
    if re.fullmatch(r"LD HL, 0X[0-9A-F]{4}", text):
        return 3
    if re.fullmatch(r"LD \(0X[0-9A-F]{4}\), A", text):
        return 3
    if re.fullmatch(r"JR NZ, [A-Z_][A-Z0-9_]*", text):
        return 2
    raise ValueError(f"unsupported-control-instruction:{text[:64]}")


def assemble_control(source: bytes) -> bytes:
    if not isinstance(source, bytes) or not source or len(source) > MAX_SOURCE_BYTES:
        raise ValueError("control-source-size-invalid")
    try:
        text = source.decode("ascii", errors="strict")
    except UnicodeDecodeError:
        raise ValueError("control-source-encoding-invalid") from None
    rows: list[tuple[str | None, str]] = []
    labels: dict[str, int] = {}
    pc = 0x0100
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if ":" in line:
            label, remainder = line.split(":", 1)
            label = label.strip().upper()
            if not re.fullmatch(r"[A-Z_][A-Z0-9_]*", label) or label in labels:
                raise ValueError("control-label-invalid")
            labels[label] = pc
            line = remainder.strip()
            if not line:
                continue
        size = _instruction_size(line)
        rows.append((None, re.sub(r"\s+", " ", line.strip().upper())))
        pc += size
    if pc > 0x0134:
        raise ValueError("control-code-overlaps-header")
    code = bytearray()
    pc = 0x0100
    for _, text in rows:
        if text == "DI":
            data = bytes((0xF3,))
        elif text == "XOR A":
            data = bytes((0xAF,))
        elif text == "LD (HL+), A":
            data = bytes((0x22,))
        elif text == "DEC B":
            data = bytes((0x05,))
        elif text == "DEC C":
            data = bytes((0x0D,))
        elif text == "LD B, B":
            data = bytes((0x40,))
        elif match := re.fullmatch(r"LDH \(0X([0-9A-F]{2})\), A", text):
            data = bytes((0xE0, int(match.group(1), 16)))
        elif match := re.fullmatch(r"LDH A, \(0X([0-9A-F]{2})\)", text):
            data = bytes((0xF0, int(match.group(1), 16)))
        elif match := re.fullmatch(r"LD HL, 0X([0-9A-F]{4})", text):
            value = int(match.group(1), 16)
            data = bytes((0x21, value & 0xFF, value >> 8))
        elif match := re.fullmatch(r"LD ([BC]), 0X([0-9A-F]{2})", text):
            data = bytes((0x06 if match.group(1) == "B" else 0x0E, int(match.group(2), 16)))
        elif match := re.fullmatch(r"LD A, 0X([0-9A-F]{2})", text):
            data = bytes((0x3E, int(match.group(1), 16)))
        elif match := re.fullmatch(r"LD \(0X([0-9A-F]{4})\), A", text):
            value = int(match.group(1), 16)
            data = bytes((0xEA, value & 0xFF, value >> 8))
        elif match := re.fullmatch(r"CP 0X([0-9A-F]{2})", text):
            data = bytes((0xFE, int(match.group(1), 16)))
        elif match := re.fullmatch(r"JR NZ, ([A-Z_][A-Z0-9_]*)", text):
            if match.group(1) not in labels:
                raise ValueError("control-label-unknown")
            displacement = labels[match.group(1)] - (pc + 2)
            if not -128 <= displacement <= 127:
                raise ValueError("control-branch-out-of-range")
            data = bytes((0x20, displacement & 0xFF))
        else:
            raise ValueError(f"unsupported-control-instruction:{text[:64]}")
        code.extend(data)
        pc += len(data)
    if pc > 0x0134:
        raise ValueError("control-code-overlaps-header")
    return bytes(code)


def build_control_rom(source: bytes) -> bytes:
    code = assemble_control(source)
    if len(code) > 0x34:
        raise ValueError("control-code-overlaps-header")
    rom = bytearray(0x8000)
    rom[0x0100:0x0100 + len(code)] = code
    rom[0x0134:0x0143] = b"GBB22-SYNTHETIC"[:0x0F].ljust(0x0F, b"\x00")
    rom[0x0143] = 0
    rom[0x0147] = 0
    rom[0x0148] = 0
    rom[0x0149] = 0
    checksum = 0
    for value in rom[0x0134:0x014D]:
        checksum = (checksum - value - 1) & 0xFF
    rom[0x014D] = checksum
    return bytes(rom)


def expected_frame() -> list[tuple[int, int, int]]:
    """Independent analytical DMG frame: shade 0 everywhere, tile 1's first pixel at shade 1."""
    shade_colours = ((255, 255, 255), (170, 170, 170), (85, 85, 85), (0, 0, 0))
    pixels = [shade_colours[0]] * (160 * 144)
    pixels[24 * 160 + 16] = shade_colours[1]
    return pixels


def _records(paths: list[tuple[str, bytes]]) -> list[dict[str, Any]]:
    return [{"path": path, "size_bytes": len(data), "sha256": sha256(data)} for path, data in paths]


def _write_synthetic_admission_repo(root: pathlib.Path, source: bytes, rom: bytes,
                                    reference: bytes) -> tuple[pathlib.Path, dict[str, Any]]:
    _git(root, "init", "-q")
    _git(root, "symbolic-ref", "HEAD", "refs/heads/main")
    _git(root, "read-tree", "--empty")
    _git(root, "config", "user.name", "GabbaBoy Synthetic Control")
    _git(root, "config", "user.email", "synthetic-control@example.invalid")
    object_dir = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-path", "objects"],
                                cwd=ROOT, capture_output=True, check=True, timeout=30).stdout.rstrip(b"\r\n")
    alternate = root / ".git/objects/info/alternates"
    alternate.parent.mkdir(parents=True, exist_ok=True)
    alternate.write_bytes(object_dir + b"\n")

    license_bytes = subprocess.run(["git", "show", f"{BASELINE_COMMIT}:LICENSE"], cwd=ROOT,
                                   capture_output=True, check=True, timeout=30).stdout
    (root / "LICENSE").write_bytes(license_bytes)
    (root / "cmake").mkdir(parents=True, exist_ok=True)
    (root / "cmake/FixtureAdmissionPolicy.json").write_bytes(
        (ROOT / "cmake/FixtureAdmissionPolicy.json").read_bytes())
    fixture = root / "fixtures/synthetic"
    fixture.mkdir(parents=True, exist_ok=True)
    source_path = "fixtures/synthetic/control.asm"
    rom_path = "fixtures/synthetic/control.gb"
    reference_path = "fixtures/synthetic/control-reference.rgb"
    notice_path = "fixtures/synthetic/LICENSE.txt"
    notice = b"Original synthetic Phase 22 test control. No third-party fixture bytes.\n"
    for path, data in ((source_path, source), (rom_path, rom),
                       (reference_path, reference), (notice_path, notice)):
        target = root.joinpath(*path.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    source_revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                     capture_output=True, check=True, timeout=30).stdout.decode().strip()
    files = _records([(source_path, source), (rom_path, rom), (reference_path, reference),
                      (notice_path, notice)])
    code_paths = [source_path, rom_path, reference_path]
    components = {
        "code": {"presence": "present", "terms": "MIT project-authored synthetic control",
                 "evidence": {"path": source_path, "sha256": sha256(source)},
                 "covered_paths": code_paths, "scope": {"repository": True, "public_ci": True}},
        "art": {"presence": "absent", "reason": "synthetic flat-color pixels only"},
        "audio_driver": {"presence": "absent", "reason": "no audio component"},
        "build_inputs": {"presence": "absent", "reason": "stdlib emitter is recorded as build-only"},
        "notices": {"presence": "present", "terms": "original test-only notice",
                    "evidence": {"path": notice_path, "sha256": sha256(notice)},
                    "covered_paths": [notice_path], "scope": {"repository": True, "public_ci": True}},
    }
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "fixture_kind": "synthetic-test-only-diagnostic-control",
        "decision": {"status": "approved", "reviewer_role": "automated synthetic contract",
                     "rationale": "Test-only bytes validate admission plumbing, not third-party permission.",
                     "component_rationale": {"code": "Original project-authored control only.",
                                             "notices": "Original test notice only."}},
        "permissions": {"repository": True, "public_ci": True},
        "source": {"repository": "https://github.com/szTheory/gabbaboy", "revision": source_revision},
        "inputs": _records([(source_path, source), (rom_path, rom), (reference_path, reference)]),
        "files": files,
        "build": {"recipe": "bounded stdlib opcode emitter from control.asm", "tools": [
            {"name": "synthetic-control-emitter", "version": "1", "terms": "MIT project source",
             "source_repository": "https://github.com/szTheory/gabbaboy", "revision": source_revision,
             "disposition": "build_only", "component": None, "covered_paths": []}]},
        "components": components,
        "notices": {"local_path": notice_path, "sha256": sha256(notice),
                    "index_path": "THIRD_PARTY_NOTICES.md"},
    }
    manifest_path = fixture / "manifest.json"
    manifest_raw = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if len(manifest_raw) > MAX_JSON_BYTES:
        raise RuntimeError("synthetic-manifest-size")
    manifest_path.write_bytes(manifest_raw)
    index = ("### Manifest and notice digests\n\n"
             "| Fixture directory | `manifest.json` SHA-256 | `LICENSE.txt` SHA-256 |\n"
             "|---|---|---|\n"
             f"| `synthetic` | `{sha256(manifest_raw)}` | `{sha256(notice)}` |\n").encode("utf-8")
    (root / "THIRD_PARTY_NOTICES.md").write_bytes(index)
    _git(root, "add", "LICENSE", "cmake/FixtureAdmissionPolicy.json", "fixtures/synthetic",
         "THIRD_PARTY_NOTICES.md")
    tree = _git(root, "write-tree").decode("ascii").strip()
    commit = _git(root, "commit-tree", tree, "-p", BASELINE_COMMIT, "-m",
                  "synthetic: original Phase 22 admission control").decode("ascii").strip()
    _git(root, "update-ref", "refs/heads/main", commit)
    (fixture / "admission.commit").write_text(commit + "\n", encoding="ascii")
    return manifest_path, manifest


def check_synthetic_admission(root: pathlib.Path, manifest_path: pathlib.Path,
                              checker_path: pathlib.Path = PHASE20) -> tuple[int, bytes]:
    relative = manifest_path.relative_to(root).as_posix()
    code, stdout, stderr = _bounded_run([sys.executable, "-I", str(checker_path), "--check-manifest",
                                         relative, "--repo-root", str(root)], cwd=root)
    return code, stdout + stderr


def require_candidate_rights(source_root: pathlib.Path, source_revision: str) -> None:
    """Use the immutable candidate checker to stop diagnostic admission on unresolved rights."""
    checker = source_root / CANDIDATE_CHECKER_PATH
    for relative, path in ((CANDIDATE_CHECKER_PATH, checker),
                           (CANDIDATE_CLOSEOUT_PATH, source_root / CANDIDATE_CLOSEOUT_PATH)):
        require_worktree_source_file(source_root, source_revision, relative, path)
    code, stdout, stderr = _bounded_run(
        [sys.executable, "-I", str(checker), "--check-closeout", "--closeout-stage", "games",
         "--require-satisfied", "--repo-root", str(source_root), "--source-revision", source_revision],
        cwd=source_root,
    )
    output = (stderr + stdout).decode("utf-8", errors="replace").strip()
    if code == 0:
        return
    if code == 1 and output.startswith("candidate-closeout-rights-unresolved:"):
        details = output.partition(":")[2].strip()
        raise AdmissionRefused(f"candidate-rights-unresolved: {details}")
    raise AdmissionRefused(f"candidate-rights-check-failed: {output[:384] or 'no checker output'}")


def _commit_test_admission_source(root: pathlib.Path, *, inventory: bool = False) -> str:
    """Create a local immutable source fixture for admission-gate controls."""
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "GabbaBoy Admission Control")
    _git(root, "config", "user.email", "admission-control@example.invalid")
    checker = root / ADMISSION_CHECKER_PATH
    checker.parent.mkdir(parents=True, exist_ok=True)
    checker.write_bytes(pathlib.Path(__file__).read_bytes())
    phase20_checker = root / PHASE20_CHECKER_PATH
    phase20_checker.parent.mkdir(parents=True, exist_ok=True)
    phase20_checker.write_bytes(PHASE20.read_bytes())
    phase20_policy = root / PHASE20_POLICY_PATH
    phase20_policy.parent.mkdir(parents=True, exist_ok=True)
    phase20_policy.write_bytes((ROOT / PHASE20_POLICY_PATH).read_bytes())
    for relative in CANDIDATE_CONTRACT_PATHS:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / relative).read_bytes())
    files = [ADMISSION_CHECKER_PATH, "tests/external/diagnostic-assessment.json"]
    files.extend((PHASE20_CHECKER_PATH, PHASE20_POLICY_PATH))
    files.extend(CANDIDATE_CONTRACT_PATHS)
    if inventory:
        files.append("tests/external/gbmicrotest-inventory.json")
    _git(root, "add", *files)
    _git(root, "commit", "-qm", "synthetic: immutable admission source")
    return _git(root, "rev-parse", "HEAD").decode("ascii").strip()


def require_approved(root: pathlib.Path, source_revision: str,
                     manifest_path: pathlib.Path | None = None, *,
                     source_repo_root: pathlib.Path | None = None,
                     source_paths: tuple[tuple[str, pathlib.Path], ...] = (),
                     candidate_rights: bool = False) -> dict:
    """Require committed evidence and policy bytes before any real fixture can be used."""
    if not re.fullmatch(r"[0-9a-f]{40}", source_revision):
        raise AdmissionRefused("source-revision-invalid")
    try:
        root = root.resolve(strict=True)
        source_root = (source_repo_root or root).resolve(strict=True)
    except OSError:
        raise AdmissionRefused("scope-resolution-required: source repository unavailable") from None
    require_worktree_source_file(
        source_root, source_revision, ADMISSION_CHECKER_PATH, pathlib.Path(__file__))
    for relative, path in source_paths:
        require_worktree_source_file(source_root, source_revision, relative, path)
    # The Phase 20 checker is the policy implementation invoked for the synthetic
    # manifest gate. Its product policy file is another executable input to that
    # decision, so neither may come from an uncommitted worktree edit.
    require_worktree_source_file(source_root, source_revision, PHASE20_CHECKER_PATH,
                                 source_root / PHASE20_CHECKER_PATH)
    require_worktree_source_file(source_root, source_revision, PHASE20_POLICY_PATH,
                                 source_root / PHASE20_POLICY_PATH)
    if candidate_rights:
        require_candidate_rights(source_root, source_revision)
    if manifest_path is not None:
        relative = repository_relative_path(source_root, manifest_path)
        require_worktree_source_file(source_root, source_revision, relative, manifest_path)

    assessment_bytes = read_source_file(
        source_root, source_revision, "tests/external/diagnostic-assessment.json")
    record = _json_without_duplicates(assessment_bytes, "diagnostic-assessment")
    if record.get("origin") in ("synthetic", "test-only") \
            or str(record.get("fixture_kind", "")).startswith("synthetic"):
        raise AdmissionRefused("synthetic-only-record-refused")
    declared_gates = record.get("required_gates", record.get("gates", []))
    if isinstance(declared_gates, list):
        unresolved_ids = [str(gate.get("id", "unknown")) for gate in declared_gates
                          if isinstance(gate, dict) and gate.get("status") != "supported"]
        if unresolved_ids:
            raise AdmissionRefused("scope-resolution-required: unresolved gates=" + ",".join(unresolved_ids))
    with tempfile.TemporaryDirectory(prefix="gbb-immutable-admission-") as name:
        evidence_root = pathlib.Path(name)
        for relative in ("tests/external/diagnostic-assessment.json",
                         "tests/external/gbmicrotest-inventory.json"):
            target = evidence_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(read_source_file(source_root, source_revision, relative))
        record, inventory = validate_assessment(evidence_root)
    unresolved_ids = [gate["id"] for gate in record["required_gates"] if gate["status"] != "supported"]
    unresolved_ids.extend(component["id"] for component in record["components"]
                          if component["status"] == "unresolved")
    if record.get("status") != "approved" or unresolved_ids:
        detail = ",".join(unresolved_ids) if unresolved_ids else "assessment-not-approved"
        raise AdmissionRefused(f"scope-resolution-required: {detail}")
    for case in inventory["cases"]:
        for identity, label in ((case["source"], "source"), (case["prebuilt_rom"], "rom")):
            if not isinstance(identity.get("sha256"), str) or not HEX64.fullmatch(identity["sha256"]):
                raise AdmissionRefused(f"scope-resolution-required: {label} sha256 not independently recorded for {case['name']}")
    if manifest_path is not None:
        if not manifest_path.is_file():
            raise AdmissionRefused("diagnostic-manifest-missing")
        code, output = check_synthetic_admission(
            root, manifest_path, source_root / PHASE20_CHECKER_PATH)
        if code or b"PASS: fixture admission" not in output:
            raise AdmissionRefused("fixture-admission-refused")
    return record


def _write_package_manifest(path: pathlib.Path, rom: bytes) -> None:
    record = {"fixtures": [{"size_bytes": len(rom), "sha256": sha256(rom)}]}
    path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")


def _scan_product_tree(tree: pathlib.Path, manifest: pathlib.Path) -> tuple[int, bytes]:
    cmake = shutil.which("cmake")
    if not cmake:
        raise RuntimeError("cmake-unavailable")
    code, stdout, stderr = _bounded_run([cmake, f"-DGBB_SCAN_DIR={tree}",
                                         f"-DGBB_FORBIDDEN_MANIFEST={manifest}",
                                         "-DGBB_FORBIDDEN_LABEL=synthetic-rom",
                                         "-P", str(SCANNER)], cwd=ROOT, timeout=15)
    return code, stdout + stderr


def _package_controls(rom: bytes, temp: pathlib.Path) -> tuple[bool, bool]:
    manifest = temp / "package-identities.json"
    _write_package_manifest(manifest, rom)
    clean = temp / "package-clean"
    clean.mkdir()
    (clean / "README.txt").write_bytes(b"synthetic clean package tree\n")
    clean_code, clean_output = _scan_product_tree(clean, manifest)
    if clean_code or b"synthetic-rom absent" not in clean_output:
        raise RuntimeError("synthetic-package-positive-failed")
    infected = temp / "package-infected"
    infected.mkdir()
    (infected / "renamed-data.bin").write_bytes(rom)
    bad_code, bad_output = _scan_product_tree(infected, manifest)
    if bad_code == 0 or b"synthetic-rom-installed: renamed-data.bin" not in bad_output:
        raise RuntimeError("synthetic-package-negative-control-failed")
    return True, True


def run_tracer(runner_path: pathlib.Path) -> int:
    if not runner_path.is_file() or runner_path.is_symlink():
        print("acid2 tracer refused: runner-path-invalid")
        return 2
    try:
        runner_bytes = read_limited(runner_path, 512 * 1024 * 1024, "runner")
        source = read_limited(CONTROL_SOURCE, MAX_SOURCE_BYTES, "source")
    except AdmissionRefused as error:
        print(f"acid2 tracer refused: {error}")
        return 2
    if not runner_bytes:
        print("acid2 tracer refused: runner-size-invalid")
        return 2
    mask_tool = _load_module("phase22_acid2_masks", ROOT / "tests/scripts/verify-acid2-masks.py")
    acid2 = _load_module("phase22_acid2_local", ACID2_TOOL)
    rom = build_control_rom(source)
    expected = expected_frame()
    reference = bytes(channel for pixel in expected for channel in pixel)
    cells = mask_tool.source_cells(source)
    if tuple(cells) != SOURCE_CELL_ALLOWLIST:
        print("acid2 tracer refused: source-cell-allowlist-mismatch")
        return 2
    mask = mask_tool.build_mask(cells)
    overlay = mask_tool.overlay_png(expected, mask)
    try:
        identities = composition_identity_bundle(source, rom, reference, cells, mask, overlay)
    except AdmissionRefused as error:
        print(f"acid2 tracer refused: {error}")
        return 2
    with tempfile.TemporaryDirectory(prefix="gbb-phase22-synthetic-") as name:
        temp = pathlib.Path(name)
        admission_root = temp / "admission-repo"
        admission_root.mkdir()
        admission_manifest, _record = _write_synthetic_admission_repo(admission_root, source, rom, reference)
        admission_code, admission_output = check_synthetic_admission(admission_root, admission_manifest)
        if admission_code != 0 or b"PASS: fixture admission" not in admission_output:
            print("acid2 tracer error: synthetic admission failed")
            return 3
        try:
            unapproved_code = _unapproved_input_control(acid2, temp, rom, expected)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
            print(f"acid2 tracer error: approval stop control failed ({error.__class__.__name__})")
            return 3
        if unapproved_code != 2:
            print("acid2 tracer error: unapproved input was not refused before runner invocation")
            return 3
        try:
            ppm = acid2.run_core(runner_path, {"rom_sha256": sha256(rom), "rom_size": len(rom),
                                                "runner_model": "dmg-cpu-b"}, rom,
                                CONTROL_BUDGET_HALF_DOTS, timeout=30)
            actual = acid2.read_ppm(ppm)
            mask_tool.validate_mask(mask, cells)
            compare_code, compare_result = mask_tool.compare_masked(actual, expected, mask, cells)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
            print(f"acid2 tracer error: runner/comparison failed ({error.__class__.__name__})")
            return 3
        clean_pass, inserted_refused = _package_controls(rom, temp)
        if compare_code != 0 or not clean_pass or not inserted_refused:
            print(f"acid2 tracer fail: {compare_result}")
            return 1
        receipt = {
            "schema_version": 1,
            "origin": "synthetic-test-only",
            "evidence_class": "controlled-composition synthetic harness",
            "source": {"path": "tests/acid2/control.asm", "sha256": sha256(source)},
            "rom": {"size_bytes": len(rom), "sha256": sha256(rom)},
            "reference": {"kind": "analytically-specified RGB888", "sha256": sha256(reference)},
            "runner": {"size_bytes": len(runner_bytes), "sha256": sha256(runner_bytes),
                       "model": "dmg-cpu-b"},
            "budget_half_dots": CONTROL_BUDGET_HALF_DOTS,
            "mask": {"cells": [{"column": column, "row": row} for column, row in cells],
                     "sha256": sha256(mask), "overlay_sha256": sha256(overlay)},
            "identities": identities,
            "expected_frame_sha256": sha256(reference),
            "observed_frame_sha256": sha256(bytes(channel for pixel in actual for channel in pixel)),
            "comparison": compare_result,
            "admission": {"checker": "Phase 20 verify-fixture-admission.py --check-manifest",
                          "fixture_kind": "synthetic-test-only-diagnostic-control"},
            "product_scan": {"clean_tree_pass": clean_pass, "renamed_rom_refused": inserted_refused},
        }
        receipt_path = temp / "receipt.json"
        receipt_bytes = (json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n").encode()
        if len(receipt_bytes) > 32 * 1024:
            print("acid2 tracer error: receipt-size-limit")
            return 3
        receipt_path.write_bytes(receipt_bytes)
        checked_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        try:
            validate_identity_bundle(identities, checked_receipt.get("identities"))
        except AdmissionRefused:
            print("acid2 tracer error: receipt-identity-mismatch")
            return 3
        if (checked_receipt.get("origin") != "synthetic-test-only"
                or checked_receipt.get("rom", {}).get("sha256") != sha256(rom)
                or checked_receipt.get("runner", {}).get("sha256") != sha256(runner_bytes)
                or checked_receipt.get("mask", {}).get("sha256") != sha256(mask)):
            print("acid2 tracer error: receipt-identity-mismatch")
            return 3
    print(f"acid2 tracer pass origin=synthetic-only profile=dmg-cpu-b "
          f"rom_sha256={sha256(rom)} mask_sha256={sha256(mask)}")
    return 0


def _unapproved_input_control(acid2, temp: pathlib.Path, rom: bytes,
                              expected: list[tuple[int, int, int]]) -> int:
    rom_path = temp / "unapproved-synthetic.gb"
    reference_path = temp / "unapproved-synthetic.png"
    manifest_path = temp / "unapproved-manifest.json"
    rom_path.write_bytes(rom)
    reference = acid2.encode_png_rgb(expected)
    reference_path.write_bytes(reference)
    manifest = {"ldbb_budget_half_dots": CONTROL_BUDGET_HALF_DOTS,
                "kinds": {"cgb-acid2": {"rom_sha256": sha256(rom),
                                          "reference_sha256": sha256(reference),
                                          "runner_model": "dmg-cpu-b", "rom_size": len(rom)}}}
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    invoked = False

    def forbidden_runner(*_args, **_kwargs):
        nonlocal invoked
        invoked = True
        raise AssertionError("runner-invoked-before-admission")

    original = acid2.run_core
    acid2.run_core = forbidden_runner
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = acid2.main(["--rom", str(rom_path), "--reference", str(reference_path),
                                 "--runner", str(temp / "must-not-run"), "--rom-kind", "cgb-acid2",
                                 "--manifest", str(manifest_path)])
    finally:
        acid2.run_core = original
    if result != 2 or invoked or "scope-resolution-required" not in output.getvalue():
        raise RuntimeError("unapproved-input-did-not-stop-before-runner")
    return result


class AdmissionContractTests(unittest.TestCase):
    def test_original_synthetic_record_passes_real_phase20_cli(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gbb-admission-positive-") as name:
            root = pathlib.Path(name)
            source = CONTROL_SOURCE.read_bytes()
            rom = build_control_rom(source)
            reference = bytes(channel for pixel in expected_frame() for channel in pixel)
            manifest, _record = _write_synthetic_admission_repo(root, source, rom, reference)
            code, output = check_synthetic_admission(root, manifest)
            self.assertEqual(code, 0, output.decode("utf-8", "replace"))
            self.assertIn(b"PASS: fixture admission", output)

    def test_synthetic_origin_never_satisfies_real_approval(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gbb-admission-gate-") as name:
            root = pathlib.Path(name)
            assessment = root / "tests/external/diagnostic-assessment.json"
            assessment.parent.mkdir(parents=True)
            assessment.write_text(json.dumps({"origin": "test-only", "status": "approved",
                                              "source_revision": "a" * 40}), encoding="utf-8")
            revision = _commit_test_admission_source(root)
            with self.assertRaisesRegex(AdmissionRefused, "synthetic-only-record-refused"):
                require_approved(root, revision)

    def test_malformed_approval_json_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gbb-admission-json-") as name:
            root = pathlib.Path(name)
            assessment = root / "tests/external/diagnostic-assessment.json"
            assessment.parent.mkdir(parents=True)
            assessment.write_bytes(b'{"origin":')
            revision = _commit_test_admission_source(root)
            with self.assertRaisesRegex(AdmissionRefused, "diagnostic-assessment-invalid"):
                require_approved(root, revision)


class AdmissionControlTests(unittest.TestCase):
    runner_path: pathlib.Path | None = None

    def test_compiled_runner_shared_diagnostic_positive_and_negative(self) -> None:
        if self.runner_path is None:
            self.skipTest("no compiled runner supplied")
        if not self.runner_path.is_file():
            self.fail("compiled diagnostic runner is missing")

        def run_case(actual: int, expected: int, terminal: int) -> subprocess.CompletedProcess[bytes]:
            with tempfile.TemporaryDirectory(prefix="gbb-shared-diagnostic-control-") as name:
                root = pathlib.Path(name)
                rom = bytearray(32768)
                rom[0x100:0x104] = bytes((0x00, 0xC3, 0x50, 0x01))  # entry: NOP; JP $0150
                rom[0x150:0x15E] = bytes((
                    0x3E, actual, 0xE0, 0x80,  # FF80 actual
                    0x3E, expected, 0xE0, 0x81,  # FF81 expected
                    0x3E, terminal, 0xE0, 0x82,  # FF82 terminal
                    0x18, 0xFE,  # bounded post-terminal loop
                ))
                checksum = 0
                for offset in range(0x134, 0x14D):
                    checksum = (checksum - rom[offset] - 1) & 0xFF
                rom[0x14D] = checksum
                rom_path = root / "synthetic.gb"
                rom_path.write_bytes(rom)
                case = (
                    "id=synthetic rom=synthetic.gb rom_sha256=" + sha256(rom) +
                    " rom_size=32768 oracle=diagnostic-shared-ff80-ff82 diagnostic_expected=00"
                    " budget_half_dots=1024 instruction_limit=64 event_limit=512 model_pass=dmg-cpu-b\n"
                )
                (root / "cases.txt").write_text(case, encoding="ascii")
                return subprocess.run(
                    [str(self.runner_path), "--acceptance", "cases.txt", "--case", "synthetic"],
                    cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5, check=False)

        passed = run_case(0, 0, 1)
        self.assertEqual(passed.returncode, 0, passed.stdout.decode("utf-8", "replace"))
        self.assertIn(b"status=pass", passed.stdout)
        failed = run_case(1, 0, 255)
        self.assertEqual(failed.returncode, 1, failed.stdout.decode("utf-8", "replace"))
        self.assertIn(b"reason=observed-mismatch", failed.stdout)

    def _diagnostic_closeout_inputs(self) -> tuple[dict[str, Any], dict[str, Any]]:
        record = _json_without_duplicates(
            (ROOT / DIAGNOSTIC_CLOSEOUT_PATH).read_bytes(), "diagnostic-closeout")
        # Admission mutation controls always start from the pre-runtime state. The
        # committed closeout may carry truthful Stage A and selected-case receipts.
        acid2 = record.get("acid2")
        if isinstance(acid2, dict) and acid2.get("status") in ("executed", "runtime-failed"):
            acid2["status"] = "admitted-before-runtime"
            acid2["runtime"] = {
                "status": "pending", "source_revision": None,
                "closeout_record_sha256": None,
                "fixture_admission_commit": ACID2_FIXTURE_ADMISSION_COMMIT,
                "manifest_sha256": ACID2_FIXTURE_MANIFEST_SHA256,
                "bundle_sha256": ACID2_FIXTURE_BUNDLE_SHA256,
                "runner_sha256": None, "qualification_sha256": None,
                "evidence_path": None, "evidence_sha256": None, "comparisons": [],
            }
        if isinstance(record.get("gbmicrotest"), dict):
            record["status"] = "admitted-before-runtime"
        gbmicrotest = record.get("gbmicrotest")
        if isinstance(gbmicrotest, dict) and gbmicrotest.get("status") in ("executed", "runtime-failed"):
            gbmicrotest["status"] = "admitted-before-runtime"
            gbmicrotest["cohort_status"] = "admitted-before-runtime"
            gbmicrotest["blocked_by"] = []
            accounting = gbmicrotest.get("accounting")
            if isinstance(accounting, dict):
                accounting["executed_names"] = []
                accounting["runtime_results"] = []
                accounting["final_execution_accounting_complete"] = False
            source_review = gbmicrotest.get("source_review")
            if isinstance(source_review, dict):
                local_review = source_review.get("local_rom_review")
                if isinstance(local_review, dict):
                    local_review["runtime_status"] = "pending"
                protocol = source_review.get("protocol")
                if isinstance(protocol, dict):
                    protocol["runtime_status"] = "pending"
        rights_raw = _git(ROOT, "show", f"{DIAGNOSTIC_RIGHTS_REVISION}:{CANDIDATE_CLOSEOUT_PATH}")
        return record, _json_without_duplicates(rights_raw, "diagnostic-rights-input")

    def test_acid2_snapshot_admits_two_real_derivatives_but_keeps_font_excluded(self) -> None:
        record, rights = self._diagnostic_closeout_inputs()
        validated = validate_diagnostic_closeout_record(record, rights, "acid2")
        self.assertEqual(validated["status"], "admitted-before-runtime")
        self.assertEqual(validated["_blockers"], [])
        self.assertEqual(validated["acid2"]["font_data"], "excluded-by-design")
        self.assertEqual([case["derivative"]["status"] for case in validated["acid2"]["cases"]],
                         ["admitted", "admitted"])
        self.assertEqual([case["model_scope"]["runner_model"] for case in validated["acid2"]["cases"]],
                         ["dmg-cpu-b", "cgb-cpu-e"])

    def test_acid2_gate_refuses_a_synthetic_derivative_claim(self) -> None:
        record, rights = self._diagnostic_closeout_inputs()
        record["acid2"]["cases"][0]["derivative"] = {
            "status": "created", "path": "fixtures/acid2/dmg.gb", "sha256": "a" * 64}
        with self.assertRaisesRegex(AdmissionRefused, "diagnostic-closeout-acid2-case-mutated:dmg-acid2-v1.0"):
            validate_diagnostic_closeout_record(record, rights, "acid2")

    def test_acid2_gate_refuses_a_mutated_source_rights_outcome(self) -> None:
        record, rights = self._diagnostic_closeout_inputs()
        source = _diagnostic_source_by_id(rights, "dmg-acid2-v1.0")
        component = _diagnostic_component(source, "footer-and-reference-images")
        component["outcome"] = "unresolved"
        with self.assertRaisesRegex(AdmissionRefused, "diagnostic-closeout-rights-mismatch:dmg-acid2-v1.0"):
            validate_diagnostic_closeout_record(record, rights, "acid2")

    def test_acid2_runtime_receipt_requires_all_three_source_pinned_profiles(self) -> None:
        record, _rights = self._diagnostic_closeout_inputs()
        runtime = record["acid2"]["runtime"]
        runtime.update({
            "status": "pass", "source_revision": "a" * 40,
            "closeout_record_sha256": "b" * 64, "runner_sha256": "c" * 64,
            "qualification_sha256": "d" * 64, "evidence_path": DIAGNOSTIC_RUNTIME_PREFLIGHT_PATH,
            "evidence_sha256": "e" * 64,
        })
        runtime["comparisons"] = []
        with self.assertRaisesRegex(AdmissionRefused, "diagnostic-closeout-acid2-comparison-set-invalid"):
            _validate_acid2_runtime_result(runtime)

    def test_gbmicrotest_accounts_for_one_admitted_case_and_512_exclusions(self) -> None:
        record, rights = self._diagnostic_closeout_inputs()
        inventory = validate_gbmicrotest_inventory(ROOT)
        validated = validate_diagnostic_closeout_record(record, rights, "gbmicrotest", inventory)
        accounting = validated["gbmicrotest"]["accounting"]
        self.assertEqual(accounting["roster_count"], GBMICROTEST_CASE_COUNT)
        self.assertTrue(accounting["roster_accounting_complete"])
        self.assertEqual(accounting["admitted_eligible_names"], [GBMICROTEST_SELECTED_CASE])
        self.assertEqual(accounting["executed_names"], [])
        self.assertEqual(accounting["blocked_candidate_names"], [])
        self.assertEqual(len(accounting["excluded_names"]), GBMICROTEST_CASE_COUNT - 1)
        self.assertFalse(accounting["final_execution_accounting_complete"])
        self.assertEqual(validated["_blockers"], [])
        self.assertEqual(validated["gbmicrotest"]["status"], "admitted-before-runtime")
        review = validated["gbmicrotest"]["source_review"]
        self.assertEqual(review["model_applicability"]["status"], "supported")
        self.assertEqual(review["model_applicability"]["hardware_applicability"],
                         "not-established; no hardware or DMG-CPU-08 claim")
        selected = next(item for item in validated["gbmicrotest"]["cases"]
                        if item["name"] == GBMICROTEST_SELECTED_CASE)
        self.assertEqual(selected["prebuilt_rom"]["sha256"], GBMICROTEST_SELECTED_ROM_SHA256)
        self.assertEqual(selected["disposition"]["status"], "eligible-for-one-case-cohort")
        self.assertEqual(selected["derivative"]["sha256"], GBMICROTEST_SELECTED_DERIVATIVE_SHA256)
        self.assertEqual(review["output_scope"]["status"], "supported-bounded-selected-derivative")
        self.assertEqual(review["output_scope"]["rights_evidence"]["issue"], GBMICROTEST_LICENSE_ISSUE)
        self.assertEqual(review["output_scope"]["rights_evidence"]["license_commit"], GBMICROTEST_LICENSE_COMMIT)

    def test_gbmicrotest_output_scope_binds_exact_issue_and_license_commit(self) -> None:
        inventory = validate_gbmicrotest_inventory(ROOT)
        mutations = (
            ("issue.comment_id", lambda scope: scope["rights_evidence"]["issue"].__setitem__("comment_id", 2080090498)),
            ("issue.comment_author", lambda scope: scope["rights_evidence"]["issue"].__setitem__("comment_author", "other")),
            ("issue.comment_body", lambda scope: scope["rights_evidence"]["issue"].__setitem__("comment_body", "Unknown")),
            ("issue.url", lambda scope: scope["rights_evidence"]["issue"].__setitem__("comment_url", "https://example.invalid/")),
            ("commit.subject", lambda scope: scope["rights_evidence"]["license_commit"].__setitem__("subject", "Other")),
            ("commit.paths", lambda scope: scope["rights_evidence"]["license_commit"].__setitem__("changed_paths", ["LICENSE", "README.md"])),
            ("commit.sha", lambda scope: scope["rights_evidence"]["license_commit"].__setitem__("sha", "a" * 40)),
        )
        for label, mutate in mutations:
            record, rights = self._diagnostic_closeout_inputs()
            mutate(record["gbmicrotest"]["source_review"]["output_scope"])
            with self.subTest(evidence=label), self.assertRaisesRegex(
                    AdmissionRefused, "diagnostic-closeout-gbmicrotest-source-review-mutated"):
                validate_diagnostic_closeout_record(record, rights, "gbmicrotest", inventory)

    def test_gbmicrotest_local_derivative_digest_and_offset_allowlist_are_bound(self) -> None:
        inventory = validate_gbmicrotest_inventory(ROOT)
        for field, value in (
                ("sha256", "a" * 64),
                ("all_changed_offsets_allowlisted", False)):
            record, rights = self._diagnostic_closeout_inputs()
            review = record["gbmicrotest"]["source_review"]["local_rom_review"]
            if field == "sha256":
                review["derivative"][field] = value
            else:
                review["transform"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(
                    AdmissionRefused, "diagnostic-closeout-gbmicrotest-source-review-mutated"):
                validate_diagnostic_closeout_record(record, rights, "gbmicrotest", inventory)

    def test_gbmicrotest_output_scope_cannot_be_promoted_by_root_mit_label(self) -> None:
        record, rights = self._diagnostic_closeout_inputs()
        inventory = validate_gbmicrotest_inventory(ROOT)
        record["gbmicrotest"]["source_review"]["output_scope"]["status"] = "supported"
        with self.assertRaisesRegex(AdmissionRefused, "diagnostic-closeout-gbmicrotest-source-review-mutated"):
            validate_diagnostic_closeout_record(record, rights, "gbmicrotest", inventory)

    def test_gbmicrotest_bounded_output_scope_cannot_expand_beyond_selected_derivative(self) -> None:
        inventory = validate_gbmicrotest_inventory(ROOT)
        for field, value in (("scope_limit", "All 513 ROMs are permitted."),
                             ("references", ["https://opensource.org/license/mit"]),
                             ("status", "supported")):
            record, rights = self._diagnostic_closeout_inputs()
            record["gbmicrotest"]["source_review"]["output_scope"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(
                    AdmissionRefused, "diagnostic-closeout-gbmicrotest-source-review-mutated"):
                validate_diagnostic_closeout_record(record, rights, "gbmicrotest", inventory)

    def test_gbmicrotest_runtime_binding_refuses_wrong_candidate_or_nonfinite_time(self) -> None:
        valid = {
            "case": GBMICROTEST_SELECTED_CASE, "runner_case_id": "div-inc-a",
            "source_revision": "a" * 40, "closeout_record_sha256": "b" * 64,
            "fixture_admission_commit": GBMICROTEST_ADMISSION_COMMIT,
            "manifest_sha256": GBMICROTEST_MANIFEST_SHA256,
            "source_sha256": GBMICROTEST_SELECTED_SOURCE_SHA256,
            "original_rom_sha256": GBMICROTEST_SELECTED_ROM_SHA256,
            "derivative_sha256": GBMICROTEST_SELECTED_DERIVATIVE_SHA256,
            "model": "dmg-cpu-b", "verdict": "pass", "actual": "00", "expected": "00",
            "terminal": "01", "instruction_count": 12, "event_count": 64, "end_half_dots": 512,
            "elapsed_seconds": 0.1, "runner_sha256": "c" * 64,
            "qualification_sha256": "d" * 64,
            "runner_exit_code": 0, "reason": None,
            "evidence_path": "build/phase24/diagnostic-runtime-preflight.json",
            "evidence_sha256": "e" * 64,
        }
        with self.assertRaisesRegex(AdmissionRefused, "runtime-source-revision-mismatch"):
            _validate_gbmicrotest_runtime_result([valid], expected_source_revision="f" * 40)
        mutant = dict(valid, elapsed_seconds=float("nan"))
        with self.assertRaisesRegex(AdmissionRefused, "runtime-result-mismatch"):
            _validate_gbmicrotest_runtime_result([mutant])
        mismatch = dict(valid, verdict="source-failure", runner_exit_code=1,
                        reason="observed-mismatch", actual="ff", expected="00", terminal="ff")
        self.assertEqual(_validate_gbmicrotest_runtime_result([mismatch])["verdict"], "source-failure")
        bounded = dict(valid, verdict="bounded-failure", runner_exit_code=3,
                       reason="guest-deadline", actual=None, expected=None, terminal=None,
                       event_count=0, end_half_dots=8192)
        self.assertEqual(_validate_gbmicrotest_runtime_result([bounded])["verdict"], "bounded-failure")

    def test_gbmicrotest_software_scope_does_not_promote_hardware_or_cgb_claims(self) -> None:
        inventory = validate_gbmicrotest_inventory(ROOT)
        for field, value in (("hardware_applicability", "supported"),
                             ("cgb_applicability", "supported")):
            record, rights = self._diagnostic_closeout_inputs()
            record["gbmicrotest"]["source_review"]["model_applicability"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(
                    AdmissionRefused, "diagnostic-closeout-gbmicrotest-source-review-mutated"):
                validate_diagnostic_closeout_record(record, rights, "gbmicrotest", inventory)

    def test_gbmicrotest_accounting_refuses_candidate_promotion(self) -> None:
        record, rights = self._diagnostic_closeout_inputs()
        inventory = validate_gbmicrotest_inventory(ROOT)
        accounting = record["gbmicrotest"]["accounting"]
        accounting["admitted_eligible_names"] = [GBMICROTEST_SELECTED_CASE]
        accounting["executed_names"] = [GBMICROTEST_SELECTED_CASE]
        accounting["blocked_candidate_names"] = []
        with self.assertRaisesRegex(AdmissionRefused, "diagnostic-closeout-gbmicrotest-accounting-mutated"):
            validate_diagnostic_closeout_record(record, rights, "gbmicrotest", inventory)

    def test_gbmicrotest_roster_refuses_a_substituted_rom_digest(self) -> None:
        record, rights = self._diagnostic_closeout_inputs()
        inventory = validate_gbmicrotest_inventory(ROOT)
        row = next(item for item in record["gbmicrotest"]["cases"]
                   if item["name"] == GBMICROTEST_SELECTED_CASE)
        row["prebuilt_rom"]["sha256"] = "a" * 64
        with self.assertRaisesRegex(AdmissionRefused, "diagnostic-closeout-gbmicrotest-case-accounting-mutated"):
            validate_diagnostic_closeout_record(record, rights, "gbmicrotest", inventory)

    def test_gbmicrotest_rights_mutant_does_not_approve_generated_roms(self) -> None:
        record, rights = self._diagnostic_closeout_inputs()
        inventory = validate_gbmicrotest_inventory(ROOT)
        source = _diagnostic_source_by_id(rights, "gbmicrotest-463eb6b")
        _diagnostic_component(source, "prebuilt-roms")["outcome"] = "supported"
        with self.assertRaisesRegex(AdmissionRefused, "diagnostic-closeout-gbmicrotest-rights-mismatch"):
            validate_diagnostic_closeout_record(record, rights, "gbmicrotest", inventory)

    def test_unresolved_candidate_component_reaches_intended_admission_refusal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gbb-candidate-rights-admission-") as name:
            root = pathlib.Path(name)
            self._copy_review_records(root)
            revision = _commit_test_admission_source(root, inventory=True)
            with self.assertRaisesRegex(AdmissionRefused, "candidate-rights-unresolved:") as caught:
                require_approved(root, revision, candidate_rights=True)
            detail = str(caught.exception)
            self.assertIn("potion-panic-gbcompo25/converter-code", detail)
            self.assertIn("ucity-1.3/hardware-inc", detail)

    def test_each_mutated_identity_refuses(self) -> None:
        expected = {name: sha256(("expected:" + name).encode("ascii")) for name in IDENTITY_FIELDS}
        validate_identity_bundle(expected, dict(expected))
        for name in IDENTITY_FIELDS:
            with self.subTest(identity=name):
                candidate = dict(expected)
                candidate[name] = sha256(("mutated:" + name).encode("ascii"))
                with self.assertRaisesRegex(AdmissionRefused, f"identity-mismatch:{name}"):
                    validate_identity_bundle(expected, candidate)

    def test_identity_bundle_rejects_missing_extra_and_malformed_fields(self) -> None:
        expected = {name: sha256(("expected:" + name).encode("ascii")) for name in IDENTITY_FIELDS}
        missing = dict(expected)
        del missing["overlay"]
        with self.assertRaisesRegex(AdmissionRefused, "identity-field-set-invalid"):
            validate_identity_bundle(expected, missing)
        extra = dict(expected, extra=sha256(b"extra"))
        with self.assertRaisesRegex(AdmissionRefused, "identity-field-set-invalid"):
            validate_identity_bundle(expected, extra)
        malformed = dict(expected, mask="not-a-digest")
        with self.assertRaisesRegex(AdmissionRefused, "identity-invalid:mask"):
            validate_identity_bundle(expected, malformed)

    def test_altered_admission_pin_and_notice_index_are_refused(self) -> None:
        source = CONTROL_SOURCE.read_bytes()
        rom = build_control_rom(source)
        reference = bytes(channel for pixel in expected_frame() for channel in pixel)
        with tempfile.TemporaryDirectory(prefix="gbb-admission-pins-") as name:
            root = pathlib.Path(name)
            manifest, _record = _write_synthetic_admission_repo(root, source, rom, reference)
            pin = manifest.parent / "admission.commit"
            pin.write_text("0" * 40 + "\n", encoding="ascii")
            code, output = check_synthetic_admission(root, manifest)
            self.assertNotEqual(code, 0)
            self.assertIn(b"admission-pin-invalid", output)
        with tempfile.TemporaryDirectory(prefix="gbb-notice-pin-") as name:
            root = pathlib.Path(name)
            manifest, _record = _write_synthetic_admission_repo(root, source, rom, reference)
            index = root / "THIRD_PARTY_NOTICES.md"
            index.write_bytes(index.read_bytes() + b"\nchanged synthetic notice pin\n")
            code, output = check_synthetic_admission(root, manifest)
            self.assertNotEqual(code, 0)
            self.assertIn(b"admission-pin-mismatch", output)

    def test_unsafe_manifest_path_is_refused_before_commit_comparison(self) -> None:
        source = CONTROL_SOURCE.read_bytes()
        rom = build_control_rom(source)
        reference = bytes(channel for pixel in expected_frame() for channel in pixel)
        with tempfile.TemporaryDirectory(prefix="gbb-unsafe-admission-") as name:
            root = pathlib.Path(name)
            manifest_path, manifest = _write_synthetic_admission_repo(root, source, rom, reference)
            manifest["files"][0]["path"] = "../unsafe.bin"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            code, output = check_synthetic_admission(root, manifest_path)
            self.assertNotEqual(code, 0)
            self.assertIn(b"path-invalid", output)

    def test_malformed_synthetic_manifest_json_is_refused(self) -> None:
        source = CONTROL_SOURCE.read_bytes()
        rom = build_control_rom(source)
        reference = bytes(channel for pixel in expected_frame() for channel in pixel)
        with tempfile.TemporaryDirectory(prefix="gbb-malformed-admission-") as name:
            root = pathlib.Path(name)
            manifest_path, _manifest = _write_synthetic_admission_repo(root, source, rom, reference)
            manifest_path.write_bytes(b'{"')
            code, output = check_synthetic_admission(root, manifest_path)
            self.assertNotEqual(code, 0)
            self.assertIn(b"json-invalid", output)

    def test_absent_approval_fails_before_runner_path_is_used(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gbb-admission-gate-") as name:
            root = pathlib.Path(name)
            with self.assertRaisesRegex(AdmissionRefused, "scope-resolution-required"):
                require_approved(root, "a" * 40)

    def test_unresolved_gate_refuses_even_when_status_claims_approved(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gbb-admission-unresolved-") as name:
            root = pathlib.Path(name)
            assessment = root / "tests/external/diagnostic-assessment.json"
            assessment.parent.mkdir(parents=True)
            assessment.write_text(json.dumps({
                "origin": "upstream",
                "status": "approved",
                "source_revision": "a" * 40,
                "gates": [{"id": "reference-art", "status": "unresolved",
                           "reason": "repository and public-CI grant scope not established"}],
            }), encoding="utf-8")
            revision = _commit_test_admission_source(root)
            with self.assertRaisesRegex(AdmissionRefused, "scope-resolution-required.*reference-art"):
                require_approved(root, revision)

    def test_uncommitted_approval_mutants_cannot_authorize_real_inputs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gbb-admission-dirty-approval-") as name:
            root = pathlib.Path(name)
            self._copy_review_records(root)
            revision = _commit_test_admission_source(root, inventory=True)

            assessment = json.loads((root / "tests/external/diagnostic-assessment.json").read_text())
            for gate in assessment["required_gates"]:
                gate["status"] = "supported"
                gate["blocker"] = None
                gate["evidence"] = ["https://github.com/example/committed-review"]
            for component in assessment["components"]:
                component["status"] = "supported"
                component["scope"] = {"repository": True, "public_ci": True}
                component["evidence"] = ["https://github.com/example/committed-review"]
                component["blocker"] = None
            assessment["model_applicability"]["gbmicrotest"]["per_case_source_evidence"] = [
                {"case": case["name"], "source": "https://github.com/example/case-review"}
                for case in json.loads(
                    (root / "tests/external/gbmicrotest-inventory.json").read_text())["cases"]
            ]
            assessment["source_revision"] = revision
            assessment["status"] = "approved"
            self._write_record(root, "diagnostic-assessment.json", assessment)

            inventory = json.loads((root / "tests/external/gbmicrotest-inventory.json").read_text())
            for case in inventory["cases"]:
                for identity in (case["source"], case["prebuilt_rom"]):
                    identity["sha256"] = "a" * 64
                    identity["sha256_status"] = "verified-against-pinned-git-blob"
            self._write_record(root, "gbmicrotest-inventory.json", inventory)

            # Prove the working-tree mutant is internally plausible to the legacy schema checks.
            mutable_record, _ = validate_assessment(root)
            self.assertEqual(mutable_record["status"], "approved")

            checker_path = root / PHASE20_CHECKER_PATH
            checker_bytes = checker_path.read_bytes()
            checker_path.write_bytes(checker_bytes[:2] + b"x" + checker_bytes[3:])
            with self.assertRaisesRegex(AdmissionRefused, "source file differs from commit: tests/scripts/verify-fixture-admission.py"):
                require_approved(root, revision)
            checker_path.write_bytes(checker_bytes)

            policy_path = root / PHASE20_POLICY_PATH
            policy_bytes = policy_path.read_bytes()
            policy_path.write_bytes(b"[" + policy_bytes[1:])
            with self.assertRaisesRegex(AdmissionRefused, "source file differs from commit: cmake/FixtureAdmissionPolicy.json"):
                require_approved(root, revision)
            policy_path.write_bytes(policy_bytes)

            with self.assertRaisesRegex(AdmissionRefused, "scope-resolution-required.*unresolved gates") as caught:
                require_approved(root, revision)
            self.assertIn("gbmicrotest_case_applicability", str(caught.exception))

    def _copy_review_records(self, root: pathlib.Path) -> None:
        destination = root / "tests/external"
        destination.mkdir(parents=True)
        for filename in ("diagnostic-assessment.json", "gbmicrotest-inventory.json"):
            (destination / filename).write_bytes((ROOT / "tests/external" / filename).read_bytes())

    def _write_record(self, root: pathlib.Path, filename: str, record: dict[str, Any]) -> None:
        (root / "tests/external" / filename).write_text(
            json.dumps(record, sort_keys=True), encoding="utf-8")

    def test_rights_status_mutant_needs_positive_repository_and_ci_scope(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gbb-admission-rights-mutant-") as name:
            root = pathlib.Path(name)
            self._copy_review_records(root)
            record = json.loads((root / "tests/external/diagnostic-assessment.json").read_text())
            component = next(item for item in record["components"] if item["id"] == "acid2_reference_images")
            component["status"] = "supported"
            self._write_record(root, "diagnostic-assessment.json", record)
            with self.assertRaisesRegex(AdmissionRefused, "positive-scope-incomplete:acid2_reference_images"):
                validate_assessment(root)

    def test_model_status_mutant_needs_per_case_source_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gbb-admission-model-mutant-") as name:
            root = pathlib.Path(name)
            self._copy_review_records(root)
            record = json.loads((root / "tests/external/diagnostic-assessment.json").read_text())
            record["model_applicability"]["gbmicrotest"]["per_case_source_evidence"] = []
            gate = next(item for item in record["required_gates"]
                        if item["id"] == "gbmicrotest_case_applicability")
            gate["status"] = "supported"
            gate["blocker"] = None
            self._write_record(root, "diagnostic-assessment.json", record)
            with self.assertRaisesRegex(AdmissionRefused, "case-applicability-evidence-incomplete"):
                validate_assessment(root)

    def test_roster_projection_rejects_changed_identity_even_with_same_totals(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gbb-admission-roster-mutant-") as name:
            root = pathlib.Path(name)
            self._copy_review_records(root)
            record = json.loads((root / "tests/external/gbmicrotest-inventory.json").read_text())
            case = record["cases"][0]
            case["source"]["git_blob_sha1"] = "0" * 40
            self._write_record(root, "gbmicrotest-inventory.json", record)
            with self.assertRaisesRegex(AdmissionRefused, "projection-pin-mismatch"):
                validate_gbmicrotest_inventory(root)

    def test_eligibility_mutant_cannot_hide_a_blocked_case(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gbb-admission-eligibility-mutant-") as name:
            root = pathlib.Path(name)
            self._copy_review_records(root)
            record = json.loads((root / "tests/external/gbmicrotest-inventory.json").read_text())
            moved = record["accounting"]["blocked_not_observed_names"].pop()
            record["accounting"]["admitted_eligible_names"] = [moved]
            self._write_record(root, "gbmicrotest-inventory.json", record)
            with self.assertRaisesRegex(AdmissionRefused, "eligibility-accounting-mismatch"):
                validate_gbmicrotest_inventory(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=False)
    modes.add_argument("--self-test-tracer", action="store_true")
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--self-test-controls", action="store_true")
    modes.add_argument("--check-assessment", action="store_true")
    modes.add_argument("--check-closeout", action="store_true")
    modes.add_argument("--prepare-gbmicrotest-fixture", action="store_true")
    parser.add_argument("--require-approved", action="store_true")
    parser.add_argument("--closeout-kind", choices=("acid2", "gbmicrotest", "all"))
    parser.add_argument("--runner", type=pathlib.Path)
    parser.add_argument("--current-build-qualification", type=pathlib.Path)
    parser.add_argument("--deadline-seconds", type=int)
    parser.add_argument("--write-evidence", type=pathlib.Path)
    parser.add_argument("--repo-root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--source-repo-root", type=pathlib.Path)
    parser.add_argument("--source-revision", default="HEAD")
    args = parser.parse_args(argv)
    if not any((args.self_test_tracer, args.self_test, args.self_test_controls,
                args.check_assessment, args.check_closeout, args.prepare_gbmicrotest_fixture,
                args.require_approved)):
        parser.error("one checker mode is required")
    if args.check_closeout and args.closeout_kind is None:
        parser.error("--check-closeout requires --closeout-kind")
    if args.closeout_kind and not args.check_closeout:
        parser.error("--closeout-kind requires --check-closeout")
    runtime_flags = (args.current_build_qualification is not None or args.deadline_seconds is not None
                     or args.write_evidence is not None)
    if runtime_flags and (not args.check_closeout or args.runner is None
                          or args.current_build_qualification is None or args.deadline_seconds is None
                          or args.write_evidence is None):
        parser.error("runtime requires --check-closeout, --runner, --current-build-qualification, "
                     "--deadline-seconds, and --write-evidence together")
    if runtime_flags and not args.require_approved:
        parser.error("runtime requires --require-approved")
    if runtime_flags and args.closeout_kind not in ("acid2", "gbmicrotest", "all"):
        parser.error("bounded runtime requires --closeout-kind acid2, gbmicrotest, or all")
    if args.require_approved and (args.self_test_tracer or args.self_test or args.self_test_controls
                                  or args.check_assessment):
        parser.error("--require-approved may modify --check-closeout or run as the legacy admission mode")
    if args.self_test_tracer:
        if args.runner is None:
            parser.error("--self-test-tracer requires --runner")
        return run_tracer(args.runner.resolve())
    if args.prepare_gbmicrotest_fixture:
        try:
            prepare_gbmicrotest_fixture(args.repo_root)
            return 0
        except (AdmissionRefused, OSError, subprocess.SubprocessError) as error:
            print(f"REJECT {error}", file=sys.stderr)
            return 2
    if args.self_test or args.self_test_controls:
        if args.runner is not None:
            AdmissionControlTests.runner_path = args.runner.resolve()
        suite_class = AdmissionContractTests if args.self_test else AdmissionControlTests
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(suite_class)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1
    try:
        if args.check_assessment:
            record, inventory = validate_assessment(args.repo_root.resolve())
            unresolved = sum(gate["status"] != "supported" for gate in record["required_gates"])
            print(f"diagnostic assessment valid status={record['status']} unresolved_gates={unresolved} "
                  f"gbmicrotest_cases={len(inventory['cases'])}")
            return 0
        revision = args.source_revision
        if revision == "HEAD":
            revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=args.repo_root,
                                      capture_output=True, check=True, timeout=30).stdout.decode().strip()
        if args.check_closeout:
            invocation_started = time.monotonic()
            record = check_diagnostic_closeout(args.repo_root, revision, args.closeout_kind,
                                               require_approved=args.require_approved)
            if runtime_flags:
                qualified = validate_current_runner_qualification(
                    args.repo_root, revision, args.runner, args.current_build_qualification,
                    invocation_started, args.deadline_seconds)
                if args.closeout_kind == "acid2":
                    if args.write_evidence.resolve(strict=False) != (
                            args.repo_root.resolve() / ACID2_RUNTIME_EVIDENCE_PATH):
                        raise AdmissionRefused("diagnostic-runtime-acid2-evidence-path-invalid")
                    runtime = run_acid2_runtime(
                        args.repo_root, revision, qualified["runner"], args.deadline_seconds,
                        invocation_started, record["_acid2_bundle_content"],
                        record["_acid2_manifest"], qualified, args.write_evidence)
                    print(f"diagnostic closeout acid2 runtime result source={revision} comparisons=3 "
                          f"verdict={runtime['status']} runner={runtime['runner_sha256']} "
                          f"qualification={runtime['qualification_sha256']} "
                          f"evidence={runtime['evidence_sha256']}")
                    return 0 if runtime["status"] == "pass" else 1
                if args.closeout_kind == "all":
                    output_path = args.write_evidence.resolve(strict=False)
                    preflight_path = (args.repo_root.resolve() / DIAGNOSTIC_RUNTIME_PREFLIGHT_PATH)
                    final_path = (args.repo_root.resolve() / DIAGNOSTIC_RUNTIME_FINAL_PATH)
                    if output_path not in (preflight_path, final_path):
                        raise AdmissionRefused("diagnostic-runtime-combined-evidence-path-invalid")
                    closeout_raw = read_source_file(args.repo_root, revision, DIAGNOSTIC_CLOSEOUT_PATH)
                    closeout_sha = sha256(closeout_raw)
                    acid2_runtime = run_acid2_runtime(
                        args.repo_root, revision, qualified["runner"], args.deadline_seconds,
                        invocation_started, record["_acid2_bundle_content"],
                        record["_acid2_manifest"], qualified)
                    gb_evidence_relative = (GBMICROTEST_RUNTIME_PREFLIGHT_PATH
                                            if output_path == preflight_path
                                            else GBMICROTEST_RUNTIME_FINAL_PATH)
                    gb_runtime = run_gbmicrotest_runtime(
                        args.repo_root, revision, qualified["runner"],
                        qualified["qualification_path"], args.deadline_seconds,
                        pathlib.Path(gb_evidence_relative), invocation_started,
                        record["_gbmicrotest_bundle_content"], qualified)
                    accounting = record["gbmicrotest"]["accounting"]
                    eligible_names = accounting["admitted_eligible_names"]
                    excluded_names = accounting["excluded_names"]
                    if (eligible_names != [GBMICROTEST_SELECTED_CASE]
                            or len(excluded_names) != GBMICROTEST_CASE_COUNT - 1
                            or set(eligible_names) & set(excluded_names)):
                        raise AdmissionRefused("diagnostic-runtime-roster-accounting-mismatch")
                    combined_status = ("pass" if acid2_runtime["status"] == "pass"
                                       and gb_runtime["verdict"] == "pass" else "runtime-failed")
                    combined = {
                        "schema": "gabbaboy-diagnostic-runtime-evidence-v1",
                        "source_revision": revision,
                        "closeout_record_sha256": closeout_sha,
                        "runner_sha256": qualified["runner_sha256"],
                        "qualification_sha256": qualified["qualification_sha256"],
                        "acid2": {"status": acid2_runtime["status"],
                                  "comparisons": acid2_runtime["comparisons"]},
                        "gbmicrotest": gb_runtime,
                        "eligible_names": eligible_names,
                        "executed_names": [GBMICROTEST_SELECTED_CASE]
                        if gb_runtime["verdict"] == "pass" else [],
                        "excluded_names": excluded_names,
                        "roster_count": GBMICROTEST_CASE_COUNT,
                        "combined_status": combined_status,
                    }
                    relative_output = (DIAGNOSTIC_RUNTIME_PREFLIGHT_PATH
                                       if output_path == preflight_path
                                       else DIAGNOSTIC_RUNTIME_FINAL_PATH)
                    previous_evidence_sha = None
                    if output_path == preflight_path:
                        previous_rows = record.get("gbmicrotest", {}).get("accounting", {}).get("runtime_results", [])
                        if isinstance(previous_rows, list) and len(previous_rows) == 1:
                            previous_evidence_sha = previous_rows[0].get("evidence_sha256")
                    _target, combined_sha = _write_ignored_json(args.repo_root.resolve(),
                                                                relative_output, combined,
                                                                expected_previous_sha256=previous_evidence_sha)
                    if output_path == preflight_path:
                        _record_combined_preflight_result(
                            args.repo_root, revision, closeout_sha, acid2_runtime, gb_runtime,
                            relative_output, combined_sha)
                    else:
                        _verify_combined_runtime_stable(record, acid2_runtime, gb_runtime)
                    if combined_status == "pass":
                        print(f"diagnostic closeout runtime pass source={revision} acid2=2 "
                              f"eligible={len(eligible_names)} executed={len(combined['executed_names'])} "
                              f"excluded={len(excluded_names)}")
                        return 0
                    print(f"diagnostic closeout runtime result source={revision} acid2=3 "
                          f"eligible={len(eligible_names)} executed={len(combined['executed_names'])} "
                          f"excluded={len(excluded_names)} acid2_verdict={acid2_runtime['status']} "
                          f"gbmicrotest_verdict={gb_runtime['verdict']}")
                    return 1
                runtime = run_gbmicrotest_runtime(
                    args.repo_root, revision, qualified["runner"],
                    qualified["qualification_path"], args.deadline_seconds,
                    args.write_evidence, invocation_started,
                    record["_gbmicrotest_bundle_content"], qualified)
                record_gbmicrotest_runtime_result(args.repo_root, revision, runtime)
                executed = 1 if runtime["verdict"] == "pass" else 0
                print(f"diagnostic closeout runtime result source={revision} gbmicrotest=1 "
                      f"eligible=1 executed={executed} excluded={len(record['gbmicrotest']['accounting']['excluded_names'])} "
                      f"verdict={runtime['verdict']} reason={runtime['reason'] or 'none'} "
                      f"runner={runtime['runner_sha256']} evidence={runtime['evidence_sha256']}")
                return 0 if runtime["verdict"] == "pass" else 1
            print(f"diagnostic closeout valid kind={args.closeout_kind} status={record['status']} "
                  f"blockers={','.join(record['_blockers']) or 'none'}")
            return 0
        source_root = (args.source_repo_root or args.repo_root).resolve(strict=True)
        require_approved(args.repo_root.resolve(strict=True), revision,
                         source_repo_root=source_root, candidate_rights=True)
    except (AdmissionRefused, OSError, subprocess.SubprocessError) as error:
        message = str(error)
        if message.startswith("scope-resolution-required:"):
            print(message, file=sys.stderr)
        else:
            print(f"scope-resolution-required: {message}", file=sys.stderr)
        return 2
    print("diagnostic-admission approved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
