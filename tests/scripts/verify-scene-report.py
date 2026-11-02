#!/usr/bin/env python3
"""Create and check bounded, local scene reports without discovering game media."""

import argparse
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import uuid


MAX_REPORT_BYTES = 65536
MAX_TEXT_BYTES = {"title": 256, "scene": 512, "symptom": 4096}
MAX_LIST_ITEMS = 128
SOURCE_CONTRACT_PATHS = (
    "tests/scripts/verify-scene-report.py",
    "tests/cmake/game-evidence.cmake",
    "docs/scene-feedback.md",
)
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
STAGES = {"triage", "reproduced", "regression-ready"}
CLASSIFICATIONS = {"core", "conversion", "host", "original-behavior", "unknown"}
FIELDS = {
    "schema_version", "report_id", "synthetic", "created_at", "title", "scene", "symptom",
    "stage", "classification", "metadata", "reproduction", "privacy", "promotion",
}
METADATA_FIELDS = {
    "public_release", "source_revision", "build_id", "rom_sha256", "model_profile",
    "execution_mode", "route",
}
REPRODUCTION_FIELDS = {
    "status", "boundary", "behavior_kind", "sequence", "budget_master_ticks", "evidence", "blocker",
}
PRIVACY_FIELDS = {"private_media_used", "private_media_refs"}


class Reject(Exception):
    """A scene report violates a local intake or promotion rule."""


def reject_if(condition, reason):
    if condition:
        raise Reject(reason)


def require_keys(value, expected, where):
    if not isinstance(value, dict):
        raise Reject(f"{where}-not-object")
    missing = sorted(expected - set(value))
    extra = sorted(set(value) - expected)
    if missing:
        raise Reject(f"{where}-field-missing:{','.join(missing)}")
    if extra:
        raise Reject(f"{where}-field-unknown:{','.join(extra)}")


def bounded_text(value, field):
    if not isinstance(value, str):
        raise Reject(f"scene-report-{field}-invalid")
    try:
        size = len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError:
        raise Reject(f"scene-report-{field}-invalid") from None
    if not value.strip() or size > MAX_TEXT_BYTES[field]:
        raise Reject(f"scene-report-{field}-invalid")
    if any(ord(char) < 0x20 or ord(char) == 0x7f for char in value):
        raise Reject(f"scene-report-{field}-invalid")
    return value.strip()


def clean_optional_text(value, where, limit=1024):
    if not isinstance(value, str) or len(value.encode("utf-8", errors="replace")) > limit:
        raise Reject(f"scene-report-{where}-invalid")
    if any(ord(char) < 0x20 and char not in "\t\n" for char in value):
        raise Reject(f"scene-report-{where}-invalid")
    return value


def no_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Reject(f"scene-report-json-duplicate-key:{key}")
        result[key] = value
    return result


def reject_json_constant(value):
    raise Reject(f"scene-report-json-invalid-constant:{value}")


def parse_json(raw, where):
    if len(raw) > MAX_REPORT_BYTES:
        raise Reject(f"scene-report-size-limit:{where}")
    try:
        return json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=no_duplicate_pairs,
                          parse_constant=reject_json_constant)
    except Reject:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise Reject(f"scene-report-json-invalid:{where}") from None


