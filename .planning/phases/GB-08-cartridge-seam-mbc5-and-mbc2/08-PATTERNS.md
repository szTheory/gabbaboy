# Phase 8: Cartridge Seam, MBC5 and MBC2 - Pattern Map

**Mapped:** 2026-10-11
**Files analyzed:** 27 new/modified files
**Analogs found:** 25 / 27 (2 partial: no existing multi-suite runner selection, no existing per-address MBC2 style decode)

All analog paths below were checked with `git ls-files` and are tracked source (none is a gitignored mirror). Paths are repo-relative. Line numbers are as read at HEAD `3ab4031`.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/core/gabbaboy.c` (Cartridge mapper section, seam) | core mapper / service | request-response (bus read/write) | itself: MBC1 helpers `:412-436`, `read8` `:683-695`, `write8` `:744-774`, `read_supported` `:965-969`, `validate_header` `:1640-1680`, `gbb_load_rom` `:1707-1735`, battery calls `:1737-1779` | exact (in-place refactor) |
| `src/core/gabbaboy.c` (MBC5, MBC2 cases, rumble) | core mapper | request-response | MBC1 case in same section | role-match |
| `include/gabbaboy/gabbaboy.h` (`GBB_NO_RUMBLE`, `gbb_rumble_state`, comments) | public API | request-response | `gbb_battery_generation` (`gabbaboy.c:1773-1779`) and header battery docs `gabbaboy.h:140-157` | exact |
| `tests/test_mbc5.c` | test | request-response (guest program through bus) | `tests/test_cartridge.c` | exact |
| `tests/test_mbc2.c` | test | request-response + battery CRUD | `tests/test_battery.c` + `tests/test_cartridge.c` | exact |
| `tests/CMakeLists.txt` (new executables, tests, install scan, mutant hooks) | config | batch | existing `test_cartridge`/`test_battery` blocks `:23-44`, libbet block `:368-440` | exact |
| `tests/expected-tests.txt` | config | batch | itself (append `+` lines only) | exact |
| `src/runner/main.c` (`suite_def`, per-case `size_bytes`, `mbc_cases[]`) | runner adapter | batch / request-response | itself `:30-62`, `:70-103`, `:129-155`, `:211-237`, `:335-348` | exact (partial for suite selection) |
| `tests/test_runner.c` (touch only if identifiers change) | test | request-response | itself (`#include`s `src/runner/main.c`) | exact |
| `fixtures/mooneye-mbc/*` (15 `.gb`, `manifest.json`, `LICENSE.txt`, `SOURCES.md`, `ELIGIBILITY.md`) | fixture | file-I/O | `fixtures/mooneye/` | exact |
| `cmake/VerifyMooneyeMbc.cmake` | verification script | batch | `cmake/VerifyMooneye.cmake` | exact |
| `tests/scripts/reproduce-mooneye-mbc.sh` | repro script | batch | `tests/scripts/reproduce-mooneye.sh` | role-match (parent hard-codes dir and three names) |
| `fixtures/mbc5-banking/*` (`banking.asm`, `banking.gb`, `manifest.json`, `LICENSE.txt`) | fixture | file-I/O | `fixtures/mbc1-continuation/` | exact |
| `tests/scripts/reproduce-mbc5-banking.sh` | repro script | batch | `tests/scripts/reproduce-mbc1-continuation.sh` | exact |
| `cmake/ScanForbiddenFixtures.cmake` (or Python) | verification script | batch | `scan_dir` + `scan_self_test` in `tests/scripts/verify-libbet-admission.py:339-367, 700-715` | role-match (language differs; CMake recommended) |
| `cmake/PreviewPackageSmoke.cmake` (add scan of extracted prefix) | verification script | batch | itself `:56-80` | exact |
| `tests/acceptance/CMakeLists.txt` (ninth-bit mutant) | config | batch | JOYP mutant `:277-333` | exact |
| `.gitattributes`, `THIRD_PARTY_NOTICES.md` | config | n/a | existing libbet/mbc1-continuation rows | exact |
| `.github/workflows/fixture-repro.yml` (sibling leg, mbc5-banking step) | CI config | batch | `mooneye-candidate-repro` and MBC1 continuation step | exact |
| `src/player/session.c` / `session.h` (`battery_unsupported`) | adapter | request-response | `player_session_identify_rom` `:158-173` | exact |
| `src/player/main.c` (status string + stderr warning) | adapter / UI | event-driven | existing battery status branches (~`:511-520`, ~`:950-965`) | role-match |
| `src/player/limitations.h` + `tests/player/test_limitations.c` | config / text pin | n/a | `limitations.h` itself | exact |
| `tests/player/test_session.c` + `tests/player/expected-tests.txt` (`player_session_battery_unsupported`) | test | request-response | `tests/player/test_session.c:103-176` | exact |
| `docs/cartridge-and-saves.md`, `docs/native-integration.md:59`, `gabbaboy.h:23` comment | docs | n/a | themselves | exact |
| `tests/measure_core.c` | no change (advisory run only) | | | n/a |
| Scratch old-vs-new differential harness | one-off, not committed | batch | `tests/test_loader_fuzz.c` grid style | partial |
| `fixtures/mooneye/*`, `tests/baseline/*`, `cmake/VerifyMooneye.cmake` | MUST NOT CHANGE | | | n/a |

## Pattern Assignments

### `src/core/gabbaboy.c` Cartridge mapper section (seam plan, then MBC5 and MBC2 rows)

**Analog:** the existing MBC1 code in the same file. The seam is an in-place replacement; keep branch order (D-06).

**Instance fields to fold into `cart_state`** (lines 56-61):
```c
    uint8_t cartridge_type;
    uint8_t mbc1_rom_bank_low;
    uint8_t mbc1_rom_bank_high;
    uint8_t mbc1_mode;
    int mbc1_ram_enabled;
```
`battery_generation`, `cartridge_ram`, `cartridge_ram_size`, `rom`, `rom_size` stay as instance fields. `ROM_ONLY` must be enum value 0 because `gbb_create` uses `calloc` (`:1693`).

