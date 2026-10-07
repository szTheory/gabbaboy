---
phase: GB-02-dmg-cpu-bus-and-time
plan: 06
subsystem: cpu-timing
tags: [dmg, timestamped-input, stop-wake, serial, half-dots, tdd]
requires:
  - phase: GB-02-dmg-cpu-bus-and-time
    provides: timed CPU bus phases, bounded execution, timer and disconnected serial
provides:
  - Fixed-capacity ordered per-instance timestamped input queue
  - Bounded STOP wait timeline with frozen oscillator devices and modeled wake
  - External serial edge sampling and partition-equivalence coverage
affects: [02-07 diagnostics and fixtures, 02-09 installed consumers]
actuals:
  tokens: 6275
  tasks: 2
  commits: 5
commits: 5
plan_head_before: 5e615bafca77082aebb71da3a7a26be626099e02
plan_head_after: f1249621383eef0c38eccce0a43c28f4dc6c7585
tech-stack:
  added: []
  patterns: [fixed 64-event instance queue, timestamp application at timed device and CPU boundaries]
key-files:
  created: [tests/test_events.c]
  modified: [include/gabbaboy/gabbaboy.h, src/core/gabbaboy.c, tests/test_control.c, tests/CMakeLists.txt, tests/expected-tests.txt, README.md]
key-decisions:
  - "STOP waits advance only the bounded master timeline; CPU, divider, timer, and internal serial oscillator state remains frozen."
  - "Events with equal timestamps preserve caller order and apply before the next CPU fetch."
  - "STOP wake models one selected input-line transition without claiming full JOYP behavior."
decisions:
  - "STOP waits advance only the bounded master timeline; oscillator-driven devices remain frozen."
  - "Timestamped input batches use a fixed capacity of 64 and reject malformed admission atomically."
requirements-completed: []
coverage:
  - id: D1
    description: "A stopped guest advances only bounded master time, freezes oscillator devices, and wakes at the accepted timestamp."
    requirement: CPU-02
    verification:
      - kind: unit
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(event_stop_wake|stop_wait)$'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Ordered timestamped input batches, external serial edges, partitioned runs, overflow, and trace capacity remain deterministic and bounded."
    requirement: CPU-04
    verification:
      - kind: unit
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(event_(queue_order|queue_atomic|partition|deadline_inside|external_serial_edges|time_overflow)|run_output_capacity)$'"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error (70/70)"
        status: pass
    human_judgment: false
duration: 6min
completed: 2026-10-06
status: complete
---

# Phase 2 Plan 06: Timestamped Inputs and Bounded Partitioned Runs Summary

**A fixed 64-event queue now drives deterministic STOP wake and external serial input on the half-dot timeline, with stable ties and equal-time partition evidence.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-10-06T20:03:51Z
- **Completed:** 2026-10-06T20:10:15Z
- **Tasks:** 2
- **Files modified or created:** 7

## Accomplishments

- Added the public timestamped input event API and fixed-capacity per-instance admission with atomic pointer, ordering, timestamp, event-value, and capacity validation.
- STOP entry resets DIV. A positive stopped run advances only master input time; CPU, divider, timer, and internal serial oscillator work freezes. A modeled wake at the exact budget boundary is consumed once before any later CPU fetch.
- External serial input edges are sampled at their timestamps. Tests prove same-time caller order, edge timing inside an instruction, equal actual-time CPU trace/WRAM equivalence across run partitions, near-maximum-time handling, and caller trace canaries.
- Updated the existing STOP wait regression and public README/API comments to describe the new behavior and retain the explicit limit that full JOYP semantics are deferred.

## Task Commits

1. **Task 1 RED:** `df86e85` — registered and ran the failing `event_stop_wake` assertion; OpenGSD accepted its captured TAP evidence as `RED_EVIDENCE_OK`.
2. **Task 1 GREEN:** `f71d445` — implemented event admission/application, STOP master-time waiting, oscillator freeze, DIV reset, wake, and external serial edges.
3. **Task 2 tests:** `1a0bd4a` — added queue, partition, serial, overflow, and output-capacity cases.
4. **Task 2 regression correction:** `74d7b4a` — updated the existing `stop_wait` expectation after that named assertion failed; its captured TAP evidence also passed the OpenGSD RED classifier.
5. **API documentation:** `f124962` — documented event and STOP semantics in the public header and README.

