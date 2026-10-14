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
- **Ordering constraints.** Double speed (Phase 12) and HDMA (Phase 13) both change the run loop and must not run in parallel. Within Phase 8, the seam plan lands first, then the MBC2 plan and then the MBC5 plan run in sequence (they share the core, public header and test-inventory files, and the MBC5 cross-mapper control needs a real MBC2; 08-CONTEXT D-08 as amended at planning).

- [x] **Phase 7: DMG Game Acceptance and Regression Baseline** - Admit one rights-clear DMG game, prove it end to end headless and in the player, and freeze the DMG baseline (completed 2026-10-11)
- [x] **Phase 8: Cartridge Seam, MBC5 and MBC2** - Move MBC1 behind a type-table mapper seam with no observable change, then add MBC5 and MBC2 (completed 2026-10-11)
- [x] **Phase 9: MBC3, Deterministic RTC and Cartridge Persistence** - Add MBC3 with an emulated-time RTC, explicit host catch-up, versioned battery block, loader-matrix hardening and new-mapper continuation (completed 2026-10-11)
- [x] **Phase 10: CGB Profile, Banking and Register Visibility** - Select CGB-CPU-E, detect execution mode, bank VRAM/WRAM, and gate every model-specific behavior (completed 2026-10-12)
- [x] **Phase 11: CGB Colour Rendering and Player Colour** - Render CGB attributes and palettes through an RGB555 frame call, a DMG-compatibility palette, and `--model` in the player (completed 2026-10-13)
- [x] **Phase 12: CGB Double Speed** - KEY1/STOP speed switching with a modelled pause and a CPU-stall run-loop branch (completed 2026-10-14)
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
**Plans**: 17/17 plans complete

Plans:
**Wave 1**
- [x] 07-01-PLAN.md — Libbet admission: vendored digest-pinned ROM, G5 manifest, fail-closed verifier, install-tree exclusion check, draft PR with Windows spike

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 07-02-PLAN.md — Shared acceptance library: gbinput 1 parser, deadline stepper and replay driver, predicate table; library replay tracer and unit tests
- [x] 07-03-PLAN.md — D-19(i) pre-freeze investigation: mixer saturation (fix only a demonstrated defect; core-mutant anchor unchanged)
- [x] 07-04-PLAN.md — Opt-in libbet-repro workflow and pinned rebuild recipe with automated registry provenance checks

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 07-05-PLAN.md — Runner tracer: case-file parser, --acceptance CLI, heap ROM loader, acceptance_libbet; Mooneye heap buffers
- [x] 07-17-PLAN.md — D-19(ii) pre-freeze investigation: early Start taps explained from the pinned source (fix only a demonstrated defect; core-mutant anchor unchanged)

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 07-06-PLAN.md — Case-file hardening: runner-level negative files and the case/path boundary matrix

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 07-07-PLAN.md — Canonical RGB/PCM digests, checkpoints, PPM on failure, --observe, independent digest vectors

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 07-08-PLAN.md — Applicability, strict xfail, exit-4 exclusions and suite receipts with declared exclusion counts

**Wave 7** *(blocked on Wave 6 completion)*
- [x] 07-09-PLAN.md — LD B,B frame capture: frame-digest@ldbb/@t paths, regression-class LD B,B observations, mismatch PPM and not-ready controls

**Wave 8** *(blocked on Wave 7 completion)*
- [x] 07-10-PLAN.md — Controls: no input, SELECT, drop START and JOYP core mutant

**Wave 9** *(blocked on Wave 8 completion)*
- [x] 07-11-PLAN.md — SGB tolerance, bounded stall diagnosis, first exact-head CI cross-OS identity and PCM calibration

**Wave 10** *(blocked on Wave 9 completion)*
- [x] 07-12-PLAN.md — Packaged SDL3 player --input-script smoke with headless PCM equality and package ROM scan
- [x] 07-13-PLAN.md — Baseline comparator with a negative control for every failure category

**Wave 11** *(blocked on Wave 10 completion)*
- [x] 07-14-PLAN.md — Player controls, registered D-38 surface check, exact-head macos-player-package evidence

**Wave 12** *(blocked on Wave 11 completion)*
- [x] 07-15-PLAN.md — Inspected baseline freeze in a baseline: commit, cross-OS identity and JUnit inventory steps