**MBC1 helpers to keep verbatim as the MBC1 case** (lines 412-436):
```c
static size_t mbc1_rom_bank(const gbb_instance *m, uint16_t address) {
    const size_t mask = mbc1_rom_bank_mask(m);
    if (address < 0x4000u)
        return m->mbc1_mode ? ((size_t)m->mbc1_rom_bank_high << 5) & mask : 0u;
    /* Translate zero before masking: a small ROM can disconnect upper lines. */
    const size_t low = m->mbc1_rom_bank_low == 0u ? 1u : m->mbc1_rom_bank_low;
    return (((size_t)m->mbc1_rom_bank_high << 5) | low) & mask;
}
```
The `<< 5` here is why a ninth-bit mutant pattern for MBC5 (`& 1u) << 8`) is unique.

**Reset pattern** (lines 438-442, inside `reset_state`, also run from `gbb_create` with `rom == NULL`):
```c
    m->mbc1_rom_bank_low = 1u;
    m->mbc1_rom_bank_high = 0u;
    m->mbc1_mode = 0u;
    m->mbc1_ram_enabled = 0;
```
Replace with a `mapper_reset()` safe on an unloaded instance. Rumble-line "count one change" must live in `gbb_reset` only (`:1704-1708`), not `reset_state`, or load would count a spurious change (P5).

**read8 cartridge branches** (lines 683-695):
```c
    if (address < 0x8000u) {
        if (m->rom == NULL || address >= m->rom_size) return 0xFFu;
        if (!cartridge_is_mbc1(m)) return m->rom[address];
        const size_t bank = mbc1_rom_bank(m, address);
        const size_t offset = bank * 0x4000u + (size_t)(address & 0x3FFFu);
        return offset < m->rom_size ? m->rom[offset] : 0xFFu;
    }
    if (address >= 0xA000u && address <= 0xBFFFu) {
        if (m->mbc1_ram_enabled && m->cartridge_ram != NULL &&
            m->cartridge_ram_size != 0u)
            return m->cartridge_ram[mbc1_ram_offset(m, address)];
        return 0xFFu;
    }
```
Turn into `switch (kind)`; keep the `offset < m->rom_size` guard on every kind. MBC2 enabled read returns the stored canonical byte (`0xF0|nibble`), index `address & 0x1FF`.

**write8 mapper registers** (lines 744-755): the MBC1 split `address < 0x2000 / < 0x4000 / < 0x6000 / else`. MBC5 uses `<0x2000` enable, `<0x3000` low 8 bits, `<0x4000` bit 8 (`value & 1`), `<0x6000` RAM bank (mask `0x0F`, or `0x07` plus bit 3 line on rumble types), `else` ignored. MBC2 splits `address < 0x4000` by `(address & 0x0100)`, NOT by `< 0x2000` (Pattern 3 in RESEARCH).

**write8 RAM + generation bump** (lines 762-774), the only `cartridge_type == 0x03u` literal besides `:1739`:
```c
        if (m->mbc1_ram_enabled && m->cartridge_ram != NULL &&
            m->cartridge_ram_size != 0u) {
            const size_t offset = mbc1_ram_offset(m, address);
            const uint8_t previous = m->cartridge_ram[offset];
            if (previous != value) {
                m->cartridge_ram[offset] = value;
                if (m->cartridge_type == 0x03u &&
                    m->battery_generation != UINT64_MAX)
                    ++m->battery_generation;
            }
        }
```
Replace the literal with the stored `has_battery` flag. For MBC2 compare against the canonical `0xF0 | (value & 0x0F)` before deciding to bump.

**read_supported fail-closed window** (lines 965-969): replace `cartridge_is_mbc1(m)` with the stored `ram_window_mapped` flag, keep the RAM-present term. Every MBC5 and MBC2 row must set it (P2, A4), or a guest read of `A000` stops with `GBB_STOP_UNSUPPORTED_BUS`.

**validate_header** (lines 1640-1680): keep this precedence verbatim, table-ize the middle:
```c
    if (rom == NULL || size == 0) return GBB_INVALID_ARGUMENT;
    if (size < 0x150) return GBB_ROM_TRUNCATED;
    if (size > GBB_MAX_ROM_SIZE) return GBB_ROM_TOO_LARGE;     /* becomes: > (MBC5 row ? 8 MiB : 2 MiB) */
    ...
    if (type != 0x00u && !is_mbc1) return GBB_UNSUPPORTED_CARTRIDGE;
    if ((!is_mbc1 && rom_size_code != 0u) || (is_mbc1 && rom_size_code > 0x06u))
        return GBB_UNSUPPORTED_ROM_SIZE;                        /* rom_size_code > row.max, BEFORE the shift */
    ... RAM rule (type 0/1 none; 2/3: code 2 -> 8192, code 3 and rom_code <= 4 -> 32768) ...
    const size_t declared = (size_t)32768u << rom_size_code;
    if (size < declared) return GBB_ROM_TRUNCATED;
    if (size != declared) return GBB_ROM_SIZE_MISMATCH;
    /* checksum -> GBB_INVALID_ROM; then MBC1M candidate -> GBB_UNSUPPORTED_CARTRIDGE_VARIANT */
```
The early ceiling is 2 MiB for every non-MBC5 type byte (including unknown rows), never the per-kind declared max (P3). `rom[0x147]` is safe to read there since `size >= 0x150`.

**gbb_load_rom validate-allocate-commit** (lines 1707-1735): preserve exactly; commit `cart_state` where `instance->cartridge_type = info.type;` is today; MBC2 RAM (512 bytes, `memset 0xFF`) comes from the row, not `$149`.
```c
    free(instance->rom);
    free(instance->cartridge_ram);
    instance->rom = copy;
    ...
    instance->battery_generation = 0u;
    instance->cartridge_type = info.type;
    reset_state(instance);
    instance->loaded = 1;
```

