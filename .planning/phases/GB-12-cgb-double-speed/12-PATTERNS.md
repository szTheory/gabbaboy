# Phase 12: CGB Double Speed - Pattern Map

**Mapped:** 2026-10-13
**Files analyzed:** 27 new/modified groups
**Analogs found:** 25 / 27 (all analog paths verified git-tracked; line numbers are HEAD `fb45111`)

Line numbers in `src/core/gabbaboy.c` match RESEARCH "Code Map" (`a719721`; only docs changed since).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `src/core/gabbaboy.c` stall branch in `gbb_run_internal` | core/cpu loop | event-driven (budgeted stepping) | HALT branch, same function `:3970-3990` | exact |
| `src/core/gabbaboy.c` `stop_case`, `divider_reset`, `cpu_stalled`, tick sites | core/helpers | transform | `halt_bug_keeps_control_target` `:3905`, `instruction_cost` `:3599` | role |
| `src/core/gabbaboy_test.h` + `gbb_test_speed_state` | test seam | request-response | `gbb_test_bank_state` `gabbaboy.c:3897-3903` | exact |
| `tests/test_cgb_speed_internal.c` (+ partition sweeps) | test, white-box single TU | batch | `tests/test_cgb_colour_internal.c` | exact |
| `tests/CMakeLists.txt` runtime-mask mutant helper (`GBB_P12_MUT`) | build/test config | batch | `gbb_colour_mutant` `:1942-1990` | role (variant) |
| `cgb_speed_*static_assert_mutant` (if added) | test config | batch | `cgb_adr_half_dot_static_assert_mutant` `:1671-1691` | exact |
| `tests/test_age.c` (AGE driver) | test, ROM runner | request-response | `src/runner/main.c` `cgb_cases[]` + `tests/test_mooneye_cgb_div_sweep.c` | partial (no AGE precedent) |
| `tests/external/cgb-speed-dispositions.json` | data/config | record | `tests/external/cgb-ppu-dispositions.json` | exact |
| `tests/scripts/verify-cgb-speed-dispositions.py` | verifier | transform | `tests/scripts/verify-external-dispositions.py` | exact |
| `fixtures/cgb-speed/*` | fixture (original) | file-I/O | `fixtures/cgb-colour/` | exact |
| `fixtures/age/*` | fixture (third-party) | file-I/O | `fixtures/magentests/` | role |
| `tests/scripts/reproduce-cgb-speed.sh`, `test-reproduce-cgb-speed.sh` | script | batch | `reproduce-cgb-colour.sh`, `test-reproduce-cgb-colour.sh` | exact |
| `tests/scripts/reproduce-age.sh` | script | batch (network compare) | `reproduce-magentests.sh` | exact |
| `.github/workflows/fixture-repro.yml` | CI | batch | existing "Reproduce CGB colour fixture bytes" step + pin block | exact |
| `docs/model-gates.md` + core `MODEL:` tags | doc/gate | n/a | Phase 11 dispositions section + `verify-model-gates.py` | exact |
| `tests/check_no_phase12_rows.cmake` | test script | transform | `tests/check_no_phase11_rows.cmake` | exact |
| `tests/fuzz_core.c` speed mode + seeds in `tests/test_fuzz_core.c` | fuzz | streaming | `fuzz_palette` / `FUZZ_PALETTE_HALF_DOT_LIMIT` | exact |
| Partition-equivalence cases | test | batch | `halt_timer_partition` `tests/test_control.c:191`; `rtc_slice_invariance` | exact |
| `tests/player/cgb_smoke.cmake` + `tests/player/CMakeLists.txt` | test | request-response | existing `player_cgb_smoke` branch | exact |
| `tests/consumers/c/main.c`, `cpp/main.cpp` inline guest | consumer test | request-response | `cgb_api_smoke` `:67` | exact |
| `src/player/limitations.h`, `tests/player/test_limitations.c`, README, preview.yml, `src/player/main.c:401` | claims | n/a | self (E2 claims edit) | exact |
| `tests/expected-tests.txt`, `cmake/ExpectedTests.cmake`, `tests/player/expected-tests.txt` | inventory | n/a | Phase 11 blocks | exact |
| `tests/test_cgb_tables.c:288` + `docs/cgb-profile.md:302` | mirror | n/a | self (must change together) | exact |

## Pattern Assignments

### Stall branch in `gbb_run_internal` (`src/core/gabbaboy.c`)

**Analog:** HALT branch `:3970-3990` (insert between `stopped` `:3921-3945` and interrupt dispatch `:3946`). Do NOT copy the stopped branch: `GBB_STOP_NO_PROGRESS` is set only there (`:3941`).

