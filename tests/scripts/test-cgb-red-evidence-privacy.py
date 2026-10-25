#!/usr/bin/env python3
"""Keep committed RED evidence free of absolute workstation paths."""
from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
# Completed-milestone record: read from the v0.2 archive, never the live phases directory (Phase 16 TUNE-01).
PHASE = ROOT / ".planning/milestones/v0.2-phases/GB-14-cgb-e-model-qualification-and-corpus"
RED_RECORDS = (
    "14-07-task3-red-evidence.json",
    "14-09-red-task1.json",
    "14-09-red-task2.json",
    "14-10-red-task1.json",
    "14-10-red-task2.json",
)
ABSOLUTE_PATH = re.compile(r"(?<![A-Za-z0-9_.])/(?:Users|home|private|tmp)/[^\s\"'<>]+")


def has_absolute_path(output: str) -> bool:
    return ABSOLUTE_PATH.search(output) is not None


class RedEvidencePrivacyTests(unittest.TestCase):
    def test_records_have_only_repository_relative_paths(self) -> None:
        leaking_records = []
        for filename in RED_RECORDS:
            try:
                record = json.loads((PHASE / filename).read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                self.fail(f"RED evidence record is unavailable or invalid: {filename}")
            output = record.get("output")
            if type(output) is not str:
                self.fail(f"RED evidence output is missing: {filename}")
            if has_absolute_path(output):
                leaking_records.append(filename)
        self.assertFalse(leaking_records,
                         "absolute workstation paths remain in RED records: " +
                         ", ".join(leaking_records))

    def test_classifier_detects_a_synthetic_absolute_path(self) -> None:
        self.assertTrue(has_absolute_path(
            'Traceback: File "/home/example/project/tests/test_case.py", line 4'))


if __name__ == "__main__":
    unittest.main(verbosity=2)
