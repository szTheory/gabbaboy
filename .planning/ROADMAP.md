# Roadmap: GabbaBoy

## Milestones

- ✅ **v0.1 Limited DMG Preview** — Phases 1–6 and 06.1, shipped 2026-10-10; [archive](milestones/v0.1-ROADMAP.md).
- ✅ **v0.2 Color & Cartridge Breadth** — Phases 7–15 and 15.1, shipped 2026-10-24; [archive](milestones/v0.2-ROADMAP.md).
- ✅ **v0.3 Save States & Host Contract** — Phases 16–19, 35 plans, shipped 2026-10-31; [archive](milestones/v0.3-ROADMAP.md).
- 🚧 **v0.4 Evidence Floor** — Phases 20–23, roadmap owner-approved; Phase 20 is complete, with RIGHTS-01 still pending because no fixture was admitted.

## v0.4 — Evidence Floor

**Goal:** Establish a reproducible floor for CGB game progress and rendering evidence before deeper timing work, or document a specific reason neither named game candidate could be admitted.

The two substantive tracks are CGB game acceptance with scene regressions, and diagnostic admission. A capped tune-up establishes the fixture boundary first; a qualified release closes the milestone. The approved scope is in [REQUIREMENTS.md](REQUIREMENTS.md), with decisions and future candidates in [DECISIONS.md](context/DECISIONS.md) and [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md).

## Phases

Numbering continues after completed Phase 19. Decimal phases are reserved for explicitly approved insertions.

- [x] **Phase 20: Fixture Admission Tune-up** — New evidence enters through a checked rights and distribution boundary. Nine plans and exact-head hosted platform/package qualification are complete; RIGHTS-01 remains pending because no fixture was admitted.
- [x] **Phase 21: CGB Game Progress and Scene Regressions** — The shared runner proves CGB progress and records the bounded game-candidate outcome. (completed 2026-11-02)
- [ ] **Phase 22: Synthetic Composition and Diagnostic Gate Assessment** — Preserve synthetic composition evidence and machine-check why the real diagnostic candidates remain unadmitted.
- [ ] **Phase 23: Qualified v0.4.0 Release** — Published artifacts and support records carry only the evidence actually established.

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
**Plan cap**: 10
**Plans**: 8/10 plans used — the cap preserves two honest reserve slots while covering the eight plan files, including the single gap-work plan. The primary and fallback candidate attempts each occupy one conditional plan. Plan 21-08 is the single reserved gap round; after CR-04/CR-05 closure it reopened within that same plan for CR-06 and completed with exact 24-input qualification and source-drift controls. No additional plan or gap round was added. PR #140 final head `507019f9` passed required exact-head CI, fixture reproduction, installed consumers, and player-package smoke, then squash-merged as `bef2cfbd`; Phase 22 proceeds under the separate owner-approved D-141 scope.

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
**Plans**: 4 live plans (22-01, 22-02, 22-10 complete; 22-11 closure and boundary prepared; full local suite evidence recorded, final exact-head PR gate determines boundary status); 7 original plans are superseded under D-141 and excluded from execution.
**Boundary candidate**: Phase 22 is complete only after the final exact-head required checks, package artifacts, reviews, and merge-tree equivalence pass. Until then, Phase 22 remains conditional and Phase 23 stays unstarted.
**Execution waves**: Four sequential dependency waves: 22-01 (complete) → 22-02 (close the existing metadata assessment) → 22-10 (immutable no-go contract and public claims) → 22-11 (local/review/security/exact-head remote qualification and boundary). Original 22-03 through 22-09 carry machine-readable `status: superseded` and must not dispatch.

Plans:
**Wave 1**
- [x] 22-01-PLAN.md — Preserve the completed original synthetic composition tracer and controls.

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 22-02-PLAN.md — Close the committed metadata assessment under the approved rescope; preserve the seven refused gates and Pending requirements.

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 22-10-PLAN.md — Check immutable metadata, exact 513-name inventory, no-go/public claims, test membership and current source/package boundaries.

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 22-11-PLAN.md — Qualify final local/review/security/remote evidence, generate automated closure and pause before `/gsd-discuss-phase 23`.

The source coverage and dependency audit is [22-SOURCE-AUDIT.md](phases/GB-22-composition-and-microtest-evidence/22-SOURCE-AUDIT.md). Completed tracer and assessment commits are preserved; real-fixture build/admission/execution and downloaded-lifecycle work are outside the approved Phase 22 scope. Original requirement definitions and existing fixture-admission/package boundaries remain intact.

### Phase 23: Qualified v0.4.0 Release

**Status**: Unstarted and owner-controlled; after Phase 22 qualifies, the next action is `/gsd-discuss-phase 23`.

