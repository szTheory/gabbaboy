---
phase: GB-11-cgb-colour-rendering-and-player-colour
verified: 2026-10-20T22:33:55Z
status: passed
score: 112/112 must-haves verified
covered_files:
  - ".github/workflows/ci.yml"
  - ".github/workflows/fixture-repro.yml"
  - ".github/workflows/preview.yml"
  - ".planning/REQUIREMENTS.md"
  - ".planning/context/DECISIONS.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-01-PLAN.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-01-SUMMARY.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-02-PLAN.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-02-SUMMARY.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-03-PLAN.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-03-SUMMARY.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-04-PLAN.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-04-SUMMARY.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-05-PLAN.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-05-SUMMARY.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-06-PLAN.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-06-SUMMARY.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-07-PLAN.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-07-SUMMARY.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-08-PLAN.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-08-SUMMARY.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-09-PLAN.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-09-SUMMARY.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-10-PLAN.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-10-SUMMARY.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-11-PLAN.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-11-SUMMARY.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-12-PLAN.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-12-SUMMARY.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-13-PLAN.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-13-SUMMARY.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-14-PLAN.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-14-SUMMARY.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-15-PLAN.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-15-SUMMARY.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-BENCH.json"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-BENCH.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-REFRESH-GATES.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-REVIEW-DISPOSITION.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-REVIEW.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-SECURITY.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-UAT.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-VALIDATION.md"
  - ".planning/phases/GB-11-cgb-colour-rendering-and-player-colour/COVERAGE.md"
  - "README.md"
  - "docs/cgb-profile.md"
  - "docs/model-gates.md"
  - "docs/native-integration.md"
  - "fixtures/cgb-colour/LICENSE.txt"
  - "fixtures/cgb-colour/attr.asm"
  - "fixtures/cgb-colour/colour-attr.gb"
  - "fixtures/cgb-colour/colour-compat.gb"
  - "fixtures/cgb-colour/colour-cram.gb"
  - "fixtures/cgb-colour/colour-hblank.gb"
  - "fixtures/cgb-colour/colour-lcdc0.gb"
  - "fixtures/cgb-colour/colour-lcdoff.gb"
  - "fixtures/cgb-colour/common.inc"
  - "fixtures/cgb-colour/compat.asm"
  - "fixtures/cgb-colour/cram.asm"
  - "fixtures/cgb-colour/hblank.asm"
  - "fixtures/cgb-colour/lcdoff.asm"
  - "fixtures/cgb-colour/manifest.json"
  - "fixtures/magentests/ELIGIBILITY.md"
  - "fixtures/magentests/manifest.json"
  - "include/gabbaboy/gabbaboy.h"
  - "src/accept/digest.c"
  - "src/accept/gbb_accept.h"
  - "src/core/gabbaboy.c"
  - "src/player/colour.c"
  - "src/player/limitations.h"
  - "src/player/main.c"
  - "src/player/session.c"
  - "src/runner/acceptance.c"
  - "tests/CMakeLists.txt"
  - "tests/acceptance/CMakeLists.txt"
  - "tests/acceptance/cases-cgb-colour.txt"
  - "tests/acid2/manifest.json"
  - "tests/cgb_consumer_symbol_coverage.cmake"
  - "tests/check_no_phase11_rows.cmake"
  - "tests/consumers/c/main.c"
  - "tests/consumers/cpp/main.cpp"
  - "tests/data/cgb-priority-truth.inc"
  - "tests/expected-tests.txt"
  - "tests/external/cgb-ppu-dispositions.json"
  - "tests/fuzz_core.c"
  - "tests/measure_core.c"
  - "tests/player/CMakeLists.txt"
  - "tests/player/cgb_smoke.cmake"
  - "tests/player/claims_agree.cmake"
  - "tests/player/test_colour.c"
  - "tests/scripts/gen-cgb-priority-truth.py"
  - "tests/scripts/reproduce-cgb-colour.sh"
  - "tests/scripts/run-acid2-local.py"
  - "tests/scripts/test-reproduce-cgb-colour.sh"
  - "tests/scripts/verify-cgb-apu-dispositions.py"
  - "tests/scripts/verify-cgb-hdma-dispositions.py"
  - "tests/scripts/verify-cgb-speed-dispositions.py"
  - "tests/scripts/verify-dmg-baseline.sh"
  - "tests/scripts/verify-external-dispositions.py"
  - "tests/scripts/verify-summary-coverage.py"
  - "tests/scripts/verify-uat-closure.py"
  - "tests/scripts/verify-v02-consumers.py"
  - "tests/test_acceptance_digest.c"
  - "tests/test_cgb_colour.c"
  - "tests/test_cgb_colour_internal.c"
  - "tests/test_magentests.c"
covered_digest: "v3:sha256:8f8da66a088c24c242c91c82165d720dde1cd4a81ad96f80a579835990050a2d"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 3/3
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 11: CGB Colour Rendering and Player Colour Verification Report

**Phase Goal:** CGB software renders in colour through a new RGB555 frame call, DMG software on the CGB profile uses an original documented compatibility palette, and the player presents either model.
**Status:** passed. **Scope:** 3 roadmap criteria plus all 109 plan-specific assertions, 35 prohibitions, 47 artifact references (35 unique paths) and 31 links across all 15 plans. All three requirements remain satisfied. Separate roadmap and plan rows preserve the detailed contract rather than concealing it behind three headings.
**Re-verification:** Refresh of the previous passed report; expanded contract audit, not a new implementation run or phase completion transition.

## Evidence scope and historical interpretation

Current unchanged source snapshot: `e444dd2320acf0e4e0d83fb89009311edcaa5e13`. The orchestrator configured and rebuilt before the fresh full regression: **1,144/1,144**, zero skips, **486.68 s**; rebuilt SDL player **98/98**, zero skips, **21.72 s**. I read both complete result inventories in the local regression/player logs, reconciled named coverage references, inspected implementation and test assertions, and independently reran the focused checks below. No source/test/doc delta from that source snapshot was present. The persistent receipt is [11-REFRESH-GATES.md](11-REFRESH-GATES.md); transient logs are `/tmp/gabbaboy-phase11-regression.log` and `/tmp/gabbaboy-phase11-player-all.log`.

Historical assertions (no Phase12 tree, routes, deferred FF55/double speed/HDMA, excluded external assets, plan-specific lack of production edits) are evaluated from their recorded bounded task revisions and **immutable boundary `4811033`**, never live HEAD absence/routes/ancestry. Each of the 15 before→after commit windows resolves and is ordered within its own window. Pre-squash task commits are not assumed ancestors of the squash history or boundary. Plans01/05 have byte-identical core source across their own windows; plan14's core delta changes MODEL comments only. Pre-phase and boundary DMG composition/copy bodies agree after comment/whitespace normalization. Current implementation of later phases does not retroactively falsify Phase11's stop or constitute Phase11 evidence for those later features.

D-20 is an adopted applicability clarification, not hidden AGE colour coverage: AGE at `1f5bc10e` has no CGB colour/attribute/priority ROM. Roadmap criterion1 relies on the independent priority oracle, original RGBDS fixtures and the three admitted MagenTests ROMs. Boundary AGE timing rows were expected-unsupported; Phase14 has since replaced these with exact pinned expected failures. Mealybug remains model-inapplicable for CGB-E. Neither set supplies Phase11 colour passes.

## Goal Achievement

### Roadmap observable truths

| ID | Truth | Status | Evidence |
| --- | --- | --- | --- |
| R1 | CGB attributes, BG/OBJ CRAM auto-increment and mode-3 lockout, CGB priority and RGB555 output work; exhaustive oracle and original/MagenTests fixtures check them; DMG shade output stays byte-identical. | VERIFIED | P01–03,P05–11,P14 below; 6,144-row direct path and 64 complete-frame sample; shade-flip, bank, priority, lockout and copy-time-resolve controls. D-20 explicitly limits AGE applicability. |
| R2 | DMG software on the CGB profile uses a fixed original documented compatibility palette a host can override; no boot-ROM palette table ships. | VERIFIED | P04/P06/P08; independent authored ramp, separate per-instance configuration, reject-without-mutation and future-frame tests, documentation mirror and mutated-doc control. |
| R3 | SDL3 player supports --model auto/dmg/cgb, colour presentation and automated CGB smoke in native CI. | VERIFIED | P12/P13/P14; current real native smoke plus wrong-colour/wrong-path/ignored-flag controls. .github/workflows/ci.yml invokes player verification; historical hosted receipt remains revision-bound. |

### Plan-specific observable truths

Every numbered plan assertion is retained verbatim below. “VERIFIED (historical)” means its time-bounded delivery/absence assertion is proven at the recorded phase boundary or plan window; ongoing colour behavior also has current tests. Evidence group Pxx below identifies concrete implementation, behavioral tests and negative controls for the row.