**Wave 13** *(blocked on Wave 12 completion)*
- [x] 07-16-PLAN.md — Acceptance docs, support-ledger entry, recorded refinements and lessons, PR ready, triage and handoff

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
**Plans**: 10/10 plans complete (seam plan first; MBC2 then MBC5 run in sequence because they share the core, header and test-inventory files)

Plans:
**Wave 1**
- [x] 08-01-PLAN.md — Cartridge mapper seam in gabbaboy.c with old-versus-new differential, frozen digest and draft PR

**Wave 2**
- [x] 08-02-PLAN.md — MBC2: bit-8 decode, 512 canonical nibbles, normalising battery import

**Wave 3**
- [x] 08-03-PLAN.md — MBC5: 9-bit banking, 8 MiB type-aware ceiling, rumble API, cross-mapper control

**Wave 4** *(parallel)*
- [x] 08-04-PLAN.md — Player runs MBC2/MBC5 battery carts without persistence and says so
- [x] 08-05-PLAN.md — Mooneye mbc2/mbc5 derivatives admitted and executed: pinned rebuild, sibling manifest, multi-suite runner, 7/7 and 8/8

**Wave 5**
- [x] 08-06-PLAN.md — Sibling verifier, 22 mooneye_mbc CTests, PC agreement and fail-closed controls, SOURCES/ELIGIBILITY and notices

**Wave 6**
- [x] 08-07-PLAN.md — Install/package scans, ninth-bit mutant, hosted Linux rebuild leg, exact-head CI

**Wave 7**
- [x] 08-08-PLAN.md — Original MBC5 banking fixture: bank $1FF, bank 0 upper window, rumble masking

**Wave 8**
- [x] 08-09-PLAN.md — Docs, evidence ledger, support entry, decisions, lessons, future direction

**Wave 9**
- [x] 08-10-PLAN.md — Phase gates, exact-head evidence, PR ready (left open), handoff to /gsd-verify-work 8

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
**Plans**: 18/18 plans complete

Plans:
**Wave 1**
- [x] 09-01-PLAN.md — Tracer: MBC3 mapper rows, decode and MBC30 variant with the synthetic-image mbc3_* matrix
- [x] 09-02-PLAN.md — MagenTests admission (rights, digests, provenance, RGBDS 0.6.1 CI pin) and the shared manifest digest check
- [x] 09-03-PLAN.md — Fuzz synthesised-length mode on the 8 MiB bound with ten pinned length-class seeds
- [x] 09-04-PLAN.md — v0.1 save corpus generated once by the v0.1.2 writer, with an offline check
- [x] 09-05-PLAN.md — Original MBC3+RTC continuation guest with a byte-identical rebuild
- [x] 09-06-PLAN.md — Original MBC2 continuation guest with a byte-identical rebuild

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 09-07-PLAN.md — MagenTests screen oracle for MBC1/MBC3/MBC5 with negative control and install exclusion
- [x] 09-08-PLAN.md — rtc3test admission and legacy-RGBDS reproduction legs for rtc3test and MagenTests

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 09-09-PLAN.md — Lazy emulated-time RTC, original differential/metamorphic/edge tests, no-host-clock CI proof, draft PR and exact-head CI read
- [x] 09-10-PLAN.md — Original MBC5 continuation guest and fixture-repro pin checks and rebuilds for all three guests

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 09-11-PLAN.md — Battery image with the 21-byte RTC block, gbb_rtc_catch_up and GBB_NO_RTC, pure host catch-up policy table

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 09-12-PLAN.md — rtc3test headless oracle with exact transcripts checked against rtc3test's stated values; cross-OS core continuation of the original guests
- [x] 09-13-PLAN.md — Player envelope v2, core-derived classification (WR-02), clock adapter, v0.1 corpus tests
- [x] 09-14-PLAN.md — Installed C and C++ consumers exercise the RTC API; integration-guide RTC section

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 09-15-PLAN.md — Loader contradiction matrix with independent oracle; five RTC mutation controls
- [x] 09-16-PLAN.md — Catch-up on reopen, --clock-unix scope, fresh-process MBC2/MBC3+RTC/MBC5 continuation

