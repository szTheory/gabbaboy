---
phase: GB-03-visible-interactive-dmg
plan: 12
subsystem: testing
tags: [DMG, OAM-DMA, FF46, Mooneye, C17]
requires:
  - phase: GB-03-visible-interactive-dmg
    provides: Instance-owned DMA state, bus access restrictions, and registered guest test harness
provides:
  - Active-DMA FF46 readback and restart writes reach the bounded DMA register handler
  - Guest regressions for startup copy, accepted restart completion, register readback, and existing access/source boundaries
  - Provenance-qualified startup/restart/readback evidence while simultaneous PPU/DMA arbitration and JOYP IF remain open
affects: [phase-03-verification, dma, video-evidence]
actuals:
  tokens: 10389.25
  tasks: 2
  commits: 7
tech-stack:
  added: []
  patterns: [original HRAM guest probes with timestamped bus and DMA observers]
key-files:
  created: []
  modified:
    - src/core/gabbaboy.c
    - tests/test_dma.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - docs/dmg-video-evidence.md
    - .planning/phases/GB-03-visible-interactive-dmg/03-VERIFICATION.md
key-decisions:
  - Keep the first fresh-transfer M-cycle CPU-accessible, then apply the existing active-DMA access gate when the first byte transfers; admit FF46 reads/writes as the only later non-HRAM exception.
  - Treat pinned Mooneye DMG-family results and its documented CPU-B test fleet as upstream suite evidence, not as a project physical CPU-B observation because per-test/per-unit logs are unavailable.
patterns-established:
  - Keep source-backed DMA register/start/restart checks in original guest ROMs and register each case exactly once in both CTest and the expected inventory.
requirements-completed: []
coverage:
  - id: D1
    description: Active FF46 reads and restart writes preserve the latest register value and bounded replacement transfer behavior.
    requirement: VIDEO-02
    verification:
      - kind: unit
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^dma_(start|restart|register_readback|hram|source_mapping)$'"
        status: pass
      - kind: unit
        ref: "tests/test_dma.c#dma_restart (restart+1272 `$FF`, restart+1288 `$01`)"
        status: pass
    human_judgment: false
  - id: D2
    description: DMA evidence records exact pinned assertions, source provenance limits, D-024, and unresolved arbitration boundaries.
    requirement: VIDEO-02
    verification:
      - kind: other
        ref: "docs/dmg-video-evidence.md#DMA-and-access-evidence-matrix"
        status: pass
    human_judgment: true
    rationale: Pinned suite fleet provenance does not include per-test/per-unit records, and the open simultaneous PPU/DMA claim needs model-applicable evidence beyond software regression.
  duration: "~30min (exact start not captured)"
completed: 2026-10-07
status: complete
plan_head_before: 905bed7b1959a1e1f438cb7da6ffdfa468f152d9
plan_head_after: 17d96b0a14bf9e64f97466686ffe60cb494cd9c9
---

# Phase 3 Plan 12: FF46 DMA Restart and Readback Summary

**Fresh DMA startup, active FF46 restart, and register readback now follow the pinned DMG-family assertions in the bounded per-instance path, with the remaining Phase 3 evidence limits kept open.**

## Performance

- **Duration:** Approximately 30 minutes; execution began before the first task commit, and the exact start time was not captured.
- **Started:** Not captured.
- **Completed:** 2026-10-07T18:46:13-04:00.
- **Tasks:** 2.
- **Files modified:** 6 implementation, test, and evidence files, plus this summary.

## Accomplishments

- Added the targeted active FF46 readback guest first and confirmed its RED evidence with `gsd_run check tdd-red-evidence` (`RED_EVIDENCE_OK`). The target failed on the active register read assertion, not on setup or test discovery.
- Added a second RED/GREEN guest slice for the fresh-transfer M=1 OAM access window; its RED assertion showed the core gated the first OAM fetch one cycle too early.
- Allowed FF46 reads and writes through the active-DMA bus gate while retaining the existing 160-byte transfer handler, other non-HRAM restrictions, and the `$8000–$DFFF` source policy.
- Added instance-owned DMA startup gate state so the first M-cycle remains accessible and ordinary DMA CPU restrictions begin with the first transferred byte.
- Added startup, accepted restart, exact replacement completion, and register-readback cases. The restart guest observes FE00=`$FF` at restart+1272 half-dots and FE00=`$01` at restart+1288 half-dots; the PPU is disabled for this probe.
- The fresh-start guest executes `INC B` from OAM during M=1, then sees the first `$D7` DMA byte at start+8 half-dots. The upstream B/C/D/E tuple remains attributed to its pinned source; the owned guest does not claim to reproduce every final register.
- Updated the evidence matrix and Phase 3 verification report to distinguish upstream DMG-family assertion tables and fleet documentation from this project's physical-hardware evidence.

## Verification

