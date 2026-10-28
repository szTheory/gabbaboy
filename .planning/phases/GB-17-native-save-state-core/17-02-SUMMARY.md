---
phase: GB-17-native-save-state-core
plan: "02"
subsystem: state-persistence
tags: [save-state, SHA-256, canonical-serialization, CTest, immutable-revision]
requires:
  - phase: GB-17-native-save-state-core/17-01
    provides:
      - Versioned state codec, 198-field descriptor ledger, cached ROM identity, and installed tracer
provides:
  - SHA-256 identity and end-to-end save/load continuation across 15 mapper/profile/mode categories
  - Read-only state-field validation, non-failing application, and exact canonical resave checks
  - Automated 198-field documentation census and four semantic mutation controls
affects: [GB-17-native-save-state-core/17-03, native-integration]
actuals:
  tokens: 30519.25
  tasks: 2
  commits: 5
commits: 5
plan_head_before: b84fa0c9ffef0d13fa172af54c645604a6d45227
plan_head_after: 7fb9587fed2edca14db3dbb4c66a6ff87fadffb5
tech-stack:
  added: []
  patterns:
    - One typed descriptor walk drives state sizing, encoding, validation, application, and field census.
    - Caller bytes are fully validated before a non-failing apply pass.
    - Immutable-revision checkers materialize source with git show and exercise negatives in disposable copies.
key-files:
  created:
    - tests/test_state_codec.c
    - tests/scripts/verify-state-mutants.py
  modified:
    - src/core/gabbaboy.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - docs/state-format.md
    - tests/scripts/verify-state-contract.py
key-decisions:
  - "Keep one state descriptor ledger as the source for field order, validation, application, and census."
  - "Retain accepted lazy RTC and audio representation exactly; invalid state is rejected before the destination is changed."
  - "Treat ROM SHA-256 as cached immutable identity and test it independently from the state CRC."
requirements-completed: [STATE-01, STATE-02, STATE-03, STATE-05]
coverage:
  - id: D1
    description: "Strong cached ROM identity refuses same-title, same-size content changes and keeps failed replacement transactional; mapper/profile/mode state loads continue deterministically."
    requirement: STATE-01
    human_judgment: false
    verification:
      - kind: e2e
        ref: "state_identity and state_codec_matrix at immutable revision 7fb9587fed2edca14db3dbb4c66a6ff87fadffb5; SHA-256 empty/abc/multi-block vectors, generated CRC32 collision pair, hash-count controls, and all 15 mapper/profile/mode categories."
        status: pass
  - id: D2
    description: "Accepted states resave byte-identically across canonical queue, audio, palette, mapper, and in-flight device boundaries, and keep the fixed state size."
    requirement: STATE-02
    human_judgment: false
    verification:
      - kind: e2e
        ref: "state_canonical, state_codec_matrix, state_audio_bound, and state_size_bound at immutable revision 7fb9587fed2edca14db3dbb4c66a6ff87fadffb5."
        status: pass
  - id: D3
    description: "CRC-recomputed semantic-invalid state values are rejected without mutating the destination; field relationships and hardware-domain bounds are checked before apply."
    requirement: STATE-03
    human_judgment: false
    verification:
      - kind: unit
        ref: "state_semantic_bounds and state_override_isolation at immutable revision 7fb9587fed2edca14db3dbb4c66a6ff87fadffb5."
        status: pass
      - kind: integration
        ref: "verify-state-mutants.py --rev 7fb9587fed2edca14db3dbb4c66a6ff87fadffb5 killed normalization-on-load, skipped-cross-field-check, big-endian wire encoding, and test-override-leakage mutants at their named semantic guards."
        status: pass
  - id: D4
    description: "All 198 serialized fields are independently censused against the format ledger, with omitted-row and width mutation controls."
    requirement: STATE-05
    human_judgment: false
    verification:
      - kind: integration
        ref: "state_field_census and state_field_census_controls at immutable revision 7fb9587fed2edca14db3dbb4c66a6ff87fadffb5; direct immutable census reports 198 rows."
        status: pass
  - id: D5
    description: "The documented wire bounds and state test registration are checked alongside the production tracer and immutable revision gates."
    requirement: STATE-05
    human_judgment: false
    verification:
      - kind: integration
        ref: "state_format_contract, state_inventory, state_inventory_controls, state_globals, state_globals_controls, state_revision_controls, state_precodec_gate, and state_tracer at immutable revision 7fb9587fed2edca14db3dbb4c66a6ff87fadffb5."
        status: pass
