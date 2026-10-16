#!/usr/bin/env python3
"""Validate public CGB claims against pinned source, inventory and result evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve()
MAX_JSON_BYTES = 32 * 1024 * 1024
SAMESUITE_REVISION = "f15645fb049a47ea235f6d2c9a033e72d8087901"
CLAIM_DOCS = {
    "profile": "docs/cgb-profile.md",
    "audio": "docs/audio-and-playback.md",
    "gates": "docs/model-gates.md",
    "corpus": "docs/cgb-corpus.md",
    "readme": "README.md",
    "preview": "docs/preview.md",
    "unreleased": "docs/support/unreleased.md",
    "player": "src/player/limitations.h",
}
PROFILE_ROWS = {
    ("$FF76", "DMG"): ("stop", "ignored"),
    ("$FF76", "CGB"): ("channel 2:channel 1 digital DAC values", "ignored"),
    ("$FF76", "COMPAT"): ("$FF", "ignored"),
    ("$FF77", "DMG"): ("stop", "ignored"),
    ("$FF77", "CGB"): ("channel 4:channel 3 digital DAC values", "ignored"),
    ("$FF77", "COMPAT"): ("$FF", "ignored"),
}
APU_TESTS = {
    "cgb_apu_wave_latch",
    "cgb_apu_wave_fetch",
    "cgb_apu_power",
    "cgb_apu_off_writes",
    "cgb_apu_wave_access",
    "cgb_apu_div_stop",
    "cgb_apu_transition_controls",
    "cgb_apu_trigger_length_sweep",
    "cgb_pcm_tracer",
    "cgb_pcm_tracer_control",
    "cgb_apu_wave_direct_ram_control",
    "cgb_tables_io",
    "cgb_tables_io_mutated_doc",
}
REQUIRED_TEXT = {
    "profile": (
        "digital DAC inputs", "CGB compatibility mode reads `$FF`",
        "CH3 sample latch", "CGB-CPU-E software model",
        "physical CGB-E", "cgb-apu-dispositions.json",
        "cgb-corpus-receipt.json",
    ),
    "audio": (
        "CGB digital PCM registers", "before NR50 level scaling",
        "compatibility mode reads `$FF`", "CH3 output uses a sample byte",
        "next timer fetch", "no physical CGB-E timing or waveform",
        "cgb_apu_transition_controls", "cgb_pcm_tracer",
    ),
    "corpus": (
        "author expectation", "differential evidence", "current complete receipt",
        "physical CGB-E", "analog audio/color", "general game compatibility",
        "cgb-corpus-inventory.json", "cgb-apu-dispositions.json",
        "verify-cgb-corpus-report.py",
        "SameBoy agreement is differential evidence; author-encoded targets",
    ),
}
UNQUALIFIED_CLAIM = re.compile(
    r"(?:physical\s+CGB(?:-E)?\s+(?:hardware\s+)?(?:is\s+)?"
    r"(?:qualified|measured|verified|proven|passes all)|"
    r"CGB-E\s+hardware\s+(?:proves|measures|qualifies)|"
    r"physical\s+CGB-E\s+analog\s+(?:audio|color)\s+(?:is\s+)?"
    r"(?:qualified|measured|verified|proven)|"
    r"general game compatibility\s+(?:is\s+)?(?:qualified|proven|claimed))",
    re.IGNORECASE,
)
XFAIL_AS_PASS_CLAIM = re.compile(
    r"(?:matched\s+xfails?|expected[- ]failures?)[\w\s-]{0,35}"
    r"(?:are|count(?:ed)? as|treated as|included in).{0,35}(?:guest\s+|observed\s+)?passes?",
    re.IGNORECASE,
)
MARKERS = {
    "profile": ("<!-- cgb-apu-claims-begin -->", "<!-- cgb-apu-claims-end -->"),
    "io": ("<!-- cgb-io-visibility-begin -->", "<!-- cgb-io-visibility-end -->"),
    "audio": ("<!-- cgb-apu-audio-claims-begin -->", "<!-- cgb-apu-audio-claims-end -->"),
    "corpus": ("<!-- cgb-corpus-evidence-begin -->", "<!-- cgb-corpus-evidence-end -->"),
    "gates": ("<!-- cgb-research14-ledger-begin -->", "<!-- cgb-research14-ledger-end -->"),
}


class ContractError(Exception):
    """A named failure in the public-claims contract."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ContractError(code)


