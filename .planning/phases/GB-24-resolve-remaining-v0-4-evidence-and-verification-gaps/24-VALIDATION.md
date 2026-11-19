---
phase: "24"
slug: "resolve-remaining-v0-4-evidence-and-verification-gaps"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-18"
---

# Phase 24 — Validation Strategy

> Updated for D-219 on 2026-11-19. D-218's seven focused CTests passed at source candidate `0b4387091b5148b35af420daf3b6743aa27d8fbb`; frozen reviewed head `ba5afae5cb5c53a04c859fa9e94c3b422d995ad6` returned NO-GO for runtime-binding and reflective archive-pin proof gaps. No push, protected matrix or merge followed. D-219 integrates those Python proof gaps with cross-checker Git selection and complete state-fork inventory CLI exclusivity. Source scope is only `verify-dense-input.py`, `verify-diagnostic-evidence.py`, `verify-no-phase-paths.py`, `verify-planning-hygiene.py`, `verify-state-forks.py`, and `verify-workflow-policy-coverage.py` under `tests/scripts/`, plus additive `24-CLOSEOUT.md` evidence.
>
> D-219 allows at most two scoped correction/review passes total after D-218 NO-GO: the first corrected-candidate review is pass one, and one in-scope correction/fresh review may be pass two. Local diagnosis and targeted retests may converge before review. A clean final review gates the single protected matrix; any failed/skipped/stale/missing required context ends that route without retry. Keep the same seven focused CTests (`plan_cap`, `phase22_evidence_controls`, `phase22_evidence_contract`, `no_phase_paths_controls`, `no_phase_paths`, `workflow_policy_coverage_controls`, `planning_hygiene_controls`), order, timeouts and control floors. No broad local suite, local ROM/Acid2 replay, Task 7, phase/milestone closure, v0.5 or cleanup is included. Only already-admitted fixture/game cases within the protected matrix may run under prior D-211 authority; both diagnostic manifests remain excluded.

**Historical guidance:** D-216/D-217/D-218 candidates, local passes and failed reviews stay candidate-specific history. Their allowances are spent. D-219 supplies only the scope/limits above and does not reset project-wide caps or add a plan; the total remains 40.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | Existing Python standard library and CMake/CTest |
| Config | Existing CMake presets and CTest registrations |
| Quick run | Syntax-only AST parsing of scoped checker targets, immutable identity/scope checks, then existing source-only/Git-context/inventory controls |
| Focused run | Inspect exact registrations with `ctest --show-only=json-v1`; run existing controls only |
| Full suite | Excluded; D-103 remains a separate milestone gate |
| Runtime | No new deadline is authorized; preserve the existing 30-second hygiene timeout and 125-control floor |

## Per-Task Verification Map

| Task ID | Plan | Contract | Existing control seam | Evidence and status |
|---|---|---|---|---|
| 24-01-T10-archive-path-contracts | 01 | D-215's original CR-01–CR-03 corrections and controls were locally exercised at `e1d3200`; the follow-up review found two additional linter bypasses, now assigned to T13. | `no_phase_paths_controls`, `no_phase_paths`, `planning_hygiene_controls` | Historical direct checks passed; do not replay T10 wholesale. T13 adds causal `chr()` and helper-body controls. No runtime symlink containment claim/test. |
| 24-01-T11-manifest-git-context | 01 | D-215 archive/route, raw pin and dense-input Git-context corrections were locally exercised at `e1d3200`; the follow-up review found a separate inherited-environment gap in diagnostic evidence, now assigned to T13. | `phase22_evidence_controls`, `phase22_evidence_contract`, existing dense-input Git-context controls | Historical direct checks passed; do not replay T11 wholesale. T13 adds diagnostic boundary-control isolation. No fixture-bearing local execution. |
| 24-01-T13-review-findings-path-git-census | 01 | Historical D-217 correction for earlier five findings; its local tests passed at `cbef748`, but its final review at `4239a8b` found three blockers. | Historical seven focused CTests | Preserve as history; no re-dispatch. |
| 24-01-T14-static-proof-recovery / T12 qualification | 01 | Historical D-218 two-checker correction and seven focused local passes; frozen review found two critical gaps. | Historical seven focused CTests and exact-head NO-GO | Preserve source `0b438709` and reviewed head `ba5afae5`; no re-dispatch or renewed authority. |
| 24-01-T15-runtime-archive-proof | 01 | Closed AST proof for aliased imports, function `__globals__`, reflective proof-sensitive globals including exact D-209 pin; finite revision binders/callers and pre-read full-SHA guard; isolate both proof-checker Git adapters. | Existing path/hygiene source-only controls and original-object/selector tests | Pending D-219 execution; static mutants are parsed, never executed. T-24-30/T-24-31 plus retained T-24-26–28 contracts. |
| 24-01-T16-git-inventory-boundary | 01 | Audit remaining four Git adapters for replacements and selector environments; per-adapter original-byte/untouched-decoy proof; inventory production CLI rejects seven operation and ten input classes before effects. | Existing dense-input Git-context, diagnostic/workflow self-test, state-fork inventory/CLI controls | Pending D-219 execution; exact 153-case census/exclusions and configure/build/runner=0 in direct controls. T-24-31/T-24-32. |
| 24-01-T17-d219-qualification | 01 | Bind integrated immutable candidate to all seven focused CTests, at most two scoped correction/review passes total, one protected matrix after clean final review and conditional identical-head merge. | Existing CTest registrations and protected PR contexts | Pending D-219 execution; all deadlines/floors unchanged. Evidence before every freeze; post-freeze receipts outside candidate. T-24-33. |

