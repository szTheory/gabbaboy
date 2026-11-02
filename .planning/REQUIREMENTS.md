# Requirements: GabbaBoy

**Defined:** 2026-10-31  
**Milestone:** v0.4 Evidence Floor  
**Core Value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.

## v1 Requirements

### CGB Game Acceptance

- [x] **GAME-01**: The shared game-acceptance runner supports CGB RGB555 frame observations and guest-progress predicates on the CGB-CPU-E software profile while preserving the existing DMG acceptance path.
- [x] **GAME-02**: A CGB game result binds the exact ROM digest, profile and mode, scripted inputs, progress predicate, and observation data; a positive progress case and no-input/wrong-input or deliberately broken-predicate controls distinguish real guest progress from a vacuous pass.

### Fixture Admission and Rights

- [ ] **FIXT-01**: Game-fixture search is bounded to Potion Panic (GB Compo 2025 demo) first and µCity 1.3 as the sole fallback; each attempt verifies the exact source/build, ROM digest, cartridge header, and CGB mode, and failure of both candidates produces a reasoned absence without a third search.
- [ ] **RIGHTS-01**: An admitted game or diagnostic fixture has verified redistribution permission for repository and public-CI use, with per-component code, art, audio-driver, build-input, and notice terms recorded; game ROMs are excluded from installed and product-release packages, and GabbaBoy's root MIT license remains unchanged.

### Diagnostic Evidence

- [ ] **DIAG-01**: The admitted dmg-acid2 and cgb-acid2 derivatives replace glyph tiles and mask the text region, with source/build provenance and rights recorded; their evidence is labeled as controlled composition, not mode-3 timing.
- [ ] **DIAG-02**: Each admitted gbmicrotest case is tied to exact source and bytes, redistribution terms, and declared model applicability; suite results retain explicit eligible, executed, and excluded cases.

### Scene Feedback

- [ ] **FEED-01**: A concise title/scene/symptom report is enough to start agent-owned reproduction and classification; any resulting automated scene regression has an independent expected behavior and a negative control, while personal ROMs, saves, states, and captures remain outside the repository.

### Release Evidence

- [ ] **REL-01**: The qualified v0.4 release and support documentation state whether a CGB game was admitted or why it was not, identify evidence by model and source, and preserve limits on hardware, perceptual, timing, and general-compatibility claims.

## v2 Requirements

Deferred to a later owner-approved milestone.

### Integration and Timing

- **ADPT-01**: A libretro adapter confines framework globals to the adapter, maps the core's model/input/video/audio/persistence/state contracts, and is qualified through a real RetroArch Steam Deck path after a later milestone explicitly selects it.
- **PPU-01**: DMG PPU FIFO/fetcher and mode-3 timing are qualified against the admitted rendering references and model-applicable tests, subject to the existing deterministic performance budget.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full libretro adapter or a supported Steam Deck/Linux player path | The owner has an SSH workflow for exploratory feedback, but GabbaBoy's Linux SDL player path is not qualified. Scheduling the adapter requires a separate tradeoff against evidence work. |
| More than the named primary and fallback game candidates | The search is intentionally bounded; after both admission attempts, a justified absence is an acceptable outcome. |
| CGB mode-3 timing rewrite or CGB-D/other-silicon qualification | v0.4 establishes CGB game and diagnostic evidence first; later timing work needs admitted oracles. |
| Physical hardware, perceptual video/audio, or general game-compatibility claims | Current evidence is software-model and fixture scoped. |
| Changing the root MIT license or relabeling fixture/component terms | The audited fallback retains MIT for GabbaBoy; each external component keeps its own verified terms. |
| A libfuturo dependency, release synchronization, or early GabbaBoy API/state-format freeze | libfuturo is coordination context only; changes require a concrete consumer gap and a separate decision. |
| Personal ROMs, saves, states, or play captures in repository or public CI | Owner-owned observations may guide private reproduction, but do not grant redistribution rights. |
| Optional v0.3 release-tooling candidates by default | RM-032 remains proposed; include a change only if v0.4's release evidence shows it is required. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GAME-01 | Phase 21 | Complete |
| GAME-02 | Phase 21 | Complete |
| FIXT-01 | Phase 21 | Pending |
| RIGHTS-01 | Phase 20 | Pending |
| DIAG-01 | Phase 22 | Pending |
| DIAG-02 | Phase 22 | Pending |
| FEED-01 | Phase 21 | Pending |
| REL-01 | Phase 23 | Pending |

**Coverage:**
- v1 requirements: 8 total
- Mapped to phases: 8
- Unmapped: 0

---
*Requirements defined: 2026-10-31*  
*Last updated: 2026-10-31 after v0.4 roadmap approval*
