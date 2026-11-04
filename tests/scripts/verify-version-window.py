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
    "tests/data/support-claims-v0.4.json",
    "tests/scripts/verify-support-ledger.py",
    "tests/scripts/verify-v02-adoption.py",
    "release-please-config.json",
    "tests/data/cgb-candidates/potion-panic.json",
    "tests/data/cgb-candidates/ucity-1.3.json",
    "tests/external/diagnostic-assessment.json",
    "tests/external/gbmicrotest-inventory.json",
    "tests/baseline/state-goldens-v1.json",
    "tests/data/state-compatibility.json",
)
# Regenerated outputs of the version PR (the ledger path is derived from the version).
REQUIRED_GENERATED_FILES = ("CMakeLists.txt", "CHANGELOG.md", ".release-please-manifest.json")

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
    unclassified_inputs = sorted(set(inputs) - set(REQUIRED_MANAGED_INPUTS))
    if unclassified_inputs:
        reject("window-record-invalid", f"managed_inputs has unclassified input {unclassified_inputs[0]}")
    generated = exact_keys(record["generated"], {"files", "pr_body_sha256"}, "generated")
    files = digest_map(generated["files"], "generated.files")
    expected_generated = {*REQUIRED_GENERATED_FILES, f"docs/support/v{record['release_version']}.md"}
    for path in sorted(expected_generated):
        if path not in files:
            reject("window-generated-missing", f"generated.files omits {path}")
    unclassified_generated = sorted(set(files) - expected_generated)
    if unclassified_generated:
        reject("window-record-invalid", f"generated.files has unclassified output {unclassified_generated[0]}")
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


def validate_version_outputs(repo: Path, commit: str, expected_version: str) -> None:
    """Check exact generated identity and its first public changelog section at an immutable revision."""
    actual_version = tree_version(repo, commit)
    if actual_version != expected_version:
        reject("window-version-mismatch", f"the requested version is {expected_version}, but the tree is {actual_version}")

    ledger_path = f"docs/support/v{expected_version}.md"
    ledger = git_blob(repo, commit, ledger_path)
    expected_heading = f"# GabbaBoy v{expected_version} support ledger".encode("utf-8")
    if ledger is None or not ledger.splitlines() or ledger.splitlines()[0] != expected_heading:
        reject("window-version-output-mismatch", f"{ledger_path} is absent or has the wrong version heading")

    changelog = git_blob(repo, commit, "CHANGELOG.md")
    if changelog is None:
        reject("window-version-output-mismatch", "CHANGELOG.md is absent")
    try:
        text = changelog.decode("utf-8")
    except UnicodeDecodeError:
        reject("window-version-output-mismatch", "CHANGELOG.md is not UTF-8")
    visible = visible_markdown(text)
    sections = list(re.finditer(r"(?m)^## \[(\d+\.\d+\.\d+)\](?:\([^\r\n]*\))?[^\r\n]*$", visible))
    if not sections or sections[0].group(1) != expected_version:
        found = sections[0].group(1) if sections else "none"
        reject("window-version-output-mismatch", f"the first changelog release section is {found}, expected {expected_version}")
    first = sections[0]
    end = sections[1].start() if len(sections) > 1 else len(visible)
    section = visible[first.end():end]
    canonical_ledger = f"https://github.com/szTheory/gabbaboy/blob/v{expected_version}/{ledger_path}"
    destination = r"(?:" + re.escape(ledger_path) + r"|" + re.escape(canonical_ledger) + r")"
    ledger_link = re.compile(r"(?<![!\\])\[[^\]\n]*\]\(\s*" + destination + r"\s*\)")
    if ledger_link.search(section) is None:
        reject("window-version-output-mismatch", f"the {expected_version} changelog section does not link {ledger_path}")


def visible_markdown(text: str) -> str:
    """Mask comments, code blocks, and inline code while preserving source offsets."""
    def mask(match: re.Match[str]) -> str:
        return "".join("\n" if char == "\n" else "\r" if char == "\r" else " "
                       for char in match.group(0))

    text = re.sub(r"<!--.*?(?:-->|\Z)", mask, text, flags=re.DOTALL)
    text = mask_fenced_code_blocks(text)
    text = re.sub(r"(?m)^(?: {4}|\t)[^\r\n]*", mask, text)
    return mask_inline_code_spans(text)


