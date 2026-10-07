# Phase GB-03: Visible Interactive DMG - Pattern Map

**Mapped:** 2026-10-07  
**Files analyzed:** 17 proposed implementation surfaces (grouped by subsystem below)  
**Analogs found:** 15 / 17; no in-repository PPU implementation or SDL player exists

## File Classification

| New/Modified File Area | Role | Data Flow | Closest Analog | Match Quality |
|------------------------|------|-----------|----------------|---------------|
| `include/gabbaboy/gabbaboy.h` | API/model | request-response | same public header, lines 92-147 | exact |
| `src/core/gabbaboy.c` | service/core | event-driven + transform | same core, lines 11-40, 127-175, 279-360, 749-911 | role-match; no PPU analog |
| `tests/test_ppu.c` (composition and timing cases) | test | transform + event-driven | `tests/test_bus.c`, `tests/test_events.c` | role-match |
| `tests/test_dma.c` | test | event-driven + request-response | `tests/test_bus.c` | role-match |
| `tests/test_joypad.c` | test | event-driven + request-response | `tests/test_events.c` | exact for queue discipline; partial for JOYP behavior |
| `tests/CMakeLists.txt`, `tests/expected-tests.txt` | config/test inventory | batch | same files, lines 1-100; `cmake/ExpectedTests.cmake` | exact |
| `fixtures/visible-demo/*` (source, ROM, rights, manifest, recipe) | fixture/config | file-I/O + transform | `fixtures/tracer/*` | exact for provenance/reproduction, role-match for gameplay |
| `src/player/main.c` | controller/adapter | event-driven + file-I/O + request-response | `src/runner/main.c` and public API consumer | partial; no SDL UI analog |
| `CMakeLists.txt` | config | request-response | same file, lines 21-33, 90-92 | exact |
| `.github/workflows/ci.yml`, `.github/workflows/preview.yml` | config/delivery | batch + file-I/O | `.github/workflows/preview.yml` | role-match |
| `.github/workflows/fixture-repro.yml` | config/delivery | batch + file-I/O | same workflow, lines 17-40 | exact |
| `cmake/VerifyFixture.cmake` and player/package smoke helpers | utility/test | file-I/O + transform | `cmake/VerifyFixture.cmake`, `cmake/PreviewPackageSmoke.cmake` | role-match |
| installed C/C++ consumer smoke files | test | request-response | `tests/consumers/c/main.c`, `tests/consumers/cpp/main.cpp` | role-match |

The research additionally maps `test_dma.c`, `test_joypad.c`, and `test_ppu.c`; keep named image composition, raster timing, DMA contention, JOYP, and gameplay outcomes separate in the inventory. SDL adapter behavior and fixture-specific outcomes need new tests because no equivalent host player or interactive guest currently exists.

## Pattern Assignments

### `include/gabbaboy/gabbaboy.h` (public API, request-response)

**Analog:** `include/gabbaboy/gabbaboy.h`

**Ownership and bounded-output pattern (lines 92-104, 127-147):**

```c
/* The opaque instance owns its mutable state and a private copy of a loaded ROM.
 * Create/load may allocate; run/reset/peek do not. Each instance may be called
 * by one thread at a time. Separate instances have no shared mutable state. */
gbb_error gbb_create(gbb_profile profile, gbb_instance **out_instance);
void gbb_destroy(gbb_instance *instance);
/* A failed replacement leaves the current ROM and machine state unchanged. */
gbb_error gbb_load_rom(gbb_instance *instance, const uint8_t *rom, size_t rom_size);
```

The completed-frame API should follow the caller-owned, capacity-bounded output contract already used by `gbb_run_ex` and `gbb_peek_ram`; document dimensions, pitch, shade encoding, reset effects, invalid arguments, and no partial writes alongside its declaration. Keep SDL types and host time out of this header.

**Timestamped event contract (lines 46-55, 105-116):**

```c
typedef struct {
    uint64_t at_half_dots;
    gbb_input_event_kind kind;
    uint8_t value;
} gbb_input_event;
/* ... absolute half-dot ticks; equal timestamps keep caller order;
 * admission is atomic; malformed/past/unordered events are rejected. */
gbb_error gbb_queue_events(gbb_instance *instance, const gbb_input_event *events, size_t count);
```

Add button transition kinds and explicit button values to this same fixed queue; preserve the validated batch semantics.

### `src/core/gabbaboy.c` (core service, event-driven + transform)

**Analog:** `src/core/gabbaboy.c` (same file; no existing PPU or DMA subsystem)

**Instance-owned state and reset (lines 11-40, 127-150):**

```c
struct gbb_instance {
    /* CPU, bus and device state live on this instance. */
    uint64_t time_half_dots;
    gbb_input_event input_events[GBB_INPUT_EVENT_CAPACITY];
    size_t input_event_count;
    uint8_t wram[8192], hram[127];
    /* ... */
};

static void reset_machine(gbb_instance *m) {
    /* reset device and CPU fields in place; clear pending input */
    m->input_event_count = 0;
}
```

