---
gsd_state_version: "1.0"
milestone: v0.4
milestone_name: Evidence Floor
current_phase: 24
current_phase_name: Resolve remaining v0.4 evidence and verification gaps
current_plan: Phase 24 D-210 Task 8 recovery blocked after its single independent review; Task 7 remains unfinished
status: blocked
stopped_at: D-210 review found required CI would execute admitted game ROMs, outside the authorized no-ROM scope
last_updated: "2026-11-17T21:26:12Z"
state_head: 054f2d0d80f4e15c70d43408c026280b93ec6b08
progress:
  total_phases: 6
  completed_phases: 5
  total_plans: 33
  completed_plans: 32
  percent: 97
last_activity: 2026-11-17
---

# Project State

## Current Position

**Milestone stage:** v0.4 — Evidence Floor was administratively closed with accepted gaps under D-209. D-210 Task 8 implementation and focused checks passed at reviewed candidate `054f2d0d80f4e15c70d43408c026280b93ec6b08`, but its one independent review is `issues_found`: the required native matrix executes admitted game ROMs, violating the explicit no-ROM limit. Its review allowance is spent; no PR or matrix was opened/run. See `/private/tmp/gabbaboy-d210-review-054f2d0.md`. Original requirement outcomes, accepted gaps, and qualified v0.4.0 release are unchanged.
**Requirements:** 7/8 original requirements are complete. RIGHTS-01, DIAG-01 and DIAG-02 are complete for the exact admitted diagnostic scope; FIXT-01 remains Pending and deferred.
**Phase state:** Phase 24 Task 7 and its plan summary remain incomplete; Task 8 implementation and eight focused CTests pass, but the sole review found one Critical scope blocker and one Warning. Phase 20, 21, and 23.1 verification is stale. No PR or protected matrix was started. These remain disclosed gaps, not passes.
**Next route:** The owner acts next with `$gsd-discuss-phase 24` to resolve the no-game-ROM versus required-CI conflict and decide whether any new recovery scope, fix, review, and matrix are authorized. Do not push/open a PR or start required CI under D-210. If any future scope passes and is reconciled to clean `main`, then start v0.5 DMG PPU Timing with `$gsd-new-milestone`. Both automatic-advance flags remain false.

**Final diagnostic evidence:** The Acid2 lane ran once: DMG-on-DMG and CGB-on-CGB matched; DMG-on-CGB differed at all 19,840 compared pixels. The failed result was not replayed and its cause is unproven. One `div_inc_timing_a` case passed for the DMG-CPU-B software model; one case was eligible/executed and 512 remain excluded. Details are in [Phase 24 closeout](phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CLOSEOUT.md).

The preceding D-206 and D-207 blocks are historical checkpoints. D-208 reconciled the literal diagnostic criteria; D-209 is the current owner direction to close v0.4 with FIXT-01 and stale/incomplete verification disclosed.

## Qualified Release

