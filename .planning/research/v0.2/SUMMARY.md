# Project Research Summary: GabbaBoy v0.2 Color & Cartridge Breadth

**Project:** GabbaBoy, milestone v0.2 Color & Cartridge Breadth (delta over the founding research in [`../SUMMARY.md`](../SUMMARY.md))
**Domain:** Game Boy / Game Boy Color emulator core (portable C17), subsequent milestone
**Researched:** 2026-10-10
**Confidence:** MEDIUM overall. HIGH for licenses, revisions, digests and build reproducibility. MEDIUM for mapper and PPU behavior drawn from Pan Docs. LOW-to-MEDIUM for CGB timing details still tagged `[VERIFY]` or `[KB]` in the source files.

Topic evidence: [STACK.md](STACK.md), [FEATURES.md](FEATURES.md), [ARCHITECTURE.md](ARCHITECTURE.md), [PITFALLS.md](PITFALLS.md).

## Executive Summary

v0.2 extends a shipped, bootless DMG-CPU-B core (ROM-only and MBC1 cartridges, 160x144 shade frames, four-channel APU) to three capabilities: a rights-clear game proven end to end on the existing DMG player, MBC2/MBC3/MBC5 cartridges with a deterministic RTC, and one CGB silicon revision (CPU-CGB-E) running in CGB mode and DMG-compatibility mode. Experienced emulator authors build this in a fixed order: freeze the existing hardware output first, isolate mapper and model state behind explicit seams, then add each model-specific behavior as a declared profile predicate with test applicability. The emulated half-dot timeline stays the only clock, and every claim is scoped to a named corpus rather than "compatible."

The stack needs no new runtime or build dependency. New material is fixture data (immutable revisions, notices, SHA-256 digests), a small project-authored runner addition (frame hash at the `LD B,B` breakpoint, scripted joypad input, 5-to-8-bit colour expansion), and opt-in Linux-only legacy RGBDS reproduction recipes. The architecture adds a cartridge module with a type table, banked WRAM/VRAM, palette RAM and an RGB555 frame path, a CPU-stall branch distinct from the existing `stopped` branch, and a lazily evaluated RTC. Double speed and HDMA are the high-risk items: both change the run loop, so they land in sequence, and both need deeper phase research before requirements.

Main risks: (1) CGB array reshaping can silently change shipped DMG output, so a DMG digest baseline must exist before CGB code; (2) DMG-only quirks (STOP, boot state, PPU/APU quirks, `read_supported` allow-lists) leak into CGB unless a model-gate audit tags them; (3) speed switching and HDMA are easy to model as shortcuts; (4) RTC determinism and latch semantics are subtle; (5) test-ROM pass rates can be presented as game compatibility. Four rights items (mgblib-derived font provenance, GBDK runtime terms, gbclock plugin licences, the compat-palette table) gate specific fixtures and must be resolved or scoped before those fixtures are vendored.

## Key Findings

### Recommended Stack

No change to language, build or existing pins. ISO C17, CMake 3.25+, Ninja, CTest unchanged. RGBDS 1.0.1 stays (do not bump to 1.0.4; it changes owned-fixture bytes for no gain). WLA-DX keeps its pin (`91c52b1`, wla-gb 10.7, `-nS`). Mooneye stays at `31510e1`. Legacy RGBDS 0.4.2 (`ede982b`) and 0.6.1 (`69a5739`) are for byte-for-byte reproduction of specific upstream ROMs only, in an opt-in workflow.

- Core: ISO C17 / CMake / Ninja / CTest (nothing new needed).
- RGBDS 1.0.1: assembles all SameSuite and AGE ROMs; project fixtures.
- Legacy RGBDS 0.4.2 / 0.6.1 (reproduction only): cgb-acid2, dmg-acid2, rtc3test, Mealybug need 0.4.x; MagenTests needs 0.6.1.

Copy-not-depend additions (small, project-owned): frame capture at `LD B,B` canonicalized to RGB888 and hashed with the existing SHA-256 (PPM only on failure); CGB expansion `(x<<3)|(x>>2)`; scripted joypad with emulated-time waits (rtc3test is ~47 emulated seconds, headless); stdlib-only `python3 -I` PNG-to-digest script at admission time only.

Do not add: libpng, stb, zlib, a JSON or RTC library, `time()`/`clock_gettime` in core, submodules for fixtures, Docker as a required tool.

### Fixture Catalogue

Follows `fixtures/<suite>/{manifest.json, LICENSE.txt, SOURCES.md}`.

