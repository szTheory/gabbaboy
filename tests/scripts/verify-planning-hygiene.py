#!/usr/bin/env python3
"""Planning hygiene checks for GabbaBoy (Phase 16 plan 16-05, TUNE-05; D-24..D-27).

Five checks, each a pure function over text or a directory that returns (summary, errors) with stable
error-code prefixes, so a control can pin the failure class instead of "some error":

  --check plan-cap (--roadmap PATH --phases-dir DIR | --rev COMMIT [--repo DIR])
      Every "### Phase N:" heading under "## Phase Details" needs one "**Plan cap**: N" line. Every plan file in
      the matching GB-N-* directory counts against it, whether it is named NN-NN-PLAN.md, NN-NNa-PLAN.md or
      NN-NN-PLAN-extra.md (a decimal phase counts against its parent unless it has its own heading and cap line;
      gap plans count). A cap above 12 fails, the caps must sum to at most 40 and the active milestone may list at
      most four phases (D-24, D-102, WR-05). One slot of every cap is reserved for the single gap round: plans that
      do not declare `gap_closure: true` may number at most cap - 1. With --rev the ROADMAP and the plan names
      are read from that full commit id with git, never from the working tree (a symbolic revision is refused).
      The phases directory is an argument: no default path. Prints "plan-cap pass phases=N plans=M".
  --check lessons-ids --lessons PATH
      "### ID / ..." is the only lesson heading form and ids compare as exact tokens; an id may appear once.
      A duplicate report names every occurrence's line and keeps the earliest (D-25).
      Prints "lessons-ids pass ids=N".
  --check state-size --state PATH
      STATE.md stays within STATE_MAX_BYTES raw bytes and STATE_MAX_LINES newline characters (D-26).
      Prints "state-size pass bytes=N lines=M".
  --check playstead-docs --root DIR
      README.md, docs/native-integration.md and .planning/research/PRECEDENT.md state PLAYSTEAD-CONTRACT section
      5 (GB, GBC and GBA through mGBA 0.10.5 on Playstead main 234bd45b21 as process adapters): the stale pin,
      "GBA/mGBA" and the current-tense 1de3e95 blocked-capability sentences are rejected, "234bd45b21" is required
      in each file, and the two sentences verify-v02-adoption.py requires must survive (D-27). No live
      GabbaBoy/Playstead integration is ever claimed. Prints "playstead-docs pass files=3".

  --check deferrals --rev COMMIT [--repo DIR]
      Pins the Phase 19 RM-024 deferral and the six RM-032 v0.4 candidates in FUTURE-MILESTONES.md.
      Reads that file from one full immutable commit id with git show. Prints "deferrals pass pins=8".

  --self-test   runs every rule against generated and committed fixtures and prints
                "planning-hygiene self-test pass controls=N" once; --rev/--repo select the
                immutable FUTURE-MILESTONES.md used by the deferral live-positive control.

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
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

if not __debug__ or sys.flags.optimize:
    raise SystemExit("verify-planning-hygiene must not run with python -O")

STATE_MAX_BYTES = 40960
STATE_MAX_LINES = 250
PLAN_CAP_MAX = 12
PLAN_CAP_SUM_MAX = 40
PHASE_COUNT_MAX = 4
GAP_RESERVE = 1

PHASE_HEADING = re.compile(r"^### Phase (\d+(?:\.\d+)?):")
CAP_LINE = re.compile(r"^\*\*Plan cap\*\*: (\d+)\s*$")
# A plan is any NN-<digit-led id>-PLAN*.md file: the canonical NN-NN-PLAN.md and suffixed forms such as NN-NNa-PLAN.md or
# NN-NN-PLAN-extra.md count too, so a plan cannot dodge the cap by its name. NN-PLAN-CHECK.md (no id) is not a plan.
PLAN_FILE = re.compile(r"^(\d+(?:\.\d+)?)-\d[^/\\]*-PLAN[^/\\]*\.md$", re.IGNORECASE)
GAP_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.DOTALL)
GAP_LINE = re.compile(r"(?m)^gap_closure:\s*true\s*$")
FULL_COMMIT = re.compile(r"[0-9a-f]{40}")
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


PlanTree = dict[str, dict[str, Callable[[], str]]]
# The one spelling of the phases directory this checker uses: a path inside a named commit, read with git, never the live tree.
PHASES_AT_REV = ".planning/phases"
DEFERRALS_AT_REV = ".planning/context/FUTURE-MILESTONES.md"
DEFERRAL_PINS = (
    "IN-03 (IN-A03), IN-04 (IN-B01) and IN-06 (IN-B03) deferred here by Phase 19 D-10",
    "RM-032",
    "GitHub immutable releases with `gh release verify`",
    "An optional ruleset protecting `v*` tags",
    "SLSA build provenance",
    "Rename the `v02-*` evidence names to version-agnostic names (D-16)",
    "`bump-minor-pre-major` in release-please-config.json (D-03)",
    "Move the paired-timing baseline off v0.1.0",
)


def is_gap_plan(text: str) -> bool:
    """A plan that declares `gap_closure: true` in its frontmatter is the phase's gap-round plan."""
    match = GAP_FRONTMATTER.match(text.replace("\r\n", "\n"))
    return match is not None and GAP_LINE.search(match.group(1)) is not None


