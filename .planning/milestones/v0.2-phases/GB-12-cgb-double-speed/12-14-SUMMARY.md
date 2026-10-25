---
phase: 12-cgb-double-speed
plan: 14
subsystem: testing
tags: [cgb, double-speed, partition-invariance, snapshot, ctest]
requires:
  - phase: GB-12 plans 12-01 through 12-13
    provides: CGB speed switching, the measured stall constant, speed fixtures, and the mutant-core test seam
provides:
  - Explicit full-state digest tests for CGB speed-switch run partition invariance
  - Snapshot-backed 129-cut windows at the real stall end in both speed directions
  - STOP/IRQ, multicut, budget, and digest-sensitivity test coverage
affects: [GB-12, CGB-06, D-26, D-29]
actuals:
  tokens: 19265
  tasks: 3
  commits: 3
plan_head_before: 7ec15b98573e6309d27afb324fcfc0fa608f915d
plan_head_after: 2e8cbb35f5c594f69247b98899a569deb78f80bf
tech-stack:
  added: []
  patterns:
    - Explicit little-endian state digests cover independent machine state, ROM/RAM ownership, and observable output streams.
    - White-box snapshots copy cartridge RAM and test output while preserving ROM ownership and rejecting unsupported pointers.
key-files:
  created:
    - tests/test_cgb_partition.c
  modified:
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - Keep the shipped stall constant and speed fixture unchanged; derive real-stall positions from the core constant.
  - Treat already-enabled IME with a pending IRQ as an IRQ-before-STOP preemption case, separate from delayed-EI STOP switching.
  - Retain the natural timer-raised EI;STOP guest as the partitioned switch-plus-IRQ-dispatch proof; selector-level calls are supplementary only.
patterns-established:
  - Each real stall-end sweep shares one tested prefix snapshot, restores destination-owned ROM/RAM buffers, and compares an explicit digest.
  - Test-derived STOP retirement times are checked by stepping the generated guest instruction by instruction.
requirements-completed: [CGB-06]
coverage:
  - id: CGB-06-STALL-BOUNDARIES
    description: Full-state run partitioning matches around stall start and at both real-constant stall ends, with a timer wake inside the stall.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_partition_stall_start_window
        status: pass
      - kind: unit
        ref: cgb_partition_hostile_irq_in_stall
        status: pass
      - kind: unit
        ref: cgb_partition_stall_end_window_to_double
        status: pass
      - kind: unit
        ref: cgb_partition_stall_end_window_to_normal
        status: pass
  - id: CGB-06-SNAPSHOT-RESTORE
    description: Snapshot restore preserves the independent continuation digest and rejects unsupported pointer ownership.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_partition_snapshot_fidelity
        status: pass
      - kind: unit
        ref: cgb_partition_stall_end_window_to_double
        status: pass
      - kind: unit
        ref: cgb_partition_stall_end_window_to_normal
        status: pass
  - id: CGB-06-SEEDED-MULTICUT
    description: Seeded, fixed interior, and zero/sub-quantum budgets retain the same final digest and make valid progress.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_partition_stall_end_window_seeded
        status: pass
      - kind: unit
        ref: cgb_partition_interior_points
        status: pass
      - kind: unit
        ref: cgb_partition_seeded_multicut
        status: pass
      - kind: unit
        ref: cgb_partition_zero_and_subquantum
        status: pass
  - id: CGB-06-STOP-IRQ-SCENARIOS
    description: Pending-IRQ, held-button, LCD-off, back-to-back, and chained STOP scenarios are cut around step-measured retirement boundaries.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_partition_pending_at_stop
        status: pass
      - kind: unit
        ref: cgb_partition_held_button
        status: pass
      - kind: unit
        ref: cgb_partition_lcd_off
        status: pass
      - kind: unit
        ref: cgb_partition_back_to_back
        status: pass
      - kind: unit
        ref: cgb_partition_chained
        status: pass
  - id: CGB-06-DIGEST-SENSITIVITY
    description: A one-M joypad timing change and mutation of every digest input group, including ROM and cartridge RAM, change the digest.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_partition_sensitivity_joypad_shift
        status: pass
      - kind: unit
        ref: cgb_partition_sensitivity_digest_input
        status: pass
  - id: D-34-M16-NEGATIVE-CONTROL
    description: Per-call stall-wake sampling is detected by the M16 mutant while the zero-mask control passes.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: cgb_partition_mutant_m16
        status: pass
      - kind: integration
        ref: cgb_partition_mutant_m16_control
        status: pass
  - id: D-29-PER-CASE-CAP
    description: Every partition CTest has a half-dot cap and explicit timeout; measured local Debug wall times are recorded in CMake.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: ctest --test-dir build -R '^cgb_partition_' -V --no-tests=error -j1
        status: pass
      - kind: integration
        ref: ctest --test-dir build --output-on-failure --no-tests=error -j8
        status: pass
