# Phase 11: CGB Colour Rendering and Player Colour - Pattern Map

**Mapped:** 2026-10-12
**Files analyzed:** 38 new/modified
**Analogs found:** 36 / 38 (2 partial, see "No Analog Found")
**Scope note:** 11-RESEARCH.md "Code Map" already holds line-anchored seams in `src/core/gabbaboy.c`, the header, runner and player. This file does not repeat that map. It confirms the analogs and gives copyable excerpts with current anchors (HEAD `28c0076`). All analog paths were checked with `git ls-files` (tracked; no gitignored `.gsd/capabilities` mirrors involved). Phase 10 analogs in `10-PATTERNS.md` remain valid for registration discipline, `expect_exit.cmake`, doc-contract, fixture-manifest and unknown-bus patterns; only Phase 11 deltas are listed.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/core/gabbaboy.c` (CRAM, `ppu_pixel_cgb`/`ppu_pixel_compat`/`ppu_compose_cgb`, dispatch, `rgb_*` buffers, API) | core | streaming (per-dot) + request-response | self: `ppu_pixel_shade` (:2242), `ppu_transfer_dot` (:2360), `io_read_cgb`/`io_write_cgb` (:1249-1291) | exact (self) |
| `include/gabbaboy/gabbaboy.h` (`gbb_copy_frame_rgb555`, `gbb_compat_palette`, set/get) | public API | request-response | `gbb_info` handshake (`gabbaboy.h:325-355`), `gbb_copy_frame` comment (:245-260) | exact |
| `tests/test_cgb_colour_internal.c` (CRAM ports, truth table, buffers) | test (white-box) | transform | `tests/test_banking_internal.c`, `tests/test_cgb_tables.c` (include core) | exact |
| `tests/test_cgb_colour.c` (public API, fixtures, mutant driver) | test | request-response | `tests/test_banking.c` (case dispatch, guest markers) | exact |
| `tests/CMakeLists.txt` `gbb_colour_mutant` function | config (configure-time mutant) | batch | `gbb_banking_mutant` (:243-278) | exact |
| `tests/data/cgb-priority-truth.inc` + `tests/scripts/gen-cgb-priority-truth.py` | test data + generator | batch | `tests/scripts/rgb-digest-vector.py` (independent-vector script) | role-match |
| `tests/test_cgb_visibility.c` (rewrite DEFERRED(11) cells) | test | request-response | self (:348-349, :385, :397, :697-701, :719) | exact (self) |
| `tests/test_cgb_tables.c` (+ field names, kind rendering, `compat_palette` mode) | test | transform | self (`field_names` :25-39, `render_io` :277-303, `case_emit` :241) | exact (self) |
| `docs/cgb-profile.md`, `docs/model-gates.md`, `docs/native-integration.md`, `docs/support/unreleased.md` | docs (mirrored) | transform | self; marker blocks `<!-- cgb-post-boot-begin -->` | exact (self) |
| `fixtures/cgb-colour/{*.asm, *.gb, manifest.json, LICENSE.txt}` | fixture (original) | file-I/O | `fixtures/cgb-banking/` | exact |
| `tests/scripts/reproduce-cgb-colour.sh` | utility (repro) | batch | `tests/scripts/reproduce-cgb-banking.sh` | exact |
| `.github/workflows/fixture-repro.yml` (new step + pin block) | CI config | batch | cgb-banking step (:147) and pin block (:32-62) | exact |
| `fixtures/magentests/` (+3 `.gbc`, manifest, ELIGIBILITY, SOURCES) | fixture (third-party) | file-I/O | existing `fixtures/magentests/` (3 `mbc_oob_sram_*`) | exact |
| `tests/scripts/reproduce-magentests.sh` (per-ROM table) | utility (repro) | batch | self (`self_check` asserts `len(entries) == 3`) | exact (self) |
| `tests/test_magentests.c` (CGB cases via RGB555) | test | request-response | self (`expect_screen`, `negative_control`) | role-match |
| `src/accept/gbb_accept.h`, `src/accept/digest.c` (RGB555 digest, PPM, expand helper) | utility | transform | `gbb_accept_rgb_digest*` (`gbb_accept.h:205-216`, `digest.c`) | exact |
| `tests/test_acceptance_digest.c` (RGB555 vectors) | test | transform | self | exact (self) |
| `src/runner/acceptance.c` (CGB frame branch, :185-197, :721, :726) | runner | request-response | self | exact (self) |
| `tests/acceptance/cases*.txt` (CGB frame-digest row) | config | batch | existing `cases.txt` rows | role-match |
| `src/player/colour.c`, `src/player/colour.h` | utility (SDL-free) | transform | `src/player/presentation.[ch]` (SDL-free helper) | role-match |
| `src/player/main.c` (`--model`, `select_profile`, `update_frame` CGB branch, title token, `--smoke-colour`) | player adapter | request-response | self: `update_frame` (:642-671), `format_window_title` (:692-705), `run_script_smoke` (:2190-2238), `smoke_read_demo_target_pixel` (:842-857) | exact (self) |
| `src/player/session.c`/`.h` (`player_session_probe_profile`) | player adapter | file-I/O | `player_session_replace_rom` (`session.c:221-268`) | exact |
| `src/player/limitations.h`, `tests/player/test_limitations.c`, README, `--help`, `preview.yml` | docs/config | transform | self (verbatim-pinned text) | exact (self) |
| `tests/player/test_colour.c`, `tests/player/CMakeLists.txt`, `tests/player/expected-tests.txt` | test | transform | `tests/player/test_limitations.c`; `elseif(test_name ...)` dispatch | role-match |
| `tests/consumers/{c,cpp}` (rgb555 + compat calls) | test (installed consumer) | request-response | `cgb_api_smoke` in `tests/consumers/c/main.c` | exact |
| `tests/fuzz_core.c` (palette sequences, `gbb_set_compat_palette`) | test (fuzz) | batch | self | exact (self) |
| `tests/measure_core.c` (CGB workload / profile option) | utility (bench) | batch | self (`argc != 3`, DMG-only) | role-match |
| `tests/expected-tests.txt` | config | n/a | self (sorted-equality gate) | exact |

## Pattern Assignments

### `src/core/gabbaboy.c`: CRAM storage and ports (core, request-response)

**Analog:** `io_read_cgb` / `io_write_cgb` (`gabbaboy.c:1249-1291`), `io_visibility[]` rows `:1199-1203`, `cpu_vram_access_allowed` `:1384-1389`, `post_boot[]` BCPS/OCPS rows `:886-889`, `PB_RAM_FILL` `:1024-1030`.

**Table rows to flip** (`:1199-1203`, change only the CGB cell kind; keep DMG and compat cells verbatim per D-31):
```c
[0x69] = { IOC(DMG_STOP), IOC_DEF(DEFERRED_RW, 11), IOC(CONST_FF), IOS_PANDOCS }, /* BCPD ... */
[0x6B] = { IOC(DMG_STOP), IOC_DEF(DEFERRED_RW, 11), IOC(CONST_FF), IOS_PANDOCS }, /* OCPD ... */
[0x6C] = { IOC(DMG_STOP), IOC_DEF(DEFERRED_RW, 11), IOC(CONST_FF), IOS_PANDOCS }, /* OPRI ... */
```

**Case shape to extend** (`io_read_cgb`, `:1253-1261`; add `IO_BCPD`/`IO_OCPD`/`IO_OPRI` cases beside `IO_VBK`):
```c
    case IO_VBK: return (uint8_t)(0xFEu | (m->vram_bank & 1u));
    case IO_SVBK: return (uint8_t)(0xF8u | (m->svbk & 7u));
    ...
    default: return 0xFFu; /* CONST_FF, DEFERRED_W; DEFERRED_RW is refused before the read */
