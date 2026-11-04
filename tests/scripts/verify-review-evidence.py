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


class DuplicateJSONKey(ValueError):
    """Raised when a marked report object repeats a property."""


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
    object_name = f"{revision}:{path}"
    size_result = git(repo, "cat-file", "-s", object_name, check=False)
    if size_result.returncode != 0:
        return None
    try:
        size = int(size_result.stdout.strip())
    except ValueError:
        reject("review-source-invalid", f"Git returned an invalid object size for {path}")
    if size > limit:
        reject("review-source-too-large", path)
    result = git(repo, "cat-file", "blob", object_name)
    if len(result.stdout) != size:
        reject("review-source-invalid", f"Git returned a truncated object for {path}")
    return result.stdout


def is_ancestor(repo: Path, older: str, newer: str) -> bool:
    return git(repo, "merge-base", "--is-ancestor", older, newer, check=False).returncode == 0


def string_value(value: object, label: str, *, required: bool = True, maximum: int = 8192) -> str | None:
    if value is None and not required:
        return None
    if type(value) is not str or (required and not value.strip()):
        reject("review-report-shape-invalid", f"{label} must be a nonempty string")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError:
        reject("review-report-shape-invalid", f"{label} is not valid UTF-8")
    if size > maximum:
        reject("review-report-shape-invalid", f"{label} exceeds {maximum} bytes")
    return value


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKey(key)
        result[key] = value
    return result


