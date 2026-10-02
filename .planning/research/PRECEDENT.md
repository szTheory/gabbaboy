---
title: Transferable lessons from active sibling projects
project: GabbaBoy
researched: 2026-10-02
scope: C Game Boy and Game Boy Color core; host adapters; evidence and delivery
confidence: MEDIUM
status: research recommendations, not implemented GabbaBoy behavior
---

# Transferable project lessons

GabbaBoy targets Game Boy and Game Boy Color. NES, Neo Geo and GBA projects provide engineering precedent, not hardware specifications, compatible cartridges, or ready-made conformance claims. Preserve the reasoning and evidence; implement Game Boy behavior from its own sources.

This review inspected recent repository files and commit histories. It did not rerun sibling tests or query their hosted release state. **Implemented** means source/workflow exists; **recorded verification** means the repository records a run; **proposal** means planning only. Source paths below are relative to the named repository, so this document contains no workstation paths or account identities. Playstead and GlueyNeo were active, dirty worktrees: working-tree observations are explicitly distinguished from pinned commits. Other inspected repositories were clean at inspection.

Confidence uses the installed OpenGSD classifier: `query classify-confidence --provider websearch --verified` returned **MEDIUM**. That conservative tier applies to this synthesis, including transfer recommendations. Direct source observations and recorded verification have separate evidence labels instead of being promoted to unqualified hardware truth.

## Evidence map and currency

| Repository | Observed HEAD / date | Evidence actually present | Limits |
|---|---|---|---|
| GlueyNeo | `2f6ddbd`, 2026-10-02 | Authored C CPU diagnostic and timing slices; independent review invalidated an earlier candidate acceptance; explicit source/oracle/budget records | Early experiment. No accepted complete CPU/backend, playable Neo Geo core, hosted CI or release claimed. Concurrent uncommitted isolation work was excluded from qualification claims. |
| Nesturbator | `25bcfbc`, 2026-10-02 | C17 library/test card/runner, public API tests, generated palette, shared host conversion | Phase 1 underway. Plans for libretro, install packaging, full CI and real NES execution are not evidence those deliverables already work. |
| Playstead | `1de3e95`, 2026-09-28 | Production integration and recovery tooling; tracked evidence sanitization; current continuation capability refusal | Many uncommitted planning/workflow changes. Working-tree fixture guidance is useful but not assigned to HEAD. No current in-game continuation pass. |
| lattice_stripe | `66379aeb`, 2026-09-25 | Explicit aggregate CI, optional dependency isolation, synthetic consumer, release verification and recent retrospective | Elixir package mechanisms need adaptation to C; recorded release evidence was not independently fetched in this research. |
| ExifCleaner Electron | `c100554`, 2026-09-28 | Cross-platform packaged-app smoke, per-test execution evidence, exact release asset promotion and audits | Packaging/workflow source inspected; no fresh hosted run. Its large pipeline is inappropriate to copy wholesale into an empty C project. |

## Decisions GabbaBoy should inherit

### P-01 — Current evidence supersedes old success

GlueyNeo's `01-REVIEW.md` identified legal guest operands reaching undefined C shifts and unsafe host generator paths after earlier acceptance evidence. Its current `STATE.md`, `01-08-SUMMARY.md` and `01-09-SUMMARY.md` keep CPU admission pending despite passing diagnostic slices. The review itself was source inspection, not a new runtime reproduction. On 2026-10-02, `d8c5450` also corrected a CTest receipt parser that had misunderstood current `LastTest.log` blocks.

**Adopt:** each compatibility result binds source SHA, dirty status, compiler/flags, model profile, fixture identity, oracle version, test identities and outcome. A later counterexample reopens the claim. Keep one current ledger with supersession links and preserve old receipts as history. Phase closure must inspect current failures and exclusions.

**Tradeoff:** precise records cost a little tooling; they prevent much larger re-investigation and incorrect release claims. Do not build a custom governance framework before the first guest program runs.

