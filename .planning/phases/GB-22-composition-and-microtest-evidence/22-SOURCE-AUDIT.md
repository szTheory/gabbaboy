# Phase 22 revised source coverage and execution audit

The owner-approved D-141 decision on 2026-11-03 and the CONTEXT scope amendment govern this plan set. The original requirement definitions remain unchanged. This audit records planned coverage, not implemented or verified completion.

## Live plan graph and ownership

| Plan | State | Needs | Creates or closes | Wave |
|---|---|---|---|---|
| 22-01 | Complete; original PLAN/SUMMARY unchanged | Existing Phase 20 contract | Original synthetic compiled-runner tracer, source-cell mask and identity/refusal controls | 1 |
| 22-02 | Partial; existing Task 1 commits retained | 22-01, owner-approved rescope | Honest assessment summary and explicit public no-go; no repeated upstream work or human checkpoint | 2 |
| 22-10 | Planned | 22-02 metadata and public disposition | Immutable evidence checker, causal controls, CTest/inventory binding, public profile/claim reconciliation | 3 |
| 22-11 | Planned | 22-10 contract | Final local/review/security/exact-head remote qualification, shared closure and Phase 23 handoff | 4 |

All execution is sequential because the plans share documents or CTest consumers. No same-wave file ownership overlaps. Plan 22-10 owns new checker/CTest registrations and expected inventory membership; 22-11 consumes them and does not introduce more tests. Existing six Phase 22 CTests remain, with exactly two new evidence tests. The completed phase-leading tracer remains in 22-01; 22-10 leads its new end-to-end snapshot path with a tracer task.

Plans 22-03 through 22-09 retain their historical bodies with machine-readable `status: superseded`. They must not dispatch, require no SUMMARY, and do not supply live must-haves or requirement completion. Historical phase-wide output lists inside 22-01 are superseded by this audit and the live remaining plans; 22-01 itself is preserved byte-for-byte as instructed. Eleven files exist and four are live, both within the 12-plan cap.

## Multi-source coverage

| Source | Item | Current contract | Plan coverage | Status |
|---|---|---|---|---|
| GOAL | ROADMAP Phase 22 goal | Reproducible synthetic source-anchored composition plus machine-checked metadata explaining why real diagnostics remain unadmitted | 01, 02, 10, 11 | COVERED |
| GOAL | Revised criterion 1 | Compiled synthetic tracer, fixed source-cell mask, exact unmasked comparison, identity/image/mask controls | 01 retained; 10/11 recheck | COVERED |
| GOAL | Revised criterion 2 | Source-bound complete 513-name metadata inventory; every unresolved gate visible; raw approval refuses | 02, 10, 11 | COVERED |
| GOAL | Revised criterion 3 | Synthetic-only public claims, no license-prohibition inference, DIAG/RIGHTS Pending | 02, 10, 11 | COVERED |
| REQ | DIAG-01 | Original admitted derivative definition remains Pending; phase-scoped override only | 02/10/11 requirement disposition and false-completion controls | COVERED as disposition, not satisfied |
| REQ | DIAG-02 | Original admitted cohort definition remains Pending; phase-scoped override only | 02/10/11 exact roster/no-go/false-completion controls | COVERED as disposition, not satisfied |
| REQ | RIGHTS-01 | Remains Pending, single owner Phase 20; no new permission or notices | 02/10/11 invariant; not assigned as a Phase 22 completion requirement | External ownership preserved |
| CONTEXT | D-01 identity/independent expectation/claim limits | Preserve synthetic analytical expectation and upstream metadata identities; no upstream-derived fixture or reference payload | 01 retained; 02, 10, 11 | COVERED as amended |
| CONTEXT | D-01 source builds, replacement glyphs, admitted derivatives | Explicitly superseded for Phase 22 by owner CONTEXT amendment/D-141 | 03/04 retired; 02/10/11 enforce no real build/admission/result | Excluded by explicit scope amendment |
| CONTEXT | D-02 source-cell mask/exact comparison/negative controls | Preserve the existing synthetic source-cell mask, identity checks and exact unmasked comparator; no real acid2 text layout or glyph claim | 01 retained; 10/11 recheck | COVERED as amended |
| CONTEXT | D-03 full immutable roster and evidence dimensions | Exact 513 names/paths/blob identities/sizes/protocols; 480 macro + 2 inline + 31 exclusions, 482 blocked; zero admitted/executed and incomplete final accounting | 02, 10, 11 | COVERED as amended |
| CONTEXT | D-03 raw ROM SHA-256, admitted execution and per-case qualification | Not observed; seven gates remain unresolved, real use refused; no digest manufacture or partial-suite success | 02, 10, 11; 05/06 retired | Excluded execution, covered refusal |
| CONTEXT | Shared rights/root MIT/package/no-dependency constraints | No new payload, notice, package destination or install; preserve existing actual-tree controls | 02, 10, 11 | COVERED |
| CONTEXT | D-141 owner rescope | Synthetic plus metadata acceptance, no human checkpoint, original requirements Pending, future real use needs evidence plus separately selected scope | 02, 10, 11 | COVERED |
| RESEARCH | Standard stack, package legitimacy | Existing Python stdlib/Git/CMake/CTest only; no package install | 02, 10, 11 | COVERED |
| RESEARCH | Verified acid2 source/gitlink identities | Reuse committed metadata; do not repeat upstream fetch or raw-payload checks | 02, 10 | COVERED |
| RESEARCH | Roster fingerprint and protocol scan | Retain independently pinned exact projection, 480 shared/2 inline/31 non-protocol classes, not counts alone | 02, 10 | COVERED |
| RESEARCH | Separate identity/rights/build/oracle/model dimensions | Unknown SHA-256/build/model/oracle facts stay unknown; digests and public MIT text cannot grant admission | 02, 10, 11 | COVERED |
| RESEARCH | CPU-08 uncertainty versus CPU-B/CGB-E | Preserve suite-wide uncertainty and no per-case/hardware implication | 02, 10, 11 | COVERED |
| RESEARCH | Eligibility versus terminal accounting | Eligibility is a predicate; execution/exclusion terminal semantics retained; blocked candidates are not completed suite accounting | 02, 10 | COVERED |
| RESEARCH | Mask bounds, one-pixel/malformed image/identity discrimination | Existing synthetic controls remain real compiled-runner evidence within their stated limits | 01 retained; 10/11 recheck | COVERED |
| RESEARCH | Immutable records, bounded input, unsafe paths, causal negative controls | Git snapshot, bounded JSON/processes, independent projection, specific refusal reasons, CTest-wired mutants | 10, 11 | COVERED |
| RESEARCH | Component rights and source/output distribution separation | Preserve policy/notices/license, no diagnostic payload in source/product, existing actual-tree core/player/archive controls | 02, 10, 11 | COVERED |
| RESEARCH | Source-built derivatives, real source-text masks and glyph outputs | Original deliverables explicitly superseded by CONTEXT amendment/D-141; build compatibility and rights remain open | 03/04 retired; 02/10 no-go evidence | Excluded by explicit scope amendment |
| RESEARCH | Real gbmicrotest protocol runner/cohort execution | Original execution deliverables explicitly superseded; no runner/core change or real-case tests | 05/06 retired; 02/10 no-go evidence | Excluded by explicit scope amendment |
| RESEARCH | New fixture identities/notices/downloaded lifecycle wiring | No new fixture bytes require these outputs; original payload-dependent distribution plans retired | 07/08/09 retired; 10 preserves current boundary | Excluded by explicit scope amendment |
| PROJECT | Final local/review/security/exact-head remote gates | Required tests/negative controls, actual required remote lanes, same-head reviews, merge-tree identity, bounded fixes | 11 | COVERED |
| PROJECT | Automated SUMMARY/UAT closure | Required block schema, shared writer/self-test; no invented manual UAT | 02, 10, 11 | COVERED |
| PROJECT | Phase pause and immutable point-in-time route | Explicit boundary commit, later-HEAD control, both auto flags false, /gsd-discuss-phase 23 | 10, 11 | COVERED |

