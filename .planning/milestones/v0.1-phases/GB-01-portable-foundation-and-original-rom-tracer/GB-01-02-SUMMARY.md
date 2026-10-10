---
phase: 01-portable-foundation-and-original-rom-tracer
plan: 02
subsystem: core
tags: [c17, lifecycle, rom-loader, bounded-execution, tracer]
requires:
  - phase: 01
    provides: "C17 DMG-CPU-B tracer core, fixture, and offline digest test"
provides:
  - "Documented opaque-instance ownership, reset, threading, error, budget, and trace contracts"
  - "Named API lifecycle, independent-instance, run-boundary, and trace-capacity regressions"
  - "Typed bounded ROM validation with non-destructive replacement failures"
  - "Distinct guest-failure, unsupported-opcode, timeout, and trace-exhaustion controls"
affects: [01-03, 01-04, 01-05, api-consumers, ci]
actuals:
  tokens: 5219
  tasks: 2
  commits: 2
commits: 2
plan_head_before: 246fd91838aced751e2022d62397d3ae5074ab37
plan_head_after: c69fd162eea188bc9a3069324ca4e7f32ec06aa7
tech-stack:
  added: []
  patterns: ["Parse candidate ROMs before replacing live state", "Use caller-owned bounded traces and whole-instruction budget preflight"]
key-files:
  created: [tests/test_api.c, tests/test_loader.c, tests/test_tracer.c]
  modified: [CMakeLists.txt, include/gabbaboy/gabbaboy.h, src/core/gabbaboy.c, src/runner/main.c]
key-decisions:
  - "ROM validation reports malformed, truncated, oversized, mismatched, and unsupported cartridge-size conditions separately."
  - "Reset retains the loaded ROM while restoring the deterministic profile state and clearing guest RAM and emulated time."
requirements-completed: [BASE-02, BASE-03, BASE-04, BASE-07]
coverage:
  - id: D1
    description: "Public instance lifecycle, reset, independent state, exact budget bounds, and bounded trace behavior are exercised by named API cases."
    requirement: BASE-02
    verification:
      - kind: unit
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R 'instance_lifecycle|independent_instances|run_bounds|trace_capacity'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Malformed and unsupported ROM images return typed errors while preserving the loaded guest state."
    requirement: BASE-03
    verification:
      - kind: unit
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R 'loader_'"
        status: pass
    human_judgment: false
  - id: D3
    description: "The original guest success protocol and distinct guest failure, unsupported opcode, timeout, and trace-exhaustion controls are tested."
    requirement: BASE-04
    verification:
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R 'tracer_(success|failure|unsupported|timeout|trace)'"
        status: pass
    human_judgment: false
  - id: D4
    description: "The named lifecycle, loader, and tracer controls are present in the executable CTest inventory for later required-CI enforcement."
    requirement: BASE-07
    verification:
      - kind: unit
        ref: "ctest --test-dir build -N (21 named tests); full local CTest suite passed"
        status: pass
    human_judgment: false
duration: 7min
completed: 2026-10-03
status: complete
---

# Phase 1 Plan 2: Bounded Lifecycle, Loader, and Output/Error Contract Summary

**Opaque DMG-CPU-B instances now have reset and ownership rules, strict whole-instruction budgets, typed bounded ROM rejection, and tested guest/host stop outcomes.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-03T11:25:41Z
- **Completed:** 2026-10-03T11:32:49Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Documented instance ownership, one-thread-at-a-time use, supported profile, pointer lifetimes, reset behavior, run units, and caller-owned trace constraints in the public header.
- Added reset that retains the copied ROM and restores profile registers, zero-filled emulator-policy RAM, and time zero.
- Added named API checks for lifecycle, independent instances, zero/insufficient/exact/sufficient budgets, invalid trace pairs, and trace-capacity exhaustion without overwriting adjacent caller storage.
- Added typed ROM loader outcomes for null/zero arguments, truncation, hard size limits, header mismatch, invalid checksum, unsupported cartridge/ROM/RAM size, and allocation failure; replacement parsing completes before the current ROM or guest state changes.
- Added negative tracer controls for a guest RAM mismatch, unsupported opcode, caller time-budget timeout, and exhausted trace output. The runner now has enough bounded trace capacity for the normal fixture and treats trace exhaustion as non-pass.

