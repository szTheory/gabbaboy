## Phase 11: CGB colour rendering and player colour

CGB software now renders in colour through a new `gbb_copy_frame_rgb555` call. This covers tile attributes from VRAM bank 1, BG/OBJ colour palette RAM (auto-increment, mode-3 lockout) and CGB priority, with LCDC.0 as master priority. Colour is resolved per dot against live CRAM, into RGB555 buffers kept separate from the DMG shade buffers.

DMG software on the CGB profile renders through an original, documented compatibility palette that a host can override with `gbb_set_compat_palette` / `gbb_get_compat_palette`. No boot-ROM palette table ships.

The SDL3 player takes `--model auto|dmg|cgb` (default `dmg`), expands RGB555 into the existing RGBA32 texture and passes an automated CGB colour smoke.

The DMG profile stays byte-identical. `tests/baseline` is unchanged, `verify-dmg-baseline.sh` passes at every core-touching step, a white-box shade-identity pin plus a mutant guard the DMG frame path, and `gbb_copy_frame` behaviour is unchanged.

### Owner veto items (veto window: before this PR merges)

1. **`gbb_copy_frame_rgb555` shape (D-15).**
   - Byte pitch and byte capacity, as for `gbb_copy_frame`; both must be even.
   - Native `uint16_t` values `R | G<<5 | B<<10` with bit 15 always 0.
   - It serves the CGB profile in both modes and returns `GBB_UNSUPPORTED_PROFILE` on the DMG profile; widening later is additive.
   - Validation and no-write-on-error follow `gbb_copy_frame`.
2. **Compat palette API (D-17a).**
   - `gbb_compat_palette { struct_size; bg[4], obj0[4], obj1[4] }` with `GBB_COMPAT_PALETTE_SIZE_V1`.
   - `gbb_set_compat_palette` (NULL restores the default) and `gbb_get_compat_palette`.
   - Set validates the whole struct first and rejects bit 15 rather than masking it.
   - It is instance configuration: it survives reset and ROM load and is not emulation or save state.
3. **Default compat palette look (D-18).**
   - An original neutral, slightly warm ramp `$639F, $4275, $254B, $0421`, identical for BG, OBJ0 and OBJ1.
   - It comes from a documented rule and is pinned against `docs/cgb-profile.md`.
   - No title-hash table, and no boot-ROM or peer values.
4. **Player default `--model dmg` (D-26).** `auto` and `cgb` are opt-in, so dual-mode Libbet (the Phase 7 baseline) stays on DMG; Phase 15 may flip the default. Only the three player session sites route through the profile selector.
5. **OPRI stored, no priority effect (D-08).** It reads `$FE | bit0` in CGB mode and `$FF` in compat. Object order is latched to the mode.
6. **MagenTests evidence labels (D-21).** `bg_oam_priority` is a CGB hardware photo (revision E unattested), `oam_internal_priority` is a SameBoy differential (not hardware) and `ppu_disabled_state` is author-attested.
7. **acid2 stays out of the repo and required CI (D-24, G1).** An optional local runner takes a ROM pinned by SHA-256. The executor ran the real pinned cgb-acid2 and dmg-acid2 locally (not committed), and both matched their references.

**D-29 judgement.** The API additions are two functions for the frame call and compat palette, one struct and one size constant, all appended. No existing function changes behaviour. `gbb_copy_frame` keeps returning `GBB_UNSUPPORTED_PROFILE` on the whole CGB profile (D-16).

**Deviation (D-20).** AGE has no CGB colour, attribute or priority ROM; its only CGB image tests are `m3-bg-{lcdc,scx}`, which need CGB mode-3 timing (Phase 14). Success criterion 1's "AGE/MagenTests" is therefore met by:
- the exhaustive generated truth table;
- three MagenTests ROMs;
- six original RGBDS fixtures.

The AGE and Mealybug mode-3 cases are recorded as expected-unsupported or unsupported-model in `tests/external/cgb-ppu-dispositions.json`, with no third-party bytes in the repo.