**Wave 7** *(blocked on Wave 6 completion)*
- [x] 09-17-PLAN.md — MBC3/RTC evidence ledger, cartridge-and-saves contract, capability text

**Wave 8** *(blocked on Wave 7 completion)*
- [x] 09-18-PLAN.md — Phase gates, evidence head, PR ready (left open), decisions/lessons, research index and handoff to /gsd-verify-work 9

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
**Plans**: 20/20 plans complete

Plans (serial waves: every plan edits `tests/expected-tests.txt` and `tests/CMakeLists.txt`, most also `src/core/gabbaboy.c`):
- [x] 10-01-PLAN.md — Wave 1: model-gate scanner (R1-R5, --release, self-test mutants) and docs/model-gates.md skeleton
- [x] 10-02-PLAN.md — Wave 2: tag every core function and model-differing branch (comment-only), gate table, real-file controls
- [x] 10-03-PLAN.md — Wave 3: runner model<->profile mapping, --profile, removed unsupported-profile rejection, DMG byte-identity controls
- [x] 10-04-PLAN.md — Wave 4: DMG post-boot pin test, then the post_boot[] provenance table refactor (own commit)
- [x] 10-05-PLAN.md — Wave 5: appended profile/info API, gbb_probe_rom, gbb_get_info, PGB rejection, parity tests
- [x] 10-06-PLAN.md — Wave 6: CGB and compat post-boot columns, create flip, copy_frame gate, DIV sweep, channel-1 silence
- [x] 10-07-PLAN.md — Wave 7: docs/cgb-profile.md post-boot mirror and test_cgb_tables provenance checks
- [x] 10-08-PLAN.md — Wave 8: banked VRAM/WRAM arrays and helpers with the DMG flat-reference metamorphic test
- [x] 10-09-PLAN.md — Wave 9: io_visibility table and CGB decode, deferred-access latch, IE gate, VBK/SVBK selection, behaviour cases
- [x] 10-10-PLAN.md — Wave 10: per-cell visibility matrix (DMG/CGB/compat) with flip, cross-column and sweep controls; io doc mirror and table check
- [x] 10-11-PLAN.md — Wave 11: KEY0 lock behavioural probe and STOP with KEY1 armed fail-closed
- [x] 10-12-PLAN.md — Wave 12: CGB OAM DMA source map, echo/bank public tests, D-17 pin, core-mutant controls
- [x] 10-13-PLAN.md — Wave 13: original fixtures/cgb-banking (two builds, three controls, byte-identical repro)
- [x] 10-14-PLAN.md — Wave 14: fixtures/mooneye-cgb derivation, manifest, rights files and eligibility (byte-identical repro)
- [x] 10-15-PLAN.md — Wave 15: VerifyMooneyeCgb digest/inventory verifier with tamper controls, install scan and CI repro job
- [x] 10-16-PLAN.md — Wave 16: Mooneye CGB runner suite with expected-unsupported rows and the real-ROM DIV sweep
- [x] 10-17-PLAN.md — Wave 17: banking-indirection A/B benchmark, CTest receipt checks and evidence report
- [x] 10-18-PLAN.md — Wave 18: fuzz, loader and consumer coverage on both profiles, instance isolation, ASan
- [x] 10-19-PLAN.md — Wave 19: D-070 half-dot ADR with static asserts and contract, guide, support ledger, D-071+
- [x] 10-20-PLAN.md — Wave 20: phase gates, evidence head, PR with six owner veto items (left open), handoff to /gsd-verify-work 10

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
**Plans**: 15/15 plans complete

Plans:
**Wave 1**
- [x] 11-01-PLAN.md — DMG shade-identity pin, colour mutant harness, independent 6144-row priority truth oracle

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 11-02-PLAN.md — CRAM storage and BCPD/OCPD ports, OPRI, post-boot CRAM rows, DEFERRED(11) cells flipped

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 11-03-PLAN.md — RGB555 dual store, per-dot dispatch, CGB attributes/priority composer

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 11-04-PLAN.md — compat renderer: default compat palette, ppu_compat_resolve, ppu_pixel_compat

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 11-05-PLAN.md — truth table through the real colour path, per-input priority and attribute mutants

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 11-06-PLAN.md — public gbb_copy_frame_rgb555 and compat palette API, docs and installed consumers

