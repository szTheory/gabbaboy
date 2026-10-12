; Original GabbaBoy MBC5 + RAM + battery continuation fixture (128 KiB RAM).
; A store run writes the marker 'G','B','5',$00 at bank 0 $A000 and
; 'G','B','5',$0F at bank 15 $A000 (the bytes are hex literals because RGBDS
; 1.0.1 warns that string-as-number is obsolete). A resume run verifies both
; markers and publishes C001 = $A5 only when both are intact. Two banks 15
; apart show that the whole 16-bank (128 KiB) battery image is persisted.
;
; WRAM results: C000 = $01 store run, $02 resume run; C001 = $A5 when both
; markers were intact.

SECTION "Entry", ROM0[$0100]
    jp Start
    ds $0150 - @, $00

SECTION "Program", ROM0[$0150]
Start:
    di
    xor a
    ldh [$FF40], a            ; keep the oracle independent of PPU output
    ld a, $0A
    ld [$0000], a             ; enable external RAM
    ; Fresh RAM reads $FF, so a missing or rejected save takes the store branch.
    xor a
    ld [$4000], a             ; RAM bank 0
    ld hl, $A000
    call CheckMarker0
    jr nz, Store
    ld a, $0F
    ld [$4000], a             ; RAM bank 15
    call CheckMarker15
    jr nz, Store

Resume:
    ld a, $A5
    ld [$C001], a             ; reached only when both markers are intact
    ld a, $02
    ld [$C000], a             ; resume branch finished
ResumeHalt:
    di
    halt
    jr ResumeHalt

Store:
    xor a
    ld [$4000], a             ; RAM bank 0
    ld hl, $A000
    ld a, $47                 ; 'G'
    ld [hl+], a
    ld a, $42                 ; 'B'
    ld [hl+], a
    ld a, $35                 ; '5'
    ld [hl+], a
    xor a
    ld [hl], a                ; bank tag $00
    ld a, $0F
    ld [$4000], a             ; RAM bank 15
    ld hl, $A000
    ld a, $47
    ld [hl+], a
    ld a, $42
    ld [hl+], a
    ld a, $35
    ld [hl+], a
    ld a, $0F
    ld [hl], a                ; bank tag $0F
    ld a, $01
    ld [$C000], a             ; store branch finished
StoreHalt:
    di
    halt
    jr StoreHalt

; Z is set when the four bytes at $A000 are 'G','B','5',$00 (bank 0 marker).
CheckMarker0:
    ld b, $00
    jr CheckMarker
; Z is set when the four bytes at $A000 are 'G','B','5',$0F (bank 15 marker).
CheckMarker15:
    ld b, $0F
CheckMarker:
    ld hl, $A000
    ld a, [hl+]
    cp $47
    ret nz
    ld a, [hl+]
    cp $42
    ret nz
    ld a, [hl+]
    cp $35
    ret nz
    ld a, [hl]
    cp b
    ret
