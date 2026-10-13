# Phase GB-12 Continuation

Completed workflow stage: **Phase GB-12 — CGB Double Speed, plan 12-12 execution** (2026-10-13). Phase 12 remains in progress; see [12-12-SUMMARY.md](12-12-SUMMARY.md). Earlier evidence remains in [12-09-SUMMARY.md](12-09-SUMMARY.md), [12-10-SUMMARY.md](12-10-SUMMARY.md), and [12-11-SUMMARY.md](12-11-SUMMARY.md).

Task commits: player speed smoke and M1 PPU control `3ca58af`, D-41 capability wording `025aedd`, and installed C/C++ speed guests with unarmed-twin controls `4ed085b`. The smoke pins the speed fixture's RGBA digest and CGB title token; claims checks pass across player surfaces. Freshly installed C and C++ consumers pass their bounded public-API switch guests, both unarmed twins are rejected, and symbol coverage is unchanged. `speed.gb` remains SHA-256 `3c6e88de1e28d47566f7486dd13813c8fb1baf48ee336509e3902bd9ff8e2f3f`. Software-model evidence only; no hardware or perceptual result is claimed.

The consumer observes frame generation through the existing `gbb_frame_info` API and continues bounded calls after the first `HALTED_IDLE`, because the guest halts before the first frame completes. The two-frame cap is retained.

Next plan: **GB-12 plan 12-13 — reproducible CGB speed fixture and offline workflow controls**. Next phase after Phase 12: **Phase 13 — CGB HDMA** (not started). Next command: **`/gsd-execute-phase 12`** (resumes at 12-13). Auto-advance and auto-chain remain false. Stop after Phase 12 and wait for the owner before entering another phase.
