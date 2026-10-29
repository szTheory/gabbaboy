"""Original synthetic ROMs and a bounded runner helper shared by the host-mode harnesses.

Stdlib only. Load it from a `python3 -I` script with importlib (isolated mode disables sibling
imports):

    spec = importlib.util.spec_from_file_location("host_fixture", Path(__file__).with_name("host_fixture.py"))

Every ROM is generated here from a few bytes of hand-assembled Game Boy code, so no third-party
image is involved and nothing binary is committed.
"""
from __future__ import annotations

import os
import signal
import subprocess

if not __debug__:  # the harnesses check explicitly, never with assert, but -O is refused anyway
    raise SystemExit("host_fixture refuses to run under python -O")

KINDS = ("counter", "write5a", "idle", "spin-increment", "illegal-opcode")

# Hand-assembled SM83 programs placed at $0150. Each begins by enabling cartridge RAM
# (ld a,$0A; ld ($0000),a) and ends in a one-instruction spin (jr -2).
_ENABLE_RAM = bytes([0x3E, 0x0A, 0xEA, 0x00, 0x00])
_SPIN = bytes([0x18, 0xFE])
_PROGRAMS = {
    # ld a,($A000); inc a; jr nz,+2; ld a,$01; ld ($A000),a; spin.
    # 0xFF wraps to 0x00 and is replaced by 0x01, so the counter never stores 0.
    "counter": _ENABLE_RAM + bytes([0xFA, 0x00, 0xA0, 0x3C, 0x20, 0x02, 0x3E, 0x01,
                                    0xEA, 0x00, 0xA0]) + _SPIN,
    # ld a,$5A; ld ($A000),a; spin.
    "write5a": _ENABLE_RAM + bytes([0x3E, 0x5A, 0xEA, 0x00, 0xA0]) + _SPIN,
    # Touches no cartridge RAM.
    "idle": _SPIN,
    # Never settles: increments the 16-bit little-endian value at $A000/$A001 in a tight loop, so
    # cartridge RAM differs at every frame boundary (the signal rows need an image that a partial
    # frame, a missed flush or a stale flush would visibly change).
    #   loop: ld a,($A000); inc a; ld ($A000),a; jr nz,loop; ld a,($A001); inc a; ld ($A001),a; jr loop
    "spin-increment": _ENABLE_RAM + bytes([0xFA, 0x00, 0xA0, 0x3C, 0xEA, 0x00, 0xA0, 0x20, 0xF7,
                                           0xFA, 0x01, 0xA0, 0x3C, 0xEA, 0x01, 0xA0, 0x18, 0xEE]),
    # ld a,$5A; ld ($A000),a; then opcode $D3, which the SM83 leaves undefined: the core stops.
    "illegal-opcode": _ENABLE_RAM + bytes([0x3E, 0x5A, 0xEA, 0x00, 0xA0, 0xD3]),
}


def header_checksum(rom: bytearray) -> int:
    """Header checksum over $0134..$014C, as the boot ROM computes it."""
    total = 0
    for index in range(0x134, 0x14D):
        total = (total - rom[index] - 1) & 0xFF
    return total


def build_rom(kind: str, cart_type: int, ram_code: int, rom_code: int = 0) -> bytes:
    """A header-valid ROM of 32768 << rom_code bytes whose program is `kind`."""
    if kind not in _PROGRAMS:
        raise ValueError(f"unknown ROM kind {kind!r}")
    if not 0 <= rom_code <= 8:
        raise ValueError("rom_code out of range")
    rom = bytearray(32768 << rom_code)
    rom[0x100:0x104] = bytes([0x00, 0xC3, 0x50, 0x01])  # nop; jp $0150
    rom[0x147] = cart_type
    rom[0x148] = rom_code
    rom[0x149] = ram_code
    program = _PROGRAMS[kind]
    rom[0x150:0x150 + len(program)] = program
    rom[0x14D] = header_checksum(rom)
    return bytes(rom)


def run_runner(runner: str, args: list[str], cwd: str, timeout: float) -> tuple[int, str, str]:
    """Runs the runner with a hard time bound. On expiry the whole process group is killed and
    TimeoutError is raised, so a hung runner can never wedge a test."""
    process = subprocess.Popen(
        [runner, *args],
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        start_new_session=(os.name != "nt"),
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        try:
            if os.name == "nt":
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            pass
        process.communicate()
        raise TimeoutError(f"runner exceeded {timeout} s") from error
    return process.returncode, stdout, stderr
