---
phase: GB-03-visible-interactive-dmg
plan: "07"
subsystem: public-api
tags: [c17, frame-copy, joypad-events, installed-consumers]

# Dependency graph
requires:
  - phase: GB-03-visible-interactive-dmg
    provides: Completed-frame copy API and bounded timestamped event queue
provides:
  - Checked frame-copy extents and rejection of overlapping pixel/metadata outputs
  - Direct frame generation, reset, padding, canary, and per-instance tests
  - Atomic event failure-precedence coverage and relocated C/C++ consumers for button/frame APIs
affects: [GB-03-08, GB-03-09, phase-3-verification]

# Actuals
actuals:
  tokens: 5725
  tasks: 2
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns: [validate complete output ranges before mutation, fail-closed external package consumers]

key-files:
  created: []
  modified:
    - include/gabbaboy/gabbaboy.h
    - src/core/gabbaboy.c
    - tests/test_api.c
    - tests/test_events.c
    - tests/test_ppu.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/consumers/c/main.c
    - tests/consumers/cpp/main.cpp

key-decisions:
  - "Frame copies validate checked pitch/capacity arithmetic and disjoint pixel/metadata ranges before readiness checks or writes; all failures preserve caller outputs."
  - "For valid nonempty queue requests, remaining capacity is checked before event contents, so over-capacity errors take precedence over malformed entries."
  - "Installed C/C++ examples exercise timestamped button events and completed-frame copies through only the exported public package."

patterns-established:
  - "Test frame output against exact-capacity buffers, row padding, metadata sentinels, overlap, reset, partial-frame, and independent-instance controls."
  - "Exercise public package consumers from a relocated install without private headers or SDL dependencies."

requirements-completed: [VIDEO-01, VIDEO-03, VIDEO-05]

coverage:
  - id: D1
    description: "Frame-copy success and failure paths preserve output boundaries, stable completed generations, reset invalidation, and per-instance isolation."
    requirement: VIDEO-01
    verification:
      - kind: unit
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(frame_copy_failures|frame_generation_lifecycle|independent_instances)$'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Malformed and over-capacity event batches reject atomically with documented precedence; timestamp ordering and run partition behavior remain stable."
    requirement: VIDEO-03
    verification:
      - kind: unit
        ref: "CTest event_queue_atomic, event_queue_failure_precedence, event_queue_order, event_partition, event_time_overflow, joypad_*"
        status: pass
    human_judgment: false
  - id: D3
    description: "Relocated C and C++ consumers load the installed fixture, submit timestamped button edges, run the core, and copy a completed frame using public declarations only."
    requirement: VIDEO-05
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-phase2-installed.sh; installed inventory 137/137, core-only inventory 132/132"
        status: pass
    human_judgment: false

# Metrics
duration: 10 min
completed: 2026-10-07
status: complete
---

# Phase GB-03 Plan 07 Summary

**The public frame API now rejects invalid and overlapping outputs atomically, and relocated C/C++ consumers exercise frame and timestamped-button APIs.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-10-07T20:18:58Z
- **Completed:** 2026-10-07T20:28:30Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Rejected frame-copy address overflow and any overlap between the caller-declared pixel capacity and `gbb_frame_info` before output mutation.
- Added direct tests for nulls, short pitch/capacity, arithmetic overflow, not-ready frames, overlap, active-row canaries, repeat copies, partial following frames, reset invalidation, and instance isolation.
- Documented queue capacity-before-content validation precedence and verified malformed mixed batches do not append earlier valid events.
- Extended external C and C++ package consumers to queue A-button press/release events, run the installed core, and verify a completed 160×144 shade frame.

## Task Commits

1. **Task 1 RED tests: Cover frame-copy failure boundaries** — `cb8eee8` (`test(GB-03-07): cover frame copy failure boundaries`)
2. **Task 1 implementation: Reject overlapping frame-copy outputs** — `cc316c3` (`feat(GB-03-07): reject overlapping frame copy outputs`)
3. **Task 2: Exercise event failures and installed consumers** — `c57e0ff` (`test(GB-03-07): exercise event failures and installed consumers`)

Plan metadata is recorded in the follow-up documentation commit.

## Files Created/Modified

- `include/gabbaboy/gabbaboy.h` — precise frame extent/error and event-queue precedence contracts.
- `src/core/gabbaboy.c` — checked pixel/info pointer ranges before frame output.
- `tests/test_api.c`, `tests/test_ppu.c` — frame independence, canary, generation, reset, and output failure cases.
- `tests/test_events.c` — malformed mixed-batch atomicity and capacity-first error precedence.
- `tests/consumers/c/main.c`, `tests/consumers/cpp/main.cpp` — installed public API button and frame smoke.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — registered boundary tests and fail-closed inventory.

## Decisions Made

- Frame validation checks the complete caller-declared capacity range for overlap, with checked address-end arithmetic. Validation precedes frame readiness so invalid output arguments always return `GBB_INVALID_ARGUMENT` without changing pixels or metadata.
- Queue pointer checks and empty-batch handling retain their existing precedence. For nonempty requests with valid pointers, remaining capacity is checked before reading entries; over-capacity calls return `GBB_EVENT_QUEUE_FULL` even when an entry is malformed.
- External consumers continue using only the installed `GabbaBoy::core` target and public header; the default package remains SDL-free.

## Deviations from Plan

- The plan's anchored CTest expressions named literal prefixes (`frame_copy_`, `event_`) and therefore did not select the suffixed tests. They were corrected to enumerate registered case names, and the focused selections were rerun: 3/3 frame cases and 11/11 event/joypad/frame cases passed.

## Issues Encountered

- A STOP result differs depending on whether a wake deadline falls within the run window. The atomicity test now expects `GBB_STOP_STOPPED` when no event was admitted and no wake is due in the requested interval; an existing queued wake at the interval boundary remains `GBB_STOP_NO_PROGRESS`.

## User Setup Required

None.

## Next Phase Readiness

Wave 8 / Plan 03-08 can bind the owned interactive fixture source to its checked-in bytes and pinned hosted reproduction. Phase 3 still has open D-08 JOYP interrupt evidence and VIDEO-02 simultaneous PPU/DMA applicability; VIDEO-03 remains incomplete. Native window perception is unavailable without a desktop display, and no physical DMG-CPU-B observation occurred.

---
*Phase: GB-03-visible-interactive-dmg*
*Completed: 2026-10-07*
