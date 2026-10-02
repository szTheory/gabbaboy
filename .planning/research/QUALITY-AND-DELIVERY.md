# GabbaBoy quality, performance and delivery

Researched: 2026-10-02. Status: proposed operating policy; no test results, compatibility rate or performance baseline yet exists. Scope complements [STACK.md](STACK.md) and hardware-specific research.

Evidence confidence: **MEDIUM** from OpenGSD `query classify-confidence --provider websearch --verified`; sources are primary documentation. Numeric targets below are examples or measurement policies, not established product results. Recheck changing GitHub policies and action versions when implementing workflows.

## Evidence before a compatibility claim

| Evidence layer | High-value checks | Boundary of the claim |
|---|---|---|
| Public API | Empty/truncated/oversized inputs, invalid configuration, output capacity, load failure leaves old session intact, multiple contexts, lifecycle errors | Safety and integration behavior, not hardware fidelity |
| Component contracts | Table-driven arithmetic/bus/timing boundaries with independently specified expected results | Avoid tests that reimplement the same algorithm and repeat its mistake |
| Hardware fixtures | Licensed, pinned test ROMs with explicit model, boot mode, pass mechanism, cycle limit and expected result | A suite passing does not establish every model or game works |
| End-to-end homebrew | Deterministic input replay through cartridge, CPU, PPU, APU and host outputs; a bounded completion criterion | Useful integration evidence; screenshots alone cannot establish timing or sound accuracy |
| State and properties | Save/restore/replay equivalence, chunked stepping equivalence at supported boundaries, reset determinism, independent instance isolation | Reject stale pointers and missing hidden state; record deterministic seeds and failing cases |
| Differential checks | Compare against documented hardware traces first; reference emulator disagreements become investigations | Another emulator is evidence, not an infallible oracle; never copy opaque expected output as proof |
| Robustness | Narrow ROM/state/save parsers, bounded machine execution, operation-sequence fuzzing, allocation failure where injectable | No crash is not proof of correct emulation; resource bounds are part of the oracle |
| Adoption | Install then relocate package; external C and C++ consumers; clean core-only configure with SDL unavailable | Verifies what downstream users receive rather than only the source-tree build |
| Shipping | Unpack exact release archive in a clean location; dependency inspection, `--version`, licensed bounded smoke and installed-core consumer | Packaging evidence; dummy audio/video drivers do not certify actual device behavior |

Every test result should identify fixture hash/version, license, hardware model, boot path, core revision, build configuration, runtime limits and verdict. Keep unsupported / excluded / timeout / crash / pass distinct. Timeouts fail their test; do not turn them into skips. Compare compatibility denominators only when fixture sets and configurations match. Private commercial-ROM results remain local and opt-in.

Use CTest labels to separate fast contracts, hardware suites, integration, packaging and fuzz replay. Every expected test set must execute at least one test and assert expected inventory; a filter typo yielding zero tests cannot pass. Run release-mode tests with assertions active. Keep hermetic fixture retrieval or vendored licensed bytes pinned by hashes; never make ordinary CI depend on a mutable website or a live game download.

ASan catches memory faults; UBSan checks include signed overflow, bad shifts and misalignment. Configure UBSan to fail the job on findings; its default recovery behavior can otherwise print an error while continuing. Use a small explicit allowlist for intentional unsigned hardware wrap if additional integer sanitizers are enabled. Do not ship sanitizer runtimes as the normal release binary. [Q1][Q2]

Fuzz harnesses must tolerate empty and malformed bytes, reset per invocation, avoid `exit`, and bound memory and emulated ticks independently of wall time. Split load/state/save harnesses so coverage is meaningful. Replay fixed regressions in PRs; run fresh mutations on a scheduled budget and preserve minimized failures. LibFuzzer remains practical with matching Clang, although major feature development has moved elsewhere; keep the reusable harness independent of the engine. [Q3]

## Fast CI with explicit scope

