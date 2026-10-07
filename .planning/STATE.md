---
gsd_state_version: "1.0"
milestone: v0.1
current_phase: 02
current_phase_name: DMG CPU, Bus, and Time
status: Ready for independent verification
stopped_at: Completed GB-02 Plan 02-16 runner and exact-revision qualification; independent verification next
last_updated: "2026-10-07T03:06:23.682Z"
last_activity: 2026-10-07
last_activity_desc: Plan 02-16 passed runner, offline/relocated inventory, and exact-PR-SHA hosted gates; CPU-01 through CPU-05 remain pending independent verification.
state_head: 8481d603b780af7889832ea3a8d3ad84d2439ba5
progress:
  total_phases: 6
  completed_phases: 1
  total_plans: 21
  completed_plans: 21
milestone_name: limited DMG preview
---

# Project State

## Project Reference

See: [PROJECT.md](PROJECT.md) (updated 2026-10-03)

**Core value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Current focus:** Phase GB-02 — DMG CPU, Bus, and Time

## Current Position

Phase: GB-02 (DMG CPU, Bus, and Time) — EXECUTING
Plan: 16 of 16
Status: Ready for independent verification
Last activity: 2026-10-07 — Plan 02-16 passed runner, offline/relocated inventory, and exact-PR-SHA hosted gates; CPU-01 through CPU-05 remain pending independent verification.

Progress: [██░░░░░░░░] 17% of milestone phases complete; Phase 1 has 5/5 plans and passed verification

## Performance Metrics

- Total unique plans executed: 21; plan execution does not imply phase qualification.
- Average duration / total execution time: 24 min / 502 min recorded across 21 plans.
- Per-phase metrics / recent trend: Phase 1 complete; all 16 live Phase GB-02 plans now have summaries, including Plan 02-16. Plan 02-15 is superseded after its preserved halt. Independent Phase 2 verification is next.
- Emulator correctness, speed, memory, and CI baselines: No general hardware/gameplay baseline. The latest local offline core inventory passed 100/100 with no skips; relocated installed inventory passed 105/105, including C/C++ consumers. The runner passed all three admitted derived candidates with the fixed one-CPU/two-timer denominator. Final PR SHA `8481d603b780af7889832ea3a8d3ad84d2439ba5` passed Linux, macOS, Windows, Linux ASan/UBSan, CMake-floor relocation, and original/candidate fixture-reproduction jobs. The original ROM reporting paths remain PPU/LY-limited; no physical hardware test occurred. CPU-01 through CPU-05 remain pending independent Phase 2 verification.

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
- [Phase GB-02]: The source-qualified eligible denominator remains fixed regardless of emulator outcomes.
- [Phase GB-02]: Replace the separately unqualified Mooneye font asset with an original same-size zero asset while preserving hardware-test logic.
- [Phase GB-02]: The tracer-only preparation runner does not qualify Mooneye guests; strict protocol-aware results belong to Plan 02-08.
- [Phase GB-02]: LD B,B remains an ordinary CPU instruction; the host runner alone classifies Mooneye register results.
- [Phase GB-02]: DAA runner budget is 2000000 half-dots based on the pinned source's 4096-case workload and 1343488-half-dot minimum.
- [Phase GB-02]: The strict eligible corpus denominator remains one CPU and two timer fixtures regardless of emulator outcome.
- [Phase GB-02]: Installed C and C++ consumers verify the fixed timestamped-event queue, bounded results, and caller-owned diagnostics through the relocated public package.
- [Phase GB-02]: Separate fixture reproduction runs on PR/push/manual triggers with pinned tools and sources; ordinary test inventories remain offline and use checked-in ROM bytes.
- [Phase GB-02]: Do not fabricate LY or bypass assertions to close corpus failures; valid digests/reproduction do not prove phase applicability.
- [Phase GB-02]: DMG-CPU-B startup F is selected from the retained ROM header checksum at load and reset.
- [Phase GB-02]: RET and RETI stack reads use offsets 8/16; taken conditional RET retains 16/24 and untaken RET performs no stack read.
- [Phase GB-02]: Keep checked-in Mooneye ROM bytes and the fixed three-case denominator unchanged until a deterministic cross-host linker recipe is qualified.
- [Phase GB-02]: Preserve the pinned Mooneye manifest's exact raw bytes at checkout with a path-scoped `-text` attribute; continue strict SHA-256 admission.
- [Phase GB-02]: Pin candidate linker ordering to `wlalink -nS -d -S`; admit derived fixtures only after exact local/hosted byte identity, source/rights provenance, protocol probes, and strict manifest verification.
- [Phase 02]: Bind Mooneye pass/fail to its source-qualified callback and exact result PC.
- [Phase 02]: Label candidate fixtures as derived headless reporting closures and retain the unchanged upstream assertions; do not infer original-ROM PPU applicability or hardware qualification.
- [Phase 02]: Keep CPU-01 through CPU-05 pending until independent phase verification assesses the final local and exact-SHA hosted evidence.

### Pending Todos

