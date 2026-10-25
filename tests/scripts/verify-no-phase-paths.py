#!/usr/bin/env python3
"""TUNE-01 phase-path lint: tracked tests, scripts, docs and workflows never read the live phases directory.

Contract (Phase 16 D-06, D-07):

* Every git-tracked text file outside .planning/ is scanned. Binary files (a NUL byte in the first
  8 KiB, the same rule as grep -I) are out of scope, and so is a bare "phases/" that lacks the
  .planning parent; both edges are recorded here because the edge probe left them unclassified.
* Four spellings of the live phases directory are rejected: the literal, joined segments (a quoted
  ".planning" followed by a quoted "phases" through a comma, a division or a plus), backslash
  separators, and the ${PROJECT_SOURCE_DIR}-prefixed form. The accepted spelling names a completed
  milestone archive: .planning/milestones/v<N>.<M>-phases/.
* Exceptions live in one count-pinned allowlist of (file, max hits, reason). A file with more hits than
  its pin fails, and a row whose observed hits fall below its pin is stale and fails, so a retargeted
  reader cannot leave a loose exception behind.
* The success line prints files=N exactly once. The CTest pins a floor on N, and a fixed list of
  must-scan files proves the walk reached the files that matter.

The lint must spell the forbidden forms in its own patterns and fixtures; its own row in the
allowlist is a measured count, not an obfuscation.
"""
from __future__ import annotations

import argparse
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

if not __debug__ or sys.flags.optimize:
    raise SystemExit("verify-no-phase-paths must not run with python -O")

ROOT = Path(__file__).resolve().parents[2]

# (file, max hits, reason). Counts are measured on the tree with --check --report and pinned exactly.
ALLOWLIST = (
    ("tests/CMakeLists.txt", 1,
     "GBB_LIVE_PHASES_DIR definition, the single allowlisted spelling of the live phases directory (D-07)"),
    ("tests/scripts/verify-phase8-closure-contract.py", 1,
     "PHASE constant: Phase 8 boundary-commit reads, a point-in-time git show path (D-06)"),
    ("tests/scripts/verify-closeout-scan.py", 5,
     "temp-fixture layout strings built inside a throwaway repository, not reads of the live tree"),
    ("tests/scripts/verify-no-phase-paths.py", 0,
     "the lint's own spelling patterns and self-test fixture text"),
)

# Files the walk must reach, or the scan is vacuous.
MUST_SCAN = (
    "tests/CMakeLists.txt",
    "tests/scripts/verify-summary-coverage.py",
    "tests/scripts/verify-closeout-dispositions.py",
)

# One alternation so each spot is counted once. The prefixed form is tried first.
SPELLINGS = re.compile(
    r"(?P<prefixed>\$\{PROJECT_SOURCE_DIR\}/\.planning/phases(?![\w-]))"
    r"|(?P<literal>\.planning/phases(?![\w-]))"
    r"|(?P<backslash>\.planning\\+phases(?![\w-]))"
    r"|(?P<joined>[\"']\.planning/?[\"']\)?\s*(?:,|/|\+)\s*[\"']phases[\"'])"
)
SNIFF_BYTES = 8192


class LintError(Exception):
    pass


def need(condition: bool, message: str) -> None:
    if not condition:
        raise LintError(message)


def tracked_files(root: Path) -> list[str]:
    result = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], check=False, capture_output=True)
    need(result.returncode == 0, "REJECT git-ls-files: %s" % result.stderr.decode("utf-8", "replace").strip())
    return sorted(name for name in result.stdout.decode("utf-8", "surrogateescape").split("\0") if name)


def read_text(root: Path, name: str) -> str | None:
    path = root / name
    try:
        info = os.lstat(path)
    except OSError:
        return None
    if not stat.S_ISREG(info.st_mode):
        return None
    data = path.read_bytes()
    if b"\0" in data[:SNIFF_BYTES]:
        return None
    return data.decode("utf-8", "replace")


