# CGB profile: post-boot state and evidence classes

This document publishes where each post-boot value of the three profile columns comes from
(DECISIONS D-06) and how strong that evidence is (D-07). The table below is a mirror of the
`post_boot[]` table in `src/core/gabbaboy.c`. `test_cgb_tables` parses it and fails on any
difference from the code, in either direction, so the doc cannot drift quietly.

The columns are: DMG (the DMG-CPU-B profile; the value this core implements, byte-pinned by the
v0.1 baseline), CGB (the CGB-CPU-E profile running a CGB-mode ROM) and COMPAT (the CGB-CPU-E
profile running in DMG compatibility mode, which is also the state with no ROM loaded).

## Evidence classes

| Class | Meaning | Where allowed |
|-------|---------|---------------|
| `HW_TEST` | A named Mooneye hardware test pins the value. | COMPAT column only. |
| `PANDOCS` | Pan Docs documentation. It is prose, not a hardware measurement. | Any column. |
| `ORACLE_SAMEBOY` | A differential oracle (SameBoy). An emulator is not hardware evidence. | Any column. |
| `POLICY` | A deterministic project choice. Every such cell carries a reason. | Any column. |
| `HEADER_DERIVED` | Computed from the ROM header; the cell holds the base value. | Any column. |

Only COMPAT cells carry `HW_TEST`: no hardware test in this project covers CGB mode, and the DMG
column records implemented behaviour, which may differ from Pan Docs (a reason beginning
`diverges-from-pandocs` says so). The `boot_div-cgbABCDE` test applies to CGB revisions A-E, so
the DIV-phase cells are a CGB A-E claim and not a CGB-E-only claim. SameBoy and Pan Docs cells are
never hardware evidence. Values are written `$XX` or `$XXXX`; a header-derived cell shows its
base value and the rule in its reason.

## Post-boot table

