"""Regression checks for the pinned MagenTests ROM admission command."""

import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tests" / "scripts" / "reproduce-magentests.sh"


class MagenAdmissionTests(unittest.TestCase):
    def test_self_test_accepts_clean_copy_and_rejects_provenance_mutations(self):
        result = subprocess.run(
            ["bash", str(SCRIPT), "--self-test"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("self-test=pass", result.stdout)


if __name__ == "__main__":
    unittest.main()
