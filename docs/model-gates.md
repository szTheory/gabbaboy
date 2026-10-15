# Model gates

Decision D-08 requires every behaviour that differs between the original Game Boy (DMG) and Game Boy
Color (CGB) to be declared in the source and in this table, and requires CI to prove the two agree.
`tests/scripts/verify-model-gates.py` reads `src/core/gabbaboy.c` and the table below; it never
writes to either.

## Tag grammar

A tag is a C comment:

```
MODEL: CLASS GATE-NN [GUARD=token] [basis=ref] [research:N] [expected-failure:reason] [-- prose]
```

- `CLASS` is `DMG_ONLY`, `CGB_ONLY`, `BOTH` or `UNKNOWN`.
- `ref` and `reason` are a bare word or a double-quoted string.
- A function tag sits in the comment block directly above the definition (no blank line between).
  A branch tag sits inside a function, directly above the guarded code.
- Table cells repeat the tag: class, `GUARD` token or `-`, and the resolution items in the order
  `basis=`, `research:`, `expected-failure:` (or `-` when there are none).

## Rules

1. **R1** Every top-level function definition carries a `MODEL` tag in the comment block above it.
2. **R2** Code tags and the table rows are a bijection by `GATE` id with identical class, guard and
   resolution. Rows are in ascending id order. An empty table or missing marker pair fails.
3. **R3** `UNKNOWN` needs `research:N` or `expected-failure:reason`. Under `--release` every
   `research:` `UNKNOWN` fails.
4. **R4** `DMG_ONLY` and `CGB_ONLY` need their `GUARD` token in code within the 12 code lines after
   the tag.
5. **R5** A `BOTH` tag without `basis=` fails if the 12 code lines after a branch tag (or the whole
   body of a function tag) contain a hazard token: a `0xFF40` to `0xFF7F` literal, `stopped`,
   `halt_bug`, `dma_`, `apu_power`, `ppu_mode`, or a `return 0xFFu`.

## GATE-00

`GATE-00` is the single shared id for model-neutral function tags (OQ4). It is accepted only with
class `BOTH` and a `basis=`, may repeat in code, and has exactly one row here. Every other `GATE-NN`
occurs exactly once in code and once in the table.

