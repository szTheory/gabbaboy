---
phase: GB-17-native-save-state-core
plan: "04"
subsystem: state-persistence
tags: [operational-horizon, overflow-safety, CGB, CTest, immutable-mutation]
requires:
  - phase: GB-17-native-save-state-core/17-03
    provides:
      - Transactional native state API, canonical codec, refusal and save/load closure controls
provides:
  - Shared 2^62 operational time horizon across run wrappers and advancing branches
  - Transactional timestamp bounds for queued events and borrowed acceptance spans
  - Complete accepted-state horizon closure matrix and immutable branch-specific guard mutations
affects: [state-persistence, CGB timing, acceptance]
actuals:
  tokens: 22401
  tasks: 3
  commits: 7
commits: 7
plan_head_before: 207e7bc0688ec78f4164d1a52f67a8d3586d2206
plan_head_after: f64a798539b517604db3c522e689f56416e7df5c
tech-stack:
  added: []
  patterns:
    - Subtraction-safe horizon checks share one predicate and one checked time projection.
    - Immutable source mutations require branch witness, intended TAP assertion failure, and unrelated passing control.
    - Fixture setup dependencies make the named closure gate select every bounded shard.
key-files:
  created:
    - tests/scripts/verify-state-horizon.py
  modified:
    - src/core/gabbaboy.c
    - include/gabbaboy/gabbaboy.h
    - tests/test_state_horizon.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - docs/state-format.md
    - tests/test_cgb_hdma_internal.c
    - tests/test_cgb_speed_internal.c
    - cmake/P12Mutants.cmake
    - .planning/phases/GB-17-native-save-state-core/17-04-PLAN.md
key-decisions:
  - "Use one checked `state_time_fits` predicate for the 2^62 limit while preserving the separately validated UINT64_MAX timer sentinel."
  - "Keep the full audio phase and ring-head closure space; split it into fixture-linked CTest shards within the normal per-test timeout."
requirements-completed: [STATE-02, STATE-03]
duration: 50min
started: 2026-10-26T18:30:21-04:00
completed: 2026-10-26
status: complete
---

# Phase 17 Plan 04: Operational State Horizon Summary

**Run and acceptance paths now stop at a shared 2^62 time horizon, event/span admission is transactional, and a complete 5,644-case phase/head matrix proves accepted boundary states remain saveable.**

## Performance

- **Duration:** 50 min
- **Started:** 2026-10-26T18:30:21-04:00
- **Completed:** 2026-10-26T19:20:28-04:00
- **Tasks:** 3
- **Files modified:** 11

## Accomplishments

- Applied one subtraction-safe horizon rule to STOP elapsed time, CPU stalls, HDMA ticks and reservations, IRQ service, HALT, instruction execution, full speed-switch reservation, peripheral projection and target advancement. Over-cap live state refuses without mutation; exact-cap observations and valid timer sentinels remain supported.
- Bounded ordinary queued timestamps and borrowed acceptance spans, preserving event order at equal timestamps and rejecting invalid spans without changing the machine or caller cursor.
- Added a complete accepted-state closure matrix over 2,822 audio-phase classes and both ring-head positions. All 5,644 cases load, advance exactly to the cap, save/load/resave canonically, and refuse the next timed operation without state change. The exact named CTest gate selects all 16 linked cases (the root plus 15 shards).
- Added immutable, witnessed missing-guard mutations for every advancing/admission path and every public/acceptance wrapper. Each mutant compiled, failed its intended semantic assertion after the required branch witness, and passed the unrelated codec control.
- Migrated legacy HDMA and speed-switch near-`UINT64_MAX` fixtures to the adopted 2^62 contract while retaining explicit over-cap invalid/no-mutation checks. Retargeted the existing M22 mutation to the cap-aware full reservation guard.

## Verification

- `cmake --preset phase1` and `cmake --build --preset phase1` passed at `f64a798539b517604db3c522e689f56416e7df5c`.
- Task 1 selector `state_(horizon|horizon_wrappers|horizon_sentinels)` passed 3/3.
- Task 2 selector `state_(horizon_events|horizon_closure|canonical|audio_bound)` passed 19/19. Fixture selection ran all 16 closure tests; each shard completed in about 18–22 seconds, and the run reported all 5,644 phase/head cases with no omitted shard cases.
- Task 3 selector `state_horizon_(mutants|mutant_controls)` passed 2/2. The checker report at the immutable revision records 14/14 intended mutant failures, each with semantic exit 1 and unrelated control exit 0; no compile or setup failure counted as a kill. AppleClang 21 and the configured Debug `-O2` test build were used; sanitizers were disabled in this build.
- The affected CGB/speed-switch/HDMA/partition, model-gate and test-budget selection passed 126/126, including `cgb_speed_headroom`, the M22 omitted-reservation mutant and control, `cgb_hdma_resource_bounds`, and speed stall/device-state controls. `dmg_baseline` passed 1/1.
- The Task 1, Task 2 and Task 3 JUnit RED records each returned `RED_EVIDENCE_OK`; semantic inspection confirmed stop-wait cap crossing, borrowed-span cap+1 acceptance, and the deliberately removed stop-wait guard respectively. Task 1/2 evidence was regenerated from their immutable pre-GREEN commits without changing earlier records.
- `git diff --check` passed. The full project CTest suite is left to the phase orchestrator's post-wave run.

