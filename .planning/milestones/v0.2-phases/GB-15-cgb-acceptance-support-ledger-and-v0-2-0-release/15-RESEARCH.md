# Phase 15: CGB Acceptance, Support Ledger and v0.2.0 Release — Research

**Researched:** 2026-10-16  
**Domain:** Game Boy Color acceptance evidence, support-ledger validation, installed package consumers, bounded fuzz/performance receipts, GitHub release delivery  
**Confidence:** MEDIUM overall; high for inspected repository contracts, medium for current upstream/tool observations. Execution gates remain open.

<user_constraints>
## User Constraints


### A. Scope, reuse and dependencies

- **D-01: Close the four release requirements without reopening completed phases.** Reuse source-qualified research, corpus membership, exact-signature dispositions and completed UAT. Run current integration/regression/package checks where Phase 15 changes reach them; do not rerun prior GSD verification workflows merely because a new phase exists. Known failures remain visible; unexpected regressions block readiness.
- **D-02: Prefer small original local helpers and existing machinery.** Carry D-096 forward: another small copy can be better than another dependency when its semantics are inspectable. Reuse matching helpers; copied third-party code still needs rights and notices. No new runtime dependency, benchmark package, report registry, dashboard, service or parallel CI matrix is justified. Any necessary tool dependency needs an explicit capability, pinned provenance and transitive/maintenance cost comparison.

### B. CGB game evidence and its explicit fallback

- **D-03: Attempt one bounded Rebound admission and acceptance route.** Use upstream source `DevEd2/Rebound` at `cc2966e1643d480d0780fb6cc5b9ef53d5ef6898` as the candidate to audit. It is a native-CGB/MBC5 candidate with source-visible level/screen/coin state. This is a research choice, not admission. Reconcile the milestone's older candidate digest `195765b8ca3b0fb7d37b7b92d0242d6c7e01ec71f27f93e565fa081e449cbb92` with the exact source and tool recipe; do not assume they correspond. Pin a working build toolchain rather than adding latest-version requirements.
- **D-04: Apply GAME-01 rights and reproducibility gates before admitting bytes.** Require source commit, all code/runtime/submodule/asset rights and notices, exact output digest/size, bounded rebuild recipe, tool identities, boot/model/mapper labels and a reproducibility statement. A repository-wide MIT label alone is insufficient asset evidence. Inspect rights from primary sources; do not contact authors or copy uncertain bytes into required CI. A successful rebuild proves bytes, not redistribution permission or gameplay.
- **D-05: Prove meaningful native-CGB progress independently of output digests.** Derive a game-native objective from pinned source, with digest-bound addresses/ROM anchors. It must be false in title/attract state and during passive movement, hold after meaningful scripted input at two consecutive frame boundaries, and fail for no-input and wrong-input controls at the same emulated-time budget. Reuse timed input, bounded public runs and guest-memory observations. Record model, CGB execution mode, boot policy, script/ROM hashes, objective state, master time, canonical RGB555 frame digests and non-silent PCM digest. Digests are regression observations; neither a screenshot nor CTest evaluator success establishes progress or hardware accuracy.
- **D-06: Resolve the small runner seam before promising acceptance.** The current progress-capture path is Libbet/DMG-frame bound and can reject a CGB profile as `frame-unsupported-profile`; the RGB555 oracle elsewhere does not automatically fix it. Planning must prototype a bounded native-CGB predicate/capture adaptation without weakening Libbet's ROM/anchor binding or altering its frozen results. If admitted and proven, run the positive and intended failing controls through existing headless Linux/macOS/Windows lanes; extend an existing macOS packaged-player smoke when the same script exercises the shipped path. No new UI or perceptual approval is required.
- **D-07: Use the explicit absence alternative when any game gate cannot close.** After the focused rights/build/predicate/runner feasibility work, an unresolved gate or need for a broad core rewrite ends this attempt. Admit no uncertain ROM and state **“No CGB game-level evidence exists”** in the ledger, release notes and relevant product claims, with a structural check that rejects contrary claims. This satisfies the documented CGB-11 alternative; it does not satisfy fuzz/performance or other release requirements. Rex Runner, GBHack and Aevilia remain considered alternatives, not a mandatory fallback search. Do not assign the owner a legal reading or manual gameplay test to avoid the explicit absence route.

### C. Support ledger and adopter contracts

