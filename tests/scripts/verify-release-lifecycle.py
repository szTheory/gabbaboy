#!/usr/bin/env python3
"""Replay the release evidence lifecycle against bounded, captured GitHub API shapes (RM-028, D-20).

    verify-release-lifecycle.py [--rev SHA] --replay
    verify-release-lifecycle.py [--rev SHA] --self-test
    verify-release-lifecycle.py [--rev SHA] --self-test-post-tag
    verify-release-lifecycle.py [--rev SHA] --self-test-post-tag-group {trust,capture_source,draft_assets,recovery_sums,consumer,publication}
    verify-release-lifecycle.py [--rev SHA] --self-test-post-tag-coverage
    verify-release-lifecycle.py [--rev SHA] --check-capture
    verify-release-lifecycle.py --sanitize-capture RAW_DIR OUTPUT

--rev is a resolved immutable 40-hex commit (CTest passes the configure-time HEAD; without it HEAD is resolved to a
commit id once). Every production file the replay uses is materialized from that commit with git show; the live working
tree is never read and never a fallback, so uncommitted edits are not what is judged.

The replay runs the production lifecycle script (.github/scripts/release-evidence-lifecycle.sh) and, through it, the
production gates, unchanged, from a non-git workspace for the attacher and from a tag checkout for the judge jobs, with
GH_REPO explicit. Only the transport is replaced:

  * a `gh` executable that serves response shapes derived from tests/data/release-api/captured.json and refuses every
    endpoint, flag, repository, mutation and oversized or reshaped response it was not told about; and
  * a download helper that serves the fixture source archive for the one expected URL.

The release workflow's one publish command is intercepted by that `gh` and recorded as a decision. The replay proves
deterministic logic. It does not prove live GitHub permissions, and nothing here reaches the network or a real tag,
release or asset.
"""
from __future__ import annotations

import argparse
import ast
import concurrent.futures
import copy
from collections.abc import Callable
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import itertools
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHA1 = re.compile(r"[0-9a-f]{40}")
SHA256 = re.compile(r"[0-9a-f]{64}")
REPO = "szTheory/gabbaboy"

LIFECYCLE = ".github/scripts/release-evidence-lifecycle.sh"
WORKFLOW = ".github/workflows/release.yml"
DELIVERY = "tests/scripts/verify-v02-delivery.py"
CAPTURE = "tests/data/release-api/captured.json"
RECOVERY_FIXTURE = "tests/data/release-api/v030-notes-failure.json"
SOURCES = "tests/data/release-api/SOURCES.md"
RECOVERY_ADOPTION = "tests/scripts/verify-v02-adoption.py"
RECOVERY_CLAIMS = "tests/scripts/verify-cgb-corpus-claims.py"
RECOVERY_RELEASE_DOC = "docs/release.md"
POST_TAG_COVERAGE = "tests/data/release-lifecycle-post-tag-coverage.json"
# Production files the replay materializes from --rev into the judge checkout (the `trusted/` tree of every job).
JUDGE_FILES = (
    LIFECYCLE,
    ".github/scripts/verify-release-gates.sh",
    ".github/scripts/verify-published-release-assets.py",
    ".github/scripts/verify-release-source-proof.py",
    ".github/scripts/download-release-artifact.py",
    "tests/scripts/verify-release-gates.py",
    "tests/scripts/verify-perf-gate.py",
)
# mode -> the release.yml job whose step must call it
MODES = {
    "attach-evidence": "attach-v02-evidence",
    "validate-evidence": "candidate-platform-manifest",
    "build-manifest": "candidate-platform-manifest",
    "validate-draft": "publish-qualified-release",
    "final-gate": "publish-qualified-release",
    "nightly-gate": "publish-qualified-release",
    "publish-draft": "publish-qualified-release",
}
NIGHTLY_RUN_ID = 40245698754
PERF_SOURCE_REV = "b93137f00d07b11dc74e40330e0ddf6029c0677d"
PERF_LIMITS_BASE_REV = "947d6a9d177af6c04a5f9ea6abcc2c470ab9be57"
LOAD_VERIFIERS_STEP = "Load trusted release evidence verifiers"
EVIDENCE_ATTACHED = ("support-ledger.json", "cgb-corpus-receipt.json", "v02-fuzz-receipt.json", "v02-performance-receipt.json")
FINAL_NAMES = ("SHA256SUMS", "release-receipt.json")
RELEASE_ID = 900000001
FIRST_ASSET_ID = 900100001
RUN_ID = 50000000001
MAX_CAPTURE_BYTES = 256 * 1024
MAX_RECOVERY_FIXTURE_BYTES = 256 * 1024
RESPONSE_KEYS = ("release", "release_assets", "workflow_runs", "workflow_run", "jobs", "artifacts", "check_runs",
                 "pull_request", "pull_requests", "attempt_jobs", "ci_run", "commit")
PARALLEL = max(2, min(8, os.cpu_count() or 2))


class Reject(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"REJECT {code}: {message}")
        self.code = code


@dataclass(frozen=True)
class ControlOutcome:
    control_id: str
    message: str


@dataclass(frozen=True)
class PostTagRegistration:
    group: str
    control_ids: tuple[str, ...]
    run: Callable[[Context], str | ControlOutcome | list[ControlOutcome]]


def _post_tag_case_id(prefix: str, label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", label.casefold()).strip("-")
    if not slug:
        raise Reject("post-tag-coverage", f"control label has no stable id characters: {label!r}")
    return f"{prefix}.{slug}"


# ----------------------------------------------------------------------------------------------- immutable source

def git_show(rev: str, path: str) -> bytes:
    done = subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:{path}"], capture_output=True, timeout=60)
    if done.returncode != 0:
        raise Reject("rev-file-missing", f"{path} is not present at {rev}")
    return done.stdout


def resolve_rev(rev: str) -> str:
    if not SHA1.fullmatch(rev):
        raise Reject("rev-malformed", "--rev must be a resolved 40-hex commit")
    done = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-t", rev], capture_output=True, text=True, timeout=60)
    if done.returncode != 0 or done.stdout.strip() != "commit":
        raise Reject("rev-unresolved", "--rev does not name a commit in this repository")
    return rev


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------------------------- shapes and capture
# Key-set comparison only: a served object must have exactly the keys the captured object has, recursively (the first
# element of a list stands for the list; an empty list matches any list). An invented member, such as a `repository`
# key on a check run, or a missing one, such as `check_suite`, is a different shape.
SHAPE_SRC = '''
def key_shape(value):
    if isinstance(value, dict):
        return {key: key_shape(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [key_shape(value[0])] if value else []
    return None


def same_shape(left, right):
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(same_shape(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return not left or not right or same_shape(left[0], right[0])
    return not isinstance(left, (dict, list)) and not isinstance(right, (dict, list))
'''
_shape_ns: dict = {}
exec(SHAPE_SRC, _shape_ns)  # noqa: S102 - fixed source shared verbatim with the transport stub
key_shape = _shape_ns["key_shape"]
same_shape = _shape_ns["same_shape"]

# Members the production consumers read. Their presence in the capture is part of the frozen contract; `repository`
# on a check run is forbidden because GitHub does not return one (the consumer derives it from url and html_url).
REQUIRED_PATHS = {
    "release": ("id", "tag_name", "draft", "assets.0.id", "assets.0.name", "assets.0.size", "assets.0.digest",
                "assets.0.state", "assets.0.browser_download_url", "assets.0.url"),
    "release_assets": ("0.id", "0.name", "0.size", "0.digest", "0.state", "0.url", "0.browser_download_url"),
    "workflow_runs": ("workflow_runs.0.id", "workflow_runs.0.run_attempt", "workflow_runs.0.status",
                      "workflow_runs.0.head_sha", "workflow_runs.0.path", "workflow_runs.0.event",
                      "workflow_runs.0.conclusion", "workflow_runs.0.check_suite_id"),
    "workflow_run": ("id", "run_attempt", "status", "conclusion", "head_sha", "path", "event", "check_suite_id"),
    "jobs": ("jobs.0.id", "jobs.0.run_id", "jobs.0.run_attempt", "jobs.0.head_sha", "jobs.0.status",
             "jobs.0.conclusion", "jobs.0.name", "jobs.0.check_run_url"),
    "artifacts": ("artifacts.0.id", "artifacts.0.name", "artifacts.0.size_in_bytes", "artifacts.0.expired",
                  "artifacts.0.digest", "artifacts.0.workflow_run.id", "artifacts.0.workflow_run.head_sha"),
    "check_runs": ("check_runs.0.id", "check_runs.0.name", "check_runs.0.head_sha", "check_runs.0.status",
                   "check_runs.0.conclusion", "check_runs.0.url", "check_runs.0.html_url",
                   "check_runs.0.check_suite.id", "check_runs.0.app.id", "check_runs.0.app.slug"),
    "pull_request": ("number", "state", "merged_at", "merge_commit_sha", "base.ref", "base.repo.full_name",
                     "head.sha", "head.repo.full_name"),
    "pull_requests": ("0.number", "0.merged_at", "0.merge_commit_sha", "0.base.ref", "0.head.sha"),
    "attempt_jobs": ("jobs.0.completed_at", "jobs.0.run_id", "jobs.0.run_attempt", "total_count"),
    "ci_run": ("id", "run_attempt", "head_sha", "path", "event", "status", "conclusion"),
    "commit": ("sha",),
}

# D-21 inventory. Forms use `{}` for a shell-expanded path segment, so different variable spellings for the same
# endpoint share one entry. `route` identifies the immutable replay transport branch; pinned forms name a rule in the
# trusted workflow policy checker. `ci_run` is captured ahead of its first consumer in 19-05.
POST_TAG_ENDPOINTS = (
    {"form": "gh api repos/{}/actions/runs/{}/attempts/{}/jobs?per_page=100",
     "sources": (LIFECYCLE, WORKFLOW), "consumer": "nightly-gate and candidate rehearsal binder",
     "coverage": "replayed:attempt_jobs", "route": "actions/runs/([0-9]+)/attempts/([0-9]+)/jobs"},
    {"form": "gh api repos/{}/actions/runs/{}/artifacts?per_page=100",
     "sources": (WORKFLOW,), "consumer": "rehearsal performance artifact selection",
     "coverage": "pinned:check_release"},
    {"form": "gh api repos/{}/actions/runs/{}",
     "sources": (SOURCES, WORKFLOW), "consumer": "19-05 exact-source CI performance receipt verifier input",
     "coverage": "replayed:ci_run", "route": "actions/runs/[0-9]+"},
    {"form": "gh api repos/{}/actions/workflows/ci.yml/runs?head_sha={}&event=push&branch=main&per_page=100",
     "sources": (WORKFLOW,), "consumer": "candidate fuzz receipt source-run lookup",
     "coverage": "pinned:check_release"},
    {"form": "gh api repos/{}/actions/workflows/release-rehearsal.yml/runs?branch=rehearsal/{}&status=success&per_page=100",
     "sources": (LIFECYCLE, WORKFLOW), "consumer": "newest exact-tag rehearsal selection",
     "coverage": "replayed:workflow_runs", "route": "actions/workflows/release-rehearsal.yml/runs"},
    {"form": "gh api repos/{}/actions/workflows/{}/runs?per_page=100",
     "sources": (".github/scripts/verify-release-gates.sh",), "consumer": "recovery run identity check",
     "coverage": "pinned:check_release_gate_wiring"},
    {"form": "gh api repos/{}/branches/main/protection",
     "sources": (".github/scripts/verify-release-gates.sh",), "consumer": "version PR required-check policy",
     "coverage": "pinned:check_release_gate_wiring"},
    {"form": "gh api repos/{}/commits/{}",
     "sources": (LIFECYCLE, ".github/scripts/verify-release-gates.sh", WORKFLOW),
     "consumer": "tag-to-source identity check", "coverage": "replayed:commit", "route": "commits/[^/]+"},
    {"form": "gh api repos/{}/commits/{}/check-runs?per_page=100",
     "sources": (".github/scripts/verify-release-gates.sh",), "consumer": "exact-head required-check evidence",
     "coverage": "replayed:check_runs", "route": "commits/[0-9a-f]{40}/check-runs"},
    {"form": "gh api repos/{}/commits/{}/pulls",
     "sources": (LIFECYCLE, WORKFLOW), "consumer": "merged version PR identity and merge time",
     "coverage": "replayed:pull_requests", "route": "commits/[0-9a-f]{40}/pulls"},
    {"form": "gh api repos/{}/contents/CMakeLists.txt?ref={}",
     "sources": (WORKFLOW,), "consumer": "tagged source version extraction", "coverage": "pinned:check_release"},
    {"form": "gh api repos/{}/pulls/{}",
     "sources": (".github/scripts/verify-release-gates.sh",), "consumer": "merged source PR proof",
     "coverage": "replayed:pull_request", "route": "pulls/\\d+"},
    {"form": "gh api repos/{}/releases/{}",
     "sources": (LIFECYCLE, ".github/scripts/verify-release-gates.sh", WORKFLOW),
     "consumer": "draft and published release state", "coverage": "replayed:release", "route": "releases/\\d+"},
    {"form": "gh api repos/{}/releases/{}/assets?per_page=100",
     "sources": (LIFECYCLE, ".github/scripts/verify-release-gates.sh", WORKFLOW),
     "consumer": "release asset inventory and digest readback", "coverage": "replayed:release_assets",
     "route": "releases/\\d+/assets"},
    {"form": "gh api repos/{}/releases?per_page=100",
     "sources": (LIFECYCLE, WORKFLOW), "consumer": "release lookup by tag", "coverage": "replayed:release",
     "route": "tail == \"releases\""},
    {"form": "gh pr checks",
     "sources": (WORKFLOW,), "consumer": "merged version PR required-check gate", "coverage": "pinned:check_release"},
    {"form": "gh release download",
     "sources": (LIFECYCLE, ".github/scripts/verify-release-gates.sh", WORKFLOW),
     "consumer": "readback of already-uploaded release bytes", "coverage": "replayed:release_assets",
     "route": '["release", "download"]'},
    {"form": "gh release edit",
     "sources": (LIFECYCLE, ".github/scripts/verify-release-gates.sh"), "consumer": "single intercepted publish decision", "coverage": "replayed:release",
     "route": '["release", "edit"]'},
    {"form": "gh release upload",
     "sources": (LIFECYCLE, ".github/scripts/verify-release-gates.sh", WORKFLOW),
     "consumer": "in-memory upload and retry lifecycle", "coverage": "replayed:release",
     "route": '["release", "upload"]'},
    {"form": "gh run download",
     "sources": (WORKFLOW,), "consumer": "candidate and rehearsal artifact download", "coverage": "pinned:check_release"},
    {"form": "gh run download {} --name perf-gate-{}-{}",
     "sources": (WORKFLOW,), "consumer": "same-run performance gate receipt download",
     "coverage": "pinned:perf_gate_artifact_name"},
    {"form": "gh run list",
     "sources": (LIFECYCLE, "tests/scripts/verify-release-gates.py"), "consumer": "newest nightly-asan run selection", "coverage": "replayed:workflow_runs",
     "route": "run command is allowed only as the two nightly gate reads"},
    {"form": "gh run view",
     "sources": (LIFECYCLE, "tests/scripts/verify-release-gates.py"), "consumer": "nightly-asan replay job result", "coverage": "replayed:workflow_runs",
     "route": "run command is allowed only as the two nightly gate reads"},
)
SELF = "tests/scripts/verify-release-lifecycle.py"
POLICY = ".github/scripts/verify-workflow-policy.py"
FORBIDDEN_MEMBERS = {"check_runs": ("check_runs.0.repository",)}
EMAIL = re.compile(r"[A-Za-z0-9._%+\[\]-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
REDACTED_EMAIL = "redacted@example.invalid"
FORBIDDEN_TEXT = re.compile(r"/Users/|/home/|[A-Za-z]:\\\\Users|\bgh[pousr]_[A-Za-z0-9]{20,}|github_pat_|BEGIN [A-Z ]*PRIVATE KEY")
KEEP_LOGINS = {"szTheory", "github"}
USER_KEYS = {"login", "node_id", "avatar_url"}
TRUNCATE_ARRAYS = {"assets": 2, "workflow_runs": 2, "jobs": 8, "artifacts": 2, "files": 1, "steps": 2}
OMITTED = "[omitted by the capture sanitizer]"
SOURCES_DIGEST = re.compile(r"(?m)^- captured\.json sha256: ([0-9a-f]{64})$")
RECOVERY_SOURCES_DIGEST = re.compile(r"(?m)^- `v030-notes-failure\.json` sha256: ([0-9a-f]{64})$")
RECOVERY_SOURCES_SIZE = re.compile(r"(?m)^- bytes: ([0-9]+) \(bound: ([0-9]+)\)$")
RECOVERY_SOURCES_SECTION = re.compile(
    r"(?ms)^## v0\.3\.0 first post-tag failure \(additive fixture\)\n(.*?)(?=^## |\Z)"
)
RECOVERY_TAG = "v0.3.0"
RECOVERY_SOURCE_SHA = "a3f3390451f9a893aa47475f15a722ada86daaa6"
RECOVERY_RELEASE_ID = 429606490
RECOVERY_RUN_ID = 41148606886
RECOVERY_JOB_ID = 124379552103
RECOVERY_RELATIVE_LINK = b"[support ledger](docs/support/v0.3.0.md)"
RECOVERY_PINNED_LINK = (
    b"[support ledger](https://github.com/szTheory/gabbaboy/blob/v0.3.0/docs/support/v0.3.0.md)"
)
RECOVERY_DISPATCH = {
    "workflow": "release-please.yml",
    "ref": "main",
    "inputs": {"retry": True, "tag_name": RECOVERY_TAG, "source_sha": RECOVERY_SOURCE_SHA,
               "release_id": str(RECOVERY_RELEASE_ID)},
}


def dig(value, path: str):
    for part in path.split("."):
        if isinstance(value, list):
            if not part.isdigit() or int(part) >= len(value):
                return None, False
            value = value[int(part)]
        elif isinstance(value, dict):
            if part not in value:
                return None, False
            value = value[part]
        else:
            return None, False
    return value, True


def sanitize(value, key: str = "", log: dict | None = None):
    """Apply the documented capture transform; every rule is data-independent and tested by --self-test."""
    log = {} if log is None else log
    if isinstance(value, dict):
        if USER_KEYS <= value.keys():
            login = str(value.get("login", ""))
            if login in KEEP_LOGINS or login.endswith("[bot]"):
                return {k: sanitize(v, k, log) for k, v in value.items()}
            blank = {k: v for k, v in value.items()}
            for k, v in list(blank.items()):
                if isinstance(v, str) and login and login in v:
                    blank[k] = v.replace(login, "sanitized-user")
            # same members as the original, never more or fewer: only values that exist are replaced
            for member, replacement in (("login", "sanitized-user"), ("id", 1), ("node_id", "U_sanitized"), ("gravatar_id", ""),
                                        ("avatar_url", "https://avatars.githubusercontent.com/u/1?v=4"), ("site_admin", False)):
                if member in blank:
                    blank[member] = replacement
            log["users"] = log.get("users", 0) + 1
            return blank
        out = {}
        for k, v in value.items():
            if k == "body" and isinstance(v, str):
                out[k] = OMITTED
            elif k in ("patch", "signature", "payload") and isinstance(v, str):
                out[k] = OMITTED
            elif k in ("runner_name", "runner_group_name") and isinstance(v, str):
                out[k] = "GitHub Actions"
            elif k == "runner_id" and isinstance(v, int):
                out[k] = 0
            elif k == "name" and isinstance(v, str) and "email" in value and "date" in value:
                out[k] = "Sanitized Author"
            elif isinstance(v, list) and k in TRUNCATE_ARRAYS and len(v) > TRUNCATE_ARRAYS[k]:
                log.setdefault("truncated", {})[k] = [TRUNCATE_ARRAYS[k], len(v)]
                out[k] = [sanitize(item, k, log) for item in v[:TRUNCATE_ARRAYS[k]]]
            else:
                out[k] = sanitize(v, k, log)
        return out
    if isinstance(value, list):
        return [sanitize(item, key, log) for item in value]
    if isinstance(value, str):
        text = EMAIL.sub(REDACTED_EMAIL, value)
        if key in ("message", "display_title", "title", "description") and len(text) > 200:
            text = text[:200] + "...[truncated]"
        return text
    return value


def assemble_capture(raw: dict[str, object]) -> dict:
    """Select the bounded responses and sanitize them. `raw` holds the parsed gh api responses by capture name."""
    log: dict = {}
    names = {"required-native", "fixture-repro", "preview-package-smoke"}
    checks = copy.deepcopy(raw["check_runs"])
    picked, seen = [], set()
    for run in checks["check_runs"]:
        if run["name"] in names and run["name"] not in seen:
            picked.append(run)
            seen.add(run["name"])
    if seen != names:
        raise Reject("capture-incomplete", "the raw check-run response lacks one of the three required contexts")
    extra = next((run for run in checks["check_runs"] if run["name"] not in names), None)
    if extra is not None:
        picked.append(extra)
    log.setdefault("truncated", {})["check_runs"] = [len(picked), len(checks["check_runs"])]
    checks["check_runs"] = picked
    release = copy.deepcopy(raw["release"])
    assets = copy.deepcopy(raw["release_assets"])
    log["truncated"]["release_assets"] = [min(2, len(assets)), len(assets)]
    responses = {
        "release": release, "release_assets": assets[:2], "workflow_runs": raw["workflow_runs"],
        "workflow_run": raw["workflow_run"], "jobs": raw["jobs"], "artifacts": raw["artifacts"],
        "check_runs": checks, "pull_request": raw["pull_request"], "pull_requests": raw["pull_requests"],
        "attempt_jobs": raw["attempt_jobs"], "ci_run": raw["ci_run"], "commit": raw["commit"],
    }
    responses = {name: sanitize(value, "", log) for name, value in responses.items()}
    return {"schema_version": 1, "kind": "github-api-capture", "api_version": "2022-11-28", "repository": REPO,
            "identity": raw["identity"], "sanitizer": {"truncated": log.get("truncated", {}), "users_replaced": log.get("users", 0)},
            "responses": responses}


def capture_text(capture: dict) -> str:
    return json.dumps(capture, indent=2, sort_keys=True) + "\n"


def v030_changelog_section(changelog: bytes) -> bytes:
    """Return the exact v0.3.0 heading and section bytes, including original LF endings."""
    lines = changelog.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines)
              if re.match(br"^## \[0\.3\.0\](?:\(|\s|$)", line)]
    if len(starts) != 1:
        raise Reject("recovery-source-section", "tagged CHANGELOG must contain exactly one v0.3.0 section")
    start = starts[0]
    end = next((index for index in range(start + 1, len(lines)) if lines[index].startswith(b"## ")), len(lines))
    return b"".join(lines[start:end])


def recovery_document_markers(repair_spec: dict) -> tuple[tuple[str, bytes], ...]:
    return (
        ("corrective main PR", b"non-releasable corrective main pull request"),
        ("offline full replay", b"full offline release-lifecycle replay"),
        ("immutable source identity", repair_spec["source_sha"].encode("ascii")),
        ("original tagged-section digest", repair_spec["original_section_sha256"].encode("ascii")),
        ("repaired tagged-section digest", repair_spec["repaired_body_sha256"].encode("ascii")),
        ("body-only PATCH", b"PATCH request contains only"),
        ("explicit retry mode", b"retry=true"),
        ("truthful workflow head", b"heads as G"),
        ("product source binding", b"pre-publish inventory bound to S"),
        ("attempt is not retry mode", b"Do not infer retry mode from `run_attempt`"),
        ("release API reference", b"https://docs.github.com/en/rest/releases/releases#update-a-release"),
        ("dispatch API reference", b"https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event"),
        ("second failure hold", b"If the retry fails again or any precondition has"),
    )


def recovery_document_section(raw: bytes, repair_spec: dict) -> bytes:
    heading = b"## Recovering lost v0.3.0 draft notes\n"
    if b"\r" in raw or raw.count(heading) != 1:
        raise Reject("recovery-document", "release documentation must have one LF-terminated recovery procedure")
    start = raw.index(heading) + len(heading)
    next_heading = re.search(rb"(?m)^## ", raw[start:])
    section = raw[start:start + next_heading.start()] if next_heading else raw[start:]
    spec_markers = recovery_document_markers(repair_spec)
    missing = [name for name, marker in spec_markers if marker not in section]
    if missing:
        raise Reject("recovery-document", f"release recovery procedure omits safeguards: {', '.join(missing)}")
    return section


def repair_support_ledger_link(section: bytes, relative_link: bytes, pinned_link: bytes) -> bytes:
    """Apply the one allowlisted URL replacement, accepting the identical repair as a no-op."""
    if relative_link != RECOVERY_RELATIVE_LINK or pinned_link != RECOVERY_PINNED_LINK:
        raise Reject("recovery-link-target", "the only allowed repair is the v0.3.0 support-ledger link")
    relative_count = section.count(RECOVERY_RELATIVE_LINK)
    pinned_count = section.count(RECOVERY_PINNED_LINK)
    link_count = section.count(b"[support ledger](")
    if relative_count == 0 and pinned_count == 1 and link_count == 1:
        return section
    if relative_count != 1:
        raise Reject("recovery-link-count", "the tagged section must contain one relative support-ledger link")
    if pinned_count != 0 or link_count != 1:
        raise Reject("recovery-link-duplicate", "the tagged section contains an unexpected or duplicate support link")
    return section.replace(RECOVERY_RELATIVE_LINK, RECOVERY_PINNED_LINK, 1)


