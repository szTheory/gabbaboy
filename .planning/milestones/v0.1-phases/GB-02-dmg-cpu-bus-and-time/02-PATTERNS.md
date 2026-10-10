# Phase 2: DMG CPU, Bus, and Time - Pattern Map

**Mapped:** 2026-10-06  
**Files analyzed:** 16 existing or implied files/surfaces  
**Analogs found:** 16 / 16 (new optional implementation modules inherit the core pattern)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/core/gabbaboy.c` (or proposed internal core modules) | service/core | transform, request-response | `src/core/gabbaboy.c` | exact foundation |
| `include/gabbaboy/gabbaboy.h` | model/API | request-response | same | exact |
| `src/runner/main.c` | controller/runner | file-I/O, request-response | same | exact |
| `tests/test_api.c` | test | request-response | same | exact |
| `tests/test_tracer.c` | test | request-response | same | exact |
| New focused CPU/bus/timer/serial tests (likely `tests/test_cpu.c`, `tests/test_bus.c`, `tests/test_timer.c`) | test | transform, request-response | `tests/test_api.c`, `tests/test_tracer.c` | role-match |
| `tests/test_loader.c` | test | file-I/O, request-response | same | exact; preserve loader regression coverage |
| `tests/CMakeLists.txt` | config/test registration | request-response | same | exact |
| `tests/expected-tests.txt` | config/inventory | request-response | same | exact |
| `fixtures/tracer/tracer.asm` | fixture/source | transform | same | exact |
| `fixtures/tracer/manifest.json` | config/provenance | file-I/O | same | exact |
| New admitted Mooneye ROMs, notices, and manifests under `fixtures/mooneye/` | fixture/config | file-I/O | `fixtures/tracer/` | role-match |
| `cmake/VerifyFixture.cmake` or fixture verifier extension | utility/config | file-I/O | same | exact |
| `README.md` and public API comments | docs | request-response | same | role-match |
| `tests/consumers/c/main.c`, `tests/consumers/cpp/main.cpp` | test/consumer | file-I/O, request-response | same | exact |
| `.github/workflows/ci.yml`, `.github/scripts/verify-test-inventory.sh` | config/CI | batch | same | exact |

The source tree currently has a single tracked core translation unit. Splitting it into CPU, bus, timer, serial, or timeline files is an implementation option from research, not a required abstraction; new modules should preserve the instance-owned, portable C17 style below. PPU, rendering, DMA arbitration, SDL input mapping, full JOYP behavior, and CGB remain outside this headless phase.

## Pattern Assignments

### `src/core/gabbaboy.c` and any new internal core modules (core/service, transform)

**Analog:** `src/core/gabbaboy.c` (164 lines; tracked)

The current file is the implementation base, though its eight-opcode decoder and `$A000` fixture RAM must not be treated as the desired hardware model. Keep mutation instance-local and separate bus access, decode/cost, execution, and public result handling. New internal files may take the relevant function groups without changing ownership rules.

**Imports and ownership** (lines 1-15):
```c
#include "gabbaboy/gabbaboy.h"

#include <stdlib.h>
#include <string.h>

struct gbb_instance {
    uint8_t *rom;
    size_t rom_size;
    uint8_t ram[8192];
    uint8_t a, f, b, c, d, e, h, l;
    uint8_t div, stat;
    uint16_t pc, sp;
    uint64_t time_half_dots;
    int loaded;
};
```

**Reset and bounded load pattern** (lines 19-26, 77-89): reset fields explicitly, clear owned RAM/time, validate before allocation, copy caller ROM, and only then replace the active image. Preserve the failed-replacement atomicity exercised by `tests/test_loader.c` lines 60-70.

**Current decode/preflight seam** (lines 92-113, 144-159): `decode()` yields instruction size/cost/support; `instruction_cost()` resolves conditional timing; `gbb_run()` checks full cost against remaining budget before trace write and execution. This is the closest implementation seam for instruction-boundary stepping. Expand it to legal/lockup behavior and timed bus/device transitions while retaining preflight: no partial instruction or consumed-time overshoot; if the next whole instruction does not fit, return explicit no-progress with machine/time unchanged. Internal timed phases still process device deadlines and queued timestamped inputs at their actual half-dot times. Do not turn the public API into a mid-instruction yield.

```c
uint8_t cost=instruction_cost(instance,d);
if (cost > budget_half_dots-result.consumed_half_dots) return result;
if (trace != NULL && result.trace_count == trace_capacity) { result.reason=GBB_STOP_TRACE_FULL; return result; }
if (trace != NULL) save_trace(instance,d,&trace[result.trace_count++]);
execute(instance,cost);
result.consumed_half_dots += cost;
```

**Bus pattern to replace/extend** (lines 28-36): `read8`/`write8` are the centralized address boundary. Keep all CPU-visible mapping there (or in a direct extracted bus module), including ROM-only cartridge space, WRAM/echo, HRAM, IE/IF and device registers. The current `$A000-$BFFF` array behavior is explicitly Phase 1 fixture policy and must be removed as hardware mapping; tracer scratch moves to WRAM. Apply timer edges and serial shifts at timed bus phases, not only at instruction completion.

### `include/gabbaboy/gabbaboy.h` (public model/API)

**Analog:** `include/gabbaboy/gabbaboy.h` (81 lines; tracked)

Keep the C/C++ boundary (`#ifdef __cplusplus`, lines 7-9), opaque instance (line 11), fixed-width data, caller-owned output and documented ownership (lines 53-56). Extend the bounded API only as required for distinct lockup/no-progress/STOP/timeout/unsupported/output-exhaustion outcomes and fixed-capacity ordered timestamped inputs. Document queue ordering/full behavior and output semantics explicitly; no hidden host clock, callbacks, or dynamic formatting.

