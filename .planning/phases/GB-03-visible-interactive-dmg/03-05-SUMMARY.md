---
phase: GB-03-visible-interactive-dmg
plan: "05"
subsystem: player/input
tags: [sdl3, deterministic-input, clock-mapping, optional-player]

# Dependency graph
requires:
  - phase: GB-02-dmg-cpu-bus-and-time
    provides: bounded instance API, timestamped event queue, and copied frame interface
provides:
  - Opt-in SDL3 player that copies and renders owned-demo frames
  - Checked host-nanosecond to guest-half-dot mapping and bounded keyboard adapter
  - Focus-loss release recovery with eight queue slots reserved beyond normal input
affects: [GB-03-06, GB-03-09, phase-3-verification]

# Actuals
actuals:
  tokens: 10901
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: [optional SDL3 3.4.18]
  patterns: [offscreen SDL software-renderer smoke, quotient/remainder clock conversion, adapter-owned pending-event reconciliation]

key-files:
  created:
    - tests/player/test_input.c
  modified:
    - CMakeLists.txt
    - src/player/main.c
    - src/player/input.c
    - src/player/input.h
    - tests/player/CMakeLists.txt
    - tests/player/expected-tests.txt
    - tests/scripts/verify-phase3-player.sh

key-decisions:
  - "Keep SDL discovery and linking behind the OFF-by-default GABBABOY_BUILD_PLAYER option."
  - "Map SDL timestamps at 8,388,608 half-dots per second with checked integer arithmetic; keep host clock state outside the core."
  - "Limit ordinary player events to 56 outstanding entries so releases for all eight held buttons fit atomically on focus loss."
  - "Pin SDL3 3.4.18 from the official immutable release and verify its published source digest before building."

patterns-established:
  - "Record adapter queue capacity before core admission so accepted core events cannot be lost from the adapter's reconciliation mirror."
  - "Use SDL_PushEvent and a software renderer for deterministic headless player smoke without requiring a desktop session."

requirements-completed: []

coverage:
  - id: D1
    description: "The opt-in SDL player copies a completed frame and an injected A press/release reaches the owned demo's deterministic guest result."
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh#player_smoke"
        status: pass
    human_judgment: false
  - id: D2
    description: "Checked time conversion, stable event ordering, key mapping, repeat handling, pause/resume, reset and focus-loss release recovery are covered."
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh#player_input_events,player_input_focus,player_input_time"
        status: pass
    human_judgment: false
  - id: D3
    description: "The normal SDL window has not received a live visual/perceptual check in the current environment because no desktop display is available."
    verification: []
    human_judgment: true
    rationale: "Automated smoke verifies copied frames and SDL rendering through an offscreen software renderer, but cannot judge the native desktop window. The smallest follow-up is to launch the optional player on a desktop and confirm the demo is visible and responsive."

# Metrics
duration: 19 min
completed: 2026-10-07
status: complete
---

# Phase GB-03 Plan 05 Summary

**An optional SDL3 player now renders copied demo frames and maps keyboard events deterministically onto the bounded guest input queue.**

## Performance

- **Duration:** 19 min
- **Started:** 2026-10-07T19:44:55Z
- **Completed:** 2026-10-07T20:03:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Added an OFF-by-default SDL3 player target; default configuration stays SDL-free.
- Added an official SDL3 3.4.18 source download and digest check to the opt-in verification helper.
- Added checked nanosecond/half-dot conversion, SDL key mapping, stable late-event ordering, repeat suppression, pause/resume rebasing, reset, and focus-loss release recovery.
- Added an offscreen SDL event/render smoke and three adapter test cases for timing, transitions, queue capacity, and recovery.

## Task Commits

1. **Task 1: Add the optional SDL player path from demo ROM to copied frames** — `a5aae82` (`feat(GB-03-05): add optional SDL player smoke`)
2. **Task 2: Make host input timestamps and focus-loss releases deterministic** — `9ef104a` (`feat(GB-03-05): make player input timeline deterministic`)

Plan metadata is recorded in the follow-up documentation commit.

## Files Created/Modified

- `CMakeLists.txt` — optional player build flag and exact SDL package requirement.
- `src/player/main.c` — demo loading, copied-frame conversion/rendering, SDL event loop, and finite smoke path.
- `src/player/input.c`, `src/player/input.h` — checked clock mapping, input scheduling, pause/reset, and focus-loss recovery.
- `tests/player/test_input.c` — timing, key transitions, capacity boundary, and recovery tests.
- `tests/player/CMakeLists.txt`, `tests/player/expected-tests.txt` — nonempty optional player test inventory.
- `tests/scripts/verify-phase3-player.sh` — digest-checked SDL acquisition and optional player verification.

## Decisions Made

- SDL remains isolated to the optional player target; the ordinary core build and tests do not discover SDL.
- SDL timestamps map to the 8,388,608 Hz DMG half-dot clock through quotient/remainder math, avoiding multiplication of arbitrary host timestamps.
- The adapter reserves eight of its 64 pending event slots for releasing every possible held button after focus loss.
- The upstream pin was updated to SDL3 3.4.18, whose release includes a macOS quit/window lifecycle fix relevant to this player.

## Deviations from Plan

None. The helper smoke uses an offscreen SDL software renderer as specified for headless verification; the normal native window could not be visually exercised because this environment has no desktop display.

## Issues Encountered

- The first rerun found a test-dispatcher call missing its demo-path argument. It was corrected before the task commit, and the optional inventory then passed.
- Review found that adapter capacity should be preflighted before mutating the core queue. The input adapter now checks its mirror capacity before core admission.

## User Setup Required

None for build or automated verification. A desktop visual check remains outstanding because no display is available in this environment.

## Next Phase Readiness

Wave 6 / Plan 03-06 can add ROM replacement, session controls, visible status and integer high-DPI presentation. The Phase 3 evidence gates for simultaneous PPU/DMA collisions and exact JOYP interrupt timing remain open; no physical DMG-CPU-B observation occurred.

---
*Phase: GB-03-visible-interactive-dmg*
*Completed: 2026-10-07*
