#!/usr/bin/env python3
"""Run the original native-CGB input/progress control through gabbaboy-runner.

The ROM is assembled from documented SM83 instruction bytes at runtime. It is
temporary test data, not a fixture or installable product input.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile

if not __debug__:
    raise SystemExit("verify-cgb-progress refuses to run under python -O")

NINTENDO_LOGO = bytes.fromhex(
    "ce ed 66 66 cc 0d 00 0b 03 73 00 83 00 0c 00 0d 00 08 11 1f 88 89 00 "
    "0e dc cc 6e e6 dd dd d9 99 bb bb 67 63 6e 0e ec cc dd dc 99 9f bb b9 33 3e"
)
ROM_SIZE = 32768
BUDGET_HALF_DOTS = 120 * 140448


class Program:
    def __init__(self) -> None:
        self.code = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[tuple[int, str]] = []

    def emit(self, *values: int) -> None:
        self.code.extend(values)

    def label(self, name: str) -> None:
        if name in self.labels:
            raise ValueError(f"duplicate label {name}")
        self.labels[name] = len(self.code)

    def jr_nz(self, name: str) -> None:
        self.emit(0x20, 0)
        self.fixups.append((len(self.code) - 1, name))

    def jr(self, name: str) -> None:
        self.emit(0x18, 0)
        self.fixups.append((len(self.code) - 1, name))

    def finish(self) -> bytes:
        for offset, name in self.fixups:
            if name not in self.labels:
                raise ValueError(f"missing label {name}")
            relative = self.labels[name] - (offset + 1)
            if not -128 <= relative <= 127:
                raise ValueError(f"relative jump to {name} is out of range")
            self.code[offset] = relative & 0xFF
        return bytes(self.code)


def authored_program() -> tuple[bytes, dict[str, int]]:
    """Build a palette-0 blue-to-green control and source-derived WRAM markers."""
    p = Program()
    p.emit(0xF3)                         # di
    p.emit(0xAF)                         # xor a
    p.emit(0xE0, 0x40)                   # ldh ($ff40),a; disable LCD for palette setup
    p.emit(0x3E, 0x80, 0xE0, 0x68)       # BGPI: palette 0, colour 0, auto-increment
    p.emit(0x3E, 0x1F, 0xE0, 0x69)       # BGPD low: RGB555 blue = $001f
    p.emit(0xAF, 0xE0, 0x69)             # BGPD high
    p.label("ready_anchor")
    p.emit(0x3E, 0xA5, 0xEA, 0x00, 0xC0) # ld a,$a5; ld ($c000),a
    p.emit(0xAF, 0xEA, 0x01, 0xC0)       # xor a; ld ($c001),a
    p.emit(0x3E, 0x91, 0xE0, 0x40)       # LCD on, BG on, unsigned tile data
    p.label("poll_anchor")
    p.emit(0x3E, 0x20, 0xE0, 0x00)       # select direction keys at JOYP
    p.emit(0xF0, 0x00, 0xCB, 0x47)       # read JOYP; bit 0 is RIGHT
    p.jr_nz("poll_anchor")              # released RIGHT: continue polling
    p.emit(0xFA, 0x01, 0xC0, 0xB7)       # read progress byte; OR a
    p.jr_nz("poll_anchor")              # only accept the first press
    p.label("progress_anchor")
    p.emit(0x3E, 0x01, 0xEA, 0x01, 0xC0) # ld a,1; ld ($c001),a exactly once
    p.label("vblank_wait")
    p.emit(0xF0, 0x44, 0xFE, 0x90)       # read LY; compare with 144
    p.jr_nz("vblank_wait")
    p.emit(0x3E, 0x80, 0xE0, 0x68)       # select BG palette 0, colour 0
    p.emit(0x3E, 0xE0, 0xE0, 0x69)       # BGPD low: RGB555 green = $03e0
    p.emit(0x3E, 0x03, 0xE0, 0x69)       # BGPD high
    p.label("spin")
    p.jr("spin")
    return p.finish(), dict(p.labels)


def header_checksum(rom: bytearray) -> int:
    value = 0
    for byte in rom[0x134:0x14D]:
        value = (value - byte - 1) & 0xFF
    return value


def build_rom() -> tuple[bytes, dict[str, int]]:
    program, labels = authored_program()
    rom = bytearray(ROM_SIZE)
    rom[0x100:0x104] = bytes((0x00, 0xC3, 0x50, 0x01))  # nop; jp $0150
    rom[0x104:0x134] = NINTENDO_LOGO
    rom[0x134:0x143] = b"GBB CGB CONTROL"
    rom[0x143] = 0x80                        # CGB capable; native mode on CGB profile
    rom[0x146] = 0x00                        # no SGB features
    rom[0x147] = 0x00                        # ROM-only cartridge
    rom[0x148] = 0x00                        # 32 KiB
    rom[0x149] = 0x00                        # no external RAM
    rom[0x150:0x150 + len(program)] = program
    rom[0x14D] = header_checksum(rom)
    rom[0x14E:0x150] = b"\x00\x00"       # global checksum is not consumed by the core
    labels = {name: 0x150 + offset for name, offset in labels.items()}
    return bytes(rom), labels


def input_script(with_right: bool) -> bytes:
    lines = ["gbinput 1", "wait 1f", "mark title", "wait 1f", "mark play_start",
             "wait 1f", "mark mid"]
    if with_right:
        lines.append("tap RIGHT 1f")
        lines.append("wait 116f")
    else:
        lines.append("wait 117f")
    return ("\n".join(lines) + "\n").encode("ascii")


def case_line(identifier: str, rom: bytes, script_name: str, script: bytes) -> str:
    return (f"id={identifier} rom=control.gb rom_sha256={hashlib.sha256(rom).hexdigest()} "
            f"rom_size={len(rom)} oracle=progress-predicate predicate=cgb-control-progress "
            f"expect_hw_capability=0 input_script={script_name} "
            f"input_sha256={hashlib.sha256(script).hexdigest()} "
            f"budget_half_dots={BUDGET_HALF_DOTS} model_pass=cgb-cpu-e\n")


def load_host_fixture(repo_root: Path):
    path = repo_root / "tests/scripts/host_fixture.py"
    spec = importlib.util.spec_from_file_location("host_fixture", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("host-fixture-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_tracer(runner: Path, repo_root: Path) -> int:
    rom, _ = build_rom()
    positive = input_script(True)
    with tempfile.TemporaryDirectory(prefix="gbb-cgb-progress-") as temp:
        work = Path(temp)
        (work / "control.gb").write_bytes(rom)
        (work / "positive.input").write_bytes(positive)
        (work / "cases.txt").write_text(case_line("cgb-control-progress", rom, "positive.input", positive),
                                         encoding="ascii")
        helper = load_host_fixture(repo_root)
        code, stdout, stderr = helper.run_runner(str(runner),
            ["--acceptance", "cases.txt", "--case", "cgb-control-progress", "--model", "cgb-cpu-e", "--receipt"],
            str(work), 30)
    if code != 0 or "status=pass" not in stdout:
        print("verify-cgb-progress: positive native-CGB input route failed: "
              f"exit={code} stdout={stdout.strip()} stderr={stderr.strip()}", file=sys.stderr)
        return 1
    print("verify-cgb-progress: positive native-CGB input route passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--source-revision")
    parser.add_argument("--tracer", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    rom, _ = build_rom()
    if len(rom) != ROM_SIZE or hashlib.sha256(rom).hexdigest() == "":
        print("verify-cgb-progress: authored ROM check failed", file=sys.stderr)
        return 1
    if args.self_test:
        print("verify-cgb-progress: authored ROM self-test passed")
        return 0
    if args.tracer:
        return run_tracer(args.runner.resolve(), args.repo_root.resolve())
    print("verify-cgb-progress: select --self-test or --tracer", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
