---
phase: GB-11-cgb-colour-rendering-and-player-colour
reviewed: 2026-10-13T00:00:00Z
depth: standard
files_reviewed: 46
files_reviewed_list:
  - .gitattributes
  - .github/workflows/fixture-repro.yml
  - .github/workflows/preview.yml
  - .gitignore
  - fixtures/cgb-colour/attr.asm
  - fixtures/cgb-colour/compat.asm
  - fixtures/cgb-colour/cram.asm
  - fixtures/cgb-colour/hblank.asm
  - fixtures/cgb-colour/lcdoff.asm
  - include/gabbaboy/gabbaboy.h
  - src/accept/digest.c
  - src/accept/gbb_accept.h
  - src/core/gabbaboy.c
  - src/player/colour.c
  - src/player/colour.h
  - src/player/limitations.h
  - src/player/main.c
  - src/player/session.c
  - src/player/session.h
  - src/runner/acceptance.c
  - src/runner/acceptance.h
  - tests/CMakeLists.txt
  - tests/cgb_consumer_symbol_coverage.cmake
  - tests/check_no_phase11_rows.cmake
  - tests/consumers/c/main.c
  - tests/consumers/cpp/main.cpp
  - tests/fuzz_core.c
  - tests/measure_core.c
  - tests/player/cgb_smoke.cmake
  - tests/player/claims_agree.cmake
  - tests/player/test_colour.c
  - tests/player/test_limitations.c
  - tests/player/test_session.c
  - tests/scripts/gen-cgb-priority-truth.py
  - tests/scripts/reproduce-cgb-colour.sh
  - tests/scripts/reproduce-magentests.sh
  - tests/scripts/rgb-digest-vector.py
  - tests/scripts/run-acid2-local.py
  - tests/scripts/verify-external-dispositions.py
  - tests/test_acceptance_digest.c
  - tests/test_cgb_colour.c
  - tests/test_cgb_colour_internal.c
  - tests/test_cgb_tables.c
  - tests/test_cgb_visibility.c
  - tests/test_fuzz_core.c
  - tests/test_magentests.c
findings:
  critical: 0
  warning: 3
  info: 5
  total: 8
status: issues_found
---

# Phase 11: Code Review Report

**Reviewed:** 2026-10-13T00:00:00Z
**Depth:** standard
**Files Reviewed:** 46
**Status:** issues_found

## Summary

Reviewed the Phase 11 diff (`3012e8f..HEAD`) of the C17 core, public header, acceptance and player adapters, test drivers, CMake mutant harness and the bash/python scripts. The two large files (`src/core/gabbaboy.c`, `tests/CMakeLists.txt`) were reviewed on their Phase 11 diff only.

The core colour path holds up under adversarial reading:

- **Frame copy (D-15):** `gbb_copy_frame_rgb555` validates NULL arguments, then pointer and pitch alignment, then pitch and capacity overflow, then the `out_info` overlap, and only then profile and not-ready. Nothing is written before the copy loop, so no-write-on-error holds.
- **Compat palette (D-17/D-17a):** `gbb_set_compat_palette` validates every entry (bit 15 rejected, never masked) before the first store. `gbb_get_compat_palette` writes nothing on error, `struct_size` included.
- **CRAM (D-11/D-12):** every CRAM index is masked to 6 bits, so no guest byte reaches outside the 64-byte arrays. The auto-increment wraps inside bits 0-5. The blocked-write increment and the lock predicate follow the decisions.
- **VRAM and frame bounds:** the CGB map and tile fetches stay inside the 8 KiB bank (`0x1C00 + 1023 < 0x2000`, tile bases checked against `0x1800`). `rgb_working` and `rgb_completed` are indexed by `ly * 160 + slot`, which is bounded by the transfer logic.
- **DMG shade path (D-02/D-25):** the shade store is written only under `model_is_dmg`. The compat and CGB branches write only the RGB store.
- **Compat default ramp:** the four `compat_default_rgb555` literals match the stated rule (R = Y, G = Y - (Y>>3), B = Y - (Y>>2)).
- **Privacy:** a grep of all in-scope files for home paths, emails and personal identifiers found nothing.

No Critical defects were proven. The remaining findings are one negative control that cannot fail for the reason it claims, one script exit-code collision, one pin-comparison gap, and minor robustness and diagnosability points.

## Warnings

### WR-01: `magentests_cgb_ppu_disabled_state_compat` cannot distinguish a passing guest from a failing one

