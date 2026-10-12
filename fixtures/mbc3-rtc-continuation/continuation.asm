; Original GabbaBoy MBC3 + timer + battery continuation fixture.
; A store run sets the RTC chosen by the mode byte at SRAM $A010, then writes an
; "RTC" marker at $A000-$A002. A resume run (marker present) latches the clock
; and publishes the registers in WRAM so a later process can compare them.
;
; WRAM results: C000 = $01 store run, $02 resume run; C001..C005 = S M H DL DH;
; C006 = $A5 when the marker was intact.

DEF RTC_S  EQU $08
DEF RTC_M  EQU $09
DEF RTC_H  EQU $0A
DEF RTC_DL EQU $0B
DEF RTC_DH EQU $0C

SECTION "Entry", ROM0[$0100]
    jp Start
    ds $0150 - @, $00

SECTION "Program", ROM0[$0150]
Start:
    di
    xor a
    ldh [$FF40], a            ; keep the oracle independent of PPU output
    ld a, $0A
    ld [$0000], a             ; enable external RAM and RTC registers together
    xor a
    ld [$4000], a             ; RAM bank 0 holds the marker and mode byte
    ld a, [$A000]
    cp $52
    jr nz, Store
    ld a, [$A001]
    cp $54
    jr nz, Store
    ld a, [$A002]
    cp $43
    jr nz, Store

Resume:
    xor a
    ld [$6000], a             ; latch sequence: $00 then $01 copies the live clock
    ld a, $01
    ld [$6000], a
    ld a, RTC_S
    ld [$4000], a
    ld a, [$A000]             ; selected RTC register is read through the RAM window
    ld [$C001], a
    ld a, RTC_M
    ld [$4000], a
    ld a, [$A000]
    ld [$C002], a
    ld a, RTC_H
    ld [$4000], a
    ld a, [$A000]
    ld [$C003], a
    ld a, RTC_DL
    ld [$4000], a
    ld a, [$A000]
    ld [$C004], a
    ld a, RTC_DH
    ld [$4000], a
    ld a, [$A000]
    ld [$C005], a
    xor a
    ld [$4000], a             ; back to RAM bank 0 to re-check the marker
    ld a, [$A000]
    cp $52
    jr nz, ResumeDone
    ld a, [$A001]
    cp $54
    jr nz, ResumeDone
    ld a, [$A002]
    cp $43
    jr nz, ResumeDone
    ld a, $A5
    ld [$C006], a
ResumeDone:
    ld a, $02
    ld [$C000], a
    jr Park

Store:
    ld a, [$A010]             ; mode byte; fresh RAM reads $FF which means normal
    ld b, a
    cp $01
    jr z, ModeHalted
    cp $02
    jr z, ModeRollover

ModeNormal:                   ; 00:00:00 day 0, running
    ld c, $00                 ; S
    ld d, $00                 ; M
    ld e, $00                 ; H
    ld h, $00                 ; DL
    ld l, $00                 ; DH
    jr SetClock

ModeHalted:                   ; 12:34:56 day 0, halt bit set after the fields
    ld c, 56
    ld d, 34
    ld e, 12
    ld h, $00
    ld l, $40
    jr SetClock

ModeRollover:                 ; 23:59:50 day 511, running (DL $FF, day MSB set)
    ld c, 50
    ld d, 59
    ld e, 23
    ld h, $FF
    ld l, $01

SetClock:
    ld a, RTC_S
    ld [$4000], a
    ld a, c
    ld [$A000], a
    ld a, RTC_M
    ld [$4000], a
    ld a, d
    ld [$A000], a
    ld a, RTC_H
    ld [$4000], a
    ld a, e
    ld [$A000], a
    ld a, RTC_DL
    ld [$4000], a
    ld a, h
    ld [$A000], a
    ld a, RTC_DH              ; written last so the halt bit follows the fields
    ld [$4000], a
    ld a, l
    ld [$A000], a
    xor a
    ld [$4000], a             ; RAM bank 0 for the marker; $A010 is left intact
    ld a, $52
    ld [$A000], a
    ld a, $54
    ld [$A001], a
    ld a, $43
    ld [$A002], a
    ld a, $01
    ld [$C000], a

Park:
    di
.loop:
    halt
    nop
    jr .loop