<!-- model-gates-begin -->
| Gate | Class | Guard | Resolution | Site | Note |
| --- | --- | --- | --- | --- | --- |
| GATE-00 | BOTH | - | basis="model-neutral function; hardware-visible model access is declared by its caller branch gate" | any function | shared id for neutral helpers, including PCM channel taps; caller gates declare CGB-only access |
| GATE-01 | UNKNOWN | - | research:14 | audio_process_sample | high-pass filter constant differs by model |
| GATE-02 | UNKNOWN | - | research:14 | ppu_update_stat_line | STAT interrupt line edge timing on CGB is unresearched; deferred by D-09/D-12 |
| GATE-03 | DMG_ONLY | model_is_dmg | - | post_boot_apply | the header-checksum F branch exists on the DMG profile only; CGB F is $80 |
| GATE-04 | BOTH | - | basis="post_boot[] column per profile (D-06)" | post_boot_apply | post-boot DIV differs by model |
| GATE-05 | BOTH | - | basis="post_boot[] column per profile (D-06)" | post_boot_apply | post-boot SC differs by model |
| GATE-06 | BOTH | - | basis="post_boot[] column per profile (D-06)" | post_boot_apply | post-boot IF differs by model |
| GATE-07 | BOTH | - | basis="post_boot[] column per profile (D-06)" | post_boot_apply | post-boot APU register literals differ by model |
| GATE-08 | BOTH | - | basis="post_boot[] column per profile (D-06)" | post_boot_apply | post-boot DMA register differs by model |
| GATE-09 | BOTH | - | basis=D-025 | post_boot_apply | RAM fill is emulator policy; hardware power-on RAM is unspecified |
| GATE-10 | UNKNOWN | - | research:14 | post_boot_apply | post-boot PPU mode, LY and STAT literals differ by model; the CGB mode-3 and line-0 timing question is deferred by D-09/D-12 |
| GATE-11 | BOTH | - | basis=PANDOCS | post_boot_apply | LCDC, BGP and OBP post-boot values are common to both models |
| GATE-12 | BOTH | - | basis=pandocs-joyp | joypad_value | P1 button and direction select lines are the same on both models |
| GATE-13 | UNKNOWN | - | research:14 | cpu_vram_access_allowed | VRAM CPU lock window during mode 3; CGB lock-edge offsets are unresearched and deferred by D-09/D-12 |
| GATE-14 | UNKNOWN | - | research:14 | cpu_oam_access_allowed | OAM CPU lock window during modes 2 and 3; CGB lock-edge offsets are unresearched and deferred by D-09/D-12 |
| GATE-15 | UNKNOWN | - | expected-failure:dmg-length-retention | apu_power_off | CGB-E state clear and Wave RAM retention are guest-tested; DMG length-counter retention remains outside the frozen baseline |
| GATE-16 | UNKNOWN | - | expected-failure:cgb-separate-buses | read8 | OAM-DMA CPU bus conflict: CGB uses separate buses (D-17) |
| GATE-17 | UNKNOWN | - | research:14 | read8 | SC unused bits read differently on CGB (fast clock bit) |
| GATE-18 | BOTH | - | basis=PANDOCS | read8 | APU register masks and NR52 channel-status bits are covered by CGB guest readback and the DMG baseline |
| GATE-19 | BOTH | - | basis="CGB current-byte alias; DMG alias remains scoped software policy" | read8 | active Wave RAM reads alias the current byte; CGB guest coverage and DMG revision baseline are separate evidence |
| GATE-20 | UNKNOWN | - | research:14 | read8 | STAT mode and coincidence bits at LCD transitions; CGB transition timing is unresearched and deferred by D-09/D-12 |
| GATE-21 | CGB_ONLY | model_is_cgb | - | read8 | IE bits 5-7 are stored on the CGB profile (Mooneye unused_hwio-C and unused_hwio-GS); DMG reads them as 1 (OQ2, owner veto item 6) |
| GATE-22 | BOTH | - | basis=cartridge-side | cart_read | ROM reads are decided by the mapper, not the console |
| GATE-23 | BOTH | - | basis=wram-echo-map | read8 | work RAM and echo mapping; CGB WRAM banking is selected in wram_byte |
| GATE-24 | UNKNOWN | - | research:14 | timer_increment | TIMA overflow and reload timing |
| GATE-25 | UNKNOWN | - | expected-failure:cgb-separate-buses | write8 | OAM-DMA CPU bus conflict: CGB uses separate buses (D-17) |
| GATE-26 | BOTH | - | basis=cartridge-side | write8 | mapper register writes are decided by the cartridge |
| GATE-27 | UNKNOWN | - | research:14 | write8 | JOYP write select and IF side effects |
| GATE-28 | UNKNOWN | - | research:14 | write8 | LCD on and off timing; the LCDC bit 0 meaning is carried by the CGB-mode siblings GATE-80 and GATE-81 |
| GATE-29 | UNKNOWN | - | research:14 | write8 | STAT write spurious interrupt quirk is DMG-specific |
| GATE-30 | BOTH | - | basis="OAM DMA start requests and byte period are shared; its CPU-rate conversion is declared by GATE-90" | write8 | FF46 records the pending OAM DMA page and starts the shared transfer period |
| GATE-31 | BOTH | - | basis="DIV reset and frame-sequencer edge use the same selected-speed tap on both models, D-11" | write8 | DIV write resets the counter and clocks the frame sequencer through the shared helper |
| GATE-32 | UNKNOWN | - | research:14 | write8 | TAC write glitch timing |
| GATE-33 | UNKNOWN | - | research:14 | write8 | serial data and control write behaviour |
| GATE-34 | UNKNOWN | - | expected-failure:dmg-length-retention | write8 | CGB-E NR52 off/on behavior is guest-tested; DMG length-counter retention remains outside the frozen baseline |
| GATE-35 | BOTH | - | basis="CGB current-byte alias; DMG alias remains scoped software policy" | write8 | active Wave RAM writes alias the current byte; the CGB guest checks the write/read and latch separation |
| GATE-36 | BOTH | - | basis="APU register writes are gated by NR52 power; Wave RAM is decoded separately" | write8 | CGB off-state writes are ignored except Wave RAM; read masks and post-on state are guest-checked |
| GATE-37 | CGB_ONLY | model_is_cgb | - | write8 | IE bits 5-7 are stored on the CGB profile; DMG keeps IE & $1F (OQ2); interrupt dispatch still masks with $1F |
| GATE-38 | BOTH | - | basis=wram-echo-map | write8 | work RAM and echo mapping; CGB WRAM banking is selected in wram_byte |
| GATE-39 | CGB_ONLY | model_is_cgb | - | read_supported_map | on the CGB profile FF00-FF7F readability comes from io_visibility[]; only DEFERRED read cells stop; the DMG chain is unchanged |
| GATE-40 | UNKNOWN | - | research:14 | read_supported | FEA0-FEFF stays fail-closed on both profiles this phase (A6) |
| GATE-41 | UNKNOWN | - | research:14 | apply_input_events_now | STOP wake conditions outside the armed CGB speed-switch path |
| GATE-42 | BOTH | - | basis="no SM83 opcode difference" | instruction_address | HALT bug PC repeat is an SM83 trait |
| GATE-43 | BOTH | - | basis="DMG semantics: LCDC bit 0 gates BG and window; runs for the DMG profile and compat mode, CGB mode uses ppu_cgb_background" | ppu_background_color | the function now runs only under DMG semantics; the CGB-mode sibling is ppu_cgb_background |
| GATE-44 | UNKNOWN | - | research:14 | ppu_scan_object | OAM scan against a DMA in flight; the CGB scan timing question is deferred by D-09/D-12 |
| GATE-45 | BOTH | - | basis="DMG semantics: object priority by X then OAM index; runs for the DMG profile and compat mode, CGB mode uses ppu_cgb_object" | ppu_object_color | the function now runs only under DMG semantics; the CGB-mode sibling is ppu_cgb_object |
| GATE-46 | BOTH | - | basis="DMG semantics: DMG palette shade composition; runs for the DMG profile and compat mode, CGB mode uses ppu_pixel_cgb" | ppu_pixel_shade | the function now runs only for the DMG profile and compat mode; the CGB-mode sibling is ppu_pixel_cgb |
| GATE-47 | UNKNOWN | - | research:14 | ppu_fetcher_step | fetcher push timing; CGB mode-3 fetcher timing is not claimed and is deferred by D-09/D-12 |
| GATE-48 | UNKNOWN | - | research:14 | ppu_object_should_stall | object fetch during DMA and its transfer timing; CGB mode-3 stall timing is not claimed and is deferred by D-09/D-12 |
| GATE-49 | UNKNOWN | - | research:14 | ppu_transfer_dot | mode 3 start-up and window stall timing; CGB mode-3 length, WX and window-range differences are not claimed and are deferred by D-09/D-12 |
| GATE-50 | UNKNOWN | - | research:14 | ppu_advance_dot | line length and LY timing; CGB line-edge timing is unresearched and deferred by D-09/D-12 |
| GATE-51 | CGB_ONLY | model_is_cgb | - | dma_source_read | OAM DMA reads the cartridge and the banked VRAM and WRAM on the CGB profile (D-16); cartridge and E0-FF cells are PANDOCS or ORACLE_SAMEBOY, not hardware |
| GATE-52 | UNKNOWN | - | expected-failure:cgb-dma-restart-oracle-only | dma_start | restart timing has no CGB-specific oracle |
| GATE-53 | BOTH | - | basis="OAM DMA byte period is measured in CPU ticks and remains common across profiles, D-10" | dma_advance_half_dot | OAM DMA byte period |
| GATE-54 | UNKNOWN | - | research:14 | advance_devices_to | timer reload and IF delay |
| GATE-55 | UNKNOWN | - | research:14 | advance_devices_to | serial internal clock rate |
| GATE-56 | CGB_ONLY | double_speed | - | advance_devices_to | the CGB APU frame sequencer uses the selected DIV tap, bit 12 normal and bit 13 double (D-11) |
| GATE-57 | DMG_ONLY | model_is_dmg | - | gbb_copy_frame | frame output is DMG shades only; the CGB profile returns GBB_UNSUPPORTED_PROFILE (D-05) |
| GATE-58 | BOTH | - | basis=D-24 | validate_header | header and checksum validation is profile-independent |
| GATE-59 | BOTH | - | basis=profile-argument-validated | gbb_create | the switch accepts exactly the two implemented profiles (D-01) |
| GATE-60 | BOTH | - | basis="no SM83 opcode difference" | decode | illegal-opcode decode is identical on DMG and CGB |
| GATE-61 | BOTH | - | basis="no SM83 opcode difference" | execute | HALT and the halt bug |
| GATE-62 | UNKNOWN | - | research:14 | execute | STOP on the DMG, compat and unarmed paths |
| GATE-63 | BOTH | - | basis="no SM83 opcode difference" | enter_interrupt | interrupt entry timing is a CPU trait |
| GATE-64 | BOTH | - | basis="no SM83 opcode difference" | gbb_run_internal | illegal-opcode lockup is a CPU trait |
| GATE-65 | BOTH | - | basis="DIV and the divider phase reset at STOP on both models; shared divider_reset, D-02/D-39" | gbb_run_internal | DIV and divider phase reset through the shared helper on both STOP paths |
| GATE-66 | BOTH | - | basis=wram-echo-map | gbb_peek_ram | debug peek of work RAM |
| GATE-67 | CGB_ONLY | GBB_PROFILE_CGB_CPU_E | - | validate_header | a PGB-flagged $143 is rejected on the CGB profile instead of running in a mode the hardware would not enter (D-03) |
| GATE-68 | CGB_ONLY | model_is_cgb | - | compat_title_registers | compat-mode B and HL are derived from the licensee title sum |
| GATE-69 | CGB_ONLY | model_is_cgb | - | io_cgb_cell | the io_visibility[] column is chosen by profile and execution mode |
| GATE-70 | CGB_ONLY | model_is_cgb | - | io_read_cgb | FF4C-FF7F reads on the CGB profile; native FF56 applies the disconnected-receiver mask from D-07 |
| GATE-71 | CGB_ONLY | model_is_cgb | - | io_write_cgb | FF4C-FF7F writes on the CGB profile; DEFERRED cells latch bus_unsupported, while native FF56 stores its declared bits |
| GATE-72 | CGB_ONLY | model_is_cgb | - | read8 | FF4C-FF7F decode goes through io_visibility[]; the DMG profile falls through unchanged (D-09) |
| GATE-73 | CGB_ONLY | model_is_cgb | - | write8 | FF4C-FF7F decode goes through io_visibility[]; a no-op on the DMG profile (C4) |
| GATE-74 | CGB_ONLY | model_is_cgb | - | execute | CGB mode STOP with KEY1 armed takes the implemented speed-switch path (D-01/D-23) |
| GATE-75 | DMG_ONLY | model_is_dmg | - | dma_source_read | the DMG OAM DMA source map is VRAM and WRAM only; ROM, cartridge RAM and E0-FF read $FF (D-024) |
| GATE-76 | UNKNOWN | - | research:14 | cpu_cram_access_allowed | CRAM CPU lock is a plain mode-3 predicate; edge offsets unresearched (D-12) |
| GATE-77 | UNKNOWN | - | research:14 | io_write_cgb | OPRI is stored without priority effect after boot (D-08) |
| GATE-78 | CGB_ONLY | model_is_cgb | - | write8 | LCD off blanks the RGB working frame to white and keeps the completed RGB frame (D-02) |
| GATE-79 | CGB_ONLY | model_is_cgb | - | ppu_advance_dot | the RGB frame completes with the shade frame on the CGB profile (D-02) |
| GATE-80 | CGB_ONLY | model_is_cgb | - | ppu_transfer_dot | CGB mode resolves RGB555 per dot against live CRAM into rgb_working (D-01, D-02); compat mode routing is plan 11-04 |
| GATE-81 | CGB_ONLY | model_is_cgb | - | ppu_window_should_start | CGB mode enables the window by LCDC bit 5 alone, shifting mode-3 window-start stall timing when LCDC bit 0 is clear; CGB mode-3 timing is not claimed (D-09) |
| GATE-82 | CGB_ONLY | model_is_cgb | - | ppu_transfer_dot | compat mode resolves DMG shades through the instance compat palette into rgb_working and never writes the shade store (D-17, D-39) |
| GATE-83 | CGB_ONLY | model_is_cgb | - | gbb_copy_frame_rgb555 | colour frames are CGB-profile only; the DMG profile returns GBB_UNSUPPORTED_PROFILE (D-15), symmetric with GATE-57 |
| GATE-84 | CGB_ONLY | key1_armed | - | stop_case | an armed CGB-mode STOP selects the speed-switch decision table (D-01/D-02) |
| GATE-85 | UNKNOWN | - | expected-failure:speed-switch-held-button-oracle-only | stop_case | held-button STOP semantics have SameBoy evidence but no independent hardware pin |
| GATE-86 | UNKNOWN | - | expected-failure:speed-switch-pending-irq-oracle-only | stop_case | pending-IRQ switch and instruction-length semantics are not independently pinned |
| GATE-87 | CGB_ONLY | cpu_stalled | - | gbb_run_internal | the CGB speed-switch pause advances through the bounded CPU stall branch (D-06/D-07) |
| GATE-88 | UNKNOWN | - | expected-failure:speed-switch-wake-oracle-only | gbb_run_internal | only the IME-on stall wake has an AGE hardware row; the remaining wake semantics use SameBoy |
| GATE-89 | UNKNOWN | - | expected-failure:speed-switch-odd-mode-alignment | speed_switch_apply_realign | normal-speed entry phase in odd PPU modes remains unsupported (D-09) |
| GATE-90 | CGB_ONLY | double_speed | - | advance_devices_to | cpu_ticks scales instruction cost, bus offsets, interrupt and halt literals, timer reload (GATE-54), serial (GATE-55) and OAM DMA period |
| GATE-91 | CGB_ONLY | model_is_cgb | - | ppu_set_mode | only a visible-line CGB mode-3-to-0 edge latches an ordinary HBlank request |
| GATE-92 | CGB_ONLY | model_is_cgb | - | hdma_request | an armed waiting HBlank request is latched once at the selected safe event boundary |
| GATE-93 | CGB_ONLY | model_is_cgb | - | hdma_source_valid | block admission accepts only ROM, cartridge-mapped A000-BFFF or direct C000-DFFF WRAM |
| GATE-94 | CGB_ONLY | model_is_cgb | - | hdma_source_read | cart_read supplies absent/disabled cartridge bytes as FF; direct WRAM uses wram_byte |
| GATE-95 | CGB_ONLY | model_is_cgb | - | hdma_admit_block | all 16 source addresses and destination offsets validate before mutation; VBK is sampled once |
| GATE-96 | CGB_ONLY | model_is_cgb | - | hdma_advance_half_dot | one byte commits per four master half-dots after OAM and before PPU; 64-half-dot duration is policy |
| GATE-97 | CGB_ONLY | model_is_cgb | - | hdma_register_write | FF55 starts or clears the bounded HBlank request and updates private status |
| GATE-98 | CGB_ONLY | model_is_cgb | - | hdma_stop_at_invalid_block | invalid block stop preserves remaining FF55 status and rejects before the next block mutates |
| GATE-99 | CGB_ONLY | model_is_cgb | - | hdma_start_headroom_available | FF55 starts reserve finite byte-work headroom before master-time overflow |
<!-- model-gates-end -->

