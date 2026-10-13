# Phase 11: CGB Colour Rendering and Player Colour - Research

**Researched:** 2026-10-12
**Domain:** Deterministic C emulator core (Game Boy Color PPU colour path, palette RAM, public RGB555 API) plus an SDL3 host adapter, original RGBDS fixtures, CTest and CMake verifiers
**Confidence:** HIGH for the code map, test infrastructure and primary-source rules; MEDIUM for the MagenTests ROM behaviour on this core (not yet run) and for rebuild reproducibility of the three new third-party ROMs

<user_constraints>
## User Constraints (from CONTEXT.md)

CONTEXT.md carries D-01 to D-44. They are LOCKED. The planner must read `11-CONTEXT.md` `<decisions>` in full; it is not repeated here. The items that most constrain this research, copied verbatim in meaning and wording:

### Locked Decisions (headline set)
- D-01 RGB555 is resolved per dot in `ppu_transfer_dot`, never at frame-copy time. No tuple-carrying FIFO.
- D-02 Dual store: `frame_working`/`frame_completed` stay `uint8_t` shades written only under DMG semantics; add `rgb_working`/`rgb_completed` `uint16_t[GBB_FRAME_PIXELS]` written only on the CGB profile (CGB mode and compat mode). LCD off fills `rgb_working` with `0x7FFF` and leaves `rgb_completed`; frame completion copies working to completed; reset zero-fills both and clears `frame_generation`.
- D-03 `ppu_compose_cgb(...)` is a pure function beside the DMG path. DMG code is not edited except to add model-gate tags.
- D-04 The model check stays a per-dot branch unless the A/B benchmark shows a cost above noise.
- D-05..D-09, D-38..D-40 attributes, LCDC.0 master priority in CGB mode, priority rule, object order latched at boot (OAM index in CGB mode, X-order in compat mode), OPRI has no effect after boot, CGB mode-3 length deferred, window attribute fetch, compat rendering with DMG semantics, VRAM bank 1 post-boot zero.
- D-10..D-14 palette RAM ports, auto-increment, blocked-write increment, lockout predicate `ppu_mode == 3` with LCD on, post-boot CRAM `$7FFF`.
- D-15, D-16, D-17, D-17a, D-18, D-19, D-41, D-42 the public API: `gbb_copy_frame_rgb555` (byte pitch, `GBB_UNSUPPORTED_PROFILE` on DMG), `gbb_copy_frame` keeps `GBB_UNSUPPORTED_PROFILE` on the whole CGB profile, `gbb_compat_palette` and its set/get calls, original default palette, no colour correction, `gbb_frame_info` unchanged.
- D-20..D-25, D-43 oracles and fixtures: AGE has no CGB colour ROM (state the deviation), three MagenTests ROMs, exhaustive priority truth table, `fixtures/cgb-colour/`, acid2 not in repo or required CI, DMG byte-identity at every wave, runner RGB555 digests.
- D-26..D-30, D-44 player: `--model auto|dmg|cgb` default `dmg`, `select_profile` seam, RGBA32 expansion `(c<<3)|(c>>2)`, window title token, no compat-palette flag, CGB smoke on the existing native jobs, claims follow evidence.
- D-31..D-37 process: DEFERRED(11) cells flip in the same plan as their storage, `MODEL:` tags and `docs/model-gates.md` rows, advisory A/B benchmark against `3012e8f`, fuzz additions, wave order, Phase 12 and 13 preparation, SUMMARY `coverage:` schema, zero human UAT.

### Claude's Discretion
- The exact compat ramp values within D-18's rule.
- Internal names (`rgb_working`, `ppu_compose_cgb`, `ppu_compat_resolve`).
- The fixture ROM layout and the frame counts for MagenTests runs.
- Whether the expansion helper is copied or shared.
- Plan granularity within the D-35 waves.

### Deferred Ideas (OUT OF SCOPE)
- Phase 14 or later: CGB mode-3 length, WX and window-range quirks, CRAM lock edge offsets, the PPU-blocked black-pixel quirk, AGE `m3-bg-*` admission.
- Phase 15 or later: flipping the player default to `auto`.
- Future milestone: a player compat-palette flag or presets; optional, labelled colour correction in the player.
- Owner-driven: G1 clearance from the mgblib author (would admit cgb-acid2/dmg-acid2 to required CI).
- Future: `gbb_copy_frame_rgb555` on the DMG profile with a host DMG palette (additive widening).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CGB-04 | CGB software renders with tile attributes, BG/OBJ colour palette RAM (auto-increment, mode-3 lockout) and CGB priority rules, exposed through a new RGB555 frame call; the DMG frame call stays byte-identical | Code map sections A-D (seams in `ppu_transfer_dot`, `io_visibility[]`, `post_boot[]`, `gbb_copy_frame_rgb555`), priority/CRAM semantics verified against Pan Docs and SameBoy, truth-table design, MagenTests predicates, DMG identity gate |
| CGB-05 | DMG software on the CGB profile renders through a fixed, original, documented compatibility palette that a host can override; no boot-ROM palette table | `ppu_compat_resolve` design, `gbb_compat_palette` ABI notes, default-ramp rule and candidate values, doc-mirror test, survives-reset requirement |
| CGB-09 | The SDL3 player runs software as `--model auto|dmg|cgb` with colour presentation and passes an automated CGB smoke | Player code map (argv grammar, three session create sites, texture upload, title, hidden-surface smoke), corrections to D-30's premise, new smoke mode and mutant design, CTest inventory facts |
</phase_requirements>

## Project Constraints (from AGENTS.md)

`./CLAUDE.md` does not exist; `AGENTS.md` is binding. Directives that bind this phase:
- Original portable C core, explicit ownership and error behaviour, bounded public operations, no hidden globals. Host timing, filesystem, UI and audio devices stay in adapters. So: no `getenv`, no static test switches in core production code; mutants are configure-time source copies.
- Prefer small direct code and targeted abstractions; copy small code instead of adding dependencies (owner memory: prefer copy over dependency). No new package, action or toolchain is needed in this phase.
- Evidence before performance complexity; benchmarks record revision, build, hardware, workload, model, output digest, warm-up, samples and uncertainty.
- Guard ROM/save/state boundaries against overflow, truncation and partial mutation; explicit portable serialisation (RGB555 digests are little-endian byte pairs).
- Distinguish hardware-backed tests, differential oracles, metamorphic properties, regression fixtures and private observations; declare applicability and expected-failure reasons.
- No Nintendo boot ROMs, commercial images or unlicensed homebrew; every third-party fixture needs documented redistribution rights and a digest.
- Never put personal home paths, emails or machine identifiers in public artifacts.
- Stop after the phase; do not auto-advance. Every deliverable gets an automated check with a negative control (D-069); write SUMMARY `coverage:` in the GSD block schema (`tests/scripts/verify-summary-coverage.py`, registered `--since 11`).
- Update source, API docs, examples, tests and limitation notes together; keep main releasable.

## Summary

The core already has almost every seam this phase needs, and the DMG path is small enough to leave byte-for-byte untouched. The per-dot pixel write is two lines at the end of `ppu_transfer_dot` (`src/core/gabbaboy.c:2403-2404`); the register table rows for BCPD, OCPD and OPRI are the only `DEFERRED(11)` cells (`:1200,:1202,:1203`); changing their kind in `io_visibility[]` automatically turns the fail-closed read preflight off for them because that preflight is `io_cgb_cell(m, address)->kind != IO_DEFERRED_RW` (`:2024-2026`). The recommended core shape is therefore: leave every DMG function alone, add CGB-mode sibling functions (`ppu_cgb_background`, `ppu_cgb_object`, `ppu_compose_cgb`, `ppu_pixel_cgb`) and a compat sibling (`ppu_pixel_compat` + `ppu_compat_resolve`) that reuse the DMG tile and object helpers unchanged (bank 0, X-order is exactly the compat semantics), and dispatch once per dot in `ppu_transfer_dot`.

Several CONTEXT premises need correction before planning (full list in "Corrections and gaps found in CONTEXT"). The ones that change plan content: (1) the player has no existing RGBA digest and no ROM-path argument, so the CGB smoke is a new smoke mode, and it needs no SDL video driver because hidden smoke renders to an SDL surface through the software renderer; (2) of the six hard-coded `GBB_PROFILE_DMG_CPU_B` sites in `src/player/main.c`, only three are session sites that should route through `select_profile`; (3) the MagenTests ROM `oam_internal_priority` cannot fail the D-21 "X-order ordering in CGB mode" negative control because its two object pairs never share an opaque pixel (verified by simulation below), so that ROM needs a different negative control and ordering stays proved by the truth table; (4) the `window` gating mask `0x21` appears in three shared PPU sites and must become `0x20` in CGB mode, which also touches mode-3 window start timing; (5) fourteen `research:11` model-gate rows are owned by this phase and each needs a disposition.

The three admitted MagenTests ROMs have precise, derivable expected images, so each gets a literal structural predicate in RGB555 (`bg_oam_priority`: eight 8x8 cells at x 32-39, y 16k to 16k+7, cells 0,2,3 are green over blue halves and cells 1,4,5,6,7 are fully green, zero red; `ppu_disabled_state`: all 23040 pixels `0x03E0`; `oam_internal_priority`: 84 opaque pixels, green and red triangles). `bg_oam_priority` toggles LCDC bit 0, bit 1 and bit 3 per object band from STAT/LYC interrupts and writes `WHITE = $FFFF` into palette RAM, so bit 15 must be masked at resolve time. All three ROMs are CGB-flagged (`$143` = `$C0`, `$C0`, `$80`) and have not been run on this core: the plan must treat "passes its structural predicate" as a gate that can fail, with an honest fallback (do not pin a digest, record an expected-unsupported reason) rather than a forced pass.

**Primary recommendation:** Build in D-35 wave order with a mutant harness first; keep DMG functions untouched and add `ppu_cgb_*`/`ppu_compat_*` siblings dispatched once per dot; flip the three `DEFERRED(11)` cells in the same plan as CRAM and OPRI storage; add `gbb_copy_frame_rgb555` by duplicating the validated argument block of `gbb_copy_frame` (do not refactor it); add a new player smoke mode with an RGBA digest and compiled-mutant controls, and keep all `--model` handling in one `select_profile` seam used by the three session create sites.

## Architectural Responsibility Map

This is a library-plus-adapter project, not a web stack. Tiers are mapped to the project's own layers.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Tile attribute fetch, priority composition, CRAM resolve per dot | Core (`src/core/gabbaboy.c`) | - | Per-dot resolution is a locked decision (D-01); only the core sees PPU dot time. |
| Palette RAM ports, lockout, OPRI storage | Core (`io_visibility[]`, `io_read_cgb`, `io_write_cgb`) | Docs mirror + `test_cgb_tables` | Table-driven decode is the Phase 10 single source of truth. |
| RGB555 frame copy, compat palette get/set, argument validation | Core public API (`include/gabbaboy/gabbaboy.h`) | Consumers tests, `docs/native-integration.md` | One-way ABI; validation before any write. |
| RGB555 to RGBA expansion, window title, `--model` parsing, profile selection | Player adapter (`src/player`) | `src/accept` (shared expansion + digest helper) | Host concerns stay out of the core (AGENTS.md). |
| RGB555 frame digests for evidence | `src/accept` (shared with runner and player smoke) | Runner (`src/runner/acceptance.c`) | Explicit serialisation, one canonical header label. |
| Fixture build and rebuild proof | RGBDS fixtures + `tests/scripts/reproduce-*.sh` + `fixture-repro.yml` | CTest digest tests | Existing pattern; no new tooling. |
| DMG byte-identity proof | `tests/scripts/verify-dmg-baseline.sh` + frozen ledger | Flat-reference and tracer digest tests | Existing gate (Phase 10 D-19). |

