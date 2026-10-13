; Original GabbaBoy LCD-off fixture (MIT; see LICENSE.txt). Shows one solid BG colour for four
; frames, switches the LCD off at the start of VBlank, records $A5 at $C000 and spins. The host
; reads the marker and then checks that the last completed frame is retained and that no new frame
; is produced while the LCD stays off (D-02).

INCLUDE "common.inc"

; Spin until LY is back in the visible lines, so the next WaitVBlank starts a new frame.
MACRO WaitActive
.act\@:
    ldh a, [rLY]
    cp 144
    jr nc, .act\@
ENDM

    CartridgeEntry

SECTION "Program", ROM0[$0150]
Start:
    di
    ld sp, $FFFE
    WaitVBlank
    xor a
    ldh [rLCDC], a            ; LCD off: palette RAM is open
    ld hl, Colour
    WriteBgColour0
    ld a, $91                 ; LCD on, BG on; VRAM is all zero so every pixel is BG colour 0
    ldh [rLCDC], a
    ld b, 4
.frames:
    WaitVBlank
    WaitActive
    dec b
    jr nz, .frames
    WaitVBlank
    xor a
    ldh [rLCDC], a            ; LCD off inside VBlank
    ld a, $A5
    ld [$C000], a
.spin:
    jr .spin

SECTION "Data", ROM0
Colour:
    dw $2A55