The Phase 24 roadmap has no assigned requirement IDs. These checks validate the phase's evidence contract and do not promote any original v0.4 requirement. D-209 remains authoritative: seven of eight requirements are complete, FIXT-01 is Pending.

## Sampling Rate and Order

- Before each focused test, run cheap syntax, candidate identity, immutable route/archive, and direct causal checks for the changed seam.
- Before CTest, verify the full candidate and ancestry from committed objects, reject unexpected source changes, and inspect the exact configured test commands using `--show-only=json-v1`.
- Run the plan-cap check first, relevant existing focused controls next, and `planning_hygiene_controls` last. Keep fixture-bearing local execution excluded; only existing admitted fixture/game cases inside the approved protected matrix may run.
- T15 then T16 then T17 are sequential continuation slices in one existing plan. T15 touches two proof checkers; T16 touches the other four. At T17, inspect the seven configured commands and retain their existing registration order, with plan_cap first and planning_hygiene_controls last.
- D-218's review is NO-GO history. D-219 permits first corrected review as pass one and one in-scope correction/requalification/fresh review as pass two. An unavailable review, new out-of-scope issue or unresolved correctness/security blocker after pass two stops. A clean pass-one review needs no second pass. Only a clean final review permits the one protected matrix; any failed/skipped/stale/missing required context stops without matrix retry.
- The CR-03 check proves lexical component containment in the finite source AST seam. Runtime filesystem symlink resolution is out of scope; add no symlink test/platform dependency and claim no symlink containment. An actual symlink-based read escape revealed in that seam stops execution as a new out-of-scope trust/correctness issue. Existing archive-blob symlink refusal controls remain part of the separate current/archive contract.
- If the exact reviewed and matrix-tested head passes every required context, merge and reconcile that same head through the existing protected PR. Phase 24 verification, Task 7, milestone audit/archive, and v0.5 remain separate.
- For CI efficiency, record run/revision identity, job and step durations, queue and dependency waits, timeout headroom, and whether package steps ran or were skipped. Use the data to recommend only safe improvements; preserve all required checks and branch protection. Do not add speculative caching/concurrency or change workflow triggers. Keep package-waiter redesign separate.
- Do not run the broad suite, Acid2 replay, prior `div_inc_timing_a` replay, excluded gbmicrotest cases, Task 7, Phase 24 verification, milestone audit/archive, or v0.5 work under this plan.

## Wave 0 Requirements

- Existing standard-library checks, CMake/CTest registrations, Git object reads, and the protected PR workflow are sufficient; add no dependency, test identity, phase, or plan.
- Preserve the one-plan/40-plan limits and D-219's six-file source whitelist. No new CTest scaffold is required: extend causal controls in current seams, prove exact positives and refuse unsupported proof shapes. All new D-219 mitigations remain pending until execution evidence exists. Keep Task 7, D-103, phase/milestone closure and worktree cleanup separate.

## Manual-Only Verifications

None for this planning deliverable. Exact-head review and protected CI are automated qualification gates; no manual UAT is added.

## Validation Sign-Off

- [x] Historical: D-215's six finding contracts and D-216's four additional findings mapped to existing control seams; T10/T11 are recorded as historical direct passes.
- [x] Historical D-218 findings, local passes and NO-GO map to the frozen candidate; its authority is not reused.
- [x] Cheap checks precede focused tests; full required hosted coverage is preserved.
- [x] Requirement, release, and milestone boundaries remain explicit.
- [x] Historical: updated sole plan and independent static plan review passed for the D-216 active route and qualification controls.
- [x] D-218 revised sole plan and reconciled validation passed independent static plan checking with no blockers, warnings, or advisories.
- [x] D-219 binding/archive-pin/Git/CLI contracts map to T15/T16/T17 and existing causal control seams; the two-pass total and single-matrix stop conditions are explicit.
- [x] D-219 revised sole plan and reconciled validation passed independent static plan checking with no blockers, warnings, or advisories; the documentation-only boundary is committed.
- [ ] D-219 correction controls and all seven focused CTests pass at the integrated immutable candidate.
- [ ] Final independent review is clean within two passes total and the one protected matrix passes for the identical head; merge only through existing protection.
