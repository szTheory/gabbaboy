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
  tokens: 22675.5
  tasks: 3
  commits: 9
commits: 9
plan_head_before: 207e7bc0688ec78f4164d1a52f67a8d3586d2206
plan_head_after: 95302423da0aa4bd7ce060621c4b262e28675b2a
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
    - tests/test_events.c
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
coverage:
  - id: D1
    description: "Every native run wrapper and independently advancing branch respects the shared 2^62 horizon while retaining transactional refusal and valid timer sentinel behavior."
    requirement: STATE-02
    human_judgment: false
    verification:
      - kind: unit
        ref: "state_horizon, state_horizon_wrappers, and state_horizon_sentinels at immutable revision f64a798539b517604db3c522e689f56416e7df5c."
        status: pass
      - kind: integration
        ref: "Affected CGB speed-switch, HDMA, partition, model-gate, and test-budget selection passed 126/126 at immutable revision f64a798539b517604db3c522e689f56416e7df5c."
        status: pass
  - id: D2
    description: "Ordinary event and borrowed-span admission is capped without partial mutation, equal-time ordering changes, or loss of save/load closure."
    requirement: STATE-03
    human_judgment: false
    verification:
      - kind: integration
        ref: "state_horizon_events, state_horizon_closure, state_canonical, and state_audio_bound at immutable revision f64a798539b517604db3c522e689f56416e7df5c; the fixture-linked closure gate covered all 5,644 audio-phase/ring-head combinations."
        status: pass
  - id: D3
    description: "Every independent horizon/admission guard has a witnessed immutable semantic mutation and unrelated codec control, including under the project sanitizer configuration."
    requirement: STATE-03
    human_judgment: false
    verification:
      - kind: integration
        ref: "verify-state-horizon.py at immutable revision 95302423da0aa4bd7ce060621c4b262e28675b2a: all 14 semantic mutants exit 1 and controls exit 0 in normal and sanitizer=true runs; sanitizer self-test passes with control leak detection enabled."
        status: pass
duration: 63min
started: 2026-10-26T18:30:21-04:00
completed: 2026-10-26T19:33:05-04:00
status: complete
---

# Phase 17 Plan 04: Operational State Horizon Summary

**Run and acceptance paths now stop at a shared 2^62 time horizon, event/span admission is transactional, and a complete 5,644-case phase/head matrix proves accepted boundary states remain saveable.**

## Performance

- **Duration:** 63 min
- **Started:** 2026-10-26T18:30:21-04:00
- **Completed:** 2026-10-26T19:33:05-04:00
- **Tasks:** 3
- **Files modified:** 11

## Accomplishments

- Applied one subtraction-safe horizon rule to STOP elapsed time, CPU stalls, HDMA ticks and reservations, IRQ service, HALT, instruction execution, full speed-switch reservation, peripheral projection and target advancement. Over-cap live state refuses without mutation; exact-cap observations and valid timer sentinels remain supported.
- Bounded ordinary queued timestamps and borrowed acceptance spans, preserving event order at equal timestamps and rejecting invalid spans without changing the machine or caller cursor.
- Added a complete accepted-state closure matrix over 2,822 audio-phase classes and both ring-head positions. All 5,644 cases load, advance exactly to the cap, save/load/resave canonically, and refuse the next timed operation without state change. The current named CTest gate selects all 128 linked cases (the root plus 127 shards).
- Added immutable, witnessed missing-guard mutations for every advancing/admission path and every public/acceptance wrapper. Each mutant compiled, failed its intended semantic assertion after the required branch witness, and passed the unrelated codec control.
- Migrated legacy HDMA and speed-switch near-`UINT64_MAX` fixtures to the adopted 2^62 contract while retaining explicit over-cap invalid/no-mutation checks. Retargeted the existing M22 mutation to the cap-aware full reservation guard.

## Verification

