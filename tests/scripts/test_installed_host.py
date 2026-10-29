#!/usr/bin/env python3
"""Installed host-mode smoke for gabbaboy-runner (Phase 18, D-28).

    python3 -I test_installed_host.py --prefix P --work DIR --source-contract docs/host-contract.json

Runs the INSTALLED runner only (never the build-tree one) from a working directory that is unrelated
to the prefix, against a fresh temporary save directory:

  * a two-process continuation reads back a game-visible counter ($01, then $02);
  * a preloaded $41 image yields $42;
  * the installed share/gabbaboy/host-contract.json is byte-identical to the source contract and
    agrees with the installed runner's --print-save-format;
  * one seeded control (the installed JSON with a single digit changed) must be rejected by the same
    comparison with `installed-contract-drift`.

It is a stdlib harness rather than a `cmake -P` script because the counter ROM and the $41 preload
image contain NUL bytes, which CMake strings cannot hold. Assertions are explicit checks, never
`assert`; python -O is refused. Diagnostics name stems and tokens only, never absolute paths.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import sys
from pathlib import Path

if not __debug__:
    raise SystemExit("test_installed_host refuses to run under python -O")

_spec = importlib.util.spec_from_file_location(
    "host_fixture", Path(__file__).resolve().with_name("host_fixture.py"))
host_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(host_fixture)

RUN_TIMEOUT = 50.0  # below the 60 s CTest bound so a hang fails here with a reason
MBC1_RAM_BATTERY = 0x03
RAM_8K = 0x02
DRIFT = "installed-contract-drift"


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


def forbid_path(paths: list[Path], *streams: str) -> None:
    """T-18-32: no diagnostic may echo an absolute path of the caller."""
    for path in paths:
        for needle in {str(path), str(path.resolve())}:
            for stream in streams:
                require(needle not in stream, "diagnostic leaked an absolute path")


def run(runner: Path, args: list[str], cwd: Path) -> tuple[int, str, str]:
    return host_fixture.run_runner(str(runner), args, str(cwd), RUN_TIMEOUT)


def run_host(runner: Path, rom: Path, saves: Path, cwd: Path, frames: int) -> str:
    code, out, err = run(
        runner, ["--rom", str(rom), "--save-dir", str(saves), "--frames", str(frames)], cwd)
    require(code == 0, f"exit {code}, expected 0: {err.strip()!r}")
    require("gbb-host: ready" in err, "missing 'gbb-host: ready'")
    require(re.search(rf"gbb-host: exit status=clean reason=frames stopped_at_frame={frames} ", err),
            "missing the clean exit line")
    return out + err


def compare_contract(installed: bytes, source: bytes, printed_id: str, printed_bytes: int) -> None:
    """The one comparison: installed JSON equals the source byte for byte, and the id and byte count
    the installed runner printed name a row of that JSON."""
    if installed != source:
        raise Failure(f"{DRIFT}: share/gabbaboy/host-contract.json differs from the source contract")
    try:
        rows = json.loads(installed.decode("utf-8"))["save_formats"]["rows"]
    except (UnicodeDecodeError, ValueError, KeyError, TypeError):
        raise Failure(f"{DRIFT}: installed contract is not a host contract document") from None
    matches = [row for row in rows if row.get("id") == printed_id]
    if not matches:
        raise Failure(f"{DRIFT}: printed id {printed_id} is not a row of the installed contract")
    if any(row.get("bytes") != printed_bytes for row in matches):
        raise Failure(f"{DRIFT}: printed bytes {printed_bytes} disagree with the installed row for {printed_id}")


def seed_drift(installed: bytes) -> bytes:
    """One digit of the $03/$02 row's `bytes` value is changed (8192 becomes 8193)."""
    text = installed.decode("utf-8")
    row = re.search(
        r'("type": "0x03",\s*"ram_code": "0x02",.*?"bytes": )8192(,)', text, flags=re.DOTALL)
    require(row is not None, "the $03/$02 row was not found in the installed contract")
    seeded = text[:row.start()] + row.group(1) + "8193" + row.group(2) + text[row.end():]
    require(seeded != text, "the seeded copy equals the original")
    return seeded.encode("utf-8")


