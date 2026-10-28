#!/usr/bin/env python3
"""Executable positive and negative controls for the Phase 13 remote receipt contract."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
CHECKER_PATH = ROOT / "tests/scripts/verify-hdma-lane.py"
EXPECTED_HEAD = "a" * 40
REQUIRED_CONTEXTS = (
    "required-native",
    "fixture-repro",
    "preview-package-smoke",
)
WORKFLOWS = {
    "required-native": "ci",
    "fixture-repro": "fixture-repro",
    "preview-package-smoke": "preview-package-smoke",
}


def load_checker():
    spec = importlib.util.spec_from_file_location("hdma_closure", CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load closure checker at {CHECKER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_receipt() -> dict:
    return {
        "headSha": EXPECTED_HEAD,
        "requiredJobs": list(REQUIRED_CONTEXTS),
        "results": [
            {
                "name": name,
                "workflowName": WORKFLOWS[name],
                "databaseId": 1000 + index,
                "attempt": 1,
                "event": "pull_request",
                "headSha": EXPECTED_HEAD,
                "status": "completed",
                "conclusion": "success",
            }
            for index, name in enumerate(REQUIRED_CONTEXTS)
        ],
    }


def rejected(checker, receipt: dict, reason: str) -> bool:
    """True only when the receipt is refused AND the refusal names the intended defect. A refusal for any other reason
    leaves the intended defect unexercised, so it is reported like an acceptance."""
    try:
        checker.validate_remote_evidence(receipt, EXPECTED_HEAD)
    except checker.ContractError as error:
        return reason in str(error)
    return False


def file_rejected(checker, payload: bytes, reason: str) -> bool:
    with tempfile.TemporaryDirectory(prefix="gabbaboy-remote-receipt-") as directory:
        path = Path(directory) / "remote-checks.json"
        path.write_bytes(payload)
        try:
            checker.load_remote_evidence(path)
        except checker.ContractError as error:
            return reason in str(error)
    return False


def main() -> int:
    checker = load_checker()
    checker.validate_remote_evidence(valid_receipt(), EXPECTED_HEAD)

    missing = valid_receipt()
    missing["results"] = missing["results"][:1]

    duplicate = valid_receipt()
    failed = dict(duplicate["results"][0], conclusion="failure")
    duplicate["results"] = [failed, *duplicate["results"]]

    unrecognized = valid_receipt()
    unrecognized["requiredJobs"].append("manual-green-check")
    unrecognized["results"].append({
        **unrecognized["results"][0],
        "name": "manual-green-check",
    })

    wrong_event = valid_receipt()
    wrong_event["results"][1] = dict(wrong_event["results"][1], event="push")

    wrong_head = valid_receipt()
    wrong_head["results"][2] = dict(wrong_head["results"][2], headSha="b" * 40)

    wrong_workflow = valid_receipt()
    wrong_workflow["results"][0] = dict(wrong_workflow["results"][0], workflowName="fixture-repro")

    pending = valid_receipt()
    pending["results"][0] = dict(pending["results"][0], status="in_progress")

    failed_conclusion = valid_receipt()
    failed_conclusion["results"][0] = dict(failed_conclusion["results"][0], conclusion="cancelled")

    invalid_provenance = valid_receipt()
    invalid_provenance["results"][0] = dict(invalid_provenance["results"][0], databaseId=0)

    invalid_attempt = valid_receipt()
    invalid_attempt["results"][0] = dict(invalid_attempt["results"][0], attempt=0)

    duplicate_required = valid_receipt()
    duplicate_required["requiredJobs"][-1] = duplicate_required["requiredJobs"][0]

    skipped_conclusion = valid_receipt()
    skipped_conclusion["results"][0] = dict(skipped_conclusion["results"][0], conclusion="skipped")

    reused_run = valid_receipt()
    reused_run["results"][1] = dict(reused_run["results"][1], databaseId=reused_run["results"][0]["databaseId"])

    stale_top_level = dict(valid_receipt(), headSha="b" * 40)

    unknown_field = valid_receipt()
    unknown_field["operatorOverride"] = True

    # name -> (receipt, text the refusal must contain)
    controls = {
        "missing-required-context": (missing, "exactly the three authoritative PR context results"),
        "contradictory-duplicate": (duplicate, "exactly the three authoritative PR context results"),
        "unrecognized-context": (unrecognized, "must name the three authoritative PR contexts"),
        "wrong-event": (wrong_event, "is not from a pull_request event"),
        "wrong-head": (wrong_head, "is stale"),
        "wrong-workflow-provenance": (wrong_workflow, "has the wrong workflow provenance"),
        "pending-status": (pending, "is skipped, pending, or failed"),
        "failed-conclusion": (failed_conclusion, "is skipped, pending, or failed"),
        "skipped-conclusion": (skipped_conclusion, "is skipped, pending, or failed"),
        "invalid-run-provenance": (invalid_provenance, "invalid GitHub run databaseId"),
        "reused-run-id": (reused_run, "reuses a GitHub run databaseId"),
        "invalid-attempt": (invalid_attempt, "invalid GitHub run attempt"),
        "duplicate-required-context": (duplicate_required, "requiredJobs contains duplicates"),
        "stale-top-level-head": (stale_top_level, "remote result head is stale"),
        "unrecognized-top-level-field": (unknown_field, "must contain only headSha, requiredJobs, and results"),
    }
    accepted = [name for name, (receipt, reason) in controls.items() if not rejected(checker, receipt, reason)]

    with tempfile.TemporaryDirectory(prefix="gabbaboy-remote-receipt-") as directory:
        path = Path(directory) / "remote-checks.json"
        path.write_text(json.dumps(valid_receipt()), encoding="utf-8")
        checker.validate_remote_evidence(checker.load_remote_evidence(path), EXPECTED_HEAD)
    if not file_rejected(checker, b" " * (checker.MAX_REMOTE_RECEIPT_BYTES + 1), "exceeds"):
        accepted.append("oversized-receipt-file")
    if not file_rejected(checker, b"{malformed", "is malformed"):
        accepted.append("malformed-receipt-file")
    if not file_rejected(checker, b'{"headSha":"a","headSha":"b"}', "duplicate JSON field"):
        accepted.append("duplicate-json-field")
    if accepted:
        print("hdma-remote-evidence controls failed; invalid receipts accepted=" + ",".join(accepted),
              file=sys.stderr)
        return 1

    print("hdma-remote-evidence controls pass positive=1 negative=%d contexts=%d" %
          (len(controls) + 3, len(REQUIRED_CONTEXTS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
