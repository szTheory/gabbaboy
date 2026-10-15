#!/usr/bin/env python3
"""Regression tests for the inherited Phase 14 AGE and gate contract."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "tests/external/cgb-corpus-inventory.json"
RESEARCH14_GATES = {
    "GATE-01", "GATE-02", "GATE-10", "GATE-13", "GATE-14", "GATE-15",
    "GATE-17", "GATE-18", "GATE-19", "GATE-20", "GATE-24", "GATE-27",
    "GATE-28", "GATE-29", "GATE-32", "GATE-33", "GATE-34", "GATE-35",
    "GATE-36", "GATE-40", "GATE-41", "GATE-44", "GATE-47", "GATE-48",
    "GATE-49", "GATE-50", "GATE-54", "GATE-55", "GATE-62", "GATE-76",
    "GATE-77",
}


class InheritedPhase14Contract(unittest.TestCase):
    def test_all_research14_gates_have_owned_dispositions(self) -> None:
        data = json.loads(INVENTORY.read_text(encoding="utf-8"))
        rows = data.get("research14_dispositions", [])
        self.assertEqual(
            RESEARCH14_GATES,
            {row.get("gate") for row in rows},
            "inventory must name every inherited research14 gate",
        )


if __name__ == "__main__":
    unittest.main()
