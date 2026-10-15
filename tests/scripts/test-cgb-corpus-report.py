#!/usr/bin/env python3
"""Contract tests for the private CGB corpus report adapter."""

import json
import subprocess
import sys
import tempfile
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

    def test_tracer_controls(self):
        completed = subprocess.run(
            [sys.executable, "-I", str(REPORTER), "--self-test-controls"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("cgb-corpus-report tracer-controls pass clean=1 altered=1 stale-green=1",
                      completed.stdout)
        with tempfile.TemporaryDirectory(prefix="cgb-report-control-", dir=ROOT / "build") as temp:
            base = Path(temp)
            fake_build = base / "missing-build"
            receipt_path = base / "receipt.json"
            receipt_path.write_text(
                '{"schema":"gabbaboy-cgb-corpus-receipt-v1","status":"complete"}\n',
                encoding="utf-8",
            )
            failed = subprocess.run(
                [sys.executable, "-I", str(REPORTER), "--run", "--build-dir", str(fake_build),
                 "--receipt", str(receipt_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0)
            current = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(current.get("status"), "incomplete", current)
            self.assertEqual(current.get("counts", {}).get("completed_cases"), 0, current)
            self.assertEqual(current.get("failure_codes"), ["input-unavailable"], current)


class PrivatePathFreeResult(unittest.TextTestResult):
    def _exc_info_to_string(self, err, test):
        return "{}: {}".format(err[0].__name__, err[1])


class PrivatePathFreeRunner(unittest.TextTestRunner):
    resultclass = PrivatePathFreeResult


if __name__ == "__main__":
    unittest.main(testRunner=PrivatePathFreeRunner)