```
The `io_write_cgb` `IO_DEFERRED_RW`/`IO_DEFERRED_W` arm (`:1283-1287`) is what currently latches `bus_unsupported`; the new kinds must not fall into it.

**Lockout predicate** (separate function, own gate row; model on `:1384-1389`):
```c
/* MODEL: BOTH GATE-00 basis=see-branch-gates */
static int cpu_vram_access_allowed(const gbb_instance *m) {
    /* MODEL: UNKNOWN GATE-13 research:11 -- VRAM CPU lock window during mode 3 */
    return (m->lcdc & 0x80u) == 0 || m->ppu_mode != 3u;
}
```
New `cpu_cram_access_allowed` copies the body with a `UNKNOWN research:14` tag (D-12).

**Post-boot rows** (`:886-889`): existing rows use `PBC_POLICY(value, reason)`; add `PB_BG_CRAM_FILL`/`PB_OBJ_CRAM_FILL` modelled on `PB_RAM_FILL` (`:1024-1030`, including its inline `MODEL: BOTH GATE-09` tag). Adding enum members forces: the `_Static_assert` at `:898-899`, `field_names[]` in `tests/test_cgb_tables.c:25-39` (positional), and the doc rows between `<!-- cgb-post-boot-begin -->`/`end`.

**Semantic snippet** (`cram_data_write` index math `0x80 | ((idx + 1) & 0x3F)`) is in RESEARCH Pattern 2; copy verbatim.

---

### `src/core/gabbaboy.c`: dual-store, dispatch, copy-frame (core, streaming + request-response)

**Analog:** self.

**Dispatch point** (`ppu_transfer_dot`, `:2402-2405`, current):
```c
    --m->ppu_fifo_count;
    m->frame_working[(unsigned)m->ly * GBB_FRAME_WIDTH + fetched_slot] =
        ppu_pixel_shade(m, fetched_slot);
    if (++m->ppu_output_x == GBB_FRAME_WIDTH) m->ppu_transfer_complete = 1;
