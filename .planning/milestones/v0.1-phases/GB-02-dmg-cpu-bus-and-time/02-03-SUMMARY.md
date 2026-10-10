---
phase: GB-02-dmg-cpu-bus-and-time
plan: 03
subsystem: cpu
tags: [sm83, cb-opcodes, flags, bus-timing, c17]
requires:
  - phase: GB-02-dmg-cpu-bus-and-time/02-02
    provides: Base opcode execution and private timed bus observer
provides:
  - Complete execution of all 256 CB-prefixed SM83 opcodes
  - Correct CB rotate/shift/BIT/RES/SET flags and register or WRAM results
  - Distinct BIT (HL) read and modifying (HL) read/write phases with full-cost preflight
affects: [GB-02-dmg-cpu-bus-and-time, cpu, timed bus]
requirements-completed: []
coverage:
  - id: D1
    description: All 256 documented CB encodings match independent register, memory, flag, PC, and cost expectations.
    requirement: CPU-01
    verification:
      - kind: unit
        ref: tests/test_cpu.c#cpu_cb_matrix (all 256 encodings)
        status: pass
      - kind: unit
        ref: tests/test_cpu.c#cpu_cb_flags_edges (00/01/7F/80/FF)
        status: pass
    human_judgment: false
  - id: D2
    description: BIT (HL) is read-only, modifying CB (HL) instructions use read/write phases, and short budgets preserve guest state.
    requirement: CPU-01
    verification:
      - kind: unit
        ref: tests/test_cpu.c#cpu_cb_wram,cpu_cb_budget,cpu_cb_timed_access
        status: pass
    human_judgment: false
tech-stack:
  added: []
  patterns: [compact CB group decode, complete-instruction cycle preflight, per-instance timed bus observation]
key-files:
  created: []
  modified: [src/core/gabbaboy.c, tests/test_cpu.c, tests/CMakeLists.txt, tests/expected-tests.txt]
key-decisions:
  - "CB register operations cost 16 half-dots; BIT (HL) costs 24; other (HL) CB operations cost 32."
  - "BIT preserves carry and sets H; RES and SET preserve flags; rotate/shift groups set Z and carry from their results."
metrics:
  duration: 6min
  completed: 2026-10-06
status: complete
commits: 4
plan_head_before: 6ce122ede49b6ebd3cfa9889a1464a1a3f9d4bcd
plan_head_after: 180042cb77c6b8749a3748b221c7609dd48e59b4
---

# Phase 2 Plan 03: Complete CB SM83 Execution Summary

**The DMG CPU now executes every CB-prefixed rotate, shift, bit, reset, and set opcode with verified flags, WRAM results, and timed memory phases.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-10-06T19:00:03Z
- **Completed:** 2026-10-06T19:05:30Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added public-API guest regressions proving BIT (HL) performs a read without a write and RES (HL) performs a timed read/write while preserving flags.
- Added a one-half-dot-short memory CB budget case that returns at the prior instruction boundary without reading or mutating the target.
- Added an independently calculated semantic matrix that executes every CB byte and checks registers, WRAM, flags, next PC, and register versus memory cycle costs.
- Added boundary checks for input values 00, 01, 7F, 80, and FF and bus timestamps for BIT's read-only path and RES's read/modify/write path.
- Implemented all eight rotate/shift operations plus BIT, RES, and SET across all eight register selectors.

## Task Commits

1. **Run CB BIT and RES on WRAM through the public API** — `aabdcd6` (test), `d56d411` (feat)
2. **Complete the full CB opcode matrix** — `52d3656` (test), `180042c` (feat)

TDD RED records are in `build/tdd-red-02-03-task1.json` and `build/tdd-red-02-03-task2.json`. Both passed `gsd_run check tdd-red-evidence` with `RED_EVIDENCE_OK`. The first target failed on unchanged WRAM after the CB placeholder; the second failed on the missing rotate result after executing the first opcode in the 256-byte matrix. No separate refactor was needed.

## Files Modified

- `src/core/gabbaboy.c` — CB decode costs and rotate, shift, BIT, RES, and SET semantics.
- `tests/test_cpu.c` — WRAM/budget tests, all-encoding matrix, edge values, and timed bus checks.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — registered the five CB tests in the required inventory.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking Issue] Moved the CB helper below the register write accessor.**
- **Found during:** Task 1 implementation
- **Issue:** The first build rejected the helper's call to `set_reg` because its definition appeared later in the C file.
- **Fix:** Placed the helper after both register accessors; no public interface change was needed.
- **Files modified:** `src/core/gabbaboy.c`
- **Verification:** Focused CB tests and the complete CTest inventory passed.
- **Committed in:** `d56d411`

## Verification

- Task 1: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^cpu_cb_(wram|budget)$'` — 2/2 passed.
- Task 2: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^cpu_cb_(matrix|flags_edges|timed_access)$'` — 3/3 passed.
- Overall: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` — 42/42 passed, including installed runner and C/C++ consumers.
- Independent RED evidence validation returned `RED_EVIDENCE_OK` for both TDD tasks.

## Issues Encountered

The first focused implementation run exposed an expected-flag mistake in the new test: SCF preserves the initial zero flag, while BIT of set bit zero clears zero. The test was corrected to expect carry-plus-half-carry (`0x30`). Timestamp expectations were aligned with the existing `LD (HL),A` write phase at offset 16. The final focused and full inventories pass.

## User Setup Required

None.

## Next Phase Readiness

Phase 2 Plan 02-03 execution is complete. Phase 2 remains in progress; next is Plan 02-04, **CPU control states and interrupts**. Continue with `$gsd-execute-phase 2`. Phase 3 — **Visible Interactive DMG** — remains gated on complete Phase 2 verification and owner direction. Full CPU requirement traceability remains pending final phase verification.

---
*Phase: GB-02-dmg-cpu-bus-and-time*
*Completed: 2026-10-06*

## Self-Check: PASSED

- Summary was written after all four task commits and their hashes were verified as ancestors of the phase branch.
- Task commit count is measured as 4 from `6ce122ede49b6ebd3cfa9889a1464a1a3f9d4bcd` through `180042cb77c6b8749a3748b221c7609dd48e59b4`; the plan metadata commit is outside this task evidence range.
- All five declared CB test names are registered and passed; the complete 42-test suite passed.
- No new stubs, skipped tests, or unrun automated verification were found in the modified files.
