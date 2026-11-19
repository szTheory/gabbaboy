---
phase: "24"
slug: "resolve-remaining-v0-4-evidence-and-verification-gaps"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-18"
---

# Phase 24 — Validation Strategy

> Updated for D-217 on 2026-11-18. This note and the current task map supersede D-216's earlier scope and pass-count instructions; prior results remain historical evidence. The owner authorizes the five exact findings from the review of `5652e488f7940e00b2b00893cd5dbbea8d620fc8`: runtime adapter rebinding, changed/transformed validated revisions, replacement-ref object redirection, alternate-index scan suppression, and conflicting inventory modes. The source whitelist is `tests/scripts/verify-no-phase-paths.py`, `tests/scripts/verify-planning-hygiene.py`, `tests/scripts/verify-dense-input.py`, `tests/scripts/verify-diagnostic-evidence.py`, `tests/scripts/verify-state-forks.py`, and `tests/scripts/verify-workflow-policy-coverage.py`, plus additive `24-CLOSEOUT.md` evidence.
>
> The initial D-216 review and its first correction/re-review pass are spent. T13 followed by T12 uses the one remaining second/final correction/re-review pass; D-217 adds no review, matrix or retry. Only a clean final review permits the already-authorized single protected PR matrix and conditional protected merge of its identical passing head. Keep the same seven focused CTests (`plan_cap`, `phase22_evidence_controls`, `phase22_evidence_contract`, `no_phase_paths_controls`, `no_phase_paths`, `workflow_policy_coverage_controls`, `planning_hygiene_controls`), their existing timeouts and control floors. No broad local suite, fixture/ROM/Acid2 execution, Task 7, phase/milestone closure, v0.5 or worktree cleanup is authorized. Existing admitted fixture/game cases remain permitted only inside that protected matrix under D-211; Acid2 and excluded diagnostic cases remain unexecuted.

**Historical D-216 guidance (superseded by D-217):** D-216 originally authorized four exact corrections and focused local execution, with hosted qualification gated by a clean review and one protected matrix. Its initial review and first correction/re-review have now occurred; this historical statement supplies no renewed pass allowance.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | Existing Python standard library and CMake/CTest |
| Config | Existing CMake presets and CTest registrations |
| Quick run | Syntax-only AST parse of the six D-217 correction targets; use behavioral controls for proof |
| Focused run | Inspect exact registrations with `ctest --show-only=json-v1`; run existing controls only |
| Full suite | Excluded; D-103 remains a separate milestone gate |
| Runtime | Not remeasured during D-217 planning; preserve the existing 30-second hygiene timeout and 125-control floor; no deadline increase is authorized |

## Per-Task Verification Map

| Task ID | Plan | Contract | Existing control seam | Evidence and status |
|---|---|---|---|---|
| 24-01-T10-archive-path-contracts | 01 | D-215's original CR-01–CR-03 corrections and controls were locally exercised at `e1d3200`; the follow-up review found two additional linter bypasses, now assigned to T13. | `no_phase_paths_controls`, `no_phase_paths`, `planning_hygiene_controls` | Historical direct checks passed; do not replay T10 wholesale. T13 adds causal `chr()` and helper-body controls. No runtime symlink containment claim/test. |
| 24-01-T11-manifest-git-context | 01 | D-215 archive/route, raw pin and dense-input Git-context corrections were locally exercised at `e1d3200`; the follow-up review found a separate inherited-environment gap in diagnostic evidence, now assigned to T13. | `phase22_evidence_controls`, `phase22_evidence_contract`, existing dense-input Git-context controls | Historical direct checks passed; do not replay T11 wholesale. T13 adds diagnostic boundary-control isolation. No fixture-bearing local execution. |
| 24-01-T13-review-findings-path-git-census | 01 | Preserve earlier corrections; prove runtime adapter binding and unchanged validated full revisions, disable replacement refs and isolate Git selectors across the six approved checkers, preserve complete tracked inventory despite an alternate index, and refuse conflicting inventory modes/inputs. | Existing path, hygiene and workflow-policy self-tests; diagnostic `--self-test-controls`; dense-input `--check-git-context`; state-fork `--inventory-controls` | Add the five D-217 finding controls through existing seams; retain actual original-object/selector/census positives and causal negatives, unexecuted synthetic manifests and unchanged real inventory; pending D-217 execution. |
| 24-01-T12-trust-timeout-qualification | 01 | Bind all D-217 causal controls, raw pins/ancestry, exact 153-case census/exclusions, trust overlay and seven focused tests to the corrected immutable source revision; then use the remaining final re-review and existing protected matrix/conditional merge gates. | `verify-dense-input.py --check-git-context`, state-fork `--inventory-controls`, then the same seven CTests, including actual new hygiene/workflow-policy controls | Keep identities, 125-control floor and 30-second bound; D-216 candidate passes remain point-in-time history and do not qualify the D-217 candidate; pending execution. |