def _strict_recovery_json(raw: bytes, label: str) -> object:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON member {key!r}")
            result[key] = value
        return result

    try:
        return json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=unique)
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise Reject("recovery-json", f"{label} is not unambiguous UTF-8 JSON: {error}") from error


def _recovery_privacy(raw: bytes) -> None:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError as error:
        raise Reject("recovery-sanitize", "recovery fixture is not valid UTF-8") from error
    if FORBIDDEN_TEXT.search(text):
        raise Reject("recovery-sanitize", "recovery fixture contains a local path or credential marker")
    if any(email != REDACTED_EMAIL for email in EMAIL.findall(text)):
        raise Reject("recovery-sanitize", "recovery fixture contains an unredacted email address")


def _require_recovery_keys(value: object, keys: set[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise Reject("recovery-schema", f"{label} members differ from the exact recovery schema")
    return value


def validate_recovery_fixture(raw: bytes, sources: bytes, *, verify_digest: bool = True) -> dict:
    if len(raw) > MAX_RECOVERY_FIXTURE_BYTES:
        raise Reject("recovery-bound", f"recovery fixture exceeds {MAX_RECOVERY_FIXTURE_BYTES} bytes")
    if b"\r" in raw or not raw.endswith(b"\n"):
        raise Reject("recovery-eol", "recovery fixture must be LF-terminated UTF-8 JSON")
    _recovery_privacy(raw)
    sources_text = sources.decode("utf-8", errors="strict")
    sections = RECOVERY_SOURCES_SECTION.findall(sources_text)
    size_rows = RECOVERY_SOURCES_SIZE.findall(sections[0]) if len(sections) == 1 else []
    if (len(size_rows) != 1 or int(size_rows[0][0]) != len(raw)
            or int(size_rows[0][1]) != MAX_RECOVERY_FIXTURE_BYTES):
        raise Reject("recovery-size", "SOURCES.md recovery fixture byte count or bound differs from the captured bytes")
    recorded = RECOVERY_SOURCES_DIGEST.findall(sections[0])
    if verify_digest and (len(recorded) != 1 or recorded[0] != sha256_bytes(raw)):
        raise Reject("recovery-digest", "SOURCES.md does not pin exactly the recovery fixture SHA-256")
    fixture = _strict_recovery_json(raw, "recovery fixture")
    fixture = _require_recovery_keys(fixture, {
        "schema_version", "kind", "repository", "api_version", "failure_snapshot", "releases_list_capture",
        "failed_notes", "reviewed_body", "tagged_repair",
    }, "recovery fixture")
    if (fixture.get("schema_version") != 1 or fixture.get("kind") != "v030-post-tag-notes-failure"
            or fixture.get("repository") != REPO or fixture.get("api_version") != "2022-11-28"):
        raise Reject("recovery-schema", "recovery fixture header differs from the v0.3.0 capture")

    snapshot = _require_recovery_keys(fixture["failure_snapshot"], {
        "tag", "source_sha", "release_id", "workflow_run_id", "workflow_run_attempt", "candidate_job_id",
        "workflow_path", "event", "head_branch", "head_sha", "status", "conclusion",
        "failed_step", "adoption_reason", "draft_detail", "draft_detail_capture_file_sha256", "draft_assets",
        "draft_assets_capture_file_sha256", "workflow_run", "workflow_run_capture_file_sha256", "candidate_job",
        "candidate_job_capture_file_sha256", "capture_sanitizer",
    }, "failure_snapshot")
    if (snapshot["tag"], snapshot["source_sha"], snapshot["release_id"], snapshot["workflow_run_id"],
            snapshot["workflow_run_attempt"], snapshot["candidate_job_id"], snapshot["workflow_path"],
            snapshot["event"], snapshot["head_branch"], snapshot["head_sha"],
            snapshot["status"], snapshot["conclusion"], snapshot["adoption_reason"]) != (
            RECOVERY_TAG, RECOVERY_SOURCE_SHA, RECOVERY_RELEASE_ID, RECOVERY_RUN_ID, 1, RECOVERY_JOB_ID,
            ".github/workflows/release-please.yml", "push", "main", RECOVERY_SOURCE_SHA,
            "completed", "failure", "release-notes-absence-missing"):
        raise Reject("recovery-identity", "the captured first-failure run, job, release, tag or source identity changed")
    hashes = ("draft_detail_capture_file_sha256", "draft_assets_capture_file_sha256",
              "workflow_run_capture_file_sha256", "candidate_job_capture_file_sha256")
    if any(not isinstance(snapshot[key], str) or not re.fullmatch(r"[0-9a-f]{64}", snapshot[key]) for key in hashes):
        raise Reject("recovery-provenance", "first-failure API capture digests are malformed")
    failed_step = _require_recovery_keys(snapshot["failed_step"], {"name", "number", "status", "conclusion"}, "failed_step")
    if (failed_step["name"] != "Require final release notes to satisfy the v0.2 adoption contract"
            or type(failed_step["number"]) is not int or failed_step["number"] != 6
            or failed_step["status"] != "completed" or failed_step["conclusion"] != "failure"):
        raise Reject("recovery-failure", "the actual candidate adoption step identity or result changed")

    draft = snapshot["draft_detail"]
    if not isinstance(draft, dict) or (draft.get("id"), draft.get("tag_name"), draft.get("target_commitish"),
            draft.get("draft"), draft.get("prerelease"), draft.get("published_at"), draft.get("body"), draft.get("assets")) != (
            RECOVERY_RELEASE_ID, RECOVERY_TAG, RECOVERY_SOURCE_SHA, True, False, None, OMITTED, []):
        raise Reject("recovery-draft", "captured draft detail is not the original unpublished empty-asset draft")
    if snapshot["draft_assets"] != []:
        raise Reject("recovery-assets", "the captured first-failure draft must have no assets")
    run = snapshot["workflow_run"]
    if not isinstance(run, dict) or any(run.get(key) != value for key, value in {
            "id": RECOVERY_RUN_ID, "run_attempt": 1, "path": ".github/workflows/release-please.yml",
            "event": "push", "head_branch": "main", "head_sha": RECOVERY_SOURCE_SHA,
            "status": "completed", "conclusion": "failure"}.items()):
        raise Reject("recovery-run", "captured release-please workflow run identity or failure changed")
    job = snapshot["candidate_job"]
    if not isinstance(job, dict) or any(job.get(key) != value for key, value in {
            "id": RECOVERY_JOB_ID, "run_id": RECOVERY_RUN_ID, "run_attempt": 1,
            "name": "release-candidate / downloaded-linux-x64-candidate", "head_sha": RECOVERY_SOURCE_SHA,
            "status": "completed", "conclusion": "failure"}.items()):
        raise Reject("recovery-job", "captured Linux candidate job identity or failure changed")
    if job.get("head_branch") != "main" or "body" in job or "runner_id" not in job:
        raise Reject("recovery-sanitize", "candidate job capture does not preserve or sanitize its API shape")

    list_capture = _require_recovery_keys(fixture["releases_list_capture"], {
        "endpoint", "captured_at", "capture_kind", "raw_response_sha256", "entry_count", "response", "sanitizer",
    }, "releases_list_capture")
    if (list_capture["endpoint"] != "repos/szTheory/gabbaboy/releases?per_page=100"
            or list_capture["captured_at"] != "2026-10-31T00:48:23Z"
            or list_capture["capture_kind"] != "bounded read-only GET after the failed run; not the failure-snapshot timestamp"
            or type(list_capture["entry_count"]) is not int or not isinstance(list_capture["response"], list)
            or len(list_capture["response"]) != list_capture["entry_count"]
            or not isinstance(list_capture["raw_response_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", list_capture["raw_response_sha256"])):
        raise Reject("recovery-list", "bounded release-list response provenance or shape is malformed")
    targets = [row for row in list_capture["response"] if isinstance(row, dict) and row.get("id") == RECOVERY_RELEASE_ID]
    if len(targets) != 1 or not same_shape(targets[0], draft):
        raise Reject("recovery-list", "release-list capture does not contain one same-shaped target draft")
    if any(targets[0].get(key) != draft.get(key) for key in ("id", "tag_name", "target_commitish", "draft", "prerelease", "published_at", "assets")):
        raise Reject("recovery-list", "release-list capture target identity differs from the failure snapshot")
    if "body" in targets[0] and targets[0]["body"] != OMITTED:
        raise Reject("recovery-sanitize", "release-list target body was not removed by the capture sanitizer")

    notes = _require_recovery_keys(fixture["failed_notes"], {
        "text", "utf8_sha256", "response_body_sha256", "response_body_digest_kind", "release_detail_capture_file_sha256",
    }, "failed_notes")
    if (not isinstance(notes["text"], str) or not notes["text"] or
            hashlib.sha256(notes["text"].encode("utf-8")).hexdigest() != notes["utf8_sha256"]
            or notes["response_body_sha256"] != notes["utf8_sha256"]
            or notes["response_body_digest_kind"] != "SHA-256 of the decoded GitHub release body encoded as UTF-8"
            or notes["release_detail_capture_file_sha256"] != snapshot["draft_detail_capture_file_sha256"]):
        raise Reject("recovery-notes", "separately retained failed notes and response provenance are inconsistent")
    reviewed = _require_recovery_keys(fixture["reviewed_body"], {"text", "utf8_sha256", "pinned_support_link_occurrences"},
                                      "reviewed_body")
    if (not isinstance(reviewed["text"], str)
            or hashlib.sha256(reviewed["text"].encode("utf-8")).hexdigest() != reviewed["utf8_sha256"]
            or reviewed["pinned_support_link_occurrences"] != 1
            or reviewed["text"].encode("utf-8").count(RECOVERY_PINNED_LINK) != 1):
        raise Reject("recovery-reviewed-body", "frozen reviewed body does not bind the exact pinned ledger URL once")
    repair = _require_recovery_keys(fixture["tagged_repair"], {
        "tag", "source_sha", "section_heading", "support_ledger_path", "relative_link", "tag_pinned_link",
        "original_section_sha256", "repaired_body_sha256", "transformation",
    }, "tagged_repair")
    if (repair["tag"], repair["source_sha"], repair["section_heading"], repair["support_ledger_path"],
            repair["relative_link"], repair["tag_pinned_link"]) != (
            RECOVERY_TAG, RECOVERY_SOURCE_SHA, "## [0.3.0]", "docs/support/v0.3.0.md",
            RECOVERY_RELATIVE_LINK.decode(), RECOVERY_PINNED_LINK.decode()):
        raise Reject("recovery-repair", "repair fixture permits a different tag, source, path or link transformation")
    if any(not isinstance(repair[key], str) or not re.fullmatch(r"[0-9a-f]{64}", repair[key])
           for key in ("original_section_sha256", "repaired_body_sha256")):
        raise Reject("recovery-repair", "tagged source and repaired body SHA-256 values are malformed")
    if repair["transformation"] != (
            "replace exactly one relative support-ledger link with the v0.3.0 tag-pinned GitHub blob link; "
            "preserve all other UTF-8 bytes"):
        raise Reject("recovery-repair", "repair transformation description changed")
    return fixture


def _recovery_tag_source(tag: str, expected_source: str) -> tuple[str, bytes, bytes]:
    if tag != RECOVERY_TAG or expected_source != RECOVERY_SOURCE_SHA:
        raise Reject("recovery-tag", "recovery must remain bound to v0.3.0 at immutable source S")
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"],
                            capture_output=True, text=True, timeout=60)
    if commit.returncode != 0 or commit.stdout.strip() != expected_source:
        raise Reject("recovery-tag", "local v0.3.0 tag no longer resolves to the captured source S")
    blob = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", f"{tag}:docs/support/v0.3.0.md"],
                          capture_output=True, text=True, timeout=60)
    if blob.returncode != 0 or subprocess.run(["git", "-C", str(ROOT), "cat-file", "-t", blob.stdout.strip()],
                                              capture_output=True, text=True, timeout=60).stdout.strip() != "blob":
        raise Reject("recovery-ledger", "tagged support-ledger blob is missing")
    changelog = git_show(expected_source, "CHANGELOG.md")
    ledger = git_show(expected_source, "docs/support/v0.3.0.md")
    return commit.stdout.strip(), changelog, ledger


def _recovery_v030_root(source: str, temporary: Path) -> Path:
    root = temporary / "v030-source-root"
    for relative in ("CMakeLists.txt", ".release-please-manifest.json", "tests/baseline/perf-attribution-v1.json"):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git_show(source, relative))
    tree = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", source, "docs/support"],
                          capture_output=True, text=True, timeout=60)
    if tree.returncode != 0:
        raise Reject("recovery-source-root", "cannot enumerate the immutable support-ledger paths")
    ledgers = [path for path in tree.stdout.splitlines() if path.startswith("docs/support/") and path.endswith(".md")]
    if "docs/support/v0.3.0.md" not in ledgers:
        raise Reject("recovery-source-root", "immutable source root lacks the v0.3.0 support ledger")
    for relative in ledgers:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git_show(source, relative))
    return root


def _run_adoption(notes: bytes, label: str, source: str, root: Path) -> tuple[int, str]:
    note_path = root.parent / f"{label}.md"
    note_path.write_bytes(notes)
    result = subprocess.run([sys.executable, "-I", str(ROOT / RECOVERY_ADOPTION), "--release-notes", str(note_path),
                             "--root", str(root), "--repo", str(ROOT), "--rev", source],
                            cwd=ROOT, capture_output=True, text=True, timeout=30)
    return result.returncode, result.stdout + result.stderr


def _expect_adoption_pass(notes: bytes, label: str, source: str, root: Path) -> int:
    code, output = _run_adoption(notes, label, source, root)
    if code != 0:
        raise Reject("recovery-adoption", f"production adoption checker refused {label}: {output[:240]}")
    try:
        summary = json.loads(output)
    except json.JSONDecodeError as error:
        raise Reject("recovery-adoption", f"production adoption checker output for {label} is not JSON") from error
    if summary.get("mode") != "release-notes" or summary.get("target") != "0.3.0" \
            or summary.get("positive_success") is not True or summary.get("checks") != 22:
        raise Reject("recovery-adoption", f"production adoption checker positive for {label} is incomplete")
    return summary["checks"]


def _expect_adoption_failure(notes: bytes, expected_reason: str, source: str, root: Path) -> int:
    code, output = _run_adoption(notes, "captured-failed-notes", source, root)
    if code != 1 or f"verify-v02-adoption fail: {expected_reason}" not in output:
        raise Reject("recovery-adoption", f"captured failed notes did not refuse for {expected_reason}: {output[:240]}")
    return 1


def _check_repaired_digest(body: bytes, expected: str) -> None:
    if hashlib.sha256(body).hexdigest() != expected:
        raise Reject("recovery-repaired-digest", "transformed release body differs from the bound SHA-256")


class RecoveryTransport:
    """A refusing in-memory model of the one body-only PATCH and one exact main retry dispatch."""

    def __init__(self, snapshot: dict, failed_body: bytes, repaired_body: bytes, repaired_sha: str):
        self.release_id = snapshot["release_id"]
        self.tag = snapshot["tag"]
        self.source_sha = snapshot["source_sha"]
        self.draft = True
        self.prerelease = False
        self.published_at = None
        self.assets = []
        self.body = failed_body
        self.failed_sha = hashlib.sha256(failed_body).hexdigest()
        self.repaired_body = repaired_body
        self.repaired_sha = repaired_sha
        self.patch_count = 0
        self.dispatch_count = 0

    def patch(self, release_id: int, payload: dict) -> str:
        if release_id != RECOVERY_RELEASE_ID or release_id != self.release_id:
            raise Reject("recovery-release-id", "metadata repair targets only the captured draft ID")
        if not isinstance(payload, dict) or set(payload) != {"body"} or not isinstance(payload.get("body"), str):
            raise Reject("recovery-patch-shape", "metadata repair request may contain only a UTF-8 body")
        if (self.tag != RECOVERY_TAG or self.source_sha != RECOVERY_SOURCE_SHA or not self.draft
                or self.prerelease or self.published_at is not None or self.assets != []):
            raise Reject("recovery-publication-race", "draft/tag/source/assets changed before metadata repair")
        requested = payload["body"].encode("utf-8")
        if requested != self.repaired_body or hashlib.sha256(requested).hexdigest() != self.repaired_sha:
            raise Reject("recovery-repaired-digest", "metadata repair body differs from the exact qualified bytes")
        current_sha = hashlib.sha256(self.body).hexdigest()
        if self.body == requested:
            return "no-op"
        if current_sha != self.failed_sha:
            raise Reject("recovery-publication-race", "draft body changed from the captured failure before repair")
        self.body = requested
        self.patch_count += 1
        return "patched"

    def dispatch(self, request: dict) -> str:
        if (self.release_id != RECOVERY_RELEASE_ID or self.tag != RECOVERY_TAG
                or self.source_sha != RECOVERY_SOURCE_SHA or self.draft is not True
                or self.prerelease is not False or self.published_at is not None or self.assets != []
                or self.body != self.repaired_body):
            raise Reject("recovery-dispatch-state", "retry dispatch requires the same unpublished repaired draft at S")
        if self.dispatch_count:
            raise Reject("recovery-dispatch-duplicate", "only one explicit retry dispatch is allowed")
        if not isinstance(request, dict) or set(request) != {"workflow", "ref", "inputs"}:
            raise Reject("recovery-dispatch-shape", "retry request must be the exact workflow/ref/inputs projection")
        inputs = request.get("inputs")
        if not isinstance(inputs, dict) or set(inputs) != {"retry", "tag_name", "source_sha", "release_id"} \
                or type(inputs.get("retry")) is not bool:
            raise Reject("recovery-dispatch-shape", "retry request inputs are incomplete or incorrectly typed")
        if request != RECOVERY_DISPATCH:
            raise Reject("recovery-dispatch-identity", "retry request differs from the exact mainG/tagS release inputs")
        self.dispatch_count += 1
        return "dispatched"


def _recovery_expect_reject(label: str, code: str, action: Callable[[], object]) -> int:
    try:
        action()
    except Reject as error:
        if error.code != code:
            raise Reject("recovery-control", f"{label} refused as {error.code}, expected {code}") from error
        return 1
    raise Reject("recovery-control", f"negative control accepted: {label}")


