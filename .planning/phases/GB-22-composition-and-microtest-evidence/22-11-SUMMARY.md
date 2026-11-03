---
phase: GB-22-composition-and-microtest-evidence
plan: "11"
subsystem: testing
tags: [diagnostics, immutable-evidence, no-go, exact-head, phase-boundary]
requires:
  - phase: GB-22-composition-and-microtest-evidence
    provides: Synthetic tracer, metadata assessment, immutable no-go checker and mutation controls
provides:
  - Fixed renamed-payload admission scan and immutable Phase 20 checker/policy binding
  - Reviewed synthetic-plus-metadata evidence and automated UAT closure
  - Candidate Phase 22 boundary and owner-controlled Phase 23 handoff
affects: [diagnostic-admission, phase-23-release-evidence]
actuals:
  tokens: 20575
  tasks: 3
  commits: 9
tech-stack:
  added: []
  patterns:
    - Immutable commit blobs bind every diagnostic admission checker and policy dependency
    - Added payloads are scanned individually with bounded content signatures
key-files:
  created:
    - .planning/phases/GB-22-composition-and-microtest-evidence/22-UAT.md
  modified:
    - tests/scripts/verify-diagnostic-admission.py
    - tests/scripts/verify-diagnostic-evidence.py
    - .planning/phases/GB-22-composition-and-microtest-evidence/22-EVIDENCE.md
    - .planning/phases/GB-22-composition-and-microtest-evidence/22-VALIDATION.md
    - .planning/phases/GB-22-composition-and-microtest-evidence/22-REVIEW.md
    - .planning/phases/GB-22-composition-and-microtest-evidence/22-SECURITY.md
    - .planning/phases/GB-22-composition-and-microtest-evidence/.continue-here.md
    - .planning/STATE.md
    - .planning/state.json
    - .planning/ROADMAP.md
key-decisions:
  - "Reject renamed archives and diagnostic payloads by suffix and content signatures, with per-blob bounds."
  - "Bind the Phase 20 checker and policy to the immutable selected source before invoking the checker."
  - "Keep all seven real-fixture gates unresolved and stop at Phase 22; Phase 23 remains owner-controlled."
requirements-completed: []
coverage:
  - id: D1
    description: "The immutable diagnostic assessment retains 513 metadata cases and refuses real admission with all seven gates unresolved; renamed payload and dependency mutants are refused."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_.*$': immutable evidence contract, added-payload controls and source-archive control"
        status: pass
      - kind: other
        ref: "python3 -I tests/scripts/verify-diagnostic-evidence.py --check --repo-root . --source-revision HEAD --write-evidence build/phase22/evidence.json"
        status: pass
      - kind: other
        ref: "verify-diagnostic-admission.py --self-test-controls: 12 mutation controls; --require-approved exits 2 with all seven gates"
        status: pass
  - id: D2
    description: "Synthetic tracer, current fixture/product boundaries and fixed test budgets pass; independent code and security reviews close the source findings."
    human_judgment: false
    verification:
      - kind: integration
        ref: "cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(phase22_.*|fixture_admission_(repository|controls)|fixture_product_(core|player)_controls|test_budget(_controls)?)$'"
        status: pass
      - kind: other
        ref: "22-REVIEW.md and 22-SECURITY.md: exact reviewed source 25f8966cdbb34733b7e51f58f97182caa2b9ea39; no unresolved source findings"
        status: pass
      - kind: other
        ref: "verify-summary-coverage.py for 22-01, 22-02, 22-10 and this block; D2 in 22-02 has human_judgment: false"
        status: pass
  - id: D3
    description: "The candidate boundary preserves Pending requirements, false automatic-advance flags, all seven no-go gates, and the exact owner-controlled Phase 23 route."
    human_judgment: false
    verification:
      - kind: other
        ref: "verify-diagnostic-evidence.py --check-boundary at the immutable boundary commit recorded in 22-EVIDENCE.md"
        status: pass
      - kind: other
        ref: "verify-uat-closure.py for this phase: shared closure self-test and full live-summary coverage pass"
        status: pass
duration: candidate
completed: 2026-11-03
status: candidate
plan_head_before: 7f57dcc3542fb274f74257f48c6cd9d1c7e49741
plan_head_after: 6447839b8d5e4435f209c790ae350ace4388a591
commits: 9
---

