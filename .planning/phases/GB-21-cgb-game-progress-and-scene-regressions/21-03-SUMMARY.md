---
phase: GB-21-cgb-game-progress-and-scene-regressions
plan: "03"
subsystem: testing
tags: [cgb, candidate-evidence, fixture-admission, python, cmake, ctest]
requires:
  - phase: GB-20-fixture-admission-tune-up
    provides:
      - Phase 20 fixture manifest, notice and immutable admission-pin checker
provides:
  - Fixed ordered candidate record contract with immutable primary references and explicit cutoff facts
  - Synthetic admitted-progress and confined-build controls using the Phase 20 admission CLI
affects: [GB-21-02, GB-21-04, GB-21-05, GB-21-07, fixture-admission]
actuals:
  tokens: 28869
  tasks: 2
  commits: 4
commits: 4
plan_head_before: 13a73a3eff4051a36e69da727a783f20dd5144f9
plan_head_after: 51fd58086ac7b70a8a52d4c844942156717e17d9
tech-stack:
  added: [Python standard library, CMake, CTest]
  patterns:
    - Exact two-ID candidate order and immutable fallback references
    - Private disposable Git clones for synthetic positive and negative controls
key-files:
  created:
    - tests/scripts/verify-cgb-candidates.py
    - tests/scripts/test_cgb_candidate_order.py
    - tests/cmake/game-evidence.cmake
    - docs/cgb-game-candidates.md
  modified:
    - tests/CMakeLists.txt
key-decisions:
  - "Self-tests use synthetic records and a synthetic CGB ROM in a disposable clone; they do not decide either real candidate attempt."
  - "FIXT-01 remains pending until the bounded primary and conditional fallback attempts and final composition are completed in later plans."
requirements-completed: []
coverage:
  - id: D1
    description: Fixed candidate order, final-state rules, missing-record rejection and explicit cutoff accounting.
    requirement: FIXT-01
    verification:
      - kind: unit
        ref: python3 -I tests/scripts/test_cgb_candidate_order.py
        status: pass
      - kind: integration
        ref: ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission_contract$'
        status: pass
    human_judgment: false
  - id: D2
    description: Admitted evidence delegates to Phase 20, binds native-CGB progress and receipt identities, and requires confined build and probe evidence.
    requirement: FIXT-01
    verification:
      - kind: integration
        ref: ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission_controls$'
        status: pass
      - kind: integration
        ref: cmake --preset phase1 && cmake --build --preset phase1
        status: pass
    human_judgment: false
metrics:
  duration: 32min
  completed: 2026-11-02
status: complete
---

# Phase GB-21 Plan 21-03: CGB Candidate Evidence Contract Summary

**Two-candidate CGB evidence checks now bind admission to Phase 20 and require confined native-CGB progress receipts.**

## Performance

- **Duration:** 32 minutes
- **Started:** 2026-11-02T02:07:33Z
- **Completed:** 2026-11-02T02:40:05Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added a source-bound contract for exactly Potion Panic first and preferred µCity 1.3 only after a committed primary no-go; partial records carry explicit blocked-stage reasons and cannot close final state.
- Required the existing Phase 20 manifest, notice and pin checker for admitted synthetic subjects, then bound the ROM/header, native-CGB mode, case/input/predicate, progress controls, checkpoints, PCM digests and receipt to immutable identities.
- Required executed-build isolation evidence and added controls for network, credential, mount, privilege and probe failures. A build-isolation environment no-go proves the candidate build did not run and leaves later facts unobserved.
- Registered separate contract and admission-control CTests. Their positive and negative records, ROM and runner exist only inside disposable synthetic Git clones.

## Task Commits

1. **Task 1 RED:** `ec8c39d0` — define candidate attempt order contract.
2. **Task 1 GREEN:** `8793173e` — add ordered candidate record contract.
3. **Task 2 RED:** `b9b47ca8` — define admission and build isolation controls.
4. **Task 2 GREEN:** `51fd5808` — close candidate admission and isolation controls.

## Files Created/Modified

- `tests/scripts/verify-cgb-candidates.py` — bounded record, order, admission, progress, receipt and build-isolation validation with synthetic CLI controls.
- `tests/scripts/test_cgb_candidate_order.py` — unit controls for candidate order, admitted progress rules and subprocess limits.
- `tests/CMakeLists.txt` — includes the phase game-evidence CTest registrations.
- `tests/cmake/game-evidence.cmake` — immutable-source CTest registration for both candidate contract suites.
- `docs/cgb-game-candidates.md` — record, admission, isolation and cutoff semantics.

## Decisions Made

- Keep both real candidate attempts out of this plan. The checker’s positives are synthetic and cannot be interpreted as rights clearance, compatibility evidence or candidate outcomes.
- Keep FIXT-01 pending until Plans 21-04 and 21-05 produce the bounded primary/fallback outcomes and Plan 21-07 composes final evidence.

## Deviations from Plan

None — both tasks stayed within the synthetic contract and control scope.

## Issues Encountered

- The temporary synthetic `.gbc` file matched the repository’s binary ignore rule, so the disposable fixture commit explicitly added that generated control ROM. No candidate image or ROM was added to the project checkout.
- CMake reported that a matching Clang libFuzzer runtime was unavailable; deterministic sanitizer regressions remained enabled. The required configure, full build and focused CTests passed.
- The full CTest suite was not run; this plan’s verification calls for the two registered admission contract/control tests. Final full-suite qualification remains in the later phase plan.

## Requirement Traceability

- **FIXT-01:** Contract and controls are implemented, but the requirement remains pending because neither actual candidate attempt was run or decided here.
- **GAME-02:** Existing Phase 21 progress-tracer coverage remains complete; this plan adds candidate-side binding controls without changing that status.

## User Setup Required

None.

## Next Phase Readiness

Plan 21-03 is complete. No actual Potion Panic or µCity attempt was run. Plan 21-02 remains the next unfinished Wave 2 plan; candidate attempts remain gated to Plans 21-04 and 21-05 after their dependencies. Continue Phase 21 through `/gsd-execute-phase 21`; this executor did not start another plan.

---
*Phase: GB-21-cgb-game-progress-and-scene-regressions*
*Completed: 2026-11-02*

## Self-Check: PASSED

- SUMMARY.md exists at the expected phase path.
- All four task commits are ancestors of the current plan head.
- Measured plan commit count and plan head boundaries match the persisted ledger.
