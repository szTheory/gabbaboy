---
phase: "24"
slug: "resolve-remaining-v0-4-evidence-and-verification-gaps"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-17"
---

# Phase 24 — Validation Strategy

> D-213 planning contract, now authorized for execution by D-214. The revised plan passed independent static plan review; implementation checks have not run yet. The D-209 v0.4 closeout and archived requirement dispositions remain unchanged.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Existing Python standard-library checks and CMake/CTest |
| **Config file** | `CMakePresets.json`, `tests/cmake/hygiene.cmake`, and existing lane registrations |
| **Quick run command** | `python3 -I -c 'import ast,pathlib; paths=("tests/scripts/verify-dense-input.py","tests/scripts/verify-diagnostic-evidence.py","tests/scripts/verify-planning-hygiene.py","tests/scripts/verify-state-forks.py","tests/scripts/verify-no-phase-paths.py","tests/scripts/verify-workflow-policy-coverage.py"); [ast.parse(pathlib.Path(p).read_text(encoding="utf-8"), filename=p) for p in paths]'` — run after the D-214-authorized planning-boundary preflight; this checks syntax and file presence, not behavior. |
| **Focused CTest command** | After cheap checks and the immutable candidate preflight, inspect exact existing CTest names/commands with `--show-only=json-v1`; run only the plan's focused controls, with `plan_cap` first and `planning_hygiene_controls` last. |
| **Full suite command** | Not in this recovery scope. D-103 remains a separate milestone gate. |
| **Estimated runtime** | Not remeasured in planning. Preserve the 30-second hygiene timeout unless measured stage/load evidence supports a narrow same-coverage change. |

## Per-Task Verification Map

| Task ID | Plan | Wave | Contract | Threat Ref | Secure Behavior | Test Type | Automated Command / Boundary | File Exists | Status |
|---------|------|------|----------|------------|-----------------|-----------|-----------------------------|-------------|--------|
| 24-01-T10-archive-path-contracts | 01 | 1 | Exact D-209 archive facts coexist with the committed current Phase 24 route; the path linter distinguishes finite immutable/self-test uses from live readers and separately allows exactly two historical JSON provenance values. | T-24-13 | Keep the general scan and must-scan controls; reject unclassified literals, same-count live-reader substitutions, changed immutable inputs and extra historical-path uses. | integration/control | Existing `phase22_evidence_controls`, `no_phase_paths_controls`, `no_phase_paths`, and `planning_hygiene_controls`; run only after cheap path and boundary checks establish no ROM execution. | Existing | ⬜ pending |
| 24-01-T11-manifest-git-context | 01 | 1 | The candidate Git object resolves full active fixture pins/ancestry, while the immutable state-fork inventory is the exact active/excluded union and never expands diagnostic ROMs. | T-24-14 | Keep production admission fail-closed; exclude Acid2, the prior `div_inc_timing_a` case and all 512 other gbmicrotest cases. | integration/control | Non-executing Git-context and inventory controls first; fixture-bearing dense-input/state-fork behavior only inside the separately authorized protected PR matrix. | Existing harness and matrix lane | ⬜ pending |
| 24-01-T12-trust-timeout-qualification | 01 | 1 | The v0.4.0 tagged checker remains independently verified, only the exact D-209 notice delta is modeled, and the hygiene timeout is diagnosed before any budget change. | T-24-15 | Reject unrelated checker/rights drift; retain all unique cases, current CTest identities and the 125-control floor. | integration/control | Existing `plan_cap`, `phase22_evidence_controls`, `phase22_evidence_contract`, `no_phase_paths_controls`, `no_phase_paths`, `workflow_policy_coverage_controls`, and `planning_hygiene_controls`, selected exactly as the final plan prescribes. | Existing | ⬜ pending |

The task identifiers match the sole Phase 24 plan. These are conditional implementation checks, not results. No product test, configure/build, CTest, CI, or ROM execution ran during planning.

## Sampling Rate

- **Planning:** static plan structure, frontmatter, verify-command path/failure-direction probes, and independent plan review only.
- **Before implementation tests:** D-214 authorizes one local unpushed documentation-only boundary commit from the plan's exact whitelist; inspect its full diff, then check route/archive identity and implementation ancestry before configure or longer work.
- **Local convergence:** run cheap syntax, identity, path and non-executing inventory controls first. When an in-scope check fails, preserve its cause, diagnose it, fix within T10–T12, and rerun the relevant controls until they pass. There is no numeric retry allowance for this scoped local loop. Stop for owner discussion if the cause is outside scope or cannot be safely resolved within it.
- **Focused CTest:** configure only after the immutable preflight. Inspect show-only JSON, then run `plan_cap`, the necessary existing focused contract controls, and `planning_hygiene_controls` last. Preserve the existing coverage, 30-second bound unless measured evidence proves a narrow same-coverage adjustment necessary, and 125-control floor. Do not run the broad suite.
- **Remote qualification:** after local convergence, verify the original D-211 runs remain terminal, freeze the exact final candidate, obtain at most one independent review, then spend at most one protected PR matrix. A review finding or any failed/missing/skipped/stale required context stops further qualification without new owner scope. Keep all required jobs and branch protection.
- **CI efficiency:** collect measured durations and critical-path waits at the CI/release boundary. The three long exact-head preview waits are a separate follow-up; do not reduce required coverage, add unmeasured caching/concurrency, or change triggers to `workflow_run`. Apply `.planning/context/WORKFLOW.md#cicd-efficiency`.
- **Excluded:** broad local suite; Acid2 replay; prior `div_inc_timing_a` replay; any excluded gbmicrotest case; local fixture-bearing matrix; new fixtures/dependencies/CTest identities; Task 7; Phase 24 or milestone verification/archive; requirement/status changes; release changes; merge or worktree cleanup.

## Wave 0 Requirements

- Existing Python, CMake, CTest, Git snapshot, and protected-PR seams are sufficient; no dependency is added.
- Keep one existing Phase 24 plan and at most 40 v0.4 plans; no phase or test identity is added.
- The D-214-authorized planning-boundary commit is local and unpushed, includes only the reviewed planning whitelist, and excludes the three dirty T10 source scripts, `state.json`, `milestone.lock`, and unrelated changes.
- Confirm all path/archive/route assertions against committed objects; working-tree text cannot substitute for immutable evidence.

## Manual-Only Verifications

None for this planning deliverable. Do not add manual UAT to satisfy a template. Exact-head review and protected CI are later independent gates under D-214, only after local convergence.

## Validation Sign-Off

- [x] The sole plan has three ordered tasks and each verification command states a failure condition.
- [x] Static frontmatter/plan-structure validation and the independent plan check passed.
- [x] The plan preserves D-209 requirement statuses, ownership, accepted gaps, and the Acid2 failure/exclusion.
- [x] Local in-scope convergence is distinct from the one-review/one-matrix final qualification limit.
- [ ] Implementation controls and focused CTests are pending; the D-214-authorized review and protected matrix remain gated on their successful local convergence.
