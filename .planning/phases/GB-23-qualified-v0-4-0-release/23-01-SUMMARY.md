---
phase: GB-23-qualified-v0-4-0-release
plan: "01"
subsystem: release-evidence
tags: [support-ledger, python, ctest, immutable-evidence]
requires:
  - phase: GB-21-cgb-game-progress-and-scene-regressions
    provides: Bounded candidate outcomes and CGB-CPU-E harness evidence.
  - phase: GB-22-composition-and-microtest-evidence
    provides: Synthetic tracer acceptance and metadata-only assessment.
  - phase: GB-19-qualified-v0-3-0-release
    provides: Historical support profile and byte-stable v0.3 ledger.
provides:
  - Source-bound v0.4 candidate, harness, diagnostic, inherited-support and limitation claims.
  - Production v0.4 ledger rendering and mutation controls.
affects: [23-02, release-notes, support-ledger]
tech-stack:
  added: []
  patterns:
    - Closed profile validated against immutable Git objects.
    - Counts and requirement states recomputed from pinned evidence.
    - Visible-disclosure checks paired with causal hidden-output controls.
key-files:
  created: [tests/data/support-claims-v0.4.json]
  modified:
    - tests/scripts/verify-support-ledger.py
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "Carry the nine state/core/player claims from the pinned v0.3 profile without creating new producer receipts."
  - "Report the CGB-CPU-E native harness as repeatability-only and diagnostics as synthetic plus metadata-only."
  - "REL-01 remains Pending until Plan 23-06 establishes actual release evidence."
patterns-established:
  - "Phase 21/22 artifacts, inventories and requirement states use exact historical Git revisions and blob identities."
  - "Hidden HTML-comment and fenced-code disclosures have causal refusal controls."
requirements-completed: []
coverage:
  - id: CANDIDATE-OUTCOMES
    description: "The production writer renders both source/rights-scope no-go reasons and rejects candidate promotion."
    human_judgment: false
    verification:
      - kind: integration
        ref: "Focused Phase 23 CTest command passed 7/7, including support_ledger_v04_tracer and support_claims_v04_controls, at 004aac8474d3022b2f0e3b53e4f22b1ea0e52e9d."
        status: pass
  - id: HARNESS-AND-DIAGNOSTIC-SCOPE
    description: "The ledger reports the CGB-CPU-E harness as repeatability-only and derives 513/7/0/0 counts from immutable metadata."
    human_judgment: false
    verification:
      - kind: integration
        ref: "support_claims_v04_controls and support_ledger_v04_tracer passed, including model/source/count/status and hidden-disclosure mutations."
        status: pass
  - id: HISTORICAL-SUPPORT-AND-LIMITS
    description: "Historical v0.3 claims and ledger bytes remain stable while current limits and Pending requirements are explicit."
    human_judgment: false
    verification:
      - kind: integration
        ref: "support_claims, support_claims_controls, release_disclosure_generator and release_disclosure_controls passed; historical-ledger mutation controls passed."
        status: pass
actuals:
  tokens: 14780.5
  tasks: 2
  commits: 7
plan_head_before: 4a4513998ba026d1c6e1dec6d8ab6fc5cd517f4f
plan_head_after: 004aac8474d3022b2f0e3b53e4f22b1ea0e52e9d
duration: 1h
completed: 2026-11-03
status: complete
---

# Phase 23 Plan 01: Source-bound support ledger

**The v0.4 ledger renders pinned candidate outcomes, harness and diagnostic boundaries, inherited support claims, and release limitations through the existing production writer.**

## Performance

- **Duration:** 1 h
- **Started:** 2026-11-04T00:53:14Z
- **Completed:** 2026-11-04T01:53:15Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Bound Potion Panic and µCity 1.3 to immutable Phase 21 records and preserved their distinct source/rights-scope no-go reasons without asserting a license prohibition.
- Labeled the CGB-CPU-E native-mode original harness as harness-only; RGB555/PCM digests establish repeatability only.
- Bound the synthetic tracer, 513-entry inventory, seven unresolved gates, zero fixtures admitted, and zero executed to immutable Phase 22 evidence.
- Carried forward all nine state/core/player claims from the historical v0.3 profile without manufacturing receipts; preserved v0.3 ledger bytes.
- Kept FIXT-01, RIGHTS-01, DIAG-01, DIAG-02 and REL-01 Pending. Added source, count, model, mode, execution, status, visibility and historical-ledger controls.

