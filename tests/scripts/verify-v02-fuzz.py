#!/usr/bin/env python3
"""Produce and verify bounded, source-bound v0.2.0 libFuzzer evidence."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve()
WORKFLOW = ".github/workflows/ci.yml"
SCHEMA_VERSION = 1
CAMPAIGN_SECONDS = 60
SOURCE_FILES = (
    "CMakeLists.txt",
    "CMakePresets.json",
    "tests/CMakeLists.txt",
    "tests/fuzz_core.c",
    "tests/fuzz/fuzz_core.dict",
    "tests/scripts/run-bounded-fuzz.sh",
    "tests/scripts/verify-v02-fuzz.py",
    WORKFLOW,
    "fixtures/tracer/tracer.gb",
    "fixtures/rtc3test/rtc3test.gb",
    "fixtures/rtc3test/manifest.json",
    "fixtures/rtc3test/ELIGIBILITY.md",
    "fixtures/mbc3-rtc-continuation/continuation.gb",
    "fixtures/mbc3-rtc-continuation/manifest.json",
)
REQUIRED_LIMITS = {
    "max_input_bytes": 65536,
    "campaign_seconds": 60,
    "per_input_timeout_seconds": 2,
    "rss_limit_mib": 512,
    "jobs": 1,
    "workers": 1,
    "fuzz_core": {
        "input_bytes": 65536,
        "operations_per_input": 16,
        "run_half_dots": 2048,
        "input_half_dots": 8192,
        "speed_half_dots": 600000,
        "cgb_hdma_operations": 16,
        "cgb_hdma_half_dots": 16384,
        "cgb_apu_operations": 16,
        "cgb_apu_half_dots": 8192,
        "cgb_io_operations": 64,
        "palette_operations": 512,
        "palette_half_dots": 400000,
        "synth_rom_max_bytes": 8388608,
    },
}
FUZZ_ARGS = (
    "-max_len=65536",
    "-max_total_time=60",
    "-timeout=2",
    "-rss_limit_mb=512",
    "-jobs=1",
    "-workers=1",
    "-print_final_stats=1",
)
SEED_SPECS = (
    ("dmg-loader", "fixtures/tracer/tracer.gb", "loader"),
    ("dmg-mbc1-battery-api", "fixtures/tracer/tracer.gb", "stateful"),
    ("cgb-profile-api", "fixtures/tracer/tracer.gb", "cgb-api"),
    ("cgb-speed", "fixtures/tracer/tracer.gb", "speed-cgb"),
    ("dmg-speed", "fixtures/tracer/tracer.gb", "speed-dmg"),
    ("cgb-io", "fixtures/tracer/tracer.gb", "cgb-io"),
    ("cgb-palette", "fixtures/tracer/tracer.gb", "cgb-palette"),
    ("cgb-apu-hostile", "fixtures/tracer/tracer.gb", "cgb-apu"),
    ("cgb-hdma", "fixtures/tracer/tracer.gb", "cgb-hdma"),
    ("rtc3test-mbc3-timer-header", "fixtures/rtc3test/rtc3test.gb", "rtc-header"),
    ("mbc3-rtc-continuation-header", "fixtures/mbc3-rtc-continuation/continuation.gb", "rtc-header"),
)
HEX_256 = re.compile(r"^[0-9a-f]{64}$")
HEX_160 = re.compile(r"^[0-9a-f]{40}$")
MAX_ARTIFACT_ZIP_BYTES = 24 * 1024 * 1024
MAX_ARTIFACT_MEMBER_BYTES = 16 * 1024 * 1024
MAX_RECEIPT_BYTES = 1024 * 1024


class ReceiptError(ValueError):
    """An evidence object fails a named production contract."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_output(*args: str, cwd: Path = ROOT) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise ReceiptError("git source identity unavailable")
    return result.stdout.strip()


def source_commit() -> str:
    commit = os.environ.get("GITHUB_SHA") or git_output("rev-parse", "HEAD")
    if not HEX_160.fullmatch(commit):
        raise ReceiptError("source SHA must be a full 40-character commit")
    return commit


def source_manifest(commit: str, *, compare_worktree: bool = True) -> dict[str, str]:
    if not HEX_160.fullmatch(commit):
        raise ReceiptError("source SHA must be a full 40-character commit")
    result: dict[str, str] = {}
    for relative in SOURCE_FILES:
        committed = subprocess.run(
            ["git", "show", f"{commit}:{relative}"], cwd=ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        )
        if committed.returncode != 0:
            raise ReceiptError(f"source input absent at source SHA: {relative}")
        digest = sha256_bytes(committed.stdout)
        if compare_worktree:
            try:
                actual = (ROOT / relative).read_bytes()
            except OSError as exc:
                raise ReceiptError(f"source input unavailable: {relative}") from exc
            if sha256_bytes(actual) != digest:
                raise ReceiptError(f"stale source input differs from source SHA: {relative}")
        result[relative] = digest
    return result