**Source:** GlueyNeo `.planning/phases/01-cpu-acceptance-experiment/{01-REVIEW,01-08-SUMMARY,01-09-SUMMARY}.md`; `tools/owned_cpu/contract.py`; commits `d8c5450`, `0d4f1e3` (2026-10-02).

### P-02 — Audit legal guest arithmetic and host tools

GlueyNeo review CR-01–06 found signed/oversized shifts, unchecked path copies, unsigned EOF handling and one-past-capacity writes. A successful diagnostic exercised none of these arithmetic edges. These are transferable C failure classes; their 68000 instructions and cycle rules are not Game Boy rules.

**Adopt:** defined unsigned arithmetic, explicit carry/borrow logic, checked shifts and lengths, explicit byte loads/stores and bounded counters. Test zero, maximum, sign transition and exact/one-over limits. Sanitizer lanes cover the loader, state codec and bounded arbitrary guest execution, plus any fixture generator. Review generator outputs and source together when generation exists.

**Gate:** CPU arithmetic and parser slices must provide meaningful boundary evidence before claiming conformance. A fuzzer receives a work budget, so a valid guest infinite loop does not become an unbounded CI process.

### P-03 — Time is a public contract

GlueyNeo's latest owned slice separates reset debt, instruction, interrupt, exception and idle accounting, bounds requests, records overshoot, preserves ordered partial bus effects, and states that its functional callback trace is not a pin-level trace. That explicit distinction is the lesson; its instruction-boundary granularity is not sufficient evidence for Game Boy PPU/timer/DMA timing.

**Adopt:** define GabbaBoy's emulated time unit, event ordering, run limits, stop reasons and model-specific clock domains before subsystems interact. A zero-work request must have defined behavior. Argument validation can be transactional; a host error after visible guest side effects needs an explicit partial-progress result or terminal fault contract. Never promise all failures leave all state unchanged without proving it.

**Gate:** partitioned runs versus uninterrupted runs, simultaneous-event boundaries, reset/stop/wakeup, and host-fault ordering. Event expectations come from GB sources and model-specific tests.

**Source:** GlueyNeo `experiments/owned_cpu/{cpu.c,SUBSET.md}`, `tests/owned_cpu/ORACLE.md`, `01-09-SUMMARY.md`; `0d4f1e3` (2026-10-02).

### P-04 — Prove a small consumer seam immediately

Nesturbator already implements a test card, rational audio sample accounting, caller-owned pitched buffers, explicit allocation/error behavior and two-instance checks. Its header is compiled alone as C and C++, and SHA-256 has known-answer tests. These are implemented early integration checks, not NES emulation proof.

**Adopt:** early GabbaBoy library + headless runner + thin libretro adapter, with a deterministic integration fixture clearly labeled as synthetic until the CPU executes guest code. Keep the core independent of windows, filesystems, audio devices, wall clocks and frontend packages. Use a shared host conversion helper where the runner and adapter need identical presentation; hash native emulated output separately from host color treatment.

**Tradeoff:** a small synthetic seam gives early usable artifacts and validates integration; it must not consume a long milestone while delaying real DMG execution. Native GB/GBC pixels, stereo audio, screen dimensions and clock rates must come from GB requirements.

**Sources:** Nesturbator `include/nesturbator.h`, `src/frame.c`, `host/convert.c`, `tests/check.h`, `tests/core/test_frame.c`, `tests/header/`; `258780c`, `b27f865`, `25bcfbc` (2026-10-02).

### P-05 — Test installation as a real adopter

lattice_stripe's latest milestone uses a separate synthetic Phoenix consumer and a published-package smoke. Its retrospective distinguishes the package release commit, current main, and archive metadata. Nesturbator plans an install-consumer test but had not implemented its installation phase at inspection.

**Adopt:** a tiny external C/C++ consumer builds against GabbaBoy's staged installation, then separately against downloaded release assets. Exercise creation, loading an original fixture, input, audio/video, persistence, and destruction through only installed headers and libraries. Verify exported targets, symbol visibility, include paths and no accidental SDL/libretro/test-framework dependency. Add a minimal-core build with adapters and tools disabled.

