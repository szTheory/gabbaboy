#!/usr/bin/env python3
"""Contract tests for the private CGB corpus report adapter."""

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORTER = ROOT / "tests" / "scripts" / "verify-cgb-corpus-report.py"
DAA_CASE_ID = "mooneye:acceptance/instr/daa.s"


class CorpusReportTracerTests(unittest.TestCase):
    def test_tracer_single_case_receipt(self):
        completed = subprocess.run(
            [sys.executable, "-I", str(REPORTER), "--self-test"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        receipt = json.loads(completed.stdout)
        self.assertEqual(receipt.get("schema"), "gabbaboy-cgb-corpus-receipt-v1")
        self.assertEqual(receipt.get("status"), "complete", receipt)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual([case.get("id") for case in receipt.get("cases", [])], [DAA_CASE_ID])
        self.assertEqual(receipt["counts"]["attempted_cases"], 1)
        self.assertEqual(receipt["counts"]["completed_cases"], 1)
        self.assertEqual(receipt["counts"]["observed_pass_cases"], 1)
        self.assertEqual(receipt["counts"]["assertions"], 1)


class PrivatePathFreeResult(unittest.TextTestResult):
    def _exc_info_to_string(self, err, test):
        return "{}: {}".format(err[0].__name__, err[1])


class PrivatePathFreeRunner(unittest.TextTestRunner):
    resultclass = PrivatePathFreeResult


if __name__ == "__main__":
    unittest.main(testRunner=PrivatePathFreeRunner)
