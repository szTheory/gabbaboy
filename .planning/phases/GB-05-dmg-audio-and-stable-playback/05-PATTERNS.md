# Phase 5: DMG Audio and Stable Playback - Pattern Map

**Mapped:** 2026-10-08  
**Files analyzed:** 17 likely implementation, integration, and validation files  
**Analogs found:** 14 / 17 (as implementation-structure analogs; there is no existing APU, PCM, SPSC ring, or callback implementation)

This is a codebase pattern map, not a design override. The phase context locks the audio contract. Existing patterns below are safe to reuse where stated; timer, input, and session code are analogs for organization and invariants, not code to transplant into audio logic.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `include/gabbaboy/gabbaboy.h` | public API | request-response / caller-owned output | same file's `gbb_run_ex` contract | exact API convention |
| `src/core/gabbaboy.c` | core model, bus, timeline | event-driven / transform | same file's timer/divider and whole-operation run loop | role-match; no APU analog |
| `src/player/audio.h` (likely new) | adapter interface | streaming | `src/player/input.h` | role-match for bounded adapter state; no audio analog |
| `src/player/audio.c` (likely new) | SDL audio adapter and ring | streaming / event-driven | `src/player/input.c` for bounded state transitions; `src/player/main.c` SDL ownership for integration | partial; no callback/SPSC analog |
| `src/player/input.h` | adapter state/API | event-driven | existing source ownership and queue declarations | direct extension |
| `src/player/input.c` | input adapter | event-driven | itself; focus release and retry | exact |
| `src/player/main.c` | app controller | event-driven / streaming | existing event loop, pause/reset/replacement routes | exact integration location |
| `src/player/session.c` | session service | file-I/O / transactional | existing replacement and battery persistence | exact lifecycle contract; audio should not move into this module |
| `src/player/session.h` | service interface | request-response | existing session declarations | exact |
| `tests/test_apu.c` (likely new) | core test | event-driven / transform | `tests/test_timer.c` | role-match |
| `tests/test_audio.c` or audio cases in API tests (likely new/modified) | core API test | streaming / request-response | `tests/test_api.c`, `tests/test_events.c` | role-match |
| `tests/player/test_audio.c` (likely new) | adapter test | streaming / event-driven | `tests/player/test_input.c` | role-match; no concurrent ring test analog |
| `CMakeLists.txt` | build config | build graph | existing optional player target | exact |
| `tests/CMakeLists.txt` | test registration | test inventory | existing core test targets | exact |
| `tests/player/CMakeLists.txt` | test registration | test inventory | existing player inventory dispatch | exact |
| `tests/expected-tests.txt` | test inventory | configuration | self, mirrored by `tests/CMakeLists.txt` registrations | exact convention |
| `tests/player/expected-tests.txt` | test inventory | configuration | self, dispatched by player CMake file | exact convention |

The context also names `tests/test_timer.c`, `tests/player/test_input.c`, `tests/player/test_session.c`, and `tests/scripts/reproduce-visible-demo.sh` as precedent. They need not all change: add a new focused test file only if it improves separation, and extend existing inventories and fixture evidence without introducing a framework or unlicensed ROM corpus. No new fixture manifest is required if signal vectors are authored as test data; if a redistributable binary fixture is added, follow the existing manifest/reproduction precedent.

## Pattern Assignments

### `include/gabbaboy/gabbaboy.h` (public API, request-response)

**Analog:** `include/gabbaboy/gabbaboy.h`, lines 181-207.

The established contract documents whole-instruction execution, explicit stop reasons, caller-owned optional buffers, no allocation, and returned output counts. Lines 197-203 state that outputs remain caller-owned and capacity is reserved for a complete operation before state mutation; insufficient capacity reports `GBB_STOP_OUTPUT_FULL` without writing a record for that operation. Model the audio API on those properties, but define frame units, format, mute behavior, and PCM-count reporting explicitly. The existing `GBB_STOP_OUTPUT_FULL` alias at line 48 is a convention to inspect, not evidence that reusing the trace enum alias is necessarily the right public API shape.

