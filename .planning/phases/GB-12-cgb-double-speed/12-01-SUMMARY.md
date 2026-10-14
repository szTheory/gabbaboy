---
phase: 12-cgb-double-speed
plan: 01
subsystem: cgb-speed-switch
tags: [cgb, key1, stop, half-dot-timeline, regression-pins]
requires:
  - phase: 11-cgb-colour-rendering-and-player-colour
    provides: "CGB mode, RGB555 frames, colour fixtures and model-gate contracts"
provides:
  - "Eight pre-change CGB single-speed FNV-1a identity pins over seven fixtures and an inline timer/serial/DMA guest"
  - "CGB KEY1/STOP double-speed transition at instruction retirement with persisted bounded stall consumption"
  - "Private speed-state test seam and trace/budget regression coverage"
affects: [12-02, 12-03, 12-05, 12-06, 12-07, 12-08, 12-09]
actuals:
  tokens: 9177
  tasks: 2
  commits: 2
  plan_head_before: aac4772aa2735062d2469e05b11de038c3ea2d08
  plan_head_after: 43114cb3f7987d4da95369843cfbcab67658e210
tech-stack:
  added: []
  patterns:
    - "White-box test translation unit includes the core source without linking the core library"
    - "STOP retirement switches speed and hands a persistent stall to a dedicated run-loop branch"
key-files:
  created:
    - tests/test_cgb_speed_internal.c
  modified:
    - src/core/gabbaboy.c
    - src/core/gabbaboy_test.h
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/test_cgb_visibility.c
    - tests/test_cgb_tables.c
    - docs/cgb-profile.md
key-decisions:
  - "Record the eight single-speed pins at pre-phase head fb45111 before the core changes; they are software regression identities, not hardware evidence."
  - "Keep speed state and its getter private to the core test seam; the public header and ABI remain unchanged."
  - "Represent STOP's 2 M cost in normal-speed half-dots and apply the speed shift once in instruction_cost."
patterns-established:
  - "The speed-switch stall consumes one CPU M-cycle per run-loop iteration while advancing the shared master timeline."
requirements-completed: [CGB-06]
coverage:
  - id: D1
    description: "Pre-change CGB frame, PCM and inline timer/serial/DMA identity pins detect altered output."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_speed_identity_pin
        status: pass
      - kind: unit
        ref: cgb_speed_identity_pin_flipped
        status: pass
      - kind: unit
        ref: cgb_speed_internal_harness_alive
        status: pass
  - id: D2
    description: "Armed CGB STOP switches at retirement, exposes KEY1 speed, consumes a resumable stall, and emits only the STOP trace record."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_speed_tracer_switch
        status: pass
      - kind: unit
        ref: cgb_stop_armed_cgb
        status: pass
      - kind: unit
        ref: cgb_stop_unarmed_cgb
        status: pass
      - kind: unit
        ref: cgb_stop_compat_ignores_key1
        status: pass
      - kind: unit
        ref: cgb_stop_dmg_control
        status: pass
  - id: D3
    description: "KEY1 documentation, model-gate declarations and existing DMG identity remain consistent."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_tables_io
        status: pass
      - kind: unit
        ref: model_gates
        status: pass
      - kind: other
        ref: bash tests/scripts/verify-dmg-baseline.sh
        status: pass
duration: 10 min
completed: 2026-10-13
status: complete
commits: 2
---

# Phase 12 Plan 01: CGB speed-switch tracer Summary

Eight CGB single-speed output pins now protect the unmodified core baseline, and the first production speed switch completes through KEY1, STOP retirement and a bounded destination-speed stall.

## Accomplishments

- Recorded seven fixture identities over 30 frames of RGB555 and PCM output, plus one inline guest identity covering timer, serial and OAM DMA. The flipped-pin test proves the baseline gate can fail.
- Implemented KEY1 bit 7, CGB-only armed STOP selection, DIV/APU edge reset, speed-scaled CPU timing sites, and a persisted stall branch with audio and overflow preflights.
- Added private speed-state inspection and verified budget partitioning, KEY1 readback, STOP-only trace output, the unchanged unarmed/compat/DMG paths, model gates, and the existing DMG baseline.

## Performance

- **Duration:** 10 min
- **Started:** 2026-10-13T16:48:13Z
- **Completed:** 2026-10-13T16:57:52Z
- **Tasks:** 2
- **Files modified:** 8

## Task Commits

1. **Task 1: Pre-change CGB single-speed identity pin** - `9dfc604` (`test`)
2. **Task 2: KEY1/STOP speed-switch tracer** - `43114cb` (`feat`)

## Decisions Made

- The identity digests were recorded from the unmodified core at `fb45111`; they are software regression pins, not hardware evidence.
- Speed state remains private to the core and test seam. No public header or API symbol changed.
- The CGB inline guest waits for its internal-clock transfer to complete before reading SB, since active-transfer SB reads are fail-closed by the existing bus model.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Wait for serial completion before sampling SB in the baseline guest**
- **Found during:** Task 1
- **Issue:** Immediate SB reads while the internal-clock transfer was active correctly stopped at `$FF01` with `GBB_STOP_UNSUPPORTED_BUS`, preventing the requested fixed-budget identity digest.
- **Fix:** Added a guest delay before starting OAM DMA and collecting the 64 register samples, so the transfer completes before SB is read.
- **Files modified:** `tests/test_cgb_speed_internal.c`
- **Verification:** `cgb_speed_identity_pin` and its flipped negative control passed.
- **Committed in:** `9dfc604`

**2. [Rule 3 - Blocking] Correct the flipped-pin CTest wrapper arguments**
- **Found during:** Task 1
- **Issue:** The first CMake registration passed `GBB_COMMAND`/`GBB_ARGUMENTS`, while `expect_exit.cmake` requires `GBB_CMD`.
- **Fix:** Passed the executable and arguments through the expected `GBB_CMD` list.
- **Files modified:** `tests/CMakeLists.txt`
- **Verification:** `cgb_speed_identity_pin_flipped` passed and matched `observed` with exit code 1 from the test program.
- **Committed in:** `9dfc604`

**Total deviations:** 2 auto-fixed. Both corrected test harness issues within planned scope.

## Verification

- `cmake --preset phase1 && cmake --build --preset phase1`: passed.
- The plan regression selection passed **47/47**, including speed pins and negative control, STOP controls, CGB table/doc contract, model gates, visibility matrix, banking digest and DMG identity checks.
- `bash tests/scripts/verify-dmg-baseline.sh`: `baseline status=pass`.
- `ctest --test-dir build -R '^summary_coverage$' --output-on-failure --no-tests=error`: passed.
- The identity task commit contains no core edit; no public header change was made.

## Known Stubs

None.

## Self-Check: PASSED

The test driver exists, both task commits are ancestors of the recorded plan head, and the plan coverage contract passes.

---
*Phase: 12-cgb-double-speed*
*Completed: 2026-10-13*
