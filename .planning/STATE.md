---
gsd_state_version: "1.0"
milestone: v0.2
milestone_name: Color & Cartridge Breadth
current_plan: 12
status: planning
stopped_at: Completed 10-11-PLAN.md
last_updated: "2026-10-12T17:53:34.985Z"
last_activity: 2026-10-12
last_activity_desc: Phase 10 execution started
state_head: 30bb2e27b720e23ee72652183de530c6acb6fc31
progress:
  total_phases: 9
  completed_phases: 4
  total_plans: 65
  completed_plans: 56
  percent: 44
current_phase: 10
current_phase_name: CGB Profile, Banking and Register Visibility
---

# Project State

## Project Reference

See: [PROJECT.md](PROJECT.md) (updated 2026-10-11)

**Core value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Current focus:** Phase 10 — CGB Profile, Banking and Register Visibility

## Current Position

Current Plan: 12
Total Plans in Phase: 20

Completed: Phase 9 (MBC3, Deterministic RTC and Cartridge Persistence) — execution plus the execute-phase tail: code review (4 fixed, 1 skipped), Nyquist validation, security (0 open), regression gate and gsd-verifier `passed` (09-VERIFICATION.md)
Verified: Phase 9 `/gsd-verify-work 9` passed 2026-10-12 — 14/14 UAT items automated (09-UAT.md), the guide-wording item replaced by the `native_guide_rtc_contract` check; re-verification `passed` (09-VERIFICATION.md); PR #65 squash-merges at the exact-head green branch head (pre-authorized)
Next step: Phase 10 — CGB Profile, Banking and Register Visibility — execution via `/gsd-execute-phase 10` (planned 2026-10-12; owner chooses when)
Last activity: 2026-10-12 — Phase 10 execution started

Progress (v0.2): [███░░░░░░░] 33% (3/9 phases)

## Performance Metrics

