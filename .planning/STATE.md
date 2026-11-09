---
gsd_state_version: "1.0"
milestone: v0.4
milestone_name: Evidence Floor
current_phase: 23
current_phase_name: Qualified v0.4.0 Release
current_plan: 4
status: executing
stopped_at: "Plan 23-04 T3: exact-head qualification run 42654987218 hit existing job limits; owner scheduling-scope decision is needed."
last_updated: "2026-11-09T17:30:40.000Z"
last_activity: "2026-11-09: Implementation 61f08de3 remains bound to three independent reviews; the exact local suite passed 1,942/1,942 at 9f38c43e. PR #146 remains at 343606f0. Its fixture, performance, player-package, sanitizer-build/fuzz, and Linux full-suite lanes passed; the exact-head CI run was cancelled after macOS, CMake-floor, sanitizer-inventory, and Windows jobs reached the existing 40/50/55/60-minute caps. No CTest assertion failure appeared before cancellation; native Linux passed in 47m56s. Preview smoke failed because its required CI run did not pass. D-163 prohibits changing job budgets and per-test timeouts. The serial 200-shard reservation prevents several required lanes from finishing, so merge is held for an owner decision on a bounded scheduling rescope. SEC-23-09 remains a low Git-output resource-bound note accepted by the report gate; no source change was made for it."
state_head: 343606f0cb105c837e928dc58d2ecea8b37e9670
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
**Current focus:** Plan 23-04 T3 is held on PR #146 at `343606f0cb105c837e928dc58d2ecea8b37e9670`. Local full CTest passed 1,942/1,942 at `9f38c43e`, and native Linux passed the hosted suite. macOS, CMake-floor, sanitizer-inventory, and Windows jobs hit their existing caps while running passing docs shards; preview smoke consequently failed. D-163 prohibits changing job budgets and per-test timeouts. Await the owner decision on a scheduling rescope before editing the PR branch or rerunning hosted qualification.

## Current Position

Current Plan: 4
Total Plans in Phase: 9
Phase: GB-23 (Qualified v0.4.0 Release) — EXECUTING
Phase 20 plans: 20-01 through 20-09 have summaries; all nine are complete under the approved cap.
Phase 21 plans: eight plans across six dependency waves are complete. Verification passed 5/5 roadmap criteria; the owner-approved phase-scoped override leaves FIXT-01 Pending because neither candidate cleared its source/rights gate.
Status: Executing Phase 23
Last activity: 2026-11-09: The immutable report gate passed on `343606f0` with three reports and 68 findings. The exact local candidate `9f38c43e` passed configure/build and 1,942/1,942 CTests with no skips after the build was refreshed. PR #146 now points to `343606f0`; fixture reproduction, performance, and macOS player package passed. Required native and dependent hosted checks are still running. SEC-23-09 remains a low availability-hardening note; no release fixture was fetched/admitted and REL-01 remains pending. Phase 23 is not complete.

Completed stage: **Phase 22 — Synthetic Composition and Diagnostic Gate Assessment**. All five plans are complete. The final configured local suite passed 1,732/1,732; PR #142's exact head passed required CI, fixture reproduction, package artifact checks, independent reviews, branch protection, and merge-tree equality before merge as `ca2f0be6`. The phase remains metadata-only: seven real-fixture gates are unresolved, no real fixture was admitted or executed, DIAG-01, DIAG-02, and RIGHTS-01 remain Pending, and no license prohibition is inferred. A post-merge Windows push run exposed `phase22_evidence_controls` timing out at its existing 60-second bound under parallel load; PR #143 serializes this test without changing its timeout or assertions and merged as `4eee5b51` after exact-head checks passed. Its post-merge main CI, fixture-reproduction, and release-please runs all passed. PR #144 recorded the handoff and passed its protected checks and post-merge planning CI; the fixture-reproduction and release-please runs passed too. Local main was merged with remote main without rewriting the three local v0.4 commits, and the resulting tree matched origin at `d18db4c5`. The final ignored cleanup record is `build/phase22/repository-cleanup-evidence.json`.

## Phase 23 Execution Handoff

Phase 23 is incomplete at Plan 23-04 T3. The reviewed implementation is `61f08de30b4f74ae539f827c5b04e1188fc3ea79`; the local exact-candidate suite passed 1,942/1,942 at `9f38c43ecc312f7ef868e4f359a8d30eee21760e`. PR #146 remains open at `343606f0cb105c837e928dc58d2ecea8b37e9670`.

Hosted run `42654987218` completed without qualification: native Linux passed 1,942/1,942 in 47m56s, while macOS stopped at 1,895/1,942 at 40 minutes, CMake 3.25.3 at 1,839/1,942 at 50 minutes, the sanitizer test shard at 1,785/1,853 at 55 minutes, and Windows at 1,746/1,804 at 60 minutes. The cancellation logs show passing docs shards and no assertion failures. Fixture reproduction run `42654987232` succeeded; preview run `42654987242` failed because its required CI run did not pass. D-163 explicitly forbids changing job budgets or per-test timeouts, and the four-slot reservation for all 200 docs shards makes the current native/floor jobs exceed those windows.

The PR body now records those results. Merge is held. The recommended next step is an owner-approved scheduling rescope that runs two docs shards concurrently while preserving all 200 assertions, labels, 90-second per-test ceilings, four-worker global CTest limit, and current job caps. After that decision, update the rescope/checker controls, reissue all three exact-source reviews, rerun the focused and full local suites, then run one fresh exact-head hosted qualification. Do not merge or advance to Phase 24 until Phase 23 closes.

Continue with `/gsd-execute-phase 23` after the owner decision. REL-01, DIAG-01, DIAG-02, and RIGHTS-01 remain Pending where evidence is unestablished. No real game or diagnostic fixture is admitted, and no tag or publication is claimed.

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

**Last session:** 2026-11-09T17:30:40.000Z
**Stopped at:** Plan 23-04 T3 hosted qualification on PR #146 did not pass because four required jobs reached their existing time caps. Local full CTest and hosted Linux passed. All docs shards passed before cancellation; no assertion failure was observed. Await a decision on amending D-163's four-slot reservation.
**Resume file:** .planning/phases/GB-23-qualified-v0-4-0-release/.continue-here.md

## Operator Next Steps

Phase 23 — Qualified v0.4.0 Release — is at Plan 23-04 T3, held on PR #146. Local exact-candidate CTest passed 1,942/1,942 at `9f38c43e`; hosted Linux passed 1,942/1,942. The latest exact-head hosted run did not qualify: macOS, CMake-floor, sanitizer-inventory, and Windows reached their existing job caps while executing passing docs shards; fixture reproduction passed and preview smoke failed because the required CI run did not pass. D-163 keeps the four-slot reservation for all 200 docs shards and prohibits changing job budgets or per-test timeouts. The supported correction is to amend only the shard reservation to two slots, preserving all 200 controls, assertions, labels, 90-second per-test ceilings, global CTest parallelism of four, and existing CI caps. No source or CI change is authorized until that scheduling decision is made. If approved, update the decision and controls, reissue the three exact-source reviews, run focused and full local qualification, then make one fresh exact-head hosted attempt. No merge, tag, publication, or Phase 24 work is eligible. Resume with `/gsd-execute-phase 23` and stop at the Phase 23 boundary.

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
