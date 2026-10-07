---
gsd_state_version: "1.0"
milestone: v0.1
current_phase: 02
current_phase_name: DMG CPU, Bus, and Time
status: executing
stopped_at: Completed Plan GB-02-17 candidate qualification and admission; Phase 2 remains executing
last_updated: "2026-10-07T02:37:49Z"
last_activity: 2026-10-07
last_activity_desc: Executed Plan 02-17; all three derived candidates matched the exact hosted Linux run, passed provenance/protocol gates, and were admitted with the one-CPU/two-timer denominator; CPU-05 remains pending Plan 02-16
state_head: 8cfd3040f1e0443b40708fd777f9664751483236
progress:
  total_phases: 6
  completed_phases: 1
  total_plans: 21
  completed_plans: 20
milestone_name: limited DMG preview
---

# Project State

## Project Reference

See: [PROJECT.md](PROJECT.md) (updated 2026-10-03)

**Core value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Current focus:** Phase GB-02 — DMG CPU, Bus, and Time

## Current Position

Phase: GB-02 (DMG CPU, Bus, and Time) — EXECUTING
Plan: 02-17 complete; 02-16 is next
Status: Executing Phase GB-02
Last activity: 2026-10-07 — Plan 02-17 admitted all three derived candidates after exact local/hosted byte identity, protocol and provenance checks. Plan 02-15 remains superseded with its halted summary preserved; Plan 02-16 is next. CPU-05 and Phase 2 remain pending independent runner and phase verification.

Progress: [██░░░░░░░░] 17% of milestone phases complete; Phase 1 has 5/5 plans and passed verification

## Performance Metrics

- Total unique plans executed: 20; plan execution does not imply phase qualification.
- Average duration / total execution time: 24 min / 478 min recorded for Phase 1 Plans 01–05 and Phase 2 Plans 01–14 plus Plan 02-17.
- Per-phase metrics / recent trend: Phase 1 complete; the original nine Phase 2 plans and gap-closure Plans 02-10 through 02-14 and 02-17 are executed. Plan 02-15 is superseded after its preserved halt; Plan 02-16 remains.
- Emulator correctness, speed, memory, and CI baselines: No general hardware/gameplay baseline. The latest local offline inventory ran 98 tests with 94 passes and no skips; Windows installed inventory ran 103 tests with 99 passes and no skips. Both retain the four documented unsupported-LY failures for the original ROMs. The exact derived candidate bytes now match local Darwin/arm64 and hosted Linux/x86_64; strict manifest verification passed. Plan 02-16 still owns runner and phase qualification.

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

### Pending Todos

None outside the roadmap.

### Blockers/Concerns

- Independent [Phase 2 verification](phases/GB-02-dmg-cpu-bus-and-time/02-VERIFICATION.md) returned `gaps_found`; Plans 02-10 and 02-11 now have focused corrections for startup/return phases, EI scheduling, and interrupt diagnostic chronology. Plan 02-12 resolved Windows manifest portability and distinct negative-control receipts at the tested revision. Plan 02-17 closed the candidate byte/provenance/protocol admission gate. Plan 02-16 still must verify runner behavior and exact-revision phase evidence. No CPU requirement is complete.
- The latest local offline CTest inventory ran 98/98: 94 passed and the four known Mooneye unsupported-LY cases failed, with no skips. The exact Windows installed inventory ran 103/103: 99 passed and the same four failures; all four Windows manifest/fixture controls passed and raw bytes matched the Git blob. Earlier at `c583e33`, Linux normal and ASan/UBSan each ran 94 cases with the same four failures and no sanitizer finding; the relocated install ran 99 with the same failures and five installed API checks passing. Prior-phase regression selection passed 24/24. Required corpus IDs remain fixed at three.
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

Last session: 2026-10-07T02:37:49Z
Stopped at: Completed Phase GB-02 Plan 02-17 candidate qualification and admission; Phase 2 remains executing
Resume file: .planning/.continue-here.md
Next command in fresh context: $gsd-execute-phase 2 --gaps-only
Continuation note: [.continue-here.md](.continue-here.md)
Completed workflow stage: Executed Phase GB-02 gap-closure Plan 02-17. The deterministic `wlalink -nS -d -S` recipe produced three repeatable local candidates whose complete bytes matched hosted Linux run 37561292904 at source revision `93647ac98b7f8437cc9640e3dec437bba4f11e9c`; source/rights/protocol gates passed and the staged candidates were admitted. The original manifest/ROM hashes and one-CPU/two-timer denominator are retained in the baseline record. Plan 02-15 is superseded/non-runnable and its halted summary remains unchanged. CPU-05 and Phase 2 remain incomplete because runner/inventory and independent phase verification are still pending.
Next stage: Execute Phase GB-02 Plan 02-16, “verify runner protocol, inventory, and final exact-revision evidence.” Run `$gsd-execute-phase 2 --gaps-only` to resume.
Next implementation phase: Phase 3 — Visible Interactive DMG, paused until Phase 2 gaps and required checks are closed and the owner chooses to continue. Both auto-advance flags remain false.
