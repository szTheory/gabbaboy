#!/usr/bin/env python3
"""Compose Phase 21's source-qualified CGB harness, candidate, and scene evidence."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_CHILD_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_RUNNER_BYTES = 128 * 1024 * 1024
GIT_TIMEOUT_SECONDS = 20
CHECK_TIMEOUT_SECONDS = 90
FULL_COMMIT = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_HARNESS_ROM_SHA256 = "17822873ec8641280d9504229d96850414e872bc90de5431469a498e5271db7e"
EXPECTED_HARNESS_INPUT_SHA256 = "0ccfce12e082a0d6bf52ee6a0867b62beb096f5b9403d715e0c5b354c3b14fc2"
UCITY_13_REVISION = "d1880a2a112d7c26f16c0fc06a15b6c32fdc9137"
UCITY_HARDWARE_SHA256 = "05f43643bf29459f6a86b2fedf00b887133b98038fa4f51112ced0f01a762715"
EVIDENCE_OUTPUT_ROOT = "build/phase21-evidence"

CANDIDATES = (
    ("potion-panic-gbcompo25", "tests/data/cgb-candidates/potion-panic.json", "Potion Panic"),
    ("ucity-1.3", "tests/data/cgb-candidates/ucity-1.3.json", "µCity 1.3"),
)
PHASE21_DIR = chr(46) + "planning" + chr(47) + "phases" + chr(47) + "GB-21-cgb-game-progress-and-scene-regressions"
SOURCE_PATHS = (
    "tests/scripts/verify-cgb-game-evidence.py",
    "tests/scripts/verify-cgb-progress.py",
    "tests/scripts/verify-cgb-candidates.py",
    "tests/scripts/verify-scene-report.py",
    "tests/scripts/host_fixture.py",
    "tests/cmake/game-evidence.cmake",
    "tests/CMakeLists.txt",
    "docs/game-acceptance.md",
    "docs/cgb-profile.md",
    "docs/support/unreleased.md",
    "docs/scene-feedback.md",
    f"{PHASE21_DIR}/21-06-SUMMARY.md",
    *(candidate[1] for candidate in CANDIDATES),
)
FALSE_CLAIM_PATTERNS = (
    re.compile(r"\b(?:prove|proves|proved|establish|establishes|qualify|qualifies)\s+(?:(?:real[- ]game|game)\s+)?progress\b", re.I),
    re.compile(r"\b(?:prove|proves|proved|establish|establishes|qualify|qualifies)\s+(?:(?:rendering|game)\s+)?accuracy\b", re.I),
    re.compile(r"\b(?:physical|real)\s+cgb(?:[- ]?(?:cpu[- ]?)?e)?\s+(?:hardware\s+)?(?:is|was)\s+(?:qualified|verified|proven|passed)\b", re.I),
    re.compile(r"\b(?:general|broad)\s+game\s+compatibility\s+(?:is|was)\s+(?:qualified|proven|established)\b", re.I),
    re.compile(r"\bmode[- ]3\s+timing\s+(?:is|was)\s+(?:qualified|proven|established)\b", re.I),
    re.compile(r"\bperceptual\s+(?:audio|video|colour|color)?\s*quality\s+(?:is|was)\s+(?:qualified|proven|established)\b", re.I),
)
LICENSE_NAME_PATTERN = (
    r"(?:cc[\s-]*by(?:[\s-]*nc)?[\s-]*sa(?:[\s-]*4\.0)?"
    r"|creative\s+commons\s+attribution-noncommercial-sharealike\s+4\.0\s+international"
    r"|mit(?:\s+license)?|bsd(?:[\s-]*2[\s-]*clause)?"
    r"|gpl[\s-]*(?:v[\s-]*)?3(?:\.0)?(?:[\s-]*(?:only|or[\s-]*later|\+))?)"
)
PROHIBITION_VERB_PATTERN = r"(?:prohibit(?:s|ed)?|forbid(?:s|den)?|ban(?:s|ned)?)"
LEGAL_LICENSE_PATTERN = re.compile(rf"\b{LICENSE_NAME_PATTERN}\b", re.I)
LEGAL_PROHIBITION_VERB_PATTERN = re.compile(
    rf"\b(?:categorically\s+)?{PROHIBITION_VERB_PATTERN}\b", re.I)
LEGAL_ILLEGAL_USE_PATTERN = re.compile(
    r"\b(?:use|repository use|public-ci use)\s+(?:is|was)\s+illegal\b", re.I)
LEGAL_SENTENCE_BOUNDARY_PATTERN = re.compile(r"[.!?](?=\s|$)|\n")


class Reject(Exception):
    """A bounded, stable rejection for malformed or unsupported evidence."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail[:512]

    def __str__(self) -> str:
        return f"{self.code}{': ' + self.detail if self.detail else ''}"


def run_bounded(argv: list[str], cwd: Path, *, timeout: int = CHECK_TIMEOUT_SECONDS) -> subprocess.CompletedProcess[bytes]:
    try:
        result = subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as error:
        raise Reject("subprocess-timeout", Path(argv[0]).name) from error
    except OSError as error:
        raise Reject("subprocess-unavailable", f"{Path(argv[0]).name}: {error.strerror}") from error
    if len(result.stdout) > MAX_CHILD_OUTPUT_BYTES or len(result.stderr) > MAX_CHILD_OUTPUT_BYTES:
        raise Reject("subprocess-output-limit", Path(argv[0]).name)
    return result


