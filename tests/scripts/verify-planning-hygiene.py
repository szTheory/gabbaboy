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
  --check v04-gap-assessment --stage report|handoff --rev COMMIT --baseline-rev COMMIT [--repo DIR]
      Checks the additive Phase 24 eight-requirement assessment and pending-verification handoff from commits.
      The input, protected Phase 20/21 history, and later containing candidates are distinct identities.
      Prints "v04-gap-assessment pass stage=report|handoff".

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
import hashlib
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
V04_D205_PHASE_CAPS = {**V04_APPROVED_PHASE_CAPS, "24": 1}
V04_D205_EXCEPTION_TEXT = "the owner approved only the exact active v0.4 phase set 20/21/22/23/23.1/24"
V04_D205_PHASE24_PLAN_LINE = "**Plans:** Exactly one ordinary plan (`24-01-PLAN.md`); no Phase 24 gap reserve."
V04_D205_DECISION_HEADING = "## D-205 — One Phase 24 rescope for remaining v0.4 gaps (2026-11-16)"
V04_D205_DECISION_BODY = (
    "The owner authorized one Phase 24 rescope for the four Pending requirements and stale Phase 20/21 verification. "
    "This supersedes D-193/D-203 only on the prohibition against adding a sixth v0.4 phase. "
    "The phase discussion and plan must keep original requirement ownership and preserve all other limits: "
    "total plan capacity does not exceed 40; no broad suite or third lifecycle retest; no release retry, tag, or asset "
    "changes; and no fixture admission or rights action without a separate explicit authorization. "
    "This rescope does not accept any requirement gap or authorize milestone archival/cleanup. "
    "Both auto-advance flags remain false."
)

PHASE_HEADING = re.compile(r"^### Phase (\d+(?:\.\d+)?):")
CAP_LINE = re.compile(r"^\*\*Plan cap\*\*: (\d+)[ \t]*$")
# A plan is any NN-<digit-led id>-PLAN*.md file: the canonical NN-NN-PLAN.md and suffixed forms such as NN-NNa-PLAN.md or
# NN-NN-PLAN-extra.md count too, so a plan cannot dodge the cap by its name. NN-PLAN-CHECK.md (no id) is not a plan.
PLAN_FILE = re.compile(r"^(\d+(?:\.\d+)?)-\d[^/\\]*-PLAN[^/\\]*\.md$", re.IGNORECASE)
GAP_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.DOTALL)
V04_GAP_HANDOFF_SUMMARY_KEYS = frozenset((
    "phase", "plan", "subsystem", "tags", "requires", "provides", "affects", "actuals",
    "plan_head_before", "plan_head_after", "tech-stack", "key-files", "key-decisions",
    "patterns-established", "requirements-completed", "coverage", "duration", "completed", "status",
))
FULL_COMMIT = re.compile(r"[0-9a-f]{40}")
PHASE_DIR = re.compile(r"^GB-(\d+(?:\.\d+)?)-")
LESSON_HEADING = re.compile(r"^### ([A-Z0-9]+(?:-[A-Z0-9]+)+) / ")

DATA = Path(__file__).resolve().parents[1] / "data" / "planning-hygiene"


def markdown_source_lines(text: str) -> list[str]:
    """Normalize Markdown line endings and split only on CommonMark line endings."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized:
        return []
    lines = normalized.split("\n")
    if lines[-1] == "":
        lines.pop()
    return lines


def phase_details(roadmap: str) -> list[str] | None:
    """Active phase lines, including the D-205 Phase 24 block appended to the approval boundary."""
    lines = markdown_source_lines(roadmap)
    active: list[str] | None = None
    for start, line in enumerate(lines):
        if re.fullmatch(r" {0,3}##[ \t]+Phase Details[ \t]*", line):
            end = len(lines)
            for stop in range(start + 1, len(lines)):
                if re.match(r"^ {0,3}##[ \t]+", lines[stop]):
                    end = stop
                    break
            active = lines[start + 1:end]
            break
    if active is None:
        return None
    # Phase 24's reviewed one-plan record currently sits below the planning/approval
    # boundary. Include active headings there so the immutable cap check sees D-205's
    # sixth phase instead of silently treating its plans as orphaned.
    boundary = next((index for index, line in enumerate(lines)
                     if re.fullmatch(r" {0,3}##[ \t]+Planning and Approval Boundary[ \t]*", line)), None)
    if boundary is not None:
        extra_start = next((index for index in range(boundary + 1, len(lines))
                            if PHASE_HEADING.match(lines[index])), None)
        if extra_start is not None:
            active.extend(lines[extra_start:])
    return active


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
    """Parse the one supported root boolean; fail closed on aliases or malformed declarations."""
    normalized, _ = yaml_source_lines(text)
    match = GAP_FRONTMATTER.match(normalized)
    if match is None:
        return False
    declaration: str | None = None
    _, lines = yaml_source_lines(match.group(1))
    for line in lines:
        if not line or line[0] in " \t" or line.startswith("#"):
            continue
        key = parse_frontmatter_plain_key(line)
        alias = _frontmatter_root_key_is_alias(line, "gap_closure")
        if key != "gap_closure" and not alias:
            if key is None and re.search(r"(?<![A-Za-z0-9_-])gap_closure(?![A-Za-z0-9_-])", line):
                return True
            continue
        if key != "gap_closure" or not line.startswith("gap_closure:") or declaration is not None:
            return True
        declaration = line[len("gap_closure:"):]
    if declaration is None:
        return False
    value = yaml_horizontal_strip(declaration)
    if re.fullmatch(r"true(?:[ \t]+#.*)?", value, re.IGNORECASE):
        return True
    if re.fullmatch(r"false(?:[ \t]+#.*)?", value, re.IGNORECASE):
        return False
    return True


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


def read_rev(repo: Path, rev: str) -> tuple[str, PlanTree, str | None]:
    """Read the roadmap, plan tree, and D-205 authority from one immutable commit."""
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
    decisions = git_run(repo, "show", f"{rev}:.planning/context/DECISIONS.md")
    decision_text = decisions.stdout.decode("utf-8", errors="strict") if decisions.returncode == 0 else None
    return roadmap.stdout.decode("utf-8"), tree, decision_text


V04_IMPLEMENTATION_HEAD = "ca2f0be6b38e7dd22e0eb3296b9a21cceed1a765"
V04_IMPLEMENTATION_TREE = "e768b7ec26d7c07542d6aa29aef53ae8fc826c5e"
V04_EVIDENCE_HEAD = "d18db4c56d2a79e6138df37a9d16e3d346a86e13"
V04_PENDING_OWNERS = {"FIXT-01": "Phase 21", "RIGHTS-01": "Phase 20",
                      "DIAG-01": "Phase 22", "DIAG-02": "Phase 22"}
V04_GAP_INPUT_REV = "f511baa8c0330f5cd90d56da55d79dbc873b0559"
V04_GAP_REPORT_PATH = ".planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-EVIDENCE.md"
V04_GAP_AUDIT_PATH = ".planning/v0.4-MILESTONE-AUDIT.md"
V04_GAP_REQUIREMENTS_PATH = ".planning/REQUIREMENTS.md"
V04_GAP_SOURCE_PATHS = (
    V04_GAP_REQUIREMENTS_PATH,
    V04_GAP_AUDIT_PATH,
    ".planning/context/DECISIONS.md",
    ".planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CONTEXT.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-VERIFICATION.md",
    ".planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-VERIFICATION.md",
    ".planning/phases/GB-22-composition-and-microtest-evidence/22-VERIFICATION.md",
    ".planning/phases/GB-23-qualified-v0-4-0-release/23-VERIFICATION.md",
    ".planning/phases/GB-23.1-close-v0-4-requirement-and-verification-gaps/23.1-VERIFICATION.md",
)
V04_GAP_REQUIREMENT_FIELDS = frozenset((
    "id", "original_criterion", "original_owner", "tracker_status", "milestone_audit_status",
    "historical_report_path", "historical_report_status", "historical_requirement_result",
    "current_freshness", "evidence_boundary", "remaining_gate",
))
V04_GAP_PHASE_FIELDS = frozenset((
    "phase", "historical_report_path", "historical_report_status", "historical_source_identity",
    "current_audit_observation", "changed_covered_file_categories", "outstanding_full_verification_gate",
))
V04_GAP_EXPECTED = {
    "GAME-01": ("Phase 21", "Complete", "partial", "runner satisfaction", "stale",
                "Fresh full Phase 21 verification remains outside this assessment; the audit stays partial."),
    "GAME-02": ("Phase 21", "Complete", "partial", "harness-only satisfaction", "stale",
                "Fresh full Phase 21 verification remains outside this assessment; the audit stays partial."),
    "FIXT-01": ("Phase 21", "Pending", "unsatisfied", "bounded no-go override", "stale",
                "Separately authorized work must establish exact source/build, ROM digest, cartridge header, native CGB mode, and the bounded candidate outcome."),
    "RIGHTS-01": ("Phase 20", "Pending", "unsatisfied", "admission-boundary pass with no admitted fixture", "stale",
                  "Separate authorization is required for component-specific repository/public-CI redistribution and admission authority."),
    "DIAG-01": ("Phase 22", "Pending", "unsatisfied", "approved metadata-only scope passed; no derivative admitted", "not_evaluated",
                "Separately authorized work must establish admitted derivative composition, source/build provenance, and rights."),
    "DIAG-02": ("Phase 22", "Pending", "unsatisfied", "approved metadata-only scope passed; no case executed", "not_evaluated",
                "Separately authorized work must establish exact eligible case source/bytes, terms, model applicability, and eligible/executed/excluded accounting."),
    "FEED-01": ("Phase 21", "Complete", "partial", "workflow-contract satisfaction", "stale",
                "Fresh full Phase 21 verification remains outside this assessment; the audit stays partial."),
    "REL-01": ("Phase 23", "Complete", "satisfied", "release verification passed", "passed",
               "No requirement-specific gate is recorded; D-103 remains an independent milestone gate."),
}
V04_GAP_HISTORICAL_REPORTS = {
    "GAME-01": ".planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-VERIFICATION.md",
    "GAME-02": ".planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-VERIFICATION.md",
    "FIXT-01": ".planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-VERIFICATION.md",
    "RIGHTS-01": ".planning/phases/GB-20-fixture-admission-tune-up/20-VERIFICATION.md",
    "DIAG-01": ".planning/phases/GB-22-composition-and-microtest-evidence/22-VERIFICATION.md",
    "DIAG-02": ".planning/phases/GB-22-composition-and-microtest-evidence/22-VERIFICATION.md",
    "FEED-01": ".planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-VERIFICATION.md",
    "REL-01": ".planning/phases/GB-23-qualified-v0-4-0-release/23-VERIFICATION.md",
}
V04_GAP_PHASE_IDENTITY_FIELDS = {"20": ("source_head", "verification_head"),
                                 "21": ("verified", "covered_digest")}
V04_REPORT_EXPECTED_FIELDS = {
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
V04_PROTECTED_ROOT_KEYS = frozenset(V04_REPORT_EXPECTED_FIELDS) | frozenset(
    ("unresolved_gates", "requirement_dispositions", "requirements", "report_kind",
     "assessment_input_commit", "baseline_commit", "milestone", "milestone_status",
     "milestone_audit_status", "phase_completion_scope", "requirements_satisfied_by_phase",
     "refreshes_phase20_21", "satisfies_d103", "source_records", "requirement_assessments",
     "phase_assessments"))
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


def cache_fixture_commit_snapshot(repo: Path, parent_rev: str | None, rev: str,
                                  files: dict[str, bytes | str], deleted: tuple[str, ...] = ()) -> None:
    """Cache a test-only committed snapshot from its immutable parent plus the fixture's exact written blobs."""
    if parent_rev is None:
        snapshot: dict[str, bytes] = {}
    else:
        parent, error = commit_snapshot(repo, parent_rev)
        if parent is None:
            raise SystemExit(f"planning-hygiene self-test FAIL: fixture parent snapshot unavailable: {error}")
        snapshot = dict(parent)
    for path, content in files.items():
        snapshot[path] = content if isinstance(content, bytes) else content.encode("utf-8")
    for path in deleted:
        snapshot.pop(path, None)
    COMMIT_SNAPSHOT_CACHE[(str(repo.resolve()), rev)] = snapshot


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


def yaml_source_lines(text: str) -> tuple[str, list[str]]:
    """Normalize YAML line endings and split only its LF, CR, or CRLF boundaries."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized:
        return normalized, []
    lines = normalized.split("\n")
    if lines[-1] == "":
        lines.pop()
    return normalized, lines


def yaml_horizontal_strip(value: str) -> str:
    """Trim only YAML's horizontal token whitespace, never Unicode scalar content."""
    return value.strip(" \t")


def parse_frontmatter_plain_key(line: str) -> str | None:
    """Read the fixed schema's plain key spelling before an optional spaced colon."""
    match = re.match(r"^([A-Za-z0-9_-]+)[ \t]*:", line)
    return match.group(1) if match is not None else None


def decode_frontmatter_scalar(raw: str) -> str | None:
    """Decode exact plain text or the supported, unescaped matching quote subset."""
    value = yaml_horizontal_strip(raw)
    starts_quoted = bool(value) and value[0] in "\"'"
    ends_quoted = bool(value) and value[-1] in "\"'"
    if not starts_quoted and not ends_quoted:
        return value
    # A quote at the end of an otherwise plain scalar is content (and must not
    # disappear into the expected value); quoted syntax begins only at column 1.
    if not starts_quoted:
        return value
    if not ends_quoted or value[0] != value[-1]:
        return None
    quote = value[0]
    inner = value[1:-1]
    if quote in inner:
        return None
    if quote == '"' and "\\" in inner:
        return None
    return inner


def _frontmatter_block_scalar_indent(raw: str, parent_indent: int) -> int | None:
    """Return the minimum indentation for this fixed reader's supported block scalars."""
    value = decode_frontmatter_scalar(raw)
    if value is None:
        return None
    marker = re.fullmatch(r"[|>](?:[+-][1-9]?|[1-9][+-]?)?", value)
    if marker is None:
        return None
    digit = next((int(char) for char in value if char in "123456789"), None)
    return parent_indent + digit if digit is not None else parent_indent


def frontmatter_fields(text: str) -> tuple[dict[str, str], str]:
    normalized, _ = yaml_source_lines(text)
    match = GAP_FRONTMATTER.match(normalized)
    if match is None:
        return {}, normalized
    fields: dict[str, str] = {}
    _, lines = yaml_source_lines(match.group(1))
    # Never collapse duplicate root pairs into a dict before the validator sees them.
    if frontmatter_duplicates(text):
        return fields, normalized[match.end():]
    for line in lines:
        key = parse_frontmatter_plain_key(line)
        if key is not None:
            colon = line.find(":")
            value = decode_frontmatter_scalar(line[colon + 1:])
            if value is not None:
                fields[key] = value
    return fields, normalized[match.end():]


def closed_frontmatter_root_errors(text: str, allowed_keys: frozenset[str]) -> list[str]:
    """Reject unknown, aliased, decorated, or duplicate root keys in a fixed document schema."""
    normalized, _ = yaml_source_lines(text)
    match = GAP_FRONTMATTER.match(normalized)
    if match is None:
        return ["missing YAML frontmatter"]
    errors: list[str] = []
    seen: set[str] = set()
    _, lines = yaml_source_lines(match.group(1))
    for line in lines:
        if not line or line.startswith("#") or line[0] in " \t":
            continue
        key = parse_frontmatter_plain_key(line)
        if key is None:
            if any(_frontmatter_root_key_is_alias(line, allowed) for allowed in allowed_keys):
                errors.append("unsupported or aliased protected root key syntax")
            else:
                errors.append("unsupported root key syntax")
            continue
        if key not in allowed_keys:
            errors.append(f"unsupported root key '{key}'")
        if not line.startswith(f"{key}:"):
            errors.append(f"noncanonical root key '{key}'")
        if key in seen:
            errors.append(f"duplicate root key '{key}'")
        seen.add(key)
    return errors


def frontmatter_duplicates(text: str) -> list[str]:
    """Return duplicate top-level YAML keys and repeated fields within a sequence object."""
    normalized, _ = yaml_source_lines(text)
    match = GAP_FRONTMATTER.match(normalized)
    if match is None:
        return []
    _, lines = yaml_source_lines(match.group(1))
    top_level: set[str] = set()
    item_fields: set[str] | None = None
    block_scalar_indent: int | None = None
    duplicates: list[str] = []
    for line in lines:
        if block_scalar_indent is not None:
            if not yaml_horizontal_strip(line):
                continue
            indentation = len(line) - len(line.lstrip(" "))
            if indentation > block_scalar_indent:
                continue
            block_scalar_indent = None
        if not yaml_horizontal_strip(line):
            continue
        if line[0] not in " \t":
            item_fields = None
            key = parse_frontmatter_plain_key(line)
            if key is not None:
                if key in top_level:
                    duplicates.append(f"top-level key '{key}'")
                top_level.add(key)
                if key in V04_PROTECTED_ROOT_KEYS and not line.startswith(f"{key}:"):
                    duplicates.append(f"noncanonical protected root key '{key}'")
            elif any(_frontmatter_root_key_is_alias(line, protected)
                     for protected in V04_PROTECTED_ROOT_KEYS):
                # Preserve unsupported root syntax so consumers cannot silently drop it.
                duplicates.append("unsupported or aliased protected root key syntax")
            continue
        item = re.match(r"^[ \t]*-[ \t]+([A-Za-z0-9_-]+)[ \t]*:[ \t]*(.*?)[ \t]*$", line)
        if item:
            item_fields = {item.group(1)}
            block_scalar_indent = _frontmatter_block_scalar_indent(item.group(2), 2)
            continue
        nested_key = parse_frontmatter_plain_key(line.lstrip(" \t"))
        if nested_key is not None and item_fields is not None:
            key = nested_key
            if key in item_fields:
                duplicates.append(f"nested field '{key}'")
            item_fields.add(key)
            colon = line.find(":")
            block_scalar_indent = _frontmatter_block_scalar_indent(line[colon + 1:], 4)
    return duplicates


def frontmatter_sequence(text: str, key: str) -> list[str] | None:
    normalized, _ = yaml_source_lines(text)
    match = GAP_FRONTMATTER.match(normalized)
    if match is None:
        return None
    _, lines = yaml_source_lines(match.group(1))
    if frontmatter_duplicates(text):
        return None
    for index, line in enumerate(lines):
        if line != f"{key}:":
            continue
        values: list[str] = []
        for item in lines[index + 1:]:
            if not yaml_horizontal_strip(item):
                continue
            if not item.startswith((" ", "\t")):
                break
            value = re.match(r"^[ \t]+-[ \t]+(.+?)[ \t]*$", item)
            if value:
                decoded = decode_frontmatter_scalar(value.group(1))
                if decoded is None:
                    return None
                values.append(decoded)
        return values
    return None


def frontmatter_objects(text: str, key: str) -> list[dict[str, str]] | None:
    normalized, _ = yaml_source_lines(text)
    match = GAP_FRONTMATTER.match(normalized)
    if match is None:
        return None
    _, lines = yaml_source_lines(match.group(1))
    if frontmatter_duplicates(text):
        return None
    start = next((index for index, line in enumerate(lines) if line == f"{key}:"), None)
    if start is None:
        return None
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    block_scalar_indent: int | None = None
    for line in lines[start + 1:]:
        horizontal = yaml_horizontal_strip(line)
        if not horizontal or horizontal.startswith("#"):
            continue
        indentation = len(line) - len(line.lstrip(" "))
        if block_scalar_indent is not None:
            if indentation > block_scalar_indent:
                continue
            block_scalar_indent = None
        if line[0] not in " \t":
            if parse_frontmatter_plain_key(line) is None:
                return None
            break
        # The fixed disposition schema accepts only two-space items and four-space
        # members. Every other nonblank row is refused so its members cannot disappear.
        item = re.fullmatch(r" {2}-[ \t]+([A-Za-z0-9_-]+):[ \t]*(.*?)[ \t]*", line)
        if item:
            if current is not None:
                entries.append(current)
            decoded = decode_frontmatter_scalar(item.group(2))
            if decoded is None:
                return None
            current = {item.group(1): decoded}
            block_scalar_indent = _frontmatter_block_scalar_indent(item.group(2), 2)
            continue
        field = re.fullmatch(r" {4}([A-Za-z0-9_-]+):[ \t]*(.*?)[ \t]*", line)
        if field is None or current is None:
            return None
        decoded = decode_frontmatter_scalar(field.group(2))
        if decoded is None:
            return None
        current[field.group(1)] = decoded
        block_scalar_indent = _frontmatter_block_scalar_indent(field.group(2), 4)
    if current is not None:
        entries.append(current)
    return entries