<!-- cgb-post-boot-begin -->
| field | column | value | prov | src | reason |
|-------|--------|-------|------|-----|--------|
| a | DMG | $01 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| a | CGB | $11 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| a | COMPAT | $11 | HW_TEST | 4 | Mooneye boot_regs-cgb, compat mode |
| f | DMG | $80 | HEADER_DERIVED | 3 | $B0 when header byte $14D is non-zero, else $80 |
| f | CGB | $80 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| f | COMPAT | $80 | HW_TEST | 4 | Mooneye boot_regs-cgb, compat mode |
| b | DMG | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| b | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| b | COMPAT | $00 | PANDOCS | 1 | Pan Docs: B is the title-byte sum when the licensee is $01 (or $33 with new licensee "01"), else $00; header-derived |
| c | DMG | $13 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| c | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| c | COMPAT | $00 | HW_TEST | 4 | Mooneye boot_regs-cgb, compat mode |
| d | DMG | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| d | CGB | $FF | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| d | COMPAT | $00 | HW_TEST | 4 | Mooneye boot_regs-cgb, compat mode |
| e | DMG | $D8 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| e | CGB | $56 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| e | COMPAT | $08 | HW_TEST | 4 | Mooneye boot_regs-cgb, compat mode |
| h | DMG | $01 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| h | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| h | COMPAT | $00 | HW_TEST | 4 | Mooneye boot_regs-cgb, compat mode |
| l | DMG | $4D | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| l | CGB | $0D | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| l | COMPAT | $7C | HW_TEST | 4 | Mooneye boot_regs-cgb, compat mode |
| sp | DMG | $FFFE | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| sp | CGB | $FFFE | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| sp | COMPAT | $FFFE | HW_TEST | 4 | Mooneye boot_regs-cgb, compat mode |
| pc | DMG | $0100 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| pc | CGB | $0100 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| pc | COMPAT | $0100 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| div | DMG | $AB | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| div | CGB | $26 | POLICY | 8 | no hardware oracle for CGB mode; real hardware varies with the header and held buttons |
| div | COMPAT | $26 | HW_TEST | 6 | Mooneye boot_div-cgbABCDE; applicability CGB A-E, not a CGB-E-only claim |
| divider_counter | DMG | $AB00 | POLICY | 2 | internal 16-bit counter whose high byte is DIV |
| divider_counter | CGB | $2678 | POLICY | 8 | no hardware oracle for CGB mode; real hardware varies with the header and held buttons |
| divider_counter | COMPAT | $2678 | HW_TEST | 6 | Mooneye boot_div-cgbABCDE; applicability CGB A-E, not a CGB-E-only claim |
| divider_phase | DMG | $00 | POLICY | 2 | sub-tick phase of the divider counter starts aligned |
| divider_phase | CGB | $00 | POLICY | 8 | no hardware oracle for CGB mode; real hardware varies with the header and held buttons |
| divider_phase | COMPAT | $00 | HW_TEST | 6 | Mooneye boot_div-cgbABCDE; applicability CGB A-E, not a CGB-E-only claim |
| tima | DMG | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| tima | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| tima | COMPAT | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| tma | DMG | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| tma | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| tma | COMPAT | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| tac | DMG | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| tac | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| tac | COMPAT | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| serial_data | DMG | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| serial_data | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| serial_data | COMPAT | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| serial_control | DMG | $7E | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| serial_control | CGB | $7F | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| serial_control | COMPAT | $7E | HW_TEST | 5 | Mooneye boot_hwio-C, compat mode |
| ie | DMG | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| ie | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| ie | COMPAT | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| if | DMG | $00 | POLICY | 2 | diverges-from-pandocs: IF reads $E0 here; Pan Docs lists $E1 |
| if | CGB | $01 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| if | COMPAT | $01 | HW_TEST | 5 | Mooneye boot_hwio-C, compat mode |
| ime | DMG | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| ime | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| ime | COMPAT | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| nr11 | DMG | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| nr11 | CGB | $80 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| nr11 | COMPAT | $80 | HW_TEST | 5 | Mooneye boot_hwio-C, compat mode |
| nr12 | DMG | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| nr12 | CGB | $F3 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| nr12 | COMPAT | $F3 | HW_TEST | 5 | Mooneye boot_hwio-C, compat mode |
| ch1_enabled | DMG | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| ch1_enabled | CGB | $01 | POLICY | 8 | channel 1 enabled-but-silent: current volume 0, no boot chime is synthesised (A2) |
| ch1_enabled | COMPAT | $01 | POLICY | 8 | channel 1 enabled-but-silent: current volume 0, no boot chime is synthesised (A2) |
| nr50 | DMG | $00 | POLICY | 2 | diverges-from-pandocs: NR50 is 0 here; Pan Docs lists $77 |
| nr50 | CGB | $77 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| nr50 | COMPAT | $77 | HW_TEST | 5 | Mooneye boot_hwio-C, compat mode |
| nr51 | DMG | $FF | POLICY | 2 | diverges-from-pandocs: NR51 is $FF here; Pan Docs lists $F3 |
| nr51 | CGB | $F3 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| nr51 | COMPAT | $F3 | HW_TEST | 5 | Mooneye boot_hwio-C, compat mode |
| apu_power | DMG | $01 | POLICY | 2 | diverges-from-pandocs: NR52 reads $F0 here; Pan Docs lists $F1 (channel 1 on) |
| apu_power | CGB | $01 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| apu_power | COMPAT | $01 | HW_TEST | 5 | Mooneye boot_hwio-C, compat mode |
| dma_register | DMG | $FF | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| dma_register | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| dma_register | COMPAT | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| lcdc | DMG | $91 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| lcdc | CGB | $91 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| lcdc | COMPAT | $91 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| stat | DMG | $00 | POLICY | 2 | diverges-from-pandocs: stored STAT bits are 0 and the mode/LY below make STAT read $86; Pan Docs lists $85 |
| stat | CGB | $00 | POLICY | 8 | no hardware oracle for CGB mode; real hardware varies with the header and held buttons |
| stat | COMPAT | $00 | POLICY | 8 | no hardware oracle for CGB mode; real hardware varies with the header and held buttons |
| ly | DMG | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| ly | CGB | $00 | POLICY | 8 | no hardware oracle for CGB mode; real hardware varies with the header and held buttons |
| ly | COMPAT | $00 | POLICY | 8 | no hardware oracle for CGB mode; real hardware varies with the header and held buttons |
| lyc | DMG | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| lyc | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| lyc | COMPAT | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| scx | DMG | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| scx | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| scx | COMPAT | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| scy | DMG | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| scy | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| scy | COMPAT | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| wx | DMG | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| wx | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| wx | COMPAT | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| wy | DMG | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| wy | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| wy | COMPAT | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| bgp | DMG | $FC | PANDOCS | 1 | Pan Docs Power Up Sequence, DMG |
| bgp | CGB | $FC | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| bgp | COMPAT | $FC | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| obp0 | DMG | $FF | POLICY | 2 | diverges-from-pandocs: OBP0 is $FF here; Pan Docs does not give a fixed value |
| obp0 | CGB | $FF | POLICY | 8 | same value as the DMG cell; Pan Docs gives no CGB-specific value |
| obp0 | COMPAT | $FF | POLICY | 8 | same value as the DMG cell; Pan Docs gives no CGB-specific value |
| obp1 | DMG | $FF | POLICY | 2 | diverges-from-pandocs: OBP1 is $FF here; Pan Docs does not give a fixed value |
| obp1 | CGB | $FF | POLICY | 8 | same value as the DMG cell; Pan Docs gives no CGB-specific value |
| obp1 | COMPAT | $FF | POLICY | 8 | same value as the DMG cell; Pan Docs gives no CGB-specific value |
| ppu_mode | DMG | $02 | POLICY | 2 | diverges-from-pandocs: starts in mode 2 at line 0; Pan Docs STAT $85 implies vblank |
| ppu_mode | CGB | $02 | POLICY | 8 | no hardware oracle for CGB mode; real hardware varies with the header and held buttons |
| ppu_mode | COMPAT | $02 | POLICY | 8 | no hardware oracle for CGB mode; real hardware varies with the header and held buttons |
| joypad_select | DMG | $30 | POLICY | 2 | diverges-from-pandocs: P1 reads $FF here; Pan Docs lists $CF |
| joypad_select | CGB | $30 | ORACLE_SAMEBOY | 7 | SameBoy CGB boot state: P1 reads $FF |
| joypad_select | COMPAT | $30 | HW_TEST | 5 | Mooneye boot_hwio-C, compat mode |
| joypad_buttons | DMG | $00 | POLICY | 2 | no button held at power-on |
| joypad_buttons | CGB | $00 | POLICY | 8 | no button held at power-on |
| joypad_buttons | COMPAT | $00 | POLICY | 8 | no button held at power-on |
| key1 | DMG | $00 | POLICY | 2 | not applicable on the DMG profile: the register is not decoded there (reads stop, writes are ignored) |
| key1 | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| key1 | COMPAT | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| vram_bank | DMG | $00 | POLICY | 2 | the DMG profile pins the VRAM bank at 0 |
| vram_bank | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| vram_bank | COMPAT | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| svbk | DMG | $00 | POLICY | 2 | not applicable on the DMG profile: the register is not decoded there (reads stop, writes are ignored) |
| svbk | CGB | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| svbk | COMPAT | $00 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| wram_bank | DMG | $01 | POLICY | 2 | the DMG profile pins the switchable WRAM bank at 1 |
| wram_bank | CGB | $01 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| wram_bank | COMPAT | $01 | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB in compatibility mode |
| bcps | DMG | $00 | POLICY | 2 | not applicable on the DMG profile: the register is not decoded there (reads stop, writes are ignored) |
| bcps | CGB | $C0 | POLICY | 8 | no hardware oracle for CGB-mode index |
| bcps | COMPAT | $C8 | HW_TEST | 5 | Mooneye boot_hwio-C, compat mode |
| ocps | DMG | $00 | POLICY | 2 | not applicable on the DMG profile: the register is not decoded there (reads stop, writes are ignored) |
| ocps | CGB | $C0 | POLICY | 8 | no hardware oracle for CGB-mode index |
| ocps | COMPAT | $D0 | HW_TEST | 5 | Mooneye boot_hwio-C, compat mode |
| ff72 | DMG | $00 | POLICY | 2 | not applicable on the DMG profile: the register is not decoded there (reads stop, writes are ignored) |
| ff72 | CGB | $00 | POLICY | 8 | initial $00 per D-10; no hardware oracle for this CGB register |
| ff72 | COMPAT | $00 | POLICY | 8 | initial $00 per D-10; no hardware oracle for this CGB register |
| ff73 | DMG | $00 | POLICY | 2 | not applicable on the DMG profile: the register is not decoded there (reads stop, writes are ignored) |
| ff73 | CGB | $00 | POLICY | 8 | initial $00 per D-10; no hardware oracle for this CGB register |
| ff73 | COMPAT | $00 | POLICY | 8 | initial $00 per D-10; no hardware oracle for this CGB register |
| ff74 | DMG | $00 | POLICY | 2 | not applicable on the DMG profile: the register is not decoded there (reads stop, writes are ignored) |
| ff74 | CGB | $00 | POLICY | 8 | initial $00 per D-10; no hardware oracle for this CGB register |
| ff74 | COMPAT | $00 | POLICY | 8 | compat mode does not decode FF74: reads $FF, writes ignored; stored value stays 0 |
| ff75 | DMG | $00 | POLICY | 2 | not applicable on the DMG profile: the register is not decoded there (reads stop, writes are ignored) |
| ff75 | CGB | $00 | POLICY | 8 | bits 4-6 stored; reads $8F with them clear |
| ff75 | COMPAT | $00 | POLICY | 8 | bits 4-6 stored; reads $8F with them clear |
| bg_cram_fill | DMG | $00 | POLICY | 2 | not applicable on the DMG profile: the register is not decoded there (reads stop, writes are ignored) |
| bg_cram_fill | CGB | $7FFF | PANDOCS | 1 | Pan Docs Power Up Sequence, CGB |
| bg_cram_fill | COMPAT | $7FFF | POLICY | 8 | the compat renderer never reads CRAM and the data ports read $FF in compat mode; deterministic fill only |
| obj_cram_fill | DMG | $00 | POLICY | 2 | not applicable on the DMG profile: the register is not decoded there (reads stop, writes are ignored) |
| obj_cram_fill | CGB | $7FFF | POLICY | 8 | Pan Docs calls OBJ CRAM uninitialised; white by policy (D-14) |
| obj_cram_fill | COMPAT | $7FFF | POLICY | 8 | the compat renderer never reads CRAM and the data ports read $FF in compat mode; deterministic fill only |
| opri | DMG | $00 | POLICY | 2 | not applicable on the DMG profile: the register is not decoded there (reads stop, writes are ignored) |
| opri | CGB | $00 | POLICY | 8 | boot ROM leaves priority by OAM index; no hardware oracle (D-08) |
| opri | COMPAT | $00 | POLICY | 8 | compat mode reads OPRI as $FF; stored value inert |
| ram_fill | DMG | $00 | POLICY | 2 | D-025 deterministic fill |
| ram_fill | CGB | $00 | POLICY | 8 | D-025 deterministic fill |
| ram_fill | COMPAT | $00 | POLICY | 8 | D-025 deterministic fill |
<!-- cgb-post-boot-end -->

