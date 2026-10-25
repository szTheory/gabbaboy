#!/usr/bin/env python3
"""Hold the v0.3 Phase 16 carry-over dispositions to their evidence and, once released, to tag-bound receipts.

16-DISPOSITIONS.json is the v0.3 record (the digest-pinned v0.2 15.1-DISPOSITIONS.json is never edited, and
verify-closeout-dispositions.py keeps asserting owner_accepted=0 for that archived record only). One row per
carry-over item. A release-linked row waits in `pending-release` until publication and then closes only with
tag-bound receipts:

  * receipts.tag / tag_sha: the published tag and the commit it names
  * receipts.rehearsal_run {id, head_sha, head_tree, conclusion: success}: the green rehearsal at the rehearsed head
  * receipts.trusted_judge {id, conclusion: success}: the rehearsal's trusted-judge job
  * receipts.nightly_asan_run {id, head_sha, head_tree, conclusion: success}: the dispatched nightly-asan run
  * receipts.release_readback {path, sha256}: a committed readback JSON {tag, tag_sha, is_draft: false, assets: [...],
    reconciliation: {...}}, its bytes pinned by SHA-256
  * receipts.pr_closures {path, sha256}: a committed JSON {prs: [{number, state: CLOSED, closed_at, comment_url,
    changed_paths}]} for exactly #78-#92, none touching src/ or include/
  * the rehearsal and nightly head trees must equal the tag commit's tree (a squash merge rewrites the commit and keeps the tree)

--check PATH validates the record. --rev REV reads the record and every receipt it names with `git show REV:<path>`
and never calls gh or reads the working tree, so a boundary check sees point-in-time facts from the boundary commit.
Without --rev the working tree is read (pre-commit use). --self-test drives this very CLI over a private fixture
repository; a fixture is not hosted evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

if not __debug__:
    raise SystemExit("verify-v03-dispositions refuses to run under python -O (its asserts and checks must stay on)")

ROOT = pathlib.Path(__file__).resolve().parents[2]
DECISIONS = ".planning/context/DECISIONS.md"
EXPECTED_TESTS = "tests/expected-tests.txt"
MAX_BYTES = 8 * 1024 * 1024
STATUSES = ("pending-release", "closed", "accepted-later", "accepted-dropped", "accepted-history", "seed",
            "superseded", "disclosed-exception")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
DECISION_ID = re.compile(r"^D-[0-9]{3}$")
TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
RELEASE_LINKED = ("LIM-SUPPORT-LEDGER-PIN", "LIM-PERF-REVIEW", "LIM-REHEARSAL-FAILED", "LIM-TRUSTED-JUDGE")
RELEASE_CLOSURE = ["rehearsal_run", "trusted_judge", "nightly_asan_run", "release_readback"]
PR_ROW = "PR-78-92-SUPERSEDED"
PR_NUMBERS = list(range(78, 93))
VALIDATION_ROWS = ("34-1", "34-2", "35-2", "35-3", "36-1", "36-2", "36-3")

# id -> admitted statuses. The id set is exact: a missing, dropped or extra row is rejected.
REQUIRED: dict[str, tuple[str, ...]] = {
    **{item: ("pending-release", "closed") for item in RELEASE_LINKED},
    PR_ROW: ("pending-release", "closed"),
    "LIM-ASAN-STALL-TIMING": ("closed",),
    "LIM-RESIDUAL-WRITE-JOBS": ("accepted-later",),
    "LIM-NO-HOST-WRONG-ROM": ("accepted-later",),
    "LIM-WINDOWS-POSIX-CONTROLS": ("accepted-later",),
    "LIM-HIST-AUDIO-RED": ("accepted-dropped",),
    "LIM-HIST-M7": ("accepted-dropped",),
    "LIM-SHIP11-UNCLASSIFIED": ("accepted-dropped",),
    "LIM-PROHIBITION-FLAGS": ("accepted-dropped",),
    "LEDGER-93-APPEND": ("disclosed-exception",),
    **{f"VAL-{row}": ("superseded",) for row in VALIDATION_ROWS},
    "AUDIT-13-VERIFICATION-PADDING": ("accepted-history",),
    "GR-IN-03": ("seed",),
    "GR2-IN-01": ("seed",),
    "AUDIT-SUMMARY-REQUIREMENTS-KEY": ("accepted-history",),
    "AUDIT-LEGACY-SUMMARY-PROBLEMS": ("accepted-history",),
}
OWNER_STATUSES = ("accepted-later", "accepted-dropped")
ROW_KEYS = {"id", "status", "decision", "title", "evidence", "owner_accepted", "owner_decision", "basis", "closure_requires"}
ROW_REQUIRED = {"id", "status", "decision", "title", "evidence", "owner_accepted"}
TOP_KEYS = {"schema_version", "plan", "scope", "audit_source", "receipts", "rows"}


class Reject(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def reject(code: str, message: str) -> None:
    raise Reject(code, message)


class Source:
    """Reads a path from the working tree, or from one commit with `git show REV:<path>` (never both)."""

    def __init__(self, repo: pathlib.Path, rev: str | None) -> None:
        self.repo = repo
        self.rev = rev

    def relative(self, path: str) -> str:
        candidate = pathlib.PurePosixPath(path.replace("\\", "/"))
        if candidate.is_absolute():
            try:
                candidate = pathlib.PurePosixPath(pathlib.Path(path).resolve().relative_to(self.repo.resolve()).as_posix())
            except ValueError:
                reject("path-invalid", f"{path} is outside the repository")
        parts = candidate.parts
        if not parts or ".." in parts or "." in parts or any(not part for part in parts):
            reject("path-invalid", f"{path} is not a clean repository-relative path")
        return candidate.as_posix()

    def exists(self, path: str) -> bool:
        relative = self.relative(path)
        if self.rev is not None:
            return subprocess.run(["git", "-C", str(self.repo), "cat-file", "-e", f"{self.rev}:{relative}"],
                                  capture_output=True, check=False).returncode == 0
        return (self.repo / relative).exists()

    def read(self, path: str, code: str = "receipt-missing") -> bytes:
        relative = self.relative(path)
        if self.rev is not None:
            done = subprocess.run(["git", "-C", str(self.repo), "show", f"{self.rev}:{relative}"], capture_output=True, check=False)
            if done.returncode != 0:
                reject(code, f"{relative} is not present at {self.rev}")
            raw = done.stdout
        else:
            target = self.repo / relative
            if not target.is_file():
                reject(code, f"{relative} is not a file in the working tree")
            raw = target.read_bytes()
        if len(raw) > MAX_BYTES:
            reject("file-too-large", f"{relative} exceeds {MAX_BYTES} bytes")
        return raw


def git_tree(repo: pathlib.Path, commit: str) -> str | None:
    done = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"{commit}^{{tree}}"],
                          capture_output=True, text=True, check=False)
    return done.stdout.strip() if done.returncode == 0 and HEX40.match(done.stdout.strip()) else None


def parse_json(raw: bytes, what: str, code: str = "schema-malformed"):
    def pairs(items):
        seen = {}
        for key, value in items:
            if key in seen:
                reject(code, f"{what} repeats the key {key!r}")
            seen[key] = value
        return seen

    try:
        return json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=pairs)
    except (UnicodeDecodeError, ValueError) as error:
        reject(code, f"{what} is not valid JSON: {error}")


def text(value, label: str, limit: int = 4000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit or any(ord(char) < 32 for char in value):
        reject("schema-malformed", f"{label} must be a non-empty single-line string")
    return value


def decision_ids(source: Source) -> set[str]:
    document = source.read(DECISIONS, "decisions-missing").decode("utf-8", errors="strict")
    return set(re.findall(r"^\| (D-[0-9]{3}) \|", document, re.M))


def test_names(source: Source) -> set[str]:
    document = source.read(EXPECTED_TESTS, "expected-tests-missing").decode("utf-8", errors="strict")
    return {line.strip() for line in document.splitlines() if line.strip() and not line.startswith("#")}


def check_evidence(row: dict, source: Source, tests: set[str]) -> None:
    evidence = row["evidence"]
    if not isinstance(evidence, list) or not evidence:
        reject("evidence-missing", f"{row['id']} needs a non-empty evidence list")
    for entry in evidence:
        entry = text(entry, f"{row['id']} evidence entry", 500)
        if entry.startswith("ctest:"):
            if entry[6:] not in tests:
                reject("evidence-missing", f"{row['id']} names CTest {entry[6:]!r}, which tests/expected-tests.txt does not list")
        elif entry.startswith("run:"):
            if not re.fullmatch(r"[1-9][0-9]*", entry[4:]):
                reject("evidence-missing", f"{row['id']} run reference {entry!r} is not a positive run id")
        elif not source.exists(entry):
            reject("evidence-missing", f"{row['id']} names {entry}, which does not exist" + (f" at {source.rev}" if source.rev else ""))


def check_row(row, source: Source, decisions: set[str], tests: set[str]) -> None:
    if not isinstance(row, dict):
        reject("schema-malformed", "a row must be an object")
    unknown = set(row) - ROW_KEYS
    missing = ROW_REQUIRED - set(row)
    if unknown or missing:
        reject("schema-malformed", f"{row.get('id', '?')}: unknown keys {sorted(unknown)} or missing keys {sorted(missing)}")
    ident = text(row["id"], "row id", 100)
    status = row["status"]
    if status not in STATUSES:
        reject("status-unknown", f"{ident} has the unknown status {status!r}")
    if status not in REQUIRED.get(ident, STATUSES):
        reject("status-mismatch", f"{ident} may only be {'/'.join(REQUIRED[ident])}, not {status}")
    text(row["title"], f"{ident} title")
    if not isinstance(row["decision"], str) or not DECISION_ID.match(row["decision"]) or row["decision"] not in decisions:
        reject("decision-unknown", f"{ident} cites {row['decision']!r}, which {DECISIONS} does not record")
    if "basis" in row:
        text(row["basis"], f"{ident} basis")
    check_evidence(row, source, tests)
    owned = row["owner_accepted"]
    if type(owned) is not bool:
        reject("owner-accepted-invalid", f"{ident} owner_accepted must be true or false")
    if owned:
        owner_decision = row.get("owner_decision")
        if status not in OWNER_STATUSES or not isinstance(owner_decision, str) or owner_decision not in decisions:
            reject("owner-accepted-invalid", f"{ident} is owner_accepted without a recorded decision id for an accepted-later/accepted-dropped row")
    elif "owner_decision" in row or status in OWNER_STATUSES:
        reject("owner-accepted-invalid", f"{ident} must be owner_accepted with its decision id, or neither")
    wanted = RELEASE_CLOSURE if ident in RELEASE_LINKED else (["pr_closures"] if ident == PR_ROW else None)
    if wanted is None:
        if "closure_requires" in row:
            reject("closure-requires-invalid", f"{ident} is not release-linked and takes no closure_requires")
    elif row.get("closure_requires") != wanted:
        reject("closure-requires-invalid", f"{ident} must name closure_requires {wanted}")


def check_receipt_file(source: Source, receipt, name: str) -> tuple[bytes, object]:
    if not isinstance(receipt, dict) or set(receipt) != {"path", "sha256"} or not isinstance(receipt["path"], str) \
            or not isinstance(receipt["sha256"], str) or not HEX64.match(receipt["sha256"]):
        reject("receipt-invalid", f"{name} must be {{path, sha256}} with a 64-hex digest")
    raw = source.read(receipt["path"])
    if hashlib.sha256(raw).hexdigest() != receipt["sha256"]:
        reject("receipt-digest-mismatch", f"{name} bytes do not match the recorded SHA-256")
    return raw, parse_json(raw, name, "receipt-invalid")


def check_run(receipt, name: str, with_head: bool) -> None:
    keys = {"id", "head_sha", "head_tree", "conclusion"} if with_head else {"id", "conclusion"}
    if not isinstance(receipt, dict) or set(receipt) != keys or type(receipt["id"]) is not int or receipt["id"] < 1 \
            or receipt["conclusion"] != "success":
        reject("receipt-invalid", f"{name} must be {sorted(keys)} with a positive id and conclusion success")
    if with_head and (not isinstance(receipt["head_sha"], str) or not HEX40.match(receipt["head_sha"])
                      or not isinstance(receipt["head_tree"], str) or not HEX40.match(receipt["head_tree"])):
        reject("receipt-invalid", f"{name} head_sha and head_tree must be 40-hex")


def check_readback(source: Source, receipts: dict) -> None:
    _, readback = check_receipt_file(source, receipts["release_readback"], "release_readback")
    if not isinstance(readback, dict) or readback.get("tag") != receipts["tag"] or readback.get("tag_sha") != receipts["tag_sha"] \
            or readback.get("is_draft") is not False:
        reject("receipt-invalid", "the release readback must record the same tag and tag commit and is_draft false")
    assets = readback.get("assets")
    if not isinstance(assets, list) or not assets or any(
            not (isinstance(item, str) and item) and not (isinstance(item, dict) and isinstance(item.get("name"), str) and item["name"])
            for item in assets):
        reject("receipt-invalid", "the release readback must list its assets")
    if not isinstance(readback.get("reconciliation"), dict) or not readback["reconciliation"]:
        reject("receipt-invalid", "the release readback must record its reconciliation")


def check_pr_closures(source: Source, receipt) -> None:
    _, closures = check_receipt_file(source, receipt, "pr_closures")
    prs = closures.get("prs") if isinstance(closures, dict) else None
    if not isinstance(prs, list):
        reject("pr-closure-invalid", "pr_closures must list prs")
    numbers = [item.get("number") if isinstance(item, dict) else None for item in prs]
    if sorted(n for n in numbers if type(n) is int) != PR_NUMBERS or len(numbers) != len(PR_NUMBERS):
        missing = [n for n in PR_NUMBERS if numbers.count(n) != 1]
        reject("pr-closure-invalid", f"pr_closures must list each of #78-#92 exactly once (problem with {missing})")
    for item in prs:
        number = item["number"]
        if set(item) != {"number", "state", "closed_at", "comment_url", "changed_paths"} or item["state"] != "CLOSED" \
                or not isinstance(item["closed_at"], str) or not item["closed_at"].strip() \
                or not isinstance(item["comment_url"], str) or not item["comment_url"].startswith("https://") \
                or not isinstance(item["changed_paths"], list) \
                or any(not isinstance(path, str) or not path for path in item["changed_paths"]):
            reject("pr-closure-invalid", f"#{number} must be CLOSED with closed_at, an https comment_url and changed_paths")
        for path in item["changed_paths"]:
            first = path.replace("\\", "/").lstrip("./").split("/", 1)[0].lower()
            if first in ("src", "include"):
                reject("pr-closure-invalid", f"#{number} changed {path}; a superseded PR must not touch src/ or include/")


def check_receipts(receipts, rows: dict, source: Source) -> None:
    closed = {ident for ident, row in rows.items() if row["status"] == "closed" and "closure_requires" in row}
    if receipts is None:
        if closed:
            reject("closure-without-receipts", f"{sorted(closed)} are closed without tag-bound receipts")
        return
    needed = {"tag", "tag_sha", *RELEASE_CLOSURE, "pr_closures"}
    if not isinstance(receipts, dict) or set(receipts) != needed:
        reject("closure-without-receipts", f"receipts must hold exactly {sorted(needed)}")
    if not isinstance(receipts.get("tag"), str) or not TAG.match(receipts["tag"]) \
            or not isinstance(receipts.get("tag_sha"), str) or not HEX40.match(receipts["tag_sha"]):
        reject("receipt-invalid", "receipts.tag must be vX.Y.Z and tag_sha 40-hex")
    check_run(receipts["rehearsal_run"], "rehearsal_run", True)
    check_run(receipts["trusted_judge"], "trusted_judge", False)
    check_run(receipts["nightly_asan_run"], "nightly_asan_run", True)
    tag_tree = git_tree(source.repo, receipts["tag_sha"])
    if tag_tree is None:
        reject("tree-mismatch", f"the tag commit {receipts['tag_sha']} is not readable, so its tree cannot be compared")
    for name in ("rehearsal_run", "nightly_asan_run"):
        run = receipts[name]
        if run["head_tree"] != tag_tree:
            reject("tree-mismatch", f"{name} head tree {run['head_tree']} differs from the tag tree {tag_tree}")
        actual = git_tree(source.repo, run["head_sha"])
        if actual is not None and actual != run["head_tree"]:
            reject("tree-mismatch", f"{name} head commit {run['head_sha']} has tree {actual}, not the recorded {run['head_tree']}")
    check_readback(source, receipts)
    check_pr_closures(source, receipts["pr_closures"])


def check(record_path: str, repo: pathlib.Path, rev: str | None) -> str:
    source = Source(repo, rev)
    record = parse_json(source.read(record_path, "record-missing"), "the disposition record")
    if not isinstance(record, dict) or set(record) != TOP_KEYS or record["schema_version"] != 1 or record["plan"] != "16-06":
        reject("schema-malformed", f"the record must be a version 1 plan 16-06 record with exactly {sorted(TOP_KEYS)}")
    text(record["scope"], "scope")
    text(record["audit_source"], "audit_source")
    decisions = decision_ids(source)
    tests = test_names(source)
    if not isinstance(record["rows"], list):
        reject("schema-malformed", "rows must be a list")
    rows: dict[str, dict] = {}
    for row in record["rows"]:
        check_row(row, source, decisions, tests)
        if row["id"] in rows:
            reject("id-set", f"duplicate row {row['id']}")
        rows[row["id"]] = row
    if set(rows) != set(REQUIRED):
        reject("id-set", f"missing rows {sorted(set(REQUIRED) - set(rows))} and extra rows {sorted(set(rows) - set(REQUIRED))}")
    check_receipts(record["receipts"], rows, source)
    pending = sum(row["status"] == "pending-release" for row in rows.values())
    closed = sum(row["status"] == "closed" for row in rows.values())
    owner = sum(row["owner_accepted"] for row in rows.values())
    return f"v03-dispositions pass rows={len(rows)} pending={pending} closed={closed} owner_accepted={owner}"


# ------------------------------------------------------------------------------------------------ self-test
RECORD_REL = ".planning/phases/GB-16-fixture/16-DISPOSITIONS.json"
READBACK_REL = ".planning/phases/GB-16-fixture/16-release-readback.json"
CLOSURES_REL = ".planning/phases/GB-16-fixture/16-pr-closures.json"
SCRIPT = pathlib.Path(__file__).resolve()


def git(repo: pathlib.Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                           "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
                          capture_output=True, text=True, check=True)
    return done.stdout.strip()


def fixture_rows() -> list[dict]:
    rows = []
    for ident, admitted in REQUIRED.items():
        status = admitted[0]
        row = {"id": ident, "status": status, "decision": "D-106", "title": f"Fixture row {ident}",
               "evidence": ["docs/evidence.md", "ctest:fixture_test", "run:12345"], "owner_accepted": status in OWNER_STATUSES}
        if row["owner_accepted"]:
            row["owner_decision"] = "D-106"
        if ident in RELEASE_LINKED:
            row["closure_requires"] = list(RELEASE_CLOSURE)
        if ident == PR_ROW:
            row["closure_requires"] = ["pr_closures"]
        rows.append(row)
    return rows


def closures_document() -> dict:
    return {"prs": [{"number": number, "state": "CLOSED", "closed_at": "2026-10-26T00:00:00Z",
                     "comment_url": f"https://example.invalid/pull/{number}#issuecomment-1",
                     "changed_paths": ["tests/CMakeLists.txt", ".planning/STATE.md"]} for number in PR_NUMBERS]}


def build_fixture(base: pathlib.Path) -> dict:
    repo = base / "repo"
    (repo / ".planning/context").mkdir(parents=True)
    (repo / "docs").mkdir()
    (repo / "tests").mkdir()
    (repo / RECORD_REL).parent.mkdir(parents=True)
    (repo / DECISIONS).write_text("| ID | Decision |\n|---|---|\n| D-106 | carry-over |\n| D-110 | ledger |\n", encoding="utf-8")
    (repo / EXPECTED_TESTS).write_text("fixture_test\n", encoding="utf-8")
    (repo / "docs/evidence.md").write_text("evidence\n", encoding="utf-8")
    git(repo.parent, "init", "-q", "repo")
    pending = {"schema_version": 1, "plan": "16-06", "scope": "fixture", "audit_source": "fixture", "receipts": None, "rows": fixture_rows()}
    (repo / RECORD_REL).write_text(json.dumps(pending, indent=1) + "\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "fixture: pending record")
    tag_sha = git(repo, "rev-parse", "HEAD")
    tag_tree = git(repo, "rev-parse", "HEAD^{tree}")
    git(repo, "tag", "v0.2.1")
    git(repo, "commit", "-q", "--allow-empty", "-m", "fixture: rehearsed head with the same tree")
    same_tree_head = git(repo, "rev-parse", "HEAD")
    (repo / "docs/other.md").write_text("other\n", encoding="utf-8")
    git(repo, "add", "docs/other.md")
    git(repo, "commit", "-q", "-m", "fixture: head with another tree")
    other_head = git(repo, "rev-parse", "HEAD")
    other_tree = git(repo, "rev-parse", "HEAD^{tree}")
    git(repo, "rm", "-q", "docs/other.md")
    git(repo, "commit", "-q", "-m", "fixture: back to the tag tree")
    readback = {"tag": "v0.2.1", "tag_sha": tag_sha, "is_draft": False, "assets": ["gabbaboy-core-linux-x64.tar.gz"],
                "reconciliation": {"result": "reconciled"}}
    return {"repo": repo, "tag_sha": tag_sha, "tag_tree": tag_tree, "same_tree_head": same_tree_head, "other_head": other_head,
            "other_tree": other_tree, "readback": readback, "closures": closures_document()}


def closed_record(facts: dict, readback_raw: bytes, closures_raw: bytes) -> dict:
    record = json.loads((facts["repo"] / RECORD_REL).read_text(encoding="utf-8"))
    for row in record["rows"]:
        if row["status"] == "pending-release":
            row["status"] = "closed"
    record["receipts"] = {
        "tag": "v0.2.1", "tag_sha": facts["tag_sha"],
        "rehearsal_run": {"id": 111, "head_sha": facts["same_tree_head"], "head_tree": facts["tag_tree"], "conclusion": "success"},
        "trusted_judge": {"id": 222, "conclusion": "success"},
        "nightly_asan_run": {"id": 333, "head_sha": facts["same_tree_head"], "head_tree": facts["tag_tree"], "conclusion": "success"},
        "release_readback": {"path": READBACK_REL, "sha256": hashlib.sha256(readback_raw).hexdigest()},
        "pr_closures": {"path": CLOSURES_REL, "sha256": hashlib.sha256(closures_raw).hexdigest()},
    }
    return record


def serialise(value: dict) -> bytes:
    return (json.dumps(value, indent=1, sort_keys=True) + "\n").encode("utf-8")


def run_cli(repo: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", str(SCRIPT), "--repo", str(repo), *args], capture_output=True, text=True,
                          timeout=120, check=False)


def self_test() -> int:
    controls = 0
    with tempfile.TemporaryDirectory(prefix="gabbaboy-v03-dispositions-") as temporary:
        base = pathlib.Path(temporary)
        facts = build_fixture(base)
        repo = facts["repo"]

        def expect_pass(label: str, result: subprocess.CompletedProcess, needle: str) -> None:
            if result.returncode != 0 or needle not in result.stdout:
                raise SystemExit(f"self-test positive {label} failed: {result.stderr.strip() or result.stdout.strip()}")

        def expect_reject(label: str, result: subprocess.CompletedProcess, code: str) -> None:
            nonlocal controls
            if result.returncode == 0 or "v03-dispositions pass" in result.stdout:
                raise SystemExit(f"self-test accepted {label}")
            if f"REJECT {code}:" not in result.stderr:
                raise SystemExit(f"self-test {label}: expected REJECT {code}, got: {result.stderr.strip()[:240]}")
            controls += 1

        # Positive: the pending record before the tag, from the working tree and at a commit.
        pending_head = git(repo, "rev-parse", "HEAD")
        expect_pass("pending", run_cli(repo, "--check", RECORD_REL), f"rows={len(REQUIRED)} pending=5 closed=1 owner_accepted=7")
        expect_pass("pending at rev", run_cli(repo, "--check", RECORD_REL, "--rev", pending_head), "pending=5")

        # Positive: a closed record whose receipts are committed, read at that commit; owner_accepted rows cite their decision id.
        readback_raw = serialise(facts["readback"])
        closures_raw = serialise(facts["closures"])
        record = closed_record(facts, readback_raw, closures_raw)
        (repo / READBACK_REL).write_bytes(readback_raw)
        (repo / CLOSURES_REL).write_bytes(closures_raw)
        (repo / RECORD_REL).write_bytes(serialise(record))
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "fixture: closed record with receipts")
        closed_head = git(repo, "rev-parse", "HEAD")
        expect_pass("closed at rev", run_cli(repo, "--check", RECORD_REL, "--rev", closed_head), "pending=0 closed=6 owner_accepted=7")

        def case(label: str, code: str, mutate, *, rev_check: bool = True) -> None:
            """Write a mutated record (and receipts) into the working tree, commit it, and require REJECT on both read paths."""
            variant = json.loads(json.dumps(record))
            files = {READBACK_REL: readback_raw, CLOSURES_REL: closures_raw}
            mutate(variant, files)
            (repo / RECORD_REL).write_bytes(serialise(variant))
            for rel, raw in files.items():
                (repo / rel).write_bytes(raw)
            git(repo, "add", "-A")
            git(repo, "commit", "-q", "--allow-empty", "-m", f"fixture: {label}")
            head = git(repo, "rev-parse", "HEAD")
            expect_reject(label, run_cli(repo, "--check", RECORD_REL), code)
            if rev_check:
                expect_reject(label + " at rev", run_cli(repo, "--check", RECORD_REL, "--rev", head), code)

        def without_receipts(variant, files):
            variant["receipts"] = None

        def tampered_readback(variant, files):
            files[READBACK_REL] = readback_raw.replace(b"v0.2.1", b"v0.2.9")

        def tampered_closures(variant, files):
            files[CLOSURES_REL] = closures_raw + b" "

        def closures_without_85(variant, files):
            document = json.loads(closures_raw)
            document["prs"] = [item for item in document["prs"] if item["number"] != 85]
            files[CLOSURES_REL] = serialise(document)
            variant["receipts"]["pr_closures"]["sha256"] = hashlib.sha256(files[CLOSURES_REL]).hexdigest()

        def closures_naming_src(variant, files):
            document = json.loads(closures_raw)
            document["prs"][3]["changed_paths"].append("src/core/gabbaboy.c")
            files[CLOSURES_REL] = serialise(document)
            variant["receipts"]["pr_closures"]["sha256"] = hashlib.sha256(files[CLOSURES_REL]).hexdigest()

        def closures_open_pr(variant, files):
            document = json.loads(closures_raw)
            document["prs"][0]["state"] = "OPEN"
            files[CLOSURES_REL] = serialise(document)
            variant["receipts"]["pr_closures"]["sha256"] = hashlib.sha256(files[CLOSURES_REL]).hexdigest()

        def draft_readback(variant, files):
            document = dict(facts["readback"], is_draft=True)
            files[READBACK_REL] = serialise(document)
            variant["receipts"]["release_readback"]["sha256"] = hashlib.sha256(files[READBACK_REL]).hexdigest()

        def unequal_tree(variant, files):
            variant["receipts"]["rehearsal_run"].update(head_sha=facts["other_head"], head_tree=facts["other_tree"])

        def lying_tree(variant, files):
            variant["receipts"]["rehearsal_run"].update(head_sha=facts["other_head"])

        def dropped_row(variant, files):
            variant["rows"] = [row for row in variant["rows"] if row["id"] != "LIM-TRUSTED-JUDGE"]

        def extra_row(variant, files):
            variant["rows"].append({key: value for key, value in variant["rows"][2].items() if key != "closure_requires"} | {"id": "LIM-INVENTED"})

        def unknown_status(variant, files):
            variant["rows"][0]["status"] = "waived"

        def owner_without_decision(variant, files):
            for row in variant["rows"]:
                if row["id"] == "LIM-HIST-M7":
                    del row["owner_decision"]

        def owner_unknown_decision(variant, files):
            for row in variant["rows"]:
                if row["id"] == "LIM-HIST-M7":
                    row["owner_decision"] = "D-999"

        def missing_evidence(variant, files):
            variant["rows"][2]["evidence"] = ["docs/not-there.md"]

        def unknown_decision(variant, files):
            variant["rows"][2]["decision"] = "D-998"

        def flipped_dropped_row(variant, files):
            for row in variant["rows"]:
                if row["id"] == "LIM-HIST-AUDIO-RED":
                    row["status"] = "closed"

        case("closure without receipts", "closure-without-receipts", without_receipts)
        case("tampered readback digest", "receipt-digest-mismatch", tampered_readback)
        case("tampered pr-closures digest", "receipt-digest-mismatch", tampered_closures)
        case("pr-closures receipt missing #85", "pr-closure-invalid", closures_without_85)
        case("pr-closures receipt naming a src path", "pr-closure-invalid", closures_naming_src)
        case("pr-closures receipt with an open PR", "pr-closure-invalid", closures_open_pr)
        case("readback of a draft release", "receipt-invalid", draft_readback)
        case("rehearsal head with a different tree", "tree-mismatch", unequal_tree)
        case("rehearsal head tree recorded falsely", "tree-mismatch", lying_tree)
        case("dropped row", "id-set", dropped_row)
        case("extra row", "id-set", extra_row)
        case("unknown status", "status-unknown", unknown_status)
        case("owner_accepted without a decision id", "owner-accepted-invalid", owner_without_decision)
        case("owner_accepted with an unrecorded decision id", "owner-accepted-invalid", owner_unknown_decision)
        case("evidence path that does not exist", "evidence-missing", missing_evidence)
        case("decision id that DECISIONS.md does not record", "decision-unknown", unknown_decision)
        case("a dropped row flipped to closed", "status-mismatch", flipped_dropped_row)

        # A receipt present in the working tree but absent at the commit read by --rev.
        (repo / RECORD_REL).write_bytes(serialise(record))
        (repo / READBACK_REL).write_bytes(readback_raw)
        (repo / CLOSURES_REL).write_bytes(closures_raw)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "fixture: restore the closed record")
        git(repo, "rm", "-q", "--cached", READBACK_REL)
        git(repo, "commit", "-q", "-m", "fixture: receipt untracked at this commit")
        absent_head = git(repo, "rev-parse", "HEAD")
        expect_pass("receipt present in the working tree", run_cli(repo, "--check", RECORD_REL), "closed=6")
        expect_reject("receipt absent at --rev", run_cli(repo, "--check", RECORD_REL, "--rev", absent_head), "receipt-missing")
    print(f"v03-dispositions self-test pass controls={controls}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", metavar="PATH", help="the disposition record, relative to the repository (or absolute)")
    parser.add_argument("--rev", help="read the record and every receipt with git show REV:<path>; no working tree, no gh")
    parser.add_argument("--repo", type=pathlib.Path, default=ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            return self_test()
        if args.check:
            print(check(args.check, args.repo.resolve(), args.rev))
            return 0
        parser.error("choose --check PATH or --self-test")
    except Reject as error:
        print(f"REJECT {error.code}: {error.message}", file=sys.stderr)
        return 1
    except (OSError, KeyError, TypeError, AttributeError, UnicodeError, subprocess.SubprocessError) as error:
        print(f"REJECT schema-malformed: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
