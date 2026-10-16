#!/usr/bin/env python3
"""Verify inherited AGE row identities and Phase 14 research-gate ownership."""
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
INVENTORY = ROOT / "tests/external/cgb-corpus-inventory.json"
SPEED = ROOT / "tests/external/cgb-speed-dispositions.json"
AGE_MANIFEST = ROOT / "fixtures/age/manifest.json"
EXPECTED_TESTS = ROOT / "tests/expected-tests.txt"
MODEL_GATES = ROOT / "docs/model-gates.md"
AGE_COMMIT = "1f5bc10e2cb60b86c19f8d0287ff78f410c4f639"
RESEARCH14_GATES = {
    "GATE-01", "GATE-02", "GATE-10", "GATE-13", "GATE-14", "GATE-15",
    "GATE-17", "GATE-18", "GATE-19", "GATE-20", "GATE-24", "GATE-27",
    "GATE-28", "GATE-29", "GATE-32", "GATE-33", "GATE-34", "GATE-35",
    "GATE-36", "GATE-40", "GATE-41", "GATE-44", "GATE-47", "GATE-48",
    "GATE-49", "GATE-50", "GATE-54", "GATE-55", "GATE-62", "GATE-76",
    "GATE-77",
}
AGE_ROW_CASES = {
    "spsw-div-cgbBCE", "spsw-tima-cgbE", "spsw-tima-cgbBC",
    "spsw-stop-prefetch-cgbBCE", "spsw-interrupts-cgbE", "spsw-mode0-cgbBCE",
    "spsw-ch2-lc-delay-cgbBCE", "stat-mode-ds-cgbBCE", "stat-mode-cgbE",
    "stat-mode-sprites-ds-cgbBCE", "stat-mode-sprites-dmgC-cgbBCE",
    "stat-mode-window-ds-cgbBCE", "stat-mode-window-cgbBCE",
}
AGE_M3_CASES = {
    "m3-bg-lcdc", "m3-bg-lcdc-nocgb", "m3-bg-lcdc-ds",
    "m3-bg-scx", "m3-bg-scx-nocgb", "m3-bg-scx-ds",
}
MODE0_SEGMENTS = (
    ("initial-normal", "LY_TEST 456 * 3 / 4 - 10"),
    ("after-first-switch-to-double", "LY_TEST 125"),
    ("after-first-return-to-single", "LY_TEST 98"),
    ("after-second-switch-to-double", "LY_TEST 125"),
    ("after-second-return-to-single", "LY_TEST 98 + 456 / 4"),
)


class ContractError(Exception):
    pass


def need(ok: bool, code: str) -> None:
    if not ok:
        raise ContractError(code)


def read_json(path: Path) -> dict:
    need(path.is_file() and path.stat().st_size <= 2_000_000, "input-size-or-missing")
    value = json.loads(path.read_text(encoding="utf-8"))
    need(isinstance(value, dict), "input-shape")
    return value


def age_speed_rows(speed: dict) -> dict[str, dict]:
    suites = [row for row in speed.get("suites", []) if row.get("suite") == "age-test-roms"]
    need(len(suites) == 1, "age-speed-suite-count")
    rows = suites[0].get("rows")
    need(isinstance(rows, list), "age-speed-row-shape")
    result = {row.get("case"): row for row in rows}
    need(len(result) == len(rows), "age-speed-duplicate-case")
    return result


def case_identity(case: dict, fixture: dict, output: dict) -> str:
    source_sha = fixture.get("source_sha256")
    source = fixture["source_path"] + ("#" + source_sha if source_sha else "")
    return "|".join((
        "age@" + AGE_COMMIT,
        source,
        output["output_path"] + "#" + output["sha256"],
        case["model"], case["mode"], case["speed"], case["id"],
    ))


def mode0_semantic_assertions(rows: list[dict]) -> list[dict]:
    flat = b"".join(bytes.fromhex(row["expected_hex"]) for row in rows)
    actual = b"".join(bytes.fromhex(row["observed_hex"]) for row in rows)
    assertions: list[dict] = []
    for segment_index, (segment_id, ly_source) in enumerate(MODE0_SEGMENTS):
        base = segment_index * 24
        expected = flat[base:base + 4]
        observed = actual[base:base + 4]
        assertions.append({
            "id": f"spsw-mode0/{segment_id}/ly",
            "kind": "ly",
            "source_label": ly_source,
            "byte_offset": base,
            "byte_length": 4,
            "row_index": base // 8,
            "expected_hex": expected.hex().upper(),
            "observed_hex": observed.hex().upper(),
            "observed_disposition": "pass" if expected == observed else "fail",
        })
        for scx in range(10):
            for read_index in range(2):
                offset = base + 4 + scx * 2 + read_index
                expected_byte = flat[offset:offset + 1]
                observed_byte = actual[offset:offset + 1]
                assertions.append({
                    "id": f"spsw-mode0/{segment_id}/scx-{scx}/stat-read-{read_index + 1}",
                    "kind": "scx-stat",
                    "source_label": f"SCX_TEST {scx}; STAT read {read_index + 1}",
                    "byte_offset": offset,
                    "byte_length": 1,
                    "row_index": offset // 8,
                    "expected_hex": expected_byte.hex().upper(),
                    "observed_hex": observed_byte.hex().upper(),
                    "observed_disposition": "pass" if expected_byte == observed_byte else "fail",
                })
    return assertions


def expected_mode0_ids() -> list[str]:
    ids: list[str] = []
    for segment_id, _ in MODE0_SEGMENTS:
        ids.append(f"spsw-mode0/{segment_id}/ly")
        for scx in range(10):
            ids.extend((
                f"spsw-mode0/{segment_id}/scx-{scx}/stat-read-1",
                f"spsw-mode0/{segment_id}/scx-{scx}/stat-read-2",
            ))
    return ids


def _signature(rows: list[dict]) -> tuple[str, int]:
    mask = 0
    actual = bytearray()
    full = (1 << len(rows)) - 1
    for index, row in enumerate(rows):
        expected = bytes.fromhex(row["expected_hex"])
        observed = bytes.fromhex(row["observed_hex"])
        need(len(expected) == 8 and len(observed) == 8, "age-row-byte-width")
        actual.extend(observed)
        if expected == observed:
            mask |= 1 << index
    actual.extend((mask & 0xFF, (mask >> 8) & 0xFF))
    signature = hashlib.sha256(actual).hexdigest()
    need(mask <= full, "age-row-mask-range")
    return signature, mask


def _validated_age_fixture(root: Path, name: str, fixture: dict) -> tuple[Path, str, str, int, int]:
    file_name = fixture.get("file")
    need(isinstance(file_name, str) and 0 < len(file_name) <= 120,
         f"age-fixture-file:{name}")
    relative = PurePosixPath(file_name)
    need(not relative.is_absolute() and len(relative.parts) == 1
         and relative.name == name + ".gb" and ".." not in relative.parts,
         f"age-fixture-path:{name}")
    fixture_dir = (root / "fixtures/age").resolve()
    rom_path = (fixture_dir / relative.name).resolve()
    need(rom_path.parent == fixture_dir and rom_path.is_file()
         and rom_path.stat().st_size == 0x8000 and fixture.get("size_bytes") == 0x8000,
         f"age-fixture-bounds:{name}")

    def address(field: str) -> tuple[int, str]:
        value = fixture.get(field)
        need(isinstance(value, str) and len(value) <= 8, f"age-fixture-address:{name}:{field}")
        normalized = value.replace("$", "0x", 1)
        try:
            parsed = int(normalized, 0)
        except ValueError as exc:
            raise ContractError(f"age-fixture-address:{name}:{field}") from exc
        need(0 <= parsed <= 0xFFFF, f"age-fixture-address:{name}:{field}")
        return parsed, f"0x{parsed:04X}"

    results, results_arg = address("test_results_address")
    expected, expected_arg = address("expected_address")
    row_count, budget = fixture.get("rows"), fixture.get("budget_half_dots")
    need(type(row_count) is int and 1 <= row_count <= 16,
         f"age-fixture-row-bound:{name}")
    need(type(budget) is int and 0 < budget <= 71_000_000,
         f"age-fixture-budget-bound:{name}")
    need(results + row_count * 8 <= 0x10000
         and expected + 1 + row_count * 8 <= 0x8000,
         f"age-fixture-address-range:{name}")
    return rom_path, results_arg, expected_arg, row_count, budget