**Sources:** lattice_stripe `.planning/RETROSPECTIVE.md` (v1.12, 2026-09-25), `.github/workflows/ci.yml`, `scripts/maintainer/{published_hex_adopter_smoke,release_evidence_check}.sh`; `ad48bd32` (2026-09-24). Nesturbator `.planning/preparation/ENGINEERING.md` is a proposal source only for installation.

### P-06 — Check that the test ran and that its oracle can fail

ExifCleaner CI verifies named negative controls actually executed, because a green test process had been insufficient. Its `72b5b2e` commit (2026-09-18) wired a previously uninvoked evidence gate into CI. Playstead likewise added a hosted-evidence workflow after discovering a validator existed but was never called. GlueyNeo's supervised mutations accept only the named assertion, not crashes or unrelated failures. Its historical Python assertions could disappear under optimization.

**Adopt:** expected test identities and nonzero denominators for required conformance lanes; explicit pass/fail/unsupported/blocked/timeout outcomes. Add a few high-value negative controls for the harness, state continuation and loader safety. Validators use explicit errors, not C `assert` or Python `assert` as mandatory evidence logic. Test missing, stale and malformed reports. Wire every promised gate into its actual CI/release path.

**Tradeoff:** targeted mutation checks protect valuable oracles; mutating every ordinary unit test creates maintenance cost without proportional value.

**Sources:** ExifCleaner `.github/workflows/ci.yml`, `scripts/{nc_evidence_gate,oracle_accountability_gate}.mjs`; Playstead `.github/workflows/verify-hosted-evidence.yml`; GlueyNeo `tests/owned_cpu/negative_timing.py`, `01-REVIEW.md` WR-01.

### P-07 — Homebrew availability is not redistribution permission

| Playstead fixture | Observed evidence | GabbaBoy consequence |
|---|---|---|
| AerevenAdvance | Working-tree `playstead-mac/docs/TEST-FIXTURES.md` identifies an owner-supplied **private GBA** fixture, with an ignored registry and private saves. This review did not locate or establish redistribution permission. | Do not copy into public CI or claim it is a GB/GBC fixture. Reuse the private-fixture registry pattern only when needed. |
| `playstead-mac/spike/testrom/savetest.gba` | Tracked original GBA source, source comments and project MIT license; source/build/header files are available. `main.c` writes SRAM automatically. | Useful original-fixture design precedent, but GBA bytes cannot execute on GB/GBC. Build an original GB fixture with reviewed toolchain/assets instead. |
| `savetest.gba` restoration claim | `main.c` initializes its counter to zero and overwrites SRAM on startup; fixture guide explicitly limits its proof. | It can demonstrate writes/flush, not restored game progress. A GB continuation fixture must read persisted state and make resumed behavior distinguishable from a fresh boot. |

**Adopt:** a public fixture manifest records source URL/revision, license/notice, build recipe, toolchain, binary hash and expected model/outcome. Source, assets, generated ROM and boot-logo requirements each need an explicit provenance decision. A checksum proves byte identity, never permission. Commercial ROMs, BIOS, personal saves and captures remain outside Git and public CI.

### P-08 — Byte restoration is only one part of continuation

Playstead's latest 2026-09-28 qualification ledger remains `blocked-capability`. The earlier inference that mGBA lacked deterministic Lua input controls was corrected; the actual unresolved issue was a supported noninteractive loader for the exact installed 0.10.5 app. No fixture replay or current visible continuation pass followed. Documentation for later/master source was not accepted as release capability.

**Adopt:** the GabbaBoy runner itself supports deterministic inputs and bounded stepping, avoiding reliance on GUI automation to establish core correctness. Prove persistence by save → destroy → fresh instance → load → resumed behavior; compare with a fresh-start negative control. Prove snapshots by loading into a fresh instance and matching subsequent CPU/bus/video/audio behavior at awkward timer/DMA/PPU boundaries. Test independent instances without sharing mutable hidden state.