- `cmake --preset phase1` and `cmake --build --preset phase1` passed at `f64a798539b517604db3c522e689f56416e7df5c`; the build was repeated successfully after the checker-only fix at `95302423da0aa4bd7ce060621c4b262e28675b2a`.
- Task 1 selector `state_(horizon|horizon_wrappers|horizon_sentinels)` passed 3/3.
- At the original plan revision, Task 2 selector `state_(horizon_events|horizon_closure|canonical|audio_bound)` passed 19/19 and fixture selection ran all 16 closure tests, reporting all 5,644 phase/head cases.
- Task 3 selector `state_horizon_(mutants|mutant_controls)` passed 2/2 at both `f64a798539b517604db3c522e689f56416e7df5c` and `95302423da0aa4bd7ce060621c4b262e28675b2a`. The immutable checker report records 14/14 intended mutant failures, each with semantic exit 1 and unrelated control exit 0; no compile or setup failure counted as a kill. The normal build used AppleClang 21 and the configured Debug `-O2` test build.
- The corrected immutable checker and controls passed 2/2 in the Linux sanitizer container at `95302423da0aa4bd7ce060621c4b262e28675b2a`, configured with `GABBABOY_ENABLE_SANITIZERS=ON` and the project ASan/UBSan flags. The CTest properties used the existing sanitizer timeout multiplier (180 seconds); the checker report recorded `sanitizer=true`, all 14 semantic exits as 1, and all control exits as 0. The sanitizer self-test passed 1/1. Leak detection remains enabled for passing controls; the expected-failing mutant child disables only LSan because its intentional early assertion return bypasses teardown, while ASan/UBSan remain enabled.
- The original 16-way sanitizer closure run in the local `linux/amd64` container under `arm64` emulation had eight shards reach the existing 180-second CTest timeout. This was an emulation runtime limit, not a semantic failure. The timeout policy was not changed; the matrix was split into 128 complete shards in the integration follow-up below.
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
8. **Checker fix: Keep sanitizer mutant failures semantic** — `9530242`.

The persisted plan ledger measured nine commits from `207e7bc0688ec78f4164d1a52f67a8d3586d2206` through `95302423da0aa4bd7ce060621c4b262e28675b2a`, including the initial summary-only record. The realized implementation diff measured 90,702 characters, or 22,675.5 estimate tokens.

## TDD Gate Compliance

- **Task 1 RED:** The immutable pre-GREEN commit `1e544f6` ran the registered `state_horizon` CTest successfully through configure and build, then failed the `horizon_matrix` stop-wait semantic assertion because elapsed STOP time crossed the cap. `build/state_horizon_task1_red.json` passed `check tdd-red-evidence` with `RED_EVIDENCE_OK`.
- **Task 1 GREEN:** `state_horizon`, `state_horizon_wrappers`, and `state_horizon_sentinels` pass at `f64a798`.
- **Task 2 RED:** The immutable pre-GREEN commit `96ef0cd` ran `state_horizon_events` and failed the intended borrowed-span cap-plus-one admission assertion. `build/state_horizon_events_task2_red.json` passed `check tdd-red-evidence` with `RED_EVIDENCE_OK`.
- **Task 2 GREEN:** Event/span admission, equal-time event ordering, all accepted-state closure cases, canonical save/load, and audio-bound controls pass at `f64a798`.
- **Task 3 RED:** The branch-specific missing-stop-wait-guard mutation emitted its witness and failed the named semantic assertion; `build/state_horizon_guard-red.json` passed `check tdd-red-evidence` with `RED_EVIDENCE_OK`.
- **Task 3 GREEN:** All 14 immutable guard mutants are semantically rejected and all unrelated controls pass at `f64a798`. The sanitizer checker follow-up at `9530242` preserves those semantic kills with ASan/UBSan active and leak detection enabled on passing controls.

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

**2. [Rule 1 - Bug] Keep intentional sanitizer mutant failures distinguishable from leak reports**

- **Found during:** Task 3 sanitizer verification.
- **Issue:** A semantically failing mutation intentionally returns at its assertion before the test fixture can destroy the machine, so LeakSanitizer reported the expected early exit as a non-TAP failure and obscured whether the named guard was killed.
- **Fix:** Disabled leak detection only in the expected-failing mutant child when sanitizer compile flags are present. ASan/UBSan remain enabled, and leak detection stays enabled for the passing control; the checker self-test verifies semantic failure recognition.
- **Files modified:** `tests/scripts/verify-state-horizon.py`.
- **Verification:** Immutable normal and sanitizer mutant/control CTests pass 2/2, with 14/14 semantic mutant exits 1, all controls 0, and sanitizer self-test 1/1.
- **Commit:** `9530242`.

