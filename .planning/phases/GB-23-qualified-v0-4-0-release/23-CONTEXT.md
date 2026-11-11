# Phase 23: Qualified v0.4.0 Release - Context

**Gathered:** 2026-11-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the qualified v0.4.0 release through GabbaBoy's existing trusted release path. Final implementation-head qualification and the release rehearsal must pass for the reviewed revision, with the required hosted coverage, consumer evidence, and regression controls. Phase 20–22 evidence remains historical; do not refresh it just for this release.

The release notes and versioned support ledger must state that neither of the two Phase 21 CGB game candidates was admitted and why, identify the CGB-CPU-E original harness result as harness-only, distinguish Phase 22's synthetic tracer and metadata inventory from real diagnostic execution, and preserve hardware, perceptual, timing, platform, and general-compatibility limits. The released/downloaded product bytes, source identity, digests, installed consumers, notices, and fixture-exclusion checks must reconcile under the established package policy. The release does not make FIXT-01, RIGHTS-01, DIAG-01, or DIAG-02 complete merely by recording their pending outcomes.

Keep the scope to the existing release path and v0.4.0 evidence. Full libretro, Linux/Steam Deck player support, CGB timing rewrites, license migration, early API/state freeze, and new release infrastructure remain outside this phase.
</domain>

<decisions>
## Implementation Decisions

### Public release notes
- **D-01:** Keep the v0.4.0 release notes concise while stating enough to satisfy the release contract: name Potion Panic and µCity 1.3, give each recorded source/rights-scope reason, say neither was built or run and no CGB game was admitted, distinguish the CGB-CPU-E harness-only result from game progress, distinguish diagnostic/reproducibility observations, retain the required limits, and link the versioned support ledger. Do not repeat the full evidence tables in the release notes.

### Versioned support ledger
- **D-02:** Use a generated v0.4 support ledger with a concise but self-sufficient Phase 21/22 summary and direct links to the detailed evidence records. Preserve the evidence distinctions and enough source/model/outcome detail for REL-01; do not duplicate every candidate field or each of the seven diagnostic gate records in the ledger. Leave the historical v0.3.0 ledger unchanged.
- **D-03:** Generate and validate public claims from the project's source-bound release inputs and immutable evidence records. Do not hand-edit rendered ledger output or let the release notes and ledger drift into conflicting versions of the same result.

### Evidence and claim boundaries
- **D-04:** Phase 21 admitted no CGB game after its two ordered attempts. Potion Panic stopped before source acquisition because the creator-linked source could not be reached and exact component grants plus repository/public-CI scope were not established. µCity 1.3 stopped at the required `source/engine/hardware.inc` component, for which no identified grant or notice establishes repository/public-CI scope. Neither candidate was built or run; ROM bytes, loaded mode, progress, observations, and candidate receipts remain unobserved. Describe these as source/rights-scope no-go outcomes, not license prohibitions.
- **D-05:** Report the original CGB-CPU-E native-mode harness as harness-only evidence. Its repeatable RGB555/PCM observations do not establish admitted-game progress, rendering accuracy, perceptual quality, physical CGB-E behavior, mode-3 timing, or general compatibility.
- **D-06:** Report Phase 22 as a synthetic composition tracer plus metadata-only assessment: 513 named entries, seven unresolved real-fixture gates, zero real fixtures admitted, and zero real fixtures executed. Keep DIAG-01, DIAG-02, and RIGHTS-01 Pending. Do not imply that metadata identities, the synthetic tracer, or a digest establish fixture admission or diagnostic execution.

### Release qualification
- **D-07:** Use the established version PR, trusted release rehearsal, exact-source/tag release gates, downloaded-artifact checks, installed-consumer smoke, notices, and fixture-exclusion controls. Publish only after the existing required checks qualify the reviewed release bytes. Preserve the actual supported product/platform matrix and unsigned/not-notarized limits; checksums and source binding must not be described as code signing or notarization.
- **D-08:** Do not repeat earlier phase qualification as if it were new v0.4.0 evidence. Bind this release to its reviewed implementation source and downloaded package identities while carrying Phase 20–22 receipts as historical records.

### the agent's Discretion
- Choose the exact v0.4 support-claim input fields, renderer/verifier organization, concise prose, headings, test controls, and plan decomposition within the roadmap's nine scheduled plans plus its reserved gap slot. Prefer existing CMake and Python standard-library tooling; add no dependency or release capability without demonstrated need and an in-scope blocker.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase boundary and requirements
- `.planning/ROADMAP.md` §Phase 23 — scope, REL-01, release success criteria, nine scheduled plans and the reserved gap slot, and explicit out-of-scope items.
- `.planning/REQUIREMENTS.md` §Release Evidence — REL-01's exact claim requirements and pending requirement status.
- `.planning/PROJECT.md` — v0.4 evidence boundaries, root MIT license, and product limitations.
- `.planning/STATE.md` — Phase 22 closure and current Phase 23 route.
- `.planning/context/DECISIONS.md` D-017 and D-069 — qualify downloaded release bytes and keep verification automated with negative controls.