HALT template (verbatim `:3976-3989`):
```c
if (budget_half_dots - result.consumed_half_dots < 8u) return result;       /* BUDGET, consumed unchanged */
if (!audio_preflight(instance, 8u)) { result.reason=GBB_STOP_OUTPUT_FULL; return result; }
if (UINT64_MAX - instance->time_half_dots < 8u) { result.reason=GBB_STOP_INVALID_STATE; return result; }
advance_devices(instance, 8u);
result.consumed_half_dots += 8u;
result.reason=GBB_STOP_HALTED_IDLE;
if ((instance->ie & instance->interrupt_flags & 0x1Fu) != 0) { instance->halted=0; result.reason=GBB_STOP_BUDGET; }
continue;
```
Replace `8u` with `step` (`min(stall, quantum)`, quantum `8u >> double_speed`); do not set `reason`; decrement `cpu_stall_half_dots` after `advance_devices`. Order of checks (budget, `audio_preflight`, `UINT64_MAX` headroom) must match.

**Interrupt-entry headroom variant** (`:3948-3950`, `:3961`) for the `irq_cost = 40u >> double_speed` local:
```c
if (40u > budget_half_dots - result.consumed_half_dots) return result;
if (!audio_preflight(instance, 40u)) { result.reason=GBB_STOP_OUTPUT_FULL; return result; }
if (UINT64_MAX - instance->time_half_dots < 40u) { result.reason=GBB_STOP_INVALID_STATE; return result; }
```
**Instruction headroom** (`:4015-4022`): `uint8_t cost=instruction_cost(instance,d);` then `if (cost > budget_half_dots-result.consumed_half_dots) return result;` / `audio_preflight(instance, cost)` / `UINT64_MAX - time_half_dots < cost`. Change only `instruction_cost` (`:3599`, `return d.ticks;` -> shifted); the preflights then follow automatically.

**Switch-at-retire placement:** after `:4035` `if (instance->ime_delay != 0 && --instance->ime_delay == 0) instance->ime = 1;` and before the GATE-65 block `:4036-4044` (copy of the divider-reset trio there goes into `divider_reset()`).

**Tag pattern:** every new top-level function needs `/* MODEL: BOTH GATE-00 basis="..." */` directly above (e.g. `:3883-3894`); branch tags like `/* MODEL: BOTH GATE-64 basis="..." -- ... */` at `:3998`.

### Test seam `gbb_test_speed_state` (`gabbaboy.c` + `gabbaboy_test.h`)

**Analog:** `gabbaboy.c:3897-3903`
```c
/* Private test seam, like gbb_test_cpu_snapshot: reports the effective banks, never public ABI. */
/* MODEL: BOTH GATE-00 basis="debug seam" */   (see :3891-3894 for the tag form)
void gbb_test_bank_state(const gbb_instance *m, uint8_t *out_vram_bank, uint8_t *out_wram_bank) {
    if (m == NULL) return;
    if (out_vram_bank != NULL) *out_vram_bank = m->vram_bank;
    if (out_wram_bank != NULL) *out_wram_bank = m->wram_bank;
}
```
Header form `src/core/gabbaboy_test.h:17-24` (doc comment, `uint16_t gbb_test_last_unsupported_address(const gbb_instance *m);`). Other seams are `extern`-declared inside tests (`tests/fuzz_core.c:55`: `extern void gbb_test_bank_state(const gbb_instance *, uint8_t *, uint8_t *);`); the new one goes in the header (RESEARCH I) so signature drift fails to compile. NULL-tolerant out-params.

### `tests/test_cgb_speed_internal.c` (white-box single TU)

**Analog:** `tests/test_cgb_colour_internal.c`
Header (lines 1-23):
```c
/* ... single translation unit that includes the core source, so it must not link GabbaBoy::core. ...
 * Usage: test_cgb_colour_internal <case> [fixtures-root] */
#ifdef GBB_COLOUR_CORE_SOURCE
#include GBB_COLOUR_CORE_SOURCE
#else
#include "../src/core/gabbaboy.c"
#endif
#include <stdio.h>
#include <stdlib.h>
#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)
```
Use `GBB_P12_CORE_SOURCE` for the macro name. `main` dispatches by `strcmp(argv[1], name)` over a case table (`:1189-1206`, `PLAIN_CASES[i].name`); the speed test adds `--mutants <mask>` parsing before dispatch. Seeded RNG to copy: `tests/test_banking_internal.c:26-31` (xorshift64 `rng_next`). CMake target form (`tests/CMakeLists.txt:1919-1922`):
```cmake
add_executable(test_cgb_colour_internal test_cgb_colour_internal.c)
target_include_directories(test_cgb_colour_internal PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_cgb_colour_internal PRIVATE c_std_17)
set_target_properties(test_cgb_colour_internal PROPERTIES C_EXTENSIONS OFF)
```
Also `tests/test_mbc3_rtc_internal.c` (`GBB_CORE_SOURCE_PATH`, `tests/CMakeLists.txt:66-119`) as the second include-the-core precedent.

