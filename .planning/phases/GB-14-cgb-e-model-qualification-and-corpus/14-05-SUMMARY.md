---
phase: 14-cgb-e-model-qualification-and-corpus
plan: "05"
subsystem: test-coverage
tags: [cgb, corpus, provenance, inventory]
requires: []
provides:
  - Pinned source closure and frozen CGB case membership for four external suites
  - Fail-closed corpus inventory validator with positive and negative controls
  - Documented output admission, rights, model, and evidence states
affects: [phase-14-corpus-qualification, verify-work]
actuals:
  tokens: 100552
  tasks: 2
  commits: 3
plan_head_before: f019f755f66f6b41fc00b39807df4bd32b19bf69
plan_head_after: 3cacf9822f2a36ce787920adaae56e996cf4ccc8
tech-stack:
  added: []
  patterns:
    - Independently frozen source and case rosters validate membership before execution
    - Standard-library validation bounds input and fixture reads before processing
key-files:
  created:
    - tests/external/cgb-corpus-inventory.json
    - tests/scripts/verify-cgb-corpus-inventory.py
    - docs/cgb-corpus.md
  modified:
    - fixtures/magentests/ELIGIBILITY.md
key-decisions:
  - Keep rights-blocked or unsupported-model optional fixtures visible as not-run and outside executed counts.
  - Keep author expectation, evaluator disposition, execution result, and assertion evidence separate.
  - Leave CGB-10 open; this plan freezes corpus membership but does not complete qualification.
requirements-completed: []
coverage:
  - id: D1
    description: Frozen pinned source closure and selected CGB model/mode case identities
    human_judgment: false
    verification:
      - kind: unit
        ref: python3 -I tests/scripts/verify-cgb-corpus-inventory.py --selection-only
        status: pass
      - kind: unit
        ref: python3 -I tests/scripts/verify-cgb-corpus-inventory.py --self-test; 18 named mutation controls
        status: pass
  - id: D2
    description: Admission, rights, model applicability, and MagenTests documentation agree with pinned manifests
    human_judgment: false
    verification:
      - kind: integration
        ref: python3 -I tests/scripts/verify-cgb-corpus-inventory.py --selection-only
        status: pass
      - kind: integration
        ref: python3 -I tests/scripts/verify-cgb-corpus-inventory.py --self-test; stale Magen claim and false evidence controls
        status: pass
duration: 13m
completed: 2026-10-15
status: complete
---

# Phase 14 Plan 05: Pinned CGB Corpus Inventory Summary

**Frozen inventory covers 181 pinned source candidates, 109 output states, and 107 CGB model/mode cases with independent membership checks and bounded evidence reads.**

## Performance

- **Duration:** 13m
- **Started:** 2026-10-15T17:06:08Z
- **Completed:** 2026-10-15T17:19:08Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Enumerated 181 source candidates across Mooneye, SameSuite, AGE, and MagenTests; froze 109 output records (28 admitted, 81 pending) and 107 required model/mode cases.
- Preserved the 83-candidate Mooneye header closure and selected nine cases, including the unsuffixed `acceptance/timer/div_write.s` identity and source-only `vblank_stat_intr-C.s`; froze all 74 SameSuite APU/DMA cases, 19 AGE cases, and five MagenTests CGB cases.
- Separated author expectations, evaluator dispositions, admission/rights states, terminal observations, and assertion contracts. Optional local acid2 and Mealybug entries remain unrun behind rights/model gates, with no hardware qualification claimed.
- Corrected the stale MagenTests HBlank not-vendored statement: the output is admitted as the seventh fixture, while `key0_lock_after_boot` remains source-only.
- Bounded admitted fixture reads to 1 MB and the downstream expected-test inventory to 2 MB, checking file size before reading and testing both rejection paths.

## Task Commits

1. **Task 1: Tracer: pinned Mooneye source header becomes a validated selected identity** - `96bbd77` (`test(14-05): freeze pinned CGB corpus selection`)
2. **Task 2: Expand broad source closure and rights/model dispositions** - `1caa2b0` (`test(14-05): validate CGB corpus scope and provenance`)
3. **Task 2 Rule 2 correctness follow-up: Bound evidence reads and add size-limit controls** - `3cacf98` (`fix(14-05): bound CGB corpus evidence reads`)

## Files Created/Modified

- `tests/external/cgb-corpus-inventory.json` - Pinned source/output/case inventory with independent membership fingerprints and explicit lifecycle/evidence states.
- `tests/scripts/verify-cgb-corpus-inventory.py` - Standard-library validator for roster identity, provenance, rights/model dispositions, admission integrity, and completion preconditions.
- `docs/cgb-corpus.md` - Inventory schema, cohort counts, lifecycle meanings, and machine-checked mirror of selected identities.
- `fixtures/magentests/ELIGIBILITY.md` - Updated the HBlank fixture admission description.

## Verification

- `python3 -I tests/scripts/verify-cgb-corpus-inventory.py --selection-only` passed: `sources=181 outputs=109 admitted=28 pending=81 cases=107 assertions=pending`.
- `python3 -I tests/scripts/verify-cgb-corpus-inventory.py --self-test` passed 18 expected-mismatch controls: oversized output, omitted/duplicate source, wrong or filtered unsuffixed header, substituted case, empty denominator, source-only execution, missing family, changed pin, unknown source, incorrect SameSuite README quote, false hardware claim, stale Magen admission, optional rights/model mismatch, missing CTest bindings, oversized expected-test inventory, and incomplete admission.
- `git diff --check` passed before the final task commit. Task commits contain no deletions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing bounded-read protection] Bound corpus output and expected-test inventory reads.**
- **Found during:** Task 2
- **Issue:** T-14-10 requires bounded parser/output work; the verifier hashed admitted fixture bytes and the downstream expected-test inventory without enforcing per-file size limits first.
- **Fix:** Enforced a 1 MB maximum for admitted fixture bytes and a 2 MB maximum for the expected-test inventory, with stat-based size checks before reads and dedicated rejection controls.
- **Files modified:** `tests/scripts/verify-cgb-corpus-inventory.py`
- **Verification:** Selection-only validation and all 18 self-test controls passed.
- **Committed in:** `3cacf98`

**Total deviations:** 1 auto-fixed correctness issue.
**Impact on plan:** Completed the planned bounded-work mitigation without expanding public APIs, dependencies, or phase scope.

## Issues Encountered

The Git metadata directory was read-only to the default sandbox, so the plan-local pre-commit ledger could not be persisted there. Commit count and base/head identities were measured directly from Git history; authorized task commits completed with hooks enabled. Pre-existing shared `.planning/STATE.md`, `.planning/config.json`, `.planning/state.json`, and `.planning/milestone.lock` changes were left untouched.

## User Setup Required

None.

## Next Phase Readiness

Plan 14-05 freezes source and case identities; it does not qualify pending outputs or complete CGB-10. Phase 14 remains in progress, and later phase plans must bind executions and assertions before a qualification claim.

## Self-Check: PASSED

The three task commits are ancestors of the current implementation head, and all four declared deliverable files exist. The inventory validator, all 18 negative controls, the strict summary coverage checker, and GSD coverage classification passed.

---
*Phase: 14-cgb-e-model-qualification-and-corpus*
*Completed: 2026-10-15*
