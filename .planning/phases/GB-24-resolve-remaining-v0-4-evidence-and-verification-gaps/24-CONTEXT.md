# Phase 24: Resolve remaining v0.4 evidence and verification gaps - Context

**Gathered:** 2026-11-18; updated after the D-216 recovery authorization
**Status:** D-215 local T10–T12 checks passed at candidate `e1d3200b1568fb619759c0f31cf4a8605e57ea06` (tree `1dd6999e95076662c21eb79c63c4baf3188cdb1e`), but its independent exact-head review found three path/Git-environment blockers and a separate newline-bearing Git-path census blocker. The owner extended the sole plan to cover all four findings and explicitly authorized the correction, focused local retests, up to two scoped post-correction review-fix passes, one full protected PR matrix after a clean review, and conditional protected merge of the identical qualified head. D-215's first blocked candidate and review remain immutable history. Task 7, Phase 24 verification, milestone audit/archive, v0.5 and worktree cleanup remain outside this scope.

<domain>
## Phase Boundary

Produce one additive, commit-pinned assessment of current v0.4 evidence and the stale Phase 20/21 verification boundary. Map every original v0.4 requirement to its owner, original acceptance criteria, current evidence, verification freshness, and exact remaining gate. Preserve the Phase 20/21 verification reports as historical records and preserve D-209's current requirement dispositions, including FIXT-01 Pending. Use only focused, existing checks that fit the approved scope; any result is point-in-time evidence and does not refresh the full Phase 20/21 verification or satisfy the D-103 final-head suite gate.

The phase may complete its own assessed deliverable while FIXT-01 remains Pending and v0.4 remains open; the other seven original v0.4 requirements are complete under D-209. Phase completion must not be represented as satisfying FIXT-01 or completing the milestone. Research is limited to first-party metadata for the already named candidates and diagnostic upstreams. No third candidate search, fixture/source payload acquisition, build/run/admission, rights determination, broad suite, lifecycle retry, release change, tag/asset operation, or milestone archival is included.

After the fresh review found Critical CR-01, the owner directed us to follow the bounded recovery recommendation. Address only the BOM-prefixed plan-classification bypass within the existing 24-01 plan: normalize exactly one leading UTF-8 BOM before checking the canonical frontmatter fence, fail closed on a second consecutive BOM, and add production-CLI controls for the Phase 24 D-205 guard. The bypassing gap plan must fail for the specific D-205 gap-plan reason; its otherwise identical ordinary-plan twin must pass. Use one same-plan correction task, one clean independent review of its exact committed candidate, and only the existing plan_cap and planning_hygiene_controls CTests after cheap direct checks. The configured focused regression hook must pass before Phase 24 verification can resume. Any Critical/correctness/security finding or new blocker in the fresh review stops the phase before verification.

This recovery adds no plan, dependency, or CTest identity and does not reset any earlier test-suite, lifecycle, release, fixture, rights, or milestone limit. Keep the actual 40-plan ceiling, preserve the 30-second CTest timeout and 125-control floor, and retain D-209's current requirement dispositions under their original owners. Do not run the broad suite, third lifecycle retest, phase verifier before recovery gates pass, milestone close, archival, or cleanup while blocked.

D-214 completed its local recovery gates at `feb195f5e50eb4669b5bdb8b62e50459ec84121d` (tree `a28ca6b6644e90bde15b7ecc5c6e10bc94e7e0a6`). The fresh exact-head review at that candidate found three path-contract bypasses, an archive-pair fallback that skips current-route validation, and two candidate-Git validation weaknesses. The owner selected one integrated same-plan correction for all six findings. This new scope is planning-only until the updated plan is checked and execution is separately authorized.

The findings are specifically: CR-01, decoded/escaped string values can name protected paths without a lexical spelling; CR-02, a protected path passed through a local helper parameter is not tracked to its reader; CR-03, a path syntactically rooted at a temporary directory can add components that escape that root; CR-04, removing both archived v0.4 files selects legacy validation and skips current-route checks; WR-01, text-mode Git output can normalize a bare CR in an admission pin; WR-02, inherited `GIT_DIR`, `GIT_WORK_TREE`, and related variables can redirect temporary-repository commands. The full review artifact is `/private/tmp/24-D214-REVIEW.md` in the current environment.

