---
phase: 13-cgb-hdma
plan: "02"
subsystem: core
tags: [cgb, hdma, source-mapping, overflow, tdd]
requires:
  - phase: 13-01
    provides: Guest-visible FF51-FF55 tracer, bounded run-loop service, and reserved address-policy test names
provides:
  - Narrow CGB HDMA source windows with whole-block prevalidation and safe invalid-block status
  - Widened destination continuation through A000 with non-wrapping overflow behavior
  - Address, mapper-bank, WRAM-bank, VBK, and overflow regression matrices
affects: [13-03, cgb-profile, model-gates, CGB-07]
actuals:
  tokens: 16542
  tasks: 2
  commits: 4
commits: 4
plan_head_before: 1062a6c8222cfa97071ee05db3e821bcb3cabe89
plan_head_after: b257ac8d0400fbe325b2eb8859ad72e3a07855a3
tech-stack:
  added: []
  patterns:
    - Guest-programmed CGB HDMA policy matrices use existing core-private test seams
    - Mapper and bank selections are sampled through existing cartridge and WRAM paths
key-files:
  created: []
  modified:
    - src/core/gabbaboy.c
    - tests/test_cgb_hdma_internal.c
    - tests/test_cgb_speed_internal.c
    - tests/test_cgb_visibility.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - docs/cgb-profile.md
    - docs/model-gates.md
    - .planning/context/DECISIONS.md
    - .planning/context/LESSONS.md
key-decisions:
  - "Admit only ROM, cartridge-mapped A000-BFFF, and direct WRAM C000-DFFF sources; preserve cart_read FF behavior for absent or disabled RAM."
  - "Prevalidate all 16 bytes before block mutation and preserve completed prefixes, rejected cursors, and remaining FF55 status on failure."
  - "Retain A000 in a widened destination cursor after a legal 9FF0 block; complete a final block or stop additional work without wrap."
  - "Keep bank changes effective at each newly admitted block and retain physical CGB-E timing and arbitration as UNKNOWN."
patterns-established:
  - "Reject unsupported source windows before touching the current block or reading peripheral addresses through the CPU bus."
  - "Test legal continuation and overflow separately so FF55 completion and remaining-work status cannot alias."
requirements-completed: []
coverage:
  - id: CGB-07-STATE
    description: Guest-visible transfer state, initial kicks, genuine HBlank triggers, and bounded byte cadence remain covered.
    requirement: CGB-07
    human_judgment: false
    verification:
      - kind: integration
        ref: ctest:cgb_hdma_state_matrix,cgb_hdma_trigger_matrix,cgb_hdma_timing_policy
        status: pass
      - kind: integration
        ref: ctest:cgb_hdma_state_matrix_controls,cgb_hdma_trigger_matrix_controls,cgb_hdma_timing_policy_controls
        status: pass
      - kind: integration
        ref: ctest:cgb_visibility_deferred_stop,cgb_visibility_deferred_latch_interrupt,cgb_visibility_matrix_cgb,cgb_visibility_cross_column_control
        status: pass
  - id: CGB-07-MAP
    description: ROM, cartridge RAM, and WRAM endpoints and between-block bank changes use mapped storage paths; invalid windows leave the rejected block unchanged.
    requirement: CGB-07
    human_judgment: false
    verification:
      - kind: integration
        ref: ctest:cgb_hdma_address_matrix
        status: pass
      - kind: integration
        ref: ctest:cgb_hdma_address_matrix_controls
        status: pass
      - kind: integration
        ref: ctest:cgb_speed_xfail_hdma_fails_closed,cgb_speed_xfail_hdma_fails_closed_negative
        status: pass
  - id: CGB-07-OVERFLOW
    description: Destination 9FF0 completion, A000 continuation rejection, restart, and explicit reprogramming preserve FF55 status without wrapping.
    requirement: CGB-07
    human_judgment: false
    verification:
      - kind: integration
        ref: ctest:cgb_hdma_overflow_policy
        status: pass
      - kind: integration
        ref: ctest:cgb_hdma_overflow_policy_controls
        status: pass
  - id: CGB-07-POLICY-DOCS
    description: Model/profile claims, D-06 provenance, and partial-execution memory contract match tested behavior and preserve the frozen DMG baseline.
    requirement: CGB-07
    human_judgment: false
    verification:
      - kind: other
        ref: ctest:model_gates
        status: pass
      - kind: other
        ref: bash tests/scripts/verify-dmg-baseline.sh
        status: pass
      - kind: other
        ref: python3 -I phase13-policies bounded-section contract and per-field deletion controls
        status: pass
metrics:
  duration: 24min
  completed: 2026-10-14
status: complete
---

