---
phase: 11-cgb-colour-rendering-and-player-colour
plan: 12
subsystem: sdl3-player-cgb-presentation
tags: [player, cgb, rgb555, select-profile, d-26, d-27, d-28, d-29, d-30, mutants]
status: complete
requires:
  - phase: 11-cgb-colour-rendering-and-player-colour
    provides: "11-06 public gbb_copy_frame_rgb555, 11-07 gbb_accept_expand5, 11-08 colour-attr.gb fixture"
provides:
  - "gabbaboy-player --model auto|dmg|cgb (default dmg) through one select_profile seam, player_session_probe_profile"
  - "CGB update_frame branch: gbb_copy_frame_rgb555 expanded by src/player/colour.c into the existing RGBA32 texture"
  - "Window title model token (DMG, CGB, CGB (DMG-compat)) and the headless --smoke-colour mode"
  - "player_cgb_smoke with a pinned RGBA digest and 40 independently computed spot pixels, plus four compiled mutants"
affects: [11-13, 11-14]
requirements-completed: []
plan_head_before: 75be0f16c9aa86c03ef478dc38bbeb26c9bb707d
plan_head_after: 92660facdd857aa4c611c87aeb4090cbb90a4931
actuals:
  tokens: 13600
  tasks: 2
  commits: 2
coverage:
  - id: C1
    description: "The select_profile seam maps every model and $143 value to the right profile, reports the CGB-only note only for a $C0 ROM on the DMG model, rejects a PGB header for every model, and leaves its outputs unchanged for a missing file"
    requirement: CGB-09
    human_judgment: false
    verification:
      - kind: unit
        ref: "player_session_model_select"
        status: pass
      - kind: unit
        ref: "player_session_model_pgb"
        status: pass
      - kind: unit
        ref: "player_session_model_missing_file"
        status: pass
  - id: C2
    description: "A session library whose select_profile ignores the model fails player_session_model_select"
    requirement: CGB-09
    human_judgment: false
    verification:
      - kind: unit
        ref: "player_cgb_model_mutant_ignores_flag"
        status: pass
  - id: C3
    description: "RGB555 to RGBA32 expansion equals the independent formula for all 32768 values at two pitches, alpha is always 255, and a red/blue-swapped colour.c fails the same test"
    requirement: CGB-09
    human_judgment: false
    verification:
      - kind: unit
        ref: "player_cgb_expand"
        status: pass
      - kind: unit
        ref: "player_cgb_expand_mutant_rb_swap"
        status: pass
  - id: C4
    description: "The window title model token is DMG, CGB or CGB (DMG-compat) from the machine mode, and - with no ROM"
    requirement: CGB-09
    human_judgment: false
    verification:
      - kind: unit
        ref: "player_cgb_title_token"
        status: pass
  - id: C5
    description: "The real player renders colour-attr.gb in colour: the uploaded RGBA digest is pinned, at least 14 distinct colours appear, 40 rendered-surface spot pixels equal values computed in CMake from the fixture's literal RGB555 palette entries, and the title token is CGB"
    requirement: CGB-09
    human_judgment: false
    verification:
      - kind: e2e
        ref: "player_cgb_smoke"
        status: pass
  - id: C6
    description: "A player built with R and B swapped in colour.c and a player whose update_frame is forced onto the DMG path each make the smoke check fail"
    requirement: CGB-09
    human_judgment: false
    verification:
      - kind: e2e
        ref: "player_cgb_smoke_mutant_rb_swap"
        status: pass
      - kind: e2e
        ref: "player_cgb_smoke_mutant_dmg_path"
        status: pass
  - id: C7
    description: "The --model grammar: an unknown or missing value is a usage error with exit 2, cgb on a DMG-only ROM reports CGB (DMG-compat), auto picks CGB for a CGB ROM, dmg and the default model refuse the colour smoke, and auto picks DMG for a DMG ROM"
    requirement: CGB-09
    human_judgment: false
    verification:
      - kind: e2e
        ref: "player_cgb_cli"
        status: pass
  - id: C8
    description: "The existing DMG player behaviour is unchanged: --model auto --smoke passes exactly like player_smoke, including the invalid-ROM replacement that fails its probe and leaves the session intact, and the whole player suite still passes"
    requirement: CGB-09
    human_judgment: false
    verification:
      - kind: e2e
        ref: "player_cgb_model_auto_smoke"
        status: pass
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh --build-package"
        status: pass
---

# Phase 11 Plan 12: SDL3 player CGB model, colour presentation and smoke Summary

`gabbaboy-player` takes a leading `--model auto|dmg|cgb` (default `dmg`), picks the profile through one `player_session_probe_profile` seam, presents CGB frames by expanding RGB555 with `(c << 3) | (c >> 2)` into the existing RGBA32 texture, shows the mode in the title, and is checked by an automated colour smoke with independent expectations and four detected mutants.

## Accomplishments