def mask_fenced_code_blocks(text: str) -> str:
    """Mask CommonMark fenced blocks, including blockquote containers."""
    output: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    fence_quote_depth = 0

    def quote_prefix(content: str, limit: int | None = None) -> tuple[int, int]:
        depth = 0
        position = 0
        while limit is None or depth < limit:
            start = position
            spaces = 0
            while position < len(content) and content[position] == " " and spaces < 4:
                position += 1
                spaces += 1
            if spaces > 3 or position >= len(content) or content[position] != ">":
                position = start
                break
            depth += 1
            position += 1
            if position < len(content) and content[position] in " \t":
                position += 1
        return depth, position

    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        ending = line[len(content):]
        if fence_char is not None:
            depth, position = quote_prefix(content, fence_quote_depth)
            if depth == fence_quote_depth:
                candidate = content[position:]
                closing = re.match(r"^ {0,3}([`~]+)[ \t]*$", candidate)
                closes = (closing is not None and closing.group(1)[0] == fence_char
                          and len(closing.group(1)) >= fence_length
                          and all(char == fence_char for char in closing.group(1)))
                output.append(" " * len(content) + ending)
                if closes:
                    fence_char = None
                    fence_length = 0
                    fence_quote_depth = 0
                continue
            fence_char = None
            fence_length = 0
            fence_quote_depth = 0

        depth, position = quote_prefix(content)
        candidate = content[position:]
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", candidate)
        if opening and not (opening.group(1)[0] == "`" and "`" in opening.group(2)):
            fence_char = opening.group(1)[0]
            fence_length = len(opening.group(1))
            fence_quote_depth = depth
            output.append(" " * len(content) + ending)
        else:
            output.append(line)
    return "".join(output)


def mask_inline_code_spans(text: str) -> str:
    """Mask CommonMark backtick spans, including multiline spans, without moving offsets."""
    tick = chr(96)
    chars = list(text)
    runs: list[tuple[int, int, int, bool]] = []
    index = 0
    length = len(text)
    while index < length:
        if text[index] != tick:
            index += 1
            continue
        opening = index
        while index < length and text[index] == tick:
            index += 1
        delimiter = index - opening
        backslashes = 0
        cursor = opening - 1
        while cursor >= 0 and text[cursor] == "\\":
            backslashes += 1
            cursor -= 1
        runs.append((opening, index, delimiter, backslashes % 2 == 1))

    next_same: list[int | None] = [None] * len(runs)
    next_by_length: dict[int, int] = {}
    for run_index in range(len(runs) - 1, -1, -1):
        delimiter = runs[run_index][2]
        next_same[run_index] = next_by_length.get(delimiter)
        next_by_length[delimiter] = run_index

    run_index = 0
    while run_index < len(runs):
        opening, _, _, escaped = runs[run_index]
        closing_index = next_same[run_index]
        if escaped or closing_index is None:
            run_index += 1
            continue
        end = runs[closing_index][1]
        for offset in range(opening, end):
            if chars[offset] not in ("\n", "\r"):
                chars[offset] = " "
        run_index = closing_index + 1
        while run_index < len(runs) and runs[run_index][0] < end:
            run_index += 1
    return "".join(chars)

