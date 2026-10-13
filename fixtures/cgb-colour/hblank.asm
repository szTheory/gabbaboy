; Original GabbaBoy CGB per-line colour guest (MIT; see LICENSE.txt).
; Changes BG palette 0 colour 0 once per scanline so every visible row has its own colour:
;   line 0 is set during VBlank; the HBlank (STAT mode 0) interrupt of line y writes the colour of
;   line (y + 1) mod 144. The screen is one all-index-0 tile, so row y shows ColourTable[y].
; ColourTable[y] = (y * 229 + 1) & $7FFF: distinct and non-zero for y 0..143 (manifest "protocol").
; The main loop is one jump and holds no register, so the handler saves nothing.

INCLUDE "common.inc"

SECTION "StatVector", ROM0[$0048]
    jp StatHandler

    CartridgeEntry

SECTION "Program", ROM0[$0150]
Start:
    di
    ld sp, $FFFE
    WaitVBlank
    ld a, $91                 ; LCD on, BG on, tile data $8000, map $9800; VRAM is all zero
    ldh [rLCDC], a
    ld hl, ColourTable        ; line 0's colour, written while the LCD is in VBlank
    WriteBgColour0
    xor a
    ldh [rIF], a              ; drop any request raised before the source was armed
    ld a, $08                 ; STAT bit 3: mode 0 (HBlank) interrupt
    ldh [rSTAT], a
    ld a, $02                 ; IE bit 1: STAT
    ldh [rIE], a
    ei
.spin:                        ; no HALT: gbb_run returns at every HALT, so one call per frame would advance
    jr .spin                  ; only to the next interrupt and the fixture would not draw a whole frame

StatHandler:                  ; entered in the HBlank of line LY: write line (LY + 1) mod 144
    ldh a, [rLY]
    inc a
    cp 144
    jr nz, .index
    xor a
.index:
    ld l, a
    ld h, 0
    add hl, hl                ; two bytes per entry
    ld de, ColourTable
    add hl, de
    WriteBgColour0
    reti

SECTION "Table", ROM0
ColourTable:
FOR y, 144
    dw (y * 229 + 1) & $7FFF
ENDR