**Battery calls** (lines 1737-1779): `has_battery_ram` swaps `cartridge_type == 0x03u` for `has_battery`. Error order is `INVALID_ARGUMENT`, `NO_BATTERY`, `BUFFER_TOO_SMALL`/`BATTERY_SIZE_MISMATCH`. MBC2 import (D-21) adds normalise-then-compare-then-commit before the single `++battery_generation`:
```c
    if (size_bytes != instance->cartridge_ram_size) return GBB_BATTERY_SIZE_MISMATCH;
    if (memcmp(instance->cartridge_ram, bytes, size_bytes) != 0) {
        memcpy(instance->cartridge_ram, bytes, size_bytes);
        if (instance->battery_generation != UINT64_MAX)
            ++instance->battery_generation;
    }
```

**gbb_rumble_state** copy the argument/error shape of `gbb_battery_generation` (lines 1773-1779): NULL args return `GBB_INVALID_ARGUMENT`, not-applicable returns the new error, outputs untouched on any error.

**Do not touch:** `recognized_mbc1m_candidate` (`:1620-1638`), the JOYP anchor `if ((m->joypad_select & 0x20u) == 0)` (`:540`, must stay exactly once), DMA source reads (no cartridge access).

---

### `include/gabbaboy/gabbaboy.h`

**Analog:** the enum and battery docs.

**Append-only enum** (lines 18-35): add `GBB_NO_RUMBLE` after `GBB_FRAME_NOT_READY`. Update the comment on `GBB_ROM_TOO_LARGE` ("actual image exceeds the 2 MiB hard limit", line 23) to describe the type-aware 2 MiB/8 MiB ceiling.

**Doc-comment style to copy for `gbb_rumble_state`** (lines 140-157, battery block): states ownership, "On errors, output values ... remain unchanged", and generation/counter semantics. Update "raw RAM bytes" wording for MBC2 canonical bytes.

---

### `tests/test_mbc5.c` (test, request-response)

**Analog:** `tests/test_cartridge.c`

**Imports and REQUIRE macro** (lines 1-9):
```c
#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)
```

**Helpers to copy (the project prefers copy over a shared lib)** (lines 24-68): `new_machine`, `fix_checksum`, `make_banked_rom` (stamps `bank` at `bank*0x4000+0x1000`), `emit_mapper_write` (`LD A,n; LD (nn),A`), `emit_guest_read` (`LD A,(nn); LD (nn),A`). For ROMs larger than the 32 KiB header the stamp location `+0x1000` works for any bank; for MBC5 ROM codes use `bank_count = 2 << rom_code` (valid up to `$08` = 512 banks).

**Core guest-program pattern** (lines 70-115, `run_bank_case`): build program, copy to WRAM via a bootstrap so a remap of bank 0 cannot remove the code, `gbb_run(...) == GBB_STOP_HALTED_IDLE`, read results with `gbb_peek_ram`:
```c
    REQUIRE(gbb_load_rom(machine, rom, rom_size) == GBB_OK);
    const gbb_run_result run = gbb_run(machine, 4096u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_HALTED_IDLE);
    REQUIRE(gbb_peek_ram(machine, 0xC100u) == expected_lower);
```
`gbb_peek_ram` serves only WRAM/HRAM (`gabbaboy.c:2305-2311`), so cartridge reads must go through the guest or `gbb_copy_battery`. MBC5 bank 0 at `$4000` needs the same WRAM bootstrap only if the program lives in the switchable window; bank 0 fixed at `$0000-$3FFF` means the program can stay in bank 0.

**Test dispatch** (lines 277-284):
```c
int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "cartridge_tracer") == 0) return cartridge_tracer();
    ...
    return 2;
}
```
Test names (proposals from RESEARCH validation map): `mbc5_header_matrix`, `mbc5_rom_banking`, `mbc5_ram_*`, `mbc5_rumble_*`, `mbc5_rom_bound`, `mbc5_cgb_flag_ignored`, `mbc5_cross_mapper_control`, `mbc5_bank_1ff`, `mbc5_banking_guest`. The `$1FF` test inflates 8 MiB in memory: set `rom[0x148]=8`, write marker at `0x1FF*0x4000+0x1000`, `fix_checksum`, total length `8 MiB` exactly (P19). Size-bound tests copy `tests/test_loader_fuzz.c` style (2 MiB+1 and `SIZE_MAX` on type `$01` still `GBB_ROM_TOO_LARGE`, previous guest state intact).

---

### `tests/test_mbc2.c` (test, request-response + battery)

**Analog:** `tests/test_battery.c` for battery round trips, `tests/test_cartridge.c` for guest register probes.

**make_rom / roundtrip pattern** (test_battery.c lines 18-72):
```c
static uint8_t *make_rom(uint8_t rom_code, uint8_t type, uint8_t ram_code,
                         size_t *out_size) {
    *out_size = (size_t)32768u << rom_code;
    uint8_t *rom = calloc(*out_size, 1u);
    ...
    rom[0x147u] = type; rom[0x148u] = rom_code; rom[0x149u] = ram_code;
    fix_checksum(rom);
```
```c
    REQUIRE(gbb_battery_size(machine, &size) == GBB_OK);
    REQUIRE(gbb_import_battery(machine, input, size) == GBB_OK);
    REQUIRE(gbb_copy_battery(machine, output, size + 4u) == GBB_OK);
    for (size_t i = size; i < size + 4u; ++i) REQUIRE(output[i] == 0xC7u);   /* canary after buffer */
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
```
**Error and NULL-argument pattern** (lines 74-120): `GBB_BUFFER_TOO_SMALL` leaves buffer unchanged (0xA5 canary), `BATTERY_SIZE_MISMATCH` at `size-1`/`size+1`, NULL args return `GBB_INVALID_ARGUMENT` and leave outputs at sentinel values (`0x1234`, `0x5678`). **No-battery table** (lines 122-130) with `{type, ram_code}` cases: add `{0x05, 0}` expecting `GBB_NO_BATTERY` on all four calls. Note MBC2 `fill_pattern` import must be expected back as `0xF0 | (b & 0x0F)`, so round-trip equality only holds for already-canonical input; write a separate normalisation test.

