---
phase: 12-cgb-double-speed
plan: 17
subsystem: testing
tags: [CGB, AGE, CTest, dispositions]
requires:
  - phase: GB-12 plans 12-09 and 12-16
    provides: Measured switch timing window, committed-core AGE verdicts, and immutable fixture baselines
provides:
  - Four current-behavior pins for unresolved CGB speed-switch behavior
  - Complete expected-failure disposition manifest with docs and inventory verification
  - Measured AGE sensitivity matrix for M6, M21, M28, and M27
affects: [GB-12 plan 12-18, CGB-06, AGE fixtures]
tech-stack:
  added: []
  patterns:
    - Expected-failure disposition rows cross-check their exact pin tests against the test inventory and docs mirror.
    - AGE sensitivity runs compare each admitted ROM against clean behavior under runtime-mask mutants.
key-files:
  created:
    - tests/scripts/verify-cgb-speed-dispositions.py
  modified:
    - cmake/P12Mutants.cmake
    - docs/cgb-profile.md
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/external/cgb-speed-dispositions.json
    - tests/test_age.c
    - tests/test_cgb_speed_internal.c
key-decisions:
  - Keep all unresolved behavior tied to measured current-core pins and explicit mutant or input-mutation negative controls.
  - Correct M28 to add a half-dot only when switching to double speed; preserve its measured spsw-mode0 discrimination and spsw-div low-bit insensitivity.
requirements-completed: [CGB-06]
actuals:
  tokens: 17606.75
  tasks: 3
  commits: 3
commits: 3
plan_head_before: 115a9d3701eec1c2f0b133bb5073e7a9d4aedd2b
plan_head_after: 6808783a00ae83d69a2ed405057f7a6ebbaee5e8
metrics:
  duration: "23m+ lower bound"
  completed: 2026-10-13
status: complete
coverage:
  - id: CGB-06-SPEED-BEHAVIOR-PINS
    description: Four unresolved speed-switch behaviors are pinned to current behavior with mutant or deliberate-input negative controls.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: cgb_speed_xfail_pause_ppu_output
        status: pass
      - kind: integration
        ref: cgb_speed_mutant_m7_xfail_ppu
        status: pass
      - kind: integration
        ref: cgb_speed_mutant_m7_xfail_ppu_control
        status: pass
      - kind: integration
        ref: cgb_speed_xfail_dma_restart
        status: pass
      - kind: integration
        ref: cgb_speed_mutant_m14_xfail_dma_restart
        status: pass
      - kind: integration
        ref: cgb_speed_xfail_hdma_fails_closed_negative
        status: pass
      - kind: integration
        ref: cgb_speed_xfail_stop_oam_unchanged_negative
        status: pass
  - id: CGB-06-SPEED-DISPOSITIONS
    description: All disposition rows are pinned to inventory tests, mirrored in the CGB profile, and protected by edited-reason and missing-pin controls.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: other
        ref: cgb_speed_dispositions
        status: pass
      - kind: other
        ref: cgb_speed_dispositions_mutated
        status: pass
      - kind: other
        ref: cgb_speed_dispositions_pinned_by_missing
        status: pass
      - kind: other
        ref: cgb_external_dispositions
        status: pass
      - kind: other
        ref: cgb_external_dispositions_mutated
        status: pass
  - id: CGB-06-AGE-SENSITIVITY
    description: Every admitted AGE ROM is compared against clean behavior for all four stall and DIV mutants, with required DIV discrimination retained for M6, M21, and M27.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: age_sensitivity_m6
        status: pass
      - kind: integration
        ref: age_sensitivity_m21
        status: pass
      - kind: integration
        ref: age_sensitivity_m28
        status: pass
      - kind: integration
        ref: age_sensitivity_m27
        status: pass
      - kind: integration
        ref: age_sensitivity_m28_reference_mutated
        status: pass
  - id: CGB-06-M28-SCOPE
    description: The M28 test mutant is limited to double-speed destinations and the normal-speed transition invariant is pinned independently.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_speed_m28_normal_unchanged
        status: pass
      - kind: unit
        ref: cgb_speed_m28_normal_unchanged_control
        status: pass
      - kind: integration
        ref: age_sensitivity_m28
        status: pass
  - id: CGB-06-FULL-SUITE
    description: The complete configured local CTest inventory passes after the plan changes.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -j8 (895/895)"
        status: pass
