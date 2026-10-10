# Feature Landscape: v0.2 Color & Cartridge Breadth

**Domain:** Game Boy / Game Boy Color emulator core (original portable C17), subsequent milestone
**Researched:** 2026-10-10
**Scope:** Only the NEW v0.2 features. The founding landscape stays in [../FEATURES.md](../FEATURES.md) and is not repeated.
**Overall confidence:** MEDIUM. Pan Docs, Gekkio GBCTR, Mooneye/SameSuite/AGE READMEs and rtc3test/BGB format notes were read directly. Items tagged LOW rest on memory of hardware behavior and need phase-level research against SameBoy source and test ROMs before a requirement is written. (The OpenGSD research-plan/classify-confidence cache seam was not run; confidence tags here are assigned by source class: test-author README or Pan Docs read this session = MEDIUM-HIGH, recollection = LOW.)

## Executive Recommendation

1. **Game acceptance first, with a rights-clear ROM that is already DMG-playable.** Candidate: Libbet and the Magic Floor v0.08 (zlib, Damian Yerrick / Martin Korth; 32 KiB ROM-only, uses audio, has a prebuilt release asset). It also carries CGB flag `$80`, so the same ROM later gives a CGB-mode smoke for free. Asset SHA-256 observed this session: `3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9`; header verified (type `$00`, 32 KiB, `$143=$80`, SGB flag `$03`). Treat as a candidate until the fixture manifest records source commit, license text, and digest.
2. **Mappers before color.** MBC5, MBC2, and MBC3+RTC are bus-level, independent of CGB, cheap relative to CGB, and every one has a hardware-documented test (Mooneye `emulator-only/mbc2|mbc5`, rtc3test). They also force the two API changes (battery/persistent-state shape, ROM size limit) that CGB should not be entangled with.
3. **One CGB revision: CGB-E, named `GBB_PROFILE_CGB_E`.** SameSuite's APU tests pass completely only on CGB-E (CGB-D and older fail on PCM12/PCM34 glitches), Mooneye splits `boot_div` into `cgb0` and `cgbABCDE`, and Mealybug expectations exist for earlier steppings. One revision keeps every claim testable. CGB-0..D and AGB are explicit unsupported/excluded, not silently approximated.
4. **Color output is a new frame format, not a hack on shade indexes.** Add an RGB555 frame copy; keep `gbb_copy_frame` DMG-only.
5. **RTC is deterministic by construction:** core counts emulated time only; the host injects elapsed offline seconds explicitly; persistence is the VBA-M/BGB 48-byte footer (read 44 or 48, always write 48).

---

## 1. Game-level acceptance (DMG player)

### What it is
A single end-to-end proof that a third-party-authored ROM is playable through the same public API the player uses, before any broadened claim. It is a vertical slice, not a compatibility percentage.

### Observable behaviors that need tests (automated, headless)
| Behavior | How to assert | Evidence class |
|---|---|---|
| Boots to the title/first screen | Frame digest at a fixed emulated time with no input; non-blank (more than one distinct shade index, tile-structure checked) | Regression fixture + private-observation-free |
| Responds to meaningful input | Scripted `gbb_queue_events` (Start, then direction/A); frame digest sequence changes at known emulated timestamps and returns deterministic digests across runs | Regression fixture |
| Progress is guest-observable | A game state change visible in output (e.g. Libbet leaves title, enters a floor, moves after Control Pad input) rather than "no crash" | Regression fixture |
| Audio responds | PCM from `gbb_run_audio`: non-silent after title/start; RMS above a floor and a stable digest over N frames; muted before first sound as appropriate | Regression fixture (not a perceptual claim) |
| Pause/reset/quit path through player | Existing player smoke reused; no new UI | Existing |
| Determinism | Same input script, same digests across Linux/macOS/Windows CI | Existing CI matrix |

### Classification
| Item | Class | Complexity | Notes |
|---|---|---|---|
| One rights-clear fixture with manifest (license, source, digest, redistribution) | Table stakes | Low | Reuse the v0.1 fixture manifest/eligibility process (`fixtures/*/manifest.json`, `ELIGIBILITY.md`). Libbet's zlib license requires the notice be kept; credit Korth. |
| Scripted input + frame/audio digest test | Table stakes | Low-Med | Uses existing API only. |
| Second game | Differentiator (defer) | Med | Not needed for the one-game requirement; pick a mapper-using ROM only if one is rights-clear (see 2-4). |
| "Plays X% of library" or commercial ROM runs | Anti-feature | n/a | Prohibited by AGENTS.md; unmeasurable. |
| Human "looks good" UAT | Anti-feature | n/a | Record perceptual limits honestly; do not invent manual UAT. |

### Dependencies on existing core
Needs only shipped v0.1 behavior (ROM-only, PPU, JOYP, APU). If acceptance exposes an emulator bug, that bug is in scope of the milestone's first phase and gates the broadened claims. Libbet is SGB-flagged (`$146=$03`): the DMG-CPU-B profile must ignore SGB commands cleanly (SGB packets over JOYP must not hang the guest). That is a concrete test the acceptance will exercise.

### Qualified claim shape
"With profile DMG-CPU-B, ROM `libbet.gb` (sha256 ..., zlib), the scripted sequence S reaches frame digests D1..Dn and non-silent audio digest A. This is one game, not game compatibility."

---

## 2. MBC2

**Hardware (Pan Docs MBC2, Gekkio GBCTR; MEDIUM-HIGH).** Up to 256 KiB ROM, 16 banks. Built-in 512 x 4-bit RAM at `A000-A1FF`, echoed through `A200-BFFF` (only low 9 address bits used). Register decode is by address bit 8, not by address range: bit 8 clear in `0000-3FFF` writes RAM enable (low nibble `$A` enables); bit 8 set writes ROM bank (low 4 bits; 0 maps to 1). Header RAM-size code is `$00` even though RAM exists; types `$05` (MBC2) and `$06` (MBC2+BATTERY).

