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
PHASE20 = ROOT / "tests/scripts/verify-fixture-admission.py"
ACID2_TOOL = ROOT / "tests/scripts/run-acid2-local.py"
CONTROL_SOURCE = ROOT / "tests/acid2/control.asm"
SCANNER = ROOT / "cmake/ScanForbiddenFixtures.cmake"
BASELINE_COMMIT = "7cc6495e64f3645caa120e7458f754585b788985"
MAX_SOURCE_BYTES = 64 * 1024
MAX_ROM_BYTES = 32 * 1024
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_PROCESS_OUTPUT = 64 * 1024
CONTROL_BUDGET_HALF_DOTS = 350_000
HEX64 = re.compile(r"^[0-9a-f]{64}$")
IDENTITY_FIELDS = ("rom", "reference", "source", "layout", "glyph", "allowlist", "mask", "overlay")


class AdmissionRefused(ValueError):
    pass


def validate_identity_bundle(expected: dict[str, str], candidate: dict[str, str]) -> None:
    """Red-phase scaffold; candidate identities are intentionally not checked yet."""
    return None


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
    pixels = [(255, 255, 255)] * (160 * 144)
    pixels[24 * 160 + 16] = (170, 170, 170)
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


def require_approved(root: pathlib.Path, source_revision: str, manifest_path: pathlib.Path | None = None) -> dict:
    """Require a source-bound, non-synthetic assessment before a real diagnostic can run."""
    if not re.fullmatch(r"[0-9a-f]{40}", source_revision):
        raise AdmissionRefused("source-revision-invalid")
    assessment = root / "tests/external/diagnostic-assessment.json"
    if not assessment.is_file():
        raise AdmissionRefused("scope-resolution-required: diagnostic assessment absent")
    raw = read_limited(assessment, MAX_JSON_BYTES, "diagnostic-assessment")
    try:
        record = json.loads(raw.decode("utf-8", "strict"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        raise AdmissionRefused("diagnostic-assessment-invalid") from None
    if not isinstance(record, dict) or record.get("origin") in ("synthetic", "test-only") \
            or record.get("fixture_kind", "").startswith("synthetic"):
        raise AdmissionRefused("synthetic-only-record-refused")
    if record.get("status") != "approved" or record.get("source_revision") != source_revision:
        raise AdmissionRefused("scope-resolution-required: approval/source identity unresolved")
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
    mask = mask_tool.build_mask(cells)
    overlay = mask_tool.overlay_png(expected, mask)
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
    def test_synthetic_origin_never_satisfies_real_approval(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gbb-admission-gate-") as name:
            root = pathlib.Path(name)
            assessment = root / "tests/external/diagnostic-assessment.json"
            assessment.parent.mkdir(parents=True)
            assessment.write_text(json.dumps({"origin": "test-only", "status": "approved",
                                              "source_revision": "a" * 40}), encoding="utf-8")
            with self.assertRaisesRegex(AdmissionRefused, "synthetic-only-record-refused"):
                require_approved(root, "a" * 40)


class AdmissionControlTests(unittest.TestCase):
    def test_each_mutated_identity_refuses(self) -> None:
        expected = {name: sha256(("expected:" + name).encode("ascii")) for name in IDENTITY_FIELDS}
        for name in IDENTITY_FIELDS:
            with self.subTest(identity=name):
                candidate = dict(expected)
                candidate[name] = sha256(("mutated:" + name).encode("ascii"))
                with self.assertRaisesRegex(AdmissionRefused, f"identity-mismatch:{name}"):
                    validate_identity_bundle(expected, candidate)

    def test_absent_approval_fails_before_runner_path_is_used(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gbb-admission-gate-") as name:
            root = pathlib.Path(name)
            with self.assertRaisesRegex(AdmissionRefused, "scope-resolution-required"):
                require_approved(root, "a" * 40)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test-tracer", action="store_true")
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--self-test-controls", action="store_true")
    modes.add_argument("--require-approved", action="store_true")
    parser.add_argument("--runner", type=pathlib.Path)
    parser.add_argument("--repo-root", type=pathlib.Path, default=ROOT)
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
        revision = args.source_revision
        if revision == "HEAD":
            revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=args.repo_root,
                                      capture_output=True, check=True, timeout=30).stdout.decode().strip()
        require_approved(args.repo_root.resolve(), revision)
    except (AdmissionRefused, OSError, subprocess.SubprocessError) as error:
        print(f"scope-resolution-required: {error}", file=sys.stderr)
        return 2
    print("diagnostic-admission approved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
