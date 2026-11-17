# Phase 24: Resolve remaining v0.4 evidence and verification gaps - Context

**Gathered:** 2026-11-16; post-T6 discussion updated 2026-11-17
**Status:** T6 evidence reviewed; literal-criterion reconciliation recorded; FIXT-01 still blocks Task 7

<domain>
## Phase Boundary

Produce one additive, commit-pinned assessment of current v0.4 evidence and the stale Phase 20/21 verification boundary. Map every original v0.4 requirement to its owner, original acceptance criteria, current evidence, verification freshness, and exact remaining gate. Preserve the Phase 20/21 verification reports as historical records and keep FIXT-01, RIGHTS-01, DIAG-01, and DIAG-02 Pending under their original owners. Use only focused, existing checks that fit the approved scope; any result is point-in-time evidence and does not refresh the full Phase 20/21 verification or satisfy the D-103 final-head suite gate.

The phase may complete its own assessed deliverable while the four requirements remain Pending and v0.4 remains open. Its completion must not be represented as requirement satisfaction or milestone completion. Research is limited to first-party metadata for the already named candidates and diagnostic upstreams. No third candidate search, fixture/source payload acquisition, build/run/admission, rights determination, broad suite, lifecycle retry, release change, tag/asset operation, or milestone archival is included.

After the fresh review found Critical CR-01, the owner directed us to follow the bounded recovery recommendation. Address only the BOM-prefixed plan-classification bypass within the existing 24-01 plan: normalize exactly one leading UTF-8 BOM before checking the canonical frontmatter fence, fail closed on a second consecutive BOM, and add production-CLI controls for the Phase 24 D-205 guard. The bypassing gap plan must fail for the specific D-205 gap-plan reason; its otherwise identical ordinary-plan twin must pass. Use one same-plan correction task, one clean independent review of its exact committed candidate, and only the existing plan_cap and planning_hygiene_controls CTests after cheap direct checks. The configured focused regression hook must pass before Phase 24 verification can resume. Any Critical/correctness/security finding or new blocker in the fresh review stops the phase before verification.

This recovery adds no plan, dependency, or CTest identity and does not reset any earlier review, test-suite, lifecycle, release, fixture, rights, or milestone limit. Keep the actual 40-plan ceiling, preserve the 30-second CTest timeout and 125-control floor, and retain every requirement as Pending under its original owner. Do not run the broad suite, third lifecycle retest, phase verifier before recovery gates pass, milestone close, archival, or cleanup while blocked.
</domain>

<decisions>
## Implementation Decisions

### Additive verification evidence
- **D-01:** Keep the Phase 20/21 verification reports and their source identities unchanged. Record current checks in an additive Phase 24 evidence record pinned to an exact commit; label them as point-in-time checks, not refreshed phase verification.
- **D-02:** Run only the existing focused checks that cover changed in-scope contracts, after cheaper identity/consistency checks. Do not run the broad CTest suite, claim the full Phase 20/21 criteria are refreshed, or change their GSD stale statuses. The D-103 exact-final-head suite remains a separate milestone gate.

### Read-only candidate research
- **D-03:** If source metadata helps explain the current gaps, consult only first-party pages for Potion Panic, µCity 1.3, dmg-acid2, cgb-acid2, and the pinned gbmicrotest upstream. Record source identity and page-access results as facts. Do not search a third game candidate, fetch ROM/source payloads, build, run, or admit fixture bytes, or draw a legal/rights conclusion from metadata labels.
- **D-04:** Treat upstream-page access failures as access failures, not evidence that a source or permission is absent. A later rights determination or fixture action requires separate explicit authorization.

### Phase exit with gaps
- **D-05:** Phase 24 can pass when its additive evidence map and automated controls are complete, even if the four original requirements remain Pending and Phase 20/21 remain marked stale. Keep the milestone audit at `gaps_found`; do not accept gaps, close v0.4, or imply that phase completion satisfies the original requirements.
- **D-06:** Preserve the 40-plan total ceiling. The roadmap currently has 39 plan files, so Phase 24 has one plan available; no plan, review, gap, test-suite, lifecycle, release, fixture, or rights budget is reset by this rescope.

### Bounded recovery for Critical CR-01

