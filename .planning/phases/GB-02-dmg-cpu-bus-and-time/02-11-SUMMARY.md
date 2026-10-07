---
phase: GB-02-dmg-cpu-bus-and-time
plan: 11
subsystem: core
tags: [sm83, interrupts, timer, diagnostics, tdd]
requires:
  - phase: GB-02-10
    provides: Checksum-derived post-boot flags and corrected return stack phases
provides:
  - Consecutive EI preserves the first delayed IME enable
  - Timer deadlines precede interrupt IF bus diagnostics at the same entry phase
affects: [CPU-02, CPU-03, CPU-04, interrupt-verification]
actuals:
  tokens: 2049
  tasks: 2
  commits: 4
commits: 4
plan_head_before: 7955b77ee6e0155ae3e14596e71c716f89b49941
plan_head_after: 0e09138b093281b01e70a05023aca391d91c0102
tech-stack:
  added: []
  patterns: [Instruction-boundary EI latch preservation, device advance before timed bus diagnostics]
key-files:
  created: []
  modified: [src/core/gabbaboy.c, tests/test_control.c, tests/CMakeLists.txt, tests/expected-tests.txt]
key-decisions:
  - Preserve an active EI countdown when another EI executes; DI still cancels it and RETI still enables immediately.
  - Advance devices to interrupt IF acknowledgement time before clearing IF and emitting the bus record.
requirements-completed: []
duration: 12min
completed: 2026-10-07
status: complete
---

# Phase GB-02 Plan 11: EI and Interrupt Diagnostic Ordering Summary

**Consecutive EI now vectors at the first scheduled boundary, and timer events appear before same-time interrupt IF acknowledgement diagnostics.**

## Accomplishments

- `EI;EI` with pending IE/IF vectors at t=96–136 before the following NOP. The regression asserts vector PC `0x40`, return address `0x010a`, stack bytes, and identical whole/split execution. Existing EI delay, EI;DI, RETI, and entry tests remain green.
- Interrupt entry advances devices through the IF acknowledgement phase before clearing IF or emitting that bus write. A guest timer overflow at t=208 reloads at t=216 during VBlank entry; diagnostics are instruction at 208, timer then IF write at 216, stack writes at 224 and 232, and the next timer edge at 240. The test checks all adjacent timestamps, IF value `0xe4`, vector `0x40`, stack return `0x0115`, 40-half-dot cost, short-budget nonmutation, and whole/split equality.
- Both cases are registered in the exact CTest inventory.

## TDD Gate Compliance

| Task | RED evidence | Semantic assessment | RED commit | GREEN commit |
|---|---|---|---|---|
| EI chain | `build/tests/test_control interrupt_ei_chain`, exit 1; target TAP assertion failed at the 136-half-dot vector boundary; `gsd_run check tdd-red-evidence` returned `RED_EVIDENCE_OK` | The current core ran the NOP and consumed only 104 half-dots, so it could not complete the expected vector within budget. | `37b193e` | `d5414e7` |
| Diagnostic order | `build/tests/test_control interrupt_diagnostic_order`, exit 1; target TAP assertion failed on the expected first timer record; `gsd_run check tdd-red-evidence` returned `RED_EVIDENCE_OK` | Six records were present, but the IF write preceded the timer reload at the same timestamp. | `fedf35b` | `0e09138` |

The temporary RED records live in the ignored local build directory; no synthetic report was committed. No refactor commit was needed.

## Verification

At committed core revision `0e09138b093281b01e70a05023aca391d91c0102`, `cmake --preset phase1` and `cmake --build --preset phase1` passed. The combined focused selection `interrupt_ei_chain`, `interrupt_ei_delay`, `interrupt_entry`, `interrupt_diagnostic_order`, `interrupt_budget`, and `timer_mid_instruction` passed 6/6 with no missing case.

The complete offline CTest inventory ran 98/98 cases: 94 passed, 4 failed. The failures are the previously open Mooneye required suite and its DAA/two timer cases, which still stop at unsupported LY before the advertised protocol. The fresh runner receipt reports core revision `0e09138b093281b01e70a05023aca391d91c0102`. No new failure appeared in the other 94 cases; this plan does not complete CPU-02/03/04 or Phase GB-02.

## Deviations from Plan

The new diagnostic regression initially expected timer vector `0x50`. Its guest arms VBlank as the selected interrupt and timer IF only during entry, so the correct vector is `0x40`; the test expectation was corrected before the GREEN commit. The first draft also expected five diagnostic records; the independently timed next timer edge at t=240 adds a sixth. Neither correction changed the intended timer-before-IF assertion or the pinned test workload.

## Open Issues

The four Mooneye unsupported-LY failures, fixture cross-host byte reproduction gap, and remaining Phase 2 verification work remain open. Keep the fixed eligible denominator and all CPU requirements pending until the complete phase evidence passes. Phase 3 — Visible Interactive DMG — remains paused.

## Self-Check: PASSED

All four declared source/test files exist. The four task commits are ancestors of HEAD, and the measured plan interval contains four commits. No fixture, manifest, or owner runtime file was staged by this plan.