def validate_report(value):
    require_keys(value, FIELDS, "scene-report")
    if value["schema_version"] != 1 or isinstance(value["schema_version"], bool):
        raise Reject("scene-report-schema-version-invalid")
    if not isinstance(value["report_id"], str) or not re.fullmatch(r"scene-[0-9a-f]{32}", value["report_id"]):
        raise Reject("scene-report-id-invalid")
    if not isinstance(value["synthetic"], bool):
        raise Reject("scene-report-synthetic-invalid")
    if not isinstance(value["created_at"], str):
        raise Reject("scene-report-created-at-invalid")
    try:
        datetime.datetime.fromisoformat(value["created_at"].replace("Z", "+00:00"))
    except ValueError:
        raise Reject("scene-report-created-at-invalid") from None
    for field in ("title", "scene", "symptom"):
        bounded_text(value[field], field)
    if not isinstance(value["stage"], str) or value["stage"] not in STAGES:
        raise Reject("scene-report-stage-invalid")
    if not isinstance(value["classification"], str) or value["classification"] not in CLASSIFICATIONS:
        raise Reject("scene-report-classification-invalid")

    metadata = value["metadata"]
    require_keys(metadata, METADATA_FIELDS, "scene-report-metadata")
    for field, item in metadata.items():
        clean_optional_text(item, f"metadata-{field}", 512)
        if not item.strip():
            raise Reject(f"scene-report-metadata-{field}-invalid")
    source_revision = metadata["source_revision"]
    if source_revision != "unknown" and not HEX40.fullmatch(source_revision):
        raise Reject("scene-report-metadata-source-revision-invalid")
    rom_digest = metadata["rom_sha256"]
    if rom_digest != "unknown" and not HEX64.fullmatch(rom_digest):
        raise Reject("scene-report-metadata-rom-sha256-invalid")

    reproduction = value["reproduction"]
    require_keys(reproduction, REPRODUCTION_FIELDS, "scene-report-reproduction")
    if (not isinstance(reproduction["status"], str) or
            reproduction["status"] not in {"not-run", "reproduced", "not-reproduced", "blocked"}):
        raise Reject("scene-report-reproduction-status-invalid")
    if not isinstance(reproduction["boundary"], str) or reproduction["boundary"] not in CLASSIFICATIONS:
        raise Reject("scene-report-reproduction-boundary-invalid")
    sequence = reproduction["sequence"]
    evidence = reproduction["evidence"]
    if not isinstance(sequence, list) or len(sequence) > MAX_LIST_ITEMS:
        raise Reject("scene-report-sequence-invalid")
    if not isinstance(evidence, list) or len(evidence) > MAX_LIST_ITEMS:
        raise Reject("scene-report-evidence-invalid")
    for step in sequence:
        clean_optional_text(step, "sequence-step", 512)
        if not step.strip():
            raise Reject("scene-report-sequence-invalid")
    for item in evidence:
        clean_optional_text(item, "evidence-item", 1024)
        if not item.strip():
            raise Reject("scene-report-evidence-invalid")
    budget = reproduction["budget_master_ticks"]
    if budget is not None and (not isinstance(budget, int) or isinstance(budget, bool) or budget < 1):
        raise Reject("scene-report-budget-invalid")
    blocker = clean_optional_text(reproduction["blocker"], "blocker", 2048)
    if value["stage"] == "triage":
        if value["classification"] != "unknown" or reproduction["status"] != "not-run":
            raise Reject("scene-report-triage-must-remain-unresolved")
        if (reproduction["boundary"] != "unknown" or reproduction["behavior_kind"] != "unknown" or
                sequence or budget is not None or evidence):
            raise Reject("scene-report-triage-has-reproduction-claims")
        if not blocker.strip():
            raise Reject("scene-report-triage-next-action-required")
    elif value["stage"] == "reproduced":
        if reproduction["status"] != "reproduced" or value["classification"] == "unknown":
            raise Reject("scene-report-reproduction-evidence-required")
        if not sequence or budget is None or not evidence:
            raise Reject("scene-report-reproduction-evidence-incomplete")

    privacy = value["privacy"]
    require_keys(privacy, PRIVACY_FIELDS, "scene-report-privacy")
    if not isinstance(privacy["private_media_used"], bool):
        raise Reject("scene-report-private-media-flag-invalid")
    media_refs = privacy["private_media_refs"]
    if not isinstance(media_refs, list) or len(media_refs) > MAX_LIST_ITEMS:
        raise Reject("scene-report-private-media-refs-invalid")
    for reference in media_refs:
        clean_optional_text(reference, "private-media-reference", 1024)
    if value["stage"] == "regression-ready":
        raise Reject("scene-report-promotion-contract-required")
    return value


def initial_report(title, scene, symptom, synthetic=False):
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "schema_version": 1,
        "report_id": f"scene-{uuid.uuid4().hex}",
        "synthetic": synthetic,
        "created_at": now,
        "title": bounded_text(title, "title"),
        "scene": bounded_text(scene, "scene"),
        "symptom": bounded_text(symptom, "symptom"),
        "stage": "triage",
        "classification": "unknown",
        "metadata": {
            "public_release": "unknown",
            "source_revision": "unknown",
            "build_id": "unknown",
            "rom_sha256": "unknown",
            "model_profile": "unknown",
            "execution_mode": "unknown",
            "route": "unknown",
        },
        "reproduction": {
            "status": "not-run",
            "boundary": "unknown",
            "behavior_kind": "unknown",
            "sequence": [],
            "budget_master_ticks": None,
            "evidence": [],
            "blocker": (
                "Recover the public release, source/build, ROM identity, and model; inspect independent "
                "documentation, then choose a bounded runner route."
            ),
        },
        "privacy": {"private_media_used": False, "private_media_refs": []},
        "promotion": None,
    }


