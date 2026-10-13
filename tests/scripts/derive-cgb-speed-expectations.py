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
PHASE_SPEEDS = (1, 2, 1, 2)


def rows(speed_factor):
    result = []
    phase_speeds = (1, speed_factor, 1, speed_factor)
    for phase, source_speed in enumerate(phase_speeds):
        tima = Fraction(DOTS_PER_LINE * source_speed, TAC_PERIOD_T[1])
        result.append(("tima", phase, math.floor(tima), math.ceil(tima)))
        key1 = 0x7E | (0x80 if source_speed == 2 else 0)
        result.append(("key1", phase, key1, key1))
        if phase < 3:
            result.append(("key1-armed", phase, key1 | 1, key1 | 1))
            destination = phase_speeds[phase + 1]
            stall_half_dots = Fraction(STALL_T * (2 if destination == 1 else 2),
                                       1 if destination == 1 else speed_factor)
            stop_half_dots = Fraction(STOP_M_CYCLES * 4 * 2, source_speed)
            line_center = ((stall_half_dots + stop_half_dots) / (2 * DOTS_PER_LINE)) % 154
            line_min = math.floor(line_center) - 2
            line_max = math.ceil(line_center) + 2
            result.append(("stop-lines", phase, line_min, line_max))
            next_key1 = 0x7E | (0x80 if destination == 2 else 0)
            result.append(("key1-after", phase, next_key1, next_key1))
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
