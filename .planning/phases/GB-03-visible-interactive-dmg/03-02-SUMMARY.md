---
phase: GB-03-visible-interactive-dmg
plan: "02"
subsystem: emulation
tags: [c17, ppu, fifo, stat, ctest]
requires:
  - phase: GB-03-visible-interactive-dmg
    provides: Timed background scanout, completed-frame copy, and timestamped guest input from Plan 03-01
provides:
  - Independent background/window/object shade-image coverage
  - Per-instance bounded PPU transfer state with variable mode-3 completion
  - Guest-visible LCD/STAT/LY/LYC and VBlank behavior with source-qualified timing tests
affects: [GB-03-03, GB-03-04, GB-03-05, GB-03-06, GB-03-07, GB-03-08, GB-03-09]
actuals:
  tokens: 15388
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns: [fixed per-instance PPU work queue, private PPU timing observer, source-applicability ledger]
key-files:
  created:
    - tests/test_ppu.c
    - docs/dmg-video-evidence.md
  modified:
    - src/core/gabbaboy.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "Use a fixed 16-slot pixel-work queue and four two-dot fetch stages; keep authored tile and object shading in the shared compositor at output time."
  - "Treat Pan Docs timing as a source-qualified bootless DMG expectation, not a physical DMG-CPU-B measurement."
  - "Reset the PPU dot phase on LCD enable/disable as deterministic emulator policy and record that limitation."
patterns-established:
  - "Keep private PPU timing events separate from guest bus events and public API output."
  - "Test transfer timing at observed guest bus phases and keep expected images independent of the renderer."
requirements-completed: [VIDEO-01, VIDEO-05]
coverage:
  - id: D1
    description: "Authored frames cover BG/window/sprite maps, palettes, scrolling, clipping, transparency, priority, flips, object size, and the ten-object line limit."
    requirement: VIDEO-01
    verification:
      - kind: integration
        ref: "tests/test_ppu.c#frame_composition_bg,frame_composition_window,frame_composition_sprites,frame_composition_priority"
        status: pass
    human_judgment: false
  - id: D2
    description: "Guest-visible LCD modes, SCX/window/object transfer penalties, STAT edges, LYC, VBlank, LY wrap, and run partition invariance have independent checks."
    requirement: VIDEO-01
    verification:
      - kind: integration
        ref: "tests/test_ppu.c#ppu_timing_modes,ppu_timing_stat,ppu_timing_lcd,ppu_timing_fetch,ppu_timing_partition"
        status: pass
    human_judgment: false
  - id: D3
    description: "Every asserted timing case is linked to a pinned primary documentation snapshot with CPU-B and electrical-FIFO limitations stated."
    requirement: VIDEO-05
    verification:
      - kind: other
        ref: docs/dmg-video-evidence.md
        status: pass
    human_judgment: false
duration: 30min
completed: 2026-10-07
status: complete
---

# Phase GB-03 Plan 03-02: DMG Composition and Timing Summary

**The shared renderer now composes independently authored BG/window/object images, while the timed PPU exposes variable transfer, LCD/STAT edges, VBlank, and LY wrap through bounded per-instance state.**

## Performance

- **Duration:** 30 minutes
- **Started:** 2026-10-07T17:43:00Z
- **Completed:** 2026-10-07T18:13:15Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added independently authored shade images for signed/unsigned tile addressing, map choice, SCX/SCY wrap, WX/WY clipping and line progression, palettes, sprite transparency/priority/order, 8×8 and 8×16 objects, flips, and the ten-object line limit.
- Replaced the fixed Mode 3 cutoff with a 16-slot per-instance work queue, four two-dot fetch stages, fine-scroll discard, window restart, and bounded object penalties. LCD mode, LY/LYC, the combined STAT condition line, VBlank IF, and deterministic LCD toggles now advance with the existing half-dot timeline.
- Added a separate private PPU event observer and five named timing tests, including exact guest STAT reads, LYC and combined-source edges, IF/LY polling, partition equivalence, and completed-frame equality.
- Pinned the Pan Docs source snapshot and documented the model scope, controls, and timing uncertainties in `docs/dmg-video-evidence.md`.

## Task Commits

1. **Task 1 RED:** `e9ea878` — failing window composition image.
2. **Task 1 GREEN:** `e5a16f6` — background, window, and object composition.
3. **Task 2 RED:** `41355ea` — failing SCX transfer-timing assertion.
4. **Task 2 GREEN:** `2e1fdc8` — LCD, STAT, and variable transfer timing.

## TDD Evidence and Verification

- **Task 1 RED:** `frame_composition_window` failed at authored pixel `(0,1)`: shade 1 was rendered where the window expected shade 2. `build/tdd-red-03-02-task1.json` was accepted as `RED_EVIDENCE_OK` / `target_test_failed`.
- **Task 2 RED:** `ppu_timing_fetch` observed the STAT read exactly 504 half-dots after LCD enable, then failed only because mode 0 was observed where SCX=3 expected mode 3. `build/tdd-red-03-02-task2.json` was accepted as `RED_EVIDENCE_OK` / `target_test_failed`.
- The Plan 03-02 verification selection passed **14/14**, including all composition/timing cases and existing output-capacity, event-partition, HALT/timer-partition, and STOP regressions.
- `git diff --check` passed. The full offline inventory and sanitizer lane remain part of Phase 3 closeout.

## Evidence Limits and Threat Mitigations

- Pan Docs is the pinned primary documentation source. These tests are source-qualified expectations applied to the bootless DMG-CPU-B profile; no physical CPU-B observation occurred.
- The 16-slot queue tracks bounded output-pixel slots; the compositor resolves tile and object shade when a slot is emitted. This does not claim electrical or revision-specific equivalence of internal DMG FIFO contents.
- T-03-05 uses fixed queue, frame, and object arrays with guarded screen and tile indices. T-03-06 advances one dot at a time with at most ten selected objects and finite queue operations. No new dependency was added for T-03-12.
- OAM DMA, memory contention, STAT-write transients, mid-line register mutation, negative/offscreen sprite timing, X=0 with nonzero SCX, and physical-hardware behavior remain outside this plan's evidence.

## Decisions Made

- Keep pixel composition in one production renderer shared by the player and test guest. The timing queue carries screen-pixel slots while the compositor calculates final shades at output.
- Reset the PPU dot phase on LCD enable/disable as a deterministic bootless policy; do not present that policy as a measured CPU-B edge.
- Keep PPU events private to tests and separate from the guest bus observer so existing bus event counts remain stable.

## Deviations from Plan

None. No dependency was added. The timing implementation and tests preserve the existing finite run model; full-suite and Linux sanitizer evidence are pending Phase 3 closeout.

## User Setup Required

None.

## Next Phase Readiness

Plan 03-03 is next: model timed OAM DMA and CPU/PPU memory contention, using the new per-dot PPU mode and access state. Continue with `$gsd-execute-phase 3 --wave 3`. Phase 3 remains executing; do not advance to Phase 4.

---
*Phase: GB-03-visible-interactive-dmg*
*Completed: 2026-10-07*
