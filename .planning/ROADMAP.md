# Roadmap: GabbaBoy

## Overview

GabbaBoy is an original portable C17 core for Game Boy and Game Boy Color. v0.1 delivered a limited, evidence-bounded DMG preview: an installable core, timed CPU/bus diagnostics, an interactive optional SDL3 player, MBC1 battery continuation, scoped audio, and a qualified v0.1.0 release. v0.2 Color & Cartridge Breadth first proves one rights-clear game end to end on the existing DMG player and freezes a DMG regression baseline, then adds MBC5/MBC2/MBC3 cartridges with a deterministic RTC, then one CGB silicon revision (CGB-CPU-E) in CGB and DMG-compatibility modes, and ends with a model- and corpus-qualified v0.2.0 release. Evidence and ordering rationale: [research/v0.2/SUMMARY.md](research/v0.2/SUMMARY.md). Revisable later direction: [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md).

## Milestones

- ✅ **v0.1 Limited DMG Preview** — Phases 1–6 plus inserted 06.1 (shipped 2026-10-10; release `v0.1.0` published 2026-10-09)
- 🚧 **v0.2 Color & Cartridge Breadth** — Phases 7–15 (in progress; Phase 7 not started)
- 📋 **v0.3 States & Integration** (provisional) — save states (STATE-01) and a qualified Playstead adapter (INT-01)

## Phases

**Phase Numbering:**
- Integer phases (7, 8, 9): planned milestone work, continuing from v0.1 (directory prefix `GB-`)
- Decimal phases (7.1, 7.2): urgent insertions (marked INSERTED)

<details>
<summary>✅ v0.1 Limited DMG Preview (Phases 1–6, 06.1) — SHIPPED 2026-10-10</summary>

- [x] Phase 1: Portable Foundation and Original ROM Tracer (5/5 plans) — completed 2026-10-03
- [x] Phase 2: DMG CPU, Bus, and Time (17/17 plans) — completed 2026-10-07
- [x] Phase 3: Visible Interactive DMG (13/13 plans) — completed 2026-10-09
- [x] Phase 4: MBC1 and Safe Battery Continuation (7/7 plans) — completed 2026-10-08
- [x] Phase 5: DMG Audio and Stable Playback (7/7 plans) — completed 2026-10-09
- [x] Phase 6: Qualified DMG Release and Consumer Handoff (7/7 plans) — completed 2026-10-09
- [x] Phase 06.1: Address v0.1 tech debt (INSERTED) (8/8 plans) — completed 2026-10-10

Full detail: [v0.1 roadmap archive](milestones/v0.1-ROADMAP.md), [requirements](milestones/v0.1-REQUIREMENTS.md), [audit](milestones/v0.1-MILESTONE-AUDIT.md), [phase records](milestones/v0.1-phases/).

</details>

## v0.2 Color & Cartridge Breadth

Milestone goal: play supported CGB software and the common MBC2/MBC3/MBC5 cartridge set (with deterministic RTC) through the same bounded core and player, after first proving one rights-clear game end to end on the existing DMG player.

Milestone-wide rules:
- **DMG baseline gate.** From Phase 8 onward, every phase proves DMG-CPU-B output byte-identical to the Phase 7 frozen baseline (EVID-02), or records an approved, evidence-backed change.
- **Phase stop.** Each phase ends with evidence and one named next command; nothing auto-advances.
- **Claims.** Support statements name the model (DMG-CPU-B or CGB-CPU-E), corpus revision and executed denominator; test-ROM pass rates are never presented as game compatibility.
- **Ordering constraints.** Double speed (Phase 12) and HDMA (Phase 13) both change the run loop and must not run in parallel. Within Phase 8, MBC5 and MBC2 plans may run in parallel after the seam plan lands.

