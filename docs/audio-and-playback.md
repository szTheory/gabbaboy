# Audio and playback contract

The core emits 48,000 frames per second as signed 16-bit interleaved stereo
(left, then right). Storage belongs to the caller; core stepping allocates
nothing. Legacy run entry points advance the APU muted. Audio output is a
deterministic DMG-CPU-B software model and does not qualify a physical unit or
perceived sound quality.

## Signal acceptance limits (declared before kernel tuning)

The original project-authored signal references are a unit impulse, a zero to
positive step, and a periodic 1/8-duty pulse train. Inputs use signed Q15 mixer
levels. The impulse, step, and periodic vectors each contain 16 frames; the
Nyquist test has a 2,048-frame zero warmup followed by 2,048 alternating frames;
the high-pass settling vector has 256 frames. No imported ROM or third-party
signal fixture is used.

The kernel acceptance limits are: impulse peak no greater than the input peak;
the 1/8-duty periodic reference retains at least 1,000 output units of peak;
alternating Nyquist input is at most 32 output units after a 2,048-frame zero
warmup; and a positive step decays to between 6,000 and 7,000 units by frame
256. An additional authored edge test injects the same level change at phases
0, 3/8, and 7/8 of an output interval and requires distinct, ordered first
samples. These checks establish bounded responses for the listed vectors and
fractional-phase sensitivity; they do not establish general passband ripple,
alias rejection across all frequencies, or perceptual quality. The DMG-style
high-pass charge factor is scaled from Pan Docs' approximation to 48 kHz as
`0.999958^(4194304/48000)`, approximately `0.99634`; the filter uses Q15
coefficient 32648, nearest rounding with ties away from zero, and s16
saturation.

The original kernel detects mixed-level changes on each emulated half-dot,
maps their position into one of eight fixed fractional phases, and deposits
Q15 step-response corrections into a 16-frame per-instance ring. A bounded
16-tap update is performed only when a channel mix changes; each emitted frame
consumes one ring slot. The Q15 table is static, with no runtime generation,
allocations, dependencies, or data-dependent loop bounds. Accumulation uses
signed 64-bit intermediates and final s16 saturation. APU reset clears the
event ring, phase, mix baseline, and HPF history.

All completed PCM must be byte-identical and have identical frame counts when
the same guest timeline is run whole, in two halves, or in repeated 792
half-dot partitions. Sample phase and filter history are per instance and
survive output-call boundaries; APU reset clears them.

## Bounded throughput method

The per-emulated-half-dot work is fixed: channel state advancement and a bounded
mix comparison; a changed mix performs at most 16 table updates per channel,
and each 48 kHz crossing consumes one ring slot. The throughput bound is
therefore independent of caller buffer size and edge spacing. There are no
allocations, device calls, or external DSP packages in the core path. The
current authored signal-vector digest is FNV-1a 64
`202a3e9f96f3cead`; the guest partition PCM digest is
`b5bb127cdda6a035`. The previous FIR timing sample is not evidence for this
kernel and is retired; no isolated timing sample is claimed here. Signal tests
remain software-model evidence only, separate from perceptual or physical
hardware qualification.

## API storage and backpressure

`gbb_run_audio` writes whole frames to caller-owned memory. `frame_capacity` is
measured in frames, not samples or bytes. A NULL frame pointer is accepted only
with zero capacity. An overflowing frame extent or overlap between frame and
count storage is rejected before guest work; the count output is initialized to
zero. The core preflights the next indivisible instruction and returns
`GBB_STOP_OUTPUT_FULL` before it starts if required output will not fit;
`out_frame_count` reports frames written by that call. The caller must consume
or preserve those frames before reusing the storage. There is no hidden queue
and no silent PCM drop. Legacy `gbb_run` and `gbb_run_ex` explicitly advance the
APU muted, without PCM storage.

The DMG high-pass filter is a documented software approximation. It does not
model board variation, passive components, DAC analog behavior, host conversion,
playback hardware, or listening perception. No physical DMG or perceptual audio
qualification is claimed by the signal tests.
