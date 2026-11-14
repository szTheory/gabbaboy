#!/usr/bin/env python3
"""Planning hygiene checks for GabbaBoy (Phase 16 plan 16-05, TUNE-05; D-24..D-27).

Six checks, each a pure function over text or a directory that returns (summary, errors) with stable
error-code prefixes, so a control can pin the failure class instead of "some error":

  --check plan-cap (--roadmap PATH --phases-dir DIR | --rev COMMIT [--repo DIR])
      Every "### Phase N:" heading under "## Phase Details" needs one "**Plan cap**: N" line. Every plan file in
      the matching GB-N-* directory counts against it, whether it is named NN-NN-PLAN.md, NN-NNa-PLAN.md or
      NN-NN-PLAN-extra.md (a decimal phase counts against its parent unless it has its own heading and cap line;
      gap plans count). A cap above 12 fails, the caps must sum to at most 40 and the active milestone may list at
      most four phases (D-24, D-102, WR-05), with the exact D-193 v0.4 exception. One slot of every cap is reserved for the single gap round: plans that
      do not declare `gap_closure: true` may number at most cap - 1. With --rev the ROADMAP and the plan names
      are read from that full commit id with git, never from the working tree (a symbolic revision is refused).
      At an explicitly completed milestone with no active requirements or phase records, the matching
      archived roadmap and plan tree are read from the same commit; incomplete live roadmaps still fail.
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
  --check v04-reconciliation --stage report|handoff --rev COMMIT --baseline-rev COMMIT [--repo DIR]
      Checks Phase 22's historical report or its current Phase 23.1 handoff using two immutable commits.
      Historical Phase 20/21 reports, the audit snapshot, requirements and Phase 22 source artifacts must
      match the execution-start baseline; the Phase 22 facts are read from their pinned evidence commit.
      Prints "v04-reconciliation pass stage=report|handoff".

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
import json
import os
import posixpath
import re
import subprocess
import sys
import tarfile
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
V04_APPROVED_PHASE_CAPS = {"20": 9, "21": 8, "22": 12, "23": 10, "23.1": 1}
V04_EXCEPTION_TEXT = "one exact exception for the active v0.4 phase set 20/21/22/23/23.1"

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
    roadmap_path = ".planning/ROADMAP.md"
    phases_path = PHASES_AT_REV
    roadmap = git_run(repo, "show", f"{rev}:{roadmap_path}")
    if roadmap.returncode != 0:
        raise SystemExit(f"plan-cap-rev: {roadmap_path} cannot be read at {rev}")
    listing = git_run(repo, "ls-tree", "-r", "--name-only", "-z", rev, "--", phases_path)
    if listing.returncode != 0:
        raise SystemExit(f"plan-cap-rev: {phases_path} cannot be listed at {rev}")
    # A collapsed roadmap is legitimate only at the recorded milestone boundary. Never
    # hide an incomplete active roadmap by falling back to a previous archive.
    active_paths = [path for path in listing.stdout.split(b"\0") if path]
    placeholder = (PHASES_AT_REV + "/.gitkeep").encode("utf-8")
    if phase_details(roadmap.stdout.decode("utf-8")) is None and active_paths in ([], [placeholder]):
        state = git_run(repo, "show", f"{rev}:.planning/STATE.md")
        requirements = git_run(repo, "ls-tree", "--name-only", rev, "--", ".planning/REQUIREMENTS.md")
        state_text = state.stdout.decode("utf-8", errors="strict") if state.returncode == 0 else ""
        frontmatter = GAP_FRONTMATTER.match(state_text)
        fields = frontmatter.group(1) if frontmatter else ""
        versions = re.findall(r"^milestone: (v[0-9]+\.[0-9]+)$", fields, re.MULTILINE)
        statuses = re.findall(r"^status: (.+)$", fields, re.MULTILINE)
        if statuses == ["milestone_completed"] and len(versions) == 1 and requirements.returncode == 0 and not requirements.stdout:
            base = f".planning/milestones/{versions[0]}"
            roadmap_path = base + "-ROADMAP.md"
            phases_path = base + "-phases"
            roadmap = git_run(repo, "show", f"{rev}:{roadmap_path}")
            if roadmap.returncode != 0:
                raise SystemExit(f"plan-cap-rev: archived roadmap {roadmap_path} cannot be read at {rev}")
            listing = git_run(repo, "ls-tree", "-r", "--name-only", "-z", rev, "--", phases_path)
            if listing.returncode != 0:
                raise SystemExit(f"plan-cap-rev: {phases_path} cannot be listed at {rev}")
    prefix = phases_path.split("/")
    tree: PlanTree = {}
    for raw in listing.stdout.split(b"\0"):
        parts = raw.decode("utf-8", errors="replace").split("/")
        if len(parts) != len(prefix) + 2 or parts[:len(prefix)] != prefix:
            continue
        directory, name = parts[-2], parts[-1]
        files = tree.setdefault(directory, {})
        if PLAN_FILE.match(name):
            def reader(path: str = "/".join(parts)) -> str:
                shown = git_run(repo, "show", f"{rev}:{path}")
                if shown.returncode != 0:
                    raise SystemExit(f"plan-cap-rev: {path} cannot be read at {rev}")
                return shown.stdout.decode("utf-8", errors="replace")
            files[name] = reader
    return roadmap.stdout.decode("utf-8"), tree


V04_IMPLEMENTATION_HEAD = "ca2f0be6b38e7dd22e0eb3296b9a21cceed1a765"
V04_IMPLEMENTATION_TREE = "e768b7ec26d7c07542d6aa29aef53ae8fc826c5e"
V04_EVIDENCE_HEAD = "d18db4c56d2a79e6138df37a9d16e3d346a86e13"
V04_PENDING_OWNERS = {"FIXT-01": "Phase 21", "RIGHTS-01": "Phase 20",
                      "DIAG-01": "Phase 22", "DIAG-02": "Phase 22"}
V04_UNRESOLVED_GATES = (
    "acid2_derivative_build_reproducibility",
    "acid2_component_rights_and_output_scope",
    "acid2_profile_applicability",
    "gbmicrotest_component_rights_and_output_scope",
    "gbmicrotest_prebuilt_rom_sha256",
    "gbmicrotest_case_applicability",
    "gbmicrotest_independent_oracle",
)
V04_HISTORICAL_AUDIT = ".planning/v0.4-MILESTONE-AUDIT.md"
V04_PHASE22_SUMMARIES = ("22-01-SUMMARY.md", "22-02-SUMMARY.md", "22-10-SUMMARY.md",
                         "22-11-SUMMARY.md", "22-12-SUMMARY.md")


COMMIT_SNAPSHOT_CACHE: dict[tuple[str, str], dict[str, bytes]] = {}


def commit_snapshot(repo: Path, rev: str) -> tuple[dict[str, bytes] | None, str | None]:
    """Read the planning tree from a commit in one Git operation; cache only immutable object ids."""
    cache_key = (str(repo.resolve()), rev)
    if cache_key in COMMIT_SNAPSHOT_CACHE:
        return COMMIT_SNAPSHOT_CACHE[cache_key], None
    if not FULL_COMMIT.fullmatch(rev):
        return None, "v04-reconciliation-rev: --rev must be a full 40-hex commit id"
    found = git_run(repo, "cat-file", "-t", rev)
    if found.returncode != 0 or found.stdout.strip() != b"commit":
        return None, f"v04-reconciliation-rev: {rev} is not a commit in {repo}"
    archive = git_run(repo, "archive", "--format=tar", rev, "--", ".planning")
    if archive.returncode != 0:
        return None, f"v04-reconciliation-tree: cannot read planning files at {rev}"
    snapshot: dict[str, bytes] = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as tar:
            for member in tar.getmembers():
                if member.isfile():
                    stream = tar.extractfile(member)
                    if stream is not None:
                        snapshot[member.name] = stream.read()
    except (tarfile.TarError, OSError) as error:
        return None, f"v04-reconciliation-tree: cannot decode planning snapshot at {rev}: {error}"
    if not snapshot:
        return None, f"v04-reconciliation-tree: commit has no readable planning files at {rev}"
    COMMIT_SNAPSHOT_CACHE[cache_key] = snapshot
    return snapshot, None


def commit_paths(repo: Path, rev: str) -> tuple[list[str] | None, str | None]:
    """List planning paths in one immutable commit after validating its full object identity."""
    snapshot, error = commit_snapshot(repo, rev)
    return (sorted(snapshot) if snapshot is not None else None), error


def commit_file(repo: Path, rev: str, path: str) -> bytes | None:
    """Read a single file from a commit; never fall back to the checkout."""
    snapshot, _ = commit_snapshot(repo, rev)
    return snapshot.get(path) if snapshot is not None else None


def phase_directory(paths: list[str], number: str) -> str | None:
    """Find a unique phase directory from immutable Git inventory and its numeric metadata."""
    found = {"/".join(path.split("/")[:3]) for path in paths
             if len(path.split("/")) >= 4 and path.startswith(PHASES_AT_REV + "/")
             and (match := PHASE_DIR.match(path.split("/")[2])) is not None and match.group(1) == number}
    return next(iter(found)) if len(found) == 1 else None


def phase_file(paths: list[str], number: str, filename: str) -> str | None:
    directory = phase_directory(paths, number)
    if directory is None:
        return None
    candidate = f"{directory}/{filename}"
    return candidate if candidate in paths else None


def frontmatter_fields(text: str) -> tuple[dict[str, str], str]:
    match = GAP_FRONTMATTER.match(text.replace("\r\n", "\n"))
    if match is None:
        return {}, text
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if line and not line[0].isspace() and ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip("\"'")
    return fields, text[match.end():]


def frontmatter_duplicates(text: str) -> list[str]:
    """Return duplicate top-level YAML keys and repeated fields within a sequence object."""
    match = GAP_FRONTMATTER.match(text.replace("\r\n", "\n"))
    if match is None:
        return []
    top_level: set[str] = set()
    item_fields: set[str] | None = None
    duplicates: list[str] = []
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if not line[0].isspace():
            item_fields = None
            top = re.match(r"^([A-Za-z0-9_-]+):", line)
            if top:
                key = top.group(1)
                if key in top_level:
                    duplicates.append(f"top-level key '{key}'")
                top_level.add(key)
            continue
        item = re.match(r"^\s+-\s+([A-Za-z0-9_-]+):", line)
        if item:
            item_fields = {item.group(1)}
            continue
        nested = re.match(r"^\s+([A-Za-z0-9_-]+):", line)
        if nested and item_fields is not None:
            key = nested.group(1)
            if key in item_fields:
                duplicates.append(f"nested field '{key}'")
            item_fields.add(key)
    return duplicates


def frontmatter_sequence(text: str, key: str) -> list[str] | None:
    match = GAP_FRONTMATTER.match(text.replace("\r\n", "\n"))
    if match is None:
        return None
    lines = match.group(1).splitlines()
    for index, line in enumerate(lines):
        if line.strip() != f"{key}:":
            continue
        values: list[str] = []
        for item in lines[index + 1:]:
            if not item.strip():
                continue
            if not item.startswith((" ", "\t")):
                break
            value = re.match(r"\s+-\s+(.+?)\s*$", item)
            if value:
                values.append(value.group(1).strip().strip("\"'"))
        return values
    return None


def frontmatter_objects(text: str, key: str) -> list[dict[str, str]] | None:
    match = GAP_FRONTMATTER.match(text.replace("\r\n", "\n"))
    if match is None:
        return None
    lines = match.group(1).splitlines()
    start = next((index for index, line in enumerate(lines) if line.strip() == f"{key}:"), None)
    if start is None:
        return None
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in lines[start + 1:]:
        if line and not line[0].isspace():
            break
        item = re.match(r"\s+-\s+([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
        if item:
            if current is not None:
                entries.append(current)
            current = {item.group(1): item.group(2).strip().strip("\"'")}
            continue
        field = re.match(r"\s+([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
        if field and current is not None:
            current[field.group(1)] = field.group(2).strip().strip("\"'")
    if current is not None:
        entries.append(current)
    return entries


def markdown_section(text: str, title: str) -> str:
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines)
                  if re.match(r"^#{1,4}\s+" + re.escape(title) + r"\s*$", line, re.IGNORECASE)), None)
    if start is None:
        return ""
    end = next((index for index in range(start + 1, len(lines))
                if re.match(r"^#{1,4}\s+", lines[index])), len(lines))
    return "\n".join(lines[start + 1:end])


def markdown_heading_count(text: str, title: str) -> int:
    """Count exact Markdown headings for a contract section, case-insensitively."""
    pattern = re.compile(r"^#{1,6}\s+" + re.escape(title) + r"\s*$", re.IGNORECASE)
    return sum(bool(pattern.match(line)) for line in text.splitlines())


def markdown_table_cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    cells = [cell.strip() for cell in stripped[1:-1].split("|")]
    if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
        return None
    return cells


def has_local_link(text: str, source_path: str, target_path: str) -> bool:
    for match in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", text):
        href = match.group(1).strip().split(None, 1)[0].strip("<>").split("#", 1)[0]
        if not href or "://" in href or href.startswith(("mailto:", "data:", "/")):
            continue
        if posixpath.normpath(posixpath.join(posixpath.dirname(source_path), href)) == target_path:
            return True
    return False


def requirement_traceability(text: str) -> dict[str, tuple[str, str]]:
    section = markdown_section(text, "Traceability")
    rows: dict[str, tuple[str, str]] = {}
    for line in section.splitlines():
        match = re.match(r"\|\s*(FIXT-01|RIGHTS-01|DIAG-01|DIAG-02)\s*\|\s*(Phase\s+\d+(?:\.\d+)?)\s*\|\s*(Pending|Complete|Satisfied)\s*\|", line, re.IGNORECASE)
        if match:
            rows[match.group(1).upper()] = (" ".join(match.group(2).split()), match.group(3).capitalize())
    return rows


def phase22_immutable_paths(paths: list[str]) -> list[str]:
    directory = phase_directory(paths, "22")
    if directory is None:
        return []
    selected = []
    for path in paths:
        if not path.startswith(directory + "/"):
            continue
        filename = path.rsplit("/", 1)[-1]
        if filename in ("22-EVIDENCE.md", "22-SOURCE-AUDIT.md") or re.fullmatch(r"22-\d+(?:\.\d+)?-SUMMARY\.md", filename):
            selected.append(path)
    return sorted(selected)


def compare_immutable_inputs(repo: Path, rev: str, baseline_rev: str,
                             target_paths: list[str], baseline_paths: list[str]) -> list[str]:
    errors: list[str] = []
    fixed_paths = [V04_HISTORICAL_AUDIT, ".planning/REQUIREMENTS.md"]
    for number in ("20", "21"):
        name = f"{number}-VERIFICATION.md"
        base_path = phase_file(baseline_paths, number, name)
        target_path = phase_file(target_paths, number, name)
        if base_path is None or target_path is None or base_path != target_path:
            errors.append(f"v04-history-missing: Phase {number} verification is missing or moved")
        else:
            fixed_paths.append(base_path)
    phase23_continue_base = phase_file(baseline_paths, "23", ".continue-here.md")
    phase23_continue_target = phase_file(target_paths, "23", ".continue-here.md")
    if phase23_continue_base is None or phase23_continue_target is None or phase23_continue_base != phase23_continue_target:
        errors.append("v04-history-missing: Phase 23 continuation is missing or moved")
    else:
        fixed_paths.append(phase23_continue_base)
    base_22 = phase22_immutable_paths(baseline_paths)
    target_22 = phase22_immutable_paths(target_paths)
    if not base_22 or base_22 != target_22:
        errors.append("v04-history-phase22: Phase 22 evidence, source audit, or summary inventory changed")
    fixed_paths.extend(base_22)
    for path in fixed_paths:
        before = commit_file(repo, baseline_rev, path)
        after = commit_file(repo, rev, path)
        if before is None or after is None:
            errors.append(f"v04-history-missing: required historical file is missing: {path.rsplit('/', 1)[-1]}")
        elif before != after:
            errors.append(f"v04-history-changed: immutable historical file changed: {path.rsplit('/', 1)[-1]}")
    return errors


def check_v04_report(repo: Path, rev: str, baseline_rev: str,
                     paths: list[str], baseline_paths: list[str]) -> tuple[str, list[str]]:
    errors = compare_immutable_inputs(repo, rev, baseline_rev, paths, baseline_paths)
    report_path = phase_file(paths, "22", "22-VERIFICATION.md")
    if report_path is None:
        return "", errors + ["v04-report-missing: Phase 22 verification report is missing from --rev"]
    if phase_file(baseline_paths, "22", "22-VERIFICATION.md") is not None:
        errors.append("v04-report-baseline: Phase 22 verification already exists at --baseline-rev")
    raw = commit_file(repo, rev, report_path)
    if raw is None:
        return "", errors + ["v04-report-missing: Phase 22 verification report cannot be read from --rev"]
    report = raw.decode("utf-8", errors="replace")
    fields, body = frontmatter_fields(report)
    duplicate_fields = frontmatter_duplicates(report)
    if duplicate_fields:
        errors.append("v04-report-frontmatter-duplicate: " + ", ".join(duplicate_fields))
    expected_fields = {
        "phase": "GB-22-composition-and-microtest-evidence",
        "source_head": V04_EVIDENCE_HEAD,
        "implementation_head": V04_IMPLEMENTATION_HEAD,
        "evidence_head": V04_EVIDENCE_HEAD,
        "report_kind": "boundary_reconstruction",
        "status": "passed",
        "metadata_cases": "513",
        "shared_macro_cases": "480",
        "inline_cases": "2",
        "initial_no_protocol_exclusions": "31",
        "admitted": "0",
        "executed": "0",
        "requirements_satisfied": "[]",
    }
    for key, expected in expected_fields.items():
        if fields.get(key) != expected:
            errors.append(f"v04-report-field: {key} must be {expected}")
    if frontmatter_sequence(report, "unresolved_gates") != list(V04_UNRESOLVED_GATES):
        errors.append("v04-report-gates: the exact seven unresolved gates must be a frontmatter sequence")
    dispositions = frontmatter_objects(report, "requirement_dispositions") or []
    disposition_ids = [item.get("id", "") for item in dispositions]
    if len(disposition_ids) != len(set(disposition_ids)):
        errors.append("v04-report-requirements: requirement disposition IDs must be unique")
    actual_dispositions = {item.get("id", ""): (item.get("status", ""), item.get("original_owner", "")) for item in dispositions}
    expected_dispositions = {key: ("Pending", owner) for key, owner in V04_PENDING_OWNERS.items()}
    if actual_dispositions != expected_dispositions:
        errors.append("v04-report-requirements: four original requirements must remain Pending with their original owners")

    implementation_tree = git_run(repo, "show", "-s", "--format=%T", V04_IMPLEMENTATION_HEAD)
    if implementation_tree.returncode != 0 or implementation_tree.stdout.decode("ascii", errors="replace").strip() != V04_IMPLEMENTATION_TREE:
        errors.append("v04-report-implementation: pinned implementation merge or tree identity is unavailable")
    evidence_paths, evidence_error = commit_paths(repo, V04_EVIDENCE_HEAD)
    if evidence_error:
        errors.append("v04-report-evidence: pinned Phase 22 evidence commit is unavailable")
    else:
        evidence_path = phase_file(evidence_paths or [], "22", "22-EVIDENCE.md")
        audit_path = phase_file(evidence_paths or [], "22", "22-SOURCE-AUDIT.md")
        evidence = commit_file(repo, V04_EVIDENCE_HEAD, evidence_path) if evidence_path else None
        audit = commit_file(repo, V04_EVIDENCE_HEAD, audit_path) if audit_path else None
        evidence_text = evidence.decode("utf-8", errors="replace") if evidence else ""
        audit_text = audit.decode("utf-8", errors="replace") if audit else ""
        if not evidence or not audit or any(value not in evidence_text for value in ("513", "480", "31", "admitted = 0", "executed = 0")):
            errors.append("v04-report-evidence: pinned evidence does not support the structured metadata-only counts")
        if any(gate not in audit_text for gate in V04_UNRESOLVED_GATES):
            errors.append("v04-report-evidence: pinned source audit does not contain the exact unresolved gates")
        if "482" not in audit_text or "blocked" not in audit_text.lower():
            errors.append("v04-report-evidence: pinned source audit does not preserve the 482 blocked-candidate count")

    requirements_base = commit_file(repo, baseline_rev, ".planning/REQUIREMENTS.md")
    requirements_now = commit_file(repo, rev, ".planning/REQUIREMENTS.md")
    if requirements_base is None or requirements_now is None or requirements_base != requirements_now:
        errors.append("v04-report-requirements: REQUIREMENTS.md changed from the execution-start baseline")
    elif requirement_traceability(requirements_now.decode("utf-8", errors="replace")) != {
            key: (owner, "Pending") for key, owner in V04_PENDING_OWNERS.items()}:
        errors.append("v04-report-requirements: original Pending owners do not match REQUIREMENTS.md")

    if "historical reconstruction scope" not in body.lower() or "synthetic" not in body.lower() or "metadata-only" not in body.lower():
        errors.append("v04-report-scope: report must identify the historical synthetic-plus-metadata reconstruction scope")
    if "482 protocol candidates remain blocked" not in " ".join(body.lower().split()):
        errors.append("v04-report-evidence: report must retain the blocked 482 protocol-candidate count")
    for heading in ("Historical reconstruction scope", "Goal Achievement", "Exact game no-go facts",
                    "Requirement truth and preserved limits"):
        if markdown_heading_count(body, heading) != 1:
            errors.append(f"v04-report-heading: {heading} must appear exactly once")
    goal = markdown_section(body, "Goal Achievement") or markdown_section(body, "Goal achievement")
    table = [cells for line in goal.splitlines() if (cells := markdown_table_cells(line)) is not None]
    status_columns = [index for index, title in enumerate(table[0] if table else [])
                      if title.strip().lower() in ("status", "historical status", "result", "result status")]
    criterion_rows: list[tuple[int, list[str], str]] = []
    for line in goal.splitlines():
        cells = markdown_table_cells(line)
        if not cells:
            continue
        criterion = re.match(r"^(\d+)\s*[.)]\s*", cells[0])
        if criterion:
            criterion_rows.append((int(criterion.group(1)), cells, line))
    criterion_ids = [number for number, _, _ in criterion_rows]
    if criterion_ids != [1, 2, 3]:
        errors.append("v04-report-criteria: exactly criteria 1, 2, and 3 need explicit evidence rows")
    if len(status_columns) != 1:
        errors.append("v04-report-criteria: the criterion table needs exactly one Status or Result column")
    elif len(criterion_rows) == 3:
        for number, cells, _ in criterion_rows:
            status_index = status_columns[0]
            result = re.sub(r"[*_`]", "", cells[status_index]).strip().upper() if len(cells) > status_index else ""
            if result != "VERIFIED":
                errors.append(f"v04-report-criteria: criterion {number} result must be VERIFIED")
    criterion_lines = [line.lower() for _, _, line in criterion_rows]
    if len(criterion_lines) != 3:
        errors.append("v04-report-criteria: all three approved Phase 22 criteria need explicit evidence rows")
    else:
        criterion_terms = (
            ("synthetic", "composition", "source-cell", "mask", "identity", "image"),
            ("513", "metadata", "seven", "admitted", "executed"),
            ("documentation", "automated", "synthetic-only", "no-go", "license prohibition",
             "diag-01", "diag-02", "rights-01", "pending"),
        )
        for index, terms in enumerate(criterion_terms):
            if not all(term in criterion_lines[index] for term in terms):
                errors.append(f"v04-report-criteria: criterion {index + 1} is missing its scoped evidence facts")
    evidence_paths, _ = commit_paths(repo, V04_EVIDENCE_HEAD)
    required_link_names = ("22-EVIDENCE.md", "22-SOURCE-AUDIT.md", *V04_PHASE22_SUMMARIES)
    required_link_paths = [phase_file(paths, "22", name) for name in required_link_names]
    if (not report_path or any(path is None for path in required_link_paths)
            or any(not has_local_link(report, report_path, path) for path in required_link_paths if path is not None)):
        errors.append("v04-report-links: source, summary, and evidence key links must resolve in the immutable report revision")
    if evidence_paths is None or any(phase_file(evidence_paths, "22", name) is None for name in ("22-EVIDENCE.md", "22-SOURCE-AUDIT.md")):
        errors.append("v04-report-links: pinned evidence commit lacks its Phase 22 evidence or source audit")
    no_go = " ".join(markdown_section(body, "Exact game no-go facts").lower().split())
    potion_terms = ("potion panic", "creator-linked", "ref", "commit", "fork", "source authority", "unobserved")
    ucity_terms = ("µcity 1.3", "d1880a2a112d7c26f16c0fc06a15b6c32fdc9137", "source/engine/hardware.inc",
                   "grant", "notice", "no upstream tool", "no rom", "no-go")
    if not all(term in no_go for term in potion_terms) or not all(term in no_go for term in ucity_terms):
        errors.append("v04-report-no-go: exact Potion Panic and µCity 1.3 source/rights cutoffs are incomplete")
    limits = " ".join(markdown_section(body, "Requirement truth and preserved limits").lower().split())
    if not all(term in limits for term in ("license prohibition", "permission", "hardware", "perceptual", "timing", "linux", "steam deck", "playstead")):
        errors.append("v04-report-limits: software-model, rights, hardware, perception, timing, and platform limits are incomplete")
    if "full milestone closure remains unsatisfied" not in " ".join(body.lower().split()):
        errors.append("v04-report-open: report must say full milestone closure remains unsatisfied")
    return "v04-reconciliation pass stage=report", errors


def check_v04_handoff(repo: Path, rev: str, baseline_rev: str,
                      paths: list[str], baseline_paths: list[str]) -> tuple[str, list[str]]:
    errors: list[str] = []
    report_path = phase_file(paths, "22", "22-VERIFICATION.md")
    report_raw = commit_file(repo, rev, report_path) if report_path else None
    report = report_raw.decode("utf-8", errors="replace") if report_raw is not None else ""
    _, report_errors = check_v04_report(repo, rev, baseline_rev, paths, baseline_paths)
    errors.extend(report_errors)
    state_path, project_path = ".planning/STATE.md", ".planning/PROJECT.md"
    state_raw, project_raw = commit_file(repo, rev, state_path), commit_file(repo, rev, project_path)
    continuation_path = phase_file(paths, "23.1", ".continue-here.md")
    continuation_raw = commit_file(repo, rev, continuation_path) if continuation_path else None
    if state_raw is None or project_raw is None or continuation_raw is None:
        return "", errors + ["v04-handoff-missing: STATE, PROJECT, or current phase continuation is missing"]
    state, project = state_raw.decode("utf-8", errors="replace"), project_raw.decode("utf-8", errors="replace")
    continuation = continuation_raw.decode("utf-8", errors="replace")
    for document_name, document, heading in (
            ("STATE", state, "Owner Handoff"),
            ("PROJECT", project, "Current State"),
            ("continuation", continuation, "Owner Handoff")):
        if markdown_heading_count(document, heading) != 1:
            errors.append(f"v04-handoff-heading: {document_name} {heading} heading must appear exactly once")
    state_fields, _ = frontmatter_fields(state)
    if state_fields.get("current_phase") != "23.1" or state_fields.get("milestone") != "v0.4" or state_fields.get("status") == "milestone_completed":
        errors.append("v04-handoff-state: current state must remain in open Phase 23.1 of v0.4")
    config_raw = commit_file(repo, rev, ".planning/config.json")
    try:
        config = json.loads(config_raw.decode("utf-8")) if config_raw is not None else {}
        workflow = config["workflow"]
        if workflow.get("auto_advance") is not False or workflow.get("_auto_chain_active") is not False:
            errors.append("v04-handoff-auto: both automatic-advance flags must remain false")
    except (KeyError, TypeError, ValueError, UnicodeError):
        errors.append("v04-handoff-auto: planning config or both false auto flags are missing")

    state_handoff = markdown_section(state, "Owner Handoff")
    project_state = markdown_section(project, "Current State")
    current_handoff = markdown_section(continuation, "Owner Handoff") or continuation
    state_norm = " ".join(state_handoff.lower().split())
    project_norm = " ".join(project_state.lower().split())
    continuation_norm = " ".join(continuation.lower().split())
    if not all(value in state_norm for value in ("phase 22", "historical verification", "phase 20", "stale", "phase 21", "stale")):
        errors.append("v04-handoff-stale: current state must mark Phase 20/21 reports stale and Phase 22 report historical")
    required_pending = ("FIXT-01", "RIGHTS-01", "DIAG-01", "DIAG-02")
    for document_name, text in (("STATE", state_handoff), ("PROJECT", project_state), ("continuation", current_handoff)):
        normalized = " ".join(text.lower().split())
        if "pending" not in normalized or not all(req.lower() in normalized for req in required_pending):
            errors.append(f"v04-handoff-pending: {document_name} must preserve all four Pending requirements")
    for req, owner in V04_PENDING_OWNERS.items():
        line_found = any(req in line and owner.lower() in line.lower() and "pending" in line.lower()
                         for line in state_handoff.splitlines())
        if not line_found:
            errors.append(f"v04-handoff-owner: current STATE handoff must retain {req} as Pending under {owner}")
    if "v0.4 remains open" not in state_norm or "v0.4 remains open" not in project_norm:
        errors.append("v04-handoff-open: STATE and PROJECT must keep the v0.4 milestone open")
    if not all(term in state_norm for term in ("exact-final-head full-suite", "unfulfilled", "no broad local suite",
                                               "no third local lifecycle retest", "no release retry", "no tag/asset/rights action")):
        errors.append("v04-handoff-stops: preserved final-suite, lifecycle, publication, tag, asset, and rights stops are incomplete")
    route = "/gsd-audit-milestone v0.4"
    if route not in state_handoff or route not in continuation or "owner-only" not in continuation_norm:
        errors.append("v04-handoff-route: current handoff must preserve the owner-only audit route")
    if "no next phase or milestone is selected" not in continuation_norm or "phase 23.1" not in continuation_norm:
        errors.append("v04-handoff-phase: continuation must close Phase 23.1 without selecting or starting another phase")
    for path, text in ((state_path, state), (project_path, project), (continuation_path, continuation)):
        if report_path and not has_local_link(text, path, report_path):
            errors.append(f"v04-handoff-link: {path.rsplit('/', 1)[-1]} does not link to the Phase 22 report")
    if not report or "full milestone closure remains unsatisfied" not in " ".join(report.lower().split()):
        errors.append("v04-handoff-report: current handoff report is missing or overstates milestone completion")
    return "v04-reconciliation pass stage=handoff", errors


def check_v04_reconciliation(repo: Path, stage: str, rev: str, baseline_rev: str) -> tuple[str, list[str]]:
    if stage not in ("report", "handoff"):
        return "", ["v04-reconciliation-stage: stage must be report or handoff"]
    if not FULL_COMMIT.fullmatch(baseline_rev):
        return "", ["v04-reconciliation-baseline: --baseline-rev must be a full 40-hex commit id"]
    paths, error = commit_paths(repo, rev)
    if error:
        return "", [error]
    baseline_paths, error = commit_paths(repo, baseline_rev)
    if error:
        return "", ["v04-reconciliation-baseline: --baseline-rev is not a readable commit"]
    assert paths is not None and baseline_paths is not None
    if stage == "report":
        return check_v04_report(repo, rev, baseline_rev, paths, baseline_paths)
    return check_v04_handoff(repo, rev, baseline_rev, paths, baseline_paths)


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
    roadmap_contract = " ".join(roadmap.lower().split())
    approved_v04_exception = (
        caps == V04_APPROVED_PHASE_CAPS
        and V04_EXCEPTION_TEXT in roadmap_contract
        and "see d-193" in roadmap_contract
    )
    if len(caps) > PHASE_COUNT_MAX and not approved_v04_exception:
        errors.append(f"plan-cap-phase-count: the active milestone lists {len(caps)} phases, above {PHASE_COUNT_MAX}")
        if set(caps) == set(V04_APPROVED_PHASE_CAPS):
            errors.append("plan-cap-approved-exception: the Phase 23.1 exception requires the exact D-193 phase set, caps, and roadmap approval")
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
        _, errors = check_plan_cap(roadmap_text([("16", "2"), ("17", "2"), ("18", "2"), ("19", "2"), ("20", "2"), ("21", "2")]), phases("six", {}))
        expect("a sixth active phase fails", errors, "plan-cap-phase-count")
        approved_caps = [("20", "9"), ("21", "8"), ("22", "12"), ("23", "10"), ("23.1", "1")]
        approved_tree = phases("approved-v04", {"20": 8, "21": 7, "22": 11, "23": 9, "23.1": 0},
                               {"20": 1, "21": 1, "22": 1, "23.1": 1})
        approved_roadmap = roadmap_text(approved_caps).replace(
            "## Progress", "The owner approved one exact exception for the active v0.4 phase set 20/21/22/23/23.1. See D-193.\n\n## Progress")
        summary, errors = check_plan_cap(approved_roadmap, approved_tree)
        expect("the exact owner-approved v0.4 fifth phase passes", errors, None)
        if summary != "plan-cap pass phases=5 plans=39":
            raise SystemExit(f"planning-hygiene self-test FAIL: unexpected approved v0.4 pass line {summary!r}")
        substituted = roadmap_text([("20", "9"), ("21", "8"), ("22", "12"), ("23", "10"), ("23.2", "1")]).replace(
            "## Progress", "The owner approved one exact exception for the active v0.4 phase set 20/21/22/23/23.1. See D-193.\n\n## Progress")
        _, errors = check_plan_cap(substituted, phases("substituted-v04", {}))
        expect("a substituted fifth phase is rejected", errors, "plan-cap-phase-count")
        _, errors = check_plan_cap(roadmap_text(approved_caps), phases("wrong-fifth-allocation", {}))
        expect("the fifth phase requires the exact approved cap allocation", errors, "plan-cap-phase-count")
        expect("a changed allocation has a specific exception refusal", errors, "plan-cap-approved-exception")
        _, errors = check_plan_cap(roadmap_text(approved_caps).replace(
            "## Progress", "The owner approved one exact exception for the active v0.4 phase set 20/21/22/23/23.1.\n\n## Progress"),
            phases("missing-d193", {}))
        expect("the fifth phase requires an explicit D-193 roadmap exception", errors, "plan-cap-phase-count")
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
        controls += self_test_v04_reconciliation(base, repo)

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
            mutant = normalized.replace(pin, "")
            if mutant == normalized:
                raise SystemExit(f"planning-hygiene self-test FAIL: deferral pin mutant was not seeded: {pin}")
            _, errors = check_deferrals(mutant)
            expected = f"deferral-unrecorded: {pin}"
            if errors != [expected]:
                raise SystemExit(f"planning-hygiene self-test FAIL: omission of {pin!r} gave {errors}")
            controls += 1

        duplicated = normalized + " RM-032"
        _, errors = check_deferrals(duplicated)
        if errors:
            raise SystemExit(f"planning-hygiene self-test FAIL: duplicate identifier rejected: {errors}")
        _, errors = check_deferrals(duplicated.replace("RM-032", ""))
        if errors != ["deferral-unrecorded: RM-032"]:
            raise SystemExit(f"planning-hygiene self-test FAIL: duplicate identifier omission: {errors}")
        controls += 2

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

    # The same immutable reader must follow a completed archive, while a missing
    # archive, an active requirement or leftover live plan cannot mask an invalid roadmap.
    git("checkout", "-q", good_rev)
    archive_root = ".planning/milestones/v0.3"
    archive_files = {archive_root + "-ROADMAP.md": good[".planning/ROADMAP.md"],
                     PHASES_AT_REV + "/.gitkeep": "",
                     ".planning/ROADMAP.md": "# Roadmap\n\n## Milestones\n\nv0.3 shipped.\n",
                     ".planning/STATE.md": "---\nmilestone: v0.3\nstatus: milestone_completed\n---\n"}
    for name, content in good.items():
        if name.startswith(PHASES_AT_REV + "/"):
            archive_files[archive_root + "-phases/" + name[len(PHASES_AT_REV) + 1:]] = content
    git("rm", "-q", "-r", PHASES_AT_REV)
    archived_rev = commit(archive_files, "archive completed milestone")
    expect_rev("completed archive", archived_rev, None)
    # Dirty live files and the current checkout must never replace committed boundary facts.
    (repo / ".planning/ROADMAP.md").write_text("broken working tree", encoding="utf-8")
    expect_rev("archive ignores working-tree roadmap", archived_rev, None)
    git("checkout", "-q", "--", ".planning/ROADMAP.md")
    active_req_rev = commit({".planning/REQUIREMENTS.md": "active requirement\n"}, "active requirements cannot use archive")
    expect_rev("active requirements cannot fall back to archive", active_req_rev, "plan-cap-vacuous")
    git("checkout", "-q", archived_rev)
    live_plan_rev = commit({dir17 + "17-01-PLAN.md": PRIMARY_FRONTMATTER_TEXT}, "leftover live plan")
    expect_rev("live phase records cannot fall back to archive", live_plan_rev, "plan-cap-vacuous")
    git("checkout", "-q", archived_rev)
    git("rm", "-q", archive_root + "-ROADMAP.md")
    git("commit", "-q", "-m", "missing archive roadmap")
    refused("missing archive roadmap", git("rev-parse", "HEAD"), "archived roadmap")
    git("checkout", "-q", archived_rev)
    over_cap_archive_rev = commit({archive_root + "-ROADMAP.md": roadmap_text([("16", "8"), ("17", "2")])},
                                  "archived plans exceed cap")
    expect_rev("archive still enforces plan cap", over_cap_archive_rev, "plan-cap-exceeded")
    expect_rev("earlier archive stays valid", archived_rev, None)
    return controls


def self_test_v04_reconciliation(base: Path, source_repo: Path) -> int:
    """Exercise report/handoff contracts through the real CLI in a disposable Git repository."""
    controls = 0
    source_repo = source_repo.resolve()
    object_result = git_run(source_repo, "rev-parse", "--git-path", "objects")
    if object_result.returncode != 0:
        raise SystemExit("planning-hygiene self-test FAIL: could not resolve source Git object directory")
    object_dir = Path(object_result.stdout.decode("utf-8", errors="replace").strip())
    if not object_dir.is_absolute():
        object_dir = (source_repo / object_dir).resolve()
    for needed in (V04_IMPLEMENTATION_HEAD, V04_EVIDENCE_HEAD):
        if git_run(source_repo, "cat-file", "-t", needed).stdout.strip() != b"commit":
            raise SystemExit(f"planning-hygiene self-test FAIL: required immutable Phase 22 object is unavailable: {needed}")

    repo = base / "v04-reconciliation-repo"
    repo.mkdir()
    env = {key: value for key, value in os.environ.items() if key in ("PATH", "SYSTEMROOT", "TMPDIR", "TEMP", "TMP")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, GIT_AUTHOR_NAME="fixture",
               GIT_AUTHOR_EMAIL="fixture@example.invalid", GIT_COMMITTER_NAME="fixture",
               GIT_COMMITTER_EMAIL="fixture@example.invalid")

    def git(*args: str) -> str:
        done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                              check=True, env=env, timeout=60)
        return done.stdout.strip()

    git("init", "-q")
    alternate = repo / ".git" / "objects" / "info" / "alternates"
    alternate.parent.mkdir(parents=True, exist_ok=True)
    alternate.write_text(str(object_dir) + "\n", encoding="utf-8")

    phase_dirs = {number: f".planning/phases/GB-{number}-fixture" for number in ("20", "21", "22", "23", "23.1")}
    roadmap = roadmap_text(list(V04_APPROVED_PHASE_CAPS.items())).replace(
        "## Progress", f"The owner approved one exact exception for the active v0.4 phase set 20/21/22/23/23.1. See D-193.\n\n## Progress")
    requirements = """# Requirements

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FIXT-01 | Phase 21 | Pending |
| RIGHTS-01 | Phase 20 | Pending |
| DIAG-01 | Phase 22 | Pending |
| DIAG-02 | Phase 22 | Pending |
"""
    base_files: dict[str, str] = {
        ".planning/ROADMAP.md": roadmap,
        ".planning/REQUIREMENTS.md": requirements,
        ".planning/config.json": json.dumps({"workflow": {"auto_advance": False, "_auto_chain_active": False}}) + "\n",
        ".planning/v0.4-MILESTONE-AUDIT.md": "Historical audit snapshot: gaps found.\n",
        ".planning/STATE.md": """---
