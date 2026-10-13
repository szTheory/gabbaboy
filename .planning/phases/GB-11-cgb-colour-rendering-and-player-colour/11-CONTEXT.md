# Phase 11: CGB Colour Rendering and Player Colour - Context

**Gathered:** 2026-10-12
**Status:** Ready for planning
**Method:** Advisor fan-out with auto-follow, per the owner's standing instruction (re-pasted during this discussion). Seven researchers ran in parallel, each with an adversarial pass:
- PPU rendering, priority and OPRI
- palette RAM semantics
- the RGB555 API and compat palette
- oracles and fixtures
- the player and CGB smoke
- a gap sweep
- cross-emulator pixel-pipeline architecture

A separate adversarial reviewer then checked the synthesised draft against the repo, Pan Docs and SameBoy source. It amended D-02, D-08, D-15, D-17, D-23 and D-26, and added D-38 to D-44. Its key claims were re-verified locally: `fixtures/libbet/libbet.gb` has `$143 = $80`; LCD off clears only `frame_working` (`src/core/gabbaboy.c:1837`); reset clears both buffers (`:1330-1332`); OPRI is `DEFERRED(11)` (`:1203`).

Primary sources read:
- Pan Docs: Palettes, Tile_Maps, OAM, LCDC, CGB_Registers, Power_Up_Sequence.
- SameBoy `Core/display.c` and `Core/memory.c` (master, `c4cf7abab79a` for display.c).
- mGBA `src/gb/renderers/software.c` (`143adf5aa2a6`).
- AGE test ROMs at `1f5bc10e` (README, Makefile, `m3-bg-*` sources and PNGs).
- MagenTests at `3f9c090f` (README, Makefile, `src/*/main.asm`).

Gambatte and ares were not read; they are comparison-only and nothing depends on them.

Reconciliation rule, as in Phase 10: hardware tests beat Pan Docs prose, which beats a single emulator. Where evidence runs out, the tie goes to DMG byte-identity and fail-closed honesty. Owner veto points are listed at the end.

<domain>
## Phase Boundary

Phase 11 delivers:
- **CGB-mode colour rendering:** BG/window tile attributes from VRAM bank 1, OBJ bank and palette attributes, BG/OBJ colour palette RAM (auto-increment, mode-3 lockout) and CGB priority rules.
- **The new call `gbb_copy_frame_rgb555`.**
- **DMG-compatibility rendering on the CGB profile:** a fixed, original, documented compat palette that the host can override.
- **The SDL3 player:** `--model auto|dmg|cgb`, colour presentation, and an automated CGB smoke in CI.

`gbb_copy_frame` stays byte-identical for DMG.

Not in this phase:
- Double speed (Phase 12).
- HDMA/GDMA (Phase 13).
- CGB-E qualification and corpus expansion (Phase 14).
- CGB acceptance and release (Phase 15).
- CGB mode-3 length and WX quirks (D-09).
- Colour correction.
- A player palette flag.
- Save states.

</domain>

<decisions>
## Implementation Decisions

### A. Pixel path and frame storage

- **D-01: RGB555 is resolved per dot** in `ppu_transfer_dot`, at the point where `ppu_pixel_shade` now resolves a DMG shade, against live CRAM.
  - Never defer resolution to frame-copy time. A copy-time resolve breaks per-scanline palette effects, and no peer does it (SameBoy mixes against a write-time table; mGBA draws per range).
  - Add no tuple-carrying FIFO.
