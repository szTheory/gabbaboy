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

## Milestone: v0.2 — Color & Cartridge Breadth

**Shipped:** 2026-10-24 (release `v0.2.0` published from tag source `ab301aa`)
**Phases:** 10 (7–15 plus inserted 15.1) | **Plans:** 170 | **Tasks:** 172 | **Commits:** 137 over 15 days

### What Was Built
- Libbet v0.08 game-level acceptance on DMG-CPU-B, both headless and in the packaged player, plus a frozen DMG baseline that gated every later phase.
- A type-table mapper seam with MBC5, MBC2 and MBC3, an emulated-time RTC, explicit host catch-up and a versioned battery block.
- The CGB-CPU-E profile: banking, register visibility, RGB555 colour and a compatibility palette, KEY1 double speed with a measured stall, and general/HBlank HDMA.
- A pinned CGB-E corpus of 107 cases (25 passes, 82 matched expected failures), with an explicit record that no CGB game-level evidence exists.
- The qualified `v0.2.0` release (corpus, fuzz, performance, consumer and source-archive receipts), then a 36-plan hardening phase that bound closeout evidence to immutable commits.

### What Worked
- Freezing the DMG baseline first. Every CGB and mapper phase proved DMG output unchanged with one live CTest, not by argument.
- Measurement-pinned dispositions (exact-signature expected failures) kept CGB claims honest without tuning constants to pass oracles.
- Rehearsing the exact-tag release producers on the version PR found three defects before tagging.
- Automated UAT closure (`verify-uat-closure.py`) with negative controls removed manual checkpoints from Phases 13–15.1.

### What Was Inefficient
- Phase 15.1 grew to 36 plans across two gap-closure rounds, plus a validation pass and two re-audits. Several of those rounds existed only to fix verifiers that read live HEAD state instead of boundary commits (GB-GSD-024, GB-VERIFY-002, GB-EVID-002).
- Hosted jobs near their timeouts were re-run repeatedly before anyone compared per-test durations; PR #98 needed seven CI attempts (GB-CI-010).
- Verification freshness went stale again. By close, the runtime reported Phase 7–15 reports stale, which forced an `override_closeout` even though the audit re-ran the cross-phase evidence (GB-GSD-008 again).
- Test-consumed helpers lived in phase directories, so the default phase archive would have broken main (GB-GSD-026).

### Patterns Established
- Boundary checks read point-in-time facts from the boundary commit (strict-head replay per boundary), never from the live HEAD.
- Disposition ledgers: every audit debt is `closed`, `closed_with_residual` or `limitation_open` with an owner action. Nothing is silently accepted.
- Each support claim names the model and corpus revision, and is kept separate from each execution receipt (GB-RELEASE-003).
- Merges happen only at exact-head green required checks, and the merge receipt is recorded at the next boundary.

### Key Lessons
1. Write verifiers against an immutable commit from the start. Retrofitting point-in-time reads cost a whole gap-closure round.
2. Keep reusable checkers in `tests/scripts/`, not phase directories, so milestone archival stays a pure move.
3. When a hosted job fails on timeout twice, compare durations before re-running.
4. Plan a freshness strategy for long milestones: either re-verify at close or accept a documented override bound to a fresh audit.

### Cost Observations
- Model mix: not recorded. The integration checker resolved to Haiku. Orchestration and execution ran on Opus.
- Sessions: not recorded.
- Notable: releasing at Phase 15 and then hardening in 15.1 took about four days, about as long as the four CGB feature phases (11–14) together.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v0.1 | 7 | 64 | Exact-head CI gate, freshness-checked verification, debt-closure phase before close |
| v0.2 | 10 | 170 | Frozen DMG baseline gate, exact-tag release rehearsal, boundary-commit verifiers, zero-checkpoint automated UAT |

### Cumulative Quality

| Milestone | Local CTest | Fuzz targets | New runtime deps in core |
|-----------|-------------|--------------|--------------------------|
| v0.1 | 184/184 (06.1 regression) | loader, battery, API (bounded) | 0 (SDL only in the optional player) |
| v0.2 | 1183/1183 (15.1 verify) | v0.1 set plus hosted 60 s libFuzzer ASan/UBSan campaign | 0 |

### Top Lessons (Verified Across Milestones)

1. Verification freshness goes stale whenever late phases touch shared files, so budget a refresh or a documented override at close (GB-GSD-008; v0.1 and v0.2).
2. Close a `tech_debt` audit with an inserted debt phase before archiving (06.1 and 15.1). Owner-only decisions stay explicit rather than accepted.
3. A local pass, a stale run or a branch commit is not hosted proof. Bind evidence to the exact head or merge commit (v0.1 exact-head gate; v0.2 GB-EVID-002).
