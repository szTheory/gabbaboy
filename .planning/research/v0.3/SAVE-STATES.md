# STATE-01 research: transactional, versioned native save states

Scope: GabbaBoy v0.3 STATE-01, "Transactional versioned native save states covering hidden in-flight state with exact continuation equivalence."
Basis: GabbaBoy `main` at `02776e5` (read-only inspection of `include/gabbaboy/gabbaboy.h` and `src/core/gabbaboy.c`, 5,049 lines). Sibling precedent is nesturbator v3 Phase 12 (`src/state.c`, `src/state.h`, `tests/core/test_state_*.c`, `12-RESEARCH.md` pitfalls P1–P20) and schwaystation `src/state.c`. External sources are listed at the end.

This report recommends a design. Nothing here is implemented, and no claim is made that any part works.

---

## 1. Current machine state (what a state must capture)

### 1.1 Architectural facts that shape the design

- **One translation unit, one opaque struct.** All mutable state is in `struct gbb_instance` (lines 369–503). I found no mutable file-scope statics; the only file-scope tables are `static const`. So the "no hidden globals" rule already holds, and the struct really is the whole machine.
- **There is no event scheduler.** The core is tick-driven. `advance_devices_to` (line 3264) steps one half-dot at a time through timer reload, serial, DIV/APU frame sequencer, APU channel timers, the resampler, OAM DMA, HDMA and the PPU. The only "pending events" are (a) the countdown fields inside devices and (b) the 64-entry host input queue `input_events[]`. So nothing like mGBA's `nextEvent` or a Gambatte event queue needs to be rebased. All time is the absolute `time_half_dots` (uint64, 2^23 per second at both speeds, D-070).
- **Run boundaries are the only save points.** `gbb_run*` preflights each instruction, IRQ dispatch, HALT M-cycle, stall step or HDMA tick, and returns only between them. A public save or load can only happen between run calls, so no mid-instruction CPU micro-state (decoded opcode, bus phase) is ever live. The exceptions are fields that deliberately **cross** a boundary. These are the hidden in-flight state (§1.2).
- **Pointers and host-owned fields** (`rom`, `cartridge_ram`, `audio_frames*`, `diagnostic_*`, `test_*` observers, `accept_input_span`) are borrowed during a run or owned by the host. They must never be serialized.
- **Instance configuration is not emulation state.** `compat_rgb555` survives reset and load (D-17), as does `profile` (fixed at create).
- **A precedent exists.** The battery RTC block (D-16, lines 3903–3943) is already written field by field, little-endian, with a magic and version, and parsed into a local before commit. It returns typed errors and leaves the instance unchanged on refusal. Import compares before writing and bumps `battery_generation` once. STATE-01 should generalise this pattern, not invent a new one.

### 1.2 Hidden in-flight state a naive snapshot (registers + RAM) would miss

