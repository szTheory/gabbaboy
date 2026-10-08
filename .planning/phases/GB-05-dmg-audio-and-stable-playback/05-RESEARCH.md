# Phase 5: DMG Audio and Stable Playback - Research

**Researched:** 2026-10-08  
**Domain:** DMG APU modeling, bounded deterministic PCM, SDL3 playback, input and session lifecycle  
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Scoped DMG APU model

- **D-01:** Implement all four DMG channels (two pulse, wave, and noise), their documented DMG register behavior, NR50/NR51 stereo mixer routing, DAC enable behavior, and the DIV-APU frame sequencer. Clock APU progression from the emulated divider/master timeline, including divider-write edges, HALT, STOP, reset, and instruction chunk boundaries; do not derive device time from host polling or instruction counts. This is a deterministic documented software model, not a claim that every DMG-CPU-B revision behaves identically.
- **D-02:** Include a small original per-instance fixed-point DMG-style high-pass filter after the stereo mix. Use Pan Docs' documented DMG approximation and scale its charge factor to the fixed 48 kHz sample rate (`0.999958^(4194304/48000)`, approximately `0.99634` per sample); specify rounding and saturation. Reset filter history on APU reset and preserve it across ordinary output-buffer boundaries. Label the coefficient as an approximation: it does not qualify every board, passive component, output path, or host chain. Keep digital channel/mixer expectations separate from filtered PCM expectations.

### PCM contract and resampling

- **D-03:** Standardize core PCM at 48,000 frames/second, signed 16-bit interleaved stereo (left, right), with fixed-point mixing/resampling, declared rounding, and saturating conversion. The core has no device-format negotiation or host audio dependency. The frontend owns its output storage; core audio calls allocate nothing.
- **D-04:** Use a small original bounded fixed-point band-limited-step/polyphase resampler for edge-driven channel changes. Keep phase and filter state per instance; bound work for each emulated interval; exercise response, overflow, exact sample counts, and output equality across different run chunk sizes with independently authored signal fixtures. Box/hold and linear interpolation are simpler, but leave aliasing inadequately controlled for square-wave content. Blip_Buffer is a credible author implementation, but its C++/LGPL integration adds a dependency/build/license surface the project does not need yet. Do not copy its code. Reconsider an external library only if measured evidence shows the original kernel cannot meet the documented quality or throughput floor.
- **D-05:** Add an audio-aware run/output path that writes frames into caller-owned storage and preflights capacity before an indivisible guest instruction. If it cannot emit the next required sample without exceeding capacity, stop before that operation and report output-full with the actual produced frame count. Never overwrite or silently drop PCM. Keep any no-audio stepping explicitly documented as a request to run muted. Reuse the existing whole-instruction and `GBB_STOP_OUTPUT_FULL` pattern; do not add an unbounded core queue or shared global DSP state.

### SDL3 playback, host volume, and measurements

- **D-06:** Use `SDL_OpenAudioDeviceStream` for the system default playback device with an SDL audio-stream callback. The existing event/main-loop thread runs the guest and publishes its caller-buffer PCM into a separate fixed-capacity single-producer/single-consumer adapter ring; it passes no more output capacity to the core than the ring can accept. The callback feeds SDL only from that ring and never runs the emulator. Use C17 atomics with documented acquire/release ordering and bounded copy/zero-fill work. Count requested PCM frames missing from the ring as application PCM underflow, and record high-water and producer backpressure. The producer stops/limits guest advancement at capacity rather than dropping frames. Callback code must not allocate app memory, block on app locks, log, or perform lifecycle work; quiesce it before clearing or destroying adapter state.
- **D-07:** Start with an approximately two-video-frame target and a four-video-frame adapter-ring ceiling. These are bounded initial tuning values, not measured end-to-end latency guarantees. Keep the guest's half-dot timeline and APU/divider behavior independent of host queue state. SDL performs device-format/rate adaptation. SDL's stream queued-byte count is only an input backlog measure; it is not played-frame count, end-to-end latency, or proof of a hardware underrun. Report measured application underflow/backpressure/high-water by their exact names.
- **D-08:** Keep host gain independent of emulated NR50/NR51. Default to 100%, apply gain through SDL's audio stream, and expose simple discoverable keyboard volume increase/decrease controls through the existing help/title surfaces. Do not add a settings screen or audio framework. If audio cannot be opened or recovered, show audio unavailable and continue the guest through an explicit, counted host-sink policy without accumulating stale PCM.

### Input and lifecycle

