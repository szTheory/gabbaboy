# Requirements: GabbaBoy

**Defined:** 2026-10-10
**Core value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Active milestone:** v0.2 — Color & Cartridge Breadth. Evidence and recommendations: [research/v0.2/SUMMARY.md](research/v0.2/SUMMARY.md). Shipped v0.1 requirements are archived in [milestones/v0.1-REQUIREMENTS.md](milestones/v0.1-REQUIREMENTS.md).

## v0.2 requirements

Every requirement maps to exactly one phase. Completion needs implementation and current evidence, not only a document or proposed test. Support claims name the model (DMG-CPU-B or CGB-CPU-E), the corpus revision and the executed denominator; test-ROM pass rates are never presented as game compatibility. Refines the v0.1 commitments CGB-01..03, CART-01 and RTC-01 into atomic requirements.

### Game-level acceptance and evidence tooling

- [ ] **GAME-01**: A maintainer can admit one rights-clear DMG game (Libbet and the Magic Floor primary; Tobu Tobu Girl only if GBDK runtime terms clear) whose manifest records source commit, licence text, per-asset provenance, release digest and reproducibility statement; admission fails if any embedded-asset right is unrecorded.
- [ ] **GAME-02**: A headless acceptance run of that game, driven by scripted input timed in emulated device time, reaches a guest-memory progress predicate with recorded frame digests and a non-silent PCM digest, while the same run without input does not reach it, on Linux, macOS and Windows CI.
- [ ] **GAME-03**: The packaged SDL3 player launches the admitted game and passes an automated input/progress/audio smoke.
- [ ] **EVID-01**: The runner can capture a frame at the `LD B,B` breakpoint as a canonical RGB digest (image written only on failure), replay a scripted joypad input file with emulated-time waits, and honour per-fixture model applicability (`model_pass`, `model_fail`, `target_revision`, `unsupported-model`) without any new dependency.
- [ ] **EVID-02**: A frozen DMG regression baseline (executed CTest inventory, Mooneye closures, acceptance frame/audio digests, benchmark baseline) is recorded, and every later v0.2 phase proves DMG-CPU-B output byte-identical to it or documents an approved, evidence-backed change.

### Cartridges

- [ ] **CART-01**: Cartridge behavior sits behind a type-table-driven mapper seam (kind, RAM, battery, RTC, rumble) with no observable change: the MBC1 suite, battery continuation fixture and DMG baseline remain byte-identical.
- [ ] **CART-02**: A caller can run MBC5 cartridges (`$19-$1E`) with 9-bit ROM banking including bank 0 in the switchable window, ROM up to 8 MiB and RAM up to 128 KiB; the rumble bit is masked from RAM banking and exposed as host-readable state; the pinned Mooneye `mbc5` derivatives pass 8/8.
- [ ] **CART-03**: A caller can run MBC2 cartridges (`$05/$06`) with address-bit-8 register decode, 512x4-bit built-in RAM echoed through `A000-BFFF` with upper nibbles reading as 1s, and a 512-byte battery image; the pinned Mooneye `mbc2` derivatives pass 7/7.
- [ ] **CART-04**: A caller can run MBC3 cartridges (`$0F-$13`) with 7-bit ROM banking and RAM banks `00-03`; MBC30 and other unsupported variants are rejected with an explicit error; MagenTests out-of-bounds SRAM cases pass for MBC1/MBC3/MBC5.
- [ ] **CART-05**: The loader rejects every contradictory type/ROM-size/RAM-size/file-length combination for the new mappers (exact, one-under, one-over) with no partial mutation, and fuzz targets cover the raised 8 MiB bound.
- [ ] **CART-06**: Battery data for MBC2, MBC3 and MBC5 survives a fresh-process continuation in the player without corrupting a good save, and every v0.1 save file still loads unchanged.

### Deterministic RTC

- [ ] **RTC-01**: The MBC3 RTC advances only from emulated time (2^23 half-dots per second, independent of CPU speed) with correct latch (`00` then `01`), halt, sticky day carry and 9-bit day counter; rtc3test passes; CI proves `src/core` uses no host clock.
- [ ] **RTC-02**: A host can apply elapsed wall-clock seconds between runs through an explicit catch-up call with defined negative, overflow and rollback policy; catch-up is never a side effect of battery import.
- [ ] **RTC-03**: RTC state persists in a versioned little-endian core battery block, and the player's save envelope records the save time and applies the catch-up policy on reopen; an original RTC continuation fixture passes across fresh processes.

### Game Boy Color (CGB-CPU-E)

