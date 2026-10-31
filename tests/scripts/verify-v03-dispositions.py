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
import ast
import datetime as dt
import hashlib
import io
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import tokenize

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
READBACK_V2_KEYS = {
    "tag", "tag_sha", "tag_tree", "is_draft", "is_prerelease", "release_id", "published_at", "url",
    "assets", "reconciliation", "release_run", "attach_v02_evidence", "pre_publish_inventory",
    "pre_publish_inventory_source", "sha256sums", "release_receipt", "sidecar_ledger",
}
PUBLICATION_SOURCE_KEYS = {
    "schema_version", "source_sha", "workflow_sha", "workflow_ref", "dispatch", "run_api",
    "attach_job_api", "final_job_api", "release_receipt_raw",
}
RETRY_DISPATCH_KEYS = {"workflow", "ref", "inputs"}
RETRY_INPUT_KEYS = {"retry", "tag_name", "source_sha", "release_id"}
RETRY_RUN_API_KEYS = {
    "id", "run_attempt", "path", "event", "head_branch", "head_sha", "status", "conclusion",
    "repository_full_name",
}
RETRY_JOB_API_KEYS = {
    "id", "run_id", "head_sha", "name", "status", "conclusion", "started_at", "completed_at",
}
RECOVERY_ALLOWED_PATHS = {
    "tests/scripts/verify-release-lifecycle.py",
    "tests/data/release-api/v030-notes-failure.json",
    "tests/data/release-api/SOURCES.md",
    "tests/CMakeLists.txt",
    "tests/expected-tests.txt",
    "tests/scripts/verify-v03-dispositions.py",
    "docs/release.md",
    ".planning/phases/GB-19-qualified-v0-3-0-release/19-08-PLAN.md",
    ".planning/phases/GB-19-qualified-v0-3-0-release/19-POST-TAG-FAILURE.md",
    ".planning/phases/GB-19-qualified-v0-3-0-release/COVERAGE.md",
}
RECOVERY_CRITICAL_PATHS = (
    ".github/workflows/release.yml", ".github/workflows/release-please.yml",
    ".github/scripts/release-evidence-lifecycle.sh", ".github/scripts/verify-release-gates.sh",
    ".github/scripts/verify-release-source-proof.py", "tests/scripts/verify-v02-adoption.py",
    ".github/scripts/verify-workflow-policy.py", "tests/scripts/verify-workflow-policy-coverage.py",
    "tests/data/workflow-policy-controls.json", "tests/baseline/perf-gate-v1.txt",
    "tests/data/support-claims-v0.3.json", "tests/data/release-disclosure.json",
    "tests/data/state-compatibility.json", "tests/data/version-window.json", "docs/support/v0.3.0.md",
)
RECOVERY_CRITICAL_PREFIXES = ("src/", "include/")
PRE_PUBLISH_KEYS = {"schema_version", "kind", "tag", "source_sha", "release_id", "run_id", "run_attempt", "assets"}
PRE_PUBLISH_SOURCE_KEYS = {"run_id", "run_attempt", "artifact_name", "artifact_id", "file_sha256", "raw"}
FORBIDDEN_TEXT = re.compile(r"/Users/|/home/|[A-Za-z]:\\\\Users|\bgh[pousr]_[A-Za-z0-9]{20,}|github_pat_|BEGIN [A-Z ]*PRIVATE KEY")
FORBIDDEN_TEXT_ASSIGNMENT = r'''FORBIDDEN_TEXT = re.compile(r"/Users/|/home/|[A-Za-z]:\\\\Users|\bgh[pousr]_[A-Za-z0-9]{20,}|github_pat_|BEGIN [A-Z ]*PRIVATE KEY")'''
SHA256_LINE = re.compile(r"^([0-9a-f]{64})  ([^/\\\s]+)$")
PERF_DIGEST_PIN = re.compile(rb"(?m)^rom\.([a-z0-9-]+)\.digest=([0-9a-f]{16})$")
READBACK_V2_REL = "fixture/19-release-readback.json"
READBACK_LIFECYCLE_REL = "tests/scripts/verify-release-lifecycle.py"
READBACK_LEDGER_REL = "docs/support/v0.3.0.md"
FINAL_ASSET_NAMES = {"SHA256SUMS", "release-receipt.json"}
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


def perf_digest_pins(raw: bytes) -> dict[str, str]:
    rows = PERF_DIGEST_PIN.findall(raw)
    pins = {name.decode("ascii"): digest.decode("ascii") for name, digest in rows}
    if len(pins) != len(rows) or set(pins) != {"libbet", "tracer", "visible-demo"}:
        reject("readback-receipt-mismatch", "source S performance limits must pin each gated ROM digest exactly once")
    return pins


