; Original synthetic Phase 22 control, not an acid2 or game fixture.
; It clears the background tile/map, writes one two-colour 8x8 marker at map cell
; (column 2, row 3), selects the four DMG shades, then waits for VBlank.
start:
    DI
    XOR A
    LDH (0x40), A

    LD HL, 0x8000
    LD B, 0x20
clear_tiles:
    LD (HL+), A
    DEC B
    JR NZ, clear_tiles

    LD HL, 0x9800
    LD C, 0x04
clear_map_outer:
    LD B, 0x00
clear_map_inner:
    LD (HL+), A
    DEC B
    JR NZ, clear_map_inner
    DEC C
    JR NZ, clear_map_outer

    LD A, 0x80
    LD (0x8010), A
    LD A, 0x01
    LD (0x9862), A
    LD A, 0xE4
    LDH (0x47), A
    LD A, 0x91
    LDH (0x40), A

wait_frame:
    LDH A, (0x44)
    CP 0x90
    JR NZ, wait_frame
    LD B, B
