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
DETAIL_KEYS = ("run_attempt", "head_sha", "event", "path", "status")
# A terminal failure must be seen on this many consecutive polls of the same
# (run id, run attempt) before it is believed: a re-run can briefly leave a stale
# completed/failure read behind a new attempt (research A6, Pitfall 1).
DEBOUNCE_POLLS = 2


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
    return ("WAIT", reason, None)


def decide(sha, listing, fetch_detail, fetch_jobs, required, state):
    """Return (verdict, reason, payload) for one poll. All I/O is injected."""
    if (not isinstance(listing, dict) or not isinstance(listing.get("total_count"), int)
            or not isinstance(listing.get("workflow_runs"), list)):
        return _wait(state, "malformed run list")
    if listing["total_count"] > len(listing["workflow_runs"]):
        return ("FAIL", "run list truncated", None)
    kept = [r for r in listing["workflow_runs"]
            if isinstance(r, dict) and r.get("head_sha") == sha and r.get("event") == EVENT
            and r.get("path") == WORKFLOW_PATH and isinstance(r.get("id"), int)
            and isinstance(r.get("run_number"), int)]
    if not kept:
        return _wait(state, "no matching run yet")
    newest = max(kept, key=lambda r: r["run_number"])
    detail = fetch_detail(newest["id"])
    if not isinstance(detail, dict) or any(detail.get(k) != newest.get(k) for k in DETAIL_KEYS):
        return _wait(state, "list/detail disagree")
    run_id = newest["id"]
    attempt = detail.get("run_attempt")
    if detail.get("status") != "completed":
        return _wait(state, "newest run {} attempt {} is {}".format(run_id, attempt, detail.get("status")))

    conclusion = detail.get("conclusion")
    if conclusion == "success":
        jobs = fetch_jobs(run_id)
        if (not isinstance(jobs, dict) or not isinstance(jobs.get("total_count"), int)
                or not isinstance(jobs.get("jobs"), list)):
            return _wait(state, "malformed job list")
        if jobs["total_count"] > len(jobs["jobs"]):
            return ("FAIL", "job list truncated", None)
        job_attempts = {}
        for name in required:
            matches = [j for j in jobs["jobs"] if isinstance(j, dict) and j.get("name") == name]
            if len(matches) != 1:
                return ("FAIL", "required job {} appears {} times in run {}".format(name, len(matches), run_id),
                        {"run_id": run_id, "failed_job": name, "result": "missing" if not matches else "duplicated"})
            job = matches[0]
            if job.get("conclusion") != "success":
                return ("FAIL", "required job {} concluded {} in run {}".format(name, job.get("conclusion"), run_id),
                        {"run_id": run_id, "failed_job": name, "result": job.get("conclusion")})
            job_attempts[name] = job.get("run_attempt")
        return ("PASS", "run {} attempt {} succeeded".format(run_id, attempt),
                {"run_id": run_id, "run_attempt": attempt, "job_attempts": job_attempts})

    # Any non-success terminal conclusion: believe it only after consecutive agreeing polls.
    key = (run_id, attempt)
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
             fetchers, github_output=None, attempt_job=None):
    """Poll until PASS or FAIL, or fail closed at the deadline. Returns an exit code."""
    state = {"key": None, "streak": 0}
    start = clock()
    while True:
        try:
            verdict, reason, payload = decide(sha, fetchers["list"](), fetchers["detail"],
                                              fetchers["jobs"], required, state)
        except TransientError as exc:
            state["key"] = None
            state["streak"] = 0
            verdict, reason, payload = "WAIT", "transport: {}".format(exc), None
        if verdict == "PASS":
            attempt = payload["job_attempts"][attempt_job] if attempt_job else payload["run_attempt"]
            print("exact-head-ci: PASS run_id={} run_attempt={} sha={}".format(payload["run_id"], attempt, sha))
            if github_output:
                # The player artifact is named with the attempt in which the job ran
                # (research Pitfall 3), which is the job's run_attempt, not the run's.
                with open(github_output, "a") as handle:
                    handle.write("run_id={}\nrun_attempt={}\n".format(payload["run_id"], attempt))
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
    """jobs: dict of name -> (conclusion, run_attempt)."""
    body = {"total_count": len(jobs),
            "jobs": [{"name": n, "conclusion": c, "run_attempt": a} for n, (c, a) in jobs.items()]}
    body.update(overrides)
    return body


