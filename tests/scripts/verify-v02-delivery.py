#!/usr/bin/env python3
"""Qualify the v0.2.0 delivery evidence against owner validators and live GitHub state.

Modes
  --check-evidence DIR --tag TAG --source-sha SHA [--source-archive PATH]
      Run the owner validators (support sidecar, performance, fuzz, source archive) over one
      evidence directory and bind every receipt to the exact tag/source.
  --stage phase-pr|published --receipt PATH [--published-dir DIR --validation-dir DIR]
      Compare a bounded captured delivery receipt with fresh read-only GitHub readback.
  --self-test
      Drive this checker end to end over a private fixture repository and simulated readback.

--repo-root selects the Git checkout whose owner validators are run (default: this checkout).
Only read-only `gh api` GET requests are made; nothing here tags, uploads, publishes or merges.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
REPO = "szTheory/gabbaboy"
HEX40 = re.compile(r"[0-9a-f]{40}")
HEX64 = re.compile(r"[0-9a-f]{64}")
TAG_RE = re.compile(r"v\d+\.\d+\.\d+")
MAX_JSON_BYTES = 8 * 1024 * 1024
OWNER_TIMEOUT_SECONDS = 600

CORPUS = "cgb-corpus-receipt.json"
SIDECAR = "support-ledger.json"
PERFORMANCE = "v02-performance-receipt.json"
FUZZ = "v02-fuzz-receipt.json"
ARCHIVE_RECEIPT = "source-archive-receipt.json"
CONSUMER = "v02-consumer-receipt.json"
EVIDENCE_NAMES = (CORPUS, SIDECAR, PERFORMANCE, FUZZ, ARCHIVE_RECEIPT, CONSUMER)
REUSE_FILE = "evidence-reuse.json"
WORKLOAD_ID = "original-wram-tracer-1m-half-dots-v1"
BEHAVIORS = ("profile_selection", "probe_info", "rgb555_frame_copy", "rtc_catch_up")

# Inputs that decide what a producer measured or fuzzed. A prior producer may stand in for the tag
# only if every one is byte-identical (Git object identity) between producer and tag.
COVERED_INPUTS = (
    "CMakeLists.txt", "include", "src", "fixtures", "tests/CMakeLists.txt",
    "tests/measure_core.c", "tests/fuzz_core.c", "tests/fuzz",
    "tests/scripts/measure-release-baseline.sh", "tests/scripts/verify-v02-performance.py",
    "tests/scripts/run-bounded-fuzz.sh", "tests/scripts/verify-v02-fuzz.py",
    ".github/workflows/ci.yml",
)
OWNERS = {
    "ledger": "tests/scripts/verify-support-ledger.py",
    "performance": "tests/scripts/verify-v02-performance.py",
    "fuzz": "tests/scripts/verify-v02-fuzz.py",
    "archive": "tests/scripts/verify-v02-source-archive.py",
}
REQUIRED_CONTEXTS = {"required-native": 15368, "fixture-repro": 15368, "preview-package-smoke": 15368}
APP_SLUG = "github-actions"


class Reject(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def reject(code: str, message: str) -> None:
    raise Reject(code, message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path, code: str) -> Any:
    try:
        if path.stat().st_size > MAX_JSON_BYTES:
            reject(code, f"{path.name} exceeds the size bound")
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise Reject(code, f"{path.name} is unreadable or invalid JSON") from error


def git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=120)
    if done.returncode != 0:
        reject("git-failed", f"git {args[0]} failed")
    return done.stdout.strip()


def git_ok(repo: Path, *args: str) -> bool:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=120).returncode == 0


# ---------------------------------------------------------------------------- owner execution

def run_owner(name: str, root: Path, *args: str) -> None:
    script = root / OWNERS[name]
    if not script.is_file():
        reject(f"owner-{name}", f"owner validator {OWNERS[name]} is absent from the checkout")
    try:
        done = subprocess.run([sys.executable, "-I", str(script), *args], cwd=root,
                              capture_output=True, text=True, timeout=OWNER_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        reject(f"owner-{name}", f"owner validator {name} timed out")
    if done.returncode != 0:
        tail = (done.stderr or done.stdout).strip().splitlines()[-1:] or ["no output"]
        reject(f"owner-{name}", f"owner validator {name} rejected the evidence: {tail[0][:200]}")


@contextlib.contextmanager
def producer_checkout(repo: Path, sha: str):
    """A detached checkout of the original producer so its own validator judges its own receipt."""
    parent = Path(tempfile.mkdtemp(prefix="gb-producer."))
    target = parent / "tree"
    try:
        git(repo, "worktree", "add", "--detach", str(target), sha)
        yield target
    finally:
        subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(target)],
                       capture_output=True, timeout=120)
        shutil.rmtree(parent, ignore_errors=True)


def covered_inputs_equal(repo: Path, producer: str, source: str) -> None:
    for path in COVERED_INPUTS:
        left = subprocess.run(["git", "-C", str(repo), "rev-parse", f"{producer}:{path}"],
                              capture_output=True, text=True, timeout=60)
        right = subprocess.run(["git", "-C", str(repo), "rev-parse", f"{source}:{path}"],
                               capture_output=True, text=True, timeout=60)
        if left.returncode != 0 or right.returncode != 0 or left.stdout != right.stdout:
            reject("reuse-input-changed", f"covered input {path} differs between producer and tag")


def reuse_entry(evidence: Path, family: str, receipt_sha: str, repo: Path, source: str, tag: str) -> str | None:
    """Return the original producer SHA when a justified reuse record covers this family."""
    path = evidence / REUSE_FILE
    if not path.is_file():
        return None
    records = read_json(path, "reuse-invalid")
    entry = records.get(family) if isinstance(records, dict) else None
    if entry is None:
        return None
    if not isinstance(entry, dict):
        reject("reuse-invalid", f"reuse record for {family} is malformed")
    producer = entry.get("original_producer_sha")
    if not isinstance(producer, str) or not HEX40.fullmatch(producer) or producer != receipt_sha:
        reject("reuse-invalid", f"{family} reuse must name the receipt's own unaltered producer SHA")
    if not isinstance(entry.get("justification"), str) or len(entry["justification"].strip()) < 20:
        reject("reuse-invalid", f"{family} reuse lacks a substantive justification")
    if git(repo, "rev-parse", f"{tag}^{{commit}}") != source:
        reject("reuse-tag-binding", "tag does not resolve to the frozen source SHA")
    if not git_ok(repo, "merge-base", "--is-ancestor", producer, source):
        reject("reuse-invalid", f"{family} producer is not an ancestor of the tag source")
    covered_inputs_equal(repo, producer, source)
    return producer


# ------------------------------------------------------------------------- evidence directory

def check_evidence(evidence: Path, tag: str, source: str, repo: Path, archive: Path | None) -> dict[str, int]:
    if not TAG_RE.fullmatch(tag) or not HEX40.fullmatch(source):
        reject("identity-malformed", "tag or source SHA is malformed")
    docs: dict[str, Any] = {}
    for name in EVIDENCE_NAMES:
        path = evidence / name
        if not path.is_file() or path.stat().st_size == 0:
            reject("evidence-missing", f"required evidence {name} is absent or empty")
        docs[name] = read_json(path, "evidence-invalid")
        if not isinstance(docs[name], dict):
            reject("evidence-invalid", f"{name} is not a JSON object")
    if archive is None or not archive.is_file():
        reject("evidence-missing", "the generated source archive is required beside its receipt")

    sidecar = docs[SIDECAR]
    if (sidecar.get("schema_version") != 2 or sidecar.get("tag") != tag or sidecar.get("source_sha") != source
            or sidecar.get("version") != tag[1:]):
        reject("sidecar-binding", "support sidecar is not the schema-2 sidecar of this exact tag and source")
    if sidecar.get("corpus_receipt_sha256") != sha256_bytes((evidence / CORPUS).read_bytes()):
        reject("sidecar-binding", "support sidecar does not bind the supplied corpus receipt bytes")

    fuzz = docs[FUZZ]
    workflow = fuzz.get("workflow")
    if not isinstance(workflow, dict):
        reject("fuzz-binding", "fuzz receipt has no workflow identity")
    for field in ("run_id", "attempt"):
        if type(workflow.get(field)) is not int or workflow[field] < 1:
            reject("fuzz-binding", f"fuzz workflow {field} is not a positive integer")
    perf_sha = (docs[PERFORMANCE].get("source") or {}).get("candidate", {}).get("sha")
    fuzz_sha = fuzz.get("source_sha")
    reuse = {"performance": None, "fuzz": None}
    for family, claimed in (("performance", perf_sha), ("fuzz", fuzz_sha)):
        if not isinstance(claimed, str) or not HEX40.fullmatch(claimed):
            reject(f"{'fuzz' if family == 'fuzz' else 'performance'}-binding", f"{family} receipt carries no source SHA")
        if claimed != source:
            reuse[family] = reuse_entry(evidence, family, claimed, repo, source, tag)
            if reuse[family] is None:
                reject(f"{'fuzz' if family == 'fuzz' else 'performance'}-binding",
                       f"{family} receipt was produced for another revision and no justified reuse is recorded")

    consumer = docs[CONSUMER]
    results = consumer.get("results")
    behaviors = consumer.get("api_behaviors")
    if (consumer.get("result") != "passed" or consumer.get("source_sha") != source
            or consumer.get("isolated_prefix") is not True or not isinstance(results, dict)
            or set(results) != {"c", "cpp"} or not isinstance(behaviors, dict)
            or set(behaviors) != set(BEHAVIORS)
            or any(behaviors[b] != {"c": "passed", "cpp": "passed"} for b in BEHAVIORS)):
        reject("consumer-binding", "downloaded C and C++ consumer results are missing, partial or for another source")

    run_owner("ledger", repo, "--tag", tag, "--source-sha", source, "--receipt", str(evidence / CORPUS),
              "--verify-sidecar", str(evidence / SIDECAR))
    for family, option, name in (("performance", "--verify", PERFORMANCE), ("fuzz", "--verify", FUZZ)):
        if reuse[family] is None:
            run_owner(family, repo, option, str(evidence / name))
        else:
            with producer_checkout(repo, reuse[family]) as old:
                run_owner(family, old, option, str(evidence / name))
    run_owner("archive", repo, "--check-receipt", str(evidence / ARCHIVE_RECEIPT), "--archive", str(archive),
              "--tag", tag, "--source-sha", source)
    return {"evidence_families": len(EVIDENCE_NAMES), "reused": sum(v is not None for v in reuse.values())}


# ----------------------------------------------------------------------------- live readback

class LiveReader:
    """Read-only GitHub readback; `gh api` without a method flag is a GET."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def get(self, path: str) -> Any:
        self.calls.append(path)
        try:
            done = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=120)
            if done.returncode != 0:
                reject("readback-failed", f"live read of {path} failed")
            return json.loads(done.stdout)
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
            raise Reject("readback-failed", f"live read of {path} failed") from error