def check_retry_publication_source(source: Source, readback: dict, release_run: dict, attach: dict,
                                   source_row: dict, sums_bytes: bytes, receipt: dict) -> str:
    """Prove a workflow-dispatch retry ran trusted main G while every product byte stays bound to tag S."""
    publication = readback.get("publication_source")
    if not isinstance(publication, dict) or set(publication) != PUBLICATION_SOURCE_KEYS \
            or type(publication.get("schema_version")) is not int or publication["schema_version"] != 1:
        reject("readback-publication-source", "retry publication_source must have the exact version-1 schema")
    source_sha = publication.get("source_sha")
    workflow_sha = publication.get("workflow_sha")
    workflow_ref = publication.get("workflow_ref")
    if source_sha != readback["tag_sha"] or not isinstance(workflow_sha, str) or not HEX40.fullmatch(workflow_sha) \
            or workflow_sha == source_sha or workflow_ref != "refs/heads/main":
        reject("readback-publication-source", "retry must distinguish immutable tag S from main workflow G")
    repo = source.repo
    commit_check = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{workflow_sha}^{{commit}}"],
                                  capture_output=True, check=False)
    if commit_check.returncode != 0:
        reject("readback-publication-source", "retry workflow G is not an immutable commit object")
    ancestry = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", source_sha, workflow_sha],
                             capture_output=True, check=False)
    if ancestry.returncode != 0:
        reject("readback-publication-source", "tag source S is not an ancestor of retry workflow G")
    changed = subprocess.run(["git", "-C", str(repo), "diff", "--name-only", "-z", source_sha, workflow_sha],
                             capture_output=True, check=False)
    if changed.returncode != 0:
        reject("readback-publication-source", "the exact S-to-G recovery diff cannot be read")
    changed_paths = {item.decode("utf-8", errors="strict") for item in changed.stdout.split(b"\0") if item}
    if not changed_paths or changed_paths - RECOVERY_ALLOWED_PATHS:
        reject("readback-publication-source", "G must contain a non-empty diff limited to the approved recovery allowlist")

    source_paths = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "-z", "--name-only", source_sha],
                                  capture_output=True, check=False)
    if source_paths.returncode != 0:
        reject("readback-publication-source", "tag source S tree cannot be enumerated")
    source_path_set = {item.decode("utf-8", errors="strict") for item in source_paths.stdout.split(b"\0") if item}
    missing_critical = set(RECOVERY_CRITICAL_PATHS) - source_path_set
    if missing_critical or any(not any(path.startswith(prefix) for path in source_path_set)
                               for prefix in RECOVERY_CRITICAL_PREFIXES):
        reject("readback-publication-source", f"tag source S lacks required protected files: {sorted(missing_critical)}")
    protected_diff = subprocess.run(["git", "-C", str(repo), "diff", "--quiet", source_sha, workflow_sha,
                                     "--", *RECOVERY_CRITICAL_PATHS, *RECOVERY_CRITICAL_PREFIXES],
                                    capture_output=True, check=False)
    if protected_diff.returncode != 0:
        reject("readback-publication-source", "a protected product or policy blob changed between S and G")

    dispatch = publication.get("dispatch")
    if not isinstance(dispatch, dict) or set(dispatch) != RETRY_DISPATCH_KEYS \
            or dispatch.get("workflow") != "release-please.yml" or dispatch.get("ref") != "main":
        reject("readback-publication-source", "retry dispatch must explicitly name release-please.yml on main")
    inputs = dispatch.get("inputs")
    if not isinstance(inputs, dict) or set(inputs) != RETRY_INPUT_KEYS or inputs.get("retry") is not True \
            or inputs.get("tag_name") != readback["tag"] or inputs.get("source_sha") != source_sha \
            or inputs.get("release_id") != str(readback["release_id"]):
        reject("readback-publication-source", "retry dispatch inputs do not bind true retry, tag S and this draft ID")

    run_api = publication.get("run_api")
    if not isinstance(run_api, dict) or set(run_api) != RETRY_RUN_API_KEYS:
        reject("readback-publication-source", "retry run API projection has the wrong exact fields")
    run_id = run_api.get("id")
    attempt = run_api.get("run_attempt")
    if type(run_id) is not int or run_id < 1 or type(attempt) is not int or attempt < 1 \
            or run_api.get("path") != ".github/workflows/release-please.yml" \
            or run_api.get("event") != "workflow_dispatch" or run_api.get("head_branch") != "main" \
            or run_api.get("head_sha") != workflow_sha or run_api.get("status") != "completed" \
            or run_api.get("conclusion") != "success" \
            or run_api.get("repository_full_name") != "szTheory/gabbaboy":
        reject("readback-publication-source", "actual retry run must be a successful main workflow_dispatch at G")
    if release_run.get("workflow") != run_api["path"] or release_run.get("event") != run_api["event"] \
            or release_run.get("run_id") != run_id or release_run.get("head_sha") != workflow_sha \
            or release_run.get("conclusion") != "success":
        reject("readback-publication-source", "legacy release_run projection disagrees with the actual retry API run")
    if source_row.get("run_id") != run_id or source_row.get("run_attempt") != attempt:
        reject("readback-publication-source", "downloaded pre-publish inventory run/attempt differs from actual retry")

    jobs = []
    for key, tail in (("attach_job_api", "attach-qualified-v02-evidence"),
                      ("final_job_api", "final-downloaded-byte-gate-and-publish")):
        job = publication.get(key)
        if not isinstance(job, dict) or set(job) != RETRY_JOB_API_KEYS:
            reject("readback-publication-source", f"{key} must contain the exact job API projection")
        name = job.get("name")
        if type(job.get("id")) is not int or job["id"] < 1 or job.get("run_id") != run_id \
                or job.get("head_sha") != workflow_sha or not isinstance(name, str) or not name.endswith(tail) \
                or job.get("status") != "completed" or job.get("conclusion") != "success":
            reject("readback-publication-source", f"{key} is not the successful expected job from retry G")
        parsed = []
        for field in ("started_at", "completed_at"):
            value = job.get(field)
            if not isinstance(value, str):
                reject("readback-publication-source", f"{key}.{field} must be the actual API timestamp")
            try:
                stamp = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                reject("readback-publication-source", f"{key}.{field} is not an ISO timestamp")
            if stamp.tzinfo is None:
                reject("readback-publication-source", f"{key}.{field} must include a timezone")
            parsed.append(stamp)
        if parsed[1] < parsed[0]:
            reject("readback-publication-source", f"{key} completion precedes its start")
        jobs.append((job, int((parsed[1] - parsed[0]).total_seconds())))
    attach_job, attach_duration = jobs[0]
    final_job, _ = jobs[1]
    if attach.get("run_id") != run_id or attach.get("job_id") != attach_job["id"] \
            or attach.get("head_sha") != workflow_sha or attach.get("conclusion") != "success" \
            or attach.get("started_at") != attach_job["started_at"] \
            or attach.get("completed_at") != attach_job["completed_at"] \
            or attach.get("duration_seconds") != attach_duration \
            or release_run.get("final_publish_job_id") != final_job["id"]:
        reject("readback-publication-source", "legacy attach/final job fields differ from actual API job projections")

    raw_text = publication.get("release_receipt_raw")
    if not isinstance(raw_text, str):
        reject("readback-receipt-mismatch", "retry must retain the exact downloaded release-receipt UTF-8 bytes")
    raw_bytes = raw_text.encode("utf-8")
    if not raw_bytes or len(raw_bytes) > MAX_BYTES or b"\r" in raw_bytes \
            or hashlib.sha256(raw_bytes).hexdigest() != receipt.get("sha256"):
        reject("readback-receipt-mismatch", "downloaded raw release receipt bytes differ from the readback digest")
    raw_receipt = parse_json(raw_bytes, "downloaded release receipt", "readback-receipt-mismatch")
    if not isinstance(raw_receipt, dict) or raw_receipt.get("tag") != readback["tag"] \
            or raw_receipt.get("source_sha") != source_sha \
            or raw_receipt.get("release_id") != str(readback["release_id"]) \
            or raw_receipt.get("sha256sums_sha256") != hashlib.sha256(sums_bytes).hexdigest():
        reject("readback-receipt-mismatch", "raw release receipt tag/source/release or SHA256SUMS binding differs")
    perf = raw_receipt.get("perf_gate")
    perf_roms = {"libbet", "tracer", "visible-demo"}
    perf_keys = {"schema_version", "kind", "source_sha", "base_sha", "limits_blob", "ir", "digests",
                 "realtime_min", "tool", "run_id", "run_attempt"}
    if not isinstance(perf, dict) or set(perf) != perf_keys or type(perf.get("schema_version")) is not int \
            or perf.get("schema_version") != 1 or perf.get("kind") != "perf-gate-receipt" \
            or perf.get("source_sha") != source_sha or perf.get("base_sha") != "ab301aa69b1f085050fd66bf7b1378863a0821f2" \
            or not isinstance(perf.get("limits_blob"), str) or not HEX40.fullmatch(perf["limits_blob"]) \
            or not isinstance(perf.get("ir"), dict) or set(perf["ir"]) != perf_roms \
            or not isinstance(perf.get("digests"), dict) or set(perf["digests"]) != perf_roms \
            or not isinstance(perf.get("tool"), dict) \
            or set(perf["tool"]) != {"base_build_identity", "head_build_identity"} \
            or type(perf.get("run_id")) is not int or perf["run_id"] < 1 \
            or type(perf.get("run_attempt")) is not int or perf["run_attempt"] < 1 \
            or not isinstance(perf.get("realtime_min"), str) \
            or not re.fullmatch(r"[1-9][0-9]*/[1-9][0-9]*", perf["realtime_min"]):
        reject("readback-receipt-mismatch", "embedded perf receipt is not bound to exact product source S")
    limits_blob = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet",
                                  f"{source_sha}:tests/baseline/perf-gate-v1.txt"],
                                 capture_output=True, text=True, check=False)
    if limits_blob.returncode != 0 or limits_blob.stdout.strip() != perf["limits_blob"]:
        reject("readback-receipt-mismatch", "embedded perf receipt policy pin differs from source S")
    limits_bytes = subprocess.run(["git", "-C", str(repo), "show",
                                   f"{source_sha}:tests/baseline/perf-gate-v1.txt"],
                                  capture_output=True, check=False)
    if limits_bytes.returncode != 0:
        reject("readback-receipt-mismatch", "source S performance limits bytes are unavailable")
    digest_pins = perf_digest_pins(limits_bytes.stdout)
    for rom in perf_roms:
        ir = perf["ir"][rom]
        digests = perf["digests"][rom]
        if not isinstance(ir, dict) or set(ir) != {"base", "head"} or type(ir.get("base")) is not int \
                or ir["base"] < 1 or not isinstance(ir.get("head"), list) or len(ir["head"]) != 2 \
                or any(type(item) is not int or item < 1 for item in ir["head"]) \
                or not isinstance(digests, dict) or set(digests) != {"base", "head"} \
                or not isinstance(digests.get("base"), str) or not re.fullmatch(r"[0-9a-f]{16}", digests["base"]) \
                or not isinstance(digests.get("head"), list) or len(digests["head"]) != 2 \
                or any(not isinstance(item, str) or not re.fullmatch(r"[0-9a-f]{16}", item) for item in digests["head"]) \
                or digests["base"] != digest_pins[rom] or digests["head"] != [digest_pins[rom]] * 2:
            reject("readback-receipt-mismatch", f"embedded perf receipt {rom} digest differs from the pinned workload")
    for identity in perf["tool"].values():
        if identity is not None and (not isinstance(identity, str) or not HEX64.fullmatch(identity)):
            reject("readback-receipt-mismatch", "embedded perf receipt carries an invalid tool build identity")
    raw_assets = raw_receipt.get("assets")
    expected_raw_assets = receipt.get("assets")
    if not isinstance(raw_assets, list) or not isinstance(expected_raw_assets, list):
        reject("readback-receipt-mismatch", "raw and projected release receipt assets must be arrays")
    raw_by_name = {}
    raw_ids = set()
    inventory_ids = {item["name"]: item["id"] for item in readback["pre_publish_inventory"]}
    for item in raw_assets:
        if not isinstance(item, dict) or set(item) != {"name", "id", "sha256"} \
                or not isinstance(item.get("name"), str) or not item["name"] \
                or type(item.get("id")) is not int or item["id"] < 1 \
                or not isinstance(item.get("sha256"), str) or not HEX64.fullmatch(item["sha256"]) \
                or item["name"] in raw_by_name or item["id"] in raw_ids:
            reject("readback-receipt-mismatch", "raw release receipt assets must have unique name/id and exact digest fields")
        raw_by_name[item["name"]] = item
        raw_ids.add(item["id"])
    projected_by_name = {}
    for item in expected_raw_assets:
        if not isinstance(item, dict) or set(item) != {"name", "sha256"}:
            reject("readback-receipt-mismatch", "projected release receipt assets must omit only the API id")
        projected_by_name[item["name"]] = item["sha256"]
    if set(raw_by_name) != set(projected_by_name) or not set(raw_by_name) <= set(inventory_ids) \
            or any(raw_by_name[name]["sha256"] != projected_by_name[name]
                   or raw_by_name[name]["id"] != inventory_ids[name] for name in raw_by_name):
        reject("readback-receipt-mismatch", "raw receipt asset IDs/digests differ from the full inventory and projected receipt")
    return f"v03-readback retry pass workflow={workflow_sha} source={source_sha} attempt={attempt}"


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


