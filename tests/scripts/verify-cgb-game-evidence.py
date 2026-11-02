#!/usr/bin/env python3
"""Compose Phase 21's source-qualified CGB harness, candidate, and scene evidence."""
from __future__ import annotations

import argparse
import sys


class Reject(Exception):
    pass


def candidate_outcome(records: list[dict[str, object]]) -> dict[str, str] | None:
    """Return the one permitted terminal game-evidence disposition."""
    return None


def self_test() -> None:
    cases = (
        ([{"candidate_id": "potion-panic", "disposition": {"status": "admitted"}},
          {"candidate_id": "ucity-1.3", "disposition": {"status": "not-needed"}}],
         {"status": "admitted", "candidate_id": "potion-panic"}),
        ([{"candidate_id": "potion-panic", "disposition": {"status": "no-go", "reason": "rights scope"}},
          {"candidate_id": "ucity-1.3", "disposition": {"status": "admitted"}}],
         {"status": "admitted", "candidate_id": "ucity-1.3"}),
        ([{"candidate_id": "potion-panic", "disposition": {"status": "no-go", "reason": "source scope"}},
          {"candidate_id": "ucity-1.3", "disposition": {"status": "no-go", "reason": "hardware include scope"}}],
         {"status": "no-game", "candidate_id": "none"}),
    )
    for records, expected in cases:
        actual = candidate_outcome(records)
        if actual != expected:
            raise Reject(f"candidate-outcome-contract-missing: expected={expected} actual={actual}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--self-test-controls", action="store_true")
    parser.add_argument("--runner")
    parser.add_argument("--repo-root")
    parser.add_argument("--source-revision")
    parser.add_argument("--write-evidence")
    args = parser.parse_args(argv)
    if args.self_test:
        try:
            self_test()
        except Reject as error:
            print(f"verify-cgb-game-evidence: {error}", file=sys.stderr)
            return 1
        print("game-evidence self-test pass")
        return 0
    print("verify-cgb-game-evidence: implementation unavailable", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
