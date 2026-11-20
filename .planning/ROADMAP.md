# Roadmap: GabbaBoy

## Milestones

- ✅ **v0.1 Limited DMG Preview** — Phases 1–6 and 06.1; shipped 2026-10-10; [archive](milestones/v0.1-ROADMAP.md).
- ✅ **v0.2 Color & Cartridge Breadth** — Phases 7–15 and 15.1; shipped 2026-10-24; [archive](milestones/v0.2-ROADMAP.md).
- ✅ **v0.3 Save States & Host Contract** — Phases 16–19; shipped 2026-10-31; [archive](milestones/v0.3-ROADMAP.md).
- ⚠️ **v0.4 Evidence Floor** — administratively closed 2026-11-17 after the qualified v0.4.0 release. Seven of eight requirements are complete; FIXT-01 remains Pending. Phase 24 Task 7, current verification for Phases 20/21/23.1, and D-103's exact-final-head suite are deferred and disclosed; [archive](milestones/v0.4-ROADMAP.md).

## Next

No new milestone is active. v0.4 remains administratively closed under D-209; Phase 24 recovery stays in its sole existing plan. D-223 replaces the failed D-222 immutable-loader route: independently check/commit the amended plan, develop and freeze one gate-only replacement, then continue T25's valid duplicate-job and bounded-waiter corrections and T26's exact-head qualification/conditional protected merge. The direct D-222 gate self-test passed 26 controls; its immutable launch failed because the executed globals were not a registered module and lacked `__file__`. Keep the two-changed-candidate maximum and require a concrete in-scope candidate-one matrix failure plus causal fix before candidate two. After exact-head merge/reconciliation, run active-scope automated Phase 24 verification and finish the D-209-compatible v0.4 audit/override completion/cleanup. Preserve D-209 statuses, FIXT-01 Pending, the failed unreplayed Acid2 result, Task 7 deferral, D-103's broad-suite restriction, existing contexts/coverage/protection and pinned archive snapshots. Do not start v0.5 during this route. Keep this worktree and both automatic-advance flags false until reconciliation.

## Recovery Phase

### Phase 24: Resolve remaining v0.4 evidence and verification gaps

**Status:** D-223 updates the sole Phase 24 plan after the D-222 immutable-loader self-test failed. Its independent check and planning-boundary commit are next. T18–T23 and rejected candidates remain preserved history; no new candidate push or matrix has occurred since D-220. Preserve D-209 accepted requirement gaps.
**Goal:** Repair the immutable gate execution context in one replacement gate, correct the D-221 waiter defects, and qualify/merge only the exact freshly reviewed candidate through existing protection. Then record active Phase 24 verification and finish the D-209-compatible v0.4 lifecycle without changing accepted gaps.
**Requirements:** []
**Requirement boundary:** This recovery does not reassign requirements or change their statuses; the archived v0.4 tracker remains authoritative.
**Depends on:** Phase 23.1 (historical)
**Plan cap:** 1 existing ordinary plan; create no phase or additional plan.
**Success Criteria** (what must be TRUE):
  1. A single gate-only replacement is pinned as a child of the checked D-223 plan; its registered-module loader executes only verified original gate bytes, and both direct and immutable self-tests pass before T25/T26.
  2. Missing, malformed, stale, substituted or ambiguous source, qualification, review, provenance, history, PR, protection or context evidence denies before reservation or promotion; the local guard makes no server-side enforcement claim.
  3. Valid duplicate-name fixtures pass schema validation first, then exercise the duplicate-name WAIT predicate; malformed/duplicate-ID cases remain separate refusals.
  4. Every GitHub waiter child receives only the remaining original monotonic deadline; timeout and exhausted budget remain transient uncertainty/fail-closed, without relaxing the 5100-second deadline or existing test limits.
  5. Keep the existing ten CTest identities and required contexts; run cheap syntax/scope/direct controls before serial focused CTests, with hygiene last. Do not run the D-103 broad suite; add no dependency, fixture effect or CTest identity.
  6. A maximum of two changed, locally qualified, independently code/security-reviewed matrix candidates is allowed; candidate two requires a concrete in-scope first-matrix failure and causal fix. Merge only the identical reviewed head with all required contexts green under current branch protection.
  7. Record actual queue/dependency waits, job/step durations, timeout headroom and package-step behavior. Do not weaken coverage or release gates; assess optimization from measured CI evidence.
  8. Generate an active-task SUMMARY with `requirements-completed: []` and pass automated Phase 24 verification for T24–T26 only; preserve FIXT-01 Pending, Task 7 deferred, Acid2 failed/unreplayed, D-103 unfulfilled and all D-209 dispositions.
  9. Complete the v0.4 audit with `gaps_found` and `override_closeout`, preserve the D-209 archive snapshots byte-for-byte, reconcile reviewed work onto main, and finish with clean status. Do not start v0.5 in this route.
**Plans:**
- [ ] 24-01-PLAN.md — D-223 T24–T26: registered-module immutable gate replacement, duplicate/deadline corrections, guarded exact-head qualification, automated phase verification, and D-209-compatible milestone closeout; earlier candidates remain preserved history.
