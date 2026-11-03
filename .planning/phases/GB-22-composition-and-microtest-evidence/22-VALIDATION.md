---
phase: "22"
slug: "composition-and-microtest-evidence"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-02"
---

# Phase 22 — Validation Strategy

> Feedback contract for controlled acid2 composition evidence and the source-bound gbmicrotest cohort. Fixture identity, rights, model applicability, and emulator accuracy are separate claims.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | CMake/CTest with Python standard-library checkers. |
| **Config file** | `CMakePresets.json` (`phase1`); test registration in `tests/CMakeLists.txt`. |
| **Quick run command** | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_'` after configure/build. |
| **Full suite command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`. |
| **Feedback target** | Keep new synthetic controls bounded; measure actual runtime during execution and retain existing test budgets. |

---

## Sampling Rate

- **After each task commit:** Run the smallest focused CTest or standard-library contract check for the changed behavior.
- **After each plan wave:** Run the combined acid2, cohort-accounting, rights, and package-exclusion checks affected by that wave.
- **Before `$gsd-verify-work`:** Run the configured full preset command once at the final implementation head and retain exact-head evidence.
- **Feedback target:** Keep focused controls under the existing 60-second CTest ceiling; record measured duration instead of raising budgets to fit.

---

## Per-Task Verification Map

Nine plans contain eighteen tasks. Commands run from the checkout root. Test names below are implementation targets, not claims that tests already exist or passed. Every new checker has an automated negative control; unresolved admission remains a real stop. Every task's automated command is followed by its observable failing direction in the PLAN file.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 22-01-T1 | 22-01 | 1 | DIAG-01, RIGHTS-01 | T-22-01, T-22-02, T-22-03, T-22-19 | Original synthetic ROM traverses real Phase 20 CLI, compiled runner, independent masked expectation, receipt and product scanner. | e2e | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_acid2_tracer$'` | New source/check; runner/admission/scanner exist | pending |
| 22-01-T2 | 22-01 | 1 | DIAG-01, RIGHTS-01 | T-22-01, T-22-02, T-22-03, T-22-19 | Changed source/ROM/reference/glyph/allowlist/mask/overlay, coordinated broader mask and one unmasked pixel fail with distinct reasons. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_(acid2_(tracer\|contract\|controls)\|fixture_admission_(contract\|controls))$'` | New checks; base acid2 tool exists | pending |
| 22-02-T1 | 22-02 | 2 | DIAG-01, DIAG-02, RIGHTS-01 | T-22-04, T-22-05, T-22-06 | All 513 names/pins, 480 macro and two inline verdicts, 31 initial exclusions, independent applicability and component grants remain visible. | integration | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_(admission_assessment\|fixture_admission_(contract\|controls))$'` | New records/assessment check | pending |
| 22-02-T2 | 22-02 | 2 | DIAG-01, DIAG-02, RIGHTS-01 | T-22-04, T-22-05, T-22-06 | Incomplete rights, model, oracle or required build facts exit nonzero with scope-resolution-required before downstream use; no redundant confirmation for clear gates. | other | `python3 -I tests/scripts/verify-diagnostic-admission.py --require-approved --repo-root . --source-revision HEAD` | New approval CLI; true owner scope gate | pending |
| 22-03-T1 | 22-03 | 3 | DIAG-01, RIGHTS-01 | T-22-07 | Original glyph/source-cell inputs regenerate bounded masks; missing/adjacent cells and changed anchors refuse. | integration | `python3 -I tests/scripts/reproduce-acid2.py --self-test-inputs && python3 -I tests/scripts/reproduce-acid2.py --check-inputs --repo-root . --source-revision HEAD` | New source/check/admission records; existing Phase 20 tool | pending |
| 22-03-T2 | 22-03 | 3 | DIAG-01, RIGHTS-01 | T-22-07 | Two clean builds reproduce both derivatives and mask/overlay members; references stay byte-identical; source/tool/member mutants fail. | integration | `python3 -I tests/scripts/reproduce-acid2.py --self-test && python3 -I tests/scripts/reproduce-acid2.py --verify-build --repo-root . --source-revision HEAD` | New build/glyph/allowlist records | pending |
| 22-04-T1 | 22-04 | 4 | DIAG-01, RIGHTS-01 | T-22-08, T-22-09 | Admitted acid2 bundle, manifest, grant notice and immutable pin match reproduced outputs; changed members refuse. | integration | `python3 -I tests/scripts/verify-fixture-admission.py --check-repository --repo-root . && python3 -I tests/scripts/reproduce-acid2.py --verify-build --repo-root . --source-revision HEAD` | New source/check/admission records; existing Phase 20 tool | pending |
| 22-04-T2 | 22-04 | 4 | DIAG-01, RIGHTS-01 | T-22-08, T-22-09 | Both real admitted derivatives compare exactly outside independently bounded source-cell masks; absence/skips/mismatches fail. | e2e | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_acid2_(tracer\|contract\|controls\|build_controls\|reproduction\|dmg_admitted\|cgb_admitted)$'` | New admitted assets/real tests | pending |
| 22-05-T1 | 22-05 | 5 | DIAG-02, RIGHTS-01 | T-22-10, T-22-11 | Existing runner observes reviewed HRAM protocol; default/partial verdict, identity/profile and protocol mutants fail. | e2e | `cmake --preset phase1 && cmake --build --preset phase1 && python3 -I tests/scripts/verify-gbmicrotest.py --self-test --runner build/gabbaboy-runner` | New oracle/checker; existing runner/API | pending |
| 22-05-T2 | 22-05 | 5 | DIAG-02, RIGHTS-01 | T-22-10, T-22-11 | Exact expected registrations and JUnit execution sets reject missing eligible tests, aggregator-only success, omissions and skips despite passing base controls. | integration | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_gbmicrotest_(protocol\|contract\|controls)$'` | New source/check/admission records; existing Phase 20 tool | pending |
| 22-06-T1 | 22-06 | 6 | DIAG-02, RIGHTS-01 | T-22-12 | All 513 source/ROM pairs and reviewed eligibility/exclusions retain exact Phase 20 grants, provenance, member bindings and immutable pin. | integration | `python3 -I tests/scripts/verify-fixture-admission.py --check-repository --repo-root . && python3 -I tests/scripts/verify-diagnostic-admission.py --require-approved --repo-root . --source-revision HEAD` | New source/check/admission records; existing Phase 20 tool | pending |
| 22-06-T2 | 22-06 | 6 | DIAG-02, RIGHTS-01 | T-22-12 | Complete independently expected eligible CTest names and JUnit executions are required; missing registrations/executions and skips fail despite passing base controls. | e2e | `cmake --preset phase1 && cmake --build --preset phase1 && python3 -I tests/scripts/verify-fixture-admission.py --check-repository --repo-root . && ctest --preset phase1 --show-only=json-v1 > build/phase22/gbmicrotest-ctest.json && python3 -I tests/scripts/verify-gbmicrotest.py --check-registration --ctest-inventory build/phase22/gbmicrotest-ctest.json --repo-root . --source-revision HEAD && ctest --preset phase1 --output-on-failure --no-tests=error --output-junit build/phase22/gbmicrotest-ctest-results.xml -R '^phase22_gbmicrotest_(protocol\|contract\|controls\|admitted\|case_.*)$' && python3 -I tests/scripts/verify-gbmicrotest.py --check-suite --ctest-inventory build/phase22/gbmicrotest-ctest.json --ctest-results build/phase22/gbmicrotest-ctest-results.xml --runner build/gabbaboy-runner --repo-root . --source-revision HEAD --write-evidence build/phase22/gbmicrotest-results.json` | New admitted cohort/per-case bindings | pending |
| 22-07-T1 | 22-07 | 7 | RIGHTS-01, DIAG-01, DIAG-02 | T-22-13, T-22-14, T-22-15 | Actual product trees reject bundled/renamed/extracted ROM/reference identities; exact bound projection cannot omit bytes. | integration | `python3 -I tests/scripts/verify-fixture-admission.py --check-repository --repo-root . && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(fixture_product_core_controls\|fixture_product_player_controls\|phase22_package_(bindings\|controls))$'` | Existing product checks; new identity view | pending |
| 22-07-T2 | 22-07 | 7 | RIGHTS-01, DIAG-01, DIAG-02 | T-22-13, T-22-14, T-22-15 | Source archive admission/notice/member checks and real product layouts stay distinct; nested/unlisted members, missing notices and disguised leakage fail. | integration | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_(package_(bindings\|controls)\|distribution_(contract\|controls))$'` | Existing archive checks; new controls | pending |
| 22-08-T1 | 22-08 | 8 | DIAG-01, DIAG-02, RIGHTS-01 | T-22-20, T-22-21, T-22-22 | Trusted downloaded macOS core/player and Windows core archive checks consume the complete view; disguised suffixless ROM/reference bytes fail and extraction is cleaned. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_group_release_jobs$'` | New checker wiring; existing downloaded archives, workflow, and lifecycle | pending |
| 22-08-T2 | 22-08 | 8 | DIAG-01, DIAG-02, RIGHTS-01 | T-22-20, T-22-21, T-22-22 | Synthetic disguised-byte controls assert the specific refusal; source-bound mutations reject projection removal/repointing or movement behind lifecycle validation. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(workflow_policy_group_release_jobs\|workflow_policy_coverage\|workflow_policy_coverage_controls\|release_lifecycle_controls)$'` | Existing registered CTests and control registry extended | pending |
| 22-09-T1 | 22-09 | 9 | DIAG-01, DIAG-02, RIGHTS-01 | T-22-23, T-22-24, T-22-25 | Source-bound reconciliation requires both real derivatives, complete cohort, package/view bindings, trusted downloaded archive controls, and current claim limits. | integration | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase22_(evidence_(contract\|controls)\|fixture_admission_(contract\|controls)\|package_bindings\|distribution_contract\|workflow_policy_group_release_jobs)$'` | New source-bound evidence checker | pending |
| 22-09-T2 | 22-09 | 9 | DIAG-01, DIAG-02, RIGHTS-01 | T-22-23, T-22-24, T-22-25 | Live PR head equals qualified source/local HEAD; applicable remote checks and same-head reviews pass; measured CI timings and automation value are recorded. | integration | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` plus the evidence/remote/closure commands below | Existing full-suite/closure tool; new evidence and CI timing records | pending |

Commands and CTest names are planning targets and must be made runnable by the plans. Every negative invocation must assert the intended refusal reason so setup failures cannot count as a successful control.

Final task additional commands:

- `python3 -I tests/scripts/verify-diagnostic-evidence.py --check --runner build/gabbaboy-runner --repo-root . --source-revision HEAD --write-evidence build/phase22/evidence.json`
- `python3 -I tests/scripts/verify-diagnostic-evidence.py --check-remote --repo-root . --source-revision HEAD --review-evidence build/phase22/review.json --security-evidence build/phase22/security.json --write-evidence build/phase22/remote-evidence.json`
- `python3 -I tests/scripts/verify-uat-closure.py .planning/phases/GB-22-composition-and-microtest-evidence --write .planning/phases/GB-22-composition-and-microtest-evidence/22-EVIDENCE.md && python3 -I tests/scripts/verify-uat-closure.py .planning/phases/GB-22-composition-and-microtest-evidence --self-test`

Every regex uses `--no-tests=error`; 22-05 supplies exact-set refusal controls and 22-06-T2 owns every eligible case registration plus the aggregator; --check-registration and --check-suite compare independently derived expected names against CTest JSON and JUnit results before the final evidence checker revalidates those identities, so a broad regex with only a subset present cannot establish completion. Plan 22-08 extends the already registered trusted `workflow_policy_group_release_jobs` and lifecycle control coverage; it creates no test name. The inventory owner table below identifies each registration update and Plan 22-09-T2 final reconciliation. New checks stay within existing ceilings; per-case execution is split rather than inflating a cohort-wide timeout. RGBDS reproduction uses the existing reproduction lane; native jobs validate the bound record and actual diagnostic comparisons.

## Dependencies and File Ownership

| Wave | Plan | Needs | Creates / user-visible increment |
|---|---|---|---|
| 1 | 22-01 | Existing acceptance runner and Phase 20 policy | One original diagnostic exercises admission → real runner → independent masked comparison → product refusal. |
| 2 | 22-02 | 22-01 admission adapter | Complete source/rights/model assessment and a real stop for unresolved gates. |
| 3 | 22-03 | 22-02 all-clear | Source-checked original glyph inputs, exact text masks and reproduced acid2 candidate bundles in ignored staging. |
| 4 | 22-04 | 22-03 reproduced inputs and identities | Immutable acid2 admission and both required real independent comparisons. |
| 5 | 22-05 | 22-02 assessment; 22-04 shared CMake ownership | Source-reviewed existing-runner protocol and registration/execution completeness controls. |
| 6 | 22-06 | 22-02 all-clear; 22-05 protocol/controls | Complete admitted cohort, every eligible per-case CTest and required aggregator, exact registration/JUnit execution proof. |
| 7 | 22-07 | 22-04/06 admitted manifests and real results | Bound forbidden-byte view, actual product exclusions and source archive controls. |
| 8 | 22-08 | 22-07 complete identity view and source/product boundaries | Trusted downloaded core/player archive checks consume the projection; disguised-byte controls and source-bound workflow/lifecycle coverage preserve validation-before-consumption/publication. |
| 9 | 22-09 | 22-04/06/07/08 real evidence | Source-bound reconciliation, live exact-head remote checks, same-head review/security closure, measured CI-efficiency finding, and owner-controlled phase handoff. |

The shared `tests/CMakeLists.txt` and notice index intentionally serialize these plans. Same-wave plans do not overlap because each wave has one plan. No redundant prior SUMMARY chain is required: references are limited to actual shared admission, fixture and evidence contracts. Bundle/member identities and source mapping are mandatory data, not stubs.

### Expected CTest Inventory Ownership

`tests/expected-tests.txt` is the tracked exact-name input checked by `cmake/ExpectedTests.cmake`; it is an owned output whenever a task changes registrations. Update it at each registration boundary, preserving prior entries, so the configure-time parity check remains satisfiable. Plan 22-08 extends existing release-policy/lifecycle test names and their source-bound control inventory, so it adds no `tests/expected-tests.txt` row. Plan 22-09-T2 performs final reconciliation after all Phase 22 registrations.

| Registration boundary | Inventory owner | Exact update |
|---|---|---|
| 22-01-T1 | 22-01-T1 | Add `phase22_acid2_tracer`. |
| 22-01-T2 | 22-01-T2 | Add the four acid2 and fixture-admission contract/control tests. |
| 22-02-T1 | 22-02-T1 | Add `phase22_admission_assessment`. |
| 22-04-T2 | 22-04-T2 | Add four acid2 build, reproduction and admitted-comparison tests. |
| 22-05-T2 | 22-05-T2 | Add the three base microtest protocol/accounting tests. |
| 22-06-T2 | 22-06-T2 | Add every eligible microtest case and the admitted aggregator. |
| 22-07-T1 | 22-07-T1 | Add package binding and package control tests. |
| 22-07-T2 | 22-07-T2 | Add distribution contract and distribution control tests. |
| 22-08-T1/T2 | Existing release-policy/lifecycle CTests | Extend the registered release_jobs and lifecycle controls; no new test-name row. |
| 22-09-T1 | 22-09-T1 | Add evidence contract and evidence control tests. |
| 22-09-T2 | 22-09-T2 | Regenerate/reconcile the final complete inventory against settled CTest registrations, including 22-07 and 22-09 additions. |

## Multi-Source Coverage Audit

| Source | Item | Plan / task | Status | Coverage |
|---|---|---|---|---|
| GOAL | Admitted independent rendering/microtest evidence with exact identities and explicit applicability | 22-02 through 22-09 | COVERED | Real approval gate, both actual pipelines, trusted downloaded-byte boundary and final source-bound reconciliation. |
| REQ | DIAG-01 | 22-01; 22-03/04; 22-09 | COVERED | Original glyphs, reproducible derivatives, unchanged references and exact source-cell masking. |
| REQ | DIAG-02 | 22-02; 22-05/06; 22-09 | COVERED | All 513 source/ROM names and evidence, reviewed verdicts and complete required execution accounting. |
| REQ | RIGHTS-01 cross-cutting admission | 22-01 through 22-09 | COVERED | Phase 20 records/pins, explicit grants, notices, source/product separation, trusted downloaded packages, and unchanged root MIT. |
| CONTEXT | D-01 pinned source/build, original glyphs, unchanged oracle and composition-only claims | 22-01-T1/T2; 22-02; 22-03/04; 22-09 | COVERED | Full derivative/source/tool/reference/rights identity chain and causal controls. |
| CONTEXT | D-02 source-cell allowlist, bounded mask/overlay, exact unmasked pixels | 22-01-T2; 22-03-T1/T2; 22-04-T1/T2 | COVERED | Source-anchored greeting/footer mapping, fixed 160x144 output, independent area bounds and one-pixel/broadened-mask controls. |
| CONTEXT | D-03 pinned complete microtest inventory, rights/model/protocol accounting | 22-02; 22-05/06; 22-09 | COVERED | Explicit eligibility-versus-terminal-outcome interpretation; 480 macro + two inline verdicts; 31 initial oracle exclusions; real scope stop. |
| RESEARCH | Exact acid2 source/gitlink/reference pins and RGBDS compatibility uncertainty | 22-02-T1; 22-03-T1/T2 | COVERED | Reverify immutable facts, existing RGBDS 1.0.1 pin, independent clean repeated build and no silent version substitution. |
| RESEARCH | Remaining component and generated-logo/reference rights are unresolved | 22-02-T1/T2 | COVERED | Component-by-component repository/public-CI scope and blocking owner evidence/rescope route before real use. |
| RESEARCH | WLA-DX unpinned; prebuilt identity is not build reproducibility | 22-02-T1/T2; 22-06-T1 | COVERED | Separate claims; no schema weakening, invented tool pin or unverified reproducible-build claim. |
| RESEARCH | CPU-08 statement uncertain; CPU-B cross-model; CGB not inferred | 22-02; 22-05/06; 22-09 | COVERED | Per-case source applicability and separately bound actual execution profile. |
| RESEARCH | Source roster identities/counts and no default HRAM verdict success | 22-02-T1; 22-05-T1/T2; 22-06-T1/T2 | COVERED | Full named fingerprint, inline protocol review and original fail/running/timeout controls. |
| RESEARCH | Actual package scanner schema differs from acid2 manifest | 22-07-T1/T2 | COVERED | Checked scanner-compatible byte projection with no rights authority; whole bundle and individual member denial. |
| RESEARCH | Trusted downloaded core/player archive checks must consume the same complete diagnostic byte projection before release lifecycle use | 22-08-T1/T2 | COVERED | Actual release verifier loads the view from the trusted root; synthetic disguised-byte refusal and source-bound lifecycle-order controls cover core/player paths. |
| RESEARCH | Bounded stdlib tooling, safe paths/subprocesses/member decoding | 22-01; 22-03/04; 22-05/06; 22-07 | COVERED | No added dependency; specific oversized/traversal/link/identity controls and immutable commit reads. |
| RESEARCH | CTest registration and automated negative controls on every deliverable | All eighteen tasks | COVERED | Concrete task map, specific failing directions, registration-bound expected-test inventory, existing release-control coverage and final source-bound evidence gate. |
| RESEARCH | No hardware/timing/game/broad compatibility or glyph comparison claim | 22-01/05/06/08/09 must-haves and 22-09-T1 | COVERED | Independent evidence labels, automated consistency controls and explicit descriptor-less unresolved prohibitions. |

No deferred ideas were introduced. Rights/applicability/source/build inability is an execution blocker requiring explicit scope resolution, not a silently missing plan. No frontend, external-service API or ORM schema is in scope. Assumption-delta detected a generic “another” wording signal; the recorded choice is **no-change**, preserving mandatory diagnostic evidence identity rather than making it optional.

## Spec-less Assumptions and Prohibition Recall

All five supplied generic probes remain explicit `status: unresolved` assumptions in plan must-haves: DIAG-01 empty/encoding in 22-01; DIAG-02 adjacency/empty/ordering in 22-02. Proposed operational behavior is documented without pretending a phase SPEC resolved them. Descriptor-less transparency prohibitions in 22-01, 22-02, 22-05, 22-06, 22-07, 22-08, and 22-09 remain unresolved and visible for downstream review; they have no invented `check_*` descriptors or automatic dismissal.

Adversarial recall considered self-derived references, broadened masks, synthetic-only completion, denominator changes, unsupported model claims, leaked fixture bytes, mutable source identities, path injection and unbounded work. Routine equality/bounds/duplicate/ordering issues stay in task behavior. Injection/path handling is security canon handled by the threat model and secure-phase review. Bespoke kept prohibitions concern laundering diagnostic/synthetic results into broader evidence and manufacturing admission by changing denominators or rights labels. No manual UAT was invented.

---

## Wave 0 Requirements

- [ ] Verify the pinned gbmicrotest tree and preserve all 513 source/ROM names with independently bound source and ROM identities.
- [ ] Resolve the accounting model explicitly: eligibility is an applicability/rights predicate; execution and exclusion are terminal outcomes, and every eligible case must execute. Record an exclusion reason for every case that cannot run.
- [ ] Record component-level rights and decide repository/public-CI use before admitting any third-party source, art, reference image, or ROM bytes.
- [ ] Verify the existing RGBDS 1.0.1 pin against both acid2 source revisions; keep source/build/output identities separate and make no gbmicrotest reproducible-build claim without a pinned WLA-DX closure and verified output.
- [ ] Create original replacement-glyph source, source-anchored text-cell allowlists, bounded generated masks, and reviewable overlays with pinned identities.
- [ ] Add synthetic negative controls for altered source/ROM/reference/mask identities, mask broadening, one unmasked pixel, incorrect model applicability, dropped/duplicated cases, unexplained exclusions, and missing execution.
- [ ] Register all new controls with CTest and extend actual core/player package checks for exact restricted fixture identities.

---

## Manual-Only Verifications

No manual UAT is planned. A maintainer's rights or model-scope decision remains an explicit admission gate when repository evidence cannot resolve it; it must not be converted into a manual test or inferred from a digest, populated manifest, or suite-wide license label.

---

## Planning Revision Dispositions

Each of the four Open Questions in 22-RESEARCH.md is marked RESOLVED for planning and mapped to an explicit implementation invariant or fail-closed execution/scope gate. Rights grants, model qualification and toolchain compatibility/reproduction remain unproven until the prescribed evidence exists.

Every plan includes the complete phase artifact/symbol index. Threats are registered once with unique numbered IDs; the package/dependency threat is T-22-19 in 22-01, trusted downloaded-product threats use T-22-20 through T-22-22 in 22-08, and final evidence uses T-22-23 through T-22-25 in 22-09. No dependency install is authorized. All nine plans have two tasks and no plan exceeds nine owned files; sequential waves preserve shared CMake/notice/checker ownership. This revision runs planning-structure and consistency checks only; no project build/test result, release publication, platform qualification, or fixture admission is claimed.

## Validation Sign-Off

- [ ] All tasks have `<automated>` verification or an explicit Wave 0 dependency.
- [ ] Sampling continuity: no three consecutive tasks lack automated verification.
- [ ] Wave 0 covers every missing validation dependency.
- [ ] No watch-mode flags.
- [ ] Focused checks stay within existing limits and measured feedback latency is recorded.
- [ ] Set `nyquist_compliant: true` only after execution-time validation closes every row.

**Planning mapping:** complete; execution evidence and validation sign-off remain pending.