class FixtureReader:
    def __init__(self, table: dict[str, Any]) -> None:
        self.table = table
        self.calls: list[str] = []

    def get(self, path: str) -> Any:
        self.calls.append(path)
        if path not in self.table:
            reject("readback-failed", f"simulated readback has no response for {path}")
        return json.loads(json.dumps(self.table[path]))


def api(path: str) -> str:
    return f"repos/{REPO}/{path}"


def need_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or not HEX40.fullmatch(value):
        reject("receipt-malformed", f"{label} is not a full commit SHA")
    return value


def check_pr(reader: Any, proof: Any, label: str, merged: bool) -> str:
    if not isinstance(proof, dict) or type(proof.get("number")) is not int or proof["number"] < 1:
        reject("receipt-malformed", f"{label} has no pull request number")
    head = need_sha(proof.get("head_sha"), f"{label} head")
    pull = reader.get(api(f"pulls/{proof['number']}"))
    if pull.get("number") != proof["number"] or pull.get("base", {}).get("ref") != "main":
        reject("pr-mismatch", f"{label} is not the recorded pull request against main")
    if pull.get("head", {}).get("sha") != head:
        reject("pr-mismatch", f"{label} head differs from the reviewed head")
    if merged:
        merge = need_sha(proof.get("merge_commit_sha"), f"{label} merge commit")
        if pull.get("state") != "closed" or not pull.get("merged_at") or pull.get("merge_commit_sha") != merge:
            reject("pr-mismatch", f"{label} is not merged at the recorded merge commit")
    checks = reader.get(api(f"commits/{head}/check-runs?per_page=100"))
    seen: dict[str, list[dict[str, Any]]] = {}
    for run in checks.get("check_runs", []):
        if run.get("name") in REQUIRED_CONTEXTS:
            seen.setdefault(run["name"], []).append(run)
    for context, app_id in REQUIRED_CONTEXTS.items():
        for run in seen.get(context) or reject("checks-mismatch", f"{label} has no {context} check on its head"):
            app = run.get("app") or {}
            if (run.get("head_sha") != head or run.get("status") != "completed"
                    or run.get("conclusion") != "success" or app.get("id") != app_id
                    or app.get("slug") != APP_SLUG):
                reject("checks-mismatch", f"{label} required check {context} is stale, incomplete or foreign")
    return head


