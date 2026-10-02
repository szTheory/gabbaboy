---
title: GabbaBoy pitfalls and prevention gates
project: GabbaBoy
researched: 2026-10-02
confidence: MEDIUM
status: research recommendations, not implemented behavior
---

# Domain pitfalls

**Domain:** portable C Game Boy / Game Boy Color emulation. Confidence is **MEDIUM**, using OpenGSD's `classify-confidence --provider websearch --verified` result. Hardware-specific references were checked by the parallel hardware researcher against upstream documentation on 2026-10-02; sibling source and verification records were inspected directly. Recommendations below are design inferences, not claims of existing GabbaBoy correctness.

The critical risk is convincing-looking success that proves the wrong thing: a green suite with no required cases, a restored file without resumed behavior, a correct final register value with incorrect bus timing, or an old receipt applied to changed code. [PRECEDENT.md](PRECEDENT.md) records the inspected sibling evidence and its limits. [HARDWARE-AND-VALIDATION.md](HARDWARE-AND-VALIDATION.md) provides the model, fixture-license and oracle details behind the hardware gates.

## Critical pitfalls

### F-01 — Implementing a different Game Boy model by accident

**What goes wrong:** generic “Game Boy compatible” claims combine DMG, CGB revisions, CGB compatibility mode and later hardware behaviors. A test can intentionally fail some physical revisions.

**Prevention:** an explicit selected hardware model/profile controls reset, registers, timer/APU/DMA quirks and test applicability. Record fixture model, revision, boot path and expected outcome. Do not count unsupported or inapplicable cases as passes. Begin with one named DMG model, then add a named CGB profile.

**Detection/gate:** conformance report partitions model-specific denominators; wrong-model controls cannot produce a passing qualification. Establish the profile contract in the foundation; expand it during CGB work.

