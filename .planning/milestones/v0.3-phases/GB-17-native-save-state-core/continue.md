# Phase 17 continuation

Completed stage: **Phase 17 execution, plans 17-01..07 implemented with targeted evidence**. Settled full suite at `7cb5739`: 1481/1482; the `test_budget` rejection of the two plan-07 advisory perf TIMEOUTs is fixed in `5701130` (base 60 s, measured ~7 s) with the affected tests passing. The hosted ASan fuzz timeout at `b3e57bc` is fixed in `f0591f4` (state path rules resolved once per field); full suite 1482/1482 at `f0591f4`. Windows portability fixes in `be8ec08` and `0c8fd56`; PR130 hosted checks all green at `0c8fd56` (41 pass, 3 path-skipped). Re-verify once at the final phase head.

Plan 17-08 implemented at `9de6089`; full suite 1486/1486 there after `cmake --preset phase1` (stale revision stamp otherwise); hosted checks pending at that head.

Plan 17-09 implemented through `c2c10df`; `e5064c3` fixes the Windows `v02_support_ledger_controls` timeout (GB-CI-012); full suite 1488/1488 at `e5064c3`, hosted pending.

Plan 17-10 implemented through `de7761b`; IN-03 closed in `fdce605`/`50fda9e`: `report-red` job timeout 5 and a provisional `ci-timeouts.json` row cite hosted dry run 40749683012 at `fe4c932`. Open for 17-11/verification: `verify-workflow-policy.py --check --verify-cited` fails `release.yml:candidate-performance` (job renamed to `exact-tag-advisory-paired-performance-observation` before this session; cited run 39406047351 has the old name). `716aab2` fixes the macOS `state_horizon_mutants` timeout; full suite 1488/1488 there.

Next stage: **Phase 17 — Native Save State Core, wave 11 / plan 17-11**. Resume command: `/gsd-execute-phase 17`.

Next feature phase: **18 — Player Save Slots and Host Contract**, after Phase 17 execution/verification and owner choice. Both auto flags remain false. Never start Phase 18 automatically.

Read ten completed summaries and `17-11-PLAN.md` with the existing context, research, patterns, source audit and validation. Reuse decisions and evidence. One primary plan remains, plus the reserved gap slot. No formal phase review has begun; retain the two review-fix/one gap-round limits. RM-027 remains a Phase 19 entry blocker.

Implemented: explicit 198-field codec; exact release/format/model/ROM identity; validation, refusal, observers, purity; full 2^62 horizon; 153 corpus snapshot forks and 14 model-applicable categories; 198 omission controls; three compiled platform pins with exact base dispositions; deep semantic fuzzing and whole-instance/RAM refusal oracle. Source, API, consumer and limitation notes remain coordinated.

Hosted fork integration at `f192100`: Windows Git path separators fail; invalid VRAM-bank/speed/queue poison can crash before intended discrepancies; RAM/rumble omissions need exact skip/readback diagnostics. The independent Plan05 worker owns only fork test/checker/control/summary files, with targeted fixes passing and full normal/ASan matrix audit pending. Preserve valid-target future comparisons; no crash/setup/timeout is a kill. Plan07 performance/release files are independent.

Runtime is now Claude Code (`runtime: claude`). Use current OpenGSD @opengsd/gsd-core 1.19.0 and resolve each role. Serial phase branch `gsd/phase-17-native-save-state-core`, draft PR130. Isolation adapter degraded because origin/HEAD unresolved; no manual worktrees. Parent owns STATE/ROADMAP/REQUIREMENTS/state.json/continuation and PR; executors own explicit paths and committed summaries. Preserve owner config edits and lockfile. Raw machine-specific reports stay ignored under build/. Sanitized Plan05 history was published at f192100; final summaries use reachable sanitized refs. Current required remote checks must pass before merge, never stale/skipped/local substitutes.

## Verification in progress (2026-10-28)

All 11 plans executed (no gap plan used); final plan source head `6199487`. Verification so far: wave gates clear; Nyquist audit 0 gaps (`e8ea47a`); security 29/29 (`2fac1be`). Code review (`b89cd74`, 3 slices) found 5 critical defects, so T-17-27 was reopened (`be21b41`). **Review-fix round 1 of 2** (`b2acaa7`..`e9e2d57`) fixed all 5 criticals and 10 of 13 warnings, each with a negative control. Dispositions are in `17-REVIEW-DISPOSITION.md`, T-17-27 is closed again, and the full suite passed 1496/1496 at `e9e2d57`. One review-fix round remains. Remaining steps: the hosted exact-head checks at the pushed head, the regression gate and the goal verifier (`gsd-verifier`), then `phase.complete`. Release precondition (WR-C03): after merge, dispatch the `report-red` dry run on main and re-cite the provisional `nightly-asan.yml:report-red` row before any release.

## Phase 17 complete (2026-10-28)

Goal verification `passed` 8/8 (`17-VERIFICATION.md`). `phase.complete` ran. Hosted exact-head CI for PR130 is green at `2eb492f` (41 pass, 3 path-skipped). Two Windows-only fixes came after the review round: `2eb492f` (inventory exemption for the POSIX-only `perf_advisory_*` pair) and the round-1 timing fixes. One review-fix round and the gap slot were left unused.

Next phase: **18 — Player Save Slots and Host Contract**. Command: `/gsd-discuss-phase 18`, only when the owner chooses. Release preconditions before v0.3.0: re-cite the provisional `nightly-asan.yml:report-red` row from a dry run on main after merge (WR-C03); re-cite `release.yml:candidate-performance` from the next release run; RM-027 is the Phase 19 entry blocker. Deferred review items are listed in `17-REVIEW-DISPOSITION.md`.