Bit-8 decode table test: for each address in `{0x0000,0x00FF,0x0100,0x2000,0x2100,0x3FFF,0x4000,0x6000}` and values, assert via guest reads which register changed. Echo test: 8192 addresses against a 512-nibble model. Two-instance round trip: guest write, `gbb_copy_battery`, `gbb_import_battery` into a fresh instance, guest reads back (analog: end of `test_cartridge.c` `cartridge_no_ram_reads`, lines ~255-262, which restores into `fresh`).

---

### `tests/CMakeLists.txt` and `tests/expected-tests.txt`

**Analog (executable + test registration)**, lines 23-44:
```cmake
add_executable(test_cartridge test_cartridge.c)
target_link_libraries(test_cartridge PRIVATE GabbaBoy::core)
target_compile_features(test_cartridge PRIVATE c_std_17)
set_target_properties(test_cartridge PROPERTIES C_EXTENSIONS OFF)
add_test(NAME cartridge_tracer COMMAND test_cartridge cartridge_tracer)
```
and the loop idiom `foreach(case ...) add_test(NAME battery_${case} COMMAND test_battery battery_${case})`.

**Fixture digest test** (lines 222-226):
```cmake
add_test(NAME mbc1_continuation_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DROM=${PROJECT_SOURCE_DIR}/fixtures/mbc1-continuation/continuation.gb
    -DMANIFEST=${PROJECT_SOURCE_DIR}/fixtures/mbc1-continuation/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixture.cmake)
```
Copy for `mbc5_banking_fixture_digest`. Copy the `mooneye_fixture_digest`/`mooneye_eligible_inventory` pair (lines 227-234) for `mooneye_mbc_fixture_digest`/`mooneye_mbc_eligible_inventory` with `-DGBB_MOONEYE_DIR=.../fixtures/mooneye-mbc -P cmake/VerifyMooneyeMbc.cmake`.

**Runner case tests** (lines 291-313): copy `mooneye_case_${case}` loop and the `set_tests_properties(... TIMEOUT 30)` plus `PASS_REGULAR_EXPRESSION` pinned to `status=pass ... callback_pc=XXXX result_pc=4071|4072|407e`. Use `mooneye_mbc_case_*` names; do not use an `installed_` prefix (P15).

**Inventory rule:** every `add_test` needs a matching `+` line in `tests/expected-tests.txt` in the same commit (configure fails otherwise); no `-` lines (D-12). Put each plan's names in a separate block (P16).

**Exact-exit negative controls:** use `tests/expect_exit.cmake` (`GBB_CMD`, `GBB_EXPECT_CODE`, `GBB_EXPECT_REGEX`); the existing runner negative-control pattern is lines 270-290 (`expect_runner_failure.cmake`) for fail-closed manifest tests (unknown manifest digest -> `invalid-manifest`, exit 2).

---

### `src/runner/main.c` (suite_def, per-case size, mbc table)

**Analog:** itself. Existing identifiers used by `tests/test_runner.c` (which `#include`s `main.c`): `cases[]`, `MAX_ROM`, `MOONEYE_SOURCE_REVISION`, `MOONEYE_PATCH_SHA256`, `fixture_case`, `run_guest`, `protocol_status`, `budget_status`, `unsupported_core_stop`, `suite_counts_valid`, `hash_matches`, `read_bounded`. Keep those or update `test_runner.c` in the same plan.

**fixture_case struct and table row** (lines 30-51): add `size_t size_bytes` (existing three rows get `MAX_ROM`), keep one row per line so a CTest can compare it to the manifest:
```c
typedef struct {
    const char *id; const char *alias; const char *category; const char *rom;
    const char *sha256; const char *original_sha256; const char *source_path;
    uint16_t pass_callback_pc; uint16_t fail_callback_pc; uint16_t result_pc;
    uint8_t pass_registers[6]; uint8_t fail_registers[6];
    uint64_t budget;
} fixture_case;
```
**Manifest admission by SHA-256** (lines 70-77) is the single-digest point to generalise into `{manifest_sha256, cases, count}`:
```c
static int manifest_bytes_valid(const uint8_t *bytes,size_t length) {
    static const char expected[]=MOONEYE_MANIFEST_SHA256;
    return hash_matches(bytes,length,expected);
}
```
`MOONEYE_MANIFEST_SHA256` is also printed in both receipt `printf`s (`:217`, `:232`); the selected suite digest must print identical bytes for the three existing cases (the `PASS_REGULAR_EXPRESSION`s and `dmg_baseline --observe` consume them).

**ROM load with fixed size** (lines 90-103) is the `MAX_ROM` / `n != MAX_ROM` pair to replace with `size_bytes`:
```c
    size_t n=fread(rom,1,MAX_ROM+1,file);
    ...
    if(n!=MAX_ROM)return "bad-size";
    if(!hash_matches(rom,n,fc->sha256))return "bad-digest";
```
Allocate `size_bytes + 1`, cap by `GBB_CASES_MAX_ROM_BYTES` (8 MiB, `src/runner/acceptance.h:29`). `run_one` allocates `malloc(MAX_ROM+1)` at line 213.

**Oracle (reuse unchanged)** (lines 129-155): `protocol_status` pass requires `registers_match(pass)` and `pass_callback_seen`; fail requires six `0x42` and `fail_callback_seen`; else `unsupported`. Open Question 1: mbc2 ROMs have up to 6 fail callbacks, recommended bounded array of fail PCs; keep scalar `fail_callback_pc` for the three parent rows since `test_runner.c` reads it.