def check_runs(reader: Any, runs: Any, head: str) -> None:
    if not isinstance(runs, list) or not runs:
        reject("receipt-malformed", "workflow_runs must list the observed attempts")
    identities = [(r.get("id"), r.get("attempt")) for r in runs if isinstance(r, dict)]
    if len(identities) != len(runs) or len(set(identities)) != len(identities):
        reject("runs-mismatch", "workflow run attempts are malformed or duplicated")
    for run_id, attempt in identities:
        if type(run_id) is not int or type(attempt) is not int or run_id < 1 or attempt < 1:
            reject("receipt-malformed", "workflow run identity is not a positive integer pair")
        latest = reader.get(api(f"actions/runs/{run_id}"))
        if latest.get("run_attempt") != attempt:
            reject("runs-mismatch", f"workflow run {run_id} attempt {attempt} is stale or superseded")
        one = reader.get(api(f"actions/runs/{run_id}/attempts/{attempt}"))
        if (one.get("head_sha") != head or one.get("status") != "completed"
                or one.get("conclusion") != "success"):
            reject("runs-mismatch", f"workflow run {run_id} attempt {attempt} is not a successful run of the head")


def hash_directory(directory: Path) -> dict[str, tuple[int, str]]:
    result = {}
    for path in sorted(directory.iterdir()):
        if path.is_symlink() or not path.is_file():
            reject("readback-mismatch", f"final readback holds a non-regular entry: {path.name}")
        data = path.read_bytes()
        result[path.name] = (len(data), sha256_bytes(data))
    return result


