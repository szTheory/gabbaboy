---
title: GabbaBoy v0.2 pitfalls (Color and Cartridge Breadth)
project: GabbaBoy
milestone: v0.2
researched: 2026-10-10
confidence: MEDIUM
status: research recommendations, not implemented behavior
extends: ../PITFALLS.md (F-01..F-25) and ../../context/LESSONS.md
---

# Domain pitfalls: adding MBC2/MBC3/MBC5, deterministic RTC, and a CGB profile to a shipped DMG-only core

**Domain:** portable C17 Game Boy / Game Boy Color emulator, subsequent milestone. **Researched:** 2026-10-10. **Overall confidence: MEDIUM.**

Confidence key used per item:
- **[PD]** read from Pan Docs (gbdev.io) on 2026-10-10 during this research. Pan Docs is the best public secondary source but carries its own "TO BE VERIFIED" and "research needed" notes. Cite the page and treat as MEDIUM-HIGH, not hardware proof.
- **[KB]** background knowledge of well-known emulator behavior that was NOT re-fetched this session. Treat as MEDIUM/LOW. The prevention step is "confirm against a pinned primary source or hardware-observed test before coding".
- **[LOCAL]** derived from this repository's own lessons (`LESSONS.md`) and v0.1 pitfalls. High confidence for GabbaBoy-specific process risks.

This file does not restate F-01..F-25. Where a v0.2 pitfall is the CGB/mapper instance of an existing one, the F-ID is named and only the new angle is given.

The dominant v0.2 risk pattern: **a DMG-only core has hundreds of implicit "this is the only model" assumptions (STOP, boot state, PPU quirks, APU quirks, `read_supported` address lists, 160x144 shade-only frame format, single WRAM/VRAM bank). Each is a place where DMG behavior leaks into CGB, or where CGB refactoring silently changes the shipped DMG output.** Mapper work is comparatively mechanical but has sharp bit-width and size-heuristic edges.

Phase slots used below are **proposed groupings, not roadmap numbers**: **A** game acceptance on the DMG player; **B** mappers (MBC5, MBC2, MBC3) and RTC; **C** CGB foundation (profile, loader, boot state, KEY0/KEY1, banking, speed switch); **D** CGB video + HDMA (attributes, palettes, priority, compat mode); **E** CGB model-difference qualification (APU/timer/PPU quirks, corpus denominators); **F** support ledger, docs, release.

---

## Critical pitfalls

### V2-01: CGB refactor silently changes shipped DMG output or performance
**What goes wrong:** Introducing VRAM bank 1, WRAM banks 1-7, a color frame format, new IO registers and a model switch touches the bus, PPU and frame API that DMG hashes and baselines depend on. A DMG game or the three admitted Mooneye closures changes behavior or digest without any DMG test noticing, or the memory fast path slows measurably.
**Why it happens:** Shared code paths are generalized "for both models"; DMG goldens only cover what v0.1 happened to sample.
**Consequences:** A v0.2 release that regresses v0.1 claims (F-25 "additive" change altering output semantics), or a changed frame buffer format that breaks the C/C++ install consumers.
**Prevention:**
1. Before any CGB code lands, freeze a DMG regression set: the current 184 CTest inventory, all frame/audio digests, and the game-acceptance run from Phase A. Require byte-identical DMG results under the DMG profile for the whole milestone; any intended change gets a reviewed golden update (F-10, F-16).
2. Keep DMG framebuffer pixels in their existing documented format. Add color as a new explicit output format selected by profile (versioned, documented, ABI-reviewed). Do not reinterpret the existing buffer.
3. Add VRAM/WRAM bank selection as an indirection resolved once per access path and measure it against the v0.1 baseline with the existing benchmark protocol (F-19) before and after.
**Detection:** DMG digest diff in the exact-head gate; installed-consumer smoke on the old DMG API; benchmark delta outside recorded uncertainty.
**Phase:** C (introduce regression freeze first), enforced in D, E, F.
**Confidence:** HIGH (process), grounded in F-16, F-25, GB-VIDEO-001.

### V2-02: DMG-only behavior leaks into the CGB profile (and the reverse)
**What goes wrong:** v0.1 encoded DMG-CPU-B quirks as the only behavior. Under CGB these are wrong or absent. Known candidates, each needing a per-model decision:
- **STOP**: v0.1 implements DMG STOP. On CGB, STOP with KEY1 bit 0 armed performs the speed switch instead of entering low-power (see V2-06). [PD CGB_Registers]
- **Boot register state**: bootless CGB differs from DMG (A=$11, C=$00, E=$08 in DMG-compat, DIV/STAT/LY header-dependent; DMA reads $00 vs $FF; SC $7F vs $7E). [PD Power_Up_Sequence]
- **Hardware-register reset values/readability**: CGB-only registers read $FF in non-CGB mode (see V2-10). [PD Power_Up_Sequence]
- **OAM corruption bug**, **STAT write spurious IRQ**, **first-frame/LCD-on line-0 quirks**, **VRAM/OAM lock windows**, **OAM DMA bus-conflict behavior**: documented DMG/MGB-specific or revision-specific. [KB] If v0.1 implements any, each needs a model predicate and a test run on both profiles that expects the difference.
- **APU quirks** (length counters across power-off, wave RAM access while channel 3 plays, zombie-mode envelope behavior, PCM12/PCM34 readback registers on CGB). [KB]
**Why it happens:** quirks were implemented as unconditional code under the "one named DMG model" strategy (F-01).
**Prevention:** Run a **model-gate audit** as the first CGB task: enumerate every DMG-specific branch/constant in `src/` (grep for STOP, boot init, STAT write, OAM bug, DMA, APU power/off logic), tag each with `DMG_ONLY | CGB_ONLY | BOTH | UNKNOWN`, and put the tag in code comments plus a table in `docs/`. `UNKNOWN` becomes a research task or a documented expected failure, never a silent default. Make the profile a first-class value threaded through the instance (no hidden globals, AGENTS.md rule).
**Detection:** a paired test per quirk that runs the same guest under both profiles and asserts they differ; CGB-profile run of the DMG-only quirk test must fail (negative control per F-10).
**Phase:** C (audit), D/E (resolution).
**Confidence:** MEDIUM (list is partly [KB]); the audit method is the actionable part.