| Feature | Class | Complexity | Notes |
|---|---|---|---|
| Bit-8 register decode, 4-bit bank, 0->1, RAM enable low-nibble `$A` | Table stakes | Low | Mooneye `emulator-only/mbc2/bits_ramg`, `bits_romb` pin this. |
| 512x4-bit RAM with 9-bit echo across `A000-BFFF` | Table stakes | Low | Mooneye `mbc2/ram`. |
| Upper-nibble read policy | Table stakes (decision) | Low | Pan Docs: undefined; Mooneye `bits_unused` expects a specific pattern. Adopt what the hardware test expects (reads set upper four bits to 1), record it as test-backed, and keep the doc-says-undefined caveat. Do not generalize. |
| Header special-case (type `$05/$06` with RAM size `$00`) | Table stakes | Low | The existing loader rejects "contradictory type/RAM declarations"; MBC2 must be allowed explicitly. |
| Battery (type `$06`): 512-byte image | Table stakes | Low-Med | See 5 and the API section. Import must mask to low nibble; export policy (upper nibble `$F` vs `$0`) must be documented. mGBA distinguishes packed/unpacked MBC2 save layouts, so name exactly one supported layout. |
| ROM sizes beyond 256 KiB | Anti-feature | n/a | Reject as unsupported variant. |
| Interop with other emulators' MBC2 `.sav` variants | Differentiator (defer) | Med | Only with named fixtures. |

**Tests:** Mooneye `emulator-only/mbc2/{bits_ramg,bits_romb,bits_unused,ram,rom_512kb,rom_1Mb,rom_2Mb}` (MIT repo; keep the v0.1 per-asset rule: the Mooneye common font has separate licensing). Plus original synthetic banked ROM and a battery round-trip test.

**Dependencies:** loader matrix, battery size query (512 bytes, not 8/32 KiB), battery envelope in player.

---

## 3. MBC3 and deterministic RTC

**Hardware (Pan Docs MBC3, BGB RTC note; MEDIUM-HIGH).** ROM banks `01-7F` (write 0 -> 1), up to 2 MiB; RAM bank register `00-03` selects 8 KiB RAM, `08-0C` selects an RTC register; `0A` written to `0000-1FFF` enables RAM and RTC; latch is a `00` then `01` write to `6000-7FFF`. RTC registers: S `08` (0-59), M `09`, H `0A` (0-23), DL `0B`, DH `0C` (bit 0 day bit 8, bit 6 halt, bit 7 day carry, sticky until cleared). Reads return the latched copy; the live clock keeps running. Types `$0F` (TIMER+BATTERY, no RAM), `$10` (TIMER+RAM+BATTERY), `$11/$12/$13` (no timer). MBC30 (Pokemon Crystal JP only): 4 MiB ROM, 8 RAM banks.

| Feature | Class | Complexity | Notes |
|---|---|---|---|
| MBC3 ROM/RAM banking, enable gate, RAM bank 0-3 | Table stakes | Low | MBC3 Tester exists but has **no license** (repo shows none); use only as an uncommitted local oracle, or ask the author. |
| RTC register select, latch edge (`00`->`01`), read-latched/write-live semantics | Table stakes | Med | rtc3test basic subtest. |
| Halt bit, day carry (sticky), 9-bit day counter | Table stakes | Med | rtc3test basic subtest. |
| Register value masking on read/write (S/M 6 bits, H 5 bits, DH mask `$C1`) and rollover of out-of-range written values | Table stakes | Med | rtc3test "range tests" (LOW-MEDIUM on exact rollover; derive from the test, not from memory). |
| 15-bit sub-second prescaler reset by writing seconds | Table stakes (for rtc3test) | Med | rtc3test "sub-second writes" (26 emulated seconds). Model the 32.768 kHz divider, not a simple 1 Hz tick. |
| Deterministic time source: RTC advances only from emulated time (half-dot timeline), independent of CPU double speed | Table stakes | Med | The RTC crystal is cartridge-side. 1 s = 8,388,608 half-dots on the existing timeline. Never read host time inside the core. |
| Explicit offline catch-up: `advance by N seconds` host call | Table stakes | Low-Med | Core applies N seconds honoring halt and carry. Host computes N from footer timestamp (adapter policy). |
| Timer-only cartridge `$0F` (no RAM) | Table stakes | Low | Battery payload is the RTC alone; today's `GBB_NO_BATTERY` and exact-RAM-size semantics must be revisited. |
| Wall-clock-follow mode in player | Differentiator | Low | Adapter computes elapsed from monotonic/wall clock and calls the advance API; default may be "emulated time + catch-up since last save". |
| Rollback/clock-skew policy (future timestamp, saved-in-future) | Table stakes (policy) | Low | VBA-M/BGB ignore future timestamps; adopt: future or sentinel timestamp => zero catch-up. |
| MBC30 (4 MiB ROM / 64 KiB RAM) | Anti-feature this milestone | Low if limit raised | Single-game, no rights-clear fixture. Reject with `GBB_UNSUPPORTED_CARTRIDGE_VARIANT` rather than silently mapping MBC3 limits. |
| Simultaneous host-clock sync during play | Anti-feature | n/a | Breaks determinism. |

**Persistence format convention (BGB RTC note, MEDIUM-HIGH).** Footer appended to the RAM bytes; 44 or 48 bytes; all little-endian dwords with one register byte in the low byte of each. Layout: seconds, minutes, hours, days-low, days-high (live), the same five latched, then a Unix timestamp of save time (64-bit LE in the 48-byte variant, 32-bit in the 44-byte VBA-2005 variant). If the writer has no clock, write `ff ff ff 7f ff ff ff 7f` (future => ignored by loaders). Recommendation: **import both lengths, export 48**, and detect by file size only inside a host adapter that already knows the cartridge RAM size (size alone is the discriminator: RAM + 44 or + 48; for timer-only carts RAM is 0).

**Tests:** rtc3test (Unlicense per GitHub license metadata; built with RGBDS 0.4.2 per c-sp howto; subtests: A = basic 13 s, Down+A = range 8 s, Down,Down+A = sub-second 26 s emulated) via scripted input and screenshot-digest or register-pass semantics; plus original ROMs asserting: latch edge ordering, halt freeze, carry stickiness, catch-up of N seconds with halt and day wrap, footer round-trip 44->48, future-timestamp ignore, determinism across double-speed (once CGB lands: RTC progress per emulated second unchanged).

**Dependencies on existing core:** timed event timeline (half-dots) already present; `gbb_copy_battery` and the player envelope (v1 envelope hard-codes type `$03` and RAM 8/32 KiB) must change.

---

## 4. MBC5 (including rumble)

