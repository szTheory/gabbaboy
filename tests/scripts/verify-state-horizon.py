#!/usr/bin/env python3
"""Kill each operational time-horizon guard on an immutable core revision."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_SOURCES = (
    "CMakeLists.txt",
    "include/gabbaboy/gabbaboy.h",
    "src/core/gabbaboy.c",
    "src/core/gabbaboy_test.h",
    "src/core/gbb_accept_input.h",
    "tests/test_state_horizon.c",
)
CONTROL_CASE = "horizon_fixture_control"


class HorizonCheckError(Exception):
    pass


@dataclass(frozen=True)
class Edit:
    old: str
    new: str


@dataclass(frozen=True)
class Mutant:
    name: str
    case: str
    witnesses: tuple[str, ...]
    expected_failure: str
    edits: tuple[Edit, ...]


def edit(old: str, new: str) -> Edit:
    return Edit(old, new)


MUTANTS = (
    Mutant(
        "stop-wait", "horizon_stop_wait", ("# horizon witness: stop-wait",),
        "horizon discrepancy: stop-wait",
        (edit("uint64_t available = GBB_STATE_TIME_LIMIT - instance->time_half_dots;",
              "uint64_t available = UINT64_MAX - instance->time_half_dots;"),),
    ),
    Mutant(
        "cpu-stall", "horizon_cpu_stall",
        ("# horizon witness: horizon discrepancy: cpu-stall",),
        "horizon discrepancy: cpu-stall",
        (edit(
            """/* GBB_HORIZON_GUARD: cpu-stall */
            if (!state_time_fits(instance->time_half_dots, step)) {
                result.reason = GBB_STOP_NO_PROGRESS;
                return result;
            }""",
            "/* GBB_HORIZON_GUARD: cpu-stall */\n            /* mutant removed CPU-stall horizon preflight */"),),
    ),
    Mutant(
        "hdma-tick", "horizon_hdma_tick",
        ("# horizon witness: horizon discrepancy: hdma-tick",),
        "horizon discrepancy: hdma-tick",
        (edit(
            """/* GBB_HORIZON_GUARD: hdma-tick */
            if (!state_time_fits(instance->time_half_dots, 1u)) {
                result.reason = GBB_STOP_NO_PROGRESS;
                return result;
            }""",
            "/* GBB_HORIZON_GUARD: hdma-tick */\n            /* mutant removed HDMA tick horizon preflight */"),),
    ),
    Mutant(
        "irq", "horizon_irq", ("# horizon witness: horizon discrepancy: irq",),
        "horizon discrepancy: irq",
        (edit(
            """/* GBB_HORIZON_GUARD: irq */
            uint64_t irq_target = 0u;
            if (!state_time_project(instance->time_half_dots, irq_cost, &irq_target)) {
                result.reason = GBB_STOP_NO_PROGRESS;
                return result;
            }""",
            "/* GBB_HORIZON_GUARD: irq */\n            uint64_t irq_target = instance->time_half_dots + irq_cost;"),),
    ),
    Mutant(
        "halt", "horizon_halt", ("# horizon witness: horizon discrepancy: halt",),
        "horizon discrepancy: halt",
        (edit(
            """/* GBB_HORIZON_GUARD: halt */
            if (!state_time_fits(instance->time_half_dots, m_cycle)) { result.reason=GBB_STOP_NO_PROGRESS; return result; }""",
            "/* GBB_HORIZON_GUARD: halt */\n            /* mutant removed HALT horizon preflight */"),),
    ),
    Mutant(
        "instruction", "horizon_instruction",
        ("# horizon witness: horizon discrepancy: instruction",),
        "horizon discrepancy: instruction",
        (edit(
            """/* GBB_HORIZON_GUARD: instruction */
        uint64_t instruction_target = 0u;
        if (!state_time_project(instance->time_half_dots, cost, &instruction_target)) {
            result.reason = GBB_STOP_NO_PROGRESS;
            return result;
        }""",
            "/* GBB_HORIZON_GUARD: instruction */\n        uint64_t instruction_target = instance->time_half_dots + cost;"),),
    ),
    Mutant(
        "speed-switch-reservation", "horizon_speed_switch",
        ("# horizon witness: horizon discrepancy: speed-switch-reservation",),
        "horizon discrepancy: speed-switch-reservation",
        (edit(
            """/* GBB_HORIZON_GUARD: speed-switch-reservation */
                if (!state_time_fits(instance->time_half_dots, switch_headroom)) { /* P12-M22 */
                    result.reason = GBB_STOP_NO_PROGRESS;
                    return result;
                }""",
            "/* GBB_HORIZON_GUARD: speed-switch-reservation */\n                /* mutant removed full speed-switch reservation */"),),
    ),
    Mutant(
        "peripheral-addition", "horizon_peripheral",
        ("# horizon witness: peripheral-addition",),
        "horizon discrepancy: peripheral-addition",
        (
            edit(
                """/* GBB_HORIZON_GUARD: peripheral-addition */
    if (state_time_project(m->time_half_dots, half_dots, &target))
        advance_devices_to(m, target);""",
                """/* GBB_HORIZON_GUARD: peripheral-addition */
    target = m->time_half_dots + half_dots;
    advance_devices_to(m, target);""",
            ),
            edit(
                """    /* GBB_HORIZON_GUARD: peripheral-target */
    if (m->time_half_dots > GBB_STATE_TIME_LIMIT || target > GBB_STATE_TIME_LIMIT ||
        target < m->time_half_dots) return;""",
                "    /* GBB_HORIZON_GUARD: peripheral-target */\n    /* mutant removed target horizon backstop */",
            ),
        ),
    ),
    Mutant(
        "peripheral-target", "horizon_peripheral_target",
        ("# horizon witness: peripheral-target",),
        "horizon discrepancy: peripheral-target",
        (edit(
            """    /* GBB_HORIZON_GUARD: peripheral-target */
    if (m->time_half_dots > GBB_STATE_TIME_LIMIT || target > GBB_STATE_TIME_LIMIT ||
        target < m->time_half_dots) return;""",
            "    /* GBB_HORIZON_GUARD: peripheral-target */\n    /* mutant removed target horizon backstop */"),),
    ),
    Mutant(
        "ordinary-event", "horizon_event_admission",
        ("# horizon witness: ordinary-event cap-plus-one",),
        "horizon discrepancy: ordinary-event cap+1 admitted",
        (edit("""        /* GBB_HORIZON_GUARD: ordinary-event */
        if (event->at_half_dots > GBB_STATE_TIME_LIMIT ||
            event->at_half_dots < instance->time_half_dots""",
              """        /* GBB_HORIZON_GUARD: ordinary-event */
        if (event->at_half_dots < instance->time_half_dots"""),),
    ),
    Mutant(
        "borrowed-span", "horizon_span_admission",
        ("# horizon witness: borrowed-span cap-plus-one",),
        "horizon discrepancy: borrowed span cap+1 admitted or mutated",
        (
            edit("""        /* GBB_HORIZON_GUARD: borrowed-span-event */
        if (!input_event_valid(event) || event->at_half_dots > GBB_STATE_TIME_LIMIT ||
""",
                 """        /* GBB_HORIZON_GUARD: borrowed-span-event */
        if (!input_event_valid(event) ||
"""),
        ),
    ),
    Mutant(
        "hdma-block-reservation", "horizon_hdma_reservation",
        ("# horizon witness: horizon discrepancy: hdma-reservation",),
        "horizon discrepancy: hdma-reservation",
        (edit("return state_time_fits(m->time_half_dots, required);",
              "return UINT64_MAX - m->time_half_dots >= required;"),),
    ),
    Mutant(
        "run-entry-over-cap", "horizon_sentinels",
        ("# horizon witness: run-entry-over-cap",),
        "horizon discrepancy: over-cap live state was not refused unchanged",
        (edit(
            """    /* GBB_HORIZON_GUARD: run-entry-over-cap */
    if (instance->time_half_dots > GBB_STATE_TIME_LIMIT) {
        result.reason = GBB_STOP_INVALID_STATE;
        return result;
    }""",
            "    /* GBB_HORIZON_GUARD: run-entry-over-cap */\n    /* mutant removed live over-cap refusal */"),),
    ),
    Mutant(
        "public-wrappers", "horizon_wrappers",
        (
            "# horizon witness: wrapper gbb_run",
            "# horizon witness: wrapper gbb_run_ex",
            "# horizon witness: wrapper gbb_run_audio",
            "# horizon witness: wrapper gbb_accept_run_diagnostic",
            "# horizon witness: wrapper gbb_accept_run_audio",
        ),
        "horizon discrepancy: public or acceptance wrapper",
        (edit(
            """/* GBB_HORIZON_GUARD: instruction */
        uint64_t instruction_target = 0u;
        if (!state_time_project(instance->time_half_dots, cost, &instruction_target)) {
            result.reason = GBB_STOP_NO_PROGRESS;
            return result;
        }""",
            "/* GBB_HORIZON_GUARD: instruction */\n        uint64_t instruction_target = instance->time_half_dots + cost;"),),
    ),
)

EXPECTED_MUTANT_NAMES = (
    "stop-wait", "cpu-stall", "hdma-tick", "irq", "halt", "instruction",
    "speed-switch-reservation", "peripheral-addition", "peripheral-target",
    "ordinary-event", "borrowed-span", "hdma-block-reservation",
    "run-entry-over-cap", "public-wrappers",
)


def run(command: Sequence[str], *, cwd: Path | None = None,
        timeout: float = 60.0, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, cwd=cwd, text=True, capture_output=True,
                              check=False, timeout=timeout, env=env)
    except subprocess.TimeoutExpired as error:
        raise HorizonCheckError(f"command timed out after {timeout:g}s: {command[0]}") from error


def git_show(revision: str, path: str) -> bytes:
    result = subprocess.run(["git", "show", f"{revision}:{path}"], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise HorizonCheckError(f"immutable source unavailable for {path}: {detail}")
    return result.stdout


def resolve_revision(value: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise HorizonCheckError("--rev must be a resolved immutable 40-hex commit")
    result = run(["git", "rev-parse", "--verify", f"{value}^{{commit}}"], cwd=ROOT)
    resolved = result.stdout.strip()
    if result.returncode != 0 or resolved != value:
        raise HorizonCheckError("--rev does not resolve to the requested immutable commit")
    return resolved


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise HorizonCheckError(f"{label}: guard anchor must occur once, found {count}")
    return text.replace(old, new, 1)


def apply_mutant(source: str, mutant: Mutant) -> str:
    changed = source
    for index, replacement in enumerate(mutant.edits, start=1):
        changed = replace_once(changed, replacement.old, replacement.new,
                               f"{mutant.name} edit {index}")
    if changed == source:
        raise HorizonCheckError(f"{mutant.name}: mutation made no source change")
    return changed


def validate_mutant_inventory(mutants: Sequence[Mutant]) -> None:
    names = tuple(mutant.name for mutant in mutants)
    if names != EXPECTED_MUTANT_NAMES:
        raise HorizonCheckError(
            f"mutant inventory mismatch: expected {EXPECTED_MUTANT_NAMES}, found {names}")
    for mutant in mutants:
        if not mutant.case or not mutant.expected_failure or not mutant.witnesses or not mutant.edits:
            raise HorizonCheckError(f"{mutant.name}: incomplete branch/category/witness definition")


def self_test_helpers() -> None:
    validate_mutant_inventory(MUTANTS)
    try:
        validate_mutant_inventory(MUTANTS[:-1])
    except HorizonCheckError:
        pass
    else:
        raise HorizonCheckError("self-test: missing mutant category was accepted")
    for broken in ("missing", "duplicated\nguard\nguard"):
        try:
            replace_once(broken, "guard", "", "self-test anchor rejection")
        except HorizonCheckError:
            continue
        raise HorizonCheckError("self-test: missing or duplicate guard anchor was accepted")
    try:
        check_semantic_rejection(0, "# horizon witness: stop-wait\n", MUTANTS[0])
    except HorizonCheckError:
        pass
    else:
        raise HorizonCheckError("self-test: surviving mutant was accepted")
    try:
        check_semantic_rejection(1, "not ok 1 - unrelated\n", MUTANTS[0])
    except HorizonCheckError:
        pass
    else:
        raise HorizonCheckError("self-test: unwitnessed failure was accepted as a kill")


def check_semantic_rejection(exit_code: int, output: str, mutant: Mutant) -> None:
    if exit_code != 1:
        raise HorizonCheckError(f"{mutant.name}: semantic case must exit 1, got {exit_code}")
    expected_assertion = f"not ok 1 - {mutant.case}"
    if "TAP version 13" not in output or expected_assertion not in output:
        raise HorizonCheckError(f"{mutant.name}: failure was not a TAP assertion result")
    missing = [witness for witness in mutant.witnesses if witness not in output]
    if missing:
        raise HorizonCheckError(f"{mutant.name}: missing branch witness: {missing[0]}")
    if mutant.expected_failure not in output:
        raise HorizonCheckError(f"{mutant.name}: intended semantic discrepancy was not reported")
    assertion_at = output.index(expected_assertion)
    late_witnesses = [witness for witness in mutant.witnesses
                      if output.index(witness) > assertion_at]
    if late_witnesses:
        raise HorizonCheckError(
            f"{mutant.name}: branch witness followed the failing assertion: {late_witnesses[0]}")


def materialize_sources(revision: str, directory: Path) -> tuple[dict[str, bytes], str]:
    sources: dict[str, bytes] = {}
    for relative in REQUIRED_SOURCES:
        content = git_show(revision, relative)
        sources[relative] = content
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    cmake_text = sources["CMakeLists.txt"].decode("utf-8")
    version = re.search(r"project\(GabbaBoy VERSION (\d+)\.(\d+)\.(\d+)", cmake_text)
    if version is None:
        raise HorizonCheckError("immutable CMakeLists.txt has no numeric three-part release version")
    release = version.groups()
    return sources, ".".join(release)


def compiler_command(build_dir: Path) -> tuple[list[str], list[str], str]:
    cache = build_dir / "CMakeCache.txt"
    if not cache.is_file():
        raise HorizonCheckError("--build-dir must be an existing configured CMake build")
    values: dict[str, str] = {}
    for line in cache.read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.match(r"^([^:#]+):[^=]+=([^\r\n]*)$", line)
        if match:
            values[match.group(1)] = match.group(2)
    compiler_modules = sorted((build_dir / "CMakeFiles").glob("*/CMakeCCompiler.cmake"))
    if compiler_modules:
        compiler_text = compiler_modules[-1].read_text(encoding="utf-8", errors="replace")
        for key in ("CMAKE_C_COMPILER_ID", "CMAKE_C_COMPILER_FRONTEND_VARIANT"):
            match = re.search(rf'^set\({key} "([^"\n]*)"\)', compiler_text, re.M)
            if match:
                values[key] = match.group(1)
    compiler_value = values.get("CMAKE_C_COMPILER", "")
    if not compiler_value:
        raise HorizonCheckError("configured C compiler is missing from CMakeCache.txt")
    compiler = [compiler_value]
    launcher = values.get("CMAKE_C_COMPILER_LAUNCHER", "")
    if launcher:
        compiler = shlex.split(launcher.replace(";", " ")) + compiler
    compiler.extend(shlex.split(values.get("CMAKE_C_COMPILER_ARG1", "")))
    compiler_id = values.get("CMAKE_C_COMPILER_ID", "")
    frontend = values.get("CMAKE_C_COMPILER_FRONTEND_VARIANT", "")
    build_type = values.get("CMAKE_BUILD_TYPE", "").upper()
    msvc_style = compiler_id == "MSVC" or frontend == "MSVC"
    flags: list[str] = []
    flags.extend(shlex.split(values.get("CMAKE_C_FLAGS", "")))
    if build_type:
        flags.extend(shlex.split(values.get(f"CMAKE_C_FLAGS_{build_type}", "")))
    flags.append("/std:c17" if msvc_style else "-std=c17")
    # Match the horizon test target's Debug optimization; sanitizer instrumentation stays on.
    if build_type == "DEBUG":
        flags.append("/O2" if msvc_style else "-O2")
    sanitizer = values.get("GABBABOY_ENABLE_SANITIZERS", "OFF").upper() in {"ON", "TRUE", "1"}
    if sanitizer:
        if msvc_style:
            raise HorizonCheckError("configured sanitizer build uses an unsupported MSVC frontend")
        flags.extend(["-fsanitize=address,undefined", "-fno-omit-frame-pointer"])
    identity = f"{compiler_id or 'unknown'} {compiler_value}"
    version_args = ["/Bv"] if msvc_style else ["--version"]
    version = run([*compiler, *version_args], timeout=10)
    if version.returncode == 0 and version.stdout.strip():
        identity += " | " + version.stdout.splitlines()[0]
    return compiler, flags, identity


def build_and_run(revision: str, base: Path, source_root: Path,
                  contents: dict[str, bytes], version: str,
                  mutant: Mutant, compiler: list[str], compiler_flags: list[str],
                  *, compile_timeout: float = 60.0) -> dict[str, object]:
    work = base / mutant.name
    core = contents["src/core/gabbaboy.c"].decode("utf-8")
    mutated_core = apply_mutant(core, mutant)
    mutated_bytes = mutated_core.encode("utf-8")
    mutated_source = work / "mutated-gabbaboy.c"
    mutated_source.parent.mkdir(parents=True, exist_ok=True)
    mutated_source.write_bytes(mutated_bytes)
    major, minor, patch = version.split(".")
    msvc_style = any(flag.startswith("/") and flag.lower().startswith("/std:")
                     for flag in compiler_flags)
    binary = work / ("horizon-mutant.exe" if msvc_style else "horizon-mutant")
    if msvc_style:
        defines = [
            f"/DGBB_STATE_RELEASE_MAJOR={major}",
            f"/DGBB_STATE_RELEASE_MINOR={minor}",
            f"/DGBB_STATE_RELEASE_PATCH={patch}",
            f'/DGBB_CORE_SOURCE_PATH=\\"{mutated_source}\\"',
        ]
        command = [*compiler, *compiler_flags, *defines,
                   f"/I{source_root / 'include'}", f"/I{source_root / 'src/core'}",
                   f"/Fe:{binary}", str(source_root / "tests/test_state_horizon.c")]
    else:
        command = [
            *compiler, *compiler_flags,
            f"-DGBB_STATE_RELEASE_MAJOR={major}",
            f"-DGBB_STATE_RELEASE_MINOR={minor}",
            f"-DGBB_STATE_RELEASE_PATCH={patch}",
            f'-DGBB_CORE_SOURCE_PATH="{mutated_source}"',
            "-I", str(source_root / "include"),
            "-I", str(source_root / "src/core"),
            str(source_root / "tests/test_state_horizon.c"),
            "-o", str(binary),
        ]
    build = run(command, cwd=source_root, timeout=compile_timeout)
    if build.returncode != 0 or not binary.is_file():
        raise HorizonCheckError(
            f"{mutant.name}: mutant compile failed and cannot count as a kill\n"
            f"{build.stdout}{build.stderr}"
        )
    semantic = run([str(binary), mutant.case], cwd=source_root, timeout=30)
    semantic_output = semantic.stdout + semantic.stderr
    check_semantic_rejection(semantic.returncode, semantic_output, mutant)
    control = run([str(binary), CONTROL_CASE], cwd=source_root, timeout=30)
    control_output = control.stdout + control.stderr
    if control.returncode != 0 or f"ok 1 - {CONTROL_CASE}" not in control_output:
        raise HorizonCheckError(
            f"{mutant.name}: unrelated {CONTROL_CASE} control failed\n{control_output}"
        )
    return {
        "name": mutant.name,
        "case": mutant.case,
        "input_sha256": {name: sha256_bytes(value) for name, value in contents.items()},
        "mutated_core_sha256": sha256_bytes(mutated_bytes),
        "binary_sha256": sha256_bytes(binary.read_bytes()),
        "compiler_command": compiler,
        "compiler_flags": compiler_flags,
        "semantic_exit_code": semantic.returncode,
        "semantic_witnesses": list(mutant.witnesses),
        "semantic_output_sha256": sha256_bytes(semantic_output.encode("utf-8")),
        "control_case": CONTROL_CASE,
        "control_exit_code": control.returncode,
        "control_output_sha256": sha256_bytes(control_output.encode("utf-8")),
    }


def execute(revision: str, build_dir: Path, *, self_test: bool) -> dict[str, object]:
    validate_mutant_inventory(MUTANTS)
    compiler, compiler_flags, compiler_identity = compiler_command(build_dir)
    selected = MUTANTS[:1] if self_test else MUTANTS
    results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="state-horizon-", dir=build_dir) as temp_name:
        temporary = Path(temp_name)
        source_root = temporary / "source"
        contents, version = materialize_sources(revision, source_root)
        for mutant in selected:
            result = build_and_run(revision, temporary, source_root, contents, version, mutant,
                                   compiler, compiler_flags)
            results.append(result)
    report: dict[str, object] = {
        "revision": revision,
        "compiler": compiler_identity,
        "compiler_flags": compiler_flags,
        "sanitizers_enabled": any("sanitize" in flag for flag in compiler_flags),
        "control_case": CONTROL_CASE,
        "mutants_expected": len(selected),
        "mutants_killed": len(results),
        "results": results,
    }
    output_path = build_dir / ("state_horizon_mutant_selftest.json" if self_test
                               else "state_horizon_mutants.json")
    temporary_report = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary_report, output_path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rev", required=True,
                        help="resolved immutable 40-hex implementation commit")
    parser.add_argument("--build-dir", required=True,
                        help="existing CMake build directory for compiler/sanitizer settings")
    parser.add_argument("--self-test", action="store_true",
                        help="test anchor/rejection checks and run one real witnessed mutant")
    args = parser.parse_args()
    try:
        revision = resolve_revision(args.rev)
        build_dir = Path(args.build_dir).resolve(strict=True)
        if not build_dir.is_dir():
            raise HorizonCheckError("--build-dir must name an existing directory")
        if args.self_test:
            self_test_helpers()
        report = execute(revision, build_dir, self_test=args.self_test)
    except HorizonCheckError as error:
        print(f"state-horizon check failed: {error}", file=sys.stderr)
        return 1
    label = "self-test" if args.self_test else "mutants"
    print(f"state_horizon_{label} pass revision={report['revision']} "
          f"killed={report['mutants_killed']}/{report['mutants_expected']} "
          f"control={CONTROL_CASE} sanitizer={str(report['sanitizers_enabled']).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