**File:** `tests/test_magentests.c:216-245` (comment at 213-215; also `fixtures/magentests/ELIGIBILITY.md:41`)
**Issue:** The compat variant runs the same ROM with `$143` cleared and asserts that every pixel equals `palette.bg[0]`. In compat mode the guest's CRAM writes are ignored, so the green (pass) and red (fail) verdicts, which are both delivered through CRAM, are invisible.

Disassembling the ROM at `0x183..0x1A5` shows both verdict paths:

- Pass path: `ld a,0`, then `sla a` twice, then `ld [$FF47],a`, so BGP = `0x00`.
- Fail path: `ld a,3`, then `sla a` twice, then `ld [$FF47],a`, so BGP = `0x0C`.

BGP `0x0C` still maps colour index 0 to shade 0, and the blank background is all colour index 0. So a guest that read the wrong STAT mode after switching the LCD off renders the identical uniform frame. The comment's claim "the pass path writes BGP = 0" is true but does not discriminate. The test therefore passes for a reason unrelated to the STAT mode-0 behaviour it is named after.

**Fix:** Make the verdict observable in compat mode, or stop presenting the test as a STAT check. For example, read the guest's own verdict from WRAM or a register (as `cgb_colour_guest_cram` does with `$C000`), or assert on the machine state after the LCD-off sequence (`gbb_peek_ram`, or the `m->bgp` white-box value `0x00` versus `0x0C`). If neither is possible for this upstream ROM, rename the case to describe what it actually proves (compat mode ignores CRAM and renders the default BG shade 0) and drop the claim in `ELIGIBILITY.md` that it checks STAT.

### WR-02: `run-acid2-local.py` uncaught errors exit 1, the same code as "frames differ"; pin check and use are separate reads

**File:** `tests/scripts/run-acid2-local.py:226-255`
**Issue:** `main()` returns exit 1 from `compare()` for "acid2 result=differs". The manifest load (`json.loads(args.manifest.read_text())`, line 239) and the `manifest["kinds"][args.rom_kind]` and `manifest["ldbb_budget_half_dots"]` lookups sit outside the `try`. A missing or corrupt manifest, or a missing key, raises an uncaught exception, and Python exits 1 with a traceback. A caller or CI step that keys on "exit 1 means rendering differs" would misread a harness failure as an emulator mismatch.

Separately, `check_pins` hashes `rom` and `reference` (lines 38-45), and `run_core` then copies the ROM again (`shutil.copyfile`) and `main` re-reads the reference. A file swapped between the hash and the use bypasses the T-11-19 pin. This is a local-only tool, so exploitability is low, but the stated guarantee ("refused before it is run or decoded") is not actually enforced.

**Fix:** Read each input once into memory, hash those bytes, and pass the same bytes onward (write the pinned ROM bytes into the temp dir instead of copying the original path, and decode the PNG from the hashed bytes). Move the manifest load and key lookups inside the `try` and map `KeyError`/`json.JSONDecodeError` to `acid2 error:` with exit 3.

### WR-03: `reproduce-cgb-colour.sh` pin comparison passes when both manifests omit a key; `fail` mislabels tool failures

**File:** `tests/scripts/reproduce-cgb-colour.sh:55-57, 45-47, 99-101`
**Issue:**
- (a) The check `build.get(key) != ref.get(key)` is `None != None` (false) if the pin key is absent from both the colour and cgb-banking manifests. A deleted `archive_sha256` or `ci_archive_sha256` in both files passes the equality gate. The only absolute pin enforced is `version == '1.0.1'`. A later `build['archive_sha256']` then raises `KeyError`, only when `GBB_RGBDS_ARCHIVE` is set, and it surfaces as a traceback with exit 1 rather than a clean failure.
- (b) `fail()` always prints `result=differs`, including for `tool-failed-*`, bad recipe and bad manifest conditions. The captured rgbasm, rgblink and rgbfix stderr is discarded (`capture_output=True` and never printed), so a tool failure is reported with no cause. Consumers that grep `result=differs` for a byte difference get false positives.

**Fix:**
```python
for key in ('assembler','version','archive','archive_sha256','ci_archive','ci_archive_sha256'):
    if not build.get(key) or build.get(key) != ref.get(key):
        fail(f'build-pin-{key}-missing-or-differs-from-cgb-banking')
```
Print `result=error reason=...` for non-comparison failures and include `done.stderr[:200]` in the `tool-failed-*` message.

