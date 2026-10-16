---
phase: 15-cgb-acceptance-support-ledger-and-v0-2-0-release
plan: "02"
subsystem: testing
tags: [support-ledger, cgb, ctest, python, release-evidence]
requires:
  - phase: 15-01
    provides: "Public CGB game-evidence absence statement and production claim checker"
provides:
  - "Receipt-bound v0.2.0 support ledger with complete CGB model and assertion denominators"
  - "Exact-tag support sidecar generation and schema-scoped ledger selection"
  - "Reconciled unreleased pointer and current corpus evidence documentation"
affects: [phase-15-release-qualification, support-claims, cgb-corpus-validation]
actuals:
  tokens: 830245
  tasks: 2
  commits: 5
commits: 5
plan_head_before: 1f67527a9ec4f8629f9b2b26ce74e1857ae791f0
plan_head_after: 9ab24c92b883a9ec4e8c38093efeba22467668f9
tech-stack:
  added: []
  patterns:
    - "Release ledger records exact corpus receipt and source-input identities; tagged sidecars supply release source binding"
    - "Positive and negative acceptance controls execute through production CLI entry points"
key-files:
  created:
    - docs/support/v0.2.0.md
  modified:
    - docs/support/unreleased.md
    - docs/cgb-corpus.md
    - tests/scripts/verify-support-ledger.py
    - tests/scripts/verify-cgb-corpus-claims.py
key-decisions:
  - "v0.2.0 selects only docs/support/v0.2.0.md; patch-tag reuse remains within the validated major/minor scope."
  - "The tracked ledger binds the actual receipt and producer revision without embedding a self-referential release source SHA; the exact-tag sidecar supplies that binding."
  - "CGB game-level evidence remains explicitly absent, while software corpus evidence and physical-hardware limitations remain separate."
patterns-established:
  - "Schema-2 support claims validate complete receipt, inventory, disposition, source-input, and build-artifact bytes before producing a release sidecar."
  - "Temporary Git fixtures exercise positive tag behavior and named rejection controls through the production validator."
requirements-completed: [SHIP-09, CGB-11]
coverage:
  - id: D1
    description: "The v0.2.0 support ledger records model, mode, cartridge, evidence, corpus, denominator, failure, exclusion, and known-issue scope from the actual receipt."
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-support-ledger.py --check-current --receipt build/cgb-corpus-receipt.json"
        status: pass
      - kind: integration
        ref: "python3 -I tests/scripts/verify-support-ledger.py --self-test"
        status: pass
  - id: D2
    description: "The v0.2.0 support ledger is selected exactly for v0.2.0 and binds release sidecars to the tagged ledger, receipt, inventory, and source inputs."
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-support-ledger.py --self-test (positive schema-2 path and 14 rejected controls)"
        status: pass
      - kind: integration
        ref: "python3 -I tests/scripts/verify-support-ledger.py --self-test (temporary Git sidecar fixture: positive path and 17 controls)"
        status: pass
  - id: D3
    description: "The unreleased document is a bounded pointer to the reconciled v0.2.0 ledger, and the claim checker rejects missing or contrary statements."
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-cgb-corpus-claims.py --self-test (15 rejection controls)"
        status: pass
  - id: D4
    description: "The CGB corpus guide cites current producer evidence while separating guest outcomes from assertion outcomes and preserving evidence limits."
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-cgb-corpus-claims.py --receipt build/cgb-corpus-receipt.json --source-revision 9ab24c92b883a9ec4e8c38093efeba22467668f9 --allow-ancestor"
        status: pass
      - kind: integration
        ref: "python3 -I tests/scripts/verify-cgb-corpus-inventory.py --bindings"
        status: pass
  - id: D5
    description: "Schema-1 behavior remains covered while schema-2 ledger and sidecar paths reject malformed, stale, narrowed, duplicated, or forged evidence."
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -m py_compile tests/scripts/verify-support-ledger.py tests/scripts/verify-cgb-corpus-claims.py"
        status: pass
      - kind: integration
        ref: "python3 -I tests/scripts/verify-support-ledger.py --self-test"
        status: pass
duration: 42min
started: "2026-10-16T14:47:14Z"
completed: "2026-10-16T15:29:26Z"
status: complete
---

# Phase 15 Plan 02: CGB Acceptance Support Ledger and v0.2.0 Release Summary

**A receipt-bound v0.2.0 ledger reports 107 CGB cases with 25 actual guest passes, 82 matched expected failures, and assertion-level results kept separate.**

## Performance

- **Duration:** 42 minutes, measured from the first plan commit through final verification.
- **Started:** 2026-10-16 14:47:14 UTC (first recorded plan commit; executor start was not separately persisted).
- **Completed:** 2026-10-16 15:29:26 UTC.
- **Tasks:** 2 completed.
- **Files modified:** 5 plan deliverables.

