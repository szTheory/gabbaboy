---
gsd_state_version: "1.0"
milestone: v0.1
current_phase: 05
current_phase_name: DMG Audio and Stable Playback
status: executing
stopped_at: Completed GB-05-03-PLAN.md
last_updated: "2026-10-08T13:41:22.961Z"
last_activity: 2026-10-08
last_activity_desc: Phase GB-05 execution started
state_head: 2fcadb3ca6d600bb8de4e5a42837b15f2a506b3e
progress:
  total_phases: 6
  completed_phases: 4
  total_plans: 49
  completed_plans: 45
milestone_name: limited DMG preview
---

# Project State

## Project Reference

See: [PROJECT.md](PROJECT.md) (updated 2026-10-07)

**Core value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Current focus:** Phase GB-05 — DMG Audio and Stable Playback

## Current Position

Phase: GB-05 (DMG Audio and Stable Playback) — EXECUTING
Plan: 4 of 7
Status: Executing Phase GB-05
Last activity: 2026-10-08 — Phase GB-05 execution started

Progress: [███████░░░] 67% of milestone phases complete. Phases 1–4 passed goal verification. Phase 4 has 7/7 plan summaries and 4/4 verified goal truths; the core inventory passed 155/155, the relocated package inventory passed 160/160 plus a 155/155 core-only subset, the macOS player/package inventory passed 37/37, and exact hosted PR checks and downloaded Linux/macOS/player package receipts passed on source head `79f83f627ffb3631811b2f39b23081117ebaab8f`. The Windows fixture-byte checkout issue was fixed with narrow Git attributes and re-reviewed clean. See the Phase 4 verification, validation, security, and UI review artifacts. Phase 5 has seven plans in seven dependency-ordered waves; Plans 05-01 through 05-03 are complete with summaries. Plan 05-03's scoped APU/tracer regressions passed 8/8, completing AUDIO-01's deterministic digital-channel scope with explicit revision and perceptual limits. Phase 5 remains in progress; no physical DMG or perceptual audio qualification is claimed.

## Performance Metrics