def self_test_post_tag_recovery(rev: str) -> tuple[int, int, str, str]:
    fixture_raw = git_show(rev, RECOVERY_FIXTURE)
    sources = git_show(rev, SOURCES)
    release_doc = git_show(rev, RECOVERY_RELEASE_DOC)
    adoption_source = git_show(rev, RECOVERY_ADOPTION)
    claims_source = git_show(rev, RECOVERY_CLAIMS)
    if b"\r" in release_doc or not release_doc:
        raise Reject("recovery-document", "release documentation must be readable immutable UTF-8 with LF endings")
    if adoption_source != git_show(RECOVERY_SOURCE_SHA, RECOVERY_ADOPTION) \
            or (ROOT / RECOVERY_ADOPTION).read_bytes() != adoption_source:
        raise Reject("recovery-adoption-source", "the production adoption checker differs from immutable tagged S")
    if claims_source != git_show(RECOVERY_SOURCE_SHA, RECOVERY_CLAIMS) \
            or (ROOT / RECOVERY_CLAIMS).read_bytes() != claims_source:
        raise Reject("recovery-adoption-source", "the production claim rules differ from immutable tagged S")
    fixture = validate_recovery_fixture(fixture_raw, sources)
    snapshot = fixture["failure_snapshot"]
    repair_spec = fixture["tagged_repair"]
    recovery_doc = recovery_document_section(release_doc, repair_spec)
    document_controls = 0
    for label, marker in recovery_document_markers(repair_spec):
        if recovery_doc.count(marker) != 1:
            raise Reject("recovery-document", f"procedure safeguard marker is not unique: {label}")
        omitted = release_doc.replace(marker, b"", 1)
        document_controls += _recovery_expect_reject(f"omitted procedure safeguard: {label}", "recovery-document",
            lambda omitted=omitted: recovery_document_section(omitted, repair_spec))
    tag_commit, changelog, ledger = _recovery_tag_source(repair_spec["tag"], repair_spec["source_sha"])
    if tag_commit != RECOVERY_SOURCE_SHA or not ledger:
        raise Reject("recovery-ledger", "tagged source or support ledger bytes are unavailable")
    section = v030_changelog_section(changelog)
    if b"\r" in section or not section.endswith(b"\n"):
        raise Reject("recovery-source-section", "tagged v0.3.0 section must preserve LF-terminated UTF-8 bytes")
    original_hash = sha256_bytes(section)
    if original_hash != repair_spec["original_section_sha256"]:
        raise Reject("recovery-source-digest", "tagged CHANGELOG section differs from the recorded source SHA-256")
    if section.count(RECOVERY_RELATIVE_LINK) != 1 or section.count(RECOVERY_PINNED_LINK) != 0:
        raise Reject("recovery-link-count", "tagged source section does not have exactly one allowed relative ledger link")
    repaired = repair_support_ledger_link(section, RECOVERY_RELATIVE_LINK, RECOVERY_PINNED_LINK)
    repaired_hash = sha256_bytes(repaired)
    _check_repaired_digest(repaired, repair_spec["repaired_body_sha256"])
    if repaired != section.replace(RECOVERY_RELATIVE_LINK, RECOVERY_PINNED_LINK, 1):
        raise Reject("recovery-byte-integrity", "repair changed bytes beyond the one approved URL replacement")
    if repair_support_ledger_link(repaired, RECOVERY_RELATIVE_LINK, RECOVERY_PINNED_LINK) != repaired:
        raise Reject("recovery-idempotency", "repeating the exact repair changed the body")

    with tempfile.TemporaryDirectory(prefix="gb-post-tag-recovery.") as temporary:
        temp = Path(temporary)
        v030_root = _recovery_v030_root(RECOVERY_SOURCE_SHA, temp)
        adoption_checks = 0
        adoption_checks += _expect_adoption_failure(fixture["failed_notes"]["text"].encode("utf-8"),
                                                    "release-notes-absence-missing", RECOVERY_SOURCE_SHA, v030_root)
        adoption_checks += _expect_adoption_pass(section, "tagged-original-section", RECOVERY_SOURCE_SHA, v030_root)
        adoption_checks += _expect_adoption_pass(repaired, "tagged-repaired-section", RECOVERY_SOURCE_SHA, v030_root)
        positives = 3

        controls = document_controls
        controls += _recovery_expect_reject("missing relative ledger link", "recovery-link-count",
            lambda: repair_support_ledger_link(section.replace(RECOVERY_RELATIVE_LINK, b""),
                                              RECOVERY_RELATIVE_LINK, RECOVERY_PINNED_LINK))
        controls += _recovery_expect_reject("duplicate relative ledger link", "recovery-link-count",
            lambda: repair_support_ledger_link(section + b"\n" + RECOVERY_RELATIVE_LINK,
                                              RECOVERY_RELATIVE_LINK, RECOVERY_PINNED_LINK))
        controls += _recovery_expect_reject("main-branch link target", "recovery-link-target",
            lambda: repair_support_ledger_link(section, RECOVERY_RELATIVE_LINK,
                                              b"[support ledger](https://github.com/szTheory/gabbaboy/blob/main/docs/support/v0.3.0.md)"))
        controls += _recovery_expect_reject("wrong-tag link target", "recovery-link-count",
            lambda: repair_support_ledger_link(section.replace(RECOVERY_RELATIVE_LINK,
                b"[support ledger](https://github.com/szTheory/gabbaboy/blob/v0.2.1/docs/support/v0.3.0.md)"),
                RECOVERY_RELATIVE_LINK, RECOVERY_PINNED_LINK))
        controls += _recovery_expect_reject("wrong ledger path", "recovery-link-target",
            lambda: repair_support_ledger_link(section, b"[support ledger](docs/support/unreleased.md)", RECOVERY_PINNED_LINK))
        controls += _recovery_expect_reject("mixed second replacement", "recovery-link-duplicate",
            lambda: repair_support_ledger_link(section + RECOVERY_PINNED_LINK, RECOVERY_RELATIVE_LINK, RECOVERY_PINNED_LINK))
        controls += _recovery_expect_reject("tampered repaired byte", "recovery-repaired-digest",
            lambda: _check_repaired_digest(repaired + b" ", repair_spec["repaired_body_sha256"]))
        controls += _recovery_expect_reject("duplicate fixture JSON key", "recovery-json",
            lambda: _strict_recovery_json(b'{"schema_version":1,"schema_version":1}', "control fixture"))
        controls += _recovery_expect_reject("fixture digest drift", "recovery-digest",
            lambda: validate_recovery_fixture(fixture_raw,
                sources.replace(sha256_bytes(fixture_raw).encode("ascii"), b"0" * 64, 1)))
        size_line = f"- bytes: {len(fixture_raw)} (bound: {MAX_RECOVERY_FIXTURE_BYTES})".encode("ascii")
        wrong_size_line = f"- bytes: {len(fixture_raw) + 1} (bound: {MAX_RECOVERY_FIXTURE_BYTES})".encode("ascii")
        controls += _recovery_expect_reject("fixture byte-count drift", "recovery-size",
            lambda: validate_recovery_fixture(fixture_raw, sources.replace(size_line, wrong_size_line, 1)))
        privacy_doc = json.loads(json.dumps(fixture))
        privacy_doc["reviewed_body"]["text"] += " /Users/private"
        controls += _recovery_expect_reject("local path leak", "recovery-sanitize",
            lambda: _recovery_privacy(json.dumps(privacy_doc).encode("utf-8")))

        def validate_mutated_fixture(value: dict) -> dict:
            raw = (json.dumps(value, sort_keys=True) + "\n").encode("utf-8")
            sources_text = sources.decode("utf-8", errors="strict")
            section_match = RECOVERY_SOURCES_SECTION.search(sources_text)
            if section_match is None:
                raise Reject("recovery-control", "recovery fixture provenance section disappeared from the positive")
            section = section_match.group(1)
            size_match = RECOVERY_SOURCES_SIZE.search(section)
            if size_match is None:
                raise Reject("recovery-control", "recovery fixture byte-count row disappeared from the positive")
            size_row = f"- bytes: {len(raw)} (bound: {MAX_RECOVERY_FIXTURE_BYTES})"
            section = section[:size_match.start()] + size_row + section[size_match.end():]
            amended_sources = (sources_text[:section_match.start(1)] + section
                               + sources_text[section_match.end(1):]).encode("utf-8")
            return validate_recovery_fixture(raw, amended_sources, verify_digest=False)

        wrong_source = json.loads(json.dumps(fixture))
        wrong_source["failure_snapshot"]["source_sha"] = "0" * 40
        controls += _recovery_expect_reject("wrong failed source", "recovery-identity",
            lambda: validate_mutated_fixture(wrong_source))
        wrong_release = json.loads(json.dumps(fixture))
        wrong_release["failure_snapshot"]["draft_detail"]["id"] += 1
        controls += _recovery_expect_reject("wrong draft identity", "recovery-draft",
            lambda: validate_mutated_fixture(wrong_release))
        nonzero_assets = json.loads(json.dumps(fixture))
        nonzero_assets["failure_snapshot"]["draft_assets"] = [{"id": 1}]
        controls += _recovery_expect_reject("unexpected starting asset", "recovery-assets",
            lambda: validate_mutated_fixture(nonzero_assets))
        wrong_time = json.loads(json.dumps(fixture))
        wrong_time["failure_snapshot"]["draft_detail"]["published_at"] = "2026-10-31T00:00:00Z"
        controls += _recovery_expect_reject("published draft state", "recovery-draft",
            lambda: validate_mutated_fixture(wrong_time))

        failed_body = fixture["failed_notes"]["text"].encode("utf-8")
        transport = RecoveryTransport(snapshot, failed_body, repaired, repair_spec["repaired_body_sha256"])
        if transport.patch(RECOVERY_RELEASE_ID, {"body": repaired.decode("utf-8")}) != "patched":
            raise Reject("recovery-patch", "qualified body was not applied by the in-memory patch model")
        positives += 1
        if transport.patch(RECOVERY_RELEASE_ID, {"body": repaired.decode("utf-8")}) != "no-op" or transport.patch_count != 1:
            raise Reject("recovery-idempotency", "identical body retry was not a safe no-op")
        positives += 1
        if transport.dispatch(dict(RECOVERY_DISPATCH)) != "dispatched" or transport.dispatch_count != 1:
            raise Reject("recovery-dispatch", "exact retry request was not accepted once")
        positives += 1
        if (transport.release_id, transport.tag, transport.source_sha, transport.draft, transport.prerelease,
                transport.published_at, transport.assets) != (
                RECOVERY_RELEASE_ID, RECOVERY_TAG, RECOVERY_SOURCE_SHA, True, False, None, []):
            raise Reject("recovery-patch", "body-only request changed draft or product identity")

        controls += _recovery_expect_reject("patch request with a state mutation", "recovery-patch-shape",
            lambda: RecoveryTransport(snapshot, failed_body, repaired, repair_spec["repaired_body_sha256"]).patch(
                RECOVERY_RELEASE_ID, {"body": repaired.decode("utf-8"), "draft": False}))
        controls += _recovery_expect_reject("wrong release id", "recovery-release-id",
            lambda: RecoveryTransport(snapshot, failed_body, repaired, repair_spec["repaired_body_sha256"]).patch(
                RECOVERY_RELEASE_ID + 1, {"body": repaired.decode("utf-8")}))
        changed = RecoveryTransport(snapshot, failed_body, repaired, repair_spec["repaired_body_sha256"])
        changed.patch(RECOVERY_RELEASE_ID, {"body": repaired.decode("utf-8")})
        controls += _recovery_expect_reject("conflicting second body", "recovery-repaired-digest",
            lambda: changed.patch(RECOVERY_RELEASE_ID, {"body": (repaired + b" ").decode("utf-8")}))
        published = RecoveryTransport(snapshot, failed_body, repaired, repair_spec["repaired_body_sha256"])
        published.published_at = "2026-10-31T00:00:00Z"
        controls += _recovery_expect_reject("publication raced before repair", "recovery-publication-race",
            lambda: published.patch(RECOVERY_RELEASE_ID, {"body": repaired.decode("utf-8")}))
        raced = RecoveryTransport(snapshot, failed_body, repaired, repair_spec["repaired_body_sha256"])
        raced.body = b"competing body"
        controls += _recovery_expect_reject("body changed concurrently", "recovery-publication-race",
            lambda: raced.patch(RECOVERY_RELEASE_ID, {"body": repaired.decode("utf-8")}))
        wrong_request = RecoveryTransport(snapshot, failed_body, repaired, repair_spec["repaired_body_sha256"])
        wrong_request.patch(RECOVERY_RELEASE_ID, {"body": repaired.decode("utf-8")})
        wrong_request.dispatch(dict(RECOVERY_DISPATCH))
        for label, mutate in (
            ("release id changed after repair", lambda state: setattr(state, "release_id", RECOVERY_RELEASE_ID + 1)),
            ("tag changed after repair", lambda state: setattr(state, "tag", "v0.2.1")),
            ("source changed after repair", lambda state: setattr(state, "source_sha", "0" * 40)),
            ("draft cleared after repair", lambda state: setattr(state, "draft", False)),
            ("prerelease enabled after repair", lambda state: setattr(state, "prerelease", True)),
            ("publication time changed after repair",
             lambda state: setattr(state, "published_at", "2026-10-31T00:00:00Z")),
            ("asset added after repair", lambda state: setattr(state, "assets", [{"id": 1}])),
            ("body changed after repair", lambda state: setattr(state, "body", b"competing body")),
        ):
            drifted = RecoveryTransport(snapshot, failed_body, repaired, repair_spec["repaired_body_sha256"])
            drifted.patch(RECOVERY_RELEASE_ID, {"body": repaired.decode("utf-8")})
            mutate(drifted)
            controls += _recovery_expect_reject(label, "recovery-dispatch-state",
                lambda drifted=drifted: drifted.dispatch(dict(RECOVERY_DISPATCH)))
        for label, mutate in (
            ("wrong workflow", lambda request: request.update(workflow="release.yml")),
            ("wrong ref", lambda request: request.update(ref=RECOVERY_TAG)),
            ("retry false", lambda request: request["inputs"].update(retry=False)),
            ("wrong tag input", lambda request: request["inputs"].update(tag_name="v0.2.1")),
            ("wrong source input", lambda request: request["inputs"].update(source_sha="0" * 40)),
            ("wrong release input", lambda request: request["inputs"].update(release_id="1")),
        ):
            invalid = json.loads(json.dumps(RECOVERY_DISPATCH))
            mutate(invalid)
            invalid_transport = RecoveryTransport(snapshot, failed_body, repaired,
                repair_spec["repaired_body_sha256"])
            invalid_transport.patch(RECOVERY_RELEASE_ID, {"body": repaired.decode("utf-8")})
            controls += _recovery_expect_reject(label, "recovery-dispatch-identity",
                lambda invalid=invalid, invalid_transport=invalid_transport: invalid_transport.dispatch(invalid))
        controls += _recovery_expect_reject("duplicate retry dispatch", "recovery-dispatch-duplicate",
            lambda: wrong_request.dispatch(dict(RECOVERY_DISPATCH)))

    if controls < 20 or positives < 5 or adoption_checks != 45:
        raise Reject("recovery-controls", "recovery controls lack the required negative and production-adoption positives")
    return controls, positives, original_hash, repaired_hash


def check_capture(text: bytes, sources: str) -> dict:
    """Provenance, bound, sanitization and schema contract of the saved capture. Raises Reject; returns the capture."""
    if len(text) > MAX_CAPTURE_BYTES:
        raise Reject("capture-oversize", f"captured.json exceeds the {MAX_CAPTURE_BYTES}-byte bound")
    if b"\r" in text:
        raise Reject("capture-eol", "captured.json must use LF line endings (its digest is byte-bound)")
    recorded = SOURCES_DIGEST.findall(sources)
    if len(recorded) != 1 or recorded[0] != sha256_bytes(text):
        raise Reject("capture-digest", "SOURCES.md does not record exactly the SHA-256 of captured.json")
    for field in ("Endpoints", "API version", "Sanitization", "Provenance"):
        if not re.search(rf"(?m)^## {field}$", sources):
            raise Reject("capture-provenance", f"SOURCES.md lacks the '{field}' section")
    try:
        capture = json.loads(text.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Reject("capture-json", "captured.json is not valid UTF-8 JSON") from error
    body = text.decode("utf-8")
    if FORBIDDEN_TEXT.search(body):
        raise Reject("capture-sanitization", "captured.json carries a local path, credential or key marker")
    for match in EMAIL.findall(body):
        if match != REDACTED_EMAIL:
            raise Reject("capture-sanitization", "captured.json carries an unredacted email address")
    if (capture.get("schema_version") != 1 or capture.get("kind") != "github-api-capture"
            or capture.get("repository") != REPO or capture.get("api_version") != "2022-11-28"):
        raise Reject("capture-schema", "captured.json header is not the schema-1 capture of this repository")
    responses = capture.get("responses")
    if not isinstance(responses, dict) or tuple(sorted(responses)) != tuple(sorted(RESPONSE_KEYS)):
        raise Reject("capture-schema", "captured.json responses are not exactly the declared endpoint set")
    for name, paths in REQUIRED_PATHS.items():
        for path in paths:
            if not dig(responses[name], path)[1]:
                raise Reject("capture-schema", f"captured {name} lacks the member {path} the production consumers read")
    for name, paths in FORBIDDEN_MEMBERS.items():
        for path in paths:
            if dig(responses[name], path)[1]:
                raise Reject("capture-schema", f"captured {name} carries the invented member {path}")
    for run in responses["check_runs"]["check_runs"]:
        if "repository" in run:
            raise Reject("capture-schema", "a captured check run carries an invented repository member")
    identity = capture.get("identity")
    if not isinstance(identity, dict) or not SHA1.fullmatch(str(identity.get("source_sha", ""))) \
            or not SHA1.fullmatch(str(identity.get("pr_head_sha", ""))):
        raise Reject("capture-schema", "captured identity lacks the source and PR head SHAs")
    return capture


# ----------------------------------------------------------------------------------------------------- transport
# The `gh` replacement. It is a separate process, so the production shell sees an ordinary executable. State lives in
# GB_STUB_DIR: state.json (rows, shapes, decisions), store/ (asset bytes) and calls.jsonl (every call, in order).
STUB_SOURCE = r'''#!/usr/bin/env python3
"""Replay transport standing in for the gh executable. It serves recorded shapes and refuses everything else."""
import fnmatch, hashlib, json, mimetypes, os, pathlib, re, shutil, subprocess, sys

DIR = pathlib.Path(os.environ["GB_STUB_DIR"])
REPO = os.environ["GB_STUB_REPO"]
MAX_BODY = 1024 * 1024
MAX_ITEMS = 100
MAX_UPLOAD = 8 * 1024 * 1024
''' + SHAPE_SRC + r'''

def log(entry):
    entry["argv"] = ARGV
    with open(DIR / "calls.jsonl", "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def refuse(why):
    log({"outcome": "refused", "why": why})
    sys.stderr.write("gh-replay-stub: refused: " + why + "\n")
    sys.exit(97)


def fail(message, mutation=None):
    log({"outcome": "failed", "why": message, "mutation": mutation})
    sys.stderr.write(message + "\n")
    sys.exit(1)


def state():
    return json.loads((DIR / "state.json").read_text(encoding="utf-8"))


def save(value):
    (DIR / "state.json").write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def asset_row(st, name, data):
    row = json.loads(json.dumps(st["asset_template"]))
    new_id = st["next_asset_id"]
    st["next_asset_id"] = new_id + 1
    tag = st["release"]["tag_name"]
    row.update(id=new_id, name=name, size=len(data), digest="sha256:" + hashlib.sha256(data).hexdigest(),
               node_id="RA_replay_%d" % new_id, state="uploaded", download_count=0,
               content_type=mimetypes.guess_type(name)[0] or "application/octet-stream",
               created_at="2026-10-28T00:00:00Z", updated_at="2026-10-28T00:00:00Z")
    row["url"] = re.sub(r"/assets/\d+$", "/assets/%d" % new_id, row["url"])
    row["browser_download_url"] = row["browser_download_url"].rsplit("/releases/download/", 1)[0] + "/releases/download/%s/%s" % (tag, name)
    return row


def release_object(st):
    release = json.loads(json.dumps(st["release"]))
    release["assets"] = st["assets"]
    return release


def serve(kind, body):
    shape = st_shapes.get(kind)
    if shape is not None:
        conforming = all(same_shape(item, shape) for item in body) if isinstance(body, list) and isinstance(shape, dict) else same_shape(body, shape)
        if not conforming:
            refuse("served %s response does not have the captured shape" % kind)
    text = json.dumps(body)
    if len(text) > MAX_BODY:
        refuse("response for %s exceeds the %d-byte bound" % (kind, MAX_BODY))
    items = body if isinstance(body, list) else next((v for v in body.values() if isinstance(v, list)), []) if isinstance(body, dict) else []
    if len(items) > MAX_ITEMS:
        refuse("response for %s exceeds %d items" % (kind, MAX_ITEMS))
    return text


def api(args):
    path, jq = None, None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--jq" and i + 1 < len(args):
            jq = args[i + 1]
            i += 2
        elif arg.startswith("--jq="):
            jq = arg[5:]
            i += 1
        elif arg.startswith("-") or path is not None:
            refuse("api flag or extra argument is not allowed: " + arg)
        else:
            path = arg
            i += 1
    if path is None:
        refuse("api without a path")
    route, _, query = path.partition("?")
    m = re.fullmatch(r"repos/([^/]+/[^/]+)/(.+)", route)
    if not m:
        refuse("unlisted endpoint " + route)
    if m.group(1) != REPO:
        refuse("repository %s is not the replay repository" % m.group(1))
    tail = m.group(2)
    st = state()
    kind = body = None
    if re.fullmatch(r"commits/[^/]+", tail) and not query:
        kind, ref = "commit", tail.split("/", 1)[1]
        if ref not in st["commits"]:
            fail("HTTP 404: Not Found (" + route + ")")
        body = st["commits"][ref]
    elif re.fullmatch(r"actions/runs/[0-9]+", tail) and not query:
        if int(tail.split("/")[2]) != st["ci_run"]["id"]:
            fail("HTTP 404: Not Found (" + route + ")")
        kind, body = "ci_run", st["ci_run"]
    elif re.fullmatch(r"commits/[0-9a-f]{40}/pulls", tail) and not query:
        if tail.split("/")[1] != st["source_sha"]:
            fail("HTTP 404: Not Found (" + route + ")")
        kind, body = "pull_requests", st["pull_requests"]
    elif re.fullmatch(r"actions/runs/[0-9]+/attempts/[0-9]+/jobs", tail) and query == "per_page=100":
        match = re.fullmatch(r"actions/runs/([0-9]+)/attempts/([0-9]+)/jobs", tail)
        if int(match.group(1)) != st["rehearsal_run_id"] or int(match.group(2)) != st["rehearsal_attempt"]:
            fail("HTTP 404: Not Found (" + route + ")")
        kind, body = "attempt_jobs", st["attempt_jobs"]
    elif tail == "releases" and query == "per_page=100":
        kind, body = "release", [release_object(st)]
    elif re.fullmatch(r"releases/\d+", tail) and not query:
        if int(tail.split("/")[1]) != st["release"]["id"]:
            fail("HTTP 404: Not Found (" + route + ")")
        kind, body = "release", release_object(st)
    elif re.fullmatch(r"releases/\d+/assets", tail) and query == "per_page=100":
        if int(tail.split("/")[1]) != st["release"]["id"]:
            fail("HTTP 404: Not Found (" + route + ")")
        kind, body = "release_assets", st["assets"]
    elif tail == "actions/workflows/release-please.yml/runs" and query == "per_page=100":
        kind, body = "workflow_runs", {"total_count": len(st["runs"]), "workflow_runs": st["runs"]}
    elif tail == "actions/workflows/release-rehearsal.yml/runs" and \
            query == "branch=rehearsal/%s&status=success&per_page=100" % st["release"]["tag_name"]:
        kind, body = "workflow_runs", {"total_count": len(st["rehearsal_runs"]), "workflow_runs": st["rehearsal_runs"]}
    elif re.fullmatch(r"pulls/\d+", tail) and not query:
        if int(tail.split("/")[1]) != st["pull_request"]["number"]:
            fail("HTTP 404: Not Found (" + route + ")")
        kind, body = "pull_request", st["pull_request"]
    elif re.fullmatch(r"commits/[0-9a-f]{40}/check-runs", tail) and query == "per_page=100":
        if tail.split("/")[1] != st["check_runs_head"]:
            fail("HTTP 404: Not Found (" + route + ")")
        kind, body = "check_runs", st["check_runs"]
    else:
        refuse("unlisted endpoint " + route + ("?" + query if query else ""))
    text = serve(kind, body)
    log({"outcome": "ok", "kind": kind})
    if jq is None:
        sys.stdout.write(text + "\n")
        return
    done = subprocess.run(["jq", "-r", jq], input=text, capture_output=True, text=True)
    sys.stdout.write(done.stdout)
    sys.stderr.write(done.stderr)
    sys.exit(done.returncode)


def parse_release(args, valueflags):
    tag, files, opts = None, [], {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in valueflags and i + 1 < len(args):
            opts.setdefault(arg, []).append(args[i + 1])
            i += 2
        elif arg.startswith("-"):
            opts.setdefault(arg, []).append(True)
            i += 1
        elif tag is None:
            tag = arg
            i += 1
        else:
            files.append(arg)
            i += 1
    return tag, files, opts


def release_download(args):
    tag, files, opts = parse_release(args, {"--repo", "--pattern", "--dir"})
    if set(opts) - {"--repo", "--pattern", "--dir"} or files or opts.get("--repo") != [REPO] or len(opts.get("--dir", [])) != 1:
        refuse("release download with unexpected arguments")
    st = state()
    if tag != st["release"]["tag_name"]:
        fail("release not found: " + str(tag))
    out = pathlib.Path(opts["--dir"][0])
    patterns = opts.get("--pattern") or ["*"]
    names = [row["name"] for row in st["assets"] if any(fnmatch.fnmatchcase(row["name"], p) for p in patterns)]
    if not names:
        fail("no assets match the file pattern")
    out.mkdir(parents=True, exist_ok=True)
    for name in names:
        shutil.copyfile(DIR / "store" / name, out / name)
    log({"outcome": "ok", "kind": "download", "names": names})


def release_upload(args):
    tag, files, opts = parse_release(args, {"--repo"})
    if set(opts) - {"--repo"} or opts.get("--repo") != [REPO] or len(files) != 1:
        refuse("release upload with unexpected arguments (no --clobber, one file)")
    st = state()
    if tag != st["release"]["tag_name"]:
        fail("release not found: " + str(tag))
    if not st["release"]["draft"]:
        refuse("upload to a published release")
    path = pathlib.Path(files[0])
    data = path.read_bytes() if path.is_file() else None
    if data is None or len(data) > MAX_UPLOAD:
        refuse("upload source is missing or exceeds the %d-byte bound" % MAX_UPLOAD)
    name = path.name
    if any(row["name"] == name for row in st["assets"]):
        fail("HTTP 422: asset under the same name already exists: " + name, "upload-refused:" + name)
    (DIR / "store" / name).write_bytes(data)
    st["assets"].append(asset_row(st, name, data))
    save(st)
    log({"outcome": "ok", "kind": "upload", "mutation": "upload:" + name})


def release_edit(args):
    tag, files, opts = parse_release(args, {"--repo"})
    if files or opts.get("--repo") != [REPO] or set(opts) != {"--repo", "--draft=false", "--verify-tag"}:
        refuse("release edit is allowed only as the one publish command: --draft=false --verify-tag")
    st = state()
    if tag != st["release"]["tag_name"] or not st["release"]["draft"]:
        refuse("publish decision for a release that is not the replay draft")
    st["release"]["draft"] = False
    st["decisions"].append({"tag": tag, "argv": ARGV})
    save(st)
    log({"outcome": "ok", "kind": "publish-decision", "mutation": "publish-decision"})


NIGHTLY_LIST_FIELDS = "databaseId,attempt,headSha,headBranch,event,status,conclusion,createdAt,workflowName"
NIGHTLY_VIEW_FIELDS = "databaseId,attempt,headSha,headBranch,event,status,conclusion,createdAt,updatedAt,workflowName,jobs"


def run_cmd(args):
    """gh run list / gh run view with exactly the closed field lists the nightly gate reads; recorded JSON, no other call."""
    st = state()
    tag = st["release"]["tag_name"]
    if args == ["list", "--repo", REPO, "--workflow", "nightly-asan.yml", "--branch", "rehearsal/" + tag, "--limit", "50",
                "--json", NIGHTLY_LIST_FIELDS]:
        body = st["nightly_runs"]
    elif len(args) == 6 and args[0] == "view" and args[2:] == ["--repo", REPO, "--json", NIGHTLY_VIEW_FIELDS]:
        body = st["nightly_view"].get(args[1])
        if body is None:
            fail("HTTP 404: Not Found (run " + args[1] + ")")
    else:
        refuse("run command is allowed only as the two nightly gate reads")
    log({"outcome": "ok", "kind": "nightly-run"})
    sys.stdout.write(json.dumps(body) + "\n")


ARGV = sys.argv[1:]
st_shapes = state()["shapes"] if (DIR / "state.json").is_file() else {}
if not ARGV:
    refuse("no command")
if ARGV[0] == "api":
    api(ARGV[1:])
elif ARGV[0] == "run":
    run_cmd(ARGV[1:])
elif ARGV[0:2] == ["release", "download"]:
    release_download(ARGV[2:])
elif ARGV[0:2] == ["release", "upload"]:
    release_upload(ARGV[2:])
elif ARGV[0:2] == ["release", "edit"]:
    release_edit(ARGV[2:])
else:
    refuse("unlisted command " + " ".join(ARGV[:2]))
'''

# The download helper the lifecycle runs from `trusted/`. Only the transport differs: it keeps the production CLI contract
# (URL, OUTPUT, --max-bytes, --total-timeout), accepts the single expected GitHub archive URL and nothing else.
DOWNLOAD_STUB = r'''#!/usr/bin/env python3
import hashlib, json, os, pathlib, re, sys
args = sys.argv[1:]
dir_ = pathlib.Path(os.environ["GB_STUB_DIR"])
def log(entry):
    with open(dir_ / "calls.jsonl", "a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(entry, argv=["download-release-artifact"] + args), sort_keys=True) + "\n")
if len(args) < 2 or not re.fullmatch(r"https://github\.com/%s/archive/refs/tags/v[0-9]+\.[0-9]+\.[0-9]+\.tar\.gz" % re.escape(os.environ["GB_STUB_REPO"]), args[0]):
    log({"outcome": "refused", "why": "unexpected URL"}); sys.stderr.write("download-stub: refused unexpected URL\n"); sys.exit(97)
rest = args[2:]
if "--max-bytes" not in rest or "--total-timeout" not in rest:
    log({"outcome": "refused", "why": "unbounded download"}); sys.stderr.write("download-stub: refused an unbounded download\n"); sys.exit(97)
data = (dir_ / "archive.tar.gz").read_bytes()
pathlib.Path(args[1]).write_bytes(data)
log({"outcome": "ok", "kind": "archive", "sha256": hashlib.sha256(data).hexdigest()})
'''
GH_WRAPPER = '#!/usr/bin/env bash\nexec "{python}" -I "{stub}" "$@"\n'


# ------------------------------------------------------------------------------------------------------- the lab

def retarget(value, mapping: dict[str, str]):
    """Rewrite the captured identity (tag, ids, SHAs) to the fixture identity inside every string, id and URL."""
    text = json.dumps(value)
    for old, new in mapping.items():
        text = text.replace(old, new)
    return json.loads(text)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise Reject("module-load", f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_git(repo: Path, *args: str, check: bool = True) -> str:
    env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_TERMINAL_PROMPT": "0"}
    done = subprocess.run(["git", "-C", str(repo), "-c", "user.name=replay", "-c", "user.email=replay@example.invalid",
                           "-c", "commit.gpgsign=false", *args], capture_output=True, text=True, timeout=120, env=env)
    if check and done.returncode != 0:
        raise Reject("git-failed", f"git {args[0]} failed: {done.stderr.strip()[:200]}")
    return done.stdout.strip()


class Outcome:
    def __init__(self, rc: int, out: str, err: str, calls: list[dict]) -> None:
        self.rc, self.out, self.err, self.calls = rc, out, err, calls

    @property
    def text(self) -> str:
        return self.out + self.err

    def mutations(self) -> list[str]:
        return [c["mutation"] for c in self.calls if c.get("mutation") and c.get("outcome") == "ok"]


class Template:
    """Everything immutable that a scenario copies: the judge repository, evidence, candidate assets and seeded state."""

    def __init__(self, base: Path, rev: str, files: dict[str, bytes], capture: dict) -> None:
        self.base, self.rev, self.files, self.capture = base, rev, files, capture
        delivery_dir = base / "delivery-rev"
        for relative in (DELIVERY,):
            target = delivery_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(files[relative])
        self.delivery = load_module(delivery_dir / DELIVERY, "_lifecycle_delivery_fixture")
        self.judge_parent = base / "judge"
        repo, producer, source = self.delivery.make_fixture_repo(self.judge_parent)
        self.judge, self.source, self.tag = repo, source, "v0.2.0"
        # The production perf-receipt verifier reads immutable Git objects from both the tagged source and the
        # ratchet base. Give this synthetic source those exact committed bytes and an alternates link to the project
        # object database; the temporary replay repository itself remains isolated and has no network access.
        objects = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--path-format=absolute", "--git-path", "objects"],
                                 capture_output=True, text=True, timeout=60)
        if objects.returncode != 0 or not Path(objects.stdout.strip()).is_dir():
            raise Reject("fixture-perf-receipt", "the immutable project Git object store is unavailable")
        alternates = repo / ".git/objects/info/alternates"
        alternates.parent.mkdir(parents=True, exist_ok=True)
        alternates.write_text(objects.stdout.strip() + "\n", encoding="utf-8")
        perf_source_files = ("tests/baseline/perf-gate-v1.txt", "fixtures/tracer/tracer.gb",
                             "fixtures/libbet/libbet.gb", "fixtures/visible-demo/demo.gb")
        for relative in perf_source_files:
            done = subprocess.run(["git", "-C", str(ROOT), "show", f"{PERF_SOURCE_REV}:{relative}"],
                                  capture_output=True, timeout=60)
            if done.returncode != 0:
                raise Reject("fixture-perf-receipt", f"the immutable performance source lacks {relative}")
            target = repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(done.stdout)
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                        "add", "--", *perf_source_files], check=True, capture_output=True, timeout=60)
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                        "-c", "commit.gpgsign=false", "commit", "-q", "-m", "source: pinned performance policy and ROMs"],
                       check=True, capture_output=True, timeout=60)
        self.source = run_git(repo, "rev-parse", "HEAD")
        run_git(repo, "tag", "-f", self.tag, self.source)
        source = self.source
        for relative in JUDGE_FILES:
            target = repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(files[relative])
        run_git(repo, "add", "-A")
        run_git(repo, "commit", "-q", "-m", "judge: production scripts at the replay revision")
        self.judge_sha = run_git(repo, "rev-parse", "HEAD")
        fixture_data = repo / "tests/data/perf-gate"
        shutil.copytree(ROOT / "tests/data/perf-gate", fixture_data)
        perf_receipt = base / "perf-gate-receipt.json"
        perf_env = os.environ.copy()
        perf_env.update(GITHUB_RUN_ID="40259198255", GITHUB_RUN_ATTEMPT="1")
        perf = subprocess.run([sys.executable, "-I", str(repo / "tests/scripts/verify-perf-gate.py"), "--evaluate",
                               "--limits", "tests/baseline/perf-gate-v1.txt", "--base", "tests/data/perf-gate/base",
                               "--head", "tests/data/perf-gate/head-pass", "--realtime", "tests/data/perf-gate/realtime-pass.txt",
                               "--base-rev", PERF_LIMITS_BASE_REV, "--source-head-rev", self.source,
                               "--build-base-identity", "a" * 64, "--build-head-identity", "b" * 64,
                               "--emit-receipt", str(perf_receipt)], cwd=repo, env=perf_env,
                              capture_output=True, text=True, timeout=60)
        if perf.returncode != 0 or not perf_receipt.is_file():
            raise Reject("fixture-perf-receipt", f"the exact source performance receipt fixture failed: {perf.stderr.strip()[-250:]}")
        self.perf_gate_receipt = perf_receipt.read_bytes()
        self.perf_gate_run = (json.dumps({"event": "push", "head_sha": self.source, "path": ".github/workflows/ci.yml",
                                          "id": 40259198255, "run_attempt": 1}, sort_keys=True, indent=2) + "\n").encode()
        # The rehearsed head: another commit with exactly the tagged tree (a squash commit differs, its tree does not), kept
        # on a branch so every clone of the judge repository holds it.
        self.rehearsal_head = run_git(repo, "commit-tree", f"{source}^{{tree}}", "-p", source, "-m", "rehearsal head")
        run_git(repo, "branch", "rehearsal-fixture", self.rehearsal_head)
        self.other_head = run_git(repo, "commit-tree", f"{self.judge_sha}^{{tree}}", "-p", source, "-m", "head with another tree")
        run_git(repo, "branch", "other-tree-fixture", self.other_head)
        self.evidence = base / "evidence"
        self.archive = self.delivery.make_evidence(self.evidence, source, repo)
        # the production sidecar also names the tagged ledger blob under `ledger.git_blob_oid`, which the draft gate reads
        sidecar = json.loads((self.evidence / "support-ledger.json").read_text())
        sidecar["ledger"] = {"git_blob_oid": sidecar["ledger_blob"]}
        (self.evidence / "support-ledger.json").write_text(json.dumps(sidecar, indent=2, sort_keys=True) + "\n")
        self.pr_head = capture["identity"]["pr_head_sha"].replace("c", "d", 1) if capture["identity"]["pr_head_sha"] == source \
            else capture["identity"]["pr_head_sha"]
        self.pr_number = capture["responses"]["pull_request"]["number"]
        self.candidate = self.candidate_assets()
        self.state_dir = base / "state-template"
        self.seed(self.state_dir)
        for name_, data in self.candidate.items():
            stub_upload(self.state_dir, self.tag, name_, data, base / "seed")
        (self.state_dir / "calls.jsonl").unlink(missing_ok=True)
        self.stages: dict[str, Path] = {}

    # -- fixture content ---------------------------------------------------------------------------------------
    def candidate_assets(self) -> dict[str, bytes]:
        source, tag = self.source, self.tag

        def jb(value) -> bytes:
            return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()

        proof = {"head_sha": self.pr_head, "merge_commit_sha": source, "pr_number": self.pr_number, "required_checks": "passed"}
        files: dict[str, bytes] = {
            "gabbaboy-core-linux-x64.tar.gz": b"replay linux core archive\n",
            "gabbaboy-notices.txt": b"replay notices\n",
            "build-receipt.json": jb({"source_sha": source, "asset_name": "gabbaboy-core-linux-x64.tar.gz",
                                      "build": {"runner": "replay-linux"}}),
            "gabbaboy-core-macos-arm64.tar.gz": b"replay macos core archive\n",
            "gabbaboy-build-receipt-macos-arm64.json": jb({"source_sha": source, "platform": "macos-arm64", "build": {"runner": "replay-macos"}}),
            "gabbaboy-preview-macos-arm64.tar.gz": b"replay macos preview archive\n",
            "gabbaboy-preview-macos-arm64-build-receipt.json": jb({"source_revision": source, "result": "passed"}),
            "gabbaboy-core-windows-x64.tar.gz": b"replay windows core archive\n",
            "gabbaboy-build-receipt-windows-x64.json": jb({"source_sha": source, "platform": "windows-x64", "build": {"runner": "replay-windows"}}),
            "candidate-receipt.json": jb({"schema_version": 1, "tag_name": tag, "source_sha": source,
                                          "release_id": str(RELEASE_ID), "draft": True, "prior_pr_proof": proof}),
            "source-receipt.json": jb({"schema_version": 1, "version": tag[1:], "tag_name": tag, "source_sha": source,
                                       "release_id": str(RELEASE_ID), "draft": True, "source_clean": True, "prior_pr_proof": proof}),
            "source-archive-receipt.json": (self.evidence / "source-archive-receipt.json").read_bytes(),
            "v02-consumer-receipt.json": (self.evidence / "v02-consumer-receipt.json").read_bytes(),
        }
        for platform in ("macos-arm64", "windows-x64"):
            archive = files[f"gabbaboy-core-{platform}.tar.gz"]
            files[f"gabbaboy-core-{platform}.tar.gz.sha256"] = (sha256_bytes(archive) + "\n").encode()
        return files

    def seed(self, directory: Path) -> None:
        """Build the stub state: the captured shapes retargeted to the fixture identity, with the candidate draft."""
        responses = copy.deepcopy(self.capture["responses"])
        identity = self.capture["identity"]
        mapping = {
            str(identity["release_id"]): str(RELEASE_ID), identity["tag"]: self.tag,
            identity["source_sha"]: self.source, identity["pr_head_sha"]: self.pr_head,
            str(identity["run_id"]): str(RUN_ID - 1000), "40257161612": str(RUN_ID - 500),
        }
        responses = {name: retarget(value, mapping) for name, value in responses.items()}
        shapes = {
            "commit": key_shape(responses["commit"]), "ci_run": key_shape(responses["ci_run"]),
            "release": key_shape(responses["release"]),
            "release_assets": key_shape(responses["release_assets"]), "workflow_runs": key_shape(responses["workflow_runs"]),
            "pull_request": key_shape(responses["pull_request"]), "pull_requests": key_shape(responses["pull_requests"]),
            "attempt_jobs": key_shape(responses["attempt_jobs"]), "check_runs": key_shape(responses["check_runs"]),
        }
        release = responses["release"]
        template = copy.deepcopy(release["assets"][0])
        release.update(id=RELEASE_ID, tag_name=self.tag, draft=True, prerelease=False, name=self.tag)
        release["assets"] = []
        run_template = responses["workflow_runs"]["workflow_runs"][0]
        old = copy.deepcopy(run_template)
        old.update(id=RUN_ID - 1000, run_attempt=1, status="completed", conclusion="failure", head_sha=self.source,
                   event="push", path=".github/workflows/release-please.yml")
        pull = responses["pull_request"]
        pull.update(number=self.pr_number, state="closed", merged_at="2026-10-26T00:00:00Z", merge_commit_sha=self.source)
        pull["base"]["ref"] = "main"
        pull["base"]["repo"]["full_name"] = REPO
        pull["head"]["sha"] = self.pr_head
        pull["head"]["repo"]["full_name"] = REPO
        checks = responses["check_runs"]
        for run in checks["check_runs"]:
            run["head_sha"] = self.pr_head
            run["status"], run["conclusion"] = "completed", "success"
        commit = responses["commit"]
        commit["sha"] = self.source
        rehearsal = copy.deepcopy(run_template)
        rehearsal.update(id=RUN_ID - 500, run_attempt=1, status="completed", conclusion="success", head_sha=self.rehearsal_head,
                         head_branch="rehearsal/" + self.tag, event="workflow_dispatch",
                         path=".github/workflows/release-rehearsal.yml")
        rehearsal["repository"]["full_name"] = REPO
        rehearsal["head_repository"]["full_name"] = REPO
        pull_requests = responses["pull_requests"]
        if not isinstance(pull_requests, list) or not pull_requests:
            raise Reject("capture-incomplete", "the captured merge commit has no pull request")
        matching_prs = [pr for pr in pull_requests if pr.get("merge_commit_sha") == self.source and pr.get("base", {}).get("ref") == "main"]
        if len(matching_prs) != 1:
            raise Reject("capture-incomplete", "the captured merge commit does not map to exactly one merged main PR")
        matching_prs[0]["head"]["sha"] = self.rehearsal_head
        attempt_jobs = responses["attempt_jobs"]
        for job in attempt_jobs["jobs"]:
            job["run_id"] = RUN_ID - 500
            job["run_attempt"] = rehearsal["run_attempt"]
        nightly = {"databaseId": NIGHTLY_RUN_ID, "attempt": 1, "headSha": self.rehearsal_head,
                   "headBranch": "rehearsal/" + self.tag, "event": "workflow_dispatch", "status": "completed",
                   "conclusion": "success", "createdAt": "2026-10-26T12:00:00Z", "workflowName": "nightly-asan"}
        nightly_view = dict(nightly, updatedAt="2026-10-26T12:40:05Z", jobs=[
            {"name": "asan-full-replay", "status": "completed", "conclusion": "success",
             "startedAt": "2026-10-26T12:00:10Z", "completedAt": "2026-10-26T12:40:00Z"}])
        state = {
            "release": release, "assets": [], "asset_template": template, "next_asset_id": FIRST_ASSET_ID,
            "runs": [old], "run_template": run_template, "pull_request": pull, "check_runs": checks,
            "check_runs_head": self.pr_head, "commits": {self.tag: commit, self.source: commit},
            "source_sha": self.source, "pull_requests": pull_requests, "attempt_jobs": attempt_jobs,
            "ci_run": responses["ci_run"],
            "rehearsal_run_id": rehearsal["id"], "rehearsal_attempt": rehearsal["run_attempt"],
            "decisions": [], "shapes": shapes, "rehearsal_runs": [rehearsal],
            "nightly_runs": [nightly], "nightly_view": {str(NIGHTLY_RUN_ID): nightly_view},
        }
        directory.mkdir(parents=True)
        (directory / "store").mkdir()
        (directory / "state.json").write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
        (directory / "archive.tar.gz").write_bytes(self.archive.read_bytes())
        stub = directory / "gh_stub.py"
        stub.write_text(STUB_SOURCE, encoding="utf-8")