def check_stage(stage: str, receipt: Any, reader: Any, published_dir: Path | None,
                validation_dir: Path | None) -> str:
    if not isinstance(receipt, dict) or receipt.get("schema_version") != 1 or receipt.get("stage") != stage:
        reject("receipt-malformed", f"receipt is not a version 1 {stage} delivery receipt")
    if sorted(receipt.get("required_checks", [])) != sorted(REQUIRED_CONTEXTS):
        reject("receipt-malformed", "receipt does not name exactly the required checks")
    phase_head = check_pr(reader, receipt.get("phase_pr"), "phase pull request", merged=stage == "published")
    check_runs(reader, receipt.get("workflow_runs"), phase_head)
    if stage == "phase-pr":
        return "phase pull request, required checks and workflow attempts agree with live state"

    source = need_sha(receipt.get("source_sha"), "source_sha")
    tag, release_id = receipt.get("tag"), receipt.get("release_id")
    if not isinstance(tag, str) or not TAG_RE.fullmatch(tag) or type(release_id) is not int:
        reject("receipt-malformed", "tag or release ID is malformed")
    version_pr = receipt.get("version_pr")
    check_pr(reader, version_pr, "version pull request", merged=True)
    if version_pr["merge_commit_sha"] != source:
        reject("pr-mismatch", "the squash merge of the version pull request is not the tag source")

    # Fresh state first: release, then tag, then assets.
    release = reader.get(api(f"releases/{release_id}"))
    if release.get("draft") is not False or not release.get("published_at") or release.get("tag_name") != tag:
        reject("publication-mismatch", "live release is not the published release of this tag")
    publication = receipt.get("publication")
    if not isinstance(publication, dict) or publication.get("published_at") != release.get("published_at"):
        reject("publication-mismatch", "receipt publication time differs from live state")
    if reader.get(api(f"commits/{tag}")).get("sha") != source:
        reject("tag-mismatch", "the published tag does not resolve to the frozen source")

    readback = receipt.get("asset_readback")
    if not isinstance(readback, dict) or not isinstance(readback.get("assets"), list) or not readback["assets"]:
        reject("receipt-malformed", "receipt has no asset readback inventory")
    expected = {}
    for row in readback["assets"]:
        if (not isinstance(row, dict) or not isinstance(row.get("name"), str) or type(row.get("size")) is not int
                or not isinstance(row.get("sha256"), str) or not HEX64.fullmatch(row["sha256"])
                or row["name"] in expected):
            reject("receipt-malformed", "asset readback row is malformed or duplicated")
        expected[row["name"]] = (row["size"], row["sha256"])
    live_assets = reader.get(api(f"releases/{release_id}/assets?per_page=100"))
    live = {}
    for asset in live_assets:
        name = asset.get("name")
        if name in live:
            reject("readback-mismatch", f"live release has duplicate asset {name}")
        live[name] = (asset.get("size"), str(asset.get("digest", "")).removeprefix("sha256:"))
    if live != expected:
        reject("readback-mismatch", "live asset names, sizes or digests differ from the receipt inventory")
    for name in EVIDENCE_NAMES:
        if name not in expected:
            reject("readback-mismatch", f"published inventory lacks evidence asset {name}")
    sidecars = receipt.get("sidecars")
    if not isinstance(sidecars, dict) or set(sidecars) != set(EVIDENCE_NAMES) or any(
            sidecars[n] != expected[n][1] for n in EVIDENCE_NAMES):
        reject("receipt-malformed", "sidecar digests do not match the published evidence assets")
    archive = receipt.get("source_archive")
    if (not isinstance(archive, dict) or not HEX64.fullmatch(str(archive.get("sha256", "")))
            or archive.get("receipt_sha256") != expected[ARCHIVE_RECEIPT][1]):
        reject("receipt-malformed", "source archive identity is missing or differs from its published receipt")

    if published_dir is None or validation_dir is None:
        reject("readback-mismatch", "published readback needs a final download directory and the earlier validation directory")
    final, earlier = published_dir.resolve(), validation_dir.resolve()
    if final == earlier or final in earlier.parents or earlier in final.parents:
        reject("readback-mismatch", "earlier validation download cannot serve as publication proof")
    if hash_directory(published_dir) != expected:
        reject("readback-mismatch", "final downloaded bytes differ from the receipt inventory")
    return "published release, tag, assets and final readback agree with live state"