def tree_from_dir(phases_dir: Path) -> PlanTree | None:
    """Phase directory name -> plan file name -> reader, from a working directory; None when it is not a directory."""
    if not phases_dir.is_dir():
        return None
    tree: PlanTree = {}
    for directory in sorted(p for p in phases_dir.iterdir() if p.is_dir()):
        tree[directory.name] = {f.name: (lambda f=f: f.read_text(encoding="utf-8", errors="replace"))
                                for f in directory.iterdir() if f.is_file() and PLAN_FILE.match(f.name)}
    return tree


def git_run(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "SYSTEMROOT", "TMPDIR", "TEMP", "TMP")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False, env=env, timeout=60)


def read_rev(repo: Path, rev: str) -> tuple[str, PlanTree]:
    """The ROADMAP text and the plan tree of one commit. Only a full commit id is accepted, so what is judged cannot move
    between reads, and nothing is read from the working tree."""
    if not FULL_COMMIT.fullmatch(rev):
        raise SystemExit("plan-cap-rev: --rev must be a full 40-hex commit id, not a name")
    found = git_run(repo, "cat-file", "-t", rev)
    if found.returncode != 0 or found.stdout.strip() != b"commit":
        raise SystemExit(f"plan-cap-rev: {rev} is not a commit in {repo}")
    roadmap = git_run(repo, "show", f"{rev}:.planning/ROADMAP.md")
    if roadmap.returncode != 0:
        raise SystemExit(f"plan-cap-rev: .planning/ROADMAP.md cannot be read at {rev}")
    listing = git_run(repo, "ls-tree", "-r", "--name-only", "-z", rev, "--", PHASES_AT_REV)
    if listing.returncode != 0:
        raise SystemExit(f"plan-cap-rev: {PHASES_AT_REV} cannot be listed at {rev}")
    tree: PlanTree = {}
    for raw in listing.stdout.split(b"\0"):
        parts = raw.decode("utf-8", errors="replace").split("/")
        if len(parts) != 4 or parts[:2] != PHASES_AT_REV.split("/"):
            continue
        directory, name = parts[2], parts[3]
        files = tree.setdefault(directory, {})
        if PLAN_FILE.match(name):
            def reader(path: str = "/".join(parts)) -> str:
                shown = git_run(repo, "show", f"{rev}:{path}")
                if shown.returncode != 0:
                    raise SystemExit(f"plan-cap-rev: {path} cannot be read at {rev}")
                return shown.stdout.decode("utf-8", errors="replace")
            files[name] = reader
    return roadmap.stdout.decode("utf-8"), tree


def read_deferrals(repo: Path, rev: str) -> str:
    """Read FUTURE-MILESTONES.md from one full commit id; never consult the working tree."""
    if not FULL_COMMIT.fullmatch(rev):
        raise SystemExit("deferrals-rev: --rev must be a full 40-hex commit id, not a name")
    found = git_run(repo, "cat-file", "-t", rev)
    if found.returncode != 0 or found.stdout.strip() != b"commit":
        raise SystemExit(f"deferrals-rev: {rev} is not a commit in {repo}")
    content = git_run(repo, "show", f"{rev}:{DEFERRALS_AT_REV}")
    if content.returncode != 0:
        raise SystemExit(f"deferrals-rev: {DEFERRALS_AT_REV} cannot be read at {rev}")
    return content.stdout.decode("utf-8", errors="strict")


