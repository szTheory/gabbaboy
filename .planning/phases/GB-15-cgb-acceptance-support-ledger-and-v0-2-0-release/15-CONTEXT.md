# Phase 15: CGB Acceptance, Support Ledger and v0.2.0 Release - Context

**Gathered:** 2026-10-16
**Status:** Ready for planning; focused LIGHT research gates remain
**Method:** Owner-delegated consideration of every relevant area, three independent typed research investigations, primary-source checks and a parent adversarial reconciliation. Recommended choices are adopted under the owner's explicit instruction; no interactive answers, approval, gameplay result or release readiness is invented. Discussion only.

<domain>
## Phase Boundary

Deliver **CGB-11, SHIP-09, SHIP-10 and SHIP-11**: one rights-clear native-CGB game acceptance or an explicit absence statement; a model-qualified v0.2 support ledger; current installed consumers and adoption documentation; and an exact-tag v0.2.0 release with refreshed fuzzing and performance evidence, including a measured DMG comparison against v0.1.

Phase 14 is merged as PR #71 at `c771b1b9c143d7589f8bb40c163c2e9f89ca1168`. Its completed 49/49 automated UAT and 41/41 goal verification are prerequisites to reuse. The 107-case corpus receipt contains 25 actual guest passes and 82 matched expected failures; it does not qualify physical CGB-E or any CGB game. This discussion implements nothing, admits no game bytes, runs no new qualification/benchmark/fuzz campaign, closes no Phase 15 requirement and publishes no release.

Preserve the portable C17 core, existing C API, bounded stepping, deterministic RTC and frozen DMG outputs. Physical/perceptual qualification, broader timing/APU rewrites, additional silicon/peripherals, new frontend features, save states and Playstead integration remain outside this phase. v0.3 is provisional future scope, not an automatic next stage.
</domain>

<decisions>
## Implementation Decisions

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
</decisions>

<canonical_refs>
## Canonical References

Downstream agents must read the relevant sections before research/planning or implementation. Local paths are repository-relative; the topic notes retain checked primary URLs/pins. No separate Phase 15 SPEC exists.

### Scope, durable memory and prerequisites
- `AGENTS.md` — phase stops, authorization, boundaries, rights and automation.
- `.planning/ROADMAP.md` — Phase 15 goal and four success criteria; LIGHT research.
- `.planning/REQUIREMENTS.md` — CGB-11 and SHIP-09/10/11, including the explicit absence alternative.
- `.planning/PROJECT.md` — current product and consumer scope.
- `.planning/context/DECISIONS.md` — D-025/069/096/099/100 and Phase 15 adopted direction.
- `.planning/context/LESSONS.md` — release/consumer, source identity, actual inventory, privacy and UAT closure lessons.
- `.planning/research/INDEX.md` — topic navigation and evidence corrections.
- `.planning/research/v0.2/SUMMARY.md` — milestone game candidates, rights gates and release scope.
- `.planning/research/v0.2/STACK.md` — older candidate/build observations; candidate digests require reconciliation.
- `.planning/phases/GB-12-cgb-double-speed/12-CONTEXT.md` — inherited speed/evidence contracts; completed work stays closed.
- `.planning/phases/GB-13-cgb-hdma/13-CONTEXT.md` — software-policy and consumer limitations.
- `.planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-CONTEXT.md` — independent corpus and source expectations.
- `.planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-CLOSURE.md` — revision-bound evidence and limitations.
- `.planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-VERIFICATION.md` — completed goal verification.
- `.planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-UAT.md` — completed automated UAT, not a workflow to repeat.

### Discussion evidence and primary-source checks
- `.planning/research/phase15-game-acceptance.md` — considered candidates, immutable upstream references and admission/predicate gates.
- `.planning/research/phase15-evidence-consumers.md` — versioned ledger, existing consumer coverage, v0.1.0 A/B and real fuzzing gaps.
- `.planning/research/phase15-release-delivery.md` — staged delivery alternatives, official GitHub/Apple docs and dated PR #70 snapshot.

