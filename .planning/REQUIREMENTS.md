# Requirements: GabbaBoy

**Defined:** 2026-10-24
**Core Value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Milestone:** v0.3 Save States & Host Contract. Scope evidence: [research/v0.3/SUMMARY.md](research/v0.3/SUMMARY.md). Decisions: D-102–D-106.

Each requirement names the automated check that proves it (D-105). Every check carries a negative control, and verify-work needs no human checkpoint (D-069).

## v0.3 Requirements

### Tune-up (v0.2 debt and delivery hygiene)

- [ ] **TUNE-01**: No test or CTest entry reads from `.planning/phases`.
  - A lint CTest fails on a seeded phase path.
  - The v0.2 phase records are archived to `milestones/v0.2-phases/`, and the full suite passes afterwards.
- [ ] **TUNE-02**: The Phase 8 contract verifiers are registered in CTest and pass. Each rejects a seeded defect.
- [ ] **TUNE-03**: A cumulative DMG performance gate on a named Linux hosted Release build:
  - an instruction-count proxy measured against the `v0.2.0` tag, plus a realtime multiple with headroom for later PPU work;
  - the gate fails on a seeded regression;
  - an attribution receipt assigns the v0.2 slowdown to phase merges, closing LIM-PERF-REVIEW.
- [ ] **TUNE-04**: CI stays inside its budget, enforced by checks:
  - a per-test time budget;
  - the ASan stall replay is split or moved to a scheduled lane, with a bounded PR replay that keeps a negative control;
  - every job's timeout cites the run it doubles, and jobs run at no more than 60% of their limit;
  - a planning-only lane behind one required aggregator check, whose classifier rejects `src/` or `tests/` changes as a negative control.
- [ ] **TUNE-05**: Planning hygiene is machine-checked:
  - a CTest compares each phase's plan count with its ROADMAP cap (negative control: an over-cap fixture);
  - a LESSONS id uniqueness test, with the current duplicates renumbered;
  - STATE.md stays under a size bound;
  - the stale Playstead statements in README, `docs/native-integration.md` and PRECEDENT are corrected.
- [ ] **TUNE-06**: The v0.2 release debt is closed:
  - a new versioned support ledger for post-`v0.2.0` source passes `--check-current`, without rewriting `v0.2.0`;
  - the hosted rehearsal and trusted judge are green at the exact head;
  - `v0.2.1` is published from release-please PR #75;
  - PRs #78–92 are closed as superseded;
  - the LIM dispositions from D-106 are recorded.

### Save states (STATE-01)

- [ ] **STATE-01**: The public API offers `gbb_state_size`, `gbb_save_state` and `gbb_load_state`.
  - The size is fixed per loaded ROM and mode.
  - Saving does not mutate state and does not allocate.
  - Errors are typed and appended to the existing codes.
  - API docs are updated, and the installed C and C++ consumers exercise the calls.
- [ ] **STATE-02**: A save state continues exactly. A fork matrix over the admitted corpus saves at seeded random points and at targeted ones:
  - targeted points: mid OAM DMA, mid HDMA, the speed-switch stall, HALT/EI delay, the APU sequencer, RTC sub-seconds and a partly drawn frame;
  - each state loads into a fresh, deliberately corrupted instance;
  - every later frame, PCM sample, run result, battery image and final state byte must match the uninterrupted run;
  - a coverage gate fails when any in-flight category was never present at a save point;
  - field-drop mutant builds must all be caught.
- [ ] **STATE-03**: Loading is transactional and bounded.
  - Every refused load leaves the instance byte-identical. Refusal cases: truncation, byte flips, wrong magic/version/profile/mode/ROM, out-of-range fields, and 64-bit time fields above 2^62.
  - A closure property test: any accepted state, run N steps, still saves to an accepted state.
  - A fuzz target for state loads is part of the hosted fuzz campaign.
- [ ] **STATE-04**: Completeness is machine-checked.
  - An inventory checker fails when an instance-struct member has no recorded serialize/reset treatment.
  - An `nm`-based CTest fails on any writable global in the core library.
  - Each check rejects a seeded fixture.
- [ ] **STATE-05**: State bytes are portable and canonical.
  - Encoding is explicitly little-endian.
  - Saving a just-loaded state reproduces identical bytes.
  - Pinned state digests match on Linux, macOS and Windows CI.
