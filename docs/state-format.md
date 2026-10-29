# Native machine state format

The native state API serializes a complete, bounded GabbaBoy machine state to a
caller-owned byte buffer. It has no filesystem access and does not replace the
cartridge battery API. The public calls are:

```c
gbb_error gbb_state_size(const gbb_instance *instance, size_t *out_size);
gbb_error gbb_save_state(const gbb_instance *instance, uint8_t *out_bytes,
                         size_t capacity_bytes);
gbb_error gbb_load_state(gbb_instance *instance, const uint8_t *bytes,
                         size_t size_bytes);
```

## Wire header

All integers are unsigned little-endian unless a body field is explicitly
signed. The header is exactly 64 bytes:

| Offset | Width | Field | Required value or meaning |
|---:|---:|---|---|
| 0 | 4 | Magic | ASCII `GBBS` |
| 4 | 2 | Format version | `1` |
| 6 | 2 | Header size | `64` |
| 8 | 2 | Release major | Exact `PROJECT_VERSION` major |
| 10 | 2 | Release minor | Exact `PROJECT_VERSION` minor |
| 12 | 2 | Release patch | Exact `PROJECT_VERSION` patch |
| 14 | 2 | Behavior version | `1` |
| 16 | 1 | Profile | Exact destination profile |
| 17 | 1 | Execution mode | Exact destination mode |
| 18 | 2 | Reserved flags | Both bytes zero |
| 20 | 32 | ROM identity | SHA-256 of the complete loaded ROM |
| 52 | 4 | Body size | Exact descriptor-derived size; at most `524288` |
| 56 | 4 | Total size | Exactly `64 + body size`; at most `524352` |
| 60 | 4 | CRC-32 | CRC described below |

Each release component must be a nonnegative decimal integer no greater than
65535. CMake rejects a version that does not have exactly three components or
that exceeds the wire range. A state can load only with the same release
triplet, behavior and format versions, profile, execution mode, and ROM digest.
The digest is an identity check, not authentication. Builds with the same
release triplet are qualified together by the project; an unreleased or
locally modified build has no cross-build compatibility promise unless it
retains the same state contract.

CRC is CRC-32/ISO-HDLC: reflected polynomial `0xEDB88320`, initial value
`0xFFFFFFFF`, reflected input and output, and final XOR `0xFFFFFFFF`. It covers
header bytes `0..59` followed by the body. The CRC field itself is excluded.
The check value for ASCII `123456789` is `0xCBF43926`. CRC detects accidental
corruption; it is not a MAC or signature.

## Body order and scalar encoding

The body has no C structure padding, pointers, host handles, or implicit
alignment. It walks 198 typed descriptors in this order:

1. Cartridge RAM bytes, with the length derived from the matching ROM.
2. Mapper registers, rumble state and MBC3 RTC state.
3. WRAM, HRAM, VRAM, OAM and bank/register state.
4. Both DMG frame buffers, both CGB RGB555 buffers, compatibility palette and
   frame metadata.
5. PPU scan/FIFO/fetch state, OAM DMA and CGB HDMA in-flight state.
6. Joypad, CPU registers and mode, interrupt, timer, divider, serial, lockup,
   and emulated-time state.
7. Input event count and all 64 fixed queue slots.
8. APU registers, channel/sequencer state, sample phase, signed audio event
   ring, mix levels and high-pass filter history.

Each descriptor contributes its fixed element count times its 1-, 2-, 4- or
8-byte wire width. Multi-byte values are little-endian. The ordered names,
counts, widths, and typed source fields are the `STATE_FIELDS` ledger in
[`src/core/gabbaboy.c`](../src/core/gabbaboy.c); its order is part of the wire
contract. A change to that ledger changes the body and requires a compatible
versioned format decision. Derived machine identity, ROM contents, observer
counters, test-only fields, pointers and host output buffers are not body data.

Booleans encode only `0` or `1`. The input count is at most 64; active events
are time ordered, cannot precede saved emulated time, and must have a valid kind
and value. Unused queue slots are encoded as zero and a decoder rejects
nonzero unused slots. CGB frame pixels and the compatibility palette are at most `0x7FFF`, while CGB palette RAM bytes are stored whole;
DMG frame indices are `0..3`; MBC2's 512 RAM bytes use canonical `$F0 | nibble`
values. RAM is at most 131072 bytes. RTC fields must satisfy the timer cartridge
invariants; RTC state is zero for cartridges without a timer. Ordinary emulated
times are at most `2^62`; `timer_reloaded_at` may also use `UINT64_MAX` as its
validated sentinel.

