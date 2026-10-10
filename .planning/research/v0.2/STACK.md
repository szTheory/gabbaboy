# Stack Research: v0.2 Color & Cartridge Breadth (delta only)

**Domain:** Game Boy / Game Boy Color emulator core (portable C17). Delta over `.planning/research/STACK.md` and `HARDWARE-AND-VALIDATION.md`.
**Researched:** 2026-10-10
**Confidence:** HIGH for licenses, revisions and build reproducibility (primary sources read directly, and every build claim below was reproduced locally); MEDIUM for hardware applicability of individual ROMs (author-asserted); LOW where marked.

Method note: sources were read at the primary repositories (LICENSE files, READMEs, headers inside the assembly, release assets, tree listings via the GitHub API). Builds and byte comparisons were run in a scratch directory on macOS (RGBDS 1.0.1 release binary, SHA-256 matches the existing manifests) and in Alpine 3.20 Linux containers on the same Apple-silicon host (legacy RGBDS built from source). The OpenGSD research-plan/classify-confidence seam was not used for these primary-source reads.

## Verdict: no new runtime or build dependency

v0.2 needs **zero** new libraries, submodules, GitHub Actions, or package-manager installs in the core, runner, or player. Everything new is (a) fixture data with notices and digests, (b) a small amount of project-authored C inside the existing runner (it already carries its own SHA-256), and (c) opt-in, Linux-only fixture-reproduction recipes that build old pinned assemblers from source the same way WLA-DX is built today. This matches the owner's copy-over-dependency preference.

Specifically do NOT add: libpng/stb_image/zlib (see "Reference images"), a JSON library in C, an RTC library or any `time()`/`clock_gettime` in the core, SDL changes, Python packages (stdlib-only Python with `-I` is already the project norm for tooling), Docker as a required tool (used here only for research), or git submodules for fixtures.

## Recommended Stack

### Core Technologies (unchanged, plus pins for the new fixtures)

| Technology | Version / pin | Purpose | Why |
|---|---|---|---|
| ISO C17, CMake >= 3.25, Ninja, CTest | unchanged | core, runner, tests | Nothing in v0.2 needs a newer language or build feature. |
| RGBDS | **1.0.1** (existing pin; macOS zip SHA-256 `2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645`, Linux x86_64 `80a5cad8dae27e24e46a93041352c47cadbc165103983f41c2b3082c42f6dad9`) | project-authored fixtures, SameSuite, AGE test roms | Verified: all 78 SameSuite `.asm` assemble/link on 1.0.1 (obsolescence warnings only), and all 50 AGE ROMs at HEAD build identically on 1.0.1 and 0.9.4. Latest is v1.0.4 (2026-09-22); do not bump, because a bump changes owned-fixture bytes and buys nothing. |
| WLA-DX | existing pin: commit `91c52b1f4ef3cc8ba3c0638f7536539579af6a9f` (wla-gb 10.7, wlalink 5.22), linker flag `-nS` | Mooneye derivative fixtures | Existing `fixtures/mooneye/headless-report.patch` (SHA-256 `c3679ab5...16e5a721`) applies cleanly at the pinned Mooneye revision and builds the MBC2/MBC5 tests unchanged (verified). master has moved (7ae11df, 2026-10-07); do not repin. |
| RGBDS **0.4.2** (legacy, reproduction only) | git commit `ede982b50a68a6253ffbab17dc4184710b08032f`, tree `8aca0f4f3684fed60490440b7143b46c4974033e` | rebuild cgb-acid2, dmg-acid2, rtc3test, Mealybug | cgb-acid2 and dmg-acid2 sources do NOT assemble on 1.0.1 (hardware.inc macros, verified failure); rtc3test only assembles on 0.4.x (0.5.1 fails, verified; the c-sp aggregator also documents 0.4.2). Needs `make`, a C++ compiler, bison, flex, libpng-dev, pkg-config. |
| RGBDS **0.6.1** (legacy, reproduction only) | git commit `69a573923f208d625df589c7a54a18738b07969c`, tree `78910921528b724d75f3bfced5d8212318049b44` | rebuild MagenTests 0.5.0 | The Makefile passes `rgbasm -L`, removed by 0.8.0. 0.6.1 reproduces all 8 release ROMs byte-for-byte (verified). |

Policy recommendation: **vendor the upstream author's released bytes when they equal a pinned legacy rebuild** (true for cgb-acid2, dmg-acid2, rtc3test, MagenTests), so ordinary CTest never needs a legacy assembler and the hosted `fixture-repro` leg proves the equality. For Mealybug (no current release; the zip in the repo is stale and has only 31 of 35 ROMs) and SameSuite/AGE (no releases), the rebuild IS the provenance.

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---|---|---|---|
| (none new) | | | |

Copy-not-depend items, all small and project-owned:

| Capability to add | Where | Size / approach |
|---|---|---|
| Framebuffer capture at the `LD B,B` software breakpoint | `src/runner/main.c` | cgb-acid2, dmg-acid2, Mealybug, SameSuite and AGE all stop on `LD B,B` (verified in each source). Canonicalize to RGB888, hash with the runner's existing SHA-256, compare to a stored digest. Write a PPM (trivial text header + raw bytes) only on failure for human diffing. |
| CGB 5-bit to 8-bit expansion `(x<<3)\|(x>>2)` | runner presentation canonicalizer | Specified identically by cgb-acid2, Mealybug and AGE. DMG shades `00/55/AA/FF`. |
| CGB-in-DMG-mode palettes (bootless) | core CGB profile | AGE documents BG `#000000 #0063C6 #7BFF31 #FFFFFF` and OBJ `#000000 #943939 #FF8484 #FFFFFF` (darkest to lightest) as the expected compat-mode colors; dmg-acid2 ships a `reference-cgb.png` for the same case. Treat as MEDIUM until checked against Pan Docs/boot ROM behavior. Needed by rtc3test and MBC3-tester style screenshot oracles. |
| Scripted joypad + emulated-time waits | runner input script | rtc3test is menu-driven: A (basic, 13 emulated s), Down+A (range, 8 s), Down+Down+A (sub-second writes, 26 s) per the c-sp howto; total ~47 emulated seconds, so keep it a headless fast-forward job, never wall-clock. |
| Reference-PNG to canonical-digest conversion | `tests/scripts/` (stdlib Python, `python3 -I`) | Verified: a ~35-line stdlib decoder (zlib+struct, palette depths 2/4/8) turns cgb-acid2 `img/reference.png` into 160x144 RGB with digest `df86492849e620d0cd2d421013795997d083ddc2a1ef216b44bf6b9b2f603803`. Run at admission time only; CTest compares digests, so C never decodes PNG. |

