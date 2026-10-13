# Phase 12: CGB Double Speed - Context

**Gathered:** 2026-10-13
**Status:** Ready for planning
**Method:** Advisor fan-out with auto-follow, per the owner's standing instruction (re-pasted during this discussion). Six researchers ran in parallel, each with an adversarial pass:
- switch sequence and pause
- clock domains and the `research:12` model gates
- oracles, fixtures and expected failures
- host API, player and docs
- a cross-emulator gap sweep (SameBoy `c4cf7ab`, mGBA `143adf5`, AGE `4a8ec44`, libretro Gambatte `d9d6cd0`, ares)
- robustness, security and verification automation (added when the owner re-pasted the boilerplate)

A separate adversarial reviewer checked the synthesised draft against SameBoy `c4cf7abab79a`, AGE `1f5bc10e`, Pan Docs master (`CGB_Registers.md` at `bdb4df1`), libretro Gambatte and repo HEAD `70c441b`. It amended D-02, D-04, D-05, D-06, D-08, D-09, D-10, D-12, D-13, D-19, D-21, D-22, D-25, D-26, D-27 and D-29, and added D-34 to D-36. Its load-bearing claims were re-verified locally:
- A budget smaller than one instruction returns `GBB_STOP_BUDGET` with nothing consumed (`tests/test_control.c:47`). `GBB_STOP_NO_PROGRESS` comes only from the stopped branch (`src/core/gabbaboy.c:3941`).
- The halt branch steps per M-cycle with a wake check at each step (`:3970-3987`).
- The STOP gate-tag anchor is at `tests/CMakeLists.txt:1760`.
- SameBoy `stop()` sends a held button into HALT (`sm83_cpu.c:392-446`).

Reconciliation rule, as in Phases 10 and 11: hardware tests beat Pan Docs prose, which beats a single emulator. Where evidence runs out, the tie goes to DMG byte-identity, determinism and fail-closed honesty. Owner veto points are listed at the end.

<domain>
## Phase Boundary

Phase 12 delivers CGB-06:
- On the CGB profile in CGB mode, KEY1 arm followed by STOP switches CPU speed.
- CPU, timer/DIV, serial and the OAM DMA byte period run at twice the rate in double speed.
- PPU, APU and RTC timing are unchanged in master time.
- The switch pause is explicit, resumable stall state with a sourced, named duration. Devices keep advancing during it, and it never enters the DMG `stopped` sleep path.
- Partitioned runs equal one run across switches and stalls.
- Unresearched pause behaviours are recorded as named expected failures, each pinned to its exact current behaviour.

Not in this phase:
- HDMA/GDMA (Phase 13). Only the stall predicate that Phase 13 will attach to is shaped now.
- CGB-E APU/I/O differences such as PCM12/PCM34 (Phase 14).
- CGB mode-3 length (D-083, Phase 14).
- Save-state serialisation (v0.3). New fields are listed for it, but no serialiser is built.
- Any player feature.

</domain>

<decisions>
## Implementation Decisions

### A. Switch sequence (STOP with KEY1 armed)

- **D-01: The switch path is gated by `model_is_cgb(m) && exec_mode == GBB_MODE_CGB && key1_armed`.**
  - The DMG-profile STOP path and the unarmed or compat-mode STOP path stay byte-identical. Compat mode already reads KEY1 as `$FF` and ignores writes (SameBoy `memory.c`; `docs/cgb-profile.md`).
  - The GATE-74 `bus_unsupported` latch at `$FF4D` is removed, and the `DEFERRED(12)` text goes with it.
- **D-02: The decision table is SameBoy's `stop()` (`Core/sm83_cpu.c` ~L385-455, `c4cf7abab79a`), triangulated with AGE.** It is evaluated at STOP.
  - SameBoy `Core/` is under the Expat licence (MIT-equivalent; the extra condition covers `iOS/` only). The table may be re-expressed with attribution, but code is never copied verbatim without the notice.
  1. **A selected joypad line is low** (`(P1 & $0F) != $0F`, SameBoy `exit_by_joyp`). There is no switch, KEY1 stays armed and DIV is not reset.
     - If `IE & IF & $1F` is 0, the operand is fetched, PC = pc+2, and the CPU enters the existing **HALT** branch with its normal wake rules.
     - If it is non-zero, STOP is 1 byte and there is no halt.
     - Basis: ORACLE_SAMEBOY (`immediate_exit && !interrupt_pending → halted`). Tag UNKNOWN. This is the held-button hostile case.
  2. **`IE & IF & $1F` is non-zero at STOP:**
     - The switch happens: speed flips, KEY1 bit 0 clears, DIV resets.
     - There is no stall, and STOP is 1 byte, so the next byte executes as an opcode.
     - With IME set, dispatch follows normally.
     - Basis: AGE `caution/spsw-interrupts*` (author-attested hardware) confirms no pause and the DIV reset. The speed flip and the 1-byte length are ORACLE_SAMEBOY only, because the AGE rows cannot distinguish them. Tag UNKNOWN.
  3. **Otherwise:** the operand byte is fetched and PC = pc+2.
     - At STOP retire, `double_speed` toggles, KEY1 bit 0 clears, and DIV plus the divider phase reset through the shared GATE-65 reset (falling-edge `timer_set_signal` and the APU edge included). The reset is extracted to one helper used by both STOP paths.
     - Then the stall counter loads.
     - Basis: AGE `spsw-stop-prefetch-cgbBCE` and `spsw-div-cgbBCE` (author-attested hardware), SameBoy and Gambatte.