The Phase 24 roadmap has no assigned requirement IDs. These checks validate the phase's evidence contract and do not promote any original v0.4 requirement. D-209 remains authoritative: seven of eight requirements are complete, FIXT-01 is Pending.

## Sampling Rate and Order

- Before each focused test, run cheap syntax, candidate identity, immutable route/archive, and direct causal checks for the changed seam.
- Before CTest, verify the full candidate and ancestry from committed objects, reject unexpected source changes, and inspect the exact configured test commands using `--show-only=json-v1`.
- Run the plan-cap check first, relevant existing focused controls next, and `planning_hygiene_controls` last. Keep fixture-bearing local execution excluded; only existing admitted fixture/game cases inside the approved protected matrix may run.
- D-217 authorizes only the remaining T13 correction and T12 qualification. The initial D-216 review and first correction/re-review are spent; after in-scope local checks converge, freeze the candidate SHA/tree and use the one remaining second/final correction/re-review pass on the cumulative correction. Local diagnosis and directly relevant retests remain part of this pass. Stop for any new out-of-scope trust/correctness issue, unavailable review or unresolved finding at that final re-review; no further correction/re-review is authorized. The already-authorized single protected PR matrix may run only after a clean final review; any failed, skipped, stale or missing required context stops with no matrix retry.
- Historical D-216 pass accounting: its original wording permitted up to two post-correction fix-and-re-review passes after the initial review. That original allocation is retained as history only; one pass has been consumed and D-217 permits only the one remaining pass stated above.
- The CR-03 check proves lexical component containment in the finite source AST seam. Runtime filesystem symlink resolution is out of scope; add no symlink test/platform dependency and claim no symlink containment. An actual symlink-based read escape revealed in that seam stops execution as a new out-of-scope trust/correctness issue. Existing archive-blob symlink refusal controls remain part of the separate current/archive contract.
- If the exact reviewed and matrix-tested head passes every required context, merge and reconcile that same head through the existing protected PR. Phase 24 verification, Task 7, milestone audit/archive, and v0.5 remain separate.
- For CI efficiency, record run/revision identity, job and step durations, queue and dependency waits, timeout headroom, and whether package steps ran or were skipped. Use the data to recommend only safe improvements; preserve all required checks and branch protection. Do not add speculative caching/concurrency or change workflow triggers. Keep package-waiter redesign separate.
- Do not run the broad suite, Acid2 replay, prior `div_inc_timing_a` replay, excluded gbmicrotest cases, Task 7, Phase 24 verification, milestone audit/archive, or v0.5 work under this plan.

## Wave 0 Requirements

- Existing standard-library checks, CMake/CTest registrations, Git object reads, and the protected PR workflow are sufficient; add no dependency, test identity, phase, or plan.
- Preserve the one-plan limit and D-217's five exact findings across the six named checker files; the owner has authorized this extension within the one remaining correction/re-review pass. D-216's earlier exact four-finding scope is historical and superseded for this correction. Keep phase/milestone closure, Task 7, D-103 and worktree cleanup separate.

## Manual-Only Verifications

None for this planning deliverable. Exact-head review and protected CI are automated qualification gates; no manual UAT is added.

## Validation Sign-Off

- [x] Historical: D-215's six finding contracts and D-216's four additional findings mapped to existing control seams; T10/T11 are recorded as historical direct passes.
- [x] D-217's five exact findings map to the six approved checker files and existing control seams, using the one remaining correction/re-review pass without a budget reset.
- [x] Cheap checks precede focused tests; full required hosted coverage is preserved.
- [x] Requirement, release, and milestone boundaries remain explicit.
- [x] Historical: updated sole plan and independent static plan review passed for the D-216 active route and qualification controls.
- [ ] D-217 revised sole plan and reconciled validation receive a clean independent static plan check.
- [ ] D-217 authorized implementation controls and focused CTests pass at the corrected immutable candidate.
- [ ] The remaining final re-review and existing single complete protected matrix pass for the identical head.