def parse_cmake_cache(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    except OSError as exc:
        raise ReceiptError("unsupported build: matching Clang sanitizer cache is unavailable") from exc
    parsed: dict[str, str] = {}
    for line in lines:
        if not line or line.startswith("//") or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split("=", 1)
        if ":" in key:
            parsed[key.split(":", 1)[0]] = value
    return parsed


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise ReceiptError(f"required build input unavailable: {path.name}") from exc
    return digest.hexdigest()


def compiler_contract(build: Path) -> dict[str, object]:
    cache_path = build / "CMakeCache.txt"
    cache = parse_cmake_cache(cache_path)
    compiler_path = cache.get("CMAKE_C_COMPILER", "")
    if not compiler_path or Path(compiler_path).name not in {"clang-18", "clang"}:
        raise ReceiptError("unsupported compiler: expected the CMake Clang 18 toolchain")
    if cache.get("GBB_HAS_CLANG_LIBFUZZER_RUNTIME") != "1":
        raise ReceiptError("unsupported compiler runtime: matching libFuzzer was not configured")
    if cache.get("GABBABOY_ENABLE_SANITIZERS") != "ON":
        raise ReceiptError("unsupported sanitizer build: GABBABOY_ENABLE_SANITIZERS is not ON")
    if cache.get("CMAKE_BUILD_TYPE", "").lower() != "debug":
        raise ReceiptError("unsupported build type: sanitizer Debug configuration is required")
    ninja = build / "build.ninja"
    try:
        ninja_text = ninja.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ReceiptError("matching Ninja build metadata is unavailable") from exc
    if "-fsanitize=fuzzer,address,undefined" not in ninja_text:
        raise ReceiptError("unsupported sanitizer flags: libFuzzer, ASan and UBSan are required")
    if not re.search(r"-fsanitize=address,undefined", ninja_text):
        raise ReceiptError("unsupported sanitizer flags: ASan and UBSan are required")
    compiler = Path(compiler_path)
    if not compiler.is_absolute() or not compiler.is_file():
        raise ReceiptError("unsupported compiler: configured Clang binary is unavailable")
    version = subprocess.run([str(compiler), "--version"], text=True, capture_output=True, check=False)
    first_line = (version.stdout or version.stderr).splitlines()
    if version.returncode != 0 or not first_line or not re.search(r"clang version 18(?:\.|\s)", first_line[0], re.I):
        raise ReceiptError("unsupported compiler: configured compiler is not Clang 18")
    binary = build / "tests" / "fuzz_core"
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ReceiptError("unsupported fuzz target: matching fuzz_core binary is unavailable")
    probe = subprocess.run([str(binary), "-help=1"], text=True, capture_output=True, check=False, timeout=10)
    if "libFuzzer" not in probe.stdout + probe.stderr:
        raise ReceiptError("unsupported fuzz target: binary does not expose libFuzzer runtime")
    return {
        "label": "clang-18",
        "version": re.sub(r"\s+", " ", first_line[0]).strip()[:160],
        "major": 18,
        "cmake_compiler_id": "Clang",
        "libfuzzer": True,
        "asan": True,
        "ubsan": True,
        "compiler_sha256": sha256_file(compiler),
        "cmake_cache_sha256": sha256_file(cache_path),
        "build_ninja_sha256": sha256_file(ninja),
        "binary_sha256": sha256_file(binary),
    }


def read_fixture(relative: str) -> bytes:
    try:
        return (ROOT / relative).read_bytes()
    except OSError as exc:
        raise ReceiptError(f"seed source unavailable: {relative}") from exc


def fixture_header(source: bytes) -> tuple[int, int, int, int]:
    if len(source) < 0x150:
        raise ReceiptError("admitted fixture is shorter than a Game Boy cartridge header")
    return source[0x147], source[0x148], source[0x149], source[0x143]


def seed_bytes(source: bytes, selector: str) -> bytes:
    if selector == "loader":
        prefix = b"\x00"
    elif selector == "stateful":
        prefix = b"\x01\x01\x03\x02\x04\x05\x00\x00"
    elif selector == "cgb-api":
        prefix = b"\x80\x01\x02\x03\x04\x05\x00\x00"
    elif selector == "speed-cgb":
        prefix = b"\x90\x01\x00\x02\x03\x04"
    elif selector == "speed-dmg":
        prefix = b"\x10\x01\x00\x02\x03\x04"
    elif selector == "cgb-io":
        prefix = b"\xC0\x03\x70\x01\x00\xFF\x40"
    elif selector == "cgb-palette":
        prefix = b"\xA0\x03\x00\xFF\x7F\x01\x02"
    elif selector == "cgb-apu":
        prefix = b"\xD3\x00\xFF\x10\x20\x30\x40\x50\x60\x70\x80\x90"
    elif selector == "cgb-hdma":
        prefix = b"\xB0\x00\xFF\x10\x20\x30\x40\x50\x60\x70"
    elif selector == "rtc-header":
        cartridge_type, rom_size, ram_size, cgb_flag = fixture_header(source)
        prefix = bytes((0x02, cartridge_type, rom_size, ram_size, 0x00, 0x00, cgb_flag))
    else:
        raise ReceiptError("unknown deterministic seed selector")
    return prefix + source[: min(len(source), 512)]


def prepare_seeds(corpus: Path) -> list[dict[str, object]]:
    corpus.mkdir(parents=True, exist_ok=False)
    records: list[dict[str, object]] = []
    for label, source_path, selector in SEED_SPECS:
        source = read_fixture(source_path)
        data = seed_bytes(source, selector)
        target = corpus / f"{label}.seed"
        target.write_bytes(data)
        records.append({
            "label": label,
            "source": source_path,
            "source_sha256": sha256_bytes(source),
            "sha256": sha256_bytes(data),
            "bytes": len(data),
        })
    return records


def expected_seed_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for label, source_path, selector in SEED_SPECS:
        source = read_fixture(source_path)
        data = seed_bytes(source, selector)
        records.append({
            "label": label,
            "source": source_path,
            "source_sha256": sha256_bytes(source),
            "sha256": sha256_bytes(data),
            "bytes": len(data),
        })
    return records


def limits_contract(value: object) -> None:
    if value != REQUIRED_LIMITS:
        raise ReceiptError("resource limits do not match the bounded campaign contract")


def workflow_job_id(repository: str, run_id: int, attempt: int) -> int | None:
    api = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return None
    url = f"{api}/repos/{repository}/actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100"
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "GabbaBoy-fuzz-receipt-producer",
    })
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read(2 * 1024 * 1024))
    except Exception:
        return None
    wanted = os.environ.get("GITHUB_JOB", "")
    if wanted == "linux-sanitizers":
        wanted = "linux-asan-ubsan"
    for job in payload.get("jobs", []):
        if job.get("name") == wanted and isinstance(job.get("id"), int):
            return job["id"]
    return None