def _check_mode0_semantics(case: dict, row_assertions: list[dict]) -> None:
    expected = mode0_semantic_assertions(row_assertions)
    observed = case.get("semantic_assertions")
    need(isinstance(observed, list) and [r.get("id") for r in observed] == expected_mode0_ids(),
         "age-mode0-semantic-membership")
    need(observed == expected, "age-mode0-semantic-values")
    kinds = {r["id"]: r["kind"] for r in observed}
    need(all(kinds[key] == "ly" for key in kinds if key.endswith("/ly")),
         "age-mode0-ly-kind")
    need(all(kinds[key] == "scx-stat" for key in kinds if "/scx-" in key),
         "age-mode0-scx-stat-kind")
    need(not any("/ly/" in key or "/scx-stat/" in key for key in kinds),
         "age-mode0-merged-semantic-id")


def _check_live_age_rows(case_name: str, output: str,
                         assertions: list[dict]) -> list[tuple[str, str, str, str]]:
    records = []
    for line in output.splitlines():
        if not line.startswith("age-assertion-row "):
            continue
        match = re.fullmatch(
            r"age-assertion-row id=([^ ]+) expected=([0-9A-F]{16}) actual=([0-9A-F]{16}) disposition=(pass|fail)",
            line,
        )
        need(match is not None, f"age-live-row-event-invalid:{case_name}")
        records.append(match.groups())
    expected = [
        (row["id"], row["expected_hex"], row["observed_hex"], row["observed_disposition"])
        for row in assertions
    ]
    need(records == expected, f"age-live-row-drift:{case_name}")
    return records


