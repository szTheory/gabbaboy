#!/usr/bin/env python3
"""Wait for the exact-head pull-request CI run and decide whether it certifies a revision.

Rule (phase 06.1 D-07): among ci.yml pull_request runs for exactly the given head SHA, the
run with the highest run_number decides. A run keeps its id and run_number across re-runs;
only run_attempt grows, so ordering is by run_number alone and run_attempt is used for
list/detail consistency, failure debouncing and the player artifact name. An older success
never satisfies a newer failed or pending run. Any doubt (malformed or truncated data,
list/detail disagreement, transport errors) waits, and the deadline fails closed.

The gate is read-only: it only issues GET requests through `gh api` and never builds a
shell string or a jq program from its inputs.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time

SHA_RE = re.compile(r"[0-9a-f]{40}")
REPO_RE = re.compile(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+")
WORKFLOW_PATH = ".github/workflows/ci.yml"
EVENT = "pull_request"
DETAIL_KEYS = ("id", "run_number", "run_attempt", "head_sha", "event", "path", "status", "conclusion")
# A terminal failure must be seen on this many consecutive polls of the same
# (run id, run attempt) before it is believed: a re-run can briefly leave a stale
# completed/failure read behind a new attempt (research A6, Pitfall 1).
DEBOUNCE_POLLS = 2
FAIL_FAST_DEPENDENCIES = (
    "changes", "planning-checks", "native-linux-x64", "native-macos-arm64", "native-windows-x64",
    "linux-asan-ubsan", "linux-asan-ubsan-tests", "linux-asan-ubsan-acceptance",
    "cmake-floor-3.25.3", "perf-gate", "player-gate", "macos-player-package",
)
RUN_STATUSES = frozenset(("completed", "in_progress", "queued", "waiting", "requested", "pending"))
JOB_STATUSES = frozenset(("completed", "in_progress", "queued", "waiting", "requested", "pending"))
CONCLUSIONS = frozenset(("success", "failure", "neutral", "cancelled", "skipped", "timed_out",
                         "action_required", "stale"))
FAIL_FAST_CONCLUSIONS = frozenset(("failure", "timed_out", "cancelled", "action_required"))


class TransientError(Exception):
    """A gh/API problem that may clear on the next poll."""


def gh_get(path, params=None):
    """GET one REST endpoint through gh api. Argv list only: no shell, no jq."""
    cmd = ["gh", "api", "-X", "GET", path]
    for key, value in (params or {}).items():
        cmd += ["-f", "{}={}".format(key, value)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise TransientError("gh api {} failed: {}".format(path, result.stderr.strip()[:200]))
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise TransientError("gh api {} returned invalid JSON: {}".format(path, exc))


def _wait(state, reason):
    state["key"] = None
    state["streak"] = 0
    state["component_key"] = None
    state["component_streak"] = 0
    return ("WAIT", reason, None)


def planning_run(jobs):
    """True when the run's own job results show the D-21 planning lane: `changes` and `planning-checks` each
    appear exactly once and succeeded. ci.yml runs planning-checks only for kind=planning (it is skipped for
    kind=full), and required-native, a required job here, passes kind=planning only if every heavy job was skipped,
    so this is read from the trusted exact-head run, never from pull-request text."""
    for name in ("changes", "planning-checks"):
        matches = [j for j in jobs if isinstance(j, dict) and j.get("name") == name]
        if len(matches) != 1 or matches[0].get("conclusion") != "success":
            return False
    return True


def _positive_int(value):
    return type(value) is int and value > 0


def _valid_conclusion(status, conclusion):
    if status == "completed":
        return isinstance(conclusion, str) and conclusion in CONCLUSIONS
    return conclusion is None


def _valid_run_record(run):
    return (isinstance(run, dict) and _positive_int(run.get("id"))
            and _positive_int(run.get("run_number")) and _positive_int(run.get("run_attempt"))
            and isinstance(run.get("head_sha"), str) and SHA_RE.fullmatch(run["head_sha"]) is not None
            and isinstance(run.get("event"), str) and bool(run["event"])
            and isinstance(run.get("path"), str) and bool(run["path"])
            and run.get("status") in RUN_STATUSES
            and _valid_conclusion(run.get("status"), run.get("conclusion")))


def _valid_jobs_response(response):
    if (not isinstance(response, dict) or type(response.get("total_count")) is not int
            or response["total_count"] < 0 or not isinstance(response.get("jobs"), list)
            or response["total_count"] != len(response["jobs"])):
        return None
    records = response["jobs"]
    seen_ids = set()
    for job in records:
        if (not isinstance(job, dict) or not _positive_int(job.get("id"))
                or not _positive_int(job.get("run_id"))
                or not isinstance(job.get("head_sha"), str) or SHA_RE.fullmatch(job["head_sha"]) is None
                or not isinstance(job.get("name"), str) or not job["name"]
                or job.get("status") not in JOB_STATUSES
                or not _valid_conclusion(job.get("status"), job.get("conclusion"))
                or ("run_attempt" in job and not _positive_int(job["run_attempt"]))
                or job["id"] in seen_ids):
            return None
        seen_ids.add(job["id"])
    return records


def _required_native_failure(jobs, sha, run_id, run_number, attempt):
    """Return (failure key, reason), or (None, reason) for a conclusive no-failure observation.

    GitHub's existing jobs endpoint is queried with filter=latest, so its result is scoped to
    the newest run attempt. Job payloads may omit run_attempt; the caller rereads the parent
    run after this response and rejects an attempt/SHA/status change before using it.
    """
    records = _valid_jobs_response(jobs)
    if records is None:
        return False, "malformed or incomplete job list"
    for job in records:
        if job["run_id"] != run_id or job["head_sha"] != sha:
            return False, "job list contains a wrong run or head identity"
    by_name = {}
    for job in records:
        by_name.setdefault(job["name"], []).append(job)
    dependency_jobs = []
    for name in FAIL_FAST_DEPENDENCIES:
        matches = by_name.get(name, [])
        if len(matches) != 1:
            return False, "required dependency {} appears {} times".format(name, len(matches))
        job = matches[0]
        if "run_attempt" in job and job["run_attempt"] != attempt:
            return False, "required dependency {} is copied from another attempt".format(name)
        dependency_jobs.append(job)
    for job in dependency_jobs:
        if (job["status"] == "completed" and job["conclusion"] in FAIL_FAST_CONCLUSIONS):
            key = (run_id, run_number, attempt, job["id"], job["name"], job["conclusion"])
            return key, "required dependency {} concluded {}".format(job["name"], job["conclusion"])
    return None, "no terminal required dependency failure"


def decide(sha, listing, fetch_detail, fetch_jobs, required, state, planning_skippable=(),
           fail_fast_required_native=False):
    """Return (verdict, reason, payload) for one poll. All I/O is injected.

    planning_skippable names required jobs that a kind=planning run legitimately skips (the macOS player package:
    a planning-only head changes no source, so no package exists to verify). Only an exact `skipped` conclusion in
    a planning run is excused; every other case, and every non-planning run, judges the job as before."""
    if (not isinstance(listing, dict) or type(listing.get("total_count")) is not int
            or listing["total_count"] < 0 or not isinstance(listing.get("workflow_runs"), list)):
        return _wait(state, "malformed run list")
    if listing["total_count"] != len(listing["workflow_runs"]):
        return _wait(state, "run list is truncated or inconsistent")
    all_runs = listing["workflow_runs"]
    if not all(_valid_run_record(run) for run in all_runs):
        return _wait(state, "run list contains malformed selection data")
    if len({run["id"] for run in all_runs}) != len(all_runs):
        return _wait(state, "run list contains duplicate run ids")
    kept = [r for r in all_runs if r["head_sha"] == sha and r["event"] == EVENT
            and r["path"] == WORKFLOW_PATH]
    if not kept:
        return _wait(state, "no matching run yet")
    newest_number = max(r["run_number"] for r in kept)
    newest_matches = [r for r in kept if r["run_number"] == newest_number]
    if len(newest_matches) != 1:
        return _wait(state, "newest matching run number is ambiguous")
    newest = newest_matches[0]
    detail = fetch_detail(newest["id"])
    if not _valid_run_record(detail) or any(detail.get(k) != newest.get(k) for k in DETAIL_KEYS):
        return _wait(state, "list/detail disagree")
    run_id = newest["id"]
    attempt = detail.get("run_attempt")
    if detail.get("status") != "completed":
        state["key"] = None
        state["streak"] = 0
        if fail_fast_required_native and "required-native" in required:
            jobs = fetch_jobs(run_id)
            failure_key, reason = _required_native_failure(jobs, sha, run_id, detail["run_number"], attempt)
            after_jobs = fetch_detail(run_id)
            if (not _valid_run_record(after_jobs)
                    or any(after_jobs.get(k) != detail.get(k) for k in DETAIL_KEYS)):
                return _wait(state, "run identity or attempt changed while reading required jobs")
            if failure_key is False:
                return _wait(state, reason)
            if failure_key is None:
                state["component_key"] = None
                state["component_streak"] = 0
                return ("WAIT", "newest run {} attempt {} is {}; {}".format(
                    run_id, attempt, detail["status"], reason), None)
            if state.get("component_key") == failure_key:
                state["component_streak"] = state.get("component_streak", 0) + 1
            else:
                state["component_key"] = failure_key
                state["component_streak"] = 1
            if state["component_streak"] >= DEBOUNCE_POLLS:
                _, _, _, job_id, name, conclusion = failure_key
                return ("FAIL", "run {} attempt {} dependency {} job {} concluded {} twice".format(
                    run_id, attempt, name, job_id, conclusion),
                    {"run_id": run_id, "run_number": detail["run_number"], "run_attempt": attempt,
                     "failed_job": name, "result": conclusion, "job_id": job_id})
            return ("WAIT", "debouncing run {} attempt {} dependency {} conclusion {}".format(
                run_id, attempt, failure_key[4], failure_key[5]), None)
        state["component_key"] = None
        state["component_streak"] = 0
        return _wait(state, "newest run {} attempt {} is {}".format(run_id, attempt, detail.get("status")))

    conclusion = detail.get("conclusion")
    if conclusion == "success":
        jobs = fetch_jobs(run_id)
        records = _valid_jobs_response(jobs)
        if records is None:
            return _wait(state, "malformed job list")
        if any(job["run_id"] != run_id or job["head_sha"] != sha for job in records):
            return _wait(state, "job list contains a wrong run or head identity")
        job_attempts = {}
        planning = planning_run(records)
        for name in required:
            matches = [j for j in records if j.get("name") == name]
            if len(matches) != 1:
                return _wait(state, "required job {} appears {} times in run {}".format(name, len(matches), run_id))
            job = matches[0]
            if job["status"] != "completed":
                return _wait(state, "required job {} is incomplete in a completed run".format(name))
            if planning and name in planning_skippable and job.get("conclusion") == "skipped":
                job_attempts[name] = None
                continue
            if job.get("conclusion") != "success":
                return ("FAIL", "required job {} concluded {} in run {}".format(name, job.get("conclusion"), run_id),
                        {"run_id": run_id, "failed_job": name, "result": job.get("conclusion")})
            job_attempts[name] = job.get("run_attempt")
        return ("PASS", "run {} attempt {} succeeded".format(run_id, attempt),
                {"run_id": run_id, "run_attempt": attempt, "job_attempts": job_attempts,
                 "kind": "planning" if planning else "full"})

    # Any valid non-success terminal conclusion: believe it only after consecutive agreeing polls.
    state["component_key"] = None
    state["component_streak"] = 0
    key = (run_id, detail["run_number"], attempt, conclusion)
    if state.get("key") == key:
        state["streak"] = state.get("streak", 0) + 1
    else:
        state["key"] = key
        state["streak"] = 1
    if state["streak"] >= DEBOUNCE_POLLS:
        return ("FAIL", "newest run {} attempt {} concluded {}".format(run_id, attempt, conclusion),
                {"run_id": run_id, "result": conclusion})
    return ("WAIT", "debouncing terminal {} for run {} attempt {}".format(conclusion, run_id, attempt), None)


def legacy_message(sha, payload, attempt_job):
    if payload and attempt_job and payload.get("failed_job") == attempt_job:
        return "Required player package job failed in exact-head CI run {} ({}).".format(
            payload.get("run_id"), payload.get("result"))
    return "The exact pull-request CI run did not pass required-native for {}.".format(sha)


def run_gate(sha, repo, required, deadline_seconds, interval_seconds, clock, sleep,
             fetchers, github_output=None, attempt_job=None, planning_skippable=(),
             fail_fast_required_native=False):
    """Poll until PASS or FAIL, or fail closed at the deadline. Returns an exit code."""
    state = {"key": None, "streak": 0, "component_key": None, "component_streak": 0}
    start = clock()
    while True:
        try:
            verdict, reason, payload = decide(sha, fetchers["list"](), fetchers["detail"],
                                              fetchers["jobs"], required, state,
                                              planning_skippable, fail_fast_required_native)
        except TransientError as exc:
            state["key"] = None
            state["streak"] = 0
            state["component_key"] = None
            state["component_streak"] = 0
            verdict, reason, payload = "WAIT", "transport: {}".format(exc), None
        if verdict == "PASS":
            attempt = payload["job_attempts"][attempt_job] if attempt_job else payload["run_attempt"]
            if attempt is None:
                attempt = payload["run_attempt"]  # the excused job never ran, so no artifact is named after it
            print("exact-head-ci: PASS run_id={} run_attempt={} kind={} sha={}".format(
                payload["run_id"], attempt, payload["kind"], sha))
            if github_output:
                # The player artifact is named with the attempt in which the job ran
                # (research Pitfall 3), which is the job's run_attempt, not the run's.
                with open(github_output, "a") as handle:
                    handle.write("run_id={}\nrun_attempt={}\nkind={}\n".format(
                        payload["run_id"], attempt, payload["kind"]))
            return 0
        if verdict == "FAIL":
            print("exact-head-ci: FAIL {}".format(reason), file=sys.stderr)
            print(legacy_message(sha, payload, attempt_job), file=sys.stderr)
            return 1
        print("exact-head-ci: WAIT {}".format(reason))
        if clock() >= start + deadline_seconds:
            print("exact-head-ci: FAIL deadline reached", file=sys.stderr)
            print("No completed successful pull-request CI run for {} appeared within {} minutes.".format(
                sha, deadline_seconds // 60), file=sys.stderr)
            return 1
        sleep(interval_seconds)


def make_fetchers(repo, sha):
    return {
        "list": lambda: gh_get("repos/{}/actions/workflows/ci.yml/runs".format(repo),
                               {"head_sha": sha, "event": EVENT, "per_page": 100}),
        "detail": lambda run_id: gh_get("repos/{}/actions/runs/{}".format(repo, run_id)),
        "jobs": lambda run_id: gh_get("repos/{}/actions/runs/{}/jobs".format(repo, run_id),
                                      {"filter": "latest", "per_page": 100}),
    }


SELF_SHA = "a" * 40


def make_run(id_, number, attempt, status, conclusion, sha=SELF_SHA, event=EVENT, path=WORKFLOW_PATH):
    return {"id": id_, "run_number": number, "run_attempt": attempt, "status": status,
            "conclusion": conclusion, "head_sha": sha, "event": event, "path": path}


def make_listing(*runs, **overrides):
    listing = {"total_count": len(runs), "workflow_runs": list(runs)}
    listing.update(overrides)
    return listing


def make_jobs(jobs, **overrides):
    """jobs: dict of name -> (conclusion, run_attempt), with complete API-shaped identity fields."""
    run_id = overrides.pop("run_id", 2)
    head_sha = overrides.pop("head_sha", SELF_SHA)
    records = []
    for index, (name, (conclusion, attempt)) in enumerate(jobs.items()):
        records.append({"id": 100 + index, "run_id": run_id, "head_sha": head_sha,
                        "name": name, "status": "completed" if conclusion is not None else "in_progress",
                        "conclusion": conclusion, "run_attempt": attempt})
    body = {"total_count": len(records), "jobs": records}
    body.update(overrides)
    return body


def make_dependency_jobs(failed=None, conclusion="failure", *, run_id=2, head_sha=SELF_SHA, attempt=1):
    jobs = make_jobs({name: (None, attempt) for name in FAIL_FAST_DEPENDENCIES},
                     run_id=run_id, head_sha=head_sha)
    if failed is not None:
        record = next(item for item in jobs["jobs"] if item["name"] == failed)
        record["status"] = "completed"
        record["conclusion"] = conclusion
    return jobs


def _copy(value):
    return json.loads(json.dumps(value))


def _decide_poll(poll, state, required, skippable=()):
    listing, jobs = _copy(poll["listing"]), _copy(poll.get("jobs"))
    details = {k: _copy(v) for k, v in poll.get("details", {}).items()}
    def fetch_detail(run_id):
        value = details[run_id]
        if isinstance(value, list):
            return value.pop(0) if len(value) > 1 else value[0]
        return value
    try:
        return decide(SELF_SHA, listing, fetch_detail, lambda i: jobs, required, state, skippable,
                      poll.get("fail_fast_required_native", False))
    except KeyError as exc:
        # The case never expected this run to be fetched: report it as a labelled mismatch.
        return ("UNEXPECTED FETCH of run {}".format(exc), None, None)


def _poll_cases():
    """Labelled sequences of polls sharing one debounce state. Each poll: listing, details
    (run id -> detail), jobs, expected verdict."""
    req = ["required-native"]
    ok = make_jobs({"required-native": ("success", 1)})

    def done(id_, number, conclusion, attempt=1):
        return make_run(id_, number, attempt, "completed", conclusion)

    def pending(id_, number, attempt=1):
        return make_run(id_, number, attempt, "in_progress", None)

    def terminal(label, conclusion):
        run = done(2, 20, conclusion)
        return (label, req, [{"listing": make_listing(run), "details": {2: run}, "expect": "WAIT"},
                             {"listing": make_listing(run), "details": {2: run}, "expect": "FAIL"}])

    player = ["required-native", "macos-player-package"]
    planning_jobs = {"changes": ("success", 1), "planning-checks": ("success", 1),
                     "required-native": ("success", 1), "macos-player-package": ("skipped", 1)}
    full_jobs = {"changes": ("success", 1), "planning-checks": ("skipped", 1),
                 "required-native": ("success", 1), "macos-player-package": ("skipped", 1)}

    def player_case(label, jobs, expect, skippable=("macos-player-package",)):
        run = done(2, 20, "success")
        return (label, player, [{"listing": make_listing(run), "details": {2: run},
                                 "jobs": make_jobs(jobs), "expect": expect}], skippable)

    return [
        player_case("planning run permits a skipped player job -> PASS", planning_jobs, "PASS"),
        player_case("full run still rejects a skipped player job -> FAIL", full_jobs, "FAIL"),
        player_case("planning run without the skippable flag still rejects a skipped player job -> FAIL",
                    planning_jobs, "FAIL", ()),
        player_case("planning run does not excuse a failed player job -> FAIL",
                    {**planning_jobs, "macos-player-package": ("failure", 1)}, "FAIL"),
        player_case("planning run does not excuse a cancelled player job -> FAIL",
                    {**planning_jobs, "macos-player-package": ("cancelled", 1)}, "FAIL"),
        player_case("planning run with incomplete player job data waits",
                    {k: v for k, v in planning_jobs.items() if k != "macos-player-package"}, "WAIT"),
        player_case("planning-checks skipped (full) is not planning even with a skipped player job -> FAIL",
                    {**planning_jobs, "planning-checks": ("skipped", 1)}, "FAIL"),
        player_case("planning-checks failed is not planning -> FAIL",
                    {**planning_jobs, "planning-checks": ("failure", 1)}, "FAIL"),
        player_case("changes job missing is not planning -> FAIL",
                    {k: v for k, v in planning_jobs.items() if k != "changes"}, "FAIL"),
        player_case("planning run with a skipped required-native is still FAIL",
                    {**planning_jobs, "required-native": ("skipped", 1)}, "FAIL"),
        player_case("full run with a successful player job -> PASS",
                    {**full_jobs, "macos-player-package": ("success", 1)}, "PASS"),
        player_case("planning run whose player job ran and succeeded -> PASS",
                    {**planning_jobs, "macos-player-package": ("success", 1)}, "PASS"),
        ("older failed + newest in progress -> WAIT", req, [
            {"listing": make_listing(done(1, 10, "failure"), pending(2, 20)),
             "details": {2: pending(2, 20)}, "expect": "WAIT"}]),
        ("older success + newest in progress -> WAIT, never PASS", req, [
            {"listing": make_listing(done(1, 10, "success"), pending(2, 20)),
             "details": {2: pending(2, 20)}, "jobs": ok, "expect": "WAIT"}]),
        ("newest success -> PASS", req, [
            {"listing": make_listing(done(1, 10, "failure"), done(2, 20, "success")),
             "details": {2: done(2, 20, "success")}, "jobs": ok, "expect": "PASS"}]),
        ("newest failed after older success -> WAIT then FAIL", req, [
            {"listing": make_listing(done(1, 10, "success"), done(2, 20, "failure")),
             "details": {2: done(2, 20, "failure")}, "jobs": ok, "expect": "WAIT"},
            {"listing": make_listing(done(1, 10, "success"), done(2, 20, "failure")),
             "details": {2: done(2, 20, "failure")}, "jobs": ok, "expect": "FAIL"}]),
        ("attempt 2 in progress after attempt 1 failed -> WAIT", req, [
            {"listing": make_listing(pending(2, 20, attempt=2)),
             "details": {2: pending(2, 20, attempt=2)}, "expect": "WAIT"}]),
        ("wrong SHA, event and workflow path are ignored -> WAIT", req, [
            {"listing": make_listing(
                make_run(1, 30, 1, "completed", "success", sha="b" * 40),
                make_run(2, 31, 1, "completed", "success", event="push"),
                make_run(3, 32, 1, "completed", "success", path=".github/workflows/preview.yml")),
             "expect": "WAIT"}]),
        ("missing required job -> WAIT", req, [
            {"listing": make_listing(done(2, 20, "success")), "details": {2: done(2, 20, "success")},
             "jobs": make_jobs({"native-linux-x64": ("success", 1)}), "expect": "WAIT"}]),
        ("required job skipped -> FAIL", req, [
            {"listing": make_listing(done(2, 20, "success")), "details": {2: done(2, 20, "success")},
             "jobs": make_jobs({"required-native": ("skipped", 1)}), "expect": "FAIL"}]),
        ("required job failure under a successful run -> FAIL", req, [
            {"listing": make_listing(done(2, 20, "success")), "details": {2: done(2, 20, "success")},
             "jobs": make_jobs({"required-native": ("failure", 1)}), "expect": "FAIL"}]),
        ("duplicated required job -> WAIT", req, [
            {"listing": make_listing(done(2, 20, "success")), "details": {2: done(2, 20, "success")},
             "jobs": {"total_count": 2, "jobs": [
                 {"name": "required-native", "conclusion": "success", "run_attempt": 1}] * 2},
             "expect": "WAIT"}]),
        ("truncated run list (total 31, listed 30) -> WAIT", req, [
            {"listing": make_listing(*[done(i, i, "success") for i in range(1, 31)], total_count=31),
             "expect": "WAIT"}]),
        ("truncated job list -> WAIT", req, [
            {"listing": make_listing(done(2, 20, "success")), "details": {2: done(2, 20, "success")},
             "jobs": make_jobs({"required-native": ("success", 1)}, total_count=2), "expect": "WAIT"}]),
        ("empty run list -> WAIT", req, [
            {"listing": make_listing(), "expect": "WAIT"}]),
        ("malformed run list -> WAIT", req, [
            {"listing": {"workflow_runs": "nope"}, "expect": "WAIT"}]),
        ("list/detail run_attempt mismatch -> WAIT", req, [
            {"listing": make_listing(done(2, 20, "success", attempt=1)),
             "details": {2: done(2, 20, "success", attempt=2)}, "jobs": ok, "expect": "WAIT"}]),
        terminal("cancelled needs two polls -> WAIT then FAIL", "cancelled"),
        terminal("timed_out needs two polls -> WAIT then FAIL", "timed_out"),
        terminal("action_required needs two polls -> WAIT then FAIL", "action_required"),
        ("a new attempt between polls resets the debounce -> WAIT, WAIT", req, [
            {"listing": make_listing(done(2, 20, "failure", attempt=1)),
             "details": {2: done(2, 20, "failure", attempt=1)}, "expect": "WAIT"},
            {"listing": make_listing(done(2, 20, "failure", attempt=2)),
             "details": {2: done(2, 20, "failure", attempt=2)}, "expect": "WAIT"}]),
        ("an in-progress poll between failures resets the debounce", req, [
            {"listing": make_listing(done(2, 20, "failure")), "details": {2: done(2, 20, "failure")},
             "expect": "WAIT"},
            {"listing": make_listing(pending(2, 20, attempt=2)),
             "details": {2: pending(2, 20, attempt=2)}, "expect": "WAIT"},
            {"listing": make_listing(done(2, 20, "failure", attempt=2)),
             "details": {2: done(2, 20, "failure", attempt=2)}, "expect": "WAIT"}]),
    ]


def _check(label, expected, got):
    if expected != got:
        raise SystemExit("self-test failed: {}: expected {}, got {}".format(label, expected, got))


def _gate_case_deadline():
    """A perpetually in-progress run: the fake clock runs past the deadline -> exit 1."""
    run = make_run(2, 20, 1, "in_progress", None)
    clock_now = [0]

    def clock():
        return clock_now[0]

    def sleep(seconds):
        clock_now[0] += seconds

    fetchers = {"list": lambda: make_listing(run), "detail": lambda i: _copy(run),
                "jobs": lambda i: make_jobs({})}
    err = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
        rc = run_gate(SELF_SHA, "o/r", ["required-native"], 120, 10, clock, sleep, fetchers)
    _check("deadline exits 1", 1, rc)
    _check("deadline prints the legacy message", True,
           "No completed successful pull-request CI run for {} appeared within 2 minutes.".format(SELF_SHA)
           in err.getvalue())


def _gate_case_player_output():
    """Run attempt 2 but the player job ran in attempt 1: output must carry the job's attempt."""
    run = make_run(77, 20, 2, "completed", "success")
    jobs = make_jobs({"required-native": ("success", 2), "macos-player-package": ("success", 1)}, run_id=77)
    fetchers = {"list": lambda: make_listing(run), "detail": lambda i: _copy(run), "jobs": lambda i: _copy(jobs)}
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "github-output")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = run_gate(SELF_SHA, "o/r", ["required-native", "macos-player-package"], 60, 10,
                          lambda: 0, lambda s: None, fetchers, out, "macos-player-package",
                          fail_fast_required_native=True)
        with open(out) as handle:
            content = handle.read()
    _check("player mode exits 0", 0, rc)
    _check("player output takes run_attempt from the job object", "run_id=77\nrun_attempt=1\nkind=full\n", content)


