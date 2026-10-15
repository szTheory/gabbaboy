#!/usr/bin/env python3
"""Validate the CGB speed-switch evidence ledger and its checked-in mirror."""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

AGE_ROW_CASES = {
    "spsw-div-cgbBCE", "spsw-tima-cgbE", "spsw-tima-cgbBC", "spsw-stop-prefetch-cgbBCE",
    "spsw-interrupts-cgbE", "spsw-mode0-cgbBCE", "spsw-ch2-lc-delay-cgbBCE",
    "stat-mode-ds-cgbBCE", "stat-mode-cgbE", "stat-mode-sprites-ds-cgbBCE",
    "stat-mode-sprites-dmgC-cgbBCE", "stat-mode-window-ds-cgbBCE", "stat-mode-window-cgbBCE",
}
AGE_IMAGE_CASES = {
    f"m3-bg-{axis}-{variant}"
    for axis in ("lcdc", "scx")
    for variant in ("cgbBCE", "ds-cgbBCE", "nocgb-ncmBCE")
}
AGE_DIGEST_ONLY_CASE = "spsw-interrupts-cgbBC"
ROW_METADATA = {"test_results_address", "expected_address", "rows", "budget_half_dots"}
IMAGE_OUTCOMES = {"disposition", "execution_result", "pixel_result", "emulator_result", "actual_result"}


class Mismatch(Exception):
    pass


def need(condition: bool, detail: str) -> None:
    if not condition:
        raise Mismatch(detail)


def suite_map(data: dict) -> dict[str, dict]:
    result = {}
    for suite in data.get("suites", []):
        name = suite.get("suite", "")
        need(bool(name) and name not in result, f"suite {name!r}")
        result[name] = suite
    return result


def mirror_rows(document: str) -> list[tuple[str, ...]]:
    begin = "<!-- cgb-speed-dispositions-begin -->"
    end = "<!-- cgb-speed-dispositions-end -->"
    need(document.count(begin) == 1 and document.count(end) == 1,
         "docs-mirror-markers")
    block = document.split(begin, 1)[1].split(end, 1)[0]
    rows = []
    for line in block.splitlines():
        if not line.startswith("|") or line.startswith("|---") or line.startswith("|-------"):
            continue
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        if cells and cells[0] != "suite":
            need(len(cells) == 6, "docs-mirror-columns")
            rows.append(cells)
    return rows


def admitted_age_row_fixtures(root: pathlib.Path) -> dict[str, dict]:
    manifest = json.loads((root / "fixtures/age/manifest.json").read_text(encoding="utf-8"))
    need(manifest.get("fixture_protocol") == "gabbaboy-age-fixture-protocol-v1",
         "age-fixture-protocol")
    fixtures = manifest.get("fixtures", [])
    files = [fixture.get("file", "") for fixture in fixtures]
    need(len(fixtures) == 19 and len(files) == len(set(files)), "age-fixture-count")
    need(all(fixture.get("fixture_class") in {"age-row-oracle", "age-m3-reference"}
             for fixture in fixtures), "age-fixture-class")
    row_fixtures = [fixture for fixture in fixtures
                    if fixture.get("fixture_class") == "age-row-oracle"]
    image_fixtures = [fixture for fixture in fixtures
                      if fixture.get("fixture_class") == "age-m3-reference"]
    rows = {fixture.get("file", "").removesuffix(".gb"): fixture for fixture in row_fixtures}
    images = {fixture.get("file", "").removesuffix(".gb"): fixture for fixture in image_fixtures}
    need(len(rows) == 13 and set(rows) == AGE_ROW_CASES, "age-row-fixture-set")
    need(len(images) == 6 and set(images) == AGE_IMAGE_CASES, "age-image-fixture-set")
    for case, fixture in rows.items():
        need(ROW_METADATA <= set(fixture) and fixture.get("file") == f"{case}.gb",
             f"age-row-metadata {case}")
        need("qualification_status" not in fixture and not IMAGE_OUTCOMES.intersection(fixture),
             f"age-row-image-status {case}")
    for case, fixture in images.items():
        need(fixture.get("qualification_status") == "admitted-not-executed",
             f"age-image-pending {case}")
        need(not ROW_METADATA.intersection(fixture) and not IMAGE_OUTCOMES.intersection(fixture),
             f"age-image-row-or-outcome {case}")
        reference = fixture.get("reference", {})
        need(reference.get("file") == f"references/{case}.png",
             f"age-image-reference-pair {case}")
    return rows


