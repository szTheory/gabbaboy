# Roadmap: GabbaBoy

## Milestones

- ✅ **v0.1 Limited DMG Preview** — Phases 1–6 and 06.1, shipped 2026-10-10; [archive](milestones/v0.1-ROADMAP.md).
- ✅ **v0.2 Color & Cartridge Breadth** — Phases 7–15 and 15.1, shipped 2026-10-24; [archive](milestones/v0.2-ROADMAP.md).
- ✅ **v0.3 Save States & Host Contract** — Phases 16–19, 35 plans, shipped 2026-10-31; [archive](milestones/v0.3-ROADMAP.md).
- ⚠️ **v0.4 Evidence Floor** — Phase 23.1 is complete with verification passed 18/18. D-203 Task 11 fixed CR-07, its sole exact-candidate review is clean, and the two authorized focused CTests passed. The owner chose to keep v0.4 open without accepting the four Pending requirements and authorized one Phase 24 rescope under D-205. Phase 24 execution and automated closure are complete, but its fresh independent review found Critical CR-01: a BOM-prefixed YAML frontmatter fence can bypass the Phase 24 gap-plan guard. Phase 24 is blocked before verification; the prior bounded fix/review pass is exhausted. The owner acts next to decide whether to authorize a new bounded recovery. Preserve the 40-plan ceiling and all existing limits. D-103's exact-final-head broad suite remains unfulfilled; no third lifecycle retest, release retry, fixture admission or rights action is authorized. See [23.1 verification](phases/GB-23.1-close-v0-4-requirement-and-verification-gaps/23.1-VERIFICATION.md), [23.1 review](phases/GB-23.1-close-v0-4-requirement-and-verification-gaps/23.1-REVIEW.md), [Phase 24 review](phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-REVIEW.md), and [audit](v0.4-MILESTONE-AUDIT.md).

## v0.4 — Evidence Floor

**Goal:** Establish a reproducible floor for CGB game progress and rendering evidence before deeper timing work, or document a specific reason neither named game candidate could be admitted.

The two substantive tracks are CGB game acceptance with scene regressions, and diagnostic admission. A capped tune-up establishes the fixture boundary first; a qualified release closes the milestone. The approved scope is in [REQUIREMENTS.md](REQUIREMENTS.md), with decisions and future candidates in [DECISIONS.md](context/DECISIONS.md) and [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md).

## Phases

Numbering continues after completed Phase 19. Decimal phases are reserved for explicitly approved insertions.

- [x] **Phase 20: Fixture Admission Tune-up** — New evidence enters through a checked rights and distribution boundary. Nine plans and exact-head hosted platform/package qualification are complete; RIGHTS-01 remains pending because no fixture was admitted.
- [x] **Phase 21: CGB Game Progress and Scene Regressions** — The shared runner proves CGB progress and records the bounded game-candidate outcome. (completed 2026-11-02)
- [x] **Phase 22: Synthetic Composition and Diagnostic Gate Assessment** — Preserve synthetic composition evidence and machine-check why the real diagnostic candidates remain unadmitted. Completed 2026-11-03; DIAG-01, DIAG-02, and RIGHTS-01 remain pending because all seven real-fixture gates remain unresolved.
- [x] **Phase 23: Qualified v0.4.0 Release** — Published artifacts and support records carry only the evidence actually established. (completed 2026-11-13)
- [x] **Phase 23.1: Close v0.4 requirement and verification gaps** (completed 2026-11-16)
- [ ] **Phase 24: Resolve remaining v0.4 evidence and verification gaps**

## Phase Details

### Phase 20: Fixture Admission Tune-up

**Goal**: Maintainers can admit permitted evidence through one checked fixture and distribution boundary before new game or diagnostic bytes enter public automation.
**Depends on**: Phase 19, completed and archived
**Requirements**: RIGHTS-01
**Success Criteria** (what must be TRUE):
  1. A fixture can enter the repository and public CI only when exact bytes, source/build inputs, and terms for its code, art, audio driver, and notices are recorded; incomplete rights or changed identities are rejected by automated controls.
  2. An installed or product-release package containing a controlled game-ROM insertion is rejected, while a valid package retains the required component notices and GabbaBoy's MIT declaration.
