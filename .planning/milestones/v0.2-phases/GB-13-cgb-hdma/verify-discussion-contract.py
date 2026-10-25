#!/usr/bin/env python3
"""Local Phase 13 discussion receipt; deliberately not a recurring CI job."""

import argparse
import json
from pathlib import Path, PurePosixPath
import re


ROOT = Path(__file__).resolve().parents[3]
PHASE = ".planning/phases/GB-13-cgb-hdma"
CONTEXT = f"{PHASE}/13-CONTEXT.md"
RECORDS = (
    CONTEXT,
    f"{PHASE}/13-DISCUSSION-LOG.md",
    f"{PHASE}/continue.md",
    ".planning/.continue-here.md",
    ".planning/STATE.md",
    ".planning/state.json",
    ".planning/config.json",
    ".planning/REQUIREMENTS.md",
    ".planning/ROADMAP.md",
    ".planning/context/DECISIONS.md",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(records):
    context = records[CONTEXT]
    for section in ("domain", "decisions", "canonical_refs", "code_context", "specifics", "deferred"):
        require(context.count(f"<{section}>") == 1 and context.count(f"</{section}>") == 1,
                f"missing or duplicate section: {section}")
    ids = re.findall(r"^- \*\*D-(\d{2}):", context, re.M)
    require(ids == [f"{number:02}" for number in range(1, 26)], "decision ID inventory")
    require("DEEP planning research is still required" in context, "missing research boundary")
    require("master_time_delta == consumed_half_dots <= budget" in context, "missing time contract")
    require("whole-instruction" in context and "UNKNOWN" in context, "missing boundary qualification")
    refs = context.split("<canonical_refs>", 1)[1].split("</canonical_refs>", 1)[0]
    local_refs = [value for value in re.findall(r"`([^`]+)`", refs) if "/" in value]
    require(len(local_refs) >= 30, "empty canonical local references")
    for value in local_refs:
        path = PurePosixPath(value)
        require(not path.is_absolute() and ".." not in path.parts, "nonlocal canonical path")
        require((ROOT / value).is_file(), f"missing canonical file: {value}")
    for pin in (
        "0191af06ac49661587dcde3d57a241a626b8df75",
        "26a56bd6a122a6318a456abd80558408742d5adf",
        "f15645fb049a47ea235f6d2c9a033e72d8087901",
        "3f9c090f16e5a721db776febb9ba7d773e1c819c",
        "70e88fb90b59d19dfbb9c3ac36c64105202bb1f4",
    ):
        require(pin in refs and "https://github.com/" in refs, "missing source pin")
    require("- [ ] **CGB-07**" in records[".planning/REQUIREMENTS.md"], "premature requirement completion")
    config = json.loads(records[".planning/config.json"])
    for flag in ("auto_advance", "_auto_chain_active"):
        require(config["workflow"][flag] is False, f"enabled workflow flag: {flag}")
    state_json = json.loads(records[".planning/state.json"])
    require(state_json["next"]["command"] == "/gsd-plan-phase 13", "wrong machine route")
    phase = next(item for item in state_json["phases"] if item["number"] == "13")
    require(phase["status"] != "complete", "premature machine completion")
    for name in (".planning/STATE.md", ".planning/.continue-here.md", f"{PHASE}/continue.md"):
        require("/gsd-plan-phase 13" in records[name], f"missing planning route: {name}")
        require("discussion" in records[name].lower(), f"missing completed stage: {name}")
    require("current_phase: 13" in records[".planning/STATE.md"], "wrong active phase")
    rows = [line.split("|") for line in records[".planning/ROADMAP.md"].splitlines()
            if "| v0.2 |" in line]
    completed = sum(row[4].strip() == "Complete" for row in rows)
    state_count = re.search(r"^  completed_phases: (\d+)$", records[".planning/STATE.md"], re.M)
    require(state_count and int(state_count[1]) == completed, "phase progress disagrees with roadmap")
    require("D-096" in records[".planning/context/DECISIONS.md"], "missing dependency memory")
    require("D-097" in records[".planning/context/DECISIONS.md"], "missing mechanism gate memory")
    require(not list((ROOT / PHASE).glob("*-PLAN.md")), "discussion produced plans")
    require(not (ROOT / PHASE / "13-RESEARCH.md").exists(), "discussion masquerades as planning research")
    return len(local_refs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    records = {name: (ROOT / name).read_text(encoding="utf-8") for name in RECORDS}
    refs = verify(records)
    count = 0
    if args.self_test:
        cases = [
            (CONTEXT, records[CONTEXT].replace("<canonical_refs>", "<lost_refs>", 1), "canonical section"),
            (CONTEXT, records[CONTEXT].replace("**D-09:", "**D-29:", 1), "decision inventory"),
            (CONTEXT, records[CONTEXT].replace("`tests/test_dma.c`", "`tests/missing-p13-test.c`"), "missing file"),
            (CONTEXT, records[CONTEXT].replace("master_time_delta == consumed_half_dots <= budget", "unbounded"), "time bound"),
            (".planning/REQUIREMENTS.md", records[".planning/REQUIREMENTS.md"].replace("- [ ] **CGB-07**", "- [x] **CGB-07**"), "premature completion"),
            (".planning/state.json", records[".planning/state.json"].replace("/gsd-plan-phase 13", "/gsd-execute-phase 13"), "wrong machine route"),
            (".planning/.continue-here.md", records[".planning/.continue-here.md"].replace("/gsd-plan-phase 13", "/gsd-discuss-phase 13"), "stale handoff"),
            (".planning/STATE.md", re.sub(r"^  completed_phases: \d+$", "  completed_phases: 99", records[".planning/STATE.md"], flags=re.M), "false progress count"),
        ]
        for flag in ("auto_advance", "_auto_chain_active"):
            altered = json.loads(records[".planning/config.json"])
            altered["workflow"][flag] = True
            cases.append((".planning/config.json", json.dumps(altered), flag))
        for name, altered, label in cases:
            mutant = dict(records)
            mutant[name] = altered
            try:
                verify(mutant)
            except ValueError:
                count += 1
            else:
                raise ValueError(f"negative control escaped: {label}")
    print(f"discussion-contract pass decisions=25 local_refs={refs} negative_controls={count} next=/gsd-plan-phase-13")


if __name__ == "__main__":
    main()