The correction proposal is limited to those six findings and their direct positive/negative controls. It requests a Phase 24-only exception to the already-spent normal review-fix/gap limits, without changing global caps; allows up to two post-correction review-fix passes and uncapped in-scope local diagnosis/retests; allows one full protected PR matrix only after a clean review; and permits merging the exact reviewed head only if every required protected context passes. If a review is unavailable, remains blocked after the two passes, or finds a new out-of-scope issue, or if any required matrix context fails/is skipped/is stale/is missing, stop. Use existing PR #154 and merge only the exact reviewed/tested head through branch protection after all required checks pass. Task 7, requirement changes, phase verification, milestone audit/archive, D-103, excluded-ROM replay, release changes, and worktree cleanup remain separate or prohibited boundaries.
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
- **D-05:** Phase 24 can pass when its additive evidence map and automated controls are complete while FIXT-01 remains Pending and Phase 20/21 remain marked stale. Seven of eight original v0.4 requirements are complete under D-209. Keep the milestone audit at `gaps_found`; do not accept gaps, close v0.4, or imply that phase completion satisfies FIXT-01.
- **D-06:** Preserve the 40-plan total ceiling. The roadmap currently has 39 plan files, so Phase 24 has one plan available; no plan, review, gap, test-suite, lifecycle, release, fixture, or rights budget is reset by this rescope.

### Bounded recovery for Critical CR-01

- **D-07:** The owner accepted one bounded recovery for the fresh review finding in [24-REVIEW.md](24-REVIEW.md): append one correction task to the existing 24-01 plan and obtain one clean independent review of the exact committed candidate. Do not add a plan or renew any earlier review or test budget.
- **D-08:** In the existing plan classifier, remove exactly one leading UTF-8 BOM (U+FEFF) before matching the canonical frontmatter fence. If another U+FEFF remains at the beginning, treat the input as malformed and fail closed; do not let an unrecognized prefix classify a gap plan as ordinary.
- **D-09:** Exercise the immutable production plan-cap CLI with paired Phase 24 fixtures that share the same plan path and BOM-prefixed canonical frontmatter, differing only in gap_closure: true versus gap_closure: false. The first must fail specifically with the Phase 24 D-205 gap-plan refusal; the ordinary-plan twin must pass. A helper-only test is insufficient.
- **D-10:** Keep the existing Python standard-library checker and CTest identities. After cheap syntax/direct controls, run only plan_cap and planning_hygiene_controls, preserving the 30-second timeout and 125-control floor. Do not run Phase 24 verification until this focused regression hook and the one independent review are clean. If review finds a Critical/correctness/security issue or a new blocker, stop before verification.

### D-213 post-T10 recovery decisions

- **D-11 — Measure semantics, not a stale lexical count.** `verify-no-phase-paths.py` must keep its general lexical scan, must-scan list, exact historical JSON exception, stale-row rejection, and over-limit rejection. Replace only the `verify-planning-hygiene.py` count-only allowance with a narrow structural/context contract that classifies its immutable Git reads and disposable self-test paths. Do not set the pin to 30 or exempt the file. Add negative controls for an unclassified path literal and a same-count change that turns an approved fixture/source value into a live filesystem read. Use the Python standard library; no dependency or new CTest identity.
- **D-12 — Put the route in the immutable candidate.** The active Phase 24 route and matching handoff must exist in the committed candidate used by `git show <rev>:<path>` checks. Before implementation, allow a local, unpushed documentation-only planning commit that includes the route and coherent Phase 24 state/plan records. Stage only approved `.planning/` files; explicitly verify no `tests/` source edits entered that commit. Verify the route and archived v0.4 blobs from the boundary commit, then verify each implementation candidate descends from it. A dirty-worktree route does not satisfy an immutable-revision check.
- **D-13 — Replan the stopped round and permit local correction cycles.** Do not resume the failed T10–T12 execution attempt or continue at T11. Replan the same sole Phase 24 plan to include the stale count contract, committed-route prerequisite, and all six D-212 integration blockers. Within a later separately authorized execution, treat cheap and focused local failures as diagnose/fix/retest feedback inside this one bounded scope; freeze only after those gates pass. Keep the unused D-212 allowance of one fresh exact-head review and one protected PR matrix for the frozen candidate; any unresolved review finding or failed/missing required matrix context stops for owner discussion. This does not authorize Task 7, Phase 24 verification, milestone audit/archive, requirement changes, broad local suites, or excluded ROM/Acid2 execution.
- **D-14 — Apply the measured CI efficiency policy.** Follow `.planning/context/WORKFLOW.md#cicd-efficiency`: record actual job/step duration and dependency waits; run cheap changed-contract checks before long suites; retain required test membership and branch protection. Keep the full workflow matrix. Track the D-211 preview-waiter cost as a follow-up; do not fold a cross-workflow waiter redesign into this recovery plan without separate scope.