Palette RAM is filled with white (`$7FFF` words, low byte first) on every reset and ROM load (D-14).
VRAM bank 1 is zero after every reset and ROM load (POLICY, D-40); attribute tests rely on this, and
no uninitialised CRAM or VRAM value is asserted against another emulator.

## Register visibility (FF00-FF7F)

`io_visibility[]` in `src/core/gabbaboy.c` holds one row per address with DMG, CGB and COMPAT
cells. On the CGB profile FF4C-FF7F is decoded from it: KEY0 reads `$FF`; KEY1 reads `$7E` or the
armed bit in CGB mode; VBK reads `$FE` or the bank in both modes and selects VRAM only in CGB mode;
SVBK (CGB mode) reads `$F8` or the raw 3 bits and selects WRAM bank 1-7 (0 selects 1); BCPS and OCPS
store a byte and read it with bit 6 set; BCPD (FF69) and OCPD (FF6B) in CGB mode store a write at
index `BCPS & $3F` (`OCPS & $3F`) and read that byte back, and when the index register's bit 7 is set
every write advances the index (wrapping 63 to 0, bit 7 kept) even when the mode-3 lock blocked the
write; a blocked read returns `$FF` and a read never advances the index; all 8 bits of each byte are
stored. OPRI (FF6C) stores bit 0 and reads `$FE` or that bit; it has no effect on object priority
after boot (the execution mode latch decides that, D-08). In compat mode FF69, FF6B and FF6C read `$FF`
and ignore writes with no index increment. FF72-FF75 are plain registers (FF75 stores bits 4-6 only).
Unused addresses read `$FF` and ignore writes. On the CGB profile, FF51-FF54 program private HDMA
source/destination latches while reads stay `$FF` by POLICY; the source low nibble, destination high
three bits and destination low nibble are masked. FF55 accepts the bounded HBlank request used by
this phase's tracer, reports the active remaining-block field, and reads `$FF` when idle or complete.
An ordinary visible mode-3-to-0 edge latches the request; the current guest instruction retires
before one 16-byte block is admitted, before IRQ dispatch or another opcode. Each byte commits every
four master half-dots, for 64 per block with no modeled startup/teardown. The boundary, cadence and
sampling phase are software policy/unknown for physical CGB-E. Other HDMA start/cancel and lifecycle
cases remain unqualified. FF56, FF76 and FF77 remain deferred: a read stops with
`GBB_STOP_UNSUPPORTED_BUS` before anything changes and a write is dropped and reported as the same
stop once the instruction retires.
The DMG profile never enters this decode: its FF4C-FF7F reads still stop and its writes are silent
no-ops. IE bits 5-7 are stored and read back on the CGB profile only (owner veto item 6).

### Published matrix

The block below is the machine-checked mirror of `io_visibility[]`. `test_cgb_tables io` fails on
any difference in either direction, and a mutated copy of this file is kept as a negative control.
`tests/test_cgb_visibility.c` runs the same cells through the public API from an independent
table written from the D-10 decision, so this block, the code and the behaviour test must all agree.
Addresses handled by the pre-CGB code (FF00-FF02, FF04-FF07, FF0F-FF14, FF16-FF1E, FF20-FF26 and
FF30-FF4B) behave the same on every profile and are not listed. Columns: read and write describe the
cell; `IMPL` means implemented, `DEFERRED(n)` means owned by phase n and failing closed; the last
column is the evidence class (Pan Docs, Mooneye hardware test, SameBoy, or project policy).