**Hardware (Pan Docs MBC5; MEDIUM-HIGH).** 9-bit ROM bank: low 8 bits via `2000-2FFF`, bit 8 via `3000-3FFF`; writing 0 selects **bank 0** in `4000-7FFF` (no 0->1 remap); up to 8 MiB (header ROM code `$08`; `$07` = 4 MiB). RAM bank `00-0F` at `4000-5FFF`; RAM sizes 8/32/128 KiB (header `$02/$03/$04`; `$05` = 64 KiB). RAM enable: documented `$0A`; Pan Docs notes hardware appears to gate on low nibble `$A` and advises not to rely on it. Types `$19`, `$1A`, `$1B` (battery), `$1C`, `$1D`, `$1E` (rumble variants). On rumble carts bit 3 of the RAM bank register drives the motor and is not part of the bank number.

| Feature | Class | Complexity | Notes |
|---|---|---|---|
| 9-bit ROM bank, bank-0-in-upper-window, ROM up to 8 MiB | Table stakes | Low | Mooneye `emulator-only/mbc5/rom_512kb ... rom_64Mb` (64Mb = 8 MiB). Requires lifting the loader's 2 MiB hard limit and adding ROM-size codes `$07/$08`; this changes the bounded-allocation story (ROM copy + work bound) and needs a documented new cap (8 MiB) and fuzz coverage. |
| RAM banks 0-15, 8/32/64/128 KiB, battery type `$1B/$1E` | Table stakes | Low-Med | Battery size now up to 128 KiB: player envelope (v1 max 32 KiB) must grow. |
| Rumble bit masked out of the RAM bank number | Table stakes | Low | Without this, rumble carts (e.g. Pokemon Pinball class) select wrong RAM banks. |
| Expose rumble line state to host (query + change counter) | Table stakes (API) | Low | Output only. Intensity is duty-cycle of rapid toggling: host samples per frame; core need not time-stamp every toggle in v0.2. |
| Player haptics through SDL gamepad rumble | Differentiator | Low-Med | Optional adapter feature behind a flag; do not make it required. |
| RAM enable gating: pick and document (low nibble `$A`, matching existing MBC1 policy) | Table stakes (decision) | Low | Record that this follows Pan Docs' hardware note and is test-pinned by an original ROM. |
| Header-time rejection of lies (ROM size vs image, RAM size vs type) | Table stakes | Low | Reuses existing loader errors. |
| MBC5 multicarts, 1 MiB+ unusual wiring | Anti-feature | n/a | Not in scope. |

**Tests:** the eight Mooneye MBC5 ROMs; original synthetic ROMs for bank 0 in upper window, bank `$1FF`, RAM bank 15 on non-rumble, rumble masking, battery round-trip at 128 KiB.

---

## 5. Battery and persistence interplay (cross-cutting)

The three mapper families collectively break two v0.1 assumptions: "battery = exactly 8 or 32 KiB of RAM" and "no state beyond RAM bytes". Required changes: battery size may be 512 B (MBC2), 0 (timer-only), up to 128 KiB (MBC5); and a cartridge may carry RTC state separate from RAM bytes. See the API section for the recommended shape. Table stakes: round-trip tests for each, atomic player writes, recovery, unchanged identity rules. Differentiator: raw `.sav` import/export with the footer convention (explicit, opt-in, and named in docs).

---

## 6. CGB silicon profile

### 6.1 Mode selection and bootless post-boot state (table stakes, Med)

**Facts (Pan Docs Power-Up Sequence; MEDIUM-HIGH):**
- Header `$143`: bit 7 set => CGB mode (`$80` enhanced, `$C0` CGB-only); otherwise DMG-compatibility mode. The CGB boot ROM checks bit 7.
- Post-boot CPU (CGB): `A=$11`, `F` Z=1 N=0 H=0 C=0, `B=$00`, `C=$00`, `D=$FF`, `E=$56`, `H=$00`, `L=$0D`, `PC=$0100`, `SP=$FFFE`.
- DMG-compat on CGB: `A=$11`, `C=$00`, `D=$00`, `E=$08`, `B` = sum of 16 title bytes if old licensee `$01` (or `$33` with new licensee "01"), else `$00`; `HL=$991A` if `B` is `$43` or `$58`, else `$007C`.
- AGB differs (`B` +1, flags from `inc b`; `B=$01` in CGB mode): that is how games detect Game Boy Advance. **AGB is not in scope.**
- I/O after boot: `P1 $C7/$CF`, `SB $00`, `SC $7F`, `TAC $F8`, `IF $E1`, `NR52 $F1`, `LCDC $91`, `BGP $FC`, `KEY1 $7E`, `VBK $FE`, `HDMA1-5 $FF`, `RP $3E`, `SVBK $F8`, `IE $00`; `DIV`, `LY`, `STAT` depend on boot timing; `OPRI` = `$01` only in DMG-compat mode (CGB mode: 0). `KEY0` is written by the boot ROM and locks (`$04` for non-CGB carts).
- **Bootless problem (HIGH relevance):** DIV/LY/STAT phase at hand-off is what the real boot ROM leaves; Mooneye `misc/boot_div-cgb0`, `boot_div-cgbABCDE`, `boot_hwio-C`, `boot_regs-cgb` pin them. Choose a deterministic phase from those tests' expected values and mark any untestable field "policy, not hardware observation".

| Feature | Class | Complexity | Notes |
|---|---|---|---|
| `GBB_PROFILE_CGB_E` with header-driven mode (CGB vs DMG-compat) | Table stakes | Med | Explicit profile; no hybrid DMG/CGB state (Key Decision: explicit profiles). |
| CGB-only ROM (`$C0`) on DMG profile | Table stakes (policy) | Low | Recommend: keep a distinct error (new `gbb_error`) rather than running a DMG with CGB-only software; documents the model-applicability gate. |
| Bootless register table above | Table stakes | Med | Test with Mooneye `boot_regs-cgb`, `boot_hwio-C`, `boot_div-cgbABCDE`. |
| Real boot ROM execution | Anti-feature | n/a | Nintendo boot ROMs prohibited; replacement boot also out of scope. |

### 6.2 CGB-mode memory and bus (table stakes, Low-Med each)

| Feature | Behavior | Complexity | Tests |
|---|---|---|---|
| VRAM bank (`FF4F` VBK, bit 0 only, other bits read 1) | Bank 1 holds tile data `8000-97FF` and BG attribute map `9800-9FFF` | Low | SameSuite `dma/*` use it; original ROMs; cgb-acid2. |
| WRAM bank (`FF70` SVBK, bits 0-2, 0 maps to 1); bank 0 fixed at `C000`, 1-7 at `D000`; echo RAM mirrors | 32 KiB WRAM; `gbb_peek_ram` semantics extend (see API) | Low | Original ROM writing a distinct marker to each bank; peek checks. |
| Registers gated by mode: in DMG-compat, CGB-only registers read/lock as hardware does | Needs per-register table; see 6.7 | Med | Mooneye `misc/bits/unused_hwio-C`. LOW on exact compat-mode behavior of each register; verify in SameBoy/Gekkio. |