## Standard Stack

No new libraries. Everything below already exists in the repository or its pinned CI toolchain.

### Core
| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| C17 core, `gbb_instance` calloc'd opaque struct | in-tree | Add `rgb_working`, `rgb_completed`, `bg_cram[64]`, `obj_cram[64]`, `compat_rgb555[3][4]` | Opaque instance means no ABI impact (D-02) [VERIFIED: src/core/gabbaboy.c:322-437, struct is private] |
| CMake + CTest | 4.4.3 local, 3.25.3 floor in CI | Test registration, configure-time mutants | Existing pattern [VERIFIED: cmake --version, CMakePresets.json] |
| RGBDS | v1.0.1 pinned for original fixtures; v0.6.1 pinned for MagenTests | Fixture assembly | Pins already recorded in `fixtures/cgb-banking/manifest.json` and `fixtures/magentests/SOURCES.md` [VERIFIED: files read this session] |
| SDL3 | 3.4.18 exact (`find_package(SDL3 3.4.18 EXACT CONFIG REQUIRED)`) | Player only | Existing [VERIFIED: CMakeLists.txt:87] |
| Python 3 stdlib, run with `-I` | 3.14.4 local | Verifier scripts, optional table generator | Existing [VERIFIED: python3 --version] |

### Supporting
| Component | Purpose | When to Use |
|-----------|---------|-------------|
| `tests/expect_exit.cmake` | Exact-exit-code negative controls | Every mutant and verifier control |
| `cmake/VerifyFixtureManifest.cmake`, `cmake/VerifyDocContract.cmake` | Fixture digest and doc-to-header contract | New fixtures, native guide section |
| `src/accept/sha256.c` and `digest.c` | SHA-256 and canonical digests | New `gbb_accept_rgb555_*` helpers (copy the shape of `gbb_accept_rgb_digest`) |
| `tests/scripts/measure-release-baseline.sh --ab` | A/B receipt | D-33 benchmark |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Duplicating the argument block of `gbb_copy_frame` | A shared static validator | A shared helper edits the DMG function; D-03 and the byte-identity gate prefer the copy. Choose the copy. |
| Parameterising `ppu_tile_color`/`ppu_object_color`/`ppu_background_color` with bank and order arguments | CGB sibling functions | Parameterising edits DMG code (D-03). Choose siblings; reuse the DMG functions unchanged for compat mode. |
| Generating the priority truth table literals with a Python script | Hand-typing about 6000 rows | See Open Question 2. |

**Installation:** none. Reproduction tools are fetched by existing scripts from pinned archives (see Environment Availability).

**Version verification:** not applicable (no registry packages). Toolchain pins verified by reading the manifests.

## Package Legitimacy Audit

No external package is added by this phase (copy over dependency). RGBDS and SDL3 are existing pinned, digest-verified archives, not registry packages.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| none | - | - | - | - | - | No install step; `gsd_run query package-legitimacy check` not applicable |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Corrections and gaps found in CONTEXT (read first)

