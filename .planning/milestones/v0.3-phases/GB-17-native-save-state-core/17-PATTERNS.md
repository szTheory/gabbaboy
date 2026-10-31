# Phase 17: Native Save State Core - Pattern Map

**Mapped:** 2026-10-26  
**Files analyzed:** 20 tracked analog paths plus 3 implied new test/checker roles  
**Analogs found:** 20 / 23 (related patterns found; no whole-state codec or inventory equivalent exists)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `include/gabbaboy/gabbaboy.h` (modify) | component / public API | request-response | same header, battery API | exact role |
| `src/core/gabbaboy.c` (modify) | service / core | transform, request-response | same core, battery/RTC codec | role-match |
| SHA-256 core seam (location not fixed; copy/rehost if needed) | utility | transform | `src/accept/sha256.c` | partial |
| `docs/cartridge-and-saves.md` (modify) | utility / API documentation | n/a | same document | exact |
| New public state API test (suggested `tests/test_state_api.c`) | test | request-response | `tests/test_battery.c` | role-match |
| New white-box inventory/fork test (suggested `tests/test_state_internal.c`) | test | transform | `tests/test_mbc3_rtc_internal.c`, `tests/test_audio.c` | role-match |
| State semantic fuzzing (extend `tests/fuzz_core.c` or add a dedicated target) | test | transform | `tests/fuzz_core.c` | exact harness |
| `tests/CMakeLists.txt` (modify) | config / test | batch | existing CTest, mutant, fuzz and installed-client blocks | exact |
| `tests/expected-tests.txt` (modify) | config | batch | existing frozen CTest inventory | exact |
| `tests/consumers/c/main.c`, `tests/consumers/cpp/main.cpp` (modify) | test / package consumer | request-response | same installed clients | exact |
| New field-inventory and writable-global checker(s) under `tests/scripts/` (names not fixed) | utility / test | transform | `tests/scripts/verify-perf-gate.py` self-test CLI style | role-match |
| `tests/scripts/measure-release-baseline.sh`, `tests/scripts/verify-v02-performance.py`, `tests/scripts/verify-perf-gate.py`, `tests/scripts/run-perf-gate.sh` (modify) | utility | batch | same producer/verifier/gate chain | exact |
| `tests/scripts/verify-support-ledger.py` (modify) | utility | batch | same generator/checker | exact |
| `.github/scripts/verify-release-gates.sh`, `.github/scripts/verify-release-source-proof.py`, `.github/scripts/verify-workflow-policy.py` (modify) | utility / policy | request-response, batch | same release gate and policy checkers | exact |
| `.github/workflows/release.yml`, `.github/workflows/nightly-asan.yml` (modify) | config / workflow | event-driven | same workflow jobs | exact |

The named `tests/test_state_*.c` paths and checker names are suggested organization, not decisions from CONTEXT/RESEARCH. The phase requires the roles; planning can group them or extend existing test sources. All analog paths above were checked with `git ls-files`; no runtime mirror path is used.

## Pattern Assignments

### Core API, state ownership, and digest

**Analogs:** `include/gabbaboy/gabbaboy.h` lines 11-42, 139-169, 193-230; `src/core/gabbaboy.c` lines 118-140, 350-362, 369-503, 3776-3813.

- Preserve the opaque `gbb_instance`; append state-specific `gbb_error` values after existing numeric values. Public APIs return `gbb_error`, validate nulls first, and document buffer ownership/threading in the header.
- The state inventory must classify all nested members in `cart_state`, `hdma_state`, and `gbb_instance`. The existing struct is a source of fields, not a serialization pattern: never memcpy or dump it.
- `gbb_load_rom` validates and allocates replacements before freeing/swapping the current ROM and RAM (core lines 3776-3813). Compute/cache full ROM identity on the successful replacement path, before the commit point; failed loads must preserve the old identity and machine.

**SHA source:** `src/accept/sha256.c` lines 83-88 exposes `gbb_accept_sha256_hex(bytes, length, out)`. It is tracked, but belongs to the acceptance layer and formats hex; do not link the core against it. Copy/rehost a small implementation or make a narrow private core seam, then cache the full digest once when ROM replacement succeeds.

### Portable codec and battery/RTC observer behavior

