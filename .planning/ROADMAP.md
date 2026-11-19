# Roadmap: GabbaBoy

## Milestones

- ✅ **v0.1 Limited DMG Preview** — Phases 1–6 and 06.1; shipped 2026-10-10; [archive](milestones/v0.1-ROADMAP.md).
- ✅ **v0.2 Color & Cartridge Breadth** — Phases 7–15 and 15.1; shipped 2026-10-24; [archive](milestones/v0.2-ROADMAP.md).
- ✅ **v0.3 Save States & Host Contract** — Phases 16–19; shipped 2026-10-31; [archive](milestones/v0.3-ROADMAP.md).
- ⚠️ **v0.4 Evidence Floor** — administratively closed 2026-11-17 after the qualified v0.4.0 release. Seven of eight requirements are complete; FIXT-01 remains Pending. Phase 24 Task 7, current verification for Phases 20/21/23.1, and D-103's exact-final-head suite are deferred and disclosed; [archive](milestones/v0.4-ROADMAP.md).

## Next

No new milestone is active. Phase 24 remains a recovery of the D-209 v0.4 closeout candidate; it does not reopen v0.4 or change archived requirement statuses. D-215/D-216/D-217 candidates and reviews remain immutable history. D-217's final review at `4239a8b` found three blockers and its recovery allowance is spent. D-218 authorizes one exact correction in the sole existing plan, limited to the two affected checkers; one new independent go/no-go review gates one protected PR matrix and conditional merge of that identical head. Any blocker or failed, skipped, stale or missing required context stops without another correction, review or matrix. Preserve branch protection, all required coverage and the separate phase/milestone closure boundary. After successful protected reconciliation and separate closure decisions, the recommended next milestone is v0.5 DMG PPU Timing, beginning with exact admission of a small, rights-clear DMG oracle set.

## Recovery Phase

### Phase 24: Resolve remaining v0.4 evidence and verification gaps

**Status:** D-217 local qualification passed at `cbef748`; the final review of `4239a8b` found three blockers and no push or matrix followed. D-218 authorizes T14's exact two-checker correction then T12 qualification in this sole plan. Its one new exact-head go/no-go review gates one full protected matrix and conditional merge; a blocker or unsuccessful required context stops without another cycle. v0.4 remains administratively closed with accepted gaps under D-209; archived requirements and original owners/statuses remain authoritative. The original D-211 matrix and package-preview runs ended failed at candidate `96d502d` and remain unchanged.
**Goal:** Correct only the three D-217 static-proof blockers, preserve v0.4 evidence and D-209 dispositions, and qualify only the exact reviewed head through existing branch protection.
**Requirements:** []
**Requirement boundary:** This recovery does not reassign requirements or change their statuses; the archived v0.4 tracker remains authoritative.
**Depends on:** Phase 23.1 (historical)
**Plan cap:** 1 existing ordinary plan; create no phase or additional plan.
**Success Criteria** (what must be TRUE):
  1. The dense-input mutant harness provides the exact candidate Git object context needed to resolve active fixture pins and ancestry; production admission remains fail-closed.
  2. Recovery checkers read the archived v0.4 requirements and roadmap without restoring an active root requirements tracker or changing D-209's disposition.
  3. State-fork inventory accounts for diagnostic manifests as explicit non-executed exclusions; Acid2, the prior `div_inc_timing_a` case, and the 512 excluded gbmicrotest cases are not rerun.
  4. Historical phase-path checking retains live-phase-reader detection, and the v0.4.0 tagged fixture-admission trust root is not refreshed, waived, or weakened.
  5. Planning-hygiene timeout causes are diagnosed before any budget change; no broad local suite, new dependency, or new CTest identity is added.
  6. Under D-218, the approved adapter and regex validator cannot be reflectively replaced, and the validated full revision reaches each protected archive reader unchanged, including match-pattern bindings. Causal controls and the same seven focused CTests pass before one new exact-head review. A clean review permits one full protected PR matrix; any blocker or failed, missing, skipped or stale required context stops without retry. Only the identical fully qualified head may merge through existing protection. Phase/milestone closure remains separate.
  7. The protected run records actual queue/dependency waits, job/step durations, timeout headroom and package-step behavior. No coverage or release gate is weakened; workflow optimization follows measured evidence only.
**Plans:**
- [ ] 24-01-PLAN.md — D-218 three-finding correction, focused regressions, one new go/no-go review, one protected matrix after a clean review, and conditional merge; phase/milestone closure remains separate.