- **D-09:** Carry forward Phase 3's focus-loss rule: release queued guest inputs and pause on focus loss; on focus gain, re-anchor host pacing and resume only if the owner had not intentionally paused. Track button contributions by keyboard/controller source so removing one gamepad releases only its buttons; a reconnected gamepad starts neutral. Keep host input handling in SDL's existing event loop.
- **D-10:** Pause freezes guest/APU progression but preserves channel, sequencer, resampler, and filter history. Clear pending host/device PCM at pause and produce fresh output on resume. Reset first follows Phase 4 battery flush/recovery behavior, then resets APU/output state. Successful ROM replacement flushes the old battery session before commit and clears old input/video/audio state; failed replacement preserves the active session. Prefer SDL default-device migration; when reopening is necessary, quiesce callbacks and clear/count stale host PCM. Device loss alone does not change guest clock semantics or require stopping the game.

### Acceptance evidence and limits

- **D-11:** Keep authored register/channel/sequencer tests, analytical PCM/resampler signal fixtures, callback-ring stress evidence, SDL open/conversion/recovery checks, and physical/perceptual observations as separate evidence classes. Use original project-owned fixtures with reviewed notices and reproducible bytes. Do not admit unlicensed commercial images or unresolved Blargg fixtures. No test or visual/audio plausibility alone establishes hardware equivalence.
- **D-12:** For sustained playback, report exact exercised workload and revision plus PCM output digest, ring bounds/high-water, application underflow frames/events, producer-full/backpressure events, and any intentionally host-discarded frames. An automated callback shortage is an application-side PCM underflow, not proof of physical device starvation. No subjective sound-quality or universal DMG revision claim is made without the corresponding identified listening/hardware evidence.

### the agent's Discretion

- Choose public symbol names and exact API placement for audio-aware stepping, while preserving whole-instruction atomicity, caller ownership, explicit mute semantics, and bounded output.
- Choose internal APU/channel state representation and the exact fixed-point resampler kernel/table dimensions after a complexity and quality review. Avoid introducing an abstraction framework for four channels.
- Select the smallest safe C17 atomic counter widths and ring capacity representation supported by the declared macOS targets; prove atomics are lock-free on supported builds and cover wrap/full/empty behavior.
- Select volume key bindings that do not collide with the existing guest controls; document them in the current help surface.
- Set the final stress workload duration and queue thresholds from scripted evidence. Do not label an unmeasured target a latency result.

### Deferred Ideas (OUT OF SCOPE)

- CGB APU differences, VIN, DMG board-by-board analog calibration, physical hardware qualification, and subjective quality guarantees belong in later work with the appropriate hardware and evidence.
- Additional resampler families, external APU/DSP libraries, a general audio preferences screen, audio-device selection UI, and other emulator frontends remain outside this phase unless a concrete requirement or measured gap warrants a scoped change.
- No phase-matching pending todos were found.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUDIO-01 | “All four DMG sound channels, register behavior, and divider-driven sequencer produce the expected scoped digital APU results, with analog/revision approximations documented.” [VERIFIED: `.planning/REQUIREMENTS.md:47`] | Pan Docs channel, register, and sequencer references; model applicability boundary and separate digital/filtered evidence. |
| AUDIO-02 | “A frontend receives deterministic bounded PCM with documented format, sample-rate/resampling policy, buffer lifetime, and backpressure behavior; stepping does not allocate or silently lose required output.” [VERIFIED: `.planning/REQUIREMENTS.md:48`] | Fixed PCM contract and caller-owned output; atomic whole-instruction capacity preflight; chunk-invariance and independent signal fixtures. |
| AUDIO-03 | “The macOS player provides paced sound and volume control without changing guest clock semantics, with bounded queues and measured underrun/overrun behavior during sustained scripted play.” [VERIFIED: `.planning/REQUIREMENTS.md:49`] | SDL3 stream/API behavior, producer-owned guest execution, fixed SPSC host ring, precise software-side counters and workload receipt. |
| HOST-01 | “Keyboard and basic controller input remain usable across focus loss and disconnect/reconnect; the guest cannot retain a stuck pressed button after a host input reset.” [VERIFIED: `.planning/REQUIREMENTS.md:50`] | Per-source button ownership and release/reconnect tests carried forward from Phase 3 contracts. |
| HOST-02 | “Pause/resume, reset, ROM replacement, and audio-device transitions follow documented flush/recovery rules without mixing stale video/audio/input/battery state between sessions.” [VERIFIED: `.planning/REQUIREMENTS.md:51`] | Explicit per-transition state table and session-layer battery transaction ordering; adapter callback quiescence and queue flush/count policy. |
</phase_requirements>

## Summary