- **D-07:** The owner accepted one bounded recovery for the fresh review finding in [24-REVIEW.md](24-REVIEW.md): append one correction task to the existing 24-01 plan and obtain one clean independent review of the exact committed candidate. Do not add a plan or renew any earlier review or test budget.
- **D-08:** In the existing plan classifier, remove exactly one leading UTF-8 BOM (U+FEFF) before matching the canonical frontmatter fence. If another U+FEFF remains at the beginning, treat the input as malformed and fail closed; do not let an unrecognized prefix classify a gap plan as ordinary.
- **D-09:** Exercise the immutable production plan-cap CLI with paired Phase 24 fixtures that share the same plan path and BOM-prefixed canonical frontmatter, differing only in gap_closure: true versus gap_closure: false. The first must fail specifically with the Phase 24 D-205 gap-plan refusal; the ordinary-plan twin must pass. A helper-only test is insufficient.
- **D-10:** Keep the existing Python standard-library checker and CTest identities. After cheap syntax/direct controls, run only plan_cap and planning_hygiene_controls, preserving the 30-second timeout and 125-control floor. Do not run Phase 24 verification until this focused regression hook and the one independent review are clean. If review finds a Critical/correctness/security issue or a new blocker, stop before verification.

### the agent's Discretion
- Select the existing focused CTest targets that match the files and claims touched by the one plan; keep the existing test identities and CMake/Python standard-library patterns.
- Use machine-checkable positive and negative controls for the Phase 24 report so false requirement completion, ownership changes, or milestone closure are rejected.
- Keep source facts, evaluator/reviewer outcomes, current freshness, and remaining authority gates in separate fields to avoid conflating a focused control pass with requirement completion.
- Add no dependency or new CTest identity unless the plan demonstrates a concrete recurring need and stays within this one-plan scope.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone scope and authority
- `.planning/ROADMAP.md` — Phase 24, prior phase boundaries, execution limits, plan totals, and requirement ownership.
- `.planning/REQUIREMENTS.md` — Original v0.4 requirement definitions and current tracker dispositions; do not infer completion from no-go outcomes.
- `.planning/PROJECT.md` — Product scope, current limits, and milestone status.
- `.planning/STATE.md` — Current owner handoff and preserved verification/lifecycle limits.
- `.planning/context/DECISIONS.md` — D-103, D-193 through D-205; D-205 authorizes only this one rescope and does not renew the other limits.
- `.planning/v0.4-MILESTONE-AUDIT.md` — Current requirement, phase freshness, integration, and flow assessment.

### Historical evidence to preserve
- `.planning/phases/GB-20-fixture-admission-tune-up/20-VERIFICATION.md` — Phase 20's historical source identity and rights/admission outcome.
- `.planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-VERIFICATION.md` — Phase 21's historical harness, scene-contract, and candidate outcomes.
- `.planning/phases/GB-22-composition-and-microtest-evidence/22-VERIFICATION.md` — Historical synthetic-plus-metadata scope; no real diagnostics admitted or executed.
- `.planning/phases/GB-23.1-close-v0-4-requirement-and-verification-gaps/23.1-VERIFICATION.md` and `23.1-CONTEXT.md` — Phase 23.1 closure, exact owner authorization, and preserved limits.

### Recovery finding and stop conditions
- [24-REVIEW.md](.planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-REVIEW.md) — Exact-candidate finding CR-01 and the reason the existing plan guard is blocked.
- [Current continuation handoff](.planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/.continue-here.md) — Owner handoff, bounded recovery proposal, and stops to preserve.
- [24-SECURITY.md](.planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-SECURITY.md) — T-24-04 and its open status before the recovery.
- [24-01-PLAN.md](.planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-01-PLAN.md) and [24-VALIDATION.md](.planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-VALIDATION.md) — Existing one-plan scope and the two authorized focused CTests.

