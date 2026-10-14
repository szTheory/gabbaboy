#!/usr/bin/env python3
"""Check the Phase 12 plan-19 closeout artifacts and their durable handoff."""

from __future__ import annotations

import argparse
import json
import statistics
import re
import shutil
import tempfile
from pathlib import Path


PHASE_DIR = Path(".planning/phases/GB-12-cgb-double-speed")
EXPECTED_EVIDENCE_HEAD = "301f1b05577e6d35a4c3a756ded1ec15a4082c8d"
REQUIRED_RUN_IDS = ("38502094649", "38502094682", "38502094771")
MEMORY_FILES = (
    Path(".planning/context/DECISIONS.md"),
    Path(".planning/context/LESSONS.md"),
    Path(".planning/research/INDEX.md"),
)
CLOSEOUT_FILES = (
    PHASE_DIR / "12-BENCH.md",
    PHASE_DIR / "COVERAGE.md",
    Path(".planning/STATE.md"),
    Path(".planning/.continue-here.md"),
    Path(".planning/config.json"),
)
FIXTURE_SOURCE = Path("fixtures/age/SOURCES.md")
ALL_FILES = MEMORY_FILES + CLOSEOUT_FILES + (FIXTURE_SOURCE,)
REQUIRED_DECISIONS = tuple(f"D-{number:03}" for number in range(84, 96))
REQUIRED_GSD_DECISIONS = ("D-37", "D-38", "D-39", "D-40", "D-41", "D-42")


