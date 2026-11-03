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
import tempfile
from typing import Any

MAX_BYTES = 2 * 1024 * 1024
MAX_OUTPUT = 32 * 1024 * 1024
BASELINE = "f2542c8053db1e5183e0dd0e8702e77afbb2eb59"
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
BOUNDARY_PATHS = (
    ".planning/STATE.md", ".planning/state.json", ".planning/ROADMAP.md",
    ".planning/config.json",
    ".planning/phases/GB-22-composition-and-microtest-evidence/.continue-here.md",
)
FORBIDDEN_DIRS = ("fixtures/acid2", "fixtures/gbmicrotest")
FORBIDDEN_FILES = (
    "tests/external/diagnostic-package-identities.json",
    "tests/scripts/verify-diagnostic-packages.py",
)
HEX40 = re.compile(r"^[0-9a-f]{40}$")


class Reject(ValueError):
    pass


def run(argv: list[str], root: pathlib.Path, *, timeout: int = 30,
        limit: int = MAX_OUTPUT) -> tuple[int, bytes, bytes]:
    if not argv or any("\x00" in arg for arg in argv):
        raise Reject("subprocess-arguments-invalid")
    try:
        result = subprocess.run(argv, cwd=root, capture_output=True, check=False,
                                timeout=timeout,
                                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    except subprocess.TimeoutExpired:
        raise Reject("subprocess-timeout") from None
    except OSError as error:
        raise Reject(f"subprocess-start-failed:{error.__class__.__name__}") from None
    if len(result.stdout) > limit or len(result.stderr) > limit:
        raise Reject("subprocess-output-limit")
    return result.returncode, result.stdout, result.stderr


def git(root: pathlib.Path, *args: str, limit: int = MAX_OUTPUT) -> bytes:
    code, out, err = run(["git", *args], root, limit=limit)
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


def load_snapshot(root: pathlib.Path, revision: str,
                  paths: tuple[str, ...] = REQUIRED) -> dict[str, bytes]:
    entries = tree_entries(root, revision)
    result = {}
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
             "--repo-root", str(copied), "--source-revision", revision], copied)
        refusal = (out + err).decode("utf-8", "replace")
        if code != 2 or "scope-resolution-required" not in refusal:
            raise Reject("approval-refusal-contract-invalid")
        if any(gate not in refusal for gate in GATES):
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
        clauses = (
            "original synthetic DMG composition and controls passed",
            "metadata-only assessment retained all 513 source/ROM names",
            "No real upstream diagnostic payload was fetched, retained, built, run, or admitted",
            "no real diagnostic result exists",
            "Git blob IDs and sizes do not provide ROM SHA-256 values, reproducibility, or redistribution rights",
            "31 initial exclusions", "482 blocked and not observed",
            "zero admitted and zero executed", "DIAG-01 and DIAG-02 remain Pending",
            "RIGHTS-01 remains Pending under Phase 20 ownership", "a separately selected scope",
            "CPU-08", "DMG-CPU-B", "CGB-CPU-E",
        )
        for clause in clauses:
            if clause.casefold() not in current.casefold():
                raise Reject(f"documentation-current-claim-missing:{label}:{clause}")
        for gate in GATES:
            if gate not in current:
                raise Reject(f"documentation-gate-missing:{label}:{gate}")
        for phrase in ("real diagnostic result passed", "license prohibits use",
                       "license prohibition", "DIAG-01 is complete", "DIAG-02 is complete",
                       "hardware qualified", "mode-3 timing passed",
                       "broad compatibility established"):
            if phrase.casefold() in current.casefold():
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


def validate_requirements(snapshot: dict[str, bytes], root: pathlib.Path) -> None:
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
    add_tests = "\n".join(
        f'add_test(NAME "{name}" COMMAND "{cmake_exe}" -E true)' for name in sorted(actual)
    )
    project_file = (
        "cmake_minimum_required(VERSION 3.20)\nproject(Inventory NONE)\n"
        f'set(PROJECT_SOURCE_DIR "{src.as_posix()}")\n'
        f'set(GBB_TEST_INSTALL_PREFIX "{prefix.as_posix() if has_prefix else ""}")\n'
        f"{add_tests}\ninclude(\"{(src / 'cmake/ExpectedTests.cmake').as_posix()}\")\n"
        "gabbaboy_verify_registered_tests()\n"
    )
    (project / "CMakeLists.txt").write_text(project_file, encoding="utf-8")
    code, out, err = run(["cmake", "-S", str(project), "-B", str(project / "build")], project)
    if code:
        output = (out + err).decode("utf-8", "replace").casefold()
        if "registered ctest cases differ" in output:
            raise Reject("configured-ctest-inventory-mismatch")
        raise Reject("expected-test-policy-failed")