def stub_upload(stub_dir: Path, tag: str, name: str, data: bytes, staging_root: Path) -> None:
    """Add an asset to a stub state through the stub's own upload path (so rows are built by one implementation)."""
    staging = staging_root / name
    staging.parent.mkdir(parents=True, exist_ok=True)
    staging.write_bytes(data)
    env = {"PATH": os.environ.get("PATH", ""), "GB_STUB_DIR": str(stub_dir), "GB_STUB_REPO": REPO}
    done = subprocess.run([sys.executable, "-I", str(stub_dir / "gh_stub.py"), "release", "upload", tag, str(staging), "--repo", REPO],
                          capture_output=True, text=True, env=env, timeout=60)
    if done.returncode != 0:
        raise Reject("seed-failed", f"seeding {name} failed: {done.stderr.strip()[:200]}")


_COUNTER = itertools.count(1)
_COUNTER_LOCK = threading.Lock()


class Scenario:
    """One disposable copy of the stub state, judge checkout and workspaces."""

    def __init__(self, template: Template, name: str, stage: str | None = None) -> None:
        with _COUNTER_LOCK:
            number = next(_COUNTER)
        self.t = template
        self.root = template.base / f"scenario-{number:03d}-{re.sub('[^a-z0-9]+', '-', name.lower())[:40]}"
        self.stub = self.root / "stub"
        shutil.copytree(template.stages[stage] if stage else template.state_dir, self.stub)
        (self.stub / "calls.jsonl").unlink(missing_ok=True)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        gh = self.bin / "gh"
        gh.write_text(GH_WRAPPER.format(python=sys.executable, stub=self.stub / "gh_stub.py"), encoding="utf-8")
        gh.chmod(0o755)
        self.home = self.root / "home"
        self.home.mkdir()
        self.run_id = RUN_ID
        self.attempt = 1
        self.workspaces: dict[str, Path] = {}

    # -- stub helpers ------------------------------------------------------------------------------------------
    def env(self, workspace: Path, **extra: str) -> dict[str, str]:
        temp = workspace / "runner-temp"
        temp.mkdir(exist_ok=True)
        env = {
            "PATH": f"{self.bin}{os.pathsep}{os.environ.get('PATH', '')}", "HOME": str(self.home),
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_TERMINAL_PROMPT": "0",
            "GB_STUB_DIR": str(self.stub), "GB_STUB_REPO": REPO, "GH_REPO": REPO, "GITHUB_REF": "refs/heads/main",
            "GITHUB_SHA": self.t.judge_sha, "GITHUB_RUN_ID": str(self.run_id), "GITHUB_RUN_ATTEMPT": str(self.attempt),
            "GITHUB_ENV": str(workspace / "github-env"), "RUNNER_TEMP": str(temp), "TMPDIR": str(temp),
            "RELEASE_TAG": self.t.tag, "SOURCE_SHA": self.t.source, "INPUT_RELEASE_ID": "", "RETRY": "false",
            "RELEASE_ID": "", "GITHUB_WORKSPACE": str(workspace),
        }
        env.update(extra)
        return env

    def state(self) -> dict:
        return json.loads((self.stub / "state.json").read_text(encoding="utf-8"))

    def write_state(self, state: dict) -> None:
        (self.stub / "state.json").write_text(json.dumps(state, sort_keys=True), encoding="utf-8")

    def mutations_logged(self) -> list[str]:
        return [c["mutation"] for c in self.calls() if c.get("mutation") and c.get("outcome") == "ok"]

    def calls(self) -> list[dict]:
        path = self.stub / "calls.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.is_file() else []

    def add_asset(self, name: str, data: bytes) -> None:
        stub_upload(self.stub, self.t.tag, name, data, self.root / "seed")
        (self.stub / "calls.jsonl").unlink(missing_ok=True)

    def snapshot(self, label: str) -> None:
        """Freeze the stub state so later controls start from this stage without rerunning the earlier modes."""
        target = self.t.base / f"stage-{label}"
        shutil.copytree(self.stub, target)
        self.t.stages[label] = target

    def replace_asset(self, name: str, data: bytes, keep_digest: bool = False) -> None:
        """Replace an attached asset's bytes as a hostile writer would (the row digest follows unless keep_digest)."""
        (self.stub / "store" / name).write_bytes(data)
        if not keep_digest:
            state = self.state()
            for row in state["assets"]:
                if row["name"] == name:
                    row["digest"] = "sha256:" + sha256_bytes(data)
                    row["size"] = len(data)
            self.write_state(state)

    def remove_asset(self, name: str) -> None:
        state = self.state()
        state["assets"] = [row for row in state["assets"] if row["name"] != name]
        self.write_state(state)
        (self.stub / "store" / name).unlink(missing_ok=True)

    def asset_bytes(self, name: str) -> bytes:
        return (self.stub / "store" / name).read_bytes()

    def asset_names(self) -> list[str]:
        return [row["name"] for row in self.state()["assets"]]

    def set_runs(self, *, own_status: str = "in_progress", own_event: str = "push", extra: list[dict] | None = None) -> None:
        """The live release-workflow run list: this run (in progress) after the earlier failed one, plus any extra rows."""
        state = self.state()
        own = copy.deepcopy(state["run_template"])
        own.update(id=self.run_id, run_attempt=self.attempt, status=own_status, conclusion=None, head_sha=self.t.judge_sha,
                   event=own_event, path=".github/workflows/release-please.yml")
        state["runs"] = [own] + [r for r in state["runs"] if r["id"] != self.run_id] + (extra or [])
        self.write_state(state)

    # -- workspaces --------------------------------------------------------------------------------------------
    def trusted(self, workspace: Path, script: str | None = None) -> None:
        shutil.copytree(self.t.judge, workspace / "trusted", symlinks=True)
        transport = workspace / "trusted/.github/scripts/download-release-artifact.py"
        transport.write_text(DOWNLOAD_STUB, encoding="utf-8")
        if script is not None:
            (workspace / "trusted" / LIFECYCLE).write_text(script, encoding="utf-8")

    def attach_workspace(self, name: str, regenerated: dict[str, bytes] | None = None, script: str | None = None) -> Path:
        """The attacher workspace is NOT a git work tree: only `trusted/` and the downloaded producer artifacts."""
        ws = self.root / name
        ws.mkdir()
        self.trusted(ws, script)
        for directory, names in (("evidence-corpus", ("support-ledger.json", "cgb-corpus-receipt.json")),
                                 ("evidence-fuzz", ("v02-fuzz-receipt.json",)), ("evidence-performance", ("v02-performance-receipt.json",))):
            (ws / "build" / directory).mkdir(parents=True)
            for item in names:
                data = (regenerated or {}).get(item) or (self.t.evidence / item).read_bytes()
                (ws / "build" / directory / item).write_bytes(data)
        self.workspaces[name] = ws
        return ws

    def subject_workspace(self, name: str, script: str | None = None) -> Path:
        """A judge-job workspace: the exact tag checkout (a git work tree at the source SHA) with `trusted/` inside."""
        ws = self.root / name
        run_git(self.root, "clone", "-q", "--no-hardlinks", str(self.t.judge), str(ws))
        run_git(ws, "checkout", "-q", "--detach", self.t.source)
        self.trusted(ws, script)
        perf_dir = ws / "build/evidence-fuzz/perf-gate"
        perf_dir.mkdir(parents=True, exist_ok=True)
        (perf_dir / "perf-gate-receipt.json").write_bytes(self.t.perf_gate_receipt)
        (ws / "build/evidence-fuzz/perf-gate-run.json").write_bytes(self.t.perf_gate_run)
        self.workspaces[name] = ws
        return ws

    def run_mode(self, ws: Path, mode: str, *, script_path: str = "trusted/" + LIFECYCLE, **env_extra: str) -> Outcome:
        before = len(self.calls())
        env = self.env(ws, **env_extra)
        started = time.monotonic()
        done = subprocess.run(["bash", script_path, mode], cwd=ws, env=env, capture_output=True, text=True, timeout=180)
        outcome = Outcome(done.returncode, done.stdout, done.stderr, self.calls()[before:])
        outcome.seconds = time.monotonic() - started
        return outcome

    def run_gate(self, ws: Path, *args: str, **env_extra: str) -> Outcome:
        """Run one mode of the production gate script directly, from the trusted checkout, with the workflow's environment."""
        before = len(self.calls())
        done = subprocess.run(["bash", "trusted/.github/scripts/verify-release-gates.sh", *args], cwd=ws,
                              env=self.env(ws, **env_extra), capture_output=True, text=True, timeout=180)
        return Outcome(done.returncode, done.stdout, done.stderr, self.calls()[before:])

    def run_workflow_step(self, ws: Path, workflow: str, step: str, **env_extra: str) -> Outcome:
        before = len(self.calls())
        body = workflow_step_run(workflow, step)
        done = subprocess.run(["bash", "-c", body], cwd=ws, env=self.env(ws, **env_extra), capture_output=True, text=True, timeout=120)
        return Outcome(done.returncode, done.stdout, done.stderr, self.calls()[before:])


def workflow_step_run(workflow: str, step: str) -> str:
    """The `run: |` block of the named step, dedented: the same shell the hosted runner executes."""
    lines = workflow.split("\n")
    marker = f"      - name: {step}"
    if lines.count(marker) != 1:
        raise Reject("workflow-step", f"release.yml has no single step named {step!r}")
    i = lines.index(marker) + 1
    while not lines[i].startswith("        run:"):
        if lines[i].startswith("      - name:"):
            raise Reject("workflow-step", f"step {step!r} has no run block")
        i += 1
    if lines[i].strip() != "run: |":
        return lines[i].split("run:", 1)[1].strip()
    block = []
    i += 1
    while i < len(lines) and (lines[i].startswith(" " * 10) or not lines[i].strip()):
        block.append(lines[i][10:])
        i += 1
    return "\n".join(block).rstrip("\n") + "\n"


def check_wiring(workflow: str, script: str | None) -> None:
    """The production workflow must call the extracted lifecycle script for every mode, from the right job."""
    if script is None:
        raise Reject("lifecycle-missing", f"{LIFECYCLE} is absent: the lifecycle is not extracted")
    for mode, job in MODES.items():
        call = f"run: bash trusted/.github/scripts/release-evidence-lifecycle.sh {mode}\n"
        start = workflow.find(f"\n  {job}:\n")
        following = re.compile(r"\n  [a-z0-9-]+:\n").search(workflow, start + 1) if start >= 0 else None
        body = workflow[start:following.start() if following else len(workflow)] if start >= 0 else ""
        if start < 0 or body.count(call) != 1:
            raise Reject("lifecycle-unwired", f"release.yml job {job} does not call the lifecycle mode {mode} from the trusted checkout exactly once")


# -------------------------------------------------------------------------------------------- the positive replay