## Task Commits

1. **Task 1 RED: Add failing operational horizon cases** — `1e544f6`.
2. **Task 1 GREEN: Enforce the native state time horizon** — `1b744c8`.
3. **Task 2 RED: Add event and closure cases** — `96ef0cd`.
4. **Task 2 GREEN: Bound event admission and close cap states** — `84c2159`.
5. **Task 3 RED: Witness independent horizon branches** — `0da6bfb`.
6. **Authorized legacy fixture migration** — `8d8ab04`.
7. **Task 3 GREEN: Close the operational state horizon** — `f64a798`.

The persisted plan ledger measured seven commits from `207e7bc0688ec78f4164d1a52f67a8d3586d2206` through `f64a798539b517604db3c522e689f56416e7df5c`. The realized diff contained 89,604 characters, or 22,401 estimate tokens.

## TDD Gate Compliance

- **Task 1 RED:** The immutable pre-GREEN commit `1e544f6` ran the registered `state_horizon` CTest successfully through configure and build, then failed the `horizon_matrix` stop-wait semantic assertion because elapsed STOP time crossed the cap. `build/state_horizon_task1_red.json` passed `check tdd-red-evidence` with `RED_EVIDENCE_OK`.
- **Task 1 GREEN:** `state_horizon`, `state_horizon_wrappers`, and `state_horizon_sentinels` pass at `f64a798`.
- **Task 2 RED:** The immutable pre-GREEN commit `96ef0cd` ran `state_horizon_events` and failed the intended borrowed-span cap-plus-one admission assertion. `build/state_horizon_events_task2_red.json` passed `check tdd-red-evidence` with `RED_EVIDENCE_OK`.
- **Task 2 GREEN:** Event/span admission, equal-time event ordering, all accepted-state closure cases, canonical save/load, and audio-bound controls pass at `f64a798`.
- **Task 3 RED:** The branch-specific missing-stop-wait-guard mutation emitted its witness and failed the named semantic assertion; `build/state_horizon_guard-red.json` passed `check tdd-red-evidence` with `RED_EVIDENCE_OK`.
- **Task 3 GREEN:** All 14 immutable guard mutants are semantically rejected and all unrelated controls pass at `f64a798`.

## Files Created/Modified

- `src/core/gabbaboy.c` — shared safe horizon predicates, run entry/branch preflights, event/span checks, checked device advancement, and guard markers for semantic mutations.
- `tests/test_state_horizon.c` — wrapper, sentinel, event/span, collision-order, cap closure, per-branch witness, and control cases.
- `tests/scripts/verify-state-horizon.py` — exact-revision materialization, 14 isolated guard mutations, semantic TAP checks, unrelated controls, and digest report.
- `tests/CMakeLists.txt` and `tests/expected-tests.txt` — standard-timeout CTests, complete closure shard fixtures, checker/control registration, and exact inventory.
- `tests/test_cgb_hdma_internal.c` and `tests/test_cgb_speed_internal.c` — cap-relative successful reservation/headroom fixtures with retained invalid over-cap cases.
- `cmake/P12Mutants.cmake` — M22 now removes the cap-aware reservation guard.
- `docs/state-format.md` — documented accepted ordinary-time horizon and sentinel distinction.
- `include/gabbaboy/gabbaboy.h` — public run horizon contract.
- `17-04-PLAN.md` — synchronized the exhaustive changed-file registry.

## Decisions Made

- Applied the cap with checked subtraction and preserved existing stop/no-progress semantics; did not truncate atomic instruction, interrupt, HDMA, or speed-switch work to fit.
- Kept full accepted-state closure coverage and used fixture-linked shards so `-R '^state_horizon_closure$'` automatically runs the complete matrix.
- Kept timer `UINT64_MAX` sentinel validity under its separate field invariant while ordinary timestamps remain capped.

## Deviations from Plan

### Authorized Compatibility Fix

**1. [Rule 1 - Bug] Migrated existing CGB timing fixtures to the adopted operational horizon**

- **Found during:** Task 1 affected-test run.
- **Issue:** Legacy successful HDMA and speed-switch fixtures placed live machine time near `UINT64_MAX`; the new 2^62 limit correctly classified those states as invalid. The old M22 mutant only removed the pre-existing UINT64 overflow check, which became redundant behind the new cap check and did not test the intended reservation guard.
- **Fix:** Preserved explicit over-cap invalid-state/no-mutation checks; moved successful full-reservation and cap+1 no-progress examples to independent cap-relative timestamps; retargeted M22 to remove the cap-aware `state_time_fits` reservation and verified it fails the intended no-progress/no-mutation assertion.
- **Files modified:** `tests/test_cgb_hdma_internal.c`, `tests/test_cgb_speed_internal.c`, `tests/CMakeLists.txt`, `cmake/P12Mutants.cmake`, and `17-04-PLAN.md`.
- **Commit:** `8d8ab04`.

No authentication gates, new stubs, skipped tests, or security-relevant trust surfaces were introduced.

## Self-Check: PASSED

- `17-04-SUMMARY.md` exists at the required phase path.
- All seven plan commits (`1e544f6`, `1b744c8`, `96ef0cd`, `84c2159`, `0da6bfb`, `8d8ab04`, and `f64a798`) exist and are ancestors of `HEAD`.
- The `summary_coverage` CTest passed 1/1 for this block-schema coverage.
