---
phase: 14-cgb-e-model-qualification-and-corpus
plan: "10"
subsystem: testing
tags: [cgb-e, age, ctest, corpus, model-gates]
requires:
  - phase: "14-02"
    provides: FF56/FF72–FF75 visibility and register-policy contracts
  - phase: "14-03"
    provides: timed CH3 sample-latch and guest-qualified CGB APU transition behavior
  - phase: "14-04"
    provides: APU lifecycle, split-run execution, and bounded guest-test coverage
  - phase: "14-07"
    provides: pinned SameSuite APU corpus, author expectations, and per-case software observations
  - phase: "14-09"
    provides: inherited AGE image and row-oracle inputs
provides:
  - Source-labelled normal-speed STAT expectations and exact observed AGE row dispositions
  - Executable identity and semantic contracts for all 19 admitted AGE cases
  - A tested 31-gate research14 ownership ledger mirrored in the inventory and model-gate docs
affects: [CGB-08, CGB-10, phase-14-qualification, cgb-corpus]
actuals:
  tokens: 65338
  tasks: 2
  commits: 5
plan_head_before: affaa4f28665e2e5a4c655cf67b199bf8088c37a
plan_head_after: 7721a5cefe05eaf4ce43188441ac82f8c42c61c3
tech-stack:
  added: []
  patterns:
    - Stable source-row identifiers paired with independent ROM expected bytes and exact observed signatures
    - Fixture metadata validation with hostile negative controls before bounded guest execution
key-files:
  created:
    - tests/scripts/verify-age-phase14-contract.py
    - tests/scripts/test_age_phase14_contract.py
    - tests/scripts/test_age_phase14_inherited_contract.py
    - .planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-10-red-task1.json
    - .planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-10-red-task2.json
  modified:
    - tests/test_age.c
    - tests/scripts/verify-cgb-corpus-inventory.py
    - tests/external/cgb-speed-dispositions.json
    - tests/external/cgb-corpus-inventory.json
    - docs/cgb-profile.md
    - docs/model-gates.md
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - .planning/WINDOWS.md
key-decisions:
  - Keep the inherited STAT and mode-3 observations as exact software-model failures because they do not select a precise production timing event.
  - Preserve GATE-15 and GATE-34 as UNKNOWN until an independent DMG length-retention fixture and explicit baseline revision exist.
  - Keep AGE row outcomes, full-image evaluator outcomes, guest pass/fail counts, and physical-hardware claims separate.
patterns-established:
  - AGE row contracts bind stable source labels, independent expected bytes, guest-observed bytes, masks, and signatures.
  - Research14 dispositions require applicability, source, evidence or limitation, test binding, owner, and revisit condition.
requirements-completed: [CGB-08, CGB-10]
coverage:
  - id: CGB-08-AGE-ROWS
    description: Normal-speed STAT and inherited AGE row observations retain source identities, independent expected values, and exact guest dispositions.
    requirement: CGB-08
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R '^(cgb_age_assertion_identity|age_stat_mode_cgbE|age_stat_mode_ds_cgbBCE|age_stat_mode_sprites_dmgC_cgbBCE|age_stat_mode_sprites_ds_cgbBCE|age_stat_mode_window_cgbBCE|age_stat_mode_window_ds_cgbBCE|age_spsw_mode0_cgbBCE|age_spsw_ch2_lc_delay_cgbBCE)$'"
        status: pass
  - id: CGB-08-AGE-NEGATIVE-CONTROLS
    description: Mixed LY and SCX/STAT semantics, row omission and duplication, xpass, signature drift, and hostile fixture bounds are rejected.
    requirement: CGB-08
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R '^(cgb_age_assertion_controls|cgb_phase14_inherited_contract_unit)$'"
        status: pass
  - id: CGB-10-AGE-CORPUS
    description: All 19 admitted AGE identities bind unique tests while six image cases and their pixel controls remain distinct from row outcomes.
    requirement: CGB-10
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R '^(cgb_corpus_inventory_selection|cgb_corpus_inventory_selftest|cgb_age_m3_tracer|cgb_age_m3_m3_bg_lcdc_cgbBCE|cgb_age_m3_m3_bg_lcdc_nocgb_ncmBCE|cgb_age_m3_m3_bg_lcdc_ds_cgbBCE|cgb_age_m3_m3_bg_scx_cgbBCE|cgb_age_m3_m3_bg_scx_nocgb_ncmBCE|cgb_age_m3_m3_bg_scx_ds_cgbBCE|cgb_age_m3_pixel_controls|cgb_age_m3_early_frame_control)$'"
        status: pass
  - id: CGB-08-RESEARCH14-OWNERSHIP
    description: Each of the 31 inherited research14 gates has a tested resolution or explicit, owned evidence limitation mirrored in model-gate documentation.
    requirement: CGB-08
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R '^(cgb_research14_dispositions|cgb_research14_dispositions_controls|model_gates|cgb_speed_dispositions|cgb_hdma_dispositions)$'"
        status: pass
  - id: CGB-10-FROZEN-CORPUS-BASELINE
    description: AGE additions preserve frozen corpus membership, speed-domain rules, and the byte-identical DMG baseline.
    requirement: CGB-10
    human_judgment: false
    verification:
      - kind: other
        ref: "python3 -I tests/scripts/verify-speed-domains.py src/core/gabbaboy.c && bash tests/scripts/verify-dmg-baseline.sh"
        status: pass