The local full sanitizer closure attempt remains environment-limited by eight 180-second timeouts under amd64-on-arm64 emulation; native hosted sanitizer closure is pending. No timeout, test case, or acceptance criterion was weakened.

No authentication gates, new stubs, skipped tests, or security-relevant trust surfaces were introduced.

## Post-wave event fixture correction

The full post-wave suite at `d23d92f` passed 1320/1321; `event_time_overflow` still expected an event near UINT64_MAX to be admitted. Integration commit `7c1b86f` migrates `tests/test_events.c` to the adopted cap without changing core behavior: a valid STOP wake reaches 2^62, later and UINT64_MAX timestamps refuse without serialized-state change, and the next timed operation returns no progress with zero consumption and unchanged state. The event case and related classifier/mutation controls passed 14/14 in both normal and Linux ASan/UBSan builds at that commit. The original plan ledger above is unchanged; this is subsequent integration evidence. Windows remains subject to current hosted checks. The declared plan file registry includes this necessary legacy-test migration.

## Integration Follow-up: closure runtime and native Windows checker

The 16-shard matrix still approached or exceeded hosted normal and sanitizer test limits. Profiling showed that setup was negligible while each case's production save, load, resave, and full serialized-byte comparisons dominated. Commit `7b7e3b2` replaces only the harness baseline reload with an in-memory pristine instance copy. Before every reset, it verifies pointer identity; the fixture also requires that all owned/borrowed external buffers are absent except the immutable ROM. All 5,644 case inputs, production codec saves and loads, resave byte comparisons, post-cap refusal checks, and full-state byte comparisons remain in place.

The same commit fixes the Windows MinGW mutant harness. The prior executable-existence check used an extensionless output name for native GNU-on-Windows, and its source path argument retained C-incompatible backslashes. The checker now expects `.exe` on native Windows, normalizes source paths to forward slashes, and prints compiler command/exit/output diagnostics on build failure. Its self-test covers Windows path and suffix behavior. A live Windows rerun is pending hosted CI.

Commit `bb1f2e8` registers 128 fixture-linked shards and the expected-test inventory. The unchanged exact selector `ctest -R '^state_horizon_closure$'` selects the root plus all 127 fixture shards; `ctest -N` in the separate configured tree listed 128 tests. Representative shards 0, 1, 63, and 127 passed with 45, 45, 44, and 44 cases respectively. An independent partition audit covered 5,644 unique case IDs across all shards and rejected deliberate missing-case and duplicate-case controls.

At immutable code revision `7b7e3b21251f1c2a5ac74817d4afea370f96485e`, normal mutant/control CTests passed 2/2 with 14/14 semantic mutant exits 1 and all unrelated controls exit 0. The Linux ASan/UBSan CTests also passed 2/2 at the same revision with sanitizer enabled; the complete 14-mutant checker finished within its existing 180-second timeout under local amd64-on-arm64 emulation, and its self-test passed. Leak detection remained enabled for passing controls. The parent reports the local full integration selection passed 133/133 with all 128 closure shards; that run used the integration tree whose CMake registration is now committed in `bb1f2e8`. The parent is running the final 1,473-test suite at `bb1f2e8`; its result will be recorded separately.

The original plan ledger and actuals above remain unchanged. This follow-up adds only the test harness/checker fix, shard registration, and verification evidence.

## Self-Check: PASSED

- The summary exists at the required phase path and its block-schema coverage passed `summary_coverage` 1/1 after this update.
- The plan's implementation commits and subsequent integration commits `7b7e3b2` and `bb1f2e8` are ancestors of `HEAD`.
- The 128-shard exact CTest selector, four representative shard executions, independent partition negative controls, and normal/sanitizer mutant-control CTests passed as recorded above.
