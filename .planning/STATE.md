---
gsd_state_version: "1.0"
milestone: v0.3
milestone_name: Save States & Host Contract
current_phase: 19
current_phase_name: Qualified v0.3.0 Release
status: executing
stopped_at: Completed 19-01-PLAN.md
last_updated: "2026-10-29T18:33:12.943Z"
last_activity: 2026-10-29
last_activity_desc: Plan 19-01 complete; ready for 19-02
state_head: 6b35be140b9c5823f0a1866601e8133cb012525b
progress:
  total_phases: 4
  completed_phases: 3
  total_plans: 34
  completed_plans: 28
  percent: 75
current_plan: 2
---

# Project State

## Project Reference

See: [PROJECT.md](PROJECT.md) (updated 2026-10-24)

**Core value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Current focus:** Phase 19 — Qualified v0.3.0 Release

## Current Position

Phase: 19 (Qualified v0.3.0 Release) — EXECUTING
Plan: 2 of 7
Status: Ready to execute
Last activity: 2026-10-29 — Plan 19-01 complete; ready for 19-02

Completed stage: **Phase 19 execution, plan 19-01**. [19-01-SUMMARY.md](phases/GB-19-qualified-v0-3-0-release/19-01-SUMMARY.md) records the four task commits and automated evidence for timeout-ledger citations, release-head object retention, player linkage and CI trust pins. The six former `release_bound` rows and RM-031 linkage findings are closed; two SDL menu-shortcut tests remain unverified on the available headless host. The exact v0.3.0 tag is not published, so REL-01 remains pending. Next stage: **Phase 19 execution, plan 19-02 — Review leftovers and state conversion**. Run Wave 1 serially (19-02 then 19-03), then continue the planned waves; execution stops at the PR B boundary and then routes to `/gsd-verify-work 19`. Exact next command: `/gsd-execute-phase 19`, when the owner chooses. Both automatic advance flags stay false.

Prior stage: **Phase 18 verification (verify-work)**. [18-UAT.md](phases/GB-18-player-save-slots-and-host-contract/18-UAT.md) closes 73/73 deliverables automatically: zero human checkpoints, `verify-uat-closure.py` with 21 controls. [18-VERIFICATION.md](phases/GB-18-player-save-slots-and-host-contract/18-VERIFICATION.md) re-verified `passed` 4/4 at the final code head `abd8ceed`. [18-SECURITY.md](phases/GB-18-player-save-slots-and-host-contract/18-SECURITY.md) has `threats_open: 0` (33/33 closed, AR-18-01). [18-VALIDATION.md](phases/GB-18-player-save-slots-and-host-contract/18-VALIDATION.md) is Nyquist-compliant. Review-fix round 2 of 2 fixed IN-01..IN-09, so all 15 findings are `fixed`. Verification also found and fixed `test_budget` (`135c6cc5`), `planning_labels` (`70a29b29`) and the hosted-only `contract_rev_wiring` CMake 3.x format gap (`abd8ceed`; LESSONS GB-GSD-030, GB-CI-013). Full suite 1678/1678 at `abd8ceed`. Exact-head CI on PR #132 at `abd8ceed`: 41 pass, 0 fail, 3 skips confirmed covered (`planning-checks` runs only on planning-only changes; `macos-player-package` passed on the PR run). Pre-existing player-build linkage debt is RM-031, a Phase 19 entry item. Next stage: **Phase 19 — Qualified v0.3.0 Release, discussion**. Command: `/gsd-discuss-phase 19`, run only when the owner chooses. Phase 19 entry blockers: RM-027, WR-C03, the `candidate-performance` re-citation, and RM-031. Both automatic advance flags stay false.

