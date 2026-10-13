; Shared definitions for the original GabbaBoy CGB colour fixtures (MIT; see LICENSE.txt).
; Every ROM is built from one source that INCLUDEs this file and is assembled, linked and fixed
; with the RGBDS version pinned in manifest.json. The CGB flag ($0143 = $80) comes from
; "rgbfix -c" in the per-ROM recipe, never from the source.

DEF rLCDC EQU $FF40
DEF rSTAT EQU $FF41
DEF rLY   EQU $FF44
DEF rIF   EQU $FF0F
DEF rBCPS EQU $FF68
DEF rBCPD EQU $FF69
DEF rIE   EQU $FFFF

; Cartridge entry: the core starts at $0100, so a jump over the header area to Start.
MACRO CartridgeEntry
SECTION "Entry", ROM0[$0100]
    nop
    jp Start
    ds $0150 - @, $00
ENDM

; Spin until LY >= 144, so the code that follows runs inside VBlank (CRAM and VRAM are open).
MACRO WaitVBlank
.wait\@:
    ldh a, [rLY]
    cp 144
    jr c, .wait\@
ENDM

; BG palette 0, colour 0 := the RGB555 word at [hl] (low byte first). BCPS = $80 selects index 0
; with auto-increment, so the two BCPD writes fill the low then the high byte. Clobbers A, HL.
MACRO WriteBgColour0
    ld a, $80
    ldh [rBCPS], a
    ld a, [hl+]
    ldh [rBCPD], a
    ld a, [hl]
    ldh [rBCPD], a
ENDM