**Admit (required CI, subject to gates):**
- Mooneye `emulator-only/mbc2` (7) and `mbc5` (8), existing derivative recipe. Headers state hardware verification on genuine MBC2A and MBC5 chips. `rom_64Mb` (8 MiB) is the only test of the ninth ROM bank bit: keep in repo, exclude from install/packages.
- MagenTests `mbc_oob_sram_mbc1/mbc3/mbc5` (MIT; byte-identical to 0.5.0 assets on RGBDS 0.6.1).
- rtc3test v004 (Unlicense): MBC3 RTC conformance gate; screen oracle with scripted input.
- Original fixtures: `mbc2-continuation` and `mbc3-rtc-continuation` (no third-party ROM covers these).
- SameSuite non-APU DMA/interrupt/PPU (6 ROMs; X11). Rebuild is provenance; no per-ROM revision documented; classify author-verified, differential vs SameBoy CGB-E.
- AGE test ROMs (MIT; CC0 font): main CGB-E and double-speed corpus; builds identically on RGBDS 1.0.1 and 0.9.4; hardware-verified on CGB B, C, E per author.
- MagenTests CGB: `bg_oam_priority`, `oam_internal_priority`, `ppu_disabled_state` (MIT). `hblank_vram_dma` goes with HDMA. Skip `key0_lock_after_boot`.
- Mooneye acceptance subset with CGB in header pass list (53 of 75). Start with CPU/timer/DMA. Parse `pass:`/`fail:` into `model_pass` data.

**Admit with restrictions:**
- cgb-acid2 v1.1 and dmg-acid2 v1.0 (MIT): blocked for vendoring on G1 (mgblib font). If not cleared, digest-pinned optional local fixtures.
- Mealybug `dma/hdma_timing-C`, `hdma_during_halt-C`: evidence is CGB-C (and AGB/DMG blob), not CGB-E. Informational with `target_revision: CGB-C`; not counted toward CGB-E.
- Mealybug `mbc/mbc3_rtc`: most automatable independent RTC check; font under G1; conditional.
- SameSuite `apu/*` (72): later, per-ROM applicability and expected-failure reasons. Never "all on all."

**Do not admit:** Mealybug `ppu/m3_*` (expected images only for CGB-C/D; record `unsupported-model` for CGB-E); Blargg (no licence); MBC3 Tester and TurtleTests (no licence); Gambatte (GPL; local oracle only); gekkio.fi prebuilt Mooneye ROMs (embed Darkrose font); cgb-acid-hell (out of scope). Do not trust Homebrew Hub licence metadata (wrong for Tuff); read each game's own repo.

### Rights-clear Games (acceptance candidates)

| | Libbet and the Magic Floor v0.08 (FEATURES) | Tobu Tobu Girl (STACK) |
|---|---|---|
| Cartridge | Type `$00` ROM-only, 32 KiB, `$143=$80`, SGB flag `$03` | MBC1+RAM+BATT, 256 KiB, DMG |
| Licence | zlib (Yerrick, Korth credited) | Code MIT; assets CC BY 4.0 (attribution); Tangram Games |
| Open items | Bundled-asset licence completeness; exact release/build recipe; source commit not yet in manifest (G5) | Built with GBDK 2.96a and MMLGB, not reproducible in CI; GBDK 2.96a runtime redistribution terms unverified (G2) |
| Value | Isolates DMG path, no mapper dependency; SGB-packet tolerance test; later CGB smoke via `$80` | Exercises battery persistence (already supported); no new mapper evidence |

**Recommendation:** Libbet and the Magic Floor as primary, because it is ROM-only and proves the DMG path without a mapper dependency. Gate admission on: primary-repo licence text, per-asset provenance, release-asset digest, reproducibility statement. Tobu Tobu Girl is the fallback and second-game candidate for battery persistence, once G2 clears. No "game works" claim until one passes.

### Expected Features

**Must have (v0.2 table stakes):**
- DMG game acceptance: frame digests before/after scripted input; non-silent PCM after start; guest-memory progress predicate with negative control (same run without input must not reach the state).
- MBC5: 9-bit ROM bank, bank 0 selectable at `$4000`; RAM 4 bits (3 on rumble types `$1C-$1E`); ROM to 8 MiB; RAM to 128 KiB.
- MBC2: bit-8 register decode; 512x4 RAM echoed through `A000-BFFF`; upper nibble reads as 1s; 512-byte battery image; ROM to 256 KiB.
- MBC3 + deterministic RTC: 7-bit ROM bank (0 to 1); RAM `00-03`; RTC `08-0C`; latch `00` then `01`; halt, day carry, 9-bit days; sub-second prescaler reset on seconds writes (verify). Timer-only `$0F`.
- CGB-E profile, CGB and DMG-compat modes; header-driven mode from `$143` bit 7; `$C0` CGB-only handling; VRAM bank 1 and WRAM banks; attributes; CRAM with auto-increment and mode-3 lockout; BG/OBJ priority.
- RGB555 as a new frame function; `gbb_copy_frame` keeps shade semantics and errors on CGB.
- Double speed: KEY1 arm and STOP switch; CPU/timer/serial/OAM DMA at 2x; PPU/HDMA/sound unchanged; APU sequencer on DIV bit 5.
- GDMA and HBlank DMA with CPU stall, cancel, HALT interaction, HDMA5 read semantics.
- CGB-E APU subset documented as passing on CGB-E (PCM12/34, `div_write_trigger`, sweep/trigger) with listed expected failures.
- RP (`FF56`) and `FF72-FF75` as masked registers; `FF76/FF77` read-only PCM.
- Player: `--model auto|dmg|cgb`; RGB555 presentation with 5-to-8 expansion; RTC save handling; ROM cap to 8 MiB.