### Requirement to evidence

| Requirement | Evidence | Class |
|---|---|---|
| CGB-04 CRAM ports, attributes, priority, RGB555 frame call | `palette_cram_*` (blocked-write increment, read never increments, lockout predicate, compat `$FF`) with 4 mutants; `cgb_attr_*`; `cgb_priority_truth_table` (6144 rows from an independent stdlib oracle written from Pan Docs) with 12 per-input mutants; `cgb_rgb555_*` with a skewed-validator mutant; original fixtures `cgb_colour_{hblank_rows,attr,lcdc0,guest_cram,lcd_off}` (the per-line HBlank fixture catches resolve-at-copy-time); `magentests_cgb_*` with 4 mutants; runner `acceptance_cgb_colour_*` and `acceptance_digest_rgb555_vectors`; `cgb_external_dispositions` | hardware-derived and differential third-party ROMs, original regression fixtures, an independent oracle |
| CGB-05 compat palette | `cgb_compat_internal_*`, `palette_compat_*` (bit-15 rejected, survives reset, effect next frame) with a mask-bit-15 mutant; `palette_compat_mapping` fixture with a host override; `cgb_tables_compat_palette` (doc equals code and rule) with a mutated-doc control | white-box, doc mirror, original fixture |
| CGB-09 player | `player_cgb_cli`, `player_session_model_*`, `player_cgb_expand`, `player_cgb_title_token`, `player_cgb_smoke` (pinned RGBA digest, 14+ distinct colours, 40 spot pixels computed from the fixture's literal palette) with R/B-swap, DMG-path and ignored-flag mutants; `player_claims_agree` with a mutated control | player e2e with dummy SDL drivers |

Engineering close-out:
- **Model gates:** every `research:11` gate is disposed (`model_gates_no_phase11_rows` plus a mutated doc).
- **Fuzzing:** the fuzz target covers palette RAM and the compat API, with a bit-15 mutant.
- **Benchmark:** the advisory DMG A/B against Phase 10 shows medians of 98.5-100.2 percent with the digest held, so D-22 did not fire and D-04 is no hoist (`11-BENCH.md`).

### Verification

The execute-phase tail ran these gates:
- **Nyquist validation:** `validated`, `nyquist_compliant: true`; all 25 rows are automated.
- **Security:** 43/43 threats closed, `threats_open: 0` (`11-SECURITY.md`).
- **Code review:** 0 critical, 3 warnings and 5 info. Seven were fixed and one (WR-01) needed no change; a negative control was added for it anyway (`11-REVIEW-DISPOSITION.md`).
- **Regression gate:** 689/689 CTest and `baseline status=pass`. The macOS player package gate passed (93/93 player tests).
- **gsd-verifier:** `passed`, 3/3 (`11-VERIFICATION.md`).

Two CI defects were found on the pushed branch and fixed in this PR:
- **LeakSanitizer exit codes.** Deliberately failing mutant tests return early from a `REQUIRE`, and LeakSanitizer replaced their expected exit 1 with its own code. Leak detection is now off for the failing mutant run only; it stays on for the controls.
- **CGB-04 marked complete too early.** A plan executor marked CGB-04 complete before the phase finished; this was reverted until phase completion.

### Deferred and limitations

Deferred:
- CGB mode-3 length, WX and CRAM lock-edge quirks (Phase 14; DMG mode-3 timing is kept on CGB, tagged UNKNOWN);
- double speed (Phase 12) and HDMA (Phase 13);
- a player compat-palette flag, colour correction, the `auto` player default, and RGB555 on the DMG profile.

Limits:
- The player does no colour correction.
- The compat palette is the core default; there is no player flag for it.
- AGE and Mealybug mode-3 suites are expected-unsupported and not counted as passes.
- No commercial game or boot ROM is involved.

This PR stays open until `/gsd-verify-work 11` passes. The squash merge happens only afterwards, at an exact-head green head.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