```
Replace only the middle statement with the three-way dispatch in RESEARCH (profile DMG first, then `exec_mode == GBB_MODE_CGB`, else compat); the predicate must equal `post_boot_column`'s (`:904-908`).

**Reset and LCD-off sites** (add the RGB equivalents beside them):
- `:1330-1331` `memset(m->frame_working, 0, ...)` / `memset(m->frame_completed, 0, ...)`; `:1332` `frame_generation = 0`.
- `:1837` LCD-off `memset(m->frame_working, 0, sizeof(m->frame_working));` add the CGB-profile `rgb_working` fill with `0x7FFF`.
- `:2429` completion `memcpy(m->frame_completed, m->frame_working, sizeof(m->frame_completed));` gate on profile so only the active store is copied.

**`gbb_copy_frame` validation block to duplicate** (`:2705-2736`, read this session). For `gbb_copy_frame_rgb555` copy verbatim and change: min pitch `GBB_FRAME_WIDTH * 2u`; add `((uintptr_t)(void *)pixels & 1u)` and `(pitch_bytes & 1u)` rejections BEFORE the overlap block; replace the profile gate with `if (!model_is_cgb(instance)) return GBB_UNSUPPORTED_PROFILE;` carrying a `CGB_ONLY` tag with `GUARD=model_is_cgb` within 12 lines; row copy of `GBB_FRAME_WIDTH * 2u` bytes from `rgb_completed`. Key excerpt (do not refactor the DMG function, D-03):
```c
    if (instance == NULL || pixels == NULL || out_info == NULL) return GBB_INVALID_ARGUMENT;
    if (pitch_bytes < GBB_FRAME_WIDTH ||
        pitch_bytes > (SIZE_MAX - GBB_FRAME_WIDTH) / (GBB_FRAME_HEIGHT - 1u))
        return GBB_INVALID_ARGUMENT;
    size_t required = (GBB_FRAME_HEIGHT - 1u) * pitch_bytes + GBB_FRAME_WIDTH;
    if (capacity_bytes < required) return GBB_INVALID_ARGUMENT;
    ...
    if (pixels_begin < info_end && info_begin < pixels_end) return GBB_INVALID_ARGUMENT;
    /* MODEL: DMG_ONLY GATE-57 GUARD=model_is_dmg -- ... */
    if (!model_is_dmg(instance)) return GBB_UNSUPPORTED_PROFILE;
    if (instance->frame_generation == 0) return GBB_FRAME_NOT_READY;
