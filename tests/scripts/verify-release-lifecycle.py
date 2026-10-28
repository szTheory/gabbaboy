#!/usr/bin/env python3
"""Replay the release evidence lifecycle against bounded, captured GitHub API shapes (RM-028, D-20).

    verify-release-lifecycle.py --rev SHA --replay
    verify-release-lifecycle.py --rev SHA --self-test
    verify-release-lifecycle.py --rev SHA --check-capture
    verify-release-lifecycle.py --sanitize-capture RAW_DIR OUTPUT

--rev is a resolved immutable 40-hex commit. Every production file the replay uses is materialized from that commit
with git show; the live working tree is never read and never a fallback.

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
import concurrent.futures
import copy
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
SOURCES = "tests/data/release-api/SOURCES.md"
# Production files the replay materializes from --rev into the judge checkout (the `trusted/` tree of every job).
JUDGE_FILES = (
    LIFECYCLE,
    ".github/scripts/verify-release-gates.sh",
    ".github/scripts/verify-published-release-assets.py",
    ".github/scripts/verify-release-source-proof.py",
    ".github/scripts/download-release-artifact.py",
)
# mode -> the release.yml job whose step must call it
MODES = {
    "attach-evidence": "attach-v02-evidence",
    "validate-evidence": "candidate-platform-manifest",
    "build-manifest": "candidate-platform-manifest",
    "validate-draft": "publish-qualified-release",
    "final-gate": "publish-qualified-release",
    "publish-draft": "publish-qualified-release",
}
LOAD_VERIFIERS_STEP = "Load trusted release evidence verifiers"
EVIDENCE_ATTACHED = ("support-ledger.json", "cgb-corpus-receipt.json", "v02-fuzz-receipt.json", "v02-performance-receipt.json")
FINAL_NAMES = ("SHA256SUMS", "release-receipt.json")
RELEASE_ID = 900000001
FIRST_ASSET_ID = 900100001
RUN_ID = 50000000001
MAX_CAPTURE_BYTES = 256 * 1024
RESPONSE_KEYS = ("release", "release_assets", "workflow_runs", "workflow_run", "jobs", "artifacts", "check_runs",
                 "pull_request", "commit")
PARALLEL = max(2, min(8, os.cpu_count() or 2))


class Reject(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"REJECT {code}: {message}")
        self.code = code


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
    "commit": ("sha",),
}
FORBIDDEN_MEMBERS = {"check_runs": ("check_runs.0.repository",)}
EMAIL = re.compile(r"[A-Za-z0-9._%+\[\]-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
REDACTED_EMAIL = "redacted@example.invalid"
FORBIDDEN_TEXT = re.compile(r"/Users/|/home/|[A-Za-z]:\\\\Users|\bgh[pousr]_[A-Za-z0-9]{20,}|github_pat_|BEGIN [A-Z ]*PRIVATE KEY")
KEEP_LOGINS = {"szTheory", "github"}
USER_KEYS = {"login", "node_id", "avatar_url"}
TRUNCATE_ARRAYS = {"assets": 2, "workflow_runs": 2, "jobs": 2, "artifacts": 2, "files": 1, "steps": 2}
OMITTED = "[omitted by the capture sanitizer]"
SOURCES_DIGEST = re.compile(r"(?m)^- captured\.json sha256: ([0-9a-f]{64})$")


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
            blank.update(login="sanitized-user", id=1, node_id="U_sanitized", gravatar_id="",
                         avatar_url="https://avatars.githubusercontent.com/u/1?v=4", site_admin=False)
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
        "check_runs": checks, "pull_request": raw["pull_request"], "commit": raw["commit"],
    }
    responses = {name: sanitize(value, "", log) for name, value in responses.items()}
    return {"schema_version": 1, "kind": "github-api-capture", "api_version": "2022-11-28", "repository": REPO,
            "identity": raw["identity"], "sanitizer": {"truncated": log.get("truncated", {}), "users_replaced": log.get("users", 0)},
            "responses": responses}


def capture_text(capture: dict) -> str:
    return json.dumps(capture, indent=2, sort_keys=True) + "\n"


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


ARGV = sys.argv[1:]
st_shapes = state()["shapes"] if (DIR / "state.json").is_file() else {}
if not ARGV:
    refuse("no command")
if ARGV[0] == "api":
    api(ARGV[1:])
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
        for relative in JUDGE_FILES:
            target = repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(files[relative])
        run_git(repo, "add", "-A")
        run_git(repo, "commit", "-q", "-m", "judge: production scripts at the replay revision")
        self.judge_sha = run_git(repo, "rev-parse", "HEAD")
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
            str(identity["run_id"]): str(RUN_ID - 1000),
        }
        responses = {name: retarget(value, mapping) for name, value in responses.items()}
        shapes = {
            "commit": key_shape(responses["commit"]), "release": key_shape(responses["release"]),
            "release_assets": key_shape(responses["release_assets"]), "workflow_runs": key_shape(responses["workflow_runs"]),
            "pull_request": key_shape(responses["pull_request"]), "check_runs": key_shape(responses["check_runs"]),
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
        state = {
            "release": release, "assets": [], "asset_template": template, "next_asset_id": FIRST_ASSET_ID,
            "runs": [old], "run_template": run_template, "pull_request": pull, "check_runs": checks,
            "check_runs_head": self.pr_head, "commits": {self.tag: commit, self.source: commit},
            "decisions": [], "shapes": shapes,
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
    for mode in ("validate-draft", "final-gate", "publish-draft"):
        out[mode] = s.run_mode(publish, mode, **env)
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
    sums = s.asset_bytes("SHA256SUMS").decode().splitlines()
    if sorted(line.split("  ", 1)[1] for line in sums) != sorted(n for n in names if n not in FINAL_NAMES):
        raise Reject("replay-sha256sums", "SHA256SUMS does not cover exactly the qualified inventory")
    # retry: the first attempt stopped after the final metadata was attached; fresh producers regenerate different bytes
    r = Scenario(template, "retry")
    r.set_runs()
    attach = r.attach_workspace("attach-1")
    require_ok({"attach-evidence": r.run_mode(attach, "attach-evidence")}, "retry setup")
    manifest = r.subject_workspace("manifest-1")
    require_ok({m: r.run_mode(manifest, m) for m in ("validate-evidence", "build-manifest")}, "retry setup")
    publish = r.subject_workspace("publish-1")
    require_ok({"load-verifiers": r.run_workflow_step(publish, wf, LOAD_VERIFIERS_STEP, RELEASE_ID=str(RELEASE_ID)),
                "validate-draft": r.run_mode(publish, "validate-draft", RELEASE_ID=str(RELEASE_ID))}, "retry setup")
    before = {n: r.asset_bytes(n) for n in r.asset_names()}
    (r.stub / "calls.jsonl").unlink()
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
    for mode in ("validate-draft", "final-gate", "publish-draft"):
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
        publish = publish_from(ctx, s, script=text)
        require_ok({"validate-draft": s.run_mode(publish, "validate-draft", **PUBLISH_ENV)}, "missing-gate setup (identical final metadata is reused)")
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
    publish = publish_from(ctx, s, script=mutated)
    require_ok({"validate-draft": s.run_mode(publish, "validate-draft", **PUBLISH_ENV),
                "final-gate": s.run_mode(publish, "final-gate", **PUBLISH_ENV)}, "live-publication setup")
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


TASK1_CONTROLS = (c_wiring, c_wrong_repo, c_no_fallback, c_missing_attach, c_missing_gate, c_advisory_consumers, c_non_advisory,
                  c_unexpected_endpoint_in_script, c_live_publication)


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
    with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        futures = [pool.submit(fn, ctx) for fn in TASK1_CONTROLS]
        futures.append(pool.submit(control_transport, template))
        for future in futures:
            outcome = future.result()
            results.extend(outcome if isinstance(outcome, list) else [outcome])
    return positives, len(results)


def lab_integrity(workspace: Path, files: dict[str, bytes]) -> None:
    for relative in JUDGE_FILES:
        if relative.endswith("download-release-artifact.py"):
            continue  # the one transport the lab replaces by design
        if (workspace / "trusted" / relative).read_bytes() != files[relative]:
            raise Reject("lab-integrity", f"{relative} differs from the revision: the replay would not run the production code")


# ------------------------------------------------------------------------------------------------------- the CLI

def load_inputs(rev: str) -> tuple[dict[str, bytes], dict]:
    files = {path: git_show(rev, path) for path in (*JUDGE_FILES, WORKFLOW, DELIVERY, CAPTURE, SOURCES)}
    capture = check_capture(files[CAPTURE], files[SOURCES].decode("utf-8"))
    return files, capture


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rev")
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--check-capture", action="store_true")
    parser.add_argument("--sanitize-capture", nargs=2, metavar=("RAW_DIR", "OUTPUT"))
    args = parser.parse_args(argv)
    try:
        if args.sanitize_capture:
            raw_dir, output = (Path(item) for item in args.sanitize_capture)
            names = {"release": "release.json", "release_assets": "assets.json", "workflow_runs": "runs.json",
                     "workflow_run": "run.json", "jobs": "jobs.json", "artifacts": "artifacts.json",
                     "check_runs": "checks.json", "pull_request": "pull.json", "commit": "commit.json",
                     "identity": "identity.json"}
            raw = {key: json.loads((raw_dir / name).read_text(encoding="utf-8")) for key, name in names.items()}
            output.write_text(capture_text(assemble_capture(raw)), encoding="utf-8", newline="\n")
            return 0
        if not args.rev:
            parser.error("--rev is required")
        rev = resolve_rev(args.rev)
        if args.check_capture:
            files = {path: git_show(rev, path) for path in (CAPTURE, SOURCES)}
            capture = check_capture(files[CAPTURE], files[SOURCES].decode("utf-8"))
            print(f"release-lifecycle capture pass responses={len(capture['responses'])} bytes={len(files[CAPTURE])}")
            return 0
        if not (args.replay or args.self_test):
            parser.error("choose --replay, --self-test, --check-capture or --sanitize-capture")
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
            positives, count = controls(rev, files, capture, base)
            print(f"release-lifecycle controls pass positives={positives} controls={count}")
            return 0
    except Reject as error:
        print(str(error), file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