## Phase 11 dispositions

Phase 11 resolved or re-assigned every row it owned. A row re-assigned to Phase 14 keeps class
`UNKNOWN`; the reason is that the question is CGB mode-3 timing or lock-edge work that D-09 and D-12
deferred, not colour. `model_gates_no_phase11_rows` fails if a Phase 11 owner tag reappears in this
file or in `src/core/gabbaboy.c`.

| Gate | Site | Outcome | Reason |
| --- | --- | --- | --- |
| GATE-02 | ppu_update_stat_line | re-assigned to Phase 14 | CGB STAT line edge timing is timing work deferred by D-09/D-12 |
| GATE-10 | post_boot_apply | re-assigned to Phase 14 | post-boot PPU mode and line literals on CGB are timing work deferred by D-09/D-12 |
| GATE-13 | cpu_vram_access_allowed | re-assigned to Phase 14 | VRAM lock-edge offsets are lock-edge work deferred by D-09/D-12 |
| GATE-14 | cpu_oam_access_allowed | re-assigned to Phase 14 | OAM lock-edge offsets are lock-edge work deferred by D-09/D-12 |
| GATE-20 | read8 | re-assigned to Phase 14 | STAT bits at LCD transitions are timing work deferred by D-09/D-12 |
| GATE-28 | write8 | split | the LCDC bit 0 meaning is carried by GATE-80 and GATE-81; LCD on and off timing stays with Phase 14 |
| GATE-43 | ppu_background_color | resolved BOTH | DMG semantics only; CGB mode uses ppu_cgb_background (plan 11-03) |
| GATE-44 | ppu_scan_object | re-assigned to Phase 14 | OAM scan against DMA is timing work deferred by D-09/D-12 |
| GATE-45 | ppu_object_color | resolved BOTH | DMG semantics only; CGB mode uses ppu_cgb_object (plan 11-03) |
| GATE-46 | ppu_pixel_shade | resolved BOTH | DMG semantics and compat mode; CGB mode uses ppu_pixel_cgb (plan 11-03) |
| GATE-47 | ppu_fetcher_step | re-assigned to Phase 14 | CGB fetcher push timing is mode-3 timing deferred by D-09/D-12 |
| GATE-48 | ppu_object_should_stall | re-assigned to Phase 14 | object fetch stall timing is mode-3 timing deferred by D-09/D-12 |
| GATE-49 | ppu_transfer_dot | re-assigned to Phase 14 | mode 3 start-up, WX and window-range timing is deferred by D-09/D-12 |
| GATE-50 | ppu_advance_dot | re-assigned to Phase 14 | CGB line length and LY timing is deferred by D-09/D-12 |