**Locked public stepping text** (lines 66-73):
```c
/* Runs only whole supported instructions. Budget/consumed values are uint64
 * half-dot ticks. An instruction is preflighted and won't start unless its
 * full cost fits. Trace records are optional caller-owned storage; the core
 * writes no more than capacity, allocates nothing, and never overwrites prior
 * records. trace=NULL is valid only with capacity=0. Trace bytes are snapshots
 * at instruction boundaries and remain owned by the caller. */
```
Phase 2 decisions D-06/D-07 retain this no-overshoot instruction-boundary contract while allowing internal timed phases and event processing. Update the comment to describe new input/diagnostic parameters without weakening that guarantee.

### `src/runner/main.c` (host runner/controller)

**Analog:** `src/runner/main.c` (40 lines; tracked)

Read a bounded fixture file, create/load through the public API, own trace memory, interpret guest protocol outside the core, print a bounded result, and return distinct process status. For curated diagnostics extend this host-side pattern with pass/fail/timeout/unsupported, manifest identity/digest/profile/boot/protocol/ticks and bounded recent core evidence. Preserve ordinary guest semantics (`LD B,B` is not a CPU trap). Keep file I/O, formatting, and protocol interpretation out of the portable core.

```c
gbb_run_result result=gbb_run(machine,RUN_BUDGET_HALF_DOTS,trace,TRACE_CAPACITY);
uint8_t status=gbb_peek_ram(machine,0xA001);
const char *outcome=result.reason==GBB_STOP_UNSUPPORTED_OPCODE ? "unsupported" :
    result.reason==GBB_STOP_TRACE_FULL ? "trace-exhausted" :
    status==0xEE ? "guest-failure" :
    result.reason==GBB_STOP_BUDGET && status==0xA5 ? "pass" : "timeout";
```

The protocol above is specific to the original tracer. Mooneye cases need manifest-selected protocol handling and must never be counted eligible until source closure, license, DMG-CPU-B/boot applicability, ROM digest, and budget are established.

### API, CPU, bus, timer, and serial tests

**Analogs:** `tests/test_api.c` (70 lines), `tests/test_tracer.c` (47), `tests/test_loader.c` (72); all tracked.

Tests are standalone C executables with a small `REQUIRE` macro, command-line case selection, independent expected values, and explicit setup/cleanup. `test_api.c` lines 48-67 establishes strong boundary patterns: zero/short/exact budgets, no overshoot, invalid null/capacity pair, and canary bytes proving writes stop at capacity. `test_tracer.c` lines 34-44 shows named success/failure/unsupported/timeout/trace cases. Build new CPU and bus cases around register/flag/PC/SP/memory expectations; timer tests should assert exact divider phase, TIMA/TMA and IF at each collision boundary; input partition tests should compare machine state/output at equal actual consumed ticks with the identical ordered event sequence. Label owned expected values separately from hardware oracle tests.

Keep fixture file-loading and malformed-ROM cases in `test_loader.c`'s style (mutation plus repaired header checksum where needed); do not obscure independent behavioral assertions inside a generic test framework.

### Fixtures, digest, and rebuild

**Analogs:** `fixtures/tracer/tracer.asm` (24 lines), `fixtures/tracer/manifest.json` (50), `cmake/VerifyFixture.cmake` (18), all tracked.

The tracer manifest records source identity/license, explicit assembler version/recipe, output filename and SHA-256, profile/boot/applicability, protocol, reachable instruction inventory, and scope limits. Its build recipe writes temporary outputs and its digest verifier checks committed bytes offline. Carry this complete provenance pattern to every admitted upstream fixture: immutable upstream commit and source path, license and transitive include/asset closure, exact builder version/recipe, binary digest, model/boot applicability, oracle class, protocol and bounded emulated-time limit. Curated source research alone is not evidence that a generated fixture has been admitted. Normal CTest must consume checked-in bytes without network access or requiring the assembler.

