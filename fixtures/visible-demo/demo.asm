; Original GabbaBoy polling demo. The fixture displays one authored tile and
; toggles it after a timestamped A press/release through active-low FF00 reads.
SECTION "Entry", ROM0[$0100]
    jp Start
    ds $0150 - @, $00

SECTION "Program", ROM0[$0150]
Start:
    di
    xor a
    ldh [$FF40], a            ; LCD off while the owned VRAM pattern is initialized
    ld hl, $8000
    ld a, $FF
    ld [hl], a
    inc hl
    xor a
    ld [hl], a
    inc hl
    ld a, $FF
    ld [hl], a
    inc hl
    xor a
    ld [hl], a
    inc hl
    ld a, $FF
    ld [hl], a
    inc hl
    xor a
    ld [hl], a
    inc hl
    ld a, $FF
    ld [hl], a
    inc hl
    xor a
    ld [hl], a
    inc hl
    ld a, $FF
    ld [hl], a
    inc hl
    xor a
    ld [hl], a
    inc hl
    ld a, $FF
    ld [hl], a
    inc hl
    xor a
    ld [hl], a
    inc hl
    ld a, $FF
    ld [hl], a
    inc hl
    xor a
    ld [hl], a
    inc hl
    ld a, $FF
    ld [hl], a
    inc hl
    xor a
    ld [hl], a
    inc hl

    xor a                   ; tile 2 low plane is zero
    ld [hl], a
    inc hl
    ld [hl], a
    inc hl
    ld [hl], a
    inc hl
    ld [hl], a
    inc hl
    ld [hl], a
    inc hl
    ld [hl], a
    inc hl
    ld [hl], a
    inc hl
    ld [hl], a
    inc hl
    ld a, $FF               ; high plane selects color number 2
    ld [hl], a
    inc hl
    ld [hl], a
    inc hl
    ld [hl], a
    inc hl
    ld [hl], a
    inc hl
    ld [hl], a
    inc hl
    ld [hl], a
    inc hl
    ld [hl], a
    inc hl
    ld [hl], a
    inc hl

    ld a, $01
    ld [$9800], a            ; one visible color-1 cell; remaining map is zero fill
    ld a, $E4
    ldh [$FF47], a            ; identity color-number to shade mapping
    ld a, $10
    ldh [$FF00], a            ; select action row, active low
    ld a, $91
    ldh [$FF40], a            ; LCD, BG, unsigned tile data, map $9800

Poll:
    ldh a, [$FF00]
    and $01
    jr z, Pressed
    jr Poll

Pressed:
    ldh a, [$FF44]
    cp $90
    jr c, Pressed            ; wait for VBlank before changing the map
    ld a, $02
    ld [$9800], a
    ld a, $01
    ld [$C000], a

ReleasePoll:
    ldh a, [$FF00]
    and $01
    jr z, ReleasePoll
    ld a, $01
    ld [$C001], a

ReleaseWait:
    ldh a, [$FF44]
    cp $90
    jr c, ReleaseWait
    ld a, $01
    ld [$9800], a
    jr Poll