def git_output(root: Path, *args: str, timeout: int = GIT_TIMEOUT_SECONDS) -> bytes:
    env = dict(os.environ)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    env["GIT_PAGER"] = "cat"
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        result = subprocess.run(["git", "-C", str(root), *args], stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
                                env=env, check=False)
    except subprocess.TimeoutExpired as error:
        raise Reject("git-timeout", args[0] if args else "git") from error
    except OSError as error:
        raise Reject("git-unavailable", error.strerror or "git") from error
    if len(result.stdout) > MAX_SOURCE_BYTES or len(result.stderr) > 4096:
        raise Reject("git-output-limit", args[0] if args else "git")
    if result.returncode != 0:
        raise Reject("git-read-failed", args[0] if args else "git")
    return result.stdout


def resolve_source_revision(root: Path, requested: str) -> str:
    if not FULL_COMMIT.fullmatch(requested):
        raise Reject("source-revision-must-be-full-commit")
    resolved = git_output(root, "rev-parse", "--verify", f"{requested}^{{commit}}").decode("ascii", errors="strict").strip()
    if resolved != requested:
        raise Reject("source-revision-mismatch")
    return resolved


def immutable_blob(root: Path, revision: str, relative: str) -> bytes:
    size_raw = git_output(root, "cat-file", "-s", f"{revision}:{relative}").decode("ascii", errors="strict").strip()
    if not size_raw.isdecimal() or int(size_raw) > MAX_SOURCE_BYTES:
        raise Reject("source-file-size-invalid", relative)
    return git_output(root, "show", f"{revision}:{relative}")


def load_snapshot(root: Path, revision: str) -> dict[str, bytes]:
    snapshot: dict[str, bytes] = {}
    for relative in SOURCE_PATHS:
        path = root / relative
        if path.is_symlink():
            raise Reject("source-path-is-symlink", relative)
        try:
            current = path.read_bytes()
        except OSError as error:
            raise Reject("source-file-unavailable", relative) from error
        pinned = immutable_blob(root, revision, relative)
        if current != pinned:
            raise Reject("working-tree-source-mismatch", relative)
        snapshot[relative] = pinned

    listing = git_output(root, "ls-tree", "-r", "--name-only", revision, "--",
                         "tests/data/cgb-candidates").decode("utf-8", errors="strict").splitlines()
    candidate_json = {path for path in listing if path.startswith("tests/data/cgb-candidates/")
                      and path.endswith(".json")}
    expected_json = {candidate[1] for candidate in CANDIDATES}
    if candidate_json != expected_json:
        raise Reject("candidate-record-set-invalid")
    return snapshot


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Reject("json-duplicate-key", key)
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise Reject("json-nonfinite-number", value)


def parse_record(raw: bytes, where: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_pairs,
                           parse_constant=_reject_json_constant)
    except Reject:
        raise
    except (UnicodeError, json.JSONDecodeError) as error:
        raise Reject("candidate-record-invalid", where) from error
    if not isinstance(value, dict):
        raise Reject("candidate-record-invalid", where)
    return value


def _disposition(record: dict[str, Any]) -> tuple[str, str, str, str]:
    value = record.get("disposition")
    if not isinstance(value, dict):
        raise Reject("candidate-disposition-invalid")
    status = value.get("status")
    category = value.get("category", "")
    stage = value.get("blocker_stage", "")
    reason = value.get("reason", "")
    if not all(isinstance(item, str) for item in (status, category, stage, reason)):
        raise Reject("candidate-disposition-invalid")
    if len(reason) > 2048:
        raise Reject("candidate-reason-limit")
    return status, category, stage, reason


def candidate_outcome(records: list[dict[str, Any]]) -> dict[str, str]:
    """Accept only the ordered terminal primary/fallback outcomes from Phase 21."""
    if len(records) != 2:
        raise Reject("candidate-attempt-set")
    identities = [record.get("candidate_id") for record in records]
    if identities != [candidate[0] for candidate in CANDIDATES]:
        raise Reject("candidate-order-or-identity-invalid")
    first_status, _, _, first_reason = _disposition(records[0])
    second_status, _, _, second_reason = _disposition(records[1])
    statuses = (first_status, second_status)
    if "blocked-defect" in statuses:
        raise Reject("candidate-blocked-defect")
    if first_status == "admitted" and second_status == "not-needed":
        return {"status": "admitted", "candidate_id": "potion-panic-gbcompo25"}
    if first_status == "no-go" and second_status == "admitted":
        if not first_reason.strip():
            raise Reject("primary-no-go-cause-missing")
        return {"status": "admitted", "candidate_id": "ucity-1.3"}
    if first_status == "no-go" and second_status == "no-go":
        if not first_reason.strip() or not second_reason.strip():
            raise Reject("candidate-no-go-cause-missing")
        return {"status": "no-game", "candidate_id": "none"}
    raise Reject("candidate-outcome-not-terminal")


