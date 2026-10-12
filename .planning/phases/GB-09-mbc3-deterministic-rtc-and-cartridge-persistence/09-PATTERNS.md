# Phase 9: MBC3, Deterministic RTC and Cartridge Persistence - Pattern Map

**Mapped:** 2026-10-11
**Files analyzed:** 41 new or modified (grouped below)
**Analogs found:** 38 / 41 (3 partial or none, see "No Analog Found")
**All analog paths verified git-tracked** (`git ls-files` on the Phase 8 set: `tests/test_mbc2.c`, `tests/test_mbc5.c`, `tests/test_mbc5_internal.c`, `fixtures/mbc1-continuation/*`, `fixtures/mooneye-mbc/manifest.json`, `src/accept/input_script.c`, `src/player/session.c`, `tests/player/test_continuation.c`, `tests/fuzz_core.c`). No gitignored mirror path appears here.

Line numbers are for the working tree at `gsd/phase-09-discuss` (HEAD `703627e`). All paths are repo-relative.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/core/gabbaboy.c` (MBC3 kind, rows, decode, `validate_header` MBC30 check) | mapper/model | request-response (bus) | same file, Phase 8 MBC5/MBC2 branches (`:56-152`, `:786-812`, `:858-966`, `:1832-1888`) | exact |
| `src/core/gabbaboy.c` (lazy RTC: `rtc_sync`, `rtc_add_seconds`, latch, reset rebase) | model/utility | transform (time-anchored) | `rumble_changes` counter + `cart_reset_registers` (`:120-126`, `:896-905`, `:1909-1919`) | role-match |
| `src/core/gabbaboy.c` (battery image, `gbb_rtc_catch_up`, `GBB_NO_RTC`) | service/API | CRUD / file-I/O (blob) | `has_battery_ram`..`gbb_rumble_state` (`:1955-2022`) | exact |
| `include/gabbaboy/gabbaboy.h` (`GBB_NO_RTC`, `GBB_RTC_BLOCK_SIZE`, `gbb_rtc_catch_up`, comments) | config/API header | request-response | `GBB_NO_RUMBLE` + `gbb_rumble_state` in same header (`:37` per RESEARCH) | exact |
| `tests/test_mbc3.c` | test | request-response | `tests/test_mbc5.c` / `tests/test_mbc2.c` | exact |
| `tests/test_mbc3_rtc.c` | test | transform (differential, metamorphic) | `tests/test_mbc5.c` helpers + `tests/test_mbc5_internal.c` (white-box) | role-match |
| `tests/test_rtc_battery.c` | test | CRUD (blob round-trip) | `tests/test_mbc2.c` battery cases | role-match |
| `tests/test_rtc3test.c` | test (white-box, screen oracle) | event-driven (scripted input) | `tests/test_mbc5_internal.c` + `src/accept/input_script.c` | partial |
| `tests/test_magentests.c` | test (screen oracle) | request-response | `tests/test_mbc5.c` (`run_to_halt`, `load_image`) | role-match |
| `tests/test_loader_matrix.c` | test (table-driven) | batch | `tests/test_mbc5.c:520-566` (`mbc5_rom_bound`) | role-match |
| `tests/fuzz_core.c`, `tests/test_fuzz_core.c` (modified) | test/fuzz | batch | same files | exact |
| `tests/CMakeLists.txt` (modified) | config | n/a | `:32-58`, `:312-316`, `:585-645` | exact |
| `tests/expected-tests.txt`, `tests/player/expected-tests.txt` (modified) | config | n/a | same files | exact |
| `cmake/ScanForbiddenFixtures.cmake` (add label param) | utility | file-I/O | same file | exact |
| `cmake/CheckCoreNoHostClock.cmake` | utility/test script | file-I/O (scan) | `cmake/ScanForbiddenFixtures.cmake` + `tests/expect_exit.cmake` | role-match |
| `fixtures/magentests/*` | fixture (third-party) | n/a | `fixtures/mooneye-mbc/*` | exact |
| `fixtures/rtc3test/*` | fixture (third-party) | n/a | `fixtures/mooneye-mbc/*`, `fixtures/mooneye/*` | exact |
| `fixtures/{mbc3-rtc,mbc2,mbc5}-continuation/*` | fixture (original) | n/a | `fixtures/mbc1-continuation/*` | exact |
| `fixtures/save-envelope-v1/*` | fixture (generated) | file-I/O | `fixtures/mbc1-continuation/manifest.json` (manifest shape) | partial |
| `tests/scripts/reproduce-{magentests,rtc3test}.sh` | script | batch | `tests/scripts/reproduce-mbc1-continuation.sh` | role-match (legacy RGBDS) |
| `tests/scripts/reproduce-{mbc3-rtc,mbc2,mbc5}-continuation.sh` | script | batch | `tests/scripts/reproduce-mbc1-continuation.sh` | exact |
| `tests/scripts/generate-save-envelope-v1.sh` | script | batch | `tests/scripts/verify-phase3-player.sh` (per RESEARCH) | partial |
| `src/player/session.c`, `session.h` (v2 envelope, WR-02 removal) | service | file-I/O | same files (`:158-175`, `:221-247`, `:423-437`, `:659-706`) | exact |
| `src/player/catch_up_policy.{c,h}` | utility (pure) | transform | `player_save_cadence_observe` / `player_save_transition_resolve` (`session.c:798-835`) | role-match |
| `src/player/main.c`, `limitations.h` (modified) | controller/config | request-response | same files | exact |
| `tests/player/test_continuation.c` (generalise) | test | file-I/O, multi-process | same file | exact |
| `tests/player/test_session.c`, `tests/player/CMakeLists.txt` (modified) | test/config | file-I/O | same files | exact |
| `tests/consumers/{c,cpp}`, docs, `docs/mbc3-rtc-evidence.md` | consumer/doc | request-response | `docs/mbc2-mbc5-evidence.md`, existing consumers | role-match |

## Pattern Assignments

### `src/core/gabbaboy.c` - MBC3 mapper rows, kind, decode (mapper, request-response)

**Analog:** the Phase 8 MBC5/MBC2 seam in the same file.

**Kind and RAM-rule enums** (`:55-63`). Append `CART_MBC3 = 4` and `CART_RAM_MBC3 = 4`; keep `CART_ROM_ONLY = 0` (calloc-zeroed instance):
```c
typedef enum { CART_ROM_ONLY = 0, CART_MBC1 = 1, CART_MBC2 = 2, CART_MBC5 = 3 } cart_kind;
typedef enum {
    CART_RAM_NONE = 0, CART_RAM_8K_OR_32K = 1, CART_RAM_MBC2 = 2, CART_RAM_MBC5 = 3
} cart_ram_rule;
```

**Type-table rows** (`:96-110`). `has_timer` already exists as a column (always `0u` today); MBC3 flips it for `$0F/$10`. Row shape to copy:
```c
    { 0x1Bu, CART_MBC5,     1u, 1u, 0u, 0u, 0x08u, CART_RAM_MBC5,      0u,    GBB_MAX_ROM_SIZE },
```
New rows follow the same column order `{type, kind, window, batt, timer, rumble, maxrom, ram_rule, ram32, ceiling}`, with ceiling a new 4 MiB constant (add beside `GBB_MAX_ROM_SIZE` at `:52`). `cart_state` (`:69-81`) and `cartridge_info` (`:154-161`) have no `has_timer`; add it to both and plumb it in `validate_header` (`:1879-1886`) and `gbb_load_rom` (`:1945-1949`).

**Reset hook** (`:118-126`). Add `c->rtc_latch_prev = 0xFFu;` here (D-08/D-09); comment contract "never touches cartridge RAM ... safe on an unloaded instance" must stay true:
```c
static void cart_reset_registers(cart_state *c) {
    c->rom_bank_lo = 1u; c->rom_bank_hi = 0u; c->ram_bank = 0u;
    c->ram_enabled = 0u; c->mbc1_mode = 0u;
}
```

**Write-decode, control range** (`:861-912`): copy the MBC2 translate-then-mask (`:879-882`) for the `$2000-$3FFF` MBC3 bank (`v & 0x7F`, 0 to 1, `& (rom_size/0x4000 - 1)`), and the MBC5 `case` shape for the rest:
```c
                    size_t bank = value & 0x0Fu;
                    if (bank == 0u) bank = 1u;
                    m->cart.rom_bank_lo = (uint8_t)(bank & (m->rom_size / 0x4000u - 1u));
```
`$4000-$5FFF` stores the raw byte in `ram_bank` (RESEARCH Pattern 1); `$6000-$7FFF` is the latch (new; no analog in the file, see RTC section).

**RAM-window read** (`:787-812`), MBC5 branch to extend into MBC3 (RTC select `$08-$0C` returns latched byte, `$04-$07`/`$0D+` return `$FF`):
```c
        case CART_MBC5:
            if (m->cart.ram_enabled && m->cartridge_ram != NULL &&
                m->cartridge_ram_size != 0u) {
                const size_t banks = m->cartridge_ram_size / 0x2000u;
                const size_t bank = (size_t)m->cart.ram_bank & (banks - 1u);
                return m->cartridge_ram[bank * 0x2000u + (size_t)(address & 0x1FFFu)];
            }
            return 0xFFu;
```
`read8` is `const` (`:700`): RTC reads must return `rtc_l[]` without syncing.

**RAM-window write with generation bump** (`:948-961`), copy the changed-byte bump verbatim for the RAM-bank half of MBC3:
```c
                if (m->cartridge_ram[offset] != value) {
                    m->cartridge_ram[offset] = value;
                    if (m->cart.has_battery &&
                        m->battery_generation != UINT64_MAX)
                        ++m->battery_generation;
                }
```
The RTC-register write path uses the same saturating-bump idiom but gates on the D-10 snapshot-compare rule, not a single byte.

**`validate_header`** (`:1832-1888`). Order to preserve: size<0x150, ceiling, `row==NULL`, ROM code, RAM rule, declared truncated/mismatch, checksum, variant. Add a `CART_RAM_MBC3` branch (codes `$02`/`$03` only) next to the `CART_RAM_MBC5` switch (`:1854-1861`), and the MBC30 check right after the MBC1M check (`:1876-1878`):
```c
    if (row->kind == CART_MBC1 && declared >= 512u * 1024u &&
        recognized_mbc1m_candidate(rom, size))
        return GBB_UNSUPPORTED_CARTRIDGE_VARIANT;
```
Note the existing `ceiling` slot (`:1840-1842`) uses `row->early_ceiling_bytes`; a 4 MiB row ceiling lands `ROM_TOO_LARGE` for 4 MiB+1 with no other change. ROM code `$07` stays reachable only for the variant check (RESEARCH Open Question 5).

**Reset** (`:1909-1919`): `gbb_reset` currently handles rumble then `reset_state`. For D-09 insert `rtc_sync(now)` before `reset_state(instance)` (which zeroes `time_half_dots`, `:610` per RESEARCH) and `synced_at = 0` after, only for timer carts. Mirror the rumble guard shape:
```c
    if (instance->cart.rumble_on) {
        instance->cart.rumble_on = 0u;
        if (instance->cart.rumble_changes != UINT64_MAX) ++instance->cart.rumble_changes;
    }
    reset_state(instance);
```

---

### `src/core/gabbaboy.c` - battery image, catch-up (service, blob I/O)

**Analog:** `has_battery_ram` ... `gbb_rumble_state` (`:1955-2022`).

**Capability helper to generalise** (`:1955-1960`): drop the `cartridge_ram_size != 0u` requirement for timer carts (Pitfall 5):
```c
static int has_battery_ram(const gbb_instance *instance) {
    return instance != NULL && instance->loaded && instance->cart.has_battery &&
           instance->cartridge_ram != NULL && instance->cartridge_ram_size != 0u;
}
```

**Error ordering and compare-before-commit** (`:1978-2003`). Copy this structure for RAM-plus-block import: validate size, compute normalised differ flag, only then commit and bump once:
```c
    if (size_bytes != instance->cartridge_ram_size) return GBB_BATTERY_SIZE_MISMATCH;
    ...
    if (memcmp(instance->cartridge_ram, bytes, size_bytes) != 0) {
        memcpy(instance->cartridge_ram, bytes, size_bytes);
        if (instance->battery_generation != UINT64_MAX)
            ++instance->battery_generation;
    }
    return GBB_OK;
```
For the block, parse into locals, reject with `GBB_INVALID_ARGUMENT` (bad magic/version/masks/reserved) without touching RAM, then commit both and set `synced_at = time_half_dots`.

**Export on a `const` instance** (`:1969-1976`): `gbb_copy_battery` takes `const gbb_instance *`; project the RTC onto a stack copy and serialise field by field (RESEARCH "Battery block field-by-field write").

**Capability query returning a `GBB_NO_*`** (`:2014-2022`), the template for `gbb_rtc_catch_up` (NULL, then NO_RTC, then negative per RESEARCH A5):
```c
gbb_error gbb_rumble_state(const gbb_instance *instance, uint8_t *out_on,
                           uint64_t *out_changes) {
    if (instance == NULL || out_on == NULL || out_changes == NULL)
        return GBB_INVALID_ARGUMENT;
    if (!instance->loaded || !instance->cart.has_rumble) return GBB_NO_RUMBLE;
    ...
```

**RTC lazy model:** no analog in the file. Closest conceptual precedent is `rumble_changes` (saturating `u64` counter, `:899-902`) and the STOP fast-forward bypass at `:2361-2371` (why the anchor is `time_half_dots`, not `advance_devices_to`, `:1653`, untouched). Write timestamp: `bus_write` (`:1146-1155`) advances devices before `write8`, so inside `write8` `m->time_half_dots` is the write timestamp. Use the RESEARCH Pattern 2 sketch (`rtc_sync`/`rtc_add_seconds`) as the code shape.

---

### `include/gabbaboy/gabbaboy.h` (API header)

**Analog:** the `GBB_NO_RUMBLE` enum member and `gbb_rumble_state` declaration with doc comment (enum member at `:37`: `GBB_NO_RUMBLE /* loaded cartridge has no rumble line (or no ROM) */`). Append `GBB_NO_RTC` after it, add `#define GBB_RTC_BLOCK_SIZE 21u` and `gbb_rtc_catch_up(gbb_instance *, int64_t)` declared beside `gbb_rumble_state` with the same comment style. Stale comments to update (RESEARCH): `GBB_ROM_TOO_LARGE` ceiling text, `gbb_load_rom` supported types, battery comments.