- Completed unique plans: 56; recorded execution total: 1002 min. Phase 6 completed all seven reviewed plans in six dependency-ordered waves; its refreshed report passes 5/5 at `f0acb86`.
- Per-phase metrics / recent trend: All six phase implementations and 56/56 runnable plans are complete; the current OpenGSD freshness gate accepts all six phases. Phase 1's 2026-10-10 refreshed verification passes 21/21 at `ebce345` with 179/179 local CTest. Phase 2's 2026-10-10 refreshed verification passes 5/5 and CPU-01–05 at `a9050df` after quick task 261010-bz3 reconciled its CPU-02/CPU-05 SUMMARY metadata. Phase 3's refreshed verification passes 5/5; current core CTest passed 179/179, optional player tests passed 51/51, and focused output-directory safety regressions passed 8/8. Phase 5's 2026-10-10 refreshed verification passes 17/17 at `f39faac`; its clean-tree PCM receipt is recorded in its verification report. Phase 6's 2026-10-10 refreshed verification passes 5/5 at `f0acb86`; its historical asset and hosted-receipt evidence stays in its validation report. Phase 4 has 7/7 verified truths and a clean source review. FIFO ROM-open hardening passed exact-head PR #43 checks and is merged. D-025 bounds VIDEO-02/03 to the confidence-qualified software model; no physical CPU-B measurement is claimed. Plan 02-15 is superseded/non-runnable and remains historical.
- Emulator correctness, speed, memory, and CI baselines: No general hardware/gameplay baseline. The current Phase 2 refresh passed 179/179 local CTest, 88/88 focused Phase 2 cases, three eligible runner receipts, and the protocol probe with zero PPU accesses. Historical exact evidence at implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989` includes the 104/104 offline core inventory, 109/109 relocated installed C/C++ inventory, hosted CI run 37620710587, and fixture reproduction run 37620710600. Original upstream PPU-dependent reporting paths remain excluded; no physical DMG hardware test occurred.

**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01 P01 | 14 | 2 tasks | 11 files |
| Phase 01 P02 | 7 min | 2 tasks | 7 files |
| Phase 01 P03 | 94 min | 3 tasks | 10 files |
| Phase 01 P04 | 31 min | 2 tasks | 12 files |
| Phase 01 P05 | 84 min | 3 tasks | 15 files |
| Phase GB-02 P01 | 22min | 2 tasks | 14 files |
| Phase GB-02 P02 | 43 min | 2 tasks | 10 files |
| Phase 02 P03 | 6 | 2 tasks | 4 files |
| Phase 02 P04 | 16min | 2 tasks | 7 files |
| Phase GB-02 P05 | 18 | 2 tasks | 5 files |
| Phase GB-02 P06 | 6 min | 2 tasks | 7 files |
| Phase GB-02 P07 | 20 | 3 tasks | 12 files |
| Phase GB-02 P08 | 8 min | 2 tasks | 10 files |
| Phase GB-02 P09 | 8 min | 2 tasks | 10 files |
| Phase GB-02 P10 | 10 min | 2 tasks | 5 files |
| Phase GB-02 P11 | 12 min | 2 tasks | 4 files |
| Phase GB-02 P12 | 9 min | 2 tasks | 6 files |
| Phase GB-02 P13 | 8 min | 2 tasks | 3 files |
| Phase GB-02 P14 | 8 min | 2 tasks | 4 files |
| Phase GB-02 P17 | 54 min | 3 tasks | 12 files |
| Phase 02 P16 | 24min | 2 tasks | 6 files |
| Phase 02 P18 | 25 min | 2 tasks | 5 files |
| Phase GB-03 P01/P02 | 20/30 min | 1/2 tasks | 10/5 files |
| Phase GB-03 P03/P04/P05/P06/P07/P08/P09 | 79/11/19/15/10/12/24 min | 2/2/2/2/2/2/2 tasks | 6/10/8/11/9/3/5 files |
| Phase GB-03 P10 | 9+ min (lower bound; exact start not captured) | 3 tasks | 4 files |
| Phase GB-03 P11 | 4min+ minimum recorded | 2 tasks | 6 files |
| Phase GB-03 P12 | ~30 min | 2 tasks | 6 files |
| Phase GB-03 P13 | not captured | 3 tasks | implementation, tests, evidence and continuity files |
| Phase 04 P01 | 13 | 2 tasks | 12 files |
| Phase 04 P02 | 8min | 2 tasks | 7 files |
| Phase 04 P03 | 14min | 2 tasks | 5 files |
| Phase 04 P04 | 11min | 2 tasks | 8 files |
| Phase 04 P05 | 7min | 2 tasks | 11 files |
| Phase 04 P06 | 10 min | 2 tasks | 13 files |
| Phase 04 P07 | 18 min | 2 tasks | documentation, evidence, and workflow metadata |
| Phase GB-05 P01 | 13min | 2 tasks | 8 files |
| Phase GB-05 P02 | 17min | 2 tasks | 5 files |
| Phase GB-05 P03 | 21min | 2 tasks | 8 files |
| Phase GB-05 P04 | 62 min | 2 tasks | 7 files |
| Phase GB-05 P05 | 12 min | 2 tasks | 6 files |
| Phase 05 P06 | 25 min | 3 tasks | 14 files |
| Phase GB-05 P07 | 32min | 2 tasks | 12 files |
| Phase GB-06 P01 | 167 | 2 tasks | 7 files |
| Phase GB-06 P05 | 19 min | 2 tasks | 8 files |
| Phase GB-06 P02 | 8 | 2 tasks | 3 files |
| Phase GB-06 P04 | 8 min | 2 tasks | 6 files |
| Phase GB-06 P03 | 6 min | 2 tasks | 8 files |
| Phase GB-06 P07 | 7min | 2 tasks | 4 files |
| Phase GB-06 P06 | 95 min | 2 tasks | release workflow, evidence, and handoff |
| Phase 06.1 P01 | 3 min | 2 tasks | 2 files |
| Phase 06.1 P02 | 12 min | 3 tasks | 4 files |
| Phase GB-06.1 P03 | 15 min | 2 tasks | 1 files |
| Phase GB-06.1 P04 | 30 min | 3 tasks | 4 files |
| Phase GB-06.1 P05 | 20 min | 2 tasks | 11 files |
| Phase GB-06.1 P06 | 10 min | 2 tasks | 10 files |
| Phase GB-06.1 P07 | 13 min | 2 tasks | 11 files |
| Phase 06.1 P08 | 10 min | 2 tasks | 2 files |
| Phase 07 P01 | 18min | 3 tasks | 11 files |
| Phase 07 P02 | 40 min | 3 tasks | 12 files |
| Phase 07 P03 | 30 min | 2 tasks | 5 files |
| Phase 07 P04 | 20 min | 2 tasks | 4 files |
| Phase 07 P05 | 6 min | 2 tasks | 10 files |
| Phase 07 P17 | 25 min | 2 tasks | 2 files |
| Phase 07 P06 | 25 min | 2 tasks | 11 files |
| Phase 07 P07 | 75 min | 2 tasks | 11 files |
| Phase 07 P08 | 25 min | 2 tasks | 9 files |
| Phase 07 P09 | 20 min | 2 tasks | 7 files |
| Phase 07 P10 | 35 min | 2 tasks | 8 files |
| Phase 07 P11 | 130 min | 3 tasks | 9 files |
| Phase 07 P12 | 40 min | 2 tasks | 6 files |
| Phase 07 P13 | 75 min | 3 tasks | 8 files |
| Phase GB-07 P14 | 55 min | 3 tasks | 5 files |
| Phase GB-07 P07-15 | 70 min | 2 tasks | 7 files |
| Phase 7 P16 | 100 min | 3 tasks | 7 files |
| Phase 08 P01 | 70 min | 3 tasks | 3 files |
| Phase GB-08 P08-02 | 40 min | 3 tasks | 5 files |
| Phase 08 P03 | 55 min | 3 tasks | 8 files |
| Phase 08 P04 | 20 min | 2 tasks | 7 files |
| Phase 08 P05 | 40 min | 2 tasks | 24 files |
| Phase 08 P06 | 30 min | 3 tasks | 7 files |
| Phase 08 P07 | 150 min | 2 tasks | 7 files |
| Phase 08 P08-08 | 25 min | 4 tasks | 11 files |
| Phase 08 P09 | 40 min | 2 tasks | 14 files |
| Phase 08 P10 | 45 min | 2 tasks | 2 files |
| Phase 09 P01 | 25 min | 2 tasks | 7 files |
| Phase 9 P02 | 15 min | 2 tasks | 10 files |
| Phase 9 P03 | 8 min | 2 tasks | 2 files |
| Phase 9 P04 | 15 min | 2 tasks | 5 files |
| Phase 09 P05 | 20 min | 2 tasks | 5 files |
| Phase 09 P06 | 12 min | 2 tasks | 5 files |
| Phase 09 P07 | 20 min | 3 tasks | 4 files |
| Phase 9 P08 | 25 min | 3 tasks | 11 files |
| Phase 9 P09-09 | 85 min | 3 tasks | 9 files |
| Phase 09 P10 | 25 min | 2 tasks | 8 files |
| Phase 9 P11 | 40 min | 3 tasks | 9 files |
| Phase 9 P12 | 55 min | 3 tasks | 10 files |
| Phase 09 P13 | 55 min | 3 tasks | 9 files |
| Phase 09 P14 | 12 min | 2 tasks | 3 files |
| Phase 09 P15 | 45 min | 3 tasks | 3 files |
| Phase 09 P16 | 70 min | 3 tasks | 11 files |
| Phase 9 P17 | 60 min | 2 tasks | 9 files |
| Phase 9 P18 | 150 min | 2 tasks | 12 files |
| Phase 10 P01 | 25 min | 2 tasks | 4 files |
| Phase 10 P02 | 40 min | 2 tasks | 4 files |
| Phase 10 P03 | 35 min | 2 tasks | 8 files |
| Phase 10 P04 | 40 min | 2 tasks | 5 files |
| Phase 10 P05 | 35 min | 3 tasks | 8 files |
| Phase 10 P06 | 55 min | 3 tasks | 8 files |
| Phase 10 P07 | 12 min | 2 tasks | 4 files |
| Phase 10 P08 | 15 min | 2 tasks | 5 files |
| Phase 10 P09 | 40 min | 3 tasks | 8 files |
| Phase 10 P10 | 35min | 3 tasks | 5 files |
| Phase 10 P11 | 25 min | 2 tasks | 6 files |

## Accumulated Context

### Decisions

Adopted choices: [DECISIONS.md](context/DECISIONS.md). Evidence navigation: [research/INDEX.md](research/INDEX.md); synthesis dated 2026-10-02.

- Scope is GB/DMG and GBC/CGB. v0.1 is a limited DMG preview; GB/GBC breadth is the next named milestone.
- Original portable C17 core, native opaque-instance API, optional SDL3 macOS adapter; explicit time/ownership and bounded operations.
- ROM-only/scoped MBC1 and battery continuation in v0.1; no stable ABI promise. Future scope remains in [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md).
- OpenGSD workflow: automate within the authorized phase, require current evidence, then stop. Both auto-advance settings remain false; session model is inherited.
- [Phase 01]: The tracer starts from an explicit bootless DMG-CPU-B profile; deterministic RAM fill is emulator policy, not hardware startup evidence.
- [Phase 01]: RGBDS v1.0.1 is required only for fixture regeneration; normal build and digest verification use checked-in bytes offline.
- [Phase 01]: ROM validation returns distinct bounded errors and failed replacement loads leave active guest state unchanged.
- [Phase 01]: Reset retains the loaded ROM while restoring deterministic post-boot CPU state and clearing guest RAM and emulated time.
- [Phase 01]: The installed export explicitly maps the core library to GabbaBoy::core.
- [Phase 01]: Installed consumer tests are registered only when the relocated prefix exists, preserving ordinary offline CTest runs.
- [Phase 01]: CI uses explicit runner labels and a fail-closed 26-case installed CTest inventory with a 23-case core subset; runner images are not product OS claims.
- [Phase 01]: The official CMake 3.25.3 floor script and RGBDS 1.0.1 fixture reproduction passed locally in Ubuntu x86_64 containers and on PR #1; run-scoped hosted evidence is recorded in 01-VALIDATION.md.
- [Phase 01]: Pin explicit native runner labels and require every evidence job plus its exact test inventory; do not infer product OS support from runner labels.
- [Phase 01]: Keep hosted CI and branch-protection evidence pending until exact-revision remote results are observed; fixture-repro is a separate status context.
- [Phase GB-01]: Qualify preview packages and contributor claims against an exact PR SHA; query the artifact API for per-run expiry and report it without calling temporary artifacts releases.
- [Phase 01]: The bootless DMG-CPU-B tracer verifies the bounded API and guest path, not hardware-qualified memory mapping; Phase 2 owns that evidence.
- [Phase 01]: At verified implementation SHA `8396096ad17500974b30657af91fd2ef9ad51237`, all five roadmap truths and eight BASE requirements passed, standard code review was clean, and required PR contexts plus both package artifacts passed exact-SHA verification.
- [Phase 01]: Final exact hosted evidence also passed at docs-only PR SHA `9f1df9bd0a70e50033f7d8cbcbff778e3bfd94e3` after the Phase 1 closeout documentation was committed; the implementation is unchanged from SHA `8396096ad17500974b30657af91fd2ef9ad51237`.
- [Phase GB-02]: ROM-only A000-BFFF reads stop as unsupported bus and writes have no effect.
- [Phase GB-02]: The side-effect-free peek API exposes WRAM, its echo, and HRAM only.
- [Phase GB-02]: The original tracer moved its protocol from fixture-policy A000 RAM to WRAM C000/C001.
- [Phase GB-02]: RGBDS 1.0.1 fixture regeneration uses the SHA-verified official macOS archive.
- [Phase GB-02]: Unused SM83 encodings persistently lock with original PC/opcode until reset; CB-prefixed instruction semantics are owned by Plan 02-03.
- [Phase 02]: CB register operations cost 16 half-dots; BIT (HL) costs 24; other (HL) CB operations cost 32.
- [Phase 02]: BIT preserves carry and sets H; RES and SET preserve flags; rotate/shift groups set Z and carry from their results.
- [Phase 02]: Interrupt entry costs 40 half-dots, selects the lowest enabled pending bit, clears it, and pushes the interrupted PC on timed bus phases.
- [Phase 02]: HALT idle advances eligible time in whole 8-half-dot cycles; STOP remains stopped until the timestamped wake path in Plan 02-06.
- [Phase GB-02]: Timer divider falling edges and qualified TIMA/TMA reload collisions run at timed bus phases; serial overlap without qualified ordering returns bounded unsupported.
- [Phase GB-02]: STOP waits advance only the bounded master timeline; oscillator-driven CPU, divider, timer, and internal serial state stays frozen.
- [Phase GB-02]: Timestamped input uses a fixed 64-event queue with atomic admission and stable caller order for equal timestamps.
- [Phase GB-02]: Keep the eligible CPU/timer corpus denominator fixed; guest assertions, callbacks and exact result PCs classify outcomes, while digests alone never qualify applicability.
- [Phase GB-02]: Preserve derived fixture bytes, rights and pinned reproduction procedures; original PPU-dependent behavior and physical hardware remain outside the corpus claim.
- [Phase GB-02]: CPU, timer, interrupts, HALT/STOP and reset semantics are covered by the completed Phase 2 verification and validation artifacts.
- [Phase GB-02]: Installed C/C++ consumers and hosted exact-revision checks cover the Phase 2 public package; see the linked verification artifacts.
- [Phase GB-02]: On 2026-10-07, independent verification passed CPU-01 through CPU-05 and all five roadmap truths at implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989`. Final local, installed-consumer, and exact hosted evidence is recorded in Phase 2 verification and validation; original upstream PPU-dependent results and physical hardware behavior remain outside the claim.
- [Phase GB-03]: Keep the playable original ROM fixture separate from PPU composition, raster timing, DMA/access, and scripted gameplay oracles; fixture byte reproducibility does not establish DMG-CPU-B applicability.
- [Phase GB-03]: The initial background renderer advances dots on the emulated timeline and publishes a completed shade frame at VBlank entry; it is not hardware-qualified raster timing.
- [Phase GB-03]: Plan 03-02 adds fixed per-instance transfer slots and source-qualified mode/STAT/fetch expectations; the slot model does not claim electrical or CPU-B FIFO equivalence.
- [Phase GB-03]: Plan 03-03 adopts the narrower Nintendo-manual `$8000–$DFFF` DMA source range despite a pinned Pan Docs conflict; exact simultaneous PPU/DMA collision behavior remains unqualified.
- [Phase GB-03]: FF00 active-low row polling consumes timestamped button events; JOYP interrupt behavior remains gated by D-08. The optional SDL3 player bounds and transactionally replaces ROMs, keeps mutations on the event loop, and uses pixel-aligned integer scaling. The public frame API checks output extents/overlap before writes, and queue capacity precedes entry validation; relocated consumers test both APIs. RGBDS 1.0.1 fixture reproduction now binds assembly source, exact ROM bytes, and pinned archive digests locally and in hosted CI; this is not gameplay or hardware evidence. SDL3 3.4.18 and host timing remain isolated to the adapter.
- [Phase GB-03]: Player help and downloaded-package metadata now assert the preview's audio and battery-persistence limitations; those checks do not establish emulator feature behavior or hardware qualification.
- [Phase GB-03]: Pinned Mooneye cases support the fresh DMA access window, active FF46 restart, and register readback; a focused owned guest suite covers those cases. The upstream README lists a DMG-CPU-B in its hardware fleet but publishes no per-test/per-unit raw log. This evidence does not cover simultaneous PPU/DMA arbitration or JOYP interrupt timing.
- [Phase GB-03]: D-025 adopts a deterministic, confidence-qualified source-backed software model for documented but revision-sensitive JOYP and DMA/PPU behavior; exact CPU-B phases and revision parity remain unmeasured.
- [Phase GB-03]: The optional SDL3 macOS preview displayed the owned demo; the user confirmed holding Z darkens a tile and release restores it. Audio and battery persistence remain clearly identified as unimplemented.
- [Phase GB-03]: The rendered Z-down/held/up shades are asserted by the SDL smoke, and macOS package build plus downloaded-package consumer checks are required on every pull request. The 2026-10-09 UAT remains the single human confirmation of visible window behavior.
- [Phase GB-03]: Final verification passed 5/5 truths and UAT 33/33; PR #4 passed required exact-head checks and merged as `2b49dc5`.
- [Phase 04]: Hold a nonblocking exclusive advisory lock for the lifetime of each battery-backed player session; the guarantee covers cooperating GabbaBoy processes.
- [Phase 04]: Drive autosave from the core dirty generation and monotonic host time: two seconds quiet or ten seconds maximum age.
- [Phase 04]: On final save failure, require retry, explicit continue without saving, or cancellation before quit, reset, or replacement.
- [Phase 04]: Keep the original MBC1 battery fixture source, rights, manifest, pinned RGBDS recipe, and checked-in bytes together; ordinary tests verify the digest offline.
- [Phase 04]: Prove guest continuation with separate bounded processes and distinct missing-save, wrong-ROM-envelope, and altered-payload controls; this is software evidence, not physical hardware qualification.
- [Phase GB-05]: Expose audio-aware stepping as gbb_run_audio with caller-owned 48 kHz stereo frames; keep legacy run calls muted.
- [Phase GB-05]: Plan 05-03 adds wave/noise channels and all 16 NR52 status combinations as authored deterministic software-model evidence; active wave-RAM current-byte aliasing is an unqualified revision-scoped assumption. AUDIO-01 is complete for the documented digital model; analog, physical hardware, and perceptual output are not qualified.
- [Phase GB-05]: Active wave-RAM accesses alias the current byte in the scoped deterministic model; CPU-B revision variation is unqualified.
- [Phase GB-05]: Use an original per-instance Q15 8-tap FIR and the D-02 48 kHz high-pass approximation; preserve DSP history across output calls and reset it on APU reset.
- [Phase GB-05]: Reject overflowing PCM frame extents and overlap with the returned count before guest work; initialize a valid count output to zero.
- [Phase GB-05]: SDL callback services exact requested bytes and retains partial stereo frames across callbacks to avoid queue overrun.
- [Phase GB-05]: Unavailable audio sinks discard and count PCM immediately while preserving host-paced guest execution.
- [Phase GB-05]: Player gain is host-only, defaults to 100%, and is adjusted with bracket keys.
- [Phase GB-05]: Keep per-controller input keyed by stable SDL joystick IDs in a fixed bounded source table, and admit aggregate button changes to the guest queue before committing source state.
- [Phase GB-05]: Quiesce callbacks before counting and clearing ring, partial-frame, and SDL-stream PCM; perform reset and replacement host cleanup only after existing save transitions succeed.
- [Phase GB-05]: Treat SDL dummy audio and injected device events as software-path evidence; physical hotplug and audible quality remain unqualified.
- [Phase GB-05]: Bind the sustained result to the committed source revision, Release build, scoped DMG model, original licensed fixture, and PCM digest.
- [Phase GB-05]: Keep SDL queued-input bytes and application PCM underflow explicitly separate from playback latency and hardware starvation.
- [Phase GB-05]: Report dummy backend and default-device availability as software/device-presence evidence only; do not claim physical hotplug or perceptual qualification.
- [Phase GB-06]: CMake PROJECT_VERSION remains the product version source; release-please updates the matching v-prefixed tag version.
- [Phase GB-06]: Use GITHUB_TOKEN for version PRs and preserve the normal exact-head workflow approval gate.
- [Phase GB-06]: Keep the Linux candidate unpublished until the final Phase 6 release gate.
- [Phase GB-06]: Keep source, build, and downloaded-byte evidence in separate digest-linked receipts.
- [Phase GB-06]: Keep deterministic loader/battery/API regressions mandatory and enable compiler-integrated libFuzzer only when the matching Clang runtime is available; bound each input's size and work.
- [Phase GB-06]: Keep downloaded Windows release archive qualification on the existing native consumer lane and reuse the current C and C++ consumer projects.
- [Phase GB-06]: Force SDL dummy audio and video for the macOS player package smoke; report software-only behavior.
- [Phase GB-06]: Require an exact core/player release asset set and hash manifest before a platform candidate is ready.
- [Phase GB-06]: Keep stable support facts in a tracked versioned ledger and bind the exact tagged ledger blob and source SHA in a separate release sidecar.
- [Phase GB-06]: Record fixed-workload speed, process peak RSS, trace pairing, build duration, exact-source hosted check durations, and uncertainty; keep budgets advisory until repeated variance justifies one.
- [Phase GB-06]: Use the installed visible-demo fixture for successful frame output and sequentially load the MBC1 continuation fixture into the same opaque instance for save transfer.
- [Phase GB-06]: Install the visible-demo ROM with its manifest and license so the relocated native example needs no source-tree path.
- [Phase GB-06]: Keep raw battery persistence host-owned and replace only after an exclusive temporary file is flushed.
- [Phase 06.1]: Installed-consumer audio smoke is structural only (formula frame count, bounds, poison, twin/reset hash equality); no digest literal pinned
- [Phase 06.1]: 06.1-02: O_NOCTTY added to read_rom_file only; read_save_file intentionally unchanged (D-05 scope)
- [Phase GB-06.1]: 06.1-03: exact-head gate orders by run_number only; player run_attempt output taken from macos-player-package job object; terminal failures debounced over 2 polls on same (id, attempt)
- [Phase GB-06.1]: player-gate job is the single definition of player_required in ci.yml; check-player-result.sh fails closed on non-success gate
- [Phase GB-06.1]: 06.1-05: Phases 1 and 2 re-verified passed after PR 54 on the docs-only refresh branch; P1 covered_files gains wait-exact-head-ci.py and check-player-result.sh; P1 IN-01/IN-02 and P2 IN-01 fixed; new P1 IN-03/IN-04 deferred until the next wait-exact-head-ci.py change — D-10 refresh in order through execute-phase verification gates; D-09 forbids code fixes on the refresh branch
- [Phase GB-06.1]: 06.1-06: Phases 3 and 4 re-verified passed after PR 54 on the docs-only refresh branch; P3 covered_files gains wait-exact-head-ci.py and check-player-result.sh; P3 IN-01/IN-02/IN-03 fixed (IN-01 close-failure branch inspection-only); P4 stale only through session.c and test_session.c, covered set unchanged — D-10 refresh in order through execute-phase verification gates; D-09 forbids code fixes on the refresh branch
- [Phase GB-06.1]: 06.1-07: Phases 5 and 6 refreshed passed; Phase 6 covered_files gains tests/consumers/c/main.c and tests/consumers/cpp/main.cpp; P5 IN-01 fixed (documented); audit audio-consumer gap fixed; 06.1 did not change release.yml (pre-existing drift from v0.1.0 recorded)
- [Phase 07]: 07-01: the Libbet notice row pins the manifest, ROM and LICENSE.txt digests and libbet_notice checks all three; the verifier enforces the eight predicate addresses and five ROM anchors as constants
- [Phase 07]: 07-01: closure completeness is checked by EXPECTED_CLOSURE_SHA256 in required CI and by --derive-closure on the pinned source (45 files, conservative over-approximation); hosted reproduction stays unclaimed until a real run URL exists
- [Phase 07]: 07-02: gbb_accept_drive end_half_dots is the last logical deadline; predicate anchors_ok checks the SHA-256 before any anchor; drive callbacks share one context and max_batch is 1..64 (replay uses 32)
- [Phase 07]: D-027: mixer headroom divide-by-16 fixes Libbet clipping (D-19(i))
- [Phase 07]: 07-04: Libbet reproduction pins Pillow wheels for cp310-cp314 (linux x86_64, macOS arm64) and relies on the D-02 archive SHA-256 because GitHub reports no asset digest; hosted run stays null
- [Phase 07]: 07-05: Frame-digest oracles parse but the runner refuses them with exit 3 unsupported-oracle until the digest plan; runner uses tail_half_dots=0 since the verdict is T_hit
- [Phase 07]: D-028: D-19(ii) early Start taps are expected Libbet intro behaviour; joypad path unchanged
- [Phase 07]: 07-06: acceptance_negative_* forbid only status=(pass|fail|unsupported); invalid-input diagnostics print status=invalid by design
- [Phase 07]: D-029: Libbet checkpoint structure gate is >=2 distinct shades for title/play_start and >=3 for mid/hit (pinned title screen is 1-bit text); refines D-25; ratified by the owner 2026-10-11
- [Phase 07]: PCM window is stepping calls starting at or after play_start; run continues 1 s past T_hit so the window ends at T_hit+1 s (07-07)
- [Phase 07]: 07-08: gbb_case_applicability decides model before revision; model_fail strict (xfail only for declared reason); suite requires --expect-excluded and fails on excluded-count-mismatch; only dmg-cpu-b executes
- [Phase 07]: 07-09: daa LD B,B digest is a regression-class observation (mooneye.daa.frame), never a case-file reference; ldbb-controls.txt references are configure-enforced to the stdlib uniform-3 digest (D-26)
- [Phase 07]: 07-10: control regexes match the full status line (status=fail model=dmg-cpu-b reason=...); final_* fields print on every non-pass predicate line
- [Phase 07]: 07-11: D-16 PCM thresholds unchanged (peak_to_peak 2048, changes 4800); O=20290/164822, N=0/0 at exact head b6f982b, identical on Linux, macOS and Windows
- [Phase 07]: 07-11: stall report (D-18) also covers exit 3 and writes the failure PPM there; acceptance_parse_script_errors compares events field-wise (MSVC padding)
- [Phase GB-07]: 07-14: surface check forbids a superset of tokens (freopen, O_* flags, non-literal fopen mode, session persistence names); test_player_session compiles audio/input/script_smoke sources directly
- [Phase GB-07]: 07-15: DMG-CPU-B v1 ledger frozen at 5a55f19 in baseline commit 42faf9b; one ledger for all OS, changes only via CHANGES.md rows (D-30..D-35)
- [Phase 08]: 08-01: cartridge mapper section placed before gbb_instance; helpers take cart_state plus sizes
- [Phase GB-08]: MBC2 RAM stored canonical 0xF0|nibble; battery export is the stored image and import normalises before compare (08-02)
- [Phase 08]: 08-05: mbc2/mbc5 Mooneye derivatives admitted by manifest digest; budgets = ceil(2*ticks/100000)*100000; no D-27 patch needed (15/15 pass)
- [Phase 08]: 08-06: Mooneye mbc builder pin is read from the digest-checked parent manifest (sibling carries no builder object); type-mutation control requires an unmutated pass first
- [Phase 08]: 08-08: ninth bank bit proved by mbc5_bank_1ff plus test-only ninth-bit mutant (fails at C005, control passes); rom_64Mb is the 8 MiB loader/install-policy case only
- [Phase 08]: 08-09: D-049..D-062 recorded (Open Questions 1-7, D-08/D-10/D-32 refinements, D-29 amendment: ninth bit proved by mbc5_bank_1ff, not rom_64Mb)
- [Phase 09]: MBC3 selections 04-07 and 0D-FF map nothing (software-model decision, not hardware-qualified)
- [Phase 09]: MBC3 RAM code 05 is accepted only as an MBC30 marker and answered as UNSUPPORTED_CARTRIDGE_VARIANT after checksum
- [Phase 9]: 09-02: MagenTests ROMs admitted via explicit .gitignore negations; RGBDS 0.6.1 CI archive sha256 pinned in fixtures/magentests/SOURCES.md
- [Phase 9]: D-28: fuzz residue (data[0]&3u)==2u selects synthesised-length mode; 0 loader, 1/3 stateful
- [Phase 9]: 09-04: v0.1.2 save corpus generated by compiling the frozen tag's session.c directly against the pinned SDL3 prefix; reruns byte-identical
- [Phase 09]: 09-06: MBC2 guest selects store vs resume by cells 0-2 reading F3 FA F1; fresh RAM takes store branch
- [Phase 09]: 09-07: MagenTests oracle uses 16 frames plus a 0x149=0x03 negative control requiring shade 3; scan label GBB_FORBIDDEN_LABEL defaults to mooneye
- [Phase 9]: 09-08: rtc3test rebuild equality not claimed until hosted exact-head result=byte-identical (local Docker run was identical)
- [Phase 9]: 09-09: RTC latch on exactly 00 then 01 and unmapped selections 04-07 are project decisions, not hardware-confirmed
- [Phase 9]: 09-09: CI prints no_host_clock result per build leg; native-windows-x64 is MinGW GCC 14.2.0 and uses nm (research A2 resolved)
- [Phase 09]: 09-10: MBC5 continuation guest uses bank 0 and bank 15 GB5 markers; fixture-repro pin-checks and rebuilds all three continuation guests; mbc2/mbc3-rtc/mbc5 continuation ROMs are now tracked via .gitignore exceptions
- [Phase 9]: 09-11: import compares against the live clock projected to now so an identical re-import never bumps the generation; catch_up_policy_table is registered in the core inventory
- [Phase 9]: 09-12: rtc3test transcript groups coloured cells as [+...]/[!...] runs so millisecond numerics stay contiguous; expectations parsed from digest-pinned tests.md
- [Phase 09]: 09-13: MBC1 $03 keeps envelope v1 (-mbc1- name); all other battery types use v2 (-cart- name, 64-byte header, RAM then RTC block, saved_at stamp); a $03 save read from v2 is written back as v2
- [Phase 09]: 09-13: player classifies cartridges from the core (gbb_battery_size, gbb_rtc_catch_up(machine,0)); host clock read only by main.c player_clock_now
- [Phase 09]: 09-15: loader matrix oracle typed from D-27 tables, never from the core validator; RTC mutants use exactly-once tagged anchors with paired controls
- [Phase 09]: 09-16: catch-up applies once per open only for a timer cartridge with an accepted save; --clock-unix is confined to battery smoke argv
- [Phase 10]: 10-01: GATE-00 code tags compare class and basis only; doc row is the single shared GATE-00 entry
- [Phase 10]: 10-02: OAM-DMA CPU bus-conflict branches tagged UNKNOWN expected-failure:cgb-separate-buses (D-17)
- [Phase 10]: Runner carries GBB_RUNNER_PROFILE_CGB=(gbb_profile)2 until Plan 10-05 adds the public enum; CGB runs report create-failed or excluded, never fall back to DMG (D-25)
- [Phase 10]: 10-04: DMG post-boot cells record implemented values; Pan Docs divergences (IF, STAT, NR50, NR51, NR52, OBP0/1, PPU mode, P1) are POLICY with diverges-from-pandocs
- [Phase 10]: 10-05: gbb_create still rejects the CGB profile; probe/get_info append the D-02 API; PGB $143 rejected last on the CGB profile (GATE-67)
- [Phase 10]: 10-06: only compat cells pinned by a named Mooneye test carry HW_TEST; CGB-mode cells are PANDOCS/POLICY/ORACLE_SAMEBOY
- [Phase 10]: 10-06: GATE-68 CGB_ONLY covers compat title-sum B/HL; GATE-03 and GATE-57 are DMG_ONLY model_is_dmg; GATE-04..08 BOTH per-profile column
- [Phase 10]: 10-07: post-boot doc mirror is machine-checked by test_cgb_tables; header-derived cells show base value with rule in reason
- [Phase 10]: IE bits 5-7 stored on CGB profile only; DMG keeps & 0x1F (OQ2, owner veto item 6)
- [Phase 10]: Deferred register accesses latch bus_unsupported with address; latch also reported after interrupt entry
- [Phase 10]: 10-10: visibility matrix doc block lists only non-pre-CGB addresses (213 rows); EXISTING addresses must have no doc row
- [Phase 10]: 10-11: armed STOP on CGB mode latches UNSUPPORTED_BUS at FF4D (GATE-74, DEFERRED(12)); KEY0 lock proven behaviourally

