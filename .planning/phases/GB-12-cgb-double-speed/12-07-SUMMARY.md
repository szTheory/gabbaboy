---
phase: 12-cgb-double-speed
plan: 07
subsystem: cpu
tags: [cgb, stop, interrupts, stall, timing, mutants]
requires:
  - phase: 12-cgb-double-speed
    provides: STOP cases, the speed-switch stall branch, and the guest-driven timer IRQ tracer from plan 12-06
provides:
  - Timer IRQ wake from a speed-switch stall at persisted M-cycle boundaries for IME-on and IME-off guests
  - EI retirement before STOP stall entry and the CGB normal-speed realignment tail
  - Macro-derived stall duration, bounded budget behavior, live device advancement, and pre-mutation time headroom validation
affects: [12-cgb-double-speed/12-08, 12-cgb-double-speed/12-09, cgb-speed-verification]
actuals:
  tokens: 10017
  tasks: 3
  commits: 5
commits: 5
plan_head_before: 80bf2b5eaffc598e2016ca699d08cce59aed8ee5
plan_head_after: 07d00cf0192b94fe1a595e3a85e07ed046ecbc29
tech-stack:
  added: []
  patterns: [persisted M-cycle stall steps, paired runtime mutants and mask-zero controls]
key-files:
  created: [.planning/phases/GB-12-cgb-double-speed/12-07-SUMMARY.md, .planning/phases/GB-12-cgb-double-speed/continue.md]
  modified: [src/core/gabbaboy.c, tests/test_cgb_speed_internal.c, cmake/P12Mutants.cmake, tests/CMakeLists.txt, tests/expected-tests.txt]
key-decisions:
  - "Sample the speed-switch IRQ wake only between persisted M-cycle stall steps so host budget splits do not change resume time."
  - "Apply a four-half-dot REALIGN stall only when a CGB entry into normal speed lands at phase four; leave the provisional stall constant for plan 12-09 to re-measure."
  - "Keep the future signed M31 stall-offset seam mask-gated and zero at its current default."
patterns-established:
  - "Every stall behavior mutant has a named failing case and a mask-zero control; the M31 zero-offset seam has a passing mutant-mode check."
  - "Switch headroom is checked before the STOP instruction mutates CPU, speed, KEY1, divider, or stall state."
requirements-completed: [CGB-06]
coverage:
  - id: GB-12-07-WAKE
    description: "A timer IRQ ends the speed-switch stall at an M-cycle boundary; IME dispatch, IME-off resume, EI;STOP, and host budget partitioning retain their contracts."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_speed_wake_ime_on
        status: pass
      - kind: unit
        ref: cgb_speed_wake_ime_off
        status: pass
      - kind: integration
        ref: cgb_speed_ei_stop
        status: pass
      - kind: unit
        ref: cgb_speed_wake_m_boundary
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m13_wake_ime_off_ignored and its mask-zero control
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m16_wake_sampled_per_call and its mask-zero control
        status: pass
      - kind: integration
        ref: cgb_speed_mutant_m34_ei_delay_not_retired and its mask-zero control
        status: pass
  - id: GB-12-07-REALIGN
    description: "Every CGB entry into normal speed applies the D-09 four-half-dot CPU realignment tail only at phase four, and does not cut the tail short on pending IF."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_speed_realign
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m23_realignment_omitted and its mask-zero control
        status: pass
  - id: GB-12-07-LENGTH-BUDGET
    description: "The named stall duration is exact at both destination speeds, stays M-cycle aligned, and consumes no more than the caller budget."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_speed_stall_length
        status: pass
      - kind: unit
        ref: cgb_speed_budget_semantics
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m6_stall_one_m_long and its mask-zero control
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m21_stall_one_m_short and its mask-zero control
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m28_stall_one_half_dot_long and its mask-zero control
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m9_stall_budget_unbounded and its mask-zero control
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m31_stall_offset_noop
        status: pass
  - id: GB-12-07-DEVICES
    description: "CGB stall time advances PPU, DIV/TIMA, serial, OAM DMA, and audio output without exposing STOPPED, HALTED_IDLE, or NO_PROGRESS to the host."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: cgb_speed_stall_devices_advance
        status: pass
      - kind: integration
        ref: cgb_speed_never_stopped
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m5_stall_sets_stopped_devices and its mask-zero control
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m7_devices_frozen_devices and its mask-zero control
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m5_stall_sets_stopped_never and its mask-zero control
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m7_devices_frozen_never and its mask-zero control
        status: pass
  - id: GB-12-07-HEADROOM
    description: "An armed switching STOP rejects insufficient worst-case time headroom without mutation and proceeds with exactly one more half-dot available."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: cgb_speed_headroom
        status: pass
      - kind: unit
        ref: cgb_speed_mutant_m22_switch_headroom_omitted and its mask-zero control
        status: pass
  - id: GB-12-07-REGRESSION
    description: "The Phase 12 speed-switch changes preserve STOP, DMG identity, model-gate contracts, and the frozen DMG baseline across the complete CTest inventory."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: ctest --test-dir build -j8 --output-on-failure --no-tests=error
        status: pass
      - kind: other
        ref: bash tests/scripts/verify-dmg-baseline.sh
        status: pass
