# Roadmap: GabbaBoy

## Overview

GabbaBoy will grow an original portable C core from real guest execution into a usable, limited DMG player with safe battery continuation, sound, and an installed native integration path. Each phase extends the same public API and legal fixture path. No emulator functionality, passing corpus, performance baseline, remote CI, or release exists at initialization.

## Milestones

- **v0.1 — limited DMG preview:** active scope, Phases 1–6; declared ROM-only/MBC1 support and honest 0.x contracts, without stable API/ABI promises.
- **Next — GB/GBC breadth:** committed CGB direction, broader cartridges, RTC, complete states, and consumer integration; refine separately in [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md). Completing v0.1 does not complete the GB/GBC project.

Research basis: [2026-10-02 synthesis](research/SUMMARY.md), [hardware and validation](research/HARDWARE-AND-VALIDATION.md), [architecture](research/ARCHITECTURE.md), and [quality and delivery](research/QUALITY-AND-DELIVERY.md). Recommendations require implementation evidence; exact hardware profiles, tool pins, and host floors are fixed during the relevant phase.

## Phases

- [x] **Phase 1: Portable Foundation and Original ROM Tracer** - Build, embed, and download a bounded real-ROM tracer. (completed 2026-10-03)
- [x] **Phase 2: DMG CPU, Bus, and Time** - Execute scoped DMG diagnostics with reproducible timing and bounded progress. (completed 2026-10-07)
- [ ] **Phase 3: Visible Interactive DMG** - Play an original or permissioned ROM-only fixture in a macOS preview.
- [ ] **Phase 4: MBC1 and Safe Battery Continuation** - Retain meaningful guest progress across fresh processes without corrupting good saves.
- [ ] **Phase 5: DMG Audio and Stable Playback** - Hear paced sound and recover cleanly from host input/device transitions.
- [ ] **Phase 6: Qualified DMG Release and Consumer Handoff** - Download evidenced packages and reproduce native adoption with honest support claims.

## Phase Details

### Phase 1: Portable Foundation and Original ROM Tracer

**Goal**: As a developer, I want to run an original ROM with an installable GB core via a bounded API, so that I can embed it.
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: BASE-01, BASE-02, BASE-03, BASE-04, BASE-05, BASE-06, BASE-07, BASE-08
**Success Criteria** (what must be TRUE):

1. A developer can configure, build, test, and install the C17 core/runner using documented CMake/Ninja/CTest commands without SDL or network access after explicit preparation. External C and C++ consumers link installed `GabbaBoy::core` using only public includes and execute the original tracer. (BASE-01, BASE-06)
2. A caller can create, reset, run, and destroy independent opaque instances under documented model, ownership, lifetime, threading, and error rules; malformed, excessive, or unsupported ROM input produces a bounded non-destructive error. (BASE-02, BASE-03)
3. The original ROM executes its declared opcode subset through the real CPU/bus path and returns a deterministic bounded trace; unsupported execution is explicit. Every admitted fixture has reproducible source/build/digest, license, model/boot, pass-protocol, and timeout evidence. (BASE-04, BASE-05)
4. A contributor receives a required CI result proving that loader/lifecycle error cases and ASan/UBSan checks actually ran; missing mandatory fixtures/cases, failures, and timeouts fail the gate. (BASE-07)
5. A contributor can use the configured remote/PR workflow and download a revision-linked foundation-preview core/runner with an installation smoke result and explicit capability limits. (BASE-08)

**Plans**: 5/5 plans complete in 5 dependency-ordered waves; see [Phase 1 plans](phases/GB-01-portable-foundation-and-original-rom-tracer/).
- [x] 01-01-PLAN.md
- [x] 01-02-PLAN.md
- [x] 01-03-PLAN.md
- [x] 01-04-PLAN.md
- [x] 01-05-PLAN.md

### Phase 2: DMG CPU, Bus, and Time

**Goal**: As a core integrator, I want to run the declared DMG instruction and timing behavior deterministically, so that I can reproduce diagnostic failures.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: CPU-01, CPU-02, CPU-03, CPU-04, CPU-05
**Success Criteria** (what must be TRUE):

