#!/usr/bin/env python3
"""Assert that the immutable fork checker exercises both mutation negatives."""

from __future__ import annotations

import subprocess
import sys
import unittest


CHECKER, REPO, REV, REPORT = sys.argv[1:5]


def run_controls() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", CHECKER, "--mutant-controls", "--rev", REV,
         "--repo", REPO, "--check", REPORT],
        cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, check=False,
    )


class StateForkMutantControls(unittest.TestCase):
    def test_missing_mutant_record_is_refused(self) -> None:
        result = run_controls()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("missing-record=refused", result.stdout)

    def test_unexercising_fixture_is_refused(self) -> None:
        result = run_controls()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("unexercising-fixture=refused", result.stdout)

    def test_windows_git_paths_are_normalized(self) -> None:
        result = run_controls()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("windows-git-path=normalized", result.stdout)

    def test_generic_malformed_target_reason_is_refused(self) -> None:
        result = run_controls()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("malformed-invariant-reason=refused", result.stdout)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0], *sys.argv[5:]])