- [ ] **Phase 7: DMG Game Acceptance and Regression Baseline** - Admit one rights-clear DMG game, prove it end to end headless and in the player, and freeze the DMG baseline
- [ ] **Phase 8: Cartridge Seam, MBC5 and MBC2** - Move MBC1 behind a type-table mapper seam with no observable change, then add MBC5 and MBC2
- [ ] **Phase 9: MBC3, Deterministic RTC and Cartridge Persistence** - Add MBC3 with an emulated-time RTC, explicit host catch-up, versioned battery block, loader-matrix hardening and new-mapper continuation
- [ ] **Phase 10: CGB Profile, Banking and Register Visibility** - Select CGB-CPU-E, detect execution mode, bank VRAM/WRAM, and gate every model-specific behavior
- [ ] **Phase 11: CGB Colour Rendering and Player Colour** - Render CGB attributes and palettes through an RGB555 frame call, a DMG-compatibility palette, and `--model` in the player
- [ ] **Phase 12: CGB Double Speed** - KEY1/STOP speed switching with a modelled pause and a CPU-stall run-loop branch
- [ ] **Phase 13: CGB HDMA** - General-purpose and HBlank VRAM DMA with stall, cancel, readback and HALT interaction
- [ ] **Phase 14: CGB-E Model Qualification and Corpus** - CGB-E APU/I/O deltas and a headless CGB-E corpus with per-suite denominators
- [ ] **Phase 15: CGB Acceptance, Support Ledger and v0.2.0 Release** - CGB game-level evidence (or an explicit absence), current docs and consumers, and a qualified exact-tag release

## Phase Details

### Phase 7: DMG Game Acceptance and Regression Baseline

**Goal**: A maintainer can show one rights-clear DMG game starting, responding to input and progressing on the existing DMG core and player, and every later v0.2 phase has a frozen DMG baseline to prove itself against.
**Depends on**: Nothing in v0.2 (builds on shipped v0.1)
**Requirements**: GAME-01, GAME-02, GAME-03, EVID-01, EVID-02
**Success Criteria** (what must be TRUE):
  1. Admitting the game (Libbet and the Magic Floor primary) succeeds only with a manifest that records source commit, licence text, per-asset provenance, release digest and reproducibility statement; an admission attempt with any unrecorded embedded-asset right fails.
  2. A headless acceptance run with a scripted, emulated-time input file reaches the guest-memory progress predicate with recorded frame digests and a non-silent PCM digest on Linux, macOS and Windows CI, while the same run without input does not reach the predicate.
  3. The runner captures an `LD B,B` frame as a canonical RGB digest (image written only on failure), replays scripted joypad input, and honours `model_pass`/`model_fail`/`target_revision`/`unsupported-model` manifest fields, with no new dependency.
  4. The packaged SDL3 player launches the admitted game and passes an automated input/progress/audio smoke in CI.
  5. A frozen DMG baseline (executed CTest inventory, Mooneye closures, acceptance frame/audio digests, benchmark baseline) is recorded and a single check reports byte-identity against it.

**Rights gates**: G5 (Libbet asset-licence completeness and release recipe checklist) blocks admission; G2 (GBDK 2.96a runtime terms) blocks the Tobu Tobu Girl fallback.
**Research**: Light.
**Plans**: 2/17 plans executed

Plans:
**Wave 1**
- [x] 07-01-PLAN.md — Libbet admission: vendored digest-pinned ROM, G5 manifest, fail-closed verifier, install-tree exclusion check, draft PR with Windows spike

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 07-02-PLAN.md — Shared acceptance library: gbinput 1 parser, deadline stepper and replay driver, predicate table; library replay tracer and unit tests
- [ ] 07-03-PLAN.md — D-19(i) pre-freeze investigation: mixer saturation (fix only a demonstrated defect; core-mutant anchor unchanged)
- [ ] 07-04-PLAN.md — Opt-in libbet-repro workflow and pinned rebuild recipe with automated registry provenance checks

**Wave 3** *(blocked on Wave 2 completion)*
- [ ] 07-05-PLAN.md — Runner tracer: case-file parser, --acceptance CLI, heap ROM loader, acceptance_libbet; Mooneye heap buffers
- [ ] 07-17-PLAN.md — D-19(ii) pre-freeze investigation: early Start taps explained from the pinned source (fix only a demonstrated defect; core-mutant anchor unchanged)

**Wave 4** *(blocked on Wave 3 completion)*
- [ ] 07-06-PLAN.md — Case-file hardening: runner-level negative files and the case/path boundary matrix

**Wave 5** *(blocked on Wave 4 completion)*
- [ ] 07-07-PLAN.md — Canonical RGB/PCM digests, checkpoints, PPM on failure, --observe, independent digest vectors

**Wave 6** *(blocked on Wave 5 completion)*
- [ ] 07-08-PLAN.md — Applicability, strict xfail, exit-4 exclusions and suite receipts with declared exclusion counts

**Wave 7** *(blocked on Wave 6 completion)*
- [ ] 07-09-PLAN.md — LD B,B frame capture: frame-digest@ldbb/@t paths, regression-class LD B,B observations, mismatch PPM and not-ready controls

