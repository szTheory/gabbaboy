---
phase: "24"
slug: "resolve-remaining-v0-4-evidence-and-verification-gaps"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-18"
---

# Phase 24 — Validation Strategy

> Updated for D-216. The owner has authorized the four exact corrections and focused local execution; hosted qualification remains gated by a clean review and the one protected matrix.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | Existing Python standard library and CMake/CTest |
| Config | Existing CMake presets and CTest registrations |
| Quick run | Syntax-only AST parse of the three D-216 correction targets; use behavioral controls for proof |
| Focused run | Inspect exact registrations with `ctest --show-only=json-v1`; run existing controls only |
| Full suite | Excluded; D-103 remains a separate milestone gate |
| Runtime | Not remeasured during planning; preserve the 30-second hygiene timeout unless later measured evidence supports a same-coverage adjustment |

## Per-Task Verification Map

| Task ID | Plan | Contract | Existing control seam | Evidence and status |
|---|---|---|---|---|
| 24-01-T10-archive-path-contracts | 01 | D-215's original CR-01–CR-03 corrections and controls were locally exercised at `e1d3200`; the follow-up review found two additional linter bypasses, now assigned to T13. | `no_phase_paths_controls`, `no_phase_paths`, `planning_hygiene_controls` | Historical direct checks passed; do not replay T10 wholesale. T13 adds causal `chr()` and helper-body controls. No runtime symlink containment claim/test. |
| 24-01-T11-manifest-git-context | 01 | D-215 archive/route, raw pin and dense-input Git-context corrections were locally exercised at `e1d3200`; the follow-up review found a separate inherited-environment gap in diagnostic evidence, now assigned to T13. | `phase22_evidence_controls`, `phase22_evidence_contract`, existing dense-input Git-context controls | Historical direct checks passed; do not replay T11 wholesale. T13 adds diagnostic boundary-control isolation. No fixture-bearing local execution. |
| 24-01-T13-review-findings-path-git-census | 01 | Decode only bounded literal `chr()` calls; inspect the actual `git_run` body; isolate diagnostic Git-only children; use NUL-delimited raw tree paths and strict manifest decoding. | Existing `no_phase_paths_controls` / `no_phase_paths` self-tests; diagnostic `--self-test-controls`; state-fork `--inventory-controls` | Add causal controls through existing seams; keep synthetic manifests unexecuted and real inventory unchanged; pending execution. |
| 24-01-T12-trust-timeout-qualification | 01 | The raw-pin/candidate-Git check, exact 153-case census, trust overlay, ancestry, timeout diagnosis and integrated focused coverage remain qualified at the same D-216 source revision without changing requirement or release status. | `verify-dense-input.py --check-git-context`, state-fork `--inventory-controls`, then the seven existing CTests | Keep identities, 125-control floor and 30-second bound; pending execution. |

The Phase 24 roadmap has no assigned requirement IDs. These checks validate the phase's evidence contract and do not promote any original v0.4 requirement. D-209 remains authoritative: seven of eight requirements are complete, FIXT-01 is Pending.

## Sampling Rate and Order

- Before each focused test, run cheap syntax, candidate identity, immutable route/archive, and direct causal checks for the changed seam.
- Before CTest, verify the full candidate and ancestry from committed objects, reject unexpected source changes, and inspect the exact configured test commands using `--show-only=json-v1`.
- Run the plan-cap check first, relevant existing focused controls next, and `planning_hygiene_controls` last. Keep fixture-bearing local execution excluded; only existing admitted fixture/game cases inside the approved protected matrix may run.
- D-216 authorizes T13 and T12. After local checks converge, freeze the exact candidate SHA/tree and run one fresh independent exact-head review of the cumulative correction. If in-scope findings remain, allow up to two post-correction fix-and-re-review passes, with affected local checks and a fresh review for each changed candidate. Local diagnosis/retesting is uncapped within scope. Stop on any new out-of-scope trust/correctness issue, unavailable review or finding unresolved after those two passes. One full protected PR matrix may run only after a clean final review; any failed, skipped, stale or missing required context stops with no matrix retry.
- The CR-03 check proves lexical component containment in the finite source AST seam. Runtime filesystem symlink resolution is out of scope; add no symlink test/platform dependency and claim no symlink containment. An actual symlink-based read escape revealed in that seam stops execution as a new out-of-scope trust/correctness issue. Existing archive-blob symlink refusal controls remain part of the separate current/archive contract.
- If the exact reviewed and matrix-tested head passes every required context, merge and reconcile that same head through the existing protected PR. Phase 24 verification, Task 7, milestone audit/archive, and v0.5 remain separate.
- For CI efficiency, record run/revision identity, job and step durations, queue and dependency waits, timeout headroom, and whether package steps ran or were skipped. Use the data to recommend only safe improvements; preserve all required checks and branch protection. Do not add speculative caching/concurrency or change workflow triggers. Keep package-waiter redesign separate.
- Do not run the broad suite, Acid2 replay, prior `div_inc_timing_a` replay, excluded gbmicrotest cases, Task 7, Phase 24 verification, milestone audit/archive, or v0.5 work under this plan.

## Wave 0 Requirements

- Existing standard-library checks, CMake/CTest registrations, Git object reads, and the protected PR workflow are sufficient; add no dependency, test identity, phase, or plan.
- Preserve the one-plan limit and D-216's exact four-finding scope; the owner has authorized execution. Keep phase/milestone closure, Task 7, D-103 and worktree cleanup separate.

## Manual-Only Verifications

None for this planning deliverable. Exact-head review and protected CI are automated qualification gates; no manual UAT is added.

## Validation Sign-Off

- [x] D-215's six finding contracts and D-216's four additional findings map to existing control seams; T10/T11 are recorded as historical direct passes.
- [x] Cheap checks precede focused tests; full required hosted coverage is preserved.
- [x] Requirement, release, and milestone boundaries remain explicit.
- [x] Updated sole plan and independent static plan review pass for the D-216 active route and qualification controls.
- [ ] Authorized implementation controls and focused CTests pass.
- [ ] Clean exact-head review and one complete protected matrix pass.
