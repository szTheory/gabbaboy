#!/usr/bin/env python3
"""Regression tests for the inherited Phase 14 AGE and gate contract."""
from __future__ import annotations

import json
import importlib.util
import subprocess
from types import SimpleNamespace
import unittest
from pathlib import Path
from unittest import mock

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
    def test_live_guest_timeout_is_bounded_and_propagated(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "phase14_contract", ROOT / "tests/scripts/verify-age-phase14-contract.py")
        contract = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(contract)
        inventory = contract.read_json(contract.INVENTORY)
        speed = contract.read_json(contract.SPEED)
        rows = contract.age_speed_rows(speed)

        def observation(args, **kwargs):
            self.assertEqual(kwargs["timeout"], 45)
            case = Path(args[1]).stem
            output = "\n".join(
                f"age-assertion-row id={row['id']} expected={row['expected_hex']} "
                f"actual={row['observed_hex']} disposition={row['observed_disposition']}"
                for row in rows[case]["assertions"])
            return SimpleNamespace(returncode=0, stdout=output, stderr="")

        runner = str(Path(__file__))  # The child call is mocked; existence remains checked.
        with mock.patch.object(contract.subprocess, "run", side_effect=observation) as run:
            self.assertEqual(contract.check_age_assertions(
                ROOT, inventory, speed, run_guest=True, runner=runner,
                guest_timeout_seconds=45), (13, 142))
            self.assertEqual(run.call_count, 13)
        for invalid in (0, 46, True, 1.5):
            with self.subTest(invalid=invalid), self.assertRaises(contract.ContractError):
                contract.check_age_assertions(
                    ROOT, inventory, speed, guest_timeout_seconds=invalid)
        with mock.patch.object(contract.subprocess, "run",
                               side_effect=subprocess.TimeoutExpired("guest", 45)):
            with self.assertRaises(subprocess.TimeoutExpired):
                contract.check_age_assertions(
                    ROOT, inventory, speed, run_guest=True, runner=runner,
                    guest_timeout_seconds=45)

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