| ID | Plan truth | Status | Evidence |
| --- | --- | --- | --- |
| P01.1 | D-35 stage 1 / D-25: before any colour code lands, a white-box DMG shade-identity pin exists: cgb_dmg_identity_shade_pin runs fixtures/visible-demo/demo.gb, fixtures/libbet/libbet.gb and fixtures/tracer/tracer.gb on GBB_PROFILE_DMG_CPU_B for a fixed frame count and compares an FNV-1a 64 digest of frame_completed with constants recorded from the pre-phase core (regression pin, not hardware evidence) | VERIFIED | P01 |
| P01.2 | D-25: the configure-time colour mutant harness gbb_colour_mutant (exactly-once anchor, test source and cases as parameters) exists and is proven able to fail: a mutant that perturbs the DMG BG shade return makes cgb_dmg_identity_shade_pin exit 1 while its control case exits 0 | VERIFIED | P01 |
| P01.3 | D-03: this plan does not edit src/core/gabbaboy.c; bash tests/scripts/verify-dmg-baseline.sh prints baseline status=pass and measure_core still prints correctness_digest_fnv1a64=4c7a57ff3d50d228 | VERIFIED (historical) / current applicability checked | P01 |
| P01.4 | D-22 (GB-CPU-002): the CGB priority truth table is produced by an independent stdlib Python oracle written from the Pan Docs Tile_Maps/OAM/LCDC text (never from ppu_compose_cgb), committed as tests/data/cgb-priority-truth.inc with exactly 6144 literal rows = 2 modes x 2 LCDC.0 x 2 BG-attr-bit-7 x 4 BG indices x (4 x 2) object A x (4 x 2) object B x 3 X relations | VERIFIED | P01 |
| P01.5 | D-22: cgb_priority_truth_regen regenerates the table and compares bytes; a configure-time copy with one altered row fails it (exit 1); the oracle self-test proves every input column changes the expected output of at least one row (no inert input) | VERIFIED | P01 |
| P01.6 | D-06 / D-07 / D-39: the oracle encodes CGB mode (LCDC.0 = master priority, BG still drawn when clear; OBJ drawn unless LCDC.0 = 1 and (OAM bit 7 or BG attr bit 7) and BG index 1-3; object ordering by OAM index, first opaque wins) and compat mode (LCDC.0 = BG enable so BG index becomes 0; BG attr ignored; OAM bit 7 only; ordering by X, lower OAM index on ties) and a hand-written golden subset quoting those rules agrees with the generated rows | VERIFIED | P01 |
| P01.7 | D-16: tests/test_cgb_colour.c exists with a public case pinning gbb_copy_frame = GBB_UNSUPPORTED_PROFILE on the CGB profile in both CGB and compat mode after valid arguments | VERIFIED | P01 |
| P02.1 | D-10: BCPS/OCPS keep bits 0-5 index and bit 7 auto-increment with bit 6 reading 1 (existing IOC_ST(0x40, 0xBF) cells unchanged), always accessible in every PPU mode and stored in compat mode | VERIFIED | P02 |
| P02.2 | D-11: a BCPD/OCPD write stores the byte at index & 0x3F when allowed; whenever bit 7 is set the index register becomes 0x80 \| ((index + 1) & 0x3F) even if the write was blocked; a read returns the byte or $FF when blocked and never increments; all 8 bits of each byte are stored (bit 15 of a colour word kept as written) | VERIFIED | P02 |
| P02.3 | D-12: cpu_cram_access_allowed is a separate function next to cpu_vram_access_allowed returning true when the LCD is off or ppu_mode != 3, carrying its own MODEL: UNKNOWN research:14 gate row; SameBoy's edge offsets and the black-pixel quirk are not modelled | VERIFIED | P02 |
| P02.4 | D-13: in compat mode BCPD/OCPD read $FF and writes are ignored with no index increment (compat cells stay CONST_FF exactly as Phase 10 set them) | VERIFIED | P02 |
| P02.5 | D-08: OPRI in CGB mode stores bit 0 and reads $FE \| bit0, and a write changes no other instance state; in compat mode OPRI reads $FF and ignores writes; the row provenance is the SameBoy oracle with Pan Docs cited and the behaviour tagged UNKNOWN | VERIFIED | P02 |
| P02.6 | D-14: post_boot[] gains bg_cram (CGB $7FFF PAN_DOCS), obj_cram (CGB $7FFF POLICY) and opri (CGB 0 POLICY) rows; the compat CRAM column is $7FFF POLICY with reason 'the compat renderer never reads CRAM and the data ports read $FF in compat mode; deterministic fill only' (RESEARCH Correction 6, Open Question 1); docs/cgb-profile.md mirrors them and cgb_tables_postboot passes | VERIFIED | P02 |
| P02.7 | D-40: VRAM bank 1 is all zero after every reset and ROM load on the CGB profile (PB_RAM_FILL policy, pinned by cgb_postboot_vram1_zero), and docs/cgb-profile.md names this POLICY before any attribute test relies on it | VERIFIED | P02 |
| P02.8 | D-31: the three DEFERRED(11) CGB cells (FF69, FF6B, FF6C) flip in the same plan as their storage: io_visibility[], io_read_cgb/io_write_cgb, test_cgb_tables render strings, docs/cgb-profile.md io rows and prose, and the independent expectations in tests/test_cgb_visibility.c all change together; the DMG and compat cells of those rows are byte-for-byte unchanged | VERIFIED | P02 |
| P02.9 | D-32: every new function carries a MODEL: tag and every new model-differing branch a docs/model-gates.md row; ctest -R '^model_gates' passes | VERIFIED | P02 |
| P02.10 | Negative controls: configure-time mutants (no increment on a blocked write; increment on read; lockout predicate always allowing; lockout ignoring LCD off) each make a palette_cram_ case exit 1 | VERIFIED | P02 |
| P03.1 | D-01: RGB555 is resolved per dot in ppu_transfer_dot against live CRAM at the point where the DMG path calls ppu_pixel_shade; there is no copy-time resolve and no tuple-carrying FIFO | VERIFIED | P03 |
| P03.2 | D-02: gbb_instance gains uint16_t rgb_working[GBB_FRAME_PIXELS] and rgb_completed[GBB_FRAME_PIXELS]; in CGB mode only rgb_working is written per dot and frame_working stays all zero (the compat-mode branch keeps its existing shade statement until plan 11-04 routes it to rgb_working); on the DMG profile only frame_working is written and rgb_* stay all zero; LCD off fills rgb_working with 0x7FFF and leaves rgb_completed; frame completion copies rgb_working to rgb_completed sharing frame_generation and frame_completion_half_dots; reset zero-fills both RGB buffers | VERIFIED | P03 |
| P03.3 | D-03 / D-04: the DMG functions ppu_tile_color, ppu_background_color, ppu_object_color and ppu_pixel_shade keep their bodies (tag edits only); the colour path is new siblings dispatched by one per-dot branch (DMG profile, then exec_mode == GBB_MODE_CGB, else compat, which plan 11-04 fills) with no function pointer | VERIFIED | P03 |
| P03.4 | D-05 / D-36: CGB-mode BG and window read the tile index from vram[0] and the attribute from vram[1] at the same map address through a bank-explicit accessor; palette bits 0-2, tile bank bit 3, X flip bit 5, Y flip bit 6, BG priority bit 7, bit 4 ignored; OBJ tile bank is OAM bit 3 and palette bits 0-2; rendering never reads VBK (vram_bank); the colour path reads only PPU state, never CPU timing | VERIFIED | P03 |
| P03.5 | D-06: in CGB mode LCDC.0 clear still draws BG and window (window gating uses LCDC.5 alone in ppu_window_should_start and the CGB visibility helper, RESEARCH Correction 5) and objects always win; the DMG background = 0 behaviour runs only under DMG semantics | VERIFIED | P03 |
| P03.6 | D-07 / D-03: ppu_compose_cgb(lcdc, bg_index, bg_attr, obj_opaque, obj_attr) is a pure function: OBJ colour 0 transparent; OBJ wins unless LCDC.0 = 1 and (OAM bit 7 or BG attr bit 7) and BG index 1-3 | VERIFIED | P03 |
| P03.7 | D-08: object ordering is the execution-mode latch: CGB mode takes the first opaque object in ascending OAM index (compat-mode X order is plan 11-04); OPRI is never read by the renderer | VERIFIED | P03 |
| P03.8 | D-09 / D-38: window tiles use the same attribute fetch as BG with the window map and window line counter unchanged; CGB mode-3 timing stays the DMG model (UNKNOWN), the LCDC.0-clear window-start change is recorded in its gate row | VERIFIED | P03 |
| P03.9 | Bit 15 of a CRAM colour word is masked at resolve time (RESEARCH Correction 10): a guest $FFFF renders as 0x7FFF | VERIFIED | P03 |
| P03.10 | D-25: a configure-time mutant whose colour path also writes frame_working fails cgb_rgb_store_shade_untouched; verify-dmg-baseline.sh and cgb_dmg_identity_shade_pin pass at every task | VERIFIED | P03 |
| P03.11 | D-32: the research:11 rows GATE-43, GATE-45 and GATE-46 are resolved (DMG-semantics functions with a basis; new CGB siblings with CGB_ONLY rows), GATE-28 is split (bit-0 meaning resolved by the siblings, LCD on/off timing re-tagged research:14), and every new function and branch has a MODEL: tag and row | VERIFIED | P03 |
| P04.1 | D-01 / D-02: in compat mode on the CGB profile the per-dot dispatch writes rgb_working[at] = ppu_pixel_compat(m, fetched_slot) and never frame_working; cgb_rgb_store_shade_untouched renders a compat ROM ($143 = $00) and requires frame_working and frame_completed all zero | VERIFIED | P04 |
| P04.2 | D-39 / D-17: compat mode uses DMG semantics (BG attr treated as 0 with no vram[1] read, OBJ0/OBJ1 by OAM bit 4, OAM bits 0-3 ignored, LCDC.0 = BG enable, BGP/OBP0/OBP1 select the shade) and resolves the colour through ppu_compat_resolve(m, set, shade) from instance configuration compat_rgb555[3][4], separate from ppu_pixel_shade, which keeps its body | VERIFIED | P04 |
| P04.3 | D-08: compat-mode object ordering reuses ppu_object_color (smaller X wins, lower OAM index on ties) | VERIFIED | P04 |
| P04.4 | D-18: the default compat palette is one table compat_default_rgb555 of the documented ramp ($639F, $4275, $254B, $0421 for BG, OBJ0 and OBJ1), copied into compat_rgb555 in gbb_create, never in reset_state, so it survives reset and ROM load; its comment states the rule and that the values were authored here without reference to any third-party, boot-ROM or title-hash table (G4) | VERIFIED | P04 |
| P04.5 | D-17: a change to compat_rgb555 affects pixels resolved after it and never alters rgb_completed until the next frame completion | VERIFIED | P04 |
| P04.6 | D-25 / D-32: the compat functions and the compat dispatch branch carry MODEL: tags and docs/model-gates.md rows; verify-dmg-baseline.sh and cgb_dmg_identity_shade_pin pass at every task | VERIFIED | P04 |
| P05.1 | D-22: cgb_priority_truth_table drives all 6144 rows of tests/data/cgb-priority-truth.inc through the real per-pixel colour path (ppu_pixel_cgb in CGB mode, ppu_pixel_compat in compat mode) on instances whose VRAM, attributes, selected objects, CRAM and compat palette are set per row, decodes the output RGB555 back to (layer, colour index) from distinct palette colours, and requires every row to match; it asserts it checked exactly GBB_CGB_PRIORITY_TRUTH_ROWS rows | VERIFIED | P05 |
| P05.2 | D-22: cgb_priority_truth_frames renders a deterministic sample of at least 64 rows through whole frames (real OAM, ppu_scan_object, dispatch, rgb_completed) and requires the sampled pixel to match its row, so the table is not only checked below the dispatch | VERIFIED | P05 |
| P05.3 | D-06 / D-07: per-input configure-time mutants of the CGB composer (BG attr bit 7 ignored, OAM bit 7 ignored, LCDC.0 inverted, the BG-index-0 rule dropped) each make cgb_priority_truth_table exit 1 | VERIFIED | P05 |
| P05.4 | D-08: a mutant that orders CGB-mode objects by X fails the table; cgb_priority_opri_no_effect writes OPRI = 1 through write8 in CGB mode and the full table still matches; a mutant that makes OPRI select X order fails that case | VERIFIED | P05 |
| P05.5 | D-39: mutants of the compat renderer (LCDC.0 ignored as BG enable; objects resolved through the BG palette set) each fail the compat rows of the table | VERIFIED | P05 |
| P05.6 | D-05: attribute mutants (tile bank ignored, X/Y flip bits swapped, bank taken from vram_bank instead of the attribute) each fail a cgb_attr_ case | VERIFIED | P05 |
| P05.7 | D-25: no core source is edited by this plan; verify-dmg-baseline.sh passes | VERIFIED (historical) / current applicability checked | P05 |
| P06.1 | D-15: gbb_error gbb_copy_frame_rgb555(const gbb_instance *instance, uint16_t *pixels, size_t capacity_bytes, size_t pitch_bytes, gbb_frame_info *out_info) is declared append-only; before any profile check it returns GBB_INVALID_ARGUMENT for a NULL instance/pixels/out_info, a pixels pointer that is not 2-byte aligned, an odd pitch, a pitch below 320, a pitch whose 143 * pitch + 320 overflows, a capacity below 143 * pitch_bytes + 320, or a destination overlapping out_info; then GBB_UNSUPPORTED_PROFILE on the DMG profile; then GBB_FRAME_NOT_READY when no frame has completed; otherwise it copies 160 native-endian uint16_t R \| G << 5 \| B << 10 values per row with bit 15 clear, never allocates, and writes nothing on any error | VERIFIED | P06 |
| P06.2 | D-15 / D-02: the call serves the CGB profile in CGB mode and compat mode; after gbb_reset it returns GBB_FRAME_NOT_READY; while the LCD is off it keeps returning the last completed frame and the generation does not advance | VERIFIED | P06 |
| P06.3 | D-16: gbb_copy_frame keeps GBB_UNSUPPORTED_PROFILE on the whole CGB profile (GATE-57 unchanged); the header comments that said 'no colour output yet' now say shades cannot express the BG/OBJ0/OBJ1 split and point to gbb_copy_frame_rgb555 | VERIFIED | P06 |
| P06.4 | D-32: a CGB_ONLY gate (GUARD=model_is_cgb) covers gbb_copy_frame_rgb555 on the DMG profile, symmetric with GATE-57 | VERIFIED | P06 |
| P06.5 | D-17a: typedef struct gbb_compat_palette { uint32_t struct_size; uint16_t bg[4], obj0[4], obj1[4]; }, #define GBB_COMPAT_PALETTE_SIZE_V1 28u static-asserted against sizeof; gbb_set_compat_palette(instance, palette) validates the whole struct before mutating (NULL instance -> GBB_INVALID_ARGUMENT; struct_size below V1 -> GBB_INVALID_ARGUMENT; any entry with bit 15 set -> GBB_INVALID_ARGUMENT, rejected not masked; larger struct_size accepted, extra bytes ignored; NULL palette restores the default); gbb_get_compat_palette returns GBB_INVALID_ARGUMENT for a NULL instance, a NULL out, or out->struct_size below GBB_COMPAT_PALETTE_SIZE_V1, and writes nothing on any of those errors (struct_size included); on success it writes field by field within out->struct_size and sets struct_size to the 28 bytes written; both functions are accepted on both profiles; no new error codes | VERIFIED | P06 |
| P06.6 | D-17: a set takes effect for pixels resolved after the call and never recolours an already completed frame; compat CRAM is never rewritten by the host; the setting survives gbb_reset and gbb_load_rom | VERIFIED | P06 |
| P06.7 | D-18: docs/cgb-profile.md lists the rule and the 12 default RGB555 values between cgb-compat-palette markers with the note that they were authored here without reference to a third-party table; cgb_tables_compat_palette compares the doc block with compat_default_rgb555 and a mutated-doc copy is rejected | VERIFIED | P06 |
| P06.8 | D-19 / D-41: the header and docs/native-integration.md state the core applies no colour correction (hosts expand each channel with (c << 3) \| (c >> 2)) and that gbb_frame_info is unchanged and shared by both copy calls | VERIFIED | P06 |
| P06.9 | D-42: header comments, docs/native-integration.md (new RGB555 and compat-palette section inside the CGB scope, contract phrases added), docs/cgb-profile.md, docs/support/unreleased.md and the installed C and C++ consumers (calling every new symbol) change in this plan; cgb_native_guide_contract and installed_consumer_* pass; no existing struct changes layout | VERIFIED | P06 |
| P06.10 | Negative controls: a skewed-validator mutant (profile check before argument checks) and a mask-bit-15 mutant each make a public case exit 1 | VERIFIED | P06 |
| P07.1 | D-23 / D-01: colour-hblank.gb changes BG colour 0 of palette 0 to a distinct RGB555 value for each of lines 0-143 (line 0 during VBlank, line y + 1 during the HBlank of line y; value table fixed in the source and its formula recorded in the manifest); cgb_colour_hblank_rows requires each of the 144 rows of gbb_copy_frame_rgb555 to be uniform and equal to the manifest value for that row, then pins the frame digest | VERIFIED | P07 |
| P07.2 | D-23 item 4 / D-01: a configure-time mutant that resolves every pixel of a frame against one CRAM state (a function-static snapshot of bg_cram taken once per frame, at the first visible pixel x = 0 of line 0, emulating a copy-time resolve) makes cgb_colour_hblank_rows exit 1 | VERIFIED | P07 |
| P07.3 | D-23: fixtures/cgb-colour/ is an original fixture set (RGBDS 1.0.1, MIT, SHA-256 in manifest.json, same layout and manifest keys as fixtures/cgb-banking/) whose manifest records, per ROM, the exact build recipe (source, -D defines, rgbfix flags) so later plans add ROMs by adding manifest rows; every frame-checked fixture first passes a literal structural predicate from its manifest protocol before its digest pin is compared | VERIFIED | P07 |
| P07.4 | D-15 / D-43: src/accept gains GBB_ACCEPT_RGB555_HEADER "GBB-RGB555LE-v1 160x144\n", gbb_accept_rgb555_digest, gbb_accept_rgb555_digest_bin, gbb_accept_write_ppm_rgb555, gbb_accept_expand5 and gbb_accept_rgb555_distinct; digests serialise explicit little-endian byte pairs; a value above 0x7FFF is rejected with nothing written; the DMG digest functions and GBB_ACCEPT_RGB_HEADER are unchanged (the independent Python vector lands with the runner in plan 11-09) | VERIFIED | P07 |
| P07.5 | Reproduction: tests/scripts/reproduce-cgb-colour.sh rebuilds every ROM listed in fixtures/cgb-colour/manifest.json from its recorded recipe with pinned RGBDS 1.0.1 and prints result=byte-identical roms=N where N is the manifest row count (1 after this plan); fixture-repro.yml runs it and its pin-consistency block includes the new manifest | VERIFIED | P07 |
| P07.6 | D-25: verify-dmg-baseline.sh passes; acceptance_digest_vectors and the DMG frame digests are unchanged | VERIFIED | P07 |
| P08.1 | D-23: original fixtures in fixtures/cgb-colour/ (RGBDS 1.0.1, MIT, new manifest rows with sha256 and recipe) cover each BG attribute bit and OBJ bank/palette (colour-attr.gb), LCDC.0 = 0 with BG still drawn (colour-lcdc0.gb, D-06), CRAM auto-increment, wrap, read-back and blocked-write increment (colour-cram.gb, D-11), the compat BGP/OBP0/OBP1 mapping including a host override (colour-compat.gb, $143 = $00) and LCD off (colour-lcdoff.gb, D-02) | VERIFIED | P08 |
| P08.2 | D-23 item 3 (resolution 4): colour-cram.gb reports results as WRAM markers read with gbb_peek_ram after halt (C000 = $A5 pass / $EE fail plus one byte per cell), not an ld b,b register predicate; a palette-port mutant from plan 11-02 linked into the public driver makes cgb_colour_guest_cram fail | VERIFIED | P08 |
| P08.3 | D-23: every frame-checked fixture first passes a literal structural predicate from its manifest protocol (expected RGB555 values per region written from the fixture design, never from core output) before its digest pin is compared | VERIFIED | P08 |
| P08.4 | D-17 / D-39: palette_compat_mapping shows BGP/OBP0/OBP1 select shades that map through the default compat palette, and after gbb_set_compat_palette the next completed frame uses the override for BG, OBJ0 and OBJ1 separately | VERIFIED | P08 |
| P08.5 | D-02: cgb_colour_lcd_off shows the completed frame retained and generation frozen while the guest keeps the LCD off; the internal driver run of the same ROM sees rgb_working all 0x7FFF | VERIFIED | P08 |
| P08.6 | Reproduction: tests/scripts/reproduce-cgb-colour.sh (unchanged, manifest-driven from plan 11-07) prints result=byte-identical roms=6 | VERIFIED | P08 |
| P08.7 | D-25: verify-dmg-baseline.sh passes | VERIFIED | P08 |
| P09.1 | D-43 / runner flags: the runner has both --model and --profile (src/runner/main.c:441-442); --profile cgb maps through gbb_runner_model_for_option to the model token cgb-cpu-e and must agree with any --model given (main.c:460-466), so D-43's '--profile cgb' and '--model cgb-cpu-e' select the same run; the CGB cases here are registered with --model cgb-cpu-e (the existing acceptance convention) and acceptance_cgb_colour_hblank_profile_flag proves the --profile cgb spelling gives the identical pass line | VERIFIED | P09 |
| P09.2 | D-43: an acceptance frame-digest@t= case run with --model cgb-cpu-e captures through gbb_copy_frame_rgb555, digests little-endian RGB555 bytes with gbb_accept_rgb555_digest under the GBB-RGB555LE-v1 label, and prints its verdict and observed digest under keys distinct from the DMG ones (frame555 / observed555), so a CGB frame digest can never be confused with an RGB888 one | VERIFIED | P09 |
| P09.3 | D-43: the DMG digest format (gbb_accept_rgb_digest*, GBB_ACCEPT_RGB_HEADER, src/runner/acceptance.c DMG lines) is byte-identical: verify-dmg-baseline.sh passes and no acceptance.* key is added to the frozen DMG ledger | VERIFIED | P09 |
| P09.4 | D-43 controls: the same CGB case on --model dmg-cpu-b is excluded (status=excluded), a flipped reference digest fails with reason=frame-mismatch and writes an RGB555-expanded P6 PPM to --failure-dir, and a CGB progress-predicate run reports an explicit reason instead of silently observing no frames | VERIFIED | P09 |
| P09.5 | D-15 / D-43: an independent Python vector (rgb-digest-vector.py --rgb555) matches gbb_accept_rgb555_digest on a synthetic frame; 0x8000 is rejected with nothing written; padding bytes beyond 320 per row do not change the digest; gbb_accept_expand5 equals (c << 3) \| (c >> 2) | VERIFIED | P09 |
| P10.1 | D-20: AGE test ROMs at 1f5bc10e have no CGB colour, attribute or priority ROM (only m3-bg-lcdc and m3-bg-scx, which are expected-unsupported for mode-3 pixel timing per D-09); ROADMAP success criterion 1's 'AGE/MagenTests' is met by MagenTests plus the plans 11-07 and 11-08 original fixtures plus the plan 11-01/11-05 truth table (the AGE m3-bg-* expected-unsupported records themselves are plan 11-11), and fixtures/magentests/ELIGIBILITY.md and the SUMMARY state this deviation explicitly rather than imply AGE coverage | VERIFIED | P10 |
| P10.2 | D-21: bg_oam_priority.gbc, oam_internal_priority.gbc and ppu_disabled_state.gbc from MagenTests 0.5.0 (3f9c090f) are vendored with SHA-256 1b2132b3...b84c, f54fb636...7fe7 and 4808fe83...eea6 (re-verified from a fresh download before commit), MIT notice retained, manifest rows with source_dir, rgbfix_options and cgb_flag, and ELIGIBILITY labels 'CGB hardware photo, revision E unattested', 'SameBoy differential, not hardware' and 'author-attested' respectively; key0_lock_after_boot and hblank_vram_dma are not vendored | VERIFIED | P10 |
| P10.3 | D-21: each ROM runs a fixed 20 frames on GBB_PROFILE_CGB_CPU_E, the last two completed frames are byte-identical, and a literal RGB555 structural predicate must pass before its digest pin is accepted: ppu_disabled_state all 23040 pixels 0x03E0, evaluated on LCD-on frames (see the capture-point truth); oam_internal_priority: every non-0x7FFF pixel lies inside one of two 12x6 bounding boxes (x 33-44 x y 25-30, and x 33-44 x y 45-50; 144 pixels in total), a fixed subset of those 144 pixels is opaque (84 per the RESEARCH simulation: four triangle objects drawn from tile rows 1-6 and opaque columns 1-6, two per box) and each opaque pixel is green 0x03E0 or red 0x001F at the position the pinned tile data gives it, the other 60 box pixels and every pixel outside the boxes are 0x7FFF; the exact per-pixel mask and the green/red counts are derived from the pinned MagenTests 0.5.0 source (src/oam_internal_priority/graphics_data.asm and OAM setup at 3f9c090f) and recorded with that derivation in fixtures/magentests/ELIGIBILITY.md before they are typed into the test (if the derivation disagrees with the RESEARCH count of 84, the derived mask wins and the disagreement is recorded); bg_oam_priority eight 8x8 cells at x 32-39, y 16k to 16k + 7 (cells 0, 2, 3 rows 0-3 0x03E0 and rows 4-7 0x7C00; cells 1, 4, 5, 6, 7 all 0x03E0), zero 0x001F pixels, all others 0x7FFF | VERIFIED | P10 |
| P10.4 | D-21 negative controls through the colour mutant harness: an LCD-off path that does not enter mode 0 turns ppu_disabled_state red; object colours resolved from BG CRAM break oam_internal_priority (RESEARCH Correction 4: its object pairs never share an opaque pixel, so X ordering cannot be the control there; ordering stays proved by the truth table); an inverted LCDC.0 composer breaks bg_oam_priority | VERIFIED | P10 |
| P10.5 | D-21 capture point: ppu_disabled_state is checked on frames completed with the LCD on; gbb_copy_frame_rgb555 returns rgb_completed, which only advances at an LCD-on frame completion (D-02 fills only rgb_working with 0x7FFF while the LCD is off), and the test requires frame_info.generation to advance between the two captured frames, so a retained frame or an LCD-off white (0x7FFF) frame fails the predicate | VERIFIED | P10 |
| P10.6 | Resolution 6 / D-09: if bg_oam_priority fails its predicate, the core is investigated first and any defect is fixed (with its own test); an expected-unsupported record (named reason, asserted symptom, no digest) is allowed only when the failure is attributable to the CGB mode-3 timing that D-09 defers; any other unexplained failure stops the plan and is reported, never recorded as expected-unsupported; a digest is never pinned for an output that failed its predicate | VERIFIED | P10 |
| P10.7 | tests/scripts/reproduce-magentests.sh rebuilds every vendored ROM from a per-ROM table (name, source dir, rgbfix options) with RGBDS 0.6.1 at the pinned commit and its self-check counts the manifest rows instead of requiring exactly three; magentests_not_installed covers the new digests | VERIFIED | P10 |
| P10.8 | The existing mbc_oob_sram tests stay on the DMG profile and unchanged; verify-dmg-baseline.sh passes | VERIFIED | P10 |
| P11.1 | D-09 / D-20: tests/external/cgb-ppu-dispositions.json records, for AGE test ROMs at 1f5bc10e2cb60b86c19f8d0287ff78f410c4f639, exactly six cases - m3-bg-lcdc and m3-bg-scx, each in the cgbBCE, ds-cgbBCE and nocgb-ncmBCE variants (one row per upstream expected image src/m3-bg-{lcdc,scx}/m3-bg-{lcdc,scx}-{cgbBCE,ds-cgbBCE,nocgb-ncmBCE}.png) - each with disposition expected-unsupported and reason mode-3-pixel-timing, decision D-09, owner phase 14, vendored false | VERIFIED (historical) / current applicability checked | P11 |
| P11.2 | D-09: the same record lists every Mealybug Tearoom Tests ppu m3_* case at 70e88fb90b59d19dfbb9c3ac36c64105202bb1f4 (30 sources src/ppu/m3_*.asm at that pin, enumerated from the pinned tree, with the upstream count stored beside the rows) with disposition unsupported-model, reason naming that the upstream expected images cover CGB-C/D steppings only and not CGB-E, decision D-09, vendored false, rights gate G1 noted | VERIFIED (historical) / current applicability checked | P11 |
| P11.3 | D-09: cgb_external_dispositions runs tests/scripts/verify-external-dispositions.py, which requires the AGE set to equal the six names with expected-unsupported/mode-3-pixel-timing, every Mealybug row to match ^m3_ with unsupported-model and the row count to equal the stored upstream count, docs/cgb-profile.md's cgb-external-dispositions block to mirror the JSON rows, and no tracked file under fixtures/ to carry an AGE m3-bg- or Mealybug m3_ ROM or image; it needs no ROM bytes and no network | VERIFIED (historical) / current applicability checked | P11 |
| P11.4 | Negative control: cgb_external_dispositions_mutated runs the verifier on a configure-time copy of the JSON with one AGE reason changed and must exit 1 with 'disposition-mismatch' | VERIFIED (historical) / current applicability checked | P11 |
| P11.5 | D-24: acid2 ROMs add no bytes to the repository or to required CI; tests/scripts/run-acid2-local.py is an optional local runner taking --rom and --reference paths, refusing any ROM or reference PNG whose SHA-256 differs from tests/acid2/manifest.json pins, and comparing the core frame (cgb-acid2 on the CGB profile through the (c << 3) \| (c >> 2) expansion; dmg-acid2 on the DMG profile through the shade map the manifest cites from the upstream README) pixel by pixel | VERIFIED | P11 |
| P11.6 | D-24: required CI runs only acid2 self-tests on synthetic data (a stdlib PNG written by the script, a fake ROM that fails the pin, a deliberate one-pixel mismatch), never an acid2 image | VERIFIED | P11 |
| P12.1 | D-26: gabbaboy-player accepts an optional leading --model auto\|dmg\|cgb (default dmg); auto picks the CGB profile when gbb_probe_rom reports header $143 bit 7, otherwise DMG; dmg always uses the DMG profile and a CGB-only ROM shows the informational note; cgb always uses the CGB profile and a non-CGB ROM runs in compat mode; a PGB header is an error with a message and non-zero exit; a missing or unknown value is a usage error with exit 2 | VERIFIED | P12 |
| P12.2 | D-26 (as amended at planning, three-session-site narrowing) / RESEARCH Correction 2: one select_profile seam (player_session_probe_profile in session.c, reusing read_rom_file and gbb_probe_rom) is used by the three session create sites (create_machine, replace_session_rom, run_script_smoke) and re-probes on every open; the three non-session sites (authored audio guest, identify_rom_with_core, identify_smoke_rom) stay explicit DMG with a comment; a probe failure leaves the running session intact | VERIFIED | P12 |
| P12.3 | D-26: the existing Libbet and DMG player tests (player_smoke, player_session_script_*, continuation and battery smokes) keep their behaviour and digests on the default dmg | VERIFIED | P12 |
| P12.4 | D-27: the CGB branch of update_frame copies with gbb_copy_frame_rgb555 and expands each channel with gbb_accept_expand5 ((c << 3) \| (c >> 2), no colour correction) into the existing RGBA32 streaming texture through src/player/colour.c player_rgb555_frame_to_rgba; the DMG branch of update_frame is unchanged; the profile is taken from gbb_get_info, not from the flag | VERIFIED | P12 |
| P12.5 | D-28: the window title carries DMG, CGB or CGB (DMG-compat) from gbb_get_info mode through the SDL-free player_model_token(), additively so existing title assertions still hold | VERIFIED | P12 |
| P12.6 | D-29: the player has no compat-palette flag; the help text says the compat palette is the core default | VERIFIED | P12 |
| P12.7 | D-30: player_cgb_smoke runs gabbaboy-player --model cgb --smoke-colour fixtures/cgb-colour/colour-attr.gb with SDL_AUDIO_DRIVER=dummy on the existing native player job and asserts the uploaded RGBA buffer SHA-256, a minimum distinct-colour count, spot pixels whose expected RGBA the test computes from the fixture's literal RGB555 values with the expansion formula, and the title token CGB; DMG smoke digests are unchanged; no new workflow, action or GPU | VERIFIED | P12 |
| P12.8 | D-30 negative controls: a player built with an R/B-swapped colour.c and a player built with update_frame forced onto the DMG path each make the smoke check exit non-zero; a session library whose select_profile ignores the flag fails player_cgb_model_select | VERIFIED | P12 |
| P12.9 | Coupling: this plan pins player_cgb_smoke's rgba_sha256 for colour-attr.gb; it depends on plan 11-10 because that plan may fix a core defect in src/core/gabbaboy.c, and the close-out plan 11-14 re-runs bash tests/scripts/verify-phase3-player.sh --build-package at the merged head so a later core change cannot leave a stale pin unnoticed | VERIFIED | P12 |
| P13.1 | D-44 / D-19 / D-29: src/player/limitations.h and its verbatim test, README, --help/F1 help and both preview.yml capability_limits strings say, all within this plan: the player runs DMG and CGB software with --model auto\|dmg\|cgb (default dmg, D-26) and colour presentation on the CGB profile; DMG software on the CGB profile uses the core's fixed original compatibility palette and the player has no palette flag; there is no colour correction (channels expanded with (c << 3) \| (c >> 2)); audio on the CGB profile is the DMG APU model; CGB mode-3 timing, double speed and HDMA are not claimed or implemented; no CGB-E hardware qualification | VERIFIED (historical) / current applicability checked | P13 |
| P13.2 | D-44: player_claims_agree requires every phrase of one list (the D-44 claim phrases, including 'no colour correction', 'DMG APU model' and '--model auto\|dmg\|cgb') in limitations.h, README.md and both preview.yml capability_limits strings (the Linux string keeps saying it has no SDL player), and player_claims_agree_mutated, run on a configure-time README copy with one phrase removed, exits 1 with 'claims-disagree' | VERIFIED (historical) / current applicability checked | P13 |
| P13.3 | D-44: docs/preview.md drops the claim that the preview has no CGB support only where it is now false (CGB colour) and keeps 'no CGB double-speed clock behavior' | VERIFIED (historical) / current applicability checked | P13 |
| P13.4 | The claims match the evidence of plans 11-12 (player smoke, model selection) and 11-10/11-11 (MagenTests labels, AGE/Mealybug dispositions); no claim is added that a test in this phase does not support | VERIFIED (historical) / current applicability checked | P13 |
| P14.1 | D-32 / resolution 3: no MODEL tag or docs/model-gates.md row names research:11; the timing rows GATE-02, 10, 13, 14, 20, 44, 47, 48, 49 and 50 are re-tagged research:14 with a disposition table in docs/model-gates.md (gate, site, reason it is CGB timing or lock-edge work deferred by D-09/D-12), the Release status paragraph no longer says Phase 11 owns open rows, and model_gates_no_phase11_rows fails on a mutated doc copy that still carries one | VERIFIED | P14 |
| P14.2 | D-34: tests/fuzz_core.c gains palette-register sequences on the CGB profile (FF68-FF6C writes with auto-increment wrap, writes during mode 3, CRAM writes interleaved with LCD on/off, compat-mode port writes) and gbb_set_compat_palette inputs (struct_size around 28, bit 15 entries, NULL), with invariants: every gbb_copy_frame_rgb555 pixel has bit 15 clear, a rejected set leaves gbb_get_compat_palette unchanged, the DMG profile's rgb store stays empty; it runs under the phase1-asan preset with ASan/UBSan clean; a seed that breaks the bit-15 invariant in a mask-removed mutant is detected | VERIFIED | P14 |
| P14.3 | D-33 / D-04: an advisory interleaved A/B benchmark of the DMG profile against the Phase 10 head 3012e8f (tracer digest 4c7a57ff3d50d228 on both builds) and a separately recorded CGB colour workload on fixtures/cgb-colour/colour-attr.gb are recorded in 11-BENCH.md/11-BENCH.json with revision, build, hardware class, workload, model, output digest, warm-up, samples and uncertainty; the D-22 trigger (median ratio > 1.05 with lower bound > 1.0) is evaluated; the per-dot model branch is hoisted only if the trigger fires, and then the A/B and the DMG identity checks are re-run and both receipts recorded; no hosted timing gate | VERIFIED (historical) / current applicability checked | P14 |
| P14.4 | D-25: the final DMG identity check passes at the plan head: verify-dmg-baseline.sh baseline status=pass, cgb_dmg_identity_shade_pin, banking_tracer_digest_unchanged, the flat-memory reference (banking_dmg_flat_reference) and the fuzz bank asserts | VERIFIED | P14 |
| P14.5 | D-09 / D-36: docs/cgb-profile.md states CGB mode-3 timing, WX and window-range differences are not claimed, the colour path reads PPU dot time only, the renderer reads VRAM through an explicit bank, and FF55 stays DEFERRED(13) | VERIFIED (historical) / current applicability checked | P14 |
| P14.6 | D-37: every Phase 11 SUMMARY coverage block passes summary_coverage (--since 11); D-069: the phase needs zero human verification items | VERIFIED | P14 |
| P14.7 | D-35: wave order baseline -> palette RAM -> colour path and truth table -> API, fixtures and runner -> player -> close-out was followed (plan dependency chain 11-01 ... 11-15, waves 1-14) | VERIFIED (historical) / current applicability checked | P14 |
| P14.8 | Player coupling (from plan 11-12): after any core change in this plan (including a D-04 hoist) and at the plan head, bash tests/scripts/verify-phase3-player.sh --build-package passes, so player_cgb_smoke's pinned rgba_sha256 is re-checked against the final core | VERIFIED | P14 |
| P15.1 | Durable memory (AGENTS.md): .planning/context/DECISIONS.md gains one row per adopted Phase 11 choice - D-15 (RGB555 ABI), D-17a (compat palette API), D-08 (OPRI no post-boot effect), D-26 (player --model, default dmg, three session sites), D-18 (default compat ramp), D-21 (MagenTests admission and labels), D-24 (acid2 optional-local under G1) and D-09 (CGB mode-3 timing deferred; AGE m3-bg-* expected-unsupported, Mealybug m3_* unsupported-model) - numbered consecutively from the next free ID after the file's current maximum (D-075 when planned, so D-076 onward unless the file has grown), each row giving decision and status, tradeoff and rationale, and evidence (CTest names and files) with a revisit trigger, and citing the Phase 11 CONTEXT ID it adopts | VERIFIED | P15 |
| P15.2 | Durable memory: .planning/research/INDEX.md gains a Phase 11 bullet in the style of the Phase 10 bullet linking 11-RESEARCH.md, docs/cgb-profile.md, docs/native-integration.md, fixtures/cgb-colour/manifest.json, fixtures/magentests/ELIGIBILITY.md, tests/external/cgb-ppu-dispositions.json and 11-BENCH.md, with the evidence-class caveats (original fixtures and truth table are not hardware evidence; MagenTests labels per D-21; AGE has no CGB colour ROM, D-20); every relative link resolves | VERIFIED | P15 |
| P15.3 | Durable memory: .planning/context/LESSONS.md records concrete Phase 11 lessons with cause, evidence, remedy, applicability and verification, sanitized for export | VERIFIED | P15 |
| P15.4 | D-42: the phase COVERAGE.md holds exactly one line 'No external API integration: <reason>' with a reason of at most 200 characters in the Phase 9/10 form, and gsd check api-coverage.verify-pre on the phase directory passes; the repo-level cgb_consumer_symbol_coverage check from plan 11-06 still passes | VERIFIED | P15 |
| P15.5 | Handoff (AGENTS.md): STATE.md and .planning/.continue-here.md name the completed stage (Phase 11 - CGB Colour Rendering and Player Colour, execution), the next step and one copy-paste GSD command derived from the phase artifacts (normally /gsd-verify-work 11 because no 11-VERIFICATION.md exists yet), and the following phase by number and title from ROADMAP.md (Phase 12: CGB Double Speed) with its entry command (/gsd-discuss-phase 12, since no Phase 12 CONTEXT.md exists); Phase 12 is not started and workflow.auto_advance and workflow._auto_chain_active stay false | VERIFIED (historical) / current applicability checked | P15 |