```
Note the DMG function is tagged `MODEL: BOTH GATE-00 basis=see-branch-gates`; GATE-57 stays.

**Tag discipline:** every new top-level function needs a `/* MODEL: ... */` comment line directly above (scanner R1, `tests/scripts/verify-model-gates.py`); next free id is GATE-76. Never quote mutant anchor strings inside tags.

---

### `include/gabbaboy/gabbaboy.h` (public API, append-only)

**Analog:** `gbb_info` handshake (`gabbaboy.h:325-355`) and `_Static_assert(sizeof(gbb_info) == GBB_INFO_SIZE_V1, "gbb_info layout");` at `src/core/gabbaboy.c:318`. Copy the struct_size convention for `gbb_compat_palette` (V1 28u, assert in the `.c`), the out-param comment style (every error case, "Outputs are left unchanged on any error") for `gbb_copy_frame_rgb555` and `gbb_get_compat_palette`. Rewrite stale comments at `:13-16`, `:128-136`, `:245-260`. `gbb_frame_info` (`:121-126`) is reused unchanged (D-41).

---

### `tests/CMakeLists.txt`: `gbb_colour_mutant` (config, batch)

**Analog:** `gbb_banking_mutant` (`tests/CMakeLists.txt:243-278`; excerpt in this session). Copy the function: `CMAKE_CONFIGURE_DEPENDS`, `file(READ)` of the core, `string(FIND)` forward and `REVERSE` exactly-once guard with `message(FATAL_ERROR ...)`, `string(REPLACE)`, `file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_*_mutant_<name>.c)`, STATIC library with `GBB_BUILD_REVISION="...-mutant" GBB_BUILD_QUALIFIED=0`, test executable linked to the mutant library, then two `expect_exit.cmake` tests (failing case expects exit 1 plus regex naming the REQUIRE; control case expects exit 0).
```cmake
function(gbb_banking_mutant name fail_test control_test anchor replacement failing_case failing_regex control_case)
  string(FIND "${gbb_banking_core_text}" "${anchor}" first)
  string(FIND "${gbb_banking_core_text}" "${anchor}" final REVERSE)
  if(first EQUAL -1 OR NOT first EQUAL final)
    message(FATAL_ERROR ...)
  endif()
  string(REPLACE "${anchor}" "${replacement}" text "${gbb_banking_core_text}")
```
Colour sibling differences: the executable source is `test_cgb_colour.c` (public API), so the sibling takes the test source and the case args as parameters (banking hard-codes `test_banking.c`). Anchors must occur once after the colour dispatch lands (for example the new `rgb_working` dispatch line; the `0x7FFF` LCD-off fill; the `& 0x7FFFu` mask in `cram_colour`; the `bg_attr & 7` palette select). Mutants required: colour path writes `frame_working` (D-25), resolve at frame completion (D-23.4), inverted LCDC.0, object-order X in CGB mode, no increment on blocked write, wrong OBJ set in compat, `ppu_disabled_state` no mode-0 on LCD off.

**Registration pattern for cases:** `foreach(case ...) add_test(NAME ${case} COMMAND test_x ${case} ${DIR})` (`:229-232`). Insert all new tests before `gabbaboy_verify_registered_tests()` (last line of file) and list them in `tests/expected-tests.txt` in the same commit. Wrap each plan's tests in a delimited comment block (RESEARCH parallelism note).

---

### `tests/test_cgb_colour_internal.c` and truth table (test, transform)

**Analog:** `tests/test_banking_internal.c` / `tests/test_mbc5_internal.c`: `#include "../src/core/gabbaboy.c"`, no link to `GabbaBoy::core` (duplicate symbols), `target_include_directories(... PRIVATE "${PROJECT_SOURCE_DIR}/include")`, drive `read8`/`write8` and read `m->bg_cram`, `m->frame_working`, `m->rgb_working` directly. `tests/test_cgb_tables.c` is the second include-the-core precedent (CMake at `tests/CMakeLists.txt:1784-1787`). Truth-table literals: generated `tests/data/cgb-priority-truth.inc` from a stdlib Python generator (separate language from the implementation, `python3 -I`), plus a CTest that regenerates and compares bytes, an asserted row count equals the full product, and a hand-written golden subset quoting Pan Docs (RESEARCH Open Question 2; GB-CPU-002: never derive from `ppu_compose_cgb`).

---

### `tests/test_cgb_visibility.c` and `tests/test_cgb_tables.c` (rewrite for the flipped cells)

**Analog:** self. Spots to rewrite from the D-10/D-11 decisions rather than from code: `deferred_reads` (`:348-349` includes `0xFF69, 0xFF6B, 0xFF6C`), `deferred_writes` (`:385`), the compat note (`:397`), CGB cells (`:697-701`, e.g. `add_cell(V_CGB, 0xFF69, STOP, 0x5A, STOP, 0xA5, STOP, K_DEF_RW, 11, "D-10 BCPD")`), `:719`. In `test_cgb_tables.c` add `render_io` strings for the new kinds (`:277-303`), grow `field_names[]` (`:25-39`) in table order, and add a `compat_palette` mode beside `emit`/`emit_io` (main at `:452-456`; mutated-doc controls follow `cgb_tables_postboot_mutated_doc`, `tests/CMakeLists.txt:1807-1809`).