## Phase 12 dispositions

The CGB double-speed work resolved the gate rows it owned and returned independent silicon questions
to their researched phase. The shared scanner checks the code tags against the rows above, while
`model_gates_no_phase12_rows` rejects any stale Phase 12 owner marker in this table or the core.

| Gate | Site | Outcome | Reason |
| --- | --- | --- | --- |
| GATE-30 | write8 | resolved BOTH | FF46 records the DMA start request; the common byte period scales through the declared CPU-tick path |
| GATE-31 | write8 | resolved BOTH | DIV reset and APU edge use the shared selected-speed tap (D-11) |
| GATE-41 | apply_input_events_now | re-assigned to Phase 14 | generic STOP wake behavior is outside the armed CGB switch and remains researched there |
| GATE-52 | dma_start | expected failure | restart timing has no CGB-specific oracle (`cgb-dma-restart-oracle-only`) |
| GATE-53 | dma_advance_half_dot | resolved BOTH | the OAM DMA byte period follows CPU ticks at both speeds |
| GATE-54 | advance_devices_to | stays research:14 (single-speed DMG/CGB difference); double-speed scaling is declared by the cpu_ticks row | TIMA reload and IF-delay differences remain Phase 14 work; scaling belongs to GATE-90 |
| GATE-55 | advance_devices_to | stays research:14 (single-speed DMG/CGB difference); double-speed scaling is declared by the cpu_ticks row | serial internal clock and the CGB fast-serial SC bit remain Phase 14 work; scaling belongs to GATE-90 |
| GATE-56 | advance_devices_to | resolved CGB_ONLY | APU frame-sequencer tap follows DIV bit 12 at normal speed and bit 13 at double speed (D-11) |
| GATE-62 | execute | re-assigned to Phase 14 | only DMG, compat and unarmed STOP remain on the original sleep path |
| GATE-65 | gbb_run_internal | resolved BOTH | shared `divider_reset` handles DIV and divider phase on both STOP paths (D-02/D-39) |
| GATE-74 | execute | resolved CGB_ONLY | armed CGB-mode STOP takes the implemented speed-switch path |
| GATE-84 | stop_case | resolved CGB_ONLY | armed CGB STOP selects the four-case decision table |
| GATE-85 | stop_case | expected failure | held-button details have SameBoy coverage only |
| GATE-86 | stop_case | expected failure | pending-IRQ switch and one-byte STOP interpretation lacks an independent hardware pin |
| GATE-87 | gbb_run_internal | resolved CGB_ONLY | persisted speed-switch stall uses a bounded run-loop branch |
| GATE-88 | gbb_run_internal | expected failure | only the IME-on wake has an AGE row; wake behavior remains SameBoy-qualified |
| GATE-89 | speed_switch_apply_realign | expected failure | odd PPU-mode phase alignment is unsupported (D-09) |
| GATE-90 | advance_devices_to | resolved CGB_ONLY | CPU-tick conversion declares each double-speed scaling site, including the timer, serial and OAM DMA paths |