**Score: 112/112 truths verified; 0 present-but-behavior-unverified; 0 overrides.** State-transition truths have behavioral evidence, including blocked-write index advancement, completed-frame retention, palette rejection atomicity, reset/load persistence, future-frame palette effects, session failure retention, and actual RGB555 texture input. No backstop-tagged truth or unresolved judgment-tier prohibition was declared.

### Implementation and behavioral evidence by plan

**P01** — tests/test_cgb_colour_internal.c pins three DMG ROMs; gen-cgb-priority-truth.py independently enumerates 6,144 rows and input sensitivity. cgb_dmg_identity_shade_pin, shade_flip mutant/control, truth_regen/selftest/regen_mutated/table_shape and copy_frame_unsupported passed. Plan window has no core edit; frozen baseline passes.

**P02** — src/core/gabbaboy.c:1409–1435,1473–1508 implements masked indices, lockout and blocked-write increment; reset/post_boot policy is explicit. palette_cram_*, palette_opri_*, cgb_postboot_vram1_zero, cgb_tables_postboot and four palette mutant/control pairs passed.

**P03** — src/core/gabbaboy.c:2759–2874,3026–3068 traces bank-explicit fetch, pure priority, live per-dot CRAM, dual stores and completion. cgb_attr_*, rgb_store_*, cgb_priority_* and colour-writes-shade mutant/control passed; DMG baseline unchanged.