def check_age_assertions(root: Path, inventory: dict, speed: dict,
                         run_guest: bool = False, runner: str | None = None,
                         guest_timeout_seconds: int = 15) -> tuple[int, int]:
    need(type(guest_timeout_seconds) is int and 1 <= guest_timeout_seconds <= 45,
         "age-guest-timeout-invalid")
    manifest = read_json(root / "fixtures/age/manifest.json")
    need(manifest.get("source", {}).get("commit") == AGE_COMMIT, "age-source-pin")
    fixtures = {row["file"][:-3]: row for row in manifest.get("fixtures", [])
                if row.get("fixture_class") == "age-row-oracle"}
    need(set(fixtures) == AGE_ROW_CASES, "age-row-fixture-set")
    checked_fixtures = {
        name: _validated_age_fixture(root, name, fixture)
        for name, fixture in fixtures.items()
    }
    speed_rows = age_speed_rows(speed)
    need(set(speed_rows) >= AGE_ROW_CASES, "age-speed-required-set")

    age_cases = {row["id"].removeprefix("age:"): row for row in inventory.get("cases", [])
                 if row.get("suite") == "age"}
    age_outputs = {row["id"].removeprefix("age:"): row for row in inventory.get("outputs", [])
                   if row.get("suite") == "age"}
    expected_age_names = AGE_ROW_CASES | AGE_M3_CASES
    need(set(age_cases) == expected_age_names and set(age_outputs) == expected_age_names,
         "age-identity-membership")
    expected_test_lines = {
        line.strip() for line in (root / "tests/expected-tests.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    used_tests: set[str] = set()

    source_by_id = {row["id"]: row for row in inventory.get("source_candidates", [])}
    fixture_by_source = {row.get("source_path"): row for row in manifest["fixtures"]}
    for case_name in sorted(expected_age_names):
        case_id = f"age:{case_name}"
        case = age_cases[case_name]
        output = age_outputs[case_name]
        source = source_by_id.get(case.get("source_id"), {})
        fixture = fixture_by_source.get(source.get("source_path"))
        need(fixture is not None, f"age-manifest-identity:{case_name}")
        need(case.get("id") == case_id and case.get("output_id") == output.get("id") == case_id
             and case.get("source_id") == output.get("source_id"),
             f"age-case-output-identity:{case_name}")
        need(output.get("admission_status") == "admitted"
             and output.get("selected_for_corpus") is True
             and output.get("sha256") == fixture.get("sha256"),
             f"age-output-admission:{case_name}")
        need(case.get("qualified_identity") == case_identity(case, fixture, output),
             f"age-qualified-identity:{case_name}")
        binding = case.get("test_binding", {})
        if case_name in AGE_M3_CASES:
            test_name = "cgb_age_m3_" + fixture["file"].removesuffix(".gb").replace("-", "_")
        else:
            test_name = "age_" + case_name.replace("-", "_")
        need(binding == {"ctest_name": test_name, "state": "bound"}
             and test_name in expected_test_lines and test_name not in used_tests,
             f"age-test-binding:{case_name}")
        used_tests.add(test_name)

    assertions_total = 0
    for case_name in sorted(AGE_ROW_CASES):
        case_id = f"age:{case_name}"
        case = age_cases[case_name]
        fixture = fixtures[case_name]
        external = speed_rows[case_name]
        row_count = fixture.get("rows")
        assertions = external.get("assertions")
        need(external.get("pinned_by") == case["test_binding"]["ctest_name"],
             f"age-inherited-pinner:{case_name}")
        need(isinstance(row_count, int) and isinstance(assertions, list)
             and len(assertions) == row_count,
             f"age-row-assertion-count:{case_name}")
        expected_assertions = []
        for index, assertion in enumerate(assertions):
            expected_id = assertion.get("id") if case_name == "stat-mode-cgbE" else f"{case_name}/row-{index:02d}"
            need(assertion.get("id") == expected_id and assertion.get("row_index") == index,
                 f"age-row-assertion-identity:{case_name}:{index}")
            expected_hex = assertion.get("expected_hex", "")
            observed_hex = assertion.get("observed_hex", "")
            need(re.fullmatch(r"[0-9A-F]{16}", str(expected_hex)) is not None
                 and re.fullmatch(r"[0-9A-F]{16}", str(observed_hex)) is not None,
                 f"age-row-assertion-hex:{case_name}:{index}")
            observed_disposition = "pass" if expected_hex == observed_hex else "fail"
            need(assertion.get("observed_disposition") == observed_disposition,
                 f"age-row-assertion-disposition:{case_name}:{index}")
            expected_assertions.append({
                "id": expected_id,
                "row_index": index,
                "expected_disposition": "pass",
                "observed_result": observed_disposition,
                "observed_disposition": observed_disposition,
                "expected_hex": expected_hex,
                "observed_hex": observed_hex,
            })
        signature, mask = _signature(assertions)
        full_mask = (1 << row_count) - 1
        expected_case_disposition = "pass" if mask == full_mask else "expected-failure"
        if external.get("disposition") == "expected-failure" and mask == full_mask:
            raise ContractError(f"age-xpass-counted-as-pass:{case_name}")
        need(external.get("disposition") == expected_case_disposition,
             f"age-case-disposition:{case_name}")
        if expected_case_disposition == "expected-failure":
            need(external.get("signature_sha256") == signature
                 and external.get("row_mask") == f"{mask:04X}",
                 f"age-inherited-signature:{case_name}")
        else:
            need(external.get("signature_sha256") == "" and external.get("row_mask") == "",
                 f"age-pass-signature-policy:{case_name}")

        contract = case.get("assertion_contract", {})
        need(contract.get("state") == "qualified" and contract.get("count") == row_count
             and contract.get("rows") == expected_assertions,
             f"age-inventory-assertion-contract:{case_name}")
        observed_result = "pass" if mask == full_mask else "fail"
        evaluator_status = "pass" if observed_result == "pass" else "xfail"
        execution = case.get("execution", {})
        need(execution.get("state") == "completed" and execution.get("terminal") is True
             and execution.get("observed_result") == observed_result
             and execution.get("evaluator_status") == evaluator_status
             and execution.get("assertion_count") == row_count
             and execution.get("row_mask") == f"{mask:04X}"
             and execution.get("signature_sha256") == signature,
             f"age-inventory-execution:{case_name}")
        evaluator = case.get("evaluator_disposition", {})
        expected_value = external.get("reason", "-") if observed_result == "fail" else "pass"
        need(evaluator.get("state") == expected_case_disposition
             and evaluator.get("value") == expected_value
             and evaluator.get("signature_sha256") == external.get("signature_sha256")
             and evaluator.get("row_mask") == external.get("row_mask"),
             f"age-inventory-disposition:{case_name}")
        if case_name == "spsw-mode0-cgbBCE":
            _check_mode0_semantics(case, assertions)
        assertions_total += row_count

    if run_guest:
        need(runner is not None and Path(runner).is_file(), "age-assertion-runner-missing")
        for case_name in sorted(AGE_ROW_CASES):
            fixture = fixtures[case_name]
            external = speed_rows[case_name]
            rom_path, results_arg, expected_arg, row_count, budget = checked_fixtures[case_name]
            args = [
                runner,
                str(rom_path), results_arg, expected_arg,
                str(row_count), str(budget),
                "--check-disposition", external["disposition"],
            ]
            if external["disposition"] == "expected-failure":
                args.extend((external["signature_sha256"], "0x" + external["row_mask"]))
            args.append("--phase14-observations")
            result = subprocess.run(args, cwd=root, text=True, capture_output=True,
                                    check=False, timeout=guest_timeout_seconds)
            need(result.returncode == 0,
                 f"age-live-guest-verdict:{case_name}:{result.returncode}:{result.stderr.strip()}")
            _check_live_age_rows(case_name, result.stdout, external["assertions"])
    return len(AGE_ROW_CASES), assertions_total


def _research_rows(inventory: dict) -> dict[str, dict]:
    rows = inventory.get("research14_dispositions")
    need(isinstance(rows, list), "research14-ledger-missing")
    result = {row.get("gate"): row for row in rows}
    need(len(result) == len(rows), "research14-duplicate-gate")
    need(set(result) == RESEARCH14_GATES, "research14-gate-set")
    return result


def check_research14(root: Path, inventory: dict) -> None:
    rows = _research_rows(inventory)
    doc = (root / "docs/model-gates.md").read_text(encoding="utf-8")
    gate_table = {}
    ledger_marker = "## Phase 14 research14 ownership ledger"
    need(ledger_marker in doc, "research14-document-ledger-missing")
    ledger_doc = doc.split(ledger_marker, 1)[1].split("## Release status", 1)[0]
    for line in doc.splitlines():
        if line not in ledger_doc.splitlines():
            continue
        match = re.match(
            r"\| (GATE-[0-9]{2}) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \|",
            line,
        )
        if match:
            gate_table[match.group(1)] = match.groups()[1:]
    primary_rows = {}
    for line in doc.splitlines():
        match = re.match(r"\| (GATE-[0-9]{2}) \| ([A-Z_]+) \| (.*?) \| (.*?) \|", line)
        if match:
            primary_rows[match.group(1)] = match.groups()[1:]
    for gate in sorted(RESEARCH14_GATES):
        row = rows[gate]
        for field in ("applicability", "source", "status", "model_gate", "evidence_kind", "evidence", "owner", "revisit"):
            need(isinstance(row.get(field), str) and row[field].strip(),
                 f"research14-field:{gate}:{field}")
        need(isinstance(row.get("tests"), list) and all(isinstance(x, str) and x for x in row["tests"]),
             f"research14-field:{gate}:tests")
        need(row["source"] == f"src/core/gabbaboy.c MODEL tag {gate}; docs/model-gates.md"
             and gate in (root / "src/core/gabbaboy.c").read_text(encoding="utf-8"),
             f"research14-source:{gate}")
        registered = {
            line.strip() for line in (root / "tests/expected-tests.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        need(all(test in registered for test in row["tests"]), f"research14-test-binding:{gate}")
        status = row["status"]
        need(status in ("limitation", "resolved"), f"research14-status:{gate}")
        need(row["evidence_kind"] in ("test", "limitation"),
             f"research14-evidence-kind:{gate}")
        if status == "resolved":
            need(row["evidence_kind"] == "test" and bool(row["tests"]),
                 f"research14-resolution-without-test:{gate}")
        else:
            need(row["evidence_kind"] == "test" or row["evidence"],
                 f"research14-limitation-unowned:{gate}")
        primary = primary_rows.get(gate)
        need(primary is not None, f"research14-primary-model-row:{gate}")
        primary_class, _, resolution = primary
        need(row["model_gate"] == f"{primary_class}/{resolution}",
             f"research14-model-gate-mismatch:{gate}")
        if status == "limitation":
            need(row["model_gate"] == "UNKNOWN/research:14"
                 and primary_class == "UNKNOWN" and "research:14" in resolution,
                 f"research14-model-gate-mismatch:{gate}")
        else:
            need(row["model_gate"].startswith("BOTH/basis=")
                 and primary_class == "BOTH" and "research:14" not in resolution,
                 f"research14-model-gate-mismatch:{gate}")
        table = gate_table.get(gate)
        need(table is not None, f"research14-document-row:{gate}")
        evidence_cell = row["evidence"]
        if gate == "GATE-49":
            evidence_cell = (
                "Six admitted AGE images remain source/reference comparisons; current pixel totals "
                "and signatures come from the complete receipt, so the mode-3/window model "
                "remains unresolved."
            )
        expected_cells = (
            row["applicability"], row["source"], status, row["evidence_kind"],
            evidence_cell, ", ".join(row["tests"]) if row["tests"] else "none",
            row["owner"], row["revisit"],
        )
        if gate in ("GATE-15", "GATE-34"):
            revisit = row["revisit"].lower()
            need(status == "limitation" and "independent dmg" in revisit
                 and "baseline revision" in revisit,
                 f"research14-dmg-retention-obligation:{gate}")
        need(table == expected_cells, f"research14-document-mirror:{gate}")
    need("Six admitted AGE images remain source/reference comparisons" in doc
         and "current pixel totals and signatures" in doc,
         "research14-image-evidence-unattributed")


def assertions_controls(root: Path, inventory: dict, speed: dict) -> None:
    check_age_assertions(root, inventory, speed)
    controls = []

    stat_rows = age_speed_rows(speed)["stat-mode-cgbE"]["assertions"]
    stat_row = stat_rows[0]
    live_event = (
        f"age-assertion-row id={stat_row['id']} expected={stat_row['expected_hex']} "
        f"actual={stat_row['observed_hex']} disposition={stat_row['observed_disposition']}"
    )
    _check_live_age_rows("stat-mode-cgbE", live_event, stat_rows[:1])
    controls.append("live-source-labelled-row")
    replacement = "0" * 16 if stat_row["observed_hex"] != "0" * 16 else "F" * 16
    altered_event = live_event.replace(
        f"actual={stat_row['observed_hex']}", f"actual={replacement}", 1,
    )
    try:
        _check_live_age_rows("stat-mode-cgbE", altered_event, stat_rows[:1])
    except ContractError as exc:
        need(str(exc) == "age-live-row-drift:stat-mode-cgbE",
             f"age-control-wrong-diagnostic:live-row-value-drift:{exc}")
        controls.append("live-row-value-drift")
    else:
        raise ContractError("age-control-accepted:live-row-value-drift")

    manifest = read_json(root / "fixtures/age/manifest.json")
    fixture = next(row for row in manifest["fixtures"]
                   if row.get("file") == "spsw-mode0-cgbBCE.gb")

    def fixture_rejected(name: str, mutate, expected: str) -> None:
        trial = copy.deepcopy(fixture)
        mutate(trial)
        try:
            _validated_age_fixture(root, "spsw-mode0-cgbBCE", trial)
        except ContractError as exc:
            need(str(exc) == expected, f"age-fixture-control-wrong-diagnostic:{name}:{exc}")
            controls.append(name)
            return
        raise ContractError(f"age-fixture-control-accepted:{name}")

    fixture_rejected("fixture-path-traversal", lambda row: row.update({"file": "../spsw-mode0-cgbBCE.gb"}),
                     "age-fixture-path:spsw-mode0-cgbBCE")
    fixture_rejected("fixture-size-drift", lambda row: row.update({"size_bytes": 0x8001}),
                     "age-fixture-bounds:spsw-mode0-cgbBCE")
    fixture_rejected("fixture-row-bound", lambda row: row.update({"rows": 17}),
                     "age-fixture-row-bound:spsw-mode0-cgbBCE")
    fixture_rejected("fixture-budget-bound", lambda row: row.update({"budget_half_dots": 71_000_001}),
                     "age-fixture-budget-bound:spsw-mode0-cgbBCE")
    fixture_rejected("fixture-address-range", lambda row: row.update({"expected_address": "$7FF0"}),
                     "age-fixture-address-range:spsw-mode0-cgbBCE")

    def rejected(name: str, mutate, expected: str) -> None:
        trial_inventory, trial_speed = copy.deepcopy(inventory), copy.deepcopy(speed)
        mutate(trial_inventory, trial_speed)
        try:
            check_age_assertions(root, trial_inventory, trial_speed)
        except ContractError as exc:
            need(str(exc) == expected, f"age-control-wrong-diagnostic:{name}:{exc}")
            controls.append(name)
            return
        raise ContractError(f"age-control-accepted:{name}")

    rejected("omitted-row-assertion", lambda _i, s: age_speed_rows(s)["spsw-mode0-cgbBCE"]["assertions"].pop(),
             "age-row-assertion-count:spsw-mode0-cgbBCE")
    rejected("duplicated-row-assertion", lambda _i, s: age_speed_rows(s)["spsw-mode0-cgbBCE"]["assertions"].__setitem__(
        -1, copy.deepcopy(age_speed_rows(s)["spsw-mode0-cgbBCE"]["assertions"][0])),
        "age-row-assertion-identity:spsw-mode0-cgbBCE:14")
    rejected("merged-ly-scx-id", lambda i, _s: next(c for c in i["cases"] if c["id"] == "age:spsw-mode0-cgbBCE")
             ["semantic_assertions"][0].update({"id": "spsw-mode0/ly-scx-merged"}),
             "age-mode0-semantic-membership")
    def make_xpass(_inventory, speed_copy):
        row = age_speed_rows(speed_copy)["spsw-mode0-cgbBCE"]
        for assertion in row["assertions"]:
            assertion["observed_hex"] = assertion["expected_hex"]
            assertion["observed_disposition"] = "pass"
    rejected("mixed-case-xpass", make_xpass, "age-xpass-counted-as-pass:spsw-mode0-cgbBCE")
    rejected("signature-drift", lambda _i, s: age_speed_rows(s)["spsw-mode0-cgbBCE"].update(
        {"signature_sha256": "0" * 64}), "age-inherited-signature:spsw-mode0-cgbBCE")
    print("cgb-age-assertion-controls pass controls=" + ",".join(controls))


def research_controls(root: Path, inventory: dict) -> None:
    check_research14(root, inventory)
    controls = []

    def rejected(name: str, mutate, expected: str) -> None:
        trial = copy.deepcopy(inventory)
        mutate(trial)
        try:
            check_research14(root, trial)
        except ContractError as exc:
            need(str(exc) == expected, f"research14-control-wrong-diagnostic:{name}:{exc}")
            controls.append(name)
            return
        raise ContractError(f"research14-control-accepted:{name}")

    rejected("missing-gate", lambda d: d["research14_dispositions"].pop(), "research14-gate-set")
    rejected("duplicate-gate", lambda d: d["research14_dispositions"].append(
        copy.deepcopy(d["research14_dispositions"][0])), "research14-duplicate-gate")
    rejected("owner-omitted", lambda d: next(r for r in d["research14_dispositions"]
             if r["gate"] == "GATE-01").update({"owner": ""}), "research14-field:GATE-01:owner")
    rejected("source-omitted", lambda d: next(r for r in d["research14_dispositions"]
             if r["gate"] == "GATE-01").update({"source": ""}), "research14-field:GATE-01:source")
    rejected("applicability-omitted", lambda d: next(r for r in d["research14_dispositions"]
             if r["gate"] == "GATE-01").update({"applicability": ""}),
             "research14-field:GATE-01:applicability")
    rejected("dmg-obligation-removed", lambda d: next(r for r in d["research14_dispositions"]
             if r["gate"] == "GATE-15").update({"revisit": "Revisit only with better evidence."}),
             "research14-dmg-retention-obligation:GATE-15")
    rejected("false-gate-promotion", lambda d: next(r for r in d["research14_dispositions"]
             if r["gate"] == "GATE-34").update({"status": "resolved", "model_gate": "BOTH/basis=guest"}),
             "research14-model-gate-mismatch:GATE-34")
    print("cgb-research14-dispositions-controls pass controls=" + ",".join(controls))


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--assertions", action="store_true")
    group.add_argument("--assertions-controls", action="store_true")
    group.add_argument("--research14", action="store_true")
    group.add_argument("--research14-controls", action="store_true")
    parser.add_argument("--runner")
    parser.add_argument("--guest-timeout-seconds", type=int, default=15)
    args = parser.parse_args()
    try:
        inventory = read_json(INVENTORY)
        speed = read_json(SPEED)
        if args.assertions:
            count, assertions = check_age_assertions(ROOT, inventory, speed,
                run_guest=True, runner=args.runner,
                guest_timeout_seconds=args.guest_timeout_seconds)
            print(f"cgb-age-assertion-identity pass cases={count} rows={assertions} mode0-semantic=105 age-identities=19")
        elif args.assertions_controls:
            assertions_controls(ROOT, inventory, speed)
        elif args.research14:
            check_research14(ROOT, inventory)
            print(f"cgb-research14-dispositions pass gates={len(RESEARCH14_GATES)} unknown={len([r for r in inventory['research14_dispositions'] if r['status'] == 'limitation'])}")
        else:
            research_controls(ROOT, inventory)
    except (ContractError, KeyError, ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"phase14-contract mismatch: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