def workflow_identity() -> dict[str, object]:
    event = os.environ.get("GITHUB_EVENT_NAME", "local")
    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "1")
    job = os.environ.get("GITHUB_JOB", "local")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    job_id = None
    try:
        numeric_run = int(run_id)
        numeric_attempt = int(attempt)
    except ValueError:
        numeric_run = 0
        numeric_attempt = 1
    if repository and numeric_run > 0:
        job_id = workflow_job_id(repository, numeric_run, numeric_attempt)
    return {
        "event": event,
        "run_id": run_id,
        "attempt": numeric_attempt,
        "job": job,
        "job_id": job_id,
        "workflow_path": WORKFLOW,
    }


def redact_output(text: str) -> str:
    value = text.replace(str(ROOT), "<workspace>")
    value = re.sub(r"/(?:Users|home)/[^/\s]+", "<home>", value)
    value = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+", "<email>", value)
    value = re.sub(r"https?://[^\s]+", "<url>", value)
    return value[:600]


def diagnostics_from(output: str) -> list[str]:
    found = []
    markers = ("ERROR: AddressSanitizer", "runtime error:", "SUMMARY: UndefinedBehaviorSanitizer",
               "ERROR: libFuzzer", "fuzz contract failed:")
    for line in output.splitlines():
        if any(marker in line for marker in markers):
            found.append(redact_output(line))
    return found[:20]


def artifact_records(directory: Path) -> list[dict[str, object]]:
    result = []
    if not directory.exists():
        return result
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.is_symlink():
            continue
        data = path.read_bytes()
        result.append({"name": path.name, "sha256": sha256_bytes(data), "bytes": len(data)})
    return result


def campaign_id(commit: str) -> str:
    run = os.environ.get("GITHUB_RUN_ID", "local")
    attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "1")
    nonce = os.environ.get("GITHUB_RUN_ID") or str(time.time_ns())
    return f"run-{run}-attempt-{attempt}-{commit[:12]}-{nonce[-12:]}"


