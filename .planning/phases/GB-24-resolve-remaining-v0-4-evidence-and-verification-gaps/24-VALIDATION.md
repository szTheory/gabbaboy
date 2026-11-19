---
phase: "24"
slug: "resolve-remaining-v0-4-evidence-and-verification-gaps"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-18"
---

# Phase 24 — Validation Strategy

> Updated for D-218 on 2026-11-18. This note and the current task map supersede D-217's spent correction/re-review limit while preserving every prior candidate and failure as history. D-218 covers exactly three findings from the final review of `4239a8bdb0ddd33d0904c8e05eb30bc5787302fb`: reflective mutation of the approved `git_run` binding, pattern/caller rebinding of a validated revision before Git reads, and reflective mutation of `re.compile`. The source whitelist is `tests/scripts/verify-no-phase-paths.py` and `tests/scripts/verify-planning-hygiene.py`, plus additive `24-CLOSEOUT.md` evidence.
>
> D-217's review is blocked historical evidence and its allowance is spent. D-218 is a one-time exception for T14 correction and T12 qualification, one new independent go/no-go review, and one protected PR matrix only after a clean review; no repair/re-review or matrix retry follows any blocker. Keep the same seven focused CTests (`plan_cap`, `phase22_evidence_controls`, `phase22_evidence_contract`, `no_phase_paths_controls`, `no_phase_paths`, `workflow_policy_coverage_controls`, `planning_hygiene_controls`), their existing order, timeouts and control floors. No broad local suite, fixture/ROM/Acid2 execution, Task 7, phase/milestone closure, v0.5 or worktree cleanup is authorized. Existing admitted fixture/game cases may run only inside the protected matrix under prior D-211 authority; Acid2 and excluded diagnostic cases remain unexecuted.

**Historical D-216/D-217 guidance (superseded by D-218):** Earlier review/fix caps are spent. D-218 supplies only the exact new correction and final qualification stated above; it does not reset project-wide caps.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | Existing Python standard library and CMake/CTest |
| Config | Existing CMake presets and CTest registrations |
| Quick run | Syntax-only AST parse of the two D-218 checker targets; use causal behavioral controls for the binding and revision proofs |
| Focused run | Inspect exact registrations with `ctest --show-only=json-v1`; run existing controls only |
| Full suite | Excluded; D-103 remains a separate milestone gate |
| Runtime | No new deadline is authorized; preserve the existing 30-second hygiene timeout and 125-control floor |

## Per-Task Verification Map

| Task ID | Plan | Contract | Existing control seam | Evidence and status |
|---|---|---|---|---|
| 24-01-T10-archive-path-contracts | 01 | D-215's original CR-01–CR-03 corrections and controls were locally exercised at `e1d3200`; the follow-up review found two additional linter bypasses, now assigned to T13. | `no_phase_paths_controls`, `no_phase_paths`, `planning_hygiene_controls` | Historical direct checks passed; do not replay T10 wholesale. T13 adds causal `chr()` and helper-body controls. No runtime symlink containment claim/test. |
| 24-01-T11-manifest-git-context | 01 | D-215 archive/route, raw pin and dense-input Git-context corrections were locally exercised at `e1d3200`; the follow-up review found a separate inherited-environment gap in diagnostic evidence, now assigned to T13. | `phase22_evidence_controls`, `phase22_evidence_contract`, existing dense-input Git-context controls | Historical direct checks passed; do not replay T11 wholesale. T13 adds diagnostic boundary-control isolation. No fixture-bearing local execution. |
| 24-01-T13-review-findings-path-git-census | 01 | Historical D-217 correction for earlier five findings; its local tests passed at `cbef748`, but its final review at `4239a8b` found three blockers. | Historical seven focused CTests | Preserve as history; no re-dispatch. |
| 24-01-T14-static-proof-recovery | 01 | Close only the three D-217 final-review blockers: namespace mutation of `git_run`, revision rebinding including match captures across the helper chain, and mutation of the `re.compile` proof. | Existing path/hygiene self-tests extended with causal negatives and approved runtime/revision positives | Two-file source scope, no dependencies/new CTest identity; pending D-218 execution. |
| 24-01-T12-trust-timeout-qualification | 01 | Bind the corrected immutable revision, unchanged D-209 pin and earlier trust contracts to the same seven focused CTests, one new independent go/no-go review and one protected matrix only after a clean review. | Existing seven CTests in established order; exact-head review and existing protected PR contexts | Retain identity, 125-control floor, 30-second bound and all exclusions; pending D-218 execution. |

