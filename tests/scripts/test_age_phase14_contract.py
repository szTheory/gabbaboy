#!/usr/bin/env python3
"""Contract tests for the inherited Phase 14 AGE timing observations."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class TestAgePhase14Contract(unittest.TestCase):
    def test_stat_mode_cgbe_binds_source_rows_to_expected_values(self) -> None:
        manifest = json.loads((ROOT / "fixtures/age/manifest.json").read_text())
        speed = json.loads(
            (ROOT / "tests/external/cgb-speed-dispositions.json").read_text()
        )
        fixture = next(
            row for row in manifest["fixtures"]
            if row["file"] == "stat-mode-cgbE.gb"
        )
        disposition = next(
            row for suite in speed["suites"]
            if suite["suite"] == "age-test-roms"
            for row in suite["rows"]
            if row["case"] == "stat-mode-cgbE"
        )

        self.assertEqual(fixture["rows"], 14)
        assertions = disposition.get("assertions", [])
        self.assertEqual(
            len(assertions), 14,
            "stat-mode-cgbE must bind all source-labelled expected rows",
        )
        ids = [row.get("id") for row in assertions]
        self.assertEqual(len(set(ids)), 14, "AGE assertion IDs must be unique")
        self.assertEqual(
            [row.get("row_index") for row in assertions], list(range(14)),
        )
        self.assertTrue(all(row.get("expected_hex") for row in assertions))
        self.assertTrue(all(row.get("source_label") for row in assertions))


if __name__ == "__main__":
    unittest.main()
