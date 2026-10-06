---
phase: GB-02-dmg-cpu-bus-and-time
plan: 04
subsystem: cpu
tags: [sm83, interrupts, halt, stop, timing, c17]
requires:
  - phase: GB-02-dmg-cpu-bus-and-time/02-03
    provides: Complete CB-prefixed execution and timed bus observation
provides:
  - Per-instance IE, IF, IME and delayed EI state with prioritized timed interrupt dispatch
  - Bounded HALT idle and distinct HALT, STOP, lockup, and budget outcomes
  - Deterministic HALT bug operand reuse, reset restoration, and DIV phase progression
affects: [GB-02-dmg-cpu-bus-and-time/02-05, GB-02-dmg-cpu-bus-and-time/02-06, cpu, runner]
actuals:
  tokens: 8099
  tasks: 2
  commits: 4
plan_head_before: f123bdfc8d599a5b07abcdb74d346c0c4c884287
plan_head_after: 83ca2f768c4ea12bd7ca7b4e9b80942ad871317e
tech-stack:
  added: []
  patterns: [per-instance interrupt/control state, bounded idle tick advancement, complete interrupt-entry preflight]
key-files:
  created: [tests/test_control.c]
  modified: [src/core/gabbaboy.c, include/gabbaboy/gabbaboy.h, src/runner/main.c, tests/CMakeLists.txt, tests/expected-tests.txt, tests/test_cpu.c]
key-decisions:
  - "Interrupt entry costs 40 half-dots, selects the lowest enabled pending bit, clears it, and pushes the current PC on timed bus phases."
  - "HALT idle advances whole 8-half-dot cycles within the caller budget; STOP remains pending until a modeled wake path arrives in Plan 02-06."
patterns-established:
  - "EI schedules enable after one complete following instruction; DI cancels the delay and RETI enables immediately."
  - "Public run outcomes distinguish HALT idle and STOP from budget exhaustion and lockup."
requirements-completed: []
coverage:
  - id: D1
    description: "IE/IF writes, delayed EI, DI, prioritized interrupt dispatch, RETI, timed stack entry, and short-budget preflight are verified through real guest programs."
    requirement: CPU-02
    verification:
      - kind: unit
        ref: tests/test_control.c#interrupt_entry,interrupt_budget,interrupt_ei_delay,interrupt_priority
        status: pass
      - kind: integration
        ref: "cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error"
        status: pass
    human_judgment: false
  - id: D2
    description: "HALT idle and bug behavior, STOP waiting, reset profile restoration, and lockup reset have named bounded regressions."
    requirement: CPU-04
    verification:
      - kind: unit
        ref: tests/test_control.c#halt_idle,halt_bug,stop_wait,reset_profile,reset_lockup
        status: pass
      - kind: integration
        ref: tests/test_cpu.c#base_matrix
        status: pass
    human_judgment: false
duration: 16min
completed: 2026-10-06
status: complete
commits: 4
---

# Phase GB-02 Plan 04: CPU control states and interrupts Summary

**The bootless DMG CPU now dispatches timed prioritized interrupts and reports bounded HALT idle and STOP states separately.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-10-06T19:08:39Z
- **Completed:** 2026-10-06T19:24:49Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Added instance-owned IE/IF, IME, delayed EI, HALT, STOP, and HALT-bug state. Interrupt preflight preserves guest state when the 40-half-dot entry does not fit.
- Implemented lowest-bit interrupt priority, IF acknowledgement, timed high/low stack writes, vector selection, EI delay, DI cancellation, and immediate RETI enable.
- HALT now advances bounded device time and the divider; pending interrupts wake it or trigger the DMG HALT bug. STOP resets DIV and freezes progression pending a modeled wake event.
- Added distinct public `GBB_STOP_HALTED_IDLE` and `GBB_STOP_STOPPED` outcomes, with matching runner reporting. Reset clears all new persistent control state.
- Added nine named control cases. Both task RED records passed the OpenGSD `tdd-red-evidence` gate. Focused control tests passed 9/9; the full CTest suite passed 51/51, including relocated package and C/C++ consumer checks.

## Task Commits

