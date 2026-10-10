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
import json
import re
import subprocess
import sys
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


def run_self_test():
    sha = "a" * 40

    def run(id_, number, attempt, status, conclusion):
        return {"id": id_, "run_number": number, "run_attempt": attempt, "status": status,
                "conclusion": conclusion, "head_sha": sha, "event": EVENT, "path": WORKFLOW_PATH}

    def listing(*runs):
        return {"total_count": len(runs), "workflow_runs": list(runs)}

    def verdict_of(lst, details, jobs, required):
        state = {"key": None, "streak": 0}
        return decide(sha, lst, lambda i: details[i], lambda i: jobs, required, state)[0]

    ok_jobs = {"total_count": 1, "jobs": [{"name": "required-native", "conclusion": "success", "run_attempt": 1}]}
    cases = [
        ("newest success passes", "PASS",
         verdict_of(listing(run(2, 20, 1, "completed", "success")),
                    {2: run(2, 20, 1, "completed", "success")}, ok_jobs, ["required-native"])),
        ("older success + newest in progress waits", "WAIT",
         verdict_of(listing(run(1, 10, 1, "completed", "success"), run(2, 20, 1, "in_progress", None)),
                    {2: run(2, 20, 1, "in_progress", None)}, ok_jobs, ["required-native"])),
    ]
    for label, expected, got in cases:
        if got != expected:
            raise SystemExit("self-test failed: {}: expected {}, got {}".format(label, expected, got))
        print("PASS: {}".format(label))
    calls = []
    rc = main(["--sha", "NOTASHA", "--repo", "a/b", "--require", "required-native",
               "--deadline-seconds", "5"], fetchers_factory=lambda repo, sha: calls.append(1))
    if rc != 2 or calls:
        raise SystemExit("self-test failed: invalid SHA: expected exit 2 with no fetch, got {} / {}".format(rc, calls))
    print("PASS: invalid SHA exits 2 before any fetch")
    print("PASS: exact-head gate self-test ({} cases)".format(len(cases) + 1))


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
