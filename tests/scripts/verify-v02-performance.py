#!/usr/bin/env python3
"""Verify provenance-bound v0.2.0 DMG performance receipts."""
from __future__ import annotations

import hashlib
import json
import math
import platform
from pathlib import Path
import re
import statistics
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve()
BASELINE_SHA = "e30d168f7fc61de8db0a3801e7b1736362912cb7"
WORKLOAD_ID = "original-wram-tracer-1m-half-dots-v1"
EXPECTED_DIGEST = "4c7a57ff3d50d228"
EXPECTED_WARMUPS = 3
EXPECTED_PAIRS = 30
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


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
    return {
        "count": len(values),
        "median": statistics.median(values),
        "mean": statistics.mean(values),
        "sample_standard_deviation": statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def verify_receipt(receipt: object) -> dict[str, object]:
    require(isinstance(receipt, dict), "receipt-not-object")
    require(receipt.get("schema_version") == 1, "schema-version-unsupported")
    require(receipt.get("result") == "passed", "receipt-not-passed")

    source = receipt.get("source")
    require(isinstance(source, dict), "source-identity-missing")
    baseline = source.get("baseline")
    candidate = source.get("candidate")
    require(isinstance(baseline, dict) and isinstance(candidate, dict), "source-identity-missing")
    require(baseline.get("tag") == "v0.1.0" and baseline.get("sha") == BASELINE_SHA,
            "baseline-source-unknown")
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
    require(isinstance(hardware, str) and re.fullmatch(r"[A-Za-z0-9._+-]+ [A-Za-z0-9._+-]+", hardware),
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
    return receipt


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


def valid_fixture() -> dict[str, object]:
    baseline_tree = git_text("rev-parse", f"{BASELINE_SHA}^{{tree}}")
    candidate_sha = git_text("rev-parse", "HEAD")
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
        "schema_version": 1,
        "result": "passed",
        "source": {"baseline": baseline, "candidate": candidate},
        "builds": {
            "baseline": build_record(baseline, "2"),
            "candidate": build_record(candidate, "3"),
        },
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
            "decision": "within-noise",
            "investigation": "No +5% review trigger; the paired estimate is within the predeclared noise band.",
            "release_disposition": "qualified-no-trigger",
        },
        "resource_observations": {
            "warmups": 3,
            "paired_samples": 10,
            "dmg": {
                "trace": {
                    "baseline": resource_record(11_000_000, 2_000_000),
                    "candidate": resource_record(12_000_000, 2_100_000),
                },
                "no-trace": {
                    "baseline": resource_record(10_000_000, 1_900_000),
                    "candidate": resource_record(10_200_000, 1_950_000),
                },
            },
            "cgb_cpu_e": {"candidate": resource_record(11_000_000, 2_200_000)},
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

    def run_producer_collision(self) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-performance-collision-") as temp:
            path = Path(temp) / "receipt.json"
            path.write_text("existing", encoding="utf-8")
            return subprocess.run(
                ["bash", str(ROOT / "tests/scripts/measure-release-baseline.sh"),
                 "--qualify-v02", "--output", str(path)],
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

    def test_hidden_host_or_path_data_is_rejected(self) -> None:
        self.assert_rejected(lambda receipt: receipt.update(host_name="build-node.private.example"),
                             "receipt-private-data")

    def test_stale_covered_harness_identity_is_rejected(self) -> None:
        self.assert_rejected(lambda receipt: receipt["source"]["candidate"].update(harness_sha256="0" * 64),
                             "candidate-harness-identity-mismatch")

    def test_missing_resource_observations_are_rejected(self) -> None:
        self.assert_rejected(lambda receipt: receipt.pop("resource_observations"),
                             "resource-observations-missing")

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
            verified = verify_receipt(receipt)
            print(f"performance receipt verified samples={verified['measurement']['paired_samples']} "
                  f"warmups={verified['measurement']['warmups']}")
            return 0
        except (OSError, json.JSONDecodeError, ReceiptError, KeyError, TypeError) as error:
            reason = str(error) if isinstance(error, ReceiptError) else f"receipt-read-failed:{type(error).__name__}"
            print(f"verify-v02-performance: rejected:{reason}", file=sys.stderr)
            return 1
    print("usage: verify-v02-performance.py --verify PATH | --self-test", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
