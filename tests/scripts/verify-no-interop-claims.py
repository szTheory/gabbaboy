#!/usr/bin/env python3
"""No emulator-interoperability claim in the published text (Phase 18 plan 09, D-19).

    python3 -I verify-no-interop-claims.py --rev SHA --repo ROOT

GabbaBoy's raw save images are its own format (docs/host-contract.json). Six base files must therefore contain no
sentence that pairs `byte-identical`, `compatible` or `interoperab...` with `mGBA`, `SameBoy`, `BGB` or `BESS`, in either order, within 80
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
one full commit id. When present at that revision, the v0.3 ledger is scanned too; a scratch immutable commit proves
that conditional path. Prints the measured file and control counts; every failure is `REJECT <code>: <message>` on
stderr with exit 1.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys
import tempfile

if not __debug__:
    raise SystemExit("verify-no-interop-claims refuses to run under python -O (its checks must stay on)")

ROOT = pathlib.Path(__file__).resolve().parents[2]
MAX_BYTES = 8 * 1024 * 1024
NOTE = ".planning/research/v0.3/PLAYSTEAD-CONTRACT.md"
FILES = ("README.md", "docs/native-integration.md", "docs/cartridge-and-saves.md", "docs/support/unreleased.md",
         "docs/host-contract.json", NOTE)
V03_LEDGER = "docs/support/v0.3.0.md"
REVISION = re.compile(r"[0-9a-f]{40}\Z")
# A claim pairs one of the keywords with mGBA, in either order, within 80 characters of the whitespace-collapsed text.
PATTERN = re.compile(
    r"(?:byte-identical|compatible|interoperab)[^\n]{0,80}(?:mGBA|SameBoy|BGB|BESS)|"
    r"(?:mGBA|SameBoy|BGB|BESS)[^\n]{0,80}(?:byte-identical|compatible|interoperab)",
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
    ("a claim naming SameBoy", "Raw saves are byte-identical to SameBoy."),
    ("a claim naming BGB", "BGB saves are compatible with GabbaBoy."),
    ("a claim naming BESS", "GabbaBoy raw images are interoperable with BESS."),
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


def check(repo: pathlib.Path, rev: str, *, probe_optional_ledger: bool = True) -> tuple[int, int]:
    if REVISION.fullmatch(rev) is None:
        raise Reject("revision-invalid", "--rev must be a full 40-character commit id")
    verify = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{rev}^{{commit}}"],
                            capture_output=True, check=False)
    if verify.returncode != 0:
        raise Reject("revision-invalid", f"{rev} is not an available commit")
    paths = list(FILES)
    ledger = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{rev}:{V03_LEDGER}"],
                            capture_output=True, check=False)
    if ledger.returncode == 0:
        paths.append(V03_LEDGER)
    texts = {path: read_at(repo, rev, path) for path in paths}
    for path in paths:
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
    controls = len(REJECTED_CONTROLS) + 1
    if probe_optional_ledger:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-interop-ledger-") as temp:
            scratch = pathlib.Path(temp)
            for relative, text in texts.items():
                target = scratch / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")
            ledger_path = scratch / V03_LEDGER
            ledger_path.parent.mkdir(parents=True, exist_ok=True)
            ledger_path.write_text(
                "# v0.3 support ledger\n\nA seeded claim says raw saves are byte-identical to SameBoy.\n",
                encoding="utf-8")
            initialized = subprocess.run(["git", "-C", temp, "init", "--quiet"],
                                         capture_output=True, check=False)
            if initialized.returncode != 0:
                raise Reject("optional-ledger-control-error", "could not initialize the fixture repo")
            added = subprocess.run(["git", "-C", temp, "add", *[str(path.relative_to(scratch))
                                                                      for path in scratch.rglob("*")
                                                                      if path.is_file()]],
                                   capture_output=True, check=False)
            if added.returncode != 0:
                raise Reject("optional-ledger-control-error", "could not stage the fixture repo")
            committed = subprocess.run(
                ["git", "-C", temp, "-c", "user.name=GabbaBoy Test", "-c",
                 "user.email=test@example.invalid", "commit", "--quiet", "-m", "optional ledger control"],
                capture_output=True, check=False)
            if committed.returncode != 0:
                raise Reject("optional-ledger-control-error", "could not commit the fixture repo")
            scratch_rev = subprocess.run(["git", "-C", temp, "rev-parse", "HEAD"],
                                         capture_output=True, check=False, text=True).stdout.strip()
            try:
                check(scratch, scratch_rev, probe_optional_ledger=False)
            except Reject as error:
                if error.code != "interop-claim" or V03_LEDGER not in error.message:
                    raise Reject("optional-ledger-control-error",
                                 f"v0.3 ledger control failed for the wrong reason: {error.message}") from error
            else:
                raise Reject("control-accepted", "the seeded v0.3 ledger interop claim was accepted")
        controls += 1
    return len(paths), controls


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rev", required=True, help="the commit to read the files from")
    parser.add_argument("--repo", type=pathlib.Path, default=ROOT, help="the repository root")
    args = parser.parse_args()
    try:
        files, controls = check(args.repo, args.rev)
    except Reject as error:
        print(f"REJECT {error.code}: {error.message}", file=sys.stderr)
        return 1
    print(f"no-interop-claims pass files={files} controls={controls}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