def check_plan_cap(roadmap: str, phases_dir: Path) -> tuple[str, list[str]]:
    return check_plan_tree(roadmap, tree_from_dir(phases_dir), str(phases_dir))


def check_plan_tree(roadmap: str, tree: PlanTree | None, where: str) -> tuple[str, list[str]]:
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
    if len(caps) > PHASE_COUNT_MAX:
        errors.append(f"plan-cap-phase-count: the active milestone lists {len(caps)} phases, above {PHASE_COUNT_MAX}")
    for number, cap in caps.items():
        if cap is None:
            errors.append(f"plan-cap-missing: Phase {number} has no '**Plan cap**: N' line")
        elif cap > PLAN_CAP_MAX:
            errors.append(f"plan-cap-too-large: Phase {number} cap {cap} is above {PLAN_CAP_MAX}")
    total = sum(cap for cap in caps.values() if cap is not None)
    if total > PLAN_CAP_SUM_MAX:
        errors.append(f"plan-cap-sum: caps sum to {total}, above {PLAN_CAP_SUM_MAX}")

    counts = {number: 0 for number in caps}
    primary = {number: 0 for number in caps}
    if tree is not None:
        for directory_name in sorted(tree):
            match = PHASE_DIR.match(directory_name)
            if not match:
                continue
            number = match.group(1)
            owner = number if number in caps else number.split(".")[0]
            if owner not in caps:
                errors.append(f"plan-cap-orphan-dir: {directory_name} matches no phase heading")
                continue
            plans = tree[directory_name]
            counts[owner] += len(plans)
            primary[owner] += sum(1 for name in sorted(plans) if not is_gap_plan(plans[name]()))
    else:
        errors.append(f"plan-cap-phases-dir: not a directory: {where}")
    for number, cap in caps.items():
        if cap is None:
            continue
        if counts[number] > cap:
            errors.append(f"plan-cap-exceeded: Phase {number} has {counts[number]} plans, cap is {cap}")
        elif primary[number] > cap - GAP_RESERVE:
            errors.append(f"plan-cap-gap-reserve: Phase {number} has {primary[number]} plans that are not gap_closure plans; "
                          f"cap {cap} reserves {GAP_RESERVE} slot for the single gap round")
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


def check_deferrals(text: str) -> tuple[str, list[str]]:
    """Require all recorded Phase 19 deferrals/candidates after whitespace normalization."""
    normalized = " ".join(text.split())
    errors = [f"deferral-unrecorded: {phrase}" for phrase in DEFERRAL_PINS if phrase not in normalized]
    return f"deferrals pass pins={len(DEFERRAL_PINS)}", errors


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


GAP_FRONTMATTER_TEXT = "---\nphase: x\ngap_closure: true\n---\n\n# Gap plan\n"
PRIMARY_FRONTMATTER_TEXT = "---\nphase: x\ngap_closure: false\n---\n\n# Plan\n"


def make_phases(root: Path, counts: dict[str, int], gaps: dict[str, int] | None = None,
                extra: dict[str, list[str]] | None = None) -> Path:
    """Phase directories with `counts` primary plans, `gaps` more plans declaring gap_closure, and `extra` file names."""
    phases = root / "phases"
    phases.mkdir()
    for name, count in counts.items():
        directory = phases / f"GB-{name}-some-title"
        directory.mkdir()
        for index in range(1, count + 1):
            (directory / f"{name}-{index:02d}-PLAN.md").write_text(PRIMARY_FRONTMATTER_TEXT, encoding="utf-8")
        for index in range(count + 1, count + 1 + (gaps or {}).get(name, 0)):
            (directory / f"{name}-{index:02d}-PLAN.md").write_text(GAP_FRONTMATTER_TEXT, encoding="utf-8")
        for filename in (extra or {}).get(name, []):
            (directory / filename).write_text(PRIMARY_FRONTMATTER_TEXT, encoding="utf-8")
        (directory / f"{name}-SUMMARY-notes.md").write_text("", encoding="utf-8")
        (directory / f"{name}-01-SUMMARY.md").write_text("", encoding="utf-8")
        (directory / f"{name}-PLAN-CHECK.md").write_text("", encoding="utf-8")
    return phases