def validate(root: Path) -> list[str]:
    problems: list[str] = []
    docs: dict[Path, str] = {}
    for relative in ALL_FILES:
        path = root / relative
        if not path.is_file():
            problems.append(f"missing required file: {relative}")
        else:
            docs[relative] = path.read_text(encoding="utf-8")

    decisions = docs.get(MEMORY_FILES[0], "")
    decision_ids = re.findall(r"^\| (D-\d{3}) \|", decisions, re.MULTILINE)
    if len(decision_ids) != len(set(decision_ids)) or decision_ids != sorted(
        decision_ids, key=lambda item: int(item[2:])
    ):
        problems.append("decision IDs must remain unique and ordered")
    for decision in REQUIRED_DECISIONS:
        if decision_ids.count(decision) != 1:
            problems.append(f"decision row {decision} must appear exactly once")
    for decision in REQUIRED_GSD_DECISIONS:
        if f"Phase 12 {decision}" not in decisions:
            problems.append(f"adopted Phase 12 decision {decision} is missing")

    lessons = docs.get(MEMORY_FILES[1], "")
    for lesson in ("GB-CGB-008", "GB-CGB-009", "GB-CGB-010"):
        if lesson not in lessons:
            problems.append(f"durable lesson {lesson} is missing")

    index = docs.get(MEMORY_FILES[2], "")
    phase_lines = [line for line in index.splitlines() if "GB-12-cgb-double-speed" in line]
    if len(phase_lines) != 1:
        problems.append("research index must have exactly one Phase 12 entry")
    else:
        line = phase_lines[0]
        if "12-BENCH.md" not in line or "AGE" not in line or "hardware evidence" not in line:
            problems.append("Phase 12 index entry must link benchmark evidence and state AGE limits")
        for link in re.findall(r"\]\(([^)#]+)\)", line):
            if not link.startswith(("https://", "http://")):
                target = (root / MEMORY_FILES[2].parent / link).resolve()
                if not target.is_file():
                    problems.append(f"Phase 12 research link does not resolve: {link}")

    bench = docs.get(CLOSEOUT_FILES[0], "")
    if bench.count("4c7a57ff3d50d228") < 2:
        problems.append("benchmark must record the unchanged DMG tracer digest twice")
    if not re.search(r"linux-asan-ubsan", bench):
        problems.append("benchmark must record hosted linux-asan-ubsan evidence")
    if not re.search(r"GB-CI-004", bench) or not re.search(r"826.?915", bench):
        problems.append("benchmark must compare hosted sanitizer time with GB-CI-004")
    if not re.search(r"Mutant core builds?:\s*5\b", bench, re.IGNORECASE):
        problems.append("benchmark must record the five-site mutant build count")
    if "--profile cgb" not in bench or not re.search(r"(?:3|three) warm.?ups", bench, re.IGNORECASE):
        problems.append("benchmark must record the CGB workload and warm-ups")
    if not re.search(r"30 measured runs", bench, re.IGNORECASE):
        problems.append("benchmark must record all 30 measurement samples")
    if "244c987a2da74e65" not in bench or "-O3 -DNDEBUG -std=c17" not in bench:
        problems.append("benchmark must record the CGB output digest and release flags")
    if not re.search(r"Host class: Darwin arm64", bench) or "Apple clang 21.0.0" not in bench:
        problems.append("benchmark must identify the measured host class and compiler")
    if "1,000,000 half-dots" not in bench or "Input ROM SHA-256" not in bench:
        problems.append("benchmark must identify its deterministic workload and fixture digest")
    if not all(token in bench for token in ("Median", "sample standard deviation", "95% margin")):
        problems.append("benchmark must report spread and uncertainty")
    if "0.91 s" not in bench or "0.25 s" not in bench:
        problems.append("benchmark must record mutant configure and compile cost")
    sample_block = re.search(r"Raw sample `elapsed_ns` values \(30\):\s*```text\s*(.*?)\s*```", bench, re.DOTALL)
    samples = [int(value) for value in re.findall(r"\d+", sample_block.group(1))] if sample_block else []
    if len(samples) != 30:
        problems.append("benchmark must preserve exactly 30 raw elapsed_ns samples")
    else:
        reported_stats = re.search(
            r"Median ([0-9.]+) ms; minimum ([0-9.]+) ms; sample standard deviation ([0-9.]+) ms; mean ([0-9.]+) ms; 95% margin of mean `[^`]+` = ([0-9.]+) ms",
            bench,
        )
        if not reported_stats:
            problems.append("benchmark summary must report median, minimum, spread, mean, and uncertainty")
        else:
            expected = (
                statistics.median(samples) / 1e6,
                min(samples) / 1e6,
                statistics.stdev(samples) / 1e6,
                statistics.mean(samples) / 1e6,
                1.96 * statistics.stdev(samples) / (len(samples) ** 0.5) / 1e6,
            )
            for reported, measured, tolerance, label in zip(
                map(float, reported_stats.groups()), expected, (0.00006, 0.00006, 0.00006, 0.00006, 0.00006),
                ("median", "minimum", "sample deviation", "mean", "95% margin"),
            ):
                if abs(reported - measured) > tolerance:
                    problems.append(f"reported {label} differs from the preserved raw samples")
    age_rows = re.findall(r"^\| `age_[^`]+` \| [0-9.]+ \|$", bench, re.MULTILINE)
    partition_rows = re.findall(r"^\| `cgb_partition_[^`]+` \| [0-9.]+ \|$", bench, re.MULTILINE)
    if len(age_rows) < 27 or len(partition_rows) < 18:
        problems.append("benchmark must list measured times for all AGE and partition tests")
    if not re.search(r"job wall [0-9]+m[0-9]+s", bench):
        problems.append("benchmark must record the hosted sanitizer job wall time")
    if not re.search(r"CTest test time [0-9.]+ s", bench):
        problems.append("benchmark must record hosted sanitizer CTest time")
    if not re.search(r"206 Phase 12 additions.*sum to 325\.28 s", bench):
        problems.append("benchmark must record the 206 Phase 12 ASan test-duration sum")
    if "All exact-head PR checks passed" not in bench or "required-native" not in bench:
        problems.append("benchmark must attest the exact-head required CI checks passed")
    if not re.search(r"delta", bench, re.IGNORECASE):
        problems.append("benchmark must state the GB-CI-004 sanitizer-time delta")
    if "different source revisions, test inventories, and runners" not in bench or "does not establish a speedup" not in bench:
        problems.append("historical sanitizer comparison must be qualified as non-causal")
    for statement in (
        "only `spsw-div-cgbBCE` and `spsw-stop-prefetch-cgbBCE` pass",
        "changes the `spsw-mode0-cgbBCE` result but not `spsw-div-cgbBCE`",
        "`spsw-tima-cgbBC` contingency drops the B/C TIMA claim",
        "not hardware results",
    ):
        if statement not in bench:
            problems.append(f"benchmark must preserve the qualified AGE scope: {statement}")
    benchmark_prose = re.sub(r"`[^`]*`", "", bench)
    if re.search(r"\b(?:evidence|measurement|result|comparison)\s+(?:is\s+)?pending\b|\bwill be filled\b", benchmark_prose, re.IGNORECASE):
        problems.append("benchmark still contains pending evidence")
    hosted_head = re.search(r"exact PR head is `([0-9a-f]{40})`", bench)
    ci_run_ids = re.search(r"CI run IDs: ([0-9, ]+)", bench)
    if not hosted_head:
        problems.append("benchmark must name the exact hosted PR head")
    elif hosted_head.group(1) != EXPECTED_EVIDENCE_HEAD:
        problems.append("benchmark must use the exact H2 PR evidence head")
    if not ci_run_ids:
        problems.append("benchmark must list exact hosted CI run IDs")
    run_ids = re.findall(r"\d{10,}", ci_run_ids.group(1)) if ci_run_ids else []
    if not run_ids:
        problems.append("benchmark CI run ID list is empty")
    for run_id in REQUIRED_RUN_IDS:
        if run_id not in run_ids:
            problems.append(f"benchmark must include exact PR evidence run {run_id}")

    fixture_source = docs.get(FIXTURE_SOURCE, "")
    if "fixture-repro" not in fixture_source or "result=byte-identical" not in fixture_source:
        problems.append("AGE SOURCES.md must record the Linux byte-reproduction receipt")
    if "all 13" not in fixture_source:
        problems.append("AGE SOURCES.md must say the Linux receipt covered all 13 ROMs")
    if hosted_head and hosted_head.group(1) not in fixture_source:
        problems.append("AGE SOURCES.md receipt must name the exact hosted source revision")
    if "result=byte-identical roms=2" not in bench or "speed-hostile.gb" not in bench:
        problems.append("benchmark must record both exact-head CGB speed fixture bytes")
    if "provisional until the Linux" in fixture_source:
        problems.append("AGE SOURCES.md still labels the Linux digest check provisional")
    if run_ids and not any(run_id in fixture_source for run_id in run_ids):
        problems.append("AGE SOURCES.md receipt must use a listed exact-head fixture-repro run")
    manifest_path = root / "fixtures/age/manifest.json"
    if manifest_path.is_file():
        try:
            manifest_count = len(json.loads(manifest_path.read_text(encoding="utf-8"))["fixtures"])
            if manifest_count != 13:
                problems.append(f"AGE fixture manifest expected 13 entries, found {manifest_count}")
        except (KeyError, json.JSONDecodeError) as error:
            problems.append(f"AGE fixture manifest is unreadable: {error}")

    coverage = docs.get(CLOSEOUT_FILES[1], "")
    coverage_lines = coverage.splitlines()
    prefix = "No external API integration: "
    if len(coverage_lines) != 1 or not coverage_lines[0].startswith(prefix):
        problems.append("COVERAGE.md must contain exactly one API-coverage declaration")
    elif len(coverage_lines[0][len(prefix) :]) > 200:
        problems.append("API-coverage declaration reason exceeds 200 characters")

    state = docs.get(CLOSEOUT_FILES[2], "")
    continuation = docs.get(CLOSEOUT_FILES[3], "")
    for label, text in (("STATE.md", state), ("continuation note", continuation)):
        for required in (
            "Phase 12 - CGB Double Speed, execution",
            "/gsd-verify-work 12",
            "Phase 13: CGB HDMA",
            "/gsd-discuss-phase 13",
            "auto_advance",
            "_auto_chain_active",
        ):
            if required not in text:
                problems.append(f"{label} is missing handoff field: {required}")
        if hosted_head and hosted_head.group(1) not in text:
            problems.append(f"{label} does not carry the exact hosted evidence head")
        for run_id in run_ids:
            if run_id not in text:
                problems.append(f"{label} does not carry hosted CI run ID {run_id}")
    if "Both workflow.auto_advance and workflow._auto_chain_active stay false; nothing advances automatically." not in continuation:
        problems.append("continuation note must state that automatic advancement stays disabled")

    config_path = root / CLOSEOUT_FILES[4]
    if config_path.is_file():
        try:
            workflow = json.loads(config_path.read_text(encoding="utf-8"))["workflow"]
            if workflow.get("auto_advance") is not False or workflow.get("_auto_chain_active") is not False:
                problems.append("workflow auto-advance flags must both be false")
        except (KeyError, json.JSONDecodeError) as error:
            problems.append(f"workflow config is unreadable: {error}")

    if list((root / ".planning/phases").glob("GB-13-*")):
        problems.append("Phase 13 must remain unstarted")

    privacy_files = MEMORY_FILES + CLOSEOUT_FILES[:4] + (FIXTURE_SOURCE,)
    for relative in privacy_files:
        text = docs.get(relative, "")
        if re.search(r"/Users/|[A-Za-z0-9._%+-]+@(?:gmail\.com|users\.noreply\.github\.com)", text, re.IGNORECASE):
            problems.append(f"privacy scan found a personal path or email in {relative}")

    return problems


