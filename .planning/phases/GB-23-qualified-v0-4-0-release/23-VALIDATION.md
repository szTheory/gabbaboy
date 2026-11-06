---
phase: "GB-23"
slug: "qualified-v0-4-0-release"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-03"
---

# Phase 23 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | CTest through the existing CMake preset suite |
| **Config file** | `CMakePresets.json` (`phase1` configure/build/test presets) |
| **Quick run command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(support_claims|support_claims_controls|release_disclosure_generator|release_disclosure_controls|release_window_contract|release_window_controls)$'` |
| **Full suite command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` |
| **Estimated runtime** | Measured: focused Phase 23 selection 447.84 seconds and full suite 951.31 seconds with four CTest workers |

---

## Sampling Rate

- **After every task commit:** Run the focused contract and its negative control for the changed behavior.
- **After every plan wave:** Run the full suite command above.
- **Before `$gsd-verify-work`:** Full suite and final-head release evidence must be green.
- **Max feedback latency:** Use existing CTest timeouts; record measured suite and hosted queue/dependency waits before proposing any scheduling change.

---

## Per-Task Verification Map

All entries are planned checks, not execution evidence. Each task's PLAN has an observable failure condition immediately after every runnable command. The new v0.4 test identities are created and registered by their owning task before invocation.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 23-01-T1 | 01 | 1 | REL-01 | T-23-01/02 | Immutable candidate facts reach exact production-rendered Markdown; promotion/refusal controls are causal | e2e | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(support_ledger_v04_tracer|support_claims_v04|support_claims_v04_controls|support_claims|support_claims_controls)$'` | Existing verifier; new tests created by this task | pending |
| 23-01-T2 | 01 | 1 | REL-01 | T-23-01/02 | Preserve 513/seven/zero/zero, Pending status, model/evidence distinctions and historical bytes | integration | Same focused selection plus existing disclosure generator/controls, as written in 23-01-PLAN.md | Existing verifier; task expands its controls | pending |
| 23-02-T1 | 02 | 2 | REL-01 | T-23-03/04 | Actual note omissions, contradictions, hidden clauses and unsupported promotions reject | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(release_notes_v04|release_notes_v04_controls|release_disclosure_generator|release_disclosure_controls|support_claims_v04|support_claims_v04_controls|adoption_claim_boundaries_controls)$'` | New note tests created by this task | pending |
| 23-02-T2 | 02 | 2 | REL-01 | T-23-03/04 | Public runbook retains actual matrix, limits and existing recovery holds | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(v02_adoption_docs|v02_adoption_docs_controls|release_notes_v04|release_notes_v04_controls)$'` | Existing docs tests extended | pending |
| 23-03-T1 | 03 | 3 | REL-01 | T-23-05 | Every new immutable managed input independently invalidates a stale window | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(release_window_contract|release_window_controls)$'` | Existing tests extended | pending |
| 23-03-T2 | 03 | 3 | REL-01 | T-23-06 | Exact requested 0.4.0 accepts; wrong/mixed/missing generated output rejects | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(release_window_contract|release_window_controls|release_version_v04_controls)$'` | New expected-version controls created by this task | pending |
| 23-09-T1 | 09 | 4 | REL-01 | T-23-19/20 | Every reproduced incomplete HTML opener rejects production notes/docs proof for its raw-HTML diagnostic; visible/masked counterparts pass | integration | `python3 -I tests/scripts/verify-v02-adoption.py --self-test-release-notes-v04 --repo . --rev "$(git rev-parse HEAD)"`; `python3 -I tests/scripts/verify-v02-adoption.py --self-test docs --root .` | Existing script/self-tests; targeted controls and guard added by this task | pending — red/green required |
| 23-09-T2 | 09 | 4 | REL-01 | T-23-19/20 | Committed changelog rejects every opener before heading and inside selected section; old-guard causal counterpart exposes bypass; existing content gates retained | integration | `python3 -I tests/scripts/verify-version-window.py --self-test-version-v04 --repo .`; configured serial notes/docs/window/disclosure CTest selection in 23-09-PLAN.md | Existing script, fixture CLI and CTest gates; expanded controls added by this task | pending — red/green required |
| 23-04-T1 | 04 | 5 | REL-01 | T-23-07/08 | Production review-evidence CLI and causal controls reject missing roles/reports, wrong/stale SHA, invalid schema/disposition, open blocking findings and source drift | integration | `python3 -I tests/scripts/verify-review-evidence.py --self-test --rev "$(git rev-parse HEAD)" --repo .`; configured `ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase23_review_evidence_controls$'` | New verifier, CTest pair and exact inventory entries created by this task | pass |
| 23-04-T2 | 04 | 5 | REL-01 | T-23-07/08/09 | Three independent reviewers perform source review; real immutable reports mechanically enforce role/source/schema/disposition completeness | integration | `python3 -I tests/scripts/verify-review-evidence.py --check --rev "$REVIEW_EVIDENCE_SHA" --implementation-sha "$IMPLEMENTATION_SHA" --qualification-sha "$REVIEW_EVIDENCE_SHA" --repo .`; focused CTests include `phase23_review_evidence_contract` and `phase23_review_evidence_controls` | Three committed reports at `e4fec7198d8488b4c0271a1363695e8c395248d3`, reviewed implementation `0a7b2b37644f20e43da813b67561587bbd0f86e5`; direct gate and focused 55-test selection passed | pass |
| 23-04-T3 | 04 | 5 | REL-01 | T-23-07/09 | Current qualification head contains reviewed implementation plus only allowlisted evidence; full local suite and live exact-head protection pass | e2e | Real-report `--check --rev "$QUALIFICATION_SHA" --implementation-sha "$IMPLEMENTATION_SHA" --qualification-sha "$QUALIFICATION_SHA" --repo .`; configured full command; `bash .github/scripts/verify-release-gates.sh --check-pr "$PHASE_PR" "$QUALIFICATION_SHA"` | Local qualification passed at `e4fec7198d8488b4c0271a1363695e8c395248d3`: 55/55 focused tests, then 1,774/1,774 full relocated tests with no skipped cases; report gate, test-budget, and planning-label inventories passed. PR #146 is open but remote head is stale at `4183ea298bd134578576bdb186b29ba4661dd6b3`; exact-head hosted checks and protection gate remain pending | local pass; hosted pending |
| 23-07-T1 | 07 | 6 | REL-01 | T-23-16 | Actual generated immutable CMake/manifest output is exactly 0.4.0 before freeze/rehearsal/tag | integration | Immutable Git-object version assertion in 23-07-PLAN.md; paired wrong/mixed-version controls from 23-03 | Existing output; one-off assertion | pending |
| 23-07-T2 | 07 | 6 | REL-01 | T-23-17 | Compiled 0.4 pins, exact old/new digest disposition and independent base continuation evidence retain same-release-only policy | integration | Existing state pin/planning/refusal/semantic/codec controls in 23-07-PLAN.md with explicit immutable compatibility base | Existing checks | pending |
| 23-05-T1 | 05 | 7 | REL-01 | T-23-10 | Actual exact 0.4 output precedes H/R1/record-only W/R2/nightly/current-check freeze sequence | e2e | Exact-version, actual notes, active-window and live run/check commands in 23-05-PLAN.md | Existing workflow; checker extensions from 01–03 | pending |
| 23-05-T2 | 05 | 7 | REL-01 | T-23-12 | Owner makes a concrete one-way authority decision after preparation; stale head holds action | other | Existing exact-head PR gate; owner decision records authority separately from software acceptance | Existing gate | pending authority |
| 23-05-T3 | 05 | 7 | REL-01 | T-23-10/11/12 | Actual tagged/downloaded bytes, consumers/notices/fixture controls/nightly/final live inventory precede publication | e2e | Live release workflow plus existing published-asset readback verifier in 23-05-PLAN.md | Existing workflows/checkers | pending |
| 23-06-T1 | 06 | 8 | REL-01 | T-23-13 | Fresh final API/download inventory matches qualified source, product and consumer evidence | e2e | Existing published-asset verifier and lifecycle/product/workflow controls in 23-06-PLAN.md | Existing commands | pending |
| 23-06-T2 | 06 | 8 | REL-01 | T-23-14 | Exact SUMMARY schema and shared closure accept evidence and reject weakened copies; Pending requirements preserved | integration | Shared `verify-uat-closure.py` write/self-test and summary/closure CTest commands in 23-06-PLAN.md | Existing checker/CTest | pending |
| 23-08-T1 | 08 | 9 | REL-01 | T-23-18 | Sanitized transfer/CI lessons and future direction cite actual immutable release evidence | other | Lesson/roadmap section and evidence-link assertion with removed-reference/transfer controls in 23-08-PLAN.md | Existing documents; one-off bookkeeping assertion | pending |
| 23-08-T2 | 08 | 9 | REL-01 | T-23-15/18 | All nine summaries enter final closure; point-in-time boundary facts, owner route and false auto flags survive handoff | integration | Exact-summary-set/route/flag assertion with mutation controls; shared --write using 23-UAT-EVIDENCE.md, --self-test and final check in 23-08-PLAN.md | Existing config/checker; one-off bookkeeping assertion | pending |