### Pending Todos

None outside the roadmap.

### Blockers/Concerns

- The 2026-10-09 v0.1 audit initially accepted 2/6 verification reports; after the Phase 1 refresh, the live gate accepted 3/6 and the strict requirement matrix accepted 15/35. No integration blockers were found. PR #43 is squash-merged. Current phase-boundary triage found no open issues. PR #41 is an open 0.1.1 Release Please PR, currently merge-blocked at head `7e953ca552551a151c5837fd88add8ca879b69bc` with no checks reported; it is not green and remains unmerged.
- Main branch protection now enforces the three strict required CI contexts for administrators. Follow-up readback showed no required approving-review gate. PR #34 predates admin enforcement and had no recorded approval; its exact required CI contexts were green when merged.
- Phase 1's refreshed validation report is `validated` and Nyquist-compliant, with 179/179 local CTest. Phase 3 Nyquist validation is `validated`, and its UAT is complete at 34/34.

- Phase 2's refreshed canonical verifier passed all five requirements and roadmap truths. The current full local CTest run passed 179/179, the focused Phase 2 selection passed 88/88, all three admitted headless runner cases passed, and the protocol probe recorded zero PPU accesses. No physical DMG-CPU-B observation or broad compatibility claim is made. See [Phase 2 verification](milestones/v0.1-phases/GB-02-dmg-cpu-bus-and-time/02-VERIFICATION.md).
- The admitted corpus is three derived headless reporting closures (one CPU, two timer). Original Mooneye reporting paths depend on PPU/LY behavior outside scope and remain excluded. No physical DMG-CPU-B observation occurred; no hardware qualification is claimed.
- Phase 1 PR #1 and Phase 2 PR #2 were merged on 2026-10-07 after their required exact-head checks passed. The 2026-10-07 triage found no open PRs or issues at that time. Phase 2 verification is limited to its documented DMG-CPU-B CPU/timer scope; no physical DMG observation or PPU qualification is claimed.
- Phase 6 has no open goal, requirement, review, or high/blocking security finding. The release workflow's original post-publication readback failure was repaired before closeout; the live release API and a fresh download reconcile the published 18-asset inventory.
- Exact CPU-B behavior, physical DMG/MBC1 qualification, physical audio/hotplug, perceptual output, Developer ID signing/notarization, and live Playstead GB integration remain unqualified and are stated as limits, not passing claims.
- [Phase 8] Resolved: the D-29 ninth-bit mutant now targets `mbc5_bank_1ff` (D-062); upstream `rom_64Mb` never selects banks >= 256.
- [Phase 9] Resolved: Phase 8 WR-02 (player hard-coded unsupported battery types) — classification now comes only from the core, guarded by `player_session_classification_drift`. Former note: `src/player/session.c` hard-codes the unsupported battery types $06/$1B/$1E. When CART-06 adds MBC2/MBC3/MBC5 persistence, replace the list and add a test that classifies every core type byte as either `battery_backed` or `battery_unsupported`.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|