---

### `tests/test_mbc3.c` (test, request-response)

**Analog:** `tests/test_mbc5.c` (synthetic images, no fixture). Copy the whole scaffold.

**Imports + REQUIRE** (`test_mbc5.c:1-9`):
```c
#include "gabbaboy/gabbaboy.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)
```

**Program emitters** (`:14-37`): `program`, `emit_write`, `emit_read_to`, `emit_raw`, `emit_halt`. **Image builder** (`:39-72`): `fix_checksum`, `make_rom` (bank stamp `0x40+bank` at `$1000`), `install` (`JP $0200`). **Run helpers** (`:74-88`): `new_machine`, `run_to_halt` (64 slices of `1u << 20`, `GBB_STOP_HALTED_IDLE`).

**Tracer case shape** (`:90-115`): emit writes, read, halt; load; run; assert via `gbb_peek_ram(machine, 0xC000u)`.

**Dispatch** (bottom of file, one `strcmp` per case) and CMake registration via a `foreach(case ...)` list:
```cmake
add_executable(test_mbc5 test_mbc5.c)
target_link_libraries(test_mbc5 PRIVATE GabbaBoy::core)
target_compile_features(test_mbc5 PRIVATE c_std_17)
set_target_properties(test_mbc5 PROPERTIES C_EXTENSIONS OFF)
foreach(case tracer header_matrix rom_banking ...)
  add_test(NAME mbc5_${case} COMMAND test_mbc5 mbc5_${case})
endforeach()
```
(`tests/CMakeLists.txt:42-50`.) New names `mbc3_<case>` must also be added to `tests/expected-tests.txt` (configure fails otherwise).

