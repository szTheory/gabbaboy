---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 19
subsystem: docs-and-decisions
tags: [adr, half-dot, doc-contract, static-assert, integration-guide, support-ledger, d-20, d-21, d-28]
requires:
  - phase: 10-cgb-profile-banking-and-register-visibility
    provides: "10-17 benchmark numbers; 10-18 coverage; CGB profile, probe/info API"
provides:
  - "Named half-dot timeline macros and a 'half-dot timeline:' _Static_assert block in src/core/gabbaboy.c"
  - "DECISIONS D-070 (half-dot ADR) and D-071..D-075"
  - "docs/cgb-profile.md 'Half-dot timeline (D-070)' section tied to the macros by cgb_adr_half_dot_contract"
  - "docs/native-integration.md 'CGB-CPU-E profile' section checked by cgb_native_guide_contract"
  - "docs/support/unreleased.md 'CGB-CPU-E profile (Phase 10)' ledger section"
affects: [20]
actuals:
  tokens: 12000
  tasks: 3
  commits: 3
key-files:
  created: []
  modified:
    - src/core/gabbaboy.c
    - include/gabbaboy/gabbaboy.h
    - docs/cgb-profile.md
    - docs/native-integration.md
    - docs/support/unreleased.md
    - .planning/context/DECISIONS.md
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "D-070: one uint64_t half-dot master clock for normal and double speed; only CPU-side devices scale; RTC never reads double_speed"
  - "D-071..D-075 record IE bits 5-7, ch1 enabled-but-silent policy, atomic deferred reads vs latched deferred writes, GATE-00, and FEA0-FEFF plus cgb-separate-buses"
requirements-completed: []
status: complete
commits: 3
plan_head_before: 69b20d1e164fc508ca13f08ce7a8883a46446104
plan_head_after: ffa090a8cd20ee0568940ee9fc1bdaf1b054ac88
duration: 25 min
completed: 2026-10-12
coverage:
  - id: D1
    description: "Half-dot timeline numbers are compile-time facts in the core; DMG output byte-identical"
    human_judgment: false
    verification:
      - {kind: ctest, ref: "cgb_adr_half_dot_static_assert_mutant", status: pass}
      - {kind: command, ref: "bash tests/scripts/verify-dmg-baseline.sh (baseline status=pass)", status: pass}
  - id: D2
    description: "ADR doc section names only declared macros and keeps each rule"
    human_judgment: false
    verification:
      - {kind: ctest, ref: "cgb_adr_half_dot_contract", status: pass}
      - {kind: ctest, ref: "cgb_adr_half_dot_contract_undeclared_selftest", status: pass}
      - {kind: ctest, ref: "cgb_adr_half_dot_contract_missing_selftest", status: pass}
  - id: D3
    description: "CGB integration guide names only declared symbols and keeps the info API, PGB, frame-copy, banking and deferred-register promises"
    human_judgment: false
    verification:
      - {kind: ctest, ref: "cgb_native_guide_contract", status: pass}
      - {kind: ctest, ref: "cgb_native_guide_contract_missing_selftest", status: pass}
  - id: D4
    description: "Support ledger and decisions describe Phase 10 honestly (no colour, no double speed, no game claim; D-22 cost and macOS sanitizer limits stated)"
    human_judgment: false
    verification:
      - {kind: command, ref: "grep acceptance criteria for unreleased.md section and D-071..D-075 rows", status: pass}
---

# Phase 10 Plan 19: Half-dot ADR, CGB guide, support ledger and decisions Summary

The half-dot master timeline is recorded as D-070, its numbers are `_Static_assert` facts in the core, and the ADR text, the CGB integration guide and the support ledger are each machine-checked with a negative control.

## Accomplishments

- **Task 1 (tracer, c8c6b51).** Added `GBB_MASTER_HALF_DOTS_PER_SECOND`, `GBB_HALF_DOTS_PER_T_NORMAL` (2), `GBB_HALF_DOTS_PER_T_DOUBLE` (1), `GBB_T_PER_M`, `GBB_HALF_DOTS_PER_DOT`, `GBB_DOTS_PER_LINE`, `GBB_LINES_PER_FRAME` and eight `half-dot timeline:` static asserts; `ppu_advance_dot` now uses `GBB_DOTS_PER_LINE - 1u` and `GBB_LINES_PER_FRAME` (macro substitution only). D-070 row, the 'Half-dot timeline (D-070)' section, and `cgb_adr_half_dot_contract`. The tracer verification passed (build, ppu/video/model-gate/cgb_tables tests, DMG baseline `status=pass`) before expansion.
- **Task 2 (7b477d0).** `cgb_adr_half_dot_contract_undeclared_selftest`, `cgb_adr_half_dot_contract_missing_selftest`, and `cgb_adr_half_dot_static_assert_mutant` (configure-time core copy with `GBB_HALF_DOTS_PER_T_DOUBLE` 1 to 2, EXCLUDE_FROM_ALL; verified the compile error is the `half-dot timeline:` assert, not an unrelated failure).
- **Task 3 (ffa090a).** 'CGB-CPU-E profile' section in `docs/native-integration.md`, 'CGB-CPU-E profile (Phase 10)' in `docs/support/unreleased.md`, `gbb_peek_ram` header comment (follows the selected WRAM bank), stale `GBB_PROFILE_CGB_CPU_E` enum comment corrected, DECISIONS D-071..D-075, `cgb_native_guide_contract` and its missing-phrase selftest.
- The support ledger states the 10-17 DMG cost honestly (about +6-7% median versus Phase 7, D-22 trigger fired, advisory because the host was loaded) and the macOS sanitizer limitation from 10-18.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Stale public header comment on the profile enum**
- **Found during:** Task 3
- **Issue:** `gabbaboy.h` still said `gbb_create` does not accept `GBB_PROFILE_CGB_CPU_E`, contradicting the function's own comment and behavior.
- **Fix:** Comment now reads "creatable and probeable; no colour output yet". No signature change.
- **Files modified:** include/gabbaboy/gabbaboy.h
- **Commit:** ffa090a

**2. [Rule 3 - Blocking] Guide phrase wrapped across a line broke the selftest anchor**
- **Found during:** Task 3
- **Issue:** the configure-time selftest anchor "outputs unchanged on error" is an exact-once string match and failed configure because the guide wrapped it.
- **Fix:** reworded so the phrase sits on one line.
- **Files modified:** docs/native-integration.md
- **Commit:** ffa090a

Decision rows D-071..D-075 were authored from 10-CONTEXT.md, 10-RESEARCH.md and the shipped docs; five rows cover the six topics the plan listed (A2/OQ3 and OQ2 etc.), so numbering is D-071 to D-075.

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking). **Impact:** none on scope.

## Verification

- Full suite `ctest --preset phase1 -j4`: 537/537 passed (46 s); no timeouts on this run.
- `bash tests/scripts/verify-dmg-baseline.sh`: `baseline status=pass`, rows=0 changes.
- New tests: 6 (`cgb_adr_half_dot_contract`, `_undeclared_selftest`, `_missing_selftest`, `_static_assert_mutant`, `cgb_native_guide_contract`, `_missing_selftest`), all listed in tests/expected-tests.txt.
- Acceptance greps: 8 `half-dot timeline:` asserts (needs 6), one D-070 row, 5 D-07x rows (needs 4), both guide tests inventoried, ledger section present, header phrase present.

## Known Stubs

None.

## Threat Flags

None. No new endpoints, file access or trust boundaries.

## Self-Check: PASSED
