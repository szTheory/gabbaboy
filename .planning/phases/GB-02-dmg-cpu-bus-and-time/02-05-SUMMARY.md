---
phase: GB-02-dmg-cpu-bus-and-time
plan: 05
subsystem: cpu-timing
tags: [dmg, timer, serial, half-dots, tdd]
requires:
  - phase: GB-02-dmg-cpu-bus-and-time
    provides: timed SM83 bus phases, per-instance bus observer, bounded CPU execution
provides:
  - Half-dot divider and falling-edge TIMA timer with delayed reload and collision rules
  - Guest-visible disconnected internal serial completion and bounded external-clock pending state
affects: [02-06 timestamped input and partitioned runs, 02-07 CPU/timer diagnostics]
commits: 4
plan_head_before: 027f291e9138b62be1b40edf22aa7ce76df67fd6
plan_head_after: 2754cac
tech-stack:
  added: []
  patterns: [instance-owned half-dot device state, timer transitions observed through timed bus observer]
key-files:
  created: [tests/test_serial.c]
  modified: [src/core/gabbaboy.c, tests/test_timer.c, tests/CMakeLists.txt, tests/expected-tests.txt]
decisions:
  - Timer input is a gated selected-divider signal and TIMA increments on its falling edge, including DIV/TAC-induced edges.
  - Timer reload uses an eight-half-dot countdown; qualified TIMA/TMA collision behavior is asserted at sampled bus phases.
  - Internal disconnected serial shifts one high bit every 1024 half-dots; external-clock transfers remain pending until the Plan 02-06 input seam exists.
  - Unqualified active-transfer SB/SC overlap returns bounded unsupported status rather than claiming an ordering.
metrics:
  duration: 18min
  completed: 2026-10-06
  status: complete
requirements-completed: []
coverage:
  - id: D1
    description: Guest timed timer divider edges, overflow, reload, IF, and qualified collision behavior.
    requirement: CPU-03
    verification:
      - kind: unit
        ref: ctest --preset phase1 --output-on-failure --no-tests=error -R '^timer_'
        status: pass
    human_judgment: false
  - id: D2
    description: Disconnected internal serial completes and external serial remains pending without supplied edges.
    requirement: CPU-03
    verification:
      - kind: unit
        ref: ctest --preset phase1 --output-on-failure --no-tests=error -R '^serial_'
        status: pass
    human_judgment: false
---

# Phase 2 Plan 05: Timer Races and Disconnected Serial Summary

**TIMA now follows selected-divider falling edges and qualified reload collisions on the CPU bus timeline; the disconnected internal serial path completes deterministically.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-10-06
- **Completed:** 2026-10-06
- **Tasks:** 2
- **Files modified or created:** 5

## Accomplishments

- Added guest-driven tests for divider selectors, DIV/TAC induced edges, overflow visibility, reload/IF timing, and TIMA/TMA collision cases.
- Added disconnected internal serial interval/completion tests, external-clock pending behavior, and a negative case for unqualified active-transfer register overlap.
- Timer and serial events advance at sampled CPU bus phases and within complete instructions; the public API still returns at whole-instruction boundaries.

## Task Commits

1. **Task 1 RED:** `23e9983` (test: timed timer guest cases)
2. **Task 1 GREEN:** `be3ccf3` (feat: process timer edges on timed CPU phases)
3. **Task 2 RED:** `73d6e87` (test: timer race and serial cases)
4. **Task 2 GREEN:** `2754cac` (feat: model timer collisions and disconnected serial)

The plan commit ledger measured four task commits from `027f291e9138b62be1b40edf22aa7ce76df67fd6` through `2754cac`. The separate documentation/state commit is not included in that count.

## Files Created/Modified

- `src/core/gabbaboy.c` — instance-owned divider, timer reload and serial state; timestamped transitions are processed at bus access phases.
- `tests/test_timer.c` — guest-driven edge, overflow, collision, and observer timestamp tests.
- `tests/test_serial.c` — internal disconnected completion, external pending, and unsupported overlap tests.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — registered and fail-closed test inventory entries.

## Decisions Made

- Timer selector and reload expectations follow pinned Pan Docs source revision `0191af06ac49661587dcde3d57a241a626b8df75`.
- The four TMA reload collision expected values (D=7F, E=7F, C=FE, L=FE) follow the hardware-author Mooneye `tma_write_reloading` test at revision `31510e12eea6286d36eea060a6adde755e1067aa`; translated bus-phase delays are explicitly aligned to this core's sampled access phases.
- The serial implementation proves the 1024-half-dot interval and eight-edge completion only. It makes no claim about first-edge phase. External edge injection stays in Plan 02-06.
- CPU-03 and CPU-04 traceability remain pending the Phase 2 final verifier; this plan summary does not close either requirement.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Prevented double advancement of device time during CPU execution.**
- **Found during:** Task 1
- **Issue:** CPU instruction execution advanced its full duration internally while timed bus accesses also advanced devices, which could process a timer transition twice or at the wrong time.
- **Fix:** Device advancement now follows timed bus accesses and the run loop accounts for the remaining instruction duration once.
- **Files modified:** `src/core/gabbaboy.c`
- **Verification:** Focused timer guest tests and full 61-case CTest passed.
- **Committed in:** `be3ccf3`

**2. [Rule 2 - Correctness] Used bounded relative deadlines for long-running timer and serial state.**
- **Found during:** Task 2
- **Issue:** Absolute deadline timestamps could wrap near the `uint64_t` time limit, undermining monotonic processing.
- **Fix:** Timer reload and serial edges use bounded remaining-half-dot counters.
- **Files modified:** `src/core/gabbaboy.c`
- **Verification:** Timer/serial focused tests and full 61-case CTest passed.
- **Committed in:** `2754cac`

**Total deviations:** 2 auto-fixed (Rule 1: 1; Rule 2: 1). **Impact:** Both changes preserve the plan's device scope and strengthen timing correctness.

## Verification Evidence and Limits

- TDD RED was demonstrated before implementation for each task; `gsd_run check tdd-red-evidence` accepted both captured failing CTest records.
- Focused timer/serial tests passed after the GREEN changes.
- Full `ctest --preset phase1 --output-on-failure --no-tests=error` passed **61/61** after the final counter-safety change.
- `git diff --check` passed before the task GREEN commit.
- Timer/TMA collision values were translated from the pinned Mooneye test into a loaded-guest program and checked against independently specified values. This is a source-qualified adaptation, not a run of the original ROM or hardware-backed evidence.
- The in-flight observer is private test instrumentation for recording bus/device events. Public state peeks remain limited to their declared address range.
- Active-transfer SB/SC overlap without qualified ordering returns `GBB_STOP_UNSUPPORTED_BUS`; this bounded negative behavior does not assert a hardware ordering.

## Issues Encountered

None. No package installation, network endpoint, or user setup was required.

## Next Phase Readiness

Plan 02-05 is complete. Continue at **Phase 2 Plan 02-06 — timestamped inputs and bounded partitioned runs**. Phase 2 CPU requirements remain pending final goal-backward verification; do not dispatch another phase.

---
*Phase: GB-02-dmg-cpu-bus-and-time*
*Plan: 05*
*Completed: 2026-10-06*
## Self-Check: PASSED

- Summary file exists at the required path.
- All four task commits are ancestors of current HEAD.
- No TODO, FIXME, placeholder, or coming-soon stubs were found in plan files.