**P04** — src/core/gabbaboy.c:2723–2746 defines authored ramp and separate compat resolver; create initializes configuration and reset does not replace it. cgb_compat_internal_* and palette_compat_effect_next_frame passed; DMG baseline unchanged.

**P05** — tests/test_cgb_colour_internal.c includes literal oracle rows and checks all 6,144 plus 64 complete-frame samples; priority, OPRI and attribute mutants have positive controls and specific failing predicates. Current cgb_priority_truth_table/frames, opri_no_effect and all registered mutants passed. Bounded plan window has no core edit.

**P06** — src/core/gabbaboy.c:3383–3457 validates before writes and copies completed rows; include/gabbaboy/gabbaboy.h defines append-only API. cgb_rgb555_*, palette_compat_api_*, effect_next_frame, skewed-validator/mask-bit15 controls, native-guide contract and consumer-symbol coverage passed. v02_consumer_controls actually builds/runs relocated C/C++ clients.

**P07** — fixtures/cgb-colour/manifest.json pins original source/ROM bytes and recipes; test_cgb_colour.c checks 144 literal row colours before digest. cgb_colour_hblank_rows and frame_resolve mutant/control passed; acceptance_digest_rgb555_vectors passed. Shared label is defined in src/accept/gbb_accept.h and consumed by digest.c. Pinned rebuild remains the historical receipt.

