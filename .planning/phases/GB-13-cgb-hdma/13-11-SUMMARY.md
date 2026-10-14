---
phase: 13-cgb-hdma
plan: "11"
subsystem: documentation
tags: [CGB, HDMA, claims, player, documentation]
requires:
  - phase: 13-09
    provides: CGB HDMA evidence dispositions and hardware/rights qualifications
  - phase: 13-10
    provides: Bounded installed-consumer evidence for the public DMA behavior
provides:
  - Qualified native, preview, support, README, player-help, and package claims for delivered CGB DMA behavior
  - Standard-library checker for behavior, public-symbol, model, rights, and cross-surface claim consistency
  - Clean and known-bad subject snapshots for the Phase 13-12 prohibition check
affects: [13-12, CGB-07, player-support-claims]
actuals:
  tokens: 10778
  tasks: 2
  commits: 5
commits: 5
plan_head_before: 38b04c6a1ea3f33834df5db4ca710b432143ccd9
plan_head_after: d271508cee8c4740de782586d17e4c02481a1903
tech-stack:
  added: []
  patterns:
    - Run one all-surface claim predicate against either the checkout or an exact-path JSON subject
    - Generate prohibition-test subjects from the actual checkout and require diagnostic-specific rejection
key-files:
  created:
    - tests/scripts/verify-cgb-hdma-claims.py
  modified:
    - docs/native-integration.md
    - docs/support/unreleased.md
    - docs/preview.md
    - README.md
    - src/player/limitations.h
    - src/player/main.c
    - tests/player/claims_agree.cmake
    - tests/player/test_limitations.c
    - .github/workflows/preview.yml
key-decisions:
  - Keep CGB-07 open for phase-level closure; this plan qualifies software behavior but does not establish physical CGB-E evidence.
  - Exclude optional Mealybug CGB-C cases from the CGB-E denominator under the unresolved G1 rights gate.
  - Retain the documented D-06 and Pan Docs contradiction, mode-3 timing limit, DMG APU model, and general game-compatibility limit.
requirements-completed: []
coverage:
  - id: D1
    description: Native consumer claims describe bounded GDMA and HBlank DMA behavior, unchanged public calls, and the selected software model's evidence limits.
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-cgb-hdma-claims.py --native"
        status: pass
      - kind: unit
        ref: "python3 -I tests/scripts/verify-cgb-hdma-claims.py --self-test"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build -R '^(cgb_native_guide_contract|model_gates|summary_coverage)$' --output-on-failure --no-tests=error"
        status: pass
  - id: D2
    description: Player, help, README, and preview package claims agree while retaining mode-3, APU, physical-hardware, and game-compatibility limits.
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-cgb-hdma-claims.py --native-player && python3 -I tests/scripts/verify-cgb-hdma-claims.py"
        status: pass
      - kind: unit
        ref: "python3 -I tests/scripts/verify-cgb-hdma-claims.py --self-test"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build-player -R '^(player_claims_agree|player_claims_agree_mutated|player_limitations|player_cgb_cli)$' --output-on-failure --no-tests=error"
        status: pass
      - kind: integration
        ref: "cmake --preset phase1 && cmake --build --preset phase1"
        status: pass
  - id: D3
    description: Subject snapshots require the exact complete set of surfaces, pass for a clean checkout, and reject a false physical CGB-E qualification with its named diagnostic.
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-cgb-hdma-claims.py --prepare-prohibition-subjects build/p13-11-subjects"
        status: pass
      - kind: unit
        ref: "python3 -I tests/scripts/verify-cgb-hdma-claims.py --subject build/p13-11-subjects/clean.json"
        status: pass
      - kind: unit
        ref: "python3 -I tests/scripts/verify-cgb-hdma-claims.py --self-test"
        status: pass
duration: "9min+ (lower bound from first task commit; startup and research excluded)"
completed: 2026-10-14
status: complete
---

# Phase 13 Plan 13-11: Atomic Consumer Claims and Documentation Contracts Summary

Every consumer-facing surface now describes delivered CGB DMA behavior with the same software-model, timing, audio, hardware, and game-compatibility limits. The checker can also test exact text snapshots produced from the actual checkout for the next plan's prohibition control.

## Accomplishments

