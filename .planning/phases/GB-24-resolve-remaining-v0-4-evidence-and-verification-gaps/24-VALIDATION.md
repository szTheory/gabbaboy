---
phase: "24"
slug: "resolve-remaining-v0-4-evidence-and-verification-gaps"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-18"
---

# Phase 24 — Validation Strategy

> Updated from the D-215 validation architecture. Planning only; implementation and hosted qualification remain separately gated.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | Existing Python standard library and CMake/CTest |
| Config | Existing CMake presets and CTest registrations |
| Quick run | Syntax-only AST parse of the six affected Python checkers; useful after execution is authorized, but not behavioral proof |
| Focused run | Inspect exact registrations with `ctest --show-only=json-v1`; run existing controls only |
| Full suite | Excluded; D-103 remains a separate milestone gate |
| Runtime | Not remeasured during planning; preserve the 30-second hygiene timeout unless later measured evidence supports a same-coverage adjustment |

## Per-Task Verification Map

| Task ID | Plan | Contract | Existing control seam | Evidence and status |
|---|---|---|---|---|
| 24-01-T10-archive-path-contracts | 01 | CR-01–CR-03 are rejected for decoded/concatenated literals, local helper-parameter flow and static component/root escapes (absolute, parent traversal, unproven dynamic components or root rebinding); the broad lexical scan and exact historical JSON exception remain intact. | `no_phase_paths_controls`, `no_phase_paths`, `planning_hygiene_controls` | Add causal positives/negatives for lexical component containment in the existing self-test; pending execution. No runtime symlink containment claim/test. |
| 24-01-T11-manifest-git-context | 01 | CR-04 requires the archive pair and active Phase 24 route for current candidates; WR-01 validates exact raw pin bytes; WR-02 prevents inherited Git redirection from changing the temporary repository. | `phase22_evidence_controls`, `phase22_evidence_contract`, existing dense-input Git-context controls | Preserve full-revision historical mode and avoid fixture-bearing local execution; pending execution. |
| 24-01-T12-trust-timeout-qualification | 01 | The existing trust overlay, candidate ancestry, timeout diagnosis, and integrated focused coverage remain qualified without changing requirement or release status. | `plan_cap`, `workflow_policy_coverage_controls`, `planning_hygiene_controls`, plus the relevant controls above | Keep current test identities, 125-control floor, and 30-second bound unless measured evidence justifies a narrow equivalent adjustment; pending execution. |

The Phase 24 roadmap has no assigned requirement IDs. These checks validate the phase's evidence contract and do not promote any original v0.4 requirement. D-209 remains authoritative: seven of eight requirements are complete, FIXT-01 is Pending.

## Sampling Rate and Order

- Before each focused test, run cheap syntax, candidate identity, immutable route/archive, and direct causal checks for the changed seam.
- Before CTest, verify the full candidate and ancestry from committed objects, reject unexpected source changes, and inspect the exact configured test commands using `--show-only=json-v1`.
- Run the plan-cap check first, relevant existing focused controls next, and `planning_hygiene_controls` last. Keep fixture-bearing local execution excluded; only existing admitted fixture/game cases inside the approved protected matrix may run.
- Freeze the exact candidate SHA/tree and run one initial fresh independent exact-head review. If scoped findings/direct corrections remain, allow up to two post-correction fix-and-re-review passes, with affected local checks and a fresh review for each corrected candidate. Local diagnosis/retesting is uncapped within scope. Stop on any new out-of-scope trust/correctness issue, unavailable review or finding unresolved after those two passes. One full protected PR matrix may run only after a clean final review; any failed, skipped, stale or missing required context stops with no matrix retry.
- The CR-03 check proves lexical component containment in the finite source AST seam. Runtime filesystem symlink resolution is out of scope; add no symlink test/platform dependency and claim no symlink containment. An actual symlink-based read escape revealed in that seam stops execution as a new out-of-scope trust/correctness issue. Existing archive-blob symlink refusal controls remain part of the separate current/archive contract.
- If the exact reviewed and matrix-tested head passes every required context, merge and reconcile that same head through the existing protected PR. Phase 24 verification, Task 7, milestone audit/archive, and v0.5 remain separate.
- For CI efficiency, record run/revision identity, job and step durations, queue and dependency waits, timeout headroom, and whether package steps ran or were skipped. Use the data to recommend only safe improvements; preserve all required checks and branch protection. Do not add speculative caching/concurrency or change workflow triggers. Keep package-waiter redesign separate.
- Do not run the broad suite, Acid2 replay, prior `div_inc_timing_a` replay, excluded gbmicrotest cases, Task 7, Phase 24 verification, milestone audit/archive, or v0.5 work under this plan.

## Wave 0 Requirements

- Existing standard-library checks, CMake/CTest registrations, Git object reads, and the protected PR workflow are sufficient; add no dependency, test identity, phase, or plan.
- Preserve the one-plan limit and the exact D-215 scope. Keep execution unapproved until the updated plan passes its independent plan check and receives separate owner authorization.

## Manual-Only Verifications

None for this planning deliverable. Exact-head review and protected CI are automated qualification gates; no manual UAT is added.

## Validation Sign-Off

- [x] D-215's six finding contracts and existing control seams are mapped.
- [x] Cheap checks precede focused tests; full required hosted coverage is preserved.
- [x] Requirement, release, and milestone boundaries remain explicit.
- [ ] Updated plan and independent plan review pass.
- [ ] Authorized implementation controls and focused CTests pass.
- [ ] Clean exact-head review and one complete protected matrix pass.
