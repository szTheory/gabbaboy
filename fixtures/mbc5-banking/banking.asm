; Original GabbaBoy MBC5 banking guest.
; It exercises the MBC5 bank registers through the real CPU and bus and reports
; one result byte per sub-check in WRAM (see manifest.json "protocol"):
;   C000 = $A5 pass, C001 = $EE fail,
;   C002 bank 0 in the upper window, C003 bank-write orders,
;   C004 RAM banking (rumble masking on $1E, bank 15 on $1B), C005 bank $1FF.
; Result bytes: $01 pass, $FF fail, $00 not run.

DEF RESULT_PASS  EQU $A5
DEF RESULT_FAIL  EQU $EE
DEF HARNESS_1FF  EQU $5A    ; stamped by the test harness at bank $1FF, offset $1000

; Sticky failure: compare A against \1 and mark result byte \2 failed on mismatch.
; "ld" does not touch flags, so the jump consumes the compare.
MACRO CheckEq
    cp \1
    jr z, .ok\@
    ld a, $FF
    ld [\2], a
.ok\@:
ENDM

SECTION "Entry", ROM0[$0100]
    jp Start
    ds $0150 - @, $00

SECTION "Program", ROM0[$0150]
Start:
    di
    xor a
    ldh [$FF40], a            ; LCD off: the oracle is the WRAM markers, not PPU output
    ld hl, $C000
    ld b, $10
.clear:
    ld [hl+], a
    dec b
    jr nz, .clear

; --- C002: bank 0 is selectable and readable in the $4000-$7FFF window.
; MBC5 does not remap 0 to 1 (unlike MBC1), so $00 must show the bank 0 marker.
    ld a, $01
    ld [$C002], a
    xor a
    ld [$2000], a
    ld a, [$5000]
    CheckEq $B0, $C002

; --- C003: low-byte and high-bit writes compose in either order, and a write to
; one register never disturbs the other. The target is bank $102 (aliases bank 2
; on the 64 KiB image because the bank is masked to the ROM size).
    ld a, $01
    ld [$C003], a
    ld a, $02
    ld [$2000], a             ; low byte first
    ld a, $01
    ld [$3000], a             ; then the ninth bit: must keep low byte 2
    ld a, [$5000]
    CheckEq $02, $C003
    xor a
    ld [$3000], a             ; clear the ninth bit: bank 2 stays selected
    ld a, [$5000]
    CheckEq $02, $C003
    ld a, $01
    ld [$3000], a             ; high bit first
    ld a, $03
    ld [$2000], a             ; then the low byte: must keep the high bit
    ld a, [$5000]
    CheckEq $03, $C003
    xor a
    ld [$3000], a             ; clear again, bank 3 stays selected
    ld a, [$5000]
    CheckEq $03, $C003
    ld a, $01
    ld [$2000], a             ; leave bank 1 selected, ninth bit clear

; --- C004: RAM banking. $0147 chooses the branch: $1E has a rumble line on bit 3
; of the RAM bank register, $1B does not and exposes all 16 banks (128 KiB).
    ld a, $01
    ld [$C004], a
    ld a, [$0147]
    cp $1E
    ld b, 8                   ; $1E: RAM banks 0..7 (bit 3 belongs to the motor)
    jr z, .ramCount
    ld b, 16                  ; $1B: RAM banks 0..15
.ramCount:
    ld a, $0A
    ld [$0000], a             ; enable cartridge RAM
    ld c, 0
.ramWrite:                    ; a distinct byte per RAM bank: $10 + bank
    ld a, c
    ld [$4000], a
    add a, $10
    ld [$A000], a
    inc c
    ld a, c
    cp b
    jr nz, .ramWrite
    ld c, 0
.ramRead:                     ; every bank must still hold its own byte
    ld a, c
    ld [$4000], a
    ld a, [$A000]
    ld d, a
    ld a, c
    add a, $10
    cp d
    jr z, .ramReadOk
    ld a, $FF
    ld [$C004], a
.ramReadOk:
    inc c
    ld a, c
    cp b
    jr nz, .ramRead
    ld a, b
    add a, $0F                ; $10 + (count - 1): the last bank's byte
    ld e, a
    ld a, $0F
    ld [$4000], a             ; $1E: bit 3 masked -> bank 7 (line on); $1B: bank 15
    ld a, [$A000]
    ld d, a
    ld a, e
    cp d
    jr z, .ramMaskOk
    ld a, $FF
    ld [$C004], a
.ramMaskOk:
    ld a, b
    cp 8
    jr nz, .ramDone
    ld a, $08
    ld [$4000], a             ; line stays on, bank 0: the byte must be bank 0's
    ld a, [$A000]
    CheckEq $10, $C004
.ramDone:
    xor a
    ld [$0000], a             ; disable cartridge RAM again

; --- C005: bank $1FF. Only an image whose header declares 8 MiB ($0148 = $08)
; has that bank; the harness stamps $5A there. Otherwise this check is not run.
    ld a, [$0148]
    cp $08
    jr nz, Finish
    ld a, $01
    ld [$C005], a
    ld a, $FF
    ld [$2000], a             ; low byte first
    ld a, $01
    ld [$3000], a             ; then the ninth bit
    ld a, [$5000]
    CheckEq HARNESS_1FF, $C005
    xor a
    ld [$3000], a             ; ninth bit clear: bank $FF, not $1FF
    ld a, [$5000]
    CheckEq $00, $C005
    ld a, $01
    ld [$2000], a             ; park on bank 1
    ld a, $01
    ld [$3000], a             ; high bit first
    ld a, $FF
    ld [$2000], a             ; then the low byte
    ld a, [$5000]
    CheckEq HARNESS_1FF, $C005
    xor a
    ld [$3000], a

; --- Verdict: every executed sub-check must have reported $01.
Finish:
    ld hl, $C002
    ld b, 4
.verdict:
    ld a, [hl+]
    or a
    jr z, .next               ; $00: not run
    cp $01
    jr nz, .fail
.next:
    dec b
    jr nz, .verdict
    ld a, RESULT_PASS
    ld [$C000], a
    jr Halted
.fail:
    ld a, RESULT_FAIL
    ld [$C001], a
Halted:
    halt
    jr Halted

; Bank markers read at offset $1000 of each bank: bank 0 has a distinct stamp
; because MBC5 can map it into the upper window.
SECTION "Marker0", ROM0[$1000]
    db $B0

SECTION "Bank1", ROMX[$5000], BANK[1]
    db $01
SECTION "Bank2", ROMX[$5000], BANK[2]
    db $02
SECTION "Bank3", ROMX[$5000], BANK[3]
    db $03