- **D-02: Dual store.**
  - `frame_working`/`frame_completed` stay `uint8_t` shades, written only under DMG semantics, byte-identical.
  - Add `rgb_working`/`rgb_completed` `uint16_t[GBB_FRAME_PIXELS]` (2 x 45 KiB). They are written only on the CGB profile, in both CGB mode and compat mode.
  - They mirror the DMG policy exactly:
    - LCD off fills `rgb_working` with `0x7FFF` (white, consistent with DMG shade 0 being lightest; SameBoy `display.c` renders a disabled CGB LCD as `0x7FFF`) and leaves `rgb_completed`.
    - Frame completion copies working to completed.
    - Reset zero-fills both and clears `frame_generation`.
  - `gbb_instance` is opaque (calloc'd), so there is no ABI impact.
  - Frame generation and completion counters are shared by both copy calls.
  - **Reversibility:** reversible.
- **D-03: Priority composition is a pure function** `ppu_compose_cgb(...)` beside the DMG path. DMG code is not edited except to add model-gate tags.
- **D-04: The model check stays a per-dot branch.** Hoist it to a per-line flag or function pointer only if the Phase 11 A/B benchmark shows a cost above the noise floor (AGENTS.md: evidence before performance complexity).

### B. CGB-mode attributes and priority

- **D-05: Attributes.**
  - BG/window map attributes are read from `vram[1]` at the same map address as the tile index:
    - bits 0-2: palette
    - bit 3: tile-data bank
    - bit 5: X flip
    - bit 6: Y flip
    - bit 7: BG-to-OBJ priority
    - bit 4: ignored
  - Rendering never reads VBK. The PPU uses a VRAM accessor with an explicit bank argument, replacing Phase 10 D-14's `vram[0]`, which is also what HDMA will need.
  - OBJ: OAM bit 3 is the tile bank and bits 0-2 the palette. 8x16 tile masking is unchanged.
- **D-06: LCDC.0 in CGB mode is master priority, not BG enable.**
  - When it is clear, BG and window still draw and objects always win.
  - The existing DMG `background = 0` behaviour is gated on DMG semantics (DMG profile or compat mode) and must not run in CGB mode.
  - The truth table includes LCDC.0=0 rows asserting that BG is still drawn.
- **D-07: Priority rule.**
  - OBJ colour 0 is transparent.
  - Object-vs-object ordering is resolved first. Then the winning object's OAM bit 7 is tested.
  - OBJ is drawn unless LCDC.0=1, (OAM bit 7 or BG attr bit 7) is set, and the BG colour index is 1-3 (Pan Docs Tile_Maps/OAM).
- **D-08: Object ordering is a mode field latched at boot, not live OPRI.**
  - CGB mode orders by OAM index. Compat mode orders by X, lower OAM index on ties.
  - OPRI in CGB mode:
    - A write stores bit 0. The read is `$FE | bit0`. There is no effect on priority.
    - This matches SameBoy `memory.c`, which stores the register but leaves `object_priority` alone after boot, and Pan Docs: "no effect, at least not an instant effect … after the boot ROM has been unmapped", TO BE VERIFIED.
    - Provenance is ORACLE_SAMEBOY + PANDOCS, with the tag UNKNOWN.
  - OPRI in compat mode: reads `$FF` and ignores writes (Phase 10 table).
  - Negative control: in CGB mode, writing 1 to OPRI leaves the priority order unchanged.
  - **Reversibility:** reversible. Ordering is one mode field; making OPRI live later is a local change.
- **D-09: CGB mode-3 length, WX and window-range differences are deferred.**
  - DMG mode-3 timing applies on CGB, tagged UNKNOWN. GabbaBoy does not claim CGB mode-3 accuracy.
  - AGE `m3-bg-lcdc`/`m3-bg-scx` (`-cgbBCE`, `-ds-cgbBCE`, `-nocgb-ncmBCE`) are expected-unsupported with the reason `mode-3-pixel-timing`.
  - Mealybug `m3_*` stays `unsupported-model`.
- **D-38 (window): window tiles use the same attribute fetch as BG,** with the window map and the window line counter unchanged.

### C. Compat mode (DMG software on the CGB profile)

- **D-39: Compat rendering uses DMG semantics.**
  - The BG attribute is treated as 0, with no `vram[1]` map read: tile bank 0 and BG palette 0.
  - OBJ selects OBJ0/OBJ1 by OAM bit 4. OAM bit 3 and bits 0-2 are ignored.
  - LCDC.0 is BG enable. Ordering is by X (D-08).
  - BGP/OBP0/OBP1 select the shade index, which picks the colour from the compat palette (Pan Docs Power_Up_Sequence "Compatibility palettes" structure, not its values).
  - OBJ size and 8x16 behaviour are unchanged.
- **D-17: Compat colours come from instance configuration** `compat_rgb555[3][4]` (BG, OBJ0, OBJ1), read at resolve time by a new `ppu_compat_resolve(...)`, separate from `ppu_pixel_shade` (the DMG function is untouched).
  - CRAM in compat mode keeps its post-boot contents and is never rewritten by the host.
  - A set takes effect from the next dot and never recolours an already-completed frame. Both points are documented.
- **D-18: Default compat palette.**
  - An original, neutral, slightly warm 4-step ramp, identical for BG, OBJ0 and OBJ1.
  - Generated by a documented rule. The 12 RGB555 values are listed in `docs/cgb-profile.md` and pinned by a test.
  - Excluded sources (rights gate G4): the title-hash table, boot-ROM values, peer emulator values, and near-copies of the well-known DMG greens or Pocket greys.
  - The docs and commit carry a note that the values were authored here without reference to a third-party table.

### D. Palette RAM (CGB mode)

- **D-10: BCPS/OCPS (FF68/FF6A).**
  - Bits 0-5 are the index and bit 7 auto-increment. Bit 6 reads 1, with the provenance the Phase 10 table already has (HW_TEST/ORACLE, not Pan Docs).
  - Always accessible in every PPU mode.
  - Stored and writable in compat mode too (already the case since Phase 10, `gabbaboy.c:1199-1201`, `:1237-1238`).
- **D-11: BCPD/OCPD (FF69/FF6B) data ports.**
  - A write stores the byte at `index & 0x3F`. If bit 7 is set the index increments with a 6-bit wrap (63 to 0) and bit 7 is kept.
  - A blocked write (mode 3) drops the data but still increments when bit 7 is set. This is Pan Docs, explicit, and SameBoy `memory.c`. It is the roadmap DEEP item, resolved.
  - A read returns the byte, or `$FF` when blocked. Reads never increment.
  - CRAM stores all 8 bits per byte. Colour words use bits 0-14 and the unused bit 15 is stored as written, which is [VERIFY].
- **D-12: Lockout predicate.**
  - The CRAM lockout is a plain `ppu_mode == 3` predicate with the LCD on. It is the same notion as `cpu_vram_access_allowed` (`gabbaboy.c:1386-1389`) but a separate function and model gate, tagged UNKNOWN.
  - SameBoy's earlier-block and later-release edges (`display.c` ~1707, 1820-1842, 2113) are recorded as UNKNOWN and not asserted.
  - LCD off clears the lockout.
  - SameBoy's black-pixel-while-PPU-blocked behaviour is explicitly not modelled.
- **D-13: In compat mode the BCPD/OCPD data ports read `$FF`** and writes are ignored with no increment. This is unchanged from Phase 10.
- **D-14: Post-boot CGB-mode CRAM.**
  - All BG colours are `$7FFF` (PAN_DOCS: the boot ROM initialises all BG colours to white).
  - All OBJ colours are `$7FFF` (POLICY; Pan Docs calls OBJ CRAM uninitialised).
  - Both get rows in the `post_boot[]` table and the docs mirror.
- **D-40: VRAM bank 1 post-boot fill is zero** (POLICY, V2-07). Name it in `docs/cgb-profile.md` before any attribute test relies on it. Never assert uninitialised CRAM or VRAM against another emulator's value.

### E. Public API

- **D-15: `gbb_copy_frame_rgb555`.**

  ```c
  gbb_error gbb_copy_frame_rgb555(const gbb_instance *instance, uint16_t *pixels,
                                  size_t capacity_bytes, size_t pitch_bytes,
                                  gbb_frame_info *out_info);
  ```

  - Pitch and capacity are in **bytes**, matching `gbb_copy_frame`, SDL and libretro.
  - Before any profile check, return `GBB_INVALID_ARGUMENT` if any of these fails:
    - `pixels` is 2-byte aligned;
    - `pitch_bytes` is even and at least 320;
    - `capacity_bytes >= 143*pitch_bytes + 320`, with the checked arithmetic of `gabbaboy.c:2705-2718`;
    - the destination does not overlap `out_info`.
  - Values are native-endian `uint16_t` `R | G<<5 | B<<10`, with bit 15 always 0.
  - Same rules as `gbb_copy_frame`: no allocation, validation before any write, no mutation on error, `GBB_FRAME_NOT_READY` only after the arguments are valid, and reset invalidates the frame.
  - Serves the CGB profile in both CGB and compat modes. Returns `GBB_UNSUPPORTED_PROFILE` on the DMG profile, symmetric with D-16; widening later is additive.
  - Every digest, fixture and doc serialises RGB555 explicitly as little-endian byte pairs, never by `memcpy` of the host layout.
  - **Reversibility:** one-way. It is a published ABI signature; changing pitch units or the value layout after release breaks consumers.
- **D-16: `gbb_copy_frame` keeps `GBB_UNSUPPORTED_PROFILE` on the whole CGB profile,** compat mode included. Shades cannot express the BG/OBJ0/OBJ1 palette split, and one rule keeps the contract simple. Update the header comments that say "no colour output yet" (`gabbaboy.h:15`, `:246-248`).
- **D-17a: The compat palette API.**

  ```c
  typedef struct gbb_compat_palette {
      uint32_t struct_size;   /* sizeof; handshake as gbb_info */
      uint16_t bg[4], obj0[4], obj1[4];
  } gbb_compat_palette;
  #define GBB_COMPAT_PALETTE_SIZE_V1 /* static_assert against sizeof */
  gbb_error gbb_set_compat_palette(gbb_instance *instance, const gbb_compat_palette *palette); /* NULL restores the default */
  gbb_error gbb_get_compat_palette(const gbb_instance *instance, gbb_compat_palette *out);
  ```

  - Validate the whole struct before mutating anything: `struct_size >= V1` (larger is accepted, extra bytes ignored, as in the `gbb_info` handshake at `gabbaboy.h:326-355`). An entry with bit 15 set is **rejected**, not masked.
  - Accepted on both profiles. It has a visible effect only in compat mode.
  - It is instance configuration: it survives reset and ROM load, and it is not emulation state.
  - No new error codes.
  - **Reversibility:** one-way. It is a published struct and functions; V2 may only append fields.
- **D-19: The core does no colour correction.** Hosts expand each channel with `(c<<3)|(c>>2)`, matching the AGE README. Colour correction is "none in v0.2", stated in the player help (V2-29).
- **D-41: `gbb_frame_info` is unchanged** and reused by both calls; the header says so.
- **D-42: ABI and docs move together.**
  - Update the header comments, the api-coverage and consumer inventory tests (pin every new symbol), `docs/model-gates.md`, `docs/cgb-profile.md`, and `docs/native-integration.md` (a new RGB555 and compat-palette section).
  - Changes are append-only. No existing struct changes layout.

### F. Oracles and fixtures

- **D-20: AGE has no CGB colour, attribute or priority ROM.**
  - Its only CGB-mode image tests are `m3-bg-lcdc` and `m3-bg-scx`, which are expected-unsupported (D-09).
  - Success criterion 1's "AGE/MagenTests" is met by MagenTests plus original fixtures plus the truth table.
  - The plan and VERIFICATION must state this deviation explicitly rather than imply AGE coverage.
- **D-21: Admitted MagenTests ROMs,** vendored into `fixtures/magentests/` with ELIGIBILITY.md, SOURCES.md, manifest digests and licence rows (MIT; legacy RGBDS 0.6.1 reproduction like the existing `mbc_oob_sram_*`):

  | ROM | Applicability label |
  |---|---|
  | `bg_oam_priority` | CGB hardware photo, revision E unattested |
  | `oam_internal_priority` | SameBoy differential, not hardware |
  | `ppu_disabled_state` | author-attested |

  - They do not signal completion with `ld b,b`. Each runs a fixed frame count with a wide margin and asserts the last 2 frames are identical.
  - Each must pass a structural predicate before a digest pin is accepted, for example zero red pixels and five green plus three half-green/half-blue cells for `bg_oam_priority`.
  - Each has a negative control through a test-only seam: inverted LCDC.0, X-order ordering in CGB mode, or failing to leave mode 0 after LCD off.
  - Skip `key0_lock_after_boot`. `hblank_vram_dma` belongs to Phase 13.
- **D-22: Exhaustive priority truth table** over {mode CGB/compat, LCDC.0, BG attr bit 7, OAM bit 7, BG index 0-3, up to two overlapping objects each with index 0-3 and an order}.
  - The expected values are written independently from the Pan Docs text, as literal rows in the test, never derived from `ppu_compose_cgb` (GB-CPU-002).
  - The test asserts the row count equals the full product.
  - Each input, mutated, must break at least one row.
- **D-23: Original fixtures `fixtures/cgb-colour/`** (RGBDS 1.0.1, MIT, digest, rebuilt byte-identically in fixture-repro, same layout as `fixtures/cgb-banking/`):
  1. Each BG attribute bit (palette, bank, X flip, Y flip, priority).
  2. OBJ bank and palette.
  3. CRAM auto-increment, wrap, read-back and blocked-write increment, checked by an `ld b,b` register predicate.
  4. **The resolve-time negative control:** BG colour 0 is changed to a distinct RGB555 value on each line 0-143 during HBlank. The test asserts each row's colour through `gbb_copy_frame_rgb555` plus a digest. A test-only seam mutant that resolves from CRAM at frame completion must fail it.
  5. The compat mapping (BGP/OBP0/OBP1 into the compat palette, including an override).
  6. LCDC.0 = 0 with BG still drawn.
  7. LCD-off white frame.
- **D-24: cgb-acid2 and dmg-acid2 add no bytes to the repo or to required CI** while rights gate G1 (mgblib font) is open. An optional local runner takes `--rom` plus a manifest-pinned SHA-256 and compares against the upstream reference under the AGE expansion.
- **D-25: The DMG byte-identity gate (Phase 10 D-19) runs at every wave:** baseline recompute, existing suites unchanged, the flat-memory reference, and fuzz bank asserts. A mutant whose colour path writes the DMG shade buffer must fail.
- **D-43: Runner and acceptance support for RGB555.**
  - The runner's `--profile cgb` frame cases digest little-endian RGB555 bytes under a distinct digest label.
  - The DMG digest format (`gbb_accept_rgb_digest*`, `src/runner/acceptance.c`) stays byte-identical.

### G. Player

- **D-26: `--model auto|dmg|cgb`, default `dmg`.**
  - Why `dmg`: `auto` would move dual-mode ROMs, including the Phase 7 Libbet baseline (`$143=$80`) used by `player_session_script_*`, onto the CGB profile, and the player has no CGB game acceptance yet. Phase 15 may flip the default.

  | Value | Behaviour |
  |---|---|
  | `auto` | `gbb_probe_rom` header `$143` bit 7 picks the CGB profile, otherwise DMG |
  | `dmg` | Always the DMG profile; a CGB-only ROM shows the informational note |
  | `cgb` | Always the CGB profile; a non-CGB ROM runs in compat mode |

  - A PGB header is an error: exit non-zero with a message. A bad value is a usage error, exit 2.
  - The profile is re-probed on every open or reload through the single `select_profile` seam, which replaces the six hard-coded `GBB_PROFILE_DMG_CPU_B` sites. A probe failure leaves the running session intact.
  - Existing Libbet player tests keep their current behaviour and pass explicitly or by default as `dmg`.
  - **Reversibility:** reversible.
- **D-27: Presentation.**
  - RGB555 is expanded to the existing RGBA32 streaming texture with `(c<<3)|(c>>2)`, with no correction. Not `SDL_PIXELFORMAT_XBGR1555`, because renderer support varies and it would need a second texture.
  - The DMG branch of `update_frame` is untouched. The runner's expansion helper is copied, or shared through `src/accept`, so both hosts agree.
- **D-28: The window title shows `DMG`, `CGB` or `CGB (DMG-compat)`,** taken from `gbb_get_info` and not from the flag, through the testable `format_window_title`.
- **D-29: The player gets no compat-palette flag in v0.2.** The core API satisfies CGB-05. A flag is deferred.
- **D-30: CGB smoke.**
  - A CTest on the existing native jobs, using dummy SDL video and audio drivers and an original fixture ROM from `fixtures/cgb-colour/` with `--model cgb`.
  - Assertions: the RGBA readback digest, a minimum distinct-colour count, spot pixels computed independently from the expansion formula, and the title token.
  - Negative controls through the existing injected-main pattern: a mutant that forces the grey or DMG path, and one that swaps R and B, must each fail.
  - The DMG smoke digests stay unchanged. No new workflow, third-party action or GPU.
- **D-44: Player claims follow evidence.**
  - Update `src/player/limitations.h` and its verbatim-pinned test, README and `--help`, and the preview.yml `capability_limits` strings, all in the same plan (V2-29).
  - State: audio on the CGB profile is the DMG APU model; no colour correction; CGB mode-3 timing not claimed.

### H. Process and gates

- **D-31: The `DEFERRED(11)` cells (BCPD/OCPD, OPRI) flip in the same plan as their storage.** The `io_visibility[]` rows, visibility tests, `docs/cgb-profile.md` and preflight lists change together (V2-20). The compat columns stay as Phase 10 set them.
- **D-32: Every new model-differing branch gets a `MODEL:` gate tag and a `docs/model-gates.md` row,** enforced by `verify-model-gates.py`. GATE-57 (`gbb_copy_frame` unsupported on CGB) stays. A symmetric gate covers `gbb_copy_frame_rgb555` on DMG.
- **D-33: Advisory interleaved A/B benchmark** of the DMG profile against the Phase 10 head (`3012e8f`), with a CGB colour workload recorded separately. It uses the Phase 10 D-22 trigger (median ratio > 1.05 with lower bound > 1.0) and the same receipt self-test. There is no hosted timing gate.
- **D-34: Fuzz.** Add palette-register sequences (auto-increment wrap, writes during mode 3, CRAM writes interleaved with LCD on/off, compat writes) and `gbb_set_compat_palette` inputs (struct_size and bit 15) to the fuzz target, under ASan/UBSan. New tests use `cgb_`/`palette_` prefixes and are added to `tests/expected-tests.txt` in the same PR.
- **D-35: Wave order.**
  1. Baseline and negative-control mutant harness.
  2. CRAM storage and ports, OPRI, and the visibility flips.
  3. The bank-explicit accessor, attribute fetch, priority composer and truth table.
  4. The RGB555 call, compat palette and runner RGB555 digests.
  5. The player `--model`, presentation and CGB smoke.
  6. Docs, the model-gate audit, the benchmark and the final DMG identity check.
- **D-36: Prepare for Phases 12 and 13 without building them.** The colour path reads only PPU dot time, never `cpu_ticks` (D-070). The VRAM accessor takes an explicit bank. FF55 stays `DEFERRED(13)`.
- **D-37: Every plan SUMMARY `coverage:` block uses the GSD block schema** (AGENTS.md), so `summary_coverage` and `/gsd-verify-work` auto-pass. There is zero human UAT (D-069). No item needs a human visual check; every colour claim is a digest, predicate or truth-table assertion.

### Claude's Discretion

- The exact compat ramp values within D-18's rule.
- Internal names (`rgb_working`, `ppu_compose_cgb`, `ppu_compat_resolve`).
- The fixture ROM layout and the frame counts for MagenTests runs.
- Whether the expansion helper is copied or shared.
- Plan granularity within the D-35 waves.

### Owner veto window

These are adopted, but they are the points the owner may want to override:
1. **D-15:** byte pitch, and `GBB_UNSUPPORTED_PROFILE` on the DMG profile, for the one-way RGB555 ABI.
2. **D-17a:** the compat palette API shape and the bit-15 rejection.
3. **D-18:** the look of the default compat palette (a neutral warm ramp, the same for all three palettes).
4. **D-26:** player default `dmg` rather than `auto`.
5. **D-08:** OPRI writes have no priority effect after boot.
6. **D-21:** the MagenTests applicability labels (none is CGB-E-attested).
7. **D-24:** the G1 posture (acid2 optional-local only), or pursue clearance from the mgblib author.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and requirements
- `.planning/ROADMAP.md` §Phase 11 — goal, success criteria, rights gates G1 and G4, DEEP research items.
- `.planning/REQUIREMENTS.md` — CGB-04, CGB-05, CGB-09.
- `.planning/context/DECISIONS.md` — D-026 (fixed original compat palette, no title-hash; mgblib fixtures out of required CI), D-069 (zero human UAT), D-070 (half-dot timeline).
- `AGENTS.md` — engineering rules, the SUMMARY coverage schema, the phase stop.

### Prior phase decisions
- `.planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-CONTEXT.md` — D-05 (copy_frame on CGB), D-07 (post-boot table), D-10/D-11 (visibility matrix, DEFERRED(11) cells), D-14 (PPU reads `vram[0]`), D-19 (DMG byte-identity gate), D-22 (benchmark trigger); the player `select_profile` seam.
- `.planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-BENCH.md` — the benchmark harness and receipt format to reuse.

### Research
- `.planning/research/v0.2/SUMMARY.md` — P7 colour slot, admitted and excluded fixtures, Conflict #7, gates G1/G4.
- `.planning/research/v0.2/PITFALLS.md` — V2-07, V2-18, V2-19, V2-20, V2-21, V2-24, V2-28, V2-29.
- `.planning/research/v0.2/ARCHITECTURE.md` — PPU colour path and public API items 4 and 8.
- `.planning/research/v0.2/STACK.md` — RGBDS pins (1.0.1; 0.6.1 for MagenTests).

### Docs to update in-phase
- `docs/cgb-profile.md` — post-boot and io tables (mirror-checked by CTest), compat palette values.
- `docs/model-gates.md` — gate rows.
- `docs/native-integration.md` — new RGB555 and compat-palette section.

### Fixtures and CI
- `fixtures/cgb-banking/`, `fixtures/mooneye-cgb/manifest.json` — the fixture layout to copy.
- `fixtures/magentests/` (ELIGIBILITY.md, SOURCES.md) — the place to extend for the three CGB ROMs.
- `.github/workflows/fixture-repro.yml`, `.github/workflows/ci.yml`, `.github/workflows/preview.yml` (`capability_limits`).
- `tests/expected-tests.txt`, `.github/scripts/verify-test-inventory.sh`, `tests/scripts/verify-model-gates.py`, `tests/scripts/verify-summary-coverage.py`.

### External primary sources (read, not vendored)
- Pan Docs: https://gbdev.io/pandocs/Palettes.html, Tile_Maps.html, OAM.html, LCDC.html, CGB_Registers.html, Power_Up_Sequence.html.
- SameBoy `Core/display.c`, `Core/memory.c` — https://github.com/LIJI32/SameBoy (oracle only; GPL-incompatible copying is forbidden).
- AGE test ROMs `1f5bc10e2cb60b86c19f8d0287ff78f410c4f639` — https://github.com/c-sp/age-test-roms.
- MagenTests 0.5.0 `3f9c090f16e5a721db776febb9ba7d773e1c819c` — https://github.com/alloncm/MagenTests.
- cgb-acid2 v1.1 `04c6ca40…`, dmg-acid2 v1.0 `8a98ce73…` — https://github.com/mattcurrie (optional local only, G1).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ppu_transfer_dot` / `ppu_pixel_shade` / `ppu_object_color` (`src/core/gabbaboy.c` ~2193-2410): the per-dot resolution point, which D-01 extends.
- `ppu_fetcher_step` (~2275), `ppu_tile_color` (~2155): where the attribute fetch and bank-explicit reads go.
- `gbb_copy_frame` (~2700-2735): the validation order and checked arithmetic to copy for `gbb_copy_frame_rgb555`.
- `io_visibility[]` (~1199-1203) and `post_boot[]`, with their CTest doc-mirror tests (`cgb_tables_*`).
- `cpu_vram_access_allowed` (~1386): the model for the separate CRAM lockout gate.
- `gbb_accept_rgb_digest*` (`src/accept/gbb_accept.h:211`) and the runner's 5-to-8 expansion.
- Player `format_window_title`, the `update_frame` RGBA32 texture path, the `script_smoke` / `--smoke-package` and injected-main mutant pattern (`verify_script_smoke_surface`).
- `expect_exit.cmake`, the `gbb_add_summary_coverage_test` and `cgb_banking_*` fixture test patterns in `tests/CMakeLists.txt`.

### Established Patterns
- C tables are the single source of truth, with a docs mirror and a diff test (Phase 10).
- Every gate and oracle has a negative control (D-069).
- `MODEL:` tags are audited by `verify-model-gates.py`.
- Fixtures are original RGBDS sources rebuilt byte-identically in fixture-repro, with a manifest and SHA-256.
- Append-only public enums; `struct_size` handshakes.

### Integration Points
- The instance struct gains `rgb_working`/`rgb_completed` (beside `frame_working`/`frame_completed`, ~342), CRAM `bg_cram[64]`/`obj_cram[64]`, and `compat_rgb555[3][4]`.
- The reset/post-boot path (~1326) initialises CRAM and the RGB buffers. The LCD-off path (~1837) fills `rgb_working`.
- Six player `gbb_create(GBB_PROFILE_DMG_CPU_B…)` sites (`src/player/main.c` ~150, 500, 919, 1718, 1964, 2202) route through `select_profile`.
- Runner `--profile cgb` frame cases and acceptance digests (`src/runner/acceptance.c` ~194, 726).

</code_context>

<specifics>
## Specific Ideas

- A real defect the adversarial review caught: a default of `auto` would silently move the Libbet DMG baseline onto the CGB profile. Keep `dmg` as the default.
- The per-line HBlank CRAM fixture (D-23 item 4) is the test that would catch the most likely wrong design, resolving colour at copy time.
- The OPRI behaviour follows SameBoy's after-boot read-back without a live effect, rather than inventing one.

</specifics>

<deferred>
## Deferred Ideas

- **Phase 14 (CGB-E qualification) or later:** CGB mode-3 length, WX and window-range quirks, CRAM lock edge offsets, the PPU-blocked black-pixel quirk, and AGE `m3-bg-*` admission.
- **Phase 15 or later:** flipping the player default to `auto` once CGB game acceptance exists.
- **Future milestone:** a player compat-palette flag or palette presets.
- **Future milestone:** optional, labelled colour correction in the player.
- **Owner-driven:** G1 clearance from the mgblib author, which would admit cgb-acid2/dmg-acid2 to required CI.
- **Future:** `gbb_copy_frame_rgb555` on the DMG profile with a host DMG palette. This is an additive widening.

</deferred>

---

*Phase: 11-CGB Colour Rendering and Player Colour*
*Context gathered: 2026-10-12*