### Roadmap Evolution

- Phase 06.1 inserted after Phase 6: Address v0.1 tech debt: CI workflow info items and audio consumer coverage (URGENT)
- 2026-10-10: v0.2 roadmap created — Phases 7–15 continue v0.1 numbering. Order follows research/v0.2/SUMMARY.md: acceptance + DMG baseline (7); seam merged with MBC5 and MBC2 (8, MBC5/MBC2 plans parallel after the seam plan); MBC3 + RTC + loader matrix + new-mapper continuation (9); CGB profile/banking (10); colour PPU + player colour (11); double speed (12) and HDMA (13) kept separate and sequential; CGB-E qualification + corpus (14); CGB acceptance, ledger and release (15). Deep phase research flagged for 9, 11, 12, 13, 14. Rights gates: G5/G2 on 7; G1 on 9, 11, 14; G3 on 9; G4 on 11.

## Deferred Items

Active v0.2 requirements are in [REQUIREMENTS.md](REQUIREMENTS.md) (28/28 mapped); deferred v0.3 items (STATE-01, INT-01) and later direction are in its Future section and [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md), not counted in active coverage.

## Session Continuity

Last session: 2026-10-12T17:53:34.929Z
Stopped at: Completed 10-11-PLAN.md
Resume file: None
Next command in fresh context: `/gsd-execute-phase 10`