metrics:
  duration: "23m+ lower bound from first task commit; exact start not captured"
  completed: 2026-10-13
status: complete
---

# Phase GB-12 Plan 14: CGB Speed Partition Invariance Summary

**The full machine-state digest matches for partitioned and uninterrupted runs across the measured CGB speed-switch stall, both stall-end directions, STOP/IRQ paths, and seeded multicut cases.**

## Performance

- **Duration:** At least 23 minutes from the first task commit; the earlier start time was not captured.
- **Completed:** 2026-10-13.
- **Tasks:** 3.
- **Files modified:** 3.
- **Full local validation:** 853/853 CTests passed in 63.22 seconds; all 18 `cgb_partition_*` cases passed.
- **Real-stall windows:** 129 single-cut positions each at stall end switching to double and back to normal, using a shared prefix snapshot; the stall-start window also covers 129 cuts.
- **Seeded cases:** 256 multicut cases passed with seed `9e3779b97f4a7c15`; the largest CTest consumed 2,187,264 emulated half-dots and took 0.43 seconds locally.
- **Budget basis:** The 6,000,000 half-dot cap uses the prior research measurement of about 92 ns per half-dot from an ad-hoc `-O0` ASan run. That rate was not remeasured in this execution. The CMake comment records fresh local Darwin arm64 Debug timings for every case; they are not presented as ASan measurements.

## Accomplishments

- Added an explicit little-endian digest over CPU snapshot fields, speed/stall state, timer/divider/serial/DMA/PPU/APU/RTC state, bus reads, WRAM/HRAM/VRAM/OAM/palette data, cartridge RAM, RGB555 buffers, PCM, and serial output.
- Added test-only snapshot/restore helpers that deep-copy cartridge RAM and output accumulators, preserve destination-owned ROM/RAM pointers, verify immutable ROM bytes by digest, and reject unsupported non-null pointer fields.
- Proved every single cut in both 129-position real-constant stall-end windows against a restored uncut continuation. Snapshot fidelity is independently checked against an uninterrupted fresh run.
- Kept seeded short-stall, interior, budget, STOP, held-button, LCD-off, back-to-back, and chained cases as additive coverage. The 6,000,000 half-dot cap is enforced across combined windows inside each CTest.
- Added a natural timer guest that raises IF under DI, disables further timer requests, arms KEY1, then executes EI immediately before STOP. Its 129 cuts around measured STOP retirement preserve the natural switch and IRQ dispatch. A separate EI;NOP guest proves that already-enabled IME lets a pending IRQ preempt STOP decode; the direct selector/execution seam remains supplementary evidence.
- The pre-enabled-IME condition is explicitly distinguished from the delayed-EI case: when IME is already on with a pending interrupt before STOP decode, the run loop services the IRQ first, so that execution cannot demonstrate the case-3 switch at STOP.
- Preserved `GBB_SPEED_SWITCH_STALL_T` at `0x20004`, the measured AGE window `[0x20004, 0x20007]`, and the `speed.gb` SHA-256 `3c6e88de1e28d47566f7486dd13813c8fb1baf48ee336509e3902bd9ff8e2f3f`.