### Development Tools

| Tool | Purpose | Notes |
|---|---|---|
| `fixtures/<suite>/manifest.json` + `LICENSE.txt` + `SOURCES.md` | existing admission shape | Reuse exactly (see Integration). |
| `tests/scripts/reproduce-*.sh` + `.github/workflows/fixture-repro.yml` | networked, explicit reproduction | Add a `reproduce-legacy-rgbds.sh` that fetches each pinned commit by SHA, verifies the tree SHA, builds, and `--compare`s bytes. Network stays out of ordinary CTest. |

## Fixture catalogue (immutable revisions, rights, recipes, digests)

Conventions: "Rights evidence" is what I read at the primary source. "Embedded-asset caveat" matters because ROM bytes embed fonts/logos even when the source license is clean. Digests are SHA-256 captured in this research unless marked "capture at admission".

### A. Cartridge mappers

| Fixture | Revision | Rights evidence | Recipe and digests | Oracle / protocol | Decision |
|---|---|---|---|---|---|
| **Mooneye `emulator-only/mbc2/*` (7)**: `bits_ramg, bits_romb, bits_unused, ram, rom_512kb, rom_1Mb, rom_2Mb` | Mooneye `31510e12eea6286d36eea060a6adde755e1067aa` (existing pin, already vetted; tree `2b8c5242...`) | MIT, Copyright 2014-2022 Joonas Javanainen (root LICENSE, per-file headers). Only embedded-asset issue is `common/font.bin` (see Fonts). | Reuse existing derivative recipe (apply `headless-report.patch`, zero font, `wla-gb -I common`, `wlalink -nS -d -S`). Indicative digests from a local build (recapture with the pinned toolchain): `bits_ramg 7eb87a09...`, `bits_romb f382f82c...`, `bits_unused d33bed57...`, `ram 5b82d04e...`, `rom_512kb 4c7a8a58...`, `rom_1Mb 7eba692d...`, `rom_2Mb 32530509...`. Sizes 32 KiB to 256 KiB. | Mooneye `LD B,B` + Fibonacci registers (existing adapter). Headers state results were verified on a **genuine MBC2A chip** via flash cart, so these are hardware-backed. `ram.s` asserts upper nibble reads back as 1s (round 6), which settles the "undefined bits" choice for the core. | **Admit all 7.** Required for CART-01 (MBC2). |
| **Mooneye `emulator-only/mbc5/*` (8)**: `rom_512kb ... rom_64Mb` | same | MIT, same | Same recipe. `rom_8Mb` (1 MiB) `176cd6f9...`, `rom_64Mb` (8 MiB, 512 banks) `f1148d3c...`. Sizes 64 KiB to **8 MiB**. gzip shows ~12 KB for the 8 MiB ROM. | Same; verified on a genuine MBC5 chip per header. `rom_64Mb` is the **only** test exercising the ninth bank bit (banks 256-511). | **Admit all 8**, raw in the tree (git compresses). Do NOT add the 4/8 MiB ROMs to `install()`/packages (currently only three small fixtures install). Confirm the loader's ROM cap allows 8 MiB. No zlib needed. |
| (optional backfill) Mooneye `emulator-only/mbc1/*` (13) | same | same | same recipe | same | v0.1 admitted only a project-authored MBC1 continuation. These close MBC1 gaps for free; suggest, not required for v0.2. |
| **MagenTests `mbc_oob_sram_mbc1/mbc3/mbc5`** | `3f9c090f16e5a721db776febb9ba7d773e1c819c` (tag/release `0.5.0`, 2025-03-22) | MIT, Copyright 2022 alloncm. Source includes gbdev `hardware.inc` (CC0-1.0, SPDX header in the pinned copy at `21ef22d01ac55151160f3d98110c2da8846a96b2`). | Release assets, reproduced byte-identical with **RGBDS 0.6.1** + that hardware.inc. `mbc_oob_sram_mbc1 83f1fc44...`, `_mbc3 03e13fa7...`, `_mbc5 e99f5263...` (full digests in the Appendix). 32 KiB each. | Screen oracle: whole screen green (white on DMG). CGB-compat header. Out-of-range SRAM address masking per mapper. | **Admit.** Cheap cross-mapper check including MBC3. |
| **rtc3test v004** | `aaaaaa123456789/rtc3test` `80ae792bf1b3c3387929b912e6df001af3511e24`; release `v004` (2020-12-02) asset `rtc3test.gb` | **Unlicense** (public-domain dedication in LICENSE). Embedded font is the common public 8x8 IBM-style table (`src/font.asm`); no separate notice exists. Treat font as LOW-risk, record the observation. | Release bytes `a271013fb37ea1d927b854798401320b220d57abb3ca77f3d318ceb8a9def30d` (32,768 B; header type `$0F` MBC3+TIMER+BATT, no RAM, CGB-compatible flag 0x80, `rgbfix -c -m 0x0f`). **Rebuilt byte-identical with RGBDS 0.4.2** (0.5.1 fails). | Interactive, screen oracle only (no `LD B,B`). Expected screenshots live in c-sp/gameboy-test-roms (`src/rtc3test-expected`). Tests timing to 1 ms (basic) and 1.5 ms (sub-second) against DIV/timer, so RTC must be driven by the **emulated** master timeline with sub-second state that resets on RTC register writes as hardware does. | **Admit as the MBC3 RTC conformance gate.** Needs runner input scripting and a screen-hash oracle. |
| **Mealybug `mbc/mbc3_rtc`** | `mattcurrie/mealybug-tearoom-tests` `70e88fb90b59d19dfbb9c3ac36c64105202bb1f4` (2020-12-19) | MIT, Copyright 2018/2020 Matt Currie (headers on each asm file). Embedded font `old_skool_outline_thick` (from `mgblib`) has **no stated provenance** (see Fonts). | No usable release (zip is stale). Rebuild: `rgbasm -i mgblib/ -o ...`, `rgblink`, `rgbfix -v -p 255` with `mgblib` at **`1d9045a4b4cbd1ec5223e672a1cef965e9fcd194`** (the Mealybug submodule pin; NOT the cgb-acid2 pin). Identical bytes on RGBDS 0.4.2 and 0.5.1, all 35 ROMs. `mbc3_rtc.gb` `6cde433ad6464a553b7bdba77f0f101b447d8c5cfa614302692174415ce77915`. | Machine-checkable: results bytes compared to `CorrectResults` in WRAM (`TestResult` 'P'/'F') and `LD B,B`. Uses `ONE_SECOND=1048576` M-cycles with 128 M-cycle tolerance, cart type `$10` (MBC3+TIMER+RAM+BATT), runs in CGB mode. | **Admit** (second, independent, more automatable RTC check) once the font question is closed or accepted. |
| **Original `fixtures/mbc3-rtc-continuation`** (project-authored, MIT) | n/a | Owner-authored | RGBDS 1.0.1, same shape as `mbc1-continuation` (`rgbfix -f hg -m 0x10 -r 3`). | Persist progress + RTC registers across a fresh process; assert deterministic RTC advance across exported/imported battery data, halt bit, day-carry, and **CGB double speed** (see pitfall). | **Write it.** No third-party ROM covers battery+RTC continuation or RTC under double speed. |
| **Original `fixtures/mbc2-continuation`** (MIT) | n/a | Owner-authored | RGBDS 1.0.1, `-m 0x06`. | 512 x 4-bit RAM persistence, upper-nibble handling, save size 512 bytes. | **Write it.** No permissive MBC2 homebrew game exists in the corpus (see Games). |

