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
| **Estimated runtime** | Measure during execution; Phase 23 has no full-suite timing baseline yet |

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
| 23-04-T1 | 04 | 4 | REL-01 | T-23-07/08/09 | Independent release/security/consumer/adversarial source review checks causal negative controls | integration | Focused full claim/window/product/workflow/lifecycle selection in 23-04-PLAN.md | Existing and newly registered controls | pending |
| 23-04-T2 | 04 | 4 | REL-01 | T-23-07/09 | Final implementation source passes full local suite and live exact-head protection; measured CI coverage retained | e2e | Configured full command plus `bash .github/scripts/verify-release-gates.sh --check-pr "$PHASE_PR" "$IMPLEMENTATION_SHA"` | Existing commands | pending |
| 23-07-T1 | 07 | 5 | REL-01 | T-23-16 | Actual generated immutable CMake/manifest output is exactly 0.4.0 before freeze/rehearsal/tag | integration | Immutable Git-object version assertion in 23-07-PLAN.md; paired wrong/mixed-version controls from 23-03 | Existing output; one-off assertion | pending |
| 23-07-T2 | 07 | 5 | REL-01 | T-23-17 | Compiled 0.4 pins, exact old/new digest disposition and independent base continuation evidence retain same-release-only policy | integration | Existing state pin/planning/refusal/semantic/codec controls in 23-07-PLAN.md with explicit immutable compatibility base | Existing checks | pending |
| 23-05-T1 | 05 | 6 | REL-01 | T-23-10 | Actual exact 0.4 output precedes H/R1/record-only W/R2/nightly/current-check freeze sequence | e2e | Exact-version, actual notes, active-window and live run/check commands in 23-05-PLAN.md | Existing workflow; checker extensions from 01–03 | pending |
| 23-05-T2 | 05 | 6 | REL-01 | T-23-12 | Owner makes a concrete one-way authority decision after preparation; stale head holds action | other | Existing exact-head PR gate; owner decision records authority separately from software acceptance | Existing gate | pending authority |
| 23-05-T3 | 05 | 6 | REL-01 | T-23-10/11/12 | Actual tagged/downloaded bytes, consumers/notices/fixture controls/nightly/final live inventory precede publication | e2e | Live release workflow plus existing published-asset readback verifier in 23-05-PLAN.md | Existing workflows/checkers | pending |
| 23-06-T1 | 06 | 7 | REL-01 | T-23-13 | Fresh final API/download inventory matches qualified source, product and consumer evidence | e2e | Existing published-asset verifier and lifecycle/product/workflow controls in 23-06-PLAN.md | Existing commands | pending |
| 23-06-T2 | 06 | 7 | REL-01 | T-23-14 | Exact SUMMARY schema and shared closure accept evidence and reject weakened copies; Pending requirements preserved | integration | Shared `verify-uat-closure.py` write/self-test and summary/closure CTest commands in 23-06-PLAN.md | Existing checker/CTest | pending |
| 23-06-T3 | 06 | 7 | REL-01 | T-23-15 | Point-in-time boundary facts and false auto flags survive closeout; owner chooses next stage | other | Config flag assertion and shared closure check in 23-06-PLAN.md | Existing config/checker | pending |

---

## Wave 0 Requirements

- [ ] Extend the source-bound support-claims profile for v0.4 and add positive and negative contract coverage.
- [ ] Extend generated release-disclosure checks for the required v0.4 evidence distinctions and limits.
- [ ] Include the v0.4 claims input in the version-window contract and retain changed-input refusal controls.
- [ ] Preserve the historical v0.3.0 support ledger and Phase 21/22 evidence records unchanged.

These are delivered inside 23-01 through 23-03, with tests and registration in each first implementation task; no separate foundation-only wave is needed.

---

## Manual-Only Verifications

All phase behavior has automated verification. Hosted credentials, required-check status, generated version-PR content, and real downloaded release artifacts must be observed through the existing trusted release process; local tests cannot substitute for those results. No human gameplay or perceptual review is a Phase 23 gate.

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