**MBC3-specific deviations** from the MBC5 test: ROM-bank stamp must be one byte (MBC3 max 128 banks), so MBC2's single-byte stamp variant (`test_mbc2.c:46-57`) is the closer `make_rom`; the RTC select test must cover `$04-$07` maps nothing and 8 KiB banks 1-3 alias bank 0.

**Edit to existing test (breaks otherwise):** `tests/test_mbc5.c:552` drops `0x0Fu` from the legacy list:
```c
    static const uint8_t legacy[] = {0x00u, 0x01u, 0x03u, 0x05u, 0x06u, 0x0Fu, 0x18u, 0x20u, 0xFFu};
```

---

### `tests/test_mbc3_rtc.c` (test, differential/metamorphic)

**Analog:** `tests/test_mbc5.c` for black-box cases; `tests/test_mbc5_internal.c` for the white-box naive-stepper differential (needs `static rtc_add_seconds`).

**White-box single-TU pattern** (`test_mbc5_internal.c:1-10`, `:48-52`):
```c
#include "../src/core/gabbaboy.c"
#include <stdio.h>
/* Single-TU white-box test: it includes the core source to reach the static
 * write8 and the instance layout, so it must not link GabbaBoy::core. */
#define REQUIRE(x) ...
int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "mbc5_rumble_saturation") == 0) return mbc5_rumble_saturation();
    return 2;
}
```
Direct `write8(m, 0x4000u, 0x08u)` calls bypass `bus_write`, so the test must advance `m->time_half_dots` itself (Pitfall 3). Poke counters directly, as `m->cart.rumble_changes = UINT64_MAX - 1u;` does (`:34`).

