# Feature Landscape

**Project:** GabbaBoy — original portable C17 Game Boy and Game Boy Color core
**Researched:** 2026-10-02
**Status:** Recommendations only; no emulator capability is implemented.
**Confidence:** MEDIUM, returned by OpenGSD `classify-confidence --provider websearch --verified`. Official capability lists establish advertised behavior; issue reports establish reported incidents, not independently reproduced defects or prevalence.

## Product Recommendation

Deliver a small downloadable DMG player and embeddable core that can load a supported cartridge, play with sound and responsive controls, preserve battery data, close, and resume safely. Make CGB the explicit next hardware milestone, with model and clock contracts present from the beginning. Do not describe the DMG release as completing GabbaBoy's GB/GBC scope.

Prioritize trustworthy saves, predictable timing, actionable failures, and a working consumer example. These are project priorities informed by the evidence below, not a claim that competitors lack them. Mature emulators already offer extensive debugging, visual customization, and peripherals; matching their entire menu would delay useful gameplay.

## Ecosystem Signals

| Project/source | Verified advertised behavior | Implication for GabbaBoy |
|---|---|---|
| [SameBoy features](https://sameboy.github.io/features/) | DMG/CGB models, battery saves, RTC, BESS states, open source boot ROMs, configurable controls, joypads, debugging, link and accessories | Use everyday playback/persistence as baseline; keep advanced hardware and tools as staged additions. Capabilities vary by frontend. |
| [BGB official site](https://bgb.bircd.org/) | Model distinctions, debugger/watchpoints, configurable gamepads, RTC data in `.sav`, quick states and rewind | Developers value inspectability; players expect portable progress and usable controls. Its speed/compatibility statements are vendor claims, not comparative measurements. |
| [mGBA upstream changes](https://github.com/mgba-emu/mgba/blob/master/CHANGES) | GB-specific changes include boot-model handling, MBC/RTC work, audio and video corrections | Evaluate its GB implementation specifically. GBA release headlines do not prove GB behavior. |
| [SameBoy API documentation](https://github.com/LIJI32/SameBoy/wiki/) | Documented library build and instance/run/model/input/audio APIs; wiki describes its documentation as work in progress | An installed, runnable integration example and explicit contracts are useful deliverables. Do not claim GabbaBoy uniquely enables embedding. |

These are qualitative comparisons of documented capabilities. No market-share, popularity, benchmark, or universal-compatibility ranking follows from them.

## Table Stakes

Complexity is relative engineering effort and regression surface, not a delivery estimate. Priority expresses the recommendation; all rows carry the evidence confidence above.

| Feature | Why expected | Complexity | Scope and dependencies |
|---|---|---|---|
| Bounded cartridge loading and clear support errors | A failed load must explain what the user can fix | Medium | First slice: declared ROM-only/MBC support, header/size checks, unchanged live instance on failure; reject unsupported hardware explicitly. |
| Coherent DMG execution with graphics and sound | Silent demos do not fulfill playable-emulator intent | High | CPU, interrupts, timers, memory, PPU, DMA, APU and disconnected serial behavior progress together through vertical fixtures. |
| Useful cartridge coverage | Software depends on banking and persistence | High | Recommend ROM-only and MBC1 early; complete declared MBC2/MBC3/MBC5 coverage during DMG milestone. RTC is part of supported MBC3 behavior. |
| Battery persistence with visible failures | Lost progress defeats otherwise good emulation | High | Separate battery bytes from runtime state; adapter handles safe replacement/backups, permissions, disk-full errors and periodic flushing. |
| Explicit RTC policy | Time-based software and reproducible runs have different needs | Medium–high | Core takes injected time/elapsed input; adapter selects wall-clock policy; document pause, restore, rollback and offline elapsed behavior. |
| Responsive keyboard and controller input | Basic player usability | Medium | Remapping, disconnect/reconnect, focus loss and pause rules; clear pressed inputs when device/focus is lost. |
| Stable presentation and audio pacing | Correct samples are insufficient if output stutters | High | Bounded audio queue and host pacing; pause/resume/device changes cannot produce runaway work or stale audio. |
| Basic display and playback controls | Players need readable output and predictable navigation | Low–medium | Integer scaling/aspect preservation, pause/resume/reset, volume/mute; avoid a large theme/filter system. |
| Downloadable player plus native C API example | Both players and integrators must reach a working session | Medium | Thin macOS adapter, packaged headers/library, installed C consumer and C++ inclusion/link check. |
| Model selection and honest compatibility notes | DMG and CGB are distinct targets | High | Preserve model identity from first API; CGB-only ROMs fail clearly until CGB milestone; support notes identify model/revision/corpus. |
| Portable versioned save states | Expected in mature desktop emulators | High | Add after full runtime state exists; include cartridge RAM, pending events and model identity; reject malformed/wrong-ROM states without mutation. |
| CGB execution and DMG-on-CGB policy | Explicit founding requirement | High | Named near-term milestone: color/banking/DMA/speed switching and model-specific behavior; not merely colorized DMG output. |

## Differentiators Worth Investing In

| Feature | Value | Complexity | Recommendation |
|---|---|---|---|
| Save recovery users can understand | Makes failures survivable and imports explainable | Medium | First release: visible save location, backup/recovery path and clear failure status. Stage third-party import after native safety works. |
| Reproducible bug evidence without private content | Developers can reproduce a bounded run without shipping game images | Medium | Capture opt-in model/version/settings, input/time events and output digests; redact paths and never upload automatically. |
| Small documented core with actual consumers | Reduces integration surprises | Medium | Public examples exercise lifecycle, errors, ownership, audio/video and persistence; keep host clocks/files/devices outside core. |
| Evidence attached to support claims | Lets users distinguish known limits from regressions | Medium | Publish corpus/model-qualified results and exclusions; separate hardware tests, oracle comparisons and private observations. |
| Focused diagnostics | Helps homebrew authors and core debugging | Medium–high | Start with bounded trace/error hooks; add stepping, breakpoints and viewers when real debugging needs justify them. |
| Save interoperability | Allows users to bring existing progress | High | Test named raw battery/RTC formats against permissioned fixtures. Consider BESS after native state semantics stabilize. |

## User Pain and Concrete Acceptance Implications

Reports below are evidence of experienced friction, not frequency rankings. A closed historical issue is not a claim about current releases. Adapter failures on Android motivate boundary tests, not a claim of the same macOS defect.

| Pain | Direct evidence and scope | GabbaBoy response |
|---|---|---|
| Saves disappear when instances or imports interact | [VBA-M discussion #1176](https://github.com/visualboyadvance-m/visualboyadvance-m/discussions/1176): user reports Crystal/Red save trouble after opening another instance; Crystal recovered from a state, Red was not recovered | Give each session explicit save ownership. Detect conflicting writers and back up before import; never equate successful ROM launch with valid persisted progress. |
| State restore excludes RAM used as working memory | [mGBA #3819](https://github.com/mgba-emu/mgba/issues/3819), opened 2026-07-13, libretro label: reporter identifies Polished Crystal failure with SRAM omitted from state restoration | Restore cartridge RAM as machine state. Treat whether to overwrite the on-disk battery file afterward as a separate, documented policy. |
| Correct filename/size does not ensure save portability | [TI-Boy CE #233](https://github.com/calc84maniac/tiboyce/issues/233), opened 2025-12-07: converted Crystal save reportedly rejected by multiple emulators despite expected size | Validate declared formats, retain originals and report uncertainty. Do not promise arbitrary `.sav` compatibility; this report does not identify which conversion step failed. |
| RTC/save format interoperability needs explicit work | [BGB feature documentation](https://bgb.bircd.org/) describes VBA-compatible RTC payloads; [mGBA save converter source](https://github.com/mgba-emu/mgba/blob/master/src/platform/qt/SaveConverter.cpp) distinguishes GB SRAM+RTC and packed/unpacked MBC2 variants | Document supported layouts and RTC policy; round-trip each advertised variant. Extension and byte count alone are not a universal format identifier. |
| Audio can become laggy or choppy | [SameBoy #180](https://github.com/LIJI32/SameBoy/issues/180), opened 2019-05-16, now closed: user reported a sudden audio regression, including after reboot | Measure queue underruns/overruns, cadence and resume behavior. The report establishes the symptom, not its root cause or present-day prevalence. |
| Controller reconnect can block saving or continuing | [RetroArch #15481](https://github.com/libretro/RetroArch/issues/15481), opened 2023-07-15: Android reporter names SameBoy among affected cores and mGBA as unaffected | Test disconnect/reconnect while running and paused; keep keyboard/menu recovery available. Treat this as a frontend integration seam. |
| Focus and reset behavior surprise users | [SameBoy changelog](https://sameboy.github.io/changelog/): 0.15.2 adds background-input policy; 1.0 fixes shortcuts affecting another ROM; 1.0.1 fixes paused SDL reset handling | Single-window first; define focus loss, reset and pause transitions; route shortcuts to the intended instance. |
| API failure or language boundaries can corrupt trust | [SameBoy changelog](https://sameboy.github.io/changelog/): 0.15.2 fixes possible C++ integration memory corruption; 1.0.2 corrects save-state success reporting on failure | Validate packaged C/C++ consumers and induced save errors; document return values and ownership, including failed operations. |
| Model timing evolves beyond instruction correctness | [BGB model documentation](https://bgb.bircd.org/) separates model timing; [SameBoy changelog](https://sameboy.github.io/changelog/) 1.0 records CGB timing/window refinements | Require explicit model tests and output evidence. CPU-suite success cannot stand in for graphics/audio or game compatibility. |

Additional confirmed upstream signals: SameBoy 0.16.5 corrected incompatible RAM-size state loading and a rewind path risking data loss; 0.16.6 fixed occasional Mac/iOS audio distortion; 1.0.3 increased battery-save frequency and added save-conflict handling. These fixes support testing lifecycle and persistence together. [Changelog](https://sameboy.github.io/changelog/).

## Anti-Features and Deferred Scope

| Feature | Why defer or avoid | Prefer |
|---|---|---|
| Universal accuracy or fastest-emulator claims | No bounded test/benchmark establishes either | Publish revision, model, workload, output and uncertainty with every measurement. |
| Accounts, cloud sync, mandatory telemetry, library scraping | Expands data handling and failure modes outside an embeddable core | Local files, optional bounded diagnostics and frontend-owned services. |
| Nintendo boot ROM/game bundles | Conflicts with repository distribution constraints | Documented post-boot initialization initially; permission-reviewed replacement boot code or user-supplied ROM support later. |
| Full debugger UI before playback | Large integration surface before useful core behavior | Test harness and focused traces first. |
| JIT, generic multi-console framework, speculative threading | Performance complexity without local evidence | Direct portable C and measured bottlenecks. |
| Rewind/runahead and speculative audio | Depend on complete deterministic state and rollback semantics | Native states, repeatable replay and correct battery policy first. |
| Link, SGB/SGB2, Camera, Printer and uncommon cartridge peripherals | Multiply clocks, input, state and host dependencies | Future milestones with specific fixtures; implement disconnected serial behavior early. |
| Web/mobile ports, shader catalogs, achievements and broad scripting | Divert resources from macOS playback and core integration | Keep adapter boundaries ready; add a port only with its own acceptance evidence. |
| Silent fallback for unsupported mappers/models | May appear playable while destroying correctness/progress | Explicit support errors and published limitations. |

## Feature Dependencies

```text
Model/time/API contract → bounded loading → integrated DMG execution
Integrated DMG execution → video + input + paced audio → playable adapter
Mapper RAM + persistence contract → safe battery save/reopen
MBC3 + injected clock → RTC persistence and interoperability
Complete runtime state → transactional native states → replay → rewind/runahead
DMG event ordering + model contract → CGB timing/banking/color/DMA
Independent instances + serial timing → local link → network/link accessories
Native API + installed consumer → Playstead integration → optional libretro adapter
```

## Coherent First Release and Milestone Ordering

1. **Foundation and executable consumer:** public lifecycle/error/time contracts, permissioned fixture, installed consumer, headless bounded run. This is a foundation release, not a playable emulator claim.
2. **First playable DMG slice:** a supported interactive fixture runs through the public API in the macOS player, with video, keyboard, sound and pause/reset. Start narrow cartridge coverage and state limitations plainly.
3. **Useful DMG release:** recommended common MBC coverage, battery/RTC safety, controller recovery, stable pacing, native states and packaged consumer verification. Demonstrate load → play → save → exit → reopen. An interrupted/failed persistence operation must not replace the last good save.
4. **Explicit next CGB milestone:** retain DMG evidence while adding the selected CGB profile and declared compatibility modes. Test speed transitions and state/reset identity; expand supported fixtures and consumer evidence.
5. **Later milestones:** named save interchange formats/BESS, richer developer tools, link/SGB/peripherals, then ports and latency features according to demonstrated demand.

Each step contains independently useful vertical evidence. Phase decomposition belongs to the roadmap; complete the authorized phase and stop before advancing. Initial research/setup stops before Phase 1.

## Gaps and Evidence Limits

- Exact mapper/revision release coverage needs fixture and hardware-research reconciliation; recommendations above are not compatibility promises.
- Native state version policy and the point to freeze compatibility require phase-specific design; preserving arbitrary old implementation snapshots is not automatically worthwhile.
- No representative user-frequency survey was performed. Reported symptoms guide regression scenarios, not popularity rankings.
- The parent-supplied Reddit RTC thread could not be retrieved in this run; no claim here depends on it.
- mGBA's website still advertises 0.10.5 while its issue tracker contains later milestone labels. No release-version inference is made from those labels.
- Boot replacement and fixture redistribution rights need per-asset review; an emulator's advertised open source boot ROM does not establish rights for every bundled asset.