**Plan cap**: 9
**Plans**: 9 total: three original plans, the consumed single security gap round (20-04), and five owner-authorized ordinary rescope plans (20-05–20-09). Final-review security follow-ups remain inside existing plans: retain publisher metadata/cleanup/Windows containment, source/core metadata bounds and forbidden-digest work; the final product review now reopens 20-02 at Task 5 for a separate archive-wide extension-header count while retaining its chain cap. No plan or gap round is added.

Plans:
**Wave 1**
- [x] 20-01-PLAN.md — Versioned admission records, independent identity pins and shared exact product policy.

**Wave 2** *(ready after Wave 1 completion)*
- [x] 20-02-PLAN.md — Actual core install/archive/release boundary; metadata and archive-wide extension-header bounds delivered with long-path compatibility.
- [x] 20-03-PLAN.md — Actual macOS player package and notice boundary with mutation controls; hosted final qualification remains an orchestration gate.

**Wave 3** *(single in-scope security gap closure)*
- [x] 20-04-PLAN.md — Bound fixture filesystem traversal and Git tree enumeration.

**Wave 4** *(authorized rescope; original plans remain intact)*
- [x] 20-05-PLAN.md — Independently pin product policy and exports/budgets; reject forbidden digests at every regular path, including generated/one_of core/player entries.
- [x] 20-07-PLAN.md — Match repository-admission commands exactly and repair complete isolated workflow mutation subjects.
- [x] 20-08-PLAN.md — Align shared notice-contract consumers and their negative controls with the reviewed source/product distinction.

**Wave 5** *(after the indicated Wave 4 dependencies)*
- [x] 20-06-PLAN.md — Validate downloaded macOS and Windows product bytes with trusted checker/policy; metadata, cleanup and pre-creation path containment controls complete.
- [x] 20-09-PLAN.md — Restore dense-input source-only mutant configure with separate immutable baseline evidence and unqualified-build controls.

Use existing checks to assess CI headroom, current documentation, and carry-over dispositions while establishing this boundary. Preserve the accepted v0.3 audit debts and standalone closeout-helper failure unless a documented trigger actually applies. The admission contract remains mandatory when later phases add fixtures; RIGHTS-01 has this single owner phase.

### Phase 21: CGB Game Progress and Scene Regressions

**Goal**: Maintainers can obtain a reproducible CGB progress result from the shared runner, explain the bounded game-candidate outcome, and turn useful scene reports into controlled regressions.
**Depends on**: Phase 20
**Requirements**: GAME-01, GAME-02, FIXT-01, FEED-01
**Success Criteria** (what must be TRUE):
  1. The existing acceptance runner observes RGB555 output and guest progress on the bootless CGB-CPU-E software profile, confirms the selected ROM's CGB execution mode, and preserves the existing DMG acceptance behavior.
  2. A positive CGB progress case reaches an independently specified guest predicate through meaningful scripted input; no-input/wrong-input or deliberately broken-predicate controls fail, and the result binds the ROM, profile/mode, inputs, predicate, and frame/PCM observations. An original control fixture may prove the harness when no real game is admitted, and is labeled accordingly.
  3. Potion Panic's GB Compo 2025 demo is assessed first in one bounded admission/build/predicate plan. Only after its recorded no-go may one bounded µCity 1.3 preferred-ucity.gbc fallback plan run; each records exact source/build, digest, cartridge metadata, native CGB mode, and the Phase 20 rights decision. No third game search begins.
  4. An admitted game has a bound progress result with failing controls. If neither named candidate clears its gate, the evidence names each actual rights, build, predicate-feasibility, harness, or emulation blocker and the concrete harness result delivered; private play, test-ROM passes, and original fixtures are not presented as admitted game evidence.
  5. A concise title/scene/symptom report can be taken through agent-owned metadata recovery, reproduction, and fault classification without mandatory owner play. Any automated scene regression has an independently reasoned expectation and negative control; personal ROMs, saves, states, and captures stay private.