duration: "112m 29s commit window; setup before the first task commit was not timed"
completed: 2026-10-13
status: complete
---

# Phase 12 Plan 07: CGB Double-Speed Stall Semantics Summary

**CGB speed-switch stalls now wake on timer IRQ at stable M-cycle boundaries, realign normal-speed entry, and enforce exact budget, device-progress, and overflow contracts.**

## Performance

- **Duration:** 1h 52m 29s from the first task commit to the last task commit; pre-commit setup time was not captured.
- **First task commit:** 2026-10-13T19:27:44Z
- **Last task commit:** 2026-10-13T21:20:13Z
- **Tasks:** 3
- **Files modified:** 5 implementation and test files, plus this summary and the continuation note.

## Accomplishments

- A timer IRQ raised during a speed-switch stall now wakes at the next persisted CPU M-cycle boundary. IME-on guests dispatch naturally, IME-off guests resume after STOP, EI;STOP retires EI first, and split host budgets preserve the same wake time.
- CGB entries into normal speed schedule a four-half-dot `GBB_STALL_SWITCH_REALIGN` tail only when the master-time phase is four. Pending IF cannot shorten the tail, and phase-zero entries have no extension.
- Stall duration remains derived from `GBB_SPEED_SWITCH_STALL_T`, bounded to whole M-cycle steps and host budgets, with PPU, timer/DIV/TIMA, serial, OAM DMA, and audio devices advancing. Armed switching STOP checks worst-case time headroom before it mutates state.
- Added runtime mutants and mask-zero controls for wake timing, realignment, stall duration, budget bounds, device progress, STOP reasons, and headroom. The M31 signed offset seam is wired at zero without re-pinning the provisional duration.

## Task Commits

| Task | Commit | Change |
| --- | --- | --- |
| 1 | `bf0ded3` | Wake CGB speed stalls on timer IRQ; tracer and M13/M16 mutants |
| 2 RED | `09b5aa3` | Add failing wake-ordering and realignment tests |
| 2 GREEN | `231c07a` | Implement wake ordering, EI retirement, and realignment |
| 3 RED | `15234f0` | Add failing stall-duration, budget, device, and headroom tests |
| 3 GREEN | `07d00cf` | Implement headroom validation and stall mutants/seam |

The execution metadata commit is separate from the five measured task commits.

## Files Created and Modified

- `src/core/gabbaboy.c` - M-cycle wake sampling, the CGB realignment stall, and pre-mutation headroom validation.
- `tests/test_cgb_speed_internal.c` - Timer guests and the wake, realignment, duration, budget, device, and headroom cases.
- `cmake/P12Mutants.cmake` - Runtime-mask variants for plan mutants M6, M9, M21, M22, M28, and M31 alongside prior wake/realignment mutants.
- `tests/CMakeLists.txt` - Timed base tests, mutant pairs, controls, and the M31 zero-offset check.
- `tests/expected-tests.txt` - Complete test inventory entries for the plan.
- `.planning/phases/GB-12-cgb-double-speed/continue.md` - Phase handoff stage, evidence, and next route.

## Decisions Made

- Keep the stall wake sample inside the persisted stall loop, before each M-cycle step, so budget partitioning cannot alter guest-visible timing.
- Leave the provisional stall constant unchanged; plan 12-09 owns its re-measurement.
- Keep the M31 offset signed and mask-gated with a default value of zero, then prove that zero does not alter the stall-length case.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected the EI;STOP test fixture to arm KEY1.**
- **Found during:** Task 2 GREEN verification.
- **Issue:** The guest reached STOP with KEY1 unarmed, so it could not exercise the planned speed-switch stall.
- **Fix:** Set KEY1 armed before retiring EI;STOP.
- **Files modified:** `tests/test_cgb_speed_internal.c`
- **Verification:** The EI;STOP case and M34 mutant/control pair passed.
- **Committed in:** `231c07a`.