**P08** — Six original fixture/source digest sets match manifest. test_cgb_colour.c applies region/WRAM predicates before pins; colour_attr/lcdc0/guest_cram/lcd_off, palette_compat_mapping and blocked-increment mutant/control passed. LCD-off completion freezes generation. Fixture rebuild receipt is historical; current refusal controls remain green.

**P09** — src/runner/acceptance.c:733–760 selects actual profile, copies RGB555 and serializes explicit LE under distinct frame555/observed555 keys. acceptance_cgb_colour_{hblank,hblank_profile_flag,excluded_dmg,flipped_ppm,progress_refused} and independent acceptance_digest_rgb555_vectors passed; DMG baseline unchanged.

**P10** — MagenTests manifest rights/digests and ELIGIBILITY labels distinguish photo E-unattested, differential and author-attested evidence. test_magentests.c requires advancing identical captures and structural predicates before digest. All four magentests_cgb positive cases and four mutant/control pairs passed; reproduce-magentests.sh --self-check passed. D-20 AGE exclusion preserved.

**P11** — At immutable boundary 4811033, disposition JSON has exactly six AGE expected-unsupported/mode-3-pixel-timing rows and 30 Mealybug unsupported-model rows; no forbidden images are tracked. Current cgb_external_dispositions/mutated pass with Phase14 pinned AGE xfails (not colour passes). Acid2 pin/read/decode synthetic selftests/refusal/malformed controls pass; no rights-qualified ROM run claimed.