def self_test(rev: str | None = None, repo: Path = Path(".")) -> int:
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

        def phases(name: str, counts: dict[str, int], gaps: dict[str, int] | None = None,
                   extra: dict[str, list[str]] | None = None) -> Path:
            root = base / name
            root.mkdir()
            return make_phases(root, counts, gaps, extra)

        # plan-cap: boundary, cap line, cap size, cap sum, zero, vacuous.
        ok_map = [("16", "8"), ("17", "12"), ("18", "10"), ("19", "8")]
        summary, errors = check_plan_cap(roadmap_text(ok_map), phases("ok", {"16": 7, "17": 0}, {"16": 1}))
        expect("seven primary plans and the gap plan, equal to the cap, pass", errors, None)
        if summary != "plan-cap pass phases=4 plans=8":
            raise SystemExit(f"planning-hygiene self-test FAIL: unexpected pass line {summary!r}")
        _, errors = check_plan_cap(roadmap_text(ok_map), phases("over", {"16": 8}, {"16": 1}))
        expect("cap+1 plans fails", errors, "plan-cap-exceeded")
        _, errors = check_plan_cap(roadmap_text(ok_map), phases("reserve", {"16": 8}))
        expect("plans equal to the cap with no gap_closure plan leave no gap slot", errors, "plan-cap-gap-reserve")
        _, errors = check_plan_cap(roadmap_text(ok_map), phases("reserve7", {"16": 7}))
        expect("cap-1 primary plans pass without using the gap slot", errors, None)
        _, errors = check_plan_cap(roadmap_text(ok_map), phases("gap2", {"16": 6}, {"16": 2}))
        expect("gap_closure plans do not count against the primary budget", errors, None)
        _, errors = check_plan_cap(roadmap_text([("17", "12")]), phases("p12", {"17": 12}))
        expect("twelve primary plans in a cap-12 phase fail the 11 + 1 reserve", errors, "plan-cap-gap-reserve")
        _, errors = check_plan_cap(roadmap_text([("17", "12")]), phases("p11g1", {"17": 11}, {"17": 1}))
        expect("eleven primary plans plus one gap plan pass", errors, None)
        _, errors = check_plan_cap(roadmap_text([("17", "12")]), phases("p11g2", {"17": 11}, {"17": 2}))
        expect("a second gap plan beyond the cap fails", errors, "plan-cap-exceeded")
        # Suffixed and decorated names count exactly as canonical ones do (WR-05); NN-PLAN-CHECK.md is no plan.
        for label, names in (("a letter-suffixed id", ["17-01a-PLAN.md"]), ("a trailing suffix", ["17-03-PLAN-extra.md"]),
                             ("a decimal id", ["17-03.1-PLAN.md"]), ("lower case", ["17-04-plan.md"]),
                             ("a double suffix", ["17-02b-PLAN-copy.md"])):
            _, errors = check_plan_cap(roadmap_text([("17", "3")]), phases("sfx-" + label.replace(" ", "-"), {"17": 2}, extra={"17": names}))
            expect(f"{label} counts toward the cap (3 plans + reserve)", errors, "plan-cap-gap-reserve")
            _, errors = check_plan_cap(roadmap_text([("17", "12")]), phases("sfxok-" + label.replace(" ", "-"), {"17": 10}, extra={"17": names}))
            expect(f"{label} within the cap passes", errors, None)
        _, errors = check_plan_cap(roadmap_text([("17", "4")]), phases("sfxover", {"17": 3}, extra={"17": ["17-01a-PLAN.md", "17-02-PLAN-x.md"]}))
        expect("suffixed plans push a phase over its cap", errors, "plan-cap-exceeded")
        _, errors = check_plan_cap(roadmap_text([("17", "12")]), phases("chk", {"17": 11}))
        expect("NN-PLAN-CHECK.md and summaries are not plans", errors, None)
        # The four-phase milestone limit.
        _, errors = check_plan_cap(roadmap_text([("16", "4"), ("17", "4"), ("18", "4"), ("19", "4"), ("20", "4")]), phases("five", {}))
        expect("a fifth active phase fails", errors, "plan-cap-phase-count")
        _, errors = check_plan_cap(roadmap_text([("16", "4"), ("17", "4"), ("18", "4"), ("19", "4")]), phases("four", {}))
        expect("exactly four active phases pass", errors, None)
        _, errors = check_plan_cap(roadmap_text([("16", "2"), ("17", "2"), ("18", "2"), ("19", "2"), ("19.1", "2")]), phases("fivedec", {}))
        expect("a decimal phase heading is a fifth active phase", errors, "plan-cap-phase-count")
        _, errors = check_plan_cap(roadmap_text([("16", "8"), ("17", None)]), phases("nocap", {"16": 1}))
        expect("a phase without a cap line fails", errors, "plan-cap-missing")
        _, errors = check_plan_cap(roadmap_text([("16", "12")]), phases("c12", {"16": 11}, {"16": 1}))
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
        _, errors = check_plan_cap(roadmap_text([("15", "4"), ("15.1", "4")]), phases("dec1", {"15": 2, "15.1": 3}))
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

        controls += self_test_plan_cap_rev(base)

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

        live_revision = rev
        if live_revision is None:
            head = git_run(repo, "rev-parse", "HEAD")
            if head.returncode != 0:
                raise SystemExit(f"deferrals-rev: cannot resolve HEAD in {repo}")
            live_revision = head.stdout.decode("ascii").strip()
        live_text = read_deferrals(repo, live_revision)
        summary, errors = check_deferrals(live_text)
        if errors or summary != "deferrals pass pins=8":
            raise SystemExit(f"planning-hygiene self-test FAIL: live deferrals at {live_revision}: {errors}")
        controls += 1

        normalized = " ".join(live_text.split())
        for pin in DEFERRAL_PINS:
            mutant = normalized.replace(pin, "", 1)
            if mutant == normalized:
                raise SystemExit(f"planning-hygiene self-test FAIL: deferral pin mutant was not seeded: {pin}")
            _, errors = check_deferrals(mutant)
            expected = f"deferral-unrecorded: {pin}"
            if errors != [expected]:
                raise SystemExit(f"planning-hygiene self-test FAIL: omission of {pin!r} gave {errors}")
            controls += 1

        unrelated = normalized + " unrelated roadmap note for a positive twin"
        positive_twin = unrelated.replace(" unrelated roadmap note for a positive twin", "", 1)
        summary, errors = check_deferrals(positive_twin)
        if errors or summary != "deferrals pass pins=8":
            raise SystemExit(f"planning-hygiene self-test FAIL: unrelated phrase changed deferral result: {errors}")
        controls += 1

    print(f"planning-hygiene self-test pass controls={controls}")
    return 0