[v0.4.0](https://github.com/szTheory/gabbaboy/releases/tag/v0.4.0) was published 2026-11-14T00:04:34Z by [43526085579, attempt 1](https://github.com/szTheory/gabbaboy/actions/runs/43526085579). Product/tag source S is `3de1b0e427f37a202be4469dd818266f359c8b20`; trusted publication control G5 is `fbea1e2cc70f7c2ab9ea5820fa92ca18ddf997e8`. These are distinct from the later documentation/lesson/boundary commits.

Fresh readback reconciles all 22 public downloads, actual pre-publish inventory, preserved original 20 tuples/notes, source archive, final receipt/checksums, product positives/game-insertion refusals, six owner evidence families and actual native consumer byte bindings. REL-01 is complete. The one conditional publication request is spent; no retry, tag move or asset replacement is authorized. [23-EVIDENCE.md](phases/GB-23-qualified-v0-4-0-release/23-EVIDENCE.md) records the actual source/run/receipt links and retained failure chronology.

## Deferred Items

Items acknowledged at the v0.4 closeout, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| uat_gaps | GB-21 / 21-UAT-EVIDENCE.md | unknown; no open scenarios | 2026-11-17 | v0.4 |
| uat_gaps | GB-23 / 23-UAT-EVIDENCE.md | unknown; no open scenarios | 2026-11-17 | v0.4 |
| deferred_items | GB-21 / deferred-items.md: hosted PR qualification protocol | acknowledged; carried-forward note | 2026-11-17 | v0.4 |

Two items had already been acknowledged by an earlier closeout; the audit recorded five acknowledged items total after this close.

## Preserved Limits

FIXT-01 remains Pending: neither Potion Panic nor µCity has a complete source/build/ROM/header/mode/runtime chain. Do not introduce a third game candidate under the v0.4 requirement. Do not replay the Acid2 comparison or claim its cause. The v0.4.0 tag/assets and published claims remain unchanged. No hardware, perception, mode-3 timing, general compatibility, Linux player, Steam Deck, or live Playstead claim is established by this closeout.

The exact-final-head D-103 gate remains unfulfilled. Phase 20, 21, and 23.1 verification is stale; Phase 24 Task 7 is incomplete. These remain gaps, not passes. D-210's one review found that the required native matrix executes `fixtures/libbet/libbet.gb`, conflicting with its no-admitted-ROM limit; a warning also found that two positive notice-overlay controls inflate the negative-control count. No PR or matrix was started. The review allowance is exhausted, so no fix, review, or CI retry is authorized until a new owner scope. No Acid2 replay, release/tag/asset change, broad local suite, or worktree cleanup. Both automatic-advance flags remain false.

## Owner Handoff

Completed stage: **Phase 24 Task 8 implementation and focused checks** after the v0.4 D-209 closeout. The sole D-210 review of candidate `054f2d0d80f4e15c70d43408c026280b93ec6b08` found the no-ROM/required-CI conflict and a mislabeled control count. No PR/CI/merge occurred; do not switch to `main` or remove this worktree. The owner acts next with `$gsd-discuss-phase 24` to decide a new bounded scope or leave recovery stopped. Keep Task 7, FIXT-01, and the accepted gaps unchanged.

## Accumulated Context

### Roadmap Evolution

- Phase 23.1 complete; owner chose to keep v0.4 open after the refreshed `gaps_found` audit and authorized one Phase 24 rescope under D-205. The single Phase 24 plan passed independent review. No requirement gaps were accepted and no milestone archival is authorized. Next: `$gsd-execute-phase 24`; fixture/rights actions and all other preserved limits remain outside scope.
- Phase 23.1 inserted after Phase 23: Close v0.4 requirement and verification gaps (URGENT)
- Phase 23.1 Task 5 and the sole D-196 review completed; two Critical checker issues remain open. Owner acts next with `$gsd-discuss-phase 23.1` to define bounded recovery, then `$gsd-autonomous --from 23.1` after scope authorization. The milestone remains open; finish on a clean `main` after approved reconciliation.
- Phase 23.1 recovery-scoped: D-198 records one Task 6 and one independent review for CR-01/CR-02; next route is $gsd-autonomous --from 23.1.
- Phase 23.1 D-198 Task 6 and its sole review completed. The review found a Critical YAML block-scalar U+2028 bypass; the cap is exhausted, Phase 23.1 is incomplete, and no verifier ran. Owner next runs `$gsd-discuss-phase 23.1` to decide on a new scope; no next phase/milestone is selected.
- Phase 23.1 recovery scope authorized: D-199 completes the recovery discussion and authorizes exactly one final same-plan Task 7 plus one independent review for the D-198 YAML block-scalar bypass. Resume with $gsd-autonomous --from 23.1; if the review finds a Critical or new blocker, stop before phase verification.
- Phase 23.1 D-200 recovery authorized: One same-plan Task 8 and one exact-candidate review; plan 4fbc33d passed static plan checks. Task 8 implementation has not started; next: $gsd-autonomous --from 23.1.
- Phase 23.1 blocked after Phase 23: D-200 sole exact-candidate review found Critical CR-03 and CR-04 after closing D-199 CR-01 and D-196 CR-02; the one-review allowance is exhausted, no phase verifier or further correction/review follows, and the owner acts next with $gsd-discuss-phase 23.1.
- Phase 23.1 verification stopped: Task 11 and the sole D-203 independent review are complete and clean; Nyquist/security pass and the existing Phase 23 UAT has no gaps. Stop at Phase 23.1's configured regression gate because it runs the broad phase1 build and full CTest suite, prohibited by D-103/D-203. Owner next: -discuss-phase 23.1 to decide a bounded gate or explicit scope change; no phase verifier ran.
- Phase 23.1 verification stopped: Task 11 and the sole D-203 independent review are complete and clean; Nyquist/security pass and the existing Phase 23 UAT has no gaps. Stop at Phase 23.1 regression gate because the configured command runs the broad full preset suite prohibited by D-103/D-203. Owner next: $gsd-discuss-phase 23.1 to decide a bounded gate or explicit scope change; no phase verifier ran.
- Phase 23.1 focused regression gate passed: The approved one-time gate override ran only plan_cap and planning_hygiene_controls; both passed. The original full-suite workflow.test_command was restored, the prohibited broad suite did not run, and the phase verifier is next. All four requirements remain Pending and v0.4 open.

## Performance Metrics

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 23.1 P01 | about 57 min | 3 tasks | 9 files |
| Phase GB-23.1 P01 | about 34 min (D-194 amendment) | 3 tasks | 9 files |
| Phase 24 P01 | 98 min | 3 tasks | 8 files |

## Decisions

- [Phase 23.1]: D-193 permits only the exact active v0.4 phase set and cap allocation; all normal caps remain unchanged.
- [Phase 23.1]: D-141's historical synthetic-plus-metadata scope is documented without satisfying FIXT-01, RIGHTS-01, DIAG-01, or DIAG-02.
- [Phase GB-23.1]: D-194 permits exactly one same-plan correction and independent review for CR-01, CR-02, and WR-01; all other D-193 stops remain.
- [Phase 23.1]: D-195: one final same-plan CR-01/CR-02 recovery and independent review authorized; preserve all other stops; next route is -plan-phase 23.1 --skip-research.
- [Phase 23.1]: D-195: one final same-plan CR-01/CR-02 recovery and independent review authorized; preserve all other stops; next route is $gsd-plan-phase 23.1 --skip-research. Use this corrected route; the immediately preceding note had a shell-expanded command.
- [Phase 23.1]: D-196 authorizes exactly one same-plan Task 5 for the two D-195 findings, followed by one independent review of its committed candidate. The plan passed review; next: -execute-phase 23.1 (Task 5 only). Any unresolved Critical/correctness/security finding or new blocker stops the phase without further code, review, or phase verification.
- [Phase 23.1]: D-196 route correction: an earlier state-entry attempt expanded the literal dollar sign. The exact current command is `$gsd-execute-phase 23.1`, resuming Task 5 only.
- [Phase 23.1]: D-198 authorizes one same-plan Task 6 for the two D-196 Critical findings and one independent review; next: $gsd-autonomous --from 23.1.
- [Phase 23.1]: D-198 Task 6 checks passed, but the sole review at `12fcb174885d7682cade9c88a5316c00fa4b0c0a` found a Critical YAML block-scalar U+2028 bypass. The review cap is exhausted; no fix or verifier follows. Owner next: `$gsd-discuss-phase 23.1`.
- [Phase 23.1]: D-199 authorizes exactly one same-plan Task 7 for the D-198 YAML block-scalar bypass and one independent review. The current Critical remains open; next: $gsd-autonomous --from 23.1. Stop before phase verification if review finds any Critical or new blocker. — This preserves the one-plan cap and all D-193–D-198 limits while allowing the owner-directed v0.4 continuation. At milestone closeout, reconcile reviewed work to main and verify a clean worktree.
- [Phase 23.1]: D-201 authorizes one formal rescope of the existing plan for CR-03/CR-04, with one correction task and one independent review. — Keep the fixed Phase 22 report contract and standard-library checker; preserve every unrelated D-193–D-200 limit and stop before verification if any Critical remains.
- [Phase 23.1]: D-202 authorizes one same-plan Task 10 for CR-05/CR-06 and one exact-candidate independent review. — Keep the fixed Phase 22 report schema and standard-library checker; preserve all other D-193–D-201 limits and stop before verification if any Critical or new blocker remains.
- [Phase 23.1]: D-203 authorizes exactly one same-plan Task 11 correction for CR-07 and one independent exact-candidate review; preserve every other D-193–D-202 stop and budget. — The owner directed a multi-perspective fan-out and instructed the agent to follow the synthesized recommendation.
- [Phase 24]: Phase 24 assessment keeps each original v0.4 criterion, owner, tracker status, audit status, historical outcome, freshness, boundary, and remaining gate distinct.
- [Phase 24]: D-205 remains the exact one-plan Phase 24 exception within the 40-plan ceiling; the assessment completes no original requirement and does not satisfy D-103.
- [Phase 24]: D-210 authorizes exactly Task 8 in the existing plan: static validation of the exact recorded Acid2 mismatch, exact notice-index reconciliation, and explicit diagnostic `--receipt` refusal. One independent review and one protected PR matrix follow; failures stop without retry. FIXT-01, Task 7, and other D-209 gaps remain.
- [Phase 24]: The configured phase1 tests are restricted to plan_cap and planning_hygiene_controls at the committed candidate; preserve the 30-second timeout and 125-control floor.
- [Phase 24]: D-07–D-10 authorized exactly one same-plan Task 4 and one independent exact-candidate review for the BOM plan-cap bypass. Task 4, the clean review, the two focused CTests, and Phase 24 verification passed; all phase plans are complete. Continue the existing v0.4 authorization with `$gsd-autonomous --from 23.1`, preserving the four Pending requirements and D-103 stop.
- [Phase 23.1]: Phase 23.1 verification remains a historical 18/18 result and stale after Phase 24 changed the shared checker; no new recovery scope is authorized. — Phase 24 passed its own focused checks and verification under D-205. Refreshing Phase 23.1 would conflate its former fifth-phase criterion with the approved six-phase cap. Keep the four requirements Pending, v0.4 open, and D-103 unfulfilled.
- [v0.4 closeout]: D-209 closes the milestone with accepted gaps. RIGHTS-01, DIAG-01, and DIAG-02 are complete for the exact admitted diagnostics; FIXT-01 remains Pending. Phase 24 Task 7, stale verification, and D-103 remain disclosed. The next command is `$gsd-new-milestone` for v0.5 DMG PPU Timing.

## Session

**Last session:** 2026-11-17T21:26:12Z
**Stopped at:** D-210 candidate review; no PR/CI started because required native CI executes admitted game ROMs
**Resume file:** .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/.continue-here.md (historical closeout handoff)

### Blockers
D-210 is blocked after its one review. The required `required-native` matrix executes admitted game ROMs including Libbet, contrary to the D-210 no-ROM limit; reviewer also found two positive notice-overlay cases reported as negative controls. No PR or matrix was started, and no further fix/review/CI cycle is authorized. Owner next: `$gsd-discuss-phase 24` to define a new scope or preserve the stop. Acid2 was not replayed; FIXT-01 stays Pending; Task 7 and v0.4 completion remain incomplete.
