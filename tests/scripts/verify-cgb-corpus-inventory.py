#!/usr/bin/env python3
"""Fail-closed validation for the pinned Phase 14 CGB corpus selection."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "tests/external/cgb-corpus-inventory.json"
DOC = ROOT / "docs/cgb-corpus.md"
MAGEN_DOC = ROOT / "fixtures/magentests/ELIGIBILITY.md"
MAX_INPUT_BYTES = 2_000_000
MAX_FIXTURE_BYTES = 1_000_000
SUITES = ("age", "samesuite", "magentests", "mooneye")
PINS = {
    "mooneye": ("31510e12eea6286d36eea060a6adde755e1067aa", "2b8c52424a49a2a7466cf631fd8992c53d0de2fa"),
    "samesuite": ("f15645fb049a47ea235f6d2c9a033e72d8087901", None),
    "age": ("1f5bc10e2cb60b86c19f8d0287ff78f410c4f639", "2fece1a678edb18c1664efd7328a430a79c70be4"),
    "magentests": ("3f9c090f16e5a721db776febb9ba7d773e1c819c", None),
}
COUNTS = {
    "age": {"source_candidates": 19, "output_rows": 19, "required_cases": 19},
    "samesuite": {"source_candidates": 74, "output_rows": 74, "required_cases": 74},
    "magentests": {"source_candidates": 5, "output_rows": 7, "required_cases": 5},
    "mooneye": {"source_candidates": 83, "output_rows": 9, "required_cases": 9},
}
SOURCE_DIGESTS = {
    "age": "a8b8e09ed54ff30a848afa7ad0f6ca768c040314b768ba23bcad0b645d301cdb",
    "samesuite": "6362d2d4ec7b2d7781d592ff85837685412302a8b51ea593022cacaef4d7d8d6",
    "magentests": "3124e9d8044be19eaa3e516645586a20680fa054332b61f59800aa85b7e963d6",
    "mooneye": "f834287698586e0f22ff60824d0f1accf281e72075babafe7da3a4a502ed6f72",
}
OUTPUT_DIGESTS = {
    "age": "81ab90df48da3b888a210201fbd86e644f17fb83c9d14d18b9ee964add9832ce",
    "samesuite": "c94ca9b8cafe7a5510ebf5abe353c350d69875fd3e36c8c420e0812ea61430b9",
    "magentests": "928c0ce4fcb770aa48d1959ee92c9fba480f548d42d8a79721942d3525f2119c",
    "mooneye": "af6927aab0463e1041551182817ba6c7a651ae3afe791314c186164805e818a5",
}
CASE_DIGESTS = {
    "age": "7bfeeb4af1ad26e59ac9e61a2f38cadb2a20667acf49589ccf38c68093217dfa",
    "samesuite": "84cedec9d9f8790e5d9d1a4f84cde95d2b48152d37d3f38e9153f4af0c3eaea3",
    "magentests": "643808a7d9cf535b372b2df844f46fbe2b4e7454cd87e964302466c039e91b92",
    "mooneye": "3a1c17eefff83b0b693fc5cecc67bec944b08e9f042cff8cb6a5bb6f668e27ed",
}
MOONEYE_REQUIRED = {
    "acceptance/instr/daa.s",
    "acceptance/timer/div_write.s",
    "acceptance/timer/tim00.s",
    "acceptance/timer/tim00_div_trigger.s",
    "misc/boot_regs-cgb.s",
    "misc/boot_div-cgbABCDE.s",
    "misc/boot_hwio-C.s",
    "misc/bits/unused_hwio-C.s",
    "misc/ppu/vblank_stat_intr-C.s",
}
MOONEYE_TRACER_HEADER = ";   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS"
MOONEYE_CTEST_NAMES = {
    "misc/boot_regs-cgb.s": "cgb_corpus_mooneye_boot_regs_cgb",
    "misc/boot_div-cgbABCDE.s": "cgb_corpus_mooneye_boot_div_cgbABCDE",
    "misc/boot_hwio-C.s": "cgb_corpus_mooneye_boot_hwio_C",
    "misc/bits/unused_hwio-C.s": "cgb_corpus_mooneye_unused_hwio_C",
    "acceptance/instr/daa.s": "cgb_corpus_mooneye_daa",
    "acceptance/timer/div_write.s": "cgb_corpus_mooneye_div_write",
    "acceptance/timer/tim00.s": "cgb_corpus_mooneye_tim00",
    "acceptance/timer/tim00_div_trigger.s": "cgb_corpus_mooneye_tim00_div_trigger",
    "misc/ppu/vblank_stat_intr-C.s": "cgb_corpus_mooneye_vblank_stat_intr_C",
}
AGE_M3_CASE_IDS = {
    "m3-bg-lcdc-cgbBCE": "age:m3-bg-lcdc",
    "m3-bg-lcdc-nocgb-ncmBCE": "age:m3-bg-lcdc-nocgb",
    "m3-bg-lcdc-ds-cgbBCE": "age:m3-bg-lcdc-ds",
    "m3-bg-scx-cgbBCE": "age:m3-bg-scx",
    "m3-bg-scx-nocgb-ncmBCE": "age:m3-bg-scx-nocgb",
    "m3-bg-scx-ds-cgbBCE": "age:m3-bg-scx-ds",
}
AGE_M3_XFAIL_REASON = "expected-failure:cgb-e-mode3-reference-mismatch"
IMMUTABLE_OUTPUT_FIELDS = ("id", "suite", "source_id", "output_path", "selected_for_corpus", "case_ids")
IMMUTABLE_CASE_FIELDS = ("id", "suite", "source_id", "output_id", "model", "mode", "speed", "author_expectation")


class Mismatch(Exception):
    pass


def need(condition: bool, code: str) -> None:
    if not condition:
        raise Mismatch(code)


def bounded_json(path: Path) -> dict:
    size = path.stat().st_size
    need(size <= MAX_INPUT_BYTES, "inventory-size-limit")
    value = json.loads(path.read_text(encoding="utf-8"))
    need(isinstance(value, dict), "inventory-shape")
    return value


def digest_rows(rows: list[dict], projection) -> str:
    canonical = sorted(
        json.dumps(projection(row), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        for row in rows
    )
    return hashlib.sha256("\n".join(canonical).encode("utf-8")).hexdigest()


def safe_relative(value: object, code: str) -> None:
    need(isinstance(value, str) and value and len(value) <= 240, code)
    path = PurePosixPath(value)
    need(not path.is_absolute() and all(part not in ("", ".", "..") for part in path.parts), code)
    need("\x00" not in value and "\\" not in value, code)


def check_tree_pins(data: dict) -> None:
    trees = data.get("source_trees")
    need(isinstance(trees, dict) and set(trees) == set(SUITES), "source-tree-set")
    for suite, (commit, tree) in PINS.items():
        row = trees[suite]
        need(row.get("commit") == commit and row.get("tree") == tree, f"source-pin:{suite}")
        need(isinstance(row.get("repository"), str) and row["repository"], f"source-repository:{suite}")
        need(isinstance(row.get("license"), str) and row["license"], f"source-license:{suite}")


def check_rosters(data: dict) -> tuple[dict[str, dict], dict[str, dict], dict[str, dict]]:
    sources = data.get("source_candidates")
    outputs = data.get("outputs")
    cases = data.get("cases")
    need(isinstance(sources, list) and len(sources) <= 300, "source-roster-shape")
    need(isinstance(outputs, list) and len(outputs) <= 300, "output-roster-shape")
    need(isinstance(cases, list) and len(cases) <= 300, "case-roster-shape")
    source_by_id: dict[str, dict] = {}
    output_by_id: dict[str, dict] = {}
    case_by_id: dict[str, dict] = {}

    for row in sources:
        suite = row.get("suite")
        need(suite in SUITES, "source-suite")
        safe_relative(row.get("source_path"), "source-path")
        need(row.get("source_commit") == PINS[suite][0], f"source-row-pin:{suite}")
        need(row.get("id") == f"{suite}:{row['source_path']}", f"source-id:{suite}")
        need(row["id"] not in source_by_id, "duplicate-source-id")
        need(row.get("selection", {}).get("state") in ("required", "excluded"), "source-selection-state")
        need(row.get("selection", {}).get("reason"), "source-selection-reason")
        need(isinstance(row.get("family"), str) and row["family"], "source-family")
        need(isinstance(row.get("applicability"), dict), "source-applicability")
        need(isinstance(row.get("rights"), dict) and row["rights"].get("state") == "clear", "source-rights")
        need(isinstance(row.get("build"), dict) and row["build"].get("toolchain"), "source-build")
        need(isinstance(row.get("oracle"), dict) and row["oracle"].get("class"), "source-oracle")
        source_by_id[row["id"]] = row

    for suite in SUITES:
        suite_rows = [r for r in sources if r["suite"] == suite]
        need(len(suite_rows) == COUNTS[suite]["source_candidates"], f"source-count:{suite}")

    mooneye = [r for r in sources if r["suite"] == "mooneye"]
    pass_count = sum(bool(r["applicability"].get("cgb_pass_membership")) for r in mooneye)
    fail_count = sum(bool(r["applicability"].get("cgb_fail_membership")) for r in mooneye)
    both_count = sum(bool(r["applicability"].get("cgb_pass_membership")) and bool(r["applicability"].get("cgb_fail_membership")) for r in mooneye)
    need((pass_count, fail_count, both_count) == (59, 26, 2), "mooneye-header-membership-counts")
    div_write = source_by_id["mooneye:acceptance/timer/div_write.s"]
    need(div_write["applicability"].get("header_quote") == MOONEYE_TRACER_HEADER, "mooneye-header-div_write")
    need(div_write["selection"]["state"] == "required", "mooneye-unsuffixed-div_write-filtered")
    for path in ("acceptance/instr/daa.s", "acceptance/timer/tim00.s"):
        need(source_by_id[f"mooneye:{path}"]["selection"]["state"] == "required", f"mooneye-unsuffixed-filtered:{path}")
    required_paths = {r["source_path"] for r in mooneye if r["selection"]["state"] == "required"}
    need(required_paths == MOONEYE_REQUIRED, "mooneye-required-source-set")
    same_apu = [r for r in sources if r["suite"] == "samesuite" and r["source_path"].startswith("apu/")]
    need(len(same_apu) == 70 and all(
        r["applicability"].get("readme_quote") == "CPU-CGB-E – passes all tests" for r in same_apu
    ), "samesuite-readme-applicability")
    for suite in SUITES:
        suite_rows = [r for r in sources if r["suite"] == suite]
        need(digest_rows(suite_rows, lambda r: r) == SOURCE_DIGESTS[suite], f"source-candidate-fingerprint:{suite}")

    for row in outputs:
        suite = row.get("suite")
        need(suite in SUITES, "output-suite")
        need(row.get("id") not in output_by_id, "duplicate-output-id")
        need(row.get("id") and row.get("source_id") in source_by_id, "output-source-reference")
        need(source_by_id[row["source_id"]]["suite"] == suite, "output-source-suite")
        safe_relative(row.get("output_path"), "output-path")
        need(row.get("admission_status") in ("admitted", "built-scratch-not-admitted", "source-only"), "output-admission-status")
        need(isinstance(row.get("case_ids"), list) and len(row["case_ids"]) <= 100, "output-case-list")
        output_by_id[row["id"]] = row
    for suite in SUITES:
        rows = [r for r in outputs if r["suite"] == suite]
        need(len(rows) == COUNTS[suite]["output_rows"], f"output-count:{suite}")
        need(digest_rows(rows, lambda r: {k: r[k] for k in IMMUTABLE_OUTPUT_FIELDS}) == OUTPUT_DIGESTS[suite],
             f"output-membership-fingerprint:{suite}")

    for row in cases:
        suite = row.get("suite")
        need(suite in SUITES, "case-suite")
        need(row.get("id") not in case_by_id, "duplicate-case-id")
        source = source_by_id.get(row.get("source_id"))
        output = output_by_id.get(row.get("output_id"))
        need(source is not None and source["selection"]["state"] == "required", "case-source-not-selected")
        need(output is not None, "case-output-reference")
        need(output["source_id"] == source["id"] and output["suite"] == suite, "case-source-output-mismatch")
        need(row.get("model") == "CGB-CPU-E" and row.get("mode") in ("native", "compat")
             and row.get("speed") in ("normal", "double"), "case-model-mode-speed")
        need(isinstance(row.get("author_expectation"), dict) and row["author_expectation"].get("class"),
             "case-author-expectation")
        need(isinstance(row.get("evaluator_disposition"), dict) and row["evaluator_disposition"].get("state"),
             "case-evaluator-disposition")
        need(isinstance(row.get("execution"), dict), "case-execution")
        need(isinstance(row.get("assertion_contract"), dict), "case-assertion-contract")
        need(isinstance(row.get("test_binding"), dict), "case-test-binding")
        need(not row.get("hardware_qualified", False), "hardware-claim-forbidden")
        if suite == "samesuite" and source["source_path"].startswith("apu/"):
            alias = source["source_path"].removesuffix(".asm")
            test_name = "cgb_samesuite_apu_" + alias.removeprefix("apu/").replace("/", "_").replace("-", "_")
            execution = row["execution"]
            evaluator = row["evaluator_disposition"]
            assertions = row["assertion_contract"]
            binding = row["test_binding"]
            assertion_rows = assertions.get("rows")
            need(output["admission_status"] == "admitted", f"samesuite-apu-output-not-admitted:{source['source_path']}")
            need(row["author_expectation"].get("class") == "source-CorrectResults"
                 and row["author_expectation"].get("value") == "pass",
                 f"samesuite-apu-author-expectation:{source['source_path']}")
            need(evaluator.get("state") in ("pass", "expected-failure")
                 and execution.get("state") == "completed" and execution.get("terminal") is True
                 and execution.get("observed_result") in ("pass", "fail"),
                 f"samesuite-apu-execution:{source['source_path']}")
            need(not (evaluator.get("state") == "expected-failure"
                      and execution.get("observed_result") == "pass"),
                 f"samesuite-apu-xfail-counted-as-pass:{source['source_path']}")
            need(assertions.get("state") == "qualified" and isinstance(assertion_rows, list)
                 and len(assertion_rows) == assertions.get("count") and assertion_rows,
                 f"samesuite-apu-assertions:{source['source_path']}")
            need(binding.get("state") == "bound" and binding.get("ctest_name") == test_name,
                 f"samesuite-apu-test-binding:{source['source_path']}")
            need(re.fullmatch(r"[0-9a-f]{64}", str(execution.get("signature_sha256", "")))
                 and execution.get("signature_sha256") == evaluator.get("signature_sha256"),
                 f"samesuite-apu-signature:{source['source_path']}")
        if output["admission_status"] == "source-only":
            execution = row["execution"]
            need(execution.get("observed_result") is None and execution.get("terminal") is not True,
                 "source-only-output-execution")
        if output["admission_status"] != "admitted":
            execution = row["execution"]
            need(execution.get("observed_result") is None and execution.get("terminal") is not True,
                 "unadmitted-output-marked-executed")
        case_by_id[row["id"]] = row
        need(row["id"] in output["case_ids"], "output-missing-case-link")

    for suite in SUITES:
        rows = [r for r in cases if r["suite"] == suite]
        need(len(rows) == COUNTS[suite]["required_cases"], f"required-case-count:{suite}")
        need(digest_rows(rows, lambda r: {k: r[k] for k in IMMUTABLE_CASE_FIELDS}) == CASE_DIGESTS[suite],
             f"required-case-fingerprint:{suite}")
    for output in outputs:
        need(set(output["case_ids"]) <= set(case_by_id), "output-unknown-case")
        expected_ids = {c["id"] for c in cases if c["output_id"] == output["id"]}
        need(set(output["case_ids"]) == expected_ids, "output-case-mapping")
    return source_by_id, output_by_id, case_by_id


def manifest_rows(root: Path) -> dict[str, dict[str, dict]]:
    paths = {
        "age": ("fixtures/age/manifest.json", "fixtures"),
        "samesuite": ("fixtures/samesuite/manifest.json", "fixtures"),
        "magentests": ("fixtures/magentests/manifest.json", "fixtures"),
        "mooneye": ("fixtures/mooneye-cgb/manifest.json", "fixtures"),
    }
    result: dict[str, dict[str, dict]] = {}
    for suite, (path, key) in paths.items():
        manifest = bounded_json(root / path)
        if suite == "age":
            need(manifest.get("source", {}).get("commit") == PINS[suite][0]
                 and manifest.get("source", {}).get("tree") == PINS[suite][1], f"manifest-pin:{suite}")
        elif suite == "mooneye":
            need(manifest.get("suite", {}).get("revision") == PINS[suite][0]
                 and manifest.get("suite", {}).get("tree_sha1") == PINS[suite][1], f"manifest-pin:{suite}")
        else:
            need(manifest.get("suite", {}).get("revision") == PINS[suite][0], f"manifest-pin:{suite}")
        result[suite] = {}
        for fixture in manifest.get(key, []):
            file_name = fixture.get("file", fixture.get("rom"))
            if file_name:
                result[suite][file_name] = fixture
    return result


def check_admitted_outputs(root: Path, outputs: dict[str, dict], sources: dict[str, dict]) -> None:
    manifests = manifest_rows(root)
    expected_manifest = {
        "age": "fixtures/age/manifest.json",
        "samesuite": "fixtures/samesuite/manifest.json",
        "magentests": "fixtures/magentests/manifest.json",
        "mooneye": "fixtures/mooneye-cgb/manifest.json",
    }
    admitted = [row for row in outputs.values() if row["admission_status"] == "admitted"]
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", *[r["output_path"] for r in admitted]],
        check=True, capture_output=True,
    ).stdout.decode("utf-8", "replace").split("\0")
    tracked_set = set(filter(None, tracked))
    for row in admitted:
        suite = row["suite"]
        manifest_root = PurePosixPath(expected_manifest[suite]).parent
        name = PurePosixPath(row["output_path"]).relative_to(manifest_root).as_posix()
        fixture = manifests[suite].get(name)
        need(fixture is not None, f"manifest-output-missing:{row['id']}:{name}")
        source_path = sources[row["source_id"]]["source_path"]
        manifest_source = fixture.get("source_path")
        if suite == "magentests":
            manifest_source = f"{fixture.get('source_dir')}/main.asm"
        need(manifest_source == source_path, f"manifest-source-mismatch:{row['id']}")
        need(row.get("manifest_ref") == expected_manifest[suite], f"manifest-reference:{row['id']}")
        need(row.get("sha256") == fixture.get("sha256") and row.get("size_bytes") == fixture.get("size_bytes"),
             f"manifest-digest-mismatch:{row['id']}")
        need(row["output_path"] in tracked_set, f"admitted-output-untracked:{row['id']}")
        need(isinstance(fixture.get("size_bytes"), int) and 0 < fixture["size_bytes"] <= MAX_FIXTURE_BYTES,
             f"manifest-output-size-limit:{row['id']}")
        file_path = root / row["output_path"]
        need(file_path.is_file(), f"admitted-output-missing:{row['id']}")
        need(file_path.stat().st_size == fixture["size_bytes"], f"admitted-output-size:{row['id']}")
        content = file_path.read_bytes()
        need(len(content) == fixture["size_bytes"], f"admitted-output-size:{row['id']}")
        need(hashlib.sha256(content).hexdigest() == fixture["sha256"], f"admitted-output-hash:{row['id']}")


def check_mooneye_qualification(root: Path, sources: dict[str, dict],
                                outputs: dict[str, dict], cases: dict[str, dict]) -> None:
    manifest = bounded_json(root / "fixtures/mooneye-cgb/manifest.json")
    manifest_rows_by_source = {row.get("source_path"): row for row in manifest.get("fixtures", [])}
    manifest_rows_by_alias = {row.get("alias"): row for row in manifest.get("fixtures", [])}
    required_case_ids = {f"mooneye:{path}" for path in MOONEYE_CTEST_NAMES}
    mooneye_case_ids = {cid for cid, row in cases.items() if row["suite"] == "mooneye"}
    need(mooneye_case_ids == required_case_ids, "mooneye-qualified-case-set")
    need(set(manifest_rows_by_alias) == {
        "boot_regs-cgb", "boot_div-cgbABCDE", "boot_hwio-C", "unused_hwio-C", "daa",
        "div_write", "tim00", "tim00_div_trigger", "vblank_stat_intr-C",
    }, "mooneye-manifest-case-set")
    expected_roms = [row.get("rom") for row in manifest.get("fixtures", [])]
    need(manifest.get("required_roms") == expected_roms and len(expected_roms) == 9,
         "mooneye-required-rom-set")
    raw_manifest_digest = hashlib.sha256((root / "fixtures/mooneye-cgb/manifest.json").read_bytes()).hexdigest()

    for cid in sorted(required_case_ids):
        case = cases[cid]
        source = sources[case["source_id"]]
        fixture = manifest_rows_by_source.get(source["source_path"])
        need(fixture is not None, f"mooneye-manifest-source:{cid}")
        alias = fixture["alias"]
        output = outputs.get(case["output_id"])
        need(output is not None and output["admission_status"] == "admitted",
             f"mooneye-output-not-admitted:{alias}")
        need(output.get("manifest_ref") == "fixtures/mooneye-cgb/manifest.json"
             and output.get("output_path") == f"fixtures/mooneye-cgb/{fixture['rom']}"
             and output.get("sha256") == fixture["sha256"]
             and output.get("size_bytes") == fixture["size_bytes"], f"mooneye-output-manifest:{alias}")
        need(case.get("model") == "CGB-CPU-E" and case.get("mode") == "compat"
             and case.get("speed") == "normal", f"mooneye-case-model-mode:{alias}")
        need(fixture.get("eligible") is True and fixture.get("expect") == "pass"
             and fixture.get("model_pass") == ["cgb-cpu-e"]
             and fixture.get("mode") == "compat (header $143 bit 7 clear)"
             and fixture.get("cart_header_143") == "0x00", f"mooneye-manifest-model-mode:{alias}")
        need(case.get("author_expectation", {}).get("class") == "author-header"
             and case["author_expectation"].get("value") == source["applicability"].get("header_quote"),
             f"mooneye-author-expectation:{alias}")
        disposition = fixture.get("observed_disposition")
        expected_state = "expected-failure" if disposition == "expected-failure" else "pass"
        expected_result = "fail" if disposition == "expected-failure" else "pass"
        expected_status = "xfail" if disposition == "expected-failure" else "pass"
        evaluation = case.get("evaluator_disposition", {})
        need(evaluation.get("reference") == "fixtures/mooneye-cgb/manifest.json"
             and evaluation.get("state") == expected_state and evaluation.get("value") == disposition,
             f"mooneye-evaluator-disposition:{alias}")
        execution = case.get("execution", {})
        need(execution.get("state") == "completed" and execution.get("terminal") is True
             and execution.get("observed_result") == expected_result
             and execution.get("evaluator_status") == expected_status
             and execution.get("manifest_sha256") == raw_manifest_digest
             and execution.get("budget_half_dots") == fixture.get("budget_half_dots"),
             f"mooneye-execution-verdict:{alias}")
        pc_field = "pass_callback_pc" if disposition == "pass" else "fail_callback_pcs"
        expected_callbacks = [fixture[pc_field]] if disposition == "pass" else fixture[pc_field]
        callback = execution.get("callback_pc")
        need(callback in expected_callbacks, f"mooneye-assertion-callback:{alias}")
        result_pc = fixture.get("result_pc")
        need(execution.get("result_pc") == result_pc, f"mooneye-assertion-result:{alias}")
        contract = case.get("assertion_contract", {})
        rows = contract.get("rows")
        need(contract.get("state") == "qualified" and contract.get("count") == 1
             and isinstance(rows, list) and len(rows) == 1, f"mooneye-assertion-contract:{alias}")
        assertion = rows[0]
        need(assertion.get("id") == "ld-b-b-result"
             and assertion.get("expected_disposition") == fixture.get("expect")
             and assertion.get("observed_result") == expected_result
             and assertion.get("evaluator_status") == expected_status
             and assertion.get("callback_pc") == callback
             and assertion.get("result_pc") == result_pc, f"mooneye-assertion-signature:{alias}")
        binding = case.get("test_binding", {})
        need(binding.get("state") == "bound"
             and binding.get("ctest_name") == MOONEYE_CTEST_NAMES[source["source_path"]],
             f"mooneye-test-binding:{alias}")


def check_age_m3_qualification(root: Path, cases: dict[str, dict]) -> None:
    manifest = bounded_json(root / "fixtures/age/manifest.json")
    ppu = bounded_json(root / "tests/external/cgb-ppu-dispositions.json")
    commit = manifest.get("source", {}).get("commit")
    need(commit == PINS["age"][0], "age-m3-source-pin")
    fixtures = {
        row.get("file", "").removesuffix(".gb"): row
        for row in manifest.get("fixtures", [])
        if row.get("fixture_class") == "age-m3-reference"
    }
    suites = {row.get("suite"): row for row in ppu.get("suites", [])}
    ppu_rows = {row.get("case"): row for row in suites.get("age", {}).get("rows", [])}
    need(set(fixtures) == set(AGE_M3_CASE_IDS) and set(ppu_rows) == set(AGE_M3_CASE_IDS),
         "age-m3-case-set")

    for case, inventory_id in AGE_M3_CASE_IDS.items():
        fixture = fixtures[case]
        ppu_row = ppu_rows[case]
        inventory_case = cases.get(inventory_id)
        need(inventory_case is not None, f"age-m3-inventory-case:{case}")
        identity = "/".join((
            "age@" + commit,
            fixture["source_path"] + "#" + fixture["source_sha256"],
            fixture["file"] + "#" + fixture["sha256"],
            fixture["model"], fixture["mode"], fixture["speed"], case,
        ))
        mismatches = fixture.get("pixel_mismatch_count")
        signature = fixture.get("pixel_mismatch_signature_sha256")
        need(fixture.get("qualification_status") == "executed"
             and fixture.get("expected_role") == "pass-target"
             and fixture.get("execution_result") == "fail"
             and fixture.get("disposition") == "expected-failure"
             and fixture.get("reason") == AGE_M3_XFAIL_REASON,
             f"age-m3-manifest-disposition:{case}")
        need(fixture.get("case_id") == identity
             and fixture.get("pixel_assertion_count") == 23040
             and isinstance(mismatches, int) and 0 < mismatches <= 23040
             and re.fullmatch(r"[0-9a-f]{64}", str(signature)) is not None,
             f"age-m3-manifest-signature:{case}")
        need(ppu_row.get("case_id") == identity
             and ppu_row.get("disposition") == fixture.get("disposition")
             and ppu_row.get("reason") == fixture.get("reason")
             and ppu_row.get("observed_result") == "fail"
             and ppu_row.get("evaluator_status") == "xfail"
             and ppu_row.get("model") == "CGB-E"
             and ppu_row.get("mode") == fixture.get("mode")
             and ppu_row.get("speed") == fixture.get("speed")
             and ppu_row.get("pixel_assertion_count") == 23040
             and ppu_row.get("pixel_mismatch_count") == mismatches
             and ppu_row.get("pixel_mismatch_signature_sha256") == signature,
             f"age-m3-ppu-disposition:{case}")
        need(ppu_row.get("source_sha256") == fixture.get("source_sha256")
             and ppu_row.get("rom_sha256") == fixture.get("sha256")
             and ppu_row.get("reference_sha256") == fixture.get("reference", {}).get("sha256")
             and ppu_row.get("pinned_by") == "cgb_age_m3_" + case.replace("-", "_"),
             f"age-m3-ppu-identity:{case}")

        expected_mode = "native" if fixture["mode"] == "native-cgb" else "compat"
        need(inventory_case.get("model") == "CGB-CPU-E"
             and inventory_case.get("mode") == expected_mode
             and inventory_case.get("speed") == fixture.get("speed"),
             f"age-m3-inventory-model-mode:{case}")
        need(inventory_case.get("case_identity") == identity
             and inventory_case.get("author_expectation", {}).get("class") == "author-verified-source"
             and "CGB-E" in inventory_case["author_expectation"].get("value", ""),
             f"age-m3-inventory-identity-or-author:{case}")
        execution = inventory_case.get("execution", {})
        need(execution.get("state") == "completed" and execution.get("terminal") is True
             and execution.get("terminal_observation") == "frame-counter-vblank-5"
             and execution.get("observed_result") == "fail"
             and execution.get("evaluator_status") == "xfail"
             and execution.get("case_id") == identity
             and execution.get("assertion_count") == 23040
             and execution.get("mismatch_count") == mismatches
             and execution.get("signature_sha256") == signature,
             f"age-m3-inventory-execution:{case}")
        evaluator = inventory_case.get("evaluator_disposition", {})
        need(evaluator.get("reference") == "tests/external/cgb-ppu-dispositions.json#age"
             and evaluator.get("state") == "expected-failure"
             and evaluator.get("value") == AGE_M3_XFAIL_REASON
             and evaluator.get("signature_sha256") == signature,
             f"age-m3-inventory-evaluator:{case}")
        contract = inventory_case.get("assertion_contract", {})
        rows = contract.get("rows")
        need(contract.get("state") == "qualified" and contract.get("count") == 1
             and isinstance(rows, list) and len(rows) == 1,
             f"age-m3-inventory-assertion-contract:{case}")
        assertion = rows[0]
        need(assertion.get("id") == identity + "/rgb555-frame"
             and assertion.get("expected_disposition") == "pass"
             and assertion.get("observed_result") == "fail"
             and assertion.get("evaluator_status") == "xfail"
             and assertion.get("assertion_count") == 23040
             and assertion.get("mismatch_count") == mismatches
             and assertion.get("signature_sha256") == signature,
             f"age-m3-inventory-assertion:{case}")
        test_name = "cgb_age_m3_" + case.replace("-", "_")
        need(inventory_case.get("test_binding") == {"ctest_name": test_name, "state": "bound"},
             f"age-m3-inventory-test-binding:{case}")


def check_documentation(root: Path, data: dict) -> None:
    doc = (root / DOC.relative_to(ROOT)).read_text(encoding="utf-8")
    begin, end = "<!-- cgb-corpus-inventory-begin -->", "<!-- cgb-corpus-inventory-end -->"
    need(doc.count(begin) == 1 and doc.count(end) == 1, "documentation-markers")
    block = " ".join(doc.split(begin, 1)[1].split(end, 1)[0].split())
    required = (
        "gabbaboy-cgb-corpus-inventory-v1", "Mooneye", "SameSuite", "AGE", "MagenTests",
        "83", "70", "19", "9", "74", "5", "107", "109", "0", "13", "6", "8", "4,784",
        "CGB-CPU-E", "assertion", "admitted", "pending", "author", "evaluator", "rights", "ctest",
        "expected-failure", "RGB555", "current complete receipt", "observed-pass", "matched-xfail",
    )
    for token in required:
        need(token.lower() in block.lower(), f"documentation-token:{token}")
    magen_text = (root / "fixtures/magentests/ELIGIBILITY.md").read_text(encoding="utf-8")
    check_magen_claim(magen_text)


def check_magen_claim(text: str) -> None:
    need("hblank_vram_dma.gbc" in text and re.search(r"hblank_vram_dma\.gbc[\s\S]{0,500}\bis admitted\b", text, re.I) is not None,
         "magen-hblank-not-admitted")
    need(re.search(r"hblank_vram_dma[\s\S]{0,200}(?:not vendored|not admitted)", text, re.I) is None,
         "magen-hblank-stale-not-vendored")
    need("key0_lock_after_boot" in text and "source-only" in text, "magen-key0-source-only")


def check_optional_local(data: dict) -> None:
    rows = data.get("optional_local_not_run")
    need(isinstance(rows, list), "optional-local-shape")
    by_id = {r.get("id"): r for r in rows}
    need(set(by_id) == {"optional-local:cgb-acid2", "optional-local:mealybug-cgb-c"}, "optional-local-set")
    for row in by_id.values():
        need(row.get("rights_gate") == "G1" and row.get("bytes_state") == "absent", "optional-local-rights")
        need(row.get("execution_state") == "not-run:rights-gate-G1", "optional-local-execution")
        need("no outreach" in row.get("authorization", ""), "optional-local-outreach")
    mealybug = by_id["optional-local:mealybug-cgb-c"]
    need("unsupported-model" in mealybug.get("model_disposition", "")
         and "CGB-C/D" in mealybug["model_disposition"], "mealybug-model-disposition")
    need(mealybug.get("case_count") == 30, "mealybug-case-count")


def reconcile_counts(data: dict, sources: dict, outputs: dict, cases: dict) -> None:
    actual = {
        "source_candidates": len(sources),
        "output_rows": len(outputs),
        "admitted_outputs": sum(r["admission_status"] == "admitted" for r in outputs.values()),
        "pending_outputs": sum(r["admission_status"] != "admitted" for r in outputs.values()),
        "required_cases": len(cases),
    }
    counts = data.get("counts", {})
    for key, value in actual.items():
        need(counts.get(key) == value, f"declared-count:{key}")
    by_suite = counts.get("by_suite")
    need(isinstance(by_suite, dict) and set(by_suite) == set(SUITES), "declared-suite-counts")
    for suite in SUITES:
        expected = {
            "source_candidates": sum(r["suite"] == suite for r in sources.values()),
            "output_rows": sum(r["suite"] == suite for r in outputs.values()),
            "admitted_outputs": sum(r["suite"] == suite and r["admission_status"] == "admitted" for r in outputs.values()),
            "pending_outputs": sum(r["suite"] == suite and r["admission_status"] != "admitted" for r in outputs.values()),
            "required_cases": sum(r["suite"] == suite for r in cases.values()),
        }
        need(by_suite[suite] == expected, f"declared-suite-count:{suite}")
    need(data["counts"].get("assertion_rows") is None, "assertion-count-must-remain-unqualified")


def check_complete_bindings(root: Path, outputs: dict[str, dict], cases: dict[str, dict]) -> None:
    selected_outputs = {c["output_id"] for c in cases.values()}
    for oid in sorted(selected_outputs):
        output = outputs[oid]
        need(output["admission_status"] == "admitted" and re.fullmatch(r"[0-9a-f]{64}", str(output.get("sha256", ""))),
             f"bindings-required-output-pending:{oid}")
    check_test_bindings(root, cases)


def check_complete(root: Path, outputs: dict[str, dict], cases: dict[str, dict]) -> None:
    check_complete_bindings(root, outputs, cases)
    for cid, row in cases.items():
        execution = row["execution"]
        need(execution.get("state") == "completed" and execution.get("terminal") is True
             and execution.get("observed_result") in ("pass", "fail"), f"complete-case-not-terminal:{cid}")
        disposition = row["evaluator_disposition"]
        if disposition.get("state") == "expected-failure":
            need(execution["observed_result"] == "fail", f"complete-xfail-counted-as-pass:{cid}")
        assertions = row["assertion_contract"]
        rows = assertions.get("rows")
        need(isinstance(rows, list) and rows, f"complete-assertions-missing:{cid}")
        ids = [r.get("id") for r in rows]
        need(len(ids) == len(set(ids)) and all(isinstance(x, str) and x for x in ids),
             f"complete-assertions-duplicate:{cid}")
        need(assertions.get("count") == len(rows), f"complete-assertion-count:{cid}")
        for assertion in rows:
            need(isinstance(assertion.get("expected_disposition"), str) and assertion["expected_disposition"]
                 and assertion.get("observed_result") in ("pass", "fail"), f"complete-assertion-verdict:{cid}")


def check_test_bindings(root: Path, cases: dict[str, dict]) -> None:
    inventory = root / "tests/expected-tests.txt"
    need(inventory.is_file(), "bindings-expected-test-inventory-missing")
    need(inventory.stat().st_size <= MAX_INPUT_BYTES, "bindings-expected-test-inventory-size-limit")
    registered = {
        line.strip() for line in inventory.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    names = set()
    for cid, row in cases.items():
        binding = row.get("test_binding", {})
        name = binding.get("ctest_name")
        need(binding.get("state") == "bound" and isinstance(name, str)
             and re.fullmatch(r"[A-Za-z0-9_.:-]+", name), f"bindings-test-binding-pending:{cid}")
        need(name in registered, f"bindings-test-binding-not-registered:{cid}:{name}")
        need(name not in names, f"bindings-test-binding-duplicate:{name}")
        names.add(name)


def check_phase14_contract(root: Path, data: dict) -> None:
    contract_path = root / "tests/scripts/verify-age-phase14-contract.py"
    spec = importlib.util.spec_from_file_location("age_phase14_contract", contract_path)
    need(spec is not None and spec.loader is not None, "phase14-contract-import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    speed = module.read_json(root / "tests/external/cgb-speed-dispositions.json")
    module.check_age_assertions(root, data, speed)
    module.check_research14(root, data)


def check_cmake_stamp_contract(cmake: str) -> None:
    target_match = re.search(r"set\(GBB_CGB_BUILD_TARGETS\s+([^)]*)\)", cmake, re.DOTALL)
    need(target_match is not None, "ci-contract-build-stamp-target-list")
    targets = set(re.findall(r"[A-Za-z0-9_.+-]+", target_match.group(1)))
    required_targets = {
        "gabbaboy-runner", "test_age", "test_age_m3", "test_magentests",
        "test_magentests_hdma", "test_samesuite_apu", "test_samesuite_hdma",
    }
    missing = sorted(required_targets - targets)
    need(not missing, f"ci-contract-build-stamp-target-missing:{missing[0] if missing else ''}")
    need(re.search(
        r"add_dependencies\(\s*cgb_corpus_build_stamp\s+\$\{GBB_CGB_BUILD_TARGETS\}\s*\)",
        cmake), "ci-contract-build-stamp-target-order")


def check_ci_contract(root: Path, *, ci_text: str | None = None,
                      cmake_text: str | None = None) -> None:
    ci_path = root / ".github/workflows/ci.yml"
    repro_path = root / ".github/workflows/fixture-repro.yml"
    cmake_path = root / "tests/CMakeLists.txt"
    expected_path = root / "tests/expected-tests.txt"
    ci = ci_text if ci_text is not None else ci_path.read_text(encoding="utf-8")
    repro = repro_path.read_text(encoding="utf-8")
    cmake = cmake_text if cmake_text is not None else cmake_path.read_text(encoding="utf-8")
    check_cmake_stamp_contract(cmake)
    expected = {
        line.strip() for line in expected_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    required = {
        "cgb_corpus_inventory", "cgb_corpus_inventory_controls", "cgb_corpus_ci_contract",
        "cgb_corpus_report_contract", "cgb_corpus_report_controls",
        "cgb_corpus_artifact_privacy_controls", "summary_coverage",
    }
    need(required <= expected, "ci-contract-required-inventory-members")
    for name in required:
        registered = (f"add_test(NAME {name}" in cmake or
                      f"gbb_add_summary_coverage_test({name} " in cmake)
        need(registered,
             f"ci-contract-test-not-registered:{name}")
    native_start = ci.find("  native-linux:")
    native_end = ci.find("\n  native-macos:", native_start)
    native = ci[native_start:native_end if native_end >= 0 else None]
    begin = native.find("--begin-run --build-dir build")
    stream = native.find("ctest --test-dir build -T Test --no-compress-output")
    receipt = native.find("--from-ctest --build-dir build --receipt build/cgb-corpus-receipt.json")
    need(native_start >= 0 and begin >= 0, "ci-contract-begin-run")
    need(stream >= 0 and native.count("ctest --test-dir build -T Test --no-compress-output") == 1,
         "ci-contract-one-full-ctest-stream")
    need(begin < stream < receipt, "ci-contract-receipt-order")
    junit = "cgb-corpus-ctest-${{ steps.corpus_run.outputs.run_nonce }}.xml"
    need(f'--output-junit "{junit}"' in native,
         "ci-contract-junit-run-nonce")
    need("build/ctest.xml" not in native, "ci-contract-no-stale-junit-path")
    need(f'verify-test-inventory.sh "build/{junit}"' in native and
         f'--junit "build/{junit}"' in native,
         "ci-contract-junit-all-consumers-run-nonce")
    need("--test-output-size-passed 16777216" in native,
         "ci-contract-bounded-passed-test-output")
    need("build/cgb-corpus-build-stamp.json" in native,
         "ci-contract-retains-build-stamp")
    upload_start = native.find("      - name: Retain privacy-safe corpus receipt and diagnostics")
    upload_end = native.find("\n      - name: Print no-host-clock proof", upload_start)
    upload = native[upload_start:upload_end if upload_end >= 0 else None]
    path_part = upload.split("          path: |", 1)[-1].split(
        "          if-no-files-found:", 1)[0]
    upload_paths = {line.strip() for line in path_part.splitlines() if line.strip()}
    safe_upload_paths = {
        "build/cgb-corpus-receipt.json", "build/cgb-corpus-build-stamp.json",
        "build/cgb-corpus-run.json", "build/cgb-corpus-public-artifacts.json",
    }
    need(upload_start >= 0 and upload_end >= 0 and upload_paths == safe_upload_paths,
         "ci-contract-public-artifact-allowlist")
    need(".xml" not in path_part and "Test.xml" not in path_part,
         "ci-contract-no-raw-xml-artifact")
    privacy_check = native.find(
        "verify-cgb-corpus-artifacts.py --check --build-dir build")
    need(privacy_check > receipt and privacy_check < upload_start,
         "ci-contract-privacy-check-before-upload")
    sanitizer_start = ci.find("  linux-sanitizers-tests:")
    sanitizer_end = ci.find("\n  cmake-floor-", sanitizer_start)
    sanitizer = ci[sanitizer_start:sanitizer_end if sanitizer_end >= 0 else None]
    # Two complementary ASan shards each check exactly their slice of the expected inventory (LESSONS GB-CI-010).
    need(sanitizer_start >= 0 and
         "ctest --preset phase1-asan --parallel 4 -E '^acceptance_' --output-on-failure --no-tests=error --output-junit ctest.xml" in sanitizer and "ctest --preset phase1-asan --parallel 4 -R '^acceptance_' --output-on-failure --no-tests=error --output-junit ctest.xml" in sanitizer and
         sanitizer.count("verify-test-inventory.sh build-asan/ctest.xml build-asan/expected-shard.txt") == 2,
         "ci-contract-sanitizer-inventory")
    need("tests/scripts/reproduce-age.sh --compare" in repro and
         "test-reproduce-age.sh compare-tampered" in repro and
         "tests/scripts/reproduce-samesuite.sh" in repro,
         "ci-contract-age-samesuite-reproduction")
    need("tests/scripts/reproduce-mooneye-cgb.sh --compare fixtures/mooneye-cgb" in repro,
         "ci-contract-mooneye-cgb-reproduction")


def validate(root: Path, data: dict, complete: bool = False) -> tuple[dict[str, dict], dict[str, dict], dict[str, dict]]:
    need(data.get("schema") == "gabbaboy-cgb-corpus-inventory-v1" and data.get("phase") == 14, "schema")
    need(isinstance(data.get("selection_policy"), str) and data["selection_policy"], "selection-policy")
    check_tree_pins(data)
    sources, outputs, cases = check_rosters(data)
    reconcile_counts(data, sources, outputs, cases)
    check_optional_local(data)
    check_documentation(root, data)
    check_admitted_outputs(root, outputs, sources)
    check_mooneye_qualification(root, sources, outputs, cases)
    check_age_m3_qualification(root, cases)
    check_phase14_contract(root, data)
    if complete:
        check_complete(root, outputs, cases)
    return sources, outputs, cases


def self_test(root: Path, data: dict) -> None:
    validate(root, data)
    controls = []

    original_fixture_limit = MAX_FIXTURE_BYTES
    try:
        globals()["MAX_FIXTURE_BYTES"] = 1
        validate(root, data)
    except Mismatch as exc:
        need(str(exc).startswith("manifest-output-size-limit:"),
             f"self-test-wrong-diagnostic:oversized-output:{exc}")
        controls.append("oversized-output-rejected")
    else:
        raise Mismatch("self-test-control-accepted:oversized-output")
    finally:
        globals()["MAX_FIXTURE_BYTES"] = original_fixture_limit

    def rejected(name: str, mutate, expected_code: str) -> None:
        trial = copy.deepcopy(data)
        mutate(trial)
        try:
            validate(root, trial)
        except Mismatch as exc:
            need(str(exc) == expected_code, f"self-test-wrong-diagnostic:{name}:{exc}")
            controls.append(name)
            return
        raise Mismatch(f"self-test-control-accepted:{name}")

    rejected("omitted-source", lambda d: d["source_candidates"].remove(
        next(r for r in d["source_candidates"] if r["id"] == "mooneye:acceptance/timer/div_write.s")),
        "source-count:mooneye")
    rejected("duplicate-source", lambda d: d["source_candidates"].append(copy.deepcopy(d["source_candidates"][0])),
        "duplicate-source-id")
    rejected("wrong-unsuffixed-header", lambda d: next(r for r in d["source_candidates"]
        if r["id"] == "mooneye:acceptance/timer/div_write.s")["applicability"].update({"header_quote": "; pass: CGB-E only"}),
        "mooneye-header-div_write")
    rejected("filtered-unsuffixed", lambda d: next(r for r in d["source_candidates"]
        if r["id"] == "mooneye:acceptance/timer/div_write.s")["selection"].update({"state": "excluded"}),
        "mooneye-unsuffixed-div_write-filtered")
    rejected("substituted-case", lambda d: d["cases"].remove(
        next(r for r in d["cases"] if r["id"] == "mooneye:acceptance/timer/tim00.s")),
        "required-case-count:mooneye")
    rejected("empty-denominator", lambda d: d.update({"cases": []}), "required-case-count:age")
    rejected("source-only-execution", lambda d: (
        next(r for r in d["outputs"] if r["id"] == "age:spsw-div-cgbBCE").update({"admission_status": "source-only"}),
        next(r for r in d["cases"] if r["id"] == "age:spsw-div-cgbBCE")["execution"].update(
            {"state": "completed", "observed_result": "pass", "terminal": True})),
        "source-only-output-execution")
    rejected("missing-family", lambda d: d["source_candidates"][0].update({"family": ""}), "source-family")
    rejected("changed-pin", lambda d: next(r for r in d["source_candidates"]
        if r["suite"] == "age").update({"source_commit": "0000000000000000000000000000000000000000"}),
        "source-row-pin:age")
    rejected("unknown-source", lambda d: next(r for r in d["source_candidates"]
        if r["id"] == "mooneye:acceptance/add_sp_e_timing.s").update({
            "id": "mooneye:acceptance/unknown.s", "source_path": "acceptance/unknown.s"}),
        "source-candidate-fingerprint:mooneye")
    rejected("wrong-samesuite-readme", lambda d: next(r for r in d["source_candidates"]
        if r["suite"] == "samesuite" and r["source_path"].startswith("apu/"))["applicability"].update(
            {"readme_quote": "CPU-CGB-E is unqualified"}),
        "samesuite-readme-applicability")
    rejected("mooneye-wrong-model", lambda d: next(r for r in d["cases"]
        if r["id"] == "mooneye:misc/ppu/vblank_stat_intr-C.s").update({"model": "CGB-CPU-D"}),
        "case-model-mode-speed")
    rejected("mooneye-wrong-mode", lambda d: next(r for r in d["cases"]
        if r["id"] == "mooneye:misc/ppu/vblank_stat_intr-C.s").update({"mode": "native"}),
        "required-case-fingerprint:mooneye")
    rejected("mooneye-changed-failure-callback", lambda d: next(r for r in d["cases"]
        if r["id"] == "mooneye:misc/ppu/vblank_stat_intr-C.s")["execution"].update(
            {"callback_pc": "0x4001"}), "mooneye-assertion-callback:vblank_stat_intr-C")
    rejected("mooneye-xfail-counted-as-pass", lambda d: next(r for r in d["cases"]
        if r["id"] == "mooneye:misc/ppu/vblank_stat_intr-C.s")["execution"].update(
            {"observed_result": "pass"}), "mooneye-execution-verdict:vblank_stat_intr-C")

    trial = copy.deepcopy(data)
    trial_case = next(r for r in trial["cases"] if r["suite"] == "age")
    trial_case["hardware_qualified"] = True
    try:
        validate(root, trial)
    except Mismatch as exc:
        need(str(exc) == "hardware-claim-forbidden", f"self-test-wrong-diagnostic:false-hardware:{exc}")
        controls.append("false-hardware-claim")
    else:
        raise Mismatch("self-test-control-accepted:false-hardware-claim")

    magen_text = (root / "fixtures/magentests/ELIGIBILITY.md").read_text(encoding="utf-8")
    stale = magen_text + "\nThe HBlank fixture hblank_vram_dma is not vendored.\n"
    try:
        check_magen_claim(stale)
    except Mismatch as exc:
        need(str(exc) == "magen-hblank-stale-not-vendored", f"self-test-wrong-diagnostic:magen:{exc}")
        controls.append("stale-magen-admission")
    else:
        raise Mismatch("self-test-control-accepted:stale-magen-admission")

    trial = copy.deepcopy(data)
    next(r for r in trial["optional_local_not_run"] if r["suite"] == "mealybug")["rights_gate"] = None
    try:
        validate(root, trial)
    except Mismatch as exc:
        need(str(exc) == "optional-local-rights", f"self-test-wrong-diagnostic:optional-rights:{exc}")
        controls.append("optional-rights-and-model")
    else:
        raise Mismatch("self-test-control-accepted:optional-rights")

    try:
        trial = copy.deepcopy(data)
        next(r for r in trial["cases"] if r["id"] == "magentests:bg_oam_priority")["test_binding"] = {
            "ctest_name": None, "state": "pending-registration"
        }
        _, _, case_map = validate(root, trial)
        check_test_bindings(root, case_map)
    except Mismatch as exc:
        need(str(exc).startswith("bindings-test-binding-pending:"), f"self-test-wrong-diagnostic:test-binding:{exc}")
        controls.append("bindings-require-ctest-bindings")
    else:
        raise Mismatch("self-test-control-accepted:missing-test-binding")

    _, _, case_map = validate(root, data)
    original_input_limit = MAX_INPUT_BYTES
    try:
        globals()["MAX_INPUT_BYTES"] = 0
        check_test_bindings(root, case_map)
    except Mismatch as exc:
        need(str(exc) == "bindings-expected-test-inventory-size-limit",
             f"self-test-wrong-diagnostic:oversized-test-inventory:{exc}")
        controls.append("oversized-test-inventory-rejected")
    else:
        raise Mismatch("self-test-control-accepted:oversized-test-inventory")
    finally:
        globals()["MAX_INPUT_BYTES"] = original_input_limit

    try:
        _, outputs, cases = validate(root, data)
        check_complete(root, outputs, cases)
    except Mismatch as exc:
        need(str(exc) == "complete-case-not-terminal:magentests:bg_oam_priority",
             f"self-test-wrong-diagnostic:complete:{exc}")
        controls.append("complete-rejects-static-not-run-magentests-case")
    else:
        raise Mismatch("self-test-control-accepted:incomplete-complete-mode")

    check_ci_contract(root)
    ci_text = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    stale_junit = f'--junit "build/cgb-corpus-ctest-${{{{ steps.corpus_run.outputs.run_nonce }}}}.xml"'
    mutated_ci = ci_text.replace(stale_junit,
                                 "--junit build/ctest.xml", 1)
    need(mutated_ci != ci_text, "self-test-ci-mutant-anchor:junit")
    try:
        check_ci_contract(root, ci_text=mutated_ci)
    except Mismatch as exc:
        need(str(exc) == "ci-contract-no-stale-junit-path",
             f"self-test-wrong-diagnostic:stale-junit:{exc}")
        controls.append("ci-rejects-stale-junit-consumer")
    else:
        raise Mismatch("self-test-control-accepted:stale-junit-consumer")

    mutated_ci = ci_text.replace("build/cgb-corpus-public-artifacts.json",
                                 "build/Testing/*/Test.xml", 1)
    need(mutated_ci != ci_text, "self-test-ci-mutant-anchor:artifact")
    try:
        check_ci_contract(root, ci_text=mutated_ci)
    except Mismatch as exc:
        need(str(exc) == "ci-contract-public-artifact-allowlist",
             f"self-test-wrong-diagnostic:raw-artifact:{exc}")
        controls.append("ci-rejects-raw-xml-artifact")
    else:
        raise Mismatch("self-test-control-accepted:raw-xml-artifact")

    cmake_text = (root / "tests/CMakeLists.txt").read_text(encoding="utf-8")
    target_match = re.search(r"set\(GBB_CGB_BUILD_TARGETS\s+([^)]*)\)",
                             cmake_text, re.DOTALL)
    need(target_match is not None, "self-test-cmake-mutant-anchor:stamp-target")
    target_block = target_match.group(0)
    mutated_block = target_block.replace("test_age_m3", "", 1)
    need(mutated_block != target_block, "self-test-cmake-mutant-anchor:hashed-target")
    mutated_cmake = cmake_text.replace(target_block, mutated_block, 1)
    try:
        check_cmake_stamp_contract(mutated_cmake)
    except Mismatch as exc:
        need(str(exc) == "ci-contract-build-stamp-target-missing:test_age_m3",
             f"self-test-wrong-diagnostic:missing-build-target:{exc}")
        controls.append("build-stamp-rejects-missing-hashed-target")
    else:
        raise Mismatch("self-test-control-accepted:missing-build-target")
    print("cgb-corpus-inventory self-test pass controls=" + ",".join(controls))


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--selection-only", action="store_true")
    group.add_argument("--bindings", action="store_true")
    group.add_argument("--complete", action="store_true")
    group.add_argument("--ci-contract", action="store_true")
    group.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        data = bounded_json(INVENTORY)
        if args.self_test:
            self_test(ROOT, data)
        elif args.ci_contract:
            sources, outputs, cases = validate(ROOT, data)
            check_complete_bindings(ROOT, outputs, cases)
            check_ci_contract(ROOT)
            print("cgb-corpus-inventory ci-contract pass cases=107 workflow=native-sanitizer-repro")
        else:
            sources, outputs, cases = validate(ROOT, data, complete=args.complete)
            if args.bindings:
                check_complete_bindings(ROOT, outputs, cases)
            mode = "complete" if args.complete else "bindings" if args.bindings else "selection-only"
            print(
                "cgb-corpus-inventory pass mode={} sources={} outputs={} admitted={} pending={} cases={} assertions=pending".format(
                    mode,
                    len(sources), len(outputs),
                    sum(r["admission_status"] == "admitted" for r in outputs.values()),
                    sum(r["admission_status"] != "admitted" for r in outputs.values()),
                    len(cases),
                )
            )
    except (Mismatch, KeyError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"cgb-corpus-inventory mismatch: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