1. **D-30 premise: there is no existing RGBA digest and no hidden-driver need.** `player_smoke` runs `gabbaboy-player --smoke` and reads ONE rendered pixel (`smoke_read_demo_target_pixel`, `src/player/main.c:842-857`) against a shade. The only digests in the player are the scripted smoke's `rom_sha256` and `pcm_sha256` (`:2231-2233`). Hidden smoke initialises only `SDL_INIT_EVENTS | SDL_INIT_AUDIO` (`:2344-2346`) and renders to an `SDL_CreateSurface` with `SDL_CreateSoftwareRenderer` (`:544-557`), so no SDL video driver or window exists; only `SDL_AUDIO_DRIVER=dummy` matters (as for `player_session_script_no_input`, `tests/player/CMakeLists.txt:109-112`). Plan a new smoke mode with a new RGBA-surface digest. [VERIFIED: src/player/main.c as cited]
2. **D-26 "six hard-coded profile sites" are not six session sites.** `src/player/main.c` lines 150 (authored audio guest), 500 (`create_machine`), 919 (`replace_session_rom`), 1718 (`identify_rom_with_core`), 1964 (`identify_smoke_rom`), 2202 (`run_script_smoke`). Route 500, 919 and 2202 through `select_profile`. Keep 150 (authored DMG audio workload), 1718 and 1964 (battery-identity scratch instances; battery classification is profile independent) as explicit DMG with a comment, so the DMG smokes and Libbet script tests stay byte-identical. [VERIFIED: grep + reads of those sites]
3. **The player has no ROM argument.** Normal mode uses the packaged demo ROM and the Command-O dialog; `main()` rejects unknown arguments (`:2313-2323`). `--model` is therefore a global option parsed before the existing grammar, and `auto` re-probes on every open (`replace_session_rom`) and not at startup alone. A header-only probe needs the ROM bytes before the instance exists; `player_session_replace_rom` reads the file inside itself (`src/player/session.c:221-268`), so add a small `player_session_probe_profile(path, model, &profile, err)` that reuses `read_rom_file` and calls `gbb_probe_rom`. [VERIFIED: session.c:221-268, main.c:2313-2323]
4. **`oam_internal_priority` cannot discriminate object ordering on this core.** Its four objects are at (Y,X,tile) = (40,46,2), (40,40,1), (60,40,1), (60,46,2) with triangle tiles whose opaque columns are 1-6 only. I simulated per-pixel composition in both orders over the ROM's tile data and OAM: the images are identical (84 opaque pixels, x 33-44, y 25-50). So the D-21 negative control "X-order ordering in CGB mode" would not fail this ROM. Give it a different control (for example OBJ palette colours swapped, or the object path forced to the DMG shade path) and keep ordering proved by the truth table. [VERIFIED: scratch simulation this session, source from MagenTests `src/oam_internal_priority/graphics_data.asm` at `3f9c090f`]
5. **Window gating is in three shared sites, not only in `ppu_background_color`.** `ppu_window_visible_at` and `ppu_window_should_start` both test `(m->lcdc & 0x21u) == 0x21u`, and `ppu_pixel_shade` sets `ppu_window_line_drawn` only when `lcdc & 1`. In CGB mode all three must use bit 5 alone (Pan Docs LCDC.0: in CGB mode bit 0 clear only removes priority). Changing `ppu_window_should_start` changes mode-3 window stall timing for CGB mode with LCDC.0 clear; that is consistent with SameBoy (window enable is `GB_LCDC_WIN_ENABLE` alone at `display.c:517,903,1296`) and is part of the D-09 "mode-3 not claimed" disclosure. [VERIFIED: gabbaboy.c:2128-2133, 2242-2254, 2304-2309; CITED: https://gbdev.io/pandocs/LCDC.html]
6. **Compat-mode CRAM post-boot contents are unspecified.** D-14 gives CGB-mode CRAM `$7FFF`; D-17 says compat CRAM "keeps its post-boot contents". Recommend the compat column also `$7FFF`, class POLICY, reason "the compat renderer never reads CRAM and the data ports read $FF in compat mode; deterministic fill only". See Assumptions A2.
7. **Fourteen `research:11` gate rows are owned by Phase 11.** `docs/model-gates.md:47,55,58,59,65,73,88-95` (GATE-02, 10, 13, 14, 20, 28, 43, 44, 45, 46, 47, 48, 49, 50). `docs/model-gates.md` "Release status" says Phase 11 owns the remaining PPU rows. Each needs a disposition (table in Architecture Patterns).
8. **Compat reads of OPRI differ between SameBoy and the Phase 10 table.** SameBoy returns `io_registers[OPRI] | 0xFE` in any CGB model state (`memory.c:631-635`); the Phase 10 compat cell reads `$FF` (hardware test `boot_hwio-C` per CONTEXT). D-08 keeps `$FF`; do not "fix" it toward SameBoy.
9. **Auto-increment index handling.** SameBoy increments the whole stored byte then ORs bit 7 back (`memory.c:1670-1678`). This core stores BCPS with write mask `$BF` and read-OR `$40`, and the CGB post-boot BCPS is `$C0` (auto-increment ON at hand-off, index 0; `post_boot[]` `PB_BCPS` row, `gabbaboy.c:888`). Implement the increment as `0x80 | ((index + 1) & 0x3F)` so no index bit leaks into bit 6. Tests must set BCPS explicitly and never rely on the boot value (it carries `[VERIFY]` per `PB_IDX_VERIFY`).
10. **Bit 15.** MagenTests writes `WHITE = $FFFF` into palette RAM (`src/common.asm`). Store the byte as written (D-11) and mask with `0x7FFF` when resolving, so the RGB555 output always has bit 15 clear (D-15). Pan Docs: bit 15 is "ignored by the rendering process". [CITED: https://gbdev.io/pandocs/Palettes.html]
11. **D-40 is already true in code.** `PB_RAM_FILL` runs `memset(m->vram, v, sizeof(m->vram))` with `v = 0` for all three columns (`gabbaboy.c:1024-1030`, `:894-895`), so VRAM bank 1 is zero after every reset. Add a pin test and the docs sentence; no code change.
12. **MagenTests source directory names.** The release assets are `bg_oam_priority.gbc`, `oam_internal_priority.gbc`, `ppu_disabled_state.gbc`, but the first builds from `src/color_bg_oam_priority`. `tests/scripts/reproduce-magentests.sh` hard-codes three `mbc_oob_sram` ROMs and `self_check` fails unless `len(entries) == 3`; it needs a per-ROM (name, source directory, rgbfix options) table. [VERIFIED: Makefile via gh/WebFetch, script read this session]
13. **`measure_core` is DMG-only with `argc != 3` rejection** (`tests/measure_core.c:~101-107`). A CGB colour workload needs either a profile option added to a copy or a sibling target; the base worktree at `3012e8f` lacks it, so overlay the head's source onto the base build.
14. **The player CTest inventory is separate.** Player tests are listed in `tests/player/expected-tests.txt` and must match `^player_` (`tests/scripts/verify-phase3-player.sh:471`); core tests are in `tests/expected-tests.txt`. D-34's `cgb_`/`palette_` prefixes apply to core tests; player tests use `player_cgb_*`.
15. **`docs/support/unreleased.md` also says "no colour output" (lines 39 and 42)** and is checked by `tests/scripts/verify-support-ledger.py`. Update it with the other docs.

## Code Map (current HEAD `faddcb9`)

All lines below were read this session unless marked `~`.

### A. Public header `include/gabbaboy/gabbaboy.h`

| Anchor | Current | Change |
|---|---|---|
| `:13-16` | `GBB_PROFILE_CGB_CPU_E = 2  /* creatable and probeable; no colour output yet */` | comment only |
| `:128-136` | block comment ends "colour output is not yet available on it" | rewrite |
| `:245-260` | `gbb_copy_frame` comment: "The CGB-CPU-E profile has no colour output yet, so on it a call with valid arguments returns GBB_UNSUPPORTED_PROFILE" | keep the behaviour (D-16), reword to "shades cannot express the BG/OBJ0/OBJ1 split; use `gbb_copy_frame_rgb555`" |
| `:121-126` | `gbb_frame_info` is `{ uint32_t width; uint32_t height; uint64_t generation; uint64_t completion_half_dots; }` | unchanged (D-41); say so in the new comment |
| `:325-337` | `gbb_info` size handshake pattern (`struct_size` in/out, `GBB_INFO_SIZE_V1 28u`) | copy for `gbb_compat_palette` |
| append | after `gbb_get_info` (`:357`) | `gbb_copy_frame_rgb555`, `gbb_compat_palette`, `GBB_COMPAT_PALETTE_SIZE_V1`, `gbb_set_compat_palette`, `gbb_get_compat_palette` |

Verbatim handshake precedent to copy: `_Static_assert(sizeof(gbb_info) == GBB_INFO_SIZE_V1, "gbb_info layout");` at `src/core/gabbaboy.c:318`. `sizeof(gbb_compat_palette)` is 4 + 3*4*2 = 28 on every supported ABI (uint32 then six... twelve uint16 with 4-byte struct alignment), so `GBB_COMPAT_PALETTE_SIZE_V1` is `28u` [ASSUMED: arithmetic, enforce with the static assert].

### B. Core `src/core/gabbaboy.c`

**Instance and storage**

| Anchor | Fact | Seam |
|---|---|---|
| `:9-14` | `#define GBB_FRAME_WIDTH 160u`, `GBB_FRAME_HEIGHT 144u`, `GBB_FRAME_PIXELS (GBB_FRAME_WIDTH * GBB_FRAME_HEIGHT)`, `GBB_VRAM_BANKS 2u`, `GBB_VRAM_BANK_SIZE 8192u` | reuse |
| `:331` | `uint8_t vram[GBB_VRAM_BANKS][GBB_VRAM_BANK_SIZE];` | bank 1 holds BG attributes |
| `:340` | `uint8_t key1_armed, bcps, ocps, ff72, ff73, ff74, ff75;` | `bcps`/`ocps` already stored; add `bg_cram[64]`, `obj_cram[64]`, `opri` bit beside them |
| `:342-344` | `uint8_t frame_working[GBB_FRAME_PIXELS]; uint8_t frame_completed[GBB_FRAME_PIXELS]; uint64_t frame_generation;` | add `uint16_t rgb_working[...]`, `rgb_completed[...]` after them; counters shared |
| `:425-429` | `uint8_t profile; uint8_t exec_mode; ...` | `compat_rgb555[3][4]` goes here (instance config, not in `reset_state`) |

**Post-boot table**

`post_boot_field` enum `:759-775` ends `PB_FF72, PB_FF73, PB_FF74, PB_FF75, PB_RAM_FILL, PB_FIELD_COUNT`; the `_Static_assert(sizeof(post_boot) / sizeof(post_boot[0]) == PB_FIELD_COUNT, ...)` at `:898-899` forces a row per field; `post_boot_apply` `:930-1034` is a switch without `default` so a new field that is not handled is a compiler warning. Existing CRAM-adjacent rows, verbatim: `{ PB_BCPS, PB_NA(0u), PBC_POLICY(0xC0u, PB_IDX_VERIFY), PBK_HWIO(0xC8u) },` and `{ PB_OCPS, PB_NA(0u), PBC_POLICY(0xC0u, PB_IDX_VERIFY), PBK_HWIO(0xD0u) },` (`:888-889`). Add `PB_BG_CRAM_FILL`, `PB_OBJ_CRAM_FILL` (value `0x7FFFu`, fill 32 little-endian words, like `PB_RAM_FILL` at `:1024-1030`) and, if OPRI storage is a table field, `PB_OPRI` (CGB mode 0). `tests/test_cgb_tables.c:31-40` has a positional `field_names[PB_FIELD_COUNT]` array that must grow in the same order, and `docs/cgb-profile.md` rows between `<!-- cgb-post-boot-begin -->` and `<!-- cgb-post-boot-end -->` (`:31`, `:193`) must match; `test_cgb_tables emit` prints the rows.

**Register table and decode**

Verbatim current rows (`:1199-1203`):
```
[0x68] = { IOC(DMG_STOP), IOC_ST(0x40, 0xBF), IOC_ST(0x40, 0xBF), IOS_HW_TEST }, /* BCPS ... */
[0x69] = { IOC(DMG_STOP), IOC_DEF(DEFERRED_RW, 11), IOC(CONST_FF), IOS_PANDOCS }, /* BCPD ... */
[0x6A] = { IOC(DMG_STOP), IOC_ST(0x40, 0xBF), IOC_ST(0x40, 0xBF), IOS_HW_TEST }, /* OCPS ... */
[0x6B] = { IOC(DMG_STOP), IOC_DEF(DEFERRED_RW, 11), IOC(CONST_FF), IOS_PANDOCS }, /* OCPD ... */
[0x6C] = { IOC(DMG_STOP), IOC_DEF(DEFERRED_RW, 11), IOC(CONST_FF), IOS_PANDOCS }, /* OPRI ... */
```
Recommended change: add `IO_BCPD`, `IO_OCPD`, `IO_OPRI` kinds to `io_kind` (`:1060-1071`), set the CGB cell of `[0x69]`, `[0x6B]`, `[0x6C]` to them and leave the DMG and compat cells exactly as above (D-31: compat columns stay). Then:
- `io_read_cgb` (`:1249-1262`) gains three cases; BCPD/OCPD return `cpu_cram_access_allowed(m) ? cram[idx & 0x3F] : 0xFF` and never increment; OPRI returns `(uint8_t)(0xFEu | (m->opri & 1u))`.
- `io_write_cgb` (`:1266-1291`) gains three cases; a BCPD/OCPD write stores the data only when `cpu_cram_access_allowed(m)` and increments `bcps`/`ocps` whenever bit 7 is set, allowed or not (D-11); an OPRI write stores bit 0 only and changes no ordering state (D-08).
- `read_supported` (`:2024-2026`): `return io_cgb_cell(m, address)->kind != IO_DEFERRED_RW;` already allows the new kinds, so DEFERRED reads for these three addresses stop being refused with no edit.
- Define `cpu_cram_access_allowed(const gbb_instance *m)` next to `cpu_vram_access_allowed` (`:1386-1389`, whose body is `return (m->lcdc & 0x80u) == 0 || m->ppu_mode != 3u;`). Separate function, own gate row, class UNKNOWN (D-12).
- `tests/test_cgb_visibility.c` hard-codes the DEFERRED expectation in several places (`:348-349` `deferred_reads` includes `0xFF69, 0xFF6B, 0xFF6C`; `:385` `deferred_writes`; `:397` the compat note; `:697-701` the CGB cells `add_cell(V_CGB, 0xFF69, STOP, 0x5A, STOP, 0xA5, STOP, K_DEF_RW, 11, "D-10 BCPD")` etc.; `:719`). All must be rewritten from the D-10/D-11 decision, not from the code. `docs/cgb-profile.md` rows `:366-377` and the prose at `:200-206` change with them; `test_cgb_tables.c` `render_io` (`:277-303`) needs a rendering string per new kind.

**Reset and LCD-off**
- `reset_state` `:1294-1362`: `post_boot_apply` is called at `:1301` (so table CRAM fills run on every reset and ROM load); frame clears are `:1330-1332`: `memset(m->frame_working, 0, ...)`, `memset(m->frame_completed, 0, ...)`, `m->frame_generation = 0;`. Add the two RGB `memset`s here. `gbb_load_rom` calls `reset_state` after committing `exec_mode` (`:2953-2956`). Therefore `compat_rgb555` must be set in `gbb_create`, never in `reset_state`, or it would not survive reset and load (D-17a).
- LCD-off: `write8` FF40 branch `:1824-1849`, the shade clear is `:1837` `memset(m->frame_working, 0, sizeof(m->frame_working));`. On the CGB profile fill `rgb_working` with `0x7FFFu` in the same branch (D-02) and leave `rgb_completed`.

**PPU pixel path (current structure, DMG semantics)**

| Function | Lines | Role and what the CGB path needs |
|---|---|---|
| `ppu_tile_color` | 2110-2125 | reads `m->vram[0][...]`, tile base `0x1000 + (int8_t)tile*16` unless `lcdc & 0x10` or object. CGB needs a bank argument: write `ppu_cgb_tile_color(m, tile, bank, row, col, object)` and leave this one alone. |
| `ppu_window_visible_at` | 2128-2133 | `(m->lcdc & 0x21u) != 0x21u` early-out. CGB: bit 5 only. |
| `ppu_background_color` | 2136-2156 | returns colour index only; reads tile index from `vram[0][map_address]` at `:2154`. CGB sibling also reads `vram[1][map_address]` for the attribute (same address, D-05), applies X/Y flip and the tile bank. |
| `ppu_scan_object` | 2168-2190 | appends in ascending OAM index into `ppu_selected_*` (10 max), latching `ppu_selected_attributes[slot] = m->oam[offset + 3u]` so bank (bit 3) and palette (bits 0-2) are already available. |
| `ppu_object_color` | 2193-2234 | iterates selected objects in ascending index; chooses by `left < best_left || (left == best_left && index < best_index)` (`:2222`). In CGB mode the first non-transparent candidate in scan order wins (ascending index), so the CGB sibling drops the X comparison. 8x16 masking `tile &= ~1u; tile += row >> 3` (`:2213-2216`) is unchanged. |
| `ppu_palette_shade` | 2237-2239 | `(palette >> (color * 2u)) & 3u` |
| `ppu_pixel_shade` | 2242-2254 | the DMG composition (`background = 0` when `lcdc & 1` is clear; object wins unless `attributes & 0x80` and background non-zero; sets `ppu_window_line_drawn`). Untouched. |
| `ppu_window_should_start` | 2304-2309 | `(m->lcdc & 0x21u) != 0x21u` early-out; shared timing code. CGB: bit 5 only, behind a model branch with a gate row. |
| `ppu_transfer_dot` | 2360-2406 | the write at `:2403-2404`: `m->frame_working[(unsigned)m->ly * GBB_FRAME_WIDTH + fetched_slot] = ppu_pixel_shade(m, fetched_slot);`. This is THE dispatch point. |
| `ppu_advance_dot` | 2409-2456 | frame completion at `:2428-2433`: `memcpy(m->frame_completed, m->frame_working, ...)`, generation increment, `frame_completion_half_dots`. Copy `rgb_working` to `rgb_completed` here on the CGB profile (skip the shade copy there, and the RGB copy on DMG). |

Minimal dispatch (names are discretionary):
```c
const unsigned at = (unsigned)m->ly * GBB_FRAME_WIDTH + fetched_slot;
if (m->profile == GBB_PROFILE_DMG_CPU_B)        m->frame_working[at] = ppu_pixel_shade(m, fetched_slot);
else if (m->exec_mode == GBB_MODE_CGB)           m->rgb_working[at] = ppu_pixel_cgb(m, fetched_slot);
else                                             m->rgb_working[at] = ppu_pixel_compat(m, fetched_slot);
```
The mode predicate must equal `post_boot_column`'s (`:904-908`: DMG profile first, then `exec_mode == GBB_MODE_CGB`, else compat including `GBB_MODE_NONE`). [VERIFIED: file reads]

`ppu_pixel_compat` is the DMG composition with three outputs distinguished: BG via `ppu_background_color`, object via `ppu_object_color` (both unchanged, bank 0, X-order), then `compat_rgb555[0][shade(bgp)]`, `compat_rgb555[1 + ((attr >> 4) & 1)][shade(obp0 or obp1)]`. It must also set `ppu_window_line_drawn` exactly as `ppu_pixel_shade` does. `ppu_compat_resolve(const gbb_instance *m, unsigned set, uint8_t shade)` is a one-line table read (D-17). Per-dot cost on the DMG profile is one profile compare.

**Public frame call**

`gbb_copy_frame` `:2706-2736`. Validation order (copy it exactly for the RGB call): NULL checks `:2709`; `pitch_bytes < GBB_FRAME_WIDTH || pitch_bytes > (SIZE_MAX - GBB_FRAME_WIDTH) / (GBB_FRAME_HEIGHT - 1u)` `:2710-2712`; `required` and capacity `:2713-2714`; the `uintptr_t` overlap block `:2716-2724`; THEN `if (!model_is_dmg(instance)) return GBB_UNSUPPORTED_PROFILE;` `:2726` (tag GATE-57); THEN `if (instance->frame_generation == 0) return GBB_FRAME_NOT_READY;` `:2727`. For `gbb_copy_frame_rgb555`: the same prefix with `GBB_FRAME_WIDTH * 2u` (320) as the minimum pitch and as the row length, `required = 143 * pitch + 320`, plus `((uintptr_t)pixels & 1u) != 0u` and `(pitch_bytes & 1u) != 0u` rejections before the overlap block, then `if (!model_is_cgb(instance)) return GBB_UNSUPPORTED_PROFILE;`, then NOT_READY, then a row `memcpy` from `rgb_completed`. The `memcpy` of uint16 rows into a byte-addressed, 2-byte-aligned destination is native-endian by design (D-15); digests serialise explicitly.

`gbb_create` `:2875-2896` calloc's the instance; set the default compat palette there. `gbb_probe_rom`/`gbb_get_info` write field by field inside the caller's `struct_size` (see `info_store` near `:2960`); copy that discipline for `gbb_get_compat_palette`.

**Test seams** `:3564-3580` (`gbb_test_cpu_snapshot`, `gbb_test_last_unsupported_address`, `gbb_test_bank_state`). White-box tests `#include "../src/core/gabbaboy.c"` and read `m->bg_cram`, `m->frame_working` directly (precedent: `tests/test_cgb_tables.c`, `tests/test_banking_internal.c`), so no new public or extern seam is needed for CRAM or buffer assertions.

### C. Runner and acceptance (D-43)

- `src/runner/acceptance.c:185` `gbb_copy_frame(instance, st->scratch, ...)` in `on_after_step` returns `GBB_UNSUPPORTED_PROFILE` on the CGB profile and the code does `return;` ("no completed frame yet"), so a CGB run would silently observe no frames. Branch on profile there, at `:721` (`copy_latest`) and `:726` (`finish_capture`), digest with a new `gbb_accept_rgb555_digest` (header label distinct from `GBB_ACCEPT_RGB_HEADER "GBB-RGB888-v1 160x144\n"`, for example `"GBB-RGB555LE-v1 160x144\n"`, then little-endian byte pairs per pixel row by row), and print a distinct key (not `frame_hit=`).
- `gbb_accept_write_ppm` (`src/accept/digest.c:56-75`) needs an RGB555 sibling using the shared expansion helper.
- `src/runner/main.c:312-314` Mooneye `observe_case` prints `mooneye.<alias>.frame\tnot-applicable` for non-DMG; leave it (all four CGB Mooneye ROMs are compat-mode `$143 = $00`, verified, and keep their expected stops at `0xFF76`).
- Runner model plumbing already exists: `gbb_runner_profile_for_model`, `run_model`, `run_profile` (`acceptance.c:23-53`). A minimal D-43 evidence case is one `frame-digest@t=` row in a new `tests/acceptance/cases-cgb.txt` or `cases.txt` with `model_pass=cgb-cpu-e` for an original `fixtures/cgb-colour` ROM, plus a control that the same case on `dmg-cpu-b` is excluded (frozen `acceptance_libbet_excluded_cgb-cpu-e` must keep meaning). Do not add new `acceptance.*` keys to the frozen DMG baseline ledger (the comparator reports `extra:`).

### D. Player `src/player`

| Item | Anchor | Note |
|---|---|---|
| Global argv grammar | `main()` `:2272-2323` | Add `--model <v>` extraction before the existing mode detection. Bad value: usage error, exit 2 (D-26). |
| Profile create sites | `:150`, `:500`, `:919`, `:1718`, `:1964`, `:2202` | See Correction 2. |
| Texture | `create_video` `:544-597`: `SDL_CreateTexture(app->renderer, SDL_PIXELFORMAT_RGBA32, SDL_TEXTUREACCESS_STREAMING, 160, 144)` | keep RGBA32 (D-27) |
| Frame upload | `update_frame` `:642-671` | DMG branch untouched; add a CGB branch using a new SDL-free `src/player/colour.c`/`.h` `player_rgb555_to_rgba(...)` so expansion and the independent test oracle can be unit tested and mutated without SDL |
| Title | `format_window_title` `:692-705`, `update_window_title` `:707-712`, initial `SDL_CreateWindow("GabbaBoy — DMG preview", ...)` `:559` | add the mode token from `gbb_get_info` (`GBB_MODE_DMG` -> `DMG`, `GBB_MODE_CGB` -> `CGB`, `GBB_MODE_CGB_DMG_COMPAT` -> `CGB (DMG-compat)`); `run_smoke` asserts title substrings (`:2014-2026`), so existing DMG smoke assertions stay valid if the new token is additive |
| Help text | `print_player_help` `:375-401`, `show_help` `:719-758` ("The APU is a DMG-CPU-B digital model") | update with colour facts (D-44) |
| Limitations | `src/player/limitations.h` (`GBB_PLAYER_LIMITATIONS_TEXT`) pinned verbatim by `tests/player/test_limitations.c` | edit both in one commit |
| Hidden smoke harness | `run_smoke` `:2007-2134`, `smoke_render_next_frame` `:829-840`, `create_video(app, true)`: 320x288 RGBA32 surface, integer logical presentation | reuse; sample the surface after `draw_frame` |
| Existing script smoke | `run_script_smoke` `:2190-2238`, `--smoke-package rom --input-script` | Libbet baseline `$143 = $80` (verified: `xxd` read of `fixtures/libbet/libbet.gb` byte `$143` = `80`) stays on `--model dmg` by default |

New smoke mode proposal: `gabbaboy-player --model cgb --smoke-colour <rom>` (name discretionary): create hidden video, `select_profile`, load the fixture, run N frames, `update_frame` + `draw_frame`, then (a) hash the uploaded RGBA buffer (the 160x144x4 bytes handed to `SDL_UpdateTexture`) with the shared SHA-256, (b) read spot pixels from the rendered surface, (c) count distinct colours, (d) check the title token, and print one `smoke_report`-style line; exit 0 only on all pass, 1 on predicate miss, 2 on bad input (match `run_script_smoke`'s contract at `:2189`). Expected values are computed in the test from the independent expansion formula, never by calling the player's expansion.

## Architecture Patterns

### System Architecture Diagram

```
 guest ROM (CGB mode or compat) --bus writes--> io_write_cgb ----> bcps/ocps, bg_cram/obj_cram, opri
        |  (bus_write advances devices first, so ppu_mode at the write dot is exact)        |
        v                                                                                    |
  advance_devices_to -> ppu_advance_dot -> ppu_transfer_dot (mode 3, one pixel per dot)     |
                                              |                                              |
                          +-------------------+-------------------+                          |
                          | profile == DMG    | exec_mode == CGB  | else (compat)            |
                          v                   v                   v                          |
                  ppu_pixel_shade     ppu_pixel_cgb         ppu_pixel_compat                 |
                  (UNCHANGED)         bg attr(vram[1]) +    DMG composition +                |
                          |           ppu_cgb_object +      compat_rgb555[set][shade] -------+--(instance config,
                          |           ppu_compose_cgb +                                        |  set by host API)
                          |           CRAM resolve (&0x7FFF) <----- live CRAM, this dot -------+
                          v                   |                   |
                  frame_working[]       rgb_working[]       rgb_working[]
                          |                   |                   |
        ly==144: copy -> frame_completed   rgb_completed (shared generation counter)
                          |                   |
         gbb_copy_frame (DMG only)     gbb_copy_frame_rgb555 (CGB profile only, both modes)
                          |                   |
                          v                   v
                 runner digests (RGB888)  runner digests (RGB555 LE) / player (expand to RGBA32 -> SDL texture)
```

### Recommended Project Structure (additions only)
```
src/core/gabbaboy.c                 # CGB siblings, CRAM, dispatch, API (no new file: single-TU core by convention)
include/gabbaboy/gabbaboy.h         # append-only API
src/accept/gbb_accept.h, digest.c   # rgb555 expansion helper + digest + ppm (shared by runner and player)
src/player/colour.c, colour.h       # SDL-free RGB555 -> RGBA32 expansion (testable, mutable)
src/player/main.c, session.c/.h     # --model, select_profile, probe_profile, title, smoke mode
fixtures/cgb-colour/                # original RGBDS 1.0.1 fixtures, manifest.json, LICENSE.txt
fixtures/magentests/                # +3 ROMs, ELIGIBILITY.md/SOURCES.md/manifest.json updated
tests/test_cgb_colour.c             # public-API colour/CRAM/priority-fixture drivers
tests/test_cgb_colour_internal.c    # white-box: truth table, CRAM ports, buffers, mutants (includes the core)
tests/data/cgb-priority-truth.inc   # generated literal rows (see Open Question 2)
tests/scripts/gen-cgb-priority-truth.py
tests/player/test_colour.c          # expansion oracle + mutants + title token
tests/scripts/reproduce-cgb-colour.sh
docs/cgb-profile.md, docs/model-gates.md, docs/native-integration.md, docs/support/unreleased.md
```

### Pattern 1: Table-first, doc-mirrored change (flip a `DEFERRED(11)` cell)
**What:** edit `io_visibility[]`, `io_read_cgb`/`io_write_cgb`, `test_cgb_tables.c` render, `docs/cgb-profile.md` rows and prose, `tests/test_cgb_visibility.c` expectations, and any `deferred_*` arrays in one plan (D-31, V2-20).
**When:** BCPD, OCPD, OPRI.
**Example (verbatim anchors from this session):**
```c
// Source: src/core/gabbaboy.c:1266-1291 (current shape to extend)
static void io_write_cgb(gbb_instance *m, uint16_t address, uint8_t value) {
    if (!model_is_cgb(m)) return;
    const io_cell *c = io_cgb_cell(m, address);
    switch (c->kind) {
    case IO_KEY1: m->key1_armed = (uint8_t)(value & 1u); break;
    ...
    case IO_DEFERRED_RW:
    case IO_DEFERRED_W:
        m->bus_unsupported = 1;
        m->bus_unsupported_address = address;
        break;
    default: break;
    }
}
```

### Pattern 2: Palette data port semantics (D-10, D-11)
```c
/* Source: D-11; SameBoy Core/memory.c:1661-1682; Pan Docs Palettes.html "increment ... even if the write fails" */
static void cram_data_write(uint8_t *index_reg, uint8_t cram[64], uint8_t value, int allowed) {
    const unsigned idx = *index_reg & 0x3Fu;
    if (allowed) cram[idx] = value;                       /* stores all 8 bits; bit 15 masked only at resolve */
    if ((*index_reg & 0x80u) != 0u)                       /* blocked writes still increment */
        *index_reg = (uint8_t)(0x80u | ((idx + 1u) & 0x3Fu));
}
static uint8_t cram_data_read(uint8_t index_reg, const uint8_t cram[64], int allowed) {
    return allowed ? cram[index_reg & 0x3Fu] : 0xFFu;    /* reads never increment */
}
static uint16_t cram_colour(const uint8_t cram[64], unsigned palette, unsigned index) {
    const unsigned at = (palette & 7u) * 8u + (index & 3u) * 2u;
    return (uint16_t)((cram[at] | (cram[at + 1u] << 8)) & 0x7FFFu);
}
```

### Pattern 3: CGB composition as a pure function (D-03, D-07)
```c
/* Source: Pan Docs Tile_Maps.html BG-to-OBJ priority; SameBoy display.c:1277 ("pixel == 0 || !(bg_priority || attr&0x80) || !(LCDC & BG_EN)") */
typedef enum { PPU_WIN_BG = 0, PPU_WIN_OBJ = 1 } ppu_winner;
static ppu_winner ppu_compose_cgb(uint8_t lcdc, uint8_t bg_index, uint8_t bg_attr,
                                  int obj_opaque, uint8_t obj_attr) {
    if (!obj_opaque) return PPU_WIN_BG;                   /* OBJ colour 0 is transparent */
    if (bg_index == 0u) return PPU_WIN_OBJ;               /* rule 1 */
    if ((lcdc & 0x01u) == 0u) return PPU_WIN_OBJ;         /* rule 2: master priority off */
    if (((bg_attr | obj_attr) & 0x80u) == 0u) return PPU_WIN_OBJ; /* rule 3 */
    return PPU_WIN_BG;                                    /* rule 4 */
}
```
Object-versus-object ordering is resolved before this function (first opaque candidate in ascending OAM index) and the winner's OAM bit 7 is what is passed. The BG colour is `cram_colour(bg_cram, bg_attr & 7, bg_index)`, the OBJ colour `cram_colour(obj_cram, obj_attr & 7, obj_index)`.

### Anti-Patterns to Avoid
- **Resolving colour at frame copy or completion.** Breaks per-line palette effects (D-01). The HBlank-per-line fixture and a configure-time mutant guard this.
- **Writing `frame_working` on the CGB profile.** Keep the shade buffer DMG-only (D-02); a white-box test asserts it stays all zero while the CGB profile renders.
- **Reading VBK in the renderer.** The PPU passes an explicit bank (D-05, D-36).
- **A `getenv`, global flag or compile-time macro in production code to inject a mutant.** Use configure-time source copies (precedent `tests/CMakeLists.txt:243-275`).
- **Deriving the truth-table expectation from `ppu_compose_cgb`** (GB-CPU-002).
- **Editing DMG function bodies.** Tag-only edits; siblings for CGB.

### Model-gate dispositions required this phase

Existing rows (`docs/model-gates.md`): proposed outcome. Dispositions that are not decided by CONTEXT are marked as proposals for the planner to confirm (Assumption A3).

| Gate | Site | Proposed disposition |
|---|---|---|
| GATE-43 | `ppu_background_color` | resolved: DMG function becomes `BOTH basis=...`; the new CGB sibling carries `CGB_ONLY GUARD=model_is_cgb` with prose "LCDC bit 0 is master priority in CGB mode" |
| GATE-45 | `ppu_object_color` | resolved the same way; ordering mode is OAM index in CGB mode, X in compat (D-08) |
| GATE-46 | `ppu_pixel_shade` | resolved: DMG-only function, new CGB/compat siblings have their own rows |
| GATE-28 | `write8` FF40 | split: the bit-0 meaning part is resolved, LCD on/off timing stays `UNKNOWN research:14` |
| GATE-02, 10, 13, 14, 20, 44, 47, 48, 49, 50 | STAT line, post-boot PPU mode, VRAM/OAM lock windows, STAT transitions, OAM scan during DMA, fetcher timing, object fetch, mode-3 startup and window stall, line length | D-09/D-12 defer CGB mode-3, lock-edge and timing accuracy: re-tag `UNKNOWN research:14` (or `expected-failure:` with a reason) and update the "Release status" paragraph so no row still names phase 11 |
| new | `cpu_cram_access_allowed` | `UNKNOWN research:14` (D-12: plain `ppu_mode == 3` predicate, edges not asserted) |
| new | dispatch in `ppu_transfer_dot`; `ppu_pixel_cgb`; `ppu_pixel_compat`; `ppu_compat_resolve`; `ppu_window_should_start` CGB branch; `gbb_copy_frame_rgb555` | `CGB_ONLY GUARD=model_is_cgb` (the guard token must appear within 12 code lines of the tag, rule R4); the next free id is GATE-76 (highest present in code is GATE-75) |

The scanner requires every new top-level function to carry a `MODEL:` tag (R1), tag and doc row bijection by id (R2), and its self-test counts functions, so add rows and tags in the same commit.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Doc-to-code table agreement | greps | extend `tests/test_cgb_tables.c` with a `compat_palette` mode and new field names, mutated-doc copies written at configure time | Phase 10 pattern, already has selftests |
| Prose-to-API agreement | manual review | `cmake/VerifyDocContract.cmake` via `cgb_native_guide_contract` (phrases at `tests/CMakeLists.txt:1538-1545`) | Any `gbb_`/`GBB_` token in the guide must be a real header declaration |
| Fixture digest | new hash script | `cmake/VerifyFixtureManifest.cmake` (as `cgb_banking_fixture_digest`, `magentests_fixture_digest`) | Existing |
| Core mutants | runtime switches | the configure-time anchored text replacement in `gbb_banking_mutant` (`tests/CMakeLists.txt:243-275`) | Exactly-once anchor discipline |
| Frame digest and PPM | ad hoc loops | new `gbb_accept_rgb555_*` beside `gbb_accept_rgb_digest` | Explicit little-endian serialisation, one label |
| 5-to-8 bit expansion | per-host copies | one tiny shared helper `(c << 3) | (c >> 2)` in `src/accept` (player adapter already links `gabbaboy_accept`, `CMakeLists.txt:98`) | Both hosts agree (D-27) |
| A/B timing | new harness | `tests/scripts/measure-release-baseline.sh --ab` | Receipt self-tests exist (`cgb_bench_ab_*`, `tests/CMakeLists.txt:1843-1875`) |
| SHA-256 | external tool in tests | `src/accept/sha256.c` | Already linked |

**Key insight:** every verifier this phase needs already exists in a Phase 10 shape; the work is extending tables and registering new names, not inventing machinery.

## Runtime State Inventory

Not a rename or migration phase: omitted. (No stored data, live service config, OS-registered state or secrets are renamed. New persistent state is limited to checked-in fixtures and docs.)

## Common Pitfalls

### Pitfall 1: bit 15 leaks into the output
**What goes wrong:** `WHITE = $FFFF` written by a guest produces `0xFFFF` pixels; the D-15 contract says bit 15 is always 0, digests change, expansion indexes out of range in hosts.
**How to avoid:** mask in `cram_colour` (`& 0x7FFF`); fuzz and truth tests assert `(pixel & 0x8000) == 0` for every pixel; keep storing the raw byte so a future read-back policy stays a local change.
**Warning signs:** a pixel above `0x7FFF` in any copy.

### Pitfall 2: the window silently disappears when LCDC.0 is clear in CGB mode
**What goes wrong:** `ppu_window_visible_at` and `ppu_window_should_start` keep their `0x21` mask, so `bg_oam_priority` bands with LCDC.0 clear lose window logic or mode-3 timing shifts.
**How to avoid:** CGB-mode siblings and a model branch in `ppu_window_should_start`; a truth-table row with LCDC.0 = 0 and the window enabled must still draw the window.

### Pitfall 3: auto-increment and the stored bit 6
**What goes wrong:** incrementing the stored byte with `++` carries index 63 into bit 6 and leaves a stale bit; or a post-boot `$C0` is assumed to mean "no auto-increment".
**How to avoid:** `0x80 | ((idx + 1) & 0x3F)`; guests set BCPS/OCPS before BCPD/OCPD; tests assert wrap 63 to 0 with bit 7 kept.

### Pitfall 4: the lockout is evaluated at the wrong time
**What goes wrong:** a CRAM write is judged against PPU state before the bus advanced devices to the write timestamp.
**How to avoid:** `bus_write`/`bus_read` call `advance_devices_to(...)` first (`gabbaboy.c:1621-1626` for read), so `m->ppu_mode` is current when `io_*_cgb` runs; do not cache mode. Test with a guest that writes during mode 3 and mode 0 on the same line.

### Pitfall 5: the DMG path moves
**What goes wrong:** an "obvious" parameterisation of `ppu_tile_color` or a shared copy validator changes DMG codegen or ordering; baseline digests drift.
**How to avoid:** siblings only; run the baseline (`tests/scripts/verify-dmg-baseline.sh`), `banking_tracer_digest_unchanged` (`correctness_digest_fnv1a64=4c7a57ff3d50d228`) and the flat-memory reference at every wave (D-25). Include a mutant whose CGB colour path writes `frame_working` and prove it fails.

### Pitfall 6: `compat_rgb555` lost on reset or load
`gbb_load_rom` calls `reset_state` (`:2953-2956`); anything initialised there is wiped. Initialise in `gbb_create`, test "set, reset, load, get" returns the override.

### Pitfall 7: first-frame content
`rgb_working` zero-fill (D-02 reset policy) is black while the LCD-off fill is white. The completed buffer is never exposed before the first completed frame (generation 0 returns `GBB_FRAME_NOT_READY`), and the first frame rewrites every visible pixel, so this is invisible; add a test that the first completed frame after reset has no pixel left at the reset value on a solid-colour fixture.

### Pitfall 8: MagenTests ROMs do not pass on this core
They are CGB-flagged ROMs written against hardware and SameBoy, run here for the first time. `bg_oam_priority` depends on STAT/LYC interrupt timing and LCDC writes landing before x = 32 of each band (dispatch plus handler is about 48 dots into the line by my estimate, while pixel x = 32 is output no earlier than about dot 124; this estimate is [ASSUMED], not measured). **How to avoid:** make the structural predicate the gate; if a ROM fails it, investigate the core, and only then fall back to an `expected-unsupported`-style record with a named reason. Never pin a digest of an output that failed the predicate (D-21).

### Pitfall 9: player `--model` leaks into DMG smokes
`--model` default is `dmg`; DMG smokes (`player_smoke`, `player_session_script_*`, Libbet `$143 = $80`) must not change digests. The 150/1718/1964 sites stay explicit DMG.

### Pitfall 10: test inventory equality
`gabbaboy_verify_registered_tests()` (last line of `tests/CMakeLists.txt`) and `tests/player/CMakeLists.txt:231-237` both fail configure if a registered name is missing from its inventory file, or vice versa. Add names in the same commit; player names need the `player_` prefix.

### Pitfall 11: doc contract identifiers
Every `gbb_`/`GBB_` token in `docs/native-integration.md` must be declared in `include/gabbaboy/gabbaboy.h` or `examples/relocated-c/CMakeLists.txt` (`GBB_NATIVE_GUIDE_CGB_DECLS`). Keep the existing phrase `returns \`GBB_UNSUPPORTED_PROFILE\` on the CGB profile` (it is in `GBB_NATIVE_GUIDE_CGB_PHRASES`, `tests/CMakeLists.txt:1538-1545`); rewrite the sentence at `docs/native-integration.md:132-133` so the phrase survives while "until colour output exists" goes away.

### Pitfall 12: fixture and ROM line endings
New `.gb`/`.gbc` files and manifests need `.gitattributes` entries (`fixtures/cgb-banking/*.gb -text` and `manifest.json text eol=lf` are the precedent, `.gitattributes:56-60`). `fixtures/magentests` currently has no `.gitattributes` line (grep returned none); check whether the existing `.gbc` files are protected another way before adding six.

## Code Examples

### Independent expansion oracle for tests (D-19, D-27)
```c
/* The formula in the AGE README and D-19. Tests compute expectations with this and never call the player's helper. */
static uint8_t expand5(unsigned c) { return (uint8_t)((c << 3) | (c >> 2)); }
/* RGB555 value v: R = v & 31, G = (v >> 5) & 31, B = (v >> 10) & 31 -> RGBA32 bytes {expand5(R), expand5(G), expand5(B), 255} */
```

### Default compat ramp, rule and candidate values (Claude's discretion, D-18)
Rule (documented in `docs/cgb-profile.md`): a four-step luminance ramp `Y = 31, 21, 11, 1`; `R = Y`, `G = Y - (Y >> 3)`, `B = Y - (Y >> 2)`; identical for BG, OBJ0, OBJ1. Computed in this session: step 0 (31,28,24) = `$639F`; step 1 (21,19,16) = `$4275`; step 2 (11,10,9) = `$254B`; step 3 (1,1,1) = `$0421`. [ASSUMED: aesthetic acceptability is the owner veto item 3; arithmetic VERIFIED by script this session]. The values were authored from the rule above with no reference to a third-party table; the docs and commit must say so (G4).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| CGB peers resolve per range or at write time (mGBA draws per range, SameBoy mixes against a write-time table) | This core resolves per dot against live CRAM | D-01 | Per-line palette effects correct by construction; copy-time resolve is the wrong design |
| OPRI as a live priority switch | Stored bit with no effect after boot | D-08 (SameBoy `memory.c:1437-1446`: write only changes `object_priority` while the boot ROM is running or KEY0 bit 3 is set) | Local, reversible |
| Colour correction in cores | None in v0.2; hosts expand `(c<<3)|(c>>2)` | D-19 | Player help says so (V2-29) |

**Deprecated/outdated:** nothing is removed. The CONTEXT phrase "AGE/MagenTests CGB PPU ROMs" in the roadmap criterion is superseded by D-20 (AGE has none; confirmed by listing `age-test-roms` tree `1f5bc10e`: only `m3-bg-lcdc` and `m3-bg-scx` images exist, both mode-3 timing tests).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The default compat ramp values `$639F`, `$4275`, `$254B`, `$0421` are acceptable to the owner | Code Examples | Owner veto item 3; values are a one-line table change plus doc and test pin |
| A2 | Compat-column post-boot CRAM should be `$7FFF` (POLICY) because the compat renderer never reads CRAM and compat data ports read `$FF` | Corrections 6 | Another value only changes an unobservable fill and the doc row |
| A3 | The ten timing-related `research:11` gate rows should be re-tagged `research:14` (Phase 14) and the bit-0 meaning split out of GATE-28 | Model-gate dispositions | Owner may prefer `expected-failure:` reasons; scanner accepts either |
| A4 | The three MagenTests ROMs, built by upstream from the pinned source, match the release assets and rebuild byte-identically under RGBDS 0.6.1 with the Makefile flags | MagenTests | Rebuild proof fails in `fixture-repro`; report `result=differs`, never replace committed bytes (existing doctrine) |
| A5 | `bg_oam_priority`'s per-band LCDC writes land before pixel x = 32 on this core's DMG timing | Pitfall 8 | The predicate fails; investigate core timing or fall back; D-09 already disclaims CGB mode-3 accuracy |
| A6 | `sizeof(gbb_compat_palette) == 28` on all supported ABIs | Code map A | Static assert fails at compile time on a surprising ABI; adjust struct padding explicitly |
| A7 | SDL 3.4.18's software renderer reproduces exact RGBA values for nearest-neighbour integer upscales of an RGBA32 texture, so spot-pixel and surface checks are exact | Player | Existing `verify_software_layout` already checks exact red/black pixels at four sizes (`main.c:1608-1711`), so risk is low; digest the pre-upload RGBA buffer as the primary evidence |
| A8 | The SHA-256 digests of the three new ROMs below, taken from the 0.5.0 release assets, are the digests the fixture-repro job will see | MagenTests | Re-download in a fresh scratch directory at plan time and re-check (GitHub shows no asset digest, so provenance is this download) |

## Open Questions

1. **Compat CRAM post-boot value and the `opri` post-boot row.**
   - What we know: D-14 covers CGB mode only; CGB-mode OPRI reads `$FE | bit0` (D-08); Pan Docs says the boot ROM writes `$01` to OPRI in compatibility mode and lists no CGB-mode OPRI value.
   - What's unclear: whether OPRI needs a `post_boot[]` row (recommended: yes, CGB 0, POLICY with reason "boot ROM leaves priority by OAM index; no hardware oracle", compat n/a because compat reads `$FF`).
   - Recommendation: add rows `bg_cram`, `obj_cram`, `opri`; planner confirms A2.
2. **D-22 "literal rows ... never derived from `ppu_compose_cgb`" versus a table of about 6000 rows.**
   - What we know: the full product is {mode 2} x {LCDC.0 2} x {BG attr bit 7 2} x {BG index 4} x {object A: opaque index 4 x OAM bit 7 2} x {object B likewise} x {X relation of A to B: less, equal, greater} (about 6000 rows if both objects always overlap the pixel).
   - Recommendation: commit a generated `tests/data/cgb-priority-truth.inc` produced by a stdlib Python script that encodes the Pan Docs rules independently (a different language from the implementation), with a CTest that regenerates it and compares bytes, an asserted row count equal to the product, and a small hand-written golden subset quoting the four Pan Docs rules. This keeps rows literal in the C test, independent of the core, and mutation-checked.
3. **Ldbb register predicate versus WRAM markers for D-23 item 3.** CONTEXT says "checked by an `ld b,b` register predicate". The proven public-API pattern is WRAM result markers read with `gbb_peek_ram` after a halt (`cgb_banking_guest_*`, `fixtures/cgb-banking/manifest.json` `protocol`). Recommendation: use markers for the CRAM semantic fixture and a runner `frame-digest@t=` case for D-43; use an `ld b,b` predicate only if the planner wants a runner-level acceptance case for the CRAM cell.
4. **Where the three new player behaviours' tests register.** `tests/player/CMakeLists.txt` dispatches by `elseif(test_name MATCHES ...)`; a new `player_cgb_*` regex branch plus names in `tests/player/expected-tests.txt` is required, otherwise the file ends in `FATAL_ERROR "Unknown optional player test in inventory"`.
5. **Does the owner want the `compat` run of `ppu_disabled_state` (header byte patched to `$00` in memory) as an extra control?** Cheap and exercises the compat palette (expected all pixels equal `compat_rgb555[0][0]`). Recommended, not required.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| cmake | build, tests | yes | 4.4.3 (CI floor 3.25.3 job exists) | - |
| Apple clang / ninja | build | yes (Phase 10 research recorded clang 21) | - | CI covers GCC/MSVC |
| python3 | verifiers, table generator | yes | 3.14.4 | - |
| rgbasm/rgblink/rgbfix | fixture builds | installed v1.0.4, not the pinned versions | 1.0.4 | download the pinned v1.0.1 (original fixtures) and v0.6.1 (MagenTests) archives to a temp directory outside the repo and prepend `PATH`, as the reproduce scripts require (`tests/scripts/reproduce-cgb-banking.sh` rejects any other version) |
| SDL3 | player build and smoke | libSDL3 present under the local Homebrew prefix; project pins 3.4.18 EXACT and builds it in `tests/scripts/verify-phase3-player.sh` | - | the pinned-source build in that script |
| git worktree + commit `3012e8f` | D-33 A/B base | yes (`git cat-file -t 3012e8f` = commit) | - | - |
| gh CLI | MagenTests asset download | yes | - | curl the release URLs |
| valgrind, libFuzzer | not required | - | - | ASan/UBSan preset `phase1-asan`; deterministic fuzz regressions |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** pinned RGBDS 1.0.1 and 0.6.1 (scripted fetch).

## MagenTests details (D-21)

Upstream pin: `https://github.com/alloncm/MagenTests` tag `0.5.0` = commit `3f9c090f16e5a721db776febb9ba7d773e1c819c` (verified: `git rev-parse 0.5.0^{commit}` in a scratch clone equals the existing pin). Licence MIT, `Copyright (c) 2022 alloncm` (the existing `fixtures/magentests/LICENSE.txt` and the upstream `LICENSE` first lines agree). `hardware.inc` is the pinned gbdev submodule `21ef22d` (CC0) per the existing `SOURCES.md`.

Release assets (GitHub API `releases/tags/0.5.0`): `bg_oam_priority.gbc`, `hblank_vram_dma.gbc`, `key0_lock_after_boot.gbc`, `mbc_oob_sram_mbc1.gbc`, `mbc_oob_sram_mbc3.gbc`, `mbc_oob_sram_mbc5.gbc`, `oam_internal_priority.gbc`, `ppu_disabled_state.gbc`, each 32768 bytes. GitHub exposes no asset digest, so the SHA-256 values below come from a download into a fresh scratch directory this session:

| ROM | Size | SHA-256 | `$143` | Source dir (Makefile) | rgbfix options |
|---|---|---|---|---|---|
| `bg_oam_priority.gbc` | 32768 | `1b2132b354370b1eff22d867da67d8f59eb94872fdad00c277203d8d8b67b84c` | `$C0` | `src/color_bg_oam_priority` | `--color-only --mbc-type ROM` |
| `oam_internal_priority.gbc` | 32768 | `f54fb6366b3ea8597d07917729aeb358d961ae6ece7cecd003fe9c45dcb97fe7` | `$C0` | `src/oam_internal_priority` | `--color-only --mbc-type ROM` |
| `ppu_disabled_state.gbc` | 32768 | `4808fe834ea6a6344d74f007a45628c405aca5acd13d6c25f76d02f442f1eea6` | `$80` | `src/ppu_disabled_state` | `--color-compatible --mbc-type ROM` |

Rebuild recipe (extend `tests/scripts/reproduce-magentests.sh`): `rgbasm -L -i src/<dir> -i hardware.inc/ -o build/<name>.o src/<dir>/main.asm; rgblink -o build/<name>.gbc build/<name>.o; rgbfix -v -p 0 <options> build/<name>.gbc`. The existing script's `self_check` demands exactly three fixtures and lists the three `mbc_oob_sram` names; both must become a table (A4).

Rights: MIT with notice retained; each ROM keeps its ELIGIBILITY label from D-21 and the manifest records `source_dir`, `rgbfix_options` and `$143`. No acid2 bytes; no `hblank_vram_dma` (Phase 13) or `key0_lock_after_boot`.

Expected images and structural predicates (all derived from the pinned sources read this session; values are RGB555 after bit-15 masking):

- **`bg_oam_priority`** (`src/color_bg_oam_priority`, `common.asm`: `WHITE EQU $FFFF`, `RED EQU $001F`, `GREEN EQU $03E0`, `BLUE EQU $7C00`). Expected: eight 8x8 cells at x 32..39 and y `16k .. 16k+7` for k = 0..7. Cells k = 0, 2, 3: rows 0-3 of the cell `0x03E0`, rows 4-7 `0x7C00`. Cells k = 1, 4, 5, 6, 7: all 64 pixels `0x03E0`. Zero pixels equal `0x001F`. All other pixels `0x7FFF`. Derivation (index 0 and 1 of BG palette 1 are blue; objects 1,4,5,6,7 use the all-colour-1 tile and win on every band because either BG attribute bit 7, OAM bit 7 or LCDC.0 is clear; objects 0,2,3 use the half-green half-red tile and BG wins on the colour-1 rows because OAM bit 7, BG attribute bit 7 and LCDC.0 are all set where required). Stimulus requires per-band LCDC writes from STAT/LYC interrupts (LYC = 16k, bit 6 of STAT) with LCDC values `%10011011, %10011010, %10010011, %10011011, %10010011, %10010010, %10011010, %10010010` in band order. Negative control: invert LCDC.0 handling in `ppu_compose_cgb` (a configure-time mutant), expected to turn at least one blue half into red or green.
- **`oam_internal_priority`**: 84 opaque pixels (x 33..44; y 25..30 and 45..50 per my simulation, tile rows 1-6 of two objects at Y = 40 and Y = 60), green `0x03E0` (colour index 1, tile 1) and red `0x001F` (colour index 2, tile 2), everything else `0x7FFF`. Not sensitive to object ordering (Correction 4). Negative control must be something the ROM can detect: for example force the object colour lookup to the wrong palette or route CGB-mode objects through the DMG shade path; the test seam is a configure-time mutant of the core. Label: SameBoy differential, not hardware (D-21).
- **`ppu_disabled_state`**: all 23040 pixels `0x03E0`; failure paints all pixels `0x001F`. Needs STAT mode 0 with the LCD off (core returns `m->ppu_mode`, which `ppu_set_mode(m, 0)` sets at LCD off, `gabbaboy.c:1831`). Negative control: a mutant that does not set mode 0 on LCD off (expected all `0x001F`). Extra control: the same ROM with `$143` patched to `$00` and re-checksummed runs in compat mode and must produce uniform `compat_rgb555[0][0]` (Open Question 5).

Frame counts: each ROM needs at least one frame to reach vblank for `TurnOffLcd` before it sets up, so run a fixed 20 frames (3 s of emulated time is not needed; 20 x 140448 half-dots) and assert the last two completed frames are byte-identical before checking the predicate (D-21 "wide margin"). Use the `FRAME_HALF_DOTS 140448` slicing in `tests/test_magentests.c:15-19` (it runs `gbb_run` per frame and accepts `GBB_STOP_BUDGET` or `GBB_STOP_HALTED_IDLE`). `bg_oam_priority` never halts (it spins in `jp .loop` with `ei`), so it returns `GBB_STOP_BUDGET`.

The existing MagenTests tests stay on the DMG profile and are unaffected; new cases run on the CGB profile through `gbb_copy_frame_rgb555`. The redistribution guard `magentests_not_installed` scans installed trees by digest list from the manifest (`tests/CMakeLists.txt:1210-1233`), so the new files are covered when the manifest grows.

## Validation Architecture

Nyquist validation is enabled (`.planning/config.json` `workflow.nyquist_validation: true`).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | CTest over C executables with `REQUIRE` macros and TAP-ish output; CMake `-P` verifiers; stdlib Python verifiers with `--self-test`; configure-time core mutants |
| Config file | `CMakePresets.json` presets `phase1`, `phase1-asan`, `cmake-3.25.3`; `.planning/config.json` `workflow.test_command` = `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` |
| Quick run command | `ctest --preset phase1 -R '^(cgb_|palette_|magentests_cgb|cgb_visibility_|cgb_tables_)'` |
| Full suite command | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` then `bash tests/scripts/verify-dmg-baseline.sh`; ASan: `cmake --preset phase1-asan` for core waves; player: `bash tests/scripts/verify-phase3-player.sh --build-package` (runs `ctest -R '^player_'`) |

### Phase Requirements to Test Map

Names are proposals; core names must be added to `tests/expected-tests.txt`, player names to `tests/player/expected-tests.txt`.

| Req / Decision | Behaviour | Test Type | Automated Command | File Exists? | Negative control |
|---|---|---|---|---|---|
| CGB-04 / D-10, D-11 | BCPS/OCPS index, auto-increment, 6-bit wrap (63 to 0, bit 7 kept), read-back, blocked write drops data but increments, blocked read `$FF`, reads never increment, LCD off clears lockout | white-box unit | `ctest -R '^palette_cram_'` | Wave 0 | mutant: no increment on blocked write; mutant: increment on read; mutant: lockout ignores LCD-off |
| CGB-04 / D-12 | `ppu_mode == 3` predicate at the write dot, separate function and gate | unit with a guest writing on both sides of mode 3 | `ctest -R '^palette_cram_lockout'` | Wave 0 | lockout predicate returning always-allowed |
| CGB-04 / D-08 | OPRI read `$FE|bit0`; write has no priority effect; compat reads `$FF` and ignores writes | unit | `ctest -R '^palette_opri_'` | Wave 0 | in CGB mode writing 1 must leave order unchanged; mutant making it live must fail |
| CGB-04 / D-31 | three DEFERRED(11) cells flipped, table, doc and independent visibility table agree | unit + CMake | `ctest -R '^cgb_(visibility|tables)_'` | exists, rewrite | mutated doc copy; existing selftests |
| CGB-04 / D-05, D-38, D-39 | each BG attribute bit (palette, bank, X flip, Y flip, priority), bit 4 ignored, window uses same fetch; OBJ bank and palette; compat ignores attributes | fixture + white-box | `ctest -R '^cgb_attr_'` and `'^cgb_colour_guest_'` | Wave 0 | mutants: ignore bank, swap flips, read VBK instead of explicit bank |
| CGB-04 / D-06 | LCDC.0 = 0: BG still drawn and OBJ always wins in CGB mode; DMG and compat keep BG enable | white-box truth rows | part of `cgb_priority_*` | Wave 0 | inverted LCDC.0 mutant |
| CGB-04 / D-07, D-22 | exhaustive priority truth table; row count equals product; each input mutated breaks a row | white-box | `ctest -R '^cgb_priority_'` | Wave 0 | per-input mutants (BG attr bit 7, OAM bit 7, LCDC.0, index 0 rule, object order) |
| CGB-04 / D-02, D-25 | `frame_working` untouched on CGB, `rgb_*` untouched on DMG; DMG baseline recompute identical | white-box + baseline | `ctest -R '^cgb_dmg_identity'`; `bash tests/scripts/verify-dmg-baseline.sh` | Wave 0 / exists | mutant whose colour path writes `frame_working` |
| CGB-04 / D-01, D-23.4 | per-line HBlank colour change visible row by row; digest pinned | fixture | `ctest -R '^cgb_colour_hblank_rows'` | Wave 0 | configure-time mutant resolving at frame completion must exit 1 |
| CGB-04 / D-15 | argument matrix: NULL, misaligned pointer, odd pitch, pitch below 320, capacity below `143*pitch+320`, overflow, overlap with `out_info`, DMG profile `GBB_UNSUPPORTED_PROFILE`, `GBB_FRAME_NOT_READY` only after valid args, no mutation on any error (sentinel fill), reset invalidates, both modes serve | unit | `ctest -R '^cgb_rgb555_'` | Wave 0 | skewed validator (profile check before argument check) |
| CGB-04 / D-02 | LCD-off frame is `0x7FFF`, completed frame retained; reset zero-fills and clears generation | unit | `ctest -R '^cgb_rgb555_lcd_off'` | Wave 0 | mutant filling 0 |
| CGB-04 / D-14, D-40 | post-boot CRAM `$7FFF` (both banks of colours), VRAM bank 1 zero after reset | white-box + `cgb_tables_postboot` | `ctest -R '^cgb_postboot_'` | exists, extend | flipped cell control exists (`--flip`) |
| CGB-04 / D-21 | three MagenTests ROMs satisfy their structural predicates; last two frames identical; digests pinned only after the predicate passes | third-party fixture | `ctest -R '^magentests_cgb_'` | Wave 0 | per-ROM mutant (see MagenTests details) |
| CGB-05 / D-17, D-17a | `gbb_set/get_compat_palette`: NULL restores default, `struct_size` below V1 rejected, larger accepted with extra bytes ignored, bit 15 rejected (not masked), whole struct validated before mutation, survives reset and ROM load, accepted on both profiles | unit | `ctest -R '^palette_compat_api'` | Wave 0 | mutant masking bit 15 instead of rejecting |
| CGB-05 / D-39 | BGP/OBP0/OBP1 select shade, palette set chosen by OAM bit 4, override takes effect from the next dot only, completed frame not recoloured | fixture + white-box | `ctest -R '^palette_compat_mapping'` | Wave 0 | mutant using the BG set for objects |
| CGB-05 / D-18 | default 12 values equal the doc block and the rule | CMake/white-box | `ctest -R '^cgb_tables_compat_palette'` | Wave 0 | mutated doc copy |
| CGB-05 / D-42 | docs and ABI agree (new symbols declared, phrases kept) | doc contract + consumers | `ctest -R '^cgb_native_guide_contract'`; `installed_consumer_c`, `installed_consumer_cpp` call every new symbol | exists, extend | missing-phrase selftest exists |
| CGB-09 / D-26 | `--model` parsing: `auto|dmg|cgb`, bad value exit 2, PGB header error non-zero, re-probe on open, probe failure leaves session intact | player unit | `ctest -R '^player_cgb_model'` | Wave 0 | mutant `select_profile` ignoring the flag |
| CGB-09 / D-27, D-28 | expansion `(c<<3)|(c>>2)` on a table of RGB555 values vs an independent formula; title token from `gbb_get_info` | player unit | `ctest -R '^player_cgb_(expand|title)'` | Wave 0 | compiled mutants: R/B swapped, grey path |
| CGB-09 / D-30 | new smoke: RGBA digest, distinct-colour count, spot pixels, title token on a `fixtures/cgb-colour` ROM with dummy audio | player e2e | `ctest -R '^player_cgb_smoke$'` (via the player job) | Wave 0 | smoke run against mutated builds must exit non-zero (`player_cgb_smoke_mutant_*`) |
| CGB-09 / D-44 | limitation text, README, `--help`, preview `capability_limits` agree | unit | `ctest -R '^player_limitations'` | exists, edit | text pinned verbatim |
| D-34 | palette-register sequences, LCD toggles, `gbb_set_compat_palette` struct inputs under ASan/UBSan; invariant: no output pixel has bit 15 | fuzz | `ctest -R '^cgb_fuzz_'` and the `phase1-asan` run | exists, extend | seed that breaks the invariant in a mutant |
| D-33 | A/B receipt (DMG tracer digest `4c7a57ff3d50d228` on both builds; CGB colour workload recorded separately; advisory) | script | `ctest -R '^cgb_bench_ab_'` plus a recorded `11-BENCH.md` | exists | wrong-digest and missing-field controls exist |
| D-32 | `MODEL:` tags and rows in agreement; research:11 rows disposed | script | `ctest -R '^model_gates'` | exists | scanner mutants exist |
| D-37 | SUMMARY `coverage:` accepted by the classifier | script | `ctest -R '^summary_coverage'` | exists | selftest mutants exist |

### Sampling Rate
- **Per task commit:** the narrow `ctest -R` for the touched area, plus `bash tests/scripts/verify-dmg-baseline.sh` after any task that edits `src/core/gabbaboy.c`, `src/runner/*` or `src/accept/*`.
- **Per wave merge:** full `phase1` suite, then `phase1-asan` for core-touching waves, then the baseline; the player job locally before Wave 5 merges.
- **Phase gate:** full suite green on all legs at the exact PR head (macOS, Linux, Windows, ASan, CMake floor, macOS player package), `result=byte-identical` from `fixture-repro` read at the evidence head, `11-BENCH.md` recorded, `/gsd-verify-work` with zero human items.

### Wave 0 Gaps
- [ ] `tests/test_cgb_colour_internal.c` (white-box: CRAM ports, buffers, truth table, mutant harness) and `tests/test_cgb_colour.c` (public API, fixtures)
- [ ] `tests/data/cgb-priority-truth.inc` and its generator with a regenerate-and-compare test
- [ ] `fixtures/cgb-colour/` (source, ROMs, manifest, LICENSE) and `tests/scripts/reproduce-cgb-colour.sh`; `fixture-repro.yml` step and pin-consistency block entry
- [ ] extend `fixtures/magentests/` (+3 ROMs, manifest, SOURCES.md, ELIGIBILITY.md, `.gitattributes`) and `tests/test_magentests.c` cases
- [ ] `tests/player/test_colour.c`, `src/player/colour.[ch]`, `player_cgb_*` registrations
- [ ] `gbb_accept_rgb555_*` helpers and tests in `tests/test_acceptance_digest.c`
- [ ] extend `tests/measure_core.c` (or add a sibling target) with a CGB workload for D-33
- [ ] framework install: none

## Security Domain

`security_enforcement` is enabled (`security_asvs_level: 1`, `security_block_on: high`).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | no identities |
| V3 Session Management | no | none |
| V4 Access Control | no | none |
| V5 Input Validation | yes | validate every public input before any write: `gbb_copy_frame_rgb555` (NULL, alignment, even pitch, minimum pitch, capacity arithmetic with overflow guards, overlap with `out_info`), `gbb_set/get_compat_palette` (`struct_size`, bit 15, NULL), CRAM index masked with `& 0x3F` and palette/colour indices masked before indexing the 64-byte arrays, `--model` token validation, header probe bounded by the existing ROM size ceiling; fuzz under ASan/UBSan |
| V6 Cryptography | no | SHA-256 only for fixture and frame digests (existing `sha256.c`) |
| V12 Files and resources | yes (CI) | fixture reproduction runs downloaded archives only in temp directories outside the repo (existing `outside_repo` guards); run any Python that reads downloaded data with `-I` |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Out-of-bounds CRAM index from guest writes to BCPS/OCPS | Tampering | index masked to 6 bits at every use; fuzz random FF68-FF6B writes on the CGB profile |
| Misaligned `uint16_t *` or oversize pitch in the new frame call | Tampering / DoS | reject odd addresses and pitches, checked arithmetic before any write, no allocation |
| Partial mutation on a rejected palette set | Tampering | validate all 12 entries and `struct_size` first, then copy |
| Information in receipts and docs (home paths, machine ids) | Information disclosure | repo-relative paths; bench receipts record hardware class only |
| New third-party ROMs without rights record | Legal | MIT notice, digest, `ELIGIBILITY.md`, scan guard `magentests_not_installed` |
| Player `--model` or ROM path abuse | Tampering | closed set of values, bad value exit 2, existing bounded ROM read (`PLAYER_SESSION_MAX_ROM_SIZE`) |

## Recommended plan/wave split (sized for executor context)

`gabbaboy.c` is about 3800 lines (about 40K tokens): give each plan an explicit line-range reading list. Waves follow D-35. Parallelism notes: fixtures (Wave 3b) and player work (Wave 5) can start once the public API is frozen at the end of Wave 4; every plan serialises on `tests/CMakeLists.txt`, `tests/expected-tests.txt` and `gabbaboy.c`, so append new tests in a delimited block per plan.

| Wave | Plan | Scope (files) | Notes |
|---|---|---|---|
| 1 | 11-01 | Baseline recompute record; configure-time mutant harness (new `gbb_colour_mutant` function modelled on `gbb_banking_mutant`) and the "colour path writes the DMG shade buffer" mutant; `tests/test_cgb_colour_internal.c` skeleton | Test-first; mutant harness is the DMG identity guard for all later waves |
| 2 | 11-02 | CRAM storage (`bg_cram`, `obj_cram`), `post_boot[]` rows + `field_names[]` + docs mirror, `cpu_cram_access_allowed`, BCPD/OCPD kinds and ports, OPRI storage, flip the three DEFERRED(11) cells, rewrite `test_cgb_visibility` and docs rows, `palette_*` tests, gate rows | One plan: cells flip with their storage (D-31) |
| 3 | 11-03 | `ppu_cgb_*` siblings, attribute fetch with explicit bank, window mask branch, `ppu_compose_cgb`, dispatch writing `rgb_working` (not yet public), truth table (generator + `.inc` + tests + per-input mutants), gate rows for the 11 `research:11` dispositions | Largest core plan |
| 3 | 11-04 | `fixtures/cgb-colour/` sources, ROMs, manifest, reproduce script, fixture-repro step, `cgb_colour_guest_*` markers tests; HBlank-rows fixture needs the RGB555 call, so its test lands in 11-06 | Needs pinned RGBDS 1.0.1 (scripted) |
| 4 | 11-05 | `rgb_*` buffers, LCD-off and reset and completion handling, `gbb_copy_frame_rgb555` (+header, comments), `compat_rgb555`, `ppu_pixel_compat`/`ppu_compat_resolve`, `gbb_set/get_compat_palette`, default ramp + doc mirror test | Public ABI freeze point |
| 4 | 11-06 | `src/accept` RGB555 digest/PPM helper, runner CGB frame branch (D-43), `fixtures/cgb-colour` frame tests incl. HBlank rows and the copy-time mutant, MagenTests CGB ROMs (admit, manifest, ELIGIBILITY, SOURCES, repro table, tests, mutants) | MagenTests contingency decision lands here |
| 5 | 11-07 | Player: `colour.[ch]`, `--model`, `select_profile`, `player_session_probe_profile`, title token, `update_frame` CGB branch, help and limitation text, new smoke mode, `player_cgb_*` tests and compiled mutants | Run `verify-phase3-player.sh` locally |
| 6 | 11-08 | Docs (`cgb-profile.md`, `model-gates.md`, `native-integration.md`, `support/unreleased.md`, README, preview.yml `capability_limits`), consumers (`tests/consumers/c|cpp` replace the "no colour output" comment and add rgb555 and compat calls), fuzz extension, model-gate audit, A/B benchmark and `11-BENCH.md`, final DMG identity check, LESSONS entry | Close-out; no new core features |

## Sources

### Primary (HIGH confidence)
- Repository files read this session (line anchors cited inline): `include/gabbaboy/gabbaboy.h` (all); `src/core/gabbaboy.c` (1-130, 296-445, 720-1034, 1036-1362, 1380-1395, 1580-1626, 1730-2010 selectively, 2100-2490, 2640-2740, 2860-2975, 3555-3600); `src/player/main.c` (20-200, 370-840, 820-960, 1580-1800, 1940-2000, 2005-2134, 2180-2486); `src/player/session.c` (160-290), `session.h` (60-135), `limitations.h`, `presentation.[ch]`; `src/accept/gbb_accept.h` (180-263), `digest.c` (1-75), `predicate.c` (1-60); `src/runner/acceptance.c` (23-53, 160-215, 700-735, grep of all profile sites), `src/runner/main.c` (grep + 105-135, 308-324); `tests/CMakeLists.txt` (195-275, 670-710, 1525-1600, 1765-1779, 1843-1875), `tests/player/CMakeLists.txt` (all), `tests/player/expected-tests.txt`, `tests/test_magentests.c`, `tests/measure_core.c`, `tests/fuzz_core.c` (190-264), `tests/test_cgb_tables.c` (1-60, grep), `tests/scripts/reproduce-magentests.sh`, `reproduce-cgb-banking.sh`, `verify-phase3-player.sh` (425-475), `verify-dmg-baseline.sh`, `verify-summary-coverage.py`; `docs/cgb-profile.md`, `docs/model-gates.md`, `docs/native-integration.md`; `fixtures/cgb-banking/*`, `fixtures/magentests/*`, `fixtures/mooneye-cgb/manifest.json`; `.planning/phases/GB-10-*/10-PATTERNS.md`, `10-RESEARCH.md` (592-839), `10-BENCH.md`; `.planning/phases/GB-11-*/11-CONTEXT.md`.
- Pan Docs, fetched this session: Palettes (CRAM layout, RGB555, bit 15 ignored, blocked write still increments, reads never increment), LCDC (LCDC.0 non-CGB vs CGB, LCDC.5), OAM (attribute bits, CGB priority by OAM position, 8x16), Tile_Maps (BG attributes, four BG-to-OBJ rules), Power_Up_Sequence (boot ROM fades BG palettes to white, compatibility palette steps, OPRI `$01` in compat mode). https://gbdev.io/pandocs/
- SameBoy master `Core/memory.c` and `Core/display.c` downloaded to scratch this session: `memory.c:625-640, 685-720, 1430-1445, 1655-1700`; `display.c:120-150, 655-775, 1180-1235, 1277, 1296`. Oracle only; no code copied.
- MagenTests `3f9c090f`: Makefile, README, `src/common.asm`, `src/color_bg_oam_priority`, `src/oam_internal_priority`, `src/ppu_disabled_state` sources and the release asset list for tag `0.5.0` (via `gh api` and a scratch clone); release ROMs downloaded and hashed in a scratch directory.
- AGE test ROMs `1f5bc10e`: tree listing via `gh api` confirms no CGB colour, attribute or priority ROM.

### Secondary (MEDIUM confidence)
- Scratch simulation of `oam_internal_priority` composition (not committed): tile and OAM data transcribed from the pinned source, both orderings produce identical images.

### Tertiary (LOW confidence)
- The dispatch-timing estimate for `bg_oam_priority` band writes (A5), and the aesthetic of the default ramp (A1).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new components; all pins read from manifests.
- Architecture (code map and seams): HIGH - read from the current source with line anchors.
- Pitfalls: HIGH for the code and test-infrastructure pitfalls; MEDIUM for MagenTests behaviour on this core.
- Rule semantics (priority, CRAM, OPRI): HIGH - Pan Docs and SameBoy agree; hardware verification is not claimed (SameBoy is an oracle, not hardware).

**Research date:** 2026-10-12
**Valid until:** 2026-11-11 (30 days; repository state at `faddcb9` is the reference, Pan Docs and SameBoy move slowly)
