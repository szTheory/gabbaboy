# Phase 6: Qualified DMG Release and Consumer Handoff - Context

**Gathered:** 2026-10-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 6 qualifies the existing limited DMG-CPU-B software model for adoption. It delivers relocatable C/C++ core packages and a reproducible native consumer example; a legally sourced, automatically smoke-tested macOS player package; exact-byte release provenance and honest trust status; current consumer, support, upgrade, and troubleshooting documentation; scoped compatibility and reproducible performance evidence; bounded fuzz and boundary regression; and fail-closed repository release automation.

The active scope is the existing bootless DMG-CPU-B profile, ROM-only cartridges and the documented standard MBC1 subset, plus the current macOS SDL3 player. This is a qualification and handoff phase, not a hardware qualification or expansion to CGB, additional mappers, a stable ABI, or universal game compatibility. “DMG” means the Game Boy DMG model here; the existing macOS CLI package is a tar archive, not a disk-image installer.

</domain>

<decisions>
## Implementation Decisions

### Version, release identity, and macOS trust
- Use the existing CMake project version (`0.1.0` at discussion time) as the product version source and use matching `v<version>` tags. Keep generated release metadata tied to that version, exact source commit, build/toolchain identity, fixture/corpus revision, and artifact SHA-256.
- Publish one durable GitHub Release with platform assets, SHA-256 manifest, notices, release notes, and a concise support/limitations sidecar. Temporary Actions artifacts remain preview evidence, not product releases.
- Prefer GitHub immutable releases and artifact attestations where enabled and verifiable. Create a draft candidate, build once from the clean, trusted exact tag, attach the resulting assets, download and smoke those exact bytes, and publish only after every required gate passes. Never rebuild after the bytes have been qualified.
- Use release-please manifest mode for the version/release PR flow, pinned to a full action commit SHA. It is one narrowly scoped workflow dependency; do not add release/build dependencies to the C core or expand the runtime dependency tree. A scoped GitHub App token is preferred only if one is provisioned. Otherwise preserve GitHub’s approval requirement for CI triggered by a `GITHUB_TOKEN`-created PR and record that operational gate; a manual dispatch is not a replacement for required PR checks.
- The current player artifact is a macOS arm64 CLI tarball. Claim Developer ID signing or notarization only after the exact distributed artifact and its contents pass the applicable Apple verification. If credentials or a suitable distributable are unavailable, label it unsigned and document the actual launch limitation. Do not imply signing from a successful build or tell adopters to disable Gatekeeper globally.

### Package and host/compiler support
- Verify relocated installed C and C++ consumers against `GabbaBoy::core`, with no SDL or private build-tree dependency, on the tested Linux x64 (Ubuntu 22.04), macOS arm64 (macOS 14), and Windows x64 (Windows 2022) runner combinations. Add Windows relocated-package coverage if the existing package workflow does not yet provide it.
- Release the SDL3 player only for the currently tested macOS arm64 configuration. Record actual compiler, CMake, runner image, and build configuration observed by each run. Runner labels and observed OS versions are evidence for those combinations, not promises of minimum OS versions or all architectures.
- Reuse the existing CMake install/export, relocation verifier, consumer programs, and package smoke. Do not add vcpkg, Conan, Homebrew, an installer framework, a C++ wrapper, or a stable ABI promise in this phase.

### Native consumer and Playstead handoff
- Provide a small, runnable C consumer that uses the relocated installed package. It should demonstrate legal fixture loading, bounded half-dot execution, timestamped input, caller-owned frame/audio output, and the host’s explicit battery import/export responsibility. Compile and run it from outside the source/build tree as part of package qualification.
- Document how this native seam could map into a future Playstead GB adapter. The currently inspected Playstead adapter is a GBA/mGBA external-process integration, not a live GabbaBoy Game Boy integration. State that distinction plainly and do not edit the sibling project, add a Swift bridge, or invent a new process protocol here.
- Keep adopter documentation aligned with current ownership, time/input/output, save recovery, support scope, upgrade, and troubleshooting behavior. Prefer concise examples using existing APIs over a new abstraction layer.

