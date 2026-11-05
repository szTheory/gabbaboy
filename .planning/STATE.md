---
gsd_state_version: "1.0"
milestone: v0.4
milestone_name: Evidence Floor
current_phase: 23
current_phase_name: Qualified v0.4.0 Release
current_plan: 4
status: executing
stopped_at: Plan 23-04 T2: correct qualification-control assumptions, reissue all exact-source reports, and rerun focused/full qualification.
last_updated: "2026-11-05T01:46:15.000Z"
last_activity: "2026-11-05: The full suite's four failures were planning/test-harness issues. Historical-path pins, the Phase 23 gap-reserve allocation, and lifecycle recovery pin/count are corrected. The focused run found 14 source-bound ledger/review tests needing planning labels; the v0.4 notes renderer's output-only build path now has an exact checker exception and five causal controls. Direct checker controls pass and both planning-label CTests pass after reconfiguration. Commit the final label audit, reissue all three reviews at that exact source, then rerun the focused and full suites with escalated access; the sandbox-denied partial run is not qualification evidence."
state_head: 1a7558d9749538a894e23a9cf965210d57bb77dd
progress:
  total_phases: 4
  completed_phases: 3
  total_plans: 31
  completed_plans: 26
  percent: 75
---

# Project State

## Project Reference

See: [PROJECT.md](PROJECT.md), updated 2026-11-03.

**Core value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Current focus:** Plan 23-04 T2: commit the qualification-control fixes, reissue the three reviews at the exact implementation source, and pass the direct report, focused, and full-suite gates.

## Current Position

Current Plan: 4
Total Plans in Phase: 9
Phase: GB-23 (Qualified v0.4.0 Release) — EXECUTING
Phase 20 plans: 20-01 through 20-09 have summaries; all nine are complete under the approved cap.
Phase 21 plans: eight plans across six dependency waves are complete. Verification passed 5/5 roadmap criteria; the owner-approved phase-scoped override leaves FIXT-01 Pending because neither candidate cleared its source/rights gate.
Status: Executing Phase 23
Last activity: 2026-11-05: The initial 1,767-test run passed 1,763 and failed four planning/test-harness controls. Their causes are addressed: count-pin historical Git-object paths, allocate one gap slot to Phase 23 within the 40-slot cap, and update the post-tag recovery control for the reviewed checker and its 24 positive checks. The planning-label inventory sweep found 14 existing source-bound ledger/review tests; labels preserve `v02`, and the one build-tree output path is covered by an exact-mode classifier exception with five negative/positive controls. Direct no-phase-path checks pass (19 controls), planning-cap/hygiene passes (96 controls), lifecycle recovery passes (99 controls, 12 positives), and after reconfiguration the two planning-label CTests pass. The first default-sandbox focused attempt hit `/bin/ps` permission denials and two shard timeouts; rerun with escalated access after the final source review. Neither failed run is qualification evidence.

Completed stage: **Phase 22 — Synthetic Composition and Diagnostic Gate Assessment**. All five plans are complete. The final configured local suite passed 1,732/1,732; PR #142's exact head passed required CI, fixture reproduction, package artifact checks, independent reviews, branch protection, and merge-tree equality before merge as `ca2f0be6`. The phase remains metadata-only: seven real-fixture gates are unresolved, no real fixture was admitted or executed, DIAG-01, DIAG-02, and RIGHTS-01 remain Pending, and no license prohibition is inferred. A post-merge Windows push run exposed `phase22_evidence_controls` timing out at its existing 60-second bound under parallel load; PR #143 serializes this test without changing its timeout or assertions and merged as `4eee5b51` after exact-head checks passed. Its post-merge main CI, fixture-reproduction, and release-please runs all passed. PR #144 recorded the handoff and passed its protected checks and post-merge planning CI; the fixture-reproduction and release-please runs passed too. Local main was merged with remote main without rewriting the three local v0.4 commits, and the resulting tree matched origin at `d18db4c5`. The final ignored cleanup record is `build/phase22/repository-cleanup-evidence.json`.

## Phase 23 Execution Handoff

Phase 23 — Qualified v0.4.0 Release — is in progress at Plan 23-04 T2. The D-144 through D-154 matcher corrections and 32 deterministic docs shards passed their source-bound checks. The first full suite exposed four planning/test-harness assumptions; direct controls now pass after narrow fixes, and the nine scheduled plans remain unchanged under a total cap of 10 that includes the required gap reserve. Reissue all three reports against the new exact implementation, pass the direct gate, reconfigure/build, rerun the focused controls and full suite, then proceed to T3. Keep REL-01 and all Pending evidence limits. Continue with `/gsd-execute-phase 23` and stop at the Phase 23 boundary.

