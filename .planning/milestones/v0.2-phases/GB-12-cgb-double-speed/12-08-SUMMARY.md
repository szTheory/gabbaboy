---
phase: 12-cgb-double-speed
plan: 08
subsystem: cpu
tags: [cgb, speed, stop, model-gates, documentation]
requires:
  - phase: 12-cgb-double-speed
    provides: "STOP decision table, speed-switch stall, and M-cycle wake behavior from plans 12-03 through 12-07"
provides:
  - "D-12 gate dispositions with no open research:12 ownership in the core or model-gate table"
  - "GATE-84 through GATE-90 declarations for the STOP decision, stall, wake, realignment, and CPU-tick scaling"
  - "Automated no-Phase-12-row and STOP-profile document contracts with negative controls"
  - "CGB profile documentation of the implemented STOP cases and provisional stall derivation"
affects: [12-cgb-double-speed/12-09, cgb-speed-verification]
actuals:
  tokens: 7358
  tasks: 3
  commits: 3
commits: 3
plan_head_before: 9d44c5f51b3ee449a3484181cddf1377aefaa0a0
plan_head_after: a378f5170cdf33cf542ecaed83eac0530884c55e
tech-stack:
  added: []
  patterns: [model-gate bijection with phase-owner rejection, documentation contracts with missing-phrase controls]
key-files:
  created: [tests/check_no_phase12_rows.cmake]
  modified: [src/core/gabbaboy.c, docs/model-gates.md, tests/CMakeLists.txt, tests/expected-tests.txt, docs/cgb-profile.md]
key-decisions:
  - "D-12 resolves shared CPU behavior and the CGB-specific APU tap, while independent STOP, timer, and serial questions remain explicitly assigned to Phase 14 or named expected failures."
  - "Keep GBB_SPEED_SWITCH_STALL_T provisional at its current value until plan 12-09 re-measures the committed core; this plan ran no AGE verdict or window check."
requirements-completed: [CGB-06]
coverage:
  - id: GB-12-08-GATES
    description: "Every Phase 12 model-gate row is resolved, reassigned with its reason, or recorded as an expected failure; the code and table remain bijective."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: other
        ref: python3 -I tests/scripts/verify-model-gates.py
        status: pass
      - kind: integration
        ref: model_gates
        status: pass
      - kind: integration
        ref: model_gates_no_phase12_rows
        status: pass
      - kind: integration
        ref: model_gates_no_phase12_rows_mutated_doc
        status: pass
  - id: GB-12-08-STOP-DOC
    description: "The CGB profile describes all four STOP cases, the stall timing derivation, D-070 clock behavior, deferred behaviors, and future state fields."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: other
        ref: cgb_speed_profile_contract
        status: pass
      - kind: other
        ref: cgb_speed_profile_contract_missing_selftest
        status: pass
      - kind: other
        ref: cgb_adr_half_dot_contract
        status: pass
      - kind: integration
        ref: cgb_native_guide_contract
        status: pass
      - kind: integration
        ref: cgb_tables_postboot
        status: pass
      - kind: integration
        ref: cgb_tables_io
        status: pass
  - id: GB-12-08-BUILD
    description: "The updated core metadata and CTest registration configure and build, and the profile contains no stale Phase 12 deferral or verification marker."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: other
        ref: cmake --build --preset phase1
        status: pass
      - kind: other
        ref: "! rg -n 'DEFERRED\\(12\\)|\\[VERIFY\\]' docs/cgb-profile.md"
        status: pass
      - kind: other
        ref: "! rg -n '\"(0x20004|131076|262152)\"' tests/CMakeLists.txt"
        status: pass
duration: "9m 25s through the task commits; metadata closeout follows"
completed: 2026-10-13
status: complete
---

# Phase 12 Plan 08: D-12 Model Gates and STOP Documentation Summary

**The speed-switch model now has a complete gate ledger, an automated no-reopen control, and a documented four-case STOP contract with a provisional stall derivation reserved for plan 12-09 to re-measure.**

## Accomplishments