### Game outcome and rights boundary
- `.planning/phases/GB-20-fixture-admission-tune-up/20-CONTEXT.md` — component-level rights, notices, and product-package fixture policy.
- `.planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-CONTEXT.md` — ordered candidate boundary, harness-only claims, and evidence limits.
- `.planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-VERIFICATION.md` and `21-UAT-EVIDENCE.md` — accepted candidate absence and source-qualified phase outcome.
- `tests/data/cgb-candidates/potion-panic.json` and `tests/data/cgb-candidates/ucity-1.3.json` — immutable candidate dispositions and unobserved fields.
- `docs/game-acceptance.md` §Phase 21 outcome — public reproduction and precise no-go wording.

### Diagnostic outcome
- `.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md` and `22-EVIDENCE.md` — approved synthetic/metadata-only boundary, final counts, pending requirements, and no-go limits.
- `tests/external/diagnostic-assessment.json` and `tests/external/gbmicrotest-inventory.json` — current source-bound inventory and assessment inputs.
- `docs/diagnostic-evidence.md` — public distinction between synthetic composition observations and real diagnostic fixtures.

### Existing release and support-record path
- `docs/release.md` — release rehearsal, trusted publisher, downloaded-byte qualification, recovery, and support/limitation language.
- `docs/support/v0.3.0.md`, `docs/support/unreleased.md`, and `tests/data/support-claims-v0.3.json` — historical ledger, current unreleased entries, and claims-input precedent; do not rewrite v0.3.0.
- `release-please-config.json` and `.release-please-manifest.json` — existing version PR and draft/tag settings.
- `.github/workflows/release-rehearsal.yml` and `.github/workflows/release.yml` — current rehearsal, exact-source, artifact, and publish path.
- `tests/scripts/verify-support-ledger.py`, `tests/scripts/verify-release-candidate.sh`, `tests/scripts/verify-release-gates.py`, and `tests/scripts/verify-release-lifecycle.py` — existing generated-ledger and release mutation controls.
- `tests/data/release-disclosure.json` and `tests/CMakeLists.txt` — disclosure input and automated test registration patterns.
- `cmake/VerifyReleaseReceipt.cmake`, `cmake/VerifyEvidenceLedger.cmake`, `cmake/VerifyFixtureManifest.cmake`, and `cmake/ScanForbiddenFixtures.cmake` — source/receipt binding, notices, and product fixture-boundary checks.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/scripts/verify-support-ledger.py` binds generated support-ledger claims and producer receipts to immutable tag/source facts; `docs/support/v0.3.0.md` shows the established public ledger structure.
- `tests/data/release-disclosure.json` and the release disclosure CTests provide a source-bound pattern for generated, controlled release copy.
- `tests/scripts/verify-release-candidate.sh`, `cmake/VerifyReleaseReceipt.cmake`, and `cmake/VerifyEvidenceLedger.cmake` bind package bytes, source receipts, version/tag, and installed consumers.
- `cmake/VerifyFixtureManifest.cmake` and `cmake/ScanForbiddenFixtures.cmake` enforce notice and fixture-exclusion policy on product packages.
- Phase 21 candidate JSON records and `tests/external/diagnostic-assessment.json` are the authoritative bounded outcome records to summarize.

### Established Patterns
- Release-please creates a reviewed version PR and draft; the trusted rehearsal runs before tagging, then the release path builds, downloads, checks, and publishes exact identified bytes.
- Generated release claims are checked from immutable source data and include negative controls. Historical versioned ledgers remain unchanged when a new support scope is published.
- Digests establish byte identity; source, rights, model applicability, execution, hardware behavior, and perceptual quality are separate claims.
- Release packages include the established core platform matrix and macOS player; product notices and forbidden-fixture checks remain required.

### Integration Points
- The v0.4.0 version PR, changelog/release notes, support-claims input, generated support ledger, trusted release rehearsal, release gate, downloaded artifacts, and consumer/package checks form one release chain.
- Phase 21/22 evidence must flow into public summaries without changing the immutable candidate and diagnostic source records or reopening fixture admission.
</code_context>

<specifics>
## Specific Ideas

- Keep release notes and the versioned support ledger concise but fact-complete; cross-link the detailed Phase 21/22 records instead of duplicating full gate tables.
- Explicitly separate the two candidate no-go reasons, harness-only progress, synthetic diagnostic output, metadata inventory, and real-fixture absence.
- Preserve that the source/rights-scope outcomes are not license prohibitions and that unresolved requirements remain Pending.
- Report only established platform and model support, with hardware, perceptual, timing, and compatibility limits visible.
- The user asked for multi-role/adversarial review and high-quality primary sources where useful, and approved following the synthesized concise-summary recommendation.
</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 23 scope.
</deferred>

---

*Phase: 23-Qualified v0.4.0 Release*
*Context gathered: 2026-11-03*
