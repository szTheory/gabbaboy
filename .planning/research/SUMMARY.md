# Project Research Summary

**Project:** GabbaBoy
**Domain:** Original portable C Game Boy / Game Boy Color emulator and thin host adapters
**Researched:** 2026-10-02
**Confidence:** MEDIUM
**Status:** Initialization research; no emulator functionality, test pass rate or performance baseline exists.

## Executive Summary

GabbaBoy should deliver a readable, deterministic C core with a small macOS player and a documented native integration path for Playstead. Hardware behavior belongs to one instance-owned machine; files, clocks, devices and presentation belong to adapters. Build a timed SM83 interpreter, explicit bus arbitration and device transitions from Game Boy evidence. NES, Neo Geo and GBA sibling projects supply engineering lessons only. The first milestone should demonstrate useful DMG gameplay with sound and safe battery continuation, while the next named milestone delivers CGB. Completing DMG does not complete the project's GB/GBC goal.

Adopt C17, CMake 3.25 with Ninja/CTest, a standard-library-only core and optional SDL3 player. Start with an installed native consumer and a tiny original GB ROM executing a declared instruction subset through a bounded headless runner. Grow that same path into an interactive legal fixture, then battery persistence and audio. Limit first-release cartridge support to declared ROM-only and MBC1 variants; defer MBC2/MBC3/MBC5, RTC, snapshots and libretro until their acceptance work fits a later milestone. Reserve model, time and ownership seams now without pretending deferred capabilities exist.

The main risks are believable but invalid evidence, wrong event ordering, lost saves, unbounded untrusted input and release automation that qualifies different bytes. Require model/revision/boot-specific fixtures, explicit test inventories, independent expected outcomes, sanitizer/fuzz coverage and fresh-instance battery continuation. Bind release proof to the downloaded artifact and its source revision. Keep evidence tooling proportional to each slice. Initial setup stops before Phase 1; every later phase ends with evidence and a pause, with both automatic advance settings false.

## Key Findings

### Recommended Stack

[STACK.md](STACK.md) supplies the full contract and source list. These are recommendations to pin and exercise during implementation, not claims that the newest versions or all supported platforms were tested.

| Technology | Recommendation and reason |
|---|---|
| C17 | Original portable core, extensions disabled; explicit widths, endian helpers and ownership keep hardware logic understandable. |
| CMake 3.25 / preset schema 6, Ninja, CTest | Target-scoped build/install/export and repeatable developer commands; plain configure/build remains supported. |
| Standard C library | Core has no SDL, host filesystem, wall-clock, environment or network dependency. |
| SDL3, API floor 3.2 | Optional macOS player; choose a verified stable pin and deployment target when implementing it. |
| Clang/GCC/MSVC | Exercise claimed compiler/platform support; maintain ASan+UBSan and narrow bounded fuzz harnesses separately from release builds. |
| MIT for original code | Recommended permissive distribution; per-file, dependency and fixture terms remain separate. |

Static `GabbaBoy::core` and one opaque C instance are sufficient initially. Install/relocate the package and build external C and C++ consumers. Do not export private flags or frontend dependencies; do not promise stable ABI or snapshots before proving those contracts.

### Expected Features

[FEATURES.md](FEATURES.md) identifies a broader mature-product baseline. The synthesis deliberately narrows first-milestone scope.

**Must have for the initial limited DMG preview:** bounded supported-ROM loading; one named DMG profile; coherent CPU/timer/interrupt/PPU/DMA/joypad/APU behavior for the declared corpus; ROM-only and scoped MBC1; keyboard and basic controller input; pause/reset, scaling and volume; safe battery save/reopen with visible failure/recovery; paced audio; downloadable macOS player; installed native consumer and honest limitations. This is useful gameplay with limited declared support, not full DMG support. Unsupported mappers are rejected, never guessed.

**Should have as differentiators:** useful bounded traces, source-linked educational code, deterministic input replay, support reports with eligible denominators, reproducible public bug evidence and simple downstream examples. These should improve the usable core rather than grow into a separate observability or governance platform.

**Next milestone:** named CGB profile and native/compatibility modes, common mapper expansion with injected MBC3 RTC, transactional native states and concrete Playstead integration when its consumer contract is available. Sequence or split this milestone during its own planning; it is not automatic authorization. Consider libretro only after native integration and state semantics are established.

**Later:** BESS/interchange, richer debugging, other silicon revisions, link, SGB/SGB2, Camera/Printer/infrared and unusual cartridges, rewind/runahead and additional ports. GBA/NES/Neo Geo execution, proprietary bundles, mandatory telemetry and speculative JIT/frameworks remain outside scope.

### Architecture Approach