None outside the roadmap.

### Blockers/Concerns

- Independent [Phase 2 verification](phases/GB-02-dmg-cpu-bus-and-time/02-VERIFICATION.md) previously returned `gaps_found`; Plans 02-10 and 02-11 added focused corrections for startup/return phases, EI scheduling, and interrupt diagnostic chronology. Plan 02-12 resolved Windows manifest portability and distinct negative-control receipts. Plan 02-17 admitted the derived fixture set, and Plan 02-16 now passed runner, local/relocated inventory, and exact-SHA hosted checks. CPU-01 through CPU-05 remain pending until an independent verifier reassesses all seven gaps and requirement traceability.
- Plan 02-16's local core inventory ran 100/100 with no skips; the relocated installed inventory ran 105/105 with installed C/C++ consumers passing, and its fresh core-only inventory ran 100/100. Final PR head `8481d603b780af7889832ea3a8d3ad84d2439ba5` passed CI run 37564610248 and fixture-reproduction run 37564610420, including Windows and Linux ASan/UBSan. The fixed eligible corpus remains one CPU and two timer candidates.
- The original Mooneye ROMs use a PPU-dependent reporting path and remain captured as immutable pre-admission blobs. Plan 02-13's exact hosted run 37548730397 documented original-ROM byte differences caused by WLA-DX's invalid equal-priority/size `qsort` tie comparator. Plan 02-17 qualified a derivative using `wlalink -nS -d -S`; run 37561292904 matched all three 32,768-byte outputs exactly and the one-CPU/two-timer denominator was retained. Earlier [hosted evidence](phases/GB-02-dmg-cpu-bus-and-time/02-HOSTED-EVIDENCE.md) records Windows manifest rejection and required CI failures at PR head `a91d8e7`.
- Plan 02-14's [source audit and candidate probe](phases/GB-02-dmg-cpu-bus-and-time/02-14-SUMMARY.md) established the derivative callback/result path with zero observed PPU bus accesses. Plan 02-17's manifest admission passed source/rights/provenance and protocol review; strict offline digest verification reports 1 CPU and 2 timer candidates. CPU-05 remains pending until Plan 02-16 verifies runner receipts and independent Phase 2 evidence.
- [Draft PR #2](https://github.com/szTheory/gabbaboy/pull/2) publishes the Phase 2 implementation and gap reports for review, stacked on Phase 1 PR #1. Retarget and requalify after the foundation lands; no merge or release. Boundary triage found no open issues; PR #1 remains open.
- PR #1 remains open for owner review at exact hosted SHA `9f1df9bd0a70e50033f7d8cbcbff778e3bfd94e3`. Required contexts passed; both Linux/macOS preview packages passed exact digest/source/consumer verification and expire 2026-10-17T19:19Z. They are temporary artifacts, not releases.
- Native host support floors, signing, and live Playstead integration remain unverified for later release/adoption work.
- Plan 02-10 initially exposed a stale bus fixture assumption: checksum-selected startup flags made its `RET NC` case start with carry set. Quick task 261006-r6w corrected the generated ROM to a valid zero-checksum profile; its immediate 96-case report passed 92 with no skips. The newer 98-case local and 103-case Windows inventories are recorded above; CPU-01/02/04 remain pending independent Phase 2 verification.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 261006-r6w | Fix the bus_unsupported_stack fixture so RET NC tests its intended condition under checksum-selected DMG startup flags; validate the offline test inventory. | 2026-10-06 | 3231d21 | [261006-r6w-fix-the-bus-unsupported-stack-fixture-so](./quick/261006-r6w-fix-the-bus-unsupported-stack-fixture-so/) |

## Deferred Items

Future requirements and acceptance direction remain in [REQUIREMENTS.md](REQUIREMENTS.md#next-milestone-requirements--gbgbc-breadth) and [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md); none are counted in active coverage.

## Session Continuity

Last session: 2026-10-07T03:03:31.252Z
Stopped at: Completed GB-02 Plan 02-16 runner and exact-revision qualification; independent verification next
Resume file: .planning/.continue-here.md
Next command in fresh context: $gsd-execute-phase 2 --gaps-only
Continuation note: [.continue-here.md](.continue-here.md)
Completed workflow stage: Executed Phase GB-02 Plans 02-17 and 02-16. Plan 02-17 admitted the three derived candidates after hosted byte identity and provenance/protocol review. Plan 02-16 qualified callback/result-PC behavior, the fixed denominator, induced failure handling, local/relocated inventories, corpus limits, and final hosted gates at PR SHA 8481d603b780af7889832ea3a8d3ad84d2439ba5 (CI 37564610248; fixture reproduction 37564610420). CPU-01 through CPU-05 and Phase 2 remain pending independent verification.
Next stage: Run $gsd-execute-phase 2 --gaps-only for independent Phase GB-02 gap verification and requirement traceability.
Next implementation phase: Phase 3 — Visible Interactive DMG, paused until Phase 2 gaps and required checks are closed and the owner chooses to continue. Both auto-advance flags remain false.
