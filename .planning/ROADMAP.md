# Roadmap: GabbaBoy

## Milestones

- ✅ **v0.1 Limited DMG Preview** — Phases 1–6 and 06.1, shipped 2026-10-10; [archive](milestones/v0.1-ROADMAP.md).
- ✅ **v0.2 Color & Cartridge Breadth** — Phases 7–15 and 15.1, shipped 2026-10-24; [archive](milestones/v0.2-ROADMAP.md).
- ✅ **v0.3 Save States & Host Contract** — Phases 16–19, 35 plans, shipped 2026-10-31; [archive](milestones/v0.3-ROADMAP.md).
- 🚧 **v0.4 Evidence Floor** — Phases 20–23, roadmap owner-approved; Phase 20 is planned but execution has not started.

## v0.4 — Evidence Floor

**Goal:** Establish a reproducible floor for CGB game progress and rendering evidence before deeper timing work, or document a specific reason neither named game candidate could be admitted.

The two substantive tracks are CGB game acceptance with scene regressions, and diagnostic admission. A capped tune-up establishes the fixture boundary first; a qualified release closes the milestone. The approved scope is in [REQUIREMENTS.md](REQUIREMENTS.md), with decisions and future candidates in [DECISIONS.md](context/DECISIONS.md) and [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md).

## Phases

Numbering continues after completed Phase 19. Decimal phases are reserved for explicitly approved insertions.

- [ ] **Phase 20: Fixture Admission Tune-up** — New evidence enters through a checked rights and distribution boundary.
- [ ] **Phase 21: CGB Game Progress and Scene Regressions** — The shared runner proves CGB progress and records the bounded game-candidate outcome.
- [ ] **Phase 22: Composition and Microtest Evidence** — Admitted acid2 derivatives and gbmicrotest expose their exact model and oracle limits.
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
**Plans**: 9 total: three original plans, the consumed single security gap round (20-04), and five owner-authorized ordinary rescope plans (20-05–20-09). Final-review security follow-ups remain inside existing plans: 20-06 owns trusted publisher metadata/cleanup/Windows containment; the final audit reopens 20-02 for source/Linux-core TAR metadata bounds and 20-05 for forbidden-digest rejection before allowed generated paths. No plan or gap round is added.

Plans:
**Wave 1**
- [ ] 20-01-PLAN.md — Versioned admission records, independent identity pins and shared exact product policy.

**Wave 2** *(blocked on Wave 1 completion)*
- [ ] 20-02-PLAN.md — Actual core install/archive/release boundary; reopened at Task 4 for bounded source/Linux-core PAX/GNU metadata and decompressed-stream parsing.
- [ ] 20-03-PLAN.md — Actual macOS player package and notice boundary with mutation controls.

**Wave 3** *(single in-scope security gap closure)*
- [ ] 20-04-PLAN.md — Bound fixture filesystem traversal and Git tree enumeration.

**Wave 4** *(authorized rescope; original plans remain intact)*
- [ ] 20-05-PLAN.md — Independently pin product policy and exports/budgets; reopened at Task 3 to reject forbidden digests at every regular path, including generated/one_of core/player entries.
- [ ] 20-07-PLAN.md — Match repository-admission commands exactly and repair complete isolated workflow mutation subjects.
- [ ] 20-08-PLAN.md — Align shared notice-contract consumers and their negative controls with the reviewed source/product distinction.

**Wave 5** *(after the indicated Wave 4 dependencies)*
- [ ] 20-06-PLAN.md — Validate downloaded macOS and Windows product bytes with trusted checker/policy; metadata/cleanup follow-up complete, reopened at Task 4 for drive/ADS rejection and directory/file containment before creation.
- [ ] 20-09-PLAN.md — Restore dense-input source-only mutant configure with separate immutable baseline evidence and unqualified-build controls.

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
**Plan cap**: 12
**Plans**: TBD — within the cap; the primary and fallback candidate attempts each occupy at most one plan.

Captured frame and PCM digests establish reproducibility. They do not independently establish rendering accuracy, perceptual quality, physical CGB-E behavior, or general compatibility. A newly reproduced correctness/security issue must be fixed within scope or trigger a rescope; the candidate absence exit cannot silently defer it. Optional direct Steam Deck/SSH exploration is neither a completion gate nor a qualified Linux/Deck path.

