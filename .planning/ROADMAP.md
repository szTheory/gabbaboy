# Roadmap: GabbaBoy

## Overview

GabbaBoy is an original portable C17 core for Game Boy and Game Boy Color. v0.1 delivered a limited, evidence-bounded DMG preview with an installable core, timed CPU/bus diagnostics, an interactive optional SDL3 player, MBC1 battery continuation, scoped audio and a qualified v0.1.0 release. v0.2 Color & Cartridge Breadth proved one rights-clear game end to end on DMG-CPU-B and froze a DMG regression baseline. It then added MBC5/MBC2/MBC3 cartridges with a deterministic RTC and one CGB silicon revision (CGB-CPU-E) in CGB and DMG-compatibility modes, and shipped the model- and corpus-qualified v0.2.0 release. v0.3 Save States & Host Contract pays the v0.2 debt, adds exact native save states, player save slots and a host-process runner contract, and ships a qualified v0.3.0. Revisable later direction: [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md).

## Milestones

- ✅ **v0.1 Limited DMG Preview**: Phases 1–6 plus inserted 06.1 (shipped 2026-10-10; release `v0.1.0` published 2026-10-09)
- ✅ **v0.2 Color & Cartridge Breadth**: Phases 7–15 plus inserted 15.1 (shipped 2026-10-24; release `v0.2.0`; audit `tech_debt`, no blockers)
- 🚧 **v0.3 Save States & Host Contract**: Phases 16–19 (in progress; started 2026-10-24)

## Phases

**Phase Numbering:**
- Integer phases continue across milestones (directory prefix `GB-`); v0.3 runs Phases 16–19
- Decimal phases (for example 15.1) are urgent insertions (marked INSERTED)

<details>
<summary>✅ v0.1 Limited DMG Preview (Phases 1–6, 06.1): SHIPPED 2026-10-10</summary>

- [x] Phase 1: Portable Foundation and Original ROM Tracer (5/5 plans), completed 2026-10-03
- [x] Phase 2: DMG CPU, Bus, and Time (17/17 plans), completed 2026-10-07
- [x] Phase 3: Visible Interactive DMG (13/13 plans), completed 2026-10-09
- [x] Phase 4: MBC1 and Safe Battery Continuation (7/7 plans), completed 2026-10-08
- [x] Phase 5: DMG Audio and Stable Playback (7/7 plans), completed 2026-10-09
- [x] Phase 6: Qualified DMG Release and Consumer Handoff (7/7 plans), completed 2026-10-09
- [x] Phase 06.1: Address v0.1 tech debt (INSERTED) (8/8 plans), completed 2026-10-10

Full detail: [v0.1 roadmap archive](milestones/v0.1-ROADMAP.md), [requirements](milestones/v0.1-REQUIREMENTS.md), [audit](milestones/v0.1-MILESTONE-AUDIT.md), [phase records](milestones/v0.1-phases/).

</details>

<details>
<summary>✅ v0.2 Color & Cartridge Breadth (Phases 7–15, 15.1): SHIPPED 2026-10-24</summary>

- [x] Phase 7: DMG Game Acceptance and Regression Baseline (17/17 plans), completed 2026-10-11
- [x] Phase 8: Cartridge Seam, MBC5 and MBC2 (10/10 plans), completed 2026-10-11
- [x] Phase 9: MBC3, Deterministic RTC and Cartridge Persistence (18/18 plans), completed 2026-10-11
- [x] Phase 10: CGB Profile, Banking and Register Visibility (20/20 plans), completed 2026-10-12
- [x] Phase 11: CGB Colour Rendering and Player Colour (15/15 plans), completed 2026-10-13
- [x] Phase 12: CGB Double Speed (19/19 plans), completed 2026-10-14
- [x] Phase 13: CGB HDMA (12/12 plans), completed 2026-10-14
- [x] Phase 14: CGB-E Model Qualification and Corpus (13/13 plans), completed 2026-10-15
- [x] Phase 15: CGB Acceptance, Support Ledger and v0.2.0 Release (10/10 plans), completed 2026-10-20
- [x] Phase 15.1: Release Hardening and Milestone Debt Closure (INSERTED) (36/36 plans), completed 2026-10-24

