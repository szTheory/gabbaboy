---
gsd_state_version: "1.0"
milestone: v0.1
current_phase: 2
current_phase_name: DMG CPU, Bus, and Time
status: gaps_found
stopped_at: Phase 2 gap-closure planning and independent plan verification finished; seven plans are ready to execute
last_updated: "2026-10-06T22:39:13Z"
last_activity: 2026-10-06
last_activity_desc: Seven Phase 2 gap-closure plans created and independently checked; original nine plans remain executed
state_head: 0d9700ab85b91724b9215c2028a9895599da7ec3
progress:
  total_phases: 6
  completed_phases: 1
  total_plans: 21
  completed_plans: 14
milestone_name: limited DMG preview
---

# Project State

## Project Reference

See: [PROJECT.md](PROJECT.md) (updated 2026-10-03)

**Core value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Current focus:** Phase GB-02 — DMG CPU, Bus, and Time

## Current Position

Phase: 2 (DMG CPU, Bus, and Time) — GAPS FOUND; GAP PLANS READY
Plan: 9 original plans executed of 16 total; 7 gap-closure plans pending
Status: Independent verification still blocks phase completion; gap plans passed plan review
Last activity: 2026-10-06 — Seven gap-closure plans created and independently checked; CPU-01..05 remain pending

Progress: [██░░░░░░░░] 17% of milestone phases complete; Phase 1 has 5/5 plans and passed verification

## Performance Metrics

- Total unique plans executed: 14; plan execution does not imply phase qualification.
- Average duration / total execution time: 27 min / 377 min recorded for Phase 1 Plans 01–05 and Phase 2 Plans 01–09.
- Per-phase metrics / recent trend: Phase 1 complete; the original nine Phase 2 plans are executed and seven gap-closure plans are pending.
- Emulator correctness, speed, memory, and CI baselines: No general hardware/gameplay baseline. Current Linux normal and ASan/UBSan suites each fail four of 94 tests; relocated-install qualification fails four of 99. Earlier corpus passes are superseded by the corrected unsupported-read guard.

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

### Pending Todos

None outside the roadmap.

### Blockers/Concerns

- Independent [Phase 2 verification](phases/GB-02-dmg-cpu-bus-and-time/02-VERIFICATION.md) returned `gaps_found`: startup F, RET/RETI stack phases, consecutive EI, interrupt diagnostic ordering, and corpus admission/completion. No CPU requirement is complete.
- At source `c583e33`, Linux normal and ASan/UBSan runs each executed 94 cases with four failures and no skips; no sanitizer finding was reported. The relocated install executed 99 cases with the same four failures; all five installed API checks passed. Prior-phase regression selection passed 24/24. Required corpus IDs remain fixed at three.
- Required Mooneye cases read PPU LY before assertions/result protocol, contrary to Phase 2's PPU exclusion. T-02-14/15 remain open. [Hosted evidence](phases/GB-02-dmg-cpu-bus-and-time/02-HOSTED-EVIDENCE.md) adds Windows manifest rejection and a DAA reproduction mismatch; required CI failed at PR head `a91d8e7`.
- [Draft PR #2](https://github.com/szTheory/gabbaboy/pull/2) publishes the Phase 2 implementation and gap reports for review, stacked on Phase 1 PR #1. Retarget and requalify after the foundation lands; no merge or release. Boundary triage found no open issues; PR #1 remains open.
- PR #1 remains open for owner review at exact hosted SHA `9f1df9bd0a70e50033f7d8cbcbff778e3bfd94e3`. Required contexts passed; both Linux/macOS preview packages passed exact digest/source/consumer verification and expire 2026-10-17T19:19Z. They are temporary artifacts, not releases.
- Native host support floors, signing, and live Playstead integration remain unverified for later release/adoption work.

## Deferred Items

Future requirements and acceptance direction remain in [REQUIREMENTS.md](REQUIREMENTS.md#next-milestone-requirements--gbgbc-breadth) and [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md); none are counted in active coverage.

## Session Continuity

Last session: 2026-10-06
Stopped at: Phase 2 gap-closure planning finished; seven reviewed gap plans are ready to execute
Resume file: .planning/.continue-here.md
Next command in fresh context: $gsd-execute-phase 2 --gaps-only
Continuation note: [.continue-here.md](.continue-here.md)
Completed workflow stage: Phase 2 gap-closure planning for seven verification blockers (plans 02-10 through 02-16), with independent plan verification passed. The original nine plans were executed; Phase 2 itself remains incomplete and Phase 1 is the last completed implementation phase.
Next stage: Phase 2 gap-closure execution. Run `$gsd-execute-phase 2 --gaps-only` to execute only the seven new closure plans.
Next implementation phase: Phase 3 — Visible Interactive DMG, paused until Phase 2 gaps and required checks are closed and the owner chooses to continue. Both auto-advance flags remain false.