- **D-08: Author a current v0.2.0 ledger rather than concatenate phase history.** Fold `docs/support/unreleased.md` into `docs/support/v0.2.0.md` during execution, reconciling chronological and pending statements against actual producers. Include DMG-CPU-B and CGB-CPU-E, native/compatibility modes, boot path, mapper/type/size/save/RTC/rumble matrix, model-specific evidence, source revisions, known issues and exclusions. Separate implemented capability from the profile/mode on which evidence was executed. Do not imply all combinations have game or hardware proof.
- **D-09: Keep corpus, assertion and game evidence separate.** Preserve the frozen corpus identities and independent author expectations. Report eligible, attempted, completed/executed, actual guest pass/fail, matched expected failure and excluded/not-run reasons per suite and model/mode; retain assertion totals where relevant. The current 107/25/82 receipt is historical at its producer until a fresh candidate receipt confirms it. A game acceptance is a separate evidence item, not a way to inflate the test-ROM numerator. Preserve exact xfail signatures, promotion rules, rights/model exclusions and physical UNKNOWN/POLICY labels; missing required cases, changed signatures and unexpected passes fail closed.
- **D-10: Version ledger validation without weakening v0.1.** `verify-support-ledger.py` currently hardcodes schema 1, one DMG model, three case IDs, four manifests and zero failures. Add a distinct bounded v0.2 schema/version validation path, preserving the existing v0.1 tagged-ledger and sidecar behavior. Bind v0.2 membership/counts/dispositions to the admitted inventories and complete current receipt, not arbitrary caller-supplied totals. The v0.2.0 release must select **exactly `docs/support/v0.2.0.md`**; the existing newest-ledger-at-or-below-tag fallback must not silently ship v0.1 claims. Preserve the useful fallback for later fixes-only patch releases within a validated support scope.
- **D-11: Reuse both installed consumer programs as behavioral proof.** C and C++ already exercise profile selection, probe/info, CGB-only-on-DMG/PGB handling, RGB555 and stride/profile errors, RTC catch-up and negative/null/no-RTC calls, plus speed/HDMA positive and failing twins. Close only demonstrated gaps. Build and run each through relocated `find_package(GabbaBoy)`/`GabbaBoy::core`, outside checkout/build trees, then repeat against downloaded candidate package bytes on the existing platform lanes. Symbol presence or an in-tree build alone is insufficient. No new public API, C++ wrapper, stable ABI promise or widened fixture install allow-list is required.
- **D-12: Update claims, examples and notices together.** Reconcile README, public API/native integration, cartridge/save/RTC, audio/CGB, player/preview/limitations, game acceptance, release/download documentation, third-party notices and changelog links. Preserve the 21-byte RTC block and v1/v2 envelope semantics, host-owned wall-clock policy and existing save recovery limits. An installed native consumer is not live Playstead integration. Runner labels are tested configurations, not minimum OS/all-architecture promises. Raw RGB555 and dummy SDL smoke establish no perceptual color/audio or physical-device claim.

### D. Fresh performance and fuzzing evidence

- **D-13: Compare DMG against the explicit `v0.1.0` release baseline.** The baseline tag resolves to `e30d168f7fc61de8db0a3801e7b1736362912cb7`. Its measurement source contains the same `original-wram-tracer-1m-half-dots-v1` contract; execution must still verify workload and digest on both binaries. Build clean baseline and candidate sources on the same host with matching compiler/configuration/flags. Bind actual source, binary and build identities; reject `unknown` or supplied labels unsupported by those identities. Use the existing interleaved A/B mode, three warmups and thirty paired samples by default, with output digest, raw samples, hardware class, uncertainty and noise label. If the old binary fails the contract, use a documented measurement-only compatibility harness linked against the untouched old core; never relabel new-core results as old evidence.
- **D-14: Treat performance as measured evidence, with an explicit regression disposition.** Refresh existing candidate trace/no-trace, memory/resource and applicable DMG/CGB baselines without expanding into speculative optimization. Preserve correctness digests. Apply the existing +5% review trigger with its uncertainty check; investigate and record material regressions and the release disposition, rather than silently ignoring them or optimizing to a noisy percentage. The loaded-host Phase 10 6–7% observation is historical advisory context, not this comparison. Publish privacy-safe hardware class and sanitized receipts, not host names or paths.
- **D-15: Require an actual bounded libFuzzer campaign for SHIP-11.** Current Linux sanitizer CI does not pin Clang, and `run-bounded-fuzz.sh --fast` may succeed while reporting unsupported; neither guarantees refreshed fuzzing. Route a matching Clang/libFuzzer+ASan/UBSan build and the existing bounded exploration path through an eligible host, preferably the existing Linux sanitizer lane. Keep explicit input/operation/emulated-work/time/RSS/worker bounds (existing exploration is 60 seconds), dictionary and seed identities, source/build/binary identity, execution result and any minimized regression artifacts. Seed the existing model/mapper/RTC/CGB seams. Keep deterministic hostile regressions and intended failing oracle controls, but do not describe them as a campaign or claim the 64 KiB fuzz-input envelope explores every 8 MiB ROM boundary.
- **D-16: Unavailability changes the execution route, not the requirement.** A local unavailable libFuzzer runtime routes to hosted Clang evidence. If no eligible host produces a real campaign receipt, leave SHIP-11 and release readiness open; do not downgrade it to an unsupported success or routine owner UAT. Keep candidate, tested PR head, squash merge and eventual tag revisions distinct. Reconcile performance/fuzz receipts with the actual tagged source and covered-input identities; regenerate when those inputs change. Never relabel a Phase 14 receipt as a new revision.

### E. Exact-tag delivery, automation and recovery

