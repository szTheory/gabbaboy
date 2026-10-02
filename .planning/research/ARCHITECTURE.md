# GabbaBoy architecture research

Researched: 2026-10-02. Scope: Game Boy (DMG) and Game Boy Color (CGB), portable C core with optional host adapters.
Evidence confidence: **MEDIUM**, returned by OpenGSD `query classify-confidence --provider websearch --verified` for primary sources checked through web research. Design choices below are recommendations, not measured performance claims.
Related evidence and test corpus policy: [HARDWARE-AND-VALIDATION.md](HARDWARE-AND-VALIDATION.md).

## Recommendation

Build one deterministic, instance-owned machine with explicit hardware profiles, CPU bus phases, and a shared integer timeline. Keep the public API independent of SDL, operating systems, filesystem paths, network access, wall clocks, and Playstead implementation details. Ship a headless runner and thin desktop player against that same API early.

Use ordinary C17 modules with private state and named hardware operations. Begin with a readable interpreter and dot-sensitive PPU state machine. Optimize measured hot paths only after a representative correctness corpus passes. A whole-instruction scheduler that performs all memory effects at instruction end would make later timing work expensive. [SM83 reference](https://gekkio.fi/files/gb-docs/gbctr.pdf), [PPU timing](https://github.com/gbdev/pandocs/blob/master/src/Rendering.md).

## Component boundaries

```text
Playstead adapter / desktop player / CLI / benchmark and fuzz harnesses
                              |
                       public gabbaboy.h
                              |
            instance, lifecycle, bounded execution, state codec
                              |
             timing coordinator and bus ownership rules
              /       /       |       \       \
            SM83    timer    PPU/DMA    APU    serial/input
                              |
                 cartridge mapper / RAM / RTC
```

| Module | Owns | Boundary |
|---|---|---|
| `machine` | Model, lifecycle, time, stop reasons, component composition | Only public API implementation reaches all components |
| `cpu` | SM83 registers, instruction phase, IME delay, HALT/STOP/lock state | Timed bus operations; never host memory or I/O directly |
| `bus` | Address decoding, I/O routing, access restrictions, bus latches | Access initiator distinguishes CPU, DMA and PPU; debug peek is side-effect free |
| `timer` | System divider phase, edge detector, TIMA reload state | One divider source shared with APU sequencing |
| `ppu` | Modes, scanline/dot position, fetcher, pixel FIFOs, window/object state | Hardware color output and frame-ready events |
| `dma` | OAM DMA and CGB VRAM DMA progress, delays, bus claims | Transfer at scheduled times; no instantaneous bulk copy shortcut |
| `apu` | Four channels, DIV-APU sequencing, mixer/resampling state | Bounded PCM output; no audio-device callbacks inside emulation |
| `cartridge` | Validated ROM mapping, mapper state, battery RAM, RTC | Mapper operations receive emulated time and typed external events |
| `serial`, `joypad` | Shift registers, link pins, selection/edge state | Deterministic external input and link edges |
| `state` | Explicit encoding and decoding | Validates complete candidate before replacing live state |
| `diagnostics` | Optional counters and bounded event history | Structured data; host formats, writes and uploads it |

Keep these as logical boundaries; do not create a generic plugin framework or one source file per register. Prefer explicit composition over mutually recursive component dispatch. Private headers can share hardware types without exposing the machine struct publicly.

## Timing contract

**Recommendation:** represent elapsed emulated time with `uint64_t` half-dot ticks, nominally 8,388,608 per second. This represents DMG/CGB normal and double speed with integer arithmetic. Unit names belong in fields and function names, never an ambiguous `cycles` argument.

| Unit | Normal speed | CGB double speed |
|---|---:|---:|
| PPU dot | 2 timeline ticks | 2 timeline ticks |
| CPU T-cycle | 2 timeline ticks | 1 timeline tick |
| CPU M-cycle | 8 timeline ticks / 4 T-cycles | 4 timeline ticks / 4 T-cycles |

The PPU keeps its dot rate when CPU speed changes. Timer/divider, serial and OAM DMA belong to the speed-sensitive side; audio timing and VRAM DMA require their own rules. Do not rescale the whole machine. [Clock definition](https://github.com/gbdev/pandocs/blob/master/src/Rendering.md), [CGB clock domains](https://github.com/gbdev/pandocs/blob/master/src/CGB_Registers.md).

Start with explicit CPU microsteps and fixed per-device deadlines. Advance to the earliest observable transition; use small stepping where needed for register accesses, rendering and collisions. A dynamic heap of allocated events is unnecessary for this fixed set of devices. Preserve the simple stepping path for diagnostic comparison if batching is later introduced.

Document when each register write becomes visible relative to sampling, reload, DMA and interrupt recognition. Use named intra-tick phases where needed. Determinism alone does not establish hardware correctness: a universal invented ordering such as “CPU, then PPU, then timer” is insufficient. Resolve collisions against model-specific tests and document remaining assumptions. Sub-T-cycle requirements discovered by hardware research may require finer internal phases without changing the host time unit.

All public execution has a maximum tick budget and a reason for returning: budget exhausted, frame available, audio/output backpressure, breakpoint, stopped machine, or error. HALT must continue active peripherals; STOP and invalid-opcode lock must remain bounded while applying their own clock behavior. An LCD-disabled program must never make `run_frame` hang. A frame helper wraps bounded execution, rather than being the only primitive.

## Hardware model and boot policy

Keep **physical model/revision**, **execution compatibility mode**, and **presentation palette/filter** separate. A DMG game running on a CGB is a CGB in compatibility mode; it does not become a physical DMG. Boot behavior and CGB palette selection depend on more than CPU register defaults. [Power-up sequence](https://github.com/gbdev/pandocs/blob/master/src/Power_Up_Sequence.md).

Recommended first targets: DMG-CPU-B, then CPU-CGB-E. These are deliberate coverage targets, not claims that all DMG/CGB units behave alike. Resolve model-specific boot values and conformance expectations during each target phase. Add MGB and other revisions only with named evidence; reserve later SGB/SGB2 support as distinct model work. GBA hardware and GBA software are outside this project scope. [Mooneye model taxonomy](https://github.com/Gekkio/mooneye-test-suite), [CGB APU revision evidence](https://github.com/LIJI32/SameSuite/blob/master/apu/README.md).

Provide an explicit deterministic post-boot profile first, with its limitations documented. Allow a caller-provided original boot ROM without shipping it. Later consider a pinned permissive replacement boot ROM as a separate artifact after license/build review. Never silently mix post-boot state, replacement boot, and original boot when reporting a result. SameBoy demonstrates replacement DMG/CGB boot ROMs and a reusable C core; its repository has directory-specific license exceptions that must be respected. [SameBoy](https://github.com/LIJI32/SameBoy), [license](https://github.com/LIJI32/SameBoy/blob/master/LICENSE).

## Public C API and ownership

Recommended contract, to refine against the first installed consumer:

- An opaque `gbb_t` owns all mutable machine state. Multiple instances share no mutable globals. Public names use a consistent prefix and an `extern "C"` guard for C++ consumers.
- Configuration uses a version/size field and explicit capability queries. Unknown models and unsupported mandatory options fail clearly. Defer permanent ABI promises until the API has a real consumer.
- Creation and cartridge load may allocate. Successful loading copies validated ROM bytes by default; the caller may release its input afterward. A borrowed immutable ROM mode can wait for a measured need and a precise lifetime contract.
- After setup, stepping, input submission within capacity, frame retrieval and audio draining allocate nothing. Size audio/event buffers at setup; capacity exhaustion returns a documented stop reason without silent data loss.
- A machine has one calling thread. Callbacks, if used, must not re-enter it. The host transfers immutable outputs to its UI/audio threads and owns synchronization.
- Stable error enums accompany caller-owned bounded error text. No hidden `errno`, process exit, global error buffer, stdout logging or retained caller stack pointers.
- Lifecycle distinguishes reset, cartridge replacement, destruction, battery import/export, and snapshot load. Failure leaves the previous valid machine intact where practical.
- Document every pointer lifetime, size unit, alignment requirement, nullability rule and invalid-argument result in the public header, and compile its small example as an installed consumer.

This is a product recommendation informed by the independent-core precedent in [SameBoy](https://github.com/LIJI32/SameBoy) and [Gambatte's library boundary](https://github.com/libretro/gambatte-libretro/blob/master/README.md). It does not reuse their API or code.

### Video, audio and input

Expose the native 160×144 frame with a fixed byte layout, stride, frame number, timestamp and borrowed-buffer lifetime. Use a specified RGBA byte order for the common integration path; retain raw shade/color output internally for conformance. Color correction, LCD persistence, shaders and integer scaling belong in the frontend. Pixel comparisons use canonical unfiltered output.

Keep APU channel state deterministic. Produce stereo PCM into a bounded core buffer at an explicit rate; start with fixed-point arithmetic and specified rounding for portable comparisons. Separate hardware transition tests from resampler/filter tests. Band-limited synthesis is a worthwhile audio milestone because naïvely sampling discontinuities aliases, but do not import a library merely because its name looks permissive. [Band-limited synthesis author documentation](https://slack.net/~ant/libs/audio.html).

Apply button changes at defined emulated timestamps. Hosts can sample once per slice initially; recordings store actual applied times, not host poll times. Model JOYP selection and interrupt edges; keep UI key mapping and opposite-direction policy explicit in the host.

The host owns pacing and device latency. Pacing follows emulated time/audio consumption with bounded queues, not a fixed 60 Hz assumption; the native frame period differs from 1/60 second. Seeking, pause/resume and load-state explicitly flush or regenerate host audio. [Frame timing](https://github.com/gbdev/pandocs/blob/master/src/Rendering.md).

## Cartridges, time and persistence

Implement ROM-only, MBC1, MBC2, MBC3+RTC and MBC5 as small mapper modules. Treat alternate wiring and cartridge capabilities as data validated at load; do not turn all mappers into MBC1 with different masks. Plan MBC1M/MBC30 separately, followed by MBC7 motion/EEPROM, HuC variants, camera and other demonstrated demand. [Mapper details](HARDWARE-AND-VALIDATION.md#cartridge-validation).

RTC has an explicit mode: deterministic elapsed emulated time for tests/replay, or host-supplied elapsed time events for real play. The frontend records a battery-save timestamp and applies an explicit catch-up delta on resume. Define backward-clock and overflow policy; do not call `time()` from mapper reads. Saving/restoring a replay snapshot never silently catches up to wall time.

Battery data and full snapshots are separate formats and user operations. Battery export includes RAM and an explicit RTC representation; the frontend chooses filenames, validates identity and writes atomically. Define interoperability with existing `.sav`/RTC layouts through a deliberate adapter, not a guess based on extension.

Native snapshots use fixed-endian fields, a version, lengths, model, boot identity and ROM identity. Include CPU phase, interrupt delay, divider/reload state, DMA progress, PPU FIFOs/fetcher/window, APU/resampling phase, link state, mapper/RTC state and queued deterministic events. No pointers, padding, native `bool` layout, host timestamps or struct dumps.

Decode to staging, validate bounds and invariants, then replace state. Reject mismatched ROM/model or unsupported required chunks before mutation. Never restore I/O by replaying generic register writes: doing so can trigger DMA or audio. Add BESS later for best-effort interchange, while retaining native snapshots for exact replay. [BESS design and restore caveats](https://github.com/LIJI32/SameBoy/blob/master/BESS.md).

## Portable and readable implementation rules

Use fixed-width unsigned integers for registers and defined wrapping; explicit widened intermediates for arithmetic and size calculations. Encode flag behavior in small named helpers with independent truth tables. Check `CHAR_BIT`, avoid signed shifts/overflow, unaligned typed loads, aliasing violations, compiler bitfields for hardware layouts, and union-based register endian assumptions.

Build on Clang, GCC and MSVC without compiler-specific dispatch as a requirement. Keep dependencies target-scoped in CMake, headers self-contained, and SDL optional. Use named hardware constants, concise comments explaining silicon behavior and a source/test link for surprising rules. Generated opcode data can be introduced only if its generator, checked output and independent tests reduce maintenance.

ROM headers and snapshot lengths are untrusted. Cap supported allocation sizes, validate multiplication/addition before allocation, distinguish malformed content from unsupported hardware, and fuzz loader/state paths plus bounded instruction execution. Header checksum/logo mismatches may be diagnostics for homebrew; they are not permission to read outside the supplied image.

## Tradeoffs and adversarial review

| Decision | Benefit | Cost / counterargument | Recommendation |
|---|---|---|---|
| Independent C core | Reusable, educational, predictable ownership | More integration contract work | Adopt; prove with a second consumer early |
| CPU bus phases + PPU state machine | Preserves ordering needed for real raster/DMA behavior | More code than instruction/frame stepping | Adopt from the first hardware slice; add features incrementally |
| Fixed deadlines before generic event queue | Low overhead, visible ordering | Special cases stay explicit | Adopt; profile before changing |
| One accurate behavior path | Fewer hidden test/play differences | Old devices may need optimization | Adopt; optimize equivalent batching before adding accuracy modes |
| Native snapshot before BESS | Reproducible rewind and regression evidence | Less immediate interchange | Adopt; version both independently |
| ROM copy on load | Safe default ownership | Additional ROM-sized memory | Adopt; optional borrowing only when justified |
| Single-threaded machine | Determinism and easy embedding | Host must coordinate outputs | Adopt; parallelize separate machines/tests |
| Optional bounded diagnostics | Useful failure traces without global logging | Instrumentation still needs measurement | Compile expensive tracing out by default; count drops |
| Early desktop player | Frequent usable releases and real integration evidence | Frontend maintenance | Keep narrow: open ROM, play, input, audio, save, errors |

## Progressive vertical slices

1. **Embeddable skeleton:** installed library consumer, bounded runner, validated tiny ROM fixture, deterministic identity/output, reproducible build and packaging path.
2. **DMG CPU execution:** executable test ROMs through bus/timer/interrupt/serial paths; latent-state snapshot skeleton; explicit HALT/STOP behavior and allocation baseline.
3. **Visible DMG play:** PPU state machine, joypad, ROM-only/MBC1, tiny licensed interactive fixture, headless screenshot result and thin macOS player in the same release.
4. **Audible persistent DMG play:** APU, battery saves, MBC2/MBC3 RTC/MBC5, native snapshots and repeatable replay; audio queue stress at the host boundary.
5. **CGB play:** named CGB profile, native color and DMG compatibility mode, speed switching, banked memory, VRAM DMA and model-specific validation.
6. **Accuracy and performance expansion:** selected chip revisions, advanced PPU/APU cases, link, BESS and additional cartridges with independent evidence and measured demand.

These are dependency suggestions for the parent roadmap, not authorization to advance through phases. **Stop after every phase** and present evidence and the next command. Release a useful artifact after each completed vertical slice where feasible.

## Future seams and unresolved decisions

Serial starts with correct disconnected and internal-clock behavior; a later link adapter synchronizes two instances to bit-edge deadlines. A byte-at-frame-boundary hook would obstruct accurate link timing. SGB commands, borders and timing need their own model scope; reserve the seam without exposing a fictional implemented capability. [Serial hardware](https://github.com/gbdev/pandocs/blob/master/src/Serial_Data_Transfer_(Link_Cable).md).

Before CPU/PPU implementation, settle bus-phase conventions against primary tests. Before CGB implementation, recheck speed-switch pause/interrupt interactions and hardware-specific DMA behavior. Before audio release, decide sample rate, resampler, filter approximation and output determinism envelope. Before state format stabilization, demonstrate save/load continuation across active DMA, timer reload and PPU fetch boundaries.

SameBoy is an independent behavioral comparator with permissive core licensing; mGBA offers another implementation and a useful explicit mapper-support taxonomy; Gambatte offers performance and core-separation precedent. Their agreement is evidence, not proof. mGBA's MPL-2.0 and Gambatte's GPL-2.0 code must not be copied into an MIT-only core. [mGBA](https://github.com/mgba-emu/mgba), [MPL license](https://github.com/mgba-emu/mgba/blob/master/LICENSE), [Gambatte license](https://github.com/libretro/gambatte-libretro/blob/master/COPYING).