def _nested(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def validate_no_go_record(record: dict[str, Any], expected_id: str) -> None:
    status, category, stage, reason = _disposition(record)
    if status != "no-go" or category != "rights" or not reason.strip():
        raise Reject("candidate-no-go-cause-invalid", expected_id)
    admission = _nested(record, "admission", "value")
    if not isinstance(admission, dict) or admission.get("decision_status") != "no-go":
        raise Reject("candidate-rights-decision-invalid", expected_id)
    evidence = admission.get("evidence")
    if not isinstance(evidence, dict):
        raise Reject("candidate-rights-evidence-invalid", expected_id)
    for field in ("build", "rom", "execution", "progress", "observations", "receipt"):
        if _nested(record, field, "state") != "not_observed":
            raise Reject("candidate-downstream-state-inflated", f"{expected_id}:{field}")
        if _nested(record, field, "blocked_by") != "rights":
            raise Reject("candidate-cutoff-stage-mismatch", f"{expected_id}:{field}")
    if expected_id == "potion-panic-gbcompo25":
        source = _nested(record, "source")
        if not isinstance(source, dict) or source.get("state") != "not_observed" or source.get("blocked_by") != "rights":
            raise Reject("primary-source-cutoff-invalid")
        disposition_evidence = _nested(record, "disposition", "evidence")
        if not isinstance(disposition_evidence, dict) or disposition_evidence.get("kind") != "creator-linked-source-and-rights-cutoff":
            raise Reject("primary-rights-cause-invalid")
        if disposition_evidence.get("upstream_scripts_executed") is not False or disposition_evidence.get("candidate_rom_acquired_or_executed") is not False:
            raise Reject("primary-execution-fact-inflated")
        if disposition_evidence.get("source_repository") != "https://codeberg.org/DevEd/potion-panic":
            raise Reject("primary-source-authority-mismatch")
        admission_evidence = admission.get("evidence", {})
        if admission_evidence.get("creator_page") != "https://deved.itch.io/potion-panic":
            raise Reject("primary-creator-evidence-mismatch")
    elif expected_id == "ucity-1.3":
        source = _nested(record, "source", "value")
        if not isinstance(source, dict) or source.get("revision") != UCITY_13_REVISION:
            raise Reject("fallback-source-revision-mismatch")
        unresolved = _nested(admission, "evidence", "component_grants", "unresolved_build_component")
        if not isinstance(unresolved, dict) or unresolved.get("path") != "source/engine/hardware.inc" or unresolved.get("sha256") != UCITY_HARDWARE_SHA256:
            raise Reject("fallback-rights-component-mismatch")
        if unresolved.get("rights_scope") != "Grantor authority and repository/public-CI redistribution scope for this required component are unestablished.":
            raise Reject("fallback-rights-scope-mismatch")
        if _nested(record, "build", "state") != "not_observed":
            raise Reject("fallback-build-fact-inflated")
        if _nested(record, "disposition", "evidence", "upstream_execution") is not False:
            raise Reject("fallback-upstream-execution-inflated")
    else:
        raise Reject("candidate-identity-invalid")
    combined = reason + " " + str(admission.get("reason", ""))
    if _has_unqualified_license_prohibition(combined):
        raise Reject("candidate-rights-conclusion-overstated", expected_id)


def parse_snapshot_records(snapshot: dict[str, bytes]) -> list[dict[str, Any]]:
    records = [parse_record(snapshot[path], candidate_id) for candidate_id, path, _ in CANDIDATES]
    for (candidate_id, _, _), record in zip(CANDIDATES, records):
        if record.get("candidate_id") != candidate_id:
            raise Reject("candidate-identity-mismatch", candidate_id)
    outcome = candidate_outcome(records)
    if outcome["status"] == "no-game":
        for candidate_id, record in zip((candidate[0] for candidate in CANDIDATES), records):
            validate_no_go_record(record, candidate_id)
    return records


def _decode_doc(snapshot: dict[str, bytes], relative: str) -> str:
    try:
        return snapshot[relative].decode("utf-8", errors="strict")
    except (KeyError, UnicodeError) as error:
        raise Reject("documentation-source-invalid", relative) from error


def _require_markers(text: str, markers: tuple[str, ...], label: str) -> None:
    folded = re.sub(r"\s+", " ", text.casefold())
    for marker in markers:
        if re.sub(r"\s+", " ", marker.casefold()) not in folded:
            raise Reject("documentation-contract-missing", f"{label}:{marker}")


def _reject_markers(text: str, markers: tuple[str, ...], label: str) -> None:
    folded = re.sub(r"\s+", " ", text.casefold())
    for marker in markers:
        if re.sub(r"\s+", " ", marker.casefold()) in folded:
            raise Reject("documentation-outcome-contradiction", f"{label}:{marker}")


def _has_unqualified_license_prohibition(text: str) -> bool:
    if LEGAL_ILLEGAL_USE_PATTERN.search(text):
        return True

    contrast_boundary_pattern = re.compile(r"\b(?:but|however|yet|nevertheless)\b", re.I)
    for verb in LEGAL_PROHIBITION_VERB_PATTERN.finditer(text):
        sentence_start = max(
            (boundary.end() for boundary in LEGAL_SENTENCE_BOUNDARY_PATTERN.finditer(
                text, 0, verb.start())),
            default=0,
        )
        sentence_end = min(
            (boundary.start() for boundary in LEGAL_SENTENCE_BOUNDARY_PATTERN.finditer(
                text, verb.end())),
            default=len(text),
        )
        sentence = text[sentence_start:sentence_end]
        verb_start = verb.start() - sentence_start
        verb_end = verb.end() - sentence_start
        verb_prefix = sentence[max(0, verb_start - 64):verb_start]
        directly_negated = re.search(
            r"\b(?:does|do|did|is|are|was|were|will|would|can|could|should|might|may|must)"
            r"\s+not(?:\s+categorically)?\s*$|\bnever(?:\s+categorically)?\s*$",
            verb_prefix, re.I)

        for license_match in LEGAL_LICENSE_PATTERN.finditer(sentence):
            if license_match.end() <= verb_start:
                gap = verb_start - license_match.end()
            elif verb_end <= license_match.start():
                gap = license_match.start() - verb_end
            else:
                continue
            if gap > 80:
                continue

            claim_prefix = sentence[:min(license_match.start(), verb_start)]
            clause_boundaries = [
                claim_prefix.rfind(";") + 1,
                claim_prefix.rfind(":") + 1,
                *(match.end() for match in contrast_boundary_pattern.finditer(claim_prefix)),
            ]
            clause_prefix = claim_prefix[max(clause_boundaries, default=0):]
            negated_conclusion = re.search(
                r"\bnot\s+(?:a\s+)?conclusion\s+that\b", clause_prefix, re.I)
            if directly_negated is None and negated_conclusion is None:
                return True
    return False


def validate_scene_privacy(text: str) -> None:
    _require_markers(text, (
        "owner play is optional",
        "never a recurring prerequisite",
        "personal roms, battery saves, save states, screenshots, videos, and audio remain outside git and hosted ci",
        "never place them in the repository or public ci",
        "a digest or screenshot captured from gabbaboy's failing output cannot become its own oracle",
    ), "scene-privacy")


def reject_claim_inflation(documents: dict[str, str]) -> None:
    for path, text in documents.items():
        for pattern in FALSE_CLAIM_PATTERNS:
            if pattern.search(text):
                raise Reject("documentation-claim-inflation", path)
        if _has_unqualified_license_prohibition(text):
            raise Reject("documentation-rights-conclusion-overstated", path)


def validate_documentation(snapshot: dict[str, bytes], records: list[dict[str, Any]]) -> dict[str, str]:
    game = _decode_doc(snapshot, "docs/game-acceptance.md")
    profile = _decode_doc(snapshot, "docs/cgb-profile.md")
    support = _decode_doc(snapshot, "docs/support/unreleased.md")
    scene = _decode_doc(snapshot, "docs/scene-feedback.md")
    outcome = candidate_outcome(records)
    documents = {
        "docs/game-acceptance.md": game,
        "docs/cgb-profile.md": profile,
        "docs/support/unreleased.md": support,
    }
    reject_claim_inflation(documents)
    validate_scene_privacy(scene)

    _require_markers(game, (
        "## CGB game evidence",
        "Phase 21 outcome",
        "Potion Panic",
        "µCity 1.3",
        "original harness-only",
        "rgb555",
        "pcm",
        "verify-cgb-game-evidence.py",
        "--write-evidence build/phase21-evidence/result.json",
        "cmake --preset phase1",
        "cmake --build --preset phase1",
        "ctest --preset phase1",
        "Rebound",
        "Libbet and the Magic Floor v0.08",
        "no third candidate",
        "Deck",
        "Libretro",
    ), "game-acceptance")
    _require_markers(profile, (
        "No CGB game-level evidence exists",
        "Phase 21",
        "original native-CGB harness",
        "harness-only",
        "Physical CGB-E remains UNKNOWN/POLICY",
        "CGB mode-3 timing is not claimed",
        "No physical or perceptual audio/color qualification is claimed",
        "general game compatibility",
    ), "cgb-profile")
    _require_markers(support, (
        "Phase 21",
        "No CGB game-level evidence",
        "Potion Panic",
        "µCity 1.3",
        "hardware.inc",
        "harness-only",
        "UNKNOWN/POLICY",
    ), "unreleased-support")
    if outcome["status"] == "no-game":
        _reject_markers(game, ("Admitted game:",), "no-game-outcome")
        primary = records[0]
        fallback = records[1]
        primary_evidence = _nested(primary, "admission", "value", "evidence")
        fallback_evidence = _nested(fallback, "admission", "value", "evidence")
        component = _nested(fallback_evidence, "component_grants", "unresolved_build_component")
        _require_markers(game, (
            "No CGB game-level evidence exists",
            "https://codeberg.org/DevEd/potion-panic",
            "creator-linked source could not be reached",
            "component-level repository/public-CI scope remains unestablished",
            "does not establish a license prohibition",
            UCITY_13_REVISION,
            "source/engine/hardware.inc",
            UCITY_HARDWARE_SHA256,
            "no identified grant or notice",
            "toolchain identity, build confinement, rom bytes, cartridge header, loaded mode, progress, rgb555/pcm observations, and candidate receipt remain not observed",
            "no upstream tool, script, or rom was run",
            "no fallback fixture, case, input, predicate, or notice row was created",
        ), "no-game-outcome")
        if not isinstance(primary_evidence, dict) or primary_evidence.get("creator_page") != "https://deved.itch.io/potion-panic":
            raise Reject("primary-document-evidence-mismatch")
        if not isinstance(component, dict) or component.get("path") != "source/engine/hardware.inc" or component.get("sha256") != UCITY_HARDWARE_SHA256:
            raise Reject("fallback-document-evidence-mismatch")
    else:
        display = next(name for candidate_id, _, name in CANDIDATES if candidate_id == outcome["candidate_id"])
        _reject_markers(game, ("No CGB game-level evidence exists", "Phase 21 admitted no game"),
                        "admitted-game-outcome")
        _require_markers(game, (f"Admitted game: {display}",), "admitted-game-outcome")

    return outcome


def _expect_reject(action, expected_code: str, label: str) -> None:
    try:
        action()
    except Reject as error:
        if error.code != expected_code:
            raise Reject("self-test-unexpected-rejection", f"{label}:{error}") from error
        return
    raise Reject("self-test-control-not-rejected", label)


def _synthetic_records(statuses: tuple[str, str]) -> list[dict[str, Any]]:
    ids = ("potion-panic-gbcompo25", "ucity-1.3")
    return [
        {"candidate_id": candidate_id,
         "disposition": {"status": status, "category": "rights" if status == "no-go" else "",
                         "reason": "synthetic scope gate" if status == "no-go" else ""}}
        for candidate_id, status in zip(ids, statuses)
    ]


def self_test_controls(snapshot: dict[str, bytes]) -> None:
    expected = {"status": "no-game", "candidate_id": "none"}
    records = _synthetic_records(("no-go", "no-go"))
    if candidate_outcome(records) != expected:
        raise Reject("self-test-no-go-positive-failed")
    if candidate_outcome(_synthetic_records(("admitted", "not-needed"))) != {
            "status": "admitted", "candidate_id": "potion-panic-gbcompo25"}:
        raise Reject("self-test-primary-admission-positive-failed")
    if candidate_outcome(_synthetic_records(("no-go", "admitted"))) != {
            "status": "admitted", "candidate_id": "ucity-1.3"}:
        raise Reject("self-test-fallback-admission-positive-failed")

    changed_id = _synthetic_records(("no-go", "no-go"))
    changed_id[1]["candidate_id"] = "third-game"
    _expect_reject(lambda: candidate_outcome(changed_id), "candidate-order-or-identity-invalid", "changed-candidate-identity")

    missing_cause = _synthetic_records(("no-go", "no-go"))
    missing_cause[1]["disposition"].pop("reason")
    _expect_reject(lambda: candidate_outcome(missing_cause), "candidate-no-go-cause-missing", "missing-no-go-cause")

    blocked = _synthetic_records(("no-go", "no-go"))
    blocked[0]["disposition"]["status"] = "blocked-defect"
    _expect_reject(lambda: candidate_outcome(blocked), "candidate-blocked-defect", "blocked-defect")

    base_docs = {
        path: _decode_doc(snapshot, path)
        for path in ("docs/game-acceptance.md", "docs/cgb-profile.md", "docs/support/unreleased.md")
    }
    false_accuracy = dict(base_docs)
    false_accuracy["docs/game-acceptance.md"] += "\nThe frame digests establish rendering accuracy.\n"
    _expect_reject(lambda: reject_claim_inflation(false_accuracy), "documentation-claim-inflation",
                    "accuracy-claim")

    false_hardware = dict(base_docs)
    false_hardware["docs/game-acceptance.md"] += "\nPhysical CGB-E is verified.\n"
    _expect_reject(lambda: reject_claim_inflation(false_hardware), "documentation-claim-inflation",
                    "physical-hardware-claim")

    false_game = dict(base_docs)
    false_game["docs/game-acceptance.md"] += "\nThe original harness proves real-game progress.\n"
    _expect_reject(lambda: reject_claim_inflation(false_game), "documentation-claim-inflation",
                    "game-progress-claim")

    false_rights = dict(base_docs)
    false_rights["docs/game-acceptance.md"] += "\nCC BY-NC-SA prohibits this use.\n"
    _expect_reject(lambda: reject_claim_inflation(false_rights), "documentation-rights-conclusion-overstated", "license-prohibition-claim")

    false_gpl_rights = dict(base_docs)
    false_gpl_rights["docs/game-acceptance.md"] += "\nGPL-3.0-only prohibits this use.\n"
    _expect_reject(lambda: reject_claim_inflation(false_gpl_rights), "documentation-rights-conclusion-overstated",
                    "gpl-license-prohibition-claim")

    false_gpl_rights_inverse = dict(base_docs)
    false_gpl_rights_inverse["docs/game-acceptance.md"] += "\nThis use is prohibited by GPL-3.0-only.\n"
    _expect_reject(lambda: reject_claim_inflation(false_gpl_rights_inverse),
                    "documentation-rights-conclusion-overstated", "inverse-gpl-license-prohibition-claim")

    false_cc_full_rights = dict(base_docs)
    false_cc_full_rights["docs/game-acceptance.md"] += (
        "\nCreative Commons Attribution-NonCommercial-ShareAlike 4.0 International prohibits this use.\n")
    _expect_reject(lambda: reject_claim_inflation(false_cc_full_rights),
                    "documentation-rights-conclusion-overstated", "full-creative-commons-prohibition-claim")

    false_cc_by_sa_rights = dict(base_docs)
    false_cc_by_sa_rights["docs/game-acceptance.md"] += "\nCC BY-SA 4.0 prohibits this use.\n"
    _expect_reject(lambda: reject_claim_inflation(false_cc_by_sa_rights),
                    "documentation-rights-conclusion-overstated", "cc-by-sa-prohibition-claim")

    false_cc_inverse_rights = dict(base_docs)
    false_cc_inverse_rights["docs/game-acceptance.md"] += (
        "\nThis use is prohibited by Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International.\n")
    _expect_reject(lambda: reject_claim_inflation(false_cc_inverse_rights),
                    "documentation-rights-conclusion-overstated", "inverse-creative-commons-prohibition-claim")

    false_mit_rights = dict(base_docs)
    false_mit_rights["docs/game-acceptance.md"] += "\nMIT License prohibits this use.\n"
    _expect_reject(lambda: reject_claim_inflation(false_mit_rights),
                    "documentation-rights-conclusion-overstated", "mit-license-prohibition-claim")

    false_mit_inverse_rights = dict(base_docs)
    false_mit_inverse_rights["docs/game-acceptance.md"] += "\nThis use is prohibited by MIT License.\n"
    _expect_reject(lambda: reject_claim_inflation(false_mit_inverse_rights),
                    "documentation-rights-conclusion-overstated", "inverse-mit-license-prohibition-claim")

    false_bsd_rights = dict(base_docs)
    false_bsd_rights["docs/game-acceptance.md"] += "\nBSD-2-Clause prohibits this use.\n"
    _expect_reject(lambda: reject_claim_inflation(false_bsd_rights),
                    "documentation-rights-conclusion-overstated", "bsd-license-prohibition-claim")

    false_bsd_inverse_rights = dict(base_docs)
    false_bsd_inverse_rights["docs/game-acceptance.md"] += "\nThis use is prohibited by BSD-2-Clause.\n"
    _expect_reject(lambda: reject_claim_inflation(false_bsd_inverse_rights),
                    "documentation-rights-conclusion-overstated", "inverse-bsd-license-prohibition-claim")

    for label, claim in (
        ("gpl", "GPL-3.0 prohibits this use."),
        ("bsd", "BSD-2-Clause forbids repository use."),
        ("cc-by-nc-sa", "CC BY-NC-SA prohibits this use."),
        ("contrastive-not-conclusion",
         "This is not a conclusion that the rights are settled, but GPL-3.0 prohibits this use."),
        ("contrastive-second-verb",
         "GPL-3.0 does not prohibit documenting its terms, but it prohibits this use."),
    ):
        unrelated_negation = dict(base_docs)
        unrelated_negation["docs/game-acceptance.md"] += (
            f"\nThe source does not establish rights. {claim}\n")
        _expect_reject(lambda: reject_claim_inflation(unrelated_negation),
                       "documentation-rights-conclusion-overstated",
                       f"unrelated-negation-{label}-license-prohibition-claim")

    for explicit_negation in (
        "GPL-3.0 does not prohibit this use.",
        "This use is not prohibited by BSD-2-Clause.",
        "This is not a conclusion that CC BY-NC-SA prohibits this use.",
        "MIT never prohibits this use.",
    ):
        if _has_unqualified_license_prohibition(explicit_negation):
            raise Reject("self-test-explicit-negation-failed", explicit_negation)

    admitted_but_no_game = dict(snapshot)
    admitted_but_no_game["docs/game-acceptance.md"] += b"\nAdmitted game: Potion Panic\n"
    _expect_reject(lambda: validate_documentation(admitted_but_no_game,
                                                  _synthetic_records(("admitted", "not-needed"))),
                    "documentation-outcome-contradiction", "admitted-result-with-no-game-claims")

    no_game_but_admitted = dict(snapshot)
    no_game_but_admitted["docs/game-acceptance.md"] += b"\nAdmitted game: Potion Panic\n"
    _expect_reject(lambda: validate_documentation(no_game_but_admitted, parse_snapshot_records(snapshot)),
                    "documentation-outcome-contradiction", "no-game-result-with-admitted-claim")

    scene = _decode_doc(snapshot, "docs/scene-feedback.md")
    owner_play_removed = scene.replace("Owner play is optional and is never a recurring prerequisite.",
                                       "Owner play is required for every report.")
    _expect_reject(lambda: validate_scene_privacy(owner_play_removed), "documentation-contract-missing",
                    "owner-play-limit-removed")
    privacy_removed = scene.replace(
        "Personal ROMs, battery saves, save states, screenshots, videos, and audio remain outside Git and hosted CI.",
        "Personal media may be included in hosted CI.")
    _expect_reject(lambda: validate_scene_privacy(privacy_removed), "documentation-contract-missing",
                    "privacy-limit-removed")
    _expect_reject(lambda: safe_evidence_path(Path("/repo"),
                                              "build/phase21-evidence/../../escape.json"),
                    "evidence-path-traversal", "evidence-path-traversal")
    print("game-evidence controls pass outcomes=3 accepted_negations=4 rejected_controls=26 subjects=synthetic-only")


def _import_progress_checker(root: Path):
    path = root / "tests/scripts/verify-cgb-progress.py"
    spec = importlib.util.spec_from_file_location("gbb_phase21_progress_checker", path)
    if spec is None or spec.loader is None:
        raise Reject("progress-checker-unavailable")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except (ImportError, OSError, SyntaxError) as error:
        raise Reject("progress-checker-load-failed", type(error).__name__) from error
    return module


def _file_sha256(path: Path) -> str:
    try:
        size = path.stat().st_size
        if size <= 0 or size > MAX_RUNNER_BYTES or not path.is_file():
            raise Reject("runner-file-size-invalid")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
    except OSError as error:
        raise Reject("runner-unavailable", error.strerror or "runner") from error


def collect_harness_observation(root: Path, runner: Path, revision: str) -> tuple[dict[str, Any], str]:
    progress = _import_progress_checker(root)
    progress_checker = root / "tests/scripts/verify-cgb-progress.py"
    source_commit, checker_sha = progress.verify_source_identity(root, revision, progress_checker)
    if source_commit != revision:
        raise Reject("progress-source-revision-mismatch")
    runner_sha = _file_sha256(runner)
    rom, _ = progress.build_rom()
    script = progress.input_script(True)
    if hashlib.sha256(rom).hexdigest() != EXPECTED_HARNESS_ROM_SHA256:
        raise Reject("harness-rom-identity-mismatch")
    if hashlib.sha256(script).hexdigest() != EXPECTED_HARNESS_INPUT_SHA256:
        raise Reject("harness-input-identity-mismatch")
    progress.validate_source_anchors(rom)
    with tempfile.TemporaryDirectory(prefix="gbb-phase21-evidence-") as temporary:
        work = Path(temporary)
        work.chmod(0o700)
        (work / "control.gb").write_bytes(rom)
        (work / "positive.input").write_bytes(script)
        cases = progress.case_line("cgb-control-progress", "cgb-control-progress",
                                   "positive.input", rom, script)
        (work / "cases.txt").write_text(cases, encoding="ascii")
        host = progress.load_host_fixture(root)
        code, stdout, stderr = host.run_runner(
            str(runner), ["--acceptance", "cases.txt", "--case", "cgb-control-progress",
                          "--model", "cgb-cpu-e", "--observe", "--receipt"], str(work), 30)
    if code != 0 or stderr:
        raise Reject("harness-observation-run-failed", f"exit={code}")
    observation = progress.validate_observation(stdout, rom, script, source_commit)
    receipt_lines = [line for line in stdout.splitlines() if line.startswith("receipt id=")]
    if len(receipt_lines) != 1:
        raise Reject("harness-receipt-missing")
    receipt = progress.validate_native_receipt(receipt_lines[0], rom, script, source_commit)
    progress.compare_observation_receipt(observation, receipt)
    if _file_sha256(runner) != runner_sha:
        raise Reject("runner-changed-during-check")
    if observation.get("rom_sha256") != EXPECTED_HARNESS_ROM_SHA256 or observation.get("input_sha256") != EXPECTED_HARNESS_INPUT_SHA256:
        raise Reject("harness-observation-identity-mismatch")
    return {
        "software_model": observation["profile"],
        "execution_mode": observation["execution_mode"],
        "evidence_class": "original-harness-only",
        "runner_sha256": runner_sha,
        "checker_sha256": checker_sha,
        "rom_sha256": observation["rom_sha256"],
        "rom_size": int(observation["rom_size"]),
        "input_sha256": observation["input_sha256"],
        "predicate": observation["predicate_name"],
        "progress_state": {
            "ready": observation["predicate.ready"],
            "progress": observation["predicate.progress"],
        },
        "progress_timing": {
            "hit_half_dots": int(observation["t_hit_half_dots"]),
            "end_half_dots": int(observation["end_half_dots"]),
            "budget_half_dots": int(observation["budget_half_dots"]),
        },
        "rgb555": {
            "frame_format": observation["frame_format"],
            "checkpoints": {
                label: {
                    "requested_half_dots": int(observation[f"checkpoint.{label}.requested_half_dots"]),
                    "completion_half_dots": int(observation[f"checkpoint.{label}.completion_half_dots"]),
                    "sha256": observation[f"checkpoint.{label}.frame555"],
                }
                for label in ("title", "play_start", "mid", "hit")
            },
            "rolling_sha256": observation["frame.rolling555"],
        },
        "pcm": {
            "sha256": observation["pcm_sha256"],
            "samples": int(observation["pcm_samples"]),
            "audible": observation["pcm_audible"] == "true",
            "left_peak_to_peak": int(observation["pcm.window.left.peak_to_peak"]),
            "left_changes": int(observation["pcm.window.left.changes"]),
            "right_peak_to_peak": int(observation["pcm.window.right.peak_to_peak"]),
            "right_changes": int(observation["pcm.window.right.changes"]),
        },
        "build": {
            "source_revision": observation["core_revision"],
            "qualified": observation["build_qualified"] == "true",
        },
        "receipt": receipt,
    }, runner_sha


def run_cli(root: Path, label: str, arguments: list[str], marker: str) -> str:
    result = run_bounded([sys.executable, "-I", str(root / "tests/scripts" / label), *arguments], root)
    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    if result.returncode != 0:
        reason = output.strip().replace("\n", " ")[-384:]
        raise Reject("composed-check-failed", f"{label}:{reason}")
    if marker not in output:
        raise Reject("composed-check-marker-missing", label)
    return output


def check_runner_path(root: Path, value: str) -> Path:
    requested = Path(value)
    if not requested.is_absolute():
        requested = root / requested
    try:
        runner = requested.resolve(strict=True)
    except OSError as error:
        raise Reject("runner-unavailable", error.strerror or "runner") from error
    if root != runner and root not in runner.parents:
        raise Reject("runner-path-outside-repository")
    if not runner.is_file() or not os.access(runner, os.X_OK):
        raise Reject("runner-not-executable")
    _file_sha256(runner)
    return runner


def _candidate_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for (candidate_id, path, display), record in zip(CANDIDATES, records):
        status, category, stage, reason = _disposition(record)
        evidence = _nested(record, "admission", "value", "evidence")
        item: dict[str, Any] = {
            "candidate_id": candidate_id,
            "display_name": display,
            "record_path": path,
            "record_sha256": hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False,
                                                          separators=(",", ":")).encode("utf-8")).hexdigest(),
            "disposition": status,
            "category": category,
            "blocker_stage": stage,
            "cause": reason,
        }
        if isinstance(evidence, dict):
            source = _nested(record, "source", "value")
            if isinstance(source, dict) and isinstance(source.get("revision"), str):
                item["source_revision"] = source["revision"]
            unresolved = evidence.get("unresolved_build_component")
            if isinstance(unresolved, dict):
                item["unresolved_component"] = {
                    "path": unresolved.get("path"),
                    "sha256": unresolved.get("sha256"),
                    "rights_scope": unresolved.get("rights_scope"),
                }
        result.append(item)
    return result


