# GabbaBoy unreleased support-ledger entries

These entries are pending inclusion in the next versioned support ledger, `docs/support/v0.2.0.md`, which is authored with the v0.2.0 release in Phase 15. The release workflow binds only `docs/support/vX.Y.Z.md` files, so this file is not a release claim. The released `docs/support/v0.1.0.md` is unchanged.

## Libbet acceptance scope

- Libbet and the Magic Floor v0.08 has headless acceptance on the deterministic, bootless DMG-CPU-B software profile.
- This is one game. It is not a game-compatibility claim and not hardware qualification. See [Game acceptance](../game-acceptance.md) for the evidence classes, controls and limits.

## Player-platform limitation

- The packaged-player game smoke runs only in the macOS packaged player. Linux and Windows player packaging, and therefore Linux and Windows packaged-player game smoke, are not provided.
- Headless acceptance runs on Linux, macOS and Windows.

## Reproduction

- No hosted Libbet reproduction run exists yet. The reproduction workflow is dispatch-only and has not been dispatched from the default branch.

## Cartridge breadth (Phase 8)

- The core supports MBC2 (types `$05`/`$06`) and MBC5 (types `$19`-`$1E`) on the bootless DMG-CPU-B software profile, alongside ROM-only and standard MBC1. Evidence ledger: [MBC2 and MBC5 evidence](../mbc2-mbc5-evidence.md).
- The Mooneye emulator-only mbc2 (7 of 7) and mbc5 (8 of 8) test ROMs, built from revision `31510e12eea6286d36eea060a6adde755e1067aa`, pass on that profile. The upstream results are author-attested hardware results; here they run on the software profile. They are test-ROM pass counts, not game compatibility, and do not cover CGB, MBC5 RAM or the rumble line.
- The core's ROM length bound is 8 MiB for MBC5 types only; MBC3 types have a 4 MiB ceiling (see Phase 9 below) and every other type keeps its 2 MiB ceiling and error result. The Phase 8 player file bound of 2 MiB was raised to 8 MiB in Phase 9.
- `gbb_rumble_state` exposes the MBC5 rumble line and a saturating transition count. No host haptics exist in the player or runner, and no physical rumble behavior is claimed.
- Player persistence gap (closed in Phase 9): the Phase 8 player ran MBC2 `$06` and MBC5 `$1B`/`$1E` battery cartridges without saving progress. See the Phase 9 section below.
- MBC2 battery images are a canonical 512 bytes; import normalises upper nibbles, and packed 256-byte saves are unsupported.
- GitHub's automatically generated source archives include the `fixtures/mooneye-mbc` directory (about 17 MiB of test ROMs). The install tree and release packages do not contain it; no `export-ignore` is added in Phase 8 and the question is revisited at the release boundary.

## Cartridge breadth (Phase 9)

- The core supports MBC3 (types `$0F`-`$13`) with a deterministic real-time clock that advances only from emulated time (2^23 half-dots per second) and never reads the host clock. Wall-clock time is applied only by the host through `gbb_rtc_catch_up`; importing a battery image never advances the clock. MBC30 is rejected with `GBB_UNSUPPORTED_CARTRIDGE_VARIANT`. Evidence ledger: [MBC3 and RTC evidence](../mbc3-rtc-evidence.md).
- Evidence classes: rtc3test v004 and the MagenTests out-of-bounds SRAM ROMs are author-attested hardware-derived test ROMs executed on the software profile; the clock model, the loader contradiction matrix, the battery block and the player continuation are original differential, metamorphic and regression tests; the latch edge cases, unmapped selections `$04`-`$07`/`$0D`-`$FF` and the `-cart-` save name are project decisions. None is physical-RTC or game-compatibility evidence.
- Timer cartridges (`$0F`, `$10`) export cartridge RAM followed by a 21-byte versioned block (`GBB_RTC_BLOCK_SIZE`); `$0F` has no RAM, so its image is the block alone. Other battery types are unchanged.
- Player persistence now covers MBC1, MBC2, MBC3 and MBC5 battery cartridges. MBC1 `$03` keeps the v0.1 envelope byte-identically; every other type uses envelope version 2 (CRC over the header, not authentication). A reopened timer save catches up by the time since it was saved; a system clock earlier than the save, an unavailable clock or a missing stamp advance nothing. Time spent paused while the player stays open is not recovered.
- Limits: no physical MBC3, RTC or CGB observation, no BGB/VBA-M footer interop, and Mealybug `mbc3_rtc` and gbclock are excluded by rights gates G1 and G3. "Release bytes equal the rebuild" for rtc3test and MagenTests is pending a hosted `result=byte-identical` read at the final evidence head.

## CGB-CPU-E profile (Phase 10)