### Compatibility, performance, and safety evidence
- Publish a versioned support ledger tied to the release source and fixture/corpus revisions. Name the boot profile, modeled DMG revision, supported cartridge scope, exact eligible corpus, executed denominator, failures, exclusions and known issues. The three currently eligible derived CPU/timer cases are a small scoped corpus, not a game-compatibility percentage. Preserve the distinction between software-model evidence, source-derived expectations, and physical observations; there are no physical DMG, broad game-library, or perceptual claims.
- Reuse fixed project fixtures and project-owned measurement harnesses. Record workload/configuration, build type, compiler, runner/hardware and OS, output digest, warm-up, raw samples, trace/no-trace pairing, memory/allocation scope, and uncertainty. Keep initial numbers advisory; set budgets only after repeated measurements characterize variance. Trace-on/off runs must preserve the same correctness digest.
- Keep the measurement and fuzz toolchain small. Add no Google Benchmark or third-party fuzz library by default. Retain deterministic battery/API regression coverage, add bounded loader and stateful battery/API fuzz targets using compiler-integrated libFuzzer when supported, and run them with applicable sanitizers. Fast CI should run bounded deterministic seeds and regression reproducers; longer fuzz exploration can run separately. Every minimized finding becomes a fast deterministic regression. Explicitly bound input, execution, and memory.
- Boundary regressions must check overflow, truncation, allocation/work limits, and failed-operation atomicity at ROM, save, and public API edges. Do not treat fuzz duration or corpus size as correctness proof.

### Release automation, CI security, and failure behavior
- Re-read current repository rules before implementation. At discussion time, `main` used strict required contexts `required-native`, `fixture-repro`, and `preview-package-smoke`; confirm each status on the exact current PR head and verify merge eligibility instead of relying on this snapshot.
- Run release automation only from trusted repository/tag paths with least-privilege job permissions and full-SHA-pinned actions. Never use `pull_request_target` to check out or execute untrusted PR code. Missing, stale-SHA, skipped, cancelled, timed-out, or failing required evidence blocks release publication.
- Build and qualify final release bytes without depending on a cache. The repository had no configured Actions cache at discussion time; keep the release lane cache-free unless measured need justifies adding a trusted cache with immutable inputs and explicit hit/miss evidence. A cache hit is never proof of a valid artifact.
- Smoke the extracted final macOS package at a relocated path using the original legal fixture and MBC1 continuation fixture, scripted video/audio backends, and fresh processes. Exercise load, input, visible-frame production, PCM delivery, save, exit, and reopen. Record that dummy SDL devices establish software-path behavior only, not physical device or perceptual quality.
- Preserve exact-head bot CI behavior: verify a release/version PR actually receives every required check. Prefer the scoped GitHub App token if configured; otherwise use the documented approval gate for token-created PR runs. Never use a broad personal token or skip protection to make automation appear green.

### Interface and dependency restraint
- Keep the existing simple player and command-line help. Phase 6 is primarily packaging, evidence, and handoff; make only targeted usability or documentation changes that close a stated adopter need. No new UI framework.
- Follow the project preference for small, flat dependency trees. A pinned release orchestration action is justified only for repeatable release versioning; measurement and fuzz harnesses should remain project-owned or compiler-provided unless concrete evidence shows a missing capability.

### the agent's Discretion
- Choose the smallest package manifest/sidecar format that can be validated and consumed without duplicating the version, source SHA, artifact digest, or fixture identity inconsistently.
- Select fixed legal workloads and practical bounded fuzz durations after inspecting existing fixtures, CTest inventory, and CI time variance; record rationale and observed variability.
- Choose the precise documentation placement and the smallest script or C example structure that fits existing project patterns. Keep the decisions above fixed and stop if implementing them would require an unprovisioned credential, inaccessible signing identity, or an inaccurate claim.

</decisions>

<specifics>
## Specific Ideas