**Safe to reuse:** API documentation style and the contract principles (bounded operation, preflight, output counts).  
**Do not copy blindly:** the current stop-reason alias and trace-specific result fields; audio needs an unambiguous public contract.

### `src/core/gabbaboy.c` (core APU integration, event-driven)

**Analog:** the same file, `struct gbb_instance` lines 22-105; `reset_state` lines 286-320; DIV write lines 579-582; divider advancement lines 1077-1085; run/preflight lines 1643-1745.

Core state is embedded per instance. Reset initializes explicit fields. The divider increments on the existing half-dot timeline, and DIV writes update the timer signal at the write timestamp. The run loop validates state, bounds timeline arithmetic, and reserves capacity before executing an indivisible operation. Put APU/channel, sequencer, filter, resampler, and output phase state in instance-owned core state; wire events to emulated divider/timeline transitions rather than host time. Use the current timer edge behavior as a synchronization analogy, then implement APU-specific edge rules from the phase specification and primary references.

**Safe to reuse:** per-instance ownership, explicit reset initialization, half-dot scheduling, overflow checks, existing bus read/write integration, whole-instruction preflight shape.  
**Do not copy blindly:** timer signal logic, timer bit selection, or timer edge semantics as a substitute for APU behavior. There is no APU implementation to copy.

### `src/player/audio.h` (likely new, adapter interface)

**Analog:** `src/player/input.h`, lines 1-48.

The input adapter declares fixed capacities and a concrete state struct, then exposes narrow functions operating on that state and an instance. Audio may use the same direct C header style: explicit frame/ring capacities, owned state, initialization/teardown and producer/consumer functions with clear thread ownership. Keep SDL types at this player boundary and core headers SDL-free. Unlike input, ring producer and callback consumer will access state concurrently; document atomic fields and ownership in this new API rather than copying the non-atomic input state pattern.

**Safe to reuse:** include guard, direct declarations, fixed bounds, explicit arguments.  
**No close analog:** C17 SPSC atomics, callback lifecycle, lock-free proof.

### `src/player/audio.c` (likely new, SDL audio adapter, streaming)

**Analogs:** `src/player/main.c` for SDL resource ownership and `src/player/input.c` for a bounded adapter API. No tracked source has an audio callback, SPSC ring, or stream lifecycle.

The research/context design calls for SDL3 `SDL_OpenAudioDeviceStream`, an app-owned fixed-capacity SPSC ring, and a callback that only copies available PCM, zero-fills missing frames, and updates counters. Keep all guest execution and PCM production on the existing main/event-loop thread. In contrast with existing input adapter logic, callback code must not call into the core, allocate, log, block, or perform recovery. Quiesce the stream before clearing/freeing ring state. C17 atomic ordering and lock-free guarantees require dedicated implementation and stress evidence; no current code proves them.

**Safe to reuse:** SDL object ownership conventions from `main.c`; direct, bounded functions from `input.c`.  
**Do not reuse:** input's ordinary state mutation across threads.  
**No analog found:** callback buffer filling, SPSC wrap/full/empty handling, underflow counters, stream open/recovery.

### `src/player/input.h` and `src/player/input.c` (controller contribution tracking)

**Analog:** self. Header declares fixed queue capacity and explicit pause/release state; implementation checks queue capacity before admission, stores only accepted events, and retries focus releases if space is unavailable. `input.c:164-203` shows release construction, room check, timestamp scheduling, core queue call, and state update only after success.

Extend source ownership so keyboard and each gamepad contribute independently to guest buttons. A source removal should clear only its own contribution, then synthesize guest release only when no other source still holds that button. Preserve bounded admission and retry/focus rules. The current aggregate `held_buttons` bitmask is not sufficient evidence for source accounting; introduce the smallest explicit per-source representation that meets D-09.