- **D-17: Keep release-please and the existing staged exact-tag flow.** Finish the Phase 15 branch/PR with reviewed changes and required exact-head checks, then refresh the existing version PR #70 against final main before its own checks/merge. Reuse version/changelog review, exact tag/source checkout, unpublished draft, platform builds, downloaded C/C++ and macOS player smoke, support/performance sidecars, final gate, publication and API readback. Extend the current generic sidecar/performance mechanisms for D-10/D-13/D-15; they do not already provide a v0.2 ledger, v0.1 comparison or guaranteed fuzz campaign. Do not promote expiring PR-head preview artifacts as tag-built release bytes.
- **D-18: Resolve live run approvals within existing authorization.** On 2026-10-16, PR #70 at `aaeb039f339513021c288454f257f684e1c547c9` against main `c771b1b9c143d7589f8bb40c163c2e9f89ca1168` was BLOCKED; its three PR-event workflows were `action_required`, not passed or failed. An authorized agent should attempt the supported approval/recovery route and then inspect actual results at the final head. A narrowly scoped GitHub App token is a future option only if unattended runs require it and credentials are provisioned; do not introduce a credential dependency now. Hand off only an actual permission/credential/external-approval limitation, with the exact smallest action. Never bypass branch protection, substitute a dispatch check, or treat skipped/stale/local checks as protected-PR success.
- **D-19: Bind publication to every identity and distributed byte.** Preserve reviewed PR head, merge commit, tag target, source receipt, workflow run/attempt/job, build/config, exact asset names/sizes/digests and downloaded consumer evidence. Refresh source-receipt validation for final version changes, v0.2 ledger selection, comparison and campaign evidence; reject omitted, duplicate, stale or partial records. Keep release inputs trusted and bounded, token permissions scoped and public artifacts allow-listed. Retain the current Linux x64/macOS arm64/Windows x64 core plus macOS arm64 player matrix. Unsigned/not-notarized remains the declared macOS state; signing is not silently added as a release gate.
- **D-20: Make retries reuse the same unpublished identity.** Revalidate the same draft ID, tag and source; reuse byte-identical assets/receipts only. A partial or changed attachment set requires explicit safe recovery, never blind overwrite. After a publication or readback error, inspect actual release state first. Published assets and tags are not replaced to make a check green; use a later corrective version if needed. Existing phase authorization covers the normal reviewed/tested release path; do not add a confirmation-only checkpoint merely because a template mentions publishing.
- **D-21: Close the source-archive question by retaining licensed fixture source.** Keep D-051's GitHub automatic source archive inclusion, audit the admitted fixture rights/notices and document that source archives differ from product packages. Keep binaries/packages fixture-free under existing allow-lists. Do not add `export-ignore` or a new archive/promotion mechanism without an actual demonstrated problem; source/PR proof alone is not archive-content proof. Exercise a bounded archive-content/notice contract with a missing/unlicensed-file control where Phase 15 makes a distribution claim.

### F. Verification, research gates and stopping

- **D-22: Keep zero routine human UAT and economical recurring CI.** D-069 remains the default. Every deliverable carries an executable check and a negative control that fails for the intended defect; documentation uses semantic/symbol/claim contracts. Cover game false positives/absence, ledger v1/v2 and wrong-tag fallback, xfail inflation, missing/duplicate/narrowed membership, stale source/build/campaign identities, unsupported fuzz masquerading as a run, incompatible benchmark pairs, missing downloaded consumer evidence and partial release recovery. Register recurring checks in existing CTest, sanitizer, reproduction and package paths with exact inventory membership. Keep one-off discussion/handoff checks local; no GSD runtime installation or duplicate full matrix in CI. SUMMARY coverage uses the enforced block schema and `human_judgment: false` for machine-decidable work. A genuine hardware/perceptual limitation is a declared limit unless the phase requires that evidence, not an invented owner checkpoint.
- **D-23: LIGHT planning research must resolve five concrete gates.** (Q1) Rebound rights/build/digest plus meaningful native-CGB predicate feasibility, or the explicit absence route; (Q2) bounded v0.2 ledger/schema/sidecar dispatch preserving v0.1 and the exact new ledger selection; (Q3) fresh relocated/downloaded consumer and current documentation/notice coverage, including source archive policy; (Q4) matching `v0.1.0`/candidate A/B provenance and an actual bounded Clang campaign route/receipt; (Q5) final version-PR approval/event/protection, tag/source, added release evidence and retry compatibility. Reuse the three discussion topic notes and prior implementation evidence. Prototype only the seams whose uncertainty changes a plan. No repeated ecosystem survey, full game hunt or broad emulator rewrite is created by these gates.
- **D-24: Stop at discussion with one durable route.** Completed stage is **Phase 15 discussion**. Next is **Phase 15 — CGB Acceptance, Support Ledger and v0.2.0 Release, planning**, `/gsd-plan-phase 15`. Planning and execution remain unstarted; four requirements remain pending. Keep `workflow.auto_advance` and `workflow._auto_chain_active` false. Do not plan, implement, merge PR #70, publish/tag a release or begin another milestone in this invocation. Phase 15 execution must later stop at its own phase boundary.

### Agent discretion and diminishing returns