### Configure-time mutant generator (exactly-once anchors) and runtime-mask variant

**Analog:** `gbb_colour_mutant` `tests/CMakeLists.txt:1942-1990` (read core once at `:1940`).
Anchor rule (`:1943-1948`):
```cmake
file(READ ${GBB_COLOUR_CORE_SOURCE_PATH} gbb_colour_core_text)
string(FIND "${gbb_colour_core_text}" "${anchor}" first)
string(FIND "${gbb_colour_core_text}" "${anchor}" final REVERSE)
if(first EQUAL -1 OR NOT first EQUAL final)
  message(FATAL_ERROR "colour mutant ${name}: anchor '${anchor}' must occur exactly once in ...")
endif()
string(REPLACE "${anchor}" "${replacement}" text "${gbb_colour_core_text}")
```
White-box consumer (`:1953-1960`): `add_executable(${target} ${test_source})` + `target_compile_definitions(... "GBB_COLOUR_CORE_SOURCE=\"${source}\"" GBB_BUILD_REVISION="colour-mutant-${name}" GBB_BUILD_QUALIFIED=0)`.
Public-API consumer (`:1962-1972`): `add_library(gabbaboy_core_colour_mutant_${name} STATIC ${source})` linked `${library} gabbaboy_accept` in that order.
Test pair (`:1978-1991`): failing test via `expect_exit.cmake` (`GBB_CMD=$<TARGET_FILE:t>;case`, `GBB_EXPECT_CODE=1`, `GBB_EXPECT_REGEX`), control `GBB_EXPECT_CODE=0` regex `.*`, and `set_tests_properties(${fail_test} PROPERTIES ENVIRONMENT "ASAN_OPTIONS=detect_leaks=0")`.
Example call (`:1993-1998`): `gbb_colour_mutant(shade_flip test_cgb_colour_internal.c <fail> <control> "<anchor>" "<replacement>" "cgb_dmg_identity_shade_pin;${PROJECT_SOURCE_DIR}/fixtures" "observed" cgb_colour_internal_harness_alive)`.

**Runtime-mask variant (new, RESEARCH Pattern 4):** same function shape, but loop over `(n, anchor, replacement)` triples with the same forward/REVERSE check per triple, apply all `string(REPLACE)` to ONE text, prepend `unsigned gbb_p12_mutants; #define GBB_P12_MUT(n) ((gbb_p12_mutants >> (n)) & 1u)`, and register per-n failing test `exe <case> --mutants <1<<n>` and control `exe <case> --mutants 0`. Anchor lines in the core carry `/* P12-M<n> */` tags (RESEARCH section B). No closer runtime-mask analog exists (see No Analog).

Fuzz-library variant (non-white-box): `cgb_fuzz_palette_mutant_no_mask` `:2406-2440` (anchor `GBB_FUZZ_MASK_ANCHOR`, `add_library(... STATIC)`, `add_executable(test_fuzz_core_mutant_no_mask test_fuzz_core.c fuzz_core.c)` with `GBB_FUZZ_STANDALONE_TEST=1`, `_control` using a plain case).

### Static-assert mutant `cgb_adr_half_dot_static_assert_mutant`

**Analog:** `tests/CMakeLists.txt:1671-1691` (copy verbatim, change anchor/target names):
```cmake
set(gbb_adr_anchor "#define GBB_HALF_DOTS_PER_T_DOUBLE 1u")
... (FIND forward/REVERSE, FATAL_ERROR if not exactly once)
string(REPLACE "${gbb_adr_anchor}" "#define GBB_HALF_DOTS_PER_T_DOUBLE 2u" gbb_adr_mutant_text "${gbb_adr_core_text}")
add_library(gabbaboy_core_adr_mutant STATIC EXCLUDE_FROM_ALL ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_adr_mutant.c)
add_test(NAME cgb_adr_half_dot_static_assert_mutant
  COMMAND ${CMAKE_COMMAND} --build ${PROJECT_BINARY_DIR} --target gabbaboy_core_adr_mutant)
set_tests_properties(cgb_adr_half_dot_static_assert_mutant PROPERTIES
  PASS_REGULAR_EXPRESSION "half-dot timeline:" TIMEOUT 180)
```
Core side: `_Static_assert(..., "half-dot timeline: ...")` at `gabbaboy.c:201-213`. A new stall-constant static assert (`GBB_SPEED_SWITCH_STALL_T`) must start with `half-dot timeline:` to reuse this regex pattern; keep the existing mutant unchanged (`:21` macro). Note: `GBB_HALF_DOTS_PER_T_DOUBLE` stays 1u; do not rename it.