| Area | Fields | Why it is live at a run boundary |
|---|---|---|
| EI delay | `ime_delay` (0..2; 0 or 1 at a boundary) | `EI` sets 2, and the post-instruction decrement leaves 1. IME becomes 1 after the *next* instruction. |
| Halt bug | `halt_bug` | Set by HALT with IME=0 and an IRQ pending. It is consumed by the next fetch (PC not incremented). |
| HALT / STOP / lockup | `halted`, `stopped`, `locked`, `lockup_pc`, `lockup_opcode` | Execution state. STOP keeps the oscillator paused until a modeled wake event. |
| OAM DMA start latch | `dma_start_pending`, `dma_pending_page` | A write to FF46 latches the start. This is normally consumed after `execute`, **but** an IRQ-entry push onto FF46 sets it and does not consume it until after the next instruction. So it *can* be 1 at a boundary. |
| OAM DMA progress | `dma_active`, `dma_page`, `dma_index` (0..159), `dma_phase` (0..3), `dma_cpu_blocked`, `dma_register` | A transfer takes 160 M-cycles, so it straddles boundaries all the time. |
| HDMA (CGB) | all of `hdma_state`: `mode`, `active`, `pending_hblank`, `blocks_remaining`, `byte_index`, `byte_phase`, `source_cursor`, `destination_cursor`, `block_vram_bank`, the four address bytes, `control_readback` | An admitted 16-byte block consumes master time across ticks. The run loop services `pending_hblank` and `active` *before* IRQ or fetch. The mutation `P13-05-M14` already proves that dropping `byte_phase` at a run boundary is observable. |
| KEY1 speed switch | `key1_armed`, `double_speed`, `cpu_stall_kind` (NONE / SPEED_SWITCH / SWITCH_REALIGN), `cpu_stall_half_dots` (up to 0x20004 T scaled), `stop_switch_pending` (0 at a boundary) | The stall lasts about 131k T and spans many run calls by design ("consumes budget across calls"). The realign stall adds 4 half-dots. |
| Divider phase | `divider_counter` (16-bit internal DIV), `divider_phase` (normal-speed half-dot parity), `div` | `divider_phase` decides which half-dot is a CPU tick. Losing it shifts every timer, serial, APU-sequencer and DMA edge by one half-dot. |
| Timer | `timer_signal` (falling-edge detector input), `timer_reload_pending`, `timer_reload_remaining` (≤4), `timer_reloaded_at` (UINT64_MAX sentinel or a time), `tima/tma/tac` | The TIMA overflow → reload → IF delay crosses boundaries. |
| Serial | `serial_active`, `serial_bits` (0..8), `serial_edge_remaining` (≤512), `serial_data/control` | An internal-clock transfer takes 8×512 CPU ticks. |
| Interrupts | `ie`, `interrupt_flags`, `ime` | |
| PPU mode/fetcher | `ppu_dot` (<456), `ppu_half_phase`, `ppu_mode`, `ppu_stat_line` (STAT IRQ edge detector), `ppu_fifo[16]`, `ppu_fifo_head`, `ppu_fifo_count`, `ppu_fetch_stage`, `ppu_fetch_phase`, `ppu_fetch_enqueued`, `ppu_transfer_age`, `ppu_output_x`, `ppu_scroll_discard`, `ppu_fine_scroll`, `ppu_mode3_stall`, `ppu_window_started`, `ppu_transfer_complete`, `ppu_objects_stalled`, `ppu_object_tiles_fetched`, `ppu_selected_{objects,y,x,tile,attributes}[10]`, `ppu_selected_object_count`, `ppu_scan_index`, `ppu_window_line`, `ppu_window_line_drawn`, `ly`, `stat` | Mode 3 in progress at a boundary is the normal case. The window line counter is internal and not readable from any register. |
| Frame output | `frame_working[23040]`, `frame_completed[23040]`, `rgb_working[23040]`, `rgb_completed[23040]` (u16), `frame_generation`, `frame_completion_half_dots` | The working frame holds the rows already drawn this frame. Without it the first frame after a load differs. `gbb_copy_frame*` right after a load must return the same bytes and `gbb_frame_info`. |
| APU channels | per pulse: `length`, `timer`, `phase`, `volume`, `envelope_timer`, `sweep_timer`, `sweep_shadow`, `enabled`, `sweep_enabled`, `sweep_negate_used` plus the register bytes; wave: `ram[16]`, `position`, `sample_buffer` (CGB read path), `timer`, `length`, `enabled`; noise: `lfsr` (15-bit), `timer` (u32), `volume`, `envelope_timer`, `length`, `enabled` | Length, envelope and sweep counters are not readable through NRxx. |
| APU frame sequencer | `apu_sequencer_step` (0..7), `apu_power`, `apu_nr50`, `apu_nr51` | Clocked on falling DIV-bit edges (tap 0x1000 or 0x2000 by speed). |
| Resampler / host mix | `apu_sample_phase` (<2^23 after subtraction), `audio_event_ring[2][16]` (int64 band-limited step history), `audio_event_head`, `audio_mix_level[2]`, `audio_hpf_input[2]`, `audio_hpf_output[2]` | Needed for **bit-exact audio** after a load. This is the history of the 16-tap band-limited step synthesis and the HPF. SameBoy and mGBA do not keep output-filter history bit-exact. GabbaBoy's equivalence claim requires it. |
| Banking & CGB I/O | `vram_bank`, `wram_bank`, `svbk`, `bcps`, `ocps`, `bg_cram[64]`, `obj_cram[64]`, `opri`, `ff56`, `ff72..ff75` | `wram_bank` is *derived* from `svbk` (0 → 1). See footgun F2. |
| Cartridge mapper | `cart_state`: `rom_bank_lo/hi`, `ram_bank`, `ram_enabled`, `mbc1_mode`, `rumble_on` | `kind`, `has_*` and `ram_window_mapped` are cartridge identity and come from the ROM, not the state. |
| MBC3 RTC | `rtc_s/m/h/dl/dh`, `rtc_l[5]`, `rtc_latch_prev`, `rtc_sub` (<2^23), `rtc_synced_at` | The clock is lazy and anchored. `rtc_synced_at` is an absolute half-dot time and is valid because `time_half_dots` is also saved. The sub-second prescaler is hidden state. |
| Joypad & input queue | `joypad_select`, `joypad_buttons`, `input_events[64]`, `input_event_count` | Queued future events (STOP wake, serial edge, button) are part of the continuation. |
| Bus refusal latch | `bus_unsupported`, `bus_unsupported_address` | Cleared before every return that reports it, so they are expected to be 0 at a boundary. Serialize them anyway, or validate them as zero (see §4.4). |
| Time | `time_half_dots`, `instruction_start_half_dots` | `instruction_start_half_dots` is re-set before every operation. Saving it keeps the round trip canonical. |
| Cartridge RAM | `cartridge_ram[cartridge_ram_size]` (0, 512, 8K, 32K, 64K, 128K) | Includes MBC2's canonical `0xF0 \| nibble` form. |

**Excluded on purpose:**
- Pointers and borrowed outputs.
- Test observers.
- `compat_rgb555` (configuration).
- `battery_generation` and `rumble_changes`. These are host change counters. A load bumps them exactly once if the battery bytes or the rumble line actually change, as nesturbator STATE-05 does.
- `#if GBB_TEST_CGB_PCM_WRITABLE` override fields. These are test-only. The state layout must not depend on test macros. Saving under that build should refuse, or ignore the fields and say so.

### 1.3 Size estimate

| Region | Bytes |
|---|---|
| WRAM 8×4 KiB | 32,768 |
| VRAM 2×8 KiB | 16,384 |
| HRAM / OAM / CRAM / wave RAM | 127 + 160 + 128 + 16 |
| DMG shade frames (working + completed) | 46,080 |
| RGB555 frames (working + completed) | 92,160 |
| Audio ring (2×16×i64) + filter state | ~300 |
| Input queue (64 × [u64 time, u8 kind, u8 value]) | 640 |
| All other scalars (CPU, PPU, timers, DMA, HDMA, APU, mapper, RTC) | ~450 |
| Header + section framing | ~64 + ~20×8 |

- **Everything, DMG and CGB frame buffers both:** about 189 KB + cartridge RAM. Worst case (MBC5, 128 KiB RAM) about 320 KB.
- **Mode-selected frame buffers:** the DMG profile writes only shade buffers; CGB mode, and compat mode on the CGB profile, writes only RGB buffers (verify compat mode; see the `rgb_working` comment at line 397). That gives about **97 KB + RAM (DMG)** and **about 143 KB + RAM (CGB)**. The mode is fixed between `gbb_load_rom` calls, so the size stays fixed per loaded ROM. This satisfies libretro's "fixed between load_game and unload_game, never increases" rule without the variable-size quirk.
- Recommendation: serialize only the mode's frame pair, and validate that the other pair is all zero in the live instance (it is, by construction). This also halves rewind memory.

For comparison: mGBA's GB state is a fixed 0x11800 (71,680) bytes without SRAM, which goes in extdata. GabbaBoy is larger mainly because it keeps both frame buffers and CGB WRAM/VRAM. Hosts may compress; the core must not.

---

## 2. Other ecosystems (primary sources)

