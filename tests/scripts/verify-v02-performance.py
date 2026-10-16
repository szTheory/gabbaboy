#!/usr/bin/env python3
"""Verify provenance-bound v0.2.0 DMG performance receipts."""
from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve()
BASELINE_SHA = "e30d168f7fc61de8db0a3801e7b1736362912cb7"
WORKLOAD_ID = "original-wram-tracer-1m-half-dots-v1"
EXPECTED_DIGEST = "4c7a57ff3d50d228"


def git_text(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def git_bytes(revision: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(payload)


def build_record(source: dict[str, str], marker: str) -> dict[str, object]:
    compiler = {
        "id": "TestClang",
        "version": "TestClang 1.0",
        "binary_sha256": "1" * 64,
    }
    record: dict[str, object] = {
        "configuration": "Release",
        "cmake_version": "cmake version 3.29.0",
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

    def test_valid_receipt_is_accepted(self) -> None:
        result = self.run_cli(valid_fixture())
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("performance receipt verified", result.stdout)


def self_test() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PerformanceReceiptContractTests)
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        return self_test()
    if len(argv) == 2 and argv[0] == "--verify":
        print("verify-not-implemented", file=sys.stderr)
        return 1
    print("usage: verify-v02-performance.py --verify PATH | --self-test", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