Helper names/layout, schema details within the bounded contracts, compact test grouping, measurement storage and plan sizing are delegated. Adopt narrow evidence-backed corrections without repeating owner approval. Reopen a choice only for a concrete counterexample, changed requirement, failed discriminator/prototype, unavailable evidence or owner direction. Stop widening the role matrix when another lens changes no observable behavior, risk, evidence boundary or check.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research support |
|---|---|---|
| CGB-11 | One rights-clear CGB game passes a game-level acceptance run in the same style as GAME-02, or the ledger explicitly states that no CGB game-level evidence exists. | Existing bounded acceptance patterns, candidate feasibility result, and authorized explicit-absence contract. [VERIFIED: .planning/REQUIREMENTS.md:46] |
| SHIP-09 | The v0.2 support ledger names DMG-CPU-B and CGB-CPU-E, the mapper matrix, evidence class, corpus revisions, denominators, failures, exclusions and known issues. | Current schema/sidecar limitation and bounded v0.2 dispatch recommendation. [VERIFIED: .planning/REQUIREMENTS.md:50] |
| SHIP-10 | Installed C and C++ consumers exercise the new public API (profile selection, ROM probe, RGB555 frames, RTC catch-up), and API, cartridge/save, integration and third-party-notice documentation is current. | Existing consumer coverage and relocated package workflow; close verified gaps and refresh docs/notices. [VERIFIED: .planning/REQUIREMENTS.md:51] |
| SHIP-11 | A qualified exact-tag v0.2.0 release ships with refreshed fuzzing and performance baselines, including a measured DMG performance comparison against v0.1. | A/B identity controls, actual bounded Clang/libFuzzer campaign, and exact-tag provenance/release checks. [VERIFIED: .planning/REQUIREMENTS.md:52] |

All four requirements are pending in current planning state. This research does not claim release readiness or game qualification. [VERIFIED: .planning/STATE.md:33-50]
</phase_requirements>

## Summary

Plan Phase 15 as a bounded evidence-and-delivery phase using existing acceptance, support-ledger, package-consumer, benchmark, fuzz, and staged-release machinery. The strongest scope control is the explicit CGB-11 absence option: pinned Rebound source did not build with the tested official RGBDS release, so do not plan unverified ROM admission or a broad emulator rewrite. Its root MIT license alone does not establish rights for every asset. If rights/build/objective gates cannot close with admissible evidence, record “No CGB game-level evidence exists” and keep game qualification claims absent. [VERIFIED: Phase 15 CONTEXT D-03–D-07; private prototype and source inspection]

Preserve v0.1 ledger selection and sidecar behavior while adding a narrowly validated v0.2 path that selects exactly docs/support/v0.2.0.md for tag v0.2.0. Reuse both installed C/C++ behavioral consumers, but run them against relocated package installations and downloaded candidate assets; source inspection is not execution evidence. SHIP-11 requires a real bounded Clang/libFuzzer campaign and a paired measurement against the exact v0.1.0 baseline commit. Local probes show this environment cannot provide the fuzz runtime, so host availability and final-revision receipts are execution gates. [VERIFIED: tests/scripts/verify-support-ledger.py:17-29,98-110,137-145; tests/consumers/c/main.c:66-168; tests/consumers/cpp/main.cpp:593-694; tests/scripts/run-bounded-fuzz.sh:8-21,80-96; Phase 15 CONTEXT D-10–D-16]

**Primary recommendation:** Plan small, independently observable contracts around existing scripts and CI. Preserve the v0.1 validator path; fail closed on wrong-version or stale evidence; use CGB absence if focused feasibility remains unresolved; require actual downloaded-consumer, A/B, fuzz, protected-PR and exact-tag receipts before marking requirements complete. No new dependency is justified by inspected seams. [VERIFIED: AGENTS.md:7-33; Phase 15 CONTEXT D-01–D-24]

## Architectural Responsibility Map

| Capability | Primary tier | Secondary tier | Rationale |
|---|---|---|---|
| Native-CGB game predicate and bounded runner capture | Test/acceptance harness | Portable emulator core | Existing headless runner owns input, frame capture and guest-memory observation; do not change core semantics merely to force a candidate. [VERIFIED: src/runner/acceptance.c:181-204,731-761] |
| Versioned support ledger and selection | Validation scripts / release workflow | Documentation | Script validates schema and emits sidecars; tag workflow selects shipped ledger. [VERIFIED: tests/scripts/verify-support-ledger.py:17-29,98-110,182-220; .github/workflows/release.yml:340-366] |
| Installed consumer behavior | CMake package boundary | C and C++ executables | Consumers must locate installed package from relocated prefix and exercise packaged bytes. [VERIFIED: tests/CMakeLists.txt:1631-1674; .github/workflows/release.yml:340-366,618-634,761-780] |
| Performance and fuzz evidence | Build/test host | Receipt validator and release sidecar | Toolchain, binary, source revision and workload identity must match evidence to shipped revision. [VERIFIED: tests/scripts/measure-release-baseline.sh:20-30,48-58,98-149; tests/scripts/run-bounded-fuzz.sh:80-96] |
| Release identity and publication | Protected GitHub PR / release workflow | Release asset consumers | PR-head checks, merged source, tag target and downloaded asset identities determine release evidence. [VERIFIED: Phase 15 CONTEXT D-17–D-20; read-only GitHub observations] |

## Standard Stack