| Lane | Initial contents | Expansion trigger |
|---|---|---|
| Every PR | Fast format/build/contract checks; Linux Clang ASan+UBSan and fixture replay; representative GCC build; macOS player/package smoke; Windows MSVC core/consumer smoke | Add each lane when its target exists; keep advertised platforms represented without a compiler × build-type × OS Cartesian product |
| Main/release candidate | Full relevant regression set, exact-release builds, relocated install consumers, packaged player smoke and provenance manifest | Required before publishing corresponding artifact |
| Scheduled | Longer hardware/homebrew inventory, bounded fresh fuzzing, selected static analysis, oldest supported toolchain, additional architectures and optimization configurations | Expand only with a named uncovered risk; failures become tracked work |
| Controlled performance | Fixed workloads, repeated base/candidate measurements, playback soak and memory trends | Initially report only; enforce thresholds after runner variance and baseline are measured |

Use Ninja and CTest concurrency based on allocated cores and memory. Avoid launching all build/test layers with full nested parallelism; annotate expensive tests and serialize device-dependent cases. Cancel superseded PR runs, but serialize release publication without cancelling an active upload. Record queued time, wall time, runner minutes, cache restore/save time, critical path and flakes. Remove or combine redundant expensive tests after preserving their unique failure detection.

Start without compiler caching while builds are small. Add ccache only when saved compilation time exceeds restoration and maintenance cost. Key caches by OS/architecture, compiler identity, relevant flags/sanitizer mode and dependency identity; never share a CMake build tree across incompatible configurations. No cached test verdicts, secrets or private ROMs. Avoid unsafe ccache sloppiness. Always retain a clean release path and occasional cold-build checks. Current GitHub cache scopes reduce some poisoning risks; do not weaken those boundaries or treat cache contents as trusted release artifacts. [Q4][Q5]

## PR and release invariants

1. Work through PRs, with unique stable required-check names and the currently tested revision. Prefer repository auto-merge once reviews required by actual policy and all checks are satisfied. Do not use administrator bypass to meet an automation target.
2. One required aggregate gate runs with `always()` and enumerates expected job results. It fails on failure, cancellation, missing result or an unexpected skip. Deliberately optional jobs need an explicit applicability rule. GitHub treats conditionally skipped jobs as successful, while path-filtered workflows may remain pending; simple “green-looking” UI is insufficient. [Q6]
3. Require the appropriate current head/merge-group revision, not a past branch success. Current GitHub rules also require an eligible event: job checks from `workflow_dispatch` do not satisfy protected PR checks even on the exact head SHA. Use ordinary `pull_request` CI; an explicit dispatch is not a substitute. If a merge queue is enabled, CI handles `merge_group`. Validate the actual merged source revision before release, because PR merge refs and final source commits need not be identical. [Q6][Q7]
4. Use release-please manifest mode with a simple version source consumed by CMake; squash PR titles follow Conventional Commits. Pin the action to a reviewed full commit SHA with an explanatory version comment. Keep release PR generation separate from the proof that a binary is publishable. [Q8]
5. **Current token behavior matters:** GitHub's current documentation says `GITHUB_TOKEN`-created/updated PRs on `opened`, `synchronize` and `reopened` produce approval-required workflow runs. Push/release event chaining is still suppressed; explicit `workflow_dispatch`/`repository_dispatch` are exceptions. Release-please's README still describes a broader suppression rule. Follow GitHub's event documentation and test the actual repository flow. [Q8][Q9][Q10]
6. For unattended release PR CI, prefer a short-lived installation token from a GitHub App scoped to this repository and the exact required permissions. This fits the user's authorization to merge/release after gates pass. A fine-grained PAT is a fallback with rotation cost; never create a broad personal token by default. No App credential is assumed to exist. [Q10]
7. Normal PR workflows run with `pull_request`, read-only permissions and no secrets. Never run fork-controlled build code, configuration, downloaded executables or artifacts in a privileged `pull_request_target`/`workflow_run` job. Use hosted ephemeral runners for untrusted submissions; a private performance machine does not run arbitrary PR code. Pin third-party actions and update pins through reviewed dependency PRs. [Q11][Q12]
8. Default workflow permissions are read-only; grant release writes only to publication jobs. Mint App tokens only where needed. Avoid storing credentials in checkout configuration. Pass untrusted PR titles/paths through structured APIs or environment data rather than interpolated shell programs. [Q12]
9. Release source SHA, package build SHA, manifest SHA and successful verification SHA must agree. If release-please acts on a newer branch tip or returns a different revision, stop publication and validate that revision. Never build from moving `main` then attach binaries to an unrelated tag. Stage a draft/candidate until artifacts and smoke evidence are ready; publish only after the gate. [Q8 plus proposed project invariant]
10. Release workflows consume artifacts from the trusted build run tied to that SHA, verify hashes and provenance, and smoke the downloaded/unpacked bytes. Do not rebuild untested binaries after a successful packaging check. Release publication is idempotent; never overwrite an existing semantic-version tag or silently replace a published asset.

