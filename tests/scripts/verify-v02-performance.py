#!/usr/bin/env python3
"""Verify provenance-bound v0.2.0 DMG performance receipts."""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
from pathlib import Path
import re
import statistics
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve()
BASELINE_SHA = "e30d168f7fc61de8db0a3801e7b1736362912cb7"
WORKLOAD_ID = "original-wram-tracer-1m-half-dots-v1"
EXPECTED_DIGEST = "4c7a57ff3d50d228"
EXPECTED_WARMUPS = 3
EXPECTED_PAIRS = 30
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX16 = re.compile(r"^[0-9a-f]{16}$")
PRIVATE_KEY_NAMES = {
    "host", "hostname", "host_name", "machine_id", "machine_identifier",
    "serial", "serial_number", "username", "user_name", "compiler_path",
    "build_path", "working_directory", "home_directory",
}
PRIVATE_PATH = re.compile(r"(?<![A-Za-z0-9_.-])/(?:[A-Za-z0-9._-]+/)+[^\s\"']*")
WINDOWS_PATH = re.compile(r"(?:^|\s)[A-Za-z]:[\\/](?:[^\s]+)")
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PRIVATE_HOSTNAME = re.compile(r"\b(?:[A-Za-z0-9-]+\.)+(?:local|internal|private|example|corp|lan)\b", re.IGNORECASE)


class ReceiptError(ValueError):
    """A named rejection from the performance receipt contract."""