**P12** — src/player/main.c selects default DMG and routes create/open/script sessions through player_session_probe_profile; session.c probes before replacing a session. update_frame_cgb copies completed RGB555, converts via colour.c and uploads RGBA; mode token uses gbb_get_info. Rebuilt player suite passed 98/98 including model select/PGB/missing-file, smoke, 32,768-value expansion, title and wrong-path/channel/ignored-model controls.

**P13** — At boundary 4811033, limits matched delivered colour and excluded later features. Current claims_agree.cmake deliberately incorporates Phase12/13 scope; player_claims_agree and its removed-phrase negative passed. Current limitations preserve no colour correction, core compat palette, DMG APU, unclaimed mode-3 accuracy and physical UNKNOWN/POLICY; Linux retains no SDL player.

**P14** — Model gate scan and mutated-doc rejection pass; palette fuzz regression and no-mask mutant/control pass. 11-BENCH.md/json record original revisions, interleaved A/B samples and uncertainty; three medians 99.22/98.49/100.23 do not fire D-22, with no performance hoist in bounded core diff (comments only). Benchmark shape/wrong-digest controls pass. Historical FF55 deferral read at 4811033; Phase13 later implemented HDMA. summary_coverage/selftest pass; final rebuilt player suite passes.

**P15** — DECISIONS D-076..083 and Phase11 INDEX links are present and resolve; LESSONS has cause/evidence/remedy/applicability/verification. COVERAGE declares no external integration and api-coverage.verify-pre 11 passes. Immutable 4811033 STATE/continuation/config/tree establish /gsd-verify-work 11, following Phase12 title, false auto flags and no Phase12 tree; six weakened boundary controls rejected. Live handoff is deliberately outside this historical assertion.

### Prohibitions

All 35 legacy prohibition statements lack a separate verification-tier field; they are evaluated here by deterministic source/history/data and exercised contract controls, not silently treated as accepted human judgment. Time-bounded feature/asset exclusions retain their boundary scope.

| ID | Prohibition | Status | Enforcement / evidence |
| --- | --- | --- | --- |
| P01.N1 | The truth-table expectations are never computed by calling or copying ppu_compose_cgb or any core function | VERIFIED | P01 evidence above; bounded task/boundary source and records; current companion controls and applicability checked. |
| P01.N2 | No production core source changes in this plan; mutants live only in build-tree copies | VERIFIED | P01 evidence above; bounded task/boundary source and records; current companion controls and applicability checked. |
| P02.N1 | The DMG and compat cells of FF68-FF6C are not changed (D-31, D-13) | VERIFIED | P02 evidence above; current companion controls and applicability checked. |
| P02.N2 | No uninitialised CRAM or VRAM value is asserted against another emulator (D-40) | VERIFIED | P02 evidence above; current companion controls and applicability checked. |
| P02.N3 | OPRI writes never change object ordering after boot (D-08) | VERIFIED | P02 evidence above; current companion controls and applicability checked. |
| P03.N1 | gbb_copy_frame output for the DMG profile is not changed (D-02, D-25) | VERIFIED | P03 evidence above; current companion controls and applicability checked. |
| P03.N2 | The renderer never reads vram_bank or opri | VERIFIED | P03 evidence above; current companion controls and applicability checked. |
| P04.N1 | No Nintendo boot-ROM palette table and no title-hash palette ships (CGB-05, G4) | VERIFIED | P04 evidence above; current companion controls and applicability checked. |
| P04.N2 | ppu_pixel_shade, ppu_background_color and ppu_object_color keep their bodies; gbb_copy_frame output for the DMG profile is not changed (D-03, D-25) | VERIFIED | P04 evidence above; current companion controls and applicability checked. |
| P04.N3 | The compat renderer never reads vram[1] (D-39) | VERIFIED | P04 evidence above; current companion controls and applicability checked. |
| P05.N1 | Expected values come only from the committed oracle rows and the hand-written golden subset, never from a core function (GB-CPU-002) | VERIFIED | P05 evidence above; bounded task/boundary source and records; current companion controls and applicability checked. |
| P05.N2 | No production core source change in this plan | VERIFIED | P05 evidence above; bounded task/boundary source and records; current companion controls and applicability checked. |
| P06.N1 | gbb_copy_frame output for the DMG profile is not changed and its validation code is not refactored (D-03, D-16) | VERIFIED | P06 evidence above; current companion controls and applicability checked. |
| P06.N2 | No boot-ROM palette table, title-hash palette or peer-emulator palette values ship (CGB-05, G4) | VERIFIED | P06 evidence above; current companion controls and applicability checked. |
| P06.N3 | No existing public struct, enum value or function signature changes (D-42) | VERIFIED | P06 evidence above; current companion controls and applicability checked. |
| P07.N1 | No third-party ROM, boot ROM or commercial image is added under fixtures/cgb-colour/; every byte is assembled from the committed original sources | VERIFIED | P07 evidence above; current companion controls and applicability checked. |
| P07.N2 | The DMG RGB888 digest format and header string are unchanged (D-43) | VERIFIED | P07 evidence above; current companion controls and applicability checked. |
| P08.N1 | No third-party ROM, boot ROM or commercial image is added under fixtures/cgb-colour/; every byte is assembled from the committed original sources | VERIFIED | P08 evidence above; current companion controls and applicability checked. |
| P08.N2 | acid2 ROMs are not vendored (G1, D-24) | VERIFIED | P08 evidence above; current companion controls and applicability checked. |
| P09.N1 | The DMG RGB888 digest format, header label and existing acceptance output keys are unchanged (D-43) | VERIFIED | P09 evidence above; current companion controls and applicability checked. |
| P10.N1 | No acid2, key0_lock_after_boot or hblank_vram_dma bytes are added | VERIFIED | P10 evidence above; current companion controls and applicability checked. |
| P10.N2 | No MagenTests ROM is described as CGB-E hardware evidence | VERIFIED | P10 evidence above; current companion controls and applicability checked. |
| P10.N3 | No digest is pinned for an output that failed its structural predicate | VERIFIED | P10 evidence above; current companion controls and applicability checked. |
| P11.N1 | No AGE, Mealybug or acid2 ROM or reference image is vendored or run by required CI (D-09, D-24, G1) | VERIFIED | P11 evidence above; current companion controls and applicability checked. |
| P11.N2 | No AGE m3-bg-* or Mealybug m3_* case is recorded as a pass or counted as CGB-E evidence (D-09, D-20) | VERIFIED | P11 evidence above; current companion controls and applicability checked. |
| P12.N1 | The DMG branch of update_frame and the DMG smoke digests are not changed | VERIFIED | P12 evidence above; current companion controls and applicability checked. |
| P12.N2 | No player compat-palette flag and no colour correction (D-29, D-19) | VERIFIED | P12 evidence above; current companion controls and applicability checked. |
| P12.N3 | The default model is not auto (D-26) | VERIFIED | P12 evidence above; current companion controls and applicability checked. |
| P13.N1 | No claim of colour correction, a palette flag, CGB mode-3 accuracy, double speed, HDMA or CGB-E hardware qualification (D-19, D-29, D-09, D-44) | VERIFIED | P13 evidence above; bounded task/boundary source and records; current companion controls and applicability checked. |
| P13.N2 | The Linux capability string does not gain an SDL player claim | VERIFIED | P13 evidence above; bounded task/boundary source and records; current companion controls and applicability checked. |
| P14.N1 | No new core feature lands in this plan beyond a benchmark-justified hoist (D-04) | VERIFIED | P14 evidence above; current companion controls and applicability checked. |
| P14.N2 | No timing assertion is added to hosted CI (D-33) | VERIFIED | P14 evidence above; current companion controls and applicability checked. |
| P14.N3 | No personal home path, email or machine identifier appears in receipts or docs | VERIFIED | P14 evidence above; current companion controls and applicability checked. |
| P15.N1 | Phase 12 is not started: no Phase 12 directory, CONTEXT.md or plan is created, and no auto-advance flag is set (AGENTS.md phase stop) | VERIFIED | P15 evidence above; bounded task/boundary source and records; current companion controls and applicability checked. |
| P15.N2 | No personal home path, email or machine identifier enters any of these files | VERIFIED | P15 evidence above; bounded task/boundary source and records; current companion controls and applicability checked. |

