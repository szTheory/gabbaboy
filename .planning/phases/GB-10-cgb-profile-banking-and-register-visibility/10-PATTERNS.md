# Phase 10: CGB Profile, Banking and Register Visibility - Pattern Map

**Mapped:** 2026-10-12
**Files analyzed:** 34 new/modified (grouped by plan below)
**Analogs found:** 31 / 34 (3 partial, see "No Analog Found")
**Scope note:** RESEARCH.md already holds the `gabbaboy.c` line-by-line code-site map (sections "Code-site map" A/B/C). This file does NOT repeat it. It supplies the *copyable analog excerpts* for the new test, tool, fixture, CI and API-append files. All analog paths were checked with `git ls-files` (all tracked; none are gitignored mirrors).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `tests/scripts/verify-model-gates.py` | utility (CI scanner) | batch / transform | `tests/scripts/verify-libbet-admission.py` (shape, `--self-test`, `fail(token)`), `tests/scripts/verify-support-ledger.py` (stdlib header) | role-match |
| `docs/model-gates.md` | doc (table mirrored by scanner) | transform | `docs/support/*.md` ledger with `<!-- support-ledger-data-begin -->` markers (`verify-support-ledger.py:21-22`) | role-match |
| `docs/cgb-profile.md` | doc (table mirrored by C test) | transform | same marker pattern; prose contract via `VerifyDocContract.cmake` | role-match |
| `src/core/gabbaboy.c` (tags, banks, post_boot, io_visibility, latch, probe, info, static asserts) | core | request-response / CRUD | self (pre-existing patterns): `serial_unsupported` latch, `gbb_rumble_state` out-param API, `cart_row` tables | exact (self) |
| `include/gabbaboy/gabbaboy.h` (profile, enums, `gbb_info`, 2 functions, error) | public API | request-response | `gbb_error` tail (`GBB_NO_RTC`), `gbb_rumble_state`, `gbb_frame_info` | role-match |
| `tests/test_cgb_profile.c` (create/probe/info/copy_frame/parity) | test | request-response | `tests/test_loader_matrix.c` (oracle `expected_result()`), `tests/test_mbc5.c` | role-match |
| `tests/test_cgb_tables.c` (code-vs-doc diff) | test | transform | `tests/test_mbc5_internal.c` (white-box include) + `doc_contract_*_selftest` CMake mutation pattern | partial |
| `tests/test_cgb_visibility.c` (matrix, KEY0, DEFERRED) | test | request-response | `tests/test_bus.c` (`load_program`, `reject_atomically`, `unsupported_reads`) | exact |
| `tests/test_banking.c` (public VBK/SVBK/echo/DMA) | test | CRUD | `tests/test_bus.c` (`wram_guest`, `echo_hram`), `tests/test_dma.c` | exact |
| `tests/test_banking_internal.c` (`banking_dmg_flat_reference`) | test (white-box metamorphic) | CRUD | `tests/test_mbc5_internal.c` | exact |
| `tests/test_rtc3test.c` (fix `:109` `m->vram[0][...]`) | test (modified) | transform | self | exact |
| `tests/CMakeLists.txt` (registrations, core mutants, doc contract, bench self-test) | config | n/a | self: `test_bus` block, `test_mbc5_internal`, ninth-bit mutant, `gbb_add_expect_exit_test`, `native_guide_rtc_contract` | exact |
| `tests/expected-tests.txt` | config | n/a | self (sorted-equality gate `ExpectedTests.cmake`) | exact |
| `fixtures/cgb-banking/{banking.asm, *.gb x2, manifest.json, LICENSE.txt}` | fixture (original) | file-I/O | `fixtures/mbc5-banking/` | exact |
| `tests/scripts/reproduce-cgb-banking.sh` | utility (repro) | batch | `tests/scripts/reproduce-mbc5-banking.sh` | exact |
| `.github/workflows/fixture-repro.yml` (new steps) | CI config | batch | existing mbc5-banking step (~l.131-136) and `mooneye-mbc-repro` job (l.228-247) | exact |
| `fixtures/mooneye-cgb/{manifest.json, ELIGIBILITY.md, SOURCES.md, LICENSE.txt, FONT-LICENSE.txt, *.gb}` | fixture (third-party derivative) | file-I/O | `fixtures/mooneye-mbc/` | exact |
| `tests/scripts/reproduce-mooneye-cgb.sh` | utility (repro) | batch | `tests/scripts/reproduce-mooneye-mbc.sh` (`--build/--compare/--facts`) | exact |
| `cmake/VerifyMooneyeCgb.cmake` | utility (CMake -P verifier) | batch | `cmake/VerifyMooneyeMbc.cmake` | exact |
| `src/runner/main.c` (third suite, `cgb_cases[]`, `profile`/`expect_stop` fields, `--profile`) | runner | request-response | `mbc_cases[]` + `suites[]` + `MOONEYE_MBC_MANIFEST_SHA256` in same file | exact |
| `src/runner/acceptance.c` (model<->profile fn, remove `:1196` rejection) | runner | request-response | self (`options->model` / `gbb_case_model_known`) | exact (self) |
| `tests/scripts/measure-release-baseline.sh` (`--ab` mode + receipt) | utility | batch | self (`sample_summary`, `validate_pairs`, `--self-test`) | exact (self) |
| `tests/test_bench_ab.cmake` or CTest hooks for A/B self-test | test | batch | `gbb_add_expect_exit_test` + `expect_exit.cmake` | role-match |
| `tests/fuzz_core.c`, `tests/test_loader_matrix.c`, `tests/test_loader_fuzz.c` (profile-parameterise) | test | batch | selves | exact (self) |
| `tests/consumers/{c/main.c,cpp/main.cpp}` (cgb smoke) | test (installed consumer) | request-response | `battery_api_smoke` in `tests/consumers/c/main.c` | exact |
| `docs/native-integration.md` + `native_guide_cgb_contract` CTest + selftests | doc + CMake test | transform | `native_guide_rtc_contract` (`tests/CMakeLists.txt:1134-1142`) + `doc_contract_*_selftest` | exact |
| `docs/support/unreleased.md` | doc | n/a | existing ledger rows in same dir | role-match |
| `.planning/context/DECISIONS.md` (D-070), `LESSONS.md` | doc | n/a | existing rows (`D-069` last row at `:77`) | exact |
| `cmake/ScanForbiddenFixtures.cmake` + install scans | config | batch | Phase 8 `mooneye-mbc` addition (`gbb_add_mbc_scan_test`, `tests/CMakeLists.txt:839-860`) | exact |