**Analog:** `src/core/gabbaboy.c` lines 3903-3942 and 3953-4025; tests in `tests/test_battery.c` lines 41-71, 74-119 and `tests/test_rtc_battery.c` lines 490-529.

**Wire encoding excerpt** (`src/core/gabbaboy.c:3903-3918`):

```c
/* written field by field so no struct layout leaks */
out[5] = (uint8_t)(c->rtc_sub & 0xFFu);
out[6] = (uint8_t)((c->rtc_sub >> 8) & 0xFFu);
out[7] = (uint8_t)((c->rtc_sub >> 16) & 0xFFu);
out[8] = (uint8_t)((c->rtc_sub >> 24) & 0xFFu);
```

Use explicit fixed-width little-endian reads/writes like the RTC block. Its exact 21-byte battery format is not the state format; the state API needs its own fixed header and manifest.

**Validate/project/apply excerpt** (`src/core/gabbaboy.c:3983-3989, 4006-4024`):

```c
cart_state parsed = instance->cart;
if (instance->cart.has_timer) {
    const gbb_error block = rtc_block_parse(bytes + ram_size, &parsed);
    if (block != GBB_OK) return block;
}
cart_state live = instance->cart;
rtc_sync(&live, instance->time_half_dots);
if (!rtc_fields_equal(&live, &parsed)) changed = 1;
if (changed && instance->battery_generation != UINT64_MAX)
    ++instance->battery_generation;
```

Reuse the local projection idea for battery-byte observer deltas, but state load must validate the *entire* incoming manifest before any instance mutation, then apply without a failure path. Keep `battery_generation` and `rumble_changes` local; compare projected RAM+RTC bytes before applying and bump/saturate once only for a changed battery image. Restore raw RTC fields/anchor without catch-up. `tests/test_battery.c` pins untouched outputs on undersized copy and generation idempotence; `tests/test_rtc_battery.c` pins no-catch-up and clock block corruption behavior.

### White-box inventory, continuation/fork, mutations, and fuzz

**White-box analog:** `tests/test_mbc3_rtc_internal.c` lines 1-14 includes core source for static helpers and instance access. `tests/CMakeLists.txt` lines 79-100 and 114-153 configure an isolated white-box executable and build source-copy mutants; each mutant must fail its intended case and pass an unrelated control.

**Continuation analog:** `tests/test_audio.c` lines 255-281 compares whole, split, and many-slice executions byte-for-byte for PCM. `tests/test_cgb_partition.c` lines 1099-1115 checks a failing operation leaves state unchanged by comparing subsequent run results/frames against a twin. These prove slice invariance and no-mutation patterns, but neither is a save-state fork; the fresh poisoned-target field census and field-drop mutants have no exact existing analog.

**Fuzz analog:** `tests/fuzz_core.c` lines 37-59 defines standalone contract failures versus libFuzzer aborts; `gbb_fuzz_core_one_input` at lines 1045-1088 dispatches bounded semantic scenarios. `tests/CMakeLists.txt` lines 812-875 registers deterministic regression cases and enables `fuzz_core` with Clang libFuzzer/ASan/UBSan when available. Extend this semantic harness so inputs reach state-load parsing and invariants; malformed bytes must not stop at header rejection. Keep deterministic seeded fixtures in CTest and the hosted campaign on the existing lane.

**Inventory checker:** no existing checker inventories every `gbb_instance` member or enforces zero writable globals. Follow repository checker practice (`tests/scripts/* --self-test`, positive plus seeded rejection) and register both main check and negative control in CTest. Treat `GBB_TEST_*` instrumentation members/defines explicitly so they do not leak into production state bytes.

### Installed C/C++ API and package lanes

**Analogs:** `tests/consumers/c/main.c` lines 7-64 and `tests/consumers/cpp/main.cpp` lines 7-65 exercise the installed battery API with synthetic ROMs, exact error values, untouched output buffers, and cleanup. Add actual calls to size/save/load in both languages, not a source grep alone.

`CMakeLists.txt` lines 118-156 installs/exports `GabbaBoy::core` and the public include tree. `tests/CMakeLists.txt` lines 1822-1850 invokes `cmake/RunInstalledConsumer.cmake` against a relocated prefix for both `c` and `cpp`; extend these real package lanes and the frozen test inventory. `docs/cartridge-and-saves.md` lines 157-177 is the API contract style: ownership, preconditions, errors, failure atomicity, and per-instance threading belong alongside the battery contract.