**Selection and suite flow** (lines 335-348): `manifest_valid` then `suite ? count : 1`, loop `run_one`, `suite_counts_valid(eligible, executed)`. Unknown digest -> `fprintf(stderr,"invalid-manifest\n"); return 2;` (fail closed). Keep `main.c` the only runner source file changed: the mutant runner at `tests/acceptance/CMakeLists.txt:309-321` and `CMakeLists.txt:69` list runner sources explicitly.

---

### `fixtures/mooneye-mbc/*`

**Analog:** `fixtures/mooneye/` (manifest, LICENSE.txt, SOURCES.md, ELIGIBILITY.md; do not copy `headless-report.patch`, `font-source.c`, `FONT-LICENSE.txt`: reference by relative path + SHA-256).

**Manifest shape to copy** (`fixtures/mooneye/manifest.json`): top-level `suite{revision,tree_sha1,license,upstream}`, `replacement_asset`, `builder{...}`, `inventory_status`, `required_roms[]`, `excluded_candidates[]`, then `fixtures[]` entries each with `id`, `category`, `eligible`, `eligibility_basis`, `source_path`, `source_closure[]`, `rom`, `size_bytes`, `sha256`, `license`, `asset_notice`, `model`, `boot`, `oracle_class`, `protocol{pass,fail,runner_support}`, `timeout_half_dots`, `build_recipe[]`, `candidate_derivation{original_rom_sha256,harness_patch_sha256,...}`. For the sibling set, categories `mbc2` (7) and `mbc5` (8); add per-ROM `result_pc`, `pass_callback_pc`, `fail_callback_pcs` from the RESEARCH fact table; add a `parent_references` block with relative path + SHA-256 for `../mooneye/headless-report.patch` (`c3679ab5...e5d`), `../mooneye/font-source.c` (`5e5b21a1...f52`) and the builder pin. Budgets are measured at admission (parent `daa` uses 2,000,000 vs 1,804,576 measured).

**Do not commit** `.sym`, `.lnk`, `.log` (embed absolute local paths, P20).

---

### `cmake/VerifyMooneyeMbc.cmake`

**Analog:** `cmake/VerifyMooneye.cmake` (adapted copy, D-23 forbids editing the parent).

**Top-of-file and required files** (lines 1-14): `cmake_minimum_required(VERSION 3.25)`, `GBB_MOONEYE_DIR` required, `cmake_path(ABSOLUTE_PATH ...)`, required-file loop.

**Per-fixture loop** (lines 65-129): `string(JSON ... ERROR_VARIABLE json_error GET ...)` pattern; per-field required metadata loop; `rom MATCHES "[/\\\\]|\\.\\.` path guard; `file(SIZE)`/`file(SHA256)` vs manifest; duplicate id/rom guards.
```cmake
  file(SIZE "${rom_path}" actual_size)
  file(SHA256 "${rom_path}" actual_digest)
  if(NOT actual_size EQUAL expected_size OR NOT actual_digest STREQUAL digest)
    message(FATAL_ERROR "Fixture ${id} mismatch: size ${actual_size}/${expected_size}, SHA-256 ${actual_digest}/${digest}")
```
**Changes:** categories `mbc2`/`mbc5` with counts 7/8; `required_roms` must equal the 15 eligible ROMs; replace the `replacement_asset`/builder literal checks (lines 145-169) with parent-reference SHA checks of `../mooneye/headless-report.patch`, `../mooneye/font-source.c`, builder pin; success line `Verified 15 eligible Mooneye-mbc ROM(s): 7 mbc2, 8 mbc5`. CMake 3.25 floor: only `file(SIZE)`, `file(SHA256)`, `string(JSON)`, `cmake_path` (P17).

---

### `tests/scripts/reproduce-mooneye-mbc.sh`

**Analog:** `tests/scripts/reproduce-mooneye.sh` (the parent hard-requires `$fixture_dir == $repo_root/fixtures/mooneye` at line 14 and the three ROM names, so copy and adapt).

**Reuse verbatim:** pin_sha helper (134-138), `fetch_source` with `git fetch --depth=1`, revision and `HEAD^{tree}` checks (139-151), WLA-DX cmake build and version pin (163-171), font build `cc -std=c17 -O2 font-source.c` then pin (175-177), `patch --batch --fuzz=0 -p1 < patch` (182), link flags `-nS -d -S` (193), `build_set` (218-233):
```bash
    "$assembler" -I "$common_dir" -o "$object" "$source_dir/$source_path" > "$case_dir/assembler.log" 2>&1
    printf '[objects]\n%s\n' "$object" > "$link_file"
    "$linker" "${link_flags[@]}" "$link_file" "$rom" > "$case_dir/linker.log" 2>&1
```
**Change:** `source_path` is `emulator-only/mbc{2,5}/<name>.s` for the 15 cases; take the fixture dir from the sibling, patch/font from `../mooneye`; write evidence to `mktemp -d` (P20); compare against the 15 D-25 digests only after Linux recapture; extract `result_pc`/callbacks from `.sym` into the manifest only.

---

### `fixtures/mbc5-banking/*` and `tests/scripts/reproduce-mbc5-banking.sh`

**Analog:** `fixtures/mbc1-continuation/` and `tests/scripts/reproduce-mbc1-continuation.sh`.

**Manifest keys to copy** (`fixtures/mbc1-continuation/manifest.json`): `id`, `source`, `source_identity` ("Original GabbaBoy project-authored assembly"), `source_sha256`, `license` ("MIT; see LICENSE.txt and repository LICENSE"), `build{assembler:"RGBDS", version:"1.0.1", archive, archive_sha256, ci_archive:"rgbds-linux-x86_64.tar.xz", ci_archive_sha256, recipe}`, `rom`, `size_bytes`, `sha256`, `cartridge{mapper,type,rom_size_code,ram_size_code}`, `profile{name:"DMG-CPU-B", boot, applicability}`, `protocol{...}`, `scope_limits[]`. The recipe string is verified verbatim by the repro script; for banking use `rgbfix -f hg -p 0 -m 0x1E -r 4` (confirm with 1.0.1, A8/P18). The macOS and Linux archive digests are `2f6f13c6...503645` / `80a5cad8...f6dad9` (identical to the continuation fixture). `applicability` must contain "not physical hardware evidence"; state the `$1FF` marker is harness-supplied and no rumble/CGB hardware observation exists.

