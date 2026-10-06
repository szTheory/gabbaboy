---
phase: quick-261006-r6w
plan: 01
subsystem: testing
tags: [dmg, bus, checksum, ctest]
requires:
  - phase: GB-02 Plan 02-10
    provides: checksum-selected bootless DMG-CPU-B startup flags
provides:
  - Valid zero-checksum synthetic bus ROM that starts with carry clear.
  - Passing unsupported-stack rejection regression with unchanged exact CTest inventory.
affects: [Phase GB-02 verification]
actuals:
  tokens: 45
  tasks: 1
  commits: 1
tech-stack:
  added: []
  patterns: [Assert generated ROM checksum after choosing an independent header value.]
key-files:
  created: []
  modified: [tests/test_bus.c]
key-decisions:
  - "Set header byte 0x134 to 0xE7 and retain the existing checksum helper; its result must be zero."
requirements-completed: []
duration: 3min
completed: 2026-10-06
status: complete
---

# Quick 261006-r6w: Bus Unsupported Stack Fixture Summary

**The generated bus ROM now selects carry-clear startup flags, allowing RET NC to exercise the intended unsupported-stack rejection.**

## Accomplishments

- Repaired the synthetic ROM builder in `tests/test_bus.c` with an independently calculated header value and an assertion that the computed checksum is zero.
- Preserved the ROM validator, RET NC table entry, atomic rejection checks, untaken-return assertions, stack addresses, timing, and CTest registrations.
- This is the follow-up fixture repair recorded by Phase GB-02 Plan 02-10. It does not qualify CPU-01, CPU-02, or Phase GB-02.

## Task Commit

- Task 1: `3231d21` — `test(261006-r6w): select carry-clear bus fixture profile`; only `tests/test_bus.c` changed.

## Verification

- `cmake --preset phase1 -DGBB_TEST_INSTALL_PREFIX=`, `cmake --build --preset phase1`, and focused `ctest --preset phase1 --output-on-failure --no-tests=error -R '^bus_unsupported_stack$'` passed (1/1).
- A fresh full offline JUnit report at `build/bus-repair-inventory.xml` contains exactly 96 unique cases matching `tests/expected-tests.txt`, no skips, and 92 passes. `bus_unsupported_stack` passes.
- Exactly four known Mooneye unsupported-LY cases still fail: `mooneye_required_suite`, `mooneye_case_daa`, `mooneye_case_tim00`, and `mooneye_case_tim00-div-trigger`. The full CTest process exits nonzero as expected for those failures; the exact report assertion passes.
- `git diff --check` passed, and the implementation commit contains no tracked deletions.

## Deviations from Plan

- The plan's JUnit output argument `build/bus-repair-inventory.xml` resolved under the CTest preset's build working directory, producing `build/build/bus-repair-inventory.xml`. Reran with `--output-junit bus-repair-inventory.xml` and validated the fresh report at the intended `build/bus-repair-inventory.xml`. No source or inventory change was needed.

## Evidence Limits

- T-02-SC remains an accepted shared low-severity fixture/tool-supply control; this repair does not qualify the Mooneye fixtures.
- CPU requirements and Phase GB-02 remain pending independent verification. The known corpus failures remain open.

## Self-Check: PASSED

- `tests/test_bus.c` exists, implementation commit `3231d21` is an ancestor of HEAD, and the only implementation diff in that commit is the intended fixture file.
