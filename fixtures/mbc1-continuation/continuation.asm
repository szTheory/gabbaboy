; Original GabbaBoy battery continuation fixture.
; A missing save records a three-byte progress tuple in MBC1 battery RAM.
; A later process succeeds only after importing that exact tuple.
SECTION "Entry", ROM0[$0100]
    jp Start
    ds $0150 - @, $00

SECTION "Program", ROM0[$0150]
Start:
    di
    xor a
    ldh [$FF40], a            ; keep the continuation oracle independent of PPU output
    ld a, $0A
    ld [$0000], a             ; enable MBC1 external RAM
    ld a, [$A000]
    cp $47
    jr nz, EmptyOrInvalid
    ld a, [$A001]
    cp $42
    jr nz, InvalidRecord
    ld a, [$A002]
    cp $17
    jr nz, InvalidRecord

ResumeSuccess:
    ld a, $A5
    ld [$C001], a             ; only an imported, intact record reaches this marker
    ld a, $01
    ld [$C004], a
SuccessLoop:
    jr SuccessLoop

EmptyOrInvalid:
    cp $FF
    jr nz, InvalidRecord
    ld a, $47
    ld [$A000], a
    ld a, $42
    ld [$A001], a
    ld a, $17
    ld [$A002], a
    ld a, $01
    ld [$C000], a             ; guest stored progress during this process
    ld a, $E1
    ld [$C002], a             ; fresh/empty-RAM branch marker
EmptyLoop:
    jr EmptyLoop

InvalidRecord:
    ld a, $EE
    ld [$C003], a
InvalidLoop:
    jr InvalidLoop