---

### `fixtures/cgb-colour/` + `tests/scripts/reproduce-cgb-colour.sh` + CI step (fixture, file-I/O)

**Analog:** `fixtures/cgb-banking/` and `tests/scripts/reproduce-cgb-banking.sh` (exact). Layout: `banking.asm`, two `.gb`, `manifest.json`, `LICENSE.txt`.

**Manifest keys to copy** (`fixtures/cgb-banking/manifest.json`): `id`, `source`, `source_identity`, `source_sha256`, `license`, `build{assembler "RGBDS", version "1.0.1", archive, archive_sha256 "2f6f13c6...", ci_archive, ci_archive_sha256 "80a5cad8...", recipe, committed_bytes_toolchain}`, `fixtures[]{file,size_bytes,sha256}` (the `fixtures[]` array form is what `cmake/VerifyFixtureManifest.cmake` consumes), `cartridge`, `profile`, `protocol{markers,result_bytes,expectation_selection,variants,negative_controls,patch_offsets,timeout_half_dots}`, `evidence_class` ("original software fixture plus synthetic oracle, not hardware evidence"), `scope_limits[]`. Build recipe copy: `rgbasm -o ... && rgblink -n ... && rgbfix -c -v -p 0 ...`.

**Test registration** (`tests/CMakeLists.txt:225-232`):
```cmake
set(GBB_CGB_BANKING_DIR "${PROJECT_SOURCE_DIR}/fixtures/cgb-banking")
add_test(NAME cgb_banking_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DMANIFEST=${GBB_CGB_BANKING_DIR}/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixtureManifest.cmake)
foreach(case cgb_banking_guest_cgb ... )
  add_test(NAME ${case} COMMAND test_banking ${case} ${GBB_CGB_BANKING_DIR})
endforeach()
```
Name the new set `cgb_colour_fixture_digest`, `cgb_colour_guest_*`.

**CI:** add a step beside the cgb-banking one (`fixture-repro.yml:147` `bash tests/scripts/reproduce-cgb-banking.sh`, preceded by the `GBB_RGBDS_ARCHIVE`/`GBB_RGBDS_ARCHIVE_SHA256` env as in the mbc5 step excerpted in 10-PATTERNS) and extend the pin-consistency block (`:32-62`: `cgb_banking = json.loads(...)`, `cgb_banking_build = cgb_banking['build']`, `build.get(key) != cgb_banking_build.get(key)`) with `cgb-colour`. Add `.gitattributes` entries (`fixtures/cgb-banking/*.gb -text` precedent, `.gitattributes:56-60`).

**Guest protocol:** WRAM result markers read via `gbb_peek_ram` after halt (C000 `0xA5` pass / `0xEE` fail), as in `cgb_banking_*`. The HBlank-per-line fixture and compat/LCDC.0/LCD-off fixtures are checked through `gbb_copy_frame_rgb555` digests (needs the RGB555 call, so those tests land with plans 11-07 and 11-08).

---

### `fixtures/magentests/` extension + `tests/test_magentests.c` (third-party fixture)

**Analog:** the existing `fixtures/magentests/` (files: `ELIGIBILITY.md`, `LICENSE.txt`, `SOURCES.md`, `manifest.json`, three `.gbc`).

**Manifest entry shape** (`manifest.json`): `{alias, file, size_bytes, sha256, cartridge_type}`; add `source_dir`, `rgbfix_options`, `cgb_flag` per RESEARCH. SHA-256 and `$143` values for the three new ROMs are in RESEARCH "MagenTests details" (re-download to verify at plan time, A8).

**Repro script change** (`reproduce-magentests.sh`): `self_check` demands `len(entries) != 3` fail (replace with a per-ROM table of name, source dir, rgbfix options; `bg_oam_priority` builds from `src/color_bg_oam_priority`); header comment says "three mbc_oob_sram". Keep the `--self-check`/`--compare` modes, pinned upstream commit and hardware.inc `21ef22d`, `rgbds_version=v0.6.1`, and "never copies rebuilt bytes over committed fixtures".

