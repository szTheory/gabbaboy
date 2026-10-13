; Original GabbaBoy CGB banking guest (MIT; see LICENSE.txt).
; One source, two builds: rgbfix -c gives $0143 = $80 (banking-cgb.gb), plain rgbfix leaves
; $0143 = $00 (banking-dmg.gb). The guest picks its expectations from its own $0143 byte and from
; the A register at entry ($11 on the CGB profile, $01 on the DMG profile), exercises the bank
; registers through the real CPU and bus, and reports in bank-0 WRAM (see manifest.json "protocol"):
;   C000 = $A5 pass, $EE fail    C001 = run kind: 1 CGB mode, 2 compat, 3 DMG profile
;   C002.. one result byte per cell: $01 pass, $FF fail, $00 not run.
; FF4F and FF70 are touched only when A = $11: on the DMG profile those accesses stop the core
; (they are unsupported there), so a DMG-profile run checks only what memory shows without bank
; switching.
;
; Cells (result bytes C002..C00A):
;   C002 (a) VBK read-back and bank independence at 8000 and 9800      CGB header only
;   C003 (b) SVBK 0..7 read-back ($F8|raw) and a D000 marker per bank   CGB header only
;   C004 (c) F000+n written under bank k is D000+n, per bank            CGB header only
;   C005 (c) E000 mirrors C000 (checked through C100/E100)              every run
;   C006 (d) OAM DMA from D0 under SVBK 2 and 3                         CGB header only
;   C007 (d) OAM DMA from 80 under VBK 0 and 1                          CGB header only
;   C008 (d) OAM DMA from E0 and FE reads $FF                           every run
;   C009 (d) OAM DMA from page 00 matches ROM (CGB) or is $FF (DMG)     every run
;   C00A (e) ignored bank writes and D-10 read values                   DMG header only
; "CGB expectations" apply when the header says CGB or the profile is CGB; only a DMG header on
; the DMG profile expects the frozen DMG behaviour.

DEF RESULT_PASS  EQU $A5
DEF RESULT_FAIL  EQU $EE

DEF hEntryA      EQU $FF80   ; A at entry
DEF hCgbRom      EQU $FF81   ; 1 when the header says CGB ($0143 = $80)
DEF hCgbProf     EQU $FF82   ; 1 when the entry A says CGB hardware ($11)
DEF hCgbExpect   EQU $FF83   ; 1 unless this is a DMG header on the DMG profile
DEF hDma         EQU $FF90   ; OAM DMA trampoline (copied here: only HRAM is reachable during DMA)

DEF R_KIND       EQU $C001
DEF R_VBK        EQU $C002
DEF R_SVBK       EQU $C003
DEF R_ECHOB      EQU $C004
DEF R_MIRROR     EQU $C005
DEF R_DMAW       EQU $C006
DEF R_DMAV       EQU $C007
DEF R_DMAHIGH    EQU $C008
DEF R_DMAROM     EQU $C009
DEF R_FROZEN     EQU $C00A

; Compare A against \1 and mark result byte \2 failed on mismatch. "ld" does not touch flags,
; so the jump consumes the compare.
MACRO CheckEq
    cp \1
    jr z, .ok\@
    ld a, $FF
    ld [\2], a
.ok\@:
ENDM

; Mark result byte \1 failed.
MACRO FailCell
    ld a, $FF
    ld [\1], a
ENDM

MACRO SetVbk
    ld a, \1
    call SelVbk
ENDM

MACRO SetSvbk
    ld a, \1
    call SelSvbk
ENDM

; Bytes at the start of ROM bank 0 for the page-00 DMA cell: non-zero and distinct enough that a
; transfer from the wrong place cannot match them by accident. Nothing executes here.
SECTION "RomPage0", ROM0[$0000]
FOR i, 160
    db LOW($31 + i * 3)
ENDR

SECTION "Entry", ROM0[$0100]
    nop
    jp Start
    ds $0150 - @, $00

SECTION "Program", ROM0[$0150]
Start:
    di
    ldh [hEntryA], a
    xor a
    ldh [$FF40], a            ; LCD off: the oracle is the WRAM markers, not PPU output
    ld hl, $C000
    ld b, $20
.clear:
    ld [hl+], a
    dec b
    jr nz, .clear
    ld a, [$0143]
    cp $80
    ld a, 0
    jr nz, .romKind
    inc a
