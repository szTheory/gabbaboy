#!/usr/bin/env python3
"""Validate the bounded, ordered CGB game-candidate evidence records.

The checker accepts evidence records as data only. It never executes record text, build recipes,
predicates, source files, or candidate ROMs. Candidate guest execution belongs to the admitted
acceptance path and is validated from its bound receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = 1
MAX_JSON_BYTES = 1_048_576
MAX_FILE_BYTES = 8 * 1_048_576
MAX_FILES = 4096
MAX_ARRAY_ITEMS = 4096
MAX_SUBPROCESS_SECONDS = 30
MAX_SUBPROCESS_OUTPUT = 1_048_576
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
CANDIDATES = (
    ("potion-panic-gbcompo25", "GB Compo 2025", "potion-panic.gb"),
    ("ucity-1.3", "1.3", "preferred-ucity.gbc"),
)
RECORDS = {
    "potion-panic-gbcompo25": "tests/data/cgb-candidates/potion-panic.json",
    "ucity-1.3": "tests/data/cgb-candidates/ucity-1.3.json",
}
CONTRACT_PATHS = (
    "tests/scripts/verify-cgb-candidates.py",
    "tests/scripts/verify-fixture-admission.py",
    "tests/cmake/game-evidence.cmake",
    "docs/cgb-game-candidates.md",
)
ALLOWED_NO_GO_CATEGORIES = {"rights", "source", "build", "predicate"}


class Reject(Exception):
    """A bounded, user-actionable candidate-contract rejection."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reject_constant(value: str) -> None:
    raise Reject("candidate-json-nonfinite", value)


def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Reject("candidate-json-duplicate-key", key)
        result[key] = value
    return result


def parse_json(raw: bytes, where: str) -> dict[str, Any]:
    if len(raw) > MAX_JSON_BYTES:
        raise Reject("candidate-json-size-limit", where)
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(text, object_pairs_hook=unique_pairs, parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Reject("candidate-json-invalid", f"{where}: {type(error).__name__}") from None
    if not isinstance(value, dict):
        raise Reject("candidate-record-invalid", f"{where}: expected object")
    return value


def require_keys(value: dict[str, Any], required: set[str], where: str,
                 optional: set[str] | None = None) -> None:
    optional = optional or set()
    missing = sorted(required - set(value))
    extra = sorted(set(value) - required - optional)
    if missing:
        raise Reject("candidate-field-missing", f"{where}: {','.join(missing)}")
    if extra:
        raise Reject("candidate-field-unknown", f"{where}: {','.join(extra)}")


def safe_text(value: object, where: str, limit: int = 2048) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.encode("utf-8")) > limit:
        raise Reject("candidate-field-invalid", where)
    if any(ord(char) < 0x20 and char not in "\t\n" for char in value):
        raise Reject("candidate-field-invalid", where)
    return value.strip()