# Phase 13 Plan 02: Complete bounded transfer, restart and address policies Summary

**CGB HDMA now uses a prevalidated ROM/cartridge/WRAM source map and retains `$A000` overflow state without cursor wrap.**

## Performance

- **Duration:** 24 min
- **Started:** 2026-10-14T19:12:38Z
- **Completed:** 2026-10-14T19:36:03Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Restricted block sources to ROM `$0000-$7FFF`, cartridge mapping `$A000-$BFFF`, and direct WRAM `$C000-$DFFF`. Whole-block prevalidation rejects echo, VRAM, OAM, FEA0-FEFF, I/O, and HRAM before the block can mutate; absent or disabled cartridge RAM reaches `cart_read` and supplies `$FF`.
- Widened the destination cursor so `$9FF0` can complete at `$A000` without wrapping. Further blocks stop with the rejected cursor, remaining-count FF55 status, and prior valid prefix preserved; restart requires destination reprogramming.
- Added between-block MBC ROM, cartridge RAM, WRAM, and VBK bank-change checks, and recorded the qualified source/overflow policies with D-06 provenance in the model and profile documentation.
- Preserved the Phase 12 post-switch FF55 programming/readback pin and its FF54 negative twin. It verifies guest programming after the speed pause, not a transfer armed across that pause.

## Task Commits

1. **Task 1: Tracer: exact start, kick, cancel and restart through CPU execution** — `9c9f3ef` (test), `736d785` (feat).
2. **Task 2: Expand mapped sources and overflow without partial invalid blocks** — `9595d43` (test), `b257ac8` (feat).

3. **Task 2: Post-plan visibility fixture repair (outside the original four-commit task window)** — `a6b115b`.

## Files Created/Modified

- `src/core/gabbaboy.c` — narrow HDMA source validation and widened destination continuation.
- `tests/test_cgb_hdma_internal.c` — guest-driven state, address, bank-switch, invalid-window, and overflow matrices.
- `tests/test_cgb_speed_internal.c` — keep the post-switch FF55 readback active after the selected one-shot initial kick.
- `tests/test_cgb_visibility.c` — enter visible mode 2 before arming the pre-existing HBlank visibility case.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — reserved and registered exact address and overflow test names and controls.
- `docs/cgb-profile.md`, `docs/model-gates.md` — qualified source, cursor, status, and evidence policy.
- `.planning/context/DECISIONS.md` — bounded Phase 13 policy evidence with execution stage and source provenance.

## Decisions Made

- Use mapper and WRAM helpers for source reads, preserving `$FF` for absent or disabled cartridge RAM.
- Validate the full block before any write and retain the remaining count at the rejected block.
- Keep `$A000` representable and reject continuation before any wrapped destination write.
- Keep mapper and destination-bank changes effective at the next block admission. These are software policy choices; physical CGB-E behavior remains UNKNOWN.
- Keep CGB-07 open until the remaining Phase 13 plans finish their HALT, competing-stall, and corpus coverage.

## TDD Gate Compliance

- **Task 1: RED:** `cgb_hdma_state_matrix` reached its guest-visible initial-kick assertion and failed before implementation. `gsd-tools check tdd-red-evidence` returned `RED_EVIDENCE_OK` for the target JUnit report.
- **Task 1: GREEN:** `736d785` implemented the state/trigger policy. The tracer feedback gate reran the required verification and negative controls successfully before Task 2 expansion.
- **Task 2: RED:** `cgb_hdma_address_matrix` failed at the absent-RAM mapping assertion, and `cgb_hdma_overflow_policy` failed at the widened-cursor assertion. Both JUnit records passed `gsd-tools check tdd-red-evidence` with `RED_EVIDENCE_OK`; named address and overflow negative controls passed.
- **Task 2: GREEN:** `b257ac8` implemented the source and overflow policies. No behavior-neutral refactor was needed; verification exposed and corrected a pre-existing out-of-range WRAM expectation and made the post-switch FF55 fixture retain one active block after its initial kick.

## Verification

- Task 1 tracer gate: 25/25 targeted CTests passed, including state, trigger, timing, visibility, and model-gate checks.
- Task 2 exact verification: CMake configure/build passed; all four required CTest names were present; the selected `cgb_hdma_*`, `cgb_speed_*`, and `model_gates*` suite passed 176/176.
- `cgb_hdma_address_matrix_controls`, `cgb_hdma_overflow_policy_controls`, and `cgb_speed_xfail_hdma_fails_closed_negative` passed their named negative-control checks.
- The Phase 13 bounded memory contract passed with each required-field deletion rejected; `tests/scripts/verify-dmg-baseline.sh` passed with zero changed baseline rows; `git diff --check` passed.
- The OpenGSD coverage classifier reports all four deliverables auto-covered with no schema errors.
- The exact phase policy remains UNKNOWN for physical CGB-E. No hardware result or armed-across-speed-pause transfer claim is made.