.romKind:
    ldh [hCgbRom], a
    ldh a, [hEntryA]
    cp $11
    ld a, 0
    jr nz, .profKind
    inc a
.profKind:
    ldh [hCgbProf], a
    ldh a, [hCgbRom]
    ld b, a
    ldh a, [hCgbProf]
    or b
    ldh [hCgbExpect], a
    ldh a, [hCgbProf]         ; run kind: 1 CGB mode, 2 compatibility mode, 3 DMG profile
    and a
    ld a, 3
    jr z, .kindSet
    ldh a, [hCgbRom]
    and a
    ld a, 1
    jr nz, .kindSet
    ld a, 2
.kindSet:
    ld [R_KIND], a
    ld hl, DmaTrampoline      ; install the OAM DMA trampoline in HRAM
    ld de, hDma
    ld b, 8
.copyDma:
    ld a, [hl+]
    ld [de], a
    inc de
    dec b
    jr nz, .copyDma

; --- C002 cell (a): VBK reads back $FE|bank and the two VRAM banks hold their own bytes.
    ldh a, [hCgbRom]
    and a
    jp z, .cellADone
    ld a, $01
    ld [R_VBK], a
    SetVbk 0
    ld a, $10
    ld [$8000], a
    ld a, $12
    ld [$9800], a
    SetVbk 1
    ld a, $21
    ld [$8000], a
    ld a, $22
    ld [$9800], a
    ldh a, [hCgbProf]
    and a
    jr z, .aNoReadBack1
    ldh a, [$FF4F]
    CheckEq $FF, R_VBK
.aNoReadBack1:
    SetVbk 0
    ldh a, [hCgbProf]
    and a
    jr z, .aNoReadBack0
    ldh a, [$FF4F]
    CheckEq $FE, R_VBK
.aNoReadBack0:
    ld a, [$8000]
.expectVbk0:
    CheckEq $10, R_VBK
    ld a, [$9800]
    CheckEq $12, R_VBK
    SetVbk 1
    ld a, [$8000]
    CheckEq $21, R_VBK
    ld a, [$9800]
    CheckEq $22, R_VBK
    SetVbk 0
.cellADone:

; --- C003 cell (b): SVBK 0..7 read back as $F8|raw, and each bank keeps its own D000 marker.
; Bank 0 selects bank 1, so the marker written for 0 is overwritten by the one for 1.
    ldh a, [hCgbRom]
    and a
    jp z, .cellBDone
    ld a, $01
    ld [R_SVBK], a
    ld c, 0
.bWrite:
    ldh a, [hCgbProf]
    and a
    jr z, .bNoSelect          ; DMG profile: FF70 is not reachable, so no bank ever changes
    ld a, c
.svbkWriteMarkers:
    ldh [$FF70], a
.bNoSelect:
    ld a, $B0
    add a, c
    ld [$D000], a
    inc c
    ld a, c
    cp 8
    jr nz, .bWrite
    ld c, 0
.bRead:
    ldh a, [hCgbProf]
    and a
    jr z, .bNoRead
    ld a, c
    ldh [$FF70], a
    ldh a, [$FF70]
    ld b, a
    ld a, c
    or $F8
    cp b
    jr z, .bReadOk
    FailCell R_SVBK
.bReadOk:
.bNoRead:
    ld a, c
    and a
    jr nz, .bExpect
    inc a                     ; bank 0 selects bank 1
.bExpect:
    add a, $B0
    ld b, a
    ld a, [$D000]
    cp b
    jr z, .bMarkOk
    FailCell R_SVBK
.bMarkOk:
    inc c
    ld a, c
    cp 8
    jr nz, .bRead
.cellBDone:

; --- C004 cell (c): a store through F000/FDFF lands at D000/DDFF of the same bank, per bank.
    ldh a, [hCgbRom]
    and a
    jp z, .cellCDone
    ld a, $01
    ld [R_ECHOB], a
    ld c, 1
.cWrite:
    ld a, c
    call SelSvbk
    ld a, $40
    add a, c
    ld b, a
    ld [$F000], a
    ld a, [$D000]
    cp b
    jr z, .cWrite1
    FailCell R_ECHOB
.cWrite1:
    ld a, $60
    add a, c
    ld b, a
    ld [$FDFF], a
    ld a, [$DDFF]
    cp b
    jr z, .cWrite2
    FailCell R_ECHOB
.cWrite2:
    inc c
    ld a, c
    cp 8
    jr nz, .cWrite
    ld c, 1