### SameBoy native format plus BESS
- **Native sections.** `header`, `core_state`, `dma`, `mbc`, `hram`, `timing`, `apu`, `rtc`, `video`, `accessory` and others are **raw `memcpy` of struct regions**, each prefixed with a u32 size. They are host-endian.
- **Version handling.** A size mismatch reads `min(saved, current)` and skips the rest. A version or magic mismatch falls back to BESS.
- **Load path.** It loads into a temporary copy of the struct, then copies back, then runs `sanitize_state` (clamps FIFO indices, `display_cycles`, banks). This is not fully atomic: RAM buffers are read straight into the live instance after the compatibility check.
- **Lesson.** Raw struct dumps plus post-hoc sanitizing is exactly what GabbaBoy's rules forbid. The temp-copy idea is good; the non-atomic RAM path is the failure to avoid.

**BESS 1.0** (SameBoy `BESS.md`):
- Placement: an 8-byte footer (u32 offset to the first block, then `"BESS"`), so it can be **appended to any native state**.
- Blocks: 4CC plus a u32 length. Order is `NAME`, `INFO` (title + global checksum), `CORE` (0xD0 bytes: version major/minor, model 4CC, PC/AF/BC/DE/HL/SP, IME/IE/exec-state, the 128 I/O register values, and offset/size pairs pointing at RAM, VRAM, MBC RAM, OAM, HRAM and palettes elsewhere in the file), optional `XOAM`, `MBC ` (address/value write list), `RTC ` (VBA-style 0x30, including a UNIX timestamp), `HUC3`, `TPP1`, `MBC7`, `SGB `, and `END `.
- Byte order: little-endian.
- Compatibility rules: unknown blocks are skipped; a different major version is rejected; a newer minor version is read; extra bytes are ignored.
- Restore semantics: registers are applied "as if the ROM wrote them", without triggering DMA, sound or serial; DIV becomes `DIV<<8`.
- **It is explicitly best-effort.** It has no PPU fetcher, timer phase, APU counters or DMA progress. A BESS round trip therefore cannot meet GabbaBoy's exact-continuation claim.

### mGBA (GB)
- Packed fixed struct `GBSerializedState`, statically asserted at 0x11800.
- Every field is written through `STORE_32LE` / `LOAD_32LE` (portable, despite the packed struct).
- The `versionMagic` is magic + version. It loads older versions "anyway" with a warning and rejects newer ones.
- `romCrc32` and title are checked (a mismatch only warns).
- Cycle-relative event times are stored (`nextEvent`, `eiPending.when - now`, DMA/HDMA next times).
- There are bitfield flag words for halted / EI pending / IRQ pending / HDMA active / RTC latched.
- `GBDeserialize` range-checks before loading ("Savestate is corrupted: video x out of range", DMA destination out of range, and so on).
- Lessons: explicit LE, ROM CRC identity, and **validate-before-apply with named corruption reasons**. Its lenient mismatch policy (warn and continue) is weaker than GabbaBoy needs.

### Gambatte
- **Labelled-field** format (`statesaver.cpp`, `SAVE_VERSION 0x02`). Each field is a short NUL-terminated label plus a 3-byte big-endian length plus big-endian data.
- Labels are sorted for lookup; unknown labels are skipped; missing labels keep defaults. There is also an optional thumbnail.
- This gives forward and backward compatibility without version migration code. The costs are per-field overhead and the "missing field silently defaults" hazard, which breaks exactness without any error.

### libretro (`libretro.h`)
- **Size contract.** `retro_serialize_size` may only stay the same or shrink between `retro_load_game` and unload. RetroArch rewind picks one fixed size.
- **Quirks.** `RETRO_SERIALIZATION_QUIRK_INCOMPLETE` marks a state that is "usable for the common case … but should not be relied upon for … netplay or rerecording". `CORE_VARIABLE_SIZE`, `SINGLE_SESSION`, `ENDIAN_DEPENDENT` and `PLATFORM_DEPENDENT` are the others. A GabbaBoy state should need **no** quirks.
- **Contexts.** `RETRO_SAVESTATE_CONTEXT_RUNAHEAD_SAME_INSTANCE` (save/load several times per frame, "should be fast"), `RUNAHEAD_SAME_BINARY`, and `ROLLBACK_NETPLAY` ("must not contain pointers, and integers must be saved in big-endian format").
- Implications for Playstead/INT-01:
  - Save and load must be allocation-free and O(state size), with no per-call ROM CRC.
  - Run-ahead calls load every frame, so a rejected load must be cheap and a successful one bit-exact.
  - The netplay big-endian note is a frontend wire convention. The adapter can byte-swap or ship our LE bytes opaquely; the core format stays LE.

### Dolphin / higan / ares / Mesen2 (serializer patterns)
- **Dolphin `PointerWrap`** runs one `DoState(PointerWrap&)` per component in MODE_READ / MODE_WRITE / MODE_MEASURE / MODE_VERIFY, with `DoMarker("name")` sentinels to catch drift.
- **higan/ares `serializer`** does one `serialize(serializer&)` per component, uses the same code for size, save and load, and puts a version string in the header. ares rejects mismatched versions outright.
- **Mesen2 `Serializer`** uses named key/value fields (with prefixes) and compresses. It tolerates missing keys.
- **Common lesson:** *one field list drives every pass*, so size, save and load cannot drift. nesturbator's `sio` (SIZE / WRITE / VALIDATE / APPLY / RECORD) is the C17 version of this and is already proven in a sibling.

