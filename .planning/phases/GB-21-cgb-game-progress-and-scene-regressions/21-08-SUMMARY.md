---
phase: GB-21-cgb-game-progress-and-scene-regressions
plan: "08"
subsystem: testing
tags: [CGB, candidate replay, build qualification, RGB555, PCM]
requires:
  - phase: GB-21-cgb-game-progress-and-scene-regressions
    provides: Ordered candidate admission and original native-CGB harness evidence from Plans 21-01 through 21-07.
provides:
  - Separate immutable historical provenance and independently qualified current CMake runner identity.
  - Exact replay binding for supported aggregate RGB555 and PCM observations.
affects: [Phase 21 final qualification, verify-work closure]
actuals:
  tokens: 21997.25
  tasks: 2
  commits: 9
tech-stack:
  added: []
  patterns:
    - Qualify the exact normal CMake target with a test-only receipt while keeping non-test builds Python-free.
    - Compare fresh aggregate observations exactly against immutable admitted evidence after Phase 20 admission.
key-files:
  created:
    - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-08-SUMMARY.md
  modified:
    - CMakeLists.txt
    - tests/scripts/verify-cgb-candidates.py
    - tests/scripts/verify-cgb-game-evidence.py
    - tests/cmake/game-evidence.cmake
    - docs/cgb-game-candidates.md
    - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-VALIDATION.md
    - .planning/ROADMAP.md
key-decisions:
  - "Historical runner hashes and source IDs stay immutable; current build authority comes only from the trusted CMake target and its separate qualification receipt."
  - "Admitted replay binds the complete supported aggregate RGB555/PCM observation; unsupported per-checkpoint PCM is not inferred."
  - "Actual game records remain no-go and were not changed or executed; synthetic controls establish reproducibility contract behavior only."
patterns-established:
  - "Keep historical receipt validation independent from current working-checker source matching."
  - "Route valid-but-changed outputs through the admitted replay entry point and assert the precise observation mismatch."
requirements-completed: [GAME-02]
coverage:
  - id: D1
    description: The canonical CMake-built runner qualification binds the exact 24 build inputs, including state-version parsing and the borrowed acceptance-input header; dirty changes to either are rejected before candidate execution, and BUILD_TESTING=OFF remains Python-free.
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission_(contract|controls)$' at source 5335ae5c41609bc84a3842385fd2b75ec61dcdc4; 24-input receipt and per-path dirty-source/qualification controls passed"
        status: pass
      - kind: other
        ref: "cmake -S . -B build/phase21-no-tests -G Ninja -DBUILD_TESTING=OFF -DCMAKE_BUILD_TYPE=Debug -DCMAKE_DISABLE_FIND_PACKAGE_Python3=TRUE && cmake --build build/phase21-no-tests --target gabbaboy-runner; both passed at source 5335ae5c41609bc84a3842385fd2b75ec61dcdc4"
        status: pass
    human_judgment: false
  - id: D2
    description: Fresh admitted replay must reproduce the immutable aggregate end time, rolling RGB555, PCM digest, sample count, audibility, and channel statistics; valid changed values fail with the intended observation mismatch.
    requirement: GAME-02
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission_(contract|controls)$' at source 5335ae5c41609bc84a3842385fd2b75ec61dcdc4; 69 synthetic negative controls passed, fixture controls 45.32 seconds"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_game_evidence$' at source 5335ae5c41609bc84a3842385fd2b75ec61dcdc4; passed in 9.00 seconds"
        status: pass
    human_judgment: false
duration: 56min
completed: 2026-11-02
commits: 9
plan_head_before: 3a1ef76c57c3847cfa02c8519472bbbc6709b96c
plan_head_after: 5335ae5c41609bc84a3842385fd2b75ec61dcdc4
status: complete
---

# Phase GB-21 Plan 21-08: Current Runner and Aggregate Replay Summary

**Admitted synthetic replay now separates historical provenance from the exact qualified CMake runner and reproduces every supported aggregate RGB555/PCM observation.**

## Performance

- **Duration:** about 56 minutes, including the CR-06 same-plan reopening.
- **Started:** approximately 2026-11-02T17:12:00Z.
- **Completed:** 2026-11-02.
- **Tasks:** 2.
- **Files modified:** 8 implementation, documentation, roadmap, validation, and summary files.

## Accomplishments