### 6.3 CGB PPU: attributes, palettes, priority (table stakes, High overall)

**Facts (Pan Docs Palettes, CGB Registers; MEDIUM-HIGH):**
- 8 BG and 8 OBJ palettes, each 4 colors of RGB555 (bit 15 ignored), 64 bytes of CRAM each, little-endian. Index registers (BGPI `FF68`, OBPI `FF6A`) hold a 6-bit address and bit 7 auto-increment; data registers `FF69`/`FF6B`. Auto-increment advances after each *write* (even an ignored one), wraps 63->0, never on reads. During mode 3 data writes are ignored and reads return `$FF`. Boot ROM leaves all BG colors white; OBJ color 0 is never used.
- BG map attribute byte: bits 0-2 palette, bit 3 tile VRAM bank, bit 5 X flip, bit 6 Y flip, bit 7 BG-over-OBJ priority. OAM flags: bits 0-2 CGB palette, bit 3 VRAM bank, bit 4 DMG palette (compat), bits 5/6 flips, bit 7 priority. (Gekkio/Pan Docs; MEDIUM.)
- `LCDC` bit 0 on CGB is a master priority switch (0 = objects always above BG regardless of attributes), not BG-enable (the changed meaning is in Pan Docs Video Display; LOW-MEDIUM on corner cases, verify with cgb-acid2).
- `OPRI` (`FF6C` bit 0): 0 = OAM-index priority (CGB), 1 = X-coordinate priority (DMG-style). Boot ROM sets 1 for DMG-compat.

| Feature | Class | Complexity | Notes |
|---|---|---|---|
| CRAM with auto-increment, mode-3 lockout, correct post-boot contents | Table stakes | Med | SameSuite `ppu/blocking_bgpi_increase`. |
| Tile/attribute fetch from bank 1, flips, per-tile palette, BG priority bit, master priority, OPRI | Table stakes | High | cgb-acid2 (MIT) is the compositional gate. Dot-level fetcher already exists; add attribute and bank fetches without changing timing (CGB mode 3 length differences must be tested, not assumed). |
| RGB555 output frame | Table stakes | Low-Med | See API. |
| Mid-scanline palette/attribute timing | Differentiator | High | Mealybug Tearoom Tests (MIT) has expected images for specific CGB steppings; expectations for CGB-E are not guaranteed. Admit only the subset with CGB-E evidence; the rest is an explicit expected-failure with reason. |
| LCD color correction (CGB screen response) | Differentiator, adapter-only | Low | Core emits raw RGB555. Pan Docs notes the unlit screen and unsaturated pigments; correction is presentation policy, never baked into goldens. Test conventions (c-sp): expand 5->8 bits as `(x<<3)|(x>>2)`. |
| DMG-only quirks that must NOT leak into CGB | Table stakes | Low-Med | OAM corruption bug is DMG/MGB only (LOW: confirm); DMG STAT-write spurious interrupt is absent on CGB (LOW-MEDIUM: confirm). Gate each by profile; add negative tests. |
| Per-line VRAM/OAM lock timing for CGB vs DMG | Table stakes | Med | Existing DMG lock model is DMG-CPU-B; do not reuse blindly for CGB-E without a Mooneye `-C` or AGE CGB test. |

### 6.4 DMG-compatibility mode on CGB (table stakes, Med)

**Facts (Pan Docs Power-Up Sequence, MEDIUM-HIGH; c-sp howtos, MEDIUM):**
- Non-CGB-flagged cartridge on CGB-E: `KEY0=$04`, `OPRI=$01`, BG attribute map zeroed (all BG palette 0), objects choose OBJ palette 0/1 by attribute bit 4, `BGP/OBP0/OBP1` index into CGB palettes. VBK/SVBK/other CGB features are unavailable (verify exact register behaviors; LOW).
- **Palette selection:** if old licensee is `$33`, new licensee must be "01"; else old licensee must be `$01`; otherwise palette ID `$00`. Sum the 16 title bytes, look up in a table; if the index is above 64, disambiguate by the fourth title byte in a second table, ID = index + 14 x row. Manual palette override by held buttons during logo (bit 7 of CGB byte clear) is a boot-logo feature, not reproducible bootless.
- Default (unlisted) compat palette, from the c-sp test expectations: BG shades `#000000 #0063C6 #7BFF31 #FFFFFF`; OBJ `#000000 #943939 #FF8484 #FFFFFF` (these are for screenshot comparison; MEDIUM).

| Feature | Class | Complexity | Notes |
|---|---|---|---|
| DMG-compat rendering path (DMG palettes through CRAM, X-priority, attribute map treated as zero) | Table stakes | Med | Same PPU, mode flag. Test with dmg-acid2 (MIT) in compat mode and mbc/rtc test ROMs which c-sp notes run in compat mode on CGB. |
| Palette-ID selection algorithm + palette table | Table stakes if "DMG on CGB looks like a real CGB" is claimed; otherwise default-only | Med | **Rights/provenance:** the table is Nintendo boot-ROM data. Do not extract from a dump. Source from Pan Docs/TCRF description and SameBoy's reimplementation (MIT project; verify the specific file's notice), record provenance, and test with original synthetic headers (title bytes/licensee set to hash to known entries) so no commercial ROM is committed. If provenance review blocks, ship default palette `$00` only and state it. |
| User-selectable DMG-compat palette override (player) | Differentiator | Low | Needs only a core call to set the three palettes; useful for monochrome-look players. |
| Palette-ID mismatch / `B`-register title-sum parity between register init and palette logic | Table stakes | Low | Same title sum feeds `B` and the palette ID; test them together. |
| Running a DMG ROM on CGB by user choice | Table stakes (opt-in) | Low | Player `--model cgb` forces CGB-E on a DMG ROM; default `auto` follows header. |
| AGB-style DMG palette tweaks | Anti-feature | n/a | AGB unsupported. |

### 6.5 Double speed (table stakes, High)