[ARCHITECTURE.md](ARCHITECTURE.md) recommends explicit CPU bus phases and a shared integer timeline, initially half-dot ticks with fixed device deadlines. This accommodates CGB clocks without imposing a generic event framework. Observable collision ordering must come from hardware evidence; a deterministic arbitrary ordering is insufficient. Preserve bounded progress even with LCD off, HALT, STOP, locked opcodes or full output buffers.

1. **Machine/API:** lifecycle, model, time budget, stop reasons, explicit output and pointer lifetimes; independent instances with externally serialized calls.
2. **CPU/bus/timer:** SM83 microsteps, interrupt state, timed accesses, divider/reload transitions and access initiators.
3. **PPU/DMA/APU/input/serial:** fetch and transfer state, digital sound and bounded samples, timestamped input and disconnected serial behavior.
4. **Cartridge/persistence:** validated mapping and RAM; battery bytes separated from later complete snapshots and RTC policy.
5. **Adapters/tooling:** SDL player, headless fixture runner, installed consumers and eventual Playstead/libretro; host owns files, atomic save replacement, clocks and device queues.

Target **DMG-CPU-B first and CPU-CGB-E next**, subject to phase evidence review. These are recommended physical profiles, not present support. Physical revision, compatibility mode and display treatment stay separate. Use a documented deterministic post-boot profile first; original/replacement boot execution is a separately identified future path.

### Critical Pitfalls

| Risk | Prevention and acceptance consequence |
|---|---|
| Wrong timing/model despite passing CPU or image tests | CPU bus phases, timer edges and dot-sensitive PPU structure from the first hardware work; separate composition, timing and revision-specific suites. Acid2 alone cannot qualify timing. |
| C undefined behavior or resource exhaustion | Defined arithmetic, checked sizes, transactional loaders, explicit unsupported errors, bounded guest work and diagnostics; sanitizers and meaningful boundary/fuzz cases. |
| Saves restore bytes but lose progress | Original GB fixture reads old battery state and visibly resumes; save, destroy, fresh instance, reload and compare behavior. Preserve the previous good file on write failure. |
| Circular or absent proof | Track oracle ancestry, named executed cases and nonzero eligible denominators. Missing required cases, timeouts and unexpected skips fail. Preserve corrections instead of rewriting goldens to match defects. |
| Wrong revision/artifact or unsafe automation | Current eligible PR checks, strict aggregate gate, trusted release build, downloaded-byte consumer smoke and source/hash agreement; privileged jobs never execute untrusted PR payloads. |

Full prevention gates: [PITFALLS.md](PITFALLS.md), [HARDWARE-AND-VALIDATION.md](HARDWARE-AND-VALIDATION.md), [QUALITY-AND-DELIVERY.md](QUALITY-AND-DELIVERY.md).

### Reconciled Recommendations and Current Corrections

