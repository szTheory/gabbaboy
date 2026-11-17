#!/usr/bin/env python3
"""Source-cell mask generation and verification for bounded acid2 comparisons."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import pathlib
import re
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zlib

WIDTH = 160
HEIGHT = 144
CELL = 8
MAX_CELLS = 72
MAX_MASKED_PIXELS = 72 * CELL * CELL
MIN_UNMASKED_PIXELS = WIDTH * HEIGHT - MAX_MASKED_PIXELS
MAX_SOURCE_BYTES = 64 * 1024
MAX_BUNDLE_MEMBERS = 64
MAX_BUNDLE_BYTES = 512 * 1024
MAX_BUNDLE_MEMBER_BYTES = 256 * 1024
SOURCE_PINS = {
    "dmg": {
        "id": "dmg-acid2-v1.0",
        "commit": "dc2295408f881637ff69f784d8d93f3d2db30181",
        "tree": "a59741f15579a82205fff557dd000a5ebb6d7f6e",
        "source": "dmg-acid2.asm",
        "model": "dmg-cpu-b",
        "title": "DMG-ACID2",
    },
    "cgb": {
        "id": "cgb-acid2-v1.1",
        "commit": "fa5b7f86d6fb599f79e55169494d981a7af75a31",
        "tree": "a541bf54356809dc04cc050f8fc14d9620649f88",
        "source": "cgb-acid2.asm",
        "model": "cgb-cpu-e",
        "title": "CGB-ACID2",
    },
}
MGBLIB_COMMIT = "5d829bf2ffa1447dcfd63c5dab2c44488632617e"
RGBDS_COMMIT = "ede982b50a68a6253ffbab17dc4184710b08032f"
RIGHTS_DECISION_COMMIT = "169c062cd97764e2cea4052ce285209e8a886ff0"
RIGHTS_INPUT_COMMIT = "508f37f191ec76506d75921e97430148f4909209"
RIGHTS_INPUT_PATH = "tests/data/v04-closeout.json"
DMG_SHADES = (255, 170, 85, 0)


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


def rgb555_to_rgb888(value: int) -> tuple[int, int, int]:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0x7FFF:
        raise MaskRefused("rgb555-value-invalid")
    channels = (value & 0x1F, (value >> 5) & 0x1F, (value >> 10) & 0x1F)
    return tuple((channel << 3) | (channel >> 2) for channel in channels)


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


def _decode_source(source: bytes, what: str) -> str:
    if not isinstance(source, bytes) or not source or len(source) > MAX_SOURCE_BYTES:
        raise MaskRefused(f"{what}-size-invalid")
    try:
        return source.decode("ascii", errors="strict")
    except UnicodeDecodeError:
        raise MaskRefused(f"{what}-encoding-invalid") from None


def _source_lines(source: bytes, what: str) -> list[str]:
    return [line.split(";", 1)[0].strip() for line in _decode_source(source, what).splitlines()]


def acid2_source_cells(kind: str, main_source: bytes, oam_source: bytes,
                       background_source: bytes, reset_display_source: bytes) -> list[tuple[int, int]]:
    """Derive and enforce the fixed text-cell allowlist from the pinned Acid2 program.

    The OAM greeting, background exclamation mark, footer map writes, and raster scroll are
    read from source. A changed source position is refused against the accepted cell allowlist.
    """
    if kind not in SOURCE_PINS:
        raise MaskRefused("acid2-kind-invalid")
    main_lines = _source_lines(main_source, "acid2-main-source")
    oam_lines = _source_lines(oam_source, "acid2-oam-source")
    background_lines = _source_lines(background_source, "acid2-background-source")
    reset_lines = _source_lines(reset_display_source, "acid2-reset-source")

    def matching(lines: list[str], pattern: str) -> list[re.Match[str]]:
        rx = re.compile(pattern, re.IGNORECASE)
        return [match for line in lines if (match := rx.fullmatch(line))]

    # ResetDisplay initializes both scroll registers to zero before main selects SCY=$20.
    reset_text = "\n".join(reset_lines)
    if not re.search(r"XOR A\s+LD \[RSTAT\], A\s+LD \[RSCX\], A\s+LD \[RSCY\], A",
                     reset_text, re.IGNORECASE):
        raise MaskRefused("acid2-reset-scroll-source-mismatch")
    scy_values = [int(m.group(1), 16) for m in matching(
        main_lines, r"LD A, \$([0-9A-F]{2})")]
    if not any(value == 0x20 for value in scy_values):
        raise MaskRefused("acid2-scy-source-mismatch")
    if not re.search(r"LD A, \$20\s+LDH \[RSCY\], A", "\n".join(main_lines), re.IGNORECASE):
        raise MaskRefused("acid2-scy-write-missing")

    # The ten source-defined sprites encode "HelloWorld". The space and background ! are
    # included by the fixed span; the extra 11th white sprite overlaps the exclamation cell.
    try:
        oam_start = next(i for i, line in enumerate(oam_lines) if line.upper() == "OAMDATA::")
        oam_end = next(i for i in range(oam_start + 1, len(oam_lines))
                       if oam_lines[i].upper() == ".END:")
    except StopIteration:
        raise MaskRefused("acid2-oam-data-boundary-missing") from None
    oam_rows = [line for line in oam_lines[oam_start + 1:oam_end]
                if re.match(r"(?i)^DB\s", line)]
    sprite_rx = re.compile(
        r'(?i)DB\s+\$([0-9A-F]{2})\s*,\s*\$([0-9A-F]{2})\s*,\s*"([A-Za-z])"\s*,\s*(\$?[0-9A-F]{1,2})')
    sprites: list[tuple[str, int, int, int]] = []
    for line in oam_rows:
        match = sprite_rx.fullmatch(line)
        if match:
            attr_text = match.group(4)
            attr = int(attr_text[1:], 16) if attr_text.startswith("$") else int(attr_text, 10)
            sprites.append((match.group(3), int(match.group(1), 16),
                            int(match.group(2), 16), attr))
    greeting = [item for item in sprites if item[1] == 0x10 and item[0] in "HelloWorld"]
    expected_greeting = list(zip("HelloWorld", (0x28, 0x30, 0x38, 0x40, 0x48,
                                                  0x58, 0x60, 0x68, 0x70, 0x78), strict=True))
    if [(char, x) for char, _y, x, _attr in greeting] != expected_greeting:
        raise MaskRefused("acid2-oam-text-source-mismatch")
    expected_attr = 0 if kind == "dmg" else 3
    if any(y != 0x10 or attr != expected_attr for _char, y, _x, attr in greeting):
        raise MaskRefused("acid2-oam-text-flags-mismatch")
    extra_rx = re.compile(r"(?i)DB\s+\$10\s*,\s*\$80\s*,\s*1\s*,\s*(\$?[0-9A-F]{1,2})")
    extras = [line for line in oam_rows if extra_rx.fullmatch(line)]
    if len(extras) != 1:
        raise MaskRefused("acid2-eleventh-sprite-source-mismatch")
    extra_text = extra_rx.fullmatch(extras[0]).group(1)
    extra_attr = int(extra_text[1:], 16) if extra_text.startswith("$") else int(extra_text, 10)
    if extra_attr != (0x10 if kind == "dmg" else 4):
        raise MaskRefused("acid2-eleventh-sprite-flags-mismatch")

    bg_rows: list[list[str]] = []
    for line in background_lines:
        if not re.match(r"(?i)^DB\s", line):
            continue
        values = [value.strip() for value in line[2:].split(",")]
        bg_rows.append(values)
    bangs = [(column, row) for row, values in enumerate(bg_rows)
             for column, value in enumerate(values) if value == '"!"']
    if bangs != [(15, 0)]:
        raise MaskRefused("acid2-background-exclamation-source-mismatch")
    if not re.search(r"LD HL, BACKGROUNDMAP\s+LD DE, \$9880", "\n".join(main_lines), re.IGNORECASE):
        raise MaskRefused("acid2-background-placement-source-mismatch")
    hello_cells = {(column, 0) for column in range(4, 16)}

    # Source writes twenty footer tiles at $9e80 and twenty at $9ea0. LY_80 selects the
    # $9c00 background map, placing those rows at screen rows 16 and 17 after SCY=$20.
    if not re.search(r"LD HL, \$9E80.*?LD C, 20.*?LD L, \$A0.*?LD C, 20",
                     "\n".join(main_lines), re.IGNORECASE | re.DOTALL):
        raise MaskRefused("acid2-footer-map-source-mismatch")
    if not re.search(r"LY_80:\s+LD HL, R_LCDC\s+SET 3, \[HL\]",
                     "\n".join(main_lines), re.IGNORECASE):
        # Both pinned source files use the canonical hardware symbol spelling rLCDC.
        if not re.search(r"LY_80:\s+LD HL, RLCDC\s+SET 3, \[HL\]",
                         "\n".join(main_lines), re.IGNORECASE):
            raise MaskRefused("acid2-footer-map-selection-mismatch")
    if kind == "dmg":
        if not re.search(r"LY_82:\s+LD A, \$F3\s+LDH \[RSCX\], A", "\n".join(main_lines), re.IGNORECASE):
            raise MaskRefused("acid2-footer-scroll-source-mismatch")
        if not re.search(r"LY_90:.*?XOR A\s+LDH \[RSCX\], A",
                         "\n".join(main_lines), re.IGNORECASE | re.DOTALL):
            raise MaskRefused("acid2-footer-scroll-restore-missing")
        footer_scx = 0xF3
    else:
        if re.search(r"LDH \[RSCX\]", "\n".join(main_lines), re.IGNORECASE):
            raise MaskRefused("acid2-cgb-footer-scroll-mutated")
        footer_scx = 0
    footer_cells: set[tuple[int, int]] = set()
    footer_map_base = 0x9C00
    footer_start = 0x9E80
    start_offset = footer_start - footer_map_base
    first_row, first_column = divmod(start_offset, 32)
    for source_row in range(2):
        for source_column in range(20):
            for local_y in range(8):
                screen_y = (first_row + source_row) * 8 + local_y - 0x20
                if not 0 <= screen_y < HEIGHT:
                    continue
                for local_x in range(8):
                    screen_x = ((first_column + source_column) * 8 + local_x - footer_scx) % 256
                    if 0 <= screen_x < WIDTH:
                        footer_cells.add((screen_x // CELL, screen_y // CELL))
    cells = sorted(hello_cells | footer_cells, key=lambda cell: (cell[1], cell[0]))
    expected = ({(column, 0) for column in range(4, 16)}
                | ({(column, row) for row in (16, 17) for column in range(1, 20)}
                   if kind == "dmg" else
                   {(column, row) for row in (16, 17) for column in range(20)}))
    if set(cells) != expected:
        raise MaskRefused("acid2-source-cell-allowlist-mismatch")
    return cells


def validate_mask(mask: bytes, cells: list[tuple[int, int]]) -> bytes:
    """Refuse candidate masks that differ from the independently source-derived cells."""
    if not isinstance(mask, bytes) or len(mask) != WIDTH * HEIGHT:
        raise MaskRefused("mask-size-invalid")
    if any(value not in (0, 1) for value in mask):
        raise MaskRefused("mask-encoding-invalid")
    if sum(mask) == WIDTH * HEIGHT:
        raise MaskRefused("mask-no-unmasked-pixels")
    expected = build_mask(cells)
    if mask != expected:
        raise MaskRefused("mask-source-cell-mismatch")
    masked = sum(mask)
    if masked > MAX_MASKED_PIXELS or WIDTH * HEIGHT - masked < MIN_UNMASKED_PIXELS:
        raise MaskRefused("mask-area-invalid")
    return expected


def compare_masked(frame: list[tuple[int, int, int]], reference: list[tuple[int, int, int]],
                   mask: bytes, cells: list[tuple[int, int]]) -> tuple[int, str]:
    if (not isinstance(frame, list) or not isinstance(reference, list)
            or len(frame) != WIDTH * HEIGHT or len(reference) != WIDTH * HEIGHT):
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


def _synthetic_acid2_sources(kind: str) -> tuple[bytes, bytes, bytes, bytes]:
    attr, extra, scroll = ("0", "$10", "$f3") if kind == "dmg" else ("3", "4", None)
    sprite_rows = []
    for char, raw_x in zip("HelloWorld", (0x28, 0x30, 0x38, 0x40, 0x48,
                                          0x58, 0x60, 0x68, 0x70, 0x78), strict=True):
        sprite_rows.append(f'    db $10, ${raw_x:02x}, "{char}", {attr}')
    sprite_rows.append(f"    db $10, $80, 1, {extra}")
    main_rows = [
        "    ld hl, $9e80", "    xor a", "    ld c, 20", ".loop:",
        "    ld [hl+], a", "    inc a", "    dec c", "    jr nz, .loop",
        "    ld l, $a0", "    ld c, 20", ".loop2:", "    ld [hl+], a",
        "    inc a", "    dec c", "    jr nz, .loop2",
        "    ld hl, BackgroundMap", "    ld de, $9880", "    call MemCopy",
        "    ld a, $20", "    ldh [rSCY], a", "LY_80:", "    ld hl, rLCDC",
        "    set 3, [hl]", "LY_82:",
    ]
    if scroll is not None:
        main_rows.extend((f"    ld a, {scroll}", "    ldh [rSCX], a", "LY_90:",
                          "    xor a", "    ldh [rSCX], a"))
    else:
        main_rows.append("LY_90:")
    oam = "\n".join(("OAMData::", *sprite_rows, ".end:"))
    background = 'BackgroundMap::\n    db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "!", 0\n.end:'
    reset = "\n".join(("    xor a", "    ld [rSTAT], a", "    ld [rSCX], a", "    ld [rSCY], a"))
    return ("\n".join(main_rows).encode("ascii"), oam.encode("ascii"),
            background.encode("ascii"), reset.encode("ascii"))


def _json_no_duplicate_keys(data: bytes, label: str) -> dict:
    def reject_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise MaskRefused(f"{label}-duplicate-key")
            result[key] = value
        return result

    try:
        value = json.loads(data.decode("utf-8", "strict"), object_pairs_hook=reject_pairs,
                           parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()))
    except MaskRefused:
        raise
    except (UnicodeError, ValueError, TypeError):
        raise MaskRefused(f"{label}-invalid-json") from None
    if not isinstance(value, dict):
        raise MaskRefused(f"{label}-invalid-shape")
    return value


def _git_bytes(root: pathlib.Path, revision: str, relative: str,
               limit: int = MAX_BUNDLE_BYTES) -> bytes:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise MaskRefused("source-revision-invalid")
    if (not isinstance(relative, str) or "\\" in relative or relative.startswith("/")
            or any(part in ("", ".", "..") for part in relative.split("/"))):
        raise MaskRefused("source-path-invalid")
    try:
        proc = subprocess.run(["git", "show", f"{revision}:{relative}"], cwd=root,
                              capture_output=True, check=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        raise MaskRefused(f"immutable-source-unavailable:{relative}") from None
    if len(proc.stdout) > limit:
        raise MaskRefused(f"immutable-source-too-large:{relative}")
    return proc.stdout


def _rights_components(source: dict) -> dict[str, dict]:
    components = source.get("components")
    if not isinstance(components, list):
        raise MaskRefused("acid2-rights-component-list-invalid")
    result: dict[str, dict] = {}
    for component in components:
        if not isinstance(component, dict) or not isinstance(component.get("id"), str):
            raise MaskRefused("acid2-rights-component-invalid")
        if component["id"] in result:
            raise MaskRefused("acid2-rights-component-duplicate")
        result[component["id"]] = component
    return result


def validate_rights_input(root: pathlib.Path, manifest: dict) -> dict:
    expected_size = 39813
    expected_sha = "e44695dc2b5efebdbc01aed9179466d25ac8f5a55bc99a8ce94217b4adf262f9"
    rights_input = manifest.get("rights_input")
    expected_identity = {"commit": RIGHTS_INPUT_COMMIT, "path": RIGHTS_INPUT_PATH,
                         "size_bytes": expected_size, "sha256": expected_sha}
    if rights_input != expected_identity or manifest.get("rights_decision_commit") != RIGHTS_DECISION_COMMIT:
        raise MaskRefused("acid2-rights-input-identity-invalid")
    rights_raw = _git_bytes(root, RIGHTS_INPUT_COMMIT, RIGHTS_INPUT_PATH, 1 << 20)
    if len(rights_raw) != expected_size or digest(rights_raw) != expected_sha:
        raise MaskRefused("acid2-rights-input-digest-mismatch")
    record = _json_no_duplicate_keys(rights_raw, "acid2-rights-input")
    if record.get("schema") != "gabbaboy-v04-closeout-v1":
        raise MaskRefused("acid2-rights-input-schema-invalid")
    source_by_id = {item.get("id"): item for item in record.get("sources", [])
                    if isinstance(item, dict)}
    for kind in ("dmg", "cgb"):
        pin = SOURCE_PINS[kind]
        source = source_by_id.get(pin["id"])
        if (not isinstance(source, dict) or source.get("commit") != pin["commit"]
                or source.get("root_tree_sha1") != pin["tree"]):
            raise MaskRefused(f"acid2-rights-source-pin-mismatch:{kind}")
        components = _rights_components(source)
        for component_id in ("source-code", "mgblib-code", "footer-and-reference-images"):
            item = components.get(component_id)
            if not isinstance(item, dict) or item.get("outcome") != "supported":
                raise MaskRefused(f"acid2-rights-scope-unresolved:{kind}:{component_id}")
            scope = item.get("scope")
            if (not isinstance(scope, dict) or scope.get("repository") != "supported"
                    or scope.get("public_ci") != "supported"):
                raise MaskRefused(f"acid2-rights-scope-mismatch:{kind}:{component_id}")
        font = components.get("mgblib-font-data")
        if not isinstance(font, dict) or font.get("outcome") != "excluded-by-design":
            raise MaskRefused(f"acid2-font-scope-mutated:{kind}")
        images = components["footer-and-reference-images"]
        if "D-207" not in images.get("terms", ""):
            raise MaskRefused(f"acid2-image-rights-inference-unbound:{kind}")
    return record


def _safe_member_path(name: str) -> bool:
    if not isinstance(name, str) or not name or "\\" in name or name.startswith("/"):
        return False
    parts = name.split("/")
    return len(name) <= 160 and all(part not in ("", ".", "..") for part in parts)


def read_bundle(bundle_bytes: bytes, manifest: dict, *,
                expected_bundle_sha256: str, expected_bundle_size_bytes: int) -> dict[str, bytes]:
    if not isinstance(bundle_bytes, bytes) or len(bundle_bytes) > MAX_BUNDLE_BYTES:
        raise MaskRefused("acid2-bundle-size-invalid")
    if digest(bundle_bytes) != expected_bundle_sha256:
        raise MaskRefused("acid2-bundle-digest-mismatch")
    if len(bundle_bytes) != expected_bundle_size_bytes:
        raise MaskRefused("acid2-bundle-size-mismatch")
    rows = manifest.get("members")
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_BUNDLE_MEMBERS:
        raise MaskRefused("acid2-member-list-invalid")
    expected: dict[str, dict] = {}
    for row in rows:
        if (not isinstance(row, dict) or not _safe_member_path(row.get("path"))
                or isinstance(row.get("size_bytes"), bool)
                or not isinstance(row.get("size_bytes"), int)
                or not 0 <= row["size_bytes"] <= MAX_BUNDLE_MEMBER_BYTES
                or not re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256", "")))):
            raise MaskRefused("acid2-member-record-invalid")
        if row["path"] in expected:
            raise MaskRefused("acid2-member-duplicate")
        expected[row["path"]] = row
    if sum(row["size_bytes"] for row in rows) > MAX_BUNDLE_BYTES:
        raise MaskRefused("acid2-member-total-size-invalid")
    result: dict[str, bytes] = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(bundle_bytes), mode="r:") as archive:
            entries = archive.getmembers()
            names = [entry.name for entry in entries]
            expected_names = set(expected) | {"build-manifest.json"}
            if (len(entries) != len(expected_names) or names != sorted(names)
                    or set(names) != expected_names
                    or len(names) != len(set(names))):
                raise MaskRefused("acid2-archive-member-set-invalid")
            for entry in entries:
                if (not _safe_member_path(entry.name) or not entry.isfile()
                        or entry.size < 0 or entry.size > MAX_BUNDLE_MEMBER_BYTES):
                    raise MaskRefused("acid2-archive-member-type-invalid")
                if entry.uid != 0 or entry.gid != 0 or entry.mtime != 0 or entry.mode != 0o644:
                    raise MaskRefused("acid2-archive-member-metadata-invalid")
                if entry.name == "build-manifest.json":
                    if entry.size > 128 * 1024:
                        raise MaskRefused("acid2-inner-manifest-too-large")
                    stream = archive.extractfile(entry)
                    if stream is None:
                        raise MaskRefused("acid2-archive-member-unreadable")
                    data = stream.read(128 * 1024 + 1)
                    canonical = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
                    if len(data) != entry.size or data != canonical:
                        raise MaskRefused("acid2-inner-manifest-identity-mismatch")
                    result[entry.name] = data
                    continue
                row = expected.get(entry.name)
                if row is None or entry.size != row["size_bytes"]:
                    raise MaskRefused("acid2-archive-member-unlisted")
                stream = archive.extractfile(entry)
                if stream is None:
                    raise MaskRefused("acid2-archive-member-unreadable")
                data = stream.read(MAX_BUNDLE_MEMBER_BYTES + 1)
                if len(data) != entry.size or digest(data) != row["sha256"]:
                    raise MaskRefused("acid2-archive-member-digest-mismatch")
                result[entry.name] = data
    except MaskRefused:
        raise
    except (tarfile.TarError, OSError, EOFError):
        raise MaskRefused("acid2-archive-invalid") from None
    if "manifest.json" in result:
        raise MaskRefused("acid2-archive-self-manifest-refused")
    if any(name.endswith("/old_skool_outline_thick.asm") for name in result):
        raise MaskRefused("acid2-font-data-member-refused")
    logo = bytes.fromhex("ceed6666cc0d000b03730083000c000d0008111f8889000edccc6ee6ddddd999bbbb67636e0eecccdddc999fbbb9333e")
    if any(logo in data for data in result.values()):
        raise MaskRefused("acid2-nintendo-logo-bytes-refused")
    return result


def _git_text(root: pathlib.Path, *args: str) -> str:
    try:
        proc = subprocess.run(["git", *args], cwd=root, capture_output=True,
                              check=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        raise MaskRefused("acid2-git-object-unavailable") from None
    if len(proc.stdout) > 4096:
        raise MaskRefused("acid2-git-metadata-too-large")
    try:
        return proc.stdout.decode("ascii", "strict").strip()
    except UnicodeDecodeError:
        raise MaskRefused("acid2-git-metadata-invalid") from None


def _source_blob(commit: str, source_path: str, expected_data: bytes) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or not _safe_member_path(source_path):
        raise MaskRefused("acid2-source-object-identity-invalid")
    if not isinstance(expected_data, bytes) or len(expected_data) > MAX_BUNDLE_MEMBER_BYTES:
        raise MaskRefused("acid2-source-member-size-invalid")
    # Git blob identities are content-addressed and can be checked from the bounded member
    # bytes. Runtime does not need a checkout of each third-party repository or network access.
    header = f"blob {len(expected_data)}\0".encode("ascii")
    return hashlib.sha1(header + expected_data).hexdigest()


def _validate_source_objects(root: pathlib.Path, members: dict[str, bytes], manifest: dict) -> None:
    pins = manifest.get("source_pins")
    if not isinstance(pins, dict):
        raise MaskRefused("acid2-source-pins-invalid")
    expected_pins = {kind: {"commit": row["commit"], "root_tree_sha1": row["tree"],
                            "repository": f"https://github.com/mattcurrie/{kind}-acid2"}
                     for kind, row in SOURCE_PINS.items()}
    if pins != expected_pins or manifest.get("mgblib_commit") != MGBLIB_COMMIT:
        raise MaskRefused("acid2-source-pin-mutated")

    rows = manifest.get("source_object_map")
    if not isinstance(rows, list):
        raise MaskRefused("acid2-source-object-map-invalid")
    object_map = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("member_path") in object_map:
            raise MaskRefused("acid2-source-object-map-entry-invalid")
        object_map[row["member_path"]] = row
    for member_path, data in members.items():
        if not member_path.startswith("source/"):
            continue
        parts = member_path.split("/", 2)
        if len(parts) != 3:
            raise MaskRefused("acid2-source-member-path-invalid")
        component, upstream_path = parts[1], parts[2]
        if component in SOURCE_PINS and upstream_path.startswith("img/"):
            pin = SOURCE_PINS[component]
            entry = next((item for item in manifest["members"] if item["path"] == member_path), None)
            source_object = entry.get("source_object") if isinstance(entry, dict) else None
            if (not isinstance(source_object, dict)
                    or source_object.get("repository_commit") != pin["commit"]
                    or source_object.get("source_path") != upstream_path
                    or source_object.get("img_tree") != manifest["image_rights"][component]["img_tree"]):
                raise MaskRefused("acid2-image-source-object-unbound")
            if _source_blob(pin["commit"], upstream_path, data) != source_object.get("git_blob_sha1"):
                raise MaskRefused("acid2-image-source-blob-mismatch")
            continue
        expected_component = component if component in SOURCE_PINS else "mgblib" if component == "mgblib" else None
        if expected_component is None:
            raise MaskRefused("acid2-source-component-invalid")
        expected_commit = (SOURCE_PINS[component]["commit"]
                           if component in SOURCE_PINS else MGBLIB_COMMIT)
        row = object_map.get(member_path)
        if (not isinstance(row, dict) or row.get("repository_component") != expected_component
                or row.get("source_commit") != expected_commit
                or row.get("source_path") != upstream_path
                or row.get("size_bytes") != len(data) or row.get("sha256") != digest(data)):
            raise MaskRefused("acid2-source-object-map-mismatch")
        object_id = _source_blob(expected_commit, upstream_path, data)
        if row.get("git_blob_sha1") != object_id:
            raise MaskRefused("acid2-source-object-id-mismatch")
    expected_upstream = {path for path in members if path.startswith("source/")
                         and not any(path.startswith(f"source/{kind}/img/") for kind in SOURCE_PINS)}
    if set(object_map) != expected_upstream:
        raise MaskRefused("acid2-source-object-map-coverage-mismatch")


def _validate_glyph_source(glyph_source: bytes) -> None:
    text = _decode_source(glyph_source, "acid2-glyph-source")
    data_lines = [line.split(";", 1)[0].strip() for line in text.splitlines()
                  if re.match(r"(?i)^\s*DB\s", line.split(";", 1)[0])]
    if len(data_lines) != 128:
        raise MaskRefused("acid2-glyph-tile-count-invalid")
    for line in data_lines:
        values = [item.strip() for item in re.sub(r"(?i)^DB\s+", "", line).split(",")]
        if len(values) != 16 or any(not re.fullmatch(r"\$[0-9A-Fa-f]{2}", value) for value in values):
            raise MaskRefused("acid2-glyph-tile-data-invalid")


def validate_bundle_manifest(root: pathlib.Path, manifest: dict,
                             members: dict[str, bytes]) -> None:
    if manifest.get("schema") != "gabbaboy-acid2-manifest-v1":
        raise MaskRefused("acid2-manifest-schema-invalid")
    if manifest.get("status") != "admitted" or "admission_commit" in manifest:
        raise MaskRefused("acid2-manifest-admission-status-invalid")
    if manifest.get("font_data") != "excluded-by-design":
        raise MaskRefused("acid2-font-scope-mutated")
    if manifest.get("rights_decision_commit") != RIGHTS_DECISION_COMMIT:
        raise MaskRefused("acid2-rights-decision-unbound")
    rights = validate_rights_input(root, manifest)
    if manifest.get("source_revision") != RIGHTS_INPUT_COMMIT:
        raise MaskRefused("acid2-rights-source-revision-mismatch")
    if manifest.get("mgblib_commit") != MGBLIB_COMMIT:
        raise MaskRefused("acid2-mgblib-pin-mutated")
    if manifest.get("toolchain_source_commit") != RGBDS_COMMIT:
        raise MaskRefused("acid2-rgbds-pin-mutated")
    if manifest.get("nintendo_logo_bytes") != (
            "not-present; rgbfix -f hg fixes header/global checksums without inserting logo"):
        raise MaskRefused("acid2-logo-scope-mutated")
    expected_component_scope = {
        "cgb_source": "pinned root MIT; source code at exact commit only",
        "dmg_source": "pinned root MIT; source code at exact commit only",
        "footer_and_reference_images": "D-207 bounded inference for each exact pinned repository img tree; full root MIT notices and README credit retained",
        "logo": "not included; linker fill remains zero at header logo offsets; checksums only fixed",
        "mgblib_font": "excluded-by-design; no font data member or input",
        "mgblib_source": "pinned mgblib MIT; source code dependency closure only",
        "rgbds": "build-only; exact source commit, no RGBDS binary distributed",
    }
    if manifest.get("component_scope") != expected_component_scope:
        raise MaskRefused("acid2-component-scope-mutated")
    expected_model_scope = {
        "dmg": {"excluded_claims": ["glyph-accuracy", "mode-3-timing", "hardware-qualification"],
                "hardware_claim": False, "runner_model": "dmg-cpu-b"},
        "cgb": {"excluded_claims": ["glyph-accuracy", "mode-3-timing", "hardware-qualification"],
                "hardware_claim": False, "runner_model": "cgb-cpu-e"},
    }
    if manifest.get("model_scope") != expected_model_scope:
        raise MaskRefused("acid2-model-scope-mutated")
    expected_image_rights = {
        "dmg": {"img_tree": "9ebf5fb9c33685947e89f8e0170b77be1672a08a",
                "tree_sha256": "2b43b4daafc6a9c0f89dab7fcfc52549b6aed285b6f3f09eb57c716df7245ee7"},
        "cgb": {"img_tree": "65d8d4c0057ac716c632fb8ae28628b214c4a801",
                "tree_sha256": "262917f4a9a912e5fea7b8af8d9370f6c347337590e0b823fc153a1bb59e1e2e"},
    }
    if manifest.get("image_rights") != expected_image_rights:
        raise MaskRefused("acid2-image-rights-tree-mutated")
    image_members = {path for path in members if path.startswith("source/dmg/img/")
                     or path.startswith("source/cgb/img/")}
    if image_members != {
            "source/dmg/img/footer.png", "source/dmg/img/reference-dmg.png",
            "source/dmg/img/reference-cgb.png", "source/cgb/img/footer.png",
            "source/cgb/img/reference.png"}:
        raise MaskRefused("acid2-image-member-scope-mutated")
    _validate_source_objects(root, members, manifest)
    _validate_glyph_source(members.get("project/glyphs.asm", b""))

    for kind, pin in SOURCE_PINS.items():
        original_path = f"source/{kind}/src/{pin['source']}"
        derived_path = f"derived/{kind}/src/{pin['source']}"
        original = members.get(original_path)
        derived = members.get(derived_path)
        if not isinstance(original, bytes) or not isinstance(derived, bytes):
            raise MaskRefused(f"acid2-main-source-missing:{kind}")
        old_include = b'INCLUDE "mgblib/src/old_skool_outline_thick.asm"'
        new_include = b'INCLUDE "project/glyphs.asm"'
        if original.count(old_include) != 1 or derived != original.replace(old_include, new_include, 1):
            raise MaskRefused(f"acid2-source-patch-mismatch:{kind}")
        root_source = members.get(f"source/{kind}/LICENSE")
        notice = members.get(f"licenses/{kind}-MIT.txt")
        if root_source is None or notice != root_source:
            raise MaskRefused(f"acid2-license-notice-mismatch:{kind}")
        if not members.get(f"source/{kind}/img/footer.png"):
            raise MaskRefused(f"acid2-footer-image-missing:{kind}")
        font = _rights_components(next(item for item in rights["sources"] if item["id"] == pin["id"]))
        if font["mgblib-font-data"].get("outcome") != "excluded-by-design":
            raise MaskRefused(f"acid2-font-rights-not-excluded:{kind}")
    if members.get("licenses/mgblib-MIT.txt") != members.get("source/mgblib/LICENSE"):
        raise MaskRefused("acid2-mgblib-license-notice-mismatch")
    sources_text = members.get("SOURCES.md", b"").decode("utf-8", "strict")
    if ("Håkon Wium Lie and Ian Hickson" not in sources_text
            or "D-207" not in sources_text or "not an image-specific upstream statement" not in sources_text
            or "old_skool_outline_thick.asm` font bytes are absent" not in sources_text):
        raise MaskRefused("acid2-source-notice-or-credit-missing")

    reference_rows = manifest.get("references")
    expected_reference_paths = {
        "source/dmg/img/reference-dmg.png", "source/dmg/img/reference-cgb.png",
        "source/cgb/img/reference.png",
    }
    expected_overlay_paths = {"overlays/dmg/reference-dmg.png",
                              "overlays/dmg/reference-cgb.png",
                              "overlays/cgb/reference.png"}
    if not isinstance(reference_rows, list) or {row.get("path") for row in reference_rows
            if isinstance(row, dict)} != expected_reference_paths | expected_overlay_paths:
        raise MaskRefused("acid2-reference-set-invalid")
    for row in reference_rows:
        data = members.get(row["path"])
        if (data is None or row.get("sha256") != digest(data)
                or row.get("size_bytes") != len(data)):
            raise MaskRefused("acid2-reference-identity-mismatch")

    derivatives = manifest.get("derivatives")
    if not isinstance(derivatives, list) or len(derivatives) != 2:
        raise MaskRefused("acid2-derivative-set-invalid")
    expected_output = {"dmg": ("derivatives/dmg-acid2.gb", "dmg-cpu-b", "00"),
                       "cgb": ("derivatives/cgb-acid2.gbc", "cgb-cpu-e", "c0")}
    output_map = {row.get("kind"): row for row in derivatives if isinstance(row, dict)}
    if set(output_map) != set(expected_output):
        raise MaskRefused("acid2-derivative-kind-set-invalid")
    for kind, (path, model, cgb_flag) in expected_output.items():
        row = output_map[kind]
        data = members.get(path)
        if (data is None or row.get("path") != path or row.get("sha256") != digest(data)
                or row.get("size_bytes") != len(data) or row.get("header_checksum_valid") is not True
                or row.get("global_checksum_valid") is not True or row.get("header_logo_bytes_zero") is not True
                or row.get("cgb_flag") != f"0x{cgb_flag}"):
            raise MaskRefused(f"acid2-derivative-identity-invalid:{kind}")
        if data[0x104:0x134] != bytes(48):
            raise MaskRefused("acid2-nintendo-logo-bytes-refused")

    receipt_raw = members.get("receipts/build.json")
    if receipt_raw is None:
        raise MaskRefused("acid2-build-receipt-missing")
    receipt = _json_no_duplicate_keys(receipt_raw, "acid2-build-receipt")
    toolchain = manifest.get("toolchain")
    if (not isinstance(toolchain, dict) or toolchain.get("source_commit") != RGBDS_COMMIT
            or manifest.get("toolchain_source_commit") != RGBDS_COMMIT
            or not isinstance(toolchain.get("binaries"), dict)
            or set(toolchain["binaries"]) != {"rgbasm", "rgblink", "rgbfix", "rgbgfx"}):
        raise MaskRefused("acid2-toolchain-manifest-invalid")
    if (receipt.get("schema") != "gabbaboy-acid2-build-receipt-v1"
            or receipt.get("rgbds_source_commit") != RGBDS_COMMIT
            or receipt.get("mgblib_commit") != MGBLIB_COMMIT
            or receipt.get("rights_decision_commit") != RIGHTS_DECISION_COMMIT
            or receipt.get("rights_input") != manifest.get("rights_input")
            or receipt.get("source_revision_for_rights") != RIGHTS_INPUT_COMMIT
            or receipt.get("source_pins") != manifest.get("source_pins")
            or receipt.get("tools") != toolchain["binaries"]
            or receipt.get("upstream_build_scripts_executed") is not False
            or receipt.get("font_input_included") is not False
            or receipt.get("nintendo_logo_bytes_in_output") is not False):
        raise MaskRefused("acid2-build-receipt-scope-invalid")
    expected_recipe = [
        "rgbgfx -o img/footer.2bpp img/footer.png",
        "rgbasm -i mgblib/ -M build/<kind>.d -o build/<kind>.o src/<kind>-acid2.asm",
        "rgblink -n build/<rom>.sym -m build/<rom>.map -o build/<rom> build/<kind>.o",
        "rgbfix -f hg -t DMG-ACID2 -p 255 build/dmg-acid2.gb",
        "rgbfix -C -f hg -t CGB-ACID2 -p 255 build/cgb-acid2.gbc",
    ]
    if receipt.get("build_recipe") != expected_recipe:
        raise MaskRefused("acid2-build-recipe-writes-logo")
    receipt_rows = receipt.get("results")
    if not isinstance(receipt_rows, list) or {row.get("kind") for row in receipt_rows
                                               if isinstance(row, dict)} != set(SOURCE_PINS):
        raise MaskRefused("acid2-build-receipt-result-set-invalid")
    for row in receipt_rows:
        kind = row["kind"]
        derivative = next(item for item in derivatives if item["kind"] == kind)
        expected_cgb = "0x00" if kind == "dmg" else "0xc0"
        builds = row.get("build_sha256s")
        header = row.get("header")
        if (row.get("path") != derivative["path"]
                or row.get("sha256") != derivative["sha256"]
                or row.get("size_bytes") != derivative["size_bytes"]
                or row.get("clean_build_count") != 2
                or builds != [derivative["sha256"], derivative["sha256"]]
                or not isinstance(header, dict)
                or header.get("header_checksum_valid") is not True
                or header.get("global_checksum_valid") is not True
                or header.get("standard_nintendo_logo_present") is not False
                or header.get("bootless_runner_start") != "0x0100"
                or header.get("cgb_flag") != expected_cgb):
            raise MaskRefused(f"acid2-build-receipt-output-mismatch:{kind}")


def _extract_inner_manifest(bundle_bytes: bytes) -> bytes:
    if not isinstance(bundle_bytes, bytes) or len(bundle_bytes) > MAX_BUNDLE_BYTES:
        raise MaskRefused("acid2-bundle-size-invalid")
    try:
        with tarfile.open(fileobj=io.BytesIO(bundle_bytes), mode="r:") as archive:
            entries = archive.getmembers()
            names = [entry.name for entry in entries]
            if (not 1 <= len(entries) <= MAX_BUNDLE_MEMBERS + 1
                    or len(names) != len(set(names)) or names != sorted(names)):
                raise MaskRefused("acid2-archive-member-set-invalid")
            matches = [entry for entry in entries if entry.name == "build-manifest.json"]
            if len(matches) != 1:
                raise MaskRefused("acid2-inner-manifest-missing")
            entry = matches[0]
            if (not entry.isfile() or not _safe_member_path(entry.name)
                    or entry.size < 1 or entry.size > 128 * 1024
                    or entry.uid != 0 or entry.gid != 0 or entry.mtime != 0
                    or entry.mode != 0o644):
                raise MaskRefused("acid2-inner-manifest-metadata-invalid")
            stream = archive.extractfile(entry)
            if stream is None:
                raise MaskRefused("acid2-inner-manifest-unreadable")
            raw = stream.read(128 * 1024 + 1)
            if len(raw) != entry.size:
                raise MaskRefused("acid2-inner-manifest-size-invalid")
            return raw
    except MaskRefused:
        raise
    except (tarfile.TarError, OSError, EOFError):
        raise MaskRefused("acid2-archive-invalid") from None


def _bounded_tool(argv: list[str], cwd: pathlib.Path, timeout: float = 30.0) -> tuple[bytes, bytes]:
    try:
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise MaskRefused("acid2-rgbds-command-timeout") from None
    except OSError:
        raise MaskRefused("acid2-rgbds-tool-unavailable") from None
    if len(proc.stdout) > 65536 or len(proc.stderr) > 65536:
        raise MaskRefused("acid2-rgbds-output-limit")
    if proc.returncode != 0:
        raise MaskRefused("acid2-rgbds-command-failed")
    return proc.stdout, proc.stderr


def _build_acid2_once(members: dict[str, bytes], kind: str,
                      tool_bin: pathlib.Path, work: pathlib.Path) -> tuple[bytes, bytes]:
    pin = SOURCE_PINS[kind]
    for prefix in (f"source/{kind}/", "source/mgblib/"):
        for name, data in members.items():
            if name.startswith(prefix):
                rel = name[len(prefix):]
                if rel == "README.md" or rel.startswith("img/reference"):
                    continue
                target = work / rel if prefix == f"source/{kind}/" else work / "mgblib" / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    # The original upstream main is replaced only by the committed one-line font include patch.
    derived = members[f"derived/{kind}/src/{pin['source']}"]
    source_target = work / "src" / pin["source"]
    source_target.parent.mkdir(parents=True, exist_ok=True)
    source_target.write_bytes(derived)
    project_target = work / "project/glyphs.asm"
    project_target.parent.mkdir(parents=True, exist_ok=True)
    project_target.write_bytes(members["project/glyphs.asm"])
    (work / "img").mkdir(exist_ok=True)
    (work / "build").mkdir(exist_ok=True)
    (work / "img/footer.png").write_bytes(members[f"source/{kind}/img/footer.png"])
    _bounded_tool([str(tool_bin / "rgbgfx"), "-o", "img/footer.2bpp", "img/footer.png"], work)
    if digest((work / "img/footer.2bpp").read_bytes()) != digest(
            members[f"generated/{kind}/footer.2bpp"]):
        raise MaskRefused(f"acid2-footer-generation-mismatch:{kind}")
    obj = f"build/{kind}.o"
    _bounded_tool([str(tool_bin / "rgbasm"), "-i", "mgblib/", "-M",
                   f"build/{kind}.d", "-o", obj, f"src/{pin['source']}"], work)
    rom_name = "dmg-acid2.gb" if kind == "dmg" else "cgb-acid2.gbc"
    rom = f"build/{rom_name}"
    _bounded_tool([str(tool_bin / "rgblink"), "-n", f"build/{rom_name}.sym", "-m",
                   f"build/{rom_name}.map", "-o", rom, obj], work)
    if kind == "dmg":
        fix_args = ["-f", "hg", "-t", pin["title"], "-p", "255", rom]
    else:
        fix_args = ["-C", "-f", "hg", "-t", pin["title"], "-p", "255", rom]
    _bounded_tool([str(tool_bin / "rgbfix"), *fix_args], work)
    data = (work / rom).read_bytes()
    if len(data) != 32768 or data[0x104:0x134] != bytes(48):
        raise MaskRefused(f"acid2-rom-size-or-logo-invalid:{kind}")
    header_checksum = 0
    for value in data[0x134:0x14D]:
        header_checksum = (header_checksum - value - 1) & 0xFF
    global_checksum = (sum(data[:0x14E]) + sum(data[0x150:])) & 0xFFFF
    if (data[0x14D] != header_checksum
            or int.from_bytes(data[0x14E:0x150], "big") != global_checksum):
        raise MaskRefused(f"acid2-rom-checksum-invalid:{kind}")
    return data, (work / "img/footer.2bpp").read_bytes()


def reproduce_bundle(repo_root: pathlib.Path, source_revision: str,
                     fixture_manifest: pathlib.Path) -> dict:
    """Verify the committed source/rights snapshot and reproduce both no-logo derivatives."""
    root = repo_root.resolve(strict=True)
    manifest_path = fixture_manifest.resolve(strict=True)
    try:
        manifest_relative = manifest_path.relative_to(root).as_posix()
    except ValueError:
        raise MaskRefused("acid2-manifest-outside-repository") from None
    if manifest_relative != "fixtures/acid2/manifest.json":
        raise MaskRefused("acid2-generic-manifest-path-invalid")
    manifest_raw = _git_bytes(root, source_revision, manifest_relative, 128 * 1024)
    if manifest_path.read_bytes() != manifest_raw:
        raise MaskRefused("acid2-manifest-differs-from-source-revision")
    generic_manifest = _json_no_duplicate_keys(manifest_raw, "acid2-generic-manifest")
    if generic_manifest.get("schema_version") != 1 or generic_manifest.get("decision", {}).get("status") != "approved":
        raise MaskRefused("acid2-generic-manifest-not-approved")
    admission_checker_path = "tests/scripts/verify-fixture-admission.py"
    admission_checker = root / admission_checker_path
    if admission_checker.read_bytes() != _git_bytes(root, source_revision, admission_checker_path, 1 << 20):
        raise MaskRefused("acid2-admission-checker-differs-from-source-revision")
    try:
        admission_result = subprocess.run(
            [sys.executable, "-I", str(admission_checker), "--check-manifest",
             manifest_relative, "--repo-root", str(root)],
            cwd=root, capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        raise MaskRefused("acid2-generic-admission-snapshot-unavailable") from None
    if (len(admission_result.stdout) > 65536 or len(admission_result.stderr) > 65536
            or admission_result.returncode != 0):
        raise MaskRefused("acid2-generic-admission-snapshot-refused")
    archive_rows = [row for row in generic_manifest.get("files", [])
                    if isinstance(row, dict) and row.get("path") == "fixtures/acid2/derivatives.tar"]
    if len(archive_rows) != 1:
        raise MaskRefused("acid2-generic-archive-record-invalid")
    archive_row = archive_rows[0]
    bundle_path = "fixtures/acid2/derivatives.tar"
    bundle_raw = _git_bytes(root, source_revision, bundle_path, MAX_BUNDLE_BYTES)
    disk_bundle = root / pathlib.PurePosixPath(bundle_path)
    if disk_bundle.read_bytes() != bundle_raw:
        raise MaskRefused("acid2-bundle-differs-from-source-revision")
    if (archive_row.get("sha256") != digest(bundle_raw)
            or archive_row.get("size_bytes") != len(bundle_raw)):
        raise MaskRefused("acid2-generic-archive-identity-mismatch")
    manifest = _json_no_duplicate_keys(_extract_inner_manifest(bundle_raw), "acid2-inner-manifest")
    validate_rights_input(root, manifest)
    members = read_bundle(bundle_raw, manifest, expected_bundle_sha256=digest(bundle_raw),
                          expected_bundle_size_bytes=len(bundle_raw))
    validate_bundle_manifest(root, manifest, members)

    for kind in SOURCE_PINS:
        reset_path = "source/mgblib/src/display/ResetDisplay.asm"
        cells = acid2_source_cells(
            kind,
            members[f"derived/{kind}/src/{SOURCE_PINS[kind]['source']}"] ,
            members[f"source/{kind}/inc/oam.asm"],
            members[f"source/{kind}/inc/background.asm"],
            members[reset_path],
        )
        mask = build_mask(cells)
        validate_mask(members[f"masks/{kind}.bin"], cells)
        mask_record = _json_no_duplicate_keys(members[f"masks/{kind}.json"],
                                              f"acid2-{kind}-mask-record")
        if (mask_record.get("cells") != [list(cell) for cell in cells]
                or mask_record.get("cell_count") != len(cells)
                or mask_record.get("masked_pixels") != sum(mask)
                or mask_record.get("unmasked_pixels") != WIDTH * HEIGHT - sum(mask)
                or mask_record.get("mask_sha256") != digest(mask)):
            raise MaskRefused(f"acid2-mask-record-mismatch:{kind}")

    runner_script = pathlib.Path(__file__).resolve().with_name("run-acid2-local.py")
    spec = importlib.util.spec_from_file_location("acid2_reproduce_png_decoder", runner_script)
    if spec is None or spec.loader is None:
        raise MaskRefused("acid2-reference-decoder-unavailable")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    for kind, ref_names in (("dmg", ("reference-dmg.png", "reference-cgb.png")),
                             ("cgb", ("reference.png",))):
        mask = members[f"masks/{kind}.bin"]
        for ref_name in ref_names:
            reference = runner.decode_png(members[f"source/{kind}/img/{ref_name}"])
            overlay = overlay_png(reference, mask)
            if overlay != members[f"overlays/{kind}/{ref_name}"]:
                raise MaskRefused(f"acid2-overlay-reproduction-mismatch:{kind}:{ref_name}")

    tool_bin = root / "build/phase24/toolchain/rgbds-0.4.2/bin"
    tool_meta = manifest["toolchain"]["binaries"]
    for tool in ("rgbasm", "rgblink", "rgbfix", "rgbgfx"):
        path = tool_bin / tool
        try:
            raw = path.read_bytes()
            info = path.lstat()
        except OSError:
            raise MaskRefused("acid2-pinned-rgbds-binary-missing") from None
        if stat.S_ISLNK(info.st_mode) or digest(raw) != tool_meta[tool]["sha256"]:
            raise MaskRefused(f"acid2-pinned-rgbds-binary-mismatch:{tool}")
        version, _ = _bounded_tool([str(path), "--version"], root, timeout=10)
        if version.decode("ascii", "replace").strip() != tool_meta[tool]["version_output"]:
            raise MaskRefused(f"acid2-pinned-rgbds-version-mismatch:{tool}")

    results = []
    with tempfile.TemporaryDirectory(prefix="gbb-acid2-reproduce-") as temp_name:
        temp = pathlib.Path(temp_name)
        for kind in SOURCE_PINS:
            outputs = []
            for pass_number in (1, 2):
                work = temp / f"{kind}-pass-{pass_number}"
                work.mkdir()
                output, _footer = _build_acid2_once(members, kind, tool_bin, work)
                outputs.append(output)
            if outputs[0] != outputs[1]:
                raise MaskRefused(f"acid2-clean-builds-disagree:{kind}")
            expected_path = next(row["path"] for row in manifest["derivatives"]
                                 if row["kind"] == kind)
            expected_rom = members[expected_path]
            if outputs[0] != expected_rom:
                raise MaskRefused(f"acid2-reproduced-output-mismatch:{kind}")
            results.append({"kind": kind, "sha256": digest(outputs[0]),
                            "size_bytes": len(outputs[0]), "clean_builds": 2,
                            "model": SOURCE_PINS[kind]["model"]})
    return {"status": "reproduced-not-run", "source_revision": source_revision,
            "rights_input": manifest["rights_input"], "bundle_sha256": digest(bundle_raw),
            "results": results}


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

    def test_colour_conversions_use_documented_exact_vectors(self) -> None:
        vectors = {
            0x0000: (0, 0, 0),
            0x001F: (255, 0, 0),
            0x03E0: (0, 255, 0),
            0x7C00: (0, 0, 255),
            0x4210: (132, 132, 132),
            0x7FFF: (255, 255, 255),
        }
        for encoded, expanded in vectors.items():
            with self.subTest(rgb555=encoded):
                self.assertEqual(rgb555_to_rgb888(encoded), expanded)
        self.assertEqual(DMG_SHADES, (255, 170, 85, 0))

    def test_pinned_acid2_source_cells_match_the_fixed_allowlist(self) -> None:
        expected_counts = {"dmg": 50, "cgb": 52}
        for kind, count in expected_counts.items():
            with self.subTest(kind=kind):
                main, oam, background, reset = _synthetic_acid2_sources(kind)
                cells = acid2_source_cells(kind, main, oam, background, reset)
                self.assertEqual(len(cells), count)
                self.assertEqual(sum(build_mask(cells)), count * CELL * CELL)

    def test_acid2_source_scroll_and_oam_mutations_cannot_expand_allowlist(self) -> None:
        main, oam, background, reset = _synthetic_acid2_sources("dmg")
        with self.assertRaisesRegex(MaskRefused, "acid2-footer-scroll-source-mismatch"):
            acid2_source_cells("dmg", main.replace(b"$f3", b"$f2"), oam, background, reset)
        with self.assertRaisesRegex(MaskRefused, "acid2-oam-text-source-mismatch"):
            acid2_source_cells("dmg", main, oam.replace(b"$28", b"$20", 1), background, reset)


class MaskControlTests(unittest.TestCase):
    def test_rights_input_and_decision_are_exact_source_bound_gates(self) -> None:
        manifest = {
            "rights_input": {"commit": RIGHTS_INPUT_COMMIT, "path": RIGHTS_INPUT_PATH,
                             "size_bytes": 39813,
                             "sha256": "e44695dc2b5efebdbc01aed9179466d25ac8f5a55bc99a8ce94217b4adf262f9"},
            "rights_decision_commit": RIGHTS_DECISION_COMMIT,
        }
        manifest["rights_input"]["commit"] = "0" * 40
        with self.assertRaisesRegex(MaskRefused, "acid2-rights-input-identity-invalid"):
            validate_rights_input(pathlib.Path("."), manifest)

    def test_bundle_member_path_traversal_is_refused_before_archive_read(self) -> None:
        payload = b"x"
        manifest = {"bundle_sha256": digest(b""), "bundle_size_bytes": 0,
                    "members": [{"path": "../escape", "size_bytes": 1,
                                 "sha256": digest(payload)}]}
        with self.assertRaisesRegex(MaskRefused, "acid2-member-record-invalid"):
            read_bundle(b"", manifest, expected_bundle_sha256=digest(b""),
                        expected_bundle_size_bytes=0)

    def test_admitted_runner_helper_reports_exact_masked_comparison_scope(self) -> None:
        runner_script = pathlib.Path(__file__).with_name("run-acid2-local.py")
        spec = importlib.util.spec_from_file_location("acid2_admitted_runner_control", runner_script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        local = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(local)

        main, oam, background, reset = _synthetic_acid2_sources("dmg")
        cells = acid2_source_cells("dmg", main, oam, background, reset)
        mask = build_mask(cells)
        reference_pixels = [(255, 255, 255)] * (WIDTH * HEIGHT)
        reference_png = local.encode_png_rgb(reference_pixels)
        rom = bytes(32768)
        rom_sha = digest(rom)
        members = {
            "derived/dmg/src/dmg-acid2.asm": main,
            "source/dmg/inc/oam.asm": oam,
            "source/dmg/inc/background.asm": background,
            "source/mgblib/src/display/ResetDisplay.asm": reset,
            "source/dmg/img/reference-dmg.png": reference_png,
            "masks/dmg.bin": mask,
        }
        manifest = {
            "derivatives": [{"kind": "dmg", "path": "derivatives/dmg-acid2.gb",
                             "sha256": rom_sha, "size_bytes": len(rom)}],
            "model_scope": {"dmg": {"runner_model": "dmg-cpu-b", "hardware_claim": False}},
        }
        members["derivatives/dmg-acid2.gb"] = rom
        good_frame = local.PPM_HEADER + bytes(channel for px in reference_pixels for channel in px)
        original_run = local.run_core
        try:
            with tempfile.TemporaryDirectory(prefix="acid2-runner-control-") as temp_name:
                fake_runner = pathlib.Path(temp_name) / "runner"
                fake_runner.write_bytes(b"synthetic runner control")
                local.run_core = lambda *_args, **_kwargs: good_frame
                result = local.run_admitted_comparison(members, manifest, fake_runner, "dmg", 2)
                self.assertEqual(result["verdict"], "pass")
                self.assertEqual(result["mask"]["masked_pixels"], 50 * CELL * CELL)
                self.assertEqual(result["mask"]["compared_pixels"], WIDTH * HEIGHT - 50 * CELL * CELL)
                self.assertEqual(result["runner_sha256"], digest(b"synthetic runner control"))

                changed = list(reference_pixels)
                changed[0] = (0, 0, 0)
                bad_frame = local.PPM_HEADER + bytes(channel for px in changed for channel in px)
                local.run_core = lambda *_args, **_kwargs: bad_frame
                result = local.run_admitted_comparison(members, manifest, fake_runner, "dmg", 2)
                self.assertEqual(result["verdict"], "mismatch")
                self.assertEqual(result["differing_unmasked_pixels"], 1)
        finally:
            local.run_core = original_run

    def test_broadened_mask_is_refused_even_with_new_digest(self) -> None:
        cells = [(2, 3)]
        broadened = bytearray(build_mask(cells))
        broadened[3 * CELL * WIDTH + 3 * CELL] = 1
        candidate = bytes(broadened)
        candidate_digest = digest(candidate)
        self.assertNotEqual(candidate_digest, digest(build_mask(cells)))
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

    def test_invalid_cells_masks_and_images_refuse_with_specific_reason(self) -> None:
        for cells, reason in (([], "mask-cell-count-invalid"),
                              ([(2, 3), (2, 3)], "source-cell-duplicate"),
                              ([(20, 3)], "mask-cell-out-of-range")):
            with self.subTest(cells=cells), self.assertRaisesRegex(MaskRefused, reason):
                source = b"LD A, 0x01\nLD (0x9862), A\n"
                if reason == "source-cell-duplicate":
                    source = b"LD A, 0x01\nLD (0x9862), A\nLD A, 0x01\nLD (0x9862), A\n"
                    source_cells(source)
                else:
                    build_mask(cells)
        cells = [(2, 3)]
        for mask, reason in ((b"\x00", "mask-size-invalid"),
                             (bytes([2]) * (WIDTH * HEIGHT), "mask-encoding-invalid"),
                             (bytes([1]) * (WIDTH * HEIGHT), "mask-no-unmasked-pixels")):
            with self.subTest(mask_reason=reason), self.assertRaisesRegex(MaskRefused, reason):
                validate_mask(mask, cells)
        good_mask = build_mask(cells)
        reference = [(255, 255, 255)] * (WIDTH * HEIGHT)
        for image in (None, [], reference + [(0, 0, 0)]):
            with self.subTest(image_size=None if image is None else len(image)), \
                    self.assertRaisesRegex(MaskRefused, "image-size-invalid"):
                compare_masked(image, reference, good_mask, cells)
        with self.assertRaisesRegex(MaskRefused, "rgb555-value-invalid"):
            rgb555_to_rgb888(True)

    def test_acid2_truncated_and_oversized_image_bytes_refuse(self) -> None:
        script = pathlib.Path(__file__).with_name("run-acid2-local.py")
        spec = importlib.util.spec_from_file_location("phase22_acid2_local_controls", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        acid2 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(acid2)
        expected = [(0, 0, 0)] * (WIDTH * HEIGHT)
        ppm = acid2.PPM_HEADER + bytes(3 * WIDTH * HEIGHT)
        for candidate in (b"", ppm[:-1], ppm + b"\x00"):
            with self.subTest(ppm_size=len(candidate)), self.assertRaisesRegex(ValueError, "unexpected ppm layout"):
                acid2.read_ppm(candidate)
        encoded = acid2.encode_png_rgb(expected)
        with self.assertRaisesRegex(ValueError, "no IEND"):
            acid2.decode_png(encoded[:-1])
        too_large_chunk = acid2.PNG_SIG + struct.pack(">I4s", acid2.MAX_IDAT + 1, b"IDAT") + bytes(4)
        with self.assertRaisesRegex(ValueError, "bad chunk length"):
            acid2.decode_png(too_large_chunk)

    def test_fully_masked_comparison_is_refused(self) -> None:
        image = [(255, 255, 255)] * (WIDTH * HEIGHT)
        full_mask = bytes([1]) * (WIDTH * HEIGHT)
        with self.assertRaisesRegex(MaskRefused, "mask-no-unmasked-pixels"):
            compare_masked(image, image, full_mask, [(2, 3)])

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
    parser.add_argument("--reproduce", action="store_true")
    parser.add_argument("--repo-root", type=pathlib.Path)
    parser.add_argument("--source-revision")
    parser.add_argument("--fixture-manifest", type=pathlib.Path)
    args = parser.parse_args()
    if args.reproduce:
        if not (args.repo_root and args.source_revision and args.fixture_manifest):
            parser.error("--reproduce requires --repo-root, --source-revision, and --fixture-manifest")
        try:
            result = reproduce_bundle(args.repo_root, args.source_revision, args.fixture_manifest)
        except (MaskRefused, OSError, ValueError) as exc:
            print(json.dumps({"status": "refused", "reason": str(exc)},
                             sort_keys=True, separators=(",", ":")))
            return 2
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    if not args.self_test and not args.self_test_controls:
        parser.error("--self-test, --self-test-controls, or --reproduce is required")
    suite_class = MaskContractTests if args.self_test else MaskControlTests
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(suite_class)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
