#!/usr/bin/env python3
"""Verify Phase 22 diagnostic no-go evidence from an immutable Git snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
from typing import Any

MAX_BYTES = 2 * 1024 * 1024
MAX_OUTPUT = 32 * 1024 * 1024
# The current immutable source archive is about 61 MiB. Keep this separate from
# subprocess text capture and stream it to disk with a 128 MiB ceiling.
MAX_SOURCE_ARCHIVE_BYTES = 128 * 1024 * 1024
# This Phase 22 merge contains both the historical blocked assessment and the
# point-in-time requirements boundary consumed by this checker.
BASELINE = "ca2f0be6b38e7dd22e0eb3296b9a21cceed1a765"
PHASE22_BOUNDARY_REVISION = "4ac46e7406329efbd4fb6ac0dc39c86c14156691"
HISTORICAL_REQUIREMENT_REVISIONS = frozenset({BASELINE, PHASE22_BOUNDARY_REVISION})
APPROVED_BOUNDARY_REVISIONS = frozenset({PHASE22_BOUNDARY_REVISION})
# D-168/D-172 changed only the archive checker's self-test harness. Keep the
# historical boundary intact and permit exactly its independently reviewed bytes.
ARCHIVE_HARNESS_PATH = "tests/scripts/verify-v02-source-archive.py"
ARCHIVE_HARNESS_PIN = "b50f0c10e0794591a212edbfd083f10084805532"
ARCHIVE_HARNESS_SHA256 = "5a3083b6a7d32c0692672645564241a81d9be0b0939c9ee198afb951f43f183a"
# D-207 adds the precisely pinned Acid2 notice rows while retaining the Phase 22
# assessment boundary; accept only the notice index from the committed fixture snapshot.
NOTICE_INDEX_PIN = "3d0587d49e7d88815c6af7dc36f4810579a8dc48"
NOTICE_INDEX_SHA256 = "3ed10aa3c89249ab7e43364af94e667f14618befbd6168ba60e0211561417b37"
# The notice-path regression changes only the self-test harness. Preserve the
# earlier reviewed bytes too: the permanent release tag still contains them.
NOTICE_PATH_HARNESS_PIN = "5d386d9ddea41c8529a3dadc90b4855b703e383d"
NOTICE_PATH_HARNESS_SHA256 = "046840fc3754e0c7d1c687534c04d796f15fe39ff8e8d5f2ee4cef9f3f8c657e"
CHECKER = "tests/scripts/verify-diagnostic-admission.py"
ASSESSMENT = "tests/external/diagnostic-assessment.json"
INVENTORY = "tests/external/gbmicrotest-inventory.json"
GATES = (
    "acid2_derivative_build_reproducibility",
    "acid2_component_rights_and_output_scope",
    "acid2_profile_applicability",
    "gbmicrotest_component_rights_and_output_scope",
    "gbmicrotest_prebuilt_rom_sha256",
    "gbmicrotest_case_applicability",
    "gbmicrotest_independent_oracle",
)
PHASE22_TESTS = (
    "phase22_acid2_tracer", "phase22_acid2_contract", "phase22_acid2_controls",
    "phase22_admission_assessment", "phase22_fixture_admission_contract",
    "phase22_fixture_admission_controls", "phase22_evidence_contract",
    "phase22_evidence_controls",
)
PRESERVED = (
    "LICENSE", "THIRD_PARTY_NOTICES.md", "cmake/FixtureAdmissionPolicy.json",
    "cmake/ExpectedTests.cmake", "cmake/ScanForbiddenFixtures.cmake",
    "cmake/VerifyFixtureManifest.cmake", "cmake/VerifyFixture.cmake",
    "cmake/VerifyInstalledPackage.cmake", "cmake/PreviewPackageSmoke.cmake",
    "tests/scripts/verify-fixture-admission.py",
    "tests/scripts/verify-v02-source-archive.py",
    ".github/scripts/verify-test-inventory.sh",
)
REQUIRED = (
    "tests/scripts/verify-diagnostic-evidence.py", CHECKER, ASSESSMENT, INVENTORY,
    "docs/diagnostic-evidence.md", "docs/cgb-profile.md", ".planning/REQUIREMENTS.md",
    "tests/CMakeLists.txt", "tests/expected-tests.txt", *PRESERVED,
)
V04_D209_ARCHIVE_REV = "96d502d4733ac54aa8bf7fbfd7813065143771dc"
D209_PRESERVED_SOURCE_SHA256 = {
    "THIRD_PARTY_NOTICES.md": "38820b1dbf48d099438ccc5381d5d75d3b03ea18433e5ea46b7cbd744c1d0011",
    "tests/scripts/verify-fixture-admission.py": "32022b4578426289c24d089c03563a934f964b58bb68c62f5f9bdffcf26e0325",
}
V04_ARCHIVED_REQUIREMENTS = ".planning/milestones/v0.4-REQUIREMENTS.md"
V04_ARCHIVED_ROADMAP = ".planning/milestones/v0.4-ROADMAP.md"
V04_ROOT_REQUIREMENTS = ".planning/REQUIREMENTS.md"
V04_ROOT_ROADMAP = ".planning/ROADMAP.md"
V04_ARCHIVED_DISPOSITIONS = {
    "GAME-01": ("21", "Complete"), "GAME-02": ("21", "Complete"),
    "FIXT-01": ("21", "Pending"), "RIGHTS-01": ("20", "Complete"),
    "DIAG-01": ("22", "Complete"), "DIAG-02": ("22", "Complete"),
    "FEED-01": ("21", "Complete"), "REL-01": ("23", "Complete"),
}
V04_ARCHIVED_REQUIREMENT_IDS = frozenset(V04_ARCHIVED_DISPOSITIONS)
BOUNDARY_PATHS = (
    ".planning/STATE.md", ".planning/state.json", ".planning/ROADMAP.md",
    ".planning/REQUIREMENTS.md", ".planning/config.json",
    ".planning/phases/GB-22-composition-and-microtest-evidence/.continue-here.md",
)
V04_RECOVERY_PLAN = BOUNDARY_PATHS[-1].replace(
    "GB-22-composition-and-microtest-evidence/.continue-here.md",
    "GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-01-PLAN.md",
)
FORBIDDEN_DIRS = ("fixtures/acid2", "fixtures/gbmicrotest")
PHASE24_ADMITTED_FIXTURE_DIRS = ("fixtures/acid2", "fixtures/gbmicrotest")
FORBIDDEN_FILES = (
    "tests/external/diagnostic-package-identities.json",
    "tests/scripts/verify-diagnostic-packages.py",
)
PAYLOAD_SUFFIXES = {
    ".gb", ".gbc", ".rom", ".bin", ".png", ".rgb", ".tar", ".zip",
    ".gz", ".tgz", ".7z", ".bz2", ".xz", ".bmp", ".ppm", ".pbm",
    ".jpg", ".jpeg", ".webp", ".gif", ".tif", ".tiff", ".svg", ".ico",
    ".avif", ".heic", ".rar", ".zst", ".lz4", ".lz", ".arj", ".cab",
    ".iso", ".dmg", ".dat", ".img", ".raw",
}
GB_ROM_LOGO = bytes.fromhex(
    "ceed6666cc0d000b03730083000c000d0008111f8889000edccc6ee6dddd9999bbbb67636e0eecccdddc999fbbb9333e"
)
PAYLOAD_SIGNATURES = (
    b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a", b"\xff\xd8\xff", b"BM",
    b"\x00\x00\x01\x00",
    b"II*\x00", b"MM\x00*", b"RIFF", b"PK\x03\x04", b"PK\x05\x06",
    b"Rar!\x1a\x07", b"7z\xbc\xaf\x27\x1c", b"\x1f\x8b", b"BZh",
    b"\xfd7zXZ\x00", b"\x28\xb5\x2f\xfd", b"\x04\x22\x4d\x18",
)
HEX40 = re.compile(r"^[0-9a-f]{40}$")
ANSI_ESCAPE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
C1_OSC_ESCAPE = re.compile(r"\u009d.*?\u009c", re.DOTALL)
DIAGNOSTIC_CONTROLS = re.compile(r"[\x00-\x1f\x7f-\x9f]+")


class Reject(ValueError):
    pass


def sanitized_diagnostic(value: bytes | str,
                         roots: tuple[tuple[str | pathlib.Path, str], ...]) -> str:
    """Return at most 700 characters without escape sequences or local roots."""
    text = value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value)
    text = ANSI_ESCAPE.sub("", text)
    text = C1_OSC_ESCAPE.sub("", text)
    replacements: dict[str, str] = {}
    for root, token in roots:
        native = os.fspath(root)
        if not native:
            continue
        for spelling in {native, native.replace("\\", "/"), native.replace("/", "\\")}:
            if spelling:
                replacements[spelling] = token
    for spelling, token in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(spelling, token)
    return " ".join(DIAGNOSTIC_CONTROLS.sub(" ", text).split())[:700]


def cmake_path_literal(path: str | pathlib.Path) -> str:
    """Serialize a path into a CMake quoted argument using portable separators."""
    return os.fspath(path).replace("\\", "/").replace('"', '\\"')


def git_environment() -> dict[str, str]:
    """Build a small Git-only environment with repository/config redirection removed."""
    allowed = (
        "PATH", "TMPDIR", "TMP", "TEMP", "SYSTEMROOT", "SystemRoot", "WINDIR",
        "PATHEXT", "COMSPEC",
    )
    environment = {key: os.environ[key] for key in allowed if key in os.environ}
    environment.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "LC_ALL": "C",
    })
    return environment


def run(argv: list[str], root: pathlib.Path, *, timeout: int = 30,
        operation: str = "child-process",
        limit: int = MAX_OUTPUT,
        env: dict[str, str] | None = None) -> tuple[int, bytes, bytes]:
    if not argv or any("\x00" in arg for arg in argv):
        raise Reject("subprocess-arguments-invalid")
    try:
        process = subprocess.Popen(argv, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   env=env if env is not None else
                                   {**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    except OSError as error:
        raise Reject(f"subprocess-start-failed:{error.__class__.__name__}") from None
    outputs = [bytearray(), bytearray()]
    exceeded = threading.Event()
    read_errors: list[OSError] = []

    def drain(stream, output: bytearray) -> None:
        try:
            while chunk := stream.read(64 * 1024):
                if len(output) + len(chunk) > limit:
                    exceeded.set()
                if not exceeded.is_set():
                    output.extend(chunk)
        except OSError as error:
            read_errors.append(error)

    readers = [
        threading.Thread(target=drain, args=(process.stdout, outputs[0]), daemon=True),
        threading.Thread(target=drain, args=(process.stderr, outputs[1]), daemon=True),
    ]
    for reader in readers:
        reader.start()
    deadline = time.monotonic() + timeout
    timed_out = False
    while process.poll() is None:
        if exceeded.is_set():
            try:
                process.kill()
            except OSError:
                pass
            break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
            try:
                process.kill()
            except OSError:
                pass
            break
        try:
            process.wait(timeout=min(0.05, remaining))
        except subprocess.TimeoutExpired:
            continue
    process.wait()
    for reader in readers:
        reader.join(timeout=2)
    if any(reader.is_alive() for reader in readers):
        for stream in (process.stdout, process.stderr):
            if stream is not None:
                stream.close()
        raise Reject("subprocess-output-reader-stuck")
    if timed_out:
        raise Reject(f"subprocess-timeout:{operation}") from None
    if exceeded.is_set():
        raise Reject("subprocess-output-limit")
    if read_errors:
        raise Reject("subprocess-output-read-failed")
    return process.returncode, bytes(outputs[0]), bytes(outputs[1])


def git(root: pathlib.Path, *args: str, limit: int = MAX_OUTPUT) -> bytes:
    code, out, err = run(["git", "--no-replace-objects", *args], root,
                         limit=limit, env=git_environment())
    if code:
        detail = err.decode("utf-8", "replace")[-350:].strip()
        raise Reject(f"git-failed:{args[0]}:{detail}")
    return out


def resolve_revision(root: pathlib.Path, expr: str) -> str:
    if not expr or expr.startswith("-") or "\x00" in expr or len(expr) > 256:
        raise Reject("source-revision-invalid")
    value = git(root, "rev-parse", "--verify", "--end-of-options",
                f"{expr}^{{commit}}", limit=1024).decode("ascii", "strict").strip()
    if not HEX40.fullmatch(value):
        raise Reject("source-revision-not-full-commit")
    git(root, "cat-file", "-e", f"{value}^{{commit}}", limit=1024)
    return value


def safe_path(path: str) -> bool:
    return (bool(path) and not path.startswith("/") and "\\" not in path and "\x00" not in path
            and all(part not in ("", ".", "..") and re.fullmatch(r"[A-Za-z0-9._+-]+", part)
                    for part in path.split("/")))


def tree_entries(root: pathlib.Path, revision: str) -> dict[str, tuple[str, int, str]]:
    raw = git(root, "ls-tree", "-rz", "-l", "--full-tree", revision)
    result = {}
    for row in raw.split(b"\0"):
        if not row:
            continue
        try:
            metadata, path_raw = row.split(b"\t", 1)
            mode, kind, oid, *size_field = metadata.decode("ascii").split()
            path = path_raw.decode("utf-8", "strict")
        except (ValueError, UnicodeError):
            raise Reject("git-tree-entry-invalid") from None
        if not safe_path(path):
            raise Reject("git-tree-path-unsafe")
        if kind != "blob" or mode not in ("100644", "100755", "120000"):
            continue
        if mode == "120000":
            result[path] = (oid, -1, mode)
            continue
        try:
            size = int(size_field[0])
        except (IndexError, ValueError):
            raise Reject("git-tree-size-invalid") from None
        result[path] = (oid, size, mode)
        if len(result) > 100_000:
            raise Reject("git-tree-entry-limit")
    return result


def _current_snapshot_paths(entries: dict[str, tuple[str, int, str]]) -> tuple[str, ...]:
    has_requirements_archive = V04_ARCHIVED_REQUIREMENTS in entries
    has_roadmap_archive = V04_ARCHIVED_ROADMAP in entries
    if has_requirements_archive != has_roadmap_archive:
        raise Reject("source-archive-pair-invalid")
    if not has_requirements_archive:
        raise Reject("source-archive-pair-required")
    if V04_ROOT_REQUIREMENTS in entries:
        raise Reject("active-root-requirements-restored")
    shared = tuple(path for path in REQUIRED if path != V04_ROOT_REQUIREMENTS)
    return (*shared, V04_ARCHIVED_REQUIREMENTS, V04_ARCHIVED_ROADMAP,
            V04_ROOT_ROADMAP, V04_RECOVERY_PLAN)


def selected_snapshot_paths(root: pathlib.Path, revision: str) -> tuple[str, ...]:
    return _current_snapshot_paths(tree_entries(root, revision))


def load_snapshot(root: pathlib.Path, revision: str,
                  paths: tuple[str, ...] | None = None) -> dict[str, bytes]:
    entries = tree_entries(root, revision)
    result = {}
    if paths is None:
        paths = selected_snapshot_paths(root, revision)
    for path in paths:
        if not safe_path(path):
            raise Reject(f"source-path-unsafe:{path}")
        item = entries.get(path)
        if item is None:
            raise Reject(f"source-record-missing:{path}")
        _oid, size, mode = item
        if mode == "120000":
            raise Reject(f"source-symlink-refused:{path}")
        if size > MAX_BYTES:
            raise Reject(f"source-record-size-limit:{path}")
        content = git(root, "show", f"{revision}:{path}", limit=MAX_BYTES + 1)
        if len(content) != size:
            raise Reject(f"source-record-size-mismatch:{path}")
        result[path] = content
    return result


def parse_json(raw: bytes, label: str) -> dict[str, Any]:
    if len(raw) > MAX_BYTES:
        raise Reject(f"{label}-size-limit")

    def pairs(rows):
        value = {}
        for key, item in rows:
            if key in value:
                raise Reject(f"{label}-duplicate-key:{key}")
            value[key] = item
        return value

    def constant(value: str):
        raise Reject(f"{label}-invalid-constant:{value}")

    try:
        data = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=pairs,
                          parse_constant=constant)
    except Reject:
        raise
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise Reject(f"{label}-invalid-json") from None
    if not isinstance(data, dict):
        raise Reject(f"{label}-invalid-root")
    return data


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def snapshot_root(snapshot: dict[str, bytes], parent: pathlib.Path) -> pathlib.Path:
    root = parent / "repo"
    for path, raw in snapshot.items():
        target = root.joinpath(*path.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    return root


def baseline_assessment_revision(root: pathlib.Path) -> str:
    raw = git(root, "show", f"{BASELINE}:{ASSESSMENT}", limit=MAX_BYTES)
    return str(parse_json(raw, "baseline-assessment").get("source_revision", ""))


def validate_metadata(snapshot: dict[str, bytes], revision: str,
                      repo: pathlib.Path) -> dict[str, Any]:
    assessment = parse_json(snapshot[ASSESSMENT], "diagnostic-assessment")
    inventory = parse_json(snapshot[INVENTORY], "diagnostic-inventory")
    if assessment.get("status") != "blocked":
        raise Reject("assessment-not-blocked")
    if assessment.get("source_revision") != baseline_assessment_revision(repo):
        raise Reject("historical-assessment-revision-changed")
    if assessment.get("source_revision") == revision:
        raise Reject("historical-assessment-revision-inflated")
    if set(assessment) != {
        "schema", "origin", "status", "source_revision", "assessed_at", "assessment_method",
        "source_rechecks", "build_assessment", "model_applicability", "prebuilt_identity",
        "components", "required_gates", "downstream_not_observed",
    }:
        raise Reject("assessment-record-shape-mutated")
    gates = assessment.get("required_gates")
    unresolved = ([item.get("id") for item in gates
                   if isinstance(item, dict) and item.get("status") == "unresolved"]
                  if isinstance(gates, list) else [])
    if tuple(unresolved) != GATES:
        raise Reject("assessment-unresolved-gates-mismatch")
    if not isinstance(assessment.get("downstream_not_observed"), list):
        raise Reject("assessment-real-result-claims-invalid")
    baseline_record = parse_json(
        git(repo, "show", f"{BASELINE}:{ASSESSMENT}", limit=MAX_BYTES), "baseline-assessment"
    )
    current_components = [(row.get("id"), row.get("status"))
                          for row in assessment.get("components", []) if isinstance(row, dict)]
    baseline_components = [(row.get("id"), row.get("status"))
                           for row in baseline_record.get("components", []) if isinstance(row, dict)]
    if current_components != baseline_components:
        raise Reject("assessment-component-rights-disposition-changed")
    if set(inventory) != {"accounting", "cases", "counts", "schema", "upstream"}:
        raise Reject("inventory-record-shape-mutated")
    if inventory.get("counts") != {
        "named_cases": 513, "shared_macro_verdict": 480, "inline_verdict": 2,
        "initial_no_protocol_exclusions": 31, "protocol_candidates": 482,
    }:
        raise Reject("inventory-counts-mismatch")
    cases = inventory.get("cases")
    if not isinstance(cases, list) or len(cases) != 513:
        raise Reject("inventory-case-count-mismatch")
    names = [case.get("name") for case in cases if isinstance(case, dict)]
    if (len(names) != 513 or len(set(names)) != 513
            or names != sorted(names, key=lambda name: name.encode("utf-8"))):
        raise Reject("inventory-roster-identity-mismatch")
    for case in cases:
        if not isinstance(case, dict):
            raise Reject("inventory-case-invalid")
        if case.get("model_applicability", {}).get("status") != "unresolved":
            raise Reject(f"inventory-model-applicability-mutated:{case['name']}")
        for field in ("source", "prebuilt_rom"):
            identity = case.get(field)
            if (not isinstance(identity, dict) or identity.get("sha256") is not None
                    or not str(identity.get("sha256_status", "")).startswith("not-computed;")):
                raise Reject(f"inventory-payload-digest-known:{case['name']}:{field}")
    account = inventory.get("accounting")
    if (not isinstance(account, dict) or account.get("admitted_eligible_names") != []
            or account.get("executed_names") != []
            or len(account.get("excluded_names", [])) != 31
            or len(account.get("blocked_not_observed_names", [])) != 482
            or account.get("final_suite_accounting_complete") is not False):
        raise Reject("inventory-accounting-mutated")
    # Reuse the pinned roster projection and metadata validator from this exact source.
    with tempfile.TemporaryDirectory(prefix="gbb-diagnostic-snapshot-") as tmp:
        copied = snapshot_root({path: snapshot[path] for path in (CHECKER, ASSESSMENT, INVENTORY)},
                               pathlib.Path(tmp))
        checker = copied / CHECKER
        checker_digest = sha256(snapshot[CHECKER])
        code, out, err = run(
            [sys.executable, "-I", str(checker), "--check-assessment",
             "--repo-root", str(copied), "--source-revision", revision], copied)
        if code != 0 or b"status=blocked" not in out + err or b"gbmicrotest_cases=513" not in out + err:
            raise Reject("assessment-check-contract-failed")
        code, out, err = run(
            [sys.executable, "-I", str(checker), "--require-approved",
             "--repo-root", str(copied), "--source-repo-root", str(repo),
             "--source-revision", revision], copied)
        refusal = (out + err).decode("utf-8", "replace")
        if code != 2 or "scope-resolution-required" not in refusal:
            raise Reject("approval-refusal-contract-invalid")
        if any(gate not in refusal for gate in GATES):
            # Phase 24's source-specific candidate-rights check can refuse before
            # the historical assessment gates are echoed. The immutable
            # assessment above already verifies the complete unresolved gate set;
            # accept only its exact current two-component early refusal here.
            expected_rights_refusal = (
                "scope-resolution-required: candidate-rights-unresolved: "
                "potion-panic-gbcompo25/converter-code,ucity-1.3/hardware-inc"
            )
            if refusal.strip() != expected_rights_refusal:
                raise Reject("approval-refusal-gates-incomplete")
        if "Traceback" in refusal or "subprocess" in refusal:
            raise Reject("approval-refusal-generic-failure")
    return {
        "historical_assessment_revision": assessment["source_revision"],
        "cases": 513, "shared_macro": 480, "inline": 2,
        "initial_exclusions": 31, "blocked_not_observed": 482,
        "admitted": 0, "executed": 0, "unresolved_gate_ids": list(GATES),
        "approval_refusal_exit": 2, "approval_refusal": "scope-resolution-required",
        "assessment_checker_sha256": checker_digest,
    }


def decode(snapshot: dict[str, bytes], path: str) -> str:
    try:
        return snapshot[path].decode("utf-8", "strict")
    except (KeyError, UnicodeError):
        raise Reject(f"source-document-invalid:{path}") from None


def section(text: str, heading: str, label: str) -> str:
    match = re.search(rf"(?m)^## {re.escape(heading)}\s*$", text)
    if not match:
        raise Reject(f"documentation-section-missing:{label}")
    next_header = re.search(r"(?m)^## ", text[match.end():])
    end = match.end() + next_header.start() if next_header else len(text)
    value = re.sub(r"(?s)<!--.*?-->", "", text[match.end():end])
    if not value.strip():
        raise Reject(f"documentation-section-empty:{label}")
    return value


def validate_docs(snapshot: dict[str, bytes], *, complete: bool = False) -> dict[str, str]:
    evidence = decode(snapshot, "docs/diagnostic-evidence.md")
    profile = decode(snapshot, "docs/cgb-profile.md")
    if not complete:
        current = section(evidence, "Current gate result", "diagnostic-evidence")
        if "seven unresolved evidence gates" not in current:
            raise Reject("documentation-gate-summary-missing")
        if "not a finding that an upstream license prohibits use" not in current:
            raise Reject("documentation-rights-conclusion-overstated")
        if ("Requirements DIAG-01, DIAG-02, and RIGHTS-01 remain Pending" not in evidence
                and "record does not complete DIAG-01, DIAG-02, or RIGHTS-01" not in current):
            raise Reject("documentation-requirement-disposition-missing")
        if "CGB profile" not in profile and "Phase 22" not in profile:
            raise Reject("documentation-profile-scope-missing")
        return {"diagnostic-evidence": "Current gate result"}
    for label, text, heading in (
        ("diagnostic-evidence", evidence, "Phase 22 disposition"),
        ("cgb-profile", profile, "Phase 22 diagnostic evidence"),
    ):
        current = section(text, heading, label)
        normalized = " ".join(current.casefold().split())
        clauses = (
            "original synthetic DMG composition and controls passed",
            "metadata-only assessment retained all 513 source/ROM names",
            "No real upstream diagnostic payload was fetched, retained, built, run, or admitted",
            "no real diagnostic result exists",
            "Git blob IDs and sizes do not provide ROM SHA-256 values, reproducibility, or redistribution rights",
            "31 initial exclusions", "482 blocked and not observed",
            "zero admitted and zero executed", "DIAG-01 and DIAG-02 remain Pending",
            "RIGHTS-01 remains Pending under Phase 20 ownership", "a separately selected scope",
            "does not conclude that license terms prohibit use",
            "CPU-08", "DMG-CPU-B", "CGB-CPU-E",
        )
        for clause in clauses:
            if " ".join(clause.casefold().split()) not in normalized:
                raise Reject(f"documentation-current-claim-missing:{label}:{clause}")
        claim_fields = (
            "synthetic composition | supported",
            "source metadata | supported",
            "real diagnostic bytes/results | unsupported",
            "rights and profile applicability | unresolved",
            "DIAG/RIGHTS requirement completion | pending",
        )
        for field in claim_fields:
            if " ".join(field.casefold().split()) not in normalized:
                raise Reject(f"documentation-claim-field-missing:{label}:{field}")
        for gate in GATES:
            if gate not in current:
                raise Reject(f"documentation-gate-missing:{label}:{gate}")
        for phrase in ("real diagnostic result passed", "license prohibits use",
                       "license prohibition", "DIAG-01 is complete", "DIAG-02 is complete",
                       "hardware qualified", "mode-3 timing passed",
                       "broad compatibility established"):
            if phrase.casefold() in normalized:
                raise Reject(f"documentation-claim-overstated:{label}:{phrase}")
    return {"diagnostic-evidence": "Phase 22 disposition",
            "cgb-profile": "Phase 22 diagnostic evidence"}


def requirement_parts(text: str) -> tuple[dict[str, str], dict[str, str]]:
    definitions, trace = {}, {}
    for line in text.splitlines():
        match = re.match(r"- \[([ xX])\] \*\*(DIAG-01|DIAG-02|RIGHTS-01)\*\*:.*", line)
        if match:
            definitions[match.group(2)] = line
        match = re.match(r"\| (DIAG-01|DIAG-02|RIGHTS-01) \| Phase (\d+) \| (Pending|Complete) \|", line)
        if match:
            trace[match.group(1)] = f"Phase {match.group(2)}|{match.group(3)}"
    return definitions, trace


def immutable_regular_blob(root: pathlib.Path, revision: str, path: str) -> bytes:
    entries = tree_entries(root, revision)
    item = entries.get(path)
    if item is None:
        raise Reject(f"archive-source-missing:{path}")
    _oid, size, mode = item
    if mode not in ("100644", "100755"):
        raise Reject(f"archive-source-not-regular:{path}")
    content = git(root, "show", f"{revision}:{path}", limit=MAX_BYTES + 1)
    if len(content) != size:
        raise Reject(f"archive-source-size-mismatch:{path}")
    return content


def archived_requirement_facts(raw: bytes) -> tuple[dict[str, str], dict[str, str]]:
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeError:
        raise Reject("archived-requirements-invalid-utf8") from None
    criteria: dict[str, str] = {}
    checkbox: dict[str, str] = {}
    trace: dict[str, str] = {}
    for line in text.splitlines():
        definition = re.match(r"- \[([ xX])\] \*\*([A-Z]+-\d+)\*\*: (.+)$", line)
        if definition:
            identifier = definition.group(2)
            if identifier in criteria or not definition.group(3).strip():
                raise Reject("archived-requirement-definition-invalid")
            criteria[identifier] = definition.group(3)
            checkbox[identifier] = "Complete" if definition.group(1).casefold() == "x" else "Pending"
        row = re.match(r"\| ([A-Z]+-\d+) \| Phase (\d+) \| (Complete|Pending) \|", line)
        if row:
            identifier = row.group(1)
            if identifier in trace:
                raise Reject("archived-requirement-trace-duplicate")
            trace[identifier] = f"{row.group(2)}|{row.group(3)}"
    expected_trace = {identifier: f"{owner}|{status}"
                      for identifier, (owner, status) in V04_ARCHIVED_DISPOSITIONS.items()}
    if (set(criteria) != V04_ARCHIVED_REQUIREMENT_IDS
            or set(trace) != V04_ARCHIVED_REQUIREMENT_IDS
            or trace != expected_trace
            or checkbox != {identifier: status
                            for identifier, (_owner, status) in V04_ARCHIVED_DISPOSITIONS.items()}):
        raise Reject("archived-requirement-owner-status-invalid")
    return criteria, trace


def validate_recovery_contract(snapshot: dict[str, bytes], plan_paths: list[str]) -> None:
    roadmap = decode(snapshot, V04_ROOT_ROADMAP)
    if V04_ROOT_REQUIREMENTS in snapshot:
        raise Reject("active-root-requirements-restored")
    sections = re.findall(r"(?ms)^## Recovery Phase[ \t]*\n(.*?)(?=^##[ \t]+|\Z)", roadmap)
    if len(sections) != 1:
        raise Reject("recovery-route-section-invalid")
    section = sections[0]
    phases = re.findall(r"(?m)^### Phase (\d+(?:\.\d+)?): ([^\n]+)$", section)
    plans = re.findall(r"(?<![A-Za-z0-9._-])24-\d[^/\\\s`]*-PLAN[^/\\\s`]*\.md", section,
                       flags=re.IGNORECASE)
    if (phases != [("24", "Resolve remaining v0.4 evidence and verification gaps")]
            or plans != ["24-01-PLAN.md"] or "D-209" not in section):
        raise Reject("recovery-route-content-invalid")
    if plan_paths != [V04_RECOVERY_PLAN]:
        raise Reject("recovery-plan-set-invalid")
    plan = decode(snapshot, V04_RECOVERY_PLAN)
    frontmatter = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", plan, re.DOTALL)
    if frontmatter is None:
        raise Reject("recovery-plan-boundary-invalid")
    metadata = frontmatter.group(1)
    requirement_boundary = re.search(r"(?m)^requirement_boundary:[ \t]*(.+)$", metadata)
    boundary_claim = requirement_boundary.group(1).strip().strip("\"'") if requirement_boundary else ""
    if (re.search(r"(?m)^phase: GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps$",
                  metadata) is None
            or re.search(r"(?m)^plan: [\"']?01[\"']?$", metadata) is None
            or re.search(r"(?m)^requirements: \[\]$", metadata) is None
            or not all(claim in boundary_claim for claim in (
                "phase_req_ids=null", "no assignment",
                "archived v0.4 owners and dispositions remain authoritative"))):
        raise Reject("recovery-plan-boundary-invalid")


def require_source_archive_pair(snapshot: dict[str, bytes]) -> None:
    archive_flags = (V04_ARCHIVED_REQUIREMENTS in snapshot, V04_ARCHIVED_ROADMAP in snapshot)
    if archive_flags != (True, True):
        raise Reject("source-archive-pair-invalid" if any(archive_flags) else "source-archive-pair-required")


def validate_recovery_route(snapshot: dict[str, bytes], root: pathlib.Path, revision: str) -> None:
    require_source_archive_pair(snapshot)
    phase_dir = V04_RECOVERY_PLAN.rsplit("/", 1)[0] + "/"
    plan_paths = sorted(
        path for path in tree_entries(root, revision)
        if path.startswith(phase_dir)
        and re.match(r"^24-\d[^/\\]*-PLAN[^/\\]*\.md$", path.rsplit("/", 1)[-1], re.IGNORECASE)
    )
    validate_recovery_contract(snapshot, plan_paths)


def validate_requirements(snapshot: dict[str, bytes], root: pathlib.Path) -> None:
    require_source_archive_pair(snapshot)
    if V04_ROOT_REQUIREMENTS in snapshot:
        raise Reject("active-root-requirements-restored")
    for path in (V04_ARCHIVED_REQUIREMENTS, V04_ARCHIVED_ROADMAP):
        expected = immutable_regular_blob(root, V04_D209_ARCHIVE_REV, path)
        if snapshot[path] != expected:
            raise Reject(f"archived-source-mismatch:{path}")
    archived_requirement_facts(snapshot[V04_ARCHIVED_REQUIREMENTS])


def validate_historical_requirements(snapshot: dict[str, bytes], root: pathlib.Path,
                                     revision: str, *, test_fixture_revision: str | None = None) -> None:
    approved = HISTORICAL_REQUIREMENT_REVISIONS
    if test_fixture_revision is not None:
        if not HEX40.fullmatch(test_fixture_revision) or revision != test_fixture_revision:
            raise Reject("historical-requirements-test-revision-invalid")
        approved = approved | {test_fixture_revision}
    if not HEX40.fullmatch(revision) or revision not in approved:
        raise Reject("historical-requirements-revision-unapproved")
    if V04_ARCHIVED_REQUIREMENTS in snapshot or V04_ARCHIVED_ROADMAP in snapshot:
        raise Reject("historical-requirements-mode-invalid")
    if V04_ROOT_REQUIREMENTS not in snapshot:
        raise Reject("historical-requirements-missing")
    current = decode(snapshot, ".planning/REQUIREMENTS.md")
    old = git(root, "show", f"{BASELINE}:.planning/REQUIREMENTS.md",
              limit=MAX_BYTES).decode("utf-8", "strict")
    current_defs, current_trace = requirement_parts(current)
    old_defs, _ = requirement_parts(old)
    if current_defs != old_defs or set(current_defs) != {"DIAG-01", "DIAG-02", "RIGHTS-01"}:
        raise Reject("requirement-definition-changed")
    if current_trace != {"DIAG-01": "Phase 22|Pending", "DIAG-02": "Phase 22|Pending",
                         "RIGHTS-01": "Phase 20|Pending"}:
        raise Reject("requirement-disposition-changed")


def validate_boundary_revision(revision: str) -> None:
    if not HEX40.fullmatch(revision) or revision not in APPROVED_BOUNDARY_REVISIONS:
        raise Reject("boundary-revision-unapproved")


def validate_test_text(snapshot: dict[str, bytes]) -> None:
    cmake = decode(snapshot, "tests/CMakeLists.txt")
    for name in PHASE22_TESTS:
        count = len(re.findall(rf"\badd_test\s*\(\s*NAME\s+{re.escape(name)}\b", cmake))
        if count != 1:
            raise Reject(f"ctest-cmake-membership-invalid:{name}")
    validate_expected_text(decode(snapshot, "tests/expected-tests.txt"))
    if re.search(r"add_test\s*\(\s*NAME\s+phase22_(?:acid2|gbmicrotest)\w*admitted", cmake, re.I):
        raise Reject("real-admitted-case-registration-present")


def validate_expected_text(inventory: str) -> None:
    for name in PHASE22_TESTS:
        if sum(line.strip() == name for line in inventory.splitlines()) != 1:
            raise Reject(f"ctest-inventory-membership-invalid:{name}")


def configured_names(build: pathlib.Path) -> list[str]:
    if not build.is_dir():
        raise Reject("configured-build-missing")
    code, out, _err = run(["ctest", "--test-dir", str(build), "--show-only=json-v1"], build)
    if code:
        raise Reject("configured-ctest-json-unavailable")
    try:
        names = [row["name"] for row in json.loads(out.decode("utf-8", "strict"))["tests"]]
    except (UnicodeError, ValueError, KeyError, TypeError):
        raise Reject("configured-ctest-json-invalid") from None
    if len(names) != len(set(names)):
        raise Reject("configured-ctest-duplicate-name")
    return names


def check_expected_policy(snapshot: dict[str, bytes], actual: list[str],
                          temp: pathlib.Path) -> None:
    # Run the existing canonical CMake filter against the configured test set.
    src, project = temp / "policy-source", temp / "policy-check"
    for path in ("tests/expected-tests.txt", "cmake/ExpectedTests.cmake"):
        target = src / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(snapshot[path])
    project.mkdir()
    installed = {
        "installed_runner_smoke", "installed_consumer_c", "installed_consumer_cpp",
        "installed_consumer_phase2_c", "installed_consumer_phase2_cpp", "installed_host_smoke",
    }
    prefix = temp / "install-prefix"
    has_prefix = bool(set(actual) & installed)
    if has_prefix:
        prefix.mkdir()
    cmake_exe = shutil.which("cmake")
    if not cmake_exe:
        raise Reject("cmake-unavailable")
    cmake_exe_literal = cmake_path_literal(cmake_exe)
    add_tests = "\n".join(
        f'add_test(NAME "{name}" COMMAND "{cmake_exe_literal}" -E true)' for name in sorted(actual)
    )
    project_file = (
        "cmake_minimum_required(VERSION 3.20)\nproject(Inventory NONE)\n"
        f'set(PROJECT_SOURCE_DIR "{src.as_posix()}")\n'
        f'set(GBB_TEST_INSTALL_PREFIX "{prefix.as_posix() if has_prefix else ""}")\n'
        f"{add_tests}\ninclude(\"{(src / 'cmake/ExpectedTests.cmake').as_posix()}\")\n"
        "gabbaboy_verify_registered_tests()\n"
    )
    (project / "CMakeLists.txt").write_text(project_file, encoding="utf-8")
    code, out, err = run(["cmake", "-S", str(project), "-B", str(project / "build")], project,
                         operation="expected-test-policy-configure")
    if code:
        output = (out + err).decode("utf-8", "replace").casefold()
        if "registered ctest cases differ" in output:
            raise Reject("configured-ctest-inventory-mismatch")
        detail = sanitized_diagnostic(out + err, ((temp, "<temp>"),
                                                   (pathlib.Path.home(), "<home>")))
        raise Reject(f"expected-test-policy-failed:{detail}")


def validate_tests(snapshot: dict[str, bytes], build: pathlib.Path) -> int:
    validate_test_text(snapshot)
    names = configured_names(build)
    with tempfile.TemporaryDirectory(prefix="gbb-expected-tests-") as tmp:
        check_expected_policy(snapshot, names, pathlib.Path(tmp))
    return len(names)


def forbidden_fixture_path(path: str, content: bytes = b"") -> bool:
    value = path.casefold()
    if any(value == item or value.startswith(item + "/")
           for item in (*FORBIDDEN_DIRS, *FORBIDDEN_FILES)):
        return True
    if value == "tests/acid2/control.asm":
        return False
    # Reject recognizable payload extensions and known ROM, image, or archive
    # signatures when a payload is renamed to an unrelated or extensionless path.
    if pathlib.PurePosixPath(value).suffix in PAYLOAD_SUFFIXES:
        return True
    prefix = content[:4096]
    logo_end = 0x104 + len(GB_ROM_LOGO)
    if len(prefix) >= logo_end and prefix[0x104:logo_end] == GB_ROM_LOGO:
        return True
    if any(prefix.startswith(signature) for signature in PAYLOAD_SIGNATURES):
        return True
    if len(prefix) >= 12 and prefix[4:8] == b"ftyp" and prefix[8:12] in {
        b"avif", b"avis", b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1",
    }:
        return True
    if len(prefix) >= 262 and prefix[257:262] == b"ustar":
        return True
    if is_svg_document(content):
        return True
    if re.match(rb"\s*P[1-6][\s\r\n]", prefix):
        return True
    return False


def phase24_admitted_fixture_path(path: str) -> bool:
    return any(path == directory or path.startswith(directory + "/")
               for directory in PHASE24_ADMITTED_FIXTURE_DIRS)


def is_svg_document(content: bytes) -> bool:
    """Recognize an SVG document root without matching source-code examples."""
    content = normalize_xml_markup(content)
    candidate = content[3:] if content.startswith(b"\xef\xbb\xbf") else content
    while True:
        candidate = candidate.lstrip(b" \t\r\n")
        lowered = candidate[:32].lower()
        if lowered.startswith(b"<!--"):
            end = candidate.find(b"-->", 4)
            if end < 0:
                return False
            candidate = candidate[end + 3:].lstrip(b" \t\r\n")
        elif lowered.startswith(b"<?"):
            end = candidate.find(b"?>", 2)
            if end < 0:
                return False
            candidate = candidate[end + 2:].lstrip(b" \t\r\n")
        elif lowered.startswith(b"<!doctype"):
            end = doctype_end(candidate)
            if end < 0:
                return False
            candidate = candidate[end + 1:].lstrip(b" \t\r\n")
        else:
            return re.match(rb"<(?:[^:/\s<>]+:)?svg(?=[\s/>])",
                            candidate, re.IGNORECASE) is not None


def normalize_xml_markup(content: bytes) -> bytes:
    """Project UTF-16 XML punctuation to ASCII for bounded root recognition."""
    if content.startswith(b"\xff\xfe"):
        offset, little_endian = 2, True
    elif content.startswith(b"\xfe\xff"):
        offset, little_endian = 2, False
    elif content.startswith(b"<\x00"):
        offset, little_endian = 0, True
    elif content.startswith(b"\x00<"):
        offset, little_endian = 0, False
    else:
        return content
    encoded = memoryview(content)[offset:]
    if len(encoded) % 2:
        return b""
    normalized = bytearray(len(encoded) // 2)
    for index in range(0, len(encoded), 2):
        first, second = encoded[index], encoded[index + 1]
        low, high = (first, second) if little_endian else (second, first)
        normalized[index // 2] = low if high == 0 else 0xff
    return bytes(normalized)


def doctype_end(content: bytes) -> int:
    """Find a DOCTYPE terminator outside quotes, comments, and its subset."""
    index = len(b"<!DOCTYPE")
    subset_depth = 0
    quote = 0
    while index < len(content):
        if not quote and content.startswith(b"<!--", index):
            comment_end = content.find(b"-->", index + 4)
            if comment_end < 0:
                return -1
            index = comment_end + 3
            continue
        if not quote and content.startswith(b"<?", index):
            instruction_end = content.find(b"?>", index + 2)
            if instruction_end < 0:
                return -1
            index = instruction_end + 2
            continue
        byte = content[index]
        if quote:
            if byte == quote:
                quote = 0
        elif byte in (ord('"'), ord("'")):
            quote = byte
        elif byte == ord("["):
            subset_depth += 1
        elif byte == ord("]") and subset_depth:
            subset_depth -= 1
        elif byte == ord(">") and subset_depth == 0:
            return index
        index += 1
    return -1


def require_no_diagnostic_payload(paths: list[str],
                                  contents: dict[str, bytes] | None = None) -> None:
    by_path = contents or {}
    rejected = [path for path in paths if forbidden_fixture_path(path, by_path.get(path, b""))]
    if rejected:
        raise Reject("diagnostic-payload-added:" + ",".join(rejected))


def added_paths(root: pathlib.Path, revision: str) -> list[dict[str, Any]]:
    raw = git(root, "diff", "--no-renames", "--diff-filter=A", "--name-only", "-z",
              BASELINE, revision, "--")
    paths = [item.decode("utf-8", "strict") for item in raw.split(b"\0") if item]
    entries = tree_entries(root, revision)
    for path in paths:
        entry = entries.get(path)
        if entry is None:
            raise Reject("added-path-missing-from-tree:" + path)
        oid, size, mode = entry
        if mode == "120000" or size > MAX_OUTPUT:
            raise Reject("added-path-content-unavailable:" + path)
        if phase24_admitted_fixture_path(path):
            # Repository fixture admission and package exclusion have separate
            # checks; this historical inventory reader records paths/sizes only.
            continue
        require_no_diagnostic_payload([path])
        content = git(root, "cat-file", "blob", oid, limit=MAX_OUTPUT)
        if len(content) != size:
            raise Reject("added-path-size-mismatch:" + path)
        require_no_diagnostic_payload([path], {path: content})
    return [{"path": path, "size_bytes": entries.get(path, ("", 0, ""))[1]} for path in paths]


def write_bounded_git_archive(root: pathlib.Path, revision: str, destination: pathlib.Path) -> None:
    try:
        process = subprocess.Popen(
            ["git", "--no-replace-objects", "archive", "--format=tar", revision], cwd=root,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env=git_environment())
    except OSError as error:
        raise Reject(f"source-archive-start-failed:{error.__class__.__name__}") from None
    written = [0]
    exceeded = threading.Event()
    write_errors: list[OSError] = []

    def drain() -> None:
        try:
            with destination.open("wb") as output:
                while chunk := process.stdout.read(64 * 1024):
                    if written[0] + len(chunk) > MAX_SOURCE_ARCHIVE_BYTES:
                        exceeded.set()
                    if not exceeded.is_set():
                        count = output.write(chunk)
                        if count != len(chunk):
                            raise OSError("short archive write")
                        written[0] += count
        except OSError as error:
            write_errors.append(error)
            exceeded.set()

    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    deadline = time.monotonic() + 30
    timed_out = False
    while process.poll() is None:
        if exceeded.is_set():
            try:
                process.kill()
            except OSError:
                pass
            break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
            try:
                process.kill()
            except OSError:
                pass
            break
        try:
            process.wait(timeout=min(0.05, remaining))
        except subprocess.TimeoutExpired:
            continue
    process.wait()
    reader.join(timeout=2)
    if reader.is_alive():
        process.stdout.close()
        raise Reject("source-archive-reader-stuck")
    if timed_out:
        raise Reject("source-archive-timeout")
    if exceeded.is_set():
        reason = "source-archive-size-limit" if not write_errors else "source-archive-write-failed"
        raise Reject(reason)
    if process.returncode != 0 or written[0] == 0:
        raise Reject("source-archive-command-failed")


def source_archive_configure_control(root: pathlib.Path, revision: str) -> None:
    """Ensure the default tests-enabled preset still configures from a Git source archive."""
    with tempfile.TemporaryDirectory(prefix="gbb-source-archive-configure-") as name:
        source = pathlib.Path(name) / "source"
        source.mkdir()
        archive_path = pathlib.Path(name) / "source.tar"
        write_bounded_git_archive(root, revision, archive_path)
        with tarfile.open(archive_path, mode="r:") as archive:
            for member in archive.getmembers():
                path = pathlib.PurePosixPath(member.name)
                if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
                    raise Reject("source-archive-member-path-invalid")
                target = source.joinpath(*path.parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    if member.size > MAX_OUTPUT:
                        raise Reject("source-archive-member-size-limit")
                    source_file = archive.extractfile(member)
                    if source_file is None:
                        raise Reject("source-archive-member-unreadable")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with source_file, target.open("wb") as output:
                        shutil.copyfileobj(source_file, output)
                elif member.issym() or member.islnk():
                    # Only phase-history aliases use Git symlinks; CMake configuration
                    # does not consume them, and the source archive must not need them.
                    continue
                else:
                    raise Reject("source-archive-member-type-invalid")
        if (source / ".git").exists():
            raise Reject("source-archive-unexpected-git-metadata")
        code, out, err = run(["cmake", "--preset", "phase1"], source, timeout=50,
                             operation="source-archive-configure")
        if code:
            detail = (out + err).decode("utf-8", "replace")[-700:]
            raise Reject(f"source-archive-configure-failed:{detail}")


def reviewed_archive_harness(root: pathlib.Path, revision: str = ARCHIVE_HARNESS_PIN,
                             digest: str = ARCHIVE_HARNESS_SHA256) -> bytes:
    try:
        raw = git(root, "show", f"{revision}:{ARCHIVE_HARNESS_PATH}", limit=MAX_BYTES)
    except Reject:
        raise Reject("source-package-review-pin-unavailable") from None
    if hashlib.sha256(raw).hexdigest() != digest:
        raise Reject("source-package-review-pin-digest-mismatch")
    return raw


def reviewed_notice_index(root: pathlib.Path) -> bytes:
    try:
        raw = git(root, "show", f"{NOTICE_INDEX_PIN}:THIRD_PARTY_NOTICES.md", limit=MAX_BYTES)
    except Reject:
        raise Reject("source-package-notice-index-pin-unavailable") from None
    if sha256(raw) != NOTICE_INDEX_SHA256:
        raise Reject("source-package-notice-index-pin-digest-mismatch")
    return raw


def d209_preserved_source(root: pathlib.Path, path: str) -> bytes:
    expected = D209_PRESERVED_SOURCE_SHA256.get(path)
    if expected is None:
        raise Reject(f"source-package-d209-path-unapproved:{path}")
    try:
        raw = git(root, "show", f"{V04_D209_ARCHIVE_REV}:{path}", limit=MAX_BYTES)
    except Reject:
        raise Reject(f"source-package-d209-source-unavailable:{path}") from None
    if sha256(raw) != expected:
        raise Reject(f"source-package-d209-source-digest-mismatch:{path}")
    return raw


def validate_preserved_path(path: str, raw: bytes | None, root: pathlib.Path) -> None:
    baseline = git(root, "show", f"{BASELINE}:{path}", limit=MAX_BYTES)
    if raw == baseline:
        return
    if path in D209_PRESERVED_SOURCE_SHA256 and raw == d209_preserved_source(root, path):
        return
    if path == "THIRD_PARTY_NOTICES.md" and raw == reviewed_notice_index(root):
        return
    if path == ARCHIVE_HARNESS_PATH and raw == reviewed_archive_harness(root):
        return
    if path == ARCHIVE_HARNESS_PATH and raw == reviewed_archive_harness(
            root, NOTICE_PATH_HARNESS_PIN, NOTICE_PATH_HARNESS_SHA256):
        return
    raise Reject(f"source-package-boundary-changed:{path}")


def validate_boundaries(snapshot: dict[str, bytes], root: pathlib.Path,
                        revision: str) -> list[dict[str, Any]]:
    validate_preserved(snapshot, root)
    added = added_paths(root, revision)
    entries = tree_entries(root, revision)
    # This is the historical Phase 22 inventory reader. Later Phase 24 fixture
    # admissions remain outside that result; their own admission and packaging
    # checks run through the fixture policy, while forbidden_fixture_path keeps
    # them out of product packages.
    if "tests/acid2/control.asm" not in entries:
        raise Reject("synthetic-control-source-missing")
    return added


def check_snapshot(snapshot: dict[str, bytes], revision: str, root: pathlib.Path,
                   build: pathlib.Path, complete_docs: bool) -> dict[str, Any]:
    metadata = validate_metadata(snapshot, revision, root)
    docs = validate_docs(snapshot, complete=complete_docs)
    validate_requirements(snapshot, root)
    validate_recovery_route(snapshot, root, revision)
    tests = validate_tests(snapshot, build)
    added = validate_boundaries(snapshot, root, revision)
    return {"metadata": metadata, "documentation_sections": docs,
            "configured_ctest_count": tests, "added_paths": added}


def validate_boundary(snapshot: dict[str, bytes]) -> dict[str, Any]:
    if any(path not in snapshot for path in BOUNDARY_PATHS):
        raise Reject("boundary-artifact-missing")
    state = decode(snapshot, ".planning/STATE.md")
    runtime = parse_json(snapshot[".planning/state.json"], "boundary-state-json")
    roadmap = decode(snapshot, ".planning/ROADMAP.md")
    config = parse_json(snapshot[".planning/config.json"], "boundary-config")
    continuation = decode(snapshot, BOUNDARY_PATHS[-1])
    requirement_defs, requirement_trace = requirement_parts(
        decode(snapshot, ".planning/REQUIREMENTS.md"))
    if (set(requirement_defs) != {"DIAG-01", "DIAG-02", "RIGHTS-01"}
            or requirement_trace != {"DIAG-01": "Phase 22|Pending",
                                     "DIAG-02": "Phase 22|Pending",
                                     "RIGHTS-01": "Phase 20|Pending"}):
        raise Reject("boundary-requirement-disposition-invalid")
    workflow = config.get("workflow")
    if not isinstance(workflow, dict) or workflow.get("auto_advance") is not False \
            or workflow.get("_auto_chain_active") is not False:
        raise Reject("boundary-auto-advance-enabled")
    if "Phase 22 is complete" not in state and "Phase GB-22 is complete" not in state:
        raise Reject("boundary-phase22-not-complete")
    if not all(item in state for item in ("DIAG-01", "DIAG-02", "RIGHTS-01")):
        raise Reject("boundary-requirements-not-retained")
    phases = runtime.get("phases") if isinstance(runtime, dict) else None
    if not isinstance(phases, list):
        raise Reject("boundary-runtime-state-phase-invalid")
    phase_status = {str(row.get("number")): row.get("status")
                    for row in phases if isinstance(row, dict)}
    if phase_status.get("22") != "complete" or phase_status.get("23") != "pending":
        raise Reject("boundary-runtime-state-phase-invalid")
    p22 = re.search(r"(?ms)^### Phase 22:.*?(?=^### Phase 23:|\Z)", roadmap)
    p23 = re.search(r"(?ms)^### Phase 23:.*?(?=^### Phase 24:|\Z)", roadmap)
    if not p22 or not p23:
        raise Reject("boundary-roadmap-phases-missing")
    if "complete" not in p22.group(0).casefold() or "unstarted" not in p23.group(0).casefold():
        raise Reject("boundary-roadmap-status-invalid")
    if "Qualified v0.4.0 Release" not in p23.group(0):
        raise Reject("boundary-phase23-title-invalid")
    if "/gsd-discuss-phase 23" not in state or "/gsd-discuss-phase 23" not in continuation:
        raise Reject("boundary-phase23-route-invalid")
    if "Phase 23" not in continuation or "Qualified v0.4.0 Release" not in continuation:
        raise Reject("boundary-continuation-route-invalid")
    if "/gsd-execute-phase 23" in continuation or "Phase 23 is complete" in continuation:
        raise Reject("boundary-phase23-already-executed")
    if any(gate not in continuation for gate in GATES):
        raise Reject("boundary-diagnostic-stop-not-preserved")
    return {"phase22": "complete", "phase23": "unstarted",
            "next_route": "/gsd-discuss-phase 23", "automatic_advance": False}


def load_boundary(root: pathlib.Path, revision: str) -> dict[str, bytes]:
    return load_snapshot(root, revision, BOUNDARY_PATHS)


def minimal_boundary(requirements: bytes | None = None) -> dict[str, bytes]:
    return {
        ".planning/STATE.md": (
            "Phase 22 is complete. DIAG-01 and DIAG-02 remain Pending; RIGHTS-01 remains Pending.\n"
            "Phase 23 — Qualified v0.4.0 Release: /gsd-discuss-phase 23\n"
        ).encode(),
        ".planning/state.json":
            b'{"phases":[{"number":"22","status":"complete"},{"number":"23","status":"pending"}]}',
        ".planning/ROADMAP.md": (
            "### Phase 22: Synthetic Composition and Diagnostic Gate Assessment\nStatus: Complete\n"
            "### Phase 23: Qualified v0.4.0 Release\nStatus: Unstarted\n"
        ).encode(),
        ".planning/REQUIREMENTS.md": requirements or (
            "- [ ] **DIAG-01**: Original diagnostic requirement.\n"
            "- [ ] **DIAG-02**: Original diagnostic requirement.\n"
            "- [ ] **RIGHTS-01**: Original rights requirement.\n"
            "| DIAG-01 | Phase 22 | Pending |\n"
            "| DIAG-02 | Phase 22 | Pending |\n"
            "| RIGHTS-01 | Phase 20 | Pending |\n"
        ).encode(),
        ".planning/config.json":
            b'{"workflow":{"auto_advance":false,"_auto_chain_active":false}}',
        BOUNDARY_PATHS[-1]: (
            "Phase 23 — Qualified v0.4.0 Release\nNext: /gsd-discuss-phase 23\n"
            + "\n".join(GATES) + "\n"
        ).encode(),
    }


def expect_reject(fn, reason: str, label: str) -> None:
    try:
        fn()
    except Reject as error:
        if str(error).startswith(reason):
            return
        raise Reject(f"control-wrong-reason:{label}:{error}") from None
    raise Reject(f"control-accepted-mutant:{label}")


def boundary_history_control(source_root: pathlib.Path) -> None:
    with tempfile.TemporaryDirectory(prefix="gbb-boundary-control-") as name:
        root = pathlib.Path(name)
        repo = root / "candidate"
        decoy = root / "decoy"
        repo.mkdir()
        decoy.mkdir()
        git(repo, "init", "-q")
        git(decoy, "init", "-q")
        git(decoy, "config", "user.name", "GabbaBoy Synthetic Decoy")
        git(decoy, "config", "user.email", "decoy@example.invalid")
        (decoy / "decoy.txt").write_text("decoy repository must remain unchanged\n", encoding="utf-8")
        git(decoy, "add", "decoy.txt")
        git(decoy, "commit", "-qm", "synthetic decoy")

        def decoy_state() -> tuple[bytes, bytes, bytes, str]:
            git_dir = pathlib.Path(git(decoy, "rev-parse", "--absolute-git-dir").decode(
                "utf-8", "strict").strip())
            refs = git(decoy, "for-each-ref", "--format=%(refname) %(objectname)")
            status = git(decoy, "status", "--porcelain=v1", "-z")
            try:
                index = (git_dir / "index").read_bytes()
            except OSError as error:
                raise Reject(f"self-test-decoy-index-unreadable:{error.__class__.__name__}") from None
            object_root = git_dir / "objects"
            object_payload = b"\0".join(
                path.relative_to(object_root).as_posix().encode("utf-8") + b"\0" + path.read_bytes()
                for path in sorted(object_root.rglob("*")) if path.is_file())
            return refs, status, index, hashlib.sha256(object_payload).hexdigest()

        original_decoy_state = decoy_state()
        hostile_global = root / "hostile-global-config"
        hostile_system = root / "hostile-system-config"
        hostile_global.write_text("[core]\n\tbare = true\n", encoding="utf-8")
        hostile_system.write_text("[core]\n\tbare = true\n", encoding="utf-8")
        hostile = {
            "GIT_DIR": str((decoy / ".git").resolve()),
            "GIT_WORK_TREE": str(repo.resolve()),
            "GIT_COMMON_DIR": str((decoy / ".git").resolve()),
            "GIT_INDEX_FILE": str((decoy / ".git/index").resolve()),
            "GIT_OBJECT_DIRECTORY": str((decoy / ".git/objects").resolve()),
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": str((decoy / ".git/objects").resolve()),
            "GIT_CONFIG_GLOBAL": str(hostile_global),
            "GIT_CONFIG_SYSTEM": str(hostile_system),
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.bare",
            "GIT_CONFIG_VALUE_0": "true",
            "GIT_NAMESPACE": "redirected",
            "GIT_PREFIX": "redirected/",
        }
        prior_environment = {key: os.environ.get(key) for key in hostile}
        try:
            os.environ.update(hostile)
            # This identity check happens before config/add/commit writes. If Git
            # inherits either hostile selector, it reports the decoy Git-dir.
            actual_git_dir = pathlib.Path(git(repo, "rev-parse", "--absolute-git-dir").decode(
                "utf-8", "strict").strip()).resolve()
            actual_worktree = pathlib.Path(git(repo, "rev-parse", "--show-toplevel").decode(
                "utf-8", "strict").strip()).resolve()
            if actual_git_dir != (repo / ".git").resolve() or actual_worktree != repo.resolve():
                raise Reject("self-test-hostile-git-context-redirected")

            git(repo, "config", "user.name", "GabbaBoy Synthetic Boundary")
            git(repo, "config", "user.email", "boundary@example.invalid")
            baseline_requirements = git(
                source_root, "show", f"{BASELINE}:{V04_ROOT_REQUIREMENTS}", limit=MAX_BYTES)
            for path, raw in minimal_boundary(baseline_requirements).items():
                target = repo.joinpath(*path.split("/"))
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            git(repo, "add", ".")
            git(repo, "commit", "-qm", "synthetic historical boundary")
            boundary = resolve_revision(repo, "HEAD")
            if decoy_state() != original_decoy_state:
                raise Reject("self-test-hostile-git-context-mutated-decoy")
            boundary_snapshot = load_boundary(repo, boundary)
            if validate_boundary(boundary_snapshot)["phase23"] != "unstarted":
                raise Reject("self-test-historical-boundary-invalid")
            validate_historical_requirements(boundary_snapshot, source_root, boundary,
                                             test_fixture_revision=boundary)

            # Install a same-type replacement commit that changes both a boundary
            # blob and the tree. Ordinary Git must select it; the production reader
            # must return the original commit's bytes and inventory.
            state_path = ".planning/STATE.md"
            original_state = boundary_snapshot[state_path]
            mutant_state = b"synthetic replacement state must not be selected\n"
            extra_path = ".planning/d217-replacement.md"
            state_file = root / "replacement-state"
            extra_file = root / "replacement-tree-entry"
            state_file.write_bytes(mutant_state)
            extra_file.write_bytes(b"replacement tree entry\n")
            state_blob = git(repo, "hash-object", "-w", str(state_file)).decode("ascii").strip()
            extra_blob = git(repo, "hash-object", "-w", str(extra_file)).decode("ascii").strip()
            git(repo, "read-tree", boundary)
            git(repo, "update-index", "--add", "--cacheinfo",
                "100644," + state_blob + "," + state_path,
                "--cacheinfo", "100644," + extra_blob + "," + extra_path)
            replacement_tree = git(repo, "write-tree").decode("ascii").strip()
            replacement_commit = git(repo, "-c", "user.name=GabbaBoy Replacement Control",
                                     "-c", "user.email=replacement@example.invalid", "commit-tree",
                                     replacement_tree, "-p", boundary, "-m", "replacement control").decode(
                                         "ascii").strip()
            git(repo, "read-tree", boundary)
            state_file.unlink()
            extra_file.unlink()
            git(repo, "replace", boundary, replacement_commit)
            ordinary_blob = subprocess.run(["git", "-C", str(repo), "show", f"{boundary}:{state_path}"],
                                           cwd=repo, env=git_environment(), stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, check=False)
            ordinary_tree = subprocess.run(["git", "-C", str(repo), "ls-tree", "-rz", "-r", boundary],
                                           cwd=repo, env=git_environment(), stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, check=False)
            if (ordinary_blob.returncode != 0 or ordinary_blob.stdout != mutant_state
                    or ordinary_tree.returncode != 0 or extra_path.encode() not in ordinary_tree.stdout):
                raise Reject("replacement-ref control did not prove ordinary Git selected mutant boundary data")
            if (git(repo, "show", f"{boundary}:{state_path}") != original_state
                    or extra_path in tree_entries(repo, boundary)
                    or load_boundary(repo, boundary) != boundary_snapshot):
                raise Reject("production diagnostic Git readers followed a replacement commit")
            state = repo / ".planning/STATE.md"
            state.write_text("Phase 23 is complete.\n", encoding="utf-8")
            git(repo, "add", ".planning/STATE.md")
            git(repo, "commit", "-qm", "synthetic later route")
            later = resolve_revision(repo, "HEAD")
            if later == boundary or git(repo, "rev-parse", "--verify", "HEAD^").decode(
                    "ascii", "strict").strip() != boundary:
                raise Reject("self-test-candidate-head-transition-invalid")
            if decoy_state() != original_decoy_state:
                raise Reject("self-test-hostile-git-context-mutated-decoy")
            expect_reject(lambda: validate_historical_requirements(
                load_boundary(repo, later), source_root, later, test_fixture_revision=boundary),
                "historical-requirements-test-revision-invalid", "synthetic-later-revision")
            expect_reject(lambda: validate_boundary(load_boundary(repo, resolve_revision(repo, "HEAD"))),
                          "boundary-phase22-not-complete", "later-head-route")
            if validate_boundary(load_boundary(repo, boundary))["phase23"] != "unstarted":
                raise Reject("self-test-historical-boundary-rejected")
        finally:
            for key, value in prior_environment.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


def validate_inventory_shape(record: dict[str, Any]) -> None:
    cases = record.get("cases")
    if not isinstance(cases, list) or len(cases) != 513:
        raise Reject("inventory-case-count-mismatch")
    names = [row.get("name") for row in cases if isinstance(row, dict)]
    if (len(names) != 513 or len(set(names)) != 513
            or names != sorted(names, key=lambda value: value.encode("utf-8"))):
        raise Reject("inventory-roster-identity-mismatch")
    for row in cases:
        if row.get("model_applicability", {}).get("status") != "unresolved":
            raise Reject("model-applicability-mutated")
    if record.get("accounting", {}).get("executed_names") != []:
        raise Reject("accounting-mutated")


def validate_gate_shape(record: dict[str, Any]) -> None:
    unresolved = [row.get("id") for row in record.get("required_gates", [])
                  if row.get("status") == "unresolved"]
    if tuple(unresolved) != GATES:
        raise Reject("gate-set-mutated")


def run_admission_mutant(snapshot: dict[str, bytes], kind: str,
                         mutate, expected: str, label: str) -> None:
    with tempfile.TemporaryDirectory(prefix="gbb-admission-mutant-") as name:
        root = snapshot_root({path: snapshot[path] for path in (CHECKER, ASSESSMENT, INVENTORY)},
                             pathlib.Path(name))
        target = root / (ASSESSMENT if kind == "assessment" else INVENTORY)
        record = parse_json(target.read_bytes(), f"control-{label}")
        mutate(record)
        target.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
        code, out, err = run(
            [sys.executable, "-I", str(root / CHECKER), "--check-assessment",
             "--repo-root", str(root), "--source-revision", "a" * 40],
            root,
        )
        output = (out + err).decode("utf-8", "replace")
        if code == 0 or expected not in output:
            raise Reject(f"control-wrong-reason:{label}:{output[:250]}")


def validate_preserved(snapshot: dict[str, bytes], root: pathlib.Path) -> None:
    for path in PRESERVED:
        validate_preserved_path(path, snapshot.get(path), root)


def diagnostic_sanitization_control(root: pathlib.Path) -> None:
    windows_root = r"C:\Users\runneradmin\AppData\Local\Temp\gbb-diagnostic-probe"
    c1_prefix = "C1_PREFIX_KEEP"
    c1_suffix = "C1_SUFFIX_KEEP"
    raw = (f"\x1b[31mconfigure failed at {root}/project\x1b[0m\t"
           f"{windows_root}\\project\n"
           "\x1b]0;synthetic-secret-title\x1b\\\x1b]0;synthetic-bel-title\x07"
           f"{pathlib.Path.home()}/home-project {c1_prefix}"
           "\u009d0;synthetic-c1-title\u009c"
           f"{c1_suffix}" + "x" * 900).encode("utf-8")
    roots = ((root, "<temp>"), (windows_root, "<windows-temp>"),
             (pathlib.Path.home(), "<home>"))

    def assert_sanitized() -> None:
        detail = sanitized_diagnostic(raw, roots)
        if (len(detail) > 700 or "\x1b" in detail or "\n" in detail or "\t" in detail
                or str(root) in detail or windows_root in detail
                or str(pathlib.Path.home()) in detail
                or "synthetic-secret-title" in detail or "synthetic-bel-title" in detail
                or "0;synthetic-c1-title" in detail or "\u009d" in detail or "\u009c" in detail
                or c1_prefix not in detail or c1_suffix not in detail
                or "<temp>" not in detail or "<windows-temp>" not in detail or "<home>" not in detail
                or any(ord(char) < 0x20 or 0x7f <= ord(char) <= 0x9f for char in detail)):
            raise Reject("diagnostic-sanitization-control-failed")

    assert_sanitized()
    original_c1_osc_escape = C1_OSC_ESCAPE
    try:
        globals()["C1_OSC_ESCAPE"] = re.compile(r"(?!)")
        try:
            assert_sanitized()
        except Reject as exc:
            if str(exc) != "diagnostic-sanitization-control-failed":
                raise Reject("diagnostic-sanitization-mutation-control-failed") from exc
        else:
            raise Reject("diagnostic-sanitization-mutation-control-failed")
    finally:
        globals()["C1_OSC_ESCAPE"] = original_c1_osc_escape


def cmake_path_serialization_controls(root: pathlib.Path) -> None:
    cmake = shutil.which("cmake")
    if not cmake:
        raise Reject("cmake-unavailable")
    synthetic_executable = r"C:\Program Files\CMake\bin\cmake.exe"

    def configure(label: str, executable: str) -> tuple[int, bytes, bytes]:
        project = root / label
        project.mkdir()
        (project / "CMakeLists.txt").write_text(
            "cmake_minimum_required(VERSION 3.20)\nproject(PathProbe NONE)\n"
            f'add_test(NAME path_probe COMMAND "{executable}" -E true)\n',
            encoding="utf-8",
        )
        return run([cmake, "-S", str(project), "-B", str(project / "build")], project,
                   timeout=15, operation="self-test-cmake-path-probe")

    raw_code, raw_out, raw_err = configure("raw-windows-cmake-path", synthetic_executable)
    raw_detail = sanitized_diagnostic(raw_out + raw_err,
                                      ((root, "<temp>"), (pathlib.Path.home(), "<home>")))
    if raw_code == 0 or "invalid character escape" not in raw_detail.casefold():
        raise Reject("cmake-path-serialization-negative-control-failed")
    portable = cmake_path_literal(synthetic_executable)
    if "\\" in portable:
        raise Reject("cmake-path-serialization-helper-control-failed")
    portable_code, portable_out, portable_err = configure("portable-windows-cmake-path", portable)
    if portable_code != 0:
        detail = sanitized_diagnostic(portable_out + portable_err,
                                      ((root, "<temp>"), (pathlib.Path.home(), "<home>")))
        raise Reject(f"cmake-path-serialization-positive-control-failed:{detail}")


def self_test(snapshot: dict[str, bytes], controls: bool,
              revision: str, repo: pathlib.Path) -> None:
    inventory = parse_json(snapshot[INVENTORY], "self-test-inventory")
    if len(inventory.get("cases", [])) != 513:
        raise Reject("self-test-positive-inventory-failed")
    validate_metadata(snapshot, revision, repo)
    validate_docs(snapshot, complete=True)
    validate_requirements(snapshot, repo)
    validate_recovery_route(snapshot, repo, revision)
    if not controls:
        print("diagnostic evidence self-test pass metadata=513 gates=7")
        return
    mutants = (
        (lambda r: r["cases"].pop(), "inventory-case-count-mismatch", "roster-drop"),
        (lambda r: r["cases"][1].update(name=r["cases"][0]["name"]), "inventory-roster-identity-mismatch", "roster-duplicate"),
        (lambda r: r["cases"][1].update(name="substituted-name"), "inventory-roster-identity-mismatch", "roster-substitution"),
        (lambda r: r["cases"][0]["model_applicability"].update(status="supported"), "model-applicability-mutated", "wrong-model"),
        (lambda r: r["accounting"].update(executed_names=["fake"]), "accounting-mutated", "fake-execution"),
    )
    for mutate, reason, label in mutants:
        value = json.loads(json.dumps(inventory))
        mutate(value)
        expect_reject(lambda item=value: validate_inventory_shape(item), reason, label)
    run_admission_mutant(
        snapshot, "inventory",
        lambda record: _mutate_first_case_identity(record),
        "diagnostic-inventory-projection-pin-mismatch", "roster-substitution",
    )
    run_admission_mutant(
        snapshot, "inventory",
        lambda record: _mutate_first_rom_identity(record),
        "diagnostic-inventory-projection-pin-mismatch", "roster-identity",
    )
    run_admission_mutant(
        snapshot, "inventory",
        lambda record: _drop_case_with_recount(record),
        "diagnostic-inventory-case-count-mismatch", "coordinated-roster-drop",
    )
    run_admission_mutant(
        snapshot, "inventory",
        lambda record: record["accounting"].update(executed_names=[record["cases"][0]["name"]]),
        "diagnostic-inventory-eligibility-accounting-mismatch", "fake-real-execution",
    )
    run_admission_mutant(
        snapshot, "inventory",
        lambda record: record["accounting"].update(
            admitted_eligible_names=[record["accounting"]["protocol_candidate_names"][0]]),
        "diagnostic-inventory-eligibility-accounting-mismatch", "unsupported-eligibility",
    )
    run_admission_mutant(
        snapshot, "inventory",
        lambda record: record["cases"][0]["model_applicability"].update(status="supported"),
        "diagnostic-inventory-applicability-mutated", "wrong-model-applicability",
    )
    run_admission_mutant(
        snapshot, "assessment",
        lambda record: _mutate_component_rights(record),
        "diagnostic-assessment-positive-scope-incomplete:gbmicrotest_prebuilt_roms",
        "unsupported-rights-upgrade",
    )
    assessment = parse_json(snapshot[ASSESSMENT], "self-test-assessment")
    value = json.loads(json.dumps(assessment))
    next(row for row in value["required_gates"] if row["id"] == GATES[0])["status"] = "supported"
    expect_reject(lambda: validate_gate_shape(value), "gate-set-mutated", "gate-authorization")
    if V04_ARCHIVED_REQUIREMENTS in snapshot:
        plan_dir = V04_RECOVERY_PLAN.rsplit("/", 1)[0] + "/"
        plan_paths = sorted(path for path in tree_entries(repo, revision)
                            if path.startswith(plan_dir)
                            and re.match(r"^24-\d[^/\\]*-PLAN[^/\\]*\.md$",
                                         path.rsplit("/", 1)[-1], re.IGNORECASE))
        missing_archive = dict(snapshot)
        missing_archive.pop(V04_ARCHIVED_REQUIREMENTS)
        expect_reject(lambda: validate_requirements(missing_archive, repo),
                      "source-archive-pair-invalid", "missing-archive-source")
        paired_archive_removal = dict(snapshot)
        paired_archive_removal.pop(V04_ARCHIVED_REQUIREMENTS)
        paired_archive_removal.pop(V04_ARCHIVED_ROADMAP)
        paired_archive_removal[V04_ROOT_REQUIREMENTS] = git(
            repo, "show", f"{BASELINE}:{V04_ROOT_REQUIREMENTS}", limit=MAX_BYTES)
        expect_reject(lambda: validate_requirements(paired_archive_removal, repo),
                      "source-archive-pair-required", "paired-archive-removal-with-restored-tracker")
        current_entries = tree_entries(repo, revision)
        baseline_entries = tree_entries(repo, BASELINE)
        paired_entries = dict(current_entries)
        paired_entries.pop(V04_ARCHIVED_REQUIREMENTS)
        paired_entries.pop(V04_ARCHIVED_ROADMAP)
        paired_entries[V04_ROOT_REQUIREMENTS] = baseline_entries[V04_ROOT_REQUIREMENTS]
        expect_reject(lambda: _current_snapshot_paths(paired_entries),
                      "source-archive-pair-required", "current-selector-paired-archive-removal")
        route_without_archives = dict(snapshot)
        route_without_archives.pop(V04_ARCHIVED_REQUIREMENTS)
        route_without_archives.pop(V04_ARCHIVED_ROADMAP)
        expect_reject(lambda: validate_recovery_route(route_without_archives, repo, revision),
                      "source-archive-pair-required", "route-validated-without-archive-pair")
        changed_route = dict(snapshot)
        roadmap = changed_route[V04_ROOT_ROADMAP]
        recovery_marker = b"## Recovery Phase"
        recovery_start = roadmap.find(recovery_marker)
        if recovery_start < 0:
            raise Reject("self-test-recovery-route-marker-missing")
        changed_route[V04_ROOT_ROADMAP] = (
            roadmap[:recovery_start]
            + roadmap[recovery_start:].replace(b"D-209", b"D-208")
        )
        expect_reject(lambda: validate_recovery_route(changed_route, repo, revision),
                      "recovery-route-content-invalid", "mutated-recovery-route-contract")
        for label, old, new, reason in (
            ("altered-archived-criterion", b"shared game-acceptance runner",
             b"changed game-acceptance runner", f"archived-source-mismatch:{V04_ARCHIVED_REQUIREMENTS}"),
            ("altered-archived-owner", b"| GAME-01 | Phase 21 | Complete |",
             b"| GAME-01 | Phase 20 | Complete |", f"archived-source-mismatch:{V04_ARCHIVED_REQUIREMENTS}"),
            ("altered-archived-status", b"| FIXT-01 | Phase 21 | Pending |",
             b"| FIXT-01 | Phase 21 | Complete |", f"archived-source-mismatch:{V04_ARCHIVED_REQUIREMENTS}"),
        ):
            changed = dict(snapshot)
            changed[V04_ARCHIVED_REQUIREMENTS] = changed[V04_ARCHIVED_REQUIREMENTS].replace(old, new, 1)
            if changed[V04_ARCHIVED_REQUIREMENTS] == snapshot[V04_ARCHIVED_REQUIREMENTS]:
                raise Reject(f"self-test-archive-mutant-inactive:{label}")
            expect_reject(lambda item=changed: validate_requirements(item, repo), reason, label)
        changed_roadmap = dict(snapshot)
        changed_roadmap[V04_ARCHIVED_ROADMAP] = changed_roadmap[V04_ARCHIVED_ROADMAP].replace(
            b"Owner-directed closeout", b"Altered closeout", 1)
        expect_reject(lambda: validate_requirements(changed_roadmap, repo),
                      f"archived-source-mismatch:{V04_ARCHIVED_ROADMAP}", "altered-archived-roadmap")
        restored_root = dict(snapshot)
        restored_root[V04_ROOT_REQUIREMENTS] = b"# restored active tracker\n"
        expect_reject(lambda: validate_requirements(restored_root, repo),
                      "active-root-requirements-restored", "restored-active-requirements")
        archived_only = dict(snapshot)
        archived_only[V04_ROOT_ROADMAP] = snapshot[V04_ARCHIVED_ROADMAP]
        expect_reject(lambda: validate_recovery_contract(archived_only, plan_paths),
                      "recovery-route-section-invalid", "archive-only-route")
        expect_reject(lambda: validate_recovery_contract(
            snapshot, [*plan_paths, V04_RECOVERY_PLAN.replace("24-01", "24-02")]),
            "recovery-plan-set-invalid", "extra-recovery-plan")
        validate_recovery_contract(snapshot, plan_paths)
        missing_boundary_claim = dict(snapshot)
        boundary_claim_bytes = b"archived v0.4 owners and dispositions remain authoritative"
        if boundary_claim_bytes not in missing_boundary_claim[V04_RECOVERY_PLAN]:
            raise Reject("self-test-recovery-boundary-claim-inactive")
        missing_boundary_claim[V04_RECOVERY_PLAN] = missing_boundary_claim[V04_RECOVERY_PLAN].replace(
            boundary_claim_bytes, b"archived v0.4 ownership and disposition claim omitted", 1)
        expect_reject(lambda: validate_recovery_contract(missing_boundary_claim, plan_paths),
                      "recovery-plan-boundary-invalid", "missing-archived-owner-boundary-claim")
    historical_requirement = load_snapshot(repo, BASELINE, (V04_ROOT_REQUIREMENTS,))
    validate_historical_requirements(historical_requirement, repo, BASELINE)
    expect_reject(lambda: validate_requirements(historical_requirement, repo),
                  "source-archive-pair-required", "current-mode-rejects-historical-tracker")
    expect_reject(lambda: validate_historical_requirements(historical_requirement, repo, "f" * 40),
                  "historical-requirements-revision-unapproved", "unapproved-historical-revision")
    historical_requirement[V04_ROOT_REQUIREMENTS] = historical_requirement[V04_ROOT_REQUIREMENTS].replace(
        b"**DIAG-01**", b"**DIAG-01 completed**", 1)
    expect_reject(lambda: validate_historical_requirements(historical_requirement, repo, BASELINE),
                  "requirement-definition-changed", "historical-requirement-completion")
    cmake = dict(snapshot)
    cmake["tests/CMakeLists.txt"] = re.sub(
        rb"(?m)^add_test\(NAME phase22_evidence_controls\b[^\n]*\n?", b"",
        snapshot["tests/CMakeLists.txt"], count=1)
    expect_reject(lambda: validate_test_text(cmake), "ctest-cmake-membership-invalid", "missing-ctest")
    cmake_duplicate = dict(snapshot)
    cmake_duplicate["tests/CMakeLists.txt"] += (
        b"\nadd_test(NAME phase22_evidence_controls COMMAND cmake -E true)\n"
    )
    expect_reject(lambda: validate_test_text(cmake_duplicate),
                  "ctest-cmake-membership-invalid", "duplicate-ctest")
    expected_missing = dict(snapshot)
    expected_missing["tests/expected-tests.txt"] = re.sub(
        rb"(?m)^phase22_evidence_controls\n", b"",
        snapshot["tests/expected-tests.txt"], count=1)
    expect_reject(lambda: validate_test_text(expected_missing),
                  "ctest-inventory-membership-invalid", "missing-expected-test")
    expected_duplicate = dict(snapshot)
    expected_duplicate["tests/expected-tests.txt"] += b"phase22_evidence_controls\n"
    expect_reject(lambda: validate_test_text(expected_duplicate),
                  "ctest-inventory-membership-invalid", "duplicate-expected-test")
    with tempfile.TemporaryDirectory(prefix="gbb-bounded-process-") as name:
        temporary = pathlib.Path(name)
        diagnostic_sanitization_control(temporary)
        cmake_path_serialization_controls(temporary)
        expect_reject(
            lambda: run([sys.executable, "-I", "-c", "import sys; sys.stdout.write('x' * 4096)"],
                        temporary, limit=64),
            "subprocess-output-limit", "bounded-subprocess-output")
        expect_reject(
            lambda: run([sys.executable, "-I", "-c", "import time; time.sleep(2)"],
                        temporary, timeout=0.1, operation="self-test-slow-child"),
            "subprocess-timeout:self-test-slow-child", "bounded-subprocess-timeout")
    expect_reject(lambda: require_no_diagnostic_payload(
        ["fixtures/acid2/diagnostics.tar"]),
        "diagnostic-payload-added", "fixture-path")
    if (not phase24_admitted_fixture_path("fixtures/acid2/manifest.json")
            or not phase24_admitted_fixture_path("fixtures/gbmicrotest/manifest.json")
            or phase24_admitted_fixture_path("fixtures/unreviewed/manifest.json")):
        raise Reject("self-test-phase24-fixture-boundary")
    expect_reject(lambda: require_no_diagnostic_payload(
        ["assets/renamed-control.gb"]),
        "diagnostic-payload-added", "renamed-rom-path")
    expect_reject(lambda: require_no_diagnostic_payload(
        ["misc/unrelated-data.zip"]),
        "diagnostic-payload-added", "renamed-archive-path")
    for path, control in (
        ("assets/renamed-reference.webp", "renamed-webp-reference"),
        ("assets/renamed-reference.svg", "renamed-svg-reference"),
        ("assets/reference.rar", "renamed-rar-archive"),
        ("assets/reference.zst", "renamed-zstd-archive"),
        ("assets/reference.dat", "renamed-data-payload"),
    ):
        expect_reject(lambda path=path: require_no_diagnostic_payload([path]),
                      "diagnostic-payload-added", control)
    hidden_rom = bytes(0x104) + GB_ROM_LOGO + bytes(64)
    expect_reject(lambda: require_no_diagnostic_payload(
        ["assets/notes.md"], {"assets/notes.md": hidden_rom}),
        "diagnostic-payload-added", "extension-renamed-rom-content")
    hidden_image = b"\x89PNG\r\n\x1a\nsynthetic-image"
    expect_reject(lambda: require_no_diagnostic_payload(
        ["assets/reference"], {"assets/reference": hidden_image}),
        "diagnostic-payload-added", "extensionless-image-content")
    hidden_svg = b"<?xml version='1.0'?><svg xmlns='http://www.w3.org/2000/svg'/>"
    expect_reject(lambda: require_no_diagnostic_payload(
        ["assets/reference.md"], {"assets/reference.md": hidden_svg}),
        "diagnostic-payload-added", "renamed-svg-content")
    long_svg = b"<!--" + b"x" * 8192 + b"--><svg xmlns='http://www.w3.org/2000/svg'/>"
    expect_reject(lambda: require_no_diagnostic_payload(
        ["assets/reference.md"], {"assets/reference.md": long_svg}),
        "diagnostic-payload-added", "long-prefix-renamed-svg-content")
    namespaced_svg = b"<svg:svg xmlns:svg='http://www.w3.org/2000/svg'/>"
    expect_reject(lambda: require_no_diagnostic_payload(
        ["assets/reference.md"], {"assets/reference.md": namespaced_svg}),
        "diagnostic-payload-added", "namespaced-svg-content")
    doctype_svg = (b"<!DOCTYPE svg [<!ENTITY marker 'value > value'>]><svg xmlns='http://www.w3.org/2000/svg'>"
                   b"<text>&marker;</text></svg>")
    expect_reject(lambda: require_no_diagnostic_payload(
        ["assets/reference.md"], {"assets/reference.md": doctype_svg}),
        "diagnostic-payload-added", "doctype-subset-svg-content")
    for endian, bom, control in (("utf-16-le", b"\xff\xfe", "utf16le-svg-content"),
                                 ("utf-16-be", b"\xfe\xff", "utf16be-svg-content")):
        encoded_svg = bom + "<?xml version='1.0'?><svg:svg xmlns:svg='urn:svg'/>".encode(endian)
        expect_reject(lambda encoded_svg=encoded_svg: require_no_diagnostic_payload(
            ["assets/reference.md"], {"assets/reference.md": encoded_svg}),
            "diagnostic-payload-added", control)
    if forbidden_fixture_path("tests/scripts/control.py", b"svg_example = b'<svg xmlns=\\\"urn:example\\\"/>'"):
        raise Reject("self-test-false-svg-positive")
    for brand, control in ((b"avif", "extensionless-avif-content"),
                           (b"heic", "extensionless-heic-content")):
        ftyp_image = b"\x00\x00\x00\x18ftyp" + brand + b"\x00\x00\x00\x00"
        expect_reject(lambda ftyp_image=ftyp_image: require_no_diagnostic_payload(
            ["assets/reference.md"], {"assets/reference.md": ftyp_image}),
            "diagnostic-payload-added", control)
    hidden_icon = b"\x00\x00\x01\x00\x01\x00\x10\x10"
    expect_reject(lambda: require_no_diagnostic_payload(
        ["assets/reference.md"], {"assets/reference.md": hidden_icon}),
        "diagnostic-payload-added", "renamed-ico-content")
    docs_mutations = (
        ("docs/diagnostic-evidence.md", b"No real diagnostic result exists",
         b"No real diagnostic result exists. Real diagnostic result passed.",
         "documentation-claim-overstated:diagnostic-evidence:real diagnostic result passed",
         "real-pass-claim"),
        ("docs/diagnostic-evidence.md",
         b"requires new source-backed evidence and a separately selected scope.",
         b"requires new source-backed evidence and a separately selected scope. License prohibits use.",
         "documentation-claim-overstated:diagnostic-evidence:license prohibits use",
         "license-prohibition-claim"),
        ("docs/cgb-profile.md", b"DIAG-01 and DIAG-02 remain Pending",
         b"DIAG-01 and DIAG-02 remain Pending. DIAG-01 is complete.",
         "documentation-claim-overstated:cgb-profile:DIAG-01 is complete",
         "requirement-completion-claim"),
    )
    for path, old, new, reason, label in docs_mutations:
        doc = dict(snapshot)
        if old not in doc[path]:
            raise Reject(f"self-test-document-anchor-missing:{label}")
        doc[path] = doc[path].replace(old, new, 1)
        expect_reject(lambda candidate=doc: validate_docs(candidate, complete=True),
                      reason, label)
    preserved_baseline = {path: git(repo, "show", f"{BASELINE}:{path}", limit=MAX_BYTES)
                          for path in PRESERVED}
    validate_preserved(preserved_baseline, repo)
    reviewed = dict(preserved_baseline)
    reviewed[ARCHIVE_HARNESS_PATH] = reviewed_archive_harness(repo)
    validate_preserved(reviewed, repo)
    notice_path_reviewed = dict(reviewed)
    notice_path_reviewed[ARCHIVE_HARNESS_PATH] = reviewed_archive_harness(
        repo, NOTICE_PATH_HARNESS_PIN, NOTICE_PATH_HARNESS_SHA256)
    validate_preserved(notice_path_reviewed, repo)
    notice_index_reviewed = dict(notice_path_reviewed)
    notice_index_reviewed["THIRD_PARTY_NOTICES.md"] = reviewed_notice_index(repo)
    validate_preserved(notice_index_reviewed, repo)
    notice_index_mutated = dict(notice_index_reviewed)
    notice_index_mutated["THIRD_PARTY_NOTICES.md"] += b"\nmutated\n"
    expect_reject(lambda: validate_preserved(notice_index_mutated, repo),
                  "source-package-boundary-changed:THIRD_PARTY_NOTICES.md",
                  "mutated-reviewed-notice-index")
    for path in sorted(D209_PRESERVED_SOURCE_SHA256):
        d209_source_reviewed = dict(notice_path_reviewed)
        d209_source_reviewed[path] = d209_preserved_source(repo, path)
        validate_preserved(d209_source_reviewed, repo)
        d209_source_mutated = dict(d209_source_reviewed)
        d209_source_mutated[path] += b"\nmutated\n"
        expect_reject(lambda item=d209_source_mutated: validate_preserved(item, repo),
                      f"source-package-boundary-changed:{path}",
                      f"mutated-d209-source:{path}")
    notice_path_mutated = dict(notice_path_reviewed)
    notice_path_mutated[ARCHIVE_HARNESS_PATH] += b"\nmutated\n"
    expect_reject(lambda: validate_preserved(notice_path_mutated, repo),
                  f"source-package-boundary-changed:{ARCHIVE_HARNESS_PATH}",
                  "mutated-notice-path-harness")
    for path in PRESERVED:
        changed = dict(reviewed)
        changed[path] += b"\nmutated\n"
        try:
            validate_preserved(changed, repo)
        except Reject as error:
            if str(error) != f"source-package-boundary-changed:{path}":
                raise Reject(f"control-wrong-reason:preserved-boundary:{path}:{error}") from None
        else:
            raise Reject(f"control-accepted-mutant:preserved-boundary:{path}")
    expect_reject(lambda: reviewed_archive_harness(repo, revision="0" * 40),
                  "source-package-review-pin-unavailable", "unavailable-harness-pin")
    expect_reject(lambda: reviewed_archive_harness(repo, digest="0" * 64),
                  "source-package-review-pin-digest-mismatch", "mismatched-harness-pin")
    expect_reject(lambda: reviewed_archive_harness(
        repo, revision="0" * 40, digest=NOTICE_PATH_HARNESS_SHA256),
        "source-package-review-pin-unavailable", "unavailable-notice-path-harness-pin")
    expect_reject(lambda: reviewed_archive_harness(
        repo, revision=NOTICE_PATH_HARNESS_PIN, digest="0" * 64),
        "source-package-review-pin-digest-mismatch", "mismatched-notice-path-harness-pin")
    boundary = minimal_boundary()
    value = dict(boundary)
    value[BOUNDARY_PATHS[-1]] = value[BOUNDARY_PATHS[-1]].replace(
        b"/gsd-discuss-phase 23", b"/gsd-execute-phase 23")
    expect_reject(lambda: validate_boundary(value), "boundary-phase23-route-invalid", "wrong-route")
    value = dict(boundary)
    value[".planning/REQUIREMENTS.md"] = value[".planning/REQUIREMENTS.md"].replace(
        b"DIAG-01 | Phase 22 | Pending", b"DIAG-01 | Phase 22 | Complete")
    expect_reject(lambda: validate_boundary(value), "boundary-requirement-disposition-invalid",
                  "boundary-requirement-completion")
    requirement = load_snapshot(repo, BASELINE, (V04_ROOT_REQUIREMENTS,))
    validate_historical_requirements(requirement, repo, BASELINE)
    validate_boundary_revision(PHASE22_BOUNDARY_REVISION)
    expect_reject(lambda: validate_boundary_revision(BASELINE),
                  "boundary-revision-unapproved", "unapproved-boundary-revision")
    requirement[V04_ROOT_REQUIREMENTS] = requirement[V04_ROOT_REQUIREMENTS].replace(
        b"**DIAG-01**", b"**DIAG-01 changed**", 1)
    expect_reject(lambda: validate_historical_requirements(requirement, pathlib.Path.cwd(), BASELINE),
                  "requirement-definition-changed", "boundary-requirement-definition")
    value = dict(boundary)
    value[".planning/config.json"] = value[".planning/config.json"].replace(
        b'"_auto_chain_active":false', b'"_auto_chain_active":true')
    expect_reject(lambda: validate_boundary(value), "boundary-auto-advance-enabled", "auto-flag")
    boundary_history_control(repo)
    source_archive_configure_control(repo, revision)
    print("diagnostic evidence controls pass positives=1 rejected_controls=passed boundary=immutable "
          "source_archive=passed")


def _mutate_first_case_identity(record: dict[str, Any]) -> None:
    cases = record["cases"]
    for index in range(len(cases) - 1, -1, -1):
        case = cases[index]
        name = case["name"] + "-mutant"
        if (case["protocol"]["kind"] != "shared-verdict-macros"
                or any(item["name"] == name for item in cases)
                or (index + 1 < len(cases) and name >= cases[index + 1]["name"])):
            continue
        case["name"] = name
        case["source"]["path"] = f"tests/{name}.s"
        case["prebuilt_rom"]["path"] = f"bin/{name}.gb"
        return
    raise Reject("self-test-roster-mutant-unavailable")


def _mutate_first_rom_identity(record: dict[str, Any]) -> None:
    record["cases"][0]["prebuilt_rom"]["git_blob_sha1"] = "a" * 40


def _drop_case_with_recount(record: dict[str, Any]) -> None:
    removed = record["cases"].pop(0)
    record["counts"]["named_cases"] = 512
    record["counts"]["initial_no_protocol_exclusions"] = 30
    record["accounting"]["excluded_names"].remove(removed["name"])


def _mutate_component_rights(record: dict[str, Any]) -> None:
    component = next(row for row in record["components"]
                     if row["id"] == "gbmicrotest_prebuilt_roms")
    component["status"] = "supported"


def run_check(args: argparse.Namespace) -> int:
    if args.repo_root is None or args.source_revision is None:
        raise Reject("check-requires-repo-root-and-source-revision")
    root = args.repo_root.resolve(strict=True)
    revision = resolve_revision(root, args.source_revision)
    snapshot = load_snapshot(root, revision)
    build = (args.build_dir or root / "build").resolve(strict=True)
    result = check_snapshot(snapshot, revision, root, build, complete_docs=True)
    if args.write_evidence:
        if args.write_evidence.is_absolute():
            raise Reject("evidence-path-must-be-repository-relative")
        output = root / args.write_evidence
        if root not in output.resolve().parents:
            raise Reject("evidence-path-escapes-repository")
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "gabbaboy-diagnostic-evidence-v1",
            "source_revision": revision,
            "snapshot_sha256": {path: sha256(raw) for path, raw in sorted(snapshot.items())},
            "assessment": result,
        }
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checker_id = result["metadata"]["assessment_checker_sha256"]
    print(f"diagnostic evidence pass source={revision} assessment=blocked cases=513 "
          f"unresolved_gates=7 admitted=0 executed=0 assessment_checker_sha256={checker_id}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--self-test-controls", action="store_true")
    modes.add_argument("--check-boundary", action="store_true")
    parser.add_argument("--repo-root", type=pathlib.Path)
    parser.add_argument("--source-revision")
    parser.add_argument("--boundary-revision")
    parser.add_argument("--build-dir", type=pathlib.Path)
    parser.add_argument("--write-evidence", type=pathlib.Path)
    args = parser.parse_args(argv)
    try:
        if args.check_boundary:
            if args.repo_root is None or args.source_revision is None or args.boundary_revision is None:
                raise Reject("boundary-requires-source-and-boundary-revisions")
            root = args.repo_root.resolve(strict=True)
            resolve_revision(root, args.source_revision)
            validate_boundary_revision(args.boundary_revision)
            boundary = resolve_revision(root, args.boundary_revision)
            boundary_snapshot = load_boundary(root, boundary)
            validate_boundary(boundary_snapshot)
            validate_historical_requirements(boundary_snapshot, root, boundary)
            print(f"diagnostic boundary pass source={boundary} phase22=complete phase23=unstarted "
                  "next=/gsd-discuss-phase-23 auto_advance=false")
            return 0
        if args.self_test or args.self_test_controls:
            if args.repo_root is None or args.source_revision is None:
                raise Reject("self-test-requires-source-and-repo-root")
            root = args.repo_root.resolve(strict=True)
            revision = resolve_revision(root, args.source_revision)
            self_test(load_snapshot(root, revision), args.self_test_controls, revision, root)
            return 0
        return run_check(args)
    except (Reject, OSError, UnicodeError, ValueError) as error:
        print(f"diagnostic evidence refused: {error}", file=sys.stderr)
        return 2


def load_boundary(root: pathlib.Path, revision: str) -> dict[str, bytes]:
    return load_snapshot(root, revision, BOUNDARY_PATHS)


def check_snapshot(snapshot: dict[str, bytes], revision: str, root: pathlib.Path,
                   build: pathlib.Path, complete_docs: bool) -> dict[str, Any]:
    metadata = validate_metadata(snapshot, revision, root)
    docs = validate_docs(snapshot, complete=complete_docs)
    validate_requirements(snapshot, root)
    validate_recovery_route(snapshot, root, revision)
    tests = validate_tests(snapshot, build)
    added = validate_boundaries(snapshot, root, revision)
    return {"metadata": metadata, "documentation_sections": docs,
            "configured_ctest_count": tests, "added_paths": added}


if __name__ == "__main__":
    raise SystemExit(main())