**CMake for white-box** (`tests/CMakeLists.txt:52-58`): no link to the core, only include dir:
```cmake
add_executable(test_mbc5_internal test_mbc5_internal.c)
target_include_directories(test_mbc5_internal PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_mbc5_internal PRIVATE c_std_17)
set_target_properties(test_mbc5_internal PROPERTIES C_EXTENSIONS OFF)
add_test(NAME mbc5_rumble_saturation COMMAND test_mbc5_internal mbc5_rumble_saturation)
```

**Mutation controls (D-12):** copy the "mutant copy with exactly-once anchor" mechanism at `tests/CMakeLists.txt:72-116` (the ninth-bit mutant): `file(READ)` the core, `string(FIND ...)` first == last or `FATAL_ERROR`, `string(REPLACE ...)`, `file(WRITE ...mutant.c)`, `add_library(... STATIC mutant.c)`, link the test executable to it, and register with an `expect_exit` wrapper (`tests/expect_exit.cmake`, see lines 104-112). One mutant per D-12 bullet.

---

### `tests/test_rtc_battery.c` (test, blob round-trip)

**Analog:** `tests/test_mbc2.c` battery cases (`battery_image`, `battery_import`, `battery_idempotent`, `battery_errors`, `battery_no_battery`, `two_instance_roundtrip`, registered `tests/CMakeLists.txt:36-40`). Copy their structure (before/after byte comparison, generation unchanged on identical import) for the 21-byte block corruption matrix and the "run N half-dots, export, import, export identical" test.

---

### `tests/test_rtc3test.c` (white-box screen oracle)

**Analog:** `tests/test_mbc5_internal.c` (single-TU include) plus the acceptance libraries.

Includes `src/core/gabbaboy.c` for BG-map access, and **also** `src/accept/input_script.c` and `src/accept/sha256.c` as source (they are `gbb_accept_*` in `src/accept/gbb_accept.h`: `gbb_accept_script_parse` `:63`, `gbb_accept_sha256_hex` `:37`). Beware duplicate-symbol collision: do not link `GabbaBoy::core` or the accept library. Scripts follow the `gbinput 1` grammar in `tests/acceptance/inputs/*.input`:
```
gbinput 1
wait 470f
mark title
tap SELECT 3f
```
(`tests/acceptance/inputs/libbet-select.input:1-8`). rtc3test scripts use `wait 60f` / `tap A` / `tap DOWN`. Digest-pin each script and the ROM using the `VerifyFixture.cmake` test pattern:
```cmake
add_test(NAME mbc1_continuation_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DROM=${PROJECT_SOURCE_DIR}/fixtures/mbc1-continuation/continuation.gb
    -DMANIFEST=${PROJECT_SOURCE_DIR}/fixtures/mbc1-continuation/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixture.cmake)
```
(`tests/CMakeLists.txt:308-312`). Give each suite `TIMEOUT 300` (RESEARCH A4).

