#!/usr/bin/env python3
"""Contracts for the admitted SameSuite CGB-CPU-E APU cohort."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = Path(os.environ.get("GBB_TEST_BUILD_DIR", ROOT / "build"))
if not BUILD_DIR.is_absolute():
    BUILD_DIR = ROOT / BUILD_DIR
CTEST_COMMAND = os.environ.get("GBB_CTEST_COMMAND", "ctest")
MANIFEST = ROOT / "fixtures/samesuite/manifest.json"
DISPOSITIONS = ROOT / "tests/external/cgb-apu-dispositions.json"
INVENTORY = ROOT / "tests/external/cgb-corpus-inventory.json"
VALIDATOR = ROOT / "tests/scripts/verify-cgb-apu-dispositions.py"


class SameSuiteApuMembershipTests(unittest.TestCase):
    def test_exact_apu_membership_is_admitted_and_bound(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        dispositions = json.loads(DISPOSITIONS.read_text(encoding="utf-8"))
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        members = [row for row in manifest["fixtures"] if row["alias"].startswith("apu/")]
        expected_ids = {f"samesuite:{row['source_path']}" for row in members}
        self.assertEqual(70, len(members), "the frozen SameSuite APU roster contains exactly 70 members")

        outputs = {
            row["source_id"]: row for row in inventory["outputs"]
            if row.get("source_id", "").startswith("samesuite:apu/")
        }
        self.assertEqual(expected_ids, set(outputs), "inventory membership matches every manifest source")
        for source_id, output in outputs.items():
            self.assertEqual("admitted", output["admission_status"], f"required APU output is admitted: {source_id}")

        cases = {row["id"]: row for row in inventory["cases"] if row["suite"] == "samesuite"
                 and row["source_id"].startswith("samesuite:apu/")}
        self.assertEqual(expected_ids, set(cases), "inventory cases preserve every selected source")
        self.assertEqual(70, len(dispositions["cases"]), "dispositions retain all 70 source identities")

        listed = subprocess.run(
            [CTEST_COMMAND, "--test-dir", str(BUILD_DIR), "--show-only=json-v1"],
            check=True, capture_output=True, text=True,
        )
        test_names = {row["name"] for row in json.loads(listed.stdout)["tests"]}
        expected_tests = {
            "cgb_samesuite_apu_membership",
            "cgb_samesuite_apu_controls",
            "cgb_samesuite_apu_tracer",
            "cgb_samesuite_apu_tracer_controls",
            "cgb_samesuite_apu_suite",
        }
        expected_tests.update(row["test_name"] for row in dispositions["cases"])
        self.assertTrue(expected_tests <= test_names, f"missing required APU CTests: {sorted(expected_tests - test_names)}")

        validation = subprocess.run(
            [sys.executable, "-I", str(VALIDATOR), "--membership",
             "--build-dir", str(BUILD_DIR), "--ctest-command", CTEST_COMMAND],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(0, validation.returncode, validation.stderr or validation.stdout)
        self.assertIn("cases=70 author_expectation=pass observed_pass=8 xfail=62 assertions=4784",
                      validation.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