**2. [Rule 1 - Bug] Removed duplicate GATE-74 ownership from the realignment helper.**
- **Found during:** Task 3 full regression verification.
- **Issue:** GATE-74 already belongs to `execute`; assigning the same gate to the helper made the model-gate scanner reject the source.
- **Fix:** Classified the helper as a BOTH-model no-op outside CGB mode while retaining explicit CGB and execution-mode guards.
- **Files modified:** `src/core/gabbaboy.c`
- **Verification:** `model_gates`, `model_gates_real_deleted_tag`, and `model_gates_real_untagged_function` passed.
- **Committed in:** `07d00cf`.

**3. [Rule 1 - Test harness] Updated the M20 expected-failure pattern for the new wake path.**
- **Found during:** Task 3 full regression verification.
- **Issue:** With M20 forcing case 4 while IF is already pending, the new wake path resumes execution and reaches the WRAM marker assertion before the older stall-state assertion.
- **Fix:** Accept either observable assertion while keeping the mutant nonzero and its mask-zero control passing.
- **Files modified:** `tests/CMakeLists.txt`
- **Verification:** M20 mutant/control, targeted Phase 12 regression, and full CTest passed.
- **Committed in:** `07d00cf`.

**Total deviations:** 3 auto-fixed. All were required to keep the new behavior and its negative controls verifiable.

## TDD Gate Compliance

- **Task 2 RED:** `build/12-07-task2-red.json` records a fresh JUnit run where `cgb_speed_realign` failed at the expected REALIGN-kind/four-half-dot assertion. `gsd_run check tdd-red-evidence` returned `RED_EVIDENCE_OK`; semantic review confirmed the intended assertion failed after successful discovery and setup. RED commit `09b5aa3` precedes GREEN commit `231c07a`.
- **Task 2 GREEN:** The wake, EI;STOP, boundary, realignment, mutant, and control selection passed 19/19.
- **Task 3 RED:** `build/12-07-task3-red.json` records a fresh JUnit run where `cgb_speed_headroom` executed and failed because the STOP mutated state instead of returning `GBB_STOP_INVALID_STATE`. The classifier returned `RED_EVIDENCE_OK`; semantic review confirmed the missing precheck was the failure reason. RED commit `15234f0` precedes GREEN commit `07d00cf`.
- **Task 3 GREEN:** The stall length, budget, device, headroom, M31 no-op, mutant, and control selection passed 24/24.
- **Task 1 tracer gate:** After the tracer commit, the complete automated Task 1 verification reran and passed 19/19.
- No separate refactor commit was needed.

## Verification

- `cmake --preset phase1 && cmake --build --preset phase1` passed.
- The Task 2 focused wake/realignment selection passed **19/19**.
- The Task 3 focused stall/headroom and mutant-control selection passed **24/24**.
- Phase verification selection, including all `cgb_speed_*`, STOP, identity, model-gate, HALT, and interrupt-entry tests, passed **149/149**.
- Full project CTest passed **813/813** with eight workers.
- `bash tests/scripts/verify-dmg-baseline.sh` passed: inventory 313 keys, Mooneye 15, acceptance 20, bench 2, changes 0.
- Plan acceptance checks passed: exactly two M9/M22 anchors, all five required test names, M31 offset reference present, and no numeric stall-duration pin leaked into test code.
- `ctest --test-dir build -R '^summary_coverage$' --output-on-failure --no-tests=error` passed **1/1**.

## Issues Encountered

The JUnit reporter interprets a relative output path relative to CTest's build directory. The Task 3 RED run was repeated with an absolute report path, then accepted by the classifier; only the fresh validated record is used above. No implementation, test, or verification blocker remains.

## User Setup Required

None.

## Next Phase Readiness

Phase GB-12 remains in progress; plan 12-07 is complete. Plan 12-08, **“Remaining D-12 dispositions, new GATE-84 rows, GATE-62 retag, and STOP documentation,”** now depends on this plan. The next route is `/gsd-execute-phase 12`; auto-advance remains disabled.

## Self-Check: PASSED

- Summary file exists at `.planning/phases/GB-12-cgb-double-speed/12-07-SUMMARY.md`.
- Continuation note exists at `.planning/phases/GB-12-cgb-double-speed/continue.md`.
- All five task commits (`bf0ded3`, `09b5aa3`, `231c07a`, `15234f0`, `07d00cf`) are ancestors of the current plan head.

---
*Phase: 12-cgb-double-speed*
*Plan: 07*
*Completed: 2026-10-13*