### B. CGB silicon profile

Target is CPU-CGB-E (DECISIONS D-008). Hardware-applicability notes use that target.

| Fixture | Revision | Rights evidence | Recipe and digests | Oracle / protocol | Decision |
|---|---|---|---|---|---|
| **cgb-acid2 v1.1** | `mattcurrie/cgb-acid2` `04c6ca40cf75b6a93513fe596de4ab797efaff97`; release asset `v1.1` | MIT, Copyright 2020 Matt Currie. Submodule `mgblib` `5d829bf2ffa1447dcfd63c5dab2c44488632617e` (MIT). **Caveat:** "Hello World" and footer are drawn with `old_skool_outline_thick` font tiles (header: generated from `old-skool-outline-thick.png`, no author/license stated) embedded in the ROM. | Release `cgb-acid2.gbc` `197fb0bcec544f0400527fc707e0a94f55435974986e6986b424ace5de81720e` (32,768 B). **Byte-identical rebuild** with RGBDS 0.4.1, 0.4.2 and 0.5.1 (`rgbgfx` for `footer.2bpp`; `rgbfix -C -t CGB-ACID2 -v -p 255`). Fails on 1.0.1. Reference `img/reference.png` canonical RGB digest `df86492849e620d0cd2d421013795997d083ddc2a1ef216b44bf6b9b2f603803` (file SHA-256 `9ea9c262c5383353...fdf01`). | Frame capture at `LD B,B`; zero differing pixels. Needs no double speed or WRAM banking (README), so it is a **first** CGB gate, not the CGB-01 exit. | **Admit**, subject to the font note. |
| **dmg-acid2 v1.0** | `mattcurrie/dmg-acid2` `8a98ce731f96dde032ffb22ec36dc985d78fdb18`; release `v1.0` | MIT (LICENSE). Same mgblib pin and font caveat. | Release `dmg-acid2.gb` `464e14b7d42e7feea0b7ede42be7071dc88913f75b9ffa444299424b63d1dff1`, byte-identical rebuild on RGBDS 0.4.1/0.4.2/0.5.1 (`rgbfix -t DMG-ACID2 -v -p 255`). Refs: `reference-dmg.png`, **`reference-cgb.png`** (CGB running DMG mode; canonical digest `809006777f2bd065d41541b6d3ba3ae2d7574d5662e69014681ed82e48f772bc`). | Same capture protocol. | **Admit.** It was never admitted in v0.1 and is the cheapest check of both the DMG path and CGB DMG-compat colorization. |
| **SameSuite (non-APU)**: `dma/gbc_dma_cont`, `dma/gdma_addr_mask`, `dma/hdma_lcd_off`, `dma/hdma_mode0`, `interrupt/ei_delay_halt`, `ppu/blocking_bgpi_increase` | `LIJI32/SameSuite` `f15645fb049a47ea235f6d2c9a033e72d8087901` (2025-10-11; RGBDS 0.9.x compatibility merge) | "X11 License", Copyright 2018-2023 Lior Halphon (MIT-equivalent text). `include/hardware.inc` is CC0-1.0 (SPDX). `include/hexdigits.2bpp` (512 bytes, embedded in every ROM) has no separate provenance statement; repo-level license covers it as the author's work (LOW-risk). | **No releases; rebuild is the provenance.** `rgbasm -I include/ -o x.o x.asm; rgblink -o x.gb x.o; rgbfix -jv x.gb` on RGBDS 1.0.1 (macOS arm64): `gbc_dma_cont cd20f67f...`, `gdma_addr_mask d409c95d...`, `hdma_lcd_off 637a3612...`, `hdma_mode0 53f8d643...` (full in Appendix). SGB tests excluded. | **Mooneye-compatible protocol**: Fibonacci `B..L` on pass, `$42` on fail, serial bytes, `LD B,B` (verified in `base.inc`), so the existing adapter works. Needs LY wait (PPU on) and CGB mode. Author documents no per-ROM revision for non-APU tests (c-sp also found none): classify as "author-verified, revision unspecified; differential vs SameBoy CGB-E". | **Admit** these 6 for HDMA/GDMA/BGPI. |
| **SameSuite `apu/*` (72 ROMs)** | same | same | Same recipe; all assemble. | Same. README: CGB-E passes all; CGB-D all but `channel_1_sweep_restart_2`; CGB-C passes only channel 3 and non-channel tests; pre-CGB pass only `div_write_trigger*`. SameBoy-as-CGB-E fails `channel_4_freq_change` and `channel_1_sweep_restart_2`. Filenames carry revisions (`-cgb0B`, `-cgbDE`, `-A`). | **Admit later, with per-ROM model applicability and expected-failure reasons** when CGB APU differences land. Never run "all on all". |
| **AGE test roms** | `c-sp/age-test-roms` `1f5bc10e2cb60b86c19f8d0287ff78f410c4f639` (2025-02-26) | MIT, Copyright 2021 Christoph Sprenger. Font = "Cellphone Font" by domsson, **CC0** (OpenGameArt page checked). `hardware.inc` is a pre-CC0 copy (equates only; no code bytes reach the ROM). | **Builds identically on RGBDS 1.0.1 and 0.9.4** (50 ROMs, `rgbasm -Weverything -I src -I src/_include`, `rgblink -t`, `rgbfix -v -p 255`; Makefile in repo). Capture all digests at admission. | Fibonacci registers + `LD B,B` for auto-verifiable tests; screenshot tests with per-model PNGs. Hardware-verified on DMG-CPU C, CGB B, C and **E**; names encode devices (`-cgbBCE`, `-cgbE`, `-ncmBCE` = non-CGB mode on CGB). Best CGB-E-aligned corpus found: `speed-switch/spsw-{div,mode0,stop-prefetch,ch2-lc-delay,tima}*`, `stat-mode*-ds`, `m3-bg-*-ds`, `lcd-align-ly`, `oam/*`, `vram/*`, `halt/*`. `speed-switch/caution/*` can hang or damage-risk on hardware per its WARNING.md; keep emulator-only and bounded. | **Admit as the main CGB-E and double-speed corpus.** Requires the same screenshot canonicalizer. |
| **MagenTests (CGB)**: `bg_oam_priority`, `oam_internal_priority`, `hblank_vram_dma`, `ppu_disabled_state` | as above | as above | Release 0.5.0 assets, byte-identical with RGBDS 0.6.1: `bg_oam_priority 1b2132b3...`, `hblank_vram_dma e8124ce6...`, `oam_internal_priority f54fb636...`, `ppu_disabled_state 4808fe83...`. | Screen oracle (green screens; `bg_oam_priority` hardware screenshot by ISSOtm; `hblank_vram_dma` found "HDMA halts while CPU halted" with SameBoy's help). Not `LD B,B`-driven; hash a captured frame after N frames. Skip `key0_lock_after_boot` (boot-ROM behavior; GabbaBoy is bootless). | **Admit.** |
| **Mealybug `dma/hdma_timing-C`, `dma/hdma_during_halt-C`** | as above | as above | `hdma_timing-C 8c876218...`, `hdma_during_halt-C 2a55c873...` (RGBDS 0.4.2/0.5.1 identical). | Author-verified: pass CGB, AGB 0/A/B/BE; fail DMG/MGB/SGB. Single and double speed HDMA timing vs STAT mode and DIV. | **Admit** (high value for HDMA + double speed). |
| **Mealybug PPU `m3_*` (CGB)** | as above | as above | same | Expected images exist only for **CPU CGB C and CPU CGB D** (and DMG-blob; two ROMs for DMG-CPU B). Not CGB-E. | **Do not gate CGB-E on these.** Record `unsupported-model` (CGB-E) unless evidence is acquired. Useful as DMG/CGB-C/D informational. |
| **Mooneye acceptance tests with `pass: ... CGB`** | existing pin | MIT | 53 of 75 acceptance ROMs list CGB among passing models (e.g. `oam_dma/*`, `timer/*`, `ppu/intr_2_*`, `halt_*`, `ei_*`). They are DMG-header ROMs, so on CGB they run in DMG-compat mode on the CGB CPU. Derive with the existing recipe; PPU-dependent ones need a different patch than the CPU/timer-only one. | Existing adapter. Parse each header's `pass:`/`fail:` lines into the manifest `model_pass` list so applicability is data, not prose. | **Admit CPU/timer/DMA subset** to cover CGB CPU differences cheaply; PPU ones after the PPU CGB work. `misc/boot_*` and `boot_*` are boot-state tests: out of scope for the bootless profile. |

### C. Fonts and embedded-asset rights (the per-asset audit)

| Asset | Where it ends up | Finding | Action |
|---|---|---|---|
| Mooneye `common/font.bin` (Darkrose 8x8 ASCII) | Every upstream-built Mooneye ROM | Origin page lists **GPLv2 and CC-BY-SA 3.0** (code is GPL-only, PNG GPLv2 + CC-BY-SA), not MIT. Repo has no separate notice. | Keep the existing zero-font substitution (`font-source.c`, 2032 B, digest `23ba65cb...`). Applies unchanged to all new Mooneye derivatives. Do NOT use gekkio.fi prebuilt ROMs. |
| `old_skool_outline_thick` (mgblib) | cgb-acid2, dmg-acid2, all Mealybug ROMs | File header says generated from `old-skool-outline-thick.png`; author, source and license are **not stated**; mgblib repo is MIT, history is a single "Add files" commit. Hello World in cgb-acid2 is drawn from these tiles, so substitution would change the reference image. | Record as an **open rights item**. Resolution order: (1) file an issue/ask the author (mattcurrie) to confirm provenance; (2) if unconfirmed, admit by digest-only fetch for optional local runs and rely on SameSuite/AGE (CC0 font) plus project-authored rendering fixtures for required CI. Decide in the requirements phase; this is the one real blocker for vendoring acid2 and Mealybug bytes. |
| `hexdigits.2bpp` (SameSuite) | SameSuite ROMs | no provenance; repo X11 license by the author | Accept at repo level; note LOW risk. |
| Cellphone Font (AGE) | AGE ROMs | CC0 by domsson (OGA page) | Clear. Cite in notice. |
| gbdev `hardware.inc` | assembly only; equates, no bytes in ROM | CC0-1.0 (new copies); older copies unlicensed headers | No ROM impact; keep out of redistributed source trees unless CC0 header present. |
| Nintendo logo bytes in header | every ROM | already present in all existing project ROMs via `rgbfix` | Out of scope; unchanged policy. |

### D. Do not admit (blocked or unsuitable)

| Corpus | Why | Revisit |
|---|---|---|
| Blargg tests (retrio mirror, c-sp bundle) | No license found (unchanged from v0.1). CGB sound coverage is available from SameSuite/AGE instead. | Only if the author grants terms. |
| MBC3 Tester (EricKirschenmann), TurtleTests (Powerlated) | Repositories have **no license**. | Skip. |
| Gambatte test suite | GPL-2.0 (gambatte-core); GPL bytes inside an MIT repo muddy rights. | Local-only comparator, not committed. |
| cgb-acid-hell | MIT but a stress test beyond v0.2 scope. | Optional local diagnostic. |
| Mooneye prebuilt `gekkio.fi` ROMs | Embed the Darkrose font. | Use the derivative recipe. |
| GB Homebrew Hub `license` metadata as proof | Unreliable: HH lists Tuff as MIT but its README says graphics, characters, sounds and maps are "Copyright (c) 2014 Ivo Wetzel. All rights reserved", code license text contradictory. | Always read the game's own repo. |

## Rights-clear candidate games (for later acceptance, not for v0.2 CI gating)

Source for bytes: GB Homebrew Hub database `gbdev/database` at commit `50293559a496a3e20382fbf6a2e84b70ec622f88` (GPLv3 for the database tooling; each entry keeps its own license). All entries below were cross-checked against the game's own repository, not just the HH field. Header facts are from the ROM bytes.

| Role | Game | ROM (file, size, SHA-256) | Header | Rights verified at primary source | Open items |
|---|---|---|---|---|---|
| **DMG acceptance gate (recommended)** | **Tobu Tobu Girl** (Tangram Games) | `tobu.gb`, 262,144 B, `5d3871cae77db2287807e8914fd21f76203e73aa3fec20955489d45cb4571d8f` | MBC1+RAM+BATT, DMG, ROM 256 KiB, RAM 8 KiB | Repo `SimonLarsen/tobutobugirl`: code **MIT**; "all assets (images, text, sound and music)" **CC BY 4.0**. Copyright 2017 Tangram Games. Attribution required (record in THIRD_PARTY_NOTICES, keep CC BY link). Music via mmlgb driver (`.mml` sources in repo). | Built with GBDK **2.96a** (+ MMLGB.jar, pyimgtogb): not reproducible in CI, so admit the digest-pinned HH binary; and the **2.96a runtime-library redistribution terms were not verified** (GBDK-2020 states some historical GBDK files were originally LGPL). Resolve before vendoring; fallback below. Meets the gate shape: MBC1 + battery (already supported), highscore persistence, music/SFX, input. |
| DMG/CGB dual (second gate) | Tobu Tobu Girl Deluxe | `tobudx.gb`, 262,144 B, `0a0e8018dbbc8d7f8cd99f05e7cdc7b4cc9e358ecfe9377ebfb2291a84c6e310` | MBC1+RAM+BATT, CGB-compatible (0x80) | Repo `SimonLarsen/tobutobugirl-dx`: code MIT, assets CC BY 4.0. | Same GBDK note. One ROM exercises DMG mode and CGB-enhanced mode. |
| CGB-only + MBC5 | **Aevilia** (ISSOtm et al.) | `aevilia.gbc`, 131,072 B, `67e784ed61846bc84bfe9f45b9da343371eec6b896ed1b945b64c0aec7aa735b` | MBC5+RAM+BATT, CGB-only (0xC0), RAM 128 KiB | Repo `ISSOtm/Aevilia-GB`: Apache-2.0 for "code/assets present in these repositories"; DevSound MIT. RGBDS-built; the repo itself ships `bin/aevilia.gbc`. | Credits cover art by others (Kai) under the repo license; keep Apache NOTICE text. |
| CGB-only + MBC5 | GBHack (statico) | `gbhack.gbc`, 262,144 B, `f93a27e8b6272771bbba96105a2754f27ffc3f8317d71c063bdbd60dd0d74527` | MBC5+RAM+BATT, CGB-only | Repo `statico/gbhack`: MIT; GBDK-2020 + hUGEDriver + CBT-FX. | Recent (2026); audit asset credits before use. |
| CGB-only + MBC5 | Rebound (DevEd) | `Rebound.gbc`, 131,072 B, `195765b8ca3b0fb7d37b7b92d0242d6c7e01ec71f27f93e565fa081e449cbb92` | MBC5, no RAM, CGB-only | Repo `DevEd2/ReboundGB`: MIT. README lists no third-party assets. | Small game; good MBC5 smoke test. |
| CGB-compatible detection | GB Corp. (Dr. Ludos) | `gbcorp.gb`, 32,768 B, `5a39926a23ff50448859b2d924d8bba5a8c68db91563783f0c593a3aa8e7bad3` | MBC5+RAM+BATT, 0x80 | Repo `drludos/GBcorp`: MIT; GBDK-2020 4.0.6; GBT Player. Gameplay depends on console model (CGB vs DMG), a natural check of `A=$11` detection. | Audit GBT Player and music credits. |
| CGB-compatible MBC5 | Rex Runner GB | `rex-runner.gb`, 32,768 B, `91bd12159d30e86cf4eb0312f28ff1c394e701085d6a8ca641ed92b2bcc8429c` | MBC5+RAM+BATT, 0x80 | Repo `etdv-thevoid/rex-runner-gb`: MIT. | Engine submodule licenses unaudited. |
| Large ROM MBC5 | Dawn Will Come (eishiya) | `DawnWillCome.gb`, 2 MiB, `3a3b9881b5a3a3708e217efd73f443f6a97782d3b0d3a2086e1a00ac176e5e9f` | MBC5+RAM+BATT, CGB-only | README: code (incl. IDE scripts) MIT; art and music **CC-BY-4.0** (H0lyhandgrenade, eishiya, Kezia Salmon); GB Studio engine © Chris Maltby. | GB Studio engine MIT notice must ship. |
| **MBC3 + RTC game** | **gbclock v0.5** (Santiago Crespo) | `gbclock_v0.5.gb`, 262,144 B, `560a745feb57ec02ba1c6bfcaa76c203d4abea4d7600ad548c0546c533824e2e` (GitHub release `v0.4` asset; repo `kresp0/gbclock` commit `f4de4a9be6265810471e69cca62a2bc025242286`) | **MBC3+TIMER+RAM+BATT ($10)**, RAM 32 KiB, DMG | Repo CC0-1.0; README: "source code and assets ... CC0". | Only rights-clear MBC3-RTC *game-level* binary found. It is a GB Studio project that bundles community plugins under `plugins/` (RTC, Printer, Advanced Dialogue ... ) with no per-plugin license, plus the MIT GB Studio engine and GBDK-2020 runtime (GBDK-2020 states compiled ROMs need no license text, except zx0/BSD-3 if used). Rights confidence MEDIUM. It also needs a controllable RTC or deterministic seed; its purpose is "shows RTC time and survives power-off". |

Not usable as clean games: Tuff (all rights reserved assets), Renegade Rush (third-party itch.io asset packs without stated terms), Shock Lobster (mixed third-party fonts/music), 2048gb (clean zlib but no audio, fails the audio-response criterion), CatMario-GB (derivative assets), any GPL title (uCity, Geometrix, Airaki: GPL-3.0-or-later binaries would complicate an MIT repo; keep out of the tree).

**MBC2:** no permissive MBC2 game turned up in the Homebrew Hub corpus: I read the metadata of all 1,361 entries and the ROM headers of the 75 files whose license field looked permissive or copyleft (none uses cartridge type 05/06); unlicensed entries were not inspected because they are not rights-clear anyway. All commercial MBC2 titles are off limits. MBC2 coverage is Mooneye (hardware-verified) plus the original continuation fixture.

## Installation

```bash
# Nothing new for the core, runner, player, or ordinary CTest.

# Project-authored fixtures and SameSuite/AGE: the existing pinned RGBDS 1.0.1
# (same archives/digests as fixtures/*/manifest.json).

# Opt-in legacy reproduction (Linux CI leg or container), pinned by commit and tree:
#   rgbds ede982b50a68a6253ffbab17dc4184710b08032f  (v0.4.2)  make -j4   # needs bison flex libpng-dev pkg-config
#   rgbds 69a573923f208d625df589c7a54a18738b07969c  (v0.6.1)  make -j4
# Mooneye derivatives: existing WLA-DX recipe in fixtures/mooneye/SOURCES.md.
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|---|---|---|
| Vendor released bytes that equal a pinned legacy rebuild | Always rebuild in CI | Only if a legacy toolchain proves non-reproducible on hosted runners (unverified on Ubuntu; verified on Alpine/Linux and macOS 1.0.1 only). |
| Canonical-RGB SHA-256 oracle with stdlib Python at admission | Embed libpng/stb in the runner | Never for this owner; ImageMagick `compare -metric AE` (the upstream suggestion) is a dev-time convenience only. |
| Mooneye derivative recipe for MBC tests | gekkio.fi prebuilt ROMs | Never (font rights). |
| AGE + SameSuite as the CGB-E corpus | Mealybug PPU goldens | Mealybug lacks CGB-E expectations. |
| Original MBC3/MBC2 continuation fixtures | Third-party MBC3/MBC2 games | None exist rights-clear (gbclock is the one MBC3 exception). |

## What NOT to Use

| Avoid | Why | Use Instead |
|---|---|---|
| New dependency for PNG, zip, JSON, time or RTC | Violates copy-over-dependency; `zlib` not needed since large ROMs are stored raw | runner-local code, `python3 -I` stdlib at admission |
| Host clock for RTC | Breaks determinism and host independence (project rule) | RTC advanced by the emulated master timeline; seed/offset via explicit API |
| Wall-clock waits for rtc3test (~47 s) | Flaky CI | Headless emulated fast-forward with input script |
| "All SameSuite on all models" | APU pass sets differ by revision | Per-ROM `model_pass` / expected-failure data |
| Auto-downloading corpora in CI | Rights, reproducibility, supply chain | Checked-in bytes + explicit networked `--compare` |
| Trusting Homebrew Hub license metadata | Verified wrong for Tuff | Read the game's repo LICENSE and README assets section |

## Stack Patterns by Variant

**If the acid2/Mealybug font provenance cannot be confirmed:** keep both out of required CI, admit as digest-pinned optional local fixtures, and rely on AGE (CC0 font), SameSuite (X11 repo), MagenTests (MIT) and original rendering fixtures for required CGB rendering evidence. cgb-acid2's reference image is derived from the font, so a font-substituted rebuild cannot reuse it.

**If the loader's maximum ROM size is below 8 MiB:** raise it before admitting `mbc5/rom_64Mb`; do not drop the test, it is the only ninth-bank-bit proof.

## Integration with existing fixture admission

- Layout: `fixtures/<suite>/{manifest.json,LICENSE.txt,SOURCES.md,*.gb|gbc}`; follow `fixtures/mooneye/` for multi-ROM third-party suites (immutable revision + tree SHA, builder pin, source closure, `eligible` plus `excluded_candidates` with reasons, per-ROM SHA-256, finite budget) and `fixtures/mbc1-continuation/` for owned fixtures (manifest keys `cartridge`, `profile`, `protocol`, `scope_limits`).
- Add manifest fields for v0.2: `model_pass`/`model_fail` (parsed from Mooneye headers and README tables), `target_revision` (`CGB-E` or `CGB-0..D`), `oracle` (`fibonacci-ldbb`, `frame-digest@ldbb`, `frame-digest@frame-N`, `screen-text`), `reference_digest` (canonical RGB), `input_script`, `rtc_policy`, and `rights.embedded_assets` (font/logo/include provenance). A missing or empty `rights.embedded_assets` must fail verification.
- Notices: one row per suite in `THIRD_PARTY_NOTICES.md` (rights, manifest digest, ROM digest, notice digest) plus separate lines for CC BY attributions (Tobu Tobu Girl, Dawn Will Come), Apache-2.0 NOTICE (Aevilia), MIT GB Studio engine (gbclock, Dawn Will Come). Third-party licenses go in `fixtures/<suite>/LICENSE.txt` verbatim.
- Verification: extend `cmake/VerifyMooneye.cmake` pattern to a data-driven `VerifySuite.cmake`; extend `tests/expected-tests.txt` so a vanished required fixture fails. Large ROMs are excluded from `install()` lists.
- CI: add legacy-RGBDS rebuild comparisons to `fixture-repro.yml` as hosted, networked, non-required-for-merge-until-proven jobs (same posture as the existing Mooneye leg).

## Version Compatibility

| Fixture | Assembler that works | Notes |
|---|---|---|
| cgb-acid2 v1.1, dmg-acid2 v1.0 (+ mgblib `5d829bf`) | RGBDS 0.4.1, 0.4.2, 0.5.1 (byte-identical); fails 1.0.1 | mgblib HEAD (`d2727ef`, 2026-01-01) targets 0.9.4 and does not reproduce the 2020 bytes. |
| Mealybug `70e88fb` (+ mgblib `1d9045a`) | RGBDS 0.4.2 and 0.5.1 (identical) | Wrong mgblib pin fails on `print_string_literal`. |
| rtc3test v004 | RGBDS 0.4.2 only (0.5.1 fails) | |
| MagenTests 0.5.0 (+ hardware.inc `21ef22d`) | RGBDS 0.6.1 (byte-identical); 0.8.0+ reject `-L`; dropping `-L` on 1.0.1 builds but changes bytes | |
| SameSuite `f15645f` | RGBDS 1.0.1 (all 78 ROMs link) | `rgbfix -jv`. |
| AGE `1f5bc10` | RGBDS 1.0.1 and 0.9.4 identical; 0.6.1 differs | |
| Mooneye `31510e1` | WLA-DX 10.7 / wlalink 5.22 with `-nS` | Default linker order is non-deterministic across libc (qsort comparator), already documented in `fixtures/mooneye/SOURCES.md`. |

## Pitfalls specific to this stack

1. **RTC clock domain.** The MBC3 crystal is the cartridge's own 32.768 kHz oscillator, so CGB double speed must not scale RTC time: model RTC ticks against the master timeline (e.g. 8,388,608 half-dots per RTC second at 2 half-dots per single-speed T-cycle, consistent with the existing half-dot budgets), not against CPU cycles. rtc3test and Mealybug only run single speed, so only the original fixture can catch a double-speed error. (MEDIUM confidence; verify against Pan Docs MBC3 text in the phase.)
2. **Screen-only oracles** (rtc3test, MagenTests, MBC3-style tests) need a defined frame-capture rule (frame N, or stable-frame detection with a bound). Do not invent "looks plausible" passes.
3. **Revision drift.** Using a CGB-C/D golden on a CGB-E profile reports false failures; fixtures must declare `target_revision` and the runner must emit `unsupported-model`, not `fail`.
4. **Bootless CGB.** `boot_regs-cgb`, `boot_div-cgb*`, `key0_lock_after_boot` test boot-ROM-derived state; exclude, and document the synthesized post-boot register/palette state as an explicit profile.
5. **Fixture payload size.** 8 MiB (and 4 MiB) Mooneye MBC5 ROMs: keep in repo only; exclude from installed/packaged fixtures and from the consumer smoke test.

## Appendix: additional full digests captured

- Mealybug (RGBDS 0.4.2 = 0.5.1): `mbc/mbc3_rtc.gb` `6cde433ad6464a553b7bdba77f0f101b447d8c5cfa614302692174415ce77915`; `dma/hdma_timing-C.gb` `8c8762185d63dea950419ced9dbc2a8cc03eccfe448530e5f7157764c7e4f3ec`; `dma/hdma_during_halt-C.gb` `2a55c8730a9e197e16678cd248e9ff00f97e0e89e2206244009ce9f45d007548`; `ppu/m3_bgp_change.gb` `52151476d16b04654123e64bd2c22702571c529761d9c9bc2f485ca2538fc035`.
- SameSuite (RGBDS 1.0.1, macOS arm64, `rgbfix -jv`): `dma/gbc_dma_cont.gb` `cd20f67ff24d4cc90815bdd9b2c41bbeec5ec9a8abedb949f2fc704ff6d61512`; `dma/gdma_addr_mask.gb` `d409c95ddf291c2d9debc0fc3f9bf0d49b24adbcef7f560aa2ae8f6e8299e5f3`; `dma/hdma_lcd_off.gb` `637a3612dcb99bd5f2b0739fb31ad26ce390361e6878b193b894b40f882e44eb`; `dma/hdma_mode0.gb` `53f8d643548cecfc8ba5bd03721e4609571fa6a5ac383c96a2342b058fb5f2a1`.
- MagenTests 0.5.0 release assets: `bg_oam_priority.gbc` `1b2132b354370b1eff22d867da67d8f59eb94872fdad00c277203d8d8b67b84c`; `hblank_vram_dma.gbc` `e8124ce687d37a2402e20af92af1299610bfbda0871d605084c0bba2bf57135c`; `key0_lock_after_boot.gbc` `5f71946a80bb4d52b3e9c88cd8634beac6a490ff78c74c3a28f956b24c0c542c` (excluded); `mbc_oob_sram_mbc1.gbc` `83f1fc44cc26581163b58fe3df426f119dd5813c2e94a187ee0909d6ace1a8bb`; `_mbc3` `03e13fa796a9e06fa90f9b396b728c1de9f6e7351aa47a038e33c11d3a8df7dd`; `_mbc5` `e99f526386f72a8992a72137d0bd9a431b380807b551747bb3baa03421d6f54b`; `oam_internal_priority.gbc` `f54fb6366b3ea8597d07917729aeb358d961ae6ece7cecd003fe9c45dcb97fe7`; `ppu_disabled_state.gbc` `4808fe834ea6a6344d74f007a45628c405aca5acd13d6c25f76d02f442f1eea6`.
- Mooneye derivative (local WLA build, indicative only): `mbc2_bits_ramg 7eb87a09e2214693d978b754957f6dc09f79095fb1bbca7089c9ca7e563115ae`; `mbc2_bits_romb f382f82c0025093b52575bcd35715131b681392f28a81d88180db973b5ff8090`; `mbc2_bits_unused d33bed573c162b3384048dddc10c3b0d0d89dbb9023d1608cd70286988c0fa77`; `mbc2_ram 5b82d04e284a0c396271e4df0d345c7383d1c86467675a272d9a4e286f790f13`; `mbc2_rom_512kb 4c7a8a58e3bf5a45afb71b079aead912f336a13972ff93b59f964bedbc87fda5`; `mbc2_rom_1Mb 7eba692d8f426d1b6187095a9c14a99ef5ea80534d996949bca8bf0bd9e77cc3`; `mbc2_rom_2Mb 32530509d8182718b005e183259cb6eaeeb7db15c6b634ebdc362016591dadec`; `mbc5_rom_8Mb 176cd6f9a16519ba30f7d0cec3d46226ef304f3ad54e41d6d23974a03e6157a1`; `mbc5_rom_64Mb f1148d3cc631e330b991b3f34d728de5b3789b00b80b9778fb08a9bbb59efef7`.
- Reference files: cgb-acid2 `img/reference.png` file `9ea9c262c5383353e77d715d021a0f7c5ccbe438f88082cb225756e50c4fdf01`; dmg-acid2 `img/reference-dmg.png` file `ca966d50895c7efef05838590d148c2cbfd7fba57dab986f25b35b4da71abb57`, `img/reference-cgb.png` file `cbf039fd613a6db3c3d830a6a1d887efbc892aea4578ffc569b61f66a9e07ced`.

## Sources

- Mooneye Test Suite README, LICENSE, `common/common.s` (font attribution), `emulator-only/mbc2|mbc5` sources and harnesses: https://github.com/Gekkio/mooneye-test-suite (pin `31510e1`). Existing local notes: `fixtures/mooneye/SOURCES.md`, `ELIGIBILITY.md`, `FONT-LICENSE.txt`.
- Darkrose 8x8 font page (licenses): https://opengameart.org/content/8x8-ascii-bitmap-font-with-c-source
- cgb-acid2: https://github.com/mattcurrie/cgb-acid2 ; dmg-acid2: https://github.com/mattcurrie/dmg-acid2 ; mgblib: https://github.com/mattcurrie/mgblib ; Mealybug: https://github.com/mattcurrie/mealybug-tearoom-tests
- SameSuite (LICENSE, `apu/README.md`, `include/base.inc`): https://github.com/LIJI32/SameSuite
- AGE test roms: https://github.com/c-sp/age-test-roms ; Cellphone Font (CC0): https://opengameart.org/content/ascii-bitmap-font-cellphone
- MagenTests: https://github.com/alloncm/MagenTests ; gbdev hardware.inc (CC0-1.0): https://github.com/gbdev/hardware.inc
- rtc3test (Unlicense, `tests.md`): https://github.com/aaaaaa123456789/rtc3test ; c-sp aggregator howtos (exit conditions, screenshots, RGBDS 0.4.2 for rtc3test, 47 s of emulated time): https://github.com/c-sp/gameboy-test-roms
- RGBDS releases/tags: https://github.com/gbdev/rgbds ; WLA-DX: https://github.com/vhelin/wla-dx
- GB Homebrew Hub database (per-entry license fields; unreliable, see Tuff): https://github.com/gbdev/database
- Games: https://github.com/SimonLarsen/tobutobugirl , https://github.com/SimonLarsen/tobutobugirl-dx , https://github.com/ISSOtm/Aevilia-GB , https://github.com/statico/gbhack , https://github.com/DevEd2/ReboundGB , https://github.com/drludos/GBcorp , https://github.com/etdv-thevoid/rex-runner-gb , https://github.com/eishiya/DawnWillCome , https://github.com/kresp0/gbclock (itch: https://santiagocrespo.itch.io/the-gbclock) , https://github.com/BonsaiDen/Tuff.gb (rejected)
- GBDK-2020 licensing statement for compiled ROMs: https://github.com/gbdk-2020/gbdk-2020 (LICENSE overview)