**Assembly layout and WRAM-marker reporting** (`continuation.asm` lines 1-26):
```asm
SECTION "Entry", ROM0[$0100]
    jp Start
    ds $0150 - @, $00

SECTION "Program", ROM0[$0150]
Start:
    di
    xor a
    ldh [$FF40], a            ; keep the oracle independent of PPU output
    ld a, $0A
    ld [$0000], a             ; enable external RAM
    ...
    ld a, $A5
    ld [$C001], a             ; marker
```
Markers for banking: `C000=$A5` pass, `C001=$EE` fail, plus one result byte per sub-check; read by the C test via `gbb_peek_ram`. Keep the committed ROM at 64 KiB or less; the 8 MiB `$1FF` case is built in memory in `tests/test_mbc5.c`.

**Repro script** (`reproduce-mbc1-continuation.sh`): copy the RGBDS 1.0.1 exact-version gate (lines 16-25):
```bash
  version_line=$("$tool" --version | sed -n '1p')
  [[ "$version_line" == "$tool v1.0.1" ]] || { echo ... >&2; exit 1; }
```
then the `rgbasm`/`rgblink`/`rgbfix` recipe, then the inline `python3 -` verifier cross-checking manifest build pin against `fixtures/tracer/manifest.json` and `fixtures/visible-demo/manifest.json`, source SHA, ROM SHA, header bytes (`rebuilt[0x147] != 0x1E ...`), and `GBB_RGBDS_ARCHIVE` digest pin. Local Homebrew RGBDS is 1.0.4: do not use it for committed bytes.

---

### Forbidden-fixture scan (`cmake/ScanForbiddenFixtures.cmake`, recommended CMake over Python)

**Analog:** `scan_dir` and `scan_self_test` in `tests/scripts/verify-libbet-admission.py`.

**Scan semantics to reproduce** (lines 339-362): walk the tree without following symlinks; fail on any path component containing the forbidden name (case-insensitive); fail on any regular file whose size and SHA-256 match a forbidden ROM; fail on an empty tree.
```python
            if any("libbet" in part.lower() for part in relative.split("/")):
                fail("libbet-installed", relative)
            ...
            if stat.S_ISREG(target.st_mode) and target.st_size == ROM_SIZE:
                with open(path, "rb") as handle:
                    if sha256_hex(handle.read(ROM_SIZE + 1)) == ROM_SHA256:
                        fail("libbet-installed", relative)
    if count == 0:
        fail("scan-dir-empty", f"{directory.name} contains no files")
```
For the sibling: forbidden digests/sizes come from the sibling manifest (`file(GLOB_RECURSE)` + `file(SIZE)` + `file(SHA256)`; the scan lists 15 ROMs, including the 4 MiB and 8 MiB ones); path guard is any component containing `mooneye`; print `files=N` for the CTest regex `absent from scanned tree files=[1-9]`; also assert `share/gabbaboy/fixtures` immediate children are exactly `tracer;visible-demo;mbc1-continuation`. Emit a distinct failure token such as `mooneye-installed: <relative>` for `GBB_EXPECT_REGEX`.

**Self-test pattern** (`scan_self_test`, lines 700-715): clean tree passes (counts files), renamed digest copy fails, name-based hit fails, empty and missing directories fail with `scan-dir-empty`. Registered idiom (tests/CMakeLists.txt lines 429-441):
```cmake
set(GBB_LIBBET_INSTALL_CHECK "${PROJECT_BINARY_DIR}/libbet-install-check")
set(GBB_LIBBET_SCAN_SELFTEST "${PROJECT_BINARY_DIR}/libbet-scan-selftest")
file(MAKE_DIRECTORY "${GBB_LIBBET_SCAN_SELFTEST}/share")
file(COPY_FILE "${PROJECT_SOURCE_DIR}/fixtures/libbet/libbet.gb"
  "${GBB_LIBBET_SCAN_SELFTEST}/share/payload.bin")
add_test(NAME libbet_install_tree
  COMMAND ${CMAKE_COMMAND} --install ${PROJECT_BINARY_DIR} --prefix ${GBB_LIBBET_INSTALL_CHECK})
set_tests_properties(libbet_install_tree PROPERTIES FIXTURES_SETUP libbet_install TIMEOUT 120)
gbb_add_expect_exit_test(libbet_not_installed 0 "libbet absent from scanned tree files=[1-9]"
  --scan-dir "${GBB_LIBBET_INSTALL_CHECK}")
set_tests_properties(libbet_not_installed PROPERTIES FIXTURES_REQUIRED libbet_install)
gbb_add_expect_exit_test(libbet_not_installed_selftest 1 "libbet-installed: share/payload.bin"
  --scan-dir "${GBB_LIBBET_SCAN_SELFTEST}")
```
Reuse `FIXTURES_REQUIRED libbet_install` (the install tree already exists) and plant a small copy of `fixtures/mooneye-mbc/mbc5_rom_512kb.gb` (64 KiB, cheap) as `share/payload.bin`. Note `gbb_add_expect_exit_test` (tests/CMakeLists.txt:376-386) hard-wires `${Python3_EXECUTABLE} -I ${GBB_LIBBET_VERIFIER}`; a CMake-script scan needs its own `-DGBB_CMD="${CMAKE_COMMAND};-P;..."` wrapper around `expect_exit.cmake`. Name tests `mooneye_mbc_not_installed*`, never `installed_*` (P15).

---

### `cmake/PreviewPackageSmoke.cmake` (extracted-package scan)

