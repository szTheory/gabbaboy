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
repair_commit: 0f93724
tech-stack:
  added: []
  patterns: [STOP case decision table shared by decode and execute, paired mutant and mask-zero controls]
key-files:
  created: []
  modified: [src/core/gabbaboy.c, tests/test_cgb_speed_internal.c, tests/test_cgb_visibility.c, cmake/P12Mutants.cmake, tests/CMakeLists.txt, tests/expected-tests.txt]
key-decisions:
  - "Keep armed CGB-mode STOP cases 1-4 distinct; case 3 switches without a stall while case 4 loads the stall."
  - "Keep existing DMG, compatibility and unarmed STOP behavior, including held-button STOP, unchanged."
patterns-established:
  - "Every introduced STOP behavior mutant has a named case and a mask-zero control."
requirements-completed: [CGB-06]
coverage:
  - id: GB-12-06-STOP
    description: "Armed STOP decision cases, exact byte lengths and effects, public-input held-button wake, and a guest-generated timer IRQ with natural IME dispatch"
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_speed_stop_cases"
        status: pass
      - kind: integration
        ref: "cgb_speed_stop_guest_timer_irq"
        status: pass
      - kind: integration
        ref: "cgb_speed_mutant_m20_guest_timer_pending_ignored and cgb_speed_mutant_m20_guest_timer_pending_ignored_control"
        status: pass
      - kind: unit
        ref: "cgb_speed_mutant_m34_stop_falls_into_rlca and cgb_speed_mutant_m34_stop_falls_into_rlca_control"
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
- Added mutants M8, M10, M19, M20, M27, M29, M30, M32 and M33 with mask-zero controls, plus the FF04 wrong-byte negative. The 12-06 repair added M34 and its mask-zero control for the STOP/RLCA fallthrough.

## Task Commits

1. **Task 1: pending-IRQ STOP switch case** - `17ebb29` (feat)
2. **Task 2 RED: STOP contract evidence and test registrations** - `5e0fdfa` (test)
3. **Task 2 GREEN: STOP and KEY1 contracts** - `cd7cc41` (feat)
4. **Gap repair: STOP dispatch boundary and real timer guest** - `0f93724` (fix)

Plan commit count and head range are measured in frontmatter from the persisted plan ledger. The execution metadata commit is separate.

## Gap Closure

The initial 12-06 execution left the pending-IRQ tracer seeded by the host and called `enter_interrupt`/`execute` directly. The repair replaces that helper-only outcome with `cgb_speed_stop_guest_timer_irq`: an inline guest writes IE/IF, TIMA/TMA/TAC, waits for timer IF bit 2, disables the timer, arms KEY1, and executes STOP. With IME off, the next byte executes as `INC B`; with `EI` immediately before STOP, the run loop enters the timer handler naturally and then returns to `INC B`. Neither variant receives a host-injected IRQ or direct interrupt-helper call.

The repair also found a missing `break` after the nested STOP case switch. Case 3 advanced PC a second time and rotated A as RLCA; the prior `PC >= $0102` assertion accepted this. Exact PC/A/flags assertions failed before the core fix and pass afterward; M34 removes the break and fails those assertions, while its mask-zero control passes. Held cases now queue public button events and check exact PC/A/flags and DIV effects. The older `cgb_stop_armed_cgb` expectation that its marker was absent encoded the same fallthrough bug; it now requires the marker that the test comment and case-4 contract describe.

**Remaining 12-06 tracer gap:** none.

## TDD Evidence

- **RED:** `ctest --test-dir build -R ^cgb_speed_stop_cases$ --output-on-failure --output-junit build/tdd-red-12-06-task2.xml` failed at the intended case-1 held STOP assertion; the named test executed and reported the behavioral mismatch. The persisted record is `build/tdd-red-12-06-task2.json`; `gsd check tdd-red-evidence` returned `RED_EVIDENCE_OK`, and the semantic assessment is recorded there.
- **GREEN:** the committed implementation and expanded cases passed the focused suite, including each mutation and its mask-zero control.
- **REFACTOR:** no separate cleanup commit was needed.
- **Repair RED/GREEN:** after strengthening `cgb_speed_stop_cases` to require PC `$0101` and unchanged A/flags at case-3 retirement, the unmodified core failed at that assertion. Adding the outer `break` made it pass; automated M34 and its control retain the negative and positive outcomes.

## Verification

- `cmake --preset phase1 && cmake --build --preset phase1` passed.
- Focused CTest regression: **52/52 passed**, including the nine named mutants, paired controls, STOP/DMG identity checks and integration regressions.
- `bash tests/scripts/verify-dmg-baseline.sh` passed: inventory 313 keys, Mooneye 15, acceptance 20, bench 2, changes 0.
- The required summary coverage gate is recorded below after execution.
- **12-06 repair:** rebuilt the core and white-box test; focused STOP, CGB speed, identity, model-gate, baseline and summary-coverage selection passed **103/103**. The DMG frozen baseline again passed with 313 inventory keys and zero changed rows. This includes guest-driven pending timer IRQ, M19/M20/M27/M34 mutant and mask-zero controls, `cgb_stop_armed_cgb`, the visibility tracer, and unchanged pre-phase CGB identity pins.
- After the guest-specific M20 negative and mask-zero control were registered, the rebuilt complete CTest inventory passed **772/772** with eight workers.

## Issues Encountered

The original timer-driven guest experiment failed its marker assertion and was removed during initial execution. The repaired guest now passes with timer-generated IF and ordinary run-loop dispatch, and is registered as an independent CTest.

## Self-Check: PASSED

- Summary file exists and `summary_coverage` passed 1/1.
- Task commits `17ebb29`, `5e0fdfa` and `cd7cc41` are ancestors of the current plan head.

## Next Plan Readiness

Plan 12-07 remains next and can use the established case-3/case-4 switch state. Stop after Phase GB-12; do not advance automatically.

---
*Phase: 12-cgb-double-speed*
*Plan: 06*
*Completed: 2026-10-13*
