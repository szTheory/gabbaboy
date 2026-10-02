# GabbaBoy hardware and validation evidence

Researched/retrieved: **2026-10-02**. Scope: DMG and CGB; no NES, Neo Geo or GBA emulation.
Confidence: **MEDIUM** for verified web findings, from OpenGSD `query classify-confidence --provider websearch --verified`. Recommendations are explicitly distinguished from source assertions. Unresolved behavior is listed at the end.
Read with [ARCHITECTURE.md](ARCHITECTURE.md), which defines the recommended implementation boundaries.

## Evidence policy

Prioritize a reproducible test on identified hardware, then test-author documentation, then maintained hardware references, then independent emulator agreement. Pan Docs is a maintained community synthesis, not a Nintendo specification; its uncertainty notes matter. Gekkio's technical reference is primary reverse-engineering work and explicitly emphasizes pre-CGB hardware. The fetched PDF identifies revision 192, dated 2026-08-16. [Pan Docs repository](https://github.com/gbdev/pandocs), [Gekkio reference](https://gekkio.fi/files/gb-docs/gbctr.pdf).

For every non-obvious implementation rule, retain source URL/section, retrieval date, target hardware, confidence, minimal regression case and any disagreement. A passing emulator comparator must never overwrite a hardware-backed expectation automatically. Archive an immutable source revision when converting this research into an implementation dependency; the moving branch URLs below are discovery references, not reproducibility pins.

## Hardware requirements and validation gates

| Area | Hardware fact / implementation trap | Required gate before claiming support |
|---|---|---|
| CPU identity | SM83 has its own opcode/flag behavior; a generic Z80 core is not a substitute | Complete base/CB behavior, flags, taken/untaken timing and bus accesses; undefined opcode lock behavior |
| Interrupts | IME, IE and IF differ; EI takes effect after the following instruction | EI/DI/RETI, priority, entry timing and pending interrupt tests |
| HALT/STOP | HALT wakeup can occur with IME off; pending enabled requests can trigger the HALT bug; STOP has distinct model/speed behavior | Focused instruction sequences plus bounded execution when no frame can arrive |
| Divider/timer | DIV/TAC writes affect edges; TIMA reload and interrupt request are delayed after overflow | Tests across write/reload boundaries; distinguish DMG/CGB TAC behavior |
| Audio | DIV edges sequence APU; channel triggers, length and sweep have latent state | Digital output/register checks, then mixer/resampler checks independently |
| PPU | Mode 3 varies with fetch stalls; raster writes happen during rendering | Render fixtures followed by mode-3 timing fixtures and access restriction tests |
| OAM DMA | Transfer progress consumes time and affects CPU/PPU access; CGB has different bus conflicts | Start/restart/end boundaries, read/write restrictions and double-speed duration |
| CGB | Native/compatibility mode and physical revision differ; CPU double speed does not double all clocks | Model-scoped speed, banking, priority, DMA and APU suites |

