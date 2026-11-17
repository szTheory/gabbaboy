#!/usr/bin/env python3
"""Fail-closed admission adapter and original synthetic acid2 tracer control."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
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
DIAGNOSTIC_RIGHTS_REVISION = "e3b4c5c8b58c5617d9cc41f31f1bd699e6cf0a35"
DIAGNOSTIC_RIGHTS_SHA256 = "79030ea8fa874dab505812f644f75d222e4b60fb3705a6fcbbde1630acd8705d"
DIAGNOSTIC_RIGHTS_SIZE = 30529
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
GBMICROTEST_LOGO_START, GBMICROTEST_LOGO_END = 0x0104, 0x0133
GBMICROTEST_CHECKSUM_START, GBMICROTEST_CHECKSUM_END = 0x014E, 0x014F
GBMICROTEST_LICENSE_BLOB = "ca05fdbac9ec607636037171ee3856ea2a3378dd"
GBMICROTEST_LICENSE_SHA256 = "0b3557142dfcce65428fafb9c8254d9d59c027a008af4810867efd7342b77c25"
GBMICROTEST_README_BLOB = "e184a72ed5f6f1b76f5124762c6ed3f79f139e4e"
GBMICROTEST_README_SHA256 = "15610d3e922658503b5250f1e9e0106d3ad6bdee7ff43003147f5871a81a3b92"
GBMICROTEST_HEADER_BLOB = "aba48b4af33aabedc8e86adad5e5e692f6f4a348"
GBMICROTEST_HEADER_SHA256 = "380ab2e41fee82c23881b13650e6301b79809e7baa1d3c828363156a70ba9afd"
GBMICROTEST_BUILD_BLOB = "eb0ddc1368e3a777ef9787dc056d756e95c19102"
GBMICROTEST_BUILD_SHA256 = "c726ca6214cb3861fef0da43da2eebc69f7c63e944b61746be5ec028db977488"
GBMICROTEST_INLINE_CASES = frozenset(("mbc1_ram_banks", "mbc1_rom_banks"))
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
        if not isinstance(acid2, dict) or acid2.get("status") != "blocked-before-derivative":
            raise AdmissionRefused("diagnostic-closeout-acid2-outcome-invalid")
        if acid2.get("font_data") != "excluded-by-design":
            raise AdmissionRefused("diagnostic-closeout-acid2-font-scope-invalid")
        cases = acid2.get("cases")
        expected_acid2 = (
            ("dmg-acid2-v1.0", "dc2295408f881637ff69f784d8d93f3d2db30181",
             "a59741f15579a82205fff557dd000a5ebb6d7f6e"),
            ("cgb-acid2-v1.1", "fa5b7f86d6fb599f79e55169494d981a7af75a31",
             "a541bf54356809dc04cc050f8fc14d9620649f88"),
        )
        if not isinstance(cases, list) or len(cases) != len(expected_acid2):
            raise AdmissionRefused("diagnostic-closeout-acid2-case-set-invalid")
        for item, (source_id, commit, tree) in zip(cases, expected_acid2, strict=True):
            if (not isinstance(item, dict) or item.get("id") != source_id
                    or item.get("commit") != commit or item.get("root_tree_sha1") != tree
                    or item.get("blocked_by") != ["footer-and-reference-images"]
                    or item.get("derivative") != {"status": "not-created", "path": None, "sha256": None}
                    or item.get("admission") != {"status": "not-created", "commit": None}):
                raise AdmissionRefused(f"diagnostic-closeout-acid2-case-mutated:{source_id}")
            source = _diagnostic_source_by_id(rights_record, source_id)
            if source.get("commit") != commit or source.get("root_tree_sha1") != tree:
                raise AdmissionRefused(f"diagnostic-closeout-rights-pin-mismatch:{source_id}")
            image_component = _diagnostic_component(source, "footer-and-reference-images")
            if image_component.get("outcome") != "unresolved":
                raise AdmissionRefused(f"diagnostic-closeout-rights-mismatch:{source_id}:footer-and-reference-images")
            font_component = _diagnostic_component(source, "mgblib-font-data")
            if font_component.get("outcome") != "excluded-by-design":
                raise AdmissionRefused(f"diagnostic-closeout-font-rights-mutated:{source_id}")
        blockers.append("acid2-footer-reference-image-rights-unresolved")
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
        expected_source_review = {
            "selected_case": GBMICROTEST_SELECTED_CASE,
            "selection_basis": "One DIV-counter software diagnostic selected from the pinned shared-macro protocol group before any emulator outcome was observed.",
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
                "admission_status": "not-attempted",
                "staging_status": "not-staged",
                "runtime_status": "not-run",
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
                    "kind": "local bootless header derivative; not admitted or staged",
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
                "status": "unresolved",
                "component": "compiled bootless ROM output",
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
                "finding": "The pinned MIT notice grants broad rights to the undefined term Software; the README identifies prebuilt ROMs in bin/ and an unpinned WLA-DX build instruction but gives no explicit license scope for prebuilt or generated ROM outputs. No component-specific repository/public-CI output grant is established by these texts.",
                "required_evidence": "An authoritative component-specific grant or source statement that the pinned prebuilt/compiled ROM output may be redistributed in the repository and public CI.",
            },
            "logo_scope": {
                "t5_upstream_component_outcome": "unresolved",
                "current_derivative_status": "logo bytes removed from local review derivative",
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
                "runtime_status": "not-run",
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
        if gbmicrotest.get("status") != "blocked-before-admission":
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-status-mutated")
        if gbmicrotest.get("source") != {
                "repository": "https://github.com/aappleby/gbmicrotest",
                "commit": GBMICROTEST_COMMIT, "root_tree_sha1": GBMICROTEST_TREE,
                "tree_entry_count": 1034, "tree_truncated": False}:
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-source-mutated")
        if gbmicrotest.get("source_review") != expected_source_review:
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-source-review-mutated")
        if gbmicrotest.get("blocked_by") != ["prebuilt-rom-output-scope"]:
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-blockers-mutated")
        if gbmicrotest.get("cohort_status") != "blocked-before-admission":
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
                disposition = {
                    "status": "blocked-candidate",
                    "blocked_by": ["prebuilt-rom-output-scope"],
                    "reason": "The pinned original ROM and logo-free review derivative were hash-checked locally, and the case supports a DMG-CPU-B software diagnostic scope; no component-specific repository/public-CI grant for the compiled ROM output is established. No fixture was admitted, staged, or run.",
                }
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
            })
        cohort = gbmicrotest.get("accounting")
        if cohort != {
                "roster_projection_sha256": GBMICROTEST_ROSTER_PROJECTION_SHA256,
                "roster_count": GBMICROTEST_CASE_COUNT,
                "roster_accounting_complete": True,
                "admitted_eligible_names": [],
                "executed_names": [],
                "blocked_candidate_names": [GBMICROTEST_SELECTED_CASE],
                "excluded_names": excluded_names,
                "runtime_results": [],
                "final_execution_accounting_complete": False,
            }:
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-accounting-mutated")
        if cohort_cases != expected_rows:
            raise AdmissionRefused("diagnostic-closeout-gbmicrotest-case-accounting-mutated")
        blockers.append("gbmicrotest-rom-output-scope-unresolved")
    if record.get("status") != "blocked-before-admission":
        raise AdmissionRefused("diagnostic-closeout-status-mutated")
    record["_blockers"] = blockers
    return record


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
        rights_raw = _git(ROOT, "show", f"{DIAGNOSTIC_RIGHTS_REVISION}:{CANDIDATE_CLOSEOUT_PATH}")
        return record, _json_without_duplicates(rights_raw, "diagnostic-rights-input")

    def test_acid2_image_gate_stays_blocked_without_creating_an_output(self) -> None:
        record, rights = self._diagnostic_closeout_inputs()
        validated = validate_diagnostic_closeout_record(record, rights, "acid2")
        self.assertEqual(validated["status"], "blocked-before-admission")
        self.assertEqual(validated["_blockers"], ["acid2-footer-reference-image-rights-unresolved"])
        self.assertEqual([case["derivative"]["status"] for case in validated["acid2"]["cases"]],
                         ["not-created", "not-created"])

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
        component["outcome"] = "supported"
        with self.assertRaisesRegex(AdmissionRefused, "diagnostic-closeout-rights-mismatch:dmg-acid2-v1.0"):
            validate_diagnostic_closeout_record(record, rights, "acid2")

    def test_gbmicrotest_accounts_for_all_513_names_without_admitting_or_running(self) -> None:
        record, rights = self._diagnostic_closeout_inputs()
        inventory = validate_gbmicrotest_inventory(ROOT)
        validated = validate_diagnostic_closeout_record(record, rights, "gbmicrotest", inventory)
        accounting = validated["gbmicrotest"]["accounting"]
        self.assertEqual(accounting["roster_count"], GBMICROTEST_CASE_COUNT)
        self.assertTrue(accounting["roster_accounting_complete"])
        self.assertEqual(accounting["admitted_eligible_names"], [])
        self.assertEqual(accounting["executed_names"], [])
        self.assertEqual(accounting["blocked_candidate_names"], [GBMICROTEST_SELECTED_CASE])
        self.assertEqual(len(accounting["excluded_names"]), GBMICROTEST_CASE_COUNT - 1)
        self.assertFalse(accounting["final_execution_accounting_complete"])
        self.assertEqual(validated["_blockers"], ["gbmicrotest-rom-output-scope-unresolved"])
        review = validated["gbmicrotest"]["source_review"]
        self.assertEqual(review["model_applicability"]["status"], "supported")
        self.assertEqual(review["model_applicability"]["hardware_applicability"],
                         "not-established; no hardware or DMG-CPU-08 claim")
        selected = next(item for item in validated["gbmicrotest"]["cases"]
                        if item["name"] == GBMICROTEST_SELECTED_CASE)
        self.assertEqual(selected["prebuilt_rom"]["sha256"], GBMICROTEST_SELECTED_ROM_SHA256)
        self.assertEqual(selected["disposition"]["blocked_by"], ["prebuilt-rom-output-scope"])

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
            self.assertIn("potion-panic-gbcompo25/visual-assets", detail)
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
            record = check_diagnostic_closeout(args.repo_root, revision, args.closeout_kind,
                                               require_approved=args.require_approved)
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
