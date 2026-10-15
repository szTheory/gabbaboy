#!/usr/bin/env python3
"""Bounded AGE mode-3 RGB555 source-image oracle (Phase 14, D-09/D-16)."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import subprocess
import sys
import unittest
import zlib
from dataclasses import dataclass


AGE_COMMIT = "1f5bc10e2cb60b86c19f8d0287ff78f410c4f639"
AGE_CASES = {
    f"m3-bg-{axis}-{variant}"
    for axis in ("lcdc", "scx")
    for variant in ("cgbBCE", "nocgb-ncmBCE", "ds-cgbBCE")
}
AGE_TEST_NAMES = {
    "cgb_age_m3_tracer",
    "cgb_age_m3_pixel_controls",
    "cgb_age_m3_membership",
    *(f"cgb_age_m3_{case.replace('-', '_')}" for case in AGE_CASES),
}
FRAME_WIDTH = 160
FRAME_HEIGHT = 144
PIXEL_COUNT = FRAME_WIDTH * FRAME_HEIGHT
FRAME_BYTES = PIXEL_COUNT * 2
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_PNG_BYTES = 1024 * 1024
MAX_PNG_CHUNKS = 16
MAX_RAW_BYTES = FRAME_HEIGHT * (1 + FRAME_WIDTH * 4)
COMPAT_PALETTE_BG = (0x639F, 0x4275, 0x254B, 0x0421)
# AGE's pinned test-setup.inc uses BGP=$E4 (identity shade ordering). Its
# compatibility references encode those four shades with this source palette.
COMPAT_REFERENCE_SHADES = {
    (255, 255, 255): 0,
    (123, 255, 49): 1,
    (0, 99, 198): 2,
    (0, 0, 0): 3,
}
NATIVE_REFERENCE_RGB555 = {
    (255, 255, 255): 0x7FFF,
    (173, 173, 173): 0x56B5,
    (82, 82, 82): 0x294A,
    (0, 0, 0): 0x0000,
}


class OracleError(Exception):
    """A bounded input or exact-identity failure with a stable diagnostic."""


@dataclass(frozen=True)
class PngImage:
    width: int
    height: int
    pixels: tuple[tuple[int, ...], ...]
    color_type: int


@dataclass(frozen=True)
class PixelComparison:
    mismatch_count: int
    mismatch_signature: str
    first_mismatches: tuple[tuple[int, int, int], ...]


def fail(detail: str) -> None:
    raise OracleError(detail)


def read_bounded(path: pathlib.Path, limit: int) -> bytes:
    try:
        with path.open("rb") as stream:
            data = stream.read(limit + 1)
    except OSError as exc:
        fail(f"input-read-failed {path.name}: {exc.strerror or type(exc).__name__}")
    if len(data) > limit:
        fail(f"input-too-large {path.name} limit={limit}")
    return data


def safe_repo_file(root: pathlib.Path, relative: str, label: str) -> pathlib.Path:
    candidate = pathlib.PurePosixPath(relative)
    if candidate.is_absolute() or not candidate.parts or ".." in candidate.parts:
        fail(f"{label}-path-outside-allow-list")
    path = root.joinpath(*candidate.parts)
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError):
        fail(f"{label}-path-outside-allow-list")
    if not resolved.is_file():
        fail(f"{label}-not-file {relative}")
    return resolved


def decode_png(data: bytes) -> PngImage:
    if len(data) > MAX_PNG_BYTES:
        fail("png-input-too-large")
    if len(data) < 57 or data[:8] != PNG_SIGNATURE:
        fail("png-signature-or-length")

    cursor = 8
    width = height = bit_depth = color_type = None
    idat_parts: list[bytes] = []
    idat_bytes = 0
    saw_ihdr = False
    saw_idat = False
    idat_closed = False
    saw_iend = False
    chunk_count = 0
    while cursor < len(data):
        chunk_count += 1
        if chunk_count > MAX_PNG_CHUNKS:
            fail("png-chunk-count-limit")
        if len(data) - cursor < 12:
            fail("png-truncated-chunk-header")
        length = struct.unpack_from(">I", data, cursor)[0]
        kind = data[cursor + 4:cursor + 8]
        cursor += 8
        if length > MAX_PNG_BYTES or length > len(data) - cursor - 4:
            fail("png-chunk-length-invalid")
        payload = data[cursor:cursor + length]
        crc = struct.unpack_from(">I", data, cursor + length)[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != crc:
            fail(f"png-crc-mismatch-{kind.decode('ascii', 'replace')}")
        cursor += length + 4

        if not saw_ihdr:
            if kind != b"IHDR" or length != 13:
                fail("png-ihdr-missing-or-misordered")
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
            if (width < 1 or width > FRAME_WIDTH or height < 1 or height > FRAME_HEIGHT or
                    bit_depth != 8 or color_type not in (2, 6) or compression != 0 or
                    filtering != 0 or interlace != 0):
                fail("png-format-unsupported-or-out-of-bounds")
            saw_ihdr = True
            continue

        if kind == b"IHDR":
            fail("png-duplicate-ihdr")
        if kind == b"IDAT":
            if idat_closed or saw_iend:
                fail("png-idat-misordered")
            saw_idat = True
            idat_bytes += length
            if idat_bytes > MAX_PNG_BYTES:
                fail("png-idat-size-limit")
            idat_parts.append(payload)
            continue
        if saw_idat:
            idat_closed = True
        if kind == b"IEND":
            if length != 0 or not saw_idat or saw_iend:
                fail("png-iend-invalid")
            saw_iend = True
            if cursor != len(data):
                fail("png-trailing-data")
            break
        # The six pinned inputs use truecolor RGB or opaque RGBA and no ancillary
        # or palette chunks. Rejecting unknown chunks keeps this decoder's input
        # grammar exact and makes alpha behavior explicit.
        fail(f"png-unknown-chunk-{kind.decode('ascii', 'replace')}")

    if not saw_ihdr or not saw_idat or not saw_iend or width is None or height is None:
        fail("png-required-chunk-missing")

    channels = 3 if color_type == 2 else 4
    stride = width * channels
    expected_raw = height * (stride + 1)
    if expected_raw > MAX_RAW_BYTES:
        fail("png-decompressed-size-limit")
    decoder = zlib.decompressobj()
    raw = bytearray()
    try:
        for packed in idat_parts:
            pending = packed
            while pending:
                allowance = expected_raw + 1 - len(raw)
                if allowance <= 0:
                    fail("png-decompressed-size-exceeded")
                before = len(pending)
                part = decoder.decompress(pending, allowance)
                raw.extend(part)
                if len(raw) > expected_raw:
                    fail("png-decompressed-size-exceeded")
                if decoder.unused_data:
                    fail("png-zlib-trailing-data")
                pending = decoder.unconsumed_tail
                if pending and len(pending) == before and not part:
                    fail("png-decompression-no-progress")
        allowance = expected_raw + 1 - len(raw)
        if allowance <= 0:
            fail("png-decompressed-size-exceeded")
        raw.extend(decoder.flush(allowance))
    except zlib.error as exc:
        fail(f"png-deflate-invalid {exc.__class__.__name__}")
    if len(raw) != expected_raw or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        fail("png-decompressed-size-or-stream-mismatch")

    rows: list[tuple[tuple[int, ...], ...]] = []
    previous = bytearray(stride)
    cursor = 0
    for _y in range(height):
        filter_type = raw[cursor]
        current = bytearray(raw[cursor + 1:cursor + 1 + stride])
        cursor += stride + 1
        if filter_type > 4:
            fail("png-filter-unsupported")
        for index in range(stride):
            left = current[index - channels] if index >= channels else 0
            above = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = above
            elif filter_type == 3:
                predictor = (left + above) // 2
            elif filter_type == 4:
                estimate = left + above - upper_left
                distance_left = abs(estimate - left)
                distance_above = abs(estimate - above)
                distance_upper_left = abs(estimate - upper_left)
                predictor = left if distance_left <= distance_above and distance_left <= distance_upper_left else (
                    above if distance_above <= distance_upper_left else upper_left
                )
            else:
                predictor = 0
            current[index] = (current[index] + predictor) & 0xFF
        row: list[tuple[int, ...]] = []
        for x in range(width):
            start = x * channels
            pixel = tuple(current[start:start + channels])
            if channels == 4 and pixel[3] != 255:
                fail("png-alpha-not-opaque")
            row.append(pixel)
        rows.append(tuple(row))
        previous = current
    return PngImage(width, height, tuple(pixel for row in rows for pixel in row), color_type)


def rgb8_to_rgb555(rgb: tuple[int, ...]) -> int:
    red, green, blue = rgb[:3]
    r = (red * 31 + 127) // 255
    g = (green * 31 + 127) // 255
    b = (blue * 31 + 127) // 255
    return r | (g << 5) | (b << 10)


def expected_frame(image: PngImage, mode: str) -> tuple[int, ...]:
    if image.width != FRAME_WIDTH or image.height != FRAME_HEIGHT:
        fail(f"reference-dimensions actual={image.width}x{image.height} expected=160x144")
    expected: list[int] = []
    if mode == "native-cgb":
        for pixel in image.pixels:
            rgb = pixel[:3]
            if rgb not in NATIVE_REFERENCE_RGB555:
                fail(f"native-reference-color-unsupported rgb={rgb}")
            expected.append(NATIVE_REFERENCE_RGB555[rgb])
        return tuple(expected)
    if mode != "dmg-compatibility":
        fail(f"mode-unsupported {mode}")
    for pixel in image.pixels:
        rgb = pixel[:3]
        shade = COMPAT_REFERENCE_SHADES.get(rgb)
        if shade is None:
            fail(f"compat-reference-color-unsupported rgb={rgb}")
        expected.append(COMPAT_PALETTE_BG[shade])
    return tuple(expected)


def compare_pixels(expected: tuple[int, ...], actual: tuple[int, ...], case_id: str) -> PixelComparison:
    if len(expected) != PIXEL_COUNT or len(actual) != PIXEL_COUNT:
        fail(f"frame-pixel-count expected={PIXEL_COUNT} actual={len(actual)}")
    mismatches = hashlib.sha256()
    first: list[tuple[int, int, int]] = []
    count = 0
    for index, (wanted, got) in enumerate(zip(expected, actual, strict=True)):
        if wanted > 0x7FFF or got > 0x7FFF:
            fail(f"rgb555-range index={index}")
        if wanted != got:
            mismatches.update(struct.pack("<IHH", index, wanted, got))
            if len(first) < 8:
                first.append((index, wanted, got))
            count += 1
    return PixelComparison(count, mismatches.hexdigest(), tuple(first))


def pixel_assertion_id(case_id: str, index: int) -> str:
    y, x = divmod(index, FRAME_WIDTH)
    return f"{case_id}/rgb555[y={y:03d},x={x:03d}]"


def fixture_map(manifest: dict) -> dict[str, dict]:
    if manifest.get("source", {}).get("commit") != AGE_COMMIT:
        fail("age-source-commit-mismatch")
    fixtures = manifest.get("fixtures")
    if not isinstance(fixtures, list):
        fail("age-fixtures-missing")
    image_entries = [entry for entry in fixtures if entry.get("fixture_class") == "age-m3-reference"]
    names = [entry.get("file", "").removesuffix(".gb") for entry in image_entries]
    if len(image_entries) != 6 or len(set(names)) != 6 or set(names) != AGE_CASES:
        fail("age-image-case-set")
    return dict(zip(names, image_entries, strict=True))


def age_disposition_map(record: dict) -> dict[str, dict]:
    suites = {suite.get("suite"): suite for suite in record.get("suites", [])}
    suite = suites.get("age")
    if record.get("schema") != "gabbaboy-external-dispositions-v1" or not isinstance(suite, dict):
        fail("ppu-dispositions-schema-or-age-suite")
    rows = suite.get("rows", [])
    names = [row.get("case") for row in rows]
    if len(rows) != 6 or len(set(names)) != 6 or set(names) != AGE_CASES:
        fail("ppu-age-case-set")
    return dict(zip(names, rows, strict=True))


def case_identity(entry: dict, case: str) -> str:
    return "/".join((
        f"age@{AGE_COMMIT}",
        f"{entry['source_path']}#{entry['source_sha256']}",
        f"{entry['file']}#{entry['sha256']}",
        entry["model"], entry["mode"], entry["speed"], case,
    ))


def validate_frame_metadata(metadata: dict, entry: dict, case: str, rom_sha256: str) -> None:
    expected_mode = "native-cgb" if entry.get("mode") == "native-cgb" else "dmg-compatibility"
    expected = {
        "schema": "gabbaboy-age-m3-frame-v1",
        "case": case,
        "model": "CGB-E",
        "mode": expected_mode,
        "speed": entry.get("speed"),
        "terminal": "frame-counter-vblank-5",
        "generation": 5,
        "width": FRAME_WIDTH,
        "height": FRAME_HEIGHT,
        "rom_sha256": rom_sha256,
    }
    for field, wanted in expected.items():
        if metadata.get(field) != wanted:
            fail(f"frame-metadata-mismatch {field} expected={wanted} actual={metadata.get(field)}")
    palette = metadata.get("compat_palette_bg")
    if palette != list(COMPAT_PALETTE_BG):
        fail("compat-palette-policy-mismatch")


def verify_case(root: pathlib.Path, case: str, harness: pathlib.Path,
                frame_path: pathlib.Path, reference_argument: pathlib.Path | None,
                manifest_path: pathlib.Path, dispositions_path: pathlib.Path,
                observe_pending: bool = False) -> int:
    try:
        manifest = json.loads(read_bounded(manifest_path, 256 * 1024))
        record = json.loads(read_bounded(dispositions_path, 256 * 1024))
        entry = fixture_map(manifest).get(case)
        if entry is None:
            fail(f"age-case-unknown {case}")
        disposition = age_disposition_map(record)[case]
        rom_path = safe_repo_file(root, f"fixtures/age/{entry['file']}", "rom")
        rom = read_bounded(rom_path, 32768)
        if len(rom) != 32768 or hashlib.sha256(rom).hexdigest() != entry.get("sha256"):
            fail(f"rom-digest-or-size-mismatch {entry['file']}")
        try:
            header = int(entry.get("header_143", ""), 16)
        except ValueError:
            fail(f"manifest-header-invalid {case}")
        if rom[0x143] != header:
            fail(f"rom-mode-header-mismatch {case}")
        reference_rel = f"fixtures/age/{entry['reference']['file']}"
        reference_path = safe_repo_file(root, reference_rel, "reference")
        if reference_argument is not None and reference_argument.resolve() != reference_path:
            fail(f"reference-case-mismatch {case}")
        reference = read_bounded(reference_path, MAX_PNG_BYTES)
        if len(reference) != entry["reference"].get("size_bytes") or hashlib.sha256(reference).hexdigest() != entry["reference"].get("sha256"):
            fail(f"reference-digest-or-size-mismatch {case}")
        if len(str(frame_path)) > 1024:
            fail("frame-output-path-too-long")
        frame_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [str(harness), "--case", case, "--rom", str(rom_path), "--frame", str(frame_path)],
            capture_output=True, text=True, timeout=15, check=False,
        )
        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            fail(f"guest-harness-failed case={case} exit={result.returncode}")
        frame = read_bounded(frame_path, FRAME_BYTES)
        if len(frame) != FRAME_BYTES:
            fail(f"frame-size-mismatch expected={FRAME_BYTES} actual={len(frame)}")
        metadata_path = pathlib.Path(str(frame_path) + ".json")
        metadata = json.loads(read_bounded(metadata_path, 16 * 1024))
        rom_sha256 = hashlib.sha256(rom).hexdigest()
        validate_frame_metadata(metadata, entry, case, rom_sha256)
        if hashlib.sha256(frame).hexdigest() != metadata.get("frame_sha256"):
            fail("frame-digest-mismatch")
        png = decode_png(reference)
        expected = expected_frame(png, entry["mode"])
        actual = tuple(struct.unpack_from("<H", frame, index * 2)[0] for index in range(PIXEL_COUNT))
        identity = case_identity(entry, case)
        comparison = compare_pixels(expected, actual, identity)
        observed = "pass" if comparison.mismatch_count == 0 else "fail"
        if observe_pending:
            if entry.get("qualification_status") != "admitted-not-executed":
                fail("observe-mode-requires-pending-image")
            print(f"age-m3 observed case={case} model=CGB-E mode={entry['mode']} speed={entry['speed']} result={observed} assertions={PIXEL_COUNT} mismatches={comparison.mismatch_count} signature={comparison.mismatch_signature}")
            for index, wanted, got in comparison.first_mismatches:
                print(f"pixel-mismatch assertion={pixel_assertion_id(identity, index)} expected={wanted:04x} actual={got:04x}")
            return 0

        if entry.get("qualification_status") != "executed":
            fail(f"age-image-not-executed {case}")
        if entry.get("execution_result") != observed or disposition.get("observed_result") != observed:
            fail(f"age-image-observed-result-mismatch {case} actual={observed}")
        if entry.get("disposition") != disposition.get("disposition"):
            fail(f"age-image-disposition-mismatch {case}")
        if entry.get("case_id") != identity or disposition.get("case_id") != identity:
            fail(f"age-image-case-identity-mismatch {case}")
        expected_signature = comparison.mismatch_signature
        for source, label in ((entry, "manifest"), (disposition, "disposition")):
            if (source.get("pixel_assertion_count") != PIXEL_COUNT or
                    source.get("pixel_mismatch_count") != comparison.mismatch_count or
                    source.get("pixel_mismatch_signature_sha256") != expected_signature):
                fail(f"age-image-signature-mismatch {label} {case}")
        if disposition.get("pinned_by") != f"cgb_age_m3_{case.replace('-', '_')}" or disposition.get("model") != "CGB-E" or disposition.get("mode") != entry["mode"] or disposition.get("speed") != entry["speed"]:
            fail(f"age-image-execution-identity-mismatch {case}")
        if observed == "pass":
            if disposition.get("disposition") != "pass" or comparison.mismatch_count != 0:
                fail(f"age-image-pass-contract-mismatch {case}")
        else:
            if disposition.get("disposition") != "expected-failure" or not str(disposition.get("reason", "")).startswith("expected-failure:"):
                fail(f"age-image-xfail-contract-mismatch {case}")
        protocol = "pass" if observed == disposition.get("disposition", "") else "xfail" if disposition.get("disposition") == "expected-failure" and observed == "fail" else "mismatch"
        print(f"age-m3 protocol={protocol} case={case} model=CGB-E mode={entry['mode']} speed={entry['speed']} observed={observed} disposition={disposition['disposition']} assertions={PIXEL_COUNT} mismatches={comparison.mismatch_count} signature={comparison.mismatch_signature}")
        for index, wanted, got in comparison.first_mismatches:
            print(f"pixel-mismatch assertion={pixel_assertion_id(identity, index)} expected={wanted:04x} actual={got:04x}")
        if observed == "fail" and disposition.get("disposition") != "expected-failure":
            fail(f"age-m3-unexpected-pixel-mismatch {case}")
        if observed == "pass" and disposition.get("disposition") == "expected-failure":
            fail(f"age-m3-unexpected-pass {case}")
        return 0
    except (OracleError, json.JSONDecodeError, KeyError, TypeError, ValueError, subprocess.TimeoutExpired) as exc:
        detail = str(exc) if isinstance(exc, OracleError) else f"input-invalid {type(exc).__name__}"
        print(f"age-m3 error: {detail}", file=sys.stderr)
        return 1


def membership_check(root: pathlib.Path, manifest_path: pathlib.Path,
                     dispositions_path: pathlib.Path, expected_tests_path: pathlib.Path) -> None:
    manifest = json.loads(read_bounded(manifest_path, 256 * 1024))
    record = json.loads(read_bounded(dispositions_path, 256 * 1024))
    fixtures = fixture_map(manifest)
    if set(fixtures) != AGE_CASES:
        fail("age-image-case-set")
    rows = age_disposition_map(record)
    if set(rows) != AGE_CASES:
        fail("ppu-age-case-set")
    expected_lines = read_bounded(expected_tests_path, 128 * 1024).decode("utf-8").splitlines()
    expected_names = {line.strip() for line in expected_lines if line.strip() and not line.lstrip().startswith("#")}
    missing = sorted(AGE_TEST_NAMES - expected_names)
    if missing:
        fail(f"age-image-ctest-membership-missing {','.join(missing)}")
    for case, entry in fixtures.items():
        row = rows[case]
        identity = case_identity(entry, case)
        if entry.get("expected_role") != "pass-target":
            fail(f"age-image-author-target-lost {case}")
        if entry.get("qualification_status") == "admitted-not-executed":
            if row.get("disposition") != "expected-unsupported":
                fail(f"age-image-pending-disposition-mismatch {case}")
            continue
        if entry.get("qualification_status") != "executed":
            fail(f"age-image-status-invalid {case}")
        if row.get("case_id") != identity or entry.get("case_id") != identity:
            fail(f"age-image-case-identity-mismatch {case}")
        if entry.get("execution_result") not in {"pass", "fail"} or row.get("observed_result") != entry.get("execution_result"):
            fail(f"age-image-observed-result-mismatch {case}")
        if entry.get("disposition") != row.get("disposition"):
            fail(f"age-image-disposition-mismatch {case}")
        if row.get("pinned_by") != f"cgb_age_m3_{case.replace('-', '_')}" or row.get("mode") != entry.get("mode") or row.get("speed") != entry.get("speed"):
            fail(f"age-image-execution-identity-mismatch {case}")


def run_membership(root: pathlib.Path, manifest_path: pathlib.Path,
                   dispositions_path: pathlib.Path, expected_tests_path: pathlib.Path) -> int:
    try:
        membership_check(root, manifest_path, dispositions_path, expected_tests_path)
    except (OracleError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        detail = str(exc) if isinstance(exc, OracleError) else f"input-invalid {type(exc).__name__}"
        print(f"age-m3-membership error: {detail}", file=sys.stderr)
        return 1
    executed = sum(1 for item in json.loads(read_bounded(manifest_path, 256 * 1024))["fixtures"]
                   if item.get("fixture_class") == "age-m3-reference" and item.get("qualification_status") == "executed")
    print(f"age-m3-membership pass cases=6 executed={executed} required_tests={len(AGE_TEST_NAMES)}")
    return 0


class TestPngDecoder(unittest.TestCase):
    def setUp(self) -> None:
        self.root = pathlib.Path(__file__).resolve().parents[2]
        manifest = json.loads((self.root / "fixtures/age/manifest.json").read_text(encoding="utf-8"))
        self.fixtures = fixture_map(manifest)

    def test_decode_all_source_pngs_has_bounded_160_by_144_frames(self) -> None:
        for case, entry in self.fixtures.items():
            with self.subTest(case=case):
                image = decode_png((self.root / "fixtures/age" / entry["reference"]["file"]).read_bytes())
                self.assertEqual((image.width, image.height), (FRAME_WIDTH, FRAME_HEIGHT))
                self.assertEqual(len(image.pixels), PIXEL_COUNT)
                expected_frame(image, entry["mode"])

    def test_crc_mutation_has_named_failure(self) -> None:
        path = self.root / "fixtures/age/references/m3-bg-lcdc-cgbBCE.png"
        mutated = bytearray(path.read_bytes())
        mutated[29] ^= 1
        with self.assertRaisesRegex(OracleError, "png-crc-mismatch-IHDR"):
            decode_png(bytes(mutated))

    def test_unknown_chunk_has_named_failure(self) -> None:
        path = self.root / "fixtures/age/references/m3-bg-lcdc-cgbBCE.png"
        data = path.read_bytes()
        chunk = struct.pack(">I", 1) + b"ABCD" + b"x"
        chunk += struct.pack(">I", zlib.crc32(b"ABCDx") & 0xFFFFFFFF)
        mutated = data[:-12] + chunk + data[-12:]
        with self.assertRaisesRegex(OracleError, "png-unknown-chunk-ABCD"):
            decode_png(mutated)

    def test_truncated_and_oversized_inputs_fail_before_decode(self) -> None:
        with self.assertRaisesRegex(OracleError, "png-signature-or-length"):
            decode_png(PNG_SIGNATURE)
        with self.assertRaisesRegex(OracleError, "png-input-too-large"):
            decode_png(b"x" * (MAX_PNG_BYTES + 1))


class TestExecutedDispositionContract(unittest.TestCase):
    def test_all_six_images_have_executed_exact_dispositions(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[2]
        manifest = json.loads((root / "fixtures/age/manifest.json").read_text(encoding="utf-8"))
        record = json.loads((root / "tests/external/cgb-ppu-dispositions.json").read_text(encoding="utf-8"))
        fixtures = fixture_map(manifest)
        rows = age_disposition_map(record)
        self.assertEqual(set(fixtures), AGE_CASES)
        self.assertEqual(set(rows), AGE_CASES)
        for case in sorted(AGE_CASES):
            with self.subTest(case=case):
                entry = fixtures[case]
                row = rows[case]
                identity = case_identity(entry, case)
                self.assertEqual(entry.get("qualification_status"), "executed",
                                 f"age-image-not-executed {case}")
                self.assertEqual(entry.get("case_id"), identity)
                self.assertEqual(row.get("case_id"), identity)
                self.assertEqual(entry.get("execution_result"), "fail")
                self.assertEqual(row.get("observed_result"), "fail")
                self.assertEqual(entry.get("disposition"), "expected-failure")
                self.assertEqual(row.get("disposition"), "expected-failure")
                self.assertEqual(entry.get("pixel_assertion_count"), PIXEL_COUNT)
                self.assertEqual(row.get("pixel_assertion_count"), PIXEL_COUNT)
                self.assertEqual(entry.get("pixel_mismatch_signature_sha256"),
                                 row.get("pixel_mismatch_signature_sha256"))
                self.assertRegex(entry.get("pixel_mismatch_signature_sha256", ""), r"^[0-9a-f]{64}$")


class TestPixelControls(unittest.TestCase):
    def setUp(self) -> None:
        self.root = pathlib.Path(__file__).resolve().parents[2]
        manifest = json.loads((self.root / "fixtures/age/manifest.json").read_text(encoding="utf-8"))
        self.fixtures = fixture_map(manifest)
        case = "m3-bg-lcdc-cgbBCE"
        entry = self.fixtures[case]
        image = decode_png((self.root / "fixtures/age" / entry["reference"]["file"]).read_bytes())
        self.expected = expected_frame(image, entry["mode"])
        self.identity = case_identity(entry, case)

    def test_pixel_bitflip_fails_exact_pixel_assertion(self) -> None:
        clean = compare_pixels(self.expected, self.expected, self.identity)
        self.assertEqual(clean.mismatch_count, 0)
        mutated = list(self.expected)
        mutated[723] ^= 1
        changed = compare_pixels(self.expected, tuple(mutated), self.identity)
        self.assertEqual(changed.mismatch_count, 1)
        self.assertEqual(changed.first_mismatches, ((723, self.expected[723], mutated[723]),))
        self.assertNotEqual(changed.mismatch_signature, clean.mismatch_signature)
        self.assertEqual(pixel_assertion_id(self.identity, 723), f"{self.identity}/rgb555[y=004,x=083]")

    def test_wrong_frame_fails_many_pixel_assertions(self) -> None:
        wrong = compare_pixels(self.expected, (0,) * PIXEL_COUNT, self.identity)
        self.assertGreater(wrong.mismatch_count, 0)
        self.assertEqual(len(wrong.mismatch_signature), 64)


def main() -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--membership", action="store_true")
    parser.add_argument("--observe-pending", action="store_true")
    parser.add_argument("--case")
    parser.add_argument("--harness", type=pathlib.Path)
    parser.add_argument("--frame", type=pathlib.Path)
    parser.add_argument("--reference", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path,
                        default=root / "fixtures/age/manifest.json")
    parser.add_argument("--dispositions", type=pathlib.Path,
                        default=root / "tests/external/cgb-ppu-dispositions.json")
    parser.add_argument("--expected-tests", type=pathlib.Path,
                        default=root / "tests/expected-tests.txt")
    args = parser.parse_args()
    if args.self_test:
        unittest.main(argv=[sys.argv[0]], verbosity=1)
        return 0
    if args.membership:
        return run_membership(root, args.manifest, args.dispositions, args.expected_tests)
    if not args.case or not args.harness or not args.frame:
        parser.error("--case, --harness, and --frame are required for pixel comparison")
    return verify_case(root, args.case, args.harness, args.frame, args.reference,
                       args.manifest, args.dispositions, args.observe_pending)


if __name__ == "__main__":
    raise SystemExit(main())