**Analog:** itself. The libbet scan covers only the install tree; this script already installs, tars, extracts:
```cmake
set(extracted_prefix "${extract_root}/installed-prefix")
execute_process(
  COMMAND "${GBB_CMAKE_COMMAND}"
    "-DGBB_INSTALL_PREFIX=${extracted_prefix}"
    ...
    -P "${source_dir}/cmake/VerifyInstalledPackage.cmake"
  RESULT_VARIABLE runner_result OUTPUT_VARIABLE runner_output ERROR_VARIABLE runner_error)
if(NOT runner_result EQUAL 0)
  message(FATAL_ERROR "Extracted runner/package verification failed (${runner_result}): ${runner_output}${runner_error}")
endif()
```
Insert the scan right after extraction (lines ~56-80) using the same `execute_process` + `FATAL_ERROR (${result}): ${output}${error}` idiom. The script takes only `GBB_SOURCE_DIR` and friends via `-D`, so the scan must be CMake (no Python path variable) unless `-DGBB_PYTHON=` is added at `tests/CMakeLists.txt:318-327`. If `fixtures/mbc5-banking` is ever installed, also update the exact-directory list and this script's `required` list (lines 36-48).

---

### `tests/acceptance/CMakeLists.txt` (ninth-bit core mutant, D-29)

**Analog:** JOYP mutant, lines 277-333 (copy the whole block; second generated source, second library, second runner executable, two tests).

**Exactly-once anchor and text substitution:**
```cmake
set(GBB_MUTANT_SOURCE ${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c)
set(GBB_MUTANT_PATTERN "if ((m->joypad_select & 0x20u) == 0)")
set(GBB_MUTANT_REPLACEMENT "if ((m->joypad_select & 0x20u) != 0)")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${GBB_MUTANT_SOURCE})
file(READ ${GBB_MUTANT_SOURCE} gbb_core_text)
string(FIND "${gbb_core_text}" "${GBB_MUTANT_PATTERN}" gbb_mutant_first)
string(FIND "${gbb_core_text}" "${GBB_MUTANT_PATTERN}" gbb_mutant_last REVERSE)
if(gbb_mutant_first EQUAL -1 OR NOT gbb_mutant_first EQUAL gbb_mutant_last)
  message(FATAL_ERROR "core-mutant pattern '${GBB_MUTANT_PATTERN}' must occur exactly once in ...")
endif()
string(REPLACE "${GBB_MUTANT_PATTERN}" "${GBB_MUTANT_REPLACEMENT}" gbb_mutant_text "${gbb_core_text}")
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_joyp_mutant.c "${gbb_mutant_text}")
```
Mutant library and runner (lines 296-321): `add_library(... STATIC <generated>.c)`, `target_compile_definitions(... GBB_BUILD_REVISION="...-mutant" GBB_BUILD_QUALIFIED=0)`, runner executable lists `src/runner/main.c`, `cases.c`, `acceptance.c` and the five `src/accept/*.c` files explicitly, linked to the mutant core only; nothing installed or exported.

**Test pattern** (lines 323-333) via `expect_exit.cmake` with `GBB_EXPECT_CODE`/`GBB_EXPECT_REGEX`. For ninth-bit: two tests on the mutant runner, `--manifest fixtures/mooneye-mbc/manifest.json --case mbc5_rom_64Mb` must not pass (exit 1 or 3, expect regex matching `status=(fail|unsupported)`), `--case mbc5_rom_32Mb` must pass (exit 0). The MBC5 bank composition must sit on one line so `& 1u) << 8` (replace `& 1u` with `& 0u`) occurs once; the existing MBC1 helper uses `<< 5` so no collision. The mutant needs a runner built after Plan D adds the sibling suite, so keep this in the admission plan, not the mapper plans. The anchor `if ((m->joypad_select & 0x20u) == 0)` must remain exactly once after the seam.

---

### `src/player/session.c` / `session.h` / `main.c` / `limitations.h` (D-22)

**Analog:** `player_session_identify_rom` (session.c lines 158-173):
```c
    out_identity->cartridge_type = rom[0x147u];
    out_identity->ram_size = rom[0x149u] == 0x02u ? 8192u :
                             rom[0x149u] == 0x03u ? 32768u : 0u;
    out_identity->battery_backed = rom[0x147u] == 0x03u &&
                                   out_identity->ram_size != 0u;
    out_identity->saved_generation = 0u;
    out_identity->persistence_enabled = out_identity->battery_backed;
    return true;
```
Keep `battery_backed` exactly as is (so `battery_file_path` `:247`, save `:444`, save/lock `:664, :732` all early-return, creating no file). Add `bool battery_unsupported` (true when type is `0x06`, `0x1B`, `0x1E`) to `player_save_identity` in `session.h`; tests construct identities with `= {0}` so it is source compatible. The player's `PLAYER_SESSION_MAX_ROM_SIZE` stays 2 MiB (`session.c:19`, `:114-143`); do not edit `read_rom_file` or its "2 MiB read bound" wording (P22).

**limitations text** (`src/player/limitations.h`): change only the clause "Battery saves support standard MBC1 type $03 with 8 or 32 KiB RAM." and mirror it byte-for-byte in `tests/player/test_limitations.c`; also `README.md:6`, `docs/preview.md:3, 63`, `docs/cartridge-and-saves.md`.

**Player test:** copy the `player_session_replace_rom(machine, &current_path, path, &identity, error, sizeof(error))` call shape from `tests/player/test_session.c:103-176`; add case `player_session_battery_unsupported` there and a line in `tests/player/expected-tests.txt`. The CMake dispatcher already routes `^player_session_[a-z0-9_]+$` to `test_player_session` (tests/player/CMakeLists.txt:56). Assert `battery_backed==false && battery_unsupported==true` for in-memory `$06/$1B/$1E` ROMs, then that the test preference directory stays empty. Player CTests only exist with `-DGABBABOY_BUILD_PLAYER=ON` (macOS, SDL3).