## Performance Metrics

All nine Phase 20 plans have executed. Configure/build and release-candidate replay passed at the final implementation head. Two full CTest runs plus six focused retests provide passing evidence for all 1,711 tests, including a standalone pass for the source-archive control after a full-suite timeout. Preserve the existing deterministic cost budget and state-continuation evidence.
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 21 P01 | 16min | 2 tasks | 6 files |
| Phase GB-21 P03 | 32min | 2 tasks | 5 files |
| Phase GB-21 P02 | 25min | 2 tasks | 8 files |
| Phase GB-21 P06 | 17min | 2 tasks | 4 files |
| Phase GB-21 P04 | 4min | 3 tasks | 2 files |
| Phase GB-21 P05 | 15min | 3 tasks | 1 files |
| Phase GB-21 P07 | 533min | 2 tasks | 17 files |
| Phase GB-22 P01 | 19min | 2 tasks | 6 files |
| Phase 22 P10 | about 24 min | 2 tasks | 5 files |
| Phase GB-22 P11 | about 90 min through local evidence preparation | 3 tasks | 19 files |
| Phase GB-23 P01 | 56min | 2 tasks | 4 files |
| Phase 23 P02 | 1h | 2 tasks | 5 files |
| Phase 23 P03 | 25min | 2 tasks | 3 files |

## Accumulated Context

Adopted decisions: [DECISIONS.md](context/DECISIONS.md), including v0.4 scope D-138 and the retained v0.3 closeout choice D-137. Detailed prior state: [v0.3-STATE-ARCHIVE.md](milestones/v0.3-STATE-ARCHIVE.md). The recent boundary sibling/Playstead scan is retained; no sibling was modified.

v0.4 has two substantive tracks: shared CGB progress/game evidence and acid2/gbmicrotest admission. Potion Panic is the first bounded candidate; µCity 1.3 is the only fallback. Exact source/build/model/rights gates remain pending; no game fixture is admitted. A justified absence after both attempts is permitted, but a newly reproduced unresolved correctness/security defect requires a rescope.

Retain root MIT and separate fixture terms. Full libretro is a near-term candidate outside v0.4; direct Steam Deck/SSH exploration is optional and does not qualify a Linux player. libfuturo is independent coordination context with no dependency or early API/state freeze.

RM-024 test quality, RM-025 measured CI duplication, the standalone closeout-helper failure, and optional release-tooling candidates retain their accepted dispositions and triggers in [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md). Do not reopen them without a concrete trigger. Existing release authority and platform exclusions remain scoped by the audit.

## Deferred Items

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| deferred_items | GB-16-tune-up-and-v0-2-debt-closure/deferred-items.md | Owner acknowledged failing standalone closeout-scan self-test for later repair or retirement; status remains failing | 2026-10-31 | v0.3 |
| verification | Phases 16–18 | Original passed boundary reports retained; stale runtime projections explicitly accepted at close | 2026-10-31 | v0.3 |
| tech_debt | Nine audit debt items | Owner accepted deferral; exact dispositions in closeout and audit | 2026-10-31 | v0.3 |
| uat_gaps | GB-14-cgb-e-model-qualification-and-corpus/14-UAT-REVIEW.md | clean (0 pending scenarios; prior scanner false positive), carried forward | 2026-10-24 | v0.2 |

Known verification overrides: 1 newly acknowledged, 1 carried forward. The runtime acknowledgment writer suppresses the exact artifact state; no failing verdict was rewritten.

## Session Continuity

**Last session:** 2026-11-05T01:46:15.000Z
**Stopped at:** Plan 23-04 T2's 14-test planning-label audit and exact output-only exception pass direct checks. Commit the final harness changes, reissue all three exact-source reviews, then rerun focused/full qualification with escalated access.
**Resume file:** .planning/phases/GB-23-qualified-v0-4-0-release/.continue-here.md

## Operator Next Steps

Phase 23 — Qualified v0.4.0 Release — is in progress at Plan 23-04 T2. The full docs controls and direct planning/lifecycle checks pass; both planning-label CTests now pass with the exact output-only exception. The first full suite remains a failed run with four diagnosed planning/test-harness issues, and the initial default-sandbox focused attempt is incomplete due denied `/bin/ps` calls and two shard timeouts. Commit the final harness changes, reissue all three reports at the resulting exact implementation source, pass the direct report gate, then rerun configure/build, the focused selection, and the full suite under escalated access before T3. Phase 23 keeps nine scheduled plans under total cap 10, including the gap reserve; the four-phase cap sum remains 40. No v0.4.0 qualification or publication is claimed. Continue with `/gsd-execute-phase 23` and stop at the Phase 23 boundary.