Full detail: [v0.2 roadmap archive](milestones/v0.2-ROADMAP.md), [requirements](milestones/v0.2-REQUIREMENTS.md), [audit](milestones/v0.2-MILESTONE-AUDIT.md), [integration audit](milestones/v0.2-INTEGRATION-AUDIT.md), [quick tasks](milestones/v0.2-quick/). The phase records stay in [phases/](phases/), because CTest and the closeout verifiers read files there (see MILESTONES.md).

</details>

## v0.3 Save States & Host Contract

Milestone goal: players and embedders can save and restore exact machine state, the runner is safe to drive from a host process (raw `.sav`, SIGTERM save-and-exit, exit codes), the v0.2 debt is paid with v0.2.1 shipped, and `v0.3.0` is published as a qualified release. Scope evidence: [research/v0.3/SUMMARY.md](research/v0.3/SUMMARY.md); decisions D-102–D-106; requirements: [REQUIREMENTS.md](REQUIREMENTS.md).

Milestone-wide rules:
- **Budget (D-102).** Four phases and at most 38 plans in total (8 + 12 + 10 + 8). Each phase records a machine-readable `**Plan cap**`, enforced by the TUNE-05 plan-cap CTest; a 50% overrun triggers a rescope.
- **Round caps (D-102).** At most 2 review-fix rounds and 1 gap-closure round per phase. A finding still open at the cap becomes a recorded disposition that the milestone audit lists. An unresolved correctness or security finding in new code forces a rescope and is never turned into a seed.
- **Checks, not ceremonies (D-069, D-105).** Every success criterion below is an automated check with a negative control. Checkers live in `tests/scripts/`, take an immutable commit as input and are wired into CTest when created; the first executable plan of a feature exercises the compiled public-API path. verify-work needs no human checkpoint.
- **Closeout (D-103).** Phase verification stays bound to its boundary commit; the milestone audit runs the full suite at the exact final head so a `verified_closeout` is reachable. No per-phase verification-refresh PRs.
- **DMG baseline.** Every phase keeps the frozen DMG-CPU-B baseline (`dmg_baseline`) green, or records an approved, evidence-backed change.
- **Phase stop.** Each phase ends with evidence and one named next command; nothing auto-advances.
- **Scope limits.** Save states are same-version-only before 1.0 (D-106). INT-01b (RM-020), RTC footer interop (RM-021), BESS (RM-022) and libretro (RM-009) are out of scope.

- [x] **Phase 16: Tune-up and v0.2 Debt Closure** - Archive v0.2 phase records behind a lint, wire the Phase 8 verifiers, add the perf gate and CI/planning hygiene checks, and ship v0.2.1 (completed 2026-10-26)
- [ ] **Phase 17: Native Save State Core** - Public `gbb_state_size`/`gbb_save_state`/`gbb_load_state` with exact continuation, transactional bounded loads, machine-checked completeness and portable canonical bytes
- [ ] **Phase 18: Player Save Slots and Host Contract** - Numbered state slots in the SDL player and a `--rom`/`--save-dir` runner with atomic raw `.sav`, SIGTERM save-and-exit, an exit-code table and declared save-format ids
- [ ] **Phase 19: Qualified v0.3.0 Release** - Publish `v0.3.0` from its exact tag after a green exact-tag rehearsal, with a scoped support ledger and tag-bound receipts

## Phase Details

### Phase 16: Tune-up and v0.2 Debt Closure