Evidence: [SM83 instruction set](https://github.com/gbdev/pandocs/blob/master/src/CPU_Instruction_Set.md), [interrupts](https://github.com/gbdev/pandocs/blob/master/src/Interrupts.md), [HALT](https://github.com/gbdev/pandocs/blob/master/src/halt.md), [STOP](https://github.com/gbdev/pandocs/blob/master/src/Reducing_Power_Consumption.md), [timer](https://github.com/gbdev/pandocs/blob/master/src/Timer_Obscure_Behaviour.md), [audio](https://github.com/gbdev/pandocs/blob/master/src/Audio_details.md), [PPU](https://github.com/gbdev/pandocs/blob/master/src/pixel_fifo.md), [OAM DMA](https://github.com/gbdev/pandocs/blob/master/src/OAM_DMA_Transfer.md), [CGB](https://github.com/gbdev/pandocs/blob/master/src/CGB_Registers.md).

### Clock and timer rules to preserve

Use explicit T-cycle, M-cycle and PPU-dot terminology. One M-cycle comprises four CPU T-cycles. CGB double speed halves CPU T-cycle duration in physical time while PPU dots remain unchanged. APU sequencing follows falling edges of visible DIV bit 4, or bit 5 in double speed, preserving the nominal 512 Hz sequence rate. A DIV reset can trigger an early edge. [Clock relationship](https://github.com/gbdev/pandocs/blob/master/src/Rendering.md), [APU divider](https://github.com/gbdev/pandocs/blob/master/src/Audio_details.md).

TIMA overflow exposes zero before the subsequent M-cycle reload/IF request. TIMA writes can cancel pending reload, while writes during reload behave differently; TMA writes can alter the reloaded value. Use a state transition model rather than independent countdowns. Some CGB TAC-enable behavior varies between individual consoles; one universal result would overstate certainty. [Timer circuit and races](https://github.com/gbdev/pandocs/blob/master/src/Timer_Obscure_Behaviour.md).

### PPU and DMA rules to preserve

Keep fetcher progress and separate background/object FIFO metadata; sample registers at the correct stage, retain window internal position, and distinguish DMG/CGB priority. OAM/VRAM access restrictions belong in bus arbitration, including side effects from DMA. Dot-level structure is recommended now even if the first visible release covers only straightforward scenes. [Pixel FIFO](https://github.com/gbdev/pandocs/blob/master/src/pixel_fifo.md).

OAM DMA occupies 160 M-cycles, corresponding to 640 normal-speed or 320 double-speed dots for the transfer. Model startup/restart details separately. DMG limits CPU access during DMA; CGB cartridge and WRAM buses allow source-dependent access. CGB general VRAM DMA and HBlank DMA also stop CPU execution during transfers; cancellation and HALT interaction need explicit tests. [OAM DMA](https://github.com/gbdev/pandocs/blob/master/src/OAM_DMA_Transfer.md), [CGB DMA](https://github.com/gbdev/pandocs/blob/master/src/CGB_Registers.md), [author's HDMA test](https://github.com/alloncm/MagenTests).

### Cartridge validation

| Controller | Essential behavior | Focused boundary cases |
|---|---|---|
| ROM-only | Fixed ROM, optional declared RAM | Truncated image, unsupported size, absent RAM |
| MBC1 | Coupled bank registers and mode-dependent mapping | Bank-zero remapping, lower-region mapping, RAM enable, disconnected address lines; MBC1M tracked separately |
| MBC2 | 512×4-bit internal RAM and address-bit-8 register decode | RAM mirrors, nibble writes, bank-zero mapping; document chosen upper-read-bit behavior |
| MBC3 | ROM/RAM selection, separate live/latched RTC | 00→01 latch transition, halt, day carry, RTC register selection, resume catch-up |
| MBC5 | Nine-bit ROM bank, valid bank zero, RAM/rumble variants | Highest bank, absent address lines, rumble bit separation |

Sources: [MBC1](https://github.com/gbdev/pandocs/blob/master/src/MBC1.md), [MBC2](https://github.com/gbdev/pandocs/blob/master/src/MBC2.md), [MBC3/MBC30](https://github.com/gbdev/pandocs/blob/master/src/MBC3.md), [MBC5](https://github.com/gbdev/pandocs/blob/master/src/MBC5.md). In particular, Pan Docs labels MBC2 upper RAM-read bits undefined; do not generalize a convenient value into a proven property of every chip.

Recommendation: expose unsupported cartridge types clearly, and expand by named mapper/capability. MBC7 needs EEPROM protocol and sensor state, not only bank switching. Camera, infrared, HuC, MMM01 and unusual multicarts need distinct research and fixtures. A mature emulator still distinguishes partial controller support: mirror that honesty. [MBC7](https://github.com/gbdev/pandocs/blob/master/src/MBC7.md), [mGBA mapper support table](https://github.com/mgba-emu/mgba/blob/master/README.md).

## Test corpus admission and licenses

License status below records inspected upstream files, not a blanket grant for every dependency, submodule or binary found elsewhere. Before vendoring a fixture, pin its source commit, compiler/assembler if rebuilt, ROM hash, notices, assets and submodule provenance. Public availability alone is insufficient.

| Corpus | Verified license evidence | Best use | Limitation / admission decision |
|---|---|---|---|
| Mooneye Test Suite | [MIT LICENSE](https://github.com/Gekkio/mooneye-test-suite/blob/main/LICENSE) | CPU, timer, interrupt, DMA and model behavior | Admit selected acceptance tests; suffixes scope expected hardware; emulator-only/manual/madness are separate tracks |
| dmg-acid2 | [MIT LICENSE](https://github.com/mattcurrie/dmg-acid2/blob/master/LICENSE) | DMG and CGB compatibility-mode rendering smoke | Separate reference images; explicitly not a mode-3 timing test |
| cgb-acid2 | [MIT LICENSE](https://github.com/mattcurrie/cgb-acid2/blob/master/LICENSE) | CGB color/priority rendering smoke | Does not require double speed or WRAM banking; cannot prove those features |
| Mealybug Tearoom | [MIT LICENSE](https://github.com/mattcurrie/mealybug-tearoom-tests/blob/master/LICENSE) | Mode-3 raster writes and fetch timing | Expected images for named DMG/CGB-C/CGB-D hardware; target-specific goldens required |
| SameSuite | [Author LICENSE](https://github.com/LIJI32/SameSuite/blob/master/LICENSE), titled X11 with permissive text | CGB APU and additional obscure behavior | Inspect each sub-suite; hardware revisions intentionally have different pass sets |
| MagenTests | [MIT LICENSE](https://raw.githubusercontent.com/alloncm/MagenTests/HEAD/LICENSE) | CGB priority, VRAM DMA/HALT, register and mapper cases | Inspect individual oracle provenance; some expected images come from an emulator |
| Blargg Game Boy tests via retrio mirror | [Mirror](https://github.com/retrio/gb-test-roms); inspected selected author readmes and tree | CPU/memory/sound diagnostics once rights resolved | No top-level license found; selected readmes do not establish distribution rights. Keep automatic vendoring blocked pending per-file/source review |

Mooneye methodology and hardware lists are documented by its author. Mealybug supplies emulator-produced expected images alongside real-device photos, so its goldens are useful evidence but are not direct digital hardware captures. [Mooneye author README](https://github.com/Gekkio/mooneye-test-suite), [Mealybug author README](https://github.com/mattcurrie/mealybug-tearoom-tests).

Do not infer Blargg test-ROM rights from the separate LGPL sound libraries. Downloading an unresolved corpus during CI is not a substitute for resolving rights. Start required CI with the clearly admitted suites and GabbaBoy-owned minimal fixtures; optional local diagnostics must retain provenance and policy.

## Machine-readable pass protocols

**Mooneye:** in an explicitly selected test fixture, recognize `LD B,B` with B/C/D/E/H/L = 3/5/8/13/21/34 as success, or six 0x42 values as failure; serial output provides the corresponding protocol. A random `LD B,B` in a commercial game must have ordinary CPU semantics. Do not patch LY/SC into a fake-success environment for whole-machine conformance. [Author protocol](https://github.com/Gekkio/mooneye-test-suite#passfail-reporting).

**Acid2:** compare canonical output pixels against the reference for the specified hardware/mode. DMG uses the documented grayscale values; CGB 5-bit components expand with `(x << 3) | (x >> 2)`. Disable presentation filters. A line renderer can pass these tests, which makes them an early visual gate only. [DMG protocol](https://github.com/mattcurrie/dmg-acid2), [CGB protocol](https://github.com/mattcurrie/cgb-acid2).

**Mealybug:** capture on its software breakpoint and compare against the correct named model's expected image with zero differing canonical pixels. Save a difference image on failure. CGB-C/D expectations cannot automatically gate the recommended CGB-E target. [Author automation instructions](https://github.com/mattcurrie/mealybug-tearoom-tests#usage).

**Blargg, after admission:** protocol varies by suite. The sound-test documentation specifies signature DE B0 61 at A001–A003, status at A000 (80 running; terminal result code), and text at A004. CPU-instruction tests also describe serial text via SB/SC. Implement adapters by fixture, never a universal heuristic that treats “printed something” as passing. [Sound protocol](https://github.com/retrio/gb-test-roms/blob/master/dmg_sound/readme.txt), [CPU protocol](https://github.com/retrio/gb-test-roms/blob/master/cpu_instrs/readme.txt).

Every runner result needs a finite emulated-tick budget and a host watchdog. Distinguish `pass`, `fail`, `timeout`, `unsupported-model`, `missing-fixture`, `invalid-fixture` and `expected-failure`. Required fixtures that disappear fail CI. Expected failures need an issue, rationale and review date; a new unexpected pass prompts review instead of being ignored.

## Reproducible compatibility record

Recommended fixture/result manifest fields:

```text
fixture id; source URL + immutable revision; ROM SHA-256; license + notice path
assembler/build recipe or binary origin; model + SoC revision; boot mode + identity
required mapper/peripherals; input/RTC seed or event log; timeout in emulated ticks
oracle type + protocol; expected image/trace hash + provenance; expected status
core revision; compiler/build flags; runner version; observed result + artifacts
```

Generate a compatibility page from this manifest. Report passed/failed/unsupported counts with the eligible denominator and corpus revision. A test suite percentage is never a percentage of all retail games. Separately track boots, reaches gameplay, saves, audio, graphics, link and known game-specific issues. User-owned cartridge dumps stay outside repository and public CI; avoid publishing private paths or accidentally attaching dumps to failure bundles.

## Shift verification left

| Layer | Automated proof | Suitable cadence |
|---|---|---|
| Small unit checks | Exhaustive feasible ALU/flag inputs, bus decode edges, timer transitions, mapper masks | Every PR |
| Properties | Same event stream is independent of run chunking; snapshot continuation equivalence; reset determinism | Every PR with fixed seeds; broader scheduled seeds |
| ROM acceptance | Model-scoped admitted hardware tests with exact protocols | Focused required subset per PR; larger corpus scheduled |
| Integration | Installed C consumer, thin player output path, battery save/reload, error reporting | Every relevant PR |
| Fuzzing | ROM parser, mapper/state imports, truncated/malformed lengths, bounded execution | Sanitized PR smoke plus scheduled campaigns; retain minimized regressions |
| Differential | Compare traces with pinned independent cores, investigate disagreements | Targeted debugging and scheduled discovery |
| Real hardware | Resolve genuinely unknown behavior using minimized ROM and identified chip | Only when existing evidence cannot decide; preserve results afterward |

Use independently derived expected flag tables; a property that restates the implementation does not validate it. Snapshot testing must cross active DMA, TIMA reload, HALT/interrupt transitions, window/fetch state and audio phases. Full device behavior remains active in whole-machine tests, including when graphics or audio output is discarded.

For SameSuite APU tests, CGB-E has a different documented pass set from CGB-C/D, and pre-CGB devices lack the PCM registers used by most cases. A blanket “all tests on all models” gate would demand incorrect behavior. [Author hardware outcomes](https://github.com/LIJI32/SameSuite/blob/master/apu/README.md).

## Performance, diagnostics and baselines

Recommendation: benchmark a fixed mix of CPU-heavy, sprite/window-heavy, audio-heavy, mapper/RTC and CGB double-speed workloads. Record emulated seconds per wall second, core frame/slice latency distribution, allocation counts, peak memory, save/load latency and binary size. Measure host audio underruns and queue latency separately; throughput alone can hide poor playability.

Establish reproducible Release-build baselines on identified hardware with warm-up, compiler flags, corpus hashes and repeated runs. Separate core throughput from graphical vsync/audio waits. Use CI trends and generous budgets on shared runners; hard small-percentage regressions require a stable runner and noise evidence. Performance improvements must preserve the same model, features and correctness corpus.

The requested p99.999 bar needs enough observations and a useful failure definition. Ten million observations contain only about 100 samples in the upper 0.001%, before accounting for correlation; short CI runs cannot substantiate five-nines latency. Begin with median/p95/p99, maximum, sustained headroom and zero known audio starvation under a declared load; add long soak runs when they change decisions.

Default diagnostics are per-instance, opt-in and bounded: cycle/phase, bus initiator/address, interrupts, frame/audio counts and stop reasons. A trace ring records dropped-event counts. Format and persist on the host after a failure. Measure disabled tracing overhead; avoid per-instruction allocation, string formatting or network telemetry.

## Known uncertainties and phase research obligations

- **CGB speed switch:** Pan Docs has detailed pause behavior and open interrupt questions. Recheck against targeted hardware evidence before claiming precise STOP fidelity.
- **Pixel FIFO:** source text explicitly marks some sprite-penalty ordering unconfirmed; use model-specific tests instead of treating prose as a complete circuit specification.
- **Revision coverage:** the recommended CGB-E target does not have an automatic right to CGB-C/D screenshot goldens. Acquire evidence or keep those tests unsupported for that target.
- **Analog audio:** DAC fades/filter differences are partly model- and device-dependent. Document approximation and separate deterministic digital correctness from analog fidelity.
- **Boot state:** full original boot execution, replacement boot execution and synthesized post-boot state can differ. Pin and report the mode; research CGB compatibility palettes separately.
- **Corpus rights:** Blargg admission and each suite's submodules/assets require completion before distribution; root license badges alone do not close that work.
- **Reference emulator currency:** the original Gambatte repository currently says the project was taken private; use the named public libretro fork as the reproducible comparator. Do not describe the private original as a maintained public dependency. [Original README](https://github.com/sinamas/gambatte), [public fork](https://github.com/libretro/gambatte-libretro).

This research initializes the evidence backlog. No hardware behavior has been implemented or validated in GabbaBoy yet, no corpus binaries have been vendored, and no compatibility/performance baseline has been earned. Complete project initialization, then stop before Phase 1 as requested.
