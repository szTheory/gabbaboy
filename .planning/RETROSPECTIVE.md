# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v0.1 — Limited DMG Preview

**Shipped:** 2026-10-10 (release `v0.1.0` published 2026-10-09)
**Phases:** 7 (1–6 plus inserted 06.1) | **Plans:** 64 | **Tasks:** 104 | **Commits:** 389 over 9 days

### What Was Built
- An installable, relocatable `GabbaBoy::core` package with bounded opaque instances, typed ROM rejection, and relocated C/C++ consumers.
- A timed SM83 CPU, interrupts, timer and serial on a deterministic event timeline, qualified against a pinned, rights-cleared Mooneye CPU/timer subset.
- A timed PPU, OAM DMA and JOYP, plus an optional SDL3 player that runs a byte-reproducible original interactive demo.
- MBC1 banking and fresh-process battery continuation that preserves a good save.
- A scoped four-channel APU with bounded 48 kHz PCM and clean host device and focus transitions.
- An exact-tag release with a support ledger, performance receipt, fuzzing, and a downloaded-byte reconciled inventory.

### What Worked
- Original project-authored ROMs and fixtures kept every claim legally redistributable and reproducible.
- Exact-head required CI checks, plus fail-closed test inventories, caught stale and skipped lanes that a local pass would have hidden.
- Owner steering D-025 (confidence-qualified software models) unblocked VIDEO-02/03 without overclaiming CPU-B silicon behavior.
- Closing the first `tech_debt` audit with an inserted phase (06.1) produced a clean `passed` re-audit and a `verified_closeout`.

### What Was Inefficient
- Phase 2 grew to 17 plans. Fixture qualification ran into CRLF checkout conversion on Windows and cross-host WLA-DX section-ordering differences before three candidates were admitted.
- Verification freshness fingerprints went stale whenever shared files changed. Phases 1, 2, 3, 5 and 6 needed refresh passes before the audit could accept them (GB-GSD-008).
- Summary metadata (`requirements-completed`) drifted from verification and needed a quick-task reconciliation.
- ROADMAP.md lacked a versioned milestone heading, so `milestone.complete` initially could not find the phases (GB-GSD-013).

### Patterns Established
- Every claim is scoped to a named model, boot profile and corpus, and limits are stated as limits rather than passes.
- Code PRs and docs-only verification-refresh PRs are separate, and each merges only at an exact green head.
- Each audit `tech_debt` line gets a disposition row (fixed or re-deferred, with a reason and a trigger).
- Each phase stops for the owner, with the next command persisted in STATE.md and the continuation note.

### Key Lessons
1. Give the roadmap a `## vX.Y <Name>` heading and keep summary metadata in step with verification from the first phase. Milestone tooling depends on both.
2. When shared files change late in a milestone, budget a freshness refresh for every earlier phase they cover.
3. Qualify fixtures on every CI host early. Line endings and tool ordering differences surface only cross-host.
4. Prove game-level progress before broadening compatibility claims (GB-GAME-001).

### Cost Observations
- Model mix and session count were not recorded during v0.1. Record them from the start of the next milestone.
- Notable: the audit, debt phase and re-audit loop took about one day and turned `tech_debt` into a clean close.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v0.1 | 7 | 64 | Exact-head CI gate, freshness-checked verification, debt-closure phase before close |

### Cumulative Quality

| Milestone | Local CTest | Fuzz targets | New runtime deps in core |
|-----------|-------------|--------------|--------------------------|
| v0.1 | 184/184 (06.1 regression) | loader, battery, API (bounded) | 0 (SDL only in the optional player) |

### Top Lessons (Verified Across Milestones)

1. (Populated once a lesson is confirmed in a second milestone.)
