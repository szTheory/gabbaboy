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
| bcps | CGB | $C0 | POLICY | 8 | [VERIFY] no hardware oracle for CGB-mode index |
| bcps | COMPAT | $C8 | HW_TEST | 5 | Mooneye boot_hwio-C, compat mode |
| ocps | DMG | $00 | POLICY | 2 | not applicable on the DMG profile: the register is not decoded there (reads stop, writes are ignored) |
| ocps | CGB | $C0 | POLICY | 8 | [VERIFY] no hardware oracle for CGB-mode index |
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
| ram_fill | DMG | $00 | POLICY | 2 | D-025 deterministic fill |
| ram_fill | CGB | $00 | POLICY | 8 | D-025 deterministic fill |
| ram_fill | COMPAT | $00 | POLICY | 8 | D-025 deterministic fill |
<!-- cgb-post-boot-end -->

## Register visibility (FF00-FF7F)

`io_visibility[]` in `src/core/gabbaboy.c` holds one row per address with DMG, CGB and COMPAT
cells. On the CGB profile FF4C-FF7F is decoded from it: KEY0 reads `$FF`; KEY1 reads `$7E` or the
armed bit in CGB mode; VBK reads `$FE` or the bank in both modes and selects VRAM only in CGB mode;
SVBK (CGB mode) reads `$F8` or the raw 3 bits and selects WRAM bank 1-7 (0 selects 1); BCPS and OCPS
store a byte and read it with bit 6 set; FF72-FF75 are plain registers (FF75 stores bits 4-6 only).
Unused addresses read `$FF` and ignore writes. Registers owned by a later phase (FF55 write, FF56,
FF69, FF6B, FF6C, FF76, FF77) are deferred: a read stops with `GBB_STOP_UNSUPPORTED_BUS` before
anything changes and a write is dropped and reported as the same stop once the instruction retires.
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
| $FF4D | CGB | $7E or armed bit | bit 0 arms the switch | IMPL | PANDOCS |
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
| $FF51 | DMG | stop | ignored | IMPL | PANDOCS |
| $FF51 | CGB | $FF | ignored | IMPL | PANDOCS |
| $FF51 | COMPAT | $FF | ignored | IMPL | PANDOCS |
| $FF52 | DMG | stop | ignored | IMPL | PANDOCS |
| $FF52 | CGB | $FF | ignored | IMPL | PANDOCS |
| $FF52 | COMPAT | $FF | ignored | IMPL | PANDOCS |
| $FF53 | DMG | stop | ignored | IMPL | PANDOCS |
| $FF53 | CGB | $FF | ignored | IMPL | PANDOCS |
| $FF53 | COMPAT | $FF | ignored | IMPL | PANDOCS |
| $FF54 | DMG | stop | ignored | IMPL | PANDOCS |
| $FF54 | CGB | $FF | ignored | IMPL | PANDOCS |
| $FF54 | COMPAT | $FF | ignored | IMPL | PANDOCS |
| $FF55 | DMG | stop | ignored | IMPL | PANDOCS |
| $FF55 | CGB | $FF | dropped, stop after retire | DEFERRED(13) | PANDOCS |
| $FF55 | COMPAT | $FF | ignored | IMPL | PANDOCS |
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
| $FF69 | CGB | stop | dropped, stop after retire | DEFERRED(11) | PANDOCS |
| $FF69 | COMPAT | $FF | ignored | IMPL | PANDOCS |
| $FF6A | DMG | stop | ignored | IMPL | HW_TEST |
| $FF6A | CGB | stored or $40 | stored and $BF | IMPL | HW_TEST |
| $FF6A | COMPAT | stored or $40 | stored and $BF | IMPL | HW_TEST |
| $FF6B | DMG | stop | ignored | IMPL | PANDOCS |
| $FF6B | CGB | stop | dropped, stop after retire | DEFERRED(11) | PANDOCS |
| $FF6B | COMPAT | $FF | ignored | IMPL | PANDOCS |
| $FF6C | DMG | stop | ignored | IMPL | PANDOCS |
| $FF6C | CGB | stop | dropped, stop after retire | DEFERRED(11) | PANDOCS |
| $FF6C | COMPAT | $FF | ignored | IMPL | PANDOCS |
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

STOP with KEY1 bit 0 armed: DEFERRED(12). On the CGB profile in CGB mode the speed switch is not
modelled, so the instruction retires and the run reports `GBB_STOP_UNSUPPORTED_BUS` with the KEY1
address ($FF4D); the machine never enters the DMG STOP sleep and no speed change is faked. STOP
without arming, STOP in compatibility mode (which ignores KEY1 writes) and STOP on the DMG profile
use the shared path and report `GBB_STOP_STOPPED`.

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