def first_attempt(s: Scenario, wf: str) -> dict[str, Outcome]:
    """attach -> manifest -> final gates -> publish decision, the way the hosted workflow orders them."""
    out: dict[str, Outcome] = {}
    s.set_runs()
    attach = s.attach_workspace("attach")
    out["attach-evidence"] = s.run_mode(attach, "attach-evidence")
    manifest = s.subject_workspace("manifest")
    out["validate-evidence"] = s.run_mode(manifest, "validate-evidence")
    out["build-manifest"] = s.run_mode(manifest, "build-manifest")
    publish = s.subject_workspace("publish")
    env = {"RELEASE_ID": str(RELEASE_ID)}
    out["load-verifiers"] = s.run_workflow_step(publish, wf, LOAD_VERIFIERS_STEP, **env)
    for mode in ("validate-draft", "final-gate", "nightly-gate", "publish-draft"):
        out[mode] = s.run_mode(publish, mode, **env)
        if mode == "validate-draft" and out[mode].rc == 0 and "finalized-first" not in s.t.stages:
            s.snapshot("finalized-first")  # an attempt that stopped here has attached the final metadata
    return out


def require_ok(outcomes: dict[str, Outcome], label: str) -> None:
    for mode, outcome in outcomes.items():
        if outcome.rc != 0:
            raise Reject("replay-failed", f"{label}: {mode} exited {outcome.rc}: {outcome.text.strip()[-400:]}")


def expect_fail(outcome: Outcome, label: str, needle: str) -> None:
    """A rejection is only credited when the run exited non-zero AND said why in the intended words."""
    if outcome.rc == 0:
        raise Reject("control-accepted", f"{label}: the lifecycle accepted a defect")
    if "gh-replay-stub: refused" in outcome.err and "refused" not in needle:
        raise Reject("control-transport", f"{label}: the replay transport refused a call instead of the production check: {outcome.err.strip()[-200:]}")
    if needle not in outcome.text:
        raise Reject("control-wrong-reason", f"{label}: wanted {needle!r}, got {outcome.text.strip()[-300:]!r}")


def replay(rev: str, files: dict[str, bytes], capture: dict, base: Path) -> dict[str, int]:
    wf = files[WORKFLOW].decode("utf-8")
    check_wiring(wf, files[LIFECYCLE].decode("utf-8"))
    template = Template(base, rev, files, capture)
    perf = json.loads((template.evidence / "v02-performance-receipt.json").read_text())
    if (perf.get("schema_version") != 3 or perf["regression_disposition"].get("release_disposition") != "advisory"
            or not perf["measurement"]["summary"].get("review_trigger")):
        raise Reject("fixture-advisory", "the replay evidence does not carry a triggered advisory performance receipt")
    s = Scenario(template, "first-attempt")
    out = first_attempt(s, wf)
    require_ok(out, "first attempt")
    # the attacher ran in a workspace that is not a git work tree
    if subprocess.run(["git", "-C", str(s.workspaces["attach"]), "rev-parse", "--show-toplevel"], capture_output=True,
                      env={**os.environ, "GIT_CEILING_DIRECTORIES": str(s.root)}).returncode == 0:
        raise Reject("replay-workspace", "the attacher workspace is a git work tree")
    state, calls = s.state(), s.calls()
    refused = [c for c in calls if c.get("outcome") == "refused"]
    if refused:
        raise Reject("replay-refused", f"the transport refused a production call: {refused[0]['why']}")
    names = s.asset_names()
    if len(names) != len(set(names)) or len(names) != len(template.candidate) + 4 + 1 + 2:
        raise Reject("replay-inventory", f"unexpected final draft inventory: {len(names)} assets")
    uploads = [m for m in (c.get("mutation") for c in calls) if m]
    expected_uploads = {f"upload:{n}" for n in (*EVIDENCE_ATTACHED, "candidate-platform-manifest.json", *FINAL_NAMES)}
    if set(uploads) - {"publish-decision"} != expected_uploads or uploads.count("publish-decision") != 1 or len(uploads) != 8:
        raise Reject("replay-mutations", f"the lifecycle wrote something other than the evidence, manifest, final receipts and one decision: {uploads}")
    if len(state["decisions"]) != 1 or "--draft=false" not in state["decisions"][0]["argv"]:
        raise Reject("replay-decision", "the publish decision was not recorded exactly once")
    release_receipt = json.loads(s.asset_bytes("release-receipt.json"))
    if release_receipt.get("perf_gate") != json.loads(template.perf_gate_receipt):
        raise Reject("replay-perf-gate", "release-receipt.json does not carry the verified CI performance gate receipt")
    expected_profile = f"{template.tag} deterministic software profiles DMG-CPU-B and CGB-CPU-E as scoped by docs/support/{template.tag}.md"
    if release_receipt.get("limits", [None])[0] != expected_profile:
        raise Reject("replay-profile", "release receipt does not name both version-scoped software profiles")
    inventory_path = s.workspaces["publish"] / "build/release-final/pre-publish-inventory.json"
    if not inventory_path.is_file():
        raise Reject("replay-pre-publish-inventory", "final-gate did not write the durable pre-publish inventory")
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    expected_assets = sorted(({"name": row["name"], "id": row["id"], "digest": row["digest"]}
                              for row in state["assets"]), key=lambda row: row["name"])
    expected_inventory = {"schema_version": 1, "kind": "pre-publish-inventory", "tag": template.tag,
                          "source_sha": template.source, "release_id": RELEASE_ID, "run_id": RUN_ID,
                          "run_attempt": 1, "assets": expected_assets}
    if inventory != expected_inventory:
        raise Reject("replay-pre-publish-inventory", "pre-publish inventory does not bind the exact sorted draft asset names, ids and digests")
    sums = s.asset_bytes("SHA256SUMS").decode().splitlines()
    if sorted(line.split("  ", 1)[1] for line in sums) != sorted(n for n in names if n not in FINAL_NAMES):
        raise Reject("replay-sha256sums", "SHA256SUMS does not cover exactly the qualified inventory")
    # retry: the first attempt stopped after the final metadata was attached; fresh producers regenerate different bytes
    r = Scenario(template, "retry", "finalized-first")
    before = {n: r.asset_bytes(n) for n in r.asset_names()}
    r.run_id, r.attempt = RUN_ID + 1, 1
    r.set_runs(own_event="workflow_dispatch")
    regenerated = {
        "support-ledger.json": json.dumps({**json.loads(before["support-ledger.json"]), "run_id": "retry-run"}, sort_keys=True).encode() + b"\n",
        "cgb-corpus-receipt.json": b'{"corpus": "complete", "nonce": "retry"}\n',
    }
    rt = {"RETRY": "true", "INPUT_RELEASE_ID": str(RELEASE_ID), "RELEASE_ID": str(RELEASE_ID)}
    attach2 = r.attach_workspace("attach-2", regenerated)
    if (attach2 / "build/evidence-corpus/cgb-corpus-receipt.json").read_bytes() == before["cgb-corpus-receipt.json"]:
        raise Reject("replay-retry", "the retry fixture did not regenerate different run-specific bytes")
    outs = {"attach-evidence": r.run_mode(attach2, "attach-evidence", **rt)}
    manifest2 = r.subject_workspace("manifest-2")
    outs["validate-evidence"] = r.run_mode(manifest2, "validate-evidence", **rt)
    outs["build-manifest"] = r.run_mode(manifest2, "build-manifest", **rt)
    publish2 = r.subject_workspace("publish-2")
    outs["load-verifiers"] = r.run_workflow_step(publish2, wf, LOAD_VERIFIERS_STEP, **rt)
    for mode in ("validate-draft", "final-gate", "nightly-gate", "publish-draft"):
        outs[mode] = r.run_mode(publish2, mode, **rt)
    require_ok(outs, "retry")
    after = {n: r.asset_bytes(n) for n in before}
    retry_mutations = [m for m in (c.get("mutation") for c in r.calls()) if m]
    if retry_mutations != ["publish-decision"]:
        raise Reject("replay-retry", f"the retry uploaded or replaced something: {retry_mutations}")
    if after != before or (attach2 / "build/evidence-corpus/cgb-corpus-receipt.json").read_bytes() != before["cgb-corpus-receipt.json"]:
        raise Reject("replay-retry", "the retry did not reuse the identical already-attached bytes")
    if len(r.state()["decisions"]) != 1 or any(c.get("outcome") == "refused" for c in r.calls()):
        raise Reject("replay-retry", "the retry did not end in exactly one recorded decision with no refused call")
    return {"modes": len(MODES) + 1, "publish_decisions": len(state["decisions"]) + len(r.state()["decisions"]), "live_mutations": 0,
            "uploads": sum(1 for u in uploads if u.startswith("upload:")), "calls": len(calls)}


# ------------------------------------------------------------------------------------------------------ controls

class Context:
    """What every control needs: the template, the workflow text and the unmodified lifecycle script."""

    def __init__(self, template: Template, wf: str, script: str, files: dict[str, bytes]) -> None:
        self.t, self.wf, self.script, self.files = template, wf, script, files

    def scenario(self, name: str, stage: str | None = None) -> Scenario:
        s = Scenario(self.t, name, stage)
        s.set_runs()
        return s


def mutate_script(script: str, old: str, new: str) -> str:
    """A disposable copy of the lifecycle with one edit. An anchor that is not there exactly once is an unexercised mutant."""
    if script.count(old) != 1:
        raise Reject("mutant-unexercised", f"the mutation anchor is not present exactly once: {old[:70]!r}")
    return script.replace(old, new)


def build_stages(ctx: Context) -> Scenario:
    """Run the first attempt once and freeze the stub state after the attach, manifest and final-metadata stages."""
    s = ctx.scenario("stages")
    attach = s.attach_workspace("attach")
    require_ok({"attach-evidence": s.run_mode(attach, "attach-evidence")}, "stage attach")
    s.snapshot("attached")
    manifest = s.subject_workspace("manifest")
    require_ok({m: s.run_mode(manifest, m) for m in ("validate-evidence", "build-manifest")}, "stage manifest")
    s.snapshot("manifested")
    publish = s.subject_workspace("publish")
    env = {"RELEASE_ID": str(RELEASE_ID)}
    require_ok({"load-verifiers": s.run_workflow_step(publish, ctx.wf, LOAD_VERIFIERS_STEP, **env),
                "validate-draft": s.run_mode(publish, "validate-draft", **env)}, "stage final metadata")
    s.snapshot("finalized")
    return s


def publish_from(ctx: Context, s: Scenario, name: str = "publish", script: str | None = None) -> Path:
    ws = s.subject_workspace(name, script)
    done = s.run_workflow_step(ws, ctx.wf, LOAD_VERIFIERS_STEP, RELEASE_ID=str(RELEASE_ID))
    require_ok({"load-verifiers": done}, "publish prelude")
    return ws


PUBLISH_ENV = {"RELEASE_ID": str(RELEASE_ID)}
FINAL_GATE_LINE = 'bash trusted/.github/scripts/verify-release-gates.sh --check-draft-final "$RELEASE_ID" "$RELEASE_TAG" "$SOURCE_SHA"'


def c_wrong_repo(ctx: Context) -> str:
    s = ctx.scenario("wrong-repo")
    before = s.asset_names()
    outcome = s.run_mode(s.attach_workspace("a"), "attach-evidence", GH_REPO="other/repository")
    expect_fail(outcome, "wrong GH_REPO", "Evidence attachment runs only from trusted main workflow runs")
    if outcome.calls or s.asset_names() != before:
        raise Reject("control-effect", "a wrong GH_REPO reached the transport or changed the draft")
    return "a wrong GH_REPO is refused before any transport call"


def c_no_fallback(ctx: Context) -> str:
    s = ctx.scenario("no-fallback")
    ws = s.attach_workspace("a")
    env = s.env(ws)
    env.pop("GH_REPO")
    inventory = Path(env["RUNNER_TEMP"]) / "inventory.json"
    inventory.write_text(json.dumps([{"name": "support-ledger.json", "size": 1, "sha256": "0" * 64}]), encoding="utf-8")
    done = subprocess.run(["bash", "trusted/.github/scripts/verify-release-gates.sh", "--check-recovery", str(RELEASE_ID), ctx.t.tag,
                           ctx.t.source, str(inventory), str(s.run_id), "1", "subset"], cwd=ws, env=env, capture_output=True, text=True, timeout=60)
    refused = [c for c in s.calls() if c["argv"][:2] == ["repo", "view"] and c.get("outcome") == "refused"]
    if done.returncode == 0 or "repository identity could not be read" not in done.stderr or len(refused) != 1:
        raise Reject("control-wrong-reason", f"a missing GH_REPO did not stop at the repository identity: {done.stderr.strip()[-200:]}")
    return "a missing GH_REPO stops at the repository identity and the replay refuses the gh repo view fallback"


def c_missing_attach(ctx: Context) -> str:
    s = ctx.scenario("missing-attach")
    outcome = s.run_mode(s.subject_workspace("m"), "validate-evidence")
    expect_fail(outcome, "missing attach", "is absent or empty")
    if s.state()["decisions"] or s.mutations_logged():
        raise Reject("control-effect", "skipping the attach step still changed the release")
    return "skipping the attach step stops the lifecycle at the evidence gate"


