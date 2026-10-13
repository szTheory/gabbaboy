---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 03
subsystem: runner
tags: [runner, profile, model-mapping, cgb, dmg, byte-identity, ctest]
requires: ["10-02"]
provides:
  - "gbb_runner_profile_for_model, gbb_runner_profile_label, gbb_runner_model_for_option (src/runner/acceptance.c, declared in acceptance.h)"
  - "Runner flag --profile dmg|cgb in manifest and acceptance modes; reasons unknown-profile, profile-model-conflict, create-failed"
  - "tests/runner_profile_identity.cmake and seven cgb_runner_profile_* CTests"
affects: [10-05, 10-06]
tech-stack:
  added: []
  patterns: ["single model<->profile mapping drives create calls and printed labels", "byte-identity comparison with a negative control"]
key-files:
  created:
    - tests/runner_profile_identity.cmake
  modified:
    - src/runner/main.c
    - src/runner/acceptance.c
    - src/runner/acceptance.h
    - tests/test_runner.c
    - tests/verify_runner_help.cmake
    - tests/acceptance/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "Runner-local GBB_RUNNER_PROFILE_CGB = (gbb_profile)2 until Plan 10-05 adds the public enum (D-01); the core still rejects it, and the runner reports create-failed rather than falling back to DMG"
  - "A CGB manifest request prints one 'mooneye.<alias> status=excluded reason=unsupported-model profile=CGB-CPU-E' line per case and exits 4, before any ROM is loaded"
  - "The new CTests use expect_exit.cmake (exact exit code plus forbid regex) instead of a bare PASS_REGULAR_EXPRESSION so exit 4 and exit 2 are asserted"
requirements-completed: [CGB-01]
duration: 35 min
completed: 2026-10-12
status: complete
commits: 2
plan_head_before: 9303c345ea6ea79fb10ffa0628d87ef7e58df042
plan_head_after: af1179529f0dae037551cb80c8f410238fe4de91
actuals:
  tokens: 30000
  tasks: 2
  commits: 2
coverage:
  - deliverable: "One mapping drives every runner create call and label; CGB requests are excluded under a CGB label and never carry a DMG label"
    human_judgment: false
    verification:
      - kind: ctest
        ref: "cgb_runner_profile_manifest_cgb_excluded, cgb_runner_profile_acceptance_cgb_excluded, cgb_runner_profile_unknown, cgb_runner_profile_model_conflict"
        status: pass
  - deliverable: "DMG runner output is byte-identical with and without --profile dmg"
    human_judgment: false
    verification:
      - kind: ctest
        ref: "cgb_runner_profile_dmg_identity_mooneye, cgb_runner_profile_dmg_identity_acceptance, cgb_runner_profile_dmg_identity_negative"
        status: pass
      - kind: command
        ref: "bash tests/scripts/verify-dmg-baseline.sh (baseline status=pass)"
        status: pass
---

# Phase 10 Plan 03: Runner Model-Profile Mapping Summary

The runner now has one model<->profile mapping (dmg-cpu-b/DMG-CPU-B and cgb-cpu-e/CGB-CPU-E) behind a new `--profile dmg|cgb` option, with the acceptance-mode `unsupported-profile` rejection removed and DMG output unchanged byte for byte.

## Accomplishments

- Mapping functions `gbb_runner_profile_for_model`, `gbb_runner_profile_label`, `gbb_runner_model_for_option` are defined once in `src/runner/acceptance.c`. Every create call (`run_guest`, `observe_case`, `run_original_tracer`, the three acceptance sites and the diagnostic replay) and every `profile=` / `model=` label in `main.c` and `acceptance.c` goes through them. `GBB_PROFILE_DMG_CPU_B` appears once outside the header, inside the mapping.
- `--profile` is parsed before the acceptance dispatch. Unknown values exit 2 with `reason=unknown-profile`; a `--profile`/`--model` disagreement exits 2 with `reason=profile-model-conflict`. `--model` keeps working in acceptance mode through the same mapping.
- A CGB manifest request prints `mooneye.<alias> status=excluded reason=unsupported-model profile=CGB-CPU-E` per case and exits 4 without loading a ROM.
- Acceptance mode no longer rejects non-DMG models; the applicability check still runs first (`acceptance_libbet_excluded_cgb-cpu-e` unchanged). A model the core cannot create yet prints `status=unsupported reason=create-failed model=<model>` and exits 3.
- Help text and `runner_help` updated for the new option.

## Task Commits

1. Task 1 (tracer): `a92be5c` feat(10-03) mapping, `--profile`, labels, create sites, acceptance rejection removal. The tracer verify (existing `runner_`, `mooneye_case_`, `acceptance_` tests plus CGB-excluded) passed before expansion.
2. Task 2: `af11795` test(10-03) `cgb_runner_profile_*` CTests, `tests/runner_profile_identity.cmake`, inventory entries.

## Verification

- `ctest --preset phase1 --no-tests=error -j4`: 426/426 passed (includes seven new cgb_runner_profile_* tests).
- `bash tests/scripts/verify-dmg-baseline.sh`: `baseline status=pass`.
- Acceptance criteria: `GBB_PROFILE_DMG_CPU_B` count 0 (main.c) + 1 (acceptance.c); `model=dmg-cpu-b` count 0; `reason=unsupported-profile` count 0; `git diff --quiet main -- tests/baseline` exits 0; the three required inventory names present.

## Deviations from Plan

**1. [Rule 3 - Blocker] tests/test_runner.c call sites**
- **Found during:** Task 1 build
- **Issue:** `tests/test_runner.c` includes `main.c` and calls `run_guest`, whose signature gained a profile argument.
- **Fix:** Passed `GBB_RUNNER_PROFILE_DMG` at the three call sites.
- **Files modified:** tests/test_runner.c
- **Commit:** a92be5c

**2. [Rule 2 - Missing control] identity negative control**
- Added `cgb_runner_profile_dmg_identity_negative` (baseline run is a CGB-excluded case, so the comparison script must fail), so the identity check cannot pass vacuously. Registered in `tests/expected-tests.txt`. Commit af11795.

**3. Test mechanism**
- The CGB-excluded tests assert the exact exit code through `expect_exit.cmake` with a forbid regex rather than only `PASS_REGULAR_EXPRESSION`/`FAIL_REGULAR_EXPRESSION`, because a regex-only CTest would also pass on a wrong exit code. All tests live in `tests/acceptance/CMakeLists.txt` (which already owns `gbb_add_acceptance_exit`) rather than `tests/CMakeLists.txt`; the TIMEOUT 30 is set per test.
- Task 1/Task 2 commits split by file (source vs tests) rather than strictly by tracer scope, because the acceptance.c mapping and label edits are interdependent.

**Total deviations:** 2 auto-fixed, 2 mechanism notes. **Impact:** none on behaviour.

## Known Stubs

None. One reachable-only-on-CGB item is deferred by design: the frame-capture branch that would print not-applicable when `gbb_copy_frame` returns `GBB_UNSUPPORTED_PROFILE` was not added, because the core cannot create a CGB instance (create fails first with `create-failed`) and `gbb_copy_frame` has no such return today. It lands with D-05 in Plan 10-06.

## Self-Check: PASSED

- tests/runner_profile_identity.cmake: FOUND
- Commits a92be5c and af11795: FOUND in HEAD history
- Full ctest 426/426 and baseline status=pass re-run after the final edits.