**Should have:** DMG-compat default palette with host override; rumble state exposed to host (haptics optional); explicit raw `.sav` import/export with 44/48-byte RTC footer as adapter; window title showing model/mode.

**Defer or exclude (named in ledger):** AGB; CGB-0 through CGB-D; MBC30; MBC1M; HuC, MMM01, MBC6/7, camera; IR peer link; rumble motor realism; colour correction fidelity; perceptual claims; physical hardware; save states; Playstead. Title-hash palette table (G4). Host-clock sync during play.

### Architecture Approach

v0.1 holds: one translation unit, instance-owned machine, `uint64_t` half-dot timeline, no hidden globals. v0.2 adds plain-integer sub-structs (`cart_state`, `rtc_state`, `cgb_state`, `hdma_state`) with a single reset each, and enum + `switch` dispatch. No vtables or function pointers (blocks v0.3 serialization).

Components:
1. Cartridge module (`src/core/cartridge.c/.h`, new): type table (kind, RAM, battery, RTC, rumble); header validation; ROM/RAM access; control writes; battery eligibility. Moves MBC1 out of `gabbaboy.c`.
2. RTC (new): lazy, emulated-time clock. Stores `sub_half_dots`, live and latched counters, `synced_at`. No per-half-dot work. Syncs at latch writes, register writes, halt toggles, battery export.
3. Bus (modified): region-decoded `read8`/`write8`; `read_supported` as fail-closed allow-list for every new register/window; banked `wram[8][4096]`, `vram[2][8192]`.
4. PPU colour path (modified): attribute and bank fetch; palette RAM; `ppu_pixel_word` returning RGB555 in CGB. Internal frame widens to `uint16_t`; public DMG bytes unchanged.
5. Timing domains (modified): `double_speed` flag; `cpu_ticks(m,t) = t >> double_speed` at choke points (`instruction_cost`, bus offset, interrupt/halt literals, divider, APU DIV mask via `apu_div_mask(m)`, serial, OAM DMA period). `execute()` itself needs no edit.
6. CPU stall (new): run-loop branch parallel to `stopped`; devices keep advancing; bounded quanta <= 64 half-dots; preflighted. Used by speed switch, GDMA, HBlank DMA.
7. HDMA/GDMA (new): integer state; byte-pair scheduling in `advance_devices_to` next to OAM DMA; HBlank trigger at mode-0 edge in `ppu_set_mode`; source dispatch (ROM, cart RAM, WRAM bank; `$FF` for illegal).
8. Public API (append-only): `GBB_PROFILE_CGB_CPU_E = 2`; `gbb_probe_rom`; `gbb_get_info`; `gbb_copy_frame_rgb555`; `gbb_rtc_catch_up` (between runs only); new error codes appended.
9. Host adapters (player, runner): ROM probe, profile choice, RGB555 presentation, envelope v1/v2, wall-clock catch-up policy. Core never calls a clock.

Patterns: three combinations only (DMG/DMG, CGB-CPU-E/CGB, CGB-CPU-E/DMG-compat). Post-boot state is a table keyed by mode; DMG row byte-identical. Speed switch is separate from DMG STOP sleep; never sets `stopped`. Save blob: RAM bytes for non-RTC carts (byte-identical to v0.1 MBC1); RAM plus fixed-size little-endian RTC block (~17 bytes, versioned) for RTC carts. No struct dumps.

### Critical Pitfalls

1. DMG output silently changes (V2-01). Freeze DMG regression set before CGB code: 184 CTest, frame/audio digests for acceptance and Mooneye closures, benchmark baseline. Byte-identical DMG results for the milestone. Keep public DMG frame bytes; add colour as new format; measure banking indirection.
2. DMG-only assumptions leak into CGB (V2-02, V2-20). Model-gate audit before CGB code: tag every DMG-specific branch `DMG_ONLY | CGB_ONLY | BOTH | UNKNOWN` in code and `docs/`. Register visibility matrix (register x {DMG, CGB-native, CGB-compat}) with one test per cell.
3. Speed switch as clock multiplier or flag flip (V2-03, V2-04). Record timeline-unit decision before coding (half-dot, exact for both speeds). Model pause (~2050 M-cycles) as explicit state with deadline; PPU/APU keep advancing. Test usual pre-switch sequence (IE=0, JOYP=`$30`, KEY1 armed, STOP) and hostile sequence (IE non-zero, pending IRQ, held button).
4. HDMA as instant copy or OAM DMA clone (V2-05). Separate stall state in the scheduler; block start on mode-0 edge; defined LCD-off, HALT, cancel, mid-transfer bank change, invalid source behavior; bounded (<= 128 blocks).
5. RTC nondeterminism and latch errors (V2-13/14/15). Only time source is emulated time: 1 RTC second = 2^23 half-dots (= 4,194,304 normal-speed T-cycles; do not use the T-cycle figure literally in double speed). Offline progress via explicit `gbb_rtc_catch_up` with checked arithmetic, honouring halt and carry, saturating. CI guard: no `time`/`clock`/`rand` includes in `src/core`. Table-driven latch tests (0,1 latches; 1,1 does not; 0,0,1 latches; 1,0,1 latches).
6. Compatibility claimed from test-ROM pass rates (V2-24, V2-26). Ledger: model x feature x evidence class x corpus revision x counts. "Supported" = passes named corpus and acceptance run, never "plays games." Docs lint for "compatible."