## Phase 13 plan 13-01 dispositions

The tracer implements one ordinary visible-line HBlank block through the existing whole-instruction
run loop. Its safe-boundary, byte cadence and transfer ordering are explicit software policy; no
physical CGB-E transfer timing has been established. `speed-switch-hdma-hblank-across-stall` now
checks only that a guest can program FF55 and read its active one-block status after the switch.

| Gate | Site | Outcome | Reason |
| --- | --- | --- | --- |
| GATE-91 | ppu_set_mode | resolved CGB_ONLY | only the visible mode-3-to-0 edge latches the HBlank request |
| GATE-92 | hdma_request | resolved CGB_ONLY | one pending request is held until the current instruction retires |
| GATE-93 | hdma_source_valid | resolved CGB_ONLY | whole source windows are checked before block admission |
| GATE-94 | hdma_source_read | resolved CGB_ONLY | source map is limited to cart and WRAM helpers |
| GATE-95 | hdma_admit_block | resolved CGB_ONLY | a full block validates before admission and samples VBK once |
| GATE-96 | hdma_advance_half_dot | resolved CGB_ONLY | service consumes bounded master time with the selected four-half-dot cadence |
| GATE-97 | hdma_register_write | resolved CGB_ONLY | FF55 initializes private cursors and exposes active or completed status |
| GATE-99 | hdma_start_headroom_available | resolved CGB_ONLY | accepted FF55 starts reserve checked master-time headroom for their finite byte work |