def failed_receipt(receipt_path: Path, reason: str, commit: str | None = None) -> None:
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "unsupported" if reason.startswith("unsupported") else "failed",
        "mode": "explore",
        "source_sha": commit,
        "limits": REQUIRED_LIMITS,
        "result": {
            "outcome": "unsupported" if reason.startswith("unsupported") else "failed",
            "exit_code": None,
            "execution_count": 0,
            "elapsed_seconds": 0.0,
            "synthetic": False,
            "failure": redact_output(reason),
            "arguments": list(FUZZ_ARGS),
        },
        "minimized_artifacts": [],
        "workflow": workflow_identity(),
    }
    receipt_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def produce_campaign(build_dir: Path, receipt_path: Path) -> int:
    receipt_path = receipt_path if receipt_path.is_absolute() else ROOT / receipt_path
    build_dir = build_dir if build_dir.is_absolute() else ROOT / build_dir
    try:
        commit = source_commit()
        compiler = compiler_contract(build_dir)
        inputs = source_manifest(commit)
        dictionary = ROOT / "tests/fuzz/fuzz_core.dict"
        dictionary_sha = sha256_file(dictionary)
        fixture_manifest = json.loads((ROOT / "fixtures/rtc3test/manifest.json").read_text(encoding="utf-8"))
        rtc_data = read_fixture("fixtures/rtc3test/rtc3test.gb")
        rtc_fixture = next(item for item in fixture_manifest["fixtures"] if item["file"] == "rtc3test.gb")
        if sha256_bytes(rtc_data) != rtc_fixture["sha256"]:
            raise ReceiptError("admitted RTC seed fixture digest does not match its manifest")
        continuation_manifest = json.loads((ROOT / "fixtures/mbc3-rtc-continuation/manifest.json").read_text(encoding="utf-8"))
        continuation = read_fixture("fixtures/mbc3-rtc-continuation/continuation.gb")
        if sha256_bytes(continuation) != continuation_manifest.get("sha256"):
            raise ReceiptError("original MBC3 RTC seed fixture digest does not match its manifest")
        identifier = campaign_id(commit)
        corpus = build_dir / "fuzz-corpus" / identifier
        artifacts = build_dir / "fuzz-artifacts" / identifier
        log_path = build_dir / f"v02-fuzz-{identifier}.log"
        artifacts.mkdir(parents=True, exist_ok=False)
        seeds = prepare_seeds(corpus)
        binary = build_dir / "tests/fuzz_core"
        command = [str(binary), str(corpus), *FUZZ_ARGS,
                   f"-dict={dictionary}", f"-artifact_prefix={artifacts}{os.sep}"]
        started = utc_now()
        before = time.monotonic()
        try:
            process = subprocess.run(command, cwd=build_dir, text=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, timeout=75, check=False)
            output = process.stdout
            return_code = process.returncode
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or "")
            if isinstance(output, bytes):
                output = output.decode("utf-8", errors="replace")
            output += "\nlibFuzzer process exceeded outer 75-second timeout\n"
            return_code = 124
        elapsed = time.monotonic() - before
        log_path.write_text(redact_output(output), encoding="utf-8")
        counts = re.findall(r"stat::number_of_executed_units:\s*(\d+)", output)
        if not counts:
            counts = re.findall(r"\bDone\s+(\d+)\s+runs?\b", output)
        execution_count = int(counts[-1]) if counts else 0
        minimized = artifact_records(artifacts)
        issues = diagnostics_from(output)
        outcome = "passed"
        failure = None
        if return_code != 0:
            outcome, failure = "failed", f"fuzzer exited with code {return_code}"
        elif elapsed < CAMPAIGN_SECONDS:
            outcome, failure = "failed", "fuzzer process ended before the required 60-second campaign"
        elif execution_count <= 0:
            outcome, failure = "failed", "libFuzzer final statistics contain no nonzero execution count"
        elif issues:
            outcome, failure = "failed", "sanitizer or fuzz-contract diagnostic was emitted"
        output_digest = sha256_bytes(output.encode("utf-8", errors="replace"))
        payload: dict[str, object] = {
            "schema_version": SCHEMA_VERSION,
            "status": "complete" if outcome == "passed" else "failed",
            "mode": "explore",
            "source_sha": commit,
            "source_tree": git_output("rev-parse", f"{commit}^{{tree}}"),
            "source_inputs": inputs,
            "compiler": compiler,
            "dictionary_sha256": dictionary_sha,
            "seeds": seeds,
            "limits": REQUIRED_LIMITS,
            "result": {
                "outcome": outcome,
                "started_at": started,
                "execution_count": execution_count,
                "elapsed_seconds": round(elapsed, 3),
                "exit_code": return_code,
                "synthetic": False,
                "arguments": list(FUZZ_ARGS),
                "output_sha256": output_digest,
                "diagnostics": issues,
                "failure": failure,
            },
            "minimized_artifacts": minimized,
            "workflow": workflow_identity(),
        }
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if outcome != "passed":
            print(f"campaign=failed reason={failure} executions={execution_count} elapsed={elapsed:.3f}s artifacts={len(minimized)}", file=sys.stderr)
            return 1
        print(f"campaign=passed executions={execution_count} elapsed={elapsed:.3f}s seeds={len(seeds)} artifacts={len(minimized)}")
        return 0
    except (ReceiptError, OSError, ValueError, KeyError, StopIteration, subprocess.TimeoutExpired) as exc:
        try:
            failed_receipt(receipt_path, str(exc), os.environ.get("GITHUB_SHA") or None)
        except OSError:
            pass
        print(f"campaign=unsupported reason={redact_output(str(exc))}", file=sys.stderr)
        return 2


