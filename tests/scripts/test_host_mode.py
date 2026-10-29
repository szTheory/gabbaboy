#!/usr/bin/env python3
"""End-to-end host-mode scenarios for gabbaboy-runner (Phase 18, HOST-01).

    python3 -I test_host_mode.py --runner PATH --work DIR --scenario NAME

Each scenario starts from an empty directory under --work, drives the real runner process, and prints
`host-mode scenario=<name> pass` or `FAIL <name>: <why>` (exit 1). Assertions are explicit checks, never
`assert`, so the harness behaves identically under any interpreter flags; python -O is refused.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import shutil
import sys
from pathlib import Path

if not __debug__:
    raise SystemExit("test_host_mode refuses to run under python -O")

_spec = importlib.util.spec_from_file_location(
    "host_fixture", Path(__file__).resolve().with_name("host_fixture.py"))
host_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(host_fixture)

RUN_TIMEOUT = 50.0  # below the 60 s CTest bound so a hang fails here with a reason
MBC1_RAM_BATTERY = 0x03
MBC5_RAM_BATTERY = 0x1B
RAM_8K = 0x02


class Failure(Exception):
    pass


def require(condition: bool, why: str) -> None:
    if not condition:
        raise Failure(why)


def fresh_dir(path: Path) -> Path:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def run(runner: str, rom: Path, save_dir: Path, frames: int, cwd: Path) -> tuple[int, str, str]:
    return host_fixture.run_runner(
        runner, ["--rom", str(rom), "--save-dir", str(save_dir), "--frames", str(frames)],
        str(cwd), RUN_TIMEOUT)


def forbid_work_path(work: Path, *streams: str) -> None:
    """Privacy prohibition (T-18-05): no diagnostic may echo the caller's absolute path."""
    for needle in {str(work), str(work.resolve())}:
        for stream in streams:
            require(needle not in stream, "diagnostic leaked the absolute work directory path")


def listing(save_dir: Path) -> list[str]:
    return sorted(entry.name for entry in save_dir.iterdir())


def expect_clean_exit(code: int, stderr: str, frames: int) -> None:
    require(code == 0, f"exit {code}, expected 0: {stderr.strip()!r}")
    ready = stderr.find("gbb-host: ready")
    exit_line = re.search(
        rf"gbb-host: exit status=clean reason=frames stopped_at_frame={frames} "
        r"flush=(written|unchanged)\b", stderr)
    require(ready >= 0, "missing 'gbb-host: ready'")
    require(exit_line is not None, "missing the clean exit line with flush=(written|unchanged)")
    require(ready < exit_line.start(), "'gbb-host: ready' must precede the exit line")


def scenario_continuation(runner: str, work: Path) -> None:
    """XFER-002: a second process imports the first run's raw .sav, so the guest counter advances."""
    base = fresh_dir(work)
    rom = base / "counter.gb"
    rom.write_bytes(host_fixture.build_rom("counter", MBC1_RAM_BATTERY, RAM_8K))
    saves = fresh_dir(base / "saves")
    sav = saves / "counter.sav"

    code, out, err = run(runner, rom, saves, 60, base)
    expect_clean_exit(code, err, 60)
    require(sav.is_file(), "first run did not publish counter.sav")
    first = sav.read_bytes()
    require(len(first) == 8192, f"first image is {len(first)} bytes, expected 8192")
    require(first[0] == 0x01, f"first run counter is {first[0]:#04x}, expected 0x01")
    require(listing(saves) == ["counter.sav"], f"unexpected directory entries {listing(saves)}")
    forbid_work_path(base, out, err)

    # An import-ignoring runner would start from fresh RAM and write 0x01 again; only an import of the
    # first run's bytes gives exactly 0x02 here.
    code, out, err = run(runner, rom, saves, 60, base)
    expect_clean_exit(code, err, 60)
    second = sav.read_bytes()
    require(len(second) == 8192, f"second image is {len(second)} bytes")
    require(second[0] == 0x02, f"second run counter is {second[0]:#04x}, expected 0x02 (import lost)")
    require(second[1:] == first[1:], "second run altered bytes the guest never touched")
    require(listing(saves) == ["counter.sav"], f"temp file left behind: {listing(saves)}")
    forbid_work_path(base, out, err)

    preload_dir = fresh_dir(base / "preload")
    preload = bytearray((i * 7 + 3) & 0xFF for i in range(8192))
    preload[0] = 0x41
    (preload_dir / "counter.sav").write_bytes(bytes(preload))
    code, out, err = run(runner, rom, preload_dir, 60, base)
    expect_clean_exit(code, err, 60)
    result = (preload_dir / "counter.sav").read_bytes()
    require(len(result) == 8192, f"preloaded image became {len(result)} bytes")
    require(result[0] == 0x42, f"preloaded counter is {result[0]:#04x}, expected 0x42")
    require(result[1:] == bytes(preload[1:]), "preloaded bytes were not preserved")
    require(listing(preload_dir) == ["counter.sav"], f"temp file left behind: {listing(preload_dir)}")
    forbid_work_path(base, out, err)


