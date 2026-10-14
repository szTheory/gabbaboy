#!/usr/bin/env python3
"""Check consumer-facing CGB HDMA claims against the selected bounded model."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NATIVE = (
    "docs/native-integration.md",
    "docs/support/unreleased.md",
    "docs/preview.md",
    "README.md",
)


def fail(message: str) -> int:
    print(f"CGB HDMA claims: {message}", file=sys.stderr)
    return 1


def check_native() -> int:
    for relative in NATIVE:
        path = ROOT / relative
        text = path.read_text(encoding="utf-8")
        if "HBlank DMA" not in text:
            return fail(f"{relative}: missing required behavior claim: HBlank DMA")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", action="store_true")
    args = parser.parse_args()
    return check_native()


if __name__ == "__main__":
    raise SystemExit(main())