milestone: v0.4
current_phase: "23.1"
current_phase_name: Close v0.4 requirement and verification gaps
status: executing
---

## Owner Handoff

The milestone stays open. Phase 22's historical report is not yet present. Phase 20 and Phase 21 reports remain stale. FIXT-01, RIGHTS-01, DIAG-01, and DIAG-02 remain Pending.
""",
        ".planning/PROJECT.md": """## Current State

The v0.4 milestone remains open. Four requirements remain Pending.
""",
        f"{phase_dirs['20']}/20-VERIFICATION.md": "Phase 20 historical report: stale.\n",
        f"{phase_dirs['21']}/21-VERIFICATION.md": "Phase 21 historical report: stale.\n",
        f"{phase_dirs['22']}/22-EVIDENCE.md": "Phase 22 source evidence snapshot.\n",
        f"{phase_dirs['22']}/22-SOURCE-AUDIT.md": "Phase 22 source audit snapshot.\n",
        f"{phase_dirs['23']}/.continue-here.md": "Historical Phase 23 continuation; unchanged.\n",
        f"{phase_dirs['23.1']}/23.1-01-PLAN.md": "---\ngap_closure: true\n---\n",
    }
    for name in V04_PHASE22_SUMMARIES:
        base_files[f"{phase_dirs['22']}/{name}"] = f"{name} immutable summary.\n"

    def commit(files: dict[str, str], message: str) -> str:
        for relative, content in files.items():
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode("utf-8"))
            git("add", relative)
        git("commit", "-q", "-m", message)
        return git("rev-parse", "HEAD")

    baseline_rev = commit(base_files, "fixture baseline")

    def artifact_link(name: str) -> str:
        return f"[{name}]({name})"

    gates = "\n".join(f"  - {gate}" for gate in V04_UNRESOLVED_GATES)
    dispositions = "\n".join(f"  - id: {requirement}\n    status: Pending\n    original_owner: {owner}"
                             for requirement, owner in V04_PENDING_OWNERS.items())
    report_content = f"""---
