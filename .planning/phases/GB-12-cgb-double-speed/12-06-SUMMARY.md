---
phase: 12-cgb-double-speed
plan: 06
subsystem: cpu
tags: [cgb, stop, double-speed, interrupts, mutants]
requires:
  - phase: 12-cgb-double-speed
    provides: speed-switch primitive and stall tracer from plans 12-01 through 12-05
provides:
  - Five-way armed CGB STOP decision table and case-specific byte lengths
  - Immediate pending-IRQ switch path, 2 M switch cost, and KEY1/KEY0 contracts
  - STOP fetch-preflight, operand, FF04, DMG and unarmed regression controls
affects: [12-cgb-double-speed]
actuals:
  tokens: 5941
  tasks: 2
  commits: 3
commits: 3
plan_head_before: fed97e8dbf73b20b1193c3cc9bf9005bc817282d
plan_head_after: cd7cc41dd3cd9ca8f5aa68ed02105d5e924b7922
tech-stack:
  added: []
  patterns: [STOP case decision table shared by decode and execute, paired mutant and mask-zero controls]
key-files:
  created: []
  modified: [src/core/gabbaboy.c, tests/test_cgb_speed_internal.c, cmake/P12Mutants.cmake, tests/CMakeLists.txt, tests/expected-tests.txt]
key-decisions:
  - "Keep armed CGB-mode STOP cases 1-4 distinct; case 3 switches without a stall while case 4 loads the stall."
  - "Keep existing DMG, compatibility and unarmed STOP behavior, including held-button STOP, unchanged."
patterns-established:
  - "Every introduced STOP behavior mutant has a named case and a mask-zero control."
requirements-completed: [CGB-06]
coverage:
  - id: GB-12-06-STOP
    description: "Armed STOP decision cases, lengths, immediate pending-IRQ switch and held-button wake behavior"
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_speed_stop_cases"
        status: pass
      - kind: unit
        ref: "cgb_speed_mutant_m20_pending_ignored and cgb_speed_mutant_m20_pending_ignored_control"
        status: pass
      - kind: unit
        ref: "cgb_speed_mutant_m19_held_predicate_ignored and cgb_speed_mutant_m19_held_predicate_ignored_control"
        status: pass
  - id: GB-12-06-FETCH
    description: "STOP operand independence and opcode fetch from FF04 with a wrong-byte negative"
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_speed_stop_operand"
        status: pass
      - kind: unit
        ref: "cgb_speed_stop_prefetch_ff04 and cgb_speed_stop_prefetch_ff04_negative"
        status: pass
      - kind: unit
        ref: "cgb_speed_mutant_m33_operand_changes_switch and cgb_speed_mutant_m33_operand_changes_switch_control"
        status: pass
  - id: GB-12-06-SPEED
    description: "Switch cost, KEY1/KEY0 semantics and DMG/unarmed identity remain enforced"
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_speed_stop_cost, cgb_speed_key1_readback, cgb_speed_key0_no_switch"
        status: pass
      - kind: unit
        ref: "cgb_speed_dmg_unarmed_unchanged"
        status: pass
      - kind: unit
        ref: "cgb_speed_mutant_m8_speed_gate_removed, cgb_speed_mutant_m10_key1_arm_not_cleared, cgb_speed_mutant_m27_divider_reset_omitted, cgb_speed_mutant_m29_switch_cost_one_m, cgb_speed_mutant_m30_dmg_stop_apu_edge, cgb_speed_mutant_m32_key0_toggles_speed and cgb_speed_mutant_m33_operand_changes_switch; each paired _control"
        status: pass
      - kind: integration
        ref: "cgb_speed_tracer_switch, cgb_speed_identity_pin, cgb_speed_identity_pin_flipped, cgb_stop_*, cgb_dmg_identity_*, banking_tracer_digest_unchanged, cgb_runner_profile_dmg_identity_*, model_gates*"
        status: pass
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh"
        status: pass
duration: 41m28s
completed: 2026-10-13
status: complete
---

# Phase 12 Plan 06: STOP Decision Cases and KEY1 Contract Summary

**CGB STOP now applies a five-case decision table with case-3 no-stall switching, preserved DMG/unarmed behavior, and automated mutant controls.**

## Performance

- **Duration:** 41m28s
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added the held/no-pending, held/pending, not-held/pending, and neither-pending armed CGB STOP paths; fetch sizing and switch cost follow the selected case.
- Added contract tests for KEY1 readback, ignored KEY0 writes, FF04 instruction fetch, operand independence, and DMG/unarmed identity.
- Added mutants M8, M10, M19, M20, M27, M29, M30, M32 and M33 with mask-zero controls, plus the FF04 wrong-byte negative.

## Task Commits

1. **Task 1: pending-IRQ STOP switch case** - `17ebb29` (feat)
2. **Task 2 RED: STOP contract evidence and test registrations** - `5e0fdfa` (test)
3. **Task 2 GREEN: STOP and KEY1 contracts** - `cd7cc41` (feat)

Plan commit count and head range are measured in frontmatter from the persisted plan ledger. The execution metadata commit is separate.

## Deviations from Plan

The pending-IRQ tracer seeds IE/IF directly in the white-box fixture and invokes the interrupt-dispatch helpers for its IME-enabled variant. It does not yet have the plan's guest program configure TAC/TIMA, wait for IF bit 2, and naturally dispatch through the run loop. An attempted timer-driven guest edit destabilized the existing tracer oracle and was discarded; the committed tests and production changes remain green. This narrower tracer evidence is an outstanding plan gap for follow-up, not evidence of an end-to-end timer guest.

**Total deviations:** 1 documented limitation.
**Impact on plan:** STOP state-table behavior and both pending-IRQ outcomes are checked, while guest-generated timer sequencing and run-loop interrupt dispatch remain unproven by this plan's tracer.

## TDD Evidence

- **RED:** `ctest --test-dir build -R ^cgb_speed_stop_cases$ --output-on-failure --output-junit build/tdd-red-12-06-task2.xml` failed at the intended case-1 held STOP assertion; the named test executed and reported the behavioral mismatch. The persisted record is `build/tdd-red-12-06-task2.json`; `gsd check tdd-red-evidence` returned `RED_EVIDENCE_OK`, and the semantic assessment is recorded there.
- **GREEN:** the committed implementation and expanded cases passed the focused suite, including each mutation and its mask-zero control.
- **REFACTOR:** no separate cleanup commit was needed.

## Verification

- `cmake --preset phase1 && cmake --build --preset phase1` passed.
- Focused CTest regression: **52/52 passed**, including the nine named mutants, paired controls, STOP/DMG identity checks and integration regressions.
- `bash tests/scripts/verify-dmg-baseline.sh` passed: inventory 313 keys, Mooneye 15, acceptance 20, bench 2, changes 0.
- The required summary coverage gate is recorded below after execution.

## Issues Encountered

The timer-driven guest experiment failed its marker state assertion; its uncommitted edit was removed and the pre-existing white-box tracer restored. No experimental code remains.

## Self-Check: PASSED

- Summary file exists and `summary_coverage` passed 1/1.
- Task commits `17ebb29`, `5e0fdfa` and `cd7cc41` are ancestors of the current plan head.

## Next Plan Readiness

Plan 12-07 remains next and can use the established case-3/case-4 switch state. The direct timer-wait/dispatch guest trace described above remains unverified. Stop after Phase GB-12; do not advance automatically.

---
*Phase: 12-cgb-double-speed*
*Plan: 06*
*Completed: 2026-10-13*