- **select_profile seam (D-26 as amended).** `player_session_probe_profile` in `session.c` reuses `read_rom_file` (same bound) and `gbb_probe_rom`. It probes the CGB profile first so a PGB header (`GBB_UNSUPPORTED_EXECUTION_MODE`) is an error ("PGB ROMs are not supported") for every model, then chooses DMG, CGB, or CGB exactly when `$143` bit 7 is set (auto), and reports `GBB_INFO_CGB_ONLY_ON_DMG` from the chosen DMG probe. The three session sites (`create_machine`, `replace_session_rom`, `run_script_smoke`) use it; `replace_session_rom` probes before creating the candidate, so a failure leaves the running session untouched (re-probed on every open). The authored audio guest, `identify_rom_with_core` and `identify_smoke_rom` stay explicit DMG with a comment, so `grep -c 'gbb_create(GBB_PROFILE_DMG_CPU_B' src/player/main.c` is 3.
- **Colour presentation (D-27).** `src/player/colour.c` (SDL-free, compiled directly into the player and the tests) holds `player_rgb555_frame_to_rgba` and `player_model_token`. `update_frame` chooses its branch from `gbb_get_info` profile, not the flag; the CGB branch uses `gbb_copy_frame_rgb555` and the same `SDL_UpdateTexture` call. The DMG branch body is unchanged, so every existing DMG smoke digest is unchanged.
- **Title and help (D-28, D-29).** The title gains a ` | <token> | ` field after the ROM name (additive, so the existing substring assertions hold). The help text names `--model`, says the compatibility palette is the core default, and says the player applies no colour correction. There is no palette flag.
- **Headless smoke (D-30).** `--smoke-colour ROM` renders 30 frames through the hidden software renderer and prints `smoke_colour rgba_sha256=... distinct=... title_token=... spot=x,y:rrggbb;...`. It exits 2 with "smoke-colour needs the CGB profile" when the selected profile is DMG.
- **Checks.** `tests/player/cgb_smoke.cmake` computes the 40 expected spot colours (4 quadrants of each of 10 cells of `colour-attr.gb`) in CMake integer math from the literal palette values in `attr.asm` and the documented expansion, never from the player. The RGBA digest pin (`8633f67e...a6c4`) was recorded after the spot checks passed. The player was observed to render all 14 distinct colours of the fixture (cell 5 shows `0x2222`, BG priority winning over the object).

## Negative controls (each confirmed to fail for its own reason)

- `player_cgb_smoke_mutant_rb_swap`: a player built from a configure-time copy of `colour.c` with the R and B extractions exchanged fails on cell 0 ("is ce9c31, expected 319cce").
- `player_cgb_smoke_mutant_dmg_path`: a player built from a copy of `main.c` with the CGB branch of `update_frame` disabled exits 1 ("Could not copy completed frame (error 2)").
- `player_cgb_expand_mutant_rb_swap`: `test_colour` linked against the swapped `colour.c` fails its singleton channel check.
- `player_cgb_model_mutant_ignores_flag`: `test_session` linked against a `session.c` copy whose model choice is forced to DMG fails `player_session_model_select` at the profile REQUIRE.
- Every mutant source is produced by `gbb_player_mutate_source`, which stops configure unless the anchor occurs exactly once. The flag-ignoring mutant sets `ASAN_OPTIONS=detect_leaks=0` on its deliberately failing run, with a comment, matching commit 361256d's rule.

## Deviations from Plan

**1. [Rule 3 - Blocking] `test_player_reset_transition` links the player's `main.c`-derived code.** It failed to link once `main.c` called `player_rgb555_frame_to_rgba` and `player_model_token`. `colour.c` is now also a source of that test in `tests/player/CMakeLists.txt` (already a listed file). Commit 92660fa.

**2. [Rule 1 - Bug] Audio backpressure stalled the colour smoke.** The first `--smoke-colour` run exited 1 silently because `advance_to` returns false when the audio ring is full and nothing drains it. The smoke now calls `player_audio_clear` before each frame. Commit 6281a3e.

**3. [Rule 1 - Bug] Spot sampling used logical, not output, coordinates.** `frame_destination` is in logical units (160x144), the hidden surface is 320x288, so the first spots read the wrong pixels. Sampling now uses `SDL_GetRenderLogicalPresentationRect`. Commit 6281a3e.

**4. Two tasks in two commits split by layer.** The tracer slice and the grammar completion share one `main.c` change and one test inventory that must stay consistent at every commit, so the commits are source (6281a3e) and tests (92660fa) rather than one per plan task. The player suite passes at the head; the intermediate commit builds because it adds no tests.

**5. `player_cgb_cli` is a mode of `cgb_smoke.cmake`** (`-DGBB_CHECK=cli`) rather than several `expect_exit.cmake` invocations, to keep the file set to the planned list. It covers every row of the behaviour list except a PGB ROM on the command line, which `player_session_model_pgb` covers at the seam instead.

## Verification

- `bash tests/scripts/verify-phase3-player.sh --build-package`: 91/91 `^player_` tests passed (12 new), then the packaged smokes passed.
- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`: 677/677 tests passed (about 182 s). The `phase1-asan` preset is Linux-only and is not run on this host; CI on the pushed branch runs it.
- `bash tests/scripts/verify-dmg-baseline.sh`: `baseline status=pass`. No edit touched `src/core/gabbaboy.c`, `src/runner/*` or `src/accept/*`.
- Coupling note: the `player_cgb_smoke` digest depends on the core's CGB output for `colour-attr.gb`; close-out plan 11-14 re-runs the player suite at the merged head.

## Known Stubs

None.

## Threat Flags

None. The new command-line value is a closed three-token set (T-11-27), the probe reuses the bounded `read_rom_file` (T-11-28), the RGBA buffers are fixed 160x144 (T-11-29), and the smoke writes nothing and runs with an isolated HOME (T-11-30).

## Self-Check: PASSED

Created files (`src/player/colour.c`, `src/player/colour.h`, `tests/player/test_colour.c`, `tests/player/cgb_smoke.cmake`) exist; commits 6281a3e and 92660fa are ancestors of HEAD.