Minor but recurring: echo RAM must follow selected WRAM bank; OAM DMA source decoding differs by model; MBC2 battery canonicalization; header lies reject with no partial mutation; docs, changelog, ledger in the same PR as each capability.

## Conflicts Reconciled

| # | Topic | Conflict | Resolution |
|---|---|---|---|
| 1 | Speed switch and HDMA order | PITFALLS puts speed switch in foundation and HDMA in video phase. ARCHITECTURE and FEATURES: double speed (8) before HDMA (9), both after colour PPU. | Adopt ARCHITECTURE/FEATURES order. Timeline-unit ADR recorded at CGB foundation entry (PITFALLS' point); code in speed phase. |
| 2 | Seam refactor vs mappers first | FEATURES: "mappers before colour." ARCHITECTURE: behavior-preserving seam first. PITFALLS: one mapper per family. | Seam first, then mappers, separate per family. |
| 3 | Acceptance game | FEATURES: Libbet (ROM-only, zlib). STACK: Tobu Tobu Girl (MBC1, GBDK terms unverified). | Libbet primary; Tobu fallback after G2. |
| 4 | RTC persistence format | FEATURES: write BGB/VBA-M 48-byte footer (read 44/48, write 48) and public footer codec in core. ARCHITECTURE/PITFALLS: explicit LE core RTC block inside opaque blob; host envelope carries save timestamp. | Core-native RTC block for all native saves. 44/48-byte footer becomes host-side interop adapter, import-first; export only after layout verified against pinned primary source. No footer codec in public core API in v0.2. Reason: core stays free of file formats and wall-clock (AGENTS.md); one persistence path. |
| 5 | Profile name | FEATURES: `GBB_PROFILE_CGB_E`. ARCHITECTURE: `GBB_PROFILE_CGB_CPU_E` (D-008). | `GBB_PROFILE_CGB_CPU_E`. |
| 6 | CGB-only ROM on DMG profile | FEATURES: new error `GBB_UNSUPPORTED_MODEL_FOR_ROM`. ARCHITECTURE/PITFALLS: load as hardware does, flag. | Load with info flag and player warning. |
| 7 | DMG-compat palette | FEATURES: title-hash table with provenance review. ARCHITECTURE/PITFALLS: one fixed original palette. | Fixed original palette default, host-overridable. Title-hash excluded unless G4 cleared. |
| 8 | Mealybug HDMA evidence | STACK admits `hdma_*-C`. FEATURES/ARCHITECTURE gate CGB-E only. | Admit as informational, CGB-C applicability, not in CGB-E denominator. |
| 9 | Framebuffer | PITFALLS: don't reinterpret buffer. ARCHITECTURE: widen to `uint16_t`. | Both hold: internal widens; public DMG bytes and `gbb_copy_frame` unchanged, enforced by digest gate. |
| 10 | MBC2 upper nibble on read | PITFALLS: modeled convention. STACK/FEATURES: Mooneye `ram`/`bits_unused`. | Settled: reads return upper nibble 1s (Mooneye-pinned). Export normalizes to `$F`; import masks. |
| 11 | RTC catch-up name | FEATURES: `gbb_rtc_advance_seconds`. ARCHITECTURE: `gbb_rtc_catch_up`. | `gbb_rtc_catch_up`; deliberate host call, never import/restore side effect. |
| 12 | DIV at speed switch | ARCHITECTURE resets DIV on switch. FEATURES: DIV does not tick during pause. | Both: reset at switch and no ticking during pause; verify in the double-speed phase. |
| 13 | Pause-time interrupts | Pan Docs TODO. | Not claimed; expected failure or unspecified. |
| 14 | RTC clock figure | PITFALLS: 4,194,304 T-cycles. STACK/ARCHITECTURE: 8,388,608 half-dots. | Both correct at normal speed. Code uses half-dots. |

## Implications for Roadmap

Proposed slots P1 to P11; the roadmapper assigns final numbers. Each phase stops with evidence and a named next command (AGENTS.md). P3 and P4 can run in parallel after P2. P8 and P9 must not run in parallel.

**P1: DMG game-level acceptance and regression freeze.** Required first; finds DMG defects before CGB confusion; establishes acceptance method and DMG digest baseline. Delivers: admitted Libbet (or Tobu fallback) with full manifest (source commit, licence text, per-asset provenance, digest, embedded-asset notes; empty `rights.embedded_assets` fails); `tests/acceptance/` harness with scripted input and frame/audio digests; runner extensions (frame capture at `LD B,B`, PPM on failure, scripted input, emulated-time waits); manifest fields `model_pass`, `model_fail`, `target_revision`, `oracle`, `reference_digest`, `input_script`, `rtc_policy`, `rights.embedded_assets`; guest-memory progress predicate with negative control; SGB-packet tolerance test; DMG digest baseline across the CTest suite, Mooneye closures, and the acceptance run on Linux/macOS/Windows. Avoids: V2-26, V2-27, V2-17, V2-01. Research: light.

**P2: Behavior-preserving cartridge seam and model-gate audit.** Highest regression risk per line moved; v0.1 suite is the oracle; precedes all mappers and CGB bus work. Delivers: `cartridge.c/.h` with type table; MBC1 behind `cart_*` with identical behavior; `read8`/`write8` region split; `read_supported` via `cart_ram_window_mapped`; battery eligibility from type table; model-gate audit (every DMG-specific branch tagged in code and `docs/`); gate: MBC1 suite, continuation fixture, DMG digests byte-identical. Avoids: V2-08, V2-02, V2-01. Research: standard.

**P3: MBC5 and ROM/RAM matrix.** Simplest new mapper; most CGB titles use it; raise ROM cap once here. Delivers: MBC5 (`$19-$1E`): 9-bit bank from two registers; bank 0 selectable at `$4000`; RAM 4 bits (3 on rumble); RAM enable low nibble `$A` (test `$0A` and `$1A`); cap 2 MiB to 8 MiB; ROM codes `$07/$08`; RAM codes `$04/$05`; recheck size computations and fuzz bounds; eight Mooneye `mbc5` ROMs; original ROMs for bank `$1FF`, bank 0 upper window, rumble masking; battery round trip at 128 KiB; loader matrix (type x ROM code x RAM code x file length) incl. exact/one-under/one-over. Avoids: V2-09, V2-10, V2-12, V2-08. Research: standard; confirm loader bound at 8 MiB and repo size policy for `rom_64Mb`.

**P4: MBC2.** Independent of RTC; small; parallel with P3. Delivers: bit-8 decode (bit 8 clear = RAM enable; set = ROM bank, 0 to 1), table-driven test; 512x4 RAM echo through `A000-BFFF`; size from mapper type, not `$149`; types `$05/$06` with RAM code `$00`; 512-byte blob, export `$F` upper nibble, import masked; seven Mooneye `mbc2` ROMs; `mbc2-continuation`; ROM limit 256 KiB. Avoids: V2-11, V2-12. Research: standard.

**P5: MBC3, deterministic RTC, battery blob, envelope v2.** Only phase coupling emulated time to persistence; isolate. Delivers: MBC3 banking (7-bit ROM; RAM `00-03`; RTC `08-0C`; latch `00`->`01`); types `$0F-$13`; MBC30 rejected with `GBB_UNSUPPORTED_CARTRIDGE_VARIANT`; RTC module lazy, 2^23 half-dots per second, checked 64-bit arithmetic, halt, sticky day carry, 9-bit days, 15-bit crystal prescaler (256 half-dots per tick); seconds-write prescaler reset (verify); `gbb_rtc_catch_up(instance, seconds)` between runs only, honours halt, saturates, O(1), never fired by import/restore; core blob = RAM + versioned LE RTC block (~17 bytes); RTC writes bump the battery generation, elapsed ticks do not; player envelope v2 for RTC carts only (host `saved_at`, CRC over payload); v1 unchanged and loadable; rtc3test as conformance gate (scripted input, ~47 s emulated); `mbc3-rtc-continuation`; Mealybug `mbc3_rtc` if G1 clears. Avoids: V2-13, V2-14, V2-15, V2-16, V2-01. Research: DEEP (write-while-running, rollover, sub-second reset, carry, halt).

**P6: CGB profile skeleton, banking, post-boot, register visibility (no colour output).** Changes array shapes and public enum; gated on P1 baseline and P2 audit; half-dot ADR recorded here. Delivers: `GBB_PROFILE_CGB_CPU_E`; `gbb_probe_rom`; `gbb_get_info`; execution mode from `$143` bit 7 at load; `$C0` on DMG loads with flag; post-boot table per mode with per-field provenance (Pan Docs section, Mooneye `boot_regs-cgb`/`boot_hwio-C`/`boot_div-cgbABCDE`, or project choice); DMG row byte-identical; `vram[2]`, `wram[8]`, VBK, SVBK, echo rules; `read_supported` additions one at a time; KEY0 boot-state only, locked; visibility matrix with one test per cell; ADR for half-dot decision; benchmark of banking indirection. Avoids: V2-01, V2-02, V2-06, V2-07, V2-20, V2-03 (decision). Research: moderate (DIV/LY phase; compat-mode register readability).

**P7: CGB colour PPU, palette RAM, RGB555 frame, compat palette, player colour.** First visible CGB output. Delivers: BG attribute fetch from bank 1 (palette, bank, flips, priority); OBJ attribute bank/palette; LCDC bit 0 master priority in CGB (verify); single priority function with exhaustive truth table over {mode, OPRI, LCDC.0, BG priority, OAM priority, colour indices}; CRAM (`bg_pal[64]`, `obj_pal[64]`, BGPI/OBPI auto-increment; mode-3 lockout separate predicate; blocked-write auto-increment as stated model); `gbb_copy_frame_rgb555` with same validation; `gbb_copy_frame` on CGB errors; DMG-compat via `BGP/OBP0/OBP1` then CRAM palette 0 (BG) and 0/1 (OBJ); one fixed original compat palette; player `--model auto|dmg|cgb`, XRGB1555 or RGBA expansion, correction off; tests: cgb-acid2 (if G1), AGE and MagenTests CGB PPU ROMs, original attribute-bit fixtures. Avoids: V2-18, V2-19, V2-21, V2-29, V2-24. Research: moderate-to-deep (LCDC.0, OPRI timing, CGB mode-3 length, blocked-write increment).

**P8: Double speed and CPU stall.** Run-loop change; must precede HDMA. Delivers: KEY1 arm and switch via STOP on CGB only (never `stopped`, never `GBB_STOP_STOPPED`); `cpu_ticks` scaling at choke points; divider; APU DIV bit 5 (`apu_div_mask`); serial 512 per bit, fast 16; OAM DMA period (4, verify); TIMA reload 4; stall branch (quanta <= 64 half-dots, devices advance, counts toward budget); named pause constant (~2050 M-cycles in master half-dots, sourced); tests: original DIV/TIMA/serial-per-scanline ROM; AGE `speed-switch` and `stat-mode*-ds` (emulator-only; avoid `caution/*`); SameSuite APU DIV subset; "run N, stop, run M = run N+M" across stall. Avoids: V2-03, V2-04, V2-22. Research: DEEP (pause interrupts; DIV and PPU in pause; applicable test list).

**P9: GDMA and HBlank DMA.** Needs banking, PPU mode edges, sources, stall with speed awareness; not parallel with P8. Delivers: FF51-FF55 live-counter semantics; GDMA with stall; HBlank DMA at mode-0 entry on visible lines only; cancel by bit 7 = 0; HDMA5 read semantics; byte-pair scheduling in `advance_devices_to`; source dispatch (ROM, cart RAM, WRAM; `$FF` illegal; VRAM source stated undefined); destination uses current VRAM bank; tests: SameSuite `dma/*` (6); MagenTests `hblank_vram_dma` (SameBoy-assisted oracle, record); Mealybug `hdma_*-C` informational; original cancel/HALT ROMs. Avoids: V2-05, V2-21. Research: DEEP (LCD-off, mode-3 GDMA, overflow state, HALT, cross-bank source, same-half-dot ordering).

**P10: CGB-E model qualification.** Last; tests need full surface; declared applicability per delta. Delivers: CGB-E APU subset (PCM12/34 via per-channel DAC taps; powered-off length/register rules; wave RAM init; sweep/DIV-write triggers; expected failures `channel_4_freq_change` and `channel_1_sweep_restart_2` unless implemented; zombie mode only if documented for CGB-E); RP stub, `FF72-75` masked storage, `FF76/77`; serial fast clock; CGB timer/TAC eligibility records (not DMG reuse); echo/unused I/O per mode; corpus expansion (AGE `oam`, `vram`, `halt`, `lcd-align-ly`; Mooneye CGB acceptance beyond CPU/timer; SameSuite APU with per-ROM `model_pass`); Mealybug `m3_*` as `unsupported-model`; per-suite denominators with reasons. Avoids: V2-23, V2-24, V2-25, V2-22, rest of V2-02. Research: deep-moderate (CGB-E APU rules; wave RAM; SameBoy disagreement list; enumerate Mooneye CGB suffixed list).

**P11: CGB acceptance, ledger, docs, v0.2 release.** Delivers: one rights-clear CGB title (lowest-risk MIT: Rebound (MBC5, no RAM, small); Rex Runner (CGB-compatible MBC5, 32 KiB); GBHack (asset credits audit); Aevilia (Apache-2.0 NOTICE, MBC5 battery, CGB-only)), or state "no CGB game-level evidence"; model-qualified ledger `docs/support/v0.2.0.md` (models DMG-CPU-B and CGB-CPU-E; evidence columns; denominators; exclusions); docs (`cartridge-and-saves.md`, `native-integration.md`, limitations, `THIRD_PARTY_NOTICES.md`); exact-tag release; changelog compare links (GB-RELEASE-001). Avoids: V2-24, V2-28, V2-29. Research: light.

**Phase ordering rationale:** freeze and acceptance first (P1); seam before mappers, mappers before CGB (P2-P5); profile and banking before colour and speed (P6-P7); speed before HDMA (P8-P9); qualification last (P10-P11). Parallel allowed: P3/P4 after P2; P7 player colour on frozen `gbb_copy_frame_rgb555` signature after P6. P8/P9 not parallel.

**Research flags:** Deep before planning: P5 (RTC), P8 (speed pause), P9 (HDMA), P7 (colour PPU), P10 (APU/model). Light: P1, P6, P11. Standard: P2, P3, P4, fixture manifest process.

**Gating items:**

| ID | Item | Blocks | Owner phase | Action |
|---|---|---|---|---|
| G1 | mgblib `old_skool_outline_thick` font: author/source/licence not stated; cgb-acid2 Hello World drawn with it | Vendoring cgb-acid2, dmg-acid2, Mealybug bytes into required CI (and Mealybug RTC) | P7, P10, P5 (Mealybug) | Ask mgblib author. If unconfirmed: digest-pinned optional local runs; required CGB rendering evidence from AGE (CC0 font), SameSuite, MagenTests, originals. |
| G2 | GBDK 2.96a runtime redistribution terms (Tobu ROMs) | Tobu Tobu Girl/DX as admitted binaries | P1 if chosen | Verify, or pick Libbet. |
| G3 | gbclock v0.5: bundled community GB Studio plugins with no per-plugin licence (MEDIUM) | gbclock as RTC fixture | Not required for P5 | Use rtc3test and originals as primary RTC evidence; gbclock only after plugin licences checked. |
| G4 | DMG-compat title-hash palette table (boot-ROM-derived) | Title-hash palette selection | P7 | Excluded unless rights decision clears it. |
| G5 | Libbet asset licence completeness and release recipe | P1 admission | P1 | Checklist before admission. |
| G6 | Mooneye derivatives: common font replaced with zero bytes (Darkrose is GPL/CC BY-SA) | Claim wording | P3-P5 | Already resolved in v0.1. Scope claims to "derivative of `31510e1`, same code path." |
| G7 | Low-risk notices: SameSuite `hexdigits.2bpp`; rtc3test font; older `hardware.inc` | None | P1-P10 | Accept at repo level; record. |

**Decisions requiring DECISIONS.md entries:** (1) profile name `GBB_PROFILE_CGB_CPU_E` (D-008); (2) core-native RTC block; footer interop host-side and deferred (Conflict #4); (3) CGB-only ROM loads on DMG with flag (Conflict #6); (4) fixed original DMG-compat palette; title-hash excluded (Conflict #7); (5) single CGB revision CGB-CPU-E; CGB-0..D, AGB, MBC30 unsupported and named; (6) MBC2 upper-nibble and MBC5 RAM-enable policies; (7) Libbet primary pending checklist.

## Confidence Assessment

| Area | Confidence | Notes |
|---|---|---|
| Stack | HIGH | Licences, revisions, digests, builds read at primary sources and reproduced locally. Individual ROM hardware applicability is author-asserted (MEDIUM). G1, G2 open. |
| Features | MEDIUM | Pan Docs MBC2/3/5 and CGB pages read directly (MEDIUM-HIGH with their own TO-BE-VERIFIED notes). CGB compat register readability and LCDC.0 LOW. BGB footer from secondary page. |
| Architecture | MEDIUM | Integration points HIGH (read from `src/core/gabbaboy.c`, header, player, runner). Many hardware numbers `[VERIFY]` not re-fetched (pause length, double-speed HDMA timing, OAM DMA period, palette blocked-write increment). |
| Pitfalls | MEDIUM | Process items HIGH (repo lessons). Many hardware items `[KB]`. |

**Overall: MEDIUM.** Strong for mapper bit-level behavior (hardware-verified upstream ROMs), licences and process. Weak for CGB timing, pause, HDMA edges, CGB-E APU deltas. The ledger must say "unknown" there. SameBoy, mGBA, Gambatte were not source-inspected; every "verify in SameBoy" item is open work.

### Gaps to Address

- Speed-switch pause (P8): interrupts, DIV and PPU during pause. Deep research; unknowns as expected failures.
- RTC write/rollover/sub-second (P5): derive from rtc3test source and expected images; confirm seconds-write prescaler reset.
- CGB-E post-boot DIV/LY/STAT (P6): pin to Mooneye `boot_div-cgbABCDE`, `boot_regs-cgb`, or record as policy.
- CGB compat-mode register readability (P6): verify per register (Mooneye `unused_hwio-C`, AGE) before the matrix.
- LCDC.0, OPRI, CGB mode-3 length (P7): cgb-acid2 (if G1) and originals.
- Blocked-write palette auto-increment (P7): choose, state, test.
- HDMA edges (P9): mark unresearched cases; do not invent values.
- CGB-E APU deltas (P10): SameSuite README primary; verify each delta; do not rely on recalled DMG-to-CGB differences.
- Mooneye CGB-suffixed list (P10): enumerate from pinned tree; parse headers.
- Hardware claims are author-asserted: record device list per suite; no independent hardware claim.
- Derivative ROMs (G6): scope claims.
- Repo size (P3): 8 MiB `rom_64Mb` committed raw; confirm policy and install exclusion.
- Loader bound at 8 MiB (P3): confirm cap and fuzz; do not silently drop the ninth-bank-bit proof.
- Acceptance game (P1): Libbet checklist (G5); Tobu only after G2.
- Support wording (P11): "passes named corpus and acceptance run," with denominators.

## Sources

Primary (read directly this milestone):
- Mooneye Test Suite `31510e12eea6286d36eea060a6adde755e1067aa` (README, LICENSE, `common/common.s`, `emulator-only/mbc2|mbc5`, `misc/boot_*`, `misc/bits/unused_hwio-C`). https://github.com/Gekkio/mooneye-test-suite
- SameSuite `f15645fb049a47ea235f6d2c9a033e72d8087901` (LICENSE, `apu/README.md`, `include/base.inc`). https://github.com/LIJI32/SameSuite
- cgb-acid2 `04c6ca40cf75b6a93513fe596de4ab797efaff97` (v1.1); dmg-acid2 `8a98ce731f96dde032ffb22ec36dc985d78fdb18` (v1.0); mgblib `5d829bf`/`1d9045a`; Mealybug Tearoom Tests `70e88fb90b59d19dfbb9c3ac36c64105202bb1f4`. https://github.com/mattcurrie
- AGE test ROMs `1f5bc10e2cb60b86c19f8d0287ff78f410c4f639`. https://github.com/c-sp/age-test-roms
- MagenTests 0.5.0 `3f9c090f16e5a721db776febb9ba7d773e1c819c`. https://github.com/alloncm/MagenTests
- rtc3test v004 `80ae792bf1b3c3387929b912e6df001af3511e24` (Unlicense). https://github.com/aaaaaa123456789/rtc3test
- c-sp game-boy-test-roms howtos. https://github.com/c-sp/gameboy-test-roms
- Pan Docs (read 2026-10-10; MEDIUM-HIGH): Power-Up Sequence, CGB Registers, Palettes, OAM, MBC2, MBC3, MBC5, Cartridge Header. https://gbdev.io/pandocs/
- GB Homebrew Hub database `50293559a496a3e20382fbf6a2e84b70ec622f88` (licence fields unreliable). https://github.com/gbdev/database
- Candidate game repos: tobutobugirl and tobutobugirl-dx (SimonLarsen), Aevilia-GB (ISSOtm), gbhack (statico), ReboundGB (DevEd2), GBcorp (drludos), rex-runner-gb (etdv-thevoid), DawnWillCome (eishiya), gbclock (kresp0), Libbet (pinobatch).
- RGBDS (1.0.1 pin; 0.4.2, 0.6.1 reproduction only). https://github.com/gbdev/rgbds
- WLA-DX `91c52b1f4ef3cc8ba3c0638f7536539579af6a9f`. https://github.com/vhelin/wla-dx
- gbdev hardware.inc (CC0-1.0). https://github.com/gbdev/hardware.inc
- Cellphone Font (CC0). https://opengameart.org/content/ascii-bitmap-font-cellphone
- Darkrose 8x8 font (GPLv2 and CC BY-SA 3.0). https://opengameart.org/content/8x8-ascii-bitmap-font-with-c-source
- GBDK-2020 licence statement. https://github.com/gbdk-2020/gbdk-2020

Secondary (MEDIUM or LOW): BGB RTC save note (https://bgb.bircd.org/rtcsave.html; not BGB source); Gekkio GBCTR rev. 192 (https://gekkio.fi/files/gb-docs/gbctr.pdf; pre-CGB emphasis); SameBoy features page (comparison only; source not inspected).

Repository evidence: `src/core/gabbaboy.c` (2305 lines), `include/gabbaboy/gabbaboy.h`, `docs/cartridge-and-saves.md`, `src/player/session.c`, `src/player/main.c`, `src/runner/main.c`, `CMakeLists.txt`, `fixtures/mooneye/{SOURCES.md,ELIGIBILITY.md,FONT-LICENSE.txt,headless-report.patch}`, `.planning/PROJECT.md`, `.planning/research/SUMMARY.md`, `.planning/context/LESSONS.md`, `.planning/context/DECISIONS.md` (D-002, D-008, D-012, D-013, D-016, D-024, D-025).

---
*Research completed: 2026-10-10. Ready for roadmap.*