- Scope: profile, banking and register visibility, original fixtures plus admitted Mooneye boot-register test ROMs. `GBB_PROFILE_CGB_CPU_E` is creatable and probeable, selects CGB or DMG-compatibility mode from header byte `$143`, and exposes VRAM and WRAM banking and the CGB I/O register map. Colour rendering arrived in Phase 11 (see the CGB colour entry below); there is no game compatibility claim and no hardware qualification of a CGB-E board. See [CGB profile](../cgb-profile.md).
- Public API: `gbb_probe_rom`, `gbb_get_info` and `gbb_info` (28 bytes, `struct_size` handshake); PGB-flagged ROMs return `GBB_UNSUPPORTED_EXECUTION_MODE`; `gbb_copy_frame` returns `GBB_UNSUPPORTED_PROFILE` on the CGB profile; `gbb_peek_ram` follows the selected WRAM bank.
- Admitted Mooneye ROMs (revision `31510e12`): `boot_regs-cgb`, `boot_div-cgbABCDE`, `boot_hwio-C` and `unused_hwio-C`, run in compatibility mode. They are author-attested hardware results executed on the software profile. `boot_div-cgbABCDE` applies to CGB revisions A-E, so it is not a CGB-E-only claim. `boot_hwio-C` and `unused_hwio-C` are expected-unsupported (they stop with an unsupported bus at `$FF76`) until Phase 14.
- Deferred at Phase 10 and implemented in Phase 13: HDMA (see below). Other registers deferred to later phases stop with `GBB_STOP_UNSUPPORTED_BUS`. The OAM DMA bus conflict stays as on DMG (expected failure `cgb-separate-buses`). DMG `$FF4C`-`$FF7F` stays fail-closed.
- DMG cost: the profile work adds a measured median cost to the DMG no-trace run of about 6-7% against Phase 7 on a loaded host. That crosses the D-22 review trigger (+5%); the figure is advisory because the host was loaded, and the owner reviews it before merge.
- Sanitizers: the macOS toolchain used for local verification cannot run the leak sanitizer, so the sanitizer evidence for the CGB fuzz and loader paths comes from the hosted Linux legs, not from a local macOS run.

## CGB colour (Phase 11)

- Scope: CGB-mode colour (CRAM palettes, tile attributes, BG-to-OBJ priority), the DMG-compatibility colour palette and a new RGB555 frame call. `gbb_copy_frame_rgb555` copies the completed frame as native-endian `uint16_t` values with bit 15 clear, with byte pitch and capacity, on the CGB profile only (`GBB_UNSUPPORTED_PROFILE` on the DMG profile). `gbb_copy_frame` is unchanged and still returns `GBB_UNSUPPORTED_PROFILE` on the CGB profile. `gbb_compat_palette` with `gbb_set_compat_palette` and `gbb_get_compat_palette` (`GBB_COMPAT_PALETTE_SIZE_V1`) lets a host override the compatibility palette, whose default ramp was authored for GabbaBoy without any third-party palette table. See [CGB profile](../cgb-profile.md) and the [native integration guide](../native-integration.md).
- Evidence classes: original fixtures, an independent priority truth table written from public documentation, differential and metamorphic checks, and MagenTests results as labelled in the evidence ledger. These are software behaviour tests, not hardware observation.
- Limits: the core applies no colour correction, CGB mode-3 timing is not claimed, there is no CGB-E hardware qualification and no game-compatibility claim.

## CGB double speed (Phase 12)

- Scope: on the CGB software profile, guest code switches speed through KEY1 and STOP. Budgets, `consumed_half_dots`, and frames remain in master half-dots at both speeds (140448 half-dots per frame); the guest sees speed through KEY1 bit 7 and there is no public speed getter.
- Pause: the modeled switch pause is consumed across calls, each returning `GBB_STOP_BUDGET` with progress and never `GBB_STOP_STOPPED` or `GBB_STOP_HALTED_IDLE`. A budget below one instruction or one stall M-cycle returns `GBB_STOP_BUDGET` with `consumed_half_dots` zero.
- Evidence: `cgb_speed_*` and `cgb_partition_*` tests cover switching and partitioned progress. `cgb_speed_ppu_apu_rtc_unscaled` checks unscaled device time; `cgb_speed_mutant_m12_rtc_reads_speed` rejects a mutant that scales RTC reads with CPU speed. Among the admitted AGE cases, only `spsw-div-cgbBCE` and `spsw-stop-prefetch-cgbBCE` pass; eleven other cases retain named expected-failure dispositions. These are software-model results, not hardware observations.
- M28 scope: the corrected mutation adds a half-dot only when switching to double speed. `age_sensitivity_m28` shows `spsw-mode0-cgbBCE` discriminates it while `spsw-div-cgbBCE` does not; this DIV result does not generalize to all AGE cases.
- Limits at the Phase 12 boundary: CGB mode-3 timing remained unimplemented. No physical CGB or game-compatibility claim is made.

## CGB HDMA (Phase 13)

- Scope: the unchanged `gbb_run` path executes guest GDMA and HBlank DMA on the bootless CGB-CPU-E software model. FF55 reports active remaining blocks, `$FF` on completion, and the selected waiting-transfer cancellation readback. LCD-off or visible mode 0 admits one initial HBlank block; later blocks need a visible mode-3-to-0 edge. HALT does not replay an edge observed while the CPU is halted.
- Timing and bounds: the selected model commits one byte every four master half-dots, 64 half-dots per 16-byte block, with no modeled startup or teardown. Source and destination ranges are checked per block before mutation; unsupported windows and overflow stop with `GBB_STOP_UNSUPPORTED_BUS`, retaining earlier completed blocks.
- Evidence and limits: the admitted SameSuite and MagenTests cases pass on the selected model; MagenTests is SameBoy-assisted differential evidence. This does not qualify physical CGB-E hardware. The D-06 `$83` -> `$02` -> `$00` -> `$80` sequence remains in conflict with Pan Docs and physical CGB-E remains UNKNOWN/POLICY. Optional Mealybug CGB-C cases are `not-run:rights-gate-G1`, informational only, and outside the CGB-E denominator. CGB mode-3 timing, physical APU behavior, and general game compatibility are not claimed.

