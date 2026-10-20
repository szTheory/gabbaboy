#!/usr/bin/env python3
"""Validate the stable support ledger and bind it to an immutable Git tag."""
from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
# Set only by --evidence-only while verifying an already attached sidecar in a job that did not build the
# product: the receipt then lives outside the checkout and the producer's build files are absent. Source
# inputs, the receipt's content and every build file that IS present are still checked; generation and
# --check-current never relax anything.
EVIDENCE_ONLY = False
# Ledgers are versioned when the support scope changes, not on every release.
# A release binds the newest ledger at or below its own version, read from the
# tagged tree, so a fixes-only patch release reuses the unchanged ledger.
LEDGER_DIR = "docs/support"
LEDGER_NAME = re.compile(r"v(\d+)\.(\d+)\.(\d+)\.md")
TAG = re.compile(r"v(\d+)\.(\d+)\.(\d+)")
BEGIN = "<!-- support-ledger-data-begin -->"
END = "<!-- support-ledger-data-end -->"
MAX_LEDGER_BYTES = 32 * 1024 * 1024
MAX_RECEIPT_BYTES = 32 * 1024 * 1024
MAX_INPUT_BYTES = 32 * 1024 * 1024
V2_REQUIRED_CASES = 107
V2_MODEL = "CGB-CPU-E"
V2_MANIFEST_PATHS = [
    "fixtures/age/manifest.json",
    "fixtures/magentests/manifest.json",
    "fixtures/mooneye-cgb/manifest.json",
    "fixtures/samesuite/manifest.json",
]
V2_DISPOSITION_PATHS = [
    "tests/external/cgb-apu-dispositions.json",
    "tests/external/cgb-ppu-dispositions.json",
    "tests/external/cgb-speed-dispositions.json",
]
CASE_IDS = [
    "mooneye-acceptance-instr-daa",
    "mooneye-acceptance-timer-tim00",
    "mooneye-acceptance-timer-tim00-div-trigger",
]


def fail(message: str) -> None:
    raise ValueError(message)


def version_key(match: re.Match) -> tuple[int, int, int]:
    return tuple(int(part) for part in match.groups())


def select_ledger(names: list[str], tag: str) -> str:
    """Select only a ledger from this tag's major/minor support scope."""
    tag_match = TAG.fullmatch(tag)
    if not tag_match:
        fail("tag must be a vX.Y.Z release tag")
    release = version_key(tag_match)
    candidates = []
    for name in names:
        match = LEDGER_NAME.fullmatch(name)
        version = version_key(match) if match else None
        if version and version[:2] == release[:2] and version <= release:
            candidates.append((version, name))
    if not candidates:
        if release == (0, 2, 0):
            fail("exact v0.2.0 support ledger is missing")
        fail("no support ledger exists in this release's major/minor scope")
    return f"{LEDGER_DIR}/{max(candidates)[1]}"


def ledger_version(path: str) -> str:
    return ".".join(LEDGER_NAME.fullmatch(pathlib.PurePosixPath(path).name).groups())


def working_tree_ledger() -> str:
    # Keep the legacy validator's fixture fixed as newer ledger schemas arrive.
    return f"{LEDGER_DIR}/v0.1.0.md"


def parse_ledger(raw: bytes, expected_version: str) -> dict:
    if len(raw) > MAX_LEDGER_BYTES:
        fail("ledger exceeds the bounded read size")
    try:
        source = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        fail(f"ledger is not valid UTF-8: {error}")
    if "\ufffd" in source:
        fail("ledger contains Unicode replacement character")
    if re.search(r"(?im)^\s*[\"']?(?:source_sha|release_source_sha)[\"']?\s*[:=]\s*[\"']?[0-9a-f]{40}", source):
        fail("tracked ledger must not embed a future/full release source SHA")
    if BEGIN not in source or END not in source or source.count(BEGIN) != 1 or source.count(END) != 1:
        fail("ledger must contain exactly one delimited structured data block")
    block = source.split(BEGIN, 1)[1].split(END, 1)[0]
    match = re.search(r"```json\s*(.*?)\s*```", block, re.S)
    if not match:
        fail("ledger structured data block is missing fenced JSON")
    try:
        data = json.loads(match.group(1), object_pairs_hook=unique_pairs)
    except (json.JSONDecodeError, ValueError) as error:
        fail(f"invalid or duplicate-key ledger JSON: {error}")
    if type(data) is dict and any(type(data.get(key)) is str and
                                  re.fullmatch(r"[0-9a-f]{40,64}", data[key])
                                  for key in ("source_sha", "release_source_sha")):
        fail("tracked ledger must not embed a future/full release source SHA")
    validate_data(data, expected_version)
    return data


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def validate_data(data: dict, expected_version: str) -> None:
    if isinstance(data, dict) and data.get("schema_version") == 2:
        validate_data_v2(data, expected_version)
        return
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        fail("unsupported ledger schema")
    if data.get("version") != expected_version or data.get("boot") != "skipped":
        fail("ledger version/profile identity is missing or unstable")
    if data.get("model") != "bootless DMG-CPU-B deterministic software profile":
        fail("ledger must name the scoped bootless DMG-CPU-B model")
    if data.get("broad_game_claim") is not False or data.get("physical_dmg_observations") != 0:
        fail("ledger contains a broad-game or unsupported physical-hardware claim")
    cases = data.get("executed_cases")
    ids = [case.get("id") for case in cases] if isinstance(cases, list) else []
    if ids != CASE_IDS or len(set(ids)) != len(ids):
        fail("eligible cases are missing, duplicated, or not in stable manifest order")
    if data.get("eligible_denominator") != len(CASE_IDS) or data.get("executed_denominator") != len(CASE_IDS):
        fail("ledger denominator does not equal the fixed executed corpus")
    if any(case.get("status") != "pass" for case in cases):
        fail("case outcomes must be explicit and nonempty")
    if data.get("failures") != []:
        fail("current failures must be represented explicitly (empty list means none)")
    if not data.get("known_issues") or len(set(data["known_issues"])) != len(data["known_issues"]):
        fail("known issues are missing or duplicated")
    if not data.get("fixture_classes") or len(set(data["fixture_classes"])) != len(data["fixture_classes"]):
        fail("fixture classes are missing or duplicated")
    if not re.fullmatch(r"[0-9a-f]{40}", data.get("corpus_revision", "")):
        fail("exact corpus revision is missing or malformed")
    exclusions = data.get("excluded_cartridges")
    limitations = data.get("limitations")
    evidence = data.get("evidence_classes")
    if not exclusions or len(set(exclusions)) != len(exclusions):
        fail("missing or duplicate exclusions")
    if not limitations or len(set(limitations)) != len(limitations):
        fail("missing or duplicate limitations")
    if not evidence or len(set(evidence)) != len(evidence):
        fail("missing or duplicate evidence classes")
    if not any("physical DMG" in item for item in limitations):
        fail("physical-hardware limitation is missing")
    if any(re.search(r"\b(all|every|most)\s+games?\b|compatible with games", item, re.I)
           for item in limitations):
        fail("broad game compatibility wording detected")
    paths = data.get("manifest_paths")
    digests = data.get("manifest_sha256")
    if not isinstance(paths, list) or len(paths) != 4 or len(set(paths)) != len(paths):
        fail("fixture/corpus manifest identities are missing or duplicated")
    if not isinstance(digests, dict) or set(digests) != set(paths):
        fail("manifest digest map does not match the listed manifests")
    for path, value in digests.items():
        if not re.fullmatch(r"[0-9a-f]{64}", value):
            fail(f"malformed SHA-256 for {path}")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded)


def relative_path(value: object, code: str = "input-path-invalid") -> str:
    if (type(value) is not str or not value or len(value) > 4096 or "\0" in value or
            "\\" in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value) or
            any(part in ("", ".", "..") for part in value.split("/"))):
        fail(code)
    return value


def bounded_file(path: pathlib.Path, limit: int, code: str) -> bytes:
    try:
        size = path.stat().st_size
        if size > limit:
            fail(code + ":too-large")
        raw = path.read_bytes()
    except OSError as error:
        fail(code + ":unavailable")
    if len(raw) > limit:
        fail(code + ":too-large")
    return raw


