---
phase: GB-22-composition-and-microtest-evidence
plan: "10"
subsystem: testing
tags: [python, cmake, ctest, diagnostics, evidence]

requires:
  - phase: GB-22-composition-and-microtest-evidence
    provides: Synthetic tracer and metadata assessment from Plans 22-01 and 22-02
provides:
  - Immutable metadata and real-fixture no-go contract with causal controls
  - Synchronized Phase 22 diagnostic claims in both public evidence documents
affects: [Phase 22 Plan 22-11, release evidence]

actuals:
  tokens: 13772
  tasks: 2
  commits: 5

tech-stack:
  added: []
  patterns:
    - Python standard-library checker reads bounded facts from one resolved immutable commit
    - Boundary assertions use an explicit historical commit rather than live HEAD routing

key-files:
  created:
    - tests/scripts/verify-diagnostic-evidence.py
  modified:
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - docs/diagnostic-evidence.md
    - docs/cgb-profile.md

key-decisions:
  - "D-141 remains the scope boundary: synthetic evidence and metadata-only no-go assessment; DIAG-01, DIAG-02, and RIGHTS-01 remain Pending."
  - "A real approval refusal passes only with exit code 2 and the complete seven unresolved gate set."

patterns-established:
  - "The checker reports metadata inventory and refusal evidence without fetching, retaining, building, or executing upstream payloads."
  - "CTest and expected-test inventory membership are checked as an exact set with mutation controls."

requirements-completed: []
coverage:
  - id: D1
    description: Immutable snapshot proves the 513-name metadata inventory and exact seven-gate real-fixture refusal.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_(evidence_(contract|controls)|acid2_(tracer|contract|controls)|fixture_admission_(contract|controls))$'"
        status: pass
      - kind: other
        ref: "python3 -I tests/scripts/verify-diagnostic-evidence.py --check --repo-root . --source-revision HEAD --write-evidence build/phase22/evidence.json"
        status: pass
  - id: D2
    description: Public diagnostic documents state the metadata-only no-go disposition and retain evidence and compatibility limits.
    human_judgment: false
    verification:
      - kind: integration
        ref: "phase22_evidence_controls CTest: documentation and claim mutations are rejected"
        status: pass
      - kind: other
        ref: "phase1 preset configure/build and immutable diagnostic evidence check"
        status: pass
  - id: D3
    description: Existing synthetic tracer and fixture-admission contracts remain passing, with boundary checks bound to an immutable supplied revision.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_(evidence_(contract|controls)|acid2_(tracer|contract|controls)|fixture_admission_(contract|controls))$'"
        status: pass
      - kind: other
        ref: "phase22_evidence_controls CTest: immutable historical boundary and later-HEAD mutation controls"
        status: pass

commits: 5
plan_head_before: 8f8056651f70482d41f2d74bbb750b1e846f261d
plan_head_after: 31425631a85c0cd199c955a9c1460ff57b9df827
duration: about 24 min
completed: 2026-11-03
status: complete
---

# Phase 22 Plan 10: Immutable Diagnostic No-Go Contract Summary

**A source-bound checker and CTest controls prove the 513-name metadata inventory, seven unresolved gates, and exact real-fixture refusal while public claims remain synthetic-plus-metadata only.**

## Performance

- **Duration:** about 24 min
- **Started:** approximately 2026-11-03T10:58:00Z
- **Completed:** 2026-11-03T11:22:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added an immutable snapshot checker that verifies all 513 identities, seven unresolved evidence gates, zero real admitted or executed cases, the 31 excluded and 482 blocked accounting, and a specifically valid approval refusal (exit 2 with every gate present).
- Added causal controls for metadata, assessment, public claims, CTest inventory, payload and package-policy boundaries, and historical boundary facts. The existing synthetic tracer and fixture-admission controls also pass.
- Reconciled both public diagnostic documents with the same evidence, preserved the open requirements and compatibility limits, and made no upstream payload or real-result claim.

## Task Commits

1. **Task 1: Prove one immutable metadata/no-go snapshot through the real assessment gate and CTest** - `2e965fec` (feat), `4e5b4696` (fix), `b04a66be` (fix)
2. **Task 2: Reconcile public claims with the same checked metadata snapshot** - `4188f1bf` (feat), `31425631` (fix)

## Files Created/Modified

- `tests/scripts/verify-diagnostic-evidence.py` - Immutable metadata, approval-refusal, claims, membership, and boundary checker with negative controls.
- `tests/CMakeLists.txt` - Registers the two new immutable evidence CTests.
- `tests/expected-tests.txt` - Tracks the exact Phase 22 test inventory.
- `docs/diagnostic-evidence.md` - Records metadata-only findings and the no-go disposition.
- `docs/cgb-profile.md` - Synchronizes the diagnostic profile and evidence limits.

## Decisions Made

- Followed D-141: retain the synthetic-plus-metadata scope; no upstream diagnostic payload was fetched, retained, built, run, or admitted.
- Kept DIAG-01, DIAG-02, and RIGHTS-01 Pending because the seven required real-fixture evidence gates remain unresolved.
- Git object IDs and sizes do not establish the missing ROM SHA-256 values, reproducibility, or redistribution rights; missing evidence is not described as a license prohibition.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected two no-go checker assertions exposed by its negative controls**
- **Found during:** Task 1
- **Issue:** The checker output did not interpolate the checker identity, and one mutant expected a refusal reason that the assessment contract does not emit.
- **Fix:** Corrected the output formatting and asserted the actual specific assessment refusal reason.
- **Files modified:** `tests/scripts/verify-diagnostic-evidence.py`
- **Verification:** Re-ran the evidence contract and mutation-control CTests successfully.
- **Committed in:** `4e5b4696`

**2. [Rule 1 - Bug] Redirected the rights mutation to the claim text enforced by the checker**
- **Found during:** Task 1
- **Issue:** The first rights mutant changed unchecked prose and therefore did not test the intended guard.
- **Fix:** Mutated the checked rights clause and required its specific refusal reason.
- **Files modified:** `tests/scripts/verify-diagnostic-evidence.py`
- **Verification:** The rights mutation is rejected by `phase22_evidence_controls`.
- **Committed in:** `b04a66be`

**3. [Rule 3 - Blocking issue] Aligned the checker’s default build path with the Phase 1 preset**
- **Found during:** Task 2 verification
- **Issue:** The checker default pointed to `build/phase1`, while the configured Phase 1 preset writes under `build`.
- **Fix:** Changed the default to the actual preset build directory so its package-boundary check can complete without a nonstandard override.
- **Files modified:** `tests/scripts/verify-diagnostic-evidence.py`
- **Verification:** Re-ran the configured Phase 1 build, focused CTests, and direct evidence command successfully.
- **Committed in:** `31425631`

**Total deviations:** 3 auto-fixed (2 Rule 1, 1 Rule 3)
**Impact on plan:** The corrections made the planned controls check their intended evidence and use the project’s configured build location; scope and deliverables did not change.

## Issues Encountered

Negative controls exposed incorrect expected reasons and one mutation targeting text outside the enforced claim. Those were corrected and the controls then passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 22-10 is complete. Plan 22-11 remains the next in-phase plan. The seven real-fixture gates remain unresolved, the three requirements remain Pending, and no real diagnostic payload or result was introduced. Do not advance to Phase 23 before the remaining Phase 22 plan and the owner’s phase boundary.

---
*Phase: GB-22-composition-and-microtest-evidence*
*Completed: 2026-11-03*

## Self-Check: PASSED

- Summary file exists and its block-style coverage passes `verify-summary-coverage.py`.
- All five task commits are ancestors of the plan source head recorded above.