**Separate contracts:** battery save bytes, RTC data, emulator snapshots, replay identity and C ABI each version independently. Keep the persistent save format simple and interoperable where documented; snapshot compatibility may be more constrained and must say so.

**Sources:** Playstead `playstead-mac/docs/{TEST-FIXTURES,CONTINUATION-PROTOCOL}.md`, `.planning/phases/06-recovery-proof-ci-and-e2e-pipeline/06-CONTINUATION-QUALIFICATION.md`; HEAD `1de3e95` (2026-09-28), current working-tree evidence. No private fixture registry was opened.

### P-09 — Required checks must explicitly require success

lattice_stripe uses one `ci-gate` with `if: always()` and checks each required dependency result equals `success`; it also compiles without optional dependencies and treats documentation warnings as failures. GitHub can otherwise regard skipped checks as successful, while workflow-level filtering can leave required checks pending. [GitHub required-check guidance](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)

**Adopt:** an always-running aggregate check, explicit expected lanes, bounded timeouts and fail-safe change classification. Initially keep the workflow simple; add path-based job savings only with controls proving required coverage remains. A capability absent from an optional developer machine may be skipped locally, but that result cannot qualify a promised release platform or required CI behavior.

**Source:** lattice_stripe `.github/workflows/ci.yml:456`; Nesturbator `.planning/preparation/ENGINEERING.md` offers a similar proposal, not installed CI.

### P-10 — Refresh automation assumptions against current GitHub behavior