**Wave 8** *(blocked on Wave 7 completion)*
- [ ] 07-10-PLAN.md — Controls: no input, SELECT, drop START and JOYP core mutant

**Wave 9** *(blocked on Wave 8 completion)*
- [ ] 07-11-PLAN.md — SGB tolerance, bounded stall diagnosis, first exact-head CI cross-OS identity and PCM calibration

**Wave 10** *(blocked on Wave 9 completion)*
- [ ] 07-12-PLAN.md — Packaged SDL3 player --input-script smoke with headless PCM equality and package ROM scan
- [ ] 07-13-PLAN.md — Baseline comparator with a negative control for every failure category

**Wave 11** *(blocked on Wave 10 completion)*
- [ ] 07-14-PLAN.md — Player controls, registered D-38 surface check, exact-head macos-player-package evidence

**Wave 12** *(blocked on Wave 11 completion)*
- [ ] 07-15-PLAN.md — Inspected baseline freeze in a baseline: commit, cross-OS identity and JUnit inventory steps

**Wave 13** *(blocked on Wave 12 completion)*
- [ ] 07-16-PLAN.md — Acceptance docs, support-ledger entry, recorded refinements and lessons, PR ready, triage and handoff

### Phase 8: Cartridge Seam, MBC5 and MBC2

**Goal**: Cartridge behavior lives behind one type-table mapper seam with no observable DMG change, and callers can run MBC5 and MBC2 cartridges.
**Depends on**: Phase 7 (DMG baseline)
**Requirements**: CART-01, CART-02, CART-03
**Success Criteria** (what must be TRUE):
  1. With MBC1 moved behind the type-table seam (kind, RAM, battery, RTC, rumble), the MBC1 suite, battery continuation fixture and Phase 7 DMG baseline are byte-identical.
  2. MBC5 cartridges (`$19-$1E`) run with 9-bit ROM banking including bank 0 in the switchable window, ROM up to 8 MiB and RAM up to 128 KiB; the rumble bit is masked from RAM banking and readable by the host; the pinned Mooneye `mbc5` derivatives pass 8/8.
  3. MBC2 cartridges (`$05/$06`) run with address-bit-8 register decode and 512x4-bit RAM echoed through `A000-BFFF` with upper nibbles reading as 1s, exporting a 512-byte battery image; the pinned Mooneye `mbc2` derivatives pass 7/7.
  4. Original fixtures for MBC5 bank `$1FF`, bank 0 in the upper window and rumble masking pass, and the 8 MiB `rom_64Mb` derivative is kept out of install and package artifacts.

**Research**: Standard (confirm the 8 MiB loader bound and repository size policy for `rom_64Mb`).
**Plans**: TBD (seam plan first; MBC5 and MBC2 plans may then run in parallel)

### Phase 9: MBC3, Deterministic RTC and Cartridge Persistence

**Goal**: Callers can run MBC3 cartridges whose RTC advances only from emulated time, hosts apply wall-clock catch-up explicitly, and battery data for every new mapper survives fresh-process continuation.
**Depends on**: Phase 8
**Requirements**: CART-04, CART-05, CART-06, RTC-01, RTC-02, RTC-03
**Success Criteria** (what must be TRUE):
  1. MBC3 cartridges (`$0F-$13`) run with 7-bit ROM banking and RAM banks `00-03`; MBC30 and other unsupported variants are rejected with an explicit error; MagenTests out-of-bounds SRAM cases pass for MBC1/MBC3/MBC5.
  2. rtc3test passes headless with scripted input: the RTC advances at 2^23 half-dots per second independent of CPU speed, with `00`-then-`01` latch, halt, sticky day carry and 9-bit day counter; a CI check proves `src/core` uses no host clock.
  3. `gbb_rtc_catch_up` applies elapsed seconds between runs with tested negative, overflow and rollback policy, and importing a battery image never advances the RTC.
  4. RTC state round-trips through a versioned little-endian core battery block; the player envelope records save time and applies catch-up on reopen; the original RTC continuation fixture passes across fresh processes, MBC2/MBC3/MBC5 battery data continues without corrupting a good save, and every v0.1 save file still loads unchanged.
  5. The loader rejects every contradictory type/ROM-size/RAM-size/file-length combination for MBC2/MBC3/MBC5 (exact, one-under, one-over) with no partial mutation, and fuzz targets cover the raised 8 MiB bound.