### V2-03: Speed switch implemented as a global clock multiplier
**What goes wrong:** Extends F-04. Concretely: doubling the master timeline also doubles PPU, APU sample generation and HDMA; or timer/DIV, serial, OAM DMA fail to follow the CPU.
**Facts:** In double speed the CPU, timer/divider, serial and OAM DMA run at 2x; LCD controller, HDMA-to-VRAM timing and sound timing do not. [PD CGB_Registers] The APU frame sequencer is clocked from a DIV bit that moves up one position in double speed so audio stays at normal rate. [KB; Pan Docs Audio_details, confirm]
**Why it happens:** v0.1's rational audio sample accounting and PPU dot counting are probably expressed in CPU cycles.
**Prevention:**
1. Decide the **timeline base unit before coding**: it must express a double-speed T-cycle exactly and survive a mid-frame speed change without rounding (verify whether v0.1's half-dot unit already does; if a T-cycle equals one timeline tick, change that first and rerun the full DMG suite per V2-01).
2. Express each device's advance as `elapsed_ticks * device_ratio`, with the ratio owned by the speed state, and keep remainders per device across the switch (same discipline as F-14 sample remainder).
3. Audio: sample count per emulated second must be identical in normal and double speed; assert PCM frame count over a fixed number of video frames in both modes.
**Detection:** a guest that counts VBlanks while running a CPU-cycle loop sees ~2x CPU cycles per frame in double speed and the same frame rate; DIV increments 2x per frame; PCM samples per frame unchanged; speed switch mid-scanline does not shift PPU phase.
**Phase:** C (design), E (qualification).
**Confidence:** MEDIUM-HIGH.

### V2-04: STOP-based switch handled as an instantaneous flag flip
**What goes wrong:** Setting KEY1 bit 7 immediately, ignoring the pause, DIV freeze, PPU/APU side effects, interrupt/joypad conditions, or mis-handling STOP when KEY1 bit 0 is clear on CGB.
**Facts:** KEY1 bit 0 arms; STOP then switches and clears bit 0; the CPU pauses ~2050 M-cycles (8200 T-cycles); DIV does not tick during the pause so some audio events are missed; video memory locking freezes (modes 0/1 produce black pixels, mode 2 renders BG without sprites, mode 3 unaffected); whether interrupts can occur during the pause is marked TODO upstream. [PD CGB_Registers]
**Prevention:** Model the pause as an explicit state with a recorded end deadline, not a cycle jump; keep PPU and APU advancing in their own domains during it; record in the evidence doc every behavior Pan Docs marks unknown and choose a documented conservative model (D-025 pattern: confidence-qualified software model, uncertainty stated). Keep the CGB STOP path separate from the existing DMG STOP path rather than adding a branch inside it. Test games' usual pre-switch sequence (IE=0, JOYP=$30, KEY1=1, STOP) per Pan Docs, plus a hostile sequence (IE nonzero, pending interrupt, button held).
**Detection:** switch round-trip count, elapsed emulated time equals pause + normal execution, partition-equivalence (split run) across the pause (XFER-004), speed bit stable across HALT and reset.
**Phase:** C. Needs deeper research (mandatory per F-04) on pause-time interrupt behavior; SameSuite/Mooneye CGB speed-switch tests are the hardware-observed oracle candidates.
**Confidence:** MEDIUM (primary facts [PD], interrupt behavior unknown).

### V2-05: HDMA/GDMA modeled as an instant copy
**What goes wrong:** Extends F-02. GDMA copies all blocks at once with no CPU stall; HBlank DMA copies in the wrong mode, fires at LY>=144, runs during LCD-off incorrectly, or does not stall the CPU per block.
**Facts [PD CGB_Registers]:** $10-byte blocks; length = (FF55 low 7 bits + 1) * $10; GDMA halts the program until complete and copies even during VRAM access; HBlank DMA copies one block per HBlank at LY 0-143 and not in VBlank; a block takes ~8 us regardless of CPU speed (so in double speed it stalls the CPU for twice as many M-cycles); HALT pauses the transfer; writing bit 7 = 0 to FF55 during an HBlank transfer cancels it, FF55 bit 7 then reads 1, and HDMA1-4 are not reset; FF55 reads $FF after GDMA; destination overflow stops early with register state "still under investigation"; do not start an HBlank transfer while already in mode 0.
**Why it happens:** HDMA looks like OAM DMA, which v0.1 already has, so its machinery is copied; but HDMA stalls the CPU and is gated by PPU mode, not CPU-bus contention.
**Prevention:** Implement HDMA as a separate stall state owned by the machine scheduler with explicit source/dest cursor registers (FF51-54 as live counters, readable back per hardware tests, not as stale write-latches [KB]); define: block start condition (mode-0 entry edge, not level), VRAM bank used for the destination at each block (FF4F changes mid-transfer are a documented hazard), source address masks and invalid-source behavior [KB], what timers/PPU/APU do during the stall (they advance; only the CPU is stalled [KB]), interaction with HALT, LCD off/on mid-transfer, and with speed switch. Bound work: a malicious FF55 length can't exceed 128 blocks (2 KiB), so per-write work is already bounded; keep the scheduler step bounded too.
**Detection:** SameSuite `dma/` hardware-observed cases (gdma/hdma start-at-mode-0, lcd-off, cancel, address wrap) as a pinned, license-reviewed corpus (see V2-17); guest ROM that cancels at each block; HALT during HBlank transfer; FF55 readback sequence assertions; split-run equivalence.
**Phase:** D (after palettes/banking exist so VRAM bank semantics are real). Mandatory deeper research.
**Confidence:** MEDIUM ([PD] facts, with explicit upstream unknowns).

### V2-06: Cart-header-driven mode selection done by value equality
**What goes wrong:** Loader treats only $80/$C0 at $143 as CGB, or treats a nonzero byte as CGB, or refuses a CGB-only image on the DMG profile, or auto-picks the profile instead of taking it from the caller.
**Facts:** $80 = CGB-enhanced and backward compatible; $C0 = CGB-only, bit 6 ignored by hardware; hardware acts on bit 7 and the boot ROM writes the value to KEY0. [PD The_Cartridge_Header, Power_Up_Sequence] Old DMG titles used all 16 title bytes, so $143 can hold arbitrary title characters. [KB]
**Prevention:** The public API keeps hardware profile an explicit caller choice (F-01). Provide a documented, tested header-to-mode function equivalent to boot-ROM behavior for CGB profile (bit 7 test, value to KEY0), including what is done for out-of-spec values (document as unsupported with bounded rejection rather than guessing PGB bits). Running a CGB-only image under the DMG profile follows hardware (software decides; no refusal in the core), with a clear diagnostic, per GB-CORE-001 "advertised capability must be reachable".
**Detection:** loader matrix test over every `$143` value class with expected mode; DMG-title with high-bit-in-title control.
**Phase:** C.
**Confidence:** MEDIUM.

### V2-07: Bootless CGB state invented, or a Nintendo boot-ROM derivative embedded
**What goes wrong:** v0.1 is bootless DMG-CPU-B. A CGB profile still needs the post-boot state: registers (A=$11 etc.), KEY0 value, OPRI, compat palettes, palette RAM contents, WRAM/VRAM/OAM init, DIV phase. Tempting shortcuts: paste values from another emulator's source (license and ancestry issue, F-10), or copy the boot ROM's title-hash palette lookup table (a derivative of Nintendo's boot ROM data; AGENTS.md forbids boot ROMs).
**Facts:** for non-CGB cartridges the boot ROM writes $04 to KEY0 (DMG compat mode), $01 to OPRI (DMG object priority), selects compatibility palettes from a header-derived ID, and on color models the hand-off writes $11 to FF50; background colors are initialized to white and OBJ colors are left uninitialized except OBJ0 color 0 low byte $00 [PD Power_Up_Sequence, Palettes]. Several of those registers depend on the header, DIV/STAT/LY included.
**Prevention:** Document the post-boot state as a single versioned table with a source per field (Pan Docs section, hardware test, or "project choice"). For DMG-only software on the CGB profile, ship an **original** compat palette policy (e.g., the DMG four-shade ramp; no title-hash table) and declare it as a limitation: games will look different from a real CGB's colorization. Choose a deterministic fill for fields the hardware leaves random (and record that games using uninitialized memory as RNG seed may differ, V2-24). Never assert uninitialized OBJ CRAM against another emulator's value.
**Detection:** init table test with per-field provenance; repo scan to ensure no boot ROM bytes or lookup tables copied.
**Phase:** C.
**Confidence:** MEDIUM-HIGH.

### V2-08: Mapper implemented by extending the MBC1 code path
**What goes wrong:** MBC5 and MBC3 get MBC1 quirks (bank 0 to 1 remap, mode register, 5-bit masks) or MBC1 gets disturbed when the common bank logic is generalized. MBC1's 1 MiB+ multicart (MBC1M) heuristics are accidentally applied.
**Prevention:** One small, separately tested mapper per family (`rom_only`, `mbc1`, `mbc2`, `mbc3`, `mbc5`) behind a minimal table or switch; share only the bounded-allocation/bank-mask helpers. Before touching shared code, snapshot MBC1 test and fresh-process continuation evidence (v0.1 MBC1 continuation fixture) and require them unchanged. Resist a generic mapper framework (AGENTS.md: small direct code).
**Detection:** MBC1 suite + continuation fixture byte-identical after each mapper lands; cross-mapper negative controls (the same write sequence yields different banks per type).
**Phase:** B.
**Confidence:** HIGH (process).

---

## Moderate pitfalls (mapper)

### V2-09: MBC5 ROM bank number handling
**What goes wrong:** (1) Writing 0 remaps to bank 1 (MBC1/2/3 habit); on MBC5, writing 0 selects bank 0. (2) The 9th bit lives at $3000-$3FFF and the low 8 at $2000-$2FFF; implementing one 9-bit write that clears the low byte on a high write, or accepting $2000-$3FFF as one range. (3) A $3000 write with value bits above bit 0 changes bank. (4) Bank mask not tied to loaded ROM size, so banks beyond the image return host memory or garbage. [PD MBC5]
**Prevention:** two registers, `bank = (hi & 1) << 8 | lo`; mask by the power-of-two ceiling of loaded image banks (document out-of-range choice; ROM image is bounded by header and file length, GB-CORE-001). Address $0000-$3FFF is always bank 0 fixed; only $4000-$7FFF follows the register.
**Detection:** tests with a ROM whose every 16 KiB bank starts with its own bank number: bank 0 at $4000 equals the fixed bank; low-byte-then-high-bit and high-bit-then-low-byte orders; bank $1FF on an 8 MiB image; one-over-bank reads.
**Phase:** B.
**Confidence:** HIGH [PD].

### V2-10: MBC5 RAM bank and rumble
**What goes wrong:** RAM bank masks to 3 bits even without rumble, or keeps 4 bits on rumble carts so bit 3 (the motor) selects a RAM bank. Persisted save then contains wrong banks. [PD MBC5]
**Prevention:** decide by cartridge type: rumble types $1C-$1E mask RAM bank to 3 bits, ignore motor output (no host rumble in v0.2, state it); non-rumble use 4 bits (0-F) clipped to header RAM size. RAM-enable value policy: Pan Docs says real hardware decodes low nibble $A but advises not to rely on it; pick one behavior, verify with Mooneye/other hardware-observed mapper tests at a pinned revision, and test both $0A and (e.g.) $1A.
**Phase:** B.
**Confidence:** MEDIUM-HIGH.

### V2-11: MBC2 decoding by address bit 8 and 4-bit RAM
**What goes wrong:**
- The MBC2 uses a single register window $0000-$3FFF: **address bit 8 clear = RAM enable** (value low nibble must be $A), **bit 8 set = ROM bank** (low 4 bits; 0 gives 1). Implementations that follow the MBC1 split ($0000-$1FFF enable, $2000-$3FFF bank) miss writes to $2000 with bit 8 clear (those are RAM enable, not a bank change) and mis-select banks.
- RAM is 512 x 4 bits at $A000-$A1FF and **echoes** through $A200-$BFFF using the low 9 address bits. Upper nibble is undefined on read per Pan Docs; many programs and emulators expect a fixed `1111` pattern and read-modify-write the nibble. [PD MBC2; upper-nibble convention [KB]]
- Header says RAM size = 0 for MBC2 even with a battery, so a loader rule "no RAM code means no RAM" (or one that allocates by RAM code) breaks it. [PD Cartridge_Header]
- Battery file size is 512 bytes (not zero, not 8 KiB), and exporting upper nibbles verbatim creates save files that differ by emulator.
**Prevention:** Decode on bit 8 explicitly with a table-driven test over every address bit combination; set RAM size from mapper type, not from `$149`; mask reads by an explicit documented policy (recommend returning `0xF0 | nibble`, noted as a modeled convention and tested against a hardware-observed mapper test if available) and **mask on write and export** so battery bytes are canonical; round-trip in a fresh process (XFER-002), plus a wrong-save control; ROM limit is 16 banks (256 KiB) because the bank register is 4 bits, so reject larger declared MBC2 images (GB-CORE-001).
**Detection:** write $00 to $2000 must not change bank; write $00 to $2100 must select bank 1; read at $A200 equals $A000; imported 512-byte save with garbage upper nibbles round-trips to canonical export.
**Phase:** B.
**Confidence:** HIGH for bit-8 decode and 512x4 [PD]; MEDIUM for upper-nibble policy.

### V2-12: Header size heuristics and header lies
**What goes wrong:** Extends F-07/GB-CORE-001. New mapper codes add more ways for header, file length and mapper type to disagree: ROM size code vs file length (padding or truncation), type code vs actual mapper behavior, type `$0F`/`$11` (no RAM) with `$149` nonzero, `$149` = `$01` (believed to be a toolchain mistake) or unofficial ROM size `$52`-`$54`, `$08`/`$09` ROM+RAM types with unknown behavior, MBC1M multicarts, MBC3 variants with larger RAM/ROM (MBC30), and MBC5 up to 8 MiB. [PD Cartridge_Header; MBC30 [KB]]
**Prevention:** Keep v0.1's rule: a successful load means every advertised byte is reachable. For each newly supported type, add a per-type admission table (allowed ROM codes, RAM codes, battery/timer/rumble flags). Reject unsupported combinations with a specific bounded error and no partial mutation; do not "repair" or autodetect a different mapper from content. Require file length to equal the header-implied size exactly (or document accepted padding) and cover exact, one-under and one-over cases. Treat header checksum policy explicitly (bootless: warn vs reject) and test it.
**Detection:** loader matrix test (type x ROM code x RAM code x file length); the next-unsupported code must reject without mutating an existing instance.
**Phase:** B (and C for the CGB flag, V2-06).
**Confidence:** HIGH.

### V2-13: MBC3 RTC latch, halt, day-carry semantics
**What goes wrong:** Conflating live vs latched registers; latching on any write of 1; ignoring the 0-then-1 edge; reading latched values that tick; clearing the day-carry flag automatically; not stopping the clock when the halt bit is set; losing the high day bit; letting S/M/H take out-of-range values.
**Facts [PD MBC3]:** $08 S 0-59, $09 M 0-59, $0A H 0-23, $0B day low 8, $0C bit 0 = day bit 8 (9-bit 0-511), bit 6 = halt (set before writing the registers), bit 7 = day carry (sticky until the program clears it); latch is a write of $00 then $01 to $6000-$7FFF; RTC and RAM share the $0A enable; RAM bank select $00-$07 vs RTC select $08-$0C at $4000-$5FFF; ROM bank register is 7 bits and 0 maps to 1.
**Prevention:** Model RTC as `{live fields + sub-second counter, latched fields, latch-edge state, halt, carry}` with clear invariants. Define: what a read returns before the first latch; whether RAM-disable ($00) affects latch state; what happens when software writes a field while running (writes affect the live clock; recommend requiring halt for deterministic tests) and the sub-second reset on seconds writes [KB]; unused bits' read value (decide and test, e.g. mask S/M to 6 bits, H to 5, DH to bits 0/6/7); carry sets on 511 to 0 and never auto-clears. Provide a boot value (all zeros, halt clear) in the support ledger.
**Detection:** table-driven latch sequences (0,1 latches; 1,1 does not; 0,0,1 latches; 1,0,1 latches), tick across minute/hour/day/511-wrap boundaries using the injected clock, halt/resume, field write while halted, carry persistence across save/reload.
**Phase:** B. Needs deeper research on write-while-running and subsecond behavior; pin a hardware-observed source before claiming.
**Confidence:** MEDIUM-HIGH for [PD] facts; MEDIUM for the undefined cells.

### V2-14: Nondeterministic RTC (host clock inside the core)
**What goes wrong:** Extends F-09 into concrete traps for this repo: `time()` or `clock_gettime()` in `src/core`; the SDL player passing wall-clock deltas per frame (frame pacing jitter becomes RTC jitter); headless tests that pass or fail depending on when they run; fast-forward/pause/step changing game-visible time; clock rollback, DST/timezone, 2038 `time_t`, or a huge offline gap producing day-counter overflow on load.
**Prevention:**
1. The core's only time source is **emulated cycles**: 1 RTC second = 4,194,304 T-cycles (double-speed does not change the RTC rate, so convert via the device-time base, not CPU cycles) with exact remainder carried; this makes headless runs perfectly reproducible.
2. A separate, explicit, bounded **host-supplied elapsed-seconds input** (adapter-only, e.g., at load time or "advance RTC by N seconds") covers offline progression. The core never reads a clock; the player adapter computes `now - saved_timestamp` with checked 64-bit arithmetic, clamps negative (rollback) and huge deltas by documented policy, and records the applied delta.
3. Persist the RTC in the battery file (see V2-15). Replay/acceptance records include the external time input.
4. Add a CI grep/symbol check that `src/core` has no time/clock/rand includes (cheap permanent guard).
**Detection:** run the same ROM twice at different wall times and compare digests; fake-clock adapter tests; rollback and 2^40-second gap cases; pause 10 minutes in the player and assert the policy.
**Phase:** B.
**Confidence:** HIGH (design), builds on F-09.

### V2-15: RTC persistence format and interoperability
**What goes wrong:** Inventing an undocumented footer, writing raw structs (AGENTS.md forbids), storing host-endian/`time_t`-width fields, or inconsistent with other emulators' RTC sidecar formats so users' existing saves import wrongly; v0.1 battery import/export lacks a version field so adding RTC breaks old MBC1 saves; atomic-write and bounded-import rules (SAVE-02/03) are not extended to the longer file.
**Prevention:** Specify an explicit little-endian layout (RAM bytes + fixed RTC trailer with version, live fields, latched fields, halt/carry, saved timestamp as 64-bit unsigned seconds), validate-then-commit, reject wrong length with no mutation, and keep MBC1/MBC5 saves unchanged. Decide deliberately whether to also import the commonly used 48-byte VBA-style trailer [KB] (recommend import-only after format is verified against a pinned source, otherwise defer and document). Carry MBC2's canonical 512-byte nibble save.
**Detection:** fuzz the import; round-trip with fresh instance and fresh process; wrong-RTC-save negative control; v0.1 MBC1 saves still load.
**Phase:** B.
**Confidence:** MEDIUM.

### V2-16: MBC3 bank-range and variant edges
**What goes wrong:** Treating MBC3 as 4 RAM banks only, or allowing banks 4-7 on a 32 KiB cart; ROM bank 7 bits vs a larger variant; selecting an RTC register on a cart type that has no TIMER ($11-$13) so RTC "appears" on non-timer carts; selecting $00-$03 RAM on `$0F` (timer, no RAM) mapping nonexistent RAM. [PD MBC3, Cartridge_Header]
**Prevention:** feature flags derive from the type table ({RAM, BATTERY, TIMER}) not from the mapper family; unmapped selections read $FF and ignore writes; one named test per cartridge type code.
**Phase:** B.
**Confidence:** MEDIUM-HIGH.

### V2-17: Fixture licensing traps (fonts, submodules, "MIT repo" assumptions)
**What goes wrong:** Extends F-21 and GB-FIXTURE-001. The repository root license does not cover each included asset. Specific traps for v0.2 corpora:
- Mooneye's shared text-printing include carries a third-party font (already handled by replacement in v0.1). Mapper and CGB tests built from the same include inherit the same issue: the original ROM-drawn text path also needs PPU reporting, which v0.1 excluded (GB-CORPUS-001).
- SameSuite, Mealybug, acid2 and blargg test sets each have their own license posture; blargg's `gb-test-roms` historically ship without an explicit license [KB]; verify, do not assume, SameSuite's and acid2's licenses and build assets at the pinned commit. [KB]
- Test repos often use **git submodules** or fetch toolchains (RGBDS, WLA-DX) and screenshots/reference images. A recursive clone silently imports additional unlicensed content, and expected screenshots may be hardware captures of Nintendo-licensed output.
- Homebrew games for acceptance (Phase A) often have separate code and asset licenses (some assets NC or no-derivs) [KB].
**Prevention:** Fixture admission checklist per source: exact commit, SPDX per file group (code, font, graphics, audio, reference images), submodule list with their licenses, redistribution decision, digest, and "built by us from source with pinned toolchain" vs "binary taken". If any part is unclear, keep it out of the repository and run only as an ignored local differential (F-22). Fetch non-recursively and enumerate with `git ls-files --stage` to detect gitlinks; reuse the existing fixture manifest, `.gitattributes` and digest tooling (GB-FIXTURE-001 CRLF lesson applies to any new text/binary fixture).
**Detection:** CI rule that every file under `fixtures/` is covered by a manifest entry with a license and digest and every gitlink is rejected; license review recorded in the same PR as admission.
**Phase:** A (game), B, D, E (corpora).
**Confidence:** MEDIUM ([LOCAL] high; per-repo license facts [KB], verify).

---

## Moderate pitfalls (CGB video, banking, compat mode)

### V2-18: Palette RAM access rules copied from VRAM/OAM
**What goes wrong:** Applying the VRAM/OAM lockout window to CRAM (palettes block only during mode 3), skipping index auto-increment on a blocked write, auto-incrementing on read, wrapping the index at the wrong place, or leaving CRAM readable/writable with LCD on at wrong times.
**Facts [PD Palettes]:** BGPI/OBPI freely accessible; BGPD/OBPD data port: during mode 3 writes are ignored and reads return $FF; the index **auto-increments after each write even if the write was ignored**; reads never auto-increment; index wraps 63 to 0; colors are RGB555 little-endian with bit 15 ignored; each CRAM is 64 bytes (8 palettes x 4 colors x 2 bytes); OBJ color 0 is always transparent. BG colors start white; OBJ CRAM is mostly uninitialized.
**Prevention:** separate predicates for VRAM, OAM, CRAM accessibility; CRAM store as raw 64-byte arrays and convert at render time (hash canonical bytes, F-16); explicit reset policy for uninitialized OBJ CRAM (V2-07). Both mid-write instruction alignment (the first byte of a pair written in HBlank, second in mode 3) need device-time tests.
**Detection:** guest ROM writes 64 bytes through the port across modes and reads back; blocked write still advances index; read without advance; wrap at 64.
**Phase:** D.
**Confidence:** MEDIUM-HIGH [PD].

### V2-19: Object priority, OPRI, and BG-over-OBJ conflated
**What goes wrong:** Using DMG X-coordinate priority in CGB mode (or vice versa); resolving BG-over-OBJ before object-vs-object priority; treating LCDC bit 0 as BG enable in CGB mode; ignoring both the OAM attribute priority bit and BG tile attribute priority bit; applying OPRI after the boot ROM unmapped when its effect is uncertain.
**Facts [PD OAM, CGB_Registers]:** DMG: smaller X wins, ties by OAM order; CGB: OAM order only. Object priority is resolved first, then the winner's "BG over OBJ" flag is evaluated (a high-priority object with the flag can hide lower-priority objects, even those without it). OPRI (FF6C bit 0) selects the style; the boot ROM sets it from the mode; upstream marks effects after boot unmap as "TO BE VERIFIED", and says the change is instant. In CGB mode, LCDC bit 0 means BG/window master priority (objects always on top when clear) rather than BG enable, and BG tile attribute bit 7 also forces BG over OBJ [KB; confirm in Pan Docs Tile_Maps/LCDC].
**Prevention:** one explicit function that takes {mode, OPRI, LCDC.0, BG attr priority, OAM priority, color indices} and is unit-tested exhaustively (small input space), independent of the rendering path (GB-CPU-002 independent-oracle approach); in DMG-compat mode on CGB, set OPRI per boot state (V2-07). Treat OPRI writes after boot as a documented project choice with the uncertainty stated.
**Detection:** exhaustive truth-table test; cgb-acid2 as supporting evidence only (V2-21).
**Phase:** D.
**Confidence:** MEDIUM ([PD] for priority rules; LCDC.0 and attribute-bit semantics [KB]).

### V2-20: CGB-mode register visibility and compat-mode behavior
**What goes wrong:** Exposing CGB registers in DMG-compat mode (or hiding them in CGB mode), forgetting that KEY0 is locked after boot, allowing the program to switch DMG/CGB mode at runtime, mishandling DMG palette registers in compat mode, VRAM bank 1/WRAM bank switching working in compat mode.
**Facts [PD]:** KEY0 ($FF4C) is written only by the boot ROM and locked afterward; bit 2 = DMG compat mode; in non-CGB mode KEY1, VBK, HDMA1-5, RP, SVBK read $FF; palette registers BGPI/BGPD/OGPI/OGPD depend on compat mode; VBK reads bit 0 with other bits 1; SVBK 0 selects bank 1, WRAM bank 0 fixed at C000-CFFF, banks 1-7 at D000-DFFF. In compat mode BGP/OBP0/OBP1 writes feed the compat palettes in CRAM [KB; Pan Docs does not describe the mapping on the page fetched].
**Prevention:** Make mode a per-instance constant set during load/reset (KEY0 write is a boot-state event, not a guest-writable register after init); a visibility table (register x {DMG, CGB-native, CGB-compat}) in code and docs with a test per cell, including write-ignored and read-$FF cases; add every new IO address to `read_supported`/`write` preflight lists deliberately (GB-VIDEO-001 and GB-CORPUS-001 are the exact failure: logic exists but preflight excludes it, or an unsupported read returns $FF and a corpus appears to pass).
**Detection:** register visibility matrix test; guest that tries to write KEY0, VBK, SVBK in DMG profile and in compat mode and reads back.
**Phase:** C (table), D (palette parts).
**Confidence:** MEDIUM-HIGH.

### V2-21: VRAM bank 1 / attribute rendering details
**What goes wrong:** Attribute map read from the wrong bank, tile data bank bit ignored, flip bits applied to the wrong axis or for 8x16 objects, 8x16 object bit 0 behavior, the sprite tile bank bit confused with the BG one, VBK mid-scanline changes, VRAM lock applied to only bank 0, HDMA destination ignoring VBK. [KB; Pan Docs Tile_Maps/OAM]
**Prevention:** separate bank storage `vram[2][8192]` with a single accessor taking an explicit bank argument; tile fetcher logic never reads "current VBK" for rendering (only CPU access does); test each attribute bit independently with original ROMs; keep the DMG fetch path unchanged and covered by V2-01.
**Phase:** D.
**Confidence:** MEDIUM.

### V2-22: Double-speed timer/serial/OAM DMA/PPU CPU-visible edges
**What goes wrong:** Timer (TIMA/TMA/TAC/DIV) edge logic keyed to M-cycle counters instead of DIV falling edges so double speed changes the edge-to-instruction relationship; serial clock not doubled or CGB fast-serial missing; OAM DMA duration assumed 160 M-cycles real-time in both speeds; CPU access timestamps in double speed span two per dot, so v0.1's "same half-dot" ordering resolution may be too coarse. [PD CGB_Registers for rates; granularity [LOCAL]]
**Prevention:** audit each device's tick function for implicit assumptions "1 CPU M-cycle = 4 timeline ticks"; unit tests at the boundary in both speeds (partition equivalence, XFER-004); re-run the three admitted Mooneye closures unchanged under the DMG profile and add equivalent CGB-profile closures only where the fixture is model-applicable.
**Phase:** C/E.
**Confidence:** MEDIUM.

### V2-23: Model-difference scope creep and unlabeled revisions
**What goes wrong:** "CGB" is not one chip: CGB-0, A, B, C, D, E and AGB differ in documented ways (boot ROM variants, wave RAM initialization, APU, timing). Pan Docs notes CGB0 does not initialize wave RAM, AGB changes B and flag behavior, and hand-off values differ across revisions. [PD Power_Up_Sequence] Implementing "whatever the test passes" mixes revisions.
**Prevention:** pick one named baseline (recommendation: CGB-E, the revision most hardware-observed suites target; confirm in the pinned suite READMEs) and explicitly exclude AGB/older revisions in the ledger, consistent with the out-of-scope list. Every test case in the corpus manifest gets `{model, revision, applicability, expected}`; inapplicable cases are excluded from the denominator, not counted as passes (F-01). D-025 applies: use a deterministic, confidence-qualified model where silicon is undetermined.
**Detection:** wrong-model control (a CGB-D-only expected result must not pass CGB-E qualification); nonzero per-model denominators.
**Phase:** E.
**Confidence:** HIGH (process); revision choice MEDIUM.

---

## Moderate pitfalls (evidence and claims)

### V2-24: Claiming compatibility from test-ROM pass rates
**What goes wrong:** Extends F-20. cgb-acid2 passing is described as "CGB compatible"; SameSuite totals mixed across revisions; Mooneye/mapper tests passing is described as "MBC5 supported" while games using bank features unexercised by the tests fail; the support ledger reads like a universal claim.
**Prevention:** the ledger states: model/revision x feature (mapper, speed, HDMA, palette modes) x evidence class (hardware-backed, differential oracle, metamorphic, regression fixture, private observation) x corpus revision x counts. "Supported" means "passes the named corpus and the game-acceptance run", never "plays games". Keep one acceptance game (V2-26) as the only gameplay claim; for CGB add a rights-clear CGB title or ROM only if it exists, otherwise state "no CGB game-level evidence". Do not write "compatible" without a denominator.
**Detection:** docs lint for unqualified words (compatible, supports all) in release notes and README; ledger rows missing denominators fail CI.
**Phase:** E, F.
**Confidence:** HIGH.

### V2-25: Oracle ancestry for CGB work
**What goes wrong:** Cross-checking GabbaBoy against SameBoy/mGBA/Gambatte-derived behavior and treating agreement as truth (F-10), or porting expected values from them (license and circularity). CGB has fewer hardware-observed references than DMG, so agreement between emulators is more tempting.
**Prevention:** record oracle ancestry per case; prefer hardware-observed ROM suites (Mooneye CGB cases, SameSuite) as primary; emulator output as differential only; when only emulators disagree or no hardware reference exists, mark UNKNOWN with an expected-failure reason rather than choosing silently. No code or tables copied from reference emulators without license review.
**Phase:** C-E.
**Confidence:** HIGH.

### V2-26: Game-level acceptance that proves nothing
**What goes wrong:** Extends XFER-006/GB-GAME-001. (a) "Reached title screen" or "frames are changing" counted as progress; (b) attract-mode loops pass; (c) acceptance with a commercial/private ROM, trace, or save committed; (d) assertion on a screenshot hash only, tied to platform-specific scaling/gamma; (e) the chosen game needs MBC5/CGB, defeating the "prove DMG first" purpose; (f) the game's license covers the binary but not its assets or reuse in CI; (g) "perceptually looks right" or "sounds right" written as a pass without a human, or a UAT invented to satisfy a template.
**Prevention:** pick a rights-clear ROM-only/MBC1 DMG game whose license (code + art + audio, separately) permits redistribution or build-from-source in CI; define the predicate **in guest memory** (e.g., a documented RAM variable/tilemap state/OAM count or an input-dependent state transition), plus a **negative control**: same run with no input (or a wrong input) must not reach the state, and a mutated core path must fail it (F-10). Capture the player-visible side as evidence of *response* (frame differs after input; non-silent PCM after a trigger) but label it as machine-checked response, not perceptual quality. If it stalls, use a bounded PC/opcode/bus/interrupt trace and add a small rights-clear regression (GB-GAME-001). Private titles stay in ignored local records.
**Detection:** acceptance run is in the exact-head required gate; predicate documented in the manifest; control runs included in the expected-test inventory.
**Phase:** A (gate before B-E claims).
**Confidence:** HIGH.

### V2-27: Nondeterministic input replay and unseeded game state
**What goes wrong:** Input recorded in host frames, wall time or SDL event timestamps; replay applies keys at "frame N" where frame boundaries differ (LCD-off periods have no VBlank; CGB double speed changes cycles per frame); JOYP sampling vs IF.4 edges (v0.1 JOYP model) make a one-cycle shift change a game's RNG; games seed RNG from DIV phase or uninitialized WRAM/HRAM, so a different power-on fill diverges; audio/video hashes depend on the host resampler or scaler.
**Prevention:** record input as `(emulated device time in timeline ticks, key mask)` against a ROM digest, model/profile, power-on-state policy version and API/emulation version; use the core's own deterministic timeline in headless replays; document and fix the power-on RAM fill pattern as part of the profile (and call out that real hardware is random); hash canonical native pixels and PCM, not presentation output (F-16); pace by emulated time only. Run each replay twice in one process and across two fresh processes plus the multi-instance interleaving check (GB-TEST-002) before accepting it.
**Detection:** replay twice differs only if state is wrong; changing the power-on fill intentionally changes the digest for an RNG-sensitive game (proves the dependency is recorded).
**Phase:** A.
**Confidence:** MEDIUM-HIGH.

### V2-28: Test-inventory and gate regressions from adding many new cases
**What goes wrong:** GB-GSD-002 / GB-CI-003 / F-11 at a larger scale: new CGB or mapper tests not in `expected-tests.txt`, regexes selecting stale families, sanitizer subset missing new files, CGB corpus reported skipped on a runner, GSD `workflow.test_command` still a no-op (GB-GSD-006).
**Prevention:** name families (`mbc2_*`, `mbc3_*`, `mbc5_*`, `rtc_*`, `cgb_*`, `hdma_*`, `speed_*`, `palette_*`) and use family-wide filters; update the inventory in the same PR; keep fail on skip; set the project test command so the GSD gate cannot pass as `true`; verify the three required contexts at the exact head. Add Windows/MinGW to the mapper and CGB lanes (RTC 64-bit time and endianness are likely host-sensitive).
**Phase:** every phase.
**Confidence:** HIGH ([LOCAL]).

### V2-29: Player integration surprises
**What goes wrong:** Color output through SDL changes presentation geometry or pixel-format assumptions tested in GB-PLAYER-001; RGB555 expansion/LCD color correction applied silently and baked into hashes; save-path code for RTC/MBC2 bypasses the existing atomic-write and lock protocol; RTC adapter reads wall time on the audio/UI thread; the player advertises CGB when only a subset passes.
**Prevention:** keep raw native pixels in the core API and any color correction in the adapter as a labeled option (default plain 5-to-8-bit expansion, documented formula); reuse the same battery session/lock for all mapper saves; the player passes RTC input through the public API only; update player help text and README per capability.
**Phase:** D (video), B (saves), F (docs).
**Confidence:** MEDIUM-HIGH.

---

## Minor pitfalls

- **MBC1M and other mappers assumed away:** the ledger must list "MBC1M, MBC30 beyond tested sizes, MBC6/7, HuC1/3, TAMA5, camera" as unsupported with a bounded loader rejection, not a silent attempt.
- **Echo RAM with WRAM banking:** E000-FDFF mirrors C000-DDFF, so reads from echo of D000-DDFF must follow the current SVBK bank. [KB] Easy to forget when WRAM becomes banked; add a test.
- **OAM DMA source decoding on CGB:** source ranges ≥ $E000 and VRAM bank/WRAM bank used as the source differ by model. [KB]
- **LCD-off during HDMA/CRAM access:** palette access and HDMA when LCD is off; document and test.
- **Uninitialized CGB memory:** VRAM bank 1, WRAM banks, OAM, CRAM need a deterministic fill policy recorded in the profile (V2-07/V2-27).
- **Unbounded diagnostics or trace in the acceptance runner:** keep trace bounded per GB-GAME-001.
- **Documentation drift:** update API docs, support ledger, limitations, examples and changelog in the same PR as each capability; remember the v0.1 changelog compare-link lesson (GB-RELEASE-001) and give v0.2 a `## v0.2 ...` ROADMAP heading from the start (GB-GSD-013).
- **Phase pause:** do not chain phases; each phase stops with evidence and the next command (AGENTS.md).

---

## Phase-specific warnings

| Phase slot | Likely pitfall | Mitigation |
|---|---|---|
| A: game acceptance | V2-26, V2-27, V2-17 (game license) | Guest-memory predicate + negative control; replay keyed to device time; license by code/art/audio; ignored local record for any private title |
| B: MBC5 | V2-08, V2-09, V2-10, V2-12 | Separate mapper; two-register 9-bit bank; per-type admission table; MBC1 evidence unchanged |
| B: MBC2 | V2-11, V2-12 | Bit-8 decode table test; 512x4 canonical save; size from mapper not `$149`; 16 ROM banks max |
| B: MBC3 + RTC | V2-13..V2-16 | Emulated-time-only core; adapter-only offline delta; explicit LE trailer; latch/halt/carry truth tables; hardware source pinned |
| C: CGB foundation | V2-01, V2-02, V2-06, V2-07, V2-20 | Freeze DMG regressions first; model-gate audit; header-to-mode table; original compat palette policy; register visibility matrix |
| C: speed switch | V2-03, V2-04, V2-22 | Timeline-unit decision up front; separate CGB STOP path; per-device ratios; pause as modeled state |
| D: video | V2-18, V2-19, V2-21, V2-29 | Separate CRAM/VRAM/OAM predicates; exhaustive priority truth table; bank-explicit fetcher; raw RGB555 in core |
| D: HDMA/GDMA | V2-05 | Scheduler stall state; mode-0 edge starts; HALT/LCD-off/cancel tests; hardware-observed DMA suite with reviewed license |
| E: model quals | V2-23, V2-24, V2-25 | One named revision; per-model denominators; UNKNOWN with expected-failure reasons; oracle ancestry |
| F: release | V2-24, V2-28, V2-29 | Ledger with denominators; exact-head gates; docs lint for unqualified compatibility words |

Research flags (deeper phase research needed): **B-RTC** (undefined write/subsecond behavior), **C-speed switch** (pause-time interrupts, DIV behavior), **D-HDMA** (stall/halt/LCD-off/overflow), **D-priority/compat palette mapping**, **E-APU/CGB model differences**. Standard patterns: MBC5/MBC2 mapping, loader tables, fixtures manifest.

---

## Sources

Fetched 2026-10-10 (Pan Docs, community documentation; MEDIUM-HIGH, includes upstream "to be verified" notes):
- [Pan Docs MBC3](https://gbdev.io/pandocs/MBC3.html), [MBC2](https://gbdev.io/pandocs/MBC2.html), [MBC5](https://gbdev.io/pandocs/MBC5.html)
- [Pan Docs CGB Registers (KEY0/KEY1, HDMA, VBK/SVBK, OPRI)](https://gbdev.io/pandocs/CGB_Registers.html)
- [Pan Docs Palettes](https://gbdev.io/pandocs/Palettes.html), [OAM](https://gbdev.io/pandocs/OAM.html)
- [Pan Docs Cartridge Header](https://gbdev.io/pandocs/The_Cartridge_Header.html), [Power-Up Sequence](https://gbdev.io/pandocs/Power_Up_Sequence.html)

Not re-fetched this session ([KB], verify before depending): Pan Docs Audio details (frame sequencer DIV bits), Tile Maps/LCDC bit 0 semantics, OAM Corruption Bug scope, SameSuite/Mooneye/Mealybug/cgb-acid2/blargg licenses and CGB applicability, VBA-style RTC trailer layout, MBC30 limits.

Repository evidence: `../../PITFALLS.md` (F-01..F-25), `../../../context/LESSONS.md` (XFER-001..006, GB-CORPUS-001, GB-CI-001/003, GB-CORE-001, GB-VIDEO-001, GB-FIXTURE-001, GB-TEST-002, GB-GAME-001, GB-GSD-002/006/013, GB-PLAYER-001, GB-RELEASE-001), `../../PROJECT.md`.
