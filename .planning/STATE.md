---
gsd_state_version: "1.0"
milestone: v0.4
milestone_name: Evidence Floor
current_phase: 20
current_phase_name: Fixture Admission Tune-up
status: executing
stopped_at: Phase 20 local verification complete — awaiting exact-head hosted macOS qualification
last_updated: "2026-11-01T14:12:14Z"
last_activity: 2026-11-01
last_activity_desc: Phase 20 rescope, reviews, security audit, full local suite, and release replay passed; hosted PR gate is pending
state_head: 3cdfb1dbebeb60c5969de5fbeb93401968dc067c
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 9
  completed_plans: 9
  percent: 0
---

# Project State

## Project Reference

See: [PROJECT.md](PROJECT.md), updated 2026-10-31.

**Core value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Current focus:** Phase 20 — Fixture Admission Tune-up

## Current Position

Phase: 20 (Fixture Admission Tune-up) — EXECUTING, hosted exact-head qualification pending
Plans: 20-01 through 20-09 have summaries; all nine plans are complete under the approved cap.
Status: Local configure/build, all 1,711 CTests, release-candidate replay, final code reviews, and the 29-entry security audit pass. The hosted `macos-player-package` check must still pass on the final pushed revision before Phase 20 closes. `RIGHTS-01` remains pending because no fixture was admitted.
Last activity: 2026-11-01 — final local Phase 20 verification passed; preparing the hosted exact-head check.

Completed stage: **Phase 20 implementation, rescope, final reviews, security audit, and local verification**. All nine plans have summaries; configure/build, 1,711/1,711 CTests, and the release-candidate replay pass at implementation head `7293eb47a6c799b6455dd854533aca932f4529ad`. The phase remains open only for exact-head hosted macOS package qualification. `RIGHTS-01` remains pending because no fixture was admitted. Previous completed implementation phase remains **19 — Qualified v0.3.0 Release**.

Next workflow stage: **Exact-head hosted Phase 20 qualification**. The agent will push the reviewed Phase 20 candidate, open/refresh its PR, and verify the required macOS package check on the resulting head. No user action is needed while those checks run. Both `workflow.auto_advance` and `workflow._auto_chain_active` remain false. Stop at Phase 20; do not begin Phase 21 — CGB Game Progress and Scene Regressions before hosted qualification passes.

## Performance Metrics

All nine Phase 20 plans have executed. Configure/build, full CTest (1,711/1,711), and release-candidate replay pass. No new performance measurements are claimed. Preserve the existing deterministic cost budget and state-continuation evidence.

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

**Last session:** 2026-11-01T14:12:14Z
**Stopped at:** Phase 20 local verification complete — awaiting hosted exact-head macOS check
**Resume file:** .planning/phases/GB-20-fixture-admission-tune-up/continue.md

## Operator Next Steps

No user action is needed now. The agent will complete the exact-head hosted PR check, then update the phase boundary records. If all required checks pass, the next phase is **21 — CGB Game Progress and Scene Regressions**, with exact next command **/gsd-discuss-phase 21**. Do not restart Phase 19 or automatically advance to Phase 21.