```cmake
file(SHA256 "${ROM}" actual_sha256)
file(READ "${MANIFEST}" manifest_json)
string(JSON expected_sha256 ERROR_VARIABLE json_error GET "${manifest_json}" sha256)
if(NOT actual_sha256 STREQUAL expected_sha256)
  message(FATAL_ERROR "Fixture digest mismatch: expected ${expected_sha256}, got ${actual_sha256}")
endif()
```

For the project-authored tracer, preserve the existing regression that its scratch protocol is guest-visible, but update `tracer.asm`, the manifest address/protocol and runner/tests together when moving from `$A000` to WRAM. Keep the explicit note that the old external-RAM behavior was fixture policy, not hardware evidence.

### CTest inventory, consumers, docs, and CI

**Analogs:** `tests/CMakeLists.txt` lines 4-71; `tests/expected-tests.txt` lines 1-26; `cmake/ExpectedTests.cmake` lines 7-20; `tests/consumers/c/main.c` and `tests/consumers/cpp/main.cpp` lines 16-29; `README.md` lines 48-87; `.github/workflows/ci.yml` lines 10-131; `.github/scripts/verify-test-inventory.sh` lines 12-39. All are tracked.

CTest registers named cases explicitly (foreach is used for parallel parameterized cases), requires fixture-digest verification, and asserts the registered names equal the checked-in expected inventory. The expected inventory includes installed runner/C/C++ tests, but `ExpectedTests.cmake` removes only those three when no relocated install prefix exists. Update both registration and inventory when adding required cases; retain fail-closed exact JUnit comparison in CI so a missing or skipped test cannot look green.

Installed consumers include only the installed public header, use `find_package(GabbaBoy CONFIG REQUIRED)`/`GabbaBoy::core` in their CMake analogs, load fixture bytes as an external caller, and exercise the public lifecycle/run/output contract. Update both C and C++ consumers for any public API change. README's embedding contract, profile/evidence limits, fixture instructions, and phase scope are product docs and should be revised with implementation; keep hardware claims tied to the actual corpus and model. Native CI runs required inventory on Linux, macOS, and Windows; sanitizer CI runs the core subset and inventory verifier. Keep ordinary qualification offline, sanitizer coverage, exact inventory and installed-consumer checks connected as appropriate.

## Shared Patterns

### Ownership, bounds, and outcomes
**Sources:** `include/gabbaboy/gabbaboy.h:53-73`, `src/core/gabbaboy.c:77-89,144-159`. State belongs to an opaque instance; caller buffers have explicit capacity; allocation is limited to create/load; failed ROM replacement is atomic. All new event, trace and diagnostic storage remains bounded and caller-owned. Keep unsupported, lockup, timeout, no-progress and output exhaustion distinct.

### Time and partition behavior
**Sources:** `include/gabbaboy/gabbaboy.h:66-73`, `tests/test_api.c:48-56`. Preflight the whole instruction against remaining half-dot budget and return only at instruction boundaries. Process internal bus/device/input deadlines at their real timestamps; identical ordered events and equal actual elapsed ticks must produce equivalent supported state/output regardless of caller budget partition. Do not consume unused requested time or consult wall-clock time.

### Evidence and diagnostics
**Sources:** `src/runner/main.c:26-39`, `fixtures/tracer/manifest.json:2-25`, `cmake/VerifyFixture.cmake:8-17`, `tests/expected-tests.txt:1-26`. Keep guest test protocol and human-readable receipts in the runner, fixture identity/provenance in manifests, digest checks offline, and the eligible denominator explicit. Separate project-owned expected-value tests from hardware-verified Mooneye results; exclude PPU-, boot-ROM-, model-, manual-, or emulator-only cases from this phase's denominator.

## No Analog Found

No role/data-flow category lacks a local analog. The repository has no existing general CPU, mapped bus, timer, serial, or timestamped-input implementation; these are new behavior and should extend/extract the tracked core foundation rather than copy a nonexistent subsystem. No Mooneye fixture is admitted yet; its research candidates are not source-code analogs and each requires the phase's fixture audit before inclusion.

## Metadata

**Analog search scope:** `src/core`, `src/runner`, `include/gabbaboy`, `tests`, `tests/consumers`, `fixtures/tracer`, `cmake`, root documentation, `.github/workflows`, `.github/scripts`.  
**Tracked-source gate:** Every existing source analog named above was verified with `git ls-files`; no ignored `.gsd` runtime mirror is referenced.  
**Pattern extraction date:** 2026-10-06
