; Original GabbaBoy CGB speed fixture. Records are phase-major, 32 bytes each, at WRAM $C100.
; Offsets: 0 KEY1 before probes; 1 KEY1 armed; 2 KEY1 after STOP; 3 TIMA delta across one
; scanline; 13 LY immediately before STOP; 15 LY immediately after STOP resumes. The remaining
; fields are reserved here for the same guest's later DIV/serial/APU/DMA probes.
; The phase sequence is normal, double, normal, double. This is a deterministic software probe,
; not physical-hardware evidence.

INCLUDE "common.inc"
CartridgeEntry

SECTION "Program", ROM0[$0150]
Start:
    di
    ld sp, $FFFE
    xor a
    ld [wPhase], a
    ld [wDone], a

    ; Palette RAM is open with the LCD disabled. Tile/map memory starts at zero, so BG colour 0
    ; fills the frame; the end loop changes that colour once per PPU frame for digest sensitivity.
    ldh [rLCDC], a
    ld a, $80
    ldh [rBCPS], a
    xor a
    ldh [rBCPD], a
    ldh [rBCPD], a
    ld a, $91
    ldh [rLCDC], a

    ; A free-running square channel stays audible after the one-shot length-expiry probe.
    ld a, $80
    ldh [rNR52], a
    ld a, $77
    ldh [rNR50], a
    ld a, $11
    ldh [rNR51], a
    ld a, $80
    ldh [rNR11], a
    ld a, $F3
    ldh [rNR12], a
    ld a, $78
    ldh [rNR13], a
    ld a, $85
    ldh [rNR14], a

    ; Distinct copied OAM data lets the later two bus reads distinguish a blocked access from a
    ; read after the final DMA byte has arrived.
    ld hl, $C000
    ld b, 160
    ld a, $A5
.fill_dma_source:
    ld [hl+], a
    dec b
    jr nz, .fill_dma_source

.phase_loop:
    SetSamplePtr
    ldh a, [rKEY1]
    StoreAt 0

    xor a
    ldh [rTIMA], a
    ld a, $05
    ldh [rTAC], a
    WaitNextLine
    ldh a, [rTIMA]
    ld [wScratch], a
    WaitNextLine
    ldh a, [rTIMA]
    ld b, a
    ld a, [wScratch]
    ld c, a
    ld a, b
    sub c
    StoreAt 3

    ld a, [wPhase]
    cp 3
    jr nc, .last_phase

    ; Arm and read KEY1, then capture LY directly before the STOP instruction.
    ld a, 1
    ldh [rKEY1], a
    SetSamplePtr
    inc hl
    ldh a, [rKEY1]
    ld [hl], a
    SetSamplePtr
    ld de, 13
    add hl, de
    ldh a, [rLY]
    ld [hl], a
    stop
    nop
    ldh a, [rLY]
    StoreAt 15
    ldh a, [rKEY1]
    StoreAt 2
    jr .next_phase

.last_phase:
    ldh a, [rKEY1]
    StoreAt 2

.next_phase:
    ld a, [wPhase]
    inc a
    ld [wPhase], a
    cp 4
    jp nz, .phase_loop

    ld a, 1
    ld [wDone], a

    ; Restart channel 1 without the length-enable bit, retaining a steady host PCM stream.
    ld a, $C0
    ldh [rNR11], a
    ld a, $85
    ldh [rNR14], a

.animate:
    WaitVBlank
    ld a, $80
    ldh [rBCPS], a
    inc b
    ld a, b
    cp 32
    jr c, .colour_ready
    ld b, 1
.colour_ready:
    ld a, b
    ldh [rBCPD], a
    xor a
    ldh [rBCPD], a
.wait_frame_end:
    ldh a, [rLY]
    cp 144
    jr nc, .wait_frame_end
    jr .animate

SECTION "Header", ROM0[$0134]
    db "GBB SPEED"
    ds 6, 0
    db $C0 ; CGB-only cartridge; no boot ROM is included.
    db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    ds $0150 - @, 0

SECTION "ROM padding", ROMX[$4000], BANK[1]
    ds $8000 - @, 0