1. The declared DMG profile produces expected base/CB instruction, flag, arithmetic, address, and bus-access timing results, with explicit illegal-opcode behavior. (CPU-01)
2. Model-applicable cases observe expected interrupt entry, EI delay, HALT/HALT-bug, STOP, reset, and deterministic post-boot results. (CPU-02)
3. Guests observe the declared memory mapping, divider/timer edges and reload races, and disconnected serial behavior at timed access boundaries. (CPU-03)
4. Equal timestamped inputs and elapsed emulated time produce equal supported state/output across different run partitions; LCD-off, HALT/STOP, lockup, and full output capacity return within the caller's bounded contract. (CPU-04)
5. A headless run reports pass/fail/timeout/unsupported against a pinned eligible CPU/timer corpus with model/boot/protocol identity and sufficient retained trace evidence to reproduce failures. (CPU-05)

**Plans**: All 17 runnable plans have summaries: the original nine, gap-closure Plans 02-10 through 02-14, and Plans 02-16 through 02-18. Plan 02-15 is explicitly superseded and non-runnable; its halted summary remains historical evidence. The goal-backward verifier passed all five roadmap truths, the security audit closed all 45 registered threats, and the Nyquist audit resolved all eight identified coverage gaps with no escalation. At implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989`, the local 104-case inventory, relocated 109-case inventory, exact hosted CI run 37620710587, and fixture reproduction run 37620710600 passed. See [verification](phases/GB-02-dmg-cpu-bus-and-time/02-VERIFICATION.md), [validation](phases/GB-02-dmg-cpu-bus-and-time/02-VALIDATION.md), and [security](phases/GB-02-dmg-cpu-bus-and-time/02-SECURITY.md). No physical DMG-CPU-B observation is claimed. Phase 3 remains paused until the owner chooses to continue; next command: `$gsd-discuss-phase 3`.
**Wave 1**
- [x] 02-01-PLAN.md — ROM-only bus and WRAM tracer

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 02-02-PLAN.md — complete base SM83 instructions and lockup

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 02-03-PLAN.md — complete CB SM83 instructions

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 02-04-PLAN.md — interrupts, HALT, STOP and reset

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 02-05-PLAN.md — timer races and disconnected serial

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 02-06-PLAN.md — timestamped inputs and bounded partitioned runs

**Wave 7** *(blocked on Wave 6 completion)*
- [x] 02-07-PLAN.md — pinned offline CPU/timer diagnostics

**Wave 8** *(blocked on Wave 7 completion)*
- [x] 02-08-PLAN.md — runner protocols, statuses and receipts

**Wave 9** *(blocked on Wave 8 completion)*
- [x] 02-09-PLAN.md — installed consumers, CI and documentation

**Gap-closure waves** *(execute with `$gsd-execute-phase 2 --gaps-only`)*

**Gap wave 1**
- [x] 02-10-PLAN.md — checksum-derived post-boot flags and RET/RETI phases
- [x] 02-13-PLAN.md — diagnose and repair pinned fixture byte reproduction (diagnostic complete; exact cross-host byte qualification remains open)

**Gap wave 2** *(blocked on Gap wave 1 completion)*
- [x] 02-11-PLAN.md — consecutive EI semantics and chronological interrupt diagnostics

**Gap wave 3** *(blocked on Gap wave 2 completion)*
- [x] 02-12-PLAN.md — Windows manifest portability and distinct negative-control results

**Gap wave 4** *(blocked on Gap wave 3 and 02-13 completion)*
- [x] 02-14-PLAN.md — source-qualify PPU-independent corpus candidates and result protocol (source/protocol path later qualified and admitted by Plan 02-17)

**Gap wave 5** *(blocked on Gap wave 4 completion)*
- 02-15-PLAN.md — superseded/non-runnable; retain 02-15-SUMMARY.md as historical evidence
- [x] 02-17-PLAN.md — qualify deterministic candidate-aware cross-host bytes and admit fixtures after exact hosted byte identity

**Gap wave 6** *(blocked on Gap wave 5 qualification/admission outcome)*
- [x] 02-16-PLAN.md — verify runner protocol, inventory, and final exact-revision evidence

**Gap wave 7** *(closes the independently verified CPU-01/D-01 semantic coverage gap)*
- [x] 02-18-PLAN.md — assert legal base-opcode architectural semantics, branch paths, address effects and timed bus behavior

### Phase 3: Visible Interactive DMG

**Goal**: A macOS user can play a legal interactive ROM-only GB fixture with deterministic input and evidenced DMG video behavior.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: VIDEO-01, VIDEO-02, VIDEO-03, VIDEO-04, VIDEO-05
**Success Criteria** (what must be TRUE):

1. Background, window, and sprites render as expected, with LCD/STAT transitions and dot-sensitive fetching demonstrated by separate composition and raster-timing cases. (VIDEO-01)
2. Guests observe model-specific OAM DMA, VRAM/OAM restrictions, and CPU/PPU/DMA contention results. (VIDEO-02)
3. Timestamped joypad transitions produce deterministic selection/interrupt behavior through both the public API and SDL keyboard path. (VIDEO-03)
4. A macOS user can open and play an original or permissioned ROM-only fixture, resize with correct aspect/integer scaling, pause, reset, and quit; errors are actionable. (VIDEO-04)
5. Automated evidence separately reports image composition, raster timing, and scripted gameplay; the visible preview labels incomplete audio and persistence. (VIDEO-05)

**Plans:** All 11 plans have summaries across 10 dependency-ordered waves; gap-closure Plans 03-10 and 03-11 occupy Wave 10. Phase verification remains open on VIDEO-02 and VIDEO-03 model-applicability evidence, so Phase 3 remains in progress.
**Wave 1**
- [x] 03-01-PLAN.md — playable production-core tracer with timestamped input and copied frames

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 03-02-PLAN.md — background/window/object composition and dot-sensitive LCD/STAT behavior

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 03-03-PLAN.md — OAM DMA, memory restrictions, and CPU/PPU/DMA contention

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 03-04-PLAN.md — bounded joypad matrix and evidence-gated interrupt behavior

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 03-05-PLAN.md — optional SDL3 player and deterministic host input timing

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 03-06-PLAN.md — ROM controls, high-DPI integer presentation, and visible limitations

**Wave 7** *(blocked on Wave 6 completion)*
- [x] 03-07-PLAN.md — public API failure boundaries and installed C/C++ consumers

**Wave 8** *(blocked on Wave 7 completion)*
- [x] 03-08-PLAN.md — reproducible original fixture and pinned hosted reproduction

**Wave 9** *(blocked on Wave 8 completion)*
- [x] 03-09-PLAN.md — exact-revision macOS preview package qualification

**Gap wave 10** *(closes only the remaining evidence and limitation-test gaps; both plans depend on Wave 9)*
- [x] 03-10-PLAN.md — source-applicable DMA/JOYP evidence and provenance-gated CPU-B observation
- [x] 03-11-PLAN.md — automated audio and battery-persistence limitation assertions

**UI hint**: yes

### Phase 4: MBC1 and Safe Battery Continuation

**Goal**: Players can use declared MBC1 cartridges and resume meaningful saved progress after restarting without losing their last good save on failure.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: SAVE-01, SAVE-02, SAVE-03, SAVE-04
**Success Criteria** (what must be TRUE):

1. Declared standard MBC1 ROM/RAM/battery configurations exhibit expected banking and enable behavior; excluded variants and other mappers return explicit errors. (SAVE-01)
2. A frontend can import/export bounded battery data under documented identity/size rules, and malformed imports leave live state unchanged. (SAVE-02)
3. The player follows documented atomic replacement, recovery, and concurrent-writer rules; failed writes preserve the last good save and visibly report failure. (SAVE-03)
4. An original GB fixture saves, exits, reopens in a fresh instance/process, and resumes behavior dependent on prior bytes; empty/wrong-save controls demonstrate a meaningful continuation oracle. (SAVE-04)

**Plans**: TBD
**UI hint**: yes

### Phase 5: DMG Audio and Stable Playback

**Goal**: Players hear paced DMG sound and retain responsive controls through normal playback and host-device transitions.
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: AUDIO-01, AUDIO-02, AUDIO-03, HOST-01, HOST-02
**Success Criteria** (what must be TRUE):

1. All four DMG sound channels, registers, and divider-driven sequencer produce expected scoped digital results, with analog/revision approximations stated. (AUDIO-01)
2. Frontends receive deterministic bounded PCM under documented format, sample-rate/resampling, buffer-lifetime, and backpressure rules; stepping neither allocates nor silently discards required output. (AUDIO-02)
3. The macOS player provides volume control and paced sound without changing guest clock semantics; sustained scripted play records queue bounds and underrun/overrun behavior. (AUDIO-03)
4. Keyboard/basic controller input recovers across focus loss and disconnect/reconnect; host input reset cannot leave guest buttons stuck. (HOST-01)
5. Pause/resume, reset, ROM replacement, and audio-device transitions follow documented flush/recovery behavior without mixing stale video/audio/input/battery state between sessions. (HOST-02)

**Plans**: TBD
**UI hint**: yes

### Phase 6: Qualified DMG Release and Consumer Handoff

**Goal**: Adopters can download a qualified limited-DMG release, reproduce native integration, and assess its actual compatibility, safety, and performance evidence.
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: SHIP-01, SHIP-02, SHIP-03, SHIP-04, SHIP-05, SHIP-06, SHIP-07, SHIP-08
**Success Criteria** (what must be TRUE):

1. Clean relocated packages build/run external C/C++ consumers on the claimed host/compiler matrix without private/SDL dependencies; an adopter can follow current build, ownership/time/input/output, save recovery, support/upgrade/troubleshooting docs and a reproducible Playstead-oriented native example with honest live-integration status. (SHIP-01, SHIP-04)
2. The packaged macOS player passes automated legal-fixture load/input/video/audio/save/exit/reopen smoke; perceptual or device limitations are separately recorded. (SHIP-02)
3. Downloaded release bytes match their source revision/version/digests and include notices and release notes; only verified signing/notarization is claimed. Actual repository evidence covers required PR checks, bot CI, current-revision merge eligibility, release triggering, cache behavior, and failure propagation; stale/skipped lanes or untrusted privileged execution cannot authorize publication. (SHIP-03, SHIP-08)
4. An adopter can inspect a support ledger naming DMG revision, boot profile, mapper scope, corpus revision, executed eligible denominator, failures/exclusions, and known issues, alongside reproducible fixed-workload speed, memory/allocation, trace, build, and CI baselines with output digests, samples, environment, and uncertainty. Budgets follow measured variance; subset pass rates are not all-game compatibility. (SHIP-05, SHIP-06)
5. Maintainers can reproduce bounded loader/battery/API fuzz and boundary-regression results under applicable sanitizers; minimized findings enter fast regression coverage while longer exploration remains separately runnable. (SHIP-07)

**Plans**: TBD
**UI hint**: yes

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Portable Foundation and Original ROM Tracer | 5/5 | Complete    | 2026-10-03 |
| 2. DMG CPU, Bus, and Time | 17/17 | Complete | 2026-10-07 |
| 3. Visible Interactive DMG | 11/11 | In Progress | - |
| 4. MBC1 and Safe Battery Continuation | 0/TBD | Not started | - |
| 5. DMG Audio and Stable Playback | 0/TBD | Not started | - |
| 6. Qualified DMG Release and Consumer Handoff | 0/TBD | Not started | - |

## Execution Contract

All **35/35 active requirements** map to exactly one phase in [REQUIREMENTS.md](REQUIREMENTS.md). Phase 1's BASE-01 through BASE-08 are satisfied at the verified implementation revision; exact hosted CI, fixture reproduction, and Linux/macOS package evidence also passed at the docs-only PR head recorded in [Phase 1 verification](phases/GB-01-portable-foundation-and-original-rom-tracer/01-VERIFICATION.md). Requirements for later phases remain pending their own implementation and evidence. Safety, fixture rights, documentation, install consumers, and release evidence expand as each boundary arrives. Phase 6 qualifies the completed product; it does not postpone basic safety or packaging until the end.

Automate authorized work within each phase, then inspect current verification/release/consumer evidence, update traceability and [lessons](context/LESSONS.md), triage issues/PRs, report limitations and the exact next command, and **stop**. Never auto-advance phases or milestones; keep both auto-advance flags false. Credential, hardware, or perceptual gaps must be recorded honestly with the smallest necessary human action, never converted into passing evidence. Remote/CI setup begins in Phase 1; absent access remains an explicit completion limitation.

Phase 1 Plans 01–05 are complete. Goal-backward verification passed 5/5 roadmap truths and all 8 BASE requirements; standard code review is clean. Phase 2 Plans 02-01 through 02-14 and 02-16 through 02-18 are complete; 02-15 remains superseded/non-runnable. Phase 2 passed 5/5 roadmap truths, all five CPU requirements, 45/45 security threats, Nyquist validation and code review; no physical DMG hardware test is claimed. The original nine Phase 3 plans are complete; gap-closure Plans 03-10 and 03-11 are ready in Wave 10. VIDEO-01, VIDEO-04, and VIDEO-05 are complete, including exact-head CI run 37686137977 and downloaded-package consumer run 37686137834 at `fd62c48d84b8339435fefd008147f0c06f696e0e`. Phase 3 remains open with VIDEO-02 simultaneous PPU/DMA evidence and D-08/VIDEO-03 JOYP interrupt evidence unresolved; live desktop perception and physical DMG-CPU-B observation remain unavailable. The exact next command is `$gsd-execute-phase 3 --gaps-only`; keep both auto-advance flags false and stop before Phase 4: MBC1 and Safe Battery Continuation.