### Existing checkers and wiring
- [Plan checker](tests/scripts/verify-planning-hygiene.py) — Plan frontmatter classifier, immutable plan-cap CLI, and current production-CLI self-test seam for the BOM regression.
- `tests/CMakeLists.txt` — Existing CTest inventory and phase evidence integration.
- `tests/cmake/game-evidence.cmake` — Existing focused CGB progress, candidate, and scene-report checks.
- `tests/cmake/hygiene.cmake` — Existing planning-hygiene controls and immutable-source checks.
- `tests/expected-tests.txt` — Release-side inventory of registered tests.
- `tests/scripts/verify-fixture-admission.py` — Technical fixture record/package-boundary checks; not a legal rights determination.
- `tests/scripts/verify-cgb-candidates.py` — Bounded candidate ordering and metadata checks; does not establish unobserved ROM/build/mode facts.
- `tests/scripts/verify-cgb-progress.py` — CGB harness/progress observations and controls; distinguishes synthetic harness evidence from real-game evidence.
- `tests/scripts/verify-diagnostic-admission.py` — Metadata-only diagnostic gate and refusal controls.
- `tests/scripts/verify-scene-report.py` — Scene-intake/promotion contract checks.
- `tests/scripts/verify-summary-coverage.py` and `tests/scripts/verify-uat-closure.py` — Existing automated planning/UAT closure patterns.