def _gate_case_planning_output():
    """A planning run excuses the skipped player job: exit 0, kind=planning, run attempt in the output."""
    run = make_run(78, 20, 3, "completed", "success")
    jobs = make_jobs({"changes": ("success", 3), "planning-checks": ("success", 3),
                      "required-native": ("success", 3), "macos-player-package": ("skipped", 3)}, run_id=78)
    fetchers = {"list": lambda: make_listing(run), "detail": lambda i: _copy(run), "jobs": lambda i: _copy(jobs)}
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "github-output")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = run_gate(SELF_SHA, "o/r", ["required-native", "macos-player-package"], 60, 10,
                          lambda: 0, lambda s: None, fetchers, out, "macos-player-package",
                          ["macos-player-package"])
        with open(out) as handle:
            content = handle.read()
    _check("planning run exits 0", 0, rc)
    _check("planning output declares kind=planning", "run_id=78\nrun_attempt=3\nkind=planning\n", content)


def _gate_case_unknown_skippable():
    with contextlib.redirect_stderr(io.StringIO()):
        rc = main(["--sha", SELF_SHA, "--repo", "o/r", "--require", "required-native",
                   "--planning-skippable", "macos-player-package", "--deadline-seconds", "5"],
                  fetchers_factory=lambda repo, sha: None)
    _check("--planning-skippable outside --require exits 2", 2, rc)


