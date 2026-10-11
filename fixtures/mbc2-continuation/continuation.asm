; Original GabbaBoy MBC2 battery continuation fixture.
; MBC2 has 512 built-in cells of 4 bits each. A store run fills every cell
; with the pattern (i * 7 + 3) & $0F. A resume run publishes its success
; marker only if all 512 cells read back with their pattern.
SECTION "Entry", ROM0[$0100]
    jp Start
    ds $0150 - @, $00

SECTION "Program", ROM0[$0150]
Start:
    di
    xor a
    ldh [$FF40], a            ; keep the continuation oracle independent of PPU output
    ld a, $0A
    ld [$0000], a             ; MBC2 decodes RAM enable only when address bit 8 is clear
    ; Only the low nibble of each cell is stored; the upper nibble reads as $F.
    ; Cells 0..2 hold $3, $A, $1, so reading $F3, $FA, $F1 identifies a saved
    ; pattern. Fresh RAM does not read that, so a missing save takes the store branch.
    ld a, [$A000]
    cp $F3
    jr nz, StoreRun
    ld a, [$A001]
    cp $FA
    jr nz, StoreRun
    ld a, [$A002]
    cp $F1
    jr nz, StoreRun

ResumeRun:
    ld hl, $A000
    ld d, $03                 ; pattern for cell 0
ResumeLoop:
    ld a, d
    or $F0                    ; the unconnected upper nibble reads as $F
    cp [hl]
    jr nz, ResumeDone         ; any mismatch leaves the success marker clear
    call NextPattern
    inc hl
    ld a, h
    cp $A2                   ; $A000 + 512 cells = $A200
    jr nz, ResumeLoop
    ld a, $A5
    ld [$C001], a             ; reached only when every cell matches
ResumeDone:
    ld a, $02
    ld [$C000], a             ; resume branch finished
ResumeHalt:
    di
    halt
    jr ResumeHalt

StoreRun:
    ld hl, $A000
    ld d, $03
StoreLoop:
    ld a, d
    ld [hl+], a               ; MBC2 keeps only the low nibble
    call NextPattern
    ld a, h
    cp $A2
    jr nz, StoreLoop
    ld a, $01
    ld [$C000], a             ; store branch finished
StoreHalt:
    di
    halt
    jr StoreHalt

; D = (D + 7) & $0F, so cell i holds (i * 7 + 3) & $0F.
NextPattern:
    ld a, d
    add 7
    and $0F
    ld d, a
    ret