def _decode_frontmatter_key(raw: str) -> str | None:
    """Decode the small quoted-key subset needed to recognize requirements aliases."""
    value = raw.strip(" \t")
    if not value or value[0] not in "\"'":
        return None
    quote = value[0]
    decoded: list[str] = []
    index = 1
    while index < len(value):
        char = value[index]
        if quote == "'":
            if char == "'":
                if index + 1 < len(value) and value[index + 1] == "'":
                    decoded.append("'")
                    index += 2
                    continue
                tail = value[index + 1:].strip(" \t")
                return "".join(decoded) if not tail or tail.startswith(":") else None
            decoded.append(char)
            index += 1
            continue
        if char == '"':
            tail = value[index + 1:].strip(" \t")
            return "".join(decoded) if not tail or tail.startswith(":") else None
        if char != "\\":
            decoded.append(char)
            index += 1
            continue
        index += 1
        if index >= len(value):
            return None
        escaped = value[index]
        simple = {
            "0": "\0", "a": "\a", "b": "\b", "t": "\t", "n": "\n",
            "v": "\v", "f": "\f", "r": "\r", "e": "\x1b", " ": " ",
            '"': '"', "/": "/", "\\": "\\", "N": "\x85", "_": "\xa0",
            "L": "\u2028", "P": "\u2029",
        }
        if escaped in simple:
            decoded.append(simple[escaped])
            index += 1
            continue
        width = {"x": 2, "u": 4, "U": 8}.get(escaped)
        if width is None:
            return None
        digits = value[index + 1:index + 1 + width]
        if len(digits) != width or re.fullmatch(r"[0-9A-Fa-f]+", digits) is None:
            return None
        try:
            decoded.append(chr(int(digits, 16)))
        except ValueError:
            return None
        index += width + 1
    return None


def _frontmatter_root_key_is_alias(line: str, key: str) -> bool:
    """Recognize YAML-equivalent root spellings without normalizing them as accepted input."""
    candidate = yaml_horizontal_strip(line)
    if not candidate or candidate.startswith("#"):
        return False
    # Explicit keys, merge keys, and aliases are outside this schema. An arbitrary alias name
    # may refer to any protected key anchored elsewhere, so reject it without guessing its name.
    if candidate == "?" or candidate.startswith(("? ", "?\t", "*")):
        return True
    if re.match(r"^<<[ \t]*:", candidate):
        return True
    decorated = False
    # YAML node properties may precede a key in either order. This schema needs no tagged or
    # anchored root key; inspect recognized properties and refuse malformed property syntax.
    while True:
        property_prefix = re.match(r"^(?:&[^ \t\[\]{},]+|!(?:<[^>]*>|[^ \t\[\]{},]*))[ \t]+(.+)$",
                                   candidate)
        if property_prefix is None:
            break
        decorated = True
        candidate = yaml_horizontal_strip(property_prefix.group(1))
    if not candidate:
        return decorated
    if candidate[0] in "&!":
        return True
    if candidate[0] in "\"'":
        decoded = _decode_frontmatter_key(candidate)
        if decoded == key:
            return True
        # Malformed quoted forms that visibly begin with this protected key also fail closed.
        visible = candidate[1:].lstrip(" \t")
        return decoded is None and visible.startswith(key) and (
            len(visible) == len(key) or visible[len(key)] in " '\"\t:")
    plain_key = parse_frontmatter_plain_key(candidate)
    if plain_key == key:
        return decorated or not candidate.startswith(f"{key}:")
    return False


def frontmatter_mapping_pairs(text: str, key: str) -> list[tuple[str, str]] | None:
    """Read only one canonical root map while retaining pairs and rejecting YAML aliases."""
    normalized, _ = yaml_source_lines(text)
    match = GAP_FRONTMATTER.match(normalized)
    if match is None:
        return None
    _, lines = yaml_source_lines(match.group(1))
    if frontmatter_duplicates(text):
        return None
    for line in lines:
        if line and line[0] not in " \t" and line != f"{key}:" and _frontmatter_root_key_is_alias(line, key):
            return None
    roots = [index for index, line in enumerate(lines) if line == f"{key}:"]
    if len(roots) != 1:
        return None
    pairs: list[tuple[str, str]] = []
    for line in lines[roots[0] + 1:]:
        if not yaml_horizontal_strip(line):
            continue
        if line[0] not in " \t":
            break
        if not line.startswith("  ") or line.startswith("   "):
            return None
        entry = re.fullmatch(r" {2}([A-Za-z0-9_-]+):[ \t]*(.*)", line)
        if entry is None:
            return None
        raw_value = entry.group(2).strip(" \t")
        if not raw_value:
            return None
        value = decode_frontmatter_scalar(raw_value)
        if value is None:
            return None
        if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
            return None
        pairs.append((entry.group(1), value))
    return pairs


def visible_markdown_lines(text: str) -> list[str | None]:
    """Mask code and HTML comments in place so every Markdown contract sees the same lines."""
    source_lines = markdown_source_lines(text)
    visible: list[str | None] = []
    fence: tuple[str, int] | None = None
    comment = False
    inline_ticks = 0

    def tick_run(line: str, start: int) -> int:
        end = start
        while end < len(line) and line[end] == "`":
            end += 1
        return end - start

    def escaped(line: str, index: int) -> bool:
        backslashes = 0
        index -= 1
        while index >= 0 and line[index] == "\\":
            backslashes += 1
            index -= 1
        return backslashes % 2 == 1

    def has_inline_close(line_index: int, start: int, length: int) -> bool:
        for future_index in range(line_index, len(source_lines)):
            future = source_lines[future_index]
            if future_index > line_index and not future.strip():
                return False
            position = start if future_index == line_index else 0
            while position < len(future):
                if future[position] != "`":
                    position += 1
                    continue
                run = tick_run(future, position)
                if run == length:
                    return True
                position += run
        return False

    for line_index, line in enumerate(source_lines):
        if fence is not None:
            marker, length = fence
            visible.append(None)
            inline_ticks = 0
            if re.fullmatch(r" {0,3}" + re.escape(marker) + "{" + str(length) + r",}[ \t]*", line):
                fence = None
            continue

        if not comment:
            opening = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
            if opening:
                run, info = opening.groups()
                if run[0] != "`" or "`" not in info:
                    fence = (run[0], len(run))
                    visible.append(None)
                    inline_ticks = 0
                    continue
            if inline_ticks == 0 and (line.startswith("\t") or re.match(r"^ {4,}", line)):
                visible.append(None)
                continue

        masked = list(line)
        position = 0
        while position < len(line):
            if comment:
                end = line.find("-->", position)
                mask_end = len(line) if end < 0 else end + 3
                for index in range(position, mask_end):
                    masked[index] = " "
                if end < 0:
                    position = len(line)
                    break
                comment = False
                position = mask_end
                continue

            if inline_ticks:
                if line[position] == "`" and tick_run(line, position) == inline_ticks:
                    position += inline_ticks
                    inline_ticks = 0
                else:
                    position += 1
                continue

            if line.startswith("<!--", position) and not escaped(line, position):
                comment = True
                continue

            if line[position] == "`" and not escaped(line, position):
                run = tick_run(line, position)
                if has_inline_close(line_index, position + run, run):
                    inline_ticks = run
                    position += run
                    continue
                position += run
                continue

            position += 1

        visible.append("".join(masked))
    return visible


def markdown_section(text: str, title: str) -> str:
    lines = visible_markdown_lines(text)
    heading_pattern = re.compile(r"^#{1,4}[ \t]+" + re.escape(title)
                                 + r"(?:[ \t]+#+)?[ \t]*$", re.IGNORECASE)
    start = next((index for index, line in enumerate(lines)
                  if line is not None and heading_pattern.match(line)), None)
    if start is None:
        return ""
    next_heading_pattern = re.compile(r"^#{1,4}[ \t]+.*?(?:[ \t]+#+)?[ \t]*$")
    end = next((index for index in range(start + 1, len(lines))
                if lines[index] is not None and next_heading_pattern.match(lines[index])), len(lines))
    return "\n".join(line if line is not None else "" for line in lines[start + 1:end])


def markdown_heading_count(text: str, title: str) -> int:
    """Count exact Markdown headings for a contract section, case-insensitively."""
    pattern = re.compile(r"^#{1,6}[ \t]+" + re.escape(title)
                         + r"(?:[ \t]+#+)?[ \t]*$", re.IGNORECASE)
    return sum(bool(line is not None and pattern.match(line)) for line in visible_markdown_lines(text))


def protected_setext_headings(text: str, titles: tuple[str, ...]) -> list[str]:
    """Find protected plain-text Setext titles outside fenced and indented code."""
    normalize = lambda value: re.sub(r"[ \t]+", " ", value.lower()).strip(" \t")
    protected = {normalize(title): title for title in titles}
    visible = visible_markdown_lines(text)

    found: list[str] = []
    for index, line in enumerate(visible):
        if line is None or re.fullmatch(r" {0,3}(?:=+|-+)[ \t]*", line) is None:
            continue
        title_lines: list[str] = []
        previous = index - 1
        while previous >= 0:
            candidate = visible[previous]
            if (candidate is None or not candidate.strip()
                    or re.match(r"^ {0,3}#{1,6}(?:[ \t]+|$)", candidate)
                    or re.fullmatch(r" {0,3}(?:=+|-+)[ \t]*", candidate)):
                break
            title_lines.insert(0, candidate.strip())
            previous -= 1
        protected_title = protected.get(normalize(" ".join(title_lines)))
        if protected_title is not None:
            found.append(protected_title)
    return found


def markdown_table_cells(line: str) -> list[str] | None:
    stripped = line.strip(" \t")
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    cells = [cell.strip(" \t") for cell in stripped[1:-1].split("|")]
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
    for line in markdown_source_lines(section):
        match = re.match(r"\|[ \t]*(FIXT-01|RIGHTS-01|DIAG-01|DIAG-02)[ \t]*\|[ \t]*"
                         r"(Phase[ \t]+\d+(?:\.\d+)?)[ \t]*\|[ \t]*"
                         r"(Pending|Complete|Satisfied)[ \t]*\|", line, re.IGNORECASE)
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
    visible_body = "\n".join(line if line is not None else "" for line in visible_markdown_lines(body))
    visible_body_norm = " ".join(visible_body.lower().split())
    duplicate_fields = frontmatter_duplicates(report)
    if duplicate_fields:
        errors.append("v04-report-frontmatter-duplicate: " + ", ".join(duplicate_fields))
    for key, expected in V04_REPORT_EXPECTED_FIELDS.items():
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
    requirement_pairs = frontmatter_mapping_pairs(report, "requirements")
    expected_requirements = {key: "pending" for key in V04_PENDING_OWNERS}
    requirements_valid = (
        requirement_pairs is not None
        and len(requirement_pairs) == len(expected_requirements)
        and len({key for key, _ in requirement_pairs}) == len(requirement_pairs)
        and {key for key, _ in requirement_pairs} == set(expected_requirements)
        and all(value == expected_requirements[key] for key, value in requirement_pairs)
        and {key for key, _ in requirement_pairs} == set(actual_dispositions)
    )
    if not requirements_valid:
        errors.append("v04-report-requirements: nested requirements must exactly match the four Pending dispositions")

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

    if ("historical reconstruction scope" not in visible_body_norm
            or "synthetic" not in visible_body_norm or "metadata-only" not in visible_body_norm):
        errors.append("v04-report-scope: report must identify the historical synthetic-plus-metadata reconstruction scope")
    if "482 protocol candidates remain blocked" not in visible_body_norm:
        errors.append("v04-report-evidence: report must retain the blocked 482 protocol-candidate count")
    report_headings = ("Historical reconstruction scope", "Goal Achievement", "Exact game no-go facts",
                       "Requirement truth and preserved limits")
    setext_headings = protected_setext_headings(body, report_headings)
    if setext_headings:
        errors.append("v04-report-heading: protected report headings must use ATX syntax: " + ", ".join(setext_headings))
    for heading in report_headings:
        if markdown_heading_count(body, heading) != 1:
            errors.append(f"v04-report-heading: {heading} must appear exactly once")
    goal = markdown_section(body, "Goal Achievement") or markdown_section(body, "Goal achievement")
    goal_lines = markdown_source_lines(goal)
    table = [cells for line in goal_lines if (cells := markdown_table_cells(line)) is not None]
    status_columns = [index for index, title in enumerate(table[0] if table else [])
                      if title.strip().lower() in ("status", "historical status", "result", "result status")]
    criterion_rows: list[tuple[int, list[str], str]] = []
    for line in goal_lines:
        cells = markdown_table_cells(line)
        if not cells:
            continue
        criterion = re.match(r"^(\d+)[ \t]*[.)][ \t]*", cells[0])
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
            or any(not has_local_link(visible_body, report_path, path)
                   for path in required_link_paths if path is not None)):
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
    if "full milestone closure remains unsatisfied" not in visible_body_norm:
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
    duplicate_state_fields = frontmatter_duplicates(state)
    if duplicate_state_fields:
        errors.append("v04-handoff-frontmatter-duplicate: " + ", ".join(duplicate_state_fields))
    for document_name, document, heading in (
            ("STATE", state, "Owner Handoff"),
            ("PROJECT", project, "Current State"),
            ("continuation", continuation, "Owner Handoff")):
        if protected_setext_headings(document, (heading,)):
            errors.append(f"v04-handoff-heading: {document_name} {heading} must use ATX syntax")
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
    current_handoff = markdown_section(continuation, "Owner Handoff")
    state_norm = " ".join(state_handoff.lower().split())
    project_norm = " ".join(project_state.lower().split())
    continuation_norm = " ".join(current_handoff.lower().split())
    if not all(value in state_norm for value in ("phase 22", "historical verification", "phase 20", "stale", "phase 21", "stale")):
        errors.append("v04-handoff-stale: current state must mark Phase 20/21 reports stale and Phase 22 report historical")
    required_pending = ("FIXT-01", "RIGHTS-01", "DIAG-01", "DIAG-02")
    for document_name, text in (("STATE", state_handoff), ("PROJECT", project_state), ("continuation", current_handoff)):
        normalized = " ".join(text.lower().split())
        if "pending" not in normalized or not all(req.lower() in normalized for req in required_pending):
            errors.append(f"v04-handoff-pending: {document_name} must preserve all four Pending requirements")
    for req, owner in V04_PENDING_OWNERS.items():
        line_found = any(re.match(r"^[ \t]*[-*+][ \t]+", line)
                         and req in line and owner.lower() in line.lower() and "pending" in line.lower()
                         for line in markdown_source_lines(state_handoff))
        if not line_found:
            errors.append(f"v04-handoff-owner: current STATE handoff must retain {req} as Pending under {owner}")
    if "v0.4 remains open" not in state_norm or "v0.4 remains open" not in project_norm:
        errors.append("v04-handoff-open: STATE and PROJECT must keep the v0.4 milestone open")
    if not all(term in state_norm for term in ("exact-final-head full-suite", "unfulfilled", "no broad local suite",
                                               "no third local lifecycle retest", "no release retry", "no tag/asset/rights action")):
        errors.append("v04-handoff-stops: preserved final-suite, lifecycle, publication, tag, asset, and rights stops are incomplete")
    route = "/gsd-audit-milestone v0.4"
    if route not in state_handoff or route not in current_handoff or "owner-only" not in continuation_norm:
        errors.append("v04-handoff-route: current handoff must preserve the owner-only audit route")
    if "no next phase or milestone is selected" not in continuation_norm or "phase 23.1" not in continuation_norm:
        errors.append("v04-handoff-phase: continuation must close Phase 23.1 without selecting or starting another phase")
    for path, text in ((state_path, state), (project_path, project), (continuation_path, continuation)):
        visible_text = "\n".join(line if line is not None else "" for line in visible_markdown_lines(text))
        if report_path and not has_local_link(visible_text, path, report_path):
            errors.append(f"v04-handoff-link: {path.rsplit('/', 1)[-1]} does not link to the Phase 22 report")
    visible_report = "\n".join(line if line is not None else "" for line in visible_markdown_lines(report))
    if not report or "full milestone closure remains unsatisfied" not in " ".join(visible_report.lower().split()):
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


def frontmatter_root_keys(text: str) -> list[str] | None:
    """Return simple root keys for a fixed-schema report, refusing unsupported root syntax."""
    normalized, _ = yaml_source_lines(text)
    match = GAP_FRONTMATTER.match(normalized)
    if match is None:
        return None
    keys: list[str] = []
    _, lines = yaml_source_lines(match.group(1))
    for line in lines:
        if not line or line[0] in " \t" or line.startswith("#"):
            continue
        key = parse_frontmatter_plain_key(line)
        if key is None:
            return None
        keys.append(key)
    return keys


def all_requirement_traceability(text: str) -> dict[str, tuple[str, str]]:
    """Read the eight v0.4 owner/status rows without changing the legacy Pending-only reader."""
    section = markdown_section(text, "Traceability")
    rows: dict[str, tuple[str, str]] = {}
    for line in markdown_source_lines(section):
        cells = markdown_table_cells(line)
        if cells is None or len(cells) < 3 or cells[0] not in V04_GAP_EXPECTED:
            continue
        if re.fullmatch(r"Phase[ \t]+\d+(?:\.\d+)?", cells[1]) and cells[2] in ("Complete", "Pending"):
            rows[cells[0]] = (" ".join(cells[1].split()), cells[2])
    return rows


def v04_gap_requirement_definitions(text: str) -> dict[str, str]:
    definitions: dict[str, str] = {}
    for line in markdown_source_lines(text):
        match = re.match(r"^- \[[ xX]\] \*\*([A-Z0-9-]+)\*\*: (.+)$", line)
        if match and match.group(1) in V04_GAP_EXPECTED:
            definitions[match.group(1)] = match.group(2)
    return definitions


def v04_gap_audit_requirements(text: str) -> dict[str, tuple[str, str]]:
    section = markdown_section(text, "Requirements Coverage")
    rows: dict[str, tuple[str, str]] = {}
    for line in markdown_source_lines(section):
        cells = markdown_table_cells(line)
        if cells is None or len(cells) < 6 or cells[0] not in V04_GAP_EXPECTED:
            continue
        owner_value = " ".join(cells[1].split())
        owner = f"Phase {owner_value}" if re.fullmatch(r"\d+(?:\.\d+)?", owner_value) else owner_value
        result = cells[-1].strip().lower()
        status = next((known for prefix, known in (("partial", "partial"),
                                                     ("unsatisfied", "unsatisfied"),
                                                     ("satisfied", "satisfied"))
                       if result.startswith(prefix)), "")
        if status:
            rows[cells[0]] = (owner, status)
    return rows


def v04_gap_audit_phase_statuses(text: str) -> dict[str, tuple[str, str]]:
    section = markdown_section(text, "Phase Verification Status")
    rows: dict[str, tuple[str, str]] = {}
    for line in markdown_source_lines(section):
        cells = markdown_table_cells(line)
        if cells is None or len(cells) < 4:
            continue
        match = re.match(r"^(\d+)\b", cells[0])
        if match:
            rows[match.group(1)] = (cells[2].strip().lower(), cells[-1].strip())
    return rows


def v04_gap_sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def v04_gap_evidence_boundary(input_rev: str, report_path: str, report_raw: bytes,
                              requirements_raw: bytes, audit_raw: bytes) -> str:
    return (f"input_commit={input_rev};report_path={report_path};report_blob_sha256={v04_gap_sha(report_raw)};"
            f"requirements_path={V04_GAP_REQUIREMENTS_PATH};requirements_blob_sha256={v04_gap_sha(requirements_raw)};"
            f"audit_path={V04_GAP_AUDIT_PATH};audit_blob_sha256={v04_gap_sha(audit_raw)}")