### Sibling cores
- **nesturbator** (the best precedent; copy it, do not depend on it):
  - 64-byte header with PNG-style magic `89 'N' 'T' 'S' 0D 0A 1A 0A`, format version, header size, total size, behaviour revision (recorded, not enforced), mapper / submapper / region, ROM CRC-32, state CRC-32 that skips its own field, frame, ticks, and zero reserved bytes.
  - Untagged body in field-list order, then cartridge RAM.
  - Exact size required.
  - Ordered typed errors: ARGUMENT → SIZE(<header) → FORMAT → CARTRIDGE (identity before length) → SIZE → CHECKSUM → INVALID.
  - VALIDATE pass then APPLY that cannot fail.
  - `save_generation` bumps only when battery bytes change.
  - Bounds classed S (index/shift safety) and L (bounded work, e.g. PPU gap < one frame, ticks ≤ 2^62).
  - `_Static_assert(sizeof …)` tripwires.
  - Fork matrix into a **poisoned** fresh instance, a stress ROM so DMA straddles boundaries, save-every-frame metamorphic check, reject sweep, and a state fuzz target.
  - Its pitfalls P4 (memcpy NULL,0), P5 (hostile ticks hang), P6–P8 (signed overflow and indices from hostile fields), P13 (pre-fill poison is weak unless whitebox), P14 (unsaved fields surface frames later), P16 (corpus does not exercise straddles) all apply directly.
- **schwaystation:** `schway_state_size/save/load` plus a `schway_state_visit(visitor)` that reports each field by name, width and count, with distinct MAGIC / VERSION / CRC / FIELD errors. The named visitor is a useful test and introspection hook.
- glueyneo, genewhip, muhtari and cogmaster have libretro glue, digests or snapshot vocabulary, but no native state format worth copying.

---

## 3. Recommendation

### 3.1 Format

One self-contained native format: little-endian, fixed layout per format version, with light section framing.

```
Header (64 bytes)
  0  magic[8]        89 'G' 'B' 'S' 0D 0A 1A 0A   (detects 7-bit/CRLF/text-mode damage)
  8  format_version  u16  (= GBB_STATE_FORMAT_VERSION)
 10  header_size     u16  (= 64)
 12  total_size      u32
 16  behaviour_rev   u32  (recorded; not enforced on load)
 20  profile         u8   (gbb_profile)
 21  exec_mode       u8   (gbb_exec_mode)
 22  cartridge_type  u8   (raw $147)
 23  flags           u8   (bit0 RTC section present; others zero)
 24  rom_size        u32
 28  ram_size        u32  (cartridge RAM only)
 32  rom_crc32       u32  (CRC-32/IEEE of the whole ROM, computed once at gbb_load_rom)
 36  header_global_checksum u16 ($14E-$14F) ; 38 header_checksum u8 ; 39 reserved u8
 40  time_half_dots  u64
 48  state_crc32     u32  (covers every byte except this field)
 52  reserved[12]    zero
Sections, in fixed order, each: tag 4CC, u32 length (must equal the exact v1 length)
  "CPU " "INTR" "TIMR" "SERL" "DMA " "HDMA" "SPED" "BANK" "PPU " "OAM " "PAL " "VRAM"
  "WRAM" "HRAM" "APU " "AOUT" "FRME" "JOYP" "INPQ" "CART" ["RTC "] ["SRAM"] "END "
```

- **Encoding.**
  - Every multi-byte value is written one byte at a time, LSB first.
  - `int` booleans become u8 0/1, and VALIDATE rejects other values.
  - `size_t` counts become u32.
  - The u16 RGB555 buffers are written as explicit LE pairs, matching the existing digest rule in the header.
  - Unused input-queue slots are written as zero.
  - **The encoding is canonical:** `save(load(S)) == S` byte for byte.
- **Why framing and not pure untagged order** (nesturbator) or TLV (Gambatte):
  - The tags cost about 160 bytes.
  - They make a hex dump and a failure report self-locating ("INVALID in HDMA at +5").
  - They give a later v2 loader a clean per-section dispatch point if migration is ever wanted.
  - Lengths are *exact* per version, so the framing adds no tolerance and no silent-default hazard, unlike Gambatte and Mesen.
  - (The critique in §6 notes this could be dropped.)
