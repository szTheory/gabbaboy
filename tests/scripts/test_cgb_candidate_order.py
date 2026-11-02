#!/usr/bin/env python3
"""Regression tests for the closed two-candidate ordering contract."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


CHECKER = Path(__file__).with_name("verify-cgb-candidates.py")
SPEC = importlib.util.spec_from_file_location("verify_cgb_candidates", CHECKER)
assert SPEC is not None and SPEC.loader is not None
CHECKER_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER_MODULE)


def record(candidate_id: str, disposition: str) -> dict[str, str]:
    return {"candidate_id": candidate_id, "disposition": disposition}


def valid_isolation() -> dict[str, object]:
    return {
        "mechanism": "synthetic-namespace",
        "source_identity": {"repository": "https://example.invalid/game", "revision": "a" * 40},
        "toolchain_identity": [
            {"name": "rgbds", "version": "1.0.1", "revision": "b" * 40, "sha256": "c" * 64}
        ],
        "launcher_policy": {"path": "sandbox/launcher-policy.json", "sha256": "d" * 64},
        "environment_allowlist": ["PATH", "LANG"],
        "privilege_escalation": False,
        "mounts": [
            {"root_label": "source", "access": "read-only"},
            {"root_label": "toolchain", "access": "read-only"},
            {"root_label": "output", "access": "read-write"},
        ],
        "network_disabled": True,
        "credentials_absent": True,
        "probes": {
            "outside_root_read": {
                "baseline": "allowed", "restricted": "denied", "target": "outside-root",
                "log_id": "outside-read-control", "log_sha256": "e" * 64,
            },
            "local_network": {
                "baseline": "allowed", "restricted": "denied", "target": "local-endpoint",
                "log_id": "network-control", "log_sha256": "f" * 64,
            },
        },
    }


def admitted_record() -> dict[str, object]:
    return {
        "schema_version": 1,
        "candidate_id": "potion-panic-gbcompo25",
        "release": "GB Compo 2025",
        "preferred_artifact": "potion-panic.gb",
        "stage": "final",
        "partial": False,
        "admission": {"state": "observed", "value": {"decision_status": "approved"}},
        "rom": {
            "state": "observed",
            "value": {"size_bytes": 32768, "sha256": "1" * 64,
                      "header": {"cgb_flag": 0x80}},
        },
        "execution": {
            "state": "observed", "value": {"profile": "cgb-cpu-e", "actual_mode": "native-cgb"}
        },
        "progress": {
            "state": "observed",
            "value": {
                "positive": {"control_id": "positive", "status": "pass", "raw_reason": "predicate-reached"},
                "controls": {
                    "no_input": {"control_id": "no-input", "status": "fail", "raw_reason": "predicate-not-reached"},
                    "wrong_input": {"control_id": "wrong-input", "status": "fail", "raw_reason": "predicate-not-reached"},
                    "impossible_predicate": {"control_id": "impossible", "status": "fail", "raw_reason": "predicate-not-reached"},
                },
            },
        },
        "build": {"state": "observed", "value": {"build_isolation": valid_isolation()}},
        "disposition": {"status": "admitted"},
    }


class CandidateOrderTests(unittest.TestCase):
    def test_primary_and_fallback_no_go_form_a_valid_absence(self) -> None:
        records = [
            record("potion-panic-gbcompo25", "no-go"),
            record("ucity-1.3", "no-go"),
        ]
        self.assertIsNone(CHECKER_MODULE.validate_attempt_order(records))

    def test_missing_primary_is_rejected(self) -> None:
        records = [record("ucity-1.3", "no-go")]
        self.assertEqual(
            CHECKER_MODULE.validate_attempt_order(records), "candidate-attempt-set"
        )

    def test_fallback_without_primary_no_go_is_rejected(self) -> None:
        records = [
            record("potion-panic-gbcompo25", "admitted"),
            record("ucity-1.3", "no-go"),
        ]
        self.assertEqual(
            CHECKER_MODULE.validate_attempt_order(records), "candidate-fallback-not-eligible"
        )

    def test_admitted_subject_requires_phase20_native_progress_controls(self) -> None:
        self.assertIsNone(CHECKER_MODULE.validate_admitted_contract(admitted_record()))
        mutated = admitted_record()
        mutated["execution"]["value"]["actual_mode"] = "compatibility"
        self.assertEqual(
            CHECKER_MODULE.validate_admitted_contract(mutated), "candidate-native-mode-required"
        )

    def test_admitted_subject_requires_distinct_input_and_predicate_controls(self) -> None:
        mutated = admitted_record()
        del mutated["progress"]["value"]["controls"]["wrong_input"]
        self.assertEqual(
            CHECKER_MODULE.validate_admitted_contract(mutated), "candidate-progress-controls-missing"
        )

    def test_executed_build_requires_confined_isolation_and_denial_probes(self) -> None:
        isolation = valid_isolation()
        self.assertIsNone(CHECKER_MODULE.validate_build_isolation(isolation))
        mutations = []
        network = valid_isolation()
        network["network_disabled"] = False
        mutations.append((network, "candidate-build-isolation-network"))
        credentials = valid_isolation()
        credentials["environment_allowlist"].append("AWS_SECRET_ACCESS_KEY")
        mutations.append((credentials, "candidate-build-isolation-credentials"))
        mounts = valid_isolation()
        mounts["mounts"].append({"root_label": "extra", "access": "read-write"})
        mutations.append((mounts, "candidate-build-isolation-mounts"))
        privilege = valid_isolation()
        privilege["privilege_escalation"] = True
        mutations.append((privilege, "candidate-build-isolation-privilege"))
        outside = valid_isolation()
        outside["probes"]["outside_root_read"]["restricted"] = "allowed"
        mutations.append((outside, "candidate-build-isolation-outside-probe"))
        endpoint = valid_isolation()
        endpoint["probes"]["local_network"]["restricted"] = "allowed"
        mutations.append((endpoint, "candidate-build-isolation-network-probe"))
        for subject, expected in mutations:
            with self.subTest(expected=expected):
                self.assertEqual(CHECKER_MODULE.validate_build_isolation(subject), expected)


if __name__ == "__main__":
    unittest.main()