duration: 21min
completed: 2026-10-15
status: complete
---

# Phase 14 Plan 10: CGB-E Model Qualification and Corpus Summary

**Inherited AGE timing rows are now source-attributed and independently checked, and all 31 research14 gates have executable, owned dispositions without promoting unresolved software observations to hardware claims.**

## Performance

- **Duration:** 21 minutes from the first RED evidence commit through final focused verification.
- **Started:** 2026-10-15T21:51:25Z
- **Completed:** 2026-10-15T22:11:58Z
- **Tasks:** 2 completed.
- **Files modified:** 14 plan artifacts before this SUMMARY, plus this SUMMARY.
- **Actuals:** 65,338 tokens by unified-diff character count divided by four; 5 task commits measured from `plan_head_before`.
- **Inputs:** AGE source commit `1f5bc10e2cb60b86c19f8d0287ff78f410c4f639`; inventory SHA-256 `66545786ea4b20655a8e4146cb215adc837e772087c0718a53ce0d5d54f855dc`; speed-disposition SHA-256 `9a5be5731e4b72be38dbded66dfbed2d15790ee550dbc05c4b3dbe1989dfa8cc`; AGE manifest SHA-256 `52a022327cc9b6eb9df2a6383b77cf8c006fca26e789c757c15dc2c58e1e4791`.

## Accomplishments

- Bound the 14 normal-speed `stat-mode-cgbE` rows to source labels and independent expected ROM bytes. Five rows match and nine fail; the exact mask remains `0D11` with signature `529c3f4d3b1571437d88b1c4806ada4dfa786b4740751b3128628df6abe8ffe9`. The complete guest remains an expected failure.
- Bound all 13 AGE row-oracle cases and 19 admitted AGE identities. The live guest contract checked 142 rows. Two cases pass all rows and 11 retain exact expected-failure dispositions. The mixed `spsw-mode0-cgbBCE` case remains 3/15, mask `01C0`; its 105 semantic observations preserve five distinct LY reads and every individual SCX/STAT read.
- Recorded all 31 inherited research14 gates in both the inventory and `docs/model-gates.md`. Four are test-resolved and 27 remain `UNKNOWN/research:14` limitations with applicability, source, evidence or limitation, tests, owner, and revisit condition. GATE-15 and GATE-34 continue to require an independent DMG length-retention fixture and an explicit baseline revision.
- Preserved the distinct AGE image cohort: 0/6 full images match, with 18,208 mismatching pixels out of 138,240. These evaluator outcomes do not convert into AGE row, guest, or hardware passes.
- Preserved frozen membership at 109 admitted outputs, 107 required identities, and zero pending outputs. No production core or public API change, dependency, source repin, hardware claim, or Phase 15 work was introduced. Phase 12’s `0x20004` T constant and Phase 13 policies remain untouched.

## TDD Gate Compliance

- **Task 1 RED:** `test_stat_mode_cgbe_binds_source_rows_to_expected_values` failed on the missing 14-row source contract. The current-run classifier returned `RED_EVIDENCE_OK`; semantic assessment confirms the target assertion failed after successful fixture loading and test collection. Evidence: [14-10-red-task1.json](14-10-red-task1.json). GREEN implementation: `7faab0d`.
- **Task 2 RED:** `test_all_research14_gates_have_owned_dispositions` failed because the inventory had no research14 disposition rows. The current-run classifier returned `RED_EVIDENCE_OK`; semantic assessment confirms successful inventory loading and unittest collection. Evidence: [14-10-red-task2.json](14-10-red-task2.json). GREEN implementation: `43b1668`.
- RED precedes GREEN for both tasks. The later bounded-fixture-control commit strengthens the Task 2 trust-boundary verification.

## Task Commits

1. **Task 1 RED:** `9a5134b` — test(14-10): add failing AGE source assertion identity test.
2. **Task 1 GREEN:** `7faab0d` — feat(14-10): bind normal-speed STAT rows to source expectations.
3. **Task 2 RED:** `4ca9346` — test(14-10): add failing research gate ownership contract.
4. **Task 2 GREEN:** `43b1668` — feat(14-10): bind inherited AGE rows and research gates.
5. **Task 2 hardening:** `8083b25` — fix(14-10): exercise hostile AGE fixture bounds.

## Files Created and Modified

