# Phase 13 continuation

Completed stage: **Phase 13 automated UAT complete**.

All 45 deliverables across 12 plans close automatically, zero human checkpoints or gaps. The exact mapping and no-repeat rule are in [13-UAT.md](13-UAT.md); the goal report is [13-VERIFICATION.md](13-VERIFICATION.md). Fresh full native 994/994 and SDL3 player 1,087/1,087 suites at source `e556c1b` pass with no skips. Reviewed source `eeb1ce9` passes focused 9/9 and exact installed/package consumers 6/6. The DMG baseline has zero changed rows. See [13-BENCH.md](13-BENCH.md) for source-qualified receipts; final published UAT metadata requires its own exact-head CI before the pre-authorized PR #69 merge. GitHub holds that final head and merge receipt.
Next stage: **Phase 14 discussion**.
Next command: `/gsd-discuss-phase 14`.

Reuse this completed UAT and existing research/decisions; do not rerun verify-work, replan or ask a confirmation-only question on unchanged evidence. Reopen only changed covered behavior, a concrete regression or stale/unavailable evidence. D-069 and LESSONS GB-GSD-016 govern future phases by default. Both auto flags remain false; Phase 14 — CGB-E Model Qualification and Corpus remains unstarted.

The Phase 13 software fixture denominator remains 5/5 for CGB-E; optional CGB-C evidence remains rights-gated and outside that denominator. The D-06/Pan Docs discrepancy and timing/APU/mode-3/game limits remain explicit. These software test and fixture results do not qualify physical hardware.

Read [13-11-SUMMARY.md](13-11-SUMMARY.md) for the latest claim contracts and TDD receipts. Read [13-10-SUMMARY.md](13-10-SUMMARY.md) for installed-package evidence; [13-05-SUMMARY.md](13-05-SUMMARY.md) retains the HDMA test-harness and bounded-oracle receipts. One generated test-only runtime-mask core serves the public, internal, and partition harnesses. The public guest predicate detects full CPU no-steal behavior, while sub-byte cadence sensitivity is checked by the bounded signed-offset internal oracle. Physical CGB-E timing remains UNKNOWN. No matching Clang libFuzzer runtime was available, so no campaign is claimed.

Plan 13-06 admits exactly `gbc_dma_cont`, `gdma_addr_mask`, `hdma_lcd_off`, and `hdma_mode0` from SameSuite revision `f15645fb049a47ea235f6d2c9a033e72d8087901`. Offline provenance checks, all named negative controls, and exact RGBDS 1.0.1 rebuild comparisons pass. The existing fixture-repro job runs the mandatory complete set. See [13-06-SUMMARY.md](13-06-SUMMARY.md), [13-02-SUMMARY.md](13-02-SUMMARY.md), and [13-01-SUMMARY.md](13-01-SUMMARY.md).

The fixture results establish source/ROM provenance only. The SameSuite author expectations and SameBoy agreement are not independent physical CGB-E evidence; the D-06/Pan Docs contradiction remains recorded without changing upstream expectations. Mealybug CGB-C bytes remain outside this admitted set under the unresolved G1 rights gate.

Plan 13-03 adds public guest HALT/timer-IRQ wake, independent speed-pause and HDMA residuals, selected STOP freeze behavior, and OAM/HDMA/PPU ordering. Plan 13-04 adds the explicit full-field partition oracle, lifecycle and isolation checks, finite-work headroom guard, capacity checks and bounded FF51–55 seeds. Its task checks passed 33/33 and 16/16, full CTest passed 940/940, and the frozen DMG baseline has no changed rows. The matching Clang libFuzzer runtime was unavailable, so no libFuzzer campaign is claimed. See [13-04-SUMMARY.md](13-04-SUMMARY.md) for exact commits and receipts.

Plan 13-07 pins the 32,768-byte `hblank_vram_dma.gbc` at SHA-256 `e8124ce687d37a2402e20af92af1299610bfbda0871d605084c0bba2bf57135c`, rebuilt from MagenTests revision `3f9c090f16e5a721db776febb9ba7d773e1c819c` using digest-verified RGBDS 0.6.1. Its source map starts at ROM `$022C`; FF52 aligns the first transfer to `$0220`, yielding 12 `$FF` bytes and 1,012 tile-index-1 bytes. The visible screen is green only after map/status/HALT checks, with digest pinned afterward. See [13-07-SUMMARY.md](13-07-SUMMARY.md) for evidence and commits.

Read [13-09-SUMMARY.md](13-09-SUMMARY.md) for the exact fixture dispositions, mutation controls, and verification receipts; [13-08-SUMMARY.md](13-08-SUMMARY.md) retains the original guest and player evidence. Reuse the Phase 13 summaries and established decisions unless a concrete discriminator fails or new evidence changes them. Phase 14 (CGB-E Model Qualification and Corpus) remains unstarted. Both `workflow.auto_advance` and `workflow._auto_chain_active` remain false; stop before Phase 14.
