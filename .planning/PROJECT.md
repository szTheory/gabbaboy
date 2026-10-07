# GabbaBoy

## What This Is

GabbaBoy is a portable C17 emulator core for Nintendo Game Boy (DMG) and Game Boy Color (CGB), with a planned optional desktop player and an integration path for Playstead and other frontends. Phase 1 delivers an installable headless core and runner, an opaque bounded C API, and a project-authored ROM tracer for a narrow bootless DMG-CPU-B profile. General gameplay, hardware-qualified memory behavior, CGB execution, and the desktop player remain future work.

## Core Value

Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.

## Requirements

### Validated

- ✓ Portable C17 core and headless runner with an installable `GabbaBoy::core` export — Phase 1.
- ✓ Bounded opaque-instance API and original-ROM tracer with explicit fixture provenance and limited DMG-CPU-B claims — Phase 1.
- ✓ Relocated C and C++ consumers, required CI inventory, and revision-qualified Linux/macOS preview packages — Phase 1.

### Active

- [ ] Deliver progressively useful DMG and CGB releases with clearly bounded hardware and cartridge support.
- [ ] Provide a dependency-light C API with explicit memory ownership, timing, video, audio, input, persistence, errors, and lifecycle contracts.
- [ ] Provide a thin macOS player early; keep the headless core usable independently.
- [ ] Establish reproducible hardware tests, integration fixtures, sanitizer/fuzz checks, and performance baselines.
- [ ] Make save and state handling safe, deterministic, bounded, and versioned.
- [ ] Ship tested artifacts through efficient PR and release automation, with installation and consumer smoke checks.
- [ ] Maintain source-linked design decisions, current documentation, a rolling roadmap, and transferable lessons.

### Out of Scope

- NES, Neo Geo, and GBA execution — distinct hardware belongs in distinct projects.
- Proprietary game or boot ROM distribution — public automation needs permissioned fixtures.
- A game library manager, accounts, online services, or mandatory telemetry — frontend concerns outside the core.
- Universal compatibility, unmeasured “fastest” claims, or instruction-test pass rates presented as game compatibility.
- JIT, plugin frameworks, a generic multi-console bus, and broad scripting before demonstrated need.
- SGB/SGB2, additional silicon revisions, uncommon cartridge peripherals, link accessories, rewind/runahead, and web/mobile ports in the first milestone — retain as revisable future scope.

## Context

- The founding brief is [BRIEF.md](context/BRIEF.md). Detailed evidence and tradeoffs live in [research/](research).
- Sibling emulators are developing concurrently. Recent fixes and experiments in GlueyNeo, Nesturbator, and Playstead are useful precedent, with evidence strength recorded separately from intentions.
- Playstead is an intended consumer, not a prerequisite for first gameplay. An optional SDL player allows direct macOS use and exercises the same public API as external consumers.
- Mature OSS delivery practices from lattice_stripe and ExifCleaner inform CI and release design when still relevant to this C library.
- SameBoy, mGBA, hardware research, and test authors are comparison and evidence sources. Oracle agreement alone does not establish hardware correctness.
- Prefer small vertical demonstrations over completing entire subsystems in isolation. Each demonstration must preserve a path to correct timing.

## Constraints

- **Scope:** Game Boy and Game Boy Color. DMG first as a vertical slice; CGB remains a named near-term milestone, with timing/API choices accommodating it from the start.
- **Implementation:** Portable C17 is the initial recommendation; CMake/Ninja/CTest; keep SDL and platform code outside the core.
- **Correctness:** Explicit device time, hardware model, deterministic inputs, RTC policy, and ordering at observable boundaries. Host clocks and filesystem I/O belong in adapters.
- **Security:** Treat ROMs, battery files, save states, and frontend arguments as untrusted. Bound lengths, work, allocation, and diagnostics.
- **Performance:** Measure emulated work and correctness together. Optimize profiled bottlenecks; no accuracy shortcuts hidden behind benchmarks.
- **Public distribution:** MIT recommended; audit each imported source/fixture and retain its notices. Do not publish personal paths, identities, credentials, private ROM collections, or unlicensed assets.
- **Workflow:** OpenGSD; recommendations can be adopted without repeated approval. Stop after each phase and before beginning the next milestone unless explicitly directed otherwise.
- **Verification:** Automate repeatable acceptance, including packaged artifacts and downstream consumers. A workflow pause does not require routine manual UAT.
- **Shipping:** PRs and required green checks before merging. Automate releases within the authorized phase. Local bootstrap may precede a remote; remote hosting setup is a Phase 1 deliverable.

## Key Decisions

| Decision | Rationale | Outcome |
|---|---|---|
| GB/DMG + GBC/CGB target | Explicit current request supersedes copied console names | Adopted scope |
| Original core in portable C17 | Embedding, educational readability, host coverage | Initial recommendation; recheck at Phase 1 |
| Thin optional SDL3 player | Early macOS gameplay while exercising public API | Initial recommendation |
| Native C API first, libretro later | Precise ownership and deterministic semantics without frontend coupling | Initial recommendation |
| Explicit profiles for hardware revisions | Avoid accidental DMG/CGB hybrid behavior | Adopted principle; choose exact baseline revisions in phase planning |
| MIT for original contributions | Simple permissive reuse | Initial recommendation; per-asset license review required |
| Automated work inside phases, explicit phase stops | High velocity and owner review/model choice coexist | Required |
| Inherit the session model | User can change model between phases without stale hardcoded model IDs | Adopted configuration |
| PR-based phase branches | Keep main releasable and retain review/verification evidence | Adopted configuration |
| Corpus-qualified claims and measurements | A passing subset is not universal hardware/game compatibility | Required |
| Bootless DMG-CPU-B tracer as the first delivered slice | A real guest path validates the portable API and install flow while keeping hardware, gameplay, and CGB claims bounded | Verified in Phase 1; memory-map conformance continues in Phase 2 |

## Evolution

At each phase boundary, update delivered requirements, evidence, limitations, decisions, docs, performance/correctness baseline changes, open issue/PR triage, and the next recommended action. Stop before the next phase.

At each milestone boundary, audit this document and the active requirements, summarize compatibility by tested model/corpus, refresh the near/mid/long-term roadmap, and prepare a concise lesson transfer for sibling emulator projects. Keep unverified external advice separate until reproduced locally.

---
Last updated: 2026-10-03 after Phase 1 verification and closeout.
