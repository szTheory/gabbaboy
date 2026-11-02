#!/usr/bin/env python3
"""Regression tests for the closed two-candidate ordering contract."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
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
                "positive": {"control_id": "positive", "status": "pass", "raw_reason": "predicate-reached",
                             "observation_sha256": "2" * 64},
                "controls": {
                    "no_input": {"control_id": "no-input", "status": "fail", "raw_reason": "predicate-not-reached",
                                 "observation_sha256": "3" * 64},
                    "wrong_input": {"control_id": "wrong-input", "status": "fail", "raw_reason": "predicate-not-reached",
                                    "observation_sha256": "4" * 64},
                    "impossible_predicate": {"control_id": "impossible-predicate", "status": "fail",
                                             "raw_reason": "predicate-not-reached", "observation_sha256": "5" * 64},
                },
            },
        },
        "build": {"state": "observed", "value": {"build_isolation": valid_isolation()}},
        "disposition": {"status": "admitted"},
    }


class CandidateOrderTests(unittest.TestCase):
    def test_cmake_source_path_key_accepts_windows_slashes_and_rejects_neighbor(self) -> None:
        backslash = r"C:\build\synthetic\src\core\gabbaboy.c"
        forward_slash = "C:/build/synthetic/src/core/gabbaboy.c"
        wrong_source = "C:/build/synthetic/src/core/gabbaboy_test.c"
        case_variant = "c:/BUILD/SYNTHETIC/src/core/gabbaboy.c"

        self.assertEqual(
            CHECKER_MODULE.cmake_source_path_key(backslash),
            CHECKER_MODULE.cmake_source_path_key(forward_slash),
        )
        self.assertNotEqual(
            CHECKER_MODULE.cmake_source_path_key(forward_slash),
            CHECKER_MODULE.cmake_source_path_key(wrong_source),
        )
        if os.name == "nt":
            self.assertEqual(
                CHECKER_MODULE.cmake_source_path_key(forward_slash),
                CHECKER_MODULE.cmake_source_path_key(case_variant),
            )
        else:
            self.assertNotEqual(
                CHECKER_MODULE.cmake_source_path_key(forward_slash),
                CHECKER_MODULE.cmake_source_path_key(case_variant),
            )

    def test_cmake_source_entry_matches_relative_file_by_filesystem_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            expected = root / "src" / "core" / "gabbaboy.c"
            expected.parent.mkdir(parents=True)
            expected.write_bytes(b"synthetic CMake source\n")
            build_dir = root / "build"
            build_dir.mkdir()

            relative_entry = {
                "directory": str(build_dir),
                "file": os.path.relpath(expected, start=build_dir),
                "command": "cc -DGBB_BUILD_QUALIFIED=1 -c source.c",
            }
            self.assertTrue(CHECKER_MODULE.cmake_source_entry_matches(relative_entry, expected, root))

            wrong_source = root / "src" / "core" / "gabbaboy_test.c"
            wrong_source.write_bytes(b"different source\n")
            wrong_entry = dict(relative_entry)
            wrong_entry["file"] = os.path.relpath(wrong_source, start=build_dir)
            self.assertFalse(CHECKER_MODULE.cmake_source_entry_matches(wrong_entry, expected, root))

            case_variant = dict(relative_entry)
            case_variant["file"] = str(expected).swapcase()
            self.assertEqual(
                CHECKER_MODULE.cmake_source_entry_matches(case_variant, expected, root),
                os.name == "nt",
            )

    def test_cmake_compile_command_accepts_arguments_form(self) -> None:
        entry = {"arguments": ["cc", "-DGBB_BUILD_QUALIFIED=1", "-c", "source.c"]}
        self.assertEqual(
            CHECKER_MODULE.cmake_compile_command(entry),
            "cc -DGBB_BUILD_QUALIFIED=1 -c source.c",
        )

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

    def test_primary_admission_makes_only_the_fallback_not_needed(self) -> None:
        records = [
            record("potion-panic-gbcompo25", "admitted"),
            record("ucity-1.3", "not-needed"),
        ]
        self.assertIsNone(CHECKER_MODULE.validate_attempt_order(records))

    def test_partial_pair_is_stage_only_and_cannot_close_final_state(self) -> None:
        records = [record("potion-panic-gbcompo25", "partial"), record("ucity-1.3", "partial")]
        self.assertIsNone(CHECKER_MODULE.validate_attempt_order(records, require_final=False))
        self.assertEqual(
            CHECKER_MODULE.validate_attempt_order(records), "candidate-partial-not-final"
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

    def test_subprocess_output_limit_is_enforced_while_child_runs(self) -> None:
        with self.assertRaisesRegex(CHECKER_MODULE.Reject, "candidate-subprocess-output-limit"):
            CHECKER_MODULE.run_process(
                [sys.executable, "-c", "import sys; sys.stdout.write('x' * 1000000)"],
                Path.cwd(), output_limit=64,
            )

    def test_subprocess_timeout_kills_and_reaps_child(self) -> None:
        with self.assertRaisesRegex(CHECKER_MODULE.Reject, "candidate-subprocess-timeout"):
            CHECKER_MODULE.run_process(
                [sys.executable, "-c", "import time; time.sleep(5)"],
                Path.cwd(), timeout=0.05,
            )


if __name__ == "__main__":
    unittest.main()
