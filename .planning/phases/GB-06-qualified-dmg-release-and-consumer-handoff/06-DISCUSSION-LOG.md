# Phase 6: Qualified DMG Release and Consumer Handoff - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `06-CONTEXT.md`; this log preserves alternatives and rationale.

**Date:** 2026-10-08
**Phase:** 6-Qualified DMG Release and Consumer Handoff
**Areas discussed:** Release identity and macOS trust, package/support matrix, native consumer and Playstead handoff, compatibility/performance/fuzz evidence, release automation and CI security

The owner explicitly delegated the choices and asked for broad fan-out followed by one synthesized recommendation per decision area. No per-area answers are represented as direct user quotes. The assessment used product/adopter, architecture/build, security/supply-chain, operations, test/evidence, performance, and UX/documentation lenses. External research favored primary GitHub, Apple, CMake, LLVM, and release-please documentation. The owner's preference for a small, flat dependency tree was applied throughout.

---

## Release identity, versioning, and macOS trust

| Option | Description | Selected |
|--------|-------------|----------|
| Temporary Actions artifacts only | Reuse preview artifacts; low setup cost, but short retention and weak durable adoption identity. | |
| Versioned GitHub Release, exact bytes, verifiable provenance | Use a version/tag, source/build metadata, digests, a draft qualification path, and immutable publication when supported. Consumers get durable assets and a source-to-byte trail. | ✓ |
| Package registry or installer ecosystem | Add package managers or a macOS installer/app-store pipeline. Familiar to some adopters but expands scope and dependency/maintenance surface beyond the current CLI package. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Assume signing/notarization from successful packaging | Incorrectly conflates build success with Apple trust and risks misleading adopters. | |
| Sign and notarize only if exact distributed files pass Apple's verification | Best user trust when real identity, credentials, format, and validation are available; requires secure credentials and actual verification. | ✓ |
| Ship explicitly unsigned until those prerequisites exist | Accurate fallback for the present CLI tarball; docs must state actual macOS launch friction. | ✓ (fallback state) |