<!-- cgb-io-visibility-begin -->
| address | column | read | write | status | src |
|---------|--------|------|-------|--------|-----|
| $FF03 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF03 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF03 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF08 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF08 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF08 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF09 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF09 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF09 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF0A | DMG | stop | ignored | IMPL | HW_TEST |
| $FF0A | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF0A | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF0B | DMG | stop | ignored | IMPL | HW_TEST |
| $FF0B | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF0B | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF0C | DMG | stop | ignored | IMPL | HW_TEST |
| $FF0C | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF0C | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF0D | DMG | stop | ignored | IMPL | HW_TEST |
| $FF0D | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF0D | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF0E | DMG | stop | ignored | IMPL | HW_TEST |
| $FF0E | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF0E | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF15 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF15 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF15 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF1F | DMG | stop | ignored | IMPL | HW_TEST |
| $FF1F | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF1F | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF27 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF27 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF27 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF28 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF28 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF28 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF29 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF29 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF29 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF2A | DMG | stop | ignored | IMPL | HW_TEST |
| $FF2A | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF2A | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF2B | DMG | stop | ignored | IMPL | HW_TEST |
| $FF2B | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF2B | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF2C | DMG | stop | ignored | IMPL | HW_TEST |
| $FF2C | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF2C | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF2D | DMG | stop | ignored | IMPL | HW_TEST |
| $FF2D | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF2D | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF2E | DMG | stop | ignored | IMPL | HW_TEST |
| $FF2E | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF2E | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF2F | DMG | stop | ignored | IMPL | HW_TEST |
| $FF2F | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF2F | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF4C | DMG | stop | ignored | IMPL | PANDOCS |
| $FF4C | CGB | $FF | ignored | IMPL | PANDOCS |
| $FF4C | COMPAT | $FF | ignored | IMPL | PANDOCS |
| $FF4D | DMG | stop | ignored | IMPL | PANDOCS |
| $FF4D | CGB | $7E, bit 7 speed, bit 0 armed | bit 0 arms the switch | IMPL | PANDOCS |
| $FF4D | COMPAT | $FF | ignored | IMPL | PANDOCS |
| $FF4E | DMG | stop | ignored | IMPL | HW_TEST |
| $FF4E | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF4E | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF4F | DMG | stop | ignored | IMPL | PANDOCS |
| $FF4F | CGB | $FE or bank | bit 0 selects the bank | IMPL | PANDOCS |
| $FF4F | COMPAT | $FE or bank | ignored, bank stays 0 | IMPL | PANDOCS |
| $FF50 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF50 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF50 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF51 | DMG | stop | ignored | IMPL | POLICY |
| $FF51 | CGB | stored or $FF | stored and $FF | IMPL | POLICY |
| $FF51 | COMPAT | $FF | ignored | IMPL | POLICY |
| $FF52 | DMG | stop | ignored | IMPL | POLICY |
| $FF52 | CGB | stored or $FF | stored and $F0 | IMPL | POLICY |
| $FF52 | COMPAT | $FF | ignored | IMPL | POLICY |
| $FF53 | DMG | stop | ignored | IMPL | POLICY |
| $FF53 | CGB | stored or $FF | stored and $1F | IMPL | POLICY |
| $FF53 | COMPAT | $FF | ignored | IMPL | POLICY |
| $FF54 | DMG | stop | ignored | IMPL | POLICY |
| $FF54 | CGB | stored or $FF | stored and $F0 | IMPL | POLICY |
| $FF54 | COMPAT | $FF | ignored | IMPL | POLICY |
| $FF55 | DMG | stop | ignored | IMPL | POLICY |
| $FF55 | CGB | stored or $00 | stored and $FF | IMPL | POLICY |
| $FF55 | COMPAT | $FF | ignored | IMPL | POLICY |
| $FF56 | DMG | stop | ignored | IMPL | PANDOCS |
| $FF56 | CGB | stop | dropped, stop after retire | DEFERRED(14) | PANDOCS |
| $FF56 | COMPAT | $FF | ignored | IMPL | PANDOCS |
| $FF57 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF57 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF57 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF58 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF58 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF58 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF59 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF59 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF59 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF5A | DMG | stop | ignored | IMPL | HW_TEST |
| $FF5A | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF5A | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF5B | DMG | stop | ignored | IMPL | HW_TEST |
| $FF5B | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF5B | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF5C | DMG | stop | ignored | IMPL | HW_TEST |
| $FF5C | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF5C | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF5D | DMG | stop | ignored | IMPL | HW_TEST |
| $FF5D | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF5D | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF5E | DMG | stop | ignored | IMPL | HW_TEST |
| $FF5E | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF5E | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF5F | DMG | stop | ignored | IMPL | HW_TEST |
| $FF5F | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF5F | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF60 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF60 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF60 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF61 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF61 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF61 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF62 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF62 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF62 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF63 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF63 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF63 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF64 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF64 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF64 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF65 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF65 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF65 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF66 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF66 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF66 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF67 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF67 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF67 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF68 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF68 | CGB | stored or $40 | stored and $BF | IMPL | HW_TEST |
| $FF68 | COMPAT | stored or $40 | stored and $BF | IMPL | HW_TEST |
| $FF69 | DMG | stop | ignored | IMPL | PANDOCS |
| $FF69 | CGB | palette byte at index, $FF while mode 3 | stores at index, auto-increments even when blocked | IMPL | PANDOCS |
| $FF69 | COMPAT | $FF | ignored | IMPL | PANDOCS |
| $FF6A | DMG | stop | ignored | IMPL | HW_TEST |
| $FF6A | CGB | stored or $40 | stored and $BF | IMPL | HW_TEST |
| $FF6A | COMPAT | stored or $40 | stored and $BF | IMPL | HW_TEST |
| $FF6B | DMG | stop | ignored | IMPL | PANDOCS |
| $FF6B | CGB | palette byte at index, $FF while mode 3 | stores at index, auto-increments even when blocked | IMPL | PANDOCS |
| $FF6B | COMPAT | $FF | ignored | IMPL | PANDOCS |
| $FF6C | DMG | stop | ignored | IMPL | SAMEBOY |
| $FF6C | CGB | $FE or bit 0 | bit 0 stored, no priority effect after boot | IMPL | SAMEBOY |
| $FF6C | COMPAT | $FF | ignored | IMPL | SAMEBOY |
| $FF6D | DMG | stop | ignored | IMPL | HW_TEST |
| $FF6D | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF6D | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF6E | DMG | stop | ignored | IMPL | HW_TEST |
| $FF6E | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF6E | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF6F | DMG | stop | ignored | IMPL | HW_TEST |
| $FF6F | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF6F | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF70 | DMG | stop | ignored | IMPL | PANDOCS |
| $FF70 | CGB | $F8 or raw bank bits | raw 3 bits stored, 0 selects bank 1 | IMPL | PANDOCS |
| $FF70 | COMPAT | $FF | ignored | IMPL | PANDOCS |
| $FF71 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF71 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF71 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF72 | DMG | stop | ignored | IMPL | SAMEBOY |
| $FF72 | CGB | stored or $00 | stored and $FF | IMPL | SAMEBOY |
| $FF72 | COMPAT | stored or $00 | stored and $FF | IMPL | SAMEBOY |
| $FF73 | DMG | stop | ignored | IMPL | SAMEBOY |
| $FF73 | CGB | stored or $00 | stored and $FF | IMPL | SAMEBOY |
| $FF73 | COMPAT | stored or $00 | stored and $FF | IMPL | SAMEBOY |
| $FF74 | DMG | stop | ignored | IMPL | SAMEBOY |
| $FF74 | CGB | stored or $00 | stored and $FF | IMPL | SAMEBOY |
| $FF74 | COMPAT | $FF | ignored | IMPL | SAMEBOY |
| $FF75 | DMG | stop | ignored | IMPL | PANDOCS |
| $FF75 | CGB | stored or $8F | stored and $70 | IMPL | PANDOCS |
| $FF75 | COMPAT | stored or $8F | stored and $70 | IMPL | PANDOCS |
| $FF76 | DMG | stop | ignored | IMPL | PANDOCS |
| $FF76 | CGB | stop | dropped, stop after retire | DEFERRED(14) | PANDOCS |
| $FF76 | COMPAT | stop | dropped, stop after retire | DEFERRED(14) | PANDOCS |
| $FF77 | DMG | stop | ignored | IMPL | PANDOCS |
| $FF77 | CGB | stop | dropped, stop after retire | DEFERRED(14) | PANDOCS |
| $FF77 | COMPAT | stop | dropped, stop after retire | DEFERRED(14) | PANDOCS |
| $FF78 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF78 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF78 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF79 | DMG | stop | ignored | IMPL | HW_TEST |
| $FF79 | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF79 | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF7A | DMG | stop | ignored | IMPL | HW_TEST |
| $FF7A | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF7A | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF7B | DMG | stop | ignored | IMPL | HW_TEST |
| $FF7B | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF7B | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF7C | DMG | stop | ignored | IMPL | HW_TEST |
| $FF7C | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF7C | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF7D | DMG | stop | ignored | IMPL | HW_TEST |
| $FF7D | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF7D | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF7E | DMG | stop | ignored | IMPL | HW_TEST |
| $FF7E | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF7E | COMPAT | $FF | ignored | IMPL | HW_TEST |
| $FF7F | DMG | stop | ignored | IMPL | HW_TEST |
| $FF7F | CGB | $FF | ignored | IMPL | HW_TEST |
| $FF7F | COMPAT | $FF | ignored | IMPL | HW_TEST |
<!-- cgb-io-visibility-end -->

