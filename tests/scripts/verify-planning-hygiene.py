#!/usr/bin/env python3
"""Planning hygiene checks for GabbaBoy (Phase 16 plan 16-05, TUNE-05; D-24..D-27).

Four checks, each a pure function over text or a directory that returns (summary, errors) with stable
error-code prefixes, so a control can pin the failure class instead of "some error":

  --check plan-cap --roadmap PATH --phases-dir DIR
      Every "### Phase N:" heading under "## Phase Details" needs one "**Plan cap**: N" line. The number of
      NN-NN-PLAN.md files in the matching GB-N-* directory must not exceed it (a decimal phase counts against
      its parent unless it has its own heading and cap line; gap plans count), a cap above 12 fails, and the
      caps must sum to at most 40 (D-24, D-102). The phases directory is an argument: no default path.
      Prints "plan-cap pass phases=N plans=M".
  --check lessons-ids --lessons PATH
      "### ID / ..." is the only lesson heading form and ids compare as exact tokens; an id may appear once.
      A duplicate report names every occurrence's line and keeps the earliest (D-25).
      Prints "lessons-ids pass ids=N".
  --check state-size --state PATH
      STATE.md stays within STATE_MAX_BYTES raw bytes and STATE_MAX_LINES newline characters (D-26).
      Prints "state-size pass bytes=N lines=M".
  --check playstead-docs --root DIR
      Added by the Playstead docs task of the same plan.

  --self-test   runs every rule against generated and committed fixtures and prints
                "planning-hygiene self-test pass controls=N" once.

STATE bound measurement (git history of .planning/STATE.md, bytes / newline count):
  end of Phase 14 (c771b1b)      60,812 / 536
  end of Phase 15 (04fe3c6)      65,092 / 569   (+4,280 / +33)
  end of Phase 15.1 (5356d38)    90,052 / 675   (+24,960 / +106)
  Phases 15 and 15.1 together grew the file by 29,240 bytes and 139 lines, 14.6 KB and 70 lines per phase on
  average, and 15.1 alone is the outlier that put the file at 76 KB. After the Phase 16 trim the live file is
  about 5 KB and 90 lines, so STATE_MAX_BYTES = 40,960 (40 KiB) and STATE_MAX_LINES = 250 leave about 35 KB and
  160 lines of room: roughly one v0.3 milestone at the Phase 15 growth rate (four phases at about 4.3 KB each),
  and a trip wire two phases in at the Phase 15.1 rate. Raising the bound needs a decision, not an edit.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import re
import sys
import tempfile
from pathlib import Path

if not __debug__ or sys.flags.optimize:
    raise SystemExit("verify-planning-hygiene must not run with python -O")

STATE_MAX_BYTES = 40960
STATE_MAX_LINES = 250
PLAN_CAP_MAX = 12
PLAN_CAP_SUM_MAX = 40

PHASE_HEADING = re.compile(r"^### Phase (\d+(?:\.\d+)?):")
CAP_LINE = re.compile(r"^\*\*Plan cap\*\*: (\d+)\s*$")
PLAN_FILE = re.compile(r"^(\d+(?:\.\d+)?)-\d+-PLAN\.md$")
PHASE_DIR = re.compile(r"^GB-(\d+(?:\.\d+)?)-")
LESSON_HEADING = re.compile(r"^### ([A-Z0-9]+(?:-[A-Z0-9]+)+) / ")

DATA = Path(__file__).resolve().parents[1] / "data" / "planning-hygiene"


def phase_details(roadmap: str) -> list[str] | None:
    """The lines of the '## Phase Details' section, or None when it is absent."""
    lines = roadmap.splitlines()
    for start, line in enumerate(lines):
        if line.strip() == "## Phase Details":
            end = len(lines)
            for stop in range(start + 1, len(lines)):
                if lines[stop].startswith("## "):
                    end = stop
                    break
            return lines[start + 1:end]
    return None


def check_plan_cap(roadmap: str, phases_dir: Path) -> tuple[str, list[str]]:
    errors: list[str] = []
    section = phase_details(roadmap)
    if section is None:
        return "", ["plan-cap-vacuous: ROADMAP has no '## Phase Details' section"]
    caps: dict[str, int | None] = {}
    current: str | None = None
    for line in section:
        heading = PHASE_HEADING.match(line)
        if heading:
            current = heading.group(1)
            if current in caps:
                errors.append(f"plan-cap-duplicate-phase: Phase {current} has two headings")
            caps[current] = None
            continue
        if line.startswith("### "):
            current = None
            continue
        cap = CAP_LINE.match(line)
        if cap and current is not None:
            if caps[current] is not None:
                errors.append(f"plan-cap-duplicate-cap: Phase {current} has two Plan cap lines")
            caps[current] = int(cap.group(1))
    if not caps:
        return "", ["plan-cap-vacuous: ROADMAP lists no active phase headings"]
    for number, cap in caps.items():
        if cap is None:
            errors.append(f"plan-cap-missing: Phase {number} has no '**Plan cap**: N' line")
        elif cap > PLAN_CAP_MAX:
            errors.append(f"plan-cap-too-large: Phase {number} cap {cap} is above {PLAN_CAP_MAX}")
    total = sum(cap for cap in caps.values() if cap is not None)
    if total > PLAN_CAP_SUM_MAX:
        errors.append(f"plan-cap-sum: caps sum to {total}, above {PLAN_CAP_SUM_MAX}")

    counts = {number: 0 for number in caps}
    if phases_dir.is_dir():
        for directory in sorted(p for p in phases_dir.iterdir() if p.is_dir()):
            match = PHASE_DIR.match(directory.name)
            if not match:
                continue
            number = match.group(1)
            owner = number if number in caps else number.split(".")[0]
            if owner not in caps:
                errors.append(f"plan-cap-orphan-dir: {directory.name} matches no phase heading")
                continue
            counts[owner] += sum(1 for f in directory.iterdir() if f.is_file() and PLAN_FILE.match(f.name))
    else:
        errors.append(f"plan-cap-phases-dir: not a directory: {phases_dir}")
    for number, cap in caps.items():
        if cap is not None and counts[number] > cap:
            errors.append(f"plan-cap-exceeded: Phase {number} has {counts[number]} plans, cap is {cap}")
    return f"plan-cap pass phases={len(caps)} plans={sum(counts.values())}", errors


def check_lessons_ids(text: str) -> tuple[str, list[str]]:
    seen: dict[str, list[int]] = {}
    for number, line in enumerate(text.splitlines(), start=1):
        match = LESSON_HEADING.match(line)
        if match:
            seen.setdefault(match.group(1), []).append(number)
    if not seen:
        return "", ["lessons-vacuous: LESSONS has no '### ID /' heading"]
    errors = []
    for lesson_id in sorted(seen):
        lines = sorted(seen[lesson_id])
        if len(lines) > 1:
            where = ", ".join(str(n) for n in lines)
            errors.append(f"lessons-duplicate-id: {lesson_id} at lines {where}; keep line {lines[0]}")
    return f"lessons-ids pass ids={len(seen)}", errors


def check_state_size(data: bytes, max_bytes: int = STATE_MAX_BYTES, max_lines: int = STATE_MAX_LINES) -> tuple[str, list[str]]:
    size = len(data)
    lines = data.count(b"\n")
    errors = []
    if size > max_bytes:
        errors.append(f"state-size-bytes: {size} bytes is above {max_bytes}")
    if lines > max_lines:
        errors.append(f"state-size-lines: {lines} lines is above {max_lines}")
    return f"state-size pass bytes={size} lines={lines}", errors


def codes(errors: list[str]) -> set[str]:
    return {error.split(":", 1)[0] for error in errors}


# ---- self-test -------------------------------------------------------------------------------------------


def roadmap_text(caps: list[tuple[str, str | None]]) -> str:
    out = ["# Roadmap", "", "## Phase Details", ""]
    for number, cap in caps:
        out += [f"### Phase {number}: Name", "", "**Goal**: x"]
        if cap is not None:
            out.append(f"**Plan cap**: {cap}")
        out.append("")
    out += ["## Progress", "", "### Phase 99: not an active heading", "**Plan cap**: 99", ""]
    return "\n".join(out)


def make_phases(root: Path, counts: dict[str, int]) -> Path:
    phases = root / "phases"
    phases.mkdir()
    for name, count in counts.items():
        directory = phases / f"GB-{name}-some-title"
        directory.mkdir()
        for index in range(1, count + 1):
            (directory / f"{name}-{index:02d}-PLAN.md").write_text("", encoding="utf-8")
        (directory / f"{name}-SUMMARY-notes.md").write_text("", encoding="utf-8")
        (directory / f"{name}-01-SUMMARY.md").write_text("", encoding="utf-8")
    return phases


def self_test() -> int:
    controls = 0

    def expect(label: str, errors: list[str], code: str | None) -> None:
        nonlocal controls
        if code is None:
            if errors:
                raise SystemExit(f"planning-hygiene self-test FAIL: {label} should pass but gave {errors}")
        elif code not in codes(errors):
            raise SystemExit(f"planning-hygiene self-test FAIL: {label} did not report {code}: {errors}")
        controls += 1

    with tempfile.TemporaryDirectory(prefix="gbb-hygiene.") as scratch:
        base = Path(scratch)

        def phases(name: str, counts: dict[str, int]) -> Path:
            root = base / name
            root.mkdir()
            return make_phases(root, counts)

        # plan-cap: boundary, cap line, cap size, cap sum, zero, vacuous.
        ok_map = [("16", "8"), ("17", "12"), ("18", "10"), ("19", "8")]
        summary, errors = check_plan_cap(roadmap_text(ok_map), phases("ok", {"16": 8, "17": 0}))
        expect("plan count equal to the cap passes", errors, None)
        if summary != "plan-cap pass phases=4 plans=8":
            raise SystemExit(f"planning-hygiene self-test FAIL: unexpected pass line {summary!r}")
        _, errors = check_plan_cap(roadmap_text(ok_map), phases("over", {"16": 9}))
        expect("cap+1 plans fails", errors, "plan-cap-exceeded")
        _, errors = check_plan_cap(roadmap_text([("16", "8"), ("17", None)]), phases("nocap", {"16": 1}))
        expect("a phase without a cap line fails", errors, "plan-cap-missing")
        _, errors = check_plan_cap(roadmap_text([("16", "12")]), phases("c12", {"16": 12}))
        expect("cap 12 passes", errors, None)
        _, errors = check_plan_cap(roadmap_text([("16", "13")]), phases("c13", {"16": 1}))
        expect("cap 13 fails", errors, "plan-cap-too-large")
        _, errors = check_plan_cap(roadmap_text([("16", "10"), ("17", "10"), ("18", "10"), ("19", "10")]),
                                   phases("sum40", {}))
        expect("a cap sum of 40 passes", errors, None)
        _, errors = check_plan_cap(roadmap_text([("16", "10"), ("17", "10"), ("18", "10"), ("19", "11")]),
                                   phases("sum41", {}))
        expect("a cap sum of 41 fails", errors, "plan-cap-sum")
        _, errors = check_plan_cap(roadmap_text([("16", "8")]), phases("zero", {}))
        expect("a phase with zero plans passes", errors, None)
        _, errors = check_plan_cap(roadmap_text([]), phases("none", {}))
        expect("a ROADMAP with no active phase heading is vacuous", errors, "plan-cap-vacuous")
        _, errors = check_plan_cap("# Roadmap\n\n## Progress\n", phases("nosection", {}))
        expect("a ROADMAP without Phase Details is vacuous", errors, "plan-cap-vacuous")
        _, errors = check_plan_cap(roadmap_text([("15", "4"), ("15.1", "3")]), phases("dec1", {"15": 2, "15.1": 3}))
        expect("a decimal phase with its own cap counts against itself", errors, None)
        _, errors = check_plan_cap(roadmap_text([("15", "4")]), phases("dec2", {"15": 2, "15.1": 3}))
        expect("a decimal phase without a cap counts against its parent", errors, "plan-cap-exceeded")
        _, errors = check_plan_cap(roadmap_text([("16", "8")]), phases("orphan", {"17": 1}))
        expect("a phase directory without a heading is an orphan", errors, "plan-cap-orphan-dir")
        _, errors = check_plan_cap(roadmap_text([("16", "3")]).replace("**Plan cap**: 3", "**Plan cap**: 3\n**Plan cap**: 4"),
                                   phases("dupcap", {"16": 1}))
        expect("two cap lines for one phase fail", errors, "plan-cap-duplicate-cap")
        _, errors = check_plan_cap(roadmap_text([("16", "8")]), base / "does-not-exist")
        expect("a missing phases directory fails", errors, "plan-cap-phases-dir")
        # The committed roadmap fixture reproduces the live shape: four capped phases and a stray later heading.
        fixture_roadmap = (DATA / "roadmap-over-cap.md").read_text(encoding="utf-8")
        _, errors = check_plan_cap(fixture_roadmap, phases("fixture", {"16": 4}))
        expect("the committed over-cap roadmap fixture is rejected", errors, "plan-cap-exceeded")

        # lessons-ids: exact tokens, every occurrence named, earliest kept, order independent.
        lessons = "### GB-TEST-001 / d / one\n\n### GB-TEST-0010 / d / ten\n\n### GB-TEST-002 / d / two\n"
        summary, errors = check_lessons_ids(lessons)
        expect("near-collision ids are distinct", errors, None)
        if summary != "lessons-ids pass ids=3":
            raise SystemExit(f"planning-hygiene self-test FAIL: unexpected lessons pass line {summary!r}")
        _, errors = check_lessons_ids(lessons + "text\n### GB-TEST-001 / d / again\n")
        expect("a duplicate id fails", errors, "lessons-duplicate-id")
        if not any("lines 1, 7" in e and "keep line 1" in e for e in errors):
            raise SystemExit(f"planning-hygiene self-test FAIL: duplicate report lacks lines and the kept line: {errors}")
        controls += 1
        lines = (lessons + "x\n### GB-TEST-001 / d / again\n### GB-TEST-001 / d / third\n").splitlines()
        _, forward = check_lessons_ids("\n".join(lines))
        _, reverse = check_lessons_ids("\n".join(reversed(lines)))
        if len(forward) != 1 or "keep line 1" not in forward[0] or "lines 1, 7, 8" not in forward[0]:
            raise SystemExit(f"planning-hygiene self-test FAIL: three-way duplicate report wrong: {forward}")
        if len(reverse) != 1 or "lessons-duplicate-id: GB-TEST-001" not in reverse[0]:
            raise SystemExit(f"planning-hygiene self-test FAIL: reversed duplicate report wrong: {reverse}")
        controls += 2
        _, errors = check_lessons_ids("# Lessons\n\nno ids here\n")
        expect("a file with zero ids is vacuous", errors, "lessons-vacuous")
        _, errors = check_lessons_ids("### GB-TEST-001 — d\n### gb-test-001 / d\n### GB-TEST-001/d\n")
        expect("only the '### ID /' heading form counts", errors, "lessons-vacuous")
        _, errors = check_lessons_ids((DATA / "lessons-duplicates.md").read_text(encoding="utf-8"))
        expect("the committed duplicate-id fixture is rejected", errors, "lessons-duplicate-id")

        # state-size: raw bytes and newline characters, exactly at the bound.
        _, errors = check_state_size(b"x" * (STATE_MAX_BYTES - 1) + b"\n")
        expect("STATE at the byte bound passes", errors, None)
        _, errors = check_state_size(b"x" * STATE_MAX_BYTES + b"\n")
        expect("STATE one byte over fails", errors, "state-size-bytes")
        _, errors = check_state_size(b"\n" * STATE_MAX_LINES)
        expect("STATE at the line bound passes", errors, None)
        _, errors = check_state_size(b"\n" * (STATE_MAX_LINES + 1))
        expect("STATE one line over fails", errors, "state-size-lines")
        multibyte = ("é" * (STATE_MAX_BYTES // 2 + 1)).encode("utf-8")
        _, errors = check_state_size(multibyte)
        expect("bytes are counted raw, not as decoded characters", errors, "state-size-bytes")
        _, errors = check_state_size(b"line\r\n" * STATE_MAX_LINES)
        expect("CRLF is one newline character per line", errors, None)
        # The oversized control is a fixture file driven through the CLI, never the live STATE.md.
        oversized = base / "state-oversized.md"
        oversized.write_bytes(b"line of state text\n" * (STATE_MAX_LINES + 5))
        with contextlib.redirect_stderr(io.StringIO()):
            oversized_exit = main(["--check", "state-size", "--state", str(oversized)])
        if oversized_exit != 1:
            raise SystemExit("planning-hygiene self-test FAIL: the oversized STATE fixture exited zero")
        controls += 1

        # CLI: an unreadable input is a failure, never a pass.
        with contextlib.redirect_stderr(io.StringIO()):
            missing_exit = main(["--check", "lessons-ids", "--lessons", str(base / "missing.md")])
        if missing_exit != 1:
            raise SystemExit("planning-hygiene self-test FAIL: a missing LESSONS file exited zero")
        controls += 1

        controls += self_test_playstead(base)

    print(f"planning-hygiene self-test pass controls={controls}")
    return 0


def self_test_playstead(base: Path) -> int:
    """Hook for the Playstead docs controls; replaced by the docs task of this plan."""
    return 0


# ---- CLI -------------------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", choices=("plan-cap", "lessons-ids", "state-size", "playstead-docs"))
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--roadmap")
    parser.add_argument("--phases-dir")
    parser.add_argument("--lessons")
    parser.add_argument("--state")
    parser.add_argument("--root")
    args = parser.parse_args(argv)
    if args.self_test == bool(args.check):
        parser.error("give exactly one of --check NAME or --self-test")
    if args.self_test:
        return self_test()
    try:
        if args.check == "plan-cap":
            if not args.roadmap or not args.phases_dir:
                parser.error("plan-cap needs --roadmap and --phases-dir")
            summary, errors = check_plan_cap(Path(args.roadmap).read_text(encoding="utf-8"), Path(args.phases_dir))
        elif args.check == "lessons-ids":
            if not args.lessons:
                parser.error("lessons-ids needs --lessons")
            summary, errors = check_lessons_ids(Path(args.lessons).read_text(encoding="utf-8"))
        elif args.check == "state-size":
            if not args.state:
                parser.error("state-size needs --state")
            summary, errors = check_state_size(Path(args.state).read_bytes())
        else:
            if not args.root:
                parser.error("playstead-docs needs --root")
            summary, errors = check_playstead_docs(Path(args.root))
    except OSError as error:
        print(f"planning-hygiene FAIL: cannot read input: {error}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"planning-hygiene FAIL {error}", file=sys.stderr)
        return 1
    print(summary)
    return 0


def check_playstead_docs(root: Path) -> tuple[str, list[str]]:
    return "", ["playstead-docs-unavailable: not implemented yet"]


if __name__ == "__main__":
    raise SystemExit(main())