def check_readback_v2(source: Source, readback, tag: str, repo: pathlib.Path, rev: str | None) -> str:
    """Reconcile the post-publication record to tag objects and its pre-publication artifact."""
    if not isinstance(readback, dict):
        reject("receipt-invalid", "readback must be a JSON object")
    release_run = readback.get("release_run")
    if not isinstance(release_run, dict) or type(release_run.get("retry")) is not bool:
        reject("receipt-invalid", "release_run must explicitly state whether this is a retry")
    is_retry = release_run["retry"] is True
    if "pre_publish_inventory_source" not in readback:
        reject("readback-inventory-unsourced", "pre-publish inventory source is required")
    expected_keys = READBACK_V2_KEYS | ({"publication_source"} if is_retry else set())
    if set(readback) != expected_keys:
        reject("receipt-invalid", f"readback must contain exactly {sorted(expected_keys)}")
    if not TAG.fullmatch(tag) or readback.get("tag") != tag or not isinstance(readback.get("tag_sha"), str) \
            or not HEX40.fullmatch(readback["tag_sha"]) or not isinstance(readback.get("tag_tree"), str) \
            or not HEX40.fullmatch(readback["tag_tree"]):
        reject("readback-tag-mismatch", "readback tag, commit or tree is malformed or differs from --tag")
    tag_commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"{tag}^{{commit}}"],
                                capture_output=True, text=True, check=False)
    tag_sha = tag_commit.stdout.strip() if tag_commit.returncode == 0 else None
    tag_tree = git_tree(repo, tag) if tag_sha is not None else None
    if tag_sha != readback["tag_sha"] or tag_tree != readback["tag_tree"]:
        reject("readback-tag-mismatch", "readback tag SHA/tree do not match the tag objects in the repository")
    if readback["is_draft"] is not False or readback["is_prerelease"] is not False:
        reject("receipt-invalid", "published readback must have is_draft and is_prerelease false")

    release_id = readback.get("release_id")
    if type(release_id) is not int or release_id < 1 or not isinstance(readback.get("published_at"), str) \
            or not readback["published_at"].strip() or not isinstance(readback.get("url"), str) \
            or not readback["url"].startswith("https://"):
        reject("receipt-invalid", "readback release id, publication time and URL are malformed")
    reconciliation = readback.get("reconciliation")
    if not isinstance(reconciliation, dict) or set(reconciliation) != {"verifier", "result", "compared_with", "asset_count"} \
            or any(not isinstance(reconciliation.get(key), str) or not reconciliation[key].strip()
                   for key in ("verifier", "result", "compared_with")) \
            or type(reconciliation.get("asset_count")) is not int or reconciliation["asset_count"] < 1:
        reject("receipt-invalid", "reconciliation must be a complete legacy-schema result")
    if not isinstance(release_run, dict) or set(release_run) != {
            "workflow", "run_id", "event", "retry", "head_sha", "conclusion", "final_publish_job_id"} \
            or not isinstance(release_run.get("workflow"), str) or not release_run["workflow"].strip() \
            or type(release_run.get("run_id")) is not int or release_run["run_id"] < 1 \
            or not isinstance(release_run.get("event"), str) or not release_run["event"].strip() \
            or type(release_run.get("retry")) is not bool \
            or release_run.get("conclusion") != "success" or type(release_run.get("final_publish_job_id")) is not int \
            or release_run["final_publish_job_id"] < 1:
        reject("receipt-invalid", "release_run must identify a successful candidate run with a positive final job id")
    attach = readback.get("attach_v02_evidence")
    if not isinstance(attach, dict) or set(attach) != {
            "run_id", "job_id", "head_sha", "conclusion", "started_at", "completed_at", "duration_seconds"} \
            or type(attach.get("run_id")) is not int or attach["run_id"] < 1 \
            or type(attach.get("job_id")) is not int or attach["job_id"] < 1 \
            or attach.get("conclusion") != "success" \
            or not isinstance(attach.get("started_at"), str) or not attach["started_at"].strip() \
            or not isinstance(attach.get("completed_at"), str) or not attach["completed_at"].strip() \
            or type(attach.get("duration_seconds")) is not int or attach["duration_seconds"] < 0:
        reject("receipt-invalid", "attach_v02_evidence must identify a successful attacher job")
    if not is_retry and (release_run.get("head_sha") != readback["tag_sha"]
                         or attach.get("head_sha") != readback["tag_sha"]):
        reject("readback-workflow-head-mismatch", "normal push runs must remain bound to the exact tag source")
    if not is_retry and (release_run.get("workflow") != ".github/workflows/release-please.yml"
                         or release_run.get("event") != "push"):
        reject("readback-workflow-identity", "normal readback must come from the release-please push workflow")

    source_row = readback.get("pre_publish_inventory_source")
    if not isinstance(source_row, dict) or set(source_row) != PRE_PUBLISH_SOURCE_KEYS \
            or type(source_row.get("run_id")) is not int or source_row["run_id"] < 1 \
            or type(source_row.get("run_attempt")) is not int or source_row["run_attempt"] < 1 \
            or type(source_row.get("artifact_id")) is not int or source_row["artifact_id"] < 1 \
            or not isinstance(source_row.get("artifact_name"), str) \
            or not isinstance(source_row.get("file_sha256"), str) or not HEX64.fullmatch(source_row["file_sha256"]) \
            or not isinstance(source_row.get("raw"), str):
        reject("readback-inventory-unsourced", "pre-publish inventory source metadata is missing or malformed")
    raw_bytes = source_row["raw"].encode("utf-8")
    if hashlib.sha256(raw_bytes).hexdigest() != source_row["file_sha256"]:
        reject("readback-inventory-unsourced", "pre-publish inventory raw bytes do not match file_sha256")
    try:
        inventory = parse_json(raw_bytes, "pre-publish inventory", "readback-inventory-unsourced")
    except Reject as error:
        if error.code == "readback-inventory-unsourced":
            raise
        reject("readback-inventory-unsourced", error.message)
    if not isinstance(inventory, dict) or set(inventory) != PRE_PUBLISH_KEYS \
            or inventory.get("schema_version") != 1 or inventory.get("kind") != "pre-publish-inventory" \
            or inventory.get("tag") != tag or inventory.get("source_sha") != readback["tag_sha"] \
            or inventory.get("release_id") != release_id or inventory.get("run_id") != source_row["run_id"] \
            or inventory.get("run_attempt") != source_row["run_attempt"] \
            or source_row["artifact_name"] != f"release-pre-publish-inventory-{source_row['run_id']}-{source_row['run_attempt']}" \
            or source_row["run_id"] != release_run["run_id"]:
        reject("readback-inventory-unsourced", "pre-publish inventory is not sourced from this release run and tag")
    inventory_assets = inventory.get("assets")
    if not isinstance(inventory_assets, list) or not inventory_assets:
        reject("readback-inventory-unsourced", "pre-publish inventory must contain a non-empty asset list")
    inventory_by_name = {}
    for item in inventory_assets:
        if not isinstance(item, dict) or set(item) != {"name", "id", "digest"} \
                or not isinstance(item.get("name"), str) or not item["name"] \
                or type(item.get("id")) is not int or item["id"] < 1 \
                or not isinstance(item.get("digest"), str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", item["digest"]):
            reject("readback-inventory-unsourced", "pre-publish inventory contains a malformed asset")
        if item["name"] in inventory_by_name:
            reject("readback-inventory-unsourced", "pre-publish inventory repeats an asset name")
        inventory_by_name[item["name"]] = item
    if readback.get("pre_publish_inventory") != inventory_assets:
        reject("readback-inventory-unsourced", "embedded inventory differs from the sourced pre-publish file")

    assets = readback.get("assets")
    if not isinstance(assets, list) or not assets:
        reject("readback-assets-mismatch", "published API asset list must be non-empty")
    assets_by_name = {}
    ids = set()
    for item in assets:
        if not isinstance(item, dict) or set(item) != {"name", "id", "size", "digest"} \
                or not isinstance(item.get("name"), str) or not item["name"] \
                or type(item.get("id")) is not int or item["id"] < 1 \
                or type(item.get("size")) is not int or item["size"] < 0 \
                or not isinstance(item.get("digest"), str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", item["digest"]):
            reject("readback-assets-mismatch", "published API asset list contains a malformed row")
        if item["name"] in assets_by_name or item["id"] in ids:
            reject("readback-assets-mismatch", "published API asset names and ids must be unique")
        assets_by_name[item["name"]] = item
        ids.add(item["id"])
    if not FINAL_ASSET_NAMES.issubset(inventory_by_name):
        reject("readback-inventory-unsourced", "the sourced inventory must include SHA256SUMS and release-receipt.json")
    if set(assets_by_name) != set(inventory_by_name):
        reject("readback-assets-mismatch", "published API asset names differ from the complete sourced inventory")
    for name, item in inventory_by_name.items():
        api_item = assets_by_name.get(name)
        if api_item is None or api_item["id"] != item["id"] or api_item["digest"] != item["digest"]:
            reject("readback-assets-mismatch", f"published asset {name} differs from its pre-publish id or digest")

    payload_names = set(inventory_by_name) - FINAL_ASSET_NAMES
    if not payload_names:
        reject("readback-inventory-unsourced", "the sourced inventory must include qualified payload assets")

    sums = readback.get("sha256sums")
    sums_asset = assets_by_name.get("SHA256SUMS")
    if not isinstance(sums, dict) or set(sums) != {"asset_id", "lines"} or sums_asset is None \
            or type(sums.get("asset_id")) is not int or sums["asset_id"] != sums_asset["id"] \
            or not isinstance(sums.get("lines"), list):
        reject("readback-digest-mismatch", "SHA256SUMS asset reference or lines are malformed")
    checksums = {}
    for line in sums["lines"]:
        if not isinstance(line, str):
            reject("readback-digest-mismatch", "SHA256SUMS lines must be text")
        match = SHA256_LINE.fullmatch(line)
        if not match or match[2] in checksums:
            reject("readback-digest-mismatch", "SHA256SUMS contains a malformed or duplicate line")
        checksums[match[2]] = match[1]
    expected_sum_names = payload_names
    if set(checksums) != expected_sum_names:
        reject("readback-digest-mismatch", "SHA256SUMS names differ from the published assets it must cover")
    for name, digest in checksums.items():
        if digest != assets_by_name[name]["digest"][7:]:
            reject("readback-digest-mismatch", f"SHA256SUMS digest for {name} differs from its API digest")
    sums_bytes = ("\n".join(sums["lines"]) + "\n").encode("utf-8")
    if hashlib.sha256(sums_bytes).hexdigest() != sums_asset["digest"][7:]:
        reject("readback-digest-mismatch", "SHA256SUMS bytes differ from the digest of the attached metadata asset")

    receipt = readback.get("release_receipt")
    receipt_asset = assets_by_name.get("release-receipt.json")
    if not isinstance(receipt, dict) or set(receipt) != {"asset_id", "sha256", "assets"} \
            or receipt_asset is None or type(receipt.get("asset_id")) is not int \
            or receipt["asset_id"] != receipt_asset["id"] \
            or not isinstance(receipt.get("sha256"), str) or not HEX64.fullmatch(receipt["sha256"]) \
            or receipt["sha256"] != receipt_asset["digest"][7:]:
        reject("readback-receipt-mismatch", "release-receipt asset id or digest differs from the API")
    receipt_assets = receipt.get("assets")
    if not isinstance(receipt_assets, list) or len(receipt_assets) != len(payload_names):
        reject("readback-receipt-mismatch", "release receipt asset digests do not cover the sourced inventory")
    receipt_by_name = {}
    for item in receipt_assets:
        if not isinstance(item, dict) or set(item) != {"name", "sha256"} \
                or not isinstance(item.get("name"), str) or not item["name"] \
                or not isinstance(item.get("sha256"), str) or not HEX64.fullmatch(item["sha256"]) \
                or item["name"] in receipt_by_name:
            reject("readback-receipt-mismatch", "release receipt contains a malformed asset digest")
        receipt_by_name[item["name"]] = item["sha256"]
    if set(receipt_by_name) != payload_names or any(
            receipt_by_name[name] != inventory_by_name[name]["digest"][7:] for name in payload_names):
        reject("readback-receipt-mismatch", "release receipt asset digests differ from the sourced API inventory")

    if is_retry:
        check_retry_publication_source(source, readback, release_run, attach, source_row,
                                       sums_bytes, receipt)

    ledger = readback.get("sidecar_ledger")
    expected_ledger_path = f"docs/support/{tag}.md"
    if not isinstance(ledger, dict) or set(ledger) != {"path", "git_blob_oid"} \
            or ledger.get("path") != expected_ledger_path or not isinstance(ledger.get("git_blob_oid"), str) \
            or not HEX40.fullmatch(ledger["git_blob_oid"]):
        reject("readback-ledger-blob-mismatch", "sidecar ledger path or Git blob id is malformed")
    blob = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"{tag}:{expected_ledger_path}"],
                          capture_output=True, text=True, check=False)
    blob_oid = blob.stdout.strip() if blob.returncode == 0 else None
    blob_type = subprocess.run(["git", "-C", str(repo), "cat-file", "-t", blob_oid], capture_output=True, text=True,
                               check=False) if blob_oid else None
    if blob_oid != ledger["git_blob_oid"] or blob_type is None or blob_type.returncode != 0 or blob_type.stdout.strip() != "blob":
        reject("readback-ledger-blob-mismatch", "sidecar ledger blob does not match the tag's support ledger")

    try:
        if FORBIDDEN_TEXT.search(json.dumps(readback, sort_keys=True, ensure_ascii=False)):
            reject("readback-private-text", "readback contains a personal path, token or private-key marker")
    except (TypeError, ValueError):
        reject("readback-private-text", "readback cannot be safely scanned for private text")
    lifecycle = source.read(READBACK_LIFECYCLE_REL, "readback-pattern-mismatch").decode("utf-8", errors="strict")
    copied_pattern = next((line.strip() for line in lifecycle.splitlines() if line.startswith("FORBIDDEN_TEXT =")), None)
    if copied_pattern != FORBIDDEN_TEXT_ASSIGNMENT:
        reject("readback-pattern-mismatch", "copied FORBIDDEN_TEXT pattern differs from the lifecycle checker at this revision")

    return f"v03-readback pass tag={tag} assets={len(assets)}"


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
            normalized = pathlib.PurePosixPath(path)
            parts = path.split("/")
            if "\\" in path or path.startswith("/") or re.match(r"^[A-Za-z]:", path) \
                    or any(part in ("", ".", "..") for part in parts) or normalized.as_posix() != path:
                reject("pr-closure-invalid", f"#{number} changed path {path!r} is not a canonical repository-relative path")
            first = parts[0].lower()
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
RECORD_REL = "fixture/16-DISPOSITIONS.json"
READBACK_REL = "fixture/16-release-readback.json"
CLOSURES_REL = "fixture/16-pr-closures.json"
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