- Added a BUILD_TESTING-only post-build qualification receipt for the canonical `gabbaboy-runner`. It binds the configure source revision, qualification state, all 24 selected build inputs, writer, exact target path, and measured executable digest. The admitted replay checks the current artifact around native-CGB preflight and replay while preserving historical source IDs and runner hashes.
- Made the current runner revision compile-time fixed, kept Phase 20 admission ahead of candidate guest execution, retained CR-03 working-copy case/input blob checks, and added a cross-revision positive plus causal artifact/source/path/hash and stale-build controls.
- Bound fresh admitted replay to exact aggregate end time, rolling RGB555, PCM digest and sample count, audibility, and left/right PCM statistics. Named checkpoints remain RGB555/time only; unsupported per-checkpoint PCM was removed from the admitted contract.
- Added valid-but-changed digest and PCM observation controls through the admitted replay entry point. The controls assert the intended `candidate-runner-observation-mismatch` reason. Missing/extra aggregate fields and coordinated receipt drift are also rejected.
- Kept Python test tooling out of `BUILD_TESTING=OFF`; configuring with Python package discovery disabled and building only `gabbaboy-runner` succeeded.
- Reopened this same Plan 21-08 after CR-06 exposed two omitted build inputs. Added `src/core/gbb_accept_input.h` and `cmake/StateVersion.cmake` to the exact shared CMake/Python list. Isolated configuration controls set `GBB_BUILD_QUALIFIED=0` for each dirty input and return to `1` after restoration; qualification-receipt controls reject each post-qualification mutation before candidate execution.
- Preserved both actual game no-go records and all historical IDs/hashes. No game candidate ROM or upstream source was executed. These controls establish synthetic reproducibility behavior, not game accuracy, hardware behavior, or rights.
- `GAME-02` is complete. `FIXT-01` remains Pending in `REQUIREMENTS.md` because neither candidate was admitted; the synthetic replay controls do not satisfy that requirement.

## Task Commits

1. **Task 1: Replay across revisions with distinct historical and current build authority** — `866ba503` (test), `7e47cde1` (fix); amended input controls `d287f568`, test evidence parsing `8d4f8bae`, and complete 24-input binding `5335ae5c`.
2. **Task 2: Bind the supported aggregate RGB555 and PCM observations exactly** — `65e7dbc2` (test), `44f2c47d` (fix).

Nine commits are measured from ledger base `3a1ef76c57c3847cfa02c8519472bbbc6709b96c` through `5335ae5c41609bc84a3842385fd2b75ec61dcdc4`, including the initial summary and CR-06 plan amendment commits. The final summary/validation/roadmap metadata commit is separate.

## Verification Results

- `cmake --preset phase1` and `cmake --build --preset phase1` passed at source `5335ae5c41609bc84a3842385fd2b75ec61dcdc4`.
- `ctest --test-dir build --output-on-failure --no-tests=error -R '^phase21_fixture_admission_(contract|controls)$'` passed both tests at that source in 48.60 seconds total. The contract took 3.28 seconds and the controls took 45.32 seconds, within their unchanged 60-second budgets. The controls report 69 synthetic negative controls and six replay positives.
- The added CMake controls configured a clean isolated source tree with `GBB_BUILD_QUALIFIED=1`, then separately changed each newly included path and observed `GBB_BUILD_QUALIFIED=0`; a restored clean configure returned to `1`. Each source was restored before the next control, and neither configure-only mutation invoked the candidate runner.
- The qualification-receipt controls separately changed each file after qualification and rejected with `candidate-current-build-qualification-source-drift` naming the changed path. Invocation markers did not change for either rejection. The recorded CMake/Python inventories matched exactly at 24 entries.
- `ctest --test-dir build --output-on-failure --no-tests=error -R '^phase21_game_evidence$'` passed in 9.00 seconds at source `5335ae5c41609bc84a3842385fd2b75ec61dcdc4`.
- Python-disabled product check passed at that source: `cmake -S . -B build/phase21-no-tests -G Ninja -DBUILD_TESTING=OFF -DCMAKE_BUILD_TYPE=Debug -DCMAKE_DISABLE_FIND_PACKAGE_Python3=TRUE`, followed by `cmake --build build/phase21-no-tests --target gabbaboy-runner`.
- The generated qualification receipt reports source `5335ae5c41609bc84a3842385fd2b75ec61dcdc4`, `build_qualified=true`, 24 source-bound inputs including both amended paths, and runner SHA-256 `d9d48397adcea4502ac8ce0cdbe9127bc3cd14dc80815a636458016079b731d6`. The composed evidence receipt reports the same runner digest and `game=not-admitted`.
- `ctest --test-dir build --output-on-failure --no-tests=error -R '^summary_coverage$'` passed, validating the required machine-readable coverage block.
- `git diff --check` passed. The validation map records both Plan 21-08 checks. The final full-suite run and independent review/security audits remain with the phase orchestrator, which will run them once at the final phase head.

## Deviations from Plan

None — the plan scope and existing CTest budgets were preserved.

## Issues Encountered

The isolated clone initially advertised the feature branch as `origin/HEAD`, which made the guarded commit check unable to identify the actual default branch. The orchestrator corrected only the isolated clone's remote HEAD to `main`; the branch guard then passed. The original working-copy configuration was not changed.

## User Setup Required

None — no external service configuration is required.

## Next Phase Readiness

CR-04, CR-05, and CR-06 are addressed with automated synthetic controls and are ready for independent re-review and threat verification. `FIXT-01` remains Pending because no actual candidate was admitted. The phase orchestrator owns the final full suite and phase-boundary closure; no candidate execution or additional rights decision is authorized or needed by this plan.

---
*Phase: GB-21-cgb-game-progress-and-scene-regressions*
*Completed: 2026-11-02*

## Self-Check: PASSED

- Summary file exists at the required path.
- All nine plan commits through `5335ae5c` are ancestors of the current implementation HEAD.
- The `summary_coverage` CTest passes for this summary's coverage schema.