---

# Phase 12 Plan 17: Disposition Pins and Stall Sensitivity Summary

**Unresolved speed-switch behavior now has explicit current-core pins, and four-mutant AGE sensitivity is recorded without tuning the measured stall constant.**

## Performance

- **Duration:** At least 23 minutes, measured from the first task commit because the executor start timestamp was not captured.
- **Completed:** 2026-10-13.
- **Tasks:** 3.
- **Files modified:** 8.
- **Full-suite verification:** 895/895 CTests passed in 40.90 seconds.

## Accomplishments

- Added pins for PPU output during the speed-switch pause, OAM DMA restart timing, fail-closed HDMA5 writes, and unchanged OAM across switching STOP. Each has a meaningful mutant or targeted-input negative control.
- Completed the CGB speed disposition manifest and CGB profile mirror. The verifier checks all 35 rows, documented reasons, AGE manifest membership, exact SHA-256 formats, and every `pinned_by` test against the registered inventory. Edited-reason and missing-test controls both reject their mutated copies; Phase 11 disposition checks still pass and its files are unchanged.
- Swept all 13 admitted AGE ROMs with M6, M21, M28, and M27 against the clean committed-core result. `spsw-div-cgbBCE` remains discriminating for M6, M21, and M27. The corrected M28 mutant changes the measured result for `spsw-mode0-cgbBCE`, while `spsw-div-cgbBCE` remains insensitive to its low-bit change.
- Kept core behavior and the stall constant unchanged. The source revision used for the sweep was `db1dd7b9635752c96f99f76fd9f2594ad80af5d1`; identity pins and fixture bytes remain unchanged.

## Task Commits

1. **Task 1: Pin speed-switch PPU output disposition** — `9f6980ee80098ebd80d7b6d773fcfd5f3f5fae13`.
2. **Task 2: Pin remaining speed-switch dispositions** — `1dbf868d676c94eda34f86702b24be888fd575bd`.
3. **Task 3: Enforce AGE stall sensitivity** — `6808783a00ae83d69a2ed405057f7a6ebbaee5e8`.

## Decisions Made

- Pin unresolved behavior to measured current-core behavior and preserve explicit negative controls so a future implementation change must revisit the disposition.
- Corrected the M28 test mutant to add one half-dot only when the transition enters double speed. The all-ROM remeasurement still shows an `spsw-mode0-cgbBCE` change, so that measured sensitivity is recorded; only the DIV ROM remains insensitive to the mutant's low-bit change.
- Keep expected-failure and expected-unsupported labels scoped to their declared model and evidence. The measurements are software-model results, not hardware receipts.

## Deviations from Plan

**1. Corrected M28 mutation scope and recorded the measured mode-0 sensitivity.**

- **Found during:** Task 3 sensitivity verification.
- **Issue:** The initial M28 harness mutation added one half-dot to transitions in both directions, while the plan defines M28 as adding the half-dot when switching to double speed. Its initial AGE result conflicted with the plan's blanket expectation that AGE would not detect M28.
- **Fix:** Restricted M28 to double-speed destination transitions, added a normal-speed unchanged test and control, and reran all 13 admitted AGE ROMs against M28.
- **Result:** `spsw-mode0-cgbBCE` changes; `spsw-div-cgbBCE` does not. The JSON, verifier, and docs now preserve both results without changing core behavior or fitting the stall constant.
- **Files modified:** `cmake/P12Mutants.cmake`, `tests/test_cgb_speed_internal.c`, `tests/CMakeLists.txt`, `tests/external/cgb-speed-dispositions.json`, `tests/scripts/verify-cgb-speed-dispositions.py`, `docs/cgb-profile.md`.
- **Commit:** `6808783a00ae83d69a2ed405057f7a6ebbaee5e8`.

**Total deviations:** 1 evidence-driven test-mutant scope correction.

## Self-Check: PASSED

- Summary file exists at the expected phase path.
- All three task commits are ancestors of the current plan head.
- The new summary coverage block passes `summary_coverage` (1/1).
