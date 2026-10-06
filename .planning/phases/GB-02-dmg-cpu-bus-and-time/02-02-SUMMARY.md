---
phase: GB-02-dmg-cpu-bus-and-time
plan: 02
subsystem: cpu
tags: [sm83, opcodes, timing, lockup, bus]
requires:
  - phase: GB-02-dmg-cpu-bus-and-time/02-01
    provides: ROM-only guest memory path and WRAM/HRAM bus behavior
provides:
  - Unprefixed base opcode decode, register/flag execution, and conditional cycle preflight
  - Per-instance persistent unused-opcode lockup with PC/opcode result metadata
  - Private timed bus observer and CPU matrix, flags, stack, and lockup regressions
affects: [GB-02-dmg-cpu-bus-and-time/02-03, cpu, runner]
actuals:
  tokens: 8818
  tasks: 2
  commits: 3
plan_head_before: d21fa1508c6e3da8f6764b89722ffd940bf0bab2
plan_head_after: e7c55cef0db2b7a87cb15b9f91668c531690f5e7
tech-stack:
  added: []
  patterns: [private per-instance timed bus observation, complete-instruction cycle preflight]
key-files:
  created: [tests/test_cpu.c]
  modified: [src/core/gabbaboy.c, include/gabbaboy/gabbaboy.h, src/runner/main.c, tests/test_api.c, tests/test_tracer.c, tests/test_bus.c, tests/test_loader.c, tests/CMakeLists.txt, tests/expected-tests.txt]
key-decisions:
  - "Unused encodings retain the offending PC/opcode and stop deterministically until reset."
  - "The CB-prefixed extension remains for Plan 02-03; this plan executes unprefixed base operations."
patterns-established:
  - "Cycle costs are selected before mutation and conditional paths use their own full cost."
  - "Test bus events are recorded per instance from the same helpers that perform memory accesses."
requirements-completed: [CPU-01, CPU-04]
coverage:
  - id: D1
    description: Every base byte has an explicit legal/unused classification and unused opcodes lock up persistently until reset.
    requirement: CPU-01
    verification:
      - kind: unit
        ref: tests/test_cpu.c#base_matrix
        status: pass
      - kind: unit
        ref: tests/test_cpu.c#illegal_lockup and tests/test_api.c#illegal_lockup
        status: pass
    human_judgment: false
  - id: D2
    description: Conditional CALL/RET and representative arithmetic/memory operations expose complete budget costs and timed bus effects.
    requirement: CPU-04
    verification:
      - kind: integration
        ref: tests/test_cpu.c#call_stack,conditional_budget,flags_edges,timed_access
        status: pass
    human_judgment: false
duration: 38min
completed: 2026-10-06
status: complete
---

# Phase GB-02 Plan 02: Complete legal base opcode matrix and unused-opcode lockup Summary

**Bootless DMG execution now decodes the unprefixed SM83 instruction set, observes timed guest bus operations, and reports persistent unused-opcode lockup with reproducible metadata.**

## Performance

- **Duration:** 38 min
- **Started:** 2026-10-06T17:57:00Z
- **Completed:** 2026-10-06T18:35:00Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments

- Added conditional CALL/RET execution with stack byte ordering, branch-specific cost preflight, and per-instance timestamp/address/access/value bus observations.
- Implemented base opcode classification and execution, arithmetic/flag updates, and persistent D3-family lockup that returns the original PC/opcode until reset.
- Updated API, runner, tracer, and legacy timing assertions; added 6 named CPU cases plus API lockup coverage.
- Verified the complete offline CTest suite and installed C/C++ consumers: 37/37 passed.

## Task Commits

1. **Task 1: Execute a conditional guest call and stack round-trip** - `7f4d6ed` (test), `6a972fe` (feat)
2. **Task 2: Complete legal base opcode matrix and unused-opcode lockup** - `e7c55ce` (feat)

**Plan metadata:** `b359d29` (summary); final state/roadmap metadata commit is recorded separately.

## Files Created/Modified

- `tests/test_cpu.c` - Generated-ROM CPU matrix, conditional stack/budget, lockup, flags, and timed-access checks.
- `src/core/gabbaboy.c`, `include/gabbaboy/gabbaboy.h` - Instruction decode/execution, timed bus observer, and lockup result state.
- `src/runner/main.c`, `tests/test_api.c`, `tests/test_tracer.c` - Lockup result mapping and regression coverage.
- `tests/test_bus.c`, `tests/test_loader.c` - Updated expected whole-instruction timing boundaries.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` - Registered the new regression cases.

## Decisions Made

- Unused opcodes are a persistent CPU lockup distinct from unsupported bus behavior; reset clears lockup while preserving the loaded ROM.
- The CB-prefixed instruction map remains the direct scope of Plan 02-03; this plan classifies the CB prefix as legal rather than an unused encoding.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected existing whole-instruction timing expectations after expanding the decoder.**
- **Found during:** Task 2
- **Issue:** Existing API/loader/bus tests assumed prior tracer-only instruction costs, including budgets that ended between newly supported instructions.
- **Fix:** Adjusted fixture budgets to exact whole-instruction boundaries and corrected the absent-cartridge write path expectation.
- **Files modified:** `tests/test_api.c`, `tests/test_bus.c`, `tests/test_loader.c`
- **Verification:** Full CTest suite passed 37/37.
- **Committed in:** `e7c55ce`

### Process Deviation

Task 2's broad implementation rewrite began before its new matrix assertions were captured as a separate RED run. The targeted new cases and the full suite were then built and passed before the task commit. Task 1 followed RED/GREEN with commits `7f4d6ed` and `6a972fe`.

**Total deviations:** 1 auto-fixed correctness issue; 1 process deviation.
**Impact on plan:** No planned scope was omitted; the CB extension is the following plan's scope.

## Issues Encountered

- The initial matrix verification used an 8-half-dot budget, which cannot start a CB-prefixed instruction; increasing the independent one-step matrix budget to 64 exposed the intended classification result.
- Existing lifecycle/loader tests stopped at an insufficient budget after accurate whole-instruction costs replaced the tracer subset's earlier costs.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 02-02 is complete; Phase GB-02 remains in progress. Plan 02-03 owns CB-prefixed semantics. The full phase verification and later waves remain pending.

---
*Phase: GB-02-dmg-cpu-bus-and-time*
*Completed: 2026-10-06*

## Self-Check: PASSED

- Summary file exists at the required phase path.
- Task commit hashes `7f4d6ed`, `6a972fe`, and `e7c55ce` are present in current HEAD ancestry.
- Measured ledger range contains three commits from `d21fa1508c6e3da8f6764b89722ffd940bf0bab2` through `e7c55cef0db2b7a87cb15b9f91668c531690f5e7`.
