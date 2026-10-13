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
        need(r["disposition"] == "expected-unsupported", f"age-disposition {r['case']}")
        need(r["reason"] == "mode-3-pixel-timing", f"age-reason {r['case']}")
        need(r["decision"] == "D-09" and r["owner_phase"] == 14, f"age-decision {r['case']}")
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


def check_tracked(repo_root: pathlib.Path, suites: dict) -> None:
    out = subprocess.run(["git", "-C", str(repo_root), "ls-files", "-z", "--", "fixtures"],
                         check=True, capture_output=True).stdout.decode("utf-8", "replace")
    stems = [r["case"] for r in suites["mealybug"]["rows"]]
    for path in filter(None, out.split("\0")):
        name = path.rsplit("/", 1)[-1]
        if not name.lower().endswith((".gb", ".gbc", ".png")):
            continue
        need("m3-bg-" not in name, f"tracked-age-file {path}")
        need(not any(name.startswith(stem) for stem in stems), f"tracked-mealybug-file {path}")


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
    args = ap.parse_args()
    try:
        suites = load_suites(args.record)
        expected = check_rows(suites)
        need(doc_rows(args.doc) == expected, "doc-mirror-differs")
        check_tracked(args.repo_root, suites)
    except (Mismatch, KeyError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"disposition-mismatch {type(exc).__name__ if not isinstance(exc, Mismatch) else ''}{exc}")
        return 1
    print(f"external-dispositions pass age=6 mealybug={len(suites['mealybug']['rows'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