def _gate_case_fail_fast_requires_required_native():
    calls = []
    with contextlib.redirect_stderr(io.StringIO()):
        rc = main(["--sha", SELF_SHA, "--repo", "o/r", "--require", "some-other-job",
                   "--fail-fast-required-native", "--deadline-seconds", "5"],
                  fetchers_factory=lambda repo, sha: calls.append((repo, sha)))
    _check("fail-fast requires required-native before any fetch", (2, []), (rc, calls))


def _gate_case_player_failure_message():
    run = make_run(5, 20, 1, "completed", "success")
    jobs = make_jobs({"required-native": ("success", 1), "macos-player-package": ("failure", 1)}, run_id=5)
    fetchers = {"list": lambda: make_listing(run), "detail": lambda i: _copy(run), "jobs": lambda i: _copy(jobs)}
    err = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
        rc = run_gate(SELF_SHA, "o/r", ["required-native", "macos-player-package"], 60, 10,
                      lambda: 0, lambda s: None, fetchers, None, "macos-player-package")
    _check("failed player job exits 1", 1, rc)
    _check("failed player job prints the legacy player message", True,
           "Required player package job failed in exact-head CI run 5 (failure)." in err.getvalue())


def _gate_case_transient_then_pass():
    run = make_run(2, 20, 1, "completed", "success")
    jobs = make_jobs({"required-native": ("success", 1)})
    calls = []

    def listing():
        calls.append(1)
        if len(calls) == 1:
            raise TransientError("simulated gh failure")
        return make_listing(run)

    fetchers = {"list": listing, "detail": lambda i: _copy(run), "jobs": lambda i: _copy(jobs)}
    with contextlib.redirect_stdout(io.StringIO()):
        rc = run_gate(SELF_SHA, "o/r", ["required-native"], 60, 10, lambda: 0, lambda s: None, fetchers)
    _check("transport error waits, then the next poll passes", (0, 2), (rc, len(calls)))