---

## Pattern Assignments

### `tests/scripts/verify-model-gates.py` (utility, batch)

**Analog:** `tests/scripts/verify-libbet-admission.py` (RESEARCH's recommended precedent; it is registered in CTest through `expect_exit.cmake`, unlike `verify-support-ledger.py` which only runs as a CI step `python3 tests/scripts/verify-support-ledger.py --self-test`, `.github/workflows/ci.yml:24`). Use the libbet shape; borrow only the header from `verify-support-ledger.py`.

**Header / stdlib-only / ROOT** (`verify-libbet-admission.py:1-26`, `verify-support-ledger.py:1-21`):
```python
#!/usr/bin/env python3
"""Fail-closed admission check ... Standard library only; run as `python3 -I`."""
from __future__ import annotations
import argparse, json, pathlib, re, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[2]
```

**Token-failure convention** (`verify-libbet-admission.py:88-90`). Every failure is `fail("token", detail)` and the CTest regex matches the leading token:
```python
def fail(token: str, detail: str | None = None) -> None:
    raise ValueError(token if detail is None else f"{token}: {detail}")
```
Scanner tokens to define: `gate-untagged-function`, `gate-doc-mismatch`, `gate-unresolved-unknown`, `gate-guard-missing`, `gate-hazard-under-both`.

**Self-test mutant harness** (`:598-605`). Copy `expect()` verbatim; each D-08 mutant is one `expect(token, lambda: verify(mutated_copy), label)` call. Per RESEARCH pitfall 10, build the "untagged new function" mutant by appending a function to a *copy of the real source text*, and assert the scanner's function count equals the independent count (126 at HEAD + new functions):
```python
def expect(token: str, action, label: str) -> None:
    try:
        action()
    except ValueError as error:
        if not str(error).startswith(token):
            fail("self-test", f"{label}: expected {token}, got {error}")
        return
    fail("self-test", f"{label}: mutation was accepted")
```

**Main / exit-code contract** (`:800-837`): `argparse` with `--self-test`, `--release` (R3), `--source`, `--doc`; `try/except (ValueError, OSError)` prints `... failed: {error}` to stderr and returns 1; success prints one fixed line that CTest regex-matches; `raise SystemExit(main())`.

**CTest registration** (`tests/CMakeLists.txt:749-759`, `:760-775`). Do not reuse `gbb_add_expect_exit_test` as-is: it hard-wires `GBB_LIBBET_VERIFIER`. Copy the function body into a `gbb_add_model_gate_test` sibling (or generalise with a verifier argument). Note `$<SEMICOLON>` joining:
```cmake
function(gbb_add_expect_exit_test name code regex)
  set(command "${Python3_EXECUTABLE}" -I "${GBB_LIBBET_VERIFIER}" ${ARGN})
  list(JOIN command "$<SEMICOLON>" joined)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${joined}" -DGBB_EXPECT_CODE=${code} "-DGBB_EXPECT_REGEX=${regex}"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT 30)
endfunction()
```
Mutant inputs: libbet writes mutated manifest copies at configure time with `string(JSON ... SET ...)` + `file(WRITE ...)` into `${PROJECT_BINARY_DIR}/libbet-admission/` (`:762-775`). For the model-gate scanner the mutants are better built inside `--self-test` (Python) AND as 2-3 per-mutant CTests (`model_gates_mutant_deleted_tag`, ...) that pass `--source <mutated copy>`; write the mutated source copies at configure time with `file(READ)` / `string(REPLACE)` / `file(WRITE)`.
All names must start `model_gates` and be added to `tests/expected-tests.txt` in the same commit.

---

### `docs/model-gates.md` and `docs/cgb-profile.md` (doc, transform)

**Analog:** begin/end marker blocks in `docs/support/*.md` parsed by `verify-support-ledger.py:21-22`:
```python
BEGIN = "<!-- support-ledger-data-begin -->"
END = "<!-- support-ledger-data-end -->"
```
Use `<!-- model-gates-begin -->` / `<!-- cgb-post-boot-begin -->` / `<!-- cgb-io-visibility-begin -->` equivalents. Machine-parsed rows go between markers (one row per GATE id; one row per post_boot field and io_visibility register). `test_cgb_tables` and the scanner read only between markers; prose outside is free.

Doc-contract caveat (RESEARCH pitfall 11): any `gbb_`/`GBB_` token in a doc passed to `VerifyDocContract.cmake` must be a real whole-word declaration (comments stripped). Only `docs/native-integration.md` is contract-checked; the two new docs are not, unless you add contracts.

---

### `include/gabbaboy/gabbaboy.h` (public API, append-only)

**Analog:** the existing tails. Enum append (`gbb_error`, lines 17-40): add the comma on `GBB_NO_RTC` and append in the same trailing-comment style.
```c
    GBB_NO_RUMBLE,            /* loaded cartridge has no rumble line (or no ROM) */
    GBB_NO_RTC                /* loaded cartridge has no MBC3 timer (or no ROM) */   /* <- add "," then: */
    GBB_UNSUPPORTED_EXECUTION_MODE /* ... */
} gbb_error;
```
Profile append (`:13-15`): `GBB_PROFILE_DMG_CPU_B = 1` -> add `, GBB_PROFILE_CGB_CPU_E = 2`.

**Out-param + doc-comment shape** to copy for `gbb_probe_rom` / `gbb_get_info` (`gbb_rumble_state`, header ~`:190-205`): leading block comment states every error case, "Outputs are left unchanged on any error", then the prototype. D-02/D-04 text goes in that same style:
```c
 * ... argument returns GBB_INVALID_ARGUMENT; no loaded ROM ... returns GBB_NO_RUMBLE. Outputs are left unchanged on any error.
gbb_error gbb_rumble_state(const gbb_instance *instance, uint8_t *out_on,
                           uint64_t *out_changes);
```
**No existing size-tagged struct.** `gbb_frame_info` (`:73-79` region, `uint32_t width; ... uint64_t completion_half_dots;`) is the only plain out-struct and has no `struct_size`; `gbb_info.struct_size` is a new convention (D-02 owner-veto item 1). Header-size assert goes in `gabbaboy.c` not the header (RESEARCH C5):
```c
_Static_assert(sizeof(gbb_info) == GBB_INFO_SIZE_V1, "gbb_info layout");
```
`_Static_assert` precedent: `src/runner/acceptance.c:675`, `src/player/audio.c:15,17`.

Also update comments at `:126-129` ("only implemented model is bootless DMG-CPU-B"), `:144-149` (CGB flag ignored on DMG), `gbb_copy_frame` doc (D-05), `gbb_peek_ram` doc (follows WRAM bank) in the commits RESEARCH names.

---

### `src/core/gabbaboy.c` — idioms to copy (beyond RESEARCH's site map)

**Deferred-write latch** (generalise `serial_unsupported`). Set sites (`:1211-1217`):
```c
    else if (address == 0xFF01) {
        if (m->serial_active) m->serial_unsupported = 1;
        else m->serial_data = value;
    }
```
Report site, post-`execute` (`:2766-2770`), cleared in `reset_state` (`:666`):
```c
        if (instance->serial_unsupported) {
            instance->serial_unsupported = 0;
            result.reason = GBB_STOP_UNSUPPORTED_BUS;
            return result;
        }
```
Replace with a `bus_unsupported` + `bus_unsupported_address` pair; keep the serial behaviour identical (serial sets the same latch).

**Fail-closed read allow-list** `read_supported` (`:1331-1349`) is a single `||` chain taking `const gbb_instance *m` (may be NULL). Extend with CGB branches guarded by `m != NULL && m->profile == GBB_PROFILE_CGB_CPU_E`, same style as the existing cartridge-RAM clause `(address >= 0xA000 && address <= 0xBFFF && m != NULL && ...)`.

**Create switch** (`:2078-2087`): the one-line `if (profile != GBB_PROFILE_DMG_CPU_B) return GBB_UNSUPPORTED_PROFILE;` becomes a `switch` returning `GBB_UNSUPPORTED_PROFILE` for any other value; `calloc` leaves every new field zero, so `reset_state` must set `wram_bank = 1` (pitfall 1).

**Test seams** (non-header, `extern` in tests): `gbb_test_observer_set/count`, `gbb_test_cpu_snapshot` (`:534-545`, `:2632`). Add `gbb_test_last_unsupported_address` and `gbb_test_bank_state` in this style; declare `extern` in tests exactly as `tests/test_bus.c:15-17`.

**Tag comments** (D-08) are comment-only. Never quote `if ((m->joypad_select & 0x20u) == 0)` or `& 1u) << 8` in a tag (configure-time mutant anchors, `tests/acceptance/CMakeLists.txt:288`, `tests/CMakeLists.txt:209`).

---

### `tests/test_cgb_visibility.c` (test, request-response)

**Analog:** `tests/test_bus.c` (exact; owner decision D-11 names it).

**Includes / REQUIRE / seams** (`:1-17`):
```c
#include "gabbaboy/gabbaboy.h"
#include <assert.h> <stdio.h> <stdlib.h> <string.h>
#define REQUIRE(x) do { if (!(x)) { printf("not ok 1 - %s\n", #x); fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)
#define PASS(name) do { printf("ok 1 - %s\n", name); } while (0)
extern void gbb_test_cpu_snapshot(const gbb_instance *, gbb_trace_record *);
```

**Synthetic ROM loader** (`:19-44`). Copy and add a `profile` and a `$143` parameter; set `rom[0x143]` BEFORE `fix_checksum` (checksum covers 0x134..0x14C). The `0xe7` trick makes the checksum wrap to 0 only for CGB flag 0; for other `$143` values do not `assert(rom[0x14d]==0)`:
```c
static void fix_checksum(uint8_t *rom) {
    uint8_t sum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14D] = sum;
}
static gbb_instance *load_program(const uint8_t *program, size_t length) {
    uint8_t *rom = calloc(1, 32768);
    if (rom == NULL) return NULL;
    memcpy(rom + 0x100, program, length);
    rom[0x134] = 0xe7;
    fix_checksum(rom);
    ...
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK || gbb_load_rom(machine, rom, 32768) != GBB_OK) { gbb_destroy(machine); machine = NULL; }
```

**Guest idiom** for cells: raw opcode arrays, `LDH (a8),A` = `0xE0,n`, `LDH A,(a8)` = `0xF0,n` (`unsupported_reads`, `:124-137`): `{0xf0,missing_io[i]}` reads one IO address then stops. Store results to HRAM (`0xE0,0x80+k`) and read with `gbb_peek_ram(m, 0xFF80+k)` (`echo_hram`, `:228-240`).

**DEFERRED-read stop is atomic** and tested by `reject_atomically` (`:46-67`): asserts `GBB_STOP_UNSUPPORTED_BUS`, `consumed_half_dots == 0`, trace/diagnostic buffers untouched, CPU snapshot `memcmp`-equal. Reuse verbatim for DEFERRED *read* cells. For DEFERRED *writes*, assert the stop happens after the instruction (latch) and only that the write did not take effect (pitfall 5), via `gbb_test_last_unsupported_address`.

**Dispatch** (`:264-280`): `argv[1]` case name, `printf("1..1\n")`, `PASS("<ctest name>")`, `return 2` for unknown. Registration (`tests/CMakeLists.txt:275-281`):
```cmake
add_executable(test_bus test_bus.c)
target_link_libraries(test_bus PRIVATE GabbaBoy::core)
target_compile_features(test_bus PRIVATE c_std_17)
set_target_properties(test_bus PROPERTIES C_EXTENSIONS OFF)
foreach(case wram_guest echo_hram absent_cart preflight unsupported_reads ...)
  add_test(NAME bus_${case} COMMAND test_bus ${case})
endforeach()
```
Use `foreach(case ...)` with prefix `cgb_visibility_`. Insert before `gabbaboy_verify_registered_tests()` (last line, `:1194`) and list every name in `tests/expected-tests.txt` (e.g. `bus_*` rows at `:95-102`).

Negative controls D-11: "flip one expected byte" and "run other column" can be in-test (table copy mutated, assert mismatch detected via a helper `run_cell()` returning pass/fail); "delete a row" = in-test sweep over FF00..FF7F against a local copy with one row removed.

---

### `tests/test_cgb_profile.c` (test, request-response)

**Analog:** `tests/test_loader_matrix.c` for the independent oracle; `tests/test_mbc5.c` for dispatch.

**Independent oracle idiom** (`test_loader_matrix.c:73-88`): a hand-typed `expected_result()` written from the decision text, not from the core. For probe/load parity, call it for load, `gbb_probe_rom` for probe, and assert both equal the oracle on every row of the matrix. The profile-dependent term is the only extra branch:
```c
static gbb_error expected_result(uint8_t type, uint8_t rom_code, uint8_t ram_code, size_t length, int checksum_ok) {
    if (length > 8u * MIB) return GBB_ROM_TOO_LARGE;
    ...
    if (!checksum_ok) return GBB_INVALID_ROM;
    ...
    return GBB_OK;
}
```
Add `profile` and `cgb_flag` parameters; PGB (bit7 && (bit2||bit3)) on CGB profile returns `GBB_UNSUPPORTED_EXECUTION_MODE` *last* (RESEARCH: after `:2065`). Negative control "skewed probe": compile a second tiny validator in the test with the PGB check moved first and assert the parity loop would detect it.

`struct_size` cases (0, 27, 28, larger with sentinel tail bytes preserved) follow `tests/test_battery.c`'s "outputs untouched on error" pattern (`consumers/c/main.c` uses `memset(output, 0xA7, ...)` then checks every byte; same sentinel trick).

---

### `tests/test_banking.c` and `tests/test_banking_internal.c` (test, CRUD)

**Analog 1 (public):** `tests/test_bus.c` `wram_guest` / `echo_hram` (guest writes via real CPU, reads with `gbb_peek_ram`).
```c
const uint8_t program[] = {0x21,0x00,0xC0,0x3E,0x42,0x77,0x7E};   /* LD HL,$C000; LD A,$42; LD (HL),A; LD A,(HL) */
gbb_run_result r = gbb_run(m, 56, NULL, 0);
REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 56);
REQUIRE(gbb_peek_ram(m, 0xC000) == 0x42);
```
Echo pair (`:228-233`): write C000, read E000 via `gbb_peek_ram(m, 0xE000)`. Extend with SVBK writes (`0xE0,0x70`) then D000/F000.

**Analog 2 (white-box, `banking_dmg_flat_reference`):** `tests/test_mbc5_internal.c`. The whole TU includes the core and must NOT link `GabbaBoy::core`:
```c
#include "../src/core/gabbaboy.c"
#include <stdio.h>
#define REQUIRE(x) do { if (!(x)) { fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)
...
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    write8(m, 0x4000u, 0x08u);
```
Registration (`tests/CMakeLists.txt:188-192`): `target_include_directories(... PRIVATE "${PROJECT_SOURCE_DIR}/include")`, no link library. Drive `read8`/`write8` directly with LCD off and a fixed-seed PRNG; assert `m->vram_bank == 0 && m->wram_bank == 1` per step.

**Core mutants for echo/DMA bank (D-19, RESEARCH "Core-mutant controls"):** copy the ninth-bit block exactly (`tests/CMakeLists.txt:206-250`): `set_property(... CMAKE_CONFIGURE_DEPENDS ...)`, `file(READ)`, `string(FIND ... REVERSE)` exactly-once check with `message(FATAL_ERROR ...)`, `string(REPLACE)`, `file(WRITE)`, a `STATIC` mutant library with `GBB_BUILD_REVISION="...-mutant" GBB_BUILD_QUALIFIED=0`, a mutant test executable, and two `expect_exit.cmake` tests: one expecting `-DGBB_EXPECT_CODE=1` + the REQUIRE text regex, one in-mutant control expecting code 0:
```cmake
add_test(NAME mbc5_ninth_bit_mutant_bank_1ff
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_mbc5_ninth_bit_mutant>;mbc5_bank_1ff;${PROJECT_SOURCE_DIR}/fixtures/mbc5-banking/banking.gb"
    -DGBB_EXPECT_CODE=1 "-DGBB_EXPECT_REGEX=r.3. == 0x01u"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
```
Anchors for the new mutants must be strings that occur once after the reshape (e.g. the new `wram_index` F000-FDFF line); pick them after the array commit lands.

---

### `fixtures/cgb-banking/` + `tests/scripts/reproduce-cgb-banking.sh` (fixture, file-I/O)

**Analog:** `fixtures/mbc5-banking/{banking.asm, manifest.json, LICENSE.txt, banking.gb}` and `tests/scripts/reproduce-mbc5-banking.sh`.

**Assembly conventions** (`banking.asm:1-45`): header comment naming the protocol, `DEF RESULT_PASS EQU $A5` / `DEF RESULT_FAIL EQU $EE`, sticky `CheckEq` macro, `SECTION "Entry", ROM0[$0100]  jp Start  ds $0150 - @, $00`, `di`, `ldh [$FF40],a` LCD off, clear result bytes at C000.
```asm
MACRO CheckEq
    cp \1
    jr z, .ok\@
    ld a, $FF
    ld [\2], a
.ok\@:
ENDM
```
For two builds from one source, branch on entry A (`$01` DMG profile, `$11` CGB profiles; the core sets A in `reset_state`) and on a `$143` byte read from ROM. Build recipes differ only by `rgbfix -c` vs plain `rgbfix` flags (`mbc5` uses `rgbfix -f hg -p 0 -m 0x1E -r 4`).

**Manifest** (`fixtures/mbc5-banking/manifest.json`): copy key set exactly — `id`, `source`, `source_identity`, `source_sha256`, `license`, `build{assembler, version "1.0.1", archive, archive_sha256 "2f6f13c6ec98...", ci_archive, ci_archive_sha256 "80a5cad8da...", recipe}`, `rom`, `size_bytes`, `sha256`, `cartridge`, `profile{name, boot, applicability}`, `protocol{markers, result_bytes, variants..., timeout_half_dots}`, `evidence_class`, `scope_limits[]`. Two ROMs: RESEARCH says use a `fixtures[]` array so `cmake/VerifyFixtureManifest.cmake` works (see `mbc5` single top-level form; `VerifyFixture.cmake` is per-ROM). Profile name here is `CGB-CPU-E` for the CGB build and also records the DMG-profile control run. `evidence_class` must stay "original software fixture plus synthetic oracle, not hardware evidence".

**Reproduce script skeleton** (`reproduce-mbc5-banking.sh:1-45`): `set -euo pipefail`, `repo_root`, `mktemp -d` + `trap cleanup EXIT`, per-tool `--version` equality check against `v1.0.1` (local is 1.0.4: executors fetch the pinned archive to a temp dir and prepend `PATH`), `rgbasm`/`rgblink`/`rgbfix`, then an embedded `python3 - ... <<'PY'` that cross-checks manifest vs `tracer`/`visible-demo`/`mbc1-continuation` RGBDS pin, source sha, rebuilt==checked-in bytes, optional `GBB_RGBDS_ARCHIVE` / `GBB_RGBDS_ARCHIVE_SHA256`, and finally prints `result=byte-identical`. Copy the structure; loop over two ROMs.

**Guest test driver** (test_mbc5.c `mbc5_banking_guest`, `:835-861`): read ROM, assert header bytes, `gbb_load_rom`, run to halt, `gbb_peek_ram(machine, 0xC00x)` markers, `0xC000 == 0xA5`, `0xC001 != 0xEE`. In-memory variants never written to disk (`rom[0x147]=0x1B; fix_checksum(rom);`, `:865-885`). Use the same for negative controls (i) patched expected value -> `$EE`, (ii) CGB build on DMG profile, (iii) skip-SVBK variant. Register as:
```cmake
add_test(NAME mbc5_banking_guest
  COMMAND test_mbc5 mbc5_banking_guest ${PROJECT_SOURCE_DIR}/fixtures/mbc5-banking/banking.gb)
```
Digest test uses `VerifyFixtureManifest.cmake` (see `tests/CMakeLists.txt:445-465` for `-P VerifyFixture.cmake` calls); name it `cgb_banking_fixture_digest`.

**CI step** (`.github/workflows/fixture-repro.yml:131-136`):
```yaml
      - name: Reproduce MBC5 banking fixture bytes
        shell: bash
        run: |
          test -s tests/expected-tests.txt
          GBB_RGBDS_ARCHIVE="$RUNNER_TEMP/rgbds-$RGBDS_RELEASE_VERSION/$RGBDS_ARCHIVE" \
            GBB_RGBDS_ARCHIVE_SHA256="$RGBDS_ARCHIVE_SHA256" \
            bash tests/scripts/reproduce-mbc5-banking.sh
```
Also extend the leading pin-consistency Python block (`fixture-repro.yml:28-43`) so `cgb-banking`'s `build` object is compared with the others. Check `.gitattributes` marks the new `.gb`/`.gbc` binary (RESEARCH A5; libbet precedent in `GITATTRIBUTES_LINES`: `fixtures/libbet/libbet.gb -text`).

---

### `fixtures/mooneye-cgb/` + `tests/scripts/reproduce-mooneye-cgb.sh` + `cmake/VerifyMooneyeCgb.cmake` (third-party fixture)

**Analog:** `fixtures/mooneye-mbc/` (full copy pattern), `tests/scripts/reproduce-mooneye-mbc.sh`, `cmake/VerifyMooneyeMbc.cmake`.

**Manifest shape** (`fixtures/mooneye-mbc/manifest.json:1-50`): `suite{name, revision "31510e12...", tree_sha1, license, upstream}`, `parent_references[]` (three `../mooneye/...` files with sha256 and role: `headless-report-patch`, `zero-font-source`, `builder-pin`), `replacement_asset`, `inventory_status`, `required_roms[]`, `fixtures[]` (`id, rom, category, eligible, result_pc, ...`), `categories`. No `builder` object (the pin is read from the parent manifest; `builder-pin-mismatch` token). For CGB add per-fixture `model_pass`, `target_revision`, `expect_stop` (and expected last-read address for the two staged `expected-unsupported` rows); do not add new top-level fields beyond that (D-25/D-26).

**ELIGIBILITY.md** (`fixtures/mooneye-mbc/ELIGIBILITY.md`): sections "Inventory", "Evidence class (D-30)" (what is and is not claimed; "no CGB claim" becomes "CGB A-E only, never CGB-E alone"), "Per-ROM program-counter table" (ROM alias | result_pc | pass callback | fail callbacks | budget). Add the narrower C3 claim: "reaching FF76 proves FF00-FF75 passed" holds for `boot_hwio-C` only; `unused_hwio-C` unmapped rows come after FF76.

**CMake verifier** (`VerifyMooneyeMbc.cmake:1-60`): `GBB_MOONEYE_DIR`, `GBB_MANIFEST` (tamper control), `GBB_MODE` (digest | inventory | pc-table), `GBB_RUNNER_SOURCE`; `cmake_path(ABSOLUTE_PATH ...)`, `string(JSON ... ERROR_VARIABLE json_error LENGTH ...)`, helper `gbb_fixture_field(out index field)`, counts per category, loops `foreach(index RANGE 0 N)` with duplicate-id/ROM checks and local-filename regex `[/\\\\]|\\.\\.`. Hard-coded counts (15, mbc2 7 / mbc5 8) become 4 and the CGB categories. Row-parse markers become `gbb:cgb-rows-begin/end`.

**CTest registration set** (`tests/CMakeLists.txt:542-575`): `mooneye_cgb_fixture_digest`, `_eligible_inventory`, `_pc_table`, plus tamper tests:
```cmake
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/mooneye-mbc-tamper")
file(READ "${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc/manifest.json" GBB_MBC_MANIFEST_JSON)
string(JSON GBB_MBC_TAMPERED_JSON SET "${GBB_MBC_MANIFEST_JSON}" fixtures 0 result_pc "\"0x407f\"")
file(WRITE "${PROJECT_BINARY_DIR}/mooneye-mbc-tamper/manifest.json" "${GBB_MBC_TAMPERED_JSON}")
add_test(NAME mooneye_mbc_pc_table_tamper
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_MODE=pc-table;-DGBB_MANIFEST=...;-DGBB_MOONEYE_DIR=...;-DGBB_RUNNER_SOURCE=.../src/runner/main.c;-P;.../cmake/VerifyMooneyeMbc.cmake"
    -DGBB_EXPECT_CODE=1 -DGBB_EXPECT_REGEX=pc-table-mismatch
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
```
Unknown-manifest control (raw-SHA gate): `configure_file(... COPYONLY)` then `file(APPEND ... " ")`, runner `--manifest ... --suite` expects exit 2 + `invalid-manifest` (`:566-577`). Suite + per-case tests (`:665-690`): `add_test(NAME mooneye_mbc_required_suite COMMAND gabbaboy-runner --manifest ${GBB_MBC_MANIFEST} --suite --receipt)` with `PASS_REGULAR_EXPRESSION "suite eligible=15 executed=15 status=pass.*suite categories mbc2=7/7 mbc5=8/8"`, and a `foreach(entry IN LISTS GBB_MBC_CASES)` of `alias:callback_pc:result_pc` strings split with `string(REPLACE ":" ";" parts ...)`. For CGB the two staged ROMs need a distinct expected status (`status=expected-unsupported ... stop=unsupported-bus`), and RESEARCH C11 flags that `boot_regs-cgb`/`boot_div-cgbABCDE` end in `quit_check_asserts` (single shared callback; pass_cb == fail_cb, like `tim00` in `cases[]` with `0x4000,0x4000`), so copy the `tim00` row convention (`main.c:60-64`) rather than the mbc rows.

**Runner rows** (`src/runner/main.c`, Phase 8 additions). Add a third `*_cases[]` between `gbb:cgb-rows-begin/end`, a new `MOONEYE_CGB_MANIFEST_SHA256` define, and a third `suites[]` entry:
```c
#define MOONEYE_MBC_MANIFEST_SHA256 "9800c795fcf033abd6bda2e171af6c22d27e745f2b5946fc49bd0f9ce2fb5801"
static const suite_def suites[] = {
    {MOONEYE_MANIFEST_SHA256, MOONEYE_PATCH_SHA256, cases, sizeof(cases)/sizeof(cases[0]), 0},
    {MOONEYE_MBC_MANIFEST_SHA256, MOONEYE_PATCH_SHA256, mbc_cases, sizeof(mbc_cases)/sizeof(mbc_cases[0]), 1}
};
```
`fixture_case` (`:32-49`) gains `profile` and `expect_stop` fields; add them at the END of the struct so existing positional initialisers stay valid only if you also append `0`/defaults... in practice every existing row ends with `{..}, N}` for `fail_callback_pcs, fail_callback_count`; designated-order means new trailing fields default to zero when omitted, so appending fields at the end preserves all DMG rows byte-for-byte. Hard-coded literals to parametrise: `profile=DMG-CPU-B` at `:266, :280, :303`, `gbb_create(GBB_PROFILE_DMG_CPU_B` at `:214, :241, :295`; `category_names[2]` (`:393`). `observe_case` (`:241-264`) must print `mooneye.<alias>.frame\tnot-applicable` for CGB rows (`gbb_copy_frame` returns UNSUPPORTED_PROFILE).

**Repro script** (`reproduce-mooneye-mbc.sh:1-40`): `--build OUTDIR | --compare FIXTURE_DIR | --facts OUTDIR`, `outside_repo()` guard, `pin_sha()` against parent files, `roms=(...)` list + `source_of()`; swap the list for `misc/boot_regs-cgb`, `misc/boot_div-cgbABCDE`, `misc/boot_hwio-C`, `misc/bits/unused_hwio-C` (note the `misc/bits/` subpath for `unused_hwio-C`). CI job to copy: `fixture-repro.yml:228-247` (`mooneye-mbc-repro`, `bash tests/scripts/reproduce-mooneye-mbc.sh --compare fixtures/mooneye-mbc`, upload evidence artifact).

---

### `src/runner/main.c` / `src/runner/acceptance.c` (runner, request-response)

**Analog:** self. Two concrete excerpts to modify.

Model/profile threading in acceptance (`acceptance.c:1186-1198`):
```c
    const char *model = options->model != NULL ? options->model : "dmg-cpu-b";
    ...
    gbb_case_applicability_kind kind = gbb_case_applicability(c, model, options->revision);
    if (kind == GBB_CASE_EXCLUDED_MODEL || kind == GBB_CASE_EXCLUDED_REVISION) {
        printf("acceptance id=%s status=excluded reason=%s model=%s\n", ...);
        *excluded = 1;
        return EXIT_EXCLUDED;
    }
    if (strcmp(model, "dmg-cpu-b") != 0) {            /* <- remove (D-25) */
        printf("acceptance id=%s status=unsupported reason=unsupported-profile model=%s\n", c->id, model);
        return EXIT_UNSUPPORTED;
    }
```
Keep the applicability check ABOVE the removed block so frozen test `acceptance_libbet_excluded_cgb-cpu-e` (`tests/acceptance/CMakeLists.txt:125-127`) still prints `status=excluded reason=unsupported-model` (RESEARCH pitfall 7). `gbb_case_model_known` (`src/runner/cases.c:325-327`) already accepts `cgb-cpu-e`.

Single mapping function: one `static`/shared `gbb_profile gbb_runner_profile_for_model(const char *model, int *ok)` plus the reverse label function; replace every `GBB_PROFILE_DMG_CPU_B` / `"model=dmg-cpu-b"` / `profile=DMG-CPU-B` literal (site lists in RESEARCH section C). DMG output lines must remain byte-identical (baseline).

---

### `tests/scripts/measure-release-baseline.sh` (`--ab` mode)

**Analog:** self. Argument handling currently (`:5-7`):
```bash
SELF_TEST=false
if [[ "${1:-}" == "--self-test" ]]; then SELF_TEST=true; shift; fi
[[ $# -eq 0 ]] || { echo "usage: $0 [--self-test]" >&2; exit 2; }
```
Extend to accept `--ab <base> <head>`; keep the numeric-bound checks on `GBB_RELEASE_MEASURE_SAMPLES` (3..30), `WARMUPS` (1..20), timeouts (`:14-17`). Python body runs via `python3 - ... <<'PY'` (heredoc, not `-I`); the AB branch can live in the same heredoc.

Reusable helpers:
```python
def require(ok, message):
    if not ok:
        raise SystemExit(message)
def sample_summary(values):
    require(bool(values), "zero samples cannot produce a summary")
    ...
    return {"count": len(values), "median": statistics.median(values), "min": min(values),
            "max": max(values), "mean": avg, "sample_standard_deviation": stdev,
            "approx_95_percent_mean_margin": 1.96 * stdev / (len(values) ** 0.5)}
```
Self-test style (`:107-120`): call the validator with a bad input inside `try/except SystemExit: pass / else: raise SystemExit("self-test: ... accepted")`; copy that for "mutated digest" and "receipt missing a field". Digest to enforce on both builds: `correctness_digest_fnv1a64=4c7a57ff3d50d228` parsed from the same `mode=... correctness_digest_fnv1a64=...` line the existing sample loop reads (RESEARCH "Benchmark mechanics").

Existing gap to be aware of: nothing in `tests/CMakeLists.txt` or `ci.yml` currently registers this script (grep found only the file itself and `.planning`), so the A/B self-test CTest is a first. Use `add_test` with `COMMAND bash script --ab ...` guarded by `NOT WIN32`, or run via `${CMAKE_COMMAND} -P` wrapper; Windows constraint (RESEARCH pitfall 14): no `taskset`, no `/proc`, no literal `python3` in CTest commands. If the self-test must run on Windows legs, the AB logic should be in a `-I` Python file rather than a bash heredoc. The bash wrapper has no Windows precedent, so confirm which legs run `ctest` over the full set before gating on `NOT WIN32`.

---

### `tests/CMakeLists.txt` doc-contract additions (`native_guide_cgb_contract`, D-21 ADR tie)

**Analog:** `native_guide_rtc_contract` (`tests/CMakeLists.txt:1134-1142`) and the selftest family (`:1147-1192`).
```cmake
add_test(NAME native_guide_rtc_contract
  COMMAND ${CMAKE_COMMAND}
    -DGBB_DOC=${PROJECT_SOURCE_DIR}/docs/native-integration.md
    "-DGBB_DECLARATIONS=${PROJECT_SOURCE_DIR}/include/gabbaboy/gabbaboy.h;${PROJECT_SOURCE_DIR}/examples/relocated-c/CMakeLists.txt"
    "-DGBB_REQUIRED=${GBB_NATIVE_GUIDE_RTC_PHRASES}"
    "-DGBB_SCOPE_START=`gbb_rtc_catch_up` applies host wall-clock time"
    -P ${GBB_DOC_CONTRACT_SCRIPT})
set_tests_properties(native_guide_rtc_contract PROPERTIES
  PASS_REGULAR_EXPRESSION "doc-contract pass identifiers=[1-9][0-9]* phrases=12[^0-9]")
```
Phrase list `GBB_NATIVE_GUIDE_RTC_PHRASES` is a CMake list of literal backticked strings defined just above (`:1128-1133`). For the ADR tie (D-21) call the same script with `GBB_DOC=<DECISIONS.md or docs/cgb-profile.md>` and `GBB_DECLARATIONS=.../src/core/gabbaboy.c` (comments are stripped, so the ADR macro names must be real `#define`s). Negative controls: `file(WRITE "${GBB_DOC_SELFTEST}/x.md" ...)` + `expect_exit.cmake` with `GBB_EXPECT_CODE=1` + `doc-contract-undeclared: <id>` / `doc-contract-missing: <phrase>`, `GBB_FORBID_REGEX` to prove the failure is the intended one.

---

### `tests/consumers/{c,cpp}` (installed consumer smoke)

**Analog:** `battery_api_smoke` (`tests/consumers/c/main.c:7-30`): local `rom[]` built with explicit header bytes + checksum loop, `gbb_create`/`gbb_load_rom` under `goto done` error flow, sentinel `0xA7` fill to assert outputs untouched on error. Add `cgb_api_smoke`: `gbb_create(GBB_PROFILE_CGB_CPU_E, ...)`, `gbb_probe_rom` (struct_size 28), `gbb_get_info`, and a `$C0` ROM on DMG expecting `GBB_INFO_CGB_ONLY_ON_DMG`. The api-coverage gate is satisfied by the consumers calling each new symbol. Registered names (`installed_consumer_c`, `installed_consumer_cpp`) are in the exclusion list in `cmake/ExpectedTests.cmake`; adding a case inside the existing executable avoids new names.

---

### Shared Patterns

#### Test registration discipline
**Source:** `cmake/ExpectedTests.cmake:1-33`, `tests/CMakeLists.txt:1194`
**Apply to:** every new `add_test` (including selftests and mutants).
`gabbaboy_verify_registered_tests()` sorts both lists and `FATAL_ERROR`s on inequality at configure time, so every new CTest name must be appended to `tests/expected-tests.txt` in the same commit and registered BEFORE line `:1194`. The baseline inventory check (`cmake/VerifyDmgBaseline.cmake:422-431`) fails only on *removed* frozen names; additions are free (baseline has 314 `inventory.*` lines). New prefixes: `cgb_`, `banking_`, `model_gates`, `mooneye_cgb_`, `bench_ab`, `adr_half_dot`, `native_guide_cgb_contract`, `runner_profile`.

#### Exact-exit-code negative controls
**Source:** `tests/expect_exit.cmake:1-70`
**Apply to:** every Python/CMake verifier negative control.
Inputs `GBB_CMD` (list), `GBB_EXPECT_CODE` (decimal), `GBB_EXPECT_REGEX`, optional `GBB_FORBID_REGEX`, `GBB_WORKDIR`, `GBB_EXPECT_FILE*`. A different non-zero code fails, so a crash is never mistaken for the expected rejection:
```cmake
add_test(NAME x COMMAND ${CMAKE_COMMAND}
  "-DGBB_CMD=<prog>;<args>" -DGBB_EXPECT_CODE=1 "-DGBB_EXPECT_REGEX=<token>"
  -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
```

#### Configure-time mutants
**Source:** `tests/CMakeLists.txt:206-250`, `tests/acceptance/CMakeLists.txt:288`
**Apply to:** banking core mutants (echo ignores bank; DMA reads wrong bank), optional KEY0-writable mutant.
Exactly-once anchor via `string(FIND ...)` forward and `REVERSE`, `message(FATAL_ERROR ...)` otherwise; text kept quoted (it contains semicolons); mutant library not installed or exported.

#### Fixture manifest + provenance
**Source:** `fixtures/mbc5-banking/manifest.json`, `fixtures/mooneye-mbc/manifest.json`, `SOURCES.md`, `ELIGIBILITY.md`, `LICENSE.txt`, `FONT-LICENSE.txt`
**Apply to:** `fixtures/cgb-banking/`, `fixtures/mooneye-cgb/`.
Every fixture: sha256 of source and ROM, pinned RGBDS 1.0.1 or WLA-DX 91c52b1f pin read by digest from the parent manifest, `scope_limits[]`, `evidence_class`, no boot ROMs, explicit "not hardware evidence" for original fixtures; third-party derivatives carry upstream revision/tree and MIT notice.

#### Fail-closed unsupported-bus
**Source:** `src/core/gabbaboy.c:1331-1349` (read pre-flight), `:1211-1217` + `:2766-2770` (latch), `tests/test_bus.c:46-67` (`reject_atomically`)
**Apply to:** all DEFERRED cells and the CGB STOP-armed path. Reads stop atomically before any state change; writes stop after retire with the write dropped (documented asymmetry, RESEARCH C10).

#### DMG byte-identity gate
**Source:** `tests/scripts/verify-dmg-baseline.sh`, `tests/baseline/dmg-cpu-b-v1.txt`, `tests/baseline/CHANGES.md`
**Apply to:** after every wave touching `gabbaboy.c` or `src/runner/*`; zero ledger lines may change; new tests must not add `acceptance.*`/`mooneye.*` ledger keys (the comparator reports `extra:`, `VerifyDmgBaseline.cmake:447-452`). Mooneye CGB `--observe` lines must not enter the baseline keys.

#### Pinned-tool temp-dir discipline
**Source:** `reproduce-mbc5-banking.sh:9-26`, `reproduce-mooneye-mbc.sh:30-33` (`outside_repo`)
**Apply to:** all repro scripts: build products only under `mktemp -d`/outside the working tree; version equality check against the pinned tool; never run scripts from inside a downloaded archive directory.

---

## No Analog Found

| File / Concern | Role | Data Flow | Reason |
|---|---|---|---|
| `gbb_info` `struct_size` in/out convention | public API | request-response | No existing size-tagged struct in `gabbaboy.h`; `gbb_frame_info` has no size field. Follow D-02/D-04 text and RESEARCH section A; owner-veto item 1. |
| `tests/test_cgb_tables.c` doc-diff | test | transform | No existing C test parses a Markdown doc. Closest: `VerifyDocContract.cmake` (CMake) for the doc side and `test_mbc5_internal.c` for white-box access to `post_boot[]`/`io_visibility[]`. Mutated-doc/mutated-table controls can be written at configure time with `file(READ)/string(REPLACE)/file(WRITE)` (the `doc-contract-selftest` approach) and passed as a path argument to the test executable. |
| `bench_ab` CTest on all OS legs | test | batch | `measure-release-baseline.sh` is not registered in CTest or CI today and is bash with embedded `python3`. No precedent for a Windows-portable timing self-test; decide wrapper vs `-I` Python (see script section). |
| `expected-unsupported` runner status | runner | request-response | Runner today maps every non-budget stop to a generic `unsupported` (`unsupported_core_stop()` `main.c:150-155`) and exits 0 only on `pass`. No existing "pass iff stopped at declared address" status; design per RESEARCH "Runner row fields to add". |

## Metadata

**Analog search scope:** `tests/`, `tests/scripts/`, `cmake/`, `fixtures/{mbc5-banking,mooneye-mbc,mooneye,magentests}`, `include/gabbaboy/`, `src/core/`, `src/runner/`, `.github/workflows/{ci,fixture-repro}.yml`, `docs/`.
**Files read for excerpts:** `tests/test_bus.c`, `tests/test_mbc5_internal.c`, `tests/test_loader_matrix.c` (oracle), `tests/test_mbc5.c` (banking guest), `tests/consumers/c/main.c`, `tests/CMakeLists.txt` (170-285, 536-700, 735-800, 1128-1194), `tests/expect_exit.cmake`, `cmake/{VerifyDocContract,VerifyMooneyeMbc,ExpectedTests}.cmake`, `tests/scripts/{verify-libbet-admission.py,verify-support-ledger.py,reproduce-mbc5-banking.sh,reproduce-mooneye-mbc.sh,measure-release-baseline.sh}`, `fixtures/mbc5-banking/*`, `fixtures/mooneye-mbc/*`, `src/runner/main.c`, `src/runner/acceptance.c`, `include/gabbaboy/gabbaboy.h`, `src/core/gabbaboy.c` (targeted).
**Tracked-source gate (#3645):** all analog paths verified with `git ls-files`; no `.gsd/capabilities` mirrors involved.
**Pattern extraction date:** 2026-10-12