duration: 26min
completed: 2026-10-26
status: complete
---

# Phase 17 Plan 02: Native Save State Identity and Canonical Validation Summary

**State snapshots now bind complete ROM identity, preserve exact continuation across all admitted mapper and hardware modes, and reject semantically invalid bytes before mutating an instance.**

## Performance

- **Duration:** 26 min
- **Started:** 2026-10-26T21:07:48Z
- **Completed:** 2026-10-26T21:33:12Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Extended the real installed state tracer through SHA-256 vectors, an original equal-CRC32/different-SHA ROM pair, hash-count controls, transactional failed replacement, and 15 mapper/profile/mode categories.
- Added canonical exact-resave and future-continuation coverage for queue sizes 0, 1, and 64; mapper and audio boundaries; all explicit wire widths; and in-flight CPU/device states.
- Closed semantic validation for device, CPU, timer, serial, event, palette, pixel, and mapper fields. State application now follows complete validation through a non-failing pass.
- Added an immutable 198-field census and mutation harness; registered each new control in CTest and the exact test inventory.

## Verification

- Configure and full phase1 build passed at immutable source revision 7fb9587fed2edca14db3dbb4c66a6ff87fadffb5.
- The targeted state acceptance selection passed 18/18 CTests, including identity, codec matrix, canonical roundtrip, semantic bounds, override isolation, census and its negative controls, mutation controls, format contract, precodec gate, and tracer (10.33 seconds).
- The immutable mutation harness passed with 4/4 requested mutants killed and 3/3 baseline cases passing. The endian mutant changes wire emission to big-endian and is killed by the independent ppu_dot little-endian byte sentinel.
- The direct immutable field census matched all 198 rows; the census negative controls passed.
- git diff --check passed.
- The complete project CTest suite is left for the phase orchestrator's post-wave verification.

## Task Commits

1. **Task 1 RED: Extend the installed tracer to all identities and hardware modes** — 15231de.
2. **Task 1 GREEN: Extend state identity and field census** — 050d0e7.
3. **Task 2 RED: Add canonical and semantic state boundary tests** — c8167ef.
4. **Task 2 GREEN: Close field validation and canonical resave** — 8b46270.
5. **Checker correction: Verify census and endian mutants** — 7fb9587.

The plan ledger measured five commits from b84fa0c9ffef0d13fa172af54c645604a6d45227 through 7fb9587fed2edca14db3dbb4c66a6ff87fadffb5.

## TDD Gate Compliance

- Task 1 RED evidence for state_identity and state_codec_matrix returned RED_EVIDENCE_OK. The first exposed acceptance of an inconsistent ROM-only mapper field; the second exposed invalid post-boot CGB register domains. state_size_bound passed as the unrelated control in both runs.
- Task 2 RED evidence returned RED_EVIDENCE_OK: CRC-recomputed hdma.source_low=1 was accepted and changed the destination, while state_size_bound passed.
- GREEN: state_identity, state_codec_matrix, state_semantic_bounds and the remaining 14 selected state checks pass at the final immutable revision.
- The post-GREEN mutation controls demonstrate intended failures: accepted envelope bytes changed by normalization-on-load; div[0]=1 changed the semantic relation while state accepted it; big-endian ppu_dot bytes violated the 23 01 sentinel; and test-override leakage failed the 198-field census.

