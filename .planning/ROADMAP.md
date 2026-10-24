# Roadmap: GabbaBoy

## Overview

GabbaBoy is an original portable C17 core for Game Boy and Game Boy Color. v0.1 delivered a limited, evidence-bounded DMG preview with an installable core, timed CPU/bus diagnostics, an interactive optional SDL3 player, MBC1 battery continuation, scoped audio and a qualified v0.1.0 release. v0.2 Color & Cartridge Breadth proved one rights-clear game end to end on DMG-CPU-B and froze a DMG regression baseline. It then added MBC5/MBC2/MBC3 cartridges with a deterministic RTC and one CGB silicon revision (CGB-CPU-E) in CGB and DMG-compatibility modes, and shipped the model- and corpus-qualified v0.2.0 release. Revisable later direction: [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md).

## Milestones

- ✅ **v0.1 Limited DMG Preview**: Phases 1–6 plus inserted 06.1 (shipped 2026-10-10; release `v0.1.0` published 2026-10-09)
- ✅ **v0.2 Color & Cartridge Breadth**: Phases 7–15 plus inserted 15.1 (shipped 2026-10-24; release `v0.2.0`; audit `tech_debt`, no blockers)
- 📋 **v0.3 States & Integration** (provisional): save states (STATE-01) and a qualified Playstead adapter (INT-01). Define it with `/gsd-new-milestone`.

## Phases

**Phase Numbering:**
- Integer phases continue across milestones (directory prefix `GB-`); the next milestone starts at Phase 16
- Decimal phases (for example 15.1) are urgent insertions (marked INSERTED)

<details>
<summary>✅ v0.1 Limited DMG Preview (Phases 1–6, 06.1): SHIPPED 2026-10-10</summary>

- [x] Phase 1: Portable Foundation and Original ROM Tracer (5/5 plans), completed 2026-10-03
- [x] Phase 2: DMG CPU, Bus, and Time (17/17 plans), completed 2026-10-07
- [x] Phase 3: Visible Interactive DMG (13/13 plans), completed 2026-10-09
- [x] Phase 4: MBC1 and Safe Battery Continuation (7/7 plans), completed 2026-10-08
- [x] Phase 5: DMG Audio and Stable Playback (7/7 plans), completed 2026-10-09
- [x] Phase 6: Qualified DMG Release and Consumer Handoff (7/7 plans), completed 2026-10-09
- [x] Phase 06.1: Address v0.1 tech debt (INSERTED) (8/8 plans), completed 2026-10-10

Full detail: [v0.1 roadmap archive](milestones/v0.1-ROADMAP.md), [requirements](milestones/v0.1-REQUIREMENTS.md), [audit](milestones/v0.1-MILESTONE-AUDIT.md), [phase records](milestones/v0.1-phases/).

</details>

<details>
<summary>✅ v0.2 Color & Cartridge Breadth (Phases 7–15, 15.1): SHIPPED 2026-10-24</summary>

- [x] Phase 7: DMG Game Acceptance and Regression Baseline (17/17 plans), completed 2026-10-11
- [x] Phase 8: Cartridge Seam, MBC5 and MBC2 (10/10 plans), completed 2026-10-11
- [x] Phase 9: MBC3, Deterministic RTC and Cartridge Persistence (18/18 plans), completed 2026-10-11
- [x] Phase 10: CGB Profile, Banking and Register Visibility (20/20 plans), completed 2026-10-12
- [x] Phase 11: CGB Colour Rendering and Player Colour (15/15 plans), completed 2026-10-13
- [x] Phase 12: CGB Double Speed (19/19 plans), completed 2026-10-14
- [x] Phase 13: CGB HDMA (12/12 plans), completed 2026-10-14
- [x] Phase 14: CGB-E Model Qualification and Corpus (13/13 plans), completed 2026-10-15
- [x] Phase 15: CGB Acceptance, Support Ledger and v0.2.0 Release (10/10 plans), completed 2026-10-20
- [x] Phase 15.1: Release Hardening and Milestone Debt Closure (INSERTED) (36/36 plans), completed 2026-10-24

Full detail: [v0.2 roadmap archive](milestones/v0.2-ROADMAP.md), [requirements](milestones/v0.2-REQUIREMENTS.md), [audit](milestones/v0.2-MILESTONE-AUDIT.md), [integration audit](milestones/v0.2-INTEGRATION-AUDIT.md), [quick tasks](milestones/v0.2-quick/). The phase records stay in [phases/](phases/), because CTest and the closeout verifiers read files there (see MILESTONES.md).

</details>

## Progress

| Milestone | Phases | Plans | Status | Shipped |
|-----------|--------|-------|--------|---------|
| v0.1 Limited DMG Preview | 7 | 64/64 | Complete | 2026-10-10 |
| v0.2 Color & Cartridge Breadth | 10 | 170/170 | Complete | 2026-10-24 |
| v0.3 States & Integration | — | — | Not started (provisional) | — |
