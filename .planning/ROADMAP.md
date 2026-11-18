# Roadmap: GabbaBoy

## Milestones

- ✅ **v0.1 Limited DMG Preview** — Phases 1–6 and 06.1; shipped 2026-10-10; [archive](milestones/v0.1-ROADMAP.md).
- ✅ **v0.2 Color & Cartridge Breadth** — Phases 7–15 and 15.1; shipped 2026-10-24; [archive](milestones/v0.2-ROADMAP.md).
- ✅ **v0.3 Save States & Host Contract** — Phases 16–19; shipped 2026-10-31; [archive](milestones/v0.3-ROADMAP.md).
- ⚠️ **v0.4 Evidence Floor** — administratively closed 2026-11-17 after the qualified v0.4.0 release. Seven of eight requirements are complete; FIXT-01 remains Pending. Phase 24 Task 7, current verification for Phases 20/21/23.1, and D-103's exact-final-head suite are deferred and disclosed; [archive](milestones/v0.4-ROADMAP.md).

## Next

No new milestone is active. Phase 24 remains a recovery of the D-209 v0.4 closeout candidate; it does not reopen v0.4 or change archived requirement statuses. D-215's T10–T12 local checks passed at `e1d3200`, but the exact-head review found four blockers; no push or matrix followed. D-216 extends the sole existing plan to cover those four findings and authorizes T13 corrections followed by T12 qualification. Up to two scoped fix/re-review passes remain available, then one full protected matrix after a clean final review and conditional protected merge of the identical head. Preserve branch protection, all required coverage and the separate phase/milestone closure boundary. After successful protected reconciliation and separate closure decisions, the recommended next milestone is v0.5 DMG PPU Timing, beginning with exact admission of a small, rights-clear DMG oracle set.

## Recovery Phase

### Phase 24: Resolve remaining v0.4 evidence and verification gaps

**Status:** D-216 authorizes T13's four-finding correction and T12 final qualification in the sole existing plan. Candidate `e1d3200` and its blocked review remain immutable historical evidence; no push or matrix followed. v0.4 remains administratively closed with accepted gaps under D-209; archived requirements and original owners/statuses remain authoritative. The original D-211 matrix and package-preview runs ended failed at candidate `96d502d` and remain unchanged.
**Goal:** Execute the bounded integrated recovery for the remaining Phase 24 trust-boundary findings, preserve v0.4 evidence and D-209 dispositions, and qualify only the exact reviewed head through existing branch protection.
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
  6. Under D-216, the four exact reviewed path/Git/census findings are corrected and locally tested before the seven existing focused CTests. A fresh independent review may be followed by up to two scoped fix-and-re-review passes. A new out-of-scope issue or unresolved finding stops. Only a clean final review permits one full protected PR matrix; failed, missing, skipped or stale required contexts stop without retry. The identical fully qualified head may merge through existing protection. Phase/milestone closure remains separate.
**Plans:**
- [ ] 24-01-PLAN.md — D-216 four-finding extension and execution, focused regressions, scoped review exception, one full protected matrix and conditional merge; phase/milestone closure remains separate.