phase: GB-22-composition-and-microtest-evidence
source_head: {V04_EVIDENCE_HEAD}
implementation_head: {V04_IMPLEMENTATION_HEAD}
evidence_head: {V04_EVIDENCE_HEAD}
report_kind: boundary_reconstruction
status: passed
metadata_cases: 513
shared_macro_cases: 480
inline_cases: 2
initial_no_protocol_exclusions: 31
admitted: 0
executed: 0
unresolved_gates:
{gates}
requirements_satisfied: []
requirement_dispositions:
{dispositions}
---

## Historical reconstruction scope

This is a historical reconstruction of the approved synthetic-plus-metadata Phase 22 scope. The metadata-only assessment never admitted or executed a real diagnostic fixture.

## Goal Achievement

| Phase 22 roadmap criterion | Historical status | Evidence and limits |
|---|---|---|
| 1. The original compiled synthetic composition tracer preserves source-cell mask, identity, and image controls. | **VERIFIED** | See {artifact_link('22-01-SUMMARY.md')} and {artifact_link('22-EVIDENCE.md')}. The recorded compiled tracer check covers the source-cell mask and identity/image controls. |
| 2. The full 513-name metadata inventory records seven gates, admitted=0, and executed=0. | **VERIFIED** | See {artifact_link('22-02-SUMMARY.md')}, {artifact_link('22-10-SUMMARY.md')}, and {artifact_link('22-SOURCE-AUDIT.md')}. The 482 protocol candidates remain blocked. |
| 3. Documentation and automated checks keep the tracer labeled synthetic-only, record the real-fixture no-go without asserting a license prohibition, and leave DIAG-01, DIAG-02, and RIGHTS-01 Pending. | **VERIFIED** | See {artifact_link('22-11-SUMMARY.md')} and {artifact_link('22-12-SUMMARY.md')}. Synthetic-only claims describe no real game or diagnostic evidence. |