Plan Phase 5 as an end-to-end vertical slice through the existing C17 core and optional SDL3 macOS adapter. Preserve the architecture boundary: guest-time APU state and deterministic PCM live in the per-instance core; device conversion, gain, host pacing, SPSC staging, and recovery live in the player. Keep all four channel generators and the frame sequencer tied to the emulated divider/master timeline. Do not use host polling, callback time, or instruction count as guest audio time. [CITED: https://gbdev.io/pandocs/Audio.html] [CITED: https://gbdev.io/pandocs/Audio_Registers.html]

The user has locked a 48 kHz signed 16-bit interleaved stereo output, a small original fixed-point edge resampler, a caller-buffer audio run path with whole-instruction preflight, and an SDL callback-fed bounded ring. These choices match the core's existing no-allocation and bounded-output architecture. SDL is already pinned at 3.4.18 in the project state; do not add a core audio package or new framework. [VERIFIED: `.planning/STATE.md:129`, “SDL3 3.4.18 and host timing remain isolated to the adapter.”] [VERIFIED: `include/gabbaboy/gabbaboy.h:186-204`, “An instruction is preflighted and won't start unless its full cost fits.”; “The core allocates/formats nothing.”]

The principal planning risk is scope interdependence: exact APU edge timing, resampler phase, output-capacity preflight, and lifecycle resets can each appear locally correct while diverging across chunk sizes or transitions. Sequence implementation so a minimal audible tracer is proven first, then expand channel behavior, PCM analysis, host callback and lifecycle cases. Keep software-model tests, authored signal fixtures, SDL adapter stress, and any physical/perceptual observations as separate evidence. Pan Docs itself describes the usual/common APU behavior and notes quirks; passing its model-derived tests is not a claim of universal silicon equivalence. [CITED: https://gbdev.io/pandocs/Audio.html] [CITED: https://gbdev.io/pandocs/Audio_details.html]

**Primary recommendation:** implement APU and deterministic PCM in the existing core, expose bounded caller-owned frames with explicit output-full semantics, then adapt them through SDL3 on the main-thread producer / callback consumer boundary; first prove timeline/chunk invariance, then measure a sustained scripted player run with labels that distinguish application PCM shortage from device playback starvation.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| DMG registers, channels, DIV sequencer, deterministic mixer/filter/resampler | Core / emulated hardware | — | These behaviors must follow guest emulated time and be reproducible independent of the host sink. [CITED: https://gbdev.io/pandocs/Audio.html] |
| Bounded output lifetime and backpressure | Core API | Player adapter | Core owns capacity preflight and result counts; player owns caller storage and must not offer capacity the ring cannot accept. [VERIFIED: `include/gabbaboy/gabbaboy.h:188-204`] |
| Device selection, sample conversion, host gain, callback and queue measures | SDL player adapter | SDL audio device | SDL stream handles device format conversion and gain; its callback receives variable byte requests and may run on any thread. [CITED: https://wiki.libsdl.org/SDL3/SDL_OpenAudioDeviceStream] [CITED: https://wiki.libsdl.org/SDL3/SDL_AudioStreamCallback] |
| Keyboard/controller focus and source ownership | SDL player event loop | Core timestamped input API | Host events are translated into guest transitions; per-source contribution lets one disconnected source be released without releasing another's buttons. [VERIFIED: `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-CONTEXT.md`, D-09] |
| Reset/replacement persistence ordering | Player session layer | Core reset and player audio adapter | Preserve Phase 4 battery flush/transaction rules before replacing/resetting the session; clear old host queues only after the transaction commits. [VERIFIED: `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-CONTEXT.md`, D-10] |

## Standard Stack

### Core

| Component | Version / Policy | Purpose | Why Standard |
|-----------|------------------|---------|--------------|
| C17 | Existing project language; no added dependency | Per-instance APU and deterministic core PCM | Required portable core boundary; no SDL or host device state in the core. [VERIFIED: `AGENTS.md`, “Original portable C core”; `.planning/STATE.md:91`] |
| Existing public run API conventions | Keep API names as planner discretion | Add audio output while preserving caller-owned buffers and whole-instruction preflight | The current API already preflights instructions and bounds optional caller-owned output. [VERIFIED: `include/gabbaboy/gabbaboy.h:186-204`] |
| Fixed-point DSP implemented in-repo | No package | Mixing, high-pass approximation, and band-limited step resampling | Directly satisfies deterministic and no-allocation core constraints; implementation must be justified by analytical tests and bounded work. [VERIFIED: `05-CONTEXT.md`, D-02 through D-05] |

### Player adapter

| Component | Version / Policy | Purpose | Why Standard |
|-----------|------------------|---------|--------------|
| SDL3 | 3.4.18 exact in current CMake configuration | Default playback stream, audio conversion, stream gain, and callback | Already an optional host dependency; keep it out of the exported core. [VERIFIED: `CMakeLists.txt:64`, `find_package(SDL3 3.4.18 EXACT CONFIG REQUIRED`] |
| C17 atomics | Existing compiler/platform support must be proved for supported macOS targets | SPSC ring indices and bounded callback counters | Avoid another queue package while requiring actual lock-free verification and documented ordering. [VERIFIED: `05-CONTEXT.md`, D-06 and discretion item 3] |
| Existing CTest / player smoke infrastructure | Extend in place | API, DSP fixture, adapter, and transition verification | Project's root CMake enables CTest. [VERIFIED: `CMakeLists.txt:19`, `include(CTest)`] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Original fixed-point kernel (locked) | Blip_Buffer | Its event-driven band-limited approach is a strong DSP alternative, but this project would take on C++ integration, LGPL obligations, and a new dependency. Keep as a revisit trigger only if analytical/throughput evidence shows the original kernel misses a documented floor. [CITED: https://www.slack.net/~ant/bl-synth/] [CITED: https://github.com/blarggs-audio-libraries/Blip_Buffer] |
| Fixed 48 kHz core format (locked) | Device-native/configurable core format | More flexible, but multiplies public behavior and golden-output cases; SDL already provides the adapter boundary. [CITED: https://wiki.libsdl.org/SDL3/SDL_OpenAudioDeviceStream] |
| Bounded callback ring (locked) | Run the emulator in the audio callback | Lowest buffering interface, but puts instruction execution, event processing, and unbounded guest work on a deadline-sensitive thread and violates existing one-thread-per-instance expectations. [VERIFIED: `AGENTS.md`, “one-thread-per-core-instance”; `05-CONTEXT.md`, D-06] |
| SPSC ring (locked) | Main-loop-only SDL stream queue | Simpler and worth considering for backlog-only playback; it does not provide a direct app-callback shortage count and makes producer pacing evidence less direct. Keep queue bytes accurately labeled. [CITED: https://wiki.libsdl.org/SDL3/SDL_GetAudioStreamQueued] |

**Installation:** None for the core or phase research. Reuse the existing SDL3 dependency and existing project build/test setup. No external audio/DSP package is recommended.

## Architecture Patterns

### Data path

```text
guest register writes + DIV/master-clock edges
        ↓
per-instance DMG channel counters / frame sequencer
        ↓
NR50/NR51 digital stereo mix → fixed-point approximate DMG HPF
        ↓
edge resampler / fixed 48 kHz s16 stereo frames
        ↓ caller-owned output; preflight before guest instruction
player main loop → bounded SPSC adapter ring
        ↓ SDL callback copies available frames, zero-fills shortage, counts it
SDL_AudioStream conversion + host gain → default playback device
```

**Recommended file ownership:** extend existing core state and bus/timeline code; expose the frame contract in the public header; keep stream/ring code in a focused player audio adapter; integrate lifecycle ownership at existing player/session routes; extend existing CTest inventories. Avoid broad audio abstractions or new user-facing settings screens. Existing source mapping is recorded in `05-CONTEXT.md` under “Integration Points”.

### Pattern 1: Drive audio from emulated edges

Use the same half-dot/master timeline as CPU and divider behavior. Advance channel timers and sequencer at emulated edges, including DIV writes and oscillator stop/reset cases. Output-call chunk boundaries must not reset or quantize the emulated phase. Pan Docs describes the APU as synchronized to the master clock, with divider-related length/envelope sequencing; the exact target software model and caveats remain explicit. [CITED: https://gbdev.io/pandocs/Audio.html] [CITED: https://gbdev.io/pandocs/Audio_Registers.html]

### Pattern 2: Capacity is checked before indivisible work

Before an instruction that may produce samples, calculate a conservative upper bound or otherwise stage the deterministic output so the core can stop before guest mutation if caller capacity is insufficient. Return actual frame count plus an explicit output-full reason; do not produce frames into hidden unbounded storage and do not discard required audio. Existing run API source quote: “An instruction is preflighted and won't start unless its full cost fits.” and “Diagnostics reserve a complete operation before it mutates state; an insufficient reserve stops with GBB_STOP_OUTPUT_FULL.” [VERIFIED: `include/gabbaboy/gabbaboy.h:186-204`]

### Pattern 3: Callback is a bounded transport adapter

SDL's callback receives requested byte counts that can vary and may run on any thread. Copy only from the fixed SPSC ring into a bounded scratch/output region, fill any shortage with silence, count missing source frames, and submit the bytes through the SDL callback contract. Never call the core, wait on an app mutex, log, allocate app memory, or perform device lifecycle work there. Quiesce the stream before resetting/destroying ring storage. [CITED: https://wiki.libsdl.org/SDL3/SDL_AudioStreamCallback] [CITED: https://wiki.libsdl.org/SDL3/SDL_OpenAudioDeviceStream] [CITED: https://wiki.libsdl.org/SDL3/SDL_PutAudioStreamData]

### Pattern 4: Keep guest state separate from host controls and queues

Volume is player gain, not an edit to emulated NR50/NR51. SDL stream gain 1.0 means no change; use it for host loudness. Device queue or ring occupancy must never alter emulated divider/APU progression. SDL stream queued bytes are bytes submitted as input and cannot be converted directly to output frames or playout latency; record ring occupancy, app underflow, producer backpressure, and intentionally discarded host frames as separate metrics. [CITED: https://wiki.libsdl.org/SDL3/SDL_SetAudioStreamGain] [CITED: https://wiki.libsdl.org/SDL3/SDL_GetAudioStreamQueued]

### Anti-Patterns to Avoid

- **Host-time-driven guest sound:** creates partition-dependent emulation and makes host load affect guest state. Drive only from emulated time.
- **Instruction-count sampling:** instruction durations and edge times vary; use timeline edges and test equal runs split into different chunks.
- **Silently dropping output on full buffers:** violates deterministic consumer contract. Stop before mutation and expose output-full/backpressure.
- **Callback runs core or logs/allocates/locks:** guest work is not bounded to the device request and can miss callback deadlines. Keep callback limited to copy, silence fill, and atomic counters.
- **Calling SDL queued bytes “latency” or “hardware underruns”:** SDL documents this as stream input bytes, not output-ready/playout measurement. Use precise labels.
- **Resetting all host input on one controller disconnect:** releases buttons still held by keyboard/other controllers. Track host-source contributions.
- **Flushing old audio before ROM replacement commits:** if replacement fails, active session and its queued playback could become inconsistent. Preserve session transaction ordering.
- **Treating determinism or emulator agreement as hardware fidelity:** retain the declared model applicability and evidence class.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|------------|-------------|-----|
| Device format/rate adaptation | Core device negotiation or a second platform audio backend | SDL3 `SDL_AudioStream` | This is already the host boundary and SDL provides app-side format plus device conversion. [CITED: https://wiki.libsdl.org/SDL3/SDL_OpenAudioDeviceStream] |
| Host gain controls | Guest register mutation to simulate player volume | SDL stream gain | Keeps user preference out of guest-visible APU state. [CITED: https://wiki.libsdl.org/SDL3/SDL_SetAudioStreamGain] |
| APU framework for four channels | Generic pluggable sound-device framework | Explicit per-instance channel state | No multiple chips/frontends are in scope; project guidance favors direct, targeted code. [VERIFIED: `AGENTS.md`; `05-CONTEXT.md`, Discretion] |
| New resampling dependency | Copy/vendor Blip_Buffer or introduce a generic DSP layer preemptively | Small original bounded kernel with fixtures | Dependency is explicitly deferred unless evidence finds the in-repo approach inadequate; do not copy code. [VERIFIED: `05-CONTEXT.md`, D-04 and Deferred Ideas] |

## Common Pitfalls

### Sequencer edge and power-state ordering

**What goes wrong:** Length/envelope/sweep events shift after DIV writes, HALT/STOP, reset, or a run-call split.  
**Prevention:** Integrate APU sequencing with the existing emulated divider transition, and lock behavior with explicit edge tests around writes and oscillator state. Do not conflate CPU machine cycles with APU ticks. [CITED: https://gbdev.io/pandocs/Audio_Registers.html]

### Nonlinear period-to-sample mapping and aliasing

**What goes wrong:** Naive per-frame output or linear interpolation masks event timing, changes results by chunk partition, or aliases the pulse/noise output.  
**Prevention:** Keep fixed-point phase per instance, specify all rounding/saturation, measure the response using independently authored impulses/steps/periodic signals, and assert exact counts and chunk equality. This recommendation is the locked design choice; its final kernel dimensions/quality floor remain agent discretion and need test evidence.

### SPSC false assumptions

**What goes wrong:** A ring appears correct under a single host but races on wrap, uses a non-lock-free atomic, or shares indices incorrectly during clear/shutdown.  
**Prevention:** Document producer/consumer ownership, acquire/release handoff, full/empty convention, arithmetic wrap proof, counter widths, target `atomic_is_lock_free` evidence, stress tests, and callback quiescence before lifecycle mutation. [VERIFIED: `05-CONTEXT.md`, D-06 and Discretion]

### SDL callback buffering misunderstood

**What goes wrong:** Treating callback request sizes as fixed frames, assuming submitted bytes are already played, or assuming a shortage counter identifies hardware starvation.  
**Prevention:** Use current `additional_amount` bytes and explicit bytes-per-frame conversion, bound callback work against a documented request ceiling, and label counts as application PCM underflow. SDL says request amounts may change from call to call and can be overestimated by stream buffering/resampling. [CITED: https://wiki.libsdl.org/SDL3/SDL_AudioStreamCallback] [CITED: https://wiki.libsdl.org/SDL3/SDL_GetAudioStreamQueued]

### Stale state on pause, focus and session transitions

**What goes wrong:** Old frames play after resume or ROM replacement; focus gain unexpectedly overrides intentional pause; source disconnect leaves input down.  
**Prevention:** Create a transition matrix that separately states guest/APU state, input release, ring clear/count, SDL stream clear, battery flush outcome, and callback quiescence for pause, focus loss/gain, reset, successful/failed ROM replacement, device migration/reopen, and shutdown. Test adversarial orderings, especially device loss while paused and replacement with queued output. [VERIFIED: `05-CONTEXT.md`, D-09 and D-10]

### Filter model overclaim

**What goes wrong:** A Pan Docs digital/software approximation is presented as measured output from every DMG-CPU-B.  
**Prevention:** Keep channel/mixer expectations separate from filtered PCM and host conversion; identify the chosen coefficient as an approximation and require identified device/listening evidence for perceptual claims. [CITED: https://gbdev.io/pandocs/Audio_details.html]

## Validation Architecture

Validation is enabled: project config contains exact source quote `"nyquist_validation": true` at `.planning/config.json:24`; security enforcement is also enabled with `"security_enforcement": true` at `.planning/config.json:48`.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | CTest through existing CMake test targets. Root CMake source quote: `include(CTest)`. [`CMakeLists.txt:19`] |
| Config file | `CMakeLists.txt`, `tests/CMakeLists.txt`, `tests/player/CMakeLists.txt` |
| Quick command | `cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` (add a focused `-R` expression only after test names exist). [VERIFIED: `README.md:22-26`] |
| Full command | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`; use the sanitizer and package/fixture lanes for the changed evidence as applicable. [VERIFIED: `README.md:22-32`; `CMakePresets.json:4-20`] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Evidence | File Exists? |
|--------|----------|-----------|--------------------|--------------|
| AUDIO-01 | Channel trigger/disable, register reads/writes, mixer routing, sequencer clocks and DIV-write edges | Unit / model regression | Add authored focused APU tests to existing core test inventory; assert relevant channel and sequencer state/output | No APU tests yet; Wave 0 / implementation |
| AUDIO-02 | Format, deterministic frames, whole-operation capacity, actual produced count, no allocation/drop, chunk-size equivalence | Unit / API regression | Add API tests with insufficient capacity before operation, exact-fit output, overrun-safe buffers, repeated/chunked identical output, and no-allocation instrumentation if existing harness supports it | No audio API tests yet; Wave 0 / implementation |
| AUDIO-03 | SDL player playback/gain, ring bounds, underflow/backpressure, transition behavior over sustained scripted play | Adapter integration / scripted stress | Extend existing player smoke/test inventory; report revision, workload, digest, target/ring bounds, high-water, underflow frames/events, producer-full events, host drops | Existing player tests only; add audio path |
| HOST-01 | Keyboard/controller source release through focus and disconnect/reconnect | Unit / SDL event integration | Extend existing input tests with interleaved source contributions, removal/re-add neutral state, focus-loss queued release | Existing input module/tests; add cases |
| HOST-02 | Pause/resume, reset, ROM replacement, audio device transitions do not mix session state | Session integration / state-transition tests | Extend session tests and player scripted smoke for successful/failed replacement plus reset/pause/device flush semantics | Existing session module/tests; add cases |

### Wave 0 Gaps

- [ ] No APU channel/sequencer test fixture inventory exists yet; author original register-driven cases with explicit DMG model applicability.
- [ ] No PCM analytical fixture suite exists; add authored impulse/step/pulse/noise and saturation/overflow checks without imported commercial ROM data.
- [ ] No SDL callback ring stress or audio-device recovery evidence exists; establish host-side deterministic ring tests independently from device-dependent smoke.
- [ ] Define a scripted sustained workload and evidence schema before measuring thresholds; include exact source revision/build/host, digest, queue/ring limits, app underflow/backpressure, and discarded host frames.

## Security Domain

Security enforcement is enabled; this is a local emulator/player, not an authenticated network service. ASVS authentication/session controls do not apply to this scope. Treat malformed/hostile ROM-driven register traffic and output capacity arithmetic as untrusted-input boundaries; keep public operations bounded, avoid overflow in frame/counter math, validate sample extents before writing, and ensure malformed or unsupported states cannot produce partial guest mutation. Avoid callbacks that can re-enter core/session operations. Do not add remote content fetching, telemetry, proprietary ROMs, or fixtures with unclear rights. [VERIFIED: `.planning/config.json:48`; `AGENTS.md`, Engineering rules and fixture restrictions]

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No authenticated user/service boundary in this phase. |
| V3 Session Management | No | No web sessions; host lifecycle rules are product-state management, not auth sessions. |
| V4 Access Control | No | No multi-user authorization boundary. |
| V5 Input Validation | Yes | Bound caller frame count and memory extents, guard integer overflow, validate adapter request sizes, preserve transactional failure behavior. |
| V6 Cryptography | No | No cryptography required; do not add it. |

**Known threat patterns:** integer overflow in frame byte/count calculations (tampering/availability); callback lifecycle race/use-after-free (availability/memory safety); adversarial guest sequences causing unbounded DSP work (availability); fixture/license provenance error (legal/project policy). Mitigate with explicit arithmetic bounds, callback quiescence, deterministic worst-case work limits, and authored fixture notices/digests.

## Code Examples

These are API-shape reminders rather than proposed code to paste into a particular implementation. Current core source quote: `GBB_STOP_OUTPUT_FULL = GBB_STOP_TRACE_FULL`; existing API docs say `"The core allocates/formats nothing."` [VERIFIED: `include/gabbaboy/gabbaboy.h:38-49, 195-204`]

```c
/* Illustrative only: actual public names and result shape remain discretion. */
audio_result = gbb_run_audio(instance, budget_half_dots,
                             caller_frames, frame_capacity);
if (audio_result.reason == GBB_STOP_OUTPUT_FULL) {
    /* Consume the returned frame count, provide capacity, then resume. */
}
```

SDL's documented app-side stream callback has signature:

```c
typedef void (SDLCALL *SDL_AudioStreamCallback)(
    void *userdata, SDL_AudioStream *stream,
    int additional_amount, int total_amount);
```

Use `additional_amount` in bytes, not as an assumed fixed callback frame count; align to the app input bytes-per-frame and cap work according to supported SDL behavior and the chosen adapter policy. SDL docs: [callback](https://wiki.libsdl.org/SDL3/SDL_AudioStreamCallback), [open stream](https://wiki.libsdl.org/SDL3/SDL_OpenAudioDeviceStream), [put data](https://wiki.libsdl.org/SDL3/SDL_PutAudioStreamData).

## State of the Art

| Earlier / tempting approach | Phase 5 recommendation | Evidence |
|------------------------------|------------------------|----------|
| Generate audio from host frame polling | Generate from emulated master/divider edges | Pan Docs synchronizes APU to master clock. [CITED: https://gbdev.io/pandocs/Audio.html] |
| Let SDL/device sample rate define core behavior | Fixed-format core PCM; convert at SDL boundary | SDL stream accepts app-side format and adapts output to device. [CITED: https://wiki.libsdl.org/SDL3/SDL_OpenAudioDeviceStream] |
| Treat stream queue bytes as played latency | Treat as submitted input backlog only | SDL states input-byte queued amount is not directly convertible to output amount. [CITED: https://wiki.libsdl.org/SDL3/SDL_GetAudioStreamQueued] |
| Treat a silent callback fill as physical device underrun | Call it application PCM underflow | Callback counts only the missing frames in the application's source ring; SDL/device internals are outside that counter. [CITED: https://wiki.libsdl.org/SDL3/SDL_AudioStreamCallback] |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The current SDL default playback migration behavior is sufficient for the player's simple default-device policy; explicit reopen remains a fallback. | Summary / SDL3 | If macOS migration does not meet the product transition contract, planner must add a scoped device-reopen path and test it. |
| A2 | A small original band-limited fixed-point kernel can meet the still-to-be-defined correctness and throughput floor without a package. | Standard Stack / resampling | If analytical quality or measured throughput fails, kernel design must be revisited; dependency remains a separately reviewed decision. |
| A3 | Fixed 48 kHz output plus SDL conversion meets the intended frontends' needs for the v0.1 phase. | PCM contract | Future embedding consumers needing another rate may require a later versioned API, not hidden runtime negotiation here. |

## Open Questions

1. **What is the testable minimum passband/alias/signal-response floor for the original resampler?**
   - What we know: format, fixed point, bounded operation, and independent response fixtures are locked.
   - What's unclear: the numerical acceptance threshold and table/kernel dimensions are not chosen.
   - Recommendation: planner schedules analytical reference calculations and measured throughput as explicit evidence; don't claim perceptual quality from a numerical fixture alone.
2. **How are SDL callback request sizes bounded for the supported stream configuration?**
   - What we know: SDL says requested byte amounts can vary and may be overestimated due to buffering/resampling.
   - What's unclear: concrete worst-case adapter scratch capacity on all supported macOS devices.
   - Recommendation: inspect SDL3 contract and the actual configured stream behavior; ensure callback can safely satisfy the current request with bounded scratch/copy policy or explicitly count/fail safely. [CITED: https://wiki.libsdl.org/SDL3/SDL_AudioStreamCallback]
3. **Which exact automated smoke can validate device transitions in CI?**
   - What we know: physical/perceptual claims are out of scope; software ring tests are automatable.
   - What's unclear: whether the repository's CI runner exposes a usable SDL audio device.
   - Recommendation: separate deterministic adapter tests from device-open smoke; if CI has no device, report that availability gap honestly and use a virtual/fake stream boundary only if already available without adding a dependency.

## Environment Availability

Phase implementation uses existing project dependencies. Runtime identity was checked and returned `{"packageName":"@opengsd/gsd-core","version":"1.16.0"}`. SDL3 is declared as exact 3.4.18 in the existing player CMake configuration; the actual audio device is an optional runtime capability and must be probed by player smoke rather than assumed present. [VERIFIED: `CMakeLists.txt:64`]

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| OpenGSD core runtime | Research tooling | ✓ | 1.16.0 | — |
| C compiler / CMake / CTest | Core and player build/tests | Project build infrastructure present; not version-probed in this research | — | Use existing repo build docs and CI matrix |
| SDL3 development package | Optional macOS player | Declared by exact CMake requirement | 3.4.18 | Core/headless checks run without SDL; player audio cannot be exercised absent package/device |
| Default playback device | Player runtime smoke | Not probed; device availability is environment-specific | — | Show audio unavailable; continue according to explicit counted host-sink policy |

**Missing dependencies with no fallback:** None identified for planning. No package install is required by the recommended design.

## Sources

### Primary / authoritative documentation

- [Pan Docs — Audio](https://gbdev.io/pandocs/Audio.html) — four specialized channels, master clock, and APU concepts. Direct page fetch returned 403 in this session; search index result exposed the page content. Treat details as cited, not session-verified.
- [Pan Docs — Audio Registers](https://gbdev.io/pandocs/Audio_Registers.html) — register conventions, channel control, NR50/NR51. Direct fetch returned 403; search index result returned targeted content.
- [Pan Docs — Audio Details](https://gbdev.io/pandocs/Audio_details.html) — generator/DAC/mixer/filter model. Search result; direct page fetch was unavailable.
- [SDL3 `SDL_OpenAudioDeviceStream`](https://wiki.libsdl.org/SDL3/SDL_OpenAudioDeviceStream) — default device, app stream format, callback setup, initially paused device, destroy semantics; opened directly 2026-10-08.
- [SDL3 `SDL_AudioStreamCallback`](https://wiki.libsdl.org/SDL3/SDL_AudioStreamCallback) — variable callback byte request, any-thread behavior, callback constraints; opened directly 2026-10-08.
- [SDL3 `SDL_PutAudioStreamData`](https://wiki.libsdl.org/SDL3/SDL_PutAudioStreamData) — copies input for later conversion, callback locking caveat; opened directly 2026-10-08.
- [SDL3 `SDL_GetAudioStreamQueued`](https://wiki.libsdl.org/SDL3/SDL_GetAudioStreamQueued) — queued input-byte semantics and lack of direct output-byte conversion; opened directly 2026-10-08.
- [SDL3 `SDL_SetAudioStreamGain`](https://wiki.libsdl.org/SDL3/SDL_SetAudioStreamGain) — gain meaning/default and thread safety; opened directly 2026-10-08.
- [SDL3 `SDL_ClearAudioStream`](https://wiki.libsdl.org/SDL3/SDL_ClearAudioStream) — pending-data drop semantics; opened directly 2026-10-08.
- [SDL3 migration guide](https://wiki.libsdl.org/SDL3/README-migration) — callback example uses `additional_amount` and `SDL_PutAudioStreamData`.
- [Band-Limited Sound Synthesis](https://www.slack.net/~ant/bl-synth/) and [Blip_Buffer source](https://github.com/blarggs-audio-libraries/Blip_Buffer) — resampling background and competitive alternative; not code to copy or a chosen dependency.

### Project sources read

- `AGENTS.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/config.json`, `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-CONTEXT.md`, `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-DISCUSSION-LOG.md`, `.planning/research/AUDIO-OUTPUT.md`, `.planning/research/INDEX.md`.
- `include/gabbaboy/gabbaboy.h`, `src/core/gabbaboy.c`, `src/player/main.c`, `CMakeLists.txt`, `tests/CMakeLists.txt`, and `tests/player/CMakeLists.txt`.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH for reuse/no new package and existing SDL version; MEDIUM for detailed SDL callback adaptation because host audio behavior varies.
- Architecture: HIGH for core/adapter ownership and explicit context decisions; MEDIUM for custom kernel and ring engineering, which need proof in implementation.
- Pitfalls: HIGH for SDL documentation caveats and project constraints; MEDIUM for hardware-model behavior due target revision limits.

**Research date:** 2026-10-08  
**Valid until:** 2026-11-07 for stable emulator/API architecture; recheck SDL docs before implementation if SDL version changes.