As checked on 2026-10-02, GitHub Cloud documents approval-required PR workflows for certain PR creation/update events made with `GITHUB_TOKEN`; ordinary pushes by that token still suppress workflow recursion. Explicit dispatch starts a workflow, but its Actions checks are not eligible to satisfy protected PR required checks. Thus old sibling statements about bot PRs and dispatch fallback must not become GabbaBoy defaults. [Token behavior](https://docs.github.com/en/actions/concepts/security/github_token), [required-check eligibility](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)

**Adopt:** for unattended bot PRs, prefer a narrowly scoped GitHub App installation token, and prove the actual PR → required check → current-head merge → release event chain in the repository. Recheck PR identity and head immediately before merging. Do not bypass branch protection or treat a stale green run as qualifying a new head. Handle merge queues through their documented event when used. Keep explicit user-requested GSD phase pauses independent from routine authorized PR/release automation.

**Sources examined:** lattice_stripe `.github/workflows/{release,release-pr-automerge,publish-hex}.yml`; ExifCleaner `.github/workflows/auto-merge-release.yml`. Their current files are precedent, not authority for GitHub's current product semantics.

### P-11 — Publish the bytes that passed the consumer smoke

ExifCleaner builds and installs native packages, runs smoke against the installed app, writes source/artifact receipts, then promotes artifacts from that exact CI run. Its release job audits a draft and downloaded draft bytes before publication. macOS bundles stay sealed in an archive/package when crossing job boundaries, preserving required filesystem metadata.

**Adopt:** build GabbaBoy archives once per qualified source/configuration, test unpacked library/runner/core artifacts, create a checksum/provenance manifest, assemble the complete draft, verify downloaded bytes, then publish. A macOS libretro module needs real-host loading evidence; a separately shipped app would additionally need its own signing/notarization policy. Do not invent signing claims from the existence of a DMG, ZIP or successful compile.

**Tradeoff:** a tiny SDK needs fewer packages than ExifCleaner. Preserve the proof chain, not its seven-artifact count. Attestations add provenance only when verified; they do not prove correctness. [GitHub attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations)

**Sources:** ExifCleaner `.github/workflows/{ci,release}.yml`, `scripts/{release_evidence,release_asset_gate,release_state_gate}.mjs`; `88ced72` (2026-09-22) corrected Windows artifact naming and false signing claims.

### P-12 — Optimize CI with measured critical paths and dependency boundaries

lattice_stripe has distinct optional-integration and adopter lanes; ExifCleaner restores browser payload caches but still installs system dependencies. These patterns solve concrete faults. Their full runtime/framework matrices are disproportionate for GabbaBoy's initial footprint.

**Adopt:** measure cold and warm wall time, runner-minutes and peak memory before adding caches or multiplying jobs. Use target-based CMake and core-only builds; scope warnings and sanitizer flags to owned targets. Keep at least one clean dependency/build path. A compiler cache key must include compiler/toolchain, target, build options and relevant dependency identity; never treat a cache hit as proof of correct dependency selection. Bound build/test parallelism by memory and CPU, and cancel superseded PR work.

**Security:** cache contents are inputs, and privileged workflows must not execute untrusted PR code or restore untrusted executable payloads without an appropriate trust boundary. Do not cache secrets. [GitHub cache guidance](https://docs.github.com/en/actions/concepts/workflows-and-actions/dependency-caching), [secure-use reference](https://docs.github.com/en/actions/reference/security/secure-use)

### P-13 — Make performance claims explainable

Inherited goal: fast feedback and measurable runtime improvement. No inspected sibling receipt establishes a GB/GBC frame-time baseline.

**Adopt:** first measure emulated cycles/second, host time/frame, real-time headroom, allocations after load, peak resident memory, audio underruns and startup/load time against named workloads and hardware. Keep correctness hashes beside benchmark identities. Use deterministic operation/allocation budgets in ordinary CI; use repeated controlled hardware measurements for timing regressions. A p99.999 claim requires enough samples to estimate that tail and an explicit confidence method; a short noisy hosted run cannot establish it. Avoid threshold inflation, changed workloads or baseline refreshes that hide regressions.

**Tradeoff:** profile before batching events, adding SIMD or changing dispatch. Maintain an observable scalar path where it materially supports comparison. Do not bolt on high-volume tracing by default; optional bounded trace sinks must demonstrate negligible disabled cost and avoid guest/private content in public logs.

### P-14 — Keep the readable core smaller than its policy system

lattice_stripe's recent retrospective values cohesive private modules, an explicit consumer API, reader navigation, and bounded quality work. GlueyNeo's diagnostic was eventually made a prerequisite for expanding the experiment; its measured churn records show evidence tooling is a real maintenance cost. Nesturbator's small CTest assertion helper is a plausible alternative to vendoring a test framework, while GlueyNeo uses Unity. Neither choice universally wins.

**Adopt:** small modules named after hardware responsibilities, plain control flow, localized byte/integer helpers, source citations for nonobvious hardware behavior, and one current contract per topic. Introduce dependencies only for a concrete payoff. Keep current milestone detailed, next milestone outlined, later work provisional. Revise docs and evidence in the same behavior PR, then stop at the user's named phase checkpoint. No database, Phoenix/Ecto, network telemetry service or general plugin framework belongs in the emulator core merely because a sibling uses one.

## Lightweight cross-project lesson exchange

At milestone close or when explicitly requested, produce a public-safe record with: lesson ID; source project/commit/date; observed failure; smallest counterexample; supported scope; changed invariant; repair and exact verification; limits; cost; and superseded lesson IDs. Receiving projects must re-evaluate hardware and licensing applicability before adoption. Share semantic patterns and source pointers; do not ferry private ROMs, save states, captures, absolute paths, credentials or copied incompatible code.

## Remaining qualification work

- Verify current GitHub Cloud token/ruleset behavior in GabbaBoy when the remote and App identity exist; this research did not configure remote protections.
- License and build a GB-specific public fixture corpus; Playstead's private GBA fixture does not supply that corpus.
- Qualify real RetroArch macOS loading and installed-package use for GabbaBoy artifacts.
- Measure GB-specific accuracy/performance baselines; synthetic integration, conformance, homebrew playability and private commercial compatibility need separate denominators.
- Revisit sibling lessons at future milestones using their newest source and failed evidence, without reopening already resolved user setup.
