# Phase 5: DMG Audio and Stable Playback - Context

**Gathered:** 2026-10-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the four DMG APU channels and their register/divider-sequencer behavior in the existing bootless DMG-CPU-B software model; provide bounded deterministic 48 kHz stereo PCM; play it through the optional SDL3 macOS player with host volume, responsive input, and clean recovery across pause, focus, controller, ROM, reset, and audio-device transitions. The phase must document where a deterministic software approximation ends and hardware/perceptual qualification would begin.

This phase does not add CGB audio, VIN input, boot ROM execution, a new audio framework, generic audio settings UI, emulator-wide threading, or physical DMG-CPU-B claims. Existing C17, one-thread-per-core-instance, explicit ownership, bounded operations, no-unlicensed-fixture, and phase-pause constraints continue to apply. No third-party APU or resampler dependency is planned; revisit one only if measured correctness or performance evidence justifies its integration and license surface.

</domain>

<decisions>
## Implementation Decisions

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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope, owner constraints, and requirements
- `AGENTS.md` — C17, bounded operations, dependency preference, evidence classes, fixture rights, and mandatory phase pause.
- `.planning/PROJECT.md` — GB/GBC identity and core/player product boundary.
- `.planning/REQUIREMENTS.md` § Audio and host lifecycle — AUDIO-01 through AUDIO-03 and HOST-01/HOST-02 acceptance.
- `.planning/ROADMAP.md` § Phase 5 — goal, success criteria, scope, and dependency.
- `.planning/STATE.md` — current phase/session status and exact handoff route.
- `.planning/context/BRIEF.md` — owner priorities, including a small dependency tree.
- `.planning/context/DECISIONS.md` — D-015 (evidence classes), D-016 (measure before performance complexity), D-025 (confidence-qualified software models), and prior workflow constraints.
- `.planning/context/WORKFLOW.md` — authorized progression and mandatory stop at phase boundaries.

### Research, evidence, and quality
- `.planning/research/INDEX.md` — research routing and confidence/provenance rules.
- `.planning/research/AUDIO-OUTPUT.md` — Phase 5 APU, PCM, SDL, queue-measurement, and evidence research.
- `.planning/research/SUMMARY.md` — integrated model/evidence and fixture-rights constraints.
- `.planning/research/ARCHITECTURE.md` — core timeline, host adapter, ownership, and per-instance boundaries.
- `.planning/research/HARDWARE-AND-VALIDATION.md` — model applicability, fixture admission, evidence labels, and no hardware overclaims.
- `.planning/research/PITFALLS.md` — misleading emulator agreement, untrusted ROMs, and false acceptance signals.
- `.planning/research/QUALITY-AND-DELIVERY.md` — CTest, sanitizer, fixture reproduction, and package-smoke conventions.

### Prior decisions and implementation surfaces
- `.planning/phases/GB-03-visible-interactive-dmg/03-CONTEXT.md` and `03-RESEARCH.md` — SDL event loop, pacing, focus loss/gain, keyboard mapping, and transactional ROM replacement.
- `.planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-CONTEXT.md` — battery flush/recovery ordering and failed-replacement preservation.
- `include/gabbaboy/gabbaboy.h` — one-thread-per-instance, no-allocation run API, whole-instruction behavior, caller-owned output, and `GBB_STOP_OUTPUT_FULL` contracts.
- `src/core/gabbaboy.c` — per-instance guest state, half-dot timeline, divider advancement, and run/diagnostic preflight.
- `src/player/main.c` — SDL main loop, host pacing, window/help/status, and reset/replacement/quit paths.
- `src/player/input.c` and `src/player/input.h` — keyboard mapping, timestamped events, focus-release tracking, and bounded input admission.
- `src/player/session.c` and `src/player/session.h` — transactional ROM/session and battery lifecycle integration.
- `tests/test_api.c`, `tests/test_timer.c`, `tests/player/test_input.c`, `tests/player/test_session.c`, `tests/CMakeLists.txt`, `tests/player/CMakeLists.txt`, and `tests/expected-tests.txt` — API, timing, player behavior, and required inventory patterns.
- `fixtures/visible-demo/manifest.json` and `tests/scripts/reproduce-visible-demo.sh` — original fixture rights and pinned RGBDS reproduction precedent.
- `.github/workflows/ci.yml`, `.github/workflows/fixture-repro.yml`, and `.github/workflows/preview.yml` — current evidence/package paths.