def check_v04_gap_assessment(repo: Path, stage: str, rev: str,
                             baseline_rev: str) -> tuple[str, list[str]]:
    """Validate the Phase 24 evidence and pending-verification handoff from immutable commits."""
    if stage not in ("report", "handoff"):
        return "", ["v04-gap-assessment-stage: stage must be report or handoff"]
    errors: list[str] = []
    if not FULL_COMMIT.fullmatch(rev):
        return "", ["v04-gap-assessment-rev: --rev must be a full 40-hex commit id"]
    if not FULL_COMMIT.fullmatch(baseline_rev):
        return "", ["v04-gap-assessment-baseline: --baseline-rev must be a full 40-hex commit id"]
    if rev == V04_GAP_INPUT_REV:
        return "", ["v04-gap-assessment-input: report-containing revision must differ from its assessment input"]
    paths, error = commit_paths(repo, rev)
    if error:
        return "", [error.replace("v04-reconciliation", "v04-gap-assessment")]
    baseline_paths, error = commit_paths(repo, baseline_rev)
    if error:
        return "", ["v04-gap-assessment-baseline: --baseline-rev is not a readable commit"]
    input_paths, error = commit_paths(repo, V04_GAP_INPUT_REV)
    if error:
        return "", ["v04-gap-assessment-input: required assessment input is not a readable full commit"]
    assert paths is not None and baseline_paths is not None and input_paths is not None

    report_path = phase_file(paths, "24", "24-EVIDENCE.md")
    if report_path != V04_GAP_REPORT_PATH:
        return "", ["v04-gap-assessment-report: canonical Phase 24 evidence report is missing or moved"]
    report_raw = commit_file(repo, rev, report_path)
    input_requirements_raw = commit_file(repo, V04_GAP_INPUT_REV, V04_GAP_REQUIREMENTS_PATH)
    input_audit_raw = commit_file(repo, V04_GAP_INPUT_REV, V04_GAP_AUDIT_PATH)
    requirements_raw = commit_file(repo, rev, V04_GAP_REQUIREMENTS_PATH)
    audit_raw = commit_file(repo, rev, V04_GAP_AUDIT_PATH)
    if None in (report_raw, input_requirements_raw, input_audit_raw, requirements_raw, audit_raw):
        return "", ["v04-gap-assessment-input: report, requirements, or audit blob is missing from its pinned commit"]
    assert report_raw is not None and input_requirements_raw is not None and input_audit_raw is not None
    assert requirements_raw is not None and audit_raw is not None
    report = report_raw.decode("utf-8", errors="strict")
    requirements = requirements_raw.decode("utf-8", errors="strict")
    audit = audit_raw.decode("utf-8", errors="strict")
    input_requirements = input_requirements_raw.decode("utf-8", errors="strict")
    input_audit = input_audit_raw.decode("utf-8", errors="strict")
    fields, body = frontmatter_fields(report)
    duplicates = frontmatter_duplicates(report)
    if duplicates:
        errors.append("v04-gap-assessment-frontmatter: duplicate or aliased protected keys: " + ", ".join(duplicates))
    root_keys = frontmatter_root_keys(report)
    expected_root_keys = {
        "phase", "report_kind", "assessment_input_commit", "baseline_commit", "milestone",
        "milestone_status", "milestone_audit_status", "phase_completion_scope",
        "requirements_satisfied_by_phase", "refreshes_phase20_21", "satisfies_d103",
        "source_records", "requirement_assessments", "phase_assessments",
    }
    if root_keys is None or len(root_keys) != len(expected_root_keys) or set(root_keys) != expected_root_keys:
        errors.append("v04-gap-assessment-frontmatter: unsupported or unexpected root fields")
    expected_fields = {
        "phase": "GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps",
        "report_kind": "point_in_time_gap_assessment",
        "assessment_input_commit": V04_GAP_INPUT_REV,
        "baseline_commit": baseline_rev,
        "milestone": "v0.4",
        "milestone_status": "open",
        "milestone_audit_status": "gaps_found",
        "phase_completion_scope": "evidence_map_only",
        "requirements_satisfied_by_phase": "[]",
        "refreshes_phase20_21": "false",
        "satisfies_d103": "false",
    }
    for key, expected in expected_fields.items():
        if fields.get(key) != expected:
            code = "v04-gap-assessment-input" if key in ("assessment_input_commit", "baseline_commit") else "v04-gap-assessment-field"
            errors.append(f"{code}: {key} must be {expected}")
    if fields.get("assessment_input_commit") == rev:
        errors.append("v04-gap-assessment-input: report cannot assess its own containing revision")
    if baseline_rev == V04_GAP_INPUT_REV:
        errors.append("v04-gap-assessment-baseline: baseline and assessment input must be distinct commits")

    source_records = frontmatter_objects(report, "source_records") or []
    source_rows = [(item.get("path", ""), item.get("sha256", "")) for item in source_records]
    if any(set(item) != {"path", "sha256"} for item in source_records) or \
            [path for path, _ in source_rows] != list(V04_GAP_SOURCE_PATHS):
        errors.append("v04-gap-assessment-source-records: source records must list the exact canonical input paths in order")
    source_raw: dict[str, bytes] = {}
    for path in V04_GAP_SOURCE_PATHS:
        raw = commit_file(repo, V04_GAP_INPUT_REV, path)
        if raw is None:
            errors.append(f"v04-gap-assessment-source-records: required source blob is missing at input: {path}")
            continue
        source_raw[path] = raw
    expected_records = [(path, v04_gap_sha(source_raw[path])) for path in V04_GAP_SOURCE_PATHS if path in source_raw]
    if source_rows != expected_records:
        errors.append("v04-gap-assessment-source-records: recorded SHA-256 identities do not match the immutable input blobs")
    if any(not re.fullmatch(r"[0-9a-f]{64}", digest) for _, digest in source_rows):
        errors.append("v04-gap-assessment-source-records: every blob identity must be a full lowercase SHA-256")
    input_decisions = source_raw.get(".planning/context/DECISIONS.md", b"").decode("utf-8", errors="replace")
    if "D-204" not in input_decisions or "D-205" not in input_decisions:
        errors.append("v04-gap-assessment-input: pinned decisions do not contain the current D-204/D-205 authorization")

    for number in ("20", "21"):
        name = f"{number}-VERIFICATION.md"
        target_path = phase_file(paths, number, name)
        baseline_path = phase_file(baseline_paths, number, name)
        input_path = phase_file(input_paths, number, name)
        if target_path is None or target_path != baseline_path or target_path != input_path:
            errors.append(f"v04-gap-assessment-history: Phase {number} report path is missing or moved from baseline")
            continue
        before = commit_file(repo, baseline_rev, baseline_path)
        at_input = commit_file(repo, V04_GAP_INPUT_REV, input_path)
        at_target = commit_file(repo, rev, target_path)
        if before is None or at_input is None or at_target is None or before != at_input or before != at_target:
            errors.append(f"v04-gap-assessment-history: Phase {number} report bytes must remain identical to baseline")
            continue
        base_fields, _ = frontmatter_fields(before.decode("utf-8", errors="strict"))
        input_fields, _ = frontmatter_fields(at_input.decode("utf-8", errors="strict"))
        target_fields, _ = frontmatter_fields(at_target.decode("utf-8", errors="strict"))
        identity_fields = V04_GAP_PHASE_IDENTITY_FIELDS[number]
        if any(not base_fields.get(key) or base_fields.get(key) != input_fields.get(key)
               or base_fields.get(key) != target_fields.get(key) for key in identity_fields):
            errors.append(f"v04-gap-assessment-history: Phase {number} report source identity fields differ from baseline")

    requirements_target_fields = all_requirement_traceability(requirements)
    input_tracker_fields = all_requirement_traceability(input_requirements)
    if requirements_raw != input_requirements_raw or requirements_target_fields != input_tracker_fields:
        errors.append("v04-gap-assessment-requirements: REQUIREMENTS.md must preserve the assessed input tracker")
    expected_tracker = {key: (value[0], value[1]) for key, value in V04_GAP_EXPECTED.items()}
    if requirements_target_fields != expected_tracker:
        errors.append("v04-gap-assessment-requirements: the eight original tracker owners and statuses must be preserved")
    definitions = v04_gap_requirement_definitions(input_requirements)
    if set(definitions) != set(V04_GAP_EXPECTED):
        errors.append("v04-gap-assessment-requirements: REQUIREMENTS.md must define exactly the eight v0.4 criteria")

    audit_fields, _ = frontmatter_fields(audit)
    input_audit_fields, _ = frontmatter_fields(input_audit)
    if audit_raw != input_audit_raw or audit_fields.get("milestone") != "v0.4" or \
            audit_fields.get("status") != "gaps_found" or input_audit_fields.get("status") != "gaps_found":
        errors.append("v04-gap-assessment-audit: target audit must preserve the pinned open gaps_found audit")
    audit_requirements = v04_gap_audit_requirements(audit)
    expected_audit = {key: (values[0], values[2]) for key, values in V04_GAP_EXPECTED.items()}
    if audit_requirements != expected_audit:
        errors.append("v04-gap-assessment-audit: all eight milestone audit dispositions and original owners must match")
    audit_date = audit_fields.get("audited", "")[:10]
    if not re.fullmatch(r"20\d\d-\d\d-\d\d", audit_date):
        errors.append("v04-gap-assessment-audit: dated audit observation is missing")
    phase_statuses = v04_gap_audit_phase_statuses(audit)
    if phase_statuses.get("20", ("", ""))[0] != "stale" or phase_statuses.get("21", ("", ""))[0] != "stale":
        errors.append("v04-gap-assessment-audit: Phase 20 and Phase 21 must remain stale")

    requirement_rows = frontmatter_objects(report, "requirement_assessments") or []
    row_ids = [item.get("id", "") for item in requirement_rows]
    if len(row_ids) != len(set(row_ids)) or set(row_ids) != set(V04_GAP_EXPECTED):
        errors.append("v04-gap-assessment-requirements: exactly eight unique original requirement rows are required")
    if any(set(item) != V04_GAP_REQUIREMENT_FIELDS for item in requirement_rows):
        errors.append("v04-gap-assessment-requirements: assessment row fields must match the exact schema")
    rows_by_id = {item.get("id", ""): item for item in requirement_rows}
    requirements_hash = v04_gap_sha(input_requirements_raw)
    audit_hash = v04_gap_sha(input_audit_raw)
    for requirement, expected in V04_GAP_EXPECTED.items():
        row = rows_by_id.get(requirement)
        report_source = V04_GAP_HISTORICAL_REPORTS[requirement]
        source_report_raw = source_raw.get(report_source)
        if row is None or source_report_raw is None or requirement not in definitions:
            continue
        source_report = source_report_raw.decode("utf-8", errors="strict")
        report_fields, _ = frontmatter_fields(source_report)
        owner, tracker_status, audit_status, historical_result, freshness_kind, remaining_gate = expected
        expected_freshness = {
            "stale": f"stale at dated {audit_date} audit; no Phase 24 refresh",
            "not_evaluated": f"historical runtime freshness not_evaluated; dated {audit_date} audit passed for metadata-only scope only",
            "passed": f"passed in dated {audit_date} milestone audit; D-103 remains separate",
        }[freshness_kind]
        expected_boundary = v04_gap_evidence_boundary(
            V04_GAP_INPUT_REV, report_source, source_report_raw, input_requirements_raw, input_audit_raw)
        expected_row = {
            "id": requirement,
            "original_criterion": definitions[requirement],
            "original_owner": owner,
            "tracker_status": tracker_status,
            "milestone_audit_status": audit_status,
            "historical_report_path": report_source,
            "historical_report_status": report_fields.get("status", ""),
            "historical_requirement_result": historical_result,
            "current_freshness": expected_freshness,
            "evidence_boundary": expected_boundary,
            "remaining_gate": remaining_gate,
        }
        if row != expected_row:
            errors.append(f"v04-gap-assessment-requirements: {requirement} must keep criterion, owner, statuses, history, freshness, evidence, and gate distinct")
        if report_fields.get("status") != "passed":
            errors.append(f"v04-gap-assessment-history: {requirement} historical report status must be passed")
        history_text = " ".join(source_report.lower().split())
        result_terms = {
            "GAME-01": ("game-01", "satisfied"),
            "GAME-02": ("game-02", "harness-only", "satisfied"),
            "FIXT-01": ("fixt-01", "passed (override)", "pending"),
            "RIGHTS-01": ("rights-01 remains pending", "no candidate was admitted"),
            "DIAG-01": ("diag-01", "pending", "metadata-only"),
            "DIAG-02": ("diag-02", "513", "metadata-only"),
            "FEED-01": ("feed-01", "workflow contract", "satisfied"),
            "REL-01": ("rel-01", "verified"),
        }[requirement]
        if any(term not in history_text for term in result_terms):
            errors.append(f"v04-gap-assessment-history: {requirement} interpretation lacks support in its pinned historical report")
        if requirement in ("DIAG-01", "DIAG-02") and report_fields.get("current_freshness") != "not_evaluated":
            errors.append(f"v04-gap-assessment-history: {requirement} must preserve historical runtime freshness as not_evaluated")

    phase_rows = frontmatter_objects(report, "phase_assessments") or []
    phase_ids = [item.get("phase", "") for item in phase_rows]
    if len(phase_ids) != len(set(phase_ids)) or set(phase_ids) != {"20", "21"}:
        errors.append("v04-gap-assessment-phase: exactly the Phase 20 and Phase 21 freshness assessments are required")
    if any(set(item) != V04_GAP_PHASE_FIELDS for item in phase_rows):
        errors.append("v04-gap-assessment-phase: freshness row fields must match the exact schema")
    phase_rows_by_id = {item.get("phase", ""): item for item in phase_rows}
    expected_categories = {"20": "workflow, CMake, and admission files",
                           "21": "CMake, documentation, and test files"}
    for number in ("20", "21"):
        row = phase_rows_by_id.get(number)
        report_source = f".planning/phases/GB-{number}-" + (
            "fixture-admission-tune-up/20-VERIFICATION.md" if number == "20" else
            "cgb-game-progress-and-scene-regressions/21-VERIFICATION.md")
        source_report_raw = source_raw.get(report_source)
        if row is None or source_report_raw is None:
            continue
        source_report = source_report_raw.decode("utf-8", errors="strict")
        report_fields, _ = frontmatter_fields(source_report)
        identity_fields = V04_GAP_PHASE_IDENTITY_FIELDS[number]
        historical_identity = "; ".join(f"{key}={report_fields[key]}" for key in identity_fields)
        expected_row = {
            "phase": number,
            "historical_report_path": report_source,
            "historical_report_status": report_fields.get("status", ""),
            "historical_source_identity": historical_identity,
            "current_audit_observation": f"stale at dated {audit_date} audit",
            "changed_covered_file_categories": expected_categories[number],
            "outstanding_full_verification_gate": f"Fresh full Phase {number} verification remains outstanding; Phase 24 checks do not refresh it.",
        }
        if row != expected_row or report_fields.get("status") != "passed":
            errors.append(f"v04-gap-assessment-phase: Phase {number} must preserve its historical identity and stale audit boundary")
        audit_phase = phase_statuses.get(number, ("", ""))[1].lower()
        if any(term.lower() not in audit_phase for term in expected_categories[number].replace(",", "").replace("and", "").split()):
            errors.append(f"v04-gap-assessment-phase: Phase {number} changed-file categories must match the dated audit")

    visible_body = "\n".join(line if line is not None else "" for line in visible_markdown_lines(body))
    visible_norm = " ".join(visible_body.lower().split())
    if any(term not in visible_norm for term in (
            "point-in-time", "does not refresh phase 20/21", "does not satisfy d-103",
            "does not satisfy the four pending requirements", "v0.4 remains open", "gaps_found",
            "no rights determination", "no permission is inferred", "513", "seven unresolved gates",
            "admitted=0", "executed=0", "482 blocked candidates", "31 initial exclusions")):
        errors.append("v04-gap-assessment-body: scope, counts, freshness, and rights limits must remain explicit")
    context_text = source_raw.get(V04_GAP_SOURCE_PATHS[3], b"").decode("utf-8", errors="replace")
    context_norm = " ".join(context_text.lower().split())
    source_observations = (
        "2026-11-16", "https://deved.itch.io/potion-panic", "https://codeberg.org/deved/potion-panic",
        "https://github.com/antoniond/ucity", "https://github.com/antoniond/ucity/releases/tag/v1.3",
        "https://codeberg.org/skylyrac/ucity", "dmg-acid2/blob/v1.0/readme.md",
        "cgb-acid2/blob/v1.1/readme.md", "gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/readme.md",
        "could not fetch", "do not infer",
    )
    if any(term not in context_norm for term in source_observations):
        errors.append("v04-gap-assessment-source-observations: existing first-party metadata and access failures must remain attributed without rights inference")
    if any(not has_local_link(visible_body, report_path, path) for path in V04_GAP_SOURCE_PATHS):
        errors.append("v04-gap-assessment-links: every immutable source record must have a valid local link")

    if stage == "report":
        return "v04-gap-assessment pass stage=report", errors
    return check_v04_gap_handoff(repo, rev, baseline_rev, paths, report_path, errors)


def check_v04_gap_handoff(repo: Path, rev: str, baseline_rev: str, paths: list[str],
                          report_path: str, errors: list[str]) -> tuple[str, list[str]]:
    """Check the committed assessment closure without converting it into phase verification."""
    phase_dir = ".planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps"
    expected_paths = {
        "summary": f"{phase_dir}/24-01-SUMMARY.md",
        "validation": f"{phase_dir}/24-VALIDATION.md",
        "continuation": f"{phase_dir}/.continue-here.md",
        "uat": f"{phase_dir}/24-UAT.md",
        "state": ".planning/STATE.md",
    }
    documents: dict[str, str] = {}
    for label, path in expected_paths.items():
        if path not in paths:
            errors.append(f"v04-gap-assessment-handoff: missing {label} at committed handoff revision")
            continue
        raw = commit_file(repo, rev, path)
        if raw is None:
            errors.append(f"v04-gap-assessment-handoff: cannot read {label} from committed handoff revision")
        else:
            documents[label] = raw.decode("utf-8", errors="strict")
    summary = documents.get("summary", "")
    validation = documents.get("validation", "")
    continuation = documents.get("continuation", "")
    state = documents.get("state", "")
    summary_schema_errors = closed_frontmatter_root_errors(summary, V04_GAP_HANDOFF_SUMMARY_KEYS)
    if summary_schema_errors:
        errors.append("v04-gap-assessment-handoff: summary frontmatter must use its closed root-key schema: " +
                      ", ".join(summary_schema_errors))
        summary_fields, summary_body = {}, ""
    else:
        summary_fields, summary_body = frontmatter_fields(summary)
        if summary_fields.get("status") != "complete" or summary_fields.get("requirements-completed") != "[]":
            errors.append("v04-gap-assessment-handoff: summary must complete the assessment plan with requirements-completed: []")
        if summary_fields.get("phase") != "GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps" or summary_fields.get("plan") != "01":
            errors.append("v04-gap-assessment-handoff: summary must identify the Phase 24 plan")

    summary_norm = " ".join(summary_body.lower().split())
    validation_norm = " ".join(validation.lower().split())
    continuation_norm = " ".join(continuation.lower().split())
    state_norm = " ".join(state.lower().split())
    current_marker = "current handoff:"
    current_start = state_norm.rfind(current_marker)
    current_end = state_norm.find("## accumulated context", current_start)
    state_handoff = state_norm[current_start:current_end if current_end >= 0 else None] if current_start >= 0 else ""
    for label, text in (("summary", summary_norm), ("continuation", continuation_norm), ("STATE current handoff", state_handoff)):
        requirements = ("fixt-01", "rights-01", "diag-01", "diag-02", "pending", "v0.4", "gaps_found",
                        "phase 20", "phase 21", "stale", "d-103", "unfulfilled", "$gsd-verify-work 24",
                        "no broad local suite", "no third local lifecycle retest", "no release retry",
                        "no tag/asset/rights action", "no fixture admission")
        if any(term not in text for term in requirements):
            errors.append(f"v04-gap-assessment-handoff: {label} must preserve Pending owners, stale phases, open audit, D-103, and every scoped stop")
        owner_facts = (
            "fixt-01 — pending, original owner phase 21",
            "rights-01 — pending, original owner phase 20",
            "diag-01 — pending, original owner phase 22",
            "diag-02 — pending, original owner phase 22",
        )
        if any(owner_fact not in text for owner_fact in owner_facts):
            errors.append(f"v04-gap-assessment-handoff: {label} must retain each Pending requirement's original owner")
        if re.search(r"d-103[^.]{0,60}\b(?:fulfilled|satisfied|passed|complete|completed)\b", text) or \
                re.search(r"v0\.4[^.]{0,60}\b(?:closed|completed|milestone_completed)\b", text) or \
                "milestone_status: closed" in text or "milestone_audit_status: passed" in text:
            errors.append(f"v04-gap-assessment-handoff: {label} contradicts the unfulfilled D-103 or open milestone state")
    if any(term not in summary_norm for term in (
            "phase 24 execution/automated closure complete", "phase verification pending",
            "orchestrator is the next actor", "assessment input", "protected baseline",
            "tested checker/report candidate", V04_GAP_INPUT_REV.lower(), baseline_rev.lower())):
        errors.append("v04-gap-assessment-handoff: summary must separate execution, phase verification, and the three commit boundaries")
    check_candidate_match = re.search(r"tested checker/report candidate[:` ]+([0-9a-f]{40})", summary_norm)
    if check_candidate_match is None:
        errors.append("v04-gap-assessment-handoff: the full tested checker/report candidate must be recorded")
    elif check_candidate_match.group(1) in (rev, V04_GAP_INPUT_REV):
        errors.append("v04-gap-assessment-handoff: tested candidate must differ from input and later handoff-containing commits")
    if rev == V04_GAP_INPUT_REV:
        errors.append("v04-gap-assessment-handoff: committed handoff cannot equal its assessment input")
    if "requirements-completed: []" not in summary_norm:
        errors.append("v04-gap-assessment-handoff: summary must keep requirements-completed empty")
    if "$gsd-verify-work 24" not in continuation_norm or "orchestrator" not in continuation_norm:
        errors.append("v04-gap-assessment-handoff: continuation must route the orchestrator to Phase 24 verification")
    if "planning-hygiene" not in validation_norm or "24-01-t1-map" not in validation_norm or \
            "24-01-t2-controls" not in validation_norm or "24-01-t3-closure" not in validation_norm:
        errors.append("v04-gap-assessment-handoff: validation map must retain all three plan task IDs")
    required_links = {
        "summary": (expected_paths["report"] if "report" in expected_paths else report_path,
                    expected_paths["validation"], expected_paths["uat"], expected_paths["continuation"]),
        "continuation": (report_path, expected_paths["summary"], expected_paths["validation"], expected_paths["uat"]),
        "state": (report_path, expected_paths["summary"], expected_paths["validation"], expected_paths["uat"]),
    }
    for label, targets in required_links.items():
        source_path = expected_paths[label]
        text = documents.get(label, "")
        if any(not has_local_link(text, source_path, target) for target in targets):
            errors.append(f"v04-gap-assessment-handoff: {label} must link to its local immutable evidence artifacts")
    roadmap, tree, decisions = read_rev(repo, rev)
    _, plan_cap_errors = check_plan_tree(roadmap, tree, rev, decisions)
    if plan_cap_errors:
        errors.extend(f"v04-gap-assessment-handoff: {error}" for error in plan_cap_errors)
    return "v04-gap-assessment pass stage=handoff", errors


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


def has_exact_d205_authorization(decisions_text: str | None) -> bool:
    """Accept D-205 only when its one canonical decision section has the exact authorized scope."""
    if decisions_text is None:
        return False
    lines = markdown_source_lines(decisions_text)
    headings = [index for index, line in enumerate(lines) if line == V04_D205_DECISION_HEADING]
    if len(headings) != 1:
        return False
    start = headings[0] + 1
    end = next((index for index in range(start, len(lines))
                if re.match(r"^ {0,3}#{1,6}[ \t]+", lines[index])), len(lines))
    body = " ".join(" ".join(line.split()) for line in lines[start:end] if line.strip())
    return body == V04_D205_DECISION_BODY


