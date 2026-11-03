#!/usr/bin/env python3
"""Source-cell mask generation and verification for bounded acid2 comparisons."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import struct
import unittest
import zlib

WIDTH = 160
HEIGHT = 144
CELL = 8
MAX_CELLS = 72
MAX_MASKED_PIXELS = 72 * CELL * CELL
MIN_UNMASKED_PIXELS = WIDTH * HEIGHT - MAX_MASKED_PIXELS
MAX_SOURCE_BYTES = 64 * 1024


class MaskRefused(ValueError):
    pass


def build_mask(cells: list[tuple[int, int]]) -> bytes:
    """Build a fixed 160x144 binary mask from unique 20x18 source tile cells."""
    if not isinstance(cells, list) or not cells or len(cells) > MAX_CELLS:
        raise MaskRefused("mask-cell-count-invalid")
    pixels = bytearray(WIDTH * HEIGHT)
    seen: set[tuple[int, int]] = set()
    for cell in cells:
        if (not isinstance(cell, tuple) or len(cell) != 2
                or any(isinstance(part, bool) or not isinstance(part, int) for part in cell)):
            raise MaskRefused("mask-cell-invalid")
        column, row = cell
        if not (0 <= column < WIDTH // CELL and 0 <= row < HEIGHT // CELL):
            raise MaskRefused("mask-cell-out-of-range")
        if cell in seen:
            raise MaskRefused("mask-cell-duplicate")
        seen.add(cell)
        for y in range(row * CELL, (row + 1) * CELL):
            start = y * WIDTH + column * CELL
            pixels[start:start + CELL] = b"\x01" * CELL
    return bytes(pixels)


def source_cells(source: bytes) -> list[tuple[int, int]]:
    """Derive visible tile-map cells written with tile 1 from the original control source."""
    if not isinstance(source, bytes) or len(source) > MAX_SOURCE_BYTES:
        raise MaskRefused("source-size-invalid")
    try:
        text = source.decode("ascii", errors="strict")
    except UnicodeDecodeError:
        raise MaskRefused("source-encoding-invalid") from None
    accumulator: int | None = None
    cells: list[tuple[int, int]] = []
    for original in text.splitlines():
        line = original.split(";", 1)[0].strip().upper()
        if not line:
            continue
        load = re.fullmatch(r"LD\s+A\s*,\s*(0X[0-9A-F]{1,4}|[0-9]{1,4})", line)
        if load:
            accumulator = int(load.group(1), 0)
            continue
        store = re.fullmatch(r"LD\s*\(\s*(0X[0-9A-F]{4})\s*\)\s*,\s*A", line)
        if store:
            address = int(store.group(1), 16)
            if 0x9800 <= address < 0x9C00 and accumulator == 1:
                offset = address - 0x9800
                column, row = offset % 32, offset // 32
                if column >= WIDTH // CELL or row >= HEIGHT // CELL:
                    raise MaskRefused("source-cell-not-visible")
                cells.append((column, row))
            accumulator = None
            continue
        if line.startswith("LD ") or line.startswith("LDH ") or line in ("XOR A", "DI"):
            accumulator = None
    if not cells:
        raise MaskRefused("source-text-cells-missing")
    if len(cells) != len(set(cells)):
        raise MaskRefused("source-cell-duplicate")
    return cells


def validate_mask(mask: bytes, cells: list[tuple[int, int]]) -> bytes:
    """Refuse candidate masks that differ from the independently source-derived cells."""
    if not isinstance(mask, bytes) or len(mask) != WIDTH * HEIGHT:
        raise MaskRefused("mask-size-invalid")
    if any(value not in (0, 1) for value in mask):
        raise MaskRefused("mask-encoding-invalid")
    expected = build_mask(cells)
    if mask != expected:
        raise MaskRefused("mask-source-cell-mismatch")
    masked = sum(mask)
    if masked > MAX_MASKED_PIXELS or WIDTH * HEIGHT - masked < MIN_UNMASKED_PIXELS:
        raise MaskRefused("mask-area-invalid")
    return expected


def compare_masked(frame: list[tuple[int, int, int]], reference: list[tuple[int, int, int]],
                   mask: bytes, cells: list[tuple[int, int]]) -> tuple[int, str]:
    if len(frame) != WIDTH * HEIGHT or len(reference) != WIDTH * HEIGHT:
        raise MaskRefused("image-size-invalid")
    for pixels in (frame, reference):
        if any(not isinstance(px, tuple) or len(px) != 3
               or any(isinstance(ch, bool) or not isinstance(ch, int) or not 0 <= ch <= 255 for ch in px)
               for px in pixels):
            raise MaskRefused("image-pixel-invalid")
    validate_mask(mask, cells)
    differing = sum(1 for index, (left, right) in enumerate(zip(frame, reference))
                    if not mask[index] and left != right)
    if differing:
        return 1, f"acid2 result=differs unmasked_pixels={differing}"
    return 0, f"acid2 result=match masked_pixels={sum(mask)}"


def overlay_png(frame: list[tuple[int, int, int]], mask: bytes) -> bytes:
    if len(frame) != WIDTH * HEIGHT or len(mask) != WIDTH * HEIGHT:
        raise MaskRefused("overlay-size-invalid")
    if any(value not in (0, 1) for value in mask):
        raise MaskRefused("overlay-mask-invalid")
    pixels = [(255, 0, 255) if mask[index] else px for index, px in enumerate(frame)]
    raw = b"".join(b"\x00" + bytes(channel for px in pixels[y * WIDTH:(y + 1) * WIDTH] for channel in px)
                    for y in range(HEIGHT))

    def chunk(tag: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class MaskContractTests(unittest.TestCase):
    def test_source_cell_marks_exact_pixels(self) -> None:
        mask = build_mask([(2, 3)])
        self.assertEqual(len(mask), WIDTH * HEIGHT)
        self.assertEqual(sum(mask), CELL * CELL)
        self.assertEqual(mask[3 * CELL * WIDTH + 2 * CELL], 1)
        self.assertEqual(mask[3 * CELL * WIDTH + 3 * CELL], 0)

    def test_mask_is_anchored_to_source_cell(self) -> None:
        source = b"LD A, 0x01\nLD (0x9862), A\n"
        cells = source_cells(source)
        self.assertEqual(cells, [(2, 3)])
        self.assertEqual(validate_mask(build_mask(cells), cells), build_mask([(2, 3)]))

    def test_broadened_mask_is_refused_even_with_new_digest(self) -> None:
        cells = [(2, 3)]
        broadened = bytearray(build_mask(cells))
        broadened[3 * CELL * WIDTH + 3 * CELL] = 1
        candidate = bytes(broadened)
        candidate_digest = digest(candidate)
        self.assertEqual(len(candidate_digest), 64)
        with self.assertRaisesRegex(MaskRefused, "mask-source-cell-mismatch"):
            validate_mask(candidate, cells)

    def test_only_unmasked_pixel_differences_fail(self) -> None:
        reference = [(255, 255, 255)] * (WIDTH * HEIGHT)
        cells = [(2, 3)]
        mask = build_mask(cells)
        changed_masked = list(reference)
        changed_masked[3 * CELL * WIDTH + 2 * CELL] = (0, 0, 0)
        self.assertEqual(compare_masked(changed_masked, reference, mask, cells)[0], 0)
        changed_unmasked = list(reference)
        changed_unmasked[0] = (0, 0, 0)
        self.assertEqual(compare_masked(changed_unmasked, reference, mask, cells),
                         (1, "acid2 result=differs unmasked_pixels=1"))

    def test_overlay_has_bounded_png_identity(self) -> None:
        frame = [(255, 255, 255)] * (WIDTH * HEIGHT)
        mask = build_mask([(2, 3)])
        overlay = overlay_png(frame, mask)
        self.assertTrue(overlay.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertLess(len(overlay), 1 << 20)
        self.assertEqual(len(digest(overlay)), 64)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--self-test-controls", action="store_true")
    args = parser.parse_args()
    if not args.self_test and not args.self_test_controls:
        parser.error("--self-test is required")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MaskContractTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