def resolve_repo_root(value):
    root = Path(value) if value is not None else Path(__file__).resolve().parents[2]
    try:
        root = root.resolve(strict=True)
    except OSError:
        raise Reject("scene-report-repo-root-unavailable") from None
    if not root.is_dir():
        raise Reject("scene-report-repo-root-unavailable")
    return root


def check_no_symlink_components(root, target):
    try:
        relative = target.relative_to(root)
    except ValueError:
        raise Reject("scene-report-output-outside-repo") from None
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise Reject("scene-report-output-symlink")


def safe_output_directory(root, requested=None):
    raw = Path(requested) if requested is not None else root / "build" / "scene-reports"
    if ".." in raw.parts:
        raise Reject("scene-report-output-traversal")
    lexical = raw if raw.is_absolute() else root / raw
    expected = root / "build" / "scene-reports"
    try:
        lexical.relative_to(expected)
    except ValueError:
        raise Reject("scene-report-output-outside-local-directory") from None
    check_no_symlink_components(root, lexical)
    try:
        lexical.mkdir(parents=True, exist_ok=True, mode=0o700)
    except OSError:
        raise Reject("scene-report-output-unavailable") from None
    check_no_symlink_components(root, lexical)
    if not lexical.is_dir():
        raise Reject("scene-report-output-unavailable")
    return lexical


def safe_report_path(root, requested):
    raw = Path(requested)
    if ".." in raw.parts:
        raise Reject("scene-report-path-traversal")
    lexical = raw if raw.is_absolute() else root / raw
    expected = root / "build" / "scene-reports"
    try:
        lexical.relative_to(expected)
    except ValueError:
        raise Reject("scene-report-path-outside-local-directory") from None
    check_no_symlink_components(root, lexical)
    try:
        if not lexical.is_file() or lexical.stat().st_size > MAX_REPORT_BYTES:
            raise Reject("scene-report-file-unavailable-or-oversize")
    except OSError:
        raise Reject("scene-report-file-unavailable-or-oversize") from None
    return lexical


def write_new_report(root, report, output=None):
    directory = safe_output_directory(root, output)
    validate_report(report)
    destination = directory / f"{report['report_id']}.json"
    payload = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if len(payload) > MAX_REPORT_BYTES:
        raise Reject("scene-report-size-limit:new-report")
    try:
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
    except FileExistsError:
        raise Reject("scene-report-output-collision") from None
    except OSError:
        raise Reject("scene-report-output-write-failed") from None
    return destination