**Test driver** (`test_magentests.c`): copy the shape of `read_file`, `FRAME_HALF_DOTS 140448u`, the per-frame `gbb_run` loop accepting `GBB_STOP_BUDGET`/`GBB_STOP_HALTED_IDLE`, and the `negative_control` byte-patch-and-recheck-checksum idiom (`rom[0x149u]=0x03u` then recompute `0x14D` over `0x134..0x14C`). Differences: create `GBB_PROFILE_CGB_CPU_E`, use `gbb_copy_frame_rgb555` with `uint16_t pixels[23040]` and pitch 320, run 20 frames, assert the last two completed frames are byte-identical, then a literal RGB555 structural predicate per ROM (not shade histogram). Existing `expect_screen` is DMG/shade only; add a sibling `expect_rgb555_*` rather than editing it. Registration copy: `tests/CMakeLists.txt:679-696` (`add_executable(test_magentests ...)`, `magentests_fixture_digest` via `VerifyFixtureManifest.cmake`, per-case `add_test`). New names use `magentests_cgb_*`. Core mutants for these ROMs go through `gbb_colour_mutant`; note `oam_internal_priority` cannot use the X-order control (RESEARCH Correction 4).

The redistribution guard `magentests_not_installed` (`tests/CMakeLists.txt:1210-1233`) reads the manifest digest list, so it covers new files automatically.

---

### `src/accept/gbb_accept.h` / `digest.c` / runner (utility + runner, transform)

**Analog:** `gbb_accept_rgb_digest`, `gbb_accept_rgb_digest_bin`, `gbb_accept_write_ppm`, `gbb_accept_frame_distinct_shades` (`gbb_accept.h:205-216`; `digest.c:56-75` for PPM). Add `gbb_accept_rgb555_digest(_bin)`, `gbb_accept_write_ppm_rgb555`, and a one-line shared expansion helper `(c << 3) | (c >> 2)` beside them; header label distinct from `GBB_ACCEPT_RGB_HEADER` (suggest `"GBB-RGB555LE-v1 160x144\n"`) then little-endian byte pairs. Return convention copied: 0 on success, nonzero on invalid input (value above `0x7FFF`), out not written. Tests: extend `tests/test_acceptance_digest.c`.

**Runner:** `src/runner/acceptance.c:185-197` currently does `gbb_copy_frame(...)` then `gbb_accept_rgb_digest_bin(st->scratch, FRAME_PITCH, bin)` with errors `"frame-skipped"`/`"frame-invalid"`; branch on profile, copy to a `uint16_t` scratch via `gbb_copy_frame_rgb555`, digest with the RGB555 sibling, print a distinct key (not `frame_hit=`). Same at `:721`, `:726`. DMG output lines stay byte-identical (`tests/scripts/verify-dmg-baseline.sh`); new cases must not add `acceptance.*` keys to the frozen ledger.

---

### `src/player/main.c`, `session.c`, `colour.[ch]` (player adapter, request-response)

**Analog:** self.

**Frame upload, DMG branch untouched** (`main.c:642-671`): keeps `gbb_copy_frame` into `uint8_t shades[...]`, expands via `player_palette_rgba[shade]`, `SDL_UpdateTexture(app->texture, NULL, rgba, (int)(PLAYER_FRAME_WIDTH * 4u))`, sets `displayed_generation`/`needs_redraw`. Add a CGB branch (selected by `gbb_get_info` profile, not the flag) that calls `gbb_copy_frame_rgb555` with `uint16_t` buffer and byte pitch 320, expands with `player_rgb555_to_rgba` from the new SDL-free `colour.c` (analog for the SDL-free module split: `src/player/presentation.[ch]`), then the same `SDL_UpdateTexture`. The texture is already RGBA32 streaming (`:584`).

**Title** (`format_window_title`, `:692-705`): single `snprintf` of `"GabbaBoy | %s | %s | Gain %u%% | %s | ... | %s"`; add the mode token additively so `run_smoke` assertions (`:2013-2026`) stay valid.

