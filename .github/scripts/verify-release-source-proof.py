#!/usr/bin/env python3
"""Validate the frozen release source receipt against live PR/check-run evidence."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


REQUIRED_CONTEXTS = {
    "required-native": 15368,
    "fixture-repro": 15368,
    "preview-package-smoke": 15368,
}
EXPECTED_APP_SLUG = "github-actions"
EXPECTED_REPOSITORY = "szTheory/gabbaboy"
# GitHub's check-run objects carry no `repository` member; the repository is the prefix of the object's own API URL and of
# its html_url. Both are matched as strict prefixes ending in a slash, so szTheory/gabbaboy-evil cannot pass.
API_CHECK_RUN_PREFIX = f"https://api.github.com/repos/{EXPECTED_REPOSITORY}/check-runs/"
HTML_PREFIX = f"https://github.com/{EXPECTED_REPOSITORY}/"


def check_run_in_expected_repository(run: dict[str, Any]) -> bool:
    url, html_url = run.get("url"), run.get("html_url")
    return (isinstance(url, str) and url.startswith(API_CHECK_RUN_PREFIX)
            and re.fullmatch(r"[0-9]+", url[len(API_CHECK_RUN_PREFIX):]) is not None
            and isinstance(html_url, str) and html_url.startswith(HTML_PREFIX)
            and isinstance(run.get("check_suite"), dict))


def validate(receipt: dict[str, Any], pr: dict[str, Any], checks: dict[str, Any],
             tag: str, source_sha: str, release_id: str) -> None:
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag) or not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("expected tag or source SHA is malformed")
    if (receipt.get("tag_name") != tag or receipt.get("version") != tag[1:]
            or receipt.get("source_sha") != source_sha or str(receipt.get("release_id")) != release_id
            or receipt.get("draft") is not True or receipt.get("source_clean") is not True):
        raise ValueError("source receipt is not bound to the frozen tag, version, source, release ID and draft")

    proof = receipt.get("prior_pr_proof")
    if not isinstance(proof, dict):
        raise ValueError("source receipt is missing its protected-PR proof")
    pr_number = proof.get("pr_number")
    head_sha = proof.get("head_sha")
    if (not isinstance(pr_number, int) or pr_number < 1
            or not isinstance(head_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", head_sha)
            or proof.get("merge_commit_sha") != source_sha or proof.get("required_checks") != "passed"):
        raise ValueError("source receipt contains stale or incomplete protected-PR proof fields")
    if (pr.get("number") != pr_number or pr.get("state") != "closed" or not pr.get("merged_at")
            or pr.get("base", {}).get("ref") != "main" or pr.get("merge_commit_sha") != source_sha
            or pr.get("head", {}).get("sha") != head_sha
            or pr.get("base", {}).get("repo", {}).get("full_name") != EXPECTED_REPOSITORY
            or pr.get("head", {}).get("repo", {}).get("full_name") != EXPECTED_REPOSITORY):
        raise ValueError("live pull request does not match the source receipt's merged main PR")

    observed: dict[str, list[dict[str, Any]]] = {}
    for run in checks.get("check_runs", []):
        if run.get("name") in REQUIRED_CONTEXTS:
            observed.setdefault(run["name"], []).append(run)
    for context, app_id in REQUIRED_CONTEXTS.items():
        runs = observed.get(context, [])
        if not runs:
            raise ValueError(f"recorded protected context {context!r} has no exact-head check-run evidence")
        for run in runs:
            if run.get("head_sha") != head_sha:
                raise ValueError(f"protected context {context!r} has stale check evidence")
            if not check_run_in_expected_repository(run):
                raise ValueError(f"protected context {context!r} belongs to the wrong repository")
            if run.get("status") != "completed" or run.get("conclusion") != "success":
                raise ValueError(f"protected context {context!r} is incomplete or unsuccessful")
            app = run.get("app") or {}
            if app.get("id") != app_id or app.get("slug") != EXPECTED_APP_SLUG:
                raise ValueError(f"protected context {context!r} came from the wrong GitHub App")


# --- Reuse of a rehearsal run's performance receipt (WR-01) -------------------------------------------------------------
#
# release.yml may reuse the advisory performance receipt a rehearsal run produced, instead of measuring again, only when
# that run provably built the tagged tree. A branch name or an artifact name alone proves nothing: anyone who can push
# `rehearsal/v...` can run their own copy of the workflow and upload any artifact with the expected name. So the run is
# bound by workflow path, event, completed success, branch, repository (no fork) and by the tagged tree, resolved from git
# objects (head_sha equal to the tag source, or a head whose tree is the tag source's tree, which also means the workflow
# file that ran was the tagged one). The artifact is then bound to that exact run and attempt. Only the newest successful
# run is a candidate: if it is stale or ineligible the receipt is not reused and a fresh measurement follows, an older run
# is never substituted behind it.
REHEARSAL_WORKFLOW_PATH = ".github/workflows/release-rehearsal.yml"
REHEARSAL_EVENTS = ("push", "workflow_dispatch")
FULL_SHA = re.compile(r"[0-9a-f]{40}")
MAX_RUN_LIST = 100
MAX_RECEIPT_BYTES = 8 * 1024 * 1024
TreeOf = Callable[[str], "str | None"]


def git_tree_of(revision: str) -> "str | None":
    """The tree object id of a full commit id, read from the local object database; None when it cannot be proved."""
    if not FULL_SHA.fullmatch(revision):
        return None
    try:
        result = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{revision}^{{tree}}"],
                                capture_output=True, text=True, check=False, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    tree = result.stdout.strip()
    return tree if result.returncode == 0 and FULL_SHA.fullmatch(tree) else None


def _is_id(value: Any) -> bool:
    return type(value) is int and value > 0


def _repository_name(run: dict[str, Any], key: str) -> Any:
    member = run.get(key)
    return member.get("full_name") if isinstance(member, dict) else None


def _rehearsal_timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"rehearsal-postdates-tag: {label} missing or invalid")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as error:
        raise ValueError(f"rehearsal-postdates-tag: {label} missing or invalid") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"rehearsal-postdates-tag: {label} missing or invalid")
    return parsed.astimezone(timezone.utc)


def validate_rehearsal_run(run: Any, tag: str, source_sha: str, repo: str, tree_of: TreeOf,
                           pr_head: str | None = None, not_after: dict[str, Any] | None = None) -> None:
    """Raise ValueError unless this run object is the successful rehearsal of exactly the tagged tree."""
    if not isinstance(run, dict) or not _is_id(run.get("id")) or not _is_id(run.get("run_attempt")):
        raise ValueError("rehearsal run object is malformed")
    path = run.get("path")
    if not isinstance(path, str) or path.split("@", 1)[0] != REHEARSAL_WORKFLOW_PATH:
        raise ValueError("run is not a run of the rehearsal workflow")
    if run.get("event") not in REHEARSAL_EVENTS:
        raise ValueError(f"rehearsal run was triggered by {run.get('event')!r}, not push or workflow_dispatch")
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        raise ValueError("rehearsal run has not completed successfully")
    if run.get("head_branch") != f"rehearsal/{tag}":
        raise ValueError(f"rehearsal run ran on branch {run.get('head_branch')!r}, not rehearsal/{tag}")
    if _repository_name(run, "repository") != repo or _repository_name(run, "head_repository") != repo:
        raise ValueError("rehearsal run belongs to another repository or a fork")
    head = run.get("head_sha")
    if not isinstance(head, str) or not FULL_SHA.fullmatch(head):
        raise ValueError("rehearsal run head is not a full commit id")
    if head != source_sha:
        head_tree, source_tree = tree_of(head), tree_of(source_sha)
        if head_tree is None or source_tree is None:
            raise ValueError("the tree of the rehearsal head or of the tagged source cannot be proved from git objects")
        if head_tree != source_tree:
            raise ValueError("rehearsal run head tree differs from the tagged tree")
    if pr_head is not None and head != pr_head:
        raise ValueError("rehearsal-not-version-pr-head: the run head is not the merged version PR head")
    if not_after is not None:
        merged_at = _rehearsal_timestamp(not_after.get("merged_at"), "merged_at")
        attempt_jobs = not_after.get("attempt_jobs")
        jobs = attempt_jobs.get("jobs") if isinstance(attempt_jobs, dict) else None
        if (not isinstance(attempt_jobs, dict) or type(attempt_jobs.get("total_count")) is not int
                or not isinstance(jobs, list) or not jobs or len(jobs) != attempt_jobs["total_count"]
                or len(jobs) > MAX_RUN_LIST):
            raise ValueError("rehearsal-postdates-tag: attempt jobs are missing, truncated or malformed")
        completed = []
        for job in jobs:
            if (not isinstance(job, dict) or job.get("run_id") != run["id"]
                    or job.get("run_attempt") != run["run_attempt"]):
                raise ValueError("rehearsal-postdates-tag: attempt jobs do not match the selected run and attempt")
            completed.append(_rehearsal_timestamp(job.get("completed_at"), "attempt job completed_at"))
        if max(completed) > merged_at:
            raise ValueError("rehearsal-postdates-tag: the selected run attempt completed after the version PR merged")


def bind_rehearsal_run(document: Any, tag: str, source_sha: str, repo: str, tree_of: TreeOf,
                       pr_head: str, merged_at: str | None = None,
                       attempt_jobs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Select the newest successful rehearsal of the tagged tree, then bind it to the reviewed PR and merge time."""
    if (merged_at is None) != (attempt_jobs is None):
        raise ValueError("rehearsal-postdates-tag: incomplete not_after binding")
    run = select_performance_run(document, tag, source_sha, repo, tree_of)
    not_after = None if merged_at is None else {"merged_at": merged_at, "attempt_jobs": attempt_jobs}
    validate_rehearsal_run(run, tag, source_sha, repo, tree_of, pr_head=pr_head, not_after=not_after)
    return run