def self_test_plan_cap_rev(base: Path) -> int:
    """--rev judges one commit's ROADMAP and plan names with git, so a working-tree edit, a later commit or a moving name
    cannot change the verdict. Everything runs in a disposable repository."""
    controls = 0
    repo = base / "rev-repo"
    repo.mkdir()
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "SYSTEMROOT", "TMPDIR", "TEMP", "TMP")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, GIT_AUTHOR_NAME="fixture",
               GIT_AUTHOR_EMAIL="fixture@example.invalid", GIT_COMMITTER_NAME="fixture",
               GIT_COMMITTER_EMAIL="fixture@example.invalid")

    def git(*args: str) -> str:
        done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, env=env, timeout=60)
        return done.stdout.strip()

    def commit(files: dict[str, str], message: str) -> str:
        for rel, content in files.items():
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode("utf-8"))  # bytes, so a Windows text-mode write cannot add CRs (GB-CI-011)
            git("add", rel)
        git("commit", "-q", "-m", message)
        return git("rev-parse", "HEAD")

    def judge(rev: str) -> list[str]:
        roadmap, tree = read_rev(repo, rev)
        return check_plan_tree(roadmap, tree, rev)[1]

    def expect_rev(label: str, rev: str, code: str | None) -> None:
        nonlocal controls
        errors = judge(rev)
        if code is None and errors or code is not None and code not in codes(errors):
            raise SystemExit(f"planning-hygiene self-test FAIL: --rev {label}: wanted {code}, got {errors}")
        controls += 1

    def refused(label: str, rev: str, message: str) -> None:
        nonlocal controls
        try:
            read_rev(repo, rev)
        except SystemExit as error:
            if message not in str(error):
                raise SystemExit(f"planning-hygiene self-test FAIL: --rev {label} refused for the wrong reason: {error}")
            controls += 1
            return
        raise SystemExit(f"planning-hygiene self-test FAIL: --rev {label} was accepted")

    git("init", "-q")
    dir17 = PHASES_AT_REV + "/GB-17-name/"
    good = {".planning/ROADMAP.md": roadmap_text([("16", "8"), ("17", "4")]),
            dir17 + "17-01-PLAN.md": PRIMARY_FRONTMATTER_TEXT, dir17 + "17-02-PLAN.md": PRIMARY_FRONTMATTER_TEXT,
            dir17 + "17-03-PLAN.md": GAP_FRONTMATTER_TEXT, dir17 + "17-SUMMARY.md": ""}
    good_rev = commit(good, "good")
    expect_rev("a valid commit with a gap_closure plan read through git", good_rev, None)
    # The working tree is never consulted: uncommitted extra plans and a rewritten ROADMAP change nothing for this commit.
    (repo / (dir17 + "17-01a-PLAN.md")).write_text(PRIMARY_FRONTMATTER_TEXT, encoding="utf-8")
    (repo / ".planning/ROADMAP.md").write_text(roadmap_text([("16", "8")] * 5), encoding="utf-8")
    expect_rev("with uncommitted working-tree changes the commit still passes", good_rev, None)
    git("checkout", "-q", "--", ".planning/ROADMAP.md")
    (repo / (dir17 + "17-01a-PLAN.md")).unlink()
    # Later commits are judged on their own; the earlier commit keeps its verdict.
    suffixed_rev = commit({dir17 + "17-01a-PLAN.md": PRIMARY_FRONTMATTER_TEXT, dir17 + "17-01b-PLAN-extra.md": PRIMARY_FRONTMATTER_TEXT},
                          "suffixed plans over the cap")
    expect_rev("a committed suffixed plan over the cap", suffixed_rev, "plan-cap-exceeded")
    expect_rev("the earlier commit keeps its verdict", good_rev, None)
    reserve_rev = commit({dir17 + "17-03-PLAN.md": PRIMARY_FRONTMATTER_TEXT, ".planning/ROADMAP.md": roadmap_text([("16", "8"), ("17", "5")])},
                         "gap plan loses its marker")
    expect_rev("a committed gap plan without its marker leaves no reserved slot", reserve_rev, "plan-cap-gap-reserve")
    five_rev = commit({".planning/ROADMAP.md": roadmap_text([("16", "2"), ("17", "4"), ("18", "2"), ("19", "2"), ("20", "2")])},
                      "fifth phase")
    expect_rev("a committed fifth active phase", five_rev, "plan-cap-phase-count")
    # Names and non-commits are refused, each for its own reason.
    refused("HEAD", "HEAD", "full 40-hex commit id")
    refused("a short id", good_rev[:12], "full 40-hex commit id")
    refused("an upper-case id", good_rev.upper(), "full 40-hex commit id")
    refused("a tree id", git("rev-parse", f"{good_rev}^{{tree}}"), "is not a commit")
    refused("an absent id", "0" * 40, "is not a commit")
    # The CLI: a pass and a refusal, with the rev given as the only source.
    outputs = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(outputs[0]), contextlib.redirect_stderr(outputs[1]):
        ok_exit = main(["--check", "plan-cap", "--rev", good_rev, "--repo", str(repo)])
        bad_exit = main(["--check", "plan-cap", "--rev", suffixed_rev, "--repo", str(repo)])
    if ok_exit != 0 or bad_exit != 1 or "plan-cap pass phases=2 plans=3" not in outputs[0].getvalue() \
            or "plan-cap-exceeded" not in outputs[1].getvalue():
        raise SystemExit(f"planning-hygiene self-test FAIL: --rev through the CLI: {ok_exit} {bad_exit} {outputs[0].getvalue()} {outputs[1].getvalue()}")
    controls += 2
    return controls


