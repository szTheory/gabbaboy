#!/usr/bin/env python3
"""Validate the bounded, ordered CGB game-candidate evidence records.

The checker accepts evidence records as data only. It never executes record text, build recipes,
predicates, source files, or candidate ROMs. Candidate guest execution belongs to the admitted
acceptance path and is validated from its bound receipt.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
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
ALLOWED_NO_GO_CATEGORIES = {"rights", "source", "build", "identity", "mode", "predicate"}
FACT_FIELDS = ("source", "build", "admission", "rom", "execution", "progress", "observations", "receipt")
FACT_STAGE_ORDER = {
    "rights": 0, "source": 1, "build": 2, "identity": 3, "mode": 4,
    "progress": 5, "receipt": 6,
}
FACT_FIELD_STAGE = {
    "admission": "rights", "source": "source", "build": "build", "rom": "identity",
    "execution": "mode", "progress": "progress", "observations": "progress", "receipt": "receipt",
}
NO_GO_STAGE = {
    "rights": "rights", "source": "source", "build": "build", "identity": "identity",
    "mode": "mode", "predicate": "progress",
}
SAFE_ENVIRONMENT = {"PATH", "LANG", "LC_ALL", "TZ", "TMPDIR", "SOURCE_DATE_EPOCH", "ZERO_AR_DATE"}


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
                output_limit: int = MAX_SUBPROCESS_OUTPUT,
                environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[bytes]:
    try:
        process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0,
                                   env=environment)
    except OSError as error:
        raise Reject("candidate-subprocess-unavailable", f"{Path(argv[0]).name}: {error.strerror}") from None

    output = {"stdout": bytearray(), "stderr": bytearray()}
    overflow = threading.Event()
    read_error = threading.Event()

    def drain(name: str, stream: Any) -> None:
        try:
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    return
                remaining = output_limit - len(output[name])
                if remaining > 0:
                    output[name].extend(chunk[:remaining])
                if len(chunk) > remaining:
                    overflow.set()
        except OSError:
            read_error.set()
        finally:
            try:
                stream.close()
            except OSError:
                read_error.set()

    readers = [
        threading.Thread(target=drain, args=("stdout", process.stdout), daemon=True),
        threading.Thread(target=drain, args=("stderr", process.stderr), daemon=True),
    ]
    for reader in readers:
        reader.start()
    deadline = time.monotonic() + timeout
    timed_out = False
    while process.poll() is None:
        if overflow.is_set():
            break
        if time.monotonic() >= deadline:
            timed_out = True
            break
        time.sleep(0.01)
    if overflow.is_set() or timed_out:
        try:
            process.terminate()
            process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
                process.wait(timeout=2)
            except (OSError, subprocess.TimeoutExpired):
                pass
    else:
        process.wait()
    for reader in readers:
        reader.join(timeout=2)
    if process.poll() is None:
        try:
            process.kill()
            process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            raise Reject("candidate-subprocess-cleanup-failed", Path(argv[0]).name) from None
    if timed_out:
        raise Reject("candidate-subprocess-timeout", Path(argv[0]).name)
    if overflow.is_set():
        raise Reject("candidate-subprocess-output-limit", Path(argv[0]).name)
    if read_error.is_set() or any(reader.is_alive() for reader in readers):
        raise Reject("candidate-subprocess-output-read-failed", Path(argv[0]).name)
    return subprocess.CompletedProcess(argv, process.returncode,
                                       bytes(output["stdout"]), bytes(output["stderr"]))


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


def validate_attempt_order(records: object, require_final: bool = True) -> str | None:
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
    if primary_status == "blocked-defect" or fallback_status == "blocked-defect":
        return "candidate-blocked-defect"
    if require_final and (primary_status == "partial" or fallback_status == "partial"):
        return "candidate-partial-not-final"
    if not require_final and primary_status == "partial":
        if fallback_status != "partial":
            return "candidate-fallback-not-eligible"
        return None
    if not require_final and fallback_status == "partial":
        if primary_status != "no-go":
            return "candidate-fallback-not-eligible"
        return None
    if primary_status == "no-go":
        if fallback_status not in {"no-go", "admitted"}:
            return "candidate-fallback-not-eligible"
    elif primary_status == "admitted":
        if fallback_status != "not-needed":
            return "candidate-fallback-not-eligible"
    else:
        return "candidate-primary-not-final"
    return None


def validate_build_isolation(value: object, allow_environment_failure: bool = False) -> str | None:
    """Validate the confined build and probe evidence required for executed builds."""
    try:
        return _validate_build_isolation(value, allow_environment_failure)
    except Reject as error:
        return error.code


def _validate_build_isolation(value: object, allow_environment_failure: bool = False) -> str | None:
    if not isinstance(value, dict):
        raise Reject("candidate-build-isolation-missing")
    require_keys(value, {
        "mechanism", "source_identity", "toolchain_identity", "launcher_policy",
        "environment_allowlist", "privilege_escalation", "mounts", "network_disabled",
        "credentials_absent", "probes",
    }, "build_isolation")
    safe_text(value["mechanism"], "build_isolation.mechanism", 128)
    source = value["source_identity"]
    if not isinstance(source, dict):
        raise Reject("candidate-build-isolation-source")
    require_keys(source, {"repository", "revision"}, "build_isolation.source_identity")
    safe_text(source["repository"], "build_isolation.source_identity.repository")
    if not isinstance(source["revision"], str) or not HEX40.fullmatch(source["revision"]):
        raise Reject("candidate-build-isolation-source")
    tools = value["toolchain_identity"]
    if not isinstance(tools, list) or not tools or len(tools) > 64:
        raise Reject("candidate-build-isolation-toolchain")
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            raise Reject("candidate-build-isolation-toolchain")
        require_keys(tool, {"name", "version", "revision", "sha256"}, f"toolchain_identity[{index}]")
        for key in ("name", "version"):
            safe_text(tool[key], f"toolchain_identity[{index}].{key}", 128)
        if not isinstance(tool["revision"], str) or not HEX40.fullmatch(tool["revision"]):
            raise Reject("candidate-build-isolation-toolchain")
        if not isinstance(tool["sha256"], str) or not HEX64.fullmatch(tool["sha256"]):
            raise Reject("candidate-build-isolation-toolchain")
    policy = value["launcher_policy"]
    if not isinstance(policy, dict):
        raise Reject("candidate-build-isolation-policy")
    require_keys(policy, {"path", "sha256"}, "build_isolation.launcher_policy")
    relative_path(policy["path"], "build_isolation.launcher_policy.path")
    if not isinstance(policy["sha256"], str) or not HEX64.fullmatch(policy["sha256"]):
        raise Reject("candidate-build-isolation-policy")
    environment = value["environment_allowlist"]
    if not isinstance(environment, list) or not environment or len(environment) > 64:
        raise Reject("candidate-build-isolation-credentials")
    safe_environment = {"PATH", "LANG", "LC_ALL", "TZ", "TMPDIR", "SOURCE_DATE_EPOCH", "ZERO_AR_DATE"}
    if any(not isinstance(name, str) or name not in safe_environment for name in environment) \
            or len(set(environment)) != len(environment):
        raise Reject("candidate-build-isolation-credentials")
    if value["privilege_escalation"] is not False:
        raise Reject("candidate-build-isolation-privilege")
    mounts = value["mounts"]
    if not isinstance(mounts, list) or len(mounts) != 3:
        raise Reject("candidate-build-isolation-mounts")
    mount_map: dict[str, str] = {}
    for mount in mounts:
        if not isinstance(mount, dict):
            raise Reject("candidate-build-isolation-mounts")
        require_keys(mount, {"root_label", "access"}, "build_isolation.mounts[]")
        label, access = mount["root_label"], mount["access"]
        if not isinstance(label, str) or label in mount_map or not isinstance(access, str):
            raise Reject("candidate-build-isolation-mounts")
        mount_map[label] = access
    if mount_map != {"source": "read-only", "toolchain": "read-only", "output": "read-write"}:
        raise Reject("candidate-build-isolation-mounts")
    failure: str | None = None
    if value["network_disabled"] is not True:
        if not allow_environment_failure or value["network_disabled"] is not False:
            raise Reject("candidate-build-isolation-network")
        failure = "candidate-build-isolation-network"
    if value["credentials_absent"] is not True:
        raise Reject("candidate-build-isolation-credentials")
    probes = value["probes"]
    if not isinstance(probes, dict):
        raise Reject("candidate-build-isolation-probes")
    require_keys(probes, {"outside_root_read", "local_network"}, "build_isolation.probes")
    for name, target in (("outside_root_read", "outside-root"), ("local_network", "local-endpoint")):
        probe = probes[name]
        if not isinstance(probe, dict):
            raise Reject("candidate-build-isolation-probes")
        require_keys(probe, {"baseline", "restricted", "target", "log_id", "log_sha256"},
                     f"build_isolation.probes.{name}")
        code = ("candidate-build-isolation-outside-probe" if name == "outside_root_read"
                else "candidate-build-isolation-network-probe")
        if probe["target"] != target:
            raise Reject(code)
        if probe["baseline"] != "allowed":
            if not allow_environment_failure or probe["baseline"] != "denied":
                raise Reject(code)
            failure = failure or code
        if probe["restricted"] != "denied":
            if not allow_environment_failure or probe["restricted"] != "allowed":
                raise Reject(code)
            failure = failure or code
        if not isinstance(probe["log_id"], str) or not re.fullmatch(r"[a-zA-Z0-9._-]{1,128}", probe["log_id"]):
            raise Reject("candidate-build-isolation-probes")
        if not isinstance(probe["log_sha256"], str) or not HEX64.fullmatch(probe["log_sha256"]):
            raise Reject("candidate-build-isolation-probes")
    return failure


def validate_admitted_contract(record: object) -> str | None:
    """Validate the Phase 20 admission, native-mode and progress evidence for an admitted record."""
    try:
        _validate_admitted_contract(record)
    except Reject as error:
        return error.code
    return None


def _observed_value(record: dict[str, Any], field: str) -> dict[str, Any]:
    fact = record.get(field)
    if not isinstance(fact, dict) or fact.get("state") != "observed" or not isinstance(fact.get("value"), dict):
        raise Reject("candidate-admitted-fact-missing", field)
    return fact["value"]


def _validate_admitted_contract(record: object) -> None:
    if not isinstance(record, dict):
        raise Reject("candidate-record-invalid")
    if disposition_status(record) != "admitted":
        raise Reject("candidate-disposition-invalid")
    admission = _observed_value(record, "admission")
    if admission.get("decision_status") != "approved":
        raise Reject("candidate-phase20-admission-required")
    rom = _observed_value(record, "rom")
    size = rom.get("size_bytes")
    digest = rom.get("sha256")
    header = rom.get("header")
    if not isinstance(size, int) or isinstance(size, bool) or size < 0x150 or size > 8 * 1024 * 1024 \
            or not isinstance(digest, str) or not HEX64.fullmatch(digest) or not isinstance(header, dict):
        raise Reject("candidate-rom-identity-invalid")
    cgb_flag = header.get("cgb_flag")
    if isinstance(cgb_flag, bool) or cgb_flag not in {0x80, 0xC0}:
        raise Reject("candidate-native-header-required")
    execution = _observed_value(record, "execution")
    if execution.get("profile") != "cgb-cpu-e" or execution.get("actual_mode") != "native-cgb":
        raise Reject("candidate-native-mode-required")
    progress = _observed_value(record, "progress")
    positive = progress.get("positive")
    controls = progress.get("controls")
    if not isinstance(positive, dict) or not isinstance(controls, dict):
        raise Reject("candidate-progress-controls-missing")
    if positive.get("status") != "pass" or positive.get("raw_reason") != "predicate-reached":
        raise Reject("candidate-progress-positive-invalid")
    if positive.get("control_id") != "positive":
        raise Reject("candidate-progress-positive-invalid")
    if not isinstance(positive.get("observation_sha256"), str) \
            or not HEX64.fullmatch(positive["observation_sha256"]):
        raise Reject("candidate-progress-positive-invalid")
    required = {"no_input", "wrong_input", "impossible_predicate"}
    expected_ids = {
        "no_input": "no-input",
        "wrong_input": "wrong-input",
        "impossible_predicate": "impossible-predicate",
    }
    if set(controls) != required:
        raise Reject("candidate-progress-controls-missing")
    identities: set[str] = set()
    observation_digests = {positive["observation_sha256"]}
    for key, control in controls.items():
        if not isinstance(control, dict) or control.get("status") != "fail" \
                or control.get("raw_reason") != "predicate-not-reached":
            raise Reject("candidate-progress-control-invalid", key)
        control_id = control.get("control_id")
        if control_id != expected_ids[key] or control_id in identities:
            raise Reject("candidate-progress-control-invalid", key)
        if not isinstance(control.get("observation_sha256"), str) \
                or not HEX64.fullmatch(control["observation_sha256"]):
            raise Reject("candidate-progress-control-invalid", key)
        identities.add(control_id)
        observation_digest = control["observation_sha256"]
        if observation_digest in observation_digests:
            raise Reject("candidate-progress-control-invalid", f"duplicate observation: {key}")
        observation_digests.add(observation_digest)
    if "build" in record:
        build = _observed_value(record, "build")
        if build.get("executed") is True:
            error = validate_build_isolation(build.get("build_isolation"))
            if error:
                raise Reject(error)


def _validate_inventory(value: object, where: str, *, allow_empty: bool = False) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) > MAX_FILES or (not allow_empty and not value):
        raise Reject("candidate-inventory-invalid", where)
    seen: set[str] = set()
    total = 0
    for index, item in enumerate(value):
        label = f"{where}[{index}]"
        if not isinstance(item, dict):
            raise Reject("candidate-inventory-invalid", label)
        require_keys(item, {"path", "size_bytes", "sha256"}, label)
        path = relative_path(item["path"], f"{label}.path")
        size = item["size_bytes"]
        digest = item["sha256"]
        if path in seen:
            raise Reject("candidate-inventory-duplicate", path)
        if isinstance(size, bool) or not isinstance(size, int) or size < 0 or size > MAX_FILE_BYTES:
            raise Reject("candidate-inventory-invalid", f"{label}.size_bytes")
        if not isinstance(digest, str) or not HEX64.fullmatch(digest):
            raise Reject("candidate-inventory-invalid", f"{label}.sha256")
        total += size
        if total > MAX_FILES * 1024 * 1024:
            raise Reject("candidate-inventory-size-limit", where)
        item["path"] = path
        seen.add(path)
    return value


def _validate_source(value: dict[str, Any]) -> None:
    require_keys(value, {"repository", "revision", "submodules", "inventory", "build_inputs"}, "source")
    safe_text(value["repository"], "source.repository")
    if not isinstance(value["revision"], str) or not HEX40.fullmatch(value["revision"]):
        raise Reject("candidate-source-revision-invalid")
    submodules = value["submodules"]
    if not isinstance(submodules, list) or len(submodules) > 128:
        raise Reject("candidate-submodule-inventory-invalid")
    submodule_paths: set[str] = set()
    for index, item in enumerate(submodules):
        if not isinstance(item, dict):
            raise Reject("candidate-submodule-inventory-invalid")
        require_keys(item, {"path", "repository", "revision"}, f"source.submodules[{index}]")
        path = relative_path(item["path"], f"source.submodules[{index}].path")
        safe_text(item["repository"], f"source.submodules[{index}].repository")
        if not isinstance(item["revision"], str) or not HEX40.fullmatch(item["revision"]) or path in submodule_paths:
            raise Reject("candidate-submodule-inventory-invalid")
        submodule_paths.add(path)
    inventory = _validate_inventory(value["inventory"], "source.inventory")
    inputs = _validate_inventory(value["build_inputs"], "source.build_inputs")
    inventory_map = {item["path"]: (item["size_bytes"], item["sha256"]) for item in inventory}
    for item in inputs:
        if inventory_map.get(item["path"]) != (item["size_bytes"], item["sha256"]):
            raise Reject("candidate-build-input-not-pinned", item["path"])


def _validate_build(value: dict[str, Any], source: dict[str, Any]) -> None:
    require_keys(value, {"recipe", "recipe_sha256", "tools", "executed", "result"}, "build",
                 {"build_isolation"})
    recipe = safe_text(value["recipe"], "build.recipe", 8192)
    if value["recipe_sha256"] != sha256(recipe.encode("utf-8")):
        raise Reject("candidate-build-recipe-mismatch")
    tools = value["tools"]
    if not isinstance(tools, list) or not tools or len(tools) > 64:
        raise Reject("candidate-build-tools-invalid")
    tool_ids: set[str] = set()
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            raise Reject("candidate-build-tools-invalid")
        require_keys(tool, {"name", "version", "terms", "source_repository", "revision", "sha256"},
                     f"build.tools[{index}]")
        name = safe_text(tool["name"], f"build.tools[{index}].name", 128)
        safe_text(tool["version"], f"build.tools[{index}].version", 128)
        safe_text(tool["terms"], f"build.tools[{index}].terms", 512)
        safe_text(tool["source_repository"], f"build.tools[{index}].source_repository", 512)
        if name in tool_ids or not isinstance(tool["revision"], str) or not HEX40.fullmatch(tool["revision"]) \
                or not isinstance(tool["sha256"], str) or not HEX64.fullmatch(tool["sha256"]):
            raise Reject("candidate-build-tools-invalid")
        tool_ids.add(name)
    if not isinstance(value["executed"], bool) or value["result"] not in {"passed", "failed", "not-run"}:
        raise Reject("candidate-build-result-invalid")
    isolation = value.get("build_isolation")
    if value["executed"]:
        error = validate_build_isolation(isolation)
        if error:
            raise Reject(error)
    elif isolation is not None:
        failure = validate_build_isolation(isolation, allow_environment_failure=True)
        if failure is None:
            raise Reject("candidate-build-isolation-unexpected")
    if isolation is not None:
        if isolation["source_identity"] != {
            "repository": source["repository"], "revision": source["revision"]
        }:
            raise Reject("candidate-build-isolation-source")
        inventory = {item["path"]: item["sha256"] for item in source["inventory"]}
        if inventory.get(isolation["launcher_policy"]["path"]) != isolation["launcher_policy"]["sha256"]:
            raise Reject("candidate-build-isolation-policy")
        expected_tools = sorted((tool["name"], tool["version"], tool["revision"], tool["sha256"])
                                for tool in tools)
        actual_tools = sorted((tool["name"], tool["version"], tool["revision"], tool["sha256"])
                              for tool in isolation["toolchain_identity"])
        if expected_tools != actual_tools:
            raise Reject("candidate-build-isolation-toolchain")


def _validate_admission(value: dict[str, Any]) -> None:
    status = value.get("decision_status")
    if status == "approved":
        require_keys(value, {"decision_status", "manifest_path", "manifest_sha256", "pin_path", "pin_commit"},
                     "admission")
        relative_path(value["manifest_path"], "admission.manifest_path")
        relative_path(value["pin_path"], "admission.pin_path")
        if not isinstance(value["manifest_sha256"], str) or not HEX64.fullmatch(value["manifest_sha256"]):
            raise Reject("candidate-admission-identity-invalid")
        if not isinstance(value["pin_commit"], str) or not HEX40.fullmatch(value["pin_commit"]):
            raise Reject("candidate-admission-identity-invalid")
    elif status == "no-go":
        require_keys(value, {"decision_status", "reason", "evidence"}, "admission")
        safe_text(value["reason"], "admission.reason")
        if not isinstance(value["evidence"], (dict, list)) or not value["evidence"]:
            raise Reject("candidate-admission-evidence-missing")
    else:
        raise Reject("candidate-admission-decision-invalid")


def _validate_rom(value: dict[str, Any]) -> None:
    require_keys(value, {"path", "size_bytes", "sha256", "header", "build_recipe_sha256"}, "rom")
    relative_path(value["path"], "rom.path")
    size = value["size_bytes"]
    if isinstance(size, bool) or not isinstance(size, int) or size < 0x150 or size > 8 * 1024 * 1024:
        raise Reject("candidate-rom-identity-invalid")
    if not isinstance(value["sha256"], str) or not HEX64.fullmatch(value["sha256"]):
        raise Reject("candidate-rom-identity-invalid")
    if not isinstance(value["build_recipe_sha256"], str) or not HEX64.fullmatch(value["build_recipe_sha256"]):
        raise Reject("candidate-rom-identity-invalid")
    header = value["header"]
    if not isinstance(header, dict):
        raise Reject("candidate-rom-header-invalid")
    require_keys(header, {"title", "mapper_type", "rom_size_code", "ram_size_code", "cgb_flag"}, "rom.header")
    safe_text(header["title"], "rom.header.title", 32)
    for key in ("mapper_type", "rom_size_code", "ram_size_code", "cgb_flag"):
        if isinstance(header[key], bool) or not isinstance(header[key], int) or not 0 <= header[key] <= 255:
            raise Reject("candidate-rom-header-invalid", key)


def _validate_progress(value: dict[str, Any], source: dict[str, Any]) -> None:
    require_keys(value, {
        "case_id", "case_file", "case_sha256", "input_script", "predicate", "budget_half_dots",
        "positive", "controls",
    }, "progress")
    safe_text(value["case_id"], "progress.case_id", 64)
    relative_path(value["case_file"], "progress.case_file")
    for key in ("case_sha256",):
        if not isinstance(value[key], str) or not HEX64.fullmatch(value[key]):
            raise Reject("candidate-progress-identity-invalid", key)
    input_script = value["input_script"]
    if not isinstance(input_script, dict):
        raise Reject("candidate-progress-identity-invalid", "input_script")
    require_keys(input_script, {"path", "sha256"}, "progress.input_script")
    relative_path(input_script["path"], "progress.input_script.path")
    if not isinstance(input_script["sha256"], str) or not HEX64.fullmatch(input_script["sha256"]):
        raise Reject("candidate-progress-identity-invalid", "input_script.sha256")
    predicate = value["predicate"]
    if not isinstance(predicate, dict):
        raise Reject("candidate-progress-identity-invalid", "predicate")
    require_keys(predicate, {"path", "sha256", "anchors"}, "progress.predicate")
    predicate_path = relative_path(predicate["path"], "progress.predicate.path")
    if not isinstance(predicate["sha256"], str) or not HEX64.fullmatch(predicate["sha256"]):
        raise Reject("candidate-progress-identity-invalid", "predicate.sha256")
    inventory = {item["path"]: item["sha256"] for item in source["inventory"]}
    if inventory.get(predicate_path) != predicate["sha256"]:
        raise Reject("candidate-predicate-not-source-anchored")
    anchors = predicate["anchors"]
    if not isinstance(anchors, list) or not anchors or len(anchors) > 128:
        raise Reject("candidate-predicate-anchor-missing")
    for index, anchor in enumerate(anchors):
        if not isinstance(anchor, dict):
            raise Reject("candidate-predicate-anchor-invalid")
        require_keys(anchor, {"offset", "bytes_hex"}, f"progress.predicate.anchors[{index}]")
        if not isinstance(anchor["offset"], int) or isinstance(anchor["offset"], bool) or anchor["offset"] < 0:
            raise Reject("candidate-predicate-anchor-invalid")
        if not isinstance(anchor["bytes_hex"], str) or not re.fullmatch(r"(?:[0-9A-Fa-f]{2})(?: [0-9A-Fa-f]{2})*", anchor["bytes_hex"]):
            raise Reject("candidate-predicate-anchor-invalid")
    budget = value["budget_half_dots"]
    if isinstance(budget, bool) or not isinstance(budget, int) or budget <= 0 or budget > 10**13:
        raise Reject("candidate-progress-budget-invalid")
    # The control result matrix is validated separately for the public unit tests.
    record_stub = {"disposition": {"status": "admitted"}, "admission": {"state": "observed", "value": {"decision_status": "approved"}},
                   "rom": {"state": "observed", "value": {"size_bytes": 0x150, "sha256": "0" * 64,
                            "header": {"cgb_flag": 0x80}}},
                   "execution": {"state": "observed", "value": {"profile": "cgb-cpu-e", "actual_mode": "native-cgb"}},
                   "progress": {"state": "observed", "value": value}}
    error = validate_admitted_contract(record_stub)
    if error:
        raise Reject(error)


def _validate_observation(value: dict[str, Any]) -> None:
    require_keys(value, {"checkpoints"}, "observations")
    checkpoints = value["checkpoints"]
    if not isinstance(checkpoints, list) or not checkpoints or len(checkpoints) > 128:
        raise Reject("candidate-observations-invalid")
    names: set[str] = set()
    for index, checkpoint in enumerate(checkpoints):
        if not isinstance(checkpoint, dict):
            raise Reject("candidate-observations-invalid")
        require_keys(checkpoint, {"name", "half_dots", "rgb555_sha256", "pcm_sha256"},
                     f"observations.checkpoints[{index}]")
        name = safe_text(checkpoint["name"], f"observations.checkpoints[{index}].name", 128)
        if name in names:
            raise Reject("candidate-observations-duplicate", name)
        names.add(name)
        time_value = checkpoint["half_dots"]
        if isinstance(time_value, bool) or not isinstance(time_value, int) or time_value < 0 or time_value > 10**13:
            raise Reject("candidate-observations-invalid", name)
        for key in ("rgb555_sha256", "pcm_sha256"):
            if not isinstance(checkpoint[key], str) or not HEX64.fullmatch(checkpoint[key]):
                raise Reject("candidate-observations-invalid", key)


def _validate_receipt(value: dict[str, Any], record: dict[str, Any],
                      selected_revision: str, root: Path) -> str:
    source = record["source"]["value"]
    rom = record["rom"]["value"]
    execution = record["execution"]["value"]
    progress = record["progress"]["value"]
    observations = record["observations"]["value"]
    build = record["build"]["value"]
    require_keys(value, {
        "path", "sha256", "project_source_revision", "game_source_revision", "case_sha256",
        "input_sha256", "predicate_sha256", "runner_sha256", "binary_sha256",
    }, "receipt")
    path = relative_path(value["path"], "receipt.path")
    raw = read_regular(root, path)
    if value["sha256"] != sha256(raw):
        raise Reject("candidate-receipt-digest-mismatch")
    project_revision = value["project_source_revision"]
    if not isinstance(project_revision, str) or not HEX40.fullmatch(project_revision) \
            or value["game_source_revision"] != source["revision"]:
        raise Reject("candidate-receipt-source-mismatch")
    ancestor = run_process(["git", "merge-base", "--is-ancestor", project_revision, selected_revision], root)
    if ancestor.returncode != 0:
        raise Reject("candidate-receipt-source-mismatch")
    validate_source_contract(root, project_revision)
    if value["case_sha256"] != progress["case_sha256"] or value["input_sha256"] != progress["input_script"]["sha256"] \
            or value["predicate_sha256"] != progress["predicate"]["sha256"]:
        raise Reject("candidate-receipt-progress-mismatch")
    for key in ("runner_sha256", "binary_sha256"):
        if not isinstance(value[key], str) or not HEX64.fullmatch(value[key]):
            raise Reject("candidate-receipt-identity-invalid", key)
    receipt_json = parse_json(raw, path)
    require_keys(receipt_json, {
        "case_id", "rom_sha256", "profile", "actual_mode", "status", "budget_half_dots",
        "input_sha256", "predicate_sha256", "build_recipe_sha256", "project_source_revision",
        "game_source_revision", "runner_sha256", "binary_sha256", "positive", "controls",
        "observations",
    }, "receipt document")
    if receipt_json["case_id"] != progress["case_id"] or receipt_json["rom_sha256"] != rom["sha256"] \
            or receipt_json["profile"] != execution["profile"] or receipt_json["actual_mode"] != execution["actual_mode"] \
            or receipt_json["status"] != "pass" or receipt_json["budget_half_dots"] != progress["budget_half_dots"] \
            or receipt_json["input_sha256"] != progress["input_script"]["sha256"] \
            or receipt_json["predicate_sha256"] != progress["predicate"]["sha256"] \
            or receipt_json["build_recipe_sha256"] != build["recipe_sha256"] \
            or receipt_json["project_source_revision"] != project_revision \
            or receipt_json["game_source_revision"] != source["revision"] \
            or receipt_json["runner_sha256"] != value["runner_sha256"] \
            or receipt_json["binary_sha256"] != value["binary_sha256"] \
            or receipt_json["positive"] != progress["positive"] \
            or receipt_json["controls"] != progress["controls"] \
            or receipt_json["observations"] != observations:
        raise Reject("candidate-receipt-content-invalid")
    return project_revision


def _rom_header(data: bytes) -> dict[str, Any]:
    title_raw = data[0x134:0x144]
    try:
        title = title_raw.split(b"\0", 1)[0].decode("ascii", errors="strict").strip()
    except UnicodeDecodeError:
        raise Reject("candidate-rom-header-invalid", "title encoding") from None
    return {
        "title": title,
        "mapper_type": data[0x147],
        "rom_size_code": data[0x148],
        "ram_size_code": data[0x149],
        "cgb_flag": data[0x143],
    }


def _manifest_file_map(manifest: dict[str, Any]) -> dict[str, tuple[int, str]]:
    entries = manifest.get("files")
    if not isinstance(entries, list) or len(entries) > MAX_FILES:
        raise Reject("candidate-admission-manifest-invalid", "files")
    result: dict[str, tuple[int, str]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise Reject("candidate-admission-manifest-invalid", "file entry")
        path = relative_path(entry.get("path"), "manifest.files.path")
        size = entry.get("size_bytes")
        digest = entry.get("sha256")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0 or size > MAX_FILE_BYTES \
                or not isinstance(digest, str) or not HEX64.fullmatch(digest) or path in result:
            raise Reject("candidate-admission-manifest-invalid", path)
        result[path] = (size, digest)
    return result


def _validate_admitted_cross_bindings(root: Path, revision: str, record: dict[str, Any]) -> None:
    source = record["source"]["value"]
    build = record["build"]["value"]
    admission = record["admission"]["value"]
    rom = record["rom"]["value"]
    progress = record["progress"]["value"]
    manifest_path = admission["manifest_path"]
    manifest_raw = read_regular(root, manifest_path)
    if sha256(manifest_raw) != admission["manifest_sha256"]:
        raise Reject("candidate-admission-manifest-mismatch")
    manifest = parse_json(manifest_raw, manifest_path)
    if manifest.get("schema_version") != 1 or not isinstance(manifest.get("decision"), dict) \
            or manifest["decision"].get("status") != "approved":
        raise Reject("candidate-phase20-admission-required")
    pin_path = admission["pin_path"]
    if pin_path != f"{PurePosixPath(manifest_path).parent}/admission.commit":
        raise Reject("candidate-admission-pin-path-invalid")
    pin_bytes = read_regular(root, pin_path)
    try:
        pin_commit = pin_bytes.decode("ascii").strip()
    except UnicodeDecodeError:
        raise Reject("candidate-admission-pin-invalid") from None
    if pin_commit != admission["pin_commit"] or not HEX40.fullmatch(pin_commit):
        raise Reject("candidate-admission-pin-invalid")
    manifest_source = manifest.get("source")
    if not isinstance(manifest_source, dict) or (manifest_source.get("repository"), manifest_source.get("revision")) \
            != (source["repository"], source["revision"]):
        raise Reject("candidate-admission-source-mismatch")
    manifest_build = manifest.get("build")
    if not isinstance(manifest_build, dict) or manifest_build.get("recipe") != build["recipe"]:
        raise Reject("candidate-admission-build-mismatch")
    record_tools = {tool["name"]: tool for tool in build["tools"]}
    manifest_tools = manifest_build.get("tools")
    if not isinstance(manifest_tools, list) or len(manifest_tools) != len(record_tools):
        raise Reject("candidate-admission-build-mismatch")
    for tool in manifest_tools:
        record_tool = record_tools.get(tool.get("name")) if isinstance(tool, dict) else None
        if record_tool is None or any(record_tool.get(key) != tool.get(manifest_key) for key, manifest_key in (
            ("name", "name"), ("version", "version"), ("terms", "terms"),
            ("source_repository", "source_repository"), ("revision", "revision"),
        )):
            raise Reject("candidate-admission-build-mismatch")
    files = _manifest_file_map(manifest)
    if files.get(rom["path"]) != (rom["size_bytes"], rom["sha256"]):
        raise Reject("candidate-admission-rom-mismatch")
    rom_bytes = read_regular(root, rom["path"])
    if len(rom_bytes) != rom["size_bytes"] or sha256(rom_bytes) != rom["sha256"]:
        raise Reject("candidate-rom-identity-mismatch")
    if _rom_header(rom_bytes) != rom["header"]:
        raise Reject("candidate-rom-header-mismatch")
    if rom["build_recipe_sha256"] != build["recipe_sha256"]:
        raise Reject("candidate-rom-build-link-mismatch")
    manifest_inputs = manifest.get("inputs")
    if not isinstance(manifest_inputs, list):
        raise Reject("candidate-admission-inputs-invalid")
    expected_inputs = sorted((item["path"], item["size_bytes"], item["sha256"]) for item in source["build_inputs"])
    try:
        actual_inputs = sorted((item["path"], item["size_bytes"], item["sha256"]) for item in manifest_inputs)
    except (KeyError, TypeError):
        raise Reject("candidate-admission-inputs-invalid") from None
    if expected_inputs != actual_inputs:
        raise Reject("candidate-admission-inputs-mismatch")
    receipt_value = record["receipt"]["value"]
    project_revision = receipt_value.get("project_source_revision")
    if not isinstance(project_revision, str) or not HEX40.fullmatch(project_revision):
        raise Reject("candidate-receipt-source-mismatch")
    if sha256(immutable_blob(root, project_revision, progress["case_file"])) != progress["case_sha256"]:
        raise Reject("candidate-progress-project-source-mismatch", "case_file")
    if sha256(immutable_blob(root, project_revision, progress["input_script"]["path"])) \
            != progress["input_script"]["sha256"]:
        raise Reject("candidate-progress-project-source-mismatch", "input_script")
    source_inventory = {item["path"]: item["sha256"] for item in source["inventory"]}
    if source_inventory.get(progress["predicate"]["path"]) != progress["predicate"]["sha256"]:
        raise Reject("candidate-predicate-not-source-anchored")


def _check_phase20_admission(root: Path, record: dict[str, Any]) -> None:
    manifest_path = record["admission"]["value"]["manifest_path"]
    checker = root / "tests/scripts/verify-fixture-admission.py"
    result = run_process([sys.executable, "-I", str(checker), "--check-manifest", manifest_path,
                          "--repo-root", str(root)], root, timeout=MAX_SUBPROCESS_SECONDS)
    if result.returncode != 0 or b"PASS: fixture admission" not in result.stdout:
        detail = (result.stdout + result.stderr).decode("utf-8", errors="replace").strip()[-512:]
        raise Reject("candidate-phase20-admission-failed", detail)


def _run_admitted_candidate(root: Path, runner: Path, record: dict[str, Any]) -> None:
    """Execute only an admitted subject, after the real Phase 20 check has passed."""
    progress = record["progress"]["value"]
    isolation = record["build"]["value"]["build_isolation"]
    environment = {
        name: os.environ[name] for name in isolation["environment_allowlist"] if name in os.environ
    }
    result = run_process([str(runner), "--acceptance", progress["case_file"], "--case",
                          progress["case_id"], "--receipt"], root,
                         timeout=MAX_SUBPROCESS_SECONDS, environment=environment)
    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    if result.returncode != 0 or "status=pass" not in output \
            or not ("model=cgb-cpu-e" in output or "profile=CGB-CPU-E" in output) \
            or "mode=native-cgb" not in output:
        raise Reject("candidate-runner-result-invalid")


def _validate_commit_record_ref(root: Path, revision: str, value: object,
                                expected_status: str, expected_path: str) -> None:
    if not isinstance(value, dict):
        raise Reject("candidate-primary-reference-invalid")
    require_keys(value, {"path", "commit", "sha256"}, "primary record reference")
    if value["path"] != expected_path or not isinstance(value["commit"], str) \
            or not HEX40.fullmatch(value["commit"]) or not isinstance(value["sha256"], str) \
            or not HEX64.fullmatch(value["sha256"]):
        raise Reject("candidate-primary-reference-invalid")
    ancestor = run_process(["git", "merge-base", "--is-ancestor", value["commit"], revision], root)
    if ancestor.returncode != 0:
        raise Reject("candidate-primary-record-not-in-history")
    raw = immutable_blob(root, value["commit"], expected_path)
    if sha256(raw) != value["sha256"]:
        raise Reject("candidate-primary-reference-mismatch")
    primary = parse_json(raw, expected_path)
    if disposition_status(primary) != expected_status:
        raise Reject("candidate-primary-reference-state-invalid")


def _validate_primary_no_go_reference(root: Path, revision: str, record: dict[str, Any]) -> None:
    disposition = record["disposition"]
    _validate_commit_record_ref(root, revision, disposition.get("primary_no_go_ref"), "no-go",
                                RECORDS[CANDIDATES[0][0]])


def _validate_not_needed_reference(root: Path, revision: str, record: dict[str, Any]) -> None:
    _validate_commit_record_ref(root, revision, record["disposition"].get("primary_record_ref"), "admitted",
                                RECORDS[CANDIDATES[0][0]])


def _validate_not_observed(record: dict[str, Any], status: str) -> None:
    unobserved = record["unobserved"]
    if not isinstance(unobserved, list) or len(unobserved) > len(FACT_FIELDS):
        raise Reject("candidate-unobserved-invalid")
    declarations: dict[str, tuple[str, str]] = {}
    for index, item in enumerate(unobserved):
        if not isinstance(item, dict):
            raise Reject("candidate-unobserved-invalid")
        require_keys(item, {"field", "blocked_by", "reason"}, f"unobserved[{index}]")
        field = item["field"]
        if field not in FACT_FIELDS or field in declarations:
            raise Reject("candidate-unobserved-invalid")
        blocked_by = item["blocked_by"]
        reason = safe_text(item["reason"], f"unobserved[{index}].reason", 512)
        if blocked_by != "primary-admitted" and blocked_by not in FACT_STAGE_ORDER:
            raise Reject("candidate-unobserved-cause-invalid", field)
        declarations[field] = (blocked_by, reason)
    actual_unobserved: set[str] = set()
    for field in FACT_FIELDS:
        fact = record[field]
        if not isinstance(fact, dict):
            raise Reject("candidate-fact-invalid", field)
        if fact.get("state") == "observed":
            require_keys(fact, {"state", "value"}, field)
            if not isinstance(fact["value"], dict):
                raise Reject("candidate-fact-invalid", field)
            continue
        if fact.get("state") != "not_observed":
            raise Reject("candidate-fact-invalid", field)
        require_keys(fact, {"state", "blocked_by", "reason"}, field)
        blocked_by = fact["blocked_by"]
        reason = safe_text(fact["reason"], f"{field}.reason", 512)
        declaration = declarations.get(field)
        if declaration != (blocked_by, reason):
            raise Reject("candidate-unobserved-accounting-mismatch", field)
        actual_unobserved.add(field)
        if blocked_by != "primary-admitted":
            cutoff = record["disposition"].get("blocker_stage") if isinstance(record["disposition"], dict) else None
            if blocked_by != cutoff:
                raise Reject("candidate-unobserved-cause-invalid", field)
            if FACT_STAGE_ORDER[blocked_by] >= FACT_STAGE_ORDER[FACT_FIELD_STAGE[field]]:
                raise Reject("candidate-unobserved-cause-not-earlier", field)
    if actual_unobserved != set(declarations):
        raise Reject("candidate-unobserved-accounting-mismatch")
    if status == "admitted" and actual_unobserved:
        raise Reject("candidate-admitted-incomplete")
    if status == "not-needed" and actual_unobserved != set(FACT_FIELDS):
        raise Reject("candidate-not-needed-has-observed-facts")


def validate_record(root: Path, revision: str, record: dict[str, Any], expected_id: str,
                    stage: str | None, require_final: bool, runner: Path | None = None) -> str:
    expected = candidate_metadata(expected_id)
    require_keys(record, {
        "schema_version", "candidate_id", "release", "preferred_artifact", "stage", "partial",
        "source", "build", "admission", "rom", "execution", "progress", "observations", "receipt",
        "unobserved", "disposition",
    }, "record")
    if record["schema_version"] != SCHEMA_VERSION:
        raise Reject("candidate-schema-unsupported", str(record["schema_version"]))
    if (record["candidate_id"], record["release"], record["preferred_artifact"]) != expected:
        raise Reject("candidate-identity-mismatch", expected_id)
    allowed_stages = {"source", "rights", "build", "identity", "mode", "progress", "final"}
    if record["stage"] not in allowed_stages or not isinstance(record["partial"], bool):
        raise Reject("candidate-stage-invalid", expected_id)
    if stage is not None and record["stage"] != stage:
        raise Reject("candidate-stage-mismatch", expected_id)
    disposition = record["disposition"]
    if not isinstance(disposition, dict) or not isinstance(disposition.get("status"), str):
        raise Reject("candidate-disposition-invalid", expected_id)
    status = disposition["status"]
    if status == "admitted":
        require_keys(disposition, {"status", "reason", "evidence"}, "disposition", {"primary_no_go_ref"})
        safe_text(disposition["reason"], "disposition.reason")
        if not isinstance(disposition["evidence"], (dict, list)) or not disposition["evidence"]:
            raise Reject("candidate-disposition-evidence-missing")
        if record["stage"] != "final" or record["partial"]:
            raise Reject("candidate-partial-not-final", expected_id)
    elif status == "no-go":
        require_keys(disposition, {"status", "category", "reason", "evidence", "blocker_stage"},
                     "disposition", {"primary_no_go_ref"})
        if disposition["category"] not in ALLOWED_NO_GO_CATEGORIES:
            raise Reject("candidate-no-go-category-invalid", expected_id)
        if disposition["blocker_stage"] != NO_GO_STAGE[disposition["category"]]:
            raise Reject("candidate-no-go-stage-invalid", expected_id)
        safe_text(disposition["reason"], "disposition.reason")
        if not isinstance(disposition["evidence"], (dict, list)) or not disposition["evidence"]:
            raise Reject("candidate-no-go-evidence-missing", expected_id)
        if record["stage"] != "final" or record["partial"]:
            raise Reject("candidate-partial-not-final", expected_id)
    elif status == "not-needed":
        require_keys(disposition, {"status", "reason", "primary_record_ref"}, "disposition")
        safe_text(disposition["reason"], "disposition.reason")
        if expected_id != CANDIDATES[1][0] or record["stage"] != "final" or record["partial"]:
            raise Reject("candidate-not-needed-invalid")
    elif status == "blocked-defect":
        require_keys(disposition, {"status", "category", "reason", "evidence", "blocker_stage"}, "disposition")
        if disposition["category"] not in {"harness", "emulation", "security"}:
            raise Reject("candidate-blocked-defect-invalid")
        safe_text(disposition["reason"], "disposition.reason")
        if not isinstance(disposition["evidence"], (dict, list)) or not disposition["evidence"]:
            raise Reject("candidate-blocked-defect-evidence-missing")
        if require_final:
            raise Reject("candidate-blocked-defect")
    elif status == "partial":
        require_keys(disposition, {"status", "reason", "evidence", "blocker_stage"}, "disposition")
        safe_text(disposition["reason"], "disposition.reason")
        if not isinstance(disposition["evidence"], (dict, list)) or not disposition["evidence"]:
            raise Reject("candidate-partial-evidence-missing")
        if not record["partial"] or record["stage"] == "final" or require_final:
            raise Reject("candidate-partial-not-final", expected_id)
    else:
        raise Reject("candidate-disposition-invalid", expected_id)
    if require_final and (record["stage"] != "final" or record["partial"]):
        raise Reject("candidate-partial-not-final", expected_id)
    for field in FACT_FIELDS:
        if not isinstance(record[field], dict):
            raise Reject("candidate-fact-invalid", field)
    _validate_not_observed(record, status)
    if status == "admitted":
        contract_error = validate_admitted_contract(record)
        if contract_error:
            raise Reject(contract_error)
    for field in FACT_FIELDS:
        fact = record[field]
        if fact["state"] != "observed":
            continue
        if field == "receipt":
            continue
        value = fact["value"]
        if field == "source":
            _validate_source(value)
        elif field == "build":
            source_fact = record["source"]
            if source_fact["state"] != "observed":
                raise Reject("candidate-build-source-missing")
            _validate_build(value, source_fact["value"])
        elif field == "admission":
            _validate_admission(value)
        elif field == "rom":
            _validate_rom(value)
        elif field == "execution":
            require_keys(value, {"profile", "actual_mode"}, "execution")
            safe_text(value["profile"], "execution.profile", 64)
            safe_text(value["actual_mode"], "execution.actual_mode", 64)
        elif field == "progress":
            source_fact = record["source"]
            if source_fact["state"] != "observed":
                raise Reject("candidate-progress-source-missing")
            _validate_progress(value, source_fact["value"])
        elif field == "observations":
            _validate_observation(value)
    if status == "no-go" and disposition["category"] == "build":
        if record["build"]["state"] != "observed":
            raise Reject("candidate-build-no-go-unbound")
        build_value = record["build"]["value"]
        if build_value["executed"] is False:
            failure = validate_build_isolation(build_value.get("build_isolation"),
                                               allow_environment_failure=True)
            if build_value["result"] != "not-run" or failure is None:
                raise Reject("candidate-build-no-go-unbound")
            evidence = disposition["evidence"]
            if not isinstance(evidence, dict) or evidence.get("isolation_failure") != failure:
                raise Reject("candidate-build-no-go-unbound")
            for field in ("rom", "execution", "progress", "observations", "receipt"):
                fact = record[field]
                if fact.get("state") != "not_observed" or fact.get("blocked_by") != "build":
                    raise Reject("candidate-build-no-go-facts-observed", field)
    if status == "admitted":
        if record["build"]["value"]["executed"] is not True \
                or record["build"]["value"]["result"] != "passed":
            raise Reject("candidate-admitted-build-incomplete")
        _validate_admitted_cross_bindings(root, revision, record)
        _check_phase20_admission(root, record)
    if record["receipt"]["state"] == "observed":
        if any(record[name]["state"] != "observed" for name in
               ("source", "rom", "build", "execution", "progress", "observations")):
            raise Reject("candidate-receipt-source-missing")
        _validate_receipt(record["receipt"]["value"], record, revision, root)
    if status == "admitted" and runner is not None:
        _run_admitted_candidate(root, runner, record)
    if status == "not-needed":
        _validate_not_needed_reference(root, revision, record)
    if expected_id == CANDIDATES[1][0] and status in {"admitted", "no-go"}:
        _validate_primary_no_go_reference(root, revision, record)
    return status


def record_path(root: Path, relative: str) -> dict[str, Any]:
    raw = read_regular(root, relative)
    return parse_json(raw, relative)


def _validate_record_set(root: Path) -> None:
    directory = root / "tests/data/cgb-candidates"
    if directory.is_symlink():
        raise Reject("candidate-attempt-set", "candidate record directory must not be a link")
    try:
        entries = list(directory.iterdir())
    except OSError:
        return
    expected = {PurePosixPath(path).name for path in RECORDS.values()}
    for entry in entries:
        if entry.suffix != ".json":
            continue
        if entry.name not in expected or entry.is_symlink() or not entry.is_file():
            raise Reject("candidate-attempt-set", f"unexpected record path: {entry.name}")


def validate_all(root: Path, revision: str, stage: str | None,
                 require_final: bool, runner: Path | None = None) -> tuple[list[dict[str, Any]], dict[str, str]]:
    contract = validate_source_contract(root, revision)
    _validate_record_set(root)
    records: list[dict[str, Any]] = []
    for candidate_id, relative in RECORDS.items():
        try:
            record = record_path(root, relative)
        except Reject as error:
            if error.code == "candidate-file-unavailable":
                raise Reject("candidate-record-missing", relative) from None
            raise
        records.append(record)
    error = validate_attempt_order(records, require_final=require_final)
    if error:
        raise Reject(error)
    for candidate, record in zip(CANDIDATES, records):
        validate_record(root, revision, record, candidate[0], stage, require_final, runner)
    return records, contract


def validate_one(root: Path, revision: str, relative: str, stage: str | None,
                 require_final: bool, runner: Path | None = None) -> tuple[dict[str, Any], dict[str, str]]:
    contract = validate_source_contract(root, revision)
    record = record_path(root, relative)
    candidate_id = record.get("candidate_id")
    if candidate_id not in RECORDS:
        raise Reject("candidate-identity-invalid", "record path has no fixed candidate identity")
    if relative != RECORDS[candidate_id]:
        raise Reject("candidate-record-path-mismatch", candidate_id)
    validate_record(root, revision, record, candidate_id, stage, require_final, runner)
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
        detail = output.strip().replace("\n", " ")[-512:]
        raise Reject("candidate-self-test-failed",
                     f"CLI exit={result.returncode} expected={expect_code}: {detail}")
    if expect_text and expect_text not in output:
        detail = output.strip().replace("\n", " ")[-512:]
        raise Reject("candidate-self-test-failed", f"CLI omitted {expect_text}: {detail}")
    return output


def _not_observed(field: str, blocked_by: str, reason: str) -> dict[str, str]:
    return {"state": "not_observed", "blocked_by": blocked_by, "reason": reason}


def synthetic_no_go_record(candidate: tuple[str, str, str],
                           primary_ref: dict[str, str] | None = None) -> dict[str, Any]:
    candidate_id, release, artifact = candidate
    cutoff_reason = "synthetic rights cutoff; no candidate source or game bytes were inspected"
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "candidate_id": candidate_id,
        "release": release,
        "preferred_artifact": artifact,
        "stage": "final",
        "partial": False,
        "source": _not_observed("source", "rights", cutoff_reason),
        "build": _not_observed("build", "rights", cutoff_reason),
        "admission": {"state": "observed", "value": {
            "decision_status": "no-go", "reason": "synthetic rights decision",
            "evidence": {"kind": "synthetic", "reference": "temporary self-test only"},
        }},
        "rom": _not_observed("rom", "rights", cutoff_reason),
        "execution": _not_observed("execution", "rights", cutoff_reason),
        "progress": _not_observed("progress", "rights", cutoff_reason),
        "observations": _not_observed("observations", "rights", cutoff_reason),
        "receipt": _not_observed("receipt", "rights", cutoff_reason),
        "unobserved": [
            {"field": field, "blocked_by": "rights", "reason": cutoff_reason}
            for field in FACT_FIELDS if field != "admission"
        ],
        "disposition": {
            "status": "no-go", "category": "rights", "blocker_stage": "rights",
            "reason": "Synthetic rights decision for contract tests only.",
            "evidence": {"kind": "synthetic", "reference": "temporary test repository"},
        },
    }
    if primary_ref is not None:
        record["disposition"]["primary_no_go_ref"] = primary_ref
    return record


def _commit_temp_paths(root: Path, paths: list[str], message: str) -> str:
    git(root, "add", *paths)
    git(root, "commit", "--quiet", "-m", message)
    return git(root, "rev-parse", "HEAD").decode("ascii").strip()


def _prepare_temp_repo(source_root: Path, root: Path) -> str:
    result = run_process(["git", "clone", "--quiet", "--shared", str(source_root), str(root)],
                         source_root, timeout=MAX_SUBPROCESS_SECONDS)
    if result.returncode != 0:
        raise Reject("candidate-self-test-repository-failed")
    git(root, "config", "user.name", "GabbaBoy Automation")
    git(root, "config", "user.email", "automation@users.noreply.github.com")
    for relative in (*CONTRACT_PATHS, "tests/scripts/test_cgb_candidate_order.py"):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_root / relative, destination)
    case_file = root / "tests/acceptance/synthetic-cgb-candidate.case"
    input_script = root / "tests/acceptance/inputs/synthetic-cgb-candidate.input"
    case_file.parent.mkdir(parents=True, exist_ok=True)
    input_script.parent.mkdir(parents=True, exist_ok=True)
    case_file.write_text("synthetic candidate case; no game bytes\n", encoding="utf-8")
    input_script.write_text("gbinput 1\n0 A down\n100 A up\n", encoding="ascii")
    runner = root / "tests/scripts/synthetic-runner.py"
    runner.write_text(
        "#!/usr/bin/env python3\n"
        "import os\n"
        "from pathlib import Path\n"
        "if any(key in os.environ for key in ('AWS_SECRET_ACCESS_KEY', 'GITHUB_TOKEN', 'GH_TOKEN')):\n"
        "    raise SystemExit(73)\n"
        "marker = Path('tests/data/cgb-candidates/runner-invocations.txt')\n"
        "marker.parent.mkdir(parents=True, exist_ok=True)\n"
        "with marker.open('a', encoding='utf-8') as stream:\n"
        "    stream.write('invoked\\n')\n"
        "print('acceptance id=synthetic-cgb-progress status=pass model=cgb-cpu-e profile=CGB-CPU-E mode=native-cgb')\n",
        encoding="utf-8",
    )
    runner.chmod(0o755)
    paths = [*CONTRACT_PATHS, "tests/scripts/test_cgb_candidate_order.py",
             "tests/scripts/synthetic-runner.py", "tests/acceptance/synthetic-cgb-candidate.case",
             "tests/acceptance/inputs/synthetic-cgb-candidate.input"]
    return _commit_temp_paths(root, paths, "synthetic candidate contract source snapshot")


def _write_synthetic_admission_fixture(root: Path) -> dict[str, Any]:
    fixture = "fixtures/synthetic-cgb"
    fixture_dir = root / fixture
    (fixture_dir / "evidence").mkdir(parents=True, exist_ok=True)
    (fixture_dir / "sandbox").mkdir(parents=True, exist_ok=True)
    rom = bytearray(32768)
    rom[0x100:0x103] = b"\xC3\x50\x01"
    rom[0x134:0x13C] = b"SYNTHCGB"
    rom[0x143] = 0x80
    rom[0x147] = 0x00
    rom[0x148] = 0x00
    rom[0x149] = 0x00
    checksum = 0
    for value in rom[0x134:0x14D]:
        checksum = (checksum - value - 1) & 0xFF
    rom[0x14D] = checksum
    source_files = {
        f"{fixture}/program.asm": b"; synthetic candidate build input; never executed\n",
        f"{fixture}/predicate.asm": b"; synthetic source anchor for a bounded progress predicate\n",
        f"{fixture}/sandbox/launcher-policy.json": b'{"environment":["PATH","LANG"],"network":false}\n',
    }
    other_files = {
        f"{fixture}/candidate.gbc": bytes(rom),
        f"{fixture}/LICENSE.txt": b"Synthetic test terms; not a candidate license decision.\n",
        f"{fixture}/evidence/grant.txt": b"Temporary synthetic fixture evidence only.\n",
    }
    for path, data in {**source_files, **other_files}.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    file_data = {**source_files, **other_files}
    file_records = [
        {"path": path, "size_bytes": len(data), "sha256": sha256(data)}
        for path, data in sorted(file_data.items())
    ]
    inputs = [item for item in file_records if item["path"] in source_files]
    grant_path = f"{fixture}/evidence/grant.txt"
    grant_digest = sha256(other_files[grant_path])
    recipe = "rgbasm -o synthetic.o program.asm; rgblink -o candidate.gbc synthetic.o"
    tool_revision = "b" * 40
    components = {
        "code": {"presence": "present", "terms": "Synthetic MIT-style test terms",
                 "evidence": {"path": grant_path, "sha256": grant_digest},
                 "covered_paths": [f"{fixture}/candidate.gbc", f"{fixture}/program.asm",
                                   f"{fixture}/predicate.asm"],
                 "scope": {"repository": True, "public_ci": True}},
        "art": {"presence": "absent", "reason": "Synthetic control has no separate art."},
        "audio_driver": {"presence": "absent", "reason": "Synthetic control has no audio driver."},
        "build_inputs": {"presence": "present", "terms": "Synthetic MIT-style test terms",
                         "evidence": {"path": grant_path, "sha256": grant_digest},
                         "covered_paths": [item["path"] for item in inputs],
                         "scope": {"repository": True, "public_ci": True}},
        "notices": {"presence": "present", "terms": "Synthetic test terms",
                    "evidence": {"path": grant_path, "sha256": grant_digest},
                    "covered_paths": [f"{fixture}/LICENSE.txt", grant_path],
                    "scope": {"repository": True, "public_ci": True}},
    }
    manifest = {
        "schema_version": 1,
        "fixture_kind": "synthetic-cgb-candidate-control",
        "decision": {"status": "approved", "reviewer_role": "synthetic-test",
                     "rationale": "Disposable self-test fixture; no candidate rights judgment.",
                     "component_rationale": {"code": "Synthetic control only.",
                                             "build_inputs": "Synthetic control only.",
                                             "notices": "Synthetic control only."}},
        "permissions": {"repository": True, "public_ci": True},
        "source": {"repository": "https://example.invalid/synthetic-cgb", "revision": "a" * 40},
        "inputs": inputs,
        "files": file_records,
        "build": {"recipe": recipe, "tools": [{"name": "rgbds", "version": "1.0.1",
                  "terms": "Synthetic MIT-style test terms", "source_repository": "https://example.invalid/rgbds",
                  "revision": tool_revision, "disposition": "build_only", "component": None,
                  "covered_paths": []}]},
        "components": components,
        "notices": {"local_path": f"{fixture}/LICENSE.txt",
                    "sha256": sha256(other_files[f"{fixture}/LICENSE.txt"]),
                    "index_path": "THIRD_PARTY_NOTICES.md"},
    }
    manifest_path = f"{fixture}/manifest.json"
    manifest_raw = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    (root / manifest_path).write_bytes(manifest_raw)
    manifest_digest = sha256(manifest_raw)
    license_digest = manifest["notices"]["sha256"]
    (root / "THIRD_PARTY_NOTICES.md").write_bytes((
        "### Manifest and notice digests\n\n"
        "| Fixture directory | `manifest.json` SHA-256 | `LICENSE.txt` SHA-256 |\n"
        "|---|---|---|\n"
        f"| `synthetic-cgb` | `{manifest_digest}` | `{license_digest}` |\n"
    ).encode("utf-8"))
    git(root, "add", fixture, "THIRD_PARTY_NOTICES.md")
    git(root, "add", "-f", f"{fixture}/candidate.gbc")
    git(root, "commit", "--quiet", "-m", "synthetic admitted CGB fixture")
    pin = git(root, "rev-parse", "HEAD").decode("ascii").strip()
    (root / f"{fixture}/admission.commit").write_text(pin + "\n", encoding="ascii")
    return {
        "fixture": fixture, "rom_path": f"{fixture}/candidate.gbc", "rom": bytes(rom),
        "rom_sha256": sha256(bytes(rom)), "manifest_path": manifest_path,
        "manifest_sha256": manifest_digest, "pin_path": f"{fixture}/admission.commit",
        "pin_commit": pin, "source_files": source_files, "inputs": inputs,
        "source_repository": manifest["source"]["repository"], "source_revision": "a" * 40,
        "recipe": recipe, "tool_revision": tool_revision, "tool_sha256": sha256(b"synthetic tool"),
        "manifest": manifest,
    }


def synthetic_admitted_record(root: Path, project_revision: str,
                              fixture: dict[str, Any], candidate: tuple[str, str, str] = CANDIDATES[0],
                              primary_no_go_ref: dict[str, str] | None = None) -> dict[str, Any]:
    runner_path = "tests/scripts/synthetic-runner.py"
    runner_sha = sha256(read_regular(root, runner_path))
    source_inventory = [
        {"path": path, "size_bytes": len(data), "sha256": sha256(data)}
        for path, data in sorted(fixture["source_files"].items())
    ]
    tool = {"name": "rgbds", "version": "1.0.1", "terms": "Synthetic MIT-style test terms",
            "source_repository": "https://example.invalid/rgbds", "revision": fixture["tool_revision"],
            "sha256": fixture["tool_sha256"]}
    isolation = {
        "mechanism": "synthetic-namespace-control",
        "source_identity": {"repository": fixture["source_repository"],
                            "revision": fixture["source_revision"]},
        "toolchain_identity": [{"name": tool["name"], "version": tool["version"],
                                 "revision": tool["revision"], "sha256": tool["sha256"]}],
        "launcher_policy": {"path": f"{fixture['fixture']}/sandbox/launcher-policy.json",
                             "sha256": sha256(fixture["source_files"][f"{fixture['fixture']}/sandbox/launcher-policy.json"])},
        "environment_allowlist": ["PATH", "LANG"],
        "privilege_escalation": False,
        "mounts": [{"root_label": "source", "access": "read-only"},
                   {"root_label": "toolchain", "access": "read-only"},
                   {"root_label": "output", "access": "read-write"}],
        "network_disabled": True, "credentials_absent": True,
        "probes": {
            "outside_root_read": {"baseline": "allowed", "restricted": "denied",
                                  "target": "outside-root", "log_id": "synthetic-outside-root",
                                  "log_sha256": sha256(b"synthetic outside-root denial")},
            "local_network": {"baseline": "allowed", "restricted": "denied",
                              "target": "local-endpoint", "log_id": "synthetic-local-network",
                              "log_sha256": sha256(b"synthetic network denial")},
        },
    }
    case_file = "tests/acceptance/synthetic-cgb-candidate.case"
    input_path = "tests/acceptance/inputs/synthetic-cgb-candidate.input"
    case_sha = sha256(immutable_blob(root, project_revision, case_file))
    input_sha = sha256(immutable_blob(root, project_revision, input_path))
    predicate_path = f"{fixture['fixture']}/predicate.asm"
    predicate_sha = sha256(fixture["source_files"][predicate_path])
    case_id = "synthetic-cgb-progress"
    controls = {
        "no_input": {"control_id": "no-input", "status": "fail", "raw_reason": "predicate-not-reached",
                     "observation_sha256": sha256(b"synthetic no-input observation")},
        "wrong_input": {"control_id": "wrong-input", "status": "fail", "raw_reason": "predicate-not-reached",
                        "observation_sha256": sha256(b"synthetic wrong-input observation")},
        "impossible_predicate": {"control_id": "impossible-predicate", "status": "fail",
                                  "raw_reason": "predicate-not-reached",
                                  "observation_sha256": sha256(b"synthetic impossible-predicate observation")},
    }
    positive = {"control_id": "positive", "status": "pass", "raw_reason": "predicate-reached",
                "observation_sha256": sha256(b"synthetic positive observation")}
    observations = {"checkpoints": [
        {"name": "play-start", "half_dots": 100, "rgb555_sha256": sha256(b"synthetic RGB555"),
         "pcm_sha256": sha256(b"synthetic PCM")},
        {"name": "progress-hit", "half_dots": 200, "rgb555_sha256": sha256(b"synthetic RGB555 hit"),
         "pcm_sha256": sha256(b"synthetic PCM hit")},
    ]}
    receipt_name = "potion-panic" if candidate == CANDIDATES[0] else "ucity-1.3"
    receipt_path = f"tests/data/cgb-candidates/evidence/{receipt_name}.receipt.json"
    receipt_doc = {
        "case_id": case_id, "rom_sha256": fixture["rom_sha256"], "profile": "cgb-cpu-e",
        "actual_mode": "native-cgb", "status": "pass", "budget_half_dots": 500000,
        "input_sha256": input_sha, "predicate_sha256": predicate_sha,
        "build_recipe_sha256": sha256(fixture["recipe"].encode("utf-8")),
        "project_source_revision": project_revision, "game_source_revision": fixture["source_revision"],
        "runner_sha256": runner_sha, "binary_sha256": runner_sha,
        "controls": controls, "positive": positive, "observations": observations,
    }
    write_json(root / receipt_path, receipt_doc)
    receipt_sha = sha256(read_regular(root, receipt_path))
    record = {
        "schema_version": SCHEMA_VERSION, "candidate_id": candidate[0],
        "release": candidate[1], "preferred_artifact": candidate[2], "stage": "final", "partial": False,
        "source": {"state": "observed", "value": {
            "repository": fixture["source_repository"], "revision": fixture["source_revision"],
            "submodules": [], "inventory": source_inventory, "build_inputs": fixture["inputs"],
        }},
        "build": {"state": "observed", "value": {
            "recipe": fixture["recipe"], "recipe_sha256": sha256(fixture["recipe"].encode("utf-8")),
            "tools": [tool], "executed": True, "result": "passed", "build_isolation": isolation,
        }},
        "admission": {"state": "observed", "value": {
            "decision_status": "approved", "manifest_path": fixture["manifest_path"],
            "manifest_sha256": fixture["manifest_sha256"], "pin_path": fixture["pin_path"],
            "pin_commit": fixture["pin_commit"],
        }},
        "rom": {"state": "observed", "value": {
            "path": fixture["rom_path"], "size_bytes": len(fixture["rom"]),
            "sha256": fixture["rom_sha256"], "header": _rom_header(fixture["rom"]),
            "build_recipe_sha256": sha256(fixture["recipe"].encode("utf-8")),
        }},
        "execution": {"state": "observed", "value": {"profile": "cgb-cpu-e", "actual_mode": "native-cgb"}},
        "progress": {"state": "observed", "value": {
            "case_id": case_id, "case_file": case_file, "case_sha256": case_sha,
            "input_script": {"path": input_path, "sha256": input_sha},
            "predicate": {"path": predicate_path, "sha256": predicate_sha,
                          "anchors": [{"offset": 0x100, "bytes_hex": "C3 50 01"}]},
            "budget_half_dots": 500000, "positive": positive, "controls": controls,
        }},
        "observations": {"state": "observed", "value": observations},
        "receipt": {"state": "observed", "value": {
            "path": receipt_path, "sha256": receipt_sha, "project_source_revision": project_revision,
            "game_source_revision": fixture["source_revision"], "case_sha256": case_sha,
            "input_sha256": input_sha, "predicate_sha256": predicate_sha,
            "runner_sha256": runner_sha, "binary_sha256": runner_sha,
        }},
        "unobserved": [],
        "disposition": {"status": "admitted", "reason": "Synthetic admitted control only.",
                         "evidence": {"kind": "synthetic", "reference": "temporary Phase 20 fixture"}},
    }
    if primary_no_go_ref is not None:
        record["disposition"]["primary_no_go_ref"] = primary_no_go_ref
    return record


def synthetic_not_needed_record(primary_ref: dict[str, str]) -> dict[str, Any]:
    reason = "fallback not needed after the immutable primary record was admitted"
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_id": CANDIDATES[1][0],
        "release": CANDIDATES[1][1],
        "preferred_artifact": CANDIDATES[1][2],
        "stage": "final",
        "partial": False,
        **{field: _not_observed(field, "primary-admitted", reason) for field in FACT_FIELDS},
        "unobserved": [
            {"field": field, "blocked_by": "primary-admitted", "reason": reason}
            for field in FACT_FIELDS
        ],
        "disposition": {
            "status": "not-needed",
            "reason": "Synthetic fallback control only.",
            "primary_record_ref": primary_ref,
        },
    }


def synthetic_build_isolation_no_go(root: Path, project_revision: str,
                                    fixture: dict[str, Any]) -> dict[str, Any]:
    record = synthetic_admitted_record(root, project_revision, fixture)
    reason = "network isolation was not available; candidate build scripts were not executed"
    record["build"]["value"]["executed"] = False
    record["build"]["value"]["result"] = "not-run"
    record["build"]["value"]["build_isolation"]["network_disabled"] = False
    for field in ("rom", "execution", "progress", "observations", "receipt"):
        record[field] = _not_observed(field, "build", reason)
    record["unobserved"] = [
        {"field": field, "blocked_by": "build", "reason": reason}
        for field in ("rom", "execution", "progress", "observations", "receipt")
    ]
    record["disposition"] = {
        "status": "no-go", "category": "build", "blocker_stage": "build",
        "reason": reason,
        "evidence": {"isolation_failure": "candidate-build-isolation-network"},
    }
    return record


def _current_revision(root: Path) -> str:
    return git(root, "rev-parse", "HEAD").decode("ascii").strip()


def _record_ref(root: Path, path: str, commit: str) -> dict[str, str]:
    raw = immutable_blob(root, commit, path)
    return {"path": path, "commit": commit, "sha256": sha256(raw)}


def _run_all(root: Path, *, runner: bool = True, expected_code: int = 0,
             expected_text: str = "PASS: candidate records") -> str:
    args = ["--check-all", "--repo-root", str(root), "--source-revision", _current_revision(root),
            "--require-final"]
    if runner:
        args.extend(("--runner", "tests/scripts/synthetic-runner.py"))
    return run_checker(root, *args, expect_code=expected_code, expect_text=expected_text)


def _runner_invocations(root: Path) -> int:
    marker = root / "tests/data/cgb-candidates/runner-invocations.txt"
    if not marker.exists():
        return 0
    return len(marker.read_text(encoding="utf-8").splitlines())


def _commit_record(root: Path, record: dict[str, Any], path: str,
                   extra_paths: tuple[str, ...] = ()) -> str:
    write_json(root / path, record)
    return _commit_temp_paths(root, [path, *extra_paths], "synthetic candidate record")


def _no_go_order_controls(root: Path) -> tuple[dict[str, str], str]:
    primary_path = RECORDS[CANDIDATES[0][0]]
    fallback_path = RECORDS[CANDIDATES[1][0]]
    primary_commit = _commit_record(root, synthetic_no_go_record(CANDIDATES[0]), primary_path)
    primary_ref = _record_ref(root, primary_path, primary_commit)
    fallback = synthetic_no_go_record(CANDIDATES[1], primary_ref)
    _commit_record(root, fallback, fallback_path)

    before = _runner_invocations(root)
    _run_all(root, runner=True)
    if _runner_invocations(root) != before:
        raise Reject("candidate-self-test-failed", "a no-go record invoked the candidate runner")

    primary_file = root / primary_path
    valid_primary = synthetic_no_go_record(CANDIDATES[0])
    primary_file.unlink()
    _run_all(root, expected_code=1, expected_text="candidate-record-missing")
    write_json(primary_file, valid_primary)

    mutated = copy.deepcopy(valid_primary)
    mutated["disposition"]["status"] = "admitted"
    write_json(primary_file, mutated)
    _run_all(root, expected_code=1, expected_text="candidate-fallback-not-eligible")

    mutated = copy.deepcopy(valid_primary)
    mutated["disposition"] = {
        "status": "blocked-defect", "category": "harness", "blocker_stage": "progress",
        "reason": "Synthetic unresolved control defect.", "evidence": {"kind": "synthetic"},
    }
    write_json(primary_file, mutated)
    _run_all(root, expected_code=1, expected_text="candidate-blocked-defect")

    partial = copy.deepcopy(valid_primary)
    partial["stage"] = "rights"
    partial["partial"] = True
    partial["disposition"] = {
        "status": "partial", "blocker_stage": "rights",
        "reason": "Synthetic rights-stage record; assessment remains open.",
        "evidence": {"kind": "synthetic"},
    }
    write_json(primary_file, partial)
    revision = _current_revision(root)
    partial_args = ["--check-record", primary_path, "--repo-root", str(root),
                    "--source-revision", revision, "--stage", "rights"]
    run_checker(root, *partial_args, expect_text="PASS: candidate record")
    run_checker(root, *partial_args, "--require-final", expect_code=1,
                expect_text="candidate-partial-not-final")

    write_json(primary_file, valid_primary)
    (root / "tests/data/cgb-candidates/third.json").write_text("{}\n", encoding="utf-8")
    _run_all(root, expected_code=1, expected_text="candidate-attempt-set")
    (root / "tests/data/cgb-candidates/third.json").unlink()

    reordered = copy.deepcopy(valid_primary)
    reordered["candidate_id"] = CANDIDATES[1][0]
    write_json(primary_file, reordered)
    _run_all(root, expected_code=1, expected_text="candidate-attempt-set")
    write_json(primary_file, valid_primary)
    _run_all(root)
    return primary_ref, primary_commit


def _admission_controls(root: Path, project_revision: str, fixture: dict[str, Any],
                        primary_no_go_ref: dict[str, str]) -> int:
    primary_path = RECORDS[CANDIDATES[0][0]]
    admitted_path = RECORDS[CANDIDATES[1][0]]
    receipt_path = "tests/data/cgb-candidates/evidence/ucity-1.3.receipt.json"

    build_no_go = synthetic_build_isolation_no_go(root, project_revision, fixture)
    build_no_go_commit = _commit_record(root, build_no_go, primary_path)
    primary_no_go_ref = _record_ref(root, primary_path, build_no_go_commit)
    fallback_no_go = synthetic_no_go_record(CANDIDATES[1], primary_no_go_ref)
    _commit_record(root, fallback_no_go, admitted_path)
    before = _runner_invocations(root)
    _run_all(root, runner=True)
    if _runner_invocations(root) != before:
        raise Reject("candidate-self-test-failed", "an isolation no-go executed a build or candidate")

    fallback_admitted = synthetic_admitted_record(
        root, project_revision, fixture, candidate=CANDIDATES[1], primary_no_go_ref=primary_no_go_ref,
    )
    fallback_commit = _commit_record(root, fallback_admitted, admitted_path, (receipt_path,))
    del fallback_commit
    before = _runner_invocations(root)
    _run_all(root, runner=True)
    if _runner_invocations(root) != before + 1:
        raise Reject("candidate-self-test-failed", "admitted fallback did not run exactly once")

    primary_path = RECORDS[CANDIDATES[0][0]]
    primary_receipt = "tests/data/cgb-candidates/evidence/potion-panic.receipt.json"
    admitted_primary = synthetic_admitted_record(root, project_revision, fixture)
    primary_commit = _commit_record(root, admitted_primary, primary_path, (primary_receipt,))
    primary_ref = _record_ref(root, primary_path, primary_commit)
    not_needed = synthetic_not_needed_record(primary_ref)
    _commit_record(root, not_needed, admitted_path)

    before = _runner_invocations(root)
    _run_all(root, runner=True)
    if _runner_invocations(root) != before + 1:
        raise Reject("candidate-self-test-failed", "not-needed fallback invoked or suppressed the primary runner")

    baseline = copy.deepcopy(admitted_primary)
    primary_record_path = root / primary_path
    baseline_bytes = primary_record_path.read_bytes()
    control_count = 0

    def mutation(label: str, change, expected: str, *, mutate_notices: bool = False) -> None:
        nonlocal control_count
        before_count = _runner_invocations(root)
        if mutate_notices:
            notice_path = root / "THIRD_PARTY_NOTICES.md"
            notice = notice_path.read_bytes()
            notice_path.write_bytes(notice + b"synthetic mutation\n")
            try:
                _run_all(root, expected_code=1, expected_text=expected)
            finally:
                notice_path.write_bytes(notice)
        else:
            if primary_record_path.read_bytes() != baseline_bytes:
                raise Reject("candidate-self-test-failed", f"{label} started from a mutated record")
            subject = copy.deepcopy(baseline)
            change(subject)
            write_json(root / primary_path, subject)
            try:
                _run_all(root, expected_code=1, expected_text=expected)
            finally:
                primary_record_path.write_bytes(baseline_bytes)
        if _runner_invocations(root) != before_count:
            raise Reject("candidate-self-test-failed", f"{label} executed the admitted runner")
        control_count += 1

    mutation("missing-isolation", lambda value: value["build"]["value"].pop("build_isolation"),
             "candidate-build-isolation-missing")
    mutation("network-enabled", lambda value: value["build"]["value"]["build_isolation"].update(
        network_disabled=False), "candidate-build-isolation-network")
    mutation("inherited-credential", lambda value: value["build"]["value"]["build_isolation"][
        "environment_allowlist"].append("AWS_SECRET_ACCESS_KEY"), "candidate-build-isolation-credentials")
    mutation("credential-presence", lambda value: value["build"]["value"]["build_isolation"].update(
        credentials_absent=False), "candidate-build-isolation-credentials")
    mutation("extra-writable-mount", lambda value: value["build"]["value"]["build_isolation"][
        "mounts"].append({"root_label": "extra", "access": "read-write"}),
        "candidate-build-isolation-mounts")
    mutation("privilege-escalation", lambda value: value["build"]["value"]["build_isolation"].update(
        privilege_escalation=True), "candidate-build-isolation-privilege")
    mutation("outside-root-allowed", lambda value: value["build"]["value"]["build_isolation"][
        "probes"]["outside_root_read"].update(restricted="allowed"),
        "candidate-build-isolation-outside-probe")
    mutation("local-network-allowed", lambda value: value["build"]["value"]["build_isolation"][
        "probes"]["local_network"].update(restricted="allowed"),
        "candidate-build-isolation-network-probe")
    mutation("compatibility-mode", lambda value: value["execution"]["value"].update(
        actual_mode="compatibility"), "candidate-native-mode-required")
    mutation("header-only-native-claim", lambda value: value["rom"]["value"]["header"].update(
        cgb_flag=0), "candidate-native-header-required")
    mutation("missing-progress-control", lambda value: value["progress"]["value"]["controls"].pop(
        "wrong_input"), "candidate-progress-controls-missing")
    mutation("incorrect-negative-control", lambda value: value["progress"]["value"]["controls"][
        "wrong_input"].update(raw_reason="predicate-reached"), "candidate-progress-control-invalid")
    mutation("altered-manifest-pin-digest", lambda value: value["admission"]["value"].update(
        manifest_sha256="f" * 64), "candidate-admission-manifest-mismatch")
    mutation("rewritten-rom-identity", lambda value: value["rom"]["value"].update(sha256="e" * 64),
        "candidate-admission-rom-mismatch")
    mutation("rewritten-predicate-source", lambda value: value["progress"]["value"]["predicate"].update(
        sha256="d" * 64), "candidate-predicate-not-source-anchored")
    mutation("rewritten-input-binding", lambda value: value["progress"]["value"]["input_script"].update(
        sha256="c" * 64), "candidate-progress-project-source-mismatch")
    mutation("altered-pcm-checkpoint", lambda value: value["observations"]["value"]["checkpoints"][0].update(
        pcm_sha256="b" * 64), "candidate-receipt-content-invalid")
    mutation("recipe-rom-mismatch", lambda value: value["build"]["value"].update(recipe="changed recipe"),
        "candidate-build-recipe-mismatch")
    mutation("blocked-defect-cannot-close", lambda value: value.update(disposition={
        "status": "blocked-defect", "category": "harness", "blocker_stage": "progress",
        "reason": "Synthetic unresolved defect.", "evidence": {"kind": "synthetic"},
    }), "candidate-blocked-defect")
    mutation("phase20-pin-is-authoritative", lambda value: None,
        "candidate-phase20-admission-failed", mutate_notices=True)

    fallback_baseline = copy.deepcopy(not_needed)
    fallback_record = root / admitted_path
    fallback_baseline_bytes = fallback_record.read_bytes()
    changed_fallback = copy.deepcopy(fallback_baseline)
    changed_fallback["preferred_artifact"] = "renamed-ucity.gbc"
    write_json(fallback_record, changed_fallback)
    try:
        _run_all(root, expected_code=1, expected_text="candidate-identity-mismatch")
    finally:
        fallback_record.write_bytes(fallback_baseline_bytes)
    if fallback_record.read_bytes() != fallback_baseline_bytes:
        raise Reject("candidate-self-test-failed", "fallback identity mutation was not restored")
    before_count = _runner_invocations(root)
    _run_all(root, runner=True)
    if _runner_invocations(root) != before_count + 1:
        raise Reject("candidate-self-test-failed", "restored evidence did not run exactly once")
    control_count += 1

    return control_count


def self_test(source_root: Path, selected_revision: str | None, controls_only: bool = False) -> None:
    """Exercise the public CLI with only synthetic records in a private disposable clone."""
    if selected_revision is not None:
        revision = resolve_source_revision(source_root, selected_revision)
        validate_source_contract(source_root, revision)
    with tempfile.TemporaryDirectory(prefix="gbb-candidate-contract-") as temporary:
        root = Path(temporary)
        project_revision = _prepare_temp_repo(source_root, root)
        fixture = _write_synthetic_admission_fixture(root)
        (root / "tests/data/cgb-candidates").mkdir(parents=True, exist_ok=True)
        primary_ref, primary_no_go_commit = _no_go_order_controls(root)

        unit_test = run_process(
            [sys.executable, "-I", str(source_root / "tests/scripts/test_cgb_candidate_order.py")],
            source_root,
        )
        if unit_test.returncode != 0:
            raise Reject("candidate-self-test-failed", "candidate contract assertions failed")

        controls = 8
        if controls_only:
            controls += _admission_controls(root, project_revision, fixture, primary_ref)
        else:
            # Keep a known no-go fallback reference valid in the synthetic history.
            _ = primary_no_go_commit
    if controls_only:
        print(f"PASS: candidate contract controls positives=5 negative_controls={controls} synthetic_only=true")
    else:
        print(f"PASS: candidate contract synthetic=2 order-controls={controls}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--self-test-controls", action="store_true")
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
        runner_path: Path | None = None
        if args.runner:
            runner = Path(args.runner)
            if not runner.is_absolute():
                runner = root / runner
            runner = runner.resolve(strict=True)
            if root != runner and root not in runner.parents:
                raise Reject("candidate-runner-path-invalid")
            if not runner.is_file() or not os.access(runner, os.X_OK):
                raise Reject("candidate-runner-unavailable")
            runner_path = runner
        if args.self_test:
            self_test(root, args.source_revision, controls_only=False)
            return 0
        if args.self_test_controls:
            self_test(root, args.source_revision, controls_only=True)
            return 0
        if not args.source_revision:
            raise Reject("candidate-source-revision-required")
        revision = resolve_source_revision(root, args.source_revision)
        if args.check_all:
            records, contract = validate_all(root, revision, args.stage, args.require_final, runner_path)
            print(f"PASS: candidate records count={len(records)} source={revision} "
                  f"checker={contract['tests/scripts/verify-cgb-candidates.py']}")
        else:
            relative = relative_path(args.check_record, "--check-record")
            record, contract = validate_one(root, revision, relative, args.stage, args.require_final, runner_path)
            print(f"PASS: candidate record id={record['candidate_id']} stage={record['stage']} "
                  f"source={revision} checker={contract['tests/scripts/verify-cgb-candidates.py']}")
        return 0
    except (Reject, OSError, subprocess.SubprocessError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
