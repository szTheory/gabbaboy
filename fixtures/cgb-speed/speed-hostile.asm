; Original hostile-entry CGB speed guest. The host patches only ROM byte $0200 in memory.
; Outcome bytes at $C200: marker, selector, KEY1 before/armed/after, handler ran,
; LY before/after STOP, final IF bit 2, reserved byte, post-stall DIV and DMA sentinel.
; $C0FE is the done marker. Selector 0 records no-variant; values above 8 record bad-selector.

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
    cp 2
    jp z, Entry2PendingIme0
    cp 3
    jp z, Entry3IrqInStall
    cp 4
    jp z, Entry4HeldButton
    cp 5
    jp z, Entry5EiStop
    cp 6
    jp z, Entry6LcdOff
    cp 7
    jp z, Entry7DmaActive
    cp 8
    jp z, Entry8BackToBack
    jp BadSelector

NoVariant:
    ld a, $A0
    ld [wHostileMarker], a
    jp Complete

BadSelector:
    ld a, $A9
    ld [wHostileMarker], a
    jp Complete

SECTION "Selector", ROM0[$0200]
    db 0

SECTION "Hostile program", ROM0[$0201]

Entry1PendingIme:
    call PrepareFastPending
    ei
    stop
    nop
    jp RecordAfterStop

Entry2PendingIme0:
    call PrepareFastPending
    ; Keep the pending request but make this entry's IME-off precondition explicit.
    di
    stop
    nop
    jp RecordAfterStop

PrepareFastPending:
    ; Generate one timer request while IME is clear. For selector 1, EI is the next
    ; instruction before STOP, so its delayed enable matures at STOP retirement.
    di
    ld a, $04
    ld [rIE], a
    ; A zero reload value avoids an immediate repeated overflow while IF is pending.
    xor a
    ldh [rTMA], a
    ld a, $FF
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
    ret

Entry3IrqInStall:
    ld a, $04
    ld [rIE], a
    xor a
    ldh [rIF], a
    ldh [rTMA], a
    ldh [rTIMA], a
    ld a, $05
    ldh [rTAC], a
    call RecordBeforeArm
    ei
    stop
    nop
    jp RecordAfterStop

Entry4HeldButton:
    ; The host holds RIGHT through the public input-event API. FF00 selects the
    ; direction row; the enabled slow timer later wakes the HALT selected by STOP.
    ld a, $20
    ldh [rP1], a
    ld a, $04
    ld [rIE], a
    xor a
    ldh [rIF], a
    ldh [rTMA], a
    ldh [rTIMA], a
    call RecordBeforeArm
    ld a, $04
    ldh [rTAC], a
    xor a
    ldh [rIF], a
    ei
    stop
    nop
    jp RecordAfterStop

Entry5EiStop:
    xor a
    ld [rIE], a
    ldh [rIF], a
    call RecordBeforeArm
    ei
    stop
    nop
    jp RecordAfterStop

Entry6LcdOff:
    xor a
    ld [rIE], a
    ldh [rIF], a
    ldh [rLCDC], a
    call RecordBeforeArm
    stop
    nop
    ldh a, [rLY]
    ld [wHostileOutcome + 7], a
    ldh a, [rKEY1]
    ld [wHostileOutcome + 4], a
    ldh a, [rDIV]
    ld [wHostileOutcome + 10], a
    jp RecordFinalIf

Entry7DmaActive:
    xor a
    ld [rIE], a
    ldh [rIF], a
    ld hl, $C000
    ld b, 160
    ld a, $A5
.fill_oam_source:
    ld [hli], a
    dec b
    jr nz, .fill_oam_source
    ld hl, DmaStopRoutine
    ld de, $FF80
    ld bc, DmaStopRoutineEnd - DmaStopRoutine
    CopyBytes
    call RecordBeforeArm
    jp $FF80

DmaAfterResume:
    ldh a, [rLY]
    ld [wHostileOutcome + 7], a
    ldh a, [rKEY1]
    ld [wHostileOutcome + 4], a
    xor a
    ldh [rLCDC], a
    ld a, [$FE9F]
    ld [wHostileOutcome + 11], a
    jp RecordFinalIf

Entry8BackToBack:
    xor a
    ld [rIE], a
    ldh [rIF], a
    call RecordBeforeArm
    ld b, 4
.switch_again:
    ld a, 1
    ldh [rKEY1], a
    stop
    nop
    dec b
    jr nz, .switch_again
    ldh a, [rLY]
    ld [wHostileOutcome + 7], a
    ldh a, [rKEY1]
    ld [wHostileOutcome + 4], a
    jp RecordFinalIf

RecordBeforeArm:
    ldh a, [rKEY1]
    ld [wHostileOutcome + 2], a
    ld a, 1
    ldh [rKEY1], a
    ldh a, [rKEY1]
    ld [wHostileOutcome + 3], a
    ldh a, [rLY]
    ld [wHostileOutcome + 6], a
    ret

RecordAfterStop:
    ldh a, [rLY]
    ld [wHostileOutcome + 7], a
    ldh a, [rKEY1]
    ld [wHostileOutcome + 4], a
    jp RecordFinalIf

RecordFinalIf:
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

Complete:
    ; Once every observable is recorded, disarm pending requests before the stable idle loop.
    xor a
    ld [rIE], a
    ldh [rIF], a
    ld a, 1
    ld [wDone], a
.idle:
    halt
    jr .idle

; The two-byte STOP and the immediate continuation both live in HRAM while OAM DMA owns ROM.
DmaStopRoutine:
    ld a, $C0
    ldh [rDMA], a
    stop
    nop
    jp DmaAfterResume
DmaStopRoutineEnd:

SECTION "Header", ROM0[$0134]
    db "GBB HOSTILE"
    ds 4, 0
    db $C0 ; CGB-only cartridge; no boot ROM is included.
    db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    ds $0150 - @, 0

SECTION "ROM padding", ROMX[$4000], BANK[1]
    ds $8000 - @, 0