| Tool or component | Current evidence | Phase use |
|---|---|---|
| CMake and CTest | Project requires CMake 3.25 or newer and configures C17 with extensions disabled. [VERIFIED: CMakeLists.txt:1,19-29,32-50] | Extend existing tests and package workflows; retain current framework. |
| Python validation scripts | Existing support-ledger and release validators are Python scripts. [VERIFIED: tests/scripts/verify-support-ledger.py:1-29; tests/scripts/run-bounded-fuzz.sh:1-8] | Add narrow schema, identity and negative-control checks to existing scripts. |
| Clang/libFuzzer with ASan/UBSan | Local bounded-fuzz self-test reported “self-test=pass libfuzzer_runtime=unsupported deterministic_regressions=required”; exploration requires Clang fuzzer/address/undefined sanitizers. [VERIFIED: tests/scripts/run-bounded-fuzz.sh:8-21,47-78; current local execution] | Required for actual exploration; use eligible hosted runner if local compiler lacks runtime. |
| Existing C and C++ package consumers | Consumer executables already exercise selected public CGB behaviors. [VERIFIED: tests/consumers/c/main.c:66-168; tests/consumers/cpp/main.cpp:593-694] | Close demonstrated gaps and run against relocated/downloaded packages. |
| Existing GitHub release workflows | Release workflow has Linux, macOS and Windows asset/consumer paths. [VERIFIED: .github/workflows/release.yml:340-366,618-634,761-780] | Retain staged exact-tag workflow and attach validated evidence sidecars. |

No external runtime package or benchmark library is recommended; no package installation is part of this research.

**Standard validation command:** cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error. [VERIFIED: .planning/config.json:20-25,48-54]

## Architecture Patterns

### Evidence path

~~~text
Pinned source and rights
  -> bounded game build and objective feasibility
  -> admitted ROM plus positive/negative acceptance controls
     OR explicit no-game-evidence statement
  -> model/mode corpus and game evidence kept separate
  -> versioned support validator and sidecars
  -> relocated C/C++ consumers on downloaded package bytes
  -> matching benchmark and bounded fuzz receipts
  -> protected final PR, exact tag/source, draft assets and readback
~~~

Every boundary must bind evidence to exact source, build, ROM, model/mode, package or tag. Do not promote source inspection, local self-test, an old receipt, or a PR-preview artifact into final-tag evidence. [VERIFIED: Phase 15 CONTEXT D-09–D-20]

### Recommended structure and plan slices

Reuse current ownership boundaries:

- Acceptance: src/runner/acceptance.c and tests/acceptance/; adapt only the bounded CGB predicate/capture seam if the game gate closes.
- Ledger: docs/support/ and tests/scripts/verify-support-ledger.py; keep version dispatch explicit.
- Consumers: tests/consumers/c/, tests/consumers/cpp/, existing CMake package smoke and release workflow.
- Evidence: tests/scripts/measure-release-baseline.sh, bounded fuzz runner, and existing release/source-receipt validators.
- Docs/notices: update existing API, cartridge/save, integration, limitation, release and third-party notice documents together.

Paths and responsibilities are source-inspected; exact task grouping is a planning recommendation. [VERIFIED: source paths cited in this document]

### Version-dispatched ledger

The existing validator defines LEDGER_DIR as "docs/support"; the fixed case IDs are "mooneye-acceptance-instr-daa", "mooneye-acceptance-timer-tim00", and "mooneye-acceptance-timer-tim00-div-trigger"; and it checks schema_version against 1. [VERIFIED: tests/scripts/verify-support-ledger.py:17-29,98-110] Preserve these exact v1 values and behavior. Add a v0.2 branch with its own required shape and tag selection; do not let newest-at-or-below lookup ship v0.1 content for v0.2.0. [VERIFIED: tests/scripts/verify-support-ledger.py:40-53,98-110; recommendation grounded in CONTEXT D-10]

### Behavioral installed-package proof

