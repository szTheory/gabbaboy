#!/usr/bin/env python3
"""No emulator-interoperability claim in the published text (Phase 18 plan 09, D-19).

    python3 -I verify-no-interop-claims.py --rev SHA --repo ROOT

GabbaBoy's raw save images are its own format (docs/host-contract.json). Six files must therefore contain no line
that matches the case-insensitive pattern `(byte-identical|compatible|interoperab)[^.\\n]*mGBA`, applied one line
at a time so a match never spans lines: README.md, docs/native-integration.md, docs/cartridge-and-saves.md,
docs/support/unreleased.md, docs/host-contract.json and .planning/research/v0.3/PLAYSTEAD-CONTRACT.md.

The scan carries its own negative control: a copy of the Playstead note with its pre-correction sentence appended
(`Non-RTC SRAM is byte-identical to mGBA and can be documented as such.`) must be rejected by the same function in
the same run, so a scan that can no longer see a claim fails instead of passing quietly. Power-loss wording is not
pattern-scanned; the native guide's positive `no power-loss guarantee` phrase is pinned by a phrase contract.

The files are read with `git show REV:<path>` (never the working tree), so a check sees the point-in-time facts of
one commit. Prints `no-interop-claims pass files=6 controls=1`; every failure is `REJECT <code>: <message>` on
stderr with exit 1.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

if not __debug__:
    raise SystemExit("verify-no-interop-claims refuses to run under python -O (its checks must stay on)")

ROOT = pathlib.Path(__file__).resolve().parents[2]
MAX_BYTES = 8 * 1024 * 1024
NOTE = ".planning/research/v0.3/PLAYSTEAD-CONTRACT.md"
FILES = ("README.md", "docs/native-integration.md", "docs/cartridge-and-saves.md", "docs/support/unreleased.md",
         "docs/host-contract.json", NOTE)
PATTERN = re.compile(r"(byte-identical|compatible|interoperab)[^.\n]*mGBA", re.IGNORECASE)
# The sentence the note carried before the D-19 correction; the seeded control re-appends it.
ORIGINAL = "Non-RTC SRAM is byte-identical to mGBA and can be documented as such."


class Reject(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def read_at(repo: pathlib.Path, rev: str, path: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{path}"], capture_output=True, check=False)
    if done.returncode != 0:
        raise Reject("file-missing", f"{path} is not present at {rev}")
    if len(done.stdout) > MAX_BYTES:
        raise Reject("file-missing", f"{path} exceeds {MAX_BYTES} bytes")
    return done.stdout.decode("utf-8", errors="strict")


def scan(label: str, text: str) -> None:
    for number, line in enumerate(text.splitlines(), start=1):  # one line at a time
        if PATTERN.search(line):
            raise Reject("interop-claim", f"{label} line {number} makes an emulator interoperability claim")


def check(repo: pathlib.Path, rev: str) -> int:
    texts = {path: read_at(repo, rev, path) for path in FILES}
    for path in FILES:
        scan(path, texts[path])
    seeded = texts[NOTE].rstrip("\n") + "\n" + ORIGINAL + "\n"
    try:
        scan("the seeded copy", seeded)
    except Reject:
        return len(FILES)
    raise Reject("control-accepted",
                 "the seeded copy holding the original Playstead sentence was accepted; the scan has lost its teeth")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rev", required=True, help="the commit to read the files from")
    parser.add_argument("--repo", type=pathlib.Path, default=ROOT, help="the repository root")
    args = parser.parse_args()
    try:
        files = check(args.repo, args.rev)
    except Reject as error:
        print(f"REJECT {error.code}: {error.message}", file=sys.stderr)
        return 1
    print(f"no-interop-claims pass files={files} controls=1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