**Goal**: v0.3 feature work starts from a clean, fast and honest baseline: the v0.2 phase records are archived, the Phase 8 verifiers run in CTest, performance and CI budgets are gated, planning hygiene is machine-checked, and `v0.2.1` is published.
**Depends on**: Nothing in v0.3 (builds on shipped `v0.2.0`)
**Requirements**: TUNE-01, TUNE-02, TUNE-03, TUNE-04, TUNE-05, TUNE-06
**Plan cap**: 8
**Success Criteria** (what must be TRUE):
  1. A lint CTest fails on a seeded `.planning/phases` path in a test and passes on the tree after the v0.2 phase records move to `milestones/v0.2-phases/`; the full suite passes after the move, and the Phase 8 contract verifiers run in CTest, each rejecting its seeded defect.
  2. A cumulative DMG perf gate on a named Linux hosted Release build compares an instruction-count proxy against the `v0.2.0` tag plus a realtime multiple with headroom, and fails on a seeded regression; an attribution receipt assigns the v0.2 slowdown to phase merges and closes LIM-PERF-REVIEW.
  3. CI budget checks fail on their negative controls: an over-budget per-test fixture; a PR ASan stall replay that is bounded (full replay in a split or scheduled lane) yet still rejects its control; a job timeout that cites no doubled run or exceeds the 60% ratio; and a `src/` or `tests/` change offered to the planning-only aggregator classifier.
  4. Planning hygiene CTests reject an over-cap phase fixture against the ROADMAP `**Plan cap**` lines, a duplicated LESSONS id (current duplicates renumbered) and an oversized STATE.md, and a docs check rejects the stale Playstead statements now corrected in README, `docs/native-integration.md` and PRECEDENT.
  5. A new versioned support ledger for post-`v0.2.0` source passes `--check-current` while a check rejects any change to the `v0.2.0` ledger bytes; the hosted rehearsal and trusted judge are green at the exact head; `v0.2.1` is published from release-please PR #75 and its release readback reconciles; PRs #78–92 are closed as superseded and the D-106 LIM dispositions are recorded.

**Plans**: 7/7 plans complete (cap 8; one slot kept for the single gap round)

Plans:
**Wave 1**
- [x] 16-01-PLAN.md — Archive v0.2 phase records behind the phase-path lint; CTest scaffolding (TUNE-01)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 16-02-PLAN.md — Cachegrind Ir perf gate vs v0.2.0, seeded-regression control, attribution receipt (TUNE-03)

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 16-03-PLAN.md — Per-test TIMEOUT ratchet, sharded and bounded ASan stall replay, nightly-asan lane (TUNE-04)

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 16-04-PLAN.md — Planning-only classifier behind required-native, timeout ledger, planning-label lint (TUNE-04)

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 16-05-PLAN.md — Phase 8 verifiers in CTest on a boundary tag; plan-cap, LESSONS, STATE and Playstead checks (TUNE-02, TUNE-05)

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 16-06-PLAN.md — v0.2.0 ledger freeze, version-agnostic release checks, review path, v0.3 disposition record (TUNE-06)

**Wave 7** *(blocked on Wave 6 completion)*
- [x] 16-07-PLAN.md — v0.2.1 release window, publication and readback, PR #78-92 closures, boundary commit (TUNE-06)

**Cross-cutting constraints:**
- git diff --quiet <plan base> HEAD -- src include holds (D-04).

### Phase 17: Native Save State Core

