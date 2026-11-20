#!/usr/bin/env python3
"""Fail-closed local promotion guard for the bounded Phase 24 recovery.

This guard controls only the authorized local GSD route. It does not claim to
prevent a repository administrator or another client from bypassing it.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import hmac
import json
import math
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest import mock
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence


GATE_PATH = ".github/scripts/phase24-promotion-gate.py"
PLAN_REV = "6d5359f90297687bc8cc4535cc5d4e2ee7921f8e"
PLAN_PARENT = "febaa91c969daf2f82ac85424eb4623684ecdfc7"
PLAN_TREE = "2b1588386f244c71e13480b5663629820e8dcc29"
PLAN_BLOB = "cf0101b90e254e9e333ec681c79a7a5358c3d91b"
PLAN_SHA256 = "367628081211701c4ef67fb8254b40969f3e921f2da6a531186c2e2a248e5f5f"
PLAN_PATH_SHA256 = "981d088bc4d660fbb67e39db130bb8ec6bba081e6717b99ab9ec825388cdc72e"
DISCUSSION_REV = "6d5359f90297687bc8cc4535cc5d4e2ee7921f8e"
DISCUSSION_TREE = "2b1588386f244c71e13480b5663629820e8dcc29"
DISCUSSION_BLOB = "fa61417d8b8c6df967cb8f3be78dcff098d47e4e"
DISCUSSION_SHA256 = "6f5ad7a42a31aa22ba7dc398e62ad447778525609b58c047bf15a324d8b0744c"
DISCUSSION_PATH_SHA256 = "c0600dcc6a37ca945963f6e2d89a3c0509c324cca4c07f143f92916e49703657"
CLOSEOUT_REV = "9bf8048de96b9f40898238a0ef9b8a723b04bbe5"
CLOSEOUT_TREE = "8f1b848155d0a24492ad6023da07e3b286fc79f4"
CLOSEOUT_BLOB = "5518083f3bf5cecb8ba3eb9e127dc730a64bb4d8"
CLOSEOUT_SHA256 = "5fad7cb8bfa8355338081f315240bef918bf085883f2d61d502363c641fb5e5b"
CLOSEOUT_PATH_SHA256 = "56f44d6804c1ae7ca224578d88d51d10a3bc086f9844bae48bcfaae0f044f703"
SOURCE_PARENT = "7761be6f90041efd0bb6928279c002a369962d7f"
SOURCE_TREE = "1c4c9d2162a3fc32cff2a1205215511372372a56"
D225_PLAN_REV = "570279b42491f06527f754c42ce482e395241ba1"
D225_PLAN_TREE = "eff1298df62b7f43308c845f9d07bc0eb5d89d44"
D225_GATE_REV = "e1f072f23d2d6a6fcfb328f0b30f224fe006c533"
D225_GATE_PARENT = D225_PLAN_REV
D225_GATE_TREE = "f02887b8ef6addb08c5bfe31a89e7a50c898a704"
D225_GATE_BLOB = "13518dd3a40871c7476a9480a372b43d5550cadd"
D225_GATE_SHA256 = "8c75d1963a56dd7086c5c0d97d11d2f7738abc60c1d9d92c2dd2c4d38bbe9daf"
D225_STOP_CANDIDATE = "e16873ad03c725e3564d857d8a5ae4850c2049e1"
D225_STOP_TREE = "44daf50eecc641ea1eb56a2910ed92bbdfcffd9d"
D226_PLAN_REV = "9bf8048de96b9f40898238a0ef9b8a723b04bbe5"
D226_PLAN_PARENT = D225_STOP_CANDIDATE
D226_PLAN_TREE = "8f1b848155d0a24492ad6023da07e3b286fc79f4"
D226_GATE_REV = "f9ccf6b4a211bc33270f6f8172e40a4e4cb22cba"
D226_GATE_PARENT = D226_PLAN_REV
D226_GATE_TREE = "e2727a6873c0cce0617934e69d14844001cdbb96"
D226_GATE_BLOB = "d37be8847ca654b0b318103fef07e130ad918a56"
D226_GATE_SHA256 = "ea6c281eee7f3161235b235d6d67e9f4d11ebcbb230f42b9a51ee491a85afb9e"
D226_STOP_INTERMEDIATE = "0e17d1fc34ebbae530bd1ba71279905ee4378ab7"
D226_STOP_INTERMEDIATE_TREE = "2493116af15bd1b5f65b5206b67e3456606717ec"
D226_STOP_CANDIDATE = "febaa91c969daf2f82ac85424eb4623684ecdfc7"
D226_STOP_PARENT = "0e17d1fc34ebbae530bd1ba71279905ee4378ab7"
D226_STOP_TREE = "5f903b66071ec9f2bdbc6d007e9b917c4079c45c"
D226_HISTORY_PINS = {
    "d225_gate_rev": D225_GATE_REV,
    "d225_gate_tree": D225_GATE_TREE,
    "d225_gate_blob": D225_GATE_BLOB,
    "d225_gate_sha256": D225_GATE_SHA256,
    "d225_stop_candidate": D225_STOP_CANDIDATE,
    "d225_stop_parent": D225_GATE_REV,
    "d225_stop_tree": D225_STOP_TREE,
    "d226_plan_rev": D226_PLAN_REV,
    "d226_plan_parent": D226_PLAN_PARENT,
    "d226_plan_tree": D226_PLAN_TREE,
    "d226_gate_rev": D226_GATE_REV,
    "d226_gate_parent": D226_GATE_PARENT,
    "d226_gate_tree": D226_GATE_TREE,
    "d226_gate_blob": D226_GATE_BLOB,
    "d226_gate_sha256": D226_GATE_SHA256,
    "d226_stop_intermediate": D226_STOP_INTERMEDIATE,
    "d226_stop_intermediate_parent": D226_GATE_REV,
    "d226_stop_intermediate_tree": D226_STOP_INTERMEDIATE_TREE,
    "d226_waiter_correction_blob": "0eda5971bf059cbdba560c3b9d9bd8d6cb1ecb8d",
    "d226_coverage_correction_blob": "060f8f7626fb7f39cadd5d2782c5416ee7974d8d",
    "d226_stop_candidate": D226_STOP_CANDIDATE,
    "d226_stop_parent": D226_STOP_PARENT,
    "d226_stop_tree": D226_STOP_TREE,
}
D224_GATE_REV = "dc321ba3fe51a7391ed9d1c9680cfc621d626d9d"
D224_GATE_PARENT = "9b0023fd4954fcbd970ce33fe599a029e51701a5"
D224_GATE_TREE = "7f954b15d98120bdec4d2486e96b6f8e5b705497"
D224_GATE_BLOB = "a97a45121d2c4550a853febff6674cbeb32ccd34"
D224_GATE_SHA256 = "1484f3d0aca1a5d79cbf7475cba94f95b400f9f56d99fbe3fbebea42dadcf37c"
D209_REV = "96d502d4733ac54aa8bf7fbfd7813065143771dc"
D220_SHA = "f19d5ae2f5819d18074a68e1e80d959dc31b1302"
D221_SHA = "9bab99b6af2462291d8481ce5da14fa72c1777e4"
D221_TREE = "b0008efaf254b07a7dbc0549473f57aad472e6a0"
D221_EXEC_REV = "6f682cc93f499ddfc8ee61ced3a24d1af5d67418"
REQUIREMENTS_BLOB = "fc86255cef47ac9296cb62bbc0a3038f733acf0a"
ROADMAP_BLOB = "bd710ffb3158b9fef42b531560c29445637a6cb3"
STATE_FORKS_BLOB = "42e095bf270510b757510282d5c7172c38b04406"
PLANNING_HYGIENE_SHA256 = "c80afba104ff252da2161a710d59b47ebda97e680973f6fb4d3897d179c7b9c8"
EXPECTED_REPO = "szTheory/gabbaboy"
EXPECTED_URL = "https://github.com/szTheory/gabbaboy.git"
EXPECTED_PR = 154
EXPECTED_BASE = "main"
REQUIRED_CONTEXTS = ("required-native", "fixture-repro", "preview-package-smoke")
REQUIRED_WORKFLOW_PATHS = {
    "required-native": ".github/workflows/ci.yml",
    "fixture-repro": ".github/workflows/fixture-repro.yml",
    "preview-package-smoke": ".github/workflows/preview.yml",
}
ALLOWED_ROOT_STATUS = ".planning/state.json"
MAX_JSON_BYTES = 2_000_000
MAX_REPORT_BYTES = 2_000_000
MAX_CMAKE_CACHE_BYTES = 1_000_000
MAX_OUTPUT_BYTES = 1_000_000
CHILD_TIMEOUT = 30.0
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
FULL_SHA256 = re.compile(r"^[0-9a-f]{64}$")
PLAN_SOURCE_PATHS = (
    "tests/scripts/verify-no-phase-paths.py",
    "tests/scripts/verify-planning-hygiene.py",
    "tests/scripts/verify-state-forks.py",
    ".github/scripts/wait-exact-head-ci.py",
    ".github/scripts/verify-workflow-policy.py",
    ".github/workflows/preview.yml",
    "tests/scripts/verify-workflow-policy-coverage.py",
)
EXPECTED_CANDIDATE_CORRECTIONS = (
    ".github/scripts/wait-exact-head-ci.py",
    "tests/scripts/verify-workflow-policy-coverage.py",
)
CORRECTION_SOURCE_PINS = {
    ".github/scripts/wait-exact-head-ci.py": ("100755", "blob", "0eda5971bf059cbdba560c3b9d9bd8d6cb1ecb8d"),
    "tests/scripts/verify-workflow-policy-coverage.py": ("100644", "blob", "771e64dd919f91dcdb8ef4163d985c517b82e6cb"),
}
D226_ROUTE_CORRECTION_PINS = {
    ".github/scripts/wait-exact-head-ci.py": ("100755", "blob", "0eda5971bf059cbdba560c3b9d9bd8d6cb1ecb8d"),
    "tests/scripts/verify-workflow-policy-coverage.py": ("100644", "blob", "060f8f7626fb7f39cadd5d2782c5416ee7974d8d"),
}
EXPECTED_CANDIDATE_CORRECTION_HASHES = {hashlib.sha256(path.encode("utf-8")).hexdigest(): path for path in EXPECTED_CANDIDATE_CORRECTIONS}
ALLOWED_CANDIDATE_PATH_HASHES = set(EXPECTED_CANDIDATE_CORRECTION_HASHES) | {CLOSEOUT_PATH_SHA256}
HISTORICAL_PATHS = {
    ".planning/milestones/v0.4-REQUIREMENTS.md": REQUIREMENTS_BLOB,
    ".planning/milestones/v0.4-ROADMAP.md": ROADMAP_BLOB,
    "tests/data/state-forks.json": STATE_FORKS_BLOB,
}
HOSTILE_GIT_ENV = {
    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE",
    "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0",
    "GIT_CONFIG_VALUE_0", "GIT_CEILING_DIRECTORIES",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM", "GIT_PREFIX", "GIT_SHALLOW_FILE",
    "GIT_QUARANTINE_PATH", "GIT_TRACE", "GIT_TRACE_SETUP", "GIT_TRACE_PACKET",
    "GIT_ASKPASS", "SSH_ASKPASS",
}
SAFE_PROCESS_ENV = (
    "PATH", "SYSTEMROOT", "SystemRoot", "WINDIR", "PATHEXT", "COMSPEC",
    "TMPDIR", "TMP", "TEMP",
)
AUTH_ENV_KEYS = SAFE_PROCESS_ENV + (
    "HOME", "XDG_CONFIG_HOME", "GH_CONFIG_DIR", "GH_TOKEN", "GITHUB_TOKEN",
)


class GateError(Exception):
    """A deliberate fail-closed refusal with a stable machine-readable reason."""

    def __init__(self, reason: str, message: str | None = None):
        super().__init__(message or reason)
        self.reason = reason


def deny(reason: str, message: str | None = None) -> None:
    raise GateError(reason, message)


def valid_sha(value: Any) -> bool:
    return type(value) is str and FULL_SHA.fullmatch(value) is not None


def valid_sha256(value: Any) -> bool:
    return type(value) is str and FULL_SHA256.fullmatch(value) is not None


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            deny("duplicate_json_key", f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    deny("nonfinite_json_number", f"non-finite JSON number: {value}")


def _finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        deny("nonfinite_json_number", "non-finite JSON number")
    return parsed


def strict_json_bytes(data: bytes, *, max_bytes: int = MAX_JSON_BYTES) -> Any:
    if len(data) > max_bytes:
        deny("json_too_large")
    try:
        text = data.decode("utf-8", errors="strict")
        return json.loads(text, object_pairs_hook=_unique_pairs, parse_constant=_reject_constant, parse_float=_finite_float)
    except GateError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        deny("malformed_json", str(exc))


def exact_keys(value: Any, expected: Iterable[str], label: str) -> Mapping[str, Any]:
    if type(value) is not dict or set(value) != set(expected):
        deny("schema_keys", f"{label} has missing, extra, or non-object fields")
    return value


def require_type(value: Any, expected: type, label: str) -> Any:
    if type(value) is not expected:
        deny("schema_type", f"{label} has wrong type")
    return value


def require_sha(value: Any, label: str) -> str:
    if not valid_sha(value):
        deny("invalid_sha", f"{label} must be a full lowercase SHA-1")
    return value


def require_digest(value: Any, label: str) -> str:
    if not valid_sha256(value):
        deny("invalid_sha256", f"{label} must be a full lowercase SHA-256")
    return value


def reject_hostile_git_environment(env: Mapping[str, str] | None = None) -> None:
    current = os.environ if env is None else env
    offenders = sorted(name for name in HOSTILE_GIT_ENV if name in current)
    for name in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM"):
        if name in current and current[name] != os.devnull:
            offenders.append(name)
    if offenders:
        deny("hostile_git_environment", "hostile Git environment selectors are present")


def source_git_env(env: Mapping[str, str] | None = None) -> dict[str, str]:
    current = os.environ if env is None else env
    safe = {name: current[name] for name in SAFE_PROCESS_ENV if name in current}
    safe.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "LC_ALL": "C",
    })
    return safe


def auth_environment(env: Mapping[str, str] | None = None) -> dict[str, str]:
    current = os.environ if env is None else env
    safe = {name: current[name] for name in AUTH_ENV_KEYS if name in current}
    for name in HOSTILE_GIT_ENV:
        safe.pop(name, None)
    safe.pop("GH_REPO", None)
    safe.pop("GH_HOST", None)
    safe.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GH_PROMPT_DISABLED": "1",
        "GH_HOST": "github.com",
        "LC_ALL": "C",
    })
    return safe


def fixed_push_argv(candidate_sha: str, branch: str) -> list[str]:
    require_sha(candidate_sha, "candidate SHA")
    if type(branch) is not str or re.fullmatch(r"[A-Za-z0-9._/-]{1,200}", branch) is None or branch.startswith("-") or ".." in branch:
        deny("invalid_pr_branch")
    return [
        "git", "--no-replace-objects", "-c", "credential.helper=",
        "-c", "credential.helper=!gh auth git-credential",
        "-c", "credential.interactive=false", "push", "origin",
        f"{candidate_sha}:refs/heads/{branch}",
    ]


def fixed_merge_argv(candidate_sha: str) -> list[str]:
    require_sha(candidate_sha, "candidate SHA")
    return [
        "gh", "pr", "merge", str(EXPECTED_PR), "--repo", EXPECTED_REPO,
        "--merge", "--match-head-commit", candidate_sha,
    ]


@dataclass(frozen=True)
class DiffEntry:
    old_mode: str
    new_mode: str
    old_oid: str
    new_oid: str
    status: str
    path: str
    raw_path: bytes | None = None

    @property
    def path_bytes(self) -> bytes:
        if self.raw_path is not None:
            return self.raw_path
        return self.path.encode("utf-8", errors="strict")


def parse_raw_nul_diff(data: bytes) -> list[DiffEntry]:
    if not data or not data.endswith(b"\x00"):
        deny("malformed_raw_diff")
    parts = data[:-1].split(b"\x00")
    if len(parts) % 2:
        deny("malformed_raw_diff")
    entries: list[DiffEntry] = []
    for index in range(0, len(parts), 2):
        try:
            fields = parts[index].decode("ascii", errors="strict").split()
            path = parts[index + 1].decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            deny("malformed_raw_diff")
        raw_path = parts[index + 1]
        if len(fields) != 5 or not fields[0].startswith(":"):
            deny("malformed_raw_diff")
        old_mode, new_mode = fields[0][1:], fields[1]
        old_oid, new_oid, status = fields[2], fields[3], fields[4]
        if re.fullmatch(r"[0-7]{6}", old_mode) is None or re.fullmatch(r"[0-7]{6}", new_mode) is None:
            deny("malformed_raw_diff")
        if re.fullmatch(r"[0-9a-f]{40}", old_oid) is None or re.fullmatch(r"[0-9a-f]{40}", new_oid) is None:
            deny("malformed_raw_diff")
        if status not in {"A", "M", "D", "T"} or not path or path.startswith("/") or ".." in Path(path).parts:
            deny("malformed_raw_diff")
        entries.append(DiffEntry(old_mode, new_mode, old_oid, new_oid, status, path, raw_path))
    if len({entry.path for entry in entries}) != len(entries):
        deny("duplicate_diff_path")
    return entries


class Git:
    def __init__(self, root: Path, *, env: Mapping[str, str] | None = None, timeout: float = CHILD_TIMEOUT):
        self.root = root.resolve(strict=True)
        self.env = dict(source_git_env() if env is None else env)
        self.timeout = timeout

    def run(self, *args: str, input_bytes: bytes | None = None, allow_failure: bool = False, timeout: float | None = None) -> bytes:
        result = self.run_result(*args, input_bytes=input_bytes, timeout=timeout)
        if result.returncode and not allow_failure:
            deny("git_read_failed", "Git object or repository read failed")
        return result.stdout

    def run_result(self, *args: str, input_bytes: bytes | None = None, timeout: float | None = None) -> subprocess.CompletedProcess[bytes]:
        argv = ["git", "--no-replace-objects", "-C", str(self.root), *args]
        try:
            result = subprocess.run(
                argv, input=input_bytes, capture_output=True, check=False,
                timeout=self.timeout if timeout is None else timeout, env=self.env,
            )
        except subprocess.TimeoutExpired:
            deny("git_timeout")
        if len(result.stdout) > MAX_OUTPUT_BYTES or len(result.stderr) > MAX_OUTPUT_BYTES:
            deny("git_output_too_large")
        return result

    def text(self, *args: str, allow_failure: bool = False) -> str:
        try:
            return self.run(*args, allow_failure=allow_failure).decode("utf-8", errors="strict").strip()
        except UnicodeDecodeError:
            deny("git_output_encoding")

    def object_type(self, rev: str) -> str:
        require_sha(rev, "Git revision")
        value = self.text("cat-file", "-t", rev)
        if self.text("rev-parse", "--verify", rev) != rev:
            deny("non_original_object")
        return value

    def blob(self, rev: str, path: str) -> bytes:
        require_sha(rev, "Git revision")
        return self.run("show", f"{rev}:{path}")

    def tree(self, rev: str) -> str:
        require_sha(rev, "Git revision")
        return self.text("rev-parse", f"{rev}^{{tree}}")

    def parents(self, rev: str) -> list[str]:
        require_sha(rev, "Git revision")
        line = self.text("rev-list", "--parents", "-n", "1", rev)
        fields = line.split()
        if not fields or fields[0] != rev or any(not valid_sha(item) for item in fields):
            deny("invalid_commit_parents")
        return fields[1:]

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        require_sha(ancestor, "ancestor")
        require_sha(descendant, "descendant")
        return self.run_result("merge-base", "--is-ancestor", ancestor, descendant).returncode == 0

    def exists(self, *args: str) -> bool:
        return self.run_result(*args).returncode == 0

    def raw_diff(self, before: str, after: str) -> list[DiffEntry]:
        raw = self.run("diff", "--no-ext-diff", "--no-renames", "--raw", "-z", "--no-abbrev", before, after)
        return parse_raw_nul_diff(raw)

    def tree_entry(self, rev: str, path: str) -> tuple[str, str, str]:
        require_sha(rev, "tree revision")
        raw = self.run("ls-tree", "-r", "-z", rev, "--", path)
        if not raw.endswith(b"\0"):
            deny("malformed_tree_entry")
        records = raw[:-1].split(b"\0") if raw else []
        if len(records) != 1:
            deny("tree_entry_cardinality")
        header, separator, raw_path = records[0].partition(b"\t")
        fields = header.split(b" ")
        if not separator or len(fields) != 3 or raw_path != path.encode("utf-8"):
            deny("malformed_tree_entry")
        try:
            mode, object_type, oid = (field.decode("ascii", errors="strict") for field in fields)
        except UnicodeDecodeError:
            deny("malformed_tree_entry")
        if re.fullmatch(r"[0-7]{6}", mode) is None or object_type != "blob" or re.fullmatch(r"[0-9a-f]{40}", oid) is None:
            deny("malformed_tree_entry")
        return mode, object_type, oid

    def tree_entry_by_path_digest(self, rev: str, expected_tree: str, path_sha256: str) -> tuple[str, str, str]:
        require_sha(rev, "Git tree revision")
        require_sha(expected_tree, "expected Git tree")
        require_digest(path_sha256, "raw path SHA-256")
        if self.object_type(rev) != "commit" or self.tree(rev) != expected_tree:
            deny("planning_tree_mismatch")
        listing = self.run("ls-tree", "-r", "-z", "--full-tree", rev)
        mode, object_type, oid = _select_tree_entry(listing, path_sha256)
        if mode != "100644" or object_type != "blob":
            deny("planning_entry_metadata")
        return mode, object_type, oid

    def pinned_blob(self, rev: str, expected_tree: str, path_sha256: str, expected_oid: str, expected_sha256: str) -> bytes:
        require_sha(expected_oid, "expected planning blob")
        require_digest(expected_sha256, "expected planning content SHA-256")
        mode, object_type, oid = self.tree_entry_by_path_digest(rev, expected_tree, path_sha256)
        if (mode, object_type, oid) != ("100644", "blob", expected_oid):
            deny("planning_blob_pin_mismatch")
        if self.text("cat-file", "-t", oid) != "blob":
            deny("planning_entry_not_blob")
        content = self.run("cat-file", "blob", oid)
        if digest_bytes(content) != expected_sha256:
            deny("planning_blob_digest_mismatch")
        return content


def _select_tree_entry(listing: bytes, path_sha256: str) -> tuple[str, str, str]:
    require_digest(path_sha256, "raw path SHA-256")
    if type(listing) is not bytes or not listing or not listing.endswith(b"\x00"):
        deny("malformed_planning_tree")
    records = listing[:-1].split(b"\x00")
    if not records or any(not record for record in records):
        deny("malformed_planning_tree")
    seen_paths: set[bytes] = set()
    matches: list[tuple[str, str, str]] = []
    valid_modes = {
        (b"100644", b"blob"), (b"100755", b"blob"), (b"120000", b"blob"),
        (b"160000", b"commit"), (b"040000", b"tree"),
    }
    for record in records:
        header, separator, raw_path = record.partition(b"\t")
        fields = re.fullmatch(rb"([0-7]{6}) (blob|commit|tree) ([0-9a-f]{40})", header)
        if (not separator or not raw_path or fields is None
                or (fields.group(1), fields.group(2)) not in valid_modes):
            deny("malformed_planning_tree")
        if raw_path in seen_paths:
            deny("duplicate_planning_tree_path")
        seen_paths.add(raw_path)
        if digest_bytes(raw_path) == path_sha256:
            try:
                matches.append(tuple(field.decode("ascii", errors="strict") for field in fields.groups()))
            except UnicodeDecodeError:
                deny("malformed_planning_tree")
    if not matches:
        deny("planning_path_missing")
    if len(matches) != 1:
        deny("planning_path_ambiguous")
    return matches[0]


def _candidate_contains(git: Git, base_sha: str, candidate_sha: str) -> bool:
    return git.is_ancestor(base_sha, candidate_sha)


def _frontmatter_list(raw: bytes, field: str) -> tuple[str, ...]:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        deny("plan_encoding")
    match = re.search(rf"(?ms)^\s*{re.escape(field)}:\s*\n((?:[ \t]+-\s+[^\n]+\n)+)", text)
    if match is None:
        deny("plan_scope_missing", f"plan is missing {field}")
    values = tuple(re.sub(r"\s+#.*$", "", line.strip()[2:]).strip() for line in match.group(1).splitlines())
    if not values or len(set(values)) != len(values) or any(not value or value.startswith("/") or ".." in Path(value).parts for value in values):
        deny("plan_scope_invalid", f"plan {field} is malformed")
    return values


def parse_plan_scopes(raw: bytes) -> tuple[tuple[str, ...], tuple[str, ...]]:
    sources = _frontmatter_list(raw, "source_allowlist")
    corrections = _frontmatter_list(raw, "correction_allowlist")
    if sources != (*PLAN_SOURCE_PATHS, GATE_PATH):
        deny("plan_source_scope_changed")
    if corrections != EXPECTED_CANDIDATE_CORRECTIONS:
        deny("plan_correction_scope_changed")
    return sources, corrections


def current_root(git: Git) -> tuple[str, str, str]:
    root = git.text("rev-parse", "--show-toplevel")
    absolute_git_dir = git.text("rev-parse", "--absolute-git-dir")
    branch = git.text("symbolic-ref", "--quiet", "--short", "HEAD")
    if Path(root).resolve(strict=True) != git.root or not branch.startswith("gsd/phase-24-"):
        deny("wrong_repository_or_branch")
    return root, absolute_git_dir, branch


def _validate_inherited_gate_boundary(git: Git) -> dict[str, str]:
    """Prove the checked D-227 route inherits the exact frozen D-226 gate."""
    if (git.object_type(D225_PLAN_REV) != "commit" or git.tree(D225_PLAN_REV) != D225_PLAN_TREE
            or git.parents(D225_PLAN_REV) != [SOURCE_PARENT]):
        deny("d225_plan_baseline_mismatch")
    if (git.object_type(D225_GATE_REV) != "commit" or git.tree(D225_GATE_REV) != D225_GATE_TREE
            or git.parents(D225_GATE_REV) != [D225_GATE_PARENT]):
        deny("d225_gate_baseline_mismatch")
    if (git.tree_entry(D225_GATE_REV, GATE_PATH) != ("100644", "blob", D225_GATE_BLOB)
            or digest_bytes(git.blob(D225_GATE_REV, GATE_PATH)) != D225_GATE_SHA256):
        deny("d225_gate_blob_mismatch")
    d225_transition = git.raw_diff(D225_PLAN_REV, D225_GATE_REV)
    if (len(d225_transition) != 1
            or (d225_transition[0].path_bytes, d225_transition[0].status, d225_transition[0].old_mode,
                d225_transition[0].new_mode, d225_transition[0].old_oid, d225_transition[0].new_oid)
            != (GATE_PATH.encode("ascii"), "M", "100644", "100644", D224_GATE_BLOB, D225_GATE_BLOB)):
        deny("d225_gate_transition_mismatch")
    if (git.object_type(D224_GATE_REV) != "commit" or git.tree(D224_GATE_REV) != D224_GATE_TREE
            or git.parents(D224_GATE_REV) != [D224_GATE_PARENT]):
        deny("d224_gate_baseline_mismatch")
    if (git.tree_entry(D224_GATE_REV, GATE_PATH) != ("100644", "blob", D224_GATE_BLOB)
            or digest_bytes(git.blob(D224_GATE_REV, GATE_PATH)) != D224_GATE_SHA256):
        deny("d224_gate_blob_mismatch")

    if (git.object_type(D225_STOP_CANDIDATE) != "commit"
            or git.tree(D225_STOP_CANDIDATE) != D225_STOP_TREE
            or git.parents(D225_STOP_CANDIDATE) != [D225_GATE_REV]
            or git.tree_entry(D225_STOP_CANDIDATE, GATE_PATH) != ("100644", "blob", D225_GATE_BLOB)
            or any(entry.path_bytes == GATE_PATH.encode("ascii") for entry in git.raw_diff(D225_GATE_REV, D225_STOP_CANDIDATE))):
        deny("d225_stop_candidate_mismatch")
    if (git.object_type(D226_PLAN_REV) != "commit"
            or git.tree(D226_PLAN_REV) != D226_PLAN_TREE
            or git.parents(D226_PLAN_REV) != [D226_PLAN_PARENT]
            or git.tree_entry(D226_PLAN_REV, GATE_PATH) != ("100644", "blob", D225_GATE_BLOB)
            or any(entry.path_bytes == GATE_PATH.encode("ascii") for entry in git.raw_diff(D225_STOP_CANDIDATE, D226_PLAN_REV))):
        deny("d226_plan_baseline_mismatch")
    if (git.object_type(D226_GATE_REV) != "commit"
            or git.tree(D226_GATE_REV) != D226_GATE_TREE
            or git.parents(D226_GATE_REV) != [D226_GATE_PARENT]
            or git.tree_entry(D226_GATE_REV, GATE_PATH) != ("100644", "blob", D226_GATE_BLOB)
            or digest_bytes(git.blob(D226_GATE_REV, GATE_PATH)) != D226_GATE_SHA256):
        deny("d226_gate_baseline_mismatch")
    d226_transition = git.raw_diff(D226_PLAN_REV, D226_GATE_REV)
    if (len(d226_transition) != 1
            or (d226_transition[0].path_bytes, d226_transition[0].status, d226_transition[0].old_mode,
                d226_transition[0].new_mode, d226_transition[0].old_oid, d226_transition[0].new_oid)
            != (GATE_PATH.encode("ascii"), "M", "100644", "100644", D225_GATE_BLOB, D226_GATE_BLOB)):
        deny("d226_gate_transition_mismatch")

    if (git.object_type(D226_STOP_INTERMEDIATE) != "commit"
            or git.tree(D226_STOP_INTERMEDIATE) != D226_STOP_INTERMEDIATE_TREE
            or git.parents(D226_STOP_INTERMEDIATE) != [D226_GATE_REV]
            or git.tree_entry(D226_STOP_INTERMEDIATE, GATE_PATH) != ("100644", "blob", D226_GATE_BLOB)
            or any(entry.path_bytes == GATE_PATH.encode("ascii") for entry in git.raw_diff(D226_GATE_REV, D226_STOP_INTERMEDIATE))):
        deny("d226_stop_intermediate_mismatch")
    if (git.object_type(D226_STOP_CANDIDATE) != "commit"
            or git.tree(D226_STOP_CANDIDATE) != D226_STOP_TREE
            or git.parents(D226_STOP_CANDIDATE) != [D226_STOP_PARENT]
            or git.tree_entry(D226_STOP_CANDIDATE, GATE_PATH) != ("100644", "blob", D226_GATE_BLOB)
            or any(entry.path_bytes == GATE_PATH.encode("ascii") for entry in git.raw_diff(D226_STOP_INTERMEDIATE, D226_STOP_CANDIDATE))):
        deny("d226_stop_candidate_mismatch")
    if (git.object_type(PLAN_REV) != "commit" or git.tree(PLAN_REV) != PLAN_TREE
            or git.parents(PLAN_REV) != [PLAN_PARENT] or PLAN_PARENT != D226_STOP_CANDIDATE
            or git.tree_entry(PLAN_PARENT, GATE_PATH) != ("100644", "blob", D226_GATE_BLOB)
            or git.tree_entry(PLAN_REV, GATE_PATH) != ("100644", "blob", D226_GATE_BLOB)):
        deny("plan_parent_mismatch")
    for before, after, reason in (
        (D226_STOP_CANDIDATE, PLAN_REV, "plan_changed_inherited_gate"),
    ):
        if any(entry.path_bytes == GATE_PATH.encode("ascii") for entry in git.raw_diff(before, after)):
            deny(reason)
    return {
        "rev": D226_GATE_REV,
        "tree": D226_GATE_TREE,
        "blob": D226_GATE_BLOB,
        "sha256": D226_GATE_SHA256,
        "mode": "100644",
    }


def _validate_gate_replacement_diff(entries: Sequence[DiffEntry]) -> str:
    if len(entries) != 1:
        deny("bootstrap_diff_not_one_file")
    entry = entries[0]
    if (entry.path_bytes, entry.status, entry.old_mode, entry.new_mode, entry.old_oid) != (
        GATE_PATH.encode("ascii"), "M", "100644", "100644", D226_GATE_BLOB,
    ):
        deny("bootstrap_diff_scope")
    return entry.new_oid


def _validate_plan_source_entries(git: Git, plan_rev: str) -> None:
    if git.object_type(SOURCE_PARENT) != "commit" or git.tree(SOURCE_PARENT) != SOURCE_TREE:
        deny("d226_source_parent_mismatch")
    for path in PLAN_SOURCE_PATHS:
        if path in CORRECTION_SOURCE_PINS:
            expected = CORRECTION_SOURCE_PINS[path]
            route_entry = D226_ROUTE_CORRECTION_PINS[path]
            if (git.tree_entry(SOURCE_PARENT, path) != expected
                    or git.tree_entry(D226_STOP_INTERMEDIATE, path) != route_entry
                    or git.tree_entry(D226_STOP_CANDIDATE, path) != route_entry
                    or git.tree_entry(plan_rev, path) != route_entry):
                deny("d226_correction_source_pin_mismatch", path)
            continue
        if git.tree_entry(plan_rev, path) != git.tree_entry(D221_SHA, path):
            deny("d221_source_drift", path)


def validate_plan_anchor(git: Git, *, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    current = os.environ if env is None else env
    rev = current.get("PHASE24_D222_PLAN_REV", "")
    digest = current.get("PHASE24_D222_PLAN_SHA256", "")
    if rev != PLAN_REV or digest != PLAN_SHA256:
        deny("missing_or_wrong_plan_handoff")
    if git.object_type(rev) != "commit" or git.tree(rev) != PLAN_TREE or git.parents(rev) != [PLAN_PARENT]:
        deny("wrong_plan_commit")
    raw = git.pinned_blob(rev, PLAN_TREE, PLAN_PATH_SHA256, PLAN_BLOB, PLAN_SHA256)
    if digest_bytes(raw) != digest:
        deny("wrong_plan_blob")
    source_scope, corrections = parse_plan_scopes(raw)
    _validate_plan_source_entries(git, rev)
    if git.tree(D221_SHA) != D221_TREE or git.object_type(D209_REV) != "commit":
        deny("historical_commit_drift")
    for path, expected_blob in HISTORICAL_PATHS.items():
        if git.text("rev-parse", f"{rev}:{path}") != expected_blob:
            deny("historical_data_drift", path)
    if git.text("rev-parse", f"{D209_REV}:.planning/milestones/v0.4-REQUIREMENTS.md") != REQUIREMENTS_BLOB:
        deny("d209_requirements_drift")
    if git.text("rev-parse", f"{D209_REV}:.planning/milestones/v0.4-ROADMAP.md") != ROADMAP_BLOB:
        deny("d209_roadmap_drift")
    hygiene = git.blob(rev, "tests/scripts/verify-planning-hygiene.py")
    if digest_bytes(hygiene) != PLANNING_HYGIENE_SHA256:
        deny("planning_hygiene_pin_drift")
    if not git.is_ancestor(D221_EXEC_REV, rev):
        deny("d221_boundary_not_ancestor")
    if (git.object_type(DISCUSSION_REV) != "commit" or git.tree(DISCUSSION_REV) != DISCUSSION_TREE
            or git.parents(DISCUSSION_REV) != [PLAN_PARENT]
            or digest_bytes(git.pinned_blob(DISCUSSION_REV, DISCUSSION_TREE, DISCUSSION_PATH_SHA256, DISCUSSION_BLOB, DISCUSSION_SHA256)) != DISCUSSION_SHA256):
        deny("discussion_boundary_drift")
    git.pinned_blob(CLOSEOUT_REV, CLOSEOUT_TREE, CLOSEOUT_PATH_SHA256, CLOSEOUT_BLOB, CLOSEOUT_SHA256)
    inherited_gate = _validate_inherited_gate_boundary(git)
    loader_sha256 = digest_bytes(extract_plan_loader(raw))
    return {
        "rev": rev,
        "parent": PLAN_PARENT,
        "tree": PLAN_TREE,
        "blob": PLAN_BLOB,
        "sha256": PLAN_SHA256,
        "source_allowlist": list(source_scope),
        "correction_allowlist": list(corrections),
        "discussion_rev": DISCUSSION_REV,
        "discussion_tree": DISCUSSION_TREE,
        "discussion_blob": DISCUSSION_BLOB,
        "discussion_sha256": DISCUSSION_SHA256,
        "closeout_rev": CLOSEOUT_REV,
        "closeout_tree": CLOSEOUT_TREE,
        "closeout_blob": CLOSEOUT_BLOB,
        "closeout_sha256": CLOSEOUT_SHA256,
        "inherited_gate": inherited_gate,
        "loader_sha256": loader_sha256,
    }


def _safe_receipt_path(root: Path, value: Any, *, max_bytes: int = MAX_JSON_BYTES) -> tuple[Path, bytes]:
    if type(value) is not str or not value or Path(value).is_absolute() or ".." in Path(value).parts:
        deny("unsafe_receipt_path")
    root_resolved = root.resolve(strict=True)
    path = root_resolved / value
    cursor = root_resolved
    try:
        for component in Path(value).parts:
            cursor = cursor / component
            info = cursor.lstat()
            if stat.S_ISLNK(info.st_mode):
                deny("receipt_symlink_component")
        resolved = path.resolve(strict=True)
        resolved.relative_to(root_resolved)
    except (OSError, ValueError):
        deny("receipt_missing_or_outside_root")
    if not stat.S_ISREG(info.st_mode) or info.st_size > max_bytes:
        deny("receipt_not_bounded_regular_file")
    try:
        data = path.read_bytes()
    except OSError:
        deny("receipt_unreadable")
    if len(data) > max_bytes:
        deny("receipt_too_large")
    return resolved, data


def _receipt_path_under_build(value: Any, label: str) -> str:
    if type(value) is not str or not value.startswith("build/phase24/") or Path(value).is_absolute() or ".." in Path(value).parts:
        deny("receipt_path_scope", f"{label} must be under ignored build/phase24")
    return value


def _check_ignored(git: Git, path: str) -> None:
    status = git.run_result("check-ignore", "--quiet", "--", path)
    if status.returncode != 0:
        deny("receipt_not_ignored", path)


def _require_schema_version(obj: Mapping[str, Any], label: str) -> None:
    if type(obj.get("schema_version")) is not int or obj["schema_version"] != 1:
        deny("schema_version", f"unsupported {label} schema")


def _load_receipt(root: Path, relative: Any, *, max_bytes: int = MAX_JSON_BYTES) -> tuple[Path, dict[str, Any], bytes]:
    path, raw = _safe_receipt_path(root, relative, max_bytes=max_bytes)
    value = strict_json_bytes(raw, max_bytes=max_bytes)
    if type(value) is not dict:
        deny("receipt_not_object", str(relative))
    return path, value, raw


def _verify_current_tree_clean(git: Git, expected_head: str) -> None:
    if git.text("rev-parse", "HEAD") != expected_head:
        deny("checkout_head_mismatch")
    raw = git.run("status", "--porcelain=v1", "-z", "--untracked-files=all")
    if raw and not raw.endswith(b"\x00"):
        deny("malformed_status")
    parts = raw.split(b"\x00")[:-1]
    index = 0
    while index < len(parts):
        entry = parts[index]
        if len(entry) < 4:
            deny("malformed_status")
        status = entry[:2].decode("ascii", errors="strict")
        try:
            path = entry[3:].decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            deny("malformed_status")
        if path == ALLOWED_ROOT_STATUS and status == " M":
            index += 1
            continue
        # Rename/copy records include a second NUL-delimited path and are not
        # allowed even if their first displayed path looks harmless.
        if status[0] in {"R", "C"} or status[1] in {"R", "C"}:
            deny("renamed_worktree_path")
        deny("dirty_source_checkout", path)
    if git.run_result("diff", "--cached", "--quiet").returncode != 0:
        deny("staged_changes_present")


def _verify_candidate_closeout_change(git: Git, candidate_sha: str, candidate_tree: str, change: DiffEntry) -> None:
    if digest_bytes(change.path_bytes) != CLOSEOUT_PATH_SHA256:
        deny("closeout_path_identity")
    if (change.status, change.old_mode, change.new_mode) != ("M", "100644", "100644"):
        deny("closeout_path_mutation")
    mode, object_type, oid = git.tree_entry_by_path_digest(candidate_sha, candidate_tree, CLOSEOUT_PATH_SHA256)
    if (mode, object_type, oid) != ("100644", "blob", change.new_oid):
        deny("closeout_tree_diff_mismatch")
    updated = git.run("cat-file", "blob", oid)
    original = git.pinned_blob(CLOSEOUT_REV, CLOSEOUT_TREE, CLOSEOUT_PATH_SHA256, CLOSEOUT_BLOB, CLOSEOUT_SHA256)
    if not updated.startswith(original):
        deny("closeout_not_additive")


def _verify_bootstrap_source(git: Git, receipt: Mapping[str, Any], *, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    current = os.environ if env is None else env
    plan = exact_keys(receipt.get("plan"), {"rev", "parent", "tree", "blob", "sha256", "path_sha256"}, "bootstrap.plan")
    discussion = exact_keys(receipt.get("discussion"), {"rev", "tree", "blob", "sha256", "path_sha256"}, "bootstrap.discussion")
    closeout = exact_keys(receipt.get("closeout"), {"rev", "tree", "blob", "sha256", "path_sha256"}, "bootstrap.closeout")
    loader = exact_keys(receipt.get("loader"), {"sha256"}, "bootstrap.loader")
    inherited_gate = exact_keys(receipt.get("inherited_gate"), {"rev", "tree", "blob", "sha256", "mode"}, "bootstrap.inherited_gate")
    gate = exact_keys(receipt.get("gate"), {"rev", "parent", "tree", "blob", "sha256", "old_blob", "old_mode"}, "bootstrap.gate")
    trusted = exact_keys(receipt.get("trusted_handoff"), {"authority", "plan_rev", "plan_sha256", "gate_rev", "gate_sha256"}, "bootstrap.trusted_handoff")
    root_receipt = exact_keys(receipt.get("repository"), {"root", "git_dir", "branch"}, "bootstrap.repository")
    for label, value in (("plan.rev", plan["rev"]), ("plan.parent", plan["parent"]), ("plan.tree", plan["tree"]), ("plan.blob", plan["blob"]), ("discussion.rev", discussion["rev"]), ("discussion.tree", discussion["tree"]), ("discussion.blob", discussion["blob"]), ("closeout.rev", closeout["rev"]), ("closeout.tree", closeout["tree"]), ("closeout.blob", closeout["blob"]), ("inherited_gate.rev", inherited_gate["rev"]), ("inherited_gate.tree", inherited_gate["tree"]), ("inherited_gate.blob", inherited_gate["blob"]), ("gate.rev", gate["rev"]), ("gate.parent", gate["parent"]), ("gate.tree", gate["tree"]), ("gate.blob", gate["blob"]), ("gate.old_blob", gate["old_blob"])):
        require_sha(value, label)
    for label, value in (("plan.sha256", plan["sha256"]), ("plan.path_sha256", plan["path_sha256"]), ("discussion.sha256", discussion["sha256"]), ("discussion.path_sha256", discussion["path_sha256"]), ("closeout.sha256", closeout["sha256"]), ("closeout.path_sha256", closeout["path_sha256"]), ("loader.sha256", loader["sha256"]), ("gate.sha256", gate["sha256"]), ("trusted.plan_sha256", trusted["plan_sha256"]), ("trusted.gate_sha256", trusted["gate_sha256"])):
        require_digest(value, label)
    if plan != {"rev": PLAN_REV, "parent": PLAN_PARENT, "tree": PLAN_TREE, "blob": PLAN_BLOB, "sha256": PLAN_SHA256, "path_sha256": PLAN_PATH_SHA256}:
        deny("bootstrap_plan_receipt_mismatch")
    if discussion != {"rev": DISCUSSION_REV, "tree": DISCUSSION_TREE, "blob": DISCUSSION_BLOB, "sha256": DISCUSSION_SHA256, "path_sha256": DISCUSSION_PATH_SHA256}:
        deny("bootstrap_discussion_receipt_mismatch")
    if closeout != {"rev": CLOSEOUT_REV, "tree": CLOSEOUT_TREE, "blob": CLOSEOUT_BLOB, "sha256": CLOSEOUT_SHA256, "path_sha256": CLOSEOUT_PATH_SHA256}:
        deny("bootstrap_closeout_receipt_mismatch")
    if inherited_gate != {"rev": D226_GATE_REV, "tree": D226_GATE_TREE, "blob": D226_GATE_BLOB, "sha256": D226_GATE_SHA256, "mode": "100644"}:
        deny("bootstrap_inherited_gate_mismatch")
    gate_rev = current.get("PHASE24_D222_GATE_REV", "")
    gate_digest = current.get("PHASE24_D222_GATE_SHA256", "")
    if not valid_sha(gate_rev) or not valid_sha256(gate_digest):
        deny("missing_trusted_gate_handoff")
    if gate["rev"] != gate_rev or gate["sha256"] != gate_digest or gate["parent"] != PLAN_REV:
        deny("bootstrap_gate_receipt_mismatch")
    if gate["old_blob"] != D226_GATE_BLOB or gate["old_mode"] != "100644":
        deny("bootstrap_old_gate_mismatch")
    if trusted != {
        "authority": "gsd-executor",
        "plan_rev": PLAN_REV,
        "plan_sha256": PLAN_SHA256,
        "gate_rev": gate_rev,
        "gate_sha256": gate_digest,
    }:
        deny("untrusted_bootstrap_handoff")
    validate_plan_anchor(git, env=current)
    plan_bytes = git.pinned_blob(PLAN_REV, PLAN_TREE, PLAN_PATH_SHA256, PLAN_BLOB, PLAN_SHA256)
    expected_loader_digest = digest_bytes(extract_plan_loader(plan_bytes))
    if loader["sha256"] != expected_loader_digest:
        deny("bootstrap_loader_digest_mismatch")
    if git.object_type(PLAN_REV) != "commit" or git.tree(PLAN_REV) != PLAN_TREE or git.parents(PLAN_REV) != [PLAN_PARENT]:
        deny("plan_object_mismatch")
    if digest_bytes(git.pinned_blob(PLAN_REV, PLAN_TREE, PLAN_PATH_SHA256, PLAN_BLOB, PLAN_SHA256)) != PLAN_SHA256:
        deny("plan_blob_mismatch")
    if digest_bytes(git.pinned_blob(DISCUSSION_REV, DISCUSSION_TREE, DISCUSSION_PATH_SHA256, DISCUSSION_BLOB, DISCUSSION_SHA256)) != DISCUSSION_SHA256:
        deny("discussion_blob_mismatch")
    if digest_bytes(git.pinned_blob(CLOSEOUT_REV, CLOSEOUT_TREE, CLOSEOUT_PATH_SHA256, CLOSEOUT_BLOB, CLOSEOUT_SHA256)) != CLOSEOUT_SHA256:
        deny("closeout_blob_mismatch")
    if git.object_type(gate_rev) != "commit" or git.tree(gate_rev) != gate["tree"] or git.parents(gate_rev) != [PLAN_REV]:
        deny("gate_object_mismatch")
    inherited = _validate_inherited_gate_boundary(git)
    if inherited != {key: inherited_gate[key] for key in ("rev", "tree", "blob", "sha256", "mode")}:
        deny("bootstrap_inherited_gate_drift")
    new_gate_blob = _validate_gate_replacement_diff(git.raw_diff(PLAN_REV, gate_rev))
    gate_bytes = git.blob(gate_rev, GATE_PATH)
    if git.text("rev-parse", f"{gate_rev}:{GATE_PATH}") != new_gate_blob or digest_bytes(gate_bytes) != gate_digest or new_gate_blob != gate["blob"]:
        deny("gate_blob_mismatch")
    _verify_executing_bytes(gate_bytes, executing_source_bytes())
    root, git_dir, branch = current_root(git)
    if root_receipt != {"root": root, "git_dir": git_dir, "branch": branch}:
        deny("bootstrap_repository_mismatch")
    if current.get("PHASE24_D222_PLAN_REV") != PLAN_REV or current.get("PHASE24_D222_PLAN_SHA256") != PLAN_SHA256:
        deny("plan_handoff_mismatch")
    scopes = exact_keys(receipt.get("scope"), {"source_allowlist", "correction_allowlist"}, "bootstrap.scope")
    source_scope, correction_scope = parse_plan_scopes(plan_bytes)
    if scopes != {"source_allowlist": list(source_scope), "correction_allowlist": list(correction_scope)}:
        deny("bootstrap_scope_mismatch")
    expected_history_pins = {
        "d209_rev": D209_REV,
        "d220_candidate": D220_SHA,
        "d221_candidate": D221_SHA,
        "d221_tree": D221_TREE,
        "d221_exec_rev": D221_EXEC_REV,
        "requirements_blob": REQUIREMENTS_BLOB,
        "roadmap_blob": ROADMAP_BLOB,
        "state_forks_blob": STATE_FORKS_BLOB,
        "planning_hygiene_sha256": PLANNING_HYGIENE_SHA256,
        **D226_HISTORY_PINS,
    }
    if receipt.get("history_pins") != expected_history_pins:
        deny("bootstrap_historical_pins_mismatch")
    return {"plan": dict(plan), "discussion": dict(discussion), "closeout": dict(closeout), "loader": dict(loader), "inherited_gate": dict(inherited_gate), "gate": dict(gate), "repository": dict(root_receipt), "scope": dict(scopes)}


def _verify_executing_bytes(original_bytes: bytes, executing_bytes: Any) -> None:
    if type(original_bytes) is not bytes or type(executing_bytes) is not bytes or not hmac.compare_digest(original_bytes, executing_bytes):
        deny("executing_gate_bytes_mismatch")


def _registered_module_bytes(module_name: str, namespace: Mapping[str, Any]) -> bytes:
    module = sys.modules.get(module_name)
    if module is None or module.__dict__ is not namespace:
        deny("executing_module_not_registered")
    source = namespace.get("__phase24_gate_bytes__")
    if type(source) is not bytes:
        deny("immutable_gate_bytes_missing")
    return source


def executing_source_bytes() -> bytes:
    module = sys.modules.get(__name__)
    if module is None or module.__dict__ is not globals():
        deny("executing_module_not_registered")
    if __name__ != "__main__":
        return _registered_module_bytes(__name__, globals())
    try:
        source = Path(__file__).read_bytes()
    except (OSError, TypeError, NameError):
        deny("direct_gate_source_unreadable")
    injected = globals().get("__phase24_gate_bytes__")
    if injected is not None:
        _verify_executing_bytes(source, injected)
    return source


def extract_plan_loader(plan_bytes: bytes) -> bytes:
    blocks = re.findall(rb"<trusted_invocation>\n(.*?)\n</trusted_invocation>", plan_bytes, re.S)
    if len(blocks) != 1:
        deny("plan_loader_block_ambiguous")
    sources = re.findall(rb"```python\n(.*?)\n```", blocks[0], re.S)
    if len(sources) != 1:
        deny("plan_loader_source_ambiguous")
    return sources[0]


def fresh_plan_wrapper_source() -> str:
    """Return the loader selected from the pinned immutable plan bytes."""
    plan_bytes = Git(Path.cwd()).pinned_blob(PLAN_REV, PLAN_TREE, PLAN_PATH_SHA256, PLAN_BLOB, PLAN_SHA256)
    return extract_plan_loader(plan_bytes).decode("utf-8", errors="strict")


def verify_bootstrap(root: Path, bootstrap_path: str) -> dict[str, Any]:
    reject_hostile_git_environment()
    git = Git(root)
    _check_ignored(git, bootstrap_path)
    _, receipt, _ = _load_receipt(root, bootstrap_path)
    exact_keys(receipt, {"schema_version", "kind", "plan", "discussion", "closeout", "loader", "inherited_gate", "gate", "repository", "scope", "history_pins", "trusted_handoff"}, "bootstrap")
    _require_schema_version(receipt, "bootstrap")
    if receipt.get("kind") != "phase24-d227-bootstrap":
        deny("bootstrap_kind")
    result = _verify_bootstrap_source(git, receipt)
    _verify_current_tree_clean(git, str(result["gate"]["rev"]))
    return {"decision": "ALLOW", "mode": "verify-bootstrap", "plan_rev": PLAN_REV, "plan_sha256": PLAN_SHA256, "loader_sha256": result["loader"]["sha256"], "discussion_sha256": result["discussion"]["sha256"], "gate_rev": result["gate"]["rev"], "gate_sha256": result["gate"]["sha256"]}


def _verify_candidate_scope(git: Git, bootstrap: Mapping[str, Any], candidate_sha: str, *, require_checkout: bool = True) -> dict[str, Any]:
    require_sha(candidate_sha, "candidate SHA")
    gate_rev = str(bootstrap["gate"]["rev"])
    plan_rev = str(bootstrap["plan"]["rev"])
    if git.object_type(candidate_sha) != "commit" or git.text("rev-parse", "--verify", candidate_sha) != candidate_sha:
        deny("candidate_not_original_commit")
    candidate_tree = git.tree(candidate_sha)
    if not valid_sha(candidate_tree) or not git.is_ancestor(gate_rev, candidate_sha):
        deny("candidate_not_descendant_of_bootstrap")
    if not git.is_ancestor(D221_EXEC_REV, candidate_sha):
        deny("candidate_not_descendant_of_execution_base")
    entries = git.raw_diff(gate_rev, candidate_sha)
    if not entries:
        deny("candidate_unchanged")
    paths = {entry.path for entry in entries}
    path_hashes = {digest_bytes(entry.path.encode("utf-8", errors="strict")) for entry in entries}
    if path_hashes - ALLOWED_CANDIDATE_PATH_HASHES:
        deny("candidate_scope_exceeded")
    if len(paths) != len(entries) or any(entry.status != "M" or entry.old_mode != "100644" or entry.new_mode != "100644" for entry in entries):
        deny("candidate_path_mutation")
    if not path_hashes.intersection(EXPECTED_CANDIDATE_CORRECTION_HASHES):
        deny("candidate_has_no_causal_source_change")
    for entry in entries:
        if digest_bytes(entry.path.encode("utf-8", errors="strict")) == CLOSEOUT_PATH_SHA256:
            _verify_candidate_closeout_change(git, candidate_sha, candidate_tree, entry)
    if git.text("rev-parse", f"{candidate_sha}:{GATE_PATH}") != bootstrap["gate"]["blob"]:
        deny("frozen_gate_blob_changed")
    for path in PLAN_SOURCE_PATHS:
        if path == GATE_PATH:
            continue
        expected = git.text("rev-parse", f"{plan_rev}:{path}")
        actual = git.text("rev-parse", f"{candidate_sha}:{path}")
        if path not in EXPECTED_CANDIDATE_CORRECTIONS and actual != expected:
            deny("inherited_source_blob_changed", path)
    for path, expected in HISTORICAL_PATHS.items():
        if git.text("rev-parse", f"{candidate_sha}:{path}") != expected:
            deny("candidate_historical_data_changed", path)
    if git.text("rev-parse", f"{D209_REV}:.planning/milestones/v0.4-REQUIREMENTS.md") != REQUIREMENTS_BLOB or git.text("rev-parse", f"{D209_REV}:.planning/milestones/v0.4-ROADMAP.md") != ROADMAP_BLOB:
        deny("candidate_d209_archive_drift")
    if digest_bytes(git.blob(candidate_sha, "tests/scripts/verify-planning-hygiene.py")) != PLANNING_HYGIENE_SHA256:
        deny("candidate_planning_hygiene_drift")
    cumulative = git.raw_diff(plan_rev, candidate_sha)
    if len(cumulative) != 1 + len(entries) or {item.path for item in cumulative} != {GATE_PATH} | paths:
        deny("cumulative_scope_mismatch")
    if require_checkout:
        _verify_current_tree_clean(git, candidate_sha)
    return {"sha": candidate_sha, "tree": candidate_tree, "paths": sorted(paths), "diff_sha256": digest_bytes(b"\x00".join((item.path.encode("utf-8") + b"\x00" + item.status.encode("ascii")) for item in entries))}


MANIFEST_KEYS = {
    "schema_version", "kind", "candidate_sha", "candidate_tree", "bootstrap_rev",
    "plan_rev", "plan_sha256", "gate_sha256", "receipts", "expected_remote",
    "causal_resolution",
}
MANIFEST_RECEIPT_KEYS = {"qualification", "code_review", "security_review", "provenance", "history"}
REMOTE_EXPECTATION_KEYS = {"repository", "pull_request", "head_branch", "prior_head_sha", "base_sha", "protection_sha256"}
REVIEW_RECEIPT_KEYS = {"schema_version", "kind", "candidate_sha", "candidate_tree", "role", "reviewer_agent", "verdict", "report_path", "report_sha256"}
PROVENANCE_KEYS = {"schema_version", "kind", "plan_rev", "gate_rev", "gate_sha256", "candidate_sha", "candidate_tree", "implementation_agent", "review_dispatches", "qualification_dispatch", "expected_tests"}
QUALIFICATION_KEYS = {"schema_version", "kind", "candidate_sha", "candidate_tree", "plan_rev", "gate_rev", "gate_sha256", "interpreter", "tests", "direct_controls", "inventory", "ctest_inventory", "fixture_effects", "source_pins"}
TEST_RESULT_KEYS = {"name", "command", "interpreter", "transcript_path", "transcript_sha256", "exit_code", "markers", "actual", "floor", "elapsed_seconds", "deadline_seconds", "processors"}

EXPECTED_TESTS = (
    "plan_cap",
    "phase22_evidence_controls",
    "phase22_evidence_contract",
    "no_phase_paths_controls",
    "no_phase_paths",
    "wait_exact_head_ci_controls",
    "workflow_policy_check",
    "workflow_policy_group_ci",
    "workflow_policy_coverage_controls",
    "planning_hygiene_controls",
)
TEST_DEADLINES = {
    "plan_cap": 30,
    "phase22_evidence_controls": 60,
    "phase22_evidence_contract": 60,
    "no_phase_paths_controls": 60,
    "no_phase_paths": 60,
    "wait_exact_head_ci_controls": 60,
    "workflow_policy_check": 60,
    "workflow_policy_group_ci": 180,
    "workflow_policy_coverage_controls": 30,
    "planning_hygiene_controls": 30,
}
TEST_PROCESSORS = {name: 4 if name == "workflow_policy_group_ci" else 1 for name in EXPECTED_TESTS}
TEST_PASS_PATTERNS = {
    "plan_cap": r"plan-cap pass phases=[0-9]+ plans=[0-9]+",
    "phase22_evidence_controls": r"diagnostic evidence controls pass positives=1 rejected_controls=passed boundary=immutable",
    "phase22_evidence_contract": r"diagnostic evidence pass source=[0-9a-f]+ assessment=blocked cases=513 unresolved_gates=7 admitted=0 executed=0 assessment_checker_sha256=[0-9a-f]+",
    "no_phase_paths_controls": r"no-phase-paths self-test pass controls=[0-9]+",
    "no_phase_paths": r"no-phase-paths pass files=[0-9]+ allowlisted=[0-9]+",
    "wait_exact_head_ci_controls": r"exact-head gate self-test [^c]+cases[^c]+controls=[0-9]+",
    "workflow_policy_check": r"PASS: workflow privilege and trust wiring residual_write_jobs=[0-9]+",
    "workflow_policy_group_ci": r"PASS: workflow policy group ci controls=[0-9]+ ids_sha256=[0-9a-f]+",
    "workflow_policy_coverage_controls": r"PASS: workflow policy coverage self-test controls=[0-9]+",
    "planning_hygiene_controls": r"planning-hygiene self-test pass controls=[0-9]+",
}
TEST_LABELS: dict[str, tuple[str, ...] | None] = {
    "plan_cap": ("planning",),
    "phase22_evidence_controls": ("planning",),
    "phase22_evidence_contract": ("ctest-inventory-only", "planning"),
    "no_phase_paths_controls": ("planning",),
    "no_phase_paths": ("planning",),
    "wait_exact_head_ci_controls": ("planning",),
    "workflow_policy_check": None,
    "workflow_policy_group_ci": None,
    "workflow_policy_coverage_controls": None,
    "planning_hygiene_controls": ("planning",),
}
TEST_FLOORS = {
    "plan_cap": 4,
    "phase22_evidence_controls": 0,
    "phase22_evidence_contract": 0,
    "no_phase_paths_controls": 16,
    "no_phase_paths": 380,
    "wait_exact_head_ci_controls": 40,
    "workflow_policy_check": 0,
    "workflow_policy_group_ci": 0,
    "workflow_policy_coverage_controls": 0,
    "planning_hygiene_controls": 125,
}
INVENTORY_KEYS = {"transcript_path", "transcript_sha256", "exit_code", "cases", "runner_cases", "build_cases", "configure_cases"}
CTEST_INVENTORY_KEYS = {"command", "transcript_path", "transcript_sha256", "exit_code", "test_count", "runner_cases", "build_cases", "configure_cases"}
DIRECT_CONTROL_KEYS = {"name", "command", "transcript_path", "transcript_sha256", "exit_code", "markers"}
DIRECT_CONTROL_NAMES = ("pinned_gate_self_test", "wait_exact_head_ci_self_test", "promotion_coverage_controls", "dense_input_git_context", "state_fork_inventory_controls")
DIRECT_CONTROL_MARKERS = {
    "pinned_gate_self_test": r"PHASE24_D227_SELF_TESTS=PASS tests=[1-9][0-9]*",
    "wait_exact_head_ci_self_test": TEST_PASS_PATTERNS["wait_exact_head_ci_controls"],
    "promotion_coverage_controls": r"^PASS: phase24-promotion-controls gate=(?P<gate_sha256>[0-9a-f]{64}) controls=[0-9]+$",
    "dense_input_git_context": r"dense-input git-context=pass rev=[0-9a-f]{40} controls=[0-9]+ configure=0 build=0 runner=0",
    "state_fork_inventory_controls": r"state-fork inventory-controls pass rev=[0-9a-f]{40} cases=153 controls=[0-9]+ runner=0 build=0 configure=0",
}
_SELF_TEST_ACTIVE = False


def _text(value: Any, label: str, *, max_chars: int = 1000) -> str:
    if type(value) is not str or not value or len(value) > max_chars or "\x00" in value:
        deny("schema_text", f"{label} is invalid")
    return value


def _sha256_value(value: Any, label: str) -> str:
    require_digest(value, label)
    return value


def _read_transcript(root: Path, path_value: Any, sha_value: Any, label: str) -> tuple[str, bytes]:
    relative = _receipt_path_under_build(path_value, label)
    path, data = _safe_receipt_path(root, relative, max_bytes=MAX_REPORT_BYTES)
    expected = _sha256_value(sha_value, f"{label}.sha256")
    if digest_bytes(data) != expected:
        deny("transcript_digest_mismatch", label)
    return relative, data


def _check_report_identity(body: bytes, *, role: str, agent: str, candidate_sha: str, candidate_tree: str, verdict: str) -> None:
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        deny("review_report_encoding")
    # Reviewers are asked to include this explicit metadata block so a clean
    # result cannot be inferred from a missing findings section or exit code.
    required = {
        "Review role": role,
        "Reviewer agent": agent,
        "Reviewed commit": candidate_sha,
        "Reviewed tree": candidate_tree,
        "Verdict": verdict,
    }
    for label, expected in required.items():
        matches = re.findall(rf"(?mi)^{re.escape(label)}\s*:\s*([^\r\n]+)\s*$", text)
        if matches != [expected]:
            deny("review_report_identity_or_verdict", label)
    findings = re.findall(r"(?mi)^(?:Open findings|Unresolved findings|Findings)\s*:\s*([^\r\n]+)\s*$", text)
    if not findings or any(value.strip().casefold() not in {"none", "0", "no open findings"} for value in findings):
        deny("review_report_has_findings")
    if re.search(r"(?mi)^\s*(?:#{1,6}\s+[^\r\n]*\b(?:unresolved\s+)?warnings?\b[^\r\n]*|(?:unresolved\s+)?warnings?\s*:\s*[^\r\n]+)\s*$", text):
        deny("review_report_has_warning_heading")
    if re.search(r"(?i)\b(NO-GO|BLOCKER|CRITICAL|HIGH severity|unresolved warning)\b", text):
        deny("review_report_not_clean")


def _manifest_receipt(root: Path, manifest: Mapping[str, Any], key: str) -> tuple[Path, dict[str, Any], bytes]:
    raw_by_key = manifest.get("_receipt_raw")
    paths = manifest.get("receipts")
    if type(raw_by_key) is not dict or key not in raw_by_key or type(paths) is not dict or type(paths.get(key)) is not str:
        deny("manifest_receipt_not_preverified", key)
    raw = raw_by_key[key]
    value = strict_json_bytes(raw, max_bytes=MAX_JSON_BYTES)
    if type(value) is not dict:
        deny("receipt_not_object", key)
    return _safe_receipt_path(root, paths[key], max_bytes=MAX_JSON_BYTES)[0], value, raw


def _require_manifest_digest(raw: bytes, trusted_digest: Any) -> None:
    if not valid_sha256(trusted_digest) or digest_bytes(raw) != trusted_digest:
        deny("evidence_manifest_digest_mismatch")


def _bind_receipt_refs(receipt_refs: Any, read_bytes: Callable[[str], bytes]) -> tuple[dict[str, str], dict[str, bytes]]:
    refs = exact_keys(receipt_refs, MANIFEST_RECEIPT_KEYS, "manifest.receipts")
    paths: dict[str, str] = {}
    bodies: dict[str, bytes] = {}
    seen: set[str] = set()
    for label in sorted(MANIFEST_RECEIPT_KEYS):
        ref = exact_keys(refs[label], {"path", "sha256"}, f"manifest.receipts.{label}")
        path = _receipt_path_under_build(ref["path"], label)
        digest = require_digest(ref["sha256"], f"manifest.receipts.{label}.sha256")
        if path in seen:
            deny("manifest_receipt_path_reused", label)
        seen.add(path)
        body = read_bytes(path)
        if type(body) is not bytes or not hmac.compare_digest(digest_bytes(body), digest):
            deny("manifest_receipt_digest_mismatch", label)
        paths[label] = path
        bodies[label] = body
    return paths, bodies


def _validate_review(root: Path, manifest: Mapping[str, Any], provenance: Mapping[str, Any], role: str, verdict: str) -> dict[str, Any]:
    key = "code_review" if role == "gsd-code-reviewer" else "security_review"
    _, receipt, raw = _manifest_receipt(root, manifest, key)
    exact_keys(receipt, REVIEW_RECEIPT_KEYS, key)
    _require_schema_version(receipt, key)
    if receipt["kind"] != "phase24-d222-review" or receipt["candidate_sha"] != manifest["candidate_sha"] or receipt["candidate_tree"] != manifest["candidate_tree"]:
        deny("review_candidate_mismatch", key)
    agent = _text(receipt["reviewer_agent"], f"{key}.reviewer_agent", max_chars=120)
    if receipt["role"] != role or receipt["verdict"] != verdict:
        deny("review_role_or_verdict", key)
    report_path, report = _safe_receipt_path(root, _receipt_path_under_build(receipt["report_path"], f"{key}.report_path"), max_bytes=MAX_REPORT_BYTES)
    report_digest = _sha256_value(receipt["report_sha256"], f"{key}.report_sha256")
    if digest_bytes(report) != report_digest:
        deny("review_report_digest_mismatch", key)
    dispatches = provenance["review_dispatches"]
    if type(dispatches) is not list or len(dispatches) != 2:
        deny("review_provenance_shape")
    matches = [item for item in dispatches if type(item) is dict and item.get("role") == role]
    if len(matches) != 1:
        deny("review_dispatch_ambiguous", key)
    dispatch = exact_keys(matches[0], {"role", "reviewer_agent", "candidate_sha", "candidate_tree", "report_path", "report_sha256", "result"}, f"provenance.{key}")
    if dispatch != {
        "role": role,
        "reviewer_agent": agent,
        "candidate_sha": manifest["candidate_sha"],
        "candidate_tree": manifest["candidate_tree"],
        "report_path": receipt["report_path"],
        "report_sha256": report_digest,
        "result": verdict,
    }:
        deny("review_dispatch_mismatch", key)
    if agent == provenance["implementation_agent"]:
        deny("reviewer_not_independent", key)
    _check_report_identity(report, role=role, agent=agent, candidate_sha=manifest["candidate_sha"], candidate_tree=manifest["candidate_tree"], verdict=verdict)
    return {"agent": agent, "role": role, "report_path": str(report_path), "report_sha256": report_digest, "report_bytes": report}


def _server_side_enforcement_required(text: str) -> bool:
    pattern = r"(?:server[- ]side enforcement.{0,80}(?:required|necessary|must)|(?:requires?|needs?|must|necessary).{0,80}server[- ]side enforcement)"
    return re.search(pattern, text, re.IGNORECASE | re.DOTALL) is not None


def _expected_ctest_argv(name: str) -> list[str]:
    if name not in EXPECTED_TESTS:
        deny("qualification_test_unknown", name)
    return ["ctest", "--preset", "phase1", "--output-on-failure", "--no-tests=error", "-j", "1", "-R", f"^{name}$"]


def _expected_inventory_command() -> list[str]:
    selection = "^(" + "|".join(EXPECTED_TESTS) + ")$"
    return ["ctest", "--preset", "phase1", "--show-only=json-v1", "-R", selection]


def _expected_direct_control_command(name: str, candidate_sha: str, gate_rev: str, gate_sha256: str, interpreter: str) -> list[str]:
    if name == "pinned_gate_self_test":
        return [interpreter, "-I", "-c", fresh_plan_wrapper_source(), "--self-test"]
    if name == "wait_exact_head_ci_self_test":
        return [interpreter, "-I", ".github/scripts/wait-exact-head-ci.py", "--self-test"]
    if name == "promotion_coverage_controls":
        return [interpreter, "-I", "tests/scripts/verify-workflow-policy-coverage.py", "--phase24-promotion-controls", "--root", ".", "--gate-rev", gate_rev, "--gate-sha256", gate_sha256]
    if name == "dense_input_git_context":
        return [interpreter, "-I", "tests/scripts/verify-dense-input.py", "--check-git-context", "--source-revision", candidate_sha]
    if name == "state_fork_inventory_controls":
        return [interpreter, "-I", "tests/scripts/verify-state-forks.py", "--inventory-controls", "--rev", candidate_sha, "--repo", "."]
    deny("qualification_direct_control_name", str(name))


def _validate_direct_control(root: Path, raw_control: Any, name: str, candidate_sha: str, gate_rev: str, gate_sha256: str, interpreter: str) -> str:
    control = exact_keys(raw_control, DIRECT_CONTROL_KEYS, f"direct_controls.{name}")
    if control["name"] != name or control["command"] != _expected_direct_control_command(name, candidate_sha, gate_rev, gate_sha256, interpreter):
        deny("qualification_direct_control_command", name)
    if type(control["exit_code"]) is not int or control["exit_code"] != 0 or control["markers"] != [DIRECT_CONTROL_MARKERS[name]]:
        deny("qualification_direct_control_result", name)
    direct_path, direct_body = _read_transcript(root, control["transcript_path"], control["transcript_sha256"], name)
    try:
        direct_text = direct_body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        deny("qualification_direct_control_encoding", name)
    matches = list(re.finditer(DIRECT_CONTROL_MARKERS[name], direct_text, re.MULTILINE))
    if name == "promotion_coverage_controls":
        marker_lines = re.findall(r"(?m)^(?:PASS: )?phase24-promotion-controls\b[^\r\n]*$", direct_text)
        if len(matches) != 1 or len(marker_lines) != 1:
            deny("qualification_direct_marker_missing", name)
        if not hmac.compare_digest(matches[0].group("gate_sha256"), gate_sha256):
            deny("qualification_direct_marker_gate_mismatch", name)
    elif not matches:
        deny("qualification_direct_marker_missing", name)
    return direct_path


DIRECT_CONTROL_SAMPLE_OUTPUT = {
    "pinned_gate_self_test": "PHASE24_D227_SELF_TESTS=PASS tests=19",
    "wait_exact_head_ci_self_test": "exact-head gate self-test passed cases=3 controls=40",
    "promotion_coverage_controls": "PASS: phase24-promotion-controls gate={gate_sha256} controls=12",
    "dense_input_git_context": "dense-input git-context=pass rev=" + "b" * 40 + " controls=8 configure=0 build=0 runner=0",
    "state_fork_inventory_controls": "state-fork inventory-controls pass rev=" + "c" * 40 + " cases=153 controls=10 runner=0 build=0 configure=0",
}
TEST_PASS_SAMPLE_OUTPUT = {
    "plan_cap": "plan-cap pass phases=4 plans=38",
    "phase22_evidence_controls": "diagnostic evidence controls pass positives=1 rejected_controls=passed boundary=immutable",
    "phase22_evidence_contract": "diagnostic evidence pass source=" + "a" * 40 + " assessment=blocked cases=513 unresolved_gates=7 admitted=0 executed=0 assessment_checker_sha256=" + "b" * 64,
    "no_phase_paths_controls": "no-phase-paths self-test pass controls=16",
    "no_phase_paths": "no-phase-paths pass files=380 allowlisted=10",
    "wait_exact_head_ci_controls": DIRECT_CONTROL_SAMPLE_OUTPUT["wait_exact_head_ci_self_test"],
    "workflow_policy_check": "PASS: workflow privilege and trust wiring residual_write_jobs=0",
    "workflow_policy_group_ci": "PASS: workflow policy group ci controls=10 ids_sha256=" + "d" * 64,
    "workflow_policy_coverage_controls": "PASS: workflow policy coverage self-test controls=12",
    "planning_hygiene_controls": "planning-hygiene self-test pass controls=125",
}


def _expected_ctest_command(name: str, root: Path, python: str, cmake: str, candidate_sha: str) -> list[str]:
    base = str(root)
    build = str(root / "build")
    checker_hygiene = f"{base}/tests/scripts/verify-planning-hygiene.py"
    checker_phase22 = f"{base}/tests/scripts/verify-diagnostic-evidence.py"
    checker_paths = f"{base}/tests/scripts/verify-no-phase-paths.py"
    checker_wait = f"{base}/.github/scripts/wait-exact-head-ci.py"
    checker_policy = f"{base}/.github/scripts/verify-workflow-policy.py"
    checker_coverage = f"{base}/tests/scripts/verify-workflow-policy-coverage.py"
    expect = f"{base}/tests/expect_exit.cmake"
    cmd: list[str]
    if name == "phase22_evidence_controls":
        cmd = [python, "-I", checker_phase22, "--self-test-controls", "--repo-root", base, "--source-revision", candidate_sha]
    elif name == "phase22_evidence_contract":
        cmd = [python, "-I", checker_phase22, "--check", "--repo-root", base, "--source-revision", candidate_sha, "--build-dir", build]
    else:
        sub: list[str]
        expected_code = "0"
        regex = ""
        floor_key: str | None = None
        floor_value: str | None = None
        workdir = False
        fresh = False
        if name == "plan_cap":
            sub = [python, "-I", checker_hygiene, "--check", "plan-cap", "--rev", candidate_sha, "--repo", base]
            regex = TEST_PASS_PATTERNS[name]
            floor_key, floor_value, workdir = "phases", "4", True
        elif name == "no_phase_paths_controls":
            sub = [python, "-I", checker_paths, "--self-test"]
            regex, floor_key, floor_value = TEST_PASS_PATTERNS[name], "controls", "16"
        elif name == "no_phase_paths":
            sub = [python, "-I", checker_paths, "--check"]
            regex, floor_key, floor_value = TEST_PASS_PATTERNS[name], "files", "380"
        elif name == "wait_exact_head_ci_controls":
            sub = [python, "-I", checker_wait, "--self-test"]
            regex, floor_key, floor_value = TEST_PASS_PATTERNS[name], "controls", "40"
        elif name == "workflow_policy_check":
            sub = [python, "-I", checker_policy, "--check", "--root", base]
            regex = TEST_PASS_PATTERNS[name]
        elif name == "workflow_policy_group_ci":
            completion = f"{build}/workflow-policy-ci.json"
            sub = [python, "-I", checker_policy, "--self-test", "--group", "ci", "--root", base, "--completed-file", completion]
            regex, fresh = TEST_PASS_PATTERNS[name], True
        elif name == "workflow_policy_coverage_controls":
            sub = [python, "-I", checker_coverage, "--self-test", "--root", base, "--rev", candidate_sha]
            regex = TEST_PASS_PATTERNS[name]
        elif name == "planning_hygiene_controls":
            sub = [python, "-I", checker_hygiene, "--self-test", "--rev", candidate_sha, "--repo", base]
            regex, floor_key, floor_value, workdir = TEST_PASS_PATTERNS[name], "controls", "125", True
        else:
            deny("qualification_test_unknown", name)
        encoded_sub = ";".join(sub)
        cmd = [cmake, f"-DGBB_CMD={encoded_sub}", "-DGBB_EXPECT_CODE=" + expected_code, "-DGBB_EXPECT_REGEX=" + regex]
        if workdir:
            cmd.append(f"-DGBB_WORKDIR={base}")
        if floor_key is not None:
            cmd.extend([f"-DGBB_EXPECT_MIN_KEY={floor_key}", f"-DGBB_EXPECT_MIN_VALUE={floor_value}"])
        if fresh:
            cmd.extend([f"-DGBB_EXPECT_FILE={build}/workflow-policy-ci.json", "-DGBB_EXPECT_FILE_FRESH=TRUE"])
        cmd.extend(["-P", expect])
    return cmd


def _validate_ctest_inventory(root: Path, python: str, candidate_sha: str, inventory: Any) -> None:
    if (type(inventory) is not dict or inventory.get("kind") != "ctestInfo"
            or type(inventory.get("version")) is not dict or type(inventory.get("tests")) is not list):
        deny("qualification_inventory_shape")
    version = inventory["version"]
    if any(type(version.get(field)) is not int or version[field] < 0 for field in ("major", "minor", "patch")):
        deny("qualification_inventory_version")
    if type(inventory.get("backtraceGraph")) is not dict:
        deny("qualification_inventory_backtrace")
    rows = inventory["tests"]
    by_name: dict[str, dict[str, Any]] = {}
    for row in rows:
        if type(row) is not dict or type(row.get("name")) is not str or row["name"] in by_name:
            deny("qualification_inventory_names")
        by_name[row["name"]] = row
    if len(rows) != len(EXPECTED_TESTS) or set(by_name) != set(EXPECTED_TESTS):
        deny("qualification_inventory_names")
    cmake = shutil.which("cmake")
    if type(cmake) is not str or not Path(cmake).is_absolute():
        deny("qualification_cmake_unavailable")
    for name in EXPECTED_TESTS:
        row = by_name[name]
        if row.get("command") != _expected_ctest_command(name, root, python, cmake, candidate_sha):
            deny("qualification_inventory_command", name)
        props = row.get("properties")
        if type(props) is not list:
            deny("qualification_inventory_properties", name)
        values: dict[str, Any] = {}
        for prop in props:
            if type(prop) is not dict or type(prop.get("name")) is not str or prop["name"] in values:
                deny("qualification_inventory_property_shape", name)
            values[prop["name"]] = prop.get("value")
        if values.get("TIMEOUT") != TEST_DEADLINES[name] or values.get("PROCESSORS", 1) != TEST_PROCESSORS[name]:
            deny("qualification_inventory_deadline_or_processors", name)
        expected_labels = TEST_LABELS[name]
        if expected_labels is None:
            if "LABELS" in values:
                deny("qualification_inventory_unexpected_labels", name)
        else:
            labels = values.get("LABELS")
            if type(labels) is not list or any(type(label) is not str for label in labels) or tuple(sorted(labels)) != tuple(sorted(expected_labels)):
                deny("qualification_inventory_labels", name)
        if values.get("FIXTURES_REQUIRED") or values.get("FIXTURES_SETUP"):
            deny("qualification_inventory_fixture_dependency", name)


def _validate_test_result(root: Path, item: Any, interpreter_path: str, candidate_sha: str) -> dict[str, Any]:
    test = exact_keys(item, TEST_RESULT_KEYS, "qualification.test")
    name = _text(test["name"], "test.name", max_chars=200)
    command = test["command"]
    if type(command) is not list or command != _expected_ctest_argv(name):
        deny("qualification_command")
    if test["interpreter"] != interpreter_path:
        deny("qualification_test_interpreter", name)
    transcript_path, transcript = _read_transcript(root, test["transcript_path"], test["transcript_sha256"], name)
    if type(test["exit_code"]) is not int or test["exit_code"] != 0:
        deny("qualification_nonzero", name)
    markers = test["markers"]
    if markers != [TEST_PASS_PATTERNS[name]]:
        deny("qualification_markers", name)
    text = transcript.decode("utf-8", errors="strict")
    if re.search(TEST_PASS_PATTERNS[name], text, re.MULTILINE) is None:
        deny("qualification_marker_missing", name)
    for field in ("actual", "floor", "elapsed_seconds", "deadline_seconds", "processors"):
        if type(test[field]) not in (int, float) or type(test[field]) is bool or test[field] < 0:
            deny("qualification_numeric_type", f"{name}.{field}")
    if type(test["actual"]) is not int:
        deny("qualification_integer_type", f"{name}.actual")
    if test["deadline_seconds"] != TEST_DEADLINES[name] or test["processors"] != TEST_PROCESSORS[name] or test["floor"] != TEST_FLOORS[name]:
        deny("qualification_test_contract", name)
    if test["actual"] < TEST_FLOORS[name] or test["elapsed_seconds"] > TEST_DEADLINES[name]:
        deny("qualification_floor_or_deadline", name)
    if type(test["deadline_seconds"]) is not int or type(test["floor"]) is not int or type(test["processors"]) is not int:
        deny("qualification_integer_type", name)
    return {"name": name, "command": command, "interpreter": test["interpreter"], "transcript_path": transcript_path, "transcript_sha256": test["transcript_sha256"], "exit_code": 0}


def _validate_qualification(root: Path, manifest: Mapping[str, Any], provenance: Mapping[str, Any], bootstrap: Mapping[str, Any]) -> dict[str, Any]:
    _, qualification, qualification_raw = _manifest_receipt(root, manifest, "qualification")
    exact_keys(qualification, QUALIFICATION_KEYS, "qualification")
    _require_schema_version(qualification, "qualification")
    expected = {
        "kind": "phase24-d227-qualification",
        "candidate_sha": manifest["candidate_sha"],
        "candidate_tree": manifest["candidate_tree"],
        "plan_rev": PLAN_REV,
        "gate_rev": manifest["bootstrap_rev"],
        "gate_sha256": manifest["gate_sha256"],
    }
    if any(qualification.get(key) != value for key, value in expected.items()):
        deny("qualification_identity_mismatch")
    interpreter = exact_keys(qualification["interpreter"], {"path", "version", "configured_path"}, "qualification.interpreter")
    for field in interpreter:
        _text(interpreter[field], f"interpreter.{field}", max_chars=500)
    configured = _configured_python(root)
    if (not Path(configured).is_absolute() or sys.executable != configured
            or interpreter != {"path": configured, "version": sys.version.split()[0], "configured_path": configured}):
        deny("qualification_interpreter_identity")
    tests = qualification["tests"]
    expected_tests = provenance["expected_tests"]
    if type(tests) is not list or type(expected_tests) is not list or len(tests) != len(EXPECTED_TESTS) or tuple(expected_tests) != EXPECTED_TESTS:
        deny("qualification_test_count")
    parsed = [_validate_test_result(root, item, configured, candidate_sha=manifest["candidate_sha"]) for item in tests]
    if [item["name"] for item in parsed] != list(EXPECTED_TESTS):
        deny("qualification_test_inventory_mismatch")
    direct = qualification["direct_controls"]
    if type(direct) is not list or len(direct) != len(DIRECT_CONTROL_NAMES):
        deny("qualification_direct_controls")
    direct_paths: list[str] = []
    for expected_name, raw_control in zip(DIRECT_CONTROL_NAMES, direct):
        direct_paths.append(_validate_direct_control(root, raw_control, expected_name, manifest["candidate_sha"], manifest["bootstrap_rev"], manifest["gate_sha256"], configured))
    inventory = exact_keys(qualification["inventory"], INVENTORY_KEYS, "qualification.inventory")
    if type(inventory["exit_code"]) is not int or inventory["exit_code"] != 0 or type(inventory["cases"]) is not int or inventory["cases"] != 153 or any(type(inventory[field]) is not int or inventory[field] != 0 for field in ("runner_cases", "build_cases", "configure_cases")):
        deny("qualification_inventory_counts")
    inventory_path, inventory_body = _read_transcript(root, inventory["transcript_path"], inventory["transcript_sha256"], "inventory")
    if b'"cases":153' not in inventory_body.replace(b" ", b"") or b'"runner_cases":0' not in inventory_body.replace(b" ", b""):
        deny("qualification_inventory_transcript_mismatch")
    ctest_inventory = exact_keys(qualification["ctest_inventory"], CTEST_INVENTORY_KEYS, "qualification.ctest_inventory")
    if ctest_inventory["command"] != _expected_inventory_command():
        deny("qualification_ctest_inventory_command_vector")
    if (type(ctest_inventory["exit_code"]) is not int or ctest_inventory["exit_code"] != 0
            or type(ctest_inventory["test_count"]) is not int or ctest_inventory["test_count"] != len(EXPECTED_TESTS)
            or any(type(ctest_inventory[field]) is not int or ctest_inventory[field] != 0 for field in ("runner_cases", "build_cases", "configure_cases"))):
        deny("qualification_ctest_inventory_counts")
    ctest_path, ctest_body = _read_transcript(root, ctest_inventory["transcript_path"], ctest_inventory["transcript_sha256"], "CTest inventory")
    try:
        ctest_json = strict_json_bytes(ctest_body, max_bytes=MAX_REPORT_BYTES)
    except GateError:
        deny("qualification_ctest_inventory_json")
    _validate_ctest_inventory(root, configured, manifest["candidate_sha"], ctest_json)
    effects = qualification["fixture_effects"]
    if type(effects) is not list or effects:
        deny("qualification_fixture_effect")
    pins = exact_keys(qualification["source_pins"], {"plan_rev", "plan_sha256", "plan_path_sha256", "discussion_rev", "discussion_tree", "discussion_blob", "discussion_sha256", "discussion_path_sha256", "closeout_rev", "closeout_tree", "closeout_blob", "closeout_sha256", "closeout_path_sha256", "loader_sha256", "d226_gate_rev", "d226_gate_tree", "d226_gate_blob", "d226_gate_sha256", "d226_gate_mode", "d221_exec_rev", "d209_rev", "requirements_blob", "roadmap_blob", "state_forks_blob", "planning_hygiene_sha256", "gate_rev", "gate_sha256"}, "qualification.source_pins")
    if pins != {
        "plan_rev": PLAN_REV,
        "plan_sha256": PLAN_SHA256,
        "plan_path_sha256": PLAN_PATH_SHA256,
        "discussion_rev": DISCUSSION_REV,
        "discussion_tree": DISCUSSION_TREE,
        "discussion_blob": DISCUSSION_BLOB,
        "discussion_sha256": DISCUSSION_SHA256,
        "discussion_path_sha256": DISCUSSION_PATH_SHA256,
        "closeout_rev": CLOSEOUT_REV,
        "closeout_tree": CLOSEOUT_TREE,
        "closeout_blob": CLOSEOUT_BLOB,
        "closeout_sha256": CLOSEOUT_SHA256,
        "closeout_path_sha256": CLOSEOUT_PATH_SHA256,
        "loader_sha256": bootstrap["loader"]["sha256"],
        "d226_gate_rev": D226_GATE_REV,
        "d226_gate_tree": D226_GATE_TREE,
        "d226_gate_blob": D226_GATE_BLOB,
        "d226_gate_sha256": D226_GATE_SHA256,
        "d226_gate_mode": "100644",
        "d221_exec_rev": D221_EXEC_REV,
        "d209_rev": D209_REV,
        "requirements_blob": REQUIREMENTS_BLOB,
        "roadmap_blob": ROADMAP_BLOB,
        "state_forks_blob": STATE_FORKS_BLOB,
        "planning_hygiene_sha256": PLANNING_HYGIENE_SHA256,
        "gate_rev": manifest["bootstrap_rev"],
        "gate_sha256": manifest["gate_sha256"],
    }:
        deny("qualification_source_pin_mismatch")
    if provenance.get("qualification_dispatch") != {
        "candidate_sha": manifest["candidate_sha"],
        "candidate_tree": manifest["candidate_tree"],
        "receipt_path": manifest["receipts"]["qualification"],
        "receipt_sha256": digest_bytes(qualification_raw),
        "result": "PASS",
        "test_names": expected_tests,
    }:
        # The dispatch binds the exact parsed receipt independently of the
        # manifest path; it deliberately cannot be satisfied by a pass label.
        deny("qualification_dispatch_mismatch")
    return {"tests": parsed, "direct_controls": direct_paths, "inventory": inventory_path, "ctest_inventory": ctest_path}


def _validate_provenance(root: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    _, provenance, _ = _manifest_receipt(root, manifest, "provenance")
    exact_keys(provenance, PROVENANCE_KEYS, "provenance")
    _require_schema_version(provenance, "provenance")
    if provenance["kind"] != "phase24-d222-trusted-handoff" or provenance["plan_rev"] != PLAN_REV or provenance["gate_rev"] != manifest["bootstrap_rev"] or provenance["gate_sha256"] != manifest["gate_sha256"] or provenance["candidate_sha"] != manifest["candidate_sha"] or provenance["candidate_tree"] != manifest["candidate_tree"]:
        deny("trusted_handoff_mismatch")
    _text(provenance["implementation_agent"], "provenance.implementation_agent", max_chars=120)
    expected_tests = provenance["expected_tests"]
    if type(expected_tests) is not list or tuple(expected_tests) != EXPECTED_TESTS:
        deny("trusted_test_inventory")
    return dict(provenance)


def _load_manifest(root: Path, git: Git, bootstrap: Mapping[str, Any], candidate_arg: Any, evidence_arg: Any, env: Mapping[str, str] | None = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    current = os.environ if env is None else env
    evidence_path = evidence_arg or current.get("PHASE24_D222_EVIDENCE", "")
    if not evidence_path or evidence_path != current.get("PHASE24_D222_EVIDENCE", evidence_path):
        deny("missing_trusted_evidence_path")
    evidence_path = _receipt_path_under_build(evidence_path, "evidence manifest")
    _check_ignored(git, evidence_path)
    manifest_file, manifest_raw = _safe_receipt_path(root, evidence_path, max_bytes=MAX_JSON_BYTES)
    trusted_manifest_digest = current.get("PHASE24_D222_EVIDENCE_SHA256", "")
    _require_manifest_digest(manifest_raw, trusted_manifest_digest)
    manifest = strict_json_bytes(manifest_raw, max_bytes=MAX_JSON_BYTES)
    if type(manifest) is not dict:
        deny("receipt_not_object", "candidate manifest")
    exact_keys(manifest, MANIFEST_KEYS, "candidate manifest")
    _require_schema_version(manifest, "candidate manifest")
    if manifest["kind"] != "phase24-d222-candidate" or manifest["candidate_sha"] != candidate_arg or candidate_arg != current.get("PHASE24_D222_REV"):
        deny("candidate_handoff_mismatch")
    require_sha(manifest["candidate_sha"], "candidate SHA")
    require_sha(manifest["candidate_tree"], "candidate tree")
    require_sha(manifest["bootstrap_rev"], "bootstrap revision")
    require_sha(manifest["plan_rev"], "plan revision")
    require_digest(manifest["plan_sha256"], "plan digest")
    require_digest(manifest["gate_sha256"], "gate digest")
    if manifest["bootstrap_rev"] != bootstrap["gate"]["rev"] or manifest["plan_rev"] != PLAN_REV or manifest["plan_sha256"] != PLAN_SHA256 or manifest["gate_sha256"] != bootstrap["gate"]["sha256"]:
        deny("manifest_anchor_mismatch")
    receipt_paths, receipt_raw = _bind_receipt_refs(
        manifest["receipts"],
        lambda path: (_check_ignored(git, path), _safe_receipt_path(root, path, max_bytes=MAX_JSON_BYTES)[1])[1],
    )
    manifest["receipts"] = receipt_paths
    manifest["_receipt_raw"] = receipt_raw
    remote = exact_keys(manifest["expected_remote"], REMOTE_EXPECTATION_KEYS, "manifest.expected_remote")
    if remote["repository"] != EXPECTED_REPO or type(remote["pull_request"]) is not int or remote["pull_request"] != EXPECTED_PR or remote["head_branch"] == "":
        deny("manifest_remote_identity")
    _text(remote["head_branch"], "expected_remote.head_branch", max_chars=200)
    require_sha(remote["prior_head_sha"], "expected_remote.prior_head_sha")
    require_sha(remote["base_sha"], "expected_remote.base_sha")
    require_digest(remote["protection_sha256"], "expected_remote.protection_sha256")
    candidate = _verify_candidate_scope(git, bootstrap, manifest["candidate_sha"])
    if candidate["tree"] != manifest["candidate_tree"]:
        deny("candidate_tree_mismatch")
    if manifest["causal_resolution"] is not None and type(manifest["causal_resolution"]) is not dict:
        deny("causal_resolution_type")
    if manifest["causal_resolution"] is not None:
        cause = exact_keys(manifest["causal_resolution"], {"previous_candidate_sha", "matrix_run_id", "run_attempt", "failed_context", "causal_fix_paths", "failure_contract"}, "candidate causal resolution")
        previous_sha = require_sha(cause["previous_candidate_sha"], "causal_resolution.previous_candidate_sha")
        if type(cause["matrix_run_id"]) is not str or re.fullmatch(r"[1-9][0-9]{0,19}", cause["matrix_run_id"]) is None or type(cause["run_attempt"]) is not int or cause["run_attempt"] < 1:
            deny("causal_resolution_run_binding")
        changed = {entry.path for entry in git.raw_diff(previous_sha, candidate["sha"])}
        if type(cause["causal_fix_paths"]) is not list or not set(cause["causal_fix_paths"]).issubset(changed):
            deny("candidate_two_fix_not_changed_from_first")
    provenance = _validate_provenance(root, manifest)
    qualification = _validate_qualification(root, manifest, provenance, bootstrap)
    code_review = _validate_review(root, manifest, provenance, "gsd-code-reviewer", "CLEAN")
    security_review = _validate_review(root, manifest, provenance, "gsd-security-auditor", "SECURED")
    if code_review["agent"] == security_review["agent"]:
        deny("reviewers_not_distinct")
    for review in (code_review, security_review):
        report_text = review["report_bytes"].decode("utf-8", errors="strict")
        if _server_side_enforcement_required(report_text):
            deny("server_side_enforcement_required")
    return dict(manifest), candidate, provenance, {"qualification": qualification, "code_review": code_review, "security_review": security_review}


class CommandRunner:
    def run(self, argv: Sequence[str], *, env: Mapping[str, str], timeout: float, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
        if type(argv) not in (list, tuple) or not argv or any(type(item) is not str or not item or "\x00" in item for item in argv):
            deny("invalid_fixed_argv")
        try:
            result = subprocess.run(list(argv), input=input_bytes, capture_output=True, check=False, timeout=timeout, env=dict(env))
        except subprocess.TimeoutExpired:
            deny("child_timeout")
        except OSError:
            deny("child_unavailable")
        if len(result.stdout) > MAX_OUTPUT_BYTES or len(result.stderr) > MAX_OUTPUT_BYTES:
            deny("child_output_too_large")
        return result


class GitHubReader:
    """Fixed-endpoint GitHub read adapter; endpoints are never caller supplied."""

    def __init__(self, runner: CommandRunner, env: Mapping[str, str], timeout: float = CHILD_TIMEOUT):
        self.runner = runner
        self.env = dict(env)
        self.timeout = timeout

    def get(self, route: str) -> Any:
        patterns = (
            re.escape(f"repos/{EXPECTED_REPO}"),
            re.escape(f"repos/{EXPECTED_REPO}/pulls/{EXPECTED_PR}"),
            re.escape(f"repos/{EXPECTED_REPO}/branches/{EXPECTED_BASE}/protection"),
            re.escape(f"repos/{EXPECTED_REPO}/commits/") + r"[0-9a-f]{40}/status",
            re.escape(f"repos/{EXPECTED_REPO}/commits/") + r"[0-9a-f]{40}/check-runs\?filter=latest&per_page=100",
            re.escape(f"repos/{EXPECTED_REPO}/actions/runs?head_sha=") + r"[0-9a-f]{40}&per_page=100",
            re.escape(f"repos/{EXPECTED_REPO}/actions/runs/") + r"[0-9]+/jobs\?per_page=100",
            re.escape(f"repos/{EXPECTED_REPO}/actions/runs/") + r"[1-9][0-9]{0,19}",
            re.escape(f"repos/{EXPECTED_REPO}/actions/runs/") + r"[1-9][0-9]{0,19}/jobs\?filter=latest&per_page=100",
            re.escape(f"repos/{EXPECTED_REPO}/commits/{EXPECTED_BASE}"),
            re.escape(f"repos/{EXPECTED_REPO}/commits/") + r"[0-9a-f]{40}",
        )
        if not any(re.fullmatch(pattern, route) for pattern in patterns):
            deny("unapproved_api_route")
        result = self.runner.run(["gh", "api", route], env=self.env, timeout=self.timeout)
        if result.returncode != 0:
            deny("github_read_failed", "GitHub readback failed or was unavailable")
        return strict_json_bytes(result.stdout, max_bytes=MAX_OUTPUT_BYTES)

    def auth_status(self) -> None:
        # stdout and stderr intentionally remain private: gh may include account
        # information or helper diagnostics, neither belongs in audit receipts.
        result = self.runner.run(["gh", "auth", "status", "--hostname", "github.com"], env=self.env, timeout=self.timeout)
        if result.returncode != 0:
            deny("github_auth_unavailable", "existing GitHub authentication is unavailable")


def _validate_pr_and_protection(git: Git, reader: GitHubReader, manifest: Mapping[str, Any], candidate: Mapping[str, Any], *, action: str) -> dict[str, Any]:
    repo = reader.get(f"repos/{EXPECTED_REPO}")
    if type(repo) is not dict or repo.get("full_name") != EXPECTED_REPO:
        deny("remote_repository_mismatch")
    permissions = repo.get("permissions")
    if type(permissions) is not dict or permissions.get("pull") is not True or permissions.get("push") is not True:
        deny("remote_read_permission_missing")
    pr = reader.get(f"repos/{EXPECTED_REPO}/pulls/{EXPECTED_PR}")
    if type(pr) is not dict or type(pr.get("number")) is not int or pr["number"] != EXPECTED_PR or pr.get("state") != "open" or pr.get("draft") is not False:
        deny("pull_request_not_promotable")
    head = pr.get("head")
    base = pr.get("base")
    if type(head) is not dict or type(base) is not dict or type(head.get("repo")) is not dict or type(base.get("repo")) is not dict:
        deny("pull_request_shape")
    remote = manifest["expected_remote"]
    if head["repo"].get("full_name") != EXPECTED_REPO or base["repo"].get("full_name") != EXPECTED_REPO or base.get("ref") != EXPECTED_BASE or base.get("sha") != remote["base_sha"]:
        deny("pull_request_base_or_repo_changed")
    if head.get("ref") != remote["head_branch"] or not valid_sha(head.get("sha")):
        deny("pull_request_head_identity")
    if action == "push":
        if head["sha"] != remote["prior_head_sha"] or head["sha"] == candidate["sha"]:
            deny("push_remote_head_changed")
    elif action == "merge":
        if head["sha"] != candidate["sha"] or remote["prior_head_sha"] != candidate["sha"]:
            deny("merge_head_mismatch")
    else:
        deny("invalid_action")
    protection = reader.get(f"repos/{EXPECTED_REPO}/branches/{EXPECTED_BASE}/protection")
    _validate_protection(protection)
    protection_digest = digest_bytes(canonical_json(protection))
    if not hmac.compare_digest(protection_digest, remote["protection_sha256"]):
        deny("protection_changed_or_stale")
    if action == "push":
        if not _candidate_contains(git, remote["base_sha"], candidate["sha"]):
            deny("candidate_not_based_on_current_main")
    return {"pr": pr, "protection": protection, "protection_sha256": protection_digest, "head_sha": head["sha"], "base_sha": base["sha"], "branch": head["ref"]}


def _validate_protection(value: Any) -> None:
    if type(value) is not dict:
        deny("protection_unreadable")
    status = value.get("required_status_checks")
    if type(status) is not dict or status.get("strict") is not True:
        deny("protection_not_strict")
    contexts = status.get("contexts")
    checks = status.get("checks")
    if type(contexts) is not list or any(type(item) is not str for item in contexts) or tuple(sorted(contexts)) != tuple(sorted(REQUIRED_CONTEXTS)):
        deny("required_contexts_changed")
    if type(checks) is not list:
        deny("required_context_apps_unreadable")
    check_contexts: list[str] = []
    for item in checks:
        if type(item) is not dict or type(item.get("context")) is not str or type(item.get("app_id")) is not int or item["app_id"] <= 0:
            deny("required_context_app_shape")
        check_contexts.append(item["context"])
    if tuple(sorted(check_contexts)) != tuple(sorted(REQUIRED_CONTEXTS)):
        deny("required_context_app_bindings_changed")
    for key in ("enforce_admins", "allow_force_pushes", "allow_deletions"):
        policy = value.get(key)
        if type(policy) is not dict or type(policy.get("enabled")) is not bool:
            deny("protection_policy_shape", key)
    if value["enforce_admins"]["enabled"] is not True or value["allow_force_pushes"]["enabled"] is not False or value["allow_deletions"]["enabled"] is not False:
        deny("protection_policy_changed")


def _protected_app_ids(value: Any) -> dict[str, int]:
    _validate_protection(value)
    checks = value["required_status_checks"]["checks"]
    mapping = {item["context"]: item["app_id"] for item in checks}
    if set(mapping) != set(REQUIRED_CONTEXTS):
        deny("required_context_app_bindings_changed")
    return mapping


def _validate_workflow_path(run: Mapping[str, Any], context: str) -> None:
    path = run.get("path")
    if type(path) is not str or path.split("@", 1)[0] != REQUIRED_WORKFLOW_PATHS[context]:
        deny("required_context_workflow_mismatch", context)


def _configured_python(root: Path) -> str:
    root_resolved = root.resolve(strict=True)
    relative = Path("build/CMakeCache.txt")
    cursor = root_resolved
    try:
        for component in relative.parts:
            cursor = cursor / component
            info = cursor.lstat()
            if stat.S_ISLNK(info.st_mode):
                deny("cmake_cache_symlink")
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_CMAKE_CACHE_BYTES:
            deny("cmake_cache_shape")
        cache_path = cursor.resolve(strict=True)
        cache_path.relative_to(root_resolved)
        raw = cache_path.read_bytes()
    except (OSError, ValueError):
        deny("cmake_cache_unavailable")
    if len(raw) > MAX_CMAKE_CACHE_BYTES:
        deny("cmake_cache_too_large")
    try:
        lines = raw.decode("utf-8", errors="strict").splitlines()
    except UnicodeDecodeError:
        deny("cmake_cache_encoding")
    entries = [line for line in lines if line.startswith("Python3_EXECUTABLE")]
    if len(entries) != 1:
        deny("cmake_python_entry_ambiguous")
    match = re.fullmatch(r"Python3_EXECUTABLE:[A-Z_]+=(.+)", entries[0])
    if match is None:
        deny("cmake_python_entry_shape")
    value = match.group(1)
    if value != value.strip() or not Path(value).is_absolute():
        deny("cmake_python_path_invalid")
    try:
        executable = Path(value)
        resolved = executable.resolve(strict=True)
        if not resolved.is_file() or not os.access(resolved, os.X_OK):
            deny("cmake_python_unavailable")
    except OSError:
        deny("cmake_python_unavailable")
    return value


def _validate_status_and_checks(reader: GitHubReader, candidate: Mapping[str, Any], pr_branch: str, protection: Mapping[str, Any]) -> dict[str, Any]:
    sha = candidate["sha"]
    protected_apps = _protected_app_ids(protection)
    status = reader.get(f"repos/{EXPECTED_REPO}/commits/{sha}/status")
    if type(status) is not dict or status.get("sha") != sha or type(status.get("statuses")) is not list:
        deny("commit_status_shape")
    statuses = status["statuses"]
    by_context: dict[str, list[dict[str, Any]]] = {name: [] for name in REQUIRED_CONTEXTS}
    for row in statuses:
        if type(row) is not dict or type(row.get("context")) is not str or type(row.get("state")) is not str or type(row.get("id")) is not int or row["id"] <= 0:
            deny("commit_status_row_shape")
        if row["context"] in by_context:
            by_context[row["context"]].append(row)
    if any(len(rows) > 1 for rows in by_context.values()):
        deny("commit_status_duplicate")
    for context, rows in by_context.items():
        if not rows:
            continue
        row = rows[0]
        if row["state"] != "success" or type(row.get("creator")) is not dict or type(row.get("creator", {}).get("login")) is not str or type(row.get("updated_at")) is not str:
            deny("legacy_commit_status_not_success", context)
    checks = reader.get(f"repos/{EXPECTED_REPO}/commits/{sha}/check-runs?filter=latest&per_page=100")
    if type(checks) is not dict or checks.get("total_count") != len(checks.get("check_runs", [])) or type(checks.get("check_runs")) is not list:
        deny("check_runs_shape")
    run_by_name: dict[str, list[dict[str, Any]]] = {name: [] for name in REQUIRED_CONTEXTS}
    for row in checks["check_runs"]:
        if type(row) is not dict:
            deny("check_run_row_shape")
        name = row.get("name")
        if name in run_by_name:
            suite = row.get("check_suite")
            app = row.get("app")
            pulls = row.get("pull_requests")
            if row.get("head_sha") != sha or row.get("status") != "completed" or row.get("conclusion") != "success" or type(suite) is not dict or type(suite.get("id")) is not int or type(app) is not dict or type(app.get("id")) is not int or app["id"] != protected_apps[name] or type(pulls) is not list or sum(1 for p in pulls if type(p) is dict and p.get("number") == EXPECTED_PR) != 1:
                deny("required_check_not_current_success", str(name))
            run_by_name[name].append(row)
    if any(len(rows) != 1 for rows in run_by_name.values()):
        deny("check_run_duplicate_or_missing")
    runs = reader.get(f"repos/{EXPECTED_REPO}/actions/runs?head_sha={sha}&per_page=100")
    if type(runs) is not dict or type(runs.get("workflow_runs")) is not list or runs.get("total_count") != len(runs["workflow_runs"]):
        deny("workflow_runs_shape")
    latest: dict[tuple[int, int], dict[str, Any]] = {}
    seen_attempts: set[tuple[int, int, int]] = set()
    for run in runs["workflow_runs"]:
        if (type(run) is not dict or any(type(run.get(field)) is not int or run[field] <= 0 for field in ("id", "workflow_id", "run_number", "run_attempt", "check_suite_id"))):
            deny("workflow_run_row_shape")
        if run["run_attempt"] != 1:
            deny("workflow_rerun_prohibited")
        if run.get("head_sha") != sha:
            deny("workflow_run_wrong_sha")
        pulls = run.get("pull_requests")
        if (run.get("event") != "pull_request" or run.get("head_branch") != pr_branch or run.get("status") != "completed" or run.get("conclusion") != "success"
                or type(pulls) is not list or sum(1 for p in pulls if type(p) is dict and p.get("number") == EXPECTED_PR) != 1):
            deny("workflow_run_not_current_success")
        key = (run["workflow_id"], run["run_number"])
        attempt_key = (run["workflow_id"], run["run_number"], run["run_attempt"])
        if attempt_key in seen_attempts:
            deny("workflow_run_attempt_ambiguous")
        seen_attempts.add(attempt_key)
        if key not in latest or run["run_attempt"] > latest[key]["run_attempt"]:
            latest[key] = run
        elif run["run_attempt"] == latest[key]["run_attempt"]:
            deny("workflow_run_attempt_ambiguous")
    if not latest:
        deny("workflow_runs_missing")
    context_runs: dict[str, dict[str, Any]] = {}
    for context, rows in run_by_name.items():
        check = rows[0]
        suite_id = check.get("check_suite", {}).get("id")
        matching_runs = [run for run in latest.values() if run.get("check_suite_id") == suite_id]
        if type(suite_id) is not int or len(matching_runs) != 1:
            deny("check_run_not_bound_to_latest_workflow")
        _validate_workflow_path(matching_runs[0], context)
        context_runs[context] = matching_runs[0]
    # Read each latest job collection and prove the required check name is a
    # completed job in the matching current workflow run, not only a parent pass.
    for context, rows in run_by_name.items():
        workflow_run = context_runs[context]
        workflow_run_id = workflow_run["id"]
        job_list = reader.get(f"repos/{EXPECTED_REPO}/actions/runs/{workflow_run_id}/jobs?per_page=100")
        if type(job_list) is not dict or type(job_list.get("jobs")) is not list or job_list.get("total_count") != len(job_list["jobs"]):
            deny("workflow_jobs_shape", context)
        matching = [job for job in job_list["jobs"] if type(job) is dict and job.get("name") == context]
        if len(matching) != 1:
            deny("workflow_job_duplicate_or_missing", context)
        job = matching[0]
        if job.get("run_id") != workflow_run_id or job.get("head_sha") != sha or job.get("status") != "completed" or job.get("conclusion") != "success" or type(job.get("id")) is not int or job["id"] <= 0:
            deny("workflow_job_not_current_success", context)
    return {"contexts": list(REQUIRED_CONTEXTS), "workflow_run_ids": sorted(run["id"] for run in context_runs.values()), "attempts": sorted(run["run_attempt"] for run in context_runs.values())}


def _validate_causal_matrix_failure(reader: GitHubReader, candidate: Mapping[str, Any], manifest: Mapping[str, Any], state: Mapping[str, Any], remote: Mapping[str, Any]) -> dict[str, Any]:
    cause = exact_keys(manifest.get("causal_resolution"), {"previous_candidate_sha", "matrix_run_id", "run_attempt", "failed_context", "causal_fix_paths", "failure_contract"}, "candidate two causal resolution")
    run_id = cause["matrix_run_id"]
    attempt = cause["run_attempt"]
    context = cause["failed_context"]
    if type(run_id) is not str or re.fullmatch(r"[1-9][0-9]{0,19}", run_id) is None or type(attempt) is not int or attempt != 1 or context not in REQUIRED_CONTEXTS:
        deny("causal_remote_binding_shape")
    if state.get("candidate_number") != 2 or state.get("failure_run_id") != run_id or state.get("failure_run_attempt") != attempt or state.get("failed_context") != context:
        deny("causal_remote_history_mismatch")
    previous_sha = require_sha(cause["previous_candidate_sha"], "causal_resolution.previous_candidate_sha")
    if remote.get("head_sha") != previous_sha:
        deny("causal_previous_head_not_current")
    reconciled = _reconcile_candidate_one_context_runs(reader, previous_sha, remote.get("branch"), context, run_id, attempt, remote.get("protection"))
    run = reader.get(f"repos/{EXPECTED_REPO}/actions/runs/{run_id}")
    if type(run) is not dict or type(run.get("id")) is not int or run["id"] != int(run_id) or type(run.get("run_attempt")) is not int or run["run_attempt"] != attempt:
        deny("causal_remote_attempt_unknown_or_repeated")
    pulls = run.get("pull_requests")
    if (run.get("head_sha") != previous_sha or run.get("event") != "pull_request" or run.get("head_branch") != remote.get("branch")
            or run.get("status") != "completed" or run.get("conclusion") != "failure" or type(pulls) is not list
            or sum(1 for item in pulls if type(item) is dict and item.get("number") == EXPECTED_PR) != 1):
        deny("causal_remote_run_not_failed_current_pr")
    _validate_workflow_path(run, context)
    jobs = reader.get(f"repos/{EXPECTED_REPO}/actions/runs/{run_id}/jobs?filter=latest&per_page=100")
    if type(jobs) is not dict or type(jobs.get("jobs")) is not list or jobs.get("total_count") != len(jobs["jobs"]):
        deny("causal_remote_jobs_shape")
    matching = [job for job in jobs["jobs"] if type(job) is dict and job.get("name") == context]
    if len(matching) != 1:
        deny("causal_remote_job_ambiguous")
    job = matching[0]
    if (job.get("run_id") != int(run_id) or job.get("head_sha") != previous_sha
            or job.get("status") != "completed" or job.get("conclusion") != "failure"
            or type(job.get("id")) is not int or job["id"] <= 0):
        deny("causal_remote_job_not_terminal_failure")
    return {"run_id": run_id, "run_attempt": attempt, "context": context, "job_id": job["id"], "head_sha": previous_sha, "context_run_ids": reconciled["context_run_ids"]}


def _reconcile_candidate_one_context_runs(reader: GitHubReader, sha: str, branch: Any, failed_context: str, failed_run_id: str, failed_attempt: int, protection: Mapping[str, Any]) -> dict[str, Any]:
    protected_apps = _protected_app_ids(protection)
    checks = reader.get(f"repos/{EXPECTED_REPO}/commits/{sha}/check-runs?filter=latest&per_page=100")
    if type(checks) is not dict or type(checks.get("check_runs")) is not list or checks.get("total_count") != len(checks["check_runs"]):
        deny("causal_check_runs_shape")
    by_context: dict[str, list[dict[str, Any]]] = {name: [] for name in REQUIRED_CONTEXTS}
    for row in checks["check_runs"]:
        if type(row) is not dict:
            deny("causal_check_run_row_shape")
        if row.get("name") not in by_context:
            continue
        suite = row.get("check_suite")
        pulls = row.get("pull_requests")
        if (row.get("head_sha") != sha or row.get("status") != "completed" or row.get("conclusion") not in {"success", "failure"}
                or type(suite) is not dict or type(suite.get("id")) is not int or suite["id"] <= 0
                or type(row.get("app")) is not dict or type(row["app"].get("id")) is not int or row["app"]["id"] != protected_apps[row["name"]]
                or type(pulls) is not list or sum(1 for item in pulls if type(item) is dict and item.get("number") == EXPECTED_PR) != 1):
            deny("causal_check_run_not_current_terminal", str(row.get("name")))
        by_context[row["name"]].append(row)
    if any(len(by_context[name]) != 1 for name in REQUIRED_CONTEXTS):
        deny("causal_required_context_check_ambiguous")
    context_suites: dict[str, int] = {}
    for name, rows in by_context.items():
        context_suites[name] = rows[0]["check_suite"]["id"]
    if len(set(context_suites.values())) != len(REQUIRED_CONTEXTS):
        deny("causal_context_suite_reused")
    if by_context[failed_context][0]["conclusion"] != "failure":
        deny("causal_failed_context_run_mismatch")
    run_list = reader.get(f"repos/{EXPECTED_REPO}/actions/runs?head_sha={sha}&per_page=100")
    if type(run_list) is not dict or type(run_list.get("workflow_runs")) is not list or run_list.get("total_count") != len(run_list["workflow_runs"]):
        deny("causal_workflow_runs_shape")
    by_id: dict[int, dict[str, Any]] = {}
    workflow_numbers: set[tuple[int, int]] = set()
    for row in run_list["workflow_runs"]:
        if (type(row) is not dict or any(type(row.get(field)) is not int or row[field] <= 0 for field in ("id", "workflow_id", "run_number", "run_attempt", "check_suite_id"))):
            deny("causal_workflow_run_row_shape")
        if row["run_attempt"] != 1:
            deny("causal_workflow_rerun_prohibited")
        key = (row["workflow_id"], row["run_number"])
        if row["id"] in by_id or key in workflow_numbers:
            deny("causal_workflow_run_duplicate_or_repeated_attempt")
        by_id[row["id"]] = row
        workflow_numbers.add(key)
        pulls = row.get("pull_requests")
        if (row.get("head_sha") != sha or row.get("event") != "pull_request" or row.get("head_branch") != branch
                or row.get("status") != "completed" or row.get("conclusion") not in {"success", "failure"}
                or type(pulls) is not list or sum(1 for item in pulls if type(item) is dict and item.get("number") == EXPECTED_PR) != 1):
            deny("causal_workflow_run_not_current_terminal")
    context_runs: dict[str, dict[str, Any]] = {}
    for context, suite_id in context_suites.items():
        matching = [row for row in by_id.values() if row["check_suite_id"] == suite_id]
        if len(matching) != 1:
            deny("causal_context_run_missing_from_latest_list", context)
        context_runs[context] = matching[0]
        row = matching[0]
        _validate_workflow_path(row, context)
        if context == failed_context and (str(row["id"]) != failed_run_id or row["run_attempt"] != failed_attempt or row["conclusion"] != "failure"):
            deny("causal_context_latest_attempt_mismatch", context)
    return {"context_run_ids": {name: row["id"] for name, row in context_runs.items()}, "context_run_attempts": {name: row["run_attempt"] for name, row in context_runs.items()}}


def _git_config_values(git: Git, *args: str) -> list[str]:
    result = git.run_result("config", "--local", *args)
    if result.returncode not in (0, 1):
        deny("git_remote_config_unreadable")
    if result.returncode == 1:
        return []
    try:
        values = result.stdout.decode("utf-8", errors="strict").splitlines()
    except UnicodeDecodeError:
        deny("git_remote_config_encoding")
    if any(not value or "\x00" in value for value in values):
        deny("git_remote_config_invalid")
    return values


def _verify_origin(git: Git) -> None:
    urls = _git_config_values(git, "--get-all", "remote.origin.url")
    push_urls = _git_config_values(git, "--get-all", "remote.origin.pushurl")
    if urls != [EXPECTED_URL] or push_urls not in ([], [EXPECTED_URL]):
        deny("origin_url_mismatch")
    follow_tags = _git_config_values(git, "--get-all", "push.followTags")
    if len(follow_tags) > 1:
        deny("origin_follow_tags_ambiguous")
    if follow_tags:
        value = follow_tags[0].casefold()
        if value in {"true", "yes", "on", "1"}:
            deny("origin_follow_tags_enabled")
        if value not in {"false", "no", "off", "0"}:
            deny("origin_follow_tags_ambiguous")
    mirror = _git_config_values(git, "--get-all", "remote.origin.mirror")
    if len(mirror) > 1:
        deny("origin_mirror_ambiguous")
    if mirror:
        value = mirror[0].casefold()
        if value in {"true", "yes", "on", "1"}:
            deny("origin_mirror_enabled")
        if value not in {"false", "no", "off", "0"}:
            deny("origin_mirror_ambiguous")
    effective_result = git.run_result("remote", "get-url", "--push", "origin")
    if effective_result.returncode != 0 or effective_result.stdout.decode("utf-8", errors="strict").strip() != EXPECTED_URL:
        deny("effective_push_url_mismatch")


def _credential_probe(runner: CommandRunner, root: Path, env: Mapping[str, str]) -> None:
    if not env.get("HOME"):
        deny("auth_home_missing")
    argv = [
        "git", "--no-replace-objects", "-c", "credential.helper=",
        "-c", "credential.helper=!gh auth git-credential",
        "-c", "credential.interactive=false", "-C", str(root), "credential", "fill",
    ]
    request = b"protocol=https\nhost=github.com\npath=szTheory/gabbaboy.git\n\n"
    result = runner.run(argv, env=env, timeout=CHILD_TIMEOUT, input_bytes=request)
    if result.returncode != 0:
        deny("credential_path_unavailable", "existing credential helper did not provide credentials")
    output = bytearray(result.stdout)
    try:
        decoded = output.decode("utf-8", errors="strict")
        pairs: dict[str, str] = {}
        for line in decoded.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                if key in pairs:
                    deny("credential_response_ambiguous")
                pairs[key] = value
        if not pairs.get("username") or not pairs.get("password"):
            deny("credential_path_empty", "existing credential helper returned no usable credentials")
    except UnicodeDecodeError:
        deny("credential_response_encoding")
    finally:
        for index in range(len(output)):
            output[index] = 0
        del output


HISTORY_KEYS = {"schema_version", "kind", "records", "head"}
HISTORY_RECORD_KEYS = {
    "seq", "kind", "candidate_sha", "candidate_tree", "action_id", "previous_digest",
    "digest", "outcome", "run_id", "context", "in_scope", "causal_fix_paths",
    "remote_head_sha", "base_sha", "branch", "run_attempt",
}
ZERO_DIGEST = "0" * 64


def _record_digest(record: Mapping[str, Any]) -> str:
    body = {key: value for key, value in record.items() if key != "digest"}
    return digest_bytes(bytes.fromhex(str(record["previous_digest"])) + canonical_json(body))


def _historical_record(seq: int, sha: str, tree: str, outcome: str, previous_digest: str) -> dict[str, Any]:
    value = {
        "seq": seq,
        "kind": "historical",
        "candidate_sha": sha,
        "candidate_tree": tree,
        "action_id": None,
        "previous_digest": previous_digest,
        "digest": "0" * 64,
        "outcome": outcome,
        "run_id": None,
        "context": None,
        "in_scope": False,
        "causal_fix_paths": [],
        "remote_head_sha": None,
        "base_sha": None,
        "branch": None,
        "run_attempt": None,
    }
    value["digest"] = _record_digest(value)
    return value


def _validate_history(value: Any) -> list[dict[str, Any]]:
    history = exact_keys(value, HISTORY_KEYS, "history")
    _require_schema_version(history, "history")
    if history["kind"] != "phase24-d222-history" or type(history["records"]) is not list:
        deny("history_shape")
    records: list[dict[str, Any]] = []
    previous = ZERO_DIGEST
    for index, raw in enumerate(history["records"]):
        record = exact_keys(raw, HISTORY_RECORD_KEYS, f"history.record[{index}]")
        if type(record["seq"]) is not int or record["seq"] != index or record["previous_digest"] != previous or not valid_sha256(record["digest"]):
            deny("history_chain_sequence")
        if _record_digest(record) != record["digest"]:
            deny("history_chain_digest")
        if not valid_sha(record["candidate_sha"]) or not valid_sha(record["candidate_tree"]):
            deny("history_candidate_sha")
        if type(record["causal_fix_paths"]) is not list or any(type(path) is not str for path in record["causal_fix_paths"]):
            deny("history_causal_paths")
        if record["kind"] == "historical":
            if record["run_id"] is not None or record["run_attempt"] is not None:
                deny("history_historical_run_binding")
        elif record["kind"] == "matrix_result":
            if type(record["run_id"]) is not str or re.fullmatch(r"[1-9][0-9]{0,19}", record["run_id"]) is None or type(record["run_attempt"]) is not int or record["run_attempt"] < 1:
                deny("history_matrix_run_binding")
        elif record["run_id"] is not None or record["run_attempt"] is not None:
            deny("history_unexpected_run_binding")
        records.append(dict(record))
        previous = record["digest"]
    if len(records) < 2 or records[:2] != [
        _historical_record(0, D220_SHA, "bca9ae3eb312ca732f2386a04812ea0f304ae91d", "matrix_failed", ZERO_DIGEST),
        _historical_record(1, D221_SHA, D221_TREE, "review_no_go", _historical_record(0, D220_SHA, "bca9ae3eb312ca732f2386a04812ea0f304ae91d", "matrix_failed", ZERO_DIGEST)["digest"]),
    ]:
        deny("history_missing_immutable_prior_results")
    if history["head"] != previous:
        deny("history_head_mismatch")
    _validate_history_transitions(records)
    return records


def _validate_history_transitions(records: Sequence[Mapping[str, Any]]) -> None:
    by_action: dict[str, list[Mapping[str, Any]]] = {}
    reservations: list[Mapping[str, Any]] = []
    terminal_matrix: dict[str, Mapping[str, Any]] = {}
    successful_candidate: str | None = None
    did_merge = False
    for index, record in enumerate(records[2:], start=2):
        kind = record["kind"]
        if kind not in {"reservation", "push_result", "matrix_result", "merge_reservation", "merge_result"}:
            deny("history_record_kind")
        action_id = record["action_id"]
        if type(action_id) is not str or re.fullmatch(r"[0-9a-f]{32}", action_id) is None:
            deny("history_action_id")
        by_action.setdefault(action_id, []).append(record)
        if kind == "reservation":
            if successful_candidate is not None or record["outcome"] != "ALLOW" or any(item["candidate_sha"] == record["candidate_sha"] for item in reservations):
                deny("history_reservation_replay")
            reservations.append(record)
            if len(reservations) > 2:
                deny("matrix_candidate_limit")
            if len(reservations) == 2:
                first = reservations[0]
                failure = terminal_matrix.get(first["candidate_sha"])
                if failure is None or failure["outcome"] != "failed" or failure["in_scope"] is not True or failure["context"] not in REQUIRED_CONTEXTS or not set(failure["causal_fix_paths"]).intersection(EXPECTED_CANDIDATE_CORRECTIONS) or record["candidate_sha"] == first["candidate_sha"]:
                    deny("candidate_two_not_causally_eligible")
        elif kind == "push_result":
            matches = [item for item in by_action[action_id] if item["kind"] == "reservation"]
            if len(matches) != 1 or record["outcome"] != "pushed" or record["candidate_sha"] != matches[0]["candidate_sha"]:
                deny("history_push_transition")
        elif kind == "matrix_result":
            if record["candidate_sha"] not in {item["candidate_sha"] for item in reservations} or record["outcome"] not in {"passed", "failed"} or type(record["run_id"]) is not str or not record["run_id"]:
                deny("history_matrix_transition")
            if not any(item["kind"] == "reservation" and item["action_id"] == action_id and item["candidate_sha"] == record["candidate_sha"] for item in by_action[action_id]):
                deny("history_matrix_action_binding")
            if record["run_id"] in {item.get("run_id") for item in records[:index] if item["kind"] == "matrix_result"}:
                deny("history_duplicate_or_repeated_attempt")
            if record["outcome"] == "failed":
                if record["context"] not in REQUIRED_CONTEXTS or record["in_scope"] is not True:
                    deny("history_failure_out_of_scope")
            else:
                if record["context"] is not None or record["in_scope"] is not False:
                    deny("history_success_shape")
                if successful_candidate is not None:
                    deny("multiple_matrix_successes")
                successful_candidate = record["candidate_sha"]
            terminal_matrix[record["candidate_sha"]] = record
        elif kind == "merge_reservation":
            if record["outcome"] != "ALLOW" or terminal_matrix.get(record["candidate_sha"], {}).get("outcome") != "passed":
                deny("history_merge_reservation_transition")
            if any(item["kind"] == "merge_reservation" for item in records[2:index]):
                deny("history_merge_reservation_replay")
        elif kind == "merge_result":
            if did_merge or record["outcome"] != "merged" or terminal_matrix.get(record["candidate_sha"], {}).get("outcome") != "passed" or not any(item["kind"] == "merge_reservation" and item["action_id"] == action_id for item in records[2:index]):
                deny("history_merge_transition")
            did_merge = True
    for action_id, items in by_action.items():
        kinds = [item["kind"] for item in items]
        if kinds.count("reservation") != 1 or kinds.count("push_result") > 1 or kinds.count("matrix_result") > 1 or kinds.count("merge_result") > 1:
            deny("history_action_ambiguous")
        if "matrix_result" in kinds and "push_result" not in kinds:
            deny("history_matrix_without_push")
        if "merge_result" in kinds and "matrix_result" not in kinds:
            deny("history_merge_without_matrix")
        if "merge_result" in kinds and "merge_reservation" not in kinds:
            deny("history_merge_without_reservation")
        if "merge_reservation" in kinds and kinds.count("merge_reservation") != 1:
            deny("history_merge_action_ambiguous")


def _history_state(records: Sequence[Mapping[str, Any]], candidate: Mapping[str, Any], manifest: Mapping[str, Any], *, action: str) -> dict[str, Any]:
    reservations = [item for item in records[2:] if item["kind"] == "reservation"]
    pushes = [item for item in records[2:] if item["kind"] == "push_result"]
    matrices = [item for item in records[2:] if item["kind"] == "matrix_result"]
    merges = [item for item in records[2:] if item["kind"] == "merge_result"]
    merge_reservations = [item for item in records[2:] if item["kind"] == "merge_reservation"]
    if merges:
        deny("history_already_merged")
    if merge_reservations:
        deny("merge_action_already_reserved")
    candidate_sha = candidate["sha"]
    own_reservations = [item for item in reservations if item["candidate_sha"] == candidate_sha]
    own_matrix = [item for item in matrices if item["candidate_sha"] == candidate_sha]
    if action == "push":
        if own_reservations:
            deny("candidate_already_reserved")
        if len(reservations) >= 2:
            deny("matrix_candidate_limit")
        if len(reservations) == 0:
            if manifest["causal_resolution"] is not None:
                deny("unexpected_candidate_one_causality")
            return {"candidate_number": 1, "previous_candidate": None}
        if len(reservations) != 1:
            deny("history_candidate_sequence")
        first_sha = reservations[0]["candidate_sha"]
        first_results = [item for item in matrices if item["candidate_sha"] == first_sha]
        if len(first_results) != 1 or first_results[0]["outcome"] != "failed" or first_results[0]["in_scope"] is not True:
            deny("candidate_two_requires_in_scope_matrix_failure")
        first_failure = first_results[0]
        cause = exact_keys(manifest["causal_resolution"], {"previous_candidate_sha", "matrix_run_id", "run_attempt", "failed_context", "causal_fix_paths", "failure_contract"}, "candidate two causal resolution")
        if cause["previous_candidate_sha"] != first_sha or cause["matrix_run_id"] != first_failure["run_id"] or cause["run_attempt"] != first_failure["run_attempt"] or cause["failed_context"] != first_failure["context"]:
            deny("candidate_two_failure_binding")
        if cause["failed_context"] not in REQUIRED_CONTEXTS or type(cause["causal_fix_paths"]) is not list or not cause["causal_fix_paths"] or any(path not in EXPECTED_CANDIDATE_CORRECTIONS for path in cause["causal_fix_paths"]):
            deny("candidate_two_cause_scope")
        if not set(cause["causal_fix_paths"]).issubset(candidate["paths"]):
            deny("candidate_two_fix_not_in_diff")
        _text(cause["failure_contract"], "causal_resolution.failure_contract", max_chars=300)
        if candidate_sha == first_sha or candidate_sha in {D220_SHA, D221_SHA}:
            deny("candidate_two_unchanged_or_historical")
        return {"candidate_number": 2, "previous_candidate": first_sha, "failure_run_id": first_failure["run_id"], "failure_run_attempt": first_failure["run_attempt"], "failed_context": first_failure["context"]}
    if action == "merge":
        if len(own_reservations) != 1 or len(own_matrix) != 1 or own_matrix[0]["outcome"] != "passed":
            deny("merge_requires_current_matrix_success")
        if len(pushes) != len(reservations) or any(item["candidate_sha"] != candidate_sha for item in own_matrix):
            deny("merge_history_incomplete")
        return {"candidate_number": reservations.index(own_reservations[0]) + 1, "previous_candidate": None}
    deny("invalid_history_action")


def _new_action_id() -> str:
    return secrets.token_hex(16)


def _history_record_action(path: Path, records: list[dict[str, Any]], *, kind: str, candidate: Mapping[str, Any], action_id: str, outcome: str, run_id: str | None = None, run_attempt: int | None = None, context: str | None = None, in_scope: bool = False, causal_fix_paths: Sequence[str] = (), remote_head_sha: str | None = None, base_sha: str | None = None, branch: str | None = None) -> list[dict[str, Any]]:
    lock_path = path.with_name(path.name + ".lock")
    with _exclusive_lock(lock_path):
        _, current = _load_history_file(path.parent.parent.parent, str(path.relative_to(path.parent.parent.parent)))
        if [item["digest"] for item in current] != [item["digest"] for item in records]:
            deny("history_changed_during_action")
        _append_hash_record(
            current, kind=kind, candidate_sha=candidate["sha"], candidate_tree=candidate["tree"],
            action_id=action_id, outcome=outcome, run_id=run_id, context=context,
            run_attempt=run_attempt,
            in_scope=in_scope, causal_fix_paths=causal_fix_paths, remote_head_sha=remote_head_sha,
            base_sha=base_sha, branch=branch,
        )
        _persist_history(path, current)
        return current


def _authorization_contract(action: str, candidate: Mapping[str, Any], history_state: Mapping[str, Any], remote_state: Mapping[str, Any], *, auth_ready: bool, credential_ready: bool) -> None:
    if action not in {"push", "merge"}:
        deny("invalid_action")
    if not auth_ready:
        deny("auth_not_ready")
    if action == "push" and not credential_ready:
        deny("credential_not_ready")
    if remote_state.get("head_sha") == candidate.get("sha") and action == "push":
        deny("candidate_already_remote")
    if remote_state.get("branch") != history_state.get("branch", remote_state.get("branch")):
        deny("remote_branch_changed")
    if action == "merge" and remote_state.get("head_sha") != candidate.get("sha"):
        deny("merge_head_mismatch")


def _read_remote_after_push(reader: GitHubReader, candidate: Mapping[str, Any], expected_remote: Mapping[str, Any]) -> dict[str, Any]:
    pr = reader.get(f"repos/{EXPECTED_REPO}/pulls/{EXPECTED_PR}")
    if type(pr) is not dict or pr.get("state") != "open" or pr.get("draft") is not False or type(pr.get("head")) is not dict or type(pr.get("base")) is not dict:
        deny("post_push_pr_readback_ambiguous")
    head = pr["head"]
    base = pr["base"]
    if head.get("sha") != candidate["sha"] or head.get("ref") != expected_remote["head_branch"] or base.get("sha") != expected_remote["base_sha"] or base.get("ref") != EXPECTED_BASE:
        deny("post_push_head_readback_mismatch")
    return {"head_sha": head["sha"], "base_sha": base["sha"], "branch": head["ref"]}


def _read_merge_after_action(reader: GitHubReader, candidate: Mapping[str, Any], expected_remote: Mapping[str, Any]) -> dict[str, Any]:
    pr = reader.get(f"repos/{EXPECTED_REPO}/pulls/{EXPECTED_PR}")
    if type(pr) is not dict or pr.get("merged") is not True or pr.get("state") != "closed" or type(pr.get("head")) is not dict or type(pr.get("base")) is not dict:
        deny("merge_readback_not_complete")
    merge_sha = pr.get("merge_commit_sha")
    if not valid_sha(merge_sha) or pr["head"].get("sha") != candidate["sha"] or pr["base"].get("ref") != EXPECTED_BASE:
        deny("merge_readback_identity")
    merge_commit = reader.get(f"repos/{EXPECTED_REPO}/commits/{merge_sha}")
    main_commit = reader.get(f"repos/{EXPECTED_REPO}/commits/{EXPECTED_BASE}")
    if type(merge_commit) is not dict or type(merge_commit.get("sha")) is not str or merge_commit["sha"] != merge_sha or type(merge_commit.get("tree")) is not dict or merge_commit["tree"].get("sha") != candidate["tree"] or type(merge_commit.get("parents")) is not list or not any(type(parent) is dict and parent.get("sha") == candidate["sha"] for parent in merge_commit["parents"]):
        deny("merge_tree_or_parent_mismatch")
    if type(main_commit) is not dict or main_commit.get("sha") != merge_sha:
        deny("main_readback_mismatch")
    return {"merge_sha": merge_sha, "tree": candidate["tree"], "main_sha": main_commit["sha"]}


def _require_command_success(result: subprocess.CompletedProcess[bytes], reason: str) -> None:
    if result.returncode != 0:
        # Do not forward subprocess output: credential helpers and gh can emit
        # authentication details or private account information.
        deny(reason)


def _dispatch_fixed_action(action: str, candidate: Mapping[str, Any], branch: str, runner: CommandRunner, env: Mapping[str, str], *, timeout: float = CHILD_TIMEOUT) -> subprocess.CompletedProcess[bytes]:
    if action == "push":
        argv = fixed_push_argv(candidate["sha"], branch)
    elif action == "merge":
        argv = fixed_merge_argv(candidate["sha"])
    else:
        deny("invalid_action")
    return runner.run(argv, env=env, timeout=timeout)


def _run_live(root: Path, args: argparse.Namespace, runner: CommandRunner | None = None) -> dict[str, Any]:
    if runner is not None and not _SELF_TEST_ACTIVE:
        deny("injected_runner_is_self_test_only")
    reject_hostile_git_environment()
    git = Git(root)
    _verify_origin(git)
    bootstrap_path = args.bootstrap or os.environ.get("PHASE24_D222_BOOTSTRAP", "")
    if not bootstrap_path:
        deny("missing_bootstrap_receipt")
    bootstrap_path = _receipt_path_under_build(bootstrap_path, "bootstrap receipt")
    _check_ignored(git, bootstrap_path)
    _, bootstrap_receipt, _ = _load_receipt(root, bootstrap_path)
    exact_keys(bootstrap_receipt, {"schema_version", "kind", "plan", "discussion", "closeout", "loader", "inherited_gate", "gate", "repository", "scope", "history_pins", "trusted_handoff"}, "bootstrap")
    _require_schema_version(bootstrap_receipt, "bootstrap")
    if bootstrap_receipt.get("kind") != "phase24-d227-bootstrap":
        deny("bootstrap_kind")
    bootstrap = _verify_bootstrap_source(git, bootstrap_receipt)
    manifest, candidate, provenance, evidence = _load_manifest(root, git, bootstrap, args.candidate, args.evidence)
    history_path, records = _load_history_file(root, manifest["receipts"]["history"], manifest["_receipt_raw"]["history"])
    effective_action = args.mode
    if effective_action == "preflight":
        matrix_result = next((item for item in records[2:] if item["kind"] == "matrix_result" and item["candidate_sha"] == candidate["sha"]), None)
        effective_action = "merge" if matrix_result is not None and matrix_result["outcome"] == "passed" else "push"
    state = _history_state(records, candidate, manifest, action=effective_action)
    reader_runner = runner or CommandRunner()
    gh_env = auth_environment()
    reader = GitHubReader(reader_runner, gh_env)
    reader.auth_status()
    remote = _validate_pr_and_protection(git, reader, manifest, candidate, action=effective_action)
    state = {**state, "branch": remote["branch"]}
    if effective_action == "push" and state.get("candidate_number") == 2:
        state["causal_readback"] = _validate_causal_matrix_failure(reader, candidate, manifest, state, remote)
    if args.mode == "preflight":
        return {
            "decision": "PREFLIGHT_OK",
            "candidate_sha": candidate["sha"],
            "candidate_tree": candidate["tree"],
            "candidate_number": state["candidate_number"],
            "remote_head_sha": remote["head_sha"],
            "base_sha": remote["base_sha"],
            "required_contexts": list(REQUIRED_CONTEXTS),
            "promotion_executed": False,
        }
    if args.mode == "push":
        _credential_probe(reader_runner, root, gh_env)
        state = {**state, "branch": remote["branch"]}
        _authorization_contract(args.mode, candidate, state, remote, auth_ready=True, credential_ready=True)
        action_id = _new_action_id()
        records = _history_record_action(
            history_path, records, kind="reservation", candidate=candidate,
            action_id=action_id, outcome="ALLOW", remote_head_sha=remote["head_sha"],
            base_sha=remote["base_sha"], branch=remote["branch"],
        )
        result = _dispatch_fixed_action("push", candidate, remote["branch"], reader_runner, gh_env)
        _require_command_success(result, "push_failed_or_ambiguous")
        records = _history_record_action(
            history_path, records, kind="push_result", candidate=candidate,
            action_id=action_id, outcome="pushed", remote_head_sha=remote["head_sha"],
            base_sha=remote["base_sha"], branch=remote["branch"],
        )
        readback = _read_remote_after_push(reader, candidate, manifest["expected_remote"])
        return {"decision": "ALLOW", "action": "push", "candidate_sha": candidate["sha"], "candidate_tree": candidate["tree"], "action_id": action_id, "readback": readback, "matrix_started_by_pr_push": True, "promotion_command": "git push origin <candidate>:<validated-pr-head>"}
    if args.mode == "merge":
        matrix = _validate_status_and_checks(reader, candidate, remote["branch"], remote["protection"])
        _authorization_contract("merge", candidate, state, remote, auth_ready=True, credential_ready=True)
        action_id = _new_action_id()
        records = _history_record_action(
            history_path, records, kind="merge_reservation", candidate=candidate,
            action_id=action_id, outcome="ALLOW", remote_head_sha=remote["head_sha"],
            base_sha=remote["base_sha"], branch=remote["branch"],
        )
        result = _dispatch_fixed_action("merge", candidate, remote["branch"], reader_runner, gh_env)
        _require_command_success(result, "merge_failed_or_ambiguous")
        readback = _read_merge_after_action(reader, candidate, manifest["expected_remote"])
        _history_record_action(
            history_path, records, kind="merge_result", candidate=candidate,
            action_id=action_id, outcome="merged", remote_head_sha=remote["head_sha"],
            base_sha=remote["base_sha"], branch=remote["branch"],
        )
        return {"decision": "ALLOW", "action": "merge", "candidate_sha": candidate["sha"], "candidate_tree": candidate["tree"], "action_id": action_id, "matrix": matrix, "readback": readback, "promotion_command": "gh pr merge 154 --repo szTheory/gabbaboy --merge --match-head-commit <candidate>"}
    deny("invalid_action")




def _append_hash_record(records: list[dict[str, Any]], *, kind: str, candidate_sha: str, candidate_tree: str, action_id: str, outcome: str, run_id: str | None = None, run_attempt: int | None = None, context: str | None = None, in_scope: bool = False, causal_fix_paths: Sequence[str] = (), remote_head_sha: str | None = None, base_sha: str | None = None, branch: str | None = None) -> dict[str, Any]:
    prev = records[-1]["digest"] if records else ZERO_DIGEST
    record = {
        "seq": len(records), "kind": kind, "candidate_sha": candidate_sha,
        "candidate_tree": candidate_tree, "action_id": action_id,
        "previous_digest": prev, "digest": ZERO_DIGEST, "outcome": outcome,
        "run_id": run_id, "context": context, "in_scope": in_scope,
        "causal_fix_paths": list(causal_fix_paths), "remote_head_sha": remote_head_sha,
        "base_sha": base_sha, "branch": branch, "run_attempt": run_attempt,
    }
    record["digest"] = _record_digest(record)
    records.append(record)
    return record


@contextlib.contextmanager
def _exclusive_lock(path: Path):
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError:
        deny("history_locked", "trusted history is locked; do not retry or clear the lock automatically")
    try:
        os.write(fd, b"phase24-d222\n")
        os.fsync(fd)
        yield
    finally:
        os.close(fd)
        try:
            path.unlink()
        except OSError:
            deny("history_lock_cleanup_failed")


def _write_atomic(path: Path, data: bytes) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=".d222-", dir=str(path.parent))
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        dir_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def _load_history_file(root: Path, history_relative: str, raw_bytes: bytes | None = None) -> tuple[Path, list[dict[str, Any]]]:
    _check_ignored(Git(root), history_relative)
    if raw_bytes is None:
        path, value, _ = _load_receipt(root, history_relative)
    else:
        path, _ = _safe_receipt_path(root, history_relative, max_bytes=MAX_JSON_BYTES)
        value = strict_json_bytes(raw_bytes, max_bytes=MAX_JSON_BYTES)
        if type(value) is not dict:
            deny("receipt_not_object", history_relative)
    records = _validate_history(value)
    return path, records


def _persist_history(path: Path, records: list[dict[str, Any]]) -> None:
    head = records[-1]["digest"] if records else ZERO_DIGEST
    raw = canonical_json({"schema_version": 1, "kind": "phase24-d222-history", "records": records, "head": head}) + b"\n"
    _write_atomic(path, raw)


class _RecordingRunner(CommandRunner):
    def __init__(self, responses: Mapping[str, Any] | None = None, action_result: subprocess.CompletedProcess[bytes] | None = None, credential_output: bytes = b"username=private-user\npassword=private-secret\n", auth_ready: bool = True):
        self.responses = dict(responses or {})
        self.action_result = action_result or subprocess.CompletedProcess([], 0, b"", b"")
        self.credential_output = credential_output
        self.auth_ready = auth_ready
        self.calls: list[tuple[list[str], dict[str, str], float, bytes | None]] = []

    def run(self, argv: Sequence[str], *, env: Mapping[str, str], timeout: float, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
        self.calls.append((list(argv), dict(env), timeout, input_bytes))
        if len(argv) >= 3 and list(argv[:2]) == ["gh", "api"]:
            route = argv[2]
            if route not in self.responses:
                return subprocess.CompletedProcess(list(argv), 1, b"", b"private fake read failure")
            response = self.responses[route]
            if type(response) is list:
                if not response:
                    return subprocess.CompletedProcess(list(argv), 1, b"", b"private fake read exhausted")
                response = response.pop(0)
            return subprocess.CompletedProcess(list(argv), 0, canonical_json(response), b"")
        if len(argv) >= 3 and list(argv[:3]) == ["gh", "auth", "status"]:
            return subprocess.CompletedProcess(list(argv), 0 if self.auth_ready else 1, b"private fake auth output", b"")
        if len(argv) >= 2 and argv[0] == "git" and argv[-2:] == ["credential", "fill"]:
            return subprocess.CompletedProcess(list(argv), 0, self.credential_output, b"")
        return subprocess.CompletedProcess(list(argv), self.action_result.returncode, self.action_result.stdout, self.action_result.stderr)

    @property
    def action_calls(self) -> list[list[str]]:
        return [call[0] for call in self.calls if call[0] and call[0][0] in {"git", "gh"} and ("push" in call[0] or (call[0][:3] == ["gh", "pr", "merge"]))]


def _test_genesis_history() -> dict[str, Any]:
    first = _historical_record(0, D220_SHA, "bca9ae3eb312ca732f2386a04812ea0f304ae91d", "matrix_failed", ZERO_DIGEST)
    second = _historical_record(1, D221_SHA, D221_TREE, "review_no_go", first["digest"])
    return {"schema_version": 1, "kind": "phase24-d222-history", "records": [first, second], "head": second["digest"]}


def _test_history_append(history: dict[str, Any], **fields: Any) -> None:
    records = [dict(item) for item in history["records"]]
    _append_hash_record(records, **fields)
    history["records"] = records
    history["head"] = records[-1]["digest"]


def _fake_success_responses(sha: str, tree: str = "b" * 40, branch: str = "phase24-candidate") -> dict[str, Any]:
    statuses = []
    checks = []
    runs = []
    jobs: dict[str, Any] = {}
    for index, context in enumerate(REQUIRED_CONTEXTS):
        status_id = 101 + index
        run_id = 701 + index
        suite_id = 1701 + index
        statuses.append({"id": status_id, "context": context, "state": "success", "creator": {"login": "github-actions[bot]"}, "updated_at": "2026-11-20T00:00:00Z"})
        checks.append({
            "name": context, "head_sha": sha, "status": "completed", "conclusion": "success",
            "external_id": f"{run_id}:{900 + index}", "details_url": "https://github.com/szTheory/gabbaboy/actions",
            "check_suite": {"id": suite_id}, "app": {"id": 15368, "slug": "github-actions"},
            "pull_requests": [{"number": EXPECTED_PR}],
        })
        runs.append({
            "id": run_id, "workflow_id": 201 + index, "run_number": 1, "run_attempt": 1,
            "head_sha": sha, "check_suite_id": suite_id, "event": "pull_request", "head_branch": branch,
            "status": "completed", "conclusion": "success", "path": REQUIRED_WORKFLOW_PATHS[context] + "@refs/pull/154/merge",
            "name": f"workflow-{index}", "created_at": "2026-11-20T00:00:00Z", "updated_at": "2026-11-20T00:01:00Z",
            "repository": {"full_name": EXPECTED_REPO}, "head_repository": {"full_name": EXPECTED_REPO},
            "pull_requests": [{"number": EXPECTED_PR}],
        })
        jobs[f"repos/{EXPECTED_REPO}/actions/runs/{run_id}/jobs?per_page=100"] = {
            "total_count": 1,
            "jobs": [{"id": 901 + index, "run_id": run_id, "name": context, "head_sha": sha, "status": "completed", "conclusion": "success"}],
        }
    responses = {
        f"repos/{EXPECTED_REPO}/commits/{sha}/status": {"sha": sha, "statuses": statuses},
        f"repos/{EXPECTED_REPO}/commits/{sha}/check-runs?filter=latest&per_page=100": {"total_count": len(checks), "check_runs": checks},
        f"repos/{EXPECTED_REPO}/actions/runs?head_sha={sha}&per_page=100": {"total_count": len(runs), "workflow_runs": runs},
    }
    responses.update(jobs)
    return responses


def _fake_causal_failure_responses(run_id: str, attempt: int, sha: str, branch: str, context: str) -> dict[str, Any]:
    number = int(run_id)
    check_runs = []
    workflow_runs = []
    for index, name in enumerate(REQUIRED_CONTEXTS):
        actual_run_id = number if name == context else number + 100 + index
        suite_id = number + 1000 + index
        conclusion = "failure" if name == context else "success"
        check_runs.append({
            "name": name, "head_sha": sha, "status": "completed", "conclusion": conclusion,
            "check_suite": {"id": suite_id}, "app": {"id": 15368, "slug": "github-actions"},
            "pull_requests": [{"number": EXPECTED_PR}],
        })
        workflow_runs.append({
            "id": actual_run_id, "workflow_id": 501 + index, "run_number": 1,
            "run_attempt": attempt if name == context else 1, "check_suite_id": suite_id,
            "head_sha": sha, "event": "pull_request", "head_branch": branch,
            "status": "completed", "conclusion": conclusion, "path": REQUIRED_WORKFLOW_PATHS[name] + "@refs/pull/154/merge",
            "pull_requests": [{"number": EXPECTED_PR}],
        })
    responses: dict[str, Any] = {
        f"repos/{EXPECTED_REPO}/commits/{sha}/check-runs?filter=latest&per_page=100": {
            "total_count": len(check_runs), "check_runs": check_runs,
        },
        f"repos/{EXPECTED_REPO}/actions/runs?head_sha={sha}&per_page=100": {
            "total_count": len(workflow_runs), "workflow_runs": workflow_runs,
        },
        f"repos/{EXPECTED_REPO}/actions/runs/{run_id}": {
            "id": number, "run_attempt": attempt, "head_sha": sha, "event": "pull_request",
            "head_branch": branch, "status": "completed", "conclusion": "failure",
            "path": REQUIRED_WORKFLOW_PATHS[context] + "@refs/pull/154/merge",
            "pull_requests": [{"number": EXPECTED_PR}],
        },
        f"repos/{EXPECTED_REPO}/actions/runs/{run_id}/jobs?filter=latest&per_page=100": {
            "total_count": 1,
            "jobs": [{"id": number + 1, "run_id": number, "head_sha": sha, "name": context, "status": "completed", "conclusion": "failure"}],
        },
    }
    return responses


def _test_manifest_receipt_refs(bodies: Mapping[str, bytes]) -> dict[str, dict[str, str]]:
    return {
        key: {"path": f"build/phase24/{key}.json", "sha256": digest_bytes(bodies[key])}
        for key in MANIFEST_RECEIPT_KEYS
    }


def _test_protection() -> dict[str, Any]:
    return {
        "required_status_checks": {"strict": True, "contexts": list(REQUIRED_CONTEXTS), "checks": [{"context": name, "app_id": 15368} for name in REQUIRED_CONTEXTS]},
        "enforce_admins": {"enabled": True}, "allow_force_pushes": {"enabled": False}, "allow_deletions": {"enabled": False},
    }


class PromotionGateContractTests(unittest.TestCase):
    def test_d226_plan_anchor_accepts_exact_parent_bound_corrections(self) -> None:
        handoff = {"PHASE24_D222_PLAN_REV": PLAN_REV, "PHASE24_D222_PLAN_SHA256": PLAN_SHA256}
        try:
            anchor = validate_plan_anchor(Git(Path.cwd()), env=handoff)
        except GateError as error:
            self.fail(f"valid D226 plan anchor was denied by {error.reason}")
        self.assertEqual(anchor["rev"], PLAN_REV)
        self.assertEqual(anchor["parent"], PLAN_PARENT)
        self.assertEqual(anchor["inherited_gate"]["blob"], D226_GATE_BLOB)
        self.assertEqual(anchor["source_allowlist"], [*PLAN_SOURCE_PATHS, GATE_PATH])
        self.assertEqual(anchor["correction_allowlist"], list(EXPECTED_CANDIDATE_CORRECTIONS))

    def test_d226_plan_anchor_refuses_source_parent_or_correction_drift(self) -> None:
        real_git = Git(Path.cwd())
        handoff = {"PHASE24_D222_PLAN_REV": PLAN_REV, "PHASE24_D222_PLAN_SHA256": PLAN_SHA256}

        class MutatedTree:
            def __init__(self, fault: str) -> None:
                self.fault = fault
                self.action_calls: list[str] = []

            def __getattr__(self, name: str) -> Any:
                return getattr(real_git, name)

            def tree(self, rev: str) -> str:
                if self.fault == "source_tree" and rev == SOURCE_PARENT:
                    return "0" * 40
                return real_git.tree(rev)

            def tree_entry(self, rev: str, path: str) -> tuple[str, str, str]:
                entry = real_git.tree_entry(rev, path)
                if self.fault == "plan_correction_oid" and rev == PLAN_REV and path == EXPECTED_CANDIDATE_CORRECTIONS[0]:
                    return entry[0], entry[1], "0" * 40
                if self.fault == "parent_correction_mode" and rev == SOURCE_PARENT and path == EXPECTED_CANDIDATE_CORRECTIONS[0]:
                    return "100644", entry[1], entry[2]
                if self.fault == "parent_correction_type" and rev == SOURCE_PARENT and path == EXPECTED_CANDIDATE_CORRECTIONS[1]:
                    return entry[0], "tree", entry[2]
                if self.fault == "noncorrection_drift" and rev == PLAN_REV and path == PLAN_SOURCE_PATHS[0]:
                    return entry[0], entry[1], "0" * 40
                return entry

        expected = {
            "source_tree": "d226_source_parent_mismatch",
            "plan_correction_oid": "d226_correction_source_pin_mismatch",
            "parent_correction_mode": "d226_correction_source_pin_mismatch",
            "parent_correction_type": "d226_correction_source_pin_mismatch",
            "noncorrection_drift": "d221_source_drift",
        }
        for fault, reason in expected.items():
            with self.subTest(fault=fault):
                mutated = MutatedTree(fault)
                with self.assertRaises(GateError) as error:
                    validate_plan_anchor(mutated, env=handoff)
                self.assertEqual(error.exception.reason, reason)
                self.assertEqual(mutated.action_calls, [])

    def test_pinned_raw_tree_resolver_is_available_for_planning_blobs(self) -> None:
        resolver = getattr(Git, "pinned_blob", None)
        self.assertTrue(callable(resolver), "production Git adapter must resolve a planning blob by pinned raw-path digest")

    def test_pinned_raw_tree_resolver_selects_all_three_d226_planning_blobs(self) -> None:
        git = Git(Path.cwd())
        for rev, tree, path_hash, oid, content_hash in (
            (PLAN_REV, PLAN_TREE, PLAN_PATH_SHA256, PLAN_BLOB, PLAN_SHA256),
            (DISCUSSION_REV, DISCUSSION_TREE, DISCUSSION_PATH_SHA256, DISCUSSION_BLOB, DISCUSSION_SHA256),
            (CLOSEOUT_REV, CLOSEOUT_TREE, CLOSEOUT_PATH_SHA256, CLOSEOUT_BLOB, CLOSEOUT_SHA256),
        ):
            with self.subTest(path_sha256=path_hash):
                content = git.pinned_blob(rev, tree, path_hash, oid, content_hash)
                self.assertEqual(digest_bytes(content), content_hash)
        with self.assertRaises(GateError) as error:
            git.pinned_blob(PLAN_REV, PLAN_TREE, PLAN_PATH_SHA256, "0" * 40, PLAN_SHA256)
        self.assertEqual(error.exception.reason, "planning_blob_pin_mismatch")
        with self.assertRaises(GateError) as error:
            git.pinned_blob(PLAN_REV, PLAN_TREE, PLAN_PATH_SHA256, PLAN_BLOB, "0" * 64)
        self.assertEqual(error.exception.reason, "planning_blob_digest_mismatch")
        self.assertEqual(_validate_inherited_gate_boundary(git)["blob"], D226_GATE_BLOB)

    def test_pinned_raw_tree_resolver_preserves_newline_tab_and_non_utf8_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="phase24-tree-bytes-") as temp:
            root = Path(temp).resolve()
            env = source_git_env()
            def run(*args: str) -> bytes:
                result = subprocess.run(["git", "-C", str(root), *args], env=env, capture_output=True, check=True, timeout=15)
                return result.stdout
            run("init", "--quiet")
            run("config", "user.name", "Phase 24 test")
            run("config", "user.email", "phase24-test@example.invalid")
            target = b"odd\nname\t.txt"
            content = b"pinned bytes stay bytes\n"
            root_bytes = os.fsencode(root)
            fd = os.open(root_bytes + b"/" + target, os.O_CREAT | os.O_WRONLY, 0o600)
            try:
                os.write(fd, content)
            finally:
                os.close(fd)
            for name, body in ((b"plain.txt", b"plain\n"), (b"tab\tdecoy.txt", b"decoy\n"), (b"line\nbreak.txt", b"line\n")):
                fd = os.open(root_bytes + b"/" + name, os.O_CREAT | os.O_WRONLY, 0o600)
                try:
                    os.write(fd, body)
                finally:
                    os.close(fd)
            run("add", "--all")
            run("commit", "--quiet", "-m", "byte path fixture")
            rev = run("rev-parse", "HEAD").decode("ascii").strip()
            reader = Git(root)
            tree = reader.tree(rev)
            oid = hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\x00" + content).hexdigest()
            path_hash = hashlib.sha256(target).hexdigest()
            self.assertEqual(reader.pinned_blob(rev, tree, path_hash, oid, digest_bytes(content)), content)
            non_utf8_path = b"odd\nname\t\xff.txt"
            non_utf8_listing = b"100644 blob " + oid.encode("ascii") + b"\t" + non_utf8_path + b"\x00"
            self.assertEqual(_select_tree_entry(non_utf8_listing, hashlib.sha256(non_utf8_path).hexdigest()), ("100644", "blob", oid))
            with self.assertRaises(GateError) as error:
                reader.pinned_blob(rev, tree, hashlib.sha256(b"missing.txt").hexdigest(), oid, digest_bytes(content))
            self.assertEqual(error.exception.reason, "planning_path_missing")
            with self.assertRaises(GateError) as error:
                reader.pinned_blob(rev, "0" * 40, path_hash, oid, digest_bytes(content))
            self.assertEqual(error.exception.reason, "planning_tree_mismatch")

    def test_raw_tree_parser_refuses_malformed_duplicate_and_ambiguous_entries(self) -> None:
        path = b"raw-name"
        oid = b"a" * 40
        digest = hashlib.sha256(path).hexdigest()
        good = b"100644 blob " + oid + b"\t" + path + b"\x00"
        self.assertEqual(_select_tree_entry(good, digest), ("100644", "blob", oid.decode("ascii")))
        for malformed in (b"", good[:-1], good + b"\x00", b"100755 tree " + oid + b"\t" + path + b"\x00"):
            with self.subTest(listing=malformed[:40]), self.assertRaises(GateError):
                _select_tree_entry(malformed, digest)
        duplicate = good + good
        with self.assertRaises(GateError) as error:
            _select_tree_entry(duplicate, digest)
        self.assertEqual(error.exception.reason, "duplicate_planning_tree_path")
        original_digest = digest_bytes
        def colliding_hash(value: bytes) -> str:
            if value in {b"one", b"two"}:
                return digest
            return original_digest(value)
        ambiguous = b"100644 blob " + oid + b"\tone\x00" + b"100644 blob " + oid + b"\ttwo\x00"
        with mock.patch(__name__ + ".digest_bytes", side_effect=colliding_hash):
            with self.assertRaises(GateError) as error:
                _select_tree_entry(ambiguous, digest)
        self.assertEqual(error.exception.reason, "planning_path_ambiguous")

    def test_raw_diff_keeps_opaque_path_bytes_for_digest_comparisons(self) -> None:
        raw_path = b"opaque\nname\tbytes"
        record = b":100644 100644 " + b"a" * 40 + b" " + b"b" * 40 + b" M\x00" + raw_path + b"\x00"
        entry = parse_raw_nul_diff(record)[0]
        self.assertEqual(entry.path_bytes, raw_path)
        self.assertEqual(entry.path, raw_path.decode("utf-8"))
        self.assertEqual(digest_bytes(entry.path_bytes), hashlib.sha256(raw_path).hexdigest())

    def test_git_output_limit_applies_to_full_raw_tree_listing(self) -> None:
        git = Git(Path.cwd())
        oversized = subprocess.CompletedProcess(["git"], 0, b"x" * (MAX_OUTPUT_BYTES + 1), b"")
        with mock.patch(__name__ + ".subprocess.run", return_value=oversized):
            with self.assertRaises(GateError) as error:
                git.run("ls-tree", "-r", "-z", "--full-tree", PLAN_REV)
        self.assertEqual(error.exception.reason, "git_output_too_large")

    def test_d227_inherited_gate_boundary_proves_the_pinned_d226_gate_chain(self) -> None:
        real_git = Git(Path.cwd())
        expected = {"rev": D226_GATE_REV, "tree": D226_GATE_TREE, "blob": D226_GATE_BLOB, "sha256": D226_GATE_SHA256, "mode": "100644"}
        self.assertEqual(_validate_inherited_gate_boundary(real_git), expected)

        class MutatedBoundary:
            def __init__(self, fault: str) -> None:
                self.fault = fault
                self.action_calls: list[str] = []
            def __getattr__(self, name: str) -> Any:
                return getattr(real_git, name)
            def tree_entry(self, rev: str, path: str) -> tuple[str, str, str]:
                actual = real_git.tree_entry(rev, path)
                if self.fault == "parent_mode" and rev == PLAN_PARENT:
                    return "100755", "blob", D226_GATE_BLOB
                if self.fault == "parent_blob" and rev == PLAN_PARENT:
                    return "100644", "blob", "0" * 40
                if self.fault == "parent_type" and rev == PLAN_PARENT:
                    return "120000", "blob", D226_GATE_BLOB
                if self.fault == "parent_object_type" and rev == PLAN_PARENT:
                    return "100644", "tree", D226_GATE_BLOB
                if self.fault == "intermediate_blob" and rev == D226_STOP_INTERMEDIATE:
                    return "100644", "blob", D225_GATE_BLOB
                return actual
            def blob(self, rev: str, path: str) -> bytes:
                if self.fault == "baseline_content" and rev == D226_GATE_REV and path == GATE_PATH:
                    return b"substituted gate content"
                return real_git.blob(rev, path)
            def parents(self, rev: str) -> list[str]:
                if self.fault == "root" and rev == PLAN_REV:
                    return []
                if self.fault == "merge" and rev == PLAN_REV:
                    return [PLAN_PARENT, D226_GATE_REV]
                if self.fault == "wrong_stop_parent" and rev == D226_STOP_CANDIDATE:
                    return [D226_GATE_REV]
                return real_git.parents(rev)
            def raw_diff(self, before: str, after: str) -> list[DiffEntry]:
                if self.fault in {"history_diff", "history_add", "history_delete", "history_type", "history_rename"} and (before, after) == (D226_GATE_REV, D226_STOP_INTERMEDIATE):
                    if self.fault == "history_diff":
                        return [DiffEntry("100644", "100644", D226_GATE_BLOB, D226_GATE_BLOB, "M", GATE_PATH)]
                    if self.fault == "history_add":
                        return [DiffEntry("000000", "100644", "0" * 40, D226_GATE_BLOB, "A", GATE_PATH)]
                    if self.fault == "history_delete":
                        return [DiffEntry("100644", "000000", D226_GATE_BLOB, "0" * 40, "D", GATE_PATH)]
                    if self.fault == "history_type":
                        return [DiffEntry("100644", "120000", D226_GATE_BLOB, "0" * 40, "T", GATE_PATH)]
                    return [
                        DiffEntry("100644", "000000", D226_GATE_BLOB, "0" * 40, "D", GATE_PATH),
                        DiffEntry("000000", "100644", "0" * 40, "3" * 40, "A", "renamed-gate.py"),
                    ]
                if self.fault == "d225_transition" and (before, after) == (D225_PLAN_REV, D225_GATE_REV):
                    return [DiffEntry("100644", "100644", D224_GATE_BLOB, "4" * 40, "M", GATE_PATH)]
                if self.fault == "d226_transition" and (before, after) == (D226_PLAN_REV, D226_GATE_REV):
                    return [DiffEntry("100644", "100644", D225_GATE_BLOB, "4" * 40, "M", GATE_PATH)]
                if self.fault == "plan_diff" and (before, after) == (PLAN_PARENT, PLAN_REV):
                    return [DiffEntry("100644", "100644", D226_GATE_BLOB, D226_GATE_BLOB, "M", GATE_PATH)]
                if self.fault == "malformed_diff" and (before, after) == (PLAN_PARENT, PLAN_REV):
                    deny("malformed_raw_diff")
                return real_git.raw_diff(before, after)

        for fault in ("parent_mode", "parent_blob", "parent_type", "parent_object_type", "intermediate_blob", "baseline_content", "history_diff", "history_add", "history_delete", "history_type", "history_rename", "d225_transition", "d226_transition", "plan_diff", "malformed_diff", "root", "merge", "wrong_stop_parent"):
            with self.subTest(fault=fault):
                mutated = MutatedBoundary(fault)
                with self.assertRaises(GateError):
                    _validate_inherited_gate_boundary(mutated)
                self.assertEqual(mutated.action_calls, [])

    def test_d227_gate_only_diff_requires_exact_old_to_new_regular_file_modification(self) -> None:
        exact = DiffEntry("100644", "100644", D226_GATE_BLOB, "a" * 40, "M", GATE_PATH)
        self.assertEqual(_validate_gate_replacement_diff([exact]), exact.new_oid)
        rejected = (
            [DiffEntry("000000", "100644", "0" * 40, exact.new_oid, "A", GATE_PATH)],
            [DiffEntry("100644", "000000", D226_GATE_BLOB, "0" * 40, "D", GATE_PATH)],
            [DiffEntry("100644", "100644", D226_GATE_BLOB, exact.new_oid, "T", GATE_PATH)],
            [DiffEntry("100755", "100644", D226_GATE_BLOB, exact.new_oid, "M", GATE_PATH)],
            [DiffEntry("100644", "100755", D226_GATE_BLOB, exact.new_oid, "M", GATE_PATH)],
            [DiffEntry("100644", "100644", "0" * 40, exact.new_oid, "M", GATE_PATH)],
            [exact, DiffEntry("100644", "100644", "1" * 40, "2" * 40, "M", "extra.txt")],
        )
        for entries in rejected:
            with self.subTest(entries=entries):
                with self.assertRaises(GateError):
                    _validate_gate_replacement_diff(entries)
        with self.assertRaises(GateError):
            _validate_gate_replacement_diff([])
        with self.assertRaises(GateError):
            _validate_gate_replacement_diff([
                DiffEntry("100644", "000000", D226_GATE_BLOB, "0" * 40, "D", GATE_PATH),
                DiffEntry("000000", "100644", "0" * 40, "3" * 40, "A", "renamed-gate.py"),
            ])

    def test_git_adapter_ignores_replacement_refs_for_original_object_reads(self) -> None:
        with tempfile.TemporaryDirectory(prefix="phase24-replace-ref-") as temp:
            root = Path(temp)
            env = source_git_env()
            env.pop("GIT_NO_REPLACE_OBJECTS", None)
            def run(*args: str) -> bytes:
                result = subprocess.run(["git", "-C", str(root), *args], env=env, capture_output=True, check=True, timeout=15)
                return result.stdout
            run("init", "--quiet")
            run("config", "user.name", "Phase 24 test")
            run("config", "user.email", "phase24-test@example.invalid")
            target = root / "gate.py"
            target.write_bytes(b"original pinned bytes\n")
            run("add", "gate.py")
            run("commit", "--quiet", "-m", "original")
            original = run("rev-parse", "HEAD").decode("ascii").strip()
            target.write_bytes(b"replacement object bytes\n")
            run("commit", "--quiet", "-am", "replacement")
            replacement = run("rev-parse", "HEAD").decode("ascii").strip()
            run("replace", original, replacement)
            self.assertEqual(run("show", f"{original}:gate.py"), b"replacement object bytes\n")
            reader = Git(root)
            self.assertEqual(reader.blob(original, "gate.py"), b"original pinned bytes\n")
            original_tree = reader.tree(original)
            original_bytes = b"original pinned bytes\n"
            original_oid = hashlib.sha1(b"blob " + str(len(original_bytes)).encode("ascii") + b"\x00" + original_bytes).hexdigest()
            self.assertEqual(reader.pinned_blob(original, original_tree, hashlib.sha256(b"gate.py").hexdigest(), original_oid, digest_bytes(b"original pinned bytes\n")), b"original pinned bytes\n")
            self.assertNotEqual(reader.tree(original), run("rev-parse", f"{original}^{{tree}}").decode("ascii").strip())
            changed = reader.raw_diff(original, replacement)
        self.assertEqual([(entry.path_bytes, entry.status) for entry in changed], [(b"gate.py", "M")])

    def test_executing_module_is_registered_before_test_patching(self) -> None:
        current_module = sys.modules.get(__name__)
        self.assertTrue(current_module is not None, "executing gate module must be registered before exec")
        self.assertTrue(current_module.__dict__ is globals(), "module registration must own the executing globals")
        with mock.patch(__name__ + "._verify_origin") as patched:
            self.assertIs(sys.modules[__name__]._verify_origin, patched)

    def test_immutable_source_uses_registered_bytes_without_opening_candidate_copy(self) -> None:
        module_name = "_phase24_immutable_source_control"
        module = types.ModuleType(module_name)
        module.__file__ = "<immutable-phase24-gate>"
        module.__phase24_gate_bytes__ = b"original pinned source bytes"
        sys.modules[module_name] = module
        try:
            with mock.patch.object(Path, "read_bytes", side_effect=AssertionError("candidate source read")):
                self.assertEqual(_registered_module_bytes(module_name, module.__dict__), b"original pinned source bytes")
            candidate_namespace = {"__phase24_gate_bytes__": b"candidate checkout bytes"}
            with self.assertRaises(GateError):
                _registered_module_bytes(module_name, candidate_namespace)
            del module.__phase24_gate_bytes__
            with self.assertRaises(GateError):
                _registered_module_bytes(module_name, module.__dict__)
        finally:
            sys.modules.pop(module_name, None)

    def _run_live_fixture(self, action: str, candidate_number: int = 1, fault: str | None = None) -> tuple[dict[str, Any] | None, GateError | None, _RecordingRunner]:
        root = Path.cwd().resolve()
        first_sha, first_tree = "a" * 40, "b" * 40
        candidate_sha = first_sha if candidate_number == 1 else "d" * 40
        candidate_tree = first_tree if candidate_number == 1 else "e" * 40
        base_sha = "f" * 40
        branch = "phase24-candidate"
        candidate = {"sha": candidate_sha, "tree": candidate_tree, "paths": [EXPECTED_CANDIDATE_CORRECTIONS[0]]}
        history_obj = _test_genesis_history()
        history_records = [dict(item) for item in history_obj["records"]]
        cause: dict[str, Any] | None = None
        if candidate_number == 2:
            first_action = "1" * 32
            run_id, attempt, context = "44199999999", 1, "required-native"
            _append_hash_record(history_records, kind="reservation", candidate_sha=first_sha, candidate_tree=first_tree, action_id=first_action, outcome="ALLOW")
            _append_hash_record(history_records, kind="push_result", candidate_sha=first_sha, candidate_tree=first_tree, action_id=first_action, outcome="pushed")
            _append_hash_record(history_records, kind="matrix_result", candidate_sha=first_sha, candidate_tree=first_tree, action_id=first_action, outcome="failed", run_id=run_id, run_attempt=attempt, context=context, in_scope=True, causal_fix_paths=[EXPECTED_CANDIDATE_CORRECTIONS[0]])
            cause = {"previous_candidate_sha": first_sha, "matrix_run_id": run_id, "run_attempt": attempt, "failed_context": context, "causal_fix_paths": [EXPECTED_CANDIDATE_CORRECTIONS[0]], "failure_contract": "required-native exposed a deterministic causal failure"}
        elif action == "merge":
            action_id = "1" * 32
            _append_hash_record(history_records, kind="reservation", candidate_sha=candidate_sha, candidate_tree=candidate_tree, action_id=action_id, outcome="ALLOW")
            _append_hash_record(history_records, kind="push_result", candidate_sha=candidate_sha, candidate_tree=candidate_tree, action_id=action_id, outcome="pushed")
            _append_hash_record(history_records, kind="matrix_result", candidate_sha=candidate_sha, candidate_tree=candidate_tree, action_id=action_id, outcome="passed", run_id="44199999991", run_attempt=1, context=None, in_scope=False)
        history = _validate_history({"schema_version": 1, "kind": "phase24-d222-history", "records": history_records, "head": history_records[-1]["digest"]})
        remote_head = first_sha if candidate_number == 2 else (candidate_sha if action == "merge" else "c" * 40)
        protection = _test_protection()
        if fault == "protection_mutated":
            protection["allow_force_pushes"]["enabled"] = True
        protection_digest = digest_bytes(canonical_json(protection))
        manifest = {
            "candidate_sha": candidate_sha, "candidate_tree": candidate_tree, "causal_resolution": cause,
            "receipts": {"history": "build/phase24/history.json"}, "_receipt_raw": {"history": b"{}"},
            "expected_remote": {"repository": EXPECTED_REPO, "pull_request": EXPECTED_PR, "head_branch": branch,
                "prior_head_sha": candidate_sha if action == "merge" else remote_head, "base_sha": base_sha,
                "protection_sha256": protection_digest},
        }
        pr_initial = {
            "number": EXPECTED_PR, "state": "open", "draft": False,
            "head": {"sha": remote_head, "ref": branch, "repo": {"full_name": EXPECTED_REPO}},
            "base": {"sha": base_sha, "ref": EXPECTED_BASE, "repo": {"full_name": EXPECTED_REPO}},
        }
        if fault == "pr_stale":
            pr_initial["head"]["sha"] = "9" * 40
        if action == "merge":
            merge_sha = "9" * 40
            pr_after = {"number": EXPECTED_PR, "merged": True, "state": "closed", "merge_commit_sha": merge_sha,
                "head": {"sha": candidate_sha}, "base": {"ref": EXPECTED_BASE}}
        else:
            pr_after = {"state": "open", "draft": False,
                "head": {"sha": candidate_sha, "ref": branch},
                "base": {"sha": base_sha, "ref": EXPECTED_BASE}}
        responses: dict[str, Any] = {
            f"repos/{EXPECTED_REPO}": {"full_name": EXPECTED_REPO, "permissions": {"pull": True, "push": True}},
            f"repos/{EXPECTED_REPO}/pulls/{EXPECTED_PR}": [pr_initial, pr_after],
            f"repos/{EXPECTED_REPO}/branches/{EXPECTED_BASE}/protection": protection,
        }
        if candidate_number == 2:
            causal = _fake_causal_failure_responses(cause["matrix_run_id"], cause["run_attempt"], first_sha, branch, cause["failed_context"])
            if fault == "causal_attempt":
                causal[f"repos/{EXPECTED_REPO}/actions/runs/{cause['matrix_run_id']}"]["run_attempt"] += 1
            if fault == "causal_suite_mismatch":
                run_list_key = f"repos/{EXPECTED_REPO}/actions/runs?head_sha={first_sha}&per_page=100"
                causal[run_list_key]["workflow_runs"][0]["check_suite_id"] += 999
            if fault == "causal_app_mismatch":
                check_key = f"repos/{EXPECTED_REPO}/commits/{first_sha}/check-runs?filter=latest&per_page=100"
                causal[check_key]["check_runs"][0]["app"]["id"] = 99999
            if fault == "causal_wrong_workflow_path":
                run_list_key = f"repos/{EXPECTED_REPO}/actions/runs?head_sha={first_sha}&per_page=100"
                causal[run_list_key]["workflow_runs"][0]["path"] = ".github/workflows/unexpected.yml"
            if fault == "causal_repeated_attempt":
                run_list_key = f"repos/{EXPECTED_REPO}/actions/runs?head_sha={first_sha}&per_page=100"
                repeated = dict(causal[run_list_key]["workflow_runs"][0])
                repeated["id"] += 5000
                repeated["run_attempt"] += 1
                causal[run_list_key]["workflow_runs"].append(repeated)
                causal[run_list_key]["total_count"] += 1
            if fault == "causal_attempt_two":
                run_list_key = f"repos/{EXPECTED_REPO}/actions/runs?head_sha={first_sha}&per_page=100"
                failed_run = next(row for row in causal[run_list_key]["workflow_runs"] if row["id"] == int(cause["matrix_run_id"]))
                failed_run["run_attempt"] = 2
            if fault == "causal_job_missing":
                causal.pop(f"repos/{EXPECTED_REPO}/actions/runs/{cause['matrix_run_id']}/jobs?filter=latest&per_page=100")
            responses.update(causal)
        if action == "merge":
            status_sha = "9" * 40 if fault == "matrix_fail" else candidate_sha
            responses.update(_fake_success_responses(status_sha, candidate_tree, branch))
            if fault == "check_app_mismatch":
                check_key = f"repos/{EXPECTED_REPO}/commits/{status_sha}/check-runs?filter=latest&per_page=100"
                responses[check_key]["check_runs"][0]["app"]["id"] = 99999
            if fault == "wrong_workflow_path":
                run_key = f"repos/{EXPECTED_REPO}/actions/runs?head_sha={status_sha}&per_page=100"
                responses[run_key]["workflow_runs"][0]["path"] = ".github/workflows/unexpected.yml"
            if fault == "matrix_fail":
                bad_statuses = responses[f"repos/{EXPECTED_REPO}/commits/{status_sha}/status"]["statuses"]
                bad_statuses[0]["state"] = "failure"
            responses[f"repos/{EXPECTED_REPO}/commits/{merge_sha}"] = {"sha": merge_sha, "tree": {"sha": candidate_tree}, "parents": [{"sha": candidate_sha}]}
            responses[f"repos/{EXPECTED_REPO}/commits/{EXPECTED_BASE}"] = {"sha": merge_sha}
        runner = _RecordingRunner(responses, auth_ready=(fault != "auth_missing"))
        bootstrap_receipt = {"schema_version": 1, "kind": "phase24-d227-bootstrap", "plan": {}, "discussion": {}, "closeout": {}, "loader": {}, "inherited_gate": {}, "gate": {}, "repository": {}, "scope": {}, "history_pins": {}, "trusted_handoff": {}}
        args = argparse.Namespace(bootstrap="build/phase24/test-bootstrap.json", candidate=candidate_sha, evidence="build/phase24/test-manifest.json", mode=action)
        action_log: list[str] = []

        def append_action(path: Path, records: list[dict[str, Any]], *, kind: str, candidate: Mapping[str, Any], action_id: str, outcome: str, **kwargs: Any) -> list[dict[str, Any]]:
            action_log.append(kind)
            _append_hash_record(records, kind=kind, candidate_sha=candidate["sha"], candidate_tree=candidate["tree"], action_id=action_id, outcome=outcome,
                run_id=kwargs.get("run_id"), run_attempt=kwargs.get("run_attempt"), context=kwargs.get("context"), in_scope=kwargs.get("in_scope", False),
                causal_fix_paths=kwargs.get("causal_fix_paths", ()), remote_head_sha=kwargs.get("remote_head_sha"), base_sha=kwargs.get("base_sha"), branch=kwargs.get("branch"))
            return records

        loader_patch = mock.patch.multiple(__name__, _verify_origin=mock.DEFAULT, _check_ignored=mock.DEFAULT,
            _load_receipt=mock.DEFAULT, _verify_bootstrap_source=mock.DEFAULT, _load_manifest=mock.DEFAULT,
            _load_history_file=mock.DEFAULT, _history_record_action=mock.DEFAULT)
        with loader_patch as patched, mock.patch.dict(os.environ, {"PATH": os.environ.get("PATH", "/usr/bin"), "HOME": "/tmp"}, clear=True), \
                mock.patch(__name__ + ".reject_hostile_git_environment"), mock.patch(__name__ + "._candidate_contains", return_value=True):
            patched["_load_receipt"].return_value = (root / "build/phase24/test-bootstrap.json", bootstrap_receipt, canonical_json(bootstrap_receipt))
            patched["_verify_bootstrap_source"].return_value = {"gate": {"sha256": "0" * 64}}
            patched["_load_manifest"].return_value = (manifest, candidate, {}, {})
            patched["_load_history_file"].return_value = (root / "build/phase24/history.json", history)
            patched["_history_record_action"].side_effect = append_action
            try:
                result = _run_live(root, args, runner=runner)
                return result, None, runner
            except GateError as exc:
                return None, exc, runner

    def test_run_live_production_path_dispatches_one_fixed_action_for_each_allow(self) -> None:
        for action, candidate_number in (("push", 1), ("merge", 1), ("push", 2)):
            with self.subTest(action=action, candidate_number=candidate_number):
                result, error, runner = self._run_live_fixture(action, candidate_number)
                self.assertIsNone(error)
                self.assertIsNotNone(result)
                self.assertEqual(len(runner.action_calls), 1)
                expected = fixed_push_argv(("a" if candidate_number == 1 else "d") * 40, "phase24-candidate") if action == "push" else fixed_merge_argv("a" * 40)
                self.assertEqual(runner.action_calls, [expected])

    def test_run_live_production_path_denies_mutated_inputs_before_action(self) -> None:
        cases = (("push", 1, "auth_missing"), ("push", 1, "pr_stale"), ("push", 1, "protection_mutated"),
            ("push", 2, "causal_attempt"), ("push", 2, "causal_job_missing"), ("push", 2, "causal_suite_mismatch"),
            ("push", 2, "causal_repeated_attempt"), ("push", 2, "causal_app_mismatch"), ("push", 2, "causal_attempt_two"),
            ("push", 2, "causal_wrong_workflow_path"), ("merge", 1, "matrix_fail"),
            ("merge", 1, "check_app_mismatch"), ("merge", 1, "wrong_workflow_path"))
        for action, candidate_number, fault in cases:
            with self.subTest(action=action, candidate_number=candidate_number, fault=fault):
                result, error, runner = self._run_live_fixture(action, candidate_number, fault)
                self.assertIsNone(result)
                self.assertIsNotNone(error)
                self.assertEqual(runner.action_calls, [])

    def test_manifest_and_all_receipts_require_trusted_raw_digests(self) -> None:
        body = canonical_json({"schema_version": 1}) + b"\n"
        with self.assertRaises(GateError):
            _require_manifest_digest(body, None)
        with self.assertRaises(GateError):
            _require_manifest_digest(body, "0" * 64)
        _require_manifest_digest(body, digest_bytes(body))
        bodies = {key: canonical_json({"key": key}) for key in MANIFEST_RECEIPT_KEYS}
        refs = _test_manifest_receipt_refs(bodies)
        reads: list[str] = []
        paths, verified = _bind_receipt_refs(refs, lambda path: (reads.append(path), bodies[Path(path).stem])[1])
        self.assertEqual(set(paths), MANIFEST_RECEIPT_KEYS)
        self.assertEqual(set(verified), MANIFEST_RECEIPT_KEYS)
        self.assertEqual(len(reads), len(MANIFEST_RECEIPT_KEYS))
        bad = dict(refs)
        bad["security_review"] = {**refs["security_review"], "sha256": "0" * 64}
        with self.assertRaises(GateError):
            _bind_receipt_refs(bad, lambda path: bodies[Path(path).stem])
        missing = dict(refs)
        missing["history"] = {"path": refs["history"]["path"]}
        with self.assertRaises(GateError):
            _bind_receipt_refs(missing, lambda path: bodies[Path(path).stem])

    def test_direct_receipts_and_test_actual_counts_are_exact(self) -> None:
        candidate_sha, gate_rev, gate_sha = "a" * 40, "b" * 40, "c" * 64
        with tempfile.TemporaryDirectory(prefix="phase24-direct-") as temp:
            root = Path(temp)
            for name in DIRECT_CONTROL_NAMES:
                sample = DIRECT_CONTROL_SAMPLE_OUTPUT[name].format(gate_sha256=gate_sha)
                output = (sample + "\n").encode()
                relative = f"build/phase24/{name}.txt"
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(output)
                receipt = {
                    "name": name,
                    "command": _expected_direct_control_command(name, candidate_sha, gate_rev, gate_sha, sys.executable),
                    "transcript_path": relative,
                    "transcript_sha256": digest_bytes(output),
                    "exit_code": 0,
                    "markers": [DIRECT_CONTROL_MARKERS[name]],
                }
                self.assertEqual(_validate_direct_control(root, receipt, name, candidate_sha, gate_rev, gate_sha, sys.executable), relative)
                bad_marker = dict(receipt, markers=["PASS"])
                with self.assertRaises(GateError):
                    _validate_direct_control(root, bad_marker, name, candidate_sha, gate_rev, gate_sha, sys.executable)
                bad_command = dict(receipt, command=list(receipt["command"]) + ["--unexpected"])
                with self.assertRaises(GateError):
                    _validate_direct_control(root, bad_command, name, candidate_sha, gate_rev, gate_sha, sys.executable)
                if name == "promotion_coverage_controls":
                    marker_path = root / relative
                    wrong_output = f"PASS: phase24-promotion-controls gate={'d' * 64} controls=12\n".encode()
                    marker_path.write_bytes(wrong_output)
                    wrong_digest = dict(receipt, transcript_sha256=digest_bytes(wrong_output))
                    with self.assertRaises(GateError) as error:
                        _validate_direct_control(root, wrong_digest, name, candidate_sha, gate_rev, gate_sha, sys.executable)
                    self.assertEqual(error.exception.reason, "qualification_direct_marker_gate_mismatch")

                    for invalid_output in (
                        b"phase24-promotion-controls pass gate=" + (gate_sha.encode()) + b" controls=12\n",
                        b"no producer marker\n",
                        (sample + "\n" + sample + "\n").encode(),
                    ):
                        marker_path.write_bytes(invalid_output)
                        invalid_receipt = dict(receipt, transcript_sha256=digest_bytes(invalid_output))
                        with self.assertRaises(GateError):
                            _validate_direct_control(root, invalid_receipt, name, candidate_sha, gate_rev, gate_sha, sys.executable)

                    marker_path.write_bytes(output)
                    nonzero = dict(receipt, exit_code=1)
                    with self.assertRaises(GateError):
                        _validate_direct_control(root, nonzero, name, candidate_sha, gate_rev, gate_sha, sys.executable)
                    missing = dict(receipt, transcript_path="build/phase24/missing-promotion-marker.txt")
                    with self.assertRaises(GateError):
                        _validate_direct_control(root, missing, name, candidate_sha, gate_rev, gate_sha, sys.executable)

            name = "plan_cap"
            relative = f"build/phase24/{name}-actual.txt"
            body = (TEST_PASS_SAMPLE_OUTPUT[name] + "\n").encode()
            (root / relative).write_bytes(body)
            result = {
                "name": name, "command": _expected_ctest_argv(name), "interpreter": sys.executable,
                "transcript_path": relative, "transcript_sha256": digest_bytes(body), "exit_code": 0,
                "markers": [TEST_PASS_PATTERNS[name]], "actual": TEST_FLOORS[name], "floor": TEST_FLOORS[name],
                "elapsed_seconds": 0.1, "deadline_seconds": TEST_DEADLINES[name], "processors": TEST_PROCESSORS[name],
            }
            _validate_test_result(root, result, sys.executable, candidate_sha)
            result["actual"] = float(TEST_FLOORS[name])
            with self.assertRaises(GateError):
                _validate_test_result(root, result, sys.executable, candidate_sha)

    def test_configured_python_comes_from_unique_cmake_cache_entry(self) -> None:
        with tempfile.TemporaryDirectory(prefix="phase24-cmake-cache-") as temp:
            root = Path(temp)
            cache = root / "build/CMakeCache.txt"
            cache.parent.mkdir()
            cache.write_text(f"Python3_EXECUTABLE:UNINITIALIZED={sys.executable}\n", encoding="utf-8")
            self.assertEqual(_configured_python(root), sys.executable)
            cache.write_text(f"Python3_EXECUTABLE:UNINITIALIZED={sys.executable}\nPython3_EXECUTABLE:FILEPATH={sys.executable}\n", encoding="utf-8")
            with self.assertRaises(GateError):
                _configured_python(root)
            cache.write_text("Python3_EXECUTABLE:UNINITIALIZED=/missing/configured/python\n", encoding="utf-8")
            with self.assertRaises(GateError):
                _configured_python(root)
            cache.write_text("Python3_EXECUTABLE:UNINITIALIZED=relative/python\n", encoding="utf-8")
            with self.assertRaises(GateError):
                _configured_python(root)

    def test_strict_manifest_receipts_and_candidate_scope_run_before_actions(self) -> None:
        candidate_sha, candidate_tree = "a" * 40, "b" * 40
        gate_rev, gate_tree = "c" * 40, "d" * 40
        gate_bytes = executing_source_bytes()
        gate_blob = hashlib.sha1(b"blob " + str(len(gate_bytes)).encode("ascii") + b"\0" + gate_bytes).hexdigest()
        gate_sha = digest_bytes(gate_bytes)
        plan_bytes = Git(Path.cwd()).pinned_blob(PLAN_REV, PLAN_TREE, PLAN_PATH_SHA256, PLAN_BLOB, PLAN_SHA256)
        discussion_bytes = Git(Path.cwd()).pinned_blob(DISCUSSION_REV, DISCUSSION_TREE, DISCUSSION_PATH_SHA256, DISCUSSION_BLOB, DISCUSSION_SHA256)
        closeout_bytes = Git(Path.cwd()).pinned_blob(CLOSEOUT_REV, CLOSEOUT_TREE, CLOSEOUT_PATH_SHA256, CLOSEOUT_BLOB, CLOSEOUT_SHA256)
        source_git = Git(Path.cwd())
        d224_gate_bytes = Git(Path.cwd()).blob(D224_GATE_REV, GATE_PATH)
        d225_gate_bytes = Git(Path.cwd()).blob(D225_GATE_REV, GATE_PATH)
        d226_gate_bytes = Git(Path.cwd()).blob(D226_GATE_REV, GATE_PATH)
        loader_sha256 = digest_bytes(extract_plan_loader(plan_bytes))
        with tempfile.TemporaryDirectory(prefix="phase24-manifest-") as temp:
            root = Path(temp).resolve()
            (root / "build/phase24").mkdir(parents=True)
            (root / "build/CMakeCache.txt").write_text(f"Python3_EXECUTABLE:UNINITIALIZED={sys.executable}\n", encoding="utf-8")
            class FixtureGit:
                def __init__(self) -> None:
                    self.root = root
                    self.plan_gate_changed = False
                    self.gate_parent_override: list[str] | None = None
                    self.anchor_fault: str | None = None
                    self.replacement_diff = [DiffEntry("100644", "100644", D226_GATE_BLOB, gate_blob, "M", GATE_PATH)]
                def run_result(self, *args: str, **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
                    if args[:2] == ("check-ignore", "--quiet") or args[:3] == ("diff", "--cached", "--quiet"):
                        return subprocess.CompletedProcess(list(args), 0, b"", b"")
                    if args[:1] == ("status",):
                        return subprocess.CompletedProcess(list(args), 0, b"", b"")
                    if args[:3] == ("config", "--local", "--get-all"):
                        values = {"remote.origin.url": [EXPECTED_URL], "remote.origin.pushurl": []}.get(args[-1], [])
                        if not values:
                            return subprocess.CompletedProcess(list(args), 1, b"", b"")
                        return subprocess.CompletedProcess(list(args), 0, ("\n".join(values) + "\n").encode(), b"")
                    if args[:2] == ("remote", "get-url"):
                        return subprocess.CompletedProcess(list(args), 0, (EXPECTED_URL + "\n").encode(), b"")
                    return subprocess.CompletedProcess(list(args), 1, b"", b"")
                def run(self, *args: str, **kwargs: Any) -> bytes:
                    result = self.run_result(*args, **kwargs)
                    if result.returncode:
                        deny("fixture_git_read")
                    return result.stdout
                def text(self, *args: str, **kwargs: Any) -> str:
                    if args == ("rev-parse", "--show-toplevel"):
                        return str(root)
                    if args == ("rev-parse", "--absolute-git-dir"):
                        return str(root / ".git")
                    if args == ("symbolic-ref", "--quiet", "--short", "HEAD"):
                        return "gsd/phase-24-fixture"
                    if args == ("rev-parse", "HEAD"):
                        return candidate_sha
                    if args == ("rev-parse", "--verify", candidate_sha):
                        return candidate_sha
                    if args == ("rev-parse", f"{candidate_sha}:{GATE_PATH}"):
                        return gate_blob
                    if args == ("rev-parse", f"{gate_rev}:{GATE_PATH}"):
                        return gate_blob
                    if args == ("rev-parse", f"{D224_GATE_REV}:{GATE_PATH}") or args == ("rev-parse", f"{D225_PLAN_REV}:{GATE_PATH}"):
                        return D224_GATE_BLOB
                    if args == ("rev-parse", f"{D225_GATE_REV}:{GATE_PATH}") or args == ("rev-parse", f"{D225_STOP_CANDIDATE}:{GATE_PATH}") or args == ("rev-parse", f"{D226_PLAN_REV}:{GATE_PATH}"):
                        return D225_GATE_BLOB
                    if args == ("rev-parse", f"{D226_GATE_REV}:{GATE_PATH}") or args == ("rev-parse", f"{D226_STOP_INTERMEDIATE}:{GATE_PATH}") or args == ("rev-parse", f"{D226_STOP_CANDIDATE}:{GATE_PATH}") or args == ("rev-parse", f"{PLAN_PARENT}:{GATE_PATH}") or args == ("rev-parse", f"{PLAN_REV}:{GATE_PATH}"):
                        return D226_GATE_BLOB
                    if len(args) == 2 and args[0] == "rev-parse" and ":" in args[1]:
                        rev, path = args[1].split(":", 1)
                        if path in HISTORICAL_PATHS:
                            return HISTORICAL_PATHS[path]
                        if path in PLAN_SOURCE_PATHS:
                            if path == GATE_PATH:
                                return gate_blob
                            return hashlib.sha1(path.encode()).hexdigest()
                        if path == ".planning/milestones/v0.4-REQUIREMENTS.md":
                            return REQUIREMENTS_BLOB
                        if path == ".planning/milestones/v0.4-ROADMAP.md":
                            return ROADMAP_BLOB
                    deny("fixture_git_text", repr(args))
                def object_type(self, rev: str) -> str:
                    return "commit"
                def exists(self, *args: str) -> bool:
                    return args[-1] == f"{DISCUSSION_REV}:{GATE_PATH}"
                def tree(self, rev: str) -> str:
                    if self.anchor_fault == "source_parent_tree" and rev == SOURCE_PARENT:
                        return "0" * 40
                    return {candidate_sha: candidate_tree, PLAN_REV: PLAN_TREE, DISCUSSION_REV: DISCUSSION_TREE, D225_PLAN_REV: D225_PLAN_TREE, D225_GATE_REV: D225_GATE_TREE, D225_STOP_CANDIDATE: D225_STOP_TREE, D226_PLAN_REV: D226_PLAN_TREE, D226_GATE_REV: D226_GATE_TREE, D226_STOP_INTERMEDIATE: D226_STOP_INTERMEDIATE_TREE, D226_STOP_CANDIDATE: D226_STOP_TREE, D224_GATE_REV: D224_GATE_TREE, gate_rev: gate_tree, D221_SHA: D221_TREE, SOURCE_PARENT: SOURCE_TREE}.get(rev, D221_TREE)
                def parents(self, rev: str) -> list[str]:
                    if rev in {PLAN_REV, DISCUSSION_REV}:
                        return [PLAN_PARENT]
                    if rev == gate_rev:
                        return [PLAN_REV] if self.gate_parent_override is None else list(self.gate_parent_override)
                    if rev == D225_PLAN_REV:
                        return [SOURCE_PARENT]
                    if rev == D225_GATE_REV:
                        return [D225_GATE_PARENT]
                    if rev == D225_STOP_CANDIDATE:
                        return [D225_GATE_REV]
                    if rev == D226_PLAN_REV:
                        return [D226_PLAN_PARENT]
                    if rev == D226_GATE_REV:
                        return [D226_GATE_PARENT]
                    if rev == D226_STOP_INTERMEDIATE:
                        return [D226_GATE_REV]
                    if rev == D226_STOP_CANDIDATE:
                        return [D226_STOP_PARENT]
                    if rev == D224_GATE_REV:
                        return [D224_GATE_PARENT]
                    return []
                def is_ancestor(self, ancestor: str, descendant: str) -> bool:
                    return True
                def blob(self, rev: str, path: str) -> bytes:
                    if rev == D224_GATE_REV and path == GATE_PATH:
                        return d224_gate_bytes
                    if rev == D225_GATE_REV and path == GATE_PATH:
                        return d225_gate_bytes
                    if rev == D226_GATE_REV and path == GATE_PATH:
                        return d226_gate_bytes
                    if rev == gate_rev and path == GATE_PATH:
                        return gate_bytes
                    if path == "tests/scripts/verify-planning-hygiene.py":
                        return (Path.cwd() / path).read_bytes()
                    deny("fixture_git_blob", path)
                def pinned_blob(self, rev: str, tree: str, path_sha256: str, oid: str, sha256: str) -> bytes:
                    expected = {
                        (PLAN_REV, PLAN_TREE, PLAN_PATH_SHA256, PLAN_BLOB, PLAN_SHA256): plan_bytes,
                        (DISCUSSION_REV, DISCUSSION_TREE, DISCUSSION_PATH_SHA256, DISCUSSION_BLOB, DISCUSSION_SHA256): discussion_bytes,
                        (CLOSEOUT_REV, CLOSEOUT_TREE, CLOSEOUT_PATH_SHA256, CLOSEOUT_BLOB, CLOSEOUT_SHA256): closeout_bytes,
                    }
                    try:
                        return expected[(rev, tree, path_sha256, oid, sha256)]
                    except KeyError:
                        deny("fixture_pinned_blob_mismatch")
                def tree_entry(self, rev: str, path: str) -> tuple[str, str, str]:
                    if path == GATE_PATH:
                        if rev in {D224_GATE_REV, D225_PLAN_REV}:
                            return "100644", "blob", D224_GATE_BLOB
                        if rev in {D225_GATE_REV, D225_STOP_CANDIDATE, D226_PLAN_REV}:
                            return "100644", "blob", D225_GATE_BLOB
                        if rev in {D226_GATE_REV, D226_STOP_INTERMEDIATE, D226_STOP_CANDIDATE, PLAN_PARENT, PLAN_REV}:
                            return "100644", "blob", D226_GATE_BLOB
                        if rev in {gate_rev, candidate_sha}:
                            return "100644", "blob", gate_blob
                        deny("fixture_tree_entry_revision")
                    if path in CORRECTION_SOURCE_PINS and rev in {SOURCE_PARENT, D226_STOP_INTERMEDIATE, D226_STOP_CANDIDATE, PLAN_REV}:
                        if self.anchor_fault == "plan_correction_oid" and rev == PLAN_REV:
                            expected = CORRECTION_SOURCE_PINS[path]
                            return expected[0], expected[1], "0" * 40
                        if rev == SOURCE_PARENT:
                            return CORRECTION_SOURCE_PINS[path]
                        return D226_ROUTE_CORRECTION_PINS[path]
                    if path in PLAN_SOURCE_PATHS and rev in {PLAN_REV, D221_SHA}:
                        if self.anchor_fault == "noncorrection_drift" and rev == PLAN_REV and path == PLAN_SOURCE_PATHS[0]:
                            entry = source_git.tree_entry(D221_SHA, path)
                            return entry[0], entry[1], "0" * 40
                        return source_git.tree_entry(D221_SHA, path)
                    deny("fixture_tree_entry_path")
                def raw_diff(self, before: str, after: str) -> list[DiffEntry]:
                    correction = DiffEntry("100644", "100644", "1" * 40, "2" * 40, "M", EXPECTED_CANDIDATE_CORRECTIONS[0])
                    gate_change = self.replacement_diff
                    if before == D225_PLAN_REV and after == D225_GATE_REV:
                        return [DiffEntry("100644", "100644", D224_GATE_BLOB, D225_GATE_BLOB, "M", GATE_PATH)]
                    if before == D225_GATE_REV and after == D225_STOP_CANDIDATE:
                        return []
                    if before == D225_STOP_CANDIDATE and after == D226_PLAN_REV:
                        return []
                    if before == D226_PLAN_REV and after == D226_GATE_REV:
                        return [DiffEntry("100644", "100644", D225_GATE_BLOB, D226_GATE_BLOB, "M", GATE_PATH)]
                    if before in {D226_GATE_REV, D226_STOP_INTERMEDIATE} and after in {D226_STOP_INTERMEDIATE, D226_STOP_CANDIDATE}:
                        return []
                    if before == D226_STOP_CANDIDATE and after == PLAN_REV:
                        return gate_change if self.plan_gate_changed else []
                    if before == D224_GATE_REV and after == D225_PLAN_REV:
                        return []
                    if before == PLAN_REV and after == gate_rev:
                        return gate_change
                    if before == gate_rev:
                        return [correction]
                    if before == PLAN_REV and after == candidate_sha:
                        return [*gate_change, correction]
                    return [correction]

            test_git = FixtureGit()
            reports: dict[str, tuple[str, bytes, str]] = {}
            for role, agent, verdict in (("gsd-code-reviewer", "review-code", "CLEAN"), ("gsd-security-auditor", "review-security", "SECURED")):
                relative = f"build/phase24/{agent}.md"
                text = (f"Review role: {role}\nReviewer agent: {agent}\nReviewed commit: {candidate_sha}\nReviewed tree: {candidate_tree}\nVerdict: {verdict}\nFindings: none\n")
                data = text.encode()
                (root / relative).write_bytes(data)
                reports[role] = (relative, data, agent)
            test_rows = []
            for name in EXPECTED_TESTS:
                relative = f"build/phase24/{name}.txt"
                data = (TEST_PASS_SAMPLE_OUTPUT[name] + "\n").encode()
                (root / relative).write_bytes(data)
                floor = TEST_FLOORS[name]
                test_rows.append({
                    "name": name, "command": _expected_ctest_argv(name), "interpreter": sys.executable,
                    "transcript_path": relative, "transcript_sha256": digest_bytes(data), "exit_code": 0,
                    "markers": [TEST_PASS_PATTERNS[name]], "actual": floor, "floor": floor,
                    "elapsed_seconds": 0.1, "deadline_seconds": TEST_DEADLINES[name], "processors": TEST_PROCESSORS[name],
                })
            direct_rows = []
            for name in DIRECT_CONTROL_NAMES:
                relative = f"build/phase24/{name}.txt"
                sample = DIRECT_CONTROL_SAMPLE_OUTPUT[name].format(gate_sha256=gate_sha)
                data = (sample + "\n").encode()
                (root / relative).write_bytes(data)
                direct_rows.append({
                    "name": name,
                    "command": _expected_direct_control_command(name, candidate_sha, gate_rev, gate_sha, sys.executable),
                    "transcript_path": relative, "transcript_sha256": digest_bytes(data), "exit_code": 0,
                    "markers": [DIRECT_CONTROL_MARKERS[name]],
                })
            inventory_relative = "build/phase24/inventory.json"
            inventory_body = canonical_json({"cases": 153, "runner_cases": 0, "build_cases": 0, "configure_cases": 0}) + b"\n"
            (root / inventory_relative).write_bytes(inventory_body)
            cmake = shutil.which("cmake")
            self.assertIsNotNone(cmake)
            ctest_rows = []
            for name in EXPECTED_TESTS:
                properties: list[dict[str, Any]] = [{"name": "TIMEOUT", "value": TEST_DEADLINES[name]}]
                if TEST_PROCESSORS[name] != 1:
                    properties.append({"name": "PROCESSORS", "value": TEST_PROCESSORS[name]})
                if TEST_LABELS[name] is not None:
                    properties.append({"name": "LABELS", "value": list(TEST_LABELS[name])})
                ctest_rows.append({"name": name, "command": _expected_ctest_command(name, root, sys.executable, cmake or "", candidate_sha), "properties": properties})
            ctest_body = canonical_json({"kind": "ctestInfo", "version": {"major": 3, "minor": 29, "patch": 0}, "backtraceGraph": {}, "tests": ctest_rows}) + b"\n"
            ctest_relative = "build/phase24/ctest-inventory.json"
            (root / ctest_relative).write_bytes(ctest_body)
            qualification = {
                "schema_version": 1, "kind": "phase24-d227-qualification", "candidate_sha": candidate_sha,
                "candidate_tree": candidate_tree, "plan_rev": PLAN_REV, "gate_rev": gate_rev, "gate_sha256": gate_sha,
                "interpreter": {"path": sys.executable, "version": sys.version.split()[0], "configured_path": sys.executable},
                "tests": test_rows, "direct_controls": direct_rows,
                "inventory": {"transcript_path": inventory_relative, "transcript_sha256": digest_bytes(inventory_body), "exit_code": 0, "cases": 153, "runner_cases": 0, "build_cases": 0, "configure_cases": 0},
                "ctest_inventory": {"command": _expected_inventory_command(), "transcript_path": ctest_relative, "transcript_sha256": digest_bytes(ctest_body), "exit_code": 0, "test_count": len(EXPECTED_TESTS), "runner_cases": 0, "build_cases": 0, "configure_cases": 0},
                "fixture_effects": [],
                "source_pins": {"plan_rev": PLAN_REV, "plan_sha256": PLAN_SHA256, "plan_path_sha256": PLAN_PATH_SHA256, "discussion_rev": DISCUSSION_REV, "discussion_tree": DISCUSSION_TREE, "discussion_blob": DISCUSSION_BLOB, "discussion_sha256": DISCUSSION_SHA256, "discussion_path_sha256": DISCUSSION_PATH_SHA256, "closeout_rev": CLOSEOUT_REV, "closeout_tree": CLOSEOUT_TREE, "closeout_blob": CLOSEOUT_BLOB, "closeout_sha256": CLOSEOUT_SHA256, "closeout_path_sha256": CLOSEOUT_PATH_SHA256, "loader_sha256": loader_sha256, "d226_gate_rev": D226_GATE_REV, "d226_gate_tree": D226_GATE_TREE, "d226_gate_blob": D226_GATE_BLOB, "d226_gate_sha256": D226_GATE_SHA256, "d226_gate_mode": "100644", "d221_exec_rev": D221_EXEC_REV, "d209_rev": D209_REV, "requirements_blob": REQUIREMENTS_BLOB, "roadmap_blob": ROADMAP_BLOB, "state_forks_blob": STATE_FORKS_BLOB, "planning_hygiene_sha256": PLANNING_HYGIENE_SHA256, "gate_rev": gate_rev, "gate_sha256": gate_sha},
            }
            qualification_raw = canonical_json(qualification) + b"\n"
            qualification_path = "build/phase24/qualification.json"
            (root / qualification_path).write_bytes(qualification_raw)
            review_dispatches = []
            review_receipts: dict[str, bytes] = {}
            for key, (role, verdict) in (("code_review", ("gsd-code-reviewer", "CLEAN")), ("security_review", ("gsd-security-auditor", "SECURED"))):
                relative, report_bytes, agent = reports[role]
                receipt = {"schema_version": 1, "kind": "phase24-d222-review", "candidate_sha": candidate_sha, "candidate_tree": candidate_tree, "role": role, "reviewer_agent": agent, "verdict": verdict, "report_path": relative, "report_sha256": digest_bytes(report_bytes)}
                raw = canonical_json(receipt) + b"\n"
                review_receipts[key] = raw
                (root / f"build/phase24/{key}.json").write_bytes(raw)
                review_dispatches.append({"role": role, "reviewer_agent": agent, "candidate_sha": candidate_sha, "candidate_tree": candidate_tree, "report_path": relative, "report_sha256": digest_bytes(report_bytes), "result": verdict})
            provenance = {
                "schema_version": 1, "kind": "phase24-d222-trusted-handoff", "plan_rev": PLAN_REV, "gate_rev": gate_rev,
                "gate_sha256": gate_sha, "candidate_sha": candidate_sha, "candidate_tree": candidate_tree,
                "implementation_agent": "implementer", "review_dispatches": review_dispatches,
                "qualification_dispatch": {"candidate_sha": candidate_sha, "candidate_tree": candidate_tree, "receipt_path": qualification_path, "receipt_sha256": digest_bytes(qualification_raw), "result": "PASS", "test_names": list(EXPECTED_TESTS)},
                "expected_tests": list(EXPECTED_TESTS),
            }
            provenance_raw = canonical_json(provenance) + b"\n"
            provenance_path = "build/phase24/provenance.json"
            (root / provenance_path).write_bytes(provenance_raw)
            history_raw = canonical_json(_test_genesis_history()) + b"\n"
            history_path = "build/phase24/history.json"
            (root / history_path).write_bytes(history_raw)
            receipt_bodies = {"qualification": qualification_raw, "provenance": provenance_raw, "history": history_raw, **review_receipts}
            receipt_paths = {key: f"build/phase24/{key}.json" for key in receipt_bodies}
            manifest = {
                "schema_version": 1, "kind": "phase24-d222-candidate", "candidate_sha": candidate_sha, "candidate_tree": candidate_tree,
                "bootstrap_rev": gate_rev, "plan_rev": PLAN_REV, "plan_sha256": PLAN_SHA256, "gate_sha256": gate_sha,
                "receipts": {key: {"path": receipt_paths[key], "sha256": digest_bytes(body)} for key, body in receipt_bodies.items()},
                "expected_remote": {"repository": EXPECTED_REPO, "pull_request": EXPECTED_PR, "head_branch": "phase24-candidate", "prior_head_sha": "f" * 40, "base_sha": "9" * 40, "protection_sha256": "0" * 64},
                "causal_resolution": None,
            }
            manifest_raw = canonical_json(manifest) + b"\n"
            manifest_path = "build/phase24/manifest.json"
            (root / manifest_path).write_bytes(manifest_raw)
            bootstrap = {
                "gate": {"rev": gate_rev, "parent": PLAN_REV, "tree": gate_tree, "blob": gate_blob, "sha256": gate_sha, "old_blob": D226_GATE_BLOB, "old_mode": "100644"},
                "plan": {"rev": PLAN_REV, "parent": PLAN_PARENT, "tree": PLAN_TREE, "blob": PLAN_BLOB, "sha256": PLAN_SHA256, "path_sha256": PLAN_PATH_SHA256},
                "discussion": {"rev": DISCUSSION_REV, "tree": DISCUSSION_TREE, "blob": DISCUSSION_BLOB, "sha256": DISCUSSION_SHA256, "path_sha256": DISCUSSION_PATH_SHA256},
                "closeout": {"rev": CLOSEOUT_REV, "tree": CLOSEOUT_TREE, "blob": CLOSEOUT_BLOB, "sha256": CLOSEOUT_SHA256, "path_sha256": CLOSEOUT_PATH_SHA256},
                "loader": {"sha256": loader_sha256},
                "inherited_gate": {"rev": D226_GATE_REV, "tree": D226_GATE_TREE, "blob": D226_GATE_BLOB, "sha256": D226_GATE_SHA256, "mode": "100644"},
            }
            env = {"PHASE24_D222_EVIDENCE": manifest_path, "PHASE24_D222_EVIDENCE_SHA256": digest_bytes(manifest_raw), "PHASE24_D222_REV": candidate_sha}
            runner = _RecordingRunner()
            loaded, candidate, provenance_loaded, _ = _load_manifest(root, test_git, bootstrap, candidate_sha, manifest_path, env)
            self.assertEqual(candidate["sha"], candidate_sha)
            self.assertEqual(provenance_loaded["expected_tests"], list(EXPECTED_TESTS))
            self.assertEqual(loaded["receipts"], receipt_paths)
            self.assertEqual(runner.action_calls, [])
            wrong_repo = dict(manifest)
            wrong_repo["expected_remote"] = dict(manifest["expected_remote"], repository="attacker/example")
            wrong_repo_raw = canonical_json(wrong_repo) + b"\n"
            (root / manifest_path).write_bytes(wrong_repo_raw)
            with self.assertRaises(GateError):
                _load_manifest(root, test_git, bootstrap, candidate_sha, manifest_path, {**env, "PHASE24_D222_EVIDENCE_SHA256": digest_bytes(wrong_repo_raw)})
            self.assertEqual(runner.action_calls, [])
            (root / manifest_path).write_bytes(manifest_raw)
            with self.assertRaises(GateError):
                _load_manifest(root, test_git, bootstrap, candidate_sha, manifest_path, {**env, "PHASE24_D222_EVIDENCE_SHA256": "0" * 64})
            self.assertEqual(runner.action_calls, [])

            protection = _test_protection()
            manifest["expected_remote"].update({
                "prior_head_sha": "f" * 40,
                "base_sha": "9" * 40,
                "protection_sha256": digest_bytes(canonical_json(protection)),
            })
            manifest_raw = canonical_json(manifest) + b"\n"
            (root / manifest_path).write_bytes(manifest_raw)
            source_scope, correction_scope = parse_plan_scopes(plan_bytes)
            bootstrap_receipt = {
                "schema_version": 1, "kind": "phase24-d227-bootstrap",
                "plan": {"rev": PLAN_REV, "parent": PLAN_PARENT, "tree": PLAN_TREE, "blob": PLAN_BLOB, "sha256": PLAN_SHA256, "path_sha256": PLAN_PATH_SHA256},
                "discussion": {"rev": DISCUSSION_REV, "tree": DISCUSSION_TREE, "blob": DISCUSSION_BLOB, "sha256": DISCUSSION_SHA256, "path_sha256": DISCUSSION_PATH_SHA256},
                "closeout": {"rev": CLOSEOUT_REV, "tree": CLOSEOUT_TREE, "blob": CLOSEOUT_BLOB, "sha256": CLOSEOUT_SHA256, "path_sha256": CLOSEOUT_PATH_SHA256},
                "loader": {"sha256": loader_sha256},
                "inherited_gate": {"rev": D226_GATE_REV, "tree": D226_GATE_TREE, "blob": D226_GATE_BLOB, "sha256": D226_GATE_SHA256, "mode": "100644"},
                "gate": {"rev": gate_rev, "parent": PLAN_REV, "tree": gate_tree, "blob": gate_blob, "sha256": gate_sha, "old_blob": D226_GATE_BLOB, "old_mode": "100644"},
                "repository": {"root": str(root), "git_dir": str(root / ".git"), "branch": "gsd/phase-24-fixture"},
                "scope": {"source_allowlist": list(source_scope), "correction_allowlist": list(correction_scope)},
                "history_pins": {"d209_rev": D209_REV, "d220_candidate": D220_SHA, "d221_candidate": D221_SHA, "d221_tree": D221_TREE, "d221_exec_rev": D221_EXEC_REV, "requirements_blob": REQUIREMENTS_BLOB, "roadmap_blob": ROADMAP_BLOB, "state_forks_blob": STATE_FORKS_BLOB, "planning_hygiene_sha256": PLANNING_HYGIENE_SHA256, **D226_HISTORY_PINS},
                "trusted_handoff": {"authority": "gsd-executor", "plan_rev": PLAN_REV, "plan_sha256": PLAN_SHA256, "gate_rev": gate_rev, "gate_sha256": gate_sha},
            }
            bootstrap_path = "build/phase24/d227-bootstrap-fixture.json"
            (root / bootstrap_path).write_bytes(canonical_json(bootstrap_receipt) + b"\n")
            bootstrap_env = {
                "PHASE24_D222_PLAN_REV": PLAN_REV,
                "PHASE24_D222_PLAN_SHA256": PLAN_SHA256,
                "PHASE24_D222_GATE_REV": gate_rev,
                "PHASE24_D222_GATE_SHA256": gate_sha,
            }
            verified_bootstrap = _verify_bootstrap_source(test_git, bootstrap_receipt, env=bootstrap_env)
            self.assertEqual(verified_bootstrap["inherited_gate"], bootstrap_receipt["inherited_gate"])
            exact_replacement_diff = test_git.replacement_diff
            for bad_entry in (
                DiffEntry("000000", "100644", "0" * 40, gate_blob, "A", GATE_PATH),
                DiffEntry("100644", "000000", D226_GATE_BLOB, "0" * 40, "D", GATE_PATH),
                DiffEntry("100644", "100644", "0" * 40, gate_blob, "M", GATE_PATH),
            ):
                test_git.replacement_diff = [bad_entry]
                with self.subTest(replacement_diff=bad_entry):
                    with self.assertRaises(GateError):
                        _verify_bootstrap_source(test_git, bootstrap_receipt, env=bootstrap_env)
            test_git.replacement_diff = [*exact_replacement_diff, DiffEntry("100644", "100644", "1" * 40, "2" * 40, "M", "extra.txt")]
            with self.assertRaises(GateError):
                _verify_bootstrap_source(test_git, bootstrap_receipt, env=bootstrap_env)
            for bad_parents in ([], [PLAN_REV, D225_GATE_REV]):
                test_git.gate_parent_override = bad_parents
                with self.subTest(gate_parents=bad_parents):
                    with self.assertRaises(GateError):
                        _verify_bootstrap_source(test_git, bootstrap_receipt, env=bootstrap_env)
            test_git.gate_parent_override = None
            test_git.replacement_diff = exact_replacement_diff
            initial_pr = {
                "number": EXPECTED_PR, "state": "open", "draft": False,
                "head": {"sha": "f" * 40, "ref": "phase24-candidate", "repo": {"full_name": EXPECTED_REPO}},
                "base": {"sha": "9" * 40, "ref": EXPECTED_BASE, "repo": {"full_name": EXPECTED_REPO}},
            }
            pushed_pr = {
                "state": "open", "draft": False,
                "head": {"sha": candidate_sha, "ref": "phase24-candidate"},
                "base": {"sha": "9" * 40, "ref": EXPECTED_BASE},
            }
            responses = {
                f"repos/{EXPECTED_REPO}": {"full_name": EXPECTED_REPO, "permissions": {"pull": True, "push": True}},
                f"repos/{EXPECTED_REPO}/pulls/{EXPECTED_PR}": [initial_pr, pushed_pr],
                f"repos/{EXPECTED_REPO}/branches/{EXPECTED_BASE}/protection": protection,
            }
            live_runner = _RecordingRunner(responses)
            live_args = argparse.Namespace(bootstrap=bootstrap_path, candidate=candidate_sha, evidence=manifest_path, mode="push")
            live_env = {
                "PATH": os.environ.get("PATH", "/usr/bin"), "HOME": str(root),
                "PHASE24_D222_EVIDENCE": manifest_path,
                "PHASE24_D222_EVIDENCE_SHA256": digest_bytes(manifest_raw),
                "PHASE24_D222_REV": candidate_sha,
                "PHASE24_D222_PLAN_REV": PLAN_REV,
                "PHASE24_D222_PLAN_SHA256": PLAN_SHA256,
                "PHASE24_D222_GATE_REV": gate_rev,
                "PHASE24_D222_GATE_SHA256": gate_sha,
            }
            promo_row = next(row for row in direct_rows if row["name"] == "promotion_coverage_controls")
            promo_path = root / promo_row["transcript_path"]
            original_promo_body = promo_path.read_bytes()
            original_promo_digest = promo_row["transcript_sha256"]
            original_qualification_raw = qualification_raw
            original_provenance_raw = provenance_raw
            original_manifest_raw = manifest_raw
            original_qualification_digest = manifest["receipts"]["qualification"]["sha256"]
            original_provenance_digest = manifest["receipts"]["provenance"]["sha256"]
            wrong_promo_body = f"PASS: phase24-promotion-controls gate={'e' * 64} controls=12\n".encode()
            promo_path.write_bytes(wrong_promo_body)
            promo_row["transcript_sha256"] = digest_bytes(wrong_promo_body)
            qualification_raw = canonical_json(qualification) + b"\n"
            (root / qualification_path).write_bytes(qualification_raw)
            provenance["qualification_dispatch"]["receipt_sha256"] = digest_bytes(qualification_raw)
            provenance_raw = canonical_json(provenance) + b"\n"
            (root / provenance_path).write_bytes(provenance_raw)
            manifest["receipts"]["qualification"]["sha256"] = digest_bytes(qualification_raw)
            manifest["receipts"]["provenance"]["sha256"] = digest_bytes(provenance_raw)
            manifest_raw = canonical_json(manifest) + b"\n"
            (root / manifest_path).write_bytes(manifest_raw)
            marker_runner = _RecordingRunner(responses)
            marker_env = {**live_env, "PHASE24_D222_EVIDENCE_SHA256": digest_bytes(manifest_raw)}
            with mock.patch(__name__ + ".Git", return_value=test_git), \
                    mock.patch.dict(globals(), {"__phase24_gate_bytes__": gate_bytes}), \
                    mock.patch.dict(os.environ, marker_env, clear=True):
                with self.assertRaises(GateError) as error:
                    _run_live(root, live_args, runner=marker_runner)
                self.assertEqual(error.exception.reason, "qualification_direct_marker_gate_mismatch")
            self.assertEqual(marker_runner.calls, [])
            self.assertEqual(marker_runner.action_calls, [])
            self.assertEqual((root / history_path).read_bytes(), history_raw)
            promo_path.write_bytes(original_promo_body)
            promo_row["transcript_sha256"] = original_promo_digest
            qualification_raw = original_qualification_raw
            provenance_raw = original_provenance_raw
            manifest_raw = original_manifest_raw
            provenance["qualification_dispatch"]["receipt_sha256"] = digest_bytes(qualification_raw)
            manifest["receipts"]["qualification"]["sha256"] = original_qualification_digest
            manifest["receipts"]["provenance"]["sha256"] = original_provenance_digest
            (root / qualification_path).write_bytes(qualification_raw)
            (root / provenance_path).write_bytes(provenance_raw)
            (root / manifest_path).write_bytes(manifest_raw)

            bad_bootstrap = dict(bootstrap_receipt)
            bad_bootstrap["trusted_handoff"] = dict(bootstrap_receipt["trusted_handoff"], authority="untrusted")
            (root / bootstrap_path).write_bytes(canonical_json(bad_bootstrap) + b"\n")
            malformed_runner = _RecordingRunner(responses)
            with mock.patch(__name__ + ".Git", return_value=test_git), \
                    mock.patch.dict(globals(), {"__phase24_gate_bytes__": gate_bytes}), \
                    mock.patch.dict(os.environ, live_env, clear=True):
                with self.assertRaises(GateError):
                    _run_live(root, live_args, runner=malformed_runner)
            self.assertEqual(malformed_runner.calls, [])
            self.assertEqual(malformed_runner.action_calls, [])
            (root / bootstrap_path).write_bytes(canonical_json(bootstrap_receipt) + b"\n")

            test_git.plan_gate_changed = True
            discussion_runner = _RecordingRunner(responses)
            with mock.patch(__name__ + ".Git", return_value=test_git), \
                    mock.patch.dict(globals(), {"__phase24_gate_bytes__": gate_bytes}), \
                    mock.patch.dict(os.environ, live_env, clear=True):
                with self.assertRaises(GateError):
                    _run_live(root, live_args, runner=discussion_runner)
            self.assertEqual(discussion_runner.calls, [])
            self.assertEqual(discussion_runner.action_calls, [])
            test_git.plan_gate_changed = False

            for fault, reason in (("source_parent_tree", "d226_source_parent_mismatch"),
                                  ("plan_correction_oid", "d226_correction_source_pin_mismatch"),
                                  ("noncorrection_drift", "d221_source_drift")):
                test_git.anchor_fault = fault
                rejected_runner = _RecordingRunner(responses)
                with self.subTest(anchor_fault=fault), \
                        mock.patch(__name__ + ".Git", return_value=test_git), \
                        mock.patch.dict(globals(), {"__phase24_gate_bytes__": gate_bytes}), \
                        mock.patch.dict(os.environ, live_env, clear=True):
                    with self.assertRaises(GateError) as error:
                        _run_live(root, live_args, runner=rejected_runner)
                    self.assertEqual(error.exception.reason, reason)
                self.assertEqual(rejected_runner.calls, [])
                self.assertEqual(rejected_runner.action_calls, [])
                self.assertEqual((root / history_path).read_bytes(), history_raw)
            test_git.anchor_fault = None

            for bad_entry in (
                DiffEntry("000000", "100644", "0" * 40, gate_blob, "A", GATE_PATH),
                DiffEntry("100644", "000000", D225_GATE_BLOB, "0" * 40, "D", GATE_PATH),
                DiffEntry("100644", "100644", "0" * 40, gate_blob, "M", GATE_PATH),
            ):
                test_git.replacement_diff = [bad_entry]
                invalid_runner = _RecordingRunner(responses)
                with self.subTest(live_replacement_diff=bad_entry):
                    with mock.patch(__name__ + ".Git", return_value=test_git), \
                            mock.patch.dict(globals(), {"__phase24_gate_bytes__": gate_bytes}), \
                            mock.patch.dict(os.environ, live_env, clear=True):
                        with self.assertRaises(GateError):
                            _run_live(root, live_args, runner=invalid_runner)
                    self.assertEqual(invalid_runner.action_calls, [])
            test_git.replacement_diff = exact_replacement_diff

            with mock.patch(__name__ + ".Git", return_value=test_git), \
                    mock.patch.dict(globals(), {"__phase24_gate_bytes__": gate_bytes}), \
                    mock.patch.dict(os.environ, live_env, clear=True):
                allowed = _run_live(root, live_args, runner=live_runner)
            self.assertEqual(allowed["decision"], "ALLOW")
            self.assertEqual(live_runner.action_calls, [fixed_push_argv(candidate_sha, "phase24-candidate")])

            (root / history_path).write_bytes(history_raw)
            (root / "build/CMakeCache.txt").write_text("Python3_EXECUTABLE:UNINITIALIZED=/missing/configured/python\n", encoding="utf-8")
            cache_runner = _RecordingRunner(responses)
            with mock.patch(__name__ + ".Git", return_value=test_git), \
                    mock.patch.dict(globals(), {"__phase24_gate_bytes__": gate_bytes}), \
                    mock.patch.dict(os.environ, live_env, clear=True):
                with self.assertRaises(GateError):
                    _run_live(root, live_args, runner=cache_runner)
            self.assertEqual(cache_runner.action_calls, [])
            self.assertEqual(cache_runner.calls, [])
            (root / "build/CMakeCache.txt").write_text(f"Python3_EXECUTABLE:UNINITIALIZED={sys.executable}\n", encoding="utf-8")

            bad_provenance = dict(provenance)
            bad_provenance["review_dispatches"] = [dict(item) for item in provenance["review_dispatches"]]
            bad_provenance["review_dispatches"][0]["report_sha256"] = "0" * 64
            bad_provenance_raw = canonical_json(bad_provenance) + b"\n"
            (root / provenance_path).write_bytes(bad_provenance_raw)
            manifest["receipts"]["provenance"]["sha256"] = digest_bytes(bad_provenance_raw)
            bad_manifest_raw = canonical_json(manifest) + b"\n"
            (root / manifest_path).write_bytes(bad_manifest_raw)
            provenance_runner = _RecordingRunner(responses)
            bad_env = {**live_env, "PHASE24_D222_EVIDENCE_SHA256": digest_bytes(bad_manifest_raw)}
            with mock.patch(__name__ + ".Git", return_value=test_git), \
                    mock.patch.dict(globals(), {"__phase24_gate_bytes__": gate_bytes}), \
                    mock.patch.dict(os.environ, bad_env, clear=True):
                with self.assertRaises(GateError):
                    _run_live(root, live_args, runner=provenance_runner)
            self.assertEqual(provenance_runner.action_calls, [])
            self.assertEqual(provenance_runner.calls, [])

            code_review_path, original_code_report, _ = reports["gsd-code-reviewer"]
            code_report_with_stop = original_code_report + b"The review requires server-side enforcement before approval.\n"
            (root / code_review_path).write_bytes(code_report_with_stop)
            code_review_receipt = strict_json_bytes(review_receipts["code_review"])
            code_review_receipt["report_sha256"] = digest_bytes(code_report_with_stop)
            code_review_raw = canonical_json(code_review_receipt) + b"\n"
            (root / receipt_paths["code_review"]).write_bytes(code_review_raw)
            (root / provenance_path).write_bytes(provenance_raw)
            provenance_with_code_report = dict(provenance)
            provenance_with_code_report["review_dispatches"] = [dict(item) for item in provenance["review_dispatches"]]
            code_dispatch = next(item for item in provenance_with_code_report["review_dispatches"] if item["role"] == "gsd-code-reviewer")
            code_dispatch["report_sha256"] = digest_bytes(code_report_with_stop)
            provenance_with_code_report_raw = canonical_json(provenance_with_code_report) + b"\n"
            (root / provenance_path).write_bytes(provenance_with_code_report_raw)
            manifest["receipts"]["code_review"]["sha256"] = digest_bytes(code_review_raw)
            manifest["receipts"]["provenance"]["sha256"] = digest_bytes(provenance_with_code_report_raw)
            code_stop_manifest_raw = canonical_json(manifest) + b"\n"
            (root / manifest_path).write_bytes(code_stop_manifest_raw)
            code_stop_runner = _RecordingRunner(responses)
            code_stop_env = {**live_env, "PHASE24_D222_EVIDENCE_SHA256": digest_bytes(code_stop_manifest_raw)}
            with mock.patch(__name__ + ".Git", return_value=test_git), \
                    mock.patch.dict(globals(), {"__phase24_gate_bytes__": gate_bytes}), \
                    mock.patch.dict(os.environ, code_stop_env, clear=True):
                with self.assertRaises(GateError) as stop:
                    _run_live(root, live_args, runner=code_stop_runner)
            self.assertEqual(stop.exception.reason, "server_side_enforcement_required")
            self.assertEqual(code_stop_runner.action_calls, [])
            self.assertEqual(code_stop_runner.calls, [])

    def test_ctest_inventory_binds_exact_order_commands_interpreter_deadlines_and_floors(self) -> None:
        root = Path.cwd().resolve()
        python = sys.executable
        cmake = shutil.which("cmake")
        self.assertIsNotNone(cmake)
        sha = "a" * 40
        rows = []
        for name in EXPECTED_TESTS:
            props = [{"name": "TIMEOUT", "value": TEST_DEADLINES[name]}]
            if TEST_PROCESSORS[name] != 1:
                props.append({"name": "PROCESSORS", "value": TEST_PROCESSORS[name]})
            if TEST_LABELS[name] is not None:
                props.append({"name": "LABELS", "value": list(TEST_LABELS[name])})
            rows.append({"name": name, "command": _expected_ctest_command(name, root, python, cmake or "", sha), "properties": props})
        inventory = {"kind": "ctestInfo", "version": {"major": 3, "minor": 29, "patch": 0}, "backtraceGraph": {}, "tests": rows[::-1]}
        _validate_ctest_inventory(root, python, sha, inventory)
        bad = json.loads(json.dumps(inventory))
        bad["tests"][0]["command"].append("--parallel")
        with self.assertRaises(GateError):
            _validate_ctest_inventory(root, python, sha, bad)
        bad = json.loads(json.dumps(inventory))
        bad["tests"][7]["properties"][0]["value"] = 30
        with self.assertRaises(GateError):
            _validate_ctest_inventory(root, python, sha, bad)
        bad = json.loads(json.dumps(inventory))
        bad_row = next(row for row in bad["tests"] if row["name"] == "phase22_evidence_contract")
        next(prop for prop in bad_row["properties"] if prop["name"] == "LABELS")["value"] = ["planning"]
        with self.assertRaises(GateError):
            _validate_ctest_inventory(root, python, sha, bad)
        bad = json.loads(json.dumps(inventory))
        bad_row = next(row for row in bad["tests"] if row["name"] == "workflow_policy_check")
        bad_row["properties"].append({"name": "LABELS", "value": ["planning"]})
        with self.assertRaises(GateError):
            _validate_ctest_inventory(root, python, sha, bad)
        with self.assertRaises(GateError):
            _validate_ctest_inventory(root, python, sha, {"tests": rows[:-1]})

    def test_candidate_two_reads_exact_latest_failed_run_and_job(self) -> None:
        first_sha, first_tree = "a" * 40, "b" * 40
        run_id, attempt, context = "44199999999", 1, "required-native"
        history = _test_genesis_history()["records"]
        action_id = "1" * 32
        records = [dict(item) for item in history]
        _append_hash_record(records, kind="reservation", candidate_sha=first_sha, candidate_tree=first_tree, action_id=action_id, outcome="ALLOW")
        _append_hash_record(records, kind="push_result", candidate_sha=first_sha, candidate_tree=first_tree, action_id=action_id, outcome="pushed")
        _append_hash_record(records, kind="matrix_result", candidate_sha=first_sha, candidate_tree=first_tree, action_id=action_id, outcome="failed", run_id=run_id, run_attempt=attempt, context=context, in_scope=True, causal_fix_paths=[EXPECTED_CANDIDATE_CORRECTIONS[0]])
        records = _validate_history({"schema_version": 1, "kind": "phase24-d222-history", "records": records, "head": records[-1]["digest"]})
        second = {"sha": "c" * 40, "tree": "d" * 40, "paths": [EXPECTED_CANDIDATE_CORRECTIONS[0]]}
        cause = {"previous_candidate_sha": first_sha, "matrix_run_id": run_id, "run_attempt": attempt, "failed_context": context, "causal_fix_paths": [EXPECTED_CANDIDATE_CORRECTIONS[0]], "failure_contract": "required-native exposed a deterministic causal failure"}
        manifest = {"causal_resolution": cause}
        state = _history_state(records, second, manifest, action="push")
        remote = {"head_sha": first_sha, "branch": "phase24-candidate", "protection": _test_protection()}
        responses = _fake_causal_failure_responses(run_id, attempt, first_sha, remote["branch"], context)
        runner = _RecordingRunner(responses)
        result = _validate_causal_matrix_failure(GitHubReader(runner, {"PATH": "/usr/bin"}), second, manifest, state, remote)
        self.assertEqual(result["run_attempt"], attempt)
        self.assertEqual(len(runner.calls), 4)
        stale = _fake_causal_failure_responses(run_id, attempt + 1, first_sha, remote["branch"], context)
        stale_runner = _RecordingRunner(stale)
        with self.assertRaises(GateError):
            _validate_causal_matrix_failure(GitHubReader(stale_runner, {"PATH": "/usr/bin"}), second, manifest, state, remote)
        self.assertEqual(len(stale_runner.calls), 2)
        self.assertEqual(stale_runner.calls[0][0][2], f"repos/{EXPECTED_REPO}/commits/{first_sha}/check-runs?filter=latest&per_page=100")
        self.assertEqual(stale_runner.calls[1][0][2], f"repos/{EXPECTED_REPO}/actions/runs?head_sha={first_sha}&per_page=100")
        self.assertTrue(all("/jobs?" not in call[0][2] for call in stale_runner.calls))
        mutated = _fake_causal_failure_responses(run_id, attempt, "e" * 40, remote["branch"], context)
        mutated_runner = _RecordingRunner(mutated)
        with self.assertRaises(GateError):
            _validate_causal_matrix_failure(GitHubReader(mutated_runner, {"PATH": "/usr/bin"}), second, manifest, state, remote)
        self.assertEqual(len(mutated_runner.calls), 1)

    def test_eligible_candidate_one_uses_fixed_non_force_push(self) -> None:
        candidate = {"sha": "a" * 40, "tree": "b" * 40, "paths": [EXPECTED_CANDIDATE_CORRECTIONS[0]]}
        history_obj = _test_genesis_history()
        records = _validate_history(history_obj)
        history_state = _history_state(records, candidate, {"causal_resolution": None}, action="push")
        remote = {"head_sha": "c" * 40, "base_sha": "d" * 40, "branch": "phase24-candidate"}
        runner = _RecordingRunner()
        _authorization_contract("push", candidate, {**history_state, "branch": remote["branch"]}, remote, auth_ready=True, credential_ready=True)
        result = _dispatch_fixed_action("push", candidate, remote["branch"], runner, auth_environment({"PATH": "/usr/bin", "HOME": "/tmp"}))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(runner.calls[0][0], fixed_push_argv(candidate["sha"], remote["branch"]))
        self.assertNotIn("--force", runner.calls[0][0])

    def test_eligible_reviewed_candidate_merges_with_head_match(self) -> None:
        sha = "a" * 40
        candidate = {"sha": sha, "tree": "b" * 40, "paths": [EXPECTED_CANDIDATE_CORRECTIONS[0]]}
        history_obj = _test_genesis_history()
        records = [dict(item) for item in history_obj["records"]]
        action_id = "1" * 32
        _append_hash_record(records, kind="reservation", candidate_sha=sha, candidate_tree=candidate["tree"], action_id=action_id, outcome="ALLOW")
        _append_hash_record(records, kind="push_result", candidate_sha=sha, candidate_tree=candidate["tree"], action_id=action_id, outcome="pushed")
        _append_hash_record(records, kind="matrix_result", candidate_sha=sha, candidate_tree=candidate["tree"], action_id=action_id, outcome="passed", run_id="44199999991", run_attempt=1, context=None, in_scope=False)
        history_state = _history_state(records, candidate, {}, action="merge")
        remote = {"head_sha": sha, "branch": "phase24-candidate", "protection": _test_protection()}
        runner = _RecordingRunner(_fake_success_responses(sha))
        _authorization_contract("merge", candidate, {**history_state, "branch": remote["branch"]}, remote, auth_ready=True, credential_ready=True)
        _validate_status_and_checks(GitHubReader(runner, {"PATH": "/usr/bin"}), candidate, remote["branch"], _test_protection())
        result = _dispatch_fixed_action("merge", candidate, remote["branch"], runner, {"PATH": "/usr/bin"})
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(runner.calls), 7)
        self.assertEqual(runner.calls[-1][0], fixed_merge_argv(sha))
        self.assertIn("--match-head-commit", runner.calls[-1][0])
        self.assertNotIn("--admin", runner.calls[-1][0])

    def test_candidate_two_needs_causal_in_scope_matrix_failure(self) -> None:
        first_sha, first_tree = "a" * 40, "b" * 40
        second_sha, second_tree = "c" * 40, "d" * 40
        first_id = "1" * 32
        history_obj = _test_genesis_history()
        records = [dict(item) for item in history_obj["records"]]
        _append_hash_record(records, kind="reservation", candidate_sha=first_sha, candidate_tree=first_tree, action_id=first_id, outcome="ALLOW")
        _append_hash_record(records, kind="push_result", candidate_sha=first_sha, candidate_tree=first_tree, action_id=first_id, outcome="pushed")
        _append_hash_record(records, kind="matrix_result", candidate_sha=first_sha, candidate_tree=first_tree, action_id=first_id, outcome="failed", run_id="44199999999", run_attempt=1, context="required-native", in_scope=True, causal_fix_paths=[EXPECTED_CANDIDATE_CORRECTIONS[0]])
        validated = _validate_history({"schema_version": 1, "kind": "phase24-d222-history", "records": records, "head": records[-1]["digest"]})
        second = {"sha": second_sha, "tree": second_tree, "paths": [EXPECTED_CANDIDATE_CORRECTIONS[0]]}
        cause = {"previous_candidate_sha": first_sha, "matrix_run_id": "44199999999", "run_attempt": 1, "failed_context": "required-native", "causal_fix_paths": [EXPECTED_CANDIDATE_CORRECTIONS[0]], "failure_contract": "the protected required-native job exposed a deterministic in-scope failure"}
        state = _history_state(validated, second, {"causal_resolution": cause}, action="push")
        self.assertEqual(state["candidate_number"], 2)
        bad = {"causal_resolution": {**cause, "matrix_run_id": "44100000000"}}
        with self.assertRaises(GateError):
            _history_state(validated, second, bad, action="push")
        replay = dict(second, sha=first_sha)
        with self.assertRaises(GateError):
            _history_state(validated, replay, {"causal_resolution": cause}, action="push")

    def test_successful_first_matrix_closes_candidate_budget_but_allows_merge(self) -> None:
        sha, tree = "a" * 40, "b" * 40
        candidate = {"sha": sha, "tree": tree, "paths": [EXPECTED_CANDIDATE_CORRECTIONS[0]]}
        records = [dict(item) for item in _test_genesis_history()["records"]]
        action_id = "1" * 32
        _append_hash_record(records, kind="reservation", candidate_sha=sha, candidate_tree=tree, action_id=action_id, outcome="ALLOW")
        _append_hash_record(records, kind="push_result", candidate_sha=sha, candidate_tree=tree, action_id=action_id, outcome="pushed")
        _append_hash_record(records, kind="matrix_result", candidate_sha=sha, candidate_tree=tree, action_id=action_id, outcome="passed", run_id="44199999991", run_attempt=1, context=None, in_scope=False)
        history = _validate_history({"schema_version": 1, "kind": "phase24-d222-history", "records": records, "head": records[-1]["digest"]})
        with self.assertRaises(GateError):
            _history_state(history, {"sha": "c" * 40, "tree": "d" * 40, "paths": list(candidate["paths"])}, {"causal_resolution": {"previous_candidate_sha": sha, "matrix_run_id": "44199999991", "run_attempt": 1, "failed_context": "required-native", "causal_fix_paths": list(candidate["paths"]), "failure_contract": "failure"}}, action="push")
        self.assertEqual(_history_state(history, candidate, {}, action="merge")["candidate_number"], 1)

    def test_strict_json_rejects_duplicates_nonfinite_and_boolean_counts(self) -> None:
        with self.assertRaises(GateError):
            strict_json_bytes(b'{"mode":"push","mode":"merge"}')
        with self.assertRaises(GateError):
            strict_json_bytes(b'{"ratio":NaN}')
        with self.assertRaises(GateError):
            strict_json_bytes(b'{"ratio":1e999}')
        with self.assertRaises(GateError):
            strict_json_bytes(b'{"ratio":-1e999}')
        with self.assertRaises(GateError):
            require_type(True, int, "count")

    def test_receipt_paths_reject_symlinked_parent_components(self) -> None:
        with tempfile.TemporaryDirectory(prefix="phase24-symlink-") as temp:
            root = Path(temp) / "root"
            outside = Path(temp) / "outside"
            root.mkdir()
            outside.mkdir()
            (outside / "receipt.json").write_bytes(b"{}")
            (root / "build").mkdir()
            (root / "build/phase24").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(GateError):
                _safe_receipt_path(root, "build/phase24/receipt.json")

    def test_auth_environment_keeps_only_required_auth_inputs(self) -> None:
        env = auth_environment({
            "PATH": "/usr/bin", "HOME": "/home/agent", "GH_CONFIG_DIR": "/tmp/gh",
            "GITHUB_TOKEN": "secret-token", "GIT_DIR": "/tmp/evil", "GIT_CONFIG_COUNT": "1",
            "GIT_ASKPASS": "/tmp/prompt", "SSH_ASKPASS": "/tmp/ssh-prompt", "EXTRA_SECRET": "hide-me",
        })
        self.assertEqual(env["HOME"], "/home/agent")
        self.assertEqual(env["GH_CONFIG_DIR"], "/tmp/gh")
        self.assertEqual(env["GITHUB_TOKEN"], "secret-token")
        self.assertEqual(env["GIT_CONFIG_GLOBAL"], os.devnull)
        self.assertEqual(env["GH_HOST"], "github.com")
        self.assertEqual(env["GH_PROMPT_DISABLED"], "1")
        for key in ("GIT_DIR", "GIT_CONFIG_COUNT", "GIT_ASKPASS", "SSH_ASKPASS", "EXTRA_SECRET", "GH_REPO"):
            self.assertNotIn(key, env)

    def test_hostile_git_environment_fails_before_reads(self) -> None:
        runner = _RecordingRunner()
        with self.assertRaises(GateError):
            reject_hostile_git_environment({"GIT_DIR": "/tmp/redirect"})
        reject_hostile_git_environment({"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull})
        self.assertEqual(runner.action_calls, [])

    def test_wrong_repository_and_gate_handoffs_fail_before_actions(self) -> None:
        runner = _RecordingRunner()
        class WrongRootGit:
            root = Path.cwd().resolve()
            def text(self, *args: str) -> str:
                if args == ("rev-parse", "--show-toplevel"):
                    return str(Path.cwd().parent.resolve())
                if args == ("rev-parse", "--absolute-git-dir"):
                    return str(Path.cwd() / ".git")
                if args == ("symbolic-ref", "--quiet", "--short", "HEAD"):
                    return "gsd/phase-24-test"
                deny("unexpected_fake_git_read")
        with self.assertRaises(GateError):
            current_root(WrongRootGit())
        gate_rev, gate_sha = "a" * 40, "b" * 64
        bootstrap = {
            "plan": {"rev": PLAN_REV, "parent": PLAN_PARENT, "tree": PLAN_TREE, "blob": PLAN_BLOB, "sha256": PLAN_SHA256, "path_sha256": PLAN_PATH_SHA256},
            "discussion": {"rev": DISCUSSION_REV, "tree": DISCUSSION_TREE, "blob": DISCUSSION_BLOB, "sha256": DISCUSSION_SHA256, "path_sha256": DISCUSSION_PATH_SHA256},
            "closeout": {"rev": CLOSEOUT_REV, "tree": CLOSEOUT_TREE, "blob": CLOSEOUT_BLOB, "sha256": CLOSEOUT_SHA256, "path_sha256": CLOSEOUT_PATH_SHA256},
            "loader": {"sha256": digest_bytes(extract_plan_loader(Git(Path.cwd()).pinned_blob(PLAN_REV, PLAN_TREE, PLAN_PATH_SHA256, PLAN_BLOB, PLAN_SHA256)))},
            "inherited_gate": {"rev": D226_GATE_REV, "tree": D226_GATE_TREE, "blob": D226_GATE_BLOB, "sha256": D226_GATE_SHA256, "mode": "100644"},
            "gate": {"rev": gate_rev, "parent": PLAN_REV, "tree": "c" * 40, "blob": "d" * 40, "sha256": gate_sha, "old_blob": D226_GATE_BLOB, "old_mode": "100644"},
            "trusted_handoff": {"authority": "gsd-executor", "plan_rev": PLAN_REV, "plan_sha256": PLAN_SHA256, "gate_rev": gate_rev, "gate_sha256": gate_sha},
            "repository": {"root": str(Path.cwd()), "git_dir": str(Path.cwd() / ".git"), "branch": "gsd/phase-24-test"},
            "scope": {"source_allowlist": list((*PLAN_SOURCE_PATHS, GATE_PATH)), "correction_allowlist": list(EXPECTED_CANDIDATE_CORRECTIONS)},
            "history_pins": {"d209_rev": D209_REV, "d220_candidate": D220_SHA, "d221_candidate": D221_SHA, "d221_tree": D221_TREE, "d221_exec_rev": D221_EXEC_REV, "requirements_blob": REQUIREMENTS_BLOB, "roadmap_blob": ROADMAP_BLOB, "state_forks_blob": STATE_FORKS_BLOB, "planning_hygiene_sha256": PLANNING_HYGIENE_SHA256, **D226_HISTORY_PINS},
        }
        base_env = {"PHASE24_D222_PLAN_REV": PLAN_REV, "PHASE24_D222_PLAN_SHA256": PLAN_SHA256, "PHASE24_D222_GATE_REV": gate_rev, "PHASE24_D222_GATE_SHA256": gate_sha}
        for bad_env in ({**base_env, "PHASE24_D222_GATE_REV": "f" * 40}, {**base_env, "PHASE24_D222_GATE_SHA256": "e" * 64}):
            with self.assertRaises(GateError):
                _verify_bootstrap_source(runner, bootstrap, env=bad_env)
        with self.assertRaises(GateError):
            _verify_executing_bytes(b"pinned immutable gate source", b"candidate checkout substitution")
        self.assertEqual(runner.action_calls, [])

    def test_origin_follow_tags_setting_cannot_expand_push_scope(self) -> None:
        class ConfigGit:
            root = Path.cwd()
            def __init__(self, values: Mapping[str, list[str]]) -> None:
                self.values = values
            def run_result(self, *args: str, **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
                if args[:2] == ("config", "--local"):
                    values = self.values.get(args[-1], [])
                    if not values:
                        return subprocess.CompletedProcess(list(args), 1, b"", b"")
                    return subprocess.CompletedProcess(list(args), 0, ("\n".join(values) + "\n").encode(), b"")
                if args[:2] == ("remote", "get-url"):
                    return subprocess.CompletedProcess(list(args), 0, EXPECTED_URL.encode() + b"\n", b"")
                return subprocess.CompletedProcess(list(args), 1, b"", b"")
        base = {"remote.origin.url": [EXPECTED_URL]}
        for values in (["true"], ["false", "true"], ["sometimes"]):
            with self.assertRaises(GateError):
                _verify_origin(ConfigGit({**base, "push.followTags": list(values)}))
        for values in (["true"], ["false", "true"], ["sometimes"]):
            with self.assertRaises(GateError):
                _verify_origin(ConfigGit({**base, "remote.origin.mirror": list(values)}))
        _verify_origin(ConfigGit({**base, "push.followTags": ["false"]}))
        _verify_origin(ConfigGit({**base, "remote.origin.mirror": ["false"]}))
        _verify_origin(ConfigGit(base))

    def test_review_stop_detector_catches_both_server_enforcement_word_orders(self) -> None:
        self.assertTrue(_server_side_enforcement_required("The review says server-side enforcement is required."))
        self.assertTrue(_server_side_enforcement_required("The report requires server-side enforcement before approval."))
        self.assertFalse(_server_side_enforcement_required("The local guard validates the candidate."))

    def test_raw_nul_diff_requires_unique_regular_file_records(self) -> None:
        raw = b":000000 100644 " + b"0" * 40 + b" " + b"1" * 40 + b" A\x00file.py\x00"
        entry = parse_raw_nul_diff(raw)[0]
        self.assertEqual((entry.status, entry.path, entry.raw_path, entry.new_mode), ("A", "file.py", b"file.py", "100644"))
        with self.assertRaises(GateError):
            parse_raw_nul_diff(raw[:-1])
        duplicate = raw + raw[1:]
        with self.assertRaises(GateError):
            parse_raw_nul_diff(duplicate)

    def test_plan_scopes_are_read_from_original_committed_plan(self) -> None:
        git = Git(Path.cwd())
        raw = git.pinned_blob(PLAN_REV, PLAN_TREE, PLAN_PATH_SHA256, PLAN_BLOB, PLAN_SHA256)
        sources, corrections = parse_plan_scopes(raw)
        self.assertEqual(sources, (*PLAN_SOURCE_PATHS, GATE_PATH))
        self.assertEqual(corrections, EXPECTED_CANDIDATE_CORRECTIONS)
        with self.assertRaises(GateError):
            parse_plan_scopes(raw.replace(b"tests/scripts/verify-state-forks.py", b"tests/scripts/unapproved.py", 1))
        altered_correction = raw.replace(
            b"correction_allowlist:\n  - .github/scripts/wait-exact-head-ci.py",
            b"correction_allowlist:\n  - .github/scripts/other.py",
            1,
        )
        with self.assertRaises(GateError) as error:
            parse_plan_scopes(altered_correction)
        self.assertEqual(error.exception.reason, "plan_correction_scope_changed")

    def test_protection_requires_current_exact_contexts_and_strict_admin_policy(self) -> None:
        good = {
            "required_status_checks": {"strict": True, "contexts": list(REQUIRED_CONTEXTS), "checks": [{"context": name, "app_id": 15368} for name in REQUIRED_CONTEXTS]},
            "enforce_admins": {"enabled": True}, "allow_force_pushes": {"enabled": False}, "allow_deletions": {"enabled": False},
        }
        _validate_protection(good)
        bad = json.loads(json.dumps(good))
        bad["allow_force_pushes"]["enabled"] = True
        with self.assertRaises(GateError):
            _validate_protection(bad)
        bad = json.loads(json.dumps(good))
        bad["required_status_checks"]["contexts"].append("extra")
        with self.assertRaises(GateError):
            _validate_protection(bad)
        bad = json.loads(json.dumps(good))
        bad["enforce_admins"]["enabled"] = False
        with self.assertRaises(GateError):
            _validate_protection(bad)

    def test_latest_status_check_run_and_job_must_all_pass(self) -> None:
        sha = "a" * 40
        runner = _RecordingRunner(_fake_success_responses(sha))
        reader = GitHubReader(runner, {"PATH": "/usr/bin"})
        result = _validate_status_and_checks(reader, {"sha": sha}, "phase24-candidate", _test_protection())
        self.assertEqual(result["contexts"], list(REQUIRED_CONTEXTS))
        self.assertEqual(len(runner.calls), 6)
        bad = _fake_success_responses(sha)
        bad[f"repos/{EXPECTED_REPO}/commits/{sha}/status"]["statuses"][0]["state"] = "skipped"
        runner = _RecordingRunner(bad)
        with self.assertRaises(GateError):
            _validate_status_and_checks(GitHubReader(runner, {"PATH": "/usr/bin"}), {"sha": sha}, "phase24-candidate", _test_protection())

        status_free = _fake_success_responses(sha)
        status_free[f"repos/{EXPECTED_REPO}/commits/{sha}/status"]["statuses"] = []
        _validate_status_and_checks(GitHubReader(_RecordingRunner(status_free), {"PATH": "/usr/bin"}), {"sha": sha}, "phase24-candidate", _test_protection())

        rerun = _fake_success_responses(sha)
        rerun_key = f"repos/{EXPECTED_REPO}/actions/runs?head_sha={sha}&per_page=100"
        rerun[rerun_key]["workflow_runs"][0]["run_attempt"] = 2
        rerun_runner = _RecordingRunner(rerun)
        with self.assertRaises(GateError):
            _validate_status_and_checks(GitHubReader(rerun_runner, {"PATH": "/usr/bin"}), {"sha": sha}, "phase24-candidate", _test_protection())
        self.assertEqual(rerun_runner.action_calls, [])

        duplicate_pr = _fake_success_responses(sha)
        check_key = f"repos/{EXPECTED_REPO}/commits/{sha}/check-runs?filter=latest&per_page=100"
        duplicate_pr[check_key]["check_runs"][0]["pull_requests"].append({"number": EXPECTED_PR})
        duplicate_runner = _RecordingRunner(duplicate_pr)
        with self.assertRaises(GateError):
            _validate_status_and_checks(GitHubReader(duplicate_runner, {"PATH": "/usr/bin"}), {"sha": sha}, "phase24-candidate", _test_protection())
        self.assertEqual(duplicate_runner.action_calls, [])

        bad = _fake_success_responses(sha)
        first = bad[f"repos/{EXPECTED_REPO}/commits/{sha}/check-runs?filter=latest&per_page=100"]["check_runs"][0]
        first["app"]["id"] = 99999
        runner = _RecordingRunner(bad)
        with self.assertRaises(GateError):
            _validate_status_and_checks(GitHubReader(runner, {"PATH": "/usr/bin"}), {"sha": sha}, "phase24-candidate", _test_protection())

    def test_credential_probe_is_private_and_requires_both_fields(self) -> None:
        runner = _RecordingRunner()
        env = auth_environment({"PATH": "/usr/bin", "HOME": "/tmp", "GH_CONFIG_DIR": "/tmp/gh"})
        _credential_probe(runner, Path.cwd(), env)
        argv, passed_env, timeout, request = runner.calls[0]
        self.assertEqual(argv[0:8], ["git", "--no-replace-objects", "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential", "-c", "credential.interactive=false"])
        self.assertEqual(request, b"protocol=https\nhost=github.com\npath=szTheory/gabbaboy.git\n\n")
        self.assertEqual(timeout, CHILD_TIMEOUT)
        self.assertEqual(passed_env["HOME"], "/tmp")
        no_credential = _RecordingRunner(credential_output=b"username=only-user\n")
        with self.assertRaises(GateError) as error:
            _credential_probe(no_credential, Path.cwd(), env)
        self.assertNotIn("only-user", str(error.exception))

    def test_fixed_dispatch_refuses_bad_state_before_action_call(self) -> None:
        runner = _RecordingRunner()
        candidate = {"sha": "a" * 40, "tree": "b" * 40}
        remote = {"head_sha": candidate["sha"], "branch": "phase24-candidate"}
        with self.assertRaises(GateError):
            _authorization_contract("push", candidate, {"branch": remote["branch"]}, remote, auth_ready=True, credential_ready=True)
        self.assertEqual(runner.calls, [])
        with self.assertRaises(GateError):
            _authorization_contract("push", candidate, {"branch": remote["branch"]}, {"head_sha": "c" * 40, "branch": "phase24-candidate"}, auth_ready=False, credential_ready=True)
        self.assertEqual(runner.calls, [])

    def test_plan_loader_is_unique_and_fresh_process_rejects_bad_pins(self) -> None:
        git = Git(Path.cwd())
        raw = git.pinned_blob(PLAN_REV, PLAN_TREE, PLAN_PATH_SHA256, PLAN_BLOB, PLAN_SHA256)
        loader = extract_plan_loader(raw)
        self.assertIn(b"PHASE24_D222_GATE_REV", loader)
        duplicated = raw + b"\n<trusted_invocation>\n```python\npass\n```\n</trusted_invocation>\n"
        with self.assertRaises(GateError):
            extract_plan_loader(duplicated)
        wrapper = fresh_plan_wrapper_source()
        self.assertEqual(wrapper.encode("utf-8"), loader)
        env = source_git_env()
        env.pop("PHASE24_D222_GATE_REV", None)
        env.pop("PHASE24_D222_GATE_SHA256", None)
        try:
            missing = subprocess.run([sys.executable, "-I", "-c", wrapper], capture_output=True, timeout=30, env=env)
        except OSError:
            self.fail("fresh Python interpreter was unavailable")
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn(b"DENY: missing trusted gate pins", missing.stderr)
        env.update({"PHASE24_D222_GATE_REV": D224_GATE_REV, "PHASE24_D222_GATE_SHA256": "0" * 64})
        wrong_gate = subprocess.run([sys.executable, "-I", "-c", wrapper], capture_output=True, timeout=30, env=env)
        self.assertNotEqual(wrong_gate.returncode, 0)
        self.assertIn(b"DENY: gate digest mismatch", wrong_gate.stderr)
        with self.assertRaises(GateError):
            _verify_executing_bytes(b"immutable bootstrap bytes", b"candidate checkout bytes")


def _run_self_test() -> int:
    global _SELF_TEST_ACTIVE
    _SELF_TEST_ACTIVE = True
    loaded = globals().get("__phase24_gate_bytes__")
    executing_source_bytes()
    if loaded is not None:
        source = Path.cwd()
        git = Git(source)
        gate_rev = os.environ.get("PHASE24_D222_GATE_REV", "")
        gate_digest = os.environ.get("PHASE24_D222_GATE_SHA256", "")
        if not valid_sha(gate_rev) or not valid_sha256(gate_digest):
            deny("missing_trusted_gate_handoff")
        pinned = git.blob(gate_rev, GATE_PATH)
        if digest_bytes(pinned) != gate_digest:
            deny("gate_digest_mismatch")
        _verify_executing_bytes(pinned, loaded)
    try:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(PromotionGateContractTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if result.wasSuccessful():
            print(f"PHASE24_D227_SELF_TESTS=PASS tests={result.testsRun}")
            return 0
        return 1
    finally:
        _SELF_TEST_ACTIVE = False


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=True, allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--verify-bootstrap", action="store_true")
    modes.add_argument("--preflight", action="store_true")
    modes.add_argument("--action", choices=("push", "merge"))
    parser.add_argument("--bootstrap")
    parser.add_argument("--candidate")
    parser.add_argument("--evidence")
    return parser


def _emit(value: Mapping[str, Any]) -> None:
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)
    if args.self_test:
        if any((args.bootstrap, args.candidate, args.evidence)):
            _emit({"decision": "DENY", "reason": "self_test_has_live_arguments"})
            return 2
        try:
            return _run_self_test()
        except GateError as exc:
            _emit({"decision": "DENY", "reason": exc.reason, "message": str(exc)})
            return 2
        except Exception:
            _emit({"decision": "DENY", "reason": "self_test_unexpected_error"})
            return 2
    root = Path.cwd().resolve(strict=True)
    try:
        if args.verify_bootstrap:
            if args.candidate or args.evidence:
                deny("bootstrap_mode_extra_arguments")
            path = args.bootstrap or os.environ.get("PHASE24_D222_BOOTSTRAP", "")
            if not path:
                deny("missing_bootstrap_receipt")
            result = verify_bootstrap(root, path)
        else:
            if not args.candidate or not valid_sha(args.candidate):
                deny("missing_or_invalid_candidate")
            args.mode = "preflight" if args.preflight else args.action
            if args.mode is None:
                deny("invalid_action")
            result = _run_live(root, args)
        _emit(result)
        return 0
    except GateError as exc:
        _emit({"decision": "DENY", "reason": exc.reason, "message": str(exc)})
        return 2
    except Exception:
        # Avoid emitting exception text; subprocess/config exceptions can carry
        # credential-bearing helper output or private host paths.
        _emit({"decision": "DENY", "reason": "unexpected_gate_error"})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
