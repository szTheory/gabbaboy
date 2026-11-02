---
gsd_state_version: "1.0"
milestone: v0.4
milestone_name: Evidence Floor
current_phase: 21
current_phase_name: CGB Game Progress and Scene Regressions
current_plan: 7
status: ready_for_verification
stopped_at: Completed GB-21-07-PLAN.md; exact-head PR qualification then shared verify-work
last_updated: "2026-11-02T10:33:29.100Z"
last_activity: 2026-11-02
last_activity_desc: Completed GB-21 Plan 21-07 local qualification at 9bed35ce; final PR-head hosted qualification is the next gate
state_head: 9bed35ce6e80e407ea31543cf986c795c9da061d
progress:
  total_phases: 4
  completed_phases: 1
  total_plans: 16
  completed_plans: 16
  percent: 25
---

# Project State

## Project Reference

See: [PROJECT.md](PROJECT.md), updated 2026-10-31.

**Core value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Current focus:** Phase GB-21 — CGB Game Progress and Scene Regressions

## Current Position

Current Plan: 7
Total Plans in Phase: 7
Phase: GB-21 (CGB Game Progress and Scene Regressions) — FINAL QUALIFICATION
Phase 20 plans: 20-01 through 20-09 have summaries; all nine are complete under the approved cap.
Phase 21 plans: seven reviewed plans across five dependency waves; all four requirements are covered.
Status: Local execution complete; verify the exact-head hosted and installed-consumer checks, then run shared phase closure
Last activity: 2026-11-02 — Completed Phase GB-21 Plan 21-07 local qualification at `9bed35ce`

Completed stage: **Phase 20 — Fixture Admission Tune-up, implementation and final verification**. All nine plans are complete. All 1,711 CTests have passing evidence across two partial full runs and six focused retests; no single full-suite invocation was all-green. Exact-head pull/push CI, preview-package, and fixture-reproduction runs passed; the security audit had no open items and final code review was clean. The final GSD verifier passes all 35 implementation truths with no human checkpoint. The owner reviewed the two judgment findings: public availability or matching hashes do not establish legal permission, and historical fixture approvals were preserved without extending them to new evidence. This review resolves those verification findings only. No fixture was admitted, no legal permission was granted, and `RIGHTS-01` remains Pending. Phase 21 planning is complete; Plan 21-01 now supplies the native-CGB progress tracer and loaded-mode refusal control.

Current stage: Phase 21 — CGB Game Progress and Scene Regressions, final qualification. Plans 21-01 through 21-07 are summarized; configure/build, all 1,724 CTests, the fixed 60-second test-budget gate, and source-bound receipt pass at source `9bed35ce6e80e407ea31543cf986c795c9da061d`. The serial full suite completed in 1,227.20 seconds. Windows CMake-path, pinned-byte, Python-runner, and matching-Debug-configuration fixes pass locally. The push diagnostic at `b4e4c41a` is not PR qualification; use only hosted checks whose head SHA matches the final PR #140 head, including installed-consumer jobs. Potion Panic is a no-go because exact component grants and repository/public-CI source scope were not established after its creator-linked source fetch failed. µCity 1.3 is a no-go because required `source/engine/hardware.inc` has no identified grant or notice. Neither outcome asserts license prohibition; neither game was run and downstream tool/build/ROM facts remain not observed. FIXT-01 remains pending. The CGB ROM result is harness-only, and the scene workflow is synthetic-only with no live defect claimed. Both workflow.auto_advance and workflow._auto_chain_active remain false.

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
| Phase GB-21 P07 | 393min | 2 tasks | 17 files |

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

**Last session:** 2026-11-02T10:33:29.012Z
**Stopped at:** Completed GB-21-07-PLAN.md; exact-head PR qualification then shared verify-work
**Resume file:** .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/.continue-here.md

## Operator Next Steps

Phase 21 Plan 21-07 local implementation and qualification are complete at source `9bed35ce`; configure/build, all 1,724 CTests, the unchanged 60-second budget, and the source-bound receipt passed. Check hosted native/platform and installed-consumer jobs on the exact final PR #140 head; the earlier push run is diagnostic only. When those checks pass, run **/gsd-verify-work 21** for shared phase closure. Phase 22 — Composition and Microtest Evidence — remains not started; after Phase 21 closes, the owner-selected next phase command is **/gsd-discuss-phase 22**. Do not invoke that command automatically. Both auto-advance flags remain false.

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