def bounded_json(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    try:
        if path.stat().st_size > MAX_JSON_BYTES:
            raise ContractError(f"input-too-large:{relative}")
        value = json.loads(path.read_text(encoding="utf-8"))
    except ContractError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractError(f"input-unavailable:{relative}") from error
    require(type(value) is dict, f"input-invalid:{relative}")
    return value


def read_surfaces() -> dict[str, str]:
    result: dict[str, str] = {}
    for key, relative in CLAIM_DOCS.items():
        try:
            result[key] = (ROOT / relative).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise ContractError(f"surface-unavailable:{relative}") from error
    return result


def marked_block(text: str, key: str) -> str:
    start_marker, end_marker = MARKERS[key]
    start = text.find(start_marker)
    end = text.find(end_marker)
    require(start >= 0 and end > start, f"missing-claim-markers:{key}")
    return text[start + len(start_marker):end]


def parse_markdown_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def validate_profile_matrix(block: str) -> None:
    rows: dict[tuple[str, str], tuple[str, str]] = {}
    for line in block.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = parse_markdown_row(line)
        if len(cells) == 6 and cells[0] in ("$FF76", "$FF77"):
            rows[(cells[0], cells[1])] = (cells[2], cells[3])
    for key, expected in PROFILE_ROWS.items():
        require(rows.get(key) == expected, f"io-matrix-cell-mismatch:{key[0]}:{key[1]}")


def validate_ff76_tracer() -> None:
    try:
        core = (ROOT / "src/core/gabbaboy.c").read_text(encoding="utf-8")
        tables = (ROOT / "tests/test_cgb_tables.c").read_text(encoding="utf-8")
        guest = (ROOT / "tests/test_cgb_apu.c").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ContractError("ff76-source-evidence-unavailable") from error
    require("[0x76] = { IOC(DMG_STOP), IOC(PCM12), IOC(CONST_FF), IOS_PANDOCS }" in core
            and "[0x77] = { IOC(DMG_STOP), IOC(PCM34), IOC(CONST_FF), IOS_PANDOCS }" in core,
            "ff76-source-mode-map-mismatch")
    table_start = tables.find("static int pcm_io_contract(")
    table_end = tables.find("static int undocumented_io_contract(", table_start)
    require(table_start >= 0 and table_end > table_start, "ff76-table-oracle-missing")
    table_contract = tables[table_start:table_end]
    require("0x76u, 0x77u" in table_contract and "IO_PCM12, IO_PCM34" in table_contract
            and "IO_CONST_FF" in table_contract and "IO_DMG_STOP" in table_contract,
            "ff76-table-oracle-mismatch")
    guest_start = guest.find("static int read_pcm12_as_guest(")
    tracer_start = guest.find("static int cgb_pcm_tracer(", guest_start)
    require(guest_start >= 0 and tracer_start > guest_start, "ff76-guest-tracer-missing")
    guest_contract = guest[guest_start:tracer_start]
    tracer_end = guest.find("static size_t configured_pcm_program(", tracer_start)
    tracer_contract = guest[tracer_start:tracer_end]
    require("0xF0u; program[length++] = 0x76u" in guest_contract
            and "events[i].address == 0xFF76u" in guest_contract
            and "0xF0u : 0x0Fu" in tracer_contract and "value_matches" in tracer_contract
            and "read_pcm12_as_guest(&result)" in tracer_contract,
            "ff76-guest-assertion-mismatch")


def validate_same_suite(dispositions: dict[str, Any], inventory: dict[str, Any]) -> None:
    suite = bounded_json("fixtures/samesuite/manifest.json")
    require(suite.get("suite", {}).get("revision") == SAMESUITE_REVISION,
            "samesuite-source-revision-mismatch")
    require(dispositions.get("schema") == "gabbaboy-cgb-apu-dispositions-v1",
            "apu-disposition-schema-mismatch")
    require(dispositions.get("suite", {}).get("revision") == SAMESUITE_REVISION,
            "apu-disposition-source-revision-mismatch")
    cases = dispositions.get("cases")
    require(type(cases) is list and len(cases) == 70, "apu-source-membership-mismatch")
    sources = {item.get("path"): item for item in suite.get("source_files", [])
               if type(item) is dict}
    fixture_records = {item.get("source_path"): item for item in suite.get("fixtures", [])
                       if type(item) is dict}
    inv_cases = {item.get("id"): item for item in inventory.get("cases", [])
                 if type(item) is dict}
    ids: set[str] = set()
    for item in cases:
        source = item.get("source_path")
        case_id = "samesuite:" + str(source)
        require(case_id not in ids, "apu-source-membership-duplicate")
        ids.add(case_id)
        source_record = sources.get(source)
        fixture_record = fixture_records.get(source)
        case = inv_cases.get(case_id)
        require(type(source_record) is dict and type(fixture_record) is dict and type(case) is dict,
                "apu-source-membership-mismatch")
        require(item.get("source_sha256") == source_record.get("sha256"),
                "apu-source-digest-mismatch")
        require(item.get("rom_sha256") == fixture_record.get("sha256") and
                item.get("fixture_path") == "fixtures/samesuite/" + fixture_record.get("file", ""),
                "apu-output-identity-mismatch")
        require(item.get("test_name") == case.get("test_binding", {}).get("ctest_name"),
                "apu-test-binding-mismatch")
        require(item.get("author_expectation", {}).get("value") == "pass",
                "apu-author-expectation-mismatch")
        execution = item.get("execution", {})
        require(execution.get("state") == "completed" and execution.get("terminal") is True
                and execution.get("observed_result") in ("pass", "fail"),
                "apu-terminal-observation-missing")
        require(item.get("evaluator_disposition", {}).get("value") in
                ("pass", "expected-failure"), "apu-evaluator-disposition-invalid")
        try:
            rom_bytes = (ROOT / item["fixture_path"]).read_bytes()
        except (OSError, KeyError, TypeError) as error:
            raise ContractError("apu-source-or-output-unavailable") from error
        require(hashlib.sha256(rom_bytes).hexdigest() == item.get("rom_sha256"),
                "apu-output-digest-mismatch")
    expected_ids = {"samesuite:" + str(item.get("path")) for item in suite["source_files"]
                    if str(item.get("path", "")).startswith("apu/")}
    require(ids == expected_ids and len(expected_ids) == 70, "apu-source-membership-mismatch")
    require(sum(case.get("suite") == "samesuite" and case.get("id", "").startswith("samesuite:apu/")
                for case in inv_cases.values()) == 70, "apu-inventory-membership-mismatch")


def ledger_rows(block: str) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for line in block.splitlines():
        if line.lstrip().startswith("| GATE-"):
            cells = parse_markdown_row(line)
            require(len(cells) == 9, "research14-ledger-row-shape")
            gate = cells[0]
            require(gate not in rows, "research14-ledger-membership")
            rows[gate] = cells
    return rows


def validate_ledger(block: str, inventory: dict[str, Any]) -> None:
    expected: dict[str, list[str]] = {}
    dispositions = inventory.get("research14_dispositions")
    require(type(dispositions) is list, "research14-dispositions-unavailable")
    for item in dispositions:
        gate = item.get("gate")
        expected[gate] = [
            gate, item.get("applicability"), item.get("source"), item.get("status"),
            item.get("evidence_kind"), item.get("evidence"), ", ".join(item.get("tests", [])),
            item.get("owner"), item.get("revisit"),
        ]
    actual = ledger_rows(block)
    require(set(actual) == set(expected) and len(expected) == 31,
            "research14-ledger-membership")
    for gate, row in expected.items():
        if gate == "GATE-49":
            row[5] = ("Six admitted AGE images remain source/reference comparisons; current pixel totals "
                      "and signatures come from the complete receipt, so the mode-3/window model "
                      "remains unresolved.")
        require(actual.get(gate) == row, f"research14-ledger-row-mismatch:{gate}")


def validate_product_surfaces(surfaces: dict[str, str]) -> None:
    limits = {
        "readme": "No physical CGB-E, analog audio, or general game compatibility claim follows",
        "preview": "No physical CGB-E audio, analog output, or general game compatibility claim follows",
        "unreleased": "These tests do not qualify physical CGB-E, analog audio/color, or general game compatibility",
        "player": "physical CGB-E remains UNKNOWN/POLICY",
    }
    for key, limit in limits.items():
        text = " ".join(surfaces[key].split())
        require("FF76/FF77" in text and "digital DAC inputs" in text,
                f"product-claim-missing:{key}")
        require(re.search(r"compatibility mode reads `?\$FF`?", text, re.IGNORECASE) is not None,
                f"product-compatibility-policy-missing:{key}")
        require("CGB-CPU-E software model" in text,
                f"product-model-scope-missing:{key}")
        require(re.search(r"(?:DMG APU|APU.{0,20}DMG).{0,35}(?:model|playback)|"
                          r"(?:model|playback).{0,35}(?:DMG APU|APU.{0,20}DMG)",
                          text, re.IGNORECASE) is not None,
                f"product-playback-scope-missing:{key}")
        require(limit.lower() in text.lower(), f"product-limit-missing:{key}")
    all_public = "\n".join(surfaces[key] for key in limits)
    require(XFAIL_AS_PASS_CLAIM.search(all_public) is None,
            "xfail-inflated-public-claim")


def validate_observation_counts(cases: list[dict[str, Any]], claimed: dict[str, Any]) -> None:
    total = len(cases)
    passes = sum(case.get("observed_result") == "pass" and
                 case.get("evaluator_status") == "pass" for case in cases)
    fails = sum(case.get("observed_result") == "fail" for case in cases)
    matched = sum(case.get("matched_xfail") is True for case in cases)
    rows = [row for case in cases for row in case.get("assertions", [])]
    passed_rows = sum(row.get("observed_result") == "pass" and
                      row.get("evaluator_status") == "pass" for row in rows)
    derived = {
        "attempted_cases": sum(case.get("attempted") is True for case in cases),
        "completed_cases": sum(case.get("completed") is True for case in cases),
        "observed_pass_cases": passes,
        "observed_fail_cases": fails,
        "matched_xfail_cases": matched,
        "assertions": len(rows),
        "passing_assertions": passed_rows,
    }
    require(passes + fails == total and all(
        claimed.get(key) == value for key, value in derived.items()),
        "receipt-counts-mismatch")


def validate_suite_summaries(receipt: dict[str, Any], inventory: dict[str, Any]) -> None:
    cases = receipt.get("cases", [])
    summaries = receipt.get("suite_summary", [])
    require(type(summaries) is list, "receipt-suite-summary-missing")
    by_suite = {summary.get("suite"): summary for summary in summaries if type(summary) is dict}
    required_suites = {case.get("suite") for case in inventory.get("cases", [])}
    require(set(by_suite) == required_suites and len(by_suite) == len(required_suites),
            "receipt-suite-summary-membership-mismatch")
    for suite in required_suites:
        group = [case for case in cases if case.get("suite") == suite]
        summary = by_suite[suite]
        rows = [row for case in group for row in case.get("assertions", [])]
        pixels = sum(case.get("details", {}).get("image_pixels", 0) for case in group)
        mismatches = sum(case.get("details", {}).get("pixel_mismatches", 0) for case in group)
        values = {
            "admitted_cases": len(group),
            "applicable_cases": len(group),
            "attempted_cases": sum(case.get("attempted") is True for case in group),
            "completed_cases": sum(case.get("completed") is True for case in group),
            "observed_pass_cases": sum(case.get("observed_result") == "pass" and
                                        case.get("evaluator_status") == "pass" for case in group),
            "observed_fail_cases": sum(case.get("observed_result") == "fail" for case in group),
            "matched_xfail_cases": sum(case.get("matched_xfail") is True for case in group),
            "not_run_cases": sum(case.get("completed") is not True for case in group),
            "assertions": len(rows),
            "passing_assertions": sum(row.get("observed_result") == "pass" and
                                      row.get("evaluator_status") == "pass" for row in rows),
            "failing_assertions": sum(row.get("observed_result") == "fail" for row in rows),
            "image_pixels": pixels,
            "pixel_mismatches": mismatches,
            "required_eligible_cases": inventory["counts"]["by_suite"][suite]["required_cases"],
        }
        require(all(summary.get(key) == value for key, value in values.items()),
                "receipt-suite-derived-counts-mismatch:" + str(suite))


def validate_static(surfaces: dict[str, str] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    surfaces = surfaces or read_surfaces()
    inventory = bounded_json("tests/external/cgb-corpus-inventory.json")
    dispositions = bounded_json("tests/external/cgb-apu-dispositions.json")
    require(inventory.get("schema") == "gabbaboy-cgb-corpus-inventory-v1",
            "inventory-schema-mismatch")
    require(inventory.get("counts", {}).get("required_cases") == 107,
            "inventory-required-denominator-mismatch")
    profile = marked_block(surfaces["profile"], "profile")
    audio = marked_block(surfaces["audio"], "audio")
    corpus = marked_block(surfaces["corpus"], "corpus")
    gates = marked_block(surfaces["gates"], "gates")
    validate_profile_matrix(marked_block(surfaces["profile"], "io"))
    validate_ff76_tracer()
    validate_same_suite(dispositions, inventory)
    validate_ledger(gates, inventory)
    try:
        cmake = (ROOT / "tests/CMakeLists.txt").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ContractError("apu-test-registration-unavailable") from error
    registered_tests = set(re.findall(r"add_test\(NAME\s+([A-Za-z0-9_]+)", cmake))
    require(APU_TESTS <= registered_tests, "apu-test-registration-missing")
    for key, phrases in REQUIRED_TEXT.items():
        block = " ".join({"profile": profile, "audio": audio, "corpus": corpus}[key].split())
        for phrase in phrases:
            require(phrase in block, f"claim-evidence-or-limit-missing:{key}:{phrase}")
    report = (ROOT / "tests/scripts/verify-cgb-corpus-report.py").read_text(encoding="utf-8")
    require('SCHEMA = "gabbaboy-cgb-corpus-receipt-v1"' in report,
            "receipt-schema-contract-mismatch")
    require("--begin-run" in corpus and "--from-ctest" in corpus,
            "receipt-protocol-evidence-missing")
    all_public = "\n".join(surfaces.values())
    require(UNQUALIFIED_CLAIM.search(all_public) is None, "unqualified-hardware-or-game-claim")
    for token in ("eight observed guest passes", "8 terminal guest passes", "62 exact current-observation xfails",
                  "18,208 pixels differ", "4,784 result assertions", "25 observed passes and 82 matched"):
        require(token not in all_public, "stale-observed-count-in-public-claim")
    validate_product_surfaces(surfaces)
    validate_observation_counts(
        [{"observed_result": "pass", "evaluator_status": "pass", "attempted": True,
          "completed": True, "matched_xfail": False, "assertions": [
              {"observed_result": "pass", "evaluator_status": "pass"}]},
         {"observed_result": "fail", "evaluator_status": "xfail", "attempted": True,
          "completed": True, "matched_xfail": True, "assertions": [
              {"observed_result": "fail", "evaluator_status": "xfail"}]}],
        {"attempted_cases": 2, "completed_cases": 2, "observed_pass_cases": 1,
         "observed_fail_cases": 1, "matched_xfail_cases": 1, "assertions": 2,
         "passing_assertions": 1},
    )
    return inventory, dispositions


def validate_receipt(path: Path, inventory: dict[str, Any]) -> dict[str, Any]:
    try:
        if path.stat().st_size > MAX_JSON_BYTES:
            raise ContractError("receipt-too-large")
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except ContractError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractError("receipt-unavailable-or-invalid") from error
    require(type(receipt) is dict and receipt.get("schema") == "gabbaboy-cgb-corpus-receipt-v1"
            and receipt.get("version") == 1, "receipt-schema-mismatch")
    require(receipt.get("status") == "complete", "receipt-not-complete")
    identity = receipt.get("identity", {})
    cases = receipt.get("cases", [])
    expected = {case.get("id"): case for case in inventory.get("cases", [])}
    actual = {case.get("id"): case for case in cases if type(case) is dict}
    require(set(actual) == set(expected) and len(actual) == 107,
            "receipt-case-membership-mismatch")
    require(identity.get("case_ids") == sorted(expected), "receipt-identity-membership-mismatch")
    require(identity.get("hardware_qualified") is False, "receipt-hardware-qualification-claim")
    require(identity.get("inventory_sha256") == hashlib.sha256(
        (ROOT / "tests/external/cgb-corpus-inventory.json").read_bytes()).hexdigest(),
        "receipt-inventory-ancestry-mismatch")
    try:
        current = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                 check=True, capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError) as error:
        raise ContractError("receipt-current-revision-unavailable") from error
    require(identity.get("core_revision") == current, "receipt-not-current-revision")
    expected_names: dict[str, str] = {}
    for case_id, source_case in expected.items():
        binding = source_case.get("test_binding", {})
        expected_names[case_id] = binding.get("ctest_name")
        observed = actual[case_id]
        require(observed.get("test_name") == expected_names[case_id] and
                observed.get("suite") == source_case.get("suite"),
                "receipt-case-binding-mismatch")
        require(observed.get("attempted") is True and observed.get("completed") is True and
                observed.get("observed_result") in ("pass", "fail"),
                "receipt-terminal-case-missing")
        require((observed.get("observed_result") == "pass" and
                 observed.get("evaluator_status") == "pass" and
                 observed.get("matched_xfail") is False) or
                (observed.get("observed_result") == "fail" and
                 observed.get("evaluator_status") == "xfail" and
                 observed.get("matched_xfail") is True),
                "receipt-observation-disposition-mismatch")
        evidence = observed.get("evidence", {})
        for field in ("source_id", "output_id", "source_path", "output_path", "output_sha256"):
            expected_value = source_case.get(field)
            if expected_value is not None:
                require(evidence.get(field) == expected_value,
                        "receipt-source-result-ancestry-mismatch")
    aggregate = ["cgb_samesuite_apu_suite"]
    require(identity.get("case_ctest_names") == sorted(expected_names.values()) and
            identity.get("aggregate_ctest_names") == aggregate and
            identity.get("ctest_names") == sorted(expected_names.values() + aggregate),
            "receipt-ctest-ancestry-mismatch")
    require(receipt.get("run", {}).get("ctest_cases") == 108 and
            receipt.get("run", {}).get("id") == identity.get("run_id") and
            bool(receipt.get("run", {}).get("run_nonce_sha256")),
            "receipt-nonce-or-stream-mismatch")
    rows = [row for case in cases for row in case.get("assertions", [])]
    pixels = sum(case.get("details", {}).get("image_pixels", 0) for case in cases)
    mismatches = sum(case.get("details", {}).get("pixel_mismatches", 0) for case in cases)
    claimed_counts = receipt.get("counts", {})
    validate_observation_counts(cases, claimed_counts)
    require(claimed_counts.get("admitted_cases") == len(expected) and
            claimed_counts.get("applicable_cases") == len(expected) and
            claimed_counts.get("required_eligible_cases") == len(expected) and
            claimed_counts.get("not_run_cases") == 0 and
            claimed_counts.get("excluded_cases") == 0 and
            claimed_counts.get("image_pixels") == pixels and
            claimed_counts.get("pixel_mismatches") == mismatches and
            claimed_counts.get("failing_assertions") == len(rows) - claimed_counts.get("passing_assertions", 0),
            "receipt-derived-counts-mismatch")
    validate_suite_summaries(receipt, inventory)
    cohorts = receipt.get("required_behavior_cohorts", [])
    expected_cohorts = {
        "age-row-contracts": 13,
        "magentests-source-predicates": 5,
        "mooneye-cgb-cases": 9,
        "samesuite-apu-original-assertions": 70,
        "samesuite-dma-source-assertions": 4,
    }
    actual_cohorts = {item.get("name"): item for item in cohorts if type(item) is dict}
    require(set(actual_cohorts) == set(expected_cohorts),
            "receipt-behavior-cohort-membership-mismatch")
    for name, required in expected_cohorts.items():
        item = actual_cohorts[name]
        require(item.get("required_cases") == required and
                item.get("observed_pass_cases", 0) > 0 and
                item.get("observed_pass_cases", 0) + item.get("matched_xfail_cases", 0) == required,
                "receipt-behavior-cohort-evidence-mismatch:" + name)
    return receipt


def assert_control(name: str, fn, expected: str) -> None:
    try:
        fn()
    except ContractError as error:
        require(expected in str(error), f"self-test-wrong-diagnostic:{name}")
        return
    raise ContractError(f"self-test-control-not-detected:{name}")


def mutate_block(text: str, key: str, old: str, new: str) -> str:
    start_marker, end_marker = MARKERS[key]
    start = text.find(start_marker)
    end = text.find(end_marker)
    require(start >= 0 and end > start, f"self-test-marker-missing:{key}")
    block_start = start + len(start_marker)
    block = text[block_start:end]
    require(old in block, f"self-test-subject-missing:{key}")
    block = block.replace(old, new, 1)
    return text[:block_start] + block + text[end:]


def run_self_test() -> None:
    baseline = read_surfaces()
    validate_static(baseline)

    def matrix_mutant() -> None:
        changed = dict(baseline)
        changed["profile"] = changed["profile"].replace(
            "| $FF76 | CGB | channel 2:channel 1 digital DAC values | ignored | IMPL | PANDOCS |",
            "| $FF76 | CGB | $FF | ignored | IMPL | PANDOCS |", 1)
        validate_static(changed)
    assert_control("wrong-matrix-cell", matrix_mutant, "io-matrix-cell-mismatch:$FF76:CGB")

    def missing_compatibility() -> None:
        changed = dict(baseline)
        changed["profile"] = changed["profile"].replace(
            "| $FF76 | COMPAT | $FF | ignored | IMPL | PANDOCS |", "", 1)
        validate_static(changed)
    assert_control("omitted-compatibility", missing_compatibility, "io-matrix-cell-mismatch:$FF76:COMPAT")

    def hardware_overclaim() -> None:
        changed = dict(baseline)
        changed["corpus"] = changed["corpus"].replace(
            "<!-- cgb-corpus-evidence-end -->",
            "Physical CGB-E is qualified by this corpus.\n<!-- cgb-corpus-evidence-end -->", 1)
        validate_static(changed)
    assert_control("hardware-overclaim", hardware_overclaim, "unqualified-hardware-or-game-claim")

    def product_hardware_overclaim() -> None:
        changed = dict(baseline)
        changed["preview"] += "\nPhysical CGB-E is qualified by this corpus.\n"
        validate_static(changed)
    assert_control("product-hardware-overclaim", product_hardware_overclaim,
                   "unqualified-hardware-or-game-claim")

    def analog_overclaim() -> None:
        changed = dict(baseline)
        changed["corpus"] = changed["corpus"].replace(
            "<!-- cgb-corpus-evidence-end -->",
            "Physical CGB-E analog audio is measured by this corpus.\n<!-- cgb-corpus-evidence-end -->", 1)
        validate_static(changed)
    assert_control("analog-overclaim", analog_overclaim, "unqualified-hardware-or-game-claim")

    def author_oracle_swap() -> None:
        inventory = bounded_json("tests/external/cgb-corpus-inventory.json")
        payload = bounded_json("tests/external/cgb-apu-dispositions.json")
        payload["cases"][0]["author_expectation"]["value"] = "expected-failure"
        assert_control("author-versus-oracle-swap",
                       lambda: validate_same_suite(payload, inventory),
                       "apu-author-expectation-mismatch")

    author_oracle_swap()

    def prose_author_oracle_swap() -> None:
        changed = dict(baseline)
        changed["corpus"] = changed["corpus"].replace(
            "agreement is differential evidence; author-encoded targets",
            "is the author oracle; author-encoded targets", 1)
        validate_static(changed)
    assert_control("prose-author-oracle-swap", prose_author_oracle_swap,
                   "claim-evidence-or-limit-missing:corpus")

    def missing_gate() -> None:
        changed = dict(baseline)
        changed["gates"] = mutate_block(changed["gates"], "gates",
                                        "| GATE-01 |", "| GATE-XX |")
        validate_static(changed)
    assert_control("omitted-gate", missing_gate, "research14-ledger-membership")

    def omitted_limit() -> None:
        changed = dict(baseline)
        changed["corpus"] = mutate_block(changed["corpus"], "corpus",
                                         "analog audio/color", "digital output")
        validate_static(changed)
    assert_control("omitted-limit", omitted_limit, "claim-evidence-or-limit-missing:corpus")

    def omitted_evidence_link() -> None:
        changed = dict(baseline)
        changed["corpus"] = mutate_block(changed["corpus"], "corpus",
                                         "[`cgb-corpus-inventory.json`](../tests/external/cgb-corpus-inventory.json)",
                                         "[missing inventory link]")
        validate_static(changed)
    assert_control("omitted-evidence-link", omitted_evidence_link,
                   "claim-evidence-or-limit-missing:corpus")

    def inflated_xfail_passes() -> None:
        validate_observation_counts(
            [{"observed_result": "pass", "evaluator_status": "pass", "attempted": True,
              "completed": True, "matched_xfail": False, "assertions": []},
             {"observed_result": "fail", "evaluator_status": "xfail", "attempted": True,
              "completed": True, "matched_xfail": True, "assertions": []}],
            {"attempted_cases": 2, "completed_cases": 2, "observed_pass_cases": 2,
             "observed_fail_cases": 0, "matched_xfail_cases": 1, "assertions": 0,
             "passing_assertions": 0},
        )
    assert_control("xfail-inflated-pass-count", inflated_xfail_passes, "receipt-counts-mismatch")

    def product_xfail_inflation() -> None:
        changed = dict(baseline)
        changed["readme"] += "\nMatched xfails are counted as observed passes.\n"
        validate_product_surfaces(changed)
    assert_control("xfail-inflated-product-claim", product_xfail_inflation,
                   "xfail-inflated-public-claim")

    def product_compatibility_omission() -> None:
        changed = dict(baseline)
        changed["readme"] = changed["readme"].replace(
            "CGB compatibility mode reads `$FF`", "CGB compatibility mode is undocumented", 1)
        validate_product_surfaces(changed)
    assert_control("product-compatibility-omission", product_compatibility_omission,
                   "product-compatibility-policy-missing:readme")

    def product_analog_limit_omission() -> None:
        changed = dict(baseline)
        changed["preview"] = changed["preview"].replace(
            "analog output", "digital output", 1)
        validate_product_surfaces(changed)
    assert_control("product-analog-limit-omission", product_analog_limit_omission,
                   "product-limit-missing:preview")
    print("cgb-corpus-claims self-test pass controls=14")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    try:
        inventory, _ = validate_static()
        if args.receipt:
            receipt = validate_receipt(args.receipt, inventory)
            counts = receipt["counts"]
            print("cgb-corpus-claims pass receipt=" + str(args.receipt) +
                  " cases=" + str(counts["completed_cases"]) +
                  " passes=" + str(counts["observed_pass_cases"]) +
                  " matched-xfails=" + str(counts["matched_xfail_cases"]) +
                  " assertions=" + str(counts["assertions"]))
        else:
            print("cgb-corpus-claims pass mode=static cases=107 gates=31 apu-sources=70")
        if args.self_test:
            run_self_test()
    except (ContractError, KeyError, TypeError, ValueError) as error:
        print("cgb-corpus-claims fail: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
