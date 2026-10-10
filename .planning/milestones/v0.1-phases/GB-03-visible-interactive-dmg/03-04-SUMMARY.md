---
phase: GB-03-visible-interactive-dmg
plan: "04"
subsystem: input/testing
tags: [joypad, dmg-cpu-b, deterministic-input, evidence-gate]

# Dependency graph
requires:
  - phase: GB-02-dmg-cpu-bus-and-time
    provides: timestamped bounded input queue and timed guest bus operations
provides:
  - Public JOYP active-low matrix and queue regression coverage
  - Audited D-08 source disposition documenting why exact interrupt timing remains unqualified
affects: [phase-3-player, phase-3-verification]

# Actuals (#2632)
actuals:
  tokens: 6185
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns: [finite guest probes for public input, explicit evidence gates for model-specific IRQ claims]

key-files:
  created: [tests/test_joypad.c]
  modified:
    - include/gabbaboy/gabbaboy.h
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - .planning/phases/GB-03-visible-interactive-dmg/03-RESEARCH.md
    - .planning/phases/GB-03-visible-interactive-dmg/03-VALIDATION.md
    - docs/dmg-video-evidence.md
    - .planning/STATE.md
    - .planning/.continue-here.md

key-decisions:
  - "Keep existing timestamped queue and active-low polling behavior; add direct finite guest coverage because the core already met the polling contract."
  - "Do not implement or test an exact JOYP IF edge until evidence supports expected DMG-CPU-B sample timestamps and selection interactions."

patterns-established:
  - "Keep matrix polling, queue determinism, and hardware interrupt qualification as separate evidence claims."

requirements-completed: []

coverage:
  - id: D1
    description: "Active-low JOYP row selection, independent instances, atomic queue behavior, equal-time ordering, reset, and partition determinism are covered by finite guest tests."
    verification:
      - kind: unit
        ref: "tests/test_joypad.c; ctest --preset phase1 --output-on-failure --no-tests=error -R '^(joypad_selection|joypad_queue_atomic|joypad_equal_time|joypad_partition)$'"
        status: pass
    human_judgment: false
  - id: D2
    description: "D-08's exact DMG-CPU-B JOYP interrupt timing is explicitly retained as an unresolved evidence gate."
    verification:
      - kind: other
        ref: "docs/dmg-video-evidence.md#joypad-matrix-and-interrupt-evidence"
        status: pass
    human_judgment: true
    rationale: "The available manual, hardware note, and die-derived schematic do not establish the exact model-specific sample cases; further source tracing or a hardware trace is required before interrupt behavior can be claimed."

# Metrics
duration: 11min
completed: 2026-10-07
status: complete
---

# Phase 3 Plan 03-04 Summary

**Public JOYP matrix and queue behavior now have direct tests, while unsupported DMG-CPU-B interrupt timing remains an explicit gate.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-10-07T19:34:20Z
- **Completed:** 2026-10-07T19:44:55Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments

- Added original guest-program tests for each button, P14/P15 rows, both/neither selection, simultaneous input, and per-instance state.
- Verified invalid and past events, atomic overflow rejection, full queue behavior, reset, equal-time caller order, and whole-versus-partitioned execution.
- The complete local offline suite passed 129/129 tests after integration.
- Audited Nintendo's Game Boy Programming Manual, a 2017 hardware research note, and a pinned DMG-CPU-B die-derived schematic set. Their available evidence does not determine the exact IF sampling phase or held-key row-switch interaction, so the core makes no JOYP IF claim and VIDEO-03 remains incomplete.
- Updated the public API comment and evidence/validation documents without adding dependencies or changing core implementation.

## Task Commits

1. **Task 1: Complete bounded button-event and active-low matrix semantics** — `7c76fb8` (`test(GB-03-04): cover JOYP matrix and queue contract`)
2. **Task 2: Close or explicitly retain the model-specific JOYP interrupt gate** — `eb1f3a3` (`docs(GB-03-04): retain JOYP interrupt evidence gate`)

Plan summary and continuation metadata are recorded in the Phase 3 execution metadata commit.

## Files Created/Modified

- `tests/test_joypad.c` — direct finite guest tests for JOYP selection, queue contract, ordering, and partition behavior.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — registered four explicit cases in the fail-closed inventory.
- `include/gabbaboy/gabbaboy.h` — documented that JOYP IF generation remains unmodeled while D-08 is open.
- `.planning/phases/GB-03-visible-interactive-dmg/03-RESEARCH.md`, `docs/dmg-video-evidence.md` — source audit and applicability limits.
- `.planning/phases/GB-03-visible-interactive-dmg/03-VALIDATION.md` — recorded task results and retained evidence gate.
- `.planning/STATE.md`, `.planning/.continue-here.md` — routed execution to Wave 5 / Plan 03-05.

## Decisions Made

The existing queue and active-low read implementation already satisfied the planned polling and queue behavior, so this plan added regression coverage and clarified the public contract without changing core logic. Nintendo's manual gives DMG-family matrix and low-pulse guidance; the hardware note's synchronous observations and the reconstructed CPU-B schematic do not yet produce independently supported before/at/after half-dot expectations. No interrupt edge is guessed.

## Deviations from Plan

None. The plan explicitly allowed the evidence-gate branch to retain D-08 and keep VIDEO-03 incomplete when model-applicable expected cases were unavailable.

## Issues Encountered

An initial test buffer was too small for the manual's six-read P15 probe; it was enlarged before the committed test run. No product dependency or core implementation change was needed.

## User Setup Required

None.

## Next Phase Readiness

Wave 5 / Plan 03-05 can proceed with the optional SDL3 player and deterministic host-input adapter. Phase 3 is not complete: VIDEO-02's simultaneous PPU/DMA collision qualification and VIDEO-03's exact JOYP interrupt evidence remain open. No physical DMG-CPU-B observation occurred.

---
*Phase: GB-03-visible-interactive-dmg*
*Completed: 2026-10-07*
