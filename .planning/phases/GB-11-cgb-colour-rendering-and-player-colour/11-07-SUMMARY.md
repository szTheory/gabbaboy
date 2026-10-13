---
phase: 11-cgb-colour-rendering-and-player-colour
plan: 07
subsystem: cgb-colour-fixture-pipeline
tags: [rgb555, fixture, rgbds, reproduction, d-01, d-15, d-23, d-43, mutant]
requires:
  - phase: 11-cgb-colour-rendering-and-player-colour
    provides: "11-03 per-dot RGB resolve, 11-06 public gbb_copy_frame_rgb555"
provides:
  - "src/accept RGB555 helpers: GBB_ACCEPT_RGB555_HEADER, gbb_accept_rgb555_digest(_bin), gbb_accept_write_ppm_rgb555, gbb_accept_expand5, gbb_accept_rgb555_distinct"
  - "fixtures/cgb-colour/ original fixture set with colour-hblank.gb, common.inc, manifest with per-row recipe, MIT licence"
  - "tests/scripts/reproduce-cgb-colour.sh manifest-driven pinned rebuild and the fixture-repro CI step"
  - "cgb_colour_hblank_rows plus the frame-resolve mutant"
affects: [11-08, 11-09]
requirements-completed: []
actuals:
  tokens: 36000
  tasks: 2
  commits: 3
coverage:
  - id: C1
    description: "A guest that rewrites BG colour 0 in each HBlank shows its own colour on every one of the 144 rows of the public RGB555 frame, the first completed frame holds no reset-fill zero pixel, and the frame digest is pinned"
    human_judgment: false
    verification:
      - kind: integration
        ref: "cgb_colour_hblank_rows"
        status: pass
  - id: C2
    description: "Resolving the whole frame against one CRAM snapshot is detected as a wrong row, with a passing control on the same mutated core"
    human_judgment: false
    verification:
      - kind: integration
        ref: "cgb_colour_mutant_frame_resolve"
        status: pass
      - kind: integration
        ref: "cgb_colour_mutant_frame_resolve_control"
        status: pass
  - id: C3
    description: "The committed fixture ROM matches the size and SHA-256 recorded in its manifest"
    human_judgment: false
    verification:
      - kind: integration
        ref: "cgb_colour_fixture_digest"
        status: pass
  - id: C4
    description: "The RGB555 digest helpers serialise explicit little-endian pairs, the independent Python computation of the pinned frame digest agrees, and the DMG digest vectors are unchanged"
    human_judgment: false
    verification:
      - kind: unit
        ref: "acceptance_digest_vectors"
        status: pass
      - kind: other
        ref: "python3 -I computation of the GBB-RGB555LE-v1 digest of the table-derived frame equals the pinned abb528b8ffd636f85dcd62b1f13e60ea2f1ef7ac368c84b4767e5b967d2e9546"
        status: pass
  - id: C5
    description: "The manifest-driven script rebuilds every ROM from its recipe with RGBDS 1.0.1 byte for byte, rejects a different tool version and a tampered ROM, and the CI job runs it"
    human_judgment: false
    verification:
      - kind: other
        ref: "bash tests/scripts/reproduce-cgb-colour.sh"
        status: pass
  - id: C6
    description: "DMG output stays byte-identical"
    human_judgment: false
    verification:
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh"
        status: pass
status: complete
commits: 3
plan_head_before: 57bd048a3fb2d604e8c058a6a7a8a0734faee9c7
plan_head_after: b4e5722c61d5ac83154d084d41fc7a8c1faac44b
duration: 50 min
completed: 2026-10-12
---

# Phase 11 Plan 07: CGB colour fixture pipeline Summary

The first original CGB colour ROM (a per-line HBlank palette writer) is built with the pinned RGBDS 1.0.1, checked row by row through the public `gbb_copy_frame_rgb555`, digest-pinned with new little-endian RGB555 helpers, and rebuilt byte-identically from its manifest recipe.

## Accomplishments