**Facts (Pan Docs CGB Registers; MEDIUM-HIGH):** `KEY1` (`FF4D`): bit 7 read-only current speed, bit 0 armed. `STOP` with bit 0 armed performs the switch and clears bit 0. Double speed doubles CPU, timer/DIV, serial, and OAM DMA; LCD, HDMA, and sound timing are unchanged. After `STOP` the CPU pauses 2050 M-cycles (8200 T-cycles); DIV does not tick during it so some audio events are skipped. During the pause PPU quirks exist: mode 0/1 gives no VRAM access with black pixels; mode 2 background renders without sprites; mode 3 unaffected. Whether interrupts can fire during the pause is TODO in Pan Docs (LOW; do not claim). APU frame sequencing follows DIV bit 5 in double speed so the 512 Hz rate is preserved (HARDWARE-AND-VALIDATION.md; MEDIUM). Recommended guest procedure: IE=0, JOYP=`$30`, set KEY1, `STOP`.

| Feature | Class | Complexity | Notes |
|---|---|---|---|
| KEY1 arm + STOP switch with correct pause length and no low-power STOP side effects | Table stakes | High | Interacts with existing `GBB_STOP_STOPPED`/wake machinery in v0.1: a speed-switch STOP must **not** return `GBB_STOP_STOPPED` waiting for wake. API note below. |
| CPU/timer/serial/OAM-DMA at 2x; PPU/APU/HDMA at 1x | Table stakes | High | The half-dot timeline already supports it (CPU M-cycle = 8 half-dots normal, 4 double). Budget and input timestamps keep meaning unchanged. |
| APU sequencer from DIV bit 5 in double speed | Table stakes | Med | SameSuite `apu/div_write_trigger*`. |
| PPU artifacts during the 2050-M-cycle pause | Differentiator | Med-High | Pan Docs-described; not game-relevant for most; start with correct duration, add rendering quirk only if a test requires it. |
| Interrupt delivery during pause | Open question | n/a | Do not claim; mark expected-failure/unspecified. |

**Tests:** original ROM measuring DIV/TIMA/serial progress per scanline before and after the switch; Gambatte `speedchange*` tests (GPL-licensed upstream; use only as local oracle unless redistribution review passes); SameSuite apu div tests; AGE tests (MIT, verified on DMG, CGB-B/C/E hardware per c-sp); Mooneye CGB variants for timer/oam_dma with `-C`/`-cgb` suffixes in double speed where available. RTC rate invariant under speed switch.

### 6.6 General-purpose and HBlank DMA (HDMA) (table stakes, Med-High)

**Facts (Pan Docs; MEDIUM-HIGH):** `HDMA1/2` source (write-only; valid `0000-7FF0`, `A000-DFF0`; low 4 bits ignored); `HDMA3/4` destination (bits 12-4 only, targets `8000-9FF0`); `HDMA5` write: bits 0-6 = length in 16-byte blocks minus 1 (so `$10-$800` bytes), bit 7 selects mode. General-purpose DMA copies all at once and halts the CPU; it ignores PPU VRAM lock. HBlank DMA copies `$10` bytes per HBlank on LY 0-143 only, the CPU halts for each block and runs in between; HALT pauses it. `HDMA5` read: remaining blocks minus 1; bit 7 reads 0 while active, 1 when finished or cancelled ($FF when done). Writing 0 to bit 7 during an HBlank transfer cancels it (HDMA1-4 not reset). Starting HBlank DMA during mode 0 is called out as unsafe; destination overflow stops early with unresearched state (LOW). A `$10`-byte block takes 8 M-cycles at normal speed, 16 at double speed (about the same wall time).

| Feature | Class | Complexity | Tests |
|---|---|---|---|
| GDMA: address masking, length, CPU halt duration, VRAM-bank-aware destination | Table stakes | Med | SameSuite `dma/gdma_addr_mask`, `dma/gbc_dma_cont`; MagenTests (MIT; some oracles from an emulator - inspect). |
| HDMA per-HBlank block copy, LY 0-143 only, resume next frame | Table stakes | High | SameSuite `dma/hdma_mode0`, `dma/hdma_lcd_off`. |
| HDMA5 read semantics, cancel, new transfer after cancel | Table stakes | Med | Original ROM + SameSuite. |
| HALT interaction, double speed block timing, LCD-off behavior | Table stakes | High | SameSuite `hdma_lcd_off`; MagenTests VRAM-DMA/HALT; mark unresearched cases explicitly. |
| Source from VRAM / echo / OAM / IO / HRAM | Edge | Low | Pan Docs: VRAM source copies garbage; others untested. State "garbage/undefined, not claimed" instead of choosing a convenient value. |
| Interaction with OAM DMA in progress | Differentiator | Med | CGB OAM DMA bus differences from DMG (HARDWARE-AND-VALIDATION.md); LOW until an oracle is chosen. |

### 6.7 CGB-specific CPU/I-O differences (table stakes unless noted)

| Item | Class | Complexity | Notes |
|---|---|---|---|
| Serial fast clock (`SC` bit 1, CGB only) and `SC $7F` post-boot | Table stakes (disconnected serial) | Low-Med | Disconnected endpoint already exists; add bit and 2x/double-speed rates. LOW-MEDIUM on exact rate math; verify against Pan Docs serial chapter. |
| Timer/TAC/DIV edge differences DMG vs CGB | Table stakes | Med | Existing derived Mooneye timer closures are DMG-CPU-B; CGB variants need new eligibility records, not reuse. Pan Docs notes some CGB TAC-enable behavior varies by console; state as per-model-assumed. |
| `JOYP` interrupt on CGB | Gate | n/a | v0.1 left JOYP IF generation unmodeled (DMG evidence gate open). Do not silently extend to CGB. |
| Echo RAM, FEA0-FEFF region, I/O unused bits per mode | Table stakes | Med | Mooneye `unused_hwio-C`; many reads differ from DMG. |
| STOP/HALT/IME bugs unchanged | n/a | n/a | No SM83 opcode differences between DMG and CGB; do not fork the CPU. |

### 6.8 CGB APU differences (scope: minimum viable model, then optional)

Facts: SameSuite APU README (read this session; MEDIUM-HIGH): CGB-E passes every apu test; CGB-D fails `channel_1_sweep_restart_2`; CGB-C and earlier glitch `PCM12/PCM34` for channels 1, 2, 4 when read in the same M-cycle as a change; pre-CGB devices lack PCM registers so most tests are N/A. The "zombie mode" NRx2 glitch differs per revision; only CGB-E is documented.

