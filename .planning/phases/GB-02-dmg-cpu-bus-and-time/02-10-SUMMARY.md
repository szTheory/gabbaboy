---
phase: GB-02-dmg-cpu-bus-and-time
plan: 10
subsystem: cpu
tags: [dmg, sm83, ctest, timing]
requires:
  - phase: GB-01
    provides: validated ROM loading and deterministic bootless reset behavior
provides:
  - Header-checksum-selected DMG-CPU-B startup F on load and reset.
  - Timed RET, RETI, taken RET cc, and untaken RET cc stack behavior with registered regressions.
affects: [Phase GB-02 CPU verification]
actuals:
  tokens: 5320
  tasks: 2
  commits: 4
  plan_head_before: 7cbb5087316c6402212d95cff4fbe9cc76ed6acc
  plan_head_after: 3066a5665164363c849f9f045c0563c401de6f18
tech-stack:
  added: []
  patterns:
    - Reset derives profile flags from the retained validated ROM header.
    - Timed stack reads use fixed opcode-form-specific offsets.
key-files:
  created: []
  modified:
    - src/core/gabbaboy.c
    - tests/test_control.c
    - tests/test_cpu.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "DMG-CPU-B starts with F=0x80 for header checksum zero and F=0xB0 for nonzero checksum; reset reuses the loaded ROM profile."
  - "RET and RETI read stack bytes at offsets 8 and 16; taken conditional RET retains offsets 16 and 24; untaken conditional RET performs no stack read."
requirements-completed: [] # CPU-01, CPU-02, and CPU-04 remain pending independent phase re-verification.
coverage:
  - id: D1
    description: "ROM checksum selects post-boot F at load and reset, with branch behavior and failed-load atomicity asserted."
    requirement: CPU-01
    verification:
      - kind: unit
        ref: "ctest --preset phase1 -R ^(reset_(profile|header_flags)$|loader_non_destructive$)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Return instruction stack reads match fixed timed bus expectations and bounded no-progress behavior."
    requirement: CPU-02
    verification:
      - kind: unit
        ref: "ctest --preset phase1 -R ^cpu_(return_phases|call_stack|conditional_budget)$"
        status: pass
    human_judgment: false
duration: 10min
completed: 2026-10-06
status: complete
---

# Phase GB-02 Plan 02-10: Startup Flags and Return Stack Phases Summary

**DMG-CPU-B reset now follows the loaded header checksum, and return instructions place stack reads on their expected timed bus phases.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-10-06T23:19:45Z
- **Completed:** 2026-10-06T23:29:46Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- reset_state selects F=0x80 for checksum zero and F=0xB0 for nonzero checksum at ROM load and reset.
- Registered checksum-profile tests cover first-branch outcomes, reset after execution, and failed replacement atomicity.
- RET and RETI stack reads occur at offsets 8/16; taken RET Z reads at 16/24; untaken RET NZ performs no stack read.
- The return tests assert addresses, values, timestamps, event order, total instruction time, final PC/SP/flags, RETI interrupt enable, and short-budget nonmutation.

## Task Commits

1. **Task 1 RED: checksum-profile regressions** — 67ea3a9 (test(02-10): cover checksum-selected bootless flags)
2. **Task 1 GREEN: checksum-selected startup flags** — e08b160 (fix(02-10): select post-boot flags from ROM checksum)
3. **Task 2 RED: return-phase regressions** — e1ac1c0 (test(02-10): cover return stack bus phases)
4. **Task 2 GREEN: timed return reads** — 3066a56 (fix(02-10): place return stack reads on opcode phases)

## TDD Evidence

