---
phase: GB-23-qualified-v0-4-0-release
verified: 2026-11-14T00:16:18Z
status: passed
score: 3/3 Phase 23 roadmap success criteria verified for the release goal
requirements:
  REL-01: satisfied for the qualified software release and stated evidence scope
  FIXT-01: pending
  RIGHTS-01: pending
  DIAG-01: pending
  DIAG-02: pending
phase_completion: pending Plan 23-08 final all-nine-summary boundary; Plan 23-06 shared closure passed
---

# Phase 23: Qualified v0.4.0 Release Verification

## Goal achievement

**Goal:** Users receive a qualified v0.4.0 release whose packages and support records accurately describe the established CGB game and diagnostic evidence.

**Result:** The software-release goal and REL-01 are verified within the published scope. The product/tag source is S, `3de1b0e427f37a202be4469dd818266f359c8b20`. The actual trusted publisher is G5, `fbea1e2cc70f7c2ab9ea5820fa92ca18ddf997e8`, and is distinct from S. Publisher workflow [43526085579, attempt 1](https://github.com/szTheory/gabbaboy/actions/runs/43526085579) completed successfully; release [v0.4.0](https://github.com/szTheory/gabbaboy/releases/tag/v0.4.0) is public at S. Plan 23-06 shared closure now passes over eight completed summaries, including weakened-copy controls and the six configured summary/closure CTests. Final phase completion still requires Plan 23-08’s all-nine-summary boundary.

| Phase 23 roadmap criterion | Status | Evidence and limits |
|---|---|---|
| 1. The reviewed implementation passes final local/hosted qualification and the trusted release rehearsal, including required hosted coverage, consumers, and regression controls; earlier phase evidence stays historical. | **VERIFIED** | Plan 23-04 records final local CTest at qualification `459faf51c265b0e6fc357bf5ec77bb44c7abf1dd` passing all 1,942 required identities with no skips. Protected PR 152 exact-head CI, fixture reproduction, and preview passed at reviewed qualifier `b47d840bff6457811d5e5919b6479e0bf6f9e743`. Post-merge G5 CI [43516339016](https://github.com/szTheory/gabbaboy/actions/runs/43516339016) passed all six required canonical inventories with no skipped required cases. The exact-tree nightly [43269869181](https://github.com/szTheory/gabbaboy/actions/runs/43269869181), rehearsal R1 [43245302329](https://github.com/szTheory/gabbaboy/actions/runs/43245302329), and R2 [43258530932](https://github.com/szTheory/gabbaboy/actions/runs/43258530932) retain their original source identities. The publisher rechecked the active S window, merged PR 147 proof, and nightly. Product-source fuzz provenance is [S CI 43292805796](https://github.com/szTheory/gabbaboy/actions/runs/43292805796), attempt 1, with its 97-execution receipt; G5’s separate fuzz campaign is control-revision evidence and is not substituted for S. |
| 2. Notes and support ledger state either admitted-game software-model progress or the justified absence after the two named candidate attempts, distinguish diagnostic/reproducibility observations, and retain hardware, perceptual, timing, platform, and compatibility limits. | **VERIFIED** | Published [release notes](https://github.com/szTheory/gabbaboy/releases/tag/v0.4.0) and [support ledger](https://github.com/szTheory/gabbaboy/blob/3de1b0e427f37a202be4469dd818266f359c8b20/docs/support/v0.4.0.md) preserve the bounded no-go. Potion Panic lacks established creator-linked exact source/component-level repository and public-CI rights. µCity 1.3 lacks an identified grant or notice for required `source/engine/hardware.inc`. Neither was built or run; neither result establishes a license prohibition. The diagnostic assessment remains 513 named cases, seven unresolved gates, zero newly admitted real fixtures, and zero executed real fixtures. Synthetic composition and CGB-CPU-E software-model/harness observations are not real-game or real-diagnostic results. They establish no physical-hardware behavior, perceptual accuracy, mode-3 timing, broad game compatibility, Linux player, Steam Deck, or live Playstead qualification. Packages are unsigned and not notarized. |
| 3. Published/downloaded artifact identities and digests match the release source; consumers work on those bytes; notices are present; real products pass fixture-exclusion checks and reject a game-ROM insertion. | **VERIFIED** | The public release has exactly 22 assets. Independent post-publication readback checked every downloaded asset’s size/hash against live GitHub metadata and the trusted inventory, bound receipts/policy/native-consumer evidence to the release, and verified `SHA256SUMS` plus the final [release receipt](https://github.com/szTheory/gabbaboy/releases/download/v0.4.0/release-receipt.json) (SHA-256 `0871604836d7d30ca7450932fdc27aa343926d9d1c0baf7e7d33ffe3109adb8e`). The publisher’s [pre-publication inventory artifact](https://github.com/szTheory/gabbaboy/actions/runs/43526085579/artifacts/14087303157) binds the 22 entries to G5. The source archive verifies against S and its recomputed receipt is byte-identical to the public [source-archive receipt](https://github.com/szTheory/gabbaboy/releases/download/v0.4.0/source-archive-receipt.json). Four actual product packages pass the existing product policy; four matching game-ROM insertion controls reject with `product-fixture-leak`. Native Linux and Windows C/C++ checks in the publisher run use the exact public archive/build-receipt hashes; post-publication native macOS C/C++ checks use the actual public macOS archive and include installed-host continuation. Notices and six evidence families pass the trusted receipt checks. |

## Requirement truth and preserved limits

REL-01 is satisfied for the published, source-bound software evidence above. The following requirements remain **Pending** because publication of a no-go record does not admit a fixture or complete its evidence gates:

- **FIXT-01:** no game candidate cleared the rights/source gate; no candidate was built or run.
- **RIGHTS-01:** no fixture was admitted; no license prohibition is inferred.
- **DIAG-01** and **DIAG-02:** the assessment is metadata-only, with seven admission gates unresolved and no real diagnostic fixture admitted or executed.

The 513/seven/zero/zero diagnostic count and both candidate no-go reasons are unchanged. Evidence from the CGB-CPU-E software model, authored harness, synthetic composition tracer, metadata inventory, and reproducibility observations must not be promoted to hardware, visual/perceptual, timing, game-compatibility, or real-diagnostic evidence. Current release packages do not claim a Linux player, Steam Deck, signed/notarized distribution, or live Playstead support.

## Review and security reconciliation

The three fixed structured reports continue to bind reviewed implementation `96505505594612bec77f811acb7d0084cccffb94`; all 80 historical finding objects and their provenance are preserved. Later version, window, harness, and scoped recovery acceptances supplement the source trail without editing or repinning those reports. The accepted reports and Plan 23-04 summary report no new unresolved correctness/security blocker; the existing low, non-blocking `SEC-23-09` resource-bound note remains open. This verification changes no finding status: it preserves the report dispositions, and represents no open high/critical correctness/security finding as closed.

Plan 23-06’s **T-23-13 (asset/receipt tampering)** mitigation is evidenced by the trusted publication gates and independent public-byte readback: current release/API identity, all 22 hashes, immutable source and receipts, product-policy positives and insertion refusals, and consumers on actual published bytes were checked. Its **T-23-14 (completion/requirement-status spoofing)** evidence is grounded in the separate source, control, run, attempt, and asset identities above; requirement states and fallback flags are preserved below. The shared writer/default check, all 21 weakened-copy controls and the six configured summary/closure CTests pass over the eight completed summaries, mitigating T-23-14 within Plan 23-06. Plan 23-08 must still include its own summary and immutable boundary evidence in final closure. Plan 23-06’s **T-23-SC** package-install risk remains the plan’s accepted documentation/closure-only scope; actual product-consumer checks are separately evidenced by Plan 23-05.

The existing source-bound controls used for publication and product evidence include the [published-asset inventory verifier](https://github.com/szTheory/gabbaboy/blob/fbea1e2cc70f7c2ab9ea5820fa92ca18ddf997e8/.github/scripts/verify-published-release-assets.py), [product-policy checker](https://github.com/szTheory/gabbaboy/blob/fbea1e2cc70f7c2ab9ea5820fa92ca18ddf997e8/.github/scripts/verify-workflow-policy.py), [native consumer checker](https://github.com/szTheory/gabbaboy/blob/fbea1e2cc70f7c2ab9ea5820fa92ca18ddf997e8/tests/scripts/verify-v02-consumers.py), [portable release-receipt check](https://github.com/szTheory/gabbaboy/blob/fbea1e2cc70f7c2ab9ea5820fa92ca18ddf997e8/cmake/VerifyReleaseReceipt.cmake), and the immutable [review-evidence gate](https://github.com/szTheory/gabbaboy/blob/fbea1e2cc70f7c2ab9ea5820fa92ca18ddf997e8/tests/scripts/verify-review-evidence.py). The existing [shared UAT closure tool](https://github.com/szTheory/gabbaboy/blob/fbea1e2cc70f7c2ab9ea5820fa92ca18ddf997e8/tests/scripts/verify-uat-closure.py) remains the required automated closure mechanism. These checks support the facts they measured; they do not override pending fixture requirements or fallback classifications.

## Unresolved fallback flags

The spec-less SOURCE-AUDIT fallback remains visible:

1. The REL-01 edge probe is `unclassified`, `unresolved`, with null verification/resolution/reason; it remains an **unresolved flagged assumption**.
2. The descriptor-less transparency prohibition that source/rights no-go must not become a license ban, and harness/synthetic/metadata observations must not become admitted-game/real-diagnostic evidence, remains **unresolved and flagged-unverified**.
3. The descriptor-less transparency prohibition that recording absence must not complete admission requirements or grant hardware, perceptual, timing, general-game, Linux-player, or Steam Deck qualification also remains **unresolved and flagged-unverified**.

The concrete release/product controls provide software evidence but do not classify these probe items. No descriptor fields, automated dismissal, or human UAT claim is invented to force closure.

## Boundary

The qualified release goal and Plan 23-06 reconciliation/shared closure pass. The generated interim closure covers eight completed summaries, with no human checkpoint. Plan 23-08 still owns the transfer lessons, exact ninth-summary set, immutable owner route/auto flags and final shared closure. This report does not auto-advance the phase or start the milestone audit.
