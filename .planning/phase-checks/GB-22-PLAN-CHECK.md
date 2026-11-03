# Phase 22 Plan Check — Rescope Revision 3

**Checked:** 2026-11-03  
**Phase:** 22 — Composition and Microtest Evidence  
**Plans checked:** 9  
**Status:** passed

## Verdict

The nine plans cover the Phase 22 goal and its DIAG-01/DIAG-02 requirements, and carry the cross-cutting RIGHTS-01 admission and distribution constraints. The three roadmap success criteria are backed by executable tasks, linked artifacts, and negative controls. No blocker, warning, or advisory remains in this pass.

The previous plan-check findings are addressed. Plan 22-08 now routes the complete diagnostic identity view from the trusted checkout into downloaded-product verification and covers disguised bytes and lifecycle ordering. Plan 22-09 now requires measured CI headroom and recurring automation-value assessment in `22-EVIDENCE.md`. Expected-test ownership is listed at each CTest registration boundary, with final reconciliation assigned to 22-09-T2.

## Goal and Requirement Coverage

| Requirement / invariant | Plan coverage | Result |
|---|---|---|
| DIAG-01 — reproducible font-substituted derivatives, unchanged independent references, source-mapped text mask, exact unmasked comparison, composition-only claim | 22-01-T1/T2; 22-02-T1/T2; 22-03-T1/T2; 22-04-T1/T2; 22-07; 22-08; 22-09 | Covered |
| DIAG-02 — all 513 source/ROM names and identities, per-case protocol/applicability, explicit eligibility and terminal outcomes, all eligible cases executed | 22-02-T1/T2; 22-05-T1/T2; 22-06-T1/T2; 22-07; 22-08; 22-09 | Covered |
| RIGHTS-01 — Phase 20 component-rights gate, immutable admission/notice records, source versus binary boundaries, unchanged root MIT | 22-01 through 22-09, with admission in 22-02/04/06, distribution in 22-07/08, reconciliation in 22-09 | Covered |
| Locked D-01/D-02/D-03 and deferred scope | 22-01 through 22-09 | Honored; no scope reduction or deferred idea added |

Plans separate source identity, byte identity, rights, reproducible-build status, expected-result protocol, and model applicability. The acid2 reference remains independent of GabbaBoy output, and masks are bounded to source-derived substituted text cells. The microtest accounting keeps eligibility as a predicate and executed/excluded as disjoint terminal outcomes; it retains the 480 macro cases, two separately reviewed inline verdicts, and 31 initial exclusions. Unsupported rights, oracle, build, or model facts lead to a real scope-resolution stop rather than a synthetic or partial admission claim.

## Earlier Findings Rechecked

| Previous finding | Current evidence | Result |
|---|---|---|
| Trusted downloaded core/player checks did not consume the new diagnostic identity projection (BLOCKER) | 22-08-T1 passes the complete view from the trusted repo root through `verify-workflow-policy.py` to `verify-fixture-admission.py --check-product-tree` for downloaded macOS core/player and Windows core archives. 22-08-T2 covers unrelated suffixless ROM/reference bytes, specific refusal, extraction cleanup, lifecycle ordering, source-bound workflow mutations, and control coverage. 22-09-T1 requires these controls in final evidence. | Resolved |
| Phase handoff omitted measured CI efficiency and automation value (WARNING) | 22-09-T2 requires job/step timing, queue/dependency waits, timeout headroom, recurring automation value, and a recorded evidence-backed action or no-actionable-change finding in `22-EVIDENCE.md`, while preserving required lanes and gates. | Resolved |
| `tests/expected-tests.txt` registration ownership was unclear | Registration tasks list the inventory file and add their exact registrations; 22-09-T2 performs final parity reconciliation after all additions. 22-08 extends existing registered controls and explicitly adds no new test name. | Resolved |

## Plan Structure, Dependencies, and Scope

All nine `verify.plan-structure` queries returned `valid: true`, with no errors or warnings. Each plan has two tasks, and all 18 tasks have the required files, action, verify, and done fields. The checkpoint in 22-02 is conditional on an actual unresolved gate and carries a blocking stop.