Completed workflow stage: **Phase 10 - CGB Profile, Banking and Register Visibility, planning** (2026-10-12) on branch `gsd/phase-10-cgb-profile-banking-and-register-visibility`. 10-RESEARCH.md (corrections C1-C13 to CONTEXT), 10-PATTERNS.md, 10-VALIDATION.md and plans 10-01..10-20 (one plan per wave, serial because every plan edits `tests/expected-tests.txt` and `tests/CMakeLists.txt`). Plan checker passed on iteration 2 (iteration 1: split the 15-file Mooneye CGB plan and the over-budget visibility plan, D-27 test prefixes, PATTERNS analog references). Coverage gates: CGB-01..03 covered, decisions 29/29. Research open questions auto-resolved per the owner's standing instruction: `gbb_create` accepts CGB in 10-06; IE bits 5-7 stored on CGB only (new owner veto item 6); CGB post-boot IF/audio cells for `boot_hwio-C`; shared GATE-00 tag; deferred writes stop through a latch. Owner veto window (before the phase PR merges): `gbb_info` ABI, PGB rejection, `gbb_copy_frame` error on CGB, DMG FF4C-FF7F unchanged, +5% bench review trigger, CGB IE bits 5-7. Execution preconditions: network for the pinned RGBDS 1.0.1 archive (10-13) and Mooneye/WLA-DX sources (10-14), gh access and exact-head CI (10-20). Next step: **Phase 10 execution** via **`/gsd-execute-phase 10`**. Both auto-advance flags stay false; nothing advances automatically.

