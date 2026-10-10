# Milestones

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
