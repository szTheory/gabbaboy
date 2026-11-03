---
gsd_state_version: "1.0"
milestone: v0.4
milestone_name: Evidence Floor
current_phase: 22
current_phase_name: Composition and Microtest Evidence
current_plan: Not started
status: planning
stopped_at: Phase 21 verified; final closeout-head PR checks and merge remain in progress before Phase 22 planning
last_updated: "2026-11-03T01:29:20Z"
last_activity: 2026-11-02
last_activity_desc: Phase 21 verification passed 5/5 with the owner-approved FIXT-01 pending disposition; final closeout PR qualification remains
state_head: e0845db5841a1d56d8a297cbfaa3e0811af6ad67
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 17
  completed_plans: 17
  percent: 50
---

# Project State

## Project Reference

See: [PROJECT.md](PROJECT.md), updated 2026-10-31.

**Core value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Current focus:** Phase 21 closeout; Phase 22 remains unstarted

## Current Position

Current Plan: Not started
Total Plans in Phase: 0
Phase: 22 — Composition and Microtest Evidence (not started)
Phase 20 plans: 20-01 through 20-09 have summaries; all nine are complete under the approved cap.
Phase 21 plans: eight plans across six dependency waves are complete. Verification passed 5/5 roadmap criteria; the owner-approved phase-scoped override leaves FIXT-01 Pending because neither candidate cleared its source/rights gate.
Status: Phase 21 verified; final closeout-head PR checks and merge pending. Phase 22 planning waits for the owner-selected command.
Last activity: 2026-11-02 — Phase 21 verification and exact implementation-source CI completed; final documentation head remains to be qualified.

Completed stage: **Phase 21 — CGB Game Progress and Scene Regressions, implementation and verification**. All eight plans are complete. The final code source `e0845db5` passed configure/build, the 18 compile-command tests, and focused fixture-admission controls. The serial CTest suite passed 1,717/1,718 before `v02_source_archive_controls` hit its existing 90-second limit; that exact test passed an isolated same-source retry in 77.17 seconds. All tests have passing evidence across the full run plus the retry, but no single full invocation was all-green. Exact-head PR CI, fixture reproduction, both installed-package consumers, and player-package smoke passed at `e0845db5`. Independent scoped review and security review found no remaining issues; the security report has zero open threats. The verifier passed all five roadmap criteria using the documented owner disposition for FIXT-01. That requirement stays Pending; no game source or ROM was run and no rights clearance is claimed. The closeout documentation changes the PR head, so its exact checks must pass before merge. Phase 22 — Composition and Microtest Evidence — remains unstarted.

Current stage: Finish Phase 21's closeout on PR #140. The exact implementation-source head `e0845db5` has green PR native/platform, sanitizer, CMake-floor, fixture-reproduction, and package-consumer evidence. The currently edited closeout artifacts will be committed and pushed as a new PR head; accept merge only after that current head's required checks pass. Potion Panic and µCity 1.3 remain source/rights-scope no-go outcomes, not license prohibitions; neither game was run. `FIXT-01` remains Pending under the explicit phase-scoped verification override. The original CGB result is harness-only, and the scene workflow is synthetic-only. Keep both automatic-advance flags false.

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

**Last session:** 2026-11-03T01:29:20Z
**Stopped at:** Phase 21 verified; final closeout PR #140 exact-head checks and merge in progress
**Resume file:** .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/.continue-here.md

## Operator Next Steps

Phase 21 is verified at implementation source `e0845db5`; local, independent review/security, and exact-head PR evidence are recorded in the phase artifacts. The full CTest run had one existing 90-second timeout, and that exact test passed its isolated same-source retry at 77.17 seconds; no single full run was all-green. The verifier passed 5/5 roadmap criteria with an explicit phase-scoped disposition, while `FIXT-01` stays Pending. The current closeout commit changes the PR SHA. Continue with final PR #140 exact-head checks, then merge only if all required statuses pass. Phase 22 — Composition and Microtest Evidence — remains unstarted. The owner-selected next command after Phase 21 closeout is **/gsd-discuss-phase 22**; do not invoke it automatically. Both auto-advance flags remain false.

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
