---
phase: "11"
slug: "cgb-colour-rendering-and-player-colour"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-12"
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Seeded from `11-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | CTest over C executables with `REQUIRE` macros; CMake `-P` verifiers; stdlib Python verifiers with `--self-test`; configure-time core mutants |
| **Config file** | `CMakePresets.json` (`phase1`, `phase1-asan`, `cmake-3.25.3`); `tests/expected-tests.txt`; `tests/player/expected-tests.txt` |
| **Quick run command** | `ctest --preset phase1 -R '^(cgb_\|palette_\|magentests_cgb_\|model_gates)' --output-on-failure --no-tests=error` |
| **Full suite command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error && bash tests/scripts/verify-dmg-baseline.sh` |
| **Player command** | `bash tests/scripts/verify-phase3-player.sh --build-package` (runs `ctest -R '^player_'`) |
| **Estimated runtime** | ~120 seconds quick; ~10 minutes full + ASan |

---

## Sampling Rate

- **After every task commit:** the narrow `ctest -R` for the touched area, plus `bash tests/scripts/verify-dmg-baseline.sh` after any task that edits `src/core/gabbaboy.c`, `src/runner/*` or `src/accept/*` (D-25).
- **After every plan wave:** full `phase1` suite, `phase1-asan` for core-touching waves, then the DMG baseline; the player command before Wave 5 closes.
- **Before `/gsd-verify-work`:** full suite green on every required CI leg at the exact PR head; `fixture-repro` reports `byte-identical` for `cgb-colour` and `magentests`; `11-BENCH.md` recorded; `summary_coverage` passes.
- **Max feedback latency:** 120 seconds for the quick command.

---

## Per-Task Verification Map

Plans fill in task IDs; each row below must be owned by at least one task `<automated>` verify with a `<fails_when>`.

