# Phase 5: DMG Audio and Stable Playback - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `05-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-10-08
**Phase:** 5 — DMG Audio and Stable Playback
**Areas discussed:** DMG APU fidelity boundary; PCM format/resampling/backpressure; SDL playback/volume/queue measurement; input/session/device transitions.

The owner requested all relevant decision points be explored across technical, product, security, architecture, host, and evidence lenses, with primary sources where useful, adversarial tradeoff review, and recommendation-led defaults. The owner explicitly authorized automatically following recommendations. Three specialist reviews and targeted follow-ups were synthesized against the current C17 API, SDL3 player, phase requirements, and project evidence rules. The selected options below record that authorized synthesis; they do not claim the owner individually selected every row in an interactive menu.

---

## DMG APU model and fidelity boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Implement only the digital channel generators and omit output-stage behavior | Simplest distinction between channel correctness and output electronics; may leave DC offset/pops and diverges from the documented DMG signal path. | |
| Implement the four DMG channels and registers with one documented DMG-style high-pass approximation | Delivers useful deterministic stereo output; filter remains an explicit software model rather than a claim about every DMG-CPU-B board. | ✓ |
| Require physical DMG-CPU-B measurements before implementing analog output behavior | Strongest hardware basis, but blocks a software-model phase on hardware/data that are not currently available. | |

**User's choice:** Explore all options, then follow the synthesized recommendation.
**Notes:** Hardware/reference lens: Pan Docs describes four channels, a 512 Hz DIV-APU sequencer, NR50/NR51 routing, and a DMG high-pass approximation; its coefficient is not universal board evidence. Core lens: keep sequencer/filter state per instance and derive it from emulated divider time. Security/evidence lens: use fixed-point bounds and separate digital expectations from filtered PCM. Recommendation: include a small original fixed-point per-instance filter using the DMG-style factor scaled to 48 kHz, and label it as approximate; exclude CGB/VIN and hardware-equivalence claims.

---

## PCM format, resampling, and backpressure

| Option | Description | Selected |
|--------|-------------|----------|
| Device-native PCM or caller-configurable sample rates/formats | Flexible for frontends, but increases core configuration branches and makes cross-device output/goldens harder to compare. | |
| Fixed 48 kHz signed 16-bit interleaved stereo | Stable core contract with room for left/right NR51 routing; SDL adapts it to the device. | ✓ |

| Resampler option | Description | Selected |
|-----------------|-------------|----------|
| Box/zero-order hold | Small and predictable, but weakly suppresses square-wave harmonics and aliases. | |
| Linear interpolation | Small and smooths transitions, but is not a band-limited filter and does not establish a strong aliasing floor. | |
| Original bounded fixed-point band-limited-step/polyphase kernel | Better matches edge-driven console channels without adding a runtime dependency; adds kernel/phase arithmetic that must be tested and bounded. | ✓ |
| Blip_Buffer dependency | An established event-driven option, but adds C++ integration and LGPL compliance/build surface to a portable C17 core. | |

| Output boundary option | Description | Selected |
|-----------------------|-------------|----------|
| Unbounded core or host queue | Hides backpressure and permits memory growth under a slow consumer. | |
| Fixed per-instance core ring plus pull API | Preserves `gbb_run` call shape but adds state, buffering, and possible thread/ownership ambiguity inside the core. | |
| Caller-owned output from an audio-aware run path | Extends the existing run/output model; preflight capacity before a whole instruction and return output-full rather than drop samples. | ✓ |

**User's choice:** Explore all options, then follow the synthesized recommendation.
**Notes:** Product/consumer lens: a fixed output rate and sample type are easiest to use and reproduce. DSP lens: channel edges need an explicit anti-aliasing policy; deterministic linear interpolation alone does not guarantee quality. Architecture lens: current `gbb_run_ex` already accepts bounded caller-owned output and preflights operation capacity, while each core instance is single-threaded; caller-owned audio avoids an internal ring and makes lifetime/backpressure visible. Security/performance lens: use fixed-point operations, saturating output, bounded work, and no new package. Recommendation: 48 kHz s16 stereo; original band-limited resampler; per-instance phase; caller-buffer output with whole-instruction preflight and explicit output-full. No copying from Blip_Buffer.