def check_plan_cap(roadmap: str, phases_dir: Path,
                   decisions_text: str | None = None) -> tuple[str, list[str]]:
    return check_plan_tree(roadmap, tree_from_dir(phases_dir), str(phases_dir), decisions_text)


def check_plan_tree(roadmap: str, tree: PlanTree | None, where: str,
                    decisions_text: str | None = None) -> tuple[str, list[str]]:
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
    approved_v04_d193 = (
        caps == V04_APPROVED_PHASE_CAPS
        and V04_EXCEPTION_TEXT in roadmap_contract
        and "see d-193" in roadmap_contract
    )
    approved_v04_d205 = (
        caps == V04_D205_PHASE_CAPS
        and V04_D205_EXCEPTION_TEXT in roadmap_contract
        and "see d-205" in roadmap_contract
        and "phase 24 has one ordinary plan and no new gap reserve" in roadmap_contract
        and has_exact_d205_authorization(decisions_text)
    )
    approved_v04_exception = approved_v04_d193 or approved_v04_d205
    if len(caps) > PHASE_COUNT_MAX and not approved_v04_exception:
        errors.append(f"plan-cap-phase-count: the active milestone lists {len(caps)} phases, above {PHASE_COUNT_MAX}")
    if set(caps) in (set(V04_APPROVED_PHASE_CAPS), set(V04_D205_PHASE_CAPS)) and not approved_v04_exception:
        errors.append("plan-cap-approved-exception: the active v0.4 exception requires the exact phase set, caps, and roadmap approval")
    for number, cap in caps.items():
        if cap is None:
            errors.append(f"plan-cap-missing: Phase {number} has no '**Plan cap**: N' line")
        elif cap > PLAN_CAP_MAX:
            errors.append(f"plan-cap-too-large: Phase {number} cap {cap} is above {PLAN_CAP_MAX}")
    total = sum(cap for cap in caps.values() if cap is not None)
    if total > PLAN_CAP_SUM_MAX and not approved_v04_d205:
        errors.append(f"plan-cap-sum: caps sum to {total}, above {PLAN_CAP_SUM_MAX}")

    if approved_v04_d205:
        phase24_lines: list[str] = []
        in_phase24 = False
        for line in section:
            heading = PHASE_HEADING.match(line)
            if heading:
                in_phase24 = heading.group(1) == "24"
            elif line.startswith("### ") and in_phase24:
                in_phase24 = False
            if in_phase24:
                phase24_lines.append(line)
        if phase24_lines.count(V04_D205_PHASE24_PLAN_LINE) != 1 or roadmap_contract.count("gap reserve") != 2:
            errors.append("plan-cap-d205-reserve: Phase 24 plan allowance cannot gain or renew a gap reserve")

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
        elif number == "24" and approved_v04_d205:
            pass  # D-205 grants this one ordinary plan without opening a gap reserve.
        elif primary[number] > cap - GAP_RESERVE:
            errors.append(f"plan-cap-gap-reserve: Phase {number} has {primary[number]} plans that are not gap_closure plans; "
                          f"cap {cap} reserves {GAP_RESERVE} slot for the single gap round")
    if approved_v04_d205:
        phase24_dirs = [name for name in tree or {}
                        if (match := PHASE_DIR.match(name)) is not None and match.group(1) == "24"]
        phase24_names = sorted(name for directory in phase24_dirs for name in tree[directory])
        if len(phase24_dirs) != 1 or phase24_names != ["24-01-PLAN.md"]:
            errors.append("plan-cap-d205-phase24-plan: Phase 24 must contain exactly one ordinary 24-01-PLAN.md")
        elif is_gap_plan(tree[phase24_dirs[0]]["24-01-PLAN.md"]()):
            errors.append("plan-cap-d205-phase24-gap: Phase 24 must not use a gap_closure plan or reserve")
        actual_total = sum(counts.values())
        if actual_total > PLAN_CAP_SUM_MAX:
            errors.append(f"plan-cap-actual-total: the active milestone has {actual_total} actual plan files, above {PLAN_CAP_SUM_MAX}")
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

        controls += self_test_plan_cap_rev(base, repo, rev)

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
        controls += self_test_v04_gap_assessment(base, repo, live_revision)
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


def self_test_plan_cap_rev(base: Path, source_repo: Path, source_rev: str | None) -> int:
    """--rev judges one commit's ROADMAP and plan names with git, so a working-tree edit, a later commit or a moving name
    cannot change the verdict. Everything runs in a disposable repository."""
    controls = 0
    if source_rev is None:
        head = git_run(source_repo, "rev-parse", "HEAD")
        if head.returncode != 0:
            raise SystemExit(f"planning-hygiene self-test FAIL: could not resolve source HEAD in {source_repo}")
        source_rev = head.stdout.decode("ascii").strip()
    repo = base / "rev-repo"
    repo.mkdir()
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "SYSTEMROOT", "TMPDIR", "TEMP", "TMP")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, GIT_AUTHOR_NAME="fixture",
               GIT_AUTHOR_EMAIL="fixture@example.invalid", GIT_COMMITTER_NAME="fixture",
               GIT_COMMITTER_EMAIL="fixture@example.invalid")

    def git(*args: str) -> str:
        done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, env=env, timeout=60)
        return done.stdout.strip()

    def head() -> str | None:
        raw = (repo / ".git/HEAD").read_text(encoding="ascii").strip()
        ref_path = repo / ".git" / raw[5:] if raw.startswith("ref: ") else None
        if ref_path is None:
            return raw or None
        return ref_path.read_text(encoding="ascii").strip() if ref_path.exists() else None

    def commit(files: dict[str, str], message: str) -> str:
        parent_rev = head()
        new_paths = any(not (repo / rel).exists() for rel in files)
        for rel, content in files.items():
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode("utf-8"))  # bytes, so a Windows text-mode write cannot add CRs (GB-CI-011)
        if new_paths or parent_rev is None:
            git("add", "--", *files)
            git("commit", "-q", "-m", message)
        else:
            git("commit", "-q", "-a", "-m", message)
        revision = head()
        if revision is None:
            raise SystemExit("planning-hygiene self-test FAIL: fixture commit did not create HEAD")
        cache_fixture_commit_snapshot(repo, parent_rev, revision, files)
        return revision

    def judge(rev: str) -> list[str]:
        roadmap, tree, decisions = read_rev(repo, rev)
        return check_plan_tree(roadmap, tree, rev, decisions)[1]

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

    # D-205 is a single exact six-phase exception, not a general sixth-phase allowance.
    d205_caps = [("20", "9"), ("21", "8"), ("22", "12"), ("23", "10"), ("23.1", "1")]
    d205_roadmap = roadmap_text(d205_caps).split("## Progress", 1)[0]
    d205_decision_path = ".planning/context/DECISIONS.md"
    d205_decisions_raw = commit_file(source_repo, source_rev, d205_decision_path)
    if d205_decisions_raw is None:
        raise SystemExit("planning-hygiene self-test FAIL: source revision lacks immutable D-205 decision record")
    d205_decisions = d205_decisions_raw.decode("utf-8", errors="strict")
    d205_roadmap += (
        "## Planning and Approval Boundary\n\n"
        "The owner approved only the exact active v0.4 phase set 20/21/22/23/23.1/24. See D-205.\n\n"
        "### Phase 24: Resolve remaining v0.4 evidence and verification gaps\n\n"
        "**Goal:** preserve the evidence boundary.\n"
        "**Plan cap**: 1\n"
        f"{V04_D205_PHASE24_PLAN_LINE}\n\n"
        "**D-205 bounded exception:** the owner approved only the exact active v0.4 phase set "
        "20/21/22/23/23.1/24. See D-205. Phase 24 has one ordinary plan and no new gap reserve; "
        "independently enforce no more than 40 actual plan files.\n"
    )
    d205_caps_actual = {"20": 8, "21": 7, "22": 11, "23": 9, "23.1": 0, "24": 1}
    d205_gaps = {"20": 1, "21": 1, "22": 1, "23.1": 1}
    d205_root = base / "d205-path"
    d205_root.mkdir()
    d205_phases = make_phases(d205_root, d205_caps_actual, d205_gaps)
    summary, errors = check_plan_cap(d205_roadmap, d205_phases, d205_decisions)
    if errors or summary != "plan-cap pass phases=6 plans=40":
        raise SystemExit(f"planning-hygiene self-test FAIL: path-based D-205 40-plan fixture: {summary} {errors}")
    controls += 1
    renewed_path_roadmap = d205_roadmap.replace(
        V04_D205_PHASE24_PLAN_LINE, "**Plans:** Phase 24 has one plan plus a renewed gap reserve.", 1)
    _, errors = check_plan_cap(renewed_path_roadmap, d205_phases, d205_decisions)
    if "plan-cap-d205-reserve" not in codes(errors):
        raise SystemExit(f"planning-hygiene self-test FAIL: path-based D-205 reserve renewal was accepted: {errors}")
    controls += 1

    d205_repo = base / "d205-rev-repo"
    d205_repo.mkdir()

    def d205_git(*args: str) -> str:
        done = subprocess.run(["git", "-C", str(d205_repo), *args], capture_output=True, text=True,
                              check=True, env=env, timeout=60)
        return done.stdout.strip()

    def d205_head() -> str:
        head = (d205_repo / ".git/HEAD").read_text(encoding="ascii").strip()
        if head.startswith("ref: "):
            ref_path = d205_repo / ".git" / head[5:]
            return ref_path.read_text(encoding="ascii").strip() if ref_path.exists() else ""
        return head

    def d205_commit(files: dict[str, str], message: str, delete: tuple[str, ...] = ()) -> str:
        parent_rev = d205_head() or None
        new_path = any(not (d205_repo / rel).exists() for rel in files)
        for rel, content in files.items():
            path = d205_repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode("utf-8"))
        for rel in delete:
            (d205_repo / rel).unlink()
        if new_path or delete:
            d205_git("add", "-A", "--", ".planning")
            d205_git("commit", "-q", "-m", message)
        else:
            d205_git("commit", "-q", "-a", "-m", message)
        revision = d205_head()
        cache_fixture_commit_snapshot(d205_repo, parent_rev, revision, files, delete)
        return revision

    d205_git("init", "-q")
    d205_dir_paths: dict[str, str] = {}
    d205_files: dict[str, str] = {".planning/ROADMAP.md": d205_roadmap,
                                  d205_decision_path: d205_decisions}
    for phase_dir in sorted(d205_phases.iterdir()):
        if not phase_dir.is_dir():
            continue
        rel_dir = f".planning/phases/{phase_dir.name}"
        for plan in sorted(phase_dir.iterdir()):
            if plan.is_file() and PLAN_FILE.match(plan.name):
                relative = f"{rel_dir}/{plan.name}"
                d205_files[relative] = plan.read_text(encoding="utf-8")
                if phase_dir.name.startswith("GB-24-"):
                    d205_dir_paths[plan.name] = relative
    d205_good = d205_commit(d205_files, "canonical exact D-205 40-plan fixture")

    def d205_cli(rev: str, expected: str | None, label: str) -> None:
        nonlocal controls
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            exit_code = main(["--check", "plan-cap", "--rev", rev, "--repo", str(d205_repo)])
        error_text = errors.getvalue()
        if expected is None:
            if exit_code != 0 or "plan-cap pass phases=6 plans=40" not in output.getvalue():
                raise SystemExit(f"planning-hygiene self-test FAIL: {label} should pass via CLI: {exit_code} {error_text}")
        elif exit_code != 1 or expected not in error_text:
            raise SystemExit(f"planning-hygiene self-test FAIL: {label} should fail with {expected}: {exit_code} {error_text}")
        controls += 1

    d205_cli(d205_good, None, "canonical immutable six-phase 40-plan exception")
    (d205_repo / ".planning/ROADMAP.md").write_text("broken live ROADMAP", encoding="utf-8")
    d205_cli(d205_good, None, "D-205 immutable revision ignores dirty checkout")

    def d205_variant(label: str, files: dict[str, str], expected: str, delete: tuple[str, ...] = ()) -> None:
        d205_git("checkout", "-q", "--", ".planning/ROADMAP.md")
        d205_git("checkout", "-q", d205_good)
        variant = d205_commit(files, label, delete)
        d205_cli(variant, expected, label)

    d205_variant("unauthorized sixth phase", {".planning/ROADMAP.md": d205_roadmap.replace(
        "20/21/22/23/23.1/24", "20/21/22/23/23.1/25")}, "plan-cap-phase-count")
    seventh = d205_roadmap + "\n### Phase 25: unauthorized\n\n**Plan cap**: 1\n"
    d205_variant("unauthorized seventh phase", {".planning/ROADMAP.md": seventh}, "plan-cap-phase-count")
    d205_variant("missing D-205 approval", {".planning/ROADMAP.md": d205_roadmap.replace(
        "approved only the exact active v0.4 phase set 20/21/22/23/23.1/24",
        "has no exception for the active v0.4 phase set")}, "plan-cap-phase-count")
    d205_variant("missing D-205 decision with roadmap approval retained", {},
                 "plan-cap-approved-exception", delete=(d205_decision_path,))
    contradictory_decisions = d205_decisions.replace(
        "This supersedes D-193/D-203 only on the prohibition against adding a sixth v0.4 phase.",
        "This does not supersede D-193/D-203 on the prohibition against adding a sixth v0.4 phase.", 1)
    if contradictory_decisions == d205_decisions:
        raise SystemExit("planning-hygiene self-test FAIL: contradictory D-205 mutant was not seeded")
    d205_variant("contradictory D-205 decision with roadmap approval retained",
                 {d205_decision_path: contradictory_decisions}, "plan-cap-approved-exception")
    d205_variant("altered historical cap", {".planning/ROADMAP.md": d205_roadmap.replace(
        "**Plan cap**: 9", "**Plan cap**: 8", 1)}, "plan-cap-approved-exception")
    d205_variant("41st actual plan", {".planning/phases/GB-24-some-title/24-02-PLAN-extra.md": PRIMARY_FRONTMATTER_TEXT},
                 "plan-cap-actual-total")
    d205_variant("decorated second Phase 24 plan", {
        ".planning/phases/GB-24-some-title/24-02-PLAN-extra.md": PRIMARY_FRONTMATTER_TEXT},
        "plan-cap-d205-phase24-plan")
    d205_variant("Phase 24 gap plan", {
        ".planning/phases/GB-24-some-title/24-01-PLAN.md": GAP_FRONTMATTER_TEXT}, "plan-cap-d205-phase24-gap")
    quoted_gap_key = GAP_FRONTMATTER_TEXT.replace("gap_closure: true", '"gap_closure": true', 1)
    if quoted_gap_key == GAP_FRONTMATTER_TEXT:
        raise SystemExit("planning-hygiene self-test FAIL: quoted Phase 24 gap key mutant was not seeded")
    d205_variant("Phase 24 quoted gap_closure key", {
        ".planning/phases/GB-24-some-title/24-01-PLAN.md": quoted_gap_key}, "plan-cap-d205-phase24-gap")
    flow_gap_key = "---\n{phase: x, gap_closure: true}\n---\n\n# Gap plan\n"
    d205_variant("Phase 24 flow-map gap_closure key", {
        ".planning/phases/GB-24-some-title/24-01-PLAN.md": flow_gap_key}, "plan-cap-d205-phase24-gap")
    d205_variant("attempted reserve renewal", {".planning/ROADMAP.md": renewed_path_roadmap}, "plan-cap-d205-reserve")
    return controls


