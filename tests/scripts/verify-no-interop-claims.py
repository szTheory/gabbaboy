#!/usr/bin/env python3
"""No emulator-interoperability claim in the published text (Phase 18 plan 09, D-19).

    python3 -I verify-no-interop-claims.py --rev SHA --repo ROOT

GabbaBoy's raw save images are its own format (docs/host-contract.json). Six files must therefore contain no
sentence that pairs `byte-identical`, `compatible` or `interoperab...` with `mGBA`, in either order, within 80
characters. Each file is scanned with its whitespace collapsed to single spaces, so a claim hard-wrapped across lines
or split by a `.sav` token still counts; a match is made case-insensitively. Five explicit disclaimer phrases
(`no save interoperability with`, `no byte interoperability with`, `not byte-identical to`, `not compatible with`,
`not interoperable with`) are removed before the scan, so honest wording is not pushed towards evasive wording; any
other negation ("not only compatible with mGBA") is still a claim.

The scan carries its own controls, run through the same function in the same run: the pre-correction Playstead
sentence appended to the note (`Non-RTC SRAM is byte-identical to mGBA and can be documented as such.`), a claim
wrapped across lines, a claim with a `.sav` token before mGBA, a claim with mGBA first and a claim that only
negates part of the sentence must each be rejected, and the allowed disclaimers must be accepted, so a scan that
has lost its teeth or has become over-eager fails instead of passing quietly. Power-loss wording is not
pattern-scanned; the native guide's positive `no power-loss guarantee` phrase is pinned by a phrase contract.

The files are read with `git show REV:<path>` (never the working tree), so a check sees the point-in-time facts of
one commit. Prints `no-interop-claims pass files=6 controls=6`; every failure is `REJECT <code>: <message>` on
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
# A claim pairs one of the keywords with mGBA, in either order, within 80 characters of the whitespace-collapsed text.
PATTERN = re.compile(
    r"(?:byte-identical|compatible|interoperab)[^\n]{0,80}mGBA|mGBA[^\n]{0,80}(?:byte-identical|compatible|interoperab)",
    re.IGNORECASE)
# Honest disclaimers, removed before the scan. Nothing broader than these exact phrases is exempt.
DISCLAIMERS = re.compile(
    r"no (?:save|byte) interoperability with|not byte-identical to|not compatible with|not interoperable with",
    re.IGNORECASE)
# The sentence the note carried before the D-19 correction; the seeded control re-appends it.
ORIGINAL = "Non-RTC SRAM is byte-identical to mGBA and can be documented as such."
# Claims the scan has to see however they are written, and disclaimers it has to let through.
REJECTED_CONTROLS = (
    ("the original sentence", ORIGINAL),
    ("a hard-wrapped claim", "Non-RTC SRAM is compatible\nwith mGBA and can be documented as such."),
    ("a claim past a .sav token", "The raw save is compatible with the .sav format of mGBA."),
    ("a claim with mGBA first", "Saves written by mGBA are interoperable with GabbaBoy."),
    ("a partly negated claim", "Raw saves are not only compatible with mGBA, they are byte-identical to it."),
)
ACCEPTED_CONTROL = (
    "GabbaBoy saves are not compatible with mGBA. There is no save interoperability with mGBA, and a raw image is\n"
    "not byte-identical to mGBA output; they are not interoperable with it either."
)


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
    flat = DISCLAIMERS.sub(" ", re.sub(r"\s+", " ", text))
    found = PATTERN.search(flat)
    if found is not None:
        context = flat[max(0, found.start() - 20):found.end() + 20]
        raise Reject("interop-claim", f"{label} makes an emulator interoperability claim near: {context!r}")


def check(repo: pathlib.Path, rev: str) -> int:
    texts = {path: read_at(repo, rev, path) for path in FILES}
    for path in FILES:
        scan(path, texts[path])
    for label, sentence in REJECTED_CONTROLS:
        try:
            scan(f"the seeded {label}", texts[NOTE].rstrip("\n") + "\n" + sentence + "\n")
        except Reject:
            continue
        raise Reject("control-accepted", f"the seeded {label} was accepted; the scan has lost its teeth")
    try:
        scan("the seeded disclaimers", texts[NOTE].rstrip("\n") + "\n" + ACCEPTED_CONTROL + "\n")
    except Reject as error:
        raise Reject("control-rejected", f"the allowed disclaimers were rejected: {error.message}") from error
    return len(FILES)


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
    print(f"no-interop-claims pass files={files} controls={len(REJECTED_CONTROLS) + 1}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