def scene_phase_facts(snapshot: dict[str, bytes]) -> dict[str, str]:
    summary = _decode_doc(snapshot, f"{PHASE21_DIR}/21-06-SUMMARY.md").casefold()
    if "the owner supplied no live scene report" not in summary:
        raise Reject("scene-report-status-not-source-bound")
    return {
        "report_status": "none-supplied-for-phase",
        "workflow_status": "synthetic-contract-only; no live regression promoted",
        "private_media": "not examined or included",
        "owner_play": "optional; not a recurring prerequisite",
    }


def collect_check_result(root: Path, runner: Path, revision: str,
                         snapshot: dict[str, bytes]) -> dict[str, Any]:
    records = parse_snapshot_records(snapshot)
    outcome = validate_documentation(snapshot, records)
    candidate_args = ["--check-all", "--require-final", "--repo-root", str(root),
                      "--source-revision", revision]
    if outcome["status"] == "admitted":
        candidate_args.extend(("--runner", str(runner)))
    run_cli(root, "verify-cgb-progress.py",
            ["--discrimination", "--runner", str(runner), "--repo-root", str(root),
             "--source-revision", revision], "cgb-discrimination status=pass")
    run_cli(root, "verify-cgb-progress.py",
            ["--compatibility", "--runner", str(runner), "--repo-root", str(root),
             "--source-revision", revision], "compatibility-control pass actual=cgb-dmg-compat")
    run_cli(root, "verify-cgb-progress.py",
            ["--observations", "--runner", str(runner), "--repo-root", str(root),
             "--source-revision", revision], "cgb-observations status=pass")
    run_cli(root, "verify-cgb-candidates.py", candidate_args,
            f"PASS: candidate records count=2 source={revision}")
    run_cli(root, "verify-scene-report.py",
            ["--self-test", "contract", "--repo-root", str(root), "--source-revision", revision],
            "scene-report documentation contract self-test pass")

    harness, runner_sha = collect_harness_observation(root, runner, revision)
    source_hashes = {path: hashlib.sha256(snapshot[path]).hexdigest() for path in SOURCE_PATHS}
    game_record: dict[str, Any] = {
        "status": "not-admitted" if outcome["status"] == "no-game" else "admitted",
        "candidate_id": outcome["candidate_id"],
        "evidence_class": "no-game-admitted" if outcome["status"] == "no-game" else "candidate-progress",
    }
    if outcome["status"] == "admitted":
        selected = next(record for record in records if record.get("candidate_id") == outcome["candidate_id"])
        game_record["candidate_receipt"] = _nested(selected, "receipt", "value")
    return {
        "schema_version": 1,
        "source_revision": revision,
        "runner_sha256": runner_sha,
        "source_files": source_hashes,
        "game_result": game_record,
        "candidate_attempts": _candidate_summary(records),
        "original_harness": harness,
        "harness_controls": {
            "positive": "pass",
            "no_input": "predicate-not-reached",
            "wrong_input": "predicate-not-reached",
            "impossible_predicate": "predicate-not-reached",
            "strict_xfail": "predicate-not-reached",
            "compatibility_mode": "refused; actual=cgb-dmg-compat",
        },
        "scene_feedback": scene_phase_facts(snapshot),
        "limitations": [
            "The authored control ROM establishes runner progress behavior only; it is not an admitted game.",
            "RGB555 and PCM digests are same-run reproducibility observations, not accuracy or perceptual oracles.",
            "Physical CGB-E behavior, mode-3 timing, and general game compatibility remain unqualified.",
            "Candidate rights/source-scope no-go findings do not establish that a license prohibits use.",
        ],
    }