The other recorded Phase 22 summaries are {artifact_link('22-11-SUMMARY.md')} and {artifact_link('22-12-SUMMARY.md')}.

## Exact game no-go facts

Potion Panic's creator-linked repository failed before a ref/commit was returned and its fork is not source authority; source/build/ROM/header/mode/predicate/observations remain unobserved. For µCity 1.3, source `d1880a2a112d7c26f16c0fc06a15b6c32fdc9137` was inspected, but required `source/engine/hardware.inc` lacks an identified grant/notice; no upstream tool/ROM ran and no ROM/header/mode/predicate/receipt was produced. These are missing-evidence no-go outcomes.

## Requirement truth and preserved limits

No license prohibition or fixture permission is inferred. FIXT-01, RIGHTS-01, DIAG-01, and DIAG-02 remain Pending with their original owners. Hardware, perceptual, timing, Linux, Steam Deck, and Playstead support remain unqualified. Full milestone closure remains unsatisfied.
"""
    report_path = f"{phase_dirs['22']}/22-VERIFICATION.md"
    no_report_exit, no_report_out = 0, (io.StringIO(), io.StringIO())
    with contextlib.redirect_stdout(no_report_out[0]), contextlib.redirect_stderr(no_report_out[1]):
        no_report_exit = main(["--check", "v04-reconciliation", "--stage", "report", "--rev", baseline_rev,
                               "--baseline-rev", baseline_rev, "--repo", str(repo)])
    if no_report_exit != 1 or "v04-report-missing" not in no_report_out[1].getvalue():
        raise SystemExit(f"planning-hygiene self-test FAIL: missing Phase 22 report was not rejected: {no_report_out[0].getvalue()} {no_report_out[1].getvalue()}")
    controls += 1

    report_rev = commit({report_path: report_content}, "add historical report")

    def cli_check(stage: str, rev: str, expected_code: str | None = None) -> None:
        nonlocal controls
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            result = main(["--check", "v04-reconciliation", "--stage", stage, "--rev", rev,
                           "--baseline-rev", baseline_rev, "--repo", str(repo)])
        if expected_code is None:
            expected_line = f"v04-reconciliation pass stage={stage}"
            if result != 0 or output.getvalue().strip() != expected_line:
                raise SystemExit(f"planning-hygiene self-test FAIL: {stage} CLI positive: {result} {output.getvalue()} {error.getvalue()}")
        elif result != 1 or expected_code not in error.getvalue():
            raise SystemExit(f"planning-hygiene self-test FAIL: {stage} CLI negative wanted {expected_code}: {result} {output.getvalue()} {error.getvalue()}")
        controls += 1

    cli_check("report", report_rev)
    first_disposition = "\n".join(dispositions.splitlines()[:3])
    for label, mutated, error_code in (
        ("wrong phase", report_content.replace("phase: GB-22-composition-and-microtest-evidence",
                                                 "phase: GB-21-cgb-game-progress-and-scene-regressions", 1), "v04-report-field"),
        ("wrong status", report_content.replace("status: passed", "status: complete", 1), "v04-report-field"),
        ("boundary identity", report_content.replace(f"source_head: {V04_EVIDENCE_HEAD}", "source_head: " + "0" * 40), "v04-report-field"),
        ("metadata count", report_content.replace("metadata_cases: 513", "metadata_cases: 512"), "v04-report-field"),
        ("gate list", report_content.replace(V04_UNRESOLVED_GATES[-1], "wrong_final_gate"), "v04-report-gates"),
        ("false requirement completion", report_content.replace("    status: Pending", "    status: Satisfied", 1), "v04-report-requirements"),
        ("weakened criterion 3", report_content.replace("DIAG-01, DIAG-02, and RIGHTS-01 Pending",
                                                          "diagnostic and rights requirements Pending", 1), "v04-report-criteria"),
        ("criterion result", report_content.replace("| **VERIFIED** | See [22-01-SUMMARY.md]", "| **PARTIAL** | See [22-01-SUMMARY.md]", 1),
         "v04-report-criteria"),
        ("duplicate gate key", report_content.replace(f"unresolved_gates:\n{gates}",
                                                         f"unresolved_gates:\n{gates}\nunresolved_gates:\n{gates}", 1),
         "v04-report-frontmatter-duplicate"),
        ("duplicate disposition block", report_content.replace(f"requirement_dispositions:\n{dispositions}",
                                                                 f"requirement_dispositions:\n{dispositions}\nrequirement_dispositions:\n{dispositions}", 1),
         "v04-report-frontmatter-duplicate"),
        ("duplicate nested field", report_content.replace("    status: Pending\n    original_owner:",
                                                            "    status: Pending\n    status: Pending\n    original_owner:", 1),
         "v04-report-frontmatter-duplicate"),
        ("duplicate requirement ID", report_content.replace(f"requirement_dispositions:\n{dispositions}",
                                                               f"requirement_dispositions:\n{dispositions}\n{first_disposition}", 1),
         "v04-report-requirements"),
        ("duplicate no-go heading", report_content.replace("## Requirement truth and preserved limits",
                                                              "## Exact game no-go facts\nDuplicate no-go heading.\n\n## Requirement truth and preserved limits", 1),
         "v04-report-heading"),
    ):
        mutated_rev = commit({report_path: mutated}, f"mutate report {label}")
        cli_check("report", mutated_rev, error_code)
    git("checkout", "-q", report_rev)
    changed_history = "Phase 20 historical report was rewritten.\n"
    history_rev = commit({f"{phase_dirs['20']}/20-VERIFICATION.md": changed_history}, "mutate historical report")
    cli_check("report", history_rev, "v04-history-changed")

    git("checkout", "-q", report_rev)
    state_path, project_path = ".planning/STATE.md", ".planning/PROJECT.md"
    phase22_link_state = f"phases/{phase_dirs['22'].rsplit('/', 1)[-1]}/22-VERIFICATION.md"
    phase22_link_project = phase22_link_state
    phase22_link_continuation = f"../{phase_dirs['22'].rsplit('/', 1)[-1]}/22-VERIFICATION.md"
    state_handoff = f"""---