def smoke(prefix: Path, work: Path, source_contract: Path) -> None:
    runner = prefix / "bin" / ("gabbaboy-runner.exe" if os.name == "nt" else "gabbaboy-runner")
    installed_contract = prefix / "share" / "gabbaboy" / "host-contract.json"
    require(runner.is_file(), "installed bin/gabbaboy-runner is missing")
    require(installed_contract.is_file(), "installed share/gabbaboy/host-contract.json is missing")
    require(source_contract.is_file(), "the source contract is missing")

    base = fresh_dir(work)
    cwd = fresh_dir(base / "cwd")  # unrelated to the prefix
    rom_dir = fresh_dir(base / "rom")
    rom = rom_dir / "counter.gb"
    rom.write_bytes(host_fixture.build_rom("counter", MBC1_RAM_BATTERY, RAM_8K))
    saves = fresh_dir(base / "save")
    sav = saves / "counter.sav"
    private = [base, prefix]

    streams = run_host(runner, rom, saves, cwd, 60)
    forbid_path(private, streams)
    first = sav.read_bytes()
    require(len(first) == 8192, f"first image is {len(first)} bytes, expected 8192")
    require(first[0] == 0x01, f"first run counter is {first[0]:#04x}, expected 0x01")
    streams = run_host(runner, rom, saves, cwd, 60)
    forbid_path(private, streams)
    second = sav.read_bytes()
    require(len(second) == 8192, f"second image is {len(second)} bytes")
    require(second[0] == 0x02, f"second run counter is {second[0]:#04x}, expected 0x02 (import lost)")
    require(second[1:] == first[1:], "second run altered bytes the guest never touched")
    require(sorted(entry.name for entry in saves.iterdir()) == ["counter.sav"],
            "unexpected entries beside counter.sav")

    preload_dir = fresh_dir(base / "preload")
    preload = bytearray((i * 7 + 3) & 0xFF for i in range(8192))
    preload[0] = 0x41
    (preload_dir / "counter.sav").write_bytes(bytes(preload))
    streams = run_host(runner, rom, preload_dir, cwd, 60)
    forbid_path(private, streams)
    result = (preload_dir / "counter.sav").read_bytes()
    require(result[0] == 0x42, f"preloaded counter is {result[0]:#04x}, expected 0x42")
    require(result[1:] == bytes(preload[1:]), "preloaded bytes were not preserved")

    code, out, err = run(runner, ["--print-save-format", "--rom", str(rom)], cwd)
    require(code == 0, f"--print-save-format exit {code}: {err.strip()!r}")
    printed = re.fullmatch(r"save_format=(gabbaboy-[a-z0-9-]+) bytes=([0-9]+)\n", out)
    require(printed is not None, f"unexpected --print-save-format output {out!r}")
    printed_id, printed_bytes = printed.group(1), int(printed.group(2))
    forbid_path(private, out, err)

    installed = installed_contract.read_bytes()
    source = source_contract.read_bytes()
    compare_contract(installed, source, printed_id, printed_bytes)

    seeded = seed_drift(installed)
    try:
        compare_contract(seeded, source, printed_id, printed_bytes)
    except Failure as rejection:
        require(str(rejection).startswith(f"{DRIFT}:"), f"control rejected for the wrong reason: {rejection}")
        require("differs from the source contract" in str(rejection),
                "control was not rejected by the byte-identity leg")
    else:
        raise Failure("the seeded drift control was accepted")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--work", required=True)
    parser.add_argument("--source-contract", required=True)
    parser.add_argument("--receipt", type=Path,
                        help="write the path-free host smoke result with exclusive create")
    args = parser.parse_args()
    try:
        smoke(Path(os.path.abspath(args.prefix)), Path(os.path.abspath(args.work)),
              Path(os.path.abspath(args.source_contract)))
        if args.receipt is not None:
            payload = json.dumps({"result": "passed", "continuation": "01,02", "preload": "42"},
                                 sort_keys=True) + "\n"
            descriptor = os.open(args.receipt, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload.encode("utf-8"))
    except Failure as failure:
        print(f"FAIL installed-host: {failure}")
        return 1
    except (OSError, TimeoutError) as error:
        print(f"FAIL installed-host: {type(error).__name__}: {error}")
        return 1
    print("installed-host pass continuation=01,02 preload=42 controls=1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
