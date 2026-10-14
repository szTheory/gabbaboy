#!/usr/bin/env python3
"""Validate Phase 12 CGB speed-switch dispositions without network access."""
from __future__ import annotations

import json
import argparse
import pathlib
import re
import sys


class Mismatch(Exception):
    pass


def need(condition: bool, detail: str) -> None:
    if not condition:
        raise Mismatch(detail)


def main() -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=pathlib.Path,
                        default=root / "tests/external/cgb-speed-dispositions.json")
    args = parser.parse_args()
    record = args.record
    try:
        data = json.loads(record.read_text(encoding="utf-8"))
        need(data.get("schema") == "gabbaboy-external-dispositions-v1", "schema")
        suites = data.get("suites", [])
        need(bool(suites), "suite-set")
        rows = [(suite.get("suite", ""), row)
                for suite in suites for row in suite.get("rows", [])]
        need(len(rows) > 0, "rows-empty")
        for suite, _ in rows:
            need(bool(suite), "suite-name")
        for suite in suites:
            if suite.get("vendored") is True:
                need(re.fullmatch(r"[0-9a-f]{40}", suite.get("commit", "")) is not None,
                     f"commit {suite.get('suite', '')}")

        inventory = set()
        for rel in ("tests/expected-tests.txt", "tests/player/expected-tests.txt"):
            path = root / rel
            if path.exists():
                inventory.update(path.read_text(encoding="utf-8").split())
        for _, row in rows:
            if row.get("disposition") == "expected-failure":
                case = row.get("case", "")
                pinned_by = row.get("pinned_by", "")
                need(bool(pinned_by), f"pinned_by {case} missing")
                need(pinned_by in inventory, f"pinned_by {case} {pinned_by}")
    except (Mismatch, KeyError, ValueError, OSError) as exc:
        detail = str(exc)
        if detail.startswith("pinned_by "):
            print(f"disposition-mismatch {detail}")
        else:
            print(f"disposition-mismatch {detail}")
        return 1
    print(f"cgb-speed-dispositions pass rows={len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