def validate_receipt(path: Path, *, expected_sha: str | None = None, verify_source: bool = True) -> dict[str, object]:
    if not path.is_file():
        raise ReceiptError("receipt not found")
    if path.stat().st_size > MAX_RECEIPT_BYTES:
        raise ReceiptError("receipt exceeds the 1 MiB size limit")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReceiptError("receipt is unreadable or invalid JSON") from exc
    if not isinstance(value, dict):
        raise ReceiptError("receipt must be a JSON object")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ReceiptError("unsupported receipt schema")
    if value.get("status") != "complete":
        status = value.get("status", "missing")
        raise ReceiptError(f"campaign status {status} is not complete")
    if value.get("mode") != "explore":
        raise ReceiptError("campaign mode must be explore; fast-only results cannot qualify")
    if "source_sha" not in value:
        raise ReceiptError("receipt missing required field source_sha")
    commit = value.get("source_sha")
    if not isinstance(commit, str) or not HEX_160.fullmatch(commit):
        raise ReceiptError("receipt source SHA must be a full commit ID")
    if expected_sha and commit != expected_sha:
        raise ReceiptError("receipt source SHA does not match the requested source SHA")
    current_head = git_output("rev-parse", "HEAD")
    if commit != current_head:
        raise ReceiptError("stale receipt source SHA does not match the current commit")
    result = value.get("result")
    if not isinstance(result, dict):
        raise ReceiptError("receipt result must be an object")
    if result.get("synthetic") is not False:
        raise ReceiptError("synthetic results are forbidden")
    executions = result.get("execution_count")
    if not isinstance(executions, int) or isinstance(executions, bool) or executions <= 0:
        raise ReceiptError("executions must be greater than zero")
    elapsed = result.get("elapsed_seconds")
    if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool) or elapsed < CAMPAIGN_SECONDS:
        raise ReceiptError("actual elapsed time must be at least 60 seconds")
    if result.get("outcome") != "passed" or result.get("exit_code") != 0:
        raise ReceiptError("campaign process did not complete successfully")
    if not HEX_256.fullmatch(str(result.get("output_sha256", ""))):
        raise ReceiptError("campaign output digest is missing or invalid")
    if not isinstance(result.get("diagnostics"), list) or result["diagnostics"]:
        raise ReceiptError("campaign contains sanitizer or fuzz-contract diagnostics")
    if result.get("arguments") != list(FUZZ_ARGS):
        raise ReceiptError("campaign arguments do not prove the configured time and resource bounds")
    limits_contract(value.get("limits"))
    compiler = value.get("compiler")
    if not isinstance(compiler, dict) or compiler.get("label") != "clang-18" or compiler.get("major") != 18:
        raise ReceiptError("receipt compiler is not Clang 18")
    if compiler.get("cmake_compiler_id") != "Clang" or not re.search(r"clang version 18(?:\.|\s)", str(compiler.get("version", "")), re.I):
        raise ReceiptError("receipt does not identify the configured Clang 18 compiler")
    for field in ("compiler_sha256", "cmake_cache_sha256", "build_ninja_sha256", "binary_sha256"):
        digest = compiler.get(field)
        if not isinstance(digest, str) or not HEX_256.fullmatch(digest):
            raise ReceiptError(f"receipt compiler/build identity missing valid {field}")
    if compiler.get("libfuzzer") is not True or compiler.get("asan") is not True or compiler.get("ubsan") is not True:
        raise ReceiptError("receipt must bind libFuzzer, ASan and UBSan")
    if not HEX_256.fullmatch(str(value.get("dictionary_sha256", ""))):
        raise ReceiptError("receipt dictionary SHA-256 is missing or invalid")
    if value["dictionary_sha256"] != sha256_file(ROOT / "tests/fuzz/fuzz_core.dict"):
        raise ReceiptError("dictionary identity differs from the exact source input")
    seeds = value.get("seeds")
    if not isinstance(seeds, list) or seeds != expected_seed_records():
        raise ReceiptError("seed identities differ from deterministic admitted-fixture seeds")
    workflow = value.get("workflow")
    if not isinstance(workflow, dict) or workflow.get("workflow_path") != WORKFLOW:
        raise ReceiptError("workflow run/attempt/job identity is missing")
    for field in ("run_id", "attempt", "job", "event"):
        if field not in workflow:
            raise ReceiptError(f"workflow identity missing {field}")
    if value.get("source_tree") != git_output("rev-parse", f"{commit}^{{tree}}"):
        raise ReceiptError("source tree does not match source SHA")
    source_inputs = value.get("source_inputs")
    if not isinstance(source_inputs, dict) or set(source_inputs) != set(SOURCE_FILES):
        raise ReceiptError("source input manifest does not match the required build inputs")
    for relative, expected in source_inputs.items():
        if not isinstance(expected, str) or not HEX_256.fullmatch(expected):
            raise ReceiptError(f"source input digest invalid: {relative}")
    if verify_source:
        actual_inputs = source_manifest(commit, compare_worktree=True)
        if source_inputs != actual_inputs:
            raise ReceiptError("source input identities do not match the exact source SHA")
    minimized = value.get("minimized_artifacts")
    if not isinstance(minimized, list):
        raise ReceiptError("minimized artifact inventory must be a list")
    for artifact in minimized:
        if not isinstance(artifact, dict) or not isinstance(artifact.get("name"), str):
            raise ReceiptError("minimized artifact inventory contains an invalid record")
        if PurePosixPath(artifact["name"]).name != artifact["name"] or not re.fullmatch(r"[A-Za-z0-9._-]{1,160}", artifact["name"]):
            raise ReceiptError("minimized artifact name is not a safe basename")
        if not HEX_256.fullmatch(str(artifact.get("sha256", ""))) or not isinstance(artifact.get("bytes"), int):
            raise ReceiptError("minimized artifact digest or size is invalid")
        if artifact["bytes"] < 0 or artifact["bytes"] > REQUIRED_LIMITS["max_input_bytes"]:
            raise ReceiptError("minimized artifact size exceeds the configured input bound")
    return value