**Rights gates**: G1 (mgblib font) gates Mealybug `mbc3_rtc` as required evidence; G3 (gbclock plugin licences) keeps gbclock out — rtc3test and original fixtures are primary.
**Research**: DEEP (write-while-running, rollover, sub-second prescaler reset on seconds write, day carry, halt).
**Plans**: TBD

### Phase 10: CGB Profile, Banking and Register Visibility

**Goal**: A caller can select the CGB-CPU-E profile and run CGB software with correct execution mode, post-boot state, VRAM/WRAM banking and model-gated register visibility, without changing DMG output.
**Depends on**: Phase 8 (cartridge seam); sequenced after Phase 9 so mapper work lands before CGB array reshaping
**Requirements**: CGB-01, CGB-02, CGB-03
**Success Criteria** (what must be TRUE):
  1. A caller selects `GBB_PROFILE_CGB_CPU_E`, probes a ROM and queries model and execution mode (CGB or DMG-compatibility from header `$143` bit 7); CGB-only ROMs load on the DMG profile with an informational flag; mode-specific post-boot state carries per-field provenance and the DMG row stays byte-identical.
  2. Every DMG-specific behavior is tagged by model in code and docs, and the register visibility matrix (DMG, CGB, CGB in DMG-compatibility mode) has a passing test per cell; KEY0 is locked after boot.
  3. CGB software banks VRAM (2x8 KiB) and WRAM (8x4 KiB) with echo RAM following the selected WRAM bank and model-correct OAM DMA source behavior, verified by original fixtures.
  4. The half-dot timeline-unit decision for double speed is recorded in DECISIONS.md, and a banking-indirection benchmark shows the DMG cost against the Phase 7 baseline.

**Research**: Moderate (CGB-E post-boot DIV/LY/STAT; compat-mode register readability per Mooneye `unused_hwio-C` and AGE).
**Plans**: TBD

### Phase 11: CGB Colour Rendering and Player Colour

**Goal**: CGB software renders in colour through a new RGB555 frame call, DMG software on the CGB profile uses an original documented compatibility palette, and the player presents either model.
**Depends on**: Phase 10
**Requirements**: CGB-04, CGB-05, CGB-09
**Success Criteria** (what must be TRUE):
  1. CGB software renders with tile attributes, BG/OBJ colour palette RAM (auto-increment, mode-3 lockout) and CGB priority rules through `gbb_copy_frame_rgb555`, checked by an exhaustive priority truth table and AGE/MagenTests CGB PPU ROMs plus original attribute-bit fixtures; `gbb_copy_frame` stays byte-identical for DMG.
  2. DMG software on the CGB profile renders through a fixed, original, documented compatibility palette that a host can override; no boot-ROM palette table ships.
  3. The SDL3 player runs software with `--model auto|dmg|cgb` and colour presentation and passes an automated CGB smoke in CI.

**Rights gates**: G1 (mgblib font) gates vendoring cgb-acid2/dmg-acid2 into required CI (digest-pinned optional local runs otherwise); G4 excludes title-hash compatibility palettes.
**Research**: DEEP (LCDC bit 0 in CGB mode, OPRI timing, CGB mode-3 length, blocked-write palette auto-increment).
**Plans**: TBD
**UI hint**: yes

### Phase 12: CGB Double Speed

**Goal**: CGB software can switch speed through KEY1 and STOP, with CPU-side devices running at twice the rate while PPU and APU timing are unchanged.
**Depends on**: Phase 11
**Requirements**: CGB-06
**Success Criteria** (what must be TRUE):
  1. After KEY1 arm and STOP on the CGB profile, CPU, timer, serial and OAM DMA run at twice the rate while PPU and APU timing are unchanged, shown by an original DIV/TIMA/serial-per-scanline ROM and the applicable AGE speed-switch and double-speed STAT ROMs.
  2. The switch pause is modelled as explicit stall state with a sourced named duration; devices keep advancing and the switch never enters the DMG STOP sleep path, in both the usual and hostile (IE set, pending IRQ, held button) pre-switch sequences.
  3. Partitioned runs (run N, stop, run M) equal one run of N+M across a speed switch and stall, and unresearched pause behaviors are recorded as named expected failures.

**Research**: DEEP (interrupts, DIV and PPU during the pause; applicable test list).
**Plans**: TBD

### Phase 13: CGB HDMA

