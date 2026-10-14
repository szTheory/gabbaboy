---
phase: 12-cgb-double-speed
plan: 15
subsystem: testing
tags: [cgb, double-speed, fuzzing, libfuzzer, ctest]
requires:
  - phase: GB-12 plans 12-01 through 12-14
    provides: CGB speed switching, KEY1/STOP model behavior, measured stall handling, and the private speed-state test seam
provides:
  - Guest-driven CGB speed fuzz mode with exact master-clock and run-loop invariants
  - Eight deterministic CGB speed seeds with scenario-specific path proofs
  - KEY1 oracle inversion mutant/control and a speed-switch dictionary passed to both bounded-fuzz invocations
affects: [GB-12, CGB-06, fuzzing, CTest]
actuals:
  tokens: 7784
  tasks: 2
  commits: 2
plan_head_before: 2d11400d6a6379928e5bf8b06ef1611cbd1f0b4f
plan_head_after: a7d19c20514754024a886b16756365170a8d1843
tech-stack:
  added: []
  patterns:
    - Each fuzz seed executes a guest-authored STOP/KEY1 path and proves that the intended switch or non-switch outcome occurred.
    - Every shared run call checks monotonic master time, exact cumulative consumed half-dots, budget bounds, and CGB speed-state consistency.
key-files:
  created:
    - tests/fuzz/fuzz_core.dict
  modified:
    - src/core/gabbaboy.c
    - src/core/gabbaboy_test.h
    - tests/fuzz_core.c
    - tests/test_fuzz_core.c
    - tests/scripts/run-bounded-fuzz.sh
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - Keep all speed positives on the guest execution path; IE plus pending IF runs with IME disabled so the guest arms KEY1 and reaches STOP naturally.
  - Treat the CGB compatibility control as KEY1=$FF and use the DMG twin only for its STOP/wake non-switch result, since KEY1 is not a supported DMG guest register.
  - Read master time through a private, read-only test seam because instruction traces alone cannot establish clock equality inside a stall or STOP wait.
patterns-established:
  - Per-seed trace observations prove scenario entry and the exact expected switch count or non-switch state.
  - The inverted-oracle executable fails on speed seeds while its non-speed control remains green.
requirements-completed: [CGB-06]
coverage:
  - id: CGB-06-SPEED-FUZZ-PATHS
    description: Eight guest-driven speed seeds prove their intended switch, repeated-switch, pending-interrupt, button, DMA, LCD, compatibility, or DMG control path while checking every run call.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_fuzz_speed_regressions
        status: pass
      - kind: unit
        ref: fuzz_core_regressions
        status: pass
  - id: CGB-06-SPEED-ORACLE-NEGATIVE
    description: The inverted KEY1 oracle is detected on speed seeds and does not spuriously fail the non-speed control.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_fuzz_speed_oracle_mutant
        status: pass
      - kind: unit
        ref: cgb_fuzz_speed_oracle_mutant_control
        status: pass
  - id: CGB-06-SPEED-DICTIONARY
    description: The bounded-fuzz self-test verifies the speed-switch dictionary and its use by both fuzz invocations.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: other
        ref: bash tests/scripts/run-bounded-fuzz.sh --self-test
        status: pass
metrics:
  duration: 9min
  completed: 2026-10-13
status: complete
---

# Phase 12 Plan 15: CGB Speed Fuzz Coverage Summary

**Eight guest-driven CGB speed seeds now exercise KEY1/STOP invariants, exact master-time accounting, oracle inversion, and dictionary-assisted bounded fuzzing.**

## Performance

- **Duration:** 9 minutes from the recorded plan start at 2026-10-14T00:56:28Z; elapsed through final docs tracking.
- **Started:** 2026-10-14T00:56:28Z
- **Completed:** 2026-10-14T01:05:36Z
- **Tasks:** 2
- **Files modified:** 8 code and test files

## Accomplishments

- Added a CGB-only `cgb_speed` fuzz selector with a dedicated 600,000-half-dot cap while preserving the existing run and input limits.
- Added eight guest-program seeds. Each proves that it reached the expected switch or control state, checks invariants after every `gbb_run`, and equates the master-clock delta to the exact sum of consumed half-dots.
- Added the inverted KEY1-oracle failure/control pair, a speed-switch dictionary, and self-test checks that both bounded fuzz invocations use it.