Add PPU, joypad, and DMA state to the instance and initialize/clear it in the existing reset path. Keep fixed-size frame storage instance-owned and preserve the established no-hidden-global rule.

**Timed bus and device progression (lines 154-175, 207-255, 279-360):**

```c
static uint8_t bus_read(gbb_instance *m, uint16_t address, uint64_t offset) {
    uint64_t timestamp = m->instruction_start_half_dots + offset;
    advance_devices_to(m, timestamp);
    uint8_t value = read8(m, address);
    observe_bus(m, 1, address, 1, value);
    return value;
}

static void advance_devices_to(gbb_instance *m, uint64_t target) {
    while (m->time_half_dots < target) {
        ++m->time_half_dots;
        apply_input_events_now(m);
        /* existing timer/serial clocks advance at the timestamp */
    }
}
```

Route PPU, JOYP, and DMA register reads/writes through the same timestamped bus access path. Make access denial depend on the active model and device state at that bus timestamp; do not put host clock, SDL, or file work in the core.

**Atomic queue validation (lines 338-360):**

```c
if (count > GBB_INPUT_EVENT_CAPACITY - instance->input_event_count)
    return GBB_EVENT_QUEUE_FULL;
/* validate every event and timestamp before copying any */
memcpy(instance->input_events + instance->input_event_count, events,
       count * sizeof(*events));
instance->input_event_count += count;
```

Extend validation for button IDs and press/release values before the existing single commit. Apply queued transitions at their exact emulated timestamp through the same progression path.

### `tests/test_joypad.c` (test, event-driven + request-response)

**Analog:** `tests/test_events.c`

**Event ordering and deterministic run partition (lines 144-170):**

```c
REQUIRE(gbb_queue_events(whole, whole_edges, 8) == GBB_OK);
REQUIRE(gbb_queue_events(parts, part_edges, 8) == GBB_OK);
gbb_run_result r = gbb_run(whole, 168, whole_trace, 8);
/* run the same timeline in smaller budgets */
REQUIRE(memcmp(whole_trace, part_trace, 6 * sizeof(whole_trace[0])) == 0);
REQUIRE(gbb_peek_ram(whole, 0xC000) == gbb_peek_ram(parts, 0xC000));
```

Also copy `event_queue_atomic` (lines 118-142) for queue-full, invalid batch, reset, and overflow checks. Add focused matrix-selection/read and interrupt tests only after the primary DMG-CPU-B edge source and expected cases are fixed; event queue analogs establish ordering but do not establish JOYP electrical semantics.

### `tests/test_ppu.c`, `tests/test_dma.c` (tests, transform + timed bus)

**Analogs:** `tests/test_bus.c` and `tests/test_events.c`

`test_bus.c` lines 45-70 provides an atomic rejection assertion that checks CPU snapshot, diagnostics, observer events, RAM, and HRAM remain unchanged. Its timed bus observer declaration and fixture loader are at lines 11-43. Reuse those techniques for caller buffer canaries, precise access timestamps, and preflight/non-mutation assertions. `test_events.c` lines 109-170 provides named, independently selectable cases and whole-run/partition comparisons.

There is no frame-data, mode-transition, raster, VRAM/OAM lock, or OAM DMA analog in tracked source. Build separate fixed expected shade-index image checks, dot/mode/STAT/fetch timing cases, and DMA/access contention cases. The authored image is an output oracle; it cannot stand in for timing or access arbitration.

### `tests/CMakeLists.txt`, `tests/expected-tests.txt` (inventory, batch)

**Analog:** `tests/CMakeLists.txt` and `tests/expected-tests.txt`

**Target and named-case registration (lines 56-63):**

```cmake
add_executable(test_events test_events.c)
target_link_libraries(test_events PRIVATE GabbaBoy::core)
target_compile_features(test_events PRIVATE c_std_17)
set_target_properties(test_events PROPERTIES C_EXTENSIONS OFF)
foreach(case event_stop_wake event_boundary event_queue_order event_queue_atomic event_partition)
  add_test(NAME ${case} COMMAND test_events ${case})
endforeach()
```

Register each new deterministic test by a named case and update the fail-closed `tests/expected-tests.txt` inventory and `cmake/ExpectedTests.cmake` together. Keep player-only cases gated behind the opt-in player configuration; ordinary core tests must remain SDL-free.

### `fixtures/visible-demo/*` (fixture, file-I/O + transform)

**Analog:** `fixtures/tracer/tracer.asm`, `manifest.json`, `LICENSE.txt`

**Provenance and exact build identity (`manifest.json`, lines 2-21):**

