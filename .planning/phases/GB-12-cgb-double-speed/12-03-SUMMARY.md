---
phase: 12-cgb-double-speed
plan: 03
subsystem: cgb-speed-verification
tags: [cgb, double-speed, mutation-testing, reset, tdd]
requires:
  - phase: 12-01
    provides: "CGB speed-switch tracer, private speed-state seam and pre-change identity pins"
provides:
  - "Exactly-once multi-site runtime-mask mutant generator with M5, M7, M18, M24, M25 and M26"
  - "Opcode and CB timing, bus-offset, NOP-loop and interrupt timing contracts"
  - "Independent reset checks for speed, stall and KEY1 state"
affects: [12-04, 12-05, 12-06, 12-07, 12-08, 12-09]
actuals:
  tokens: 6393
  tasks: 3
  commits: 6
  plan_head_before: 102d44d4ce93a122f51c385e8932403052386d47
  plan_head_after: ba04065bb622e88bbef348af6f5ed3a8f0a08c62
tech-stack:
  added: []
  patterns:
    - "Build-tree-only mutant cores use per-id anchor tables, exactly-once forward and reverse checks, and runtime masks"
    - "Negative controls pair each runtime mutant with a mask-zero control"
key-files:
  created:
    - cmake/P12Mutants.cmake
    - .planning/phases/GB-12-cgb-double-speed/12-03-SUMMARY.md
  modified:
    - src/core/gabbaboy.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/test_cgb_speed_internal.c
key-decisions:
  - "Keep mutant copies under the build tree and compile them only into the private white-box test executable."
  - "Reset mutants target reset-boundary state: the post-boot table also initializes speed and KEY1 during creation and ROM loading."
requirements-completed: [CGB-06]
coverage:
  - id: GB-12-03-01
    description: "M5/M7 runtime mutants, mask-zero controls, duplicate-anchor rejection and the off-M stall static-assert mutant validate the shared mutant harness."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_speed_tracer_switch
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m5_stall_sets_stopped and cgb_speed_mutant_m5_stall_sets_stopped_control
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m7_devices_frozen and cgb_speed_mutant_m7_devices_frozen_control
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_anchor_guard
        status: pass
      - kind: unit
        ref: cgb_speed_stall_static_assert_mutant
        status: pass
  - id: GB-12-03-02
    description: "All base and CB opcode costs, bus offsets, 1000-NOP normal/double-speed loops, interrupt costs, and M18 scaling mutation are checked."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_speed_cpu_ticks
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m18_cost_unscaled and cgb_speed_mutant_m18_cost_unscaled_control
        status: pass
      - kind: other
        ref: "gsd check tdd-red-evidence build/tdd-red-12-03-task2.json returned RED_EVIDENCE_OK for the unscaled-cost scratch mutant"
        status: pass
  - id: GB-12-03-03
    description: "Reset independently clears double speed, speed-switch stall kind and duration, and KEY1 arming; each mutant is detected and its mask-zero control passes."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_speed_reset_double_speed
        status: pass
      - kind: unit
        ref: cgb_speed_reset_stall
        status: pass
      - kind: unit
        ref: cgb_speed_reset_key1
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m24_reset_retains_double_speed and cgb_speed_mutant_m24_reset_retains_double_speed_control
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m25_reset_retains_stall and cgb_speed_mutant_m25_reset_retains_stall_control
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m26_reset_retains_key1_arm and cgb_speed_mutant_m26_reset_retains_key1_arm_control
        status: pass
      - kind: other
        ref: "gsd check tdd-red-evidence build/tdd-red-12-03-task3.json returned RED_EVIDENCE_OK for the reset KEY1 scratch mutant"
        status: pass
  - id: GB-12-03-04
    description: "The full suite, CGB identity pins and the DMG baseline remain unchanged."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -j8 (713/713)"
        status: pass
      - kind: unit
        ref: cgb_speed_identity_pin and cgb_speed_identity_pin_flipped
        status: pass
      - kind: unit
        ref: cgb_instance_isolation
        status: pass
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh (baseline status=pass)"
        status: pass
      - kind: unit
        ref: summary_coverage
        status: pass
duration: 19 min
completed: 2026-10-13
status: complete
commits: 6
---

# Phase 12 Plan 03: Runtime-mask CPU timing and reset mutants Summary

The CGB double-speed contract now has a reusable exactly-once mutant generator, opcode and bus-timing checks, and independent reset tests that detect speed-state regressions.

## Performance

- **Duration:** 19 min
- **Tasks:** 3
- **Files modified:** 5
- **Task commits:** 6, measured from the persisted plan ledger

## Accomplishments

- Added a build-tree-only mutant-core generator with forward and reverse exactly-once anchor checks, runtime mask selection, a duplicate-anchor negative control, and a compile-time stall alignment negative control.
- Added M5/M7 controls for the STOP transition and frozen-device regressions.
- Checked every base and CB opcode cost, normal/double-speed instruction costs, five aligned read/write offsets, 1000 NOP executions at each speed, and 40/20-half-dot interrupt entry. M18 mutates all three timing-shift sites.
- Added separate reset tests for double speed, speed-switch stall state and KEY1 arming, with M24/M25/M26 mutants and controls.
- Verified the CGB identity pins, preserved the DMG baseline, and passed all 713 CTest cases.

## TDD Evidence

- **Task 2 RED:** `build/tdd-red-12-03-task2.json` was accepted as `RED_EVIDENCE_OK`. The scratch M18 unscaled-cost core failed `cgb_speed_cpu_ticks` at the intended double-speed instruction-cost assertion. **GREEN:** the completed M18 mutant/control pair passes, while `cgb_speed_cpu_ticks` passes on the clean generated core.
- **Task 3 RED:** `build/tdd-red-12-03-task3.json` was accepted as `RED_EVIDENCE_OK`. A scratch M26 core that re-armed KEY1 after reset failed the named reset assertion. **GREEN:** all three reset cases pass, and each field mutant is detected with its mask-zero control passing.
- No refactor-only commit was needed.

## Task Commits

- `c154786`: `feat(12-03): add runtime-mask speed mutant harness`
- `e0b5d03`: `test(12-03): add CPU double-speed scaling contract`
- `c1c8257`: `feat(12-03): add CPU timing scale mutant`
- `449f60f`: `test(12-03): add reset speed state contract`
- `f38d286`: `feat(12-03): add independent reset state mutants`
- `ba04065`: `test(12-03): split CPU and reset behavior cases`

## Deviations from Plan

- **Reset-boundary mutant setup:** M24 and M26 inject their fault only when resetting a machine with nonzero elapsed time, so creation and ROM-load initialization remain mask-zero-equivalent. M25 omits both explicit stall clears. The post-boot register table also initializes KEY1 and speed during initial state setup, so a naive omission mutant would be masked before the reset behavior under test.
- **TDD RED exercised by scratch-mutated core copies:** the clean core already implemented these contracts from plan 12-01. The scratch copies make the target assertion fail for the planned regression without changing committed production behavior.

## Auth Gates

None.

## Known Stubs

None.

## Threat Flags

None. Generated mutant cores remain test-only build-tree artifacts.

## Self-Check: PASSED

- Summary file exists and all six task commits are ancestors of the current plan head.
- `summary_coverage` passed after this file was written.
