; Original GabbaBoy CGB HBlank-DMA guest (MIT; see LICENSE.txt).
; FF55 starts one HBlank block at a time while the LCD is in Mode 2. The first
; source tile is transferred into VRAM bank 0 and the second into bank 1. The
; guest records active/completed FF55 values for both transfers, checks every
; tile byte, then records C000=A5. Any failed predicate records C000=EE and
; leaves the visible background at the distinct white failure colour.
;
; Source-derived pixels: bank-0 tile 0 contains four 4x4 quadrants: red
; RGB555 001F, green RGB555 03E0, blue RGB555 7C00, and white RGB555 7FFF.
; Bank 1 receives a distinct checked tile while the repeated visible map uses
; bank-0 tile 0. The no-transfer twin leaves the reset zero tile as white.

DEF rLCDC EQU $FF40
DEF rSTAT EQU $FF41
DEF rLY   EQU $FF44
DEF rSCY  EQU $FF42
DEF rSCX  EQU $FF43
DEF rBCPS EQU $FF68
DEF rBCPD EQU $FF69
DEF rVBK  EQU $FF4F
DEF rHDMA1 EQU $FF51
DEF rHDMA2 EQU $FF52
DEF rHDMA3 EQU $FF53
DEF rHDMA4 EQU $FF54
DEF rHDMA5 EQU $FF55

SECTION "Entry", ROM0[$0100]
    nop
    jp Start
    ds $0150 - @, $00

SECTION "Program", ROM0[$0150]
Start:
    di
    ld sp, $FFFE
    xor a
    ld [$C000], a
    ld [$C001], a
    ld [$C002], a
    ld [$C003], a
    ld [$C004], a
    ld [$C005], a

.wait_setup_vblank:
    ldh a, [rLY]
    cp 144
    jr c, .wait_setup_vblank

    xor a
    ldh [rSCX], a
    ldh [rSCY], a

    ; BG palette 0: white, red, green, and blue (little-endian RGB555 words).
    ld a, $80
    ldh [rBCPS], a
    ld a, $FF
    ldh [rBCPD], a
    ld a, $7F
    ldh [rBCPD], a
    ld a, $1F
    ldh [rBCPD], a
    xor a
    ldh [rBCPD], a
    ld a, $E0
    ldh [rBCPD], a
    ld a, $03
    ldh [rBCPD], a
    xor a
    ldh [rBCPD], a
    ld a, $7C
    ldh [rBCPD], a
    xor a
    ldh [rBCPD], a
    ldh [rVBK], a

    ; Program FF51-54 before the visible Mode-2 window; source is two aligned
    ; sixteen-byte tiles at $0400 and destination is tile 0 at $8000.
    ld a, $04
    ldh [rHDMA1], a
    xor a
    ldh [rHDMA2], a
    ldh [rHDMA3], a
    ldh [rHDMA4], a
.wait_mode2:
    ldh a, [rLY]
    cp 144
    jr nc, .wait_mode2
    ldh a, [rSTAT]
    and $03
    cp $02
    jr nz, .wait_mode2

    ld a, $80                  ; first HBlank-DMA transaction: one block
    ldh [rHDMA5], a
    ldh a, [rHDMA5]
    ld [$C001], a             ; active: one remaining block (FF55=$00)
    cp $00
    jr z, .active_status_ok
    ld a, $01
    ld [$C005], a
    jp GuestFailure
.active_status_ok:

    ld b, 144
.wait_first_complete:
    ldh a, [rHDMA5]
    cp $FF
    jr z, .first_transfer_done
    dec b
    jr nz, .wait_first_complete
    ld a, $02
    ld [$C005], a
    jp GuestFailure
.first_transfer_done:
    ld [$C002], a             ; first transaction completed
    ld a, $01
    ldh [rVBK], a             ; second HBlank transaction writes VRAM bank 1

    ; Select the next sixteen-byte source tile and start a separate transfer so
    ; FF55 samples the bank-1 destination context for this block.
    ld a, $04
    ldh [rHDMA1], a
    ld a, $10
    ldh [rHDMA2], a
    xor a
    ldh [rHDMA3], a
    ldh [rHDMA4], a
.wait_second_mode2:
    ldh a, [rLY]
    cp 144
    jr nc, .wait_second_mode2
    ldh a, [rSTAT]
    and $03
    cp $02
    jr nz, .wait_second_mode2

    ld a, $80
    ldh [rHDMA5], a
    ldh a, [rHDMA5]
    ld [$C003], a             ; active: one remaining block (FF55=$00)
    cp $00
    jr z, .second_status_ok
    ld a, $03
    ld [$C005], a
    jp GuestFailure
.second_status_ok:

    ld b, 144
.wait_second_complete:
    ldh a, [rHDMA5]
    cp $FF
    jr z, .second_transfer_done
    dec b
    jr nz, .wait_second_complete
    ld a, $03
    ld [$C005], a
    jp GuestFailure
.second_transfer_done:
    ld [$C004], a             ; second transaction completed

    ; Read every transferred byte back through the guest CPU during VBlank.
.wait_vblank_for_checks:
    ldh a, [rLY]
    cp 144
    jr c, .wait_vblank_for_checks
    xor a
    ldh [rVBK], a
    ld hl, $8000
    ld b, 4
.check_bank0_tile:
    ld a, [hli]
    cp $F0
    jr z, .bank0_low_ok
    ld a, $05
    ld [$C005], a
    jp GuestFailure
.bank0_low_ok:
    ld a, [hli]
    cp $0F
    jr z, .bank0_high_ok
    ld a, $05
    ld [$C005], a
    jp GuestFailure
.bank0_high_ok:
    dec b
    jr nz, .check_bank0_tile

    ld b, 4
.check_bank0_lower_tile:
    ld a, [hli]
    cp $F0
    jr z, .bank0_lower_low_ok
    ld a, $05
    ld [$C005], a
    jp GuestFailure
.bank0_lower_low_ok:
    ld a, [hli]
    cp $F0
    jr z, .bank0_lower_high_ok
    ld a, $05
    ld [$C005], a
    jp GuestFailure
.bank0_lower_high_ok:
    dec b
    jr nz, .check_bank0_lower_tile

    ld a, $01
    ldh [rVBK], a
    ld hl, $8000
    ld b, 8
.check_bank1_tile:
    ld a, [hli]
    cp $0F
    jr z, .bank1_low_ok
    ld a, $06
    ld [$C005], a
    jp GuestFailure
.bank1_low_ok:
    ld a, [hli]
    cp $0F
    jr z, .bank1_high_ok
    ld a, $06
    ld [$C005], a
    jp GuestFailure
.bank1_high_ok:
    dec b
    jr nz, .check_bank1_tile

    ld a, $A5
    ld [$C000], a
.pass_spin:
    jr .pass_spin

GuestFailure:
    ld a, $EE
    ld [$C000], a
.fail_spin:
    jr .fail_spin

SECTION "DMA source", ROM0[$0400]
TileBank0:
REPT 4
    db $F0, $0F
ENDR
REPT 4
    db $F0, $F0
ENDR
TileBank1:
REPT 8
    db $0F, $0F
ENDR
