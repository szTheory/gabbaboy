; Original GabbaBoy CGB banking guest (MIT; see LICENSE.txt).
; One source, two builds: rgbfix -c gives $0143 = $80 (banking-cgb.gb), plain rgbfix leaves
; $0143 = $00 (banking-dmg.gb). The guest picks its expectations from its own $0143 byte and from
; the A register at entry ($11 on the CGB profile, $01 on the DMG profile), exercises the bank
; registers through the real CPU and bus, and reports in bank-0 WRAM (see manifest.json "protocol"):
;   C000 = $A5 pass, $EE fail    C001 = run kind: 1 CGB mode, 2 compat, 3 DMG profile
;   C002.. one result byte per cell: $01 pass, $FF fail, $00 not run.
; FF4F and FF70 are touched only when A = $11: on the DMG profile those accesses stop the core
; (they are unsupported there), so a DMG run checks only what memory shows without bank switching.

DEF RESULT_PASS  EQU $A5
DEF RESULT_FAIL  EQU $EE

DEF hEntryA      EQU $FF80   ; A at entry
DEF hCgbRom      EQU $FF81   ; 1 when the header says CGB ($0143 = $80)
DEF hCgbProf     EQU $FF82   ; 1 when the entry A says CGB hardware ($11)

DEF R_KIND       EQU $C001
DEF R_SVBK       EQU $C003

; Mark result byte \1 failed. "ld" leaves flags alone, so a jump may follow.
MACRO FailCell
    ld a, $FF
    ld [\1], a
ENDM

SECTION "Entry", ROM0[$0100]
    nop
    jp Start
    ds $0150 - @, $00

SECTION "Program", ROM0[$0150]
Start:
    di
    ldh [hEntryA], a
    xor a
    ldh [$FF40], a            ; LCD off: the oracle is the WRAM markers, not PPU output
    ld hl, $C000
    ld b, $20
.clear:
    ld [hl+], a
    dec b
    jr nz, .clear
    ld a, [$0143]
    cp $80
    ld a, 0
    jr nz, .romKind
    inc a
.romKind:
    ldh [hCgbRom], a
    ldh a, [hEntryA]
    cp $11
    ld a, 0
    jr nz, .profKind
    inc a
.profKind:
    ldh [hCgbProf], a
    ldh a, [hCgbProf]         ; run kind: 1 CGB mode, 2 compatibility mode, 3 DMG profile
    and a
    ld a, 3
    jr z, .kindSet
    ldh a, [hCgbRom]
    and a
    ld a, 1
    jr nz, .kindSet
    ld a, 2
.kindSet:
    ld [R_KIND], a

; --- C003 cell (b): SVBK 0..7 read back as $F8|raw, and each bank keeps its own D000 marker.
; Bank 0 selects bank 1, so the marker written for 0 is overwritten by the one for 1.
    ldh a, [hCgbRom]
    and a
    jp z, .cellBDone
    ld a, $01
    ld [R_SVBK], a
    ld c, 0
.bWrite:
    ldh a, [hCgbProf]
    and a
    jr z, .bNoSelect          ; DMG profile: FF70 is not reachable, so no bank ever changes
    ld a, c
.svbkWriteMarkers:
    ldh [$FF70], a
.bNoSelect:
    ld a, $B0
    add a, c
    ld [$D000], a
    inc c
    ld a, c
    cp 8
    jr nz, .bWrite
    ld c, 0
.bRead:
    ldh a, [hCgbProf]
    and a
    jr z, .bNoRead
    ld a, c
    ldh [$FF70], a
    ldh a, [$FF70]
    ld b, a
    ld a, c
    or $F8
    cp b
    jr z, .bReadOk
    FailCell R_SVBK
.bReadOk:
.bNoRead:
    ld a, c
    and a
    jr nz, .bExpect
    inc a                     ; bank 0 selects bank 1
.bExpect:
    add a, $B0
    ld b, a
    ld a, [$D000]
    cp b
    jr z, .bMarkOk
    FailCell R_SVBK
.bMarkOk:
    inc c
    ld a, c
    cp 8
    jr nz, .bRead
.cellBDone:

; --- Verdict: pass only if no cell byte is $FF.
    ld d, RESULT_PASS
    ld hl, $C002
    ld b, 14
.scan:
    ld a, [hl+]
    cp $FF
    jr nz, .scanOk
    ld d, RESULT_FAIL
.scanOk:
    dec b
    jr nz, .scan
    ld a, d
    ld [$C000], a
.park:
    halt
    jr .park