## Phase 13 plan 13-02 dispositions

The address matrix pins the three admitted windows and rejects echo, VRAM, OAM, FEA0-FEFF, I/O and
HRAM before a block can mutate. Valid prefixes and the rejected block's cursors/count are preserved.
The `$9FF0` final block and widened `$A000` continuation are explicit software policy; no physical
CGB-E bus or overflow status has been measured. These results extend the earlier tracer's gate
resolutions and keep physical timing and arbitration UNKNOWN.

| Gate | Site | Outcome | Reason |
| --- | --- | --- | --- |
| GATE-93 | hdma_source_valid | resolved CGB_ONLY | the narrow map is ROM, cartridge mapping and direct WRAM; echo is rejected |
| GATE-94 | hdma_source_read | resolved CGB_ONLY | mapper reads preserve `$FF` for absent or disabled RAM; WRAM reads use selected bank |
| GATE-95 | hdma_admit_block | resolved CGB_ONLY | all source bytes and the destination are checked before first mutation; VBK is sampled per block |
| GATE-97 | hdma_register_write | resolved CGB_ONLY | cursors continue across blocks; idle writes can repair the widened overflow continuation |
| GATE-98 | hdma_stop_at_invalid_block | resolved CGB_ONLY | invalid source or destination stops with prefix, cursors and remaining FF55 status preserved |