**Plan cap**: 8
**Plans**: All eight Phase 21 plan files remain complete; the active cap is 8 after its last unused ordinary slot was reallocated to the owner-approved Phase 23.1 reconciliation. Seven primary plans and the existing single gap plan fill this cap. No Phase 21 plan, scope, or evidence changed. Plan 21-08 remains the single completed gap-work plan; after CR-04/CR-05 closure it reopened within that same plan for CR-06 and completed with exact 24-input qualification and source-drift controls. No additional plan or gap round was added. PR #140 final head `507019f9` passed required exact-head CI, fixture reproduction, installed consumers, and player-package smoke, then squash-merged as `bef2cfbd`; Phase 22 proceeds under the separate owner-approved D-141 scope.

Plans:
**Wave 1**
- [x] 21-01-PLAN.md — Shared native-CGB progress tracer, original generated control and preserved Libbet/DMG policy.
- [x] 21-03-PLAN.md — Source-bound two-candidate record/admission contract with real-CLI controls.

**Wave 2** *(blocked on the indicated Wave 1 dependencies)*
- [x] 21-02-PLAN.md — Input/predicate discrimination and independently specified original RGB555 observation controls.
- [x] 21-06-PLAN.md — Minimal scene intake, agent-owned reproduction procedure and independent/private-data promotion gates.

**Wave 3** *(blocked on Plans 21-02 and 21-03)*
- [x] 21-04-PLAN.md — One bounded Potion Panic GB Compo 2025 source/build/rights/native-progress attempt or actual no-go.

