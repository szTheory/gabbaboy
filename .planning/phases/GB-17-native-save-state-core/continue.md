# Phase 17 continuation

Completed stage: **Phase 17 execution, plans 17-01..07 implemented with targeted evidence**. Settled full suite at `7cb5739`: 1481/1482; the `test_budget` rejection of the two plan-07 advisory perf TIMEOUTs is fixed in `5701130` (base 60 s, measured ~7 s) with the affected tests passing. The hosted ASan fuzz timeout at `b3e57bc` is fixed in `f0591f4` (state path rules resolved once per field); full suite 1482/1482 at `f0591f4`. Current-head hosted qualification remains pending (PR130 checks last ran at `f192100`).

Next stage: **Phase 17 — Native Save State Core, wave 8 / plan 17-08**. Resume command: `/gsd-execute-phase 17`.

Next feature phase: **18 — Player Save Slots and Host Contract**, after Phase 17 execution/verification and owner choice. Both auto flags remain false. Never start Phase 18 automatically.

Read seven completed summaries and `17-08-PLAN.md` with the existing context, research, patterns, source audit and validation. Reuse decisions and evidence. Four primary plans remain, plus the reserved gap slot. No formal phase review has begun; retain the two review-fix/one gap-round limits. RM-027 remains a Phase 19 entry blocker.

Implemented: explicit 198-field codec; exact release/format/model/ROM identity; validation, refusal, observers, purity; full 2^62 horizon; 153 corpus snapshot forks and 14 model-applicable categories; 198 omission controls; three compiled platform pins with exact base dispositions; deep semantic fuzzing and whole-instance/RAM refusal oracle. Source, API, consumer and limitation notes remain coordinated.

Hosted fork integration at `f192100`: Windows Git path separators fail; invalid VRAM-bank/speed/queue poison can crash before intended discrepancies; RAM/rumble omissions need exact skip/readback diagnostics. The independent Plan05 worker owns only fork test/checker/control/summary files, with targeted fixes passing and full normal/ASan matrix audit pending. Preserve valid-target future comparisons; no crash/setup/timeout is a kill. Plan07 performance/release files are independent.

Runtime is now Claude Code (`runtime: claude`). Use current OpenGSD @opengsd/gsd-core 1.19.0 and resolve each role. Serial phase branch `gsd/phase-17-native-save-state-core`, draft PR130. Isolation adapter degraded because origin/HEAD unresolved; no manual worktrees. Parent owns STATE/ROADMAP/REQUIREMENTS/state.json/continuation and PR; executors own explicit paths and committed summaries. Preserve owner config edits and lockfile. Raw machine-specific reports stay ignored under build/. Sanitized Plan05 history was published at f192100; final summaries use reachable sanitized refs. Current required remote checks must pass before merge, never stale/skipped/local substitutes.