## Phase 13 plan 13-04 dispositions

Accepted FF55 starts reserve enough widened master-time headroom for the instruction and finite
64-half-dot-per-byte transfer work. Rejected starts preserve the CPU, DMA state and output buffers;
the check does not forecast arbitrary HBlank waits.

| Gate | Site | Outcome | Reason |
| --- | --- | --- | --- |
| GATE-99 | hdma_start_headroom_available | resolved CGB_ONLY | finite transfer byte work cannot wrap the master-time counter |

## Phase 14 CGB-E APU dispositions

The native CGB-mode CPU-E guest cases below exercise authored register transitions and timing
boundaries. They are software-model qualification against the pinned Pan Docs contracts and the
SameSuite author expectations; they make no physical CGB-E measurement claim. The DMG software
baseline remains frozen. Pan Docs pins: [Audio Registers](https://github.com/gbdev/pandocs/blob/0191af06ac49661587dcde3d57a241a626b8df75/src/Audio_Registers.md)
and [Audio details](https://github.com/gbdev/pandocs/blob/0191af06ac49661587dcde3d57a241a626b8df75/src/Audio_details.md).

| Gate | Model and mode | Outcome and evidence | Owner | Current signature | Promotion rule |
| --- | --- | --- | --- | --- | --- |
| GATE-15 | CGB-CPU-E, native CGB; DMG-CPU-B baseline | CGB off clears channel registers, resets the sample latch, retains Wave RAM; `cgb_apu_power` | core owner | DMG model also clears NRx1 length counters; hardware retention differs and is not changed in this phase | Resolve only in a DMG-scoped plan with an independent length-retention fixture and an explicit baseline revision |
| GATE-18 | CGB-CPU-E, native CGB; DMG-CPU-B baseline | resolved BOTH; all APU masks, including NR52, `cgb_apu_off_writes` and `cgb_apu_power` | core owner | Fixed read masks and channel status bits; no measurement claim | Reopen only with pinned evidence that contradicts the register contract |
| GATE-19 | CGB-CPU-E, native CGB; DMG-CPU-B software model | resolved BOTH; active current-byte alias and sample-buffer separation, `cgb_apu_wave_access` | core owner | FF30-FF3F reads alias `position >> 1` while CH3 is active | Reopen if a pinned CGB-E case disagrees; keep the DMG alias separately labeled as software policy |
| GATE-34 | CGB-CPU-E, native CGB; DMG-CPU-B baseline | CGB NR52 off/on and DIV continuation pass, `cgb_apu_power`; exact DMG exception remains expected-failure | core owner | Off returns `$70`, on returns `$F0` before any channel is retriggered; global DIV continues | Resolve only with the same DMG-specific fixture and baseline revision required by GATE-15 |
| GATE-35 | CGB-CPU-E, native CGB; DMG-CPU-B software model | resolved BOTH; active aliased write and subsequent fetch, `cgb_apu_wave_access` | core owner | Active FF30-FF3F writes update the currently addressed byte without refilling the CH3 sample latch | Reopen if a pinned CGB-E case disagrees; retain the DMG software-policy boundary |
| GATE-36 | CGB-CPU-E, native CGB; DMG-CPU-B baseline | resolved BOTH; all off-state APU writes ignored except Wave RAM, `cgb_apu_off_writes` | core owner | NR52 gates the register file; Wave RAM remains independently writable | Reopen only with pinned register evidence that contradicts the authored guest contract |

`cgb_apu_div_stop` forces DIV falling edges at bit 12 in normal speed and bit 13 after a guest
STOP speed switch. `cgb_apu_transition_controls` omits the DIV write in paired guests and confirms
the one-count channel remains on, so a missing edge cannot satisfy the positive case. Trigger and
length ordering covers all four channels; the channel-1 sweep guest clears a used negate operation
and verifies that a fresh trigger restarts it. Its expected direction is consistent with the pinned
SameSuite APU README's `channel_1_sweep_restart_2` CGB-E attestation, not with an emulator diff.

## Release status

`python3 -I tests/scripts/verify-model-gates.py --release` currently fails by design
(`gate-unresolved-unknown`, test `model_gates_release_blocked`): each remaining `research:` row
names a phase that has not resolved it. Phase 10 resolved its own rows by turning them into
`DMG_ONLY`/`CGB_ONLY`/`BOTH` classes with guards. Phase 11 resolved or re-assigned every row it was
given (see the dispositions above). The double-speed switch gates are now resolved or explicitly
re-assigned in the Phase 12 dispositions above; Phase 14 resolved the CGB-E APU cases listed above
and retained only the explicit DMG length-retention exception. Timer, serial, STAT, JOYP and CGB
PPU research remains. `expected-failure:cgb-separate-buses` is a declared, reasoned
expected failure (D-17) and does not block release. The release-mode test becomes a pass gate in
Phase 15.