### Phase 22: Composition and Microtest Evidence

**Goal**: Maintainers can use admitted rendering references and microtests with exact identities, explicit applicability, and expectations independent of GabbaBoy's current output.
**Depends on**: Phase 21
**Requirements**: DIAG-01, DIAG-02
**Success Criteria** (what must be TRUE):
  1. The dmg-acid2 and cgb-acid2 derivatives carry reproducible source/build and rights records, original replacement glyphs, and an explicit text mask; their expected comparisons are derived independently of GabbaBoy output and are labeled as controlled composition evidence.
  2. The admitted gbmicrotest cohort records exact source/ROM identities, redistribution terms, model applicability, and named eligible/executed/excluded cases; missing required cases or unexplained exclusions cannot yield a successful suite result.
  3. Automated negative controls detect altered fixture/reference/mask identities and incorrect case applicability or accounting; neither diagnostic results nor cross-model comparisons are reported as mode-3 timing, game-level, or physical CGB-E qualification.
**Plan cap**: 10
**Plans**: TBD — within the cap.

Fixture admission uses Phase 20's contract. An unresolved acid2 or gbmicrotest rights/model/oracle gate requires scope resolution; it is not satisfied by capturing a new golden from GabbaBoy or by borrowing another silicon model's expected image.

### Phase 23: Qualified v0.4.0 Release

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
| 20. Fixture Admission Tune-up | 0/3 | Planned | - |
| 21. CGB Game Progress and Scene Regressions | 0/TBD | Not started | - |
| 22. Composition and Microtest Evidence | 0/TBD | Not started | - |
| 23. Qualified v0.4.0 Release | 0/TBD | Not started | - |

## Planning and Approval Boundary

- At most four phases and 40 plans; at most 12 plans in any phase. Active caps are 9/12/10/9 for Phases 20/21/22/23 (40 combined), including each phase's reserved gap slot. Phase 20's gap slot is already consumed by 20-04; the five rescope additions are ordinary plans. These are scope caps, not acceptance evidence; Phase 21–23 feature goals are unchanged.
- Every deliverable has an automated check and a meaningful negative control. New reusable checkers live in tests/scripts/, use immutable commit facts where appropriate, and enter CTest when created. Automated UAT closure uses the existing shared closure tool; voluntary play is not a release gate.
- Preserve the deterministic performance budget and existing state-continuation behavior. Prefer the existing API and local helpers; new dependencies require demonstrated value.
- Both automatic-advance flags remain false. The owner approved the original Phase 20 roadmap on 2026-10-31; the single permitted security gap round became Plan 20-04. On 2026-11-01 the owner authorized an explicit Phase 20 rescope: trusted final macOS/Windows downloaded-byte checks, independent product-policy identity, exact repository-admission workflow matching, and attributable notice/export/dense-input/mutation-subject/timeout/planning-cap contract repairs. No fixture admission, legal/rights disposition change, accepted v0.3 debt repair, or sandbox-only Git-worktree code repair is authorized by this rescope.

Phase 20 remains incomplete. The owner-authorized rescope plans address the three final-review blockers and genuine Phase 20-caused full-suite failures; the five sandbox-only Git-worktree failures already passed targeted reruns and add no code scope. Retain the trusted publisher metadata/cleanup and Windows containment follow-ups in existing Plan 20-06 and their actual evidence. The final security audit adds two authorized in-place follow-ups: Plan 20-02 Task 4 bounds source/Linux-core tar decompression and pre-payload PAX/GNU header/aggregate/count parsing, while Plan 20-05 Task 3 rejects known forbidden fixture digests before any allowed/generated/one_of regular-file path handling in both layouts. Both summaries are reopened with their earlier task evidence preserved; neither stale security rows nor earlier passing coverage establishes these fixes. No fixture admission, rights/legal claim or policy change, live publication, dependency, unrelated cleanup, extra plan or cap change is included. Execute the remaining Phase 20 work with **/gsd-execute-phase 20**, resuming 20-02 at Task 4 and 20-05 at Task 3. Require final-head full-suite, trusted platform evidence, review/security and automated closure checks before declaring the phase complete. RIGHTS-01 remains pending; no fixture was admitted. Stop after Phase 20 and never advance to Phase 21 automatically.
