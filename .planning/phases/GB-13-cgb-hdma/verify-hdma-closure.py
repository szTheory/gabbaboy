#!/usr/bin/env python3
"""Close Phase 13 evidence and handoff contracts without qualifying hardware."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LANE_TESTS = (
    "cgb_hdma_claims_contract",
    "cgb_hdma_claims_contract_native",
    "cgb_hdma_claims_contract_selftest",
    "cgb_hdma_lane_contract",
    "cgb_hdma_lane_contract_selftest",
)
LANE_SCRIPT = ".planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py"
PLAN_PATH = ".planning/phases/GB-13-cgb-hdma/13-01-PLAN.md"
PROHIBITION_STATEMENT = (
    "CGB-07 evidence must not present author-test or emulator-differential agreement, "
    "including optional CGB-C ROM results, as physical CGB-E qualification."
)
ADAPTER_PATH = "tests/scripts/cgb-hdma-prohibition.test.cjs"
CLAIMS_CHECKER = "tests/scripts/verify-cgb-hdma-claims.py"
PROHIBITION_DIR = "build/phase13-prohibition"


class ContractError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def read(root: Path, relative: str) -> str:
    try:
        return (root / relative).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ContractError(f"missing or unreadable {relative}: {error}") from error


def occurrences(text: str, needle: str) -> int:
    return len(re.findall(re.escape(needle), text))


def lane_contract(root: Path) -> None:
    cmake = read(root, "tests/CMakeLists.txt")
    expected = read(root, "tests/expected-tests.txt").splitlines()
    player_expected = read(root, "tests/player/expected-tests.txt").splitlines()
    claims = read(root, "tests/scripts/verify-cgb-hdma-claims.py")
    fixture = read(root, ".github/workflows/fixture-repro.yml")
    ci = read(root, ".github/workflows/ci.yml")
    package_smoke = read(root, "cmake/PreviewPackageSmoke.cmake")
    player_claims = read(root, "tests/player/claims_agree.cmake")
    direct_registrations = re.findall(r"(?m)^\s*add_test\(NAME ([A-Za-z0-9_]+)", cmake)

    for name in LANE_TESTS:
        require(expected.count(name) == 1,
                f"exact core inventory must contain {name} once")
        require(direct_registrations.count(name) == 1,
                f"CTest must register {name} exactly once")
    require("--native-player" in cmake,
            "native claim target must use the explicit --native-player selector")
    require(f'"${{GBB_HDMA_CLOSURE_CHECKER}}" --lane' in cmake,
            "lane target must invoke the Python standard-library --lane selector")
    require(f'"${{GBB_HDMA_CLOSURE_CHECKER}}" --lane-self-test' in cmake,
            "lane control must invoke the Python standard-library --lane-self-test selector")
    require("--prohibitions" not in cmake and "--handoff" not in cmake,
            "local OpenGSD and handoff gates must stay outside recurring CTest")
    require("node " not in cmake and "gsd-tools" not in cmake,
            "recurring lane and claim CTests must not depend on Node or OpenGSD")

    core_hdma = [name for name in expected if name.startswith("cgb_hdma_") or name.startswith("samesuite_hdma_")]
    require(len(core_hdma) >= 90,
            "core HDMA inventory is unexpectedly incomplete")
    player_hdma = [name for name in player_expected if "hdma" in name.lower()]
    require(player_hdma,
            "player HDMA inventory is missing its existing smoke coverage")
    require("claims_agree" in player_claims and
            "GDMA and HBlank DMA run on the selected bootless CGB-CPU-E software model" in player_claims and
            "physical CGB-E remains UNKNOWN/POLICY" in player_claims,
            "player claims contract must retain delivered HDMA scope and its physical qualification limit")

    for needle in (
        "reproduce-cgb-hdma.sh --self-check",
        "reproduce-cgb-hdma.sh --self-test",
        "reproduce-cgb-hdma.sh --compare-pinned",
    ):
        require(needle in fixture,
                f"fixture-repro workflow is missing source-pinned check: {needle}")
    require("check_cgb_hdma_fixture_bytes" in fixture or "GBB_RGBDS_ARCHIVE_SHA256" in fixture,
            "fixture-repro must retain its digest-verified tool/source checks")
    require("ScanForbiddenFixtures.cmake" in package_smoke and "CGB-HDMA" in package_smoke,
            "installed package smoke must keep the active CGB-HDMA exclusion scan")
    require("--self-test" in claims and "--subject" in claims and "ALL_SURFACES" in claims,
            "claim checker must retain its complete-surface, subject and mutation controls")

    require("ctest --preset phase1-asan --parallel 4" in ci,
            "Debug ASan CI parallel4 contract changed")
    asan_job = re.search(r"(?ms)^  linux-sanitizers:\n(?P<section>.*?)(?=^  [a-z0-9-]+:\n|\Z)", ci)
    require(asan_job is not None and
            "name: linux-asan-ubsan" in asan_job.group("section") and
            re.search(r"(?m)^    timeout-minutes:\s*30\s*$", asan_job.group("section")) is not None,
            "Linux ASan job timeout changed from the recorded 30-minute policy")
    require("TIMEOUT 60" in cmake and "TIMEOUT 30" in cmake,
            "existing per-test timeout policy appears to have been removed")
    require("gabbaboy_verify_registered_tests()" in cmake,
            "complete configure-time expected-test enumeration guard is missing")
    print("hdma-lane-contract pass targets=5 core_hdma=%d player_hdma=%d parallel=4 timeout=30" %
          (len(core_hdma), len(player_hdma)))


def lane_self_test(root: Path) -> None:
    lane_contract(root)
    required = (
        "tests/CMakeLists.txt",
        "tests/expected-tests.txt",
        "tests/player/expected-tests.txt",
        "tests/scripts/verify-cgb-hdma-claims.py",
        ".github/workflows/fixture-repro.yml",
        ".github/workflows/ci.yml",
        "cmake/PreviewPackageSmoke.cmake",
        "tests/player/claims_agree.cmake",
    )
    with tempfile.TemporaryDirectory(prefix="gabbaboy-hdma-lane-") as temporary:
        scratch = Path(temporary)
        for relative in required:
            target = scratch / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / relative, target)
        controls = (
            ("missing-case", "tests/expected-tests.txt", "cgb_hdma_claims_contract_native"),
            ("skipped-lane", "tests/CMakeLists.txt", "cgb_hdma_lane_contract"),
            ("changed-parallelism", ".github/workflows/ci.yml", "--parallel 4"),
        )
        for label, relative, token in controls:
            source = scratch / relative
            original = source.read_text(encoding="utf-8")
            if label == "changed-parallelism":
                mutated = original.replace(token, "--parallel 1", 1)
            else:
                line = next((line for line in original.splitlines() if token in line), "")
                mutated = original.replace(line + "\n", "", 1)
            require(mutated != original,
                    f"{label} mutation anchor did not occur")
            source.write_text(mutated, encoding="utf-8")
            try:
                lane_contract(scratch)
            except ContractError:
                pass
            else:
                raise ContractError(f"lane self-test did not reject {label}")
            source.write_text(original, encoding="utf-8")
    print("hdma-lane self-test pass controls=3")


def git_output(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    require(result.returncode == 0, f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def runtime_tools(root: Path) -> Path:
    candidate = os.environ.get("GSD_TOOLS", "").strip()
    candidates: list[str] = []
    if candidate:
        tools = Path(candidate).expanduser()
        if not tools.is_file():
            raise ContractError(f"explicit GSD_TOOLS override is not a regular file: {tools}")
        candidates.append(str(tools))
    else:
        runtime_root = Path(os.environ.get("RUNTIME_DIR", git_output(root, "rev-parse", "--show-toplevel")))
        candidates.extend((
            str(runtime_root / "gsd-core/bin/gsd-tools.cjs"),
            str(runtime_root / ".claude/gsd-core/bin/gsd-tools.cjs"),
            str(runtime_root / ".codex/gsd-core/bin/gsd-tools.cjs"),
        ))
        home = Path.home()
        config_roots = (
            os.environ.get("CLAUDE_CONFIG_DIR", str(home / ".codex")),
            os.environ.get("ANTIGRAVITY_CONFIG_DIR", str(home / ".gemini/antigravity")),
            str(home / ".gemini/antigravity-ide"),
            str(home / ".gemini/antigravity-cli"),
            os.environ.get("AUGMENT_CONFIG_DIR", str(home / ".augment")),
            os.environ.get("CLINE_CONFIG_DIR", str(home / ".cline")),
            os.environ.get("CODEBUDDY_CONFIG_DIR", str(home / ".codebuddy")),
            os.environ.get("CODEX_HOME", str(home / ".codex")),
            os.environ.get("COPILOT_CONFIG_DIR", os.environ.get("COPILOT_HOME", str(home / ".copilot"))),
            os.environ.get("CURSOR_CONFIG_DIR", str(home / ".cursor")),
            os.environ.get("HERMES_HOME", str(home / ".hermes")),
            os.environ.get("KILO_CONFIG_DIR", str(Path(os.environ.get("XDG_CONFIG_HOME", home / ".config")) / "kilo")),
            os.environ.get("KIMI_CONFIG_DIR", str(home / ".config/agents")),
            str(home / ".agents"),
            os.environ.get("KIMI_CODE_HOME", str(home / ".kimi-code")),
            os.environ.get("OPENCODE_CONFIG_DIR", str(Path(os.environ.get("XDG_CONFIG_HOME", home / ".config")) / "opencode")),
            os.environ.get("PI_CODING_AGENT_DIR", str(home / ".pi/agent")),
            os.environ.get("QWEN_CONFIG_DIR", str(home / ".qwen")),
            os.environ.get("TRAE_CONFIG_DIR", str(home / ".trae")),
            os.environ.get("WINDSURF_CONFIG_DIR", str(home / ".codeium/windsurf")),
            os.environ.get("ZCODE_CONFIG_DIR", str(home / ".zcode")),
            os.environ.get("GROK_AGENTS_HOME", str(home / ".agents")),
        )
        candidates.extend(str(Path(directory) / "gsd-core/bin/gsd-tools.cjs") for directory in config_roots)
        path_candidate = shutil.which("gsd_run")
        if path_candidate:
            candidates.append(path_candidate)
    found = next((path for path in candidates if Path(path).is_file()), None)
    require(found is not None, "standard gsd_run resolver found no installed gsd-tools.cjs")
    tools = Path(found).resolve()
    require(tools.is_file(), f"resolved GSD_TOOLS is missing: {tools}")
    identity = subprocess.run(["node", str(tools), "runtime-identity", "--raw"],
                               cwd=root, capture_output=True, text=True, check=False)
    require(identity.returncode == 0, f"OpenGSD runtime identity check failed: {identity.stderr.strip()}")
    try:
        actual = json.loads(identity.stdout)
    except json.JSONDecodeError as error:
        raise ContractError(f"OpenGSD runtime identity was not JSON: {error}") from error
    require(actual.get("packageName") == "@opengsd/gsd-core",
            f"resolved runtime is not @opengsd/gsd-core: {identity.stdout.strip()}")
    require(actual.get("version") == "1.16.0",
            f"resolved OpenGSD runtime identity changed: {identity.stdout.strip()}")
    return tools


def projection_helper(root: Path, tools: Path, item: dict | None = None) -> dict:
    script = r"""