def _gate_case_jobs_filter_latest():
    """Pitfall 2: the job list must be requested with filter=latest so old attempts never count."""
    seen = []
    original = globals()["gh_get"]
    globals()["gh_get"] = lambda path, params=None: seen.append((path, dict(params or {}))) or {}
    try:
        make_fetchers("o/r", SELF_SHA)["jobs"](9)
        make_fetchers("o/r", SELF_SHA)["list"]()
    finally:
        globals()["gh_get"] = original
    _check("jobs requested with filter=latest", True, seen[0][1].get("filter") == "latest")
    _check("run list requested for the exact SHA and event", True,
           seen[1][1].get("head_sha") == SELF_SHA and seen[1][1].get("event") == EVENT)


def _active_failure_poll(jobs, run=None, *, details=None):
    run = run or make_run(2, 20, 1, "in_progress", None)
    return {"listing": make_listing(run), "details": details if details is not None else {2: [run, run]},
            "jobs": jobs, "fail_fast_required_native": True}


def _fail_fast_controls():
    """Prove exact current-attempt failure debounce, uncertainty resets and default-off behavior."""
    count = 0
    run = make_run(2, 20, 1, "in_progress", None)
    for dependency in FAIL_FAST_DEPENDENCIES:
        for conclusion in sorted(FAIL_FAST_CONCLUSIONS):
            state = {"key": None, "streak": 0, "component_key": None, "component_streak": 0}
            poll = _active_failure_poll(make_dependency_jobs(dependency, conclusion))
            _check("{} {} first matching failure waits".format(dependency, conclusion), "WAIT",
                   _decide_poll(poll, state, ["required-native"])[0])
            result = _decide_poll(poll, state, ["required-native"])
            _check("{} {} second matching failure fails".format(dependency, conclusion), "FAIL", result[0])
            _check("{} {} names exact failed dependency".format(dependency, conclusion), dependency,
                   result[2]["failed_job"])
            count += 3

    # The jobs endpoint's filter=latest binds the payload to the fetched run attempt;
    # the parent run attempt is reread after the jobs call to close an attempt rollover.
    no_job_attempt = make_dependency_jobs("native-linux-x64")
    for job in no_job_attempt["jobs"]:
        job.pop("run_attempt")
    state = {"key": None, "streak": 0, "component_key": None, "component_streak": 0}
    poll = _active_failure_poll(no_job_attempt)
    _check("filter=latest plus stable positive run attempt binds the job list", "WAIT",
           _decide_poll(poll, state, ["required-native"])[0])
    _check("current-attempt failure is useful without an undocumented job attempt field", "FAIL",
           _decide_poll(poll, state, ["required-native"])[0])
    count += 2

    for nonfailure in ("success", "skipped", "neutral"):
        state = {"key": None, "streak": 0, "component_key": None, "component_streak": 0}
        nonfailure_poll = _active_failure_poll(
            make_dependency_jobs("native-linux-x64", nonfailure))
        _check("{} child result never fails a pending run".format(nonfailure), "WAIT",
               _decide_poll(nonfailure_poll, state, ["required-native"])[0])
        _check("{} child result never passes a pending run".format(nonfailure), "WAIT",
               _decide_poll(nonfailure_poll, state, ["required-native"])[0])
        count += 2

    stale = make_dependency_jobs("native-linux-x64")
    next(job for job in stale["jobs"] if job["name"] == "native-linux-x64")["run_attempt"] = 2
    state = {"key": None, "streak": 0, "component_key": None, "component_streak": 0}
    stale_poll = _active_failure_poll(stale)
    _check("copied job from another attempt cannot fail fast", "WAIT",
           _decide_poll(stale_poll, state, ["required-native"])[0])
    _check("copied-attempt evidence never builds a failure streak", "WAIT",
           _decide_poll(stale_poll, state, ["required-native"])[0])
    count += 2

    # Every listed dependency must be present once and bound to the same run/head.
    for label, mutate in (
        ("missing dependency", lambda body: body["jobs"].pop()),
        ("duplicate dependency", lambda body: body["jobs"].append(dict(body["jobs"][0]))),
        ("wrong run identity", lambda body: body["jobs"][0].__setitem__("run_id", 999)),
        ("wrong head identity", lambda body: body["jobs"][0].__setitem__("head_sha", "b" * 40)),
        ("invalid job identifier", lambda body: body["jobs"][0].__setitem__("id", True)),
        ("unknown job status", lambda body: body["jobs"][0].__setitem__("status", "maybe")),
        ("completed job without conclusion", lambda body: body["jobs"][0].__setitem__("status", "completed")),
        ("truncated jobs list", lambda body: body.__setitem__("total_count", body["total_count"] + 1)),
    ):
        body = make_dependency_jobs("native-linux-x64")
        mutate(body)
        state = {"key": None, "streak": 0, "component_key": None, "component_streak": 0}
        test_poll = _active_failure_poll(body)
        _check("{} is inconclusive".format(label), "WAIT",
               _decide_poll(test_poll, state, ["required-native"])[0])
        _check("{} remains inconclusive on repetition".format(label), "WAIT",
               _decide_poll(test_poll, state, ["required-native"])[0])
        count += 2

    state = {"key": None, "streak": 0, "component_key": None, "component_streak": 0}
    failure_poll = _active_failure_poll(make_dependency_jobs("native-linux-x64"))
    _check("a first component failure waits before uncertainty", "WAIT",
           _decide_poll(failure_poll, state, ["required-native"])[0])
    incomplete = make_dependency_jobs("native-linux-x64")
    incomplete["jobs"].pop()
    _check("an incomplete poll interrupts the component streak", "WAIT",
           _decide_poll(_active_failure_poll(incomplete), state, ["required-native"])[0])
    _check("failure after uncertainty starts a fresh streak", "WAIT",
           _decide_poll(failure_poll, state, ["required-native"])[0])
    _check("only two new stable observations fail", "FAIL",
           _decide_poll(failure_poll, state, ["required-native"])[0])
    count += 4

    state = {"key": None, "streak": 0, "component_key": None, "component_streak": 0}
    _check("changed job id starts a new dependency streak", "WAIT",
           _decide_poll(failure_poll, state, ["required-native"])[0])
    changed_job = make_dependency_jobs("native-linux-x64")
    next(item for item in changed_job["jobs"] if item["name"] == "native-linux-x64")["id"] += 500
    changed_job_poll = _active_failure_poll(changed_job)
    _check("changed dependency job id cannot finish the prior streak", "WAIT",
           _decide_poll(changed_job_poll, state, ["required-native"])[0])
    _check("two observations of the changed job id become conclusive", "FAIL",
           _decide_poll(changed_job_poll, state, ["required-native"])[0])
    count += 3

    state = {"key": None, "streak": 0, "component_key": None, "component_streak": 0}
    _check("first run identity starts its own failure streak", "WAIT",
           _decide_poll(failure_poll, state, ["required-native"])[0])
    next_run = make_run(3, 21, 1, "in_progress", None)
    next_run_poll = _active_failure_poll(
        make_dependency_jobs("native-linux-x64", run_id=3), run=next_run,
        details={3: [next_run, next_run]})
    _check("newer run cannot finish the earlier run's failure streak", "WAIT",
           _decide_poll(next_run_poll, state, ["required-native"])[0])
    _check("two matching observations in the new run become conclusive", "FAIL",
           _decide_poll(next_run_poll, state, ["required-native"])[0])
    count += 3

    state = {"key": None, "streak": 0, "component_key": None, "component_streak": 0}
    _check("changed conclusion starts a new dependency streak", "WAIT",
           _decide_poll(failure_poll, state, ["required-native"])[0])
    timed_out_poll = _active_failure_poll(
        make_dependency_jobs("native-linux-x64", "timed_out"))
    _check("different terminal conclusion cannot finish the prior streak", "WAIT",
           _decide_poll(timed_out_poll, state, ["required-native"])[0])
    _check("two matching changed conclusions become conclusive", "FAIL",
           _decide_poll(timed_out_poll, state, ["required-native"])[0])
    count += 3

    unrelated = make_dependency_jobs()
    extra = make_jobs({"unrelated-report": ("failure", 1)}, run_id=2)["jobs"][0]
    extra["id"] = 999
    unrelated["jobs"].append(extra)
    unrelated["total_count"] += 1
    state = {"key": None, "streak": 0, "component_key": None, "component_streak": 0}
    unrelated_poll = _active_failure_poll(unrelated)
    _check("unrelated failed job cannot provide component failure", "WAIT",
           _decide_poll(unrelated_poll, state, ["required-native"])[0])
    count += 1

    changed_run = make_run(2, 20, 2, "in_progress", None)
    changed_details = {2: [run, changed_run]}
    changed_poll = _active_failure_poll(make_dependency_jobs("native-linux-x64", attempt=1), details=changed_details)
    state = {"key": None, "streak": 0, "component_key": None, "component_streak": 0}
    _check("run attempt changing during the jobs read is inconclusive", "WAIT",
           _decide_poll(changed_poll, state, ["required-native"])[0])
    current = make_run(2, 20, 2, "in_progress", None)
    current_poll = _active_failure_poll(make_dependency_jobs("native-linux-x64", attempt=2), run=current)
    _check("a fresh current-attempt failure starts a new streak", "WAIT",
           _decide_poll(current_poll, state, ["required-native"])[0])
    _check("a second stable current-attempt failure is conclusive", "FAIL",
           _decide_poll(current_poll, state, ["required-native"])[0])
    count += 3

    tied = make_run(3, 20, 1, "in_progress", None)
    tied_poll = {"listing": make_listing(run, tied), "details": {2: run, 3: tied},
                 "jobs": make_dependency_jobs("native-linux-x64"), "fail_fast_required_native": True}
    state = {"key": None, "streak": 0, "component_key": None, "component_streak": 0}
    _check("tied newest run numbers are inconclusive", "WAIT",
           _decide_poll(tied_poll, state, ["required-native"])[0])
    truncated = {"listing": make_listing(run, total_count=2), "details": {2: run},
                 "jobs": make_dependency_jobs("native-linux-x64"), "fail_fast_required_native": True}
    _check("truncated run listing is inconclusive", "WAIT",
           _decide_poll(truncated, state, ["required-native"])[0])
    for label, malformed in (
        ("duplicate run id", make_listing(run, run)),
        ("nonpositive run attempt", make_listing(dict(run, run_attempt=0))),
        ("boolean run identifier", make_listing(dict(run, id=True))),
        ("unknown run status", make_listing(dict(run, status="uncertain"))),
        ("completed run without conclusion", make_listing(dict(run, status="completed", conclusion=None))),
        ("boolean total count", make_listing(run, total_count=True)),
    ):
        bad_poll = {"listing": malformed, "details": {2: run}, "jobs": make_dependency_jobs(),
                    "fail_fast_required_native": True}
        _check("{} is inconclusive".format(label), "WAIT",
               _decide_poll(bad_poll, state, ["required-native"])[0])
    for label, bad_detail in (
        ("boolean detail attempt", dict(run, run_attempt=True)),
        ("wrong detail id", dict(run, id=999)),
        ("unknown detail status", dict(run, status="uncertain")),
    ):
        bad_poll = {"listing": make_listing(run), "details": {2: bad_detail},
                    "jobs": make_dependency_jobs(), "fail_fast_required_native": True}
        _check("{} is inconclusive".format(label), "WAIT",
               _decide_poll(bad_poll, state, ["required-native"])[0])
    count += 11

    calls = []
    off_poll = _active_failure_poll(make_dependency_jobs("native-linux-x64"))
    off_poll["fail_fast_required_native"] = False
    listing = off_poll["listing"]
    detail = run
    verdict = decide(SELF_SHA, listing, lambda _id: detail,
                     lambda _id: calls.append("jobs") or off_poll["jobs"], ["required-native"],
                     {"key": None, "streak": 0}, fail_fast_required_native=False)
    _check("fail-fast defaults off and does not fetch jobs for a pending run", ("WAIT", 0),
           (verdict[0], len(calls)))
    count += 1
    return count


