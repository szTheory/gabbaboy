#!/usr/bin/env python3
"""Validate the Phase 13 CGB HDMA evidence ledger and its CTest/doc bindings."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile


REVISION = "f15645fb049a47ea235f6d2c9a033e72d8087901"
MAGEN_REVISION = "3f9c090f16e5a721db776febb9ba7d773e1c819c"
MEALYBUG_REVISION = "70e88fb90b59d19dfbb9c3ac36c64105202bb1f4"
SAME_CASES = ("gbc_dma_cont", "gdma_addr_mask", "hdma_lcd_off", "hdma_mode0")
CASE_TESTS = {
    "gbc_dma_cont": "samesuite_hdma_gbc_dma_cont",
    "gdma_addr_mask": "samesuite_hdma_gdma_addr_mask",
    "hdma_lcd_off": "samesuite_hdma_hdma_lcd_off",
    "hdma_mode0": "samesuite_hdma_hdma_mode0",
}
SAME_EXECUTION = {
    "gbc_dma_cont": {
        "ff55_starts": [0, 0],
        "copied_bytes": 32,
        "continuation_cursor": "0xC020/0x8820",
        "elapsed_half_dots": 772848,
    },
    "gdma_addr_mask": {
        "ff55_starts": [131],
        "copied_bytes": 64,
        "continuation_cursor": "0xC040/0x8840",
        "final_ff55": "0xFF",
        "elapsed_half_dots": 769688,
        "initial_snapshot": "first 16 bytes match source-address pattern; next 16 bytes remain 0x00 after the initial block",
    },
    "hdma_lcd_off": {
        "ff55_starts": [131, 0],
        "ff55_reads": [2, 128],
        "copied_bytes": 16,
        "continuation_cursor": "0xC010/0x8810",
        "final_ff55": "0x80",
        "elapsed_half_dots": 774944,
    },
    "hdma_mode0": {
        "ff55_starts": [131, 0],
        "ff55_reads": [2, 128],
        "copied_bytes": 16,
        "continuation_cursor": "0xC010/0x8810",
        "final_ff55": "0x80",
        "elapsed_half_dots": 1046904,
    },
}


class Mismatch(Exception):
    pass


def need(condition: bool, detail: str) -> None:
    if not condition:
        raise Mismatch(detail)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def suite_map(data: dict) -> dict[str, dict]:
    suites = data.get("suites")
    need(isinstance(suites, list), "suite-set")
    result: dict[str, dict] = {}
    for suite in suites:
        name = suite.get("suite", "")
        need(bool(name) and name not in result, f"suite-name {name!r}")
        result[name] = suite
    need(set(result) == {"samesuite", "magentests", "mealybug-cgb-c"}, "suite-set")
    return result


def mirror_rows(document: str) -> list[tuple[str, ...]]:
    begin = "<!-- cgb-hdma-dispositions-begin -->"
    end = "<!-- cgb-hdma-dispositions-end -->"
    need(document.count(begin) == 1 and document.count(end) == 1, "docs-mirror-markers")
    block = document.split(begin, 1)[1].split(end, 1)[0]
    rows = []
    for line in block.splitlines():
        if not line.startswith("|"):
            continue
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        if cells and all(re.fullmatch(r"-+", cell) for cell in cells):
            continue
        if cells and cells[0] != "suite":
            need(len(cells) == 6, "docs-mirror-columns")
            rows.append(cells)
    return rows


def expected_mirror(suites: dict[str, dict]) -> list[tuple[str, ...]]:
    rows: list[tuple[str, ...]] = []
    for suite_name in ("samesuite", "magentests", "mealybug-cgb-c"):
        suite = suites[suite_name]
        for row in suite["rows"]:
            rows.append((suite_name, row["case"], row["disposition"], row.get("reason", "-"),
                         str(row.get("owner_phase", 13)), row.get("test_name") or "-"))
    return rows


def validate(data: dict, root: Path, complete: bool) -> None:
    need(data.get("schema") == "gabbaboy-cgb-hdma-dispositions-v1", "schema")
    policy = data.get("policy", {})
    need(policy.get("decisions") == ["D-06", "D-16", "D-17", "D-18", "D-19", "D-20", "D-21", "D-24"],
         "policy-decisions")
    need(policy.get("hardware_claim") is False and policy.get("model") == "CGB-CPU-E selected software model" and
         policy.get("boot_mode") == "bootless" and policy.get("same_suite_revision") == REVISION and
         policy.get("mealybug_revision") == MEALYBUG_REVISION, "policy-provenance")

    manifest = json.loads((root / "fixtures/samesuite/manifest.json").read_text(encoding="utf-8"))
    magen_manifest = json.loads((root / "fixtures/magentests/manifest.json").read_text(encoding="utf-8"))
    same_suite = manifest.get("suite", {})
    need(same_suite.get("revision") == REVISION and same_suite.get("license", "").startswith("X11"),
         "samesuite-manifest-revision")
    fixture_by_alias = {row.get("alias"): row for row in manifest.get("fixtures", [])}
    need(set(fixture_by_alias) == set(SAME_CASES), "samesuite-manifest-case-set")
    magen_fixture = next((row for row in magen_manifest.get("fixtures", [])
                          if row.get("alias") == "hblank_vram_dma"), None)
    need(magen_fixture is not None, "magen-manifest-case")

    suites = suite_map(data)
    same = suites["samesuite"]
    magen = suites["magentests"]
    mealybug = suites["mealybug-cgb-c"]
    need(same.get("repository_revision") == REVISION and same.get("target_revision") == "CGB-E" and
         same.get("model") == policy["model"] and same.get("boot_mode") == "bootless" and
         "author-test" in same.get("evidence_class", "") and
         "no independent physical CGB-E measurement" in same.get("evidence_class", ""),
         "samesuite-model-tags")
    same_rows = same.get("rows", [])
    need([row.get("case") for row in same_rows] == list(SAME_CASES), "samesuite-case-set")

    expected_tests = set((root / "tests/expected-tests.txt").read_text(encoding="utf-8").split())
    cmake = (root / "tests/CMakeLists.txt").read_text(encoding="utf-8")
    required_tests = {
        *CASE_TESTS.values(), "samesuite_hdma_gbc_dma_cont_control",
        "samesuite_hdma_gbc_dma_cont_corrupted_result_control", "cgb_hdma_dispositions",
        "cgb_hdma_dispositions_selftest", "samesuite_repro_selfcheck",
        "cgb_hdma_original_fixture", "magentests_hblank_vram_dma", "cgb_hdma_magen_controls",
        "cgb_speed_xfail_hdma_fails_closed",
    }
    need(required_tests <= expected_tests, "expected-tests-inventory")
    for name in required_tests:
        registrations = re.findall(rf"add_test\(NAME {re.escape(name)}(?=[\s)])", cmake)
        need(len(registrations) == 1, f"cmake-registration {name}")
        need(expected_tests.__contains__(name), f"inventory-name {name}")
    for name in CASE_TESTS.values():
        need(expected_tests.__contains__(name), f"test-name {name}")

    cgb_e_rows = []
    for row in same_rows:
        case = row["case"]
        fixture = fixture_by_alias[case]
        need(row.get("fixture_file") == fixture.get("file") and
             row.get("source_path") == fixture.get("source_path") and
             row.get("source_sha256") == fixture.get("source_sha256") and
             row.get("rom_sha256") == fixture.get("sha256"), f"samesuite-provenance {case}")
        rom_path = root / "fixtures/samesuite" / fixture["file"]
        need(rom_path.is_file() and sha256(rom_path) == fixture["sha256"], f"samesuite-rom-hash {case}")
        need(fixture.get("target_revision") == "CGB-E" and
             fixture.get("model") == policy["model"] and fixture.get("bootless_applicability") is True,
             f"samesuite-manifest-model {case}")
        need(row.get("expected_result") == "pass" and row.get("test_name") == CASE_TESTS[case] and
             row.get("target_revision") == "CGB-E" and row.get("model") == policy["model"] and
             row.get("boot_mode") == "bootless" and "author-test" in row.get("evidence_class", "") and
             bool(row.get("predicate")), f"samesuite-test-binding {case}")
        need(row.get("execution_status") in {"pending", "pass"}, f"samesuite-execution-state {case}")
        if row["execution_status"] == "pass":
            execution = row.get("execution", {})
            need(row.get("actual_result") == "pass" and row.get("disposition") == "pass" and
                 execution.get("status") == "pass" and execution.get("test_name") == row["test_name"],
                 f"samesuite-passing-evidence {case}")
            need(execution.get("guest_result") == "P" and
                 execution.get("pass_sentinel_b_to_l") == [3, 5, 8, 13, 21, 34] and
                 execution.get("source_start") == "0xC000" and
                 execution.get("destination_start") == "0x8800" and
                 all(execution.get(key) == value for key, value in SAME_EXECUTION[case].items()),
                 f"samesuite-execution-observation {case}")
        else:
            need(row.get("actual_result") == "not-run" and row.get("disposition") == "pending" and
                 row.get("reason", "").strip() != "", f"samesuite-pending-state {case}")
        cgb_e_rows.append(row)

    need(magen.get("repository_revision") == MAGEN_REVISION and magen.get("release") == "0.5.0" and
         magen.get("target_revision") == "CGB-E" and magen.get("model") == policy["model"] and
         magen.get("boot_mode") == "bootless" and "differential" in magen.get("evidence_class", "") and
         "not physical" in magen.get("evidence_class", ""), "magen-model-tags")
    magen_rows = magen.get("rows", [])
    need(len(magen_rows) == 1 and magen_rows[0].get("case") == "hblank_vram_dma", "magen-case-set")
    magen_row = magen_rows[0]
    magen_source = next((item for item in magen_fixture.get("source_files", [])
                         if item.get("path") == magen_row.get("source_path")), None)
    need(magen_fixture.get("sha256") == magen_row.get("rom_sha256") and
         magen_source is not None and magen_source.get("sha256") == magen_row.get("source_sha256") and
         magen_fixture.get("release") == magen.get("release"), "magen-provenance")
    magen_rom = root / "fixtures/magentests" / magen_fixture["file"]
    need(magen_rom.is_file() and sha256(magen_rom) == magen_fixture["sha256"], "magen-rom-hash")
    need(magen_row.get("expected_result") == "pass" and
         magen_row.get("test_name") == "magentests_hblank_vram_dma" and
         magen_row.get("target_revision") == "CGB-E" and magen_row.get("model") == policy["model"] and
         magen_row.get("boot_mode") == "bootless" and "differential" in magen_row.get("evidence_class", "") and
         bool(magen_row.get("predicate")), "magen-test-binding")
    need(magen_row.get("execution_status") in {"pending", "pass"}, "magen-execution-state")
    if magen_row["execution_status"] == "pass":
        magen_execution = magen_row.get("execution", {})
        need(magen_row.get("actual_result") == "pass" and magen_row.get("disposition") == "pass" and
             magen_execution.get("status") == "pass" and
             magen_execution.get("test_name") == magen_row["test_name"], "magen-passing-evidence")
        need(magen_execution.get("exact_map_bytes") == 1024 and
             magen_execution.get("alignment_prefix_bytes") == 12 and
             magen_execution.get("alignment_prefix_value") == "0xFF" and
             magen_execution.get("ff55_busy_then_complete") is True and
             magen_execution.get("halt64_second_transfer_blocked") is True and
             magen_execution.get("viewport_rgb555_green") == "0x03E0" and
             magen_execution.get("stable_frame_generations") == [16, 17] and
             re.fullmatch(r"[0-9a-f]{64}", magen_execution.get("structural_digest", "")) is not None,
             "magen-execution-observation")
        need(set(magen_execution.get("controls", [])) == {"no-transfer", "wrong-bank", "wrong-HALT"},
             "magen-execution-controls")
    else:
        need(magen_row.get("actual_result") == "not-run" and magen_row.get("disposition") == "pending",
             "magen-pending-state")
    cgb_e_rows.append(magen_row)

    need(mealybug.get("repository_revision") == MEALYBUG_REVISION and
         mealybug.get("rights_gate") == "G1" and mealybug.get("target_revision") == "CGB-C" and
         mealybug.get("informational") is True and
         mealybug.get("included_in_cgb_e_denominator") is False, "mealybug-rights-model")
    need(mealybug.get("evidence_class") == "optional local differential only; no hardware claim",
         "mealybug-hardware-claim")
    mealy_rows = mealybug.get("rows", [])
    need([row.get("case") for row in mealy_rows] == ["hdma_timing-C", "hdma_during_halt-C"],
         "mealybug-case-set")
    for row in mealy_rows:
        need(re.fullmatch(r"[0-9a-f]{64}", row.get("rom_sha256", "")) is not None and
             row.get("actual_result") == "not-run:rights-gate-G1" and
             row.get("disposition") == "not-run:rights-gate-G1" and
             row.get("execution_status") == "not-run:rights-gate-G1" and
             row.get("target_revision") == "CGB-C" and row.get("informational") is True and
             row.get("included_in_cgb_e_denominator") is False and
             row.get("test_name") is None, f"mealybug-absent-state {row.get('case')}")

    denominator = data.get("denominator", {})
    eligible = sum(row.get("target_revision", "CGB-E") == "CGB-E" for row in cgb_e_rows)
    passed = sum(row.get("execution_status") == "pass" for row in cgb_e_rows)
    cgb_c_passes = sum(row.get("disposition") == "pass" for row in mealy_rows)
    need(eligible == 5 and denominator.get("cgb_e_eligible_cases") == eligible and
         denominator.get("cgb_e_completed_passes") == passed and
         denominator.get("cgb_c_informational_cases") == cgb_c_passes == 0,
         "denominator-integrity")

    boundary = data.get("phase12_ff55_boundary", {})
    need(boundary.get("test_name") == "cgb_speed_xfail_hdma_fails_closed" and
         boundary.get("distinct_from") == "samesuite_hdma_hdma_lcd_off" and
         boundary["test_name"] in expected_tests and bool(boundary.get("description")),
         "phase12-ff55-distinct-boundary")

    doc = (root / "docs/cgb-profile.md").read_text(encoding="utf-8")
    mirror = mirror_rows(doc)
    wanted = expected_mirror(suites)
    need(len(mirror) == len(set(mirror)) and set(mirror) == set(wanted), "docs-mirror-rows")
    hdma_policy = doc.split("The selected D-06 software behavior", 1)[1].split(
        "### HDMA source map", 1)[0]
    need("$83" in hdma_policy and "$02" in hdma_policy and "$00" in hdma_policy and
         "$80" in hdma_policy and "Pan Docs instead" in hdma_policy and "UNKNOWN" in hdma_policy,
         "d06-pandocs-conflict")

    if complete:
        need(all(row.get("execution_status") == "pass" for row in cgb_e_rows),
             "complete-cgb-e-evidence")
    else:
        need(same_rows[0].get("execution_status") == "pass", "tracer-case-not-executed")
        need(all(row.get("execution_status") == "pending" for row in same_rows[1:]) and
             magen_row.get("execution_status") == "pending", "tracer-expansion-before-gate")


def self_test(data: dict, root: Path) -> int:
    validate(data, root, complete=True)
    mutations = [
        ("status", "samesuite-passing-evidence", lambda d: d["suites"][0]["rows"][0].update({"disposition": "pending"})),
        ("revision", "samesuite-model-tags", lambda d: d["suites"][0].update({"repository_revision": "0" * 40})),
        ("hash", "samesuite-provenance", lambda d: d["suites"][0]["rows"][0].update({"rom_sha256": "0" * 64})),
        ("denominator", "denominator-integrity", lambda d: d["denominator"].update({"cgb_e_eligible_cases": 6})),
        ("test-name", "samesuite-test-binding", lambda d: d["suites"][0]["rows"][0].update({"test_name": "missing_test"})),
        ("missing-row", "samesuite-case-set", lambda d: d["suites"][0]["rows"].pop()),
        ("cgb-c-pass", "mealybug-absent-state", lambda d: d["suites"][2]["rows"][0].update({"disposition": "pass", "actual_result": "pass", "execution_status": "pass"})),
        ("cgb-c-denominator", "mealybug-rights-model", lambda d: d["suites"][2].update({"included_in_cgb_e_denominator": True})),
        ("cgb-c-absent", "suite-set", lambda d: d["suites"].pop()),
        ("rights-gate", "mealybug-rights-model", lambda d: d["suites"][2].update({"rights_gate": "closed"})),
        ("cgb-c-hardware-claim", "mealybug-hardware-claim", lambda d: d["suites"][2].update({"evidence_class": "hardware-backed CGB-E measurement"})),
        ("samesuite-data-outcome", "samesuite-execution-observation gdma_addr_mask", lambda d: d["suites"][0]["rows"][1]["execution"].update({"copied_bytes": 32})),
        ("magen-data-predicate", "magen-execution-observation", lambda d: d["suites"][1]["rows"][0]["execution"].update({"exact_map_bytes": 1023})),
        ("magen-control-set", "magen-execution-controls", lambda d: d["suites"][1]["rows"][0]["execution"].update({"controls": ["no-transfer", "wrong-bank"]})),
        ("missing-magen", "magen-case-set", lambda d: d["suites"][1]["rows"].clear()),
        ("phase12-boundary", "phase12-ff55-distinct-boundary", lambda d: d["phase12_ff55_boundary"].update({"test_name": "samesuite_hdma_hdma_lcd_off"})),
    ]
    with tempfile.TemporaryDirectory(prefix="gabbaboy-hdma-disposition-") as directory:
        for name, expected_error, mutate in mutations:
            twin = copy.deepcopy(data)
            mutate(twin)
            path = Path(directory) / f"{name}.json"
            path.write_text(json.dumps(twin), encoding="utf-8")
            try:
                changed = json.loads(path.read_text(encoding="utf-8"))
                validate(changed, root, complete=True)
            except (Mismatch, KeyError, IndexError, ValueError) as error:
                need(expected_error in str(error), f"self-test-wrong-rejection {name}: {error}")
            else:
                raise Mismatch(f"self-test-accepted {name}")
    print(f"cgb-hdma-dispositions self-test pass controls={len(mutations)}")
    return 0


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--tracer", action="store_true")
    group.add_argument("--complete", action="store_true")
    group.add_argument("--self-test", action="store_true")
    parser.add_argument("--record", type=Path, default=root / "tests/external/cgb-hdma-dispositions.json")
    args = parser.parse_args()
    try:
        data = json.loads(args.record.read_text(encoding="utf-8"))
        if args.self_test:
            return self_test(data, root)
        complete = bool(args.complete)
        validate(data, root, complete=complete)
    except (Mismatch, KeyError, ValueError, OSError, IndexError) as error:
        print(f"disposition-mismatch {error}")
        return 1
    case_count = data["denominator"]["cgb_e_completed_passes"]
    print(f"cgb-hdma-dispositions pass mode={'complete' if complete else 'tracer'} cgb-e-passes={case_count}/5 cgb-c=not-run:rights-gate-G1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