No automatic approval or new risk acceptance is inferred from these results. Authenticity/rights evidence is the committed provenance, licence, pinned source and digest record, not an invented hardware attestation.

### Required artifacts

The runtime artifact checker evaluated every plan: **45/47 literal checks pass**. Its two negative results are explicitly reconciled: P07 searches for the literal digest label in digest.c, but the implementation consumes the shared header macro; P11 searches for the old AGE reason, now superseded by Phase14 xfails (the exact original record exists at 4811033). Neither is a missing/stub implementation. Manual substantive/wiring checks yield **47/47 references verified**, including the historical continuation artifact.

| Artifact | Plan references | Exists / substantive / wired evidence | Status |
| --- | --- | --- | --- |
| `tests/test_cgb_colour_internal.c` | P01, P02, P03, P04, P05 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `tests/test_cgb_colour.c` | P01, P07, P08 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `tests/scripts/gen-cgb-priority-truth.py` | P01 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `tests/data/cgb-priority-truth.inc` | P01 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `tests/CMakeLists.txt` | P01, P05 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `src/core/gabbaboy.c` | P02, P03, P04, P06 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `docs/cgb-profile.md` | P02, P06 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `include/gabbaboy/gabbaboy.h` | P06 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `docs/native-integration.md` | P06 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `fixtures/cgb-colour/manifest.json` | P07, P08 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `src/accept/digest.c` | P07 | GBB_ACCEPT_RGB555_HEADER from gbb_accept.h is hashed with explicit LE pixel bytes; vector and padding/reject tests pass. | VERIFIED |
| `tests/scripts/reproduce-cgb-colour.sh` | P07 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `src/runner/acceptance.c` | P09 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `tests/acceptance/cases-cgb-colour.txt` | P09 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `tests/test_acceptance_digest.c` | P09 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `fixtures/magentests/manifest.json` | P10 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `tests/test_magentests.c` | P10 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `fixtures/magentests/ELIGIBILITY.md` | P10 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `tests/external/cgb-ppu-dispositions.json` | P11 | Original six/30 dispositions verified at 4811033; current Phase14 xfail schema and mutated-record checks pass. | VERIFIED |
| `tests/scripts/verify-external-dispositions.py` | P11 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `tests/scripts/run-acid2-local.py` | P11 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `tests/acid2/manifest.json` | P11 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `src/player/colour.c` | P12 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `src/player/session.c` | P12 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `src/player/main.c` | P12 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `tests/player/cgb_smoke.cmake` | P12 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `src/player/limitations.h` | P13 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `tests/player/claims_agree.cmake` | P13 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `docs/model-gates.md` | P14 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `tests/fuzz_core.c` | P14 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `tests/measure_core.c` | P14 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `.planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-BENCH.md` | P14 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `.planning/context/DECISIONS.md` | P15 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `.planning/phases/GB-11-cgb-colour-rendering-and-player-colour/COVERAGE.md` | P15 | Implementation/content inspected and consumed by the Pxx paths/tests described above; runtime existence/substance check passes. | VERIFIED |
| `.planning/.continue-here.md` | P15 | Boundary 4811033 content and STATE route agree; no claim about live route. | VERIFIED |

### Key link verification

The runtime link checker recognizes **6/31** source paths. The remaining **25** have legacy descriptive `from` fields (symbol names or paths with annotations), so it reports “Source file not found”; those are parser limitations, not accepted wiring evidence. All 31 connections were traced in actual files and registered consumers below. No link is passed solely on an import or file's existence.

| ID | From → To | Connection / observed consumer | Status |
| --- | --- | --- | --- |
| P01.L1 | tests/CMakeLists.txt gbb_colour_mutant → src/core/gabbaboy.c text | tests/CMakeLists.txt gbb_colour_mutant reads core text, verifies exactly-one anchor, writes build-tree mutant and registers expected-exit plus positive-control cases. | VERIFIED |
| P01.L2 | tests/test_cgb_colour_internal.c → tests/data/cgb-priority-truth.inc | Internal driver #includes tests/data/cgb-priority-truth.inc and iterates its row array. | VERIFIED |
| P02.L1 | io_visibility[0x69], [0x6B], [0x6C] CGB cells → io_read_cgb / io_write_cgb new cases | io_visibility selects IO_BCPD/IO_OCPD/IO_OPRI; io_read_cgb/io_write_cgb dispatch those cases. | VERIFIED |
| P02.L2 | io_write_cgb BCPD/OCPD case → cpu_cram_access_allowed | Both BCPD/OCPD write cases pass cpu_cram_access_allowed(m) to cram_data_write; blocked case tests increment index. | VERIFIED |
| P03.L1 | ppu_transfer_dot → ppu_pixel_cgb | ppu_transfer_dot assigns ppu_pixel_cgb(m,fetched_slot) to rgb_working[pixel_at]. | VERIFIED |
| P03.L2 | ppu_advance_dot frame completion → rgb_completed | ppu_advance_dot copies rgb_working to rgb_completed at visible frame completion, updates shared metadata. | VERIFIED |
| P03.L3 | ppu_cgb_background → vram[1] attribute | ppu_cgb_background uses ppu_vram_read(m,1u,map_address) for attributes at the bank0 index address. | VERIFIED |
| P04.L1 | ppu_transfer_dot compat branch → ppu_pixel_compat | Compat dispatch assigns ppu_pixel_compat into rgb_working. | VERIFIED |
| P04.L2 | ppu_pixel_compat → compat_rgb555 | ppu_pixel_compat calls ppu_compat_resolve for BG/OBJ0/OBJ1; resolver reads compat_rgb555. | VERIFIED |
| P05.L1 | tests/test_cgb_colour_internal.c cgb_priority_truth_table → tests/data/cgb-priority-truth.inc | Internal test includes oracle row array then compares actual ppu_pixel_* output and count. | VERIFIED |
| P05.L2 | tests/CMakeLists.txt plan 11-05 mutants → src/core/gabbaboy.c colour siblings | CMake gbb_colour_mutant registrations patch exactly-once production expressions into build-tree siblings; all expected controls pass. | VERIFIED |
| P06.L1 | gbb_copy_frame_rgb555 → rgb_completed | Validated gbb_copy_frame_rgb555 row memcpy reads instance->rgb_completed. | VERIFIED |
| P06.L2 | gbb_set_compat_palette → compat_rgb555 | gbb_set_compat_palette validates all entries before copying bg/obj0/obj1 into compat_rgb555. | VERIFIED |
| P06.L3 | tests/consumers/c/main.c → installed header | C and C++ installed client source calls all three new APIs; symbol guard plus actual relocated consumer controls pass. | VERIFIED |
| P07.L1 | tests/test_cgb_colour.c cgb_colour_hblank_rows → gbb_copy_frame_rgb555 and gbb_accept_rgb555_digest | Public fixture driver copies RGB555, checks per-row literal predicate then calls gbb_accept_rgb555_digest. | VERIFIED |
| P07.L2 | .github/workflows/fixture-repro.yml → tests/scripts/reproduce-cgb-colour.sh | fixture-repro.yml invokes reproduce-cgb-colour.sh with pinned RGBDS tooling. | VERIFIED |
| P08.L1 | tests/test_cgb_colour.c fixture drivers → gbb_copy_frame_rgb555 and gbb_accept_rgb555_digest | Public fixture drivers copy via API then evaluate literal region/WRAM predicates before digest. | VERIFIED |
| P08.L2 | fixtures/cgb-colour/manifest.json rows → tests/scripts/reproduce-cgb-colour.sh | reproduce-cgb-colour.sh reads each manifest recipe and invokes argv lists with validated fields. | VERIFIED |
| P09.L1 | src/runner/acceptance.c capture path → src/accept gbb_accept_rgb555_digest | capture_format reads gbb_get_info; copy_latest calls RGB555 API, finish_capture calls RGB555 digest for that format. | VERIFIED |
| P09.L2 | tests/acceptance/CMakeLists.txt acceptance_digest_rgb555_vectors → tests/scripts/rgb-digest-vector.py --rgb555 | tests/acceptance/CMakeLists.txt invokes rgb-digest-vector.py --rgb555 with the compiled digest helper. | VERIFIED |
| P10.L1 | tests/test_magentests.c magentests_cgb_* → gbb_copy_frame_rgb555 | MagenTests driver calls RGB555 API after frame runs and requires generation progression and predicates before pin. | VERIFIED |
| P10.L2 | tests/scripts/reproduce-magentests.sh → fixtures/magentests/manifest.json | reproduce-magentests.sh reads per-ROM source_dir/rgbfix table checked against manifest; --self-check passes. | VERIFIED |
| P11.L1 | tests/CMakeLists.txt cgb_external_dispositions → tests/external/cgb-ppu-dispositions.json and docs/cgb-profile.md | tests/CMakeLists.txt registers verify-external-dispositions.py against JSON and docs mirror plus mutated copy. | VERIFIED |
| P11.L2 | tests/scripts/run-acid2-local.py → gabbaboy-runner --failure-dir PPM | run-acid2-local.py writes a temporary runner case and invokes --failure-dir; bounds/pin/synthetic decode controls pass. | VERIFIED |
| P12.L1 | src/player/main.c create_machine / replace_session_rom / run_script_smoke → player_session_probe_profile | main.c session creation/replacement/script call player_session_probe_profile before session construction; seam probes actual ROM. | VERIFIED |
| P12.L2 | update_frame CGB branch → gbb_copy_frame_rgb555 and player_rgb555_frame_to_rgba | update_frame obtains actual gbb_get_info profile and routes CGB to copy API, conversion, SDL_UpdateTexture. | VERIFIED |
| P13.L1 | tests/player/CMakeLists.txt player_claims_agree → src/player/limitations.h, README.md, .github/workflows/preview.yml | tests/player/CMakeLists.txt invokes claims_agree.cmake with limitations, README and preview values plus removed-phrase negative. | VERIFIED |
| P14.L1 | tests/CMakeLists.txt model_gates_no_phase11_rows → docs/model-gates.md and src/core/gabbaboy.c | tests/CMakeLists.txt invokes check_no_phase11_rows.cmake on core/docs plus mutated-doc negative. | VERIFIED |
| P14.L2 | tests/scripts/measure-release-baseline.sh --ab → tests/measure_core.c builds at 3012e8f and head | measure-release-baseline.sh --ab interleaves both builds and refuses incorrect tracer digest 4c7a57ff3d50d228; benchmark selftests exercise receipts. | VERIFIED |
| P15.L1 | .planning/research/INDEX.md Phase 11 bullet → Phase 11 evidence files | INDEX Phase11 bullet relative links all resolve to research/docs/manifests/benchmark. | VERIFIED |
| P15.L2 | .planning/STATE.md → .planning/.continue-here.md | At 4811033 STATE and continuation share /gsd-verify-work 11, completed execution and named following Phase12; six boundary mutation controls reject changed routes/flags/tree. | VERIFIED |