---

### `tests/test_magentests.c` (screen oracle through public API)

**Analog:** `tests/test_mbc5.c` public-API scaffolding (`new_machine`, `gbb_load_rom`, `gbb_run` slices). Frame sampling: use the framebuffer API (not read in this mapping; planner should grep `gbb_copy_frame`/frame accessors in `gabbaboy.h`). Negative control is built in-test: copy the ROM, set `[0x149]=0x03`, recompute the checksum with `fix_checksum` (`test_mbc5.c:39-44`), run the same frame count, require all 23040 pixels at shade 3. Digest test uses `VerifyFixture.cmake` as above.

---

### `tests/test_loader_matrix.c` (table-driven loader oracle)

**Analog:** `tests/test_mbc5.c:520-566` (`mbc5_rom_bound`): large-image `calloc`, header poke, `fix_checksum`, and `previous_rom_intact` no-mutation checks around each `gbb_load_rom` rejection:
```c
    over[0x147u] = 0x19u;
    over[0x148u] = 8u;
    fix_checksum(over);
    REQUIRE(gbb_load_rom(previous, over, eight_mib + 1u) == GBB_ROM_TOO_LARGE);
    REQUIRE(gbb_load_rom(previous, over, SIZE_MAX) == GBB_ROM_TOO_LARGE);
    REQUIRE(previous_rom_intact(previous) == 0);
```
Expand to the D-27 families, with the independent oracle function implementing the nine-step precedence. Reuse the pattern of one executable with a case-name `argv[1]` and multiple `add_test` lines (`loader_contradiction_mbc2`, ...).

---

### `tests/fuzz_core.c` / `tests/test_fuzz_core.c` (modified)

**Analog:** the files themselves. Selector point to change (`fuzz_core.c`, `gbb_fuzz_core_one_input`):
```c
    if ((data[0] & 1u) == 0u)
        fuzz_loader(machine, data, size);
    else
        fuzz_stateful_api(machine, data, size);
```
Add the `(data[0] & 3u) == 2u` synthesised-length branch first, keep existing residue meanings (`&3 == 0` loader, `== 1`/`3` stateful). Preserve verbatim these greppable literals (`:6-12`): `FUZZ_INPUT_LIMIT 65536u`, `FUZZ_OPERATION_LIMIT 16u`, `FUZZ_RUN_LIMIT UINT64_C(2048)`, `FUZZ_INPUT_HALF_DOT_LIMIT UINT64_C(8192)`. `make_battery_rom` (`:22-28`) is the template for a header-only ROM writer (reset only the first `0x150` bytes of the shared 8 MiB+1 static buffer).

---

### `cmake/ScanForbiddenFixtures.cmake` (add optional label)