def api_request(url: str, *, token: str | None = None, maximum: int = MAX_ARTIFACT_ZIP_BYTES) -> bytes:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "GabbaBoy-v02-fuzz-verifier",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(maximum + 1)
    if len(data) > maximum:
        raise ReceiptError("GitHub response exceeds configured size limit")
    return data


def repository_name() -> str:
    configured = os.environ.get("GITHUB_REPOSITORY")
    if configured and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", configured):
        return configured
    remote = git_output("remote", "get-url", "origin")
    match = re.search(r"github\.com[:/]([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?$", remote)
    if not match:
        raise ReceiptError("origin is not a GitHub repository")
    return match.group(1)


def parse_api_json(base: str, route: str, token: str | None) -> object:
    payload = api_request(f"{base.rstrip('/')}/{route.lstrip('/')}", token=token, maximum=8 * 1024 * 1024)
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ReceiptError("GitHub API returned malformed JSON") from exc


def github_api_token() -> str | None:
    configured = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if configured:
        return configured
    environment = os.environ.copy()
    environment["GIT_TERMINAL_PROMPT"] = "0"
    try:
        credentials = subprocess.run(
            ["git", "credential", "fill"], cwd=ROOT,
            input="protocol=https\nhost=github.com\n\n", text=True,
            capture_output=True, check=False, timeout=5, env=environment,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if credentials.returncode != 0:
        return None
    for line in credentials.stdout.splitlines():
        if line.startswith("password="):
            token = line.partition("=")[2]
            return token or None
    return None


def safe_zip_members(data: bytes) -> dict[str, bytes]:
    output: dict[str, bytes] = {}
    total = 0
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise ReceiptError("hosted fuzz artifact is not a ZIP archive") from exc
    with archive:
        for member in archive.infolist():
            path = PurePosixPath(member.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in member.filename:
                raise ReceiptError("hosted artifact contains an unsafe ZIP path")
            if member.is_dir():
                continue
            if member.filename in output or member.file_size > MAX_ARTIFACT_MEMBER_BYTES:
                raise ReceiptError("hosted artifact contains a duplicate or oversized member")
            total += member.file_size
            if total > MAX_ARTIFACT_ZIP_BYTES:
                raise ReceiptError("hosted artifact expands beyond the configured limit")
            output[member.filename] = archive.read(member)
    return output


def repository_branch() -> str:
    return git_output("rev-parse", "--abbrev-ref", "HEAD")


def verify_hosted(expected_sha: str, *, poll_seconds: int = 2700, interval_seconds: int = 15) -> dict[str, object]:
    if not HEX_160.fullmatch(expected_sha):
        raise ReceiptError("--source-sha must be a full commit ID")
    if git_output("rev-parse", "HEAD") != expected_sha:
        raise ReceiptError("requested source SHA does not match the current checkout")
    repo = repository_name()
    owner_repo = urllib.parse.quote(repo, safe="/")
    api = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    token = github_api_token()
    deadline = time.monotonic() + poll_seconds
    last_state = "no exact push run is visible yet"
    while time.monotonic() < deadline:
        try:
            runs_data = parse_api_json(
                api,
                f"repos/{owner_repo}/actions/runs?per_page=100",
                token,
            )
            runs = runs_data.get("workflow_runs", []) if isinstance(runs_data, dict) else []
            eligible = [run for run in runs if run.get("head_sha") == expected_sha
                        and run.get("event") == "push" and run.get("path") == WORKFLOW
                        and run.get("head_branch") == repository_branch()]
            if not eligible:
                last_state = "no exact-source ci.yml push run is visible"
            else:
                run = max(eligible, key=lambda item: (int(item.get("id", 0)), int(item.get("run_attempt", 1))))
                run_id = int(run["id"])
                attempt = int(run.get("run_attempt", 1))
                if run.get("status") != "completed":
                    last_state = f"run {run_id} attempt {attempt} is {run.get('status')}"
                else:
                    jobs_data = parse_api_json(
                        api,
                        f"repos/{owner_repo}/actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100",
                        token,
                    )
                    jobs = jobs_data.get("jobs", []) if isinstance(jobs_data, dict) else []
                    job = next((item for item in jobs if item.get("name") == "linux-asan-ubsan"), None)
                    if job is None:
                        last_state = f"run {run_id} attempt {attempt} has no eligible linux-asan-ubsan job"
                    elif job.get("conclusion") != "success":
                        raise ReceiptError(f"exact-source sanitizer job {job.get('id')} concluded {job.get('conclusion')}")
                    else:
                        artifacts_data = parse_api_json(
                            api,
                            f"repos/{owner_repo}/actions/runs/{run_id}/artifacts?per_page=100",
                            token,
                        )
                        artifacts = artifacts_data.get("artifacts", []) if isinstance(artifacts_data, dict) else []
                        artifact_name = f"v02-fuzz-{run_id}-{attempt}"
                        artifact = next((item for item in artifacts if item.get("name") == artifact_name), None)
                        if artifact is None:
                            last_state = f"run {run_id} attempt {attempt} has no {artifact_name} artifact yet"
                        elif artifact.get("expired"):
                            raise ReceiptError("exact-source fuzz receipt artifact has expired")
                        else:
                            zip_bytes = api_request(artifact["archive_download_url"], token=token)
                            members = safe_zip_members(zip_bytes)
                            receipt_matches = [name for name in members if PurePosixPath(name).name == "v02-fuzz-receipt.json"]
                            if len(receipt_matches) != 1:
                                raise ReceiptError("hosted artifact must contain exactly one fuzz receipt")
                            receipt_bytes = members[receipt_matches[0]]
                            if len(receipt_bytes) > MAX_RECEIPT_BYTES:
                                raise ReceiptError("hosted fuzz receipt exceeds the size limit")
                            with tempfile.TemporaryDirectory(prefix="gbb-v02-fuzz-verify-") as directory:
                                receipt_path = Path(directory) / "v02-fuzz-receipt.json"
                                receipt_path.write_bytes(receipt_bytes)
                                receipt = validate_receipt(receipt_path, expected_sha=expected_sha)
                            wf = receipt["workflow"]
                            if wf.get("event") != "push" or str(wf.get("run_id")) != str(run_id) or wf.get("attempt") != attempt:
                                raise ReceiptError("receipt run/attempt identity differs from its exact hosted run")
                            if wf.get("job") != "linux-sanitizers" or wf.get("job_id") != job.get("id"):
                                raise ReceiptError("receipt job identity differs from the eligible sanitizer job")
                            actual_artifacts = {
                                PurePosixPath(name).name: blob for name, blob in members.items()
                                if PurePosixPath(name).parts and PurePosixPath(name).parts[0] == "fuzz-artifacts"
                            }
                            declared = {item["name"]: item for item in receipt["minimized_artifacts"]}
                            if set(actual_artifacts) != set(declared):
                                raise ReceiptError("downloaded minimized artifacts differ from the receipt inventory")
                            for name, blob in actual_artifacts.items():
                                if sha256_bytes(blob) != declared[name]["sha256"] or len(blob) != declared[name]["bytes"]:
                                    raise ReceiptError("downloaded minimized artifact bytes do not match their receipt digests")
                            workflow_conclusion = str(run.get("conclusion") or "unknown")
                            print(f"hosted_campaign=pass source_sha={expected_sha} run={run_id} attempt={attempt} job={job['id']} executions={receipt['result']['execution_count']} elapsed={receipt['result']['elapsed_seconds']}s ci_workflow_conclusion={workflow_conclusion}")
                            return {"run_id": run_id, "attempt": attempt, "job_id": job["id"],
                                    "workflow_conclusion": workflow_conclusion, "receipt": receipt}
        except urllib.error.HTTPError as exc:
            last_state = f"GitHub API returned HTTP {exc.code}"
        except urllib.error.URLError:
            last_state = "GitHub API is temporarily unavailable"
        time.sleep(min(interval_seconds, max(0.0, deadline - time.monotonic())))
    raise ReceiptError(f"hosted exact-source verification timed out after {poll_seconds}s: {last_state}")


class ReceiptContractTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-I", str(SCRIPT), *args], cwd=ROOT,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
        )

    def verify_rejects(self, path: Path, payload: dict[str, object], reason: str) -> None:
        path.write_text(json.dumps(payload), encoding="utf-8")
        result = self.run_cli("--verify", str(path))
        self.assertNotEqual(result.returncode, 0, f"production verifier accepted negative receipt: {reason}")
        self.assertIn(reason, result.stdout, f"wrong rejection reason for negative receipt: {result.stdout}")

    def test_positive_bounded_contract_and_source_identity(self) -> None:
        limits_contract(REQUIRED_LIMITS)
        self.assertEqual(len(source_manifest(git_output("rev-parse", "HEAD"), compare_worktree=False)), len(SOURCE_FILES))
        print("positive-control=source-input-and-bounded-work-contract")

    def test_rejects_zero_execution_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.verify_rejects(Path(directory) / "zero.json", {
                "schema_version": 1, "status": "complete", "mode": "explore", "source_sha": git_output("rev-parse", "HEAD"),
                "result": {"synthetic": False, "execution_count": 0},
            }, "executions must be greater than zero")

    def test_rejects_unsupported_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.verify_rejects(Path(directory) / "unsupported.json", {
                "schema_version": 1, "status": "unsupported", "mode": "explore", "source_sha": "a" * 40,
            }, "campaign status unsupported is not complete")

    def test_producer_records_unsupported_runtime_without_qualifying(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt = root / "unsupported.json"
            result = self.run_cli("--produce", "--build-dir", str(root / "no-build"), "--receipt", str(receipt))
            self.assertNotEqual(result.returncode, 0, "unsupported runtime unexpectedly qualified")
            self.assertTrue(receipt.is_file(), "unsupported runtime did not produce a failure receipt")
            rejected = self.run_cli("--verify", str(receipt))
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("campaign status unsupported is not complete", rejected.stdout)

    def test_rejects_fast_only_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.verify_rejects(Path(directory) / "fast.json", {
                "schema_version": 1, "status": "complete", "mode": "fast", "source_sha": "a" * 40,
            }, "campaign mode must be explore")

    def test_rejects_fabricated_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.verify_rejects(Path(directory) / "fabricated.json", {
                "schema_version": 1, "status": "complete", "mode": "explore",
            }, "receipt missing required field source_sha")

    def test_rejects_stale_source_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.verify_rejects(Path(directory) / "stale.json", {
                "schema_version": 1, "status": "complete", "mode": "explore", "source_sha": "a" * 40,
            }, "stale receipt source SHA")

    def test_rejects_relaxed_campaign_bounds(self) -> None:
        limits = json.loads(json.dumps(REQUIRED_LIMITS))
        limits["campaign_seconds"] = 61
        with tempfile.TemporaryDirectory() as directory:
            self.verify_rejects(Path(directory) / "bounds.json", {
                "schema_version": 1, "status": "complete", "mode": "explore", "source_sha": git_output("rev-parse", "HEAD"),
                "result": {"synthetic": False, "execution_count": 1, "elapsed_seconds": 60,
                           "outcome": "passed", "exit_code": 0, "arguments": list(FUZZ_ARGS),
                           "output_sha256": "b" * 64, "diagnostics": []},
                "limits": limits,
            }, "resource limits do not match")

    def test_rejects_synthesized_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.verify_rejects(Path(directory) / "synthetic.json", {
                "schema_version": 1, "status": "complete", "mode": "explore", "source_sha": git_output("rev-parse", "HEAD"),
                "result": {"synthetic": True},
            }, "synthetic results are forbidden")

    def test_rejects_missing_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli("--verify", str(Path(directory) / "absent.json"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("receipt not found", result.stdout)

    def test_positive_real_receipt_when_supplied(self) -> None:
        receipt_arg = os.environ.get("GBB_FUZZ_SELF_TEST_RECEIPT")
        if not receipt_arg:
            self.skipTest("no real campaign receipt supplied; hosted qualification remains separate")
        result = self.run_cli("--verify", receipt_arg)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("receipt=pass", result.stdout)
        print("positive-control=real-campaign-receipt")


def self_test(receipt: Path | None) -> int:
    if receipt:
        os.environ["GBB_FUZZ_SELF_TEST_RECEIPT"] = str(receipt)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReceiptContractTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    # Tests are assertions; this inventory line makes a zero-control run visible in logs.
    state = "pass" if result.wasSuccessful() else "fail"
    print(f"self-test={state} positive_controls=1 negative_controls=9 rejected_mutations=0 skipped={len(result.skipped)}")
    return 0 if result.wasSuccessful() else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", type=Path, help="strictly verify a local campaign receipt")
    parser.add_argument("--produce", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--build-dir", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--receipt", type=Path, help="receipt output for --produce or positive self-test input")
    parser.add_argument("--self-test", action="store_true", help="run positive and negative production-contract controls")
    parser.add_argument("--verify-hosted", action="store_true", help="await and verify exact-source hosted push evidence")
    parser.add_argument("--source-sha", help="full commit SHA required by --verify-hosted")
    parser.add_argument("--poll-seconds", type=int, default=2700, help=argparse.SUPPRESS)
    parser.add_argument("--poll-interval-seconds", type=int, default=15, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.self_test:
            return self_test(args.receipt)
        if args.verify:
            receipt = validate_receipt(args.verify)
            print(f"receipt=pass source_sha={receipt['source_sha']} executions={receipt['result']['execution_count']} elapsed={receipt['result']['elapsed_seconds']}s")
            return 0
        if args.verify_hosted:
            if not args.source_sha:
                raise ReceiptError("--verify-hosted requires --source-sha")
            verify_hosted(args.source_sha, poll_seconds=max(1, args.poll_seconds),
                          interval_seconds=max(1, args.poll_interval_seconds))
            return 0
        if args.produce:
            if not args.build_dir or not args.receipt:
                raise ReceiptError("--produce requires --build-dir and --receipt")
            return produce_campaign(args.build_dir, args.receipt)
        parser.error("choose --produce, --verify PATH, --self-test, or --verify-hosted --source-sha SHA")
    except ReceiptError as exc:
        print(f"receipt rejected: {redact_output(str(exc))}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