def scan(root: Path) -> tuple[int, dict[str, list[tuple[int, str]]], set[str]]:
    scanned: set[str] = set()
    hits: dict[str, list[tuple[int, str]]] = {}
    for name in tracked_files(root):
        if name == ".planning" or name.startswith(".planning/"):
            continue
        text = read_text(root, name)
        if text is None:
            continue
        scanned.add(name)
        for match in SPELLINGS.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            hits.setdefault(name, []).append((line, match.lastgroup or "?"))
    return len(scanned), hits, scanned


def check(root: Path, allowlist=ALLOWLIST, must_scan=MUST_SCAN, report: bool = False) -> tuple[int, int]:
    files, hits, scanned = scan(root)
    for name in must_scan:
        need(name in scanned, "REJECT must-scan-missing: %s was not scanned" % name)
    pins: dict[str, int] = {}
    for name, maximum, reason in allowlist:
        need(bool(reason.strip()), "REJECT allowlist-reason: %s has no reason" % name)
        need(name not in pins, "REJECT allowlist-duplicate: %s appears twice" % name)
        pins[name] = maximum
    for name in sorted(hits):
        found = hits[name]
        if report:
            print("hits %s %d" % (name, len(found)), file=sys.stderr)
        if name not in pins:
            raise LintError("REJECT phase-path: %s:%d %s spelling of the live phases directory"
                            % (name, found[0][0], found[0][1]))
        if len(found) > pins[name]:
            raise LintError("REJECT over-max: %s has %d hits, allowlist pins %d (first excess at line %d)"
                            % (name, len(found), pins[name], found[pins[name]][0]))
    for name, maximum in sorted(pins.items()):
        observed = len(hits.get(name, []))
        need(observed == maximum, "REJECT stale-allowlist: %s has %d hits, allowlist pins %d" % (name, observed, maximum))
    return files, len(pins)


def run_check(args) -> int:
    files, allowlisted = check(ROOT, report=args.report)
    print("no-phase-paths pass files=%d allowlisted=%d" % (files, allowlisted))
    return 0


# ---- self-test -----------------------------------------------------------------------------------

CLEAN_FILES = {
    "tests/CMakeLists.txt": "set(GBB_V02 ${PROJECT_SOURCE_DIR}/.planning/milestones/v0.2-phases)\n",
    "tests/scripts/reader.py": "ARCHIVE = '.planning/milestones/v0.2-phases/GB-15'\n",
    "cmake/module.cmake": "message(STATUS read)\n",
    ".github/workflows/ci.yml": "name: ci\n",
    "docs/evidence.md": "See [v0.1](../.planning/milestones/v0.1-phases/GB-01/x.md) and a bare phases/ note.\n",
    "README.md": "# fixture\n",
    ".planning/phases/GB-16/note.md": "planning files may name their own directory: .planning/phases\n",
}
BINARY_BODY = b"\0\x01 .planning/phases hidden in a binary\n"


def make_fixture(root: Path, files: dict[str, str], binary: bool = True) -> None:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    if binary:
        blob = root / "tests" / "data" / "blob.bin"
        blob.parent.mkdir(parents=True, exist_ok=True)
        blob.write_bytes(BINARY_BODY)
    for command in (["init", "-q"], ["add", "-A", "-f"]):
        done = subprocess.run(["git", "-C", str(root)] + command, check=False, capture_output=True)
        need(done.returncode == 0, "fixture git %s failed" % command[0])


def expect_rejected(label: str, prefix: str, files: dict[str, str], allowlist=(), must_scan=()) -> None:
    with tempfile.TemporaryDirectory(prefix="gbb-no-phase-paths-") as name:
        root = Path(name)
        make_fixture(root, files)
        try:
            check(root, allowlist=allowlist, must_scan=must_scan)
        except LintError as error:
            need(str(error).startswith(prefix), "%s: rejected with %r, wanted %s" % (label, str(error), prefix))
            return
        raise LintError("%s: accepted a violation" % label)