- **Checksum.** CRC-32/IEEE, about 30 lines of copied code with a 1 KiB `static const` table, plus the `"123456789"` → `CBF43926` test vector. It detects corruption, not tampering, so VALIDATE still treats every state as hostile.
- **Versioning and compatibility policy** (copy nesturbator's wording):
  - Until the first release that contains states, `GBB_STATE_FORMAT_VERSION` stays 1 and the layout may change.
  - After that release, **any** byte-layout or meaning change bumps the version in the same commit, and other versions are refused with `GBB_STATE_FORMAT`. There is **no converter**; GabbaBoy promises no stable ABI.
  - A pure emulation fix bumps `GBB_BEHAVIOUR_REVISION` instead. A state saved under an older revision loads but may diverge, and tests that bind continuation must also bind the revision.
  - A CTest pins the SHA-256 of a golden state. It must change only together with a version or revision bump.
- **ROM is not included.** Identity is profile, exec mode, cartridge type, sizes, header checksums and the full ROM CRC-32, checked before length. CRC over 8 MiB costs about 10–30 ms with the table, paid once in `gbb_load_rom`, never per save. That keeps run-ahead cheap.

### 3.2 API (additive to `gabbaboy.h`)

```c
#define GBB_STATE_FORMAT_VERSION 1u
#define GBB_BEHAVIOUR_REVISION   1u
/* appended to gbb_error (values only appended): */
GBB_NO_ROM_STATE?           -> reuse GBB_INVALID_ARGUMENT? (decide; prefer a distinct GBB_STATE_NO_ROM)
GBB_STATE_FORMAT,           /* bad magic or unsupported format version */
GBB_STATE_MISMATCH,         /* profile/mode/cartridge/ROM-CRC identity differs from the loaded ROM */
GBB_STATE_SIZE_MISMATCH,    /* length != gbb_state_size or != header total, incl. every truncation */
GBB_STATE_CORRUPT,          /* CRC-32 mismatch */
GBB_STATE_INVALID,          /* CRC ok but header/section/field/cross-field rule fails */

gbb_error gbb_state_size(const gbb_instance *instance, size_t *out_size);
gbb_error gbb_save_state(const gbb_instance *instance, uint8_t *out_bytes, size_t capacity_bytes);
gbb_error gbb_load_state(gbb_instance *instance, const uint8_t *bytes, size_t size_bytes);
```

- **Size.** Exact and constant from a successful `gbb_load_rom` until the next one. It is mode-dependent (§1.3). With no ROM it returns a typed error. It does not change across `gbb_reset`.
- **Save.**
  - It is `const`: SIZE and WRITE only read through the field pointers, and the const-cast is documented as in nesturbator P15.
  - It allocates nothing.
  - It writes only on success and leaves bytes beyond `size` untouched. NULL is never a size query.
  - A `locked`, `stopped`, `halted` or mid-stall instance is saveable.
- **Load** is all-or-nothing. Checks run in this order:
  1. NULL arguments.
  2. Size below the header.
  3. Magic / version → FORMAT.
  4. No ROM, or identity differs → MISMATCH.
  5. Size → SIZE_MISMATCH.
  6. CRC → CORRUPT.
  7. Header reserved fields, section tags and lengths, field bounds, cross-field rules → INVALID.
  8. Compare battery bytes and the rumble line.
  9. APPLY, which cannot fail.
  10. Bump `battery_generation` once if cartridge RAM or the projected RTC changed. Count a rumble change if the line differs.

  A refusal leaves the instance unchanged byte for byte. A load never runs the clock or calls `gbb_rtc_catch_up`.
- **Deferred.** An instance-free `gbb_probe_state(bytes, size, gbb_state_info*)` using the `struct_size` handshake (version, profile, ROM CRC, time) is useful for slot browsers. Defer it unless INT-01 needs it.

### 3.3 Transactional apply: two-pass visitor, not a scratch instance

**Implementation**
- Copy nesturbator's `sio` design. One `static` field list per section (`cpu_io`, `ppu_io`, …) runs in modes SIZE / WRITE / VALIDATE / APPLY / RECORD.
- Primitives take a `max` bound (or a set predicate) and return the decoded value, so cross-field rules can use earlier fields. `sio_check(io, cond)` sets `bad`.
- VALIDATE walks the *same* lists over the *same* bytes, so APPLY cannot meet a byte VALIDATE did not check.
- RECORD emits `(name, offset, width, lo, hi, cross)` for tests, which merges in schwaystation's named visitor.
- Large arrays (WRAM, VRAM, frames, SRAM) are raw byte runs, with value checks only where they matter: RGB555 bit 15 must be 0, shade bytes must be ≤3, MBC2 cells must be `0xF0|n`.

**Why not decode into a scratch `gbb_instance` and commit**
- The struct is more than 300 KB with frames plus heap SRAM. A scratch copy means either an allocation per load, which breaks the run-ahead "fast, no alloc" contract and adds an OOM path, or a caller-provided scratch buffer, which complicates the API.
- The two-pass design gives the same atomicity with no allocation, provided APPLY really cannot fail. That property is testable (§4.3).
- Scratch instances stay an option *in tests*: the atomicity oracle copies the instance before a refused load and compares it after.

**After APPLY**
- Recompute nothing that is also saved.
- Wherever a derived value exists, either save only the source (`svbk`, deriving `wram_bank`) or save both and add a cross-field rule. Prefer deriving, with one shared helper used by the I/O write path and by APPLY.

### 3.4 Validation rules (hostile-state safety)

Each rule is classed **S** (memory or UB safety: index, shift, signed overflow), **L** (bounded work), or **I** (an invariant the core keeps).

**Indices and shifts (S)**
- `ppu_fifo_head<16`, `ppu_fifo_count≤16`, `ppu_selected_object_count≤10`, `ppu_scan_index≤40`.
- `ppu_dot<456`, `ly≤153`, `ppu_mode≤3`, `ppu_half_phase≤1`, `ppu_fetch_stage` and `ppu_fetch_phase` within their enums.
- `dma_index≤160` (and <160 while active), `dma_phase<4`.
- `hdma.byte_index<16`, `blocks_remaining≤128`, cursors in range, `block_vram_bank≤1`.
- Pulse `phase<8`, wave `position<32`, `apu_sequencer_step<8`, volumes ≤15, `lfsr<2^15`, `audio_event_head<16`.
- `vram_bank≤1`, `svbk≤7`.
- Mapper registers masked to their write widths.
- Palette index registers within 0..0x3F plus the auto-increment bit.
- `input_event_count≤64`, with every used event's `kind` valid and its `value` valid for that kind.

**Signed overflow (S)**
- Bound `audio_event_ring` entries, `audio_mix_level`, and the HPF in/out (s16 range) so the next `audio_round_q15` and `audio_add_edge` sums cannot overflow int64. Derive the bound from the 16-tap step table; nesturbator P6 is the precedent.

**Bounded work and headroom (L)**
- `time_half_dots ≤ 2^62`, so every `UINT64_MAX - time` headroom check (HDMA start, speed switch, stop) stays meaningful.
- `cpu_stall_half_dots ≤ 2·0x20004`, with `cpu_stall_kind` in {0,1,2} and the realign stall ≤4.
- `serial_edge_remaining≤512`, `serial_bits≤8`.
- `timer_reload_remaining≤4`, and `timer_reloaded_at` is either `UINT64_MAX` or ≤ time.
- `apu_sample_phase<2^23`.
- `rtc_sub<2^23`, `rtc_synced_at≤time`.
- Input events sorted nondecreasing and `≥ time`.
- `frame_completion_half_dots≤time`.

**Cross-field invariants (I)**
- A DMG profile or a non-CGB mode implies zero CGB-only fields (`double_speed`, stall kind, HDMA mode, `key1_armed`, `vram_bank`, `svbk`).
- `ime_delay ∈ {0,1}` at a boundary.
- `stop_switch_pending == 0`.
- `bus_unsupported == 0`.
- RTC fields follow the battery block's exact rules (S/M ≤ 0x3F, H ≤ 0x1F, DH mask 0xC1); share `rtc_block_parse`'s checks.
- A valid but unreachable state (for example mode 3 at dot 10) is **accepted if memory-safe and bounded**. The contract promises safety and bounded work for hostile states, not meaningful emulation, as nesturbator does.

### 3.5 Battery saves and RTC

- **Cartridge RAM.** The state holds cartridge RAM and the full RTC, including the sub-second prescaler, latch registers, latch edge and anchor. Loading an older state reverts SRAM. This is the expected rewind semantic, and the header comment and README must say it.
- **Generation.** `battery_generation` bumps once, only when the cartridge RAM bytes or the RTC block projected to "now" actually differ, so repeated run-ahead loads never trigger a `.sav` write. This reuses `rtc_fields_equal` and the import comparison logic.
- **RTC.** The RTC is emulated-time only. A load restores the exact clock; wall-clock catch-up stays a host decision through `gbb_rtc_catch_up`, recorded as an input event. Nothing in the core reads host time.
- **Order of operations.** Document it: host opens ROM → imports battery → optional catch-up → optionally loads a state, which overrides both.
- **Battery file vs state.** They stay separate files. The battery format (D-16, `GBRT` v1) is unchanged. A state is not a battery file, and neither accepts the other: different magic, different error.

### 3.6 BESS: later, export first, never as an equivalence path

- BESS cannot express GabbaBoy's in-flight state, so a BESS import can never meet STATE-01's exact-continuation claim. It also needs a register-replay semantic ("as if written, without side effects") that touches every I/O write path.
- **Recommendation:** no BESS in STATE-01.
- **Leave room for it:** reserve header `flags` bit 1 for "BESS trailer present". When set, `total_size` covers only the native part and the loader accepts exactly `native + trailer`.
- **Later phase or milestone:**
  - (a) An **export-only** BESS trailer, so SameBoy, BGB and mGBA users can move a game across. This is additive and testable by loading into SameBoy in a hosted job, which is a differential oracle, not a hardware claim.
  - (b) A separate `gbb_import_bess` with an explicit best-effort contract and its own typed errors. It is excluded from every equivalence test.
- Fit with D-026: interop formats belong in host adapters unless a concrete consumer needs them in the core. Exporting BESS from a host adapter is equally possible if the core exposes the needed registers. Decide at that phase.

---

## 4. Verification strategy (every deliverable automated, each with a negative control)

### 4.1 Continuation equivalence: the fork matrix (core of STATE-01)

**Reference run A**
- Per ROM and profile, a seeded schedule of run slices: mixed `gbb_run_audio` budgets, from one instruction to several frames, including odd half-dot budgets and budgets that end mid-stall.
- A recorded input-event script.
- After each slice, digest:
  - the `gbb_run_result` fields;
  - `gbb_copy_frame` or `gbb_copy_frame_rgb555` bytes (LE) and `gbb_frame_info`;
  - the audio frames;
  - the battery image and generation;
  - rumble state;
  - selected `gbb_peek_ram` bytes;
  - the full state bytes (SHA-256).

**Fork points**
- N seeded-random slice boundaries per ROM, plus every boundary in the first frames, plus **targeted straddle points** found by a whitebox census predicate:
  - OAM DMA active; `dma_start_pending`;
  - HDMA `active` with `byte_phase≠0`; `pending_hblank`; GDMA in progress;
  - speed-switch stall (early, middle, last quantum); realign stall;
  - `halted`; `stopped` with a queued wake; `halt_bug`; `ime_delay==1`;
  - timer reload pending; serial mid-transfer;
  - PPU mode 3 with a nonempty FIFO; window started; OAM scan mid-way;
  - APU length, envelope or sweep mid-count; wave `sample_buffer≠ram`;
  - RTC latched with `rtc_sub≠0`;
  - non-empty input queue; `locked`.

**Branch B**
- A fresh instance with the same ROM, run first on *different* inputs, then **whitebox-poisoned** (test hook fills every state-bearing field with 0xA5, keeping pointers and identity). nesturbator P13 shows a plain pre-fill leaves almost nothing stale.
- B loads S_k and continues with A's remaining slices and inputs.
- **Pass:** every later digest is equal, including audio bits and the final state bytes.
- **Variants:**
  - load into the *same* instance A after it has run ahead (rewind);
  - load S_k twice (idempotence);
  - load, save, compare bytes (canonical round trip).

**Corpus**
- The existing acceptance cases (Libbet, the CGB colour cases), cgb-acid2, the rtc3test inputs, the CGB HDMA/speed/APU corpus already inventoried in `tests/external/*.json`, and an MBC5 rumble image.
- Plus **synthetic straddle ROMs** assembled in-repo (rights-clear) that loop each straddle condition every frame:
  - FF46 every frame plus an IRQ push onto FF46;
  - HBlank HDMA of 0x7F blocks;
  - KEY1/STOP every N frames;
  - EI/HALT patterns;
  - TIMA at 0xFF with TMA reload;
  - internal-clock serial;
  - an RTC latch loop.

  Committed games will not exercise these by themselves (nesturbator P16).

**Census gate**
- The test fails if any straddle category was never present at at least one fork point. This guards the coverage itself.

**Save-every-boundary metamorphic test**
- Saving, and save-then-load, at every slice boundary must leave every pinned acceptance digest unchanged. Saving must be observably pure.

### 4.2 Negative controls (prove the tests can fail)

1. **Omission mutants.** Add `GBB_STATE_MUT(n)`, in the same style as the existing `GBB_P13_MUT` mutant-core build. Each mutant skips or zeroes one field in WRITE or APPLY.
   - At least one mutant per in-flight category: `dma_phase`, `dma_start_pending`, `hdma.byte_phase`, `hdma.pending_hblank`, `cpu_stall_half_dots`, `divider_phase`, `ppu_half_phase`, `ppu_fifo`, `ppu_window_line`, `frame_working`, `ime_delay`, `halt_bug`, `timer_reload_remaining`, `serial_edge_remaining`, `apu_sequencer_step`, `envelope_timer`, `wave.sample_buffer`, `audio_event_ring`, `apu_sample_phase`, `rtc_sub`, `input_events`.
   - **Every mutant must be killed** by the fork matrix. A survivor fails CI and means the corpus or census is too weak.
2. **VALIDATE-gap mutant.** Drop one bound, then show that the hostile sweep (4.3) produces a sanitizer abort or a non-INVALID result.
3. **Atomicity mutant.** Apply one section before CRC verification, then show the "unchanged on refusal" oracle fails.
4. **Field-list drift guard.** A script parses `struct gbb_instance`, `cart_state`, `hdma_state` and the APU structs, and diffs the member names against the RECORD-mode field list plus an explicit exclusion list that gives a reason for each entry.
   - Negative control: a fixture struct with an extra member must fail the script.
   - Backup: `_Static_assert` on `offsetof` of the last saved field for pointer-free sub-structs.
5. **Generation control.** Loading the same state twice bumps the generation zero times. Loading a state with different SRAM bumps it exactly once. The control is a mutant that bumps unconditionally.

### 4.3 Rejection, atomicity and fuzzing

- **Truncation sweep.** Every length from 0 to size−1, plus size+1, gives SIZE_MISMATCH. Exception: below the header but with valid magic, check the ordered result.
- **Single-byte flip sweep.** Exhaustive over the header and scalar sections, strided over RAM. Each flip gives the *first* rule it breaks: magic/version → FORMAT, identity → MISMATCH, total → SIZE, anything else → CORRUPT.
- **CRC-recomputed bound sweep.** Use the RECORD output to set each bounded field to max+1 and to the type maximum, recompute the CRC, and expect INVALID. Set it to exactly max and expect the load to succeed and N frames to run cleanly under ASan/UBSan within a time bound.
- **Atomicity oracle.** After every refusal, a whitebox comparison of the instance, plus `gbb_state_size`/save digest, battery bytes and generation, shows no change. The instance comes from `calloc` and is never struct-assigned, so a `memcmp` over the struct is a valid test oracle. Exclude pointer fields, or compare with the test hook.
- **Wrong-instance controls.** No ROM; DMG state into a CGB instance with the same ROM; same title but different CRC; MBC RAM size differs.
- **libFuzzer `fuzz_state`** (reuse the `fuzz_core.c` and standalone-test pattern).
  - Input: ROM choice + operation script + state bytes.
  - A "fix CRC" byte lets the fuzzer reach semantic validation.
  - Invariants:
    - no crash or UB;
    - result ∈ {OK, typed errors};
    - on refusal, the instance is unchanged;
    - on OK, a bounded run terminates within budget, and save gives canonical bytes that load again.
  - The seed corpus is the fork-point states.
  - Bounded iterations run in CI; longer runs are optional.

### 4.4 Portability and performance evidence

- **Pinned golden state digests** for 3 scenarios (DMG MBC1, CGB HDMA mid-block, MBC3 RTC). They must match on macOS, Linux and Windows/MSVC, and under the mutant-core build with mutants off. This catches endianness, `int`/`size_t` width and test-macro layout leaks.
- **Benchmark (informational).** Save and load time and state size per profile. It must record revision, build, hardware, workload, samples, warm-up and digest. It gives evidence for the run-ahead claim, but no target number until it has been measured.

---

## 5. Phase breakdown (v0.3; numbering continues after 15.1)

**Phase 16: Native state format and transactional load (STATE-01 a)**
- Delivers: `sio` visitor (copied and adapted), CRC-32, ROM CRC at load, header, sections, the three API calls, typed errors, all validation rules, generation semantics, header and doc comments.
- Tests: round-trip canonicality, save purity, truncation / flip / bound sweeps, atomicity oracle, field-list drift guard with its negative fixture, fuzz target, pinned golden digests.
- Proves: *format and safety*. A refused load changes nothing; hostile states are memory-safe and bounded; the bytes are canonical and portable.

**Phase 17: Continuation-equivalence qualification (STATE-01 b)**
- Delivers: synthetic straddle ROMs, census predicate and coverage gate, fork matrix over the corpus on both profiles, poisoned B instances, rewind and idempotence variants, save-every-boundary metamorphic test, omission mutants all killed, ASan/UBSan budgets (nesturbator P20: keep the sanitizer fork matrix to about 1k frames), benchmark.
- Proves: *exact continuation*. The phase is not complete until every census category is covered and every mutant is killed.

**Phase 18: Host consumption** (optional; may merge into INT-01 planning)
- Delivers: SDL player save slots and rewind ring, installed-package consumer test that uses the state API from C and C++, README section, and Playstead adapter mapping (`retro_serialize*` contexts, fixed size, no quirks).
- Proves: consumers use the real public API, and run-ahead or rewind loads do not write `.sav` files.
- BESS export is a separate future item (FUTURE-MILESTONES) with its own differential test against SameBoy.

Two phases are the minimum honest split: format/safety and equivalence fail for different reasons and need different evidence. Three phases is what I recommend if INT-01 needs a host proof before it starts.

---

## 6. Footguns

- **F1. "Transient" fields are not always zero at a boundary.** `dma_start_pending` survives when an IRQ push writes FF46. Serialize every non-pointer field, or prove a field is zero with a boundary-census assertion. Never assume.
- **F2. Derived duplicates.** `wram_bank` is derived from `svbk`. A hostile `svbk=3, wram_bank=0` breaks the D000 window. Derive with one helper, or cross-validate.
- **F3. Width-dependent types.** `int` booleans and `size_t` counts become u8 0/1 and u32. Canonical encoding requires rejecting 2..255 for booleans.
- **F4. Signed int64 audio history** from a hostile state means UB on the next sample (nesturbator P6). Bound it.
- **F5. Time near `UINT64_MAX`** makes headroom checks return `INVALID_STATE` forever, or misbehave. Cap at 2^62.
- **F6. Input queue semantics.** Events must be sorted and ≥ time. The 64-slot capacity is preserved; unused slots are zero.
- **F7. Compat palette is configuration.** It is not in the state. Equivalence tests must set the same palette in A and B. Hosts must restore their configuration themselves. Completed frames in the state already carry the resolved colours.
- **F8. Test-macro fields** (`GBB_TEST_CGB_PCM_WRITABLE`) must not change the layout. The `GBB_P13_MUT` mutant core must produce identical state bytes when mutants are off.
- **F9. Identity before length.** Another game's state must report MISMATCH, not SIZE. The size depends on the cartridge and mode.
- **F10. ROM CRC cost** belongs in `gbb_load_rom`, which changes its time profile. Measure it. It must never move into save or load.
- **F11. Behaviour revision vs format version.** Confusing them either breaks every user's states needlessly or silently lets old states diverge. Pin a golden digest to force a conscious bump.
- **F12. RTC anchor after reset.** `gbb_reset` rebases `rtc_synced_at` to 0, so validate `rtc_synced_at ≤ time`. A load never calls catch-up.
- **F13. Rewind reverts SRAM.** Hosts that write `.sav` on generation change will persist a rewound SRAM. This is the documented contract, and it surprises users (nesturbator P12).
- **F14. Frame state.** Drop `frame_working` and the first post-load frame differs. Drop `frame_completed` or `frame_generation` and `copy_frame` right after a load differs.
- **F15. `memcpy`/`memcmp` with NULL and length 0** for no-RAM cartridges is UB under UBSan (nesturbator P4). Guard every call.
- **F16. Header-declaration policy guards** and `expected-tests.txt` and other inventories will fail the moment the header grows (nesturbator P3, P9). Update them in the same commit.
- **F17. Const-cast in save/size.** It is defined only if SIZE and WRITE never store. Add a test that the instance is unchanged after save.
- **F18. Slicing.** Equivalence is tested with *identical* remaining slices in A and B. Slicing invariance (one long budget equals many short ones) is a separate property. Do not let one test silently stand in for the other.

## 7. Adversarial critique of this recommendation

1. **Two-pass validate/apply depends on discipline.** If a field's APPLY reads bytes VALIDATE never range-checked, the result is UB or unbounded work. A scratch-instance commit makes atomicity obvious but costs an allocation or a big caller buffer.
   *Answer:* one field list drives both passes, plus the bound sweep, the fuzzer and the VALIDATE-gap mutant. Still, if Phase 16 review finds the field list hard to keep symmetric, switch to a heap scratch instance for `gbb_load_state` and accept the OOM path. Run-ahead hosts would then pre-allocate.
2. **Range checks are not reachability.** A validated hostile state can put the core in configurations no test exercises. The claim is safety and bounded work, not correct emulation of nonsense. Users who expect "the state loaded, so it's valid" may be misled. The docs must say this.
3. **Section framing is redundant** while every length is fixed per version, and "future migration" is speculative given a no-converter policy (YAGNI). Pure untagged order, as in nesturbator, is simpler and proven. Keep the tags only if the diagnostic value is wanted; otherwise drop them before v1 freezes.
4. **Frame buffers dominate the size** (40–60%). SameBoy and mGBA do not store a full working and completed frame pair. An alternative is "first frame after load may differ", but that contradicts *exact* continuation and the `copy_frame` semantics. Keep the buffers, and reduce them by mode only.
5. **Full-ROM CRC identity is weaker than it looks** (collisions are unlikely but possible) and costs load time. Header checksums alone are cheaper but miss ROM hacks. SHA-256 is stronger but means more copied code. CRC-32 is the pragmatic middle; the decision should be recorded.
6. **The field-list drift script parses C with regexes,** which is fragile against macro-conditional members and multi-declarator lines (`uint8_t a, f, b, …`). It needs constrained struct style, or a hand-maintained manifest with a `sizeof`/`offsetof` tripwire on LP64 as the fallback.
7. **A finite mutant set is a sample.** Killing about 20 mutants shows the matrix is sensitive to those fields, not to all of them. Field-level completeness rests on the drift guard plus the poison test. Together these are strong but not proof.
8. **The census gate can be gamed by synthetic ROMs** that straddle in unrealistic ways. Real games may straddle in states the synthetic ROMs never produce, such as HDMA during a speed switch. Keep a game-corpus fork set alongside, and record which categories only synthetic ROMs cover.
9. **Deferring BESS** gives up interop that users of SameBoy, BGB and mGBA value. If INT-01 or a host needs cross-emulator moves early, a host-side BESS exporter could come earlier without touching the equivalence contract.
10. **Mode-dependent state size** relies on exec mode being fixed per load. If a future feature (for example a boot-ROM-like mode switch, or KEY0 writes) makes mode change at runtime, the size would vary and break libretro rewind. The sizing rule must be revisited then.

## Sources

- SameBoy BESS spec: https://github.com/LIJI32/SameBoy/blob/master/BESS.md
- SameBoy native state code: https://github.com/LIJI32/SameBoy/blob/master/Core/save_state.c
- mGBA GB state layout: https://github.com/mgba-emu/mgba/blob/master/include/mgba/internal/gb/serialize.h and `src/gb/serialize.c` (magic 0x00400000, version 3, `STORE_32LE`, range checks)
- Gambatte labelled state saver: https://github.com/pokemon-speedrunning/gambatte-core/blob/master/libgambatte/src/statesaver.cpp
- libretro API (serialize, quirks, savestate contexts): https://github.com/libretro/RetroArch/blob/master/libretro-common/include/libretro.h ; https://docs.libretro.com/development/cores/developing-cores/
- Dolphin `PointerWrap` (Common/ChunkFile.h); ares/higan `serializer` (nall/serializer.hpp); Mesen2 `Utilities/Serializer`. These patterns are described from general knowledge and were not re-fetched in this session.
- Sibling precedent (local, read-only): nesturbator `src/state.c`, `src/state.h`, `tests/core/test_state_fork.c`, `.planning/milestones/v3-phases/12-save-states-in-the-library/12-RESEARCH.md`; schwaystation `include/schwaystation.h`, `src/state.c`.
- GabbaBoy `02776e5`: `include/gabbaboy/gabbaboy.h`; `src/core/gabbaboy.c` lines 69–503 (state structs), 1535–1620 (`reset_state`), 2052–2110 (timer), 3166–3370 (DMA, APU sequencer, `advance_devices_to`), 3776–4035 (load, battery, RTC block), 4624–4911 (`gbb_run_internal`).
