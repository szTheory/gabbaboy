#!/usr/bin/env python3
"""Fail-closed validation for the pinned Phase 14 CGB corpus selection."""
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
DOC = ROOT / "docs/cgb-corpus.md"
MAGEN_DOC = ROOT / "fixtures/magentests/ELIGIBILITY.md"
MAX_INPUT_BYTES = 2_000_000
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
    "samesuite": "6ac51e6c186b004c8928f942dc8e6552ee0c1e60fcb943fbdc64581cf1bb0ef0",
    "magentests": "3124e9d8044be19eaa3e516645586a20680fa054332b61f59800aa85b7e963d6",
    "mooneye": "ad7e61d4aac679d68f6733f967f85d1eef45644779c39b37191d35026acfb326",
}
OUTPUT_DIGESTS = {
    "age": "18f8a8cc28b1674d1ad7186b0cad0ed6960dddc18624229063039933f42c1e09",
    "samesuite": "711855f181c1e2a61e511691455178ab0ea2f42064ce00911db4148f0f88db3f",
    "magentests": "928c0ce4fcb770aa48d1959ee92c9fba480f548d42d8a79721942d3525f2119c",
    "mooneye": "af6927aab0463e1041551182817ba6c7a651ae3afe791314c186164805e818a5",
}
CASE_DIGESTS = {
    "age": "7bfeeb4af1ad26e59ac9e61a2f38cadb2a20667acf49589ccf38c68093217dfa",
    "samesuite": "9cf6c0325706d4831eabb6d6d72a515474bd6b921c771bb98ff19fed5ad334c1",
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
        need(output is not None and output.get("admission_status") != "source-only", "case-output-reference")
        need(output["source_id"] == source["id"] and output["suite"] == suite, "case-source-output-mismatch")
        need(row.get("model") == "CGB-CPU-E" and row.get("mode") in ("native", "compat")
             and row.get("speed") in ("normal", "double"), "case-model-mode-speed")
        need(isinstance(row.get("author_expectation"), dict) and row["author_expectation"].get("class"),
             "case-author-expectation")
        need(isinstance(row.get("evaluator_disposition"), dict) and row["evaluator_disposition"].get("state"),
             "case-evaluator-disposition")
        need(isinstance(row.get("execution"), dict), "case-execution")
        need(isinstance(row.get("assertion_contract"), dict), "case-assertion-contract")
        need(not row.get("hardware_qualified", False), "hardware-claim-forbidden")
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
        name = PurePosixPath(row["output_path"]).name
        fixture = manifests[suite].get(name)
        need(fixture is not None, f"manifest-output-missing:{row['id']}")
        source_path = sources[row["source_id"]]["source_path"]
        manifest_source = fixture.get("source_path")
        if suite == "magentests":
            manifest_source = f"{fixture.get('source_dir')}/main.asm"
        need(manifest_source == source_path, f"manifest-source-mismatch:{row['id']}")
        need(row.get("manifest_ref") == expected_manifest[suite], f"manifest-reference:{row['id']}")
        need(row.get("sha256") == fixture.get("sha256") and row.get("size_bytes") == fixture.get("size_bytes"),
             f"manifest-digest-mismatch:{row['id']}")
        need(row["output_path"] in tracked_set, f"admitted-output-untracked:{row['id']}")
        file_path = root / row["output_path"]
        need(file_path.is_file(), f"admitted-output-missing:{row['id']}")
        content = file_path.read_bytes()
        need(len(content) == fixture["size_bytes"], f"admitted-output-size:{row['id']}")
        need(hashlib.sha256(content).hexdigest() == fixture["sha256"], f"admitted-output-hash:{row['id']}")


def check_documentation(root: Path, data: dict) -> None:
    doc = (root / DOC.relative_to(ROOT)).read_text(encoding="utf-8")
    begin, end = "<!-- cgb-corpus-inventory-begin -->", "<!-- cgb-corpus-inventory-end -->"
    need(doc.count(begin) == 1 and doc.count(end) == 1, "documentation-markers")
    block = doc.split(begin, 1)[1].split(end, 1)[0]
    required = (
        "gabbaboy-cgb-corpus-inventory-v1", "Mooneye", "SameSuite", "AGE", "MagenTests",
        "83", "70", "19", "9", "74", "5", "107", "81", "CGB-CPU-E",
        "assertion", "admitted", "pending", "author", "evaluator", "rights",
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


def check_complete(outputs: dict[str, dict], cases: dict[str, dict]) -> None:
    selected_outputs = {c["output_id"] for c in cases.values()}
    for oid in sorted(selected_outputs):
        output = outputs[oid]
        need(output["admission_status"] == "admitted" and re.fullmatch(r"[0-9a-f]{64}", str(output.get("sha256", ""))),
             f"complete-required-output-pending:{oid}")
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


def validate(root: Path, data: dict, complete: bool = False) -> tuple[dict[str, dict], dict[str, dict], dict[str, dict]]:
    need(data.get("schema") == "gabbaboy-cgb-corpus-inventory-v1" and data.get("phase") == 14, "schema")
    need(isinstance(data.get("selection_policy"), str) and data["selection_policy"], "selection-policy")
    check_tree_pins(data)
    sources, outputs, cases = check_rosters(data)
    reconcile_counts(data, sources, outputs, cases)
    check_optional_local(data)
    check_documentation(root, data)
    check_admitted_outputs(root, outputs, sources)
    if complete:
        check_complete(outputs, cases)
    return sources, outputs, cases


def self_test(root: Path, data: dict) -> None:
    validate(root, data)
    controls = []

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
    rejected("source-only-execution", lambda d: next(r for r in d["cases"]
        if r["id"] == "mooneye:acceptance/timer/div_write.s").__setitem__("output_id", "missing-output"),
        "case-output-reference")

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
        _, outputs, cases = validate(root, data)
        check_complete(outputs, cases)
    except Mismatch as exc:
        need(str(exc).startswith("complete-required-output-pending:"), f"self-test-wrong-diagnostic:complete:{exc}")
        controls.append("complete-rejects-unadmitted-required-bytes")
    else:
        raise Mismatch("self-test-control-accepted:incomplete-complete-mode")
    print("cgb-corpus-inventory self-test pass controls=" + ",".join(controls))


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--selection-only", action="store_true")
    group.add_argument("--complete", action="store_true")
    group.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        data = bounded_json(INVENTORY)
        if args.self_test:
            self_test(ROOT, data)
        else:
            sources, outputs, cases = validate(ROOT, data, complete=args.complete)
            print(
                "cgb-corpus-inventory pass mode={} sources={} outputs={} admitted={} pending={} cases={} assertions=pending".format(
                    "complete" if args.complete else "selection-only",
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