## Task Commits

1. **Task 1: Render and judge the two-candidate absence through the production ledger path** — `b2fd85bf`, `ec95f6b8`, `fc2e2748` (test, test, feat).
2. **Task 2: Expand the ledger contract to harness, diagnostic and inherited support limits** — `8054efc0`, `6d46f196`, `b1d53972`, `004aac84` (test, feat, fix, fix).

## TDD Evidence

- **Task 1 RED:** `support_claims_v04` failed its intended output assertion while the checker still returned the v0.3 result. The JUnit record returned `RED_EVIDENCE_OK`, and semantic review confirmed the target executed and failed on the planned assertion. Evidence: `build/tdd-red-evidence/23-01-T1-red.json`.
- **Task 1 GREEN/tracer gate:** The disposable 0.4.0 subject rendered both pinned outcomes. The exact configure/build/CTest command passed all five selected tests after the feature commit, so the tracer gate passed before expansion.
- **Task 2 RED:** `support_claims_v04` failed because candidate-only output omitted harness, diagnostics and inherited claims. Its JUnit record returned `RED_EVIDENCE_OK` with the intended semantic failure. Evidence: `build/tdd-red-evidence/23-01-T2-red.json`.
- **Task 2 GREEN:** The exact seven-test verification command passed. No separate refactor was needed.

## Files Created/Modified

- `tests/data/support-claims-v0.4.json` — Closed v0.4 source-bound claim profile.
- `tests/scripts/verify-support-ledger.py` — Immutable validation, rendering, visibility checks and causal controls.
- `tests/CMakeLists.txt` — Profile, controls and tracer CTest registration.
- `tests/expected-tests.txt` — Exact test inventory membership.

## Decisions Made

- The Phase 22 UAT record, not the metadata report alone, establishes that the synthetic tracer passed.
- Inherited v0.3 claims retain their original evidence names and source identity; this ledger adds no producer receipts.
- REL-01 stays Pending until Plan 23-06 establishes the actual release evidence.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Bind synthetic tracer acceptance to the Phase 22 UAT record**
- **Found during:** Task 2 verification
- **Issue:** The Phase 22 metadata report did not itself record the tracer test result.
- **Fix:** Added the immutable Phase 22 UAT path/blob pin and validated its passing tracer evidence.
- **Files modified:** `tests/data/support-claims-v0.4.json`, `tests/scripts/verify-support-ledger.py`
- **Verification:** Final seven-test Task 2 command passed, including the production tracer.
- **Committed in:** `b1d53972`

**2. [Rule 1 - Bug] Render the exact repeatability-only sentence enforced by the visibility guard**
- **Found during:** Task 2 verification
- **Issue:** The rendered meaning was correct but omitted the exact profile sentence required by the guard.
- **Fix:** Rendered the pinned profile wording and retained accuracy/perception exclusions.
- **Files modified:** `tests/scripts/verify-support-ledger.py`
- **Verification:** Final seven-test Task 2 command passed, including visible-output and hidden-output controls.
- **Committed in:** `004aac84`

**Total deviations:** 2 auto-fixed bugs (Rule 1). Both fixes closed verification defects within plan scope.

## Issues Encountered

The first Task 2 run rejected an unsupported Phase 22 wording assumption; the next exposed an exact-text mismatch in the new visibility guard. Both were fixed and the complete focused suite then passed.

## Known Stubs

None. The changed files contain no placeholder output or unwired data path.

## User Setup Required

None.

## Next Phase Readiness

Plan 23-01 is complete and the shared claim profile is ready for Plan 23-02, **Concise release disclosure**. Phase 23 remains in progress; REL-01 remains Pending, and no v0.4.0 release or publication is claimed. Continue within the accepted Phase 23 sequence and stop at the phase boundary.

## Self-Check

PASSED — the summary exists, all seven task commits are ancestors of the current head, the plan ledger measures seven commits from `plan_head_before` to `plan_head_after`, and `summary_coverage` passes.

---
*Phase: GB-23-qualified-v0-4-0-release*
*Completed: 2026-11-03*