---

### `.gitattributes`, `THIRD_PARTY_NOTICES.md`, `fixture-repro.yml`

**.gitattributes analog** (existing lines):
```
fixtures/mooneye/manifest.json -text
fixtures/mbc1-continuation/continuation.asm text eol=lf
fixtures/mbc1-continuation/manifest.json text eol=lf
fixtures/mbc1-continuation/LICENSE.txt text eol=lf
fixtures/mbc1-continuation/continuation.gb -text
fixtures/libbet/libbet.gb -text
```
Add `fixtures/mooneye-mbc/*.gb binary` (D-31 says `binary`), `fixtures/mooneye-mbc/manifest.json -text`, `text eol=lf` for its md/txt files; `fixtures/mbc5-banking/*` mirrors mbc1-continuation. Without this, Windows `autocrlf` changes the manifest digest and every runner test fails only on Windows (P14).

**Notices analog:** the libbet row in `THIRD_PARTY_NOTICES.md` (verified by `check_notices_text` in the libbet verifier; no equivalent verifier is required for the sibling, but add a Mooneye-mbc row).

**fixture-repro.yml analog:** `mooneye-candidate-repro` (lines ~143-171) stages provenance files with `cp ... "$provenance/"` and runs `bash tests/scripts/reproduce-mooneye.sh --candidate-compare fixtures/mooneye`; the `fixture-repro` job (lines ~20-110) holds an inline Python block cross-checking RGBDS pins across fixture manifests (extend with `fixtures/mbc5-banking/manifest.json` as a fourth manifest) and a "Reproduce MBC1 battery continuation fixture bytes" step to copy for `reproduce-mbc5-banking.sh`. The workflow is non-required (D-30). Third-party actions must keep their pinned SHAs (`actions/upload-artifact@ea165f8d... # v4.6.2`); add no new actions.

---

## Shared Patterns

### Validate, then allocate, then commit; failure leaves the instance untouched
**Source:** `src/core/gabbaboy.c:1707-1735` (`gbb_load_rom`).
**Apply to:** seam plan, MBC5 (8 MiB), MBC2 (512-byte row RAM). Tests: `loader_non_destructive`, `loader_mbc1m_variant`, `loader_boundary_fuzz` must pass unchanged.

### Append-only `gbb_error`, outputs untouched on error
**Source:** `include/gabbaboy/gabbaboy.h:18-35` and `gbb_battery_generation` (`gabbaboy.c:1773-1779`).
**Apply to:** `gbb_rumble_state`, MBC2 import (compare before mutate).

### Test executable with local `REQUIRE`, name-dispatch `main`, synthetic in-memory ROM
**Source:** `tests/test_cartridge.c:1-9, 277-284`; `tests/test_battery.c:11-34`.
**Apply to:** `tests/test_mbc5.c`, `tests/test_mbc2.c`. Copy `fix_checksum` (6 lines, duplicated in three files already; no shared test lib).

### Digest-pinned manifest admission with exact-exit negative controls
**Source:** `cmake/VerifyMooneye.cmake`, `cmake/VerifyFixture.cmake`, `tests/expect_exit.cmake`.
**Apply to:** sibling Mooneye verifier, fixture digest tests, scan self-test, mutant tests. A different non-zero exit or a signal can never satisfy `GBB_EXPECT_CODE`.

### Test inventory is an exact set
**Source:** `cmake/ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh`, `tests/expected-tests.txt`.
**Apply to:** every plan. `+` lines only; each `add_test` paired with a line in the same commit; names starting `installed_` are filtered out (P15).

### Single translation unit for `gabbaboy.c`
**Source:** `CMakeLists.txt:23, 69`; `tests/CMakeLists.txt:71, 168`; `tests/scripts/probe-mooneye-candidate.sh:137`; `tests/acceptance/CMakeLists.txt:287-300`; plus `tests/test_runner.c:6-8` including `src/runner/main.c`.
**Apply to:** seam plan (no new `.c`/`.h`), runner plan (no new runner `.c`).

### Frozen DMG baseline is read-only
**Source:** `tests/baseline/`, `cmake/VerifyDmgBaseline.cmake:422-443`.
**Apply to:** all plans: no `baseline:` commit, no `CHANGES.md` row; do not add sibling results to `--observe`; `bench.tracer.correctness_digest_fnv1a64` stays `4c7a57ff3d50d228`.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `suite_def` selection in `src/runner/main.c` | runner adapter | request-response | Runner admits exactly one compiled table by one manifest digest today; the multi-suite selection is new, built by generalising `manifest_bytes_valid` (`:70-73`) |
| Scratch old-vs-new differential harness (D-10) | one-off verification | batch | Not committed. Closest style analog is the grid/boundary loops in `tests/test_loader_fuzz.c`; build `gabbaboy.c` at `5673bed` (`git show 5673bed:src/core/gabbaboy.c`) and at the seam commit into two executables and `diff` the output; record input count (86,016 loader cells per RESEARCH) and digest in the seam plan verification section |
| MBC2 bit-8 address decode | core mapper | request-response | MBC1 splits by address range; MBC2 splits by address bit 8, so no existing branch is reusable as is (Pattern 3) |
| `gbb_rumble_state` rumble line and saturating change counter | public API | request-response | No existing monotonic counter other than `battery_generation` (saturates at `UINT64_MAX`, `gabbaboy.c:769`); copy that saturation idiom |

## Metadata

**Analog search scope:** `src/core/`, `src/runner/`, `src/player/`, `include/gabbaboy/`, `tests/` (incl. `tests/acceptance`, `tests/player`, `tests/scripts`), `cmake/`, `fixtures/`, `.github/workflows/`, `CMakeLists.txt`, `.gitattributes`.
**Files scanned:** about 40 opened or grepped; all named analogs confirmed tracked with `git ls-files`.
**Pattern extraction date:** 2026-10-11
