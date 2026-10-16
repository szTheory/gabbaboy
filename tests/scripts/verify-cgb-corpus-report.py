#!/usr/bin/env python3
"""Build a bounded, private receipt from existing Phase 14 CTest observations."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
from pathlib import Path
import queue
import re
import selectors
import secrets
import signal
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import threading
import time
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "gabbaboy-cgb-corpus-receipt-v1"
MAX_CASES = 4096
MAX_ASSERTIONS = 65536
MAX_EVENT_BYTES = 4096
MAX_STREAM_BYTES = 16 * 1024 * 1024
MAX_RECEIPT_BYTES = 32 * 1024 * 1024
RUN_TIMEOUT_SECONDS = 30
FULL_RUN_TIMEOUT_SECONDS = 1200
MAX_TOTAL_INPUT_BYTES = 32 * 1024 * 1024
MAX_RUN_LOG_BYTES = 16 * 1024 * 1024
RUN_ID_SCHEMA = "gabbaboy-cgb-corpus-run-v1"
BUILD_STAMP_SCHEMA = "gabbaboy-cgb-corpus-build-stamp-v1"
MAX_CTEST_XML_BYTES = 64 * 1024 * 1024
MAX_CTEST_TESTS = 10000
APU_SUITE_TEST = "cgb_samesuite_apu_suite"
DAA_ID = "mooneye:acceptance/instr/daa.s"
DAA_TEST = "cgb_corpus_mooneye_daa"
PINS = {
    "manifest_sha256": "6efe380d1eae6f2ef1cfc17375d7e71610c9135fdeb67a1452ecf72b26e02fe9",
    "rom_sha256": "3a39eda77a09b817e4e38004a3d117990565fb797e8a4f470920f1b7608f0a08",
    "original_rom_sha256": "7ce07c2d88b721d5cf2f4597f687622357f41c580ef5cd8e70a66038421394d8",
    "source_revision": "31510e12eea6286d36eea060a6adde755e1067aa",
    "source_tree_sha1": "2b8c52424a49a2a7466cf631fd8992c53d0de2fa",
    "report_patch_sha256": "c3679ab53b59da14a0f6af1fdd552316ba922762c3a91988f7f8ac4440516e5d",
    "source_path": "acceptance/instr/daa.s",
    "fixture_sha256": "3a39eda77a09b817e4e38004a3d117990565fb797e8a4f470920f1b7608f0a08",
    "callback_pc": "0166",
    "result_pc": "409a",
    "budget": 2000000,
}


class ReportError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bounded_read(path: Path, limit: int) -> bytes:
    try:
        if path.stat().st_size > limit:
            raise ReportError("input-too-large")
        data = path.read_bytes()
    except ReportError:
        raise
    except OSError as exc:
        raise ReportError("input-unavailable") from exc
    if len(data) > limit:
        raise ReportError("input-too-large")
    return data


def bounded_json(path: Path, limit: int = 4 * 1024 * 1024) -> dict:
    try:
        value = json.loads(bounded_read(path, limit))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ReportError("invalid-json") from exc
    if type(value) is not dict:
        raise ReportError("invalid-json-root")
    return value


def inside_root(path: Path) -> Path:
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(ROOT)
    except ValueError as exc:
        raise ReportError("path-outside-repository") from exc
    return resolved


def build_executable_path(build_dir: Path, target: str) -> Path:
    suffix = sysconfig.get_config_var("EXE") or ""
    if not isinstance(suffix, str):
        suffix = ""
    if suffix and not target.lower().endswith(suffix.lower()):
        target += suffix
    return build_dir / target


def repo_path(path: Path) -> str:
    try:
        return path.resolve(strict=True).relative_to(ROOT).as_posix()
    except (OSError, ValueError) as exc:
        raise ReportError("path-not-repository-relative") from exc


def validate_relative_path(value: object, code: str) -> str:
    if (type(value) is not str or not value or len(value) > 4096 or
            "\0" in value or "\\" in value or value.startswith("/") or
            re.match(r"^[A-Za-z]:", value)):
        raise ReportError(code)
    if any(part in ("", ".", "..") for part in value.split("/")):
        raise ReportError(code)
    return value


def repo_relative_file(value: object, code: str) -> Path:
    relative = validate_relative_path(value, code)
    path = inside_root(ROOT.joinpath(*relative.split("/")))
    if not path.is_file() or repo_path(path) != relative:
        raise ReportError(code)
    return path


def age_reference_path(value: object) -> Path:
    relative = validate_relative_path(value, "reference-path-invalid")
    filename = Path(relative).name
    if not filename.endswith(".png"):
        raise ReportError("reference-path-invalid")
    return repo_relative_file("fixtures/age/references/" + filename,
                              "reference-path-invalid")


def run_git(*args: str, limit: int = 1024 * 1024) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(ROOT), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReportError("git-identity-unavailable") from exc
    if completed.returncode or len(completed.stdout) > limit:
        raise ReportError("git-identity-unavailable")
    return completed.stdout


def current_revision() -> str:
    value = run_git("rev-parse", "HEAD", limit=128).decode("ascii", "strict").strip()
    if not re.fullmatch(r"[0-9a-f]{40,64}", value):
        raise ReportError("git-revision-invalid")
    return value


def covered_dirty_digest(extra_paths: tuple[str, ...] = ()) -> str:
    covered = set((
        "CMakeLists.txt",
        "src/runner/main.c",
        "src/core/gabbaboy.c",
        "tests/CMakeLists.txt",
        "tests/expected-tests.txt",
        "tests/scripts/verify-cgb-corpus-report.py",
        "tests/scripts/verify-cgb-corpus-inventory.py",
        "tests/scripts/verify-cgb-corpus-artifacts.py",
        "tests/scripts/verify-age-m3-pixels.py",
        "tests/scripts/verify-age-phase14-contract.py",
        "tests/test_age.c",
        "tests/test_magentests.c",
        "tests/test_samesuite_apu.c",
        "tests/test_samesuite_hdma.c",
        "tests/external/cgb-corpus-inventory.json",
        "fixtures/mooneye-cgb/manifest.json",
        "fixtures/age/manifest.json",
        "fixtures/samesuite/manifest.json",
        "fixtures/magentests/manifest.json",
    ))
    covered.update(extra_paths)
    rows = []
    total = 0
    for name in sorted(covered):
        data = bounded_read(ROOT / name, 32 * 1024 * 1024)
        total += len(data)
        if total > MAX_TOTAL_INPUT_BYTES:
            raise ReportError("covered-inputs-too-large")
        rows.append((name, sha256(data)))
    encoded = json.dumps(rows, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return sha256(encoded)


def load_daa_contract() -> dict:
    inventory = bounded_json(ROOT / "tests/external/cgb-corpus-inventory.json")
    cases = inventory.get("cases")
    outputs = inventory.get("outputs")
    if type(cases) is not list or type(outputs) is not list or len(cases) > MAX_CASES:
        raise ReportError("inventory-shape")
    rows = [row for row in cases if type(row) is dict and row.get("id") == DAA_ID]
    if len(rows) != 1:
        raise ReportError("case-membership")
    case = rows[0]
    output_rows = [row for row in outputs if type(row) is dict and row.get("id") == case.get("output_id")]
    if len(output_rows) != 1:
        raise ReportError("output-membership")
    output = output_rows[0]
    manifest_path = ROOT / "fixtures/mooneye-cgb/manifest.json"
    manifest_data = bounded_read(manifest_path, 4 * 1024 * 1024)
    manifest = bounded_json(manifest_path)
    manifest_sha = sha256(manifest_data)
    fixture_rows = [row for row in manifest.get("fixtures", [])
                    if type(row) is dict and row.get("alias") == "daa"]
    assertions = case.get("assertion_contract")
    expected_rows = assertions.get("rows") if type(assertions) is dict else None
    if len(fixture_rows) != 1 or type(expected_rows) is not list or len(expected_rows) != 1:
        raise ReportError("assertion-membership")
    fixture = fixture_rows[0]
    assertion = expected_rows[0]
    rom_path = ROOT / "fixtures/mooneye-cgb" / fixture.get("rom", "")
    actual_rom_sha = sha256(bounded_read(rom_path, 2 * 1024 * 1024))
    expected = {
        "manifest_sha256": manifest_sha,
        "rom_sha256": actual_rom_sha,
        "original_rom_sha256": fixture.get("original_sha256"),
        "source_revision": manifest.get("suite", {}).get("revision"),
        "source_tree_sha1": manifest.get("suite", {}).get("tree_sha1"),
        "report_patch_sha256": next((row.get("sha256") for row in manifest.get("parent_references", [])
                                      if row.get("role") == "headless-report-patch"), None),
        "source_path": case.get("source_id", "").removeprefix("mooneye:"),
        "fixture_sha256": output.get("sha256"),
        "callback_pc": assertion.get("callback_pc", "").removeprefix("0x").lower(),
        "result_pc": assertion.get("result_pc", "").removeprefix("0x").lower(),
        "budget": fixture.get("budget_half_dots"),
    }
    if expected != PINS:
        raise ReportError("pinned-input-mismatch")
    if (output.get("sha256") != actual_rom_sha or fixture.get("sha256") != actual_rom_sha or
            case.get("model") != "CGB-CPU-E" or case.get("mode") != "compat" or
            case.get("speed") != "normal" or case.get("suite") != "mooneye" or
            case.get("test_binding", {}).get("ctest_name") != DAA_TEST or
            case.get("test_binding", {}).get("state") != "bound" or
            assertion.get("id") != "ld-b-b-result" or
            assertion.get("expected_disposition") != "pass" or
            assertion.get("observed_result") != "pass" or
            assertion.get("evaluator_status") != "pass"):
        raise ReportError("case-contract-mismatch")
    if fixture.get("mode", "").split()[0] != "compat" or fixture.get("expect") != "pass":
        raise ReportError("fixture-contract-mismatch")
    return {
        "case": case,
        "fixture": fixture,
        "assertion": assertion,
        "manifest_path": manifest_path,
        "rom_path": rom_path,
        "manifest_sha256": manifest_sha,
        "rom_sha256": actual_rom_sha,
        "original_rom_sha256": fixture.get("original_sha256"),
    }


def build_identity(build_dir: Path, contract: dict) -> dict:
    build_dir = inside_root(build_dir)
    executable = build_executable_path(build_dir, "gabbaboy-runner")
    cache = build_dir / "CMakeCache.txt"
    executable_data = bounded_read(executable, 128 * 1024 * 1024)
    cache_data = bounded_read(cache, 4 * 1024 * 1024)
    cache_text = cache_data.decode("utf-8", "strict")
    relevant = [line for line in cache_text.splitlines()
                if line.startswith(("CMAKE_BUILD_TYPE:", "CMAKE_C_COMPILER:",
                                    "CMAKE_GENERATOR:", "GBB_BUILD_"))]
    if not relevant:
        raise ReportError("build-config-unavailable")
    return {
        "core_revision": current_revision(),
        "covered_dirty_inputs_sha256": covered_dirty_digest(),
        "executable_path": repo_path(executable),
        "executable_sha256": sha256(executable_data),
        "build_config_sha256": sha256("\n".join(relevant).encode("utf-8")),
        "build_cache_sha256": sha256(cache_data),
        "manifest_path": repo_path(contract["manifest_path"]),
        "manifest_sha256": contract["manifest_sha256"],
        "rom_path": repo_path(contract["rom_path"]),
        "rom_sha256": contract["rom_sha256"],
        "original_rom_sha256": contract["original_rom_sha256"],
        "suite_source_revision": PINS["source_revision"],
        "suite_source_tree_sha1": PINS["source_tree_sha1"],
        "report_patch_sha256": PINS["report_patch_sha256"],
        "source_path": PINS["source_path"],
        "tool_path": repo_path(Path(__file__)),
        "tool_sha256": sha256(bounded_read(Path(__file__), 1024 * 1024)),
        "model": "CGB-CPU-E",
        "mode": "compat",
        "speed": "normal",
        "boot_policy": "skipped",
        "budget_half_dots": PINS["budget"],
        "case_ids": [DAA_ID],
        "assertion_ids": ["ld-b-b-result"],
    }


def load_corpus_context() -> dict:
    inventory_path = ROOT / "tests/external/cgb-corpus-inventory.json"
    inventory = bounded_json(inventory_path, 8 * 1024 * 1024)
    cases = inventory.get("cases")
    outputs = inventory.get("outputs")
    sources = inventory.get("source_candidates")
    if (inventory.get("schema") != "gabbaboy-cgb-corpus-inventory-v1" or
            inventory.get("phase") != 14 or type(cases) is not list or
            type(outputs) is not list or type(sources) is not list or
            len(cases) != 107 or len(cases) > MAX_CASES or len(outputs) > 300 or len(sources) > 300):
        raise ReportError("inventory-shape")
    output_by_id = {row.get("id"): row for row in outputs if type(row) is dict}
    source_by_id = {row.get("id"): row for row in sources if type(row) is dict}
    if len(output_by_id) != len(outputs) or len(source_by_id) != len(sources):
        raise ReportError("inventory-duplicate-id")
    case_by_id = {}
    case_by_test = {}
    output_names = set()
    assertion_rows = 0
    for case in cases:
        if (type(case) is not dict or type(case.get("id")) is not str or
                not case["id"] or len(case["id"].encode("utf-8")) > 1024 or
                any(ord(char) < 33 or ord(char) == 127 for char in case["id"]) or
                case["id"] in case_by_id):
            raise ReportError("case-membership")
        cid = case["id"]
        output = output_by_id.get(case.get("output_id"))
        source = source_by_id.get(case.get("source_id"))
        binding = case.get("test_binding")
        contract = case.get("assertion_contract")
        rows = contract.get("rows") if type(contract) is dict else None
        name = binding.get("ctest_name") if type(binding) is dict else None
        if (output is None or source is None or output.get("admission_status") != "admitted" or
                case.get("suite") not in ("age", "magentests", "mooneye", "samesuite") or
                case.get("model") != "CGB-CPU-E" or case.get("mode") not in ("native", "compat") or
                case.get("speed") not in ("normal", "double") or
                output.get("suite") != case.get("suite") or source.get("suite") != case.get("suite") or
                source.get("id") != case.get("source_id") or
                type(name) is not str or not re.fullmatch(r"[A-Za-z0-9_.:-]+", name) or
                binding.get("state") != "bound" or name in case_by_test or
                type(rows) is not list or not rows or len(rows) > MAX_ASSERTIONS or
                contract.get("state") != "qualified" or contract.get("count") != len(rows)):
            raise ReportError("case-contract-incomplete")
        ids = []
        for row in rows:
            if (type(row) is not dict or type(row.get("id")) is not str or
                    not row["id"] or len(row["id"].encode("utf-8")) > MAX_EVENT_BYTES or
                    any(ord(char) < 32 or ord(char) == 127 for char in row["id"]) or
                    row.get("expected_disposition") not in ("pass", "fail")):
                raise ReportError("assertion-contract-invalid")
            ids.append(row["id"])
        if len(ids) != len(set(ids)):
            raise ReportError("assertion-membership-duplicate")
        assertion_rows += len(rows)
        if assertion_rows > MAX_ASSERTIONS:
            raise ReportError("assertion-contract-too-large")
        rel_output = validate_relative_path(output.get("output_path"), "output-path-invalid")
        repo_relative_file(rel_output, "output-path-invalid")
        validate_relative_path(source.get("source_path"), "source-path-invalid")
        if not re.fullmatch(r"[0-9a-f]{64}", str(output.get("sha256", ""))):
            raise ReportError("inventory-digest-invalid")
        if (case.get("suite") == "mooneye" and
                not re.fullmatch(r"[0-9a-f]{40}", str(source.get("source_commit", "")))):
            raise ReportError("inventory-source-revision-invalid")
        output_names.add(rel_output)
        case_by_id[cid] = {"case": case, "output": output, "source": source}
        case_by_test[name] = cid
    expected_data = bounded_read(ROOT / "tests/expected-tests.txt", 1024 * 1024)
    expected_names = expected_data.decode("utf-8", "strict").splitlines()
    expected_names = [name.strip() for name in expected_names if name.strip() and not name.lstrip().startswith("#")]
    if len(expected_names) != len(set(expected_names)) or not set(case_by_test) <= set(expected_names):
        raise ReportError("case-tests-not-registered")
    suite_counts = {suite: sum(item["case"]["suite"] == suite for item in case_by_id.values())
                    for suite in ("age", "magentests", "mooneye", "samesuite")}
    if suite_counts != {"age": 19, "magentests": 5, "mooneye": 9, "samesuite": 74}:
        raise ReportError("suite-case-count-mismatch")
    return {
        "inventory": inventory,
        "inventory_path": inventory_path,
        "cases": case_by_id,
        "case_by_test": case_by_test,
        "outputs": output_by_id,
        "sources": source_by_id,
        "output_names": sorted(output_names),
        "test_names": sorted(case_by_test),
        "assertion_rows": assertion_rows,
    }


def full_build_identity(build_dir: Path, context: dict) -> dict:
    build_dir = inside_root(build_dir)
    executables = [
        "gabbaboy-runner",
        "tests/test_age",
        "tests/test_age_m3",
        "tests/test_magentests",
        "tests/test_magentests_hdma",
        "tests/test_samesuite_apu",
        "tests/test_samesuite_hdma",
    ]
    cache_path = build_dir / "CMakeCache.txt"
    cache_data = bounded_read(cache_path, 4 * 1024 * 1024)
    artifacts = []
    for name in executables:
        path = build_executable_path(build_dir, name)
        data = bounded_read(path, 128 * 1024 * 1024)
        artifacts.append({"path": repo_path(path), "size_bytes": len(data), "sha256": sha256(data)})
    paths = set(context["output_names"])
    reference_paths = set()
    for row in context["outputs"].values():
        if type(row.get("reference_png")) is str:
            reference = age_reference_path(row["reference_png"])
            reference_paths.add(repo_path(reference))
    paths.update(reference_paths)
    paths.update({
        "tests/external/cgb-corpus-inventory.json",
        "tests/external/cgb-apu-dispositions.json",
        "tests/external/cgb-ppu-dispositions.json",
        "tests/external/cgb-speed-dispositions.json",
        "fixtures/age/manifest.json",
        "fixtures/samesuite/manifest.json",
        "fixtures/magentests/manifest.json",
        "fixtures/mooneye-cgb/manifest.json",
        "tests/scripts/verify-cgb-corpus-report.py",
        "tests/scripts/verify-cgb-corpus-inventory.py",
        "tests/scripts/verify-age-m3-pixels.py",
        "tests/scripts/verify-age-phase14-contract.py",
        "src/runner/main.c",
        "src/core/gabbaboy.c",
        "tests/CMakeLists.txt",
        "tests/expected-tests.txt",
        "tests/test_age.c",
        "tests/test_magentests.c",
        "tests/test_samesuite_apu.c",
        "tests/test_samesuite_hdma.c",
    })
    input_hashes = []
    total_bytes = len(cache_data)
    for name in sorted(paths):
        path = ROOT / name
        data = bounded_read(path, 8 * 1024 * 1024)
        total_bytes += len(data)
        if total_bytes > MAX_TOTAL_INPUT_BYTES:
            raise ReportError("covered-inputs-too-large")
        input_hashes.append({"path": repo_path(path), "size_bytes": len(data), "sha256": sha256(data)})
    cache_text = cache_data.decode("utf-8", "strict")
    config_values = [line for line in cache_text.splitlines()
                     if line.startswith(("CMAKE_BUILD_TYPE:", "CMAKE_C_COMPILER:",
                                         "CMAKE_GENERATOR:", "GBB_BUILD_"))]
    if not config_values:
        raise ReportError("build-config-unavailable")
    input_by_path = {row["path"]: row["sha256"] for row in input_hashes}
    mooneye_manifest = bounded_json(ROOT / "fixtures/mooneye-cgb/manifest.json", 4 * 1024 * 1024)
    fixture_rows = mooneye_manifest.get("fixtures")
    if type(fixture_rows) is not list or len(fixture_rows) != 9:
        raise ReportError("mooneye-manifest-invalid")
    mooneye_case_ids = {}
    for row in fixture_rows:
        if (type(row) is not dict or type(row.get("source_path")) is not str or
                type(row.get("id")) is not str or row["source_path"] in mooneye_case_ids):
            raise ReportError("mooneye-manifest-invalid")
        mooneye_case_ids[row["source_path"]] = row["id"]
    expected_mooneye_sources = {item["source"]["source_path"] for item in context["cases"].values()
                                if item["case"]["suite"] == "mooneye"}
    if set(mooneye_case_ids) != expected_mooneye_sources:
        raise ReportError("mooneye-manifest-membership")
    ctest_path = shutil.which("ctest")
    if not ctest_path:
        raise ReportError("ctest-tool-unavailable")
    ctest_bytes = bounded_read(Path(ctest_path).resolve(), 256 * 1024 * 1024)
    python_bytes = bounded_read(Path(sys.executable).resolve(), 256 * 1024 * 1024)
    version_code, version_output = run_bounded(["ctest", "--version"], timeout_seconds=10)
    if version_code != 0 or not version_output.startswith(b"ctest version "):
        raise ReportError("ctest-version-unavailable")
    identity = {
        "core_revision": current_revision(),
        "covered_dirty_inputs_sha256": covered_dirty_digest(tuple(sorted(paths))),
        "build_config_sha256": sha256("\n".join(config_values).encode("utf-8")),
        "build_cache_sha256": sha256(cache_data),
        "build_artifacts": artifacts,
        "input_hashes": input_hashes,
        "inventory_sha256": sha256(bounded_read(context["inventory_path"], 8 * 1024 * 1024)),
        "model": "CGB-CPU-E selected software model",
        "hardware_qualified": False,
        "case_ids": sorted(context["cases"]),
        "ctest_names": sorted(set(context["test_names"]) | {APU_SUITE_TEST}),
        "case_ctest_names": context["test_names"],
        "aggregate_ctest_names": [APU_SUITE_TEST],
        "mooneye_manifest_sha256": input_by_path.get("fixtures/mooneye-cgb/manifest.json"),
        "mooneye_case_ids": mooneye_case_ids,
        "tools": {
            "ctest_sha256": sha256(ctest_bytes),
            "ctest_version": version_output.decode("utf-8", "strict").strip(),
            "python_sha256": sha256(python_bytes),
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
        },
        "assertion_ids": {
            cid: [row["id"] for row in item["case"]["assertion_contract"]["rows"]]
            for cid, item in sorted(context["cases"].items())
        },
    }
    identity["identity_sha256"] = sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return identity


def ctest_test_names(build_dir: Path) -> set[str]:
    command = ["ctest", "--test-dir", str(inside_root(build_dir)), "--show-only=json-v1"]
    code, output = run_bounded(command, timeout_seconds=60)
    if code != 0:
        raise ReportError("ctest-inventory-failed")
    try:
        data = json.loads(output)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ReportError("ctest-inventory-invalid") from exc
    tests = data.get("tests") if type(data) is dict else None
    if type(tests) is not list or len(tests) > 10000:
        raise ReportError("ctest-inventory-invalid")
    names = set()
    for test in tests:
        props = {row.get("name"): row.get("value") for row in test.get("properties", [])
                 if type(row) is dict}
        labels = props.get("LABELS", [])
        name = test.get("name")
        if "cgb-corpus" in labels:
            if type(name) is not str or not re.fullmatch(r"[A-Za-z0-9_.:-]+", name):
                raise ReportError("ctest-name-invalid")
            if name in names:
                raise ReportError("ctest-name-duplicate")
            names.add(name)
    return names


def build_stamp_path(build_dir: Path) -> Path:
    return inside_root(build_dir) / "cgb-corpus-build-stamp.json"


def write_build_stamp(build_dir: Path) -> dict:
    context = load_corpus_context()
    identity = full_build_identity(build_dir, context)
    stamp = {
        "schema": BUILD_STAMP_SCHEMA,
        "input_identity_sha256": identity["identity_sha256"],
        "core_revision": identity["core_revision"],
        "build_artifacts": identity["build_artifacts"],
        "case_ids": identity["case_ids"],
        "ctest_names": identity["ctest_names"],
    }
    write_receipt(build_stamp_path(build_dir), stamp)
    return stamp


def verify_build_stamp(build_dir: Path, identity: dict) -> dict:
    stamp = bounded_json(build_stamp_path(build_dir), 4 * 1024 * 1024)
    if (stamp.get("schema") != BUILD_STAMP_SCHEMA or
            stamp.get("input_identity_sha256") != identity.get("identity_sha256") or
            stamp.get("core_revision") != identity.get("core_revision") or
            stamp.get("build_artifacts") != identity.get("build_artifacts") or
            stamp.get("case_ids") != identity.get("case_ids") or
            stamp.get("ctest_names") != identity.get("ctest_names")):
        raise ReportError("build-input-stamp-mismatch")
    return stamp


def begin_corpus_run(build_dir: Path, receipt_path: Path) -> dict:
    context = load_corpus_context()
    identity = full_build_identity(build_dir, context)
    expected_names = set(context["test_names"]) | {APU_SUITE_TEST}
    if set(identity["ctest_names"]) != expected_names or ctest_test_names(build_dir) != expected_names:
        raise ReportError("ctest-expected-membership")
    verify_build_stamp(build_dir, identity)
    inventory_code, _ = run_bounded(
        [sys.executable, "-I", str(ROOT / "tests/scripts/verify-cgb-corpus-inventory.py"), "--selection-only"],
        timeout_seconds=60)
    if inventory_code != 0:
        raise ReportError("inventory-contract-invalid")
    nonce = secrets.token_hex(16)
    started_ns = time.time_ns()
    build_dir = inside_root(build_dir)
    junit_path = build_dir / f"cgb-corpus-ctest-{nonce}.xml"
    metadata = {
        "schema": RUN_ID_SCHEMA,
        "status": "running",
        "run_nonce": nonce,
        "started_at_ns": started_ns,
        "input_identity_sha256": identity["identity_sha256"],
        "build_stamp_sha256": sha256(bounded_read(build_stamp_path(build_dir), 4 * 1024 * 1024)),
        "ctest_names": sorted(expected_names),
        "junit_path": junit_path.relative_to(ROOT).as_posix(),
        "ctest_xml_path": "",
    }
    write_receipt(build_dir / "cgb-corpus-run.json", metadata)
    incomplete = receipt_base("ctest-run-in-progress")
    incomplete["identity"] = {
        "input_identity_sha256": identity["identity_sha256"],
        "build_stamp_sha256": metadata["build_stamp_sha256"],
        "run_nonce_sha256": sha256(nonce.encode("ascii")),
        "ctest_names": sorted(expected_names),
    }
    write_receipt(inside_root(receipt_path), incomplete)
    return metadata


def parse_ctest_xml(data: bytes, expected_names: set[str]) -> tuple[list[dict], int]:
    if len(data) > MAX_CTEST_XML_BYTES:
        raise ReportError("ctest-xml-too-large")
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ReportError("ctest-xml-invalid")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ReportError("ctest-xml-invalid") from exc
    tests = [node for node in root.iter()
             if node.tag.rsplit("}", 1)[-1] == "Test" and
             (node.get("Status") is not None or node.find("Name") is not None)]
    if not tests or len(tests) > MAX_CTEST_TESTS:
        raise ReportError("ctest-xml-incomplete")
    blocks = []
    names = set()
    for test in tests:
        name = test.findtext("Name")
        status = test.get("Status")
        if (type(name) is not str or not re.fullmatch(r"[A-Za-z0-9_.:-]+", name) or
                name in names or status not in ("passed", "failed", "notrun")):
            raise ReportError("ctest-xml-test-identity")
        names.add(name)
        output = ""
        if name in expected_names:
            if status != "passed":
                raise ReportError("ctest-test-failed")
            measurements = [measurement for measurement in test.iter()
                            if measurement.tag.rsplit("}", 1)[-1] == "Measurement" and
                            measurement.get("name") in (None, "Test Output")]
            if len(measurements) != 1:
                raise ReportError("ctest-xml-output-membership")
            value = next((child for child in measurements[0]
                          if child.tag.rsplit("}", 1)[-1] == "Value"), None)
            if value is None:
                raise ReportError("ctest-xml-output-membership")
            output = value.text or ""
            if len(output.encode("utf-8")) > MAX_STREAM_BYTES:
                raise ReportError("captured-stream-too-large")
            blocks.append({"name": name, "passed": True, "output": output})
    if not expected_names <= names or {block["name"] for block in blocks} != expected_names:
        raise ReportError("ctest-xml-membership")
    return blocks, len(tests)


def verify_junit(data: bytes, expected_names: set[str]) -> None:
    if len(data) > MAX_CTEST_XML_BYTES:
        raise ReportError("ctest-junit-too-large")
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ReportError("ctest-junit-invalid")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ReportError("ctest-junit-invalid") from exc
    cases = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "testcase"]
    names = []
    for case in cases:
        name = case.get("name")
        if type(name) is not str or not name:
            raise ReportError("ctest-junit-test-identity")
        names.append(name)
        if name in expected_names and any(
                child.tag.rsplit("}", 1)[-1] in ("failure", "error", "skipped") for child in case):
            raise ReportError("ctest-test-failed")
    if len(names) != len(set(names)) or not expected_names <= set(names):
        raise ReportError("ctest-junit-membership")


def load_ctest_run(build_dir: Path, identity: dict, expected_names: set[str]) -> tuple[bytes, bytes, dict]:
    build_dir = inside_root(build_dir)
    run_path = build_dir / "cgb-corpus-run.json"
    metadata = bounded_json(run_path, 1024 * 1024)
    nonce = metadata.get("run_nonce")
    if (metadata.get("schema") != RUN_ID_SCHEMA or metadata.get("status") != "running" or
            type(nonce) is not str or not re.fullmatch(r"[0-9a-f]{32}", nonce) or
            type(metadata.get("started_at_ns")) is not int or
            metadata.get("input_identity_sha256") != identity["identity_sha256"] or
            metadata.get("ctest_names") != sorted(expected_names)):
        raise ReportError("ctest-run-identity-mismatch")
    stamp_data = bounded_read(build_stamp_path(build_dir), 4 * 1024 * 1024)
    if metadata.get("build_stamp_sha256") != sha256(stamp_data):
        raise ReportError("ctest-run-identity-mismatch")
    junit_path = inside_root(ROOT / validate_relative_path(metadata.get("junit_path"), "ctest-junit-path-invalid"))
    if junit_path != build_dir / f"cgb-corpus-ctest-{nonce}.xml":
        raise ReportError("ctest-junit-path-invalid")
    tag_path = build_dir / "Testing" / "TAG"
    tag_data = bounded_read(tag_path, 256).decode("ascii", "strict")
    tag_lines = tag_data.splitlines()
    tag = tag_lines[0].strip() if tag_lines else ""
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", tag):
        raise ReportError("ctest-tag-invalid")
    ctest_xml_path = build_dir / "Testing" / tag / "Test.xml"
    ctest_xml_data = bounded_read(ctest_xml_path, MAX_CTEST_XML_BYTES)
    junit_data = bounded_read(junit_path, MAX_CTEST_XML_BYTES)
    started_ns = metadata["started_at_ns"]
    if any(path.stat().st_mtime_ns < started_ns for path in (ctest_xml_path, junit_path)):
        raise ReportError("ctest-run-stale")
    blocks, total_tests = parse_ctest_xml(ctest_xml_data, expected_names)
    verify_junit(junit_data, expected_names)
    metadata["ctest_xml_path"] = repo_path(ctest_xml_path)
    metadata["test_xml_sha256"] = sha256(ctest_xml_data)
    metadata["junit_sha256"] = sha256(junit_data)
    metadata["status"] = "complete"
    metadata["ctest_exit_code"] = 0
    metadata["completed_at_ns"] = time.time_ns()
    metadata["ctest_total_cases"] = total_tests
    metadata["run_id"] = _run_id(identity["identity_sha256"], metadata["test_xml_sha256"],
                                 started_ns, metadata["completed_at_ns"])
    write_receipt(run_path, metadata)
    metadata["selected_blocks"] = blocks
    return ctest_xml_data, junit_data, metadata


def parse_ctest_log(data: bytes, expected_names: set[str]) -> tuple[list[dict], int]:
    if len(data) > MAX_RUN_LOG_BYTES:
        raise ReportError("ctest-log-too-large")
    try:
        text = data.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise ReportError("ctest-log-encoding") from exc
    if not re.search(r"100% tests passed(?:,\s*0 tests failed)? out of\s+\d+", text):
        raise ReportError("ctest-log-incomplete")
    blocks = []
    current = None
    denominator = None
    start_re = re.compile(r"^\s*Start\s+(\d+):\s+([A-Za-z0-9_.:-]+)\s*$")
    finish_re = re.compile(
        r"^\s*(\d+)/(\d+)\s+Test\s+#(\d+):\s+([A-Za-z0-9_.:-]+)\s+.*?\b(Passed|Failed|Not Run)\b"
    )
    for line in text.splitlines():
        if len(line.encode("utf-8")) > 65536:
            raise ReportError("ctest-log-line-too-large")
        if re.fullmatch(r"test\s+\d+", line.strip()):
            if current is not None:
                raise ReportError("ctest-log-test-truncated")
            current = {"start_id": None, "name": None, "output_lines": [], "passed": None}
            continue
        match = start_re.match(line)
        if match:
            if current is None or current["start_id"] is not None:
                raise ReportError("ctest-log-test-start")
            current["start_id"] = int(match.group(1))
            current["name"] = match.group(2)
            continue
        match = finish_re.match(line)
        if match:
            if current is None or current["start_id"] is None or current["passed"] is not None:
                raise ReportError("ctest-log-test-finish")
            _, total, test_id, name, status = match.groups()
            if int(test_id) != current["start_id"] or name != current["name"]:
                raise ReportError("ctest-log-test-identity")
            if denominator is not None and denominator != int(total):
                raise ReportError("ctest-log-denominator-changed")
            denominator = int(total)
            current["passed"] = status == "Passed"
            current["output"] = "\n".join(current["output_lines"])
            del current["output_lines"]
            blocks.append(current)
            current = None
            continue
        if current is not None and current["start_id"] is not None and current["passed"] is None:
            prefix = re.match(r"^(\d+): ?(.*)$", line)
            if prefix and int(prefix.group(1)) == current["start_id"]:
                current["output_lines"].append(prefix.group(2))
    if current is not None or denominator is None:
        raise ReportError("ctest-log-test-truncated")
    names = [block["name"] for block in blocks]
    if denominator != len(blocks) or len(names) != len(set(names)):
        raise ReportError("ctest-log-membership")
    if set(names) != expected_names:
        raise ReportError("ctest-log-membership")
    if any(block["passed"] is not True for block in blocks):
        raise ReportError("ctest-test-failed")
    if denominator <= 0:
        raise ReportError("ctest-log-membership")
    return blocks, denominator


def parse_kv_fields(line: str, prefix: str) -> dict:
    if len(line.encode("utf-8")) > MAX_EVENT_BYTES or not line.startswith(prefix):
        raise ReportError("event-line-invalid")
    fields = {}
    for token in line[len(prefix):].split():
        if "=" not in token:
            raise ReportError("event-token-invalid")
        key, value = token.split("=", 1)
        if (not re.fullmatch(r"[a-z][a-z0-9_]*", key) or not value or
                key in fields or len(value) > MAX_EVENT_BYTES):
            raise ReportError("event-token-invalid")
        fields[key] = value
    return fields


def lines_with_prefix(output: str, prefix: str) -> list[str]:
    return [line for line in output.splitlines() if line.startswith(prefix)]


def case_expected_xfail(item: dict) -> bool:
    return item["case"]["evaluator_disposition"].get("state") == "expected-failure"


def expected_signature(item: dict) -> str | None:
    evaluator = item["case"].get("evaluator_disposition", {})
    signature = evaluator.get("signature_sha256")
    if signature is None:
        signature = item["case"].get("execution", {}).get("signature_sha256")
    return signature if type(signature) is str else None


def validate_case_outcome(item: dict, observed: str, evaluator_status: str,
                          signature: str | None = None) -> bool:
    if observed not in ("pass", "fail") or evaluator_status not in ("pass", "xfail"):
        raise ReportError("case-result-invalid")
    if case_expected_xfail(item):
        expected = expected_signature(item)
        if observed != "fail" or evaluator_status != "xfail":
            raise ReportError("expected-failure-disposition-mismatch")
        if expected is not None and signature != expected:
            raise ReportError("expected-failure-signature-mismatch")
        return True
    if observed != "pass" or evaluator_status != "pass":
        raise ReportError("unexpected-case-result")
    return False


def _case_record(item: dict, assertions: list[dict], observed: str,
                 evaluator_status: str, details: dict | None = None,
                 signature: str | None = None) -> dict:
    case = item["case"]
    if (case.get("model") != "CGB-CPU-E" or case.get("mode") not in ("native", "compat") or
            case.get("speed") not in ("normal", "double")):
        raise ReportError("case-profile-mismatch")
    matched_xfail = validate_case_outcome(item, observed, evaluator_status, signature)
    output = item["output"]
    source = item["source"]
    return {
        "id": case["id"],
        "suite": case["suite"],
        "test_name": case["test_binding"]["ctest_name"],
        "model": case["model"],
        "mode": case["mode"],
        "speed": case["speed"],
        "expected_disposition": "pass",
        "evaluator_disposition": case["evaluator_disposition"].get("value"),
        "attempted": True,
        "completed": True,
        "observed_result": observed,
        "evaluator_status": evaluator_status,
        "matched_xfail": matched_xfail,
        "assertions": assertions,
        "details": details or {},
        "evidence": {
            "source_id": case["source_id"],
            "source_path": source["source_path"],
            "source_revision": source.get("source_commit"),
            "output_id": output["id"],
            "output_path": output["output_path"],
            "output_sha256": output["sha256"],
            "manifest_ref": output.get("manifest_ref"),
        },
    }


def _normalize_age_rows(item: dict, output: str) -> dict:
    case = item["case"]
    verdict_lines = lines_with_prefix(output, "age verdict=")
    row_lines = lines_with_prefix(output, "age-assertion-row ")
    contracts = case["assertion_contract"]["rows"]
    if len(verdict_lines) != 1 or len(row_lines) != len(contracts):
        raise ReportError("age-row-membership")
    verdict = parse_kv_fields(verdict_lines[0], "age ")
    expected_ids = {row["id"] for row in contracts}
    rows_by_id = {}
    for line in row_lines:
        fields = parse_kv_fields(line, "age-assertion-row ")
        row_id = fields.get("id")
        if row_id not in expected_ids or row_id in rows_by_id:
            raise ReportError("age-row-id-membership")
        expected_hex = fields.get("expected", "")
        actual_hex = fields.get("actual", "")
        disposition = fields.get("disposition")
        if (not re.fullmatch(r"[0-9A-Fa-f]{16}", expected_hex) or
                not re.fullmatch(r"[0-9A-Fa-f]{16}", actual_hex) or
                disposition not in ("pass", "fail")):
            raise ReportError("age-row-value-invalid")
        rows_by_id[row_id] = (fields, expected_hex.lower(), actual_hex.lower())
    if set(rows_by_id) != expected_ids:
        raise ReportError("age-row-membership")

    result_rows = []
    for contract in contracts:
        fields, expected_hex, actual_hex = rows_by_id[contract["id"]]
        declared_hex = contract.get("expected_hex")
        if declared_hex is not None and expected_hex != declared_hex.lower():
            raise ReportError("age-source-expectation-mismatch")
        actual_result = "pass" if expected_hex == actual_hex else "fail"
        if fields["disposition"] != actual_result:
            raise ReportError("age-row-disposition-mismatch")
        result_rows.append({
            "id": contract["id"],
            "expected_disposition": contract["expected_disposition"],
            "expected_hex": expected_hex,
            "observed_hex": actual_hex,
            "observed_result": actual_result,
            "evaluator_status": "xfail" if actual_result == "fail" and case_expected_xfail(item) else "pass",
        })
    row_passes = sum(row["observed_result"] == "pass" for row in result_rows)
    row_mask = sum(1 << i for i, row in enumerate(result_rows) if row["observed_result"] == "pass")
    match = re.fullmatch(r"(pass|fail) rows_ok=(\d+)/(\d+) mask=([0-9A-Fa-f]+) signature=([0-9a-f]{64}) half_dots=(\d+)", verdict_lines[0][len("age verdict="):])
    if not match:
        raise ReportError("age-verdict-invalid")
    observed, passed_text, total_text, mask_text, signature, ticks_text = match.groups()
    ticks = int(ticks_text)
    if (int(passed_text) != row_passes or int(total_text) != len(contracts) or
            int(mask_text, 16) != row_mask or observed != ("pass" if row_passes == len(contracts) else "fail") or
            ticks <= 0 or ticks > int(case.get("execution", {}).get("budget_half_dots", 0))):
        raise ReportError("age-verdict-count-mismatch")
    expected_fail = case_expected_xfail(item)
    if expected_fail != (observed == "fail"):
        raise ReportError("age-case-disposition-mismatch")
    if expected_fail and signature != expected_signature(item):
        raise ReportError("expected-failure-signature-mismatch")
    return _case_record(item, result_rows, observed, "xfail" if expected_fail else "pass",
                        {"passed_assertions": row_passes, "assertion_mask": mask_text.lower(),
                         "ticks": ticks, "budget_half_dots": int(case["execution"]["budget_half_dots"])},
                        signature)


def _normalize_age_image(item: dict, output: str) -> dict:
    case = item["case"]
    lines = lines_with_prefix(output, "age-m3 protocol=")
    if len(lines) != 1:
        raise ReportError("age-image-terminal-membership")
    fields = parse_kv_fields(lines[0], "age-m3 ")
    contract = case["assertion_contract"]["rows"]
    if len(contract) != 1:
        raise ReportError("age-image-contract")
    row = contract[0]
    if (fields.get("case") != Path(item["output"]["output_path"]).stem or
            fields.get("model") != "CGB-E" or fields.get("observed") not in ("pass", "fail") or
            fields.get("disposition") not in ("pass", "expected-failure") or
            fields.get("speed") != case["speed"] or
            fields.get("mode") != ("native-cgb" if case["mode"] == "native" else "dmg-compatibility")):
        raise ReportError("age-image-identity-mismatch")
    try:
        pixels = int(fields["assertions"])
        mismatches = int(fields["mismatches"])
    except (KeyError, ValueError) as exc:
        raise ReportError("age-image-count-invalid") from exc
    signature = fields.get("signature")
    if (pixels != row.get("assertion_count") or mismatches < 0 or mismatches > pixels or
            not re.fullmatch(r"[0-9a-f]{64}", signature or "") or
            fields["observed"] != ("pass" if mismatches == 0 else "fail")):
        raise ReportError("age-image-result-invalid")
    expected_fail = case_expected_xfail(item)
    if fields["disposition"] != ("expected-failure" if expected_fail else "pass"):
        raise ReportError("age-image-disposition-mismatch")
    if expected_fail and signature != expected_signature(item):
        raise ReportError("expected-failure-signature-mismatch")
    result = "pass" if mismatches == 0 else "fail"
    assertion = {
        "id": row["id"],
        "expected_disposition": row["expected_disposition"],
        "observed_result": result,
        "evaluator_status": "xfail" if expected_fail else "pass",
        "pixel_count": pixels,
        "mismatch_count": mismatches,
        "signature_sha256": signature,
    }
    return _case_record(item, [assertion], result, "xfail" if expected_fail else "pass",
                        {"image_pixels": pixels, "pixel_mismatches": mismatches}, signature)


def _normalize_mooneye(item: dict, output: str, identity: dict) -> dict:
    case = item["case"]
    if (case.get("model") != "CGB-CPU-E" or case.get("mode") != "compat" or
            case.get("speed") != "normal"):
        raise ReportError("mooneye-case-profile")
    source = item["source"]
    output_row = item["output"]
    events = lines_with_prefix(output, "case=mooneye-")
    assertions = lines_with_prefix(output, "assertion case=mooneye-")
    if len(events) != 1 or len(assertions) != 1:
        raise ReportError("mooneye-terminal-membership")
    event = parse_kv_fields(events[0], "")
    assertion = parse_kv_fields(assertions[0], "assertion ")
    expected_case = identity.get("mooneye_case_ids", {}).get(source["source_path"])
    expected_xfail = case_expected_xfail(item)
    expected_observed = "fail" if expected_xfail else "pass"
    expected_status = "xfail" if expected_xfail else "pass"
    expected_reason = case.get("evaluator_disposition", {}).get("reason")
    if (type(expected_case) is not str or event.get("case") != expected_case or
            event.get("source_path") != source["source_path"] or
            event.get("source_revision") != source.get("source_commit") or
            event.get("fixture_sha256") != output_row.get("sha256") or
            event.get("manifest_sha256") != identity.get("mooneye_manifest_sha256") or
            event.get("core_revision") != identity["core_revision"] or
            event.get("runner_revision") != identity["core_revision"] or
            event.get("profile") != "CGB-CPU-E" or event.get("boot") != "skipped" or
            event.get("protocol") != "mooneye-ld-b-b" or
            event.get("eligible") != "1" or event.get("executed") != "1" or
            event.get("stop") != "protocol-result"):
        raise ReportError("mooneye-identity-mismatch")
    observed = event.get("observed", expected_observed)
    evaluator_status = event.get("status")
    if (observed != expected_observed or evaluator_status != expected_status or
            (expected_xfail and event.get("observed_disposition") != "expected-failure") or
            (expected_xfail and event.get("reason") != expected_reason) or
            (not expected_xfail and "observed_disposition" in event)):
        raise ReportError("mooneye-result-mismatch")
    if (assertion.get("case") != event.get("case") or assertion.get("id") != "ld-b-b-result" or
            assertion.get("expected") != "pass" or assertion.get("observed") != observed or
            assertion.get("evaluator_status") != evaluator_status or assertion.get("terminal") != "1"):
        raise ReportError("mooneye-assertion-mismatch")
    try:
        ticks, budget = int(event["ticks"]), int(event["budget"])
    except (KeyError, ValueError) as exc:
        raise ReportError("mooneye-budget-invalid") from exc
    expected_budget = int(case.get("execution", {}).get("budget_half_dots", 0))
    if ticks <= 0 or budget != expected_budget or ticks > budget:
        raise ReportError("mooneye-budget-exceeded")
    expected_pcs = case.get("evaluator_disposition", {})
    if (assertion.get("callback_pc") != str(expected_pcs.get("callback_pc", "")).removeprefix("0x") or
            assertion.get("result_pc") != str(expected_pcs.get("result_pc", "")).removeprefix("0x") or
            assertion.get("ticks") != str(ticks) or assertion.get("budget") != str(budget)):
        raise ReportError("mooneye-assertion-identity")
    row = case["assertion_contract"]["rows"][0]
    if row["id"] != assertion["id"]:
        raise ReportError("mooneye-assertion-identity")
    detail = {"ticks": ticks, "budget_half_dots": budget,
              "callback_pc": "0x" + assertion["callback_pc"],
              "result_pc": "0x" + assertion["result_pc"]}
    normalized_assertion = {"id": row["id"], "expected_disposition": row["expected_disposition"],
                            "observed_result": observed, "evaluator_status": evaluator_status}
    return _case_record(item, [normalized_assertion], observed, evaluator_status, detail)


def _normalize_magentests(item: dict, output: str) -> dict:
    case = item["case"]
    events = lines_with_prefix(output, "magentests guest-result ")
    if len(events) != 1:
        raise ReportError("magentests-terminal-membership")
    fields = parse_kv_fields(events[0], "magentests guest-result ")
    expected_id = case["assertion_contract"]["rows"][0]["id"]
    if (fields.get("model") != case["model"] or fields.get("mode") != case["mode"] or
            fields.get("speed") != case["speed"] or fields.get("observed") != "pass" or
            fields.get("evaluator_status") != "pass" or fields.get("terminal") != "1" or
            fields.get("assertions") != "1" or fields.get("assertion_id") != expected_id):
        raise ReportError("magentests-result-mismatch")
    if fields.get("case") not in (case["id"].removeprefix("magentests:"),
                                  case["id"].removeprefix("magentests:") + ":native",
                                  case["id"].removeprefix("magentests:") + ":compat"):
        raise ReportError("magentests-case-identity")
    assertion = {"id": expected_id, "expected_disposition": "pass",
                 "observed_result": "pass", "evaluator_status": "pass"}
    return _case_record(item, [assertion], "pass", "pass")


def _normalize_dma(item: dict, output: str) -> dict:
    case = item["case"]
    source_name = item["source"]["source_path"].split("/")[-1].removesuffix(".asm")
    pass_lines = [line for line in output.splitlines()
                  if line.startswith("samesuite-hdma pass ")]
    assertion_lines = lines_with_prefix(output, "samesuite-hdma assertion ")
    contracts = case["assertion_contract"]["rows"]
    if len(pass_lines) != 1 or len(assertion_lines) != len(contracts):
        raise ReportError("dma-terminal-membership")
    pass_fields = parse_kv_fields(pass_lines[0], "samesuite-hdma pass ")
    if (pass_fields.get("case") != source_name or pass_fields.get("model") != case["model"] or
            pass_fields.get("mode") != case["mode"] or pass_fields.get("speed") != case["speed"] or
            pass_fields.get("boot") != "bootless" or pass_fields.get("terminal") != "1"):
        raise ReportError("dma-case-identity")
    rows = {}
    for line in assertion_lines:
        fields = parse_kv_fields(line, "samesuite-hdma assertion ")
        if fields.get("case") != source_name or fields.get("id") in rows:
            raise ReportError("dma-assertion-identity")
        if fields.get("expected") != "pass" or fields.get("observed") != "pass" or fields.get("status") != "match":
            raise ReportError("dma-assertion-failed")
        rows[fields["id"]] = fields
    expected_ids = {row["id"] for row in contracts}
    if set(rows) != expected_ids:
        raise ReportError("dma-assertion-membership")
    assertions = [{"id": row["id"], "expected_disposition": row["expected_disposition"],
                   "observed_result": "pass", "evaluator_status": "pass"} for row in contracts]
    return _case_record(item, assertions, "pass", "pass")


def _normalize_apu_suite(context: dict, suite_output: str, blocks_by_name: dict) -> dict[str, dict]:
    apu_cases = {cid: item for cid, item in context["cases"].items()
                 if item["case"]["suite"] == "samesuite" and
                 item["source"]["source_path"].startswith("apu/")}
    by_alias = {}
    for cid, item in apu_cases.items():
        if (item["case"].get("model") != "CGB-CPU-E" or
                item["case"].get("mode") != "native" or item["case"].get("speed") != "normal"):
            raise ReportError("apu-case-profile")
        alias = item["source"]["source_path"].removesuffix(".asm")
        by_alias[alias] = (cid, item)
        membership_name = item["case"]["test_binding"]["ctest_name"]
        membership_output = blocks_by_name[membership_name]["output"]
        if ("TAP version 13" not in membership_output or "1..1" not in membership_output or
                "APU membership identity present" not in membership_output):
            raise ReportError("apu-membership-control")
    guest_lines = lines_with_prefix(suite_output, "samesuite-apu guest-result ")
    assertion_lines = lines_with_prefix(suite_output, "samesuite-apu assertion ")
    expected_assertions = sum(item["case"]["assertion_contract"]["count"]
                              for _, item in by_alias.values())
    if len(guest_lines) != 70 or len(assertion_lines) != expected_assertions:
        raise ReportError("apu-suite-membership")
    assertions_by_case: dict[str, dict[str, dict]] = {}
    for line in assertion_lines:
        fields = parse_kv_fields(line, "samesuite-apu assertion ")
        alias, assertion_id = fields.get("case"), fields.get("id")
        if alias not in by_alias or type(assertion_id) is not str:
            raise ReportError("apu-assertion-unknown")
        if alias in assertions_by_case and assertion_id in assertions_by_case[alias]:
            raise ReportError("apu-assertion-duplicate")
        expected = fields.get("author_expected", "")
        observed = fields.get("observed", "")
        status = fields.get("status")
        if (not re.fullmatch(r"[0-9a-fA-F]{2}", expected) or
                not re.fullmatch(r"[0-9a-fA-F]{2}", observed) or
                status not in ("match", "mismatch") or
                status != ("match" if expected.lower() == observed.lower() else "mismatch")):
            raise ReportError("apu-assertion-value-mismatch")
        assertions_by_case.setdefault(alias, {})[assertion_id] = fields

    records = {}
    for line in guest_lines:
        fields = parse_kv_fields(line, "samesuite-apu guest-result ")
        alias = fields.get("case")
        if alias not in by_alias or alias in records:
            raise ReportError("apu-case-membership")
        cid, item = by_alias[alias]
        case = item["case"]
        contracts = case["assertion_contract"]["rows"]
        rows = assertions_by_case.get(alias, {})
        if set(rows) != {row["id"] for row in contracts}:
            raise ReportError("apu-assertion-membership")
        normalized_assertions = []
        matches = 0
        for contract in contracts:
            event = rows[contract["id"]]
            if event.get("author_expected", "").lower() != str(contract.get("author_expected", "")).lower():
                raise ReportError("apu-source-expectation-mismatch")
            observed_result = "pass" if event["status"] == "match" else "fail"
            matches += observed_result == "pass"
            normalized_assertions.append({
                "id": contract["id"],
                "expected_disposition": contract["expected_disposition"],
                "author_expected": event["author_expected"].lower(),
                "observed": event["observed"].lower(),
                "observed_result": observed_result,
                "evaluator_status": "xfail" if observed_result == "fail" and case_expected_xfail(item) else "pass",
            })
        observed = "pass" if matches == len(contracts) else "fail"
        status = "pass" if observed == "pass" else "xfail"
        if (fields.get("author_expectation") != "P" or fields.get("observed") != ("P" if observed == "pass" else "F") or
                fields.get("terminal") != "1" or fields.get("evaluator_status") != status or
                fields.get("evaluator_disposition") != ("expected-failure" if status == "xfail" else "pass") or
                fields.get("test_sample_corruption") != "disabled" or
                int(fields.get("assertions", "-1")) != len(contracts) or
                fields.get("assertion_set") != ("match" if observed == "pass" else "mismatch")):
            raise ReportError("apu-case-result-mismatch")
        try:
            elapsed = int(fields["elapsed_half_dots"])
            calls = int(fields["run_calls"])
        except (KeyError, ValueError) as exc:
            raise ReportError("apu-budget-invalid") from exc
        budget = int(case.get("execution", {}).get("budget_half_dots", 0))
        if elapsed <= 0 or calls <= 0 or budget <= 0 or elapsed > budget:
            raise ReportError("apu-budget-exceeded")
        signature = fields.get("signature_sha256")
        if not re.fullmatch(r"[0-9a-f]{64}", signature or ""):
            raise ReportError("apu-signature-invalid")
        if case_expected_xfail(item) and signature != expected_signature(item):
            raise ReportError("expected-failure-signature-mismatch")
        records[cid] = _case_record(
            item, normalized_assertions, observed, status,
            {"elapsed_half_dots": elapsed, "run_calls": calls,
             "budget_half_dots": budget, "matched_assertions": matches,
             "assertion_count": len(contracts)}, signature)

    if set(records) != set(apu_cases):
        raise ReportError("apu-case-membership")
    summary = re.search(
        r"samesuite-apu suite pass cases=(\d+) pass=(\d+) xfail=(\d+) assertions=(\d+) "
        r"model=CGB-CPU-E mode=native speed=normal boot=bootless", suite_output)
    if not summary:
        raise ReportError("apu-suite-summary-missing")
    cases_count, pass_count, xfail_count, assertion_count = map(int, summary.groups())
    actual_pass = sum(record["observed_result"] == "pass" for record in records.values())
    if (cases_count != 70 or pass_count != actual_pass or xfail_count != 70 - actual_pass or
            assertion_count != expected_assertions or actual_pass == 0):
        raise ReportError("apu-suite-summary-mismatch")
    return records


def inventory_summary(context: dict) -> tuple[dict, dict]:
    source_rows = context["inventory"]["source_candidates"]
    output_rows = context["inventory"]["outputs"]
    per_suite = {}
    excluded_sources = []
    for suite in sorted({row["suite"] for row in source_rows}):
        suite_sources = [row for row in source_rows if row["suite"] == suite]
        suite_outputs = [row for row in output_rows if row["suite"] == suite]
        suite_cases = [row["case"] for row in context["cases"].values() if row["case"]["suite"] == suite]
        excluded = [row for row in suite_sources if row.get("selection", {}).get("state") == "excluded"]
        excluded_sources.extend({
            "id": row["id"], "suite": suite, "source_path": row["source_path"],
            "reason": row.get("selection", {}).get("reason", "not-selected-in-frozen-corpus"),
        } for row in excluded)
        per_suite[suite] = {
            "discovered_candidates": len(suite_sources),
            "applicable_required_cases": len(suite_cases),
            "required_eligible_cases": len(suite_cases),
            "admitted_outputs": sum(row.get("admission_status") == "admitted" for row in suite_outputs),
            "excluded_source_candidates": len(excluded),
            "not_run_required_cases": 0,
        }
    noncase_outputs = [{
        "id": row["id"], "suite": row["suite"], "output_path": row["output_path"],
        "reason": "admitted output outside the frozen required CGB case set",
    } for row in output_rows if not row.get("case_ids")]
    return ({
        "discovered_source_candidates": len(source_rows),
        "applicable_required_cases": len(context["cases"]),
        "admitted_outputs": sum(row.get("admission_status") == "admitted" for row in output_rows),
        "required_eligible_cases": len(context["cases"]),
        "excluded_source_candidates": len(excluded_sources),
        "outputs_outside_required_case_set": len(noncase_outputs),
        "by_suite": per_suite,
    }, {"excluded_source_candidates": excluded_sources, "outputs_outside_required_case_set": noncase_outputs})


def required_cohort_summary(name: str, rows: list[dict]) -> dict:
    passing = sum(row.get("observed_result") == "pass" for row in rows)
    if not rows or passing == 0:
        raise ReportError("required-cohort-empty-or-all-xfail")
    return {
        "name": name,
        "required_cases": len(rows),
        "observed_pass_cases": passing,
        "matched_xfail_cases": sum(row.get("matched_xfail") is True for row in rows),
    }


def normalize_corpus(context: dict, blocks: list[dict], identity: dict) -> dict:
    blocks_by_name = {block["name"]: block for block in blocks}
    expected_names = set(context["test_names"]) | {APU_SUITE_TEST}
    if set(blocks_by_name) != expected_names or len(blocks_by_name) != len(blocks):
        raise ReportError("case-ctest-membership")
    apu_records = _normalize_apu_suite(context, blocks_by_name[APU_SUITE_TEST]["output"], blocks_by_name)
    records = {}
    for case_id, item in context["cases"].items():
        case = item["case"]
        suite = case["suite"]
        if suite == "samesuite" and item["source"]["source_path"].startswith("apu/"):
            record = apu_records[case_id]
        else:
            block = blocks_by_name[case["test_binding"]["ctest_name"]]
            if suite == "age":
                record = (_normalize_age_image(item, block["output"]) if case_id.startswith("age:m3-")
                          else _normalize_age_rows(item, block["output"]))
            elif suite == "mooneye":
                record = _normalize_mooneye(item, block["output"], identity)
            elif suite == "magentests":
                record = _normalize_magentests(item, block["output"])
            elif suite == "samesuite":
                record = _normalize_dma(item, block["output"])
            else:
                raise ReportError("case-suite-unknown")
        if record["id"] != case_id or case_id in records:
            raise ReportError("case-result-membership")
        records[case_id] = record
    if set(records) != set(context["cases"]):
        raise ReportError("case-result-membership")

    expected_counts = {"age": 19, "magentests": 5, "mooneye": 9, "samesuite": 74}
    suite_summary = []
    for suite, expected_count in expected_counts.items():
        suite_rows = [row for row in records.values() if row["suite"] == suite]
        if len(suite_rows) != expected_count:
            raise ReportError("suite-case-count-mismatch")
        suite_assertions = [assertion for row in suite_rows for assertion in row["assertions"]]
        passed = sum(row["observed_result"] == "pass" for row in suite_rows)
        failed = len(suite_rows) - passed
        completed = sum(row["completed"] is True for row in suite_rows)
        matched = sum(row["matched_xfail"] is True for row in suite_rows)
        if completed != expected_count or passed == 0 or matched != failed:
            raise ReportError("suite-qualification-incomplete")
        suite_summary.append({
            "suite": suite,
            "discovered_candidates": len([s for s in context["inventory"]["source_candidates"] if s["suite"] == suite]),
            "applicable_cases": expected_count,
            "admitted_cases": expected_count,
            "required_eligible_cases": expected_count,
            "attempted_cases": sum(row["attempted"] is True for row in suite_rows),
            "completed_cases": completed,
            "observed_pass_cases": passed,
            "observed_fail_cases": failed,
            "matched_xfail_cases": matched,
            "excluded_cases": 0,
            "not_run_cases": 0,
            "assertions": len(suite_assertions),
            "passing_assertions": sum(row["observed_result"] == "pass" for row in suite_assertions),
            "failing_assertions": sum(row["observed_result"] == "fail" for row in suite_assertions),
            "image_pixels": sum(int(row["details"].get("image_pixels", 0)) for row in suite_rows),
            "pixel_mismatches": sum(int(row["details"].get("pixel_mismatches", 0)) for row in suite_rows),
        })
    apu_rows = [row for row in records.values() if row["evidence"]["source_path"].startswith("apu/")]
    dma_rows = [row for row in records.values() if row["evidence"]["source_path"].startswith("dma/")]
    required_cohorts = {
        "age-row-contracts": [row for row in records.values() if row["suite"] == "age" and not row["id"].startswith("age:m3-")],
        "magentests-source-predicates": [row for row in records.values() if row["suite"] == "magentests"],
        "mooneye-cgb-cases": [row for row in records.values() if row["suite"] == "mooneye"],
        "samesuite-apu-original-assertions": apu_rows,
        "samesuite-dma-source-assertions": dma_rows,
    }
    cohort_report = []
    for name, rows in required_cohorts.items():
        cohort_report.append(required_cohort_summary(name, rows))
    inventory_counts, exclusions = inventory_summary(context)
    all_assertions = [assertion for row in records.values() for assertion in row["assertions"]]
    case_counts = {
        "applicable_cases": len(records),
        "admitted_cases": len(records),
        "required_eligible_cases": len(records),
        "attempted_cases": sum(row["attempted"] for row in records.values()),
        "completed_cases": sum(row["completed"] for row in records.values()),
        "observed_pass_cases": sum(row["observed_result"] == "pass" for row in records.values()),
        "observed_fail_cases": sum(row["observed_result"] == "fail" for row in records.values()),
        "matched_xfail_cases": sum(row["matched_xfail"] for row in records.values()),
        "excluded_cases": 0,
        "not_run_cases": 0,
        "assertions": len(all_assertions),
        "passing_assertions": sum(row["observed_result"] == "pass" for row in all_assertions),
        "failing_assertions": sum(row["observed_result"] == "fail" for row in all_assertions),
        "image_pixels": sum(int(row["details"].get("image_pixels", 0)) for row in records.values()),
        "pixel_mismatches": sum(int(row["details"].get("pixel_mismatches", 0)) for row in records.values()),
    }
    if (case_counts["attempted_cases"] != len(records) or case_counts["completed_cases"] != len(records) or
            case_counts["observed_pass_cases"] + case_counts["observed_fail_cases"] != len(records) or
            case_counts["matched_xfail_cases"] != case_counts["observed_fail_cases"] or
            case_counts["assertions"] != context["assertion_rows"]):
        raise ReportError("case-assertion-count-reconciliation")
    return {
        "schema": SCHEMA,
        "version": 1,
        "status": "complete",
        "failure_codes": [],
        "identity": identity,
        "inventory": inventory_counts,
        "exclusions": exclusions,
        "counts": case_counts,
        "suite_summary": suite_summary,
        "required_behavior_cohorts": cohort_report,
        "cases": [records[cid] for cid in sorted(records)],
    }


def parse_event(stream: bytes, contract: dict, core_revision: str | None = None) -> dict:
    if len(stream) > MAX_STREAM_BYTES:
        raise ReportError("captured-stream-too-large")
    lines = stream.splitlines()
    events = [line for line in lines if line.startswith(b"case=")]
    if len(events) != 1 or len(events[0]) > MAX_EVENT_BYTES:
        raise ReportError("case-event-membership")
    try:
        tokens = events[0].decode("ascii", "strict").split()
    except UnicodeDecodeError as exc:
        raise ReportError("event-encoding") from exc
    fields = {}
    for token in tokens:
        if "=" not in token:
            raise ReportError("event-token")
        key, value = token.split("=", 1)
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key) or key in fields or not value:
            raise ReportError("event-token")
        fields[key] = value
    expected = {
        "case": "mooneye-acceptance-instr-daa",
        "category": "instruction",
        "status": "pass",
        "manifest_sha256": contract["manifest_sha256"],
        "source_revision": PINS["source_revision"],
        "source_tree": PINS["source_tree_sha1"],
        "report_patch_sha256": PINS["report_patch_sha256"],
        "source_path": PINS["source_path"],
        "original_rom_sha256": PINS["original_rom_sha256"],
        "fixture_sha256": PINS["fixture_sha256"],
        "core_revision": core_revision or current_revision(),
        "runner_revision": core_revision or current_revision(),
        "profile": "CGB-CPU-E",
        "boot": "skipped",
        "protocol": "mooneye-ld-b-b",
        "protocol_stage": "callback-then-ld-b-b",
        "callback_result": "pass",
        "callback_pc": PINS["callback_pc"],
        "result_pc": PINS["result_pc"],
        "eligible": "1",
        "executed": "1",
    }
    for key, value in expected.items():
        if fields.get(key) != value:
            raise ReportError("event-identity-mismatch")
    if fields.get("build_qualified") not in ("true", "false"):
        raise ReportError("event-build-qualification-invalid")
    if not re.fullmatch(r"[0-9]{1,10}", fields.get("ticks", "")) or int(fields["ticks"]) <= 0:
        raise ReportError("event-ticks-invalid")
    if not re.fullmatch(r"[0-9]{1,10}", fields.get("budget", "")) or int(fields["budget"]) != PINS["budget"]:
        raise ReportError("event-budget-mismatch")
    if int(fields["ticks"]) > int(fields["budget"]):
        raise ReportError("event-budget-exceeded")
    return {
        "case": fields["case"],
        "status": "pass",
        "observed_result": "pass",
        "evaluator_status": "pass",
        "callback_result": fields["callback_result"],
        "callback_pc": "0x" + fields["callback_pc"],
        "result_pc": "0x" + fields["result_pc"],
        "ticks": int(fields["ticks"]),
        "budget_half_dots": int(fields["budget"]),
        "terminal": True,
        "build_qualified": fields["build_qualified"] == "true",
    }


def _read_bounded_pipe_chunk(stream) -> bytes:
    return stream.read1(65536)


def _queue_reader_event(events, stop_event, event) -> bool:
    while not stop_event.is_set():
        try:
            events.put(event, timeout=0.1)
            return True
        except queue.Full:
            continue
    return False


def _threaded_pipe_reader(stream, events, stop_event) -> None:
    while not stop_event.is_set():
        try:
            chunk = _read_bounded_pipe_chunk(stream)
        except (OSError, ValueError) as exc:
            _queue_reader_event(events, stop_event, ("error", exc))
            return
        if not chunk:
            _queue_reader_event(events, stop_event, ("eof", None))
            return
        if not _queue_reader_event(events, stop_event, ("chunk", chunk)):
            return


def _terminate_bounded_process(proc) -> None:
    if os.name == "posix":
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    elif os.name == "nt":
        try:
            subprocess.run(
                ["taskkill.exe", "/PID", str(proc.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=2, check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass
    try:
        proc.kill()
    except OSError:
        pass
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except OSError:
            pass
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired as exc:
            raise ReportError("runner-cleanup-failed") from exc


def _cancel_windows_reader(reader) -> None:
    if os.name != "nt" or reader.native_id is None:
        return
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        open_thread = kernel32.OpenThread
        open_thread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        open_thread.restype = wintypes.HANDLE
        cancel_io = kernel32.CancelSynchronousIo
        cancel_io.argtypes = [wintypes.HANDLE]
        cancel_io.restype = wintypes.BOOL
        close_handle = kernel32.CloseHandle
        close_handle.argtypes = [wintypes.HANDLE]
        close_handle.restype = wintypes.BOOL
        handle = open_thread(0x0001, False, reader.native_id)  # THREAD_TERMINATE
        if handle:
            try:
                cancel_io(handle)
            finally:
                close_handle(handle)
    except (AttributeError, OSError):
        pass


def _run_bounded_threaded(proc, deadline: float) -> tuple[int, bytes]:
    assert proc.stdout is not None
    output = bytearray()
    events = queue.Queue(maxsize=2)
    stop_event = threading.Event()
    reader = threading.Thread(target=_threaded_pipe_reader,
                              args=(proc.stdout, events, stop_event), daemon=True)
    reader_started = False
    completed = False
    try:
        reader.start()
        reader_started = True
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ReportError("runner-timeout")
            try:
                kind, value = events.get(timeout=min(remaining, 0.25))
            except queue.Empty:
                continue
            if kind == "error":
                raise ReportError("runner-output-read-failed") from value
            if kind == "eof":
                break
            if len(output) + len(value) > MAX_STREAM_BYTES:
                raise ReportError("captured-stream-too-large")
            output.extend(value)
            if not value:
                break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ReportError("runner-timeout")
        try:
            return_code = proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired as exc:
            raise ReportError("runner-timeout") from exc
        completed = True
        return return_code, bytes(output)
    finally:
        stop_event.set()
        if not completed:
            _terminate_bounded_process(proc)
        if reader_started:
            reader.join(timeout=2)
            if reader.is_alive():
                _cancel_windows_reader(reader)
                reader.join(timeout=1)
        if not reader.is_alive():
            proc.stdout.close()


def run_bounded(command: list[str], timeout_seconds: int = RUN_TIMEOUT_SECONDS) -> tuple[int, bytes]:
    try:
        proc = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, close_fds=True,
                                start_new_session=(os.name == "posix"))
    except OSError as exc:
        raise ReportError("runner-start-failed") from exc
    assert proc.stdout is not None
    deadline = time.monotonic() + timeout_seconds
    if os.name == "nt":
        return _run_bounded_threaded(proc, deadline)
    output = bytearray()
    selector = None
    completed = False
    try:
        selector = selectors.DefaultSelector()
        selector.register(proc.stdout, selectors.EVENT_READ)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ReportError("runner-timeout")
            ready = selector.select(min(remaining, 0.25))
            if ready:
                try:
                    chunk = os.read(proc.stdout.fileno(), 65536)
                except OSError as exc:
                    raise ReportError("runner-output-read-failed") from exc
                if not chunk:
                    selector.unregister(proc.stdout)
                else:
                    if len(output) + len(chunk) > MAX_STREAM_BYTES:
                        raise ReportError("captured-stream-too-large")
                    output.extend(chunk)
            if proc.poll() is not None and not selector.get_map():
                completed = True
                break
        return proc.returncode, bytes(output)
    except (OSError, ValueError) as exc:
        raise ReportError("runner-output-read-failed") from exc
    finally:
        if selector is not None:
            selector.close()
        if not completed:
            _terminate_bounded_process(proc)
        proc.stdout.close()


def receipt_base(reason: str) -> dict:
    return {
        "schema": SCHEMA,
        "version": 1,
        "status": "incomplete",
        "failure_codes": [reason],
        "identity": {},
        "counts": {
            "eligible_cases": 0,
            "attempted_cases": 0,
            "completed_cases": 0,
            "observed_pass_cases": 0,
            "observed_fail_cases": 0,
            "matched_xfail_cases": 0,
            "assertions": 0,
            "passing_assertions": 0,
        },
        "cases": [],
        "suite_summary": [],
    }


def validate_event_with_identity(stream: bytes, contract: dict, identity: dict) -> dict:
    event = parse_event(stream, contract, identity["core_revision"])
    if event.get("status") != "pass" or identity.get("model") != "CGB-CPU-E":
        raise ReportError("event-result-mismatch")
    return event


def complete_receipt(contract: dict, identity: dict, event: dict) -> dict:
    case = contract["case"]
    normalized = {
        "id": DAA_ID,
        "suite": "mooneye",
        "test_name": DAA_TEST,
        "model": "CGB-CPU-E",
        "mode": "compat",
        "speed": "normal",
        "boot_policy": "skipped",
        "expected_disposition": "pass",
        "attempted": True,
        "completed": True,
        "observed_result": event["observed_result"],
        "evaluator_status": event["evaluator_status"],
        "build_qualified": event["build_qualified"],
        "ticks": event["ticks"],
        "budget_half_dots": event["budget_half_dots"],
        "assertions": [{
            "id": "ld-b-b-result",
            "expected_disposition": "pass",
            "observed_result": "pass",
            "evaluator_status": "pass",
            "callback_pc": event["callback_pc"],
            "result_pc": event["result_pc"],
        }],
        "evidence": {
            "manifest_sha256": contract["manifest_sha256"],
            "rom_sha256": contract["rom_sha256"],
            "fixture_sha256": PINS["fixture_sha256"],
            "source_path": PINS["source_path"],
        },
    }
    if case.get("id") != normalized["id"] or len(normalized["assertions"]) != 1:
        raise ReportError("normalized-membership")
    return {
        "schema": SCHEMA,
        "version": 1,
        "status": "complete",
        "failure_codes": [],
        "identity": identity,
        "counts": {
            "eligible_cases": 1,
            "attempted_cases": 1,
            "completed_cases": 1,
            "observed_pass_cases": 1,
            "observed_fail_cases": 0,
            "matched_xfail_cases": 0,
            "assertions": 1,
            "passing_assertions": 1,
        },
        "cases": [normalized],
        "suite_summary": [{
            "suite": "mooneye",
            "eligible_cases": 1,
            "attempted_cases": 1,
            "completed_cases": 1,
            "observed_pass_cases": 1,
            "observed_fail_cases": 0,
            "assertions": 1,
            "passing_assertions": 1,
        }],
    }


def write_receipt(path: Path, receipt: dict) -> None:
    path = inside_root(path)
    encoded = (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if len(encoded) > MAX_RECEIPT_BYTES:
        raise ReportError("receipt-too-large")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".cgb-receipt-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def build_tracer_report(build_dir: Path) -> dict:
    contract = load_daa_contract()
    identity = build_identity(build_dir, contract)
    runner = build_executable_path(inside_root(build_dir), "gabbaboy-runner")
    command = [str(runner), "--manifest", str(contract["manifest_path"]),
               "--case", "daa", "--profile", "cgb", "--receipt"]
    return_code, stream = run_bounded(command)
    if return_code != 0:
        raise ReportError("runner-nonzero")
    event = validate_event_with_identity(stream, contract, identity)
    return complete_receipt(contract, identity, event)


def write_bytes_atomic(path: Path, data: bytes, limit: int) -> None:
    path = inside_root(path)
    if len(data) > limit:
        raise ReportError("run-artifact-too-large")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".cgb-run-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def _run_id(identity_sha256: str, log_sha256: str, started_ns: int, completed_ns: int) -> str:
    value = {"input_identity_sha256": identity_sha256, "log_sha256": log_sha256,
             "started_at_ns": started_ns, "completed_at_ns": completed_ns}
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii"))


def _load_existing_ctest_run(build_dir: Path, identity: dict, expected_names: set[str]) -> tuple[bytes, dict]:
    build_dir = inside_root(build_dir)
    log_path = build_dir / "cgb-corpus-ctest.log"
    run_path = build_dir / "cgb-corpus-run.json"
    log_data = bounded_read(log_path, MAX_RUN_LOG_BYTES)
    metadata = bounded_json(run_path, 1024 * 1024)
    if (metadata.get("schema") != RUN_ID_SCHEMA or metadata.get("status") != "complete" or
            type(metadata.get("started_at_ns")) is not int or
            type(metadata.get("completed_at_ns")) is not int or
            metadata.get("ctest_exit_code") != 0 or
            metadata.get("input_identity_sha256") != identity["identity_sha256"] or
            metadata.get("ctest_names") != sorted(expected_names) or
            metadata.get("log_sha256") != sha256(log_data) or
            metadata.get("run_id") != _run_id(identity["identity_sha256"], sha256(log_data),
                                                metadata["started_at_ns"], metadata["completed_at_ns"])):
        raise ReportError("ctest-run-identity-mismatch")
    return log_data, metadata


def build_corpus_report(build_dir: Path, from_ctest: bool = False) -> dict:
    context = load_corpus_context()
    identity = full_build_identity(build_dir, context)
    expected_names = set(context["test_names"]) | {APU_SUITE_TEST}
    if set(identity["ctest_names"]) != expected_names:
        raise ReportError("ctest-expected-membership")
    if ctest_test_names(build_dir) != expected_names:
        raise ReportError("ctest-actual-membership")
    verify_build_stamp(build_dir, identity)
    inventory_code, _ = run_bounded(
        [sys.executable, "-I", str(ROOT / "tests/scripts/verify-cgb-corpus-inventory.py"), "--selection-only"],
        timeout_seconds=60)
    if inventory_code != 0:
        raise ReportError("inventory-contract-invalid")
    build_dir = inside_root(build_dir)
    if from_ctest:
        _, _, run_metadata = load_ctest_run(build_dir, identity, expected_names)
        blocks = run_metadata.pop("selected_blocks")
        denominator = run_metadata["ctest_total_cases"]
    else:
        started_ns = time.time_ns()
        running_metadata = {
            "schema": RUN_ID_SCHEMA,
            "status": "running",
            "ctest_exit_code": None,
            "input_identity_sha256": identity["identity_sha256"],
            "ctest_names": sorted(expected_names),
            "log_sha256": "",
            "started_at_ns": started_ns,
            "completed_at_ns": None,
            "run_id": "",
            "command": "ctest --test-dir <build-dir> -L cgb-corpus -VV --output-on-failure --parallel 1",
        }
        write_receipt(build_dir / "cgb-corpus-run.json", running_metadata)
        command = ["ctest", "--test-dir", str(build_dir), "-L", "cgb-corpus",
                   "-VV", "--output-on-failure", "--parallel", "1"]
        code, log_data = run_bounded(command, timeout_seconds=FULL_RUN_TIMEOUT_SECONDS)
        completed_ns = time.time_ns()
        log_hash = sha256(log_data)
        run_metadata = {
            "schema": RUN_ID_SCHEMA,
            "status": "complete" if code == 0 else "failed",
            "ctest_exit_code": code,
            "input_identity_sha256": identity["identity_sha256"],
            "ctest_names": sorted(expected_names),
            "log_sha256": log_hash,
            "started_at_ns": started_ns,
            "completed_at_ns": completed_ns,
            "run_id": _run_id(identity["identity_sha256"], log_hash, started_ns, completed_ns),
            "command": "ctest --test-dir <build-dir> -L cgb-corpus -VV --output-on-failure --parallel 1",
        }
        write_bytes_atomic(build_dir / "cgb-corpus-ctest.log", log_data, MAX_RUN_LOG_BYTES)
        write_receipt(build_dir / "cgb-corpus-run.json", run_metadata)
        if code != 0:
            raise ReportError("ctest-run-failed")
        blocks, denominator = parse_ctest_log(log_data, expected_names)
    if denominator < len(expected_names):
        raise ReportError("ctest-run-denominator")
    report = normalize_corpus(context, blocks, identity)
    report["run"] = {
        "id": run_metadata["run_id"],
        "started_at_ns": run_metadata["started_at_ns"],
        "completed_at_ns": run_metadata["completed_at_ns"],
        "ctest_log_sha256": run_metadata.get("test_xml_sha256", run_metadata.get("log_sha256", "")),
        "ctest_cases": len(expected_names),
        "ctest_total_cases": denominator,
        "run_nonce_sha256": sha256(run_metadata["run_nonce"].encode("ascii"))
        if type(run_metadata.get("run_nonce")) is str else "",
    }
    report["identity"]["input_identity_sha256"] = identity["identity_sha256"]
    report["identity"]["run_id"] = run_metadata["run_id"]
    report["identity"]["ctest_log_sha256"] = report["run"]["ctest_log_sha256"]
    report["identity"].pop("identity_sha256", None)
    report["identity"]["identity_sha256"] = sha256(
        json.dumps(report["identity"], sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return report


def print_corpus_summary(report: dict) -> None:
    counts = report["counts"]
    for suite in report["suite_summary"]:
        print("CGB corpus suite={} cases={}/{} observed_pass={} expected_xfail={} assertions={}/{} image_pixels={} mismatches={}".format(
            suite["suite"], suite["completed_cases"], suite["required_eligible_cases"],
            suite["observed_pass_cases"], suite["matched_xfail_cases"],
            suite["passing_assertions"], suite["assertions"],
            suite["image_pixels"], suite["pixel_mismatches"]))
    print("CGB corpus receipt status=complete cases={}/{} observed_pass={} expected_xfail={} assertions={}/{} image_pixels={} mismatches={}".format(
        counts["completed_cases"], counts["required_eligible_cases"], counts["observed_pass_cases"],
        counts["matched_xfail_cases"], counts["passing_assertions"], counts["assertions"],
        counts["image_pixels"], counts["pixel_mismatches"]))


def self_test(build_dir: Path) -> int:
    report = build_tracer_report(build_dir)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


def self_test_controls() -> int:
    contract = load_daa_contract()
    clean = (b"case=mooneye-acceptance-instr-daa category=instruction status=pass "
             b"manifest_sha256=" + PINS["manifest_sha256"].encode() +
             b" source_revision=" + PINS["source_revision"].encode() +
             b" source_tree=" + PINS["source_tree_sha1"].encode() +
             b" report_patch_sha256=" + PINS["report_patch_sha256"].encode() +
             b" source_path=" + PINS["source_path"].encode() +
             b" original_rom_sha256=" + PINS["original_rom_sha256"].encode() +
             b" fixture_sha256=" + PINS["fixture_sha256"].encode() +
             b" core_revision=" + current_revision().encode() +
             b" runner_revision=" + current_revision().encode() +
             b" build_qualified=true profile=CGB-CPU-E boot=skipped "
             b" protocol=mooneye-ld-b-b protocol_stage=callback-then-ld-b-b "
             b" callback_result=pass callback_pc=0166 result_pc=409a eligible=1 executed=1 "
             b" ticks=1805896 budget=2000000\n")
    event = parse_event(clean, contract)
    if event["observed_result"] != "pass":
        raise ReportError("clean-control-rejected")
    altered = clean.replace(PINS["manifest_sha256"].encode(), b"0" * 64, 1)
    try:
        parse_event(altered, contract)
    except ReportError as exc:
        if exc.code != "event-identity-mismatch":
            raise
    else:
        raise ReportError("altered-manifest-accepted")
    with tempfile.TemporaryDirectory(prefix="cgb-report-control-", dir=ROOT / "build") as temp:
        base = Path(temp)
        out = base / "stale-receipt.json"
        out.write_text('{"schema":"gabbaboy-cgb-corpus-receipt-v1","status":"complete"}\n',
                       encoding="utf-8")
        failed = receipt_base("runner-start-failed")
        write_receipt(out, failed)
        replaced = bounded_json(out)
        if replaced.get("status") != "incomplete" or replaced.get("failure_codes") != ["runner-start-failed"]:
            raise ReportError("stale-green-not-invalidated")
    print("cgb-corpus-report tracer-controls pass clean=1 altered=1 stale-green=1")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--self-test-controls", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--write-build-stamp", action="store_true")
    group.add_argument("--begin-run", action="store_true")
    group.add_argument("--from-ctest", action="store_true")
    parser.add_argument("--build-dir", type=Path, default=ROOT / "build")
    parser.add_argument("--receipt", type=Path, default=ROOT / "build/cgb-corpus-receipt.json")
    args = parser.parse_args()
    if args.self_test_controls:
        try:
            return self_test_controls()
        except ReportError as exc:
            print("cgb-corpus-report control failed: " + exc.code, file=sys.stderr)
            return 1
    if args.self_test:
        try:
            return self_test(args.build_dir)
        except ReportError as exc:
            print(json.dumps({**receipt_base(exc.code), "schema": SCHEMA},
                             sort_keys=True, separators=(",", ":")))
            return 1
    if args.write_build_stamp:
        try:
            stamp = write_build_stamp(args.build_dir)
            print("cgb-corpus-build-stamp pass input_identity_sha256=" + stamp["input_identity_sha256"])
            return 0
        except ReportError as exc:
            print("cgb-corpus-build-stamp failed: " + exc.code, file=sys.stderr)
            return 1
    receipt_path = args.receipt
    try:
        receipt_path = inside_root(receipt_path)
    except ReportError as exc:
        print("cgb-corpus-report failed: " + exc.code, file=sys.stderr)
        return 2
    write_receipt(receipt_path, receipt_base("execution-not-started"))
    try:
        if args.begin_run:
            metadata = begin_corpus_run(args.build_dir, receipt_path)
            print("run_nonce=" + metadata["run_nonce"])
            print("junit_path=" + metadata["junit_path"])
            return 0
        report = build_corpus_report(args.build_dir, from_ctest=args.from_ctest)
        write_receipt(receipt_path, report)
        print_corpus_summary(report)
        return 0
    except ReportError as exc:
        write_receipt(receipt_path, receipt_base(exc.code))
        print("CGB corpus receipt status=incomplete failure=" + exc.code, file=sys.stderr)
        return 1
    except (OSError, UnicodeError, ValueError, subprocess.SubprocessError):
        write_receipt(receipt_path, receipt_base("report-failed"))
        print("CGB corpus receipt status=incomplete failure=report-failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