## Decisions

- [Phase 21]: The compatibility refusal control derives a valid compatibility-header variant from the same authored ROM so the loaded API mode is independently observable.
- [Phase 21]: Plan 21-03 self-tests remain synthetic-only; FIXT-01 stays pending for Plans 21-04, 21-05 and final composition.
- [Phase GB-21]: Emit each CGB receipt alongside --observe so identity, timing, digests, and PCM describe the same runner execution; compare a separate repeat only for reproducibility.
- [Phase GB-21]: A title, scene and symptom create unresolved triage; unknown identity or reproduction evidence remains explicit and never claims a live defect.
- [Phase GB-21]: A scene regression requires a rights-eligible minimized fixture, independent expected behavior, immutable source identity and a negative control that targets the stated expectation.
- [Phase GB-21]: Personal ROMs, saves, states and captures remain outside repository and hosted regression evidence; owner play is optional.
- [Phase GB-21]: Carry the existing test_budget timeout finding into Plan 21-07 without changing unrelated test declarations or adding an exception.
- [Phase GB-21]: Potion Panic stopped at the rights gate because the creator-linked exact source and component-level repository/public-CI scope could not be established; downstream facts remain not observed.
- [Phase GB-21]: After Potion Panic's checked no-go, assess only µCity 1.3's preferred `ucity.gbc`; the required hardware include has no identified grant or notice, so record a rights-scope no-go before build and keep downstream facts not observed.
- [Phase GB-21]: µCity 1.3 remains a concrete rights-scope no-go: required source/engine/hardware.inc has no identified grant or notice; do not infer license restriction from prior Codeberg reachability, and keep toolchain/build/game fields not observed.
- [Phase 21]: Potion Panic and µCity 1.3 remain rights/source-scope no-go outcomes; neither license prohibition is inferred, and FIXT-01 stays pending because required game build and ROM facts were not observed.
- [Phase 21]: The original CGB control remains harness-only under CGB-CPU-E; repeatable frame/audio digests do not qualify accuracy, physical hardware, perceptual behavior, mode-3 timing, or general compatibility.
- [Phase 21]: Fixture-admission mutation work was reduced to fit the unchanged deterministic 60-second budget without a baseline refresh or unrelated v0.3 repair.
- [Phase GB-21]: Windows synthetic controls invoke Python scripts through the active interpreter and inspect the same CTest configuration they execute.
- [Phase GB-21]: Normalize Windows CTest path separators when matching source-bound command arguments; verify with mixed-separator controls.
- [Phase 21]: Execute the nested scene CTest checks in the same explicit Debug configuration used for discovery and retain bounded failure output.
- [Phase 21]: Run nested scene CTests with the same explicit Debug configuration used for discovery and preserve failure diagnostics.
- [Phase GB-22]: Keep the tracer synthetic-only and bind its one visible tile cell to a fixed allowlist.
- [Phase GB-22]: Assert specific refusal reasons for identity, mask, image, path, and admission-pin mutants.
- [Phase GB-22]: Owner approved the Phase 22 synthetic-plus-metadata rescope; DIAG-01, DIAG-02, and RIGHTS-01 remain Pending and real fixture admission remains refused. — D-141 records that the metadata review could not establish the seven required real-fixture evidence gates. See .planning/phases/GB-22-composition-and-microtest-evidence/22-RESCOPE.md.
- [Phase 22]: Plan 22-10 checks the immutable metadata inventory and exact no-go claims while DIAG-01, DIAG-02, and RIGHTS-01 remain Pending.
- [Phase GB-22]: Retarget the Phase 21 primary-record pointer to PR #140’s squash commit only after exact record-blob identity was established; keep digest and ancestry mutants.
- [Phase GB-22]: Reduce the completed Phase 21 plan cap to 10, leaving two reserve slots and a four-phase total cap of 40.
- [Phase GB-23]: Keep the nine scheduled Phase 23 plans and reserve the tenth total-cap slot for the required single gap-closure round. Reallocate one unused ordinary-plan slot from completed Phase 21 by setting its active roadmap cap to 9; all eight Phase 21 plan files and evidence remain unchanged, and the four-phase cap sum stays 40.
- [Phase GB-22]: Allow planning inventory inspection only through the narrowly pinned configured CTest inventory invocation.
- [Phase GB-23]: Carry the nine state/core/player support claims from the pinned v0.3 profile without creating new producer receipts.
- [Phase GB-23]: Report the CGB-CPU-E native harness as repeatability-only and Phase 22 diagnostics as synthetic plus metadata-only.
- [Phase GB-23]: REL-01 remains Pending until Plan 23-06 establishes actual release evidence.
- [Phase 23]: Render the concise preface from the existing immutable support-claims-v0.4.json profile; preserve release-disclosure.json and v0.3 output. — The validated profile already contains all managed v0.4 facts, so a second copy would add drift risk without supplying new evidence.
- [Phase 23]: Owner approved the bounded Phase 23 T2 matcher correction and three-role re-review at the exact findings; amend Plan 23-04 in place and add no scheduled plan. The nine scheduled plans remain under total cap 10, including the single gap reserve, with unchanged review/gap counters; any new correctness/security finding requires another explicit owner decision.
- [Phase 23]: Owner approved D-145: extend Plan 23-04 T2 in place to reject unsupported CGB-game claims containing invisible Unicode format characters, with paired controls; no plan or budget reset.
- [Phase 23]: Owner approved D-146: extend the unsupported CGB-game claim matcher to ignore Unicode Default_Ignorable_Code_Point characters, including U+034F, with paired docs/release-note controls and exact-source review.
- [Phase 23]: Owner approved D-147: decode valid CommonMark character references only when they produce Cf or Unicode 18.0 Default_Ignorable_Code_Point characters in unsupported CGB-game claims, with paired controls and exact-source review.
- [Phase 23]: Owner approved D-148: decode all valid CommonMark character references in already-visible prose before unsupported CGB-game claim matching; preserve code masking and keep the change confined to that matcher.
- [Phase 23]: Owner approved D-149: normalize CommonMark hard line breaks only for unsupported CGB-game claim matching; preserve code masking and add paired controls. — At fc0ba4ff, adversarial review reproduced visible claims split by a backslash hard line break, including a reference-encoded space. The owner approved an in-place T2 correction and exact-source re-review; no plan or counter reset.
- [Phase 23]: Owner approved D-150: normalize CommonMark emphasis markers and inline link-label text only in the unsupported CGB-game matcher; preserve code masking and ignore destinations. — At e26757fa, adversarial review reproduced production docs-checker acceptance of bold, intraword emphasis, and inline link-label forms that CommonMark renders as visible CGB game claims. The owner approved the bounded in-place correction, paired docs/release-note controls, exact-source review, and gates on 2026-11-04; no plan or counter reset.
- [Phase 23]: Owner approved D-151: render shortcut, full, and collapsed CommonMark reference-link labels only for unsupported CGB-game claim matching; ignore destinations and titles and preserve code masking plus safe unresolved/escaped counterparts. — At exact source e017078b, release-consumer and adversarial review independently reproduced production docs-checker acceptance of visible CGB-game claims split through valid reference links. The owner approved paired docs/release-note and notice controls plus exact-source re-review on 2026-11-04; no plan or counter reset.
- [Phase 23]: Owner approved D-152: make CommonMark emphasis normalization linear in delimiter-run count using per-marker candidate stacks; preserve matched-delimiter behavior and add dense unmatched-marker controls. — At exact source b7987811, security review measured quadratic growth from rescanning all prior delimiter runs for each unmatched closer; 8,000 runs took about 1.07 seconds and the validator accepts documents up to 1 MiB. The owner approved the correction and exact-source review on 2026-11-04; no plan or counter reset.
- [Phase 23]: Owner approved D-153: apply Unicode punctuation and symbol categories as CommonMark emphasis punctuation only in unsupported CGB-game claim matching, with emoji and rule-of-three controls. — At exact source 6876fab0, adversarial review reproduced both visible claims passing the production docs matcher; no plan or counter reset.
- [Phase 23]: Owner approved D-154: reject impossible reference-label spans before copy/normalization using bounded span checks, with dense nested-bracket controls. — At exact source 6876fab0, security review found quadratic work over nested bracket spans that could exceed the docs gate timeout under the existing input limit; no plan or counter reset.

### Blockers

- No active Phase 22 blocker. The seven evidence gates still block real fixture admission, but D-141 scoped the completed phase to synthetic composition, metadata assessment, and explicit no-go controls. Do not fetch, build, run, or admit real diagnostic fixtures without a new owner-approved scope.
- Plan 23-04 T2 is active under owner-approved D-144 through D-154. Apply only the scoped Markdown normalization for unsupported CGB-game claim matching, preserve paired behavior, code masking and safe counterparts, then re-review exact source and pass report/focused CTest gates. REL-01 and publication remain Pending.