def build_readback_fixture(base: pathlib.Path) -> dict:
    repo = base / "readback-repo"
    for path in RECOVERY_CRITICAL_PATHS:
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"protected fixture {path}\n", encoding="utf-8")
    limits_path = "tests/baseline/perf-gate-v1.txt"
    limits = subprocess.run(["git", "-C", str(ROOT), "show", f"a3f3390451f9a893aa47475f15a722ada86daaa6:{limits_path}"],
                            capture_output=True, check=False)
    if limits.returncode != 0:
        raise SystemExit("self-test cannot read the immutable S performance limits")
    (repo / limits_path).write_bytes(limits.stdout)
    lifecycle_pattern = repo / READBACK_LIFECYCLE_REL
    lifecycle_pattern.parent.mkdir(parents=True, exist_ok=True)
    production_lifecycle = ROOT / READBACK_LIFECYCLE_REL
    if not production_lifecycle.is_file():
        raise SystemExit(f"self-test cannot find production lifecycle checker at {READBACK_LIFECYCLE_REL}")
    lifecycle_pattern.write_bytes(production_lifecycle.read_bytes())
    (repo / "src/core.c").parent.mkdir(parents=True)
    (repo / "src/core.c").write_text("protected core fixture\n", encoding="utf-8")
    (repo / "include/gabbaboy.h").parent.mkdir(parents=True)
    (repo / "include/gabbaboy.h").write_text("protected public API fixture\n", encoding="utf-8")
    (repo / "docs/support").mkdir(parents=True, exist_ok=True)
    (repo / "fixture").mkdir()
    (repo / READBACK_LEDGER_REL).write_text("# v0.3.0 fixture ledger\n", encoding="utf-8")
    git(repo.parent, "init", "-q", "readback-repo")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "fixture: tagged support ledger")
    tag_sha = git(repo, "rev-parse", "HEAD")
    tag_tree = git(repo, "rev-parse", "HEAD^{tree}")
    blob_oid = git(repo, "rev-parse", f"HEAD:{READBACK_LEDGER_REL}")
    git(repo, "tag", "v0.3.0")
    (repo / "docs/release.md").write_text("approved recovery procedure fixture\n", encoding="utf-8")
    (repo / "tests/scripts/verify-v03-dispositions.py").write_text("approved readback checker fixture\n", encoding="utf-8")
    git(repo, "add", "docs/release.md", "tests/scripts/verify-v03-dispositions.py")
    git(repo, "commit", "-q", "-m", "fixture: allowlisted corrective revision")
    workflow_sha = git(repo, "rev-parse", "HEAD")
    base_branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    git(repo, "checkout", "-q", "-b", "fixture-forbidden")
    (repo / "src/core.c").write_text("mutated protected core fixture\n", encoding="utf-8")
    git(repo, "add", "src/core.c")
    git(repo, "commit", "-q", "-m", "fixture: forbidden product source change")
    forbidden_sha = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-q", base_branch)

    payload_name = "gabbaboy-core-linux-x64.tar.gz"
    payload_bytes = b"qualified fixture archive\n"
    original_digest = hashlib.sha256(payload_bytes).hexdigest()
    sums_lines = [f"{original_digest}  {payload_name}"]
    sums_asset_bytes = (sums_lines[0] + "\n").encode("utf-8")
    sums_sha = hashlib.sha256(sums_asset_bytes).hexdigest()
    perf_roms = {"libbet", "tracer", "visible-demo"}
    perf_limits_blob = git(repo, "rev-parse", f"{tag_sha}:tests/baseline/perf-gate-v1.txt")
    fixture_digest_pins = perf_digest_pins(limits.stdout)
    perf_ir = {
        "libbet": {"base": 239287537, "head": [262017211, 262017211]},
        "tracer": {"base": 233590054, "head": [255901403, 255901403]},
        "visible-demo": {"base": 240007926, "head": [262724206, 262724206]},
    }
    perf = {
        "schema_version": 1, "kind": "perf-gate-receipt", "source_sha": tag_sha,
        "base_sha": "ab301aa69b1f085050fd66bf7b1378863a0821f2", "limits_blob": perf_limits_blob,
        "ir": perf_ir,
        "digests": {name: {"base": fixture_digest_pins[name], "head": [fixture_digest_pins[name]] * 2}
                    for name in perf_roms},
        "realtime_min": "244138671875/27914573824",
        "tool": {
            "base_build_identity": "00ab5ac891ee6b9ce6c80ad1fa30d303199f6c9cf026656e070688f4a55d66c3",
            "head_build_identity": "b7dbf3ed5b613562690f15f0caea464c83c1a28ff72e5ff838251de174d37a65",
        },
        "run_id": 41148606861, "run_attempt": 1,
    }
    receipt_document = {
        "schema_version": 1, "version": "0.3.0", "tag": "v0.3.0", "source_sha": tag_sha,
        "release_id": "7001", "draft": True, "signed": False, "notarized": False,
        "hardware_qualified": False, "sha256sums_sha256": sums_sha,
        "assets": [{"name": payload_name, "id": 901, "sha256": original_digest}], "perf_gate": perf,
    }
    receipt_asset_bytes = (json.dumps(receipt_document, sort_keys=True, indent=2) + "\n").encode("utf-8")
    receipt_asset_digest = hashlib.sha256(receipt_asset_bytes).hexdigest()
    inventory_assets = [
        {"name": payload_name, "id": 901, "digest": f"sha256:{original_digest}"},
        {"name": "SHA256SUMS", "id": 902, "digest": f"sha256:{hashlib.sha256(sums_asset_bytes).hexdigest()}"},
        {"name": "release-receipt.json", "id": 903, "digest": f"sha256:{receipt_asset_digest}"},
    ]
    inventory = {"schema_version": 1, "kind": "pre-publish-inventory", "tag": "v0.3.0", "source_sha": tag_sha,
                 "release_id": 7001, "run_id": 8001, "run_attempt": 2, "assets": inventory_assets}
    inventory_raw = (json.dumps(inventory, sort_keys=True, indent=2) + "\n")
    api_assets = [
        {"name": payload_name, "id": 901, "size": len(payload_bytes), "digest": f"sha256:{original_digest}"},
        {"name": "SHA256SUMS", "id": 902, "size": len(sums_asset_bytes),
         "digest": f"sha256:{hashlib.sha256(sums_asset_bytes).hexdigest()}"},
        {"name": "release-receipt.json", "id": 903, "size": len(receipt_asset_bytes), "digest": f"sha256:{receipt_asset_digest}"},
    ]
    readback = {
        "tag": "v0.3.0", "tag_sha": tag_sha, "tag_tree": tag_tree, "is_draft": False, "is_prerelease": False,
        "release_id": 7001, "published_at": "2026-10-29T12:00:00Z",
        "url": "https://github.com/example/gabbaboy/releases/tag/v0.3.0", "assets": api_assets,
        "reconciliation": {"verifier": ".github/scripts/verify-published-release-assets.py",
                            "result": "PASS: published assets match", "compared_with": "pre-publish inventory",
                            "asset_count": len(api_assets)},
        "release_run": {"workflow": ".github/workflows/release-please.yml", "run_id": 8001, "event": "push",
                        "retry": False, "head_sha": tag_sha, "conclusion": "success", "final_publish_job_id": 8101},
        "attach_v02_evidence": {"run_id": 8001, "job_id": 8102, "head_sha": tag_sha, "conclusion": "success",
                                 "started_at": "2026-10-29T11:00:00Z", "completed_at": "2026-10-29T11:01:00Z",
                                 "duration_seconds": 60},
        "pre_publish_inventory": inventory_assets,
        "pre_publish_inventory_source": {"run_id": 8001, "run_attempt": 2,
                                          "artifact_name": "release-pre-publish-inventory-8001-2", "artifact_id": 8201,
                                          "file_sha256": hashlib.sha256(inventory_raw.encode()).hexdigest(),
                                          "raw": inventory_raw},
        "sha256sums": {"asset_id": 902, "lines": sums_lines},
        "release_receipt": {"asset_id": 903, "sha256": receipt_asset_digest,
                            "assets": [{"name": payload_name, "sha256": original_digest}]},
        "sidecar_ledger": {"path": READBACK_LEDGER_REL, "git_blob_oid": blob_oid},
    }
    (repo / READBACK_V2_REL).write_bytes(serialise(readback))
    git(repo, "add", READBACK_V2_REL)
    git(repo, "commit", "-q", "-m", "fixture: committed published readback")
    return {"repo": repo, "readback": readback, "head": git(repo, "rev-parse", "HEAD"), "tag_sha": tag_sha,
            "workflow_sha": workflow_sha, "forbidden_sha": forbidden_sha,
            "release_receipt_raw": receipt_asset_bytes.decode("utf-8"),
            "workflow_ref": "refs/heads/main"}