- [ ] **STATE-06**: Battery and RTC interplay is defined.
  - A state carries cartridge RAM and the full RTC.
  - Loading never reads the wall clock or applies catch-up.
  - The battery generation bumps once, and only when battery bytes change.
  - The docs state that loading replaces save RAM and the clock.
  - A test proves an unchanged-battery load leaves the generation alone, and that a changed one bumps it.

### Player

- [ ] **PLAY-01**: The SDL player saves and loads numbered state slots through the public API only.
  - A refused or mismatched slot leaves the running game untouched and shows a clear message.
  - This is covered by automated player tests, including a wrong-ROM slot control.

### Host contract (INT-01a)

- [ ] **HOST-01**: A runner mode `--rom <path> --save-dir <dir>` writes battery saves as a raw `{saveDir}/{romBaseName}.sav`.
  - The save is atomic: an O_EXCL temp file in the save dir, then a rename.
  - Saves flush periodically.
  - The ROM basename is sanitised, with no separators or `..`.
  - Symlinked targets are refused.
  - Import is bounded to the size the cartridge header implies, with no partial mutation on refusal.
  - Each rule has a negative test.
- [ ] **HOST-02**: On SIGTERM the runner finishes the current frame, flushes the save, and exits 0 well within 2 s.
  - The handling is a `sig_atomic_t` flag in the adapter only; the core has no signal code.
  - One documented exit-code table covers clean quit, refusal, failure and crash.
  - Real-signal tests run on POSIX; Windows is declared exempt.
- [ ] **HOST-03**: GabbaBoy declares its own save-format ids and byte sizes for each cartridge kind (MBC3+RTC is 32,789 B), documented in a machine-readable table. A CTest checks the table against the produced files.

### Release

- [ ] **REL-01**: `v0.3.0` is published from its exact tag.
  - The exact-tag producer rehearsal ran green on the version PR before tagging.
  - A v0.3.0 support ledger scopes the save-state and host-contract claims by model, corpus and platform.
  - Consumer, package, fuzz and perf-gate receipts are bound to the tag.

## Future Requirements

These are deferred and tracked in [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md):

- **INT-01b** (RM-020): a candidate Playstead AdapterPin plus the qualify / initial-run / continue continuation protocol. Triggered when Playstead schedules a second adapter.
- **RTC-INTEROP** (RM-021): mGBA/VBA-M 48-byte and BGB 44-byte RTC footer import/export, on demand.
- **BESS** (RM-022): best-effort interchange, export first.
- **REWIND** (RM-013): rewind and runahead in the player over STATE-01.
- **CGB-GAME** (RM-004): first CGB game-level evidence, in v0.4 Evidence Floor.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Cross-version save-state loading | Same-version only before 1.0 (D-106). Format v1 migration is a v1.0 obligation |
| libretro core | No demonstrated adopter. Playstead consumes process adapters (D-104, RM-009) |
| Playstead code changes or live Playstead qualification | Playstead has no scheduled second adapter. GabbaBoy does not claim live integration (D-104) |
| Signal handling in the core | Host concerns stay in adapters (engineering rules) |
| Signing/notarization, Wasm, new hardware profiles | Later horizons (RM-008, RM-010, RM-011) |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TUNE-01 | Phase 16 | Pending |
| TUNE-02 | Phase 16 | Pending |
| TUNE-03 | Phase 16 | Pending |
| TUNE-04 | Phase 16 | Pending |
| TUNE-05 | Phase 16 | Pending |
| TUNE-06 | Phase 16 | Pending |
| STATE-01 | Phase 17 | Pending |
| STATE-02 | Phase 17 | Pending |
| STATE-03 | Phase 17 | Pending |
| STATE-04 | Phase 17 | Pending |
| STATE-05 | Phase 17 | Pending |
| STATE-06 | Phase 17 | Pending |
| PLAY-01 | Phase 18 | Pending |
| HOST-01 | Phase 18 | Pending |
| HOST-02 | Phase 18 | Pending |
| HOST-03 | Phase 18 | Pending |
| REL-01 | Phase 19 | Pending |

**Coverage:**
- v0.3 requirements: 17 total
- Mapped to phases: 17 (Phase 16: 6, Phase 17: 6, Phase 18: 4, Phase 19: 1)
- Unmapped: 0

---
*Requirements defined: 2026-10-24*
*Last updated: 2026-10-24 after the v0.3 roadmap (Phases 16–19)*