The plan ledger measured five commits from `5e615bafca77082aebb71da3a7a26be626099e02` through `f1249621383eef0c38eccce0a43c28f4dc6c7585`. The summary/state metadata commit is separate.

## Files Created/Modified

- `include/gabbaboy/gabbaboy.h` — event/error/result types, bounded event API, and STOP timing contract.
- `src/core/gabbaboy.c` — fixed event storage, atomic queue admission, timestamped serial/wake handling, STOP time progression and overflow checks.
- `tests/test_events.c` — STOP, queue atomicity/order, partition, serial edge, overflow, and trace-capacity guest/API cases.
- `tests/test_control.c` — positive stopped wait now asserts the consumed master timeline.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — registered the nine required focused cases.
- `README.md` — documented the public event seam and STOP limitation.

## Decisions Made

- A STOP wake event with value 1 represents the supported selected input-line transition; this does not model full JOYP selection or glitch behavior.
- External serial edge values are the sampled input bits. Same-time events retain caller order.
- If STOP wake consumes the exact remaining budget, the call returns `GBB_STOP_NO_PROGRESS`; a subsequent call must fit the full next instruction.
- CPU requirements remain pending final Phase 2 goal-backward verification; this plan does not mark CPU-02 or CPU-04 complete globally.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Regression] Updated the existing STOP wait assertion to match bounded STOP timeline behavior.**
- **Found during:** Task 2 full-suite verification.
- **Issue:** The prior control test expected a positive STOP wait to consume zero ticks, which contradicted the adopted D-07/D-08 contract.
- **Fix:** It now expects `GBB_STOP_STOPPED` with the full bounded wait consumed.
- **Files modified:** `tests/test_control.c`.
- **Verification:** Focused `stop_wait` passed; full CTest passed 70/70.
- **Committed in:** `74d7b4a`.

**2. [Project documentation] Updated public API documentation with the new event and STOP contract.**
- **Found during:** Closeout review.
- **Issue:** The new public API and time behavior were not described in the embedding guide.
- **Fix:** Added event queue, tie ordering, bounded STOP time, and JOYP limitation notes.
- **Files modified:** `README.md`, `include/gabbaboy/gabbaboy.h`.
- **Verification:** Documentation-only change; preceding full CTest passed 70/70.
- **Committed in:** `f124962`.

**Total deviations:** 2 (one regression correction and one documentation synchronization). **Impact:** Both keep existing consumers and public claims aligned with the implemented behavior.

## Verification Evidence and Limits

- T1 `event_stop_wake` failed at the planned positive-wait assertion before GREEN; `gsd_run check tdd-red-evidence` returned `RED_EVIDENCE_OK` with no report errors.
- T2 `stop_wait` exposed the stale existing zero-time assertion after the STOP behavior landed; the classifier accepted its TAP output as `RED_EVIDENCE_OK`, then the corrected focused test passed.
- Focused event/output selection passed 9/9. Full `cmake --preset phase1`, `cmake --build --preset phase1`, and `ctest --preset phase1 --output-on-failure --no-tests=error` passed **70/70**, including installed C and C++ consumers.
- The input seam models only a selected wake transition and external serial input edges. It does not establish full joypad, PPU, audio, hardware-backed or broad game compatibility behavior.
- This is software guest/API and metamorphic evidence, not a physical DMG hardware observation.

## Issues Encountered

- The sandbox denied writes to `.git/index`; normal task commits were completed through the approved escalated Git invocation with hooks. The `.git` ledger itself remained read-only, so the starting SHA was recorded in a temporary phase-local ledger and measured with `git rev-list` before summary creation.
- The first full-suite run surfaced the stale `stop_wait` expectation; it was corrected and the full suite rerun successfully.

## Next Phase Readiness

Plan 02-06 is complete. Continue at **Phase 2 Plan 02-07 — pinned CPU/timer diagnostic fixtures** using `$gsd-execute-phase 2` when the owner chooses. Phase 2 remains in progress; do not advance to Phase 3 before Phase 2 verification and owner direction. Both auto-advance settings remain false.

---
*Phase: GB-02-dmg-cpu-bus-and-time*
*Plan: 06*
*Completed: 2026-10-06*

## Self-Check: PASSED

- Summary created at the required plan path.
- All five task/documentation commits are ancestors of the recorded plan head.
- No placeholder, TODO, or FIXME stubs were found in plan-modified files.
