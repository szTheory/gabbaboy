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
  tokens: 19151.25
  tasks: 2
  commits: 4
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
key-decisions:
  - "Historical runner hashes and source IDs stay immutable; current build authority comes only from the trusted CMake target and its separate qualification receipt."
  - "Admitted replay binds the complete supported aggregate RGB555/PCM observation; unsupported per-checkpoint PCM is not inferred."
  - "Actual game records remain no-go and were not changed or executed; synthetic controls establish reproducibility contract behavior only."
patterns-established:
  - "Keep historical receipt validation independent from current working-checker source matching."
  - "Route valid-but-changed outputs through the admitted replay entry point and assert the precise observation mismatch."
requirements-completed: [GAME-02, FIXT-01]
coverage:
  - id: D1
    description: The canonical CMake-built runner has independent source, build-input, path, and executable qualification separate from immutable historical receipt identity; the BUILD_TESTING=OFF runner remains Python-free.
    requirement: FIXT-01
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission_(contract|controls)$' at source 44f2c47de920cd61860954a2a141f134a93f4b32"
        status: pass
      - kind: other
        ref: "cmake -S . -B build/phase21-no-tests -G Ninja -DBUILD_TESTING=OFF -DCMAKE_BUILD_TYPE=Debug -DCMAKE_DISABLE_FIND_PACKAGE_Python3=TRUE && cmake --build build/phase21-no-tests --target gabbaboy-runner; both passed at source 44f2c47de920cd61860954a2a141f134a93f4b32"
        status: pass
    human_judgment: false
  - id: D2
    description: Fresh admitted replay must reproduce the immutable aggregate end time, rolling RGB555, PCM digest, sample count, audibility, and channel statistics; valid changed values fail with the intended observation mismatch.
    requirement: GAME-02
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission_(contract|controls)$' at source 44f2c47de920cd61860954a2a141f134a93f4b32; 65 synthetic controls passed, fixture controls 48.56 seconds"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_game_evidence$' at source 44f2c47de920cd61860954a2a141f134a93f4b32; passed in 10.02 seconds"
        status: pass
    human_judgment: false
duration: 39min
completed: 2026-11-02
commits: 4
plan_head_before: 3a1ef76c57c3847cfa02c8519472bbbc6709b96c
plan_head_after: 44f2c47de920cd61860954a2a141f134a93f4b32
status: complete
---

# Phase GB-21 Plan 21-08: Current Runner and Aggregate Replay Summary

**Admitted synthetic replay now separates historical provenance from the exact qualified CMake runner and reproduces every supported aggregate RGB555/PCM observation.**

## Performance

- **Duration:** about 39 minutes.
- **Started:** approximately 2026-11-02T17:12:00Z.
- **Completed:** 2026-11-02.
- **Tasks:** 2.
- **Files modified:** 6 implementation, documentation, and validation files; this summary records the plan result.

## Accomplishments

- Added a BUILD_TESTING-only post-build qualification receipt for the canonical `gabbaboy-runner`. It binds the configure source revision, qualification state, 22 selected build inputs, writer, exact target path, and measured executable digest. The admitted replay checks the current artifact around native-CGB preflight and replay while preserving historical source IDs and runner hashes.
- Made the current runner revision compile-time fixed, kept Phase 20 admission ahead of candidate guest execution, retained CR-03 working-copy case/input blob checks, and added a cross-revision positive plus causal artifact/source/path/hash and stale-build controls.
- Bound fresh admitted replay to exact aggregate end time, rolling RGB555, PCM digest and sample count, audibility, and left/right PCM statistics. Named checkpoints remain RGB555/time only; unsupported per-checkpoint PCM was removed from the admitted contract.
- Added valid-but-changed digest and PCM observation controls through the admitted replay entry point. The controls assert the intended `candidate-runner-observation-mismatch` reason. Missing/extra aggregate fields and coordinated receipt drift are also rejected.
- Kept Python test tooling out of `BUILD_TESTING=OFF`; configuring with Python package discovery disabled and building only `gabbaboy-runner` succeeded.
- Preserved both actual game no-go records and all historical IDs/hashes. No game candidate ROM or upstream source was executed. These controls establish synthetic reproducibility behavior, not game accuracy, hardware behavior, or rights.

## Task Commits

1. **Task 1: Replay across revisions with distinct historical and current build authority** — `866ba503` (test), `7e47cde1` (fix).
2. **Task 2: Bind the supported aggregate RGB555 and PCM observations exactly** — `65e7dbc2` (test), `44f2c47d` (fix).

The four task commits are measured from ledger base `3a1ef76c57c3847cfa02c8519472bbbc6709b96c` through `44f2c47de920cd61860954a2a141f134a93f4b32`. The summary is committed separately.

## Verification Results

- `cmake --preset phase1` and `cmake --build --preset phase1` passed at source `44f2c47de920cd61860954a2a141f134a93f4b32`.
- `ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission_(contract|controls)$'` passed both tests. The contract took 3.58 seconds and the controls took 48.56 seconds, within their unchanged 60-second budgets. The suite covers 65 synthetic controls, including valid changed rolling digest, PCM digest/sample count, and internally consistent PCM statistics.
- `ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_game_evidence$'` passed in 10.02 seconds.
- Python-disabled product check passed: `cmake -S . -B build/phase21-no-tests -G Ninja -DBUILD_TESTING=OFF -DCMAKE_BUILD_TYPE=Debug -DCMAKE_DISABLE_FIND_PACKAGE_Python3=TRUE`, followed by `cmake --build build/phase21-no-tests --target gabbaboy-runner`.
- The generated qualification receipt reports source `44f2c47de920cd61860954a2a141f134a93f4b32`, `build_qualified=true`, 22 source-bound inputs, and runner SHA-256 `7d236fbfb7ceda1a3f73235507854450d0fb32bd3032cbf8ecac607ad41b0d82`. The composed evidence receipt reports the same runner digest and `game=not-admitted`.
- `ctest --test-dir build --output-on-failure --no-tests=error -R '^summary_coverage$'` passed, validating the required machine-readable coverage block.
- `git diff --check` passed. The validation map records both Plan 21-08 checks. The final full-suite run and independent review/security audits remain with the phase orchestrator, which will run them once at the final phase head.

## Deviations from Plan

None — the plan scope and existing CTest budgets were preserved.

## Issues Encountered

The isolated clone initially advertised the feature branch as `origin/HEAD`, which made the guarded commit check unable to identify the actual default branch. The orchestrator corrected only the isolated clone's remote HEAD to `main`; the branch guard then passed. The original working-copy configuration was not changed.

## User Setup Required

None — no external service configuration is required.

## Next Phase Readiness

The two planned correctness findings have automated synthetic controls and are ready for independent re-review and threat verification. The phase orchestrator owns the final full suite and phase-boundary closure; no candidate execution or additional rights decision is authorized or needed by this plan.

---
*Phase: GB-21-cgb-game-progress-and-scene-regressions*
*Completed: 2026-11-02*

## Self-Check: PASSED

- Summary file exists at the required path.
- All four task commits are ancestors of the current implementation HEAD.
- The `summary_coverage` CTest passes for this summary's coverage schema.