**Analog:** itself. Hard-coded strings to parameterise behind `GBB_FORBIDDEN_LABEL` (default keeps today's text, existing tests regex-match it):
```cmake
  if(lowered MATCHES "mooneye")
    message(FATAL_ERROR "mooneye-installed: ${relative}")
  ...
message(STATUS "mooneye-mbc absent from scanned tree files=${scanned_count}")
```
(`:59-61`, `:108`, `:131`). Manifest reading (`:33-48`) already uses `fixtures[].{size_bytes,sha256}`, so `fixtures/magentests/manifest.json` must use that shape. Test registration: copy `gbb_add_mbc_scan_test` (`tests/CMakeLists.txt:623-634`) plus `FIXTURES_REQUIRED libbet_install` (`:637`) for `magentests_not_installed`, and the renamed-ROM selftest (`:608-613` copy to `payload.bin`). Do not add the new fixtures to `GBB_MBC_SCAN_DIRS` (`:607`, installed set stays `tracer|visible-demo|mbc1-continuation`).

---

### `cmake/CheckCoreNoHostClock.cmake` (scan script, negative control)

**Analog:** `ScanForbiddenFixtures.cmake` for structure (`-D` inputs listed in a header comment, `foreach(required ...)` fatal checks `:19-23`, stable failure tokens) and `tests/expect_exit.cmake` for the negative control (`GBB_CMD`, `GBB_EXPECT_CODE`, `GBB_EXPECT_REGEX`, as wired at `tests/CMakeLists.txt:625-632`). Pitfall 10: CMake regex has no `\b`; core contains `apu_sequencer_clock(`, so use `(^|[^A-Za-z0-9_])(time|clock)[ \t]*\(`.

---

### `fixtures/magentests/*` and `fixtures/rtc3test/*` (third-party fixtures)

**Analog:** `fixtures/mooneye-mbc/` (`ELIGIBILITY.md`, `LICENSE.txt`, `SOURCES.md`, `manifest.json`, ROMs) and `fixtures/mooneye/` (digest/eligibility docs). Manifest consumed by the scan: `fixtures[].{alias,size_bytes,sha256}`. Add `THIRD_PARTY_NOTICES.md` entries. Reproduction scripts use legacy RGBDS (0.4.2 / 0.6.1), so they diverge from the v1.0.1 version-check block of the MBC1 script (see below).

---

### `fixtures/{mbc3-rtc,mbc2,mbc5}-continuation/*` (original fixtures)

**Analog:** `fixtures/mbc1-continuation/{continuation.asm,continuation.gb,manifest.json,LICENSE.txt}`.

**Manifest shape to copy** (`manifest.json`, whole file): keys `id`, `source`, `source_identity`, `source_sha256`, `license` ("MIT; see LICENSE.txt and repository LICENSE"), `build{assembler,version:"1.0.1",archive,archive_sha256,ci_archive,ci_archive_sha256,recipe}`, `rom`, `size_bytes`, `sha256`, `cartridge{mapper,type,rom_size_code,ram_size_code}`, `profile{name,boot,applicability}`, `protocol{...}`, `scope_limits[]`. Keep the `build` object byte-identical (fixture-repro job compares pins across fixtures). Recipes differ only in rgbfix flags: `-m 0x10 -r 2` (`$10`, 8 KiB), `-m 0x06 -r 0` (`$06`), `-m 0x1b -r 4` (`$1B`, 128 KiB).

**Guest/host protocol precedent** (manifest `protocol`): fixed WRAM addresses publish results (`C000`..`C004`), store run writes a marker to SRAM, resume run checks it.

---

### `tests/scripts/reproduce-{mbc3-rtc,mbc2,mbc5}-continuation.sh`

**Analog:** `tests/scripts/reproduce-mbc1-continuation.sh`. Copy whole. Key parts:

**Preamble and tool pin check** (`:4-24`): `set -euo pipefail`, `script_dir`/`repo_root`, `mktemp -d` work dir with `trap cleanup EXIT`, loop over `rgbasm rgblink rgbfix` demanding `"$tool v1.0.1"`.

**Build** (`:26-28`):
```bash
rgbasm -o "$work_dir/continuation.o" fixtures/mbc1-continuation/continuation.asm
rgblink -o "$work_dir/continuation.gb" "$work_dir/continuation.o"
rgbfix -f hg -p 0 -m 3 -r 2 "$work_dir/continuation.gb"
```

**Embedded Python verifier** (`:30-114`): load manifests of `tracer` and `visible-demo`, assert identical `build.version/archive/archive_sha256`; assert manifest `id`, `source`, `rom`, `source_identity`, `license` startswith `MIT;`, recipe string equality, `profile.name == 'DMG-CPU-B'` and "not physical hardware evidence", cartridge fields; compare source and ROM SHA-256; `rebuilt == checked_in`; assert header bytes `[0x147..0x149]`; optional `GBB_RGBDS_ARCHIVE` digest check; print `result=byte-identical`. Change: ROM size assertions (`32768` stays for `$10`/`$06`; MBC5 `$1B` fixture size per its own manifest) and header bytes.

**Legacy-RGBDS variants** (`reproduce-magentests.sh`, `reproduce-rtc3test.sh`) cannot reuse the v1.0.1 version-line check (`:20`); keep the digest/compare structure and swap the pinned versions.

---

### `src/player/session.c` / `session.h` (service, file-I/O)

**Analog:** the v1 implementation itself.

**Constants to change** (`session.c:19-24`):
```c
#define PLAYER_SESSION_MAX_ROM_SIZE (2u * 1024u * 1024u)   /* -> 8 MiB, tied to core bound by test */
#define PLAYER_SESSION_MAX_RAM_SIZE 32768u                 /* -> 131072u */
#define PLAYER_SAVE_HEADER_SIZE 51u
#define PLAYER_SAVE_MAGIC "GBBBSAVE"
#define PLAYER_SAVE_VERSION 1u
```
Keep the v1 constants for the `$03` writer; add v2 constants (`64u`, version 2). `read_rom_file` (`:102-125`) allocates `MAX+1` on the heap and bounds `fstat`; it follows the new cap automatically.

**WR-02 removal** (`:158-175`): delete the hard-coded RAM-size map and `battery_unsupported` block:
```c
    out_identity->ram_size = rom[0x149u] == 0x02u ? 8192u : rom[0x149u] == 0x03u ? 32768u : 0u;
    out_identity->battery_backed = rom[0x147u] == 0x03u && out_identity->ram_size != 0u;
    out_identity->battery_unsupported = rom[0x147u] == 0x06u || ...
```
Per Open Question 4, `identify_rom` keeps digest + type; `player_session_replace_rom` (`:177`) fills `ram_size`/`battery_backed`/`rtc_present` from `gbb_battery_size` after `gbb_load_rom`. Remove the field from `player_save_identity` (`session.h:12-21`) and the two branches in `src/player/main.c` (`:517`, `:965`).

**LE helpers + CRC to reuse unchanged** (`:221-247`): `crc32_bytes` (IEEE `0xEDB88320`), `put_u16_le`, `get_u16_le`, `put_u32_le`, `get_u32_le`. Add `put_i64_le`/`get_i64_le` beside them in the same style (explicit shifts, no struct dump).

**Decode with exact-size + identity checks** (`:423-437`) is the template for `decode_save_v2`: size equality first, magic, version, SHA, type, lengths, CRC; copy only after all checks:
```c
    if (size != PLAYER_SAVE_HEADER_SIZE + identity->ram_size ||
        memcmp(bytes, PLAYER_SAVE_MAGIC, 8u) != 0 ||
        get_u16_le(bytes + 8u) != PLAYER_SAVE_VERSION ||
        memcmp(bytes + 10u, identity->rom_sha256, 32u) != 0 ||
        bytes[42u] != identity->cartridge_type || ...
        return false;
```
For v2, validate `ram_len` against the allow-list and `rtc_len in {0,21}`, compute total in `uint64_t`, require bit1 only with bit0, require reserved/zero fields zero, and CRC over bytes 0-59 plus payload.

**Encode** (`:659-706`): field-by-field header write, `gbb_copy_battery`, CRC, `atomic_save`. Replace the stack arrays `bytes[PLAYER_SAVE_HEADER_SIZE + PLAYER_SESSION_MAX_RAM_SIZE]` (`:681`) and `bytes[PLAYER_SAVE_MAX_SIZE + 1u]` (`:464`) with heap buffers (Pitfall 14). Keep the `generation == identity->saved_generation` early return and the `identity->saved_generation = generation` update.

**Rejection flow:** reuse `preserve_rejected_save` (`:379`) and the "rejected and preserved" error text that `test_continuation.c` asserts (`strstr(error, "rejected and preserved")`). Fault hooks to extend with v2 tests are the `PLAYER_SESSION_TEST_FAULT_*` set in `session.h:92-102`, consumed via `consume_test_fault` (`session.c:39-43`).

**Filename literal:** `battery_file_path` (`:249`) formats `-mbc1-%02x-%08x.gbb` for all identities; `$03` must keep it, other types use `-cart-` (Open Question 3).

---

### `src/player/catch_up_policy.{c,h}` (pure utility)

**Analog:** the pure decision helpers `player_save_cadence_observe` and `player_save_transition_resolve` (`session.c:798-835`, declared `session.h:78-92`): pure functions over plain values returning an enum, no SDL. Implement as a separate TU with no SDL/CommonCrypto so it can be linked into the core test leg and run on Linux/Windows (RESEARCH Open Question 1: register as `catch_up_policy_table` in the core inventory, not `player_*`). Use `(uint64_t)now - (uint64_t)saved_at` only after a signed `now > saved_at` test.

---

### `tests/player/test_continuation.c` (multi-process continuation)

**Analog:** itself. Reusable pieces:

**Child spawn with timeout** (`:158-186`): `posix_spawnp(... {executable, "--child", mode, rom_path, pref_path, NULL} ...)`, 10 ms `nanosleep` poll, `CHILD_TIMEOUT_NS` kill. Add the clock as an extra argument (D-21), so the `argc == 5` check in `main` (`:413`) becomes `argc == 6` for the clock-injecting modes.

**Child guest driver** (`:188-257`): `player_session_test_set_pref_path`, create instance, `player_session_replace_rom`, `player_session_lock_battery`, `player_session_load_battery`, `gbb_run(machine, 200000u, ...)`, mode `store`/`resume`/`wrong`/`mutated`, assert `gbb_peek_ram(machine, 0xC00x)`. Hard-coded values to generalise: `CONTINUATION_ROM_SIZE 32768u`, `CONTINUATION_RAM_SIZE`, `SAVE_HEADER_SIZE 51u`, the `identity.ram_size != CONTINUATION_RAM_SIZE` guard (`:200`).

**Test bodies** (`:317-328`): `make_pref_directory`, `get_saved_envelope`, then a second child proves resume. New `player_continuation_mbc3_rtc_*` tests copy this shape and add `result(N) - result(0) == N`.

**CMake registration** (`tests/player/CMakeLists.txt:97-110`): extend the regex `^player_continuation_(resume|missing_save|wrong_rom|mutated_payload)$` and pass the fixture path per test. Every new name must also be added to `tests/player/expected-tests.txt` (alphabetical list; delete `player_session_battery_unsupported` there and its test in `tests/player/test_session.c:1141-1205`).

---

### `fixtures/save-envelope-v1/*` and `tests/scripts/generate-save-envelope-v1.sh`

**Analog (manifest only):** `fixtures/mbc1-continuation/manifest.json`. Generator is a one-time macOS procedure from RESEARCH "v0.1 Save Corpus Recipe" (`git archive v0.1.2` to a fresh temp dir, drive the real writer via `player_session_test_set_pref_path`). No script precedent exists; see "No Analog Found".

---

## Shared Patterns

### Test scaffolding (synthetic ROM, public API)
**Source:** `tests/test_mbc5.c:1-88` (also `tests/test_mbc2.c:1-88`)
**Apply to:** `test_mbc3.c`, `test_mbc3_rtc.c` (black-box part), `test_rtc_battery.c`, `test_magentests.c`, `test_loader_matrix.c`
`REQUIRE` macro, `fix_checksum` over `0x134..0x14C`, `make_rom` builder, `install` (`JP $0200`), `run_to_halt` slice loop. Copy rather than share (project preference: copy over dependency; both Phase 8 tests duplicate the helpers).

### Per-case CTest registration
**Source:** `tests/CMakeLists.txt:32-50`
**Apply to:** every new core test executable
```cmake
foreach(case ...)
  add_test(NAME <family>_${case} COMMAND <exe> <family>_${case})
endforeach()
```
Plus: add every name to `tests/expected-tests.txt` (exact-inventory gate; mismatch fails configure). Core-leg names must not start with `player_` (Pitfall 11).

### Saturating generation bump
**Source:** `src/core/gabbaboy.c:926-931`, `:954-958`, `:1993-1994`, `:2000-2001`
**Apply to:** MBC3 RAM write, RTC register write, `gbb_rtc_catch_up`, block import
```c
if (m->cart.has_battery && m->battery_generation != UINT64_MAX) ++m->battery_generation;
```

### No partial mutation on rejection
**Source:** `gbb_load_rom` (`:1921-1953`): validate, allocate, and only then free-and-swap; `test_mbc5.c:520-566` asserts `previous_rom_intact` after each rejection.
**Apply to:** `gbb_import_battery` with the RTC block, MBC30 variant rejection, v2 player decode (preserve-then-fresh)

### Header-check ordering (D-05 Phase 8)
**Source:** `src/core/gabbaboy.c:1832-1888`
**Apply to:** MBC3 additions and the independent oracle in `test_loader_matrix.c`. Do not reorder existing checks.

### Digest-verified fixtures
**Source:** `cmake/VerifyFixture.cmake` via `tests/CMakeLists.txt:308-316`; manifest at `fixtures/mbc1-continuation/manifest.json`
**Apply to:** every new ROM and `.input` script (`magentests_fixture_digest`, `rtc3test_fixture_digest`, `mbc3_rtc_continuation_fixture_digest`, ...)

### Install exclusion
**Source:** `cmake/ScanForbiddenFixtures.cmake` + `tests/CMakeLists.txt:591-645` (`libbet_install_tree` setup fixture, `gbb_add_mbc_scan_test`)
**Apply to:** `magentests_not_installed` (+ renamed-ROM selftest). rtc3test is not named in D-06; the planner should decide whether to scan it too (same mechanism, one more manifest).

### Mutant-copy control
**Source:** `tests/CMakeLists.txt:72-116`
**Apply to:** the five D-12 RTC mutation controls

### Field-by-field little-endian serialisation
**Source:** `src/player/session.c:231-247` (`put_u16_le`, `get_u16_le`, `put_u32_le`, `get_u32_le`)
**Apply to:** RTC block (core needs its own static copies, core has none: `src/core` cannot include player code), envelope v2

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| Core `rtc_sync` / `rtc_add_seconds` / latch logic in `gabbaboy.c` | model | time-anchored transform | No emulated-time-derived device state outside the per-half-dot loop exists for cartridge code; use RESEARCH Pattern 2 sketch, validated by naive-stepper differential test. Conceptual neighbours: `rumble_changes` saturation, STOP fast-forward at `gabbaboy.c:2361-2371`. |
| `tests/test_rtc3test.c` frame/BG-map scraping | test | scripted-input replay with BG-tile decode | Nothing in `tests/` decodes the BG map or consumes `.input` scripts in a white-box single TU (acceptance does so via the accept library, not by `#include`-ing sources). Combine the `test_mbc5_internal.c` include idiom with `src/accept/input_script.c`; resolve duplicate symbols (this TU must not link the accept library). |
| `tests/scripts/generate-save-envelope-v1.sh` | script | one-shot cross-version build | No script builds an older tagged tree; follow RESEARCH recipe and `verify-phase3-player.sh` for the SDL3 prefix recipe. |
| Legacy-RGBDS (0.4.2 / 0.6.1) reproduction legs in `.github/workflows/fixture-repro.yml` | CI | batch | Existing workflow only handles RGBDS 1.0.1 and a pin-consistency job that reads existing manifests; legacy legs need their own job (RESEARCH A7). |
| Windows/MSVC object-symbol scan in `CheckCoreNoHostClock.cmake` | utility | file-I/O | No existing `nm`/`dumpbin` use; Wave-1 spike on all five CI legs (Pitfall 18). |

## Metadata

**Analog search scope:** `src/core/gabbaboy.c`, `include/gabbaboy/`, `src/player/`, `src/accept/`, `tests/` (core, `player/`, `scripts/`, `acceptance/`), `cmake/`, `fixtures/`
**Files read:** 09-CONTEXT.md, 09-RESEARCH.md, `src/core/gabbaboy.c` (lines 50-165, 786-970, 1830-2030), `tests/test_mbc5.c` (1-140, 520-620), `tests/test_mbc2.c` (1-88), `tests/test_mbc5_internal.c`, `cmake/ScanForbiddenFixtures.cmake`, `tests/scripts/reproduce-mbc1-continuation.sh`, `fixtures/mbc1-continuation/manifest.json`, `src/player/session.c` (selected ranges), `src/player/session.h`, `tests/player/test_continuation.c` (selected ranges), `tests/fuzz_core.c`, `tests/CMakeLists.txt` (selected ranges), `tests/player/CMakeLists.txt` (90-115)
**Pattern extraction date:** 2026-10-11
