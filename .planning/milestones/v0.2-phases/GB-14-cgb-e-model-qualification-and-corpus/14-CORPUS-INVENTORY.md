# Phase 14 corpus source and output inventory

**Evidence scope.** Source applicability is read from immutable pins, not inferred from filenames. A candidate source is not an output ROM, an admitted fixture, a CGB-E eligible case, an execution, or a passing assertion. Local output counts are opened from the manifests and source docs. Mooneye source list/header excerpt at pin `31510e12eea6286d36eea060a6adde755e1067aa`; SameSuite at `f15645fb049a47ea235f6d2c9a033e72d8087901`; AGE at `1f5bc10e2cb60b86c19f8d0287ff78f410c4f639`; MagenTests at `3f9c090f16e5a721db776febb9ba7d773e1c819c`. [CITED: https://github.com/Gekkio/mooneye-test-suite/tree/31510e12eea6286d36eea060a6adde755e1067aa] [CITED: https://github.com/LIJI32/SameSuite/tree/f15645fb049a47ea235f6d2c9a033e72d8087901] [CITED: https://github.com/c-sp/age-test-roms/tree/1f5bc10e2cb60b86c19f8d0287ff78f410c4f639] [CITED: https://github.com/alloncm/MagenTests/tree/3f9c090f16e5a721db776febb9ba7d773e1c819c]

## Mooneye: all unique source paths whose pinned source header lists CGB in pass or fail

Header excerpts below are verbatim. Exact unique set: 83; CGB pass-header sources: 59; CGB fail-header sources: 26; overlap: 2; disjoint: 57 pass-only / 24 fail-only / 2 both. This is source applicability, not an E-only hardware claim. Four outputs are already admitted; five additional selected sources were built in scratch; 74 candidate rows are explicitly excluded from the finite Phase 14 selection. [VERIFIED: fixtures/mooneye-cgb/manifest.json:33-40; quote: `"required_roms": ["boot_regs-cgb.gb", "boot_div-cgbABCDE.gb", "boot_hwio-C.gb", "unused_hwio-C.gb"]`]

| Source at pin | Header line(s), verbatim | Phase 14 disposition |
|---|---|---|
| `acceptance/add_sp_e_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/bits/mem_oam.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/bits/reg_f.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/bits/unused_hwio-GS.s` | `;   fail: CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/boot_div-S.s` | `;   fail: DMG, MGB, CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/boot_div-dmg0.s` | `;   fail: DMG ABC, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/boot_div-dmgABCmgb.s` | `;   fail: DMG 0, SGB, SGB2, CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/boot_div2-S.s` | `;   fail: DMG, MGB, CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/boot_hwio-S.s` | `;   fail: DMG, MGB, CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/boot_hwio-dmg0.s` | `;   fail: DMG ABC, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/boot_hwio-dmgABCmgb.s` | `;   fail: DMG 0, SGB, SGB2, CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/boot_regs-dmg0.s` | `;   fail: DMG ABC, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/boot_regs-dmgABC.s` | `;   fail: DMG 0, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/boot_regs-mgb.s` | `;   fail: DMG, SGB, SGB2, CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/boot_regs-sgb.s` | `;   fail: DMG, MGB, SGB2, CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/boot_regs-sgb2.s` | `;   fail: DMG, MGB, SGB, CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/call_cc_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/call_cc_timing2.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/call_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/call_timing2.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/di_timing-GS.s` | `;   fail: CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/div_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/ei_sequence.s` | `;   pass: DMG0, DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/ei_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/halt_ime0_ei.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/halt_ime0_nointr_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/halt_ime1_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/halt_ime1_timing2-GS.s` | `;   fail: CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/if_ie_registers.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/instr/daa.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | include: D-13 unsuffixed CGB-pass candidate |
| `acceptance/interrupts/ie_push.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/intr_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/jp_cc_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/jp_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/ld_hl_sp_e_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/oam_dma/basic.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: OAM DMA outside selected Phase 14 families |
| `acceptance/oam_dma/reg_read.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: OAM DMA outside selected Phase 14 families |
| `acceptance/oam_dma/sources-GS.s` | `;   fail: CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/oam_dma_restart.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: OAM DMA outside selected Phase 14 families |
| `acceptance/oam_dma_start.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: OAM DMA outside selected Phase 14 families |
| `acceptance/oam_dma_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: OAM DMA outside selected Phase 14 families |
| `acceptance/pop_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/ppu/hblank_ly_scx_timing-GS.s` | `;   fail: CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/ppu/intr_1_2_timing-GS.s` | `;   fail: CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/ppu/intr_2_0_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: PPU acceptance outside named AGE mode-3/window discriminators and CGB-08 scope |
| `acceptance/ppu/intr_2_mode0_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: PPU acceptance outside named AGE mode-3/window discriminators and CGB-08 scope |
| `acceptance/ppu/intr_2_mode0_timing_sprites.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: PPU acceptance outside named AGE mode-3/window discriminators and CGB-08 scope |
| `acceptance/ppu/intr_2_mode3_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: PPU acceptance outside named AGE mode-3/window discriminators and CGB-08 scope |
| `acceptance/ppu/intr_2_oam_ok_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: PPU acceptance outside named AGE mode-3/window discriminators and CGB-08 scope |
| `acceptance/ppu/lcdon_timing-GS.s` | `;   fail: CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/ppu/lcdon_write_timing-GS.s` | `;   fail: CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/ppu/stat_irq_blocking.s` | `;   pass: DMG ABC, MGB, CGB, AGB, AGS` | exclude: PPU acceptance outside named AGE mode-3/window discriminators and CGB-08 scope |
| `acceptance/ppu/stat_lyc_onoff.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: PPU acceptance outside named AGE mode-3/window discriminators and CGB-08 scope |
| `acceptance/ppu/vblank_stat_intr-GS.s` | `;   fail: CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/push_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/rapid_di_ei.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/ret_cc_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/ret_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/reti_intr_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/reti_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/rst_timing.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: generic CPU/interrupt/timing family outside selected APU/I/O and inherited timing families |
| `acceptance/serial/boot_sclk_align-dmgABCmgb.s` | `;   fail: DMG 0, SGB, SGB2, CGB, AGB, AGS` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `acceptance/timer/div_write.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | include: D-13 unsuffixed CGB-pass candidate |
| `acceptance/timer/rapid_toggle.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: timer case outside selected DIV/APU discriminator set |
| `acceptance/timer/tim00.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | include: D-13 unsuffixed CGB-pass candidate |
| `acceptance/timer/tim00_div_trigger.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | include: selected DIV/APU trigger discriminator |
| `acceptance/timer/tim01.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: timer case outside selected DIV/APU discriminator set |
| `acceptance/timer/tim01_div_trigger.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: timer case outside selected DIV/APU discriminator set |
| `acceptance/timer/tim10.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: timer case outside selected DIV/APU discriminator set |
| `acceptance/timer/tim10_div_trigger.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: timer case outside selected DIV/APU discriminator set |
| `acceptance/timer/tim11.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: timer case outside selected DIV/APU discriminator set |
| `acceptance/timer/tim11_div_trigger.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: timer case outside selected DIV/APU discriminator set |
| `acceptance/timer/tima_reload.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: timer case outside selected DIV/APU discriminator set |
| `acceptance/timer/tima_write_reloading.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: timer case outside selected DIV/APU discriminator set |
| `acceptance/timer/tma_write_reloading.s` | `;   pass: DMG, MGB, SGB, SGB2, CGB, AGB, AGS` | exclude: timer case outside selected DIV/APU discriminator set |
| `misc/bits/unused_hwio-C.s` | `;   pass: CGB, AGB, AGS` | include: admitted; CGB-E currently stops at PCM12; compat |
| `misc/boot_div-A.s` | `;   fail: DMG, MGB, SGB, SGB2, CGB` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `misc/boot_div-cgb0.s` | `;   pass: CGB 0; ;   fail: DMG, MGB, SGB, SGB2, CGB ABCDE, AGB, AGS` | exclude: alternate boot/stepping row outside chosen existing compatibility rows and CGB-08 scope |
| `misc/boot_div-cgbABCDE.s` | `;   pass: CGB ABCDE; ;   fail: DMG, MGB, SGB, SGB2, CGB 0, AGB, AGS` | include: admitted, author CGB A–E (not E-alone); compat |
| `misc/boot_hwio-C.s` | `;   pass: CGB, AGB, AGS` | include: admitted; CGB-E currently stops at PCM12; compat |
| `misc/boot_regs-A.s` | `;   fail: DMG, MGB, SGB, SGB2, CGB` | exclude: source reports CGB in fail list, not a CGB pass target for this model corpus |
| `misc/boot_regs-cgb.s` | `;   pass: CGB` | include: admitted, author CGB pass; compat |
| `misc/ppu/vblank_stat_intr-C.s` | `;   pass: CGB, AGB, AGS` | include: D-13 source-only CGB-pass candidate |

Finite selection: existing `misc/boot_regs-cgb.s`, `misc/boot_div-cgbABCDE.s`, `misc/boot_hwio-C.s`, `misc/bits/unused_hwio-C.s`; new `acceptance/instr/daa.s`, `acceptance/timer/div_write.s`, `acceptance/timer/tim00.s`, `acceptance/timer/tim00_div_trigger.s`, `misc/ppu/vblank_stat_intr-C.s`. `unused_hwio-C` and `boot_hwio-C` currently stop at PCM12; completion after Phase 14 will require real guest pass observations. Five new outputs were built via a scratch copy of the exact existing source/WLA-DX + patch + zero-font workflow: all are 32768 bytes, each header `$143=00`, total build 4.83 seconds including the pinned WLA build. New admitted bytes remain zero. Exact selected case registration and fixture digests remain plan work. [VERIFIED: tests/scripts/reproduce-mooneye-cgb.sh; opened build flow and exact WLA/source/tool pins in this session.]

## SameSuite APU: all 70 source paths

The pinned APU README author-reports CGB-E passes all APU tests and names SameBoy differences `channel_4_freq_change` and `channel_1_sweep_restart_2`. Preserve that independent author expectation and use SameBoy as differential evidence. All 70 APU sources are selected; suffixes do not exclude. The pinned RGBDS 1.0.1 scratch build produced 70 APU outputs (78 total Makefile outputs) in 4.23 seconds; admitted APU outputs remain 0; current four admitted SameSuite outputs are DMA. [CITED: https://github.com/LIJI32/SameSuite/blob/f15645fb049a47ea235f6d2c9a033e72d8087901/apu/README.md] [VERIFIED: fixtures/samesuite/manifest.json:25-44; quote: `"version": "1.0.1"`, `"archive_sha256": "2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645"`]

- `apu/channel_1/channel_1_align.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_align_cpu.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_delay.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_duty.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_duty_delay.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_extra_length_clocking-cgb0B.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_freq_change.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_freq_change_timing-A.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_freq_change_timing-cgb0BC.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_freq_change_timing-cgbDE.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_nrx2_glitch.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_nrx2_speed_change.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_restart.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_restart_nrx2_glitch.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_stop_div.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_stop_restart.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_sweep.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_sweep_restart.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_sweep_restart_2.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_volume.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_1/channel_1_volume_div.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_2/channel_2_align.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_2/channel_2_align_cpu.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_2/channel_2_delay.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_2/channel_2_duty.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_2/channel_2_duty_delay.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_2/channel_2_extra_length_clocking-cgb0B.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_2/channel_2_freq_change.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_2/channel_2_nrx2_glitch.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_2/channel_2_nrx2_speed_change.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_2/channel_2_restart.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_2/channel_2_restart_nrx2_glitch.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_2/channel_2_stop_div.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_2/channel_2_stop_restart.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_2/channel_2_volume.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_2/channel_2_volume_div.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_3/channel_3_and_glitch.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_3/channel_3_delay.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_3/channel_3_extra_length_clocking-cgb0.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_3/channel_3_extra_length_clocking-cgbB.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_3/channel_3_first_sample.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_3/channel_3_freq_change_delay.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_3/channel_3_restart_delay.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_3/channel_3_restart_during_delay.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_3/channel_3_restart_stop_delay.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_3/channel_3_shift_delay.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_3/channel_3_shift_skip_delay.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_3/channel_3_stop_delay.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_3/channel_3_stop_div.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_3/channel_3_wave_ram_dac_on_rw.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_3/channel_3_wave_ram_locked_write.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_3/channel_3_wave_ram_sync.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_4/channel_4_align.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_4/channel_4_delay.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_4/channel_4_equivalent_frequencies.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_4/channel_4_extra_length_clocking-cgb0B.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_4/channel_4_freq_change.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_4/channel_4_frequency_alignment.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_4/channel_4_lfsr.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_4/channel_4_lfsr15.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_4/channel_4_lfsr_15_7.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_4/channel_4_lfsr_7_15.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_4/channel_4_lfsr_restart.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_4/channel_4_lfsr_restart_fast.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/channel_4/channel_4_volume_div.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/div_trigger_volume_10.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/div_write_trigger.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/div_write_trigger_10.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/div_write_trigger_volume.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.
- `apu/div_write_trigger_volume_10.asm` — selected, pinned, X11/CC0 closure, RGBDS 1.0.1 build.

## AGE inherited mode-3 source/output candidates

Pinned AGE has six ROM-producing ASM source paths plus six CGB-E reference PNGs; its Makefile maps `.asm` to `build/...gb` and copies `.png` references. All six ROM outputs were admitted and reproduced from a clean scratch tree with digest-pinned RGBDS 1.0.1 in 0.40 seconds. Four normal-speed cases are CGB-E pass targets (two native-mode and two compatibility-mode); two double-speed siblings are separately classified. Phase 14 Plan 09 executed all six source-image comparisons with exact RGB555 signatures; all currently fail without changing the upstream author pass targets. The pinned manifest and PPU ledger carry the stable case identities and mismatch counts. [CITED: https://github.com/c-sp/age-test-roms/tree/1f5bc10e2cb60b86c19f8d0287ff78f410c4f639] [VERIFIED: fixtures/age/SOURCES.md:5-16; quote: `- Pinned commit: `1f5bc10e2cb60b86c19f8d0287ff78f410c4f639``]

| Source ASM | Reference PNG | Applicability | Selection |
|---|---|---|---|
| `src/m3-bg-lcdc/m3-bg-lcdc.asm` | `src/m3-bg-lcdc/m3-bg-lcdc-cgbBCE.png` | CGB/native normal speed; source `Verified` CGB-E | include pass target |
| `src/m3-bg-lcdc/m3-bg-lcdc-nocgb.asm` | `src/m3-bg-lcdc/m3-bg-lcdc-nocgb-ncmBCE.png` | CGB-E/DMG compatibility normal speed; source `Verified` CGB-E | include pass target |
| `src/m3-bg-lcdc/m3-bg-lcdc-ds.asm` | `src/m3-bg-lcdc/m3-bg-lcdc-ds-cgbBCE.png` | CGB/native double speed; source `Verified` CGB-E | include DS sibling separately |
| `src/m3-bg-scx/m3-bg-scx.asm` | `src/m3-bg-scx/m3-bg-scx-cgbBCE.png` | CGB/native normal speed; source `Verified` CGB-E | include pass target |
| `src/m3-bg-scx/m3-bg-scx-nocgb.asm` | `src/m3-bg-scx/m3-bg-scx-nocgb-ncmBCE.png` | CGB-E/DMG compatibility normal speed; source `Verified` CGB-E | include pass target |
| `src/m3-bg-scx/m3-bg-scx-ds.asm` | `src/m3-bg-scx/m3-bg-scx-ds-cgbBCE.png` | CGB/native double speed; source `Verified` CGB-E | include DS sibling separately |

## AGE existing software observations

AGE has 13 admitted ROM outputs; these eight rows are already admitted and were re-executed through current verbose CTest. Reported values are software model observations, not hardware results. [VERIFIED: fixtures/age/manifest.json; quote: `AGE admitted manifest fixture list` (13 rows); tests/external/cgb-speed-dispositions.json holds row masks/signatures.]

| Case | Current observation |
|---|---|
| `spsw-mode0-cgbBCE` | 3/15 pass; separate LY `ds-lcd-cpu-alignment` and SCX/STAT `cgb-mode3-length` failures. |
| `spsw-ch2-lc-delay-cgbBCE` | 3/8 pass; five fail with `apu-lc-delay-after-switch`. |
| `stat-mode-cgbE` | 5/14 pass; single-speed control. |
| `stat-mode-ds-cgbBCE` | 0/14 pass; DS sibling also fails, not speed-only. |
| `stat-mode-sprites-dmgC-cgbBCE` | 3/10 pass; single-speed control. |
| `stat-mode-sprites-ds-cgbBCE` | 2/16 pass; separate DS sibling. |
| `stat-mode-window-cgbBCE` | 0/16 pass; normal-speed control. |
| `stat-mode-window-ds-cgbBCE` | 0/16 pass; same no-pass result across speed supports shared mode3/window family attribution. |

All eight existing rows retain their exact signature and row masks in `tests/external/cgb-speed-dispositions.json`. The comparison supports narrow shared STAT/window attribution and two separate `spsw-mode0` causes; it does not justify a general PPU fix. [VERIFIED: tests/external/cgb-speed-dispositions.json; quote: `"reason": "expected-failure:cgb-mode3-length"`, `"row_mask": "01C0"`, `"signature_sha256": "d2410ea8e30311f12de296781986f7e12edd0b87b729033d879cef5e2f133e82"`.]

## MagenTests source/output/admission ledger

Pinned manifest has seven admitted ROM outputs. Three MBC outputs are DMG-profile only, three PPU outputs yield four selected cases (disabled-state native and compat), and admitted HBlank DMA is the fifth eligible CGB-profile case. `key0_lock_after_boot` is source-only, belongs to prior KEY0 scope and contributes no executable case. [VERIFIED: fixtures/magentests/manifest.json:25-94; quote: fixture row includes `"alias": "hblank_vram_dma"`, total manifest has 7 fixture rows.]

| Pinned source | Output/cases | Treatment | Rights/build/oracle status |
|---|---|---|---|
| `src/mbc_oob_sram/main.asm` | `3 outputs / 3 candidates` | `exclude: DMG profile` | `MIT; RGBDS 0.6.1; admitted` |
| `src/ppu_disabled_state/main.asm` | `1 / 2 cases` | `include both native + compat` | `MIT + CC0; admitted; author-attested` |
| `src/color_bg_oam_priority/main.asm` | `1 / 1 case` | `include` | `MIT + CC0; admitted; CGB photo, E unattested` |
| `src/oam_internal_priority/main.asm` | `1 / 1 case` | `include` | `MIT + CC0; admitted; SameBoy differential` |
| `src/hblank_vram_dma/main.asm` | `1 / 1 case` | `reuse existing row` | `MIT + CC0; admitted; SameBoy differential` |
| `src/key0_lock_after_boot/main.asm` | `0 admitted / 0 cases` | `exclude: prior KEY0 scope` | `source-only; no fixture bytes` |

Documentation conflict to repair: the final `ELIGIBILITY.md` paragraph says the HBlank fixture is not vendored, while the same doc lines 42-47 call it admitted and the manifest contains its seventh ROM; retain the actual manifest/admission/repro row and correct the stale sentence. [VERIFIED: fixtures/magentests/ELIGIBILITY.md:42-47, 106-107; exact conflicting phrases are “is admitted” and “not vendored”.]