- **D-03: KEY1 reads `$7E | (double_speed << 7) | key1_armed` on the CGB profile in CGB mode.**
  - `double_speed` is the single source of truth for bit 7. Never store bit 7 separately.
  - The compat-mode and DMG reads are unchanged.
  - KEY0 (`FF4C`) writes can never change speed or mode; add a test for it.
- **D-04: STOP decides its D-02 case first, then preflights only the bytes it actually fetches** (D-073 fail-closed through `instruction_reads_supported`).
  - The 1-byte cases never preflight the operand, because hardware never reads it.
  - The operand value is ignored, so `$00` and `$FF` operands give identical results; test both.
  - AGE `spsw-stop-prefetch` fetches STOP from `$FF04`. Verify that the CGB `io_visibility` table allows opcode fetch from FF04-FF06.

### B. Pause (stall) model

- **D-05: Duration is `GBB_SPEED_SWITCH_STALL_T = 0x20008` CPU T-cycles at the new (destination) speed.**
  - That is 131080 master half-dots when switching to double speed (about 15.6 ms) and 262160 when switching to normal (about 31.3 ms).
  - Sources:
    - SameBoy `stop()` `speed_switch_halt_countdown = 0x20008`, decremented in CPU T-cycles at the current speed (`timing.c` `GB_advance_cycles`).
    - Gambatte `Memory::stop`: 0x20000 T to double and 0x20008 T to normal (`ds` is the old speed), so it agrees only for switches to normal.
    - AGE `spsw-tima` expects TIMA `$80` after the switch with the 4 KHz timer (128 × 256 M ≈ 32768 M); 2050 M would give `$08`. These are author-attested hardware rows.
    - AGE `spsw-div` (DIV `$00`/`$01` at DELAY `$3C`/`$3D`) pins the tail to about 4 T modulo 256 T.
  - **The binding requirement is the distance from DIV reset to CPU resume** that `spsw-div` and `spsw-tima` pin, not SameBoy's internal constant.
    - SameBoy's STOP is 2 M with the reset at M1, plus a −4 T `div_cycles` quirk when IME = 0.
    - GabbaBoy's STOP is 1 M (`gabbaboy.c:3581`) with the reset at retire.
    - Write that derivation into `docs/cgb-profile.md` before the first AGE run, and set the GabbaBoy constant from it.
  - SameBoy's own PPU-time pause is about 131076 half-dots to double and 262150 to normal: `speed_switch_freeze = 5`, plus a 6-T `speed_switch_countdown` at the old speed. The half-dot figures above are therefore GabbaBoy's model, not an oracle value.
  - **Rejected:** Pan Docs "2050 M-cycles / 8200 T". AGE hardware rows refute it, and 8200 = `0x2008`, which looks like a dropped digit of `0x20008`. Record this conflict in `docs/cgb-profile.md` and in DECISIONS.
  - The real-time asymmetry between directions is emulator consensus only and is named `expected-failure:speed-switch-stall-direction-asymmetry`.
- **D-06: The stall is persisted state, consumed by its own run-loop branch.**
  - Fields:
    - `cpu_stall_half_dots` (`uint32_t`).
    - `cpu_stall_kind` (`NONE`, `SPEED_SWITCH`; Phase 13 adds a kind).
    - `double_speed` (`uint8_t`).
  - The branch sits after the locked/stopped checks and before interrupt dispatch in `gbb_run_internal`. It copies the **halt branch's** shape (`gabbaboy.c:3970-3987`), not the stopped branch's; the stopped branch freezes devices and has no `audio_preflight`.
  - It steps exactly one CPU M-cycle (`cpu_ticks` 8 half-dots normal, 4 double) through `advance_devices`, and checks `IE & IF & $1F` after every step (D-08, D-34).
  - It returns early when less than one M-cycle of budget remains, runs `audio_preflight` per step (returning `GBB_STOP_OUTPUT_FULL` with no mutation), and repeats the `UINT64_MAX - time_half_dots` headroom check.
  - A larger `min(budget, stall, event)` step is rejected: an internally raised IF would then wake the CPU at a time that depends on where the host cut the budget, which breaks D-26.
  - **A separate branch rather than `halted = 1`** (which is SameBoy's and Gambatte's representation), because:
    - The stall must report `GBB_STOP_BUDGET`, not `GBB_STOP_HALTED_IDLE`. Hosts and the player smoke (`src/player/main.c:1863`) read that reason as an idle guest.
    - It needs its own countdown and kind for Phase 13.
    - HALT-bug and `halt_bug` handling must not leak in.
  - When the budget ends mid-stall it returns `GBB_STOP_BUDGET` and resumes on the next call.
  - It never reports `GBB_STOP_STOPPED` or `GBB_STOP_HALTED_IDLE`; hosts treat those as idle.
  - It never sets `stopped`. A joypad event during the stall only latches IF.
  - Provide a single `cpu_stalled(m)` predicate for Phase 13 HDMA to attach to.
  - Reject an atomic "long instruction": 262160 half-dots exceeds a 140448-half-dot frame budget, so it would never complete. Reject an inline loop and reuse of `stopped`.