### Deferred accesses stop asymmetrically

A `DEFERRED` read stops before the instruction executes: nothing changes, no time is consumed, and
the stop reports `GBB_STOP_UNSUPPORTED_BUS`. A `DEFERRED` write cannot be refused before it happens,
because the bus write is part of an instruction that has already started; the instruction retires,
the written value is dropped, and the stop is reported afterwards with the register address. The
write stop is also reported after an interrupt-entry push that hits a deferred register. A host that
resumes with another run call continues after the dropped write.

### STOP with KEY1 armed

D-01 gates the speed-switch path on the CGB profile, CGB execution mode and KEY1 bit 0 armed. At
STOP, the implementation evaluates the D-02 decision table before preflighting the bytes that case
actually reads. The table is based on SameBoy `stop()` and triangulated with the named AGE rows;
SameBoy details without an independent hardware pin remain explicitly qualified below.

| Case | Condition when STOP is evaluated | Implemented outcome | Basis and boundary |
| --- | --- | --- | --- |
| 1 | A selected joypad line is low; no enabled interrupt is pending | No switch; KEY1 stays armed and DIV is not reset. STOP reads its operand, advances PC by two, and enters the normal HALT path. | `ORACLE_SAMEBOY`; held-button behavior is `expected-failure:speed-switch-held-button-oracle-only`. |
| 2 | A selected joypad line is low; an enabled interrupt is pending | No switch or stall; STOP is one byte and does not halt. | `ORACLE_SAMEBOY`; one-byte handling is not independently pinned. |
| 3 | No selected joypad line is low; an enabled interrupt is pending | Speed flips, KEY1 bit 0 clears and DIV resets at STOP retire. There is no stall and STOP is one byte, so the next byte executes as an opcode; with IME set, interrupt dispatch proceeds normally. | AGE `caution/spsw-interrupts*` author-attests no pause and the DIV reset; speed-flip and length details are `ORACLE_SAMEBOY` only, named `expected-failure:speed-switch-pending-irq-oracle-only`. |
| 4 | No selected joypad line is low; no enabled interrupt is pending | STOP reads its operand, advances PC by two, flips speed, clears KEY1 bit 0, resets DIV and loads the persisted speed-switch stall. | AGE `spsw-stop-prefetch-cgbBCE` and `spsw-div-cgbBCE` author-attest the fetch and reset; `spsw-tima` contributes stall evidence. |

The switching STOP in cases 3 and 4 costs two CPU M-cycles through
`GBB_STOP_SWITCH_COST_HALF_DOTS` (D-38). DMG, compat, unarmed and held-button STOP keep their
existing cost. Only cases that read an operand preflight it; cases 2 and 3 never read that byte.
The operand value is ignored, so `$00` and `$FF` produce the same STOP result (D-04).

The stall is persisted machine state, consumed by a dedicated branch after the stopped check and
before interrupt dispatch. It advances devices in one CPU M-cycle quantum at a time, obeys the
caller budget and output/headroom checks, and reports `GBB_STOP_BUDGET` when a call ends mid-stall;
it never reports `GBB_STOP_STOPPED` or `GBB_STOP_HALTED_IDLE`, and never sets `stopped`. PPU, APU,
DIV/TIMA, serial and OAM DMA continue advancing while the CPU is stalled. An enabled interrupt
ends the stall at the next M-cycle boundary; IME dispatches the handler, while IME clear resumes
after STOP (D-08/D-34). The IME-on AGE row is author-attested but warns of CGB-E instability; the
other wake details remain `expected-failure:speed-switch-wake-oracle-only`.

On every entry into normal speed, D-09 adds a four-half-dot persisted realignment tail when master
time is four modulo eight. This applies at the normal-speed switch with no long stall, at a stall
completion and at an early wake. The policy is deterministic; odd PPU-mode phase behavior remains
`expected-failure:speed-switch-odd-mode-alignment`. The difference between armed and unarmed held
button handling is recorded as `expected-failure:unarmed-stop-held-button` (D-36). The remaining
DMG, compat and unarmed STOP path reports `GBB_STOP_STOPPED` as before.

### Speed-switch stall length

The stall length is measured in CPU T-cycles at the destination speed. The pre-run derivation used
the distance between DIV reset at STOP retire and CPU resume: SameBoy's `0x20008` minus the 4 T
SameBoy removes at IME=0 gives `0x20004`. That was a working model pending the committed-core AGE
run, not a hardware-datasheet claim.

Measured window. On committed core revision `2e78a48`, the pinned AGE `spsw-div-cgbBCE` software
fixture passes all five rows for the inclusive stall window `[0x20004, 0x20007]` T. The
`age_stall_window` CTest re-measures the four boundary points on every run: `0x20003` fails,
`0x20004` passes, `0x20007` passes, and `0x20008` fails. The committed
`GBB_SPEED_SWITCH_STALL_T` remains `0x20004` T and counts CPU T-cycles at the destination speed;
it is the only M-aligned value inside that window and equals SameBoy's `0x20008` minus the 4 T
adjustment.
The conversion is `T × 1` half-dot per T when switching to double speed and `T × 2` half-dots per
T when switching to normal speed. At `0x20004`, the measured model advances 131076 half-dots to
double and 262152 to normal, or 32769 M-cycles in either direction. A +1 half-dot M28 mutant stays
inside the `spsw-div-cgbBCE` window, so that ROM alone does not distinguish the low bits. The full
D-21 AGE sweep also shows `spsw-mode0-cgbBCE` changes its result under M28; this is recorded as
discriminating evidence, not as a reason to fit the constant. These are software measurements from
the pinned, author-attested AGE corpus; no physical hardware measurement is claimed. The 2050 M /
8200 T (`0x2008`) alternative and the claim that DIV does not tick are
inconsistent with the AGE `spsw-tima` and `spsw-div` observations. SameBoy uses a `0x20008` T
countdown; Gambatte uses `0x20000` T to double and `0x20008` T to normal. Direction-dependent
real-time asymmetry remains `expected-failure:speed-switch-stall-direction-asymmetry`.

### Future save-state fields

