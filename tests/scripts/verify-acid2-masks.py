#!/usr/bin/env python3
"""Source-cell mask generation and verification for bounded acid2 comparisons."""
from __future__ import annotations

import argparse
import unittest

WIDTH = 160
HEIGHT = 144
CELL = 8


def build_mask(cells: list[tuple[int, int]]) -> bytes:
    """Red-phase scaffold: the source-cell contract test must fail until implemented."""
    return bytes(WIDTH * HEIGHT)


class MaskContractTests(unittest.TestCase):
    def test_source_cell_marks_exact_pixels(self) -> None:
        mask = build_mask([(2, 3)])
        self.assertEqual(len(mask), WIDTH * HEIGHT)
        self.assertEqual(sum(mask), CELL * CELL)
        self.assertEqual(mask[3 * CELL * WIDTH + 2 * CELL], 1)
        self.assertEqual(mask[3 * CELL * WIDTH + 3 * CELL], 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("--self-test is required")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MaskContractTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
