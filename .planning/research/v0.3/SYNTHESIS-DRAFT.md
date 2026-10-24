# Draft synthesis: GabbaBoy rolling roadmap + v0.3 scope + adopted cross-project lessons

Inputs: glueyneo.md, nesturbator-muhtari.md, younger-siblings.md, playstead.md, savestate.md, velocity.md, roadmap-research.md (same directory).

## A. Diagnosis (evidence-backed)
- v0.2: 170 plans / 28 reqs (6.1 plans/req vs 1.8 in v0.1); ~8k product C lines vs 93.5k .planning lines; ~45% of calendar went to release+15.1+refresh stack+close. CI run 1.5 → ~25 min; 30% of 409 runs failed/cancelled. (velocity.md)
- Same failure pattern in siblings: glueyneo Phase 04 (65 plans, 11 review rounds, ~59 plans tooling), nesturbator Phase 16 (59 plans, 62 docs commits, 178 KB STATE), genewhip Phase 6 (44 planning commits vs 6 src), muhtari Phase 6 gate-on-gate. Fix adopted by cogmaster/muhtari: cap review-fix rounds (2) and gap rounds (1), no self-imposed quotas/clocks, tooling ideas become seeds.
- Playstead consumes emulators as hash-pinned macOS process adapters (no libretro/FFI). GB/GBC already works there through mGBA 0.10.5. Save states are NOT in Playstead v1. Live GabbaBoy integration on the Playstead side is unscheduled (needs multi-pin/CLNT-01). Concrete gaps on the GabbaBoy side: raw `{saveDir}/{romBaseName}.sav` (player writes enveloped `.gbb` in SDL prefs), save+exit 0 on SIGTERM within 2 s, MBC3 RTC layout (21-byte native block vs mGBA 48-byte footer), exit-code table, continuation protocol (qualify / initial-run / continue, exit 0/77/1) — Playstead's own continuation gate is blocked at 77 because mGBA cannot do deterministic scripted input; GabbaBoy's headless runner can.
- STATE-01 design converged across nesturbator (shipped, 10 plans), cogmaster (visitor), research: 64-byte header, one field list driving size/write/validate/apply, validate-then-apply (no partial mutation), exact-version-only pre-1.0, bounded 64-bit time fields (2^62), closure property (accepted state → run N → still saves to an accepted state), fork matrix at seeded/targeted points with coverage gate, field-drop mutant builds, struct-vs-field-list inventory checker, nm writable-global check. Size ~97 KB DMG / ~143 KB CGB + cart RAM, fixed per ROM (libretro-compatible).

## B. Rolling roadmap (to become `.planning/context/FUTURE-MILESTONES.md`, restructured in nesturbator/muhtari style: RM-NNN ids, statuses committed/proposed/parked/retired/shipped, promotion triggers, review log, snapshot at each milestone close)

Rules: ≤4 phases and ≤~40 plans per milestone; ≤12 plans per phase; 50% plan overrun = rescope trigger; ≤2 substantive tracks; every milestone ends in a qualified release; first phase of every milestone is a capped tune-up.

| Horizon | ID | Milestone | Outcome | Status |
|---|---|---|---|---|
| Immediate | RM-003 | v0.3 Host Contract & Tune-up | Playstead-ready process adapter candidate qualified by GabbaBoy's own harness; mGBA-compatible battery/RTC exchange; v0.2 debt paid; perf regression attributed and gated | committed (pending owner confirm) |
| Near | RM-004 | v0.4 Native Save States (STATE-01) | Transactional exact-continuation states over full DMG+CGB machine; player save slots | proposed |
| Near | RM-005 | v0.5 Evidence Floor | First CGB game-level evidence (Potion Panic MIT first), dmg/cgb-acid2 derivatives, gbmicrotest admission | proposed |
| Mid | RM-006 | v0.6 DMG PPU timing | pixel FIFO/fetcher, mode-3 length, Mealybug DMG, Mooneye ppu | proposed |
| Mid | RM-007 | v0.7 CGB timing & colour | cut 82 xfails to owner target, 2nd CGB game, optional user boot ROM | proposed |
| Mid | RM-008 | v0.8 Audio qualification | SameSuite APU, PCM digests | proposed |
| Long | RM-009 | v0.9 Reach | libretro core (if adopter), Wasm CI leg | parked: trigger = named adopter |
| Long | RM-010 | v1.0 Stable embeddable core | API/ABI + state format v1 freeze, support matrix, 2 DMG + 2 CGB games, 1 live consumer, perf budget | proposed |
| Post-1.0 | RM-011.. | SGB, link cable, rewind/runahead in player, MGB/AGB, exotic mappers | parked (demand/evidence triggers) |

## C. v0.3 proposed scope (Phases 16–19)
- P16 Tune-up (cap 10 plans): move test helpers out of `.planning/phases` into `tests/scripts` + lint forbidding phase paths, then archive v0.2 phase dirs; wire Phase 8 verifiers into CTest; close PRs #78–92 as superseded; decide #75 (let v0.3.0 replace); LIM dispositions (4 linked release LIMs resolved by new versioned ledger + rerun; others accepted/dropped per owner); perf regression bisect across phase merges + instruction-count proxy gate + absolute realtime budget chosen before measuring; CI hygiene (per-test time budget, CTest labels, ASan stall test split/nightly, planning-only lane); dedupe LESSONS ids + uniqueness test; trim STATE.md.
- P17 Runner host contract (INT-01a): `--rom/--save-dir` mode, raw `.sav` atomic periodic flush, SIGTERM → finish frame, flush, exit 0 well < 2 s, one exit-status table tested with real signals; GabbaBoy-declared save-format ids.
- P18 Battery/RTC interop + continuation (INT-01b): host-side mGBA/VBA-M 48-byte and BGB 44-byte RTC footer import/export (core block unchanged) with named fixtures + negatives; candidate AdapterPin JSON with schema tests; Playstead continuation protocol (qualify/initial-run/continue) over the headless runner with an original fixture and in-game readback after relaunch. Playstead-side CI run is a stretch exit recorded `not_verified` if blocked.
- P19 Release v0.3.0 (cap 8 plans): exact-tag rehearsal on version PR before tagging; release hardening done here, not after.
- Out: save states (v0.4), libretro, Wasm, Playstead code changes, notarization, CGB game attempt (v0.5).

## D. Process rules to adopt (DECISIONS + AGENTS)
1. Review-fix rounds ≤2 and gap-closure rounds ≤1 per phase; Info/non-regression warnings → seeds; only Criticals, repair regressions and gate-weakening warnings block.
2. No self-imposed quotas, wall-clock budgets or run counters as gates.
3. Phase ≤12 plans, ≤2 closeout plans; rescope at 50% overrun.
4. Checkers live in `tests/scripts/`, take an immutable commit, carry a negative control, wired into CTest at creation.
5. Freshness policy decided up front: no per-phase verification refreshes; one re-verification at the final head; `override_closeout` accepted when the audit re-runs evidence on the merged head.
6. Requirements written as the command/check that proves them.
7. First executable plan of a feature exercises the compiled public-API path (not offline checks only).
8. CI: timeouts cite the run they double; jobs ≤60% of limit; planning-only lane.
9. Cross-learn from siblings at every milestone; refresh rolling roadmap; snapshot it.
