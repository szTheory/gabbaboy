# Phase 24: Resolve remaining v0.4 evidence and verification gaps - Context

**Gathered:** 2026-11-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Produce one additive, commit-pinned assessment of current v0.4 evidence and the stale Phase 20/21 verification boundary. Map every original v0.4 requirement to its owner, original acceptance criteria, current evidence, verification freshness, and exact remaining gate. Preserve the Phase 20/21 verification reports as historical records and keep FIXT-01, RIGHTS-01, DIAG-01, and DIAG-02 Pending under their original owners. Use only focused, existing checks that fit the approved scope; any result is point-in-time evidence and does not refresh the full Phase 20/21 verification or satisfy the D-103 final-head suite gate.

The phase may complete its own assessed deliverable while the four requirements remain Pending and v0.4 remains open. Its completion must not be represented as requirement satisfaction or milestone completion. Research is limited to first-party metadata for the already named candidates and diagnostic upstreams. No third candidate search, fixture/source payload acquisition, build/run/admission, rights determination, broad suite, lifecycle retry, release change, tag/asset operation, or milestone archival is included.
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

### Existing checkers and wiring
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
</specifics>

<deferred>
## Deferred Ideas

- Candidate-specific rights determination, fixture/source payload acquisition, build/run/admission, and any new candidate require separate explicit owner authorization.
- The D-103 exact-final-head broad suite and milestone archival remain separate owner-controlled gates.
</deferred>

---

*Phase: 24-Resolve remaining v0.4 evidence and verification gaps*
*Context gathered: 2026-11-16*