The Phase 24 roadmap has no assigned requirement IDs. These checks validate the phase's evidence contract and do not promote any original v0.4 requirement. D-209 remains authoritative: seven of eight requirements are complete, FIXT-01 is Pending.

## Sampling Rate and Order

- Before each focused test, run cheap syntax, candidate identity, immutable route/archive, and direct causal checks for the changed seam.
- Before CTest, verify the full candidate and ancestry from committed objects, reject unexpected source changes, and inspect the exact configured test commands using `--show-only=json-v1`.
- Run the plan-cap check first, relevant existing focused controls next, and `planning_hygiene_controls` last. Keep fixture-bearing local execution excluded; only existing admitted fixture/game cases inside the approved protected matrix may run.
- D-217's scope and review allowance are spent; its final review at `4239a8b` is blocked. D-218 allows one exact correction task (T14), then T12 qualification and one new exact-head go/no-go review. A blocker or unavailable review stops with no additional correction/re-review. Only a clean review permits the one protected matrix; a failed, skipped, stale or missing required context stops without matrix retry.
- The CR-03 check proves lexical component containment in the finite source AST seam. Runtime filesystem symlink resolution is out of scope; add no symlink test/platform dependency and claim no symlink containment. An actual symlink-based read escape revealed in that seam stops execution as a new out-of-scope trust/correctness issue. Existing archive-blob symlink refusal controls remain part of the separate current/archive contract.
- If the exact reviewed and matrix-tested head passes every required context, merge and reconcile that same head through the existing protected PR. Phase 24 verification, Task 7, milestone audit/archive, and v0.5 remain separate.
- For CI efficiency, record run/revision identity, job and step durations, queue and dependency waits, timeout headroom, and whether package steps ran or were skipped. Use the data to recommend only safe improvements; preserve all required checks and branch protection. Do not add speculative caching/concurrency or change workflow triggers. Keep package-waiter redesign separate.
- Do not run the broad suite, Acid2 replay, prior `div_inc_timing_a` replay, excluded gbmicrotest cases, Task 7, Phase 24 verification, milestone audit/archive, or v0.5 work under this plan.

## Wave 0 Requirements

- Existing standard-library checks, CMake/CTest registrations, Git object reads, and the protected PR workflow are sufficient; add no dependency, test identity, phase, or plan.
- Preserve the one-plan limit and D-218's three exact findings across the two named checker files. D-217 and earlier correction/review limits are spent history; the owner authorizes only the new T14/T12 route and one protected matrix after a clean review. Keep phase/milestone closure, Task 7, D-103 and worktree cleanup separate.

## Manual-Only Verifications

None for this planning deliverable. Exact-head review and protected CI are automated qualification gates; no manual UAT is added.

## Validation Sign-Off

- [x] Historical: D-215's six finding contracts and D-216's four additional findings mapped to existing control seams; T10/T11 are recorded as historical direct passes.
- [x] D-218's three final D-217 findings map to the two approved checker files and existing control seams; the one-time exception and hard stop after final review are explicit.
- [x] Cheap checks precede focused tests; full required hosted coverage is preserved.
- [x] Requirement, release, and milestone boundaries remain explicit.
- [x] Historical: updated sole plan and independent static plan review passed for the D-216 active route and qualification controls.
- [x] D-218 revised sole plan and reconciled validation passed independent static plan checking with no blockers, warnings, or advisories.
- [ ] D-218 correction controls and the seven focused CTests pass at the corrected immutable candidate.
- [ ] One new independent go/no-go review is clean and the one protected matrix passes for the identical head; merge only through existing protection.
