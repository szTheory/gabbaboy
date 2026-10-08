# Audio and playback contract

## Scoped DMG model

The core models the four DMG APU channels on the bootless DMG-CPU-B software
timeline. Pulse one and two include their duty, frequency, length, DAC, and
envelope behavior; pulse one also models sweep. The wave channel models its
32-sample wave RAM, level, frequency, length, and DAC. The noise channel models
its polynomial timer and 15-bit or narrow-width LFSR. NR50 and NR51 control
digital left/right routing and level, NR52 exposes channel status and power,
and the frame sequencer follows the emulated divider edge, including DIV writes.

Active wave-RAM reads and writes alias the currently fetched byte in this
deterministic model. That behavior is revision-scoped and has no direct
DMG-CPU-B hardware observation. The APU does not implement CGB differences or
VIN. Its register and timing tests establish authored software-model results,
not universal silicon or board equivalence.

## PCM format and signal processing

Audio-aware stepping produces 48,000 signed 16-bit interleaved stereo frames
per second in left, right order. The frontend owns the output array and passes
its capacity in complete frames. A `gbb_run_audio` call allocates no memory;
legacy `gbb_run` and `gbb_run_ex` advance the APU muted.

Before starting an indivisible guest instruction, the core reserves enough
caller capacity for its possible PCM output. If the next operation cannot fit,
it returns `GBB_STOP_OUTPUT_FULL` and the exact count already written. The
caller must consume or preserve those frames before reusing the storage. The
core has no hidden output queue and does not drop required frames. Invalid
frame extents and overlap with the returned-count storage are rejected before
guest work.

The core uses an original per-instance fixed-point edge resampler. It detects
mixed-level changes at emulated half-dot resolution, selects one of eight
fractional phases, and accumulates a bounded 16-frame Q15 step response. Each
completed output frame consumes one event-ring slot. The static response table
uses signed 64-bit accumulation, saturating s16 conversion, and no runtime
table generation, allocation, or external DSP package.

After the mix, a DMG-style high-pass approximation uses Q15 coefficient 32648,
nearest rounding with ties away from zero, and s16 saturation. The coefficient
is scaled from Pan Docs' documented approximation to 48 kHz as
`0.999958^(4194304/48000)`, approximately `0.99634` per sample. Filter and
resampler history remain per instance across output calls and reset with the
APU. This does not model board variation, passive components, the DAC's analog
path, host conversion, or the listener's playback chain.

The project-authored impulse, step, 1/8-duty periodic, alternating-Nyquist, and
fractional-edge vectors have explicit peak, settling, and phase expectations.
They cover those listed inputs only; they do not claim general passband ripple,
alias rejection at every frequency, or perceived quality. The signal-vector
digest is FNV-1a 64 `202a3e9f96f3cead`; the authored guest partition digest is
`b5bb127cdda6a035`.

## SDL player behavior

The optional macOS SDL3 player requests 48 kHz signed-16 stereo input and lets
SDL adapt that stream to the selected playback device. Its main thread runs the
guest and is the only PCM producer. A callback consumes from a fixed SPSC ring;
it does not execute guest code. The ring stores 4096 frames and has a logical
ceiling of 3214 frames. The initial queue target reported by the measurement
route is 1606 frames, about two video frames; it is a tuning reference, not a
latency measurement or a promise that the queue remains at that level.

The host gain defaults to 100%. `[` and `]` change it by 10 percentage points
within 0% to 200%. Gain is applied in the SDL adapter and does not modify guest
APU registers. The title and F1 help report whether an SDL sink is available.
When no sink can be opened, the player discards and counts produced PCM while
guest execution remains host-paced.

Keyboard and gamepad button holds are tracked by source. Losing focus or
disconnecting one controller releases that source without releasing another
source's overlapping hold. The transition rules are:

| Transition | Guest/APU behavior | Host PCM and input behavior |
|---|---|---|
| Pause / resume | Pause freezes guest and APU time; resume continues their existing state. | Pause clears queued host PCM after callback quiescence; resume publishes fresh PCM. |
| Focus loss / gain | Focus loss pauses host-driven guest work; focus gain re-anchors host pacing and resumes only if the user had not paused. | Focus loss releases held input sources and clears queued PCM; a full guest input queue leaves releases pending for retry. |
| Reset | The battery-save transition succeeds before the core reset clears APU, resampler, and filter state. | Old host backlog is cleared after the save transition. A failed save leaves the active state in the existing retry/continue/cancel flow. |
| Successful ROM replacement | The old battery transaction completes before the new ROM is committed. | Old input, video, and host audio state are cleared only after commit. A failed replacement preserves the current session. |
| Audio device loss / recovery | Guest time semantics do not change. | The callback is quiesced before stale ring and SDL stream input are cleared and counted; the adapter follows SDL's default-device migration or reopen path. |