**Safe to reuse:** bounded input queue, timestamp mapping, pause/release retry semantics, commit state only after successful queueing.  
**Do not copy blindly:** aggregate bitmask semantics for multiple controllers.

### `src/player/main.c` (app integration and lifecycle)

**Analog:** same file, `reset_session` lines 442-460; `replace_session_rom` lines 471-535; pause lines 757-771; focus event handling lines 849-890; help surface lines 332-355.

The event loop already owns pause/focus handling, host pacing, status/help, reset, replacement, and shutdown. Integrate audio start/stop, gain shortcuts, audio-unavailable status, output publication, and queue clearing into these existing routes. Successful replacement swaps a staged candidate only after validation/load; failure returns before replacing active state. Reset and replacement update input/display state only after core/session operations succeed. Keep device recovery and callback quiescence explicit and keep guest progression independent of adapter backlog.

**Safe to reuse:** current lifecycle ordering, focus ownership, status/help surface, candidate-before-commit replacement.  
**Do not copy blindly:** battery-specific policy into audio code; session save behavior remains owned by session/main transitions.

### `src/player/session.c` and `src/player/session.h` (lifecycle boundary)

**Analog:** self, especially `player_session_replace_rom` and battery save/load functions. Phase 4 transactional battery behavior is already implemented here and called by `main.c`.

Audio lifecycle likely does not require changes to this service: D-10 places save flush and replacement transaction before committing new guest state, while host PCM clearing belongs at player transition boundaries. Modify session files only if integration reveals a narrowly necessary lifecycle hook; do not make the session layer own SDL streams or audio ring storage.

**Safe to reuse:** candidate validation and battery persistence guarantees.  
**Likely no change:** session's data model should remain ROM/save-focused.

### `tests/test_apu.c` (likely new) and core test sources

**Analog:** `tests/test_timer.c`, lines 1-18 and 192-225. Tests use a small guest program, load it into a real core instance, observe bus events or visible state, assert exact timestamps/values, and clean up. `tests/CMakeLists.txt:45-50` registers focused named cases using one executable and case argument.

Use short authored register-writing programs or internal test hooks already supported by the core. Cover register/DAC behavior, channel triggers, DIV-APU sequencer transitions, and reset/HALT/STOP/timeline partition edges with explicit DMG model applicability. Keep model assertions separate from filtered PCM and SDL assertions. Test fixtures must be independently authored and rights documented; do not import commercial ROMs or unresolved Blargg assets.

**Safe to reuse:** standalone C test executable style, named cases, exact edge/timestamp assertions, CTest case loop.  
**Do not copy blindly:** timer-specific observer internals or expected hardware behavior; APU model tests need their own justified assertions.

### Core PCM/API test file (likely `tests/test_audio.c` or API extension)

**Analogs:** `tests/test_api.c` lines 64-83 for bounds and untouched sentinel checks; `tests/test_events.c` for operation partition/capacity patterns; `tests/CMakeLists.txt` for target/test registration.

Exercise caller-buffer ownership, format/sample counts, zero/short/exact capacity, output-full before mutation, no overwrite, deterministic equality across different run chunk partitions, fixed-point saturation, and independently authored response fixtures. Add no allocation instrumentation only if an existing harness supports it. Keep fixtures in owned test code unless reusable binary data warrants a manifest.

**Safe to reuse:** sentinel-buffer assertions, separate instances, named case registration, C17/strict-extension target settings.  
**No analog found:** audio output arithmetic or resampler reference signals.

### `tests/player/test_audio.c` (likely new, adapter streaming test)

**Analog:** `tests/player/test_input.c`, lines 148-210. It sets up controlled state, tests both normal success and queue-full/recovery, asserts exact held/release state, and cleans up. `tests/player/CMakeLists.txt:7-25` lazily creates a focused executable based on the expected-test inventory.

Create deterministic host-side ring tests independent of physical audio hardware: wraparound, empty/full, producer backpressure, callback short fill/zero-fill, counter behavior, bounded request handling, and safe clear only after callback quiescence. Use actual concurrent stress only with explicit race-safe synchronization and repeatable setup; device/perceptual checks remain separate evidence classes.