def strict_json(raw: bytes, label: str) -> dict:
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(text, object_pairs_hook=unique_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail(label + ":invalid-json-or-duplicate-key")
    except ValueError as error:
        fail(label + ":" + str(error))
    if type(value) is not dict:
        fail(label + ":invalid-json-root")
    return value


def read_repo_file(repo_root: pathlib.Path, value: object, limit: int, code: str) -> tuple[str, bytes]:
    relative = relative_path(value, code)
    root = repo_root.resolve()
    path = (root / relative).resolve(strict=True)
    try:
        path.relative_to(root)
    except ValueError:
        fail(code + ":outside-root")
    if not path.is_file():
        fail(code + ":not-file")
    return relative, bounded_file(path, limit, code)


def _sha_field(value: object, code: str) -> None:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        fail(code)


def _sorted_unique_strings(value: object, code: str) -> list[str]:
    if (type(value) is not list or not value or any(type(item) is not str or not item for item in value) or
            len(set(value)) != len(value) or value != sorted(value)):
        fail(code)
    return value


def _count_suite_model_modes(bindings: list[dict], observations: list[dict]) -> list[dict]:
    eligible = collections.Counter()
    observed = collections.defaultdict(list)
    for row in bindings:
        key = (row["suite"], row["model"], row["mode"], row["speed"])
        eligible[key] += 1
    for row in observations:
        key = (row["suite"], row["model"], row["mode"], row["speed"])
        observed[key].append(row)
    result = []
    for suite, model, mode, speed in sorted(eligible):
        rows = observed.get((suite, model, mode, speed), [])
        assertion_rows = [item for row in rows for item in row["assertions"]]
        executed = sum(row["executed"] is True for row in rows)
        actual_pass = sum(row["observed_result"] == "pass" and row["evaluator_status"] == "pass"
                          for row in rows)
        actual_fail = sum(row["observed_result"] == "fail" for row in rows)
        matched = sum(row["matched_xfail"] is True for row in rows)
        result.append({
            "suite": suite,
            "model": model,
            "mode": mode,
            "speed": speed,
            "boot": "skipped",
            "eligible": eligible[(suite, model, mode, speed)],
            "attempted": sum(row["attempted"] is True for row in rows),
            "executed": executed,
            "actual_pass": actual_pass,
            "actual_fail": actual_fail,
            "matched_xfail": matched,
            "excluded": sum(row["excluded"] is True for row in rows),
            "not_run": eligible[(suite, model, mode, speed)] - executed,
            "assertions": len(assertion_rows),
            "passing_assertions": sum(row.get("observed_result") == "pass" and
                                      row.get("evaluator_status") == "pass" for row in assertion_rows),
            "failing_assertions": sum(row.get("observed_result") == "fail" for row in assertion_rows),
        })
    if set(observed) != set(eligible):
        fail("receipt-suite-model-mode-membership-mismatch")
    return result


def _count_receipt_cases(observations: list[dict]) -> dict:
    assertion_rows = [item for row in observations for item in row["assertions"]]
    actual_pass = sum(row["observed_result"] == "pass" and row["evaluator_status"] == "pass"
                      for row in observations)
    actual_fail = sum(row["observed_result"] == "fail" for row in observations)
    executed = sum(row["executed"] is True for row in observations)
    return {
        "admitted_cases": len(observations),
        "applicable_cases": len(observations),
        "required_eligible_cases": len(observations),
        "attempted_cases": sum(row["attempted"] is True for row in observations),
        "completed_cases": executed,
        "observed_pass_cases": actual_pass,
        "observed_fail_cases": actual_fail,
        "matched_xfail_cases": sum(row["matched_xfail"] is True for row in observations),
        "excluded_cases": sum(row["excluded"] is True for row in observations),
        "not_run_cases": len(observations) - executed,
        "assertions": len(assertion_rows),
        "passing_assertions": sum(row.get("observed_result") == "pass" and
                                   row.get("evaluator_status") == "pass" for row in assertion_rows),
        "failing_assertions": sum(row.get("observed_result") == "fail" for row in assertion_rows),
        "image_pixels": sum(row["details"].get("image_pixels", 0) for row in observations),
        "pixel_mismatches": sum(row["details"].get("pixel_mismatches", 0) for row in observations),
    }


def validate_data_v2(data: dict, expected_version: str, expected_case_count: int = V2_REQUIRED_CASES) -> None:
    if type(data) is not dict or data.get("schema_version") != 2:
        fail("unsupported ledger schema")
    if expected_version != "0.2.0" or data.get("version") != expected_version:
        fail("v0.2 ledger version/profile identity is missing or unstable")
    game = data.get("game_evidence")
    if (type(game) is not dict or game.get("status") != "absent" or
            game.get("statement") != "No CGB game-level evidence exists"):
        fail("v0.2 CGB game-evidence absence statement is missing")
    scope = data.get("scope")
    if scope != {
        "models": ["CGB-CPU-E", "DMG-CPU-B"],
        "corpus_model": "CGB-CPU-E",
        "modes": ["compat", "native"],
        "boot": "skipped",
        "physical_cgb_e": "UNKNOWN/POLICY",
    }:
        fail("v0.2 model, execution-mode, boot, or physical-evidence scope mismatch")

    source_inputs = data.get("source_inputs")
    if type(source_inputs) is not list or not source_inputs:
        fail("source-input inventory is empty or missing")
    input_paths = []
    input_by_path = {}
    for row in source_inputs:
        if type(row) is not dict:
            fail("source-input row is malformed")
        relative_path(row.get("path"))
        _sha_field(row.get("sha256"), "source-input SHA-256 is malformed")
        if type(row.get("size_bytes")) is not int or row["size_bytes"] < 0:
            fail("source-input size is malformed")
        input_paths.append(row["path"])
        input_by_path[row["path"]] = row
    if len(input_paths) != len(set(input_paths)):
        fail("source-input path is duplicated")
    if input_paths != sorted(input_paths):
        fail("source-input paths are not in stable order")

    manifest_rows = data.get("manifest_identities")
    disposition_rows = data.get("disposition_identities")
    for label, rows in (("manifest", manifest_rows), ("disposition", disposition_rows)):
        if type(rows) is not list or not rows:
            fail(label + " identities are empty or missing")
        paths = []
        for row in rows:
            if type(row) is not dict:
                fail(label + " identity row is malformed")
            relative_path(row.get("path"))
            _sha_field(row.get("sha256"), label + " SHA-256 is malformed")
            if type(row.get("size_bytes")) is not int or row["size_bytes"] < 0:
                fail(label + " size is malformed")
            paths.append(row["path"])
        if len(paths) != len(set(paths)):
            fail(label + " path is duplicated")
    if [row["path"] for row in manifest_rows] != V2_MANIFEST_PATHS:
        fail("manifest identity paths differ from the admitted suite manifests")
    if [row["path"] for row in disposition_rows] != V2_DISPOSITION_PATHS:
        fail("disposition identity paths differ from the admitted disposition files")
    for row in [*manifest_rows, *disposition_rows]:
        source_row = input_by_path.get(row["path"])
        if (source_row is None or source_row["sha256"] != row["sha256"] or
                source_row["size_bytes"] != row["size_bytes"]):
            fail("manifest or disposition identity differs from source inputs:" + row["path"])

    inventory = data.get("inventory")
    if type(inventory) is not dict:
        fail("independent inventory is missing")
    relative_path(inventory.get("path"))
    _sha_field(inventory.get("sha256"), "independent inventory SHA-256 is malformed")
    inventory_source = input_by_path.get(inventory["path"])
    if (inventory["path"] != "tests/external/cgb-corpus-inventory.json" or
            inventory_source is None or inventory_source["sha256"] != inventory["sha256"]):
        fail("independent inventory identity differs from source inputs")
    case_ids = _sorted_unique_strings(inventory.get("case_ids"), "required inventory membership is empty, duplicated, or unordered")
    if len(case_ids) != expected_case_count or inventory.get("required_case_count") != expected_case_count:
        fail("required inventory membership is incomplete or narrowed")
    bindings = inventory.get("case_bindings")
    if type(bindings) is not list or [row.get("id") for row in bindings if type(row) is dict] != case_ids:
        fail("independent inventory case bindings are incomplete or duplicated")
    for row in bindings:
        if (type(row) is not dict or type(row.get("id")) is not str or
                type(row.get("suite")) is not str or row.get("model") != V2_MODEL or
                row.get("mode") not in ("compat", "native") or
                row.get("speed") not in ("normal", "double") or
                type(row.get("test_name")) is not str or not row["test_name"] or
                type(row.get("source_id")) is not str or not row["source_id"] or
                type(row.get("source_path")) is not str or not row["source_path"] or
                type(row.get("source_revision")) is not str or
                not re.fullmatch(r"[0-9a-f]{40,64}", row["source_revision"]) or
                type(row.get("output_id")) is not str or not row["output_id"] or
                type(row.get("output_path")) is not str or not row["output_path"] or
                type(row.get("output_sha256")) is not str or
                not re.fullmatch(r"[0-9a-f]{64}", row["output_sha256"]) or
                type(row.get("assertion_ids")) is not list or not row["assertion_ids"] or
                any(type(item) is not str or not item for item in row["assertion_ids"]) or
                len(set(row["assertion_ids"])) != len(row["assertion_ids"]) or
                type(row.get("expected_failure")) is not bool or
                row.get("disposition_state") not in
                ("pass", "expected-failure", "prior-phase-observation", "prior-observation") or
                type(row.get("disposition_value")) is not str or not row["disposition_value"] or
                row["expected_failure"] != (row["disposition_state"] == "expected-failure")):
            fail("independent inventory case binding is malformed")
        relative_path(row["source_path"])
        relative_path(row["output_path"])
        if row.get("expected_signature_sha256") is not None:
            _sha_field(row["expected_signature_sha256"], "expected failure signature is malformed")

    receipt = data.get("receipt")
    if type(receipt) is not dict:
        fail("complete corpus receipt identity is missing")
    relative_path(receipt.get("path"))
    for field in ("sha256", "identity_sha256", "input_identity_sha256", "run_id", "source_inputs_sha256"):
        _sha_field(receipt.get(field), "receipt " + field + " is malformed")
    if (type(receipt.get("producer_revision")) is not str or
            not re.fullmatch(r"[0-9a-f]{40,64}", receipt["producer_revision"])):
        fail("receipt producer revision is malformed")
    if receipt["source_inputs_sha256"] != canonical_sha256(source_inputs):
        fail("receipt source-input identity digest mismatch")
    if receipt.get("model") != "CGB-CPU-E selected software model" or receipt.get("hardware_qualified") is not False:
        fail("receipt contains a model or hardware-qualification mismatch")
    run = receipt.get("run")
    if (type(run) is not dict or run.get("id") != receipt.get("run_id") or
            type(run.get("ctest_cases")) is not int or
            run.get("ctest_cases") != expected_case_count + 1 or
            type(run.get("ctest_total_cases")) is not int or
            run.get("ctest_total_cases") < run.get("ctest_cases")):
        fail("receipt CTest run is incomplete or has a mismatched denominator")
    _sha_field(run.get("ctest_log_sha256"), "receipt CTest log SHA-256 is malformed")
    _sha_field(run.get("run_nonce_sha256"), "receipt run nonce SHA-256 is missing")
    if receipt.get("case_ids") != case_ids:
        fail("receipt case membership differs from the independent inventory")
    observations = receipt.get("case_observations")
    if type(observations) is not list:
        fail("receipt case observations are missing")
    observation_ids = [row.get("id") for row in observations if type(row) is dict]
    if observation_ids != case_ids:
        fail("receipt case membership is incomplete, duplicated, or out of order")
    binding_by_id = {row["id"]: row for row in bindings}
    for row in observations:
        if type(row) is not dict:
            fail("receipt case observation is malformed")
        binding = binding_by_id[row["id"]]
        producer_case = row.get("producer_case")
        if (type(producer_case) is not dict or producer_case.get("id") != row["id"] or
                row.get("case_sha256") != canonical_sha256(producer_case) or
                row.get("assertions") != producer_case.get("assertions") or
                row.get("details") != producer_case.get("details") or
                row.get("observed_result") != producer_case.get("observed_result") or
                row.get("evaluator_status") != producer_case.get("evaluator_status") or
                row.get("matched_xfail") != producer_case.get("matched_xfail")):
            fail("receipt observation fields differ from its source-bound producer case")
        if any(row.get(field) != binding[field] for field in
               ("suite", "model", "mode", "speed", "test_name")):
            fail("receipt case binding differs from the independent inventory")
        evidence = row.get("evidence")
        if (type(evidence) is not dict or any(evidence.get(field) != binding[field] for field in
                ("source_id", "source_path", "source_revision", "output_id", "output_path", "output_sha256"))):
            fail("receipt source/output evidence differs from the independent inventory")
        if (row.get("expected_failure") is not binding["expected_failure"] or
                producer_case.get("evaluator_disposition") != binding["disposition_value"]):
            fail("receipt expected-failure disposition differs from independent inventory")
        if (row.get("boot") != "skipped" or row.get("attempted") is not True or
                row.get("executed") is not True or row.get("excluded") is not False or
                type(row.get("matched_xfail")) is not bool or
                row.get("observed_result") not in ("pass", "fail") or
                row.get("evaluator_status") not in ("pass", "xfail")):
            fail("receipt contains an incomplete or invalid case observation")
        expected_failure = binding["expected_failure"]
        if expected_failure:
            if (row["observed_result"] != "fail" or row["evaluator_status"] != "xfail" or
                    row["matched_xfail"] is not True):
                fail("receipt unexpected pass or unmatched expected failure")
        elif (row["observed_result"] != "pass" or row["evaluator_status"] != "pass" or
              row["matched_xfail"] is not False):
            fail("receipt unexpected failure or xfail-as-pass disposition")
        assertions = row.get("assertions")
        if type(assertions) is not list or not assertions:
            fail("receipt assertion membership is missing")
        assertion_ids = []
        for assertion in assertions:
            if (type(assertion) is not dict or type(assertion.get("id")) is not str or
                    not assertion["id"] or assertion.get("expected_disposition") != "pass" or
                    assertion.get("observed_result") not in ("pass", "fail") or
                    assertion.get("evaluator_status") not in ("pass", "xfail")):
                fail("receipt assertion row is malformed")
            assertion_ids.append(assertion["id"])
            if assertion.get("signature_sha256") is not None:
                _sha_field(assertion["signature_sha256"], "receipt assertion signature is malformed")
        if assertion_ids != binding["assertion_ids"]:
            fail("receipt assertion IDs or signatures differ from inventory membership")
        expected_signature = binding.get("expected_signature_sha256")
        observed_signatures = [item.get("signature_sha256") for item in assertions
                               if item.get("signature_sha256") is not None]
        if (expected_signature is not None and observed_signatures and
                expected_signature not in observed_signatures):
            fail("receipt expected failure signature changed")
        if type(row.get("details")) is not dict:
            fail("receipt case details are malformed")
        _sha_field(row.get("case_sha256"), "receipt case identity SHA-256 is malformed")
        _sha_field(row.get("assertion_signatures_sha256"), "receipt assertion signatures SHA-256 is malformed")
        if row["case_sha256"] != canonical_sha256(row.get("producer_case")):
            fail("receipt case identity digest mismatch")
        if row["assertion_signatures_sha256"] != canonical_sha256(assertions):
            fail("receipt assertion signature digest mismatch")

    expected_suite_counts = _count_suite_model_modes(bindings, observations)
    if receipt.get("suite_model_mode_counts") != expected_suite_counts:
        fail("receipt per-suite model/mode counts do not derive from case rows")
    expected_counts = _count_receipt_cases(observations)
    claimed_counts = receipt.get("counts")
    if type(claimed_counts) is not dict or any(claimed_counts.get(key) != value
                                             for key, value in expected_counts.items()):
        fail("receipt global counts do not derive from complete case and assertion rows")
    if (expected_counts["observed_pass_cases"] + expected_counts["observed_fail_cases"] != expected_case_count or
            expected_counts["observed_fail_cases"] != expected_counts["matched_xfail_cases"] or
            expected_counts["not_run_cases"] != 0 or expected_counts["excluded_cases"] != 0):
        fail("receipt pass, xfail, exclusion, or not-run totals do not close")

    artifacts = receipt.get("build_artifacts")
    if type(artifacts) is not list or not artifacts:
        fail("receipt build artifact identities are missing")
    artifact_paths = []
    for row in artifacts:
        if type(row) is not dict:
            fail("receipt build artifact is malformed")
        relative_path(row.get("path"))
        _sha_field(row.get("sha256"), "receipt build artifact SHA-256 is malformed")
        if type(row.get("size_bytes")) is not int or row["size_bytes"] < 0:
            fail("receipt build artifact size is malformed")
        artifact_paths.append(row["path"])
    if len(artifact_paths) != len(set(artifact_paths)):
        fail("receipt build artifact path is duplicated")


def _case_binding_rows(inventory: dict) -> list[dict]:
    sources = {row.get("id"): row for row in inventory.get("source_candidates", []) if type(row) is dict}
    outputs = {row.get("id"): row for row in inventory.get("outputs", []) if type(row) is dict}
    bindings = []
    for case in inventory.get("cases", []):
        if type(case) is not dict or type(case.get("id")) is not str:
            fail("inventory case is malformed")
        source = sources.get(case.get("source_id"))
        output = outputs.get(case.get("output_id"))
        rows = case.get("assertion_contract", {}).get("rows")
        if type(source) is not dict or type(output) is not dict or type(rows) is not list or not rows:
            fail("inventory case source, output, or assertion contract is missing")
        disposition = case.get("evaluator_disposition", {})
        bindings.append({
            "id": case["id"],
            "suite": case.get("suite"),
            "model": case.get("model"),
            "mode": case.get("mode"),
            "speed": case.get("speed"),
            "test_name": case.get("test_binding", {}).get("ctest_name"),
            "source_id": case.get("source_id"),
            "source_path": source.get("source_path"),
            "source_revision": source.get("source_commit"),
            "output_id": case.get("output_id"),
            "output_path": output.get("output_path"),
            "output_sha256": output.get("sha256"),
            "assertion_ids": [row.get("id") for row in rows if type(row) is dict],
            "expected_failure": disposition.get("state") == "expected-failure",
            "disposition_state": disposition.get("state"),
            "disposition_value": disposition.get("value"),
            "expected_signature_sha256": disposition.get("signature_sha256") or None,
        })
    bindings.sort(key=lambda row: row["id"])
    ids = [row["id"] for row in bindings]
    if len(ids) != len(set(ids)):
        fail("inventory case IDs are duplicated")
    return bindings


def _receipt_observations(receipt: dict, bindings: list[dict]) -> list[dict]:
    by_id = {row["id"]: row for row in bindings}
    observations = []
    seen = set()
    for producer_case in receipt.get("cases", []):
        if type(producer_case) is not dict or type(producer_case.get("id")) is not str:
            fail("receipt case is malformed")
        case_id = producer_case["id"]
        if case_id in seen or case_id not in by_id:
            fail("receipt case membership is duplicated or unknown")
        seen.add(case_id)
        binding = by_id[case_id]
        evidence = producer_case.get("evidence")
        if type(evidence) is not dict:
            fail("receipt source/output evidence is missing")
        for field in ("source_id", "source_path", "output_id", "output_path", "output_sha256"):
            if evidence.get(field) != binding[field]:
                fail("receipt source/output binding mismatch:" + case_id)
        if evidence.get("source_revision") != binding["source_revision"]:
            fail("receipt source revision mismatch:" + case_id)
        disposition = producer_case.get("evaluator_disposition")
        expected_failure = binding["expected_failure"]
        if disposition != binding["disposition_value"]:
            fail("receipt evaluator disposition differs from inventory:" + case_id)
        assertions = producer_case.get("assertions")
        if type(assertions) is not list:
            fail("receipt assertion rows are missing:" + case_id)
        observations.append({
            "id": case_id,
            "suite": producer_case.get("suite"),
            "model": producer_case.get("model"),
            "mode": producer_case.get("mode"),
            "speed": producer_case.get("speed"),
            "test_name": producer_case.get("test_name"),
            "boot": "skipped",
            "attempted": producer_case.get("attempted") is True,
            "executed": producer_case.get("completed") is True,
            "excluded": False,
            "observed_result": producer_case.get("observed_result"),
            "evaluator_status": producer_case.get("evaluator_status"),
            "matched_xfail": producer_case.get("matched_xfail"),
            "expected_failure": binding["expected_failure"],
            "evidence": {field: evidence.get(field) for field in (
                "source_id", "source_path", "source_revision", "output_id", "output_path", "output_sha256",
                "manifest_ref")},
            "details": producer_case.get("details", {}),
            "assertions": assertions,
            "case_sha256": canonical_sha256(producer_case),
            "assertion_signatures_sha256": canonical_sha256(assertions),
            "producer_case": producer_case,
        })
    if seen != set(by_id):
        fail("receipt is missing required inventory cases")
    observations.sort(key=lambda row: row["id"])
    return observations


def _validate_run_identity(receipt: dict, inventory_sha256: str) -> dict:
    identity = receipt.get("identity")
    run = receipt.get("run")
    if type(identity) is not dict or type(run) is not dict or receipt.get("status") != "complete":
        fail("corpus receipt is incomplete")
    if receipt.get("failure_codes") != [] or identity.get("hardware_qualified") is not False:
        fail("corpus receipt carries failure or hardware qualification")
    if identity.get("inventory_sha256") != inventory_sha256:
        fail("receipt inventory digest differs from independent inventory bytes")
    for field in ("identity_sha256", "input_identity_sha256", "core_revision", "run_id"):
        value = identity.get(field)
        if type(value) is not str or not re.fullmatch(r"[0-9a-f]{40,64}", value):
            fail("receipt identity field is malformed:" + field)
    if (run.get("id") != identity.get("run_id") or
            type(run.get("ctest_cases")) is not int or
            run.get("ctest_cases") != V2_REQUIRED_CASES + 1):
        fail("receipt run identity or case denominator mismatch")
    if (type(run.get("ctest_total_cases")) is not int or
            run.get("ctest_total_cases") < run.get("ctest_cases")):
        fail("receipt CTest denominator is incomplete")
    if (type(run.get("started_at_ns")) is not int or type(run.get("completed_at_ns")) is not int or
            run["completed_at_ns"] <= run["started_at_ns"]):
        fail("receipt run timestamps are invalid")
    _sha_field(run.get("ctest_log_sha256"), "receipt CTest log identity is malformed")
    _sha_field(run.get("run_nonce_sha256"), "receipt run nonce is missing")
    identity_body = dict(identity)
    claimed_identity_sha = identity_body.pop("identity_sha256")
    if canonical_sha256(identity_body) != claimed_identity_sha:
        fail("receipt identity digest does not match its fields")
    return identity


def build_v2_data(receipt: dict, receipt_raw: bytes, inventory: dict, inventory_raw: bytes,
                  repo_root: pathlib.Path, receipt_path: str,
                  tagged_inputs: dict[str, bytes] | None = None) -> dict:
    inventory_sha = sha256(inventory_raw)
    identity = _validate_run_identity(receipt, inventory_sha)
    bindings = _case_binding_rows(inventory)
    case_ids = [row["id"] for row in bindings]
    if len(case_ids) != V2_REQUIRED_CASES or inventory.get("counts", {}).get("required_cases") != V2_REQUIRED_CASES:
        fail("independent inventory required denominator is not 107")
    observations = _receipt_observations(receipt, bindings)
    identity_case_ids = identity.get("case_ids")
    if identity_case_ids != case_ids:
        fail("receipt and independent inventory IDs differ")
    assertion_ids = {row["id"]: row["assertion_ids"] for row in bindings}
    if identity.get("assertion_ids") != assertion_ids:
        fail("receipt assertion IDs differ from independent inventory contracts")
    suite_counts = _count_suite_model_modes(bindings, observations)
    counts = _count_receipt_cases(observations)
    source_inputs = identity.get("input_hashes")
    if type(source_inputs) is not list or not source_inputs:
        fail("receipt source input hash list is missing")
    input_paths = []
    for row in source_inputs:
        if type(row) is not dict:
            fail("receipt source input hash row is malformed")
        relative_path(row.get("path"))
        _sha_field(row.get("sha256"), "receipt source input SHA-256 is malformed")
        if type(row.get("size_bytes")) is not int or row["size_bytes"] < 0:
            fail("receipt source input size is malformed")
        input_paths.append(row["path"])
    if len(input_paths) != len(set(input_paths)):
        fail("receipt source input path is duplicated")
    source_inputs = sorted(source_inputs, key=lambda row: row["path"])

    def identities(paths: list[str]) -> list[dict]:
        rows = []
        for relative in paths:
            if tagged_inputs is not None and relative in tagged_inputs:
                name, raw = relative, tagged_inputs[relative]
                if len(raw) > MAX_INPUT_BYTES:
                    fail("evidence-input:too-large")
            else:
                name, raw = read_repo_file(repo_root, relative, MAX_INPUT_BYTES, "evidence-input")
            strict_json(raw, "evidence-input:" + name)
            rows.append({"path": name, "sha256": sha256(raw), "size_bytes": len(raw)})
        return rows

    source_candidate_counts = inventory.get("counts", {}).get("by_suite", {})
    excluded_by_suite = collections.Counter(
        row.get("suite") for row in inventory.get("source_candidates", [])
        if type(row) is dict and row.get("selection", {}).get("state") == "excluded")
    output_case_ids = {case.get("output_id") for case in inventory.get("cases", []) if type(case) is dict}
    outside_outputs = sum(row.get("id") not in output_case_ids for row in inventory.get("outputs", [])
                          if type(row) is dict)
    inventory_data = {
        "path": "tests/external/cgb-corpus-inventory.json",
        "sha256": inventory_sha,
        "required_case_count": V2_REQUIRED_CASES,
        "case_ids": case_ids,
        "case_bindings": bindings,
        "source_candidates_by_suite": {
            suite: {
                "discovered": values.get("source_candidates", 0),
                "required": values.get("required_cases", 0),
                "excluded": excluded_by_suite.get(suite, 0),
            } for suite, values in sorted(source_candidate_counts.items())
        },
        "admitted_outputs": inventory.get("counts", {}).get("admitted_outputs"),
        "outputs_outside_required_case_set": outside_outputs,
    }
    receipt_data = {
        "path": receipt_path,
        "sha256": sha256(receipt_raw),
        "identity_sha256": identity["identity_sha256"],
        "input_identity_sha256": identity["input_identity_sha256"],
        "source_inputs_sha256": canonical_sha256(source_inputs),
        "producer_revision": identity["core_revision"],
        "run_id": receipt["run"]["id"],
        "model": identity.get("model"),
        "hardware_qualified": identity.get("hardware_qualified"),
        "run": {key: receipt["run"].get(key) for key in (
            "id", "ctest_cases", "ctest_total_cases", "ctest_log_sha256", "run_nonce_sha256")},
        "counts": counts,
        "suite_model_mode_counts": suite_counts,
        "case_ids": case_ids,
        "case_observations": observations,
        "build_artifacts": identity.get("build_artifacts"),
    }
    return {
        "schema_version": 2,
        "version": "0.2.0",
        "game_evidence": {
            "status": "absent",
            "statement": "No CGB game-level evidence exists",
        },
        "scope": {
            "models": ["CGB-CPU-E", "DMG-CPU-B"],
            "corpus_model": "CGB-CPU-E",
            "modes": ["compat", "native"],
            "boot": "skipped",
            "physical_cgb_e": "UNKNOWN/POLICY",
        },
        "source_inputs": sorted(source_inputs, key=lambda row: row["path"]),
        "manifest_identities": identities(V2_MANIFEST_PATHS),
        "disposition_identities": identities(V2_DISPOSITION_PATHS),
        "inventory": inventory_data,
        "receipt": receipt_data,
    }


def stable_v2_evidence(data: dict) -> dict:
    """Project away only producer/run/build provenance from ledger equality."""
    stable = copy.deepcopy(data)
    receipt = stable.get("receipt")
    if type(receipt) is not dict:
        fail("complete corpus receipt identity is missing")
    for field in ("sha256", "identity_sha256", "input_identity_sha256",
                  "producer_revision", "run_id"):
        receipt.pop(field, None)
    run = receipt.get("run")
    if type(run) is not dict:
        fail("receipt CTest run is incomplete")
    receipt["run"] = {"ctest_cases": run.get("ctest_cases")}
    artifacts = receipt.get("build_artifacts")
    if type(artifacts) is not list:
        fail("receipt build artifact identities are missing")
    receipt["build_artifacts"] = [{"path": row.get("path")} for row in artifacts
                                  if type(row) is dict]
    return stable


def render_v2_ledger(data: dict) -> str:
    counts = data["receipt"]["counts"]
    suite_rows = data["receipt"]["suite_model_mode_counts"]
    lines = [
        "# GabbaBoy v0.2.0 support ledger",
        "",
        "This ledger records implemented scope and the software evidence available for the v0.2.0 release. The CGB corpus is a bounded test-ROM set, not a game library or hardware qualification. Boot ROMs are skipped; the CGB corpus ran on the selected CGB-CPU-E software model. Physical CGB-E remains UNKNOWN/POLICY.",
        "",
        "## Models and execution modes",
        "",
        "- **DMG-CPU-B:** bootless deterministic DMG software profile. The Libbet and the Magic Floor v0.08 headless acceptance is a separate single-game software result. Packaged-player game smoke is macOS-only; headless acceptance runs on Linux, macOS and Windows.",
        "- **CGB-CPU-E:** selected CGB software model, with native CGB mode and DMG compatibility mode selected from the cartridge header. Test-ROM execution is bootless. A test-ROM result applies only to the recorded model, mode, speed, case and assertion rows.",
        "- **Boot path:** skipped for both profiles. Startup state is emulator policy. No physical startup or boot-ROM behavior is asserted.",
        "",
        "## CGB test-ROM evidence",
        "",
        f"The historical producer receipt records {counts['required_eligible_cases']} eligible cases, {counts['attempted_cases']} attempted, {counts['completed_cases']} completed, {counts['observed_pass_cases']} actual guest passes, {counts['observed_fail_cases']} actual guest failures, {counts['matched_xfail_cases']} matched expected failures, {counts['excluded_cases']} excluded and {counts['not_run_cases']} not run. There are {counts['assertions']} assertion rows ({counts['passing_assertions']} passing and {counts['failing_assertions']} failing). Fresh receipts must reproduce these stable case and assertion observations; matched expected failures remain failures and never increase the guest-pass total.",
        "",
        "| Suite | Model | Mode | Speed | Eligible | Attempted | Executed | Guest pass | Guest fail | Matched xfail | Excluded | Not run | Assertions | Assertion pass | Assertion fail |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in suite_rows:
        lines.append("| {suite} | {model} | {mode} | {speed} | {eligible} | {attempted} | {executed} | {actual_pass} | {actual_fail} | {matched_xfail} | {excluded} | {not_run} | {assertions} | {passing_assertions} | {failing_assertions} |".format(**row))
    lines.extend([
        "",
        "The structured block preserves the historical receipt's exact case membership, source/output identities, inventory dispositions, assertion IDs, observed assertion rows, nonce-bound CTest run identity, receipt bytes, source inputs and build artifacts. A fresh receipt is checked against the same stable evidence and its own actual source and build bytes. Suite source provenance and each case's source revision remain attached to the inventory bindings. The source trees retain independent author expectations; evaluator outcomes are not rewritten to match them.",
        "",
        "## Implemented cartridge and save matrix",
        "",
        "These are documented loader/core capabilities. The corpus rows above identify which model/mode combinations were exercised; they do not qualify every mapper and profile combination or game.",
        "",
        "| Mapper and header types | ROM / RAM bounds | Battery image and additional behavior |",
        "|---|---|---|",
        "| ROM-only `$00` | 32 KiB ROM; no RAM | No battery image |",
        "| Standard MBC1 `$01`/`$02`/`$03` | ROM size codes `$00`–`$06` (32 KiB–2 MiB). `$01` has no RAM; `$02` is volatile; `$03` is battery-backed. RAM is 8 KiB, or 32 KiB only through 512 KiB ROM. | Type `$03` persists RAM. MBC1M wiring is unsupported. |",
        "| MBC2 `$05`/`$06` | ROM size codes `$00`–`$03` (32–256 KiB); 512 built-in 4-bit cells and no header RAM | Type `$06` image is canonical 512 bytes; packed 256-byte files are unsupported |",
        "| MBC3 `$0F`–`$13` | ROM size codes `$00`–`$06` (32 KiB–2 MiB); 4 MiB length ceiling. `$0F`/`$11` have no RAM; `$10` has timer and 8/32 KiB RAM; `$12` volatile 8/32 KiB; `$13` battery 8/32 KiB. | `$0F`/`$10` use emulated-time RTC and a 21-byte versioned clock block; `$13` persists RAM. MBC30 is rejected. |",
        "| MBC5 `$19`–`$1E` | ROM size codes `$00`–`$08` (32 KiB–8 MiB); `$19`/`$1C` have no RAM, others support 8/32/64/128 KiB by type. | `$1B`/`$1E` persist RAM. `$1C`–`$1E` expose rumble-line state, with no host haptics or physical rumble claim. |",
        "",
        "Battery export/import is caller-buffer based and atomic on rejected input. MBC3 wall-clock catch-up is an explicit host call; the core never reads the host clock. RTC, mapper and save-format behavior are software evidence, not physical-board or cross-emulator compatibility claims. See [cartridge and save contract](../cartridge-and-saves.md).",
        "",
        "## Reconciled prior scope entries",
        "",
        "- **DMG game acceptance:** Libbet and the Magic Floor v0.08 has a ROM-bound, headless DMG-CPU-B acceptance predicate. This is evidence for one game on that software profile. Packaged-player smoke is macOS-only; a hosted reproduction run remains pending because the workflow has not been dispatched.",
        "- **MBC2 and MBC5 evidence:** Mooneye emulator-only MBC2 (7/7) and MBC5 (8/8) test ROMs were run on the DMG-CPU-B software profile from test-ROM revision `31510e12eea6286d36eea060a6adde755e1067aa`. Those counts are test-ROM results, not CGB evidence, broad game compatibility, MBC5 RAM qualification or physical rumble behavior.",
        "- **MBC3 and RTC:** RTC-capable `$0F`/`$10` cartridges advance from emulated half-dots; explicit host catch-up is separate. The 21-byte clock block, import bounds, phase preservation, and MBC1/MBC2/MBC3/MBC5 battery persistence are software contracts. No physical MBC3 or RTC observation is available; MBC30 is rejected.",
        "- **CGB profile and colour:** CGB-CPU-E exposes header-selected native or DMG-compatibility execution, CGB register/banking behavior and raw RGB555 frame output. Software fixtures and differential results cover named cases only; there is no perceptual color evidence or general game claim.",
        "- **CGB speed and HDMA:** double-speed execution keeps budgets in master half-dots; GDMA and HBlank DMA follow the documented bounded block model. The known `$83` → `$02` → `$00` → `$80` HDMA sequence remains unresolved against Pan Docs. No physical CGB-E timing qualification is made.",
        "- **CGB digital APU reads:** native CGB guest reads of FF76/FF77 expose digital DAC inputs on the CGB-CPU-E software model; CGB compatibility mode reads `$FF`. Player playback continues to use the scoped DMG APU model. This says nothing about analog output or perceptual audio quality.",
        "",
        "## Game-level evidence, known issues and exclusions",
        "",
        "**No CGB game-level evidence exists.** The CGB corpus consists of bounded emulator/test ROMs. The separate DMG Libbet acceptance does not establish CGB game behavior. No uncertain game image is admitted by this ledger.",
        "",
        "Known limitations include skipped boot ROMs; no physical DMG-CPU-B or CGB-CPU-E qualification; no general game compatibility percentage; no CGB mode-3 timing qualification; no analog audio, perceptual color/audio, or physical rumble claim; no MBC1M or MBC30 support; and no Linux/Windows packaged-player game smoke. CGB-CPU-E's current APU, PPU and speed limitations remain profile/model-specific as described in the CGB corpus and profile documentation.",
        "",
        "Evidence classes are kept distinct: source-backed expectations, admitted fixture bytes, independent inventory and assertion contracts, local software execution receipts, differential observations, project-authored regression tests, and game-level acceptance. Physical-hardware evidence is absent for this ledger.",
        "",
        "The receipt below is a historical producer snapshot: its exact bytes, producer revision, run identity and build artifacts identify that earlier run. A fresh receipt must independently validate its source and build bytes and reproduce the same stable corpus evidence before a release sidecar is created. The sidecar binds that supplied receipt's digest, producer revision, run identity and build artifacts alongside the tagged source and exact ledger blob; tag verification never regenerates this ledger. This tracked ledger intentionally contains no release source SHA.",
        "",
        "<!-- support-ledger-data-begin -->",
        "```json",
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False),
        "```",
        "<!-- support-ledger-data-end -->",
        "",
        "The chronological pending entries were reconciled into this versioned ledger. See the [CGB corpus contract](../cgb-corpus.md), [CGB profile](../cgb-profile.md), [game acceptance](../game-acceptance.md) and [cartridge/save contract](../cartridge-and-saves.md) for operational details.",
        "",
    ])
    return "\n".join(lines)


def create_current_ledger(receipt_path: pathlib.Path) -> dict:
    receipt_path = receipt_path.resolve(strict=True)
    try:
        receipt_rel = receipt_path.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        fail("receipt path must stay inside the repository")
    if receipt_rel != "build/cgb-corpus-receipt.json":
        fail("current support ledger requires the canonical build/cgb-corpus-receipt.json path")
    inventory_path = ROOT / "tests/external/cgb-corpus-inventory.json"
    inventory_raw = bounded_file(inventory_path, MAX_INPUT_BYTES, "inventory")
    inventory = strict_json(inventory_raw, "inventory")
    receipt_raw = bounded_file(receipt_path, MAX_RECEIPT_BYTES, "receipt")
    receipt = strict_json(receipt_raw, "receipt")
    run_inventory_validator()
    data = build_v2_data(receipt, receipt_raw, inventory, inventory_raw, ROOT, receipt_rel)
    identity = receipt.get("identity", {})
    current = current_git_revision()
    if identity.get("core_revision") == current:
        run_existing_receipt_validator(receipt_path, inventory)
    else:
        check_source_ancestry(identity.get("core_revision", ""), current)
    validate_data_v2(data, "0.2.0")
    validate_source_bindings(data, ROOT)
    target = ROOT / "docs/support/v0.2.0.md"
    target.write_text(render_v2_ledger(data), encoding="utf-8")
    return data


def validate_source_bindings(data: dict, repo_root: pathlib.Path,
                             source_bytes: dict[str, bytes] | None = None,
                             include_build: bool = True) -> None:
    root = repo_root.resolve()
    for section, rows in (("source", data.get("source_inputs")),
                          ("build", data.get("receipt", {}).get("build_artifacts"))):
        if section == "build" and not include_build:
            continue
        if type(rows) is not list:
            fail(section + " input identities are missing")
        for row in rows:
            if type(row) is not dict:
                fail(section + " input identity is malformed")
            if section == "source" and source_bytes is not None:
                if row.get("path") not in source_bytes:
                    fail(section + "-input:missing-tagged-byte")
                name, raw = row["path"], source_bytes[row["path"]]
                if len(raw) > MAX_INPUT_BYTES:
                    fail(section + "-input:too-large")
            else:
                if (section == "build" and EVIDENCE_ONLY and type(row.get("path")) is str
                        and not (root / row["path"]).exists()):
                    continue
                name, raw = read_repo_file(root, row.get("path"), MAX_INPUT_BYTES, section + "-input")
            if sha256(raw) != row.get("sha256") or len(raw) != row.get("size_bytes"):
                fail(section + " input is stale:" + name)


def current_git_revision() -> str:
    return git("rev-parse", "HEAD").decode("ascii", "strict").strip()


def check_source_ancestry(source_revision: str, current_revision: str,
                          repo_root: pathlib.Path = ROOT) -> None:
    try:
        subprocess.run(["git", "merge-base", "--is-ancestor", source_revision, current_revision],
                       cwd=repo_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       check=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        fail("receipt producer revision is not an ancestor of the current source")


def run_inventory_validator(repo_root: pathlib.Path = ROOT) -> None:
    validator = repo_root / "tests/scripts/verify-cgb-corpus-inventory.py"
    command = [sys.executable, "-I", str(validator), "--bindings"]
    try:
        completed = subprocess.run(command, cwd=repo_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, timeout=60, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        fail("independent inventory validator unavailable")
    if completed.returncode != 0:
        fail("independent inventory validator failed: " + completed.stderr.strip())


def run_existing_receipt_validator(receipt_path: pathlib.Path, inventory: dict,
                                   repo_root: pathlib.Path = ROOT,
                                   source_revision: str | None = None,
                                   inventory_raw: bytes | None = None,
                                   input_bytes: dict[str, bytes] | None = None) -> None:
    script = repo_root / "tests/scripts/verify-cgb-corpus-claims.py"
    spec = importlib.util.spec_from_file_location("gabbaboy_cgb_claims", script)
    if spec is None or spec.loader is None:
        fail("existing corpus report validator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        module.validate_receipt(receipt_path, inventory, source_revision=source_revision,
                                allow_ancestor=source_revision is not None,
                                repo_root=repo_root, inventory_raw=inventory_raw,
                                input_bytes=input_bytes)
    except module.ContractError as error:
        fail("existing corpus report validator failed: " + str(error))


def check_ledger_static(root: pathlib.Path = ROOT, run_inventory: bool = True) -> dict:
    """Receipt-free currency check of the tracked v0.2.0 ledger.

    The tracked ledger carries a historical producer snapshot, so its build-artifact digests are not
    compared with the working tree here. Everything that the ledger claims about the covered source
    inputs, the independent inventory and its own schema is. The receipt-bound check is --check-current,
    which needs a complete corpus receipt and runs where that receipt is produced.
    """
    ledger = parse_ledger(bounded_file(root / "docs/support/v0.2.0.md", MAX_LEDGER_BYTES, "ledger"), "0.2.0")
    if run_inventory:
        run_inventory_validator(root)
    validate_data_v2(ledger, "0.2.0")
    validate_source_bindings(ledger, root, include_build=False)
    return ledger


def check_current(receipt_path: pathlib.Path) -> dict:
    receipt_path = receipt_path.resolve(strict=True)
    try:
        receipt_rel = receipt_path.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        fail("receipt path must stay inside the repository")
    if receipt_rel != "build/cgb-corpus-receipt.json":
        fail("current support ledger requires the canonical build/cgb-corpus-receipt.json path")
    ledger_path = ROOT / "docs/support/v0.2.0.md"
    ledger = parse_ledger(bounded_file(ledger_path, MAX_LEDGER_BYTES, "ledger"), "0.2.0")
    inventory_path = ROOT / "tests/external/cgb-corpus-inventory.json"
    inventory_raw = bounded_file(inventory_path, MAX_INPUT_BYTES, "inventory")
    inventory = strict_json(inventory_raw, "inventory")
    receipt_raw = bounded_file(receipt_path, MAX_RECEIPT_BYTES, "receipt")
    receipt = strict_json(receipt_raw, "receipt")
    run_inventory_validator()
    data = build_v2_data(receipt, receipt_raw, inventory, inventory_raw, ROOT, receipt_rel)
    identity = receipt.get("identity", {})
    current = current_git_revision()
    if identity.get("core_revision") == current:
        run_existing_receipt_validator(receipt_path, inventory)
    else:
        check_source_ancestry(identity.get("core_revision", ""), current)
    validate_data_v2(ledger, "0.2.0")
    validate_data_v2(data, "0.2.0")
    validate_source_bindings(data, ROOT)
    if stable_v2_evidence(ledger) != stable_v2_evidence(data):
        fail("v0.2 ledger stable evidence differs from the current receipt, inventory, source inputs, or assertions")
    return ledger


def manifest_identity(raw: bytes, path: str) -> dict:
    try:
        manifest = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=unique_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        fail(f"invalid tagged manifest {path}: {error}")
    return {"path": path, "sha256": hashlib.sha256(raw).hexdigest(),
            "id": manifest.get("id", manifest.get("suite", {}).get("name"))}


def validate_manifest_set(data: dict, manifests: dict[str, bytes]) -> list[dict]:
    identities = []
    for path in data["manifest_paths"]:
        if path not in manifests:
            fail(f"missing fixture/corpus manifest: {path}")
        identity = manifest_identity(manifests[path], path)
        if identity["sha256"] != data["manifest_sha256"][path]:
            fail(f"fixture/corpus manifest digest mismatch: {path}")
        identities.append(identity)
    corpus = json.loads(manifests["fixtures/mooneye/manifest.json"].decode("utf-8"))
    eligible = [fixture["id"] for fixture in corpus.get("fixtures", []) if fixture.get("eligible") is True]
    if eligible != CASE_IDS:
        fail("eligible corpus order or denominator differs from the pinned manifest")
    if corpus.get("suite", {}).get("revision") != data["corpus_revision"]:
        fail("corpus revision differs from the pinned manifest")
    return identities


def git(*args: str, cwd: pathlib.Path = ROOT) -> bytes:
    try:
        return subprocess.check_output(["git", *args], cwd=cwd, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        fail(f"git {' '.join(args)} failed: {error.stderr.decode(errors='replace').strip()}")


def tagged_file(repo_root: pathlib.Path, tag: str, relative: str, limit: int) -> bytes:
    relative_path(relative, "tagged-input-path-invalid")
    raw = git("show", f"{tag}:{relative}", cwd=repo_root)
    if len(raw) > limit:
        fail("tagged-input-too-large:" + relative)
    return raw


def build_v2_sidecar(tag: str, source_sha: str, repo_root: pathlib.Path,
                     ledger: str, ledger_raw: bytes, data: dict,
                     receipt_path: pathlib.Path | None) -> dict:
    if receipt_path is None:
        fail("schema-2 sidecars require --receipt PATH")
    try:
        if not receipt_path.is_absolute():
            receipt_path = repo_root / receipt_path
        receipt_path = receipt_path.resolve(strict=True)
        if EVIDENCE_ONLY:
            receipt_rel = data.get("receipt", {}).get("path")
        else:
            receipt_rel = receipt_path.relative_to(repo_root.resolve()).as_posix()
    except (OSError, ValueError):
        fail("receipt path must stay inside the tagged repository")
    if receipt_rel != data.get("receipt", {}).get("path"):
        fail("receipt path differs from the tracked ledger identity")

    tagged_inputs = {}
    source_rows = data.get("source_inputs")
    if type(source_rows) is not list or not source_rows:
        fail("tagged support ledger has no covered source inputs")
    for row in source_rows:
        if type(row) is not dict:
            fail("tagged source input identity is malformed")
        name = relative_path(row.get("path"))
        raw = tagged_file(repo_root, tag, name, MAX_INPUT_BYTES)
        if sha256(raw) != row.get("sha256") or len(raw) != row.get("size_bytes"):
            fail("tagged source input differs from ledger:" + name)
        tagged_inputs[name] = raw
    inventory_path = data["inventory"]["path"]
    inventory_raw = tagged_inputs.get(inventory_path)
    if inventory_raw is None or sha256(inventory_raw) != data["inventory"]["sha256"]:
        fail("tagged independent inventory identity mismatch")
    inventory = strict_json(inventory_raw, "tagged-inventory")
    for section in ("manifest_identities", "disposition_identities"):
        for row in data[section]:
            raw = tagged_inputs.get(row["path"])
            if raw is None or sha256(raw) != row["sha256"] or len(raw) != row["size_bytes"]:
                fail("tagged " + section.removesuffix("_identities") + " identity mismatch:" + row["path"])
            strict_json(raw, "tagged-input:" + row["path"])

    receipt_raw = bounded_file(receipt_path, MAX_RECEIPT_BYTES, "receipt")
    receipt = strict_json(receipt_raw, "receipt")
    identity = _validate_run_identity(receipt, sha256(inventory_raw))
    producer_revision = identity["core_revision"]
    check_source_ancestry(producer_revision, source_sha, repo_root)
    derived = build_v2_data(receipt, receipt_raw, inventory, inventory_raw,
                            repo_root, receipt_rel, tagged_inputs)
    validate_data_v2(data, "0.2.0")
    validate_data_v2(derived, "0.2.0")
    if stable_v2_evidence(derived) != stable_v2_evidence(data):
        fail("tagged ledger stable evidence differs from complete receipt or tagged source inputs")
    validate_source_bindings(derived, repo_root, tagged_inputs)
    head = git("rev-parse", "HEAD", cwd=repo_root).decode("ascii", "strict").strip()
    if head == source_sha:
        run_inventory_validator(repo_root)
        run_existing_receipt_validator(receipt_path, inventory, repo_root, source_sha,
                                       inventory_raw, tagged_inputs)

    blob_oid = git("rev-parse", f"{tag}:{ledger}", cwd=repo_root).decode().strip()
    relation = "exact" if producer_revision == source_sha else "ancestor"
    return {
        "schema_version": 2,
        "version": tag[1:],
        "tag": tag,
        "source_sha": source_sha,
        "ledger_version": data["version"],
        "ledger": {"path": ledger, "git_blob_oid": blob_oid,
                   "sha256": sha256(ledger_raw)},
        "manifest_identities": data["manifest_identities"],
        "inventory_sha256": data["inventory"]["sha256"],
        "disposition_identities": data["disposition_identities"],
        "corpus_receipt_sha256": derived["receipt"]["sha256"],
        "corpus_receipt_producer_revision": producer_revision,
        "corpus_receipt_source_relation": relation,
        "corpus_receipt_identity_sha256": derived["receipt"]["identity_sha256"],
        "corpus_receipt_input_identity_sha256": derived["receipt"]["input_identity_sha256"],
        "corpus_receipt_run_id": derived["receipt"]["run_id"],
        "corpus_run": derived["receipt"]["run"],
        "corpus_receipt_build_artifacts": derived["receipt"]["build_artifacts"],
        "covered_source_inputs": data["source_inputs"],
        "suite_model_mode_counts": data["receipt"]["suite_model_mode_counts"],
        "case_counts": data["receipt"]["counts"],
        "game_evidence": data["game_evidence"],
        "self_hash": None,
    }


def build_sidecar(tag: str, source_sha: str, repo_root: pathlib.Path = ROOT,
                  receipt_path: pathlib.Path | None = None) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        fail("source SHA must be a full lowercase Git commit SHA")
    actual_sha = git("rev-parse", f"{tag}^{{commit}}", cwd=repo_root).decode().strip()
    if actual_sha != source_sha:
        fail("supplied source SHA does not resolve from the requested tag")
    names = git("ls-tree", "--name-only", f"{tag}:{LEDGER_DIR}", cwd=repo_root).decode().split()
    ledger = select_ledger(names, tag)
    ledger_raw = git("show", f"{tag}:{ledger}", cwd=repo_root)
    data = parse_ledger(ledger_raw, ledger_version(ledger))
    if data.get("schema_version") == 2:
        return build_v2_sidecar(tag, source_sha, repo_root, ledger, ledger_raw, data, receipt_path)
    if receipt_path is not None:
        fail("--receipt is only accepted for schema-2 support ledgers")
    manifests = {path: git("show", f"{tag}:{path}", cwd=repo_root) for path in data["manifest_paths"]}
    identities = validate_manifest_set(data, manifests)
    blob_oid = git("rev-parse", f"{tag}:{ledger}", cwd=repo_root).decode().strip()
    return {
        "schema_version": 1,
        "version": tag[1:],
        "ledger_version": data["version"],
        "tag": tag,
        "source_sha": source_sha,
        "ledger": {"path": ledger, "git_blob_oid": blob_oid,
                   "sha256": hashlib.sha256(ledger_raw).hexdigest()},
        "fixture_manifest_identities": identities,
        "corpus_revision": data["corpus_revision"],
        "eligible_denominator": data["eligible_denominator"],
        "executed_denominator": data["executed_denominator"],
        "executed_cases": data["executed_cases"],
        "failures": data["failures"],
        "known_issues": data["known_issues"],
        "fixture_classes": data["fixture_classes"],
        "limitations": data["limitations"],
        "physical_dmg_observations": data["physical_dmg_observations"],
        "broad_game_claim": False,
        "self_hash": None,
    }


def verify_sidecar_data(observed: dict, expected: dict) -> None:
    if not isinstance(observed, dict) or observed != expected:
        fail("sidecar source SHA, tagged ledger blob, or fixture/corpus identity differs from the tag")


def _schema2_test_data() -> dict:
    source_raw = b"input"
    binary_raw = b"binary"
    evidence_raw = b"identity"
    bindings = []
    observations = []
    for case_id, expected_failure, observed, status, matched, signature, assertion_id in (
        ("case-a", False, "pass", "pass", False, None, "case-a:assertion-a"),
        ("case-b", True, "fail", "xfail", True, "1" * 64, "case-b:assertion-b"),
    ):
        assertion = {
            "id": assertion_id,
            "expected_disposition": "pass",
            "observed_result": observed,
            "evaluator_status": status,
        }
        if signature:
            assertion["signature_sha256"] = signature
        binding = {
            "id": case_id,
            "suite": "age",
            "model": V2_MODEL,
            "mode": "native",
            "speed": "normal",
            "test_name": "test_" + case_id,
            "source_id": case_id,
            "source_path": "src/" + case_id,
            "source_revision": "a" * 40,
            "output_id": case_id,
            "output_path": "fixtures/" + case_id,
            "output_sha256": "b" * 64,
            "assertion_ids": [assertion_id],
            "expected_failure": expected_failure,
            "disposition_state": "expected-failure" if expected_failure else "pass",
            "disposition_value": "expected-failure:fixture" if expected_failure else "pass",
            "expected_signature_sha256": signature,
        }
        producer_case = {
            "id": case_id,
            "suite": "age",
            "model": V2_MODEL,
            "mode": "native",
            "speed": "normal",
            "test_name": "test_" + case_id,
            "attempted": True,
            "completed": True,
            "observed_result": observed,
            "evaluator_status": status,
            "matched_xfail": matched,
            "evaluator_disposition": binding["disposition_value"],
            "assertions": [assertion],
            "evidence": {"source_id": case_id, "source_path": "src/" + case_id,
                         "source_revision": "a" * 40, "output_id": case_id,
                         "output_path": "fixtures/" + case_id, "output_sha256": "b" * 64,
                         "manifest_ref": "fixtures/manifest.json"},
            "details": {},
        }
        bindings.append(binding)
        observations.append({
            "id": case_id,
            "suite": "age",
            "model": V2_MODEL,
            "mode": "native",
            "speed": "normal",
            "test_name": producer_case["test_name"],
            "boot": "skipped",
            "attempted": True,
            "executed": True,
            "excluded": False,
            "observed_result": observed,
            "evaluator_status": status,
            "matched_xfail": matched,
            "expected_failure": expected_failure,
            "evidence": producer_case["evidence"],
            "details": {},
            "assertions": [assertion],
            "case_sha256": canonical_sha256(producer_case),
            "assertion_signatures_sha256": canonical_sha256([assertion]),
            "producer_case": producer_case,
        })
    identities = [
        *[{"path": path, "size_bytes": len(evidence_raw), "sha256": sha256(evidence_raw)}
          for path in V2_MANIFEST_PATHS],
        *[{"path": path, "size_bytes": len(evidence_raw), "sha256": sha256(evidence_raw)}
          for path in V2_DISPOSITION_PATHS],
        {"path": "tests/external/cgb-corpus-inventory.json", "size_bytes": len(evidence_raw),
         "sha256": sha256(evidence_raw)},
    ]
    source_inputs = sorted([
        {"path": "tests/input.dat", "size_bytes": len(source_raw), "sha256": sha256(source_raw)},
        *identities,
    ], key=lambda row: row["path"])
    suite_counts = _count_suite_model_modes(bindings, observations)
    counts = _count_receipt_cases(observations)
    return {
        "schema_version": 2,
        "version": "0.2.0",
        "game_evidence": {"status": "absent", "statement": "No CGB game-level evidence exists"},
        "scope": {"models": ["CGB-CPU-E", "DMG-CPU-B"], "corpus_model": "CGB-CPU-E",
                  "modes": ["compat", "native"], "boot": "skipped",
                  "physical_cgb_e": "UNKNOWN/POLICY"},
        "source_inputs": source_inputs,
        "manifest_identities": [row for row in identities if row["path"] in V2_MANIFEST_PATHS],
        "disposition_identities": [row for row in identities if row["path"] in V2_DISPOSITION_PATHS],
        "inventory": {"path": "tests/external/cgb-corpus-inventory.json",
                      "sha256": sha256(evidence_raw),
                      "required_case_count": 2, "case_ids": ["case-a", "case-b"],
                      "case_bindings": bindings,
                      "source_candidates_by_suite": {"age": {"discovered": 2, "required": 2, "excluded": 0}},
                      "admitted_outputs": 2, "outputs_outside_required_case_set": 0},
        "receipt": {"path": "build/cgb-corpus-receipt.json", "sha256": "f" * 64,
                    "identity_sha256": "0" * 64, "input_identity_sha256": "1" * 64,
                    "source_inputs_sha256": canonical_sha256(source_inputs), "run_id": "2" * 64,
                    "producer_revision": "5" * 40,
                    "model": "CGB-CPU-E selected software model", "hardware_qualified": False,
                    "run": {"id": "2" * 64, "ctest_cases": 3, "ctest_total_cases": 1133,
                            "ctest_log_sha256": "3" * 64, "run_nonce_sha256": "4" * 64},
                    "counts": counts, "suite_model_mode_counts": suite_counts,
                    "case_ids": ["case-a", "case-b"], "case_observations": observations,
                    "build_artifacts": [{"path": "build/bin.dat", "size_bytes": len(binary_raw),
                                         "sha256": sha256(binary_raw)}]},
    }


def self_test_v2() -> None:
    """Exercise schema-2 acceptance and the production validator's named controls."""
    data = _schema2_test_data()
    evidence_raw = b"identity"
    validate_data_v2(data, "0.2.0", expected_case_count=2)
    controls = []
    positive_checks = ["complete-schema2-fixture"]

    def below_selected_total(value: dict) -> None:
        value["receipt"]["run"]["ctest_total_cases"] = 2

    try:
        altered = copy.deepcopy(data)
        below_selected_total(altered)
        validate_data_v2(altered, "0.2.0", expected_case_count=2)
    except ValueError as error:
        if "mismatched denominator" not in str(error):
            fail("below-selected CTest total produced the wrong diagnostic")
        controls.append("ctest-total-below-selected")
    else:
        fail("self-test accepted a CTest total below its selected corpus stream")

    altered = copy.deepcopy(data)
    altered["receipt"]["run"]["ctest_total_cases"] = "1133"
    try:
        validate_data_v2(altered, "0.2.0", expected_case_count=2)
    except ValueError as error:
        if "mismatched denominator" not in str(error):
            fail("non-integer CTest total produced the wrong diagnostic")
        controls.append("ctest-total-noninteger")
    else:
        fail("self-test accepted a non-integer CTest total")

    def rejected(name: str, mutate, expected: str) -> None:
        altered = copy.deepcopy(data)
        mutate(altered)
        try:
            validate_data_v2(altered, "0.2.0", expected_case_count=2)
        except ValueError as error:
            if expected not in str(error):
                fail("self-test control has wrong diagnostic:" + name + ":" + str(error))
            controls.append(name)
        else:
            fail("self-test mutation was accepted:" + name)

    rejected("empty-inventory", lambda value: value["inventory"].update(case_ids=[]),
             "required inventory membership")
    rejected("null-inventory", lambda value: value["inventory"].update(case_ids=None),
             "required inventory membership")
    rejected("narrowed-inventory", lambda value: value["inventory"].update(case_ids=["case-a"]),
             "incomplete or narrowed")
    rejected("duplicate-inventory-id", lambda value: value["inventory"].update(case_ids=["case-a", "case-a"]),
             "duplicated")
    rejected("missing-required-case", lambda value: value["receipt"]["case_observations"].pop(),
             "case membership")

    def xfail_as_pass(value: dict) -> None:
        row = value["receipt"]["case_observations"][1]
        row.update(observed_result="pass", evaluator_status="pass", matched_xfail=False)
        row["producer_case"].update(observed_result="pass", evaluator_status="pass", matched_xfail=False)
        row["case_sha256"] = canonical_sha256(row["producer_case"])
        row["assertion_signatures_sha256"] = canonical_sha256(row["assertions"])
        value["receipt"]["counts"] = _count_receipt_cases(value["receipt"]["case_observations"])
        value["receipt"]["suite_model_mode_counts"] = _count_suite_model_modes(
            value["inventory"]["case_bindings"], value["receipt"]["case_observations"])

    rejected("xfail-as-pass", xfail_as_pass, "unexpected pass or unmatched expected failure")

    def missing_assertion(value: dict) -> None:
        row = value["receipt"]["case_observations"][0]
        row["assertions"] = []
        row["producer_case"]["assertions"] = []
        row["case_sha256"] = canonical_sha256(row["producer_case"])
        row["assertion_signatures_sha256"] = canonical_sha256([])
        value["receipt"]["counts"] = _count_receipt_cases(value["receipt"]["case_observations"])
        value["receipt"]["suite_model_mode_counts"] = _count_suite_model_modes(
            value["inventory"]["case_bindings"], value["receipt"]["case_observations"])

    rejected("missing-assertion", missing_assertion, "assertion membership is missing")

    def changed_signature(value: dict) -> None:
        row = value["receipt"]["case_observations"][1]
        row["assertions"][0]["signature_sha256"] = "9" * 64
        row["producer_case"]["assertions"][0]["signature_sha256"] = "9" * 64
        row["case_sha256"] = canonical_sha256(row["producer_case"])
        row["assertion_signatures_sha256"] = canonical_sha256(row["assertions"])

    rejected("changed-assertion-signature", changed_signature, "expected failure signature changed")
    rejected("unexpected-pass", xfail_as_pass, "unexpected pass or unmatched expected failure")

    try:
        strict_json(b"{\"id\":1,\"id\":2}", "self-test")
    except ValueError as error:
        if "duplicate JSON key" not in str(error):
            fail("duplicate-key control produced the wrong diagnostic")
        controls.append("duplicate-json-key")
    else:
        fail("self-test accepted duplicate JSON keys")
    try:
        strict_json(b"\xff", "self-test")
    except ValueError as error:
        if "invalid-json-or-duplicate-key" not in str(error):
            fail("malformed UTF-8 control produced the wrong diagnostic")
        controls.append("malformed-utf8")
    else:
        fail("self-test accepted malformed UTF-8")

    composed, decomposed = "caf\u00e9", "cafe\u0301"
    if composed == decomposed or sha256(composed.encode("utf-8")) == sha256(decomposed.encode("utf-8")):
        fail("self-test Unicode identity was normalized")
    if _sorted_unique_strings(sorted([composed, decomposed]), "Unicode IDs changed") != sorted([composed, decomposed]):
        fail("self-test exact decoded IDs were changed")
    positive_checks.append("exact-unicode-id-and-byte-digest")

    with tempfile.TemporaryDirectory(prefix="gabbaboy-support-ledger-inputs-") as temporary:
        temp_root = pathlib.Path(temporary)
        (temp_root / "tests").mkdir()
        (temp_root / "build").mkdir()
        (temp_root / "tests/input.dat").write_bytes(b"input")
        (temp_root / "build/bin.dat").write_bytes(b"binary")
        for row in data["source_inputs"]:
            if row["path"] == "tests/input.dat":
                continue
            destination = temp_root / row["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(evidence_raw)
        validate_source_bindings(data, temp_root)
        (temp_root / "tests/input.dat").write_bytes(b"changed")
        try:
            validate_source_bindings(data, temp_root)
        except ValueError as error:
            if "source input is stale" not in str(error):
                fail("stale-source control produced the wrong diagnostic")
            controls.append("stale-source-input")
        else:
            fail("self-test accepted stale source input")
        (temp_root / "tests/input.dat").write_bytes(b"input")
        (temp_root / "build/bin.dat").write_bytes(b"changed")
        try:
            validate_source_bindings(data, temp_root)
        except ValueError as error:
            if "build input is stale" not in str(error):
                fail("stale-build control produced the wrong diagnostic")
            controls.append("stale-build-artifact")
        else:
            fail("self-test accepted stale build artifact")
    if not controls:
        fail("self-test selected zero rejection controls")
    print("support ledger v0.2 self-test passed: positive=" + str(len(positive_checks)) +
          " rejected_controls=" + str(len(controls)) +
          " controls=" + ",".join(controls))


def self_test() -> None:
    ledger = working_tree_ledger()
    current = ledger_version(ledger)
    raw = (ROOT / ledger).read_bytes()
    data = parse_ledger(raw, current)
    manifests = {path: (ROOT / path).read_bytes() for path in data["manifest_paths"]}
    validate_manifest_set(data, manifests)
    mutations = [
        raw + b"\nsource_sha: 0123456789012345678901234567890123456789\n",
        raw.replace(b'"executed_denominator": 3', b'"executed_denominator": 2'),
        raw.replace(f'"version": "{current}"'.encode(), b'"version": "9.9.9"'),
        raw.replace(b'"broad_game_claim": false', b'"broad_game_claim": true'),
        raw.replace(b'"status": "pass"', b'"status": "pass", "status": "fail"', 1),
        raw.replace(b'mooneye-acceptance-timer-tim00-div-trigger', b'mooneye-acceptance-timer-tim00'),
        raw.replace(b'"corpus_revision": "31510e12eea6286d36eea060a6adde755e1067aa"',
                    b'"corpus_revision": "21510e12eea6286d36eea060a6adde755e1067aa"'),
        raw.replace(b'"fixtures/tracer/manifest.json": "5928', b'"fixtures/tracer/manifest.json": "0928'),
        raw + b"\xff",
    ]
    for changed in mutations:
        try:
            altered = parse_ledger(changed, current)
            validate_manifest_set(altered, manifests)
        except (ValueError, KeyError):
            continue
        fail("self-test mutation was accepted")
    try:
        mismatched = dict(manifests)
        mismatched["fixtures/tracer/manifest.json"] += b"tamper"
        validate_manifest_set(data, mismatched)
    except (ValueError, KeyError):
        pass
    else:
        fail("self-test accepted altered tagged manifest bytes")
    names = ["v0.1.0.md", "v0.2.0.md", "README.md"]
    for tag, expected in (("v0.1.0", "v0.1.0.md"), ("v0.1.1", "v0.1.0.md"), ("v0.1.10", "v0.1.0.md"),
                          ("v0.2.0", "v0.2.0.md"), ("v0.2.1", "v0.2.0.md")):
        if select_ledger(names, tag) != f"{LEDGER_DIR}/{expected}":
            fail(f"self-test selected the wrong ledger for {tag}")
    for tag in ("v0.0.9", "v0.1", "0.1.1", "v0.1.1-rc1", "v1.0.0"):
        try:
            select_ledger(names, tag)
        except ValueError:
            continue
        fail(f"self-test accepted tag without an applicable ledger: {tag}")
    for missing_names, tag in ((["v0.1.0.md"], "v0.2.0"),
                               (["v0.1.0.md"], "v0.2.1")):
        try:
            select_ledger(missing_names, tag)
        except ValueError:
            continue
        fail("self-test allowed exact-ledger or cross-scope fallback")
    fixture_sidecar = {"tag": "v0.1.0", "source_sha": "a" * 40,
                       "ledger_sha256": hashlib.sha256(raw).hexdigest(),
                       "manifest_sha256": data["manifest_sha256"]}
    for key, value in (("source_sha", "b" * 40), ("ledger_sha256", "0" * 64),
                       ("manifest_sha256", {"fixtures/tracer/manifest.json": "0" * 64})):
        altered = dict(fixture_sidecar)
        altered[key] = value
        try:
            verify_sidecar_data(altered, fixture_sidecar)
        except ValueError:
            continue
        fail("self-test accepted altered sidecar identity")
    with tempfile.TemporaryDirectory(prefix="gabbaboy-support-ledger-") as temporary:
        repository = pathlib.Path(temporary)
        for relative in [ledger, *data["manifest_paths"]]:
            destination = repository / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        environment = dict(os.environ)
        environment.update({"GIT_AUTHOR_NAME": "GabbaBoy Test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
                            "GIT_COMMITTER_NAME": "GabbaBoy Test", "GIT_COMMITTER_EMAIL": "test@example.invalid"})
        subprocess.run(["git", "init", "-q"], cwd=repository, env=environment, check=True)
        subprocess.run(["git", "add", ledger, *data["manifest_paths"]],
                       cwd=repository, env=environment, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=repository,
                       env=environment, check=True)
        fake_sha = git("rev-parse", "HEAD", cwd=repository).decode().strip()
        patch_tag = "v{}.{}.{}".format(*(int(part) + (index == 2) for index, part in enumerate(current.split("."))))
        for tag in (f"v{current}", patch_tag):
            subprocess.run(["git", "tag", tag, fake_sha], cwd=repository, env=environment, check=True)
        generated = build_sidecar(f"v{current}", fake_sha, repository)
        if generated["source_sha"] != fake_sha or generated["ledger"]["sha256"] != hashlib.sha256(raw).hexdigest():
            fail("self-test generated sidecar does not bind exact source and ledger bytes")
        patch = build_sidecar(patch_tag, fake_sha, repository)
        if (patch["tag"], patch["version"], patch["ledger_version"]) != (patch_tag, patch_tag[1:], current) \
                or patch["ledger"] != generated["ledger"]:
            fail("self-test patch release did not bind the unchanged lower ledger")
        for key in ("source_sha", "ledger", "fixture_manifest_identities"):
            altered = dict(generated)
            altered[key] = None
            try:
                verify_sidecar_data(altered, generated)
            except ValueError:
                continue
            fail(f"self-test accepted altered sidecar {key}")
    print("support ledger self-test passed: tagged sidecar binding, newest-applicable ledger selection, scope, corpus order, digests, malformed UTF-8, duplicate keys, denominator and claim controls")


def self_test_static_ledger() -> None:
    """Drive check_ledger_static through its production entry over a private copy of the covered inputs."""
    ledger_rel = "docs/support/v0.2.0.md"
    ledger = parse_ledger(bounded_file(ROOT / ledger_rel, MAX_LEDGER_BYTES, "ledger"), "0.2.0")
    rows = ledger["source_inputs"]
    if not rows:
        fail("static ledger self-test has no covered source inputs")
    with tempfile.TemporaryDirectory(prefix="gabbaboy-static-ledger-") as temporary:
        copy_root = pathlib.Path(temporary)
        for relative in [ledger_rel] + [row["path"] for row in rows]:
            target = copy_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        check_ledger_static(copy_root, run_inventory=False)
        controls = 0
        victim = copy_root / rows[0]["path"]
        original = victim.read_bytes()
        victim.write_bytes(original + b"\n")
        try:
            check_ledger_static(copy_root, run_inventory=False)
        except ValueError as error:
            if "source input is stale" not in str(error):
                fail("static ledger control rejected a changed covered input for the wrong reason: " + str(error))
            controls += 1
        else:
            fail("static ledger accepted a changed covered source input")
        victim.write_bytes(original)
        victim.unlink()
        try:
            check_ledger_static(copy_root, run_inventory=False)
        except (ValueError, OSError):
            controls += 1
        else:
            fail("static ledger accepted a missing covered source input")
        victim.write_bytes(original)
        (copy_root / ledger_rel).write_bytes(b"not a ledger\n")
        try:
            check_ledger_static(copy_root, run_inventory=False)
        except ValueError:
            controls += 1
        else:
            fail("static ledger accepted an unparseable ledger")
    if controls != 3:
        fail("static ledger self-test did not run all of its controls")
    print("support ledger static self-test passed: positive=1 rejected_controls=3 controls=changed-covered-input,missing-covered-input,unparseable-ledger")


def self_test_v2_sidecar() -> None:
    """Exercise full-membership sidecars without relying on ignored build outputs."""
    global EVIDENCE_ONLY
    ledger_path = ROOT / "docs/support/v0.2.0.md"
    ledger_raw = bounded_file(ledger_path, MAX_LEDGER_BYTES, "ledger")
    data = parse_ledger(ledger_raw, "0.2.0")
    validate_data_v2(data, "0.2.0")
    receipt_path = pathlib.Path("build/cgb-corpus-receipt.json")
    base_revision = current_git_revision()
    source_bytes = {}
    for row in data["source_inputs"]:
        raw = git("show", f"{base_revision}:{row['path']}")
        if sha256(raw) != row["sha256"] or len(raw) != row["size_bytes"]:
            fail("self-test tagged source differs from the tracked ledger:" + row["path"])
        source_bytes[row["path"]] = raw
    inventory_raw = source_bytes[data["inventory"]["path"]]
    inventory = strict_json(inventory_raw, "self-test-inventory")
    author_env = dict(os.environ)
    author_env.update({
        "GIT_AUTHOR_NAME": "GabbaBoy Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "GabbaBoy Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    })
    controls = []
    positive_checks = []

    def git_fixture(repo: pathlib.Path, *args: str) -> str:
        completed = subprocess.run(["git", *args], cwd=repo, env=author_env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, check=False, timeout=30)
        if completed.returncode != 0:
            fail("self-test Git fixture command failed: " + completed.stderr.strip())
        return completed.stdout.strip()

    def expect_rejected(name: str, action, expected: str) -> None:
        try:
            action()
        except ValueError as error:
            if expected not in str(error):
                fail("v0.2 sidecar control has wrong diagnostic:" + name + ":" + str(error))
            controls.append(name)
            return
        fail("v0.2 sidecar control was accepted:" + name)

    with tempfile.TemporaryDirectory(prefix="gabbaboy-v2-sidecar-") as temporary:
        temp_root = pathlib.Path(temporary)
        repository = temp_root / "tagged-repository"
        completed = subprocess.run(["git", "clone", "--shared", "--no-tags", "--no-checkout",
                                    str(ROOT), str(repository)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, check=False, timeout=60)
        if completed.returncode != 0:
            fail("v0.2 sidecar fixture clone failed: " + completed.stderr.strip())
        git_fixture(repository, "checkout", "-b", "support-ledger-v2-self-test", base_revision)
        destination_receipt = repository / receipt_path
        destination_receipt.parent.mkdir(parents=True, exist_ok=True)

        def make_receipt(run_key: str) -> tuple[dict, bytes, dict[str, bytes]]:
            build_artifacts = []
            artifact_bytes = {}
            for old in data["receipt"]["build_artifacts"]:
                relative = old["path"]
                raw = ("synthetic sidecar contract artifact\n" + run_key + "\n" + relative + "\n").encode()
                artifact_bytes[relative] = raw
                build_artifacts.append({"path": relative, "size_bytes": len(raw), "sha256": sha256(raw)})
                destination = repository / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(raw)

            run_id = sha256(("synthetic-run:" + run_key).encode("ascii"))
            run_nonce_sha256 = sha256(("synthetic-nonce:" + run_key).encode("ascii"))
            log_sha256 = sha256(("synthetic-ctest-log:" + run_key).encode("ascii"))
            bindings = data["inventory"]["case_bindings"]
            case_names = sorted(row["test_name"] for row in bindings)
            identity = {
                "core_revision": base_revision,
                "run_id": run_id,
                "input_identity_sha256": sha256(("synthetic-input-identity:" + run_key).encode("ascii")),
                "inventory_sha256": sha256(inventory_raw),
                "hardware_qualified": False,
                "model": "CGB-CPU-E selected software model",
                "case_ids": data["inventory"]["case_ids"],
                "assertion_ids": {row["id"]: row["assertion_ids"] for row in bindings},
                "case_ctest_names": case_names,
                "aggregate_ctest_names": ["cgb_samesuite_apu_suite"],
                "ctest_names": sorted([*case_names, "cgb_samesuite_apu_suite"]),
                "ctest_log_sha256": log_sha256,
                "input_hashes": data["source_inputs"],
                "build_artifacts": build_artifacts,
            }
            identity["identity_sha256"] = canonical_sha256(identity)
            receipt = {
                "schema": "gabbaboy-cgb-corpus-receipt-v1",
                "version": 1,
                "status": "complete",
                "failure_codes": [],
                "identity": identity,
                "run": {
                    "id": run_id,
                    "started_at_ns": 100,
                    "completed_at_ns": 200,
                    "ctest_cases": V2_REQUIRED_CASES + 1,
                    "ctest_total_cases": 1133,
                    "ctest_log_sha256": log_sha256,
                    "run_nonce_sha256": run_nonce_sha256,
                },
                "cases": [copy.deepcopy(row["producer_case"])
                          for row in data["receipt"]["case_observations"]],
            }
            raw = json.dumps(receipt, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True).encode("utf-8") + b"\n"
            destination_receipt.write_bytes(raw)
            return receipt, raw, artifact_bytes

        receipt, receipt_raw, first_artifact_bytes = make_receipt("first-independent-run")
        fixture_data = build_v2_data(receipt, receipt_raw, inventory, inventory_raw,
                                     repository, receipt_path.as_posix(), source_bytes)
        validate_data_v2(fixture_data, "0.2.0")
        if stable_v2_evidence(fixture_data) != stable_v2_evidence(data):
            fail("synthetic full-membership receipt differs from stable historical evidence")
        ledger_text = render_v2_ledger(fixture_data)
        fixture_ledger = repository / "docs/support/v0.2.0.md"
        fixture_ledger.parent.mkdir(parents=True, exist_ok=True)
        fixture_ledger.write_text(ledger_text, encoding="utf-8")
        git_fixture(repository, "add", "docs/support/v0.2.0.md")
        git_fixture(repository, "commit", "-m", "test: create complete v0.2 sidecar contract fixture")
        source_sha = git_fixture(repository, "rev-parse", "HEAD")
        for tag in ("v0.2.0", "v0.2.1"):
            git_fixture(repository, "tag", tag, source_sha)
        # Keep HEAD at the receipt producer's base revision so this synthetic
        # contract fixture cannot be mistaken for a CTest execution receipt.
        git_fixture(repository, "checkout", "--detach", base_revision)

        generated = build_sidecar("v0.2.0", source_sha, repository, receipt_path)
        if (generated.get("schema_version") != 2 or
                generated.get("ledger", {}).get("path") != "docs/support/v0.2.0.md" or
                generated.get("corpus_receipt_sha256") != sha256(receipt_raw) or
                generated.get("corpus_receipt_sha256") == data["receipt"]["sha256"] or
                generated.get("corpus_receipt_producer_revision") != receipt["identity"]["core_revision"] or
                generated.get("corpus_receipt_identity_sha256") != receipt["identity"]["identity_sha256"] or
                generated.get("corpus_receipt_input_identity_sha256") != receipt["identity"]["input_identity_sha256"] or
                generated.get("corpus_receipt_run_id") != receipt["run"]["id"] or
                generated.get("corpus_run") != fixture_data["receipt"]["run"] or
                generated.get("corpus_receipt_build_artifacts") != fixture_data["receipt"]["build_artifacts"] or
                generated.get("corpus_receipt_source_relation") != "ancestor" or
                generated.get("game_evidence") != data["game_evidence"]):
            fail("v0.2 sidecar positive fixture did not bind the exact tagged inputs")
        positive_checks.append("positive-v0.2-tagged-sidecar")

        second_receipt, second_raw, second_artifact_bytes = make_receipt("second-independent-run")
        second_sidecar = build_sidecar("v0.2.0", source_sha, repository, receipt_path)
        if (second_sidecar.get("corpus_receipt_sha256") != sha256(second_raw) or
                second_sidecar.get("corpus_receipt_sha256") == generated.get("corpus_receipt_sha256") or
                second_sidecar.get("corpus_receipt_run_id") == generated.get("corpus_receipt_run_id") or
                second_sidecar.get("corpus_receipt_build_artifacts") == generated.get("corpus_receipt_build_artifacts")):
            fail("independent fresh receipt provenance was not rebound to its supplied bytes and artifacts")
        positive_checks.append("independent-run-stable-ledger-and-fresh-provenance")

        patch_sidecar = build_sidecar("v0.2.1", source_sha, repository, receipt_path)
        if (patch_sidecar.get("ledger") != second_sidecar.get("ledger") or
                patch_sidecar.get("tag") != "v0.2.1" or
                patch_sidecar.get("corpus_receipt_sha256") != second_sidecar.get("corpus_receipt_sha256")):
            fail("v0.2 patch tag did not reuse its same-scope ledger")
        positive_checks.append("v0.2-patch-compatibility")

        # Downloaded-evidence verification (publish job): the receipt is an asset outside the checkout and
        # the producer's build files are absent. Only this opt-in mode accepts that; a present but altered
        # build file, and an outside receipt without the opt-in, are still rejected.
        outside_receipt = temp_root / "downloaded" / "cgb-corpus-receipt.json"
        outside_receipt.parent.mkdir()
        outside_receipt.write_bytes(second_raw)
        expect_rejected("receipt-outside-checkout-without-evidence-only",
                        lambda: build_sidecar("v0.2.0", source_sha, repository, outside_receipt),
                        "receipt path must stay inside the tagged repository")
        build_files = {row["path"]: (repository / row["path"]).read_bytes()
                       for row in second_receipt["identity"]["build_artifacts"]}
        for relative in build_files:
            (repository / relative).unlink()
        destination_receipt.unlink()
        try:
            expect_rejected("absent-build-without-evidence-only",
                            lambda: build_sidecar("v0.2.0", source_sha, repository, outside_receipt),
                            "receipt path must stay inside the tagged repository")
            EVIDENCE_ONLY = True
            downloaded = build_sidecar("v0.2.0", source_sha, repository, outside_receipt)
            if downloaded != second_sidecar:
                fail("downloaded-evidence verification did not reproduce the producer's sidecar")
            positive_checks.append("downloaded-evidence-without-build")
            tampered = sorted(build_files)[0]
            (repository / tampered).parent.mkdir(parents=True, exist_ok=True)
            (repository / tampered).write_bytes(build_files[tampered] + b"tampered\n")
            expect_rejected("present-build-file-still-checked-in-evidence-only",
                            lambda: build_sidecar("v0.2.0", source_sha, repository, outside_receipt),
                            "build input is stale")
        finally:
            EVIDENCE_ONLY = False
            for relative, raw in build_files.items():
                (repository / relative).parent.mkdir(parents=True, exist_ok=True)
                (repository / relative).write_bytes(raw)
            destination_receipt.write_bytes(second_raw)

        expect_rejected("missing-v2-receipt",
                        lambda: build_sidecar("v0.2.0", source_sha, repository),
                        "schema-2 sidecars require --receipt")
        expect_rejected("wrong-tag-source-sha",
                        lambda: build_sidecar("v0.2.0", "0" * 40, repository, receipt_path),
                        "supplied source SHA does not resolve")
        for key, value in (("source_sha", "0" * 40),
                           ("ledger", {**second_sidecar["ledger"], "git_blob_oid": "0" * 40}),
                           ("corpus_receipt_sha256", "0" * 64),
                           ("inventory_sha256", "0" * 64),
                           ("corpus_receipt_run_id", "0" * 64),
                           ("corpus_receipt_build_artifacts", []),
                           ("disposition_identities", []),
                           ("covered_source_inputs", []),
                           ("suite_model_mode_counts", []),
                           ("game_evidence", {"status": "present"})):
            altered = copy.deepcopy(second_sidecar)
            altered[key] = value
            expect_rejected("altered-sidecar-" + key,
                            lambda altered=altered: verify_sidecar_data(altered, second_sidecar),
                            "sidecar source SHA")

        saved_receipt = destination_receipt.read_bytes()
        changed_bytes = saved_receipt + b" \n"
        destination_receipt.write_bytes(changed_bytes)
        changed_bytes_sidecar = build_sidecar("v0.2.0", source_sha, repository, receipt_path)
        if (changed_bytes_sidecar.get("corpus_receipt_sha256") != sha256(changed_bytes) or
                changed_bytes_sidecar.get("corpus_receipt_sha256") == second_sidecar.get("corpus_receipt_sha256")):
            fail("receipt byte-identity control did not use the supplied receipt bytes")
        expect_rejected("old-sidecar-after-receipt-bytes-change",
                        lambda: verify_sidecar_data(second_sidecar, changed_bytes_sidecar),
                        "sidecar source SHA")
        destination_receipt.write_bytes(saved_receipt)
        positive_checks.append("fresh-receipt-byte-digest")

        changed_outcome = copy.deepcopy(second_receipt)
        passing_case = next(row for row in changed_outcome["cases"]
                            if row["observed_result"] == "pass")
        passing_case.update(observed_result="fail", evaluator_status="xfail", matched_xfail=True)
        changed_outcome_raw = json.dumps(changed_outcome, sort_keys=True,
                                         separators=(",", ":"), ensure_ascii=True).encode() + b"\n"
        destination_receipt.write_bytes(changed_outcome_raw)
        expect_rejected("changed-case-outcome",
                        lambda: build_sidecar("v0.2.0", source_sha, repository, receipt_path),
                        "unexpected failure")
        destination_receipt.write_bytes(saved_receipt)

        changed_assertion = copy.deepcopy(second_receipt)
        assertion_case = changed_assertion["cases"][0]
        assertion = assertion_case["assertions"][0]
        assertion["observed_result"] = "fail" if assertion.get("observed_result") == "pass" else "pass"
        changed_assertion_raw = json.dumps(changed_assertion, sort_keys=True,
                                           separators=(",", ":"), ensure_ascii=True).encode() + b"\n"
        destination_receipt.write_bytes(changed_assertion_raw)
        expect_rejected("changed-assertion-observation",
                        lambda: build_sidecar("v0.2.0", source_sha, repository, receipt_path),
                        "stable evidence differs")
        destination_receipt.write_bytes(saved_receipt)
        artifact_path = next(iter(second_artifact_bytes))
        artifact_file = repository / artifact_path
        artifact_file.write_bytes(second_artifact_bytes[artifact_path] + b"changed")
        expect_rejected("changed-build-artifact-bytes",
                        lambda: build_sidecar("v0.2.0", source_sha, repository, receipt_path),
                        "build input is stale")
        artifact_file.write_bytes(second_artifact_bytes[artifact_path])

        source_path = data["source_inputs"][0]["path"]
        git_fixture(repository, "checkout", "-b", "sidecar-mutated-source", source_sha)
        source_file = repository / source_path
        source_file.write_bytes(source_file.read_bytes() + b"\nself-test source mutation\n")
        git_fixture(repository, "add", source_path)
        git_fixture(repository, "commit", "-m", "test: mutate covered source identity")
        changed_source_sha = git_fixture(repository, "rev-parse", "HEAD")
        git_fixture(repository, "tag", "v0.2.4", changed_source_sha)
        git_fixture(repository, "checkout", "--detach", base_revision)
        expect_rejected("changed-tagged-source-input",
                        lambda: build_sidecar("v0.2.4", changed_source_sha, repository, receipt_path),
                        "tagged source input differs from ledger")

        base_ledger_text = ledger_text

        def tagged_ledger_variant(name: str, tag: str, mutate) -> None:
            branch = "sidecar-" + name
            git_fixture(repository, "checkout", "-b", branch, source_sha)
            variant = copy.deepcopy(data)
            mutate(variant)
            text = base_ledger_text
            start = text.index(BEGIN)
            end = text.index(END, start)
            block_start = text.index("```json", start)
            json_start = text.index("\n", block_start) + 1
            json_end = text.rindex("```", json_start, end)
            rewritten = (text[:json_start] + json.dumps(variant, indent=2, sort_keys=True, ensure_ascii=False) +
                         "\n" + text[json_end:])
            (repository / "docs/support/v0.2.0.md").write_text(rewritten, encoding="utf-8")
            git_fixture(repository, "add", "docs/support/v0.2.0.md")
            git_fixture(repository, "commit", "-m", "test: alter disposition identities")
            variant_sha = git_fixture(repository, "rev-parse", "HEAD")
            git_fixture(repository, "tag", tag, variant_sha)
            git_fixture(repository, "checkout", "--detach", base_revision)
            expect_rejected(name,
                            lambda: build_sidecar(tag, variant_sha, repository, receipt_path),
                            "disposition")

        tagged_ledger_variant("omitted-disposition-identity", "v0.2.2",
                              lambda altered: altered["disposition_identities"].pop())
        tagged_ledger_variant("duplicate-disposition-identity", "v0.2.3",
                              lambda altered: altered["disposition_identities"].append(
                                  copy.deepcopy(altered["disposition_identities"][0])))

    with tempfile.TemporaryDirectory(prefix="gabbaboy-v2-scope-") as temporary:
        repository = pathlib.Path(temporary)
        legacy = repository / "docs/support/v0.1.0.md"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "docs/support/v0.1.0.md", legacy)
        subprocess.run(["git", "init", "-q"], cwd=repository, env=author_env, check=True)
        subprocess.run(["git", "add", "docs/support/v0.1.0.md"], cwd=repository,
                       env=author_env, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=repository,
                       env=author_env, check=True)
        missing_sha = git_fixture(repository, "rev-parse", "HEAD")
        git_fixture(repository, "tag", "v0.2.0", missing_sha)
        git_fixture(repository, "tag", "v0.2.1", missing_sha)
        expect_rejected("missing-exact-v0.2-ledger",
                        lambda: build_sidecar("v0.2.0", missing_sha, repository),
                        "exact v0.2.0 support ledger is missing")
        expect_rejected("cross-scope-fallback",
                        lambda: build_sidecar("v0.2.1", missing_sha, repository),
                        "major/minor scope")

    if not positive_checks:
        fail("v0.2 sidecar self-test selected zero positive checks")
    print("support ledger v0.2 sidecar self-test passed: positive=" +
          str(len(positive_checks)) + " rejected_controls=" + str(len(controls)) +
          " positives=" + ",".join(positive_checks) +
          " controls=" + ",".join(controls))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--self-test-v2", action="store_true")
    parser.add_argument("--tag")
    parser.add_argument("--source-sha")
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--verify-sidecar", type=pathlib.Path)
    parser.add_argument("--check-current", action="store_true")
    parser.add_argument("--check-ledger", action="store_true",
                        help="receipt-free check of the tracked v0.2.0 ledger against its covered source inputs")
    parser.add_argument("--write-current", action="store_true")
    parser.add_argument("--receipt", type=pathlib.Path)
    parser.add_argument("--evidence-only", action="store_true",
                        help="with --verify-sidecar: the receipt is a downloaded asset and the producer's build is absent")
    args = parser.parse_args()
    if args.evidence_only:
        if not args.verify_sidecar:
            parser.error("--evidence-only is only accepted with --verify-sidecar")
        global EVIDENCE_ONLY
        EVIDENCE_ONLY = True
    try:
        if args.self_test_v2:
            self_test_v2()
            return 0
        if args.self_test:
            self_test()
            self_test_v2()
            self_test_v2_sidecar()
            self_test_static_ledger()
            return 0
        if args.check_ledger:
            data = check_ledger_static()
            print("support-ledger static pass version=0.2.0 cases=" +
                  str(data["receipt"]["counts"]["completed_cases"]) +
                  " source-inputs=" + str(len(data["source_inputs"])))
            return 0
        if args.check_current:
            if not args.receipt:
                parser.error("--check-current requires --receipt PATH")
            data = check_current(args.receipt)
            counts = data["receipt"]["counts"]
            print("support-ledger current pass version=0.2.0 cases=" +
                  str(counts["completed_cases"]) +
                  " passes=" + str(counts["observed_pass_cases"]) +
                  " matched-xfails=" + str(counts["matched_xfail_cases"]) +
                  " assertions=" + str(counts["assertions"]))
            return 0
        if args.write_current:
            if not args.receipt:
                parser.error("--write-current requires --receipt PATH")
            data = create_current_ledger(args.receipt)
            counts = data["receipt"]["counts"]
            print("support-ledger wrote version=0.2.0 cases=" +
                  str(counts["completed_cases"]) +
                  " passes=" + str(counts["observed_pass_cases"]) +
                  " matched-xfails=" + str(counts["matched_xfail_cases"]) +
                  " assertions=" + str(counts["assertions"]))
            return 0
        if not (args.tag and args.source_sha and (args.output or args.verify_sidecar)):
            parser.error("supply --tag, --source-sha and --output or --verify-sidecar, or use --self-test")
        sidecar = build_sidecar(args.tag, args.source_sha, ROOT, args.receipt)
        if args.verify_sidecar:
            observed = strict_json(bounded_file(args.verify_sidecar, MAX_LEDGER_BYTES,
                                                "sidecar"), "sidecar")
            verify_sidecar_data(observed, sidecar)
            print(f"verified source-bound support sidecar for {args.tag} ({args.source_sha})")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(sidecar, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(f"wrote source-bound support sidecar for {args.tag} ({args.source_sha})")
    except (ValueError, KeyError, OSError, TypeError, AttributeError, IndexError,
            subprocess.SubprocessError) as error:
        print(f"support-ledger verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