- **D-07: Every device keeps advancing during the stall:** PPU, APU, timer/DIV/TIMA, serial and OAM DMA, at the new speed for the CPU-side devices.
  - Basis: the AGE `spsw-tima` comment "the timer keeps running while the CPU is inactive", backed by its hardware rows, plus SameBoy.
  - **Rejected:** Pan Docs "DIV does not tick" (refuted by the same rows).
  - The Pan Docs PPU effects during the pause (black pixels in modes 0/1, no sprites in mode 2) are not modelled: `expected-failure:speed-switch-pause-ppu-output`.
- **D-08: An interrupt ends the stall early, like a HALT wake.**
  - The stall ends early when `IE & IF & $1F` becomes non-zero during it. With IME set the handler dispatches; with IME clear execution resumes after STOP. There is no halt bug.
  - Basis:
    - IME = 1 wake: AGE `caution/spsw-interrupts-cgbE` timer-interrupt rows (author-attested CGB-E hardware; `WARNING.md` reports instability on the author's CGB-E) plus SameBoy (both the halt-wake and the dispatch paths zero the countdown, `sm83_cpu.c` ~L1650/1662).
    - IME = 0 wake: ORACLE_SAMEBOY only, tagged as a separate sub-case.
    - Pan Docs still has a TODO here, so tag UNKNOWN with this basis.
  - **Rejected:** a fixed non-wakeable stall. It is deterministic but contradicts every source that models the pause.
  - `EI; STOP` is covered by tests: the EI delay retires before the stall and the wake follows this rule.
- **D-09: A CPU-to-PPU phase policy on entering normal speed.** No run-loop invariant requires 8-half-dot alignment (bus offsets are relative to `instruction_start_half_dots`). This is a policy about where the CPU lands relative to PPU dots.
  - On every entry into normal speed, if `time_half_dots % 8 == 4`, the CPU resumes 4 half-dots later. Entry points: stall end, a D-08 early wake into normal speed, and the D-02 case-2 switch to normal with no stall.
  - The extension counts as stall time inside the persisted counter. Tag UNKNOWN.
  - The resulting PPU odd-mode phase is `expected-failure:speed-switch-odd-mode-alignment`; SameBoy itself logs "odd mode not supported" here.
  - Do not adopt SameBoy's `speed_switch_freeze` or its 6-tick `speed_switch_countdown` lag.
  - A "±1 half-dot to normal" mutant is equivalent under this realignment and is excluded from D-21.

### C. Clock domains (extends D-070)

- **D-10: Scaling.**
  - CPU-side devices scale through `cpu_ticks(t) = t >> double_speed`: instruction cost, bus offsets, the interrupt/halt literals, TIMA and `timer_reload_remaining`, serial (internal clock), and the OAM DMA byte period.
  - In double speed the divider counter ticks every master half-dot.
  - Each device keeps its remainder and phase across a switch (D-070); assert `remainder < period` after a switch.
  - `timer_reload_remaining` and `serial_edge_remaining` are stored in half-dots today (`gabbaboy.c` ~L2840-2858). They become CPU T-tick countdowns, decremented on the CPU-tick phase, so no fractional remainder can exist at a switch.
    - At normal speed this is equivalent (1 T = 2 half-dots), which is proven by the DMG baseline and tracer digests staying byte-identical.
    - Assert this at the switch, with a mutant that keeps half-dot units.
  - A pending TIMA reload at the switch keeps its remaining CPU ticks.
  - PPU dots, APU and RTC never read `double_speed`. Add a structural check that `double_speed` is absent from the `ppu_*`, `apu_*` and `rtc_*` functions, with a mutant that adds it.
- **D-11: The APU frame-sequencer DIV tap is `divider_counter` bit 12 (`0x1000`) at normal speed and bit 13 (`0x2000`) at double speed,** so the sequencer stays 512 Hz in master time. This applies both in `advance_devices_to` and in the DIV-write/STOP reset edge.
  - Basis: Pan Docs Audio details and SameBoy `timing.c`.
  - Resolves GATE-56 to CGB_ONLY, guarded by `double_speed`.
  - AGE `spsw-ch2-lc-delay` (a one M-cycle length-counter delay after the switch) is `expected-failure:apu-lc-delay-after-switch`, owned by Phase 14.
- **D-12: The `research:12` gate dispositions.** Each one is enforced by `verify-model-gates.py`, and the docs row and the code tag change together.
  - GATE-30 (DMA restart and period): BOTH.
  - GATE-31 (DIV write clocks the frame sequencer): BOTH, using the D-11 tap.
  - GATE-53 (DMA byte period): BOTH, scaled.
  - GATE-65 (DIV reset on STOP): BOTH, with the shared helper from D-02.
  - GATE-56: CGB_ONLY (D-11).
  - GATE-52 (DMA restart): UNKNOWN, `expected-failure:cgb-dma-restart-oracle-only`.
  - GATE-41 (STOP wake conditions): reassigned to research:14.
  - GATE-62 is split: it keeps "DMG/unarmed STOP" as research:14, and the switch moves to new CGB_ONLY rows. The DMG STOP path is unchanged in this phase.
  - The `GBB_MG_STOP_TAG_REGEX` configure-time anchor (`tests/CMakeLists.txt:1760-1767`) must be updated in the same commit, or configure fails.
  - GATE-74: reworded to the implemented switch.
  - New rows:
    - The switch decision (D-02), the stall branch (D-06), the wake (D-08) and the realignment (D-09), each CGB_ONLY with a basis or UNKNOWN.
    - A `cpu_ticks` scaling row (`GUARD=double_speed`) that declares every scaling site: instruction cost, bus offsets, the interrupt and halt literals, the timer reload (inside GATE-54), serial (inside GATE-55) and the DMA period. Rule R2 requires every model difference to be declared.
  - Update the "Release status" paragraph of `docs/model-gates.md`, which names Phase 12.
  - `docs/model-gates.md` contains no `research:12` row at the end of the phase.
- **D-13: Budgets, frames and the trace stay in master half-dots.**
  - A frame is 140448 half-dots at both speeds, and the audio sample count per master interval is unchanged.
  - The trace gets one record at STOP retire and none per stall chunk. There is no speed flag in the trace.
  - A budget smaller than one instruction still returns `GBB_STOP_BUDGET` with `consumed_half_dots == 0`, as today (`tests/test_control.c:47`). A budget that ends mid-stall returns `GBB_STOP_BUDGET` with consumed > 0.

### D. Host surface

- **D-14: No public ABI change.**
  - No new stop reason, no `gbb_run_result` or `gbb_info` field, and no getter. The guest-visible truth is KEY1 bit 7; SameBoy also exposes no public getter.
  - `include/gabbaboy/gabbaboy.h` gets comment updates only (STOP semantics, budgets are master time at both speeds).
  - `cgb_consumer_symbol_coverage` stays unchanged, and the plan asserts this.
- **D-15: The player is unchanged** (`session.c`, `audio.c`, `limitations.h`). That is enforced by tests, not assumed:
  - Add a `player_cgb_speed_smoke` mode to `tests/player/cgb_smoke.cmake` over the new original fixture. It pins the RGBA frame digest and the audio digest after a switch.
  - A broken build with the APU at 2x and one with the PPU following the CPU speed must each fail it.
- **D-16: Installed consumers (C and C++) run the speed fixture in partitions through `gbb_run`** and check `consumed_half_dots` and the frame generation.
- **D-17: Docs are updated in-phase:**
  - `docs/cgb-profile.md`: the STOP section, the KEY1 rows, the resolved D-070 `[VERIFY]` (stall counted at the destination speed, DIV reset at STOP, the APU tap) and a "future save-state fields" list (`double_speed`, `cpu_stall_half_dots`, `cpu_stall_kind`, `key1_armed`).
  - `docs/model-gates.md`.
  - `docs/native-integration.md`: remove "no double speed" and add the master-time budget note.
  - `docs/support/unreleased.md`, `docs/preview.md`.
  - The stale "planned" wording in `docs/cartridge-and-saves.md` and `docs/mbc3-rtc-evidence.md`.
- **D-18: Reset clears `double_speed`, the stall and `key1_armed`** in the same block as `stopped` and `halt_bug`. Each field gets a test, with a negative control that omits that field from the reset.

### E. Oracles and fixtures

- **D-19: Admit 13 AGE ROMs under `fixtures/age/`**, pinned at commit `1f5bc10e2cb60b86c19f8d0287ff78f410c4f639` (tree `2fece1a6…`). AGE is MIT with a CC0 font. These are the first AGE bytes in the repo.
  - Files: `LICENSE.txt`, `SOURCES.md`, `ELIGIBILITY.md`, `manifest.json` (per-ROM SHA-256 and the verbatim "Verified:" header lines) and a copy of `WARNING.md` marked "emulator-only".
  - Rebuild exactly with the AGE Makefile recipe under RGBDS 1.0.1 using a `reproduce-age.sh` (`--self-check` and `--compare`), with one new fixture-repro step. The macOS digests stay provisional until the Linux leg confirms them.
  - Admitted, with their expected results:
    - `spsw-div-cgbBCE`: pass.
    - `spsw-tima-cgbE`: pass target.
    - `spsw-stop-prefetch-cgbBCE`: pass target.
    - `caution/spsw-interrupts-cgbE`: pass target under D-08.
    - `spsw-mode0-cgbBCE`: expected failure per row. The LY rows are `expected-failure:ds-lcd-cpu-alignment`; the SCX rows are `expected-failure:cgb-mode3-length`.
    - `spsw-ch2-lc-delay-cgbBCE`: expected failure (D-11).
    - `stat-mode/stat-mode-ds-cgbBCE`, `stat-mode-sprites/stat-mode-sprites-ds-cgbBCE`, `stat-mode-window/stat-mode-window-ds-cgbBCE`: pass targets, each with a single-speed sibling as control (`stat-mode-cgbE`, `stat-mode-sprites-dmgC-cgbBCE`, `stat-mode-window-cgbBCE`). If the sibling fails too, the failure belongs to Phase 14 (`cgb-mode3-length`), not to speed.
    - `spsw-tima-cgbBC`: a pinned `unsupported-model` row. It is a must-fail control proving the core is not B/C-flavoured **only if `spsw-tima-cgbE` passes**. Otherwise both rows are pinned expected failures and that claim is dropped.
    - The CGB-E-specific rows (`spsw-tima-cgbE` at 65 and 16 KHz and the 4 KHz 1→0 edge, and `spsw-interrupts-cgbE` `OFS_B`) need a one-M-cycle-late immediate TIMA increment after the switch's DIV reset and a one-M dispatch offset. See D-35.
  - `spsw-interrupts-cgbBC` is a digest-only row and is not vendored.
  - Excluded: `_in-progress/*` (no verified header), `m3-bg-*-ds` (D-083), and the single-speed corpus (Phase 14).
  - The target model is CGB-E. AGE "Verified" lines are author attestation; classify them as author-attested hardware and never as a reproducible receipt.
  - "Pass target" means: if the ROM still fails at the phase tail, the fallback is a named expected failure with a pinned signature, plus a recorded reason. It does not mean the constant gets tuned until the ROM passes (D-21).
- **D-20: The AGE protocol is Mooneye-style** (registers 3/5/8/13/21/34, then `LD B,B`; B=0 on failure), using the existing runner adapter. Expected failures compare the `TEST_RESULTS` WRAM digest plus a per-row pass mask. A hang or timeout is a distinct red. If an expected-failure ROM starts to pass, the test fails until its disposition is promoted.
- **D-21: Stall sensitivity sweep.** Run the admitted AGE ROMs against core mutants: stall ±1 M-cycle, +1 half-dot to double, and DIV reset not applied. Record which ROMs discriminate each one.
  - Mutants made equivalent by the D-09 realignment are excluded.
  - Results are read together with the D-35 quirk rows, so a ±1 M stall change cannot "fix" a quirk row.
  - `spsw-div` resolves about 4 T modulo 256 T; TIMA `$80` gives the coarse range.
  - The claim that the stall duration is sourced rests only on the ROMs that discriminate. This prevents fitting the constant to AGE.
- **D-22: Original fixture `fixtures/cgb-speed/`** (project-authored, MIT, RGBDS 1.0.1, rebuilt in fixture-repro).
  - The PPU scanline is the yardstick (LYC). Each phase runs the same probes: single speed, switch to double, switch back, double again.
  - Probes: TIMA per line, DIV per line, serial completion in lines, NR52 ch1 length expiry by line, the OAM DMA 159/161 M-cycle straddle, KEY1 readbacks (`$7E` → `$7F` armed → `$FE` double → `$7E` after return), and lines elapsed across STOP.
  - The STOP bounds derive from D-05 (about 143.7 lines (131080/912) to double and about 287.5 lines (262160/912) to normal, with a declared tolerance), not from Pan Docs.
  - Raw samples go to fixed WRAM. `tests/scripts/derive-cgb-speed-expectations.py` (stdlib only, `python3 -I`) derives every bound from first principles: 4194304 Hz, 456 dots per line, the TAC periods, the divider step, the serial bit time, the speed factor and D-05. It never reads the emulator. The host test re-computes every verdict.
  - Harness controls: a tampered expected table, the clean core, and the derivation run with speed factor 3; each must behave as expected.
  - Hostile pre-switch variants as separate entry points: IE set with an IRQ pending (IME on and off), an IRQ raised during the stall, a held button, `EI; STOP`, LCD off, OAM DMA active, back-to-back switches.
- **D-23: Other suites.**
  - Mooneye: nothing applicable.
  - SameSuite: the KEY1/APU ROMs are one aggregate `expected-unsupported` row with reason `pcm-registers-unbuilt`, owned by Phase 14; nothing is vendored.
  - Gambatte `speedchange`: not admitted (GPL-2.0, CGB-C results); reading only, and nothing derived is committed.
  - Blargg and the acid2 tests: not applicable.
- **D-24: Dispositions go in a new `tests/external/cgb-speed-dispositions.json`.**
  - Fields: `suite`, `case`, `disposition`, `reason`, `owner_phase`, `decision`, `signature_sha256`, `flip_rule`.
  - Its verifier, `cgb_speed_dispositions`, has a mutated negative control. The Phase 11 file and verifier stay unchanged.
  - Every named expected failure in this CONTEXT has a row, and each row pins exact current behaviour.

### F. Verification automation (D-069: zero human UAT)

- **D-25: Mutant set.** Each mutant follows the D-046/D-061 pattern: generated at configure time, with an anchor that matches exactly once in both directions (tagged `/* P12-M<n> */` when the code is written), a test-only library, a named failing case and an in-mutant control.
  - M1: the PPU is scaled by speed.
  - M2: serial is not scaled.
  - M3: timer/DIV is not scaled.
  - M4: the DIV-APU tap is not moved.
  - M5: the stall sets `stopped`.
  - M6: stall length ±1 quantum.
  - M7: devices are frozen during the stall.
  - M8: the switch is not gated on CGB mode.
  - M9: the stall is not bounded by the budget.
  - M10: KEY1 bit 0 is not cleared.
  - M11: the remainder is dropped at the switch.
  - M12: the RTC reads speed.
  - M13: an interrupt does not wake the stall.
  - M14: the OAM DMA period is not scaled.
  - Add M15: CPU-side countdowns kept in half-dot units (D-10). Add M16: wake sampled per run call instead of per M-cycle (D-34).
  - Ceiling: at most 6 mutant library builds. Mutants that do not interact may share a build with separate anchors. State the build count and its measured ASan configure and compile cost. The GB-CI-004 budget applies.
- **D-26: Partition test `cgb_partition_*`.**
  - Exhaustive single cuts at 1-half-dot step in the ±64 half-dot windows at stall start and at stall end.
  - Interior cuts only at fixed points: powers of two and M-cycle boundaries ±1. A stride-8 interior sweep would take about 8 minutes per scenario in the normal build (measured about 47 ns per half-dot), so it is rejected.
  - A hard cap on emulated half-dots per test, sized from 47 ns per half-dot × the ASan factor, so each case stays within D-29.
  - 256 seeded multi-cut cases (a copied xorshift helper; the seed is printed on failure), with at least two cuts asserted inside the stall, plus zero and sub-quantum budgets.
  - Equality is compared over an explicit serialised digest: CPU registers, `time_half_dots`, device phases, the frame digest, PCM, serial output, the RTC, and IF/KEY1/DIV/TIMA/LY/STAT reads.
  - The test also asserts non-zero progress.
  - Sensitivity control: a one-M-cycle shift of a joypad event with joypad IE set, and an independent mutation of one digest input, must each change the digest. A one-half-dot shift is not observable once wake is M-quantised, so it would fail on a correct core.
  - Scenarios: usual, IE set or IRQ pending, held button, LCD on and off, back-to-back switches, and four chained switches.
- **D-27: Fuzz.**
  - Add a `cgb_speed` mode to `test_fuzz_core` (`cgb_fuzz_speed_regressions`) with eight seeds: arm and switch; switch every 4 instructions; IE plus pending IF; held button; OAM DMA active; LCD off; a compat-mode twin; a DMG twin.
  - Each seed has a positive control proving the switch was or was not reached.
  - Invariant oracles on the shared run path: master time is monotonic and equals the sum of consumed half-dots; consumed ≤ budget; `double_speed ⇒ CGB mode`; KEY1 readback is consistent; never STOPPED for a CGB-mode switch; stall ≤ constant.
  - A libFuzzer dictionary entry for `LDH ($4D),A; STOP`.
  - Oracle control: one deliberately broken oracle (for example, the KEY1 consistency check inverted) must raise `contract_failures` above zero, following `cgb_fuzz_palette_mutant_no_mask`.
- **D-28: Headroom test.** Set `time_half_dots` near `UINT64_MAX` before a switch; the run must return INVALID_STATE with no mutation. A mutant that drops the guard must fail it.
- **D-29: ASan/UBSan budget (GB-CI-004).**
  - Each new case runs in about 1 s or less in a Debug ASan build.
  - No `slow` label exists, and the `phase1-asan` preset runs every test, so there is no slow tier. Every case, the partition sweeps included, fits the per-test cap from D-26.
  - Measure and record the phase's added ASan wall time against the GB-CI-004 baseline at the phase tail. Include the configure and compile time of the mutant builds, not only test time.
- **D-30: Benchmark is advisory only.** Record `measure_core` once with a double-speed workload (the new fixture, `--profile cgb`). The DMG baseline and tracer digests must stay byte-identical; that is the gate, and the existing tests run unmodified.
- **D-31: Every plan SUMMARY `coverage:` block uses the GSD block schema** (AGENTS.md). Every new test goes into `tests/expected-tests.txt` in the same PR, with `cgb_speed_`, `cgb_partition_`, `age_` and `cgb_fuzz_` prefixes.

### G. Process

- **D-32: Wave order.**
  1. Mutant harness, the shared DIV-reset helper, and DMG identity baselines.
  2. `double_speed` state, KEY1 readback, scaling and the APU tap.
  3. The STOP decision table, the stall branch and the wake.
  4. Original fixture, partition tests and fuzz.
  5. AGE admission, dispositions and the sensitivity sweep.
  6. Player smoke, consumers, docs, gates, benchmark, DECISIONS/LESSONS and the Phase 13 handoff.
- **D-33: Double speed and HDMA do not run in parallel (ROADMAP).** Phase 13 starts only after this phase merges.

### H. Additions from the adversarial review

- **D-34: Wake is sampled only at CPU M-cycle boundaries during the stall.** This is persisted and partition-invariant. Mutant M16 samples per run call and must fail D-26.
- **D-35: The CGB-E one-M-cycle quirks are named expected failures by default.** These are the late immediate TIMA increment after the switch's DIV reset (`spsw-tima-cgbE` `OFS`) and the dispatch offset (`spsw-interrupts-cgbE` `OFS_B`).
  - Expected-failure name: `expected-failure:cgb-e-div-reset-immediate-increment-delay`.
  - Research may promote either quirk to modelled behaviour only through its own decision row with a source, and never by tuning the shared DIV-reset helper or the D-05 constant.
- **D-36: The held-button rule (D-02 case 1) applies to the armed path only in Phase 12.** Unarmed held-button STOP stays under GATE-62 (research:14). The asymmetry is recorded in `docs/cgb-profile.md` as `expected-failure:unarmed-stop-held-button`.

### Claude's Discretion

- Internal names, and whether `cpu_stall_kind` is an enum or a `uint8_t`.
- The fixture ROM layout and probe line counts within D-22.
- Merging mutants to save compiles.
- Plan granularity within the D-32 waves.

### Owner veto window

These are adopted, but they are the points the owner may want to override:
1. **D-05:** the stall length follows AGE hardware rows and SameBoy/Gambatte (0x20008 T) and overrides Pan Docs' 2050 M.
2. **D-02 / D-08:** the hostile cases follow SameBoy (held button cancels; a pending IRQ means no stall and a 1-byte STOP; an IRQ wakes the stall) and are tagged UNKNOWN. A fixed deterministic stall was rejected.
3. **D-19:** vendoring 13 AGE ROMs (the first AGE bytes, about 416 KiB) into required CI.
4. **D-14:** no public speed getter or stop reason.
5. **D-09:** the alignment policy on entering normal speed (a 4-half-dot extension, tagged UNKNOWN).
6. **D-02 case 1:** a held button sends the CPU into HALT without switching (SameBoy semantics).
7. **D-12:** GATE-41 and the DMG/unarmed part of GATE-62 are deferred to Phase 14.
8. **D-26:** the reduced partition sweep (boundary windows plus fixed interior points, not a full interior stride).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and requirements
- `.planning/ROADMAP.md` §Phase 12 — goal, success criteria, DEEP research items, ordering with Phase 13.
- `.planning/REQUIREMENTS.md` — CGB-06.
- `.planning/context/DECISIONS.md` — D-009 (half-dot timeline), D-025 (best-supported model plus uncertainty), D-046/D-061 (mutant anchors), D-069 (zero human UAT), D-070 (speed domains), D-073 (fail-closed), D-075 (`expected-failure:` naming precedent), D-083 (mode-3 deferral).
- `.planning/context/LESSONS.md` — GB-CI-004 (ASan budget).
- `AGENTS.md`.

### Prior phase decisions
- `.planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-CONTEXT.md` — D-20/D-21 (timeline, `cpu_ticks`), the KEY1 storage.
- `.planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-CONTEXT.md` — D-36 (the colour path reads only PPU time), the dispositions JSON pattern, the player smoke pattern.

### Research
- `.planning/research/v0.2/ARCHITECTURE.md` §3 "Double speed and the event timeline", the CPU-stall row and the anti-patterns.
- `.planning/research/v0.2/PITFALLS.md` — speed-switch and run-loop pitfalls.
- `.planning/research/v0.2/SUMMARY.md` and `STACK.md` — AGE rights and the RGBDS pins.

### Code and docs to change
- `src/core/gabbaboy.c` — `case 0x10` (~3815), the run loop `gbb_run_internal` (~3912-4050), the GATE-65 reset (~4037), the DIV/APU tap (~1953, ~2863), KEY1 (~1328/1348), reset (~1411), the joypad stop-wake (~2160).
- `docs/cgb-profile.md` (STOP with KEY1 armed, KEY1 rows, timeline section), `docs/model-gates.md`, `docs/native-integration.md`, `docs/support/unreleased.md`, `docs/preview.md`, `docs/cartridge-and-saves.md`, `docs/mbc3-rtc-evidence.md`.
- `tests/test_cgb_visibility.c` (the armed-STOP cases ~887-948 flip), `tests/test_cgb_tables.c`, `tests/fuzz_core.c`, `tests/test_control.c` (partition pattern), `tests/player/cgb_smoke.cmake`, `tests/consumers/`, `tests/CMakeLists.txt`, `tests/expected-tests.txt`, `tests/scripts/verify-model-gates.py`.
- `.github/workflows/fixture-repro.yml`, `.github/workflows/ci.yml`.

### External primary sources (read, not vendored except AGE)
- Pan Docs: https://gbdev.io/pandocs/CGB_Registers.html, Reducing_Power_Consumption.html, Timer_and_Divider_Registers.html, Audio_details.html. The 2050 M figure and "DIV does not tick" are rejected (D-05, D-07).
- SameBoy `Core/sm83_cpu.c` `stop()` / `enter_stop_mode()` / `leave_stop_mode()`, `Core/timing.c`, `Core/memory.c` at `c4cf7abab79a` — https://github.com/LIJI32/SameBoy (Expat licence for `Core/`).
- AGE test ROMs `1f5bc10e2cb60b86c19f8d0287ff78f410c4f639` `src/speed-switch/`, `src/stat-mode*/` — https://github.com/c-sp/age-test-roms (MIT, CC0 font).
- libretro Gambatte `libgambatte/src/gambatte-memory.cpp` `Memory::stop` — reading only (GPL-2.0).
- mGBA `src/gb/gb.c` `GBStop` and AGE emulator `age_gb_bus.cpp` `execute_stop` — comparison only.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- The stopped branch in `gbb_run_internal`: an already bounded `step = min(remaining, available, until_event)` with the `apply_input_events_now`-then-subtract ordering and the headroom checks. The stall branch copies its shape (D-06).
- The GATE-65 DIV reset block (~4037) and the DIV-write reset (~1953): extract the shared helper (D-02).
- `divider_counter` (increments per CPU T-cycle; DIV = counter >> 8; APU tap `0x1000`).
- `timer_set_signal` / `timer_bit`: falling-edge semantics preserved across the reset.
- The `gbb_rtc_mutant` / `gbb_banking_mutant` configure-time mutant helpers in `tests/CMakeLists.txt`.
- `tests/fuzz_core.c` `require_contract` / `contract_failures` and the standalone seed runner; `data[0]` bit 7 selects CGB.
- The `tests/test_control.c` partition style; `reproduce-magentests.sh` for `reproduce-age.sh`; the Phase 11 dispositions verifier pattern.
- `tests/player/cgb_smoke.cmake` and its R/B-swap and DMG-path mutant pattern.

### Established Patterns
- Every gate and oracle has a negative control (D-069). The `MODEL:` tags are audited by `verify-model-gates.py`.
- Fixtures are rebuilt byte-identically in fixture-repro, with a manifest, SHA-256 and rights notes.
- C tables are the single source of truth, with a docs mirror and a diff test.
- Append-only public enums; the public ABI stays unchanged unless needed.

### Integration Points
- The instance struct (~338-420): add `double_speed`, `cpu_stall_half_dots` and `cpu_stall_kind` near `key1_armed` / `halted, stopped, halt_bug`.
- `cpu_ticks` at `instruction_cost`, `bus_read`/`bus_write` offsets and the interrupt/halt literals (D-070).
- The run-loop branch order: locked, stopped, the new stall, interrupt, halt, instruction.

</code_context>

<specifics>
## Specific Ideas

- The 16x disagreement between Pan Docs and the hardware ROMs on the pause length is the single most consequential finding. The sensitivity sweep (D-21) exists so the constant is evidenced rather than fitted.
- An atomic pause would hang the run loop on a frame budget. That is the main design risk, and the partition sweep (D-26) is the test that catches it.

</specifics>

<deferred>
## Deferred Ideas

- **Phase 13:** HDMA during the stall (`expected-failure:speed-switch-hdma-hblank-across-stall` until then), attached to `cpu_stalled()`.
- **Phase 14:** GATE-41/GATE-62 DMG STOP wake research, `spsw-ch2-lc-delay`, the SameSuite KEY1/PCM ROMs, CGB mode-3 length (`spsw-mode0` SCX rows, ds STAT fallbacks), and the STOP-triggered OAM bug (`expected-failure:speed-switch-stop-oam-bug`).
- **v0.3:** save-state serialisation of the D-17 field list.
- **Future:** a public speed getter for debuggers or an OSD (additive).

</deferred>

---

*Phase: 12-CGB Double Speed*
*Context gathered: 2026-10-13*