def check_release_notes(repo: Path, rev: str, release_notes: Path) -> None:
    """Delegate supplied notes to the established immutable release-notes judge."""
    script = ROOT / "tests/scripts/verify-v02-adoption.py"
    try:
        result = subprocess.run(
            [sys.executable, "-I", str(script), "--release-notes", str(release_notes),
             "--root", str(repo), "--repo", str(repo), "--rev", rev],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, check=False, timeout=90,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        reject("window-release-notes-invalid", f"the existing release-notes judge could not complete: {error}")
    if result.returncode != 0:
        detail = (result.stdout + result.stderr).strip().splitlines()
        reject("window-release-notes-invalid", detail[-1] if detail else "the existing release-notes judge rejected the notes")


def classify(path: str) -> str:
    if path in REQUIRED_GENERATED_FILES or path.startswith("docs/support/"):
        return "release-output"
    if path.startswith(("src/", "include/", "fixtures/")):
        return "source"
    if path == "docs/release.md":
        return "release-note"
    if path in REQUIRED_MANAGED_INPUTS:
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


def check_window(repo: Path, rev: str, base: str, record_path: str, body: bytes | None,
                 expected_version: str | None = None) -> str:
    """Judge the record committed at rev. Returns a one-line verdict or raises WindowError."""
    rev = resolve_commit(repo, rev, "--rev")
    base = resolve_commit(repo, base, "--base")
    record_path = relative_path(record_path, "--check")
    raw = git_blob(repo, rev, record_path, MAX_RECORD_BYTES + 1)
    if raw is None:
        reject("window-record-missing", f"{record_path} is not in the tree at {rev[:12]}")
    record = parse_record(raw)
    if validate_record_shape(record) == "inactive":
        if expected_version is not None:
            reject("window-record-inactive", "an explicit expected-version window requires an active record")
        return f"version-window inactive pass rev={rev[:12]} (normal development; no frozen content)"

    version = record["release_version"]
    if expected_version is not None and version != expected_version:
        reject("window-version-mismatch", f"the active record names {version}, expected {expected_version}")
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
    if expected_version is not None:
        validate_version_outputs(repo, rev, expected_version)
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


def check_tracked(repo: Path, rev: str | None = None, require_active: bool = False,
                  expected_version: str | None = None) -> str:
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
    version = tree_version(repo, head)
    if expected_version is not None and version != expected_version:
        reject("window-version-mismatch", f"the requested version is {expected_version}, but the tree at {head[:12]} is {version}")
    if state == "active" and version != record["release_version"]:
        reject("window-version-mismatch", f"the active record's version {record['release_version']} differs from the tree at {head[:12]}")
    if expected_version is not None and state == "active" and record["release_version"] != expected_version:
        reject("window-version-mismatch", f"the active record names {record['release_version']}, expected {expected_version}")
    if expected_version is not None:
        validate_version_outputs(repo, head, expected_version)
    required_paths = (*REQUIRED_MANAGED_INPUTS, *REQUIRED_GENERATED_FILES, f"docs/support/v{version}.md")
    for path in required_paths:
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


def build_fixture(directory: Path, main_version: str = "0.2.1",
                  release_version: str = "0.2.2") -> tuple[Fixture, str, str, bytes]:
    """Returns (fixture, main base commit, reviewed version-PR head, reviewed PR body)."""
    fx = Fixture(directory)
    fx.write("CMakeLists.txt", f"project(GabbaBoy VERSION {main_version} LANGUAGES C) # x-release-please-version\n")
    fx.write(".release-please-manifest.json", json.dumps({".": main_version}, indent=2) + "\n")
    fx.write("CHANGELOG.md", f"# Changelog\n\n## [{main_version}]\n\n- Support: [ledger](docs/support/v{main_version}.md).\n")
    for path in REQUIRED_MANAGED_INPUTS:
        fx.write(path, f"fixture input: {path}\n")
    fx.write("docs/support/v" + main_version + ".md", f"# GabbaBoy v{main_version} support ledger\n")
    fx.write("src/core/gabbaboy.c", "int core(void) { return 0; }\n")
    fx.write(RECORD_PATH, render_record(inactive_record()))
    base = fx.commit("main", "CMakeLists.txt", ".release-please-manifest.json", "CHANGELOG.md",
                     *REQUIRED_MANAGED_INPUTS, "docs/support/v" + main_version + ".md",
                     "src/core/gabbaboy.c", RECORD_PATH)
    fx.run("checkout", "-q", "-b", "release-please--branches--main")
    # The version PR: release-please bumps the version and changelog; the ledger is regenerated.
    fx.write("CMakeLists.txt", f"project(GabbaBoy VERSION {release_version} LANGUAGES C) # x-release-please-version\n")
    fx.write(".release-please-manifest.json", json.dumps({".": release_version}, indent=2) + "\n")
    fx.write("CHANGELOG.md", f"# Changelog\n\n## [{release_version}]\n\n- Support: [ledger](docs/support/v{release_version}.md).\n- generated entry\n")
    fx.write("docs/support/v" + release_version + ".md",
             f"# GabbaBoy v{release_version} support ledger\n")
    head = fx.commit("version pr", "CMakeLists.txt", ".release-please-manifest.json", "CHANGELOG.md",
                     "docs/support/v" + release_version + ".md")
    return fx, base, head, f"## {release_version}\n\n- generated entry\n".encode("utf-8")


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
        for path in REQUIRED_GENERATED_FILES:
            fx.reset(frozen)
            original = git_blob(repo, head, path)
            if original is None:
                raise AssertionError(f"fixture omitted generated output {path}")
            fx.write(path, original + b"\nregenerated\n")
            output_edit = fx.commit("generated output edit", path)
            rejected("generated-output-change-after-review-" + Path(path).name,
                     lambda output_edit=output_edit: check(output_edit, base), "window-stale-head",
                     f"release-output:{path}")
        fx.reset(frozen)
        fx.write("docs/support/v0.2.2.md", "# v0.2.2 ledger, hand edited\n")
        ledger_edit = fx.commit("release ledger edit", "docs/support/v0.2.2.md")
        rejected("release-ledger-change-after-review", lambda: check(ledger_edit, base), "window-stale-head",
                 "release-output:docs/support/v0.2.2.md")
        fx.reset(frozen)
        fx.write("CMakeLists.txt", "project(GabbaBoy VERSION 0.2.3 LANGUAGES C) # x-release-please-version\n")
        cmake_version_edit = fx.commit("generated CMake version edit", "CMakeLists.txt")
        rejected("generated-cmake-version-change-after-review", lambda: check(cmake_version_edit, base),
                 "window-stale-head", "release-output:CMakeLists.txt")
        for path in REQUIRED_MANAGED_INPUTS:
            fx.reset(frozen)
            original = git_blob(repo, head, path)
            if original is None:
                raise AssertionError(f"fixture omitted managed input {path}")
            fx.write(path, original + b"\nchanged\n")
            input_edit = fx.commit("generator input edit", path)
            rejected("generator-input-change-after-review-" + Path(path).name,
                     lambda input_edit=input_edit: check(input_edit, base), "window-stale-head",
                     f"generator-input:{path}")

        # Mismatch after regeneration: the head and base are re-recorded but a digest is not recomputed.
        fx.reset(frozen)
        fx.write("tests/data/release-disclosure.json", b"edited disclosure input\n")
        input_edit = fx.commit("generator input edit", "tests/data/release-disclosure.json")
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

        # The v0.4 claim profile must remain an individually required input, even when its
        # current bytes and the generated ledger digest are otherwise internally consistent.
        profile_path = "tests/data/support-claims-v0.4.json"
        profile_blob = git_blob(repo, head, profile_path)
        if profile_blob is None:
            raise AssertionError("fixture omitted the v0.4 claim profile")
        profile_bound = copy.deepcopy(reviewed)
        profile_bound["managed_inputs"].setdefault(profile_path, digest(profile_blob))
        fx.reset(frozen)
        bound_profile = frozen if profile_bound == reviewed else with_record(profile_bound)
        accepted("v04-profile-explicitly-bound", lambda: check(bound_profile, base))
        profile_omitted = copy.deepcopy(profile_bound)
        del profile_omitted["managed_inputs"][profile_path]
        fx.reset(bound_profile)
        rejected("v04-profile-omitted", lambda: check(with_record(profile_omitted), base),
                 "window-input-missing", profile_path)
        fx.reset(frozen)

        review_stale = with_record({**reviewed, "review": {**reviewed["review"], "head": base}})
        rejected("review-for-another-head", lambda: check(review_stale, base), "window-review-stale")
        fx.reset(frozen)
        rehearsal_stale = with_record({**reviewed, "rehearsal": {**reviewed["rehearsal"], "head": base}})
        rejected("rehearsal-for-another-head", lambda: check(rehearsal_stale, base), "window-rehearsal-stale")
        fx.reset(frozen)
        rehearsal_ref = with_record({**reviewed, "rehearsal": {**reviewed["rehearsal"], "ref": "rehearsal/v0.2.9"}})
        rejected("rehearsal-for-another-version", lambda: check(rehearsal_ref, base), "window-rehearsal-stale")
        fx.reset(frozen)
        wrong_version_files = dict(reviewed["generated"]["files"])
        wrong_version_files.pop("docs/support/v0.2.2.md")
        wrong_version_files["docs/support/v0.2.9.md"] = reviewed["generated"]["files"]["docs/support/v0.2.2.md"]
        wrong_version = with_record({**reviewed, "release_version": "0.2.9",
                                     "generated": {**reviewed["generated"], "files": wrong_version_files},
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
        for omitted_output in (*REQUIRED_GENERATED_FILES, "docs/support/v0.2.2.md"):
            fx.reset(frozen)
            dropped_output = copy.deepcopy(reviewed)
            del dropped_output["generated"]["files"][omitted_output]
            rejected("generated-output-omitted-" + Path(omitted_output).name,
                     lambda: check(with_record(dropped_output), base), "window-generated-missing",
                     omitted_output)
        fx.reset(frozen)
        widened_inputs = copy.deepcopy(reviewed)
        widened_inputs["managed_inputs"]["README.md"] = digest(b"not an allowed managed input")
        rejected("unclassified-managed-input", lambda: check(with_record(widened_inputs), base),
                 "window-record-invalid", "unclassified input README.md")
        fx.reset(frozen)
        widened_outputs = copy.deepcopy(reviewed)
        widened_outputs["generated"]["files"]["README.md"] = digest(b"not an allowed generated output")
        rejected("unclassified-generated-output", lambda: check(with_record(widened_outputs), base),
                 "window-record-invalid", "unclassified output README.md")
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
        fx.reset(base)
        fx.run("rm", "-q", "docs/support/v0.2.1.md")
        fx.run("commit", "-q", "-m", "drop the generated support ledger")
        rejected("tracked-contract-ledger-removed", lambda: check_tracked(repo), "window-input-missing",
                 "docs/support/v0.2.1.md")

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


def self_test_version_v04() -> tuple[int, int]:
    """Exercise exact v0.4.0 generated identity on committed disposable subjects."""
    positives = 0
    controls = 0

    def accepted(name: str, result: subprocess.CompletedProcess) -> None:
        nonlocal positives
        if result.returncode != 0:
            raise AssertionError(f"version-gate positive {name} was rejected: {result.stdout}{result.stderr}")
        positives += 1

    def rejected(name: str, result: subprocess.CompletedProcess, code: str) -> None:
        nonlocal controls
        if result.returncode != 1 or code not in result.stderr:
            raise AssertionError(f"version-gate control {name} was accepted or misclassified: "
                                 f"{result.stdout}{result.stderr}")
        controls += 1

    with tempfile.TemporaryDirectory(prefix="gabbaboy-version-v04-") as temporary:
        fx, base, head, body = build_fixture(Path(temporary), "0.3.0", "0.4.0")
        repo = fx.repo
        notes = Path(temporary) / "notes.md"
        bad_notes = Path(temporary) / "bad-release-notes.md"

        def cli(*arguments: str) -> subprocess.CompletedProcess:
            return subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "--repo", str(repo),
                                   *arguments], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, check=False, timeout=60)

        def set_outputs(version: str, *, manifest_version: str | None = None,
                        changelog_version: str | None = None, ledger_content_version: str | None = None,
                        ledger_link_version: str | None = None, write_ledger: bool = True) -> None:
            manifest_version = manifest_version or version
            changelog_version = changelog_version or version
            ledger_content_version = ledger_content_version or version
            ledger_link_version = ledger_link_version or version
            fx.write("CMakeLists.txt", f"project(GabbaBoy VERSION {version} LANGUAGES C) # x-release-please-version\n")
            fx.write(".release-please-manifest.json", json.dumps({".": manifest_version}, indent=2) + "\n")
            fx.write("CHANGELOG.md", f"# Changelog\n\n## [{changelog_version}]\n\n"
                     f"- Support: [ledger](docs/support/v{ledger_link_version}.md).\n- generated entry\n")
            if write_ledger:
                fx.write("docs/support/v" + version + ".md",
                         f"# GabbaBoy v{ledger_content_version} support ledger\n")
            else:
                (repo / ("docs/support/v" + version + ".md")).unlink(missing_ok=True)

        accepted("inactive-development-record", cli("--check-tracked", "--rev", base))
        accepted("inactive-0.3.0-version-assertion",
                 cli("--check-tracked", "--rev", base, "--expect-version", "0.3.0"))
        rejected("malformed-expected-version",
                 cli("--check-tracked", "--rev", base, "--expect-version", "0.4"),
                 "window-expect-version-invalid")
        accepted("generated-0.4.0-output",
                 cli("--check-tracked", "--rev", head, "--expect-version", "0.4.0"))

        notes.write_bytes(body)
        rejected("inactive-record-cannot-open-expected-window",
                 cli("--rev", base, "--base", base, "--check", RECORD_PATH,
                     "--body", str(notes), "--expect-version", "0.3.0"),
                 "window-record-inactive")

        record = draft_record(repo, head, base, body, 41, 1001, 2002)
        fx.write(RECORD_PATH, render_record(record))
        active = fx.commit("freeze exact 0.4.0 output", RECORD_PATH)
        accepted("active-0.4.0-window",
                 cli("--rev", active, "--base", base, "--check", RECORD_PATH,
                     "--body", str(notes), "--expect-version", "0.4.0"))
        rejected("expected-version-does-not-match-active-record",
                 cli("--rev", active, "--base", base, "--check", RECORD_PATH,
                     "--body", str(notes), "--expect-version", "0.3.0"),
                 "window-version-mismatch")

        # Exact version gating rejects common release-please outcomes even when all generated
        # files agree internally and the development window record remains inactive.
        for version in ("0.3.0", "0.3.1", "0.4.1"):
            fx.reset(head)
            set_outputs(version)
            wrong = fx.commit("version output " + version, "CMakeLists.txt",
                              ".release-please-manifest.json", "CHANGELOG.md",
                              "docs/support/v" + version + ".md")
            rejected("wrong-generated-version-" + version,
                     cli("--check-tracked", "--rev", wrong, "--expect-version", "0.4.0"),
                     "window-version-mismatch")

        fx.reset(head)
        set_outputs("0.4.0", manifest_version="0.3.0")
        mixed_manifest = fx.commit("mixed CMake and manifest versions", "CMakeLists.txt",
                                   ".release-please-manifest.json", "CHANGELOG.md", "docs/support/v0.4.0.md")
        rejected("mixed-cmake-manifest", cli("--check-tracked", "--rev", mixed_manifest,
                                               "--expect-version", "0.4.0"), "window-version-mismatch")

        fx.reset(head)
        set_outputs("0.4.0", ledger_content_version="0.3.0")
        wrong_ledger = fx.commit("wrong version ledger content", "CMakeLists.txt",
                                 ".release-please-manifest.json", "CHANGELOG.md", "docs/support/v0.4.0.md")
        rejected("wrong-ledger-content", cli("--check-tracked", "--rev", wrong_ledger,
                                               "--expect-version", "0.4.0"), "window-version-output-mismatch")

        fx.reset(head)
        set_outputs("0.4.0", write_ledger=False)
        missing_ledger = fx.commit("missing versioned ledger", "CMakeLists.txt",
                                   ".release-please-manifest.json", "CHANGELOG.md", "docs/support/v0.4.0.md")
        rejected("missing-versioned-ledger", cli("--check-tracked", "--rev", missing_ledger,
                                                  "--expect-version", "0.4.0"), "window-version-output-mismatch")

        fx.reset(head)
        set_outputs("0.4.0", changelog_version="0.3.1")
        wrong_changelog = fx.commit("wrong changelog version", "CMakeLists.txt",
                                    ".release-please-manifest.json", "CHANGELOG.md", "docs/support/v0.4.0.md")
        rejected("wrong-changelog-section", cli("--check-tracked", "--rev", wrong_changelog,
                                                  "--expect-version", "0.4.0"), "window-version-output-mismatch")

        fx.reset(head)
        set_outputs("0.4.0", ledger_link_version="0.3.0")
        wrong_ledger_link = fx.commit("wrong versioned changelog ledger link", "CMakeLists.txt",
                                      ".release-please-manifest.json", "CHANGELOG.md", "docs/support/v0.4.0.md")
        rejected("wrong-changelog-ledger-link", cli("--check-tracked", "--rev", wrong_ledger_link,
                                                     "--expect-version", "0.4.0"), "window-version-output-mismatch")

        changelog_section = "# Changelog\n\n## [0.4.0]\n\n"
        ledger_link = "- Support: [ledger](docs/support/v0.4.0.md)."
        tick = chr(96)
        for hiding, content in (
            ("comment", f"<!-- {ledger_link} -->"),
            ("fenced-code", f"```markdown\n{ledger_link}\n```"),
            ("indented-code", "    " + ledger_link),
            ("blockquote-fenced-code", "> ~~~markdown\n> " + ledger_link + "\n> ~~~"),
            ("list-fenced-code", f"- code:\n  {tick * 3}markdown\n  {ledger_link}\n  {tick * 3}"),
            ("unclosed-comment", f"<!--\n{ledger_link}"),
            ("inline-code-span", tick + ledger_link + tick),
            ("multiline-inline-code-span", tick + "\n" + ledger_link + "\n" + tick),
            ("image-is-not-a-ledger-link", "![ledger](docs/support/v0.4.0.md)"),
            ("external-query-is-not-a-ledger-link",
             "[ledger](https://evil.invalid/?next=docs/support/v0.4.0.md)"),
            ("external-title-is-not-a-ledger-link",
             "[ledger](https://evil.invalid/ \"docs/support/v0.4.0.md\")"),
            ("malformed-destination-is-not-a-ledger-link",
             "[ledger](not a valid destination docs/support/v0.4.0.md)"),
        ):
            accepted("visible-ledger-link-counterpart-" + hiding,
                     cli("--check-tracked", "--rev", head, "--expect-version", "0.4.0"))
            fx.reset(head)
            fx.write("CHANGELOG.md", changelog_section + content + "\n")
            hidden_link = fx.commit("hide the changelog ledger link in " + hiding, "CHANGELOG.md")
            rejected("hidden-changelog-ledger-link-" + hiding,
                     cli("--check-tracked", "--rev", hidden_link, "--expect-version", "0.4.0"),
                     "window-version-output-mismatch")

        bad_notes.write_text("v0.3.0 notes with a historical ledger link\n", encoding="utf-8")
        rejected("wrong-release-notes-version",
                 cli("--rev", active, "--base", base, "--check", RECORD_PATH, "--body", str(notes),
                     "--release-notes", str(bad_notes), "--expect-version", "0.4.0"),
                 "window-release-notes-invalid")
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
    parser.add_argument("--expect-version", help="require the judged CMake, manifest and generated outputs to match X.Y.Z")
    parser.add_argument("--release-notes", type=Path, help="also judge supplied release notes with the existing adoption validator")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--self-test-version-v04", action="store_true")
    parser.add_argument("--repo", type=Path, default=ROOT, help="repository to read (default: this checkout)")
    args = parser.parse_args()
    try:
        if args.expect_version is not None and VERSION.fullmatch(args.expect_version) is None:
            reject("window-expect-version-invalid", "expected X.Y.Z")
        if args.expect_version is not None and not (args.check or args.check_tracked):
            parser.error("--expect-version requires --check or --check-tracked")
        if args.release_notes is not None and not (args.check and args.expect_version is not None):
            parser.error("--release-notes requires --check and --expect-version")
        if args.self_test:
            positives, controls = self_test()
            print(f"version-window controls pass positives={positives} controls={controls}")
            return 0
        if args.self_test_version_v04:
            positives, controls = self_test_version_v04()
            print(f"release-version-v04 controls pass positives={positives} controls={controls}")
            return 0
        if args.check_tracked:
            print(check_tracked(args.repo, args.rev, args.require_active, args.expect_version))
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
            resolved_rev = resolve_commit(args.repo, args.rev, "--rev")
            verdict = check_window(args.repo, resolved_rev, args.base, args.check, read_body(args.body),
                                   args.expect_version)
            if args.release_notes is not None:
                check_release_notes(args.repo, resolved_rev, args.release_notes)
            print(verdict)
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
