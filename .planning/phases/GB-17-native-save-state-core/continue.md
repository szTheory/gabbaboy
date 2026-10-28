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