### AGE / Mooneye-protocol runner (`tests/test_age.c`)

**Analogs:** `src/runner/main.c:109-114` `cgb_cases[]` (rows carry profile, `result_pc`, registers `{3,5,8,13,21,34}`, budget; suite admitted by manifest SHA-256 `:131-143`, `cmake/VerifyMooneyeCgb.cmake` pc-table) and `tests/test_mooneye_cgb_div_sweep.c` (`tests/CMakeLists.txt:429-441`) for a small standalone driver linked to `GabbaBoy::core` (`target_include_directories(... "${PROJECT_SOURCE_DIR}/include")`, `c_std_17`, `C_EXTENSIONS OFF`).
Difference to document in the file: Mooneye detects a fixed `result_pc` holding `0x40`; AGE uses the first executed `LD B,B` (verdict point, RESEARCH "AGE Fixtures"). Registers pass `B,C,D,E,H,L = 3,5,8,13,21,34`, fail sets `B=0`.
**Phase 11 AGE wiring** is data only: `tests/external/cgb-ppu-dispositions.json` (`m3-bg-*`, `"vendored": false`, `expected-unsupported`) and the CMake pair at `tests/CMakeLists.txt:2347-2373`; no AGE ROM or `age_` test exists. Leave that file unchanged (D-24).

### `tests/external/cgb-speed-dispositions.json` and verifier

**Analog:** `tests/external/cgb-ppu-dispositions.json:1-26` (schema `gabbaboy-external-dispositions-v1`; suite fields `suite, repository, commit, licence, vendored, rights_gate, enumeration, upstream_count, rows[]`; row fields `case, upstream_path, disposition, reason, decision, owner_phase`). Add `signature_sha256`, `flip_rule`; `vendored` becomes `true` for the 13 ROMs.
**Verifier analog:** `tests/scripts/verify-external-dispositions.py:1-40` (stdlib, `python3 -I`, `class Mismatch`, `need(cond, detail)`, schema/commit regex `[0-9a-f]{40}`, docs block between `<!-- cgb-external-dispositions-begin -->`/`-end -->`). Copy, do not generalise. Its `vendored is False` assertion is why the Phase 11 pair stays untouched.
**CMake pair:** `tests/CMakeLists.txt:2347-2373` (pass regex `external-dispositions pass age=6`, `TIMEOUT 30`; mutated copy via anchor `string(FIND ... REVERSE)` -> `file(WRITE "${PROJECT_BINARY_DIR}/external-dispositions/mutated.json")` -> `expect_exit` code 1 regex `disposition-mismatch`).

### `fixtures/cgb-speed/` (original, project-authored)

**Analog:** `fixtures/cgb-colour/` (`manifest.json`, `LICENSE.txt`, `common.inc`, `*.asm`, `*.gb`).
Manifest shape (`fixtures/cgb-colour/manifest.json`): `id`, `source[]`, `source_identity` ("Original GabbaBoy project-authored assembly"), `source_sha256{}`, `license`, `build{assembler, version "1.0.1", archive, archive_sha256, ci_archive, ci_archive_sha256, recipe, committed_bytes_toolchain}`, `fixtures[]{file, size_bytes, sha256, recipe{source, defines[], rgbfix_flags[]}}`. Pin values must equal those already in the other manifests (guarded below).
**Digest test:** `tests/CMakeLists.txt:2270-2273`
```cmake
add_test(NAME cgb_colour_fixture_digest
  COMMAND ${CMAKE_COMMAND} -DMANIFEST=${GBB_CGB_COLOUR_DIR}/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixtureManifest.cmake)
```

### `fixtures/age/` (third party, MIT, 13 ROMs)

**Analog:** `fixtures/magentests/{manifest.json,SOURCES.md,ELIGIBILITY.md,LICENSE.txt}`; script `tests/scripts/reproduce-magentests.sh` (`--self-check` offline default / `--compare` networked: lines 8-11, 36, `:148-150`):
```bash
  --self-check) self_check ;;
  --compare) self_check >/dev/null; compare ;;
  *) echo "usage: $0 [--self-check|--compare]" >&2; exit 2 ;;
```
Output tokens: `self-check=pass`, `result=byte-identical`, `result=differs <file> <rebuilt> <committed>`.
**Install-scan guard:** `tests/CMakeLists.txt:1221-1242`:
```cmake
set(GBB_MAGENTESTS_SCAN_ARGS "-DGBB_FORBIDDEN_MANIFEST=${GBB_MAGENTESTS_DIR}/manifest.json" -DGBB_FORBIDDEN_LABEL=magentests)
gbb_add_magentests_scan_test(magentests_not_installed 0 "magentests absent from scanned tree files=[1-9]" "${GBB_LIBBET_INSTALL_CHECK}")
set_tests_properties(magentests_not_installed PROPERTIES FIXTURES_REQUIRED libbet_install)
gbb_add_magentests_scan_test(magentests_not_installed_selftest 1 "magentests-installed: share/payload.bin" "${GBB_MAGENTESTS_SCAN_SELFTEST}")
```
Self-test copies one fixture to `share/payload.bin` (`:1219-1223`, `file(COPY_FILE ...)`). **Pitfall:** `GBB_FORBIDDEN_LABEL` is regex-matched against lower-cased install paths (`cmake/ScanForbiddenFixtures.cmake:68`); use `fixtures/age` or `age-test-roms`, never `age`. Note `magentests` pins RGBDS 0.6.1 separately; AGE uses RGBDS 1.0.1, so its repro can be a step in the `fixture-repro` job (1.0.1 already on PATH) or a sibling job like `magentests-repro` (`fixture-repro.yml`, own checkout, `timeout-minutes: 20`, `upload-artifact` of `result.txt`).

### `tests/scripts/reproduce-cgb-speed.sh` (+ `test-reproduce-cgb-speed.sh`)

**Analog:** `tests/scripts/reproduce-cgb-colour.sh:1-60`: `set -euo pipefail`, `repo_root`, `mktemp -d` + `trap cleanup EXIT`, tool presence + version-line check (`"$tool v1.0.1"`), then `python3 -I - "$repo_root" "$work_dir" <<'PY'` reading the manifest; `fail()` prints `result=differs reason=...` exit 1; `error()` prints `result=error reason=...` exit 2; allow-list regexes `NAME`, `DEFINE`, `FLAG`; arguments passed as lists, never a shell. It also reads `fixtures/cgb-banking/manifest.json` as the pin reference (point at the same).
**Tests:** `tests/CMakeLists.txt:2394-2402`:
```cmake
if(NOT WIN32)
  find_program(GBB_BASH_CGB_REPRO bash REQUIRED)
  foreach(gbb_repro_case tool_failure missing_pin)
    string(REPLACE "_" "-" gbb_repro_arg "${gbb_repro_case}")
    add_test(NAME cgb_colour_repro_${gbb_repro_case}
      COMMAND ${GBB_BASH_CGB_REPRO} ${PROJECT_SOURCE_DIR}/tests/scripts/test-reproduce-cgb-colour.sh ${gbb_repro_arg})
    set_tests_properties(cgb_colour_repro_${gbb_repro_case} PROPERTIES TIMEOUT 60)
  endforeach()
endif()
```
**Windows:** every new bash-only test name must be added to `cmake/ExpectedTests.cmake:16-21` `list(REMOVE_ITEM expected_tests ... cgb_colour_repro_tool_failure cgb_colour_repro_missing_pin)`.

### `.github/workflows/fixture-repro.yml`

Two edits, copying existing text:
1. In the inline Python pin block: add `cgb_speed = json.loads((root / 'fixtures/cgb-speed/manifest.json').read_text())`, `cgb_speed_build = cgb_speed['build']`, and the loop (copy the `cgb_colour_build` loop):
```python
for key in ('version', 'archive', 'archive_sha256', 'ci_archive', 'ci_archive_sha256'):
    if build.get(key) != cgb_colour_build.get(key):
        raise SystemExit(f'CGB colour RGBDS pin {key} differs from the established fixture pin')
```
2. New step cloned from "Reproduce CGB colour fixture bytes":
```yaml
      - name: Reproduce CGB colour fixture bytes
        shell: bash
        run: |
          GBB_RGBDS_ARCHIVE="$RUNNER_TEMP/rgbds-$RGBDS_RELEASE_VERSION/$RGBDS_ARCHIVE" \
            GBB_RGBDS_ARCHIVE_SHA256="$RGBDS_ARCHIVE_SHA256" \
            bash tests/scripts/reproduce-cgb-colour.sh
```
Omitting step 1 silently drops the pin-equality guarantee (Pitfall 14).

### Model-gate rows, tags, `verify-model-gates.py`, `GBB_MG_STOP_TAG_REGEX`

**Scanner:** `tests/scripts/verify-model-gates.py` (rules R1-R5 in RESEARCH). Test registrations `tests/CMakeLists.txt:1743-1795`.
**Must change in the same commit** (`:1760-1761`):
```cmake
set(GBB_MG_STOP_TAG_REGEX
  "[ ]*/\\* MODEL: UNKNOWN GATE-[0-9][0-9] research:12 -- STOP, including CGB speed switch \\*/\n")
```
Retagged core line is currently `gabbaboy.c` execute STOP `:3814-3823` (`UNKNOWN GATE-62 research:12`); the regex must match exactly one tag after the edit (e.g. `research:14 -- STOP (DMG and unarmed paths)`), else configure fails with "STOP gate tag must occur exactly once".
`model_gates` expects `functions=1[2-9][0-9]` (`:1743`); currently 163 functions, room for 36 more. R2 compares class/guard/resolution only (Site/Note are free). Existing tag forms to copy: `/* MODEL: BOTH GATE-00 basis="no SM83 opcode difference" */` (function tag), `/* MODEL: UNKNOWN GATE-65 research:12 -- DIV reset on STOP */` (branch tag, `:4036`), `CGB_ONLY` needs `GUARD` token within 12 code lines (R4), `BOTH` followed by hazard tokens (`stopped`, `dma_`, ...) needs `basis=` (R5). Doc rows between `<!-- model-gates-begin -->`/`-end -->` (`docs/model-gates.md:42-129`); new ids start GATE-84.
**No-phase-12 check:** copy `tests/check_no_phase11_rows.cmake` (whole file, 28 lines: `GBB_FILES` list, needle `research:11`, `SEND_ERROR "phase-11-row-open: ..."`, success `message(STATUS "no-phase11-rows pass")`) to `check_no_phase12_rows.cmake` with needle `research:12`, tokens `phase-12-row-open`, `no-phase12-rows pass`. CTest pair `tests/CMakeLists.txt:2446-2465` (mutated doc: anchor `"| GATE-50 | UNKNOWN | - | research:14 |"` exactly-once -> `research:11`; for Phase 12 pick a row that will exist at `research:14` e.g. GATE-54 and revert to `research:12`). Write mutated doc to `${GBB_MODEL_GATE_DIR}/phase12-row-mutated.md`.

### Fuzz mode in `tests/fuzz_core.c`

**Analog:** `fuzz_palette` + `FUZZ_PALETTE_HALF_DOT_LIMIT UINT64_C(400000)` (`tests/fuzz_core.c:270`, loop `:378-379`, `:403-404`):
```c
if (budget > FUZZ_PALETTE_HALF_DOT_LIMIT - spent) budget = FUZZ_PALETTE_HALF_DOT_LIMIT - spent;
...
while (spent < FUZZ_PALETTE_HALF_DOT_LIMIT) { uint64_t budget = FUZZ_PALETTE_HALF_DOT_LIMIT - spent; ...
```
ROM synthesis uses hand-assembled bytes (`rom[at++] = 0xE0u; rom[at++] = 0x40u; /* LDH (LCDC),A */`, `:363`). Dispatch (`:449-460`):
```c
if (cgb && (data[0] & 0x40u) != 0u) fuzz_cgb_io(machine, data, size);
else if (cgb && (data[0] & 0x20u) != 0u) fuzz_palette(machine, data, size);
else if ((data[0] & 3u) == 2u) ...
```
Add `else if (cgb && (data[0] & 0x70u) == 0x10u) fuzz_speed(...)` BEFORE the `& 3u` branches (note `0x10` selector shares no bits with `0x40`/`0x20` checks since those test single bits first; verify `0x70==0x10` does not collide: bits 6 and 5 clear). Contract counter `gbb_fuzz_core_contract_failures()` / `require_contract(...)`. Seeds and registered names: `tests/test_fuzz_core.c` (`run_cgb_seeds`, `run_profile_select`, `run_palette_seeds`) -> CTest `fuzz_core_regressions`, `cgb_fuzz_io_regressions`, `cgb_fuzz_profile_select`, `cgb_fuzz_palette_regressions`; add `cgb_fuzz_speed_regressions` plus `tests/fuzz/fuzz_core.dict` update. Mutant pair: `cgb_fuzz_palette_mutant_no_mask` (+`_control`) `:2406-2440`; read state through `gbb_test_speed_state` (like `require_banks` via `gbb_test_bank_state`, `fuzz_core.c:55-62`).

### Partition-equivalence tests

**Analog 1:** `tests/test_control.c:191-` `halt_timer_partition`: two instances (`whole`, `split`), `make_rom(rom, p, sizeof(p))`, run the same total in different slice sizes, then `gbb_test_cpu_snapshot` + `memcmp(&before, &after, sizeof(before))` and compare observer events (`gbb_test_observer_set`, `gbb_test_observer_count`). Budget semantics to preserve (`:46-47`): `gbb_run(m, 39, trace, 8)` returns `GBB_STOP_BUDGET, consumed_half_dots == 0` for interrupt entry (needs 40 normal / 20 double).
**Analog 2:** `tests/test_mbc3_rtc_internal.c:501-531` `rtc_slice_invariance`: caps array `{64u, 4096u, 100000u, 3u * SECOND}`, `drive(m, target, caps[i], i % 2u)`, plus a fixed small-slice run ("64 half-dots, the finest a whole instruction fits in" -> at double speed the finest becomes 32 half-dots for an M-cycle of 4; stall step is 8/4 half-dots). For white-box seeded stall sweeps use `rng_next` (`tests/test_banking_internal.c:26`).

### Player smoke `tests/player/cgb_smoke.cmake`

**Analog:** the existing `smoke` branch (`cgb_smoke.cmake:48-70`): `gbb_run_player(code text --model cgb --smoke-colour "${GBB_ROM}")`, parse `smoke_colour rgba_sha256=... distinct=... title_token=... spot=...`, independent expectations from fixture source constants. CMake registration (`tests/player/CMakeLists.txt:66-80`): per-name `elseif` branch with `add_test(NAME ... COMMAND ${CMAKE_COMMAND} -DGBB_CHECK=... -DGBB_PLAYER=$<TARGET_FILE:gabbaboy-player> ${cgb_smoke_args} -P "${GBB_PLAYER_CGB_SMOKE_SCRIPT}")` + `TIMEOUT 120 ENVIRONMENT "${cgb_env}"`. Each new `player_cgb_*` name needs its own branch; the chain ends `message(FATAL_ERROR "Unknown player_cgb_ test in inventory: ...")`, and inventory is `tests/player/expected-tests.txt` (`player_cgb_*` at lines 80-88). Player runs only with `GABBABOY_BUILD_PLAYER` (macOS).

### Installed consumer inline guest

**Analog:** `tests/consumers/c/main.c:67-` `cgb_api_smoke` (called at `:407`; C++ twin `tests/consumers/cpp/main.cpp:251`, called `:409`): builds a 32 KiB ROM in-memory (`rom[0x143u]=0xC0u;` header checksum loop `for (i=0x134u; i<=0x14Cu; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);`), uses only public API (`gbb_create`, `gbb_load_rom`, `gbb_run`, `gbb_get_info`), `goto done` failure style, `passed ? 0 : 1`. A speed guest (`LD A,1; LDH ($4D),A; STOP`, then read KEY1 via a guest write to WRAM and `gbb_peek_ram`) fits here; no new public symbol is added so `cgb_consumer_symbol_coverage` is unaffected. Keep C and C++ twins in step.

### Claims surfaces (`limitations.h`, `test_limitations.c`, README, preview.yml, `main.c:401`)

**Analog:** self. The same sentence appears in five places and must agree:
`src/player/limitations.h:5` (macro `GBB_PLAYER_LIMITATIONS_TEXT`), `tests/player/test_limitations.c:8` (`expected[]`, compared with `strcmp`), `README.md:11`, `.github/workflows/preview.yml:51` and `:98` (`capability_limits`, two occurrences; the Linux one differs), `src/player/main.c:401` (`Claims: ...`). Current wording to replace: "CGB mode-3 timing, double speed and HDMA are not claimed or implemented". **Keep the phrase `CGB mode-3 timing`** (and `no colour correction`, `DMG APU model`, `--model auto|dmg|cgb`, `no palette flag`): `player_claims_agree` phrase list (`tests/player/CMakeLists.txt:381-383`) requires them verbatim on every surface, and the Linux list requires `no colour correction` + `CGB mode-3 timing`. Edit only the double-speed fragment, identically everywhere. Mutated control (`gbb_player_mutate_source` on README, expects `claims-disagree no colour correction `) needs no change.

### Registration / inventory / timeouts