### Inherited performance and release gates

**Performance analogs:**

- `tests/scripts/measure-release-baseline.sh:700-782` binds bounded workload identity, raw samples, digest, build/compiler/host, warmups, uncertainty, and the advisory interpretation into a receipt. Preserve its producer/verifier split.
- `tests/scripts/verify-v02-performance.py:1206-1259` has explicit verify, historical, reuse, reviewed-decision, and `--self-test` CLI paths with typed rejection diagnostics. `tests/scripts/verify-perf-gate.py:1-15, 32-55` is the deterministic Ir/realtime gate; `tests/scripts/run-perf-gate.sh:13-20` keeps build/run collection separate from judgment.
- `tests/CMakeLists.txt:1445-1458` registers performance checker controls. Keep the paired wall-clock review trigger advisory, while Ir 1.10 and realtime 4.02 remain blocking, with receipt binding, repeats and immutable-base ratchet controls.

**Release analogs:**

- `tests/scripts/verify-support-ledger.py:2610-2704` shows a multi-mode generator/verifier CLI, `--write-current`, and explicit `--self-test` routes. Keep historical tagged bytes fixed and derive disclosure text from validated managed inputs.
- `.github/scripts/verify-release-gates.sh:181-210, 214-258` validates required-check head/status/app identity and exact downloaded asset inventory/digests. `.github/scripts/verify-release-source-proof.py:90-110` demonstrates realistic check-run JSON (`url`, `html_url`, `check_suite`) and mutation controls.
- `.github/workflows/release.yml:1172-1185, 1498-1529` calls the receipt verifier, trusted gate and exact downloaded-byte checks in production. The lifecycle rehearsal must run these production paths against bounded API-shaped stubs; do not add a separate success-only verifier.
- `.github/scripts/verify-workflow-policy.py:275-315, 2341-2380` is the fail-closed workflow reader and mutation registry pattern for WR/IN obligations. `.github/workflows/nightly-asan.yml:45-66` separates `report-red` privilege from repository-code replay; extend this policy for required timeout, title/label dedupe and nightly-gate evidence.

## Shared Patterns

### Error and transaction contract

**Sources:** `src/core/gabbaboy.c:3776-3813, 3921-3942, 3983-4025`; `docs/cartridge-and-saves.md:157-177`. Validate arguments and exact lengths before reads; stage parsed data locally; leave caller outputs and the full instance unchanged on refusal; commit only after all checks; use typed errors and saturating observer counters.

### Test controls

**Sources:** `tests/test_battery.c:74-119`; `tests/CMakeLists.txt:89-153, 834-853, 812-875`. Every new structural or semantic checker needs a positive case and a defect that it demonstrably rejects. Mutants need an intended failing seed and an unrelated passing control; don't report unexercised mutations as evidence.

### Host/core boundary

**Sources:** `include/gabbaboy/gabbaboy.h:130-138, 193-230`; `docs/cartridge-and-saves.md:157-177`; `src/core/gabbaboy.c:3968-3972`. Keep file I/O, host clocks and devices out of the core. The caller owns stable, non-overlapping buffers; public calls serialize access to one instance; separate instances remain independent.

## No Analog Found

| File/role | Reason |
|---|---|
| State field manifest / completeness checker | No current format inventories every nested mutable field or enforces disposition for every member. Use the actual `gbb_instance` and nested structs as the inventory source. |
| Canonical state save/load codec | Battery RTC encoding and parsing are the closest partial patterns; no existing whole-machine snapshot codec or two-pass allocation-free loader exists. |
| State fork census with field-drop mutants | Existing audio slice tests and CMake source-copy mutants cover pieces, but not save/load forks across poisoned fresh targets and machine-field categories. |
| State-load semantic fuzz target | Existing `fuzz_core` has a semantic harness and hosted libFuzzer wiring, but no state parser to reuse; extend it after the public state API exists. |

## Metadata

**Analog search scope:** public header, core instance and battery/RTC code, SHA helper, existing native/white-box/fuzz/consumer tests, CTest/package wiring, performance and release scripts/workflows.  
**Files scanned:** 20 tracked analog paths (plus phase context/research).  
**Pattern extraction date:** 2026-10-26
