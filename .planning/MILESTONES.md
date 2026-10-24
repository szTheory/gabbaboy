# Milestones

## v0.2 Color & Cartridge Breadth (Shipped: 2026-10-24)

**Delivered:** One rights-clear DMG game (Libbet) proven end to end, both headless and in the packaged player, against a frozen DMG-CPU-B regression baseline. MBC5, MBC2 and MBC3 cartridges were added, with a deterministic emulated-time RTC and a versioned battery block. One CGB silicon revision (CGB-CPU-E) runs in CGB and DMG-compatibility modes, with colour rendering, double speed and HDMA. All of it was published as the corpus- and model-qualified `v0.2.0` release.

**Phases completed:** 10 phases (7–15 plus inserted 15.1), 170 plans, 172 tasks
**Closeout type:** override_closeout. 28/28 requirements are satisfied and the audit is `tech_debt` with no blockers (integration 14/15, flows 6/6, all 10 phases Nyquist-compliant). The override is needed because the runtime reports the VERIFICATION.md files for Phases 7–15 as `stale`: later phases changed files those reports cover. Phase 15.1 is fresh. The owner chose to proceed on the re-audit at `5356d38`, which re-ran the cross-phase evidence (acceptance 74/74, focused cross-phase slice 290/290, DMG baseline pass, main push CI run 40114394844 green).
**Known verification overrides:** 1 newly acknowledged, 0 carried forward (see STATE.md Deferred Items). The open-artifact scanner reads Phase 14's `14-UAT-REVIEW.md`, a clean code review with 0 findings and 0 pending scenarios, as a UAT gap.

**Stats:**
- Timeline: 2026-10-10 → 2026-10-24 (15 days), 137 commits
- Git range: `2cfa221` (v0.1 archive) → `07204ac` (v0.2 re-audit)
- Change: 1,075 files, +406,951 / −1,111 lines (most of it pinned fixtures, receipts and planning evidence)
- Code: 14,644 lines of C in `src/` + `include/` (7,029 at v0.1); 54,384 lines of tracked C/C++ in total

**Key accomplishments:**
- **DMG game acceptance and frozen baseline.** Libbet v0.08 is admitted behind a fail-closed rights manifest and replayed by a shared gbinput stepper, both headless and through the packaged SDL3 player, to a guest-memory predicate with identical PCM digests. A 313-name DMG-CPU-B ledger was frozen and is gated by the live `dmg_baseline` CTest from Phase 8 onward.
- **Cartridge breadth.** A type-table mapper seam (MBC1 with no observable change) carries MBC5, MBC2 and MBC3. The MBC3 RTC runs on emulated time with explicit host catch-up and a versioned GBRT battery block. Evidence: Mooneye mbc2/mbc5 15/15 and rtc3test v004 transcripts that match the author's values.
- **CGB-CPU-E profile.** Model-gated banking, register visibility, RGB555 attribute and palette rendering, a DMG-compatibility palette and `--model` in the player. All 126 core functions carry MODEL tags and 66 GATE ids, mirrored in `docs/model-gates.md`.
- **Double speed and HDMA.** KEY1/STOP speed switching with a measured stall window (AGE 13/13) and general-purpose and HBlank HDMA (SameSuite 4/4). Split-run machine-state digests match uninterrupted runs.
- **Qualified v0.2.0 release.** A receipt-bound ledger covers 107 CGB cases (25 guest passes, 82 matched expected failures) and states explicitly that no CGB game-level evidence exists. The release also carries relocated C/C++ consumers, a disclosed 23.96% median DMG slowdown and a hosted 60-second libFuzzer campaign.
- **Release hardening (15.1).** Closeout scan and disposition ledgers. Point-in-time boundary verifiers (strict-head replay at boundary commits). An automated UAT closure that needs zero human checkpoints. Nyquist validation 82/82.