Automated gates replace routine human UAT where there is repeatable evidence. A required GitHub approval or missing external credential is an actual remaining setup condition, not a reason to pretend delivery is automatic. **Stop after each GSD phase** with evidence and the next command: within-phase PR/merge/release automation does not authorize starting the next phase.

## Performance baselines with honest tails

| Measure | Workload / reporting rule | Gate policy |
|---|---|---|
| Core throughput | ns per emulated second/tick and realtime multiplier, broken out by model/speed and CPU/PPU/APU workload | Paired candidate/base comparisons on the same controlled machine |
| Frame execution | Median, p95, p99, maximum and deadline misses for fixed scripted workloads; include sample count | Prevent sustained regressions; tail gates only after variability is established |
| Playback quality | Underruns, queue occupancy, dropped presentation frames, audio drift and device-recovery behavior | Host integration soak, separate from headless throughput |
| Input latency | Timestamped host input through presentation; distinguish software estimate from measured physical output | No input-to-photon claim based solely on function timing |
| Memory | Instance/ROM memory, peak RSS, state size, rewind budget, allocation count in steady stepping | Hard resource limits and no unexpected recurring allocation; track deltas |
| Persistence | State encode/decode and battery-save duration, failure recovery, malformed-state rejection | Correctness first; measure realistic sizes |
| Build/DX | Clean and incremental build time, first-test latency, PR wall time, runner minutes, package size | Set budgets after observing representative builds |
| Correctness/observability | Pass/fail inventory by model; debug-disabled/enabled overhead, retained trace bytes | No compatibility “percentage” without fixed denominator and no claim of zero tracing cost without measurement |

Benchmark fixed fixture hashes, model/boot configuration, input schedule, emulated duration, audio configuration, output checksums and warm-up policy. Record compiler/version/flags, CPU/OS, governor/power/thermal state where available, raw samples and Git SHA. Keep correctness checks outside the timed inner section while still proving equivalent output. Do not compare sanitized and release timings. Repeat base and candidate in alternating order to expose drift; shared hosted-runner timings are advisory until controlled variance supports a gate. Compiler, CPU scheduling and frequency changes are documented variance sources. [Q13]

The requested p99.999 is a long-term tail question, not a useful short-PR promise. A 100,000-frame sample has only about **one observation** in its upper 0.001%; it cannot establish a stable tail estimate. For independent identically distributed deadline outcomes with zero failures, the exact one-sided 95% upper failure bound is `1 - 0.05^(1/n)`; reaching approximately `10^-5` needs about 300,000 observations. At roughly 60 frames/s this is about 83 minutes, and correlated frames/thermal cycles weaken that inference. This is a statistical derivation from the binomial model, not a GabbaBoy performance result. Prefer measured p99, maxima and deadline-miss counts in routine work, with long device-specific soaks and confidence bounds for rarer claims. [Q14]

Use a simple scalar interpreter and clear scheduling as the reference. A performance change needs a profile, output-equivalence evidence and a repeatable gain; keep improvements reversible. Maintain an explicit performance budget per workload, then ratchet it when supported by data. Do not change golden outputs or relax thresholds merely to make an optimization pass.

## Release early, then add infrastructure when justified

1. **Foundation:** headless core package, external consumers, licensed smoke fixture, CI gate, versioned source/core archive and CI macOS artifact. Public wording says foundation preview until gameplay works. A downloadable artifact must have a documented location and retention policy; durable GitHub release assets are preferable for user testing.
2. **First playable DMG slice:** small SDL player, downloadable native macOS archive, save handling, version/source metadata and packaged smoke. Automate unsigned development previews first, explicitly identifying their signing status and normal macOS launch constraints. Do not instruct users to disable Gatekeeper globally.
3. **Established delivery:** validated App credentials enable unattended release PRs; signed/notarized macOS releases only after the real Developer ID identity and credentials are configured. Inspect public signing identity for the user's privacy requirement. Use current Apple `notarytool`, verify notarization and staple where applicable. Add more platforms, libretro artifacts and stricter performance gates when their evidence exists. [Q15][Q16]