### D-214 — Execution authorization (2026-11-18)

The owner explicitly authorized the fresh D-213 execution: make the plan's local, unpushed `.planning/`-only boundary commit; execute T10, T11, and T12; iterate in-scope local diagnosis, fixes, and relevant retests until scoped checks pass; then obtain at most one fresh exact-head independent review and run at most one protected PR matrix. This authority does not resume the stopped D-212 attempt. The plan's exact whitelist, task scope, no-broad-suite/no-replay boundaries, and final review/matrix stop conditions remain binding. Phase verification, milestone audit/archive, merge, v0.5, and worktree cleanup are not included.

### D-215 — Recovery scope after the D-214 exact-head review (2026-11-18)

The owner selected one same-plan correction proposal for all four blockers and both warnings in the fresh D-214 review. This requires a Phase 24-only exception to the already-spent normal two-review-fix/one-gap limits; the global caps remain unchanged. Permit up to two post-correction review-fix passes for these six findings and direct corrections. In-scope local diagnosis, fixes, and relevant retests may converge without an arbitrary attempt count. New out-of-scope trust/correctness findings stop for owner discussion.

After local checks converge, run one initial fresh exact-head independent review. If it identifies only scoped findings/direct corrections, allow up to two post-correction fix-and-re-review passes; each corrected candidate must pass relevant local checks and receive a fresh review. Local diagnosis/retesting does not spend this review allowance. Stop on a new out-of-scope trust/correctness issue, unavailable review, or any finding unresolved after those two passes. Run one full protected PR matrix only after a clean final review, preserving every existing required context and branch-protection rule. Any failed, skipped, stale, or missing required matrix context stops without another matrix. If the exact reviewed and matrix-tested head passes every required context, the owner authorizes conditional merge through the protected PR and reconciliation to `main`; do not alter the candidate after final review or matrix qualification.

This discussion authorizes planning only; a separate owner authorization is required before executing the updated plan. Keep D-209's accepted gaps, original requirement owners/statuses, FIXT-01 Pending, Task 7 deferral, failed unreplayed Acid2 comparison, excluded gbmicrotest cases, published v0.4.0 bytes, D-103 stop, no broad local suite, and no worktree cleanup. Phase 24 verification, milestone audit/archive, and v0.5 remain separate.

### D-215 implementation recommendations from the review synthesis

- Keep the repository-wide lexical path scan and harden only its structural contract for the planning-hygiene checker. Use the Python standard-library AST to inspect decoded literal values, fold only safe literal forms, and follow protected paths through local helper parameters/calls. Prove lexical component containment for the complete derived path beneath the verified temporary root; reject absolute components, parent traversal, unproven dynamic components and root rebinding. Runtime filesystem symlink resolution is outside this finite static-analysis seam: claim no symlink containment and add no symlink test or platform dependency. If execution reveals an actual symlink-based read escape in the target seam, stop as a new out-of-scope trust/correctness issue. Do not execute inspected source or add a dependency.
- For current candidate validation, require both archived v0.4 blobs and the active Phase 24 route; do not infer historical mode from both archive files being absent. Keep historical validation behind an explicit, full-revision boundary selector.
- Read admission pins as raw Git blob bytes and accept only exactly 40 lowercase hexadecimal ASCII bytes, optionally followed by LF or CRLF; also accept the exact 40 bytes with no terminator. Reject bare CR, whitespace, extra bytes, uppercase, and non-ASCII. Sanitize repository-redirection `GIT_*` variables for temporary-repository operations and assert the selected Git directory and candidate HEAD.
- Add causal negative controls for escaped/concatenated paths, helper-argument flow, temporary-root escape, paired archive removal, malformed pin terminators, and Git environment redirection; retain positive controls for the approved immutable reads, historical boundary, exact archive pair, and valid pin forms. Reuse existing self-test/CTest identities and run cheap checks before longer gates.

