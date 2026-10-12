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