### Data-flow trace (Level 4)

| Output | Real source and path | Independent behavioral evidence | Status |
| --- | --- | --- | --- |
| Native CGB RGB555 frame | Guest writes → CRAM/index ports + VRAM0 map/VRAM1 attributes + OAM → per-dot ppu_pixel_cgb → rgb_working → frame-completion rgb_completed → gbb_copy_frame_rgb555 | 144-row HBlank fixture rejects one-frame CRAM snapshot; 6,144 priority rows and whole-frame samples; guest CRAM markers and attribute fixtures | FLOWING |
| Compatibility colour frame | Guest DMG BGP/OBP0/OBP1 shade semantics → per-instance authored/host palette → per-dot ppu_pixel_compat → completed RGB store | Separate OBJ sets, override mapping, reject-without-mutation, reset persistence and future-frame effect | FLOWING |
| Acceptance frame555 / observed555 | Actual selected instance profile → RGB555 copy → explicit LE digest header/pixel serialization → distinct verdict/failure PPM | Independent Python vector; --profile equivalence, wrong reference, wrong model and progress refusal controls | FLOWING |
| SDL texture and model title | Actual probed ROM + gbb_get_info mode/profile → RGB555 copy → 5-bit expansion to RGBA → SDL_UpdateTexture + player_model_token | Real CGB smoke checks digest/distinct colours/independent spot pixels/title; R/B swap, wrong DMG path and ignored-model mutants fail as required | FLOWING |

No rendered value terminates at a static success frame, hardcoded empty store, or mock. Literal expected pixels are test oracles derived from fixture designs, not production outputs.

### Behavioral checks executed during this refresh

| Check | Command / evidence | Result |
| --- | --- | --- |
| Rebuilt complete core regression | Orchestrator: cmake --preset phase1; cmake --build --preset phase1; ctest --preset phase1 --output-on-failure --no-tests=error; complete log inspected | 1,144/1,144, zero skips, 486.68s |
| Rebuilt native player regression | Orchestrator: ctest --test-dir build-player -R '^player_' --output-on-failure --no-tests=error; complete log inspected | 98/98, zero skips, 21.72s |
| Independent behavioral spot checks | Verifier: ctest --preset phase1 exact-name selection for summary_coverage, cgb_priority_truth_table, cgb_priority_truth_frames, cgb_priority_opri_no_effect, cgb_rgb555_lcd_off, palette_compat_effect_next_frame, cgb_colour_hblank_rows, cgb_external_dispositions and its mutated case | 9/9, 0.92s |
| Independent mutation and API wiring checks | Verifier: exact-name selection acceptance_digest_rgb555_vectors, cgb_priority_mutant_ignore_bg_attr7 and control, cgb_colour_mutant_frame_resolve and control, cgb_consumer_symbol_coverage and selftest | 7/7, 0.15s |
| DMG frozen ledger | Verifier: bash tests/scripts/verify-dmg-baseline.sh | inventory313/mooneye15/acceptance20/bench2 keys; zero changed rows; baseline status=pass |
| Magen recipe table | Verifier: bash tests/scripts/reproduce-magentests.sh --self-check | self-check=pass; not a new toolchain rebuild |
| UAT canonical closure | Verifier: python3 tests/scripts/verify-uat-closure.py .planning/phases/GB-11-cgb-colour-rendering-and-player-colour --self-test | automated=91, controls=19, pass |
| No external API declaration | Verifier: OpenGSD check api-coverage.verify-pre 11 | passed=true, block=false, none_declared=true |
| Boundary/history/data contracts | Verifier: git show/ls-tree at 4811033, task-window diff checks, current fixture/source SHA256 and INDEX link checks | false auto flags, correct route/title/no Phase12 tree; six changed-route/flag/tree controls rejected; six fixture sets and eight decision rows pass |
| Bounded independent gate supplement | 11-REFRESH-GATES.md; current source inspections and exact CTest commands | 36/36 focused checks; historical review/security/Nyquist applicability explicitly limited |

The 197 SUMMARY verification references (174 unique) were reconciled against actual commands/results, not treated as their own proof. Two legacy short names `installed_consumer_c/cpp` are not registered in this core-only inventory: the current `v02_consumer_controls` test actually installs, relocates, builds and runs both C/C++ consumers, exercises RGB555 copy and uses failing-consumer/package controls. Source symbol coverage alone would not establish this runtime consumer claim. Historical package/reproduction/ASan and benchmark receipts remain attached to their actual producing revisions in 11-UAT.md/11-BENCH.md; this run does not relabel them as current-head remote results.

### Probe execution

No Phase11 PLAN/SUMMARY declares a `probe-*.sh` and this is not a migration/tooling phase. The unrelated `tests/scripts/probe-mooneye-candidate.sh` is not silently substituted as a Phase11 probe. Phase-declared executable verification uses the registered CTests and explicit baseline/reproduction/closure commands above. Required scripted checks are real, registered and executed; pinned RGBDS rebuild has only the preserved historical hosted receipt, while current tool-failure/missing-pin refusal controls pass.

### Requirements coverage

| Requirement | Source plans | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| CGB-04 | 01–03,05–11,14,15 | Attributes, CRAM auto-increment/lockout, CGB priority, RGB555 API; DMG byte identity | SATISFIED | R1 and P01–03/P05–11/P14; independent oracle, real frames, guest fixtures, Magen predicates and targeted mutants |
| CGB-05 | 04–06,08,14,15 | Original fixed documented overridable compat palette; no boot-ROM table | SATISFIED | R2; P04/P06/P08 palette state-transition tests and code/doc mirror control |
| CGB-09 | 12–15 | Native player model selection and colour smoke | SATISFIED | R3; P12/P13/P14 real upload smoke, model and expansion seams with negative controls |

REQUIREMENTS.md maps exactly CGB-04/05/09 to Phase11 and marks each complete. All three appear in PLAN requirements. No orphaned Phase11 requirement was found.

### Anti-patterns and adversarial checks

No unresolved debt marker or proven stub/wiring defect was found in the collected modified-file/artifact scope. Marker scans distinguish literal `XXXXXX` temporary-file templates from debt comments. Core error paths validate before writes; tests include alignment/stride/overflow/overlap, no-frame, invalid palette sizes/bit15, missing file/PGB and wrong-profile cases. Negative cases assert the intended diagnostic or invariant rather than accepting any crash.

Disconfirmation targeted three plausible false passes: (1) resolving all pixels from one palette snapshot, rejected by HBlank row mutation; (2) connected-but-wrong player data, rejected by actual swapped-channel/wrong-path smokes; (3) old historical absence checks applied to current later-phase HEAD, prevented by reading boundary objects and six changed-boundary controls. The independent RGB555 label check was followed through its header macro, and the external disposition reason was traced through the explicit Phase14 update rather than accepting the raw checker verdict.

### Advisory (New Scope, Unevidenced)

None newly raised. The review-scope resolver is degraded (`phase-range/no-task-commit-rows`) and expands into later-phase files; the 36-check supplement is a bounded applicability review, not a full review of that oversized range. Historical security closes 43 threats and Nyquist covers 25 rows; this refresh reuses their applicability with explicit limits, not a new 43-threat/whole-project certification.

### Human verification required and limits

None for this phase's software contract: no deferred human-check/backstop items were declared and all 91 deliverables have decidable automated evidence. Default palette appearance remains an owner preference/veto; it is not a claim of monitor colour accuracy. Physical CGB-E, analog colour/filter characteristics, fine mode-3/CRAM lock-edge timing, unrestricted game compatibility and G1 acid2 redistribution remain unqualified. No hardware observation, perceptual audit or rights-qualified acid2 run was performed. SDL native UI checks are not browser/DOM or numerical visual scores.

### Deferred scope and gaps

No actionable gaps, regressions or unverified behaviors. Phase11's intentional mode-3/lock-edge deferrals remain explicit, and historical Phase12/13 feature exclusions are verified at the boundary; their later delivery is not counted as Phase11 work. Exact-head hosted checks and review/merge readiness remain the orchestrator's separate gate. This report does not start or complete another phase and does not alter the live handoff.

_Verifier: gsd-verifier; expanded verification refresh, 2026-10-20._