```json
{
  "id": "original-wram-tracer",
  "source": "tracer.asm",
  "source_identity": "Original GabbaBoy project-authored assembly",
  "license": "MIT; see LICENSE.txt and repository LICENSE",
  "build": { "assembler": "RGBDS", "version": "1.0.1" },
  "rom": "tracer.gb",
  "sha256": "...",
  "profile": { "name": "DMG-CPU-B", "boot": "skipped; starts at cartridge entry 0x0100" }
}
```

Reuse the same source/bytes/license/manifest adjacency and pinned RGBDS reproduction approach. Extend the manifest with the interactive protocol and explicit playable-profile limits. `tracer.asm` is only a small source-layout example; it has no graphics or gameplay pattern to copy.

### `src/player/main.c` and optional CMake target (adapter, event-driven + file-I/O)

**Analog:** `src/runner/main.c`, `include/gabbaboy/gabbaboy.h`, and `CMakeLists.txt` lines 21-33

The runner is a small CLI consumer of the opaque API, but no tracked file implements a window, keyboard, async dialog, or SDL renderer. Preserve the boundary visible in the existing target setup:

```cmake
add_library(gabbaboy_core STATIC src/core/gabbaboy.c)
add_library(GabbaBoy::core ALIAS gabbaboy_core)
target_compile_features(gabbaboy_core PUBLIC c_std_17)
add_executable(gabbaboy-runner src/runner/main.c)
target_link_libraries(gabbaboy-runner PRIVATE GabbaBoy::core)
```

Put SDL3 discovery and linkage only in an OFF-by-default player option. In the adapter, translate keyboard transitions and host timestamps to queued half-dot events, own any path received from async dialog callbacks, validate ROM replacement via `gbb_load_rom`, and render only a copied completed frame. Preserve the active session when replacement loading fails. These SDL-specific details come from `03-RESEARCH.md`; there is no local source analog.

### Workflow and package smoke files (config, batch + file-I/O)

**Analogs:** `.github/workflows/fixture-repro.yml`, `.github/workflows/preview.yml`, `cmake/PreviewPackageSmoke.cmake`

`fixture-repro.yml` lines 17-40 downloads a pinned tool, verifies its digest, rebuilds the tracked source, compares exact bytes, and checks the manifest digest. `preview.yml` lines 46-70 checks out the tested revision and records package digest, source revision, smoke result, limits, and retention. Mirror those evidence boundaries for the opt-in macOS SDL build: exact source SHA, pinned SDL source digest/license, and smoke of the produced package bytes. The preview artifact must remain a run-scoped preview, not a release claim.

## Shared Patterns

### Instance ownership, bounded operations, and reset

**Source:** `include/gabbaboy/gabbaboy.h` lines 92-147; `src/core/gabbaboy.c` lines 11-40, 127-150  
**Apply to:** public video/input API and all device state

Mutable emulated state belongs to `gbb_instance`; output buffers belong to callers and operations report exact counts/errors. Reset is explicit and clears event/device state while retaining the loaded ROM.

### Deterministic timestamps and bus sequencing

**Source:** `src/core/gabbaboy.c` lines 247-255, 279-360; `tests/test_events.c` lines 144-170  
**Apply to:** PPU, DMA, JOYP, CPU access and host input

Use absolute integer half-dot timestamps, stable event ordering, and device advancement to timed bus access. Keep host clock conversion in the adapter and verify run partition equivalence.

### Fail-closed evidence inventory and fixture identity

**Source:** `tests/CMakeLists.txt` lines 56-85; `tests/expected-tests.txt`; `cmake/ExpectedTests.cmake`; `fixtures/tracer/manifest.json`; `.github/workflows/fixture-repro.yml`  
**Apply to:** each new automated test and owned ROM

Every expected case is named in both CTest registration and inventory; fixture bytes are checked offline and reproduced in a separate pinned-tool workflow. Byte identity and guest success remain separate evidence claims.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `src/core/gabbaboy.c` PPU and DMA internals | core/device | event-driven + transform | No tracked PPU renderer, raster scheduler, VRAM/OAM arbitration, or DMA implementation exists. Extend existing instance/time/bus patterns and use the phase research for new device semantics. |
| `src/player/main.c` | SDL adapter | event-driven + file-I/O | No tracked graphical frontend, keyboard adapter, or native file dialog exists. `src/runner/main.c` is only a CLI consumer. |
| `fixtures/visible-demo/tracer.asm` gameplay/rendering logic | fixture | transform | `fixtures/tracer/tracer.asm` is a WRAM API tracer and expressly has no display/gameplay behavior. Reuse provenance/build structure only. |

## Metadata

**Analog search scope:** `include/gabbaboy`, `src`, `tests`, `fixtures/tracer`, `CMakeLists.txt`, `cmake`, `.github/workflows`  
**Files scanned:** 16 tracked analog/config files; role-specific listed paths verified with `git ls-files`  
**Pattern extraction date:** 2026-10-07