## Task Commits

1. **Task 1: Lock lifecycle, ownership, and strict run/trace boundaries** - `410ffd8` (feat)
2. **Task 2: Reject malformed cartridges without partial mutation** - `c69fd16` (feat)

**Measured commits at summary write:** 2 from `246fd91838aced751e2022d62397d3ae5074ab37` to `c69fd162eea188bc9a3069324ca4e7f32ec06aa7`.

## Files Created/Modified

- `include/gabbaboy/gabbaboy.h` - Public lifecycle, ownership, error, budget, and trace contract.
- `src/core/gabbaboy.c` - Profile reset and typed, bounded, transactional ROM replacement validation.
- `src/runner/main.c` - Distinct non-pass outcome classification and bounded trace retention for the full success workload.
- `tests/test_api.c` - Lifecycle, instance isolation, budget and trace boundary cases.
- `tests/test_loader.c` - Loader boundary, unsupported-header, and non-destructive failure cases.
- `tests/test_tracer.c` - Success and distinct negative guest/run/output controls.
- `CMakeLists.txt` - Registers named CTest cases for API, loader, and tracer controls.

## Decisions Made

- Used distinct public error values for invalid arguments, malformed headers, truncated images, over-limit images, actual/declared size mismatch, and unsupported cartridge/ROM/RAM configurations.
- Reset keeps the active ROM but clears guest RAM and elapsed profile time, so callers can restart the same fixture without reloading or retaining prior guest progress.
- The runner uses a fixed 16,384-record trace ceiling for the declared tracer budget; exhaustion is reported explicitly and never qualifies as fixture pass.

## Deviations from Plan

None - plan executed as specified.

## Issues Encountered

- The workspace sandbox denied writes to the Git index and commit metadata. The task commits were completed on the authorized phase branch through the approved Git escalation path; no source or test work was skipped.

## User Setup Required

None - no external service configuration required.

## Deferred Evidence and Limitations

- BASE-07's local CTest inventory is established, but its requirement remains pending until Plan 04's sanitizer and required hosted CI checks execute.
- No new hardware-backed or general CPU/gameplay evidence is claimed. Execution remains limited to the original fixture, declared opcode subset, and deterministic bootless DMG-CPU-B profile.

## Test Evidence

- Task 1: `cmake -S . -B build -G Ninja && cmake --build build && ctest --test-dir build --output-on-failure --no-tests=error -R 'instance_lifecycle|independent_instances|run_bounds|trace_capacity'` — 4 named cases passed.
- Task 2: `cmake -S . -B build -G Ninja && cmake --build build && ctest --test-dir build --output-on-failure --no-tests=error -R 'loader_|tracer_(success|failure|unsupported|timeout|trace)'` — 15 named cases passed.
- Full local suite: `ctest --test-dir build --output-on-failure --no-tests=error` — all 21 tests passed.
- Runner smoke: original fixture reported `outcome=pass`, `stop=budget`, `half_dots=200000`, and 8,337 bounded trace records.
- Test inventory: `ctest --test-dir build -N` listed all 21 tests, including each required named API, loader, and tracer control.

## Next Plan Readiness

Plan 01-03 is next and owns installed C/C++ consumer checks. Continue with `$gsd-execute-phase 1`; Phase 1 remains active and later phases must not start automatically.

## Self-Check: PASSED

- The created test files and modified build/API/core/runner files exist.
- Task commits `410ffd8` and `c69fd16` exist in Git history.
- Every named acceptance case passed, and the complete local CTest suite ran all 21 registered tests.

---
*Phase: 01-portable-foundation-and-original-rom-tracer*
*Completed: 2026-10-03*