def retry_readback_fixture(facts: dict) -> dict:
    """Build a retry attempt-one projection with API heads at G and downloaded product evidence at S."""
    readback = json.loads(json.dumps(facts["readback"]))
    repo = facts["repo"]
    run_id, attempt = 8002, 1
    inventory_source = readback["pre_publish_inventory_source"]
    inventory = json.loads(inventory_source["raw"])
    inventory.update(run_id=run_id, run_attempt=attempt)
    inventory_raw = json.dumps(inventory, sort_keys=True, indent=2) + "\n"
    inventory_source.update(run_id=run_id, run_attempt=attempt,
                           artifact_name=f"release-pre-publish-inventory-{run_id}-{attempt}",
                           artifact_id=8202, file_sha256=hashlib.sha256(inventory_raw.encode("utf-8")).hexdigest(),
                           raw=inventory_raw)
    attach_started, attach_completed = "2026-10-29T11:00:00Z", "2026-10-29T11:01:00Z"
    final_started, final_completed = "2026-10-29T11:01:00Z", "2026-10-29T11:02:00Z"
    workflow_sha = facts["workflow_sha"]
    run_path = ".github/workflows/release-please.yml"
    readback["release_run"] = {
        "workflow": run_path, "run_id": run_id, "event": "workflow_dispatch", "retry": True,
        "head_sha": workflow_sha, "conclusion": "success", "final_publish_job_id": 8113,
    }
    readback["attach_v02_evidence"] = {
        "run_id": run_id, "job_id": 8112, "head_sha": workflow_sha, "conclusion": "success",
        "started_at": attach_started, "completed_at": attach_completed, "duration_seconds": 60,
    }
    readback["publication_source"] = {
        "schema_version": 1, "source_sha": facts["tag_sha"], "workflow_sha": workflow_sha,
        "workflow_ref": facts["workflow_ref"],
        "dispatch": {"workflow": "release-please.yml", "ref": "main", "inputs": {
            "retry": True, "tag_name": "v0.3.0", "source_sha": facts["tag_sha"], "release_id": "7001",
        }},
        "run_api": {
            "id": run_id, "run_attempt": attempt, "path": run_path, "event": "workflow_dispatch",
            "head_branch": "main", "head_sha": workflow_sha, "status": "completed", "conclusion": "success",
            "repository_full_name": "szTheory/gabbaboy",
        },
        "attach_job_api": {
            "id": 8112, "run_id": run_id, "head_sha": workflow_sha,
            "name": "attach-qualified-v02-evidence", "status": "completed", "conclusion": "success",
            "started_at": attach_started, "completed_at": attach_completed,
        },
        "final_job_api": {
            "id": 8113, "run_id": run_id, "head_sha": workflow_sha,
            "name": "final-downloaded-byte-gate-and-publish", "status": "completed", "conclusion": "success",
            "started_at": final_started, "completed_at": final_completed,
        },
        "release_receipt_raw": facts["release_receipt_raw"],
    }
    return readback