### D-216 — Extend and execute recovery after the D-215 review (owner-authorized, 2026-11-18)

The frozen D-215 candidate `e1d3200b1568fb619759c0f31cf4a8605e57ea06` (tree `1dd6999e95076662c21eb79c63c4baf3188cdb1e`) passed its seven focused local CTests, but its fresh review identified four defects. The review receipt is [D-215 review](../../../build/phase24/d215-review-e1d3200b.md); it made no source edits and ran no tests. The owner explicitly extends the recovery to these exact four findings, superseding only the review's “out-of-scope” stop for the manifest-census finding:

1. `verify-no-phase-paths.py` misses a protected path built by bounded literal `chr()` plus concatenation because semantic analysis is gated on recognized literal values. Add safe finite folding and a causal production-source reader negative.
2. The same path checker trusts any helper named `git_run` without inspecting its body. Inspect or otherwise constrain the adapter so a helper body that reads/traverses a live checkout is rejected; add the same-count causal control while retaining the approved immutable Git reader positive.
3. `verify-diagnostic-evidence.py`'s generic `run()` forwards inherited `GIT_*` into the synthetic boundary-history repository control. Keep generic non-Git execution behavior; sanitize Git-only subprocesses with a narrow environment and assert the intended temporary repo and untouched decoy under hostile `GIT_DIR`/`GIT_WORK_TREE`.
4. `verify-state-forks.py` parses text-mode newline-delimited `git ls-tree` paths. Switch census enumeration to raw NUL-delimited bytes, decode candidate manifest paths strictly, and add synthetic newline-path controls without executing fixtures or changing the real manifest set.

Update only the sole existing Phase 24 plan, context and execution records; add no plan, dependency, CTest identity, fixture, active requirement, or source-candidate expansion. Reuse the existing Python standard library and existing `--self-test` / `--self-test-controls` / `--inventory-controls` seams. Run cheap syntax/identity/control checks first and retain the seven existing focused CTests, their identities, timeout and floors. The D-215 candidate's prior local passes remain evidence at that candidate and are not replayed wholesale; each newly affected contract is tested at its corrected immutable candidate.

This authorization permits the new correction and local diagnosis/fix/retest convergence. After local gates pass, obtain an independent review bound to the complete frozen candidate and cumulative diff. The D-215 phase-local exception allows up to two scoped fix-and-re-review passes after this correction; retain actual findings and stop on an out-of-scope trust/correctness issue or unresolved review finding after those passes. Only a clean final review permits one full protected matrix on the existing PR; any failed, skipped, stale or missing required context stops without a matrix retry. If all required contexts pass for the identical reviewed/tested head, merge it through existing branch protection. Do not alter workflow membership, coverage, timeout, cache or concurrency speculatively. Record actual job/step time, queue/dependency wait, timeout headroom and package-work execution/skips; keep the measured preview-waiter redesign separate.

Preserve D-209 statuses and owners, FIXT-01 Pending, the failed unreplayed Acid2 comparison, excluded diagnostic ROMs, published v0.4.0 bytes, D-103, Task 7, all other suite/lifecycle/release/fixture/rights stops, and the separate phase/milestone closure boundary. Keep this worktree until a successful protected merge is reconciled; no phase verification, milestone audit/archive, v0.5 or cleanup follows from this execution.

