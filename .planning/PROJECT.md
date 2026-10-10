# GabbaBoy

## What This Is

GabbaBoy is a portable C17 emulator core for Nintendo Game Boy (DMG) and Game Boy Color (CGB), with an integration path for Playstead and other frontends. The shipped v0.1 preview runs a bootless DMG-CPU-B profile with declared ROM-only/MBC1 cartridges, timed video and input, scoped four-channel audio, and safe battery continuation, through the same bounded public API that external consumers use. An optional SDL3 macOS player ships with it. Broad game compatibility, physical hardware qualification, CGB execution, further mappers, RTC, and save states remain future work.

## Current State

- **Shipped:** v0.1 Limited DMG Preview (milestone closed 2026-10-10; release [`v0.1.0`](https://github.com/szTheory/gabbaboy/releases/tag/v0.1.0) published 2026-10-09). 7 phases, 64 plans, 35/35 requirements, audit `passed`.
- **Code:** ~18k lines of C/C++ (about 7k in `src/` + `include/`); CMake/Ninja/CTest; 184 local CTest cases at the 06.1 regression run; required CI on Linux, macOS and Windows (MinGW-w64).
- **Evidence scope:** admitted corpus is three source-qualified derived Mooneye CPU/timer closures plus original project ROMs. No physical hardware, perceptual output, signing/notarization, or live Playstead integration is claimed.
- **Open:** No open issues or PRs at the v0.2 start (2026-10-10); releases `v0.1.0` and `v0.1.2` published. Accepted info-level debt is listed in the [v0.1 audit](milestones/v0.1-MILESTONE-AUDIT.md).

## Current Milestone: v0.2 Color & Cartridge Breadth

**Goal:** Play supported CGB software and the common MBC2/MBC3/MBC5 cartridge set (with deterministic RTC) through the same bounded core and player, after first proving one rights-clear game end to end on the existing DMG player.

**Target features:**
- One rights-clear game-level acceptance in the existing DMG player (guest-observable start/progress, meaningful input, visible/audio response) before any broadened claim.
- MBC5, MBC3 with deterministic host-independent RTC (and its battery persistence), and MBC2 with built-in RAM.
- A CGB silicon profile: CGB mode and DMG-compatibility mode, double-speed switching, VRAM/WRAM banking, BG/OBJ color palettes and attributes, general/HBlank HDMA, and model-specific CPU/PPU/APU differences under explicit model qualification.
- Updated support ledger, docs, release notes, and a qualified v0.2 release scoped to the tested corpus.

Deferred to v0.3 (States & Integration): transactional versioned save states (STATE-01) and a qualified Playstead adapter (INT-01), so serialization is designed once over the complete DMG+CGB machine state.

## Core Value

Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.

## Requirements

### Validated

- ✓ Portable C17 core and headless runner with an installable `GabbaBoy::core` export — Phase 1.
- ✓ Bounded opaque-instance API and original-ROM tracer with explicit fixture provenance and limited DMG-CPU-B claims — Phase 1.
- ✓ Relocated C and C++ consumers, required CI inventory, and revision-qualified Linux/macOS preview packages — Phase 1.
- ✓ Interactive optional SDL3 macOS DMG preview, original ROM-only demo, timed input/frame output, and explicit audio/persistence limits — Phase 3.
- ✓ Timed SM83 CPU, interrupts, HALT/STOP, timer and serial on a deterministic event timeline, qualified against a pinned CPU/timer corpus (CPU-01..05) — v0.1.
- ✓ Timed PPU, OAM DMA, VRAM/OAM restrictions and JOYP under the D-025 confidence-qualified model (VIDEO-01..05) — v0.1.
- ✓ MBC1 banking, bounded battery import/export, atomic player saves, and fresh-process continuation (SAVE-01..04) — v0.1.
- ✓ Scoped four-channel DMG APU, bounded 48 kHz PCM, paced SDL playback, and clean host input/device transitions (AUDIO-01..03, HOST-01..02) — v0.1.
- ✓ Qualified exact-tag release, support ledger, performance baselines, fuzzing, adopter docs, and exercised CI/release automation (SHIP-01..08) — v0.1.

### Active

v0.2 Color & Cartridge Breadth (scoped in [REQUIREMENTS.md](REQUIREMENTS.md)):

- [ ] Rights-clear game-level acceptance in the DMG player before broadened claims.
- [ ] MBC2/MBC3/MBC5 cartridges and deterministic MBC3 RTC (CART-01, RTC-01).
- [ ] CGB silicon profile, color and DMG-compatibility modes, speed switching, banking, palettes, and HDMA with model-qualified tests (CGB-01..03).

Next (v0.3, provisional): transactional versioned native save states (STATE-01) and a qualified Playstead adapter (INT-01).

Ongoing project principles: dependency-light C API with explicit contracts; headless core independent of the player; reproducible tests, sanitizers, fuzzing, and baselines; tested artifacts through PR and release automation; source-linked decisions, current docs, and transferable lessons.

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
| Original core in portable C17 | Embedding, educational readability, host coverage | ✓ Good — v0.1 shipped on Linux/macOS/Windows consumers |
| Thin optional SDL3 player | Early macOS gameplay while exercising public API | ✓ Good — player stayed optional; core export has no SDL dependency |
| Native C API first, libretro later | Precise ownership and deterministic semantics without frontend coupling | ✓ Good for v0.1; libretro still pending demonstrated value |
| Explicit profiles for hardware revisions | Avoid accidental DMG/CGB hybrid behavior | Adopted principle; choose exact baseline revisions in phase planning |
| MIT for original contributions | Simple permissive reuse | ✓ Adopted; per-asset rights recorded for every fixture |
| Automated work inside phases, explicit phase stops | High velocity and owner review/model choice coexist | Required |
| Inherit the session model | User can change model between phases without stale hardcoded model IDs | Adopted configuration |
| PR-based phase branches | Keep main releasable and retain review/verification evidence | Adopted configuration |
| Corpus-qualified claims and measurements | A passing subset is not universal hardware/game compatibility | Required |
| Bootless DMG-CPU-B tracer as the first delivered slice | A real guest path validates the portable API and install flow while keeping hardware, gameplay, and CGB claims bounded | Verified in Phase 1; memory-map conformance continues in Phase 2 |
| Confidence-qualified software models for documented but revision-sensitive behavior | Select a deterministic model from primary documentation and reverse-engineering sources, cross-check implementations, and state the remaining silicon uncertainty | ✓ Good — D-025 unblocked VIDEO-02/03; ⚠️ Revisit if hardware measurements become available |
| Exact-head required CI gate before merge | Local passes and stale runs had masked remote state | ✓ Good — enforced through 06.1; info-level script items deferred |
| Insert a debt-closure phase before closing a milestone | The first audit returned `tech_debt`; closing it first gave a clean `passed` re-audit | ✓ Good — Phase 06.1 |

## Evolution

At each phase boundary, update delivered requirements, evidence, limitations, decisions, docs, performance/correctness baseline changes, open issue/PR triage, and the next recommended action. Stop before the next phase.

At each milestone boundary, audit this document and the active requirements, summarize compatibility by tested model/corpus, refresh the near/mid/long-term roadmap, and prepare a concise lesson transfer for sibling emulator projects. Keep unverified external advice separate until reproduced locally.

---
Last updated: 2026-10-10 at the start of milestone v0.2 Color & Cartridge Breadth.