- **Scope:** FEATURES and ARCHITECTURE recommend common MBCs and native states in useful DMG work. Preserve those goals but defer them beyond the smallest useful release. MBC1 battery continuation and real sound provide an achievable first end-to-end contract.
- **Frontend:** PRECEDENT's early libretro suggestion is a reusable-consumer lesson. STACK's native C API plus SDL player wins for this project; a libretro module would add a third adapter before it provides necessary evidence. Playstead's actual requirements must be checked before promising a drop-in module.
- **Sibling maturity:** GlueyNeo's current review reopens CPU acceptance after undefined-behavior findings; diagnostic passes do not establish a complete backend. Nesturbator implements an early test-card/API seam, not proven NES gameplay or its planned install/release system. Playstead's continuation ledger remains blocked; the corrected issue is the exact installed mGBA app's noninteractive loader, not missing Lua input controls. See dated revisions and dirty-worktree limits in [PRECEDENT.md](PRECEDENT.md).
- **Fixtures:** Playstead's private GBA fixture is neither a GB fixture nor public redistribution evidence. Its original GBA save test writes data but resets at boot and cannot prove continuation. Use an original GB program that distinguishes resumed state. Pin rights, source, build recipe and digest before admission; Blargg mirror rights remain unresolved. Acid2, Mealybug and SameSuite have distinct model and oracle limitations.
- **GitHub correction:** current documentation confirms approval-required runs for certain `GITHUB_TOKEN` PR events, while normal push recursion remains suppressed. Prefer a scoped App token for unattended bot PRs. Dispatch-created Actions job checks do not satisfy protected PR checks. This was rechecked during synthesis; prove the actual repository flow before claiming automation works. [Token documentation](https://docs.github.com/en/actions/concepts/security/github_token), [required-check documentation](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks).

## Implications for Roadmap

Recommend **six phases for a limited DMG preview milestone (0.x)**. Each is an independently evidenced increment, with its own pause. There is no v1 stable API/ABI promise. Phase numbers below are input to the roadmapper, not implementation authorization.

### Phase 1: Portable Foundation and Original ROM Tracer

**Rationale:** prove the public boundary and real guest execution before expanding hardware or delivery machinery.
**Delivers:** C17 core/build/install skeleton, opaque lifecycle/model/time/error contract, bounded ROM loader, tiny explicitly declared SM83 instruction subset and original ROM emitting a deterministic bounded trace through the real bus path; fixture source/license/hash manifest, installable headless runner artifact, external C/C++ consumer, basic sanitizer/required-test-inventory CI, remote/PR setup and a truthful foundation-preview artifact. The opcode subset derives from the fixture and rejects unsupported execution explicitly; no full CPU or gameplay claim.
**Addresses:** native API, bounded loading, diagnostics, legal fixtures and early delivery.
**Avoids:** F-06/F-07/F-10/F-11/F-15/F-17; a synthetic test card substituting for guest execution. No SDL or libretro requirement yet.

### Phase 2: DMG CPU, Bus and Time

**Rationale:** timing semantics must be dependable before graphics/audio depend on them.
**Delivers:** declared base/CB instruction behavior, interrupts/EI/HALT/STOP, divider/timer races, memory and disconnected serial, scoped post-boot profile; admitted model-specific diagnostics and bus traces; partitioned-run equivalence and bounded stopped execution.
**Addresses:** coherent DMG execution, model identity and actionable failures.
**Avoids:** F-01/F-02/F-03/F-06/F-10; instruction totals used as a substitute for timed accesses.

### Phase 3: Visible Interactive DMG

**Rationale:** integrate PPU/input and an actual consumer as soon as CPU/time can support them.
**Delivers:** dot-sensitive PPU state, OAM DMA/access restrictions, joypad, ROM-only interactive original/legal fixture, canonical image checks plus separate timing cases, optional SDL macOS preview with keyboard, scaling and pause/reset. Mark this interim preview as lacking completed audio/persistence.
**Addresses:** display, controls and thin player.
**Avoids:** F-05/F-13/F-16; a correct screenshot standing in for gameplay or raster fidelity.

### Phase 4: MBC1 and Safe Battery Continuation

**Rationale:** establish persistent progress while the supported cartridge set remains small.
**Delivers:** declared MBC1 ROM/RAM/battery mapping, bounded import/export and identity policy, adapter atomic save/backup/error handling, interrupted/failed-save protection and original fixture that resumes persisted progress in a new instance/process. Document concurrent-writer behavior and visible save recovery.
**Addresses:** useful cartridge coverage, trustworthy saves and recovery.
**Avoids:** F-07/F-08/F-21; restored bytes presented as resumed progress. RTC and full snapshots remain deferred.

### Phase 5: DMG Audio and Stable Playback

**Rationale:** complete the minimum useful playback loop using proven emulated time and persistence.
**Delivers:** scoped four-channel APU/digital timing, declared mixer/resampler policy, bounded PCM, SDL queue/pacing, input focus/controller recovery, pause/resume/device transition behavior and deterministic sample checks. Measure underruns, queue growth and sustained gameplay; document analog approximations.
**Addresses:** sound, responsive controls and stable presentation.
**Avoids:** F-14/F-19; changing emulated timing to follow a host device or calling dummy-device smoke perceptual validation.

### Phase 6: Qualified DMG Release and Consumer Handoff

**Rationale:** qualify the complete small product and exact artifacts after all required behaviors exist; release preparation starts in Phase 1 rather than waiting here.
**Delivers:** packaged macOS load/play/audio/save/exit/reopen smoke, relocated C/C++ consumer, supported-model/mapper/corpus ledger, fixed legal workload performance/memory baseline, security boundary regression coverage, source/artifact/license manifest, release notes and reproducible integration example for Playstead. Recheck its actual adapter contract; record any live-host gap rather than claim an integration pass from a standalone consumer.
**Addresses:** downloadable useful player, embedding, honest support and measured speed.
**Avoids:** F-11/F-12/F-19/F-20/F-22; exact-asset verification, current eligible required checks and no unsupported signing or tail-latency claim. Stop at milestone completion.

### Phase Ordering Rationale

The same original fixture and public API grow through guest execution, interactive video, persisted progress and audio. This keeps integration errors visible while hardware dependencies develop in order. Safety, packaging and nonempty CI begin with Phase 1 and expand when new boundaries appear. Full snapshots wait until in-flight device state exists; CGB remains the next explicit hardware milestone. Long-term peripherals depend on those foundations and retain separate evidence gates.

### Research Flags

- **Phase 1:** standard C/CMake install and CI patterns need no broad ecosystem research; a narrow timing/profile/fixture and current cloud-policy check is required before the tracer contract is fixed.
- **Phases 2 and 3:** use `$gsd-plan-phase --research-phase <N>` for SM83 bus timing, interrupt/timer races, PPU/DMA and exact model-applicable fixtures.
- **Phase 4:** focused MBC1 mapping, safe-save failure semantics and original continuation fixture design; no speculative RTC research required yet.
- **Phase 5:** deeper APU/resampling and SDL device-pacing research, including digital versus analog evidence limits.
- **Phase 6:** refresh current packaging/token/signing behavior and Playstead contract; use measured data for performance decisions. Standard package-consumer patterns can reuse Phase 1.
- **Next CGB/state milestone:** mandatory model/clock-domain/HDMA/speed-switch research, CGB-E applicable oracles, RTC and complete-state continuation design.

## Confidence Assessment

| Area | Confidence | Notes |
|---|---|---|
| Stack | MEDIUM | Primary tool docs support capabilities; exact pins, platform floors and consumers still need implementation evidence. |
| Features | MEDIUM | Owner priorities and upstream documented capabilities/issue reports; no prevalence study or measured GabbaBoy compatibility. |
| Architecture | MEDIUM | Hardware research and mature independent cores support boundaries; clock collision and analog/revision details remain unresolved. |
| Pitfalls | MEDIUM | Concrete sibling source/review evidence and hardware references; sibling runs were not repeated and some worktrees were changing. |

**Overall confidence:** MEDIUM. This tier records evidence limitations under the research workflow; neither site popularity nor agreement between emulators establishes hardware truth. No implementation verification occurred during synthesis.

### Gaps to Address

- **Phase 1:** exact DMG profile/post-boot values, tracer opcode subset and oracle, public time/output contracts, immutable fixture/tool pins, macOS floor and tested architectures.
- **Phase 3/4:** legal interactive fixture and separately meaningful persisted-progress behavior; MBC1 variant exclusions and save ownership/recovery policy.
- **Phase 5:** sample rate, resampler/filter license or original implementation, deterministic output envelope and device/perceptual validation limits.
- **Phase 6:** actual remote protections/App credentials, artifact retention/publication, signing availability, Playstead consumption contract and measured performance budgets.
- **Next milestone:** CGB-E versus CGB-C/D corpus coverage, undocumented clock/FIFO behavior, RTC interchange, snapshot compatibility and independent hardware evidence where sources disagree.

**Requirements handoff:** map each initial deliverable to one verifiable requirement and owner phase; maintain a separate deferred requirement list for CGB/mappers/RTC/states/Playstead integration. Avoid universal compatibility, fixed percentage speed goals, undefined “all tests,” and stable ABI promises. [DECISIONS.md](../context/DECISIONS.md) records adopted constraints versus provisional recommendations. The active ROADMAP should select scope from this proposal and the BRIEF; this synthesis is evidence, not an immutable plan.

## Sources

Research completed 2026-10-02. Detailed source sections retain additional URLs, revision observations and applicability. Primary-source status does not upgrade every derived claim to HIGH confidence.

- [STACK.md](STACK.md): [CMake presets](https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html), [SDL3 CMake](https://wiki.libsdl.org/SDL3/INTRO-cmake), [UBSan](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html) — build, ownership, host and safety contracts.
- [FEATURES.md](FEATURES.md): [SameBoy features](https://sameboy.github.io/features/), [changelog](https://sameboy.github.io/changelog/), [BGB](https://bgb.bircd.org/) — advertised capability and concrete historical failure signals, not rankings.
- [ARCHITECTURE.md](ARCHITECTURE.md), [HARDWARE-AND-VALIDATION.md](HARDWARE-AND-VALIDATION.md): [Pan Docs](https://github.com/gbdev/pandocs), [Gekkio technical reference](https://gekkio.fi/files/gb-docs/gbctr.pdf), [Mooneye](https://github.com/Gekkio/mooneye-test-suite), [SameSuite](https://github.com/LIJI32/SameSuite), [Mealybug](https://github.com/mattcurrie/mealybug-tearoom-tests) — hardware research and author-scoped test methodology.
- [PITFALLS.md](PITFALLS.md), [PRECEDENT.md](PRECEDENT.md) — dated local source and recorded verification from active siblings; no fresh hosted/hardware reproduction.
- [QUALITY-AND-DELIVERY.md](QUALITY-AND-DELIVERY.md): [GitHub token behavior](https://docs.github.com/en/actions/concepts/security/github_token), [required checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks), [Apple notarization](https://developer.apple.com/documentation/security/customizing-the-notarization-workflow) — changing platform rules; refresh at implementation.

*Ready for requirements and roadmap: yes. Initialization must stop before Phase 1.*