def _gate_case_component_transport_reset():
    run = make_run(2, 20, 1, "in_progress", None)
    jobs = make_dependency_jobs("native-linux-x64")
    job_reads = []

    def fetch_jobs(_run_id):
        job_reads.append(1)
        if len(job_reads) == 2:
            raise TransientError("simulated job-list gap")
        return _copy(jobs)

    clock_now = [0]

    def sleep(seconds):
        clock_now[0] += seconds

    fetchers = {"list": lambda: make_listing(run), "detail": lambda _run_id: _copy(run),
                "jobs": fetch_jobs}
    with tempfile.TemporaryDirectory() as directory:
        output = os.path.join(directory, "github-output")
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = run_gate(SELF_SHA, "o/r", ["required-native"], 60, 10,
                          lambda: clock_now[0], sleep, fetchers, output,
                          fail_fast_required_native=True)
        _check("transport gap clears the debounce streak", (1, 4), (rc, len(job_reads)))
        _check("failed waiter emits no success output", False, "PASS" in stdout.getvalue())
        _check("failed waiter does not create a success output file", False, os.path.exists(output))


def _bad_sha_cases():
    calls = []
    for label, bad in (("uppercase", "A" * 40), ("39 characters", "a" * 39), ("41 characters", "a" * 41),
                       ("quote", "a" * 39 + "'"), ("space", "a" * 39 + " "), ("semicolon", "a" * 39 + ";")):
        with contextlib.redirect_stderr(io.StringIO()):
            rc = main(["--sha", bad, "--repo", "o/r", "--require", "required-native",
                       "--deadline-seconds", "5"], fetchers_factory=lambda repo, sha: calls.append(1))
        _check("SHA {} is rejected with exit 2".format(label), 2, rc)
    with contextlib.redirect_stderr(io.StringIO()):
        rc = main(["--sha", SELF_SHA, "--repo", "o/r; rm -rf", "--require", "required-native",
                   "--deadline-seconds", "5"], fetchers_factory=lambda repo, sha: calls.append(1))
    _check("repo with shell metacharacters is rejected with exit 2", 2, rc)
    _check("no fetch happened for any rejected input", [], calls)