**Safe to reuse:** case dispatch and state assertions.  
**No analog found:** concurrent ring stress, callback behavior, SDL audio device conversion/recovery.

### `CMakeLists.txt` (build graph)

**Analog:** `CMakeLists.txt:63-82` defines the optional player, pins SDL3, lists adapter sources, links `GabbaBoy::core` and SDL3, and enforces C17 without extensions. Add the focused audio adapter source to that existing target; do not introduce another dependency or audio framework. If core APU code becomes a separate source file, add it to the existing core target using its current source-list pattern.

### `tests/CMakeLists.txt`, `tests/player/CMakeLists.txt`, and expected inventories

**Analogs:** `tests/CMakeLists.txt:4-12,45-50` creates strict C17 executables and named test cases; `tests/player/CMakeLists.txt:1-25` reads the checked-in inventory and dispatches player cases; `tests/expected-tests.txt` and `tests/player/expected-tests.txt` enumerate required cases.

Add tests to both the CMake registrations and the corresponding expected-test inventory so the project’s fixed inventory check continues to enforce coverage. Reuse target properties and `gabbaboy-player-adapter` linkage. Keep tests deterministic; do not add network-dependent testing packages.

## Shared Patterns

### Core ownership and determinism

**Source:** `src/core/gabbaboy.c:22-105`, `include/gabbaboy/gabbaboy.h:117-120,181-204`  
**Apply to:** core APU/DSP and run-output API.

State belongs to a `gbb_instance`, public operations are bounded, caller owns output buffers, and one thread calls an instance at a time. Host device callbacks must only touch separately owned player adapter memory.

### Preflight and failure atomicity

**Source:** `include/gabbaboy/gabbaboy.h:187-203`; `src/core/gabbaboy.c:1728-1739`  
**Apply to:** audio frame capacity and producer publication.

Validate capacity and arithmetic before guest mutation. Report actual written frames; never overwrite or silently discard required core PCM. Player backpressure limits guest advancement rather than growing hidden storage.

### Player lifecycle and input release

**Source:** `src/player/main.c:471-535,757-771,869-890`; `src/player/input.c:164-203`  
**Apply to:** pause/focus/reset/replacement/device transitions.

Preserve intentional pause state through focus changes, release host-held buttons on focus loss, re-anchor host pacing after recovery, stage replacements before swapping, and tie ring/stream clearing to transition success and callback quiescence.

### Test inventory

**Source:** `tests/CMakeLists.txt`, `tests/player/CMakeLists.txt`, `tests/expected-tests.txt`, `tests/player/expected-tests.txt`  
**Apply to:** all new automated test files/cases.

Every test is explicitly registered and listed in the expected inventory. Keep core model, PCM signal, callback ring, SDL device, and hardware/perceptual evidence separate.

## No Analog Found

| File/Concern | Role | Data Flow | Reason |
|---|---|---|---|
| APU/channel and frame-sequencer state | core model | event-driven | No sound channels or APU register model exists. Timer/divider is only a timing integration analog. |
| Fixed-point mixer, DMG-style high-pass, edge resampler | utility/model | transform / streaming | No PCM or DSP code exists; implement a small original bounded kernel and verify with authored signals. |
| SDL callback and SPSC ring | player adapter | streaming / concurrent | Existing player adapters are single-threaded; no callback/ring pattern exists. |
| Physical/perceptual qualification | evidence | external observation | No code analog can establish hardware-specific or listening claims. |

## Metadata

**Analog search scope:** tracked `include/gabbaboy`, `src/core`, `src/player`, `tests`, root `CMakeLists.txt`, and phase context/research integration points.  
**Tracked-source gate:** all named code analogs were verified with `git ls-files`; no ignored runtime mirrors are referenced.  
**Pattern extraction date:** 2026-10-08