These are deterministic host/software transition rules. Injected device events
and the SDL dummy driver do not establish physical hotplug behavior.

## Sustained measurement

After building the pinned SDL3 player, run:

```sh
bash tests/scripts/verify-phase3-player.sh
bash tests/scripts/measure-audio-playback.sh
```

The measurement script sets `SDL_AUDIO_DRIVER=dummy` before SDL initialization,
requires a successful dummy open/stream/close/recovery smoke, and runs an
authored pulse-register workload for 300 video frames in two call partitions:
one video-frame budget and repeated 792-half-dot budgets. It replaces the entry
program of an in-memory copy of the original project-owned visible demo; the
fixture remains unchanged. The fixture is MIT-licensed and its ROM digest is
`38afb54b40f4b6612906c7a68e367199d8bff135508a39d7acdc996bf3d86530`, recorded
with its source and rights notice in `fixtures/visible-demo/manifest.json`.
The fixed partition outputs must have identical elapsed guest time, frame
count, and PCM SHA-256. A timeout is 30 seconds per route by default and can be
changed with `GBB_AUDIO_MEASURE_TIMEOUT_SECONDS` (1–300 seconds).

The JSON receipt records the full Git revision, relevant source-tree status,
Release build, model, workload and fixture identities, PCM format/digest/count,
configured queue target and ceiling, ring high-water, application PCM
underflow frames and callback events, producer backpressure observations,
intentionally discarded host frames, SDL queued-input bytes, dummy lifecycle
result, and default-device availability. It is written under
`build/phase3-player/audio-measurement/` alongside each partition's PCM and
counter record. A dirty source-tree receipt is marked `dirty`; use a receipt
from the committed revision when reporting final evidence.

Counter names retain their scope:

- `app_pcm_underflow_frames` counts complete PCM frames the application callback
  could not supply from its ring. `app_pcm_underflow_events` counts callback
  service requests that had at least one missing byte. Neither proves a
  hardware device underrun or audible dropout.
- `producer_backpressure_events` counts checks where the producer found no ring
  capacity, plus rejected ring submissions. It is an application counter, not
  guest PCM loss. The measurement route fails if any produced frame cannot be
  submitted and the script checks emitted byte count against the exact frame
  count.
- `intentionally_discarded_host_frames` counts PCM deliberately removed when a
  sink is unavailable or a host queue is cleared. It does not claim that the
  physical device played or dropped those frames.
- `audio_stream_write_failures` counts SDL callback writes that the audio stream
  rejected. `audio_stream_write_failure_pcm_bytes` counts ring-backed PCM bytes
  consumed by rejected writes, including the unsubmitted tail of a partial
  frame that cannot be resumed safely. Zero-filled underflow bytes are excluded.
  This is adapter-side loss accounting; it does not establish hardware playback.
- `sdl_queued_input_bytes` is SDL's queued input-byte count. It is not ring
  occupancy, played-frame count, output backlog, latency, or proof of device
  starvation.

The default-device probe only opens the default route and reports available or
unavailable. It does not play the measurement workload. Dummy-device and
injected-event results remain separate from physical hotplug, identified
hardware, and listening evidence.

## Evidence classes and limits

| Evidence class | What it establishes | What it does not establish |
|---|---|---|
| Authored register/channel/sequencer tests | The declared deterministic DMG-CPU-B model behavior on tested guest programs. | Silicon identity, undocumented revision quirks, CGB APU behavior, or analog output. |
| Authored signal vectors and run partitions | Listed numerical response bounds, checked API bounds, and byte/count equality across exercised partitions. | All-frequency fidelity, a general throughput benchmark, or perceived quality. |
| Ring stress and sustained receipt | Bounded SPSC behavior, application-side queue counters, and same-output workload identity. | Hardware starvation, end-to-end latency, physical output, or listening quality. |
| SDL dummy open/stream/close and injected events | The built software backend opens, accepts stream input, closes, and follows tested recovery paths. | Physical device hotplug, every host driver, or that queued bytes reached a speaker. |
| Physical or perceptual observation | Not collected for this phase. | No physical DMG-CPU-B, board/revision equivalence, analog, or subjective sound-quality claim is made. |

No Nintendo boot ROM, commercial game image, unlicensed homebrew, or unresolved
third-party audio fixture is used by the measurement route.