**Wave 4** *(blocked on the primary's final disposition)*
- [x] 21-05-PLAN.md — Sole conditional preferred µCity 1.3 fallback or checked not-needed outcome.

**Wave 5** *(blocked on controls, the final candidate pair and scene workflow)*
- [x] 21-07-PLAN.md — Actual outcome/documentation composition, final source qualification and Phase 21 handoff.

**Wave 6** *(single reserved gap round after final review)*
- [x] 21-08-PLAN.md — Separate historical provenance from current CMake artifact qualification and bind replay to exact aggregate RGB555/PCM observations.

Captured frame and PCM digests establish reproducibility. They do not independently establish rendering accuracy, perceptual quality, physical CGB-E behavior, or general compatibility. A newly reproduced correctness/security issue must be fixed within scope or trigger a rescope; the candidate absence exit cannot silently defer it. Optional direct Steam Deck/SSH exploration is neither a completion gate nor a qualified Linux/Deck path.

### Phase 22: Synthetic Composition and Diagnostic Gate Assessment

**Goal**: Maintainers can reproduce the synthetic, source-anchored composition tracer and inspect a machine-checked, metadata-only assessment explaining why real diagnostic fixtures remain unadmitted.
**Depends on**: Phase 21
**Requirements**: DIAG-01, DIAG-02
**Success Criteria** (what must be TRUE):
  1. The original synthetic composition tracer runs through the compiled runner with its fixed source-cell mask, exact unmasked comparison, and negative controls for altered identities, masks, and images.
  2. A source-bound metadata-only inventory retains all 513 named gbmicrotest source/ROM pairs and records each unresolved acid2/gbmicrotest admission gate; the approval command refuses while required evidence is unresolved.
  3. Documentation and automated checks keep the tracer labeled synthetic-only, record the real-fixture no-go without asserting a license prohibition, and leave DIAG-01, DIAG-02, and RIGHTS-01 Pending.
**Phase-scoped acceptance override**: Owner-approved on 2026-11-03; see [22-RESCOPE.md](phases/GB-22-composition-and-microtest-evidence/22-RESCOPE.md) and D-141. Phase 22's revised roadmap criteria are the acceptance contract. The original meanings of DIAG-01/02 and RIGHTS-01 are unchanged and remain Pending. No real upstream diagnostic payload is fetched, built, run, admitted, or claimed.
**Plan cap**: 12
**Plans**: Five live plans, all with summaries. The D-143 C1 correction and review, final 1,732/1,732 local suite, and PR #142 exact-head qualification are complete. PR #142 merged as `ca2f0be6`; PR #143 addressed the post-merge Windows CTest timeout and merged as `4eee5b51`. Its post-merge main CI run `41715210158`, fixture-reproduction run `41715210637`, and release-please run `41715210175` all passed. PR #144 recorded the completed handoff and passed protected checks; its post-merge planning CI run `41721377525`, fixture-reproduction run `41721377486`, and release-please run `41721377533` passed. Local main was reconciled with `origin/main` while preserving the original local v0.4 commits. Seven original plans are superseded under D-141 and excluded from execution.
**Boundary**: Phase 22 is complete at its approved metadata-only scope. The final local suite, exact-head required checks and package artifacts, reviews, branch-protection qualification, and merge-tree equivalence passed for PR #142. The separate post-merge Windows scheduling recovery, successful main CI, final docs handoff, and local-main reconciliation are recorded in the Phase 22 evidence; Phase 23 remains unstarted and owner-controlled.
**Execution waves**: Five sequential dependency waves: 22-01 (complete) → 22-02 (close the existing metadata assessment) → 22-10 (immutable no-go contract and public claims) → 22-11 (initial qualification) → 22-12 (D-143 C1 correction, independent review and final qualification). Original 22-03 through 22-09 carry machine-readable `status: superseded` and must not dispatch.

Plans:
**Wave 1**
- [x] 22-01-PLAN.md — Preserve the completed original synthetic composition tracer and controls.

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 22-02-PLAN.md — Close the committed metadata assessment under the approved rescope; preserve the seven refused gates and Pending requirements.

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 22-10-PLAN.md — Check immutable metadata, exact 513-name inventory, no-go/public claims, test membership and current source/package boundaries.

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 22-11-PLAN.md — Qualify final local/review/security/remote evidence, generate automated closure and pause before `/gsd-discuss-phase 23`.

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 22-12-PLAN.md

The source coverage and dependency audit is [22-SOURCE-AUDIT.md](phases/GB-22-composition-and-microtest-evidence/22-SOURCE-AUDIT.md). Completed tracer and assessment commits are preserved; real-fixture build/admission/execution and downloaded-lifecycle work are outside the approved Phase 22 scope. Original requirement definitions and existing fixture-admission/package boundaries remain intact.

### Phase 23: Qualified v0.4.0 Release

**Status**: Phase complete; the milestone audit found gaps, and Phase 23.1 is complete with verification passed 18/18. Its D-203 Task 11 correction fixed CR-07 and the sole exact-candidate review is clean. The owner confirmed the recorded Task 11 → review → verification-only sequence; only the two authorized focused CTests ran. The owner chose to keep v0.4 open and authorized one Phase 24 rescope under D-205. No gaps were accepted and archival is stopped. D-103 and all unrelated suite, lifecycle, release, fixture and rights limits remain unchanged.

**Goal**: Users receive a qualified v0.4.0 release whose packages and support records accurately describe the established CGB game and diagnostic evidence.
**Depends on**: Phase 22
**Requirements**: REL-01
**Success Criteria** (what must be TRUE):
  1. Final implementation-head qualification and the existing trusted release rehearsal pass for the reviewed revision with required hosted coverage, consumer evidence, and regression controls; earlier phase evidence remains historical and is not repeatedly refreshed.
  2. Release notes and the support ledger identify an admitted game's exact software-model progress result or the justified absence after the two named attempts, distinguish diagnostic and reproducibility observations, and retain hardware, perceptual, timing, platform, and compatibility limits.
  3. Published/downloaded artifact identities and digests reconcile with the release source, installed consumers work against those bytes, required license/component notices are present, and the fixture-exclusion checks accept the real packages and reject their game-ROM insertion control.
**Plan cap**: 10
**Plans**: All nine scheduled plans are complete in the existing dependency order. The cap of 10 retains its reserved gap slot; no plan or milestone was added.

Plans:
**Wave 1**
- [x] 23-01-PLAN.md — Generate the source-bound v0.4 support ledger and preserve evidence limits.

**Wave 2**
- [x] 23-02-PLAN.md — Generate concise release notes from the same checked evidence.

**Wave 3**
- [x] 23-03-PLAN.md — Bind the complete release claim and require observed exact release-please output.

**Wave 4**
- [x] 23-09-PLAN.md — Fix incomplete raw-HTML visibility bypasses in the existing notes/docs/changelog validators and add causal automated controls.

**Wave 5**
- [x] 23-04-PLAN.md — Reissue all three independent source-bound reports after the visibility fix, gate their committed evidence and qualify the implementation head.

**Wave 6**
- [x] 23-07-PLAN.md — Apply the observed 0.4.0 state-version policy before version freeze.

**Wave 7**
- [x] 23-05-PLAN.md — Prepare the version PR and use the existing trusted release lifecycle.

**Wave 8**
- [x] 23-06-PLAN.md — Reconcile downloaded release evidence and generate automated phase closure.

**Wave 9**
- [x] 23-08-PLAN.md — Record transferable lessons and stop at the owner-controlled milestone boundary.

Use the existing release path. RM-032 tooling is not an automatic work list; only a concrete release blocker can justify a narrowly scoped required change. Keep full libretro, supported Linux/Steam Deck gameplay, CGB timing rewrites, license migration, and a libfuturo dependency or early API/state freeze outside this milestone.

The [source coverage and dependency audit](phases/GB-23-qualified-v0-4-0-release/23-SOURCE-AUDIT.md), [research](phases/GB-23-qualified-v0-4-0-release/23-RESEARCH.md), and [execution contract](phases/GB-23-qualified-v0-4-0-release/23-EXECUTION-CONTRACT.md) preserve the evidence basis and execution limits. The spec-less probe's unclassified REL-01 edge and two descriptor-less transparency prohibitions remain explicitly flagged.

### Phase 23.1: Close v0.4 requirement and verification gaps (INSERTED)

**D-202 sole review outcome (historical):** The independent review examined source candidate `af36fa2f4c0f35dc6b537a3e736f5cd264b83593` at pre-review HEAD `cb4bf5685fe5145bf3bd9b3cd088ed84af067a2d`. It closed CR-05 and CR-06, confirmed carried CR-01/CR-02/CR-03/CR-04/WR-01 did not regress, and found CR-07: a non-ASCII whitespace prefix made a nonblank disposition row terminate parsing silently. D-203 later fixed CR-07. The D-201 report archive remains byte-identical to its source provenance at `01420b899f19e868aa66b4e3f5792b64736d5623` (5,274 bytes; SHA-256 `3e0d753fdabc0df22fa8808ad8e6427ea9213c45d5df7557b3e81c90269e4405`). The Task 10 checks are recorded against the exact candidate in [23.1-REVIEW-FIX.md](phases/GB-23.1-close-v0-4-requirement-and-verification-gaps/23.1-REVIEW-FIX.md).

**Goal:** Maintainers can inspect an accurate Phase 22 verification report reconstructed from immutable Phase 22 boundary evidence and a current handoff explaining why v0.4 stays open under the preserved limits.
**Requirements**: []
**Requirement disposition**: No new requirement assignments. FIXT-01 remains owned by Phase 21, RIGHTS-01 by Phase 20, and DIAG-01/DIAG-02 by Phase 22; all four remain Pending.
**Depends on:** Phase 23
**Success Criteria** (what must be TRUE):
  1. The existing cap checker accepts only the owner-approved fifth-phase insertion 23.1 with caps 9/8/12/10/1 and the single gap plan, while rejecting other fifth phases, a sixth phase, excess caps, and consumption of a reserved gap slot by an ordinary plan.
  2. `22-VERIFICATION.md` records the approved synthetic-plus-metadata Phase 22 result from immutable implementation and evidence boundaries, including 513 names, seven unresolved gates, admitted=0, executed=0, the exact no-go facts, and Pending original requirements. Historical Phase 20/21 reports and the milestone audit snapshot stay unchanged.
  3. Current state, project summary, and the Phase 23.1 handoff link the new report only after it exists, preserve stale Phase 20/21 status and four Pending requirements, and receive machine-checked SUMMARY/UAT closure without claiming milestone completion.
**Plan cap**: 1
**Plans:** The single plan's original tasks and D-194 through D-203 recovery history are recorded in its SUMMARY and review-fix log. D-203 Task 11 fixed CR-07 at source candidate `00f69d9b4a12811912f247873eef6e49cc3bac1d`; its exact-candidate review is clean, the two authorized focused CTests passed, and [23.1-VERIFICATION.md](phases/GB-23.1-close-v0-4-requirement-and-verification-gaps/23.1-VERIFICATION.md) passed 18/18 after owner confirmation of the recorded route. Phase 23.1 is complete. The owner authorized Phase 24 under D-205; its one-plan proposal passed independent review. The original `$gsd-execute-phase 24` route is historical because Phase 24 execution and automated closure are complete. The Phase 24 review then found Critical CR-01 on the BOM-prefixed YAML gap-plan bypass; the verifier did not run. Owner action next: `$gsd-discuss-phase 24` to decide whether to authorize a new bounded recovery. The existing 40-plan ceiling and all other scope limits remain in force.

Plans:
- [x] 23.1-01-PLAN.md — Enforce the exact cap exception, reconstruct Phase 22 verification from immutable evidence, and reconcile the open-milestone handoff with automated closure; D-203 Task 11 and its sole review are complete, and phase verification passed 18/18.

## Requirement Coverage

| Requirement | Owner phase |
|-------------|-------------|
| RIGHTS-01 | Phase 20 |
| GAME-01 | Phase 21 |
| GAME-02 | Phase 21 |
| FIXT-01 | Phase 21 |
| FEED-01 | Phase 21 |
| DIAG-01 | Phase 22 |
| DIAG-02 | Phase 22 |
| REL-01 | Phase 23 |

All eight v1 requirements have one owner phase. Cross-phase use of the admission and regression contracts does not create duplicate ownership.

## Progress

**Execution order:** 20 → 21 → 22 → 23 → 23.1, with an owner pause after every phase.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 20. Fixture Admission Tune-up | 9/9 | Complete; RIGHTS-01 remains pending because no fixture was admitted | 2026-11-01 |
| 21. CGB Game Progress and Scene Regressions | 8/8 | Complete; PR #140 passed exact-head checks and merged as `bef2cfbd` | 2026-11-02 |
| 22. Synthetic Composition and Diagnostic Gate Assessment | 5/5 | Complete; exact-head qualification and merge passed; DIAG-01/02 and RIGHTS-01 remain pending | 2026-11-03 |
| 23. Qualified v0.4.0 Release | 9/9 | Complete    | 2026-11-13 |
| 23.1. Close v0.4 requirement and verification gaps | 1/1 | Complete    | 2026-11-16 |

## Planning and Approval Boundary

- At most four phases and 40 plans; at most 12 plans in any phase. The owner approved one exact exception for the active v0.4 phase set 20/21/22/23/23.1: Phase 23.1 is its sole fifth phase, limited to one `gap_closure: true` reconciliation plan. Active caps are 9/8/12/10/1 (40 combined), including each phase's reserved gap slot. Phase 21's unused ordinary slot funds Phase 23.1; its seven primary plans and one existing gap plan are unchanged. There are 39 actual plan files after planning Phase 23.1. All other fifth phases and a sixth phase remain forbidden; future milestones retain the normal four-phase rule. This exception grants no new fixture, rights, release, review-round, gap-round, or milestone-close authority. See D-193. Phase 20's gap slot is consumed by 20-04; its five rescope additions are ordinary plans. These are scope caps, not acceptance evidence. D-194/D-195/D-196 record narrow same-plan recovery cycles and their exhausted stops; they do not increase the one-plan cap or renew any resource limit. D-197 authorizes autonomous orchestration through the remaining v0.4 lifecycle after a bounded recovery is discussed and authorized; D-199 authorized Task 7 and its one review, and D-200 authorizes the current Task 8 and one independent review only. This does not waive blockers, required owner decisions, D-103 or other explicit limits.
- Every deliverable has an automated check and a meaningful negative control. New reusable checkers live in tests/scripts/, use immutable commit facts where appropriate, and enter CTest when created. Automated UAT closure uses the existing shared closure tool; voluntary play is not a release gate.
- Preserve the deterministic performance budget and existing state-continuation behavior. Prefer the existing API and local helpers; new dependencies require demonstrated value.
- Both automatic-advance flags remain false. The owner approved the original Phase 20 roadmap on 2026-10-31; the single permitted security gap round became Plan 20-04. On 2026-11-01 the owner authorized an explicit Phase 20 rescope: trusted final macOS/Windows downloaded-byte checks, independent product-policy identity, exact repository-admission workflow matching, and attributable notice/export/dense-input/mutation-subject/timeout/planning-cap contract repairs. No fixture admission, legal/rights disposition change, accepted v0.3 debt repair, or sandbox-only Git-worktree code repair is authorized by this rescope.

Phase 20 completed with no admitted fixture; RIGHTS-01 remains pending. Phase 21's eight plans and five roadmap criteria are verified; its owner-approved disposition leaves FIXT-01 pending without claiming a license grant or candidate ROM. Phase 22's five plans and approved D-141/D-143 scope are complete. The final configured local suite passed 1,732/1,732; PR #142's exact head passed required CI, fixture reproduction, package artifacts, independent reviews, branch protection, and merge-tree equality before squash merge. The merged tree preserves the metadata-only assessment: seven real-fixture gates unresolved, admitted=0, executed=0; DIAG-01, DIAG-02, and RIGHTS-01 remain pending, with no license prohibition inferred. The post-merge Windows timeout and its recovery are recorded in [Phase 22 final evidence](phases/GB-22-composition-and-microtest-evidence/22-EVIDENCE.md). Phase 23 — Qualified v0.4.0 Release — is the next phase, remains unstarted and owner-controlled through **/gsd-discuss-phase 23**. Both automatic-advance flags remain false.

### Phase 24: Resolve remaining v0.4 evidence and verification gaps

**Goal:** Maintainers can inspect one additive, commit-pinned map of all eight original v0.4 requirements and Phase 20/21 freshness, with original criteria and owners, tracker statuses, milestone-audit dispositions, historical report results, current freshness, evidence boundaries, and exact remaining gates kept distinct.
**Requirements**: GAME-01, GAME-02, FIXT-01, RIGHTS-01, DIAG-01, DIAG-02, FEED-01, REL-01 (assessment coverage only; original owners and completion meanings remain unchanged)
**Depends on:** Phase 23.1
**Success Criteria** (what must be TRUE):
  1. A source-backed eight-requirement map reads an exact immutable input containing the assessed tracker, audit, decisions and historical reports; its later containing commit is a separate identity.
  2. Phase 20/21 reports and original identities remain unchanged and historical, their current stale audit observations stay explicit, and focused Phase 24 results are point-in-time evidence rather than refreshed phase verification or satisfaction of D-103.
  3. The existing planning-hygiene CLI accepts canonical committed evidence and causally refuses false requirement completion, owner drift, freshness promotion, source substitution, milestone closure and excess plan capacity; no dependency, checker, CTest or CI identity is added.
  4. Only the existing plan_cap and planning_hygiene_controls CTests run after cheap syntax/direct controls, retaining the existing timeout; shared SUMMARY/UAT closure validates this assessed deliverable without satisfying the four Pending requirements or closing v0.4.
**Plan cap**: 1
**Plans:** Exactly one ordinary plan (`24-01-PLAN.md`); no Phase 24 gap reserve.

**D-205 bounded exception:** The owner approved only the exact active v0.4 phase set 20/21/22/23/23.1/24. See D-205. This supersedes the earlier sixth-phase prohibition only for Phase 24 and preserves historical caps 9/8/12/10/1. Phase 24 has one ordinary plan and no new gap reserve; independently enforce no more than 40 actual plan files. The extra declared allowance does not authorize 41 actual plans, a changed historical cap, another sixth/seventh phase, or renewed review/gap/test/lifecycle/release/fixture/rights capacity. The earlier D-193 five-phase statement above is historical to that boundary and is superseded only on this exact point.

**Boundary:** Completing the Phase 24 assessment can coexist with FIXT-01, RIGHTS-01, DIAG-01 and DIAG-02 remaining Pending under Phases 21, 20, 22 and 22. Keep v0.4 open and its audit gaps_found. No broad suite, third lifecycle retest, release/tag/asset operation, payload acquisition, build/run/admission, rights action or archival is authorized. Both auto-advance flags remain false.

Plans:
- [x] 24-01-PLAN.md — Add the immutable all-eight gap assessment, causal controls and exact D-205 cap exception; record only the two focused CTests and shared automated closure.

**Current handoff:** Phase 24 execution and automated closure are complete, but its fresh independent review found Critical CR-01: a BOM-prefixed YAML frontmatter fence lets a `gap_closure: true` plan bypass the plan-cap guard. Phase 24 is blocked before verification and the prior bounded fix/review pass is exhausted. The owner acts next with `$gsd-discuss-phase 24` to decide whether to authorize a new bounded recovery; only after an authorized correction, clean independent review, and the configured focused regression hook may the orchestrator run `$gsd-verify-work 24`. This route preserves every remaining milestone gate and safety stop.