# ------------------------------------------------------------------------------------ CLI

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--check-evidence", type=Path)
    parser.add_argument("--tag")
    parser.add_argument("--source-sha")
    parser.add_argument("--source-archive", type=Path)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--stage", choices=("phase-pr", "published"))
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--published-dir", type=Path)
    parser.add_argument("--validation-dir", type=Path)
    parser.add_argument("--readback-fixture", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            return run_self_test()
        if args.check_evidence:
            if not (args.tag and args.source_sha):
                parser.error("--check-evidence needs --tag and --source-sha")
            counts = check_evidence(args.check_evidence, args.tag, args.source_sha, args.repo_root, args.source_archive)
            print(f"PASS: v02 delivery evidence binds {counts['evidence_families']} families to {args.tag} "
                  f"(reused={counts['reused']})")
            return 0
        if args.stage:
            if not args.receipt:
                parser.error("--stage needs --receipt")
            reader: Any = (FixtureReader(json.loads(args.readback_fixture.read_text()))
                           if args.readback_fixture else LiveReader())
            message = check_stage(args.stage, read_json(args.receipt, "receipt-malformed"), reader,
                                  args.published_dir, args.validation_dir)
            print(f"PASS: {message}")
            return 0
        parser.error("choose --self-test, --check-evidence or --stage")
    except Reject as error:
        print(f"REJECT {error.code}: {error}", file=sys.stderr)
        return 1
    return 2


# ------------------------------------------------------------------------------- self-test

STUB_OWNER = r'''
import hashlib, json, pathlib, subprocess, sys
a = sys.argv[1:]
name = pathlib.Path(sys.argv[0]).name
def opt(n): return a[a.index(n) + 1]
def die(m): print(m, file=sys.stderr); sys.exit(1)
def load(p): return json.loads(pathlib.Path(p).read_text())
def head(): return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
if name == "verify-support-ledger.py":
    tag, sha = opt("--tag"), opt("--source-sha")
    oid = subprocess.check_output(["git", "rev-parse", tag + ":docs/support/v0.2.0.md"], text=True).strip()
    want = {"schema_version": 2, "version": tag[1:], "tag": tag, "source_sha": sha, "ledger_blob": oid,
            "corpus_receipt_sha256": hashlib.sha256(pathlib.Path(opt("--receipt")).read_bytes()).hexdigest()}
    got = load(opt("--verify-sidecar"))
    if {k: got.get(k) for k in want} != want: die("sidecar differs from the tagged ledger")
elif name == "verify-v02-performance.py":
    r = load(a[1])
    if r.get("result") != "passed" or r.get("workload", {}).get("id") != "original-wram-tracer-1m-half-dots-v1":
        die("rejected:workload-identity-mismatch")
elif name == "verify-v02-fuzz.py":
    r = load(a[1])
    if r.get("status") != "complete" or r.get("mode") != "explore": die("campaign is not a complete exploration")
    if r.get("source_sha") != head(): die("stale receipt source SHA")
elif name == "verify-v02-source-archive.py":
    r = load(opt("--check-receipt"))
    if r.get("archive_sha256") != hashlib.sha256(pathlib.Path(opt("--archive")).read_bytes()).hexdigest():
        die("REJECT receipt-invalid: archive digest differs")
'''


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), *args], cwd=cwd,
                          capture_output=True, text=True, timeout=300)