def _copy(value):
    return json.loads(json.dumps(value))


def _decide_poll(poll, state, required):
    listing, jobs = _copy(poll["listing"]), _copy(poll.get("jobs"))
    details = {k: _copy(v) for k, v in poll.get("details", {}).items()}
    try:
        return decide(SELF_SHA, listing, lambda i: details[i], lambda i: jobs, required, state)
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

    return [
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
        ("missing required job -> FAIL", req, [
            {"listing": make_listing(done(2, 20, "success")), "details": {2: done(2, 20, "success")},
             "jobs": make_jobs({"native-linux-x64": ("success", 1)}), "expect": "FAIL"}]),
        ("required job skipped -> FAIL", req, [
            {"listing": make_listing(done(2, 20, "success")), "details": {2: done(2, 20, "success")},
             "jobs": make_jobs({"required-native": ("skipped", 1)}), "expect": "FAIL"}]),
        ("required job failure under a successful run -> FAIL", req, [
            {"listing": make_listing(done(2, 20, "success")), "details": {2: done(2, 20, "success")},
             "jobs": make_jobs({"required-native": ("failure", 1)}), "expect": "FAIL"}]),
        ("duplicated required job -> FAIL", req, [
            {"listing": make_listing(done(2, 20, "success")), "details": {2: done(2, 20, "success")},
             "jobs": {"total_count": 2, "jobs": [
                 {"name": "required-native", "conclusion": "success", "run_attempt": 1}] * 2},
             "expect": "FAIL"}]),
        ("truncated run list (total 31, listed 30) -> FAIL", req, [
            {"listing": make_listing(*[done(i, i, "success") for i in range(1, 31)], total_count=31),
             "expect": "FAIL"}]),
        ("truncated job list -> FAIL", req, [
            {"listing": make_listing(done(2, 20, "success")), "details": {2: done(2, 20, "success")},
             "jobs": make_jobs({"required-native": ("success", 1)}, total_count=2), "expect": "FAIL"}]),
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
    jobs = make_jobs({"required-native": ("success", 2), "macos-player-package": ("success", 1)})
    fetchers = {"list": lambda: make_listing(run), "detail": lambda i: _copy(run), "jobs": lambda i: _copy(jobs)}
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "github-output")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = run_gate(SELF_SHA, "o/r", ["required-native", "macos-player-package"], 60, 10,
                          lambda: 0, lambda s: None, fetchers, out, "macos-player-package")
        with open(out) as handle:
            content = handle.read()
    _check("player mode exits 0", 0, rc)
    _check("player output takes run_attempt from the job object", "run_id=77\nrun_attempt=1\n", content)


def _gate_case_player_failure_message():
    run = make_run(5, 20, 1, "completed", "success")
    jobs = make_jobs({"required-native": ("success", 1), "macos-player-package": ("failure", 1)})
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
    for label, required, polls in _poll_cases():
        state = {"key": None, "streak": 0}
        for index, poll in enumerate(polls):
            _check("{} (poll {})".format(label, index + 1), poll["expect"],
                   _decide_poll(poll, state, required)[0])
        print("PASS: {}".format(label))
        count += 1
    for fn, label in ((_bad_sha_cases, "invalid SHA or repo exits 2 before any fetch"),
                      (_gate_case_deadline, "deadline fails closed with the legacy message"),
                      (_gate_case_player_output, "player mode writes the job-level run_attempt"),
                      (_gate_case_player_failure_message, "failed player job keeps the legacy message"),
                      (_gate_case_transient_then_pass, "transport error waits instead of failing"),
                      (_gate_case_jobs_filter_latest, "jobs use filter=latest and the list is SHA/event scoped")):
        fn()
        print("PASS: {}".format(label))
        count += 1
    print("PASS: exact-head gate self-test ({} cases)".format(count))


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
    return run_gate(args.sha, args.repo, args.require, args.deadline_seconds, args.interval_seconds,
                    time.monotonic, time.sleep, fetchers_factory(args.repo, args.sha),
                    args.github_output, args.attempt_job)


if __name__ == "__main__":
    sys.exit(main())
