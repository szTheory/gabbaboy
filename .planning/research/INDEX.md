# GabbaBoy research index

Updated: 2026-10-08. Target: original C Game Boy / Game Boy Color core. These documents establish research and recommendations; they do not establish an implemented emulator.

## Start here

Read [SUMMARY.md](SUMMARY.md) for the integrated recommendation, six-phase initial DMG proposal, reconciled conflicts and open evidence gaps. [PROJECT.md](../PROJECT.md) defines product intent; [BRIEF.md](../context/BRIEF.md) preserves owner priorities; [WORKFLOW.md](../context/WORKFLOW.md) defines authorization and mandatory phase pauses. [DECISIONS.md](../context/DECISIONS.md) distinguishes adopted constraints from recommendations. [ROADMAP.md](../ROADMAP.md) is active milestone scope and [FUTURE-MILESTONES.md](../context/FUTURE-MILESTONES.md) is revisable direction; research proposals do not automatically add work.

## Route a question

| Question | Evidence document | Start with these primary sources |
|---|---|---|
| Which language, toolchain, library API and dependency boundaries? | [STACK.md](STACK.md) | [CMake presets](https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html), [CMake exports](https://cmake.org/cmake/help/latest/guide/importing-exporting/index.html), [SDL3](https://wiki.libsdl.org/SDL3/INTRO-cmake) |
| What should the first player deliver, and what waits? | [FEATURES.md](FEATURES.md), [SUMMARY.md](SUMMARY.md) | [SameBoy features](https://sameboy.github.io/features/), [SameBoy changes](https://sameboy.github.io/changelog/), [BGB](https://bgb.bircd.org/) |
| How should time, models, bus, device state and adapters fit? | [ARCHITECTURE.md](ARCHITECTURE.md) | [Pan Docs](https://github.com/gbdev/pandocs), [Gekkio reference](https://gekkio.fi/files/gb-docs/gbctr.pdf), [BESS](https://github.com/LIJI32/SameBoy/blob/master/BESS.md) |
| Which hardware rules, tests, model exclusions and fixture rights apply? | [HARDWARE-AND-VALIDATION.md](HARDWARE-AND-VALIDATION.md) | [Mooneye](https://github.com/Gekkio/mooneye-test-suite), [dmg-acid2](https://github.com/mattcurrie/dmg-acid2), [cgb-acid2](https://github.com/mattcurrie/cgb-acid2), [Mealybug](https://github.com/mattcurrie/mealybug-tearoom-tests), [SameSuite](https://github.com/LIJI32/SameSuite), [MagenTests](https://github.com/alloncm/MagenTests) |
| How should DMG audio, fixed PCM, resampling, and SDL playback be scoped? | [AUDIO-OUTPUT.md](AUDIO-OUTPUT.md) | [Pan Docs audio](https://gbdev.io/pandocs/Audio.html), [SDL3 audio streams](https://wiki.libsdl.org/SDL3/SDL_AudioStream), [Blip_Buffer author reference](https://www.slack.net/~ant/bl-synth/) |
| What failures must gates detect? | [PITFALLS.md](PITFALLS.md) | Hardware sources above; linked sibling review and source records in [PRECEDENT.md](PRECEDENT.md) |
| What actually works in siblings, and what was corrected? | [PRECEDENT.md](PRECEDENT.md) | Repository-relative source/review paths and observed revisions; distinguish source, recorded run, current dirty work and proposal |
| How do CI, release, safety, performance and adoption evidence work? | [QUALITY-AND-DELIVERY.md](QUALITY-AND-DELIVERY.md) | [ASan](https://clang.llvm.org/docs/AddressSanitizer.html), [UBSan](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html), [GitHub tokens](https://docs.github.com/en/actions/concepts/security/github_token), [required checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks), [Apple notarization](https://developer.apple.com/documentation/security/customizing-the-notarization-workflow) |

## Current phase evidence

- [Phase 1 planning research](../phases/GB-01-portable-foundation-and-original-rom-tracer/01-RESEARCH.md) narrows the initial fixture to the named DMG-CPU-B post-boot profile, records candidate opcode/tool/host-floor choices, and identifies what still needs implementation or hosted evidence. It is planning evidence only; it does not qualify an emulator or CI run.
- [Phase 2 planning research](../phases/GB-02-dmg-cpu-bus-and-time/02-RESEARCH.md) covers timed SM83 execution, CPU-visible mapping, timer/serial behavior and a pinned Mooneye candidate set. Mooneye fixture reproduction needs WLA-DX; ordinary tests will consume reviewed checked-in bytes. Gekkio revision 192 §12.1 documents undefined reads when no cartridge device responds, so no universal absent-RAM byte is qualified. Fixture admission and implementation evidence remain pending. [Validation contract](../phases/GB-02-dmg-cpu-bus-and-time/02-VALIDATION.md).
- Phase 2's selected Mooneye common font has separate author licensing; a root MIT notice does not establish rights for font-derived fixture bytes. The research records that closure and independently sourced timer expectations; [reviewed plans](../phases/GB-02-dmg-cpu-bus-and-time/02-PLAN-CHECK.md) assign admission and verification before any qualification claim.
- [Phase 3 planning research](../phases/GB-03-visible-interactive-dmg/03-RESEARCH.md) records the model-applicability boundary for PPU/DMA and JOYP behavior. Plan 03-09 adds exact-head macOS arm64 package and downloaded-byte evidence; see its [summary](../phases/GB-03-visible-interactive-dmg/03-09-SUMMARY.md) and [validation contract](../phases/GB-03-visible-interactive-dmg/03-VALIDATION.md). VIDEO-02 and VIDEO-03 remain open despite the package pass.
- [Phase 5 discussion context](../phases/GB-05-dmg-audio-and-stable-playback/05-CONTEXT.md) and [audio output research](AUDIO-OUTPUT.md) record the selected scoped DMG APU model, 48 kHz PCM contract, resampler/dependency decision, SDL callback/ring boundary, honest queue metrics, and hardware/perceptual evidence limits. These are planning decisions, not implemented playback or a physical DMG qualification.

## Evidence freshness and confidence

- The research set was inspected on **2026-10-02**. Web research confidence is **MEDIUM** under the installed research classifier. This records limitations of the evidence process, not popularity, market standing or automatic hardware correctness.
- Hardware-backed observation on an identified revision, test-author documentation, maintained hardware synthesis and differential emulator agreement are separate evidence classes. Issue reports establish reported symptoms; they do not establish frequency or a present defect.
- Moving URLs are discovery entry points. Before implementation or fixture ingestion, capture immutable revision, license/notice, build recipe/toolchain, digest, target model/boot path, oracle and expected result. A license at repository root does not automatically cover every asset/submodule/binary.
- Recheck GitHub/Apple policies and dependency pins during the phase that uses them. Revisit sibling current failures at milestone boundaries; retain their original inspected revision and dirty-worktree qualification.
- Every compatibility denominator identifies eligible fixture IDs, source/core revision and configuration. Pass, fail, unsupported, excluded, timeout and missing are distinct. No suite percentage represents all games; no fresh GabbaBoy compatibility/performance result exists yet.

## Corrections policy

When a contradiction matters, inspect the actual primary source or current failed evidence, record what changed and its scope, then update the relevant topic, SUMMARY and DECISIONS in the same change. Preserve the older claim's provenance with a supersession link. Do not silently regenerate goldens or treat an earlier completion receipt as current proof. Promote recommendations to verified behavior only with a linked local acceptance result for the exact revision; reopen them when a counterexample invalidates that scope.

Current corrections to retain: GlueyNeo CPU admission is pending after review; Nesturbator's synthetic seam is not real-console execution; Playstead's continuation result is blocked and its GBA fixtures cannot qualify GB; Blargg redistribution remains unresolved; Acid2 is limited composition evidence; CGB-C/D goldens do not automatically qualify CGB-E; current GitHub bot-PR approval and check-event rules supersede older blanket token assumptions. See the source-linked corrections in [SUMMARY.md](SUMMARY.md).

Keep exported lessons concise and public-safe. No private fixture bytes, saves, paths, credentials or personal machine metadata belong here. Initialization and each completed phase end at an explicit pause; neither a research link nor a future-scope entry authorizes advancing.
