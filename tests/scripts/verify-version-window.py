#!/usr/bin/env python3
"""Check the exact-content identity of a reviewed version-PR window (RM-028, D-19).

A version PR is generated content: release-please rewrites CHANGELOG.md, the version files and the PR body, and
the support ledger is rendered from managed generator inputs. A short review freeze is therefore a content/event
rule, never a clock: it begins only after generation and a green review of one exact head, and any later change
to main, source, release notes, generator inputs or the regenerated PR body ends it. It is reopened only by
regenerating the managed outputs, recomputing the digests below and rerunning the exact-head required checks and
rehearsal.

    verify-version-window.py --rev SHA --base SHA --check RECORD [--body PATH]
    verify-version-window.py --rev SHA --base SHA --digest [--body PATH] [--pull-request N ...]
    verify-version-window.py --check-tracked
    verify-version-window.py --self-test

--rev and --base are resolved immutable 40-hex commits. The record and every digest are read from Git objects at
--rev (git show semantics); the live working tree is never consulted and never a fallback. The record itself is
the one file allowed to differ between the reviewed head and --rev, so it cannot (and does not) hash itself.

This checker verifies content bindings only. The recorded review and rehearsal run identities name exact-head
hosted evidence; the required checks on the exact head, not this script, authenticate that evidence.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECORD_PATH = "tests/data/version-window.json"
MAX_RECORD_BYTES = 64 * 1024
MAX_BLOB_BYTES = 32 * 1024 * 1024
MAX_BODY_BYTES = 1024 * 1024
SHA1 = re.compile(r"[0-9a-f]{40}")
SHA256 = re.compile(r"[0-9a-f]{64}")
VERSION = re.compile(r"\d+\.\d+\.\d+")

# Generator inputs: a change to any of them changes what release-please or --write-current would render.
REQUIRED_MANAGED_INPUTS = (
    "tests/data/release-disclosure.json",
    "tests/data/support-claims-v0.3.json",
    "tests/scripts/verify-support-ledger.py",
    "release-please-config.json",
)
# Regenerated outputs of the version PR (the ledger path is derived from the version).
REQUIRED_GENERATED_FILES = ("CHANGELOG.md", ".release-please-manifest.json")

TOP_KEYS = {"schema_version", "kind", "state", "release_version", "intended", "managed_inputs", "generated",
            "review", "rehearsal"}
NULLABLE = TOP_KEYS - {"schema_version", "kind", "state"}


class WindowError(Exception):
    """A rejected window: the message starts with a stable window-* diagnostic code."""


def reject(code: str, detail: str = "") -> None:
    raise WindowError(code + (": " + detail if detail else ""))


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_body(raw: bytes) -> bytes:
    """The PR body as GitHub stores it varies in line endings and trailing newlines between the API, the web editor and
    `gh`; those carry no meaning. Every other byte is part of the reviewed content."""
    return raw.replace(b"\r\n", b"\n").rstrip(b"\n")


def git_environment() -> dict:
    environment = os.environ.copy()
    environment.update({
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
    })
    return environment


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=repo, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30,
                            env=git_environment())
    if check and result.returncode != 0:
        reject("window-git-failed", " ".join(args[:3]) + ": " + result.stderr.decode("utf-8", "replace").strip())
    return result


# Objects named by a full commit id are immutable (replace refs are disabled), so a repeated read of the same
# (repository, commit, path) or commit pair cannot change. The cache keeps the process count low on slow hosts.
_IMMUTABLE_CACHE: dict = {}


def immutable(key: tuple, compute):
    if key not in _IMMUTABLE_CACHE:
        _IMMUTABLE_CACHE[key] = compute()
    return _IMMUTABLE_CACHE[key]


def resolve_commit(repo: Path, value: str, label: str) -> str:
    """A resolved immutable commit: 40 lowercase hex that names an existing commit; never a ref or HEAD."""
    if type(value) is not str or SHA1.fullmatch(value) is None:
        reject("window-rev-malformed", f"{label} must be a full 40-hex commit, not a ref")
    def probe() -> bool:
        result = git(repo, "cat-file", "-t", value + "^{commit}", check=False)
        return result.returncode == 0 and result.stdout.strip() == b"commit"
    if not immutable(("commit", str(repo), value), probe):
        reject("window-rev-unknown", f"{label} {value[:12]} is not a commit in this repository")
    return value


def relative_path(value: object, label: str) -> str:
    if (type(value) is not str or not value or len(value) > 1024 or "\0" in value or "\\" in value or
            value.startswith("/") or re.match(r"^[A-Za-z]:", value) or
            any(part in ("", ".", "..") for part in value.split("/"))):
        reject("window-path-invalid", f"{label} is not a safe repository-relative path")
    return value


def git_blob(repo: Path, commit: str, path: str, limit: int = MAX_BLOB_BYTES) -> bytes | None:
    """The exact blob bytes at a commit, or None when the path is absent there."""
    name = f"{commit}:{relative_path(path, 'path')}"

    def read() -> bytes | None:
        size = git(repo, "cat-file", "-s", name, check=False)
        if size.returncode != 0:
            return None
        count = int(size.stdout.strip() or b"-1")
        if count < 0 or count > limit:
            reject("window-blob-too-large", path)
        blob = git(repo, "cat-file", "blob", name)
        if len(blob.stdout) != count:
            reject("window-git-failed", f"short read of {path}")
        return blob.stdout
    return immutable(("blob", str(repo), commit, path, limit), read)


def unique_pairs(pairs: list) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            reject("window-record-invalid", f"duplicate JSON key {key}")
        result[key] = value
    return result


def parse_record(raw: bytes) -> dict:
    if len(raw) > MAX_RECORD_BYTES:
        reject("window-record-invalid", "record exceeds the bounded size")
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=unique_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        reject("window-record-invalid", f"not strict UTF-8 JSON: {error}")
    if type(value) is not dict:
        reject("window-record-invalid", "record root must be an object")
    return value


def exact_keys(value: object, expected: set, label: str) -> dict:
    if type(value) is not dict:
        reject("window-record-invalid", f"{label} must be an object")
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing:
        reject("window-record-invalid", f"{label} omits {','.join(missing)}")
    if unknown:
        reject("window-record-invalid", f"{label} has unclassified field {','.join(unknown)}")
    return value


def digest_map(value: object, label: str) -> dict:
    if type(value) is not dict or not value:
        reject("window-record-invalid", f"{label} must be a non-empty object")
    for path, hexdigest in value.items():
        relative_path(path, label)
        if type(hexdigest) is not str or SHA256.fullmatch(hexdigest) is None:
            reject("window-record-invalid", f"{label} digest for {path} is not SHA-256")
    return value


def positive_int(value: object, label: str) -> int:
    if type(value) is not int or value < 1:
        reject("window-record-invalid", f"{label} must be a positive integer")
    return value


def validate_record_shape(record: dict) -> str:
    """Static shape and state rules; returns the state. No revision is consulted."""
    exact_keys(record, TOP_KEYS, "record")
    if record["schema_version"] != 1 or type(record["schema_version"]) is not int:
        reject("window-record-invalid", "schema_version must be 1")
    if record["kind"] != "release-version-window":
        reject("window-record-invalid", "kind must be release-version-window")
    state = record["state"]
    if state == "inactive":
        claimed = sorted(key for key in NULLABLE if record[key] is not None)
        if claimed:
            reject("window-inactive-claims-freeze", "an inactive record may not carry " + ",".join(claimed))
        return "inactive"
    if state != "active":
        reject("window-record-invalid", "state must be inactive or active")
    missing = sorted(key for key in NULLABLE if record[key] is None)
    if missing:
        reject("window-record-invalid", "an active record omits " + ",".join(missing))
    if type(record["release_version"]) is not str or VERSION.fullmatch(record["release_version"]) is None:
        reject("window-record-invalid", "release_version must be X.Y.Z")
    intended = exact_keys(record["intended"], {"head", "base"}, "intended")
    for key in ("head", "base"):
        if type(intended[key]) is not str or SHA1.fullmatch(intended[key]) is None:
            reject("window-record-invalid", f"intended.{key} must be a full 40-hex commit")
    inputs = digest_map(record["managed_inputs"], "managed_inputs")
    for path in REQUIRED_MANAGED_INPUTS:
        if path not in inputs:
            reject("window-input-missing", f"managed_inputs omits the generator input {path}")
    generated = exact_keys(record["generated"], {"files", "pr_body_sha256"}, "generated")
    files = digest_map(generated["files"], "generated.files")
    for path in (*REQUIRED_GENERATED_FILES, f"docs/support/v{record['release_version']}.md"):
        if path not in files:
            reject("window-generated-missing", f"generated.files omits {path}")
    if type(generated["pr_body_sha256"]) is not str or SHA256.fullmatch(generated["pr_body_sha256"]) is None:
        reject("window-record-invalid", "generated.pr_body_sha256 is not SHA-256")
    review = exact_keys(record["review"], {"head", "pull_request", "ci_run_id"}, "review")
    positive_int(review["pull_request"], "review.pull_request")
    positive_int(review["ci_run_id"], "review.ci_run_id")
    rehearsal = exact_keys(record["rehearsal"], {"head", "ref", "run_id"}, "rehearsal")
    positive_int(rehearsal["run_id"], "rehearsal.run_id")
    for label, section in (("review", review), ("rehearsal", rehearsal)):
        if type(section["head"]) is not str or SHA1.fullmatch(section["head"]) is None:
            reject("window-record-invalid", f"{label}.head must be a full 40-hex commit")
    return "active"


def tree_version(repo: Path, commit: str) -> str:
    cmake = git_blob(repo, commit, "CMakeLists.txt")
    manifest = git_blob(repo, commit, ".release-please-manifest.json")
    if cmake is None or manifest is None:
        reject("window-version-mismatch", "CMakeLists.txt or .release-please-manifest.json is absent at the revision")
    match = re.search(rb"^project\(\s*\w+\s+VERSION\s+(\d+\.\d+\.\d+)[\s)]", cmake, re.M)
    try:
        listed = json.loads(manifest.decode("utf-8"), object_pairs_hook=unique_pairs).get(".")
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        listed = None
    if match is None or listed != match.group(1).decode("ascii"):
        reject("window-version-mismatch", "the tree's CMake and release-please manifest versions disagree")
    return listed


def classify(path: str) -> str:
    if path.startswith(("src/", "include/", "fixtures/")) or path == "CMakeLists.txt":
        return "source"
    if path == "CHANGELOG.md" or path.startswith("docs/support/") or path == "docs/release.md":
        return "release-note"
    if path in REQUIRED_MANAGED_INPUTS or path == ".release-please-manifest.json":
        return "generator-input"
    if path.startswith(".github/"):
        return "workflow"
    if path.startswith("tests/"):
        return "tests"
    return "other"


def changed_paths(repo: Path, older: str, newer: str) -> list[str]:
    def compute() -> list[str]:
        output = git(repo, "diff", "--name-only", "-z", "--no-renames", older, newer).stdout
        return [name.decode("utf-8", "replace") for name in output.split(b"\0") if name]
    return immutable(("diff", str(repo), older, newer), compute)


def is_ancestor(repo: Path, older: str, newer: str) -> bool:
    return immutable(("ancestor", str(repo), older, newer),
                     lambda: git(repo, "merge-base", "--is-ancestor", older, newer, check=False).returncode == 0)


def check_window(repo: Path, rev: str, base: str, record_path: str, body: bytes | None) -> str:
    """Judge the record committed at rev. Returns a one-line verdict or raises WindowError."""
    rev = resolve_commit(repo, rev, "--rev")
    base = resolve_commit(repo, base, "--base")
    record_path = relative_path(record_path, "--check")
    raw = git_blob(repo, rev, record_path, MAX_RECORD_BYTES + 1)
    if raw is None:
        reject("window-record-missing", f"{record_path} is not in the tree at {rev[:12]}")
    record = parse_record(raw)
    if validate_record_shape(record) == "inactive":
        return f"version-window inactive pass rev={rev[:12]} (normal development; no frozen content)"

    version = record["release_version"]
    intended = record["intended"]
    head = intended["head"]
    # The reviewed identity is one exact head: review and rehearsal must name it, the rehearsal ref its version.
    if record["review"]["head"] != head:
        reject("window-review-stale", "the recorded review is for a different head than the frozen head")
    if record["rehearsal"]["head"] != head or record["rehearsal"]["ref"] != f"rehearsal/v{version}":
        reject("window-rehearsal-stale", "the recorded rehearsal is for a different head or version")
    if intended["base"] != base:
        reject("window-base-moved", f"main moved from {intended['base'][:12]} to {base[:12]}")
    if not is_ancestor(repo, base, rev):
        reject("window-base-not-ancestor", f"--base {base[:12]} is not an ancestor of {rev[:12]}")
    resolve_commit(repo, head, "intended.head")
    if not is_ancestor(repo, head, rev):
        reject("window-stale-head", f"the frozen head {head[:12]} is not an ancestor of {rev[:12]}")
    changes = [path for path in changed_paths(repo, head, rev) if path != record_path]
    if changes:
        shown = ", ".join(f"{classify(path)}:{path}" for path in changes[:6])
        reject("window-stale-head", f"{head[:12]} -> {rev[:12]} changed {len(changes)} path(s) after review: {shown}")
    if tree_version(repo, rev) != version:
        reject("window-version-mismatch", f"the tree at {rev[:12]} is not version {version}")
    for path, expected in sorted(record["managed_inputs"].items()):
        blob = git_blob(repo, rev, path)
        if blob is None or digest(blob) != expected:
            reject("window-input-changed", f"{path} is not the reviewed generator input")
    for path, expected in sorted(record["generated"]["files"].items()):
        blob = git_blob(repo, rev, path)
        if blob is None or digest(blob) != expected:
            reject("window-generated-changed", f"{path} is not the reviewed generated content")
    if body is None:
        reject("window-body-unsupplied", "an active window needs the current version-PR body (--body)")
    if digest(canonical_body(body)) != record["generated"]["pr_body_sha256"]:
        reject("window-body-overwritten", "the version-PR body differs from the reviewed body (regenerated or edited)")
    return (f"version-window active pass version={version} head={head[:12]} rev={rev[:12]} "
            f"inputs={len(record['managed_inputs'])} generated={len(record['generated']['files'])}")


def draft_record(repo: Path, rev: str, base: str, body: bytes | None, pull_request: int | None,
                 ci_run_id: int | None, rehearsal_run_id: int | None) -> dict:
    """Recompute every content digest at rev; this is how a closed window is reopened."""
    rev = resolve_commit(repo, rev, "--rev")
    base = resolve_commit(repo, base, "--base")
    version = tree_version(repo, rev)
    inputs: dict = {}
    for path in REQUIRED_MANAGED_INPUTS:
        blob = git_blob(repo, rev, path)
        if blob is None:
            reject("window-input-missing", f"{path} is absent at {rev[:12]}")
        inputs[path] = digest(blob)
    files: dict = {}
    for path in (*REQUIRED_GENERATED_FILES, f"docs/support/v{version}.md"):
        blob = git_blob(repo, rev, path)
        if blob is None:
            reject("window-generated-missing", f"{path} is absent at {rev[:12]}")
        files[path] = digest(blob)
    return {
        "schema_version": 1,
        "kind": "release-version-window",
        "state": "active",
        "release_version": version,
        "intended": {"head": rev, "base": base},
        "managed_inputs": dict(sorted(inputs.items())),
        "generated": {"files": dict(sorted(files.items())),
                      "pr_body_sha256": digest(canonical_body(body)) if body is not None else None},
        "review": {"head": rev, "pull_request": pull_request, "ci_run_id": ci_run_id},
        "rehearsal": {"head": rev, "ref": f"rehearsal/v{version}", "run_id": rehearsal_run_id},
    }


def render_record(record: dict) -> bytes:
    return (json.dumps(record, indent=2, sort_keys=False, ensure_ascii=False) + "\n").encode("utf-8")


def read_body(path: Path | None) -> bytes | None:
    if path is None:
        return None
    try:
        if path.stat().st_size > MAX_BODY_BYTES:
            reject("window-body-too-large", str(path.name))
        return path.read_bytes()
    except OSError as error:
        reject("window-body-unreadable", str(error))


def check_tracked(repo: Path, rev: str | None = None, require_active: bool = False) -> str:
    """Contract: the tracked record is well-formed and the production constants resolve in the tree."""
    if rev is None:
        head = git(repo, "rev-parse", "--verify", "HEAD^{commit}").stdout.decode("ascii").strip()
        head = resolve_commit(repo, head, "HEAD")
    else:
        head = resolve_commit(repo, rev, "--rev")
    raw = git_blob(repo, head, RECORD_PATH, MAX_RECORD_BYTES + 1)
    if raw is None:
        reject("window-record-missing", f"{RECORD_PATH} is not tracked")
    record = parse_record(raw)
    state = validate_record_shape(record)
    if state == "inactive" and require_active:
        reject("window-record-inactive", f"{RECORD_PATH} is inactive at revision {head[:12]}")
    if state == "active" and tree_version(repo, head) != record["release_version"]:
        reject("window-version-mismatch", f"the active record's version {record['release_version']} differs from the tree at {head[:12]}")
    for path in (*REQUIRED_MANAGED_INPUTS, *REQUIRED_GENERATED_FILES):
        if git_blob(repo, head, path) is None:
            reject("window-input-missing", f"the window requires {path}, which is not in the tree")
    return f"version-window contract pass state={state} rev={head[:12]} inputs={len(REQUIRED_MANAGED_INPUTS)}"


# --- self-test: disposable repositories, never the live tree -------------------------------------------------

FIXTURE_IDENTITY = {
    "GIT_AUTHOR_NAME": "Window Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
    "GIT_COMMITTER_NAME": "Window Fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
}


class Fixture:
    """A disposable repository holding a stand-in version-PR tree."""

    def __init__(self, directory: Path) -> None:
        self.repo = directory
        self.env = {**os.environ, **FIXTURE_IDENTITY}
        self.run("init", "-q", "-b", "main")
        self.run("config", "core.autocrlf", "false")

    def run(self, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=self.repo, env=self.env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30)
        if result.returncode != 0:
            raise AssertionError("fixture git " + " ".join(args) + ": " + result.stderr.decode("utf-8", "replace"))
        return result.stdout.decode("utf-8").strip()

    def write(self, path: str, content: str | bytes) -> None:
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))

    def reset(self, commit: str) -> None:
        # Move the version-PR branch to an existing commit and its tree (disposable repository only).
        self.run("checkout", "-q", "-B", "release-please--branches--main", commit)

    def commit(self, message: str, *paths: str) -> str:
        self.run("add", "--", *paths)
        self.run("commit", "-q", "-m", message)
        return self.run("rev-parse", "HEAD")


def build_fixture(directory: Path) -> tuple[Fixture, str, str, bytes]:
    """Returns (fixture, main base commit, reviewed version-PR head, reviewed PR body)."""
    fx = Fixture(directory)
    fx.write("CMakeLists.txt", "project(GabbaBoy VERSION 0.2.1 LANGUAGES C) # x-release-please-version\n")
    fx.write(".release-please-manifest.json", '{\n  ".": "0.2.1"\n}\n')
    fx.write("CHANGELOG.md", "# Changelog\n")
    fx.write("release-please-config.json", '{"release-type": "simple"}\n')
    fx.write("tests/data/release-disclosure.json", '{"schema_version": 1}\n')
    fx.write("tests/data/support-claims-v0.3.json", '{"schema_version": 1, "kind": "scoped-support-claims"}\n')
    fx.write("tests/scripts/verify-support-ledger.py", "# stand-in generator\n")
    fx.write("docs/support/v0.2.1.md", "# v0.2.1 ledger\n")
    fx.write("src/core/gabbaboy.c", "int core(void) { return 0; }\n")
    fx.write(RECORD_PATH, render_record(inactive_record()))
    base = fx.commit("main", "CMakeLists.txt", ".release-please-manifest.json", "CHANGELOG.md",
                     "release-please-config.json", "tests/data/release-disclosure.json",
                     "tests/data/support-claims-v0.3.json",
                     "tests/scripts/verify-support-ledger.py", "docs/support/v0.2.1.md",
                     "src/core/gabbaboy.c", RECORD_PATH)
    fx.run("checkout", "-q", "-b", "release-please--branches--main")
    # The version PR: release-please bumps the version and changelog; the ledger is regenerated.
    fx.write("CMakeLists.txt", "project(GabbaBoy VERSION 0.2.2 LANGUAGES C) # x-release-please-version\n")
    fx.write(".release-please-manifest.json", '{\n  ".": "0.2.2"\n}\n')
    fx.write("CHANGELOG.md", "# Changelog\n\n## 0.2.2\n\n- generated entry\n")
    fx.write("docs/support/v0.2.2.md", "# v0.2.2 ledger\n")
    head = fx.commit("version pr", "CMakeLists.txt", ".release-please-manifest.json", "CHANGELOG.md",
                     "docs/support/v0.2.2.md")
    return fx, base, head, b"## 0.2.2\n\n- generated entry\n"


def inactive_record() -> dict:
    return {"schema_version": 1, "kind": "release-version-window", "state": "inactive",
            "release_version": None, "intended": None, "managed_inputs": None, "generated": None,
            "review": None, "rehearsal": None}


def self_test() -> tuple[int, int]:
    positives = 0
    controls = 0

    def accepted(name: str, action) -> str:
        nonlocal positives
        try:
            verdict = action()
        except WindowError as error:
            raise AssertionError(f"window positive {name} was rejected: {error}") from error
        positives += 1
        return verdict

    def rejected(name: str, action, code: str, detail: str = "") -> None:
        nonlocal controls
        try:
            action()
        except WindowError as error:
            message = str(error)
            if not message.startswith(code) or detail not in message:
                raise AssertionError(f"window control {name} was rejected for the wrong reason: {message}")
        else:
            raise AssertionError(f"window control {name} was accepted")
        controls += 1

    with tempfile.TemporaryDirectory(prefix="gabbaboy-version-window-") as temporary:
        fx, base, head, body = build_fixture(Path(temporary))
        repo = fx.repo

        def freeze(at: str, base_commit: str, pr_body: bytes, **overrides) -> dict:
            record = draft_record(repo, at, base_commit, pr_body, 41, 1001, 2002)
            for key, value in overrides.items():
                record[key] = value
            return record

        def commit_record(record: dict) -> str:
            fx.write(RECORD_PATH, render_record(record))
            return fx.commit("record", RECORD_PATH)

        def check(rev: str, base_commit: str, pr_body: bytes | None = body) -> str:
            return check_window(repo, rev, base_commit, RECORD_PATH, pr_body)

        # Inactive example: normal development passes with no window, and cannot claim a freeze.
        accepted("inactive-example", lambda: check(base, base, None))
        accepted("inactive-example-ignores-body", lambda: check(base, base, b"anything"))

        # A frozen window: generated, reviewed at one exact head, then the record-only commit.
        reviewed = freeze(head, base, body)
        frozen = commit_record(reviewed)
        verdict = accepted("valid-frozen-window", lambda: check(frozen, base))
        if "active pass" not in verdict:
            raise AssertionError("a valid active window did not report an active pass")
        frozen_blob = git_blob(repo, frozen, RECORD_PATH)

        # Immutable revision: a dirty working-tree record is never consulted, and refs are not accepted.
        fx.write(RECORD_PATH, render_record(freeze(head, base, b"forged body")))
        accepted("worktree-record-ignored", lambda: check(frozen, base))
        fx.write(RECORD_PATH, frozen_blob)
        rejected("ref-instead-of-commit", lambda: check_window(repo, "HEAD", base, RECORD_PATH, body),
                 "window-rev-malformed")
        rejected("unknown-commit", lambda: check_window(repo, "0" * 40, base, RECORD_PATH, body),
                 "window-rev-unknown")
        rejected("uppercase-commit", lambda: check_window(repo, frozen.upper(), base, RECORD_PATH, body),
                 "window-rev-malformed")
        rejected("record-absent-at-revision", lambda: check_window(repo, frozen, base, "tests/data/other.json", body),
                 "window-record-missing")
        rejected("absolute-record-path", lambda: check_window(repo, frozen, base, "/etc/passwd", body),
                 "window-path-invalid")

        # Line endings and trailing newlines of the PR body carry no meaning; every other byte does.
        accepted("body-crlf-and-trailing-newline-equivalent",
                 lambda: check(frozen, base, body.replace(b"\n", b"\r\n") + b"\r\n\r\n"))
        rejected("body-one-word-changed", lambda: check(frozen, base, body.replace(b"generated", b"edited")),
                 "window-body-overwritten")

        # Body overwrite: release-please regenerated or a human edited the PR body.
        rejected("body-overwritten", lambda: check(frozen, base, b"## 0.2.2\n\n- regenerated entry\n"),
                 "window-body-overwritten")
        rejected("body-unsupplied", lambda: check(frozen, base, None), "window-body-unsupplied")

        # Main moved: any change to the reviewed base invalidates, even one unrelated to the diff.
        fx.run("checkout", "-q", "main")
        fx.write("README.md", "unrelated\n")
        moved = fx.commit("main moves", "README.md")
        fx.run("checkout", "-q", "release-please--branches--main")
        rejected("main-moved", lambda: check(frozen, moved), "window-base-moved")
        unrelated_record = commit_record({**reviewed, "intended": {"head": head, "base": moved}})
        rejected("base-not-an-ancestor-of-rev", lambda: check(unrelated_record, moved), "window-base-not-ancestor")

        # Stale head: a relevant path changed after review, classified by what it touched.
        fx.reset(frozen)
        fx.write("src/core/gabbaboy.c", "int core(void) { return 1; }\n")
        source_edit = fx.commit("source edit", "src/core/gabbaboy.c")
        rejected("source-change-after-review", lambda: check(source_edit, base), "window-stale-head",
                 "source:src/core/gabbaboy.c")
        fx.reset(frozen)
        fx.write("CHANGELOG.md", "# Changelog\n\n## 0.2.2\n\n- hand edit\n")
        note_edit = fx.commit("release note edit", "CHANGELOG.md")
        rejected("release-note-change-after-review", lambda: check(note_edit, base), "window-stale-head",
                 "release-note:CHANGELOG.md")
        fx.reset(frozen)
        fx.write("tests/data/release-disclosure.json", '{"schema_version": 1, "edited": true}\n')
        input_edit = fx.commit("generator input edit", "tests/data/release-disclosure.json")
        rejected("generator-input-change-after-review", lambda: check(input_edit, base), "window-stale-head",
                 "generator-input:tests/data/release-disclosure.json")

        # Mismatch after regeneration: the head and base are re-recorded but a digest is not recomputed.
        partial = copy.deepcopy(freeze(input_edit, base, body))
        partial["managed_inputs"]["tests/data/release-disclosure.json"] = reviewed["managed_inputs"][
            "tests/data/release-disclosure.json"]
        stale_inputs = commit_record(partial)
        rejected("input-digest-not-recomputed", lambda: check(stale_inputs, base), "window-input-changed",
                 "tests/data/release-disclosure.json")
        fx.reset(frozen)
        fx.write("docs/support/v0.2.2.md", "# v0.2.2 ledger, regenerated\n")
        regenerated = fx.commit("regenerate ledger", "docs/support/v0.2.2.md")
        partial = freeze(regenerated, base, body)
        partial["generated"]["files"]["docs/support/v0.2.2.md"] = reviewed["generated"]["files"][
            "docs/support/v0.2.2.md"]
        stale_ledger = commit_record(partial)
        rejected("ledger-digest-not-recomputed", lambda: check(stale_ledger, base), "window-generated-changed",
                 "docs/support/v0.2.2.md")

        # Valid revalidation: regenerate, recompute every digest, re-review the new exact head, freeze again.
        fx.reset(regenerated)
        revalidated = commit_record(freeze(regenerated, base, body))
        accepted("valid-revalidation-after-regeneration", lambda: check(revalidated, base))

        # Record rules: identities, versions, required inputs and the absence of any clock or readiness field.
        fx.reset(frozen)

        def with_record(record: dict) -> str:
            return commit_record(record)

        review_stale = with_record({**reviewed, "review": {**reviewed["review"], "head": base}})
        rejected("review-for-another-head", lambda: check(review_stale, base), "window-review-stale")
        fx.reset(frozen)
        rehearsal_stale = with_record({**reviewed, "rehearsal": {**reviewed["rehearsal"], "head": base}})
        rejected("rehearsal-for-another-head", lambda: check(rehearsal_stale, base), "window-rehearsal-stale")
        fx.reset(frozen)
        rehearsal_ref = with_record({**reviewed, "rehearsal": {**reviewed["rehearsal"], "ref": "rehearsal/v0.2.9"}})
        rejected("rehearsal-for-another-version", lambda: check(rehearsal_ref, base), "window-rehearsal-stale")
        fx.reset(frozen)
        wrong_version = with_record({**reviewed, "release_version": "0.2.9",
                                     "generated": {**reviewed["generated"], "files": {
                                         **reviewed["generated"]["files"],
                                         "docs/support/v0.2.9.md": reviewed["generated"]["files"][
                                             "docs/support/v0.2.2.md"]}},
                                     "rehearsal": {**reviewed["rehearsal"], "ref": "rehearsal/v0.2.9"}})
        rejected("record-for-another-version", lambda: check(wrong_version, base), "window-version-mismatch")
        fx.reset(frozen)
        for omitted_input in REQUIRED_MANAGED_INPUTS:
            fx.reset(frozen)
            dropped_input = copy.deepcopy(reviewed)
            del dropped_input["managed_inputs"][omitted_input]
            rejected("generator-input-omitted-" + Path(omitted_input).name,
                     lambda: check(with_record(dropped_input), base), "window-input-missing",
                     omitted_input)
        fx.reset(frozen)
        with_clock = {**reviewed, "expires_at": "2026-12-31T00:00:00Z"}
        rejected("clock-field-rejected", lambda: check(with_record(with_clock), base), "window-record-invalid",
                 "unclassified field expires_at")
        fx.reset(frozen)
        without_review = {key: value for key, value in reviewed.items() if key != "review"}
        rejected("review-identity-omitted", lambda: check(with_record(without_review), base),
                 "window-record-invalid", "omits review")
        fx.reset(frozen)
        fx.write(RECORD_PATH, b'{"schema_version": 1, "schema_version": 1}')
        duplicate = fx.commit("duplicate key", RECORD_PATH)
        rejected("duplicate-json-key", lambda: check(duplicate, base), "window-record-invalid", "duplicate JSON key")
        fx.reset(frozen)

        # An inactive example can never assert release readiness or carry a frozen identity.
        claims = {**inactive_record(), "intended": reviewed["intended"]}
        rejected("inactive-claims-freeze", lambda: check(with_record(claims), base), "window-inactive-claims-freeze")
        fx.reset(frozen)
        ready = {**inactive_record(), "release_ready": True}
        rejected("inactive-asserts-readiness", lambda: check(with_record(ready), base), "window-record-invalid",
                 "unclassified field release_ready")
        fx.reset(frozen)

        # The tracked-record contract resolves the production constants in a tree.
        fx.reset(base)
        accepted("tracked-contract", lambda: check_tracked(repo))
        fx.reset(frozen)
        accepted("tracked-active-contract", lambda: check_tracked(repo, frozen))
        fx.write("CMakeLists.txt", "project(GabbaBoy VERSION 0.2.3 LANGUAGES C) # x-release-please-version\n")
        fx.write(".release-please-manifest.json", '{\n  ".": "0.2.3"\n}\n')
        bumped_with_old_record = fx.commit("bump tree with an old active record", "CMakeLists.txt",
                                           ".release-please-manifest.json")
        rejected("tracked-active-record-version-mismatch",
                 lambda: check_tracked(repo, bumped_with_old_record), "window-version-mismatch")
        fx.reset(base)
        rejected("tracked-inactive-requires-active", lambda: check_tracked(repo, base, require_active=True),
                 "window-record-inactive")
        fx.reset(base)
        fx.run("rm", "-q", "release-please-config.json")
        fx.run("commit", "-q", "-m", "drop a managed input")
        rejected("tracked-contract-input-removed", lambda: check_tracked(repo), "window-input-missing")

        # The CLI reads the same objects: the exact process the workflow runs, over the frozen head.
        def cli(*arguments: str) -> subprocess.CompletedProcess:
            return subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "--repo", str(repo),
                                   *arguments], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, check=False, timeout=60)

        body_file = Path(temporary) / "body.md"
        body_file.write_bytes(body)
        fx.reset(frozen)
        tracked_active = cli("--check-tracked", "--rev", frozen)
        if tracked_active.returncode != 0 or f"version-window contract pass state=active rev={frozen[:12]}" not in tracked_active.stdout:
            raise AssertionError("CLI rejected the active tracked record at its immutable revision: "
                                 + tracked_active.stdout + tracked_active.stderr)
        positives += 1
        fx.reset(base)
        tracked_inactive = cli("--check-tracked", "--rev", base, "--require-active")
        if tracked_inactive.returncode != 1 or "window-record-inactive" not in tracked_inactive.stderr:
            raise AssertionError("CLI accepted --require-active on an inactive tracked record: "
                                 + tracked_inactive.stdout + tracked_inactive.stderr)
        controls += 1
        fx.reset(frozen)
        ok = cli("--rev", frozen, "--base", base, "--check", RECORD_PATH, "--body", str(body_file))
        if ok.returncode != 0 or "active pass" not in ok.stdout:
            raise AssertionError("CLI rejected the valid window: " + ok.stdout + ok.stderr)
        positives += 1
        body_file.write_bytes(b"overwritten\n")
        bad = cli("--rev", frozen, "--base", base, "--check", RECORD_PATH, "--body", str(body_file))
        if bad.returncode != 1 or "window-body-overwritten" not in bad.stderr:
            raise AssertionError("CLI accepted an overwritten body: " + bad.stdout + bad.stderr)
        controls += 1
    return positives, controls


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rev", help="resolved 40-hex commit whose tree and record are judged")
    parser.add_argument("--base", help="resolved 40-hex main commit the window was reviewed against")
    parser.add_argument("--check", metavar="RECORD", help="repository-relative record path, read from --rev")
    parser.add_argument("--digest", action="store_true", help="print a freshly digested draft record for --rev")
    parser.add_argument("--body", type=Path, help="the current version-PR body bytes")
    parser.add_argument("--pull-request", type=int)
    parser.add_argument("--ci-run-id", type=int)
    parser.add_argument("--rehearsal-run-id", type=int)
    parser.add_argument("--check-tracked", action="store_true")
    parser.add_argument("--require-active", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--repo", type=Path, default=ROOT, help="repository to read (default: this checkout)")
    args = parser.parse_args()
    try:
        if args.self_test:
            positives, controls = self_test()
            print(f"version-window controls pass positives={positives} controls={controls}")
            return 0
        if args.check_tracked:
            print(check_tracked(args.repo, args.rev, args.require_active))
            return 0
        if args.require_active:
            parser.error("--require-active requires --check-tracked")
        if args.digest:
            if not (args.rev and args.base):
                parser.error("--digest requires --rev and --base")
            record = draft_record(args.repo, args.rev, args.base, read_body(args.body), args.pull_request,
                                  args.ci_run_id, args.rehearsal_run_id)
            sys.stdout.write(render_record(record).decode("utf-8"))
            return 0
        if args.check:
            if not (args.rev and args.base):
                parser.error("--check requires --rev and --base")
            print(check_window(args.repo, args.rev, args.base, args.check, read_body(args.body)))
            return 0
        parser.error("supply --check, --digest, --check-tracked or --self-test")
    except WindowError as error:
        print("version-window rejected: " + str(error), file=sys.stderr)
        return 1
    except AssertionError as error:
        print("version-window self-test failed: " + str(error), file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