**Goal**: CGB software can use general-purpose and HBlank VRAM DMA with hardware-shaped CPU stall, cancel and readback, bounded per run.
**Depends on**: Phase 12 (must not run in parallel with it)
**Requirements**: CGB-07
**Success Criteria** (what must be TRUE):
  1. General-purpose DMA stalls the CPU for the transfer and HBlank DMA moves one block per visible-line mode-0 entry, both writing to the current VRAM bank, verified by SameSuite `dma/*` ROMs and original fixtures.
  2. Cancelling via HDMA5 bit 7, HDMA5 readback, HALT during a transfer, LCD-off and invalid sources follow stated behaviors with tests; unresearched cases are recorded as unspecified rather than invented.
  3. Every transfer is bounded (at most 128 blocks) and partitioned runs stay equivalent across transfers; MagenTests `hblank_vram_dma` passes with its oracle class recorded, and Mealybug `hdma_*-C` results are reported as informational CGB-C evidence outside the CGB-E denominator.

**Research**: DEEP (LCD-off, mode-3 GDMA, overflow state, HALT, cross-bank source, same-half-dot ordering).
**Plans**: TBD

### Phase 14: CGB-E Model Qualification and Corpus

**Goal**: CGB-E specific APU and I/O differences are implemented under declared per-test applicability, and a headless CGB-E corpus reports honest denominators.
**Depends on**: Phase 13
**Requirements**: CGB-08, CGB-10
**Success Criteria** (what must be TRUE):
  1. PCM12/PCM34, `FF72-FF75` masked registers and the IR port stub behave as specified on CGB-E, with per-test model applicability and named expected failures (for example `channel_4_freq_change`) in the manifests.
  2. A headless CGB-E corpus run (AGE, SameSuite, MagenTests, CGB-applicable Mooneye subset) reports per-suite passed/executed denominators with each failure and exclusion reason, and Mealybug `m3_*` cases are recorded as `unsupported-model`.
  3. The DMG baseline remains byte-identical after the CGB-E deltas land.

**Rights gates**: G1 (mgblib font) gates cgb-acid2/dmg-acid2 and Mealybug bytes in the required corpus.
**Research**: DEEP (CGB-E APU rules, wave RAM, enumeration of Mooneye CGB pass lists from the pinned tree).
**Plans**: TBD

### Phase 15: CGB Acceptance, Support Ledger and v0.2.0 Release

**Goal**: Adopters get a qualified v0.2.0 release whose ledger, docs and consumers accurately state what DMG-CPU-B and CGB-CPU-E support has been proven.
**Depends on**: Phase 14
**Requirements**: CGB-11, SHIP-09, SHIP-10, SHIP-11
**Success Criteria** (what must be TRUE):
  1. One rights-clear CGB game passes a game-level acceptance run in the GAME-02 style (scripted input, progress predicate, negative control, frame/PCM digests), or the ledger explicitly states that no CGB game-level evidence exists.
  2. The v0.2 support ledger names DMG-CPU-B and CGB-CPU-E, the mapper matrix, evidence classes, corpus revisions, denominators, failures, exclusions and known issues, and contains no unqualified compatibility claim.
  3. Installed C and C++ consumers exercise profile selection, ROM probe, RGB555 frames and RTC catch-up, and API, cartridge/save, integration and third-party-notice docs match the shipped behavior.
  4. An exact-tag v0.2.0 release publishes with refreshed fuzzing and performance baselines, including a measured DMG performance comparison against v0.1.

**Rights gates**: Per-candidate rights audit for the CGB game (Rebound, Rex Runner, GBHack, Aevilia); none is admitted without the GAME-01 manifest checklist.
**Research**: Light.
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1–6, 06.1 | v0.1 | 64/64 | Complete | 2026-10-10 |
| 7. DMG Game Acceptance and Regression Baseline | v0.2 | 2/17 | In Progress | - |
| 8. Cartridge Seam, MBC5 and MBC2 | v0.2 | 0/TBD | Not started | - |
| 9. MBC3, Deterministic RTC and Cartridge Persistence | v0.2 | 0/TBD | Not started | - |
| 10. CGB Profile, Banking and Register Visibility | v0.2 | 0/TBD | Not started | - |
| 11. CGB Colour Rendering and Player Colour | v0.2 | 0/TBD | Not started | - |
| 12. CGB Double Speed | v0.2 | 0/TBD | Not started | - |
| 13. CGB HDMA | v0.2 | 0/TBD | Not started | - |
| 14. CGB-E Model Qualification and Corpus | v0.2 | 0/TBD | Not started | - |
| 15. CGB Acceptance, Support Ledger and v0.2.0 Release | v0.2 | 0/TBD | Not started | - |