def git_output(root, *arguments):
    try:
        result = subprocess.run(["git", *arguments], cwd=root, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise Reject("scene-report-source-tool-unavailable") from None
    if result.returncode != 0 or len(result.stdout) > MAX_REPORT_BYTES:
        raise Reject("scene-report-source-unavailable")
    return result.stdout


def verify_source_contract(root, revision, checkout_overrides=None):
    if not isinstance(revision, str) or not HEX40.fullmatch(revision):
        raise Reject("scene-report-source-revision-invalid")
    resolved = git_output(root, "rev-parse", "--verify", "--quiet", f"{revision}^{{commit}}").decode(
        "ascii", errors="strict").strip()
    if resolved != revision:
        raise Reject("scene-report-source-revision-unavailable")
    checkout_overrides = checkout_overrides or {}
    digests = {}
    for relative in SOURCE_CONTRACT_PATHS:
        immutable = git_output(root, "show", f"{revision}:{relative}")
        current = checkout_overrides.get(relative)
        if current is None:
            try:
                current = (root / relative).read_bytes()
            except OSError:
                raise Reject(f"scene-report-source-file-unavailable:{relative}") from None
        if current != immutable:
            raise Reject(f"scene-report-source-mismatch:{relative}")
        digests[relative] = hashlib.sha256(immutable).hexdigest()
    return digests


def load_and_validate(root, requested):
    path = safe_report_path(root, requested)
    try:
        raw = path.read_bytes()
    except OSError:
        raise Reject("scene-report-file-unavailable-or-oversize") from None
    return validate_report(parse_json(raw, str(path))), path


def run_cli(root, *arguments):
    return subprocess.run(
        [sys.executable, "-I", str(Path(__file__).resolve()), *arguments,
         "--repo-root", str(root)],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, timeout=5, check=False,
    )


def expect_cli_reject(root, label, *arguments, reason):
    result = run_cli(root, *arguments)
    diagnostic = (result.stdout + result.stderr).strip()
    if result.returncode == 0 or reason not in diagnostic:
        raise Reject(f"scene-report-negative-control-failed:{label}:{diagnostic[:160]}")


def intake_self_test():
    controls = 0
    with tempfile.TemporaryDirectory(prefix="gbb-scene-intake-") as directory:
        root = Path(directory).resolve()
        output = root / "build" / "scene-reports"
        output.mkdir(parents=True)
        created = run_cli(
            root, "--new", "--synthetic-control", "--title", "Synthetic title",
            "--scene", "Synthetic opening scene", "--symptom", "Synthetic subject only",
            "--output", str(output),
        )
        if created.returncode != 0:
            raise Reject("scene-report-minimal-intake-failed:" + created.stderr.strip())
        reports = list(output.glob("*.json"))
        if len(reports) != 1:
            raise Reject("scene-report-intake-output-count")
        parsed = validate_report(parse_json(reports[0].read_bytes(), str(reports[0])))
        if not parsed["synthetic"] or parsed["stage"] != "triage" or parsed["classification"] != "unknown":
            raise Reject("scene-report-intake-not-unresolved-synthetic")
        if parsed["privacy"] != {"private_media_used": False, "private_media_refs": []}:
            raise Reject("scene-report-intake-private-media-default")
        controls += 1
        validated = run_cli(root, "--validate", str(reports[0]))
        if validated.returncode != 0 or "stage=triage" not in validated.stdout:
            raise Reject("scene-report-real-cli-validation-failed:" + validated.stderr.strip())
        controls += 1
        expect_cli_reject(root, "empty-title", "--new", "--title", "", "--scene", "Opening",
                          "--symptom", "Missing title", reason="scene-report-title-invalid")
        controls += 1
        expect_cli_reject(root, "oversized-symptom", "--new", "--title", "Title", "--scene", "Opening",
                          "--symptom", "x" * (MAX_TEXT_BYTES["symptom"] + 1),
                          reason="scene-report-symptom-invalid")
        controls += 1
        outside = root / "outside"
        outside.mkdir()
        expect_cli_reject(root, "unsafe-output", "--new", "--title", "Title", "--scene", "Opening",
                          "--symptom", "Unsafe path", "--output", str(outside),
                          reason="scene-report-output-outside-local-directory")
        controls += 1
        link = output / "linked"
        link.symlink_to(outside, target_is_directory=True)
        expect_cli_reject(root, "symlink-output", "--new", "--title", "Title", "--scene", "Opening",
                          "--symptom", "Unsafe symlink", "--output", str(link),
                          reason="scene-report-output-symlink")
        controls += 1
        malformed = output / "malformed.json"
        malformed.write_text('{"schema_version":1,"schema_version":1}', encoding="ascii")
        expect_cli_reject(root, "duplicate-json-key", "--validate", str(malformed),
                          reason="scene-report-json-duplicate-key:schema_version")
        controls += 1
    print(f"scene-report intake self-test pass controls={controls} subjects=synthetic-only")


def synthetic_source_file(root, relative, content):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
    return path


def create_synthetic_promotion_subject(root):
    """Create a throwaway source-pinned CTest subject; it is never game evidence."""
    root.mkdir(parents=True, exist_ok=True)
    source_root = Path(__file__).resolve().parents[2]
    synthetic_source_file(root, ".gitignore", "/build/\n")
    for relative in SOURCE_CONTRACT_PATHS:
        synthetic_source_file(root, relative, (source_root / relative).read_bytes())
    fixture = b"synthetic scene control bytes\n"
    fixture_path = "tests/fixtures/synthetic-scene.gb"
    fixture_digest = hashlib.sha256(fixture).hexdigest()
    synthetic_source_file(root, fixture_path, fixture)
    rights_path = "tests/fixtures/synthetic-scene-rights.json"
    rights = {
        "schema_version": 1,
        "origin": "project-authored",
        "license": "MIT",
        "permissions": {"repository": True, "public_ci": True},
        "files": [{"path": fixture_path, "sha256": fixture_digest}],
    }
    rights_raw = (json.dumps(rights, sort_keys=True, indent=2) + "\n").encode("utf-8")
    synthetic_source_file(root, rights_path, rights_raw)
    oracle_path = "docs/synthetic-scene-oracle.json"
    oracle_raw = b'{"expected":"blue","basis":"synthetic independent author specification"}\n'
    synthetic_source_file(root, oracle_path, oracle_raw)
    check_path = "tests/scene/scene-check.py"
    check_source = (
        "from pathlib import Path\n"
        "import sys\n"
        "mode = sys.argv[1]\n"
        "expected_marker = 'expected-static-blue'\n"
        "mutation_marker = 'mutated-static-green'\n"
        "expected = 'blue'\n"
        "if mode == 'positive':\n"
        "    actual = 'blue'\n"
        "    assert actual == expected, expected_marker\n"
        "elif mode == 'negative':\n"
        "    mutated = 'green'\n"
        "    assert mutated != expected, mutation_marker\n"
        "else:\n"
        "    raise SystemExit(2)\n"
    )
    check_bytes = check_source.encode("utf-8")
    synthetic_source_file(root, check_path, check_bytes)
    registration_path = "tests/cmake/synthetic-scenes.cmake"
    registration = (
        'add_test(NAME synthetic_scene_positive COMMAND "${Python3_EXECUTABLE}" -I '
        '"${CMAKE_SOURCE_DIR}/tests/scene/scene-check.py" positive)\n'
        'add_test(NAME synthetic_scene_negative COMMAND "${Python3_EXECUTABLE}" -I '
        '"${CMAKE_SOURCE_DIR}/tests/scene/scene-check.py" negative)\n'
        'set_tests_properties(synthetic_scene_positive synthetic_scene_negative PROPERTIES TIMEOUT 5)\n'
    )
    synthetic_source_file(root, registration_path, registration)
    top_level = (
        "cmake_minimum_required(VERSION 3.25)\n"
        "project(SceneReportSynthetic NONE)\n"
        "find_package(Python3 COMPONENTS Interpreter REQUIRED)\n"
        "enable_testing()\n"
        f'include("${{CMAKE_SOURCE_DIR}}/{registration_path}")\n'
    )
    synthetic_source_file(root, "CMakeLists.txt", top_level)
    configured = subprocess.run(["cmake", "-S", str(root), "-B", str(root / "build")],
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, timeout=15, check=False)
    if configured.returncode != 0:
        raise Reject("scene-report-synthetic-configure-failed:" + configured.stderr.strip()[-160:])
    exercised = subprocess.run(["ctest", "--test-dir", str(root / "build"), "--output-on-failure",
                                "--no-tests=error"], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, timeout=15, check=False)
    if exercised.returncode != 0:
        raise Reject("scene-report-synthetic-tests-failed:" + exercised.stderr.strip()[-160:])
    init = subprocess.run(["git", "init", "-q", str(root)], stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5, check=False)
    if init.returncode != 0:
        raise Reject("scene-report-synthetic-git-init-failed")
    add = subprocess.run(["git", "-C", str(root), "add", "CMakeLists.txt", ".gitignore", "docs",
                          "tests", "tests/cmake", "tests/fixtures", "tests/scene", "tests/scripts"],
                         stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         timeout=5, check=False)
    if add.returncode != 0:
        raise Reject("scene-report-synthetic-git-add-failed")
    commit = subprocess.run(["git", "-C", str(root), "-c", "user.name=Scene Control",
                             "-c", "user.email=scene-control@example.invalid", "commit", "-q", "-m",
                             "synthetic scene control"], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=5, check=False)
    if commit.returncode != 0:
        raise Reject("scene-report-synthetic-git-commit-failed")
    revision = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=5, check=False)
    if revision.returncode != 0:
        raise Reject("scene-report-synthetic-revision-unavailable")
    revision = revision.stdout.strip()
    output = root / "build" / "scene-reports"
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 1,
        "report_id": "scene-" + "1" * 32,
        "synthetic": True,
        "created_at": "2026-01-01T00:00:00Z",
        "title": "Synthetic title",
        "scene": "Synthetic static scene",
        "symptom": "A synthetic static scene expectation differs",
        "stage": "regression-ready",
        "classification": "core",
        "metadata": {
            "public_release": "synthetic fixture release",
            "source_revision": revision,
            "build_id": "synthetic-build-1",
            "rom_sha256": fixture_digest,
            "model_profile": "synthetic-model",
            "execution_mode": "synthetic-mode",
            "route": "one deterministic synthetic scene step",
        },
        "reproduction": {
            "status": "reproduced",
            "boundary": "core",
            "behavior_kind": "static",
            "sequence": ["load the synthetic fixture and observe the fixed scene"],
            "budget_master_ticks": 1,
            "evidence": ["synthetic fixture and independent oracle"],
            "blocker": "",
        },
        "privacy": {"private_media_used": False, "private_media_refs": []},
        "promotion": {
            "fixture": {
                "kind": "original",
                "path": fixture_path,
                "sha256": fixture_digest,
                "permission_evidence_path": rights_path,
                "permission_evidence_sha256": hashlib.sha256(rights_raw).hexdigest(),
                "minimized": True,
                "deterministic": True,
            },
            "expectation": {
                "kind": "static-pixels",
                "behavior": "The independently specified scene pixel is blue.",
                "independent_basis": "Synthetic author specification defines blue before emulator output.",
                "basis_path": oracle_path,
                "basis_sha256": hashlib.sha256(oracle_raw).hexdigest(),
            },
            "registration_path": registration_path,
            "positive": {
                "test_name": "synthetic_scene_positive",
                "source_path": check_path,
                "source_sha256": hashlib.sha256(check_bytes).hexdigest(),
                "assertion_marker": "expected-static-blue",
                "status": "pass",
            },
            "negative": {
                "test_name": "synthetic_scene_negative",
                "source_path": check_path,
                "source_sha256": hashlib.sha256(check_bytes).hexdigest(),
                "assertion_marker": "mutated-static-green",
                "status": "pass",
                "mutation_kind": "pixel",
                "mutation": "Change the expected pixel from blue to green.",
                "targets_expectation": True,
            },
        },
    }
    report_path = output / "synthetic-scene.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return revision, report_path, report