**Goal**: Embedders can save a running instance to bytes and restore it into any instance with the same ROM and mode, continuing exactly as if never interrupted, with refused loads leaving the instance untouched and completeness, bounds and portability machine-checked.
**Depends on**: Phase 16 (phase-path lint, CI budget, perf gate and plan-cap checks in place)
**Requirements**: STATE-01, STATE-02, STATE-03, STATE-04, STATE-05, STATE-06
**Plan cap**: 12
**Inherited obligations**: RM-026, RM-028, RM-029, RM-030 (D-112 and Phase 16 handoff; explicit entry work, not new state requirements)
**Canonical refs**: `.planning/phases/GB-17-native-save-state-core/17-CONTEXT.md`; `.planning/context/FUTURE-MILESTONES.md` RM-026..030; `.planning/context/DECISIONS.md` D-113
**Planning budget**: At most 11 primary plans, retaining one slot for the single gap round; all mandatory state and tooling work must fit or be explicitly rescoped before execution.
**Success Criteria** (what must be TRUE):
  1. Before any codec lands, a struct-inventory checker fails on an instance-struct member with no recorded serialize/reset treatment and an `nm`-based CTest fails on a seeded writable global in the core library; both pass on the tree.
  2. The installed C and C++ consumers call `gbb_state_size`, `gbb_save_state` and `gbb_load_state` through the compiled public API: the size is fixed per loaded ROM and mode, a check rejects a mutating or allocating save, typed errors are appended to the existing codes, and the API docs describe the calls.
  3. A fork matrix over the admitted corpus saves at seeded random points and at the targeted in-flight points (mid OAM DMA, mid HDMA, speed-switch stall, HALT/EI delay, APU sequencer, RTC sub-seconds, partly drawn frame), loads each state into a fresh deliberately corrupted instance, and matches every later frame, PCM sample, run result, battery image and final state byte; a coverage gate fails when an in-flight category never occurred at a save point, and every field-drop mutant build is caught.
  4. Every refused load (truncation, byte flips, wrong magic/version/profile/mode/ROM, out-of-range fields, 64-bit time fields above 2^62) leaves the instance byte-identical; a closure property test shows any accepted state run N steps still saves to an accepted state; and a state-load fuzz target runs in the hosted fuzz campaign.
  5. State bytes are explicitly little-endian and re-saving a just-loaded state reproduces identical bytes; pinned state digests match on Linux, macOS and Windows CI (an altered pin fails); a load carries cart RAM and the full RTC without reading the wall clock or applying catch-up, and a test shows an unchanged-battery load leaves the battery generation alone while a changed one bumps it exactly once, with the docs stating that loading replaces save RAM and the clock.

  6. A valid paired wall-clock trigger produces successful advisory evidence through the production measurement, verifier, reuse, aggregate, attach and release paths; a control proves it no longer requires ordinary timing approval. The cumulative Ir gate and separate realtime floor remain blocking and reject their controls. An immutable-base ratchet rejects an unapproved Ir-limit widening and a state-golden refresh without its compatibility/token disposition (RM-026, RM-029).
  7. The support-ledger generator renders the required historical performance disclosure without hand edits, and a control rejects its omission. Pre-tag replay invokes the production attach/manifest/publish-decision/retry code with captured, sanitized real API-shaped data, including non-git workspaces and check-run shapes; tampered, partial and stale evidence fails. A checked version-window input/regeneration/freeze rule protects reviewed content from release-please regeneration (RM-028).
  8. All WR-01..05 and IN-01..04 from the Phase 16 review are fixed with intended negative controls, including producer/workflow/event/source binding, historical tag identity, duplicate manifests, budget/cap ratchets and retry/check-app/nightly/perf/HDMA controls. The D-112 `--review-approval` and `--nightly-gate` paths run in CTest and the applicable production gates, rejecting their eight and six specified mutants respectively; point-in-time boundary checks remain immutable (RM-030). RM-027 final timeout citations remain a named Phase 19 entry blocker.

**Plans**: 0/11 complete (11 primary plans; one gap slot retained)

Plans:
**Wave 1**
- [x] 17-01-PLAN.md — Establish a production state API with pre-codec completeness checks and an installed continuation tracer.

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 17-02-PLAN.md — Expand the proven codec to strong identity and canonical validation across every mapper and hardware mode.

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 17-03-PLAN.md — Guarantee whole-instance refusal, bounded buffers and exact RAM/RTC/palette restoration with local observers.

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 17-04-PLAN.md — Make the 2^62 horizon closed across every public run, diagnostic/audio, event and peripheral path.

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 17-05-PLAN.md — Prove complete continuation with the admitted corpus, fresh poisoned destinations and field-specific omissions.

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 17-06-PLAN.md — Qualify canonical platform bytes and semantic hostile-state fuzzing in existing consumer/package/CI lanes.

**Wave 7** *(blocked on Wave 6 completion)*
- [x] 17-07-PLAN.md — Make paired timing advisory end to end while keeping deterministic Ir and realtime limits blocking.

**Wave 8** *(blocked on Wave 7 completion)*
- [x] 17-08-PLAN.md — Generate complete support disclosures and protect the future version-PR content window with managed inputs.