- **Task 1 RED:** reset_header_flags executed valid zero- and nonzero-checksum ROMs. The nonzero profile failed on the expected F=0xB0 assertion while the zero profile passed. The GSD JUnit classifier returned RED_EVIDENCE_OK; the failure was the intended startup-state assertion.
- **Task 1 GREEN:** reset_state reads checksum byte 0x14D from the retained validated ROM, with the empty-instance default remaining F=0x80.
- **Task 2 RED:** cpu_return_phases executed the setup and failed because unconditional RET reported a later stack-read timestamp than the fixed +8 expectation. The GSD JUnit classifier returned RED_EVIDENCE_OK; the failure was the intended timed-access assertion.
- **Task 2 GREEN:** unconditional RET and RETI use offsets 8/16, while conditional return phases remain unchanged.
- **Refactor:** None.

## Verification

- Task 1: configure/build passed; the required selection passed 3/3 (reset_profile, reset_header_flags, loader_non_destructive).
- Task 2: configure/build passed; the required selection passed 3/3 (cpu_return_phases, cpu_call_stack, cpu_conditional_budget).
- Full offline inventory ran 96 tests: 91 passed and 5 failed. Four are the previously recorded Mooneye unsupported-bus corpus failures (mooneye_required_suite and the three individual cases). bus_unsupported_stack also fails because its generated nonzero-checksum ROM now correctly starts with F=0xB0, while its RET NC fixture assumes C=0 and expects a stack read. This plan did not alter tests/test_bus.c because it is outside the authorized file list; preserve this as an explicit test-fixture follow-up. No corpus admission, PPU behavior, or requirement status was changed.

## Files Created/Modified

- src/core/gabbaboy.c — checksum-derived reset flags and opcode-form-specific RET/RETI stack phases.
- tests/test_control.c — checksum profile, observable branch, reset, and rejected replacement regressions.
- tests/test_cpu.c — return timing matrix, RETI interrupt behavior, zero-checksum generic CPU ROMs, and corrected call-stack phases.
- tests/CMakeLists.txt — registered the two new cases.
- tests/expected-tests.txt — included both new cases in the exact inventory.

## Decisions Made

- Header checksum zero selects F=0x80; any nonzero checksum selects F=0xB0 for this bootless DMG-CPU-B profile.
- Return stack offsets depend on opcode form: RET/RETI use the earlier phases, taken conditional RET keeps its extra condition cycle, and untaken conditional RET reads no stack byte.
- T-02-SC remains accepted as the shared low-severity fixture/tool-supply control; its acceptance does not qualify the Mooneye fixtures.

## Deviations from Plan

**1. [Rule 1 - Test fixture correction] Kept generic CPU cases on the zero-checksum profile.**
- **Found during:** Task 2
- **Issue:** The CPU test ROM builder produced a nonzero checksum even though existing independent condition expectations assumed F=0x80.
- **Fix:** Set the generic CPU test ROM header to a valid zero checksum; the dedicated control regression independently covers both checksum profiles. Updated existing call-stack observer timestamps to the corrected RET phases.
- **Files modified:** tests/test_cpu.c
- **Verification:** The required CPU return, call-stack, and conditional-budget selection passed.
- **Commit:** e1ac1c0 (test changes), 3066a56 (final setup-cost correction).

## Issues Encountered

- The pending-interrupt RETI test setup required 152 half-dots: LD A,d8 costs 16, the two absolute stores cost 32 each, LD SP,d16 costs 24, and CALL costs 48. The initial 112/144 expectation was corrected before the Task 2 GREEN commit.
- Full offline CTest remains at 91/96 because of the five cases above. The phase's CPU requirements remain pending independent re-verification; this summary does not claim Phase GB-02 complete.

## User Setup Required

None.

## Next Phase Readiness

Plan 02-10’s two focused deliverables are implemented and their focused regressions pass. Phase GB-02 remains in progress. Continue with the next gap-closure plan using $gsd-execute-phase 2 --gaps-only; keep Phase 3 paused until the remaining Phase 2 evidence and owner decision.

## Self-Check: PASSED

---
*Phase: GB-02-dmg-cpu-bus-and-time*
*Completed: 2026-10-06*