### External technical references
- [Pan Docs — Audio](https://gbdev.io/pandocs/Audio.html), [Audio Registers](https://gbdev.io/pandocs/Audio_Registers.html), and [Audio Details](https://gbdev.io/pandocs/Audio_details.html) — channel behavior, register map, divider sequencer, and high-pass approximation.
- [Gekkio, Game Boy: Complete Technical Reference](https://gekkio.fi/files/gb-docs/gbctr.pdf) — hardware/revision context; not an observation of the target unit.
- [SDL3 `SDL_OpenAudioDeviceStream`](https://wiki.libsdl.org/SDL3/SDL_OpenAudioDeviceStream), [`SDL_AudioStream`](https://wiki.libsdl.org/SDL3/SDL_AudioStream), [`SDL_AudioStreamCallback`](https://wiki.libsdl.org/SDL3/SDL_AudioStreamCallback), [`SDL_GetAudioStreamQueued`](https://wiki.libsdl.org/SDL3/SDL_GetAudioStreamQueued), [`SDL_SetAudioStreamGain`](https://wiki.libsdl.org/SDL3/SDL_SetAudioStreamGain), and [`SDL_ClearAudioStream`](https://wiki.libsdl.org/SDL3/SDL_ClearAudioStream) — official SDL3 queue, callback, conversion, gain, and lifecycle contracts.
- [Band-Limited Sound Synthesis](https://www.slack.net/~ant/bl-synth/) and [Blip_Buffer](https://github.com/blarggs-audio-libraries/Blip_Buffer) — author resampling rationale and implementation comparison; no upstream code is to be copied into the core.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `gbb_instance` in `src/core/gabbaboy.c` owns CPU, divider, timer, graphics, mapper, cartridge RAM, and time state; APU, sequencer, filter, and resampler state belong on this per-instance object.
- `gbb_run_internal` executes whole instructions, advances devices to the resulting half-dot, and already checks diagnostic capacity before mutation. The existing `GBB_STOP_OUTPUT_FULL` reason is a direct pattern for audio output backpressure.
- The public core has no SDL or filesystem dependency and promises one-thread-at-a-time access to each instance. Keep core PCM production on the same host thread that calls `gbb_run`; a device callback may consume only separately owned adapter-ring memory.
- The optional SDL3 player already owns a monotonic host-paced main loop, focus transitions, help/status, ROM replacement, reset, and quit handling. Build on these routes instead of introducing another window, settings, or audio framework.
- The session layer already owns transactional replacement and Phase 4 battery flush behavior. Apply those existing guarantees before clearing APU/host output on reset or replacement.
- Tests use fixed CTest inventories, original fixture manifests, and pinned RGBDS reproduction. Extend those contracts rather than adding a network-dependent test framework or an unreviewed ROM corpus.

### Established Patterns
- Core memory and outputs are per-instance, bounded, and caller-owned; failed calls preserve live state. Preserve these patterns for output frames, sample counts, and transition recovery.
- Existing CPU/timer behavior uses half-dot time and divider edges; the APU frame sequencer should follow those emulated edges, not host time.
- SDL and host timing stay in the adapter. Its audio-stream callback copies/zero-fills already generated PCM from the host ring into SDL and updates lock-free counters; it never advances the guest.
- Phase 3 focus loss pauses and queues releases; Phase 4 flushes battery RAM before reset/replacement and preserves the active session on failed replacement. Reuse those contracts.
- Evidence reports distinguish software model, independent fixture, SDL adapter, and hardware/perceptual observations. A deterministic digest is not by itself evidence of DMG fidelity.

### Integration Points
- Add APU register decoding to core read/write paths and sequence channel state on the existing divider/timeline, including DIV write and reset interactions.
- Produce fixed-format PCM from the per-instance mixer/filter/resampler; extend run/output reporting with bounded caller-owned capacity and preflight before a whole instruction.
- Add an optional SDL playback adapter with gain, a default-device stream, a bounded single-producer/single-consumer ring, and callback-safe state. Keep guest execution and event handling on the main thread.
- Extend player keyboard/controller source tracking and window/help status. Clear stale output at pause, reset, successful ROM replacement, focus/device recovery, and shutdown without mutating guest time.
- Add authored APU/PCM fixture coverage and host queue stress cases to existing test inventories and package evidence. Document that no physical DMG or subjective audio qualification is implied.

</code_context>

<specifics>
## Specific Ideas

- The owner asked for wide, adversarial consideration across relevant roles and ecosystems, primary sources where practical, synthesis into a concrete recommendation, and a preference for fewer/shallower dependencies. This context adopts that direction: one original bounded DSP kernel and small SPSC ring, no new package.
- SDL stream queue bytes are not end-to-end latency and cannot prove hardware underrun. Report app-level underflow/backpressure precisely and avoid stronger claims.
- APU digital tests, high-pass/resampler fixtures, SDL conversion/queue stress, and physical/perceptual observations remain distinct. An original authorized fixture is the required baseline; Blargg redistribution is not assumed.

</specifics>

<deferred>
## Deferred Ideas

- CGB APU differences, VIN, DMG board-by-board analog calibration, physical hardware qualification, and subjective quality guarantees belong in later work with the appropriate hardware and evidence.
- Additional resampler families, external APU/DSP libraries, a general audio preferences screen, audio-device selection UI, and other emulator frontends remain outside this phase unless a concrete requirement or measured gap warrants a scoped change.
- No phase-matching pending todos were found.

</deferred>

---

*Phase: 5-DMG Audio and Stable Playback*
*Context gathered: 2026-10-08*