def expect_accepted(label: str, files: dict[str, str], allowlist=(), must_scan=()) -> None:
    with tempfile.TemporaryDirectory(prefix="gbb-no-phase-paths-") as name:
        root = Path(name)
        make_fixture(root, files)
        try:
            check(root, allowlist=allowlist, must_scan=must_scan)
        except LintError as error:
            raise LintError("%s: rejected a clean tree: %s" % (label, error))


def mutated(files: dict[str, str], name: str, old: str, new: str) -> dict[str, str]:
    changed = dict(files)
    original = changed[name]
    changed[name] = original.replace(old, new)
    need(changed[name] != original, "%s: inactive mutation" % name)
    return changed


def self_test() -> int:
    controls = 0
    expect_accepted("clean tree", CLEAN_FILES)
    controls += 1
    # A real accepted milestone link, the bare directory name and a binary body all pass.
    need(".planning/milestones/v0.1-phases" in CLEAN_FILES["docs/evidence.md"], "fixture lost its v0.1 link")
    need(b".planning/phases" in BINARY_BODY, "binary fixture lost its hidden path")
    expect_accepted("milestone link, bare phases/ and binary skipped", CLEAN_FILES)
    controls += 1

    spellings = (
        ("literal", "OLD = '.planning/phases/GB-07'\n"),
        ("joined os.path.join", "OLD = os.path.join('.planning', 'phases', 'GB-07')\n"),
        ("joined Path division", "OLD = Path('.planning') / 'phases' / 'GB-07'\n"),
        ("backslash", "OLD = '.planning\\\\phases\\\\GB-07'\n"),
        ("prefixed", "set(X \"${PROJECT_SOURCE_DIR}/.planning/phases/GB-07\")\n"),
    )
    for label, body in spellings:
        files = mutated(CLEAN_FILES, "tests/scripts/reader.py", "ARCHIVE = '.planning/milestones/v0.2-phases/GB-15'\n", body)
        expect_rejected("spelling " + label, "REJECT phase-path", files)
        controls += 1

    leak = "OLD = '.planning/phases/GB-07'\n"
    for name in ("tests/scripts/reader.py", "cmake/module.cmake", ".github/workflows/ci.yml", "docs/evidence.md", "README.md"):
        changed = dict(CLEAN_FILES)
        original = changed[name]
        changed[name] = original + leak
        need(changed[name] != original, name + ": inactive mutation")
        expect_rejected("scope root " + name, "REJECT phase-path", changed)
        controls += 1

    # Allowlist behavior: an exact pin passes, over-max and stale rows fail, and reasons are mandatory.
    pinned = dict(CLEAN_FILES)
    pinned["tests/scripts/reader.py"] = CLEAN_FILES["tests/scripts/reader.py"] + leak
    expect_accepted("exact pin", pinned, allowlist=(("tests/scripts/reader.py", 1, "fixture"),))
    controls += 1
    expect_rejected("over-max row", "REJECT over-max", pinned,
                    allowlist=(("tests/scripts/reader.py", 0, "fixture"),))
    controls += 1
    expect_rejected("stale row", "REJECT stale-allowlist", CLEAN_FILES,
                    allowlist=(("tests/scripts/reader.py", 1, "fixture"),))
    controls += 1
    expect_rejected("row without reason", "REJECT allowlist-reason", pinned,
                    allowlist=(("tests/scripts/reader.py", 1, " "),))
    controls += 1
    expect_rejected("must-scan file absent", "REJECT must-scan-missing", CLEAN_FILES,
                    must_scan=("tests/scripts/does-not-exist.py",))
    controls += 1
    print("no-phase-paths self-test pass controls=%d" % controls)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="scan the tracked tree")
    mode.add_argument("--self-test", action="store_true", help="run the negative controls")
    parser.add_argument("--report", action="store_true", help="print per-file hit counts to stderr")
    args = parser.parse_args()
    try:
        return self_test() if args.self_test else run_check(args)
    except LintError as error:
        print(str(error) if str(error).startswith("REJECT") else "REJECT lint: %s" % error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