1. **Dispatch one timed VBlank interrupt from a guest program** — `21d483d` (test), `0575bf1` (feat)
2. **Complete EI, HALT, STOP, reset and lockup control transitions** — `c0a5aee` (test), `83ca2f7` (feat)

## Files Created/Modified

- `tests/test_control.c` — guest-generated interrupt and control-state regressions.
- `src/core/gabbaboy.c`, `include/gabbaboy/gabbaboy.h` — per-instance control logic, register mapping, bounded outcomes, and API contract.
- `src/runner/main.c` — distinct idle/stopped outcome reporting.
- `tests/test_cpu.c`, `tests/CMakeLists.txt`, `tests/expected-tests.txt` — base matrix expectations and test inventory.

## Decisions Made

- Interrupt entry is one preflighted 40-half-dot operation; it acknowledges the selected IF request and stacks the interrupted PC at observable timed phases.
- HALT advances eligible time in whole 8-half-dot cycles. STOP remains stopped because the timestamped input/wake path is owned by Plan 02-06.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] Reported HALT and STOP outcomes distinctly in the runner.**
- **Found during:** Task 2
- **Issue:** The runner's existing fallback would have mislabeled new bounded CPU stop outcomes as timeout or unsupported opcode.
- **Fix:** Added explicit `halted-idle` and `stopped` outcome and stop labels.
- **Files modified:** `src/runner/main.c`
- **Verification:** Full CTest suite passed 51/51, including `tracer_smoke` and installed runner smoke.
- **Committed in:** `83ca2f7`

**2. [Rule 1 - Bug] Updated the base opcode matrix for new HALT/STOP and IE behavior.**
- **Found during:** Task 2 verification
- **Issue:** Existing matrix assertions expected HALT and STOP to continue as ordinary instructions and assumed the IE address read as open bus.
- **Fix:** Asserted the new distinct HALT/STOP outcomes and the defined upper-bit IE read value on stack reads.
- **Files modified:** `tests/test_cpu.c`
- **Verification:** `cpu_base_matrix` and full CTest suite passed.
- **Committed in:** `83ca2f7`

**Total deviations:** 2 auto-fixed (Rule 1: 1; Rule 2: 1). No planned control transition was omitted.

## Verification

- Task 1 RED: `build/tdd-red-02-04-task1.json` classified `RED_EVIDENCE_OK`; the `interrupt_entry` assertion failed because short budget continued guest execution.
- Task 1 GREEN: focused `interrupt_entry` and `interrupt_budget` cases passed 2/2.
- Task 2 RED: `build/tdd-red-02-04-task2.json` classified `RED_EVIDENCE_OK`; `halt_idle` failed because the baseline treated HALT as an ordinary instruction.
- Task 2 GREEN: named interrupt/control cases passed 9/9.
- Overall: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` — 51/51 passed.

## Issues Encountered

- CTest writes to `.git/index.lock` were blocked by the sandbox. The authorized commits were completed through the installed OpenGSD SDK with normal hooks; no hook was bypassed.
- New IE/IF mapping changed the expected value when stack pops read `$FFFF`; the independent base matrix now expects the defined `$E0` unused-bit pattern.

## User Setup Required

None.

## Next Phase Readiness

Plan 02-04 is complete; Phase GB-02 remains in progress. Continue at Plan 02-05 — **Timer and divider edge model** — with `$gsd-execute-phase 2`. Phase 3 — **Visible Interactive DMG** — remains gated on Phase 2 verification and owner direction. Keep both auto-advance flags false; CPU requirement checkboxes remain pending final phase verification.

---
*Phase: GB-02-dmg-cpu-bus-and-time*
*Completed: 2026-10-06*

## Self-Check: PASSED

- Summary exists at the expected phase path.
- Task commits `21d483d`, `0575bf1`, `c0a5aee`, and `83ca2f7` are ancestors of the current branch head.
- Measured task commit count is 4 from `f123bdfc8d599a5b07abcdb74d346c0c4c884287` through `83ca2f768c4ea12bd7ca7b4e9b80942ad871317e`.
- Both TDD RED records passed OpenGSD evidence classification; all 51 registered tests passed in the final run.
- The modified source and test files contain no known stubs, skipped tests, or unrun automated verification.
