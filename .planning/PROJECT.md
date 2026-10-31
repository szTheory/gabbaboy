# GabbaBoy

## What This Is

GabbaBoy is an original, portable C17 emulator core for Game Boy (DMG) and Game Boy Color (CGB), with an integration path for Playstead and other frontends. It runs a bootless DMG preview and model-qualified CGB software with colour, double-speed switching and general/HBlank VRAM DMA through the same bounded public API that external consumers use. MBC1/2/3/5 cartridges, deterministic RTC, scoped four-channel audio and safe battery continuation are implemented. An optional SDL3 macOS player ships with it. Exact-continuation native save states, player save slots and the POSIX host-process runner contract ship in v0.3.0. Broad game compatibility, physical hardware qualification, further timing qualification and live Playstead integration remain future work.

## Current State

**Shipped and archived: [v0.3.0](https://github.com/szTheory/gabbaboy/releases/tag/v0.3.0), Save States & Host Contract.** Four phases and 35 plans satisfy all 17 requirements. The [milestone audit](milestones/v0.3-MILESTONE-AUDIT.md) remains `tech_debt`; the owner accepted a documented closeout override for three stale historical phase projections and retained nonblocking debt, including the standalone closeout helper failure. See [closeout](milestones/v0.3-CLOSEOUT.md).

The release adds bounded transactional native save/load with exact continuation, numbered player slots and the POSIX raw-save/SIGTERM/exit-code host contract. It remains a bootless software preview for tested DMG-CPU-B and CGB-CPU-E modes/corpus. Physical hardware, perceptual output, general compatibility, cross-emulator save interoperability and live Playstead integration are unqualified; packages are unsigned and not notarized.

The final implementation-head audit passed its full suite without failures/skips; boundary main CI and all 22 published asset identities/digests reconciled. These are source-bound observations, not a claim that archival itself reran hosted release producers. Original failed release attempts and boundary verification reports remain unchanged.

## Next Milestone Goals

**Proposed v0.4 — Evidence Floor**, not started: first CGB game-level evidence or a justified absence, rights-cleared font-substituted acid2 derivatives, and gbmicrotest admission. Fixture rights and game selection remain kickoff decisions. Use `/gsd-new-milestone` when the owner chooses; fresh requirements and numbered phases will be defined there. No Phase 20 exists yet. Both automatic-advance flags remain false.

<details>
<summary>Completed v0.3 scope and kickoff context</summary>

## Completed Milestone: v0.3 Save States & Host Contract

**Goal:** Add exact-continuation native save states to the core and player, and make the runner safe to drive as a host process, after first paying down the v0.2 delivery debt.

**Delivered features:**
- **Tune-up (first):** move test-consumed helpers out of phase directories, then archive the v0.2 phase records; wire the Phase 8 verifiers; close superseded PRs #78–92; attribute the DMG slowdown and gate it cumulatively against `v0.2.0`; CI hygiene; ship v0.2.1 from PR #75 once its blockers clear.
- **STATE-01 save states:** transactional, versioned (same-version only before 1.0), explicit portable serialization of the complete DMG+CGB machine, including in-flight state, with exact continuation equivalence.
- **Player save slots** over the public state API.
- **INT-01a host contract:** a `--rom`/`--save-dir` runner mode with an atomic raw `.sav`, save-and-exit 0 on SIGTERM, an exit-code table and GabbaBoy-declared save-format ids.
- **Release v0.3.0**, with the exact-tag rehearsal run before tagging.

**Key context:**
- Scope came from a seven-lens fan-out (five sibling cores, Playstead, save-state primary sources, GabbaBoy's own delivery data) plus an adversarial review. The evidence is in [research/v0.3/](research/v0.3/).
- The Playstead pin and continuation protocol (INT-01b), mGBA/BGB RTC footer interop and libretro are parked in [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md), each with a promotion trigger.
- Process caps adopted at kickoff (D-102–D-106): at most 4 phases and about 40 plans per milestone; at most 12 plans per phase; at most 2 review-fix rounds and 1 gap round per phase.

</details>

<details>
<summary>v0.2 phase-by-phase state history (superseded)</summary>

Completed stage: **Phase 15.1 execution paused at owner request — 14/19 plans executed and summarized**. Plan 07 is complete at `842ee39`; Plan 08 task 1 has an incomplete, unstaged policy checker and no task commit or SUMMARY. Waves 1–3 and Plan 07 focused evidence are retained; Wave 4 integration has not run. The latest complete core gate tested source `8174104`: 1,140/1,144 passed in 397.51 seconds. Plan 07 subsequently repaired the ledger checks in focused verification; a new full gate is still required. Plan 10 owns the obsolete dense-failure expectation and live malformed-summary negative. Five plans plus final phase qualification remain. No phase completion, live hosted qualification, PR/merge, publication, or debt acceptance is claimed.

Next phase: **15.1 — Release Hardening and Milestone Debt Closure**. Exact next command: `/gsd-execute-phase 15.1`.

Scope: [15.1-SCOPE.md](milestones/v0.2-phases/GB-15.1-release-hardening-and-milestone-debt-closure/15.1-SCOPE.md) and its machine-readable inventory track all 21 audit debts, both closeout scan items and the inherited SUMMARY schema caveat. Validate each finding before fixing; preserve historical unknowns and all v0.2.0 producer receipts. Reuse existing research and completed implementation. Both automatic advance flags remain false; v0.3 is provisional and unstarted.

**Phase 15 is complete; v0.2.0 is published.** All 10 plans are executed. [Goal verification](milestones/v0.2-phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-VERIFICATION.md) passes 12/12, and CGB-11, SHIP-09, SHIP-10 and SHIP-11 are complete. Security closes 21/21 threats, and Nyquist validation is compliant. [Automated UAT](milestones/v0.2-phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-UAT.md) closes 42/42 deliverables and 10/10 commit windows with zero human checkpoints. Release [`v0.2.0`](https://github.com/szTheory/gabbaboy/releases/tag/v0.2.0) was published from tag source `ab301aa` with 22 assets after the exact-tag gates passed. A fresh download matches the live release. It is unsigned and not notarized. No CGB game-level evidence exists; the release says so. The hosted DMG paired benchmark is +14.86% (±1.62%) slower than v0.1.0, which is disclosed in the receipt and docs/release.md. Eight advisory code-review warnings remain open in [15-REVIEW-DISPOSITION.md](milestones/v0.2-phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-REVIEW-DISPOSITION.md) for v0.2.1. Release-please PR #75 (0.2.1) is open and not merged. Milestone re-audit: **tech_debt**, 28/28 requirements satisfied, 9/9 phase goals and Nyquist-compliant phases, 9/9 connections and 6/6 flows; no critical blocker. Fresh integration passed 63/63 focused checks plus the stall diagnosis. Phase 7 validation and Phase 11/13 SUMMARY discrepancies are resolved. The audit retains 21 deferred items across three phases, including all 16 Phase 15 advisories. Debt is not silently accepted. Current route: `/gsd-execute-phase 15.1` for the owner-authorized cleanup before renewed milestone review. Open PRs at the audit snapshot: #75, #78–81; exact-head required checks remain the merge gate. Phase 15.1 is planned and awaiting execution; v0.3 remains provisional. Both auto flags remain false.

**Phase 14 is a completed prerequisite:** [14-UAT.md](milestones/v0.2-phases/GB-14-cgb-e-model-qualification-and-corpus/14-UAT.md) closes 49 deliverables and 13 bounded commit windows with zero human checkpoints; [goal verification](milestones/v0.2-phases/GB-14-cgb-e-model-qualification-and-corpus/14-VERIFICATION.md) passes 41/41 and CGB-08/CGB-10 are complete. PR #71 merged at `c771b1b9c143d7589f8bb40c163c2e9f89ca1168`. Reuse its source-qualified receipts and completed UAT. The software corpus contains 107 cases, 25 actual passes and 82 matched expected failures. Physical CGB-E remains UNKNOWN/POLICY; analog/perceptual output and general game compatibility remain unqualified.

**Phase 13 is a completed prerequisite:** execution 12/12, canonical goal verification 37/37, automated UAT 45/45 with zero human checkpoints, CGB-07 closed, and PR #69 merged at `261c660396db65712dabb5f65b3e81ee5b0a3453`. Reuse its source-qualified records and completed UAT rather than restarting them. Its 5/5 software-fixture denominator, physical CGB-E UNKNOWN/POLICY, optional CGB-C rights exclusion and D-06/Pan Docs discrepancy remain explicit.

- **Shipped:** v0.1 Limited DMG Preview (milestone closed 2026-10-10; release [`v0.1.0`](https://github.com/szTheory/gabbaboy/releases/tag/v0.1.0) published 2026-10-09). 7 phases, 64 plans, 35/35 requirements, audit `passed`.
- **Phase 7 (2026-10-11):** Libbet and the Magic Floor v0.08 passes headless acceptance on three OSes and in the macOS packaged player; the DMG baseline is frozen. One game on one software model; no hardware evidence.
- **Phase 8 (2026-10-11):** Cartridge behavior sits behind one type-table mapper seam with zero observed DMG change (old-versus-new differential, frozen baseline); MBC5 (9-bit banking, 8 MiB, rumble query) and MBC2 (built-in nibble RAM, 512-byte battery image) run in the core. Mooneye mbc2 7/7 and mbc5 8/8 pass. Player persistence is still MBC1 only; no hardware MBC observation.
- **Phase 9 (2026-10-11):** MBC3 (`$0F`-`$13`, 7-bit ROM banking, RAM banks 0-3; MBC30 rejected) runs with an RTC that advances only from emulated time (rtc3test v004 basic/range/sub-second pass; no host clock in `src/core`, proven by source and object scans). Hosts apply wall-clock time only through `gbb_rtc_catch_up(instance, int64_t)`; timer cartridges append a 21-byte versioned RTC block to the battery image. The macOS player persists MBC2/MBC3/MBC5 in a v2 envelope with `saved_at` and catch-up on reopen, and every v0.1 save loads unchanged. MagenTests OOB SRAM passes for MBC1/3/5. No physical RTC or cartridge observation.
- **Phase 10 (2026-10-12):** A caller can create the `GBB_PROFILE_CGB_CPU_E` profile, probe a ROM and read model and execution mode through a sized `gbb_info`; post-boot state is a provenance-labelled table per DMG/CGB/compat column. VRAM (2x8 KiB) and WRAM (8x4 KiB) are banked with echo and OAM DMA sources; FF00-FF7F visibility is a tested per-cell matrix, KEY0 is locked and unbuilt CGB registers fail closed. Every core function and model branch carries a scanned model tag. DMG output is byte-identical (frozen baseline), but the DMG path measured about +6-7% slower than the Phase 7 baseline on a loaded host (advisory; review trigger fired). No colour output, double speed or HDMA yet; CGB-mode post-boot cells are Pan Docs/SameBoy/policy, not hardware evidence.
- **Phase 11 (2026-10-13):** CGB software renders in colour through `gbb_copy_frame_rgb555`: palette RAM ports (auto-increment, mode-3 lockout), BG/window/OBJ attributes and the CGB priority rules resolve per dot, checked against an independent 6144-row truth table, original RGBDS fixtures and three MagenTests ROMs. DMG software on the CGB profile uses a fixed, original, documented compatibility palette a host can override (no boot-ROM table). The SDL3 player takes `--model auto|dmg|cgb` and presents colour, with a pinned CGB smoke in CI. DMG output stays byte-identical. AGE has no CGB colour ROM at its pinned commit (D-20); mode-3 pixel timing is Phase 14; no hardware or perceptual colour claim.
- **Phase 12 (2026-10-14):** KEY1 plus STOP switches CGB CPU, timer, serial and OAM DMA rates while PPU/APU/RTC remain on the master timeline. The persisted destination-speed stall is `0x20004` CPU T within the measured AGE window `[0x20004,0x20007]`; original and hostile guests, natural timer IRQ dispatch, output digests, mutation controls and partitioned runs exercise the behavior. Only AGE DIV (5/5) and STOP-prefetch (1/1) are passes; eleven other ROMs retain exact-signature expected-failure dispositions. CGB-06 goal verification passed 109/109 and the local core suite passed 898/898, with no DMG baseline change. PR #68 is merged at `8091fb591de7fb68e666be01d344f5f26ebedc5c`; no physical hardware qualification or local libFuzzer campaign is claimed.
- **Phase 13 (execution and goal verification complete):** Bounded GDMA/HBlank DMA, CPU stall/HALT interaction, cancel/readback, mapped source and bank policies, partition/resource controls, original and pinned fixtures, installed C/C++ consumers and player coverage pass the selected software contract. [13-VERIFICATION.md](milestones/v0.2-phases/GB-13-cgb-hdma/13-VERIFICATION.md) passes 37/37; [13-BENCH.md](milestones/v0.2-phases/GB-13-cgb-hdma/13-BENCH.md) records fresh local and exact-head hosted results, measured costs and artifact identities separately from history. Automated UAT passed 45/45 deliverables with zero human checkpoints; reuse the completed record unless covered behavior or evidence changes. No physical hardware or host-fuzzer campaign claim.
- **Code:** ~18k lines of C/C++ (about 7k in `src/` + `include/`); CMake/Ninja/CTest; 184 local CTest cases at the 06.1 regression run; required CI on Linux, macOS and Windows (MinGW-w64).
- **Evidence scope:** admitted corpus is three source-qualified derived Mooneye CPU/timer closures plus original project ROMs. No physical hardware, perceptual output, signing/notarization, or live Playstead integration is claimed.
- **Open:** No open issues or PRs at the v0.2 start (2026-10-10); releases `v0.1.0` and `v0.1.2` published. Accepted info-level debt is listed in the [v0.1 audit](milestones/v0.1-MILESTONE-AUDIT.md).

**Milestone definition (v0.2 Color & Cartridge Breadth):**

**Goal:** Play supported CGB software and the common MBC2/MBC3/MBC5 cartridge set (with deterministic RTC) through the same bounded core and player, after first proving one rights-clear game end to end on the existing DMG player.

**Target features:**
- One rights-clear game-level acceptance in the existing DMG player (guest-observable start/progress, meaningful input, visible/audio response) before any broadened claim.
- MBC5, MBC3 with deterministic host-independent RTC (and its battery persistence), and MBC2 with built-in RAM.
- A CGB silicon profile: CGB mode and DMG-compatibility mode, double-speed switching, VRAM/WRAM banking, BG/OBJ color palettes and attributes, general/HBlank HDMA, and model-specific CPU/PPU/APU differences under explicit model qualification.
- Updated support ledger, docs, release notes, and a qualified v0.2 release scoped to the tested corpus.

Deferred to v0.3 (States & Integration): transactional versioned save states (STATE-01) and a qualified Playstead adapter (INT-01), so serialization is designed once over the complete DMG+CGB machine state.

</details>

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

- ✓ An explicit record that no CGB game-level evidence exists, a current v0.2.0 support ledger with docs and relocated consumers, and an exact-tag qualified v0.2.0 release with corpus, fuzz, performance, consumer and source-archive receipts (CGB-11, SHIP-09..11) — Phase 15, goal verification 12/12, automated UAT 42/42; the release is unsigned and not notarized.

- ✓ Release hardening and milestone debt closure without republishing v0.2.0: closeout scan and disposition ledgers, point-in-time boundary verifiers, automated UAT closure and Nyquist validation 82/82 (EVID-02, SHIP-09..11 re-verified) — Phase 15.1; the twelve LIM rows remain owner decisions. All 28 v0.2 requirements validated — v0.2.

- ✓ Tune-up and v0.2 debt closure: v0.2 phase records archived behind a phase-path lint, Phase 8 verifiers in CTest, a cumulative DMG Ir performance gate against v0.2.0, CI budget and planning-hygiene checks, and the v0.2.1 patch release (TUNE-01..06). Phase 16: goal verification 5/5, automated UAT 51/51, security 0 open threats. The D-112 one-time gate substitutions were followed by production gate implementation in Phases 17–19; RM-030 is delivered.

- ✓ Transactional native save states and exact-continuation/portability/completeness controls (STATE-01..06) — v0.3, Phases 17–19.
- ✓ Player save slots through the public state API (PLAY-01) — v0.3, Phase 18.
- ✓ POSIX host runner with atomic raw saves, SIGTERM save-and-exit, exit-code table and declared formats (HOST-01..03 / INT-01a) — v0.3, Phases 18–19.
- ✓ Qualified tag-bound v0.3.0 publication, scoped claims and reconciled release receipts (REL-01) — v0.3, Phase 19.

### Active

None selected. All v0.3 requirements are validated in the [requirements archive](milestones/v0.3-REQUIREMENTS.md). The next milestone will define fresh requirements after the owner invokes `/gsd-new-milestone`.

Ongoing project principles: dependency-light C API with explicit contracts; headless core independent of the player; reproducible tests, sanitizers, fuzzing, and baselines; tested artifacts through PR and release automation; source-linked decisions, current docs, and transferable lessons.

### Out of Scope

- NES, Neo Geo, and GBA execution — distinct hardware belongs in distinct projects.
- Proprietary game or boot ROM distribution — public automation needs permissioned fixtures.
- A game library manager, accounts, online services, or mandatory telemetry — frontend concerns outside the core.
- Universal compatibility, unmeasured “fastest” claims, or instruction-test pass rates presented as game compatibility.
- JIT, plugin frameworks, a generic multi-console bus, and broad scripting before demonstrated need.
- SGB/SGB2, additional silicon revisions, uncommon cartridge peripherals, link accessories, rewind/runahead, and web/mobile ports in v0.1–v0.2 — retain as revisable future scope.

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
| Rehearse exact-tag release producers on the version PR tree before tagging | Release-only jobs never run in ordinary CI | ✓ Good — Phase 15: the rehearsal found three defects before the tag; a fourth (assumed package wrapper) failed the first tagged run and was fixed before publishing, without replacing assets |
| Insert a debt-closure phase before closing a milestone | The first audit returned `tech_debt`; closing it first gave a clean `passed` re-audit | ✓ Good — Phase 06.1 |
| Boundary checks read facts from the boundary commit, never the live HEAD | Live-route and ancestry assertions drifted as later commits landed and produced false gaps | ✓ Good — Phase 15.1 (strict-head replay per boundary commit; seven validation rows still read live state) |
| Automated UAT closure with zero human checkpoints | Repeatable acceptance belongs in contract checks with negative controls, not manual readings (D-069) | ✓ Good — Phases 13–15.1 closed UAT via `verify-uat-closure.py` |
| Keep v0.2 phase records in place at milestone close | CTest and closeout verifiers read helper scripts and records in `.planning/phases/`; moving them would break main | ⚠️ Superseded by Phase 16 archive — the records moved to `.planning/milestones/v0.2-phases/`, readers were retargeted and a phase-path lint guards the tree |
| Second debt-closure phase (15.1) before v0.2 archival | The post-release audit found actionable closeout debt; owner-only LIM decisions stayed explicit rather than silently accepted | ✓ Good — re-audit `tech_debt` with no blockers; 12 LIM rows still need owner decisions |

| Exact native continuation with transactional state validation | Serialized bytes include in-flight machine state; refused loads must not partially apply | ✓ Good — v0.3 fork matrix, omission mutants, canonical pins and hostile-load controls |
| Preserve phase-boundary evidence and use one final implementation-head suite | Later phases change shared files and invalidate runtime fingerprints | ✓ Good — v0.3 evidence retained; owner explicitly accepted the runtime closeout override |
| Bound release recovery and retain failed attempts | Successful retries cannot erase the original failure or change product/tag provenance | ✓ Good — v0.3.0 published with separately attributed failed and successful attempts |
| Keep reusable checks independent of phase storage | Milestone archival must preserve executable check inputs | ✓ Good — v0.3 CTest disposition/readback paths follow archived records; negative controls retained |

## Evolution

At each phase boundary, update delivered requirements, evidence, limitations, decisions, docs, performance/correctness baseline changes, open issue/PR triage, and the next recommended action. Stop before the next phase.

At each milestone boundary, audit this document and the active requirements, summarize compatibility by tested model/corpus, refresh the near/mid/long-term roadmap, and prepare a concise lesson transfer for sibling emulator projects. Keep unverified external advice separate until reproduced locally.

---
Last updated: 2026-10-31 after v0.3 milestone completion; next milestone not started.
