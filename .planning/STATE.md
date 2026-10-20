---
gsd_state_version: "1.0"
milestone: v0.2
milestone_name: Color & Cartridge Breadth
current_phase: 13
current_phase_name: CGB HDMA
current_plan: 12/12 complete
status: completed
stopped_at: Phase 13 verification refresh complete; Phase 14 verification refresh next
last_updated: "2026-10-20T23:32:42.226239+00:00"
last_activity: 2026-10-20
last_activity_desc: Refreshed Phase 13 goal verification and canonical 45-row UAT; Phase 14 remains
state_head: 3930668cb49dba7289dff34696d8de2ee96492ed
progress:
  total_phases: 9
  completed_phases: 9
  total_plans: 134
  completed_plans: 134
  percent: 100
---

# Project State

## Project Reference

See: [PROJECT.md](PROJECT.md) (updated 2026-10-20)

**Core value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Current focus:** Refresh stale phase verification before v0.2 milestone completion

## Current Position

Completed stage: **Phase 13 — CGB HDMA, verification refresh**. All 12 implementation plans were already complete. The refreshed [verification report](phases/GB-13-cgb-hdma/13-VERIFICATION.md) passes **37/37 truths**, 49 artifact declarations, 12 independently traced links and one test-tier prohibition. CGB-07 remains satisfied; OpenGSD freshness is `passed` over 107 covered files. The generic key-link detector could not interpret the narrative declarations; the verifier traced actual wiring and executed predicates.

Fresh unchanged source `a5f0d59` passed configured core regression **1,144/1,144** in **438.76 seconds** and rebuilt SDL player **98/98** in **19.87 seconds**, zero skips. Independent focused behavioral checks passed 21/21. Frozen DMG baseline has zero changed rows; all 12 bounded plan task windows reconcile. Canonical [13-UAT.md](phases/GB-13-cgb-hdma/13-UAT.md) closes **45/45 automated deliverables** with **19 rejected controls**, zero human checkpoints.

[13-REFRESH-GATES.md](phases/GB-13-cgb-hdma/13-REFRESH-GATES.md) retains historical review/security/Nyquist/UI applicability. Four historical review fixes remain closed; the duplicate-library warning persists as deferred debt. At immutable completed boundary `e7ba52c`, original pure handoff checks pass with four rejected route/flag controls. The original full wrapper pins OpenGSD 1.16.0 and refuses current 1.18.0; the actual current producer separately passes saved-prohibition fail-first/clean/live proof. Local pinned fixture rebuild is unavailable (RGBDS 1.0.4 versus required 1.0.1). Historical hosted receipts retain actual revisions; no new hosted, sanitizer runtime, hardware, perceptual or benchmark qualification is claimed.

Milestone completion remains **pending**. Phases 7–13 verification are refreshed; Phase 14 still requires refresh, including its clean UAT review. The milestone audit retains 28/28 satisfied requirements and 21 debt items; no debt acceptance occurs here. v0.3 remains provisional, unnumbered and unstarted.

Next phase: **14 — CGB-E Model Qualification and Corpus**, verification refresh only.
Exact next command: `/gsd-execute-phase 14`.
Stop after Phase 13. Both automatic advance flags remain false. No archive, tag, release or merge was performed.

Review stack: branch `gsd/phase-13-verification-refresh` builds on Phase 12 refresh PR #88. Boundary triage found no open issues; PRs #78–88 and release-please #75 remain unmerged. Required checks must pass at the exact reviewed head before merge; local results do not establish remote readiness. Preserve pre-existing config/state.json edits. The phase.complete CLI returned an incorrect last-phase route and incremented the already-complete phase count; the recorded current artifacts override that derived route without replaying completed phases. Its missing-path warnings include two command strings and historical `.planning/milestone.lock`; current artifact verification passes 49/49.

### Historical Phase 14 handoff (superseded route; preserved receipts)

Phase: 14 — CGB-E Model Qualification and Corpus
Status: Phase 14 automated UAT complete; paused for the owner
Current Plan: 13
Total Plans in Phase: 13
Last Activity: 2026-10-16
Last Activity Description: Phase 14 automated UAT complete; 49/49 automated; next Phase 15 discussion

Completed workflow stage: **Phase 14 — CGB-E Model Qualification and Corpus, automated UAT complete**. [14-UAT.md](phases/GB-14-cgb-e-model-qualification-and-corpus/14-UAT.md) closes all 49 deliverables across 13 plans automatically, with zero issues, pending/skipped/blocked rows or human checkpoints. All 13 bounded commit windows reconcile. The canonical [14-VERIFICATION.md](phases/GB-14-cgb-e-model-qualification-and-corpus/14-VERIFICATION.md) passes 41/41; CGB-08 and CGB-10 are complete. Nyquist covers 31/31 tasks, security closes 27/27 threats, and all eight implementation review findings are fixed and independently checked.

[14-CLOSURE.md](phases/GB-14-cgb-e-model-qualification-and-corpus/14-CLOSURE.md) preserves the execution receipts at their actual producers. Execution head `9c5b32dc4c75ad5f9eba44ff1c7b0a15ba0f9c7f` passed all 19 hosted jobs, including native Windows, Linux ASan/UBSan, fixture reproduction and packages. Final UAT metadata requires its own exact-head checks before the pre-authorized PR #71 merge; GitHub holds the current head and merge receipt. The complete software corpus contains 107 cases: 25 actual passes and 82 matched expected failures. Physical CGB-E remains UNKNOWN/POLICY; no analog, perceptual or general game qualification is claimed.

Next stage: **Phase 15 discussion**.
Next command: `/gsd-discuss-phase 15`.
Next phase: **15 — CGB Acceptance, Support Ledger and v0.2.0 Release** remains unstarted. Release PR #70 belongs to that phase. Stop at the Phase 14 boundary.

Both auto-advance flags remain false. Preserve D-069 automated checks with meaningful negative controls, strict SUMMARY coverage, D-096 small/flat dependencies and D-099 independent corpus membership. Reuse completed UAT and research unless covered behavior changes, contrary evidence appears, or evidence is stale/unavailable; do not repeat execution or invent a confirmation-only checkpoint. Boundary-only closure and handoff checks stay local while recurring checks remain in existing CI.

Progress (v0.2): 8/9 phases complete (89%); 124/124 currently planned plans complete (100%). Phase 15 has no plans and has not started.

### Historical Phase 13 handoff (superseded route; preserved receipts)

Phase: 13 (CGB HDMA) — VERIFIED
Status: Automated UAT complete; paused for the owner to choose the next phase.
Current Plan: 12
Total Plans in Phase: 12

Completed workflow stage: **Phase 13 automated UAT complete**.

[13-UAT.md](phases/GB-13-cgb-hdma/13-UAT.md) closes all 45 deliverables across 12 plans automatically: zero issues, pending/skipped/blocked rows and human checkpoints. All 12 bounded commit windows reconcile. The local closure check rejects 17 weakened records, including hidden manual rows; the handoff rejects contradictory stages and stale routes. [13-VERIFICATION.md](phases/GB-13-cgb-hdma/13-VERIFICATION.md) remains the canonical 37/37 goal report; covered-input refresh is performed by its owner after the UAT/handoff changes.

Fresh source `e556c1b` passed native 994/994 and SDL3 player 1,087/1,087 with no skips. Reviewed source `eeb1ce9` passed focused 9/9 and exact relocated C/C++ consumer/package 6/6. The frozen DMG baseline has zero changed rows. Prior published execution head `b7b4418` passed all 19 exact-head PR-event jobs (CI 38677996444, fixtures 38677996408, preview 38677996566; Linux ASan/UBSan 989/989). [13-BENCH.md](phases/GB-13-cgb-hdma/13-BENCH.md) binds each receipt to its own revision. Final UAT metadata requires separate exact-head checks before the pre-authorized PR #69 merge; GitHub holds the newest head and merge receipt.

D-069 and LESSONS GB-GSD-016 preserve this automation-first default: automate every decidable deliverable with a meaningful negative control, add hosted CI only for recurring value, and reuse completed UAT unless covered behavior or evidence changes. Existing security closes 25/25 threats; prior code-review fixes remain closed (four total findings including the UAT supplement, zero open). The two focused UAT automation findings are fixed and independently re-reviewed before final handoff. No new source/API behavior or owner decision is introduced.

Next stage: **Phase 14 discussion**.
Next command: /gsd-discuss-phase 14.
Next phase: **14 — CGB-E Model Qualification and Corpus** remains unstarted. Stop after Phase 13 and retain both auto-advance flags as false. Physical CGB-E remains UNKNOWN/POLICY; optional CGB-C cases are rights-gated and outside the 5/5 software-fixture denominator.