- [ ] **CGB-01**: A caller can select the `GBB_PROFILE_CGB_CPU_E` profile, probe a ROM and query the instance for model and execution mode (CGB or DMG-compatibility, from header `$143` bit 7); CGB-only ROMs load on the DMG profile with an informational flag; post-boot state is mode-specific with recorded provenance.
- [ ] **CGB-02**: Every DMG-specific behavior is audited and tagged by model, and a register visibility matrix (DMG, CGB, CGB in DMG-compatibility mode) has a test per cell; KEY0 is locked after boot.
- [ ] **CGB-03**: CGB software can bank VRAM (2x8 KiB) and WRAM (8x4 KiB) with correct echo-RAM and OAM DMA source behavior.
- [ ] **CGB-04**: CGB software renders with tile attributes, BG/OBJ colour palette RAM (auto-increment, mode-3 lockout) and CGB priority rules, exposed through a new RGB555 frame call; the existing DMG frame call stays byte-identical for DMG.
- [ ] **CGB-05**: DMG software on the CGB profile renders through a fixed, original, documented compatibility palette that a host can override; no boot-ROM palette table is shipped.
- [ ] **CGB-06**: CGB software can switch to double speed via KEY1 and STOP: CPU, timer, serial and OAM DMA run at twice the rate while PPU and APU timing are unchanged, the switch pause is modelled, and partitioned runs stay equivalent.
- [ ] **CGB-07**: CGB software can use general-purpose and HBlank VRAM DMA with CPU stall, cancel, HDMA5 readback and HALT interaction, bounded per run.
- [ ] **CGB-08**: CGB-E specific APU and I/O differences (PCM12/PCM34, `FF72-FF75`, IR port stub) are implemented with per-test model applicability and named expected failures.
- [ ] **CGB-09**: The SDL3 player can run software as `--model auto|dmg|cgb` with colour presentation and passes an automated CGB smoke.
- [ ] **CGB-10**: A headless CGB-E corpus (AGE, SameSuite, MagenTests and the CGB-applicable Mooneye subset; acid2/Mealybug only if font rights clear) reports per-suite denominators with failure and exclusion reasons.
- [ ] **CGB-11**: One rights-clear CGB game passes a game-level acceptance run in the same style as GAME-02, or the ledger explicitly states that no CGB game-level evidence exists.

### Qualified release

- [ ] **SHIP-09**: The v0.2 support ledger names DMG-CPU-B and CGB-CPU-E, the mapper matrix, evidence class, corpus revisions, denominators, failures, exclusions and known issues.
- [ ] **SHIP-10**: Installed C and C++ consumers exercise the new public API (profile selection, ROM probe, RGB555 frames, RTC catch-up), and API, cartridge/save, integration and third-party-notice documentation is current.
- [ ] **SHIP-11**: A qualified exact-tag v0.2.0 release ships with refreshed fuzzing and performance baselines, including a measured DMG performance comparison against v0.1.

## Future requirements

Deferred to v0.3 States & Integration (provisional) or later:

- **STATE-01**: Transactional versioned native save states covering hidden in-flight state with exact continuation equivalence.
- **INT-01**: Qualified Playstead adapter; libretro only if its value is demonstrated.
- BGB/VBA-M 44/48-byte RTC footer import/export as a host-side interop adapter.
- Title-hash DMG-compatibility palette selection (only if boot-ROM data provenance clears).
- Host haptics for MBC5 rumble; second DMG game (Tobu Tobu Girl) for battery persistence; gbclock RTC game once plugin licences are checked.

## Out of scope

| Feature or claim | Reason |
|---|---|
| AGB, CGB-0 through CGB-D, other silicon revisions | One named CGB revision keeps claims and tests exact; others are listed as unsupported in the ledger. |
| MBC30, MBC1M, MBC6/7, HuC, MMM01, Camera | Uncommon controllers; explicit rejection instead of guessing. |
| IR peer link, link cable | Peripheral/linked execution belongs to a later milestone. |
| Colour-correction fidelity or perceptual quality claims | No perceptual measurement; raw RGB555 with documented expansion only. |
| Physical hardware qualification | No hardware access; evidence is author-verified, differential or project-original. |
| Unlicensed fixtures (Blargg, MBC3 Tester, TurtleTests, GPL Gambatte tests) in the repository | Redistribution rights not demonstrated; local oracle use only. |
| Host clock inside the core | Determinism; wall-clock policy belongs to adapters. |
| Universal compatibility or "plays games" claims | Corpus- and model-qualified evidence only. |

## Traceability

Every v0.2 requirement maps to exactly one phase in [ROADMAP.md](ROADMAP.md).

| Requirement | Phase | Status |
|-------------|-------|--------|
| GAME-01 | Phase 7 | Pending |
| GAME-02 | Phase 7 | Pending |
| GAME-03 | Phase 7 | Pending |
| EVID-01 | Phase 7 | Pending |
| EVID-02 | Phase 7 | Pending |
| CART-01 | Phase 8 | Pending |
| CART-02 | Phase 8 | Pending |
| CART-03 | Phase 8 | Pending |
| CART-04 | Phase 9 | Pending |
| CART-05 | Phase 9 | Pending |
| CART-06 | Phase 9 | Pending |
| RTC-01 | Phase 9 | Pending |
| RTC-02 | Phase 9 | Pending |
| RTC-03 | Phase 9 | Pending |
| CGB-01 | Phase 10 | Pending |
| CGB-02 | Phase 10 | Pending |
| CGB-03 | Phase 10 | Pending |
| CGB-04 | Phase 11 | Pending |
| CGB-05 | Phase 11 | Pending |
| CGB-06 | Phase 12 | Pending |
| CGB-07 | Phase 13 | Pending |
| CGB-08 | Phase 14 | Pending |
| CGB-09 | Phase 11 | Pending |
| CGB-10 | Phase 14 | Pending |
| CGB-11 | Phase 15 | Pending |
| SHIP-09 | Phase 15 | Pending |
| SHIP-10 | Phase 15 | Pending |
| SHIP-11 | Phase 15 | Pending |

**Coverage:**
- v0.2 requirements: 28 total
- Mapped to phases: 28
- Unmapped: 0 ✓

---
*Requirements defined: 2026-10-10*
*Last updated: 2026-10-10 after v0.2 roadmap creation (Phases 7–15)*