Source and core artifacts include license/third-party notices, checksums, toolchain/dependency manifest and the API/state-format compatibility policy. Release notes distinguish supported behavior, known limitations and experimental systems. CGB support must be evidenced separately from DMG. Reproducible build metadata is useful immediately; bit-for-bit reproducibility is a later verified property, not an initial assumption.

## Operations, documentation and maintenance

- Keep public documentation portable: no local usernames, absolute home paths, private repo details, account IDs, private fixture names or copied secrets. Scrub compiler source paths from distributed diagnostics where practical; inspect archive metadata and signing identity before publication.
- Local automation secrets belong in ignored `.env.local` with variable names documented in `.env.example`; CI secrets belong in repository/environment secrets with minimal scope. Never print or upload the local file. The core does not parse dotenv files or require credentials to build/run.
- Optional diagnostics stay local: bounded caller-provided trace buffers/sinks, stable event identifiers and emulated timestamps, disabled by default. Rate-limit errors and expose overflow counters. No core network telemetry, per-instruction string formatting, background exporter or forced metrics framework.
- Same-PR documentation updates are part of changed behavior: runnable quickstart, build presets, supported models/limitations, integration example, ownership/threading rules, battery-save/state compatibility and troubleshooting. Compile examples and exercise documented commands where those are durable contracts.
- At every phase close: triage relevant open issues/PRs and scheduled failures, reconcile the compatibility ledger, review the weakest measurable quality dimension, update near/next/later roadmap and lessons with source/revision/evidence/revisit trigger, then stop for the requested phase boundary.
- Remove flaky tests only after preserving their unique signal or explicitly documenting the gap with an owner and deadline. Avoid automatic retries masking failures. Promote every useful minimized fuzz bug and integration regression into the cheapest reliable permanent test.
- Cross-project lessons are hypotheses until validated in GabbaBoy. Record the failure mechanism and regression that prevents recurrence; do not copy large CI matrices, databases, web frameworks or frontend architecture into this C core merely because they worked elsewhere.

## Sources

All retrieved 2026-10-02; confidence MEDIUM under the research seam. GitHub/Apple policy pages are living documents and must be revisited at implementation. No source establishes GabbaBoy's future compatibility or performance.

- [Q1 — AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html)
- [Q2 — UndefinedBehaviorSanitizer checks and recovery](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html)
- [Q3 — LLVM libFuzzer guidance and status](https://llvm.org/docs/LibFuzzer.html)
- [Q4 — ccache manual and correctness tradeoffs](https://ccache.dev/manual/latest.html)
- [Q5 — GitHub cache scopes and untrusted-trigger restrictions](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching)
- [Q6 — GitHub required checks, skips and merge queues](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)
- [Q7 — GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [Q8 — release-please action configuration and outputs](https://github.com/googleapis/release-please-action)
- [Q9 — Current GITHUB_TOKEN event exceptions](https://docs.github.com/en/actions/concepts/security/github_token)
- [Q10 — Triggering workflows, App tokens and PR approvals](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
- [Q11 — Risks of privileged PR workflows](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)
- [Q12 — GitHub Actions secure use, permissions and pinning](https://docs.github.com/en/actions/reference/security/secure-use)
- [Q13 — Google Benchmark variance guidance](https://github.com/google/benchmark/blob/main/docs/reducing_variance.md)
- [Q14 — NIST binomial confidence intervals](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)
- [Q15 — Apple notarization workflow](https://developer.apple.com/documentation/security/customizing-the-notarization-workflow)
- [Q16 — Apple Developer ID and distribution](https://developer.apple.com/developer-id/), [code-signing certificate identity](https://developer.apple.com/library/archive/documentation/Security/Conceptual/CodeSigningGuide/Procedures/Procedures.html) (archived identity explanation)