def validate_tests(snapshot: dict[str, bytes], build: pathlib.Path) -> int:
    validate_test_text(snapshot)
    names = configured_names(build)
    with tempfile.TemporaryDirectory(prefix="gbb-expected-tests-") as tmp:
        check_expected_policy(snapshot, names, pathlib.Path(tmp))
    return len(names)


def forbidden_fixture_path(path: str) -> bool:
    value = path.casefold()
    if any(value == item or value.startswith(item + "/")
           for item in (*FORBIDDEN_DIRS, *FORBIDDEN_FILES)):
        return True
    if value == "tests/acid2/control.asm":
        return False
    named = any(token in value for token in ("acid2", "gbmicrotest", "diagnostic"))
    payload = pathlib.PurePosixPath(value).suffix in {
        ".gb", ".gbc", ".rom", ".png", ".rgb", ".tar", ".zip", ".gz",
    }
    return named and payload


def require_no_diagnostic_payload(paths: list[str]) -> None:
    rejected = [path for path in paths if forbidden_fixture_path(path)]
    if rejected:
        raise Reject("diagnostic-payload-added:" + ",".join(rejected))


def added_paths(root: pathlib.Path, revision: str) -> list[dict[str, Any]]:
    raw = git(root, "diff", "--no-renames", "--diff-filter=A", "--name-only", "-z",
              BASELINE, revision, "--")
    paths = [item.decode("utf-8", "strict") for item in raw.split(b"\0") if item]
    entries = tree_entries(root, revision)
    require_no_diagnostic_payload(paths)
    return [{"path": path, "size_bytes": entries.get(path, ("", 0, ""))[1]} for path in paths]


def validate_boundaries(snapshot: dict[str, bytes], root: pathlib.Path,
                        revision: str) -> list[dict[str, Any]]:
    for path in PRESERVED:
        if snapshot[path] != git(root, "show", f"{BASELINE}:{path}", limit=MAX_BYTES):
            raise Reject(f"source-package-boundary-changed:{path}")
    added = added_paths(root, revision)
    entries = tree_entries(root, revision)
    for directory in FORBIDDEN_DIRS:
        if any(path == directory or path.startswith(directory + "/") for path in entries):
            raise Reject(f"diagnostic-fixture-path-present:{directory}")
    if "tests/acid2/control.asm" not in entries:
        raise Reject("synthetic-control-source-missing")
    return added


def check_snapshot(snapshot: dict[str, bytes], revision: str, root: pathlib.Path,
                   build: pathlib.Path, complete_docs: bool) -> dict[str, Any]:
    metadata = validate_metadata(snapshot, revision, root)
    docs = validate_docs(snapshot, complete=complete_docs)
    validate_requirements(snapshot, root)
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


def minimal_boundary() -> dict[str, bytes]:
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


def boundary_history_control() -> None:
    with tempfile.TemporaryDirectory(prefix="gbb-boundary-control-") as name:
        repo = pathlib.Path(name)
        git(repo, "init", "-q")
        git(repo, "config", "user.name", "GabbaBoy Synthetic Boundary")
        git(repo, "config", "user.email", "boundary@example.invalid")
        for path, raw in minimal_boundary().items():
            target = repo.joinpath(*path.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "synthetic historical boundary")
        boundary = resolve_revision(repo, "HEAD")
        if validate_boundary(load_boundary(repo, boundary))["phase23"] != "unstarted":
            raise Reject("self-test-historical-boundary-invalid")
        state = repo / ".planning/STATE.md"
        state.write_text("Phase 23 is complete.\n", encoding="utf-8")
        git(repo, "add", ".planning/STATE.md")
        git(repo, "commit", "-qm", "synthetic later route")
        expect_reject(lambda: validate_boundary(load_boundary(repo, resolve_revision(repo, "HEAD"))),
                      "boundary-phase22-not-complete", "later-head-route")
        if validate_boundary(load_boundary(repo, boundary))["phase23"] != "unstarted":
            raise Reject("self-test-historical-boundary-rejected")


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
        if snapshot.get(path) != git(root, "show", f"{BASELINE}:{path}", limit=MAX_BYTES):
            raise Reject(f"source-package-boundary-changed:{path}")


