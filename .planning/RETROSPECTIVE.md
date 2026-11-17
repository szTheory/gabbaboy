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

## Milestone: v0.3 — Save States & Host Contract

**Shipped:** 2026-10-31 | **Phases:** 4 | **Plans:** 35 | **Recorded actual tasks:** 105

### What Was Built
Native transactional states and exact continuation; player slots/undo; the POSIX raw-save/SIGTERM host runner; cumulative performance and CI/planning gates; v0.2.1 debt closure and qualified v0.3.0 publication.

### What Worked
The four-phase/plan caps kept scope bounded. Corpus forks and field omissions tested continuation through public APIs. Real filesystem/signal providers and shipped-archive consumers exercised integration failures. Automated UAT closed all four phases without human checkpoints, and failed release attempts stayed separate from recovery receipts.

### What Was Inefficient
Repeated release-policy and Windows path/EOL repairs required explicit bounded rescopes. The installed runtime still marks earlier boundary reports stale after shared-file changes, requiring an owner override despite final-head proof. Two CTest inputs still depended on live phase storage and needed retargeting during archival. The standalone scanner helper retains two failing cases outside CTest.

### Patterns Established
One shared non-failing state conversion after validation; atomic readiness-marker publication; Git paths kept separate from host filesystem paths; boundary evidence preserved across later changes; archive manifests prove SUMMARY/VERIFICATION bytes unchanged.

### Key Lessons
1. Exercise actual release entrypoints and captured API shapes before a version window, with exact immutable source binding.
2. Keep reusable check inputs independent of live phase storage and test archival before deleting originals.
3. Distinguish accepted nonblocking debt from repaired defects; never rewrite old fingerprints to manufacture readiness.
4. Reconfigure when generated tests embed source revisions, then verify once at the final implementation head.

### Cost Observations
Model mix and session counts were not recorded. The audit measured sanitizer CTest at 2,071 seconds, native Linux CTest at 868 seconds and CMake-floor install/relocation at 1,388 seconds. A separate 20-second support-ledger self-test duplicates CTest; consolidate only after proving equivalent environment, assertions and required-lane coverage. No scheduling change is justified by archival alone.

---

## Milestone: v0.4 — Evidence Floor

**Administrative closeout:** 2026-11-17 with owner-accepted gaps. **Product release:** `v0.4.0` was already published on 2026-11-14 and was not changed. **Phases:** 6 | **Plans:** 33 (32 plan summaries retained; Phase 24 Task 7 is unfinished).

### What Was Built

CGB frame/progress and scene-feedback contracts, qualified v0.4.0 release evidence, exact-source rights records, two controlled Acid2 derivatives, and one admitted/executed gbmicrotest case. The original requirement tracker now has seven completed criteria and one Pending game-fixture criterion.

### What Worked

The candidate order and rights exclusions stayed explicit. Independent review separated literal diagnostic acceptance from the Acid2 runtime comparison, so the failure remained visible without being misclassified as a core defect. The small diagnostic lane accounted for one eligible/executed case and 512 exclusions. The sibling scan found a useful renderer pattern: establish independent output oracles before implementing a scoped display path.

### What Was Inefficient

An unrelated end-to-end game-fixture requirement kept the whole evidence milestone open after the diagnostic criteria had enough evidence to close independently. Stale verification reports and a missing Phase 24 final task kept triggering workflow routes that could not make progress on FIXT-01. The cross-model Acid2 failure has no retained image map and must not be replayed under this closeout.

### Patterns Established

Close each requirement against its own literal criteria and linked evidence. Keep runtime failures distinct from specification gaps. Close a milestone with an explicit override when the owner chooses to defer an independent requirement; never rewrite the deferred requirement as satisfied. For PPU work, admit a small exact DMG oracle set first, write independent tests before changing rendering code, and check cheap identity/accounting controls before the long suite.

### Key Lessons

1. Do not make a milestone's final task all-or-nothing when the requirements are independently verifiable; record each disposition separately.
2. Freeze the closeout policy and acceptable stop conditions before starting the milestone's last phase.
3. When an oracle output is lost, preserve the original result and stop; do not replay a costly run just to obtain a more convenient artifact.
4. Move to a new, evidence-supported emulator slice when a bounded fixture gate remains blocked; do not keep reopening the same plan without a new source of evidence.

### Cost Observations

No new full CTest suite, release workflow, or Acid2 replay ran for this closeout. The model mix was not recorded. The exact-final-head D-103 suite remains deferred with FIXT-01; this is disclosed, not counted as a pass.

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v0.1 | 7 | 64 | Exact-head CI gate, freshness-checked verification, debt-closure phase before close |
| v0.2 | 10 | 170 | Frozen DMG baseline gate, exact-tag release rehearsal, boundary-commit verifiers, zero-checkpoint automated UAT |
| v0.3 | 4 | 35 | Bounded phases, state-fork/omission evidence, final-head audit, explicit override closeout |
| v0.4 | 6 | 33 | Separate requirement dispositions; owner-directed early close with FIXT-01 and stale-verification gaps disclosed |

### Cumulative Quality

| Milestone | Local CTest | Fuzz targets | New runtime deps in core |
|-----------|-------------|--------------|--------------------------|
| v0.1 | 184/184 (06.1 regression) | loader, battery, API (bounded) | 0 (SDL only in the optional player) |
| v0.2 | 1183/1183 (15.1 verify) | v0.1 set plus hosted 60 s libFuzzer ASan/UBSan campaign | 0 |
| v0.3 | 1707/1707 (implementation-head audit; zero skips) | Hosted state-load semantics added to existing campaigns | 0 |
| v0.4 | No exact-final-head suite at close; earlier phase checks remain in their linked records | No new fuzz target added at close | 0 |

### Top Lessons (Verified Across Milestones)

1. Verification freshness goes stale whenever late phases touch shared files, so budget a refresh or a documented override at close (GB-GSD-008; v0.1 and v0.2).
2. Close a `tech_debt` audit with an inserted debt phase before archiving (06.1 and 15.1). Owner-only decisions stay explicit rather than accepted.
3. A local pass, a stale run or a branch commit is not hosted proof. Bind evidence to the exact head or merge commit (v0.1 exact-head gate; v0.2 GB-EVID-002).
4. Requirements with independent acceptance evidence can be closed separately while an unrelated fixture requirement remains Pending; state the override and keep the deferred row open (GB-GSD-003; v0.4).
