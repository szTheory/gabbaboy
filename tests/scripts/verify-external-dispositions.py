#!/usr/bin/env python3
"""Offline check of the external CGB PPU suite dispositions (D-09, D-20; threat T-11-39).

Standard library only; run as `python3 -I`. Reads the committed JSON record and the docs mirror
block, and lists tracked files with git. It never reads ROM bytes and never uses the network.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

AGE_CASES = {f"m3-bg-{a}-{b}" for a in ("lcdc", "scx") for b in ("cgbBCE", "ds-cgbBCE", "nocgb-ncmBCE")}
AGE_ROW_CASES = {
    "spsw-div-cgbBCE", "spsw-tima-cgbE", "spsw-tima-cgbBC", "spsw-stop-prefetch-cgbBCE",
    "spsw-interrupts-cgbE", "spsw-mode0-cgbBCE", "spsw-ch2-lc-delay-cgbBCE",
    "stat-mode-ds-cgbBCE", "stat-mode-cgbE", "stat-mode-sprites-ds-cgbBCE",
    "stat-mode-sprites-dmgC-cgbBCE", "stat-mode-window-ds-cgbBCE", "stat-mode-window-cgbBCE",
}
ROW_METADATA = {"test_results_address", "expected_address", "rows", "budget_half_dots"}
AGE_COMMIT = "1f5bc10e2cb60b86c19f8d0287ff78f410c4f639"
AGE_XFAIL_REASON = "expected-failure:cgb-e-mode3-reference-mismatch"
BEGIN = "<!-- cgb-external-dispositions-begin -->"
END = "<!-- cgb-external-dispositions-end -->"


class Mismatch(Exception):
    pass


def need(condition: bool, detail: str) -> None:
    if not condition:
        raise Mismatch(detail)


def load_suites(record: pathlib.Path) -> dict:
    data = json.loads(record.read_text(encoding="utf-8"))
    need(data.get("schema") == "gabbaboy-external-dispositions-v1", "schema")
    need("D-20" in data.get("note_d20", ""), "note_d20-missing")
    suites = {s.get("suite"): s for s in data.get("suites", [])}
    need(set(suites) == {"age", "mealybug"}, "suite-set")
    for name, suite in suites.items():
        need(suite.get("vendored") is False, f"{name}-vendored")
        need(re.fullmatch(r"[0-9a-f]{40}", suite.get("commit", "")) is not None, f"{name}-commit")
    return suites


def check_rows(suites: dict) -> list[tuple[str, str, str, str]]:
    age = suites["age"]
    rows = age["rows"]
    cases = [r["case"] for r in rows]
    need(len(cases) == len(set(cases)) and set(cases) == AGE_CASES and age["upstream_count"] == 6,
         "age-case-set")
    for r in rows:
        need(r["disposition"] == "expected-failure", f"age-disposition {r['case']}")
        need(r["reason"] == AGE_XFAIL_REASON, f"age-reason {r['case']}")
        need(r["decision"] == "D-09" and r["owner_phase"] == 14, f"age-decision {r['case']}")
        need(r.get("observed_result") == "fail" and r.get("evaluator_status") == "xfail",
             f"age-observed-result {r['case']}")
        need(r.get("expected_role") == "pass-target" and r.get("model") == "CGB-E",
             f"age-author-target-or-model {r['case']}")
        need(r.get("promotion_rule", "").startswith("Promote only after this same pinned CGB-E model"),
             f"age-promotion-rule {r['case']}")
    mb = suites["mealybug"]
    need(mb.get("rights_gate") == "G1", "mealybug-rights-gate")
    mrows = mb["rows"]
    need(len(mrows) == mb["upstream_count"] and len(mrows) > 0, "mealybug-count")
    need(len({r["case"] for r in mrows}) == len(mrows), "mealybug-duplicate")
    for r in mrows:
        need(re.match(r"^m3_", r["case"]) is not None, f"mealybug-case {r['case']}")
        need(r["disposition"] == "unsupported-model", f"mealybug-disposition {r['case']}")
        need("CGB-C/D" in r["reason"] and "no CGB-E expectation" in r["reason"],
             f"mealybug-reason {r['case']}")
        need(r["decision"] == "D-09", f"mealybug-decision {r['case']}")
    return [(s, r["case"], r["disposition"], r["reason"])
            for s in ("age", "mealybug") for r in suites[s]["rows"]]


def executed_age_image_paths(repo_root: pathlib.Path, manifest_path: pathlib.Path | None = None) -> set[str]:
    path = manifest_path or repo_root / "fixtures/age/manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    need(manifest.get("fixture_protocol") == "gabbaboy-age-fixture-protocol-v1",
         "age-fixture-protocol")
    entries = manifest.get("fixtures", [])
    need(len(entries) == 19, "age-fixture-count")
    files = [e.get("file", "") for e in entries]
    need(len(files) == len(set(files)), "age-fixture-duplicate")
    row_entries = [e for e in entries if e.get("fixture_class") == "age-row-oracle"]
    image_entries = [e for e in entries if e.get("fixture_class") == "age-m3-reference"]
    need(all(e.get("fixture_class") in {"age-row-oracle", "age-m3-reference"} for e in entries),
         "age-fixture-class")
    need({e.get("file", "").removesuffix(".gb") for e in row_entries} == AGE_ROW_CASES and
         len(row_entries) == 13, "age-row-fixture-set")
    image_cases = {e.get("file", "").removesuffix(".gb") for e in image_entries}
    need(image_cases == AGE_CASES and len(image_entries) == 6, "age-image-fixture-set")

    paths = set()
    age_rows = {row["case"]: row for row in load_suites(repo_root / "tests/external/cgb-ppu-dispositions.json")["age"]["rows"]}
    for entry in image_entries:
        name = entry.get("file", "")
        case = name.removesuffix(".gb")
        row = age_rows[case]
        need(entry.get("qualification_status") == "executed", f"age-image-not-executed {name}")
        need(not ROW_METADATA.intersection(entry), f"age-image-row-metadata {name}")
        need(entry.get("expected_role") == "pass-target" and entry.get("execution_result") == "fail"
             and entry.get("disposition") == "expected-failure" and entry.get("reason") == AGE_XFAIL_REASON,
             f"age-image-execution-outcome {name}")
        reference = entry.get("reference", {})
        expected_reference = f"references/{name.removesuffix('.gb')}.png"
        need(reference.get("file") == expected_reference,
             f"age-image-reference-pair {name}")
        identity = "/".join((
            f"age@{AGE_COMMIT}",
            f"{entry['source_path']}#{entry['source_sha256']}",
            f"{name}#{entry['sha256']}",
            entry["model"], entry["mode"], entry["speed"], case,
        ))
        need(entry.get("case_id") == identity and row.get("case_id") == identity,
             f"age-image-case-identity-mismatch {case}")
        need(row.get("reason") == entry.get("reason") and row.get("disposition") == entry.get("disposition"),
             f"age-image-disposition-mismatch {case}")
        need(row.get("mode") == entry.get("mode") and row.get("speed") == entry.get("speed")
             and row.get("pinned_by") == "cgb_age_m3_" + case.replace("-", "_"),
             f"age-image-execution-identity-mismatch {case}")
        count = entry.get("pixel_assertion_count")
        mismatch_count = entry.get("pixel_mismatch_count")
        signature = entry.get("pixel_mismatch_signature_sha256", "")
        need(count == 23040 and isinstance(mismatch_count, int) and 0 < mismatch_count <= count
             and re.fullmatch(r"[0-9a-f]{64}", signature) is not None,
             f"age-image-signature-invalid {case}")
        need(row.get("pixel_assertion_count") == count and row.get("pixel_mismatch_count") == mismatch_count
             and row.get("pixel_mismatch_signature_sha256") == signature
             and row.get("source_sha256") == entry.get("source_sha256")
             and row.get("rom_sha256") == entry.get("sha256")
             and row.get("reference_sha256") == reference.get("sha256"),
             f"age-image-signature-mismatch {case}")
        paths.add(f"fixtures/age/{name}")
        paths.add(f"fixtures/age/{expected_reference}")
    return paths


def check_tracked(repo_root: pathlib.Path, suites: dict,
                  manifest_path: pathlib.Path | None = None) -> None:
    out = subprocess.run(["git", "-C", str(repo_root), "ls-files", "-z", "--", "fixtures"],
                         check=True, capture_output=True).stdout.decode("utf-8", "replace")
    allowed_age_images = executed_age_image_paths(repo_root, manifest_path)
    stems = [r["case"] for r in suites["mealybug"]["rows"]]
    tracked_age_images = set()
    for path in filter(None, out.split("\0")):
        name = path.rsplit("/", 1)[-1]
        if not name.lower().endswith((".gb", ".gbc", ".png")):
            continue
        if "m3-bg-" in name:
            need(path in allowed_age_images, f"tracked-age-file {path}")
            tracked_age_images.add(path)
        need(not any(name.startswith(stem) for stem in stems), f"tracked-mealybug-file {path}")
    need(tracked_age_images == allowed_age_images,
         f"tracked-age-file-set missing={sorted(allowed_age_images - tracked_age_images)}")


def doc_rows(doc: pathlib.Path) -> list[tuple[str, str, str, str]]:
    text = doc.read_text(encoding="utf-8")
    need(text.count(BEGIN) == 1 and text.count(END) == 1, "doc-markers")
    block = text.split(BEGIN, 1)[1].split(END, 1)[0]
    rows = []
    for line in block.strip().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[0] in ("suite",) or set(cells[0]) <= {"-", " "}:
            continue
        need(len(cells) == 4, f"doc-row-shape {line[:40]}")
        rows.append(tuple(cells))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", required=True, type=pathlib.Path)
    ap.add_argument("--doc", required=True, type=pathlib.Path)
    ap.add_argument("--repo-root", required=True, type=pathlib.Path)
    ap.add_argument("--age-manifest", type=pathlib.Path)
    args = ap.parse_args()
    try:
        suites = load_suites(args.record)
        expected = check_rows(suites)
        need(doc_rows(args.doc) == expected, "doc-mirror-differs")
        check_tracked(args.repo_root.resolve(), suites, args.age_manifest)
    except (Mismatch, KeyError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"disposition-mismatch {type(exc).__name__ if not isinstance(exc, Mismatch) else ''}{exc}")
        return 1
    print(f"external-dispositions pass age=6 mealybug={len(suites['mealybug']['rows'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