The v0.3 state format will need `double_speed`, `cpu_stall_half_dots`, `cpu_stall_kind` and
`key1_armed` so it can resume through a switch or during its stall.

The following behavior remains explicitly unmodelled or outside this profile: PPU output during
the pause (`expected-failure:speed-switch-pause-ppu-output`); odd-mode realignment
(`expected-failure:speed-switch-odd-mode-alignment`); APU length-counter delay after a switch
(`expected-failure:apu-lc-delay-after-switch`, Phase 14); the CGB-E immediate TIMA increment after
DIV reset (`expected-failure:cgb-e-div-reset-immediate-increment-delay`, D-35); DMG double-speed
LCD/CPU alignment (`expected-failure:ds-lcd-cpu-alignment`); CGB mode-3 length
(`expected-failure:cgb-mode3-length`, Phase 14); HBlank DMA crossing a speed-switch stall
armed-across-pause HDMA transfer is not covered by the post-switch register check (Phase 13); and the STOP/OAM bug on a
speed switch (`expected-failure:speed-switch-stop-oam-bug`, Phase 14).

<!-- cgb-speed-dispositions-begin -->
| suite | case | disposition | reason | owner phase | pinned_by |
|-------|------|-------------|--------|-------------|-----------|
| age-test-roms | spsw-div-cgbBCE | pass | - | 12 | age_spsw_div_cgbBCE |
| age-test-roms | spsw-tima-cgbE | expected-failure | expected-failure:cgb-e-div-reset-immediate-increment-delay | 12 | age_spsw_tima_cgbE |
| age-test-roms | spsw-tima-cgbBC | expected-failure | expected-failure:cgb-e-div-reset-immediate-increment-delay | 12 | age_spsw_tima_cgbBC |
| age-test-roms | spsw-stop-prefetch-cgbBCE | pass | - | 12 | age_spsw_stop_prefetch_cgbBCE |
| age-test-roms | spsw-interrupts-cgbE | expected-failure | expected-failure:cgb-e-div-reset-immediate-increment-delay | 12 | age_spsw_interrupts_cgbE |
| age-test-roms | spsw-mode0-cgbBCE | expected-failure | expected-failure:cgb-mode3-length | 14 | age_spsw_mode0_cgbBCE |
| age-test-roms | spsw-ch2-lc-delay-cgbBCE | expected-failure | expected-failure:apu-lc-delay-after-switch | 14 | age_spsw_ch2_lc_delay_cgbBCE |
| age-test-roms | stat-mode-ds-cgbBCE | expected-failure | expected-failure:cgb-mode3-length | 14 | age_stat_mode_ds_cgbBCE |
| age-test-roms | stat-mode-cgbE | expected-failure | expected-failure:cgb-mode3-length | 14 | age_stat_mode_cgbE |
| age-test-roms | stat-mode-sprites-ds-cgbBCE | expected-failure | expected-failure:cgb-mode3-length | 14 | age_stat_mode_sprites_ds_cgbBCE |
| age-test-roms | stat-mode-sprites-dmgC-cgbBCE | expected-failure | expected-failure:cgb-mode3-length | 14 | age_stat_mode_sprites_dmgC_cgbBCE |
| age-test-roms | stat-mode-window-ds-cgbBCE | expected-failure | expected-failure:cgb-mode3-length | 14 | age_stat_mode_window_ds_cgbBCE |
| age-test-roms | stat-mode-window-cgbBCE | expected-failure | expected-failure:cgb-mode3-length | 14 | age_stat_mode_window_cgbBCE |
| age-test-roms | spsw-interrupts-cgbBC | digest-only | not-vendored | 12 | - |
| gabbaboy-model | speed-switch-stall-direction-asymmetry | expected-failure | expected-failure:speed-switch-stall-direction-asymmetry | 12 | cgb_speed_stall_length |
| gabbaboy-model | speed-switch-pause-ppu-output | expected-failure | expected-failure:speed-switch-pause-ppu-output | 12 | cgb_speed_xfail_pause_ppu_output |
| gabbaboy-model | speed-switch-odd-mode-alignment | expected-failure | expected-failure:speed-switch-odd-mode-alignment | 12 | cgb_speed_realign |
| gabbaboy-model | apu-lc-delay-after-switch | expected-failure | expected-failure:apu-lc-delay-after-switch | 14 | age_spsw_ch2_lc_delay_cgbBCE |
| gabbaboy-model | cgb-dma-restart-oracle-only | expected-failure | expected-failure:cgb-dma-restart-oracle-only | 12 | cgb_speed_xfail_dma_restart |
| gabbaboy-model | cgb-e-div-reset-immediate-increment-delay-tima | expected-failure | expected-failure:cgb-e-div-reset-immediate-increment-delay | 12 | age_spsw_tima_cgbE |
| gabbaboy-model | cgb-e-div-reset-immediate-increment-delay-interrupts | expected-failure | expected-failure:cgb-e-div-reset-immediate-increment-delay | 12 | age_spsw_interrupts_cgbE |
| gabbaboy-model | unarmed-stop-held-button | expected-failure | expected-failure:unarmed-stop-held-button | 12 | cgb_speed_dmg_unarmed_unchanged |
| gabbaboy-model | speed-switch-hdma-hblank-across-stall | pass | - | 13 | cgb_speed_xfail_hdma_fails_closed |
| gabbaboy-model | speed-switch-stop-oam-bug | expected-failure | expected-failure:speed-switch-stop-oam-bug | 14 | cgb_speed_xfail_stop_oam_unchanged |
| gabbaboy-model | ds-lcd-cpu-alignment | expected-failure | expected-failure:ds-lcd-cpu-alignment | 14 | age_spsw_mode0_cgbBCE |
| gabbaboy-model | cgb-mode3-length | expected-failure | expected-failure:cgb-mode3-length | 14 | age_stat_mode_cgbE |
| gabbaboy-model | speed-switch-held-button-oracle-only | expected-failure | expected-failure:speed-switch-held-button-oracle-only | 12 | cgb_speed_stop_cases |
| gabbaboy-model | speed-switch-pending-irq-oracle-only | expected-failure | expected-failure:speed-switch-pending-irq-oracle-only | 12 | cgb_speed_stop_cases |
| gabbaboy-model | speed-switch-wake-oracle-only | expected-failure | expected-failure:speed-switch-wake-oracle-only | 12 | cgb_speed_wake_ime_off |
| gabbaboy-model | cgb-separate-buses | expected-failure | expected-failure:cgb-separate-buses | 11 | banking_bus_conflict_cgb_pin |
| samesuite | key1-apu-aggregate | expected-unsupported | pcm-registers-unbuilt | 14 | - |
| gambatte | speedchange | not-admitted | gpl-2.0-cgb-c-results | 12 | - |
| not-applicable | mooneye | not-applicable | no-applicable-cgb-speed-switch-tests | 12 | - |
| not-applicable | blargg | not-applicable | no-applicable-cgb-speed-switch-tests | 12 | - |
| not-applicable | acid2 | not-applicable | no-applicable-cgb-speed-switch-tests | 12 | - |
<!-- cgb-speed-dispositions-end -->

