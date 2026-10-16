#!/usr/bin/env python3
"""Verify relocated C and C++ consumers against an installed GabbaBoy package."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve()


class ConsumerContractTests(unittest.TestCase):
    def test_relocated_prefix_runs_both_consumers(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-v02-red-") as tmp:
            output = Path(tmp) / "receipt.json"
            command = [
                sys.executable, "-I", str(SCRIPT), "--prefix",
                str(ROOT / "build" / "relocated-prefix"), "--output", str(output),
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            receipt = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(receipt["result"], "passed")
            self.assertEqual(set(receipt["results"]), {"c", "cpp"})


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(ConsumerContractTests)
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1
    print("consumer-driver-not-implemented", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
