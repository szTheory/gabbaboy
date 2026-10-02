# GabbaBoy research index

Updated: 2026-10-02. Target: original C Game Boy / Game Boy Color core. These documents establish research and recommendations; they do not establish an implemented emulator.

## Start here

Read [SUMMARY.md](SUMMARY.md) for the integrated recommendation, six-phase initial DMG proposal, reconciled conflicts and open evidence gaps. [PROJECT.md](../PROJECT.md) defines product intent; [BRIEF.md](../BRIEF.md) preserves owner priorities; [WORKFLOW.md](../WORKFLOW.md) defines authorization and mandatory phase pauses. [DECISIONS.md](../DECISIONS.md) distinguishes adopted constraints from recommendations. Once written, ROADMAP.md is active milestone scope and FUTURE-MILESTONES.md is revisable direction; research proposals do not automatically add work.

## Route a question

| Question | Evidence document | Start with these primary sources |
|---|---|---|
| Which language, toolchain, library API and dependency boundaries? | [STACK.md](STACK.md) | [CMake presets](https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html), [CMake exports](https://cmake.org/cmake/help/latest/guide/importing-exporting/index.html), [SDL3](https://wiki.libsdl.org/SDL3/INTRO-cmake) |
| What should the first player deliver, and what waits? | [FEATURES.md](FEATURES.md), [SUMMARY.md](SUMMARY.md) | [SameBoy features](https://sameboy.github.io/features/), [SameBoy changes](https://sameboy.github.io/changelog/), [BGB](https://bgb.bircd.org/) |
| How should time, models, bus, device state and adapters fit? | [ARCHITECTURE.md](ARCHITECTURE.md) | [Pan Docs](https://github.com/gbdev/pandocs), [Gekkio reference](https://gekkio.fi/files/gb-docs/gbctr.pdf), [BESS](https://github.com/LIJI32/SameBoy/blob/master/BESS.md) |
| Which hardware rules, tests, model exclusions and fixture rights apply? | [HARDWARE-AND-VALIDATION.md](HARDWARE-AND-VALIDATION.md) | [Mooneye](https://github.com/Gekkio/mooneye-test-suite), [dmg-acid2](https://github.com/mattcurrie/dmg-acid2), [cgb-acid2](https://github.com/mattcurrie/cgb-acid2), [Mealybug](https://github.com/mattcurrie/mealybug-tearoom-tests), [SameSuite](https://github.com/LIJI32/SameSuite), [MagenTests](https://github.com/alloncm/MagenTests) |
| What failures must gates detect? | [PITFALLS.md](PITFALLS.md) | Hardware sources above; linked sibling review and source records in [PRECEDENT.md](PRECEDENT.md) |
| What actually works in siblings, and what was corrected? | [PRECEDENT.md](PRECEDENT.md) | Repository-relative source/review paths and observed revisions; distinguish source, recorded run, current dirty work and proposal |
| How do CI, release, safety, performance and adoption evidence work? | [QUALITY-AND-DELIVERY.md](QUALITY-AND-DELIVERY.md) | [ASan](https://clang.llvm.org/docs/AddressSanitizer.html), [UBSan](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html), [GitHub tokens](https://docs.github.com/en/actions/concepts/security/github_token), [required checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks), [Apple notarization](https://developer.apple.com/documentation/security/customizing-the-notarization-workflow) |

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