def copy_fixture(source: Path, target: Path) -> None:
    for relative in ALL_FILES:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, destination)
    (target / ".planning/phases").mkdir(parents=True, exist_ok=True)


def self_test(source: Path) -> int:
    initial = validate(source)
    if initial:
        raise SystemExit("closeout contract rejected the repository:\n- " + "\n- ".join(initial))

    def reject_mutation(relative: Path, mutate, label: str) -> None:
        with tempfile.TemporaryDirectory(prefix="gbb-closeout-negative-") as directory:
            scratch = Path(directory)
            copy_fixture(source, scratch)
            path = scratch / relative
            path.write_text(mutate(path.read_text(encoding="utf-8")), encoding="utf-8")
            failures = validate(scratch)
            if not failures:
                raise SystemExit(f"closeout self-test accepted mutation: {label}")

    reject_mutation(
        MEMORY_FILES[0],
        lambda text: re.sub(r"^\| D-084 \|.*\n", "", text, count=1, flags=re.MULTILINE),
        "missing adopted decision",
    )
    reject_mutation(
        MEMORY_FILES[1],
        lambda text: text.replace("GB-CGB-008", "GB-CGB-000", 1),
        "missing durable lesson",
    )
    reject_mutation(
        MEMORY_FILES[2],
        lambda text: text.replace("12-BENCH.md", "missing-12-BENCH.md", 1),
        "unresolved research link",
    )
    reject_mutation(
        CLOSEOUT_FILES[0],
        lambda text: text.replace("4c7a57ff3d50d228", "0000000000000000"),
        "changed DMG digest",
    )
    reject_mutation(
        CLOSEOUT_FILES[0],
        lambda text: re.sub(r"^CI run IDs:.*\n", "", text, count=1, flags=re.MULTILINE),
        "missing exact hosted CI run IDs",
    )
    reject_mutation(
        CLOSEOUT_FILES[0],
        lambda text: text.replace("Mutant core builds: 5", "Mutant core builds: 7", 1),
        "out-of-budget mutant build count",
    )
    reject_mutation(
        CLOSEOUT_FILES[0],
        lambda text: text.replace("sum to 325.28 s", "sum to 99.99 s", 1),
        "altered Phase 12 sanitizer test-duration sum",
    )
    reject_mutation(
        CLOSEOUT_FILES[0],
        lambda text: text.replace("All exact-head PR checks passed", "Some jobs were reported", 1),
        "missing exact-head required-check success",
    )
    reject_mutation(
        CLOSEOUT_FILES[0],
        lambda text: re.sub(r"(Raw sample `elapsed_ns` values \(30\):\s*```text\s*)[0-9]+,", r"\g<1>", text, count=1),
        "incomplete advisory sample set",
    )
    reject_mutation(
        FIXTURE_SOURCE,
        lambda text: text.replace("result=byte-identical", "result=differs", 1),
        "non-matching AGE fixture reproduction receipt",
    )
    reject_mutation(
        FIXTURE_SOURCE,
        lambda text: text.replace("38502094682", "00000000000", 1),
        "missing exact fixture-repro run ID",
    )
    reject_mutation(
        CLOSEOUT_FILES[0],
        lambda text: text.replace("result=byte-identical roms=2", "result=byte-identical roms=1", 1),
        "incomplete CGB speed fixture reproduction receipt",
    )
    reject_mutation(
        CLOSEOUT_FILES[1],
        lambda text: text.replace("No external API integration:", "External API integration:"),
        "invalid API-coverage declaration",
    )
    reject_mutation(
        CLOSEOUT_FILES[2],
        lambda text: text.replace("/gsd-verify-work 12", "/gsd-verify-work 11", 1),
        "stale STATE verification route",
    )
    reject_mutation(
        CLOSEOUT_FILES[3],
        lambda text: text.replace("/gsd-discuss-phase 13", "/gsd-discuss-phase 12", 1),
        "wrong continuation phase route",
    )
    reject_mutation(
        CLOSEOUT_FILES[4],
        lambda text: text.replace('"auto_advance": false', '"auto_advance": true', 1),
        "enabled auto-advance flag",
    )
    with tempfile.TemporaryDirectory(prefix="gbb-closeout-phase13-") as directory:
        scratch = Path(directory)
        copy_fixture(source, scratch)
        (scratch / ".planning/phases/GB-13-cgb-hdma").mkdir()
        if not any("Phase 13 must remain unstarted" in item for item in validate(scratch)):
            raise SystemExit("closeout self-test accepted a started Phase 13 directory")

    print("PASS: closeout contract positive case and 17 scratch-mutation controls")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    root = args.root.resolve()
    if args.self_test:
        return self_test(root)
    problems = validate(root)
    if problems:
        print("FAIL: Phase 12 closeout contract")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print("PASS: Phase 12 closeout contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