No currently approved source item is unplanned. The original DIAG definitions are deliberately unsatisfied, not silently rewritten. Nothing in this audit authorizes fetch/build/run/admission or treats evidence absence as a license prohibition.

## Seven unresolved gate IDs

The immutable checker must assert these exact current blockers, while preserving the two supported metadata identity gates separately:

- acid2_derivative_build_reproducibility
- acid2_component_rights_and_output_scope
- acid2_profile_applicability
- gbmicrotest_component_rights_and_output_scope
- gbmicrotest_prebuilt_rom_sha256
- gbmicrotest_case_applicability
- gbmicrotest_independent_oracle

## Discovery, sizing and verification grounding

Existing current RESEARCH/PATTERNS and repository implementations are sufficient for Level 0 internal work; no external dependency, upstream research or API selection is introduced. The architectural responsibility map keeps assessment/accounting/claims in repository test tooling and existing synthetic execution in the runner adapter; no core API change is planned.

Installed runtime identity was verified as `@opengsd/gsd-core` 1.19.0. Planning init reports standard/yolo operation, Phase 22 In Progress, existing research/context, and both auto flags false. Graphify is disabled; no graph authority is assumed. Planner skill self-load returned no configured skills. Estimate calibration has zero samples, factor 1, confidence low; estimates use that output verbatim.

Existing relevant commands and paths were inspected. The original 22-01 proof command is copied verbatim in 22-10. Existing assessment, package, source-archive, budget, summary, UAT and exact-head PR helper commands are reused. New checker paths/flags and two CTests are deliverables of 22-10 before 22-11 consumes them. There are no negative grep/count gates or ungrounded arbitrary package installs. Required raw refusal is an explicitly checked contract, not an ignored failing command.

The current assessment/controls already exist; public no-go prose currently contains obsolete scope-choice/downstream-work wording. The new evidence script and its two registrations do not yet exist, so the new contract cannot already pass at the starting tree. Boundary mode is distinct from pre-boundary mode and always consumes the explicitly selected immutable boundary commit.

## Planning-stage route

Phase 22 is not complete. Resume the partial 22-02 work with its completed commit record, then execute 22-10 and 22-11 only. The orchestrator continues `/gsd-execute-phase 22` within the approved phase; no new owner decision is needed. At the successful Phase 22 boundary, the owner controls the next route: Phase 23 — Qualified v0.4.0 Release, `/gsd-discuss-phase 23`.