def c_missing_gate(ctx: Context) -> str:
    mutated = mutate_script(ctx.script, f"# BEGIN final-gate\n{FINAL_GATE_LINE}\n", "# BEGIN final-gate\ntrue\n")
    for variant, text in (("real", ctx.script), ("mutant", mutated)):
        s = ctx.scenario(f"missing-gate-{variant}", "finalized")
        publish = s.subject_workspace("publish", text)
        # a hostile writer replaces the final receipt after the upload (the row digest follows the replacement)
        receipt = json.loads(s.asset_bytes("release-receipt.json"))
        receipt["source_sha"] = "0" * 40
        s.replace_asset("release-receipt.json", (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode())
        gate = s.run_mode(publish, "final-gate", **PUBLISH_ENV)
        if variant == "real":
            expect_fail(gate, "altered final receipt", "release receipt tag, source SHA, or release ID mismatch")
            if s.state()["decisions"]:
                raise Reject("control-effect", "the production final gate refused but a decision exists")
        else:
            if gate.rc != 0:
                raise Reject("mutant-unexercised", "removing the final gate still failed: the control would not prove the gate")
            # the one-way transition is reached; only the later readback notices, after publication would have happened
            s.run_mode(publish, "publish-draft", **PUBLISH_ENV)
            if len(s.state()["decisions"]) != 1:
                raise Reject("mutant-unexercised", "without the final gate the tampered release did not reach the publish decision")
    return "a removed final gate lets an altered final receipt reach the publish decision; the production gate refuses it first"


def c_advisory_consumers(ctx: Context) -> str:
    s = ctx.scenario("advisory", "finalized")
    perf = json.loads(s.asset_bytes("v02-performance-receipt.json"))
    if perf["regression_disposition"]["release_disposition"] != "advisory" or not perf["measurement"]["summary"]["review_trigger"]:
        raise Reject("fixture-advisory", "the attached receipt is not the triggered advisory receipt")
    digest = sha256_bytes(s.asset_bytes("v02-performance-receipt.json"))
    manifest = json.loads(s.asset_bytes("candidate-platform-manifest.json"))
    receipt = json.loads(s.asset_bytes("release-receipt.json"))
    if (receipt["evidence_sha256"]["v02-performance-receipt.json"] != digest
            or {a["name"]: a["sha256"] for a in manifest["assets"]}["v02-performance-receipt.json"] != digest
            or manifest["performance_receipt"] != "v02-performance-receipt.json"):
        raise Reject("advisory-consumers", "the advisory receipt was not carried through manifest and release receipt")
    return "the triggered advisory performance receipt reaches attach, the manifest and the final receipt"


def c_non_advisory(ctx: Context) -> str:
    s = ctx.scenario("non-advisory")
    bad = json.loads((ctx.t.evidence / "v02-performance-receipt.json").read_text())
    bad["regression_disposition"]["release_disposition"] = "accepted-with-disclosed-regression"
    attach = s.attach_workspace("a", {"v02-performance-receipt.json": (json.dumps(bad, sort_keys=True) + "\n").encode()})
    require_ok({"attach": s.run_mode(attach, "attach-evidence")}, "non-advisory setup")
    outcome = s.run_mode(s.subject_workspace("m"), "validate-evidence")
    expect_fail(outcome, "non-advisory disposition", "advisory-disposition-invalid")
    return "a performance receipt whose disposition is not advisory is refused by the evidence gate"


def c_unexpected_endpoint_in_script(ctx: Context) -> str:
    # a lifecycle that reaches for an endpoint the replay was not told about fails at the transport, not silently
    mutated = mutate_script(ctx.script, "# BEGIN publish-draft\nset -euo pipefail\n",
                            '# BEGIN publish-draft\nset -euo pipefail\ngh api "repos/$GH_REPO/actions/runs" > /dev/null\n')
    s = ctx.scenario("unexpected-endpoint", "finalized")
    publish = publish_from(ctx, s, script=mutated)
    outcome = s.run_mode(publish, "publish-draft", **PUBLISH_ENV)
    if outcome.rc == 0 or "gh-replay-stub: refused: unlisted endpoint" not in outcome.err or s.state()["decisions"]:
        raise Reject("control-wrong-reason", "an unexpected API call did not stop the lifecycle at the transport")
    return "an unexpected API call is refused by the transport and no decision is recorded"


def c_live_publication(ctx: Context) -> str:
    publish_line = 'gh release edit "$RELEASE_TAG" --repo "$GH_REPO" --draft=false --verify-tag'
    mutated = mutate_script(ctx.script, publish_line, publish_line + " --latest")
    s = ctx.scenario("live-publication", "finalized")
    publish = publish_from(ctx, s, "publish", mutated)
    validation = s.run_mode(publish, "validate-draft", **PUBLISH_ENV)
    if validation.rc != 0:
        raise Reject("control-setup", f"the live-publication control's validation setup failed: {validation.text.strip()[-250:]}")
    for mode in ("final-gate", "nightly-gate"):
        gate = s.run_mode(publish, mode, **PUBLISH_ENV)
        if gate.rc != 0:
            raise Reject("control-setup", f"the live-publication control's {mode} setup failed: {gate.text.strip()[-250:]}")
    outcome = s.run_mode(publish, "publish-draft", **PUBLISH_ENV)
    if outcome.rc == 0 or "only as the one publish command" not in outcome.err or s.state()["decisions"] or not s.state()["release"]["draft"]:
        raise Reject("control-wrong-reason", "a publish command other than the intercepted one was not refused")
    return "a publish command other than the intercepted draft transition is refused and the replay release stays a draft"


def control_transport(template: Template) -> list[str]:
    """The transport refuses what it was not told about; each refusal is exit 97 with the intended reason."""
    results: list[str] = []
    s = Scenario(template, "transport")
    stub = s.stub / "gh_stub.py"
    env = {"PATH": os.environ.get("PATH", ""), "GB_STUB_DIR": str(s.stub), "GB_STUB_REPO": REPO}

    def gh(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-I", str(stub), *args], capture_output=True, text=True, env=env, timeout=60)

    def refused(label: str, why: str, *args: str) -> None:
        done = gh(*args)
        if done.returncode != 97 or why not in done.stderr:
            raise Reject("control-transport", f"{label}: wanted refusal {why!r}, got rc={done.returncode} {done.stderr.strip()[:200]!r}")
        results.append(label)

    refused("transport refuses an unlisted endpoint", "unlisted endpoint", "api", f"repos/{REPO}/actions/runs")
    refused("transport refuses another repository", "is not the replay repository", "api", "repos/other/repository/releases?per_page=100")
    refused("transport refuses a query it was not told about", "unlisted endpoint", "api", f"repos/{REPO}/releases?per_page=1")
    refused("transport refuses a mutating api method", "flag or extra argument", "api", f"repos/{REPO}/releases/{RELEASE_ID}", "-X", "DELETE")
    refused("transport refuses a field-posting api call", "flag or extra argument", "api", f"repos/{REPO}/releases/{RELEASE_ID}", "-f", "draft=false")
    refused("transport refuses repository discovery", "unlisted command", "repo", "view", "--json", "nameWithOwner")
    refused("transport refuses release deletion", "unlisted command", "release", "delete", template.tag)
    refused("transport refuses a clobbering upload", "unexpected arguments", "release", "upload", template.tag, "x", "--clobber", "--repo", REPO)
    refused("transport refuses a publish with extra flags", "only as the one publish command", "release", "edit", template.tag,
            "--repo", REPO, "--draft=false", "--verify-tag", "--latest")
    refused("transport refuses an edit that is not the publish command", "only as the one publish command", "release", "edit", template.tag,
            "--repo", REPO, "--notes", "x")
    checks_url = f"repos/{REPO}/commits/{template.pr_head}/check-runs?per_page=100"
    state = s.state()
    state["check_runs"]["check_runs"][0]["repository"] = {"full_name": REPO}
    s.write_state(state)
    refused("transport refuses a check run with an invented repository member", "captured shape", "api", checks_url)
    state["check_runs"]["check_runs"][0].pop("repository")
    state["check_runs"]["check_runs"][0].pop("check_suite")
    s.write_state(state)
    refused("transport refuses a check run without its check_suite", "captured shape", "api", checks_url)
    state = s.state()
    state["pull_request"]["body_padding"] = "x"
    s.write_state(state)
    refused("transport refuses a reshaped pull request", "captured shape", "api", f"repos/{REPO}/pulls/{template.pr_number}")
    state = s.state()
    state["assets"] = [dict(state["asset_template"], id=i, name=f"a{i}") for i in range(101)]
    s.write_state(state)
    refused("transport refuses an oversized asset list", "exceeds 100 items", "api", f"repos/{REPO}/releases/{RELEASE_ID}/assets?per_page=100")
    state["assets"] = [dict(state["asset_template"], name="x" * (1024 * 1024))]
    s.write_state(state)
    refused("transport refuses an oversized response", "-byte bound", "api", f"repos/{REPO}/releases/{RELEASE_ID}/assets?per_page=100")
    stub_dl = s.root / "dl.py"
    stub_dl.write_text(DOWNLOAD_STUB, encoding="utf-8")
    for label, url, extra in (
            ("archive transport refuses another repository", "https://github.com/other/repository/archive/refs/tags/v0.2.0.tar.gz", ["--max-bytes", "1", "--total-timeout", "1"]),
            ("archive transport refuses a non-tag URL", f"https://github.com/{REPO}/archive/refs/heads/main.tar.gz", ["--max-bytes", "1", "--total-timeout", "1"]),
            ("archive transport refuses an unbounded download", f"https://github.com/{REPO}/archive/refs/tags/v0.2.0.tar.gz", [])):
        done = subprocess.run([sys.executable, "-I", str(stub_dl), url, str(s.root / "a.tgz"), *extra], capture_output=True, text=True, env=env, timeout=60)
        if done.returncode != 97:
            raise Reject("control-transport", f"{label}: rc={done.returncode}")
        results.append(label)
    return results


def c_wiring(ctx: Context) -> str:
    check_wiring(ctx.wf, ctx.script)
    cases = (
        ("the workflow stops calling the publish mode", ctx.wf.replace("release-evidence-lifecycle.sh publish-draft", "true"), ctx.script, "lifecycle-unwired"),
        ("the workflow runs the lifecycle from the tagged checkout", ctx.wf.replace(
            "run: bash trusted/.github/scripts/release-evidence-lifecycle.sh attach-evidence",
            "run: bash .github/scripts/release-evidence-lifecycle.sh attach-evidence"), ctx.script, "lifecycle-unwired"),
        ("the workflow calls one mode from another job", ctx.wf.replace(
            "release-evidence-lifecycle.sh validate-evidence", "release-evidence-lifecycle.sh attach-evidence"), ctx.script, "lifecycle-unwired"),
        ("the lifecycle script is absent", ctx.wf, None, "lifecycle-missing"),
    )
    for label, workflow, script, code in cases:
        try:
            check_wiring(workflow, script)
        except Reject as error:
            if error.code != code:
                raise Reject("control-wrong-reason", f"{label}: {error}") from error
        else:
            raise Reject("control-accepted", f"{label}: the wiring check accepted it")
    return "the wiring check rejects an uncalled mode, a tagged-checkout call, a cross-job call and an absent script"


def _normalize_endpoint_path(path: str) -> str:
    return re.sub(r"\$\{[^}]*\}|\$[A-Za-z_][A-Za-z0-9_]*|\$[0-9]+", "{}", path)


def _gh_forms(source: str) -> set[str]:
    forms = set()
    api_call = re.compile(r"\bgh\s+api\s+(?:\"([^\"]+)\"|'([^']+)'|(\S+))")
    for match in api_call.finditer(source):
        endpoint = next(value for value in match.groups() if value is not None)
        forms.add("gh api " + _normalize_endpoint_path(endpoint))
    for match in re.finditer(r"\bgh\s+(run|release|pr)\s+(list|view|download|checks|upload|edit)\b", source):
        forms.add(f"gh {match.group(1)} {match.group(2)}")
    if ('gh run download "$run_id"' in source and
            '--name "perf-gate-$run_id-$attempt"' in source):
        forms.add("gh run download {} --name perf-gate-{}-{}")
    return forms


def _workflow_run_blocks(source: str) -> list[str]:
    """Return commands from every YAML `run:` scalar, keeping embedded shell as source data."""
    lines = source.splitlines()
    blocks = []
    index = 0
    while index < len(lines):
        match = re.match(r"^(?P<indent>\s*)run:\s*(?P<value>.*)$", lines[index])
        if not match:
            index += 1
            continue
        indent = len(match.group("indent"))
        value = match.group("value").strip()
        if value.startswith(("|", ">")):
            content = []
            index += 1
            while index < len(lines):
                line = lines[index]
                if line.strip() and len(line) - len(line.lstrip()) <= indent:
                    break
                content.append(line)
                index += 1
            blocks.append("\n".join(content))
            continue
        blocks.append(value)
        index += 1
    return blocks


def _inventory_from_source(source: str) -> tuple[dict, ...]:
    names = {"LIFECYCLE": LIFECYCLE, "WORKFLOW": WORKFLOW, "SOURCES": SOURCES}

    def literal(item):
        if isinstance(item, ast.Constant):
            return item.value
        if isinstance(item, ast.Name) and item.id in names:
            return names[item.id]
        if isinstance(item, ast.Tuple):
            return tuple(literal(child) for child in item.elts)
        if isinstance(item, ast.List):
            return [literal(child) for child in item.elts]
        if isinstance(item, ast.Dict):
            return {literal(key): literal(value) for key, value in zip(item.keys, item.values)}
        raise ValueError(f"unsupported inventory expression {type(item).__name__}")

    try:
        tree = ast.parse(source)
        node = next(item for item in tree.body if isinstance(item, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == "POST_TAG_ENDPOINTS" for target in item.targets))
        value = literal(node.value)
    except (SyntaxError, StopIteration, ValueError) as error:
        raise Reject("endpoint-uncovered", f"POST_TAG_ENDPOINTS is not an immutable literal inventory: {error}") from error
    if not isinstance(value, tuple) or not all(isinstance(item, dict) for item in value):
        raise Reject("endpoint-uncovered", "POST_TAG_ENDPOINTS must be a tuple of endpoint records")
    return value


def check_endpoint_inventory(files: dict[str, bytes], required_paths: dict = REQUIRED_PATHS,
                             response_keys: tuple = RESPONSE_KEYS) -> int:
    """Audit command forms from immutable lifecycle/judge/workflow files against the committed inventory."""
    inventory = _inventory_from_source(files[SELF].decode("utf-8"))
    policy = files[POLICY].decode("utf-8")
    self_source = files[SELF].decode("utf-8")
    by_form = {}
    for entry in inventory:
        if not all(key in entry for key in ("form", "sources", "consumer", "coverage")):
            raise Reject("endpoint-uncovered", "an endpoint entry lacks form, sources, consumer or coverage")
        if entry["form"] in by_form:
            raise Reject("endpoint-uncovered", f"POST_TAG_ENDPOINTS repeats {entry['form']}")
        by_form[entry["form"]] = entry

    observed: dict[str, set[str]] = {}
    for relative in JUDGE_FILES:
        observed[relative] = _gh_forms(files[relative].decode("utf-8"))
    for block in _workflow_run_blocks(files[WORKFLOW].decode("utf-8")):
        observed.setdefault(WORKFLOW, set()).update(_gh_forms(block))

    for relative, forms in observed.items():
        for form in forms:
            entry = by_form.get(form)
            if entry is None:
                raise Reject("endpoint-uncovered", f"{relative} uses unlisted form {form}")
            if relative not in entry["sources"]:
                raise Reject("endpoint-uncovered", f"{form} omits source file {relative}")

    for entry in inventory:
        form, coverage = entry["form"], entry["coverage"]
        if coverage.startswith("replayed:"):
            key = coverage.split(":", 1)[1]
            paths = required_paths.get(key)
            if key not in response_keys or not paths:
                raise Reject("endpoint-uncovered", f"{form} replay key {key!r} has no REQUIRED_PATHS contract")
            route = entry.get("route")
            route_marker = route.replace("\\", "\\\\") if isinstance(route, str) else ""
            if not route_marker or route_marker not in self_source:
                raise Reject("endpoint-uncovered", f"{form} replay key {key!r} has no immutable transport route")
        elif coverage.startswith("pinned:"):
            rule = coverage.split(":", 1)[1]
            if not re.search(rf"(?m)^def {re.escape(rule)}\s*\(", policy):
                raise Reject("endpoint-uncovered", f"{form} names missing workflow policy rule {rule}")
        else:
            raise Reject("endpoint-uncovered", f"{form} has unknown coverage {coverage!r}")
    return len(inventory)


def c_endpoint_inventory(ctx: Context) -> str:
    count = check_endpoint_inventory(ctx.files)
    cases = []

    route_scenario = Scenario(ctx.t, "ci-run-capture-route")
    stub = route_scenario.stub / "gh_stub.py"
    env = {"PATH": os.environ.get("PATH", ""), "GB_STUB_DIR": str(route_scenario.stub), "GB_STUB_REPO": REPO}
    route = subprocess.run([sys.executable, "-I", str(stub), "api",
                            f"repos/{REPO}/actions/runs/40259198255"], capture_output=True, text=True, env=env, timeout=60)
    if route.returncode != 0:
        raise Reject("endpoint-route", f"the ci_run capture route refused its published run: {route.stderr.strip()[:200]}")
    try:
        ci_run = json.loads(route.stdout)
    except json.JSONDecodeError as error:
        raise Reject("endpoint-route", "the ci_run capture route did not return JSON") from error
    if (ci_run.get("id") != 40259198255 or ci_run.get("path") != ".github/workflows/ci.yml"
            or ci_run.get("event") != "push" or ci_run.get("head_sha") != ctx.t.source):
        raise Reject("endpoint-route", "the ci_run route did not serve the exact-source v0.2.1 CI push run")
    refused = subprocess.run([sys.executable, "-I", str(stub), "api",
                              f"repos/{REPO}/actions/runs/40259198254"], capture_output=True, text=True, env=env, timeout=60)
    if refused.returncode != 1 or "HTTP 404" not in refused.stderr:
        raise Reject("endpoint-route", "the ci_run route accepted a run id outside its captured fixture")

    mutated = dict(ctx.files)
    lifecycle = ctx.script.replace("# BEGIN publish-draft\n", '# BEGIN publish-draft\ngh api "repos/$GH_REPO/unlisted/lifecycle" >/dev/null\n', 1)
    mutated[LIFECYCLE] = lifecycle.encode("utf-8")
    cases.append(("an unrouted lifecycle API endpoint", mutated, REQUIRED_PATHS))

    mutated = dict(ctx.files)
    workflow = ctx.wf
    run_header = re.search(r"(?m)^(?P<indent>\s*)run:\s*\|\s*$", workflow)
    if run_header is None:
        raise Reject("control-setup", "release.yml has no block-style run step to seed")
    insertion = run_header.group(0) + "\n" + run_header.group("indent") + '  gh api "repos/$GH_REPO/unlisted/workflow"'
    mutated[WORKFLOW] = (workflow[:run_header.start()] + insertion + workflow[run_header.end():]).encode("utf-8")
    cases.append(("an unlisted API endpoint in a release.yml run block", mutated, REQUIRED_PATHS))

    missing_paths = dict(REQUIRED_PATHS)
    missing_paths.pop("attempt_jobs")
    cases.append(("a replay entry without REQUIRED_PATHS", ctx.files, missing_paths))

    for label, files, paths in cases:
        try:
            check_endpoint_inventory(files, paths)
        except Reject as error:
            if error.code != "endpoint-uncovered":
                raise Reject("control-wrong-reason", f"{label}: {error}") from error
        else:
            raise Reject("control-accepted", f"{label}: endpoint inventory accepted it")
    return f"endpoint inventory covers {count} forms and rejects an unlisted lifecycle endpoint, a run-block endpoint, and missing REQUIRED_PATHS"


def c_perf_receipt_ci_run(ctx: Context) -> str:
    """Generate against the captured source and prove ci_run passes while the neighboring release-please run fails."""
    ci_run = ctx.t.capture["responses"]["ci_run"]
    release_run = ctx.t.capture["responses"]["workflow_run"]
    source = ci_run["head_sha"]
    if (ci_run.get("id") != 40259198255 or ci_run.get("run_attempt") != 1
            or source != PERF_SOURCE_REV or ci_run.get("path") != ".github/workflows/ci.yml"):
        raise Reject("perf-receipt-capture", "the immutable ci_run fixture no longer matches the declared exact-source campaign")
    with tempfile.TemporaryDirectory(prefix="perf-receipt-ci-run-") as scratch:
        receipt = Path(scratch) / "receipt.json"
        ci_path = Path(scratch) / "ci-run.json"
        release_path = Path(scratch) / "release-run.json"
        ci_path.write_text(json.dumps(ci_run, sort_keys=True), encoding="utf-8", newline="\n")
        release_path.write_text(json.dumps(release_run, sort_keys=True), encoding="utf-8", newline="\n")
        env = os.environ.copy()
        env.update(GITHUB_RUN_ID=str(ci_run["id"]), GITHUB_RUN_ATTEMPT=str(ci_run["run_attempt"]))
        generated = subprocess.run([sys.executable, "-I", str(ROOT / "tests/scripts/verify-perf-gate.py"), "--evaluate",
                                     "--limits", "tests/baseline/perf-gate-v1.txt",
                                     "--base", "tests/data/perf-gate/base", "--head", "tests/data/perf-gate/head-pass",
                                     "--realtime", "tests/data/perf-gate/realtime-pass.txt", "--base-rev", PERF_LIMITS_BASE_REV,
                                     "--source-head-rev", source, "--build-base-identity", "a" * 64,
                                     "--build-head-identity", "b" * 64, "--emit-receipt", str(receipt)],
                                    cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
        if generated.returncode != 0 or not receipt.is_file():
            raise Reject("perf-receipt-fixture", f"the captured ci_run receipt could not be generated: {generated.stderr.strip()[-250:]}")
        command = [sys.executable, "-I", str(ROOT / "tests/scripts/verify-perf-gate.py"), "--verify-receipt",
                   str(receipt), "--source-sha", source, "--run-json", str(ci_path), "--run-id", str(ci_run["id"]),
                   "--attempt", str(ci_run["run_attempt"]), "--repo", str(ROOT)]
        positive = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
        if positive.returncode != 0:
            raise Reject("perf-receipt-capture", f"the captured ci_run did not verify: {positive.stderr.strip()[-250:]}")
        release_command = command.copy()
        release_command[release_command.index(str(ci_path))] = str(release_path)
        rejected = subprocess.run(release_command, cwd=ROOT, capture_output=True, text=True, timeout=60)
        if rejected.returncode != 1 or "REJECT perf-receipt-run" not in rejected.stderr:
            raise Reject("perf-receipt-capture", "the same receipt did not reject the captured release-please run with perf-receipt-run")
    return "the immutable ci_run response verifies the receipt; the captured release-please workflow response is rejected"


def c_perf_receipt_tamper(ctx: Context) -> str:
    s = ctx.scenario("perf-receipt-tamper", "finalized")
    ws = publish_from(ctx, s, "publish")
    path = ws / "build/evidence-fuzz/perf-gate/perf-gate-receipt.json"
    receipt = json.loads(path.read_text(encoding="utf-8"))
    receipt["run_id"] += 1
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    before = s.asset_names()
    outcome = s.run_mode(ws, "validate-draft", **PUBLISH_ENV)
    expect_fail(outcome, "tampered perf-gate receipt run id", "perf-receipt-run")
    if s.asset_names() != before or s.mutations_logged():
        raise Reject("control-effect", "a tampered perf-gate receipt changed the draft before refusal")
    return "the trusted draft validator rejects a receipt bound to another CI run without writing"


def c_profile_string(ctx: Context) -> str:
    s = ctx.scenario("profile-string", "finalized")
    receipt = json.loads(s.asset_bytes("release-receipt.json"))
    expected = f"{ctx.t.tag} deterministic software profiles DMG-CPU-B and CGB-CPU-E as scoped by docs/support/{ctx.t.tag}.md"
    if receipt.get("limits", [None])[0] != expected:
        raise Reject("profile-string", "the release receipt does not carry the exact version-aware DMG and CGB profile contract")
    mutant = json.loads(json.dumps(receipt))
    mutant["limits"][0] = "DMG-CPU-B deterministic software profile only"
    if mutant["limits"][0] == expected:
        raise Reject("profile-string-control", "the profile assertion accepted the old single-profile contract")
    return "the receipt carries both version-scoped profiles, and the former single-profile text fails the contract"


def c_pre_publish_inventory(ctx: Context) -> str:
    real = ctx.scenario("inventory-write-present", "finalized")
    workspace = real.subject_workspace("publish")
    outcome = real.run_mode(workspace, "final-gate", **PUBLISH_ENV)
    if outcome.rc != 0:
        raise Reject("inventory-control", f"the real final gate failed: {outcome.text.strip()[-200:]}")
    inventory = workspace / "build/release-final/pre-publish-inventory.json"
    if not inventory.is_file():
        raise Reject("inventory-control", "the real final gate omitted its persisted asset inventory")
    mutant_text = mutate_script(ctx.script,
        'path.write_text(json.dumps(inventory, sort_keys=True, indent=2) + "\\n", encoding="utf-8", newline="\\n")\n',
        'pass # omitted pre-publish inventory write\n')
    mutant = ctx.scenario("inventory-write-omitted", "finalized")
    mutant_workspace = mutant.subject_workspace("publish", mutant_text)
    omitted = mutant.run_mode(mutant_workspace, "final-gate", **PUBLISH_ENV)
    if omitted.rc != 0 or (mutant_workspace / "build/release-final/pre-publish-inventory.json").exists():
        raise Reject("inventory-control", "the omitted-write mutant did not leave the required inventory absent")

    def remove_qualified_archive(scenario: Scenario, workspace: Path) -> str:
        inventory_doc = json.loads((workspace / "build/release-final/pre-publish-inventory.json").read_text(encoding="utf-8"))
        name = next((row["name"] for row in inventory_doc["assets"] if row["name"] not in FINAL_NAMES), None)
        if name is None:
            raise Reject("inventory-control", "the final-gate fixture has no qualified archive to mutate")
        scenario.remove_asset(name)
        return name

    def prepare_publish(scenario: Scenario, script: str | None = None) -> Path:
        workspace = publish_from(ctx, scenario, "publish", script)
        validation = scenario.run_mode(workspace, "validate-draft", **PUBLISH_ENV)
        if validation.rc != 0:
            raise Reject("inventory-control", f"the publication fixture could not validate its draft: {validation.text.strip()[-250:]}")
        return workspace

    positive = ctx.scenario("publish-inventory-guard-positive", "finalized")
    positive_workspace = prepare_publish(positive)
    for mode in ("final-gate", "nightly-gate"):
        result = positive.run_mode(positive_workspace, mode, **PUBLISH_ENV)
        if result.rc != 0:
            raise Reject("inventory-control", f"the positive {mode} gate failed: {result.text.strip()[-250:]}")
    published = positive.run_mode(positive_workspace, "publish-draft", **PUBLISH_ENV)
    if published.rc != 0 or positive.state()["release"]["draft"] is not False \
            or len(positive.state()["decisions"]) != 1:
        raise Reject("inventory-control", f"the identical final-gate inventory did not publish exactly once: {published.text.strip()[-250:]}")

    guarded = ctx.scenario("publish-inventory-guard", "finalized")
    guarded_workspace = prepare_publish(guarded)
    for mode in ("final-gate", "nightly-gate"):
        result = guarded.run_mode(guarded_workspace, mode, **PUBLISH_ENV)
        if result.rc != 0:
            raise Reject("inventory-control", f"the production {mode} gate failed: {result.text.strip()[-250:]}")
    removed = remove_qualified_archive(guarded, guarded_workspace)
    refused = guarded.run_mode(guarded_workspace, "publish-draft", **PUBLISH_ENV)
    if refused.rc == 0 or "REJECT published-assets:" not in refused.text \
            or guarded.state()["release"]["draft"] is not True or guarded.state()["decisions"]:
        raise Reject("inventory-control", f"the live inventory mutation {removed} was not refused before publication")

    guard_line = 'python3 -I trusted/.github/scripts/verify-published-release-assets.py --verify-pre-publish "$assets" build/release-final/pre-publish-inventory.json "$RELEASE_TAG" "$SOURCE_SHA" "$RELEASE_ID" "$GITHUB_RUN_ID" "$GITHUB_RUN_ATTEMPT"\n'
    mutant_text = mutate_script(ctx.script, guard_line, "")
    unguarded = ctx.scenario("publish-inventory-guard-omitted", "finalized")
    unguarded_workspace = prepare_publish(unguarded, mutant_text)
    for mode in ("final-gate", "nightly-gate"):
        result = unguarded.run_mode(unguarded_workspace, mode, **PUBLISH_ENV)
        if result.rc != 0:
            raise Reject("inventory-control", f"the mutant production {mode} gate failed: {result.text.strip()[-250:]}")
    remove_qualified_archive(unguarded, unguarded_workspace)
    mutant_result = unguarded.run_mode(unguarded_workspace, "publish-draft", **PUBLISH_ENV)
    if mutant_result.rc == 0 or unguarded.state()["release"]["draft"] is not False \
            or len(unguarded.state()["decisions"]) != 1 or "REJECT published-assets:" not in mutant_result.text:
        raise Reject("inventory-control", "the missing-guard mutant did not demonstrate publication before its post-publish refusal")
    return "the final gate persists the frozen inventory, and the live pre-publish comparison refuses removal before the one-way transition"


# ----------------------------------------------------------------------------------------- Task 2: captured shapes

def sources_with_digest(sources: str, text: bytes) -> str:
    return SOURCES_DIGEST.sub(f"- captured.json sha256: {sha256_bytes(text)}", sources)


def expect_capture_reject(label: str, text: bytes, sources: str, code: str) -> None:
    try:
        check_capture(text, sources)
    except Reject as error:
        if error.code != code:
            raise Reject("control-wrong-reason", f"{label}: wanted {code}, got {error}") from error
        return
    raise Reject("control-accepted", f"{label}: the capture check accepted it")


def c_capture_contract(ctx: Context) -> str:
    text, sources = ctx.files[CAPTURE], ctx.files[SOURCES].decode("utf-8")
    check_capture(text, sources)  # positive first: the committed capture is accepted before any defect is credited
    base = json.loads(text.decode("utf-8"))
    count = 0

    def mutated(label: str, code: str, change, resign: bool = True) -> None:
        nonlocal count
        value = copy.deepcopy(base)
        change(value)
        new = capture_text(value).encode("utf-8")
        expect_capture_reject(label, new, sources_with_digest(sources, new) if resign else sources, code)
        count += 1

    first_run = lambda v: v["responses"]["check_runs"]["check_runs"][0]
    mutated("a stale SOURCES digest", "capture-digest", lambda v: v["responses"]["commit"].update(sha="0" * 40), resign=False)
    mutated("an email address left in the capture", "capture-sanitization", lambda v: v["responses"]["commit"].update(note="someone@example.com"))
    mutated("a local path left in the capture", "capture-sanitization", lambda v: v["responses"]["commit"].update(note="/Users/example/work"))
    mutated("a credential left in the capture", "capture-sanitization", lambda v: v["responses"]["commit"].update(note="ghp_" + "a" * 36))
    mutated("an invented repository member on a check run", "capture-schema", lambda v: first_run(v).update(repository={"full_name": REPO}))
    mutated("a check run without its check_suite", "capture-schema", lambda v: first_run(v).pop("check_suite"))
    mutated("a check run without its html_url", "capture-schema", lambda v: first_run(v).pop("html_url"))
    mutated("a pull request without its merge commit", "capture-schema", lambda v: v["responses"]["pull_request"].pop("merge_commit_sha"))
    mutated("a commit pull listing without merged_at", "capture-schema", lambda v: v["responses"]["pull_requests"][0].pop("merged_at"))
    mutated("an attempt job without completed_at", "capture-schema", lambda v: v["responses"]["attempt_jobs"]["jobs"][0].pop("completed_at"))
    mutated("a CI run without its path", "capture-schema", lambda v: v["responses"]["ci_run"].pop("path"))
    mutated("a release asset without its digest", "capture-schema", lambda v: v["responses"]["release_assets"][0].pop("digest"))
    mutated("an undeclared response", "capture-schema", lambda v: v["responses"].update(extra={}))
    mutated("a missing response", "capture-schema", lambda v: v["responses"].pop("artifacts"))
    mutated("another API version", "capture-schema", lambda v: v.update(api_version="2024-01-01"))
    mutated("another repository", "capture-schema", lambda v: v.update(repository="other/repository"))
    mutated("a capture without its source identity", "capture-schema", lambda v: v["identity"].update(source_sha="x"))
    crlf = text.replace(b"\n", b"\r\n")
    expect_capture_reject("CRLF line endings", crlf, sources_with_digest(sources, crlf), "capture-eol")
    oversize = text + b" " * MAX_CAPTURE_BYTES
    expect_capture_reject("an oversized capture", oversize, sources_with_digest(sources, oversize), "capture-oversize")
    broken = b"{" + text
    expect_capture_reject("invalid JSON", broken, sources_with_digest(sources, broken), "capture-json")
    for section in ("Provenance", "Sanitization", "Endpoints", "API version"):
        expect_capture_reject(f"SOURCES.md without its {section} section", text, sources.replace(f"## {section}\n", f"## {section} removed\n"),
                              "capture-provenance")
    expect_capture_reject("SOURCES.md without a digest line", text, SOURCES_DIGEST.sub("", sources), "capture-digest")
    return f"the capture contract rejects {count + 3 + 4 + 1} provenance, sanitization, bound and schema defects"


def c_sanitizer(ctx: Context) -> str:
    raw = {
        "body": "private release notes", "patch": "@@ -1 +1 @@ secret", "signature": "sig", "payload": "payload with a@b.example",
        "author": {"name": "Jane Doe", "email": "jane@example.com", "date": "2026-01-01T00:00:00Z"},
        "user": {"login": "jane-doe", "id": 77, "node_id": "U_77", "avatar_url": "https://avatars.githubusercontent.com/u/77?v=4",
                 "url": "https://api.github.com/users/jane-doe", "type": "User"},
        "owner": {"login": "szTheory", "id": 5, "node_id": "U_5", "avatar_url": "https://avatars.githubusercontent.com/u/5?v=4"},
        "bot": {"login": "github-actions[bot]", "id": 41898282, "node_id": "BOT", "avatar_url": "https://avatars.githubusercontent.com/in/15368"},
        "runner_name": "GitHub Actions 1000199669", "runner_id": 1000199669,
        "message": "m" * 500 + " contact jane@example.com", "assets": [{"n": i} for i in range(9)],
    }
    out = sanitize(raw, "", {})
    text = json.dumps(out)
    checks = (
        ("release/PR body text", "private release notes" not in text and out["body"] == OMITTED),
        ("commit patch, signature and payload", "secret" not in text and out["patch"] == OMITTED and out["signature"] == OMITTED and "a@b.example" not in text),
        ("git author name and email", out["author"]["name"] == "Sanitized Author" and "jane@example.com" not in text and "Jane" not in text),
        ("a human user object", out["user"]["login"] == "sanitized-user" and "jane-doe" not in text and set(out["user"]) == set(raw["user"])),
        ("the repository owner and bot accounts are kept", out["owner"]["login"] == "szTheory" and out["bot"]["login"] == "github-actions[bot]"),
        ("runner identifiers", out["runner_name"] == "GitHub Actions" and out["runner_id"] == 0),
        ("long messages", len(out["message"]) < 240 and "jane@example.com" not in out["message"]),
        ("array bounds", len(out["assets"]) == TRUNCATE_ARRAYS["assets"]),
        ("every email-shaped string", all(m == REDACTED_EMAIL for m in EMAIL.findall(text))),
    )
    for label, ok in checks:
        if not ok:
            raise Reject("sanitizer", f"the sanitizer did not apply its documented rule for {label}")
    return f"the sanitizer applies each of its {len(checks)} documented rules"


def merged_source(ctx: Context, s: Scenario, ws: Path) -> Outcome:
    receipt = ws / "build/release-final"
    receipt.mkdir(parents=True, exist_ok=True)
    (receipt / "source-receipt.json").write_bytes(s.asset_bytes("source-receipt.json"))
    return s.run_gate(ws, "--check-merged-source", ctx.t.source, ctx.t.tag, str(RELEASE_ID), "build/release-final/source-receipt.json",
                      str(Path(s.env(ws)["RUNNER_TEMP"]) / "verify-release-source-proof.py"), **PUBLISH_ENV)


def source_proof_control(ctx: Context, label: str, needle: str, change, shapes_off: bool = False) -> str:
    s = ctx.scenario("proof-" + label, "manifested")
    state = s.state()
    change(state)
    if shapes_off:
        # The transport's shape pin would refuse these reshaped payloads before the production consumer saw them. Pinning
        # is switched off for this scenario only, so the production consumer is the one that judges the old shape.
        state["shapes"].pop("check_runs", None)
        state["shapes"].pop("pull_request", None)
    s.write_state(state)
    ws = publish_from(ctx, s)
    outcome = merged_source(ctx, s, ws)
    expect_fail(outcome, label, needle)
    if not any(c.get("kind") == "check_runs" for c in outcome.calls):
        raise Reject("control-unexercised", f"{label}: the production gate never read the check runs")
    return f"source proof: {label}"


def required_run(state: dict, index: int = 0) -> dict:
    names = {"required-native", "fixture-repro", "preview-package-smoke"}
    return [r for r in state["check_runs"]["check_runs"] if r["name"] in names][index]


SOURCE_PROOF_CASES = (
    ("a stale check head", "stale check evidence", lambda st: required_run(st).update(head_sha="0" * 40), False),
    ("a check run of another App id", "wrong GitHub App", lambda st: required_run(st)["app"].update(id=1), False),
    ("a check run of another App slug", "wrong GitHub App", lambda st: required_run(st)["app"].update(slug="other-app"), False),
    ("a check run url of another repository", "wrong repository",
     lambda st: required_run(st).update(url=required_run(st)["url"].replace(REPO, "other/repository")), False),
    ("a check run url with a lookalike repository prefix", "wrong repository",
     lambda st: required_run(st).update(url=required_run(st)["url"].replace(REPO + "/", REPO + "-evil/")), False),
    ("a check run html_url of another repository", "wrong repository",
     lambda st: required_run(st).update(html_url=required_run(st)["html_url"].replace(REPO, "other/repository")), False),
    ("a check run without its check_suite", "wrong repository", lambda st: required_run(st).pop("check_suite"), True),
    ("the old repository-only check run shape", "wrong repository",
     lambda st: (required_run(st).pop("url"), required_run(st).pop("html_url"), required_run(st).update(repository={"full_name": REPO})), True),
    ("a required context without evidence", "has no exact-head check-run evidence",
     lambda st: st["check_runs"].update(check_runs=[r for r in st["check_runs"]["check_runs"] if r["name"] != "fixture-repro"]), False),
    ("a failed required context", "incomplete or unsuccessful", lambda st: required_run(st).update(conclusion="failure"), False),
    ("a mixed duplicate of a required context", "incomplete or unsuccessful",
     lambda st: st["check_runs"]["check_runs"].append({**required_run(st), "conclusion": "failure"}), False),
    ("a pull request merged to another source", "live pull request does not match", lambda st: st["pull_request"].update(merge_commit_sha="0" * 40), False),
    ("a pull request of another base repository", "live pull request does not match",
     lambda st: st["pull_request"]["base"]["repo"].update(full_name="other/repository"), False),
)


def draft_gate(ctx: Context, s: Scenario) -> Outcome:
    ws = s.subject_workspace("draft")
    return s.run_gate(ws, "--check-draft", str(RELEASE_ID), ctx.t.tag, ctx.t.source, **PUBLISH_ENV)


def draft_control(ctx: Context, label: str, needle: str, change) -> str:
    s = ctx.scenario("draft-" + label, "manifested")
    change(s)
    outcome = draft_gate(ctx, s)
    expect_fail(outcome, label, needle)
    return f"draft asset set: {label}"


def _bytes_flip(s: Scenario, name: str, keep_digest: bool) -> None:
    s.replace_asset(name, s.asset_bytes(name) + b"altered\n", keep_digest=keep_digest)


def _receipt_edit(s: Scenario, name: str, **changes) -> None:
    value = json.loads(s.asset_bytes(name))
    value.update(changes)
    s.replace_asset(name, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


def _duplicate_row(s: Scenario, name: str) -> None:
    state = s.state()
    row = next(r for r in state["assets"] if r["name"] == name)
    state["assets"].append({**row, "id": row["id"] + 1000})
    s.write_state(state)


def _extra_asset(s: Scenario) -> None:
    s.add_asset("unknown-extra-asset.bin", b"not part of the qualified set\n")


def _tag_moves(s: Scenario) -> None:
    state = s.state()
    state["commits"][s.t.tag] = {**state["commits"][s.t.tag], "sha": "0" * 40}
    s.write_state(state)


def _published(s: Scenario) -> None:
    state = s.state()
    state["release"]["draft"] = False
    s.write_state(state)


DRAFT_CASES = (
    ("attached bytes that differ from the API digest", "GitHub API digest differs from downloaded bytes", lambda s: _bytes_flip(s, "gabbaboy-notices.txt", True)),
    ("replaced bytes with a recomputed digest", "platform manifest does not bind downloaded bytes", lambda s: _bytes_flip(s, "gabbaboy-core-linux-x64.tar.gz", False)),
    ("a candidate receipt of another source", "has mismatched source_sha", lambda s: _receipt_edit(s, "candidate-receipt.json", source_sha="0" * 40)),
    ("a source receipt of another release id", "has mismatched release_id", lambda s: _receipt_edit(s, "source-receipt.json", release_id="1")),
    ("a source receipt of another tag", "has mismatched tag_name", lambda s: _receipt_edit(s, "source-receipt.json", tag_name="v9.9.9")),
    ("a support sidecar of another tag", "support sidecar is not bound to the exact tag/source",
     lambda s: _receipt_edit(s, "support-ledger.json", tag="v9.9.9")),
    ("a platform manifest of another source", "platform manifest source SHA differs from candidate",
     lambda s: _receipt_edit(s, "candidate-platform-manifest.json", source_sha="0" * 40)),
    ("a platform manifest entry that no longer matches its asset", "platform manifest does not bind downloaded bytes",
     lambda s: _receipt_edit(s, "candidate-platform-manifest.json", assets=[{"name": "gabbaboy-notices.txt", "sha256": "0" * 64}])),
    ("a partial asset set", "draft asset inventory differs", lambda s: s.remove_asset("gabbaboy-notices.txt")),
    ("a duplicated asset name", "draft asset inventory differs", lambda s: _duplicate_row(s, "gabbaboy-notices.txt")),
    ("an unknown extra asset", "draft asset inventory differs", _extra_asset),
    ("a tag that moved off the frozen source", "release tag target differs from the frozen source SHA", _tag_moves),
    ("a release that is already published", "release is already published", _published),
)


def recovery_control(ctx: Context, label: str, needle: str, change) -> str:
    s = ctx.scenario("recovery-" + label, "manifested")
    change(s)
    ws = publish_from(ctx, s)
    outcome = s.run_mode(ws, "validate-draft", **PUBLISH_ENV)
    expect_fail(outcome, label, needle)
    return f"recovery decision: {label}"


def _runs(s: Scenario, rows) -> None:
    state = s.state()
    own = next(r for r in state["runs"] if r["id"] == s.run_id)
    state["runs"] = rows(state, own)
    s.write_state(state)


RECOVERY_CASES = (
    ("this run absent from the live run list", "not in the live release workflow run list", lambda s: _runs(s, lambda st, own: [r for r in st["runs"] if r["id"] != own["id"]])),
    ("a later attempt of this run", "stale", lambda s: _runs(s, lambda st, own: [{**own, "run_attempt": own["run_attempt"] + 1}] + [r for r in st["runs"] if r["id"] != own["id"]])),
    ("a concurrent unfinished run of the same source", "concurrent publication attempt",
     lambda s: _runs(s, lambda st, own: [own, {**own, "id": own["id"] + 7, "status": "in_progress", "head_sha": s.t.source, "event": "push"}] + [r for r in st["runs"] if r["id"] != own["id"]])),
    ("a concurrent manual retry dispatch", "concurrent publication attempt",
     lambda s: _runs(s, lambda st, own: [own, {**own, "id": own["id"] + 7, "status": "queued", "head_sha": "e" * 40, "event": "workflow_dispatch"}] + [r for r in st["runs"] if r["id"] != own["id"]])),
)


def rewrite_sums(s: Scenario, change) -> None:
    """A hostile writer that rewrites SHA256SUMS and the receipt that binds it, so only the strict parse can object."""
    sums = change(s.asset_bytes("SHA256SUMS").decode("utf-8")).encode("utf-8")
    s.replace_asset("SHA256SUMS", sums)
    receipt = json.loads(s.asset_bytes("release-receipt.json"))
    receipt["sha256sums_sha256"] = sha256_bytes(sums)
    s.replace_asset("release-receipt.json", (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode())


def sums_control(ctx: Context, label: str, needle: str, change) -> str:
    s = ctx.scenario("sums-" + label, "finalized")
    ws = s.subject_workspace("publish")  # the final gate reads the live draft itself; it needs only the tag checkout and trusted/
    rewrite_sums(s, change)
    outcome = s.run_mode(ws, "final-gate", **PUBLISH_ENV)
    expect_fail(outcome, label, needle)
    if s.state()["decisions"]:
        raise Reject("control-effect", f"{label}: a decision was recorded")
    return f"final receipt: {label}"


SUMS_CASES = (
    ("a name listed twice", "more than once", lambda text: text + text.splitlines(keepends=True)[0]),
    ("a line with one space", "malformed or path-like line", lambda text: text.replace("  ", " ", 1)),
    ("a path-like name", "malformed or path-like line", lambda text: text.replace("  ", "  ../", 1)),
    ("a manifest without its final newline", "must end with a newline", lambda text: text.rstrip("\n")),
    ("a manifest that omits an asset", "SHA256SUMS must cover every candidate asset", lambda text: "".join(text.splitlines(keepends=True)[1:])),
    ("a digest that is not the asset's", "SHA256SUMS differs from downloaded bytes", lambda text: "0" * 64 + text[64:]),
)


def positive_source_baseline(ctx: Context) -> str:
    s = ctx.scenario("baseline-proof", "manifested")
    ws = publish_from(ctx, s)
    done = merged_source(ctx, s, ws)
    if done.rc != 0 or "agree" not in done.out:
        raise Reject("baseline", f"the real captured shapes did not pass the production source proof: {done.text.strip()[-300:]}")
    return "the captured exact-head source proof passes its production gate"


def positive_draft_baseline(ctx: Context) -> str:
    s2 = ctx.scenario("baseline-draft", "manifested")
    done = draft_gate(ctx, s2)
    if done.rc != 0:
        raise Reject("baseline", f"the qualified draft did not pass the production draft gate: {done.text.strip()[-300:]}")
    return "the qualified candidate asset set passes the production draft gate"


def positive_final_baseline(ctx: Context) -> str:
    s3 = ctx.scenario("baseline-final", "finalized")
    ws3 = publish_from(ctx, s3)
    done = s3.run_mode(ws3, "validate-draft", **PUBLISH_ENV)
    done_gate = s3.run_mode(ws3, "final-gate", **PUBLISH_ENV)
    if done.rc != 0 or done_gate.rc != 0:
        raise Reject("baseline", f"identical final metadata did not pass reuse and the final gate: {(done.text + done_gate.text).strip()[-300:]}")
    return "identical attached evidence passes reuse and the final gate"


def positive_baselines(ctx: Context) -> int:
    """Run the same three positive gate baselines used by the legacy lifecycle controls."""
    positive_source_baseline(ctx)
    positive_draft_baseline(ctx)
    positive_final_baseline(ctx)
    return 3


def task2_controls(ctx: Context) -> list:
    items: list = [c_capture_contract, c_sanitizer]
    items += [(lambda c, a=a: source_proof_control(c, *a)) for a in SOURCE_PROOF_CASES]
    items += [(lambda c, a=a: draft_control(c, *a)) for a in DRAFT_CASES]
    items += [(lambda c, a=a: recovery_control(c, *a)) for a in RECOVERY_CASES]
    items += [(lambda c, a=a: sums_control(c, *a)) for a in SUMS_CASES]
    return items


# ------------------------------------------------------------------------------------------- Task 3: retry ordering

RETRY_ENV = {"RETRY": "true", "INPUT_RELEASE_ID": str(RELEASE_ID), "RELEASE_ID": str(RELEASE_ID)}
EVIDENCE_DIRS = {"support-ledger.json": "evidence-corpus", "cgb-corpus-receipt.json": "evidence-corpus",
                 "v02-fuzz-receipt.json": "evidence-fuzz", "v02-performance-receipt.json": "evidence-performance"}


def regenerated_pair(ctx: Context) -> dict[str, bytes]:
    """What a retry's producers make: a corpus receipt and sidecar with new run-specific bytes, bound to each other."""
    corpus = b'{"corpus": "complete", "nonce": "retry-attempt"}\n'
    sidecar = json.loads((ctx.t.evidence / "support-ledger.json").read_text())
    sidecar.update(corpus_receipt_sha256=sha256_bytes(corpus), run_id="retry-attempt")
    return {"cgb-corpus-receipt.json": corpus, "support-ledger.json": (json.dumps(sidecar, indent=2, sort_keys=True) + "\n").encode()}


def retry_scenario(ctx: Context, name: str, stage: str = "attached") -> Scenario:
    s = ctx.scenario(name, stage)
    s.run_id, s.attempt = RUN_ID + 1, 1
    s.set_runs(own_event="workflow_dispatch")
    return s


def regenerated_snapshot(ws: Path) -> dict[str, bytes]:
    return {name: (ws / "build" / directory / name).read_bytes() for name, directory in EVIDENCE_DIRS.items()}


def edit_json_asset(s: Scenario, name: str, change) -> None:
    value = json.loads(s.asset_bytes(name))
    change(value)
    s.replace_asset(name, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


def retry_attach(ctx: Context, s: Scenario, tag: str, script: str | None = None) -> tuple[Path, Outcome, dict[str, bytes]]:
    ws = s.attach_workspace("retry-attach", regenerated_pair(ctx), script=script)
    before = regenerated_snapshot(ws)
    return ws, s.run_mode(ws, "attach-evidence", **RETRY_ENV), before


def downloads_of(outcome: Outcome) -> set[str]:
    return {name for call in outcome.calls if call.get("kind") == "download" for name in call.get("names", [])}


def refused_before_reuse(ctx: Context, label: str, needle: str, tamper, fetched: bool = True) -> str:
    s = retry_scenario(ctx, "tamper-" + label)
    tamper(s)
    ws, outcome, before = retry_attach(ctx, s, label)
    expect_fail(outcome, label, needle)
    attached_names = {n for n in EVIDENCE_DIRS if n in s.asset_names()}
    kinds = {c.get("kind") for c in outcome.calls}
    if "workflow_runs" in kinds or outcome.mutations():
        raise Reject("control-effect", f"{label}: the refusal was not independent of the recovery decision (it read live runs or wrote)")
    if regenerated_snapshot(ws) != before:
        raise Reject("control-effect", f"{label}: the refusal left the regenerated evidence replaced")
    if fetched and (not attached_names or not attached_names <= downloads_of(outcome)):
        raise Reject("control-unexercised", f"{label}: the attachments were not fetched before the refusal")
    if not fetched and downloads_of(outcome):
        raise Reject("control-unexercised", f"{label}: the earlier inventory check was expected to refuse before any download")
    return f"retry tamper: {label} is refused before any reuse or recovery decision"


RETRY_TAMPER_CASES = (
    ("an altered corpus receipt with a recomputed API digest", "does not bind the attached corpus receipt bytes",
     lambda s: s.replace_asset("cgb-corpus-receipt.json", s.asset_bytes("cgb-corpus-receipt.json") + b" ")),
    ("a fuzz receipt of another source", "not bound to the exact source revision",
     lambda s: edit_json_asset(s, "v02-fuzz-receipt.json", lambda v: v.update(source_sha="0" * 40))),
    ("a sidecar of another tag", "not the schema-2 sidecar of this exact tag and source",
     lambda s: edit_json_asset(s, "support-ledger.json", lambda v: v.update(tag="v9.9.9"))),
    ("a sidecar of another source", "not the schema-2 sidecar of this exact tag and source",
     lambda s: edit_json_asset(s, "support-ledger.json", lambda v: v.update(source_sha="0" * 40))),
    ("attached bytes that differ from the digest GitHub reports", "differs from the digest GitHub reports",
     lambda s: s.replace_asset("v02-fuzz-receipt.json", s.asset_bytes("v02-fuzz-receipt.json") + b" ", keep_digest=True)),
    ("a performance receipt that did not pass", "not a passed receipt",
     lambda s: edit_json_asset(s, "v02-performance-receipt.json", lambda v: v.update(result="failed"))),
    ("an unknown extra asset", "unknown or duplicated asset", _extra_asset),
    ("a duplicated performance receipt (refused by the inventory check that precedes the download)", "duplicate campaign or performance receipts",
     lambda s: _duplicate_row(s, "v02-performance-receipt.json"), False),
    ("a sidecar without its corpus receipt (refused by the inventory check that precedes the download)", "only partially attached",
     lambda s: s.remove_asset("cgb-corpus-receipt.json"), False),
)


def c_retry_reuse(ctx: Context) -> str:
    """Identical qualified bytes are reused after the independent check; the regenerated run-specific bytes never overwrite them."""
    s = retry_scenario(ctx, "retry-reuse")
    attached = {n: s.asset_bytes(n) for n in EVIDENCE_DIRS}
    ws, outcome, before = retry_attach(ctx, s, "reuse")
    if outcome.rc != 0:
        raise Reject("replay-retry", f"identical attached evidence was refused: {outcome.text.strip()[-300:]}")
    after = regenerated_snapshot(ws)
    if after != attached or after["cgb-corpus-receipt.json"] == before["cgb-corpus-receipt.json"]:
        raise Reject("replay-retry", "the retry did not reuse the attached bytes in place of the regenerated run-specific copies")
    if outcome.mutations() or {n: s.asset_bytes(n) for n in EVIDENCE_DIRS} != attached:
        raise Reject("replay-retry", "the retry uploaded or replaced an attached asset")
    order = [c.get("kind") for c in outcome.calls]
    if "download" not in order or "workflow_runs" not in order or order.index("download") > order.index("workflow_runs"):
        raise Reject("control-unexercised", "the attachments were not fetched before the recovery decision")
    return "a retry reuses the identical attached bytes, uploads nothing and replaces nothing"


def c_downstream_refusals(ctx: Context) -> list[ControlOutcome]:
    """Evidence that passes the independent check is still judged downstream; every refusal precedes the publish decision."""
    results: list[ControlOutcome] = []

    def stage(label: str, tamper, mode: str, needle: str, from_stage: str = "attached", attach_first: bool = True) -> None:
        s = retry_scenario(ctx, "downstream-" + label, from_stage)
        tamper(s)
        if mode == "validate-evidence":
            if attach_first:
                ws, outcome, _ = retry_attach(ctx, s, label)
                require_ok({"retry attach": outcome}, label)  # identity-valid evidence passes the independent check
            ws = s.subject_workspace("m")
            outcome = s.run_mode(ws, "validate-evidence", **RETRY_ENV)
        elif mode == "build-manifest":
            ws = s.subject_workspace("m")
            if from_stage == "attached":
                require_ok({"validate-evidence": s.run_mode(ws, "validate-evidence", **RETRY_ENV)}, label)
            outcome = s.run_mode(ws, "build-manifest", **RETRY_ENV)
        else:
            raise Reject("control-setup", mode)
        expect_fail(outcome, label, needle)
        if s.state()["decisions"] or "publish-decision" in s.mutations_logged():
            raise Reject("control-effect", f"{label}: a decision was recorded")
        results.append(ControlOutcome(_post_tag_case_id("consumer.downstream", label),
                                      f"retry downstream: {label} is refused before the publish decision"))

    stage("a campaign receipt that passes identity but is not a complete exploration",
          lambda s: edit_json_asset(s, "v02-fuzz-receipt.json", lambda v: v.update(status="incomplete")),
          "validate-evidence", "campaign is not a complete exploration")
    stage("a consumer receipt of another source", lambda s: edit_json_asset(s, "v02-consumer-receipt.json", lambda v: v.update(source_sha="0" * 40)),
          "validate-evidence", "downloaded C and C++ consumer receipt is malformed or not bound", attach_first=False)
    stage("a required platform asset removed", lambda s: s.remove_asset("gabbaboy-notices.txt"), "build-manifest", "candidate asset set mismatch")
    stage("an unknown extra asset at the manifest step", _extra_asset, "build-manifest", "candidate asset set mismatch")
    stage("final receipts without a platform manifest", lambda s: (s.add_asset("SHA256SUMS", b"x\n"), s.add_asset("release-receipt.json", b"{}\n")),
          "build-manifest", "candidate asset set mismatch")
    stage("an unknown extra asset beside the final receipts and manifest",
          lambda s: (s.add_asset("candidate-platform-manifest.json", b"{}\n"), s.add_asset("SHA256SUMS", b"x\n"), _extra_asset(s)),
          "build-manifest", "candidate asset set mismatch")
    stage("a platform manifest entry altered after attachment",
          lambda s: edit_json_asset(s, "candidate-platform-manifest.json", lambda v: v["assets"][0].update(sha256="0" * 64)),
          "build-manifest", "differs from the regenerated one", "manifested")
    return results


ATTACH_CHECK_LINE = ('bash trusted/.github/scripts/verify-release-gates.sh --check-attached-evidence "$RELEASE_TAG" "$SOURCE_SHA" '
                     '"$RUNNER_TEMP/attached-assets.json" "$RUNNER_TEMP"\n')
REUSE_LOOP_END = '      cp "$RUNNER_TEMP/attached-$name/$name" "$dir/$name"\n    fi\n  done\n'


def c_ordering_mutants(ctx: Context) -> list[ControlOutcome]:
    """IN-01: the unmutated lifecycle refuses a tampered attachment before it touches anything; a removed check lets it through
    to the recovery decision, and a check moved after the destructive reuse destroys the regenerated evidence first."""
    tamper = RETRY_TAMPER_CASES[0]
    removed = mutate_script(ctx.script, ATTACH_CHECK_LINE, "true\n")
    moved = mutate_script(mutate_script(ctx.script, ATTACH_CHECK_LINE, ""), REUSE_LOOP_END, REUSE_LOOP_END + "  " + ATTACH_CHECK_LINE)
    outcomes = {}
    for variant, script in (("real", ctx.script), ("removed", removed), ("moved", moved)):
        s = retry_scenario(ctx, f"ordering-{variant}")
        tamper[2](s)
        ws, outcome, before = retry_attach(ctx, s, variant, script=script)
        outcomes[variant] = (s, ws, outcome, before)
    s, ws, real, before = outcomes["real"]
    expect_fail(real, "real lifecycle", tamper[1])
    if regenerated_snapshot(ws) != before or "workflow_runs" in {c.get("kind") for c in real.calls}:
        raise Reject("control-effect", "the real lifecycle did not refuse before touching the regenerated evidence and the recovery decision")
    s, ws, gone, before = outcomes["removed"]
    if gone.rc != 0 or "workflow_runs" not in {c.get("kind") for c in gone.calls}:
        raise Reject("mutant-unexercised", "without the tamper check the altered attachment did not reach the recovery decision: the check is not what refuses it")
    s, ws, late, before = outcomes["moved"]
    expect_fail(late, "check after reuse", tamper[1])
    if regenerated_snapshot(ws) == before:
        raise Reject("mutant-unexercised", "a check moved after the reuse still left the regenerated evidence untouched: the ordering control proves nothing")
    if "download" not in {c.get("kind") for c in late.calls}:
        raise Reject("mutant-unexercised", "the misordered lifecycle never fetched the attachments")
    return [
        ControlOutcome("consumer.ordering.removed-tamper-check",
                       "a removed tamper check lets altered attachments reach the recovery decision; the real lifecycle refuses first"),
        ControlOutcome("consumer.ordering.check-after-reuse",
                       "a tamper check moved after the reuse destroys the regenerated evidence before it refuses; the real lifecycle does not"),
    ]


def task3_controls(ctx: Context) -> list:
    items: list = [c_retry_reuse, c_downstream_refusals, c_ordering_mutants]
    items += [(lambda c, a=a: refused_before_reuse(c, *a)) for a in RETRY_TAMPER_CASES]
    return items


def nightly_control(s: Scenario, ws: Path, base_state: dict, ctx: Context, label: str, needle: str, change) -> str:
    """The production nightly-gate mode against a hostile run history: refused in the gate's own words, before publication.

    One scenario and one workspace serve every case (the mode only reads the transport and writes under RUNNER_TEMP), so each
    case costs one mode run, not one repository clone."""
    state = copy.deepcopy(base_state)
    change(state, ctx.t)
    s.write_state(state)
    (ws / "runner-temp" / "nightly-gate-receipt.json").unlink(missing_ok=True)  # a hosted job starts with a fresh RUNNER_TEMP
    before = len(s.mutations_logged())
    out = s.run_mode(ws, "nightly-gate", RELEASE_ID=str(RELEASE_ID))
    expect_fail(out, f"nightly gate: {label}", needle)
    if len(s.mutations_logged()) != before:
        raise Reject("control-effect", f"nightly gate {label}: a refused gate still wrote to the release")
    if (ws / "runner-temp" / "nightly-gate-receipt.json").exists():
        raise Reject("control-effect", f"nightly gate {label}: a refused gate still wrote a receipt")
    return f"the nightly gate refuses {label}"


def _nightly(state: dict, **changes) -> None:
    for run in (state["nightly_runs"][0], state["nightly_view"][str(NIGHTLY_RUN_ID)]):
        run.update(changes)


def _nightly_replay(state: dict, **changes) -> None:
    state["nightly_view"][str(NIGHTLY_RUN_ID)]["jobs"][0].update(changes)


def _nightly_other_run(state: dict, head: str, **changes) -> None:
    run = dict(state["nightly_runs"][0], databaseId=NIGHTLY_RUN_ID + 1, createdAt="2026-10-26T18:00:00Z", headSha=head, **changes)
    state["nightly_runs"].append(run)
    state["nightly_view"][str(run["databaseId"])] = dict(state["nightly_view"][str(NIGHTLY_RUN_ID)], **run)


def _late_rehearsal_attempt(state: dict) -> None:
    state["attempt_jobs"]["jobs"][0]["completed_at"] = "2026-10-26T02:27:36Z"


NIGHTLY_CASES = (
    ("a failed run", "nightly-not-success", lambda st, t: _nightly(st, conclusion="failure")),
    ("a cancelled run", "nightly-not-success", lambda st, t: _nightly(st, conclusion="cancelled")),
    ("a newer run at another head", "nightly-head-mismatch", lambda st, t: _nightly_other_run(st, "1" * 40)),
    ("a skipped replay job", "nightly-replay-not-success", lambda st, t: _nightly_replay(st, conclusion="skipped")),
    ("a failed replay job", "nightly-replay-not-success", lambda st, t: _nightly_replay(st, conclusion="failure")),
    ("a run still in progress", "nightly-in-progress", lambda st, t: _nightly(st, status="in_progress", conclusion="")),
    ("no run at the rehearsed head", "nightly-no-run-at-head", lambda st, t: _nightly(st, headSha="2" * 40)),
    ("a newer red run behind which an older green one sits", "nightly-not-success",
     lambda st, t: _nightly_other_run(st, t.rehearsal_head, conclusion="failure")),
    ("a nightly run of another workflow", "nightly-no-run-at-head", lambda st, t: _nightly(st, workflowName="ci")),
    ("a rehearsed head with another tree", "differs from the tagged tree",
     lambda st, t: st["rehearsal_runs"][0].update(head_sha=t.other_head)),
    ("an attempt completed after the version PR merged", "rehearsal-postdates-tag",
     lambda st, t: _late_rehearsal_attempt(st)),
    ("no successful rehearsal run", "no successful rehearsal run", lambda st, t: st.update(rehearsal_runs=[])),
    ("no nightly run at all", "No nightly-asan run exists", lambda st, t: st.update(nightly_runs=[])),
)


def c_nightly_gate(ctx: Context) -> list[ControlOutcome]:
    positive = Scenario(ctx.t, "nightly-positive")
    ws = positive.subject_workspace("publish")
    ok = positive.run_mode(ws, "nightly-gate", RELEASE_ID=str(RELEASE_ID))
    if ok.rc != 0 or f"nightly-gate pass run_id={NIGHTLY_RUN_ID}" not in ok.out or positive.mutations_logged():
        raise Reject("replay-failed", f"nightly gate positive control: exit {ok.rc}: {ok.text.strip()[-300:]}")
    if f"rehearsal-bound run_id={RUN_ID - 500} head_sha={ctx.t.rehearsal_head}" not in ok.out:
        raise Reject("replay-failed", "the nightly gate did not report the rehearsal run it bound")
    receipt = json.loads(ok.out[ok.out.index("{"):])
    if receipt["head_sha"] != ctx.t.rehearsal_head or receipt["source_sha"] != ctx.t.source or receipt["run_id"] != NIGHTLY_RUN_ID:
        raise Reject("replay-failed", "the nightly receipt is not bound to the rehearsed head, the tagged source and the run")
    if any(c.get("outcome") == "refused" for c in positive.calls()):
        raise Reject("replay-refused", "the transport refused a production nightly call")
    base_state = positive.state()
    return [ControlOutcome(_post_tag_case_id("publication.nightly", label),
                           nightly_control(positive, ws, base_state, ctx, label, needle, change))
            for label, needle, change in NIGHTLY_CASES]


TASK1_CONTROLS = (c_wiring, c_wrong_repo, c_no_fallback, c_missing_attach, c_missing_gate, c_advisory_consumers, c_non_advisory,
                  c_unexpected_endpoint_in_script, c_live_publication, c_nightly_gate)

POST_TAG_GROUP_NAMES = ("trust", "capture_source", "draft_assets", "recovery_sums", "consumer", "publication")
DOWNSTREAM_CASE_LABELS = (
    "a campaign receipt that passes identity but is not a complete exploration",
    "a consumer receipt of another source",
    "a required platform asset removed",
    "an unknown extra asset at the manifest step",
    "final receipts without a platform manifest",
    "an unknown extra asset beside the final receipts and manifest",
    "a platform manifest entry altered after attachment",
)


def _single_post_tag_registration(group: str, control_id: str, run) -> PostTagRegistration:
    return PostTagRegistration(group, (control_id,), run)


def _parameterized_post_tag_registrations(group: str, prefix: str, cases: tuple, run) -> tuple[PostTagRegistration, ...]:
    return tuple(_single_post_tag_registration(
        group, _post_tag_case_id(prefix, case[0]), lambda ctx, case=case: run(ctx, *case)) for case in cases)


def _post_tag_registrations() -> tuple[PostTagRegistration, ...]:
    trust = (
        _single_post_tag_registration("trust", "trust.wiring", c_wiring),
        _single_post_tag_registration("trust", "trust.wrong-repository", c_wrong_repo),
        _single_post_tag_registration("trust", "trust.no-repository-fallback", c_no_fallback),
        _single_post_tag_registration("trust", "trust.missing-attachment", c_missing_attach),
        _single_post_tag_registration("trust", "trust.missing-final-gate", c_missing_gate),
        _single_post_tag_registration("trust", "trust.advisory-consumers", c_advisory_consumers),
        _single_post_tag_registration("trust", "trust.non-advisory-refusal", c_non_advisory),
        _single_post_tag_registration("trust", "trust.unexpected-endpoint", c_unexpected_endpoint_in_script),
        _single_post_tag_registration("trust", "trust.endpoint-inventory", c_endpoint_inventory),
    )
    capture_source = (
        _single_post_tag_registration("capture_source", "capture_source.positive-baseline", positive_source_baseline),
        _single_post_tag_registration("capture_source", "capture_source.capture-contract", c_capture_contract),
        _single_post_tag_registration("capture_source", "capture_source.sanitizer", c_sanitizer),
        *_parameterized_post_tag_registrations("capture_source", "capture_source.source-proof", SOURCE_PROOF_CASES,
                                                source_proof_control),
        _single_post_tag_registration("capture_source", "capture_source.perf-ci-run-receipt", c_perf_receipt_ci_run),
    )
    draft_assets = (
        _single_post_tag_registration("draft_assets", "draft_assets.positive-baseline", positive_draft_baseline),
        *_parameterized_post_tag_registrations("draft_assets", "draft_assets.candidate", DRAFT_CASES, draft_control),
    )
    recovery_sums = (
        _single_post_tag_registration("recovery_sums", "recovery_sums.positive-baseline", positive_final_baseline),
        *_parameterized_post_tag_registrations("recovery_sums", "recovery_sums.recovery", RECOVERY_CASES, recovery_control),
        *_parameterized_post_tag_registrations("recovery_sums", "recovery_sums.sha256sums", SUMS_CASES, sums_control),
    )
    consumer = (
        _single_post_tag_registration("consumer", "consumer.retry-reuse", c_retry_reuse),
        PostTagRegistration("consumer", tuple(_post_tag_case_id("consumer.downstream", label)
                                                for label in DOWNSTREAM_CASE_LABELS), c_downstream_refusals),
        PostTagRegistration("consumer", ("consumer.ordering.removed-tamper-check", "consumer.ordering.check-after-reuse"),
                            c_ordering_mutants),
        *_parameterized_post_tag_registrations("consumer", "consumer.attached-evidence", RETRY_TAMPER_CASES,
                                                refused_before_reuse),
    )
    publication = (
        _single_post_tag_registration("publication", "publication.live-publish-command", c_live_publication),
        PostTagRegistration("publication", tuple(_post_tag_case_id("publication.nightly", case[0])
                                                    for case in NIGHTLY_CASES), c_nightly_gate),
        _single_post_tag_registration("publication", "publication.perf-receipt-tamper", c_perf_receipt_tamper),
        _single_post_tag_registration("publication", "publication.profile-string", c_profile_string),
        _single_post_tag_registration("publication", "publication.pre-publish-inventory", c_pre_publish_inventory),
    )
    return (*trust, *capture_source, *draft_assets, *recovery_sums, *consumer, *publication)


def _manifest_controls(manifest: dict) -> tuple[dict, ...]:
    if (not isinstance(manifest, dict) or set(manifest) != {"schema_version", "baseline_revision", "controls"}
            or manifest.get("schema_version") != 1 or manifest.get("baseline_revision") != "dcb2c92668a47bc04f88fd3c57bc0d2e978473e1"
            or not isinstance(manifest.get("controls"), list)):
        raise Reject("post-tag-coverage", "the immutable expected-control manifest has an unsupported schema")
    expected = []
    seen = set()
    for item in manifest["controls"]:
        if not isinstance(item, dict) or set(item) != {"id", "group"}:
            raise Reject("post-tag-coverage", "an expected-control entry must contain only id and group")
        control_id, group = item["id"], item["group"]
        if (not isinstance(control_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", control_id)
                or group not in POST_TAG_GROUP_NAMES or control_id in seen):
            raise Reject("post-tag-coverage", f"invalid or duplicate expected control {control_id!r}")
        seen.add(control_id)
        expected.append({"id": control_id, "group": group})
    if not expected or set(item["group"] for item in expected) != set(POST_TAG_GROUP_NAMES):
        raise Reject("post-tag-coverage", "the expected-control manifest omits a semantic group")
    return tuple(expected)


def _load_post_tag_expected(rev: str) -> tuple[dict, ...]:
    try:
        manifest = json.loads(git_show(rev, POST_TAG_COVERAGE).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Reject("post-tag-coverage", f"the immutable expected-control manifest is invalid: {error}") from error
    return _manifest_controls(manifest)


def _registration_controls(registrations: tuple[PostTagRegistration, ...]) -> tuple[dict, ...]:
    registered = []
    seen = set()
    for registration in registrations:
        if registration.group not in POST_TAG_GROUP_NAMES or not registration.control_ids:
            raise Reject("post-tag-coverage", "a registration has no known semantic group or no control IDs")
        for control_id in registration.control_ids:
            if control_id in seen:
                raise Reject("post-tag-coverage", f"control {control_id!r} is registered more than once")
            if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", control_id):
                raise Reject("post-tag-coverage", f"control ID is not stable: {control_id!r}")
            seen.add(control_id)
            registered.append({"id": control_id, "group": registration.group})
    return tuple(registered)


def _validate_post_tag_registration(registrations: tuple[PostTagRegistration, ...], expected: tuple[dict, ...]) -> None:
    actual = _registration_controls(registrations)
    if actual != expected:
        expected_by_id = {item["id"]: item["group"] for item in expected}
        actual_by_id = {item["id"]: item["group"] for item in actual}
        missing = sorted(set(expected_by_id) - set(actual_by_id))
        extra = sorted(set(actual_by_id) - set(expected_by_id))
        wrong_group = sorted(control_id for control_id in set(expected_by_id) & set(actual_by_id)
                             if expected_by_id[control_id] != actual_by_id[control_id])
        raise Reject("post-tag-coverage", f"registration differs from baseline: missing={missing} extra={extra} wrong_group={wrong_group}")
    if set(item["group"] for item in actual) != set(POST_TAG_GROUP_NAMES):
        raise Reject("post-tag-coverage", "registration is not a complete disjoint union of semantic groups")


def _expect_coverage_rejection(registrations: tuple[PostTagRegistration, ...], expected: tuple[dict, ...], label: str) -> None:
    try:
        _validate_post_tag_registration(registrations, expected)
    except Reject as error:
        if error.code != "post-tag-coverage":
            raise Reject("coverage-self-test", f"{label}: wrong rejection {error}") from error
        return
    raise Reject("coverage-self-test", f"{label}: an invalid registration was accepted")


def post_tag_coverage_controls(rev: str) -> tuple[int, int]:
    expected = _load_post_tag_expected(rev)
    registrations = _post_tag_registrations()
    _validate_post_tag_registration(registrations, expected)
    _expect_coverage_rejection(registrations[1:], expected, "omitted registration")
    _expect_coverage_rejection((registrations[0], registrations[0], *registrations[1:]), expected, "duplicated registration")
    wrong_group = PostTagRegistration("publication", registrations[0].control_ids, registrations[0].run)
    _expect_coverage_rejection((wrong_group, *registrations[1:]), expected, "wrong-group registration")
    _expect_exit_contract_control(rev)
    return len(expected), len(registrations)


def _expect_exit_contract_control(rev: str) -> None:
    cmake = shutil.which("cmake")
    if cmake is None:
        raise Reject("expect-exit-control", "cmake is required to exercise the immutable expect_exit.cmake helper")
    helper = git_show(rev, "tests/expect_exit.cmake")
    with tempfile.TemporaryDirectory(prefix="gb-expect-exit-controls.") as name:
        lab = Path(name)
        helper_path = lab / "expect_exit.cmake"
        helper_path.write_bytes(helper)
        accepted = lab / "accepted.py"
        failed = lab / "failed.py"
        wrong_marker = lab / "wrong-marker.py"
        accepted.write_text("import sys\nprint('PASS expected-marker')\nraise SystemExit(0)\n", encoding="utf-8", newline="\n")
        failed.write_text("import sys\nprint('PASS expected-marker')\nraise SystemExit(1)\n", encoding="utf-8", newline="\n")
        wrong_marker.write_text("import sys\nprint('FAIL wrong-marker')\nraise SystemExit(0)\n", encoding="utf-8", newline="\n")

        def invoke(child: Path) -> subprocess.CompletedProcess:
            return subprocess.run(
                [cmake, f"-DGBB_CMD={Path(sys.executable).as_posix()};-I;{child.as_posix()}", "-DGBB_EXPECT_CODE=0",
                 "-DGBB_EXPECT_REGEX=PASS expected-marker", "-P", helper_path.as_posix()],
                cwd=lab, capture_output=True, text=True, timeout=10)

        passed = invoke(accepted)
        if passed.returncode != 0:
            raise Reject("expect-exit-control", f"the matching marker and zero exit were refused: {passed.stdout}{passed.stderr}")
        code_refusal = invoke(failed)
        code_output = code_refusal.stdout + code_refusal.stderr
        code_reason = "expected exit code 0 but the command returned '1'"
        if code_refusal.returncode == 0 or code_reason not in code_output or "PASS expected-marker" not in code_output:
            raise Reject("expect-exit-control", f"the matching marker did not lose to the child exit status: {code_output}")
        regex_refusal = invoke(wrong_marker)
        regex_output = regex_refusal.stdout + regex_refusal.stderr
        regex_reason = "exit code 0 was right but the output did not match 'PASS expected-marker'"
        if regex_refusal.returncode == 0 or regex_reason not in regex_output or "FAIL wrong-marker" not in regex_output:
            raise Reject("expect-exit-control", f"the wrong marker was not refused for the exact regex reason: {regex_output}")


def controls(rev: str, files: dict[str, bytes], capture: dict, base: Path) -> tuple[int, int]:
    wf = files[WORKFLOW].decode("utf-8")
    script = files[LIFECYCLE].decode("utf-8")
    template = Template(base, rev, files, capture)
    ctx = Context(template, wf, script, files)
    results: list[str] = []
    build_stages(ctx)
    positives = 1
    for relative in JUDGE_FILES:
        if (template.judge / relative).read_bytes() != files[relative]:
            raise Reject("lab-integrity", f"{relative} in the lab differs from the revision")
    tampered = Scenario(template, "integrity")
    ws = tampered.subject_workspace("publish")
    (ws / "trusted/.github/scripts/verify-release-gates.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    try:
        lab_integrity(ws, files)
    except Reject as error:
        if error.code != "lab-integrity":
            raise
        results.append("the lab refuses a permissive replacement of a production gate")
    else:
        raise Reject("control-accepted", "lab integrity accepted a replaced production gate")
    positives += positive_baselines(ctx)
    with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        futures = [pool.submit(fn, ctx) for fn in (*TASK1_CONTROLS, *task2_controls(ctx), *task3_controls(ctx))]
        futures.append(pool.submit(control_transport, template))
        for future in futures:
            outcome = future.result()
            results.extend(outcome if isinstance(outcome, list) else [outcome])
    return positives, len(results)


def _run_post_tag_registration(registration: PostTagRegistration, ctx: Context) -> list[ControlOutcome]:
    result = registration.run(ctx)
    if isinstance(result, ControlOutcome):
        outcomes = [result]
    elif isinstance(result, list) and all(isinstance(item, ControlOutcome) for item in result):
        outcomes = result
    elif isinstance(result, str):
        outcomes = [ControlOutcome(registration.control_ids[0], result)]
    else:
        raise Reject("post-tag-coverage", f"{registration.control_ids[0]} returned no identifiable control outcome")
    actual_ids = tuple(outcome.control_id for outcome in outcomes)
    if actual_ids != registration.control_ids:
        raise Reject("post-tag-coverage", f"{registration.group} emitted {actual_ids!r}; expected {registration.control_ids!r}")
    if any(not outcome.message.strip() for outcome in outcomes):
        raise Reject("post-tag-coverage", f"{registration.group} emitted an empty control result")
    return outcomes


def _run_post_tag_group(group: str, registrations: tuple[PostTagRegistration, ...], expected: tuple[dict, ...],
                        ctx: Context) -> tuple[list[ControlOutcome], int]:
    group_registrations = tuple(reg for reg in registrations if reg.group == group)
    expected_ids = tuple(item["id"] for item in expected if item["group"] == group)
    if not group_registrations or not expected_ids:
        raise Reject("post-tag-coverage", f"semantic group {group!r} is empty")

    outcomes: list[ControlOutcome] = []
    baseline_registrations = tuple(reg for reg in group_registrations
                                   if reg.control_ids[0].endswith(".positive-baseline"))
    control_registrations = tuple(reg for reg in group_registrations if reg not in baseline_registrations)
    for registration in baseline_registrations:
        outcomes.extend(_run_post_tag_registration(registration, ctx))
    with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        futures = [pool.submit(_run_post_tag_registration, registration, ctx) for registration in control_registrations]
        for future in futures:
            outcomes.extend(future.result())

    executed_ids = tuple(outcome.control_id for outcome in outcomes)
    if executed_ids != expected_ids:
        raise Reject("post-tag-coverage", f"{group} executed IDs differ from the immutable manifest: {executed_ids!r}")
    if len(set(executed_ids)) != len(executed_ids):
        raise Reject("post-tag-coverage", f"{group} executed a duplicate control ID")
    return outcomes, len(baseline_registrations)


def post_tag_controls(rev: str, files: dict[str, bytes], capture: dict, base: Path,
                      group: str | None = None) -> tuple[int, int, str, str]:
    wf = files[WORKFLOW].decode("utf-8")
    script = files[LIFECYCLE].decode("utf-8")
    template = Template(base, rev, files, capture)
    ctx = Context(template, wf, script, files)
    build_stages(ctx)
    expected = _load_post_tag_expected(rev)
    registrations = _post_tag_registrations()
    _validate_post_tag_registration(registrations, expected)
    groups = (group,) if group is not None else POST_TAG_GROUP_NAMES
    if any(name not in POST_TAG_GROUP_NAMES for name in groups):
        raise Reject("post-tag-coverage", f"unknown semantic group {group!r}")
    all_outcomes: list[ControlOutcome] = []
    positives = 0
    for name in groups:
        outcomes, group_positives = _run_post_tag_group(name, registrations, expected, ctx)
        all_outcomes.extend(outcomes)
        positives += group_positives
    executed_ids = tuple(outcome.control_id for outcome in all_outcomes)
    expected_ids = tuple(item["id"] for item in expected if group is None or item["group"] == group)
    if executed_ids != expected_ids:
        raise Reject("post-tag-coverage", "the completed group union differs from the immutable manifest")
    for control_id in executed_ids:
        print(f"post-tag-control PASS {control_id}")
    digest = hashlib.sha256("\n".join(executed_ids).encode("utf-8")).hexdigest()
    endpoint_status = "pass" if group is None or group == "trust" else "not-in-group"
    return positives, len(all_outcomes), endpoint_status, digest


def lab_integrity(workspace: Path, files: dict[str, bytes]) -> None:
    for relative in JUDGE_FILES:
        if relative.endswith("download-release-artifact.py"):
            continue  # the one transport the lab replaces by design
        if (workspace / "trusted" / relative).read_bytes() != files[relative]:
            raise Reject("lab-integrity", f"{relative} differs from the revision: the replay would not run the production code")


# ------------------------------------------------------------------------------------------------------- the CLI

def load_inputs(rev: str) -> tuple[dict[str, bytes], dict]:
    files = {path: git_show(rev, path) for path in (*JUDGE_FILES, WORKFLOW, DELIVERY, CAPTURE, SOURCES, SELF, POLICY)}
    capture = check_capture(files[CAPTURE], files[SOURCES].decode("utf-8"))
    return files, capture


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rev")
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    post_tag_mode = parser.add_mutually_exclusive_group()
    post_tag_mode.add_argument("--self-test-post-tag", action="store_true")
    post_tag_mode.add_argument("--self-test-post-tag-group", choices=POST_TAG_GROUP_NAMES)
    post_tag_mode.add_argument("--self-test-post-tag-coverage", action="store_true")
    post_tag_mode.add_argument("--self-test-post-tag-recovery", action="store_true")
    parser.add_argument("--check-capture", action="store_true")
    parser.add_argument("--sanitize-capture", nargs=2, metavar=("RAW_DIR", "OUTPUT"))
    args = parser.parse_args(argv)
    try:
        if args.sanitize_capture:
            raw_dir, output = (Path(item) for item in args.sanitize_capture)
            names = {"release": "release.json", "release_assets": "assets.json", "workflow_runs": "runs.json",
                     "workflow_run": "run.json", "jobs": "jobs.json", "artifacts": "artifacts.json",
                     "check_runs": "checks.json", "pull_request": "pull.json", "commit": "commit.json",
                     "pull_requests": "pull_requests.json", "attempt_jobs": "attempt_jobs.json",
                     "ci_run": "ci_run.json",
                     "identity": "identity.json"}
            raw = {key: json.loads((raw_dir / name).read_text(encoding="utf-8")) for key, name in names.items()}
            output.write_text(capture_text(assemble_capture(raw)), encoding="utf-8", newline="\n")
            return 0
        # Without --rev the checker resolves HEAD to its commit id once, and then reads only that commit's objects.
        head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=60)
        if not args.rev and (head.returncode != 0 or not SHA1.fullmatch(head.stdout.strip())):
            parser.error("--rev is required when HEAD does not resolve to a commit")
        rev = resolve_rev(args.rev or head.stdout.strip())
        if args.check_capture:
            files = {path: git_show(rev, path) for path in (CAPTURE, SOURCES)}
            capture = check_capture(files[CAPTURE], files[SOURCES].decode("utf-8"))
            print(f"release-lifecycle capture pass responses={len(capture['responses'])} bytes={len(files[CAPTURE])}")
            return 0
        if args.self_test_post_tag_coverage:
            baseline_ids, registrations = post_tag_coverage_controls(rev)
            print(f"release-lifecycle post-tag coverage controls pass baseline_ids={baseline_ids} registrations={registrations} "
                  "omitted=refused duplicate=refused wrong_group=refused expect_exit=pass")
            return 0
        if args.self_test_post_tag_recovery:
            controls_count, positives, original_hash, repaired_hash = self_test_post_tag_recovery(rev)
            print(f"release-lifecycle post-tag recovery controls pass controls={controls_count} positives={positives} "
                  f"original_section_sha256={original_hash} repaired_body_sha256={repaired_hash}")
            return 0
        if not (args.replay or args.self_test or args.self_test_post_tag or args.self_test_post_tag_group
                or args.self_test_post_tag_recovery):
            parser.error("choose --replay, --self-test, --self-test-post-tag, --self-test-post-tag-group, "
                         "--self-test-post-tag-coverage, --self-test-post-tag-recovery, --check-capture "
                         "or --sanitize-capture")
        try:
            script = git_show(rev, LIFECYCLE)
        except Reject:
            script = None
        check_wiring(git_show(rev, WORKFLOW).decode("utf-8"), script.decode("utf-8") if script is not None else None)
        files, capture = load_inputs(rev)
        with tempfile.TemporaryDirectory(prefix="gb-lifecycle.") as name:
            base = Path(name)
            if args.replay:
                facts = replay(rev, files, capture, base)
                print("release-lifecycle replay pass modes={modes} publish_decisions={publish_decisions} live_mutations={live_mutations} "
                      "uploads={uploads} calls={calls}".format(**facts))
                return 0
            if args.self_test_post_tag or args.self_test_post_tag_group:
                group = args.self_test_post_tag_group
                positives, count, endpoint_status, digest = post_tag_controls(rev, files, capture, base, group)
                label = group or "all"
                print(f"release-lifecycle post-tag group={label} controls={count} positives={positives} "
                      f"endpoint_inventory={endpoint_status} ids_sha256={digest}")
                return 0
            positives, count = controls(rev, files, capture, base)
            print(f"release-lifecycle controls pass positives={positives} controls={count}")
            return 0
    except Reject as error:
        print(str(error), file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