**Profile sites** (verified greps): `gbb_create(GBB_PROFILE_DMG_CPU_B` at `:150`, `:500`, `:919`, `:1718`, `:1964`, `:2202`. Route `:500`, `:919`, `:2202` through `select_profile`; keep `:150`, `:1718`, `:1964` explicit DMG with a comment (RESEARCH Correction 2). Sample of the pattern at `:2202`:
```c
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &app->machine) != GBB_OK) {
        fputs("Could not create the DMG-CPU-B machine\n", stderr);
        goto done;
    }
```

**Smoke contract to copy** (`run_script_smoke`, `:2190-2238`): prepare then `return 2` on bad input, `app->skip_final_save = true`, create machine, load ROM via `player_session_replace_rom`, compare `rom_sha256` identity, run, print one `smoke_report ...` line, `code = hit && ... ? 0 : 1`, `done:` releases. New `--smoke-colour` mode follows this exit-code contract (0 pass, 1 predicate miss, 2 bad input). Surface pixel sampling: copy `smoke_read_demo_target_pixel` (`:842-857`, `SDL_LockSurface`, `memcpy(rgba, pixel, 4u)`); per-frame driver: `smoke_render_next_frame` (`:829-840`). Argv grammar: `main()` `:2272-2323` (unknown arguments rejected, usage string at `:2320`); parse `--model` first.

**Probe helper:** `player_session_replace_rom` (`session.c:221-268`) reads the file itself; add `player_session_probe_profile(path, model, &profile, err)` reusing `read_rom_file` and `gbb_probe_rom` (header `$143` bit 7; PGB is an error).

**Limitations text** (`limitations.h`, macro `GBB_PLAYER_LIMITATIONS_TEXT`, currently "Audio uses a scoped DMG-CPU-B digital APU software model ..."): pinned verbatim by `tests/player/test_limitations.c`; edit text, test, README, `show_help`/`print_player_help` (`main.c:375-401`, `:719-758`) and the two `capability_limits` strings in `.github/workflows/preview.yml` (`:51`, `:98`) in one commit.

**Player CTest registration:** `tests/player/CMakeLists.txt` dispatches by `elseif(test_name STREQUAL ...)` / `MATCHES` (e.g. `:94-146`, `player_smoke` at `:141-146` with a `HOME=` environment); a new `player_cgb_*` branch is required or configure ends in `FATAL_ERROR "Unknown optional player test in inventory"`; names go in `tests/player/expected-tests.txt` with the `player_` prefix. Mutant builds for R/B swap and grey path: configure-time copies as in the core mutant pattern, applied to `colour.c`.

---

### `tests/consumers/{c,cpp}` (installed consumer)

**Analog:** `battery_api_smoke` / `cgb_api_smoke` in `tests/consumers/c/main.c`: hand-built ROM with checksum loop, `goto done` error flow, `0xA7` sentinel fill to prove outputs are untouched on error. Add the `gbb_copy_frame_rgb555` argument matrix and `gbb_set/get_compat_palette` calls inside the existing executable (no new CTest names; the api-coverage gate is satisfied by the calls). Replace the "no colour output" comment.

---

### `tests/measure_core.c` + A/B benchmark (utility, batch)

**Analog:** self (`argc != 3` rejection at `:92-107` accepts only `--trace`/mode, DMG-only create at `:150`) plus `tests/scripts/measure-release-baseline.sh --ab` and the `cgb_bench_ab_*` registrations at `tests/CMakeLists.txt:1843-1875` (copy `gbb_add_bench_ab_control` for any new control). Add the CGB workload as a profile option on a copy or a sibling target; the base at `3012e8f` lacks it, so overlay head source onto the base build (RESEARCH Correction 13). Record in `11-BENCH.md` following `10-BENCH.md`. DMG tracer digest to enforce on both: `correctness_digest_fnv1a64=4c7a57ff3d50d228`.

---

### `docs/*` (docs, transform)

**Analog:** marker-bounded tables mirrored by C tests (`docs/cgb-profile.md` between `<!-- cgb-post-boot-begin -->` (:31) and `-end` (:193); io rows ~`:366-377`; prose `:200-206`), `docs/model-gates.md` rows (the 14 `research:11` rows at `:47,55,58,59,65,73,88-95` need dispositions), and the doc-contract path: `cgb_native_guide_contract` (`tests/CMakeLists.txt:1553-1570`) with `GBB_NATIVE_GUIDE_CGB_DECLS` and a missing-phrase selftest (`:1573-1580`). Every `gbb_`/`GBB_` token in `docs/native-integration.md` must be declared in the header; keep the phrase ``returns `GBB_UNSUPPORTED_PROFILE` on the CGB profile`` (guide `:132-133`). `docs/support/unreleased.md` lines 39 and 42 say "no colour output" (checked by `tests/scripts/verify-support-ledger.py`).