const fs = require('node:fs');
const path = require('node:path');
const runtime = path.dirname(process.env.GSD_TOOLS);
const probe = require(path.join(runtime, 'lib', 'probe-core.cjs'));
const enforcement = require(path.join(runtime, 'lib', 'prohibition-enforcement.cjs'));
const frontmatter = require(path.join(runtime, 'lib', 'frontmatter.cjs'));
let items;
if (process.env.GSD_PLAN_PATH) {
  const content = fs.readFileSync(process.env.GSD_PLAN_PATH, 'utf8');
  items = frontmatter.parseMustHavesBlock(content, 'prohibitions');
} else {
  items = [JSON.parse(process.env.GSD_PROHIBITION_ITEM)];
}
const projected = probe.projectProhibitions(items);
const descriptor = projected.length ? enforcement.descriptorFromProjection(projected[0]) : null;
process.stdout.write(JSON.stringify({ items, projected, descriptor }));
"""
    environment = os.environ.copy()
    environment["GSD_TOOLS"] = str(tools)
    if item is None:
        environment["GSD_PLAN_PATH"] = str(root / PLAN_PATH)
        environment.pop("GSD_PROHIBITION_ITEM", None)
    else:
        environment["GSD_PROHIBITION_ITEM"] = json.dumps(item, separators=(",", ":"))
        environment.pop("GSD_PLAN_PATH", None)
    result = subprocess.run(["node", "-e", script], cwd=root, env=environment,
                            capture_output=True, text=True, check=False, timeout=10)
    require(result.returncode == 0,
            f"OpenGSD projection/parser subprocess failed: {result.stdout}{result.stderr}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ContractError(f"OpenGSD projection/parser emitted invalid JSON: {error}: {result.stdout}") from error


def expected_prohibition(root: Path) -> dict:
    return {
        "statement": PROHIBITION_STATEMENT,
        "status": "resolved",
        "verification": "test",
        "check_kind": "node-test",
        "check_target": ADAPTER_PATH,
        "check_violation_fixture": f"{PROHIBITION_DIR}/known-bad.json",
        "check_clean_fixture": f"{PROHIBITION_DIR}/clean.json",
    }


def assert_projection(projected: dict, descriptor: dict | None) -> None:
    expected = {
        "statement": PROHIBITION_STATEMENT,
        "status": "resolved",
        "verification": "test",
        "check_kind": "node-test",
        "check_target": ADAPTER_PATH,
        "check_violation_fixture": f"{PROHIBITION_DIR}/known-bad.json",
        "check_clean_fixture": f"{PROHIBITION_DIR}/clean.json",
    }
    require(projected == expected, f"OpenGSD prohibition projection changed: {projected}")
    expected_descriptor = {
        "kind": "node-test",
        "target": ADAPTER_PATH,
        "violationFixture": expected["check_violation_fixture"],
        "cleanFixture": expected["check_clean_fixture"],
    }
    require(descriptor == expected_descriptor,
            f"OpenGSD descriptor read-back changed: {descriptor}")


def serialize_flat_prohibition(item: dict) -> str:
    lines = [f"    - statement: {json.dumps(item['statement'], ensure_ascii=False)}"]
    for key in ("status", "verification", "check_kind", "check_target",
                "check_violation_fixture", "check_clean_fixture"):
        lines.append(f"      {key}: {json.dumps(item[key], ensure_ascii=False)}")
    return "\n".join(lines)


def write_projected_plan(root: Path, item: dict) -> str:
    path = root / PLAN_PATH
    original = read(root, PLAN_PATH)
    unresolved = "    - statement: " + json.dumps(PROHIBITION_STATEMENT, ensure_ascii=False) + "\n      status: unresolved"
    serialized = serialize_flat_prohibition(item)
    pending = (
        "The descriptor-less prohibition above was projected with OpenGSD projectProhibitions. "
        "It remains flagged-unverified during planning. After13-11 creates the real claim predicate,13-12 Task1 creates its node:test adapter and generated bad/clean subjects, proves the installed OpenGSD producer red/clean/non-vacuous behavior, then serializes a resolved/test descriptor back into this exact item using projectProhibitions. Until that execution proof exists retain this unresolved item without a descriptor. Resolution covers the machine-checkable claim safeguard only; physical CGB-E behavior remains UNKNOWN.13-12 closure must reject a still-flagged prohibition before phase verification."
    )
    closed = (
        "Plan 13-12 recorded the actual OpenGSD fail-first/clean/live-checkout proof in "
        "build/phase13-prohibition/receipt.json. The resolved/test descriptor was read back "
        "through the installed parser and projector before the saved projection was re-verified. "
        "This resolves only the machine-checkable claim safeguard; physical CGB-E behavior remains "
        "UNKNOWN/POLICY, and the separate generic unresolved edge remains open."
    )
    if occurrences(original, unresolved) == 1:
        updated = original.replace(unresolved, serialized, 1)
        require(occurrences(updated, pending) == 1,
                "the exact planning-pending prohibition prose was not found once")
        updated = updated.replace(pending, closed, 1)
    else:
        require(occurrences(original, serialized) == 1 and occurrences(original, closed) == 1,
                "the saved prohibition is neither the expected unresolved item nor the verified projection")
        return original
    path.write_text(updated, encoding="utf-8")
    return original


def prepare_subjects(root: Path, directory: Path) -> tuple[Path, Path]:
    command = [sys.executable, "-I", CLAIMS_CHECKER,
               "--prepare-prohibition-subjects", str(directory)]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False, timeout=30)
    require(result.returncode == 0,
            f"claim checker could not regenerate prohibition subjects: {result.stdout}{result.stderr}")
    clean = directory / "clean.json"
    bad = directory / "known-bad.json"
    require(clean.is_file() and bad.is_file(), "claim checker did not produce both prohibition subjects")
    clean_result = subprocess.run([sys.executable, "-I", CLAIMS_CHECKER, "--subject", str(clean)],
                                  cwd=root, capture_output=True, text=True, check=False, timeout=30)
    require(clean_result.returncode == 0,
            f"known-clean subject was not accepted: {clean_result.stdout}{clean_result.stderr}")
    bad_result = subprocess.run([sys.executable, "-I", CLAIMS_CHECKER, "--subject", str(bad)],
                                cwd=root, capture_output=True, text=True, check=False, timeout=30)
    diagnostic = "CGB-C evidence must not be presented as physical CGB-E qualification"
    require(bad_result.returncode == 1 and diagnostic in bad_result.stdout + bad_result.stderr,
            f"known-bad subject did not fail on the qualification diagnostic: {bad_result.stdout}{bad_result.stderr}")
    return clean, bad


def gate_request(item: dict | None, descriptor: dict | None, mode: str = "autonomous") -> dict:
    return {"prohibition": item, "check": descriptor, "mode": mode}


def run_gate(root: Path, tools: Path, request: dict, label: str) -> dict:
    directory = root / PROHIBITION_DIR
    directory.mkdir(parents=True, exist_ok=True)
    request_path = directory / f"{label}-request.json"
    request_path.write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    command = ["node", str(tools)]
    if root.resolve() != ROOT.resolve():
        command.extend(["--project-dir", str(root.resolve())])
    command.extend(["check", "prohibition-enforcement", str(request_path.relative_to(root)), "--raw"])
    result = subprocess.run(command,
                           cwd=root, capture_output=True, text=True, check=False, timeout=120)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ContractError(f"OpenGSD gate emitted non-JSON for {label}: {error}: {result.stdout}{result.stderr}") from error
    require(isinstance(payload, dict), f"OpenGSD gate did not emit a root JSON object for {label}")
    return payload


def require_green_gate(payload: dict, label: str) -> None:
    require(payload.get("status") == "green" and payload.get("flagged") is False and
            payload.get("tier") == "test" and payload.get("located") is True and
            payload.get("kind") == "node-test",
            f"OpenGSD prohibition gate was not green/unflagged/located/test/node-test ({label}): {payload}")
    evidence = payload.get("evidence")
    require(isinstance(evidence, list) and len(evidence) > 0,
            f"OpenGSD prohibition gate evidence is empty ({label})")
    row = evidence[0]
    require(isinstance(row, dict) and row.get("passed") is True and
            row.get("failFirst") is True and row.get("failFirstProof") == "violation-fixture",
            f"OpenGSD prohibition gate lacks actual fail-first/clean/live proof ({label}): {evidence}")


def require_closed_gate(payload: dict, label: str) -> None:
    require(payload.get("status") != "green" or payload.get("flagged") is not False,
            f"OpenGSD prohibition producer incorrectly accepted negative control {label}: {payload}")


def run_prohibitions(root: Path) -> dict:
    tools = runtime_tools(root)
    directory = root / PROHIBITION_DIR
    clean, bad = prepare_subjects(root, directory)
    item = expected_prohibition(root)
    first = projection_helper(root, tools, item)
    require(len(first.get("projected", [])) == 1,
            f"OpenGSD projector returned the wrong item count: {first}")
    projected = first["projected"][0]
    descriptor = first.get("descriptor")
    assert_projection(projected, descriptor)

    proposal_request = gate_request(projected, descriptor)
    proposal = run_gate(root, tools, proposal_request, "request")
    require_green_gate(proposal, "proposed projection")

    old_plan = write_projected_plan(root, projected)
    try:
        readback = projection_helper(root, tools)
        require(len(readback.get("projected", [])) == 1,
                f"saved plan did not parse to exactly one prohibition: {readback}")
        saved_item = readback["projected"][0]
        saved_descriptor = readback.get("descriptor")
        assert_projection(saved_item, saved_descriptor)
        saved_request = gate_request(saved_item, saved_descriptor)
        payload = run_gate(root, tools, saved_request, "request")
        require_green_gate(payload, "saved parser/projector round-trip")
    except Exception:
        (root / PLAN_PATH).write_text(old_plan, encoding="utf-8")
        raise
    receipt_path = directory / "receipt.json"
    receipt_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    report = {
        "runtime": str(tools),
        "identity": "@opengsd/gsd-core@1.16.0",
        "sourceRevision": git_output(root, "rev-parse", "HEAD"),
        "subjects": {
            "clean": str(clean.relative_to(root)),
            "knownBad": str(bad.relative_to(root)),
        },
        "proposal": proposal,
        "savedProjection": saved_item,
        "savedDescriptor": saved_descriptor,
        "producer": payload,
        "receipt": str(receipt_path.relative_to(root)),
    }
    (directory / "closure.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("hdma-prohibition pass fail-first=violation-fixture clean=pass live=pass projection=round-trip")
    return payload


def prohibition_self_test(root: Path) -> None:
    tools = runtime_tools(root)
    directory = root / PROHIBITION_DIR
    clean, bad = prepare_subjects(root, directory)
    projected = projection_helper(root, tools, expected_prohibition(root))
    item = projected["projected"][0]
    descriptor = projected["descriptor"]
    assert_projection(item, descriptor)
    plan_before = read(root, PLAN_PATH)

    require_closed_gate(run_gate(root, tools, gate_request(item, None), "selftest-no-descriptor"), "missing descriptor")
    missing_bad = dict(descriptor)
    missing_bad["violationFixture"] = f"{PROHIBITION_DIR}/missing-known-bad.json"
    require_closed_gate(run_gate(root, tools, gate_request(item, missing_bad), "selftest-missing-bad"), "missing bad subject")
    empty_bad = directory / "empty-known-bad.json"
    empty_bad.write_text("", encoding="utf-8")
    empty_bad_descriptor = dict(descriptor, violationFixture=str(empty_bad.relative_to(root)))
    require_closed_gate(run_gate(root, tools, gate_request(item, empty_bad_descriptor), "selftest-empty-bad"), "empty bad subject")
    malformed_bad = directory / "malformed-known-bad.json"
    malformed_bad.write_text("{", encoding="utf-8")
    malformed_bad_descriptor = dict(descriptor, violationFixture=str(malformed_bad.relative_to(root)))
    malformed_payload = run_gate(root, tools, gate_request(item, malformed_bad_descriptor),
                                 "selftest-malformed-bad")
    require_closed_gate(malformed_payload, "non-qualification checker failure")
    require(not any(isinstance(row, dict) and row.get("failFirst") is True
                    for row in malformed_payload.get("evidence", [])),
            f"malformed subject was counted as semantic fail-first evidence: {malformed_payload}")
    malformed_env = os.environ.copy()
    malformed_env["GSD_PROHIB_SUBJECT"] = str(malformed_bad)
    try:
        malformed_run = subprocess.run(
            ["node", "--test", "--test-reporter=tap", ADAPTER_PATH],
            cwd=root, env=malformed_env, capture_output=True, text=True,
            check=False, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ContractError(f"malformed-subject adapter control could not run: {error}") from error
    malformed_output = malformed_run.stdout + malformed_run.stderr
    semantic_test = "HDMA claim language does not turn software agreement into physical qualification"
    require(malformed_run.returncode != 0,
            "standalone adapter returned success for a malformed non-qualification subject")
    require(f"# Subtest: {semantic_test}" not in malformed_output and
            f"not ok 1 - {semantic_test}" not in malformed_output,
            "malformed-subject setup failure executed the semantic fail-first target")
    missing_clean = dict(descriptor, cleanFixture=f"{PROHIBITION_DIR}/missing-clean.json")
    require_closed_gate(run_gate(root, tools, gate_request(item, missing_clean), "selftest-missing-clean"), "missing clean subject")
    empty_clean = directory / "empty-clean.json"
    empty_clean.write_text("", encoding="utf-8")
    empty_clean_descriptor = dict(descriptor, cleanFixture=str(empty_clean.relative_to(root)))
    require_closed_gate(run_gate(root, tools, gate_request(item, empty_clean_descriptor), "selftest-empty-clean"), "empty clean subject")

    with tempfile.TemporaryDirectory(prefix="gabbaboy-hdma-prohibition-") as temporary:
        temp = Path(temporary)
        always_green = temp / "always-green.test.cjs"
        always_green.write_text("const {test}=require('node:test'); test('always green',()=>{});\n", encoding="utf-8")
        deceptive = dict(descriptor, target=str(always_green))
        require_closed_gate(run_gate(root, tools, gate_request(item, deceptive), "selftest-always-green"), "always-green adapter")
        empty_tap = temp / "empty.tap.test.cjs"
        empty_tap.write_text("// deliberately empty TAP control\n", encoding="utf-8")
        empty_tap_descriptor = dict(descriptor, target=str(empty_tap))
        require_closed_gate(run_gate(root, tools, gate_request(item, empty_tap_descriptor), "selftest-empty-tap"), "empty TAP")

    with tempfile.TemporaryDirectory(prefix="gabbaboy-hdma-live-unqualified-", dir="/private/tmp") as temporary:
        isolated = Path(temporary)
        try:
            bad_surfaces = json.loads(bad.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ContractError(f"generated live-claim subject is unreadable: {error}") from error
        for relative, text in bad_surfaces.items():
            destination = isolated / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(text, encoding="utf-8")
        for relative in (
            "include/gabbaboy/gabbaboy.h",
            "docs/cgb-profile.md",
            "tests/external/cgb-hdma-dispositions.json",
            CLAIMS_CHECKER,
            ADAPTER_PATH,
        ):
            destination = isolated / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / relative, destination)
        (isolated / ".planning").mkdir(parents=True, exist_ok=True)
        for source in (clean, bad):
            destination = isolated / source.relative_to(root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        live_descriptor = dict(descriptor)
        require_closed_gate(run_gate(isolated, tools, gate_request(item, live_descriptor),
                                     "selftest-live-unqualified"),
                            "live unqualified claim mutation")
    require(read(root, PLAN_PATH) == plan_before,
            "prohibition self-test changed the saved 13-01 projection")
    print("hdma-prohibition self-test pass controls=9 projection-unchanged=true")


def handoff_values(state: str, continuation: str, config: dict) -> None:
    required_route = "/gsd-verify-work 13"
    require("Phase 13 execution, pending automated closure" in state,
            "STATE.md does not name the Phase 13 execution/automated-closure stage")
    require("Phase 13 execution, pending automated closure" in continuation,
            "continue.md does not name the Phase 13 execution/automated-closure stage")
    state_commands = [line for line in state.splitlines() if line.strip().startswith("Next command:")]
    continuation_commands = [line for line in continuation.splitlines() if line.strip().startswith("Next command:")]
    require(any(required_route in line for line in state_commands),
            "STATE.md next command is not /gsd-verify-work 13")
    require(any(required_route in line for line in continuation_commands),
            "continue.md next command is not /gsd-verify-work 13")
    workflow = config.get("workflow", {}) if isinstance(config, dict) else {}
    require(workflow.get("auto_advance") is False and workflow.get("_auto_chain_active") is False,
            "workflow auto_advance and _auto_chain_active must both remain false")
    lines = (state + "\n" + continuation).splitlines()
    phase14_lines = [line.lower() for line in lines if "phase 14" in line.lower()]
    require(any("remains unstarted" in line for line in phase14_lines),
            "handoff must record Phase 14 CGB-E Model Qualification and Corpus as unstarted")
    forbidden = []
    for line in phase14_lines:
        if "remains unstarted" in line:
            continue
        for match in re.finditer(r"\bphase\s*14\b", line, flags=re.IGNORECASE):
            context = line[max(0, match.start() - 80):match.end() + 80]
            if re.search(r"\b(?:complete(?:d)?|start(?:ed|ing)?)\b", context,
                         flags=re.IGNORECASE):
                forbidden.append(line.lower())
                break
    require(not forbidden, f"handoff prematurely marks Phase 14 started or complete: {forbidden}")


def handoff_contract(root: Path) -> None:
    run_prohibitions(root)
    try:
        config = json.loads(read(root, ".planning/config.json"))
    except json.JSONDecodeError as error:
        raise ContractError(f".planning/config.json is malformed: {error}") from error
    state = read(root, ".planning/STATE.md")
    continuation = read(root, ".planning/phases/GB-13-cgb-hdma/continue.md")
    handoff_values(state, continuation, config)
    print("hdma-handoff pass stage=Phase13-execution-pending-automated-closure next=/gsd-verify-work-13 phase14=unstarted auto=false")


def summary_contract(root: Path, summary: str) -> None:
    require("CGB-07" in summary, "SUMMARY coverage does not trace the CGB-07 requirement")
    require("human_judgment: false" in summary,
            "SUMMARY coverage must declare human_judgment: false")
    coverage = re.search(r"(?ms)^coverage:\n(?P<body>.*?)(?=^[A-Za-z][A-Za-z0-9_-]*:|^---$|\Z)", summary)
    require(coverage is not None and "verification:" in coverage.group("body"),
            "SUMMARY has no block-style coverage verification entries")
    block = coverage.group("body")
    require("{" not in block and "}" not in block,
            "SUMMARY coverage must not use flow mappings or lists")
    require(not re.search(r"(?m)^\s*#", block),
            "SUMMARY coverage must not include inline comments")
    require(not re.search(r"(?m)^\s*kind:\s*ctest\s*$", block),
            "SUMMARY coverage uses unsupported kind: ctest")
    require(not re.search(r"(?m)^\s*kind:\s*(?!unit\s*$|integration\s*$|e2e\s*$|automated_ui\s*$|other\s*$)\S+", block),
            "SUMMARY coverage uses a verification kind outside the allowed vocabulary")
    summary_path = root / ".planning/phases/GB-13-cgb-hdma/13-12-SUMMARY.md"
    verifier = root / "tests/scripts/verify-summary-coverage.py"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix="-SUMMARY.md", dir=root / "build",
                                     delete=False) as temporary:
        temporary.write(summary)
        temporary_path = Path(temporary.name)
    try:
        result = subprocess.run([sys.executable, "-I", str(verifier), "--file", str(temporary_path)],
                                cwd=root, capture_output=True, text=True, check=False, timeout=30)
        require(result.returncode == 0,
                f"official summary_coverage parser rejected the block: {result.stdout}{result.stderr}")
    finally:
        temporary_path.unlink(missing_ok=True)
    if summary_path.is_file():
        result = subprocess.run([sys.executable, "-I", str(verifier), "--file", str(summary_path)],
                                cwd=root, capture_output=True, text=True, check=False, timeout=30)
        require(result.returncode == 0,
                f"official summary_coverage parser rejected the saved summary: {result.stdout}{result.stderr}")


def validate_remote_evidence(data: dict, expected_head: str) -> None:
    require(data.get("headSha") == expected_head,
            f"remote result head is stale: {data.get('headSha')} != {expected_head}")
    results = data.get("results")
    required = data.get("requiredJobs")
    require(isinstance(required, list) and required and isinstance(results, list),
            "remote evidence must list requiredJobs and results")
    index = {row.get("name"): row for row in results if isinstance(row, dict)}
    missing = [name for name in required if name not in index]
    require(not missing, f"remote evidence is missing required results: {missing}")
    bad = [name for name in required
           if index[name].get("headSha") != expected_head or
           index[name].get("status") != "completed" or
           index[name].get("conclusion") != "success"]
    require(not bad, f"remote required checks are skipped, stale, pending, or failed: {bad}")


def validate_source_revision(root: Path, bench: str, current_head: str) -> str:
    source_match = re.search(r"(?m)^- Source revision: `([0-9a-f]{40})`$", bench)
    require(source_match is not None,
            "13-BENCH must record the exact tested source revision")
    source_revision = source_match.group(1)
    require(git_output(root, "merge-base", "--is-ancestor", source_revision, current_head) == "",
            "tested source revision is not in the current history")
    changed = subprocess.run(["git", "diff", "--name-only", source_revision, current_head, "--",
                             "tests/CMakeLists.txt", "tests/expected-tests.txt",
                             "tests/scripts/cgb-hdma-prohibition.test.cjs",
                             "tests/scripts/verify-cgb-hdma-claims.py",
                             ".planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py"],
                            cwd=root, capture_output=True, text=True, check=False)
    require(changed.returncode == 0 and not changed.stdout.strip(),
            f"tested source files changed after their recorded revision: {changed.stdout}{changed.stderr}")
    return source_revision


def self_test(root: Path) -> None:
    plan = read(root, PLAN_PATH)
    require("requirements: [CGB-07]" in plan,
            "13-01 plan no longer traces the Phase 13 requirement")
    projection = projection_helper(root, runtime_tools(root))
    require(len(projection.get("projected", [])) == 1,
            f"saved prohibition projection is absent or malformed: {projection}")
    saved_item = projection["projected"][0]
    saved_descriptor = projection.get("descriptor")
    require(saved_item.get("status") == "resolved" and saved_item.get("verification") == "test",
            "saved prohibition remains unresolved or has the wrong verification tier")
    assert_projection(saved_item, saved_descriptor)
    receipt_path = root / PROHIBITION_DIR / "receipt.json"
    require(receipt_path.is_file(), "actual OpenGSD prohibition receipt is missing")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContractError(f"actual OpenGSD prohibition receipt is unreadable: {error}") from error
    require_green_gate(receipt, "saved receipt")

    bench = read(root, ".planning/phases/GB-13-cgb-hdma/13-BENCH.md")
    current_head = git_output(root, "rev-parse", "HEAD")
    validate_source_revision(root, bench, current_head)

    summary_path = root / ".planning/phases/GB-13-cgb-hdma/13-12-SUMMARY.md"
    if summary_path.is_file():
        summary_contract(root, summary_path.read_text(encoding="utf-8"))
    remote_path = root / PROHIBITION_DIR / "remote-checks.json"
    if remote_path.is_file():
        try:
            validate_remote_evidence(json.loads(remote_path.read_text(encoding="utf-8")), current_head)
        except (OSError, json.JSONDecodeError) as error:
            raise ContractError(f"remote check evidence is unreadable: {error}") from error
    print("hdma-closure self-test pass projection=resolved receipt=current-source summary=checked")


def closure_self_test(root: Path) -> None:
    self_test(root)
    sample = read(root, ".planning/phases/GB-13-cgb-hdma/13-11-SUMMARY.md")
    summary_contract(root, sample)
    for label, mutated in (
        ("ctest-kind", sample.replace("kind: integration", "kind: ctest", 1)),
        ("missing-requirement", sample.replace("CGB-07", "CGB-99")),
    ):
        try:
            summary_contract(root, mutated)
        except ContractError:
            pass
        else:
            raise ContractError(f"closure self-test accepted forged summary control {label}")

    current_head = git_output(root, "rev-parse", "HEAD")
    bench = read(root, ".planning/phases/GB-13-cgb-hdma/13-BENCH.md")
    wrong_revision = re.sub(r"(?m)^- Source revision: `[0-9a-f]{40}`$",
                            "- Source revision: `" + "0" * 40 + "`", bench, count=1)
    require(wrong_revision != bench, "closure self-test could not prepare a source-revision mutation")
    try:
        validate_source_revision(root, wrong_revision, current_head)
    except ContractError:
        pass
    else:
        raise ContractError("closure self-test accepted a stale source-revision receipt")

    handoff_base_state = """Current stage: Phase 13 execution, pending automated closure.
