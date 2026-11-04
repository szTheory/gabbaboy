#!/usr/bin/env python3
"""Verify exact-source Phase 23 review reports and qualification evidence."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
SHA1 = re.compile(r"[0-9a-f]{40}")
REPORTS = {
    "23-REVIEW.md": "release-consumer",
    "23-SECURITY.md": "security",
    "23-ADVERSARIAL.md": "adversarial",
}
REPORT_MARKER_START = "<!-- gbb-review-evidence:start -->"
REPORT_MARKER_END = "<!-- gbb-review-evidence:end -->"
MAX_REPORT_BYTES = 64 * 1024
MAX_FINDINGS = 100


class ReviewError(Exception):
    """A rejected review set with a stable review-* diagnostic."""


def reject(code: str, detail: str = "") -> None:
    raise ReviewError(code + (": " + detail if detail else ""))


def git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update({
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
    })
    return environment


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=repo,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                check=False, timeout=30, env=git_environment())
    except (OSError, subprocess.TimeoutExpired) as error:
        reject("review-git-failed", str(error))
    if check and result.returncode != 0:
        reject("review-git-failed", " ".join(args[:3]) + ": " + result.stderr.decode("utf-8", "replace").strip())
    return result


def resolve_commit(repo: Path, value: str, label: str) -> str:
    if type(value) is not str or SHA1.fullmatch(value) is None:
        reject("review-revision-invalid", f"{label} must be a full lowercase 40-hex commit")
    if git(repo, "cat-file", "-t", value, check=False).stdout.strip() != b"commit":
        reject("review-revision-invalid", f"{label} does not name an existing commit")
    return value


def git_blob(repo: Path, revision: str, path: str, limit: int = MAX_REPORT_BYTES) -> bytes | None:
    result = git(repo, "show", f"{revision}:{path}", check=False)
    if result.returncode != 0:
        return None
    if len(result.stdout) > limit:
        reject("review-source-too-large", path)
    return result.stdout


def is_ancestor(repo: Path, older: str, newer: str) -> bool:
    return git(repo, "merge-base", "--is-ancestor", older, newer, check=False).returncode == 0


def verify_registrations(repo: Path, revision: str) -> None:
    cmake_blob = git_blob(repo, revision, "tests/CMakeLists.txt", 8 * 1024 * 1024)
    inventory_blob = git_blob(repo, revision, "tests/expected-tests.txt", 2 * 1024 * 1024)
    if cmake_blob is None or inventory_blob is None:
        reject("review-test-registration-invalid", "CMakeLists.txt or expected-tests.txt is absent at --rev")
    try:
        cmake = cmake_blob.decode("utf-8")
        inventory = inventory_blob.decode("utf-8")
    except UnicodeDecodeError:
        reject("review-test-registration-invalid", "the CTest registration source is not UTF-8")

    helper = re.search(r"(?ms)^function\(gbb_add_v02_contract name timeout regex script\)(.*?)^endfunction\(\)", cmake)
    required_helper = (
        'set(command "${Python3_EXECUTABLE}" -I "${PROJECT_SOURCE_DIR}/tests/scripts/${script}" ${ARGN})',
        '"-DGBB_CMD=${command}"',
        "-DGBB_EXPECT_CODE=0",
        '"-DGBB_EXPECT_REGEX=${regex}"',
        "-P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake",
        'PROPERTIES TIMEOUT ${timeout} LABELS "v02"',
    )
    if helper is None or any(fragment not in helper.group(1) for fragment in required_helper):
        reject("review-test-registration-invalid", "the isolated Python/expect_exit contract wrapper changed")

    requirements = {
        "phase23_review_evidence_contract": (
            "verify-review-evidence.py --check --rev \"${GBB_STATE_SOURCE_REV}\" --repo \"${PROJECT_SOURCE_DIR}\"",
            r"[=[review-evidence contract pass reports=3 findings=[0-9]+ implementation=[0-9a-f]{12}]=]",
        ),
        "phase23_review_evidence_controls": (
            "verify-review-evidence.py --self-test --rev \"${GBB_STATE_SOURCE_REV}\" --repo \"${PROJECT_SOURCE_DIR}\"",
            r"[=[review-evidence controls pass positives=[1-9][0-9]* controls=[1-9][0-9]*]=]",
        ),
    }
    for name, (command, success_regex) in requirements.items():
        registration = list(re.finditer(rf"(?m)^gbb_add_v02_contract\({re.escape(name)}\s+([^\n]+)\n(.*?)^\)", cmake))
        if len(registration) != 1:
            reject("review-test-registration-invalid", f"expected exactly one registration for {name}")
        timeout, body = registration[0].group(1), registration[0].group(2)
        if timeout != "60" or command not in body or success_regex not in body:
            reject("review-test-registration-invalid", f"{name} has the wrong timeout, mode, source revision, or success assertion")

    lines = inventory.splitlines()
    for name in requirements:
        if sum(line == name for line in lines) != 1:
            reject("review-test-inventory-invalid", f"expected exactly one inventory entry for {name}")


def check(repo: Path, revision: str, implementation_sha: str | None = None,
          qualification_sha: str | None = None) -> str:
    """Validate reports from immutable Git objects. The first RED commit intentionally lacks these checks."""
    revision = resolve_commit(repo, revision, "--rev")
    checker = git_blob(repo, revision, "tests/scripts/verify-review-evidence.py", 1024 * 1024)
    try:
        running = Path(__file__).read_bytes()
    except OSError as error:
        reject("review-checker-unreadable", str(error))
    if checker is None or checker != running:
        reject("review-checker-source-mismatch", "the executing verifier differs from its blob at --rev")
    verify_registrations(repo, revision)

    # RED scaffold: this accepts a wrong implementation SHA so the registered control
    # proves the test reaches the intended identity assertion before GREEN.
    if implementation_sha is not None:
        resolve_commit(repo, implementation_sha, "--implementation-sha")
    if qualification_sha is not None and qualification_sha != revision:
        reject("review-qualification-sha-mismatch", "--qualification-sha must equal --rev")
    return f"review-evidence contract pass reports=3 findings=0 implementation={(implementation_sha or revision)[:12]}"


class Fixture:
    """Small committed subjects using the production checker and test registration."""

    def __init__(self, directory: Path) -> None:
        self.repo = directory
        self.env = {**os.environ,
                    "GIT_AUTHOR_NAME": "Review Fixture",
                    "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                    "GIT_COMMITTER_NAME": "Review Fixture",
                    "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
                    "GIT_CONFIG_GLOBAL": os.devnull,
                    "GIT_CONFIG_SYSTEM": os.devnull}
        self.run("init", "-q", "-b", "main")
        self.run("config", "core.autocrlf", "false")

    def run(self, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=self.repo, env=self.env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30)
        if result.returncode != 0:
            raise AssertionError("fixture git " + " ".join(args) + ": " + result.stderr.decode("utf-8", "replace"))
        return result.stdout.decode("utf-8").strip()

    def write(self, path: str, content: str | bytes) -> None:
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))

    def commit(self, message: str, *paths: str) -> str:
        self.run("add", "--", *paths)
        self.run("commit", "-q", "-m", message)
        return self.run("rev-parse", "HEAD")

    def reset(self, revision: str) -> None:
        self.run("checkout", "-q", "-B", "main", revision)


def report_object(role: str, reviewed_sha: str, *, reviewer_id: str | None = None,
                  report_id: str | None = None, findings: list[dict] | None = None,
                  independent: bool = True) -> dict:
    return {
        "schema_version": 1,
        "report_id": report_id or "fixture-report-" + role,
        "role": role,
        "reviewer_id": reviewer_id or "fixture-reviewer-" + role,
        "independent": independent,
        "reviewed_sha": reviewed_sha,
        "findings": findings or [],
    }


def render_report(report: dict) -> bytes:
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    return ("Independent source review fixture.\n\n" + REPORT_MARKER_START + "\n```json\n" + payload +
            "\n```\n" + REPORT_MARKER_END + "\n").encode("utf-8")


def self_test(repo: Path, source_revision: str) -> tuple[int, int]:
    """Exercise the production CLI on committed disposable subjects."""
    verify_registrations(repo, source_revision)
    cmake = git_blob(repo, source_revision, "tests/CMakeLists.txt", 8 * 1024 * 1024)
    inventory = git_blob(repo, source_revision, "tests/expected-tests.txt", 2 * 1024 * 1024)
    checker = git_blob(repo, source_revision, "tests/scripts/verify-review-evidence.py", 1024 * 1024)
    if cmake is None or inventory is None or checker is None:
        raise AssertionError("self-test source revision omitted a required fixture source")

    positives = 0
    controls = 0
    with tempfile.TemporaryDirectory(prefix="gabbaboy-review-evidence-") as temporary:
        fx = Fixture(Path(temporary))
        fx.write("tests/CMakeLists.txt", cmake)
        fx.write("tests/expected-tests.txt", inventory)
        fx.write("tests/scripts/verify-review-evidence.py", checker)
        fx.write("src/core/review-subject.c", "int review_subject(void) { return 0; }\n")
        implementation = fx.commit("implementation", "tests/CMakeLists.txt", "tests/expected-tests.txt",
                                   "tests/scripts/verify-review-evidence.py", "src/core/review-subject.c")

        fx.run("checkout", "-q", "-b", "decoy")
        fx.write("README.md", "existing but wrong implementation\n")
        wrong_implementation = fx.commit("decoy implementation", "README.md")
        fx.run("checkout", "-q", "main")

        for filename, role in REPORTS.items():
            fx.write(".planning/phases/GB-23-qualified-v0-4-0-release/" + filename,
                     render_report(report_object(role, implementation)))
        report_paths = [".planning/phases/GB-23-qualified-v0-4-0-release/" + filename for filename in REPORTS]
        report_commit = fx.commit("independent reports", *report_paths)

        def cli(at: str, *args: str) -> subprocess.CompletedProcess:
            return subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "--repo", str(fx.repo),
                                   "--rev", at, *args], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, check=False, timeout=60)

        def accepted(name: str, result: subprocess.CompletedProcess) -> None:
            nonlocal positives
            if result.returncode != 0:
                raise AssertionError(f"review positive {name} was rejected: {result.stdout}{result.stderr}")
            positives += 1

        def rejected(name: str, result: subprocess.CompletedProcess, diagnostic: str) -> None:
            nonlocal controls
            if result.returncode != 1 or diagnostic not in result.stderr:
                raise AssertionError(f"review control {name} was accepted or misclassified: {result.stdout}{result.stderr}")
            controls += 1

        accepted("complete-evidence-only-qualification",
                 cli(report_commit, "--check", "--implementation-sha", implementation,
                     "--qualification-sha", report_commit))
        rejected("wrong-existing-implementation-sha",
                 cli(report_commit, "--check", "--implementation-sha", wrong_implementation),
                 "review-implementation-mismatch")
    return positives, controls


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--rev", required=True)
    parser.add_argument("--implementation-sha")
    parser.add_argument("--qualification-sha")
    args = parser.parse_args()
    try:
        if args.self_test:
            if args.implementation_sha or args.qualification_sha:
                parser.error("--self-test does not accept implementation or qualification identities")
            positives, controls = self_test(args.repo, args.rev)
            print(f"review-evidence controls pass positives={positives} controls={controls}")
            return 0
        print(check(args.repo, args.rev, args.implementation_sha, args.qualification_sha))
        return 0
    except ReviewError as error:
        print("review-evidence rejected: " + str(error), file=sys.stderr)
        return 1
    except AssertionError as error:
        print("review-evidence self-test failed: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
