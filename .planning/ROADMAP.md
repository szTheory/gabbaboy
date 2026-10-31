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
**Plans**: 3 plans — capped at 3; this is a tune-up, not a general debt-closure phase.

Plans:
**Wave 1**
- [ ] 20-01-PLAN.md — Versioned admission records, independent identity pins and shared exact product policy.

**Wave 2** *(blocked on Wave 1 completion)*
- [ ] 20-02-PLAN.md — Actual core install, archive and release notice boundary with mutation controls.
- [ ] 20-03-PLAN.md — Actual macOS player package and notice boundary with mutation controls.

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
**Plans**: TBD — at most 12; the primary and fallback candidate attempts each occupy at most one plan.

Captured frame and PCM digests establish reproducibility. They do not independently establish rendering accuracy, perceptual quality, physical CGB-E behavior, or general compatibility. A newly reproduced correctness/security issue must be fixed within scope or trigger a rescope; the candidate absence exit cannot silently defer it. Optional direct Steam Deck/SSH exploration is neither a completion gate nor a qualified Linux/Deck path.

### Phase 22: Composition and Microtest Evidence

**Goal**: Maintainers can use admitted rendering references and microtests with exact identities, explicit applicability, and expectations independent of GabbaBoy's current output.
**Depends on**: Phase 21
**Requirements**: DIAG-01, DIAG-02
**Success Criteria** (what must be TRUE):
  1. The dmg-acid2 and cgb-acid2 derivatives carry reproducible source/build and rights records, original replacement glyphs, and an explicit text mask; their expected comparisons are derived independently of GabbaBoy output and are labeled as controlled composition evidence.
  2. The admitted gbmicrotest cohort records exact source/ROM identities, redistribution terms, model applicability, and named eligible/executed/excluded cases; missing required cases or unexplained exclusions cannot yield a successful suite result.
  3. Automated negative controls detect altered fixture/reference/mask identities and incorrect case applicability or accounting; neither diagnostic results nor cross-model comparisons are reported as mode-3 timing, game-level, or physical CGB-E qualification.
**Plans**: TBD — at most 12.

Fixture admission uses Phase 20's contract. An unresolved acid2 or gbmicrotest rights/model/oracle gate requires scope resolution; it is not satisfied by capturing a new golden from GabbaBoy or by borrowing another silicon model's expected image.

### Phase 23: Qualified v0.4.0 Release

**Goal**: Users receive a qualified v0.4.0 release whose packages and support records accurately describe the established CGB game and diagnostic evidence.
**Depends on**: Phase 22
**Requirements**: REL-01
**Success Criteria** (what must be TRUE):
  1. Final implementation-head qualification and the existing trusted release rehearsal pass for the reviewed revision with required hosted coverage, consumer evidence, and regression controls; earlier phase evidence remains historical and is not repeatedly refreshed.
  2. Release notes and the support ledger identify an admitted game's exact software-model progress result or the justified absence after the two named attempts, distinguish diagnostic and reproducibility observations, and retain hardware, perceptual, timing, platform, and compatibility limits.
  3. Published/downloaded artifact identities and digests reconcile with the release source, installed consumers work against those bytes, required license/component notices are present, and the fixture-exclusion checks accept the real packages and reject their game-ROM insertion control.
**Plans**: TBD — at most 12.

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

- At most four phases and about 40 plans; at most 12 plans in any phase. Phase 20 is capped at three plans. These are scope caps, not acceptance evidence.
- Every deliverable has an automated check and a meaningful negative control. New reusable checkers live in tests/scripts/, use immutable commit facts where appropriate, and enter CTest when created. Automated UAT closure uses the existing shared closure tool; voluntary play is not a release gate.
- Preserve the deterministic performance budget and existing state-continuation behavior. Prefer the existing API and local helpers; new dependencies require demonstrated value.
- Both automatic-advance flags remain false. The owner approved this roadmap on 2026-10-31; Phase 20 planning is complete and no phase execution has started.

Phase 20 planning and independent plan verification are complete. The next workflow stage is **Phase 20 execution — Fixture Admission Tune-up**. Exact next command: **/gsd-execute-phase 20**, only when the owner chooses to begin execution. Stop at this phase boundary; do not start Phase 20 or advance to Phase 21 automatically.