## Task Commits

1. **Task 1: Tracer — fuzz speed mode with invariants and an arm-and-switch guest seed** — `4172be6` (test)
2. **Task 2: Seven more seeds, inverted-oracle control, dictionary, and bounded-fuzz wiring** — `a7d19c2` (test)

## Files Created/Modified

- `tests/fuzz/fuzz_core.dict` — libFuzzer tokens for KEY1 arm, STOP, and arm-switch sequences.
- `src/core/gabbaboy.c`, `src/core/gabbaboy_test.h` — private read-only master-time accessor for exact test observations.
- `tests/fuzz_core.c`, `tests/test_fuzz_core.c` — fuzz mode, run invariants, scenario seeds, and oracle controls.
- `tests/scripts/run-bounded-fuzz.sh` — dictionary checks and `-dict=` arguments for both fuzz modes.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — regression, mutant/control, and inventory registration.

## Decisions Made

- A pre-enabled IME would dispatch a pending interrupt before STOP, so the pending-IF seed keeps IME disabled and verifies the guest's natural switch path.
- CGB compatibility mode must not switch and exposes KEY1 as `$FF`; the DMG control proves STOP/wake behavior without treating KEY1 as a supported DMG register.
- Master-time equality is checked directly on every shared run call. Trace monotonicity remains supplementary because a CPU trace cannot reveal time spent wholly inside stall or STOP waits.

## Deviations from Plan

**1. Added a private master-time read seam to make the planned invariant directly observable.**

- **Found during:** Task 1, when establishing exact consumed-time equality across stall and STOP-only calls.
- **Issue:** Instruction trace monotonicity does not prove exact master-time equality when a call makes no instruction progress.
- **Fix:** Added a read-only accessor in the private test interface and checked the clock delta against cumulative `gbb_run` consumption after every call.
- **Files modified:** `src/core/gabbaboy.c`, `src/core/gabbaboy_test.h`, `tests/fuzz_core.c`.
- **Verification:** Focused speed regressions and the full CTest suite passed.
- **Commit:** `4172be6`.

## TDD Evidence

Task 2 is marked `tdd="true"`, but its scope adds tests for behavior already present in the core and does not change emulator behavior. A conventional production-code RED/GREEN cycle would have required an artificial core defect. The tests instead include a meaningful negative control: the inverted KEY1 oracle fails on the speed seeds, while the same mutant executable passes its non-speed control. Both commits are test-only; no production behavior was changed.

## Validation Evidence

- `cmake --preset phase1 && cmake --build --preset phase1 -j8` — passed.
- `ctest --test-dir build -R '^(cgb_fuzz_speed_|fuzz_core_regressions$)' --output-on-failure --no-tests=error` — 4/4 passed.
- `bash tests/scripts/run-bounded-fuzz.sh --self-test` — passed; the script reports that a libFuzzer runtime is unavailable in this environment, so deterministic regressions remain the exercised fuzz evidence.
- `ctest --test-dir build --output-on-failure --no-tests=error -j8` — 856/856 passed.
- `ctest --test-dir build -R '^summary_coverage$' --output-on-failure --no-tests=error` — passed with the new structured coverage block.
- `git diff --check` — passed before the task commits.

## Issues Encountered

The installed environment lacks an executable libFuzzer runtime. The bounded-fuzz harness self-test and all deterministic guest-seed tests passed; no libFuzzer campaign is claimed.

## User Setup Required

None.

## Next Phase Readiness

Plan 12-15 is complete; Phase 12 remains in progress. Next is **GB-12 plan 12-16 — measured AGE verdicts and fixture digest guards**. Continue with **`/gsd-execute-phase 12`**, which resumes from the next incomplete plan. Phase 13 — CGB HDMA has not started; stop after Phase 12 for the owner’s direction.

---
*Phase: 12-cgb-double-speed*
*Completed: 2026-10-13*

## Self-Check: PASSED

- Task commits `4172be6` and `a7d19c2` are ancestors of the pinned branch HEAD.
- All created fuzz artifacts are tracked in the two task commits.
- The fresh focused and full-suite results recorded above passed.
- The `summary_coverage` CTest accepted the coverage schema.