| Feature | Class | Complexity | Notes |
|---|---|---|---|
| `FF76` PCM12 / `FF77` PCM34 read-only digital outputs (per-channel 4-bit amplitude, pre-mixer) | Table stakes for SameSuite and CGB-E claim | Med | Requires the APU to expose per-channel DAC output at a read instant. The existing scoped 4-channel DMG APU is the base. |
| Length-counter / register-write behavior while APU powered off (CGB differs from DMG) | Table stakes | Low-Med | LOW on exact rules; verify in SameBoy before coding. |
| Wave RAM initial contents and access timing differences | Table stakes | Med | LOW until verified; DMG access window quirks must be gated by profile. |
| NRx2 "zombie mode" envelope glitch per CGB-E | Differentiator | Med | SameSuite documents CGB-E only. |
| Sweep/DIV-write trigger behavior per CGB-E | Table stakes for SameSuite apu subset | Med-High | `div_write_trigger*`, `channel_1_*`. |
| High-pass filter charge factor CGB vs DMG | Differentiator (perceptual) | Low | Pan Docs gives different capacitor factors (recall: DMG ~0.999958, CGB ~0.998943, per-rate; verify). Not hardware-test-pinned; label as model parameter. |
| Perceptual audio equivalence claims | Anti-feature | n/a | Same limits as v0.1. |

Support rule: `GBB_PROFILE_CGB_E` claims only the SameSuite APU subset that passes on CGB-E hardware per the author, with `channel_4_freq_change` and `channel_1_sweep_restart_2` as listed SameBoy-also-fails expected-failures unless implemented to pass.

### 6.9 Infrared port RP (`FF56`) (table stakes minimal, Low)

Facts (Pan Docs): bits 7-6 read-enable (`3` enables, `0` disables and bit 1 then reads 1); bit 1 receiving (0 = signal received, 1 = none), read-only; bit 0 LED, R/W. Post-boot `RP=$3E`. Receiver adapts to ambient IR; no GBA IR.

| Item | Class | Complexity | Notes |
|---|---|---|---|
| Register with correct masks, LED bit stored, receive bit always 1 (no signal), read-enable honored | Table stakes | Low | Prevents hangs in games that probe for IR (they time out). |
| IR peer link / Mystery Gift emulation | Anti-feature | High | Needs two instances and sub-frame timing; link accessories deferred in PROJECT.md. |
| Host injection of IR pulses for tests | Differentiator (defer) | Med | Only with a fixture. |

### 6.10 Undocumented registers `FF72-FF77`

Pan Docs: `FF72`, `FF73` full R/W (initial `$00`); `FF74` R/W in CGB mode, locked at `$FF` otherwise; `FF75` bits 4-6 R/W (others read 1); `FF76/FF77` are PCM12/PCM34 (6.8). MEDIUM (Pan Docs marks details as incomplete).

| Item | Class | Complexity | Notes |
|---|---|---|---|
| `FF72-FF75` as plain storage with masks | Table stakes | Low | Tested by Mooneye `unused_hwio-C` and original ROM; no feature depends on semantics. |
| `FF76/FF77` | See 6.8 | Med | |

### 6.11 Revisions: CGB-0, A-D, E, and AGB

| Revision | v0.2 stance | Reason |
|---|---|---|
| **CGB-E** | **Supported profile (qualified subset)** | Author hardware results cover APU (SameSuite) and boot/div variants; most current CGB software targets it. |
| CGB-0 | Unsupported, named | Mooneye separates `boot_div-cgb0`. |
| CGB-A..D | Unsupported, named; their goldens may not be used for CGB-E | Mealybug and SameSuite expectations differ by stepping (HARDWARE-AND-VALIDATION.md). Tests with only CGB-C/D evidence become expected-failure with reason or are excluded. |
| AGB (GBA in CGB mode) | Unsupported (anti-feature for v0.2) | Different post-boot register values, PPU/APU quirks; some games change behavior when `B bit0` is set. Never run CGB-E under an AGB label. |
| Selecting a revision at runtime | Not now | Adding enumerators without tests would promise untested behavior. |

---

## 7. Model-qualified support claim (shape)