### First-party source metadata
- [Potion Panic creator page](https://deved.itch.io/potion-panic) — Shows the creator's source link and page-level code/asset license labels. These labels are recorded only as page metadata, not as a rights determination.
- [Potion Panic linked source repository](https://codeberg.org/DevEd/potion-panic) — The browser could not fetch this page during discussion; do not infer that the repository is absent.
- [µCity upstream repository](https://github.com/AntonioND/ucity) and [v1.3 release page](https://github.com/AntonioND/ucity/releases/tag/v1.3) — The upstream repository links to Codeberg; the release page shows tag metadata and a short commit prefix. This does not establish required-file provenance or rights.
- [µCity linked source repository](https://codeberg.org/SkyLyrac/ucity) — The browser could not fetch this page during discussion; do not infer that the repository is absent.
- [dmg-acid2 v1.0 README](https://github.com/mattcurrie/dmg-acid2/blob/v1.0/README.md), [cgb-acid2 v1.1 README](https://github.com/mattcurrie/cgb-acid2/blob/v1.1/README.md), and [pinned gbmicrotest README](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/README.md) — Primary upstream references; the browser could not fetch these pages during discussion. Do not infer that their source or permissions are absent.
- [24-CLOSEOUT.md](24-CLOSEOUT.md) and [tracked diagnostic runtime record](../../../tests/external/diagnostic-closeout.json) — Exact results and identities; ignored local runtime receipts are not a substitute for the tracked record.
- [Acid2 fixture manifest](../../../fixtures/acid2/manifest.json) and [diagnostic evidence documentation](../../../docs/diagnostic-evidence.md) — Admitted derivative, mask, provenance, and claim boundaries.
- [THIRD_PARTY_NOTICES.md](../../../THIRD_PARTY_NOTICES.md) — Contains one stale pre-T6 comparison sentence to correct during a later closeout update.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/scripts/verify-cgb-candidates.py` checks the already-bounded game-candidate records and their order; it cannot create missing source/build/ROM/header/mode observations.
- `tests/scripts/verify-cgb-progress.py` and existing CGB progress CTests cover the synthetic harness, input/predicate discrimination, and observation contract.
- `tests/scripts/verify-fixture-admission.py` checks recorded technical identity and product boundaries; it must not be treated as an automatic permission decision.
- `tests/scripts/verify-diagnostic-admission.py` checks the metadata inventory and refuses unresolved real-fixture use.
- Existing scene-report controls, SUMMARY coverage, and shared UAT closure can be reused without adding dependencies.

### Established Patterns
- Planning/evidence checks pin immutable commits or exact source identities and carry causal negative controls with valid positives.
- Existing contracts use Python's standard library and CMake/CTest; keep the dependency tree flat and test identities stable.
- Focused control passes and historical phase verification are distinct evidence types; do not merge their status labels.

### Guard parsing and validation
- The existing is_gap_plan and check_plan_tree path in tests/scripts/verify-planning-hygiene.py feeds both committed-tree plan_cap and D-205 production-CLI controls; keep the recovery on this path.
- The frontmatter matcher is anchored at the beginning of decoded plan text. A single leading BOM becomes U+FEFF under UTF-8 decoding, so normalization must happen before the fence match and repeated BOM input must be rejected rather than treated as an ordinary plan.
- Existing planning_hygiene_controls runs disposable immutable production-CLI fixtures; the paired assertion must require the exact plan-cap-d205-phase24-gap error so an unrelated refusal cannot satisfy the regression.

### Integration Points
- The additive Phase 24 evidence record must reconcile `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/PROJECT.md`, and `.planning/v0.4-MILESTONE-AUDIT.md` without changing the original requirement owners or accepted release claims.
- Existing CTest targets and `tests/expected-tests.txt` provide the test and release-inventory boundaries. No broad suite or release lifecycle rerun is in scope.
</code_context>

<specifics>
## Specific Ideas

- Pin the additive evidence record to an exact commit and state that it supplements, but does not refresh, the old Phase 20/21 reports.
- On Potion Panic's creator page, the source URL points to Codeberg and license fields are displayed. Record these as creator-page metadata only; do not infer repository contents, component-level scope, or permission.
- µCity's GitHub upstream links to Codeberg; its v1.3 release page exposes a tag and short commit prefix. This is not a substitute for exact source inventory, build provenance, hardware.inc provenance, or rights evidence.
- Preserve the bounded original candidate set. Do not try a third game, fetch fixture bytes, or claim a license prohibition.
- A successful Phase 24 result means the additive assessment and its controls pass. It does not satisfy FIXT-01, RIGHTS-01, DIAG-01, or DIAG-02, refresh the complete Phase 20/21 phase gates, or close v0.4.
- For the BOM regression, use two otherwise identical BOM-prefixed Phase 24 plans that differ only in the gap_closure boolean; require the gap plan's specific refusal and the ordinary plan's acceptance. Python's official [UTF-8-SIG codec documentation](https://docs.python.org/3.13/library/codecs.html#encodings.utf_8_sig) confirms that BOM handling applies at the start of the byte stream; keep the project's accepted one-BOM policy explicit in the local classifier.
</specifics>

<deferred>
## Deferred Ideas

- Candidate-specific rights determination, fixture/source payload acquisition, build/run/admission, and any new candidate require separate explicit owner authorization.
- The D-103 exact-final-head broad suite and milestone archival remain separate owner-controlled gates.
- Other frontmatter prefixes or YAML spellings are outside this BOM-specific recovery; if the authorized independent review identifies a distinct plan-cap bypass or blocker, preserve the stop and return it to the owner rather than extending this correction cycle.
</deferred>

---

*Phase: 24-Resolve remaining v0.4 evidence and verification gaps*
*Context gathered: 2026-11-16*

## D-206 Closeout Addendum (owner-authorized)

**Scope:** Complete the original v0.4 requirement criteria and final milestone gate in the existing Phase 24. Reuse the single `24-01-PLAN.md`; do not create a phase or plan file. Keep original requirement ownership and the actual 40-plan ceiling. Preserve all Phase 24 assessment and verification results as point-in-time history.

**Named candidate set:** Potion Panic (GB Compo 2025), then µCity 1.3 as the only fallback; dmg-acid2 v1.0, cgb-acid2 v1.1, and gbmicrotest at `463eb6bc0fe31d61781ef63060ad6d74090c0255`. No other game or diagnostic source is in scope.

**Rights and source integrity:** Inspect the exact pinned source tree, each code/art/audio/build-input component and submodule, notices, release payload identity, and repository/public-CI terms. Do not admit or stage a component payload until its distribution permission and notice requirements are verified. Keep license metadata, a legal conclusion, and an access failure distinct. A no-go is not a license prohibition. For game candidates, preserve source/build/ROM/header/mode identity even when an earlier candidate cannot be admitted. Use µCity only after a documented Potion Panic outcome. For diagnostic derivatives, preserve upstream references, replace glyph tiles with project-authored content, mask only source-anchored text, and claim controlled composition rather than timing. For gbmicrotest, bind each chosen source and exact ROM bytes, document model applicability, and account for every roster member as eligible/executed/excluded with disjoint denominators.

**Technical and test strategy:** Reuse existing Phase 20 admission, Phase 21 candidate, Phase 22 diagnostic, RGBDS reproduction, CGB runner, mask, and immutable-evidence seams. Keep dependencies unchanged and use standard-library/CMake/CTest code already in the tree. Pin any build tools used; do not call an unpinned toolchain reproducible. Add causal negative controls to existing test identities and use cheap syntax, direct checker, fixture-boundary and inventory checks before focused CTests. Do not run a broad local suite.

**Operations and release boundary:** Run exactly one full required CI matrix at the final closeout candidate through the reviewed PR path to satisfy D-103. Keep the published v0.4.0 release, tags, and assets unchanged. Merge only after an independent review and all required checks pass, then finish on `main` at the merged head with a clean worktree. Keep both automatic-advance flags false.

**Acceptance:** The original eight requirements and their owners remain authoritative. Do not promote status based on phase-plan metadata or earlier reports. Evaluate only the evidence each criterion requires; if a required source identity, component right, byte identity, model applicability, runtime accounting, or package boundary is unresolved, preserve that affected requirement as Pending and do not close/archive v0.4.

**Synthesis across lenses:** Product: preserve the bounded original criteria and candidate order. Security/rights: require exact source and per-component notices before distribution. Architecture: prefer existing seams and no new dependencies. QA: test intended refusals with negative controls and distinguish historical, focused, and final-head evidence. Operations: one final PR CI run, then reviewed merge and clean `main` handoff. Adversarial check: do not mistake repository labels, build success, a screenshot, or a passing historical report for permission or requirement completion.

## D-207 Rights Decision Addendum (owner-directed, 2026-11-17)

The owner directed best-faith decisions from collected primary sources and declined external outreach. D-207 accepts the Potion Panic creator-page CC BY-NC-SA label for the exact creator-linked `GFX`, `Levels`, `Tilesets`, and `Audio/Modules` components, with noncommercial-only scope, attribution, license notice, change marking, and share-alike treatment. It excludes the separately attributed Pigu/AYCE WLE converter; if the official prebuilt ROM is considered, its exact sidecar, digest, source relationship, header, and runtime still must be inspected. The pinned µCity `source/engine/hardware.inc` remains blocked because the file has no grant and differs from the available CC0 source.

D-207 also accepts a narrow root-MIT inference for only the pinned dmg-acid2 v1.0 and cgb-acid2 v1.1 `img/` trees, with both MIT notices and the original Acid2 creator credit retained. The `mgblib` font data remains excluded. These are explicit owner-accepted best-faith interpretations, not new upstream component-specific statements and not gap acceptance. Continue to require exact fixture bytes, pinned tools/builds, authored glyph replacement, source-derived masks, independent runtime comparisons, and the existing accounting contracts; preserve affected requirements as Pending if any required fact remains unestablished. The one accepted gbmicrotest case stays limited to its existing scope; other 512 cases and logo scope remain unresolved. No rightsholder messages will be sent.

## Post-T6 Discussion Addendum (owner-directed, 2026-11-17)

The owner asked for all relevant Phase 24 decision areas to be reviewed and for the synthesized recommendations to be followed. This records the resulting criterion-level direction. It does not authorize another Acid2 run, implementation, Task 7, CI, PR, merge, branch switch, or cleanup. Keep tracker edits for formal reconciliation; keep both automatic-advance flags false.

### Acid2 cross-model result and DIAG-01 scope

- The exact T6 run remains `runtime-failed` for DMG-on-CGB: 19,840 of 19,840 compared unmasked pixels differed. The same-model DMG-on-DMG and CGB-on-CGB comparisons each passed with zero differing pixels. Preserve all three results as recorded; do not call the cross-model result a pass or replay the fixture.
- Read-only inspection of the recorded source revision and pinned upstream references found the runner selected the admitted DMG derivative, CGB-CPU-E, and DMG mode. The recorded core source uses the intentional D-18 fixed compatibility palette in that profile, while the pinned CGB reference uses a disjoint set of expanded RGB colors. This can explain an all-pixel difference through color encoding alone. The runner discarded its temporary PPM and the retained receipt has no frame or pixel map, so this is a plausible source-level explanation, not proof of pixel geometry or a core defect.
- The original DIAG-01 wording requires admitted DMG and CGB derivatives, authored glyph replacement, a text-region mask, source/build provenance, recorded rights, and composition-only labeling. It does not require every cross-model profile comparison to match. The current Phase 24 plan adds that stricter all-profile pass gate. Align the next formal requirement map with the original wording: retain the DMG-on-CGB failure as a separate runtime discrepancy, and do not treat it as satisfaction of mode-3 timing or general CGB compatibility. The derivative records and same-model results support DIAG-01's literal criterion; formal status reconciliation must make the plan-level distinction explicit before any Task 7 decision.
- Primary upstream references document the reference-image/color-conversion convention: [dmg-acid2 v1.0 README](https://raw.githubusercontent.com/mattcurrie/dmg-acid2/v1.0/README.md) and [cgb-acid2 v1.1 README](https://raw.githubusercontent.com/mattcurrie/cgb-acid2/v1.1/README.md). No image/reference, mask, or derivative changes are authorized by this discussion.

### RIGHTS-01 and DIAG-02 literal criteria

- **RIGHTS-01:** Recommend Complete for the exact admitted diagnostic fixtures. The criterion permits a game *or diagnostic* fixture; D-207's owner-accepted bounded rights interpretations, recorded component scopes/notices, unchanged root MIT license, and existing product/package exclusion evidence satisfy the diagnostic alternative. This does not clear unadmitted game-candidate components, the other 512 gbmicrotest ROMs, excluded logo/font data, or any other source. D-207 remains an explicit bounded owner interpretation, not a claim of upstream component-specific certainty.
- **DIAG-02:** Recommend Complete for the single admitted `div_inc_timing_a` case. Its source and exact bytes, bounded redistribution terms, DMG-CPU-B software applicability, one eligible/executed case, and 512 named exclusions with reasons are recorded. This does not claim a 513-case execution, hardware behavior, or DMG-CPU-08/CGB applicability.
- Keep the original Phase 20/22 ownership. Record these as criterion-level outcomes during formal reconciliation; do not promote them based on earlier metadata-only reports or imply that all candidate sources are cleared.

### FIXT-01 and execution boundary

FIXT-01 remains Pending. Neither named game candidate has the required source-build, ROM-byte, cartridge-header, CGB-mode, and runtime facts: Potion Panic's source build is blocked by the excluded WLE converter, and µCity requires the unlicensed `hardware.inc`. Do not use either excluded component, search a third candidate, or infer completion from the no-go records. The adopted recommendation is to preserve the original requirement and leave v0.4 open; Task 7 remains blocked while FIXT-01 is Pending. Revisit only if the owner later directs a material acceptance/scope change.

### Cross-role synthesis

| Lens | Adopted direction |
|---|---|
| Product and requirement ownership | Apply each original criterion literally and keep original Phase 20/21/22 owners; do not turn a diagnostic outcome into a broader game or hardware claim. |
| Rendering and emulator behavior | Keep the cross-model pixel mismatch visible; its palette explanation is provisional because no rendered frame survived. Do not change the core or expected image to hide it. |
| QA and evidence | Preserve exact identities and failed results; distinguish the two same-model passes from the cross-model failure and from requirement satisfaction. No rerun is authorized. |
| Security and rights | Use only D-207's exact bounded scopes and full notices; unresolved game inputs and unrelated ROMs remain excluded. |
| Architecture and operations | Reuse existing source-backed records and standard-library checks; add no dependency. Task 7, final CI, PR, merge, and cleanup remain stopped until FIXT-01 is resolved. |

The existing [THIRD_PARTY_NOTICES.md](../../../THIRD_PARTY_NOTICES.md) still says the Acid2 comparison has not been performed. Correct that stale sentence in a later authorized closeout update to state the three recorded outcomes without changing fixture rights or product claims.

## D-209 owner direction — close v0.4 with accepted gaps (2026-11-17)

The owner directs administrative closeout now so emulator work can continue. RIGHTS-01, DIAG-01, and DIAG-02 are complete for the exact admitted diagnostic criteria described in the closeout record; FIXT-01 remains Pending because neither named game has the complete required evidence. Preserve the Acid2 DMG-on-CGB all-pixel mismatch as a failed result; do not replay it or claim a proven cause. Phase 24 Task 7, stale prior verification, and D-103 remain explicit closeout gaps. The next recommended scope is v0.5 DMG PPU Timing, starting through `$gsd-new-milestone`.