def promotion_self_test():
    with tempfile.TemporaryDirectory(prefix="gbb-scene-promotion-") as directory:
        root = Path(directory).resolve() / "subject"
        revision, report_path, _ = create_synthetic_promotion_subject(root)
        result = run_cli(root, "--promotion-check", str(report_path), "--source-revision", revision)
        if result.returncode != 0 or "synthetic contract accepted" not in result.stdout:
            raise Reject("scene-report-synthetic-promotion-rejected:" + (result.stderr or result.stdout).strip()[-200:])
    print("scene-report promotion self-test pass subjects=synthetic-only")


def verify_document_contract(text):
    raise Reject("scene-report-document-contract-not-implemented")


def documentation_self_test(root, source_revision=None):
    if source_revision is not None:
        verify_source_contract(root, source_revision)
    try:
        text = (root / "docs/scene-feedback.md").read_text(encoding="utf-8")
    except OSError:
        raise Reject("scene-report-document-unavailable") from None
    verify_document_contract(text)
    try:
        verify_document_contract(text.replace("--promotion-check", "--promotion-option-removed", 1))
    except Reject as error:
        if "--promotion-check" not in str(error):
            raise
    else:
        raise Reject("scene-report-document-negative-control-failed")
    print("scene-report documentation contract self-test pass subjects=synthetic-only")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--new", action="store_true")
    modes.add_argument("--validate", metavar="REPORT")
    modes.add_argument("--promotion-check", metavar="REPORT")
    modes.add_argument("--self-test", nargs="?", const="all",
                       choices=("all", "intake", "controls", "contract"))
    parser.add_argument("--title")
    parser.add_argument("--scene")
    parser.add_argument("--symptom")
    parser.add_argument("--output", help="local output directory below build/scene-reports")
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--source-revision")
    parser.add_argument("--synthetic-control", action="store_true",
                        help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        root = resolve_repo_root(args.repo_root)
        if args.self_test:
            if args.self_test in ("all", "intake"):
                intake_self_test()
            if args.self_test in ("all", "controls"):
                promotion_self_test()
            if args.self_test in ("all", "contract"):
                documentation_self_test(root, args.source_revision)
            return 0
        if args.source_revision is not None:
            verify_source_contract(root, args.source_revision)
        if args.new:
            report = initial_report(args.title, args.scene, args.symptom, args.synthetic_control)
            destination = write_new_report(root, report, args.output)
            print(f"scene-report created report={destination} stage=triage classification=unknown "
                  f"synthetic={str(report['synthetic']).lower()}")
            return 0
        if args.validate is not None:
            report, path = load_and_validate(root, args.validate)
            print(f"scene-report valid report={path} stage={report['stage']} "
                  f"classification={report['classification']} synthetic={str(report['synthetic']).lower()}")
            return 0
        if args.promotion_check is not None:
            raise Reject("scene-report-promotion-contract-incomplete")
        raise Reject("scene-report-mode-required")
    except (Reject, OSError, ValueError, UnicodeError) as error:
        print(f"verify-scene-report: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