def self_test_v04_gap_assessment(base: Path, source_repo: Path, source_rev: str) -> int:
    """Run report and handoff mutations through the committed production CLI in an alternate-object fixture."""
    controls = 0
    phase_dir = ".planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps"
    report_path = V04_GAP_REPORT_PATH
    summary_path = f"{phase_dir}/24-01-SUMMARY.md"
    validation_path = f"{phase_dir}/24-VALIDATION.md"
    continuation_path = f"{phase_dir}/.continue-here.md"
    uat_path = f"{phase_dir}/24-UAT.md"
    state_path = ".planning/STATE.md"
    repo = base / "v04-gap-assessment-repo"
    repo.mkdir()
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "SYSTEMROOT", "TMPDIR", "TEMP", "TMP")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
               GIT_AUTHOR_NAME="fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
               GIT_COMMITTER_NAME="fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid")

    def git(*args: str) -> str:
        done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                              check=True, env=env, timeout=60)
        return done.stdout.strip()

    def repo_head() -> str | None:
        head = (repo / ".git/HEAD").read_text(encoding="ascii").strip()
        if head.startswith("ref: "):
            ref_path = repo / ".git" / head[5:]
            return ref_path.read_text(encoding="ascii").strip() if ref_path.exists() else None
        return head or None

    git("init", "-q")
    object_dir_raw = git_run(source_repo, "rev-parse", "--git-path", "objects")
    if object_dir_raw.returncode != 0:
        raise SystemExit("planning-hygiene self-test FAIL: could not locate source object store")
    object_dir = Path(object_dir_raw.stdout.decode("utf-8").strip())
    if not object_dir.is_absolute():
        object_dir = source_repo.resolve() / object_dir
    alternate = repo / ".git/objects/info/alternates"
    alternate.parent.mkdir(parents=True, exist_ok=True)
    alternate.write_text(str(object_dir.resolve()) + "\n", encoding="utf-8")
    fixture_paths = (
        report_path,
        V04_GAP_REQUIREMENTS_PATH,
        V04_GAP_AUDIT_PATH,
        ".planning/context/DECISIONS.md",
        ".planning/ROADMAP.md",
        ".planning/phases/GB-20-fixture-admission-tune-up/20-VERIFICATION.md",
        ".planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-VERIFICATION.md",
        f"{phase_dir}/24-01-PLAN.md",
    )
    snapshot: dict[str, bytes] = {}
    for source_path in fixture_paths:
        raw = commit_file(source_repo, source_rev, source_path)
        if raw is None:
            raise SystemExit(f"planning-hygiene self-test FAIL: source candidate {source_rev} lacks {source_path}")
        snapshot[source_path] = raw
    for rel, content in snapshot.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    git("add", "-A", "--", ".planning")
    git("commit", "-q", "-m", "canonical immutable Phase 24 report fixture")
    git("symbolic-ref", "HEAD")
    def fixture_head() -> str:
        head = (repo / ".git/HEAD").read_text(encoding="ascii").strip()
        if head.startswith("ref: "):
            return (repo / ".git" / head[5:]).read_text(encoding="ascii").strip()
        return head
    report_rev = fixture_head()
    report_fields, _ = frontmatter_fields(snapshot[report_path].decode("utf-8", errors="strict"))
    baseline_rev = report_fields["baseline_commit"]

    def checkout(revision: str) -> None:
        git("checkout", "-q", revision)

    def commit(files: dict[str, bytes | str], message: str, delete: tuple[str, ...] = (),
               stage_new: bool = False) -> str:
        parent_rev = fixture_head() or None
        touched: list[str] = []
        for rel, content in files.items():
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            data = content if isinstance(content, bytes) else content.encode("utf-8")
            path.write_bytes(data)
            touched.append(rel)
        for rel in delete:
            git("rm", "-q", "--", rel)
            touched.append(rel)
        if stage_new or delete:
            for rel in sorted(set(touched)):
                if rel not in delete:
                    git("add", "--", rel)
            git("commit", "-q", "-m", message)
        else:
            git("commit", "-q", "-a", "-m", message)
        revision = fixture_head()
        cache_fixture_commit_snapshot(repo, parent_rev, revision, files, delete)
        return revision

    def cli(stage: str, revision: str, expected: str | None, label: str) -> None:
        nonlocal controls
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = main(["--check", "v04-gap-assessment", "--stage", stage, "--rev", revision,
                              "--baseline-rev", baseline_rev, "--repo", str(repo)])
        error_text = stderr.getvalue()
        if expected is None:
            wanted = f"v04-gap-assessment pass stage={stage}"
            if exit_code != 0 or stdout.getvalue().strip() != wanted:
                raise SystemExit(f"planning-hygiene self-test FAIL: {label} should pass: {exit_code} {stdout.getvalue()} {error_text}")
        elif exit_code != 1 or expected not in error_text:
            raise SystemExit(f"planning-hygiene self-test FAIL: {label} should fail with {expected}: {exit_code} {error_text}")
        controls += 1
        if revision != report_rev:
            COMMIT_SNAPSHOT_CACHE.pop((str(repo.resolve()), revision), None)

    def canonical() -> None:
        cli("report", report_rev, None, "canonical committed report")

    def report_text(revision: str = report_rev) -> str:
        raw = commit_file(repo, revision, report_path)
        if raw is None:
            raise SystemExit(f"planning-hygiene self-test FAIL: report fixture missing at {revision}")
        return raw.decode("utf-8", errors="strict")

    def row_span(document: str, row_id: str, collection: str = "requirement_assessments") -> tuple[int, int]:
        marker = f'  - phase: "{row_id}"\n' if collection == "phase_assessments" else f"  - id: {row_id}\n"
        start = document.find(marker)
        collection_start = document.find(collection + ":")
        end_collection = document.find("\nphase_assessments:", collection_start) if collection == "requirement_assessments" else len(document)
        if start < collection_start or start < 0 or (end_collection >= 0 and start > end_collection):
            raise SystemExit(f"planning-hygiene self-test FAIL: missing {row_id} row in {collection}")
        next_marker = "\n  - phase: " if collection == "phase_assessments" else "\n  - id: "
        next_row = document.find(next_marker, start + len(marker))
        end = min((value for value in (next_row, end_collection if end_collection >= 0 else len(document)) if value >= 0),
                  default=len(document))
        return start, end

    def mutate_row(document: str, row_id: str, mutate: Callable[[str], str],
                   collection: str = "requirement_assessments") -> str:
        start, end = row_span(document, row_id, collection)
        changed = mutate(document[start:end])
        if changed == document[start:end]:
            raise SystemExit(f"planning-hygiene self-test FAIL: mutation did not change {row_id}")
        return document[:start] + changed + document[end:]

    def mutate_report(label: str, mutation: Callable[[str], str], expected: str) -> None:
        checkout(report_rev)
        candidate = commit({report_path: mutation(report_text())}, label)
        cli("report", candidate, expected, label)

    canonical()
    # Dirty checkout facts cannot contaminate the already committed report candidate.
    (repo / V04_GAP_REQUIREMENTS_PATH).write_text("dirty false completion", encoding="utf-8")
    (repo / V04_GAP_AUDIT_PATH).write_text("dirty closed audit", encoding="utf-8")
    (repo / report_path).write_text("dirty substituted report", encoding="utf-8")
    cli("report", report_rev, None, "dirty checkout does not change immutable report")
    git("checkout", "--", V04_GAP_REQUIREMENTS_PATH, V04_GAP_AUDIT_PATH, report_path)

    # Canonical exact-source checks bind every original criterion and owner.
    canonical()
    for requirement in V04_GAP_EXPECTED:
        def drift_criterion_and_owner(block: str) -> str:
            block = re.sub(r"(?m)^    original_criterion:.*$", "    original_criterion: altered criterion", block, count=1)
            return re.sub(r"(?m)^    original_owner:.*$", "    original_owner: Phase 99", block, count=1)
        mutate_report(f"criterion and owner drift {requirement}",
                      lambda doc, requirement=requirement: mutate_row(doc, requirement, drift_criterion_and_owner),
                      "v04-gap-assessment-requirements")
    canonical()

    for requirement in ("FIXT-01", "RIGHTS-01", "DIAG-01", "DIAG-02"):
        mutate_report(f"false completion {requirement}",
                      lambda doc, requirement=requirement: mutate_row(
                          doc, requirement, lambda row: row.replace("tracker_status: Pending", "tracker_status: Complete", 1)),
                      "v04-gap-assessment-requirements")
    for requirement in ("GAME-01", "GAME-02", "FEED-01"):
        mutate_report(f"tracker audit conflation {requirement}",
                      lambda doc, requirement=requirement: mutate_row(
                          doc, requirement, lambda row: row.replace("milestone_audit_status: partial", "milestone_audit_status: satisfied", 1)),
                      "v04-gap-assessment-requirements")
    for phase in ("20", "21"):
        mutate_report(f"stale phase promotion {phase}",
                      lambda doc, phase=phase: mutate_row(
                          doc, phase, lambda row: row.replace("current_audit_observation: stale", "current_audit_observation: fresh", 1),
                          "phase_assessments"), "v04-gap-assessment-phase")
    mutate_report("diagnostic metadata recast as execution",
                  lambda doc: mutate_row(doc, "DIAG-02", lambda row: row.replace(
                      "approved metadata-only scope passed; no case executed", "513 cases admitted and executed", 1)),
                  "v04-gap-assessment-requirements")
    canonical()

    cases = (
        ("duplicate assessment row", lambda doc: (lambda span: doc[:span[1]] + "\n" + doc[span[0]:span[1]] + doc[span[1]:])(row_span(doc, "GAME-01")),
         "v04-gap-assessment-requirements"),
        ("missing assessment row", lambda doc: (lambda span: doc[:span[0]] + doc[span[1]:])(row_span(doc, "REL-01")),
         "v04-gap-assessment-requirements"),
        ("extra assessment row", lambda doc: mutate_row(doc, "REL-01", lambda row: row.replace("id: REL-01", "id: EXTRA-01", 1)),
         "v04-gap-assessment-requirements"),
        ("malformed protected alias", lambda doc: doc.replace("milestone: v0.4", "milestone: v0.4\nmilestone : closed", 1),
         "v04-gap-assessment-frontmatter"),
        ("closed milestone claim", lambda doc: doc.replace("milestone_status: open", "milestone_status: closed", 1),
         "v04-gap-assessment-field"),
        ("passed audit claim", lambda doc: doc.replace("milestone_audit_status: gaps_found", "milestone_audit_status: passed", 1),
         "v04-gap-assessment-field"),
        ("input substitution", lambda doc: doc.replace(f"assessment_input_commit: {V04_GAP_INPUT_REV}",
                                                        f"assessment_input_commit: {baseline_rev}", 1),
         "v04-gap-assessment-input"),
        ("source digest drift", lambda doc: re.sub(r"(?m)^(    sha256: )[0-9a-f]{64}$", lambda match: match.group(1) + "0" * 64, doc, count=1),
         "v04-gap-assessment-source-records"),
    )
    for label, mutation, expected in cases:
        mutate_report(label, mutation, expected)
    canonical()

    for label, revision, expected in (("abbreviated revision", source_rev[:12], "v04-gap-assessment-rev"),
                                      ("symbolic revision", "HEAD", "v04-gap-assessment-rev"),
                                      ("nonexistent revision", "0" * 40, "v04-gap-assessment-rev")):
        cli("report", revision, expected, label)
    saved_input_rev = V04_GAP_INPUT_REV
    try:
        globals()["V04_GAP_INPUT_REV"] = report_rev
        cli("report", report_rev, "v04-gap-assessment-input", "input equals containing revision")
    finally:
        globals()["V04_GAP_INPUT_REV"] = saved_input_rev

    # A full but incomplete input commit proves source-blob absence is distinct from ref syntax errors.
    checkout(report_rev)
    missing_input_files: dict[str, bytes] = {}
    for source_path in V04_GAP_SOURCE_PATHS:
        if source_path == ".planning/context/DECISIONS.md":
            continue
        source_blob = commit_file(source_repo, V04_GAP_INPUT_REV, source_path)
        if source_blob is None:
            raise SystemExit(f"planning-hygiene self-test FAIL: cannot seed missing-source input without {source_path}")
        missing_input_files[source_path] = source_blob
    missing_input = commit(missing_input_files, "remove required immutable input source",
                           delete=(".planning/context/DECISIONS.md",), stage_new=True)
    altered_report = report_text().replace(f"assessment_input_commit: {V04_GAP_INPUT_REV}",
                                           f"assessment_input_commit: {missing_input}", 1)
    missing_source_candidate = commit({report_path: altered_report}, "point assessment at source-missing input")
    try:
        globals()["V04_GAP_INPUT_REV"] = missing_input
        cli("report", missing_source_candidate, "v04-gap-assessment-source-records", "missing required input source")
    finally:
        globals()["V04_GAP_INPUT_REV"] = saved_input_rev
    COMMIT_SNAPSHOT_CACHE.pop((str(repo.resolve()), missing_input), None)

    checkout(report_rev)
    baseline_audit = commit_file(source_repo, baseline_rev, V04_GAP_AUDIT_PATH)
    if baseline_audit is None:
        raise SystemExit("planning-hygiene self-test FAIL: protected baseline audit blob is absent")
    stale_audit_candidate = commit({V04_GAP_AUDIT_PATH: baseline_audit}, "substitute stale historical audit")
    cli("report", stale_audit_candidate, "v04-gap-assessment-audit", "stale audit substitution")
    checkout(report_rev)
    historical_path = V04_GAP_HISTORICAL_REPORTS["RIGHTS-01"]
    historical = commit_file(repo, report_rev, historical_path)
    if historical is None:
        raise SystemExit("planning-hygiene self-test FAIL: protected historical report fixture is absent")
    drifted_history = commit({historical_path: historical + b"\nunauthorized historical byte drift\n"},
                            "mutate protected historical report bytes")
    cli("report", drifted_history, "v04-gap-assessment-history", "protected historical byte drift")
    canonical()

    owner_lines = ("FIXT-01 — Pending, original owner Phase 21; RIGHTS-01 — Pending, original owner Phase 20; "
                   "DIAG-01 — Pending, original owner Phase 22; DIAG-02 — Pending, original owner Phase 22.")
    limits = ("v0.4 stays open with gaps_found. Phase 20 and Phase 21 remain stale. D-103 unfulfilled. "
              "Next: $gsd-verify-work 24. no broad local suite, no third local lifecycle retest, no release retry, "
              "no tag/asset/rights action, no fixture admission.")
    links_summary = ("[evidence](24-EVIDENCE.md) [validation](24-VALIDATION.md) "
                     "[closure](24-UAT.md) [continuation](.continue-here.md)")
    summary = (
        "---\nphase: GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps\nplan: \"01\"\n"
        "status: complete\nrequirements-completed: []\n---\n\n"
        "# Phase 24 Plan 01 Summary\n\n"
        "Phase 24 execution/automated closure complete; phase verification pending. The orchestrator is the next actor. "
        f"Assessment input `{V04_GAP_INPUT_REV}`; protected baseline `{baseline_rev}`; "
        f"tested checker/report candidate: `{source_rev}`. requirements-completed: []\n\n"
        f"{owner_lines} {limits}\n\n{links_summary}\n")
    continuation = ("# Phase 24 Continuation\n\n"
                    f"{owner_lines} {limits} The orchestrator is next; use `$gsd-verify-work 24`.\n\n"
                    "[evidence](24-EVIDENCE.md) [summary](24-01-SUMMARY.md) "
                    "[validation](24-VALIDATION.md) [closure](24-UAT.md)\n")
    state = ("# Project State\n\n## Current Position\nPhase 24 execution is complete; phase verification pending.\n\n"
             "Current Handoff: Phase 24 execution/automated closure complete. "
             f"{owner_lines} {limits}\n\n"
             "[evidence](phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-EVIDENCE.md) "
             "[summary](phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-01-SUMMARY.md) "
             "[validation](phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-VALIDATION.md) "
             "[closure](phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-UAT.md)\n\n"
             "## Accumulated Context\n")
    validation = "# Validation\n\nplanning-hygiene 24-01-T1-map 24-01-T2-controls 24-01-T3-closure\n"
    handoff_files: dict[str, bytes | str] = {
        summary_path: summary,
        continuation_path: continuation,
        state_path: state,
        validation_path: validation,
        uat_path: "# Generated shared closure\n",
    }
    checkout(report_rev)
    handoff_rev = commit(handoff_files, "canonical Phase 24 handoff fixture", stage_new=True)
    cli("handoff", handoff_rev, None, "canonical committed pending-verification handoff")

    def handoff_mutant(label: str, path: str, mutation: Callable[[str], str],
                       expected: str = "v04-gap-assessment-handoff") -> None:
        checkout(handoff_rev)
        current = commit_file(repo, handoff_rev, path)
        if current is None:
            raise SystemExit(f"planning-hygiene self-test FAIL: missing handoff fixture {path}")
        original = current.decode("utf-8", errors="strict")
        changed = mutation(original)
        if changed == original:
            raise SystemExit(f"planning-hygiene self-test FAIL: handoff mutation {label} was not seeded")
        candidate = commit({path: changed}, label)
        cli("handoff", candidate, expected, label)

    handoff_mutant("summary requirement completion", summary_path,
                   lambda doc: doc.replace("requirements-completed: []", "requirements-completed: [FIXT-01]", 1))
    handoff_mutant("quoted requirements-completed alias", summary_path,
                   lambda doc: doc.replace("requirements-completed: []",
                                           'requirements-completed: []\n"requirements-completed": [FIXT-01]', 1))
    handoff_mutant("quoted status alias", summary_path,
                   lambda doc: doc.replace("status: complete", 'status: complete\n"status": incomplete', 1))
    handoff_mutant("quoted phase alias", summary_path,
                   lambda doc: doc.replace(
                       "phase: GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps",
                       'phase: GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps\n'
                       '"phase": GB-23.1-close-v0-4-requirement-and-verification-gaps', 1))
    handoff_mutant("summary owner reassignment", summary_path,
                   lambda doc: doc.replace("FIXT-01 — Pending, original owner Phase 21",
                                           "FIXT-01 — Pending, original owner Phase 20", 1))
    handoff_mutant("summary chooses audit instead of verification", summary_path,
                   lambda doc: doc.replace("$gsd-verify-work 24", "$gsd-audit-milestone v0.4", 1))
    handoff_mutant("continuation chooses audit instead of verification", continuation_path,
                   lambda doc: doc.replace("$gsd-verify-work 24", "$gsd-audit-milestone v0.4"))
    handoff_mutant("D-103 falsely fulfilled", state_path,
                   lambda doc: doc.replace("D-103 unfulfilled", "D-103 fulfilled", 1))
    handoff_mutant("milestone falsely closed", state_path,
                   lambda doc: doc.replace("v0.4 stays open with gaps_found", "v0.4 is closed with gaps_found", 1))
    handoff_mutant("missing evidence link", summary_path,
                   lambda doc: doc.replace("[evidence](24-EVIDENCE.md)", "[evidence](#missing)", 1))
    cli("handoff", handoff_rev, None, "canonical handoff remains immutable after checkout mutations")
    return controls


