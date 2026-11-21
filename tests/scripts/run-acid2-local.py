#!/usr/bin/env python3
"""Optional local acid2 comparison (D-24, rights gate G1). Standard library only; run `python3 -I`.

Never run by required CI except through --self-test, which uses synthetic data only. A ROM or
reference PNG whose SHA-256 is not pinned in tests/acid2/manifest.json is refused before it is
run or decoded (T-11-19), and the PNG decoder accepts one bounded 160x144 layout (T-11-20).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import struct
import subprocess
import sys
import tempfile
import time
import zlib

W, H = 160, 144
HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_MANIFEST = HERE.parent / "acid2" / "manifest.json"
PNG_SIG = b"\x89PNG\r\n\x1a\n"
MAX_IDAT = 1 << 20
MAX_RUNNER_OUTPUT = 1 << 16
MAX_RUNNER_BINARY = 64 * 1024 * 1024
PPM_HEADER = b"P6\n160 144\n255\n"
MAX_PPM_BYTES = len(PPM_HEADER) + W * H * 3
ADMITTED_GUEST_BUDGET_HALF_DOTS = 4213440
ADMITTED_PROFILES = {
    "dmg": {"rom_kind": "dmg", "reference": "source/dmg/img/reference-dmg.png",
            "runner_model": "dmg-cpu-b", "mode": "dmg"},
    "dmg-on-cgb": {"rom_kind": "dmg", "reference": "source/dmg/img/reference-cgb.png",
                    "runner_model": "cgb-cpu-e", "mode": "dmg"},
    "cgb": {"rom_kind": "cgb", "reference": "source/cgb/img/reference.png",
            "runner_model": "cgb-cpu-e", "mode": "cgb"},
}


class Refused(Exception):
    pass


class ManifestInvalid(Exception):
    def __init__(self, error_type: str):
        self.error_type = error_type


def parse_manifest(manifest_bytes: bytes, rom_kind: str) -> tuple[dict, int]:
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8", "strict"))
        kind = manifest["kinds"][rom_kind]
        budget = manifest["ldbb_budget_half_dots"]
        kind["rom_sha256"], kind["reference_sha256"], kind["runner_model"], kind["rom_size"]
        return kind, budget
    except (UnicodeError, ValueError, KeyError, TypeError) as exc:
        raise ManifestInvalid(exc.__class__.__name__) from None


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


def run_core(runner: pathlib.Path, kind: dict, rom: bytes, budget: int,
             timeout: float = 300) -> bytes:
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
                              cwd=work, capture_output=True, timeout=timeout)
        if len(proc.stdout) > MAX_RUNNER_OUTPUT or len(proc.stderr) > MAX_RUNNER_OUTPUT:
            raise RuntimeError("runner output limit exceeded")
        ppm = work / "out" / "acid2.ppm"
        if not ppm.is_file():
            detail = proc.stdout.decode("utf-8", "replace").strip().splitlines()[-1:] or ["no output"]
            raise RuntimeError(f"runner produced no frame (exit {proc.returncode}): {detail[0][:160]}")
        if ppm.stat().st_size > MAX_PPM_BYTES:
            raise RuntimeError("runner frame exceeds fixed PPM size")
        if proc.returncode not in (0, 1):
            detail = (proc.stderr or proc.stdout).decode("utf-8", "replace").strip().splitlines()[-1:]
            raise RuntimeError(f"runner failed (exit {proc.returncode}): {(detail or ['no output'])[0][:160]}")
        return ppm.read_bytes()


def run_admitted_comparison(members: dict[str, bytes], manifest: dict,
                            runner: pathlib.Path, kind: str,
                            deadline_seconds: float = 25) -> dict:
    """Run one comparison from an already rights/admission-validated Acid2 bundle.

    This helper does not grant or check rights. The caller must complete the immutable
    diagnostic-closeout gate and current-runner qualification before passing these bytes.
    """
    profile = ADMITTED_PROFILES.get(kind)
    if profile is None:
        raise Refused("unsupported admitted Acid2 profile")
    if not isinstance(members, dict) or not isinstance(manifest, dict):
        raise Refused("validated Acid2 bundle inputs unavailable")
    if not isinstance(deadline_seconds, (int, float)) or isinstance(deadline_seconds, bool) \
            or not 0 < deadline_seconds <= 25:
        raise Refused("Acid2 deadline outside fixed 25-second limit")
    deadline = time.monotonic() + deadline_seconds
    try:
        runner_info = runner.lstat()
        if runner.is_symlink() or not runner.is_file() or runner_info.st_size > MAX_RUNNER_BINARY:
            raise Refused("current runner artifact type or size refused")
        runner_bytes = runner.read_bytes()
    except OSError:
        raise Refused("current runner artifact unavailable") from None
    if len(runner_bytes) != runner_info.st_size:
        raise Refused("current runner artifact changed while reading")
    runner_sha256 = hashlib.sha256(runner_bytes).hexdigest()

    mask_module_path = HERE / "verify-acid2-masks.py"
    spec = importlib.util.spec_from_file_location("phase24_admitted_acid2_mask", mask_module_path)
    if spec is None or spec.loader is None:
        raise Refused("Acid2 source-mask verifier unavailable")
    masks = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(masks)

    rom_kind = profile["rom_kind"]
    suffix = "gb" if rom_kind == "dmg" else "gbc"
    derivative_path = f"derivatives/{rom_kind}-acid2.{suffix}"
    derivative_row = next((row for row in manifest.get("derivatives", [])
                           if isinstance(row, dict) and row.get("kind") == rom_kind), None)
    rom = members.get(derivative_path)
    if (not isinstance(derivative_row, dict) or not isinstance(rom, bytes)
            or derivative_row.get("path") != derivative_path
            or derivative_row.get("sha256") != hashlib.sha256(rom).hexdigest()
            or derivative_row.get("size_bytes") != len(rom)
            or len(rom) != 32768 or rom[0x104:0x134] != bytes(48)):
        raise Refused("admitted Acid2 derivative identity mismatch")

    scope_model = "cgb" if profile["runner_model"] == "cgb-cpu-e" else "dmg"
    scope = manifest.get("model_scope", {}).get(scope_model, {})
    if (not isinstance(scope, dict) or scope.get("runner_model") != profile["runner_model"]
            or scope.get("hardware_claim") is not False):
        raise Refused("admitted Acid2 software model scope mismatch")

    pin = masks.SOURCE_PINS[rom_kind]
    cells = masks.acid2_source_cells(
        rom_kind,
        members[f"derived/{rom_kind}/src/{pin['source']}"] ,
        members[f"source/{rom_kind}/inc/oam.asm"],
        members[f"source/{rom_kind}/inc/background.asm"],
        members["source/mgblib/src/display/ResetDisplay.asm"],
    )
    mask = members.get(f"masks/{rom_kind}.bin")
    masks.validate_mask(mask, cells)
    reference_bytes = members.get(profile["reference"])
    if not isinstance(reference_bytes, bytes):
        raise Refused("admitted Acid2 reference unavailable")
    reference = decode_png(reference_bytes)

    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise Refused("Acid2 runtime deadline exceeded")
    runner_kind = {"rom_sha256": hashlib.sha256(rom).hexdigest(),
                   "rom_size": len(rom), "runner_model": profile["runner_model"]}
    try:
        ppm = run_core(runner, runner_kind, rom, ADMITTED_GUEST_BUDGET_HALF_DOTS,
                       timeout=remaining)
    except subprocess.TimeoutExpired:
        raise Refused("Acid2 runtime deadline exceeded") from None
    frame = read_ppm(ppm)
    status, detail = masks.compare_masked(frame, reference, mask, cells)
    differing = sum(1 for index, (actual, expected) in enumerate(zip(frame, reference))
                    if not mask[index] and actual != expected)
    masked = sum(mask)
    return {
        "profile": kind,
        "rom_kind": rom_kind,
        "runner_model": profile["runner_model"],
        "mode": profile["mode"],
        "hardware_claim": False,
        "rom": {"path": derivative_path, "sha256": hashlib.sha256(rom).hexdigest(),
                "size_bytes": len(rom)},
        "reference": {"path": profile["reference"],
                      "sha256": hashlib.sha256(reference_bytes).hexdigest(),
                      "size_bytes": len(reference_bytes)},
        "mask": {"path": f"masks/{rom_kind}.bin",
                 "sha256": hashlib.sha256(mask).hexdigest(),
                 "masked_pixels": masked, "compared_pixels": W * H - masked},
        "runner_sha256": runner_sha256,
        "guest_budget_half_dots": ADMITTED_GUEST_BUDGET_HALF_DOTS,
        "verdict": "pass" if status == 0 else "mismatch",
        "differing_unmasked_pixels": differing,
        "detail": detail,
    }


def _run_admitted_mode(args: argparse.Namespace) -> int:
    if not (args.runner and args.source_revision and args.fixture_manifest
            and args.current_build_qualification):
        print("acid2 refused: approved mode requires runner, source revision, fixture manifest, "
              "and current build qualification")
        return 2
    root = HERE.parent.parent.resolve(strict=True)
    source_revision = args.source_revision
    try:
        adapter_path = HERE / "verify-diagnostic-admission.py"
        spec = importlib.util.spec_from_file_location("phase24_acid2_admission", adapter_path)
        if spec is None or spec.loader is None:
            raise Refused("admission checker unavailable")
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        fixture_path = args.fixture_manifest.resolve(strict=True)
        fixture_relative = adapter.repository_relative_path(root, fixture_path)
        if fixture_relative != "fixtures/acid2/manifest.json":
            raise Refused("fixture manifest path is not the admitted Acid2 manifest")
        for relative, path in (("tests/scripts/run-acid2-local.py", pathlib.Path(__file__)),
                               (fixture_relative, fixture_path)):
            adapter.require_worktree_source_file(root, source_revision, relative, path)
        validated = adapter.check_diagnostic_closeout(
            root, source_revision, "acid2", require_approved=True)
        members = validated.get("_acid2_bundle_content")
        if not isinstance(members, dict):
            raise Refused("approved Acid2 bundle bytes unavailable")
        manifest_raw = adapter.read_source_file(root, source_revision, fixture_relative)
        if fixture_path.read_bytes() != manifest_raw:
            raise Refused("fixture manifest differs from immutable source revision")
        generic_manifest = json.loads(manifest_raw.decode("utf-8", "strict"))
        manifest_bytes = members.get("build-manifest.json")
        if not isinstance(manifest_bytes, bytes):
            raise Refused("validated Acid2 member manifest unavailable")
        manifest = json.loads(manifest_bytes.decode("utf-8", "strict"))
        if (generic_manifest.get("schema_version") != 1
                or generic_manifest.get("decision", {}).get("status") != "approved"):
            raise Refused("generic Acid2 fixture admission is not approved")

        qualification = root / "tests/scripts/verify-cgb-candidates.py"
        adapter.require_worktree_source_file(
            root, source_revision, "tests/scripts/verify-cgb-candidates.py", qualification)
        qualification_result = subprocess.run(
            [sys.executable, "-I", str(qualification), "--check-build-qualification",
             "--repo-root", str(root), "--source-revision", source_revision,
             "--runner", str(args.runner.resolve(strict=True)),
             "--current-build-qualification", str(args.current_build_qualification.resolve(strict=True))],
            cwd=root, capture_output=True, timeout=10, check=False)
        if (len(qualification_result.stdout) > MAX_RUNNER_OUTPUT
                or len(qualification_result.stderr) > MAX_RUNNER_OUTPUT
                or qualification_result.returncode != 0
                or b"PASS: current runner qualification" not in qualification_result.stdout):
            raise Refused("current runner qualification refused")

        deadline = time.monotonic() + 25
        results = []
        for profile in ("dmg", "dmg-on-cgb", "cgb"):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise Refused("Acid2 total 25-second deadline exceeded")
            results.append(run_admitted_comparison(members, manifest, args.runner.resolve(),
                                                   profile, remaining))
        output = {"status": "pass" if all(row["verdict"] == "pass" for row in results)
                  else "mismatch", "source_revision": source_revision,
                  "derivative_count": 2, "comparison_count": len(results),
                  "deadline_seconds": 25, "comparisons": results}
        print(json.dumps(output, sort_keys=True, separators=(",", ":")))
        return 0 if output["status"] == "pass" else 1
    except (OSError, ValueError, RuntimeError, Refused, subprocess.SubprocessError,
            json.JSONDecodeError) as exc:
        print(f"acid2 refused: {exc}")
        return 2


def self_test() -> int:
    kind, _budget = parse_manifest(DEFAULT_MANIFEST.read_bytes(), "cgb-acid2")
    checks = 0
    pixels = [((x * 7) & 255, (y * 5) & 255, (x ^ y) & 255) for y in range(H) for x in range(W)]
    if decode_png(encode_png_rgb(pixels)) != pixels:
        print("acid2-local self-test fail: png round trip")
        return 1
    checks += 1
    try:
        parse_manifest(b'{"kinds": {}}', "cgb-acid2")
    except ManifestInvalid as exc:
        if exc.error_type != "KeyError":
            print("acid2-local self-test fail: wrong malformed-manifest failure")
            return 1
    else:
        print("acid2-local self-test fail: malformed manifest accepted")
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--self-test-tracer", action="store_true")
    ap.add_argument("--rom", type=pathlib.Path)
    ap.add_argument("--reference", type=pathlib.Path)
    ap.add_argument("--runner", type=pathlib.Path)
    ap.add_argument("--require-approved", action="store_true")
    ap.add_argument("--source-revision")
    ap.add_argument("--fixture-manifest", type=pathlib.Path)
    ap.add_argument("--current-build-qualification", type=pathlib.Path)
    ap.add_argument("--rom-kind", choices=("cgb-acid2", "dmg-acid2"))
    ap.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args(argv)
    if args.require_approved:
        if args.rom or args.reference or args.rom_kind:
            ap.error("--require-approved cannot be combined with upstream-pin inputs")
        return _run_admitted_mode(args)
    if args.self_test_tracer:
        if args.runner is None:
            ap.error("--self-test-tracer requires --runner")
        adapter_path = HERE / "verify-diagnostic-admission.py"
        spec = importlib.util.spec_from_file_location("phase22_diagnostic_admission", adapter_path)
        if spec is None or spec.loader is None:
            print("acid2 tracer error: admission adapter unavailable")
            return 3
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        return adapter.run_tracer(args.runner.resolve())
    if args.self_test:
        return self_test()
    if not (args.rom and args.reference and args.runner and args.rom_kind):
        ap.error("--rom, --reference, --runner and --rom-kind are required")
    # Exit codes: 0 match, 1 frames differ, 2 refused (unpinned input), 3 harness error
    # (manifest, runner, decode). Nothing else may reach exit 1.
    # No third-party bytes may reach the runner while the source/component approval record is
    # absent or unresolved. Bind the runner policy and manifest to the immutable source commit
    # before parsing the manifest or reading ROM/reference data.
    try:
        root = HERE.parent.parent
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
                                  check=True, timeout=30).stdout.decode("ascii").strip()
        adapter_path = HERE / "verify-diagnostic-admission.py"
        spec = importlib.util.spec_from_file_location("phase22_diagnostic_admission", adapter_path)
        if spec is None or spec.loader is None:
            raise Refused("admission adapter unavailable")
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        manifest_path = args.manifest.resolve(strict=True)
        manifest_relative = adapter.repository_relative_path(root, manifest_path)
        adapter.require_approved(
            root, revision,
            source_paths=(("tests/scripts/run-acid2-local.py", pathlib.Path(__file__)),
                          (manifest_relative, manifest_path)))
        manifest_bytes = adapter.read_source_file(root, revision, manifest_relative)
    except (OSError, ValueError, subprocess.SubprocessError, RuntimeError) as exc:
        print(f"acid2 refused: scope-resolution-required ({exc})")
        return 2
    try:
        kind, budget = parse_manifest(manifest_bytes, args.rom_kind)
    except ManifestInvalid as exc:
        print(f"acid2 error: manifest unusable ({exc.error_type})")
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