AGE rows cover the 13 admitted ROMs listed in `fixtures/age/manifest.json`; `spsw-interrupts-cgbBC` remains source-digest-only and is not vendored. The Phase 11 dispositions retain `m3-bg-*` as `vendored: false`. The D-21 sweep records that `spsw-div-cgbBCE` is insensitive to M28, while `spsw-mode0-cgbBCE` changes its measured result.

AGE rows cover the 13 admitted ROMs listed in `fixtures/age/manifest.json`; `spsw-interrupts-cgbBC` remains source-digest-only and is not vendored. The Phase 11 dispositions retain `m3-bg-*` as `vendored: false`.

AGE rows cover the 13 admitted ROMs listed in `fixtures/age/manifest.json`; `spsw-interrupts-cgbBC` remains source-digest-only and is not vendored. The Phase 11 dispositions retain `m3-bg-*` as `vendored: false`.

AGE rows cover the 13 admitted ROMs listed in `fixtures/age/manifest.json`; `spsw-interrupts-cgbBC` remains source-digest-only and is not vendored. The Phase 11 dispositions retain `m3-bg-*` as `vendored: false`.

### IE bits 5-7

On the CGB profile (both modes) IE stores and reads back all 8 bits. On the DMG profile IE keeps
`& $1F` and bits 5-7 read as 1. Interrupt dispatch masks with `$1F` on both profiles, so the extra
bits never vector.

### Regions that stay fail-closed

- **FEA0-FEFF stays fail-closed on both profiles this phase.** Prohibited-area behaviour differs by
  revision and is not modelled; an access stops visibly rather than inventing a value.
- **DMG FF4C-FF7F stays fail-closed (D-09).** Hardware reads `$FF` there (Mooneye `unused_hwio-GS`),
  but changing the DMG profile would move the v0.1 byte-identical baseline, so the hardware-correct
  read is deferred to a later DMG-change decision. The `unused_hwio-GS` ROM is not admitted.

## Banked memory and OAM DMA sources

The CGB profile in CGB mode has two VRAM banks (VBK, FF4F) and eight 4 KiB work RAM banks (SVBK,
FF70). C000-CFFF and its echo E000-EFFF are always bank 0; D000-DFFF and its echo F000-FDFF are
the bank SVBK selects, and SVBK 0 selects bank 1. In compatibility mode and on the DMG profile
the banks never move. `banking_*` cases prove this through guest code, with a core mutant for the
echo range (`banking_mutant_echo_ignores_bank`).

### OAM DMA sources

The DMG column is frozen at the v0.1 envelope (DECISIONS D-024) and the CGB column applies to both
CGB modes (D-16). Page numbers are the high byte written to FF46.

| Pages | DMG | CGB | CGB provenance |
|-------|-----|-----|----------------|
| 00-7F | `$FF` | ROM through the mapper (`cart_read`) | PANDOCS, not hardware-verified |
| 80-9F | VRAM | VRAM bank `VBK` | PANDOCS |
| A0-BF | `$FF` | cartridge RAM or RTC through the mapper (`cart_read`; `$FF` when disabled) | PANDOCS, not hardware-verified |
| C0-CF | WRAM | WRAM bank 0 | PANDOCS |
| D0-DF | WRAM | WRAM bank `SVBK` (0 reads as 1) | PANDOCS |
| E0-FF | `$FF` | `$FF` | ORACLE_SAMEBOY, not hardware-verified |

The cartridge and E0-FF cells are documentation or oracle claims. They are not hardware-verified for
CGB-E, and no document, test or release note may describe them as such. `banking_dma_rom_page`,
`banking_dma_cart_ram` and `banking_dma_high_pages` pin the implemented values.

### Limitations

- **expected-failure:cgb-separate-buses (D-17).** Real CGB hardware has separate buses, so the DMG
  rule that a CPU access outside HRAM sees `$FF` (reads) or is dropped (writes) during OAM DMA does
  not hold there. This core keeps the DMG rule on the CGB profile. `banking_bus_conflict_cgb_pin`
  pins the current behaviour so a later change is deliberate. The gate rows are GATE-16 (read) and
  GATE-25 (write) in `docs/model-gates.md`.

## Compatibility palette

In compatibility mode a DMG game's shade indices are resolved per pixel through an instance palette
instead of CRAM: three sets (background, OBJ0, OBJ1) of four RGB555 values. One rule generates the
default: a brightness ramp Y = 31, 21, 11, 1 for shades 0 to 3, with R = Y, G = Y - (Y >> 3) and
B = Y - (Y >> 2), packed `R | G << 5 | B << 10` with bit 15 clear. The same ramp seeds all three
sets. A host can override the palette with `gbb_set_compat_palette`; the override survives reset and
ROM load.

<!-- cgb-compat-palette-begin -->
| set | shade 0 | shade 1 | shade 2 | shade 3 |
| --- | --- | --- | --- | --- |
| BG | $639F | $4275 | $254B | $0421 |
| OBJ0 | $639F | $4275 | $254B | $0421 |
| OBJ1 | $639F | $4275 | $254B | $0421 |
<!-- cgb-compat-palette-end -->

These values were authored for GabbaBoy from the rule above without reference to any boot-ROM,
title-hash, peer-emulator or other third-party palette table (rights gate G4). The look is an owner
veto item (D-18). `cgb_tables_compat_palette` compares this block with the code and with the rule.

## Colour path scope

CGB mode-3 length, WX and window-range timing differences are not claimed (D-09). The one
timing-adjacent difference that is modelled is that CGB mode enables the window by LCDC bit 5 alone;
when LCDC bit 0 is clear that changes the window-start stall, and it is recorded in the GATE-81 row of
`docs/model-gates.md`. The colour path reads PPU dot time only (D-36): it resolves each pixel against
the live palette RAM at the dot it is produced and never consults a wall clock or a host-side frame
boundary. The renderer reads VRAM through an explicit bank argument rather than through the CPU
`VBK` selection, so a CPU bank switch cannot change what the renderer draws. The Phase 13 HDMA
tracer samples VBK at block admission; other HDMA behavior remains outside the colour path. The AGE
test suite has no CGB colour, attribute or priority ROM at its pinned
commit, so it is not Phase 11 colour evidence (D-20); its mode-3 pixel-timing cases are recorded as
`expected-unsupported` in the external-suite section below.

## External CGB PPU suites not run in Phase 11

Phase 11 records, but does not run, two external CGB PPU suites. Neither contributes evidence to
the colour claim, and no file from either is stored in the repository (rights gate G1 is open for
the Mealybug sources; D-09, D-20).

