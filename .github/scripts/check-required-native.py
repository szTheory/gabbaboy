#!/usr/bin/env python3
"""Judge the `required-native` aggregator verdict from the classification and every job result (D-21).

The ci.yml aggregator passes this script the classifier output (KIND) and each needed job's result through
environment variables. The rules fail toward the full matrix:

  kind=planning  `changes` and `planning-checks` succeeded and every heavy job is exactly `skipped`.
  anything else  (kind=full, empty, unknown) is treated as full: `changes` succeeded, every heavy job except
                 macos-player-package succeeded and `planning-checks` was skipped. macos-player-package is judged
                 by check-player-result.sh, which knows whether the player evidence was required.

Prints one verdict line and exits 1 on rejection. `--self-test` drives the rules through the CLI.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

# environment variable -> job it carries the result of
HEAVY = {
    "NATIVE_LINUX": "native-linux",
    "NATIVE_MACOS": "native-macos",
    "NATIVE_WINDOWS": "native-windows",
    "LINUX_SANITIZERS": "linux-sanitizers",
    "LINUX_SANITIZER_TESTS": "linux-sanitizers-tests",
    "LINUX_SANITIZER_ACCEPTANCE": "linux-sanitizers-acceptance",
    "CMAKE_FLOOR": "cmake-floor-3-25-3",
    "PERF_GATE": "perf-gate",
    "PLAYER_GATE": "player-gate",
}
# Judged in the planning branch only; the full branch hands it to check-player-result.sh.
PLAYER_PACKAGE = ("PLAYER_RESULT", "macos-player-package")


def judge(env: dict[str, str]) -> tuple[bool, str]:
    kind = env.get("KIND", "")
    changes = env.get("CHANGES", "")
    planning_checks = env.get("PLANNING_CHECKS", "")
    if changes != "success":
        return False, f"REJECT changes job result is '{changes}', not success"
    if kind == "planning":
        if planning_checks != "success":
            return False, f"REJECT kind=planning but planning-checks result is '{planning_checks}', not success"
        for var, job in (*HEAVY.items(), PLAYER_PACKAGE):
            result = env.get(var, "")
            if result != "skipped":
                return False, f"REJECT kind=planning but heavy job {job} result is '{result}', not skipped"
        return True, "required-native pass kind=planning"
    # Full is the default for any other value, so a classifier that printed something unexpected can only add work.
    shown = kind or "<empty>"
    if planning_checks != "skipped":
        return False, f"REJECT kind={shown} (full) but planning-checks result is '{planning_checks}', not skipped"
    for var, job in HEAVY.items():
        result = env.get(var, "")
        if result != "success":
            return False, f"REJECT kind={shown} (full) but required job {job} result is '{result}', not success"
    return True, "required-native pass kind=full"


def self_test() -> int:
    full = {"KIND": "full", "CHANGES": "success", "PLANNING_CHECKS": "skipped", "PLAYER_RESULT": "skipped",
            **{var: "success" for var in HEAVY}}
    planning = {"KIND": "planning", "CHANGES": "success", "PLANNING_CHECKS": "success", "PLAYER_RESULT": "skipped",
                **{var: "skipped" for var in HEAVY}}

    def variant(base: dict[str, str], **changes: str) -> dict[str, str]:
        return {**base, **changes}

    cases = [
        ("full, every heavy job succeeded", full, True),
        ("full, macos-player-package succeeded too", variant(full, PLAYER_RESULT="success"), True),
        ("full, one heavy job skipped", variant(full, PERF_GATE="skipped"), False),
        ("full, one heavy job failed", variant(full, NATIVE_WINDOWS="failure"), False),
        ("full, one heavy job cancelled", variant(full, LINUX_SANITIZERS="cancelled"), False),
        ("full, planning-checks ran", variant(full, PLANNING_CHECKS="success"), False),
        ("full, changes failed", variant(full, CHANGES="failure"), False),
        ("full, changes skipped", variant(full, CHANGES="skipped"), False),
        ("planning, every heavy job skipped", planning, True),
        ("planning, one heavy job succeeded", variant(planning, NATIVE_LINUX="success"), False),
        ("planning, macos-player-package ran", variant(planning, PLAYER_RESULT="success"), False),
        ("planning, planning-checks failed", variant(planning, PLANNING_CHECKS="failure"), False),
        ("planning, planning-checks skipped", variant(planning, PLANNING_CHECKS="skipped"), False),
        ("planning, changes failed", variant(planning, CHANGES="failure"), False),
        ("unknown kind with a full-success run is full", variant(full, KIND="surprise"), True),
        ("empty kind with a full-success run is full", variant(full, KIND=""), True),
        ("unknown kind with skipped heavy jobs is rejected", variant(planning, KIND="surprise"), False),
        ("unknown kind with planning-checks success is rejected", variant(full, KIND="Planning", PLANNING_CHECKS="success"), False),
        ("a missing result is not success", {k: v for k, v in full.items() if k != "CMAKE_FLOOR"}, False),
    ]
    controls = 0
    for label, env, want_pass in cases:
        # Through the CLI with a scrubbed environment, so the exit status and verdict line are what the workflow sees.
        child_env = {key: value for key, value in os.environ.items() if key in ("PATH", "SYSTEMROOT")}
        child_env.update(env)
        result = subprocess.run([sys.executable, "-I", os.path.abspath(__file__)], capture_output=True, text=True,
                                check=False, env=child_env, timeout=30)
        output = (result.stdout + result.stderr).strip()
        passed = result.returncode == 0 and output.startswith("required-native pass")
        rejected = result.returncode == 1 and output.startswith("REJECT")
        if want_pass != passed or want_pass == rejected:
            raise SystemExit(f"required-native self-test: {label}: exit={result.returncode} output={output!r}")
        controls += 1
    print(f"required-native self-test pass controls={controls}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if sys.flags.optimize:
        print("check-required-native: refusing to run under python -O", file=sys.stderr)
        return 2
    if args.self_test:
        return self_test()
    ok, line = judge(dict(os.environ))
    print(line, file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