## Run horizon and input-event order

The ordinary master-time clock, saved frame and instruction anchors, RTC
anchor, queued event timestamps, and borrowed acceptance-span timestamps share
the inclusive `2^62` half-dot limit. `gbb_queue_events` rejects a batch
containing a timestamp above that limit without changing the existing queue.
Acceptance spans are validated as a whole before a run begins: their events
must be valid and time ordered, their unconsumed suffix cannot precede the
instance clock, and neither a timestamp nor the instance clock may exceed the
limit. Entries before the span cursor are historical and are not replayed.

Equal-time events retain caller order. At run entry, events at the current
timestamp are applied before another CPU fetch. While devices advance, the
clock reaches an event timestamp, the event batch is applied in its original
order, and then timer, serial, audio, DMA and PPU work for that half-dot runs.
This ordering also applies at exactly `2^62`, so events at the cap can be
delivered without allowing a later clock-advancing operation to cross it.
STOP may consume a partial wait up to the cap. Instructions, interrupt entry,
HALT ticks, DMA ticks and CPU-stall ticks remain atomic: if their complete
reservation does not fit, the run returns `GBB_STOP_NO_PROGRESS` without
starting that operation. A live clock already above the cap returns
`GBB_STOP_INVALID_STATE` before mutation. Exact-cap states remain eligible for
save, load and resave.

Signed values use an explicit modulo-`2^64` representation rather than dumping
native signed objects. The decoder reconstructs negative values as
`-1 - (UINT64_MAX - encoded)`, after checking that the magnitude is representable;
out-of-range casts are not used. Audio limits are checked as a reachable
invariant, not as a guessed general-purpose numeric range:

| Bound | Derived limit |
|---|---:|
| Audio mix level | `-32768..28672` |
| Maximum mix delta | `61440` |
| Maximum coefficient delta | `32767` |
| Maximum edge contribution | `2013204480` |
| Maximum single edge half-dot lifetime | `2797` |
| Maximum ring lifetime envelope | `5630932930560` |
| High-pass input/output history | `INT16_MIN..INT16_MAX` |

The 16-slot ring check accounts for each slot's position relative to the head
and current sample phase. It bounds additions over the slot's remaining
lifetime. The executable `state_audio_bound` proof checks channel mix, edge,
coefficient, rounding, high-pass and lifetime arithmetic at the limiting
domains. The maximum admitted descriptor body is 320184 bytes, including the
maximum 131072-byte cartridge RAM; with the header the maximum emitted state is
320248 bytes. The separate 524288-byte format ceiling is an additional bound.
The installed DMG tracer currently emits 189176 bytes for its ROM and profile.

## Field census and accepted domains

The executable census below is emitted through the private `state_record_field` helper and checked against all 198 descriptors. Offsets are body offsets measured with the maximum 131072-byte cartridge RAM. For a ROM with fewer RAM bytes, subtract `131072 - cartridge_ram_size` from every offset after `cartridge_ram`; all later widths and counts remain fixed. Both profiles and all execution modes use this descriptor order. The columns are descriptor order, qualified path, maximum-RAM body offset, maximum element count, wire width in bytes, and treatment.