---

## Wave 0 Requirements

- [ ] Extend the source-bound support-claims profile for v0.4 and add positive and negative contract coverage.
- [ ] Extend generated release-disclosure checks for the required v0.4 evidence distinctions and limits.
- [ ] Include the v0.4 claims input in the version-window contract and retain changed-input refusal controls.
- [ ] Preserve the historical v0.3.0 support ledger and Phase 21/22 evidence records unchanged.

These are delivered inside 23-01 through 23-03, with tests and registration in each first implementation task; no separate foundation-only wave is needed. Plan 23-04-T1 additionally creates tests/scripts/verify-review-evidence.py and the phase23_review_evidence_contract and phase23_review_evidence_controls registrations plus both tests/expected-tests.txt entries. Both modes check the immutable registration/inventory contract, with missing/mutated registration controls. The controls run immediately on committed disposable inputs; the real-report positive CTest first runs in 23-04-T2 after all three actual reports are committed. Missing reports must fail rather than skip.

## Independent-review evidence contract

The owner-approved targeted rescope inserts 23-09 before 23-04; all later waves shift once. Existing findings RC-02/SEC-23-06/ADV-09 are bound to implementation 276f317d199cdd3246e9a90ce72a1f3a1235af1c and reports at 4c833703329a256e87614bc91c2b5b974427d6d8, with the later handoff containing metadata only. After 23-09's tested fix and SUMMARY commit, 23-04 T2 must reissue all three independent reports for the new actual implementation and run the direct real-report gate before unchanged T3 qualification. The old reports correctly fail that gate; passing plan checks or local regression controls does not close their findings. No manual UAT is added.

