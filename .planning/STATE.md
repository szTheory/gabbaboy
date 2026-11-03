---
gsd_state_version: "1.0"
milestone: v0.4
milestone_name: Evidence Floor
current_phase: 22
current_phase_name: Composition and Microtest Evidence
current_plan: 2
status: executing
stopped_at: Completed GB-22-01-PLAN.md
last_updated: "2026-11-03T10:05:17.560Z"
last_activity: 2026-11-03
last_activity_desc: Phase GB-22 Plan 22-01 complete; Plan 22-02 remains
state_head: e0cf205d576fb43461eb546026035f6d3b5e8167
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 26
  completed_plans: 18
  percent: 50
---

# Project State

## Project Reference

See: [PROJECT.md](PROJECT.md), updated 2026-10-31.

**Core value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Current focus:** Phase GB-22 — Composition and Microtest Evidence

## Current Position

Current Plan: 2
Total Plans in Phase: 9
Phase: GB-22 (Composition and Microtest Evidence) — EXECUTING
Phase 20 plans: 20-01 through 20-09 have summaries; all nine are complete under the approved cap.
Phase 21 plans: eight plans across six dependency waves are complete. Verification passed 5/5 roadmap criteria; the owner-approved phase-scoped override leaves FIXT-01 Pending because neither candidate cleared its source/rights gate.
Status: Executing Phase GB-22
Last activity: 2026-11-03 — Phase GB-22 Plan 22-01 complete; Phase execution continues

Completed stage: **Phase 21 — CGB Game Progress and Scene Regressions, implementation and verification**. All eight plans and five roadmap criteria are complete. Implementation source `e0845db5` passed configure/build, the 18 compile-command tests, and focused fixture-admission controls. The serial local CTest suite passed 1,717/1,718 before `v02_source_archive_controls` hit its existing 90-second limit; that test passed an isolated same-source retry in 77.17 seconds, so every local test has passing evidence across the full run and retry, but no single invocation was all-green. PR #140's final checked head `507019f9` passed the required native/platform, sanitizer, CMake-floor, fixture-reproduction, installed-consumer, and player-package checks and was squash-merged as `bef2cfbd`; the merged tree matches the checked PR head. The first macOS hosted full-suite attempt timed out `phase21_fixture_admission_controls` at 60.08 seconds; its same-head full-suite rerun passed all 1,724 tests, including that control in 50.18 seconds. Independent scoped review and security review found no remaining issues; the security report has zero open threats. The verifier passed all five roadmap criteria using the documented owner disposition for FIXT-01. That requirement remains Pending; no candidate game source or ROM was run and no rights clearance is claimed. Phase 22 planning has now passed independent review, with nine execution plans across nine sequential waves.

Current stage: Phase 21 is complete. PR #140 final head `507019f9` passed its required checks and merged to main as `bef2cfbd`; the squash tree matches the checked PR tree. Phase 22 Plan 22-01 is complete: the synthetic compiled-runner tracer and four identity/mask/admission controls passed. Plan 22-02 is next within the same phase; continue with `/gsd-execute-phase 22`. This synthetic evidence does not admit any game or clear third-party rights. Potion Panic and µCity 1.3 remain source/rights-scope no-go outcomes, not license prohibitions; neither game was run. `FIXT-01` remains Pending. Keep both automatic-advance flags false.

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

**Last session:** 2026-11-03T10:05:17.427Z
**Stopped at:** Completed GB-22-01-PLAN.md
**Resume file:** None

## Operator Next Steps

Phase 21 is verified at implementation source `e0845db5` and merged after exact-head PR qualification. PR #140 final head `507019f9` passed required checks and squash-merged as `bef2cfbd` with an identical tree. Phase 22 Plan 22-01 is complete; its five selected tests pass, including the original synthetic tracer. Next is Plan 22-02's admission and source-scope assessment; continue within the active phase with **/gsd-execute-phase 22**. Rights for any third-party fixture remain unresolved, and `FIXT-01` remains Pending. Do not advance automatically beyond Phase 22.

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