## Accomplishments

- Produced the full nonce-bound CGB corpus receipt from source revision `36be4dc093566b242d61c4d6afc0d024f2ff2059`. CTest passed 108/108 entries; the receipt covers 107 required model cases, with 25 actual guest passes and 82 actual guest failures matched to expected failures. Its 4,959 assertion rows contain 2,845 passes and 2,114 failures. Receipt run ID: `bccb54cf2e23f758299550a47e54828d65b1e7c28f2862ad2305fa880c943f59`; receipt SHA-256: `78e8a98f72be7431029dd8a7f05c31d7b3c198253b6506480e8570e76742c3b0`.
- Added a readable schema-2 v0.2.0 ledger with model/mode and cartridge/save scope, evidence classes, suite denominators, known limitations, and the explicit statement that no CGB game-level evidence exists. The sidecar validator binds a release tag to its exact ledger bytes, corpus receipt, inventory identities, source inputs, and build artifacts.
- Reconciled `unreleased.md` to a bounded pointer and updated the corpus guide with the current local producer evidence. The docs distinguish guest outcomes from assertion outcomes and retain physical CGB-E as UNKNOWN/POLICY.
- Preserved schema-1 checks, constrained patch-tag reuse to the same major/minor support scope, and added production-entry positive paths and negative controls for schema-2 claims and sidecars.

## Task Commits

Task 1 used a TDD acceptance fixture followed by implementation and receipt refresh:

1. **Task 1 RED:** `53aaeb2` — add v0.2 ledger acceptance fixture.
2. **Task 1 implementation:** `36be4dc` — add receipt-bound v0.2 support ledger.
3. **Task 1 receipt refresh:** `452f398` — refresh the receipt binding after the actual producer run.
4. **Task 2:** `fd9a32d` — add exact-tag support sidecars and corpus ledger.
5. **Task 2 verification fix:** `9ab24c9` — keep the isolated sidecar fixture commit reproducible.

The plan metadata commit records this summary separately from the five measured task commits.

## Files Created/Modified

- `docs/support/v0.2.0.md` — readable release scope and structured receipt-bound evidence block.
- `docs/support/unreleased.md` — concise pointer to the reconciled v0.2.0 ledger.
- `docs/cgb-corpus.md` — current producer receipt and suite-level evidence with explicit model limits.
- `tests/scripts/verify-support-ledger.py` — schema-scoped selection, ledger validation, sidecar binding, and acceptance controls.
- `tests/scripts/verify-cgb-corpus-claims.py` — synchronized support and corpus claim validation with negative controls.

## Decisions Made

- v0.2.0 must resolve to the exact `docs/support/v0.2.0.md` path. Fix-only patch tags may reuse a ledger only inside the validated major/minor scope.
- The tracked ledger records the actual producer revision and receipt bytes but omits a future release source SHA; the exact-tag sidecar binds that SHA without a self-reference.
- CGB software corpus evidence does not imply game-level compatibility or physical-hardware qualification. CGB game-level evidence remains explicitly absent.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Kept the temporary tagged-sidecar fixture commit reproducible after implementation files entered HEAD.**
- **Found during:** Task 2 post-commit verification.
- **Issue:** The fixture cloned current HEAD, then overlaid byte-identical files and attempted an empty commit, causing the production self-test to fail after the implementation commit.
- **Fix:** Added a temporary marker only inside the isolated test repository so its tagged commit remains non-empty without changing the bound ledger or receipt inputs.
- **Files modified:** `tests/scripts/verify-support-ledger.py`.
- **Verification:** The full support-ledger self-test passes with schema-1 and schema-2 positive paths, 14 ledger controls, and 17 sidecar fixture controls.
- **Committed in:** `9ab24c9`.

**Total deviations:** 1 auto-fixed (Rule 1 - Bug). The fix only makes the planned isolated Git fixture reliable after the implementation is committed.

## Issues Encountered

The plan's abbreviated corpus command did not create a run nonce and was rejected by the producer. The complete run used the producer's nonce-bound sequence (`--begin-run`, one full CTest stream, then `--from-ctest`) and passed its independent required-test inventory check. No hosted CI run or physical CGB-E observation is claimed by this plan.

## User Setup Required

None. No external service or credential configuration is required.

## Next Phase Readiness

The support ledger and its local evidence validators are ready for the remaining Phase 15 release-qualification work. The ledger preserves the absence of CGB game-level evidence and the lack of physical CGB-E qualification as explicit scope limits.

---
*Phase: 15-cgb-acceptance-support-ledger-and-v0-2-0-release*
*Plan: 02*
*Completed: 2026-10-16*

## Self-Check: PASSED

The summary file exists and all five measured task commits are ancestors of the recorded plan head.