- Documented bounded GDMA/HBlank progression, FF55 status and cancellation, HBlank grants, HALT behavior, the unchanged `gbb_run` path, instruction-boundary pending-steal approximation, selected cadence, and overflow safety.
- Aligned README, preview, support history, player help, limitations, and preview-package descriptions. Retained mode-3, DMG APU, physical CGB-E UNKNOWN/POLICY, and game-compatibility limits; CGB-C remains rights-gated and outside the CGB-E denominator.
- Added an eight-surface standard-library checker with native and intermediate selectors, exact subject validation, temporary mutation controls, and checkout-derived clean and known-bad subject preparation.
- Updated the byte-exact player limitations expectation to match the intended claim wording.

## Verification

- Full CGB HDMA claims checker and seven claim mutations plus three subject-input rejections passed.
- Checkout-derived `clean.json` passed all eight surfaces. Preparation verified that the known-bad subject exits with the specific CGB-C/physical-CGB-E qualification diagnostic.
- Player build/help and focused claims, limitations, CLI tests passed 4/4.
- Native guide, model-gates, and summary-coverage contracts passed 3/3. The Phase 1 configure/build completed successfully.
- Parent-owned Phase 13 wave integration run had already passed 988/988; this plan did not repeat the broad suite.

## Task Commits

1. **Task 1 RED:** `0cc07b5` — native guide checker failed on the intended missing HBlank DMA behavior claim; see `build/p13-11-task1-red.xml` and `build/p13-11-task1-red.json`.
2. **Task 1 GREEN:** `5774aca` — documented the native DMA contract and added the native claim checker.
3. **Rule 1 compatibility fix:** `074249a` — restored the existing README double-speed phrase after the player claim contract identified its removal.
4. **Task 2 RED:** `3625661` — player claim contract failed specifically on the missing delivered-DMA software-model phrase; see `build/p13-11-task2-red.xml` and `build/p13-11-task2-red.json`.
5. **Task 2 GREEN:** `d271508` — aligned player, help, workflow and package claims and completed the all-surface subject controls.

## TDD Gate Compliance

- **Task 1 RED:** The named CTest target executed and failed because `docs/native-integration.md` lacked the HBlank DMA behavior claim. The JUnit report and machine record classify this as a semantic assertion failure, not setup or test discovery failure.
- **Task 1 GREEN:** The `--native` selector and checker self-test passed, including mutations for stale claims, missing qualifications, undeclared symbols, and CGB-C/CGB-E conflation.
- **Task 2 RED:** The existing `player_claims_agree` target executed and failed on the new missing delivered-DMA phrase in `src/player/limitations.h`. Its unchanged JUnit report and machine record classify the intended semantic failure.
- **Task 2 GREEN:** Both all-surface selectors, the independent claim and subject negative controls, clean subject, player checks, native contracts, and phase1 build passed. No separate refactor was needed after the focused checks passed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Preserve existing double-speed support phrase**
- **Found during:** Task 2 RED verification
- **Issue:** Task 1's README wording change removed a phrase required by the existing player claim agreement test.
- **Fix:** Restored `CGB double speed is implemented` alongside the qualified DMA wording.
- **Files modified:** `README.md`
- **Verification:** Player claim agreement and mutation control passed in the focused 4/4 player test group.
- **Commit:** `074249a`

**2. [Rule 3 - Blocking issue] Update the exact player limitations test mirror**
- **Found during:** Task 2 GREEN
- **Issue:** The existing limitation test compares the shared limitation text exactly, so it would otherwise block verification of the synchronized claim update.
- **Fix:** Updated only the expected string in `tests/player/test_limitations.c` to mirror the changed macro.
- **Files modified:** `tests/player/test_limitations.c`
- **Verification:** `player_limitations` passed as part of the focused 4/4 player test group.
- **Commit:** `d271508`

### Deferred Issues

The successful phase1 build emitted existing duplicate-archive linker warnings for `test_age` and `test_cgb_speed_*`. They do not affect this documentation/checker plan and are recorded in `deferred-items.md` for the owning build-target plan.

## User Setup Required

None.

## Next Phase Readiness

Phase 13 Wave 9 Plan 13-11 is complete. Continue with **Phase 13 Wave 10 Plan 13-12**, which owns CMake and inventory registration plus the final prohibition proof, using **`/gsd-execute-phase 13 --wave 10`**. CGB-07 remains open until Phase 13 closure. Phase 14 (CGB-E Model Qualification and Corpus) remains unstarted; both auto-advance flags remain false.

---
*Phase: 13-cgb-hdma*
*Completed: 2026-10-14*

## Self-Check: PASSED

- Summary exists and the five task commits are ancestors of the current plan branch.
- `summary_coverage` and `summary_coverage_selftest` passed (2/2).
