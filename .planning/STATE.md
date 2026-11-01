---
gsd_state_version: "1.0"
milestone: v0.4
milestone_name: Evidence Floor
current_phase: 21
current_phase_name: CGB Game Progress and Scene Regressions
status: planning
stopped_at: Phase 20 complete, ready to plan Phase 21
last_updated: "2026-11-01T18:54:45.523Z"
last_activity: 2026-11-01
last_activity_desc: Phase 20 complete, transitioned to Phase 21
state_head: 39eb048e7770652b84a3fc5da7aaa3890adbd70c
progress:
  total_phases: 4
  completed_phases: 1
  total_plans: 9
  completed_plans: 9
  percent: 25
---

# Project State

## Project Reference

See: [PROJECT.md](PROJECT.md), updated 2026-10-31.

**Core value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Current focus:** Phase 21 — CGB Game Progress and Scene Regressions

## Current Position

Phase: 21 — CGB Game Progress and Scene Regressions
Plans: Phase 20-01 through 20-09 have summaries; all nine plans are complete under the approved cap.
Status: Phase 20 is complete; Phase 21 has not started.
Last activity: 2026-11-01 — Phase 20 final hosted and consumer qualification passed

Completed stage: **Phase 20 implementation, approved rescope, final reviews/security audit, local verification, and exact-head hosted qualification**. All nine plans have summaries. At implementation head `39eb048e7770652b84a3fc5da7aaa3890adbd70c`, the full local CTest run passed 1,708 tests; its three configure-time revision-snapshot failures passed after reconfigure/build in a focused retest. Both exact-head CI matrices and Linux/macOS/player consumer checks passed. All 29 authored security entries are closed and the final archive/path review is clean. `RIGHTS-01` remains pending because no fixture was admitted. Previous completed implementation phase remains **19 — Qualified v0.3.0 Release**.

Next workflow stage: **Owner pause after Phase 20**. The next phase is **21 — CGB Game Progress and Scene Regressions**; it has not started. When the owner chooses to continue, use **/gsd-discuss-phase 21**. No automatic advance is enabled; both `workflow.auto_advance` and `workflow._auto_chain_active` remain false.

## Performance Metrics

All nine Phase 20 plans have executed. Configure/build and release-candidate replay passed at the final implementation head. The full CTest run passed 1,708/1,711; the three revision-bound tests passed after reconfigure/build and focused retesting. The source-archive control runtime fell from 62.45 to 52.11 seconds with all negatives retained. Preserve the existing deterministic cost budget and state-continuation evidence.

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

**Last session:** 2026-11-01T18:54:45Z
**Stopped at:** Phase 20 complete; owner pause before Phase 21
**Resume file:** .planning/phases/GB-20-fixture-admission-tune-up/continue.md

## Operator Next Steps

No user action is needed now. Phase 20 is complete. When you choose to begin the next phase, run **/gsd-discuss-phase 21** for **21 — CGB Game Progress and Scene Regressions**. Phase 21 remains unstarted; do not auto-advance.
