; Shared definitions for the original GabbaBoy CGB double-speed fixture (MIT; see LICENSE.txt).
DEF rLCDC EQU $FF40
DEF rLY   EQU $FF44
DEF rDIV  EQU $FF04
DEF rTIMA EQU $FF05
DEF rTAC  EQU $FF07
DEF rKEY1 EQU $FF4D
DEF rIF   EQU $FF0F
DEF rSB   EQU $FF01
DEF rSC   EQU $FF02
DEF rDMA  EQU $FF46
DEF rBCPS EQU $FF68
DEF rBCPD EQU $FF69
DEF rNR10 EQU $FF10
DEF rNR11 EQU $FF11
DEF rNR12 EQU $FF12
DEF rNR13 EQU $FF13
DEF rNR14 EQU $FF14
DEF rNR50 EQU $FF24
DEF rNR51 EQU $FF25
DEF rNR52 EQU $FF26

DEF wPhase    EQU $C0F0
DEF wScratch  EQU $C0F1
DEF wLines    EQU $C0F2
DEF wDone     EQU $C0FE
DEF wSamples  EQU $C100

MACRO CartridgeEntry
SECTION "Entry", ROM0[$0100]
    nop
    jp Start
    ds $0134 - @, $00
ENDM

MACRO SetSamplePtr
    ld a, [wPhase]
    add a
    swap a
    ld l, a
    ld h, $C1
ENDM

MACRO StoreAt
    push af
    SetSamplePtr
    ld de, \1
    add hl, de
    pop af
    ld [hl], a
ENDM

MACRO WaitNextLine
    ldh a, [rLY]
    ld b, a
.wait\@:
    ldh a, [rLY]
    cp b
    jr z, .wait\@
ENDM

MACRO WaitVBlank
.wait\@:
    ldh a, [rLY]
    cp 144
    jr c, .wait\@
ENDM