**Wave 7** *(blocked on Wave 6 completion)*
- [x] 11-07-PLAN.md — RGB555 helpers, colour-hblank fixture with copy-time-resolve mutant, manifest-driven repro

**Wave 8** *(blocked on Wave 7 completion)*
- [x] 11-08-PLAN.md — attribute, LCDC.0, CRAM, compat and LCD-off fixtures with predicates

**Wave 9** *(blocked on Wave 8 completion)*
- [x] 11-09-PLAN.md — runner RGB555 frame cases (D-43) and independent RGB555 digest vectors

**Wave 10** *(blocked on Wave 9 completion)*
- [x] 11-10-PLAN.md — MagenTests CGB ROMs with predicates and mutants; AGE deviation stated (D-20)

**Wave 11** *(blocked on Wave 10 completion)*
- [x] 11-11-PLAN.md — AGE m3-bg-* / Mealybug m3_* disposition records (D-09) and optional local acid2 runner (D-24)
- [x] 11-12-PLAN.md — player --model auto|dmg|cgb, colour presentation, CGB smoke and mutants

**Wave 12** *(blocked on Wave 11 completion)*
- [x] 11-13-PLAN.md — player claims follow evidence (D-44) with a cross-surface agreement check

**Wave 13** *(blocked on Wave 12 completion)*
- [x] 11-14-PLAN.md — model-gate audit, palette fuzzing, A/B benchmark, final DMG identity and player suite

**Wave 14** *(blocked on Wave 13 completion)*
- [x] 11-15-PLAN.md — DECISIONS/INDEX/LESSONS records, COVERAGE.md declaration, Phase 12 handoff

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
**Plans**: 19/19 plans complete

Plans:
**Wave 1**
- [x] 12-01-PLAN.md — tracer: pre-change identity pin, KEY1 arm + STOP switch with persisted stall, cpu_ticks sites, D-13 trace rule
- [x] 12-02-PLAN.md — AGE vendoring part 1: rights/provenance, manifest-driven rebuild script with offline negative controls, spsw-div ROM, fixture-repro step

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 12-03-PLAN.md — runtime-mask mutant harness (multi-site anchors, guard control), cpu_ticks contract (M18), per-field reset clears
- [x] 12-04-PLAN.md — AGE vendoring part 2: the remaining 12 ROMs and manifest rows

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 12-05-PLAN.md — device scaling: tick-unit timer/serial/DMA, divider and APU tap, PPU/APU/RTC unscaled scan

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 12-06-PLAN.md — STOP decision table cases 1-4, switch cost, KEY1/KEY0 contract, DMG identity, operand/FF04/KEY0 negatives

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 12-07-PLAN.md — stall wake, realignment, exact length (macro-derived), budget semantics, headroom pre-check, EI;STOP mutant

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 12-08-PLAN.md — research:12 gate dispositions, GATE-84.. rows, cgb-profile stall derivation and STOP docs

**Wave 7** *(blocked on Wave 6 completion)*
- [x] 12-09-PLAN.md — AGE driver, spsw-div pass, public mutant library, D-37 window re-measure and re-pin rule before any constant-derived pin

**Wave 8** *(blocked on Wave 7 completion)*
- [x] 12-10-PLAN.md — original cgb-speed probe ROM, first-principles expectations and controls, audio/frame digests

**Wave 9** *(blocked on Wave 8 completion)*
- [x] 12-11-PLAN.md — hostile pre-switch entry points (selector byte) with rule-derived outcomes
- [x] 12-12-PLAN.md — player speed smoke, claims edit, installed consumer speed guests with an unarmed-twin negative

**Wave 10** *(blocked on Wave 9 completion)*
- [x] 12-13-PLAN.md — cgb-speed byte-exact rebuild script, repro controls and fixture-repro step

**Wave 11** *(blocked on Wave 10 completion)*
- [x] 12-14-PLAN.md — partition equivalence sweeps, real-constant stall-end windows in both directions via snapshot

**Wave 12** *(blocked on Wave 11 completion)*
- [x] 12-15-PLAN.md — cgb_speed fuzz mode, seeds, oracle control and dictionary

**Wave 13** *(blocked on Wave 12 completion)*
- [x] 12-16-PLAN.md — AGE per-ROM dispositions decided by measurement, generated age_ tests, vendored-byte guards