def run_self_test():
    count = 0
    for label, required, polls, *rest in _poll_cases():
        state = {"key": None, "streak": 0}
        for index, poll in enumerate(polls):
            _check("{} (poll {})".format(label, index + 1), poll["expect"],
                   _decide_poll(poll, state, required, rest[0] if rest else ())[0])
        print("PASS: {}".format(label))
        count += 1
    for fn, label in ((_bad_sha_cases, "invalid SHA or repo exits 2 before any fetch"),
                      (_gate_case_deadline, "deadline fails closed with the legacy message"),
                      (_gate_case_player_output, "player mode writes the job-level run_attempt"),
                      (_gate_case_planning_output, "planning run writes kind=planning and excuses the skipped player job"),
                      (_gate_case_unknown_skippable, "--planning-skippable must name a required job"),
                      (_gate_case_fail_fast_requires_required_native,
                       "--fail-fast-required-native requires required-native before fetch"),
                      (_gate_case_player_failure_message, "failed player job keeps the legacy message"),
                      (_gate_case_transient_then_pass, "transport error waits instead of failing"),
                      (_gate_case_jobs_filter_latest, "jobs use filter=latest and the list is SHA/event scoped"),
                      (_gate_case_component_transport_reset,
                       "component transport uncertainty resets the failure streak")):
        fn()
        print("PASS: {}".format(label))
        count += 1
    fail_fast_count = _fail_fast_controls()
    count += fail_fast_count
    print("PASS: current-attempt required-native failure controls ({})".format(fail_fast_count))
    print("PASS: exact-head gate self-test ({} cases) controls={}".format(count, count))


