---
phase: GB-03-visible-interactive-dmg
plan: "06"
subsystem: player/session
tags: [sdl3, rom-loading, high-dpi, integer-scaling]

# Dependency graph
requires:
  - phase: GB-03-visible-interactive-dmg
    provides: Optional SDL3 player, timestamped input adapter, and copied-frame interface
provides:
  - Bounded transactional ROM replacement and session controls in the optional player
  - Integer-scaled, pixel-aligned high-DPI presentation with software pixel-readback checks
  - User-facing control, status, error, and limitation documentation
affects: [GB-03-07, GB-03-09, phase-3-verification]

# Actuals
actuals:
  tokens: 13273
  tasks: 2
  commits: 1

# Tech tracking
tech-stack:
  added: []
  patterns: [bounded transactional session replacement, event-loop ownership of async dialog results, pixel-aligned SDL logical presentation]

key-files:
  created:
    - src/player/session.c
    - src/player/session.h
    - src/player/presentation.c
    - src/player/presentation.h
    - tests/player/test_session.c
    - tests/player/test_presentation.c
    - docs/preview.md
  modified:
    - CMakeLists.txt
    - src/player/main.c
    - tests/player/CMakeLists.txt
    - tests/player/expected-tests.txt

key-decisions:
  - "Keep ROM replacement in the optional adapter, cap path and file sizes, and replace the active session only after the core accepts the new image."
  - "Copy asynchronous SDL dialog results into owned event data before callback return; mutate the core only on the main event loop."
  - "Use SDL integer logical presentation with a checked whole-pixel origin correction for odd drawable sizes."
  - "Keep audio and save persistence explicitly unavailable and visible in the player documentation and status."

patterns-established:
  - "File replacement failure preserves the active guest, path, and frame generation; successful replacement resets the guest."
  - "Test software renderer output pixels as well as pure geometry when validating high-DPI placement."

requirements-completed: [VIDEO-04, VIDEO-05]

coverage:
  - id: D1
    description: "ROM replacement and session controls use bounded loading; invalid, oversized, truncated, or unsupported files preserve the current guest while successful replacement resets it."
    requirement: VIDEO-04
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh; CTest player_session_replacement_failure and player_session_replacement_success"
        status: pass
    human_judgment: false
  - id: D2
    description: "Player layouts preserve integer scale, pixel alignment, centering, and undersize handling across native, odd, letterboxed, and high-density drawable sizes."
    requirement: VIDEO-04
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh; CTest player_presentation_*"
        status: pass
    human_judgment: false
  - id: D3
    description: "The native desktop window and its status text have not received a live visual check because no desktop display is available in this environment."
    requirement: VIDEO-04
    verification: []
    human_judgment: true
    rationale: "Offscreen software-renderer readback verifies pixels and geometry but cannot judge the native window's perceptual presentation. The smallest follow-up is to launch the optional player on a desktop, open the included demo, and check the visible controls and status."

# Metrics
duration: 15 min
completed: 2026-10-07
status: complete
---

# Phase GB-03 Plan 06 Summary

**The optional SDL player now supports safe ROM replacement, keyboard/session controls, visible limitations, and pixel-aligned integer presentation.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-10-07T20:03:00Z
- **Completed:** 2026-10-07T20:18:12Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments

- Added bounded ROM file loading, transactional replacement, reset/pause behavior, native open/quit shortcuts, and an in-app controls/help view.
- Kept asynchronous dialog callbacks from mutating core state; the callback copies its result into owned event data for the main event loop.
- Added an overflow-safe integer presentation helper and checked SDL software-rendered pixels at native, odd, letterboxed, and high-density sizes.
- Documented supported images, controls, and current audio/save/hardware limitations in `docs/preview.md`.

## Task Commits

1. **Tasks 1–2: Add bounded ROM/session controls and integer high-DPI presentation** — `cd12a52` (`feat(GB-03-06): add ROM controls and integer presentation`)

Plan metadata is recorded in the follow-up documentation commit.

## Files Created/Modified

- `src/player/session.c`, `src/player/session.h` — bounded loading and transactional session replacement.
- `src/player/presentation.c`, `src/player/presentation.h` — overflow-safe integer layout calculation.
- `src/player/main.c` — keyboard/menu behavior, async file-dialog handoff, visible status, and pixel-aligned rendering.
- `tests/player/test_session.c`, `tests/player/test_presentation.c` — failure preservation, reset, geometry, and renderer pixel tests.
- `tests/player/CMakeLists.txt`, `tests/player/expected-tests.txt`, `CMakeLists.txt` — optional player test/build integration.
- `docs/preview.md` — supported ROM scope, controls, and limitations.

## Decisions Made

- ROM selection is bounded to the supported 32 KiB ROM-only format and 4096-byte paths; the previous guest survives any failed replacement.
- SDL's asynchronous file dialog callback copies selection bytes into an owned event before returning; the main loop owns app and guest mutation.
- SDL logical integer scaling remains enabled; an offset aligns odd-size drawable output to whole pixels, and sub-native surfaces do not render a partial frame.
- Audio, save persistence, and live hardware qualification remain explicit limitations.

## Deviations from Plan

None. During implementation, a generated truncated-file case was corrected to ensure it reached the intended loader branch, and an odd-size renderer offset was aligned after pixel readback exposed a half-pixel origin. Both corrections are included in the implementation and verified tests.

## Issues Encountered

- The first truncated-file test reused an invalid fixture whose header failed before the truncation check. It now creates a deterministic 128-byte image so the test exercises the intended branch.
- SDL's centered viewport can use half-pixel origins for odd drawable dimensions. The player corrects the logical destination to a whole-pixel origin, and pixel readback verifies the final edge placement.

## User Setup Required

None for automated verification. A native desktop visual check remains outstanding because this environment has no desktop display.

## Next Phase Readiness

Wave 7 / Plan 03-07 can harden public frame/event failure behavior and relocated C/C++ consumers. Phase 3 still has open JOYP interrupt timing (D-08), simultaneous PPU/DMA applicability (VIDEO-02), and live desktop perception limits; Plans 03-08 and 03-09 still own fixture reproduction and hosted package qualification. No physical DMG-CPU-B observation occurred.

---
*Phase: GB-03-visible-interactive-dmg*
*Completed: 2026-10-07*