def run_cli(repo: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", str(SCRIPT), "--repo", str(repo), *args], capture_output=True, text=True,
                          timeout=120, check=False)


def bind_retry_receipt_bytes(readback: dict, raw_text: str) -> None:
    """Keep API, downloaded receipt, and pre-publish inventory digests consistent in a semantic negative."""
    raw = raw_text.encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    readback["publication_source"]["release_receipt_raw"] = raw_text
    readback["release_receipt"]["sha256"] = digest
    receipt_asset = next(item for item in readback["assets"] if item["name"] == "release-receipt.json")
    receipt_asset.update(size=len(raw), digest=f"sha256:{digest}")
    inventory_assets = readback["pre_publish_inventory"]
    inventory_receipt = next(item for item in inventory_assets if item["name"] == "release-receipt.json")
    inventory_receipt["digest"] = f"sha256:{digest}"
    source_row = readback["pre_publish_inventory_source"]
    inventory = json.loads(source_row["raw"])
    inventory["assets"] = inventory_assets
    inventory_raw = json.dumps(inventory, sort_keys=True, indent=2) + "\n"
    source_row["raw"] = inventory_raw
    source_row["file_sha256"] = hashlib.sha256(inventory_raw.encode("utf-8")).hexdigest()


def set_retry_heads(readback: dict, head: str) -> None:
    """Bind all API and legacy control-plane head projections to one candidate head."""
    readback["publication_source"]["workflow_sha"] = head
    readback["release_run"]["head_sha"] = head
    readback["attach_v02_evidence"]["head_sha"] = head
    readback["publication_source"]["run_api"]["head_sha"] = head
    readback["publication_source"]["attach_job_api"]["head_sha"] = head
    readback["publication_source"]["final_job_api"]["head_sha"] = head


def require_python_310_grammar(source: str) -> None:
    """Reject syntax newer than the supported Python 3.10 grammar, including PEP 701 f-string escapes."""
    ast.parse(source, feature_version=(3, 10))
    fstring_start = getattr(tokenize, "FSTRING_START", None)
    fstring_end = getattr(tokenize, "FSTRING_END", None)
    if fstring_start is None or fstring_end is None:
        # Python 3.10/3.11's parser itself rejects backslashes in f-string expressions.
        return

    contexts: list[dict[str, int | bool]] = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == fstring_start:
            contexts.append({"in_expression": False, "brace_depth": 0})
            continue
        if token.type == fstring_end:
            if not contexts:
                raise ValueError("unbalanced f-string token stream")
            contexts.pop()
            continue
        if not contexts:
            continue

        context = contexts[-1]
        if context["in_expression"] and token.type == tokenize.STRING and "\\" in token.string:
            raise ValueError("Python 3.10 does not allow backslashes in f-string expressions")
        if token.type != tokenize.OP:
            continue
        if not context["in_expression"] and token.string == "{":
            context["in_expression"] = True
            context["brace_depth"] = 1
        elif context["in_expression"] and token.string == "{":
            context["brace_depth"] = int(context["brace_depth"]) + 1
        elif context["in_expression"] and token.string == "}":
            context["brace_depth"] = int(context["brace_depth"]) - 1
            if context["brace_depth"] == 0:
                context["in_expression"] = False


