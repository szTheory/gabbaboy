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


if __name__ == "__main__":
    unittest.main()