---

## SDL playback, volume, and queue evidence

| Option | Description | Selected |
|--------|-------------|----------|
| Run guest emulation from the audio callback | Keeps the callback fed directly, but would move game execution and unbounded ROM-driven work onto a time-sensitive host thread and break the current single-thread ownership model. | |
| Main-loop-fed SDL stream without app callback/ring | Lowest concurrency complexity and fits current event loop; stream queued bytes support backlog metrics but not direct callback PCM-underflow counts. | |
| Pre-generate on the main loop, then feed a fixed SPSC ring consumed by SDL's stream callback | Adds small atomic/lifecycle complexity but keeps the guest on its owner thread and gives a direct count of app PCM shortages while the device requests data. | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Apply player volume by changing guest NR50/NR51 | Confuses a host preference with guest-visible hardware state and can change guest behavior. | |
| Host-only gain control in existing help/title surfaces | Keeps guest state accurate, makes volume immediately accessible, and requires no new settings UI. | ✓ |
| Add an audio preferences screen or new audio library | More options, but adds navigation/framework/dependency work outside the phase need. | |

**User's choice:** Explore all options, then follow the synthesized recommendation.
**Notes:** SDL official docs: `SDL_OpenAudioDeviceStream` supports a data callback and default playback selection; callback requests vary and may run on any thread, so it must stay bounded. The main loop remains the only guest producer. The callback copies available ring frames, zero-fills shortages, and atomically counts application PCM underflow; producer backpressure at a full ring prevents silent overrun. Target about two video frames with a hard ceiling around four as initial values, then record scripted stress and tune only with evidence. SDL stream queued bytes are submitted backlog, not played frames or end-to-end latency. Use SDL stream gain at 100% default and document unbound volume keys in help. Continue the game with a visible unavailable state and counted sink if host playback cannot open. The callback adds concurrency state, but the measured underflow requirement and existing SDL API make that cost useful; no third-party library is added.

---

## Input and session/device transition recovery

| Option | Description | Selected |
|--------|-------------|----------|
| Best-effort continuity across host transitions | Fewer explicit rules, but can leave stuck buttons or play stale samples after pause/session changes. | |
| Transactional per-source release and output flush/recovery | Makes pause, controller removal, reset, ROM replacement, and device recovery distinct; preserves current session on failed replacement. | ✓ |
| Stop guest whenever input or audio hardware changes | Simple failure state, but makes transient disconnects unnecessarily disruptive and audio optionality a hard requirement. | |

**User's choice:** Explore all options, then follow the synthesized recommendation.
**Notes:** Product/UX lens: carry forward known Phase 3 focus behavior so users do not have to learn a new pause rule. Input lens: aggregate held buttons by source; device removal releases only that device's contributions and re-add begins neutral. Core/session lens: pause preserves guest/APU/filter state, whereas reset resets APU/output after the Phase 4 battery boundary; successful ROM replacement clears old output and failed replacement preserves the current session. SDL lens: use default-device migration where possible; otherwise synchronize callback shutdown, count/discard stale host samples, then restart. Adversarial cases include removal before queued key-up, rapid remove/re-add, focus loss with held inputs, audio loss during pause/replacement, and failed ROM replacement after output is queued.

---

## the agent's Discretion

Choose exact API symbol names/signature, APU data structures, fixed-point coefficient representation and resampler kernel, ring capacity and atomic counter representation, and volume key bindings. Preserve bounded output, caller ownership, whole-instruction preflight, one-thread-per-core-instance, callback isolation, no silent drop, and the evidence boundary in `05-CONTEXT.md`.

## Deferred Ideas

CGB audio/VIN, physical DMG board calibration, universal/perceptual fidelity claims, general audio preferences/device-selection UI, and additional DSP dependencies remain outside Phase 5. Blargg fixture rights are unresolved and are not assumed closed by this discussion.
