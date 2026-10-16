#!/usr/bin/env python3
"""Validate bounded v0.2.0 libFuzzer campaign evidence."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path


def validate_receipt(path: Path) -> None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"receipt unreadable: {exc.__class__.__name__}") from exc
    if not isinstance(value, dict) or value.get("status") != "complete":
        raise ValueError("receipt status must be complete")


class ReceiptContractTests(unittest.TestCase):
    def test_rejects_zero_execution_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps({"status": "complete", "executions": 0}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "executions must be greater than zero"):
                validate_receipt(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(ReceiptContractTests)
        )
        return 0 if result.wasSuccessful() else 1
    if args.verify:
        try:
            validate_receipt(args.verify)
        except ValueError as exc:
            print(f"receipt rejected: {exc}", file=sys.stderr)
            return 1
        print("receipt accepted")
        return 0
    parser.error("choose --verify or --self-test")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
