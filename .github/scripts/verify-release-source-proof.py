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
            or pr.get("head", {}).get("sha") != head_sha):
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
          "base": {"ref": "main"}, "head": {"sha": head}, "merge_commit_sha": source}
    checks = {"check_runs": [
        {"name": name, "head_sha": head, "status": "completed", "conclusion": "success",
         "app": {"id": 15368, "slug": EXPECTED_APP_SLUG}}
        for name in REQUIRED_CONTEXTS
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