## Files Created/Modified

- tests/test_state_codec.c — identity, mapper/mode, canonical resave, semantic-invalid, and test-override isolation tests.
- src/core/gabbaboy.c — tighter HDMA semantic constraints and non-failing state application.
- tests/CMakeLists.txt and tests/expected-tests.txt — registered CTests, limits, and exact test inventory entries.
- docs/state-format.md — documented accepted HDMA register bounds.
- tests/scripts/verify-state-contract.py — immutable field-census parsing and omitted-row/width controls.
- tests/scripts/verify-state-mutants.py — disposable immutable-source harness for the four required semantic mutants.

## Decisions Made

- Kept canonical field order, encoding, semantic validation, apply, and census coupled through the typed descriptor ledger.
- Preserved accepted lazy RTC/audio representations and validated every caller byte before applying state.
- Kept the ROM identity digest independent from the corruption-detection CRC and performed ROM hashing only at successful replacement.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical verification] Added an immutable semantic mutation harness**

- **Found during:** Task 2 test design
- **Issue:** The plan requires four specific implementation mutants to fail their intended semantic cases, but its declared checker file list had no executable mutation control for them.
- **Fix:** Added verify-state-mutants.py, which materializes immutable source into disposable copies, builds each mutant, and requires the named semantic diagnostic plus passing baseline cases. Registered its control in CTest in the same task.
- **Files modified:** tests/scripts/verify-state-mutants.py, tests/CMakeLists.txt, tests/expected-tests.txt
- **Verification:** state_codec_mutant_controls passes; all four named mutants are killed and all three baseline cases pass at the immutable plan head.
- **Committed in:** 8b46270 and 7fb9587.

**2. [Rule 1 - Test harness bug] Corrected field census output parsing**

- **Found during:** Task 2 post-GREEN validation
- **Issue:** The checker assumed Markdown pipe-table rows, but the private census executable emits plain pipe-delimited rows.
- **Fix:** Accepted the executable's row format in the immutable census parser; kept Markdown parsing and its controls intact.
- **Files modified:** tests/scripts/verify-state-contract.py
- **Verification:** state_field_census and state_field_census_controls pass; direct census matched 198 rows.
- **Committed in:** 7fb9587.

**3. [Rule 1 - Mutation harness bug] Made the endian mutant reach the wire-endian assertion**

- **Found during:** Task 2 post-GREEN mutation validation
- **Issue:** The initial mutant altered the shared integer writer, so an earlier semantic check rejected the test before the endian sentinel ran.
- **Fix:** Restricted the mutation to encoded wire emission and reported the sentinel diagnostic as the mutation evidence.
- **Files modified:** tests/scripts/verify-state-mutants.py
- **Verification:** The native-endian-encoding mutant is killed by ppu_dot expecting bytes 23 01; the other three requested mutants and all baseline cases also pass.
- **Committed in:** 7fb9587.

**Total deviations:** 1 Rule 2 addition and 2 Rule 1 test-harness fixes.
**Impact on plan:** The added checker implements the plan's explicit mutation requirement; the fixes made census and semantic mutation evidence exercise their intended contracts. No production behavior scope changed.

## Issues Encountered

The first post-GREEN 18-test run exposed the two checker issues above. After correction, the final 18-test run passed 18/18 and the complete phase1 build passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 17-02 is complete and supplies the identity, mapper/mode, canonical-resave, semantic-validation, and census evidence required by the next Phase 17 plan. Phase 17 remains in progress; no phase or milestone advance was performed.

---
*Phase: GB-17-native-save-state-core*
*Completed: 2026-10-26*

## Self-Check: PASSED

- SUMMARY file created at the required phase path.
- All five plan commits are ancestors of the implementation revision 7fb9587fed2edca14db3dbb4c66a6ff87fadffb5.
- The SUMMARY commit count and before/after revision fields match the persisted plan ledger.