Completed workflow stage: **Phase 10 - CGB Profile, Banking and Register Visibility, discussion** (2026-10-12) on branch `gsd/phase-10-cgb-profile-banking-and-register-visibility`. [10-CONTEXT.md](phases/GB-10-cgb-profile-banking-and-register-visibility/10-CONTEXT.md) locks D-01..D-29 from five parallel advisor researches (profile API, post-boot/visibility/model-gate audit, banking/DMA, half-dot ADR/benchmark, gap sweep) with adversarial passes, auto-followed per the owner's standing instruction. Key choices: sized `gbb_info` + `gbb_probe_rom`/`gbb_get_info`; PGB headers rejected on CGB with appended `GBB_UNSUPPORTED_EXECUTION_MODE`; C post-boot and visibility tables with per-cell provenance mirrored in docs and diff-tested; CI-enforced model-gate scanner; DMG FF4C-FF7F stays fail-closed (byte-identical); unbuilt CGB registers fail closed as `DEFERRED(n)`; `vram[2][8192]`/`wram[8][4096]` with DMG pinned to bank 1; ADR D-070 (half-dot single clock) with static asserts; advisory interleaved A/B benchmark. Owner veto window (before the phase PR merges): `gbb_info` ABI, PGB rejection, `gbb_copy_frame` error on CGB, DMG FF4C-FF7F unchanged, +5% bench review trigger. Next step: **Phase 10 research and planning** via **`/gsd-plan-phase 10`**. Both auto-advance flags stay false; nothing advances automatically.

Execute-phase tail (2026-10-12): code review 09-REVIEW.md (WR-01/WR-02/IN-01/IN-02 fixed in 8896725, fc85d8c, 19deb6b, 2863aae; IN-03 skipped), Nyquist validation `validated`/compliant, security 09-SECURITY.md `threats_open: 0` (T-09-34 closed by the `mbc3_rtc_evidence_ledger_names` check, 9bc23db), regression gate 404/404 CTest with installed inventory plus the player gate, and gsd-verifier `passed` (09-VERIFICATION.md, 5/5 criteria, 6/6 requirements). Phase 9 is marked complete in ROADMAP.md. PR #65 remains open, ready and unmerged; the squash merge waits for `/gsd-verify-work 9` and exact-head green CI on the final branch head.