**Accepted tech debt (21 items, non-blocking):** see the `tech_debt` list in [v0.2-MILESTONE-AUDIT.md](milestones/v0.2-MILESTONE-AUDIT.md). Highlights:
- Twelve open LIM rows need an owner decision, and none was accepted (LIM-HIST-AUDIO-RED, LIM-HIST-M7 and LIM-SHIP11-UNCLASSIFIED were due at this audit). The hosted release rehearsal stays `not_verified`.
- Nothing in CTest or CI runs the Phase 8 contract verifiers.
- Some cell padding was stripped from the Phase 13 verification prose.
- Seven 15.1 validation rows read live state.
- Summaries 15.1-31..33 use the wrong frontmatter key.
- Review findings GR-IN-03 and GR2-IN-01 are deferred.
- Open PRs #75 and #78–92 (including release-please 0.2.1) are untriaged.

**Phase records not moved:** the phase directories for Phases 7–15.1 stay in `.planning/phases/`. `tests/CMakeLists.txt` and the closeout verifiers read files there (for example `GB-13-cgb-hdma/verify-hdma-closure.py` and the GB-15 UAT-closure phase), so moving them would break the test suite on main. Before these directories can be archived, the helpers they hold must move into `tests/`. Do that in the next milestone, or archive the directories with `/gsd-cleanup` once nothing references them.

**Archive:** [roadmap](milestones/v0.2-ROADMAP.md) · [requirements](milestones/v0.2-REQUIREMENTS.md) · [audit](milestones/v0.2-MILESTONE-AUDIT.md) · [integration audit](milestones/v0.2-INTEGRATION-AUDIT.md) · [phases](phases/) · [quick tasks](milestones/v0.2-quick/)

---

## v0.1 Limited DMG Preview (Shipped: 2026-10-10)

**Delivered:** An installable, bounded C17 DMG core and optional SDL3 macOS player that run declared ROM-only/MBC1 software with timed video, input, scoped audio, and safe battery continuation, published as the qualified `v0.1.0` release.

**Phases completed:** 7 phases (1–6 plus inserted 06.1), 64 plans, 104 tasks
**Closeout type:** verified_closeout — all 7 phases `passed`, 35/35 requirements, audit `passed` (12/12 integration, 5/5 flows)
**Known verification overrides:** 0 newly acknowledged, 0 carried forward. The one open artifact (a Phase 5 `-Wunsequenced` deferred item) was confirmed fixed by `9436db0` and a clean warning-free rebuild, then marked `status: resolved`.

**Stats:**
- Timeline: 2026-10-02 → 2026-10-10 (9 days), 389 commits
- Git range: `fcfbd53` (initial) → `c21631a` (re-audit)
- Change: 393 files, +60,834 / −20 lines
- Code: 17,960 lines of C/C++ tracked (7,029 in `src/` + `include/`)

**Key accomplishments:**
- Relocatable `GabbaBoy::core` CMake package with opaque, bounded instances, typed ROM rejection, and relocated C/C++ consumers; required CI enforces an exact executed-test inventory and sanitizers.
- Timed SM83 CPU (base + CB sets), interrupts, HALT/STOP, divider/timer edges, and serial on a deterministic event timeline, qualified against a pinned, rights-cleared Mooneye CPU/timer subset.
- Timed PPU, OAM DMA, JOYP, and an optional SDL3 player running a byte-reproducible original interactive demo, with integer presentation and explicit model limits (D-025).
- MBC1 banking and fresh-process battery continuation that never corrupts a good save (bounded autosave, explicit final-save failure handling).
- Four-channel scoped DMG APU producing 48 kHz caller-owned PCM through a bounded SPSC ring, with clean host focus/device transitions.
- Exact-tag `v0.1.0` release: three core archives and a smoke-qualified macOS player, support ledger, performance receipt, fuzzing, and a downloaded-byte reconciled inventory.

**Accepted tech debt (info-level or declared scope limits):** see the audit's `tech_debt` list in [v0.1-MILESTONE-AUDIT.md](milestones/v0.1-MILESTONE-AUDIT.md). Highlights: wait-exact-head-ci.py info items (fail closed), physical CPU-B timing unmeasured, Windows archive-level package smoke re-deferred, Release-Please PR #41 (0.1.1) awaiting maintainer approval.

**Archive:** [roadmap](milestones/v0.1-ROADMAP.md) · [requirements](milestones/v0.1-REQUIREMENTS.md) · [phases](milestones/v0.1-phases/) · [quick tasks](milestones/v0.1-quick/)

---