def self_test(snapshot: dict[str, bytes], controls: bool,
              revision: str, repo: pathlib.Path) -> None:
    inventory = parse_json(snapshot[INVENTORY], "self-test-inventory")
    if len(inventory.get("cases", [])) != 513:
        raise Reject("self-test-positive-inventory-failed")
    validate_metadata(snapshot, revision, repo)
    validate_docs(snapshot)
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
        "diagnostic-assessment-supported-component-has-blocker", "unsupported-rights-upgrade",
    )
    assessment = parse_json(snapshot[ASSESSMENT], "self-test-assessment")
    value = json.loads(json.dumps(assessment))
    next(row for row in value["required_gates"] if row["id"] == GATES[0])["status"] = "supported"
    expect_reject(lambda: validate_gate_shape(value), "gate-set-mutated", "gate-authorization")
    requirement = dict(snapshot)
    requirement[".planning/REQUIREMENTS.md"] = snapshot[".planning/REQUIREMENTS.md"].replace(
        b"**DIAG-01**", b"**DIAG-01 completed**", 1)
    expect_reject(lambda: validate_requirements(requirement, pathlib.Path.cwd()),
                  "requirement-definition-changed", "requirement-completion")
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
    expect_reject(lambda: require_no_diagnostic_payload(
        ["fixtures/acid2/diagnostics.tar"]),
        "diagnostic-payload-added", "fixture-path")
    doc = dict(snapshot)
    doc["docs/diagnostic-evidence.md"] = snapshot["docs/diagnostic-evidence.md"].replace(
        b"These gaps make the evidence insufficient for admission",
        b"These gaps establish successful real diagnostic results", 1)
    expect_reject(lambda: validate_docs(doc), "documentation", "broadened-claim")
    for path in ("LICENSE", "THIRD_PARTY_NOTICES.md", "cmake/FixtureAdmissionPolicy.json"):
        value = dict(snapshot)
        value[path] += b"\nmutated\n"
        expect_reject(lambda item=value: validate_preserved(item, pathlib.Path.cwd()),
                      "source-package-boundary-changed", "preserved-boundary")
    boundary = minimal_boundary()
    value = dict(boundary)
    value[BOUNDARY_PATHS[-1]] = value[BOUNDARY_PATHS[-1]].replace(
        b"/gsd-discuss-phase 23", b"/gsd-execute-phase 23")
    expect_reject(lambda: validate_boundary(value), "boundary-phase23-route-invalid", "wrong-route")
    value = dict(boundary)
    value[".planning/config.json"] = value[".planning/config.json"].replace(
        b'"_auto_chain_active":false', b'"_auto_chain_active":true')
    expect_reject(lambda: validate_boundary(value), "boundary-auto-advance-enabled", "auto-flag")
    boundary_history_control()
    print("diagnostic evidence controls pass positives=1 rejected_controls=passed boundary=immutable")


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
    build = (args.build_dir or root / "build/phase1").resolve(strict=True)
    result = check_snapshot(snapshot, revision, root, build, complete_docs=False)
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
            "snapshot_sha256": {path: sha256(snapshot[path]) for path in REQUIRED},
            "assessment": result,
        }
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checker_id = result["metadata"]["assessment_checker_sha256"]
    print(f"diagnostic evidence pass source={revision} assessment=blocked cases=513 "
          "unresolved_gates=7 admitted=0 executed=0 assessment_checker_sha256={checker_id}")
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
            boundary = resolve_revision(root, args.boundary_revision)
            validate_boundary(load_boundary(root, boundary))
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
    tests = validate_tests(snapshot, build)
    added = validate_boundaries(snapshot, root, revision)
    return {"metadata": metadata, "documentation_sections": docs,
            "configured_ctest_count": tests, "added_paths": added}


if __name__ == "__main__":
    raise SystemExit(main())