Phase 12 is merged at `8091fb591de7fb68e666be01d344f5f26ebedc5c` (PR #68); its completed UAT remains closed absent changed behavior or contrary evidence.

Progress (v0.2): 7/9 phases complete (78%); 111/111 currently planned plans executed. Phases 14–15 are unstarted.

### Prior stage receipts (historical, before the final merges)

Completed: Phase 9 (MBC3, Deterministic RTC and Cartridge Persistence) — execution plus the execute-phase tail: code review (4 fixed, 1 skipped), Nyquist validation, security (0 open), regression gate and gsd-verifier `passed` (09-VERIFICATION.md)
Verified: Phase 9 `/gsd-verify-work 9` passed 2026-10-12 — 14/14 UAT items automated (09-UAT.md), the guide-wording item replaced by the `native_guide_rtc_contract` check; re-verification `passed` (09-VERIFICATION.md); PR #65 squash-merges at the exact-head green branch head (pre-authorized)
Completed: Phase 10 - CGB Profile, Banking and Register Visibility, execution (plans 10-01..10-20), evidence head `2fe078e8f08ed98ba0ac0e244971e7c0ead16b1e` run https://github.com/szTheory/gabbaboy/actions/runs/38299323863; PR #66 ready and not merged
Verified: Phase 10 `/gsd-verify-work 10` passed 2026-10-12 — 12/12 UAT items automated (10-UAT.md), local 541/541 with installed inventory at 3c0d6bc; verification `passed` (10-VERIFICATION.md); PR #66 squash-merges at the exact-head green branch head (pre-authorized)
Completed: Phase 11 - CGB Colour Rendering and Player Colour, planning (11-RESEARCH, 11-PATTERNS, 11-VALIDATION, plans 11-01..11-15) on branch `gsd/phase-11-cgb-colour-rendering-and-player-colour`
Completed: Phase 11 - CGB Colour Rendering and Player Colour, execution (plans 11-01..11-15) plus the execute-phase tail; gsd-verifier `passed` 3/3 (11-VERIFICATION.md); evidence head `fb7d14c` exact-head green; PR #67 open, not merged
Verified: Phase 11 `/gsd-verify-work 11` passed 2026-10-13 — 11/11 UAT rows automated covering all 91 SUMMARY coverage entries (11-UAT.md); verification `passed` (11-VERIFICATION.md); hosted ASan timeout fixed in the PR (LESSONS GB-CI-004); PR #67 squash-merges at the exact-head green branch head (pre-authorized)
Completed workflow stage: **Phase 12 - CGB Double Speed, execution** (2026-10-14), plans 12-01..12-19 plus Nyquist validation, security, UI scope review, code review and fixes, regression gate, and goal verification. [12-VERIFICATION.md](phases/GB-12-cgb-double-speed/12-VERIFICATION.md) passes 109/109 with zero unverified behaviors; OpenGSD phase.complete accepted 19/19. Local CTest passed 898/898 in 52.66 seconds, and the DMG baseline had zero changed rows. Exact tested source head `502f992fe9fd2d848845947057c2b327747c3edd`: PR CI `38565349295`, fixture reproduction `38565349297`, and package smoke `38565349116` all succeeded with every PR-event job successful; ASan/UBSan passed 893/893 in 1217.04 seconds. All three review findings are fixed; 34 security threats are closed. Draft [PR #68](https://github.com/szTheory/gabbaboy/pull/68) remains unmerged. Only AGE DIV and STOP-prefetch are passes; eleven qualified expected failures remain, and no physical hardware claim is made. The original plan 12-19 benchmark receipt is historical at `301f1b05577e6d35a4c3a756ded1ec15a4082c8d`, runs `38502094649`, `38502094682`, and `38502094771`; later metadata commits require their own exact-head checks.
Verified workflow stage: **Phase 12 - CGB Double Speed, verification** (2026-10-14), via `/gsd-verify-work 12`: [12-UAT.md](phases/GB-12-cgb-double-speed/12-UAT.md) closes 73/73 deliverables automatically, zero issues and zero human checkpoints. Fresh local CTest passed 898/898 in 107.00 seconds; the closure contract rejects nine weakened records, and all 19 bounded commit claims reconcile after correcting plan 12-04's ending SHA. D-069 and LESSONS GB-GSD-016 preserve this default. Exact execution-head `da98d56ef8fadadf34ae951b337dcdecce495936` PR-event runs `38569486172`, `38569486169`, and `38569486126` passed all 19 jobs; ASan/UBSan passed 893/893 in 1089.77 seconds. This verification-record revision requires its own exact-head checks before the pre-authorized PR #68 merge; GitHub holds that final receipt and merge state.

## Performance Metrics

- Completed unique plans: 56; recorded execution total: 1002 min. Phase 6 completed all seven reviewed plans in six dependency-ordered waves; its refreshed report passes 5/5 at `f0acb86`.
- Per-phase metrics / recent trend: All six phase implementations and 56/56 runnable plans are complete; the current OpenGSD freshness gate accepts all six phases. Phase 1's 2026-10-10 refreshed verification passes 21/21 at `ebce345` with 179/179 local CTest. Phase 2's 2026-10-10 refreshed verification passes 5/5 and CPU-01–05 at `a9050df` after quick task 261010-bz3 reconciled its CPU-02/CPU-05 SUMMARY metadata. Phase 3's refreshed verification passes 5/5; current core CTest passed 179/179, optional player tests passed 51/51, and focused output-directory safety regressions passed 8/8. Phase 5's 2026-10-10 refreshed verification passes 17/17 at `f39faac`; its clean-tree PCM receipt is recorded in its verification report. Phase 6's 2026-10-10 refreshed verification passes 5/5 at `f0acb86`; its historical asset and hosted-receipt evidence stays in its validation report. Phase 4 has 7/7 verified truths and a clean source review. FIFO ROM-open hardening passed exact-head PR #43 checks and is merged. D-025 bounds VIDEO-02/03 to the confidence-qualified software model; no physical CPU-B measurement is claimed. Plan 02-15 is superseded/non-runnable and remains historical.
- Emulator correctness, speed, memory, and CI baselines: No general hardware/gameplay baseline. The current Phase 2 refresh passed 179/179 local CTest, 88/88 focused Phase 2 cases, three eligible runner receipts, and the protocol probe with zero PPU accesses. Historical exact evidence at implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989` includes the 104/104 offline core inventory, 109/109 relocated installed C/C++ inventory, hosted CI run 37620710587, and fixture reproduction run 37620710600. Original upstream PPU-dependent reporting paths remain excluded; no physical DMG hardware test occurred.

**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01 P01 | 14 | 2 tasks | 11 files |
| Phase 01 P02 | 7 min | 2 tasks | 7 files |
| Phase 01 P03 | 94 min | 3 tasks | 10 files |
| Phase 01 P04 | 31 min | 2 tasks | 12 files |
| Phase 01 P05 | 84 min | 3 tasks | 15 files |
| Phase GB-02 P01 | 22min | 2 tasks | 14 files |
| Phase GB-02 P02 | 43 min | 2 tasks | 10 files |
| Phase 02 P03 | 6 | 2 tasks | 4 files |
| Phase 02 P04 | 16min | 2 tasks | 7 files |
| Phase GB-02 P05 | 18 | 2 tasks | 5 files |
| Phase GB-02 P06 | 6 min | 2 tasks | 7 files |
| Phase GB-02 P07 | 20 | 3 tasks | 12 files |
| Phase GB-02 P08 | 8 min | 2 tasks | 10 files |
| Phase GB-02 P09 | 8 min | 2 tasks | 10 files |
| Phase GB-02 P10 | 10 min | 2 tasks | 5 files |
| Phase GB-02 P11 | 12 min | 2 tasks | 4 files |
| Phase GB-02 P12 | 9 min | 2 tasks | 6 files |
| Phase GB-02 P13 | 8 min | 2 tasks | 3 files |
| Phase GB-02 P14 | 8 min | 2 tasks | 4 files |
| Phase GB-02 P17 | 54 min | 3 tasks | 12 files |
| Phase 02 P16 | 24min | 2 tasks | 6 files |
| Phase 02 P18 | 25 min | 2 tasks | 5 files |
| Phase GB-03 P01/P02 | 20/30 min | 1/2 tasks | 10/5 files |
| Phase GB-03 P03/P04/P05/P06/P07/P08/P09 | 79/11/19/15/10/12/24 min | 2/2/2/2/2/2/2 tasks | 6/10/8/11/9/3/5 files |
| Phase GB-03 P10 | 9+ min (lower bound; exact start not captured) | 3 tasks | 4 files |
| Phase GB-03 P11 | 4min+ minimum recorded | 2 tasks | 6 files |
| Phase GB-03 P12 | ~30 min | 2 tasks | 6 files |
| Phase GB-03 P13 | not captured | 3 tasks | implementation, tests, evidence and continuity files |
| Phase 04 P01 | 13 | 2 tasks | 12 files |
| Phase 04 P02 | 8min | 2 tasks | 7 files |
| Phase 04 P03 | 14min | 2 tasks | 5 files |
| Phase 04 P04 | 11min | 2 tasks | 8 files |
| Phase 04 P05 | 7min | 2 tasks | 11 files |
| Phase 04 P06 | 10 min | 2 tasks | 13 files |
| Phase 04 P07 | 18 min | 2 tasks | documentation, evidence, and workflow metadata |
| Phase GB-05 P01 | 13min | 2 tasks | 8 files |
| Phase GB-05 P02 | 17min | 2 tasks | 5 files |
| Phase GB-05 P03 | 21min | 2 tasks | 8 files |
| Phase GB-05 P04 | 62 min | 2 tasks | 7 files |
| Phase GB-05 P05 | 12 min | 2 tasks | 6 files |
| Phase 05 P06 | 25 min | 3 tasks | 14 files |
| Phase GB-05 P07 | 32min | 2 tasks | 12 files |
| Phase GB-06 P01 | 167 | 2 tasks | 7 files |
| Phase GB-06 P05 | 19 min | 2 tasks | 8 files |
| Phase GB-06 P02 | 8 | 2 tasks | 3 files |
| Phase GB-06 P04 | 8 min | 2 tasks | 6 files |
| Phase GB-06 P03 | 6 min | 2 tasks | 8 files |
| Phase GB-06 P07 | 7min | 2 tasks | 4 files |
| Phase GB-06 P06 | 95 min | 2 tasks | release workflow, evidence, and handoff |
| Phase 06.1 P01 | 3 min | 2 tasks | 2 files |
| Phase 06.1 P02 | 12 min | 3 tasks | 4 files |
| Phase GB-06.1 P03 | 15 min | 2 tasks | 1 files |
| Phase GB-06.1 P04 | 30 min | 3 tasks | 4 files |
| Phase GB-06.1 P05 | 20 min | 2 tasks | 11 files |
| Phase GB-06.1 P06 | 10 min | 2 tasks | 10 files |
| Phase GB-06.1 P07 | 13 min | 2 tasks | 11 files |
| Phase 06.1 P08 | 10 min | 2 tasks | 2 files |
| Phase 07 P01 | 18min | 3 tasks | 11 files |
| Phase 07 P02 | 40 min | 3 tasks | 12 files |
| Phase 07 P03 | 30 min | 2 tasks | 5 files |
| Phase 07 P04 | 20 min | 2 tasks | 4 files |
| Phase 07 P05 | 6 min | 2 tasks | 10 files |
| Phase 07 P17 | 25 min | 2 tasks | 2 files |
| Phase 07 P06 | 25 min | 2 tasks | 11 files |
| Phase 07 P07 | 75 min | 2 tasks | 11 files |
| Phase 07 P08 | 25 min | 2 tasks | 9 files |
| Phase 07 P09 | 20 min | 2 tasks | 7 files |
| Phase 07 P10 | 35 min | 2 tasks | 8 files |
| Phase 07 P11 | 130 min | 3 tasks | 9 files |
| Phase 07 P12 | 40 min | 2 tasks | 6 files |
| Phase 07 P13 | 75 min | 3 tasks | 8 files |
| Phase GB-07 P14 | 55 min | 3 tasks | 5 files |
| Phase GB-07 P07-15 | 70 min | 2 tasks | 7 files |
| Phase 7 P16 | 100 min | 3 tasks | 7 files |
| Phase 08 P01 | 70 min | 3 tasks | 3 files |
| Phase GB-08 P08-02 | 40 min | 3 tasks | 5 files |
| Phase 08 P03 | 55 min | 3 tasks | 8 files |
| Phase 08 P04 | 20 min | 2 tasks | 7 files |
| Phase 08 P05 | 40 min | 2 tasks | 24 files |
| Phase 08 P06 | 30 min | 3 tasks | 7 files |
| Phase 08 P07 | 150 min | 2 tasks | 7 files |
| Phase 08 P08-08 | 25 min | 4 tasks | 11 files |
| Phase 08 P09 | 40 min | 2 tasks | 14 files |
| Phase 08 P10 | 45 min | 2 tasks | 2 files |
| Phase 09 P01 | 25 min | 2 tasks | 7 files |
| Phase 9 P02 | 15 min | 2 tasks | 10 files |
| Phase 9 P03 | 8 min | 2 tasks | 2 files |
| Phase 9 P04 | 15 min | 2 tasks | 5 files |
| Phase 09 P05 | 20 min | 2 tasks | 5 files |
| Phase 09 P06 | 12 min | 2 tasks | 5 files |
| Phase 09 P07 | 20 min | 3 tasks | 4 files |
| Phase 9 P08 | 25 min | 3 tasks | 11 files |
| Phase 9 P09-09 | 85 min | 3 tasks | 9 files |
| Phase 09 P10 | 25 min | 2 tasks | 8 files |
| Phase 9 P11 | 40 min | 3 tasks | 9 files |
| Phase 9 P12 | 55 min | 3 tasks | 10 files |
| Phase 09 P13 | 55 min | 3 tasks | 9 files |
| Phase 09 P14 | 12 min | 2 tasks | 3 files |
| Phase 09 P15 | 45 min | 3 tasks | 3 files |
| Phase 09 P16 | 70 min | 3 tasks | 11 files |
| Phase 9 P17 | 60 min | 2 tasks | 9 files |
| Phase 9 P18 | 150 min | 2 tasks | 12 files |
| Phase 10 P01 | 25 min | 2 tasks | 4 files |
| Phase 10 P02 | 40 min | 2 tasks | 4 files |
| Phase 10 P03 | 35 min | 2 tasks | 8 files |
| Phase 10 P04 | 40 min | 2 tasks | 5 files |
| Phase 10 P05 | 35 min | 3 tasks | 8 files |
| Phase 10 P06 | 55 min | 3 tasks | 8 files |
| Phase 10 P07 | 12 min | 2 tasks | 4 files |
| Phase 10 P08 | 15 min | 2 tasks | 5 files |
| Phase 10 P09 | 40 min | 3 tasks | 8 files |
| Phase 10 P10 | 35min | 3 tasks | 5 files |
| Phase 10 P11 | 25 min | 2 tasks | 6 files |
| Phase 10 P12 | 40 min | 3 tasks | 6 files |
| Phase 10 P13 | 45 min | 3 tasks | 11 files |
| Phase 10 P14 | 25 min | 2 tasks | 12 files |
| Phase 10 P15 | 15 min | 3 tasks | 4 files |
| Phase 10 P16 | 40 min | 3 tasks | 9 files |
| Phase 10 P17 | 35 min | 2 tasks | 6 files |
| Phase 10 P18 | 45 min | 3 tasks | 9 files |
| Phase 10 P19 | 25 min | 3 tasks | 8 files |
| Phase 10 P20 | 95 min | 2 tasks | 8 files |
| Phase 11 P01 | 25 min | 2 tasks | 6 files |
| Phase 11 P02 | 45 min | 3 tasks | 8 files |
| Phase 11 P03 | 40 min | 2 tasks | 5 files |
| Phase 11 P04 | 25 min | 2 tasks | 5 files |
| Phase 11 P05 | 30 min | 3 tasks | 3 files |
| Phase 11 P06 | 55 min | 3 tasks | 17 files |
| Phase 11 P07 | 50 min | 2 tasks | 14 files |
| Phase 11 P08 | 45 min | 2 tasks | 22 files |
| Phase 11 P09 | 25 min | 3 tasks | 7 files |
| Phase 11 P10 | 30 min | 3 tasks | 12 files |
| Phase 11 P11 | 25min | 2 tasks | 8 files |
| Phase 11 P12 | 50min | 2 tasks | 11 files |
| Phase 11 P13 | 25min | 2 tasks | 9 files |
| Phase 11 P14 | 40 min | 3 tasks | 11 files |
| Phase 11 P15 | 25 min | 2 tasks | 6 files |
| Phase 12 P01 | 10 min | 2 tasks | 8 files |
| Phase 12 P02 | 7 min | 2 tasks | 10 files |
| Phase 12 P03 | 19 min | 3 tasks | 5 files |
| Phase GB-12 P04 | 4 min | 2 tasks | 14 files |
| Phase GB-12 P05 | 19m55s lower bound | 3 tasks | 6 files |
| Phase GB-12 P06 | 41m28s | 2 tasks | 5 files |
| Phase GB-12 P07 | 112m | 3 tasks | 5 files |
| Phase GB-12 P08 | 9m 25s | 3 tasks | 6 files |
| Phase GB-12 P09 | Not captured (task commits span 4m 08s) | 3 tasks | 6 files |
| Phase GB-12 P10 | 13m+ lower bound | 3 tasks | 11 files |
| Phase GB-12 P11 | >=42min lower bound | 2 tasks | 9 files |
| Phase 12 P12 | 14 min | 3 tasks | 10 files |
| Phase 12 P13 | not captured | 2 tasks | 6 files |
| Phase 12 P15 | 8min | 2 tasks | 8 files |
| Phase 12 P16 | 15min | 3 tasks | 6 files |
| Phase 12 P17 | 23m+ lower bound | 3 tasks | 8 files |
| Phase GB-12 P18 | 8 min | 2 tasks | 9 files |
| Phase 12 P19 | 50 min | 3 tasks | 12 files |
| Phase 13 P01 | 26 min | 2 tasks | 9 files |
| Phase 13 P02 | 24min | 2 tasks | 9 files |
| Phase 13 P06 | 13 min | 2 tasks | 9 files |
| Phase 13 P03 | 43min | 2 tasks | 7 files |
| Phase 13 P04 | 30min | 2 tasks | 8 files |
| Phase 13 P08 | 18min | 2 tasks | 13 files |
| Phase 13 P05 | 12 min | 2 tasks | 8 files |
| Phase 13 P07 | 20m | 2 tasks | 12 files |
| Phase 13 P09 | 30 min | 2 tasks | 9 files |
| Phase 13 P10 | 20min | 2 tasks | 7 files |
| Phase 13 P11 | 9min+ | 2 tasks | 10 files |
| Phase 15 P04 | 35 min | 2 tasks | 7 files |
| Phase 15 P07 | 45 min | 2 tasks | 2 files |
| Phase 15 P06 | 2h | 2 tasks | 5 files |
| Phase 15 P08 | 60 min | 2 tasks | 3 files |
| Phase 15 P09 | about 3 hours | 2 tasks | 9 files |
| Phase 15 P10 | 9h | 2 tasks | 20 files |

## Accumulated Context

### Decisions

Adopted choices: [DECISIONS.md](context/DECISIONS.md). Evidence navigation: [research/INDEX.md](research/INDEX.md); synthesis dated 2026-10-02.

- Scope is GB/DMG and GBC/CGB. v0.1 is a limited DMG preview; GB/GBC breadth is the next named milestone.
- Original portable C17 core, native opaque-instance API, optional SDL3 macOS adapter; explicit time/ownership and bounded operations.
- ROM-only/scoped MBC1 and battery continuation in v0.1; no stable ABI promise. Future scope remains in [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md).
- OpenGSD workflow: automate within the authorized phase, require current evidence, then stop. Both auto-advance settings remain false; session model is inherited.
- [Phase 01]: The tracer starts from an explicit bootless DMG-CPU-B profile; deterministic RAM fill is emulator policy, not hardware startup evidence.
- [Phase 01]: RGBDS v1.0.1 is required only for fixture regeneration; normal build and digest verification use checked-in bytes offline.
- [Phase 01]: ROM validation returns distinct bounded errors and failed replacement loads leave active guest state unchanged.
- [Phase 01]: Reset retains the loaded ROM while restoring deterministic post-boot CPU state and clearing guest RAM and emulated time.
- [Phase 01]: The installed export explicitly maps the core library to GabbaBoy::core.
- [Phase 01]: Installed consumer tests are registered only when the relocated prefix exists, preserving ordinary offline CTest runs.
- [Phase 01]: CI uses explicit runner labels and a fail-closed 26-case installed CTest inventory with a 23-case core subset; runner images are not product OS claims.
- [Phase 01]: The official CMake 3.25.3 floor script and RGBDS 1.0.1 fixture reproduction passed locally in Ubuntu x86_64 containers and on PR #1; run-scoped hosted evidence is recorded in 01-VALIDATION.md.
- [Phase 01]: Pin explicit native runner labels and require every evidence job plus its exact test inventory; do not infer product OS support from runner labels.
- [Phase 01]: Keep hosted CI and branch-protection evidence pending until exact-revision remote results are observed; fixture-repro is a separate status context.
- [Phase GB-01]: Qualify preview packages and contributor claims against an exact PR SHA; query the artifact API for per-run expiry and report it without calling temporary artifacts releases.
- [Phase 01]: The bootless DMG-CPU-B tracer verifies the bounded API and guest path, not hardware-qualified memory mapping; Phase 2 owns that evidence.
- [Phase 01]: At verified implementation SHA `8396096ad17500974b30657af91fd2ef9ad51237`, all five roadmap truths and eight BASE requirements passed, standard code review was clean, and required PR contexts plus both package artifacts passed exact-SHA verification.
- [Phase 01]: Final exact hosted evidence also passed at docs-only PR SHA `9f1df9bd0a70e50033f7d8cbcbff778e3bfd94e3` after the Phase 1 closeout documentation was committed; the implementation is unchanged from SHA `8396096ad17500974b30657af91fd2ef9ad51237`.
- [Phase GB-02]: ROM-only A000-BFFF reads stop as unsupported bus and writes have no effect.
- [Phase GB-02]: The side-effect-free peek API exposes WRAM, its echo, and HRAM only.
- [Phase GB-02]: The original tracer moved its protocol from fixture-policy A000 RAM to WRAM C000/C001.
- [Phase GB-02]: RGBDS 1.0.1 fixture regeneration uses the SHA-verified official macOS archive.
- [Phase GB-02]: Unused SM83 encodings persistently lock with original PC/opcode until reset; CB-prefixed instruction semantics are owned by Plan 02-03.
- [Phase 02]: CB register operations cost 16 half-dots; BIT (HL) costs 24; other (HL) CB operations cost 32.
- [Phase 02]: BIT preserves carry and sets H; RES and SET preserve flags; rotate/shift groups set Z and carry from their results.
- [Phase 02]: Interrupt entry costs 40 half-dots, selects the lowest enabled pending bit, clears it, and pushes the interrupted PC on timed bus phases.
- [Phase 02]: HALT idle advances eligible time in whole 8-half-dot cycles; STOP remains stopped until the timestamped wake path in Plan 02-06.
- [Phase GB-02]: Timer divider falling edges and qualified TIMA/TMA reload collisions run at timed bus phases; serial overlap without qualified ordering returns bounded unsupported.
- [Phase GB-02]: STOP waits advance only the bounded master timeline; oscillator-driven CPU, divider, timer, and internal serial state stays frozen.
- [Phase GB-02]: Timestamped input uses a fixed 64-event queue with atomic admission and stable caller order for equal timestamps.
- [Phase GB-02]: Keep the eligible CPU/timer corpus denominator fixed; guest assertions, callbacks and exact result PCs classify outcomes, while digests alone never qualify applicability.
- [Phase GB-02]: Preserve derived fixture bytes, rights and pinned reproduction procedures; original PPU-dependent behavior and physical hardware remain outside the corpus claim.
- [Phase GB-02]: CPU, timer, interrupts, HALT/STOP and reset semantics are covered by the completed Phase 2 verification and validation artifacts.
- [Phase GB-02]: Installed C/C++ consumers and hosted exact-revision checks cover the Phase 2 public package; see the linked verification artifacts.
- [Phase GB-02]: On 2026-10-07, independent verification passed CPU-01 through CPU-05 and all five roadmap truths at implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989`. Final local, installed-consumer, and exact hosted evidence is recorded in Phase 2 verification and validation; original upstream PPU-dependent results and physical hardware behavior remain outside the claim.
- [Phase GB-03]: Keep the playable original ROM fixture separate from PPU composition, raster timing, DMA/access, and scripted gameplay oracles; fixture byte reproducibility does not establish DMG-CPU-B applicability.
- [Phase GB-03]: The initial background renderer advances dots on the emulated timeline and publishes a completed shade frame at VBlank entry; it is not hardware-qualified raster timing.
- [Phase GB-03]: Plan 03-02 adds fixed per-instance transfer slots and source-qualified mode/STAT/fetch expectations; the slot model does not claim electrical or CPU-B FIFO equivalence.
- [Phase GB-03]: Plan 03-03 adopts the narrower Nintendo-manual `$8000–$DFFF` DMA source range despite a pinned Pan Docs conflict; exact simultaneous PPU/DMA collision behavior remains unqualified.
- [Phase GB-03]: FF00 active-low row polling consumes timestamped button events; JOYP interrupt behavior remains gated by D-08. The optional SDL3 player bounds and transactionally replaces ROMs, keeps mutations on the event loop, and uses pixel-aligned integer scaling. The public frame API checks output extents/overlap before writes, and queue capacity precedes entry validation; relocated consumers test both APIs. RGBDS 1.0.1 fixture reproduction now binds assembly source, exact ROM bytes, and pinned archive digests locally and in hosted CI; this is not gameplay or hardware evidence. SDL3 3.4.18 and host timing remain isolated to the adapter.
- [Phase GB-03]: Player help and downloaded-package metadata now assert the preview's audio and battery-persistence limitations; those checks do not establish emulator feature behavior or hardware qualification.
- [Phase GB-03]: Pinned Mooneye cases support the fresh DMA access window, active FF46 restart, and register readback; a focused owned guest suite covers those cases. The upstream README lists a DMG-CPU-B in its hardware fleet but publishes no per-test/per-unit raw log. This evidence does not cover simultaneous PPU/DMA arbitration or JOYP interrupt timing.
- [Phase GB-03]: D-025 adopts a deterministic, confidence-qualified source-backed software model for documented but revision-sensitive JOYP and DMA/PPU behavior; exact CPU-B phases and revision parity remain unmeasured.
- [Phase GB-03]: The optional SDL3 macOS preview displayed the owned demo; the user confirmed holding Z darkens a tile and release restores it. Audio and battery persistence remain clearly identified as unimplemented.
- [Phase GB-03]: The rendered Z-down/held/up shades are asserted by the SDL smoke, and macOS package build plus downloaded-package consumer checks are required on every pull request. The 2026-10-09 UAT remains the single human confirmation of visible window behavior.
- [Phase GB-03]: Final verification passed 5/5 truths and UAT 33/33; PR #4 passed required exact-head checks and merged as `2b49dc5`.
- [Phase 04]: Hold a nonblocking exclusive advisory lock for the lifetime of each battery-backed player session; the guarantee covers cooperating GabbaBoy processes.
- [Phase 04]: Drive autosave from the core dirty generation and monotonic host time: two seconds quiet or ten seconds maximum age.
- [Phase 04]: On final save failure, require retry, explicit continue without saving, or cancellation before quit, reset, or replacement.
- [Phase 04]: Keep the original MBC1 battery fixture source, rights, manifest, pinned RGBDS recipe, and checked-in bytes together; ordinary tests verify the digest offline.
- [Phase 04]: Prove guest continuation with separate bounded processes and distinct missing-save, wrong-ROM-envelope, and altered-payload controls; this is software evidence, not physical hardware qualification.
- [Phase GB-05]: Expose audio-aware stepping as gbb_run_audio with caller-owned 48 kHz stereo frames; keep legacy run calls muted.
- [Phase GB-05]: Plan 05-03 adds wave/noise channels and all 16 NR52 status combinations as authored deterministic software-model evidence; active wave-RAM current-byte aliasing is an unqualified revision-scoped assumption. AUDIO-01 is complete for the documented digital model; analog, physical hardware, and perceptual output are not qualified.
- [Phase GB-05]: Active wave-RAM accesses alias the current byte in the scoped deterministic model; CPU-B revision variation is unqualified.
- [Phase GB-05]: Use an original per-instance Q15 8-tap FIR and the D-02 48 kHz high-pass approximation; preserve DSP history across output calls and reset it on APU reset.
- [Phase GB-05]: Reject overflowing PCM frame extents and overlap with the returned count before guest work; initialize a valid count output to zero.
- [Phase GB-05]: SDL callback services exact requested bytes and retains partial stereo frames across callbacks to avoid queue overrun.
- [Phase GB-05]: Unavailable audio sinks discard and count PCM immediately while preserving host-paced guest execution.
- [Phase GB-05]: Player gain is host-only, defaults to 100%, and is adjusted with bracket keys.
- [Phase GB-05]: Keep per-controller input keyed by stable SDL joystick IDs in a fixed bounded source table, and admit aggregate button changes to the guest queue before committing source state.
- [Phase GB-05]: Quiesce callbacks before counting and clearing ring, partial-frame, and SDL-stream PCM; perform reset and replacement host cleanup only after existing save transitions succeed.
- [Phase GB-05]: Treat SDL dummy audio and injected device events as software-path evidence; physical hotplug and audible quality remain unqualified.
- [Phase GB-05]: Bind the sustained result to the committed source revision, Release build, scoped DMG model, original licensed fixture, and PCM digest.
- [Phase GB-05]: Keep SDL queued-input bytes and application PCM underflow explicitly separate from playback latency and hardware starvation.
- [Phase GB-05]: Report dummy backend and default-device availability as software/device-presence evidence only; do not claim physical hotplug or perceptual qualification.
- [Phase GB-06]: CMake PROJECT_VERSION remains the product version source; release-please updates the matching v-prefixed tag version.
- [Phase GB-06]: Use GITHUB_TOKEN for version PRs and preserve the normal exact-head workflow approval gate.
- [Phase GB-06]: Keep the Linux candidate unpublished until the final Phase 6 release gate.
- [Phase GB-06]: Keep source, build, and downloaded-byte evidence in separate digest-linked receipts.
- [Phase GB-06]: Keep deterministic loader/battery/API regressions mandatory and enable compiler-integrated libFuzzer only when the matching Clang runtime is available; bound each input's size and work.
- [Phase GB-06]: Keep downloaded Windows release archive qualification on the existing native consumer lane and reuse the current C and C++ consumer projects.
- [Phase GB-06]: Force SDL dummy audio and video for the macOS player package smoke; report software-only behavior.
- [Phase GB-06]: Require an exact core/player release asset set and hash manifest before a platform candidate is ready.
- [Phase GB-06]: Keep stable support facts in a tracked versioned ledger and bind the exact tagged ledger blob and source SHA in a separate release sidecar.
- [Phase GB-06]: Record fixed-workload speed, process peak RSS, trace pairing, build duration, exact-source hosted check durations, and uncertainty; keep budgets advisory until repeated variance justifies one.
- [Phase GB-06]: Use the installed visible-demo fixture for successful frame output and sequentially load the MBC1 continuation fixture into the same opaque instance for save transfer.
- [Phase GB-06]: Install the visible-demo ROM with its manifest and license so the relocated native example needs no source-tree path.
- [Phase GB-06]: Keep raw battery persistence host-owned and replace only after an exclusive temporary file is flushed.
- [Phase 06.1]: Installed-consumer audio smoke is structural only (formula frame count, bounds, poison, twin/reset hash equality); no digest literal pinned
- [Phase 06.1]: 06.1-02: O_NOCTTY added to read_rom_file only; read_save_file intentionally unchanged (D-05 scope)
- [Phase GB-06.1]: 06.1-03: exact-head gate orders by run_number only; player run_attempt output taken from macos-player-package job object; terminal failures debounced over 2 polls on same (id, attempt)
- [Phase GB-06.1]: player-gate job is the single definition of player_required in ci.yml; check-player-result.sh fails closed on non-success gate
- [Phase GB-06.1]: 06.1-05: Phases 1 and 2 re-verified passed after PR 54 on the docs-only refresh branch; P1 covered_files gains wait-exact-head-ci.py and check-player-result.sh; P1 IN-01/IN-02 and P2 IN-01 fixed; new P1 IN-03/IN-04 deferred until the next wait-exact-head-ci.py change — D-10 refresh in order through execute-phase verification gates; D-09 forbids code fixes on the refresh branch
- [Phase GB-06.1]: 06.1-06: Phases 3 and 4 re-verified passed after PR 54 on the docs-only refresh branch; P3 covered_files gains wait-exact-head-ci.py and check-player-result.sh; P3 IN-01/IN-02/IN-03 fixed (IN-01 close-failure branch inspection-only); P4 stale only through session.c and test_session.c, covered set unchanged — D-10 refresh in order through execute-phase verification gates; D-09 forbids code fixes on the refresh branch
- [Phase GB-06.1]: 06.1-07: Phases 5 and 6 refreshed passed; Phase 6 covered_files gains tests/consumers/c/main.c and tests/consumers/cpp/main.cpp; P5 IN-01 fixed (documented); audit audio-consumer gap fixed; 06.1 did not change release.yml (pre-existing drift from v0.1.0 recorded)
- [Phase 07]: 07-01: the Libbet notice row pins the manifest, ROM and LICENSE.txt digests and libbet_notice checks all three; the verifier enforces the eight predicate addresses and five ROM anchors as constants
- [Phase 07]: 07-01: closure completeness is checked by EXPECTED_CLOSURE_SHA256 in required CI and by --derive-closure on the pinned source (45 files, conservative over-approximation); hosted reproduction stays unclaimed until a real run URL exists
- [Phase 07]: 07-02: gbb_accept_drive end_half_dots is the last logical deadline; predicate anchors_ok checks the SHA-256 before any anchor; drive callbacks share one context and max_batch is 1..64 (replay uses 32)
- [Phase 07]: D-027: mixer headroom divide-by-16 fixes Libbet clipping (D-19(i))
- [Phase 07]: 07-04: Libbet reproduction pins Pillow wheels for cp310-cp314 (linux x86_64, macOS arm64) and relies on the D-02 archive SHA-256 because GitHub reports no asset digest; hosted run stays null
- [Phase 07]: 07-05: Frame-digest oracles parse but the runner refuses them with exit 3 unsupported-oracle until the digest plan; runner uses tail_half_dots=0 since the verdict is T_hit
- [Phase 07]: D-028: D-19(ii) early Start taps are expected Libbet intro behaviour; joypad path unchanged
- [Phase 07]: 07-06: acceptance_negative_* forbid only status=(pass|fail|unsupported); invalid-input diagnostics print status=invalid by design
- [Phase 07]: D-029: Libbet checkpoint structure gate is >=2 distinct shades for title/play_start and >=3 for mid/hit (pinned title screen is 1-bit text); refines D-25; ratified by the owner 2026-10-11
- [Phase 07]: PCM window is stepping calls starting at or after play_start; run continues 1 s past T_hit so the window ends at T_hit+1 s (07-07)
- [Phase 07]: 07-08: gbb_case_applicability decides model before revision; model_fail strict (xfail only for declared reason); suite requires --expect-excluded and fails on excluded-count-mismatch; only dmg-cpu-b executes
- [Phase 07]: 07-09: daa LD B,B digest is a regression-class observation (mooneye.daa.frame), never a case-file reference; ldbb-controls.txt references are configure-enforced to the stdlib uniform-3 digest (D-26)
- [Phase 07]: 07-10: control regexes match the full status line (status=fail model=dmg-cpu-b reason=...); final_* fields print on every non-pass predicate line
- [Phase 07]: 07-11: D-16 PCM thresholds unchanged (peak_to_peak 2048, changes 4800); O=20290/164822, N=0/0 at exact head b6f982b, identical on Linux, macOS and Windows
- [Phase 07]: 07-11: stall report (D-18) also covers exit 3 and writes the failure PPM there; acceptance_parse_script_errors compares events field-wise (MSVC padding)
- [Phase GB-07]: 07-14: surface check forbids a superset of tokens (freopen, O_* flags, non-literal fopen mode, session persistence names); test_player_session compiles audio/input/script_smoke sources directly
- [Phase GB-07]: 07-15: DMG-CPU-B v1 ledger frozen at 5a55f19 in baseline commit 42faf9b; one ledger for all OS, changes only via CHANGES.md rows (D-30..D-35)
- [Phase 08]: 08-01: cartridge mapper section placed before gbb_instance; helpers take cart_state plus sizes
- [Phase GB-08]: MBC2 RAM stored canonical 0xF0|nibble; battery export is the stored image and import normalises before compare (08-02)
- [Phase 08]: 08-05: mbc2/mbc5 Mooneye derivatives admitted by manifest digest; budgets = ceil(2*ticks/100000)*100000; no D-27 patch needed (15/15 pass)
- [Phase 08]: 08-06: Mooneye mbc builder pin is read from the digest-checked parent manifest (sibling carries no builder object); type-mutation control requires an unmutated pass first
- [Phase 08]: 08-08: ninth bank bit proved by mbc5_bank_1ff plus test-only ninth-bit mutant (fails at C005, control passes); rom_64Mb is the 8 MiB loader/install-policy case only
- [Phase 08]: 08-09: D-049..D-062 recorded (Open Questions 1-7, D-08/D-10/D-32 refinements, D-29 amendment: ninth bit proved by mbc5_bank_1ff, not rom_64Mb)
- [Phase 09]: MBC3 selections 04-07 and 0D-FF map nothing (software-model decision, not hardware-qualified)
- [Phase 09]: MBC3 RAM code 05 is accepted only as an MBC30 marker and answered as UNSUPPORTED_CARTRIDGE_VARIANT after checksum
- [Phase 9]: 09-02: MagenTests ROMs admitted via explicit .gitignore negations; RGBDS 0.6.1 CI archive sha256 pinned in fixtures/magentests/SOURCES.md
- [Phase 9]: D-28: fuzz residue (data[0]&3u)==2u selects synthesised-length mode; 0 loader, 1/3 stateful
- [Phase 9]: 09-04: v0.1.2 save corpus generated by compiling the frozen tag's session.c directly against the pinned SDL3 prefix; reruns byte-identical
- [Phase 09]: 09-06: MBC2 guest selects store vs resume by cells 0-2 reading F3 FA F1; fresh RAM takes store branch
- [Phase 09]: 09-07: MagenTests oracle uses 16 frames plus a 0x149=0x03 negative control requiring shade 3; scan label GBB_FORBIDDEN_LABEL defaults to mooneye
- [Phase 9]: 09-08: rtc3test rebuild equality not claimed until hosted exact-head result=byte-identical (local Docker run was identical)
- [Phase 9]: 09-09: RTC latch on exactly 00 then 01 and unmapped selections 04-07 are project decisions, not hardware-confirmed
- [Phase 9]: 09-09: CI prints no_host_clock result per build leg; native-windows-x64 is MinGW GCC 14.2.0 and uses nm (research A2 resolved)
- [Phase 09]: 09-10: MBC5 continuation guest uses bank 0 and bank 15 GB5 markers; fixture-repro pin-checks and rebuilds all three continuation guests; mbc2/mbc3-rtc/mbc5 continuation ROMs are now tracked via .gitignore exceptions
- [Phase 9]: 09-11: import compares against the live clock projected to now so an identical re-import never bumps the generation; catch_up_policy_table is registered in the core inventory
- [Phase 9]: 09-12: rtc3test transcript groups coloured cells as [+...]/[!...] runs so millisecond numerics stay contiguous; expectations parsed from digest-pinned tests.md
- [Phase 09]: 09-13: MBC1 $03 keeps envelope v1 (-mbc1- name); all other battery types use v2 (-cart- name, 64-byte header, RAM then RTC block, saved_at stamp); a $03 save read from v2 is written back as v2
- [Phase 09]: 09-13: player classifies cartridges from the core (gbb_battery_size, gbb_rtc_catch_up(machine,0)); host clock read only by main.c player_clock_now
- [Phase 09]: 09-15: loader matrix oracle typed from D-27 tables, never from the core validator; RTC mutants use exactly-once tagged anchors with paired controls
- [Phase 09]: 09-16: catch-up applies once per open only for a timer cartridge with an accepted save; --clock-unix is confined to battery smoke argv
- [Phase 10]: 10-01: GATE-00 code tags compare class and basis only; doc row is the single shared GATE-00 entry
- [Phase 10]: 10-02: OAM-DMA CPU bus-conflict branches tagged UNKNOWN expected-failure:cgb-separate-buses (D-17)
- [Phase 10]: Runner carries GBB_RUNNER_PROFILE_CGB=(gbb_profile)2 until Plan 10-05 adds the public enum; CGB runs report create-failed or excluded, never fall back to DMG (D-25)
- [Phase 10]: 10-04: DMG post-boot cells record implemented values; Pan Docs divergences (IF, STAT, NR50, NR51, NR52, OBP0/1, PPU mode, P1) are POLICY with diverges-from-pandocs
- [Phase 10]: 10-05: gbb_create still rejects the CGB profile; probe/get_info append the D-02 API; PGB $143 rejected last on the CGB profile (GATE-67)
- [Phase 10]: 10-06: only compat cells pinned by a named Mooneye test carry HW_TEST; CGB-mode cells are PANDOCS/POLICY/ORACLE_SAMEBOY
- [Phase 10]: 10-06: GATE-68 CGB_ONLY covers compat title-sum B/HL; GATE-03 and GATE-57 are DMG_ONLY model_is_dmg; GATE-04..08 BOTH per-profile column
- [Phase 10]: 10-07: post-boot doc mirror is machine-checked by test_cgb_tables; header-derived cells show base value with rule in reason
- [Phase 10]: IE bits 5-7 stored on CGB profile only; DMG keeps & 0x1F (OQ2, owner veto item 6)
- [Phase 10]: Deferred register accesses latch bus_unsupported with address; latch also reported after interrupt entry
- [Phase 10]: 10-10: visibility matrix doc block lists only non-pre-CGB addresses (213 rows); EXISTING addresses must have no doc row
- [Phase 10]: 10-11: armed STOP on CGB mode latches UNSUPPORTED_BUS at FF4D (GATE-74, DEFERRED(12)); KEY0 lock proven behaviourally
- [Phase 10]: 10-12: CGB OAM DMA reads ROM/cart RAM via shared cart_read, banked VRAM/WRAM, E0-FF=$FF; DMG map frozen; cart and E0-FF cells are PANDOCS/ORACLE [VERIFY], not hardware; DMG bus-conflict rule kept on CGB (cgb-separate-buses) and pinned
- [Phase 10]: 10-13: cgb-banking guest selects CGB expectations from header OR profile; only a DMG header on the DMG profile expects frozen DMG behaviour (so the CGB build on the DMG profile fails exactly the CGB-only cells); nine result cells C002..C00A
- [Phase 10]: 10-14: Mooneye CGB fixtures record original_sha256 (unpatched rebuild recomputed by the script); boot_div claims CGB-A..E only; boot_hwio-C and unused_hwio-C admitted as expected-unsupported at FF76
- [Phase 10]: 10-16: expected-unsupported refused address read via gbb_test_last_unsupported_address; real boot_div ROM confirms compat DIV window 0x2678..0x267B
- [Phase 10]: 10-17: D-22 review trigger fired (Phase 10 DMG at 105.6-107.3% of Phase 7 baseline time, advisory, loaded host); owner decides under D-016, no optimisation
- [Phase 10]: 10-18: fuzz profile selected by data[0] bit 7; original 0xFF reproducer now runs on CGB with a 0x7F DMG twin
- [Phase 10]: D-070 half-dot master timeline ADR adopted; D-071..D-075 record IE, ch1 policy, deferred-register asymmetry, GATE-00, FEA0-FEFF/cgb-separate-buses
- [Phase 10]: Phase 10 evidence head 2fe078e8f08ed98ba0ac0e244971e7c0ead16b1e is exact-head green (8 required checks, 7 fixture-repro jobs); PR #66 is ready and left open until /gsd-verify-work 10 passes
- [Phase 10]: The +5% banking benchmark review trigger fired (about +6 to 7 percent vs the Phase 7 baseline, advisory on a loaded host); no optimisation in Phase 10, owner decides per D-016
- [Phase 11]: libbet shade pin runs 900 frames (blank earlier); pins are regression, not hardware evidence
- [Phase 11]: 11-02: palette RAM lock is a plain mode-3 predicate (GATE-76) and OPRI is stored without priority effect (GATE-77); both UNKNOWN research:14
- [Phase 11]: 11-02: post-boot BCPS is C0 so bit 7 auto-increment is on; visibility port cells park the index at 0 and turn the LCD off
- [Phase 11]: 11-05: truth table drives the real pixel functions; implementation matched the oracle with no core change; 12 per-input mutants each fail
- [Phase 11]: 11-06: RGB555 frame call and compat palette API are public; skewed-validator and bit-15 mutants guard them (GATE-83)
- [Phase 11]: 11-07: colour-hblank guest uses a jr spin, not HALT, because gbb_run returns at each HALT with budget left
- [Phase 11]: 11-07: fixtures/cgb-colour ROMs are admitted by a wildcard .gitignore exception and added as manifest rows with per-row recipes
- [Phase 11]: 11-08: CRAM guest ends in a jr spin (not HALT) because gbb_run returns at every HALT; markers read with gbb_peek_ram after 10 frames
- [Phase 11]: 11-09: CGB runner frame cases print GBB-RGB555LE-v1 digests under frame555/observed555; store chosen from instance profile; CGB progress-predicate observation refused with frame-unsupported-profile
- [Phase 11]: 11-10: bg_oam_priority passed its predicate unmodified; no expected-unsupported record; AGE deviation (D-20) stated in ELIGIBILITY.md
- [Phase 11]: 11-11: acid2 local runner uses frame-digest@ldbb and a PNG decoder covering palette and greyscale (pinned references are not 8-bit RGB)
- [Phase 11]: 11-12: select_profile seam player_session_probe_profile serves the three session sites; CGB smoke pins the uploaded RGBA digest plus 40 independently computed spot pixels
- [Phase 11]: D-04: no per-dot model hoist; the D-22 trigger did not fire (DMG median 98.5 to 100.2 percent of the Phase 10 head, margins 1.5 to 1.9)
- [Phase 11]: D-32: ten PPU timing gates re-assigned research:14; model_gates_no_phase11_rows guards against a returning Phase 11 owner tag
- [Phase 12]: Recorded eight pre-change CGB single-speed identity digests at fb45111; regression pins are not hardware evidence.
- [Phase 12]: Keep speed state private to the core test seam; no public header or API symbol changes.
- [Phase 12]: Model STOP's 2 M cost in normal-speed half-dots and apply the speed shift once in instruction_cost.
- [Phase 12]: AGE fixture bytes are tied to pinned source commit/tree and RGBDS 1.0.1 archive digests.
- [Phase 12]: The byte-difference negative control mutates rebuilt bytes so it reaches the comparator after committed-fixture integrity validation.
- [Phase 12]: Runtime-mask mutant cores remain build-tree-only and use forward/reverse exactly-once anchor checks.
- [Phase 12]: Reset mutants target the explicit reset boundary because post-boot initialization also clears some speed fields.
- [Phase GB-12]: Upstream AGE Verified lines remain source attestations, while manifest expected_role records D-19 expectations.
- [Phase GB-12]: Store timer, serial and DMA countdowns in CPU ticks so speed changes preserve integer remainder state.
- [Phase GB-12]: Use DIV bit 12 at normal speed and bit 13 at double speed for frame sequencing, including divider reset.
- [Phase GB-12]: STOP case 3 switches immediately without a stall; only case 4 loads the stall.
- [Phase GB-12]: DMG, compatibility and unarmed STOP, including held-button behavior, stay on the existing STOP path.
- [Phase GB-12]: Wake is sampled only between persisted stall M-cycle steps so host budget partitioning does not change resume time.
- [Phase GB-12]: Normal-speed realignment uses a four-half-dot tail at phase four; the provisional stall duration remains for plan 12-09 re-measurement.
- [Phase GB-12]: The signed M31 stall-offset seam is wired with a zero default and a passing no-op check.
- [Phase GB-12]: Resolve Phase 12 model-gate ownership at the code-tag/table level; preserve the Phase 14 timer and serial differences and named unsupported STOP subcases.
- [Phase GB-12]: Keep the speed-switch stall constant provisional until plan 12-09 measures the committed-core AGE window; do not pin a value from the prototype alone.
- [Phase GB-12]: Plan 12-10: derive timing bounds from clock units and measured guest-loop resolution, never from fitted emulator outputs.
- [Phase GB-12]: Plan 12-10: start the OAM DMA straddle in VBlank and read at M+159/M+161 to isolate DMA from PPU OAM arbitration.
- [Phase GB-12]: Plan 12-10: pin audio and frame digests through public APIs with M17/M1 mutant failures and mask-zero controls.
- [Phase GB-12]: Use a separate selector guest for hostile STOP paths; keep speed.gb, its digest, and identity pins unchanged.
- [Phase GB-12]: Derive hostile timing intervals from D-02/D-08, 912 master half-dots per line, D-09 realignment, and the locked 0x20004 T stall.
- [Phase GB-12]: Capture pending IF before disarming IE/IF for the guest idle loop.
- [Phase 12]: Installed frame generation is verified through gbb_frame_info from gbb_copy_frame_rgb555, preserving the public ABI.
- [Phase 12]: Continue public runs after HALTED_IDLE until the first frame is available, bounded by two frame durations.
- [Phase 12]: CGB speed fixture rebuilds validate manifest recipes and separate harness errors from byte differences.
- [Phase 12]: The fixture-repro workflow cross-checks CGB speed RGBDS 1.0.1 pins and archive digests.
- [Phase 12]: Offline CGB speed controls also reject a tampered workflow manifest pin under D-069.
- [Phase 12]: Use a private read-only master-time getter to prove per-call consumed-time equality during stalls and STOP waits; CPU traces alone are insufficient.
- [Phase 12]: Keep CGB compatibility and DMG controls model-applicable: compatibility KEY1 reads as $FF, and the DMG twin verifies STOP/wake without accessing KEY1.
- [Phase 12]: Pin AGE ROM pass and expected-failure outcomes from committed-core measurements; the CGB-E Tima failure triggers the D-19 contingency, so both Tima ROMs are expected failures and the B/C claim is dropped.
- [Phase 12]: Keep Linux AGE fixture reproduction provisional until a hosted fixture-repro run verifies the digest; do not claim hardware evidence.
- [Phase 12]: Phase 12 plan 12-17: M28 adds one half-dot only on transitions to double speed; measured AGE discrimination includes spsw-mode0-cgbBCE while spsw-div-cgbBCE remains low-bit-insensitive.
- [Phase 12]: Phase 12 plan 12-17: Every named expected failure has an exact registered behavior pin, with manifest-to-doc and pin inventory checks plus negative controls.
- [Phase GB-12]: Plan 12-18 preserves the CGB speed API surface: KEY1 bit 7 is guest-visible and there is no public speed getter.
- [Phase GB-12]: AGE evidence is limited to two passing cases and eleven named expected failures; the corrected M28 mutation applies only when switching to double speed.
- [Phase 13]: Treat the post-instruction service boundary, four-half-dot byte cadence, and 64-half-dot block as software policy; physical CGB-E timing remains unknown.
- [Phase 13]: FF51-FF54 CPU reads return FF as policy while writes apply the documented source and destination masks.
- [Phase 13]: CGB HDMA source admission is limited to ROM, cartridge mapping, and direct WRAM; absent or disabled cartridge RAM retains cart_read $FF semantics.
- [Phase 13]: Validate each 16-byte source block and destination before mutation; preserve completed prefixes and rejected cursors/status on unsupported blocks.
- [Phase 13]: Keep destination $A000 representable after $9FF0; complete a final block and stop remaining work without wrapping.
- [Phase 13]: Source banks and VBK are sampled per admitted block; physical CGB-E timing and overflow status remain UNKNOWN.
- [Phase 13]: HALT wakes on real IF/IE and dispatches normally; admitted HDMA finishes and a later HBlank is required for new admission.
- [Phase 13]: Speed-pause and DMA residuals advance independently; IRQ wake is sampled at the persisted M boundary after admitted DMA retires.
- [Phase 13]: STOP freezes DMA and device remainders until wake; no missed HBlank is synthesized.
- [Phase 13]: Shared-tick software order is OAM DMA, HDMA, then PPU; physical CGB-E collision timing remains UNKNOWN.
- [Phase 13]: Accepted FF55 starts require checked master-time headroom for instruction cost plus count×64 finite byte work, without forecasting HBlank waits.
- [Phase 13]: Keep HDMA partition snapshots private and explicit; hash fields individually and do not expose raw C state or a new save-state API.
- [Phase 13]: Plan 13-07: Admit MagenTests HDMA only with release 0.5.0, pinned source revision, RGBDS 0.6.1 tool digest, preserved notices, and byte-identical rebuild.
- [Phase 13]: Plan 13-07: Derive the destination map from the linker address and FF52 alignment, then require source-derived guest data and green-screen structure before digest comparison.
- [Phase 13]: Plan 13-07: Report only selected software-model and differential evidence; physical CGB-E hardware qualification remains open.
- [Phase 13]: Plan 13-09 preserves the D-06/Pan Docs conflict; software-model outcomes do not qualify physical CGB-E behavior.
- [Phase 13]: Optional Mealybug CGB-C remains not-run:rights-gate-G1 and outside the CGB-E denominator.
- [Phase 13]: Pin every relocated consumer configure to the package config under the current install prefix.
- [Phase 13]: Check positive FF55 completion, ROM-derived readback, and DIV timing; the disabled twin diagnoses missing data and CPU-steal timing because FF55 reads FF before and after completion.
- [Phase 13]: Preserve the exact installed fixture child allow-list and reject SameSuite/Magen bytes under neutral filenames.
- [Phase 13]: Run one all-surface native/player claim predicate against the checkout or exact-path JSON subject snapshots.
- [Phase 13]: CGB-07 is closed by 37/37 goal verification; physical CGB-E remains UNKNOWN/POLICY, with no local libFuzzer campaign.
- [Phase 15]: 15-04: adoption checker reuses the production CGB claim parser with a negation guard; fuzz and publication stay unclaimed; notices carry a recomputed manifest/LICENSE digest table for all 19 fixture dirs
- [Phase 15]: 15-07: source archive bound to tag via embedded commit ID plus tagged tree blob IDs; --verify-final requires the source archive receipt as distinct evidence; --verify gains product fixture-leak check
- [Phase 15]: 15-06: fuzz speed oracle scoped to CGB profile; hosted verifier no longer forwards credentials on redirect; exact-source campaign run 39357838513 validated
- [Phase 15]: 15-08: producer reuse needs unaltered producer SHA, justification, covered-input Git-object equality and producer-checkout validation; published readback requires a distinct final download directory
- [Phase 15]: 15-09: release evidence is transported through the unpublished draft; per-run receipts are attached once and reused on retry, never replaced
- [Phase 15]: 15-09: v02_support_ledger is a receipt-free static ledger check; receipt-bound --check-current runs in the release corpus job after the receipt exists
- [Phase 15]: 15-09: downloaded sidecars are verified with opt-in --evidence-only (no producer build tree); generation and --check-current are unrelaxed
- [Phase 15]: Merge the version PR only after the non-publishing hosted rehearsal is green on its exact tree; resume a failed release run on the same unpublished draft and run control-plane verifiers from the workflow commit

### Pending Todos

None outside the roadmap.

### Blockers/Concerns

- Phase 13 boundary triage: the live open inventory contains only draft PR #69 and zero open issues. Current branch-protection readback is unavailable (GitHub integration 403); the ruleset inventory is empty. No protection bypass or new protection claim is made.
- phase.complete emitted two non-blocking literal-path warnings for command-form SUMMARY coverage refs (`bash tests/scripts/verify-dmg-baseline.sh`, `python3 -I tests/scripts/verify-model-gates.py`). Both scripts exist and their checks pass; the strict summary_coverage parser passes all entries. These are parser path interpretations, not missing implementations.

- Historical 2026-10-09 v0.1 audit initially accepted 2/6 verification reports; after the Phase 1 refresh, the live gate accepted 3/6 and the strict requirement matrix accepted 15/35. No integration blockers were found. PR #43 is squash-merged. At that historical boundary PR #41 was open; it is no longer in the current open inventory.
- Historical branch-protection readback recorded the three strict required CI contexts for administrators. Follow-up readback showed no required approving-review gate. PR #34 predates admin enforcement and had no recorded approval; its exact required CI contexts were green when merged.
- Phase 1's refreshed validation report is `validated` and Nyquist-compliant, with 179/179 local CTest. Phase 3 Nyquist validation is `validated`, and its UAT is complete at 34/34.

- Phase 2's refreshed canonical verifier passed all five requirements and roadmap truths. The current full local CTest run passed 179/179, the focused Phase 2 selection passed 88/88, all three admitted headless runner cases passed, and the protocol probe recorded zero PPU accesses. No physical DMG-CPU-B observation or broad compatibility claim is made. See [Phase 2 verification](milestones/v0.1-phases/GB-02-dmg-cpu-bus-and-time/02-VERIFICATION.md).
- The admitted corpus is three derived headless reporting closures (one CPU, two timer). Original Mooneye reporting paths depend on PPU/LY behavior outside scope and remain excluded. No physical DMG-CPU-B observation occurred; no hardware qualification is claimed.
- Phase 1 PR #1 and Phase 2 PR #2 were merged on 2026-10-07 after their required exact-head checks passed. The 2026-10-07 triage found no open PRs or issues at that time. Phase 2 verification is limited to its documented DMG-CPU-B CPU/timer scope; no physical DMG observation or PPU qualification is claimed.
- Phase 6 has no open goal, requirement, review, or high/blocking security finding. The release workflow's original post-publication readback failure was repaired before closeout; the live release API and a fresh download reconcile the published 18-asset inventory.
- Exact CPU-B behavior, physical DMG/MBC1 qualification, physical audio/hotplug, perceptual output, Developer ID signing/notarization, and live Playstead GB integration remain unqualified and are stated as limits, not passing claims.
- [Phase 8] Resolved: the D-29 ninth-bit mutant now targets `mbc5_bank_1ff` (D-062); upstream `rom_64Mb` never selects banks >= 256.
- [Phase 9] Resolved: Phase 8 WR-02 (player hard-coded unsupported battery types) — classification now comes only from the core, guarded by `player_session_classification_drift`. Former note: `src/player/session.c` hard-codes the unsupported battery types $06/$1B/$1E. When CART-06 adds MBC2/MBC3/MBC5 persistence, replace the list and add a test that classifies every core type byte as either `battery_backed` or `battery_unsupported`.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 261020-hr8 | Reconcile Phase 11 and 13 SUMMARY claims for CGB-05, CGB-09 and CGB-07 | 2026-10-20 | ba27c4b | [261020-hr8-reconcile-phase-11-and-13-summary-comple](./quick/261020-hr8-reconcile-phase-11-and-13-summary-comple/) |

### Roadmap Evolution

- Phase 06.1 inserted after Phase 6: Address v0.1 tech debt: CI workflow info items and audio consumer coverage (URGENT)
- 2026-10-10: v0.2 roadmap created — Phases 7–15 continue v0.1 numbering. Order follows research/v0.2/SUMMARY.md: acceptance + DMG baseline (7); seam merged with MBC5 and MBC2 (8, MBC5/MBC2 plans parallel after the seam plan); MBC3 + RTC + loader matrix + new-mapper continuation (9); CGB profile/banking (10); colour PPU + player colour (11); double speed (12) and HDMA (13) kept separate and sequential; CGB-E qualification + corpus (14); CGB acceptance, ledger and release (15). Deep phase research flagged for 9, 11, 12, 13, 14. Rights gates: G5/G2 on 7; G1 on 9, 11, 14; G3 on 9; G4 on 11.

## Deferred Items

Active v0.2 requirements are in [REQUIREMENTS.md](REQUIREMENTS.md) (28/28 mapped); deferred v0.3 items (STATE-01, INT-01) and later direction are in its Future section and [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md), not counted in active coverage.

## Session Continuity

Completed stage: Phase 13 — CGB HDMA, verification refresh; paused at the phase boundary.
Next phase: 14 — CGB-E Model Qualification and Corpus (verification refresh only).
Next command: `/gsd-execute-phase 14`.

## Operator Next Steps

Resume Phase 14 verification using the command above. Do not archive or tag v0.2 until its remaining verification refresh and audit items are resolved or explicitly overridden. Preserve both automatic advance flags as false.
