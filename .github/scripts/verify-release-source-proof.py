#!/usr/bin/env python3
"""Validate the frozen release source receipt against live PR/check-run evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


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
    args = parser.parse_args()
    if args.self_test:
        run_self_test()
        captured_shape_self_test()
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