- `src/accept` gains the RGB555 evidence helpers beside the untouched RGB888 ones. The digest hashes the `GBB-RGB555LE-v1 160x144` header then explicit low-byte, high-byte pairs; any value above 0x7FFF or an odd/short pitch is rejected with nothing written. The distinct counter uses a 4 KiB stack bitmap, so there is no hidden global.
- `colour-hblank.gb` (source `hblank.asm` plus `common.inc`): one all-index-0 BG tile, line 0's colour written in VBlank, and a STAT mode-0 handler that writes line `(LY + 1) mod 144`. Row `y` must equal `(y * 229 + 1) & 0x7FFF`; the 144 values are distinct and non-zero.
- `cgb_colour_hblank_rows` first runs the literal structural predicate (each row uniform and equal to its table value, 144 distinct values, no zero pixel in the first completed frame), then compares the digest. The pinned digest was recomputed independently with a short `python3 -I` script from the table formula and matches.
- `cgb_colour_mutant_frame_resolve` replaces the single BG `cram_colour` call in `ppu_pixel_cgb` with a function-static snapshot taken at line 0, x 0, emulating a copy-time resolve; the case exits 1 at row 1 and the control passes on the same mutated core.
- `fixtures/cgb-colour/manifest.json` records per-ROM `recipe` (source, `-D` defines, rgbfix flags), protocol, evidence class and scope limits. `reproduce-cgb-colour.sh` runs every row from the manifest with argument lists, validates recipe fields, compares against the committed bytes and prints `result=byte-identical roms=1`. `fixture-repro.yml` runs it and its pin-consistency block now includes the new manifest.

## Deviations from Plan

**1. [Rule 3 - Blocking] `.gitignore` exception.** `*.gb` is ignored and each checked-in fixture ROM has an exception line, so `!/fixtures/cgb-colour/*.gb` was added (a wildcard so plan 11-08 adds ROMs as manifest rows only). File not in the plan's list. Commit f0762db.

**2. [Rule 1 - Bug in own fixture] No HALT in the guest's main loop.** `gbb_run` returns at each HALT with budget left, so a halted guest advanced only one interrupt per call and the frame never completed (all rows stayed 0x7FFF). The loop is now a single `jr` and the source comment says why. No core change.

**3. [Rule 3 - Blocking] Mutant harness links the acceptance library.** `test_cgb_colour.c` now needs the digest helpers, so `gbb_colour_mutant` links `gabbaboy_accept` after the mutant library for public test sources (mutated core resolved first; the real core is not pulled). `test_cgb_colour` links `gabbaboy_accept` only, which carries the core.

**4. [Interpretation] Manifest shape.** `source` is a list and `source_sha256` a name-to-digest map because the fixture has two sources; the other cgb-banking keys are kept. The test binary takes an optional fixture-directory argument (argc 2 or 3).

**5. [Toolchain] Pinned RGBDS obtained as the precedent prescribes.** Host `rgbasm` is Homebrew 1.0.4. The macOS archive was downloaded into a scratch directory outside the repo, its SHA-256 matched the recorded pin `2f6f13c6...3645`, and `rgbasm --version` printed `rgbasm v1.0.1` before any ROM bytes were built. The ROM was never produced by 1.0.4; the script refuses it (checked: `rgbasm version mismatch: expected v1.0.1, got rgbasm v1.0.4`). The Linux byte-identity proof runs in the fixture-repro CI job on push.

**Total deviations:** 5, none affecting scope or locked decisions.

## Verification

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`: 649/649 passed.
- `bash tests/scripts/verify-dmg-baseline.sh`: baseline status=pass.
- `bash tests/scripts/reproduce-cgb-colour.sh` with pinned tools: `result=byte-identical roms=1`. Negative controls: a flipped ROM byte gives `result=differs reason=rebuilt-rom-differs-from-checked-in-colour-hblank.gb` (ROM restored from git); the 1.0.4 host tools are refused.
- Acceptance criteria: RGB555 header count 1, RGB888 header count 1, manifest `True 1`, four inventory names present, `git check-attr text` prints `unset`, `reproduce-cgb-colour.sh` appears once in the workflow, `.gitattributes` rule count 1, no ROM name in the script.
- `phase1-asan` is Linux-only; it runs in CI on the pushed branch.

## Known Stubs

None.

## Threat Flags

None. T-11-15 to T-11-18 mitigations are implemented as planned: archive digest checked, recipe fields validated and passed as argument lists, script never writes into the repository, manifest digest test, `-text` attributes, and out-of-range RGB555 rejected (its independent vector lands in plan 11-09).

## Self-Check: PASSED

Commits 6846e0c, f0762db and b4e5722 are ancestors of HEAD; fixtures/cgb-colour/colour-hblank.gb, manifest.json, hblank.asm, common.inc, LICENSE.txt, tests/scripts/reproduce-cgb-colour.sh exist.