## Task Commits

1. **Task 1: Stall-start tracer and M16 negative/control pair** — `f558a49` (`test`).
2. **Task 2: Snapshot-backed real-stall, STOP, seeded, and budget windows** — `7d996d5` (`test`).
3. **Task 3: Joypad and digest-input sensitivity controls** — `2e8cbb3` (`test`).

## Files Created/Modified

- `tests/test_cgb_partition.c` — white-box partition scenarios, explicit digest, independent snapshot/restore, and sensitivity controls.
- `tests/CMakeLists.txt` — clean and mutant targets, 18 partition CTests with 60-second timeouts, 6,000,000 half-dot caps, and measured local timings.
- `tests/expected-tests.txt` — the exact Phase 12 plan 12-14 test inventory.

## Decisions Made

- Kept the shipped stall constant and fixture bytes unchanged; all real stall positions are derived from the existing core constant.
- Treated pre-enabled IME preemption and delayed-EI switch-plus-dispatch as distinct paths, with the natural timer-generated guest as the switch/dispatch proof.
- Retained explicit byte serialization and independent observable-state comparisons rather than hashing raw structures or relying on alias-shared snapshots.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test-model bug] Corrected generated STOP addressing and independently checked retirement timing.**
- **Found during:** Task 2.
- **Issue:** Chained synthetic guests advance six ROM bytes from one STOP opcode to the next; the initial test helper used an incorrect stride and formula-only cut positions could miss the intended boundary.
- **Fix:** Corrected the per-STOP address stride and added a step-measured retirement check for each generated scenario before running its cut window.
- **Files modified:** `tests/test_cgb_partition.c`.
- **Verification:** All STOP scenario windows pass with the predicted and measured retirement times equal; the pre-enabled-IME scenario uses its measured time because the IRQ handler runs before STOP.
- **Committed in:** `7d996d5`.

**Total deviations:** 1 auto-fixed test-model issue.
**Impact on plan:** The correction strengthens boundary placement; production core behavior and fixture identity were unchanged.

## Issues Encountered

- The plan’s fixed `IME=1` selector seam cannot by itself prove case-3 execution through `gbb_run`: if IME is already enabled and IF/IE are pending, the run loop dispatches the IRQ before decoding STOP. Kept that seam as supplementary coverage and added both a genuine preemption guest and the naturally pending timer `EI;STOP` partition case without changing core semantics.
- No package installs, hardware claims, source-runtime edits, or external fixture changes were needed.

## Validation Evidence

- `cmake --preset phase1 && cmake --build --preset phase1` — passed.
- `ctest --test-dir build -R '^cgb_partition_sensitivity_' --output-on-failure --no-tests=error` — 2/2 passed.
- `ctest --test-dir build -R '^cgb_partition_' --output-on-failure --no-tests=error -j8` — 18/18 passed.
- `ctest --test-dir build -R '^cgb_partition_' -V --no-tests=error -j1` — 18/18 passed and emitted per-case emulated half-dot totals; those local wall times are recorded in `tests/CMakeLists.txt`.
- `ctest --test-dir build --output-on-failure --no-tests=error -j8` — 853/853 passed in 63.22 seconds.
- Acceptance checks confirmed all 4 tracer names, at least 12 Task 2 names, both sensitivity names, four cap references, three restore references, and no literal stall-length constants in the partition source.
- Verified the speed fixture still matches its pinned SHA-256 and that the core stall macro and AGE window are unchanged.

## Self-Check: PASSED

The summary file and test artifact exist. Task commits `f558a49`, `7d996d5`, and `2e8cbb3` are ancestors of the plan code head recorded above.