- Resolved the Phase 12 gate ownership in source and `docs/model-gates.md`: GATE-30/31/53/65 are `BOTH`, GATE-56 and GATE-74 are `CGB_ONLY`, GATE-52 is the named DMA restart expected failure, and GATE-41/GATE-62 plus GATE-54/GATE-55 remain assigned to Phase 14 for their independent questions. Added GATE-84 through GATE-90 for the armed STOP decision, held-button and pending-IRQ subcases, stall branch and wake, realignment, and the CPU-tick scaling sites. The release status now describes the Phase 12 rows as resolved or reassigned.
- Updated `GBB_MG_STOP_TAG_REGEX` with the exact GATE-62 tag and added `model_gates_no_phase12_rows` plus a mutated-row control. The direct scanner reports `functions=169 gates=91 unknown=38`; it and all 12 selected `model_gates*` tests pass.
- Replaced the stale deferred STOP description with a four-case table, the two-M-cycle switch STOP cost, operand preflight behavior, persisted M-cycle stall and wake rules, and D-09 normal-speed realignment. The half-dot timeline now states the implemented DIV reset order, destination-speed stall accounting, and normal/double APU taps.
- Documented the research-prototype stall derivation and the current provisional timing values without treating them as a hardware specification or a committed-core AGE result. `GBB_SPEED_SWITCH_STALL_T` and `divider_reset` are unchanged. The next plan owns the first AGE run and committed-core window measurement.
- Added `cgb_speed_profile_contract` with a missing-phrase control. Existing post-boot evidence text now says “no hardware oracle” directly, and the OAM DMA table says “not hardware-verified”; the qualification remains explicit and its mirrored post-boot reason stays in sync with the core.

## Task Commits

| Task | Commit | Change |
| --- | --- | --- |
| 1 | `8b0a59e` | Resolve the shared STOP divider-reset gate |
| 2 | `f19b949` | Resolve CGB speed gate rows and add the no-Phase-12-row check |
| 3 | `a378f51` | Document STOP switching and add the profile contract |

## Files Created and Modified

- `src/core/gabbaboy.c` — Phase 12 gate resolutions and expected-failure subcases; the existing post-boot evidence phrase is preserved without an editorial marker.
- `docs/model-gates.md` — resolved/reassigned Phase 12 rows, new GATE-84..GATE-90 rows, dispositions, and release status.
- `tests/check_no_phase12_rows.cmake` — owner-tag rejection with a stable failure token.
- `tests/CMakeLists.txt` — exact STOP-tag anchor, mutated-row test, and the profile document contract with a negative control.
- `tests/expected-tests.txt` — the four new model-gate and documentation test names.
- `docs/cgb-profile.md` — STOP decision table, stall derivation, resolved D-070 statement, limitations, and future save-state fields.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Verification scope] Replaced legacy `[VERIFY]` annotation tokens with explicit evidence wording.**
- **Found during:** Task 3 verification.
- **Issue:** The plan's file-wide stale-marker check also matched five inherited annotations outside the replaced D-070 sentence, including the code-mirrored BCPS/OCPS reason. Removing only the D-070 sentence left that prescribed check failing.
- **Fix:** Kept the same evidence limits while using “no hardware oracle for CGB-mode index” and “not hardware-verified” wording; updated the matching source reason with its profile table cell.
- **Files modified:** `src/core/gabbaboy.c`, `docs/cgb-profile.md`.
- **Verification:** `cgb_tables_postboot`, `cgb_tables_io`, the new profile contract, its missing-phrase control, and the full focused model-gate selection passed.
- **Commit:** `a378f51`.

## Verification

- `cmake --preset phase1` and `cmake --build --preset phase1` passed.
- The final focused selection passed **24/24**, covering the model-gate scanner and mutants, no-Phase-12-row check and mutated-doc control, post-boot and I/O table mirrors, native guide and D-070 contracts, and the new STOP profile contract and missing-phrase control.
- `python3 -I tests/scripts/verify-model-gates.py` passed with **169 functions and 91 gates**. The D-070/STOP sections contain no `[VERIFY]` or `DEFERRED(12)` marker; no numeric stall phrase was pinned in `tests/CMakeLists.txt`.
- No AGE ROM was executed and no committed-core AGE verdict/window was produced; that remains the first measurement in plan 12-09. The full CTest inventory was not repeated because this plan changes model metadata, documentation, and their focused contracts; plan 12-07's immediately preceding full-suite evidence was 813/813.

## Known Stubs

None. The stall length remains intentionally provisional until the measured gate in plan 12-09.

## Next Plan Readiness

Plan 12-09, **AGE driver, dispositions, sensitivity sweep**, is next. It performs the committed-core `spsw-div` window re-measurement before any constant-derived expectations are pinned. Next command: **`/gsd-execute-phase 12`**. Phase 12 remains in progress; automatic advance stays disabled.

## Self-Check: PASSED

- Summary file exists at `.planning/phases/GB-12-cgb-double-speed/12-08-SUMMARY.md`.
- All three task commits (`8b0a59e`, `f19b949`, `a378f51`) are ancestors of the current plan head.
- `summary_coverage` passed **1/1** for this block-schema coverage section.

---
*Phase: 12-cgb-double-speed*
*Plan: 08*
*Completed: 2026-10-13*