| Plan | Wave | Depends on | Tasks | `files_modified` | Structure |
|---|---:|---|---:|---:|---|
| 22-01 | 1 | — | 2 | 6 | Valid |
| 22-02 | 2 | 22-01 | 2 | 6 | Valid |
| 22-03 | 3 | 22-02 | 2 | 4 | Valid |
| 22-04 | 4 | 22-03 | 2 | 7 | Valid |
| 22-05 | 5 | 22-02, 22-04 | 2 | 6 | Valid |
| 22-06 | 6 | 22-02, 22-05 | 2 | 8 | Valid |
| 22-07 | 7 | 22-04, 22-06 | 2 | 9 | Valid |
| 22-08 | 8 | 22-07 | 2 | 4 | Valid |
| 22-09 | 9 | 22-04, 22-06, 22-07, 22-08 | 2 | 9 | Valid |

The dependency graph is acyclic and wave numbers follow the declared dependencies. Each wave has one plan; shared mutable files such as `tests/CMakeLists.txt`, `tests/expected-tests.txt`, `THIRD_PARTY_NOTICES.md`, and the admission checker are owned in ordered tasks/plans, so there is no same-wave or undeclared temporal coupling. Nine plans are within the Phase 22 cap of ten.

All estimates are below the configured 100,000-token per-plan budget: 22-01 34,000; 22-02 36,000; 22-03 30,000; 22-04 22,000; 22-05 30,000; 22-06 24,000; 22-07 32,000; 22-08 22,000; 22-09 30,000. Every estimate has `confidence: low`; the estimator reports zero calibration samples, so these figures are not calibrated. Task and file counts provide the stronger scope evidence; no plan reaches the task or file warning thresholds.

## Wiring, Rights, and Evidence Boundaries

- The source-cell mask, derivative bundle, admission manifest, comparison runner, package projection, and final evidence checker are connected by task actions and `must_haves.key_links`; the plans do not leave these artifacts isolated.
- The Phase 20 `--require-approved` gate precedes real acid2 and gbmicrotest use. The manifest and immutable admission snapshot retain rights authority; a digest or a populated record cannot clear permission.
- The package projection is checked against admitted manifests and actual installed/core/player trees. Trusted downloaded archive checks source it from the trusted checkout, then validate the bytes actually extracted. Negative controls include suffixless aliases, cleanup and pre-lifecycle ordering. Root MIT and the closed product fixture policy remain explicit.
- Exact CTest registration and execution sets are checked independently of broad regex matches. The microtest aggregator depends on all eligible case tests; missing, stale, duplicated, skipped, or unexplained outcomes cannot pass reconciliation.
- Model and claim limits are explicit: CPU-08 remains uncertain, CPU-B outcomes remain cross-model diagnostics, and no mode-3 timing, game-progress, physical CGB-E, perceptual, or broad-compatibility claim is derived from these diagnostics.
- The Architectural Responsibility Map is present and matches repository tooling, runner, and package-policy task placement. Research Open Questions are marked resolved for planning, with external rights/model/toolchain facts still gated. Plan actions align with PATTERNS.md analogs and no-analog guidance.

## Automated Validation Review

`22-VALIDATION.md` maps all 18 tasks to automated commands and negative controls. The refreshed probes were read in full: each contains 21 commands and `readError: null`. The failing-direction probe has 21 `ok` statements and zero blocker/warning; the path probe has zero blocker/warning (its recognized path forms are not applicable) and no read error. No verify command format, error-suppression, or grounded-path issue was reported. The validation file remains draft with execution rows pending, as expected before execution.

No build, project test, or implementation evidence was run or used in this planning review.

## Phase and Stage Handoff

The plan stops at Phase 22. Current planning-stage handoff is to the owner-controlled Phase 22 execution command, `/gsd-execute-phase 22`; this check does not start execution. At Phase 22 completion, 22-09-T2 records the exact subsequent route as Phase 23 — Qualified v0.4.0 Release, `/gsd-discuss-phase 23`, and requires both automatic-advance flags to remain false. That final continuation does not authorize Phase 23 work.

## Structured Issues

```yaml
issue_counts:
  blocker: 0
  warning: 0
  info: 0
  total: 0
issues: []
```

**Recommendation:** Plans verified. The owner may start Phase 22 execution with `/gsd-execute-phase 22`; stop at the Phase 22 boundary and wait for the owner's next selection.