def select_performance_run(document: Any, tag: str, source_sha: str, repo: str, tree_of: TreeOf) -> dict[str, Any]:
    """The newest successful rehearsal run of this tag, validated; never an older run behind a stale newest one."""
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag) or not FULL_SHA.fullmatch(source_sha) \
            or not re.fullmatch(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+", repo):
        raise ValueError("tag, source SHA or repository is malformed")
    runs = document.get("workflow_runs") if isinstance(document, dict) else None
    if not isinstance(runs, list) or len(runs) > MAX_RUN_LIST:
        raise ValueError("workflow run list is malformed or exceeds the bound")
    if not runs:
        raise ValueError("no successful rehearsal run of this tag exists")
    ids = [run.get("id") if isinstance(run, dict) else None for run in runs]
    if any(not _is_id(value) for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("workflow run list has a malformed or repeated run id")
    newest = max(runs, key=lambda run: run["id"])
    validate_rehearsal_run(newest, tag, source_sha, repo, tree_of)
    return newest


def select_performance_artifact(run: dict[str, Any], document: Any) -> str:
    """The one artifact that this exact run and attempt uploaded, or ValueError."""
    if not _is_id(run.get("id")) or not _is_id(run.get("run_attempt")):
        raise ValueError("selected run is malformed")
    name = f"rehearsal-performance-{run['id']}-{run['run_attempt']}"
    artifacts = document.get("artifacts") if isinstance(document, dict) else None
    if (not isinstance(artifacts, list) or len(artifacts) > MAX_RUN_LIST or document.get("total_count") != len(artifacts)
            or any(not isinstance(item, dict) for item in artifacts)):
        raise ValueError("artifact list is malformed, truncated or exceeds the bound")
    matches = [item for item in artifacts if item.get("name") == name]
    if len(matches) != 1:
        raise ValueError(f"the run uploaded {len(matches)} artifacts named {name}, not exactly one")
    artifact = matches[0]
    if artifact.get("expired") is not False:
        raise ValueError("the performance artifact has expired")
    size = artifact.get("size_in_bytes")
    if type(size) is not int or not 0 < size <= MAX_RECEIPT_BYTES:
        raise ValueError("the performance artifact is empty or exceeds the receipt size bound")
    origin = artifact.get("workflow_run")
    if not isinstance(origin, dict):
        raise ValueError("the performance artifact does not name its producing run")
    if origin.get("id") != run["id"] or origin.get("head_sha") != run.get("head_sha") \
            or origin.get("head_branch") != run.get("head_branch"):
        raise ValueError("the performance artifact was produced by a different run, head or branch")
    own = run.get("repository", {}).get("id") if isinstance(run.get("repository"), dict) else None
    if not _is_id(origin.get("repository_id")) or origin.get("repository_id") != origin.get("head_repository_id") \
            or origin.get("repository_id") != own:
        raise ValueError("the performance artifact comes from a fork or an unknown repository")
    return name


def fixture() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    head = "a" * 40
    source = "b" * 40
    receipt = {"tag_name": "v0.1.0", "version": "0.1.0", "source_sha": source,
               "release_id": "407367131", "draft": True, "source_clean": True,
               "prior_pr_proof": {"pr_number": 13, "head_sha": head,
                                  "merge_commit_sha": source, "required_checks": "passed"}}
    pr = {"number": 13, "state": "closed", "merged_at": "2026-10-08T00:00:00Z",
          "base": {"ref": "main", "repo": {"full_name": EXPECTED_REPOSITORY}},
          "head": {"sha": head, "repo": {"full_name": EXPECTED_REPOSITORY}},
          "merge_commit_sha": source}
    # The shape GitHub returns from commits/{sha}/check-runs: url, html_url and check_suite, no `repository`.
    checks = {"check_runs": [
        {"id": 1000 + index, "name": name, "head_sha": head, "status": "completed", "conclusion": "success",
         "url": f"{API_CHECK_RUN_PREFIX}{1000 + index}",
         "html_url": f"{HTML_PREFIX}actions/runs/1/job/{1000 + index}",
         "check_suite": {"id": 2000 + index},
         "app": {"id": 15368, "slug": EXPECTED_APP_SLUG}}
        for index, name in enumerate(REQUIRED_CONTEXTS)
    ]}
    return receipt, pr, checks


def run_self_test() -> None:
    receipt, pr, checks = fixture()
    validate(receipt, pr, checks, "v0.1.0", "b" * 40, "407367131")
    duplicate_successes = json.loads(json.dumps(checks))
    duplicate_successes["check_runs"].append(dict(duplicate_successes["check_runs"][0]))
    validate(receipt, pr, duplicate_successes, "v0.1.0", "b" * 40, "407367131")
    mutations = {
        "receipt source mismatch": lambda r, p, c: r.update(source_sha="c" * 40),
        "stale merged PR": lambda r, p, c: p.update(merge_commit_sha="c" * 40),
        "missing required context": lambda r, p, c: c["check_runs"].pop(),
        "failed required context": lambda r, p, c: c["check_runs"][0].update(conclusion="failure"),
        "stale required context": lambda r, p, c: c["check_runs"][0].update(head_sha="c" * 40),
        "wrong required-check App": lambda r, p, c: c["check_runs"][0]["app"].update(id=1),
        "wrong required-check App identity": lambda r, p, c: c["check_runs"][0]["app"].update(slug="other-app"),
        "wrong base repository": lambda r, p, c: p["base"]["repo"].update(full_name="other/repository"),
        "wrong head repository": lambda r, p, c: p["head"]["repo"].update(full_name="other/repository"),
        "check-run URL of another repository": lambda r, p, c: c["check_runs"][0].update(
            url="https://api.github.com/repos/other/repository/check-runs/1000"),
        "check-run URL missing": lambda r, p, c: c["check_runs"][0].pop("url"),
        "check-run URL with a lookalike repository prefix": lambda r, p, c: c["check_runs"][0].update(
            url="https://api.github.com/repos/szTheory/gabbaboy-evil/check-runs/1000"),
        "check-run URL with the repository only as a substring": lambda r, p, c: c["check_runs"][0].update(
            url="https://api.github.com/repos/other/repository/check-runs/1000?x=szTheory/gabbaboy/check-runs/"),
        "check-run URL with a non-numeric id": lambda r, p, c: c["check_runs"][0].update(
            url=API_CHECK_RUN_PREFIX + "1000/../../x"),
        "check-run html_url of another repository": lambda r, p, c: c["check_runs"][0].update(
            html_url="https://github.com/other/repository/actions/runs/1/job/1000"),
        "check-run html_url lookalike prefix": lambda r, p, c: c["check_runs"][0].update(
            html_url="https://github.com/szTheory/gabbaboy-evil/actions/runs/1/job/1000"),
        "check-run without a check_suite": lambda r, p, c: c["check_runs"][0].pop("check_suite"),
        "old repository-only shape without URLs": lambda r, p, c: (
            c["check_runs"][0].pop("url"), c["check_runs"][0].pop("html_url"),
            c["check_runs"][0].update(repository={"full_name": EXPECTED_REPOSITORY})),
        "mixed duplicate records": lambda r, p, c: c["check_runs"].append(
            {**c["check_runs"][0], "conclusion": "failure"}),
    }
    for label, mutate in mutations.items():
        r = json.loads(json.dumps(receipt))
        p = json.loads(json.dumps(pr))
        c = json.loads(json.dumps(checks))
        mutate(r, p, c)
        try:
            validate(r, p, c, "v0.1.0", "b" * 40, "407367131")
        except ValueError:
            continue
        raise SystemExit(f"self-test accepted {label}")
    print("PASS: saved source receipt binds merged PR and exact-head required checks")
    print("PASS: source-proof self-tests reject stale, missing, failed and wrong-App evidence")


REHEARSAL_TAG = "v0.2.1"
REHEARSAL_SOURCE = "b" * 40
REHEARSAL_REPO_ID = 1403278117


def rehearsal_fixture(base: "dict[str, Any] | None" = None,
                      artifact_base: "dict[str, Any] | None" = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    """A newest successful rehearsal run, its artifact list and the tree table the judge resolves heads through.

    With a captured run and artifact (real GitHub objects, extra members and all) only the identity members are replaced."""
    head = "c" * 40
    run = json.loads(json.dumps(base)) if base else {"repository": {"full_name": EXPECTED_REPOSITORY},
                                                      "head_repository": {"full_name": EXPECTED_REPOSITORY}}
    run.update(id=9000, run_attempt=2, path=REHEARSAL_WORKFLOW_PATH, event="push", status="completed", conclusion="success",
               head_branch=f"rehearsal/{REHEARSAL_TAG}", head_sha=head, name="release-rehearsal")
    run["repository"] = dict(run.get("repository") or {}, id=REHEARSAL_REPO_ID, full_name=EXPECTED_REPOSITORY)
    run["head_repository"] = dict(run.get("head_repository") or {}, id=REHEARSAL_REPO_ID, full_name=EXPECTED_REPOSITORY)
    artifact = json.loads(json.dumps(artifact_base)) if artifact_base else {"expired": False}
    artifact.update(name="rehearsal-performance-9000-2", expired=False, size_in_bytes=2048,
                    workflow_run={"id": 9000, "head_branch": run["head_branch"], "head_sha": head,
                                  "repository_id": REHEARSAL_REPO_ID, "head_repository_id": REHEARSAL_REPO_ID})
    other = dict(artifact, name="rehearsal-performance-9000-1", id=2)
    artifact["id"] = 1
    trees = {head: "1" * 40, REHEARSAL_SOURCE: "1" * 40}
    return run, {"total_count": 2, "artifacts": [other, artifact]}, trees


def rehearsal_reuse_self_test(base_run: "dict[str, Any] | None" = None,
                              base_artifact: "dict[str, Any] | None" = None) -> int:
    """Positive selections and each independently wrong producer, event, source, branch, fork or artifact. A control only counts
    when the refusal names its own reason; an unrelated refusal would leave the intended defect unexercised."""
    def select(runs: list[dict[str, Any]], trees: dict[str, str]) -> dict[str, Any]:
        return select_performance_run({"total_count": len(runs), "workflow_runs": runs}, REHEARSAL_TAG, REHEARSAL_SOURCE,
                                      EXPECTED_REPOSITORY, trees.get)

    run, artifacts, trees = rehearsal_fixture(base_run, base_artifact)
    controls = 0

    # Positives: a head equal to the tagged source, and a different head with the same tree, the second behind an older run.
    def require(condition: bool, label: str) -> None:
        if not condition:
            raise SystemExit(f"rehearsal-reuse self-test: positive control failed: {label}")

    chosen = select([run], trees)
    require(chosen["id"] == 9000 and select_performance_artifact(chosen, artifacts) == "rehearsal-performance-9000-2",
            "equal-tree head and its own attempt's artifact")
    exact = dict(run, head_sha=REHEARSAL_SOURCE)
    require(select([exact], {})["head_sha"] == REHEARSAL_SOURCE, "an exact head needs no tree lookup")
    older = dict(run, id=8000, head_sha="d" * 40)
    require(select([older, run], {**trees, "d" * 40: "2" * 40})["id"] == 9000, "the newest valid run is chosen over an older one")

    merged_at = "2026-10-26T02:27:35Z"
    attempt_jobs = {"total_count": 2, "jobs": [
        {"run_id": run["id"], "run_attempt": run["run_attempt"], "completed_at": "2026-10-26T02:15:10Z"},
        {"run_id": run["id"], "run_attempt": run["run_attempt"], "completed_at": "2026-10-26T02:03:44Z"},
    ]}
    bound = bind_rehearsal_run({"total_count": 1, "workflow_runs": [run]}, REHEARSAL_TAG, REHEARSAL_SOURCE,
                               EXPECTED_REPOSITORY, trees.get, run["head_sha"], merged_at, attempt_jobs)
    require(bound["id"] == run["id"], "PR-head and pre-merge attempt binding")

    def refuse(label: str, reason: str, call: Callable[[], Any]) -> None:
        nonlocal controls
        try:
            call()
        except ValueError as error:
            if reason not in str(error):
                raise SystemExit(f"rehearsal-reuse self-test: {label}: refused for the wrong reason: {error}")
            controls += 1
            return
        raise SystemExit(f"rehearsal-reuse self-test accepted {label}")

    def run_defect(label: str, reason: str, **changes: Any) -> None:
        refuse(label, reason, lambda: select([dict(run, **changes)], trees))

    late_jobs = json.loads(json.dumps(attempt_jobs))
    late_jobs["jobs"][0]["completed_at"] = "2026-10-26T02:27:36Z"
    refuse("an attempt completed after the version PR merged", "rehearsal-postdates-tag",
           lambda: bind_rehearsal_run({"workflow_runs": [run]}, REHEARSAL_TAG, REHEARSAL_SOURCE,
                                      EXPECTED_REPOSITORY, trees.get, run["head_sha"], merged_at, late_jobs))

    run_defect("another workflow", "not a run of the rehearsal workflow", path=".github/workflows/release-please.yml")
    run_defect("a workflow path that only starts like the rehearsal", "not a run of the rehearsal workflow",
               path=REHEARSAL_WORKFLOW_PATH + "x")
    run_defect("a missing workflow path", "not a run of the rehearsal workflow", path=None)
    for event in ("pull_request", "pull_request_target", "schedule", "workflow_run", "repository_dispatch", None):
        run_defect(f"event {event}", "was triggered by", event=event)
    for conclusion in ("failure", "cancelled", "skipped", "timed_out", "neutral", None):
        run_defect(f"conclusion {conclusion}", "not completed successfully", conclusion=conclusion)
    for status in ("in_progress", "queued", None):
        run_defect(f"status {status}", "not completed successfully", status=status)
    run_defect("branch main", "ran on branch", head_branch="main")
    run_defect("another tag's rehearsal branch", "ran on branch", head_branch="rehearsal/v9.9.9")
    run_defect("a branch that only starts like the rehearsal branch", "ran on branch", head_branch=f"rehearsal/{REHEARSAL_TAG}-x")
    run_defect("a run of another repository", "another repository or a fork",
               repository=dict(run["repository"], full_name="other/repository"))
    run_defect("a run from a fork head", "another repository or a fork",
               head_repository=dict(run["head_repository"], full_name="fork/gabbaboy"))
    run_defect("a run with no head repository", "another repository or a fork", head_repository=None)
    run_defect("a head that is not a full commit id", "not a full commit id", head_sha="c" * 39)
    run_defect("a zero attempt", "malformed", run_attempt=0)
    run_defect("a boolean attempt", "malformed", run_attempt=True)
    refuse("a head whose objects are absent", "cannot be proved from git objects",
           lambda: select([run], {REHEARSAL_SOURCE: "1" * 40}))
    refuse("a tagged source whose tree cannot be resolved", "cannot be proved from git objects",
           lambda: select([run], {run["head_sha"]: "1" * 40}))
    refuse("a head of another tree", "head tree differs",
           lambda: select([run], {run["head_sha"]: "2" * 40, REHEARSAL_SOURCE: "1" * 40}))
    # The newest successful run governs. A stale newest run is refused although an older run of the right tree exists.
    stale_newest = dict(run, id=9500, head_sha="f" * 40)
    refuse("a stale newest run behind which an older valid run exists", "head tree differs",
           lambda: select([run, stale_newest], {**trees, "f" * 40: "9" * 40}))
    refuse("a newest run of another event behind which an older valid run exists", "was triggered by",
           lambda: select([run, dict(run, id=9500, event="pull_request")], trees))
    refuse("an empty list", "no successful rehearsal run", lambda: select([], trees))
    refuse("a repeated run id", "repeated run id", lambda: select([run, dict(run)], trees))
    refuse("a run without an id", "malformed or repeated run id", lambda: select([{k: v for k, v in run.items() if k != "id"}], trees))
    refuse("a list that is not a list", "malformed or exceeds", lambda: select_performance_run(
        {"workflow_runs": {"id": 1}}, REHEARSAL_TAG, REHEARSAL_SOURCE, EXPECTED_REPOSITORY, trees.get))
    refuse("a document that is not an object", "malformed or exceeds", lambda: select_performance_run(
        [run], REHEARSAL_TAG, REHEARSAL_SOURCE, EXPECTED_REPOSITORY, trees.get))
    refuse("an over-long list", "malformed or exceeds", lambda: select([dict(run, id=1 + n) for n in range(MAX_RUN_LIST + 1)], trees))
    refuse("a tag that is not a release tag", "malformed", lambda: select_performance_run(
        {"workflow_runs": [run]}, "main", REHEARSAL_SOURCE, EXPECTED_REPOSITORY, trees.get))

    def artifact_defect(label: str, reason: str, mutate: Callable[[dict[str, Any], list[dict[str, Any]]], Any]) -> None:
        doc = json.loads(json.dumps(artifacts))
        outcome = mutate(doc["artifacts"][1], doc["artifacts"])
        if isinstance(outcome, tuple):
            doc = outcome[1]
        else:
            doc["total_count"] = len(doc["artifacts"])
        refuse(label, reason, lambda: select_performance_artifact(chosen, doc))

    artifact_defect("an artifact of another attempt only", "not exactly one",
                    lambda a, all_: all_.remove(a) or None)
    artifact_defect("a repeated artifact name", "not exactly one", lambda a, all_: (all_.append(dict(a, id=77)), None)[1])
    artifact_defect("an artifact renamed for another run", "not exactly one", lambda a, all_: a.update(name="rehearsal-performance-1-1"))
    artifact_defect("an expired artifact", "has expired", lambda a, all_: a.update(expired=True))
    artifact_defect("an artifact with no expiry flag", "has expired", lambda a, all_: a.pop("expired"))
    artifact_defect("an empty artifact", "size bound", lambda a, all_: a.update(size_in_bytes=0))
    artifact_defect("an oversized artifact", "size bound", lambda a, all_: a.update(size_in_bytes=MAX_RECEIPT_BYTES + 1))
    artifact_defect("an artifact with no producing run", "does not name its producing run", lambda a, all_: a.pop("workflow_run"))
    artifact_defect("an artifact of another run", "different run, head or branch", lambda a, all_: a["workflow_run"].update(id=1))
    artifact_defect("an artifact of another head", "different run, head or branch", lambda a, all_: a["workflow_run"].update(head_sha="d" * 40))
    artifact_defect("an artifact of another branch", "different run, head or branch", lambda a, all_: a["workflow_run"].update(head_branch="main"))
    artifact_defect("an artifact from a fork", "fork or an unknown repository", lambda a, all_: a["workflow_run"].update(head_repository_id=5))
    artifact_defect("an artifact of another repository", "fork or an unknown repository",
                    lambda a, all_: a["workflow_run"].update(repository_id=5, head_repository_id=5))
    artifact_defect("a truncated artifact list", "malformed, truncated", lambda a, all_: ("doc", {"total_count": 9, "artifacts": all_}))
    artifact_defect("an artifact list that is not a list", "malformed, truncated", lambda a, all_: ("doc", {"total_count": 0, "artifacts": {}}))
    print(f"PASS: rehearsal reuse selects only the newest successful run of the tagged tree and its own artifact; {controls} defects rejected")
    return controls


def rehearsal_cli_self_test() -> None:
    """The CLI the workflow runs, against a disposable repository, so equal-tree proof really comes from git objects."""
    script = Path(__file__).resolve()
    with tempfile.TemporaryDirectory(prefix="gb-rehearsal-reuse.") as scratch:
        work = Path(scratch) / "repo"
        work.mkdir()
        env = {"GIT_CONFIG_GLOBAL": str(Path(scratch) / "gitconfig"), "GIT_CONFIG_SYSTEM": "/dev/null" if sys.platform != "win32" else "NUL",
               "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
        child_env = {key: value for key, value in os.environ.items() if key in ("PATH", "SYSTEMROOT", "TMPDIR", "TEMP", "TMP")}
        child_env.update(env)

        def git(*args: str) -> str:
            done = subprocess.run(["git", *args], cwd=work, capture_output=True, text=True, check=True, env=child_env, timeout=60)
            return done.stdout.strip()

        git("init", "-q")
        (work / "tree.txt").write_text("tagged tree\n")
        git("add", "tree.txt")
        git("commit", "-q", "-m", "tagged source")
        source = git("rev-parse", "HEAD")
        git("commit", "-q", "--allow-empty", "-m", "same tree, other commit")
        same_tree = git("rev-parse", "HEAD")
        (work / "tree.txt").write_text("another tree\n")
        git("commit", "-q", "-am", "other tree")
        other_tree = git("rev-parse", "HEAD")
        run, artifacts, _ = rehearsal_fixture()
        runs_file, run_out, artifacts_file = (Path(scratch) / name for name in ("runs.json", "run.json", "artifacts.json"))
        artifacts_file.write_text(json.dumps(artifacts))

        def cli(*args: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run([sys.executable, "-I", str(script), *args], cwd=work, capture_output=True, text=True,
                                  check=False, env=child_env, timeout=60)

        def select(head: str) -> subprocess.CompletedProcess[str]:
            runs_file.write_text(json.dumps({"total_count": 1, "workflow_runs": [dict(run, head_sha=head)]}))
            return cli("--select-performance-run", str(runs_file), "--tag", REHEARSAL_TAG, "--source-sha", source,
                       "--repo", EXPECTED_REPOSITORY, "--selected-run", str(run_out))

        for head, label in ((source, "exact head"), (same_tree, "equal tree")):
            done = select(head)
            if done.returncode != 0 or done.stdout.strip() != "9000":
                raise SystemExit(f"rehearsal CLI refused the {label}: {done.stdout}{done.stderr}")
        selected = json.loads(run_out.read_text())
        artifacts_doc = json.loads(artifacts_file.read_text())
        for artifact in artifacts_doc["artifacts"]:
            artifact["workflow_run"]["head_sha"] = same_tree
        artifacts_file.write_text(json.dumps(artifacts_doc))
        done = cli("--select-performance-artifact", str(artifacts_file), "--selected-run", str(run_out))
        if done.returncode != 0 or done.stdout.strip() != "rehearsal-performance-9000-2" or selected["head_sha"] != same_tree:
            raise SystemExit(f"rehearsal CLI refused the artifact of the selected run: {done.stdout}{done.stderr}")
        stale = select(other_tree)
        if stale.returncode != 1 or "head tree differs" not in stale.stderr or stale.stdout.strip():
            raise SystemExit(f"rehearsal CLI accepted a head of another tree: {stale.returncode} {stale.stdout}{stale.stderr}")
        missing = select("a" * 40)
        if missing.returncode != 1 or "cannot be proved from git objects" not in missing.stderr:
            raise SystemExit(f"rehearsal CLI accepted a head that is not in the object database: {missing.stderr}")
        jobs_file = Path(scratch) / "attempt-jobs.json"
        jobs_file.write_text(json.dumps({"total_count": 1, "jobs": [{"run_id": run["id"], "run_attempt": run["run_attempt"],
                                                                         "completed_at": "2026-10-26T02:15:10Z"}]}))
        selected = select(same_tree)
        if selected.returncode != 0:
            raise SystemExit(f"rehearsal CLI setup refused the same-tree PR head: {selected.stderr}")
        bound = cli("--bind-rehearsal-run", str(runs_file), "--tag", REHEARSAL_TAG, "--source-sha", source,
                    "--repo", EXPECTED_REPOSITORY, "--selected-run", str(run_out), "--pr-head", same_tree,
                    "--merged-at", "2026-10-26T02:27:35Z", "--attempt-jobs", str(jobs_file))
        if (bound.returncode != 0 or bound.stdout.strip() != f"rehearsal-bound run_id={run['id']} head_sha={same_tree}"):
            raise SystemExit(f"rehearsal CLI failed to bind the selected PR head: {bound.stdout}{bound.stderr}")
        jobs_doc = json.loads(jobs_file.read_text())
        jobs_doc["jobs"][0]["completed_at"] = "2026-10-26T02:27:36Z"
        jobs_file.write_text(json.dumps(jobs_doc))
        late = cli("--bind-rehearsal-run", str(runs_file), "--tag", REHEARSAL_TAG, "--source-sha", source,
                   "--repo", EXPECTED_REPOSITORY, "--selected-run", str(run_out), "--pr-head", same_tree,
                   "--merged-at", "2026-10-26T02:27:35Z", "--attempt-jobs", str(jobs_file))
        if late.returncode != 1 or "REJECT: rehearsal-postdates-tag" not in late.stderr or late.stdout.strip():
            raise SystemExit(f"rehearsal CLI accepted a postdated attempt: {late.returncode} {late.stdout}{late.stderr}")
    print("PASS: rehearsal CLI proves equal trees from git objects and prints nothing for a refusal")


CAPTURED = Path(__file__).resolve().parents[2] / "tests/data/release-api/captured.json"


def captured_shape_self_test() -> int:
    """Judge real, sanitized GitHub objects (tests/data/release-api) with the same validator.

    The hand-built fixture above shows what the validator accepts; the captured pull request and check runs show it
    accepts what GitHub actually returns, which carries url, html_url and check_suite and no repository member. The
    receipt is built from the capture's own identity, never from the validator's constants."""
    if not CAPTURED.is_file():
        print("SKIP: no captured GitHub API shapes beside this validator (a bare copy has none)")
        return 0
    capture = json.loads(CAPTURED.read_text(encoding="utf-8"))
    identity, responses = capture["identity"], capture["responses"]
    head, source = identity["pr_head_sha"], identity["source_sha"]
    pr = json.loads(json.dumps(responses["pull_request"]))
    checks = json.loads(json.dumps(responses["check_runs"]))
    checks["check_runs"] = [run for run in checks["check_runs"] if run["name"] in REQUIRED_CONTEXTS]
    receipt = {"tag_name": identity["tag"], "version": identity["tag"][1:], "source_sha": source,
               "release_id": str(identity["release_id"]), "draft": True, "source_clean": True,
               "prior_pr_proof": {"pr_number": identity["pr_number"], "head_sha": head,
                                  "merge_commit_sha": source, "required_checks": "passed"}}
    args = (identity["tag"], source, str(identity["release_id"]))
    validate(receipt, pr, checks, *args)
    first = checks["check_runs"][0]
    if "repository" in first or not first["url"].startswith(API_CHECK_RUN_PREFIX) or not isinstance(first.get("check_suite"), dict):
        raise SystemExit("captured check runs are not the real GitHub shape")
    mutations = {
        "captured check run without its check_suite": lambda c: c["check_runs"][0].pop("check_suite"),
        "captured check run of another repository": lambda c: c["check_runs"][0].update(
            url=c["check_runs"][0]["url"].replace(EXPECTED_REPOSITORY, "other/repository")),
        "captured html_url of another repository": lambda c: c["check_runs"][0].update(
            html_url=c["check_runs"][0]["html_url"].replace(EXPECTED_REPOSITORY, "other/repository")),
        "captured check run of a stale head": lambda c: c["check_runs"][0].update(head_sha="0" * 40),
        "captured check run of another App": lambda c: c["check_runs"][0]["app"].update(id=1),
        "captured check run with only the old repository member": lambda c: (
            c["check_runs"][0].pop("url"), c["check_runs"][0].pop("html_url"),
            c["check_runs"][0].update(repository={"full_name": EXPECTED_REPOSITORY})),
        "captured required context missing": lambda c: c["check_runs"].pop(),
    }
    for label, mutate in mutations.items():
        altered = json.loads(json.dumps(checks))
        mutate(altered)
        try:
            validate(receipt, pr, altered, *args)
        except ValueError:
            continue
        raise SystemExit(f"captured-shape self-test accepted {label}")
    print(f"PASS: real captured GitHub shapes validate and {len(mutations)} captured-shape defects are rejected")
    # The rehearsal selection reads the capture's own run and artifact objects (every member GitHub returns), with only the
    # identity members replaced, so it is judged on the real shapes and not on a hand-built subset.
    rehearsal_reuse_self_test(responses["workflow_runs"]["workflow_runs"][0], responses["artifacts"]["artifacts"][0])
    return len(mutations)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt")
    parser.add_argument("--pull-request")
    parser.add_argument("--check-runs")
    parser.add_argument("--tag")
    parser.add_argument("--source-sha")
    parser.add_argument("--release-id")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--select-performance-run", metavar="RUNS_JSON",
                        help="print the id of the newest successful rehearsal run of --tag when it built the tagged tree")
    parser.add_argument("--bind-rehearsal-run", metavar="RUNS_JSON",
                        help="select the newest successful rehearsal and bind it to the reviewed version PR head")
    parser.add_argument("--select-performance-artifact", metavar="ARTIFACTS_JSON",
                        help="print the name of the one artifact the run in --selected-run uploaded")
    parser.add_argument("--selected-run", metavar="FILE", help="written by --select-performance-run, read by --select-performance-artifact")
    parser.add_argument("--repo", help="OWNER/NAME the rehearsal run must belong to")
    parser.add_argument("--pr-head", help="exact version PR head that the rehearsal must name")
    parser.add_argument("--merged-at", help="server-recorded version PR merge time for the selected attempt")
    parser.add_argument("--attempt-jobs", metavar="JOBS_JSON", help="jobs for exactly the selected run attempt")
    args = parser.parse_args()
    if args.self_test:
        run_self_test()
        rehearsal_reuse_self_test()
        rehearsal_cli_self_test()
        captured_shape_self_test()
        return 0
    if args.select_performance_run or args.bind_rehearsal_run or args.select_performance_artifact:
        try:
            if args.select_performance_run or args.bind_rehearsal_run:
                if None in (args.tag, args.source_sha, args.repo, args.selected_run):
                    parser.error("run selection requires --tag, --source-sha, --repo and --selected-run")
                if args.select_performance_run and args.bind_rehearsal_run:
                    parser.error("choose one of --select-performance-run or --bind-rehearsal-run")
                if args.bind_rehearsal_run:
                    if args.pr_head is None:
                        parser.error("--bind-rehearsal-run requires --pr-head")
                    if (args.merged_at is None) != (args.attempt_jobs is None):
                        raise ValueError("rehearsal-postdates-tag: incomplete not_after binding")
                    jobs = json.loads(Path(args.attempt_jobs).read_text(encoding="utf-8")) if args.attempt_jobs is not None else None
                    run = bind_rehearsal_run(json.loads(Path(args.bind_rehearsal_run).read_text(encoding="utf-8")),
                                             args.tag, args.source_sha, args.repo, git_tree_of, args.pr_head,
                                             args.merged_at, jobs)
                    Path(args.selected_run).write_text(json.dumps(run), encoding="utf-8")
                    print(f"rehearsal-bound run_id={run['id']} head_sha={run['head_sha']}")
                    return 0
                run = select_performance_run(json.loads(Path(args.select_performance_run).read_text(encoding="utf-8")),
                                             args.tag, args.source_sha, args.repo, git_tree_of)
                Path(args.selected_run).write_text(json.dumps(run), encoding="utf-8")
                print(run["id"])
            else:
                if args.selected_run is None:
                    parser.error("--select-performance-artifact requires --selected-run")
                run = json.loads(Path(args.selected_run).read_text(encoding="utf-8"))
                print(select_performance_artifact(run, json.loads(Path(args.select_performance_artifact).read_text(encoding="utf-8"))))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            print(f"REJECT: {error}", file=sys.stderr)
            return 1
        return 0
    required = (args.receipt, args.pull_request, args.check_runs, args.tag, args.source_sha, args.release_id)
    if any(value is None for value in required):
        parser.error("live validation requires receipt, pull-request, check-runs, tag, source-sha and release-id")
    receipt, pr, checks = (json.loads(Path(path).read_text())
                           for path in (args.receipt, args.pull_request, args.check_runs))
    validate(receipt, pr, checks, args.tag, args.source_sha, args.release_id)
    print(f"PASS: source receipt, merged PR #{pr['number']} and exact-head required checks agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
