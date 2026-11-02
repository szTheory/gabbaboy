---
gsd_state_version: "1.0"
milestone: v0.4
milestone_name: Evidence Floor
current_phase: 21
current_phase_name: CGB Game Progress and Scene Regressions
status: planning
stopped_at: Phase 21 context gathered
last_updated: "2026-11-02T00:27:58.775Z"
last_activity: 2026-11-01
last_activity_desc: Phase 20 verification passed after owner review; RIGHTS-01 stays pending and Phase 21 is unstarted
state_head: a0b81749e19056bf0d8555256e5d64da89017555
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

Phase: 20 — Fixture Admission Tune-up verification complete
Plans: Phase 20-01 through 20-09 have summaries; all nine plans are complete under the approved cap.
Status: Ready to plan
Last activity: 2026-11-01 — owner reviewed two judgment findings; Phase 20 verifier passed

Completed stage: **Phase 20 — Fixture Admission Tune-up, implementation and final verification**. All nine plans are complete. All 1,711 CTests have passing evidence across two partial full runs and six focused retests; no single full-suite invocation was all-green. Exact-head pull/push CI, preview-package, and fixture-reproduction runs passed; the security audit had no open items and final code review was clean. The final GSD verifier passes all 35 implementation truths with no human checkpoint. The owner reviewed the two judgment findings: public availability or matching hashes do not establish legal permission, and historical fixture approvals were preserved without extending them to new evidence. This review resolves those verification findings only. No fixture was admitted, no legal permission was granted, and `RIGHTS-01` remains Pending. Phase 21 has not started.

Next workflow stage: Phase 21 — CGB Game Progress and Scene Regressions, planning. Phase 21 context gathering is complete; implementation is still unstarted. When ready, run /gsd-plan-phase 21. Do not auto-advance; both workflow.auto_advance and workflow._auto_chain_active remain false.

## Performance Metrics

All nine Phase 20 plans have executed. Configure/build and release-candidate replay passed at the final implementation head. Two full CTest runs plus six focused retests provide passing evidence for all 1,711 tests, including a standalone pass for the source-archive control after a full-suite timeout. Preserve the existing deterministic cost budget and state-continuation evidence.

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

**Last session:** 2026-11-02T00:27:01.307Z
**Stopped at:** Phase 21 context gathered
**Resume file:** .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-CONTEXT.md

## Operator Next Steps

Phase 20 is complete and verified. The owner reviewed the two judgment findings; this does not admit a fixture or resolve `RIGHTS-01`, which remains Pending. Phase 21 — CGB Game Progress and Scene Regressions — is unstarted. When ready, the owner starts its discussion with **/gsd-discuss-phase 21**.