def relative_path(value: object, where: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 512:
        raise Reject("candidate-path-invalid", where)
    path = PurePosixPath(value)
    if path.is_absolute() or "\\" in value or ":" in value or any(
        part in {"", ".", ".."} for part in value.split("/")
    ):
        raise Reject("candidate-path-invalid", where)
    return path.as_posix()


def read_regular(root: Path, relative: str) -> bytes:
    relative_path(relative, "path")
    target = root.joinpath(*PurePosixPath(relative).parts)
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            raise Reject("candidate-path-link", relative)
    try:
        if not target.is_file():
            raise Reject("candidate-file-unavailable", relative)
        if target.stat().st_size > MAX_FILE_BYTES:
            raise Reject("candidate-file-size-limit", relative)
        return target.read_bytes()
    except OSError:
        raise Reject("candidate-file-unavailable", relative) from None


def run_process(argv: list[str], cwd: Path, timeout: int = MAX_SUBPROCESS_SECONDS,
                output_limit: int = MAX_SUBPROCESS_OUTPUT) -> subprocess.CompletedProcess[bytes]:
    try:
        result = subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        raise Reject("candidate-subprocess-timeout", Path(argv[0]).name) from None
    except OSError as error:
        raise Reject("candidate-subprocess-unavailable", f"{Path(argv[0]).name}: {error.strerror}") from None
    if len(result.stdout) > output_limit or len(result.stderr) > output_limit:
        raise Reject("candidate-subprocess-output-limit", Path(argv[0]).name)
    return result


def git(root: Path, *args: str, timeout: int = MAX_SUBPROCESS_SECONDS,
        output_limit: int = MAX_SUBPROCESS_OUTPUT) -> bytes:
    result = run_process(["git", *args], root, timeout, output_limit)
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace")[-240:].strip()
        raise Reject("candidate-git-failed", message or "git command failed")
    return result.stdout


def resolve_source_revision(root: Path, requested: str) -> str:
    if not isinstance(requested, str) or not HEX40.fullmatch(requested):
        raise Reject("candidate-source-revision-invalid", "expected a full lowercase commit id")
    resolved = git(root, "rev-parse", "--verify", "--quiet", f"{requested}^{{commit}}").decode().strip()
    if resolved != requested:
        raise Reject("candidate-source-revision-invalid", "commit did not resolve exactly")
    return resolved


def immutable_blob(root: Path, revision: str, path: str) -> bytes:
    size_raw = git(root, "cat-file", "-s", f"{revision}:{path}").decode("ascii", errors="strict").strip()
    if not size_raw.isdecimal() or int(size_raw) > MAX_FILE_BYTES:
        raise Reject("candidate-source-file-limit", path)
    return git(root, "show", f"{revision}:{path}", output_limit=MAX_FILE_BYTES)


def validate_source_contract(root: Path, revision: str) -> dict[str, str]:
    """Read all checker authorities from one commit and compare executable files to the checkout."""
    digests: dict[str, str] = {}
    for path in CONTRACT_PATHS:
        pinned = immutable_blob(root, revision, path)
        current = read_regular(root, path)
        if current != pinned:
            raise Reject("candidate-source-drift", path)
        digests[path] = sha256(pinned)
    return digests


def candidate_metadata(candidate_id: object) -> tuple[str, str, str]:
    if not isinstance(candidate_id, str):
        raise Reject("candidate-identity-invalid", "candidate_id must be a string")
    for expected in CANDIDATES:
        if candidate_id == expected[0]:
            return expected
    raise Reject("candidate-identity-invalid", "candidate_id is not one of the two fixed IDs")


def disposition_status(record: dict[str, Any]) -> str | None:
    value = record.get("disposition")
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and isinstance(value.get("status"), str):
        return value["status"]
    return None


def validate_attempt_order(records: object) -> str | None:
    """Return a stable rejection code when the closed two-attempt order is invalid."""
    if not isinstance(records, list) or len(records) != len(CANDIDATES):
        return "candidate-attempt-set"
    if not all(isinstance(record, dict) for record in records):
        return "candidate-attempt-set"
    ids = [record.get("candidate_id") for record in records]
    if ids != [candidate[0] for candidate in CANDIDATES]:
        return "candidate-attempt-set"
    primary_status = disposition_status(records[0])
    fallback_status = disposition_status(records[1])
    if primary_status in {"blocked-defect", "partial"} or fallback_status in {"blocked-defect", "partial"}:
        return "candidate-blocked-defect"
    if primary_status == "no-go":
        if fallback_status not in {"no-go", "admitted"}:
            return "candidate-fallback-not-eligible"
    elif primary_status == "admitted":
        if fallback_status != "not-needed":
            return "candidate-fallback-not-eligible"
    else:
        return "candidate-primary-not-final"
    return None


def validate_record_minimal(record: dict[str, Any], expected_id: str, stage: str | None,
                            require_final: bool) -> None:
    expected = candidate_metadata(expected_id)
    require_keys(record, {
        "schema_version", "candidate_id", "release", "preferred_artifact", "stage", "partial",
        "disposition",
    }, "record")
    if record["schema_version"] != SCHEMA_VERSION:
        raise Reject("candidate-schema-unsupported", str(record["schema_version"]))
    if (record["candidate_id"], record["release"], record["preferred_artifact"]) != expected:
        raise Reject("candidate-identity-mismatch", expected_id)
    if record["stage"] not in {"source", "rights", "build", "identity", "mode", "progress", "final"}:
        raise Reject("candidate-stage-invalid", expected_id)
    if not isinstance(record["partial"], bool):
        raise Reject("candidate-partial-invalid", expected_id)
    if stage is not None and record["stage"] != stage:
        raise Reject("candidate-stage-mismatch", expected_id)
    if require_final and (record["stage"] != "final" or record["partial"]):
        raise Reject("candidate-partial-not-final", expected_id)
    disposition = record["disposition"]
    if isinstance(disposition, str):
        status = disposition
    elif isinstance(disposition, dict):
        require_keys(disposition, {"status", "category", "reason", "evidence"}, "disposition")
        status = disposition["status"]
        if status == "no-go":
            if disposition["category"] not in ALLOWED_NO_GO_CATEGORIES:
                raise Reject("candidate-no-go-category-invalid", expected_id)
            safe_text(disposition["reason"], "disposition.reason")
            if not isinstance(disposition["evidence"], (dict, list)) or not disposition["evidence"]:
                raise Reject("candidate-no-go-evidence-missing", expected_id)
    else:
        raise Reject("candidate-disposition-invalid", expected_id)
    if status not in {"admitted", "no-go", "not-needed", "blocked-defect", "partial"}:
        raise Reject("candidate-disposition-invalid", expected_id)


def record_path(root: Path, relative: str) -> dict[str, Any]:
    raw = read_regular(root, relative)
    return parse_json(raw, relative)


def validate_all(root: Path, revision: str, stage: str | None,
                  require_final: bool) -> tuple[list[dict[str, Any]], dict[str, str]]:
    contract = validate_source_contract(root, revision)
    records: list[dict[str, Any]] = []
    for candidate_id, relative in RECORDS.items():
        try:
            record = record_path(root, relative)
        except Reject as error:
            if error.code == "candidate-file-unavailable":
                raise Reject("candidate-record-missing", relative) from None
            raise
        validate_record_minimal(record, candidate_id, stage, require_final)
        records.append(record)
    error = validate_attempt_order(records)
    if error:
        raise Reject(error)
    return records, contract


def validate_one(root: Path, revision: str, relative: str, stage: str | None,
                 require_final: bool) -> tuple[dict[str, Any], dict[str, str]]:
    contract = validate_source_contract(root, revision)
    record = record_path(root, relative)
    candidate_id = record.get("candidate_id")
    if candidate_id not in RECORDS:
        raise Reject("candidate-identity-invalid", "record path has no fixed candidate identity")
    if relative != RECORDS[candidate_id]:
        raise Reject("candidate-record-path-mismatch", candidate_id)
    validate_record_minimal(record, candidate_id, stage, require_final)
    return record, contract


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def run_checker(root: Path, *args: str, expect_code: int = 0,
                expect_text: str = "") -> str:
    script = root / "tests/scripts/verify-cgb-candidates.py"
    result = run_process([sys.executable, "-I", str(script), *args], root, timeout=MAX_SUBPROCESS_SECONDS)
    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    if result.returncode != expect_code:
        raise Reject("candidate-self-test-failed", f"CLI exit={result.returncode} expected={expect_code}")
    if expect_text and expect_text not in output:
        raise Reject("candidate-self-test-failed", f"CLI omitted {expect_text}")
    return output


def synthetic_record(candidate: tuple[str, str, str]) -> dict[str, Any]:
    candidate_id, release, artifact = candidate
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_id": candidate_id,
        "release": release,
        "preferred_artifact": artifact,
        "stage": "final",
        "partial": False,
        "disposition": {
            "status": "no-go",
            "category": "rights",
            "reason": "synthetic rights cutoff used only by the contract self-test",
            "evidence": {"kind": "synthetic", "reference": "temporary self-test subject"},
        },
    }