**Goal**: Users receive a qualified v0.4.0 release whose packages and support records accurately describe the established CGB game and diagnostic evidence.
**Depends on**: Phase 22
**Requirements**: REL-01
**Success Criteria** (what must be TRUE):
  1. Final implementation-head qualification and the existing trusted release rehearsal pass for the reviewed revision with required hosted coverage, consumer evidence, and regression controls; earlier phase evidence remains historical and is not repeatedly refreshed.
  2. Release notes and the support ledger identify an admitted game's exact software-model progress result or the justified absence after the two named attempts, distinguish diagnostic and reproducibility observations, and retain hardware, perceptual, timing, platform, and compatibility limits.
  3. Published/downloaded artifact identities and digests reconcile with the release source, installed consumers work against those bytes, required license/component notices are present, and the fixture-exclusion checks accept the real packages and reject their game-ROM insertion control.
**Plan cap**: 9
**Plans**: TBD — within the cap.

Use the existing release path. RM-032 tooling is not an automatic work list; only a concrete release blocker can justify a narrowly scoped required change. Keep full libretro, supported Linux/Steam Deck gameplay, CGB timing rewrites, license migration, and a libfuturo dependency or early API/state freeze outside this milestone.

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

**Execution order:** 20 → 21 → 22 → 23, with an owner pause after every phase.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 20. Fixture Admission Tune-up | 9/9 | Complete; RIGHTS-01 remains pending because no fixture was admitted | 2026-11-01 |
| 21. CGB Game Progress and Scene Regressions | 8/8 | Complete; PR #140 passed exact-head checks and merged as `bef2cfbd` | 2026-11-02 |
| 22. Synthetic Composition and Diagnostic Gate Assessment | 4/4 | In Progress under D-141; synthetic tracer and immutable metadata/no-go contract complete; DIAG-01/02 and RIGHTS-01 remain Pending | - |
| 23. Qualified v0.4.0 Release | 0/TBD | Not started | - |

## Planning and Approval Boundary

- At most four phases and 40 plans; at most 12 plans in any phase. Active caps are 9/10/12/9 for Phases 20/21/22/23 (40 combined), including each phase's reserved gap slots. Phase 21's cap was reduced from 12 to 10 after completion: its eight plan files leave two reserve slots, preserving honest slack while keeping the combined cap at 40. Phase 20's gap slot is already consumed by 20-04; the five rescope additions are ordinary plans. These are scope caps, not acceptance evidence; Phase 21–23 feature goals are unchanged.
- Every deliverable has an automated check and a meaningful negative control. New reusable checkers live in tests/scripts/, use immutable commit facts where appropriate, and enter CTest when created. Automated UAT closure uses the existing shared closure tool; voluntary play is not a release gate.
- Preserve the deterministic performance budget and existing state-continuation behavior. Prefer the existing API and local helpers; new dependencies require demonstrated value.
- Both automatic-advance flags remain false. The owner approved the original Phase 20 roadmap on 2026-10-31; the single permitted security gap round became Plan 20-04. On 2026-11-01 the owner authorized an explicit Phase 20 rescope: trusted final macOS/Windows downloaded-byte checks, independent product-policy identity, exact repository-admission workflow matching, and attributable notice/export/dense-input/mutation-subject/timeout/planning-cap contract repairs. No fixture admission, legal/rights disposition change, accepted v0.3 debt repair, or sandbox-only Git-worktree code repair is authorized by this rescope.

Phase 20 completed on implementation head `39eb048e7770652b84a3fc5da7aaa3890adbd70c`; no fixture was admitted and RIGHTS-01 remains pending. Phase 21's eight plans and five roadmap criteria are verified. Implementation source `e0845db5` passed configure/build, focused checks, and independent review/security. PR #140 final head `507019f9` passed exact-head native/platform/sanitizer/CMake-floor CI, fixture reproduction, installed consumers, and player-package smoke, then squash-merged as `bef2cfbd`. The first hosted macOS CTest attempt timed out the Phase 21 fixture-admission controls at 60.08 seconds; the same-head full-suite rerun passed all 1,724 tests. The full local CTest run passed 1,717/1,718 before one unchanged 90-second timeout; that exact test passed its 77.17-second isolated retry, so all local tests have passing evidence across those runs but no single full invocation was all-green. The verifier's owner-approved override keeps FIXT-01 Pending without claiming a license grant or candidate ROM. Phase 22 — Synthetic Composition and Diagnostic Gate Assessment — has four live plans in four sequential waves under owner-approved D-141; the synthetic tracer is complete and the metadata-only assessment awaits its revised summary. Seven real-fixture gates remain unresolved, DIAG-01/02 and RIGHTS-01 remain Pending, and no real fixture/result is claimed. The current within-phase command is **/gsd-execute-phase 22**. Both automatic-advance flags remain false.
