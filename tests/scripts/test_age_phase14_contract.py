#!/usr/bin/env python3
"""Contract tests for the inherited Phase 14 AGE timing observations."""
from __future__ import annotations

import json
import hashlib
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
        labels = [*(f"mode 0 SCX {i}" for i in range(10)),
                  "mode 1,2 SCX 0", "mode 1,2 SCX 7",
                  "mode 3 SCX 0", "mode 3 SCX 7"]
        ids = [
            *(f"stat-mode-cgbE/mode-0/scx-{i}" for i in range(10)),
            "stat-mode-cgbE/mode-1-2/scx-0",
            "stat-mode-cgbE/mode-1-2/scx-7",
            "stat-mode-cgbE/mode-3/scx-0",
            "stat-mode-cgbE/mode-3/scx-7",
        ]
        self.assertEqual([row.get("id") for row in assertions], ids)
        self.assertEqual(
            [row.get("row_index") for row in assertions], list(range(14)),
        )
        expected_address = int(fixture["expected_address"].removeprefix("$"), 16) + 1
        rom = (ROOT / "fixtures/age/stat-mode-cgbE.gb").read_bytes()
        actual_bytes = bytearray()
        row_mask = 0
        for index, row in enumerate(assertions):
            expected_hex = rom[expected_address + 8 * index:expected_address + 8 * (index + 1)].hex()
            self.assertEqual(row.get("source_label"), labels[index])
            self.assertEqual(row.get("expected_hex"), expected_hex.upper())
            observed = bytes.fromhex(row["observed_hex"])
            expected = bytes.fromhex(row["expected_hex"])
            self.assertEqual(len(observed), 8)
            matches = observed == expected
            self.assertEqual(row.get("observed_disposition"), "pass" if matches else "fail")
            if matches:
                row_mask |= 1 << index
            actual_bytes.extend(observed)
        self.assertEqual(f"{row_mask:04X}", disposition["row_mask"])
        digest_input = bytes(actual_bytes) + row_mask.to_bytes(2, "little")
        self.assertEqual(
            hashlib.sha256(digest_input).hexdigest(), disposition["signature_sha256"],
        )


if __name__ == "__main__":
    unittest.main()