| Req / Decision | Plan | Wave | Behaviour | Test Type | Automated Command | Negative control | File Exists | Status |
|---|---|---|---|---|---|---|---|---|
| D-25, D-02 | 11-01 | 1 | colour path never writes DMG shade buffer; DMG baseline identical | white-box + baseline | `ctest -R '^cgb_dmg_identity'`; `verify-dmg-baseline.sh` | mutant writing `frame_working` from colour path | ❌ W0 | ⬜ pending |
| CGB-04 / D-10..D-13 | 11-02 | 2 | BCPS/OCPS index, auto-increment, 6-bit wrap, read-back, blocked write increments, blocked read `$FF`, reads never increment, compat `$FF` | white-box unit | `ctest -R '^palette_cram_'` | mutants: no increment on blocked write; increment on read | ❌ W0 | ⬜ pending |
| CGB-04 / D-12 | 11-02 | 2 | lockout is `ppu_mode == 3` predicate, LCD off clears it | unit | `ctest -R '^palette_cram_lockout'` | predicate always-allowed mutant | ❌ W0 | ⬜ pending |
| CGB-04 / D-08 | 11-02 | 2 | OPRI read `$FE\|bit0`, no priority effect; compat `$FF` | unit | `ctest -R '^palette_opri_'` | live-OPRI mutant | ❌ W0 | ⬜ pending |
| CGB-04 / D-31 | 11-02 | 2 | three DEFERRED(11) cells flipped in table, docs and independent visibility table | unit + CMake | `ctest -R '^cgb_(visibility\|tables)_'` | mutated doc copy | ✅ rewrite | ⬜ pending |
| CGB-04 / D-14, D-40 | 11-02 | 2 | post-boot CRAM `$7FFF`, VRAM bank 1 zero | white-box | `ctest -R '^cgb_postboot_'` | `--flip` control | ✅ extend | ⬜ pending |
| CGB-04 / D-05, D-38, D-39 | 11-03 | 3 | each BG attr bit, bit 4 ignored, window same fetch, OBJ bank/palette, compat ignores attrs | white-box + fixture | `ctest -R '^cgb_attr_'` | ignore-bank, swap-flip, read-VBK mutants | ❌ W0 | ⬜ pending |
| CGB-04 / D-06, D-07, D-22 | 11-03 | 3 | exhaustive priority truth table incl. LCDC.0 master priority; asserted row count | white-box | `ctest -R '^cgb_priority_'` | per-input mutants | ❌ W0 | ⬜ pending |
| CGB-04 / D-23 | 11-04 | 3 | original RGBDS fixtures rebuild byte-identically, guest markers pass | fixture | `ctest -R '^cgb_colour_guest_'`; `fixture-repro` | manifest/digest tamper | ❌ W0 | ⬜ pending |
| CGB-04 / D-15, D-16, D-02 | 11-05 | 4 | `gbb_copy_frame_rgb555` argument matrix, DMG profile unsupported, no mutation on error, LCD-off `0x7FFF`, reset zero-fill | unit | `ctest -R '^cgb_rgb555_'` | skewed validator; LCD-off fill-0 mutant | ❌ W0 | ⬜ pending |
| CGB-05 / D-17, D-17a, D-18, D-39 | 11-05 | 4 | compat palette API, bit 15 rejected, survives reset/load, OAM bit 4 selects OBJ set, default ramp equals doc | unit + doc mirror | `ctest -R '^(palette_compat_\|cgb_tables_compat_palette)'` | mask-bit-15 mutant; BG-set-for-objects mutant; mutated doc | ❌ W0 | ⬜ pending |
| CGB-04 / D-01, D-23.4, D-43 | 11-06 | 4 | per-line HBlank CRAM change visible per row; runner digests RGB555 | fixture | `ctest -R '^cgb_colour_hblank_rows'` | resolve-at-copy-time mutant must exit 1 | ❌ W0 | ⬜ pending |
| CGB-04 / D-21 | 11-06 | 4 | three MagenTests ROMs pass structural predicates; last two frames identical; digest pinned after predicate | third-party fixture | `ctest -R '^magentests_cgb_'` | per-ROM mutant | ❌ W0 | ⬜ pending |
| CGB-09 / D-26 | 11-07 | 5 | `--model auto\|dmg\|cgb`, bad value exit 2, PGB error, re-probe on open | player unit | `ctest -R '^player_cgb_model'` | `select_profile` ignores flag mutant | ❌ W0 | ⬜ pending |
| CGB-09 / D-27, D-28 | 11-07 | 5 | `(c<<3)\|(c>>2)` expansion, title token | player unit | `ctest -R '^player_cgb_(expand\|title)'` | R/B swap, grey path mutants | ❌ W0 | ⬜ pending |
| CGB-09 / D-30 | 11-07 | 5 | CGB smoke: RGBA digest, distinct colours, spot pixels, title token | player e2e | `ctest -R '^player_cgb_smoke$'` | `player_cgb_smoke_mutant_*` exit non-zero | ❌ W0 | ⬜ pending |
| CGB-09 / D-44 | 11-07 | 5 | limitation text, help, `capability_limits` agree | unit | `ctest -R '^player_limitations'` | pinned text | ✅ edit | ⬜ pending |
| D-34 | 11-08 | 6 | palette-register fuzz, no output pixel has bit 15 | fuzz | `ctest -R '^cgb_fuzz_'` + `phase1-asan` | invariant-break seed in mutant | ✅ extend | ⬜ pending |
| D-32 | 11-08 | 6 | model-gate tags and docs agree; research:11 gates disposed | script | `ctest -R '^model_gates'` | scanner mutants | ✅ | ⬜ pending |
| D-33 | 11-08 | 6 | A/B bench receipt, DMG digest identical on both builds | script | `ctest -R '^cgb_bench_ab_'` | wrong-digest/missing-field controls | ✅ | ⬜ pending |
| D-42 | 11-08 | 6 | docs + consumers use every new symbol | doc contract + consumers | `ctest -R '^(cgb_native_guide_contract\|installed_consumer_)'` | missing-phrase selftest | ✅ extend | ⬜ pending |
| D-37 | all | all | SUMMARY coverage auto-passable | script | `ctest -R '^summary_coverage'` | selftest mutants | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_cgb_colour_internal.c` (white-box CRAM, buffers, truth table, mutant harness) and `tests/test_cgb_colour.c` (public API, fixtures)
- [ ] `tests/data/cgb-priority-truth.inc` and its independent generator with regenerate-and-compare test
- [ ] `fixtures/cgb-colour/` (sources, ROMs, manifest, LICENSE) and `tests/scripts/reproduce-cgb-colour.sh`; `fixture-repro.yml` step
- [ ] `fixtures/magentests/` +3 ROMs, manifest, SOURCES.md, ELIGIBILITY.md; per-ROM repro table; `tests/test_magentests.c` cases
- [ ] `src/player/colour.[ch]`, `tests/player/test_colour.c`, `player_cgb_*` registrations
- [ ] `gbb_accept_rgb555_*` helpers and tests
- [ ] CGB workload for `measure_core` (extension or sibling)

Framework install: none.

---

## Manual-Only Verifications

All phase behaviors have automated verification (D-069). Owner veto items in CONTEXT (D-15, D-17a, D-18, D-26, D-08, D-21, D-24) are owner decisions, not UAT.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