| Order | Qualified id | Offset | Max count | Width | Treatment |
|---:|---|---:|---:|---:|---|
| 0 | `cartridge_ram` | 0 | 131072 | 1 | serialize |
| 1 | `cart.rom_bank_lo` | 131072 | 1 | 1 | serialize |
| 2 | `cart.rom_bank_hi` | 131073 | 1 | 1 | serialize |
| 3 | `cart.ram_bank` | 131074 | 1 | 1 | serialize |
| 4 | `cart.ram_enabled` | 131075 | 1 | 1 | serialize |
| 5 | `cart.mbc1_mode` | 131076 | 1 | 1 | serialize |
| 6 | `cart.rumble_on` | 131077 | 1 | 1 | serialize |
| 7 | `cart.rtc_s` | 131078 | 1 | 1 | serialize |
| 8 | `cart.rtc_m` | 131079 | 1 | 1 | serialize |
| 9 | `cart.rtc_h` | 131080 | 1 | 1 | serialize |
| 10 | `cart.rtc_dl` | 131081 | 1 | 1 | serialize |
| 11 | `cart.rtc_dh` | 131082 | 1 | 1 | serialize |
| 12 | `cart.rtc_l` | 131083 | 5 | 1 | serialize |
| 13 | `cart.rtc_latch_prev` | 131088 | 1 | 1 | serialize |
| 14 | `cart.rtc_sub` | 131089 | 1 | 4 | serialize |
| 15 | `cart.rtc_synced_at` | 131093 | 1 | 8 | serialize |
| 16 | `wram` | 131101 | 32768 | 1 | serialize |
| 17 | `hram` | 163869 | 127 | 1 | serialize |
| 18 | `vram` | 163996 | 16384 | 1 | serialize |
| 19 | `oam` | 180380 | 160 | 1 | serialize |
| 20 | `vram_bank` | 180540 | 1 | 1 | serialize |
| 21 | `wram_bank` | 180541 | 1 | 1 | serialize |
| 22 | `svbk` | 180542 | 1 | 1 | serialize |
| 23 | `key1_armed` | 180543 | 1 | 1 | serialize |
| 24 | `bcps` | 180544 | 1 | 1 | serialize |
| 25 | `ocps` | 180545 | 1 | 1 | serialize |
| 26 | `ff56` | 180546 | 1 | 1 | serialize |
| 27 | `ff72` | 180547 | 1 | 1 | serialize |
| 28 | `ff73` | 180548 | 1 | 1 | serialize |
| 29 | `ff74` | 180549 | 1 | 1 | serialize |
| 30 | `ff75` | 180550 | 1 | 1 | serialize |
| 31 | `double_speed` | 180551 | 1 | 1 | serialize |
| 32 | `cpu_stall_kind` | 180552 | 1 | 1 | serialize |
| 33 | `stop_switch_pending` | 180553 | 1 | 1 | serialize |
| 34 | `cpu_stall_half_dots` | 180554 | 1 | 4 | serialize |
| 35 | `bg_cram` | 180558 | 64 | 1 | serialize |
| 36 | `obj_cram` | 180622 | 64 | 1 | serialize |
| 37 | `opri` | 180686 | 1 | 1 | serialize |
| 38 | `frame_working` | 180687 | 23040 | 1 | serialize |
| 39 | `frame_completed` | 203727 | 23040 | 1 | serialize |
| 40 | `rgb_working` | 226767 | 23040 | 2 | serialize |
| 41 | `rgb_completed` | 272847 | 23040 | 2 | serialize |
| 42 | `compat_rgb555` | 318927 | 12 | 2 | serialize |
| 43 | `frame_generation` | 318951 | 1 | 8 | serialize |
| 44 | `frame_completion_half_dots` | 318959 | 1 | 8 | serialize |
| 45 | `ppu_dot` | 318967 | 1 | 2 | serialize |
| 46 | `ppu_half_phase` | 318969 | 1 | 1 | serialize |
| 47 | `ppu_mode` | 318970 | 1 | 1 | serialize |
| 48 | `ppu_stat_line` | 318971 | 1 | 1 | serialize |
| 49 | `ppu_fifo` | 318972 | 16 | 1 | serialize |
| 50 | `ppu_fifo_head` | 318988 | 1 | 1 | serialize |
| 51 | `ppu_fifo_count` | 318989 | 1 | 1 | serialize |
| 52 | `ppu_fetch_stage` | 318990 | 1 | 1 | serialize |
| 53 | `ppu_fetch_phase` | 318991 | 1 | 1 | serialize |
| 54 | `ppu_fetch_enqueued` | 318992 | 1 | 2 | serialize |
| 55 | `ppu_transfer_age` | 318994 | 1 | 1 | serialize |
| 56 | `ppu_output_x` | 318995 | 1 | 1 | serialize |
| 57 | `ppu_scroll_discard` | 318996 | 1 | 1 | serialize |
| 58 | `ppu_fine_scroll` | 318997 | 1 | 1 | serialize |
| 59 | `ppu_mode3_stall` | 318998 | 1 | 1 | serialize |
| 60 | `ppu_window_started` | 318999 | 1 | 1 | serialize |
| 61 | `ppu_transfer_complete` | 319000 | 1 | 1 | serialize |
| 62 | `ppu_objects_stalled` | 319001 | 1 | 2 | serialize |
| 63 | `ppu_object_tiles_fetched` | 319003 | 1 | 4 | serialize |
| 64 | `ppu_selected_objects` | 319007 | 10 | 1 | serialize |
| 65 | `ppu_selected_y` | 319017 | 10 | 1 | serialize |
| 66 | `ppu_selected_x` | 319027 | 10 | 1 | serialize |
| 67 | `ppu_selected_tile` | 319037 | 10 | 1 | serialize |
| 68 | `ppu_selected_attributes` | 319047 | 10 | 1 | serialize |
| 69 | `ppu_selected_object_count` | 319057 | 1 | 1 | serialize |
| 70 | `ppu_scan_index` | 319058 | 1 | 1 | serialize |
| 71 | `ppu_window_line` | 319059 | 1 | 1 | serialize |
| 72 | `ppu_window_line_drawn` | 319060 | 1 | 1 | serialize |
| 73 | `lcdc` | 319061 | 1 | 1 | serialize |
| 74 | `scy` | 319062 | 1 | 1 | serialize |
| 75 | `scx` | 319063 | 1 | 1 | serialize |
| 76 | `ly` | 319064 | 1 | 1 | serialize |
| 77 | `lyc` | 319065 | 1 | 1 | serialize |
| 78 | `bgp` | 319066 | 1 | 1 | serialize |
| 79 | `obp0` | 319067 | 1 | 1 | serialize |
| 80 | `obp1` | 319068 | 1 | 1 | serialize |
| 81 | `wy` | 319069 | 1 | 1 | serialize |
| 82 | `wx` | 319070 | 1 | 1 | serialize |
| 83 | `dma_register` | 319071 | 1 | 1 | serialize |
| 84 | `dma_page` | 319072 | 1 | 1 | serialize |
| 85 | `dma_pending_page` | 319073 | 1 | 1 | serialize |
| 86 | `dma_index` | 319074 | 1 | 1 | serialize |
| 87 | `dma_phase` | 319075 | 1 | 1 | serialize |
| 88 | `dma_active` | 319076 | 1 | 1 | serialize |
| 89 | `dma_start_pending` | 319077 | 1 | 1 | serialize |
| 90 | `dma_cpu_blocked` | 319078 | 1 | 1 | serialize |
| 91 | `hdma.mode` | 319079 | 1 | 1 | serialize |
| 92 | `hdma.active` | 319080 | 1 | 1 | serialize |
| 93 | `hdma.pending_hblank` | 319081 | 1 | 1 | serialize |
| 94 | `hdma.blocks_remaining` | 319082 | 1 | 2 | serialize |
| 95 | `hdma.byte_index` | 319084 | 1 | 1 | serialize |
| 96 | `hdma.byte_phase` | 319085 | 1 | 1 | serialize |
| 97 | `hdma.source_cursor` | 319086 | 1 | 2 | serialize |
| 98 | `hdma.destination_cursor` | 319088 | 1 | 4 | serialize |
| 99 | `hdma.block_vram_bank` | 319092 | 1 | 1 | serialize |
| 100 | `hdma.source_high` | 319093 | 1 | 1 | serialize |
| 101 | `hdma.source_low` | 319094 | 1 | 1 | serialize |
| 102 | `hdma.destination_high` | 319095 | 1 | 1 | serialize |
| 103 | `hdma.destination_low` | 319096 | 1 | 1 | serialize |
| 104 | `hdma.control_readback` | 319097 | 1 | 1 | serialize |
| 105 | `joypad_select` | 319098 | 1 | 1 | serialize |
| 106 | `joypad_buttons` | 319099 | 1 | 1 | serialize |
| 107 | `a` | 319100 | 1 | 1 | serialize |
| 108 | `f` | 319101 | 1 | 1 | serialize |
| 109 | `b` | 319102 | 1 | 1 | serialize |
| 110 | `c` | 319103 | 1 | 1 | serialize |
| 111 | `d` | 319104 | 1 | 1 | serialize |
| 112 | `e` | 319105 | 1 | 1 | serialize |
| 113 | `h` | 319106 | 1 | 1 | serialize |
| 114 | `l` | 319107 | 1 | 1 | serialize |
| 115 | `div` | 319108 | 1 | 1 | serialize |
| 116 | `stat` | 319109 | 1 | 1 | serialize |
| 117 | `tima` | 319110 | 1 | 1 | serialize |
| 118 | `tma` | 319111 | 1 | 1 | serialize |
| 119 | `tac` | 319112 | 1 | 1 | serialize |
| 120 | `ie` | 319113 | 1 | 1 | serialize |
| 121 | `interrupt_flags` | 319114 | 1 | 1 | serialize |
| 122 | `ime_delay` | 319115 | 1 | 1 | serialize |
| 123 | `ime` | 319116 | 1 | 1 | serialize |
| 124 | `divider_phase` | 319117 | 1 | 1 | serialize |
| 125 | `divider_counter` | 319118 | 1 | 2 | serialize |
| 126 | `timer_signal` | 319120 | 1 | 1 | serialize |
| 127 | `timer_reload_pending` | 319121 | 1 | 1 | serialize |
| 128 | `timer_reload_remaining` | 319122 | 1 | 1 | serialize |
| 129 | `timer_reloaded_at` | 319123 | 1 | 8 | serialize |
| 130 | `instruction_start_half_dots` | 319131 | 1 | 8 | serialize |
| 131 | `serial_data` | 319139 | 1 | 1 | serialize |
| 132 | `serial_control` | 319140 | 1 | 1 | serialize |
| 133 | `serial_bits` | 319141 | 1 | 1 | serialize |
| 134 | `serial_edge_remaining` | 319142 | 1 | 2 | serialize |
| 135 | `serial_active` | 319144 | 1 | 1 | serialize |
| 136 | `bus_unsupported` | 319145 | 1 | 1 | serialize |
| 137 | `bus_unsupported_address` | 319146 | 1 | 2 | serialize |
| 138 | `halted` | 319148 | 1 | 1 | serialize |
| 139 | `stopped` | 319149 | 1 | 1 | serialize |
| 140 | `halt_bug` | 319150 | 1 | 1 | serialize |
| 141 | `pc` | 319151 | 1 | 2 | serialize |
| 142 | `sp` | 319153 | 1 | 2 | serialize |
| 143 | `time_half_dots` | 319155 | 1 | 8 | serialize |
| 144 | `input_event_count` | 319163 | 1 | 1 | serialize |
| 145 | `input_events[].at_half_dots` | 319164 | 64 | 8 | serialize |
| 146 | `input_events[].kind` | 319676 | 64 | 1 | serialize |
| 147 | `input_events[].value` | 319740 | 64 | 1 | serialize |
| 148 | `lockup_pc` | 319804 | 1 | 2 | serialize |
| 149 | `lockup_opcode` | 319806 | 1 | 1 | serialize |
| 150 | `locked` | 319807 | 1 | 1 | serialize |
| 151 | `apu_nr50` | 319808 | 1 | 1 | serialize |
| 152 | `apu_nr51` | 319809 | 1 | 1 | serialize |
| 153 | `apu_power` | 319810 | 1 | 1 | serialize |
| 154 | `apu_sequencer_step` | 319811 | 1 | 1 | serialize |
| 155 | `apu_pulse[].sweep` | 319812 | 2 | 1 | serialize |
| 156 | `apu_pulse[].duty_length` | 319814 | 2 | 1 | serialize |
| 157 | `apu_pulse[].envelope` | 319816 | 2 | 1 | serialize |
| 158 | `apu_pulse[].frequency_low` | 319818 | 2 | 1 | serialize |
| 159 | `apu_pulse[].control` | 319820 | 2 | 1 | serialize |
| 160 | `apu_pulse[].length` | 319822 | 2 | 2 | serialize |
| 161 | `apu_pulse[].frequency` | 319826 | 2 | 2 | serialize |
| 162 | `apu_pulse[].timer` | 319830 | 2 | 2 | serialize |
| 163 | `apu_pulse[].sweep_shadow` | 319834 | 2 | 2 | serialize |
| 164 | `apu_pulse[].phase` | 319838 | 2 | 1 | serialize |
| 165 | `apu_pulse[].volume` | 319840 | 2 | 1 | serialize |
| 166 | `apu_pulse[].envelope_timer` | 319842 | 2 | 1 | serialize |
| 167 | `apu_pulse[].sweep_timer` | 319844 | 2 | 1 | serialize |
| 168 | `apu_pulse[].enabled` | 319846 | 2 | 1 | serialize |
| 169 | `apu_pulse[].sweep_enabled` | 319848 | 2 | 1 | serialize |
| 170 | `apu_pulse[].sweep_negate_used` | 319850 | 2 | 1 | serialize |
| 171 | `apu_wave.dac` | 319852 | 1 | 1 | serialize |
| 172 | `apu_wave.length_reg` | 319853 | 1 | 1 | serialize |
| 173 | `apu_wave.level` | 319854 | 1 | 1 | serialize |
| 174 | `apu_wave.frequency_low` | 319855 | 1 | 1 | serialize |
| 175 | `apu_wave.control` | 319856 | 1 | 1 | serialize |
| 176 | `apu_wave.sample_buffer` | 319857 | 1 | 1 | serialize |
| 177 | `apu_wave.ram` | 319858 | 16 | 1 | serialize |
| 178 | `apu_wave.position` | 319874 | 1 | 1 | serialize |
| 179 | `apu_wave.length` | 319875 | 1 | 2 | serialize |
| 180 | `apu_wave.timer` | 319877 | 1 | 2 | serialize |
| 181 | `apu_wave.enabled` | 319879 | 1 | 1 | serialize |
| 182 | `apu_noise.length_reg` | 319880 | 1 | 1 | serialize |
| 183 | `apu_noise.envelope` | 319881 | 1 | 1 | serialize |
| 184 | `apu_noise.polynomial` | 319882 | 1 | 1 | serialize |
| 185 | `apu_noise.control` | 319883 | 1 | 1 | serialize |
| 186 | `apu_noise.volume` | 319884 | 1 | 1 | serialize |
| 187 | `apu_noise.envelope_timer` | 319885 | 1 | 1 | serialize |
| 188 | `apu_noise.length` | 319886 | 1 | 2 | serialize |
| 189 | `apu_noise.lfsr` | 319888 | 1 | 2 | serialize |
| 190 | `apu_noise.timer` | 319890 | 1 | 4 | serialize |
| 191 | `apu_noise.enabled` | 319894 | 1 | 1 | serialize |
| 192 | `apu_sample_phase` | 319895 | 1 | 8 | serialize |
| 193 | `audio_event_ring` | 319903 | 32 | 8 | serialize |
| 194 | `audio_event_head` | 320159 | 1 | 1 | serialize |
| 195 | `audio_mix_level` | 320160 | 2 | 4 | serialize |
| 196 | `audio_hpf_input` | 320168 | 2 | 4 | serialize |
| 197 | `audio_hpf_output` | 320176 | 2 | 4 | serialize |

