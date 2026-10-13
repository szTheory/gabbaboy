; Original GabbaBoy CGB palette-RAM port fixture (MIT; see LICENSE.txt). Runs the D-11 cells with
; the BG colour port and reports through WRAM: $C001..$C007 hold one byte per cell ($01 pass, $00
; fail) and $C000 holds the verdict ($A5 all cells passed, $EE otherwise). The guest then spins
; (gbb_run returns at every HALT, so the host reads the markers after a few frames).
;
;   cell 1  64 auto-increment writes, then BCPS reads $C0: the index wrapped 63 -> 0 with bit 7
;           kept and bit 6 reading 1
;   cell 2  all 64 bytes read back through a non-incrementing index
;   cell 3  a data-port read does not advance the index
;   cell 4  a write at index 63 wraps the index to 0 and the next write lands in byte 0
;   cell 5  a write during mode 3 (LCD on) is dropped but still advances the index
;   cell 6  a read during mode 3 returns $FF
;   cell 7  a write with the LCD off succeeds
; Palette data bytes keep bit 7 clear, so the cells do not depend on the top bit of a colour.

INCLUDE "common.inc"

; Z set => the value in A equals \1; otherwise bump the failure counter D.
MACRO Expect
    cp \1
    jr z, .ok\@
    inc d
.ok\@:
ENDM

; Store 1 in $C000 + \1 when D is still zero, else 0.
MACRO CellDone
    ld a, d
    or a
    ld a, 1
    jr z, .pass\@
    xor a
.pass\@:
    ld [$C000 + (\1)], a
ENDM

; Spin until the PPU reports mode 3 (STAT bits 1-0 = 3).
MACRO WaitMode3
.m3\@:
    ldh a, [rSTAT]
    and 3
    cp 3
    jr nz, .m3\@
ENDM

    CartridgeEntry

SECTION "Program", ROM0[$0150]
Start:
    di
    ld sp, $FFFE
    WaitVBlank
    xor a
    ldh [rLCDC], a            ; LCD off: the port is open for cells 1-4 and 7
    ld hl, $C000              ; clear the verdict and the seven cell bytes
    ld b, 8
.clear:
    ld [hl+], a
    dec b
    jr nz, .clear

Cell1:
    ld d, 0
    ld a, $80
    ldh [rBCPS], a
    ld hl, CramData
    ld b, 64
.write:
    ld a, [hl+]
    ldh [rBCPD], a
    dec b
    jr nz, .write
    ldh a, [rBCPS]
    Expect $C0
    CellDone 1

Cell2:
    ld d, 0
    ld hl, CramData
    ld b, 0
.read:
    ld a, b
    ldh [rBCPS], a            ; index b, auto-increment off
    ldh a, [rBCPD]
    ld c, a
    ld a, [hl+]
    cp c
    jr z, .same
    inc d
.same:
    inc b
    ld a, b
    cp 64
    jr nz, .read
    CellDone 2

Cell3:
    ld d, 0
    ld a, $85
    ldh [rBCPS], a
    ldh a, [rBCPD]
    ldh a, [rBCPD]
    ldh a, [rBCPS]
    Expect $C5
    CellDone 3

Cell4:
    ld d, 0
    ld a, $80 | 63
    ldh [rBCPS], a
    ld a, $11
    ldh [rBCPD], a            ; byte 63, index wraps to 0
    ldh a, [rBCPS]
    Expect $C0
    ld a, $22
    ldh [rBCPD], a            ; byte 0
    ld a, 63
    ldh [rBCPS], a
    ldh a, [rBCPD]
    Expect $11
    xor a
    ldh [rBCPS], a
    ldh a, [rBCPD]
    Expect $22
    CellDone 4

Cell5:
    ld d, 0
    ld a, 10
    ldh [rBCPS], a
    ld a, $77
    ldh [rBCPD], a            ; byte 10 = $77 with the LCD off
    ld a, $91
    ldh [rLCDC], a            ; LCD on
    WaitMode3
    ld a, $80 | 10
    ldh [rBCPS], a
    ld a, $55
    ldh [rBCPD], a            ; blocked: byte 10 keeps $77, the index still advances to 11
    xor a
    ldh [rLCDC], a            ; LCD off again so the checks below are not blocked
    ldh a, [rBCPS]
    Expect $C0 | 11
    ld a, 10
    ldh [rBCPS], a
    ldh a, [rBCPD]
    Expect $77
    CellDone 5

Cell6:
    ld d, 0
    ld a, 10
    ldh [rBCPS], a
    ld a, $91
    ldh [rLCDC], a
    WaitMode3
    ldh a, [rBCPD]            ; blocked read
    ld e, a
    xor a
    ldh [rLCDC], a
    ld a, e
    Expect $FF
    ldh a, [rBCPD]            ; the same byte with the LCD off
    Expect $77
    CellDone 6

Cell7:
    ld d, 0
    ld a, $80 | 20
    ldh [rBCPS], a
    ld a, $3C
    ldh [rBCPD], a
    ldh a, [rBCPS]
    Expect $C0 | 21
    ld a, 20
    ldh [rBCPS], a
    ldh a, [rBCPD]
    Expect $3C
    CellDone 7

Verdict:
    ld hl, $C001
    ld b, 7
    ld c, 0
.tally:
    ld a, [hl+]
    cp 1
    jr z, .good
    inc c
.good:
    dec b
    jr nz, .tally
    ld a, c
    or a
    ld a, $A5
    jr z, .store
    ld a, $EE
.store:
    ld [$C000], a
.spin:
    jr .spin

SECTION "Data", ROM0
CramData:
FOR i, 64
    db i + 1
ENDR