- `tests/scripts/verify-age-phase14-contract.py` — live AGE row, corpus identity, research14 ledger, and bounded-fixture verifier with negative controls.
- `tests/scripts/test_age_phase14_contract.py` and `tests/scripts/test_age_phase14_inherited_contract.py` — meaningful RED contracts for source rows and complete research14 gate membership.
- `tests/test_age.c` — private test-only row-observation output used by the verifier.
- `tests/scripts/verify-cgb-corpus-inventory.py`, `tests/external/cgb-corpus-inventory.json`, and `tests/external/cgb-speed-dispositions.json` — cross-bound inventory identities, exact row outcomes, semantic observations, and gate ownership.
- `tests/CMakeLists.txt` and `tests/expected-tests.txt` — required verifier, negative-control, and inherited-contract test registration.
- `docs/cgb-profile.md` and `docs/model-gates.md` — source-backed normal-speed STAT observations and precise gate limits.
- `.planning/WINDOWS.md` — entries for the two documented execution deviations.

## Decisions Made

- No PPU or APU timing correction was justified: the inherited rows and snapshots do not isolate a precise event with an independent passing boundary expectation.
- Full-image, row-level, evaluator, guest, and physical-hardware results remain separate evidence classes.
- GATE-15 and GATE-34 stay unresolved until independent DMG length-retention evidence and its explicit baseline revision are available.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated the inventory self-test's next unbound-case expectation.**
- **Found during:** Task 2.
- **Issue:** Binding all 19 AGE identities moved the first intentionally unbound case in the complete-inventory self-test from an AGE case to `magentests:bg_oam_priority`.
- **Fix:** Updated the expected diagnostic so the test continues to prove that complete inventory mode rejects the next unbound case.
- **Files modified:** `tests/scripts/verify-cgb-corpus-inventory.py`.
- **Verification:** `cgb_corpus_inventory_selftest` passed.
- **Committed in:** `43b1668`.

**2. [Rule 2 - Security verification] Added hostile fixture-bound controls.**
- **Found during:** Task 2 threat-model review.
- **Issue:** Fixture paths, sizes, row counts, address ranges, and guest work budgets had bounds, but those rejection paths were not covered by negative controls; JSON booleans also satisfy Python's integer type check.
- **Fix:** Added controls for traversal, size drift, excessive rows, excessive budget, and out-of-ROM expected-address ranges, and made integer bounds reject booleans.
- **Files modified:** `tests/scripts/verify-age-phase14-contract.py`.
- **Verification:** `cgb_age_assertion_controls` passed with all five fixture controls plus the row, semantic, xpass, and signature controls.
- **Committed in:** `8083b25`.

**Total deviations:** 2 auto-fixed (one blocking test expectation and one threat-model verification gap). Both were directly required to keep the expanded inventory executable and its guest boundary bounded.

## Verification Evidence and Limitations

- The required Phase 14 AGE row targets all produced terminal dispositions in the live runner. `stat-mode-cgbE` remains 5/14 (`0D11`); `spsw-mode0-cgbBCE` remains 3/15 (`01C0`) with LY and SCX/STAT observations independently identified.
- The live identity verifier reports `cases=13 rows=142 mode0-semantic=105 age-identities=19`. Its negative controls reject missing and duplicate rows, merged LY/SCX identity, xpass, signature drift, traversal, incorrect size, excessive rows or budget, and out-of-range addresses.
- The research14 contract reports `gates=31 unknown=27`; its controls reject missing/duplicate gates, missing owner/source/applicability, removed GATE-15 DMG obligations, and false gate promotion.
- The focused required cohort passed 16/16 CTests. The corpus-selection, six AGE image cases, image controls, and early-frame control passed 11/11 CTests. Speed-domain scan reported 44 functions; the frozen DMG baseline passed with 313 inventory keys, 15 Mooneye keys, 20 acceptance keys, 2 benchmark keys, and zero changed rows.
- Inherited qualification counts remain distinct: SameSuite APU records 8 guest passes and 62 exact expected failures across 4,784 assertions; the six AGE image results above are evaluator comparisons, not guest passes. These inherited SameSuite counts are not a new hardware qualification.
- No physical CGB-E measurement or game-level proof is claimed. GATE-15/34 retain the explicit independent-DMG-fixture and baseline-revision obligations; other unresolved hardware/model behavior remains owned and limited rather than fabricated as an xfail or pass.

## Issues Encountered

The first targeted CTest invocation used a nonexistent `build/phase1` directory; the repository's `phase1` preset writes to `build`. Re-running from the configured `build` directory passed. No implementation issue remained.

## Self-Check: PASSED

All created and modified plan artifacts exist, `summary_coverage` passes for the block-schema coverage records, and all five task commits are ancestors of the implementation head.


## Sanitized ancestry

The top-level commit windows use sanitized unpublished ancestry. Historical execution revision IDs and task IDs above remain as originally recorded; [14-HISTORY-REDACTION.md](14-HISTORY-REDACTION.md) maps them to the equivalent sanitized commits. Fresh final qualification is recorded separately after this rewrite.