# Phase GB-22 Plan 11: Final Qualification and Boundary Summary

**Immutable admission now refuses renamed payloads and mutable Phase 20 checker/policy substitutions; the no-go stays in force while exact-head remote qualification remains outstanding.**

## Accomplishments

- Closed the renamed-payload and mutable Phase 20 dependency findings with negative controls, keeping admission bound to immutable source blobs and rejecting newly added archives or diagnostic payloads by path and content.
- Re-ran independent code and security reviews on the fixed source. Source review is clean; only the live exact-head PR qualification remains an operational gate.
- Reconciled the local evidence with the 513-case metadata inventory, seven unresolved real-fixture gates, zero admitted or executed cases, and unchanged Pending requirements.
- Prepared automated closure and a candidate Phase 22 handoff that keeps Phase 23 unstarted and owner-controlled.

## Verification

- The focused phase1 CTest selection passed 14/14 checks on source `25f8966c`; the exact final full-suite and remote results remain pending and must be recorded for the final source before Phase 22 can close.
- Immutable evidence passed on source `6447839b`: 513 cases, seven unresolved gates, admitted=0 and executed=0.
- The admission mutation suite passed 12/12 controls, including independent Phase 20 checker and policy substitutions. Real approval correctly refused with exit 2.
- The candidate boundary is point-in-time checked. Any completed Phase 22 claim remains conditional until exact-head required PR checks and merge-tree equivalence pass.

## Decisions and Limits

- DIAG-01, DIAG-02, and RIGHTS-01 remain Pending with their original definitions; RIGHTS-01 remains owned by Phase 20.
- No upstream ROM/reference payload, upstream build or program, real fixture admission, real diagnostic result, or license prohibition is claimed.
- Phase 23 — Qualified v0.4.0 Release — remains unstarted. The exact owner route is `/gsd-discuss-phase 23`; both automatic-advance flags remain false.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Reject renamed archive and diagnostic payload additions**
- **Found during:** Task 1 review of the scoped changes.
- **Issue:** The path guard did not cover `.rar`, `.zst`, `.dat`, and extensionless payload variants.
- **Fix:** Added suffix and bounded content-signature checks with negative controls for these forms and SVG/image/ROM variants.
- **Files modified:** `tests/scripts/verify-diagnostic-evidence.py`.
- **Verification:** Immutable evidence controls, focused CTest, and independent review/security audit.

**2. [Rule 2 - Security] Bind Phase 20 checker and policy to immutable source**
- **Found during:** Task 1 scoped security review.
- **Issue:** A mutable Phase 20 checker or policy could otherwise affect approval.
- **Fix:** Compare both worktree files against blobs from the selected commit before invoking the checker; add independent mutation refusals.
- **Files modified:** `tests/scripts/verify-diagnostic-admission.py`.
- **Verification:** All 12 admission controls passed, including separate checker and policy mutations.

**3. [Rule 3 - Blocking issue] Permit tests-enabled source-archive configuration while evidence stays fail-closed**
- **Found during:** Task 1 source-archive control.
- **Issue:** The default CMake testing configuration required Git identity and prevented the planned no-Git source archive check.
- **Fix:** Preserve revision-bound evidence enforcement when Git context exists and allow source-archive configuration; evidence tests still fail closed if revision identity is unavailable.
- **Files modified:** `CMakeLists.txt`, `tests/CMakeLists.txt`.
- **Verification:** Source-archive configure control and focused Phase 22 CTest.

**Total deviations:** 3 auto-fixed issues (Rules 1, 2 and 3). All fixes directly closed correctness, security, or verification blockers within the approved scope.

## Deferred Issues

- Final full-suite and exact-head remote PR qualification are still pending. If any required run, job, artifact, review, or merge-tree evidence is unavailable or does not match the final source, leave Phase 22 unclosed and record the concrete blocker.

## Next Phase Readiness

The local synthetic-plus-metadata evidence and independent source reviews are ready. Phase 22 remains conditional on the final local full suite and exact-head remote qualification. If they pass, stop at Phase 22 and hand back the owner-controlled `/gsd-discuss-phase 23` route; do not start Phase 23.