### Scalar, array, and relationship rules

Each decoded value must fit its descriptor's 1-, 2-, 4-, or 8-byte little-endian wire width. The rules below narrow that domain where the core consumes a value as a flag, index, mask, countdown, or hardware register. Array items use the same descriptor rule per element unless an index-specific rule is stated.

| Field or group | Accepted values |
|---|---|
| Boolean storage | Exactly 0 or 1. |
| `cartridge_ram` | Any byte except MBC2, which requires exactly `0xF0 | nibble` (upper nibble F). RAM length is derived from the ROM. |
| `cart.*` mapper state | Register masks and bank limits follow the loaded mapper: ROM-only retains bank 1 and no RAM enable; MBC1 uses 5-bit low bank, 2-bit high bank and 1-bit mode; MBC2/MBC3 ROM-bank registers are masked by loaded ROM size; MBC3 RAM/RTC selector retains any byte; MBC5 high ROM bank is 1 bit and RAM bank is 4 bits, or 3 bits with rumble. ROM-only derived flags and mapper capabilities cannot be invented. |
| `cart.rtc_s`, `cart.rtc_m`, `cart.rtc_l[0..1]` | 0..63. |
| `cart.rtc_h`, `cart.rtc_l[2]` | 0..31. |
| `cart.rtc_dh`, `cart.rtc_l[4]` | Only bits 0, 6, and 7; `rtc_latch_prev` remains a full byte because every latch write is retained. |
| `cart.rtc_sub` | 0..`RTC_SUB_MASK`. RTC live and latched fields are zero on cartridges without a timer. Rumble is zero when the loaded cartridge has no rumble line. |
| `frame_working`, `frame_completed` | Each DMG shade is 0..3. |
| `rgb_working`, `rgb_completed`, `compat_rgb555` | RGB555 bit 15 is clear. |
| `bg_cram`, `obj_cram` | Any byte. Palette RAM keeps all eight bits written through BCPD/OCPD, including bit 7 of a colour's high byte; colour lookup ignores bit 15 when rendering. |
| `vram_bank`, `hdma.block_vram_bank` | 0 or 1. `wram_bank` is 1..7; raw `svbk` is 0..7 and the selected bank is `svbk == 0 ? 1 : svbk`. DMG pins VRAM bank to 0, WRAM bank to 1, and SVBK to 0. |
| `key1_armed`, `double_speed`, `stop_switch_pending`, `ppu_stat_line`, `ppu_window_started`, `ppu_transfer_complete`, DMA/HDMA activity flags | 0 or 1. CGB speed-switch state is unavailable on the DMG profile. |
| `bcps`, `ocps` | Full byte is preserved. The $40 read-as-one bit is present in post-boot compatibility state; palette consumers mask the index to 6 bits. |
| `f` | Low four bits are zero. |
| `joypad_select` | Only bits 4 and 5. `joypad_buttons` is a full byte. |
| `interrupt_flags` | Only bits 0..4. `ie` is 0..31 on DMG and a full byte on CGB. `stat` stores only bits 3..6. |
| `ppu_dot`, `ppu_half_phase`, `ppu_mode` | Dot 0..455, half-phase 0..1, mode 0..3. `ly` is 0..153 (it wraps at 154, and LCD on/off writes set it to 0); 154..255 is refused. |
| `ppu_fifo` | Each slot is `0xFF` (fine-scroll discard) or 0..159. Head is 0..15 and count 0..16. |
| `ppu_fetch_stage`, `ppu_fetch_phase`, `ppu_fetch_enqueued` | Stage 0..3, phase 0..1, enqueued pixels at most 160 plus the fine-scroll offset (0..7). |
| `ppu_transfer_age`, `ppu_output_x`, `ppu_scroll_discard`, `ppu_fine_scroll`, `ppu_mode3_stall` | Age at most 12, output x at most 160, fine/discard at most 7, mode-3 stall at most 11. |
| `ppu_selected_objects`, `ppu_selected_object_count`, `ppu_objects_stalled` | Every saved OAM index is 0..39; selected count is at most 10; stalled-object bits name only selected slots (`ppu_objects_stalled >> ppu_selected_object_count == 0`), because the core clears them together with the selection at each OAM scan start and on LCD off. `ppu_scan_index` is at most 40. Window line is at most 144. |
| OAM DMA | Index is at most 160 and phase is 0..3. An active transfer has index at most 159, because the transfer ends as the index reaches 160; `dma_active = 1` with index 160 is refused. The serialized DMA page/register and byte state are retained across its in-flight boundary. |
| HDMA registers | Source high is retained as a full byte; source low and destination low have a zero low nibble; destination high is 0..31; control readback preserves the byte produced by FF55 writes and transfer completion. |
| HDMA | Mode 0..2, byte index 0..15, phase 0..3, blocks at most 128. The per-block VRAM bank is 0 or 1. Destination cursor is either `0x0000..0x00F0` with a zero low nibble (the reset cursor 0 after FF54 writes but before any FF53 write, which is the only write that sets the high byte and always adds `0x8000`) or an absolute VRAM address `0x8000..0xA000`; `0xA000` is the legal cursor just after the final block. An active source span must be aligned and lie in a DMA-readable region; an active block's destination cursor is `0x8000..0x9FF0`, the range the engine admits, so its 16-byte span stays within VRAM. |
| CPU, timer, serial and time | IME delay at most 2; TAC at most 7; timer reload at most 4 CPU ticks; serial bits at most 8 and remaining edge at most 512 ticks; ordinary time at most `2^62`, with `UINT64_MAX` allowed only for the timer reload timestamp sentinel. |
| `apu_power`, `apu_pulse[].enabled`, `apu_wave.enabled`, `apu_noise.enabled`, sweep flags | 0 or 1. Sequencer step is 0..7. |
| Pulse channels | Phase 0..7, volume 0..15, envelope/sweep timers at most 8, frequency and sweep shadow at most 2047, length at most 64, timer at most 65472 (the maximum 16-bit-truncated reload over the 11-bit frequency domain), sweep at most `0x7F`, control contains only mask `0x47`. Envelope and duty/length register bytes are retained raw. |
| Wave channel | DAC is 0 or `0x80`; level contains only mask `0x60`; control contains only `0x47`; position at most 31, length at most 256, timer at most 4096. Length register, sample buffer and wave RAM are bytes. |
| Noise channel | Length register at most `0x3F`, control is 0 or `0x40`, volume at most 15, envelope timer at most 8, length at most 64, LFSR at most `0x7FFF`, period timer at most `112 << 16` (7,340,032), from NR43 divisor 112, shift 15 and the period helper's factor of 2. Envelope and polynomial are retained raw. |
| Audio synthesis | Signed mix levels, event-ring lifetimes and high-pass history use the reachable arithmetic bounds above; values are validated and never normalized. |