def git_text(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def git_bytes(revision: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(payload)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ReceiptError(reason)


def git_tree_sha(revision: str) -> str:
    try:
        return git_text("rev-parse", "--verify", f"{revision}^{{tree}}")
    except subprocess.CalledProcessError as error:
        raise ReceiptError("source-commit-unknown") from error


def source_blob_sha(revision: str, path: str) -> str:
    try:
        return sha256(git_bytes(revision, path))
    except subprocess.CalledProcessError as error:
        raise ReceiptError("source-input-missing") from error


def build_identity(source: dict[str, object], build: dict[str, object]) -> str:
    payload = {key: value for key, value in build.items() if key != "identity_sha256"}
    return canonical_sha({
        "source_sha": source["sha"],
        "source_tree_sha": source["tree_sha"],
        **payload,
    })


def summarize_ratios(values: list[float]) -> dict[str, object]:
    sample_sd = statistics.stdev(values) if len(values) > 1 else 0.0
    median = statistics.median(values)
    margin = 1.96 * sample_sd / math.sqrt(len(values))
    delta = median - 100.0
    return {
        "median_candidate_to_baseline_percent": median,
        "mean_candidate_to_baseline_percent": statistics.mean(values),
        "sample_standard_deviation_percent": sample_sd,
        "approx_95_percent_mean_margin": margin,
        "noise_label": "within noise (under 3%)" if abs(delta) < 3.0 else
            ("slower than base by more than 3%" if delta > 0 else "faster than base by more than 3%"),
        "review_trigger": median > 105.0 and (median - margin) > 100.0,
    }


def summarize_values(values: list[int]) -> dict[str, object]:
    sample_sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return {
        "count": len(values),
        "median": statistics.median(values),
        "mean": statistics.mean(values),
        "min": min(values),
        "max": max(values),
        "sample_standard_deviation": sample_sd,
        "approx_95_percent_mean_margin": 1.96 * sample_sd / math.sqrt(len(values)),
    }


def verify_privacy(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            require(normalized not in PRIVATE_KEY_NAMES, "receipt-private-data")
            verify_privacy(item)
    elif isinstance(value, list):
        for item in value:
            verify_privacy(item)
    elif isinstance(value, str):
        # URLs are references to external evidence, not host-local absolute file paths. Keep
        # hostname/email checks on the full value while excluding URL paths from the
        # local-path detector.
        local_path_text = re.sub(r"https?://[^\s\"']+", " ", value, flags=re.IGNORECASE)
        require(PRIVATE_PATH.search(local_path_text) is None and WINDOWS_PATH.search(value) is None and
                EMAIL.search(value) is None and PRIVATE_HOSTNAME.search(value) is None,
                "receipt-private-data")


def close_number(actual: object, expected: float) -> bool:
    return isinstance(actual, (int, float)) and not isinstance(actual, bool) and math.isclose(
        actual, expected, rel_tol=1e-10, abs_tol=1e-9)


def verify_reviewed_disposition(receipt: dict[str, object], decision: object,
                                measurement_receipt_sha256: str) -> dict[str, object]:
    require(isinstance(decision, dict), "reviewed-disposition-missing")
    verify_privacy(decision)
    require(decision.get("schema_version") == 1, "review-decision-schema-unsupported")
    decision_id = decision.get("decision_id")
    require(isinstance(decision_id, str) and decision_id.strip() and len(decision_id) <= 256 and
            not any(ord(char) < 32 for char in decision_id), "review-decision-identity-missing")
    reviewer = decision.get("reviewer_identity")
    require(isinstance(reviewer, str) and reviewer.strip() and len(reviewer) <= 256,
            "reviewer-identity-missing")
    reference = decision.get("review_reference")
    parsed_reference = urlparse(reference) if isinstance(reference, str) else None
    require(parsed_reference is not None and parsed_reference.scheme == "https" and
            parsed_reference.hostname and parsed_reference.path not in ("", "/"),
            "review-reference-invalid")
    reviewed_at = decision.get("reviewed_at")
    try:
        parsed_time = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00")) if isinstance(reviewed_at, str) else None
    except ValueError:
        parsed_time = None
    require(parsed_time is not None and parsed_time.tzinfo is not None,
            "review-timestamp-invalid")
    require(decision.get("review_type") == "independent", "independent-review-required")
    require(decision.get("decision") == "accepted-with-disclosed-regression",
            "review-decision-not-accepted")
    rationale = decision.get("rationale")
    require(isinstance(rationale, str) and rationale.strip(), "review-rationale-missing")
    require(decision.get("measurement_receipt_sha256") == measurement_receipt_sha256,
            "review-measurement-receipt-mismatch")
    require(decision.get("source_pair") == receipt.get("source"), "review-source-pair-mismatch")
    require(decision.get("workload") == receipt.get("workload"), "review-workload-mismatch")

    measurement = receipt.get("measurement")
    require(isinstance(measurement, dict), "measurement-missing")
    summary = measurement.get("summary")
    require(isinstance(summary, dict), "measurement-summary-missing")
    require(decision.get("measurement_sha256") == canonical_sha(measurement),
            "review-measurement-mismatch")
    require(decision.get("measurement_summary") == summary, "review-measurement-summary-mismatch")
    uncertainty = decision.get("uncertainty")
    expected_uncertainty = {
        "method": measurement.get("uncertainty_method"),
        "sample_standard_deviation_percent": summary.get("sample_standard_deviation_percent"),
        "approx_95_percent_mean_margin": summary.get("approx_95_percent_mean_margin"),
    }
    deviation = expected_uncertainty["sample_standard_deviation_percent"]
    margin = expected_uncertainty["approx_95_percent_mean_margin"]
    require(isinstance(uncertainty, dict) and uncertainty == expected_uncertainty and
            isinstance(expected_uncertainty["method"], str) and
            isinstance(deviation, (int, float)) and not isinstance(deviation, bool) and
            math.isfinite(deviation) and isinstance(margin, (int, float)) and
            not isinstance(margin, bool) and math.isfinite(margin),
            "review-uncertainty-mismatch")
    return decision


def verify_reviewed_measurement_basis(receipt: dict[str, object], digest: str) -> None:
    measurement_basis = receipt.get("measurement_receipt")
    require(isinstance(measurement_basis, dict), "review-measurement-receipt-missing")
    require(canonical_sha(measurement_basis) == digest, "review-measurement-receipt-mismatch")
    pending = verify_receipt(measurement_basis, allow_pending=True)
    expected = json.loads(json.dumps(receipt))
    for field in ("measurement_receipt", "measurement_receipt_sha256", "reviewed_disposition",
                  "reviewed_disposition_sha256"):
        expected.pop(field, None)
    expected["result"] = pending["result"]
    expected["regression_disposition"] = pending["regression_disposition"]
    require(canonical_sha(expected) == canonical_sha(pending),
            "review-measurement-receipt-mismatch")


def verify_receipt(receipt: object, *, allow_pending: bool = False) -> dict[str, object]:
    require(isinstance(receipt, dict), "receipt-not-object")
    schema_version = receipt.get("schema_version")
    require(schema_version in (1, 2), "schema-version-unsupported")
    legacy = schema_version == 1
    verify_privacy(receipt)
    if allow_pending:
        require(not legacy, "review-decision-legacy-receipt")

    source = receipt.get("source")
    require(isinstance(source, dict), "source-identity-missing")
    baseline = source.get("baseline")
    candidate = source.get("candidate")
    require(isinstance(baseline, dict) and isinstance(candidate, dict), "source-identity-missing")
    require(baseline.get("tag") == "v0.1.0" and baseline.get("sha") == BASELINE_SHA,
            "baseline-source-unknown")
    if legacy:
        require(candidate.get("sha") == git_text("rev-parse", "v0.2.0^{commit}"),
                "legacy-receipt-not-v0.2.0-source")
    require(git_text("rev-parse", "v0.1.0^{commit}") == BASELINE_SHA, "baseline-tag-mismatch")
    for label, identity in (("baseline", baseline), ("candidate", candidate)):
        revision = identity.get("sha")
        tree_sha = identity.get("tree_sha")
        require(isinstance(revision, str) and HEX40.fullmatch(revision) is not None,
                f"{label}-source-sha-invalid")
        require(isinstance(tree_sha, str) and HEX40.fullmatch(tree_sha) is not None,
                f"{label}-source-tree-invalid")
        require(git_tree_sha(revision) == tree_sha, f"{label}-source-tree-mismatch")
        require(revision != "0" * 40, f"{label}-source-unknown")
        harness_sha = identity.get("harness_sha256")
        require(isinstance(harness_sha, str) and HEX64.fullmatch(harness_sha) is not None,
                f"{label}-harness-hash-invalid")
        require(source_blob_sha(revision, "tests/measure_core.c") == harness_sha,
                f"{label}-harness-identity-mismatch")
    require(baseline["sha"] != candidate["sha"], "source-pair-identical")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", str(baseline["sha"]), str(candidate["sha"])],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    require(ancestry.returncode == 0, "candidate-source-not-descended-from-baseline")

    builds = receipt.get("builds")
    require(isinstance(builds, dict), "build-identities-missing")
    baseline_build = builds.get("baseline")
    candidate_build = builds.get("candidate")
    require(isinstance(baseline_build, dict) and isinstance(candidate_build, dict),
            "build-identities-missing")
    for label, identity, build in (
        ("baseline", baseline, baseline_build),
        ("candidate", candidate, candidate_build),
    ):
        require(build.get("configuration") == "Release", f"{label}-build-not-release")
        compiler = build.get("compiler")
        require(isinstance(compiler, dict), f"{label}-compiler-identity-missing")
        require(bool(compiler.get("id")) and bool(compiler.get("version")) and
                compiler.get("id") != "unknown" and compiler.get("version") != "unknown",
                f"{label}-compiler-identity-unknown")
        require(isinstance(compiler.get("binary_sha256"), str) and
                HEX64.fullmatch(compiler["binary_sha256"]) is not None,
                f"{label}-compiler-binary-hash-invalid")
        require(isinstance(build.get("cmake_version"), str) and
                build["cmake_version"].startswith("cmake version "),
                f"{label}-cmake-version-invalid")
        require(isinstance(build.get("generator"), str) and build["generator"] != "unknown",
                f"{label}-generator-invalid")
        flags = build.get("c_flags_release")
        require(isinstance(flags, str) and flags != "unknown", f"{label}-release-flags-unknown")
        require(isinstance(build.get("binary_sha256"), str) and
                HEX64.fullmatch(build["binary_sha256"]) is not None,
                f"{label}-binary-hash-invalid")
        require(build.get("harness_sha256") == identity.get("harness_sha256"),
                f"{label}-harness-build-mismatch")
        claimed_identity = build.get("identity_sha256")
        require(isinstance(claimed_identity, str) and HEX64.fullmatch(claimed_identity) is not None,
                f"{label}-build-identity-invalid")
        require(build_identity(identity, build) == claimed_identity,
                f"{label}-build-identity-mismatch")
    require(baseline_build["compiler"] == candidate_build["compiler"] and
            baseline_build["configuration"] == candidate_build["configuration"] and
            baseline_build["cmake_version"] == candidate_build["cmake_version"] and
            baseline_build["generator"] == candidate_build["generator"] and
            baseline_build["c_flags_release"] == candidate_build["c_flags_release"],
            "build-configuration-mismatch")

    workload = receipt.get("workload")
    require(isinstance(workload, dict), "workload-identity-missing")
    require(workload.get("id") == WORKLOAD_ID, "workload-identity-mismatch")
    require(workload.get("model") == "DMG-CPU-B" and
            workload.get("fixture") == "fixtures/tracer/tracer.gb" and
            workload.get("budget_half_dots") == 1_000_000,
            "workload-contract-mismatch")
    require(workload.get("correctness_digest_fnv1a64") == EXPECTED_DIGEST,
            "workload-digest-mismatch")
    fixture_sha = workload.get("fixture_sha256")
    manifest_sha = workload.get("fixture_manifest_sha256")
    require(isinstance(fixture_sha, str) and HEX64.fullmatch(fixture_sha) is not None and
            isinstance(manifest_sha, str) and HEX64.fullmatch(manifest_sha) is not None,
            "workload-input-hash-invalid")
    for identity in (baseline, candidate):
        require(source_blob_sha(identity["sha"], "fixtures/tracer/tracer.gb") == fixture_sha,
                "workload-fixture-mismatch")
        require(source_blob_sha(identity["sha"], "fixtures/tracer/manifest.json") == manifest_sha,
                "workload-manifest-mismatch")
    try:
        manifest_data = json.loads(git_bytes(candidate["sha"], "fixtures/tracer/manifest.json"))
    except (json.JSONDecodeError, subprocess.CalledProcessError) as error:
        raise ReceiptError("workload-manifest-invalid") from error
    require(manifest_data.get("id") == "original-wram-tracer" and
            manifest_data.get("sha256") == fixture_sha,
            "workload-manifest-mismatch")

    hardware = receipt.get("hardware_class")
    require(isinstance(hardware, str) and re.fullmatch(
                r"(?:Darwin|Linux|Windows) (?:arm64|aarch64|x86_64|AMD64|i386|i686|armv7l|ppc64le|s390x)", hardware),
            "hardware-class-invalid")
    measurement = receipt.get("measurement")
    require(isinstance(measurement, dict), "measurement-missing")
    require(measurement.get("warmups") == EXPECTED_WARMUPS, "warmup-count-mismatch")
    require(measurement.get("paired_samples") == EXPECTED_PAIRS, "paired-sample-count-mismatch")
    pairs = measurement.get("pairs")
    require(isinstance(pairs, list) and len(pairs) == EXPECTED_PAIRS, "paired-sample-count-mismatch")
    ratios: list[float] = []
    for index, pair in enumerate(pairs):
        require(isinstance(pair, dict), "paired-sample-invalid")
        baseline_ns, candidate_ns = pair.get("baseline_ns"), pair.get("candidate_ns")
        require(type(baseline_ns) is int and baseline_ns > 0 and
                type(candidate_ns) is int and candidate_ns > 0,
                "paired-sample-invalid")
        expected_first = "baseline" if index % 2 == 0 else "candidate"
        require(pair.get("first") == expected_first, "pair-order-invalid")
        ratios.append(100.0 * candidate_ns / baseline_ns)
    summary = measurement.get("summary")
    require(isinstance(summary, dict), "measurement-summary-missing")
    recomputed = summarize_ratios(ratios)
    for field, expected in recomputed.items():
        actual = summary.get(field)
        if isinstance(expected, float):
            require(isinstance(actual, (int, float)) and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-9),
                    f"measurement-summary-mismatch:{field}")
        else:
            require(actual == expected, f"measurement-summary-mismatch:{field}")
    require(isinstance(measurement.get("uncertainty_method"), str) and
            "standard deviation" in measurement["uncertainty_method"],
            "measurement-uncertainty-missing")

    disposition = receipt.get("regression_disposition")
    require(isinstance(disposition, dict), "regression-disposition-missing")
    require(disposition.get("review_trigger_percent") == 5.0, "regression-review-threshold-mismatch")
    estimate = recomputed["median_candidate_to_baseline_percent"] - 100.0
    margin = recomputed["approx_95_percent_mean_margin"]
    require(close_number(disposition.get("estimate_percent"), estimate) and
            close_number(disposition.get("uncertainty_margin_percent"), margin),
            "regression-estimate-mismatch")
    investigation = disposition.get("investigation")
    require(isinstance(investigation, str) and investigation.strip(),
            "regression-investigation-missing")
    if legacy:
        require(receipt.get("result") == "passed", "legacy-receipt-not-passed")
        require("reviewed_disposition" not in receipt and "measurement_receipt" not in receipt and
                "measurement_receipt_sha256" not in receipt,
                "legacy-receipt-has-new-review-fields")
        if recomputed["review_trigger"]:
            require(disposition.get("decision") == "accepted-with-disclosed-regression" and
                    disposition.get("release_disposition") == "accepted-with-disclosed-regression",
                    "legacy-regression-disposition-invalid")
        else:
            require(disposition.get("decision") == "no-review-trigger" and
                    disposition.get("release_disposition") == "qualified-no-trigger",
                    "legacy-regression-disposition-invalid")
    elif recomputed["review_trigger"] and disposition.get("decision") == "investigation-required":
        require(allow_pending, "regression-review-pending")
        require(receipt.get("result") == "pending-investigation" and
                disposition.get("release_disposition") == "pending-investigation",
                "pending-regression-disposition-invalid")
        require("reviewed_disposition" not in receipt and
                "reviewed_disposition_sha256" not in receipt and
                "measurement_receipt" not in receipt and
                "measurement_receipt_sha256" not in receipt,
                "pending-receipt-has-review-fields")
    elif recomputed["review_trigger"]:
        require(disposition.get("decision") == "accepted-with-disclosed-regression" and
                disposition.get("release_disposition") == "accepted-with-disclosed-regression" and
                receipt.get("result") == "passed",
                "regression-review-pending")
        measurement_receipt_sha = receipt.get("measurement_receipt_sha256")
        require(isinstance(measurement_receipt_sha, str) and
                HEX64.fullmatch(measurement_receipt_sha) is not None,
                "review-measurement-receipt-missing")
        reviewed = verify_reviewed_disposition(
            receipt, receipt.get("reviewed_disposition"), measurement_receipt_sha)
        verify_reviewed_measurement_basis(receipt, measurement_receipt_sha)
        require(receipt.get("reviewed_disposition_sha256") == canonical_sha(reviewed),
                "reviewed-disposition-digest-mismatch")
        require(investigation == reviewed.get("rationale"), "review-investigation-mismatch")
    else:
        require(disposition.get("decision") == "no-review-trigger" and
                disposition.get("release_disposition") == "qualified-no-trigger" and
                receipt.get("result") == "passed",
                "regression-disposition-inconsistent")
        require("reviewed_disposition" not in receipt and
                "reviewed_disposition_sha256" not in receipt and
                "measurement_receipt" not in receipt and
                "measurement_receipt_sha256" not in receipt,
                "unexpected-review-disposition")

    resources = receipt.get("resource_observations")
    require(isinstance(resources, dict), "resource-observations-missing")
    require(resources.get("source_sha") == candidate["sha"] and
            resources.get("source_tree_sha") == candidate["tree_sha"],
            "resource-source-identity-mismatch")
    require(resources.get("build_identity_sha256") == {
                "baseline": baseline_build["identity_sha256"],
                "candidate": candidate_build["identity_sha256"],
            }, "resource-build-identity-mismatch")
    require(resources.get("warmups") == 3 and resources.get("paired_samples") == 10,
            "resource-sample-count-mismatch")

    def verify_resource_record(record: object, expected_digest: str | None = EXPECTED_DIGEST) -> str:
        require(isinstance(record, dict), "resource-record-missing")
        elapsed = record.get("core_elapsed_ns")
        rss = record.get("peak_rss_bytes")
        require(isinstance(elapsed, list) and len(elapsed) == 10 and
                all(type(value) is int and value > 0 for value in elapsed),
                "resource-timing-samples-invalid")
        require(isinstance(rss, list) and len(rss) == 10 and
                all(type(value) is int and value > 0 for value in rss),
                "resource-memory-samples-invalid")
        digest = record.get("correctness_digest_fnv1a64")
        require(isinstance(digest, str) and HEX16.fullmatch(digest) is not None and
                (expected_digest is None or digest == expected_digest),
                "resource-digest-mismatch")
        for name, values in (("elapsed_summary", elapsed), ("peak_rss_summary_bytes", rss)):
            summary_record = record.get(name)
            require(isinstance(summary_record, dict), "resource-summary-missing")
            expected_summary = summarize_values(values)
            for field, expected in expected_summary.items():
                actual = summary_record.get(field)
                if isinstance(expected, float):
                    require(close_number(actual, expected), "resource-summary-mismatch")
                else:
                    require(actual == expected, "resource-summary-mismatch")
        return digest

    dmg_resources = resources.get("dmg")
    require(isinstance(dmg_resources, dict), "resource-dmg-observations-missing")
    for mode in ("trace", "no-trace"):
        mode_record = dmg_resources.get(mode)
        require(isinstance(mode_record, dict), "resource-dmg-observations-missing")
        require(mode_record.get("sample_order") == [
                    "baseline" if index % 2 == 0 else "candidate" for index in range(10)],
                "resource-sample-order-invalid")
        base_digest = verify_resource_record(mode_record.get("baseline"))
        candidate_digest = verify_resource_record(mode_record.get("candidate"))
        require(base_digest == candidate_digest, "resource-dmg-digest-mismatch")
    cgb_resources = resources.get("cgb_cpu_e")
    require(isinstance(cgb_resources, dict), "resource-cgb-observations-missing")
    candidate_fixture = git_bytes(candidate["sha"], "fixtures/tracer/tracer.gb")
    expected_cgb_mode = "native-cgb" if candidate_fixture[0x143] & 0x80 else "compatibility"
    require(cgb_resources.get("model") == "CGB-CPU-E" and
            cgb_resources.get("execution_mode") == expected_cgb_mode,
            "resource-cgb-model-mismatch")
    require(isinstance(cgb_resources.get("candidate"), dict) and
            cgb_resources["candidate"].get("sample_order") == ["candidate"] * 10,
            "resource-sample-order-invalid")
    verify_resource_record(cgb_resources.get("candidate"))
    return receipt


def apply_reviewed_disposition(measurement_path: Path, decision_path: Path,
                               output_path: Path) -> dict[str, object]:
    measurement_path = measurement_path.resolve(strict=True)
    decision_path = decision_path.resolve(strict=True)
    output_path = output_path.resolve()
    try:
        decision_path.relative_to(ROOT)
    except ValueError:
        pass
    else:
        raise ReceiptError("review-decision-must-be-outside-source-tree")
    require(measurement_path != output_path and decision_path != output_path,
            "review-output-path-collision")
    require(not output_path.exists(), "review-output-exists")
    measurement_bytes = measurement_path.read_bytes()
    try:
        measurement = json.loads(measurement_bytes)
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReceiptError("review-input-json-invalid") from error
    verified = verify_receipt(measurement, allow_pending=True)
    summary = verified["measurement"]["summary"]
    require(summary.get("review_trigger") is True, "review-decision-not-required")
    measurement_digest = canonical_sha(verified)
    reviewed = verify_reviewed_disposition(verified, decision, measurement_digest)

    qualified = json.loads(json.dumps(verified))
    qualified["result"] = "passed"
    qualified["measurement_receipt"] = verified
    qualified["measurement_receipt_sha256"] = measurement_digest
    qualified["reviewed_disposition"] = reviewed
    qualified["reviewed_disposition_sha256"] = canonical_sha(reviewed)
    disposition = qualified["regression_disposition"]
    disposition["decision"] = "accepted-with-disclosed-regression"
    disposition["investigation"] = reviewed["rationale"]
    disposition["release_disposition"] = "accepted-with-disclosed-regression"
    verify_receipt(qualified)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(qualified, indent=2, sort_keys=True) + "\n"
    temporary_path = output_path.with_name(output_path.name + f".tmp-{os.getpid()}")
    with open(temporary_path, "x", encoding="utf-8") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary_path, output_path)
    except FileExistsError as error:
        temporary_path.unlink(missing_ok=True)
        raise ReceiptError("review-output-exists") from error
    temporary_path.unlink()
    return qualified


def build_record(source: dict[str, str], marker: str) -> dict[str, object]:
    compiler = {
        "id": "TestClang",
        "version": "TestClang 1.0",
        "binary_sha256": "1" * 64,
    }
    record: dict[str, object] = {
        "configuration": "Release",
        "cmake_version": "cmake version 3.29.0",
        "generator": "Test Makefiles",
        "compiler": compiler,
        "c_flags_release": "-O3 -DNDEBUG",
        "binary_sha256": marker * 64,
        "harness_sha256": source["harness_sha256"],
    }
    record["identity_sha256"] = canonical_sha({
        "source_sha": source["sha"],
        "source_tree_sha": source["tree_sha"],
        **record,
    })
    return record


def valid_fixture(candidate_revision: str | None = None, schema_version: int = 2) -> dict[str, object]:
    baseline_tree = git_text("rev-parse", f"{BASELINE_SHA}^{{tree}}")
    candidate_sha = candidate_revision or git_text("rev-parse", "HEAD")
    candidate_tree = git_text("rev-parse", f"{candidate_sha}^{{tree}}")
    baseline_harness = sha256(git_bytes(BASELINE_SHA, "tests/measure_core.c"))
    candidate_harness = sha256(git_bytes(candidate_sha, "tests/measure_core.c"))
    baseline = {"tag": "v0.1.0", "sha": BASELINE_SHA, "tree_sha": baseline_tree,
                "harness_sha256": baseline_harness}
    candidate = {"sha": candidate_sha, "tree_sha": candidate_tree,
                 "harness_sha256": candidate_harness}
    pairs = [{"baseline_ns": 10_000_000, "candidate_ns": 10_200_000,
              "first": "baseline" if index % 2 == 0 else "candidate"}
             for index in range(30)]
    ratio_summary = summarize_ratios([102.0] * len(pairs))
    builds = {
        "baseline": build_record(baseline, "2"),
        "candidate": build_record(candidate, "3"),
    }
    def resource_record(elapsed: int, rss: int, digest: str = EXPECTED_DIGEST) -> dict[str, object]:
        times = [elapsed + index * 10 for index in range(10)]
        memory = [rss + index * 64 for index in range(10)]
        return {
            "core_elapsed_ns": times,
            "peak_rss_bytes": memory,
            "correctness_digest_fnv1a64": digest,
            "elapsed_summary": summarize_values(times),
            "peak_rss_summary_bytes": summarize_values(memory),
        }
    fixture = git_bytes(candidate_sha, "fixtures/tracer/tracer.gb")
    manifest = git_bytes(candidate_sha, "fixtures/tracer/manifest.json")
    return {
        "schema_version": schema_version,
        "result": "passed",
        "source": {"baseline": baseline, "candidate": candidate},
        "builds": builds,
        "hardware_class": f"{platform.system()} {platform.machine()}",
        "workload": {
            "id": WORKLOAD_ID,
            "model": "DMG-CPU-B",
            "fixture": "fixtures/tracer/tracer.gb",
            "fixture_sha256": sha256(fixture),
            "fixture_manifest_sha256": sha256(manifest),
            "budget_half_dots": 1_000_000,
            "correctness_digest_fnv1a64": EXPECTED_DIGEST,
        },
        "measurement": {
            "warmups": 3,
            "paired_samples": 30,
            "pairs": pairs,
            "summary": ratio_summary,
            "uncertainty_method": "paired median, sample standard deviation and approximate 95% mean margin",
        },
        "regression_disposition": {
            "review_trigger_percent": 5.0,
            "estimate_percent": 2.0,
            "uncertainty_margin_percent": 0.0,
            "decision": "no-review-trigger",
            "investigation": "No +5% review trigger; the paired estimate is within the predeclared noise band.",
            "release_disposition": "qualified-no-trigger",
        },
        "resource_observations": {
            "source_sha": candidate_sha,
            "source_tree_sha": candidate_tree,
            "build_identity_sha256": {
                "baseline": builds["baseline"]["identity_sha256"],
                "candidate": builds["candidate"]["identity_sha256"],
            },
            "warmups": 3,
            "paired_samples": 10,
            "dmg": {
                "trace": {
                    "sample_order": ["baseline" if index % 2 == 0 else "candidate" for index in range(10)],
                    "baseline": resource_record(11_000_000, 2_000_000),
                    "candidate": resource_record(12_000_000, 2_100_000),
                },
                "no-trace": {
                    "sample_order": ["baseline" if index % 2 == 0 else "candidate" for index in range(10)],
                    "baseline": resource_record(10_000_000, 1_900_000),
                    "candidate": resource_record(10_200_000, 1_950_000),
                },
            },
            "cgb_cpu_e": {
                "model": "CGB-CPU-E",
                "execution_mode": "compatibility",
                "candidate": {
                    "model": "CGB-CPU-E",
                    "execution_mode": "compatibility",
                    "sample_order": ["candidate"] * 10,
                    **resource_record(11_000_000, 2_200_000),
                },
            },
        },
    }


def triggered_pending_fixture() -> dict[str, object]:
    receipt = valid_fixture()
    measurement = receipt["measurement"]
    for pair in measurement["pairs"]:
        pair["candidate_ns"] = 11_000_000
    measurement["summary"] = summarize_ratios([110.0] * EXPECTED_PAIRS)
    disposition = receipt["regression_disposition"]
    disposition.update({
        "estimate_percent": 10.0,
        "uncertainty_margin_percent": 0.0,
        "decision": "investigation-required",
        "investigation": "A separately recorded independent review decision is required for this exact measurement.",
        "release_disposition": "pending-investigation",
    })
    receipt["result"] = "pending-investigation"
    return receipt


def decision_fixture(receipt: dict[str, object]) -> dict[str, object]:
    measurement = receipt["measurement"]
    summary = measurement["summary"]
    return {
        "schema_version": 1,
        "decision_id": "fixture-review-001",
        "reviewer_identity": "synthetic-independent-reviewer-fixture",
        "review_reference": "https://reviews.invalid/performance/fixture-001",
        "reviewed_at": datetime.now().astimezone().isoformat(),
        "review_type": "independent",
        "decision": "accepted-with-disclosed-regression",
        "rationale": "Self-test fixture only; this record is not an owner or reviewer approval.",
        "measurement_receipt_sha256": canonical_sha(receipt),
        "source_pair": json.loads(json.dumps(receipt["source"])),
        "workload": json.loads(json.dumps(receipt["workload"])),
        "measurement_sha256": canonical_sha(measurement),
        "measurement_summary": json.loads(json.dumps(summary)),
        "uncertainty": {
            "method": measurement["uncertainty_method"],
            "sample_standard_deviation_percent": summary["sample_standard_deviation_percent"],
            "approx_95_percent_mean_margin": summary["approx_95_percent_mean_margin"],
        },
    }


class PerformanceReceiptContractTests(unittest.TestCase):
    def run_cli(self, receipt: dict[str, object]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-performance-test-") as temp:
            path = Path(temp) / "receipt.json"
            path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
            return subprocess.run(
                [sys.executable, "-I", str(SCRIPT), "--verify", str(path)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )

    def run_historical_cli(self, receipt: dict[str, object], *, historical: bool) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-performance-history-") as temp:
            path = Path(temp) / "receipt.json"
            path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
            flag = "--verify-historical" if historical else "--verify"
            return subprocess.run(
                [sys.executable, "-I", str(SCRIPT), flag, str(path)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )

    @staticmethod
    def bash_executable() -> str:
        """The producer is a bash script. A bare "bash" on Windows resolves to the WSL launcher in
        System32 ahead of PATH, so take the first PATH entry that is not under the Windows directory."""
        if os.name != "nt":
            return "bash"
        windows_dir = os.path.normcase(os.environ.get("SystemRoot", r"C:\Windows"))
        for entry in os.environ.get("PATH", "").split(os.pathsep):
            candidate = os.path.join(entry, "bash.exe")
            if entry and os.path.isfile(candidate) and not os.path.normcase(candidate).startswith(windows_dir):
                return candidate
        raise AssertionError("no non-WSL bash.exe on PATH")

    def run_producer_collision(self) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-performance-collision-") as temp:
            path = Path(temp) / "receipt.json"
            path.write_text("existing", encoding="utf-8")
            result = subprocess.run(
                [self.bash_executable(), (ROOT / "tests/scripts/measure-release-baseline.sh").as_posix(),
                 "--qualify-v02", "--output", str(path)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(path.read_text(encoding="utf-8"), "existing")
            return result

    def write_controlled_build_tools(self, bin_dir: Path) -> dict[str, str]:
        bin_dir.mkdir(parents=True)
        compiler = bin_dir / "cc"
        compiler.write_text("#!/bin/sh\nprintf '%s\\n' 'test compiler 1.0'\n", encoding="utf-8")
        compiler.chmod(0o755)
        cmake = bin_dir / "cmake"
        cmake.write_text(
            "#!/bin/sh\n"
            "if [ \"${1:-}\" = \"--version\" ]; then echo 'cmake version 3.29.0'; exit 0; fi\n"
            "if [ \"${1:-}\" = \"--build\" ]; then\n"
            "  build=$2; mkdir -p \"$build/measure_core-dir\"\n"
            "  cat > \"$build/measure_core\" <<'PYBIN'\n"
            "#!/usr/bin/env python3\n"
            "import pathlib, sys\n"
            "mode = next((arg[2:] for arg in sys.argv[1:] if arg.startswith('--')), '')\n"
            "cgb = '--profile' in sys.argv and 'cgb' in sys.argv\n"
            "elapsed = 110000000 if 'candidate-build' in str(pathlib.Path(sys.argv[0])) else 100000000\n"
            "fields = ['mode=' + mode, 'workload=original-wram-tracer-1m-half-dots-v1',\n"
            "          'elapsed_ns=' + str(elapsed), 'peak_rss_bytes=2000000',\n"
            "          'correctness_digest_fnv1a64=4c7a57ff3d50d228']\n"
            "if cgb: fields.append('profile=cgb-cpu-e')\n"
            "print(' '.join(fields))\n"
            "PYBIN\n"
            "  chmod +x \"$build/measure_core\"; exit 0\n"
            "fi\n"
            "build=\n"
            "while [ $# -gt 0 ]; do if [ \"$1\" = \"-B\" ]; then shift; build=$1; fi; shift; done\n"
            "[ -n \"$build\" ] || exit 2\n"
            "mkdir -p \"$build/CMakeFiles/3.29.0\"\n"
            "cat > \"$build/CMakeCache.txt\" <<EOF\n"
            "CMAKE_BUILD_TYPE:STRING=Release\n"
            f"CMAKE_C_COMPILER:FILEPATH={compiler}\n"
            "CMAKE_C_FLAGS_RELEASE:STRING=-O3 -DNDEBUG\n"
            "CMAKE_GENERATOR:INTERNAL=Unix Makefiles\n"
            "EOF\n"
            "cat > \"$build/CMakeFiles/3.29.0/CMakeCCompiler.cmake\" <<'EOF'\n"
            "set(CMAKE_C_COMPILER_ID \"TestCC\")\n"
            "set(CMAKE_C_COMPILER_VERSION \"1.0\")\n"
            "EOF\n",
            encoding="utf-8",
        )
        cmake.chmod(0o755)
        return {"PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", ""), "CC": "cc"}

    def run_controlled_producer(self, output_path: Path) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-performance-tools-") as temp:
            env = os.environ.copy()
            env.update(self.write_controlled_build_tools(Path(temp) / "bin"))
            return subprocess.run(
                [self.bash_executable(), (ROOT / "tests/scripts/measure-release-baseline.sh").as_posix(),
                 "--qualify-v02", "--output", str(output_path), "--review-regression",
                 "The hosted DMG paired benchmark is +14.86% (±1.62%) slower than v0.1.0, "
                 "which is disclosed in the receipt and docs/release.md."],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )

    def run_apply_decision(self, measurement: Path, decision: Path, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-I", str(SCRIPT), "--apply-decision", "--measurement", str(measurement),
             "--decision", str(decision), "--output", str(output)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

    def test_valid_receipt_is_accepted(self) -> None:
        result = self.run_cli(valid_fixture())
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("performance receipt verified", result.stdout)

    def test_triggered_producer_rejects_copied_acceptance_prose(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-performance-pending-") as temp:
            path = Path(temp) / "measurement.json"
            result = self.run_controlled_producer(path)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("qualify-v02-review-trigger-fired", result.stdout)
            self.assertIn("not an independent decision", result.stdout)
            self.assertIn("wrote pending performance measurement", result.stdout)
            self.assertNotIn("wrote untriggered performance receipt", result.stdout)
            receipt = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["schema_version"], 2)
            self.assertEqual(receipt["result"], "pending-investigation")
            self.assertTrue(receipt["measurement"]["summary"]["review_trigger"])
            self.assertNotIn("reviewed_disposition", receipt)
            self.assertNotIn("The hosted DMG paired benchmark", path.read_text(encoding="utf-8"))

    def test_bound_review_decision_qualifies_exact_pending_measurement(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-performance-decision-") as temp:
            directory = Path(temp)
            measurement = directory / "pending.json"
            decision = directory / "decision.json"
            output = directory / "qualified.json"
            receipt = triggered_pending_fixture()
            receipt_bytes = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
            measurement.write_bytes(receipt_bytes)
            decision.write_text(json.dumps(decision_fixture(receipt), indent=2), encoding="utf-8")
            result = self.run_apply_decision(measurement, decision, output)
            self.assertEqual(result.returncode, 0, result.stdout)
            qualified = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(qualified["result"], "passed")
            self.assertEqual(qualified["regression_disposition"]["decision"],
                             "accepted-with-disclosed-regression")
            verify = self.run_cli(qualified)
            self.assertEqual(verify.returncode, 0, verify.stdout)

    def test_triggered_copy_of_acceptance_prose_is_not_a_decision(self) -> None:
        receipt = triggered_pending_fixture()
        receipt["result"] = "passed"
        receipt["regression_disposition"].update({
            "decision": "accepted-with-disclosed-regression",
            "investigation": "The hosted DMG paired benchmark is +14.86% (±1.62%) slower than v0.1.0.",
            "release_disposition": "accepted-with-disclosed-regression",
        })
        receipt["measurement_receipt_sha256"] = canonical_sha(triggered_pending_fixture())
        result = self.run_cli(receipt)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("reviewed-disposition-missing", result.stdout)

    def test_stale_decision_receipt_digest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-stale-review-") as temp:
            directory = Path(temp)
            receipt = triggered_pending_fixture()
            decision = decision_fixture(receipt)
            receipt["measurement"]["review_note"] = "changed after the review record"
            measurement, decision_path, output = directory / "measurement.json", directory / "decision.json", directory / "out.json"
            measurement.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
            decision_path.write_text(json.dumps(decision), encoding="utf-8")
            result = self.run_apply_decision(measurement, decision_path, output)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("review-measurement-receipt-mismatch", result.stdout)
            self.assertFalse(output.exists())

    def test_decision_must_bind_source_workload_and_measurement(self) -> None:
        mutations = (
            ("source", lambda receipt: receipt["source"]["candidate"].update(review_context="changed"),
             "review-source-pair-mismatch"),
            ("workload", lambda receipt: receipt["workload"].update(review_context="changed"),
             "review-workload-mismatch"),
            ("measurement", lambda receipt: self._change_triggered_measurement(receipt),
             "review-measurement-mismatch"),
        )
        for name, mutate, expected in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory(prefix="gabbaboy-review-binding-") as temp:
                directory = Path(temp)
                receipt = triggered_pending_fixture()
                decision = decision_fixture(receipt)
                mutate(receipt)
                decision["measurement_receipt_sha256"] = canonical_sha(receipt)
                measurement, decision_path, output = directory / "measurement.json", directory / "decision.json", directory / "out.json"
                measurement.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
                decision_path.write_text(json.dumps(decision), encoding="utf-8")
                result = self.run_apply_decision(measurement, decision_path, output)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(expected, result.stdout)
                self.assertFalse(output.exists())

    @staticmethod
    def _change_triggered_measurement(receipt: dict[str, object]) -> None:
        measurement = receipt["measurement"]
        for pair in measurement["pairs"]:
            pair["candidate_ns"] = 11_100_000
        measurement["summary"] = summarize_ratios([111.0] * EXPECTED_PAIRS)
        disposition = receipt["regression_disposition"]
        disposition["estimate_percent"] = 11.0
        disposition["uncertainty_margin_percent"] = measurement["summary"]["approx_95_percent_mean_margin"]

    def test_review_requires_uncertainty_and_independent_decision(self) -> None:
        cases = (
            ("missing-uncertainty", lambda decision: decision.pop("uncertainty"), "review-uncertainty-mismatch"),
            ("non-independent", lambda decision: decision.update(review_type="same-person"), "independent-review-required"),
            ("malformed-reference", lambda decision: decision.update(review_reference="http://review.invalid/id"),
             "review-reference-invalid"),
        )
        for name, mutate, expected in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory(prefix="gabbaboy-malformed-review-") as temp:
                directory = Path(temp)
                receipt = triggered_pending_fixture()
                decision = decision_fixture(receipt)
                mutate(decision)
                measurement, decision_path, output = directory / "measurement.json", directory / "decision.json", directory / "out.json"
                measurement.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
                decision_path.write_text(json.dumps(decision), encoding="utf-8")
                result = self.run_apply_decision(measurement, decision_path, output)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(expected, result.stdout)
                self.assertFalse(output.exists())

    def test_existing_review_output_is_not_reused_or_overwritten(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-review-output-") as temp:
            directory = Path(temp)
            receipt = triggered_pending_fixture()
            decision = decision_fixture(receipt)
            measurement, decision_path, output = directory / "measurement.json", directory / "decision.json", directory / "out.json"
            measurement.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
            decision_path.write_text(json.dumps(decision), encoding="utf-8")
            output.write_text("existing", encoding="utf-8")
            result = self.run_apply_decision(measurement, decision_path, output)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("review-output-exists", result.stdout)
            self.assertEqual(output.read_text(encoding="utf-8"), "existing")

    def test_legacy_receipt_requires_explicit_historical_parser(self) -> None:
        revision = git_text("rev-parse", "v0.2.0^{commit}")
        receipt = valid_fixture(candidate_revision=revision, schema_version=1)
        normal = self.run_historical_cli(receipt, historical=False)
        self.assertEqual(normal.returncode, 1, normal.stdout)
        self.assertIn("legacy-receipt-requires-historical-mode", normal.stdout)
        historical = self.run_historical_cli(receipt, historical=True)
        self.assertEqual(historical.returncode, 0, historical.stdout)
        self.assertIn("historical performance receipt parsed", historical.stdout)
        self.assertIn("not current qualification", historical.stdout)

    def test_final_receipt_detects_tampered_reviewed_workload_and_measurements(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-final-review-") as temp:
            directory = Path(temp)
            pending = triggered_pending_fixture()
            measurement, decision_path, output = directory / "measurement.json", directory / "decision.json", directory / "out.json"
            measurement.write_text(json.dumps(pending, sort_keys=True), encoding="utf-8")
            decision_path.write_text(json.dumps(decision_fixture(pending)), encoding="utf-8")
            applied = self.run_apply_decision(measurement, decision_path, output)
            self.assertEqual(applied.returncode, 0, applied.stdout)
            qualified = json.loads(output.read_text(encoding="utf-8"))

        changed_workload = json.loads(json.dumps(qualified))
        changed_workload["workload"]["review_context"] = "changed after review"
        workload_result = self.run_cli(changed_workload)
        self.assertEqual(workload_result.returncode, 1, workload_result.stdout)
        self.assertIn("review-workload-mismatch", workload_result.stdout)

        changed_numbers = json.loads(json.dumps(qualified))
        self._change_triggered_measurement(changed_numbers)
        summary = changed_numbers["measurement"]["summary"]
        disposition = changed_numbers["regression_disposition"]
        disposition["estimate_percent"] = 11.0
        disposition["uncertainty_margin_percent"] = summary["approx_95_percent_mean_margin"]
        numbers_result = self.run_cli(changed_numbers)
        self.assertEqual(numbers_result.returncode, 1, numbers_result.stdout)
        self.assertIn("review-measurement-mismatch", numbers_result.stdout)

    def assert_rejected(self, mutation: object, reason: str) -> None:
        receipt = valid_fixture()
        mutation(receipt)
        result = self.run_cli(receipt)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(reason, result.stdout)

    def test_unknown_baseline_revision_is_rejected(self) -> None:
        self.assert_rejected(lambda receipt: receipt["source"]["baseline"].update(sha="f" * 40),
                             "baseline-source-unknown")

    def test_forged_source_tree_is_rejected(self) -> None:
        self.assert_rejected(lambda receipt: receipt["source"]["candidate"].update(tree_sha="0" * 40),
                             "candidate-source-tree-mismatch")

    def test_forged_binary_identity_is_rejected(self) -> None:
        self.assert_rejected(lambda receipt: receipt["builds"]["candidate"].update(binary_sha256="f" * 64),
                             "candidate-build-identity-mismatch")

    def test_compiler_mismatch_is_rejected(self) -> None:
        def mutate(receipt: dict[str, object]) -> None:
            build = receipt["builds"]["candidate"]
            build["compiler"].update(version="other compiler")
            build["identity_sha256"] = build_identity(receipt["source"]["candidate"], build)
        self.assert_rejected(mutate,
                             "build-configuration-mismatch")

    def test_changed_digest_is_rejected(self) -> None:
        self.assert_rejected(lambda receipt: receipt["workload"].update(correctness_digest_fnv1a64="0000000000000000"),
                             "workload-digest-mismatch")

    def test_missing_pair_is_rejected(self) -> None:
        self.assert_rejected(lambda receipt: receipt["measurement"]["pairs"].pop(),
                             "paired-sample-count-mismatch")

    def test_wrong_warmup_count_is_rejected(self) -> None:
        self.assert_rejected(lambda receipt: receipt["measurement"].update(warmups=2),
                             "warmup-count-mismatch")

    def test_forged_uncertainty_summary_is_rejected(self) -> None:
        self.assert_rejected(lambda receipt: receipt["measurement"]["summary"].update(
            approx_95_percent_mean_margin=99.0),
            "measurement-summary-mismatch:approx_95_percent_mean_margin")

    def test_missing_regression_disposition_is_rejected(self) -> None:
        def mutate(receipt: dict[str, object]) -> None:
            receipt.pop("regression_disposition")
        self.assert_rejected(mutate, "regression-disposition-missing")

    def test_trigger_without_investigation_is_rejected(self) -> None:
        def mutate(receipt: dict[str, object]) -> None:
            measurement = receipt["measurement"]
            for pair in measurement["pairs"]:
                pair["candidate_ns"] = 11_000_000
            measurement["summary"] = summarize_ratios([110.0] * 30)
            receipt["regression_disposition"] = {
                "review_trigger_percent": 5.0,
                "estimate_percent": 10.0,
                "uncertainty_margin_percent": 0.0,
                "decision": "investigation-required",
                "investigation": "",
                "release_disposition": "pending-investigation",
            }
        self.assert_rejected(mutate, "regression-investigation-missing")

    def test_wrong_regression_threshold_is_rejected(self) -> None:
        self.assert_rejected(lambda receipt: receipt["regression_disposition"].update(
            review_trigger_percent=4.0),
            "regression-review-threshold-mismatch")

    def test_hidden_host_or_path_data_is_rejected(self) -> None:
        self.assert_rejected(lambda receipt: receipt.update(host_name="build-node.private.example"),
                             "receipt-private-data")

    def test_private_absolute_path_is_rejected(self) -> None:
        self.assert_rejected(lambda receipt: receipt["regression_disposition"].update(
            investigation="reviewed at /Users/owner/private-build/run-1"),
            "receipt-private-data")

    def test_stale_covered_harness_identity_is_rejected(self) -> None:
        self.assert_rejected(lambda receipt: receipt["source"]["candidate"].update(harness_sha256="0" * 64),
                             "candidate-harness-identity-mismatch")

    def test_missing_resource_observations_are_rejected(self) -> None:
        self.assert_rejected(lambda receipt: receipt.pop("resource_observations"),
                             "resource-observations-missing")

    def test_resource_pair_order_mutation_is_rejected(self) -> None:
        self.assert_rejected(lambda receipt: receipt["resource_observations"]["dmg"]["trace"].update(
            sample_order=["candidate" if index % 2 == 0 else "baseline" for index in range(10)]),
            "resource-sample-order-invalid")

    def test_cgb_resource_execution_mode_is_pinned(self) -> None:
        self.assert_rejected(lambda receipt: receipt["resource_observations"]["cgb_cpu_e"].update(
            execution_mode="native-cgb"),
            "resource-cgb-model-mismatch")

    def test_producer_refuses_receipt_collision(self) -> None:
        result = self.run_producer_collision()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("qualify-v02-output-exists", result.stdout)


def self_test() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PerformanceReceiptContractTests)
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
    controls = max(0, result.testsRun - 1)
    summary = {
        "status": "passed" if result.wasSuccessful() else "failed",
        "tests_run": result.testsRun,
        "positive_successes": 1 if result.wasSuccessful() else 0,
        "negative_controls": controls,
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if result.wasSuccessful() and controls > 0 and summary["positive_successes"] > 0 else 1


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        return self_test()
    if len(argv) == 2 and argv[0] == "--verify":
        try:
            receipt = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
            require(isinstance(receipt, dict) and receipt.get("schema_version") != 1,
                    "legacy-receipt-requires-historical-mode")
            verified = verify_receipt(receipt)
            print(f"performance receipt verified samples={verified['measurement']['paired_samples']} "
                  f"warmups={verified['measurement']['warmups']}")
            return 0
        except (OSError, json.JSONDecodeError, ReceiptError, KeyError, TypeError) as error:
            reason = str(error) if isinstance(error, ReceiptError) else f"receipt-read-failed:{type(error).__name__}"
            print(f"verify-v02-performance: rejected:{reason}", file=sys.stderr)
            return 1
    if len(argv) == 2 and argv[0] == "--verify-historical":
        try:
            receipt = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
            require(isinstance(receipt, dict) and receipt.get("schema_version") == 1,
                    "historical-receipt-schema-required")
            verified = verify_receipt(receipt)
            print(f"historical performance receipt parsed samples={verified['measurement']['paired_samples']} "
                  f"warmups={verified['measurement']['warmups']}; not current qualification")
            return 0
        except (OSError, json.JSONDecodeError, ReceiptError, KeyError, TypeError) as error:
            reason = str(error) if isinstance(error, ReceiptError) else f"receipt-read-failed:{type(error).__name__}"
            print(f"verify-v02-performance: rejected:{reason}", file=sys.stderr)
            return 1
    if len(argv) == 7 and argv[0] == "--apply-decision" and argv[1] == "--measurement" and \
            argv[3] == "--decision" and argv[5] == "--output":
        try:
            qualified = apply_reviewed_disposition(Path(argv[2]), Path(argv[4]), Path(argv[6]))
            print("receipt-bound independent review decision applied; performance receipt verified "
                  f"samples={qualified['measurement']['paired_samples']} "
                  f"warmups={qualified['measurement']['warmups']}")
            return 0
        except (OSError, json.JSONDecodeError, ReceiptError, KeyError, TypeError) as error:
            reason = str(error) if isinstance(error, ReceiptError) else f"review-input-failed:{type(error).__name__}"
            print(f"verify-v02-performance: rejected:{reason}", file=sys.stderr)
            return 1
    print("usage: verify-v02-performance.py --verify PATH | --verify-historical PATH | "
          "--apply-decision --measurement PATH --decision PATH --output PATH | --self-test", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