def safe_evidence_path(root: Path, requested: str) -> Path:
    target = Path(requested)
    if not target.is_absolute():
        target = root / target
    try:
        relative = target.relative_to(root)
    except ValueError as error:
        raise Reject("evidence-path-outside-repository") from error
    if any(part in {".", ".."} for part in relative.parts):
        raise Reject("evidence-path-traversal")
    if not relative.parts or relative.parts[0] != "build" or len(relative.parts) < 3 or relative.parts[1] != "phase21-evidence":
        raise Reject("evidence-path-outside-allowed-directory")
    cursor = root
    for part in relative.parts[:-1]:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise Reject("evidence-path-symlink")
        if not cursor.exists():
            try:
                cursor.mkdir(mode=0o700)
            except OSError as error:
                raise Reject("evidence-directory-create-failed", error.strerror or "directory") from error
        if not cursor.is_dir():
            raise Reject("evidence-path-parent-not-directory")
    final = root.joinpath(*relative.parts)
    if final.exists() and (final.is_symlink() or not final.is_file()):
        raise Reject("evidence-target-invalid")
    return final


def write_evidence(root: Path, requested: str, value: dict[str, Any]) -> str:
    target = safe_evidence_path(root, requested)
    payload = (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    temporary: str | None = None
    try:
        fd, temporary = tempfile.mkstemp(prefix=".phase21-evidence-", suffix=".tmp", dir=target.parent)
        try:
            os.fchmod(fd, 0o600)
        except (AttributeError, OSError):
            pass
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        temporary = None
    except OSError as error:
        raise Reject("evidence-write-failed", error.strerror or "write") from error
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except OSError:
                pass
    return target.relative_to(root).as_posix()


def run_check(args: argparse.Namespace) -> int:
    if not args.runner or not args.repo_root or not args.source_revision or not args.write_evidence:
        raise Reject("check-arguments-required")
    try:
        root = Path(args.repo_root).resolve(strict=True)
    except OSError as error:
        raise Reject("repo-root-unavailable") from error
    revision = resolve_source_revision(root, args.source_revision)
    snapshot = load_snapshot(root, revision)
    runner = check_runner_path(root, args.runner)
    receipt = collect_check_result(root, runner, revision, snapshot)
    output = write_evidence(root, args.write_evidence, receipt)
    print(f"PASS: game-evidence source={revision} model=CGB-CPU-E mode=cgb "
          f"game={receipt['game_result']['status']} evidence={output}")
    return 0


def self_test(snapshot: dict[str, bytes] | None = None) -> None:
    records = _synthetic_records(("no-go", "no-go"))
    if candidate_outcome(records) != {"status": "no-game", "candidate_id": "none"}:
        raise Reject("self-test-no-game-outcome-failed")
    if snapshot is not None:
        parse_snapshot_records(snapshot)
        validate_documentation(snapshot, parse_snapshot_records(snapshot))
        self_test_controls(snapshot)
    print("game-evidence self-test pass outcomes=3 source-grounded-docs=true")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--self-test-controls", action="store_true")
    parser.add_argument("--runner")
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--source-revision")
    parser.add_argument("--write-evidence")
    args = parser.parse_args(argv)
    try:
        if args.check:
            return run_check(args)
        if args.repo_root is None or args.source_revision is None:
            raise Reject("source-revision-and-repo-root-required")
        root = args.repo_root.resolve(strict=True)
        revision = resolve_source_revision(root, args.source_revision)
        snapshot = load_snapshot(root, revision)
        if args.self_test:
            self_test(snapshot)
            return 0
        if args.self_test_controls:
            parse_snapshot_records(snapshot)
            validate_documentation(snapshot, parse_snapshot_records(snapshot))
            self_test_controls(snapshot)
            return 0
        raise Reject("mode-required")
    except (Reject, OSError, UnicodeError, ValueError) as error:
        print(f"verify-cgb-game-evidence: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