Plan 23-04-T2 assigns distinct release-consumer, security and adversarial reviewers to 23-REVIEW.md, 23-SECURITY.md and 23-ADVERSARIAL.md. Their single marked strict-JSON blocks bind report/reviewer identities, roles, independence declaration, reviewed_sha and each finding's category/severity/required_property/disposition/rationale/fix_sha/verification_ref. All reports must name the explicit actual IMPLEMENTATION_SHA. An unresolved correctness/security finding, or any other high/critical/blocking finding, prevents qualification. Fixed/rejected findings require the source-bound disposition evidence specified in the plan. The checker enforces these declared mechanical facts; substantive LLM review quality comes from the independent source-reading reviewers.

The direct --check reads the real report blobs at REVIEW_EVIDENCE_SHA and compares their reviewed_sha to the explicitly passed IMPLEMENTATION_SHA. --qualification-sha additionally rejects changes outside the six exact Phase 23 report/evidence/validation/summary paths. This separates reviewed implementation from the later commit that records its reviews without allowing an unreviewed source/test/workflow change. Plan 23-04-T3 repeats this check at observed QUALIFICATION_SHA before qualification/merge; the hosted gate checks that actual PR head. The permanent contract CTest reads reports from its configure-time immutable revision and validates their common historical implementation identity; it does not claim later generated release-version deltas were reviewed. Plan 23-05 retains its separate generated-delta review.

The --self-test must run the production --check CLI over committed disposable fixtures, pairing each accepted counterpart with a targeted missing-report/role, duplicate-identity, wrong/stale-existing-SHA, malformed/duplicate/unknown-key, invalid-disposition, unresolved correctness/high/blocking-security or non-evidence source-change mutation. Each mutant must reject with its intended diagnostic; dirty working-tree repair cannot change the immutable outcome. Tests/registration/inventory are source-linked; no execution result is claimed here.

---

## Manual-Only Verifications

All phase behavior has automated verification. Hosted credentials, required-check status, generated version-PR content, and real downloaded release artifacts must be observed through the existing trusted release process; local tests cannot substitute for those results. No human gameplay or perceptual review is a Phase 23 gate.

Plan 23-06's closure covers completed release-evidence summaries. Final phase acceptance additionally requires Plan 23-08's completed summary and regeneration through the same shared tool with `23-UAT-EVIDENCE.md` as the evidence input; `23-UAT.md` is generated output. Plan 23-08 asserts the exact nine-summary set because shared closure validates only summaries that exist.

Plan 23-05 includes the expressly required one-way decision immediately before version-PR merge/tag/publication. This is an authority boundary, not human UAT. The spec-less REL-01 edge remains unclassified/unresolved, and two descriptor-less transparency prohibitions remain flagged-unverified; 23-SOURCE-AUDIT.md records the recall/precision/projection evidence without manufacturing human acceptance scenarios.

---

## Validation Sign-Off

- [ ] All tasks have automated verification or explicit Wave 0 dependencies.
- [ ] Sampling continuity: no three consecutive tasks without automated verification.
- [ ] Wave 0 covers all planned missing test references.
- [ ] No watch-mode flags.
- [ ] Feedback latency is measured and bounded by existing timeouts.
- [ ] Set `nyquist_compliant: true` only after the verification map is complete and passing.

**Planning status:** Exact task map complete; execution and approval evidence pending. `nyquist_compliant` and `wave_0_complete` remain false until the required checks actually run and pass.