## Info

### IN-01: `create_machine` gives the CGB-only note a different precedence than `replace_session_rom`

**File:** `src/player/main.c:545-546` (compare 1055-1056)
**Issue:** In `replace_session_rom` the `cgb_only_note` is the lowest-precedence `else if` after the battery and catch-up status. In `create_machine` it is an unconditional `if (battery_loaded && ...)` that overwrites the "Battery RAM loaded; changes are in memory until saved" status set a few lines earlier. The two open paths therefore show different status text for the same ROM. The `battery_loaded` guard (true for every ROM without a battery save failure, not only battery carts) also reads like a copy error.
**Fix:** Mirror the `else if` chain: set the note only when no battery or catch-up message is pending, and use one helper for both sites.

### IN-02: `capture_format` silently falls back to the DMG store when `gbb_get_info` fails

**File:** `src/runner/acceptance.c:728-733`
**Issue:** `gbb_get_info(...) == GBB_OK && profile == CGB ? 1u : 0u` returns 0 (DMG format) on an info error. A CGB instance would then be driven through `gbb_copy_frame`, which returns `GBB_UNSUPPORTED_PROFILE`. The case would end as "frame-not-ready" with no hint, which is the silent-gap pattern the neighbouring D-43 comment says it wants to avoid. Also, `scratch_frame.pixels555[GBB_LDBB_FRAME_BYTES]` and `gbb_ldbb_capture.pixels555` use a macro named `..._BYTES` as an element count, and only the byte array has a `_Static_assert` on its size.
**Fix:** Treat an info failure as an error (`st->error = "frame-info-unavailable"`), and add `_Static_assert(sizeof(((scratch_frame *)0)->pixels555) == GBB_ACCEPT_FRAME_WIDTH * GBB_ACCEPT_FRAME_HEIGHT * 2u, ...)`.

### IN-03: `gbb_accept_rgb555_*` helpers dereference a misaligned or NULL-path argument without checking

**File:** `src/accept/digest.c:91-108, 143-146`
**Issue:** `rgb555_valid` checks the pitch parity but not the base pointer's 2-byte alignment before the `uint16_t` reads through `rgb555_row`. A misaligned base is undefined behaviour. `gbb_accept_write_ppm_rgb555` passes `path` straight to `fopen`, and `gbb_accept_rgb555_digest_bin` does not check `out`. The header documents the caller contract, and all current callers pass aligned `uint16_t` arrays, so this is hardening rather than a live bug.
**Fix:** Add `((uintptr_t)pixels & 1u) != 0u` to `rgb555_valid`, and `path == NULL`/`out == NULL` guards returning a nonzero code.

### IN-04: Mutant failure regexes are single common words in several controls

**File:** `tests/CMakeLists.txt:2257 ("row"), 2293 ("0x001F|pixel"), 2302 and 2309 ("pixel"), 2151/2157/2169 ("bgcol"/"objcol")`; `tests/fuzz_core.c:44-47`
**Issue:** `gbb_colour_mutant` asserts exit 1 plus a bare substring. "row" also appears in the text of the unrelated `REQUIRE(hblank_row_matches(...))`, and "pixel" in any pixel-compare message. A mutant that broke the fixture earlier in the case with a different `REQUIRE` containing the same word would satisfy the control. The paired `_control` test and the anchor-once check limit the practical risk, so I rate this Info. Separately, every `require_contract` failure in `fuzz_core.c` now reports the same text `contract violated`, which lost the call-site detail that `abort()` plus a core dump previously preserved.
**Fix:** Tighten the regexes to the full diagnostic (for example `row [0-9]+ is not uniform`), and pass `__LINE__` or a message into `require_contract` for the standalone build.

### IN-05: `cgb_measure_core_unknown_profile` exercises `--profile dmg`, not an unknown name

**File:** `tests/CMakeLists.txt:2423-2428`
**Issue:** The case is described as "an unknown profile name is a usage error", but it passes `dmg`, which is a perfectly plausible valid profile name that `measure_core` simply does not accept (the parser only recognises `--profile cgb`). The control passes, but it would keep passing if `dmg` were later added as a valid value, and no genuinely unknown token such as `--profile bogus` is covered.
**Fix:** Use `--profile bogus` (or both), and keep the name consistent with what is tested.

---

_Reviewed: 2026-10-13T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
