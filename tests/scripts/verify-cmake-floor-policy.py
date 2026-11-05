#!/usr/bin/env python3
"""Keep the CMake-floor verifier's one full suite bound to the relocated install tree."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FLOOR_SCRIPT = ROOT / ".github/scripts/verify-cmake-floor.sh"
RELOCATED_CTEST = '"$ctest_bin" --test-dir "$repo_root/build-cmake-3.25.3-relocated"'
FULL_REPORT = ('--output-on-failure --no-tests=error --output-junit '
               '"$temp_root/relocated-tests.xml"')
INVENTORY_REPORT = ('"$temp_root/relocated-tests.xml" "$repo_root/tests/expected-tests.txt" '
                    '--installed')


class Reject(Exception):
    pass


def validate(text: str) -> None:
    if text.count("--output-junit") != 1 or RELOCATED_CTEST not in text or FULL_REPORT not in text:
        raise Reject("full-ctest-not-unique-relocated")
    full = text.find(RELOCATED_CTEST)
    report = text.find(FULL_REPORT)
    inventory = text.find(INVENTORY_REPORT)
    if inventory < 0 or not (full < report < inventory):
        raise Reject("relocated-inventory-not-verified")
    if "-R '^no_host_clock$' --no-tests=error -V" not in text:
        raise Reject("no-host-clock-result-missing")
    install = text.find('"$cmake_bin" --install "$repo_root/build-cmake-3.25.3"')
    move = text.find('mv "$stage" "$relocated"')
    relocated_configure = text.find('"$cmake_bin" --preset cmake-3.25.3-relocated')
    relocated_build = text.find('"$cmake_bin" --build "$repo_root/build-cmake-3.25.3-relocated"')
    if min(install, move, relocated_configure, relocated_build, full) < 0 or not (
        install < move < relocated_configure < relocated_build < full
    ):
        raise Reject("relocated-build-order-invalid")
    if "-R '^(cgb_samesuite_apu_membership|" not in text:
        raise Reject("floor-adapter-checks-missing")


def self_test(source: str) -> int:
    controls = 0
    try:
        validate(source)
    except Reject as error:
        raise Reject(f"baseline-rejected:{error}") from error
    controls += 1

    duplicated = source + '\n--output-junit "$temp_root/duplicate-tests.xml"\n'
    try:
        validate(duplicated)
    except Reject as error:
        if str(error) != "full-ctest-not-unique-relocated":
            raise Reject(f"duplicate-control-wrong-reason:{error}") from error
    else:
        raise Reject("duplicate-full-suite-accepted")
    controls += 1

    wrong_tree = source.replace(
        RELOCATED_CTEST,
        '"$ctest_bin" --test-dir "$repo_root/build-cmake-3.25.3"',
        1,
    )
    try:
        validate(wrong_tree)
    except Reject as error:
        if str(error) != "full-ctest-not-unique-relocated":
            raise Reject(f"wrong-tree-control-wrong-reason:{error}") from error
    else:
        raise Reject("preinstall-full-suite-accepted")
    controls += 1

    missing_inventory = source.replace(INVENTORY_REPORT, "", 1)
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
