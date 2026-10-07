---
gsd_state_version: "1.0"
milestone: v0.1
current_phase: 02
current_phase_name: DMG CPU, Bus, and Time
status: Phase 2 complete; paused before Phase 3
stopped_at: Phase GB-02 execution, verification, security audit, and Nyquist validation complete; owner handoff before Phase 3
last_updated: "2026-10-07"
last_activity: 2026-10-07
last_activity_desc: Plan 02-18 closed the CPU-01/D-01 gap; independent verification passed 5/5, security closed 45/45 threats, and Nyquist validation resolved 8/8 gaps.
state_head: cf28e90270be24d9528bfa8a1e4055a2b8485989
progress:
  total_phases: 6
  completed_phases: 2
  total_plans: 22
  completed_plans: 22
milestone_name: limited DMG preview
---

# Project State

## Project Reference

See: [PROJECT.md](PROJECT.md) (updated 2026-10-03)

**Core value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Current focus:** Phase GB-02 is complete; Phase GB-03 is paused until the owner chooses to continue.

## Current Position

Phase: GB-02 (DMG CPU, Bus, and Time) — COMPLETE
Plan: 02-18 gap closure complete; no runnable Phase 2 plan remains
Status: Goal-backward verification passed; paused before Phase 3 by project workflow contract
Last activity: 2026-10-07 — Verification passed 5/5 roadmap truths; all 45 registered threats are closed; Nyquist is compliant with 8/8 gaps resolved.

Progress: [███░░░░░░░] 33% of milestone phases complete; Phases 1 and 2 passed verification.

## Performance Metrics

- Total unique plans executed: 22; Phase 2 completion is based on goal verification, not task count alone.
- Average duration / total execution time: 24 min / 527 min recorded across 22 plans.
- Per-phase metrics / recent trend: Phases 1 and 2 are complete. All 17 runnable Phase 2 plans have summaries; Plan 02-15 is superseded/non-runnable and remains historical.
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
- [Phase GB-02]: On 2026-10-07, independent verification passed CPU-01 through CPU-05 and all five roadmap truths at implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989`. Final local, installed-consumer, and exact hosted evidence is recorded in Phase 2 verification and validation; original upstream PPU-dependent results and physical hardware behavior remain outside the claim.

### Pending Todos

None outside the roadmap.

### Blockers/Concerns

- Phase 2 has no open verification or security blocker. All five requirements are complete at implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989`; see [verification](phases/GB-02-dmg-cpu-bus-and-time/02-VERIFICATION.md), [validation](phases/GB-02-dmg-cpu-bus-and-time/02-VALIDATION.md), and [security](phases/GB-02-dmg-cpu-bus-and-time/02-SECURITY.md).
- The admitted corpus is three derived headless reporting closures (one CPU, two timer). Original Mooneye reporting paths depend on PPU/LY behavior outside scope and remain excluded. No physical DMG-CPU-B observation occurred; no hardware qualification is claimed.
- Draft PR #2 remains on the Phase 2 branch, stacked on PR #1. Neither PR was merged or released as part of this phase handoff. Phase-boundary issue/PR triage found no open repository issues requiring Phase 2 work.
- Native host support floors beyond the verified CI matrix, signing, and live Playstead integration remain later release/adoption work.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 261006-r6w | Fix the bus_unsupported_stack fixture so RET NC tests its intended condition under checksum-selected DMG startup flags; validate the offline test inventory. | 2026-10-06 | 3231d21 | [261006-r6w-fix-the-bus-unsupported-stack-fixture-so](./quick/261006-r6w-fix-the-bus-unsupported-stack-fixture-so/) |

## Deferred Items

Future requirements and acceptance direction remain in [REQUIREMENTS.md](REQUIREMENTS.md#next-milestone-requirements--gbgbc-breadth) and [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md); none are counted in active coverage.

## Session Continuity

Last session: 2026-10-07
Stopped at: Phase GB-02 complete after gap-only execution, verification, security audit, and Nyquist validation; owner handoff before Phase 3
Resume file: .planning/.continue-here.md
Next command in fresh context: $gsd-discuss-phase 3
Continuation note: [.continue-here.md](.continue-here.md)
Completed workflow stage: **Phase GB-02 execution and closeout.** Plan 02-18 added independent legal base-opcode semantic assertions; the verifier passed 5/5 roadmap truths, the security audit closed 45/45 threats, and Nyquist validation resolved 8/8 gaps with no escalation. Local CTest passed 104/104, installed C/C++ consumers passed 109/109, and implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989` passed exact hosted CI and fixture reproduction. The code review is clean; no physical hardware test is claimed.
Next phase: **Phase 3 — Visible Interactive DMG**. It has not started. Keep workflow auto-advance and auto-chain false; wait for the owner to choose to continue with the exact command `$gsd-discuss-phase 3`.