**Wave 9** *(blocked on Wave 8 completion)*
- [ ] 17-09-PLAN.md — Rehearse the actual attach/manifest/final-decision/retry lifecycle using bounded sanitized captured GitHub responses.

**Wave 10** *(blocked on Wave 9 completion)*
- [ ] 17-10-PLAN.md — Close every remaining Phase 16 WR/IN finding with intended controls on production gates.

**Wave 11** *(blocked on Wave 10 completion)*
- [ ] 17-11-PLAN.md — Enforce deterministic exception approval and nightly evidence in CTest and real release gates, then produce final-head evidence.

### Phase 18: Player Save Slots and Host Contract

**Goal**: Players can save and load numbered state slots in the SDL player without risking the running game, and a host process can drive the runner with a predictable save directory, atomic battery saves, a clean SIGTERM save-and-exit and documented exit codes and save formats.
**Depends on**: Phase 17 (public save-state API)
**Requirements**: PLAY-01, HOST-01, HOST-02, HOST-03
**Plan cap**: 10
**Success Criteria** (what must be TRUE):
  1. Automated player tests save and load numbered slots through the public API only, and a refused, mismatched or wrong-ROM slot leaves the running game byte-identical and shows a clear on-screen message.
  2. The runner's `--rom <path> --save-dir <dir>` mode writes battery saves as a raw `{saveDir}/{romBaseName}.sav` through an O_EXCL temp file in the save dir and a rename, flushing periodically; separate negative tests reject an unsanitised basename (separators or `..`), a symlinked target and an import outside the size the cartridge header implies, each with no partial mutation.
  3. A real-signal POSIX test sends SIGTERM and observes the runner finish the current frame, flush the save and exit 0 well within 2 s; a check rejects signal code seeded into the core (handling stays a `sig_atomic_t` flag in the adapter), each row of the documented exit-code table (clean quit, refusal, failure, crash) is exercised, and Windows is declared exempt.
  4. A machine-readable table declares GabbaBoy's save-format id and byte size for each cartridge kind (MBC3+RTC is 32,789 B), and a CTest checks it against the files the runner produces, failing on a seeded size or id mismatch.

**Plans**: TBD
**UI hint**: yes

### Phase 19: Qualified v0.3.0 Release

**Goal**: `v0.3.0` is published from its exact tag with save-state and host-contract claims scoped by model, corpus and platform, and every receipt bound to that tag; release hardening happens before the tag, not after.
**Depends on**: Phase 18
**Requirements**: REL-01
**Plan cap**: 8
**Success Criteria** (what must be TRUE):
  1. The exact-tag producer rehearsal ran green on the version PR before tagging, and a check rejects a release whose rehearsal receipt names a different revision or postdates the tag.
  2. A `v0.3.0` support ledger scopes the save-state and host-contract claims by model, corpus and platform and passes its ledger check, which rejects a seeded unscoped claim.
  3. Consumer, package, fuzz and perf-gate receipts are bound to the `v0.3.0` tag and the published asset readback reconciles; a receipt bound to any other revision is rejected.

**Plans**: TBD

## Progress

| Milestone | Phases | Plans | Status | Shipped |
|-----------|--------|-------|--------|---------|
| v0.1 Limited DMG Preview | 7 | 64/64 | Complete | 2026-10-10 |
| v0.2 Color & Cartridge Breadth | 10 | 170/170 | Complete | 2026-10-24 |
| v0.3 Save States & Host Contract | 4 | 7/18 planned (cap 38) | In progress | — |

**v0.3 execution order:** 16 → 17 → 18 → 19

| Phase | Plans Complete | Plan cap | Status | Completed |
|-------|----------------|----------|--------|-----------|
| 16. Tune-up and v0.2 Debt Closure | 7/7 | 8 | Planned | 2026-10-26 |
| 17. Native Save State Core | 8/11 | 12 | Planned | - |
| 18. Player Save Slots and Host Contract | 0/TBD | 10 | Not started | - |
| 19. Qualified v0.3.0 Release | 0/TBD | 8 | Not started | - |
