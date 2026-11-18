# Roadmap: GabbaBoy

## Milestones

- ✅ **v0.1 Limited DMG Preview** — Phases 1–6 and 06.1; shipped 2026-10-10; [archive](milestones/v0.1-ROADMAP.md).
- ✅ **v0.2 Color & Cartridge Breadth** — Phases 7–15 and 15.1; shipped 2026-10-24; [archive](milestones/v0.2-ROADMAP.md).
- ✅ **v0.3 Save States & Host Contract** — Phases 16–19; shipped 2026-10-31; [archive](milestones/v0.3-ROADMAP.md).
- ⚠️ **v0.4 Evidence Floor** — administratively closed 2026-11-17 after the qualified v0.4.0 release. Seven of eight requirements are complete; FIXT-01 remains Pending. Phase 24 Task 7, current verification for Phases 20/21/23.1, and D-103's exact-final-head suite are deferred and disclosed; [archive](milestones/v0.4-ROADMAP.md).

## Next

No new milestone is active. Phase 24 remains a recovery of the D-209 v0.4 closeout candidate; it does not reopen v0.4 or change the archived requirement statuses. The D-213 plan passed independent review and D-214 authorizes its T10–T12 recovery scope. Execution starts with the local, unpushed planning-boundary commit. After protected reconciliation and separate closure decisions, the recommended next milestone is v0.5 DMG PPU Timing, beginning with exact admission of a small, rights-clear DMG oracle set.

## Recovery Phase

### Phase 24: Resolve remaining v0.4 evidence and verification gaps

**Status:** The sole D-213 recovery plan passed an independent plan check; D-214 now authorizes T10–T12, scoped local convergence, one fresh exact-head review and one protected PR matrix. Execution is beginning with the local planning-boundary commit and its full-tree preflight. v0.4 remains administratively closed with accepted gaps under D-209; archived requirements and original owners/statuses remain authoritative. The original D-211 matrix and package-preview runs ended failed at candidate `96d502d` and remain unchanged.
**Goal:** Plan one integrated recovery round for the D-211 CI blockers, the stale Phase 24 path-linter count, and the active-route immutable-candidate gap, preserving v0.4 evidence and trust boundaries.
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
  6. Under D-214, in-scope local diagnosis/fix/retest converges until cheap and focused checks pass; then at most one fresh exact-head review and one new protected PR matrix. Any final-review finding or failed, missing, skipped, or stale required CI context stops without another review/matrix cycle.
**Plans:**
- [ ] 24-01-PLAN.md — Integrated D-213 recovery scope; D-214-authorized execution begins with the planning-boundary commit.
