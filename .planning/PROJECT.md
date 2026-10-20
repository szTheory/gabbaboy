# GabbaBoy

## What This Is

GabbaBoy is an original, portable C17 emulator core for Game Boy (DMG) and Game Boy Color (CGB), with an integration path for Playstead and other frontends. It runs a bootless DMG preview and model-qualified CGB software with colour, double-speed switching and general/HBlank VRAM DMA through the same bounded public API that external consumers use. MBC1/2/3/5 cartridges, deterministic RTC, scoped four-channel audio and safe battery continuation are implemented. An optional SDL3 macOS player ships with it. Broad game compatibility, physical hardware qualification, further timing qualification and save states remain future work.

## Current State

**Phase 15 execution is paused by the owner at 4/10 plans complete** (15-01/02/03/05). Public evidence scope, current support ledger, relocated native consumers and paired performance are implemented. The hosted native/floor jobs and 1133 sanitizer tests pass at a175a394; the real fuzz campaign hit a DMG/CGB test-harness applicability assertion and remains incomplete. The owner requested emulator/product progress rather than further security-oriented work: next 15-04 then 15-07, with the campaign parked. Resume with `/gsd-resume-work`; underlying phase command `/gsd-execute-phase 15`. Read [the checkpoint](phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/.continue-here.md). No merge, release publication or phase completion is claimed; both auto flags remain false.

**Phase 14 is a completed prerequisite:** [14-UAT.md](phases/GB-14-cgb-e-model-qualification-and-corpus/14-UAT.md) closes 49 deliverables and 13 bounded commit windows with zero human checkpoints; [goal verification](phases/GB-14-cgb-e-model-qualification-and-corpus/14-VERIFICATION.md) passes 41/41 and CGB-08/CGB-10 are complete. PR #71 merged at `c771b1b9c143d7589f8bb40c163c2e9f89ca1168`. Reuse its source-qualified receipts and completed UAT. The software corpus contains 107 cases, 25 actual passes and 82 matched expected failures. Physical CGB-E remains UNKNOWN/POLICY; analog/perceptual output and general game compatibility remain unqualified.

**Phase 13 is a completed prerequisite:** execution 12/12, canonical goal verification 37/37, automated UAT 45/45 with zero human checkpoints, CGB-07 closed, and PR #69 merged at `261c660396db65712dabb5f65b3e81ee5b0a3453`. Reuse its source-qualified records and completed UAT rather than restarting them. Its 5/5 software-fixture denominator, physical CGB-E UNKNOWN/POLICY, optional CGB-C rights exclusion and D-06/Pan Docs discrepancy remain explicit.

