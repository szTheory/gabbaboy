#!/usr/bin/env python3
"""Keep the CMake-floor verifier's one full suite bound to the relocated install tree."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FLOOR_SCRIPT = ROOT / ".github/scripts/verify-cmake-floor.sh"
CTEST_PREFIX = '"$ctest_bin" --test-dir '
FLOOR_VERSION_ASSIGNMENT = "readonly version=3.25.3"
CMAKE_BIN_ASSIGNMENT = 'cmake_bin="$temp_root/cmake-${version}-linux-x86_64/bin/cmake"'
CTEST_BIN_ASSIGNMENT = 'ctest_bin="$temp_root/cmake-${version}-linux-x86_64/bin/ctest"'
INVENTORY_PREFIX = 'bash "$repo_root/.github/scripts/verify-test-inventory.sh"'
BASE_BUILD = '"$repo_root/build-cmake-3.25.3"'
RELOCATED_BUILD = '"$repo_root/build-cmake-3.25.3-relocated"'
ADAPTER_SELECTOR = (
    "-R '^(cgb_samesuite_apu_membership|cgb_samesuite_apu_controls|cgb_corpus_report_tracer|"
    "cgb_corpus_report_tracer_controls|cgb_corpus_report_controls|cgb_corpus_report_platform_controls)$'"
)
NO_HOST_CLOCK_SELECTOR = "-R '^no_host_clock$'"
CTEST_FILTER_OPTION = re.compile(
    r"(?:^|\s)(?:-R|-E|-L|-LE|-FA|-FS|-FC|-I|-U|--tests-regex|--exclude-regex|"
    r"--label-regex|--label-exclude|--fixture-exclude-any|--fixture-exclude-setup|"
    r"--fixture-exclude-cleanup|--tests-information|--tests-from-file|--exclude-from-file|"
    r"--rerun-failed|--union)(?:\s|=|$)"
)
INSTALL_PREFIX = '"$cmake_bin" --install '
MOVE_PREFIX = 'mv "$stage" "$relocated"'
RELOCATED_CONFIGURE_PREFIX = '"$cmake_bin" --preset cmake-3.25.3-relocated'
RELOCATED_BUILD_PREFIX = f'"$cmake_bin" --build {RELOCATED_BUILD}'
FULL_REPORT = (
    '--output-on-failure --no-tests=error --output-junit "$temp_root/relocated-tests.xml"'
)
FULL_CTEST_COMMAND = (
    '"$ctest_bin" --test-dir "$repo_root/build-cmake-3.25.3-relocated" \\\n'
    '  --output-on-failure --no-tests=error --output-junit "$temp_root/relocated-tests.xml"'
)
INVENTORY_REPORT = (
    '"$temp_root/relocated-tests.xml" "$repo_root/tests/expected-tests.txt" --installed'
)


class Reject(Exception):
    pass


def active_commands(text: str, prefix: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    commands: list[tuple[int, str]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.lstrip().startswith("#") and line.lstrip().startswith(prefix):
            start = index
            parts = [line]
            while parts[-1].rstrip().endswith("\\") and index + 1 < len(lines):
                index += 1
                parts.append(lines[index])
            commands.append((start, "\n".join(parts)))
        index += 1
    return commands


def active_occurrences(text: str, prefix: str) -> int:
    return sum(
        line.count(prefix) for line in text.splitlines()
        if not line.lstrip().startswith("#")
    )


def active_word_occurrences(text: str, word: str) -> int:
    return sum(
        len(re.findall(rf"\b{re.escape(word)}\b", line))
        for line in text.splitlines()
        if not line.lstrip().startswith("#")
    )


def commented_out(text: str, command: str) -> str:
    replacement = "\n".join("# " + line for line in command.splitlines())
    return text.replace(command, replacement, 1)


def validate(text: str) -> None:
    if any(
        active_occurrences(text, assignment) != 1
        for assignment in (
            FLOOR_VERSION_ASSIGNMENT,
            CMAKE_BIN_ASSIGNMENT,
            CTEST_BIN_ASSIGNMENT,
        )
    ):
        raise Reject("floor-toolchain-not-pinned")
    if any(
        active_occurrences(text, assignment) != 1
        for assignment in ("readonly version=", "cmake_bin=", "ctest_bin=")
    ):
        raise Reject("floor-toolchain-not-pinned")
    ctest_calls = active_commands(text, CTEST_PREFIX)
    if (
        active_occurrences(text, CTEST_PREFIX) != len(ctest_calls)
        or active_occurrences(text, "--test-dir") != len(ctest_calls)
    ):
        raise Reject("full-ctest-not-unique-relocated")
    full_calls = [
        (line, call) for line, call in ctest_calls
        if not CTEST_FILTER_OPTION.search(call)
    ]
    if (
        len(full_calls) != 1
        or BASE_BUILD in full_calls[0][1]
        or RELOCATED_BUILD not in full_calls[0][1]
        or full_calls[0][1].count("--output-junit") != 1
        or FULL_REPORT not in full_calls[0][1]
        or full_calls[0][1] != FULL_CTEST_COMMAND
    ):
        raise Reject("full-ctest-not-unique-relocated")
    adapter_calls = [call for _, call in ctest_calls if ADAPTER_SELECTOR in call]
    if len(adapter_calls) != 1 or BASE_BUILD not in adapter_calls[0] or RELOCATED_BUILD in adapter_calls[0]:
        raise Reject("floor-adapter-checks-missing")
    no_host_clock_calls = [call for _, call in ctest_calls if NO_HOST_CLOCK_SELECTOR in call]
    if (
        len(no_host_clock_calls) != 1
        or BASE_BUILD not in no_host_clock_calls[0]
        or RELOCATED_BUILD in no_host_clock_calls[0]
    ):
        raise Reject("no-host-clock-result-missing")
    inventory_calls = active_commands(text, INVENTORY_PREFIX)
    if active_occurrences(text, INVENTORY_PREFIX) != len(inventory_calls):
        raise Reject("relocated-inventory-not-verified")
    installed_inventories = [
        (line, call) for line, call in inventory_calls
        if INVENTORY_REPORT in call
    ]
    full_line = full_calls[0][0]
    if (
        len(inventory_calls) != 1
        or len(installed_inventories) != 1
        or full_line >= installed_inventories[0][0]
    ):
        raise Reject("relocated-inventory-not-verified")
    install_calls = active_commands(text, INSTALL_PREFIX)
    move_calls = active_commands(text, MOVE_PREFIX)
    relocated_configure_calls = active_commands(text, RELOCATED_CONFIGURE_PREFIX)
    relocated_build_calls = active_commands(text, RELOCATED_BUILD_PREFIX)
    if any((
        active_occurrences(text, prefix) != len(calls)
        for prefix, calls in (
            (INSTALL_PREFIX, install_calls),
            (MOVE_PREFIX, move_calls),
            (RELOCATED_CONFIGURE_PREFIX, relocated_configure_calls),
            (RELOCATED_BUILD_PREFIX, relocated_build_calls),
        )
    )):
        raise Reject("relocated-build-order-invalid")
    if (
        len(install_calls) != 1
        or len(move_calls) != 1
        or len(relocated_configure_calls) != 1
        or len(relocated_build_calls) != 1
        or BASE_BUILD not in install_calls[0][1]
        or not (
            install_calls[0][0]
            < move_calls[0][0]
            < relocated_configure_calls[0][0]
            < relocated_build_calls[0][0]
            < full_line
        )
    ):
        raise Reject("relocated-build-order-invalid")
    if "-R '^no_host_clock$' --no-tests=error -V" not in no_host_clock_calls[0]:
        raise Reject("no-host-clock-result-missing")
    if len(ctest_calls) != 3:
        raise Reject("full-ctest-not-unique-relocated")
    if active_occurrences(text, "ctest_bin") != 5 or active_word_occurrences(text, "ctest") != 2:
        raise Reject("full-ctest-not-unique-relocated")


def self_test(source: str) -> int:
    controls = 0
    try:
        validate(source)
    except Reject as error:
        raise Reject(f"baseline-rejected:{error}") from error
    controls += 1

    for label, assignment, replacement in (
        ("floor version", FLOOR_VERSION_ASSIGNMENT, "readonly version=3.26.0"),
        ("cmake binary", CMAKE_BIN_ASSIGNMENT, 'cmake_bin="/usr/bin/cmake"'),
        ("ctest binary", CTEST_BIN_ASSIGNMENT, 'ctest_bin="/usr/bin/ctest"'),
    ):
        unpinned = source.replace(assignment, replacement, 1)
        try:
            validate(unpinned)
        except Reject as error:
            if str(error) != "floor-toolchain-not-pinned":
                raise Reject(f"{label}-control-wrong-reason:{error}") from error
        else:
            raise Reject(f"unpinned-{label}-accepted")
        controls += 1

    for label, duplicate in (
        ("cmake", 'cmake_bin="/usr/bin/cmake"'),
        ("ctest", 'ctest_bin="/usr/bin/ctest"'),
        ("version", "readonly version=3.25.3"),
    ):
        reassigned = source + "\n" + duplicate + "\n"
        try:
            validate(reassigned)
        except Reject as error:
            if str(error) != "floor-toolchain-not-pinned":
                raise Reject(f"duplicate-{label}-assignment-control-wrong-reason:{error}") from error
        else:
            raise Reject(f"duplicate-{label}-assignment-accepted")
        controls += 1

    for build in ("build-cmake-3.25.3", "build-cmake-3.25.3-relocated"):
        duplicate = (
            source + '\n"$ctest_bin" --test-dir "$repo_root/' + build + '" '
            + chr(92) + "\n  --no-tests=error --output-on-failure\n"
        )
        try:
            validate(duplicate)
        except Reject as error:
            if str(error) != "full-ctest-not-unique-relocated":
                raise Reject(f"duplicate-control-wrong-reason:{error}") from error
        else:
            raise Reject(f"duplicate-full-suite-accepted:{build}")
        controls += 1

    indented_duplicate = (
        source + '\n  ' + CTEST_PREFIX + RELOCATED_BUILD + ' ' + chr(92)
        + '\n    --no-tests=error --output-on-failure\n'
    )
    try:
        validate(indented_duplicate)
    except Reject as error:
        if str(error) != "full-ctest-not-unique-relocated":
            raise Reject(f"indented-duplicate-control-wrong-reason:{error}") from error
    else:
        raise Reject("indented-duplicate-full-suite-accepted")
    controls += 1

    inline_duplicate = source + '\n; ' + CTEST_PREFIX + RELOCATED_BUILD + ' --no-tests=error\n'
    try:
        validate(inline_duplicate)
    except Reject as error:
        if str(error) != "full-ctest-not-unique-relocated":
            raise Reject(f"inline-duplicate-control-wrong-reason:{error}") from error
    else:
        raise Reject("inline-duplicate-full-suite-accepted")
    controls += 1

    braced_duplicate = (
        source + '\n"${ctest_bin}" --test-dir "$repo_root/build-cmake-3.25.3-relocated" '
        '--no-tests=error\n'
    )
    try:
        validate(braced_duplicate)
    except Reject as error:
        if str(error) != "full-ctest-not-unique-relocated":
            raise Reject(f"braced-duplicate-control-wrong-reason:{error}") from error
    else:
        raise Reject("braced-duplicate-full-suite-accepted")
    controls += 1

    filtered_duplicate = (
        source + '\n"$ctest_bin" --test-dir "$repo_root/build-cmake-3.25.3-relocated" '
        "-R '.*' --no-tests=error --output-on-failure\n"
    )
    try:
        validate(filtered_duplicate)
    except Reject as error:
        if str(error) != "full-ctest-not-unique-relocated":
            raise Reject(f"filtered-duplicate-control-wrong-reason:{error}") from error
    else:
        raise Reject("filtered-full-inventory-accepted")
    controls += 1

    cwd_duplicate = (
        source + '\n(cd "$repo_root/build-cmake-3.25.3-relocated" && '
        '"$ctest_bin" --no-tests=error --output-on-failure)\n'
    )
    try:
        validate(cwd_duplicate)
    except Reject as error:
        if str(error) != "full-ctest-not-unique-relocated":
            raise Reject(f"cwd-duplicate-control-wrong-reason:{error}") from error
    else:
        raise Reject("cwd-full-inventory-accepted")
    controls += 1

    bare_ctest_duplicate = (
        source + '\n(cd "$repo_root/build-cmake-3.25.3-relocated" && '
        'ctest --no-tests=error --output-on-failure)\n'
    )
    try:
        validate(bare_ctest_duplicate)
    except Reject as error:
        if str(error) != "full-ctest-not-unique-relocated":
            raise Reject(f"bare-ctest-control-wrong-reason:{error}") from error
    else:
        raise Reject("bare-ctest-full-inventory-accepted")
    controls += 1

    full_prefix = '"$ctest_bin" --test-dir "$repo_root/build-cmake-3.25.3-relocated" \\\n'
    for selector in (
        "-R '^acceptance_'",
        "-E '^ignored_'",
        "-L unit",
        "-LE flaky",
        "-FA fixture",
        "-FS fixture",
        "-FC fixture",
        "--fixture-exclude-any fixture",
        "--fixture-exclude-setup fixture",
        "--fixture-exclude-cleanup fixture",
        "-I 1,10",
        "--tests-information 1,10",
        "-U",
        "--union",
        "--tests-regex '^acceptance_'",
        "--exclude-regex '^ignored_'",
        "--label-regex unit",
        "--label-exclude flaky",
        "--tests-from-file selected-tests.txt",
        "--exclude-from-file excluded-tests.txt",
        "--rerun-failed",
        "--preset restricted",
        "--presets-file restricted-presets.json",
        "--show-only",
    ):
        filtered_primary = source.replace(
            full_prefix,
            full_prefix[:-2] + selector + " \\\n",
            1,
        )
        try:
            validate(filtered_primary)
        except Reject as error:
            if str(error) != "full-ctest-not-unique-relocated":
                raise Reject(f"filtered-primary-control-wrong-reason:{selector}:{error}") from error
        else:
            raise Reject(f"filtered-primary-full-inventory-accepted:{selector}")
        controls += 1

    full_call = next(call for _, call in active_commands(source, CTEST_PREFIX) if FULL_REPORT in call)
    clock_call = next(
        call for _, call in active_commands(source, CTEST_PREFIX)
        if NO_HOST_CLOCK_SELECTOR in call
    )
    adapter_call = next(
        call for _, call in active_commands(source, CTEST_PREFIX)
        if ADAPTER_SELECTOR in call
    )
    for label, command, reason in (
        ("relocated full suite", full_call, "full-ctest-not-unique-relocated"),
        ("base adapter checks", adapter_call, "floor-adapter-checks-missing"),
        ("base clock check", clock_call, "no-host-clock-result-missing"),
    ):
        try:
            validate(commented_out(source, command))
        except Reject as error:
            if str(error) != reason:
                raise Reject(f"commented-{label}-control-wrong-reason:{error}") from error
        else:
            raise Reject(f"commented-{label}-accepted")
        controls += 1

    for label, prefix in (
        ("install", INSTALL_PREFIX),
        ("relocation move", MOVE_PREFIX),
        ("relocated configure", RELOCATED_CONFIGURE_PREFIX),
        ("relocated build", RELOCATED_BUILD_PREFIX),
    ):
        command = next(call for _, call in active_commands(source, prefix))
        try:
            validate(commented_out(source, command))
        except Reject as error:
            if str(error) != "relocated-build-order-invalid":
                raise Reject(f"commented-{label}-control-wrong-reason:{error}") from error
        else:
            raise Reject(f"commented-{label}-accepted")
        controls += 1

    missing_inventory = commented_out(source, next(
        call for _, call in active_commands(source, INVENTORY_PREFIX)
        if INVENTORY_REPORT in call
    ))
    try:
        validate(missing_inventory)
    except Reject as error:
        if str(error) != "relocated-inventory-not-verified":
            raise Reject(f"inventory-control-wrong-reason:{error}") from error
    else:
        raise Reject("missing-relocated-inventory-accepted")
    controls += 1
    print(f"cmake-floor policy pass full-suite=relocated installed-inventory=ok controls={controls}")
    return 0


def main() -> int:
    if not __debug__ or sys.flags.optimize:
        print("verify-cmake-floor-policy must not run with python -O", file=sys.stderr)
        return 2
    try:
        source = FLOOR_SCRIPT.read_text(encoding="utf-8")
        if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
            return self_test(source)
        if len(sys.argv) != 1:
            print("Usage: verify-cmake-floor-policy.py [--self-test]", file=sys.stderr)
            return 2
        validate(source)
    except (OSError, Reject) as error:
        print(f"verify-cmake-floor-policy fail: {error}", file=sys.stderr)
        return 1
    print("cmake-floor policy pass full-suite=relocated installed-inventory=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
