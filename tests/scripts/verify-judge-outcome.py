#!/usr/bin/env python3
"""Normalize a local or hosted trusted-judge outcome for release pre-flight.

    python3 -I verify-judge-outcome.py --key STDERR_FILE --exit N
    python3 -I verify-judge-outcome.py --hosted RUN_JSON FAILED_LOG
    python3 -I verify-judge-outcome.py --self-test

This stdlib-only checker shares one message-key rule between the local judge
emulation and the hosted rehearsal log. A missing or ambiguous failure detail
is undecidable and therefore never compares equal to an expected refusal.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

if not __debug__:
    raise SystemExit("verify-judge-outcome refuses to run under python -O (its checks must stay on)")

MAX_BYTES = 8 * 1024 * 1024
JUDGE_JOB = "rehearse-trusted-judge"
REJECT_LINE = re.compile(r"\bREJECT ([A-Za-z0-9_-]+):")
RECEIPT_LINE = re.compile(r"receipt rejected: [^\r\n]+")
UNRECOGNIZED = re.compile(r"\berror: unrecognized arguments:\s*([^\r\n]*)")
ARGPARSE_ERROR = re.compile(r"\berror: ([^\r\n]+)")
FLAG = re.compile(r"--[A-Za-z0-9][A-Za-z0-9-]*")
EXIT_CODE = re.compile(r"Process completed with exit code ([0-9]+)\.")


class Undecidable(Exception):
    """The observed output cannot be reduced to a trustworthy key."""


def bounded_bytes(path: pathlib.Path) -> bytes:
    try:
        size = path.stat().st_size
        if size > MAX_BYTES:
            raise Undecidable(f"{path} exceeds {MAX_BYTES} bytes")
        with path.open("rb") as stream:
            data = stream.read(MAX_BYTES + 1)
    except OSError as error:
        raise Undecidable(f"cannot read {path}: {error}") from error
    if len(data) > MAX_BYTES:
        raise Undecidable(f"{path} exceeds {MAX_BYTES} bytes")
    return data


def message_key(text: str, exit_code: int) -> str:
    if exit_code == 0:
        return "pass"
    for line in text.splitlines():
        candidate = line.strip()
        reject = REJECT_LINE.search(candidate)
        if reject is not None:
            return f"REJECT {reject.group(1)}"
        receipt = RECEIPT_LINE.search(candidate)
        if receipt is not None:
            return receipt.group(0)
        unknown = UNRECOGNIZED.search(candidate)
        if unknown is not None:
            flags = sorted(set(FLAG.findall(unknown.group(1))))
            if flags:
                return "usage unrecognized " + " ".join(flags)
            return "usage unrecognized"
        argparse_error = ARGPARSE_ERROR.search(candidate)
        if argparse_error is not None:
            return "usage " + argparse_error.group(1).strip()
    raise Undecidable("failure has no recognized message key")


def parse_hosted_log(raw: bytes, failed_step: str, failed_count: int) -> tuple[int, str]:
    try:
        lines = raw.decode("utf-8", errors="strict").splitlines()
    except UnicodeDecodeError as error:
        raise Undecidable("hosted failed-step log is not UTF-8") from error

    selected: list[str] = []
    for line in lines:
        fields = line.split("\t", 2)
        if len(fields) != 3 or fields[0] != JUDGE_JOB:
            continue
        step_name = fields[1]
        if step_name == failed_step or (step_name == "UNKNOWN STEP" and failed_count == 1):
            timestamp_and_message = fields[2]
            _, separator, message = timestamp_and_message.partition(" ")
            if not separator:
                raise Undecidable("hosted log line has no timestamp/message separator")
            selected.append(message[len("##[error]"):] if message.startswith("##[error]") else message)
    if not selected:
        raise Undecidable("failed judge step has no matching log lines")

    exit_codes = [int(match.group(1)) for line in selected if (match := EXIT_CODE.search(line))]
    if len(exit_codes) != 1:
        raise Undecidable("failed judge step has no unique process exit-code line")
    exit_code = exit_codes[0]
    output = "\n".join(line for line in selected if EXIT_CODE.search(line) is None)
    return exit_code, message_key(output, exit_code)


def hosted_outcome(run_data: object, failed_log: bytes) -> str:
    if not isinstance(run_data, dict):
        raise Undecidable("run JSON is not an object")
    if run_data.get("status") != "completed":
        raise Undecidable("workflow run is not completed")
    jobs = run_data.get("jobs")
    if not isinstance(jobs, list):
        raise Undecidable("run JSON has no jobs array")
    judge_jobs = [job for job in jobs if isinstance(job, dict) and job.get("name") == JUDGE_JOB]
    if len(judge_jobs) != 1:
        raise Undecidable("run JSON does not identify exactly one trusted-judge job")
    judge = judge_jobs[0]
    conclusion = judge.get("conclusion")
    if conclusion == "success":
        return "success"
    if conclusion != "failure":
        raise Undecidable("trusted-judge conclusion is neither success nor failure")
    steps = judge.get("steps")
    if not isinstance(steps, list):
        raise Undecidable("failed judge job has no steps array")
    failed_steps = [step for step in steps if isinstance(step, dict) and step.get("conclusion") == "failure"]
    if not failed_steps:
        raise Undecidable("failed judge job has no failed step")
    first = failed_steps[0]
    step_name = first.get("name")
    if not isinstance(step_name, str) or not step_name:
        raise Undecidable("failed judge step has no name")
    exit_code, key = parse_hosted_log(failed_log, step_name, len(failed_steps))
    return f"failure|{step_name}|{exit_code}|{key}"


def expect(actual: str | None, expected: str | None, label: str) -> int:
    if actual != expected:
        raise Undecidable(f"self-test {label} expected {expected!r}, got {actual!r}")
    return 1


def self_test() -> int:
    controls = 0
    controls += expect(message_key("", 0), "pass", "success key")
    controls += expect(message_key("REJECT receipt-invalid: no", 1), "REJECT receipt-invalid", "reject key")
    controls += expect(message_key("receipt rejected: stale source", 1),
                       "receipt rejected: stale source", "receipt key")
    controls += expect(message_key("usage: tool\nerror: unrecognized arguments: --zeta value --alpha other", 2),
                       "usage unrecognized --alpha --zeta", "sorted argparse flags")
    controls += expect(message_key("error: --value needs a value", 2),
                       "usage --value needs a value", "argparse key")

    def must_be_undecidable(label: str, action) -> int:
        try:
            action()
        except Undecidable:
            return expect("undecidable", "undecidable", label)
        raise Undecidable(f"self-test {label} unexpectedly produced an outcome")

    controls += must_be_undecidable("unknown local failure", lambda: message_key("linker exploded", 1))

    success = {"status": "completed", "jobs": [{"name": JUDGE_JOB, "conclusion": "success", "steps": []}]}
    controls += expect(hosted_outcome(success, b""), "success", "hosted success")

    run = {"status": "completed", "jobs": [
        {"name": "rehearse-corpus-and-support-sidecar", "conclusion": "failure", "steps": [
            {"name": "full ctest", "conclusion": "failure"}]},
        {"name": JUDGE_JOB, "conclusion": "failure", "steps": [
            {"name": "policy", "conclusion": "failure"},
            {"name": "fuzz", "conclusion": "skipped"}]},
    ]}
    hosted_log = (
        b"rehearse-corpus-and-support-sidecar\tfull ctest\t2026-10-29T12:00:00Z "
        b"##[error]REJECT corpus-invalid: bad\n"
        b"rehearse-corpus-and-support-sidecar\tfull ctest\t2026-10-29T12:00:01Z "
        b"##[error]Process completed with exit code 8.\n"
        b"rehearse-trusted-judge\tfuzz\t2026-10-29T12:00:02Z REJECT fuzz-invalid: wrong step\n"
        b"rehearse-trusted-judge\tpolicy\t2026-10-29T12:00:03Z "
        b"verify: error: unrecognized arguments: --git-root trusted-judge\n"
        b"rehearse-trusted-judge\tpolicy\t2026-10-29T12:00:04Z "
        b"##[error]Process completed with exit code 2.\n"
    )
    controls += expect(hosted_outcome(run, hosted_log),
                       "failure|policy|2|usage unrecognized --git-root", "judge-scoped hosted failure")

    def hosted_key_case(stderr_line: str, code: int, expected_key: str, label: str) -> int:
        fixture = {"status": "completed", "jobs": [{"name": JUDGE_JOB, "conclusion": "failure", "steps": [
            {"name": "policy", "conclusion": "failure"}]}]}
        log = (f"{JUDGE_JOB}\tpolicy\t2026-10-29T12:00:00Z {stderr_line}\n"
               f"{JUDGE_JOB}\tpolicy\t2026-10-29T12:00:01Z Process completed with exit code {code}.\n").encode()
        return expect(hosted_outcome(fixture, log), f"failure|policy|{code}|{expected_key}", label)

    controls += hosted_key_case("##[error]REJECT bad-input: refused", 1, "REJECT bad-input", "hosted reject key")
    controls += hosted_key_case("receipt rejected: stale source", 1,
                                "receipt rejected: stale source", "hosted receipt key")
    controls += hosted_key_case("tool: error: unrecognized arguments: --git-root trusted-judge", 2,
                                "usage unrecognized --git-root", "hosted unrecognized-argument key")
    controls += hosted_key_case("tool: error: required argument missing", 2,
                                "usage required argument missing", "hosted argparse key")
    only_other_job = b"rehearse-corpus-and-support-sidecar\tfull ctest\t2026-10-29T12:00:00Z REJECT corpus-invalid: bad\n"
    controls += must_be_undecidable("other-job-only log", lambda: hosted_outcome(run, only_other_job))
    other_step_only = b"rehearse-trusted-judge\tfuzz\t2026-10-29T12:00:00Z REJECT fuzz-invalid: bad\n"
    controls += must_be_undecidable("other judge step ignored", lambda: hosted_outcome(run, other_step_only))
    empty_failed_step = b""
    controls += must_be_undecidable("empty failed-step log", lambda: hosted_outcome(run, empty_failed_step))
    missing_exit = b"rehearse-trusted-judge\tpolicy\t2026-10-29T12:00:00Z REJECT bad: failed\n"
    controls += must_be_undecidable("missing exit-code line", lambda: hosted_outcome(run, missing_exit))
    unknown_step_run = {"status": "completed", "jobs": [{"name": JUDGE_JOB, "conclusion": "failure", "steps": [
        {"name": "policy", "conclusion": "failure"}]}]}
    unknown_step_log = (
        b"rehearse-trusted-judge\tUNKNOWN STEP\t2026-10-29T12:00:00Z REJECT policy-refused: no\n"
        b"rehearse-trusted-judge\tUNKNOWN STEP\t2026-10-29T12:00:01Z Process completed with exit code 1.\n"
    )
    controls += expect(hosted_outcome(unknown_step_run, unknown_step_log),
                       "failure|policy|1|REJECT policy-refused", "single failed UNKNOWN STEP")
    multiple_failed = {"status": "completed", "jobs": [{"name": JUDGE_JOB, "conclusion": "failure", "steps": [
        {"name": "policy", "conclusion": "failure"}, {"name": "fuzz", "conclusion": "failure"}]}]}
    controls += must_be_undecidable("ambiguous UNKNOWN STEP", lambda: hosted_outcome(multiple_failed, unknown_step_log))
    return controls


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--key", nargs=2, metavar=("STDERR_FILE", "EXIT"))
    mode.add_argument("--hosted", nargs=2, metavar=("RUN_JSON", "FAILED_LOG"))
    mode.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            controls = self_test()
            print(f"judge-outcome controls pass controls={controls}")
            return 0
        if args.key is not None:
            stderr_path = pathlib.Path(args.key[0])
            try:
                exit_code = int(args.key[1])
            except ValueError as error:
                raise Undecidable("--exit must be an integer") from error
            if exit_code < 0:
                raise Undecidable("--exit must be non-negative")
            text = bounded_bytes(stderr_path).decode("utf-8", errors="strict")
            print(message_key(text, exit_code))
            return 0
        run_path, log_path = (pathlib.Path(value) for value in args.hosted)
        try:
            run_data = json.loads(bounded_bytes(run_path).decode("utf-8", errors="strict"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise Undecidable("run JSON is not valid UTF-8 JSON") from error
        print(hosted_outcome(run_data, bounded_bytes(log_path)))
        return 0
    except (OSError, UnicodeDecodeError, Undecidable) as error:
        print(f"judge differential undecidable: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