- **AGE `m3-bg-lcdc` and `m3-bg-scx`** at `c-sp/age-test-roms` commit `1f5bc10e` are mode-3
  pixel-timing tests, each in the `cgbBCE`, `ds-cgbBCE` and `nocgb-ncmBCE` variants. This core
  does not model mid-scanline pixel timing yet, so the six cases are `expected-unsupported` with
  reason `mode-3-pixel-timing`, owned by Phase 14. AGE has no CGB colour, attribute or priority ROM
  at this pin, so none of these is Phase 11 evidence (D-20).
- **Mealybug Tearoom Tests `ppu/m3_*`** at `mattcurrie/mealybug-tearoom-tests` commit `70e88fb9`
  are `unsupported-model`: the upstream expected images were captured on CGB-C and CGB-D
  steppings only, and the project profile is CGB-CPU-E, for which upstream has no expectation.

`tests/external/cgb-ppu-dispositions.json` is the record; `cgb_external_dispositions` compares it
with the table below and with the tracked file list, and `cgb_external_dispositions_mutated`
proves that a changed reason is caught.

<!-- cgb-external-dispositions-begin -->
| suite | case | disposition | reason |
| --- | --- | --- | --- |
| age | m3-bg-lcdc-cgbBCE | expected-unsupported | mode-3-pixel-timing |
| age | m3-bg-lcdc-ds-cgbBCE | expected-unsupported | mode-3-pixel-timing |
| age | m3-bg-lcdc-nocgb-ncmBCE | expected-unsupported | mode-3-pixel-timing |
| age | m3-bg-scx-cgbBCE | expected-unsupported | mode-3-pixel-timing |
| age | m3-bg-scx-ds-cgbBCE | expected-unsupported | mode-3-pixel-timing |
| age | m3-bg-scx-nocgb-ncmBCE | expected-unsupported | mode-3-pixel-timing |
| mealybug | m3_bgp_change | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_bgp_change_sprites | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_lcdc_bg_en_change | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_lcdc_bg_en_change2 | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_lcdc_bg_map_change | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_lcdc_bg_map_change2 | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_lcdc_obj_en_change | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_lcdc_obj_en_change_variant | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_lcdc_obj_size_change | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_lcdc_obj_size_change_scx | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_lcdc_tile_sel_change | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_lcdc_tile_sel_change2 | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_lcdc_tile_sel_win_change | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_lcdc_tile_sel_win_change2 | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_lcdc_win_en_change_multiple | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_lcdc_win_en_change_multiple_wx | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_lcdc_win_map_change | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_lcdc_win_map_change2 | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_obp0_change | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_scx_high_5_bits | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_scx_high_5_bits_change2 | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_scx_low_3_bits | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_scy_change | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_scy_change2 | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_window_timing | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_window_timing_wx_0 | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_wx_4_change | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_wx_4_change_sprites | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_wx_5_change | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
| mealybug | m3_wx_6_change | unsupported-model | upstream expected images cover CGB-C/D steppings only; no CGB-E expectation |
<!-- cgb-external-dispositions-end -->

## Optional acid2 local runs

`cgb-acid2` v1.1 and `dmg-acid2` v1.0 (both MIT licensed, by Matt Currie) are not vendored and never
run in required CI: rights gate G1 (the mgblib font in the images) is open (D-24). They can be run
locally against the upstream release files, whose SHA-256 values are pinned in
`tests/acid2/manifest.json` together with the profile and the comparison rule:

```
python3 -I tests/scripts/run-acid2-local.py --rom cgb-acid2.gbc --reference reference.png \
  --runner build/gabbaboy-runner --rom-kind cgb-acid2
```

The script refuses (exit 2, `acid2 refused`) any ROM or reference PNG that is not the pinned file,
runs the ROM on the manifest's model to its `ld b,b` through `gabbaboy-runner --failure-dir`, and
compares the frame pixel by pixel (`acid2 result=match`, or `acid2 result=differs pixels=N` with exit
1). `cgb-acid2` runs on the CGB profile with the `(c << 3) | (c >> 2)` expansion, `dmg-acid2` on
DMG-CPU-B with the greyscale shade map. A local match is a differential check against the upstream
reference image, not hardware evidence. Required CI runs `cgb_acid2_local_selftest` (synthetic PNG,
PPM, one-pixel mismatch and fake ROM) and `cgb_acid2_local_refuses_unpinned` only.

## Half-dot timeline (D-070)

The `uint64_t` half-dot master timeline is the single clock for normal and double speed, and
`GBB_MASTER_HALF_DOTS_PER_SECOND` is 2^23. A CPU T-cycle is `GBB_HALF_DOTS_PER_T_NORMAL` (2) half-dots at normal speed and `GBB_HALF_DOTS_PER_T_DOUBLE` (1) at double speed, and an M-cycle is `GBB_T_PER_M` (4) T-cycles, so 8 or 4 half-dots. A PPU dot is always `GBB_HALF_DOTS_PER_DOT` (2) half-dots, and a frame is `GBB_DOTS_PER_LINE` times `GBB_LINES_PER_FRAME` dots, 140448 half-dots. The APU, HDMA and RTC are constant in master time; the RTC stays at 2^23 half-dots per second and never reads `double_speed`. Only CPU-side devices (timer and DIV, serial, the OAM DMA byte period `GBB_DMA_BYTE_PERIOD_HALF_DOTS`, TIMA reload, instruction cost, bus offsets, and interrupt/HALT literals) scale through `cpu_ticks(t) = t >> double_speed`. PPU dots, APU channel time and RTC stay in master half-dots; the APU frame-sequencer tap is DIV bit 12 at normal speed and bit 13 at double speed, keeping its master-time rate unchanged. Timer and serial countdowns retain their remaining CPU ticks across a switch. STOP resets DIV and divider phase at retire through shared `divider_reset`, before the speed bit flips and before the destination-speed stall is loaded, so the APU edge uses the pre-switch tap. The stall is counted at the destination speed.

Rejected alternatives remain a quarter-dot unit and a speed multiplier on the master clock (V2-03). SameBoy uses the same 8 MHz-unit model (differential oracle, not hardware). The APU tap and DIV reset order follow the implemented CGB switch path; no CGB-E one-M-cycle quirk is claimed as modelled behavior.

## Sources

The numbers are the `src` ids in the table and in `post_boot_source` in the code.

1. Pan Docs, Power Up Sequence (documentation, not hardware evidence).
2. v0.1 DMG-CPU-B policy, DECISIONS D-025 (project choice).
3. Cartridge header byte `$14D` (header-derived).
4. Mooneye `boot_regs-cgb` at 31510e12 (hardware test, compatibility mode CPU registers).
5. Mooneye `boot_hwio-C` at 31510e12 (hardware test, compatibility mode I/O registers).
6. Mooneye `boot_div-cgbABCDE` at 31510e12 (hardware test, applicability CGB A-E).
7. SameBoy `Core/memory.c` at c71f110e (differential oracle, not hardware).
8. CGB-profile policy, phase 10 D-06 and D-07 (project choice).
