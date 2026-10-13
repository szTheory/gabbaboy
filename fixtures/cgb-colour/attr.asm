; Original GabbaBoy CGB attribute fixture (MIT; see LICENSE.txt).
; One row of ten 16x16-pixel cells (x = 16 * cell, y 0..15); each cell isolates one rule. Every cell
; is 2x2 copies of one 8x8 tile whose four 4x4 quadrants hold known colour indices, so a flip or a
; bank swap changes the quadrant order and the manifest "protocol" lists the expected RGB555 values.
; Build with -D LCDC0_CLEAR for colour-lcdc0.gb: LCDC bit 0 is clear, so BG attribute bit 7 stops
; forcing the BG over objects while the BG itself is still drawn (D-06).
;
;   cell 0  BG palette 3                        cell 5  BG attr bit 7 (priority) under an object
;   cell 1  tile data bank 1                    cell 6  OBJ tile bank 1, OBJ palette 5
;   cell 2  X flip                              cell 7  OBJ palette 2, bank 0
;   cell 3  Y flip                              cell 8  reference: attr 0, palette 0, bank 0
;   cell 4  attr bit 4 set (unused: = cell 8)   cell 9  blank (tile 0)
;
; Quadrant order is top-left, top-right, bottom-left, bottom-right. Tile "Q" (bank 0, tile 1) holds
; indices 1, 2, 3, 0; tile "R" (bank 1, tile 1) holds 3, 0, 1, 2; tile 2 (bank 0) is solid index 1.

INCLUDE "common.inc"

IF DEF(LCDC0_CLEAR)
DEF LCDC_VALUE EQU $92        ; LCD on, OBJ on, BG bit clear
ELSE
DEF LCDC_VALUE EQU $93        ; LCD on, OBJ on, BG on; tile data $8000, map $9800, 8x8 objects
ENDC

    CartridgeEntry

SECTION "Program", ROM0[$0150]
Start:
    di
    ld sp, $FFFE
    WaitVBlank
    xor a
    ldh [rLCDC], a            ; LCD off: VRAM, OAM and CRAM are all open for the set-up below

    ld hl, BgPalettes
    LoadCram rBCPS, 32
    ld hl, ObjPalettes
    LoadCram rOCPS, 48

    ld hl, TilesBank0         ; tile 1 (Q) and tile 2 (solid 1) at $8010
    ld de, $8010
    ld bc, TilesBank0End - TilesBank0
    CopyBytes
    ld a, 1
    ldh [rVBK], a
    ld hl, TilesBank1         ; tile 1 (R) of bank 1
    ld de, $8010
    ld bc, TilesBank1End - TilesBank1
    CopyBytes
    ld hl, AttrRow            ; BG attributes live in bank 1 beside the map, rows 0 and 1
    ld de, $9800
    ld bc, 20
    CopyBytes
    ld hl, AttrRow
    ld de, $9820
    ld bc, 20
    CopyBytes
    xor a
    ldh [rVBK], a
    ld hl, MapRow             ; tile numbers, bank 0
    ld de, $9800
    ld bc, 20
    CopyBytes
    ld hl, MapRow
    ld de, $9820
    ld bc, 20
    CopyBytes

    ld hl, rOAM               ; clear OAM (160 bytes), then the twelve sprites
    ld b, 160
    xor a
.clearOam:
    ld [hl+], a
    dec b
    jr nz, .clearOam
    ld hl, Sprites
    ld de, rOAM
    ld bc, SpritesEnd - Sprites
    CopyBytes

    ld a, LCDC_VALUE
    ldh [rLCDC], a
.spin:                        ; no HALT: gbb_run returns at every HALT
    jr .spin

SECTION "Data", ROM0
; Tile data. Q: rows 0-3 are indices 1|2 (low plane $F0, high plane $0F), rows 4-7 are 3|0.
TilesBank0:
    REPT 4
        db $F0, $0F
    ENDR
    REPT 4
        db $F0, $F0
    ENDR
    REPT 8                    ; tile 2: solid index 1
        db $FF, $00
    ENDR
TilesBank0End:
TilesBank1:                   ; R: rows 0-3 are 3|0, rows 4-7 are 1|2
    REPT 4
        db $F0, $F0
    ENDR
    REPT 4
        db $F0, $0F
    ENDR
TilesBank1End:

; Tile numbers and attributes for the ten cells, two map entries per cell.
MapRow:
    db 1, 1,  1, 1,  1, 1,  1, 1,  1, 1,  2, 2,  0, 0,  0, 0,  1, 1,  0, 0
AttrRow:
    db $03, $03,  $08, $08,  $20, $20,  $40, $40,  $10, $10,  $80, $80,  0, 0,  0, 0,  0, 0,  0, 0

; CRAM colours, each a distinct RGB555 literal (low byte first). Palettes 1 and 2 (BG) and the
; unused OBJ palettes are decoys, so selecting the wrong palette cannot give the right colour.
BgPalettes:
    dw $1111, $2222, $3333, $0444   ; palette 0
    dw $7C00, $7C00, $7C00, $7C00   ; palette 1 (decoy)
    dw $7C00, $7C00, $7C00, $7C00   ; palette 2 (decoy)
    dw $5555, $6666, $7777, $4321   ; palette 3
ObjPalettes:
    dw $0A0A, $1234, $2345, $3456   ; palette 0
    dw $03E0, $03E0, $03E0, $03E0   ; palette 1 (decoy)
    dw $0B0B, $4567, $5678, $6789   ; palette 2
    dw $03E0, $03E0, $03E0, $03E0   ; palette 3 (decoy)
    dw $03E0, $03E0, $03E0, $03E0   ; palette 4 (decoy)
    dw $0C0C, $789A, $0ABC, $1BCD   ; palette 5

; Sprites: OAM y = screen y + 16, x = screen x + 8. Cell 5 (x 80): solid tile 2, OBJ palette 0, OAM
; bit 7 clear. Cell 6 (x 96): tile 1 from bank 1 (attr bit 3), palette 5. Cell 7 (x 112): tile 1,
; bank 0, palette 2.
Sprites:
    db 16,  88, 2, $00
    db 16,  96, 2, $00
    db 24,  88, 2, $00
    db 24,  96, 2, $00
    db 16, 104, 1, $0D
    db 16, 112, 1, $0D
    db 24, 104, 1, $0D
    db 24, 112, 1, $0D
    db 16, 120, 1, $02
    db 16, 128, 1, $02
    db 24, 120, 1, $02
    db 24, 128, 1, $02
SpritesEnd:
