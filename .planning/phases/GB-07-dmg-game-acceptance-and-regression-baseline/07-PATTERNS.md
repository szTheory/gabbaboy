# Phase 7: DMG Game Acceptance and Regression Baseline - Pattern Map

**Mapped:** 2026-10-10
**Files analyzed:** 40 new/modified (grouped below)
**Analogs found:** 36 / 40 (4 partial or none; see "No Analog Found")

All analog paths were confirmed git-tracked (`git ls-files`). No gitignored mirror paths are used. Line numbers are from the current branch head.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `fixtures/libbet/libbet.gb` | fixture (ROM) | file-I/O | `fixtures/mooneye/daa.gb`, `fixtures/mbc1-continuation/continuation.gb` | role |
| `fixtures/libbet/manifest.json` | config (rights/provenance) | file-I/O | `fixtures/mooneye/manifest.json` (+ `fixtures/tracer/manifest.json`) | role (new `rights.embedded_assets[]`) |
| `fixtures/libbet/LICENSE.txt`, `SOURCES.md` | docs | file-I/O | `fixtures/mooneye/LICENSE.txt`, `fixtures/mooneye/SOURCES.md` | exact |
| `tests/scripts/verify-libbet-admission.py` (or extend `verify-support-ledger.py`) | utility (fail-closed verifier) | transform | `tests/scripts/verify-support-ledger.py` | exact |
| `tests/scripts/reproduce-libbet.sh` | utility (script) | batch | `tests/scripts/reproduce-mooneye.sh` | role |
| `.github/workflows/libbet-repro.yml` | config (CI) | batch | `.github/workflows/fixture-repro.yml` | role |
| `.gitattributes`, `THIRD_PARTY_NOTICES.md` | config/docs | n/a | existing rows/lines in the same files | exact |
| `src/accept/sha256.[ch]` | utility | transform | `src/runner/main.c:62-92` (move, do not copy) | exact |
| `src/accept/input_script.[ch]` | utility (parser) | transform | `src/runner/main.c` `read_bounded` + `locate_rom` bounded style; `tests/test_loader_fuzz.c` for tests | partial |
| `src/accept/digest.[ch]` (RGB/PCM) | utility | transform | `src/runner/main.c` `hash_matches` / `sha_*` | role |
| `src/accept/predicate.[ch]` | utility | request-response | `src/runner/main.c` `fixture_case cases[]` compiled table + `protocol_status` | role |
| `src/accept/stepper.[ch]` (`advance_to`) | utility | event-driven | `src/player/main.c:580-621` `advance_to` | exact (adapt) |
| `src/runner/cases.c`, `acceptance.c`, `main.c` edits | controller/CLI | request-response | `src/runner/main.c:209-288` | exact |
| `tests/acceptance/CMakeLists.txt` | config | n/a | `tests/CMakeLists.txt:223-310` | role |
| `tests/acceptance/cases.txt`, `inputs/*.input`, `negative/*` | fixture (text) | file-I/O | `fixtures/mbc1-continuation/manifest.json` (eol=lf handling) | partial |
| `tests/test_acceptance_lib.c` (07-02: script parser, stepper, predicate), `tests/test_acceptance_cases.c` (07-06: case-file parser), `tests/test_acceptance_digest.c` (07-07: frame/rolling digests) | test | transform | `tests/test_runner.c`, `tests/test_loader_fuzz.c` | role |
| `tests/expect_exit.cmake` | test helper | request-response | `tests/expect_runner_failure.cmake` | exact (generalise) |
| core-mutant library (CMake generated) | test/config | transform | none (use RESEARCH Example 1) | none |
| `tests/baseline/dmg-cpu-b-v1.txt`, `CHANGES.md` | data/ledger | batch | none (new format) | none |
| `cmake/VerifyDmgBaseline.cmake`, `tests/scripts/verify-dmg-baseline.sh` | utility/test | batch | `cmake/VerifyFixture.cmake`, `cmake/VerifyMooneye.cmake`, `.github/scripts/verify-test-inventory.sh` | role |
| `tests/CMakeLists.txt`, `tests/expected-tests.txt` | config | n/a | same files (`add_test`, `gabbaboy_verify_registered_tests`) | exact |
| `tests/test_runner.c` (edit) | test | request-response | itself | exact |
| `src/player/main.c` (edit: `--input-script`, smoke_report) | controller/CLI | event-driven | `src/player/main.c:1466-1495` `smoke_send_z`, `2091-2125` CLI dispatch | exact |
| `tests/player/test_session.c`, `tests/player/expected-tests.txt`, `tests/player/CMakeLists.txt` | test | request-response | existing foreach dispatch in `tests/player/CMakeLists.txt` | exact |
| `tests/scripts/verify-phase3-player.sh` (edit) | utility | batch | its own lines 240-262 | exact |
| `.github/workflows/ci.yml`, `.github/scripts/check-player-result.sh` (edit, only if needed) | config | batch | themselves | exact |
| `docs/support/*` new ledger / limitation note | docs | n/a | `docs/support/v0.1.0.md` (versioning rule in `verify-support-ledger.py:12-18`) | exact |

## Pattern Assignments

### `src/accept/*` shared library (sha256, digest)

**Analog:** `src/runner/main.c`, SHA-256 at lines 62-92. Move it, do not duplicate (research Don't Hand-Roll). Keep `sha256_ctx`, `sha_init/update/final` and `hash_matches` semantics identical so Mooneye digests stay unchanged (D-20).

```c
/* main.c:63, 83-85, 92 */
typedef struct { uint32_t h[8]; uint64_t bits; uint8_t block[64]; size_t used; } sha256_ctx;
static void sha_init(sha256_ctx *c) { ... }
static void sha_update(sha256_ctx *c,const uint8_t *p,size_t n) { ... }
static void sha_final(sha256_ctx *c,char out[65]) { ... }   /* lowercase hex, 64 chars */
static int hash_matches(const uint8_t *bytes,size_t length,const char *expected) { sha256_ctx c;char hash[65];sha_init(&c);sha_update(&c,bytes,length);sha_final(&c,hash);return strcmp(hash,expected)==0; }
```

Pitfall 1: `tests/test_runner.c:6-9` textually includes `../src/runner/main.c` (`#define main gbb_runner_program_main` / `#include` / `#undef main`) and uses `MAX_ROM`, `cases`, `hash_matches`, `read_bounded`, `run_guest` (lines 24-30). If these move or change signature, edit `test_runner.c` in the same task. Static names `rotr`, `cases` can collide when the shared code is a separate TU; make shared symbols non-static with a `gbb_accept_` prefix. Keep the Mooneye path self-contained in `main.c`.

Canonical RGB digest (D-24) and PCM digest (D-16): feed `sha_update` with an explicit serialized buffer, never struct or array memory (D-33).
```c
static const char RGB_HEADER[] = "GBB-RGB888-v1 160x144\n";   /* use sizeof-1/strlen, 22 bytes */
/* shade map {255,170,85,0} replicated to R,G,B, row-major */
/* PCM: per gbb_audio_frame emit 4 bytes: L lo, L hi, R lo, R hi (via uint16_t) */
```

### `src/accept/stepper.[ch]` (deadline stepper, D-15) (utility, event-driven)

**Analog:** `src/player/main.c:580-621` `advance_to`.

```c
gbb_run_result result;
gbb_audio_frame frames[512];
size_t count = 0u;
result = gbb_run_audio(app->machine, budget, frames, capacity, &count);
...
if (result.reason != GBB_STOP_BUDGET && result.reason != GBB_STOP_OUTPUT_FULL) {   /* line 612 */
    fprintf(stderr, "Guest stopped ...");  return false;                             /* DIFFERENCE */
}
if (result.consumed_half_dots == 0) return !finish_target || result.reason == GBB_STOP_OUTPUT_FULL;
```

Adapt, do not copy verbatim: the shared stepper must also accept `GBB_STOP_HALTED_IDLE` (Libbet is halted-idle in 3801 of 3811 calls), tolerate zero-consume when the remainder is at most 48 half-dots (carry into next deadline), keep a hard iteration guard, and never read a host clock. The player keeps its own cursor in `app->input.guest_cursor_half_dots` (reconciled at 609-611 via `player_input_reconcile`), so the player wrapper must still call that reconcile. PCM frames feed the shared PCM digest before `player_audio_submit`.

### `src/runner/cases.c`, `acceptance.c`, `main.c` edits (CLI, request-response)

**Analog:** `src/runner/main.c`.

**Bounded read (reuse for D-28; generalise capacity and move to heap per D-27)** (lines 87-91):
```c
static int read_bounded(const char *path, uint8_t *buffer, size_t capacity, size_t *length) {
    FILE *f=fopen(path,"rb"); if(!f)return 0;
    size_t n=fread(buffer,1,capacity+1,f); int failed=ferror(f); fclose(f);
    if(failed||n>capacity)return 0; *length=n; return 1;
}
```
**Heap ROM with 8 MiB cap pattern** (already in the tracer path, lines 233-240): `malloc(size)`, check `length>8*1024*1024`, `fclose`, `free` on every error exit. Copy that discipline for the case-ROM loader; check exact `rom_size` and SHA-256 before `gbb_load_rom` (compare `load_case_rom`, lines 111-124: `fopen rb` -> `fread MAX+1` -> `ferror`/`fclose` -> size -> `hash_matches`; returns short reason strings `bad-size`, `bad-digest`, `missing-fixture`).

**CLI loop and exit codes** (lines 266-288): hand-rolled `for` over `argv`; unknown arg -> `invalid-arguments: use --help for usage` exit 2; bare `main` guard `argc==2&&strncmp(argv[1],"--",2)!=0` -> `run_original_tracer` must stay first. Add `--acceptance/--observe/--model/--revision/--failure-dir/--mutate` branches without altering `--manifest/--case/--suite/--receipt`. `print_usage` (257-264) text is asserted by `tests/verify_runner_help.cmake`; append usage lines only.

**Suite counts and receipt** (line 134, 280-285):
```c
static int suite_counts_valid(size_t eligible,size_t executed) { return eligible!=0&&eligible==executed; }
if(receipt)printf("suite eligible=%zu executed=%zu status=%s\n", ...);
```
Extend to `eligible= executed= excluded= xfail=` (D-22); exit code 4 is new; never use `SKIP_RETURN_CODE`.

**Run-loop pattern** (`run_guest`, 180-208): create `GBB_PROFILE_DMG_CPU_B`, `gbb_load_rom`, loop with chunked `gbb_run_ex`, `gbb_destroy(m)` on every path. The acceptance loop replaces `gbb_run_ex` with the shared stepper plus `gbb_queue_events` windows of at most 64.

**Compiled predicate table keyed by ROM digest** (analog is the `fixture_case cases[]` shape, lines 28-60): a static const array of `{rom_sha256, name, addresses, anchor bytes}`; check ROM digest first, then anchors (D-09). Reads go through `gbb_peek_ram` (WRAM only; all Libbet addresses `$C4E8-$C5A3` qualify).

**Error message style:** short kebab reasons to stderr (`invalid-manifest`, `unknown-case: ...`); new ones per CONTEXT: `invalid-script: line N: <reason>`, `invalid-cases: <reason> line=<n>`.

### `src/accept/input_script.[ch]` (parser, transform)

**Analog:** no existing tokenizer. Closest style: `locate_rom` (main.c:104-110) for bounded path handling, and `tests/test_loader_fuzz.c` for boundary matrix design (CMake lines 148-149 register `loader_boundary_fuzz`). Contract targets from `include/gabbaboy/gabbaboy.h`:
```c
/* gabbaboy.h:51-73 */
gbb_button: RIGHT=0, LEFT=1, UP=2, DOWN=3, A=4, B=5, SELECT=6, START=7
GBB_INPUT_BUTTON_PRESS = 3, GBB_INPUT_BUTTON_RELEASE = 4
struct gbb_input_event { uint64_t at_half_dots; gbb_input_event_kind kind; uint8_t value; };
/* gbb_queue_events: 64-event queue, nondecreasing absolute half-dots, not earlier than instance time, rejected batch appends nothing */
```
Units: `hd`, `f`=140448, `s`=8388608; checked arithmetic with 600 s ceiling; all-or-nothing parse before any execution; limits 64 KiB / 4096 lines / 128 B per line / 16384 events (D-11, D-12).

### `fixtures/libbet/manifest.json` (config, file-I/O)

**Analog:** `fixtures/mooneye/manifest.json` (top-level `suite{name,revision,tree_sha1,license,upstream}`, `replacement_asset`, `builder{...}`, `inventory_status`, `excluded_candidates[]`, `fixtures[]`), with `fixtures/tracer/manifest.json` fields `id, source, license, build{...}, rom, sha256, profile{...}, protocol{...}`.
```json
"suite": { "name": "...", "revision": "<40-hex>", "tree_sha1": "...", "license": "...", "upstream": "https://github.com/.../tree/<commit>" },
"builder": { "name": "...", "version": "...", "source_revision": "...", "git_archive_sha256": "...", "source_license": "...build tool only..." },
"excluded_candidates": [ { "source_path": "...", "reason": "..." } ]
```
Add: `rom{path,size_bytes:32768,sha256,header{title,type,143,146}}`, `rights.embedded_assets[]` (path, kind, author, licence, evidence pointer at pinned commit, SHA-256) covering the frozen build closure, `reproducibility`, `scope_note`, and the predicate address derivation text (D-09). The pin must be the commit `46a765a2...`, not the tag.

### `tests/scripts/verify-libbet-admission.py` (utility, transform)

**Analog:** `tests/scripts/verify-support-ledger.py`. Copy: shebang plus `from __future__ import annotations`, stdlib only, `fail(message)` raising `ValueError`, `ROOT = pathlib.Path(__file__).resolve().parents[2]`, strict duplicate-key JSON parse (`unique_pairs`, line 89), in-script `self_test()` that mutates raw bytes and requires each mutation to be rejected (lines 223-252), `main()` with argparse, errors printed as `"<tool> verification failed: {error}"` to stderr and exit 1 (lines 316-345).
```python
for changed in mutations:
    try:
        altered = parse_ledger(changed, current)
        validate_manifest_set(altered, manifests)
    except (ValueError, KeyError):
        continue
    fail("self-test mutation was accepted")
```
Per D-05 each of the five mutations (empty assets, record removed, licence `unknown`, changed ROM digest, changed header byte) needs a distinct stderr message so the exit-code wrapper can assert it. Run via `${Python3_EXECUTABLE} -I` located by `find_package(Python3 COMPONENTS Interpreter REQUIRED)` as `tests/player/CMakeLists.txt` already does (no core test calls python today; Windows risk, Pitfall 4).

### `tests/expect_exit.cmake` (test helper)

**Analog:** `tests/expect_runner_failure.cmake` (whole file, 28 lines). Copy the `execute_process(... RESULT_VARIABLE result OUTPUT_VARIABLE output ERROR_VARIABLE error)` plus combined `MATCHES` pattern; replace the weak check
```cmake
if(result STREQUAL "0" OR result MATCHES "^-1$")
```
with an exact numeric `GBB_EXPECT_CODE` comparison (see RESEARCH Code Example 2). This supports exit 1/2/3/4 distinction that `WILL_FAIL` cannot.

### `tests/acceptance/CMakeLists.txt` and `tests/CMakeLists.txt` registrations

**Analog:** `tests/CMakeLists.txt`.

Negative-case fabrication at configure time (lines 275-290):
```cmake
file(WRITE "${PROJECT_BINARY_DIR}/runner-bad-manifest.json" "{}")
file(READ "${PROJECT_SOURCE_DIR}/fixtures/mooneye/manifest.json" GBB_TAMPERED_MANIFEST)
string(REPLACE "\"model\": \"DMG-CPU-B\"" "\"model\": \"CGB-E\"" GBB_TAMPERED_MANIFEST "${GBB_TAMPERED_MANIFEST}")
file(WRITE "${PROJECT_BINARY_DIR}/runner-wrong-metadata.json" "${GBB_TAMPERED_MANIFEST}")
add_test(NAME runner_bad_manifest
  COMMAND ${CMAKE_COMMAND} -DGBB_RUNNER=$<TARGET_FILE:gabbaboy-runner> -DGBB_MANIFEST=... -DGBB_MODE=manifest
          -P ${PROJECT_SOURCE_DIR}/tests/expect_runner_failure.cmake)
```
Use the same shape for the core-mutant (string(REPLACE) on `src/core/gabbaboy.c`, JOYP line at `gabbaboy.c:532-538`; fail configure if the pattern is absent or non-unique) and for mutated Libbet manifests.

CMake-script check registration (lines 223-230), the model for `dmg_baseline` and notice checks:
```cmake
add_test(NAME mooneye_fixture_digest
  COMMAND ${CMAKE_COMMAND} -DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye -P ${PROJECT_SOURCE_DIR}/cmake/VerifyMooneye.cmake)
```
Per-case registration with a foreach (lines 291-294) for `acceptance_<id>` and `_excluded_<model>` tests.

Timeouts: runner tests use a single `set_tests_properties(... PROPERTIES TIMEOUT 30)` list (lines 297-307). Libbet cases need their own `TIMEOUT 300` (ASan run costs ~85 s). Registration is verified by `cmake/ExpectedTests.cmake`:
```cmake
function(gabbaboy_verify_registered_tests)
  get_property(registered_tests DIRECTORY PROPERTY TESTS) ... list(SORT ...)
  if(NOT registered_tests STREQUAL expected_tests) message(FATAL_ERROR ...)
```
So every new name goes into `tests/expected-tests.txt` in the same commit (configure fails otherwise), and the call at the end of `tests/CMakeLists.txt` must still be last. `.github/scripts/verify-test-inventory.sh` rejects any `<skipped`, `<failure`, `<error` (lines 15-23).

### `cmake/VerifyDmgBaseline.cmake` / `tests/scripts/verify-dmg-baseline.sh` (utility, batch)

**Analog:** `cmake/VerifyFixture.cmake` (digest compare, `file(SHA256)`, `message(FATAL_ERROR ...)` on mismatch, `-DROM= -DMANIFEST=` arguments) and `.github/scripts/verify-test-inventory.sh` (sorted-name inventory compare, `awk '{ sub(/\r$/, ""); print }'` CR stripping at the line shown, `LC_ALL=C sort`).
```cmake
file(SHA256 "${ROM}" actual_sha256)
...
if(NOT actual_sha256 STREQUAL expected_sha256)
  message(FATAL_ERROR "Fixture digest mismatch: expected ${expected_sha256}, got ${actual_sha256}")
endif()
```
Recommended (RESEARCH Pitfall 4): do the comparison in a `cmake -P` script so Windows CTest never depends on `bash`; make `verify-dmg-baseline.sh` a thin wrapper. Strip `\r`, store names sorted with `LC_ALL=C`, one output line per category, non-zero on any difference. Benchmark reuse: `tests/measure_core.c` and `tests/scripts/measure-release-baseline.sh` (digest only is identity-checked).

### `.github/workflows/libbet-repro.yml` and `tests/scripts/reproduce-libbet.sh`

**Analog:** `.github/workflows/fixture-repro.yml` and `tests/scripts/reproduce-mooneye.sh`.
```yaml
name: fixture-repro
on: { pull_request:, push:, workflow_dispatch: }      # libbet-repro: workflow_dispatch ONLY (opt-in, non-required)
permissions:
  contents: read
...
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```
Reuse the exact SHA-pinned actions, `runs-on: ubuntu-22.04`, `timeout-minutes`, archive download plus SHA-256 verification before extract. Script header convention (reproduce-mooneye.sh:1-17): `#!/usr/bin/env bash`, `set -euo pipefail`, mode-argument usage check exiting 2, `repo_root=$(git rev-parse --show-toplevel)` and an assertion that the fixture dir equals `$repo_root/fixtures/<name>`, `sha256_file() { shasum -a 256 "$1" | cut -d ' ' -f 1; }`. Do NOT fold into `fixture-repro.yml` (it enforces the single RGBDS 1.0.1 pin, visible in its inline python). The workflow compares and never writes back.

### `src/player/main.c` edits (`--input-script`, `smoke_report`)

**Analog:** same file.

CLI dispatch (lines 2091-2125). Current shape is `argc == 3` for `--smoke-package`; add the 5-arg shape (`--smoke-package <invalid-rom> --input-script <file>`) in both the boolean and the guard, and in the usage string:
```c
const bool package_smoke = argc == 3 && strcmp(argv[1], "--smoke-package") == 0;
if ((smoke && argc != 2 && argc != 4) || (audio_measure && argc != 4) || (package_smoke && argc != 3) || ...
    fprintf(stderr, "usage: %s [--help | --smoke ... | --smoke-package invalid-rom | ...]\n", argv[0]); return 2;
const char *invalid_rom = smoke && argc == 4 ? argv[3] : (package_smoke ? argv[2] : GABBABOY_PLAYER_INVALID_ROM);
```
Bounded-timestamp SDL key injection (`smoke_send_z`, 1466-1495): the scripted smoke must go through the same key path, but with EXACT script times, not the `+ 8u` skew used there:
```c
uint64_t elapsed_ns = 0u;
if (!player_input_half_dots_to_nanoseconds(elapsed_half_dots + 8u, &elapsed_ns) ||    /* replace "+ 8u" with the script's at_half_dots */
    app->input.host_anchor_ns > UINT64_MAX - elapsed_ns) { fputs("...bounded SDL key timestamp\n", stderr); return false; }
const Uint32 event_type = down ? SDL_EVENT_KEY_DOWN : SDL_EVENT_KEY_UP;
if (!push_key(app, event_type, SDL_SCANCODE_Z, app->input.host_anchor_ns + elapsed_ns) || !pump_events(app)) { ... }
```
Key map (`src/player/input.c` `map_scancode`): arrows, A->Z, B->X, START->Return, SELECT->Right Shift. Feed events in windows under `PLAYER_INPUT_NORMAL_CAPACITY 56` (capacity 64). Output the single stable line `smoke_report rom_sha256=<...> half_dots=<n> predicate=pass pcm_nonsilent=1 pcm_sha256=<...>`; exit 0 only on pass. Verify in the package script like lines 250-258.

### `tests/scripts/verify-phase3-player.sh` (edit)

**Analog:** its own lines 250-262: run packaged binary, capture to `$smoke_output`, `grep -Fq '<stable line>' ... || { cat "$smoke_output" >&2; fail '...'; }`, then `cat`. Dummy drivers exported near lines 328-329 (`SDL_AUDIO_DRIVER=dummy`, `SDL_VIDEO_DRIVER=dummy`). Add a `smoke_report ... predicate=pass` grep step and a no-input control that must fail. Option (b) in RESEARCH Open Question 3 (ROM and script from the repo checkout, not shipped in the package) avoids a redistribution/package-verifier change.

### `tests/player/CMakeLists.txt`, `tests/player/test_session.c`, `tests/player/expected-tests.txt`

**Analog:** the `foreach(test_name IN LISTS GABBABOY_PLAYER_EXPECTED_TESTS)` regex dispatch at the top of `tests/player/CMakeLists.txt` (branches like `^player_audio_(ring|...)$`, `^player_input_(...)$`, `^player_session_[a-z0-9_]+$`). A new name matching no branch must get a branch or the loop will not register it; read the rest of the file before adding names. Session-level negative controls belong in `test_session.c`.

### `.gitattributes`, `THIRD_PARTY_NOTICES.md`

**Analog:** existing lines.
```
fixtures/mooneye/manifest.json -text
fixtures/mbc1-continuation/continuation.asm text eol=lf
fixtures/mbc1-continuation/manifest.json text eol=lf
fixtures/mbc1-continuation/LICENSE.txt text eol=lf
fixtures/mbc1-continuation/continuation.gb -text
```
Add the same explicit per-file lines for `fixtures/libbet/libbet.gb -text`, the Libbet text files, `tests/acceptance/cases.txt`, `tests/acceptance/inputs/*.input`, `tests/acceptance/negative/*`, `tests/baseline/*`. Do not rely on a glob (existing file lists explicit paths).

`THIRD_PARTY_NOTICES.md`: table columns `Material | Rights and distribution | Source / manifest SHA-256 | ROM SHA-256 | Notice SHA-256`; add a Libbet row (zlib, Yerrick/Korth credits, CC0 hardware.inc note). The intro sentence "The three ROMs used in release and consumer smoke tests are original project-authored material; they are not commercial game images or third-party ROMs." becomes inaccurate (Libbet is third party and is used by acceptance, not release smoke); amend it in the same change.

### `fixtures/libbet/SOURCES.md`, `LICENSE.txt`

**Analog:** `fixtures/mooneye/SOURCES.md` (sections: "Immutable inputs and builder" with commit/tree/archive SHA-256 bullets, "Asset rights", "Source closure and eligibility", reproduction section; gate-status comment blocks) and `fixtures/mooneye/LICENSE.txt` (verbatim upstream notice).

## Shared Patterns

### Exact-inventory discipline
**Source:** `cmake/ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh`
**Apply to:** every plan that adds a CTest name (GAME-01 verifier tests, acceptance tests, baseline tests). Update `tests/expected-tests.txt` (184 names) in the same commit; player names go in `tests/player/expected-tests.txt` (51).

### Exit-code and reason assertions
**Source:** `tests/expect_runner_failure.cmake` (generalise to `tests/expect_exit.cmake`)
**Apply to:** all negative/excluded/control tests. Always assert exact code and a distinct reason regex; never `WILL_FAIL`, never `SKIP_RETURN_CODE`.

### Bounded, binary-mode file I/O
**Source:** `src/runner/main.c:87-91` `read_bounded`, `111-124` `load_case_rom`, `233-240`
**Apply to:** case-file, script, ROM, PPM reads and writes (`rb`/`wb` only, capacity+1 overflow detection, check `ferror` and `fclose`, free on every exit).

### Stdlib-only Python verifier with self-test
**Source:** `tests/scripts/verify-support-ledger.py`
**Apply to:** G5 admission verifier and any ledger tooling. `python3 -I`, no third-party imports.

### Fixture admission layout
**Source:** `fixtures/mooneye/{manifest.json,SOURCES.md,LICENSE.txt}`, `.gitattributes`, `THIRD_PARTY_NOTICES.md`, `cmake/VerifyFixture.cmake`
**Apply to:** Libbet admission and its `*_fixture_digest` CTest.

### CI gating
**Source:** `.github/workflows/ci.yml` (`player-gate` line 140 sets `player_required` only for `pull_request`; `required-native` aggregates, lines 172-202), `.github/scripts/check-player-result.sh` (self-test table accepts `false:skipped`)
**Apply to:** the player smoke (run inside the existing `macos-player-package` job; any new job must be added to `needs:`, the env block and the loop), and the baseline check (runs via CTest in all three native jobs, so no ci.yml change is expected).

### Determinism and serialization
**Source:** `src/runner/main.c` SHA helpers; AGENTS.md ("explicit portable serialization rather than raw C structure dumps")
**Apply to:** all digests (frame header plus RGB bytes, LE int16 PCM), receipts, ledger lines (sorted `key<TAB>value`, `eol=lf`, strip `\r` when comparing).

## No Analog Found

| File | Role | Data Flow | Reason / planner guidance |
|---|---|---|---|
| core-mutant library (generated `gabbaboy_joyp_mutant.c`) | test | transform | No mutant-build precedent. Use RESEARCH Code Example 1 against `src/core/gabbaboy.c:532-538` (`if ((m->joypad_select & 0x20u) == 0)`); partial analog is the configure-time `string(REPLACE)` tampering at `tests/CMakeLists.txt:277-281`. |
| `tests/baseline/dmg-cpu-b-v1.txt`, `CHANGES.md` | data | batch | New ledger format (D-30). Nearest conceptual precedents: `fixtures/mooneye/pre-admission-baseline.json`, `docs/support/v0.1.0.md`; but intentionally text, not JSON. Mind Pitfall 7 (`frozen_revision` is an ancestor commit containing all `src/` changes). |
| `src/accept/input_script.c` tokenizer | utility | transform | No line-oriented parser exists in C; follow the bounds and error-string conventions above and the `loader_boundary_fuzz` matrix style. |
| `tests/acceptance/cases.txt` key=value parser | utility | transform | Same; no existing text-config parser. Path validation (no `..`, leading `/` or `\`, `:`, empty segments) is new; `locate_rom` (main.c:104-110) only joins a directory and filename. |

## Metadata

**Analog search scope:** `src/runner`, `src/player`, `src/core/gabbaboy.c` (JOYP), `include/gabbaboy`, `tests/` (CMake, scripts, cmake helpers, player), `cmake/`, `fixtures/*`, `.github/{workflows,scripts}`, `.gitattributes`, `THIRD_PARTY_NOTICES.md`
**Files scanned:** about 30 read or grepped; 17 key analogs confirmed tracked via `git ls-files`
**Pattern extraction date:** 2026-10-10
**Open items for planner (from RESEARCH):** Mooneye `LD B,B` frame is not ready for `tim00`/`tim00_div_trigger` (record `not-ready`, Open Question 1); control cases as xfail case lines vs direct exit assertions (Open Question 2); how the Libbet ROM reaches the macOS package smoke (Open Question 3, prefer checkout path); `bash`/`python3` in Windows CTest needs a Wave 0 CI spike.