- Unique plans: 28; average duration / total execution time: 25 min / 700 min. Phase 2 completion is based on goal verification, not task count alone.
- Per-phase metrics / recent trend: Phases 1–3 are verified complete; Phase 3 has 13/13 plan summaries, 5/5 goal truths, 33/33 UAT checks, a user-confirmed packaged Z press/release, and 141/141 local CTest. PR #4's required exact-head checks passed before merge. D-025 bounds VIDEO-02/03 to the confidence-qualified software model; no physical CPU-B measurement is claimed. Plan 02-15 is superseded/non-runnable and remains historical.
- Emulator correctness, speed, memory, and CI baselines: No general hardware/gameplay baseline. At implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989`, the local offline inventory passed 104/104 with no skips, the relocated installed C/C++ inventory passed 109/109, the runner passed its fixed one-CPU/two-timer derived corpus, hosted CI run 37620710587 passed, and fixture reproduction run 37620710600 passed. Independent verification passed all five CPU requirements. Original upstream PPU-dependent reporting paths remain excluded; no physical DMG hardware test occurred.

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
| Phase GB-05 P03 | 13min | 2 tasks | 7 files |

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
- [Phase GB-03]: Final verification passed 5/5 truths and UAT 33/33; PR #4 passed required exact-head checks and merged as `2b49dc5`.
- [Phase 04]: Hold a nonblocking exclusive advisory lock for the lifetime of each battery-backed player session; the guarantee covers cooperating GabbaBoy processes.
- [Phase 04]: Drive autosave from the core dirty generation and monotonic host time: two seconds quiet or ten seconds maximum age.
- [Phase 04]: On final save failure, require retry, explicit continue without saving, or cancellation before quit, reset, or replacement.
- [Phase 04]: Keep the original MBC1 battery fixture source, rights, manifest, pinned RGBDS recipe, and checked-in bytes together; ordinary tests verify the digest offline.
- [Phase 04]: Prove guest continuation with separate bounded processes and distinct missing-save, wrong-ROM-envelope, and altered-payload controls; this is software evidence, not physical hardware qualification.
- [Phase GB-05]: Expose audio-aware stepping as gbb_run_audio with caller-owned 48 kHz stereo frames; keep legacy run calls muted.
- [Phase GB-05]: Plan 05-03 adds wave/noise channels and all 16 NR52 status combinations as authored deterministic software-model evidence; active wave-RAM current-byte aliasing is an unqualified revision-scoped assumption. AUDIO-01 is complete for the documented digital model; analog, physical hardware, and perceptual output are not qualified.
- [Phase GB-05]: Active wave-RAM accesses alias the current byte in the scoped deterministic model; CPU-B revision variation is unqualified.

### Pending Todos

None outside the roadmap.

### Blockers/Concerns

- Phase 2 has no open verification or security blocker. All five requirements are complete at implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989`; see [verification](phases/GB-02-dmg-cpu-bus-and-time/02-VERIFICATION.md), [validation](phases/GB-02-dmg-cpu-bus-and-time/02-VALIDATION.md), and [security](phases/GB-02-dmg-cpu-bus-and-time/02-SECURITY.md).
- The admitted corpus is three derived headless reporting closures (one CPU, two timer). Original Mooneye reporting paths depend on PPU/LY behavior outside scope and remain excluded. No physical DMG-CPU-B observation occurred; no hardware qualification is claimed.
- Phase 1 PR #1 and Phase 2 PR #2 were merged on 2026-10-07 after their required exact-head checks passed. Current GitHub triage found no open PRs or issues. Phase 2 verification is limited to its documented DMG-CPU-B CPU/timer scope; no physical DMG observation or PPU qualification is claimed.
- Phase 3 is complete with 5/5 verified truths, 33/33 UAT passes, 141/141 local CTest, clean code review, and required exact-head PR #4 checks. One medium threat, T-03-27, remains below the configured high-severity block threshold; revisit its automated preview-limitation assertion during release work. Exact CPU-B timing/lane and universal PPU-revision parity remain unmeasured; these are explicit evidence limits, not Phase 3 blockers under D-025.
- Native host support floors beyond the verified CI matrix, signing, and live Playstead integration remain later release/adoption work.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 261006-r6w | Fix the bus_unsupported_stack fixture so RET NC tests its intended condition under checksum-selected DMG startup flags; validate the offline test inventory. | 2026-10-06 | 3231d21 | [261006-r6w-fix-the-bus-unsupported-stack-fixture-so](./quick/261006-r6w-fix-the-bus-unsupported-stack-fixture-so/) |

## Deferred Items

Future requirements and acceptance direction remain in [REQUIREMENTS.md](REQUIREMENTS.md#next-milestone-requirements--gbgbc-breadth) and [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md); none are counted in active coverage.

## Session Continuity

Last session: 2026-10-08T13:41:22.916Z
Stopped at: Completed GB-05-03-PLAN.md
Resume file: .planning/phases/GB-05-dmg-audio-and-stable-playback/05-04-PLAN.md
Next command in fresh context: $gsd-execute-phase 5
Continuation note: [.continue-here.md](.continue-here.md)
Completed workflow stage: **Plan GB-05-03 execution, within Phase 5 of 6.** The four-channel authored APU/tracer tests passed 8/8 and AUDIO-01 is complete for the deterministic digital software model. No physical DMG, analog-output, or perceptual qualification is claimed. Phase 5 remains active; AUDIO-02, AUDIO-03, HOST-01, and HOST-02 remain pending. Keep both auto-advance flags false.
Next plan: **GB-05 Plan 05-04 — Fixed-point resampler, high-pass and bounded PCM API**, within Phase 5 — DMG Audio and Stable Playback. The exact continuation command is `$gsd-execute-phase 5`. After Phase 5 is verified, the next phase is **Phase 6 — Qualified DMG Release and Consumer Handoff**.
