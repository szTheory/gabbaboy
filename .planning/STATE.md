---
gsd_state_version: "1.0"
milestone: v0.1
current_phase: 03
current_phase_name: Visible Interactive DMG
status: executing
stopped_at: Plan 03-10 complete with unavailable hardware evidence recorded; Plan 03-11 is next
last_updated: "2026-10-07T22:06:15Z"
last_activity: 2026-10-07
last_activity_desc: Plan GB-03-10 completed; Plan GB-03-11 next
state_head: 405568397d3a8a6fe5dda4d8420e145e8744fdce
progress:
  total_phases: 6
  completed_phases: 2
  total_plans: 33
  completed_plans: 32
milestone_name: limited DMG preview
---

# Project State

## Project Reference

See: [PROJECT.md](PROJECT.md) (updated 2026-10-03)

**Core value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Current focus:** Phase GB-03 — Visible Interactive DMG

## Current Position

Phase: GB-03 (Visible Interactive DMG) — EXECUTING
Plan: 11 of 11
Status: Executing Phase GB-03
Last activity: 2026-10-07 — Plan GB-03-10 completed; Plan GB-03-11 is next

Progress: [███░░░░░░░] 33% of milestone phases complete; Phases 1 and 2 passed verification.

## Performance Metrics

- Unique plans: 27; average duration / total execution time: 25 min / 670 min. Phase 2 completion is based on goal verification, not task count alone.
- Per-phase metrics / recent trend: Phases 1 and 2 are verified complete; ten of eleven Phase 3 plans have summaries, with Plan 03-11 next. Phase 3 still has VIDEO-02/03 evidence gaps. Plan 02-15 is superseded/non-runnable and remains historical.
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

### Pending Todos

None outside the roadmap.

### Blockers/Concerns

- Phase 2 has no open verification or security blocker. All five requirements are complete at implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989`; see [verification](phases/GB-02-dmg-cpu-bus-and-time/02-VERIFICATION.md), [validation](phases/GB-02-dmg-cpu-bus-and-time/02-VALIDATION.md), and [security](phases/GB-02-dmg-cpu-bus-and-time/02-SECURITY.md).
- The admitted corpus is three derived headless reporting closures (one CPU, two timer). Original Mooneye reporting paths depend on PPU/LY behavior outside scope and remain excluded. No physical DMG-CPU-B observation occurred; no hardware qualification is claimed.
- Phase 1 PR #1 and Phase 2 PR #2 were merged on 2026-10-07 after their required exact-head checks passed. Current GitHub triage found no open PRs or issues. Phase 2 verification is limited to its documented DMG-CPU-B CPU/timer scope; no physical DMG observation or PPU qualification is claimed.
- The original nine Phase 3 plans are complete. VIDEO-01, VIDEO-04, and VIDEO-05 are complete; exact-head CI run 37686137977 and downloaded-package consumer run 37686137834 passed at source `fd62c48d84b8339435fefd008147f0c06f696e0e`. VIDEO-02 simultaneous PPU/DMA evidence and D-08/VIDEO-03 JOYP interrupt evidence remain open. Live desktop perception and physical DMG-CPU-B observation are unavailable. Gap-closure Plans 03-10/03-11 are ready; execute those before Phase 4 or claiming Phase 3 complete.
- Phase 3 gap execution is in progress. Plan 03-10 is complete with commits `eff0896`, `30187c9`, and `2c73591`; its Task 3 disposition records that no lawful, available observation setup or raw record was available to this run. DMA/PPU passed 14 focused cases, JOYP/events passed 8, and the combined DMA/JOYP filter passed 14. Plan 03-11 is next. Phase verification remains `gaps_found`; VIDEO-02 and D-08/VIDEO-03 stay open where CPU-B applicability is unsupported. Do not start Phase 4 or claim Phase 3 complete.
- Native host support floors beyond the verified CI matrix, signing, and live Playstead integration remain later release/adoption work.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 261006-r6w | Fix the bus_unsupported_stack fixture so RET NC tests its intended condition under checksum-selected DMG startup flags; validate the offline test inventory. | 2026-10-06 | 3231d21 | [261006-r6w-fix-the-bus-unsupported-stack-fixture-so](./quick/261006-r6w-fix-the-bus-unsupported-stack-fixture-so/) |

## Deferred Items

Future requirements and acceptance direction remain in [REQUIREMENTS.md](REQUIREMENTS.md#next-milestone-requirements--gbgbc-breadth) and [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md); none are counted in active coverage.

## Session Continuity

Last session: 2026-10-07
Stopped at: Phase GB-03 gap execution; Plan 03-10 is complete with its unavailable-observation dependency recorded; Plan 03-11 is next
Resume file: .planning/.continue-here.md
Next command in fresh context: $gsd-execute-phase 3 --gaps-only
Continuation note: [.continue-here.md](.continue-here.md)
Completed workflow stage: **Phase 3 gap execution — Plan 03-10.** The source ledger leaves unsupported DMA collision and JOYP IF timing unqualified; the manual transcription and schematic revision are corrected; the unavailable hardware setup is recorded as an unresolved dependency. The automated focused filters passed. Continue with Plan 03-11 using `$gsd-execute-phase 3 --gaps-only`; its prior plans now have summaries, so do not repeat completed work. Stop after Phase 3 and keep both auto-advance flags false.
Next roadmap phase: **Phase 4 — MBC1 and Safe Battery Continuation.** It has not started; do not start it until Phase 3 gap execution and verification are complete.