## Post-wave integration follow-up

The later Wave 2 full-suite run found three visibility guests that issued FF55 without first programming FF51–FF54. Prevalidation correctly rejected the zero destination; the existing stop seam reported the source cursor `$0000`, which initially obscured the rejected field. No transfer implementation change was needed.

- The deferred-stop guest now programs mapped C000 WRAM to 8000 VRAM before requesting two LCD-off HBlank blocks. The selected single initial kick leaves one block active, so the `$00` FF55 readback remains asserted.
- The interrupt-entry fixture programs that same valid map before the stack push crosses `$FF56` into FF55. The first run still proves retirement and the exact `$FF56` stop; the next run completes the neighboring transfer and resumes the vector.
- The CGB FF55 matrix supplies valid mappings and makes the second request an LCD-off two-block HBlank transfer. Its one initial kick leaves status `$00`; the compatibility twin remains `$FF`, so the cross-column negative control still discriminates the profiles.
- Fresh exact-name inventory contained 13 `cgb_visibility_*` and 18 `cgb_hdma_*` tests; all required matrix/control names were present. The combined `cgb_visibility_*`, `cgb_hdma_*`, `cgb_speed_*`, and `model_gates*` regression group passed 199/199, including the cross-column, deferred-interrupt, address, and overflow controls.

The fixture cause and prevention rule are recorded as GB-CGB-012 in `.planning/context/LESSONS.md`. The full repository suite remains assigned to the orchestrator's Wave 2 integration rerun.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected the WRAM mapping boundary test's out-of-range expected pointer**
- **Found during:** Task 2 (Expand mapped sources and overflow without partial invalid blocks)
- **Issue:** Existing `CFF0→D000` and `DFF0` assertions formed expected pointers beyond a 4 KiB WRAM bank.
- **Fix:** Compare the next D000 block from the selected bank's offset zero and use offset `$0FF0` for the DFF0 prefix.
- **Files modified:** `tests/test_cgb_hdma_internal.c`
- **Verification:** `cgb_hdma_address_matrix` and its negative control pass.
- **Committed in:** `b257ac8`.

**2. [Rule 1 - Bug] Kept the post-switch FF55 positive pin at an active readback state**
- **Found during:** Task 2 verification
- **Issue:** Its one-block request could receive the selected visible-mode-0 initial kick and complete before the guest read FF55, changing the expected active status to `$FF`.
- **Fix:** Request two blocks so the one-shot kick leaves one active block and readback `$00`; the FF54 substitution still fails the positive predicate. The test remains limited to a post-switch programming/readback assertion.
- **Files modified:** `tests/test_cgb_speed_internal.c`
- **Verification:** `cgb_speed_xfail_hdma_fails_closed` and `cgb_speed_xfail_hdma_fails_closed_negative` pass.
- **Committed in:** `b257ac8`.

**3. [Rule 1 - Bug] Preserved the existing HBlank visibility test's intended trigger**
- **Found during:** Task 1 (Tracer: exact start, kick, cancel and restart through CPU execution)
- **Issue:** The old fixture armed HDMA with LCD off, which now correctly receives a one-shot initial block before its intended visible HBlank edge.
- **Fix:** Enable LCD in mode 2 before arming, so the test isolates the genuine visible mode-3-to-0 trigger.
- **Files modified:** `tests/test_cgb_visibility.c`
- **Verification:** `cgb_hdma_visibility`, its controls, and the Task 1 tracer gate passed.
- **Committed in:** `736d785`.

**Total deviations:** 3 auto-fixed (3 Rule 1 bugs).
**Impact on plan:** Each correction keeps existing tests aligned with the selected guest-visible semantics or valid WRAM bounds. No implementation scope changed.

## Issues Encountered

The initial one-block post-switch FF55 fixture observed completion after a valid one-shot kick. Extending its count while preserving one remaining block made the intended active readback deterministic; the mirrored disposition still does not claim an armed transfer across the pause.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 13 plan 13-02 is complete and the phase remains active. Plan 13-03, **Real HALT wake and independent competing stalls**, can build on the committed address matrices and bounded policy record. CGB-07 remains pending until the remaining Phase 13 plans complete.

---
*Phase: 13-cgb-hdma*
*Completed: 2026-10-14*

## Self-Check: PASSED

The SUMMARY, lesson, and visibility fixture files exist; all four original task commits are ancestors of HEAD; the coverage checker validates all four entries and its 12 schema mutants; the post-wave regression group passed 199/199; and `git diff --check` passes.