def make_fixture_repo(base: Path) -> tuple[Path, str, str]:
    repo = base / "repo"
    (repo / "tests/scripts").mkdir(parents=True)
    for owner in OWNERS.values():
        (repo / owner).write_text(STUB_OWNER)
    for path in COVERED_INPUTS:
        target = repo / path
        if target.suffix:
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_text(f"covered {path}\n")
        else:
            target.mkdir(parents=True, exist_ok=True)
            (target / "file").write_text(f"covered {path}\n")
    (repo / "docs/support").mkdir(parents=True)
    (repo / "docs/support/v0.2.0.md").write_text("ledger\n")
    env = ["-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false"]

    def commit(message: str) -> str:
        subprocess.run(["git", "-C", str(repo), *env, "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), *env, "commit", "-q", "-m", message], check=True, capture_output=True)
        return git(repo, "rev-parse", "HEAD")

    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True, capture_output=True)
    producer = commit("producer")
    (repo / "NOTES.md").write_text("not a covered input\n")
    source = commit("source")
    subprocess.run(["git", "-C", str(repo), "tag", "v0.2.0", source], check=True, capture_output=True)
    return repo, producer, source


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def make_evidence(directory: Path, source: str) -> Path:
    directory.mkdir(parents=True)
    corpus = b'{"corpus": "complete"}\n'
    (directory / CORPUS).write_bytes(corpus)
    oid = git(directory.parent / "repo", "rev-parse", "v0.2.0:docs/support/v0.2.0.md")
    write_json(directory / SIDECAR, {"schema_version": 2, "version": "0.2.0", "tag": "v0.2.0", "source_sha": source,
                                     "ledger_blob": oid, "corpus_receipt_sha256": sha256_bytes(corpus)})
    write_json(directory / PERFORMANCE, {"result": "passed", "workload": {"id": WORKLOAD_ID},
                                         "source": {"candidate": {"sha": source}}})
    write_json(directory / FUZZ, {"status": "complete", "mode": "explore", "source_sha": source,
                                  "workflow": {"run_id": 4242, "attempt": 1, "event": "push"}})
    archive = directory.parent / "source-archive.tar.gz"
    archive.write_bytes(b"generated archive bytes\n")
    write_json(directory / ARCHIVE_RECEIPT, {"archive_sha256": sha256_bytes(archive.read_bytes()),
                                             "tag": "v0.2.0", "source_sha": source})
    write_json(directory / CONSUMER, {"result": "passed", "source_sha": source, "isolated_prefix": True,
                                      "results": {"c": {}, "cpp": {}},
                                      "api_behaviors": {b: {"c": "passed", "cpp": "passed"} for b in BEHAVIORS}})
    return archive


def edit(path: Path, change: Callable[[dict[str, Any]], None]) -> None:
    value = json.loads(path.read_text())
    change(value)
    write_json(path, value)


def evidence_controls(base: Path, repo: Path, producer: str, source: str) -> tuple[int, int]:
    positives = rejected = 0
    archive = make_evidence(base / "evidence", source)
    common = ["--tag", "v0.2.0", "--source-sha", source, "--repo-root", str(repo), "--source-archive", str(archive)]
    done = run_cli("--check-evidence", str(base / "evidence"), *common)
    if done.returncode != 0 or "PASS: v02 delivery evidence binds 6 families" not in done.stdout:
        raise SystemExit(f"complete evidence was not accepted: {done.stderr.strip()}")
    positives += 1

    def mutate(label: str, code: str, change: Callable[[Path], Path | None]) -> None:
        nonlocal rejected
        work = base / f"mut-{rejected}"
        shutil.copytree(base / "evidence", work)
        replacement = change(work)
        args = list(common)
        args[args.index("--source-archive") + 1] = str(replacement if isinstance(replacement, Path) else archive)
        result = run_cli("--check-evidence", str(work), *args)
        if result.returncode == 0:
            raise SystemExit(f"delivery self-test accepted {label}")
        if f"REJECT {code}:" not in result.stderr:
            raise SystemExit(f"delivery self-test rejected {label} for the wrong reason: {result.stderr.strip()}")
        rejected += 1

    for name in EVIDENCE_NAMES:
        mutate(f"omitted {name}", "evidence-missing", lambda w, n=name: (w / n).unlink())
    mutate("missing source archive", "evidence-missing", lambda w: w / "absent.tar.gz")
    mutate("corpus bytes not bound by the sidecar", "sidecar-binding", lambda w: (w / CORPUS).write_bytes(b"{}\n"))
    mutate("sidecar for another version", "sidecar-binding",
           lambda w: edit(w / SIDECAR, lambda d: d.update(version="0.2.1", tag="v0.2.1")))
    mutate("sidecar ledger blob differs from the tag", "owner-ledger",
           lambda w: edit(w / SIDECAR, lambda d: d.update(ledger_blob="0" * 40)))
    mutate("fuzz receipt for another SHA", "fuzz-binding",
           lambda w: edit(w / FUZZ, lambda d: d.update(source_sha="b" * 40)))
    mutate("fuzz workflow attempt zero", "fuzz-binding",
           lambda w: edit(w / FUZZ, lambda d: d["workflow"].update(attempt=0)))
    mutate("unsupported campaign", "owner-fuzz", lambda w: edit(w / FUZZ, lambda d: d.update(status="unsupported")))
    mutate("fast-only campaign", "owner-fuzz", lambda w: edit(w / FUZZ, lambda d: d.update(mode="fast")))
    mutate("incompatible benchmark workload", "owner-performance",
           lambda w: edit(w / PERFORMANCE, lambda d: d["workload"].update(id="other-workload")))
    mutate("performance for another SHA without reuse", "performance-binding",
           lambda w: edit(w / PERFORMANCE, lambda d: d["source"]["candidate"].update(sha=producer)))
    mutate("missing downloaded C++ result", "consumer-binding",
           lambda w: edit(w / CONSUMER, lambda d: d["results"].pop("cpp")))
    mutate("partial C/C++ behavior coverage", "consumer-binding",
           lambda w: edit(w / CONSUMER, lambda d: d["api_behaviors"]["rtc_catch_up"].update(cpp="failed")))
    mutate("archive receipt for other bytes", "owner-archive",
           lambda w: edit(w / ARCHIVE_RECEIPT, lambda d: d.update(archive_sha256="0" * 64)))

    # A justified reuse of an earlier producer is accepted only when every covered input is identical.
    reuse_dir = base / "reuse"
    shutil.copytree(base / "evidence", reuse_dir)
    edit(reuse_dir / PERFORMANCE, lambda d: d["source"]["candidate"].update(sha=producer))
    write_json(reuse_dir / REUSE_FILE, {"performance": {
        "original_producer_sha": producer, "justification": "Only a non-covered notes file changed after the producer."}})
    reuse_args = list(common)
    done = run_cli("--check-evidence", str(reuse_dir), *reuse_args)
    if done.returncode != 0 or "reused=1" not in done.stdout:
        raise SystemExit(f"justified reuse was not accepted: {done.stderr.strip()}")
    positives += 1
    for label, code, change in (
        ("reuse with relabelled producer", "reuse-invalid",
         lambda d: d["performance"].update(original_producer_sha=source)),
        ("reuse without justification", "reuse-invalid", lambda d: d["performance"].update(justification="ok")),
    ):
        bad = base / f"reuse-bad-{rejected}"
        shutil.copytree(reuse_dir, bad)
        edit(bad / REUSE_FILE, change)
        result = run_cli("--check-evidence", str(bad), *common)
        if result.returncode == 0 or f"REJECT {code}:" not in result.stderr:
            raise SystemExit(f"delivery self-test mishandled {label}: {result.stderr.strip()}")
        rejected += 1
    (repo / "src/file").write_text("changed covered input\n")
    env = ["-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false"]
    subprocess.run(["git", "-C", str(repo), *env, "commit", "-q", "-am", "covered change"], check=True, capture_output=True)
    changed = git(repo, "rev-parse", "HEAD")
    subprocess.run(["git", "-C", str(repo), "tag", "v0.2.1", changed], check=True, capture_output=True)
    drift = base / "reuse-drift"
    shutil.copytree(reuse_dir, drift)
    edit(drift / FUZZ, lambda d: d.update(source_sha=changed))
    edit(drift / SIDECAR, lambda d: d.update(source_sha=changed, tag="v0.2.1", version="0.2.1"))
    edit(drift / CONSUMER, lambda d: d.update(source_sha=changed))
    edit(drift / PERFORMANCE, lambda d: d["source"]["candidate"].update(sha=producer))
    result = run_cli("--check-evidence", str(drift), "--tag", "v0.2.1", "--source-sha", changed,
                     "--repo-root", str(repo), "--source-archive", str(archive))
    if result.returncode == 0 or "REJECT reuse-input-changed:" not in result.stderr:
        raise SystemExit(f"delivery self-test reused a producer across a changed covered input: {result.stderr.strip()}")
    rejected += 1
    return positives, rejected


def stage_fixture(base: Path) -> tuple[dict[str, Any], dict[str, Any], Path, Path]:
    head, merge, vhead, source = "1" * 40, "2" * 40, "3" * 40, "4" * 40
    final = base / "final-readback"
    final.mkdir(parents=True)
    names = list(EVIDENCE_NAMES) + ["gabbaboy-core-linux-x64.tar.gz", "SHA256SUMS", "release-receipt.json"]
    assets, live_assets = [], []
    for index, name in enumerate(names, start=1):
        data = f"bytes of {name}\n".encode()
        (final / name).write_bytes(data)
        assets.append({"name": name, "size": len(data), "sha256": sha256_bytes(data)})
        live_assets.append({"id": 100 + index, "name": name, "size": len(data), "digest": "sha256:" + sha256_bytes(data)})
    (base / "validation-download").mkdir()
    checks = lambda sha: {"check_runs": [{"name": n, "head_sha": sha, "status": "completed", "conclusion": "success",
                                           "app": {"id": i, "slug": APP_SLUG}} for n, i in REQUIRED_CONTEXTS.items()]}
    pr = lambda number, h, m: {"number": number, "state": "closed", "merged_at": "2026-10-20T00:00:00Z",
                               "base": {"ref": "main"}, "head": {"sha": h}, "merge_commit_sha": m}
    table = {
        api("pulls/80"): pr(80, head, merge), api(f"commits/{head}/check-runs?per_page=100"): checks(head),
        api("pulls/70"): pr(70, vhead, source), api(f"commits/{vhead}/check-runs?per_page=100"): checks(vhead),
        api("actions/runs/900"): {"run_attempt": 2},
        api("actions/runs/900/attempts/2"): {"head_sha": head, "status": "completed", "conclusion": "success"},
        api("releases/555"): {"draft": False, "published_at": "2026-10-21T00:00:00Z", "tag_name": "v0.2.0"},
        api("commits/v0.2.0"): {"sha": source},
        api("releases/555/assets?per_page=100"): live_assets,
    }
    by_name = {a["name"]: a["sha256"] for a in assets}
    receipt = {
        "schema_version": 1, "stage": "published", "required_checks": sorted(REQUIRED_CONTEXTS),
        "phase_pr": {"number": 80, "head_sha": head, "merge_commit_sha": merge},
        "version_pr": {"number": 70, "head_sha": vhead, "merge_commit_sha": source},
        "workflow_runs": [{"id": 900, "attempt": 2}], "source_sha": source, "tag": "v0.2.0", "release_id": 555,
        "sidecars": {n: by_name[n] for n in EVIDENCE_NAMES},
        "source_archive": {"sha256": "5" * 64, "receipt_sha256": by_name[ARCHIVE_RECEIPT]},
        "asset_readback": {"assets": assets}, "publication": {"published_at": "2026-10-21T00:00:00Z"},
    }
    return receipt, table, final, base / "validation-download"


def stage_controls(base: Path) -> tuple[int, int]:
    receipt, table, final, validation = stage_fixture(base)
    positives = rejected = 0

    def run(stage: str, rec: dict[str, Any], tab: dict[str, Any], published: Path | None = final,
            earlier: Path | None = validation) -> subprocess.CompletedProcess[str]:
        write_json(base / "receipt.json", rec)
        write_json(base / "readback.json", tab)
        args = ["--stage", stage, "--receipt", str(base / "receipt.json"), "--readback-fixture", str(base / "readback.json")]
        if published and stage == "published":
            args += ["--published-dir", str(published)]
        if earlier and stage == "published":
            args += ["--validation-dir", str(earlier)]
        return run_cli(*args)

    done = run("published", receipt, table)
    if done.returncode != 0 or "PASS: published release" not in done.stdout:
        raise SystemExit(f"complete published receipt was not accepted: {done.stderr.strip()}")
    positives += 1
    phase = {k: receipt[k] for k in ("schema_version", "required_checks", "phase_pr", "workflow_runs")}
    phase["stage"] = "phase-pr"
    done = run("phase-pr", phase, table)
    if done.returncode != 0:
        raise SystemExit(f"phase PR receipt was not accepted: {done.stderr.strip()}")
    positives += 1

    def expect(label: str, code: str, stage: str, mutate_rec: Callable[[dict], None] | None = None,
               mutate_tab: Callable[[dict], None] | None = None, **kwargs: Any) -> None:
        nonlocal rejected
        rec = json.loads(json.dumps(receipt if stage == "published" else phase))
        tab = json.loads(json.dumps(table))
        if mutate_rec:
            mutate_rec(rec)
        if mutate_tab:
            mutate_tab(tab)
        result = run(stage, rec, tab, **kwargs)
        if result.returncode == 0:
            raise SystemExit(f"delivery self-test accepted {label}")
        if f"REJECT {code}:" not in result.stderr:
            raise SystemExit(f"delivery self-test rejected {label} for the wrong reason: {result.stderr.strip()}")
        rejected += 1

    expect("a draft release claimed as published", "publication-mismatch", "published",
           mutate_tab=lambda t: t[api("releases/555")].update(draft=True))
    expect("a tag moved to another commit", "tag-mismatch", "published",
           mutate_tab=lambda t: t[api("commits/v0.2.0")].update(sha="9" * 40))
    expect("version merge that is not the tag source", "pr-mismatch", "published",
           mutate_rec=lambda r: r["version_pr"].update(merge_commit_sha="8" * 40))
    expect("a changed live asset digest", "readback-mismatch", "published",
           mutate_tab=lambda t: t[api("releases/555/assets?per_page=100")][0].update(digest="sha256:" + "0" * 64))
    expect("a duplicate live asset name", "readback-mismatch", "published",
           mutate_tab=lambda t: t[api("releases/555/assets?per_page=100")].append(
               dict(t[api("releases/555/assets?per_page=100")][0], id=999)))
    expect("an extra live asset", "readback-mismatch", "published",
           mutate_tab=lambda t: t[api("releases/555/assets?per_page=100")].append(
               {"id": 998, "name": "extra.bin", "size": 1, "digest": "sha256:" + "1" * 64}))
    expect("a stale workflow attempt", "runs-mismatch", "published",
           mutate_rec=lambda r: r["workflow_runs"][0].update(attempt=1))
    expect("a failed workflow attempt", "runs-mismatch", "phase-pr",
           mutate_tab=lambda t: t[api("actions/runs/900/attempts/2")].update(conclusion="failure"))
    expect("a stale required check", "checks-mismatch", "phase-pr",
           mutate_tab=lambda t: t[api(f"commits/{'1' * 40}/check-runs?per_page=100")]["check_runs"][0].update(head_sha="7" * 40))
    expect("a missing required check", "checks-mismatch", "phase-pr",
           mutate_tab=lambda t: t[api(f"commits/{'1' * 40}/check-runs?per_page=100")]["check_runs"].pop())
    expect("an unmerged phase PR claimed merged", "pr-mismatch", "published",
           mutate_tab=lambda t: t[api("pulls/80")].update(merged_at=None, state="open"))
    expect("a self-reported success-only receipt", "receipt-malformed", "published",
           mutate_rec=lambda r: (r.pop("phase_pr"), r.update(result="success")))
    expect("an earlier validation download reused as readback", "readback-mismatch", "published",
           earlier=final)
    forged = base / "forged"
    shutil.copytree(final, forged)
    (forged / "SHA256SUMS").write_bytes(b"forged\n")
    expect("a forged final readback byte", "readback-mismatch", "published", published=forged)
    return positives, rejected


def run_self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="gb-delivery-selftest.") as name:
        base = Path(name)
        repo, producer, source = make_fixture_repo(base)
        p1, r1 = evidence_controls(base, repo, producer, source)
        p2, r2 = stage_controls(base / "stage")  # separate tree keeps the fixtures independent
        positives, controls = p1 + p2, r1 + r2
        # The real owner validators must reject a forged receipt that reaches them through this entry point.
        forged = base / "forged-owner"
        forged.mkdir()
        (forged / "bad.json").write_text("{}\n")
        owner_controls = 0
        for family, option in (("performance", "--verify"), ("fuzz", "--verify")):
            owner = ROOT / OWNERS[family]
            done = subprocess.run([sys.executable, "-I", str(owner), option, str(forged / "bad.json")],
                                  cwd=ROOT, capture_output=True, text=True, timeout=120)
            if done.returncode == 0:
                raise SystemExit(f"real {family} owner validator accepted a forged receipt")
            owner_controls += 1
        if positives < 4 or controls < 30 or owner_controls != 2:
            raise SystemExit("delivery self-test inventory is too small to qualify")
        print(f"PASS: delivery checker positives={positives} rejected_controls={controls} "
              f"real_owner_rejections={owner_controls}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
