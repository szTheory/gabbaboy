#!/usr/bin/env python3
"""Check the frozen SameSuite APU roster and its already-recorded model receipts."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "fixtures/samesuite/manifest.json"
DISPOSITIONS = ROOT / "tests/external/cgb-apu-dispositions.json"
INVENTORY = ROOT / "tests/external/cgb-corpus-inventory.json"
EXPECTED_TESTS = ROOT / "tests/expected-tests.txt"
MAX_INPUT_BYTES = 2_000_000
REQUIRED_COUNTS = {"cases": 70, "pass": 8, "xfail": 62, "assertions": 4784}
REQUIRED_CTESTS = {
    "cgb_samesuite_apu_membership",
    "cgb_samesuite_apu_controls",
    "cgb_samesuite_apu_tracer",
    "cgb_samesuite_apu_tracer_controls",
    "cgb_samesuite_apu_suite",
}


class Mismatch(Exception):
    pass


def need(condition: bool, code: str) -> None:
    if not condition:
        raise Mismatch(code)


def read_json(path: Path) -> dict:
    need(path.stat().st_size <= MAX_INPUT_BYTES, f"input-size:{path.name}")
    value = json.loads(path.read_text(encoding="utf-8"))
    need(isinstance(value, dict), f"input-shape:{path.name}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ctest_name(alias: str) -> str:
    suffix = alias.removeprefix("apu/").removesuffix(".gb").replace("/", "_").replace("-", "_")
    return "cgb_samesuite_apu_" + suffix


def observation_signature(alias: str, sentinel: str, assertions: list[dict]) -> str:
    chunks = [f"samesuite-apu-observation-v1\n{alias}\n{sentinel}\n"]
    for index, assertion in enumerate(assertions):
        chunks.append(
            f"result-{index:03}|{assertion['expected']}|{assertion['observed']}\n"
        )
    return hashlib.sha256("".join(chunks).encode("ascii")).hexdigest()


def mismatch_mask(assertions: list[dict]) -> str:
    value = sum(1 << index for index, row in enumerate(assertions)
                if row["expected"] != row["observed"])
    width = max(1, (len(assertions) + 3) // 4)
    return f"{value:0{width}x}"


def current_ctest_names(root: Path) -> set[str]:
    result = subprocess.run(
        ["ctest", "--test-dir", str(root / "build"), "--show-only=json-v1"],
        check=True, capture_output=True, text=True,
    )
    return {row["name"] for row in json.loads(result.stdout)["tests"]}


def validate(root: Path, manifest: dict, report: dict, inventory: dict,
             registered_tests: set[str]) -> dict:
    fixtures = [row for row in manifest.get("fixtures", [])
                if isinstance(row, dict) and str(row.get("alias", "")).startswith("apu/")]
    need(len(fixtures) == REQUIRED_COUNTS["cases"], "manifest-apu-count")
    aliases = [row["alias"] for row in fixtures]
    need(len(aliases) == len(set(aliases)), "manifest-apu-duplicate")

    fixture_by_source = {}
    for fixture in fixtures:
        source_path = fixture.get("source_path")
        need(isinstance(source_path, str) and source_path.endswith(".asm"), "manifest-source-path")
        need(fixture["alias"] == source_path.removesuffix(".asm"),
             f"manifest-alias-source:{fixture['alias']}")
        need(source_path not in fixture_by_source, "manifest-source-duplicate")
        fixture_by_source[source_path] = fixture
        expected = fixture.get("author_expected_results")
        need(fixture.get("author_expectation", {}).get("result") == "pass"
             and isinstance(expected, list) and 1 <= len(expected) <= 144,
             f"author-expectation:{fixture['alias']}")
        need(all(re.fullmatch(r"[0-9a-f]{2}", value or "") for value in expected),
             f"author-bytes:{fixture['alias']}")
        need("G7" in fixture.get("rights_basis", "")
             and fixture.get("reproduction", {}).get("suite_revision") == report.get("suite", {}).get("revision"),
             f"fixture-provenance:{fixture['alias']}")

    report_cases = report.get("cases")
    need(isinstance(report_cases, list) and len(report_cases) == REQUIRED_COUNTS["cases"],
         "report-case-count")
    report_by_source = {row.get("source_path"): row for row in report_cases}
    need(len(report_by_source) == len(report_cases), "report-source-duplicate")
    need(set(report_by_source) == set(fixture_by_source), "manifest-report-membership")

    source_ids = {f"samesuite:{path}" for path in fixture_by_source}
    source_rows = [row for row in inventory.get("source_candidates", [])
                   if row.get("suite") == "samesuite" and str(row.get("source_path", "")).startswith("apu/")]
    need({row.get("id") for row in source_rows} == source_ids, "inventory-source-membership")
    need(all(row.get("selection", {}).get("state") == "required"
             and row.get("applicability", {}).get("readme_quote") == "CPU-CGB-E – passes all tests"
             for row in source_rows), "inventory-source-applicability")

    outputs = {row.get("source_id"): row for row in inventory.get("outputs", [])
               if str(row.get("source_id", "")).startswith("samesuite:apu/")}
    cases = {row.get("source_id"): row for row in inventory.get("cases", [])
             if str(row.get("source_id", "")).startswith("samesuite:apu/")}
    need(set(outputs) == source_ids, "inventory-output-membership")
    need(set(cases) == source_ids, "inventory-case-membership")
    need(len(outputs) == len(cases) == REQUIRED_COUNTS["cases"], "inventory-apu-count")

    config = report.get("configuration", {})
    need(config.get("model") == "CGB-CPU-E" and config.get("mode") == "native"
         and config.get("speed") == "normal" and config.get("boot") == "bootless",
         "qualification-configuration")
    need(config.get("run_budget_half_dots") == 33554432
         and config.get("run_slice_half_dots") == 2048
         and config.get("max_run_calls") == 16384, "qualification-bounds")
    need(config.get("manifest_sha256") == sha256(root / "fixtures/samesuite/manifest.json"),
         "manifest-digest")
    need(config.get("harness_source_sha256") == sha256(root / "tests/test_samesuite_apu.c"),
         "harness-digest")
    need(config.get("core_source_sha256") == sha256(root / "src/core/gabbaboy.c"),
         "core-digest")
    need(report.get("schema") == "gabbaboy-cgb-apu-dispositions-v1", "report-schema")

    statuses = [row.get("evaluator_disposition", {}).get("status") for row in report_cases]
    observed_pass = statuses.count("pass")
    observed_xfail = statuses.count("xfail")
    assertion_total = sum(row.get("execution", {}).get("assertion_count", 0)
                          for row in report_cases)
    need((observed_pass, observed_xfail, assertion_total) == (
        REQUIRED_COUNTS["pass"], REQUIRED_COUNTS["xfail"], REQUIRED_COUNTS["assertions"]
    ), "cohort-counts")

    registered = registered_tests
    expected_file_names = {
        line.strip() for line in (root / "tests/expected-tests.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    required_test_names = REQUIRED_CTESTS | {ctest_name(alias) for alias in aliases}
    need(required_test_names <= registered, "ctest-membership")
    need(required_test_names <= expected_file_names, "expected-test-membership")

    inventory_counts = inventory.get("counts", {})
    need(inventory_counts.get("admitted_outputs") == 109
         and inventory_counts.get("pending_outputs") == 0,
         "inventory-global-admission-counts")
    same_counts = inventory_counts.get("by_suite", {}).get("samesuite", {})
    need(same_counts == {
        "source_candidates": 74, "output_rows": 74, "admitted_outputs": 74,
        "pending_outputs": 0, "required_cases": 74,
    }, "inventory-samesuite-counts")

    for source_path, fixture in fixture_by_source.items():
        alias = fixture["alias"]
        source_id = f"samesuite:{source_path}"
        output = outputs[source_id]
        case = cases[source_id]
        receipt = report_by_source[source_path]
        receipt_case_id = source_id
        expected_output_id = "samesuite:" + PurePosixPath(source_path).stem
        expected_fixture_path = "fixtures/samesuite/" + fixture["file"]
        expected_test = ctest_name(alias)
        expected_values = fixture["author_expected_results"]
        assertions = receipt.get("execution", {}).get("assertions")
        evaluator = receipt.get("evaluator_disposition", {})
        execution = receipt.get("execution", {})
        status = evaluator.get("status")
        sentinel = execution.get("guest_sentinel")

        need(receipt.get("id") == receipt_case_id
             and receipt.get("fixture_path") == expected_fixture_path
             and receipt.get("source_sha256") == fixture.get("source_sha256")
             and receipt.get("rom_sha256") == fixture.get("sha256"),
             f"report-identity:{source_path}")
        need(receipt.get("test_name") == expected_test, f"report-test-name:{source_path}")
        need(receipt.get("author_expectation", {}).get("value") == "pass"
             and receipt["author_expectation"].get("result_start") == fixture.get("author_result_start")
             and receipt["author_expectation"].get("assertion_count") == len(expected_values),
             f"author-contract:{source_path}")
        need(isinstance(assertions, list) and len(assertions) == len(expected_values),
             f"assertion-count:{source_path}")
        normalized = []
        for index, assertion in enumerate(assertions):
            expected = expected_values[index]
            observed = assertion.get("observed")
            match = expected == observed
            need(assertion.get("id") == f"result-{index:03}"
                 and assertion.get("author_expected") == expected
                 and assertion.get("status") == ("match" if match else "mismatch"),
                 f"assertion-identity:{source_path}:{index}")
            normalized.append({"expected": expected, "observed": observed})
        need(execution.get("state") == "completed" and execution.get("terminal") is True
             and execution.get("assertion_count") == len(assertions),
             f"execution-not-terminal:{source_path}")
        need(sentinel in ("P", "F") and execution.get("observed_result") in ("pass", "fail"),
             f"execution-result:{source_path}")
        guest_pass = sentinel == "P" and all(row["expected"] == row["observed"] for row in normalized)
        need(not (status == "xfail" and guest_pass), f"unexpected-pass:{source_path}")
        need(status in ("pass", "xfail") and execution.get("observed_result") == (
            "pass" if guest_pass else "fail"), f"evaluator-result:{source_path}")
        need(evaluator.get("value") == ("pass" if status == "pass" else "expected-failure"),
             f"evaluator-value:{source_path}")
        need((status == "pass") == guest_pass, f"observed-pass-status:{source_path}")
        if status == "xfail":
            need(evaluator.get("reason") == "samesuite-apu-current-observation-signature"
                 and evaluator.get("owner_phase") == 14
                 and evaluator.get("decision") == "D-08/D-16"
                 and evaluator.get("promotion_rule"), f"xfail-reason:{source_path}")
        need(execution.get("matching_assertions") == sum(
            row["expected"] == row["observed"] for row in normalized
        ), f"assertion-matches:{source_path}")
        need(execution.get("mismatch_mask_hex") == mismatch_mask(normalized),
             f"mismatch-mask:{source_path}")
        signature = observation_signature(alias, sentinel, normalized)
        need(re.fullmatch(r"[0-9a-f]{64}", str(signature)) is not None
             and execution.get("signature_sha256") == signature
             and evaluator.get("signature_sha256") == signature,
             f"signature:{source_path}")

        need(output.get("admission_status") == "admitted"
             and output.get("manifest_ref") == "fixtures/samesuite/manifest.json"
             and output.get("output_path") == expected_fixture_path
             and output.get("size_bytes") == fixture.get("size_bytes")
             and output.get("sha256") == fixture.get("sha256"),
             f"inventory-output:{source_path}")
        need(case.get("id") == source_id and case.get("output_id") == output.get("id") == expected_output_id,
             f"inventory-case-identity:{source_path}")
        need(case.get("author_expectation") == {
            "class": "source-CorrectResults", "value": "pass", "source_path": source_path,
            "result_start": fixture["author_result_start"], "assertion_count": len(expected_values),
        }, f"inventory-author-contract:{source_path}")
        need(case.get("evaluator_disposition", {}).get("state") == (
            "pass" if status == "pass" else "expected-failure"
        ) and case["evaluator_disposition"].get("signature_sha256") == signature,
             f"inventory-disposition:{source_path}")
        need(case.get("execution", {}).get("state") == "completed"
             and case["execution"].get("terminal") is True
             and case["execution"].get("observed_result") == ("pass" if guest_pass else "fail")
             and case["execution"].get("evaluator_status") == status
             and case["execution"].get("signature_sha256") == signature,
             f"inventory-execution:{source_path}")
        expected_contract = [{
            "id": assertion["id"],
            "author_expected": assertion["author_expected"],
            "expected_disposition": "pass",
            "observed": assertion["observed"],
            "observed_result": "pass" if assertion["status"] == "match" else "fail",
            "evaluator_status": status,
        } for assertion in receipt["execution"]["assertions"]]
        need(case.get("assertion_contract", {}).get("state") == "qualified"
             and case["assertion_contract"].get("count") == len(expected_contract)
             and case["assertion_contract"].get("rows") == expected_contract,
             f"inventory-assertions:{source_path}")
        need(case.get("test_binding") == {"state": "bound", "ctest_name": expected_test},
             f"inventory-test-binding:{source_path}")
        need(not case.get("hardware_qualified", False), f"hardware-claim-forbidden:{source_path}")

    return {"cases": len(fixtures), "pass": observed_pass, "xfail": observed_xfail,
            "assertions": assertion_total}


def current_inputs(root: Path) -> tuple[dict, dict, dict, set[str]]:
    return (
        read_json(root / "fixtures/samesuite/manifest.json"),
        read_json(root / "tests/external/cgb-apu-dispositions.json"),
        read_json(root / "tests/external/cgb-corpus-inventory.json"),
        current_ctest_names(root),
    )


def self_test(root: Path, manifest: dict, report: dict, inventory: dict,
              registered_tests: set[str]) -> None:
    validate(root, manifest, report, inventory, registered_tests)
    print("clean-twin=pass id=frozen-apu-membership")

    def rejected(name: str, mutation, expected: str) -> None:
        trial_manifest = copy.deepcopy(manifest)
        trial_report = copy.deepcopy(report)
        trial_inventory = copy.deepcopy(inventory)
        mutation(trial_manifest, trial_report, trial_inventory)
        try:
            validate(root, trial_manifest, trial_report, trial_inventory, registered_tests)
        except Mismatch as exc:
            need(str(exc) == expected, f"control-diagnostic:{name}:{exc}")
            print(f"negative-control=pass id={name} diagnostic={expected}")
            return
        raise Mismatch(f"control-accepted:{name}")

    rejected("omitted-source", lambda m, r, i: m["fixtures"].remove(
        next(row for row in m["fixtures"] if row.get("alias") == "apu/channel_1/channel_1_align")),
        "manifest-apu-count")
    rejected("filtered-revision-suffix", lambda m, r, i: i["cases"].remove(
        next(row for row in i["cases"] if row.get("source_id") ==
             "samesuite:apu/channel_1/channel_1_sweep_restart_2.asm")),
        "inventory-case-membership")
    rejected("bogus-green-process-exit", lambda m, r, i: next(
        row for row in i["cases"] if row.get("source_id") ==
        "samesuite:apu/channel_1/channel_1_align.asm")["execution"].update(
            {"state": "not-run-by-inventory", "terminal": False, "process_exit_code": 0}),
        "inventory-execution:apu/channel_1/channel_1_align.asm")
    rejected("altered-author-expectation", lambda m, r, i: r["cases"][0]["author_expectation"].update(
        {"value": "fail"}), "author-contract:apu/channel_1/channel_1_align.asm")
    rejected("changed-signature", lambda m, r, i: next(
        row for row in i["cases"] if row.get("source_id") ==
        "samesuite:apu/channel_1/channel_1_align.asm")["execution"].update(
            {"signature_sha256": "0" * 64}),
        "inventory-execution:apu/channel_1/channel_1_align.asm")

    def xpass(m, r, i):
        row = next(case for case in r["cases"]
                   if case["evaluator_disposition"]["status"] == "xfail")
        row["execution"]["guest_sentinel"] = "P"
        row["execution"]["observed_result"] = "pass"
        for assertion in row["execution"]["assertions"]:
            assertion["observed"] = assertion["author_expected"]
            assertion["status"] = "match"
        row["execution"]["matching_assertions"] = row["execution"]["assertion_count"]
        row["execution"]["mismatch_mask_hex"] = "00"
        row["execution"]["signature_sha256"] = observation_signature(
            row["source_path"].removesuffix(".asm"), "P",
            [{"expected": assertion["author_expected"], "observed": assertion["observed"]}
             for assertion in row["execution"]["assertions"]])
        row["evaluator_disposition"]["signature_sha256"] = row["execution"]["signature_sha256"]

    rejected("unexpected-pass", xpass, "unexpected-pass:apu/channel_1/channel_1_align.asm")
    rejected("all-xfail-cohort", lambda m, r, i: [
        case["evaluator_disposition"].update({"status": "xfail", "value": "expected-failure"})
        for case in r["cases"]], "cohort-counts")
    rejected("empty-required-cohort", lambda m, r, i: i.update({"cases": []}),
             "inventory-case-membership")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--membership", action="store_true")
    group.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        manifest, report, inventory, registered_tests = current_inputs(ROOT)
        if args.self_test:
            self_test(ROOT, manifest, report, inventory, registered_tests)
            print("cgb-apu-dispositions self-test pass controls=8")
        else:
            counts = validate(ROOT, manifest, report, inventory, registered_tests)
            print("cgb-apu-dispositions membership pass cases={cases} author_expectation=pass observed_pass={pass} xfail={xfail} assertions={assertions}".format(**counts))
    except (Mismatch, KeyError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"cgb-apu-dispositions mismatch: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