### Existing implementation and recurring checks
- `include/gabbaboy/gabbaboy.h` — actual public ownership, mode/output and RTC contracts.
- `src/runner/acceptance.c` — bounded progress capture and RGB555 integration seam.
- `src/runner/cases.c` — finite acceptance/applicability case parser.
- `docs/game-acceptance.md` — existing GAME-02 predicate/negative-control and packaged-player contract.
- `tests/acceptance/cases.txt` — frozen Libbet acceptance inputs and dispositions.
- `tests/consumers/c/main.c` — installed C behavior and intended failure checks.
- `tests/consumers/cpp/main.cpp` — installed C++ behavior and intended failure checks.
- `tests/cgb_consumer_symbol_coverage.cmake` — declared API coverage guard.
- `tests/scripts/verify-support-ledger.py` — strict historical ledger/tag/manifest/sidecar validation.
- `tests/scripts/measure-release-baseline.sh` — paired DMG benchmark and existing candidate performance receipts.
- `tests/measure_core.c` — workload/output/build measurement contract.
- `tests/scripts/run-bounded-fuzz.sh` — runtime detection and bounded fast/exploration paths.
- `tests/fuzz_core.c` — hostile input/work limits and model seams.
- `tests/scripts/verify-summary-coverage.py` — enforced automatic GSD coverage schema.
- `tests/expected-tests.txt` — exact recurring test inventory.
- `docs/cgb-corpus.md` — complete-run corpus receipt identities and observed/evaluator result separation.
- `docs/support/unreleased.md` — chronological entries to reconcile into the release ledger.
- `docs/support/v0.1.0.md` — immutable historical scope; preserve its validation.
- `docs/native-integration.md` — embedding examples and adapter responsibilities.
- `docs/cartridge-and-saves.md` — mapper, battery/envelope, RTC and recovery contracts.
- `docs/cgb-profile.md` — CGB mode and software-policy limits.
- `docs/release.md` — package, trust, source/sidecar and recovery claims to update.
- `THIRD_PARTY_NOTICES.md` — actual distributed component/fixture notices.
- `.github/workflows/ci.yml` — native/sanitizer evidence and current fuzz-runtime gap.
- `.github/workflows/fixture-repro.yml` — pinned build/reproduction path.
- `.github/workflows/preview.yml` — existing downloaded-package proof.
- `.github/workflows/release-please.yml` — current version PR flow.
- `.github/workflows/release.yml` — exact-tag draft/platform/download/publish flow to extend.
- `.github/scripts/verify-release-source-proof.py` — actual source, PR and check binding.
- `.github/scripts/verify-release-gates.sh` — final draft/identity/publication gates.
</canonical_refs>

<code_context>
## Existing Code Insights

- **Reusable assets:** bounded runner input/predicate/digest logic; existing C/C++ installed examples with behavioral controls; tag-aware support sidecars; interleaved A/B harness; bounded fuzz helper; exact-source and downloaded-byte release checks. Prefer targeted changes at these seams.
- **Established patterns:** host timing/filesystem/devices stay in adapters; model and execution mode are separate; source expectations, guest observations and evaluator disposition are distinct; old release ledgers remain source-bound; public packages exclude test fixtures.
- **Integration points:** native-CGB progress frame capture/predicate binding, versioned support validation, candidate/tag proof consumers, sanitizer compiler/campaign outcome and release evidence attachment/reuse.
- **Concrete traps:** a hardcoded v0.1 validator cannot describe CGB by adding prose; ledger selection can silently fall back; `--fast` success can mean no libFuzzer; A/B labels can be unknown; existing release performance evidence is not the required v0.1 comparison; PR #70 action-required runs are not green; squash and preview revisions are not tag identities.
</code_context>

<specifics>
## Specific Ideas

Use Rebound's source-defined objective/coin/level state rather than moving pixels or elapsed time as progress. Keep wrong-input/no-input and positive runs at equal budgets. Preserve the existing game's frozen outputs while adding CGB capture. In the ledger, make actual passes, known failures and absence unmistakable. Prefer a small versioned validator over a general report generator, and a real bounded Clang campaign over an unsupported success message.

Relevant lenses were emulator/2D graphics and audio, portable C API/ownership, host adapters, QA/oracle independence, asset licensing, adopter/product claims, performance measurement, security/supply chain, DevOps and release recovery. No unrelated language/framework/3D/distributed-system capability is required. The final adversarial reconciliation corrected two optimistic delivery claims: existing generic sidecars are not v0.2 evidence, and existing sanitizer success does not guarantee an actual fuzz campaign.
</specifics>

<deferred>
## Deferred Ideas

- Broad CGB game search, further timing/APU redesign or making all 82 known failures pass.
- New silicon profiles, physical hardware/perceptual/analog qualification, peer IR/link and host haptics.
- v0.3 transactional save states and qualified Playstead integration; no automatic milestone start.
- A report registry/dashboard, new benchmark/runtime framework, artifact-promotion service or signing/notarization project.
- GitHub App provisioning unless a demonstrated unattended-run need and available credentials justify it; routine run approval recovery remains in scope for later execution.
- Unresolved G1 font rights without new evidence; no external outreach is authorized.
</deferred>

---
*Phase: 15-CGB Acceptance, Support Ledger and v0.2.0 Release*
*Context gathered: 2026-10-16*