milestone: v0.4
current_phase: "23.1"
current_phase_name: Close v0.4 requirement and verification gaps
status: executing
---

## Owner Handoff

Phase 23.1 reconciliation completed. Phase 22's historical verification report now exists at [{report_path.rsplit('/', 1)[-1]}]({phase22_link_state}). Phase 20 verification is stale and Phase 21 verification is stale. The Phase 22 report remains historical, not refreshed current coverage.

- FIXT-01 — Pending, original owner Phase 21.
- RIGHTS-01 — Pending, original owner Phase 20.
- DIAG-01 — Pending, original owner Phase 22.
- DIAG-02 — Pending, original owner Phase 22.

The v0.4 remains open. D-103's exact-final-head full-suite milestone gate remains unfulfilled. No broad local suite and no third local lifecycle retest are permitted. The publication allowance is spent: no release retry, no tag/asset/rights action. Both auto flags remain false. The owner-only next route is `/gsd-audit-milestone v0.4`.
"""
    project_state = f"""## Current State

Phase 22's historical verification is available at [{report_path.rsplit('/', 1)[-1]}]({phase22_link_project}). The v0.4 remains open. FIXT-01, RIGHTS-01, DIAG-01, and DIAG-02 remain Pending.
"""
    continuation_path = f"{phase_dirs['23.1']}/.continue-here.md"
    continuation = f"""# Phase 23.1 Closeout

