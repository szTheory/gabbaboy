; Original GabbaBoy compatibility-mode palette fixture (MIT; see LICENSE.txt). Built without the CGB
; flag ($0143 = $00), so the console runs the cartridge in DMG compatibility mode and BGP, OBP0 and
; OBP1 select shades that the compat palette maps to colours.
;
; BG: four 16-pixel bars at x 0..63 (colour indices 0, 1, 2, 3), the full screen height, BGP = $E4
; (identity). OBJ0: three 8x8 objects at x 80, 88, 96 with indices 1, 2, 3, OBP0 = $E4. OBJ1: three
; objects at x 112, 120, 128 with indices 1, 2, 3, OBP1 = $1B (reversed: index n shows shade 3 - n).
; Everything else is BG index 0.

INCLUDE "common.inc"

    CartridgeEntry

SECTION "Program", ROM0[$0150]
Start:
    di
    ld sp, $FFFE
    WaitVBlank
    xor a
    ldh [rLCDC], a

    ld a, $E4
    ldh [rBGP], a
    ldh [rOBP0], a
    ld a, $1B
    ldh [rOBP1], a

    ld hl, Tiles              ; tiles 1-3: solid indices 1, 2, 3 at $8010
    ld de, $8010
    ld bc, TilesEnd - Tiles
    CopyBytes

    ld de, $9800              ; map rows 0-17: bar columns 0-7 use tiles 0,0,1,1,2,2,3,3
    ld c, 18
.row:
    ld hl, BarRow
    ld b, 8
.col:
    ld a, [hl+]
    ld [de], a
    inc de
    dec b
    jr nz, .col
    ld a, e                   ; skip the 24 map columns after the 8 written
    add 24
    ld e, a
    jr nc, .nocarry
    inc d
.nocarry:
    dec c
    jr nz, .row

    ld hl, rOAM               ; clear OAM, then six sprites
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

    ld a, $93                 ; LCD on, BG on, OBJ on, tile data $8000, map $9800
    ldh [rLCDC], a
.spin:
    jr .spin

SECTION "Data", ROM0
Tiles:
    REPT 8
        db $FF, $00           ; index 1
    ENDR
    REPT 8
        db $00, $FF           ; index 2
    ENDR
    REPT 8
        db $FF, $FF           ; index 3
    ENDR
TilesEnd:
BarRow:
    db 0, 0, 1, 1, 2, 2, 3, 3
; OAM y = screen y + 16, x = screen x + 8. Attr $00 selects OBP0, $10 selects OBP1.
Sprites:
    db 16,  88, 1, $00
    db 16,  96, 2, $00
    db 16, 104, 3, $00
    db 16, 120, 1, $10
    db 16, 128, 2, $10
    db 16, 136, 3, $10
SpritesEnd:
