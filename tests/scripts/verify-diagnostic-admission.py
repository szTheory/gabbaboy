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
PHASE20 = ROOT / "tests/scripts/verify-fixture-admission.py"
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


def check_synthetic_admission(root: pathlib.Path, manifest_path: pathlib.Path) -> tuple[int, bytes]:
    relative = manifest_path.relative_to(root).as_posix()
    code, stdout, stderr = _bounded_run([sys.executable, "-I", str(PHASE20), "--check-manifest",
                                         relative, "--repo-root", str(root)], cwd=root)
    return code, stdout + stderr


def _commit_test_admission_source(root: pathlib.Path, *, inventory: bool = False) -> str:
    """Create a local immutable source fixture for admission-gate controls."""
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "GabbaBoy Admission Control")
    _git(root, "config", "user.email", "admission-control@example.invalid")
    checker = root / ADMISSION_CHECKER_PATH
    checker.parent.mkdir(parents=True, exist_ok=True)
    checker.write_bytes(pathlib.Path(__file__).read_bytes())
    files = [ADMISSION_CHECKER_PATH, "tests/external/diagnostic-assessment.json"]
    if inventory:
        files.append("tests/external/gbmicrotest-inventory.json")
    _git(root, "add", *files)
    _git(root, "commit", "-qm", "synthetic: immutable admission source")
    return _git(root, "rev-parse", "HEAD").decode("ascii").strip()


def require_approved(root: pathlib.Path, source_revision: str,
                     manifest_path: pathlib.Path | None = None, *,
                     source_repo_root: pathlib.Path | None = None,
                     source_paths: tuple[tuple[str, pathlib.Path], ...] = ()) -> dict:
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
        code, output = check_synthetic_admission(root, manifest_path)
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
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test-tracer", action="store_true")
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--self-test-controls", action="store_true")
    modes.add_argument("--check-assessment", action="store_true")
    modes.add_argument("--require-approved", action="store_true")
    parser.add_argument("--runner", type=pathlib.Path)
    parser.add_argument("--repo-root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--source-repo-root", type=pathlib.Path)
    parser.add_argument("--source-revision", default="HEAD")
    args = parser.parse_args(argv)
    if args.self_test_tracer:
        if args.runner is None:
            parser.error("--self-test-tracer requires --runner")
        return run_tracer(args.runner.resolve())
    if args.self_test or args.self_test_controls:
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
        source_root = (args.source_repo_root or args.repo_root).resolve(strict=True)
        require_approved(args.repo_root.resolve(strict=True), revision,
                         source_repo_root=source_root)
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