**Wave 14** *(blocked on Wave 13 completion)*
- [x] 12-17-PLAN.md — pinned_by for every named expected failure (four new pin tests), verifier and docs mirror, sensitivity sweep

**Wave 15** *(blocked on Wave 14 completion)*
- [x] 12-18-PLAN.md — host docs, header comments and stale-claim scanner

**Wave 16** *(blocked on Wave 15 completion)*
- [x] 12-19-PLAN.md — DECISIONS/LESSONS/INDEX, 12-BENCH.md with hosted ASan cost, COVERAGE.md, Phase 13 handoff

### Phase 13: CGB HDMA

**Goal**: CGB software can use general-purpose and HBlank VRAM DMA with hardware-shaped CPU stall, cancel and readback, bounded per run.
**Depends on**: Phase 12 (must not run in parallel with it)
**Requirements**: CGB-07
**Success Criteria** (what must be TRUE):
  1. General-purpose DMA stalls the CPU for the transfer and HBlank DMA moves one block per visible-line mode-0 entry, both writing to the current VRAM bank, verified by SameSuite `dma/*` ROMs and original fixtures.
  2. Cancelling via HDMA5 bit 7, HDMA5 readback, HALT during a transfer, LCD-off and invalid sources follow stated behaviors with tests; unresearched cases are recorded as unspecified rather than invented.
  3. Every transfer is bounded (at most 128 blocks) and partitioned runs stay equivalent across transfers; MagenTests `hblank_vram_dma` passes with its oracle class recorded, and Mealybug `hdma_*-C` results are reported as informational CGB-C evidence outside the CGB-E denominator.

**Research**: DEEP (LCD-off, mode-3 GDMA, overflow state, HALT, cross-bank source, same-half-dot ordering).
**Plans**: 9/12 plans executed

Plans:
**Wave 1**
- [x] 13-01-PLAN.md — Real-transfer boundary gate and guest register visibility

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 13-02-PLAN.md — Complete bounded transfer, restart and address policies
- [x] 13-06-PLAN.md — Pinned four-case SameSuite admission and reproduction

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 13-03-PLAN.md — Real HALT wake and independent competing stalls

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 13-04-PLAN.md — Partition, lifecycle and hostile-resource invariants
- [x] 13-08-PLAN.md — Original visible DMA guest and existing player smoke

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 13-05-PLAN.md — Bounded runtime mutation sensitivity and inherited anchors

**Wave 6**
- [x] 13-07-PLAN.md — Magen HDMA admission and structural differential oracle

**Wave 7** *(blocked on Wave 6 completion)*
- [x] 13-09-PLAN.md — Executed SameSuite dispositions and optional CGB-C boundary

**Wave 8** *(blocked on Wave 7 completion)*
- [ ] 13-10-PLAN.md — Installed C/C++ DMA consumers and closed package contents

**Wave 9** *(blocked on Wave 8 completion)*
- [ ] 13-11-PLAN.md — Atomic consumer claims and executable documentation contracts

**Wave 10** *(blocked on Wave 9 completion)*
- [ ] 13-12-PLAN.md — Current-revision lane cost, evidence closure and phase pause

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
| 7. DMG Game Acceptance and Regression Baseline | v0.2 | 17/17 | Complete    | 2026-10-11 |
| 8. Cartridge Seam, MBC5 and MBC2 | v0.2 | 10/10 | Complete    | 2026-10-11 |
| 9. MBC3, Deterministic RTC and Cartridge Persistence | v0.2 | 18/18 | Complete    | 2026-10-11 |
| 10. CGB Profile, Banking and Register Visibility | v0.2 | 20/20 | Complete    | 2026-10-12 |
| 11. CGB Colour Rendering and Player Colour | v0.2 | 15/15 | Complete    | 2026-10-13 |
| 12. CGB Double Speed | v0.2 | 19/19 | Complete    | 2026-10-14 |
| 13. CGB HDMA | v0.2 | 9/12 | In Progress | - |
| 14. CGB-E Model Qualification and Corpus | v0.2 | 0/TBD | Not started | - |
| 15. CGB Acceptance, Support Ledger and v0.2.0 Release | v0.2 | 0/TBD | Not started | - |
