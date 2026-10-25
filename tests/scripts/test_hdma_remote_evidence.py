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


def rejected(checker, receipt: dict) -> bool:
    try:
        checker.validate_remote_evidence(receipt, EXPECTED_HEAD)
    except checker.ContractError:
        return True
    return False


def file_rejected(checker, payload: bytes) -> bool:
    with tempfile.TemporaryDirectory(prefix="gabbaboy-remote-receipt-") as directory:
        path = Path(directory) / "remote-checks.json"
        path.write_bytes(payload)
        try:
            checker.load_remote_evidence(path)
        except checker.ContractError:
            return True
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

    stale_top_level = dict(valid_receipt(), headSha="b" * 40)

    unknown_field = valid_receipt()
    unknown_field["operatorOverride"] = True

    controls = {
        "missing-required-context": missing,
        "contradictory-duplicate": duplicate,
        "unrecognized-context": unrecognized,
        "wrong-event": wrong_event,
        "wrong-head": wrong_head,
        "wrong-workflow-provenance": wrong_workflow,
        "pending-status": pending,
        "failed-conclusion": failed_conclusion,
        "invalid-run-provenance": invalid_provenance,
        "invalid-attempt": invalid_attempt,
        "duplicate-required-context": duplicate_required,
        "stale-top-level-head": stale_top_level,
        "unrecognized-top-level-field": unknown_field,
    }
    accepted = [name for name, receipt in controls.items() if not rejected(checker, receipt)]

    with tempfile.TemporaryDirectory(prefix="gabbaboy-remote-receipt-") as directory:
        path = Path(directory) / "remote-checks.json"
        path.write_text(json.dumps(valid_receipt()), encoding="utf-8")
        checker.validate_remote_evidence(checker.load_remote_evidence(path), EXPECTED_HEAD)
    if not file_rejected(checker, b" " * (checker.MAX_REMOTE_RECEIPT_BYTES + 1)):
        accepted.append("oversized-receipt-file")
    if not file_rejected(checker, b"{malformed"):
        accepted.append("malformed-receipt-file")
    if not file_rejected(checker, b'{"headSha":"a","headSha":"b"}'):
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