**Primary-source basis:** Git documents `git ls-tree -z` as emitting path names verbatim and NUL-terminated ([git-ls-tree](https://git-scm.com/docs/git-ls-tree.html)); its environment documentation explains repository redirection by `GIT_DIR`/`GIT_WORK_TREE` ([Git environment](https://git-scm.com/docs/git)). These support the byte-delimited census and isolated-Git test boundary; neither changes fixture policy.

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
- `.planning/milestones/v0.4-REQUIREMENTS.md` — Archived original v0.4 requirement definitions and current tracker dispositions; there is no active root requirements tracker.
- `.planning/PROJECT.md` — Product scope, current limits, and milestone status.
- `.planning/STATE.md` — Current owner handoff and preserved verification/lifecycle limits.
- `.planning/context/DECISIONS.md` — D-103, D-193 through D-216; read the latest Phase 24 scope decisions alongside historical limits.
- `.planning/context/WORKFLOW.md#cicd-efficiency` — standing policy for measured CI/CD timing, cheap-before-expensive checks, and preserving required coverage.
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
- [24-CLOSEOUT.md](.planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-CLOSEOUT.md) — D-214/D-215 local candidates, focused checks and preserved failures; D-216 adds the latest exact-head review and execution authorization.

### Existing checkers and wiring
- [Plan checker](tests/scripts/verify-planning-hygiene.py) — Plan frontmatter classifier, immutable plan-cap CLI, and current production-CLI self-test seam for the BOM regression.
- `tests/scripts/verify-no-phase-paths.py` — Existing lexical Phase-path scanner and new structural/context policy for path literals and readers.
- `tests/scripts/verify-diagnostic-evidence.py` — Immutable evidence snapshot selection, archived requirements/roadmap checks, and active recovery-route validation.
- `tests/scripts/verify-dense-input.py` — Candidate Git-object, admission-pin, and temporary-subject controls.
- `tests/scripts/verify-planning-hygiene.py` — Existing sanitized Git environment helper to reuse for temporary repositories.
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

### Primary-language and Git behavior references for D-215/D-216
- [Python AST](https://docs.python.org/3/library/ast.html) and [Python lexical analysis](https://docs.python.org/3/reference/lexical_analysis.html) — AST constants represent decoded literal values; escapes and adjacent string literals affect runtime values.
- [Python pathlib](https://docs.python.org/3/library/pathlib.html) — Path containment and resolution semantics; lexical parent operations alone do not prove filesystem containment.
- [Git documentation](https://git-scm.com/docs/git) — `GIT_DIR`, `GIT_WORK_TREE`, and related environment variables can redirect repository discovery and operations.
- [Git `ls-tree`](https://git-scm.com/docs/git-ls-tree.html) — `-z` emits path names verbatim and NUL-terminated, avoiding quote/newline ambiguity in the state-fork census.

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
- The D-214 review targets `tests/scripts/verify-no-phase-paths.py`, `verify-diagnostic-evidence.py`, and `verify-dense-input.py`; preserve the existing CTest seams while making their path, archive, and Git-context contracts fail closed.

### Guard parsing and validation
- The existing is_gap_plan and check_plan_tree path in tests/scripts/verify-planning-hygiene.py feeds both committed-tree plan_cap and D-205 production-CLI controls; keep the recovery on this path.
- The frontmatter matcher is anchored at the beginning of decoded plan text. A single leading BOM becomes U+FEFF under UTF-8 decoding, so normalization must happen before the fence match and repeated BOM input must be rejected rather than treated as an ordinary plan.
- Existing planning_hygiene_controls runs disposable immutable production-CLI fixtures; the paired assertion must require the exact plan-cap-d205-phase24-gap error so an unrelated refusal cannot satisfy the regression.

### Integration Points
- The additive Phase 24 evidence record must reconcile the archived `.planning/milestones/v0.4-REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/PROJECT.md`, and `.planning/v0.4-MILESTONE-AUDIT.md` without changing the original requirement owners or accepted release claims.
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
- For the D-214 findings, treat the reported candidate as historical review input, not a clean baseline. The next implementation candidate must descend from it and retain a direct negative for each of CR-01–CR-04 and WR-01–WR-02.
- Keep the full protected matrix. Record actual job/step durations, queue/dependency waits, and timeout headroom in Phase 24 evidence; do not change required coverage or workflow triggers in this correction.
</specifics>

<deferred>
## Deferred Ideas

- Candidate-specific rights determination, fixture/source payload acquisition, build/run/admission, and any new candidate require separate explicit owner authorization.
- The D-103 exact-final-head broad suite and milestone archival remain separate owner-controlled gates.
- Other frontmatter prefixes or YAML spellings are outside this BOM-specific recovery; if the authorized independent review identifies a distinct plan-cap bypass or blocker, preserve the stop and return it to the owner rather than extending this correction cycle.
- The D-211 package-preview waiter redesign remains a separate measured follow-up. This recovery records the next run's efficiency evidence but does not change cross-workflow triggers or reduce required contexts.
</deferred>

---

*Phase: 24-Resolve remaining v0.4 evidence and verification gaps*
*Context gathered: 2026-11-18*

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

## D-210 bounded recovery addendum (owner-authorized, 2026-11-17)

D-210 authorizes only Task 8 in the existing `24-01-PLAN.md`, to repair the already frozen closeout candidate's CI contract. `phase22_admission_assessment` becomes static evidence validation for the exact recorded outcome: DMG-on-DMG pass/0, DMG-on-CGB mismatch/19,840, CGB-on-CGB pass/0. It has no runner, qualification, runtime timeout, evidence-write argument, or Acid2 execution path. The mismatch stays a failure and its cause stays unproven.

The exact D-209 status paragraph may differ from each fixture's historical `THIRD_PARTY_NOTICES.md` snapshot; all other bytes and each active fixture digest row remain pinned. Product validation accepts the complete D-209 notice index only by its exact reviewed digest. No rights text, license bytes, fixture payload, or admission identity changes. Shared diagnostic `--receipt` explicitly refuses before file access, proved with a missing ROM path.

Run only the cheap and focused checks recorded in Task 8; project-generated synthetic control ROMs are permitted only in their existing controls. Do not replay Acid2 or run another admitted upstream/game ROM. Obtain exactly one independent review and then one protected PR matrix; merge only that exact reviewed/tested head if all gates pass. Any review blocker or failed/missing required CI context ends this recovery with no retry. Task 7, Phase 24 verification, milestone audit/archive, FIXT-01, and requirement statuses remain unchanged. After successful protected reconciliation, start v0.5 from a clean `main` checkout with `$gsd-new-milestone`.

## D-211 revised bounded recovery addendum (owner-authorized, 2026-11-17)

The owner followed the recommendation after the D-210 exact-candidate review. Reuse the sole existing Phase 24 plan and add exactly one follow-up task to correct WR-01: report only rejected cases as negative controls and remove the duplicate positive overlay case. Do not change fixture rights, payloads, admission, or the recorded Acid2 outcome.

D-211 supersedes D-210's no-admitted-ROM restriction only for already-admitted game/fixture ROM cases run by the existing exact protected PR matrix: `required-native`, `fixture-repro`, and `preview-package-smoke`. This permits the existing Libbet-backed acceptance tests the reviewer identified; it adds no fixture, test case, or local ROM execution. Acid2 remains excluded from execution: `phase22_admission_assessment` stays static and checks the exact recorded three-profile result, including the failed 19,840-pixel DMG-on-CGB comparison. No broad local suite, candidate expansion, rights/requirement change, Task 7, Phase 24 verifier, milestone audit/archive, release change, or branch-protection bypass is authorized.

After cheap direct controls, run only the focused existing local test(s) covering the corrected fixture-admission checker; synthetic controls may run within those existing controls. Commit the corrected candidate, obtain exactly one fresh independent review of its exact head/tree, then open one protected PR and spend one matrix for the three named contexts. Do not push after that matrix begins. A blocker, unresolved finding, missing/failed/skipped/stale required context, or unavailable review ends this recovery without another correction, review, or matrix. Merge only the exact reviewed/tested head through branch protection if all gates pass. Keep FIXT-01 Pending and preserve D-209's accepted gaps. Start v0.5 DMG PPU Timing with `$gsd-new-milestone` only after reconciliation to clean `main`.

### Cross-role synthesis

| Lens | Adopted direction |
|---|---|
| Product and requirements | Permit only the pre-existing required CI's already-admitted ROM cases; no new compatibility claim or requirement promotion. |
| Emulator QA and evidence | Keep Acid2 static in CI; retain the cross-model mismatch as failed evidence and never replay it. |
| Security and test integrity | Fix the false negative-control count, remove the duplicated positive, preserve fixture identities and branch protection. |
| Operations | Spend one new review and one exact-head protected matrix; any blocker ends the route without retries. |
| Architecture | Reuse existing Python standard-library checker, CTest identity, and the sole Phase 24 plan; add no dependency. |

The current checkout remains the recovery worktree. Do not switch away or remove it before its reviewed changes are reconciled; a clean `main` checkout is the next milestone boundary after a successful merge.

## D-212 Integrated post-matrix gap discussion (owner-selected, 2026-11-17)

The owner selected an integrated recovery scope after the D-211 candidate failed its protected PR matrix. This authorizes discussion and planning of one gap round in the existing Phase 24 plan; it does not authorize implementation, a new review, a new CI matrix, merge, or starting v0.5. Preserve PR #154 and candidate `96d502d4733ac54aa8bf7fbfd7813065143771dc` unchanged while the original run concludes. Run `44189691301` has failed native macOS, native Linux, Linux ASan acceptance, Linux ASan tests, and the CMake-floor job; Windows is still running its required test-inventory step. Related package-preview run `44189691412` is waiting for successful matching CI. The required-native gate cannot pass with the recorded failed dependencies. Do not cancel or rerun that attempt.

### Findings to cover in the one integrated gap round

1. **Dense-input mutant Git context:** `verify-dense-input.py` copies tracked files without `.git`, then gives the mutant configure an object store containing only the legacy baseline. Repository admission correctly reads the baseline there but requires each active fixture admission pin and its ancestry in the subject repository. Keep `check_commit`, full commit identity, and ancestry checks fail-closed. Repair only the harness's temporary Git context, and add a cheap preconfigure assertion that its candidate HEAD and required admission pins resolve with the expected ancestry.
2. **Archived v0.4 planning evidence:** Phase 22 evidence and planning-hygiene checks still require root `.planning/REQUIREMENTS.md` or an active root roadmap section. The D-209 closeout deliberately keeps v0.4 detail in `.planning/milestones/v0.4-REQUIREMENTS.md` and `v0.4-ROADMAP.md`, while Phase 24 recovery remains active. Keep D-209's administrative close and requirement statuses authoritative; teach exact-revision checkers to follow the archived v0.4 source for this recovery state. Do not restore archived requirements as a new active tracker or reopen v0.4 requirements.
3. **State-fork fixture accounting:** `tests/data/state-forks.json` lists 20 manifests, while the candidate has two additional diagnostic manifests, Acid2 and gbmicrotest. The matrix iterates listed ROM rows, so adding these manifests as ordinary rows would execute Acid2 and the 512 excluded gbmicrotest cases. Keep those executions excluded; encode their exact identities and exclusion reasons in the existing inventory/contract and retain negative controls that reject accidental execution. Do not rerun the one admitted gbmicrotest case.
4. **Historical phase-path fixture:** `verify-no-phase-paths.py` rejects one literal historical path in `tests/data/v04-closeout.json`. Resolve only that exact data-fixture occurrence or narrowly allowlist its immutable line with a reason; preserve the guard against actual readers of the live phases directory.
5. **Tagged checker trust:** `workflow_policy_coverage_controls` rejects the candidate's modified `verify-fixture-admission.py` because it differs from the v0.4.0 tagged trusted snapshot. Preserve that release trust root. Do not simply refresh its digest, remove the comparison, or weaken the production admission/rights checks. Plan a design that keeps the tagged checker independently verifiable while handling the exact D-209 notice overlay; if that cannot be done within this gap round, stop and return the trust-boundary issue to the owner.
6. **Planning-hygiene timeout:** one macOS run of `planning_hygiene_controls` reached the existing 30-second timeout under parallel load; Linux failed the same self-test earlier on missing archived requirements. Diagnose runtime and failure order before changing budgets. Prefer a cheaper or properly bounded self-test; increase a timeout only if measured evidence shows it is the right correction and it preserves the same coverage.

The failed `state_fork_matrix_*` setup controls caused dependent fork, census, and mutant tests to be skipped; those are consequences of the manifest-inventory mismatch, not separate defects. The one gap round should resolve all confirmed contract groups before candidate freeze. Keep the existing one-plan structure, original requirement ownership/statuses, D-209 accepted gaps, Acid2 failure, release assets, and branch protection unchanged. Add no dependency. Run cheap syntax, identity, and inventory checks first, then only the focused existing CTests needed for the changed contracts; no broad local suite, Acid2 execution, excluded game/ROM case, candidate expansion, Task 7, Phase 24 verification, or milestone audit/archive.

If execution is later authorized, obtain one fresh independent review of the exact candidate after focused checks, then spend one new exact-head protected PR matrix through the existing branch-protected PR. Existing admitted game/fixture cases may run only within that matrix; Acid2 and excluded gbmicrotest cases remain blocked. Any focused failure, unresolved review finding, timeout without diagnosis, or failed/missing/skipped/stale required context ends the scope without another correction, review, or matrix. The original D-211 run must finish before a new candidate is pushed. Keep this recovery worktree until successful protected merge and reconciliation to clean `main`; do not switch/remove it during the recovery. The current next route is `$gsd-plan-phase 24` against the sole existing plan. No phase is newly complete, and v0.5 remains unstarted.

## D-213 Post-T10 discussion and integrated replan (owner-directed, 2026-11-18)

The owner selected all three discussion areas—path-linter policy, the immutable candidate boundary, and the recovery boundary—and asked for the synthesized recommendations to be followed. This records planning direction only. It does not authorize source edits, tests, a commit, push, review, CI, merge, phase verification, or milestone closure. The old T10–T12 execution round stays stopped; any new execution requires separate authorization after the replan.

### Path-linter policy

T10's required `verify-no-phase-paths.py --check --report` measured 30 occurrences in `verify-planning-hygiene.py` against the pinned count of 1. The two strings added during T10 were removed, but the failed check was not rerun. The continuation record identifies 28 occurrences already present at the candidate plus the two new occurrences. The checker counts lexical spellings; the target file uses paths for immutable Git reads and disposable self-test fixtures as well as historical records. Raising the value to 30 would unblock the scan but preserve a same-count substitution risk. The recommendation is a standard-library structural/context contract for this one file, with causal negatives that still reject live readers; keep the general scan and other exact exceptions intact.

### Immutable candidate boundary

The active Phase 24 root-roadmap route is present only in dirty planning edits and is absent from candidate `96d502d`. A `git show <rev>:<path>` check reads the blob/tree stored by that commit, so it cannot see the working-tree route ([Git revision syntax](https://git-scm.com/docs/gitrevisions)). The replan should permit one local, unpushed documentation-only commit before implementation, with the active route and matching handoff. It must exclude the three modified T10 checker files. Cheap preflight should prove the root route, sole plan pointer, archived v0.4 sources, and ancestry in the exact immutable commit before any configure or expensive test.

### Recovery boundary and execution route

Do not reinterpret the failed T10 gate as permission to resume the prior attempt, and do not start T11/T12 under that attempt. Replan the existing `24-01-PLAN.md` with D-212's six integration blockers and the newly exposed stale path-count contract. When later authorized, allow ordinary local diagnose/fix/retest cycles for in-scope changes until the cheap and focused gates are clean; no arbitrary one-run cap applies to local development feedback. Keep the previously scoped single fresh exact-head review and single protected PR matrix as final qualification spends, after all local gates pass. A new out-of-scope trust/correctness gap, an unresolved review finding, or failed/missing required CI context returns the work to the owner without another candidate cycle. Do not change D-209 requirement dispositions, replay Acid2 or excluded gbmicrotest cases, execute Task 7, run the broad local suite, or start v0.5.

### CI/CD efficiency finding

Read-only GitHub run records show D-211 CI [44189691301](https://github.com/szTheory/gabbaboy/actions/runs/44189691301) took about 70 minutes end-to-end. Linux ran a 1,943-test CTest stream for about 37 minutes and reported 44 failures, including the dense-input, phase-path, archived-evidence, trusted-checker, plan-cap, hygiene, and state-fork integration failures already covered by D-212. The related preview run [44189691412](https://github.com/szTheory/gabbaboy/actions/runs/44189691412) had three platform consumer jobs wait about 70 minutes each for exact-head CI; all then failed before their package configure/build/smoke steps. The next candidate should pass the scoped local preflight before push and the eventual CI handoff should record timings again. The standing policy remains in `.planning/context/WORKFLOW.md#cicd-efficiency`.

The three long-lived package waiters are a measured efficiency follow-up: `wait-exact-head-ci.py` waits for the overall workflow to complete before checking required-job results. Assess whether it can stop package consumers safely after an exact current-attempt required job becomes terminally failed, with explicit rerun/debounce and exact-SHA controls. Keep every required CI job and package/source binding. Do not change workflow triggers to `workflow_run`; the existing workflow-policy contract forbids it. This waiter redesign is outside the current recovery plan.

**Next route:** `$gsd-plan-phase 24 --skip-research` reuses the existing research and revises the sole plan. No phase is complete. After the revised plan and its independent plan check pass, the owner acts next to authorize or decline execution; then use `$gsd-execute-phase 24` only if separately authorized.