# ---- CLI -------------------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", choices=("plan-cap", "lessons-ids", "state-size", "playstead-docs", "deferrals"))
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--roadmap")
    parser.add_argument("--phases-dir")
    parser.add_argument("--rev", help="plan-cap or deferrals: a full immutable commit id to read")
    parser.add_argument("--repo", default=".", help="repository for an immutable --rev read (default: current directory)")
    parser.add_argument("--lessons")
    parser.add_argument("--state")
    parser.add_argument("--root")
    args = parser.parse_args(argv)
    if args.self_test == bool(args.check):
        parser.error("give exactly one of --check NAME or --self-test")
    if args.self_test:
        return self_test(args.rev, Path(args.repo))
    try:
        if args.check == "plan-cap":
            if args.rev:
                if args.roadmap or args.phases_dir:
                    parser.error("plan-cap --rev reads the commit only; give no --roadmap or --phases-dir")
                roadmap_text_at_rev, tree = read_rev(Path(args.repo), args.rev)
                summary, errors = check_plan_tree(roadmap_text_at_rev, tree, args.rev)
            elif not args.roadmap or not args.phases_dir:
                parser.error("plan-cap needs --rev, or --roadmap and --phases-dir")
            else:
                summary, errors = check_plan_cap(Path(args.roadmap).read_text(encoding="utf-8"), Path(args.phases_dir))
        elif args.check == "lessons-ids":
            if not args.lessons:
                parser.error("lessons-ids needs --lessons")
            summary, errors = check_lessons_ids(Path(args.lessons).read_text(encoding="utf-8"))
        elif args.check == "state-size":
            if not args.state:
                parser.error("state-size needs --state")
            summary, errors = check_state_size(Path(args.state).read_bytes())
        elif args.check == "deferrals":
            if not args.rev:
                parser.error("deferrals needs --rev COMMIT")
            summary, errors = check_deferrals(read_deferrals(Path(args.repo), args.rev))
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