- The preference from the user is to favor direct, small project code over another dependency; add a dependency only when it has a concrete benefit and stays narrowly scoped.
- Use the existing `GabbaBoy::core` install target and run consumer examples against an installed package relocated away from the build tree.
- Release metadata should make the provenance chain easy to follow: version/tag → exact source SHA → fixture/corpus identity → build environment → downloaded asset digest → smoke result.
- Treat “unsigned” and “not notarized” as valid explicit release states. They are not equivalent to verified Apple trust.
- A support ledger should let a careful adopter understand exactly what was exercised and excluded without translating a small corpus pass rate into a broad compatibility claim.
- Current Playstead reference observed at discussion time: [AdapterHost.swift](https://github.com/szTheory/playstead/blob/a102d6082968bc09ca00fefbf5c552ecf979fd63/playstead-mac/Playstead/Adapter/AdapterHost.swift) and [AdapterPin.json](https://github.com/szTheory/playstead/blob/a102d6082968bc09ca00fefbf5c552ecf979fd63/playstead-mac/Playstead/Adapter/AdapterPin.json). It describes a GBA/mGBA process adapter, so the Phase 6 example is an integration seam and adoption aid, not a live Playstead feature.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.** Recheck live repository settings and branch rules during planning/execution because they can change.

### Phase scope and project decisions
- `AGENTS.md` — phase pause, branch/PR/evidence, release, provenance, and dependency rules.
- `.planning/PROJECT.md` — identity, goals, and current product boundary.
- `.planning/REQUIREMENTS.md` §SHIP-01–SHIP-08 — the eight active phase requirements.
- `.planning/ROADMAP.md` §Phase 6 — fixed goal and five success criteria.
- `.planning/STATE.md` — current workflow state and prior phase evidence.
- `.planning/context/BRIEF.md` — milestone intent and constraints.
- `.planning/context/DECISIONS.md` D-015–D-018 and D-025 — evidence provenance, performance evidence, hosted CI gates, bot-token policy, and confidence-qualified software models.
- `.planning/context/WORKFLOW.md` — exact-head checks, workflow pause, and evidence expectations.
- `.planning/context/FUTURE-MILESTONES.md` — revisable future breadth, including live adoption work.

### Research and prior evidence
- `.planning/research/INDEX.md` — research navigation.
- `.planning/research/SUMMARY.md` — prior implementation research and Phase 6 research gaps.
- `.planning/research/QUALITY-AND-DELIVERY.md` — package, delivery, release-automation, and provenance recommendations.
- `.planning/research/PITFALLS.md` — recurring correctness and evidence pitfalls.
- `.planning/research/HARDWARE-AND-VALIDATION.md` — model applicability and validation limits.
- `.planning/research/ARCHITECTURE.md` — core/adapter boundaries and public API constraints.
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-CONTEXT.md` — settled audio, playback, evidence, and hardware-limit decisions.
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-VERIFICATION.md` and `05-VALIDATION.md` — current completed evidence and limitations.
- `.planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-VERIFICATION.md` — save-continuation behavior and package evidence.
- `.planning/phases/GB-03-visible-interactive-dmg/03-CONTEXT.md` — player/package scope and limitation claims.

### Existing implementation and workflow patterns
- `CMakeLists.txt` — version, install/export, core, and optional player configuration.
- `.github/workflows/ci.yml`, `.github/workflows/preview.yml`, and `.github/workflows/fixture-repro.yml` — current matrices, required gates, package and fixture verification.
- `cmake/PreviewPackageSmoke.cmake` and `cmake/VerifyInstalledPackage.cmake` — exact downloaded/relocated package smoke patterns.
- `tests/consumers/c/main.c` and `tests/consumers/cpp/main.cpp` — installed public API consumer patterns.
- `tests/expected-tests.txt`, `tests/test_battery_fuzz.c`, `tests/test_audio_no_alloc.c` — fail-closed inventory, existing boundary/fuzz regression, and allocation assertions.
- `tests/scripts/verify-phase3-player.sh` — pinned SDL macOS package, legal notices/fixture metadata, and package verification pattern.
- `tests/scripts/measure-audio-playback.sh` — repeatable measurement and receipt pattern.
- `README.md`, `docs/preview.md`, `docs/audio-and-playback.md`, and `docs/cartridge-and-saves.md` — current adopter-facing claims and limitations to keep synchronized.

### External primary references
- [GitHub immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases) — tag and asset immutability behavior.
- [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations) — provenance generation and verification model.
- [GitHub secure use reference](https://docs.github.com/en/actions/reference/security/secure-use), [secure `pull_request_target` use](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target), and [dependency caching](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching) — workflow token, untrusted code, pinning, and cache boundaries.
- [GitHub `GITHUB_TOKEN` behavior](https://docs.github.com/en/actions/concepts/security/github_token) — downstream workflow suppression and approval semantics.
- [Apple notarization overview](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution) and [customized notarization workflow](https://developer.apple.com/documentation/security/customizing-the-notarization-workflow) — direct-distribution requirements and scripted validation.
- [release-please action documentation](https://github.com/googleapis/release-please-action) and [release-please customization](https://github.com/googleapis/release-please/blob/main/docs/customizing.md) — manifest release flow and version-file updates.
- [CMake `install()`](https://cmake.org/cmake/help/latest/command/install.html) and [CMake package config helpers](https://cmake.org/cmake/help/latest/module/CMakePackageConfigHelpers.html) — relocatable package/export conventions.
- [LLVM libFuzzer](https://llvm.org/docs/LibFuzzer.html) — compiler-integrated fuzzing and sanitizer use without a separate runtime dependency.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- CMake install/export already exposes the core as `GabbaBoy::core`; existing C and C++ consumer programs and relocation verification can be expanded to release matrices.
- Current CI already covers Linux x64, macOS arm64, Windows x64, sanitizers, and a CMake floor. Preview packaging currently smoke-tests installed Linux x64 and macOS arm64 packages; the Phase 6 planner should close the Windows consumer gap if still present.
- The Phase 3 player verification script builds a pinned SDL 3.4.18 macOS tar package, carries legal/license and fixture metadata, runs extracted-package smoke, and records revision and package digest. Extend this rather than adding a packaging framework.
- `tests/expected-tests.txt` enforces a fixed test inventory. Existing battery fuzz regression and no-allocation audio checks provide patterns for fail-closed validation.
- `tests/scripts/measure-audio-playback.sh` already records a workload receipt and digest; reuse its provenance and sample-reporting style for phase-wide baselines.

### Established Patterns
- Public operations are bounded, per-instance, and caller-owned; host filesystem, SDL, wall clock, and environment stay in adapters.
- Packages and fixtures are verified from exact bytes; CI failures and missing inventory entries must fail closed.
- Support statements distinguish the deterministic source-backed software model from measured hardware and disclose model applicability, exclusions, and expected failures.
- Actions are pinned by full commit SHA; remote checks must pass on the exact candidate commit before merge or release.

### Integration Points
- Add release workflows beside existing CI, preview, and fixture workflows; verify their interactions with current branch protection and token-trigger semantics.
- Connect a new native example to the installed CMake package and existing legal fixtures, then run it from a relocated prefix.
- Connect release metadata and support ledger to the current fixture/corpus manifests and existing player package verifier so evidence cannot drift from the shipped bytes.
- Update the README and relevant build/API/save/preview docs together with release notes, support ledger, and troubleshooting information.

</code_context>

<deferred>
## Deferred Ideas

- CGB and additional mapper/revision support, including MBC1M, RTC, save states, and broad game-library compatibility.
- Live Playstead Game Boy integration, Swift bindings, or a new process protocol; the current adapter is GBA/mGBA.
- Stable ABI, libretro, package-manager publication, app bundle/installer/store distribution, or universal binaries.
- Physical DMG testing, perceptual audio/video judgments, device hotplug qualification, and stronger claims than available evidence supports.
- Third-party benchmark or fuzz frameworks, telemetry, and fixed performance budgets before repeated measurements characterize variance.

</deferred>

---

*Phase: GB-06-qualified-dmg-release-and-consumer-handoff*
*Context gathered: 2026-10-08*
