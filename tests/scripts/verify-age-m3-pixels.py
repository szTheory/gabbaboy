#!/usr/bin/env python3
"""Bounded AGE mode-3 RGB555 source-image oracle (Phase 14, D-09/D-16)."""
from __future__ import annotations

import pathlib
import sys
import unittest


def decode_png(data: bytes):
    """Decode one admitted 160x144 PNG; implemented after the RED gate."""
    return None


class TestPngDecoder(unittest.TestCase):
    def test_decode_source_png_has_160_by_144_pixels(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[2]
        image = root / "fixtures/age/references/m3-bg-lcdc-cgbBCE.png"
        decoded = decode_png(image.read_bytes())
        self.assertIsNotNone(decoded, "source PNG must decode to a bounded image")
        self.assertEqual((decoded.width, decoded.height), (160, 144))


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        unittest.main(argv=[sys.argv[0]], verbosity=1)
    else:
        raise SystemExit("usage: verify-age-m3-pixels.py --self-test")
