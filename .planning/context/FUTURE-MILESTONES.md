# Rolling milestone direction

Updated: 2026-10-10 (v0.1 shipped; v0.2 started). This is revisable direction, not authorization to advance. Only the active roadmap has detailed phases. Revisit the next milestone at each phase boundary and re-scope it at the current milestone audit.

| Horizon | Milestone | User outcome | Evidence / scope trigger |
|---|---|---|---|
| Shipped 2026-10-10 | **v0.1 — limited DMG preview** | Download a macOS player for declared ROM-only/MBC1 software, hear audio, retain battery progress, or embed the installed core | Six phases in ROADMAP; legal fixtures, model-qualified tests, fresh-process continuation, qualified packages, initial performance/CI baselines |
| Current: v0.2 Color & Cartridge Breadth, then v0.3 States & Integration | **GB/GBC breadth** (split: v0.2 = game acceptance, MBC2/3/5 + RTC, CGB-CPU-E; v0.3 = STATE-01 save states, INT-01 Playstead) | Play supported CGB software and a broader common cartridge set; use deterministic RTC and complete native states | CGB-01..03, CART-01, RTC-01, STATE-01, INT-01; model-specific clock/HDMA/PPU/APU tests and exact save-state continuation. Before broadening cartridge/CGB support claims, add one rights-clear ROM-only or standard-MBC1 game-level acceptance in the existing player: a guest-observable start/progress condition, meaningful input, and visible/audio response. Keep private game inputs and derived traces local. Split into smaller releases if these are too large together; do not demote CGB behind optional enhancements |
| Following, provisional | **Interoperability and developer tools** | Use a proven Playstead/libretro path, exchange supported saves, inspect clear traces and debug failures easily | Real consumer requirements, BESS/format conformance if adopted, import negative cases, cross-emulator evidence with known limits |
| Later, evidence driven | **Hardware family and accessories** | Use further silicon models, local link, SGB, uncommon cartridges and peripherals | Hardware/test access, licensed fixtures, clear demand; each feature gets an explicit model/peripheral acceptance matrix |
| Ongoing, evidence driven | **Performance and additional hosts** | Lower cost and latency while preserving output, with reliable builds on more hosts | Measured bottlenecks; output-equivalent controlled benchmarks; adopter demand for Wasm/mobile/SIMD/rewind/runahead |

## Release progression within the current milestone

Ship clearly named preview artifacts as capabilities arrive: installed core and real-ROM headless tracer; timed CPU diagnostics; interactive video player; safe battery continuation; sound and stable input/device behavior; qualified limited-DMG release. An artifact can be useful before a milestone is complete, but its release notes must state its actual capability level. Choose exact SemVer/prerelease mechanics during Phase 1 release planning.

## Replanning discipline

At phase completion, record what evidence changed the next step, the weakest useful quality dimension, open regressions, and any real integration constraint. Fix consequential gaps before expanding scope. Retain a next-step command and stop.

At milestone completion, audit traceability and packaged user outcomes, summarize corpus-qualified compatibility and measured performance, export transferable lessons when requested, and revise this table. Do not prewrite speculative implementation plans for all future milestones. No calendar estimates or universal compatibility promises are attached to these horizons.

## Deferred from Phase 8 (revisable direction, not authorization)

- **Mooneye emulator-only/mbc1 backfill:** 13 further ROMs in a sibling-manifest category `mbc1`; `multicart_rom_8Mb` is an excluded candidate (MBC1M wiring is unsupported). Reuse the Phase 8 sibling-set recipe, verifier and runner `suite_def` table.
- **`src/core/cartridge.c` split:** worthwhile only with a named reason. Six build sites must change together: `CMakeLists.txt` core source list and dirty list, the allocation probe, `fuzz_core`, `probe-mooneye-candidate.sh`, the JOYP and ninth-bit mutants (their anchors move files), and the `test_runner.c` include.
- **`read8` region-decode refactor:** only with A/B evidence (identical output digests plus a controlled timing comparison); not justified by the Phase 8 advisory timing.
- **Generalised suite verifier:** when a third Mooneye-style suite arrives, replace the adapted copy `VerifyMooneyeMbc.cmake` with one parameterised verifier.
- **Host haptics for MBC5 rumble:** map `gbb_rumble_state` samples to a host haptic API in the player; needs a real device, an intensity policy and a tested opt-out.
- **Packed 256-byte MBC2 save interop:** import/export of two-nibbles-per-byte saves from other emulators, with named fixtures and format limits.
