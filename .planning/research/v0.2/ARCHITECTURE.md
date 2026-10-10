# Architecture Research: v0.2 Color & Cartridge Breadth

**Domain:** Game Boy / Game Boy Color emulator core, subsequent-milestone integration
**Researched:** 2026-10-10
**Confidence:** MEDIUM overall. Integration points are HIGH (read directly from `src/core/gabbaboy.c`, `include/gabbaboy/gabbaboy.h`, `docs/cartridge-and-saves.md`, `src/player/`). Hardware timing claims (speed-switch stall length, HDMA block cost, palette-RAM blocked-write auto-increment, CGB-E APU deltas) are recalled from Pan Docs and sibling-emulator behavior and were NOT re-verified against primary sources in this pass. Each is tagged `[VERIFY]` and belongs in the phase-level research gate (D-025: best-supported deterministic model, uncertainty stated).

Scope: only what the new features need. The v0.1 base architecture in `../ARCHITECTURE.md` still holds (half-dot `uint64_t` timeline, instance-owned machine, no hidden globals).

## Current-source facts that drive the design

Everything lives in one translation unit, `src/core/gabbaboy.c` (2305 lines, built as `gabbaboy_core` from a single source in `CMakeLists.txt:23`). Findings that shape v0.2:

| Fact | Location | Consequence |
|---|---|---|
| Whole machine is one `struct gbb_instance` with fixed arrays: `wram[8192]`, `vram[8192]`, `frame_working/frame_completed[uint8_t x 23040]` | struct at top of file | CGB banking and RGB555 frames change array shapes; all other code indexes these directly (`ppu_tile_color`, `ppu_background_color`, `dma_source_read`, `gbb_peek_ram`, `read8`, `write8`) |
| Single `advance_devices_to(m, target)` loops one **half-dot** at a time and ticks timer/serial/divider/APU/OAM-DMA/PPU in a fixed order | ~line 1455 | The right place to hook speed-dependent divider rate, HDMA byte scheduling, and nothing else. No per-half-dot RTC work (see below) |
| CPU cost is `decode()` ticks (multiples of 8 half-dots per M-cycle); bus offsets in `execute()` are literals (`8,16,24,...`); `instruction_cost(m, d)` already takes `m` and ignores it | ~1775-1840, 1979-2065 | Double speed is a scale at three choke points (`instruction_cost`, `bus_read`/`bus_write` offset, interrupt/halt literals `40u`/`8u`), not a rewrite of `execute()` |
| `read8`/`write8` are long `if (address == ...)` chains; DMG-only register set; `read_supported()` is a **fail-closed allow-list** used by `gbb_run_internal` to return `GBB_STOP_UNSUPPORTED_BUS` | ~615, 735, 959 | Every new CGB register and every new cartridge RAM window must be added to `read_supported` or CGB games stop immediately with UNSUPPORTED_BUS |
| Mapper logic is `cartridge_is_mbc1(m)` tests inline in `read8`, `write8`, `read_supported`; `mbc1_*` fields live in the instance; battery eligibility is hard-coded `cartridge_type == 0x03u` in `has_battery_ram` and in the `write8` generation bump | ~406-430, 739-768, 1731 | No mapper seam exists. Introduce one before adding three mappers |
| `validate_header` accepts only type `$00` and `$01-$03`; `GBB_MAX_ROM_SIZE` is 2 MiB; RAM codes only `$02`/`$03`; error `GBB_UNSUPPORTED_RAM_SIZE` | ~1634-1674, line 404 | Needs a type table (kind, RAM, battery, RTC, rumble), RAM codes `$04/$05`, ROM size codes to `$08` (8 MiB for MBC5) |
| Profile is `typedef enum { GBB_PROFILE_DMG_CPU_B = 1 }`; `gbb_create` rejects anything else with `GBB_UNSUPPORTED_PROFILE`; player/runner hard-code `GBB_PROFILE_DMG_CPU_B` at 5+ call sites | header; `src/player/main.c:143,491,900,1887`; `src/runner/main.c:187,239` | Enum extension is append-only and already has an error path. Hosts need a ROM probe so they can choose the profile |
| PPU is a per-output-pixel compositor reading `m->vram` / `bgp` / `obp*` at output time (`ppu_pixel_shade`) with a modeled FIFO only for timing | ~1049-1160, 1257-1302 | Palette RAM and attribute fetch slot into the compositor; mid-line palette writes take effect on the next pixel for free |
| `ppu_set_mode()` is the single place every STAT mode transition passes | ~368 | Natural HBlank-HDMA trigger and mode-3 palette-access gate |
| `gbb_copy_frame` returns one DMG shade byte per pixel (`[0,3]`) | header + ~1572; player `main.c:626` | Needs a second, color output format; cannot be silently repurposed |
| Battery API is raw RAM bytes, exact-size, `GBB_NO_BATTERY` for non-`$03`; player v1 envelope = `GBBBSAVE`, version, SHA-256, type, RAM length (8192/32768 only), CRC-32 | `docs/cartridge-and-saves.md`, `src/player/session.c` | Backward compatibility is only at stake for the player envelope and for MBC1; MBC2/3/5 saves are new |
| STOP is `case 0x10: m->pc=pc+2; m->stopped=1;` then run loop resets divider and returns `GBB_STOP_STOPPED`; `stopped` branch advances `time_half_dots` **without** ticking devices | ~2036, 2220, 2112 | Speed switch must be a different path from STOP-sleep: devices (PPU/APU) keep running during the switch pause |
| Instance already has private test seams `gbb_test_*` (observers, CPU snapshot, audio kernel) | tests/*.c | Add CGB-specific seams the same way (never public) |

## Recommended architecture changes

```text
public gabbaboy.h  (+profile, +rom probe, +cart info, +rgb555 frame, +rtc catch-up)
        |
   machine (src/core/gabbaboy.c: lifecycle, run loop, CPU stall, advance_devices_to)
        |
   +----+-----------+-------------+----------------+----------------+
   |    |           |             |                |                |
 bus   cartridge   ppu          dma/hdma         timing domains   apu
 (region  (NEW      (+CGB attrs   (OAM DMA +       (cpu_scale,     (+CGB-E
 decode,  src/core/  palettes,     NEW HDMA/GDMA    divider rate,   deltas,
 +banked  cartridge. +rgb555)      state machine)   serial rate)    +DIV mask)
 WRAM/    c/.h
 VRAM)    kind enum
          +RTC)
```

Do not introduce vtables or function pointers into the instance: they break later native serialization (STATE-01) and sanitizer-friendly replay. Use enum + `switch`. Group new state into plain-integer sub-structs (`cart_state`, `rtc_state`, `cgb_state`, `hdma_state`) so v0.3 can serialize field-by-field and each has a single `*_reset()`.

### New vs modified components

| Component | Status | File(s) | What changes |
|---|---|---|---|
| Cartridge module | **NEW** | `src/core/cartridge.c`, `src/core/cartridge.h` (private header) | `cart_kind` enum (`ROM_ONLY, MBC1, MBC2, MBC3, MBC5`), type-table (`cart_type_info(type)` -> kind, has_ram, has_battery, has_rtc, has_rumble), `cart_validate_header`, `cart_read_rom`, `cart_write_control`, `cart_read_ram`, `cart_write_ram` (returns changed flag for battery generation), `cart_battery_*`. Moves all `mbc1_*` code out of `gabbaboy.c`. Add to `add_library(gabbaboy_core ...)` and the source list hashed at `CMakeLists.txt:48` |
| RTC module | **NEW** | same files (section) or `src/core/rtc.c` | Lazy, emulated-time-derived MBC3 clock; export/import of a fixed little-endian block; host catch-up |
| Profile/mode state | **NEW** | `gabbaboy.c` struct + `reset_state` | `profile`, `exec_mode` (DMG / CGB / CGB-in-DMG-compat), `is_cgb(m)` helper, `apply_post_boot(m)` table keyed by profile+mode |
| CGB register file | **NEW** (inside bus) | `read8`/`write8`/`read_supported` | FF4C KEY0 (locked after boot), FF4D KEY1, FF4F VBK, FF51-FF55 HDMA, FF56 RP stub, FF68-FF6B palette index/data, FF6C OPRI, FF70 SVBK, FF72-FF75, FF76/FF77 PCM12/34. All gated by `is_cgb(m)` so DMG profile still reads `$FF` / ignores |
| Banked memory | **MODIFIED** | `wram[8192]` -> `wram[8][4096]`; `vram[8192]` -> `vram[2][8192]` plus `vram_bank`, `wram_bank` | Touches `read8`, `write8`, `dma_source_read`, `gbb_peek_ram` (must keep DMG answers), echo RAM (E000-EFFF = bank 0, F000-FDFF = selected bank), `ppu_tile_color`, `ppu_background_color`, `reset_state` memsets |
| Palette RAM | **NEW** | `bg_pal[64]`, `obj_pal[64]`, `bcps`, `ocps` | CPU path in bus, compositor path in PPU |
| PPU color path | **MODIFIED** | `ppu_tile_color`, `ppu_background_color`, `ppu_object_color`, `ppu_pixel_shade`, `ppu_transfer_dot`, `ppu_scan_object` | BG map attribute fetch from VRAM bank 1, tile bank/flip/palette, BG-to-OBJ priority (attr bit 7, LCDC bit 0 master priority in CGB mode), OBJ attr bit 3 bank + bits 0-2 palette, OBJ priority by OAM index when OPRI says CGB (DMG-compat keeps lowest-X rule). Frame store becomes `uint16_t` words |
| Compat-mode palette mapping | **NEW** (small) | PPU | In CGB-in-DMG-compat mode `BGP/OBP0/OBP1` select shade 0-3, which indexes CGB palette RAM palettes (BG pal 0, OBJ pal 0/1). Bootless default palette is an explicit documented policy (see Open Decisions) |
| Speed domains | **MODIFIED** | `instruction_cost`, `bus_read`, `bus_write`, `enter_interrupt`, run-loop literals, `advance_devices_to` divider block, `apu_sequencer_clock` call sites, serial counter, OAM DMA period, `timer_reload_remaining = 8u` | Add `double_speed` (0/1) and one helper `cpu_ticks(m, ticks) = ticks >> m->double_speed` |
| CPU stall | **NEW** | run loop + new fields `cpu_stall_half_dots`, `cpu_stall_kind` | One mechanism used by speed switch and GDMA/HDMA: CPU frozen, **devices advance**. Distinct from the existing `stopped` branch which freezes devices |
| HDMA/GDMA | **NEW** | `hdma_*` fields; `hdma_advance_half_dot` called next to `dma_advance_half_dot`; trigger in `ppu_set_mode(…, 0)` | See below |
| STOP / KEY1 | **MODIFIED** | `case 0x10` in `execute`, post-execute `stopped` handling | If CGB and KEY1 armed: toggle speed, enter stall, do not set `stopped` |
| APU CGB-E deltas | **MODIFIED** | `apu_power_off`, `read8/write8` wave RAM and NR1x length writes while powered off, `apu_sequencer_clock` call sites, PCM12/PCM34 | Profile-gated; research flagged |
| Frame API | **MODIFIED/NEW** | header + `gbb_copy_frame` + new `gbb_copy_frame_rgb555` | Legacy shade API stays DMG-profile only |
| Public header | **MODIFIED** | `include/gabbaboy/gabbaboy.h` | Append-only additions listed in "Public API" |
| Player | **MODIFIED** | `src/player/main.c`, `presentation.c`, `session.c` | Profile selection via ROM probe, RGB555 presentation, save envelope v2 for RTC, wall-clock catch-up policy |
| Runner | **MODIFIED** | `src/runner/main.c` | Profile option; hard-coded `GBB_PROFILE_DMG_CPU_B` at two sites |
| Acceptance harness | **NEW** | `tests/acceptance/` | Scripted input + frame/audio digest assertions against a rights-clear ROM |
| Tests | **NEW/MODIFIED** | `tests/test_cartridge.c`, `test_battery.c`, `test_loader.c`, new `test_mbc5.c`, `test_mbc2.c`, `test_mbc3_rtc.c`, `test_cgb_*.c`, `fuzz_core.c` bounds | `tests/expected-tests.txt` inventory updates |

## Public API (append-only)

Header additions, all backward compatible with the v0.1 `GabbaBoy::core` consumers (existing symbols keep behavior on `GBB_PROFILE_DMG_CPU_B`):

1. **Profile:** add `GBB_PROFILE_CGB_CPU_E = 2` to `gbb_profile`. `gbb_create` already returns `GBB_UNSUPPORTED_PROFILE` for unknown values, so older code paths remain correct. Name the profile per D-008 (`CPU-CGB-E`); do not add a generic `GBB_PROFILE_CGB`. Physical model (profile), execution mode, and presentation palette stay separate concepts (`../ARCHITECTURE.md` "Hardware model and boot policy").
2. **ROM probe (no instance):** `gbb_error gbb_probe_rom(const uint8_t *rom, size_t size, gbb_rom_info *out)` reporting mapper kind, ROM/RAM sizes, battery/RTC/rumble flags, and CGB flag (`$143`: none, `$80` supports CGB, `$C0` CGB-only). The player and runner call it to pick the profile before `gbb_create`. Reuses the same `cart_validate_header`, so validation is not duplicated.
3. **Instance queries:** `gbb_get_profile`, `gbb_get_execution_mode` (`GBB_MODE_DMG`, `GBB_MODE_CGB`, `GBB_MODE_CGB_DMG_COMPAT`), `gbb_get_cartridge_info`. Execution mode on a CGB profile is derived from `$143` at `gbb_load_rom`/reset and recorded; it is not a host toggle (a DMG game on a CGB is a CGB in compatibility mode). A CGB-only ROM on the DMG profile loads as the real DMG would (no check) but returns a flagged info field so a host can warn.
4. **Color frame:** `gbb_copy_frame_rgb555(instance, uint16_t *pixels, capacity_pixels, pitch_pixels, gbb_frame_info*)` with identical validation and overlap rules as `gbb_copy_frame` (copy that function's checks, do not weaken them). Canonical unfiltered RGB555 (bit 15 clear). Color correction stays in the host (`presentation.c`). `gbb_copy_frame` keeps shade semantics and returns `GBB_UNSUPPORTED_PROFILE` (or a new `GBB_WRONG_FRAME_FORMAT`) on a CGB profile rather than inventing a conversion. Internally store `uint16_t frame_working[23040]` / `frame_completed[23040]` as a "native pixel word": shade index 0-3 on DMG, RGB555 on CGB. +~46 KB instance size is acceptable.
5. **RTC (see below):** `gbb_rtc_catch_up(instance, uint64_t elapsed_seconds)` and cartridge-info flag `has_rtc`.
6. New errors appended after `GBB_FRAME_NOT_READY` (enum values are ABI): e.g. `GBB_RTC_NOT_PRESENT`, optionally `GBB_WRONG_FRAME_FORMAT`.
7. `gbb_peek_ram` keeps its contract; on CGB it returns the currently mapped bank (documented). Add a `gbb_peek_ram_bank` only if tests need it.

## Integration detail by feature

### 1. Hardware profile and mode (`gbb_profile`, `reset_state`)

- Add `uint8_t profile; uint8_t exec_mode;` to `gbb_instance`; set in `gbb_create` (profile) and `gbb_load_rom` (mode from `rom[0x143]`). `gbb_create` currently runs `reset_state(m)` with no ROM; `reset_state` already branches on `m->rom != NULL` for the F register, so the mode is naturally resolved when `gbb_load_rom` calls `reset_state` a second time.
- Replace the scattered literals in `reset_state` (`a=0x01`, `f`, `div=0xAB`, `divider_counter=0xAB00`, `lcdc=0x91`, `bgp=0xFC`, ...) with `apply_post_boot(m)` selecting among three tables: DMG-CPU-B (existing values, **must be byte-identical** so all 184 v0.1 tests pass unchanged), CGB-E/CGB mode, CGB-E/DMG-compat. CGB post-boot register and DIV/LY phase values are `[VERIFY]` against Pan Docs "Power-Up Sequence" and SameBoy/mGBA CGB-E tables; "bootless" remains an explicit declared limitation (D-008).
- `is_cgb(m)` gates: CGB registers in `read8/write8/read_supported`, banked memory, palettes, speed switch, HDMA, CGB-E APU deltas. DMG-compat additionally locks most CGB registers after the (virtual) boot; the PPU uses the DMG compositor rules but palette RAM output.
- Do not add a "DMG-with-CGB-features" hybrid. Three explicit combinations only: (DMG, DMG), (CGB-E, CGB), (CGB-E, DMG-compat).

### 2. Cartridge mapper dispatch

- Extract before extending. Step 1 is a pure refactor: move `mbc1_rom_bank`, `mbc1_ram_offset`, the MBC1 branch of `write8`, `reset` of the MBC1 registers, and `validate_header` into `cartridge.c` behind `cart_*` functions with identical behavior; the v0.1 test suite (`test_cartridge.c`, `test_battery.c`, `test_loader.c`, `test_loader_fuzz.c`) is the safety net. Keep `recognized_mbc1m_candidate` and `GBB_UNSUPPORTED_CARTRIDGE_VARIANT` behavior.
- `read8` for `<0x8000` becomes `cart_read_rom(&m->cart, address)`; `A000-BFFF` becomes `cart_read_ram`; control writes become `cart_write_control(&m->cart, &m->rtc, address, value, m->time_half_dots)`. The rest of `read8` is region-decoded (split the long `if` chain into `if (address < 0x8000) ... else if (address < 0xA000) ...` first, then IO). That also removes the repeated range tests that `read_supported` duplicates.
- `read_supported`'s `A000-BFFF` clause currently means "RAM present or MBC1". Replace by `cart_ram_window_mapped(&m->cart)` so MBC2 (512x4-bit built-in RAM, header RAM code `$00`) and MBC3-with-RTC-only (no RAM, types `$0F`) are supported addresses.
- **Mappers (all `[VERIFY]` bank-register semantics against Pan Docs MBCs page and mapper-specific test ROMs):**
  - MBC5 (types `$19-$1E`): 9-bit ROM bank (`$2000-$2FFF` low 8, `$3000-$3FFF` bit 8), bank 0 is selectable at `$4000`, no zero-translation (unlike MBC1), RAM bank 4 bits (rumble carts use bit 3 as the motor, so mask to 3 bits, and expose via info only), up to 8 MiB ROM and 128 KiB RAM. Raises `GBB_MAX_ROM_SIZE` from 2 MiB; recheck every size computation and the loader fuzz bounds (`GBB_ROM_TOO_LARGE` threshold changes by mapper).
  - MBC2 (types `$05/$06`): bank register and RAM-enable share `$0000-$3FFF`, selected by address bit 8; 512x4-bit RAM mirrored through `$A000-$BFFF` (upper nibble reads as 1s); header RAM size code is `$00` but the loader must allocate 512 bytes and the battery blob is 512 bytes.
  - MBC3 (types `$0F-$13`): 7-bit ROM bank (0 -> 1), RAM bank `$00-$03` or RTC select `$08-$0C`, latch via `$00` then `$01` at `$6000-$7FFF`. MBC30 (4 MiB ROM, 64 KiB RAM, 8 RAM banks) is out of scope unless the acceptance corpus demands it; fail with `GBB_UNSUPPORTED_CARTRIDGE_VARIANT` as MBC1M does now.
- Type table drives battery eligibility: replace `cartridge_type == 0x03u` in `has_battery_ram` and the `write8` generation bump with `cart.has_battery`.
- `reset_state` currently resets mapper registers but retains RAM (`gbb_reset` doc: "retains the loaded ROM and cartridge RAM"). Preserve: mapper registers reset; RAM, battery generation and RTC counters persist across reset (RTC is a free-running crystal on real cartridges; resetting the console does not stop it).

### 3. Double speed and the event timeline

The timeline is already the right unit: one half-dot is one tick of the 8.388608 MHz master; dot rate (PPU) is 2 half-dots and constant; the CPU T-cycle is 2 half-dots in normal speed and 1 in double speed. So double speed is a **change to what the CPU-side and divider-side devices count**, not a rescale.

| Domain | Normal | Double speed | Where in current source |
|---|---|---|---|
| PPU dot (`ppu_half_phase`) | every 2 half-dots | unchanged | `advance_devices_to` tail; no change |
| APU channel timers, 48 kHz sample generation | master half-dots | unchanged `[VERIFY]` | `advance_devices_to` APU block; no change |
| CPU instruction cost and bus offsets | `ticks` (8 per M-cycle) | `ticks >> 1` (4 per M-cycle) | `instruction_cost`, `bus_read`/`bus_write` (scale `offset`), `enter_interrupt` (`8u`, `push16(16,24)`), run-loop `40u` and halted `8u` |
| Divider / `divider_counter` increment | every 2 half-dots (`divider_phase` toggles) | every half-dot | divider block at ~1480 |
| TIMA overflow reload delay | `timer_reload_remaining = 8u` half-dots | `4u` | `timer_increment` |
| APU frame sequencer clock (DIV falling edge) | bit 12 (`0x1000u`) | bit 13 (`0x2000u`) so it stays 512 Hz | `advance_devices_to` and `write8(0xFF04)` both hard-code `0x1000u`; introduce `apu_div_mask(m)` |
| Internal serial clock (`serial_edge_remaining = 1024u`) | 1024 half-dots/bit | 512 (and CGB fast-serial SC bit 1: 32 -> 16) | `write8(0xFF02)`, `advance_devices_to` serial block |
| OAM DMA byte period (`GBB_DMA_BYTE_PERIOD_HALF_DOTS = 8`) | 8 | 4 `[VERIFY]` | `dma_advance_half_dot` |
| HDMA byte pair period | 8 half-dots / 2 bytes | same (constant in master time) `[VERIFY]` | new |
| RTC | derived from master half-dots | unchanged | lazy; not in the loop |

Implementation guidance:

- Add `uint8_t double_speed;` and `static inline uint64_t cpu_ticks(m, t) { return t >> m->double_speed; }`. All literal offsets in `execute()` are multiples of 8, so the shift is exact and **`execute()` does not need editing**; scale inside `bus_read`/`bus_write` (the `offset` parameter) and in `instruction_cost`. `bus_write`'s TMA reload special case compares `timestamp - time_half_dots == timer_reload_remaining`; both sides are in master half-dots, so keep it consistent by scaling `timer_reload_remaining` at reload-arm time.
- The existing preflight (`cost > budget_half_dots - consumed`) and audio preflight use master half-dots already; they continue to work with scaled cost.
- Replace the interrupt-dispatch and halt literals with `cpu_ticks(m, 40u)` / `cpu_ticks(m, 8u)`.
- **Speed switch** (`STOP` with KEY1 bit 0 armed on CGB profile, `[VERIFY]` joypad-held and interrupt-pending edge cases flagged by `../ARCHITECTURE.md`): in `execute()` `case 0x10`, if `is_cgb(m) && key1_armed` then toggle `double_speed`, clear the arm bit, reset DIV (the current STOP path resets `divider_counter`; keep equivalent), set `cpu_stall_half_dots = SPEED_SWITCH_STALL` and `cpu_stall_kind`; **do not** set `stopped`. The stall length (approx. 2050 M-cycles in Pan Docs, `[VERIFY]`; expressed in master half-dots so it is speed-independent) is a named constant with a source comment.
- **CPU stall** is a new top-of-loop branch in `gbb_run_internal`, parallel to the existing `stopped` branch, but it calls `advance_devices_to` (PPU/APU/timer-side keep running; the CPU does not fetch). Process in bounded quanta (<= 64 half-dots) each preflighted against remaining budget and `audio_preflight`, returning to the caller with the same stop reasons as other idle progress. Progress lives in plain integers so v0.3 can snapshot mid-stall. Count stall time in `consumed_half_dots`.
- DIV-reset side effects interact with `timer_set_signal` and the APU falling edge; reuse the `0xFF04` write code path rather than duplicating.

### 4. HDMA / GDMA stealing CPU time

- State (all integers): `hdma_src` (16), `hdma_dst` (16, forced into `$8000-$9FF0`), `hdma_blocks_remaining` (0-128), `hdma_mode` (idle / general / hblank), `hdma_block_byte` (0-15), `hdma_block_pending`, `hdma_phase`, `hdma_hblank_armed_line` to prevent two blocks in one HBlank.
- **Registers:** `FF51-FF54` write-only, `FF55` write starts GDMA (bit 7 = 0) or arms HBlank DMA (bit 7 = 1); writing bit 7 = 0 while an HBlank transfer is active cancels it; read returns remaining-1 with bit 7 set when stopped `[VERIFY]`. Add all five to `read_supported`.
- **Scheduling:** HDMA transfer is performed one byte pair per 8 half-dots from `hdma_advance_half_dot(m)`, called in `advance_devices_to` next to `dma_advance_half_dot` so its order versus PPU is the same deterministic order as OAM DMA. A bulk copy at the trigger would violate the `dma` boundary rule in `../ARCHITECTURE.md` ("no instantaneous bulk copy shortcut").
- **CPU stealing:** when GDMA is written, or when `ppu_set_mode(m, 0)` fires on a visible line (`ly < 144`, LCD on) with an armed HBlank transfer, set `cpu_stall_half_dots` for the block (16 bytes = 64 half-dots, `[VERIFY]` plus a 1 M-cycle startup). The run loop's stall branch (shared with the speed switch) advances time. The CPU instruction that was already in flight completes first (the HDMA check happens only at the instruction boundary at the top of the loop, matching the existing `dma_start_pending` boundary at ~2212).
- **Source/dest access:** source reads use a new `hdma_source_read(m, addr)` that dispatches ROM (`cart_read_rom`), cartridge RAM, and banked WRAM, and returns `$FF` for illegal ranges (`$8000-$9FFF`, `$E000-$FFFF`) `[VERIFY]`. Destination writes VRAM at the current `vram_bank`. This also lets the OAM-DMA source function `dma_source_read` stop returning `$FF` for ROM on the CGB profile (D-024's narrow `$8000-$DFFF` envelope was a DMG-CPU-B policy; the CGB source range needs its own evidence note).
- **Edge cases that need hardware-backed or oracle tests:** LCD off during HBlank DMA, HALT/STOP during a pending block, GDMA with mode 3 active (are VRAM writes blocked), a speed switch while HDMA is pending, a source crossing a bank boundary, and the ordering of the HDMA byte-write versus the PPU's VRAM read in the same half-dot.

### 5. VRAM and WRAM banking in the bus

- `vram[2][8192]` with `vram_bank` (FF4F bit 0, reads `$FE | bank`); `wram[8][4096]` with `wram_bank` (FF70 bits 0-2, 0 -> 1). DMG profile never changes the banks, so DMG behavior is mechanically unchanged: bank 0 for VRAM, bank0/bank1 for `C000-CFFF`/`D000-DFFF`.
- Addresses: `C000-CFFF` bank 0; `D000-DFFF` bank `wram_bank`; echo `E000-EFFF` -> bank 0; `F000-FDFF` -> selected bank.
- Touch list: `read8`, `write8`, `dma_source_read`, `gbb_peek_ram`, `reset_state` memsets, plus every PPU VRAM accessor that now takes a bank argument. Use two tiny helpers (`wram_ptr(m, addr)`, `vram_byte(m, bank, off)`) rather than open-coding offsets in a dozen places.
- CPU VRAM access gating (`cpu_vram_access_allowed`: LCD off or not mode 3) is unchanged and applies to both banks. Bank 1 is only reachable when `is_cgb(m)` and not locked in compat mode.
- `ppu_tile_color` currently bounds `tile_base + 15 < 0x1800` and indexes `m->vram[address]`; add `bank` and keep the bound.

### 6. Palette RAM and access restrictions

- Storage: `bg_pal[64]`, `obj_pal[64]` bytes (8 palettes x 4 colors x 2 bytes, little-endian RGB555), `bcps`/`ocps` index registers (bit 7 auto-increment, 6-bit index).
- CPU access: `FF69`/`FF6B` read/write palette data at the index; reads return `$FF` and writes are dropped in **mode 3 with LCD on**, reusing `cpu_vram_access_allowed(m)`. Whether the index still auto-increments on a blocked write is `[VERIFY]` (Pan Docs and SameBoy disagree historically); implement the best-supported model and state it (D-025). The compositor reads palette RAM directly, unaffected by the CPU gate.
- Compositor: `ppu_pixel_shade` becomes `ppu_pixel_word(m, x)` returning RGB555 on CGB profiles. In DMG-compat mode: shade = DMG palette lookup (`ppu_palette_shade`, unchanged), then RGB555 from `bg_pal` palette 0 / `obj_pal` palette 0 or 1. Bootless compat default palettes are policy (below), not Nintendo's boot-ROM table (AGENTS.md forbids shipping boot ROMs; the title-hash palette table is boot-ROM data and must not be copied without a rights decision).
- Add FF68-FF6B, FF6C to `read_supported`. DMG profile: unmapped.

### 7. RTC derives time from emulated cycles (deterministic)

- Crystal arithmetic works out exactly: the RTC crystal is 32,768 Hz; the master timeline is 8,388,608 half-dots per second; so **1 RTC second = 8,388,608 half-dots = 2^23**, with no fractional drift, and it is independent of CPU speed mode because the master timeline does not rescale.
- **Lazy evaluation, not per-tick.** Do not add RTC work to `advance_devices_to` (it already loops once per half-dot; measured hot path per D-016). Store `rtc.sub_half_dots` (0..2^23-1), the five counters (S, M, H, DL, DH with halt bit 6 and day-carry bit 7), the latched copy of the five, `latch_state`, and `rtc.synced_at` (a master `time_half_dots` value). `rtc_sync(rtc, now)` adds `now - synced_at` using checked 64-bit arithmetic, carries seconds -> minutes -> hours -> 9-bit days, sets the sticky carry on day overflow, and is a no-op when halted (it just moves `synced_at`).
- Sync points: on the latch write (`00`->`01`), on any RTC register write or halt toggle (sync first, then modify), and on battery export. `read8` of the RTC window returns the latched byte, so reads never need time. `write8` runs after `bus_write` has already called `advance_devices_to`, so `m->time_half_dots` equals the access timestamp; pass it into `cart_write_control`.
- Reset, ROM replacement: reset preserves RTC state and re-bases `synced_at = 0` (reset clears `time_half_dots` to 0, so re-base before clearing; this is a real hazard); ROM replacement starts a fresh clock.
- Writing RTC seconds also resets the sub-second prescaler on hardware `[VERIFY]`; model it and document.
- **Replay determinism:** emulated time only; the same event log and input produce the same RTC. Fast-forward therefore speeds the clock; that is the documented trade-off for determinism (D-012).

#### Adapter policy for wall-clock catch-up

The core never calls `time()`. The adapter supplies elapsed real seconds at a well-defined boundary:

- `gbb_rtc_catch_up(instance, uint64_t elapsed_seconds)` is callable only between `gbb_run*` calls (an instruction boundary by construction). It syncs to the current emulated time, then adds `elapsed_seconds` to the counters (honoring halt: no advance when halted; overflow sets the day-carry flag; saturation at a documented cap so a hostile value is bounded work; arithmetic is O(1) by division, not a loop). It does not move `time_half_dots`, so replay logs stay consistent: a recorded replay stores the catch-up call and its argument as input, like any other host event.
- Policy owned by the host, documented in `docs/cartridge-and-saves.md`: (1) on save, the host records `saved_at` from its wall clock in its envelope, not in the core blob; (2) on load, `elapsed = now - saved_at`; (3) negative elapsed (clock moved backward) -> 0 and surface a warning, never subtract; (4) cap large gaps (e.g. > 2^31 s) and surface a warning; (5) never catch up when restoring a replay/snapshot (v0.3 states must not silently catch up, per `../ARCHITECTURE.md`); (6) only call for carts where `has_rtc` is true. A snapshot-restore later must skip catch-up entirely, so make the catch-up a deliberate host call rather than an import side effect.
- The core export has no timestamp precisely so that the core remains wall-clock free.

### 8. Battery file format and backward compatibility

Two layers: the **core blob** (what `gbb_copy_battery`/`gbb_import_battery` move) and the **player envelope**.

**Core blob (recommended):** keep one opaque persistent blob so hosts handle one thing. Layout is `RAM bytes` for non-RTC cartridges (**byte-identical to v0.1** for MBC1 type `$03`), and `RAM bytes || RTC block` for RTC cartridges. RTC block: fixed-size, explicit little-endian, no struct dump: block version byte, `sub_half_dots` (u32), live S/M/H/DL/DH (5 bytes), latched S/M/H/DL/DH (5 bytes), latch state byte; about 17 bytes, reserved for forward extension by version. `gbb_battery_size` returns the total blob size; `GBB_BATTERY_SIZE_MISMATCH` still means "not exactly the expected size". For RTC-only carts (`$0F`, no RAM) the blob is the RTC block alone, so `has_battery_ram` becomes `cart.has_battery` and `gbb_battery_size` can return a non-RAM size. The doc and header comment ("raw RAM bytes") must be updated.
Alternative considered: separate `gbb_rtc_export/import` calls. Rejected as the default because the host would need two parallel persistence paths, two generation notions, and a larger chance of RAM/RTC skew. Reconsider if Playstead wants to treat RAM and clock independently.

**Generation counter:** `battery_generation` bumps on changed RAM bytes as today and on guest RTC writes/halt toggles/latch changes. It does **not** bump per elapsed second (otherwise the player's quiet-period save would never settle). Consequence: the RTC value in the last saved file lags real time only by elapsed time since the last save; the wall-clock catch-up repairs that lag on next load. Final saves on quit/reset/replace (already exist) capture the live clock.

**MBC2:** blob = 512 bytes, one nibble per byte with the upper nibble normalized to `$F` on export; on import mask-then-OR so a malformed file cannot hold illegal upper bits (document).

**Player envelope (`src/player/session.c`, `docs/cartridge-and-saves.md`):**

- v1 (shipped): `GBBBSAVE`, version `1`, SHA-256, type byte, RAM length (accepts exactly 8192 or 32768), CRC-32, payload.
- Rule: **a cartridge that could have written a v1 file keeps writing v1.** MBC1 (and MBC5/MBC2 without RTC) payloads are the raw core blob, so use v1 with the type byte now holding the true header type and the length check widened to the legal set `{512, 8192, 32768, 65536, 131072}`. Old players safely reject the new lengths and types (never producible before). All v1 files continue to load.
- v2 only for RTC cartridges: v1 header fields plus `host_saved_at_unix_seconds` (u64 LE) and the payload is RAM||RTC block; the CRC covers the whole payload. The player refuses a v2 file whose type byte does not declare RTC. The v1 reader must reject version 2 cleanly (it already rejects unsupported versions) and the v2 reader accepts v1 (with no RTC) only for non-RTC types.
- The identity key (SHA-256 + type + RAM size) is unchanged; add blob length to it only if the RAM size alone cannot disambiguate.
- Keep the existing recovery semantics (`.recovery-...` rename, never auto-load), atomic temp-file replacement, and bounded, no-symlink reads. Also update `limitations.h` text so the player does not claim "MBC1 only".
- No arbitrary `.sav` import; if interchange with the de-facto 48-byte RTC trailer (VBA/BGB style) is wanted, build it as a separate tool-level adapter, not a core guess (`../ARCHITECTURE.md`).

## Data-flow changes

```text
v0.1:  CPU/bus -> read8/write8 -> {rom/mbc1, vram, wram, io}     PPU: vram,bgp -> shade u8 -> frame u8
v0.2:  CPU/bus -> read8/write8 -> region decode ->
          cart_{read,write}_*  (mapper kind switch, rtc lazy sync from m->time_half_dots)
          vram[bank], wram[bank], palette RAM, CGB IO (gated is_cgb)
       run loop: [interrupt | halt | stopped | NEW cpu_stall | instruction]
          cpu_stall(devices advance, CPU frozen): speed switch, GDMA, HBlank block
       advance_devices_to(half-dot): divider(rate by speed), serial, APU, OAM DMA, NEW hdma byte pair, PPU
       PPU: vram[bank0/1] + attrs + palette RAM -> pixel word -> frame u16 -> gbb_copy_frame_rgb555
       battery: RAM [+ RTC block] -> gbb_copy_battery -> host envelope v1/v2 (+ host saved_at)
       RTC catch-up: host wall clock -> gbb_rtc_catch_up(elapsed_s) between runs
```

## Suggested build order (dependency-respecting)

Stop after each phase (D-002); each is independently verifiable and releasable.

| # | Phase | Delivers | Depends on | Why this position |
|---|---|---|---|---|
| 1 | **DMG game-level acceptance** | `tests/acceptance` harness, scripted input, frame/audio digests, rights-clear ROM, DMG-player proof | existing v0.1 only | Required first by milestone scope. It also finds DMG PPU/CPU/APU defects *before* they are confused with CGB regressions, and fixes the acceptance method (digests, input scripts) that CGB reuses. No core API change expected; if the chosen game needs MBC5/MBC3, pick a game whose cartridge is already supported |
| 2 | **Cartridge seam refactor (no behavior change)** | `cartridge.c/.h`, type table, `read8/write8/read_supported` region split, `has_battery` generalization | 1 (so acceptance can regress-test the refactor) | Highest regression risk per line moved; v0.1 test suite is the oracle. Must precede every new mapper and CGB bus work |
| 3 | **MBC5 + larger ROM/RAM matrix** | MBC5, 8 MiB limit, RAM codes `$04/$05`, rumble flag passthrough, loader fuzz bounds | 2 | Simplest new mapper; the majority of CGB titles use it, so CGB acceptance depends on it |
| 4 | **MBC2** | built-in 512x4-bit RAM, battery blob rule | 2 | Independent of RTC; small |
| 5 | **MBC3 banking + deterministic RTC + catch-up API + battery blob + player envelope v2** | `rtc` module, `gbb_rtc_catch_up`, blob layout, host policy doc | 2, ideally 3-4 (battery blob convention) | The only phase that couples emulated time to persistence; isolate it. Header/API additions land here |
| 6 | **Profile/mode scaffolding + bus banking + CGB registers** | `GBB_PROFILE_CGB_CPU_E`, `gbb_probe_rom`, `apply_post_boot`, `vram[2]`, `wram[8]`, VBK/SVBK, `read_supported` additions, DMG byte-identical gate | 2 (bus region decode), 3 (CGB games need MBC5) | DMG behavior must not move; add a DMG replay digest baseline before changing array shapes |
| 7 | **Color PPU path + palette RAM + RGB555 frame API + compat palettes + player color presentation** | attribute fetch, palettes, priorities, `gbb_copy_frame_rgb555`, `presentation.c` color | 6 | First point at which CGB output is visible; enables cgb-acid2-style checks (verify each fixture's license first) |
| 8 | **Double speed + CPU stall mechanism** | KEY1, `STOP` switch, `cpu_ticks`, divider/APU-mask/serial/OAM-DMA rates, stall branch | 6 | Run-loop change should land before HDMA reuses it. Timing-sensitive; needs Mooneye/SameSuite CGB tests (admission per D-013) |
| 9 | **HDMA / GDMA** | FF51-FF55, per-byte-pair scheduling, HBlank trigger in `ppu_set_mode`, source dispatch | 6, 7, 8 | Needs banking (dest), PPU modes, ROM/RAM source, and the stall mechanism with speed awareness |
| 10 | **CGB-E model differences + qualification** | APU/CPU/PPU CGB-E deltas, PCM12/34, OPRI, remaining registers, model applicability matrix | 6-9 | Last because tests need the complete feature surface; each delta ships with a declared model applicability and expected-failure reasons (AGENTS.md) |
| 11 | **CGB game-level acceptance + ledger, docs, release** | CGB acceptance (reuse harness from 1), support ledger update, docs, release scoped to tested corpus | all | Mirrors the DMG gate |

Parallelism (independent ownership): phases 3, 4 can run concurrently after 2. Phase 7's player color work can start against the frozen `gbb_copy_frame_rgb555` signature once phase 6 lands. Do not parallelize 8 and 9 (both edit the run loop and `advance_devices_to`).

## Anti-patterns to avoid

- **Per-half-dot RTC ticking.** The loop already runs once per half-dot; the RTC is derivable from a timestamp difference, so lazy sync is O(1) and keeps the hot path clean.
- **Function-pointer mapper table inside the instance.** Blocks serialization and is unnecessary for five mappers.
- **Implicit wall-clock in `gbb_import_battery`.** An import that "catches up" would also fire on v0.3 snapshot restore. Make catch-up an explicit separate call.
- **Rescaling the whole machine for double speed.** Breaks PPU/APU rates; only CPU-side and divider-side domains change.
- **Letting `STOP` double as the speed switch via the `stopped` branch.** That branch freezes all devices; speed switch must keep PPU/APU running.
- **Widening `read_supported` carelessly.** It is the safety net that turns undocumented I/O into `GBB_STOP_UNSUPPORTED_BUS` instead of silent wrong behavior; add each CGB register deliberately with a test.
- **Reusing `gbb_copy_frame` for color.** Silent semantic change of a shipped function; add a new function.
- **Embedding the Nintendo CGB boot-ROM title-hash palette table** to colorize DMG games (rights); use a documented default policy.
- **Bumping the player envelope version for all carts.** Strands users who need the older file; version only what changed.

## Cross-cutting risks (flag for phase research)

| Risk | Where | Mitigation |
|---|---|---|
| Hard-coded half-dot literals scattered in the core (`40u`, `8u`, `1024u`, `0x1000u`, `GBB_DMA_BYTE_PERIOD_HALF_DOTS`, `timer_reload_remaining = 8u`) | gabbaboy.c | grep inventory in phase 8 plan; each becomes `cpu_ticks` or a named per-speed constant with a test |
| DMG regression from array reshaping | phase 6/7 | add an output digest baseline (frame + audio hash over the acceptance and Mooneye ROMs) before the change and require equality after |
| Instance size growth (+~90 KB: WRAM +24 KB, VRAM +8 KB, frames +46 KB, palettes 128 B) | struct | `calloc` already; check `measure_core` baseline (D-016) and `tests/test_audio_no_alloc.c` unaffected |
| `reset_state` re-bases `time_half_dots = 0` while RTC stores absolute timestamps | phase 5 | re-base RTC at reset; unit test across reset |
| CGB-E timing claims lack primary hardware evidence | phases 8-10 | D-025 policy; record confidence and oracle disagreement; avoid claiming hardware qualification |
| Mid-stall and mid-HDMA state must be serializable | v0.3 | keep all state as integers in sub-structs now; add a "run N, stop, run M equals run N+M" metamorphic test across stalls |
| Fuzz / allocation bounds for 8 MiB ROMs | loader | update `fuzz_core.c` and `test_loader_fuzz.c` caps and `GBB_ROM_TOO_LARGE` per mapper |

## Open decisions for the roadmap/discuss step

1. **Compat-mode default palettes:** one fixed documented palette versus a small project-authored table; recommend one fixed documented palette, host-overridable later (presentation, not execution).
2. **Core blob vs separate RTC calls:** recommended unified blob (above); confirm with the Playstead contract owner if known.
3. **Speed-switch pause length and DIV behavior:** hardware-research gate in phase 8.
4. **Whether CGB-only ROMs may load on the DMG profile:** recommend load (matches hardware) with an info flag.
5. **MBC30 / MBC1M / rumble motor output:** out of scope for v0.2; fail explicitly with existing variant error.

## Sources

- `src/core/gabbaboy.c`, `include/gabbaboy/gabbaboy.h`, `docs/cartridge-and-saves.md`, `src/player/session.c`, `src/player/main.c`, `src/runner/main.c`, `CMakeLists.txt` (this repository, read 2026-10-10): HIGH.
- `.planning/PROJECT.md`, `.planning/research/ARCHITECTURE.md`, `.planning/context/DECISIONS.md` (D-008, D-009, D-011, D-012, D-016, D-022, D-024, D-025): HIGH for project intent.
- Pan Docs (gbdev) pages on CGB registers, MBCs, power-up sequence, HDMA, and speed switch: referenced by `../ARCHITECTURE.md` and recalled here; hardware numbers tagged `[VERIFY]` were not re-fetched in this pass: MEDIUM-LOW until the phase research gate checks them.
- SameBoy, mGBA, Gambatte as behavioral comparators only (no code reuse; license constraints per `../ARCHITECTURE.md`).
