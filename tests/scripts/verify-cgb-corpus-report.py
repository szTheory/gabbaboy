#!/usr/bin/env python3
"""Build a bounded, private receipt from existing Phase 14 CTest observations."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "gabbaboy-cgb-corpus-receipt-v1"
MAX_CASES = 4096
MAX_ASSERTIONS = 65536
MAX_EVENT_BYTES = 4096
MAX_STREAM_BYTES = 16 * 1024 * 1024
MAX_RECEIPT_BYTES = 32 * 1024 * 1024
RUN_TIMEOUT_SECONDS = 30
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


def repo_path(path: Path) -> str:
    try:
        return path.resolve(strict=True).relative_to(ROOT).as_posix()
    except (OSError, ValueError) as exc:
        raise ReportError("path-not-repository-relative") from exc


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


def covered_dirty_digest() -> str:
    covered = (
        "CMakeLists.txt",
        "src/runner/main.c",
        "src/core/gabbaboy.c",
        "tests/CMakeLists.txt",
        "tests/expected-tests.txt",
        "tests/scripts/verify-cgb-corpus-report.py",
        "tests/external/cgb-corpus-inventory.json",
        "fixtures/mooneye-cgb/manifest.json",
        "fixtures/mooneye-cgb/daa.gb",
    )
    rows = []
    for name in covered:
        data = bounded_read(ROOT / name, 32 * 1024 * 1024)
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
    executable = build_dir / "gabbaboy-runner"
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
        "build_qualified": "true",
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
    }


def run_bounded(command: list[str], timeout_seconds: int = RUN_TIMEOUT_SECONDS) -> tuple[int, bytes]:
    try:
        proc = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, close_fds=True)
    except OSError as exc:
        raise ReportError("runner-start-failed") from exc
    assert proc.stdout is not None
    output = bytearray()
    selector = selectors.DefaultSelector()
    selector.register(proc.stdout, selectors.EVENT_READ)
    deadline = time.monotonic() + timeout_seconds
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                proc.kill()
                proc.wait(timeout=2)
                raise ReportError("runner-timeout")
            ready = selector.select(min(remaining, 0.25))
            if ready:
                chunk = os.read(proc.stdout.fileno(), 65536)
                if not chunk:
                    selector.unregister(proc.stdout)
                else:
                    output.extend(chunk)
                    if len(output) > MAX_STREAM_BYTES:
                        proc.kill()
                        proc.wait(timeout=2)
                        raise ReportError("captured-stream-too-large")
            if proc.poll() is not None and not selector.get_map():
                break
        return proc.returncode, bytes(output)
    finally:
        selector.close()
        proc.stdout.close()
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=2)


def receipt_base(reason: str) -> dict:
    return {
        "schema": SCHEMA,
        "version": 1,
        "status": "incomplete",
        "failure_codes": [reason],
        "identity": {},
        "counts": {
            "eligible_cases": 1,
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


def build_report(build_dir: Path) -> dict:
    contract = load_daa_contract()
    identity = build_identity(build_dir, contract)
    runner = inside_root(build_dir) / "gabbaboy-runner"
    command = [str(runner), "--manifest", str(contract["manifest_path"]),
               "--case", "daa", "--profile", "cgb", "--receipt"]
    return_code, stream = run_bounded(command)
    if return_code != 0:
        raise ReportError("runner-nonzero")
    event = validate_event_with_identity(stream, contract, identity)
    return complete_receipt(contract, identity, event)


def self_test(build_dir: Path) -> int:
    report = build_report(build_dir)
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
    receipt_path = args.receipt
    try:
        receipt_path = inside_root(receipt_path)
    except ReportError as exc:
        print("cgb-corpus-report failed: " + exc.code, file=sys.stderr)
        return 2
    write_receipt(receipt_path, receipt_base("execution-not-started"))
    try:
        report = build_report(args.build_dir)
        write_receipt(receipt_path, report)
        counts = report["counts"]
        print("CGB corpus receipt status=complete cases={}/{} observed_pass={} assertions={}/{}".format(
            counts["completed_cases"], counts["eligible_cases"], counts["observed_pass_cases"],
            counts["passing_assertions"], counts["assertions"]))
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