Prior phase evidence: **Phase 16 execution** — plans 16-01..16-07 merged; [16-VERIFICATION.md](phases/GB-16-tune-up-and-v0-2-debt-closure/16-VERIFICATION.md) `passed` 5/5 (TUNE-01..06); [16-VALIDATION.md](phases/GB-16-tune-up-and-v0-2-debt-closure/16-VALIDATION.md) Nyquist-compliant; code review 0 critical / 5 warning / 4 info, all deferred to Phase 17 as RM-030 ([16-REVIEW-DISPOSITION.md](phases/GB-16-tune-up-and-v0-2-debt-closure/16-REVIEW-DISPOSITION.md)). Boundary commit `boundary_sha: 92364c78ac002b8e199ca7e6cad4130701fe98ba`; `verify-v03-dispositions.py --check ... --rev 92364c7` passes (rows=26 pending=0 closed=6). Deviations (owner-waived gap rounds #116/#118/#120, post-tag fixes #123/#124/#125, four review issues with #122 approved) are in D-112.

Prior phase evidence: **Phase 16 verification** — [16-UAT.md](phases/GB-16-tune-up-and-v0-2-debt-closure/16-UAT.md) closes 51/51 deliverables automatically (zero human checkpoints, `verify-uat-closure.py` 21 controls); full suite 1234/1234 at `be4cee8`; goal verification re-run at the final head `passed` 5/5 (the prior report was stale only because `boundary_sha` was appended to 16-07-SUMMARY.md, LESSONS GB-GSD-027); [16-SECURITY.md](phases/GB-16-tune-up-and-v0-2-debt-closure/16-SECURITY.md) `threats_open: 0` (32 threats; T-16-22/T-16-25 owner-accepted under D-112 as AR-16-01/02, gate code added to RM-030).

Completed stage: **Phase 17 execution, plans 17-01..07 implemented with targeted evidence**. Settled full suite at `7cb5739`: 1481/1482 pass; the only failure, `test_budget` (two plan-07 advisory perf controls declared 120 s TIMEOUTs without an allowlist row), is fixed in `5701130` by restoring the base 60 s budget, and test_budget plus both controls pass. The hosted fuzz timeout at `b3e57bc` (per-byte path comparisons in state validation) is fixed in `f0591f4`; full suite 1482/1482 there. Plan 05 fork-harness integration fixes (Windows Git path separators, invariant-aware poison, bounded omission probes, separate child streams) landed through `7cb5739`; hosted checks are green at `0c8fd56` after Windows portability fixes. No crash counts as a semantic kill. Plan 17-08 implemented at `9de6089` (full suite 1486/1486). Plan 17-10 implemented; full suite 1488/1488 at `716aab2`; IN-03 closed in `fdce605`/`50fda9e` (job timeout cited from hosted dry run 40749683012). Next stage: **Phase 17 — Native Save State Core, wave 11 / plan 17-11**. Resume command: `/gsd-execute-phase 17`. One plan and phase qualification remain. Next feature phase: **18 — Player Save Slots and Host Contract**, after Phase 17 execution/verification and owner choice.
Both `workflow.auto_advance` and `workflow._auto_chain_active` remain false; stop at the Phase 17 boundary.

Runtime configuration (2026-10-26): owner switched future OpenGSD work to Codex, retaining the `adaptive` profile. Heavy/opus uses `gpt-6.1-sol` at `high` effort; standard/sonnet and light/haiku use `gpt-6-luna` at `xhigh` effort. Project `.planning/config.json` is authoritative; resolve each role's model and effort before dispatch. This configuration change does not start Phase 17.

Runtime configuration (2026-10-28): owner moved OpenGSD work from Codex to Claude Code (`runtime: claude`, `adaptive` profile; opus/sonnet/haiku resolve to `claude-opus-5-5`/`claude-sonnet-5-5`/`claude-haiku-5-5`). The stale Codex `milestone.lock` and its uncommitted `state.json` route regression are left for owner cleanup.

Runtime configuration (2026-10-29, current): owner switched future OpenGSD work back to **Codex**, retaining the **adaptive** profile. Heavy/opus uses `gpt-6.1-sol` at `high` effort; standard/sonnet and light/haiku use `gpt-6-luna` at `xhigh` effort. Project `.planning/config.json` is authoritative; retain the Claude mappings for future switches and resolve both model and effort before each dispatch. Completed workflow stage remains **Phase 19 planning**; next is **Phase 19 — Qualified v0.3.0 Release, execution**, command `/gsd-execute-phase 19`, only when the owner chooses. Both automatic advance flags remain false.

## Accumulated Context

### Decisions

Historical decisions, including the per-plan records of Phases 1-16, moved to [v0.2-STATE-ARCHIVE.md](milestones/v0.2-STATE-ARCHIVE.md). Adopted choices live in [DECISIONS.md](context/DECISIONS.md); new decisions are appended below by the runtime.
- [Phase 18]: 18-01: grammar defects are reported in argv order; a value beginning with -- is missing-value; = in any -- argument is equals-form
- [Phase 18]: 18-01: gabbaboy_host links into every target compiling src/runner/main.c (test_runner, joyp mutant runner); it names no core
- [Phase 18]: 18-02: empty-value grammar case runs in the python harness because CMake drops empty list elements; API-surface controls live in the checker's controls mode
- [Phase 18]: 18-03: gbb_get_input_clock reports last_queued_half_dots as the instance time when the queue is empty, so max(now, last) is always the earliest admissible event time
- [Phase 18]: D-11 discretion (18-04): a failed flush is retried 16 frames later (retry_after_frame = frame + 16); flushed advances only after writer success
- [Phase 18]: 18-04: host-only mutant runners are named gabbaboy-runner-hostvariant-* because verify-core-linkage.py requires every *mutant* executable to link a mutant core
- [Phase 18]: 18-04: mutant-runner CTests pin the failure reason (not only FAIL scenario) so a harness crash cannot satisfy them
- [Phase 18]: 18-05: a slot load validates in a scratch instance built from the store's own ROM copy before any write, so the battery preload precedes the live gbb_load_state (D-23 order) and a refusal touches no file (W-5)
- [Phase 18]: 18-05: a restored queue above 56 events or 140,448 x 64 half-dots ahead is UNSAFE_INPUT so the player's eight post-load releases fit the 64-event queue (discretion, W-6); the undo-source backup failure reads 'Undo not applied: undo backup failed; nothing changed'
- [Phase 18]: 18-05: host_save_io_read_bounded shares one open_regular_nofollow with the exact reader (the 18-04 follow mutant anchors on a single open); slot mutant executables are named *variant* for verify-core-linkage.py
- [Phase 18]: 18-06: the slot message lives in its own player field and is combined with save_status when the title is formatted, because the title shows save_status instead of status while a battery-save failure is active
- [Phase 18]: 18-06: player_input_rebase marks all eight buttons for release and apply_slot_load queues them through player_input_retry_focus_releases at the same host time, so the main loop retries a release the queue cannot take yet
- [Phase 18]: 18-06: A2 is resolved by an automated Cocoa menu scan that forces the cocoa video driver (the package lane exports SDL_VIDEO_DRIVER=dummy), with a seeded Command-S control
- [Phase 18]: 18-06: the Battery RAM changed hint is skipped while a slot message is shown, so a load's message is not wiped on the next frame
- [Phase 18]: 18-07: exit table rows are X(code, IDENT, name, meaning); the boundary poll runs before frame 0 and after each frame's cadence flush and pacing wait; a failed final flush and a core stop exit 1 with status=failure
- [Phase 18]: 18-07: SA_RESETHAND is asserted by behaviour (disposition back to SIG_DFL after one delivery) because Darwin does not report the flag from a sigaction query
- [Phase 18]: 18-07: gbb_host_mutant_library takes extra anchor pairs via ARGV (C replacements contain semicolons); the partial-frame decoy removes the boundary poll so every stop is mid-frame
- [Phase 18]: 18-08: save-format rows ascend by (type, ram_code) as numbers, so MBC5 lists RAM code 0x04 (128k) before 0x05 (64k); the freeze CTest accepts baseline=none or baseline=vX.Y.Z
- [Phase 18]: 18-08: --print-save-format prints save_format=none bytes=0 for a no-battery cartridge (A5); none is a sentinel, not an id, and never appears in save_formats rows
- [Phase 18]: 18-08: a re-sorted canonical JSON is still self-consistent, so canonical form also requires keys in the written order (REJECT non-canonical); the table claims no emulator interoperability (REJECT interop-claim)
- [Phase 18]: 18-09: installed_host_smoke is a stdlib Python harness (NUL bytes cannot be held in CMake strings); the interop-claim scan is its own planning-labelled script
- [Phase 18]: 18-09: five planner discretion choices recorded as D-115..D-119 in DECISIONS.md; Linux LeakSanitizer fix for deliberately failing mutants routed to 18-02 and 18-05 (detect_leaks=0)
- [Phase 19]: Release-head object retention applies to tree-equal citations only; plain rows can cite merged PR heads no longer present in the checkout.
- [Phase 19]: Keep package settings unchanged and use a distinct Debug player build for linkage identity checks.
- [Phase 19]: REL-01 remains pending until exact v0.3.0 publication and readback; 19-01 closes only release-entry work.

### Pending Todos

None outside the roadmap.

### Blockers/Concerns

Historical blockers and concerns (v0.1 and v0.2 audits, triage and phase notes) moved to [v0.2-STATE-ARCHIVE.md](milestones/v0.2-STATE-ARCHIVE.md). Phase 17 plans fit STATE-01..06 and RM-026/028/029/030 within 11 primary plans plus one reserved gap slot. Header layout and temporary all-path horizon feasibility are researched; permanent all-wrapper closure, body-size and inductive audio bounds remain ordered execution gates. Unproved correctness/security invariants require rescope. RM-027 is a named Phase 19 entry blocker, not a closed item.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|

### Roadmap Evolution

- Phase 06.1 inserted after Phase 6: Address v0.1 tech debt: CI workflow info items and audio consumer coverage (URGENT)
- 2026-10-10: v0.2 roadmap created — Phases 7–15 continue v0.1 numbering. Order follows research/v0.2/SUMMARY.md: acceptance + DMG baseline (7); seam merged with MBC5 and MBC2 (8, MBC5/MBC2 plans parallel after the seam plan); MBC3 + RTC + loader matrix + new-mapper continuation (9); CGB profile/banking (10); colour PPU + player colour (11); double speed (12) and HDMA (13) kept separate and sequential; CGB-E qualification + corpus (14); CGB acceptance, ledger and release (15). Deep phase research flagged for 9, 11, 12, 13, 14. Rights gates: G5/G2 on 7; G1 on 9, 11, 14; G3 on 9; G4 on 11.
- Phase 15.1 inserted after Phase 15: Release Hardening and Milestone Debt Closure; owner chose recommended resolve-first closeout (URGENT)
- 2026-10-24: v0.2 milestone completed and archived (override_closeout). The ROADMAP is collapsed to milestone groupings, and the phase records stay in place because CTest reads them.
- Phase 17 edited: Discussion reconciled existing RM-026/028/029/030 entry obligations into Phase 17 success criteria 6–8 and requirement traceability; scope remains four phases, cap 12 (11 primary plus gap slot). No implementation or auto-advance.

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| uat_gaps | GB-14-cgb-e-model-qualification-and-corpus/14-UAT-REVIEW.md | clean (0 pending scenarios; scanner false positive) | 2026-10-24 | v0.2 |

The archived v0.2 requirements are in [v0.2-REQUIREMENTS.md](milestones/v0.2-REQUIREMENTS.md) (28/28 complete). Deferred v0.3 items (STATE-01, INT-01) and later direction are in its Future section and [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md).

## Session Continuity

**Last session:** 2026-10-29T18:33:12.831Z
**Stopped at:** Completed 19-01-PLAN.md
**Resume file:** .planning/phases/GB-19-qualified-v0-3-0-release/19-02-PLAN.md

Completed stage: **Phase 18 — Player Save Slots and Host Contract: planning**. Phase 18 planned: 9 plans in 8 waves (18-01..18-09; gap slot 18-10 reserved, cap 10). Research, pattern map and validation strategy committed; plan checker ran 3 iterations (15 → 5 → 3 warnings, 0 blockers at the end); the final 3 warnings plus advisories were applied as narrow edits without a 4th checker pass (passed with override, iteration cap reached). Requirements 4/4 and decisions 31/31 covered. Plans: [18-01..18-09](phases/GB-18-player-save-slots-and-host-contract/); waves serialize the plans sharing `tests/expected-tests.txt` (GB-CART-003), only 18-06 ‖ 18-07 run in parallel. Branch `gsd/phase-18-player-save-slots-and-host-contract` from `f4082a6`. Plan 18-01 (host-mode tracer) is complete at `8261d35` with SUMMARY `71e0232`. Plan 18-02 (host grammar, stem and Windows-gate negatives; D-04 API and dirty-list checks) is complete at `5292988` with SUMMARY `eccc214`; full suite 1526/1526. Plan 18-03 (`gbb_get_input_clock` getter, mutants, installed consumers, API docs) is complete at `6a52d61` with SUMMARY `7ae5004`; full suite 1535/1535. Plan 18-04 (host cadence, stale-temp sweep, writer fault seams, hostile save-dir/import sweep) is complete at `8335fba` with SUMMARY `ac01321`; full suite 1581/1581. Plan 18-05 (SDL-free slot engine) is complete at `4c9962b` with SUMMARY `f246619`; full suite 1610/1610. Plan 18-06 (player slot keys, status line, input rebase, help/limitations, macOS menu-shortcut scan) is complete at `67bb2bd` with SUMMARY `60acda6`; player suite 106/106 through `--build-package`, main suite 1610/1610 after reconfiguring the revision-pinned tests. Plan 18-07 (SIGTERM/SIGINT/SIGHUP handling, exit table, real-signal harness with decoys, core no-signal check) is complete at `64c6749b` with SUMMARY `1ff9698a`; full suite 1628/1628. Plan 18-08 (`docs/host-contract.json`, `--print-save-format`, save-format completeness/produced-file/freeze checks with 36 seeded controls) is complete at `c2239bef` with SUMMARY `5266f422`; full suite 1637/1637 at `befd624c`. Next plan within Phase 18: **18-09 — installed host smoke, host-contract and slot docs with contract checks, phase-tail qualification** (wave 8, the last primary plan). Next phase: **18 — Player Save Slots and Host Contract, execution**. Next command: `/gsd-execute-phase 18`, only when the owner chooses. The v0.3.0 release-please PR stays unmerged during Phase 18. Both automatic advance flags stay false.

## Operator Next Steps

- Completed stage: **Phase 18 verification (verify-work)**. [18-UAT.md](phases/GB-18-player-save-slots-and-host-contract/18-UAT.md) closes 73/73 deliverables automatically: zero human checkpoints, `verify-uat-closure.py` with 21 controls. [18-VERIFICATION.md](phases/GB-18-player-save-slots-and-host-contract/18-VERIFICATION.md) re-verified `passed` 4/4 at the final code head `abd8ceed`. [18-SECURITY.md](phases/GB-18-player-save-slots-and-host-contract/18-SECURITY.md) has `threats_open: 0` (33/33 closed, AR-18-01). [18-VALIDATION.md](phases/GB-18-player-save-slots-and-host-contract/18-VALIDATION.md) is Nyquist-compliant. Review-fix round 2 of 2 fixed IN-01..IN-09, so all 15 findings are `fixed`. Verification also found and fixed `test_budget` (`135c6cc5`), `planning_labels` (`70a29b29`) and the hosted-only `contract_rev_wiring` CMake 3.x format gap (`abd8ceed`; LESSONS GB-GSD-030, GB-CI-013). Full suite 1678/1678 at `abd8ceed`. Exact-head CI on PR #132 at `abd8ceed`: 41 pass, 0 fail, 3 skips confirmed covered (`planning-checks` runs only on planning-only changes; `macos-player-package` passed on the PR run). Pre-existing player-build linkage debt is RM-031, a Phase 19 entry item. Next stage: **Phase 19 — Qualified v0.3.0 Release, discussion**. Command: `/gsd-discuss-phase 19`, run only when the owner chooses. Phase 19 entry blockers: RM-027, WR-C03, the `candidate-performance` re-citation, and RM-031. Both automatic advance flags stay false.
- Phase 18 execution is complete (plans 18-01..18-09, gap slot 18-10 unused): full phase1 suite 1650/1650 at `3c148865`, 18-09 SUMMARY committed. Next stage: verification of **Phase 18 — Player Save Slots and Host Contract**. Command: `/gsd-verify-work 18`, run only when the owner chooses, after code review and the PR's exact-head CI (`linux-asan-ubsan`, `native-windows-x64`, `macos-player-package`) are recorded as the 18-09 post-CI addendum. This is not Phase 19. Do not start Phase 19 automatically; RM-027 remains a Phase 19 entry blocker.
- Phase 18 execute-phase gates ran at `d3b0f0dd`: full build + CTest 1650/1650 (`build/18-gate-ctest-d3b0f0d.log`); code review [18-REVIEW.md](phases/GB-18-player-save-slots-and-host-contract/18-REVIEW.md) 0 critical / 6 warning / 9 info, all `open` in [18-REVIEW-DISPOSITION.md](phases/GB-18-player-save-slots-and-host-contract/18-REVIEW-DISPOSITION.md); [18-VERIFICATION.md](phases/GB-18-player-save-slots-and-host-contract/18-VERIFICATION.md) `human_needed`, 4/4 success criteria verified. Open before closure: owner triage of the review findings (WR-03 cross-session preload-backup overwrite first, then WR-01 ignored rollback/clock results; D-102–D-105 allow at most 2 review-fix rounds, and an unresolved correctness finding forces a rescope or gap slot 18-10), and the PR's exact-head hosted CI. Next command: `/gsd-code-review 18 --fix` (review-fix round 1), then `/gsd-verify-work 18`. The phase is not marked complete.
- Review-fix round 1 of at most 2 is complete (head `0da3c137`). `/gsd-code-review 18 --fix` fixed WR-01..WR-06 in six commits (`95294c32`, `8014d1a8`, `cfc474a8`, `0ea6f507`, `919fe641`, `aea9eb6b`) plus a WR-03 follow-up `e94174e3` (a failed battery-guard write now sets `guard_unsaved` and warns in the status message). Each fix has a test with a negative control. Report: [18-REVIEW-FIX.md](phases/GB-18-player-save-slots-and-host-contract/18-REVIEW-FIX.md) (`all_fixed`). [18-REVIEW-DISPOSITION.md](phases/GB-18-player-save-slots-and-host-contract/18-REVIEW-DISPOSITION.md): 6 fixed, 9 Info (IN-01..IN-09) open and not triaged. Owner decisions 2026-10-29: pausing input on `PLAYER_SLOT_RESTORE_FAILED` (WR-01) is accepted, and so is the third per-ROM pref file `<prefix>-battery-guard.bin` (WR-03). Local evidence: macOS `build` slot/doc/inventory 78/78 and `build-player` slot/player 150/150 at `e94174e3`. The fixer's full suite showed 2 failures from a stale configure, which passed after a reconfigure. `build-player` `core_linkage_links`, `core_linkage_controls` and `test_budget` fail identically on the pre-fix base `72a88d97`, so they are pre-existing. A full-suite re-run at the final head has not been done. Other tests in `tests/CMakeLists.txt` still capture the configure-time HEAD (same class as WR-04; out of scope). Still open before closure: the branch is 88 commits ahead of origin with no PR, so the exact-head hosted CI (`linux-asan-ubsan`, `native-windows-x64`, `macos-player-package`) has not run. Completed stage: **Phase 18 code review fix (round 1)**. Next stage: **Phase 18 — Player Save Slots and Host Contract, verification**. Command: `/gsd-verify-work 18`, run only when the owner chooses. This is not Phase 19. The phase is not marked complete.

## Performance Metrics

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 18 P01 | 15min | 2 tasks | 15 files |
| Phase 18 P02 | 9 min | 2 tasks | 10 files |
| Phase 18 P03 | 9 min | 2 tasks | 9 files |
| Phase 18 P04 | 20min | 3 tasks | 13 files |
| Phase 18 P05 | 21 min | 3 tasks | 13 files |
| Phase 18 P06 | 26 min | 3 tasks | 9 files |
| Phase 18 P07 | 18 min | 3 tasks | 13 files |
| Phase 18 P08 | 17min | 3 tasks | 13 files |
| Phase 18 P09 | 50 min | 3 tasks | 18 files |
| Phase 19 P01 | 35min | 4 tasks | 8 files |