A reasonable v0.2 claim, to be written into `docs/support/v0.2.0.md` and the source-bound ledger (same machinery as v0.1.0's):

- **Models:** `DMG-CPU-B` (bootless, unchanged v0.1 scope plus game acceptance) and `CGB-E` (bootless post-boot state in CGB mode and DMG-compat mode). Nothing else.
- **Cartridges:** ROM-only, standard MBC1 (v0.1), MBC2 (`$05/$06`), MBC3 `$0F-$13` excluding MBC30, MBC5 `$19-$1E`; exact header matrix in `cartridge-and-saves.md`.
- **Evidence classes, separate columns:** hardware-backed tests (Mooneye/SameSuite/AGE/rtc3test/cgb-acid2 results with the author's stated device list), differential oracle (SameBoy agreement, never alone), metamorphic (e.g. RTC advance(N) then advance(M) == advance(N+M); battery round-trip; speed-switch invariants), regression fixtures (frame/PCM digests), private observations (none committed).
- **Denominators:** per-suite eligible/pass/fail/unsupported/excluded/timeout/missing, each failure carrying a reason, e.g. "requires CGB-C/D stepping", "Pan Docs unresearched", "fixture not redistributable".
- **Explicit exclusions:** AGB, CGB-0..D, MBC30, MBC1M, HuC/MMM01/MBC6/MBC7/Camera, IR peer link, rumble motor realism, color-correction fidelity, perceptual video/audio, physical hardware, save states, Playstead.
- **Statement:** "Plays the listed fixtures and passes the listed hardware tests under these models; this is not general GB/GBC game compatibility."

---

## 8. Public C API changes

Current header facts (`include/gabbaboy/gabbaboy.h`): one profile enum value, 160x144 shade-index frame, battery API tied to RAM size, `gbb_peek_ram` for WRAM/HRAM, `gbb_stop_reason` includes `GBB_STOP_STOPPED`, 2 MiB ROM cap, no RTC.

| Change | Recommendation | Why / constraint |
|---|---|---|
| Model selection | Add `GBB_PROFILE_CGB_E`; keep `gbb_create(profile, ...)`. DMG-on-CGB is **not** a third profile: it is CGB-E with mode derived from the loaded ROM header, exposed read-only. | Avoids hybrid profile; mode is a property of cartridge+profile. |
| Mode and cartridge info | New `gbb_get_info(instance, gbb_info*)` returning profile, `cgb_mode` (native/compat), mapper kind, ROM/RAM sizes, has_rtc, has_battery, has_rumble, cgb_flag. | Players need this to choose output format and save policy without parsing headers. |
| New load errors | e.g. `GBB_UNSUPPORTED_MODEL_FOR_ROM` (CGB-only on DMG), keep `UNSUPPORTED_CARTRIDGE_VARIANT` for MBC30/MBC2 oversize; extend `GBB_ROM_TOO_LARGE` to the new 8 MiB bound. Add enum values only at the end (enum numbering is part of the preview ABI discipline). | Failed load leaves current ROM unchanged (existing contract). |
| ROM bound | Raise hard cap from 2 MiB to 8 MiB; add size codes `$07/$08`; document the allocation bound and fuzz it. | MBC5 requires it. |
| Color frames | Add `gbb_copy_frame_rgb555(instance, uint16_t *pixels, capacity_bytes or elements, pitch, gbb_frame_info*)` with the same overlap/overflow validation as `gbb_copy_frame`. Add `format` to `gbb_frame_info` or a separate `gbb_frame_format` query. `gbb_copy_frame` on a CGB profile returns a defined error (do not luma-convert silently). DMG profile via the RGB555 call uses the documented 4-shade mapping. | CGB colors are 15-bit; raw output keeps correction in the adapter. |
| Battery / persistence | Keep `gbb_battery_size/copy/import` as RAM-only bytes (0 for timer-only: change `GBB_NO_BATTERY` meaning to "no persistent state" only when neither RAM nor RTC exists). Add `gbb_has_rtc`, `gbb_rtc_get(gbb_rtc_state*)`, `gbb_rtc_set`, `gbb_rtc_advance_seconds(uint64_t)`. `gbb_rtc_state` is a plain struct: live S/M/H/day(9-bit)/halt/carry + latched copy + latch-pending flag + sub-second prescaler value. | Core stays free of file formats and wall clock; deterministic and testable. |
| Footer codec | Provide pure helpers (not instance-bound) `gbb_rtc_footer_decode(const uint8_t*, size_t, gbb_rtc_state*, uint64_t *saved_unix)` / `..._encode` for the 44/48 byte convention; host computes `advance = now - saved_unix` (clamp negatives to 0 and treat the `7fffffff` sentinel as no catch-up). | Interop requires exactly one implementation of the layout; keep it testable without a cartridge. |
| Battery generation | Count RTC register changes? Recommendation: RTC ticking does not bump the battery generation (would force a save every second); expose a separate `rtc_generation` bumped by guest writes/latch/halt toggles and by `advance`/`set`. Host saves RTC on exit and on RAM-dirty flush. | Avoid wearing save logic with ticks. |
| Rumble | `gbb_rumble_state(instance, uint8_t *on, uint64_t *generation)`. | Host samples per frame. |
| Speed state | Expose `gbb_get_info().double_speed` or a `gbb_speed` query for adapters that display it; budgets stay in half-dots. | Timeline already encodes speed. |
| Stop reasons | Speed-switching `STOP` must complete the switch and continue running; document that `GBB_STOP_STOPPED` remains true low-power STOP. | Prevents hosts mistaking a speed change for a hang. |
| Peek | Extend `gbb_peek_ram` documentation for banked WRAM (`C000-DFFF` shows the *current* D000 bank) and add `gbb_peek_vram(bank, addr)` only if tests need it. | Keep debug reads side-effect free. |
| DMG-compat palettes | `gbb_set_compat_palettes(...)` optional override; default behavior implements the boot-ROM selection algorithm. | Differentiator, small. |
| Docs/ABI | Update header comments, `docs/cartridge-and-saves.md`, `docs/native-integration.md`, the relocated C and C++ consumers, support ledger. Preview ABI promise stays "none". | Matches AGENTS.md "update docs together". |

## 9. Player changes

| Change | Class | Notes |
|---|---|---|
| `--model auto|dmg|cgb`, default `auto` (header bit 7 => CGB-E, else DMG-CPU-B) | Table stakes | `cgb` on a DMG ROM exercises DMG-compat; `dmg` with a CGB-only ROM shows the load error cleanly. |
| RGB555 -> texture (SDL3 `SDL_PIXELFORMAT_XRGB1555` or expand to RGBA8888); DMG still uses a fixed 4-shade palette | Table stakes | Expand 5->8 bits with `(x<<3)|(x>>2)`; correction off by default, optional flag later. |
| Save envelope version 2: variable RAM length (0, 512 B, 8/32/64/128 KiB), RTC block (live + latched + epoch seconds at save), keep CRC-32, keep ROM SHA-256 identity; read v1 saves; never silently drop RTC | Table stakes | v1 encodes type `$03` and 8/32 KiB only; per docs, "future envelope change must migrate existing progress or retain access to the older file." |
| RTC policy: on load compute elapsed since saved epoch (monotonic wall) and call `gbb_rtc_advance_seconds`; ignore future timestamps; cap documented | Table stakes | Host policy; core stays deterministic. |
| Save-on-RTC-change: flush RTC with RAM on the existing quiet-2s/10s dirty rule and at quit, not each tick | Table stakes | Reuses atomic replacement, lock, recovery. |
| Raw `.sav` import/export with 44/48-byte RTC footer | Differentiator | Explicit command or flag, never auto-detected overwriting native saves; round-trip test per variant. |
| Rumble via gamepad haptics | Differentiator | Optional. |
| Window title/status: model and mode indicator | Differentiator | Cheap diagnosability. |
| ROM size cap in file loader | Table stakes | Player's own read bound must rise to 8 MiB + header. |
| Color correction, palette picker UI, shaders | Anti-feature this milestone | Scope creep. |

---

## 10. Feature dependencies

```
Fixture manifest process (v0.1) -> rights-clear game acceptance
Game acceptance -> any broadened claim (gate)
Loader matrix + ROM-size cap raise -> MBC5 (8 MiB) -> MBC5 tests
Battery shape change (size 0/512/128K + RTC) -> MBC2, MBC3, MBC5 persistence -> player envelope v2
Half-dot timeline (exists) -> MBC3 RTC clock -> advance API -> footer codec -> player RTC policy
GBB_PROFILE_CGB_E -> header mode -> post-boot state (native vs compat)
VRAM/WRAM banking -> BG attributes -> CRAM/palettes -> RGB555 frame -> cgb-acid2
CRAM + OPRI + title-hash palette table -> DMG-compat rendering
Double speed (KEY1/STOP) -> timer/serial/OAM-DMA 2x -> APU DIV bit 5 -> HDMA 16-M-cycle blocks
HDMA -> PPU mode-0 edge exactness (existing PPU) + CPU halt arbitration
PCM12/PCM34 -> APU per-channel DAC taps -> SameSuite APU subset
Everything above -> model-qualified ledger -> v0.2 release
```

Ordering that follows from dependencies: (1) acceptance and mapper/loader/battery shape changes (independent of CGB); (2) CGB mode skeleton: profile, banking, post-boot, RGB555 path; (3) CGB PPU attributes/palettes and DMG-compat; (4) double speed then HDMA (HDMA correctness depends on speed-aware halt timing); (5) CGB APU subset and misc registers (RP, FF72-77); (6) ledger/docs/release. Double speed and HDMA are the most likely to need deeper phase research.

## 11. MVP recommendation

Prioritize: game acceptance; MBC5 and MBC2 (low risk, hardware tests exist); MBC3 + RTC with footer interop; CGB-E profile with VRAM/WRAM banking, attributes, palettes, RGB555; DMG-compat with default palette first, table-driven selection after provenance review; double speed; GDMA/HDMA; PCM12/34 and the CGB-E APU subset; RP and FF72-75 as masked registers.

Defer: AGB and CGB-0..D; MBC30; rumble haptics; mid-scanline Mealybug breadth beyond CGB-E-evidenced cases; color correction; raw `.sav` interop beyond the RTC footer; IR link; PPU pause-time artifacts during speed switch; any claim about interrupts during the switch pause.

## 12. Test source rights notes (feeds fixture admission)

| Suite | License / rights seen | Use |
|---|---|---|
| Mooneye test suite | MIT repo (GitHub metadata); font assets separately licensed (v0.1 finding) | Reuse the v0.1 derived/eligibility process |
| cgb-acid2, dmg-acid2, Mealybug Tearoom | MIT | Admit with digests; Mealybug only for steppings with CGB-E evidence |
| SameSuite | X11-style permissive text by Lior Halphon | Admit sub-suites that author lists as passing on CGB-E |
| age-test-roms | MIT | Admit tests with CGB-E hardware verification |
| rtc3test | Unlicense (GitHub metadata) | Admit; needs RGBDS 0.4.2 if rebuilt |
| MBC3 Tester | No license found | Local oracle only; do not commit |
| Gambatte tests | GPL upstream | Local oracle only unless review clears |
| MagenTests | MIT | Inspect oracle provenance per test |
| Libbet (game) | zlib; Martin Korth credit | Candidate for game acceptance |
| Blargg tests | Redistribution unresolved (v0.1 finding) | Not relied on |

## Gaps (carry into phase research)

- Exact rollover of out-of-range RTC register writes and the sub-second prescaler details: derive from rtc3test source/expected images.
- Which CGB-only registers are readable/writable in DMG-compat mode on CGB-E (LOW); KEY1 behavior in compat mode.
- CGB OAM DMA bus differences and double-speed duration against a chosen oracle.
- Bootless DIV/LY phase for CGB-E at hand-off (pin to Mooneye expected values).
- CGB-E mode 3 length and VRAM/OAM lock timing versus DMG-CPU-B; DMG-only quirks (OAM bug, STAT write bug) absent on CGB: confirm.
- Interrupts during the speed-switch pause (Pan Docs TODO).
- Provenance and rights of the DMG-compat palette table.
- Libbet license completeness for bundled assets and the exact release/build recipe.
- Mooneye CGB-suffixed test list and which have CGB-E-specific expectations (the tree listing here only confirmed `misc/` and `emulator-only/mbc2|mbc5`; `acceptance/` CGB variants were not enumerated).

## Sources

- [Pan Docs: Power-Up Sequence](https://github.com/gbdev/pandocs/blob/master/src/Power_Up_Sequence.md), [CGB Registers](https://github.com/gbdev/pandocs/blob/master/src/CGB_Registers.md), [Palettes](https://github.com/gbdev/pandocs/blob/master/src/Palettes.md), [MBC2](https://github.com/gbdev/pandocs/blob/master/src/MBC2.md), [MBC3](https://github.com/gbdev/pandocs/blob/master/src/MBC3.md), [MBC5](https://github.com/gbdev/pandocs/blob/master/src/MBC5.md) (read 2026-10-10; MEDIUM-HIGH, community synthesis with its own TODO markers)
- [Gekkio, Game Boy: Complete Technical Reference](https://gekkio.fi/files/gb-docs/gbctr.pdf) (rev. 192 referenced by v0.1 research; pre-CGB emphasis, so CGB statements here rely on Pan Docs and test authors)
- [BGB RTC save format note](https://bgb.bircd.org/rtcsave.html) (44/48-byte footer, sentinel timestamp)
- [Mooneye test suite](https://github.com/Gekkio/mooneye-test-suite) (`emulator-only/mbc2`, `emulator-only/mbc5`, `misc/boot_*`, `misc/bits/unused_hwio-C`)
- [SameSuite](https://github.com/LIJI32/SameSuite) and its [APU README](https://github.com/LIJI32/SameSuite/blob/master/apu/README.md) (CGB-E pass sets, PCM glitch on CGB-C and earlier)
- [c-sp game-boy-test-roms howtos](https://github.com/c-sp/game-boy-test-roms) (rtc3test, mbc3-tester, same-suite, age conventions, compat-mode shade values)
- [rtc3test](https://github.com/aaaaaa123456789/rtc3test), [age-test-roms](https://github.com/c-sp/age-test-roms), [cgb-acid2](https://github.com/mattcurrie/cgb-acid2), [dmg-acid2](https://github.com/mattcurrie/dmg-acid2), [Mealybug Tearoom Tests](https://github.com/mattcurrie/mealybug-tearoom-tests), [MBC3-Tester-gb](https://github.com/EricKirschenmann/MBC3-Tester-gb)
- [Libbet and the Magic Floor](https://github.com/pinobatch/libbet) (zlib; release v0.08; header inspected locally)
- Project: `.planning/PROJECT.md`, `.planning/research/FEATURES.md`, `.planning/research/HARDWARE-AND-VALIDATION.md`, `include/gabbaboy/gabbaboy.h`, `docs/cartridge-and-saves.md`, `docs/native-integration.md`
- SameBoy ([features](https://sameboy.github.io/features/)) as comparison oracle only; its source was not inspected this session, so every "verify in SameBoy" item above is open work, not a finding.
