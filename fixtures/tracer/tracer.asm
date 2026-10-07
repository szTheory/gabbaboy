; Original GabbaBoy fixture. It proves only the declared DMG-CPU-B path.
SECTION "Entry", ROM0[$0100]
    jp Start
    ds $0150 - @, $00

SECTION "Program", ROM0[$0150]
Start:
    ld hl, $A000
    ld a, $5A
    ld [hl], a
    ld a, [hl]
    cp $5A
    jr nz, Failure
    inc hl
    ld a, $A5
    ld [hl], a
Success:
    jr Success
Failure:
    inc hl
    ld a, $EE
    ld [hl], a
FailureLoop:
    jr FailureLoop