def main() -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=pathlib.Path,
                        default=root / "tests/external/cgb-speed-dispositions.json")
    args = parser.parse_args()
    try:
        data = json.loads(args.record.read_text(encoding="utf-8"))
        need(data.get("schema") == "gabbaboy-external-dispositions-v1", "schema")
        suites = suite_map(data)
        need({"age-test-roms", "gabbaboy-model", "samesuite", "gambatte",
              "not-applicable"} <= set(suites), "suite-set")
        rows = [(suite["suite"], row)
                for suite in data.get("suites", []) for row in suite.get("rows", [])]
        need(bool(rows), "rows-empty")
        for suite in data["suites"]:
            if suite.get("vendored") is True:
                need(re.fullmatch(r"[0-9a-f]{40}", suite.get("commit", "")) is not None,
                     f"commit {suite.get('suite', '')}")

        admitted = admitted_age_row_fixtures(root)
        age_rows = suites["age-test-roms"].get("rows", [])
        age_case_names = [row.get("case") for row in age_rows]
        need(len(age_rows) == 14 and len(age_case_names) == len(set(age_case_names)) and
             set(age_case_names) == AGE_ROW_CASES | {AGE_DIGEST_ONLY_CASE}, "age-case-set")
        vendored_age_rows = [row for row in age_rows if row.get("vendored") is not False]
        vendored_age = {row.get("case"): row for row in vendored_age_rows}
        need(len(vendored_age_rows) == 13 and len(vendored_age) == 13 and
             set(vendored_age) == AGE_ROW_CASES and
             set(vendored_age) == set(admitted), "age-case-set")
        for case, fixture in admitted.items():
            need(vendored_age[case].get("upstream_path") == fixture.get("source_path"),
                 f"age-upstream-path {case}")
        digest_only = [row for row in age_rows if row.get("disposition") == "digest-only"]
        need(len(digest_only) == 1 and digest_only[0].get("case") == AGE_DIGEST_ONLY_CASE and
             digest_only[0].get("vendored") is False and
             re.fullmatch(r"[0-9a-f]{64}", digest_only[0].get("source_sha256", "")) is not None,
             "age-digest-only")
        sensitivity = suites["age-test-roms"].get("sensitivity", {})
        mutants = {row.get("mutant"): row for row in sensitivity.get("mutants", [])}
        need(set(mutants) == {"M6", "M21", "M28", "M27"} and
             sensitivity.get("fixture_count") == len(AGE_ROW_CASES) and
             re.fullmatch(r"[0-9a-f]{40}", sensitivity.get("source_revision", "")) is not None,
             "age-sensitivity-shape")
        for mutant, row in mutants.items():
            cases = row.get("discriminating_cases", [])
            need(len(cases) == len(set(cases)) and set(cases) <= AGE_ROW_CASES,
                 f"age-sensitivity-cases {mutant}")
        need({"spsw-div-cgbBCE"} <= set(mutants["M6"].get("discriminating_cases", [])) and
             {"spsw-div-cgbBCE"} <= set(mutants["M21"].get("discriminating_cases", [])) and
             {"spsw-div-cgbBCE"} <= set(mutants["M27"].get("discriminating_cases", [])),
             "age-sensitivity-div-required")
        need("spsw-div-cgbBCE" not in mutants["M28"].get("discriminating_cases", []) and
             "spsw-mode0-cgbBCE" in mutants["M28"].get("discriminating_cases", []) and
             "low-bit stall window remains unchanged" in mutants["M28"].get("note", ""),
             "age-sensitivity-m28-evidence")

        inventory = set()
        for rel in ("tests/expected-tests.txt", "tests/player/expected-tests.txt"):
            path = root / rel
            if path.exists():
                inventory.update(path.read_text(encoding="utf-8").split())
        for _, row in rows:
            case = row.get("case", "")
            pin = row.get("pinned_by", "")
            if row.get("disposition") == "expected-failure":
                need(bool(pin), f"pinned_by {case} missing")
            if pin:
                need(pin in inventory, f"pinned_by {case} {pin}")
            signature = row.get("signature_sha256", "")
            if signature:
                need(re.fullmatch(r"[0-9a-f]{64}", signature) is not None,
                     f"signature {case}")
            if row.get("reason"):
                need(row.get("flip_rule"), f"flip_rule {case}")

        document = (root / "docs/cgb-profile.md").read_text(encoding="utf-8")
        mirror = mirror_rows(document)
        expected_mirror = []
        reasons = set()
        for suite, row in rows:
            reason = row.get("reason", "-")
            reasons.add(reason)
            expected_mirror.append((suite, row.get("case", ""), row.get("disposition", ""),
                                    reason, str(row.get("owner_phase", "-")),
                                    row.get("pinned_by", "-") or "-"))
        need(len(mirror) == len(set(mirror)) and set(mirror) == set(expected_mirror),
             "docs-mirror-rows")
        mirrored_reasons = {row[3] for row in mirror}
        need(reasons <= mirrored_reasons, "docs-mirror-reasons")

        phase12_profile = document.split("### STOP with KEY1 armed", 1)[1].split(
            "### IE bits 5-7", 1)[0]
        expected_names = set(re.findall(r"expected-failure:([a-z0-9-]+)", phase12_profile))
        expected_names.add("cgb-dma-restart-oracle-only")
        expected_names.discard("reason")
        row_names = {row.get("reason", "").removeprefix("expected-failure:")
                     for suite, row in rows if row.get("disposition") == "expected-failure"}
        need(expected_names <= row_names, f"expected-failure-docs {sorted(expected_names - row_names)}")

        gates = (root / "docs/model-gates.md").read_text(encoding="utf-8")
        gate_names = set(re.findall(r"expected-failure:([a-z0-9-]+)", gates))
        gate_names.discard("reason")
        need(gate_names <= row_names, f"expected-failure-model-gates {sorted(gate_names - row_names)}")

        same = suites["samesuite"]
        need(same.get("vendored") is False and len(same.get("rows", [])) == 1 and
             same["rows"][0].get("disposition") == "expected-unsupported" and
             same["rows"][0].get("reason") == "pcm-registers-unbuilt" and
             sum(row.get("reason") == "pcm-registers-unbuilt" for _, row in rows) == 1,
             "samesuite-aggregate")
        gambatte = suites["gambatte"]
        need(gambatte.get("vendored") is False and gambatte.get("license") == "GPL-2.0" and
             len(gambatte.get("rows", [])) == 1 and
             gambatte["rows"][0].get("disposition") == "not-admitted", "gambatte-not-admitted")
        not_applicable = {row.get("case") for row in suites["not-applicable"].get("rows", [])
                          if row.get("disposition") == "not-applicable"}
        need(not_applicable == {"mooneye", "blargg", "acid2"}, "not-applicable-suites")
    except (Mismatch, KeyError, ValueError, OSError, IndexError) as exc:
        print(f"disposition-mismatch {exc}")
        return 1
    print(f"cgb-speed-dispositions pass rows={len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
