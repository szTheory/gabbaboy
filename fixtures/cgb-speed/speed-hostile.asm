; Original hostile-entry CGB speed guest. The host patches only ROM byte $0200 in memory.
; Outcome bytes at $C200: marker, selector, KEY1 before/armed/after, handler ran,
; LY before/after STOP, then reserved bytes. $C0FE is the done marker.

INCLUDE "common.inc"

DEF rP1             EQU $FF00
DEF rIE             EQU $FFFF
DEF rTMA            EQU $FF06
DEF wHostileMarker  EQU $C1F0
DEF wHostileOutcome EQU $C200
DEF wSelectorByte   EQU $0200

CartridgeEntry

SECTION "Timer vector", ROM0[$0050]
    jp TimerHandler
TimerHandler:
    push af
    xor a
    ldh [rTAC], a
    ldh [rIF], a
    ld a, 1
    ld [wHostileOutcome + 5], a
    pop af
    reti

SECTION "Program", ROM0[$0150]
Start:
    di
    ld sp, $FFFE
    xor a
    ld [wDone], a
    ld [wHostileMarker], a
    ld [rIE], a
    ldh [rIF], a
    ld hl, wHostileOutcome
    ld b, 16
.clear_outcome:
    ld [hli], a
    dec b
    jr nz, .clear_outcome

    ld a, [wSelectorByte]
    ld [wHostileOutcome + 1], a
    cp 0
    jr z, NoVariant
    cp 1
    jp z, Entry1PendingIme
    cp 8
    jr c, NotImplemented
    jr nz, BadSelector
    jp Entry8BackToBack

NoVariant:
    ld a, $A0
    ld [wHostileMarker], a
    jp Complete

BadSelector:
    ld a, $A9
    ld [wHostileMarker], a
    jp Complete

NotImplemented:
    ld a, $E0
    ld [wHostileMarker], a
    jp Complete

Entry1PendingIme:
    ; The enabled timer raises IF while IME is clear. EI immediately precedes STOP, so
    ; its delayed enable matures at STOP retirement; the case-3 switch is immediate and
    ; the handler then runs after the speed change.
    ld a, $04
    ld [rIE], a
    ld a, $FF
    ldh [rTMA], a
    ldh [rTIMA], a
    ld a, $05
    ldh [rTAC], a
.wait_pending:
    ldh a, [rIF]
    bit 2, a
    jr z, .wait_pending
    xor a
    ldh [rTAC], a
    ldh a, [rKEY1]
    ld [wHostileOutcome + 2], a
    ld a, 1
    ldh [rKEY1], a
    ldh a, [rKEY1]
    ld [wHostileOutcome + 3], a
    ldh a, [rLY]
    ld [wHostileOutcome + 6], a
    ei
    stop
    nop
    ldh a, [rLY]
    ld [wHostileOutcome + 7], a
    ldh a, [rKEY1]
    ld [wHostileOutcome + 4], a
    ldh a, [rIF]
    and $04
    jr z, .if_clear
    ld a, 1
    jr .if_saved
.if_clear:
    xor a
.if_saved:
    ld [wHostileOutcome + 8], a
    ld a, 1
    ld [wHostileMarker], a
    jp Complete

Entry8BackToBack:
    ; Added by the second execution task.
    jr NotImplemented

Complete:
    ld a, 1
    ld [wDone], a
.idle:
    halt
    jr .idle

SECTION "Selector", ROM0[$0200]
    db 0

SECTION "Header", ROM0[$0134]
    db "GBB HOSTILE"
    ds 4, 0
    db $C0 ; CGB-only cartridge; no boot ROM is included.
    db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    ds $0150 - @, 0

SECTION "ROM padding", ROMX[$4000], BANK[1]
    ds $8000 - @, 0
