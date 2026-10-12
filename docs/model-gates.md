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
| GATE-00 | BOTH | - | basis="model-neutral function; see its branch gates" | any function | shared id for model-neutral function tags |
| GATE-01 | UNKNOWN | - | research:14 | audio_process_sample | high-pass filter constant differs by model |
| GATE-02 | UNKNOWN | - | research:11 | ppu_update_stat_line | STAT interrupt line edge timing is unresearched for CGB |
| GATE-03 | UNKNOWN | - | research:10 | reset_state | post-boot F depends on the header checksum and CGB compatibility mode |
| GATE-04 | UNKNOWN | - | research:10 | reset_state | post-boot DIV differs by model; the table lands in Plan 10-06 |
| GATE-05 | UNKNOWN | - | research:10 | reset_state | post-boot SC differs by model |
| GATE-06 | UNKNOWN | - | research:10 | reset_state | post-boot IF differs by model |
| GATE-07 | UNKNOWN | - | research:10 | reset_state | post-boot APU register literals differ by model |
| GATE-08 | UNKNOWN | - | research:10 | reset_state | post-boot DMA register differs by model |
| GATE-09 | BOTH | - | basis=D-025 | reset_state | RAM fill is emulator policy; hardware power-on RAM is unspecified |
| GATE-10 | UNKNOWN | - | research:11 | reset_state | post-boot PPU mode, LY and STAT literals differ by model |
| GATE-11 | BOTH | - | basis=PANDOCS | reset_state | LCDC, BGP and OBP post-boot values are common to both models |
| GATE-12 | BOTH | - | basis=pandocs-joyp | joypad_value | P1 button and direction select lines are the same on both models |
| GATE-13 | UNKNOWN | - | research:11 | cpu_vram_access_allowed | VRAM CPU lock window during mode 3 |
| GATE-14 | UNKNOWN | - | research:11 | cpu_oam_access_allowed | OAM CPU lock window during modes 2 and 3 |
| GATE-15 | UNKNOWN | - | research:14 | apu_power_off | NR52 power-off effect on APU state and wave RAM |
| GATE-16 | UNKNOWN | - | expected-failure:cgb-separate-buses | read8 | OAM-DMA CPU bus conflict: CGB uses separate buses (D-17) |
| GATE-17 | UNKNOWN | - | research:14 | read8 | SC unused bits read differently on CGB (fast clock bit) |
| GATE-18 | UNKNOWN | - | research:14 | read8 | APU read masks, including NR52 length bits |
| GATE-19 | UNKNOWN | - | research:14 | read8 | wave RAM access aliasing while the channel is enabled |
| GATE-20 | UNKNOWN | - | research:11 | read8 | STAT mode and coincidence bits at LCD transitions |
| GATE-21 | UNKNOWN | - | research:10 | read8 | IF and IE unused-bit masks; the IE gate lands in Plan 10-09 |
| GATE-22 | BOTH | - | basis=cartridge-side | read8 | ROM reads are decided by the mapper, not the console |
| GATE-23 | BOTH | - | basis=wram-echo-map | read8 | work RAM and echo mapping; CGB WRAM banking is added by a later plan |
| GATE-24 | UNKNOWN | - | research:14 | timer_increment | TIMA overflow and reload timing |
| GATE-25 | UNKNOWN | - | expected-failure:cgb-separate-buses | write8 | OAM-DMA CPU bus conflict: CGB uses separate buses (D-17) |
| GATE-26 | BOTH | - | basis=cartridge-side | write8 | mapper register writes are decided by the cartridge |
| GATE-27 | UNKNOWN | - | research:14 | write8 | JOYP write select and IF side effects |
| GATE-28 | UNKNOWN | - | research:11 | write8 | LCDC bit 0 meaning and LCD on and off timing |
| GATE-29 | UNKNOWN | - | research:14 | write8 | STAT write spurious interrupt quirk is DMG-specific |
| GATE-30 | UNKNOWN | - | research:12 | write8 | DMA restart and period |
| GATE-31 | UNKNOWN | - | research:12 | write8 | DIV write resets the counter and clocks the frame sequencer |
| GATE-32 | UNKNOWN | - | research:14 | write8 | TAC write glitch timing |
| GATE-33 | UNKNOWN | - | research:14 | write8 | serial data and control write behaviour |
| GATE-34 | UNKNOWN | - | research:14 | write8 | NR52 power-off and power-on behaviour |
| GATE-35 | UNKNOWN | - | research:14 | write8 | wave RAM write aliasing while the channel is enabled |
| GATE-36 | UNKNOWN | - | research:14 | write8 | APU register writes while powered on |
| GATE-37 | UNKNOWN | - | research:10 | write8 | IF and IE write masks; the IE gate lands in Plan 10-09 |
| GATE-38 | BOTH | - | basis=wram-echo-map | write8 | work RAM and echo mapping; CGB WRAM banking is added by a later plan |
| GATE-39 | UNKNOWN | - | research:10 | read_supported | the read allow-list is the DMG register set |
| GATE-40 | UNKNOWN | - | research:14 | read_supported | FEA0-FEFF stays fail-closed on both profiles this phase (A6) |
| GATE-41 | UNKNOWN | - | research:12 | apply_input_events_now | STOP wake conditions |
| GATE-42 | BOTH | - | basis="no SM83 opcode difference" | instruction_address | HALT bug PC repeat is an SM83 trait |
| GATE-43 | UNKNOWN | - | research:11 | ppu_background_color | LCDC bit 0 gates the window on DMG and only priority on CGB; no BG attributes yet |
| GATE-44 | UNKNOWN | - | research:11 | ppu_scan_object | OAM scan against a DMA in flight |
| GATE-45 | UNKNOWN | - | research:11 | ppu_object_color | object priority is by X on DMG and by OAM index on CGB |
| GATE-46 | UNKNOWN | - | research:11 | ppu_pixel_shade | shade composition is the DMG palette path |
| GATE-47 | UNKNOWN | - | research:11 | ppu_fetcher_step | fetcher push timing |
| GATE-48 | UNKNOWN | - | research:11 | ppu_object_should_stall | object fetch during DMA and its transfer timing |
| GATE-49 | UNKNOWN | - | research:11 | ppu_transfer_dot | mode 3 start-up and window stall timing |
| GATE-50 | UNKNOWN | - | research:11 | ppu_advance_dot | line length and LY timing |
| GATE-51 | UNKNOWN | - | research:10 | dma_source_read | DMA source map; banked VRAM and WRAM change it |
| GATE-52 | UNKNOWN | - | research:12 | dma_start | DMA restart behaviour |
| GATE-53 | UNKNOWN | - | research:12 | dma_advance_half_dot | DMA byte period |
| GATE-54 | UNKNOWN | - | research:14 | advance_devices_to | timer reload and IF delay |
| GATE-55 | UNKNOWN | - | research:14 | advance_devices_to | serial internal clock rate |
| GATE-56 | UNKNOWN | - | research:12 | advance_devices_to | frame sequencer taps a DIV bit that moves in double speed |
| GATE-57 | UNKNOWN | - | research:10 | gbb_copy_frame | frame output is DMG shades only |
| GATE-58 | BOTH | - | basis=D-24 | validate_header | header and checksum validation is profile-independent |
| GATE-59 | BOTH | - | basis=profile-argument-validated | gbb_create | profile selection is validated by the caller contract |
| GATE-60 | BOTH | - | basis="no SM83 opcode difference" | decode | illegal-opcode decode is identical on DMG and CGB |
| GATE-61 | BOTH | - | basis="no SM83 opcode difference" | execute | HALT and the halt bug |
| GATE-62 | UNKNOWN | - | research:12 | execute | STOP, including CGB speed switch |
| GATE-63 | BOTH | - | basis="no SM83 opcode difference" | enter_interrupt | interrupt entry timing is a CPU trait |
| GATE-64 | BOTH | - | basis="no SM83 opcode difference" | gbb_run_internal | illegal-opcode lockup is a CPU trait |
| GATE-65 | UNKNOWN | - | research:12 | gbb_run_internal | DIV reset on STOP |
| GATE-66 | BOTH | - | basis=wram-echo-map | gbb_peek_ram | debug peek of work RAM |
<!-- model-gates-end -->

## Release status

`python3 -I tests/scripts/verify-model-gates.py --release` currently fails by design
(`gate-unresolved-unknown`, test `model_gates_release_blocked`): every `research:` row still names a
phase that has not resolved it. Phase 10 resolves the `research:10` and `research:11` rows by
turning them into `DMG_ONLY`/`CGB_ONLY`/`BOTH` classes with guards (Plans 10-04, 10-06, 10-09 and
10-20 assert that none remain). Phase 11 owns the remaining PPU rows noted `research:11`, Phase 12
owns `research:12` (STOP, DMA and double-speed timing) and Phase 14 owns `research:14` (APU, timer,
serial, STAT and JOYP quirks). `expected-failure:cgb-separate-buses` is a declared, reasoned
expected failure (D-17) and does not block release. The release-mode test becomes a pass gate in
Phase 15.