---

## Shared Patterns

### Registration discipline
**Source:** `cmake/ExpectedTests.cmake`, last line of `tests/CMakeLists.txt` (`gabbaboy_verify_registered_tests()`), `tests/player/CMakeLists.txt:231-237`
**Apply to:** every new `add_test` (including mutants and selftests). Core names to `tests/expected-tests.txt` (prefixes `cgb_`, `palette_`, `magentests_cgb_`), player names to `tests/player/expected-tests.txt` (prefix `player_cgb_`). Both fail configure on mismatch.

### Configure-time mutant with exactly-once anchor
**Source:** `tests/CMakeLists.txt:243-278` (`gbb_banking_mutant`)
**Apply to:** all core mutant controls in plans 11-01, 11-03, 11-05, 11-06, 11-07, 11-08 and 11-10.

### Exact-exit negative controls
**Source:** `tests/expect_exit.cmake` (`GBB_CMD`, `GBB_EXPECT_CODE`, `GBB_EXPECT_REGEX`, optional `GBB_FORBID_REGEX`, `GBB_WORKDIR`)
**Apply to:** every verifier or mutant expecting a specific failure.

### Table-first, doc-mirrored change
**Source:** `post_boot[]` (`gabbaboy.c:759-899`), `io_visibility[]` (`:1199-1203`), `tests/test_cgb_tables.c`, `docs/cgb-profile.md`
**Apply to:** CRAM and OPRI rows and the 12 compat palette values.

### Fixture provenance
**Source:** `fixtures/cgb-banking/manifest.json`, `fixtures/magentests/{manifest.json,ELIGIBILITY.md,SOURCES.md}`
**Apply to:** `fixtures/cgb-colour/`, the three MagenTests ROMs. Pinned tool versions, digests, `scope_limits[]`, no hardware claim for original fixtures.

### DMG byte-identity gate
**Source:** `tests/scripts/verify-dmg-baseline.sh`, `tests/baseline/*`, `banking_tracer_digest_unchanged`
**Apply to:** every plan touching `src/core/gabbaboy.c`, `src/runner/*`, `src/accept/*`.

### Model-gate tags
**Source:** `tests/scripts/verify-model-gates.py`, `docs/model-gates.md`; tag examples at `gabbaboy.c:1255` (`CGB_ONLY GATE-70 GUARD=model_is_cgb`), `:2705` (`BOTH GATE-00 basis=...`), `:1387` (`UNKNOWN GATE-13 research:11`)
**Apply to:** every new top-level function and model-differing branch.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `src/player/colour.c` / `colour.h` | utility | transform | No existing RGB555 helper; `presentation.[ch]` is only a structural analog (SDL-free module). Use RESEARCH's expansion oracle `(c << 3) \| (c >> 2)`. |
| player RGBA digest + `--smoke-colour` | player e2e | request-response | The player has no RGBA digest or ROM-path argument today (only `rom_sha256`/`pcm_sha256` in `run_script_smoke` and a single-pixel `smoke_read_demo_target_pixel`). Combine the script-smoke contract with the shared SHA-256 and surface sampling above. |

## Metadata

**Analog search scope:** `src/core`, `src/accept`, `src/runner`, `src/player`, `include/gabbaboy`, `tests/` (CMakeLists, test_magentests.c, test_cgb_*.c, measure_core.c, player/), `tests/scripts/`, `fixtures/{cgb-banking,magentests}`, `.github/workflows/`
**Files scanned/read for excerpts:** about 25 (plus the three required-reading documents)
**Tracked-source gate (#3645):** `git ls-files` confirmed for fixtures, repro scripts, `test_magentests.c`, `measure_core.c`, `test_cgb_*.c`, `verify-model-gates.py`, `digest.c`, `test_acceptance_digest.c`, `fuzz_core.c`, player test files; `src/player/colour.[ch]` do not exist yet (new files).
**Pattern extraction date:** 2026-10-12
