#!/usr/bin/env python3
"""Hold docs/host-contract.json to the C sources that implement it (Phase 18, D-16).

The contract is hand-written canonical JSON with exactly four sections, in this order: exit_codes, cadence,
rtc_wall_clock and save_formats. This checker covers the first three; verify-save-formats.py covers save_formats.

  --check       the JSON text equals json.dumps(json.loads(text), indent=2, ensure_ascii=True) + newline (keys are
                never re-sorted); the exit_codes rows with a number equal the GBB_HOST_EXIT_TABLE rows of
                src/host/host_exit.h (code, name, meaning) and one more row has code null and the name `crash`;
                the cadence values equal the constants in src/host/gbb_host.h

The JSON and both C files are read with `git show REV:<path>` (never the working tree), so a check sees the
point-in-time facts of one commit. Every failure is `REJECT <code>: <message>` on stderr, exit 1.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

if not __debug__:
    raise SystemExit("verify-host-contract refuses to run under python -O (its checks must stay on)")

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTRACT = "docs/host-contract.json"
EXIT_HEADER = "src/host/host_exit.h"
HOST_HEADER = "src/host/gbb_host.h"
MAX_BYTES = 8 * 1024 * 1024
SECTIONS = ("exit_codes", "cadence", "rtc_wall_clock", "save_formats")
CADENCE_KEYS = ("frame_half_dots", "quiet_frames", "max_dirty_frames", "rtc_compare_frames",
                "sram_loss_window_frames", "rtc_loss_window_frames")
# JSON key -> the constant in gbb_host.h that fixes it. The two loss windows are derived: a stop loses at most
# the frames since the last flush (the age cap) or the clock-only drift since the last compare.
CADENCE_CONSTANTS = {
    "frame_half_dots": "GBB_HOST_FRAME_HALF_DOTS",
    "quiet_frames": "GBB_HOST_QUIET_FRAMES",
    "max_dirty_frames": "GBB_HOST_MAX_DIRTY_FRAMES",
    "rtc_compare_frames": "GBB_HOST_RTC_COMPARE_FRAMES",
    "sram_loss_window_frames": "GBB_HOST_MAX_DIRTY_FRAMES",
    "rtc_loss_window_frames": "GBB_HOST_RTC_COMPARE_FRAMES",
}
EXIT_ROW = re.compile(r'X\(\s*([0-9]+)\s*,\s*([A-Z][A-Z0-9_]*)\s*,\s*"([^"\\]*)"\s*,\s*"([^"\\]*)"\s*\)')
EXIT_FIELDS = ("code", "name", "meaning")


class Reject(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def reject(code: str, message: str) -> None:
    raise Reject(code, message)


def read_at(repo: pathlib.Path, rev: str, path: str) -> bytes:
    done = subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{path}"], capture_output=True, check=False)
    if done.returncode != 0:
        reject("section-missing", f"{path} is not present at {rev}")
    if len(done.stdout) > MAX_BYTES:
        reject("section-missing", f"{path} exceeds {MAX_BYTES} bytes")
    return done.stdout


def parse_canonical(raw: bytes) -> dict:
    def pairs(items):
        seen: dict = {}
        for key, value in items:
            if key in seen:
                reject("non-canonical", f"{CONTRACT} repeats the key {key!r}")
            seen[key] = value
        return seen

    try:
        text = raw.decode("ascii")
        document = json.loads(text, object_pairs_hook=pairs)
    except (UnicodeDecodeError, ValueError) as error:
        reject("non-canonical", f"{CONTRACT} is not ASCII JSON: {error}")
    if json.dumps(document, indent=2, ensure_ascii=True) + "\n" != text:
        reject("non-canonical", f"{CONTRACT} is not in canonical form (indent=2, ensure_ascii, key order kept, one final newline)")
    if not isinstance(document, dict):
        reject("section-missing", f"{CONTRACT} is not a JSON object")
    return document


def require_keys(found, expected: tuple[str, ...], what: str) -> None:
    """Exactly the expected keys in the written order. The same keys in another order are a re-sorted copy of the
    hand-written file: non-canonical, never silently accepted."""
    keys = tuple(found.keys())
    if keys == expected:
        return
    if sorted(keys) == sorted(expected):
        reject("non-canonical", f"{what} keys are {list(keys)}; the written order is {list(expected)} (never re-sorted)")
    reject("section-missing", f"{what} keys are {list(keys)}, expected exactly {list(expected)}")


def exit_table(header: str) -> list[tuple[int, str, str]]:
    """The GBB_HOST_EXIT_TABLE rows of host_exit.h as (code, name, meaning)."""
    lines = header.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith("#define GBB_HOST_EXIT_TABLE(X)")), None)
    if start is None:
        reject("exit-table-drift", f"{EXIT_HEADER} defines no GBB_HOST_EXIT_TABLE")
    body = []
    for line in lines[start:]:
        body.append(line)
        if not line.rstrip().endswith("\\"):
            break
    rows = [(int(code), name, meaning) for code, _ident, name, meaning in EXIT_ROW.findall("\n".join(body))]
    if not rows:
        reject("exit-table-drift", f"{EXIT_HEADER} has no parsable X(code, IDENT, \"name\", \"meaning\") rows")
    return rows


def cadence_constants(header: str) -> dict[str, int]:
    values = {}
    for name in set(CADENCE_CONSTANTS.values()):
        found = re.findall(rf"^#define\s+{name}\s+UINT64_C\(([0-9]+)\)\s*(?:/\*.*)?$", header, re.M)
        if len(found) != 1:
            reject("cadence-drift", f"{HOST_HEADER} must define {name} exactly once as UINT64_C(<n>)")
        values[name] = int(found[0])
    return values


def check(repo: pathlib.Path, rev: str) -> tuple[int, int]:
    document = parse_canonical(read_at(repo, rev, CONTRACT))
    require_keys(document, SECTIONS, "top-level")
    if document["rtc_wall_clock"] != "not-recorded":
        reject("section-missing", f"rtc_wall_clock must be \"not-recorded\", got {document['rtc_wall_clock']!r}")
    if not isinstance(document["save_formats"], dict):
        reject("section-missing", "save_formats must be an object")

    rows = document["exit_codes"]
    if not isinstance(rows, list) or not all(isinstance(row, dict) and tuple(row.keys()) == EXIT_FIELDS for row in rows):
        reject("exit-table-drift", f"exit_codes must be a list of objects with the fields {', '.join(EXIT_FIELDS)}")
    numbered = [(row["code"], row["name"], row["meaning"]) for row in rows if row["code"] is not None]
    crash = [row for row in rows if row["code"] is None]
    expected = exit_table(read_at(repo, rev, EXIT_HEADER).decode("utf-8", errors="strict"))
    if numbered != expected:
        reject("exit-table-drift", f"exit_codes rows {numbered} differ from GBB_HOST_EXIT_TABLE {expected}")
    if len(crash) != 1 or crash[0]["name"] != "crash" or rows[-1] is not crash[0]:
        reject("exit-table-drift", "exit_codes needs exactly one final row with code null and the name crash")

    cadence = document["cadence"]
    if not isinstance(cadence, dict):
        reject("section-missing", "cadence must be an object")
    require_keys(cadence, CADENCE_KEYS, "cadence")
    constants = cadence_constants(read_at(repo, rev, HOST_HEADER).decode("utf-8", errors="strict"))
    for key in CADENCE_KEYS:
        value = cadence[key]
        wanted = constants[CADENCE_CONSTANTS[key]]
        if isinstance(value, bool) or not isinstance(value, int) or value != wanted:
            reject("cadence-drift", f"cadence.{key} is {value!r}, {CADENCE_CONSTANTS[key]} is {wanted}")
    return len(rows), len(cadence)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="canonical JSON, exit table and cadence")
    parser.add_argument("--rev", help="the commit to read the contract and C sources from")
    parser.add_argument("--repo", type=pathlib.Path, default=ROOT, help="the repository root")
    args = parser.parse_args()
    try:
        if args.rev is None:
            reject("usage", "--rev is required")
        exit_rows, cadence_keys = check(args.repo, args.rev)
        print(f"host-contract pass exit_codes={exit_rows} cadence={cadence_keys}")
        return 0
    except Reject as error:
        print(f"REJECT {error.code}: {error.message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