def self_test_v04_reconciliation(base: Path, source_repo: Path) -> int:
    """Exercise report/handoff contracts through the real CLI in a disposable Git repository."""
    controls = 0
    git_read_cache: dict[tuple[str, tuple[str, ...]], subprocess.CompletedProcess[bytes]] = {}
    source_git_run = git_run

    def cached_git_run(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
        key = (str(repo.resolve()), args)
        if key not in git_read_cache:
            git_read_cache[key] = source_git_run(repo, *args)
        return git_read_cache[key]

    line_cases = (
        ("", []),
        ("one", ["one"]),
        ("one\n", ["one"]),
        ("one\n\n", ["one", ""]),
        ("one\r", ["one"]),
        ("one\r\n", ["one"]),
        ("one\u2028two", ["one\u2028two"]),
        ("one\u2029two", ["one\u2029two"]),
        ("one\vtwo", ["one\vtwo"]),
        ("one\ftwo", ["one\ftwo"]),
    )
    for source, expected_lines in line_cases:
        actual_lines = visible_markdown_lines(source)
        if actual_lines != expected_lines:
            raise SystemExit(f"planning-hygiene self-test FAIL: Markdown line boundary {source!r}: "
                             f"{actual_lines!r} != {expected_lines!r}")
        controls += 1

    yaml_line_cases = (
        ("", "", []),
        ("one", "one", ["one"]),
        ("one\n", "one\n", ["one"]),
        ("one\r", "one\n", ["one"]),
        ("one\r\n", "one\n", ["one"]),
        ("one\r\ntwo\rthree", "one\ntwo\nthree", ["one", "two", "three"]),
        ("one\u0085two", "one\u0085two", ["one\u0085two"]),
        ("one\u2028two", "one\u2028two", ["one\u2028two"]),
        ("one\u2029two", "one\u2029two", ["one\u2029two"]),
    )
    for source, expected_text, expected_lines in yaml_line_cases:
        actual_text, actual_lines = yaml_source_lines(source)
        if actual_text != expected_text or actual_lines != expected_lines:
            raise SystemExit(f"planning-hygiene self-test FAIL: YAML line boundary {source!r}: "
                             f"{actual_text!r} {actual_lines!r} != {expected_text!r} {expected_lines!r}")
        controls += 1

    plain_key_cases = (
        ("phase: value", "phase"),
        ("phase : value", "phase"),
        ("phase\t: value", "phase"),
        ("phase \t : value", "phase"),
        (" phase: value", None),
        ("phase value", None),
        ("phase name: value", None),
        ("phase\u00a0: value", None),
    )
    for source, expected_key in plain_key_cases:
        actual_key = parse_frontmatter_plain_key(source)
        if actual_key != expected_key:
            raise SystemExit(f"planning-hygiene self-test FAIL: plain root key {source!r}: "
                             f"{actual_key!r} != {expected_key!r}")
        controls += 1

    scalar_cases = (
        ("pending", "pending"),
        (" 'pending' \t", "pending"),
        ('"pending"', "pending"),
        ("pending'", "pending'"),
        ('pending"', 'pending"'),
        ("'pending", None),
        ('"pending', None),
        ("'pending\"", None),
        ('"pending\'', None),
        ("''pending''", None),
        ('""pending""', None),
        ('"pen\\ding"', None),
    )
    for source, expected_value in scalar_cases:
        actual_value = decode_frontmatter_scalar(source)
        if actual_value != expected_value:
            raise SystemExit(f"planning-hygiene self-test FAIL: scalar decoder {source!r}: "
                             f"{actual_value!r} != {expected_value!r}")
        controls += 1

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

    def repo_head() -> str | None:
        head = (repo / ".git/HEAD").read_text(encoding="ascii").strip()
        if head.startswith("ref: "):
            ref_path = repo / ".git" / head[5:]
            return ref_path.read_text(encoding="ascii").strip() if ref_path.exists() else None
        return head or None

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

    def commit(files: dict[str, str], message: str, *, stage_new: bool = False) -> str:
        parent_rev = repo_head()
        for relative, content in files.items():
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode("utf-8"))
        if stage_new:
            git("add", "--", *files)
            git("commit", "-q", "-m", message)
        else:
            # Every later fixture modifies an already committed path. `-a`
            # avoids a redundant Git process while keeping the same snapshot.
            git("commit", "-q", "-a", "-m", message)
        revision = repo_head()
        if revision is None:
            raise SystemExit("planning-hygiene self-test FAIL: fixture commit did not create HEAD")
        cache_fixture_commit_snapshot(repo, parent_rev, revision, files)
        return revision

    baseline_rev = commit(base_files, "fixture baseline", stage_new=True)

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
requirements:
  FIXT-01: pending
  RIGHTS-01: pending
  DIAG-01: pending
  DIAG-02: pending
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

    report_rev = commit({report_path: report_content}, "add historical report", stage_new=True)

    def cli_check(stage: str, rev: str, expected_code: str | None = None,
                  check_baseline: str | None = None) -> None:
        nonlocal controls
        output, error = io.StringIO(), io.StringIO()
        original_git_run = globals()["git_run"]
        globals()["git_run"] = cached_git_run
        try:
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                result = main(["--check", "v04-reconciliation", "--stage", stage, "--rev", rev,
                               "--baseline-rev", check_baseline or baseline_rev, "--repo", str(repo)])
        finally:
            globals()["git_run"] = original_git_run
        if expected_code is None:
            expected_line = f"v04-reconciliation pass stage={stage}"
            if result != 0 or output.getvalue().strip() != expected_line:
                commit_message = git("show", "-s", "--format=%s", rev)
                raise SystemExit(f"planning-hygiene self-test FAIL: {stage} CLI positive at {rev}: "
                                 f"{commit_message}: {result} {output.getvalue()} {error.getvalue()}")
        elif result != 1 or expected_code not in error.getvalue():
            raise SystemExit(f"planning-hygiene self-test FAIL: {stage} CLI negative wanted {expected_code}: {result} {output.getvalue()} {error.getvalue()}")
        controls += 1

    def cli_pre_fix_accepts(stage: str, rev: str, label: str, checker: Path | None = None) -> None:
        nonlocal controls
        result = subprocess.run(
            ["python3", "-I", str(checker or pre_fix_checker), "--check", "v04-reconciliation",
             "--stage", stage, "--rev", rev, "--baseline-rev", baseline_rev,
             "--repo", str(repo)], capture_output=True, text=True, check=False, env=env, timeout=60)
        expected = f"v04-reconciliation pass stage={stage}"
        if result.returncode != 0 or result.stdout.strip() != expected:
            raise SystemExit(f"planning-hygiene self-test FAIL: D-200 checker did not causally accept {label}: "
                             f"{result.returncode} {result.stdout} {result.stderr}")
        controls += 1

    # These committed-source controls prove the prior implementation accepted
    # representative mutants when every unrelated report fact was valid.
    d200_source_rev = "9991327df736f668bd8c98f4fd9441a4c563905b"
    d200_source = git_run(source_repo, "show",
                          f"{d200_source_rev}:tests/scripts/verify-planning-hygiene.py")
    if d200_source.returncode != 0:
        raise SystemExit("planning-hygiene self-test FAIL: D-200 checker source is unavailable")
    pre_fix_checker = base / "verify-planning-hygiene-d200.py"
    pre_fix_checker.write_bytes(d200_source.stdout)
    phase_field = "phase: GB-22-composition-and-microtest-evidence\n"
    cr03_pre_fix = report_content.replace(
        phase_field,
        "phase: GB-21-cgb-game-progress-and-scene-regressions\n"
        "phase : GB-22-composition-and-microtest-evidence\n", 1)
    cr03_pre_fix_rev = commit({report_path: cr03_pre_fix}, "reproduce D-200 spaced duplicate-key acceptance")
    cli_pre_fix_accepts("report", cr03_pre_fix_rev, "a spaced duplicate root key")
    cr04_pre_fix = report_content.replace("status: passed\n", 'status: "passed\n', 1)
    cr04_pre_fix_rev = commit({report_path: cr04_pre_fix}, "reproduce D-200 unmatched quote acceptance")
    cli_pre_fix_accepts("report", cr04_pre_fix_rev, "an unmatched leading scalar quote")

    # D-201 still accepts both newly reviewed D-202 mutants through the real CLI.
    # Keep these RED fixtures valid in every unrelated report and provenance field.
    d201_source_rev = "6df11f34ce19ee54c4b3270ed6214c61dbdd7927"
    d201_source = git_run(source_repo, "show",
                          f"{d201_source_rev}:tests/scripts/verify-planning-hygiene.py")
    if d201_source.returncode != 0:
        raise SystemExit("planning-hygiene self-test FAIL: D-201 checker source is unavailable")
    d201_checker = base / "verify-planning-hygiene-d201.py"
    d201_checker.write_bytes(d201_source.stdout)
    cr05_pre_fix = report_content.replace(
        phase_field,
        '"phase": GB-21-cgb-game-progress-and-scene-regressions\n' + phase_field, 1)
    cr05_pre_fix_rev = commit({report_path: cr05_pre_fix},
                              "reproduce D-201 quoted phase-root alias acceptance")
    cli_pre_fix_accepts("report", cr05_pre_fix_rev,
                        "a conflicting quoted protected phase root", d201_checker)
    cr06_extra_row = ("  - id : EXTRA-01\n    status: Satisfied\n"
                      "    original_owner: Phase 99\n")
    cr06_pre_fix = report_content.replace(
        "requirement_dispositions:\n" + dispositions,
        "requirement_dispositions:\n" + cr06_extra_row + dispositions, 1)
    cr06_pre_fix_rev = commit({report_path: cr06_pre_fix},
                              "reproduce D-201 spaced disposition-row acceptance")
    cli_pre_fix_accepts("report", cr06_pre_fix_rev,
                        "a complete contradictory disposition row with a spaced item key", d201_checker)

    cr06_tab_pre_fix = report_content.replace(
        "requirement_dispositions:\n" + dispositions,
        "requirement_dispositions:\n" + cr06_extra_row.replace("id :", "id\t:", 1) + dispositions, 1)
    cr06_tab_pre_fix_rev = commit({report_path: cr06_tab_pre_fix},
                                  "reproduce D-201 tabbed disposition-row acceptance")
    cli_pre_fix_accepts("report", cr06_tab_pre_fix_rev,
                        "a complete contradictory disposition row with a tabbed item key", d201_checker)

    # D-202's exact reviewed checker still accepts a contradictory row whose
    # unsupported non-ASCII prefix makes the object reader stop at the boundary.
    d202_source_rev = "af36fa2f4c0f35dc6b537a3e736f5cd264b83593"
    d202_source = git_run(source_repo, "show",
                          f"{d202_source_rev}:tests/scripts/verify-planning-hygiene.py")
    if d202_source.returncode != 0:
        raise SystemExit("planning-hygiene self-test FAIL: D-202 checker source is unavailable")
    d202_checker = base / "verify-planning-hygiene-d202.py"
    d202_checker.write_bytes(d202_source.stdout)
    cr07_extra_row = ("\u00a0  - id: EXTRA-01\n    status: Satisfied\n"
                      "    original_owner: Phase 99\n")
    cr07_canonical_dispositions = f"requirement_dispositions:\n{dispositions}\n"
    cr07_mutant = report_content.replace(
        cr07_canonical_dispositions,
        cr07_canonical_dispositions + cr07_extra_row, 1)
    if cr07_mutant == report_content:
        raise SystemExit("planning-hygiene self-test FAIL: could not seed the CR-07 disposition row")
    cr07_mutant_rev = commit({report_path: cr07_mutant},
                             "reproduce D-202 non-ASCII disposition-row acceptance")
    d202_namespace = {
        "__name__": "verify_planning_hygiene_d202",
        "__file__": str(source_repo / "tests/scripts/verify-planning-hygiene.py"),
        "git_run": cached_git_run,
    }
    exec(compile(d202_source.stdout, str(d202_checker), "exec"), d202_namespace)
    output, error = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
        d202_result = d202_namespace["main"]([
            "--check", "v04-reconciliation", "--stage", "report", "--rev", cr07_mutant_rev,
            "--baseline-rev", baseline_rev, "--repo", str(repo)])
    if d202_result != 0 or output.getvalue().strip() != "v04-reconciliation pass stage=report":
        raise SystemExit("planning-hygiene self-test FAIL: D-202 checker did not causally accept the "
                         f"U+00A0-prefixed contradictory disposition row: {d202_result} "
                         f"{output.getvalue()} {error.getvalue()}")
    controls += 1
    cli_check("report", cr07_mutant_rev, "v04-report-requirements")

    object_boundary_text = (
        "---\nrequirement_dispositions:\n"
        "  - id: FIXT-01\n    status: Pending\n    original_owner: Phase 21\n"
        "    note: |-\n      status: Satisfied\n      original_owner: Phase 99\n"
        "# column-zero comment does not end the object block\n"
        "  - id: RIGHTS-01\n    status: Pending\n    original_owner: Phase 20\n"
        "next_root: recognized\n---\n"
    )
    expected_objects = [
        {"id": "FIXT-01", "status": "Pending", "original_owner": "Phase 21", "note": "|-"},
        {"id": "RIGHTS-01", "status": "Pending", "original_owner": "Phase 20"},
    ]
    actual_objects = frontmatter_objects(object_boundary_text, "requirement_dispositions")
    if actual_objects != expected_objects:
        raise SystemExit("planning-hygiene self-test FAIL: object comments, block scalar, or root transition "
                         f"changed: {actual_objects!r} != {expected_objects!r}")
    controls += 1

    # The root lexer retains both spellings before any dict conversion; both
    # conflict orders and both permitted horizontal spaces are present here.
    phase_conflicts = report_content.replace(
        phase_field,
        "phase: GB-21-cgb-game-progress-and-scene-regressions\n"
        "phase : GB-22-composition-and-microtest-evidence\n"
        "phase: GB-22-composition-and-microtest-evidence\n"
        "phase\t: GB-21-cgb-game-progress-and-scene-regressions\n", 1)
    phase_conflicts_rev = commit({report_path: phase_conflicts},
                                 "reject spaced and tabbed duplicate root keys in both orders")
    cli_check("report", phase_conflicts_rev, "v04-report-frontmatter-duplicate")

    # Protected sequence/object roots must be singular and canonical, even when
    # the contradictory alias appears on either side of the accepted block.
    sequence_alias_before = "unresolved_gates :\n  - contradictory gate before\n"
    sequence_alias_after = "unresolved_gates\t:\n  - contradictory gate after\n"
    sequence_conflicts = report_content.replace(
        "unresolved_gates:\n", sequence_alias_before + "unresolved_gates:\n", 1)
    sequence_conflicts = sequence_conflicts.replace(
        "requirements_satisfied: []\n", sequence_alias_after + "requirements_satisfied: []\n", 1)
    object_alias_before = "requirement_dispositions\t:\n  - id: FIXT-01\n    status: Satisfied\n    original_owner: Phase 99\n"
    object_alias_after = "requirement_dispositions :\n  - id: FIXT-01\n    status: Satisfied\n    original_owner: Phase 99\n"
    sequence_conflicts = sequence_conflicts.replace(
        "requirement_dispositions:\n", object_alias_before + "requirement_dispositions:\n", 1)
    sequence_conflicts = sequence_conflicts.replace(
        "\n---\n", "\n" + object_alias_after + "---\n", 1)
    sequence_conflicts_rev = commit({report_path: sequence_conflicts},
                                    "reject contradictory sequence and object aliases before and after roots")
    cli_check("report", sequence_conflicts_rev, "v04-report-frontmatter-duplicate")

    sequence_alias_only = report_content.replace("unresolved_gates:\n", "unresolved_gates :\n", 1)
    sequence_alias_only_rev = commit({report_path: sequence_alias_only},
                                     "reject lone whitespace sequence root")
    cli_check("report", sequence_alias_only_rev, "v04-report-gates")
    object_alias_only = report_content.replace("requirement_dispositions:\n",
                                               "requirement_dispositions\t:\n", 1)
    object_alias_only_rev = commit({report_path: object_alias_only}, "reject lone tabbed object root")
    cli_check("report", object_alias_only_rev, "v04-report-requirements")

    def root_alias_form(root: str, form: str) -> str:
        if form == "single-quoted":
            return f"'{root}':"
        if form == "double-quoted":
            return '"' + root + '":'
        if form == "double-quoted escaped":
            return '"' + root.replace("e", "\\u0065", 1) + '":'
        if form == "tag then anchor":
            return f"!custom &d202_anchor {root}:"
        if form == "anchor then tag":
            return f"&d202_anchor !custom {root}:"
        if form == "same-line explicit key":
            return f"? {root}\n:"
        if form == "multiline explicit key":
            return f"?\n  {root}\n:"
        if form == "arbitrary alias name":
            return f"&d202_arbitrary {root}:\n*d202_arbitrary:"
        raise SystemExit(f"planning-hygiene self-test FAIL: unknown protected-root form {form!r}")

    def root_alias_block(root: str, form: str) -> str:
        header = root_alias_form(root, form)
        if form == "arbitrary alias name":
            anchor_header, alias_header = header.split("\n", 1)
            if root == "phase":
                value = " GB-21-cgb-game-progress-and-scene-regressions\n"
                return anchor_header + value + alias_header + value
            if root == "unresolved_gates":
                row = "  - d202_contradictory_gate\n"
            else:
                row = ("  - id: RIGHTS-01\n    status: Satisfied\n"
                       "    original_owner: Phase 99\n")
            return anchor_header + "\n" + row + alias_header + "\n" + row
        if root == "phase":
            return header + " GB-21-cgb-game-progress-and-scene-regressions\n"
        if root == "unresolved_gates":
            row = "  - d202_contradictory_gate\n"
        else:
            row = ("  - id: RIGHTS-01\n    status: Satisfied\n"
                   "    original_owner: Phase 99\n")
        return header + "\n" + row

    canonical_root_blocks = {
        "phase": "phase: GB-22-composition-and-microtest-evidence\n",
        "unresolved_gates": "unresolved_gates:\n" + gates + "\n",
        "requirement_dispositions": "requirement_dispositions:\n" + dispositions + "\n",
    }

    def mutate_protected_root(document: str, root: str, alias_block: str, position: str) -> str:
        canonical = canonical_root_blocks[root]
        if position == "alias only":
            replacement = alias_block
        elif position == "before canonical":
            replacement = alias_block + canonical
        elif position == "after canonical":
            replacement = canonical + alias_block
        else:
            raise SystemExit(f"planning-hygiene self-test FAIL: unknown root position {position!r}")
        mutated = document.replace(canonical, replacement, 1)
        if mutated == document:
            raise SystemExit(f"planning-hygiene self-test FAIL: could not seed {root} {position} fixture")
        return mutated

    root_forms = (
        "single-quoted", "double-quoted", "double-quoted escaped", "tag then anchor", "anchor then tag",
        "arbitrary alias name", "same-line explicit key", "multiline explicit key",
    )
    root_refusals = {
        "phase": ("v04-report-frontmatter-duplicate", "v04-report-field"),
        "unresolved_gates": ("v04-report-frontmatter-duplicate", "v04-report-gates"),
        "requirement_dispositions": ("v04-report-frontmatter-duplicate", "v04-report-requirements"),
    }
    for protected_root in canonical_root_blocks:
        duplicate_refusal, missing_root_refusal = root_refusals[protected_root]
        for form in root_forms:
            alias_block = root_alias_block(protected_root, form)
            for position in ("before canonical", "after canonical"):
                mutated = mutate_protected_root(report_content, protected_root, alias_block, position)
                mutant_rev = commit({report_path: mutated},
                                    f"reject {form} {protected_root} root {position}")
                cli_check("report", mutant_rev, duplicate_refusal)
            only_alias = mutate_protected_root(report_content, protected_root, alias_block, "alias only")
            only_alias_rev = commit({report_path: only_alias},
                                   f"reject {form} {protected_root} root without canonical spelling")
            cli_check("report", only_alias_rev, missing_root_refusal)

    spaced_item = ("  - id : EXTRA-01\n    status: Satisfied\n"
                   "    original_owner: Phase 99\n")
    tabbed_item = spaced_item.replace("id :", "id\t:", 1)
    canonical_dispositions = canonical_root_blocks["requirement_dispositions"]
    for label, extra_row in (("spaced", spaced_item), ("tabbed", tabbed_item)):
        before_rows = report_content.replace(
            "requirement_dispositions:\n",
            "requirement_dispositions:\n" + extra_row, 1)
        before_rows_rev = commit({report_path: before_rows},
                                 f"reject {label} contradictory disposition row before canonical entries")
        cli_check("report", before_rows_rev, "v04-report-requirements")
        after_rows = report_content.replace(
            canonical_dispositions, canonical_dispositions + extra_row, 1)
        after_rows_rev = commit({report_path: after_rows},
                                f"reject {label} contradictory disposition row after canonical entries")
        cli_check("report", after_rows_rev, "v04-report-requirements")

    extra_canonical_row = ("  - id: EXTRA-01\n    status: Satisfied\n"
                           "    original_owner: Phase 99\n")
    for position in ("before canonical", "after canonical"):
        if position == "before canonical":
            mutated = report_content.replace("requirement_dispositions:\n",
                                             "requirement_dispositions:\n" + extra_canonical_row, 1)
        else:
            mutated = report_content.replace(canonical_dispositions,
                                             canonical_dispositions + extra_canonical_row, 1)
        mutant_rev = commit({report_path: mutated},
                            f"reject complete extra disposition row {position}")
        cli_check("report", mutant_rev, "v04-report-requirements")

    malformed_rows = (
        ("orphan member", "    status: Satisfied\n    original_owner: Phase 99\n"),
        ("malformed item", "  - id EXTRA-01\n    status: Satisfied\n    original_owner: Phase 99\n"),
        ("unrecognized member row", "    ? status: Satisfied\n"),
    )
    for label, malformed_row in malformed_rows:
        mutated = report_content.replace("requirement_dispositions:\n",
                                         "requirement_dispositions:\n" + malformed_row, 1)
        mutant_rev = commit({report_path: mutated}, f"reject {label} in disposition object")
        cli_check("report", mutant_rev, "v04-report-requirements")
    cli_check("report", report_rev)

    # Exercise every remaining expected report field at the production CLI boundary.
    # Existing requirements-root aliases retain their dedicated map controls below.
    remaining_report_fields = (
        "source_head", "implementation_head", "evidence_head", "report_kind", "status",
        "metadata_cases", "shared_macro_cases", "inline_cases", "initial_no_protocol_exclusions",
        "admitted", "executed", "requirements_satisfied",
    )
    for protected_root in remaining_report_fields:
        canonical = next((line for line in report_content.split("\n")
                          if line.startswith(f"{protected_root}:")), None)
        if canonical is None:
            raise SystemExit(f"planning-hygiene self-test FAIL: missing canonical field {protected_root}")
        mutated = report_content.replace(canonical + "\n",
                                        f"'{protected_root}': conflicting\n{canonical}\n", 1)
        mutant_rev = commit({report_path: mutated},
                            f"reject quoted protected {protected_root} duplicate root")
        cli_check("report", mutant_rev, "v04-report-frontmatter-duplicate")

    # Direct controls exercise every existing scalar reader across unmatched,
    # mixed and repeated quote edges, plus canonical and supported quoted twins.
    scalar_readers = (
        ("field", lambda raw: frontmatter_fields(f"---\nphase: {raw}\n---\n")[0].get("phase")),
        ("sequence", lambda raw: frontmatter_sequence(f"---\nunresolved_gates:\n  - {raw}\n---\n", "unresolved_gates")),
        ("id", lambda raw: frontmatter_objects(
            f"---\nrequirement_dispositions:\n  - id: {raw}\n    status: Pending\n    original_owner: Phase 21\n---\n",
            "requirement_dispositions")),
        ("status", lambda raw: frontmatter_objects(
            f"---\nrequirement_dispositions:\n  - id: FIXT-01\n    status: {raw}\n    original_owner: Phase 21\n---\n",
            "requirement_dispositions")),
        ("original_owner", lambda raw: frontmatter_objects(
            f"---\nrequirement_dispositions:\n  - id: FIXT-01\n    status: Pending\n    original_owner: {raw}\n---\n",
            "requirement_dispositions")),
        ("map", lambda raw: frontmatter_mapping_pairs(
            f"---\nrequirements:\n  FIXT-01: {raw}\n---\n", "requirements")),
    )
    for reader_name, reader in scalar_readers:
        for raw, decoded in scalar_cases:
            actual = reader(raw)
            if reader_name == "sequence":
                expected = None if decoded is None else [decoded]
            elif reader_name in ("id", "status", "original_owner"):
                expected = None if decoded is None else [{
                    "id": decoded if reader_name == "id" else "FIXT-01",
                    "status": decoded if reader_name == "status" else "Pending",
                    "original_owner": decoded if reader_name == "original_owner" else "Phase 21",
                }]
            elif reader_name == "map":
                expected = [("FIXT-01", decoded)] if decoded is not None and re.fullmatch(
                    r"[A-Za-z0-9_-]+", decoded) else None
            else:
                expected = decoded
            if actual != expected:
                raise SystemExit(f"planning-hygiene self-test FAIL: {reader_name} scalar {raw!r}: "
                                 f"{actual!r} != {expected!r}")
            controls += 1

    # Each malformed scalar class also traverses its real report consumer so
    # the stable CLI refusal family, not merely the helper return value, is pinned.
    quoted_twins = report_content.replace(phase_field, 'phase: "GB-22-composition-and-microtest-evidence"\n', 1)
    quoted_twins = quoted_twins.replace(
        "unresolved_gates:\n" + gates,
        "unresolved_gates:\n" + "\n".join(f"  - '{gate}'" for gate in V04_UNRESOLVED_GATES), 1)
    quoted_twins = quoted_twins.replace(
        "requirement_dispositions:\n" + dispositions,
        "requirement_dispositions:\n" + "\n".join(
            f"  - id: '{requirement}'\n    status: \"Pending\"\n    original_owner: '{owner}'"
            for requirement, owner in V04_PENDING_OWNERS.items()), 1)
    quoted_twins = quoted_twins.replace(
        "requirements:\n  FIXT-01: pending\n  RIGHTS-01: pending\n  DIAG-01: pending\n  DIAG-02: pending",
        "requirements:\n  FIXT-01: \"pending\"\n  RIGHTS-01: 'pending'\n  DIAG-01: \"pending\"\n  DIAG-02: 'pending'", 1)
    quoted_twins_rev = commit({report_path: quoted_twins},
                              "accept supported matched scalar quote pairs through report CLI")
    cli_check("report", quoted_twins_rev)

    malformed_scalar_cases = (
        ("field", report_content.replace(phase_field, 'phase: "GB-22-composition-and-microtest-evidence\n', 1),
         "v04-report-field"),
        ("sequence", report_content.replace(V04_UNRESOLVED_GATES[0], '"' + V04_UNRESOLVED_GATES[0], 1),
         "v04-report-gates"),
        ("disposition id", report_content.replace("id: FIXT-01", "id: 'FIXT-01", 1),
         "v04-report-requirements"),
        ("disposition status", report_content.replace("status: Pending", "status: Pending'", 1),
         "v04-report-requirements"),
        ("disposition owner", report_content.replace("original_owner: Phase 21", 'original_owner: "Phase 21', 1),
         "v04-report-requirements"),
        ("requirements map", report_content.replace("  FIXT-01: pending", '  FIXT-01: "pending', 1),
         "v04-report-requirements"),
    )
    for label, malformed, refusal in malformed_scalar_cases:
        malformed_rev = commit({report_path: malformed}, f"reject malformed {label} scalar quoting")
        cli_check("report", malformed_rev, refusal)

    def with_markdown_newline(document: str, newline: str) -> str:
        if document.startswith("---\n"):
            frontmatter, separator, body = document.partition("\n---\n")
            if separator:
                return frontmatter + separator + body.replace("\n", newline)
        return document.replace("\n", newline)

    def with_frontmatter_newline(document: str, newline: str) -> str:
        frontmatter, closing, body = document.partition("\n---\n")
        if not closing:
            raise SystemExit("planning-hygiene self-test FAIL: fixture report has no closing frontmatter delimiter")
        normalized_frontmatter = frontmatter.replace("\n", newline)
        return f"{normalized_frontmatter}{newline}---{newline}{body}"

    def with_root_block_scalar(document: str, separator: str, apparent_value: str) -> str:
        frontmatter, closing, body = document.partition("\n---\n")
        if not closing:
            raise SystemExit("planning-hygiene self-test FAIL: fixture report has no closing frontmatter delimiter")
        scalar = f"line_boundary_note: |-\n  harmless{separator}{apparent_value}"
        return f"{frontmatter}\n{scalar}\n---\n{body}"

    def with_combined_block_scalars(document: str, separator: str,
                                    apparent_values: tuple[str, ...]) -> str:
        frontmatter, closing, body = document.partition("\n---\n")
        if not closing:
            raise SystemExit("planning-hygiene self-test FAIL: fixture report has no closing frontmatter delimiter")
        owner_field = "    original_owner: Phase 21\n"
        apparent_owner = (f"    note: |-\n      harmless{separator}"
                          "      original_owner: Phase 21\n")
        if owner_field not in frontmatter:
            raise SystemExit("planning-hygiene self-test FAIL: could not find the disposition owner fixture value")
        frontmatter = frontmatter.replace(owner_field, owner_field + apparent_owner, 1)
        scalars = []
        for index, value in enumerate(apparent_values):
            if value.endswith("\n"):
                value = value[:-1]
            scalars.append(f"line_boundary_note_{index}: |-\n  harmless{separator}{value}")
        scalar_fields = "\n".join(scalars)
        return f"{frontmatter}\n{scalar_fields}\n---\n{body}"

    def with_prefixed_root_scalar(document: str, separator: str, apparent_value: str) -> str:
        frontmatter, closing, body = document.partition("\n---\n")
        if not closing:
            raise SystemExit("planning-hygiene self-test FAIL: fixture report has no closing frontmatter delimiter")
        scalar_lines = apparent_value.rstrip("\n").split("\n")
        content = [f"    {separator}{scalar_lines[0]}"]
        content.extend(f"    {line}" for line in scalar_lines[1:])
        scalar = "line_boundary_note: |-\n" + "\n".join(content)
        return f"{frontmatter}\n{scalar}\n---\n{body}"

    def with_nested_scalar_field(document: str, separator: str, field: str, value: str) -> str:
        frontmatter, closing, body = document.partition("\n---\n")
        if not closing:
            raise SystemExit("planning-hygiene self-test FAIL: fixture report has no closing frontmatter delimiter")
        target = f"    {field}: {value}\n"
        apparent = f"    note: |-\n      {separator}{field}: {value}\n"
        if target not in frontmatter:
            raise SystemExit(f"planning-hygiene self-test FAIL: could not find disposition {field} fixture")
        frontmatter = frontmatter.replace(target, apparent, 1)
        return f"{frontmatter}\n---\n{body}"

    def with_scalar_boundary_twins(document: str, separator: str) -> str:
        frontmatter, closing, body = document.partition("\n---\n")
        if not closing:
            raise SystemExit("planning-hygiene self-test FAIL: fixture report has no closing frontmatter delimiter")
        apparent_values = [
            f"phase{separator}: GB-21-cgb-game-progress-and-scene-regressions",
            f"phase: GB-21-cgb-game-progress-and-scene-regressions{separator}",
            f"unresolved_gates:",
            "  - scalar-only gate",
            "requirements:",
            "  FIXT-01: satisfied",
            "requirement_dispositions:",
            "  - id: FIXT-01",
            "    status: Satisfied",
            "    original_owner: Phase 99",
        ]
        scalar_lines = [f"  {separator}{apparent_values[0]}"]
        scalar_lines.extend(f"  {line}" for line in apparent_values[1:])
        root_scalar = "line_boundary_note: |-\n" + "\n".join(scalar_lines)
        frontmatter = frontmatter.replace("unresolved_gates:\n", root_scalar + "\nunresolved_gates:\n", 1)
        nested = (f"    note: |-\n      {separator}status: Satisfied\n"
                  f"      {separator}original_owner: Phase 99\n")
        target = "    status: Pending\n"
        if target not in frontmatter:
            raise SystemExit("planning-hygiene self-test FAIL: could not find disposition status fixture")
        frontmatter = frontmatter.replace(target, target + nested, 1)
        return f"{frontmatter}\n---\n{body}"

    line_boundary_cases = (
        ("\u2028", "U+2028"),
        ("\u0085", "NEL"),
        ("\u2029", "U+2029"),
    )
    requirement_map = ("requirements:\n  FIXT-01: pending\n  RIGHTS-01: pending\n"
                       "  DIAG-01: pending\n  DIAG-02: pending\n")
    gate_sequence = f"unresolved_gates:\n{gates}\n"
    disposition_sequence = f"requirement_dispositions:\n{dispositions}\n"
    root_value_cases = (
        ("requirements map", requirement_map, "requirements:\n  FIXT-01: pending\n  RIGHTS-01: pending\n"
         "  DIAG-01: pending\n  DIAG-02: pending\n", "v04-report-requirements"),
        ("required scalar field", "phase: GB-22-composition-and-microtest-evidence\n",
         "phase: GB-22-composition-and-microtest-evidence", "v04-report-field"),
        ("unresolved-gates sequence", gate_sequence,
         "unresolved_gates:\n" + "\n".join(f"  - {gate}" for gate in V04_UNRESOLVED_GATES),
         "v04-report-gates"),
        ("requirement-dispositions objects", disposition_sequence,
         "requirement_dispositions:\n" + "\n".join(
             f"  - id: {requirement}\n    status: Pending\n    original_owner: {owner}"
             for requirement, owner in V04_PENDING_OWNERS.items()), "v04-report-requirements"),
    )
    for separator, separator_name in line_boundary_cases:
        for label, required_fragment, apparent_value, refusal in root_value_cases:
            missing_value = report_content.replace(required_fragment, "", 1)
            if missing_value == report_content:
                raise SystemExit(f"planning-hygiene self-test FAIL: could not remove required {label} fixture value")
            negative = with_root_block_scalar(missing_value, separator, apparent_value)
            negative_rev = commit({report_path: negative},
                                  f"hide missing {label} root value after {separator_name}")
            cli_check("report", negative_rev, refusal)

        disposition_member = "    original_owner: Phase 21\n"
        apparent_member = (f"    note: |-\n      harmless{separator}"
                           "      original_owner: Phase 21\n")
        missing_owner = report_content.replace(disposition_member, apparent_member, 1)
        if missing_owner == report_content:
            raise SystemExit("planning-hygiene self-test FAIL: could not remove disposition owner fixture value")
        missing_owner_rev = commit({report_path: missing_owner},
                                   f"hide missing disposition owner after {separator_name}")
        cli_check("report", missing_owner_rev, "v04-report-requirements")

    for (separator, separator_name), (newline, newline_name) in zip(
            line_boundary_cases, (("\n", "LF"), ("\r\n", "CRLF"), ("\r", "CR"))):
        positive = with_combined_block_scalars(
            report_content, separator, tuple(case[2] for case in root_value_cases))
        twin = with_frontmatter_newline(positive, newline)
        twin_rev = commit({report_path: twin},
                          f"accept combined {separator_name} scalar with {newline_name} frontmatter")
        cli_check("report", twin_rev)

    boundary_root_cases = (
        ("unresolved-gates sequence", gate_sequence,
         "unresolved_gates:\n" + "\n".join(f"  - {gate}" for gate in V04_UNRESOLVED_GATES),
         "v04-report-gates"),
        ("requirement-dispositions objects", disposition_sequence,
         "requirement_dispositions:\n" + "\n".join(
             f"  - id: {requirement}\n    status: Pending\n    original_owner: {owner}"
             for requirement, owner in V04_PENDING_OWNERS.items()),
         "v04-report-requirements"),
        ("requirements mapping", requirement_map, requirement_map, "v04-report-requirements"),
    )
    for separator, separator_name in line_boundary_cases:
        phase_field = "phase: GB-22-composition-and-microtest-evidence"
        malformed_key = report_content.replace(
            phase_field, f"phase{separator}: GB-22-composition-and-microtest-evidence", 1)
        malformed_key_rev = commit({report_path: malformed_key},
                                   f"reject {separator_name} in required phase key")
        cli_check("report", malformed_key_rev, "v04-report-field")

        malformed_value = report_content.replace(phase_field, phase_field + separator, 1)
        malformed_value_rev = commit({report_path: malformed_value},
                                     f"reject {separator_name} in required phase value")
        cli_check("report", malformed_value_rev, "v04-report-field")

        duplicate_alias = report_content.replace(
            phase_field, phase_field + f"\nphase{separator}: GB-21-cgb-game-progress-and-scene-regressions", 1)
        duplicate_alias_rev = commit({report_path: duplicate_alias},
                                     f"keep {separator_name} phase alias from overriding the canonical field")
        cli_check("report", duplicate_alias_rev)

        for field, original, refusal in (
                ("status", "Pending", "v04-report-requirements"),
                ("original_owner", "Phase 21", "v04-report-requirements")):
            target = f"    {field}: {original}\n"
            malformed = report_content.replace(target, f"    {field}: {original}{separator}\n", 1)
            malformed_rev = commit({report_path: malformed},
                                   f"reject {separator_name} in disposition {field} value")
            cli_check("report", malformed_rev, refusal)

        malformed_gate = report_content.replace(
            V04_UNRESOLVED_GATES[0], V04_UNRESOLVED_GATES[0] + separator, 1)
        malformed_gate_rev = commit({report_path: malformed_gate},
                                    f"reject {separator_name} in sequence value")
        cli_check("report", malformed_gate_rev, "v04-report-gates")

        malformed_requirement = report_content.replace(
            "  RIGHTS-01: pending", f"  RIGHTS-01: pending{separator}", 1)
        malformed_requirement_rev = commit({report_path: malformed_requirement},
                                            f"reject {separator_name} in requirement map value")
        cli_check("report", malformed_requirement_rev, "v04-report-requirements")

        for label, required_fragment, apparent_value, refusal in boundary_root_cases:
            missing_value = report_content.replace(required_fragment, "", 1)
            if missing_value == report_content:
                raise SystemExit(f"planning-hygiene self-test FAIL: could not remove required {label} fixture value")
            negative = with_prefixed_root_scalar(missing_value, separator, apparent_value)
            negative_rev = commit({report_path: negative},
                                  f"reject scalar {label} after {separator_name}")
            cli_check("report", negative_rev, refusal)

        for field, value in (("status", "Pending"), ("original_owner", "Phase 21")):
            negative = with_nested_scalar_field(report_content, separator, field, value)
            negative_rev = commit({report_path: negative},
                                  f"reject scalar disposition {field} after {separator_name}")
            cli_check("report", negative_rev, "v04-report-requirements")

        scalar_positive = with_scalar_boundary_twins(report_content, separator)
        scalar_positive_rev = commit({report_path: scalar_positive},
                                     f"preserve {separator_name} apparent schema inside scalar content")
        cli_check("report", scalar_positive_rev)

    for invalid_control in ("\v", "\f"):
        invalid_value = report_content.replace(
            "phase: GB-22-composition-and-microtest-evidence",
            "phase: GB-22-composition-and-microtest-evidence" + invalid_control, 1)
        invalid_value_rev = commit({report_path: invalid_value}, "refuse invalid YAML control in required scalar")
        cli_check("report", invalid_value_rev, "v04-report-field")

    cli_check("report", report_rev)
    matched_quote_requirements = report_content.replace(
        "  FIXT-01: pending\n  RIGHTS-01: pending\n  DIAG-01: pending\n  DIAG-02: pending",
        "  FIXT-01: 'pending'\n  RIGHTS-01: \"pending\"\n  DIAG-01: pending\n  DIAG-02: pending", 1)
    matched_quote_rev = commit({report_path: matched_quote_requirements}, "quote valid requirement scalars")
    cli_check("report", matched_quote_rev)

    comment_code_positive = report_content.replace(
        "This is a historical reconstruction",
        "<!-- hidden same-line comment --> This is a historical reconstruction", 1)
    comment_code_positive = comment_code_positive.replace(
        "The metadata-only assessment",
        "Literal `<!--` stays code; the matched span `first line\n<!-- stays literal\nlast line` spans lines.\n\n"
        "```text\n<!-- a fenced code marker is literal\n```\n\n    <!-- an indented code marker is literal\n\n"
        "<!-- hidden --> The metadata-only assessment", 1)
    comment_code_positive_rev = commit({report_path: comment_code_positive},
                                       "keep visible twins and code comment markers")
    cli_check("report", comment_code_positive_rev)

    comment_markers_inside_comment = report_content.replace(
        "This is a historical reconstruction",
        "<!--\n```text\n~~~\n-->\nThis is a historical reconstruction", 1)
    comment_markers_inside_comment_rev = commit(
        {report_path: comment_markers_inside_comment}, "ignore code markers within an active report comment")
    cli_check("report", comment_markers_inside_comment_rev)

    same_line_hidden_heading = report_content.replace(
        "## Historical reconstruction scope",
        "<!-- ## Historical reconstruction scope -->", 1)
    same_line_hidden_heading_rev = commit({report_path: same_line_hidden_heading},
                                          "hide report heading in a same-line comment")
    cli_check("report", same_line_hidden_heading_rev, "v04-report-heading")

    multiline_hidden_heading = report_content.replace(
        "## Historical reconstruction scope",
        "<!--\n## Historical reconstruction scope\n-->\n", 1)
    multiline_hidden_heading_rev = commit({report_path: multiline_hidden_heading},
                                          "hide report heading in a multiline comment")
    cli_check("report", multiline_hidden_heading_rev, "v04-report-heading")

    unclosed_hidden_heading = report_content.replace(
        "## Requirement truth and preserved limits",
        "<!--\n## Requirement truth and preserved limits", 1)
    unclosed_hidden_heading_rev = commit({report_path: unclosed_hidden_heading},
                                         "hide report heading with an unclosed comment")
    cli_check("report", unclosed_hidden_heading_rev, "v04-report-heading")

    hidden_scope_heading = report_content.replace(
        "## Historical reconstruction scope", "```text\n## Historical reconstruction scope\n```\n", 1)
    hidden_scope_heading_rev = commit({report_path: hidden_scope_heading},
                                      "hide historical report scope heading in code")
    cli_check("report", hidden_scope_heading_rev, "v04-report-heading")

    scope_start = report_content.index("## Historical reconstruction scope\n\n") + len("## Historical reconstruction scope\n\n")
    scope_end = report_content.index("\n\n## Goal Achievement", scope_start)
    scope_body = report_content[scope_start:scope_end]
    coded_scope_body = report_content[:scope_start] + "```text\n" + scope_body + "\n```" + report_content[scope_end:]
    coded_scope_body_rev = commit({report_path: coded_scope_body}, "hide report scope body in code")
    cli_check("report", coded_scope_body_rev, "v04-report-scope")

    commented_scope_body = (report_content[:scope_start] + "<!--\n" + scope_body + "\n-->"
                            + report_content[scope_end:])
    commented_scope_body_rev = commit({report_path: commented_scope_body}, "hide report scope body in a comment")
    cli_check("report", commented_scope_body_rev, "v04-report-scope")

    hidden_goal_heading = report_content.replace(
        "## Goal Achievement", "```text\n## Goal Achievement\n```\n", 1)
    hidden_goal_rev = commit({report_path: hidden_goal_heading}, "hide required report heading in backtick fence")
    cli_check("report", hidden_goal_rev, "v04-report-heading")

    tilde_hidden_no_go_heading = report_content.replace(
        "## Exact game no-go facts", "~~~text\n## Exact game no-go facts\n~~~\n", 1)
    tilde_hidden_no_go_rev = commit({report_path: tilde_hidden_no_go_heading},
                                   "hide required report heading in tilde fence")
    cli_check("report", tilde_hidden_no_go_rev, "v04-report-heading")

    goal_start = report_content.index("## Goal Achievement\n\n") + len("## Goal Achievement\n\n")
    goal_end = report_content.index("\n\n## Exact game no-go facts", goal_start)
    goal_body = report_content[goal_start:goal_end]
    coded_goal_body = report_content[:goal_start] + "~~~text\n" + goal_body + "\n~~~" + report_content[goal_end:]
    coded_goal_body_rev = commit({report_path: coded_goal_body}, "hide report criteria body in tilde fence")
    cli_check("report", coded_goal_body_rev, "v04-report-criteria")

    commented_goal_body = report_content[:goal_start] + "<!--\n" + goal_body + "\n-->" + report_content[goal_end:]
    commented_goal_body_rev = commit({report_path: commented_goal_body}, "hide report criteria table in a comment")
    cli_check("report", commented_goal_body_rev, "v04-report-criteria")

    no_go_start = report_content.index("## Exact game no-go facts\n\n") + len("## Exact game no-go facts\n\n")
    no_go_end = report_content.index("\n\n## Requirement truth and preserved limits", no_go_start)
    no_go_body = report_content[no_go_start:no_go_end]
    indented_no_go_body = "\n".join("    " + line if line else "    " for line in no_go_body.splitlines())
    coded_no_go_body = report_content[:no_go_start] + indented_no_go_body + report_content[no_go_end:]
    coded_no_go_body_rev = commit({report_path: coded_no_go_body}, "indent report no-go facts as code")
    cli_check("report", coded_no_go_body_rev, "v04-report-no-go")

    hidden_limits_heading = report_content.replace(
        "## Requirement truth and preserved limits",
        "~~~text\n## Requirement truth and preserved limits\n~~~\n", 1)
    hidden_limits_heading_rev = commit({report_path: hidden_limits_heading},
                                       "hide report limits heading in code")
    cli_check("report", hidden_limits_heading_rev, "v04-report-heading")

    limits_start = report_content.index("## Requirement truth and preserved limits\n\n") + len(
        "## Requirement truth and preserved limits\n\n")
    limits_body = report_content[limits_start:]
    coded_limits_body = report_content[:limits_start] + "~~~text\n" + limits_body + "\n~~~\n"
    coded_limits_body_rev = commit({report_path: coded_limits_body}, "hide report limits body in code")
    cli_check("report", coded_limits_body_rev, "v04-report-limits")

    hidden_report_boundary = report_content.replace(
        "## Exact game no-go facts\n\n",
        "## Exact game no-go facts\n\n```text\n## Requirement truth and preserved limits\n```\n\n", 1)
    hidden_report_boundary_rev = commit({report_path: hidden_report_boundary},
                                        "hide report heading duplicate and fake boundary")
    cli_check("report", hidden_report_boundary_rev)

    hidden_comment_boundary = report_content.replace(
        "## Exact game no-go facts\n\n",
        "## Exact game no-go facts\n\n<!--\n## Exact game no-go facts\n"
        "## Requirement truth and preserved limits\n-->\n\n", 1)
    hidden_comment_boundary_rev = commit({report_path: hidden_comment_boundary},
                                         "ignore hidden report duplicate and fake section boundary")
    cli_check("report", hidden_comment_boundary_rev)

    hidden_global_report_evidence = report_content.replace(
        "482 protocol candidates remain blocked",
        "<!-- 482 protocol candidates remain blocked -->")
    hidden_global_report_evidence_rev = commit({report_path: hidden_global_report_evidence},
                                               "hide report global evidence in comments")
    cli_check("report", hidden_global_report_evidence_rev, "v04-report-evidence")

    hidden_report_links = report_content.replace(
        "[22-EVIDENCE.md](22-EVIDENCE.md)", "<!-- [22-EVIDENCE.md](22-EVIDENCE.md) -->")
    hidden_report_links_rev = commit({report_path: hidden_report_links}, "hide required report links in comments")
    cli_check("report", hidden_report_links_rev, "v04-report-links")

    unclosed_report_comment = report_content.replace(
        "## Requirement truth and preserved limits", "<!-- unclosed report comment\n## Requirement truth and preserved limits", 1)
    unclosed_report_comment_rev = commit({report_path: unclosed_report_comment},
                                         "mask report content after an unclosed comment")
    cli_check("report", unclosed_report_comment_rev, "v04-report-heading")

    opposite_fence_close = report_content.replace(
        "## Goal Achievement\n\n",
        "## Goal Achievement\n\n```text\n~~~\n## Goal Achievement\n```  \n\n", 1)
    opposite_fence_close_rev = commit({report_path: opposite_fence_close},
                                      "keep opposite fence marker inside code")
    cli_check("report", opposite_fence_close_rev)

    shorter_fence_close = report_content.replace(
        "## Goal Achievement\n\n",
        "## Goal Achievement\n\n````text\n```\n## Goal Achievement\n````  \n\n", 1)
    shorter_fence_close_rev = commit({report_path: shorter_fence_close},
                                     "keep shorter fence marker inside code")
    cli_check("report", shorter_fence_close_rev)

    unclosed_goal_fence = report_content.replace("## Goal Achievement", "```text\n## Goal Achievement", 1)
    unclosed_goal_fence_rev = commit({report_path: unclosed_goal_fence}, "mask unclosed report fence to EOF")
    cli_check("report", unclosed_goal_fence_rev, "v04-report-heading")

    indented_no_go_heading = report_content.replace(
        "## Exact game no-go facts", "    ## Exact game no-go facts", 1)
    indented_no_go_heading_rev = commit({report_path: indented_no_go_heading},
                                       "hide required report heading in indented code")
    cli_check("report", indented_no_go_heading_rev, "v04-report-heading")

    closing_hash_positive = report_content.replace("## Goal Achievement", "## Goal Achievement ###", 1)
    closing_hash_positive_rev = commit({report_path: closing_hash_positive}, "retain visible ATX closing hashes")
    cli_check("report", closing_hash_positive_rev)

    first_disposition = "\n".join(dispositions.splitlines()[:3])
    unmatched_quote = report_content.replace("  RIGHTS-01: pending", "  RIGHTS-01: 'pending", 1)
    unmatched_quote_rev = commit({report_path: unmatched_quote}, "add unmatched requirement quote")
    cli_check("report", unmatched_quote_rev, "v04-report-requirements")
    wrong_parent_requirements = report_content.replace(
        "requirements:\n  FIXT-01: pending\n  RIGHTS-01: pending\n  DIAG-01: pending\n  DIAG-02: pending",
        "metadata:\n  requirements:\n  FIXT-01: pending\n  RIGHTS-01: pending\n  DIAG-01: pending\n  DIAG-02: pending", 1)
    wrong_parent_rev = commit({report_path: wrong_parent_requirements}, "nest requirements under metadata")
    cli_check("report", wrong_parent_rev, "v04-report-requirements")
    for label, mutated, error_code in (
        ("wrong phase", report_content.replace("phase: GB-22-composition-and-microtest-evidence",
                                                 "phase: GB-21-cgb-game-progress-and-scene-regressions", 1), "v04-report-field"),
        ("wrong status", report_content.replace("status: passed", "status: complete", 1), "v04-report-field"),
        ("boundary identity", report_content.replace(f"source_head: {V04_EVIDENCE_HEAD}", "source_head: " + "0" * 40), "v04-report-field"),
        ("metadata count", report_content.replace("metadata_cases: 513", "metadata_cases: 512"), "v04-report-field"),
        ("gate list", report_content.replace(V04_UNRESOLVED_GATES[-1], "wrong_final_gate"), "v04-report-gates"),
        ("nested requirement status", report_content.replace("  RIGHTS-01: pending", "  RIGHTS-01: satisfied", 1),
         "v04-report-requirements"),
        ("duplicate nested requirement ID", report_content.replace(
            "  RIGHTS-01: pending", "  RIGHTS-01: pending\n  RIGHTS-01: satisfied", 1), "v04-report-requirements"),
        ("missing nested requirement", report_content.replace("  DIAG-02: pending\n", "", 1),
         "v04-report-requirements"),
        ("extra nested requirement", report_content.replace(
            "requirements:\n", "requirements:\n  EXTRA-01: pending\n", 1), "v04-report-requirements"),
        ("missing root requirements map", report_content.replace(
            "requirements:\n  FIXT-01: pending\n  RIGHTS-01: pending\n  DIAG-01: pending\n  DIAG-02: pending\n", "", 1),
         "v04-report-requirements"),
        ("duplicate root requirements map", report_content.replace(
            "  DIAG-02: pending\nrequirement_dispositions:",
            "  DIAG-02: pending\nrequirements:\n  FIXT-01: pending\n  RIGHTS-01: pending\n  DIAG-01: pending\n  DIAG-02: pending\nrequirement_dispositions:", 1),
         "v04-report-frontmatter-duplicate"),
        ("whitespace alias replacing canonical root", report_content.replace(
            "requirements:\n", "requirements :\n", 1), "v04-report-requirements"),
        ("whitespace alias before canonical root", report_content.replace(
            "requirements:\n", "requirements :\n  FIXT-01: pending\n  RIGHTS-01: satisfied\n"
            "  DIAG-01: pending\n  DIAG-02: pending\nrequirements:\n", 1),
         "v04-report-requirements"),
        ("whitespace alias after canonical root", report_content.replace(
            "  DIAG-02: pending\nrequirement_dispositions:",
            "  DIAG-02: pending\nrequirements :\n  FIXT-01: pending\n  RIGHTS-01: satisfied\n"
            "  DIAG-01: pending\n  DIAG-02: pending\nrequirement_dispositions:", 1),
         "v04-report-requirements"),
        ("single-quoted root alias", report_content.replace(
            "  DIAG-02: pending\nrequirement_dispositions:",
            "  DIAG-02: pending\n'requirements' :\n  FIXT-01: pending\n  RIGHTS-01: satisfied\n"
            "  DIAG-01: pending\n  DIAG-02: pending\nrequirement_dispositions:", 1),
         "v04-report-requirements"),
        ("double-quoted escaped root alias", report_content.replace(
            "  DIAG-02: pending\nrequirement_dispositions:",
            '  DIAG-02: pending\n"requirem\\u0065nts":\n  FIXT-01: pending\n  RIGHTS-01: satisfied\n'
            "  DIAG-01: pending\n  DIAG-02: pending\nrequirement_dispositions:\n", 1),
         "v04-report-requirements"),
        ("tab before root alias colon", report_content.replace(
            "  DIAG-02: pending\nrequirement_dispositions:",
            "  DIAG-02: pending\nrequirements\t:\n  FIXT-01: pending\n  RIGHTS-01: satisfied\n"
            "  DIAG-01: pending\n  DIAG-02: pending\nrequirement_dispositions:", 1),
         "v04-report-requirements"),
        ("explicit-key root alias", report_content.replace(
            "  DIAG-02: pending\nrequirement_dispositions:",
            "  DIAG-02: pending\n? requirements\n: {FIXT-01: pending, RIGHTS-01: satisfied, "
            "DIAG-01: pending, DIAG-02: pending}\nrequirement_dispositions:", 1),
         "v04-report-requirements"),
        ("anchored root replacing canonical map", report_content.replace(
            "requirements:\n", "&req requirements:\n", 1), "v04-report-requirements"),
        ("tagged root replacing canonical map", report_content.replace(
            "requirements:\n", "!<tag:example.com,2026:requirements> requirements:\n", 1),
         "v04-report-requirements"),
        ("tag-then-anchor root replacing canonical map", report_content.replace(
            "requirements:\n", "!custom &req requirements:\n", 1), "v04-report-requirements"),
        ("anchor-then-tag root replacing canonical map", report_content.replace(
            "requirements:\n", "&req !custom requirements:\n", 1), "v04-report-requirements"),
        ("aliased root replacing canonical map", report_content.replace(
            "requirements:\n", "*requirements:\n", 1), "v04-report-requirements"),
        ("anchored contradictory root before canonical map", report_content.replace(
            "requirements:\n", "&req requirements:\n  FIXT-01: pending\n  RIGHTS-01: satisfied\n"
            "  DIAG-01: pending\n  DIAG-02: pending\nrequirements:\n", 1),
         "v04-report-requirements"),
        ("tagged contradictory root after canonical map", report_content.replace(
            "  DIAG-02: pending\nrequirement_dispositions:",
            "  DIAG-02: pending\n!custom requirements:\n  FIXT-01: pending\n  RIGHTS-01: satisfied\n"
            "  DIAG-01: pending\n  DIAG-02: pending\nrequirement_dispositions:", 1),
         "v04-report-requirements"),
        ("mismatched requirement quote", report_content.replace(
            "  RIGHTS-01: pending", "  RIGHTS-01: 'pending\"", 1), "v04-report-requirements"),
        ("malformed nested requirement", report_content.replace("  DIAG-02: pending", "    DIAG-02: pending", 1),
         "v04-report-requirements"),
        ("non-empty requirements satisfaction", report_content.replace(
            "requirements_satisfied: []", "requirements_satisfied: [FIXT-01]", 1), "v04-report-field"),
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
                                                              "## Exact game no-go facts ##\nDuplicate no-go heading.\n\n## Requirement truth and preserved limits", 1),
         "v04-report-heading"),
        ("Setext report duplicate", report_content.replace("## Requirement truth and preserved limits",
            "Exact game no-go facts\n---\nDuplicate no-go facts.\n\n## Requirement truth and preserved limits", 1),
         "v04-report-heading"),
        ("Setext report replacement", report_content.replace("## Exact game no-go facts",
            "Exact game no-go facts\n===", 1), "v04-report-heading"),
        ("multiline Setext report title", report_content.replace("## Goal Achievement",
            "Historical reconstruction\nscope\n===\n\n## Goal Achievement", 1), "v04-report-heading"),
    ):
        mutated_rev = commit({report_path: mutated}, f"mutate report {label}")
        cli_check("report", mutated_rev, error_code)

    decorated_roots = (
        "&req requirements:",
        "!<tag:example.com,2026:requirements> requirements:",
        "!custom &req requirements:",
        "&req !custom requirements:",
        "*requirements:",
    )
    canonical_root = "requirements:\n"
    contradictory_map = ("  FIXT-01: pending\n  RIGHTS-01: satisfied\n"
                         "  DIAG-01: pending\n  DIAG-02: pending\n")
    for decorated_root in decorated_roots:
        for position in ("before", "after"):
            if position == "before":
                mutated = report_content.replace(canonical_root,
                                                 decorated_root + "\n" + contradictory_map + canonical_root, 1)
            else:
                mutated = report_content.replace("  DIAG-02: pending\nrequirement_dispositions:",
                                                 "  DIAG-02: pending\n" + decorated_root + "\n"
                                                 + contradictory_map + "requirement_dispositions:", 1)
            mutated_rev = commit({report_path: mutated}, f"add decorated {position} requirements root")
            cli_check("report", mutated_rev, "v04-report-requirements")
            git("checkout", "-q", report_rev)

    markdown_separators = ("\u2028", "\u2029", "\v", "\f")
    for separator in markdown_separators:
        fake_heading = report_content.replace(
            "## Goal Achievement\n", f"prose{separator}## Goal Achievement\n", 1)
        fake_heading_rev = commit({report_path: fake_heading}, "inject a report heading through a Unicode separator")
        cli_check("report", fake_heading_rev, "v04-report-heading")
        git("checkout", "-q", report_rev)

        malformed_delimiter = report_content.replace(
            "## Goal Achievement\n", f"##{separator}Goal Achievement\n", 1)
        malformed_delimiter_rev = commit({report_path: malformed_delimiter},
                                         "use a non-horizontal report ATX delimiter")
        cli_check("report", malformed_delimiter_rev, "v04-report-heading")
        git("checkout", "-q", report_rev)

        criterion_two = next(line for line in report_content.split("\n") if line.startswith("| 2."))
        fake_criterion = report_content.replace(criterion_two,
                                               f"prose{separator}{criterion_two}", 1)
        fake_criterion_rev = commit({report_path: fake_criterion},
                                    "inject a criterion row through a Unicode separator")
        cli_check("report", fake_criterion_rev, "v04-report-criteria")
        git("checkout", "-q", report_rev)

        malformed_requirements = requirements.replace(
            "| FIXT-01 | Phase 21 | Pending |\n| RIGHTS-01 | Phase 20 | Pending |",
            "| FIXT-01 | Phase 21 | Pending |" + separator + "| RIGHTS-01 | Phase 20 | Pending |", 1)
        git("checkout", "-q", baseline_rev)
        malformed_baseline_rev = commit({".planning/REQUIREMENTS.md": malformed_requirements},
                                        "join requirement rows with a non-CommonMark separator")
        malformed_report_rev = commit({report_path: report_content},
                                      "add report over malformed traceability rows", stage_new=True)
        cli_check("report", malformed_report_rev, "v04-report-requirements", malformed_baseline_rev)
        git("checkout", "-q", report_rev)

    for newline_label, newline in (("CRLF", "\r\n"), ("CR", "\r")):
        newline_report_rev = commit({report_path: with_markdown_newline(report_content, newline)},
                                    f"preserve report with {newline_label} Markdown lines")
        cli_check("report", newline_report_rev)
        git("checkout", "-q", report_rev)

    tab_heading = report_content.replace("## Goal Achievement\n", "##\tGoal Achievement\t##\t\n", 1)
    tab_heading_rev = commit({report_path: tab_heading}, "accept horizontal tab ATX delimiters")
    cli_check("report", tab_heading_rev)
    git("checkout", "-q", report_rev)

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
    handoff_rev = commit(handoff_files, "reconcile current handoff", stage_new=True)
    cli_check("handoff", handoff_rev)
    handoff_documents = (
        ("STATE", state_path, state_handoff, "Owner Handoff"),
        ("PROJECT", project_path, project_state, "Current State"),
        ("continuation", continuation_path, continuation, "Owner Handoff"),
    )
    for separator in markdown_separators:
        for label, path, document, title in handoff_documents:
            heading = f"## {title}\n"
            fake_heading = document.replace(heading, f"handoff prose{separator}{heading}", 1)
            fake_heading_rev = commit({path: fake_heading},
                                     f"inject a {label} heading through a Unicode separator")
            cli_check("handoff", fake_heading_rev, "v04-handoff-heading")
            git("checkout", "-q", handoff_rev)

            malformed_delimiter = document.replace(heading, f"##{separator}{title}\n", 1)
            malformed_delimiter_rev = commit({path: malformed_delimiter},
                                             f"use a non-horizontal {label} ATX delimiter")
            cli_check("handoff", malformed_delimiter_rev, "v04-handoff-heading")
            git("checkout", "-q", handoff_rev)

        owner_line = "- FIXT-01 — Pending, original owner Phase 21."
        fake_owner = state_handoff.replace(owner_line, f"owner prose{separator}{owner_line}", 1)
        fake_owner_rev = commit({state_path: fake_owner}, "inject a STATE owner row through a Unicode separator")
        cli_check("handoff", fake_owner_rev, "v04-handoff-owner")
        git("checkout", "-q", handoff_rev)

    for label, path, document, title in handoff_documents:
        tab_document = document.replace(f"## {title}\n", f"##\t{title}\t##\t\n", 1)
        tab_rev = commit({path: tab_document}, f"accept horizontal tab ATX delimiters in {label}")
        cli_check("handoff", tab_rev)
        git("checkout", "-q", handoff_rev)

        for newline_label, newline in (("CRLF", "\r\n"), ("CR", "\r")):
            newline_document_rev = commit({path: with_markdown_newline(document, newline)},
                                          f"preserve {label} with {newline_label} Markdown lines")
            cli_check("handoff", newline_document_rev)
            git("checkout", "-q", handoff_rev)

    state_hidden_heading = state_handoff.replace(
        "## Owner Handoff\n", "```text\n## Owner Handoff\n```\n\n", 1)
    state_hidden_heading_rev = commit({state_path: state_hidden_heading}, "hide STATE handoff heading in code")
    cli_check("handoff", state_hidden_heading_rev, "v04-handoff-heading")
    git("checkout", "-q", handoff_rev)
    project_hidden_heading = project_state.replace(
        "## Current State\n", "~~~text\n## Current State\n~~~\n\n", 1)
    project_hidden_heading_rev = commit({project_path: project_hidden_heading}, "hide PROJECT state heading in code")
    cli_check("handoff", project_hidden_heading_rev, "v04-handoff-heading")
    git("checkout", "-q", handoff_rev)
    continuation_hidden_heading = continuation.replace(
        "## Owner Handoff\n", "~~~text\n## Owner Handoff\n~~~\n\n", 1)
    continuation_hidden_heading_rev = commit(
        {continuation_path: continuation_hidden_heading}, "hide continuation handoff heading in code")
    cli_check("handoff", continuation_hidden_heading_rev, "v04-handoff-heading")

    git("checkout", "-q", handoff_rev)
    handoff_comment_cases = (
        ("STATE", state_path, state_handoff, "Owner Handoff", phase22_link_state,
         "The v0.4 remains open.", "v04-handoff-open", "v04-handoff-stale"),
        ("PROJECT", project_path, project_state, "Current State", phase22_link_project,
         "The v0.4 remains open.", "v04-handoff-open", "v04-handoff-pending"),
        ("continuation", continuation_path, continuation, "Owner Handoff", phase22_link_continuation,
         "No next phase or milestone is selected or started.", "v04-handoff-phase", "v04-handoff-pending"),
    )
    for label, path, document, title, link_path, global_fact, global_error, body_error in handoff_comment_cases:
        heading_line = f"## {title}\n"
        positive_comment = document.replace(heading_line,
                                            f"## {title} <!-- visible heading after comment close -->\n", 1)
        positive_rev = commit({path: positive_comment}, f"keep {label} visible with trailing comment")
        cli_check("handoff", positive_rev)
        git("checkout", "-q", handoff_rev)

        same_line_heading = document.replace(heading_line, f"<!-- ## {title} -->\n", 1)
        same_line_heading_rev = commit({path: same_line_heading}, f"hide {label} heading on one line")
        cli_check("handoff", same_line_heading_rev, "v04-handoff-heading")
        git("checkout", "-q", handoff_rev)

        multiline_heading = document.replace(heading_line, f"<!--\n## {title}\n-->\n", 1)
        multiline_heading_rev = commit({path: multiline_heading}, f"hide {label} heading across lines")
        cli_check("handoff", multiline_heading_rev, "v04-handoff-heading")
        git("checkout", "-q", handoff_rev)

        hidden_body = document.replace(f"## {title}\n\n", f"## {title}\n\n<!--\n", 1) + "\n-->\n"
        hidden_body_rev = commit({path: hidden_body}, f"hide {label} handoff body in a comment")
        cli_check("handoff", hidden_body_rev, body_error)
        git("checkout", "-q", handoff_rev)

        hidden_global = document.replace(global_fact, f"<!-- {global_fact} -->", 1)
        hidden_global_rev = commit({path: hidden_global}, f"hide {label} global fact in a comment")
        cli_check("handoff", hidden_global_rev, global_error)
        git("checkout", "-q", handoff_rev)

        link = f"[22-VERIFICATION.md]({link_path})"
        hidden_link = document.replace(link, f"<!-- {link} -->", 1)
        hidden_link_rev = commit({path: hidden_link}, f"hide {label} report link in a comment")
        cli_check("handoff", hidden_link_rev, "v04-handoff-link")
        git("checkout", "-q", handoff_rev)

    unclosed_continuation = continuation.replace(
        "## Owner Handoff", "<!-- unclosed continuation comment\n## Owner Handoff", 1)
    unclosed_continuation_rev = commit({continuation_path: unclosed_continuation},
                                      "mask continuation heading after unclosed comment")
    cli_check("handoff", unclosed_continuation_rev, "v04-handoff-heading")

    git("checkout", "-q", handoff_rev)
    state_coded_body = state_handoff.replace("## Owner Handoff\n\n", "## Owner Handoff\n\n```text\n", 1) + "\n```\n"
    state_coded_body_rev = commit({state_path: state_coded_body}, "hide STATE handoff body in code")
    cli_check("handoff", state_coded_body_rev, "v04-handoff-stale")
    git("checkout", "-q", handoff_rev)
    project_coded_body = project_state.replace("## Current State\n\n", "## Current State\n\n~~~text\n", 1) + "\n~~~\n"
    project_coded_body_rev = commit({project_path: project_coded_body}, "hide PROJECT state body in code")
    cli_check("handoff", project_coded_body_rev, "v04-handoff-pending")
    git("checkout", "-q", handoff_rev)
    continuation_coded_body = continuation.replace(
        "## Owner Handoff\n\n", "## Owner Handoff\n\n```text\n", 1) + "\n```\n"
    continuation_coded_body_rev = commit({continuation_path: continuation_coded_body},
                                         "hide continuation handoff body in code")
    cli_check("handoff", continuation_coded_body_rev, "v04-handoff-pending")

    git("checkout", "-q", handoff_rev)
    for label, path, document, title in (
            ("STATE", state_path, state_handoff, "Owner Handoff"),
            ("PROJECT", project_path, project_state, "Current State"),
            ("continuation", continuation_path, continuation, "Owner Handoff")):
        hidden_duplicate_boundary = document.replace(
            f"## {title}\n\n", f"## {title}\n\n```text\n## {title}\n## Fake section boundary\n```\n\n", 1)
        hidden_duplicate_rev = commit({path: hidden_duplicate_boundary},
                                      f"hide {label} heading duplicate and fake boundary")
        cli_check("handoff", hidden_duplicate_rev)
        git("checkout", "-q", handoff_rev)

    setext_state_rev = commit({state_path: state_handoff + "\n   Owner Handoff\n   ---\nDuplicate state handoff.\n"},
                              "add Setext STATE handoff duplicate")
    cli_check("handoff", setext_state_rev, "v04-handoff-heading")
    git("checkout", "-q", handoff_rev)
    setext_project_rev = commit({project_path: project_state + "\nCurrent State\n===\nDuplicate project state.\n"},
                                "add Setext PROJECT heading duplicate")
    cli_check("handoff", setext_project_rev, "v04-handoff-heading")
    git("checkout", "-q", handoff_rev)
    setext_continuation_rev = commit({continuation_path: continuation + "\nOwner\nHandoff\n---\nDuplicate continuation handoff.\n"},
                                     "add multiline Setext continuation duplicate")
    cli_check("handoff", setext_continuation_rev, "v04-handoff-heading")
    git("checkout", "-q", handoff_rev)
    code_and_break_positive = state_handoff + (
        "\n```text\nOwner Handoff\n---\n```\n\n"
        "    Current State\n    ===\n\n"
        "Unrelated descriptive text\n---\n"
    )
    code_positive_rev = commit({state_path: code_and_break_positive}, "keep code and thematic-break twins valid")
    cli_check("handoff", code_positive_rev)
    git("checkout", "-q", handoff_rev)
    missing_link_rev = commit({state_path: state_handoff.replace(f"]({phase22_link_state})", "](#missing-report)")},
                              "remove current report link")
    cli_check("handoff", missing_link_rev, "v04-handoff-link")
    git("checkout", "-q", handoff_rev)
    duplicate_handoff_rev = commit({state_path: state_handoff + "\n## Owner Handoff ##\n\nDuplicate heading.\n"},
                                   "duplicate current owner handoff")
    cli_check("handoff", duplicate_handoff_rev, "v04-handoff-heading")
    git("checkout", "-q", handoff_rev)
    duplicate_phase_state = state_handoff.replace('current_phase: "23.1"',
                                                  'current_phase: "23.1"\ncurrent_phase: "22"', 1)
    duplicate_phase_rev = commit({state_path: duplicate_phase_state}, "duplicate current phase frontmatter")
    cli_check("handoff", duplicate_phase_rev, "v04-handoff-frontmatter-duplicate")
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
    parser.add_argument("--check", choices=("plan-cap", "lessons-ids", "state-size", "playstead-docs", "deferrals",
                                              "v04-reconciliation", "v04-gap-assessment"))
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--roadmap")
    parser.add_argument("--phases-dir")
    parser.add_argument("--rev", help="a full immutable commit id to read")
    parser.add_argument("--stage", choices=("report", "handoff"), help="immutable assessment stage to check")
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
                roadmap_text_at_rev, tree, decisions = read_rev(Path(args.repo), args.rev)
                summary, errors = check_plan_tree(roadmap_text_at_rev, tree, args.rev, decisions)
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
        elif args.check == "v04-gap-assessment":
            if not args.stage or not args.rev or not args.baseline_rev:
                parser.error("v04-gap-assessment needs --stage report|handoff --rev COMMIT --baseline-rev COMMIT")
            summary, errors = check_v04_gap_assessment(Path(args.repo), args.stage, args.rev, args.baseline_rev)
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
