# Roadmap: GabbaBoy

## Milestones

- ✅ **v0.1 Limited DMG Preview** — Phases 1–6 and 06.1; shipped 2026-10-10; [archive](milestones/v0.1-ROADMAP.md).
- ✅ **v0.2 Color & Cartridge Breadth** — Phases 7–15 and 15.1; shipped 2026-10-24; [archive](milestones/v0.2-ROADMAP.md).
- ✅ **v0.3 Save States & Host Contract** — Phases 16–19; shipped 2026-10-31; [archive](milestones/v0.3-ROADMAP.md).
- ⚠️ **v0.4 Evidence Floor** — administratively closed 2026-11-17 after the qualified v0.4.0 release. Seven of eight requirements are complete; FIXT-01 remains Pending. Phase 24 Task 7, current verification for Phases 20/21/23.1, and D-103's exact-final-head suite are deferred and disclosed; [archive](milestones/v0.4-ROADMAP.md).

## Next

No new milestone is active. Phase 24 remains a recovery of the D-209 v0.4 closeout candidate; archived requirement statuses remain authoritative. D-215 through D-218 candidates and blocked reviews remain immutable history. D-218's focused local checks passed, but its frozen review returned NO-GO for runtime-binding and exact archive-pin proof gaps; no push or protected matrix followed. D-219 authorizes the integrated six-checker recovery in the sole existing plan: T15/T16 correction and T17 qualification, at most two scoped correction/review passes total, then one protected matrix only after a clean final review and conditional merge of that identical passing head. Preserve required coverage, branch protection and the phase/milestone closure boundary. After this plan passes independent checking and its documentation-only boundary is committed, the next command is `$gsd-execute-phase 24`. After successful protected reconciliation and separate closure decisions, the recommended next milestone is v0.5 DMG PPU Timing, beginning with exact admission of a small, rights-clear DMG oracle set.

## Recovery Phase

### Phase 24: Resolve remaining v0.4 evidence and verification gaps

**Status:** D-219 planning updates the sole existing plan after D-218's NO-GO at frozen head `ba5afae5`. T15/T16 address the six-checker runtime/archive-pin, Git-selection and inventory-CLI scope; T17 qualifies the integrated candidate. Execution is covered by the owner's prior extend-and-execute authorization only after independent plan checking and the documentation-only planning commit. At most two correction/review passes total and one clean-review-gated protected matrix are permitted; conditional merge uses the identical reviewed/passing head. v0.4 remains administratively closed with accepted gaps under D-209. D-211's failed runs and every blocked review remain historical evidence.
**Goal:** Make the six existing checker contracts prove runtime binding, exact archive/revision identity, original-object Git selection and inventory-mode exclusivity, then qualify only the identical reviewed head through existing branch protection while preserving D-209 dispositions.
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
  6. Under D-219, aliased imports/function globals/reflective writes cannot replace the adapter, validator or exact D-209 pin; every validated revision reaches its protected reader unchanged, including match bindings. All six trusted Git adapters ignore replacement refs and inherited repository/index/object/namespace redirection. Inventory mode rejects every conflicting operation/input before Git/output effects, while valid positives and the census/exclusions remain. Causal controls and the same seven focused CTests pass before review. The first corrected review is pass one; only one in-scope correction/fresh review may be pass two. An unavailable/out-of-scope review or blocker after pass two stops. A clean final review permits one protected matrix; any failed, missing, skipped or stale required context stops without matrix retry. Only the identical fully qualified head may merge through existing protection; closure remains separate.
  7. The protected run records actual queue/dependency waits, job/step durations, timeout headroom and package-step behavior. No coverage or release gate is weakened; workflow optimization follows measured evidence only.
**Plans:**
- [ ] 24-01-PLAN.md — D-219 integrated recovery in T15/T16/T17: closed Python proof, isolated original-object Git, exclusive inventory CLI, same seven focused CTests, at most two correction/review passes total, one matrix after clean final review and conditional protected merge; phase/milestone closure remains separate.