Use CMake package discovery on a prefix moved outside the build tree and source checkout. Run existing C and C++ consumers against that installation, then repeat against downloaded candidate release assets. CMake’s official package manual describes relocatable consumption using relative package paths. [CITED: https://cmake.org/cmake/help/latest/manual/cmake-packages.7.html] Repository package smoke and downloaded asset paths already exist. [VERIFIED: tests/CMakeLists.txt:1631-1674; .github/workflows/release.yml:340-366,618-634,761-780]

### Source archive versus binary package

GitHub documents source archives as generated snapshots of repository content. [CITED: https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives] Keep licensed fixture sources/notices in source archives as CONTEXT directs, while separately ensuring product binary packages exclude fixtures. A repository source/PR check does not prove exact-tag archive contents. [VERIFIED: read-only archive inspection; Phase 15 CONTEXT D-21]

## Don't Hand-Roll

| Problem | Avoid | Use |
|---|---|---|
| Ledger parsing and tag selection | Second informal parser or release-time newest-file glob | Existing validator/sidecar path with explicit version dispatch and exact v0.2.0 selection. [VERIFIED: tests/scripts/verify-support-ledger.py:40-53,182-220] |
| Evidence denominators | Manually transcribed totals | Bind counts/membership to manifests and current receipts; test missing/duplicate membership. [VERIFIED: tests/scripts/verify-support-ledger.py:137-145; CONTEXT D-09/D-10] |
| CGB progress | Screenshot-only checks or generic frame hash | Source-derived objective predicate with same-budget no-input and wrong-input controls; use digests as regression observations only. [VERIFIED: CONTEXT D-05/D-06; src/runner/acceptance.c:731-761] |
| Benchmarking | Custom framework or manually supplied identity labels | Existing interleaved script, strengthened to bind actual source/build/binary identity. [VERIFIED: tests/scripts/measure-release-baseline.sh:20-30,98-149] |
| Fuzzing | Deterministic fast checks presented as exploration | Existing bounded exploration with matching Clang/libFuzzer/ASan/UBSan and campaign receipt. [VERIFIED: tests/scripts/run-bounded-fuzz.sh:53-96] |
| Source archives | Custom archive promotion without evidence of a problem | GitHub generated source archive plus exact-tag content/notice contract. [CITED: GitHub source archives; CONTEXT D-21] |

## Common Pitfalls

1. **Build success is not rights clearance or gameplay proof.** Pinned Rebound failed with tested RGBDS v1.0.1; no ROM digest was produced. Root MIT does not establish per-asset rights. If focused gates stay open, use explicit CGB absence. [VERIFIED: private candidate build experiment and source inspection; CONTEXT D-03–D-07]
2. **Ledger fallback can regress v0.1 or mis-select v0.2.** Preserve old path with a distinct v0.2 dispatch; test missing exact v0.2 file, wrong tag and v1 compatibility. [VERIFIED: tests/scripts/verify-support-ledger.py:98-110; CONTEXT D-10]
3. **Totals can conceal denominator changes.** Corpus attempted/executed/pass/fail/xfail/exclusion and game evidence are distinct. Historical 107/25/82 is not a Phase 15 receipt. [VERIFIED: .planning/STATE.md:33-50; CONTEXT D-09]
4. **In-tree build is not installed consumer evidence.** Symbol coverage or package smoke alone does not prove relocated/downloaded behavior. [VERIFIED: tests/CMakeLists.txt:1631-1674,2984-3003; CONTEXT D-11]
5. **Unsupported fuzz is not a campaign.** Local self-test explicitly reports unsupported; --fast can pass deterministic tests without exploration. Require a real campaign receipt. [VERIFIED: tests/scripts/run-bounded-fuzz.sh:47-78; current local execution]
6. **Benchmark labels can be false or incomplete.** Existing script can emit "unknown" when build metadata is missing; require identities grounded in actual artifacts and matching workload/digest. [VERIFIED: tests/scripts/measure-release-baseline.sh:48-58,98-149]
7. **Action-required is neither pass nor failure.** On 2026-10-16 PR #70 workflows were action_required, and required branch checks were unresolved. Use supported approval/recovery and inspect final-head checks; never bypass protection. [VERIFIED: live read-only GitHub observation; CONTEXT D-18]
8. **Preview or stale receipts do not prove exact-tag assets.** Bind merge commit, tag target, source receipt, workflow attempt, build, assets and downloaded consumer evidence. Inspect release state before retry. [VERIFIED: CONTEXT D-17–D-20]

## Code Examples

Existing runner behavior offers a narrow discriminator: CGB profile callback sets the exact error "frame-unsupported-profile", while a separate RGB555 copy/digest route exists. Preserve the error as a negative control if adding bounded CGB capture. [VERIFIED: src/runner/acceptance.c:181-204,731-761; tests/acceptance/CMakeLists.txt:417-419]

Current bounded exploration uses exact limits: -max_len=65536, -max_total_time=60, -timeout=2, -rss_limit_mb=512, -jobs=1, and -workers=1. [VERIFIED: tests/scripts/run-bounded-fuzz.sh:80-96] Keep deterministic hostile-input regression checks separate from an actual libFuzzer campaign.

The benchmark contract uses workload "original-wram-tracer-1m-half-dots-v1" and expected digest "4c7a57ff3d50d228"; default sample count is 30 with 3 warmups. [VERIFIED: tests/scripts/measure-release-baseline.sh:20-30,48-58] Reuse the contract and bind source/build/binary identity before interpreting results.

## Validation Architecture

### Test framework

| Property | Value |
|---|---|
| Framework | CMake/CTest; core uses C17. [VERIFIED: CMakeLists.txt:1,19-29,32-50] |
| Config | CMakeLists.txt, CMakePresets.json; validation preset in .planning/config.json. [VERIFIED: CMakeLists.txt:1-50; .planning/config.json:20-25,48-54] |
| Quick run | cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error |
| Focused checks | python3 -I tests/scripts/verify-support-ledger.py --self-test; bash tests/scripts/run-bounded-fuzz.sh --self-test |
| Full suite | Configured phase1 build and CTest; also run platform/package/release evidence gates. [VERIFIED: .planning/config.json:20-25,48-54] |

Support-ledger self-test passed in this research session. Fuzz self-test passed while reporting runtime unsupported. Neither proves Phase 15 completion. [VERIFIED: current executions]

### Requirement to observable check map

| Requirement | Observable check | Automated negative control | Execution state |
|---|---|---|---|
| CGB-11 | Either rights/build/objective-gated native CGB acceptance receipt with positive and same-budget no-input/wrong-input controls, or exact explicit absence statement in ledger and release claims. | Remove absence statement or submit title/passive/wrong-input observation; contract must fail. | Candidate build feasibility tested and failed; rights/objective/runner qualification remain open. |
| SHIP-09 | v0.2 ledger has required model/mode, mapper, evidence class, revisions, counts/denominators, failures, exclusions and issues; sidecar matches exact validated ledger. | Missing exact v0.2 file; wrong schema/tag; omitted/duplicate inventory; inflated xfail; stale receipt; v1 regression. | Existing v1 validator inspected and self-tested; implementation/fresh receipt pending. |
| SHIP-10 | Relocated C and C++ consumers execute profile selection, ROM probe, RGB555 and RTC behavior against installed and downloaded package bytes; docs/notices/archive pass content contracts. | Missing consumer result/symbol; bad relocation; removed API doc/notice; fixture leakage into binary; missing source archive notice. | Existing tests/workflow inspected; no fresh downloaded package execution. |
| SHIP-11 | Exact-tag release carries a real bounded Clang/libFuzzer receipt plus paired DMG v0.1.0/candidate results with matching workload, source/build/binary identity, samples and uncertainty. | Unsupported runtime presented as campaign; source mismatch; unknown build identity; incompatible digest; stale receipt. | No campaign or new A/B execution; execution gates remain open. |

### Wave 0 needs and sequence

- Reuse CMake/CTest, Python scripts, C/C++ consumers and current workflows; no framework install or dependency needed. [VERIFIED: cited paths above]
- Add version-specific ledger fixtures before changing release dispatch: preserve v1 fixture; add v0.2 valid, missing, wrong-tag, stale, duplicate and inflated controls. [RECOMMENDATION grounded in validator contract and AGENTS D-069]
- Add machine-checkable claim and archive-content/notice contracts before updating docs. Include absent-game fixture if candidate gates remain open. [RECOMMENDATION grounded in CONTEXT D-07/D-21/D-22]
- Extend only necessary receipt validators to reject stale source/build/campaign/performance identities. Negative controls must fail through the real test entry point. [RECOMMENDATION grounded in AGENTS.md:7-21 and CONTEXT D-22]
- Execute package, fuzz, A/B and release checks only on final reviewed source/tag identities.

### Sampling and phase gate

Run focused Python and CTest checks per task. At integration, run full configured CTest and relocated/downloaded consumers. Before completion require the selected CGB-11 evidence alternative; valid exact v0.2 ledger and sidecar; refreshed docs/notices and source archive contract; paired performance receipt; actual bounded fuzz receipt; protected final-PR checks; exact tag/source/assets/readback evidence. These are automated deliverables rather than routine human UAT. Hardware/perceptual/credential limits remain declared limits or true external gates. [VERIFIED: AGENTS.md:7-33; CONTEXT D-22]

## Security Domain

Security enforcement is enabled. [VERIFIED: .planning/config.json:48-54] Applicable controls are bounded file/ROM inputs, digest/receipt validation, fail-closed release evidence, scoped workflow token permissions and fixture-free binary packages. [VERIFIED: AGENTS.md:22-33; CONTEXT D-04/D-15/D-19] This phase adds no authentication/session behavior; input validation, release-publication access control and artifact provenance integrity apply. Do not broaden privileges to make action-required workflows pass.

## Environment Availability

| Dependency | Available in research environment | Evidence / phase use |
|---|---|---|
| CMake | Yes, 4.4.3 | Existing build and CTest. |
| Ninja | Yes, 1.13.2 | Existing preset backend. |
| Apple Clang | Yes, 21.0.1 | Native build available; does not establish libFuzzer runtime availability. |
| Python | Yes, 3.14.4 | Existing validators and support self-test. |
| GitHub CLI | Yes, 2.101.0 | Read-only PR/check inspection; release event recovery remains external. |
| RGBDS | 1.0.4 installed; official 1.0.1 archive also tested privately | Candidate build probe. |
| Matching Clang/libFuzzer runtime | No, bounded runner probe says unsupported | Use eligible hosted runner; no fuzz waiver. |

Versions were observed locally during research. The private v1.0.1 candidate build is distinct from source inspection and future Phase 15 execution.

## Five LIGHT Gate Outcomes

| Gate | Outcome | Planning disposition |
|---|---|---|
| Q1 — rights/build/digest/objective/runner | Pinned Rebound source was built privately with official RGBDS v1.0.1 archive SHA256 2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645. Build failed with 494 assembler errors, including “syntax error, unexpected c” and “Strings as numbers must be a single charmap unit”; no ROM/digest resulted. Root MIT license does not prove every asset. | Plan explicit CGB absence unless execution resolves rights, reproducible build, source-derived objective controls and runner feasibility without broad rewrite. No ROM bytes copied into repository. |
| Q2 — v0.2 ledger and sidecars | Existing validator hardcodes schema 1, DMG model, fixed cases/manifests and sidecar generation. Self-test passes but does not test exact v0.2.0 selection. | Add distinct v0.2 validation/sidecar path and exact docs/support/v0.2.0.md selection; preserve v1 and test wrong-version/missing exact-ledger controls. |
| Q3 — consumers/docs/notices/archive | Existing C/C++ tests cover relevant API behavior and CI has relocated/downloaded consumer routes. Read-only archive inspection found fixture licensing/source documents; no export-ignore attribute on required docs. | Reuse consumers; close demonstrated gaps and validate downloaded package bytes. Refresh docs/notices; verify exact-tag source archive and fixture-free binary packages. No fresh package consumer run. |
| Q4 — baseline A/B and fuzz | Baseline tag resolves to CONTEXT commit e30d168f7fc61de8db0a3801e7b1736362912cb7; measurement workload string matches, but no Phase 15 paired campaign ran. Local fuzz self-test reports unsupported; CI fast path is not exploration. | Run paired baseline/candidate with 3 warmups/30 samples and identity/digest/uncertainty; execute real 60-second campaign on matching Clang/libFuzzer host. No dependency or waiver. |
| Q5 — PR/protection/tag/source/proof/retry | Read-only observation 2026-10-16: PR #70 open/blocked at head aaeb039f339513021c288454f257f684e1c547c9; three PR workflows action_required; protection required required-native, fixture-repro, preview-package-smoke. v0.2.0 tag/release absent. | During authorized execution, recover supported workflow event, inspect final-head checks, merge reviewed source, then verify exact-tag assets/receipts with same-identity retry. No approval, dispatch, merge, tag or release action in research. |

Historical/live observations are not release evidence. Implementation and hosted execution gates remain open.

## Project Constraints (from AGENTS.md)

- Target Game Boy and Game Boy Color only; do not claim unimplemented emulator behavior.
- Use identity-proven OpenGSD; stop after each phase, keep both auto-advance flags false, and hand off the exact next phase and command.
- Every deliverable needs an automated check and negative control; avoid routine manual UAT.
- Use phase branches and PRs when remote exists; merge only reviewed/tested revisions after protected checks. Do not bypass protection or treat stale/skipped/local runs as remote proof.
- Keep source, API docs, examples, tests and limitation notes synchronized; triage issues/PRs at boundaries and report access failures honestly.
- Keep portable C ownership/errors explicit and operations bounded. Guard ROM/save/state boundaries against overflow, truncation, excess work and partial mutation.
- Preserve portable serialization and distinguish hardware-backed, differential, metamorphic, regression and private-game observations with applicable scope.
- No boot ROMs, commercial images, unlicensed homebrew, private data or mandatory telemetry; third-party fixtures need redistribution rights and digest.
- Keep personal paths, emails, machine identifiers and secrets out of public artifacts. Maintain evidence-based research/index/decision/roadmap/lesson artifacts. [VERIFIED: AGENTS.md:5-33]

## Open Execution Gates

1. CGB-11 requires qualifying rights-cleared game evidence or exact explicit absence contract; candidate probe did not qualify a ROM.
2. v0.2 ledger, schema validation, sidecars, exact-tag selection and negative controls are unimplemented/unexecuted.
3. Relocated/downloaded C/C++ behavior and updated docs/notices/archive checks remain.
4. Fresh paired v0.1.0/candidate benchmark and actual bounded libFuzzer receipt do not exist.
5. PR #70 recovery, final protected checks, tag/build/source provenance, asset readback and retry remain.
6. CGB hardware/perceptual accuracy is not established by RGB555 digests or dummy output; preserve the evidence limit.

## Sources and Provenance

### Repository sources read

- .planning/REQUIREMENTS.md, .planning/STATE.md, .planning/PROJECT.md, .planning/research/SUMMARY.md, .planning/ROADMAP.md, Phase 15 context/continuation and three topic notes.
- AGENTS.md, .planning/config.json, CMakeLists.txt.
- src/runner/acceptance.c, tests/acceptance/CMakeLists.txt, C/C++ consumer sources, tests/CMakeLists.txt.
- tests/scripts/verify-support-ledger.py, tests/scripts/run-bounded-fuzz.sh, tests/scripts/measure-release-baseline.sh, tests/measure_core.c.
- .github/workflows/ci.yml and .github/workflows/release.yml; read-only PR/check/protection/release observations.

### External primary documentation

- [CMake packages manual](https://cmake.org/cmake/help/latest/manual/cmake-packages.7.html)
- [LLVM LibFuzzer](https://www.llvm.org/docs/LibFuzzer.html)
- [GitHub source archives](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives)
- [GitHub Actions event triggers](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
- Rebound candidate: [pinned source](https://github.com/DevEd2/Rebound/tree/cc2966e1643d480d0780fb6cc5b9ef53d5ef6898), [README](https://github.com/DevEd2/Rebound/blob/cc2966e1643d480d0780fb6cc5b9ef53d5ef6898/README.md), [build script](https://github.com/DevEd2/Rebound/blob/cc2966e1643d480d0780fb6cc5b9ef53d5ef6898/build.sh), [license](https://github.com/DevEd2/Rebound/blob/cc2966e1643d480d0780fb6cc5b9ef53d5ef6898/LICENSE).

## Metadata

**Confidence breakdown:**  
- Existing source seams and discrete values: HIGH, source files opened and cited.
- Private build/runtime probes: MEDIUM, executed during research but limited to tested toolchain/environment.
- Live GitHub status: MEDIUM, read-only snapshot on 2026-10-16 and subject to change.
- Requirement outcomes: OPEN; none claimed complete.

**Research date:** 2026-10-16  
**Valid until:** Recheck live PR/checks and toolchain at execution; source contracts remain valid until changed.