**Sources:** [Mooneye test-suite model conventions](https://github.com/Gekkio/mooneye-test-suite), [SameSuite APU revision caveats](https://github.com/LIJI32/SameSuite/blob/master/apu/README.md), [Mealybug target models](https://github.com/mattcurrie/mealybug-tearoom-tests).

### F-02 — Correct instructions with incorrect event ordering

**What goes wrong:** running a whole instruction and adding its cycle count afterward misses timed accesses, interrupt sampling, timer edges, DMA contention and PPU register effects. CPU-only success does not establish machine timing.

**Prevention:** model bus operations and device advancement at the necessary hardware boundaries. Specify one time coordinate, ordering for simultaneous events, and clock-domain conversion. Keep traces of externally observable ordering for failing cases. Optimize only across intervals with no observable event.

**Detection/gate:** bus/event traces, partitioned execution equivalence, accesses immediately before/at/after edges and actual timing ROMs. A functional instruction-boundary CPU experiment in GlueyNeo explicitly disclaims pin timing; do not transfer its granularity as GB correctness.

**Sources:** [Pan Docs timer behavior](https://github.com/gbdev/pandocs/blob/master/src/Timer_Obscure_Behaviour.md), [rendering timing](https://github.com/gbdev/pandocs/blob/master/src/Rendering.md), [pixel FIFO](https://github.com/gbdev/pandocs/blob/master/src/pixel_fifo.md); GlueyNeo `experiments/owned_cpu/SUBSET.md` and `tests/owned_cpu/ORACLE.md` at `0d4f1e3` (2026-10-02).

### F-03 — Treating timers, HALT and interrupts as ordinary counters

**What goes wrong:** increment-on-period timer logic loses DIV/TAC edge effects and TIMA reload/write races. Immediate EI enable and a simple halted boolean miss delayed interrupt enabling and the HALT bug.

**Prevention:** encode the documented edge and pending-transition state explicitly. DIV reset can affect both TIMA and the APU frame sequencer. HALT, STOP, interrupt request and interrupt acceptance remain distinct state transitions.

**Detection/gate:** named edge and write-race cases, pending interrupts with IME disabled, EI boundary cases, wakeup versus interrupt service. Address with CPU/timer integration, before broad game claims.

**Sources:** [Timer obscure behavior](https://github.com/gbdev/pandocs/blob/master/src/Timer_Obscure_Behaviour.md), [HALT](https://github.com/gbdev/pandocs/blob/master/src/halt.md), [interrupts](https://github.com/gbdev/pandocs/blob/master/src/Interrupts.md), [APU details](https://github.com/gbdev/pandocs/blob/master/src/Audio_details.md).

### F-04 — Doubling the whole machine in CGB speed mode

**What goes wrong:** a blanket clock multiplier incorrectly speeds up PPU/APU or VRAM DMA; shared CPU/memory shortcuts miss OAM DMA bus differences between DMG and CGB.

**Prevention:** specify which devices follow CPU speed, preserve separate clock domains and model the speed-switch pause. Represent bus ownership/access restrictions explicitly. Keep documented uncertainties visible rather than inventing exact behavior.

**Detection/gate:** double-speed CPU/timer/serial and normal-rate video/audio checks; DMA from relevant source buses; switch transitions and serialization during pending work. Mandatory deeper research for CGB phase.

**Sources:** [CGB registers and speed switch](https://github.com/gbdev/pandocs/blob/master/src/CGB_Registers.md), [OAM DMA](https://github.com/gbdev/pandocs/blob/master/src/OAM_DMA_Transfer.md).

### F-05 — A good screenshot standing in for PPU timing

**What goes wrong:** fixed scanline durations and drawing from final register values pass visual composition tests but fail games that change registers during rendering. VRAM/OAM access restrictions and FIFO state disappear.

**Prevention:** first deliver a scoped rendering slice; then implement the timing behavior needed for the claimed accuracy level. Keep composition and timing suites distinct. Store pending fetch/FIFO/window/sprite state when snapshots become supported.

**Detection/gate:** mode transitions, variable mode 3 timing, midline writes, sprite/window interactions and model-specific image or trace oracles. Passing acid2 alone cannot qualify full PPU timing; its author describes intentionally limited requirements.

**Sources:** [Rendering](https://github.com/gbdev/pandocs/blob/master/src/Rendering.md), [pixel FIFO](https://github.com/gbdev/pandocs/blob/master/src/pixel_fifo.md), [dmg-acid2](https://github.com/mattcurrie/dmg-acid2), [cgb-acid2](https://github.com/mattcurrie/cgb-acid2), [Mealybug](https://github.com/mattcurrie/mealybug-tearoom-tests).

### F-06 — Host undefined behavior masquerading as hardware arithmetic

**What goes wrong:** signed overflow/shifts, integer promotions, invalid shift counts, unaligned casts and host byte order make legal guest behavior compiler-dependent. A small CPU diagnostic does not exercise the dangerous operand domain.

**Prevention:** unsigned fixed-width representations, reviewed promotion/shift rules, explicit byte decoding and checked host sizes. Separate guest wrapping from host resource overflow. Keep sanitizer coverage and boundary cases tied to real dispatch paths, not only duplicate helper calculations.

**Detection/gate:** ASan/UBSan on legal operand boundaries and malformed inputs, a release-optimization lane, and independent source review. Add these during CPU/loader implementation, before performance tuning. Avoid a universal ban on optimization or signed values; use them where behavior is proved.

**Evidence:** GlueyNeo `.planning/phases/01-cpu-acceptance-experiment/01-REVIEW.md` (2026-10-01) CR-01–06 documents reachable unsafe arithmetic and host generator defects after earlier passing receipts; [PRECEDENT.md](PRECEDENT.md), P-02.

### F-07 — Cartridge or state input escaping resource limits

**What goes wrong:** trusting header sizes/bank numbers, unchecked size arithmetic, unbounded allocations or execution, and partial state mutation on parse failure create crashes or corrupt sessions. A checksum validates neither structure nor trust.

**Prevention:** parse bytes with checked arithmetic and explicit limits; validate claimed versus available length, cartridge/controller support and bank mapping. Reject unsupported cases clearly. State loading decodes into validated temporary state and commits only after full validation; raw C struct dumps and pointers are forbidden as formats. Keep archive extraction outside the core.

**Detection/gate:** truncated, oversized, contradictory and unsupported headers; exact/one-over lengths; malformed state versions and sections; wrong ROM/model identity; allocation-failure injection; fuzz and corpus replay with bounded guest work. Start at the first cartridge loader and repeat for every new input format.

**Evidence:** GlueyNeo `01-REVIEW.md` host-tool defects and current explicit fault contract; Playstead treats fixture metadata, processes and output as untrusted with bounded schemas. These motivate GB controls without asserting identical parsers.

### F-08 — A save round trip that cannot resume

**What goes wrong:** raw memory dumps lose pointers, host handles, pending interrupts, divider phases, DMA progress, FIFO state, audio phase or RTC latch state. A save file copied back successfully says nothing about resumed gameplay.

**Prevention:** separate battery save, RTC, snapshot, replay and ABI versions. Serialize explicit fields with a stable byte order and model/content compatibility identity. Define quiescent capture boundaries or serialize all relevant in-flight work. Validate before mutating the live instance.

**Detection/gate:** save → destroy → fresh instance → load → compare subsequent observable behavior against uninterrupted execution, with multiple awkward capture points; malformed-load unchanged-state checks; two independent instances; a negative control that loses a required field must fail. Introduce at persistence/snapshot delivery, with architecture fields considered early.

**Evidence:** Playstead's original GBA `savetest.gba` resets its counter at boot and proves writes, not continuation; its current real-fixture continuation gate remains blocked. See [PRECEDENT.md](PRECEDENT.md), P-07/P-08.

### F-09 — Wall-clock time silently destroying RTC determinism

**What goes wrong:** reading host time inside the core makes replay, tests and save continuation vary by machine, clock adjustment and execution speed; conflating MBC3 live and latched clock values gives wrong reads.

**Prevention:** inject elapsed time or a documented RTC time service through the host contract. Preserve live/latched values, latch edge, halt and day carry. Define offline progression, clock rollback and persistence policy separately from fast-forward/pause behavior.

**Detection/gate:** fixed fake clock, latch transitions, halt/resume, day carry, long gaps and host-time rollback; deterministic replay records the external time input. Implement with MBC3, not as incidental frontend behavior.

**Source:** [Pan Docs MBC3](https://github.com/gbdev/pandocs/blob/master/src/MBC3.md). Host injection and rollback policy are GabbaBoy architecture recommendations inferred from determinism requirements.

### F-10 — Counting agreement as independent truth

**What goes wrong:** expected outputs copied from the implementation, two emulators with shared ancestry, or a hash updated after every change make a reassuring but circular oracle. Fixtures may also target another hardware revision.

**Prevention:** track oracle ancestry and exact source. Prefer hardware-observed, documented model-specific suites; use reference emulators as differential evidence with limitations. Keep goldens immutable unless a reviewed correction explains the changed behavior. Separate synthetic API, instruction, timing, visual, audio and game-compatibility evidence.

**Detection/gate:** targeted mutation of the result/cycle/continuation path must trigger the expected assertion; require named executed tests and nonzero denominators. A crash is not the successful detection of the intended semantic mutation.

**Evidence:** GlueyNeo `tests/owned_cpu/{ORACLE.md,negative_timing.py}`; ExifCleaner `scripts/{oracle_accountability_gate,nc_evidence_gate}.mjs` and CI wiring. Hardware scope comes from [Mooneye](https://github.com/Gekkio/mooneye-test-suite) and [SameSuite](https://github.com/LIJI32/SameSuite).

### F-11 — Green CI that skipped the required proof

**What goes wrong:** default CMake configuration registers zero tests; missing tools produce skips; release builds erase `assert`; Python optimization removes validator checks; dependent jobs skip after an earlier failure; report parsers read stale logs.

**Prevention:** supported presets contain required targets and explicit test inventory; validators use explicit failures; aggregate gate runs with `always()` and requires every expected lane to succeed. Keep pass, fail, skip, unsupported and blocked distinct. Compare required test identities with a fresh report and record current source/configuration.

**Detection/gate:** harness controls for zero tests, missing case, skipped case, wrong source, stale report and optimized builds. Establish alongside the first CI workflow and maintain when lanes change.

**Evidence:** GlueyNeo `d8c5450` fixed real CTest report parsing; Nesturbator `tests/check.h` uses active checks independent of `NDEBUG`; lattice_stripe `.github/workflows/ci.yml` explicitly checks all required results. [GitHub required status checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks).

### F-12 — Releasing a different artifact than the one tested

**What goes wrong:** stale PR checks qualify a new head; a release rebuild uses different inputs; package contents omit headers or carry workspace paths; signing/packaging is confused with runtime proof. A token-triggered event may never run the expected next workflow.

**Prevention:** check exact current PR/head and permitted event, build once, smoke the staged/downloaded artifact as a consumer, bind source/toolchain/dependency and artifact hashes, verify a complete draft's downloaded bytes, then publish. Keep privileged publisher execution separate from untrusted PR content.

**Detection/gate:** wrong SHA, absent/extra/empty asset, wrong checksum, missing license/header, stale run and install outside the checkout all fail. Prove bot PR → protected checks → merge → release lifecycle in this repository. Current cloud docs differ from older sibling assumptions: dispatch does not supply eligible protected PR checks, and some token-generated PR events require approval. [GitHub token behavior](https://docs.github.com/en/actions/concepts/security/github_token), [check eligibility](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks).

**Evidence:** ExifCleaner `.github/workflows/{ci,release}.yml` and `scripts/release_asset_gate.mjs`; lattice_stripe `scripts/maintainer/{release_candidate_check,release_evidence_check,published_hex_adopter_smoke}.sh`.

## Moderate pitfalls

| ID / failure | Prevention and detection | When addressed |
|---|---|---|
| F-13 Mutable globals break multiple instances or callbacks reenter a running instance | Own state per instance; declare callback lifetimes and reentrancy rules; audit static mutable caches; interleave and independently cold-start instances. A context pointer alone proves nothing. | Core lifecycle; every new subsystem; state work |
| F-14 Audio sounds plausible but sample clock drifts | Rational sample accounting with preserved remainder; deterministic emulated APU clock; separate host resampling/pacing; test long-run counts, channel triggers, DIV events and underruns. | Audio slice, then performance qualification |
| F-15 Public header works only inside the repository | Header-alone C/C++ builds; minimal-core build; external install consumer; explicit buffers, pitches, sample format, ownership and ABI/version policy; no private include leaks. | Foundation and each public API change |
| F-16 Hashes depend on host memory layout or display correction | Hash canonical bytes with specified endianness and no struct padding; keep native pixels separate from color response/shaders; distinguish emulation revision from presentation settings. | Runner/conformance foundation |
| F-17 Core-only consumers inherit frontend/test toolchains | Target-scoped CMake settings and optional targets; prove configure/build/install with adapters and tests disabled; do not enable C++ solely because header interoperability tests exist when tests are disabled. | Build foundation |
| F-18 Cache makes missing dependencies invisible | One cold path; correct toolchain/flag/dependency keys; validate generated inputs; never cache secrets or let privileged jobs execute untrusted cached code. Measure saved time against complexity. | CI setup and dependency changes |
| F-19 Performance ratchet measures noise or changes its workload | Fixed workload/model/build identities; host metadata and repeated measurements; allocation/work budgets in PRs, stable runner timing elsewhere. Review baseline changes separately. No unsupported p99.999 claims from small samples. | First real guest baseline and each optimization |
| F-20 “All games” lacks a denominator | Publish model/controller/feature matrix, corpus revision and measured outcomes; distinguish test-ROM accuracy, homebrew playability and private commercial compatibility. No correctness score from screenshots alone. | First compatibility report onward |
| F-21 Homebrew or available source treated as redistributable | Review exact code/assets/binary license and notices at immutable revision; public manifest; original GB fixtures where possible; private corpus stays private. MIT project licensing does not relicense imported content. | Before fixture/dependency ingestion |
| F-22 Debug evidence leaks private content | Construct allowlisted public receipts; retain private ROM/save paths, hashes and captures only in ignored local records when necessary; scrub source paths from archives/debug builds; keep `.env.local` ignored and CI credentials in secret stores. | Repository foundation and artifact publication |
| F-23 Repeated prerequisite questions churn completed setup | Keep discoverable local fixture aliases and supported scripts; consult current registry metadata/guidance before asking; do not read or publish private payload just to establish availability. | Private compatibility/testing integration |
| F-24 Test cleanup targets another process or destroys its profile early | Track exact launched child and owned temporary root; bounded process group cleanup; stop child before profile removal; abnormal cleanup is not proof of a clean save flush. | Headless/host integration and subprocess harness |
| F-25 A library change is called “additive” despite altering output semantics | Version ABI, persistence, snapshots and deterministic emulation behavior separately; document changed hashes/compatibility; provide a small migration example for consumers. | Public API foundation; every release |

These rows are transfer recommendations grounded in [PRECEDENT.md](PRECEDENT.md), especially P-03–P-14. Cache trust guidance is independently supported by [GitHub dependency caching](https://docs.github.com/en/actions/concepts/workflows-and-actions/dependency-caching). APU clock details are supported by [Pan Docs Audio details](https://github.com/gbdev/pandocs/blob/master/src/Audio_details.md).

## Minor pitfalls and avoidable maintenance cost

- **Copied stale defaults:** sibling preparation can say “no code yet” after code exists. Treat dated preparation as provenance, current code and failed evidence as current facts. Check installed CMake/compiler/action versions when implementing, not by copying a research-era pin.
- **Too much machinery before a playable slice:** a few meaningful contracts and negative controls suffice initially. Do not reproduce a mature Electron or Elixir pipeline, huge governance ledger or general telemetry platform.
- **Unreviewable generated code:** retain the generator, immutable inputs and reproduction recipe; make source-to-output changes reviewable. Prefer a small explicit implementation when it is easier to audit.
- **Timing hidden in clever helpers:** comments should explain why hardware does something, cite evidence and name model limits. Avoid macros or abstractions that hide ordering and integer conversions.
- **Workflow autonomy overruns phase pauses:** automate authorized verification, PRs and releases within the selected step, then stop at the user-requested GSD checkpoint. Initialization ends before Phase 1 begins.

## Phase-specific warnings

| Phase topic | Gate to establish | Deeper research? |
|---|---|---|
| Foundation / early distributable seam | Real install consumer, core isolation, explicit API/time/model contracts, active tests, provenance/hygiene, one truthful required CI gate | Standard C/CMake patterns; verify current platform and workflow behavior |
| DMG CPU / bus / timer / interrupts | Defined arithmetic, event ordering, HALT/EI and timer races, bounded runner, real diagnostic ROM | Yes: timing and model-specific oracle details |
| DMG PPU / DMA / input | Composition and timing suites separated; bus restrictions, midline writes and DMA interactions | Yes: FIFO/OAM quirks and hardware oracle limits |
| Audio / pacing | APU edge state, rational samples, stable host buffers; host pacing cannot alter emulated timing | Yes: APU quirks, filtering and audio comparison strategy |
| Cartridges / persistence | Controller mapping, bounded parser, battery round trip with resumed behavior; injected RTC | Yes for MBC3 and unusual cartridge variants |
| CGB | Explicit target revision, compatibility mode, clock domains, DMA/speed-switch and palette behavior | Mandatory |
| Snapshots / replay / link | Fresh-instance continuation with in-flight state; deterministic external input/time; independently clocked serial peers when link added | Mandatory |
| Release / optimization | Exact tested artifacts, downloaded consumer smoke, explicit actual compatibility matrix, reproducible benchmark subjects | Review current GitHub and host behavior; measure before expansion |

## Known limits of this research

Pan Docs and hardware test projects are high-signal public research, but they contain documented uncertainties and revision-specific results; do not flatten them into a universal specification. No new sibling tests, hardware measurements, ROM ingestion, live CI checks or releases were performed. Exact GB cycle constants and support decisions belong in the subsystem research and acceptance plans. This file identifies where proof is required and what misleading substitutes to reject.