**User's choice:** Earlier instruction delegated selection to the agent; selected versioned exact-byte release, with verified trust claims or an explicit unsigned state.
**Notes:** One versioned GitHub Release is the durable delivery channel; preview artifacts remain short-lived evidence. Use CMake's current version as the version source (`0.1.0` at discussion time) and matching `v<version>` tags. Build once from the exact trusted tag, qualify downloaded final assets, and publish only after all checks pass. Prefer immutable release and artifact-attestation features when enabled and verifiable. Apple signing/notarization is separate from build correctness; current package shape is a CLI tar archive, not a notarized `.app` or disk-image installer. This area considered adopter trust, supply-chain provenance, package simplicity, and macOS distribution experience. See GitHub's [immutable release](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases) and [artifact attestation](https://docs.github.com/en/actions/concepts/security/artifact-attestations) docs and Apple's [notarization overview](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution).

---

## Package and host/compiler support matrix

| Option | Description | Selected |
|--------|-------------|----------|
| Claim all popular OSes and compilers | Broad marketing reach but unsupported by finite evidence and invites false OS/architecture promises. | |
| Claim tested runner combinations and report observed tools | Relocated C/C++ consumers on Linux x64, macOS arm64, and Windows x64; SDL player on tested macOS arm64. Precise and expandable as evidence grows. | ✓ |
| Add package managers / multiple package formats now | Improves discoverability for some ecosystems, but adds release surfaces, package metadata, and recurring maintenance before demand is established. | |

**User's choice:** Earlier instruction delegated selection to the agent; limit claims to demonstrated matrix combinations.
**Notes:** The current CI runners are Ubuntu 22.04 x64, macOS 14 arm64, and Windows 2022 x64. Treat those as observed test configurations, not minimum OS support or universal architecture claims. Existing CMake exports and relocated consumers give adopters direct integration evidence without SDL in the core. The preview currently covers installed consumers on Linux and macOS; close Windows coverage if it remains absent. Product, build portability, and maintenance lenses all favor a narrow factual support ledger over a large unsupported matrix.

---

## Native consumer and Playstead handoff

| Option | Description | Selected |
|--------|-------------|----------|
| Add a C++ wrapper or Swift bridge | More ergonomic for one host ecosystem but creates new public/ABI and maintenance surface before an actual adopter needs it. | |
| Define a new CLI/process protocol | Could align with process-isolated integrations but adds protocol, serialization, and lifecycle decisions unrelated to current public C API. | |
| Ship a small relocated C consumer and map its seam to Playstead | Exercises the actual supported package and documents how an adopter could integrate; minimal code and no invented compatibility claim. | ✓ |
| Claim live Playstead integration | Not supported by the inspected external project state: the current adapter is for GBA/mGBA via an external process. | |

**User's choice:** Earlier instruction delegated selection to the agent; use a direct C integration example and make current Playstead status explicit.
**Notes:** Demonstrate bounded half-dot execution, timestamped input, caller-owned frame/audio buffers, and host-managed battery import/export. Compile and run against a relocated `GabbaBoy::core` install, outside the build tree. The inspected Playstead files are linked by pinned commit in `06-CONTEXT.md`; this is a documented seam, not a live GB adapter. This protects the adopter from false integration expectations and avoids a premature wrapper/protocol dependency.

---

## Compatibility, performance, and fuzz evidence

| Option | Description | Selected |
|--------|-------------|----------|
| Publish corpus pass percentages as compatibility | Simple to read, but a tiny derived CPU/timer corpus would badly overstate supported game breadth. | |
| Publish a versioned scoped support ledger | Names model, cartridge scope, eligible/executed denominator, exclusions, known issues, and exact corpus/release identity. | ✓ |
| Set performance budgets before collecting repeated measurements | Gives an early target but risks noise-driven regressions or pressure to trade correctness for a score. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Add benchmark/fuzz frameworks and dependencies | Rich feature set, but more dependency and abstraction surface than the existing C harnesses currently justify. | |
| Use project-owned harnesses and compiler-integrated fuzzing | Reuse existing scripts and fixtures; use bounded Clang/libFuzzer when useful, with sanitizers and regressions, without adding a separate runtime library. | ✓ |
| Skip new fuzzing and performance evidence | Lowest immediate work, but fails the phase requirements and leaves security/performance claims unsupported. | |

**User's choice:** Earlier instruction delegated selection to the agent; choose scoped denominators, reproducible receipts, and low-dependency bounded testing.
**Notes:** Current eligible Mooneye-derived CPU/timer cases total three; they are not an all-game compatibility measure. The support ledger must distinguish software-model evidence from hardware observations. Measurement receipts should include workload/build/environment, raw samples, warm-up, output digest, trace status, memory/allocation scope, and uncertainty; performance budgets follow observed variance. Keep a deterministic fast fuzz/regression path and separate longer bounded exploration. Minimized bugs become fast regressions. Reviewed the evidence/performance tradeoff from software test, performance, security, and product lenses; LLVM documents libFuzzer as compiler-integrated instrumentation-driven fuzzing.

---

## Release automation, CI security, and failure behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Manual uploads with no exact-byte qualification | Easy to operate initially but lacks reproducible provenance and lets upload mistakes bypass evidence. | |
| Pinned release-please flow plus draft and exact-byte gates | Automates version PRs and release metadata while keeping build, downloaded-asset smoke, required checks, and publication gates explicit. | ✓ |
| Broad PAT, cache-heavy builds, or privileged PR execution | Adds credential blast radius and risks untrusted code or stale cache influencing trusted publication. | |

| Option | Description | Selected |
|--------|-------------|----------|
| Fail open on skipped or missing workflows | Makes intermittent CI easier to tolerate but can silently publish without expected evidence. | |
| Fail closed and recheck exact commit statuses | Missing, stale, skipped, cancelled, timeout, or failed required evidence blocks merge/release. | ✓ |
| Add caching before measuring need | Can reduce latency, but introduces cache trust/poisoning and invalidation complexity without current evidence of need. | |

**User's choice:** Earlier instruction delegated selection to the agent; automate versioning narrowly, preserve required check gates, and publish only qualified exact bytes.
**Notes:** `release-please` is one workflow action dependency, pinned by full SHA; no package/build dependency is added. Prefer a scoped GitHub App token if provisioned; otherwise record and honor the approval gate for `GITHUB_TOKEN`-created PR workflow runs. Do not assume credentials exist. At discussion time, branch protection on `main` required `required-native`, `fixture-repro`, and `preview-package-smoke`; execution must refresh the rules and prove current exact-head checks and merge eligibility. Release jobs remain cache-free unless measurements justify a trusted cache. No untrusted PR code under `pull_request_target`. These choices follow GitHub's [token](https://docs.github.com/en/actions/concepts/security/github_token), [secure-use](https://docs.github.com/en/actions/reference/security/secure-use), [cache](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching), and [release-please](https://github.com/googleapis/release-please-action) documentation.

---

## The agent's discretion

- Pick a compact sidecar/manifest schema that avoids duplicating canonical version, source, fixture, and digest fields.
- Select legal fixed workloads and bounded fuzz durations from existing fixtures and measured CI variance; keep the choices reproducible and clearly scoped.
- Choose documentation placement and the smallest existing-pattern C example or script shape.
- Stop before making trust, release, or support claims that depend on credentials, a live host, or evidence the repository cannot access.

## Deferred Ideas

- CGB, more mapper/revision coverage, MBC1M, RTC, save states, libretro, stable ABI, or universal compatibility claims.
- Live Playstead Game Boy adapter, Swift binding, or a new process protocol.
- Package manager, installer, app-store, or universal-binary distribution.
- New general-purpose benchmark/fuzz dependencies, hard performance budgets before variance is known, telemetry, physical hardware testing, or perceptual/device claims.

---

*Phase: GB-06-qualified-dmg-release-and-consumer-handoff*
*Discussion log generated: 2026-10-08*