Cross-field validation is read-only and runs before apply. It binds mapper registers to immutable ROM-derived capabilities; keeps the visible DIV byte equal to the high byte of the divider counter and timer signal equal to its selected divider tap; requires pending timer reloads to have a remaining countdown and completed reloads to have none; binds internal serial clocks to an active transfer and a 1..512 edge countdown; requires an active OAM DMA to have an index below 160; requires active/pending HDMA to have nonzero blocks, aligned cursors, legal CGB-native source and destination spans, and mutually exclusive active/pending state; and checks selected-object masks, input queue order and zeroed unused slots. A rejected state leaves the receiving instance untouched. Accepted bytes are applied without allocation, ROM hashing, or repair/normalization.

## Validation and mutation behavior

`gbb_state_size` and `gbb_save_state` require a loaded ROM and a live machine
that satisfies the state invariants. `gbb_save_state` writes exactly the
reported byte count and preserves any caller buffer tail. `gbb_load_state`
requires the exact state length; it validates the complete header, CRC, every
field and cross-field invariant before applying any state. A rejected load does
not mutate the destination. The API checks in this order:

| Condition | Result |
|---|---|
| Null required pointer | `GBB_INVALID_ARGUMENT` |
| State shorter than 64 bytes or wrong magic | `GBB_STATE_BAD_FORMAT` |
| Unsupported format/header/release/behavior version | `GBB_STATE_UNSUPPORTED_VERSION` |
| Destination has no ROM | `GBB_STATE_NO_ROM` |
| Profile, mode or ROM digest differs | `GBB_STATE_IDENTITY_MISMATCH` |
| Declared body/total or supplied exact length differs | `GBB_STATE_SIZE_MISMATCH` |
| CRC mismatch | `GBB_STATE_CORRUPT` |
| Reserved bytes or semantic invariant invalid | `GBB_STATE_INVALID_CONTENT` |
| Save buffer is shorter than the required size | `GBB_BUFFER_TOO_SMALL` |
| State bytes overlap the destination instance | `GBB_INVALID_ARGUMENT` |