PLAYSTEAD_FILES = ("README.md", "docs/native-integration.md", ".planning/research/PRECEDENT.md")
PLAYSTEAD_PIN = "234bd45b21"
# (needle, error code). Needles are compared on whitespace-normalised, case-sensitive text.
PLAYSTEAD_STALE = (
    ("a102d608", "playstead-stale-pin"),
    ("GBA/mGBA", "playstead-stale-adapter-scope"),
    # The 1de3e95 observation is dated and superseded, never current: these are the sentences that stated it as current.
    ("latest 2026-09-28 qualification ledger remains", "playstead-stale-blocked-capability"),
    ("current continuation capability refusal", "playstead-stale-blocked-capability"),
    ("No current in-game continuation pass", "playstead-stale-blocked-capability"),
)
# (file, needle, error code): the contract facts and the sentences verify-v02-adoption.py requires.
PLAYSTEAD_REQUIRED = (
    ("README.md", "Playstead remains a future integration", "playstead-limit-missing"),
    ("README.md", "mGBA 0.10.5", "playstead-contract-missing"),
    ("docs/native-integration.md", "it is not a live GabbaBoy/Playstead integration", "playstead-limit-missing"),
    ("docs/native-integration.md", "mGBA 0.10.5", "playstead-contract-missing"),
    (".planning/research/PRECEDENT.md", "mGBA 0.10.5", "playstead-contract-missing"),
)


def check_playstead_docs(root: Path) -> tuple[str, list[str]]:
    texts: dict[str, str] = {}
    errors: list[str] = []
    for name in PLAYSTEAD_FILES:
        try:
            texts[name] = " ".join((root / name).read_text(encoding="utf-8").split())
        except OSError as error:
            errors.append(f"playstead-file-unreadable: {name}: {error}")
    for name, text in texts.items():
        for needle, code in PLAYSTEAD_STALE:
            if needle in text:
                errors.append(f"{code}: {name} still says {needle!r}")
        if PLAYSTEAD_PIN not in text:
            errors.append(f"playstead-pin-missing: {name} does not name Playstead main {PLAYSTEAD_PIN}")
    for name, needle, code in PLAYSTEAD_REQUIRED:
        if name in texts and needle not in texts[name]:
            errors.append(f"{code}: {name} lacks {needle!r}")
    return f"playstead-docs pass files={len(PLAYSTEAD_FILES)}", errors