- Focused CTest: `dma_start`, `dma_restart`, `dma_register_readback`, `dma_hram`, and `dma_source_mapping` passed (5/5).
- Full core CTest: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` passed (134/134).
- `git diff --check` passed. Every new test name appears exactly once in the CMake registration and once in `tests/expected-tests.txt`.
- Source comparison used immutable Mooneye revision `31510e12eea6286d36eea060a6adde755e1067aa`: `acceptance/oam_dma_start.s`, `acceptance/oam_dma_restart.s`, and `acceptance/oam_dma/reg_read.s`. No Mooneye ROM, assembly, or fixture bytes were imported.

## Task Commits

1. **Task 1 RED:** `dd25d33` — add FF46 readback and DMA restart guests.
2. **Task 1 GREEN:** `bb9f59d` — allow active DMA FF46 restart and readback.
3. **Task 1 test refinement:** `a147813` — assert the active restart completion boundary.
4. **Task 1 RED:** `29516ec` — cover fresh DMA startup access window.
5. **Task 1 GREEN:** `a1a084a` — preserve the first DMA startup cycle.
6. **Task 2:** `056ed71` — record source-backed DMA evidence boundaries.
7. **Task 2 evidence correction:** `17d96b0` — qualify the fresh startup guest and tested verification revision.

The measured plan commit count is 7 from baseline `905bed7b1959a1e1f438cb7da6ffdfa468f152d9` through head `17d96b0a14bf9e64f97466686ffe60cb494cd9c9`.

## Decisions Made

- D-024 remains unchanged: the ROM-only model uses the `$8000–$DFFF` source envelope, and the `sources-GS.s` conflict remains explicit.
- The fresh-transfer first M-cycle remains CPU-accessible; later active DMA blocks non-HRAM CPU accesses except FF46 reads/writes.
- The upstream Mooneye pass tables and README fleet list inform the source-backed subcase, but unavailable per-unit logs mean they are not reported as a project physical observation.

## Deviations from Plan

**1. [Rule 2 - Missing Critical] Allow FF46 register reads during active DMA**
- **Found during:** Task 1 (End-to-end FF46 start, active restart, and readback guest path)
- **Issue:** The active-DMA read gate returned `$FF` for FF46 before the register handler, contradicting the pinned `acceptance/oam_dma/reg_read.s` readback assertions included in the task behavior.
- **Fix:** Exempted only FF46 reads from the active-DMA HRAM gate, matching the narrowly scoped FF46 write exception.
- **Files modified:** `src/core/gabbaboy.c`, `tests/test_dma.c`
- **Verification:** The RED target failed on the FF46 readback assertion before implementation; focused DMA tests and full core CTest passed after the fix.
- **Committed in:** `bb9f59d`.

**2. [Rule 1 - Bug] Preserve the fresh-transfer M=1 access window**
- **Found during:** Task 1 (End-to-end FF46 start, active restart, and readback guest path)
- **Issue:** The active-DMA gate blocked OAM instruction fetch immediately after FF46, while pinned `acceptance/oam_dma_start.s` asserts OAM remains accessible during M=1 and becomes blocked from M=2.
- **Fix:** Added per-instance startup-gate state that permits the first M-cycle, then enables the usual non-HRAM gate when the first DMA byte transfers.
- **Files modified:** `src/core/gabbaboy.c`, `tests/test_dma.c`
- **Verification:** The `dma_start` RED failed on B=`$01`; after the fix, the focused DMA set and full 134-case CTest suite passed.
- **Committed in:** `a1a084a`.

## TDD Evidence

- **RED:** `dma_register_readback` failed because its guest read of FF46 immediately after starting DMA did not return `$9F`. The unchanged TAP report was accepted as `RED_EVIDENCE_OK`; semantic inspection confirmed the target reached the intended guest assertion.
- **GREEN:** `bb9f59d` admits active FF46 reads/writes; focused and full core CTest passed.
- **Second RED/GREEN slice:** `dma_start` failed because the first OAM instruction was blocked; `RED_EVIDENCE_OK` validated the target assertion. Commit `a1a084a` preserves the M=1 startup window, after which focused and full core CTest passed.
- **REFACTOR:** No separate refactor was needed. The later test refinement added exact one-cycle-before/after assertions for replacement completion.

Both RED records were generated from real TAP output and passed the OpenGSD `tdd-red-evidence` classifier before their corresponding GREEN commits.

## Issues Encountered

The pinned suite reports DMG-family outcomes and documents a manually tested fleet that includes DMG-CPU-B, but the available source snapshot has no per-test/per-unit raw logs. Documentation and verification now preserve this limit explicitly.

## Known Stubs

None introduced by this plan.

## Next Phase Readiness

Phase 3 remains executing. VIDEO-02 stays open for simultaneous active PPU/DMA arbitration, and D-08/VIDEO-03 stays open for JOYP IF behavior. This plan closes only FF46 startup/restart/readback progress; it does not verify Phase 3 or authorize Phase 4.

## Self-Check: PASSED

All seven plan-owned implementation, test, documentation, and summary files exist, and all seven measured plan commits are ancestors of the current branch head.

---
*Phase: GB-03-visible-interactive-dmg*
*Completed: 2026-10-07*