`gbb_state_size` and `gbb_save_state` return `GBB_STATE_INVALID_CONTENT` for a live machine that breaks a state invariant; states produced by this emulator are not expected to.

The first seven state errors use the frozen public values 21 through 27 in the
order shown by the API enum. `out_size` and save output remain untouched on an
error. Input/output state buffers must be stable for the call and must not
overlap the instance. Calls on one instance must be externally serialized;
separate instances and their caller-owned buffers are independent. The codec
does not allocate memory or hash the ROM per call; the digest is computed once
after a successful ROM load. Loading replaces serialized machine state,
including cartridge RAM, RTC and compatibility palette, while host-side
observer history remains local to the receiving instance.

The format is evidence for the bootless DMG-CPU-B and modeled CGB profiles,
including the installed continuation tests. It does not claim physical-device
equivalence or acceptance of arbitrary third-party state containers. See
[`cartridge-and-saves.md`](cartridge-and-saves.md) for the API ownership
contract and the separate battery persistence formats.

## Portable pins and compatibility dispositions

`tests/baseline/state-goldens-v1.json` pins the canonical bytes for the listed
synthetic DMG, CGB compatibility, and CGB native fixtures. The pin checker reads
source and the selected compatibility base by immutable commit ID, then compares
the compiled codec output with those committed bytes. Native CI passes the
pull-request base or push parent into that check and retains a path-free receipt
for each Linux, macOS, and Windows job. Receipts identify the source and base
commits, the compiled executable digest, the source-input digest, the fixture
descriptors, and the platform label.

The first state pins establish the initial baseline at release 0.2.1. The
mainline base used to introduce state support had no format or behavior tokens;
the Phase 17 entry base had tokens 1 and 1 but no golden pins. The compatibility
ledger records both cases explicitly. This decision does not promise that
arbitrary unreleased commits sharing version tokens can exchange states. Later
pin changes require an exact old/new digest disposition, independent continuation
evidence present at the immutable base, and the applicable release, format, or
behavior token change. A local receipt does not qualify Linux, macOS, and Windows
together; that claim requires receipts from the same hosted source revision.
Phase 19 regenerates and requalifies the pins when the release becomes 0.3.0.