- `tests/expected-tests.txt`: one contiguous block per plan; every `add_test` name must appear (aborts configure otherwise, `cmake/ExpectedTests.cmake:6-28`).
- CMake edit blocks: `# --- Phase 12 plan 12-NN begin ---` / `# --- Phase 12 plan 12-NN end ---` (Phase 11 precedent `# --- Phase 11 plan 11-14 begin ---` ... `end ---`, e.g. `tests/CMakeLists.txt:2263-2265`, `:2403`).
- Sanitizer scaling (`tests/CMakeLists.txt` tail): loops all tests, `get_test_property(TIMEOUT)` and multiplies by 3 only when a TIMEOUT is set. Give every heavy test an explicit `TIMEOUT` (AGE ROMs: 120; `set_tests_properties(x PROPERTIES TIMEOUT 120)`).
- Windows: add bash-only names to the `if(WIN32) list(REMOVE_ITEM ...)` list in `cmake/ExpectedTests.cmake`.

### KEY1 table mirror

`gabbaboy.c:1328` read, `:1209` table comment, `tests/test_cgb_tables.c:288` (`case IO_KEY1: snprintf(rd, rd_n, "$7E or armed bit"); snprintf(wr, wr_n, "bit 0 arms the switch"); return 1;`) and `docs/cgb-profile.md:302` must change together or `cgb_tables_io` fails.

## Shared Patterns

### Exactly-once anchor guard (all configure-time mutants/doc mutants)
**Source:** `tests/CMakeLists.txt:1943-1948`, `:1676-1680`, `:1772-1776`. Always `string(FIND ...)` + `string(FIND ... REVERSE)`, `FATAL_ERROR` when `first EQUAL -1 OR NOT first EQUAL final`, then `string(REPLACE ...)` and `file(WRITE ...)` into the build tree.

### Failing-by-design test via `expect_exit.cmake`
**Source:** `tests/CMakeLists.txt:1978-1991`. `-DGBB_CMD=<exe>;<args>` `-DGBB_EXPECT_CODE=1` `-DGBB_EXPECT_REGEX=<regex>` `-P tests/expect_exit.cmake`; `ENVIRONMENT "ASAN_OPTIONS=detect_leaks=0"` only on the failing test; always pair with a control (exit 0).

### Configure-dependency on read files
`set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS <file>)` before every `file(READ)` of the core/doc (`:1938-1939`, `:1749-1751`) so edits re-trigger the anchors.

### Budget/headroom triple for any new device-advancing branch
**Source:** `gabbaboy.c:3976-3978` (see stall section): budget compare, `audio_preflight`, `UINT64_MAX` headroom, then `advance_devices`.

### Tagged-function rule
**Source:** `gabbaboy.c:3883-3894`. Every new top-level function (`stop_case`, `divider_reset`, `cpu_stalled`, `timer_reload_hd`, `end_stall`, seam) needs a `MODEL:` comment directly above or `gate-untagged-function: <name>` fails `model_gates`.

### Test failure style
`REQUIRE(x)` printing `file:line: expr` and `return 1`; `main` returns 2 for usage, 0 pass (`test_cgb_colour_internal.c:15-17`, `:1189-1206`).

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| Runtime-mask mutant helper (`GBB_P12_MUT`, `--mutants <mask>`, `gbb_p12_set_mutants`) | test config | batch | All Phase 11 mutants compile one core copy per anchor (26 invocations); the merged runtime-selected form is new (RESEARCH Pattern 4). Build it from `gbb_colour_mutant` by looping triples. |
| `tests/test_age.c` AGE verdict rule (first `LD B,B`, WRAM `TEST_RESULTS` row mask) | test | request-response | No AGE ROM or `age_` test exists; Mooneye runner uses a fixed `result_pc`. Use `cgb_cases[]` shape + `test_mooneye_cgb_div_sweep.c` driver structure. |
| `tests/scripts/derive-cgb-speed-expectations.py`, `verify-speed-domains.py` | verifier | transform | No oracle-derivation script for CPU-clock timing; nearest style analogs are `tests/scripts/gen-cgb-priority-truth.py` (`--check`, `--self-test`, regen test + mutated copy at `tests/CMakeLists.txt:1999-2029`) and `verify-external-dispositions.py`. |

## Metadata

**Analog search scope:** `src/core`, `src/runner`, `src/player`, `tests/` (CMake, scripts, consumers, player, external), `fixtures/`, `cmake/`, `.github/workflows/fixture-repro.yml`
**Files read/scanned:** ~30 targeted reads (greps first, then ranges); 21 key analog paths confirmed with `git ls-files` (all tracked; no `.gsd/capabilities` mirror paths used)
**Pattern extraction date:** 2026-10-13