Completed workflow stage: **Phase 9 - MBC3, Deterministic RTC and Cartridge Persistence, execution** (2026-10-12), plans 09-01..09-18 on branch `gsd/phase-09-mbc3-deterministic-rtc-and-cartridge-persistence`. Evidence head `04c77596c375a8b186da54c2f7b253c3ef2fcdab`, run 38191589574 (https://github.com/szTheory/gabbaboy/actions/runs/38191589574): all eight required jobs success; fixture-repro run 38191589599 (https://github.com/szTheory/gabbaboy/actions/runs/38191589599): fixture-repro, mooneye-original-repro, mooneye-candidate-repro, mooneye-mbc-repro, magentests-repro and rtc3test-repro success, with `result=byte-identical` for MagenTests and rtc3test. Local ctest 401/401, `baseline status=pass`, digest `4c7a57ff3d50d228` held, privacy check clean. The docs-only handoff commit is checked as a separate head (see 09-18-SUMMARY). PR #65 is ready for review and is not merged; the pre-authorized squash merge happens only after Phase 9 verification passes at an exact-head green head. The owner may still veto the signed `gbb_rtc_catch_up` prototype (D-14) and the 21-byte RTC block in the battery image (D-15, D-17) before merge. Limitations: no physical MBC3/RTC observation, no CGB, no BGB/VBA-M footer interop, paused time not recovered. Next step: **Phase 9 verification**. Next command in fresh context: **`/gsd-verify-work 9`**. Following phase (named, not started; only after verification passes and the owner chooses to continue): **Phase 10 - CGB Profile, Banking and Register Visibility**. Gap closure, if needed, continues on this branch and PR. Both `workflow.auto_advance` and `workflow._auto_chain_active` stay false; nothing advances automatically.

Completed workflow stage: **Phase 9 - MBC3, Deterministic RTC and Cartridge Persistence, planning** (2026-10-11) on branch `gsd/phase-09-discuss`. Research, pattern map, validation strategy and 18 plans in 8 waves:
- wave 1: 09-01 MBC3 mapper tracer and MBC30 rejection; 09-02 MagenTests admission; 09-03 fuzz 8 MiB mode; 09-04 v0.1 save corpus from tag v0.1.2; 09-05/09-06 MBC3+RTC and MBC2 continuation guests;
- wave 2: 09-07 MagenTests oracle and install exclusion; 09-08 rtc3test admission (ROM plus digest-pinned upstream tests.md);
- wave 3: 09-09 lazy RTC, original RTC tests, no-host-clock check, phase branch and draft PR; 09-10 MBC5 guest and fixture-repro;
- wave 4: 09-11 battery image with RTC block, `gbb_rtc_catch_up`, `GBB_NO_RTC`, `catch_up_policy_table`;
- wave 5: 09-12 rtc3test oracle checked against tests.md; 09-13 player envelope v2 and WR-02; 09-14 installed consumers;
- wave 6: 09-15 loader matrix and RTC mutation controls; 09-16 catch-up on reopen and fresh-process continuation;
- wave 7: 09-17 evidence ledger and docs; wave 8: 09-18 gates, PR ready (not merged), handoff.

Plan checker: 3 passes (2 blockers and 3 warnings, then 1 warning, then INFO only); requirements 6/6, decisions 28/28, post-planning gap analysis 34/34. Planning deviation: the cross-OS policy test is registered as core `catch_up_policy_table`, not in the player inventory (D-26 placement). The phase branch is created from the HEAD of `gsd/phase-09-discuss`. The owner may still veto the signed catch-up prototype and the unified battery image (D-14, D-15, D-17) before the PR merges. Phase 9 is not executed. Next phase step: **Phase 9 execution** via **`/gsd-execute-phase 9`**. Both auto-advance flags stay false; nothing advances automatically.

Completed workflow stage: **Phase 9 - MBC3, Deterministic RTC and Cartridge Persistence, discussion** (2026-10-11) on branch `gsd/phase-09-discuss`. [09-CONTEXT.md](phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-CONTEXT.md) locks D-01..D-28 from four parallel advisor researches with adversarial passes, auto-followed per the owner's standing instruction. The RTC model was prototyped in scratch and passed rtc3test v004 23/23. Key choices:
- lazy RTC anchored on `time_half_dots`, with the latch not bumping the battery generation;
- `gbb_rtc_catch_up(instance, int64_t)`: negative values rejected, O(1) modular add, new `GBB_NO_RTC`;
- unified battery image of RAM plus a 21-byte versioned LE RTC block; import never advances the RTC;
- MBC30 rejected with `UNSUPPORTED_CARTRIDGE_VARIANT`;
- player envelope v1 kept byte-identical for MBC1 and v2 for every other battery type, with `saved_at` and no advance on clock rollback;
- WR-02 closed by deriving player classification from the core;
- MagenTests and rtc3test admitted with negative controls;
- two-layer no-host-clock CTest.

The signed catch-up prototype (D-14, D-17) is the one public-API choice the owner may veto before the phase PR merges. Next step: **Phase 9 research and planning** via **`/gsd-plan-phase 9`**. Both auto-advance flags stay false; nothing advances automatically.
Completed workflow stage: **Phase 8 - Cartridge Seam, MBC5 and MBC2, execution and verification** (2026-10-11). Verification passed 4/4 (CART-01..03) in [08-VERIFICATION.md](phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-VERIFICATION.md); gates: Nyquist validated (V-01..V-27 green, differential rerun 0 differences), security 41/41 closed, code review 5 findings (WR-01 and IN-01 fixed in 1620c99, 47a1d4c, a57879c and e85c1b3, WR-02 deferred to Phase 9, 2 info skipped, 0 open), regression core 320/320 and player 371/371. PR #64 is squash-merged to main after exact-head required checks pass. Limitations: `rom_64Mb` does not exercise banks >= 256 (ninth bit proven by `mbc5_bank_1ff` and the mutant pair, D-062); the player status line has no automated UI test; player persistence is MBC1 only; rumble is a query without haptics; no CGB and no hardware MBC observation. Next phase: **Phase 9 - MBC3, Deterministic RTC and Cartridge Persistence** (no CONTEXT.md yet) via **`/gsd-discuss-phase 9`**. Both auto-advance flags (`workflow.auto_advance`, `workflow._auto_chain_active`) stay false; nothing advances automatically.
Completed workflow stage: **Phase 8 - Cartridge Seam, MBC5 and MBC2, execution** (2026-10-11), plans 08-01..08-10 on branch `gsd/phase-08-cartridge-seam-mbc5-and-mbc2`. Evidence head `a3f27f71c10838e372f27d8c2fcf0070123b0919`, run 38155767928 (https://github.com/szTheory/gabbaboy/actions/runs/38155767928): all eight required jobs success; fixture-repro run 38155768038 (https://github.com/szTheory/gabbaboy/actions/runs/38155768038): fixture-repro, mooneye-original-repro, mooneye-candidate-repro and mooneye-mbc-repro success. Local ctest 319/319, `baseline status=pass`, privacy check clean. The docs-only handoff commit is checked as a separate head (see 08-10-SUMMARY). PR #64 is ready for review and left OPEN and unmerged: the pre-authorized squash merge happens only after Phase 8 verification passes, at an exact-head green head. Honest limits: rom_64Mb does not exercise banks >= 256 (the ninth bit is covered by mbc5_bank_1ff and the two mutant CTests, D-29 amended, DECISIONS D-062); the 08-04 player status line has no automated UI test; phase1-asan cannot configure on macOS, so sanitizer evidence is hosted linux-asan-ubsan plus manual local builds; no hardware MBC observation, no CGB, player persistence MBC1 only, rumble is a query without haptics. Next step: **Phase 8 verification**, `/gsd-verify-work 8`. If verification finds gaps, gap closure continues on this branch and PR. Following phase: **Phase 9 - MBC3, Deterministic RTC and Cartridge Persistence** (named, not started; only after verification passes and the owner chooses to continue). Both `workflow.auto_advance` and `workflow._auto_chain_active` stay false.

Completed workflow stage: **Phase 8 - Cartridge Seam, MBC5 and MBC2, plan 08-08 (original MBC5 banking fixture and D-29 ninth-bit mutant) executed** (2026-10-11) on branch `gsd/phase-08-cartridge-seam-mbc5-and-mbc2`. fixtures/mbc5-banking (RGBDS 1.0.1, sha256 0b852837...ddffef, 64 KiB, type $1E) passes mbc5_banking_guest (rumble on=1, 1 transition), mbc5_banking_guest_1b and mbc5_bank_1ff (in-memory 8 MiB); the ninth-bit mutant fails mbc5_bank_1ff at C005 and its control passes. Full local ctest 319/319, inventory matches. Hosted fixture-repro step and exact-head CI are not yet read (08-09/08-10). Phase 8 is not complete: plans 08-09 and 08-10 remain. Next plan: **08-09 (docs and decisions)** via **`/gsd-execute-phase 8`**. Both auto-advance flags stay false.
Completed workflow stage: **Phase 8 - Cartridge Seam, MBC5 and MBC2, plan 08-02 (MBC2) executed** (2026-10-11) on branch `gsd/phase-08-cartridge-seam-mbc5-and-mbc2`. 11 mbc2_ CTests added, full local ctest 272/272, differential `--exclude-types 05,06` `differences=0`, baseline pass. Phase 8 is not complete: plans 08-03..08-10 remain. Next plan: **08-03 (MBC5)** via **`/gsd-execute-phase 8`**. Both auto-advance flags stay false.
Completed workflow stage: **Phase 8 - Cartridge Seam, MBC5 and MBC2, plan 08-01 (cartridge seam) executed** (2026-10-11) on branch `gsd/phase-08-cartridge-seam-mbc5-and-mbc2`. Differential `cells=86016 differences=0`, digest `4c7a57ff3d50d228` held, exact-head CI green on all eight required jobs at 25e5d6e (run 38146578485), draft PR #64 open and not merged. Phase 8 is not complete: plans 08-02..08-10 remain. Next plan: **08-02 (MBC2)** via **`/gsd-execute-phase 8`** (resumes at the first plan without a SUMMARY). Both auto-advance flags stay false.

Completed workflow stage: **Phase 8 - Cartridge Seam, MBC5 and MBC2, planning** (2026-10-11) on branch `gsd/phase-08-cartridge-seam-mbc5-and-mbc2`. Research, pattern map, validation strategy and 10 plans in 9 waves: 08-01 seam (`gabbaboy.c` only, old-versus-new differential, draft PR); 08-02 MBC2; 08-03 MBC5 + 8 MiB bound + `gbb_rumble_state`; 08-04 player non-persistence and 08-05 Mooneye-mbc admission + runner in parallel; 08-06 sibling verifier and controls; 08-07 install/package scans, ninth-bit mutant, hosted leg; 08-08 original MBC5 banking fixture; 08-09 docs and decisions; 08-10 gates, PR ready and left open. Plan checker: 5 passes, final pass clean; requirements 3/3, decisions 34/34. D-08 amended at planning (sequencing only: MBC2 plan before MBC5 because both edit the same core, header and test inventory files). Phase 8 is not executed. Next phase step: **Phase 8 execution** via **`/gsd-execute-phase 8`**. Both auto-advance flags stay false; nothing advances automatically.

Completed workflow stage: **Phase 8 - Cartridge Seam, MBC5 and MBC2, discussion** (2026-10-11) on branch `gsd/phase-08-cartridge-seam-mbc5-and-mbc2`. [08-CONTEXT.md](phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-CONTEXT.md) locks D-01..D-34 from four parallel advisor researches with adversarial passes, auto-followed per the owner's standing instruction; no owner-only questions arose. Key choices: in-file cartridge seam landing first as a pure `gabbaboy.c` plan with a recorded old-versus-new differential; 8 MiB ceiling for MBC5 only, preserving every other loader return code; `gbb_rumble_state` + `GBB_NO_RUMBLE`; canonical MBC2 nibble image; player runs MBC2/MBC5 battery carts without persistence and says so (CART-06 stays Phase 9); Mooneye mbc2/mbc5 derivatives in sibling `fixtures/mooneye-mbc/` with proven install exclusion. Next step: **Phase 8 research and planning** via **`/gsd-plan-phase 8`**. Both auto-advance flags stay false; nothing advances automatically.
Continuation note: [.continue-here.md](.continue-here.md)
Completed workflow stage: **Phase 7 - DMG Game Acceptance and Regression Baseline, execution and verification** (2026-10-11). Verification passed 5/5 (GAME-01..03, EVID-01..02) in [07-VERIFICATION.md](phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-VERIFICATION.md); gates: Nyquist validated, security 49/49 closed, code review 10 findings (8 fixed, WR-01 deferred as a documented limitation, 2 info skipped, 0 open), local regression 261/261. Owner ratified D-029 on 2026-10-11. PR #63 is squash-merged to main after exact-head required checks pass. Limitations: one game on one software model, packaged-player smoke macOS only, no hardware evidence, `libbet-repro` not yet run hosted (Linux path unverified), no CTest for `frame-digest@t`. Next phase: **Phase 8 - Cartridge Seam, MBC5 and MBC2** (no CONTEXT.md yet) via **`/gsd-discuss-phase 8`**. Both auto-advance flags (`workflow.auto_advance`, `workflow._auto_chain_active`) stay false; nothing advances automatically.
Completed workflow stage: **Phase 7 - DMG Game Acceptance and Regression Baseline, execution** (2026-10-11), plans 07-01..07-17 on branch `gsd/phase-07-dmg-game-acceptance-and-regression-baseline`. Evidence head 23c0ffd7c1ab3149be1b96c8ba384acf5c655c48, run 38106136572 (https://github.com/szTheory/gabbaboy/actions/runs/38106136572): all eight required jobs success. The handoff commits that follow the evidence head change only planning files and are checked as separate heads (see the 07-16 SUMMARY), so the evidence head is not the final branch head. PR #63 is marked ready for review and is not merged. Open owner item: D-029 (shade-count relaxation of locked D-25) is pending owner confirmation. Next step: **Phase 7 verification**. Next command in fresh context: `/gsd-verify-work 7`. Following phase: **Phase 8 - Cartridge Seam, MBC5 and MBC2** (named, not started; only after verification passes and the owner chooses to continue). Both auto-advance flags (`workflow.auto_advance`, `workflow._auto_chain_active`) stay false; nothing advances automatically.
Completed workflow stage: **Phase 7 planning** (2026-10-10) on branch `gsd/phase-07-dmg-game-acceptance-and-regression-baseline`. Research, pattern map, validation strategy and 17 plans in 13 waves (07-01 Libbet admission; 07-02/03/04 shared acceptance library, mixer investigation, opt-in repro in parallel; 07-17 early-Start-tap investigation; runner, digests, applicability, LD B,B, controls, calibration; 07-12/13 player smoke and baseline comparator in parallel; 07-15 baseline freeze; 07-16 docs, PR ready and handoff). Plan checker: 6 passes; 0 blockers remaining; requirements 5/5, decisions 38/38. Owner decisions recorded in `07-CONTEXT.md`: D-14 clarification (controls assert the raw exit 1 and, for N1/N2, the separate strict-xfail mapping) and D-18 amendment (64 KiB caps the text report; one 69,135-byte PPM per failing case). Phase 7 is not executed. Next phase step: **Phase 7 execution** via **`/gsd-execute-phase 7`**. Both auto-advance settings stay false; nothing advances automatically.
Completed workflow stage: **Phase 7 context gathering** (2026-10-10). `07-CONTEXT.md` locks 38 decisions (D-01..D-38) from four parallel multi-lens/adversarial advisor researches: vendored digest-pinned Libbet v0.08 (commit 46a765a) with an opt-in RGBDS 0.7.0 rebuild workflow that must match the vendored bytes; G5 fail-closed manifest checklist; guest-state predicate (tutorial floor fully scored, not attract mode) with no-input, wrong-input, drop-START and mutant-core controls; `gbinput 1` master-timeline script; hybrid runner (`tests/acceptance/cases.txt`, compiled Mooneye table unchanged); canonical `GBB-RGB888-v1` digest; text baseline ledger `tests/baseline/dmg-cpu-b-v1.txt` with monotonic inventory and an approved-change log; macOS packaged-player `--input-script` smoke. Phase 7 is not planned or executed. Next phase step: **Phase 7 planning** via **`/gsd-plan-phase 7`**. Both auto-advance settings stay false; nothing advances automatically.

Completed workflow stage: **v0.2 milestone definition — roadmap creation** (2026-10-10). This is initialization, not Phase 7. ROADMAP.md adds the `## v0.2 Color & Cartridge Breadth` section with Phases 7–15; REQUIREMENTS.md traceability maps 28/28 requirements. Next phase: **Phase 7 — DMG Game Acceptance and Regression Baseline**, via **`/gsd-discuss-phase 7`**. Both `workflow.auto_advance` and `workflow._auto_chain_active` stay false; stop after every phase and wait for the owner. No phase is active; nothing advances automatically.

Completed workflow stage: **v0.1 milestone completion** (2026-10-10) — `verified_closeout`: 7/7 phases passed, 35/35 requirements, audit `passed`, 0 open artifacts (the Phase 5 `-Wunsequenced` item was confirmed fixed and marked resolved). ROADMAP, REQUIREMENTS, audit, phase directories and quick tasks are archived under [milestones/](milestones/); `REQUIREMENTS.md` was removed for the next milestone; tag `v0.1` marks the close. Next stage: **new milestone definition** (GB/GBC breadth direction) via `/gsd-new-milestone`. No phase is active; nothing advances automatically.

Completed workflow stage: **v0.1 milestone re-audit** (2026-10-10) — `passed`, 35/35 requirements, 7/7 phases, 12/12 integration, 5/5 flows, 0 blockers. Next step: the owner completes the milestone with `$gsd-complete-milestone v0.1`. No auto-advance.

Completed workflow stage: **Phase 06.1 — Address v0.1 tech debt: CI workflow info items and audio consumer coverage, execution and verification** (2026-10-10). Verification passed 4/4; Nyquist, security (32/32 closed), UI (not applicable), code review (3 info deferred), regression (184/184) gates run; all seven phases read passed. Next step: the owner re-runs the milestone audit with `$gsd-audit-milestone v0.1`. No auto-advance.

Completed workflow stage: **Phase 2 — DMG CPU, Bus and Time verification freshness refresh** (2026-10-10). Canonical verification passed 5/5 truths and CPU-01–05 at `a9050df` on `gsd/phase-02-verification-refresh-2`. Gates: Nyquist 0 gaps, security 45/45 closed, code review 1 info deferred with 0 open dispositions, regression 179/179 core. No hosted-CI, physical-hardware or perceptual result is claimed.

Completed workflow stage: **v0.1 milestone audit** (2026-10-10) — `tech_debt`, 35/35 requirements, 0 blockers.

Completed workflow stage: **Phase 06.1 context gathering** (2026-10-10) on branch `gsd/phase-06.1-address-v0-1-tech-debt-ci-workflow-info-items-and-audio-cons` (11 locked decisions in `06.1-CONTEXT.md`: fix all 7 info items, C/C++ installed-consumer audio smoke on Windows/Linux/macOS, newest-run exact-head gate script, code PR then docs-only refresh PR). Next: **`$gsd-plan-phase 06.1`** (research first); after Phase 06.1 verifies, re-run `$gsd-audit-milestone v0.1` and then `$gsd-complete-milestone v0.1`.

Completed workflow stage: **Phase 06.1 planning** (2026-10-10) on branch `gsd/phase-06.1-address-v0-1-tech-debt-ci-workflow-info-items-and-audio-cons`. Research, pattern map, validation strategy and 8 plans in 6 waves (wave 1: plans 01–03 in parallel; then 04 PR 1 batched workflow commit + exact-head merge; 05–07 verification refreshes of Phases 1–6; 08 disposition, docs-only PR 2, freshness confirmation). Plan checker: 3 iterations plus one narrow guidance pass, 0 blockers remaining; decision coverage 11/11. Research corrections: Windows lane is MinGW-w64 (no MSVC claim); P2 IN-01 gets a single `player-gate` definition with a `check-player-result.sh` self-test. Next: **Phase 06.1 execution** — `$gsd-execute-phase 06.1`. Phase 06.1 is not executed; nothing advances automatically.

## Operator Next Steps

- Phase 9 (MBC3, Deterministic RTC and Cartridge Persistence) is executed and verified (`/gsd-verify-work 9` passed, 14/14 automated). PR #65 squash-merges at its exact-head green head.
- The owner chooses when to start Phase 10 - CGB Profile, Banking and Register Visibility: `/gsd-discuss-phase 10`.
- Phase-stop rule: stop after each phase and yield; never auto-advance into the next phase or milestone.