def self_test(source_root: Path, selected_revision: str | None) -> None:
    """Exercise the real CLI against a private, disposable Git repository."""
    if selected_revision is not None:
        revision = resolve_source_revision(source_root, selected_revision)
        validate_source_contract(source_root, revision)
    with tempfile.TemporaryDirectory(prefix="gbb-candidate-contract-") as temporary:
        root = Path(temporary)
        (root / "tests/scripts").mkdir(parents=True)
        (root / "tests/cmake").mkdir(parents=True)
        (root / "docs").mkdir(parents=True)
        for relative in CONTRACT_PATHS:
            source = source_root / relative
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        (root / "tests/data/cgb-candidates").mkdir(parents=True)
        for candidate in CANDIDATES:
            relative = RECORDS[candidate[0]]
            write_json(root / relative, synthetic_record(candidate))
        git(root, "init", "--quiet")
        git(root, "config", "user.name", "GabbaBoy Automation")
        git(root, "config", "user.email", "automation@users.noreply.github.com")
        git(root, "add", *CONTRACT_PATHS, *RECORDS.values())
        git(root, "commit", "--quiet", "-m", "synthetic candidate contract baseline")
        revision = git(root, "rev-parse", "HEAD").decode("ascii").strip()
        common = ["--repo-root", str(root), "--source-revision", revision]
        run_checker(root, "--check-all", *common, "--require-final", expect_text="PASS: candidate records")

        primary = root / RECORDS[CANDIDATES[0][0]]
        primary.unlink()
        run_checker(root, "--check-all", *common, "--require-final", expect_code=1,
                    expect_text="candidate-record-missing")
        write_json(primary, synthetic_record(CANDIDATES[0]))

        primary_record = synthetic_record(CANDIDATES[0])
        primary_record["disposition"]["status"] = "admitted"
        write_json(primary, primary_record)
        run_checker(root, "--check-all", *common, "--require-final", expect_code=1,
                    expect_text="candidate-fallback-not-eligible")

    module_test = run_process(
        [sys.executable, "-I", str(source_root / "tests/scripts/test_cgb_candidate_order.py")],
        source_root,
    )
    if module_test.returncode != 0:
        raise Reject("candidate-self-test-failed", "candidate order assertions failed")
    print("PASS: candidate contract synthetic=2 order-controls=2")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--check-record", metavar="PATH")
    modes.add_argument("--check-all", action="store_true")
    parser.add_argument("--stage", choices=("source", "rights", "build", "identity", "mode", "progress", "final"))
    parser.add_argument("--require-final", action="store_true")
    parser.add_argument("--runner", help="optional repository-contained acceptance runner executable")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--source-revision", help="full immutable project source commit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        root = args.repo_root.resolve(strict=True)
        if args.runner:
            runner = Path(args.runner)
            if not runner.is_absolute():
                runner = root / runner
            runner = runner.resolve(strict=True)
            if root != runner and root not in runner.parents:
                raise Reject("candidate-runner-path-invalid")
            if not runner.is_file() or not os.access(runner, os.X_OK):
                raise Reject("candidate-runner-unavailable")
        if args.self_test:
            self_test(root, args.source_revision)
            return 0
        if not args.source_revision:
            raise Reject("candidate-source-revision-required")
        revision = resolve_source_revision(root, args.source_revision)
        if args.check_all:
            records, contract = validate_all(root, revision, args.stage, args.require_final)
            print(f"PASS: candidate records count={len(records)} source={revision} "
                  f"checker={contract['tests/scripts/verify-cgb-candidates.py']}")
        else:
            relative = relative_path(args.check_record, "--check-record")
            record, contract = validate_one(root, revision, relative, args.stage, args.require_final)
            print(f"PASS: candidate record id={record['candidate_id']} stage={record['stage']} "
                  f"source={revision} checker={contract['tests/scripts/verify-cgb-candidates.py']}")
        return 0
    except (Reject, OSError, subprocess.SubprocessError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