def expect_refusal(code: int, stdout: str, stderr: str, reason: str, *forbidden: str) -> None:
    """A start-up refusal: exit 2, its own `gbb-host: refused reason=` token, no frame ever ran."""
    require(code == 2, f"exit {code}, expected 2: {stderr.strip()!r}")
    require(f"gbb-host: refused reason={reason}\n" in stderr,
            f"missing 'gbb-host: refused reason={reason}': {stderr.strip()!r}")
    require("gbb-host: ready" not in stderr, "a refused run must not print 'gbb-host: ready'")
    for token in forbidden:
        require(token not in stderr, f"unexpected {token!r} in a {reason} refusal")


def scenario_rom_max(runner: str, work: Path) -> None:
    """D-04: the host ROM bound is the core's 8 MiB, not the 32 KiB acceptance cap."""
    base = fresh_dir(work)
    rom = base / "maxrom.gb"
    saves = fresh_dir(base / "saves")
    try:
        data = host_fixture.build_rom("write5a", MBC5_RAM_BATTERY, RAM_8K, rom_code=8)
        require(len(data) == 8 * 1024 * 1024, "fixture is not exactly 8 MiB")
        rom.write_bytes(data)
        code, out, err = run(runner, rom, saves, 2, base)
        expect_clean_exit(code, err, 2)
        image = (saves / "maxrom.sav").read_bytes()
        require(len(image) == 8192, f"image is {len(image)} bytes, expected 8192")
        require(image[0] == 0x5A, f"byte 0 is {image[0]:#04x}, expected 0x5a")
        require(listing(saves) == ["maxrom.sav"], f"unexpected directory entries {listing(saves)}")
        forbid_work_path(base, out, err)
    finally:
        rom.unlink(missing_ok=True)  # an 8 MiB image has no business surviving the scenario


def scenario_rom_oversize(runner: str, work: Path) -> None:
    """D-04: one byte over 8 MiB is refused by the host (rom-size) before the core ever sees it."""
    base = fresh_dir(work)
    rom = base / "oversize.gb"
    saves = fresh_dir(base / "saves")
    try:
        rom.write_bytes(host_fixture.build_rom("write5a", MBC5_RAM_BATTERY, RAM_8K, rom_code=8) + b"\x00")
        require(rom.stat().st_size == 8 * 1024 * 1024 + 1, "fixture is not exactly 8 MiB + 1")
        code, out, err = run(runner, rom, saves, 2, base)
        # rom-unsupported would mean the core, not the host cap, refused the image.
        expect_refusal(code, out, err, "rom-size", "reason=rom-unsupported")
        require(listing(saves) == [], f"refused run changed the save directory: {listing(saves)}")
        forbid_work_path(base, out, err)
    finally:
        rom.unlink(missing_ok=True)


def scenario_rom_unreadable(runner: str, work: Path) -> None:
    """A missing ROM is rom-unreadable, never a crash and never a created save."""
    base = fresh_dir(work)
    saves = fresh_dir(base / "saves")
    code, out, err = run(runner, base / "absent.gb", saves, 2, base)
    expect_refusal(code, out, err, "rom-unreadable", "reason=rom-size", "reason=rom-unsupported")
    require(listing(saves) == [], f"refused run changed the save directory: {listing(saves)}")
    forbid_work_path(base, out, err)


SCENARIOS = {
    "continuation": scenario_continuation,
    "rom-max": scenario_rom_max,
    "rom-oversize": scenario_rom_oversize,
    "rom-unreadable": scenario_rom_unreadable,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runner", required=True)
    parser.add_argument("--work", required=True)
    parser.add_argument("--scenario", required=True, choices=sorted(SCENARIOS))
    args = parser.parse_args()
    runner = os.path.abspath(args.runner)
    work = Path(os.path.abspath(args.work))
    try:
        SCENARIOS[args.scenario](runner, work)
    except Failure as failure:
        print(f"FAIL {args.scenario}: {failure}")
        return 1
    except (OSError, TimeoutError) as error:
        print(f"FAIL {args.scenario}: {type(error).__name__}: {error}")
        return 1
    print(f"host-mode scenario={args.scenario} pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