def main(argv=None, fetchers_factory=make_fetchers):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--sha")
    parser.add_argument("--repo")
    parser.add_argument("--require", action="append", default=[])
    parser.add_argument("--deadline-seconds", type=int)
    parser.add_argument("--interval-seconds", type=int, default=10)
    parser.add_argument("--github-output")
    parser.add_argument("--attempt-job")
    parser.add_argument("--planning-skippable", action="append", default=[],
                        help="required job a kind=planning run may skip (repeatable)")
    parser.add_argument("--fail-fast-required-native", action="store_true",
                        help="fail a pending run only after two identical current-attempt required dependency failures")
    args = parser.parse_args(argv)
    if args.self_test:
        run_self_test()
        return 0
    if args.sha is None or args.repo is None or not args.require or args.deadline_seconds is None:
        print("usage: --sha, --repo, --require and --deadline-seconds are required", file=sys.stderr)
        return 2
    if not SHA_RE.fullmatch(args.sha):
        print("exact-head-ci: --sha must be a full lowercase 40-hex Git SHA", file=sys.stderr)
        return 2
    if not REPO_RE.fullmatch(args.repo):
        print("exact-head-ci: --repo must look like owner/name", file=sys.stderr)
        return 2
    if bool(args.github_output) != bool(args.attempt_job):
        print("exact-head-ci: --github-output and --attempt-job must be given together", file=sys.stderr)
        return 2
    if args.attempt_job and args.attempt_job not in args.require:
        print("exact-head-ci: --attempt-job must be one of the --require names", file=sys.stderr)
        return 2
    if any(name not in args.require for name in args.planning_skippable):
        print("exact-head-ci: --planning-skippable must name --require jobs", file=sys.stderr)
        return 2
    if args.fail_fast_required_native and "required-native" not in args.require:
        print("exact-head-ci: --fail-fast-required-native requires --require required-native", file=sys.stderr)
        return 2
    return run_gate(args.sha, args.repo, args.require, args.deadline_seconds, args.interval_seconds,
                    time.monotonic, time.sleep, fetchers_factory(args.repo, args.sha),
                    args.github_output, args.attempt_job, args.planning_skippable,
                    args.fail_fast_required_native)


if __name__ == "__main__":
    sys.exit(main())