- **Shipped:** v0.1 Limited DMG Preview (milestone closed 2026-10-10; release [`v0.1.0`](https://github.com/szTheory/gabbaboy/releases/tag/v0.1.0) published 2026-10-09). 7 phases, 64 plans, 35/35 requirements, audit `passed`.
- **Phase 7 (2026-10-11):** Libbet and the Magic Floor v0.08 passes headless acceptance on three OSes and in the macOS packaged player; the DMG baseline is frozen. One game on one software model; no hardware evidence.
- **Phase 8 (2026-10-11):** Cartridge behavior sits behind one type-table mapper seam with zero observed DMG change (old-versus-new differential, frozen baseline); MBC5 (9-bit banking, 8 MiB, rumble query) and MBC2 (built-in nibble RAM, 512-byte battery image) run in the core. Mooneye mbc2 7/7 and mbc5 8/8 pass. Player persistence is still MBC1 only; no hardware MBC observation.
- **Phase 9 (2026-10-11):** MBC3 (`$0F`-`$13`, 7-bit ROM banking, RAM banks 0-3; MBC30 rejected) runs with an RTC that advances only from emulated time (rtc3test v004 basic/range/sub-second pass; no host clock in `src/core`, proven by source and object scans). Hosts apply wall-clock time only through `gbb_rtc_catch_up(instance, int64_t)`; timer cartridges append a 21-byte versioned RTC block to the battery image. The macOS player persists MBC2/MBC3/MBC5 in a v2 envelope with `saved_at` and catch-up on reopen, and every v0.1 save loads unchanged. MagenTests OOB SRAM passes for MBC1/3/5. No physical RTC or cartridge observation.
- **Phase 10 (2026-10-12):** A caller can create the `GBB_PROFILE_CGB_CPU_E` profile, probe a ROM and read model and execution mode through a sized `gbb_info`; post-boot state is a provenance-labelled table per DMG/CGB/compat column. VRAM (2x8 KiB) and WRAM (8x4 KiB) are banked with echo and OAM DMA sources; FF00-FF7F visibility is a tested per-cell matrix, KEY0 is locked and unbuilt CGB registers fail closed. Every core function and model branch carries a scanned model tag. DMG output is byte-identical (frozen baseline), but the DMG path measured about +6-7% slower than the Phase 7 baseline on a loaded host (advisory; review trigger fired). No colour output, double speed or HDMA yet; CGB-mode post-boot cells are Pan Docs/SameBoy/policy, not hardware evidence.
- **Phase 11 (2026-10-13):** CGB software renders in colour through `gbb_copy_frame_rgb555`: palette RAM ports (auto-increment, mode-3 lockout), BG/window/OBJ attributes and the CGB priority rules resolve per dot, checked against an independent 6144-row truth table, original RGBDS fixtures and three MagenTests ROMs. DMG software on the CGB profile uses a fixed, original, documented compatibility palette a host can override (no boot-ROM table). The SDL3 player takes `--model auto|dmg|cgb` and presents colour, with a pinned CGB smoke in CI. DMG output stays byte-identical. AGE has no CGB colour ROM at its pinned commit (D-20); mode-3 pixel timing is Phase 14; no hardware or perceptual colour claim.
- **Phase 12 (2026-10-14):** KEY1 plus STOP switches CGB CPU, timer, serial and OAM DMA rates while PPU/APU/RTC remain on the master timeline. The persisted destination-speed stall is `0x20004` CPU T within the measured AGE window `[0x20004,0x20007]`; original and hostile guests, natural timer IRQ dispatch, output digests, mutation controls and partitioned runs exercise the behavior. Only AGE DIV (5/5) and STOP-prefetch (1/1) are passes; eleven other ROMs retain exact-signature expected-failure dispositions. CGB-06 goal verification passed 109/109 and the local core suite passed 898/898, with no DMG baseline change. PR #68 is merged at `8091fb591de7fb68e666be01d344f5f26ebedc5c`; no physical hardware qualification or local libFuzzer campaign is claimed.
- **Phase 13 (execution and goal verification complete):** Bounded GDMA/HBlank DMA, CPU stall/HALT interaction, cancel/readback, mapped source and bank policies, partition/resource controls, original and pinned fixtures, installed C/C++ consumers and player coverage pass the selected software contract. [13-VERIFICATION.md](phases/GB-13-cgb-hdma/13-VERIFICATION.md) passes 37/37; [13-BENCH.md](phases/GB-13-cgb-hdma/13-BENCH.md) records fresh local and exact-head hosted results, measured costs and artifact identities separately from history. Automated UAT passed 45/45 deliverables with zero human checkpoints; reuse the completed record unless covered behavior or evidence changes. No physical hardware or host-fuzzer campaign claim.
- **Code:** ~18k lines of C/C++ (about 7k in `src/` + `include/`); CMake/Ninja/CTest; 184 local CTest cases at the 06.1 regression run; required CI on Linux, macOS and Windows (MinGW-w64).
- **Evidence scope:** admitted corpus is three source-qualified derived Mooneye CPU/timer closures plus original project ROMs. No physical hardware, perceptual output, signing/notarization, or live Playstead integration is claimed.
- **Open:** No open issues or PRs at the v0.2 start (2026-10-10); releases `v0.1.0` and `v0.1.2` published. Accepted info-level debt is listed in the [v0.1 audit](milestones/v0.1-MILESTONE-AUDIT.md).

## Current Milestone: v0.2 Color & Cartridge Breadth

**Goal:** Play supported CGB software and the common MBC2/MBC3/MBC5 cartridge set (with deterministic RTC) through the same bounded core and player, after first proving one rights-clear game end to end on the existing DMG player.

**Target features:**
- One rights-clear game-level acceptance in the existing DMG player (guest-observable start/progress, meaningful input, visible/audio response) before any broadened claim.
- MBC5, MBC3 with deterministic host-independent RTC (and its battery persistence), and MBC2 with built-in RAM.
- A CGB silicon profile: CGB mode and DMG-compatibility mode, double-speed switching, VRAM/WRAM banking, BG/OBJ color palettes and attributes, general/HBlank HDMA, and model-specific CPU/PPU/APU differences under explicit model qualification.
- Updated support ledger, docs, release notes, and a qualified v0.2 release scoped to the tested corpus.

Deferred to v0.3 (States & Integration): transactional versioned save states (STATE-01) and a qualified Playstead adapter (INT-01), so serialization is designed once over the complete DMG+CGB machine state.

## Core Value

Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.

## Requirements

### Validated

- ✓ Portable C17 core and headless runner with an installable `GabbaBoy::core` export — Phase 1.
- ✓ Bounded opaque-instance API and original-ROM tracer with explicit fixture provenance and limited DMG-CPU-B claims — Phase 1.
- ✓ Relocated C and C++ consumers, required CI inventory, and revision-qualified Linux/macOS preview packages — Phase 1.
- ✓ Interactive optional SDL3 macOS DMG preview, original ROM-only demo, timed input/frame output, and explicit audio/persistence limits — Phase 3.
- ✓ Timed SM83 CPU, interrupts, HALT/STOP, timer and serial on a deterministic event timeline, qualified against a pinned CPU/timer corpus (CPU-01..05) — v0.1.
- ✓ Timed PPU, OAM DMA, VRAM/OAM restrictions and JOYP under the D-025 confidence-qualified model (VIDEO-01..05) — v0.1.
- ✓ MBC1 banking, bounded battery import/export, atomic player saves, and fresh-process continuation (SAVE-01..04) — v0.1.
- ✓ Scoped four-channel DMG APU, bounded 48 kHz PCM, paced SDL playback, and clean host input/device transitions (AUDIO-01..03, HOST-01..02) — v0.1.
- ✓ Qualified exact-tag release, support ledger, performance baselines, fuzzing, adopter docs, and exercised CI/release automation (SHIP-01..08) — v0.1.
- ✓ Rights-clear DMG game acceptance (Libbet v0.08, bootless DMG-CPU-B): headless run on Linux/macOS/Windows with guest-memory predicate, frame and PCM digests and failing controls; macOS packaged-player smoke; LD B,B frame digests, input replay and model applicability; frozen DMG baseline `tests/baseline/dmg-cpu-b-v1.txt` (GAME-01..03, EVID-01..02) — Phase 7.
- ✓ Cartridge mapper seam with no observable DMG change, MBC5 (incl. bank `$1FF`, rumble state query) and MBC2 (bit-8 register decode, canonical nibble RAM and battery image), Mooneye mbc2/mbc5 derivatives kept out of install and package artifacts (CART-01..03) — Phase 8.
- ✓ MBC3 with MBC30 rejection, loader contradiction matrix with no partial mutation and 8 MiB fuzz bound, MBC2/MBC3/MBC5 fresh-process player continuation with v0.1 saves unchanged, emulated-time RTC with explicit signed catch-up and a versioned battery block (CART-04..06, RTC-01..03) — Phase 9.
- ✓ CGB-CPU-E profile with probe/info API and execution mode, mode-specific post-boot state with provenance, model-tagged core and register visibility matrix with KEY0 lock, VRAM/WRAM banking with echo and OAM DMA sources; original banking fixture and Mooneye CGB derivatives; DMG baseline unchanged (CGB-01..03) — Phase 10.
- ✓ CGB colour rendering through `gbb_copy_frame_rgb555` (palette RAM, attributes, priority, truth table and original fixtures), documented overridable compatibility palette, and SDL3 player `--model auto|dmg|cgb` colour presentation with a CI smoke (CGB-04, CGB-05, CGB-09) — Phase 11.
- ✓ CGB KEY1/STOP double-speed switching, destination-speed stall, CPU/master clock-domain separation and switch/stall partition equivalence under the named software model (CGB-06) — Phase 12; two AGE pass cases and eleven explicit expected failures, with no hardware claim.

- ✓ General-purpose and HBlank VRAM DMA with bounded CPU stalls, cancellation/HDMA5 readback, HALT interaction, partition equivalence, mapped bank policies and qualified fixture/consumer evidence (CGB-07) — Phase 13, goal verification 37/37; physical CGB-E remains UNKNOWN/POLICY.

- ✓ CGB-E digital PCM/I/O behavior and a pinned headless corpus with independent denominators (CGB-08, CGB-10) — Phase 14, goal verification 41/41; 107 complete cases, 25 actual passes and 82 matched expected failures. Physical CGB-E remains UNKNOWN/POLICY.

### Active

v0.2 Color & Cartridge Breadth (scoped in [REQUIREMENTS.md](REQUIREMENTS.md)):

- [ ] CGB acceptance or explicit absence, current support ledger/docs/consumers, and an exact-tag qualified v0.2.0 release (CGB-11, SHIP-09, SHIP-10, SHIP-11, Phase 15).

Next (v0.3, provisional): transactional versioned native save states (STATE-01) and a qualified Playstead adapter (INT-01).

Ongoing project principles: dependency-light C API with explicit contracts; headless core independent of the player; reproducible tests, sanitizers, fuzzing, and baselines; tested artifacts through PR and release automation; source-linked decisions, current docs, and transferable lessons.

### Out of Scope

- NES, Neo Geo, and GBA execution — distinct hardware belongs in distinct projects.
- Proprietary game or boot ROM distribution — public automation needs permissioned fixtures.
- A game library manager, accounts, online services, or mandatory telemetry — frontend concerns outside the core.
- Universal compatibility, unmeasured “fastest” claims, or instruction-test pass rates presented as game compatibility.
- JIT, plugin frameworks, a generic multi-console bus, and broad scripting before demonstrated need.
- SGB/SGB2, additional silicon revisions, uncommon cartridge peripherals, link accessories, rewind/runahead, and web/mobile ports in the first milestone — retain as revisable future scope.

## Context

- The founding brief is [BRIEF.md](context/BRIEF.md). Detailed evidence and tradeoffs live in [research/](research).
- Sibling emulators are developing concurrently. Recent fixes and experiments in GlueyNeo, Nesturbator, and Playstead are useful precedent, with evidence strength recorded separately from intentions.
- Playstead is an intended consumer, not a prerequisite for first gameplay. An optional SDL player allows direct macOS use and exercises the same public API as external consumers.
- Mature OSS delivery practices from lattice_stripe and ExifCleaner inform CI and release design when still relevant to this C library.
- SameBoy, mGBA, hardware research, and test authors are comparison and evidence sources. Oracle agreement alone does not establish hardware correctness.
- Prefer small vertical demonstrations over completing entire subsystems in isolation. Each demonstration must preserve a path to correct timing.

## Constraints

- **Scope:** Game Boy and Game Boy Color. DMG first as a vertical slice; CGB remains a named near-term milestone, with timing/API choices accommodating it from the start.
- **Implementation:** Portable C17 is the initial recommendation; CMake/Ninja/CTest; keep SDL and platform code outside the core.
- **Correctness:** Explicit device time, hardware model, deterministic inputs, RTC policy, and ordering at observable boundaries. Host clocks and filesystem I/O belong in adapters.
- **Security:** Treat ROMs, battery files, save states, and frontend arguments as untrusted. Bound lengths, work, allocation, and diagnostics.
- **Performance:** Measure emulated work and correctness together. Optimize profiled bottlenecks; no accuracy shortcuts hidden behind benchmarks.
- **Public distribution:** MIT recommended; audit each imported source/fixture and retain its notices. Do not publish personal paths, identities, credentials, private ROM collections, or unlicensed assets.
- **Workflow:** OpenGSD; recommendations can be adopted without repeated approval. Stop after each phase and before beginning the next milestone unless explicitly directed otherwise.
- **Verification:** Automate repeatable acceptance, including packaged artifacts and downstream consumers. A workflow pause does not require routine manual UAT.
- **Shipping:** PRs and required green checks before merging. Automate releases within the authorized phase. Local bootstrap may precede a remote; remote hosting setup is a Phase 1 deliverable.

## Key Decisions

| Decision | Rationale | Outcome |
|---|---|---|
| GB/DMG + GBC/CGB target | Explicit current request supersedes copied console names | Adopted scope |
| Original core in portable C17 | Embedding, educational readability, host coverage | ✓ Good — v0.1 shipped on Linux/macOS/Windows consumers |
| Thin optional SDL3 player | Early macOS gameplay while exercising public API | ✓ Good — player stayed optional; core export has no SDL dependency |
| Native C API first, libretro later | Precise ownership and deterministic semantics without frontend coupling | ✓ Good for v0.1; libretro still pending demonstrated value |
| Explicit profiles for hardware revisions | Avoid accidental DMG/CGB hybrid behavior | Adopted principle; choose exact baseline revisions in phase planning |
| MIT for original contributions | Simple permissive reuse | ✓ Adopted; per-asset rights recorded for every fixture |
| Automated work inside phases, explicit phase stops | High velocity and owner review/model choice coexist | Required |
| Inherit the session model | User can change model between phases without stale hardcoded model IDs | Adopted configuration |
| PR-based phase branches | Keep main releasable and retain review/verification evidence | Adopted configuration |
| Corpus-qualified claims and measurements | A passing subset is not universal hardware/game compatibility | Required |
| Bootless DMG-CPU-B tracer as the first delivered slice | A real guest path validates the portable API and install flow while keeping hardware, gameplay, and CGB claims bounded | Verified in Phase 1; memory-map conformance continues in Phase 2 |
| Confidence-qualified software models for documented but revision-sensitive behavior | Select a deterministic model from primary documentation and reverse-engineering sources, cross-check implementations, and state the remaining silicon uncertainty | ✓ Good — D-025 unblocked VIDEO-02/03; ⚠️ Revisit if hardware measurements become available |
| Exact-head required CI gate before merge | Local passes and stale runs had masked remote state | ✓ Good — enforced through 06.1; info-level script items deferred |
| Freeze a DMG baseline before any v0.2 core change | Later mapper and CGB phases must prove DMG-CPU-B output unchanged, or record an approved change | Adopted in Phase 7 — one ledger, no update mode, reverse-apply change log |
| Game acceptance gate is guest memory, digests are regression-only | Emulator-captured frame/audio digests are not hardware evidence; a guest-state predicate with failing controls is the claim | ✓ Good — Phase 7 (D-26, D-029 ratified 2026-10-11) |
| In-file type-table mapper seam before new mappers | One `switch` on a stored cartridge kind keeps the hot path direct; landing it alone with an old-versus-new differential proves no DMG change before MBC5/MBC2 | ✓ Good — Phase 8 (differential 0 differences; D-062 moved the ninth-bit proof to bank `$1FF`) |
| RTC advances only from emulated time; wall-clock catch-up is an explicit host call | Replays must not depend on the machine running them; import never advances the clock, so a host cannot apply time twice by accident | ✓ Good — Phase 9 (rtc3test pass, no-host-clock source and object proof; owner may still veto signed `int64_t` D-14 and the appended block D-15/D-17 before merge) |
| Persist the CGB speed-switch stall in destination-speed CPU T | Device work must continue during the switch pause and survive run partitions | Verified in Phase 12 at `0x20004`, with measured window and explicit model uncertainty (D-084) |
| Preserve measured oracle failures as exact-signature dispositions | A two-case pass cannot substantiate all admitted AGE behavior | Verified in Phase 12: DIV/STOP-prefetch pass, eleven qualified expected failures; M28 mode-0 sensitivity retained |
| Insert a debt-closure phase before closing a milestone | The first audit returned `tech_debt`; closing it first gave a clean `passed` re-audit | ✓ Good — Phase 06.1 |

## Evolution

At each phase boundary, update delivered requirements, evidence, limitations, decisions, docs, performance/correctness baseline changes, open issue/PR triage, and the next recommended action. Stop before the next phase.

At each milestone boundary, audit this document and the active requirements, summarize compatibility by tested model/corpus, refresh the near/mid/long-term roadmap, and prepare a concise lesson transfer for sibling emulator projects. Keep unverified external advice separate until reproduced locally.

---
Last updated: 2026-10-16 after Phase 15 planning; /gsd-execute-phase 15 is next.
