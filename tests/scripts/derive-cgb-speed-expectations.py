#!/usr/bin/env python3
"""Derive deterministic guest bounds from the documented Game Boy timing units."""

import argparse
import math
import pathlib
import sys
from fractions import Fraction

CPU_HZ = 4_194_304
DOTS_PER_LINE = 456
TAC_PERIOD_T = (1024, 16, 64, 256)
DIV_PERIOD_T = 256
SERIAL_BIT_T = 512
STALL_T = 0x20004  # Measured committed-core pass window in 12-09-SUMMARY.md; constant stayed pinned.
STOP_M_CYCLES = 2
LY_POLL_LOOP_M_CYCLES = 7
M_CYCLE_T = 4
PHASE_SPEEDS = (1, 2, 1, 2)
HOSTILE_BASE_METRICS = (
    "hostile-key1-before", "hostile-key1-armed", "hostile-key1-after",
    "hostile-double-speed", "hostile-handler", "hostile-lines",
    "hostile-halt", "hostile-if",
)


def rows(speed_factor):
    result = []
    phase_speeds = (1, speed_factor, 1, speed_factor)
    for phase, source_speed in enumerate(phase_speeds):
        line_seconds = Fraction(DOTS_PER_LINE, CPU_HZ)
        tima_hz = Fraction(CPU_HZ, TAC_PERIOD_T[1])
        tima = tima_hz * line_seconds * source_speed
        poll_jitter_t = LY_POLL_LOOP_M_CYCLES * M_CYCLE_T
        tima_jitter = Fraction(poll_jitter_t, TAC_PERIOD_T[1])
        result.append(("tima", phase, math.floor(tima - tima_jitter),
                       math.ceil(tima + tima_jitter)))
        div_hz = Fraction(CPU_HZ, DIV_PERIOD_T)
        div = div_hz * line_seconds * source_speed
        div_jitter = Fraction(poll_jitter_t, DIV_PERIOD_T)
        result.append(("div", phase, math.floor(div - div_jitter),
                       math.ceil(div + div_jitter)))
        serial_seconds = Fraction(8 * SERIAL_BIT_T, CPU_HZ)
        serial_lines = serial_seconds / line_seconds / source_speed
        result.append(("serial-lines", phase, math.floor(serial_lines), math.ceil(serial_lines) + 1))
        # CGB SC forces bits 1-6 high; the internal-clock select remains in bit 0 after completion.
        result.append(("serial-sc", phase, 0x7F, 0x7F))
        result.append(("serial-if", phase, 1, 1))
        result.append(("nr52-start", phase, 1, 1))
        length_clock_max_lines = Fraction(2 * CPU_HZ, 512) / DOTS_PER_LINE
        result.append(("nr52-lines", phase, 1, math.ceil(length_clock_max_lines) + 2))
        result.append(("nr52-end", phase, 0, 0))
        result.append(("dma-159", phase, 0xFF, 0xFF))
        result.append(("dma-161", phase, 0xA5, 0xA5))
        key1 = 0x7E | (0x80 if source_speed == 2 else 0)
        if source_speed != 1:
            key1 = 0xFE
        result.append(("key1", phase, key1, key1))
        if phase < 3:
            result.append(("key1-armed", phase, key1 | 1, key1 | 1))
            destination = phase_speeds[phase + 1]
            stall_half_dots = Fraction(STALL_T * 2, destination)
            stop_half_dots = Fraction(STOP_M_CYCLES * 4 * 2, source_speed)
            line_center = ((stall_half_dots + stop_half_dots) / (2 * DOTS_PER_LINE)) % 154
            line_min = math.floor(line_center) - 2
            line_max = math.ceil(line_center) + 2
            result.append(("stop-lines", phase, line_min, line_max))
            next_key1 = 0xFE if destination != 1 else 0x7E
            result.append(("key1-after", phase, next_key1, next_key1))

    # D-02 case 3: a timer request is pending with IE set while IME is clear;
    # EI immediately precedes STOP, so its delayed enable matures at retirement.
    # The switch is the no-stall branch, then the pending handler runs. Bounds
    # for the line delta use the named 2-M switch cost plus worst-case five-M
    # interrupt entry, bounded guest handler, and post-handler LY sample: under
    # one PPU line at the destination speed.
    fast_stop_half_dots = STOP_M_CYCLES * M_CYCLE_T * 2
    case3_path_max_m = 5 + 40 + 8
    case3_max_half_dots = fast_stop_half_dots + case3_path_max_m * M_CYCLE_T
    case3_line_max = math.ceil(case3_max_half_dots / (2 * DOTS_PER_LINE))
    result.extend((
        ("hostile-key1-before", 1, 0x7E, 0x7E),
        ("hostile-key1-armed", 1, 0x7F, 0x7F),
        ("hostile-key1-after", 1, 0xFE, 0xFE),
        ("hostile-double-speed", 1, 1, 1),
        ("hostile-handler", 1, 1, 1),
        ("hostile-lines", 1, 0, case3_line_max),
        ("hostile-halt", 1, 0, 0),
        ("hostile-if", 1, 0, 0),
    ))
    return result


def format_rows(table_rows):
    return "".join(f"{name} {phase} {low} {high}\n" for name, phase, low, high in table_rows)


def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", type=pathlib.Path)
    modes.add_argument("--check", type=pathlib.Path)
    parser.add_argument("--speed-factor", type=int, default=2)
    args = parser.parse_args()
    if args.speed_factor < 2 or args.speed_factor > 8:
        parser.error("--speed-factor must be between 2 and 8")
    expected = format_rows(rows(args.speed_factor))
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(expected, encoding="ascii", newline="")
        print(f"cgb-speed-expectations write pass rows={expected.count(chr(10))}")
        return 0
    try:
        actual = args.check.read_text(encoding="ascii")
    except OSError as error:
        print(f"cgb-speed-expectations mismatch line=1 ({error})", file=sys.stderr)
        return 1
    if actual != expected:
        expected_lines = expected.splitlines()
        actual_lines = actual.splitlines()
        first = 1
        for first, (want, got) in enumerate(zip(expected_lines, actual_lines), 1):
            if want != got:
                break
        else:
            first = min(len(expected_lines), len(actual_lines)) + 1
        print(f"cgb-speed-expectations mismatch line={first}", file=sys.stderr)
        return 1
    print(f"cgb-speed-expectations check pass rows={expected.count(chr(10))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