def playstead_good_tree(root: Path) -> None:
    good = {
        "README.md": (
            "Playstead remains a future integration: it runs GB, GBC and GBA through mGBA\n"
            "0.10.5 as an external process adapter (Playstead main `234bd45b21`)."
        ),
        "docs/native-integration.md": (
            "Playstead main `234bd45b21` runs GB, GBC and GBA through mGBA 0.10.5 as an external\n"
            "process adapter; it is not a live GabbaBoy/Playstead integration."
        ),
        ".planning/research/PRECEDENT.md": (
            "As observed at Playstead `1de3e95` (2026-09-28) the ledger was blocked; superseded by main\n"
            "`234bd45b21`, which runs GB, GBC and GBA through mGBA 0.10.5."
        ),
    }
    for name, text in good.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")


def self_test_playstead(base: Path) -> int:
    controls = 0

    def mutate(label: str, name: str, edit, code: str | None) -> None:
        nonlocal controls
        root = base / f"playstead-{controls}"
        playstead_good_tree(root)
        path = root / name
        path.write_text(edit(path.read_text(encoding="utf-8")), encoding="utf-8")
        _, errors = check_playstead_docs(root)
        if code is None:
            if errors:
                raise SystemExit(f"planning-hygiene self-test FAIL: {label} should pass but gave {errors}")
        elif code not in codes(errors):
            raise SystemExit(f"planning-hygiene self-test FAIL: {label} did not report {code}: {errors}")
        controls += 1

    root = base / "playstead-good"
    playstead_good_tree(root)
    summary, errors = check_playstead_docs(root)
    if errors or summary != "playstead-docs pass files=3":
        raise SystemExit(f"planning-hygiene self-test FAIL: the good Playstead tree gave {summary!r} {errors}")
    controls += 1
    mutate("rewrapped text still passes", "README.md", lambda t: t.replace(" ", "\n"), None)
    mutate("stale pin", "docs/native-integration.md", lambda t: t + "pinned a102d6082968bc09ca00fefbf5c552ecf979fd63\n",
           "playstead-stale-pin")
    mutate("stale adapter scope", "README.md", lambda t: t + "its adapter is GBA/mGBA\n", "playstead-stale-adapter-scope")
    mutate("current-tense blocked capability", ".planning/research/PRECEDENT.md",
           lambda t: t + "Playstead's latest 2026-09-28 qualification ledger remains `blocked-capability`.\n",
           "playstead-stale-blocked-capability")
    mutate("current refusal in the table row", ".planning/research/PRECEDENT.md",
           lambda t: t + "| a | b | current continuation capability refusal |\n", "playstead-stale-blocked-capability")
    mutate("pin dropped from a file", "docs/native-integration.md", lambda t: t.replace("234bd45b21", "main"),
           "playstead-pin-missing")
    mutate("future-integration sentence dropped", "README.md",
           lambda t: t.replace("Playstead remains a future integration", "Playstead is integrated"), "playstead-limit-missing")
    mutate("not-live sentence dropped", "docs/native-integration.md",
           lambda t: t.replace("it is not a live GabbaBoy/Playstead integration", "it is live"), "playstead-limit-missing")
    mutate("mGBA version dropped", ".planning/research/PRECEDENT.md", lambda t: t.replace("mGBA 0.10.5", "mGBA"),
           "playstead-contract-missing")
    # A missing file is an error, never a pass.
    gone = base / "playstead-gone"
    playstead_good_tree(gone)
    (gone / "README.md").unlink()
    _, errors = check_playstead_docs(gone)
    if "playstead-file-unreadable" not in codes(errors):
        raise SystemExit(f"planning-hygiene self-test FAIL: a missing README was not reported: {errors}")
    controls += 1
    return controls


if __name__ == "__main__":
    raise SystemExit(main())