## Owner Handoff

Completed stage: Phase 23.1 — Close v0.4 requirement and verification gaps. The historical report is [{report_path.rsplit('/', 1)[-1]}]({phase22_link_continuation}). FIXT-01, RIGHTS-01, DIAG-01, and DIAG-02 remain Pending; the D-103 exact-final-head suite is unfulfilled. No broad local suite, third local lifecycle retest, release retry, or tag/asset/rights action is allowed. Both auto flags remain false.

The next command is owner-only: `/gsd-audit-milestone v0.4`. No next phase or milestone is selected or started.
"""
    handoff_files = {state_path: state_handoff, project_path: project_state, continuation_path: continuation}
    handoff_rev = commit(handoff_files, "reconcile current handoff")
    cli_check("handoff", handoff_rev)
    missing_link_rev = commit({state_path: state_handoff.replace(f"]({phase22_link_state})", "](#missing-report)")},
                              "remove current report link")
    cli_check("handoff", missing_link_rev, "v04-handoff-link")
    git("checkout", "-q", handoff_rev)
    duplicate_handoff_rev = commit({state_path: state_handoff + "\n## Owner Handoff\n\nDuplicate heading.\n"},
                                   "duplicate current owner handoff")
    cli_check("handoff", duplicate_handoff_rev, "v04-handoff-heading")
    git("checkout", "-q", handoff_rev)
    config = json.loads((repo / ".planning/config.json").read_text(encoding="utf-8"))
    config["workflow"]["auto_advance"] = True
    auto_rev = commit({".planning/config.json": json.dumps(config) + "\n"}, "enable auto advance")
    cli_check("handoff", auto_rev, "v04-handoff-auto")
    git("checkout", "-q", handoff_rev)
    bad_pending = state_handoff.replace("RIGHTS-01 — Pending", "RIGHTS-01 — Complete")
    pending_rev = commit({state_path: bad_pending}, "complete pending requirement")
    cli_check("handoff", pending_rev, "v04-handoff-owner")

    # Later committed and dirty state must not affect a verdict bound to report_rev.
    git("checkout", "-q", handoff_rev)
    later_rev = commit({".planning/ROADMAP.md": roadmap + "\nLater checkout text.\n"}, "later planning checkout")
    (repo / f"{phase_dirs['22']}/22-EVIDENCE.md").write_text("dirty evidence must not replace snapshots\n", encoding="utf-8")
    cli_check("report", report_rev)
    if not later_rev:
        raise SystemExit("planning-hygiene self-test FAIL: missing later checkout commit")
    return controls


# ---- CLI -------------------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", choices=("plan-cap", "lessons-ids", "state-size", "playstead-docs", "deferrals", "v04-reconciliation"))
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--roadmap")
    parser.add_argument("--phases-dir")
    parser.add_argument("--rev", help="a full immutable commit id to read")
    parser.add_argument("--stage", choices=("report", "handoff"), help="v04-reconciliation stage to check")
    parser.add_argument("--baseline-rev", help="execution-start commit used to protect historical planning evidence")
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
        elif args.check == "v04-reconciliation":
            if not args.stage or not args.rev or not args.baseline_rev:
                parser.error("v04-reconciliation needs --stage report|handoff --rev COMMIT --baseline-rev COMMIT")
            summary, errors = check_v04_reconciliation(Path(args.repo), args.stage, args.rev, args.baseline_rev)
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