def python_310_grammar_controls() -> int:
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    require_python_310_grammar(source)

    # Python 3.12 accepts this PEP 701 form; Python 3.10 rejects its backslash in the
    # replacement field. Keep the exact escaped bytes-literal shape that failed in CI.
    incompatible = "value = f\"{hashlib.sha256(b'sums asset bytes\\n').hexdigest()}\""
    try:
        ast.parse(incompatible)
    except SyntaxError:
        # Running directly on the supported floor naturally rejects the seeded syntax.
        return 2
    try:
        require_python_310_grammar(incompatible)
    except (SyntaxError, ValueError):
        return 2
    raise SystemExit("Python 3.10 grammar controls accepted the seeded PEP 701 f-string")


def self_test() -> int:
    controls = python_310_grammar_controls()
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

        def closures_traversing_src(variant, files):
            document = json.loads(closures_raw)
            document["prs"][3]["changed_paths"].append("docs/placeholder/../../src/core/gabbaboy.c")
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
        case("pr-closures receipt traversing into src", "pr-closure-invalid", closures_traversing_src)
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


def self_test_readback() -> int:
    controls = 0
    with tempfile.TemporaryDirectory(prefix="gabbaboy-v03-readback-") as temporary:
        facts = build_readback_fixture(pathlib.Path(temporary))
        repo = facts["repo"]
        original = json.loads(json.dumps(facts["readback"]))

        def invoke(rev: str | None = None) -> subprocess.CompletedProcess:
            args = ["--check-readback", READBACK_V2_REL, "--tag", "v0.3.0"]
            if rev is not None:
                args.extend(("--rev", rev))
            return run_cli(repo, *args)

        def expect_pass(label: str, result: subprocess.CompletedProcess) -> None:
            if result.returncode != 0 or "v03-readback pass tag=v0.3.0 assets=3" not in result.stdout:
                raise SystemExit(f"self-test positive {label} failed: {result.stderr.strip() or result.stdout.strip()}")

        def expect_reject(label: str, result: subprocess.CompletedProcess, code: str) -> None:
            nonlocal controls
            if result.returncode == 0 or "v03-readback pass" in result.stdout:
                raise SystemExit(f"self-test accepted {label}")
            if f"REJECT {code}:" not in result.stderr:
                raise SystemExit(f"self-test {label}: expected REJECT {code}, got: {result.stderr.strip()[:240]}")
            controls += 1

        def case(label: str, code: str, mutate, *, lifecycle: str | None = None) -> None:
            variant = json.loads(json.dumps(original))
            mutate(variant)
            (repo / READBACK_V2_REL).write_bytes(serialise(variant))
            if lifecycle is not None:
                (repo / READBACK_LIFECYCLE_REL).write_text(lifecycle, encoding="utf-8")
            git(repo, "add", "-A")
            git(repo, "commit", "-q", "--allow-empty", "-m", f"fixture: {label}")
            head = git(repo, "rev-parse", "HEAD")
            expect_reject(label, invoke(), code)
            expect_reject(label + " at rev", invoke(head), code)

        positive = invoke()
        expect_pass("working tree", positive)
        head = git(repo, "rev-parse", "HEAD")
        committed_positive = invoke(head)
        expect_pass("commit", committed_positive)
        repeated_positive = invoke(head)
        expect_pass("repeated commit", repeated_positive)
        if committed_positive.stdout != repeated_positive.stdout:
            raise SystemExit("self-test positive output is not byte-identical across repeated runs")

        retry_original = retry_readback_fixture(facts)
        (repo / READBACK_V2_REL).write_bytes(serialise(retry_original))
        git(repo, "add", READBACK_V2_REL)
        git(repo, "commit", "-q", "-m", "fixture: successful main retry at attempt one")
        retry_head = git(repo, "rev-parse", "HEAD")
        retry_positive = invoke(retry_head)
        expect_pass("explicit main retry", retry_positive)
        repeated_retry = invoke(retry_head)
        expect_pass("repeated explicit main retry", repeated_retry)
        if retry_positive.stdout != repeated_retry.stdout:
            raise SystemExit("retry self-test output is not byte-identical across repeated runs")

        def retry_case(label: str, code: str, mutate) -> None:
            nonlocal controls
            variant = json.loads(json.dumps(retry_original))
            mutate(variant)
            (repo / READBACK_V2_REL).write_bytes(serialise(variant))
            git(repo, "add", READBACK_V2_REL)
            git(repo, "commit", "-q", "--allow-empty", "-m", f"fixture: reject retry {label}")
            head = git(repo, "rev-parse", "HEAD")
            expect_reject(label, invoke(), code)
            expect_reject(label + " at rev", invoke(head), code)

        retry_case("missing publication source", "receipt-invalid",
                   lambda value: value.pop("publication_source"))
        retry_case("wrong run head", "readback-publication-source",
                   lambda value: value["publication_source"]["run_api"].update(head_sha=facts["tag_sha"]))
        retry_case("all workflow heads substituted with S", "readback-publication-source",
                   lambda value: set_retry_heads(value, facts["tag_sha"]))
        retry_case("workflow G contains forbidden product change", "readback-publication-source",
                   lambda value: set_retry_heads(value, facts["forbidden_sha"]))
        retry_case("wrong retry source", "readback-publication-source",
                   lambda value: value["publication_source"].update(source_sha="0" * 40))
        retry_case("missing explicit dispatch inputs", "readback-publication-source",
                   lambda value: value["publication_source"].update(dispatch={"workflow": "release-please.yml", "ref": "main"}))
        retry_case("false dispatch retry", "readback-publication-source",
                   lambda value: value["publication_source"]["dispatch"]["inputs"].update(retry=False))
        retry_case("wrong dispatch tag", "readback-publication-source",
                   lambda value: value["publication_source"]["dispatch"]["inputs"].update(tag_name="v0.2.1"))
        retry_case("wrong dispatch ref", "readback-publication-source",
                   lambda value: value["publication_source"]["dispatch"].update(ref="v0.3.0"))
        retry_case("wrong workflow ref", "readback-publication-source",
                   lambda value: value["publication_source"].update(workflow_ref="refs/tags/v0.3.0"))
        retry_case("pull request retry event", "readback-publication-source",
                   lambda value: value["publication_source"]["run_api"].update(event="pull_request"))
        retry_case("foreign repository", "readback-publication-source",
                   lambda value: value["publication_source"]["run_api"].update(repository_full_name="attacker/gabbaboy"))
        retry_case("failed final job", "readback-publication-source",
                   lambda value: value["publication_source"]["final_job_api"].update(conclusion="failure"))
        retry_case("skipped attacher job", "readback-publication-source",
                   lambda value: value["publication_source"]["attach_job_api"].update(conclusion="skipped"))
        retry_case("wrong attempt binding", "readback-publication-source",
                   lambda value: value["publication_source"]["run_api"].update(run_attempt=2))
        retry_case("wrong job run id", "readback-publication-source",
                   lambda value: value["publication_source"]["attach_job_api"].update(run_id=9999))
        retry_case("wrong attacher duration", "readback-publication-source",
                   lambda value: value["attach_v02_evidence"].update(duration_seconds=61))
        retry_case("raw receipt byte drift", "readback-receipt-mismatch",
                   lambda value: value["publication_source"].update(
                       release_receipt_raw=value["publication_source"]["release_receipt_raw"] + " "))

        def wrong_raw_source(value):
            raw = json.loads(value["publication_source"]["release_receipt_raw"])
            raw["source_sha"] = "0" * 40
            bind_retry_receipt_bytes(value, json.dumps(raw, sort_keys=True, indent=2) + "\n")

        retry_case("raw receipt wrong source", "readback-receipt-mismatch", wrong_raw_source)

        def wrong_perf_source(value):
            raw = json.loads(value["publication_source"]["release_receipt_raw"])
            raw["perf_gate"]["source_sha"] = "0" * 40
            bind_retry_receipt_bytes(value, json.dumps(raw, sort_keys=True, indent=2) + "\n")

        retry_case("embedded perf source drift", "readback-receipt-mismatch", wrong_perf_source)

        def wrong_perf_digest_width(value):
            raw = json.loads(value["publication_source"]["release_receipt_raw"])
            raw["perf_gate"]["digests"]["tracer"]["base"] = "4c7a57ff3d50d22"
            bind_retry_receipt_bytes(value, json.dumps(raw, sort_keys=True, indent=2) + "\n")

        retry_case("producer FNV digest width", "readback-receipt-mismatch", wrong_perf_digest_width)

        def wrong_perf_digest_pin(value):
            raw = json.loads(value["publication_source"]["release_receipt_raw"])
            raw["perf_gate"]["digests"]["tracer"]["base"] = "0000000000000000"
            bind_retry_receipt_bytes(value, json.dumps(raw, sort_keys=True, indent=2) + "\n")

        retry_case("producer digest differs from pinned workload", "readback-receipt-mismatch", wrong_perf_digest_pin)

        def wrong_perf_repeat(value):
            raw = json.loads(value["publication_source"]["release_receipt_raw"])
            raw["perf_gate"]["digests"]["tracer"]["head"][1] = "0000000000000000"
            bind_retry_receipt_bytes(value, json.dumps(raw, sort_keys=True, indent=2) + "\n")

        retry_case("producer head digests differ", "readback-receipt-mismatch", wrong_perf_repeat)

        def wrong_raw_asset_id(value):
            raw = json.loads(value["publication_source"]["release_receipt_raw"])
            raw["assets"][0]["id"] += 1
            bind_retry_receipt_bytes(value, json.dumps(raw, sort_keys=True, indent=2) + "\n")

        retry_case("raw receipt asset ID mismatch", "readback-receipt-mismatch", wrong_raw_asset_id)

        def duplicate_raw_key(value):
            raw = value["publication_source"]["release_receipt_raw"]
            duplicated = raw.replace('"tag": "v0.3.0",', '"tag": "v0.3.0",\n  "tag": "v0.3.0",', 1)
            bind_retry_receipt_bytes(value, duplicated)

        retry_case("duplicate raw receipt key", "readback-receipt-mismatch", duplicate_raw_key)

        case("tag sha mismatch", "readback-tag-mismatch", lambda value: value.update(tag_sha="0" * 40))
        case("tag tree mismatch", "readback-tag-mismatch", lambda value: value.update(tag_tree="0" * 40))
        case("another tag", "readback-tag-mismatch", lambda value: value.update(tag="v0.3.9"))
        case("draft release", "receipt-invalid", lambda value: value.update(is_draft=True))
        case("normal push alternate workflow head", "readback-workflow-head-mismatch",
             lambda value: value["release_run"].update(head_sha=facts["workflow_sha"]))
        case("normal push arbitrary workflow", "readback-workflow-identity",
             lambda value: value["release_run"].update(workflow=".github/workflows/arbitrary.yml"))
        case("normal pull request event", "readback-workflow-identity",
             lambda value: value["release_run"].update(event="pull_request"))
        case("normal dispatch with retry false", "readback-workflow-identity",
             lambda value: value["release_run"].update(event="workflow_dispatch"))
        case("added asset", "readback-assets-mismatch",
             lambda value: value["assets"].append({"name": "unexpected.bin", "id": 999, "size": 1,
                                                   "digest": "sha256:" + "1" * 64}))
        case("removed asset", "readback-assets-mismatch", lambda value: value["assets"].pop(0))
        case("changed asset id", "readback-assets-mismatch", lambda value: value["assets"][0].update(id=990))
        case("changed asset digest", "readback-assets-mismatch",
             lambda value: value["assets"][0].update(digest="sha256:" + "1" * 64))
        case("changed SHA256SUMS asset id", "readback-assets-mismatch",
             lambda value: value["assets"][1].update(id=990))
        case("changed release-receipt asset digest", "readback-assets-mismatch",
             lambda value: value["assets"][2].update(digest="sha256:" + "1" * 64))
        case("checksum digest mismatch", "readback-digest-mismatch",
             lambda value: value["sha256sums"].update(lines=["1" * 64 + "  gabbaboy-core-linux-x64.tar.gz"]))
        case("receipt asset digest mismatch", "readback-receipt-mismatch",
             lambda value: value["release_receipt"]["assets"][0].update(sha256="1" * 64))
        case("receipt file digest mismatch", "readback-receipt-mismatch",
             lambda value: value["release_receipt"].update(sha256="1" * 64))
        case("ledger blob mismatch", "readback-ledger-blob-mismatch",
             lambda value: value["sidecar_ledger"].update(git_blob_oid="0" * 40))
        case("personal path", "readback-private-text", lambda value: value.update(url="https://example.invalid/Users/private"))
        case("credential token", "readback-private-text", lambda value: value.update(url="https://example.invalid/ghp_" + "a" * 30))
        case("inventory differs from sourced raw", "readback-inventory-unsourced",
             lambda value: value["pre_publish_inventory"][0].update(id=990))
        case("inventory raw digest mismatch", "readback-inventory-unsourced",
             lambda value: value["pre_publish_inventory_source"].update(raw=value["pre_publish_inventory_source"]["raw"] + " "))
        case("inventory raw tag mismatch", "readback-inventory-unsourced",
             lambda value: value["pre_publish_inventory_source"].update(
                 raw=json.dumps(dict(json.loads(value["pre_publish_inventory_source"]["raw"]), tag="v0.3.9"))))
        case("inventory raw release id mismatch", "readback-inventory-unsourced",
             lambda value: value["pre_publish_inventory_source"].update(
                 raw=json.dumps(dict(json.loads(value["pre_publish_inventory_source"]["raw"],), release_id=9))))
        case("inventory raw run id mismatch", "readback-inventory-unsourced",
             lambda value: value["pre_publish_inventory_source"].update(
                 raw=json.dumps(dict(json.loads(value["pre_publish_inventory_source"]["raw"]), run_id=9))))
        case("missing inventory source", "readback-inventory-unsourced",
             lambda value: value.pop("pre_publish_inventory_source"))
        case("wrong inventory artifact source", "readback-inventory-unsourced",
             lambda value: value["pre_publish_inventory_source"].update(artifact_name="untrusted.json"))
        case("privacy pattern drift", "readback-pattern-mismatch", lambda value: None,
             lifecycle="FORBIDDEN_TEXT = re.compile(r'wrong')\n")
    print(f"v03-readback controls pass controls={controls}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", metavar="PATH", help="the disposition record, relative to the repository (or absolute)")
    parser.add_argument("--check-readback", metavar="PATH", help="the post-publication v0.3 readback JSON")
    parser.add_argument("--tag", help="release tag expected by --check-readback")
    parser.add_argument("--rev", help="read the record and every receipt with git show REV:<path>; no working tree, no gh")
    parser.add_argument("--repo", type=pathlib.Path, default=ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--self-test-readback", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            return self_test()
        if args.self_test_readback:
            return self_test_readback()
        if args.check:
            if args.check_readback:
                parser.error("choose only one of --check or --check-readback")
            print(check(args.check, args.repo.resolve(), args.rev))
            return 0
        if args.check_readback:
            if not args.tag:
                parser.error("--check-readback requires --tag")
            source = Source(args.repo.resolve(), args.rev)
            readback = parse_json(source.read(args.check_readback, "receipt-missing"), "v0.3 release readback", "receipt-invalid")
            print(check_readback_v2(source, readback, args.tag, args.repo.resolve(), args.rev))
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
