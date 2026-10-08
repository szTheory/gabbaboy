# Audio and playback contract

The core emits 48,000 frames per second as signed 16-bit interleaved stereo
(left, then right). Storage belongs to the caller; core stepping allocates
nothing. Legacy run entry points advance the APU muted. Audio output is a
deterministic DMG-CPU-B software model and does not qualify a physical unit or
perceived sound quality.

## Signal acceptance limits (declared before kernel tuning)

The original project-authored signal references are a unit impulse, a zero to
positive step, and a periodic 1/8-duty pulse train. Inputs use signed Q15 mixer
levels. The test workload has 16 samples for the resampler vectors and 256
samples for high-pass settling. No imported ROM or third-party signal fixture
is used.

The kernel acceptance limits are: impulse peak no greater than the input peak;
the 1/8-duty periodic reference retains at least 1,000 output units of peak;
alternating Nyquist input is at most 32 output units after a 2,048-frame zero
warmup; and a positive step decays to between 6,000 and 7,000 units by frame
256. These are bounded software-model signal checks, not a psychoacoustic
rating. The DMG-style high-pass charge factor is scaled from Pan Docs'
approximation to 48 kHz as `0.999958^(4194304/48000)`, approximately `0.99634`;
the filter uses Q15 coefficient 32648, nearest rounding with ties away from
zero, and s16 saturation. The original FIR has eight fixed Q15 taps
`[682,2731,5461,7510,7510,5461,2731,682]`, phase zero, no runtime table
generation, and no data-dependent work.

All completed PCM must be byte-identical and have identical frame counts when
the same guest timeline is run whole, in two halves, or in repeated 800
half-dot partitions. Sample phase and filter history are per instance and
survive output-call boundaries; APU reset clears them.

## Bounded throughput method

The per-emulated-half-dot work is fixed: channel state advancement, one bounded
mix/filter operation when a 48 kHz frame deadline is crossed, and fixed-size
history updates. There are no data-dependent loops, allocations, device calls,
or external DSP packages in the core path. The throughput gate is structural
and deterministic: one bounded operation per half-dot and at most one PCM frame
per crossing. No host timing result is claimed until measured against a named
build, workload, digest, sample count, and uncertainty. This plan's signal tests
therefore distinguish exact software behavior and analytical bounds from
perceptual or hardware qualification.

## API storage and backpressure

`gbb_run_audio` writes whole frames to caller-owned memory. `frame_capacity` is
measured in frames, not samples or bytes. A NULL frame pointer is accepted only
with zero capacity. The core preflights the next indivisible instruction and
returns `GBB_STOP_OUTPUT_FULL` before it starts if required output will not fit;
`out_frame_count` reports frames written by that call. The caller must consume
or preserve those frames before reusing the storage. There is no hidden queue
and no silent PCM drop.

The DMG high-pass filter is a documented software approximation. It does not
model board variation, passive components, DAC analog behavior, host conversion,
playback hardware, or listening perception. No physical DMG or perceptual audio
qualification is claimed by the signal tests.