.cRead:                       ; every bank still holds its own pair, seen through D000 and F000
    ld a, c
    call SelSvbk
    ld a, $40
    add a, c
    ld b, a
    ld a, [$D000]
    cp b
    jr z, .cRead1
    FailCell R_ECHOB
.cRead1:
    ld a, $60
    add a, c
    ld b, a
    ld a, [$FDFF]
    cp b
    jr z, .cRead2
    FailCell R_ECHOB
.cRead2:
    inc c
    ld a, c
    cp 8
    jr nz, .cRead
    SetSvbk 6                 ; and the reverse direction: D123 is seen through F123
    ld a, $5C
    ld [$D123], a
    ld a, [$F123]
    CheckEq $5C, R_ECHOB
    SetSvbk 1
.cellCDone:

; --- C005 cell (c): E000-FDFF mirrors C000 whatever bank D000 shows (run in every mode).
    ld a, $01
    ld [R_MIRROR], a
    SetSvbk 5
    ld a, $3C
    ld [$C100], a
    ld a, [$E100]
    CheckEq $3C, R_MIRROR
    ld a, $C3
    ld [$E101], a
    ld a, [$C101]
    CheckEq $C3, R_MIRROR
    SetSvbk 1

; --- C006 cell (d): OAM DMA from D0 follows SVBK (bank 2 holds $20+i, bank 3 holds $30+i).
    ldh a, [hCgbRom]
    and a
    jp z, .cellDDone
    ld a, $01
    ld [R_DMAW], a
    SetSvbk 2
    ld hl, $D000
    ld a, $20
    call Fill160
    SetSvbk 3
    ld hl, $D000
    ld a, $30
    call Fill160
    SetSvbk 2
    call ClearOam
    ld a, $D0
    call hDma
    ld a, $20
    call CheckOam
    jr z, .dBank2Ok
    FailCell R_DMAW
.dBank2Ok:
    SetSvbk 3
    call ClearOam
    ld a, $D0
    call hDma
    ld a, $30
    call CheckOam
    jr z, .dBank3Ok
    FailCell R_DMAW
.dBank3Ok:
    SetSvbk 1
.cellDDone:

; --- C007 cell (d): OAM DMA from 80 follows VBK (bank 0 holds $10+i, bank 1 holds $80+i).
    ldh a, [hCgbRom]
    and a
    jp z, .cellDvDone
    ld a, $01
    ld [R_DMAV], a
    SetVbk 0
    ld hl, $8000
    ld a, $10
    call Fill160
    SetVbk 1
    ld hl, $8000
    ld a, $80
    call Fill160
    SetVbk 0
    call ClearOam
    ld a, $80
    call hDma
    ld a, $10
    call CheckOam
    jr z, .dVbk0Ok
    FailCell R_DMAV
.dVbk0Ok:
    SetVbk 1
    call ClearOam
    ld a, $80
    call hDma
    ld a, $80
    call CheckOam
    jr z, .dVbk1Ok
    FailCell R_DMAV
.dVbk1Ok:
    SetVbk 0
.cellDvDone:

; --- C008 cell (d): OAM DMA from E0 and FE reads $FF in every mode.
    ld a, $01
    ld [R_DMAHIGH], a
    call ClearOam
    ld a, $E0
    call hDma
    ld a, $FF
    call CheckOamConst
    jr z, .dE0Ok
    FailCell R_DMAHIGH
.dE0Ok:
    call ClearOam
    ld a, $FE
    call hDma
    ld a, $FF
    call CheckOamConst
    jr z, .dFEOk
    FailCell R_DMAHIGH
.dFEOk:

; --- C009 cell (d): OAM DMA from page 00 matches ROM on the CGB profile, $FF on a DMG header/profile.
    ld a, $01
    ld [R_DMAROM], a
    call ClearOam
    ld a, $00
    call hDma
    ldh a, [hCgbExpect]
    and a
    jr z, .dRomFrozen
    call CheckOamRom
    jr z, .dRomDone
    FailCell R_DMAROM
    jr .dRomDone
.dRomFrozen:
    ld a, $FF
    call CheckOamConst
    jr z, .dRomDone
    FailCell R_DMAROM
.dRomDone:

; --- C00A cell (e): compat and DMG runs. Bank writes are ignored (FF4F reads $FE, FF70 reads $FF
; on the CGB profile), so one bank of each kind exists and the later write wins.
    ldh a, [hCgbRom]
    and a
    jp nz, .cellEDone
    ld a, $01
    ld [R_FROZEN], a
    ldh a, [hCgbProf]
    and a
    jr z, .eNoRegisters
    ldh a, [$FF4F]
    CheckEq $FE, R_FROZEN
    ld a, $01
    ldh [$FF4F], a
    ldh a, [$FF4F]
    CheckEq $FE, R_FROZEN
    ldh a, [$FF70]
    CheckEq $FF, R_FROZEN
    ld a, $03
    ldh [$FF70], a
    ldh a, [$FF70]
    CheckEq $FF, R_FROZEN
.eNoRegisters:
    SetVbk 0                  ; two fills "in different banks" land in the one bank
    ld a, $11
    ld [$8000], a
    SetVbk 1
    ld a, $21
    ld [$8000], a
    SetVbk 0
    ld a, [$8000]
    CheckEq $21, R_FROZEN
    SetSvbk 3
    ld a, $5A
    ld [$D000], a
    SetSvbk 5
    ld a, $6B
    ld [$D000], a
    ld a, [$D000]
    CheckEq $6B, R_FROZEN
    ld a, [$F000]             ; the echo shows the same single bank
    CheckEq $6B, R_FROZEN
    SetSvbk 2                 ; DMA sees the one bank too: the later $30 pattern wins
    ld hl, $D000
    ld a, $20
    call Fill160
    SetSvbk 3
    ld hl, $D000
    ld a, $30
    call Fill160
    SetSvbk 2
    call ClearOam
    ld a, $D0
    call hDma
    ld a, $30
    call CheckOam
    jr z, .eWramOk
    FailCell R_FROZEN
.eWramOk:
    SetVbk 0
    ld hl, $8000
    ld a, $10
    call Fill160
    SetVbk 1
    ld hl, $8000
    ld a, $80
    call Fill160
    SetVbk 0
    call ClearOam
    ld a, $80
    call hDma
    ld a, $80
    call CheckOam
    jr z, .eVramOk
    FailCell R_FROZEN
.eVramOk:
.cellEDone:

; --- Verdict: pass only if no cell byte is $FF.
    ld d, RESULT_PASS
    ld hl, $C002
    ld b, 9
.scan:
    ld a, [hl+]
    cp $FF
    jr nz, .scanOk
    ld d, RESULT_FAIL
.scanOk:
    dec b
    jr nz, .scan
    ld a, d
    ld [$C000], a
.park:
    halt
    jr .park

; --- Subroutines. Bank writes happen only on the CGB profile (see the header comment).
SelVbk:                       ; A = bank; clobbers B
    ld b, a
    ldh a, [hCgbProf]
    and a
    ret z
    ld a, b
    ldh [$FF4F], a
    ret

SelSvbk:                      ; A = bank; clobbers B
    ld b, a
    ldh a, [hCgbProf]
    and a
    ret z
    ld a, b
    ldh [$FF70], a
    ret

Fill160:                      ; HL = destination, A = first byte; stores A+i for i in 0..159
    ld b, 160
.loop:
    ld [hl+], a
    inc a
    dec b
    jr nz, .loop
    ret

ClearOam:                     ; so a transfer that did nothing cannot look like a match
    ld hl, $FE00
    ld b, 160
    xor a
.loop:
    ld [hl+], a
    dec b
    jr nz, .loop
    ret

CheckOam:                     ; A = first expected byte; Z set when OAM[i] == A+i for all i
    ld hl, $FE00
    ld c, a
    ld b, 160
.loop:
    ld a, [hl+]
    cp c
    ret nz
    inc c
    dec b
    jr nz, .loop
    ret

CheckOamConst:                ; A = expected byte; Z set when every OAM byte equals it
    ld hl, $FE00
    ld c, a
    ld b, 160
.loop:
    ld a, [hl+]
    cp c
    ret nz
    dec b
    jr nz, .loop
    ret

CheckOamRom:                  ; Z set when OAM[i] == the CPU's own read of ROM address i
    ld hl, $FE00
    ld de, $0000
    ld b, 160
.loop:
    ld a, [de]
    inc de
    cp [hl]
    ret nz
    inc hl
    dec b
    jr nz, .loop
    ret

; Copied to HRAM: LDH [FF46],A; LD A,44; DEC A; JR NZ,-3; RET (waits out the 160 M-cycle transfer).
DmaTrampoline:
    db $E0, $46, $3E, 44, $3D, $20, $FD, $C9
