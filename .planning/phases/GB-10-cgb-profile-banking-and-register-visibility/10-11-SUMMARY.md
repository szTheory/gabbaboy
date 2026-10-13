---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 11
subsystem: core-cpu-tests
tags: [cgb, key0, key1, stop, fail-closed]
requires: [10-10]
provides: [armed-STOP latch on CGB, KEY0 lock behavioural probe]
affects: [12]
key-files:
  created: []
  modified: [src/core/gabbaboy.c, docs/model-gates.md, docs/cgb-profile.md, tests/test_cgb_visibility.c, tests/CMakeLists.txt, tests/expected-tests.txt]
requirements-completed: [CGB-02]
status: complete
commits: 1
plan_head_before: 0e848f2bbcaf8be801bd711be9c1e9df88e12eda
plan_head_after: 30bb2e2
actuals:
  tokens: 20000
  tasks: 2
  commits: 1
duration: 25 min
completed: 2026-10-12
coverage:
  - deliverable: "STOP with KEY1 armed latches UNSUPPORTED_BUS at FF4D on CGB mode; unarmed, compat and DMG still STOP"
    verification:
      - {kind: ctest, ref: "cgb_stop_armed_cgb", status: pass}
      - {kind: ctest, ref: "cgb_stop_unarmed_cgb", status: pass}
      - {kind: ctest, ref: "cgb_stop_compat_ignores_key1", status: pass}
      - {kind: ctest, ref: "cgb_stop_dmg_control", status: pass}
    human_judgment: false
  - deliverable: "KEY0 locked after boot, probed by behaviour, with cross-column and idempotency checks"
    verification:
      - {kind: ctest, ref: "cgb_key0_lock_cgb", status: pass}
      - {kind: ctest, ref: "cgb_key0_lock_compat", status: pass}
      - {kind: ctest, ref: "cgb_key0_lock_cross_column", status: pass}
      - {kind: ctest, ref: "cgb_key0_lock_reset_idempotent", status: pass}
    human_judgment: false
---

# Phase 10 Plan 11: KEY0 lock and armed STOP Summary

STOP with KEY1 armed on the CGB profile in CGB mode now retires and reports `GBB_STOP_UNSUPPORTED_BUS` at $FF4D (new GATE-74, CGB_ONLY, DEFERRED(12)) instead of entering the DMG sleep, and KEY0 is proven locked by behaviour in both CGB columns.

## Accomplishments

- `execute` STOP case: when `model_is_cgb`, mode is CGB and KEY1 bit 0 is armed, the bus-unsupported latch is set with address $FF4D and `stopped` is not set. GATE-62 (shared STOP) stays UNKNOWN research:12; GATE-74 row added to docs/model-gates.md; `STOP with KEY1 armed: DEFERRED(12)` section added to docs/cgb-profile.md.
- `cgb_stop_*`: armed_cgb (stop reason, seam address, next run is not STOPPED, guest continues; in-test control that the unarmed program does STOP), unarmed_cgb (also arm-then-disarm), compat_ignores_key1, dmg_control.
- `cgb_key0_lock_*`: KEY0 writes of $00/$04/$80/$C0 read back $FF in both columns; behavioural VBK probe differs between columns (CGB: FF4F reads $FF after writing 1, 8000 bank 0 reads $00; compat: $FE and $5A); mode unchanged before/after and after reset; cross_column requires each column's expectation to reject the other's run plus a mutated read-back; reset_idempotent repeats the sequence, resets twice and compares `gbb_get_info` bytes.

## Verification

- Full suite 485/485 pass; `verify-dmg-baseline.sh` prints `baseline status=pass`, rows=0.
- Negative control: replacing the KEY1-armed condition with `0` made `cgb_stop_armed_cgb` fail (others still passed); source restored before commit. model_gates tests green with the new tag.

## Deviations from Plan

**1. Single commit for both tasks.** Both tasks edit the same test file, CMake list and expected-tests list in interleaved hunks; splitting would have needed a synthetic partial state. Both are in commit 30bb2e2.

**2. Expectation note.** The plan's compat expectation "FF4F reads $FE after the VBK write" is implemented as the post-write-1 read, with the CGB column expected to read $FF (bit 0 set, $FE|1) there; this is the discriminating read between columns and follows the existing vbk_tracer evidence. No expectation was tuned to code output.

Otherwise none.

## Known Stubs

None. STOP/KEY1 speed switch is intentionally DEFERRED(12). MagenTests key0_lock_after_boot unchanged (skipped per Phase 9).

## Threat Flags

None. T-10-17 mitigated by cgb_stop_armed_cgb with the unarmed and DMG controls.

## Self-Check: PASSED
