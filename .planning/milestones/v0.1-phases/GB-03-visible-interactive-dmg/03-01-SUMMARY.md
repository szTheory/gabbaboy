---
phase: GB-03-visible-interactive-dmg
plan: "01"
subsystem: emulation
tags: [c17, ppu, joypad, rgbds, ctest]
requires:
  - phase: GB-02-dmg-cpu-bus-and-time
    provides: Timed CPU/bus execution, ROM-only loading, deterministic instance ownership, and bounded timestamped events
provides:
  - Instance-owned dot-stepped background rendering and bounded completed-frame copy API
  - Active-low FF00 polling and timestamped button press/release events
  - Original bootless interactive ROM fixture with rights, protocol, and digest metadata
affects: [GB-03-02, GB-03-03, GB-03-04, GB-03-05, GB-03-07, GB-03-08]
actuals:
  tokens: 7622
  tasks: 1
  commits: 2
tech-stack:
  added: []
  patterns: [instance-owned fixed frame buffers, emulated-time input events]
key-files:
  created:
    - fixtures/visible-demo/demo.asm
    - fixtures/visible-demo/demo.gb
    - fixtures/visible-demo/manifest.json
    - fixtures/visible-demo/LICENSE.txt
  modified:
    - include/gabbaboy/gabbaboy.h
    - src/core/gabbaboy.c
    - tests/test_tracer.c
    - tests/test_bus.c
requirements-completed: [VIDEO-01, VIDEO-03, VIDEO-05]
coverage:
  - id: D1
    description: The production core returns independently checked 160x144 DMG background shade frames through a bounded caller-owned copy.
    requirement: VIDEO-01
    verification:
      - kind: integration
        ref: tests/test_tracer.c#frame_composition_tracer
        status: pass
    human_judgment: false
  - id: D2
    description: Timestamped A press/release toggles and restores the visible tile with equal whole and partitioned execution results.
    requirement: VIDEO-03
    verification:
      - kind: integration
        ref: tests/test_tracer.c#joypad_gameplay_tracer
        status: pass
    human_judgment: false
  - id: D3
    description: The original fixture has explicit MIT rights, bootless profile/protocol metadata, and reproducible pinned-tool bytes.
    requirement: VIDEO-05
    verification:
      - kind: unit
        ref: visible_fixture_digest and RGBDS 1.0.1 source-to-byte cmp
        status: pass
    human_judgment: false
duration: 20min
completed: 2026-10-07
status: complete
---

# Phase GB-03 Plan 03-01: Visible Interactive Tracer Summary

The bootless polling guest now draws and toggles an independently checked background frame through a bounded copy API.

## Performance

- **Duration:** 20 minutes
- **Started:** 2026-10-07T17:23:31Z
- **Completed:** 2026-10-07T17:43:00Z
- **Tasks:** 1
- **Files modified:** 10

## Accomplishments

- Added fixed per-instance VRAM and shade buffers, dot progression inside `advance_devices_to`, LCD/LY/palette/scroll registers, and a copied 160x144 frame with generation and completion time.
- Added explicit button values and press/release events; FF00 reads combine selected active-low rows while STOP_WAKE remains separate.
- Added the original RGBDS-built 32 KiB polling guest, authored expected image, visible A-button change/restore, WRAM result markers, and byte digest.
- Verified image composition, scripted gameplay, release restoration, whole-versus-partitioned execution, and fixture digest independently.

## Task Commits

1. **RED: Add failing frame and gameplay tracer assertions** — `a21f94b` (`test`)
2. **GREEN: Render timed background frames and polling input** — `60f6498` (`feat`)

Plan metadata is included in the documentation commit that records this summary and progress.

## Files Created/Modified

- `include/gabbaboy/gabbaboy.h` — button events, frame metadata, bounded copy contract, and honest reset/input behavior.
- `src/core/gabbaboy.c` — per-instance BG scanout, copied completed frames, joypad matrix, and bounded event validation.
- `fixtures/visible-demo/` — owned assembly and 32 KiB ROM, MIT notice, profile/protocol, RGBDS pin, and SHA-256.
- `tests/test_tracer.c` — independent authored-image, input response, restoration, and partition checks.
- `tests/test_bus.c` — treats FF00 as implemented rather than an unsupported I/O address.

## Decisions Made

- The first renderer is a background-only baseline. Its deterministic dot path is not a claim of exact raster timing, window/object behavior, or physical DMG-CPU-B observation.
- Frame output is one byte per pixel, shade 0–3, copied from fixed instance storage; no borrowed buffer or run-time allocation is exposed.
- Button polling is active-low and row-selected. No JOYP interrupt or wake behavior is claimed; D-08 remains a separate primary-source gate for Plan 03-04.

## Deviations from Plan

The existing unsupported-bus regression had listed FF00 as absent. Because this plan implements guest polling through FF00, `tests/test_bus.c` now excludes that address from its absent-I/O cases. Other unsupported regions remain covered; VRAM read/contention qualification is left to later plans.

**Total deviations:** 1 compatibility test update. **Impact:** required to keep the Phase 2 unsupported-address contract accurate after adding JOYP behavior.

## TDD Evidence and Verification

- **RED:** `frame_composition_tracer` ran and failed at the planned public frame-copy assertion. `gbb_copy_frame` returned `GBB_FRAME_NOT_READY` (13); the CTest JUnit report was accepted by `check tdd-red-evidence` as `RED_EVIDENCE_OK` / `target_test_failed`.
- **GREEN:** The three focused tracer/digest tests passed after the implementation, and the tracer feedback gate passed again at the final task revision.
- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` — **107/107 passed**.
- RGBDS `v1.0.1` rebuilt the checked-in fixture; `cmp` passed and SHA-256 is `38afb54b40f4b6612906c7a68e367199d8bff135508a39d7acdc996bf3d86530`.
- The fixture reproduction workflow and hosted receipt are scheduled in Plan 03-08; this plan makes no hosted reproduction claim.

## Issues Encountered

During implementation, the test run exposed that the authored tile planes must be interleaved per row and that release restoration must wait for a later VBlank. The fixture and expected-image/gameplay assertions now verify those observable behaviors. The first full-suite run also exposed the stale FF00 unsupported-address expectation; the update above resolved it.

## User Setup Required

None.

## Next Phase Readiness

Plan 03-02 can proceed on this working frame path. It owns the separate window/object composition and source-qualified LCD/STAT/fetch timing cases. Phase 3 remains in progress; exact JOYP interrupt behavior and physical hardware behavior are not established here.

## Self-Check: PASSED

All Plan 03-01 success criteria were re-run: production guest frame, visible press/release response, independent expected pixels, digest, focused tracer feedback, and full offline Phase 1 suite. No physical hardware claim was made.

---
*Plan: GB-03-visible-interactive-dmg/03-01*
*Completed: 2026-10-07*
