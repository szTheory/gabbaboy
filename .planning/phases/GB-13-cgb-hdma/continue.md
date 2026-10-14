# Phase 13 continuation

Completed stage: **Phase 13 plan 13-04 execution — Partition, lifecycle and hostile-resource invariants** (2026-10-14); both tasks and four TDD commits are complete. Phase 13 remains active and CGB-07 remains open.
Next stage: **Phase 13 plan 13-08 execution — Original visible DMA guest and existing player smoke**. Exact command: **`/gsd-execute-phase 13`**.

Plan 13-06 admits exactly `gbc_dma_cont`, `gdma_addr_mask`, `hdma_lcd_off`, and `hdma_mode0` from SameSuite revision `f15645fb049a47ea235f6d2c9a033e72d8087901`. Offline provenance checks, all named negative controls, and exact RGBDS 1.0.1 rebuild comparisons pass. The existing fixture-repro job runs the mandatory complete set. See [13-06-SUMMARY.md](13-06-SUMMARY.md), [13-02-SUMMARY.md](13-02-SUMMARY.md), and [13-01-SUMMARY.md](13-01-SUMMARY.md).

The fixture results establish source/ROM provenance only. The SameSuite author expectations and SameBoy agreement are not independent physical CGB-E evidence; the D-06/Pan Docs contradiction remains recorded without changing upstream expectations. Mealybug CGB-C bytes remain outside this admitted set under the unresolved G1 rights gate.

Plan 13-03 adds public guest HALT/timer-IRQ wake, independent speed-pause and HDMA residuals, selected STOP freeze behavior, and OAM/HDMA/PPU ordering. Plan 13-04 adds the explicit full-field partition oracle, lifecycle and isolation checks, finite-work headroom guard, capacity checks and bounded FF51–55 seeds. Its task checks passed 33/33 and 16/16, full CTest passed 940/940, and the frozen DMG baseline has no changed rows. The matching Clang libFuzzer runtime was unavailable, so no libFuzzer campaign is claimed. See [13-04-SUMMARY.md](13-04-SUMMARY.md) for exact commits and receipts.

Continue with plan 13-08 only. Reuse the 13-04, 13-03, 13-06, 13-02, and 13-01 summaries and established decisions unless a concrete discriminator fails or new evidence changes them. Phase 14 remains unstarted. Both auto-advance flags remain false; stop before Phase 14.