Next command: /gsd-verify-work 13
Phase 14 — CGB-E Model Qualification and Corpus remains unstarted.
"""
    handoff_base_continue = """Current stage: Phase 13 execution, pending automated closure.
Next command: /gsd-verify-work 13
Phase 14 — CGB-E Model Qualification and Corpus remains unstarted.
"""
    handoff_base_config = {"workflow": {"auto_advance": False, "_auto_chain_active": False}}
    handoff_values(handoff_base_state, handoff_base_continue, handoff_base_config)
    historical_state = handoff_base_state + (
        "Completed workflow stage: Phase 12 planning with a long recorded rationale, "
        "decision mapping, and owner review history before its future deferrals; "
        "Phase 14 deferrals were documented as open follow-up work.\n")
    handoff_values(historical_state, handoff_base_continue, handoff_base_config)
    handoff_mutants = (
        ("stale-route", handoff_base_state.replace("/gsd-verify-work 13", "/gsd-discuss-phase 14", 1),
         handoff_base_continue, handoff_base_config),
        ("auto-advance", handoff_base_state, handoff_base_continue,
         {"workflow": {"auto_advance": True, "_auto_chain_active": False}}),
        ("phase14-started", handoff_base_state.replace("remains unstarted", "started", 1),
         handoff_base_continue, handoff_base_config),
        ("phase14-completed", handoff_base_state.replace("remains unstarted", "completed", 1),
         handoff_base_continue, handoff_base_config),
    )
    for label, state, continuation, config in handoff_mutants:
        try:
            handoff_values(state, continuation, config)
        except ContractError:
            pass
        else:
            raise ContractError(f"closure self-test accepted handoff mutation {label}")

    remote_base = {"headSha": current_head, "requiredJobs": ["native", "fixture"], "results": [
        {"name": "native", "headSha": current_head, "status": "completed", "conclusion": "success"},
        {"name": "fixture", "headSha": current_head, "status": "completed", "conclusion": "success"},
    ]}
    validate_remote_evidence(remote_base, current_head)
    remote_mutants = (
        dict(remote_base, headSha="0" * 40),
        {**remote_base, "results": [dict(remote_base["results"][0], conclusion="skipped"), remote_base["results"][1]]},
        {**remote_base, "results": [remote_base["results"][0]]},
    )
    for index, mutant in enumerate(remote_mutants):
        try:
            validate_remote_evidence(mutant, current_head)
        except ContractError:
            pass
        else:
            raise ContractError(f"closure self-test accepted stale/skipped/missing remote result {index}")
    print("hdma-closure self-test pass controls=11")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--lane", action="store_true")
    modes.add_argument("--lane-self-test", action="store_true")
    modes.add_argument("--prohibitions", action="store_true")
    modes.add_argument("--prohibitions-self-test", action="store_true")
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--handoff", action="store_true")
    args = parser.parse_args()
    try:
        if args.lane:
            lane_contract(ROOT)
        elif args.lane_self_test:
            lane_self_test(ROOT)
        elif args.prohibitions:
            run_prohibitions(ROOT)
        elif args.prohibitions_self_test:
            prohibition_self_test(ROOT)
        elif args.self_test:
            closure_self_test(ROOT)
        elif args.handoff:
            handoff_contract(ROOT)
        else:
            raise ContractError("this closure mode is not implemented yet")
    except ContractError as error:
        print(f"hdma-closure-invalid: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
