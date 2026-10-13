#!/usr/bin/env python3
"""Optional local acid2 comparison (D-24, rights gate G1). Standard library only; run `python3 -I`.

Never run by required CI except through --self-test, which uses synthetic data only. A ROM or
reference PNG whose SHA-256 is not pinned in tests/acid2/manifest.json is refused before it is
run or decoded (T-11-19), and the PNG decoder accepts one bounded 160x144 layout (T-11-20).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import subprocess
import sys
import tempfile
import zlib

W, H = 160, 144
HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_MANIFEST = HERE.parent / "acid2" / "manifest.json"
PNG_SIG = b"\x89PNG\r\n\x1a\n"
MAX_IDAT = 1 << 20
PPM_HEADER = b"P6\n160 144\n255\n"


class Refused(Exception):
    pass


def read_pinned(path: pathlib.Path, pin: str, what: str, limit: int = 1 << 20) -> bytes:
    """Read the file once, hash those bytes, and return them: the bytes that were checked are the
    bytes that get used, so a file swapped after the check cannot bypass the pin."""
    try:
        with path.open("rb") as handle:
            data = handle.read(limit + 1)
    except OSError as exc:
        raise Refused(f"unreadable input ({exc.__class__.__name__})")
    if len(data) > limit:
        raise Refused("file too large")
    if hashlib.sha256(data).hexdigest() != pin:
        raise Refused(f"{what} sha256 not pinned")
    return data


def check_pins(kind: dict, rom: pathlib.Path,
               reference: pathlib.Path | None) -> tuple[bytes, bytes | None]:
    rom_bytes = read_pinned(rom, kind["rom_sha256"], "rom")
    ref_bytes = None
    if reference is not None:
        ref_bytes = read_pinned(reference, kind["reference_sha256"], "reference")
    return rom_bytes, ref_bytes


# ---- minimal PNG codec: 160x144, non-interlaced, bit depth 8 (RGB, RGBA, grey+alpha, palette)
# and depth 1/2/4/8 for greyscale and palette. Alpha is ignored. ----

def _chunks(data: bytes):
    if data[:8] != PNG_SIG:
        raise ValueError("not a png")
    pos = 8
    while pos + 12 <= len(data):
        length, tag = struct.unpack(">I4s", data[pos:pos + 8])
        if length > MAX_IDAT or pos + 12 + length > len(data):
            raise ValueError("bad chunk length")
        body = data[pos + 8:pos + 8 + length]
        (crc,) = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])
        if zlib.crc32(tag + body) != crc:
            raise ValueError("bad chunk crc")
        yield tag, body
        pos += 12 + length
        if tag == b"IEND":
            return
    raise ValueError("no IEND")


def decode_png(data: bytes) -> list[tuple[int, int, int]]:
    ihdr = None
    plte = b""
    idat = bytearray()
    for tag, body in _chunks(data):
        if tag == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif tag == b"PLTE":
            plte = body
        elif tag == b"IDAT":
            idat += body
    if ihdr is None:
        raise ValueError("no IHDR")
    width, height, depth, ctype, comp, filt, interlace = ihdr
    if (width, height) != (W, H) or comp or filt or interlace:
        raise ValueError("unsupported png layout")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype)
    if channels is None or depth not in ((1, 2, 4, 8) if ctype in (0, 3) else (8,)):
        raise ValueError("unsupported png colour type or depth")
    bits = channels * depth
    stride = (W * bits + 7) // 8
    bpp = max(1, bits // 8)
    expect = (stride + 1) * H
    inflater = zlib.decompressobj()
    raw = inflater.decompress(bytes(idat), expect + 1)
    if len(raw) != expect or inflater.unconsumed_tail:
        raise ValueError("bad image data size")
    rows, prev = [], bytearray(stride)
    for y in range(H):
        ftype = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ftype == 0:
                add = 0
            elif ftype == 1:
                add = a
            elif ftype == 2:
                add = b
            elif ftype == 3:
                add = (a + b) >> 1
            elif ftype == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                add = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
            else:
                raise ValueError("bad filter type")
            line[i] = (line[i] + add) & 0xFF
        rows.append(line)
        prev = line
    pixels = []
    for line in rows:
        for x in range(W):
            if ctype in (0, 3):
                bit = x * depth
                v = (line[bit >> 3] >> (8 - depth - (bit & 7))) & ((1 << depth) - 1)
                if ctype == 0:
                    g = v * 255 // ((1 << depth) - 1)
                    pixels.append((g, g, g))
                else:
                    if v * 3 + 3 > len(plte):
                        raise ValueError("palette index out of range")
                    pixels.append(tuple(plte[v * 3:v * 3 + 3]))
            elif ctype == 2 or ctype == 6:
                pixels.append(tuple(line[x * channels:x * channels + 3]))
            else:
                g = line[x * 2]
                pixels.append((g, g, g))
    return pixels


def encode_png_rgb(pixels: list[tuple[int, int, int]]) -> bytes:
    raw = b"".join(b"\x00" + bytes(c for px in pixels[y * W:(y + 1) * W] for c in px) for y in range(H))

    def chunk(tag: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body))

    return (PNG_SIG + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def read_ppm(data: bytes) -> list[tuple[int, int, int]]:
    if not data.startswith(PPM_HEADER) or len(data) != len(PPM_HEADER) + W * H * 3:
        raise ValueError("unexpected ppm layout")
    body = data[len(PPM_HEADER):]
    return [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]


def compare(frame, reference) -> tuple[int, str]:
    differing = sum(1 for a, b in zip(frame, reference) if a != b)
    if differing == 0:
        return 0, "acid2 result=match"
    return 1, f"acid2 result=differs pixels={differing}"


def run_core(runner: pathlib.Path, kind: dict, rom: bytes, budget: int) -> bytes:
    """Run the pinned ROM to its ld b,b and return the newest frame PPM from the failure dir."""
    with tempfile.TemporaryDirectory(prefix="gbb-acid2-") as tmp:
        work = pathlib.Path(tmp)
        (work / "acid2.rom").write_bytes(rom)
        (work / "out").mkdir()
        line = (f"id=acid2 rom=acid2.rom rom_sha256={kind['rom_sha256']} rom_size={kind['rom_size']} "
                f"oracle=frame-digest@ldbb reference_digest={'0' * 64} "
                f"model_pass={kind['runner_model']} budget_half_dots={budget}\n")
        (work / "cases.txt").write_text(line)
        proc = subprocess.run([str(runner), "--acceptance", "cases.txt", "--case", "acid2",
                               "--model", kind["runner_model"], "--failure-dir", "out"],
                              cwd=work, capture_output=True, timeout=300)
        ppm = work / "out" / "acid2.ppm"
        if not ppm.is_file():
            detail = proc.stdout.decode("utf-8", "replace").strip().splitlines()[-1:] or ["no output"]
            raise RuntimeError(f"runner produced no frame (exit {proc.returncode}): {detail[0][:160]}")
        return ppm.read_bytes()


def self_test() -> int:
    manifest = json.loads(DEFAULT_MANIFEST.read_text())
    kind = manifest["kinds"]["cgb-acid2"]
    checks = 0
    pixels = [((x * 7) & 255, (y * 5) & 255, (x ^ y) & 255) for y in range(H) for x in range(W)]
    if decode_png(encode_png_rgb(pixels)) != pixels:
        print("acid2-local self-test fail: png round trip")
        return 1
    checks += 1
    ppm = PPM_HEADER + bytes(c for px in pixels for c in px)
    if compare(read_ppm(ppm), pixels) != (0, "acid2 result=match"):
        print("acid2-local self-test fail: equal frames")
        return 1
    checks += 1
    changed = list(pixels)
    changed[1000] = (changed[1000][0] ^ 1, changed[1000][1], changed[1000][2])
    if compare(changed, pixels) != (1, "acid2 result=differs pixels=1"):
        print("acid2-local self-test fail: one-pixel mismatch")
        return 1
    checks += 1
    with tempfile.TemporaryDirectory(prefix="gbb-acid2-st-") as tmp:
        fake = pathlib.Path(tmp) / "fake.rom"
        fake.write_bytes(b"\x00" * 64)
        try:
            check_pins(kind, fake, None)
        except Refused as exc:
            if str(exc) != "rom sha256 not pinned":
                print("acid2-local self-test fail: wrong refusal")
                return 1
        else:
            print("acid2-local self-test fail: fake rom accepted")
            return 1
    checks += 1
    with tempfile.TemporaryDirectory(prefix="gbb-acid2-st-") as tmp:
        good = pathlib.Path(tmp) / "good.bin"
        good.write_bytes(b"pinned")
        got = read_pinned(good, hashlib.sha256(b"pinned").hexdigest(), "rom")
        if got != b"pinned":
            print("acid2-local self-test fail: pinned bytes not returned")
            return 1
    checks += 1
    print(f"acid2-local self-test pass checks={checks}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--rom", type=pathlib.Path)
    ap.add_argument("--reference", type=pathlib.Path)
    ap.add_argument("--runner", type=pathlib.Path)
    ap.add_argument("--rom-kind", choices=("cgb-acid2", "dmg-acid2"))
    ap.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not (args.rom and args.reference and args.runner and args.rom_kind):
        ap.error("--rom, --reference, --runner and --rom-kind are required")
    # Exit codes: 0 match, 1 frames differ, 2 refused (unpinned input), 3 harness error
    # (manifest, runner, decode). Nothing else may reach exit 1.
    try:
        manifest = json.loads(args.manifest.read_text())
        kind = manifest["kinds"][args.rom_kind]
        budget = manifest["ldbb_budget_half_dots"]
        kind["rom_sha256"], kind["reference_sha256"], kind["runner_model"], kind["rom_size"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"acid2 error: manifest unusable ({exc.__class__.__name__})")
        return 3
    try:
        rom_bytes, ref_bytes = check_pins(kind, args.rom, args.reference)
    except Refused as exc:
        print(f"acid2 refused: {exc}")
        return 2
    try:
        reference = decode_png(ref_bytes)
        frame = read_ppm(run_core(args.runner, kind, rom_bytes, budget))
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError, zlib.error) as exc:
        print(f"acid2 error: {exc}")
        return 3
    code, message = compare(frame, reference)
    print(message)
    return code


if __name__ == "__main__":
    sys.exit(main())