def parse_report(path: str, role: str, raw: bytes) -> dict:
    if len(raw) > MAX_REPORT_BYTES:
        reject("review-report-too-large", path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        reject("review-report-invalid", f"{path} is not UTF-8")
    if text.count(REPORT_MARKER_START) != 1 or text.count(REPORT_MARKER_END) != 1:
        reject("review-report-markers-invalid", f"{path} must contain exactly one marked JSON block")
    marker_start = text.find(REPORT_MARKER_START) + len(REPORT_MARKER_START)
    marker_end = text.find(REPORT_MARKER_END)
    if marker_end <= marker_start:
        reject("review-report-markers-invalid", f"{path} has reversed evidence markers")
    block = text[marker_start:marker_end].strip()
    if block.count("```") != 2:
        reject("review-report-markers-invalid", f"{path} must contain one JSON fence")
    match = re.fullmatch(r"```json[ \t]*\r?\n(\{.*\})\r?\n```[ \t]*", block, re.DOTALL)
    if match is None:
        reject("review-report-markers-invalid", f"{path} must contain exactly one JSON object in a json fence")
    try:
        report = json.loads(match.group(1), object_pairs_hook=unique_object)
    except DuplicateJSONKey as error:
        reject("review-report-duplicate-key", f"{path} repeats {error}")
    except (json.JSONDecodeError, UnicodeError, RecursionError) as error:
        reject("review-report-invalid", f"{path} has malformed JSON: {error}")
    if type(report) is not dict:
        reject("review-report-shape-invalid", f"{path} JSON root must be an object")
    expected = {"schema_version", "report_id", "role", "reviewer_id", "independent", "reviewed_sha", "findings"}
    if set(report) != expected:
        reject("review-report-shape-invalid", f"{path} has missing or unknown top-level keys")
    if type(report["schema_version"]) is not int or report["schema_version"] != 1:
        reject("review-report-shape-invalid", f"{path} schema_version must be integer 1")
    report["report_id"] = string_value(report["report_id"], f"{path}.report_id", maximum=256)
    report["reviewer_id"] = string_value(report["reviewer_id"], f"{path}.reviewer_id", maximum=256)
    if report["role"] != role:
        reject("review-report-role-invalid", f"{path} must declare role {role}")
    if type(report["independent"]) is not bool or report["independent"] is not True:
        reject("review-report-independence-invalid", f"{path} must declare independent=true")
    sha = report["reviewed_sha"]
    if type(sha) is not str or SHA1.fullmatch(sha) is None:
        reject("review-report-sha-invalid", f"{path}.reviewed_sha must be a full lowercase commit SHA")
    if type(report["findings"]) is not list or len(report["findings"]) > MAX_FINDINGS:
        reject("review-report-findings-invalid", f"{path}.findings must be an array of at most {MAX_FINDINGS} entries")
    return report


def validate_findings(repo: Path, report: dict, path: str) -> int:
    identifiers = set()
    for index, finding in enumerate(report["findings"]):
        label = f"{path}.findings[{index}]"
        if type(finding) is not dict:
            reject("review-finding-invalid", f"{label} must be an object")
        keys = {"id", "category", "severity", "required_property", "disposition", "rationale",
                "fix_sha", "verification_ref"}
        if set(finding) != keys:
            reject("review-finding-invalid", f"{label} has missing or unknown keys")
        identifier = string_value(finding["id"], f"{label}.id", maximum=256)
        if identifier in identifiers:
            reject("review-finding-duplicate-id", f"{path} repeats finding id {identifier}")
        identifiers.add(identifier)
        category = finding["category"]
        severity = finding["severity"]
        disposition = finding["disposition"]
        if type(category) is not str or category not in {"correctness", "security", "other"}:
            reject("review-finding-invalid", f"{label}.category is outside the closed enum")
        if type(severity) is not str or severity not in {"low", "medium", "high", "critical", "blocking"}:
            reject("review-finding-invalid", f"{label}.severity is outside the closed enum")
        if type(disposition) is not str or disposition not in {"open", "fixed", "rejected"}:
            reject("review-finding-disposition-invalid", f"{label}.disposition is outside the closed enum")
        string_value(finding["required_property"], f"{label}.required_property")
        string_value(finding["rationale"], f"{label}.rationale")
        fix_sha = string_value(finding["fix_sha"], f"{label}.fix_sha", required=False, maximum=40)
        verification = string_value(finding["verification_ref"], f"{label}.verification_ref", required=False)
        if disposition == "open":
            if fix_sha is not None or verification is not None:
                reject("review-finding-disposition-invalid", f"{label} open finding must have null fix_sha and verification_ref")
            if category in {"correctness", "security"} or severity in {"high", "critical", "blocking"}:
                reject("review-finding-open-blocking", f"{label} is an unresolved correctness/security or high finding")
        elif disposition == "fixed":
            if fix_sha is None or verification is None:
                reject("review-finding-disposition-invalid", f"{label} fixed finding needs fix_sha and verification_ref")
            try:
                resolve_commit(repo, fix_sha, f"{label}.fix_sha")
            except ReviewError:
                reject("review-finding-fix-sha-invalid", f"{label}.fix_sha does not name an existing commit")
            if not is_ancestor(repo, fix_sha, report["reviewed_sha"]):
                reject("review-finding-fix-sha-invalid", f"{label}.fix_sha is not included in reviewed_sha")
        else:
            if fix_sha is not None or verification is None:
                reject("review-finding-disposition-invalid", f"{label} rejected finding needs null fix_sha and verification_ref")
    return len(report["findings"])


QUALIFICATION_ALLOWLIST = {
    ".planning/phases/GB-23-qualified-v0-4-0-release/23-REVIEW.md",
    ".planning/phases/GB-23-qualified-v0-4-0-release/23-SECURITY.md",
    ".planning/phases/GB-23-qualified-v0-4-0-release/23-ADVERSARIAL.md",
    ".planning/phases/GB-23-qualified-v0-4-0-release/23-EVIDENCE.md",
    ".planning/phases/GB-23-qualified-v0-4-0-release/23-VALIDATION.md",
    ".planning/phases/GB-23-qualified-v0-4-0-release/23-04-SUMMARY.md",
}


def has_unexpected_changes(repo: Path, older: str, newer: str) -> bool:
    """Ask Git whether any non-evidence path changed without materializing its path list."""
    excluded = [f":(top,exclude,literal){path}" for path in sorted(QUALIFICATION_ALLOWLIST)]
    result = git(repo, "diff", "--quiet", "--no-renames", older, newer, "--", ".", *excluded,
                 check=False)
    if result.returncode not in {0, 1}:
        reject("review-git-failed", "git diff --quiet could not compare implementation and qualification")
    return result.returncode == 1


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
    if (helper is None or any(fragment not in helper.group(1) for fragment in required_helper) or
            helper.group(1).count("set(command ") != 1 or helper.group(1).count("add_test(") != 1 or
            helper.group(1).count("set_tests_properties(") != 1 or
            re.search(r"set_property\s*\(\s*TEST\b", helper.group(1))):
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
        registration = list(re.finditer(rf"(?m)^gbb_add_v02_contract\({re.escape(name)}(?=\s)", cmake))
        if len(registration) != 1 or cmake.count(name) != 1:
            reject("review-test-registration-invalid", f"expected exactly one registration for {name}")
        start = registration[0].start()
        line_end = cmake.find("\n", start)
        close = cmake.find(")\n", line_end + 1)
        if line_end < 0 or close < 0:
            reject("review-test-registration-invalid", f"{name} registration is unterminated")
        timeout_match = re.search(rf"^gbb_add_v02_contract\({re.escape(name)}\s+(\d+)\s*$",
                                  cmake[start:line_end], re.M)
        if timeout_match is None:
            reject("review-test-registration-invalid", f"{name} timeout is missing")
        timeout, body = timeout_match.group(1), cmake[line_end + 1:close]
        expected_body = f"{success_regex} {command}"
        if timeout != "60" or " ".join(body.split()) != " ".join(expected_body.split()):
            reject("review-test-registration-invalid", f"{name} has the wrong timeout, mode, source revision, or success assertion")

    lines = inventory.splitlines()
    for name in requirements:
        if sum(line == name for line in lines) != 1:
            reject("review-test-inventory-invalid", f"expected exactly one inventory entry for {name}")


def check(repo: Path, revision: str, implementation_sha: str | None = None,
          qualification_sha: str | None = None) -> str:
    """Validate reports and qualification identity only from immutable Git objects."""
    revision = resolve_commit(repo, revision, "--rev")
    checker = git_blob(repo, revision, "tests/scripts/verify-review-evidence.py", 1024 * 1024)
    try:
        running = Path(__file__).read_bytes()
    except OSError as error:
        reject("review-checker-unreadable", str(error))
    if checker is None or checker != running:
        reject("review-checker-source-mismatch", "the executing verifier differs from its blob at --rev")
    verify_registrations(repo, revision)

    requested_implementation = None
    if implementation_sha is not None:
        requested_implementation = resolve_commit(repo, implementation_sha, "--implementation-sha")
    if qualification_sha is not None:
        qualification = resolve_commit(repo, qualification_sha, "--qualification-sha")
        if qualification != revision:
            reject("review-qualification-sha-mismatch", "--qualification-sha must equal --rev")

    phase = ".planning/phases/GB-23-qualified-v0-4-0-release/"
    reports = []
    for filename, role in REPORTS.items():
        path = phase + filename
        raw = git_blob(repo, revision, path)
        if raw is None:
            reject("review-report-missing", f"{path} is absent at --rev")
        reports.append((path, parse_report(filename, role, raw)))

    reviewer_ids = [report["reviewer_id"] for _, report in reports]
    report_ids = [report["report_id"] for _, report in reports]
    if len(set(reviewer_ids)) != len(reviewer_ids) or len(set(report_ids)) != len(report_ids):
        reject("review-report-identities-duplicate", "reviewer_id and report_id values must each be pairwise distinct")

    reviewed_shas = {report["reviewed_sha"] for _, report in reports}
    if len(reviewed_shas) != 1:
        reject("review-report-sha-mismatch", "all three reports must name the same implementation commit")
    reviewed_sha = resolve_commit(repo, next(iter(reviewed_shas)), "reviewed_sha")
    if not is_ancestor(repo, reviewed_sha, revision):
        reject("review-report-not-ancestor", "reviewed implementation is not an ancestor of --rev")
    if requested_implementation is not None and reviewed_sha != requested_implementation:
        reject("review-implementation-mismatch", "reports do not name --implementation-sha")

    finding_count = 0
    for path, report in reports:
        finding_count += validate_findings(repo, report, path)

    if qualification_sha is not None:
        if not is_ancestor(repo, reviewed_sha, revision):
            reject("review-qualification-not-descendant", "qualification must descend from the reviewed implementation")
        if has_unexpected_changes(repo, reviewed_sha, revision):
            reject("review-qualification-source-drift", "non-evidence paths changed after review")
    return (f"review-evidence contract pass reports=3 findings={finding_count} "
            f"implementation={reviewed_sha[:12]}")


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
        fixture_base = fx.commit("fixture source", "tests/CMakeLists.txt", "tests/expected-tests.txt",
                                 "tests/scripts/verify-review-evidence.py", "src/core/review-subject.c")
        fx.write("src/core/review-subject.c", "/* reviewed implementation */\nint review_subject(void) { return 0; }\n")
        implementation = fx.commit("implementation", "src/core/review-subject.c")

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

        def base_accept(name: str = "complete-evidence-only-qualification") -> None:
            accepted(name, cli(report_commit, "--check", "--implementation-sha", implementation,
                               "--qualification-sha", report_commit))

        base_accept()

        def report_case(name: str, diagnostic: str, changes: dict[str, bytes | dict]) -> None:
            base_accept("accepted-counterpart-" + name)
            fx.reset(report_commit)
            paths = []
            for filename, value in changes.items():
                path = phase_path(filename)
                payload = value if isinstance(value, bytes) else render_report(value)
                fx.write(path, payload)
                paths.append(path)
            mutant = fx.commit("control " + name, *paths)
            rejected(name, cli(mutant, "--check", "--implementation-sha", implementation), diagnostic)

        def phase_path(filename: str) -> str:
            return ".planning/phases/GB-23-qualified-v0-4-0-release/" + filename

        # The reports are sound; the supplied existing commit is intentionally wrong.
        base_accept("accepted-counterpart-wrong-existing-implementation-sha")
        rejected("wrong-existing-implementation-sha",
                 cli(report_commit, "--check", "--implementation-sha", wrong_implementation),
                 "review-implementation-mismatch")

        stale = report_object(REPORTS["23-SECURITY.md"], fixture_base,
                              reviewer_id="fixture-reviewer-security")
        report_case("independently-stale-report-sha", "review-report-sha-mismatch",
                    {"23-SECURITY.md": stale})

        report_case("missing-role", "review-report-role-invalid",
                    {"23-SECURITY.md": report_object("release-consumer", implementation)})
        duplicate_reviewer = report_object("security", implementation, reviewer_id="fixture-reviewer-release-consumer")
        report_case("duplicate-reviewer-identity", "review-report-identities-duplicate",
                    {"23-SECURITY.md": duplicate_reviewer})
        duplicate_report = report_object("security", implementation, report_id="fixture-report-release-consumer")
        report_case("duplicate-report-identity", "review-report-identities-duplicate",
                    {"23-SECURITY.md": duplicate_report})
        report_case("false-independence", "review-report-independence-invalid",
                    {"23-SECURITY.md": report_object("security", implementation, independent=False)})

        review_json = report_object("release-consumer", implementation)
        unknown_key = dict(review_json, unexpected=True)
        report_case("unknown-schema-key", "review-report-shape-invalid", {"23-REVIEW.md": unknown_key})
        duplicate_key_bytes = ("Independent review.\n" + REPORT_MARKER_START + "\n```json\n"
                               + '{"schema_version":1,"schema_version":1}\n```\n'
                               + REPORT_MARKER_END + "\n").encode("utf-8")
        report_case("duplicate-json-key", "review-report-duplicate-key", {"23-REVIEW.md": duplicate_key_bytes})
        malformed_markers = b"Independent review with no evidence block.\n"
        report_case("malformed-markers", "review-report-markers-invalid", {"23-REVIEW.md": malformed_markers})
        malformed_schema = report_object("release-consumer", implementation)
        malformed_schema["schema_version"] = True
        report_case("malformed-schema", "review-report-shape-invalid", {"23-REVIEW.md": malformed_schema})

        def finding(*, category: str = "other", severity: str = "medium", disposition: str = "open",
                    fix_sha: str | None = None, verification_ref: str | None = None) -> dict:
            return {"id": "F-1", "category": category, "severity": severity,
                    "required_property": "The stated boundary must hold.", "disposition": disposition,
                    "rationale": "The source review examined the relevant implementation and evidence.",
                    "fix_sha": fix_sha, "verification_ref": verification_ref}

        for name, item in (
            ("open-correctness", finding(category="correctness")),
            ("open-high-other", finding(severity="high")),
            ("open-blocking-security", finding(category="security", severity="blocking")),
        ):
            report_case(name, "review-finding-open-blocking",
                        {"23-REVIEW.md": report_object("release-consumer", implementation, findings=[item])})

        invalid_disposition = finding(disposition="deferred")
        report_case("invalid-disposition", "review-finding-disposition-invalid",
                    {"23-REVIEW.md": report_object("release-consumer", implementation,
                                                   findings=[invalid_disposition])})
        bad_fix = finding(disposition="fixed", fix_sha="not-a-commit", verification_ref="tests/review-control")
        report_case("invalid-fixed-sha", "review-finding-fix-sha-invalid",
                    {"23-REVIEW.md": report_object("release-consumer", implementation, findings=[bad_fix])})
        missing_verification = finding(disposition="fixed", fix_sha=implementation)
        report_case("fixed-without-verification", "review-finding-disposition-invalid",
                    {"23-REVIEW.md": report_object("release-consumer", implementation,
                                                   findings=[missing_verification])})

        # These are accepted disposition counterparts, including a real in-history fix.
        for name, item in (
            ("nonblocking-open-finding", finding()),
            ("verified-fixed-finding", finding(disposition="fixed", fix_sha=implementation,
                                                verification_ref="tests/review-control")),
            ("reviewer-rejected-finding", finding(disposition="rejected",
                                                   verification_ref="tests/review-control")),
        ):
            fx.reset(report_commit)
            fx.write(phase_path("23-REVIEW.md"), render_report(
                report_object("release-consumer", implementation, findings=[item])))
            accepted(name, cli(fx.commit("accepted " + name, phase_path("23-REVIEW.md")),
                               "--check", "--implementation-sha", implementation))

        def source_case(name: str, diagnostic: str, mutate) -> None:
            base_accept("accepted-counterpart-" + name)
            fx.reset(report_commit)
            cmake_text = git_blob(fx.repo, report_commit, "tests/CMakeLists.txt", 8 * 1024 * 1024).decode("utf-8")
            inventory_text = git_blob(fx.repo, report_commit, "tests/expected-tests.txt", 2 * 1024 * 1024).decode("utf-8")
            cmake_text, inventory_text = mutate(cmake_text, inventory_text)
            changed = []
            if cmake_text != git_blob(fx.repo, report_commit, "tests/CMakeLists.txt", 8 * 1024 * 1024).decode("utf-8"):
                fx.write("tests/CMakeLists.txt", cmake_text)
                changed.append("tests/CMakeLists.txt")
            if inventory_text != git_blob(fx.repo, report_commit, "tests/expected-tests.txt", 2 * 1024 * 1024).decode("utf-8"):
                fx.write("tests/expected-tests.txt", inventory_text)
                changed.append("tests/expected-tests.txt")
            mutant = fx.commit("control " + name, *changed)
            rejected(name, cli(mutant, "--check", "--implementation-sha", implementation), diagnostic)

        def block_for(cmake_text: str, target: str) -> tuple[int, int]:
            start = cmake_text.find("gbb_add_v02_contract(" + target)
            if start < 0:
                raise AssertionError("fixture registration not found: " + target)
            line_end = cmake_text.find("\n", start)
            close = cmake_text.find(")\n", line_end + 1)
            if close < 0:
                raise AssertionError("fixture registration did not terminate: " + target)
            return start, close + 1

        def edit_contract(transform):
            def mutate(cmake_text: str, inventory_text: str):
                start, end = block_for(cmake_text, "phase23_review_evidence_contract")
                return transform(cmake_text, start, end), inventory_text
            return mutate

        def edit_controls(transform):
            def mutate(cmake_text: str, inventory_text: str):
                start, end = block_for(cmake_text, "phase23_review_evidence_controls")
                return transform(cmake_text, start, end), inventory_text
            return mutate

        def change_block(cmake_text: str, start: int, end: int, old: str, new: str) -> str:
            block = cmake_text[start:end]
            if old not in block:
                raise AssertionError("fixture expected text not found: " + old)
            return cmake_text[:start] + block.replace(old, new, 1) + cmake_text[end:]

        def remove_contract(cmake_text: str, start: int, end: int) -> str:
            return cmake_text[:start] + cmake_text[end:]

        source_case("missing-contract-registration", "review-test-registration-invalid",
                    edit_contract(remove_contract))
        source_case("wrong-control-mode", "review-test-registration-invalid",
                    edit_controls(lambda text, start, end: change_block(
                        text, start, end, "--self-test", "--check")))
        source_case("wrong-contract-timeout", "review-test-registration-invalid",
                    edit_contract(lambda text, start, end: change_block(text, start, end,
                                                                         "contract 60", "contract 61")))
        source_case("wrong-control-regex", "review-test-registration-invalid",
                    edit_controls(lambda text, start, end: change_block(text, start, end,
                        "positives=[1-9][0-9]*", "positives=0")))
        source_case("wrong-revision-argument", "review-test-registration-invalid",
                    edit_controls(lambda text, start, end: change_block(text, start, end,
                        "${GBB_STATE_SOURCE_REV}", "${OTHER_REVISION}")))

        def remove_isolation(cmake_text: str, inventory_text: str):
            helper_start = cmake_text.find("function(gbb_add_v02_contract name timeout regex script)")
            helper_end = cmake_text.find("endfunction()", helper_start)
            helper = cmake_text[helper_start:helper_end]
            if 'Python3_EXECUTABLE}" -I' not in helper:
                raise AssertionError("fixture isolated-interpreter wrapper not found")
            helper = helper.replace('Python3_EXECUTABLE}" -I', 'Python3_EXECUTABLE}"', 1)
            return cmake_text[:helper_start] + helper + cmake_text[helper_end:], inventory_text

        source_case("weakened-test-wrapper", "review-test-registration-invalid", remove_isolation)

        def inventory_missing(cmake_text: str, inventory_text: str):
            return cmake_text, inventory_text.replace("phase23_review_evidence_controls\n", "", 1)

        def inventory_duplicate(cmake_text: str, inventory_text: str):
            return cmake_text, inventory_text + "phase23_review_evidence_controls\n"

        source_case("missing-inventory-entry", "review-test-inventory-invalid", inventory_missing)
        source_case("duplicate-inventory-entry", "review-test-inventory-invalid", inventory_duplicate)

        base_accept("accepted-counterpart-evidence-only-qualification")
        for name, path in (
            ("non-evidence-source-change-after-review", "README.md"),
            ("unlisted-same-phase-directory-change", phase_path("23-OTHER.md")),
        ):
            base_accept("accepted-counterpart-" + name)
            fx.reset(report_commit)
            fx.write(path, "unreviewed source change\n")
            drifted_qualification = fx.commit("non-evidence change after review", path)
            rejected(name, cli(drifted_qualification, "--check", "--implementation-sha", implementation,
                               "--qualification-sha", drifted_qualification),
                     "review-qualification-source-drift")

        # Make this the last fixture operation: its dirty-only repair is intentional.
        base_accept("accepted-counterpart-missing-report")
        fx.reset(implementation)
        for filename, role in REPORTS.items():
            if filename != "23-ADVERSARIAL.md":
                fx.write(phase_path(filename), render_report(report_object(role, implementation)))
        missing_commit = fx.commit("commit only two reports", phase_path("23-REVIEW.md"), phase_path("23-SECURITY.md"))
        fx.write(phase_path("23-ADVERSARIAL.md"), render_report(report_object("adversarial", implementation)))
        rejected("dirty-working-tree-cannot-repair-missing-report",
                 cli(missing_commit, "--check", "--implementation-sha", implementation),
                 "review-report-missing")
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
