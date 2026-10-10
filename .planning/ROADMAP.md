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
- [x] **Phase 3: Visible Interactive DMG** - 13 plans are complete; refreshed canonical verification passed 5/5 roadmap truths on 2026-10-10 after review fixes to release output placement and withdrawal reporting; existing UAT passed 34/34. (completed 2026-10-09)
- [x] **Phase 4: MBC1 and Safe Battery Continuation** - Retain meaningful guest progress across fresh processes without corrupting good saves. (implementation completed 2026-10-08; canonical verification refreshed 2026-10-09)
- [x] **Phase 5: DMG Audio and Stable Playback** - Hear paced sound and recover cleanly from host input/device transitions. (implementation completed 2026-10-08; refreshed verification passed 17/17 truths on 2026-10-10 after the shared helper and FIFO-open changes)
- [x] **Phase 6: Qualified DMG Release and Consumer Handoff** - Download evidenced packages and reproduce native adoption with honest support claims. (implementation completed 2026-10-09; refreshed verification passed 5/5 again on 2026-10-10 after the release output-path and withdrawal-reporting fixes)

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

**Plans**: 7/5 plans complete in 5 dependency-ordered waves; see [Phase 1 plans](phases/GB-01-portable-foundation-and-original-rom-tracer/).
**Verification**: Fresh canonical verification passed all five roadmap truths and BASE-01 through BASE-08 on 2026-10-09 and refreshed again on 2026-10-10 (21/21 after the CI player-gate drift); see [verification](phases/GB-01-portable-foundation-and-original-rom-tracer/01-VERIFICATION.md) and [exact-hosted evidence](phases/GB-01-portable-foundation-and-original-rom-tracer/01-VALIDATION.md).
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

**Plans**: All 17 runnable plans have summaries: the original nine, gap-closure Plans 02-10 through 02-14, and Plans 02-16 through 02-18. Plan 02-15 is explicitly superseded and non-runnable; its halted summary remains historical evidence. Fresh canonical verification on 2026-10-09 passed all five roadmap truths and CPU-01 through CPU-05. The focused Phase 2 selection passed 88/88, the current full local CTest inventory passed 179/179, and the live runner produced passing receipts for all three eligible cases; the candidate protocol probe passed with zero PPU accesses. The security audit closed all 45 registered threats, and the Nyquist audit records eight resolved gaps and zero current gaps. Earlier exact hosted CI run 37620710587 and fixture reproduction run 37620710600 qualify implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989`; they are historical source-revision evidence, not checks for the current refresh branch. See [verification](phases/GB-02-dmg-cpu-bus-and-time/02-VERIFICATION.md), [validation](phases/GB-02-dmg-cpu-bus-and-time/02-VALIDATION.md), and [security](phases/GB-02-dmg-cpu-bus-and-time/02-SECURITY.md). No physical DMG-CPU-B observation or broad compatibility claim is made. Phases 1, 3, 5 and 6 refreshed on 2026-10-10. Quick task 261010-bz3 reconciled CPU-02/CPU-05 summary metadata (02-16, 02-17); the 2026-10-10 Phase 2 freshness refresh then regenerated verification at `a9050df`: 5/5 truths and CPU-01–05 passed, 179/179 CTest, 88/88 focused Phase 2 cases, three eligible runner receipts, and the protocol probe with zero PPU accesses.
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

**Goal**: As a Mac user, I want to play a legal GB ROM with timed input and video evidence, so that I can verify the DMG preview.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: VIDEO-01, VIDEO-02, VIDEO-03, VIDEO-04, VIDEO-05
**Success Criteria** (what must be TRUE):

1. Background, window, and sprites render as expected, with LCD/STAT transitions and dot-sensitive fetching demonstrated by separate composition and raster-timing cases. (VIDEO-01)
2. Guests observe model-specific OAM DMA, VRAM/OAM restrictions, and CPU/PPU/DMA contention results. (VIDEO-02)
3. Timestamped joypad transitions produce deterministic selection/interrupt behavior through both the public API and SDL keyboard path. (VIDEO-03)
4. A macOS user can open and play an original or permissioned ROM-only fixture, resize with correct aspect/integer scaling, pause, reset, and quit; errors are actionable. (VIDEO-04)
5. Automated evidence separately reports image composition, raster timing, and scripted gameplay; the preview accurately states supported audio/persistence scope and remaining limitations. (VIDEO-05)

**Plans:** All 13 plans have summaries across 12 dependency-ordered waves. The 2026-10-10 freshness refresh passed 5/5 truths and VIDEO-01–05 at clean HEAD `9832ba4` on `gsd/phase-03-verification-refresh`. Its code review fixed a release-workflow defect: in-repo `GBB_VERIFIED_OUTPUT_DIR` values were rejected by the helper. It also fixed swallowed or masking withdrawal reports (`91d11d4`, `8151a75`). The disposition ledger has 0 open findings. Local macOS evidence: 179/179 core tests, 20/20 helper regressions, 51/51 optional player tests, extracted-package smoke, and both release self-tests. No hosted CI has run for this revision. Existing UAT test 34 records the user's current-package confirmation and is reused rather than repeated. VIDEO-02/03 remain bounded to D-025's confidence-qualified software model; exact CPU-B timing/lane and PPU-revision behavior remain unmeasured. See [verification](phases/GB-03-visible-interactive-dmg/03-VERIFICATION.md), [review](phases/GB-03-visible-interactive-dmg/03-REVIEW.md), and [UAT](phases/GB-03-visible-interactive-dmg/03-UAT.md).
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

**Gap wave 11** *(source-backed DMA startup/restart/readback; depends on Wave 10)*
- [x] 03-12-PLAN.md — FF46 startup window, active restart, and register readback; simultaneous PPU/DMA arbitration and JOYP IF remain open

**Gap wave 12** *(source-backed software-model behavior and focused guest checks; execution does not complete Phase 3)*
- [x] 03-13-PLAN.md — JOYP edge matrix, DMA/PPU scan/fetch controls, active-DMA mode matrix, word boundaries, and same-half-dot guest tie; current packaged-player UAT is complete, and rendered Z press/hold/release is asserted by the required PR package smoke

**UI hint**: yes

### Phase 4: MBC1 and Safe Battery Continuation

**Goal**: As a player, I want to resume supported MBC1 games from battery saves, so that failures preserve my last good progress.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: SAVE-01, SAVE-02, SAVE-03, SAVE-04
**Success Criteria** (what must be TRUE):

1. Declared standard MBC1 ROM/RAM/battery configurations exhibit expected banking and enable behavior; excluded variants and other mappers return explicit errors. (SAVE-01)
2. A frontend can import/export bounded battery data under documented identity/size rules, and malformed imports leave live state unchanged. (SAVE-02)
3. The player follows documented atomic replacement, recovery, and concurrent-writer rules; failed writes preserve the last good save and visibly report failure. (SAVE-03)
4. An original GB fixture saves, exits, reopens in a fresh instance/process, and resumes behavior dependent on prior bytes; empty/wrong-save controls demonstrate a meaningful continuation oracle. (SAVE-04)

**Plans**: All seven plans across seven dependency-ordered waves have execution summaries. The refreshed canonical verification passed all seven truths and SAVE-01 through SAVE-04 on 2026-10-09. The local core inventory passed 179/179; the macOS player/package verifier passed 50/50, including FIFO ROM-path rejection and state-preserving replacement failure; the extracted package resumed the original MBC1 fixture in a fresh process. The FIFO hardening then passed PR #43 exact-head CI at code SHA `9b9d58a009b175256b09fe074e3f44e1aa0320e7`: required-native, native Linux/macOS/Windows, Linux ASan/UBSan, CMake 3.25.3 floor, macOS player package, both fixture reproductions, and Linux/macOS installed-package smoke all passed. Earlier exact hosted evidence remains scoped to `79f83f627ffb3631811b2f39b23081117ebaab8f`. The refreshed source review is clean, the security audit closed 22/22 threats, and the UI audit recorded advisory status-visibility improvements without a phase blocker. See [verification](phases/GB-04-mbc1-and-safe-battery-continuation/04-VERIFICATION.md), [validation](phases/GB-04-mbc1-and-safe-battery-continuation/04-VALIDATION.md), [security](phases/GB-04-mbc1-and-safe-battery-continuation/04-SECURITY.md), and the [evidence ledger](../docs/mbc1-evidence.md). No physical DMG/MBC1 or storage power-loss qualification is claimed. The v0.1 milestone audit ran on 2026-10-09 and found no cross-phase integration breakage; see [the audit](v0.1-MILESTONE-AUDIT.md). Phases 5 and 6 refreshed again on 2026-10-10 and pass 17/17 and 5/5 truths. Phase 1 refreshed on 2026-10-10 (21/21). Phase 2 SUMMARY metadata was reconciled (quick task 261010-bz3); refresh Phase 2 verification, then rerun the strict milestone audit.
**Wave 1**
- [x] 04-01-PLAN.md

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 04-02-PLAN.md

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 04-03-PLAN.md

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 04-04-PLAN.md

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 04-05-PLAN.md

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 04-06-PLAN.md

**Wave 7** *(blocked on Wave 6 completion)*
- [x] 04-07-PLAN.md

**UI hint**: yes

### Phase 5: DMG Audio and Stable Playback

**Goal**: As a player, I want to play DMG games with paced sound, so that controls remain responsive through device changes.
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: AUDIO-01, AUDIO-02, AUDIO-03, HOST-01, HOST-02
**Success Criteria** (what must be TRUE):

1. All four DMG sound channels, registers, and divider-driven sequencer produce expected scoped digital results, with analog/revision approximations stated. (AUDIO-01)
2. Frontends receive deterministic bounded PCM under documented format, sample-rate/resampling, buffer-lifetime, and backpressure rules; stepping neither allocates nor silently discards required output. (AUDIO-02)
3. The macOS player provides volume control and paced sound without changing guest clock semantics; sustained scripted play records queue bounds and underrun/overrun behavior. (AUDIO-03)
4. Keyboard/basic controller input recovers across focus loss and disconnect/reconnect; host input reset cannot leave guest buttons stuck. (HOST-01)
5. Pause/resume, reset, ROM replacement, and audio-device transitions follow documented flush/recovery behavior without mixing stale video/audio/input/battery state between sessions. (HOST-02)

**Plans**: 7/7 plans complete in 7 dependency-ordered waves. The 2026-10-10 freshness refresh on `gsd/phase-05-verification-refresh` (cut from `origin/main` `cb4a96c` after PR #47 merged) passed 17/17 truths and AUDIO-01–03/HOST-01–02 at `f39faac`. Gates: Nyquist 0 gaps; security 14/14 threats closed (O_NONBLOCK ROM open closes a FIFO main-loop hang); code review 0 critical/warning, 1 deferred info, disposition 0 open; regression gate core 179/179, helper 20/20, player build tree 230/230. Local macOS evidence: player/package verifier 51/51 and a clean-tree two-partition 300-frame PCM measurement with matching digest `8667279ae7d3bf3cdd76a278b13d2cdfe9992d64325c15e4eef9449778eaeec4` (SDL dummy backend). No hosted CI has run for this revision; this is not physical-device, latency or perceptual proof. The F1 help distinguishes S background-save retry from R/C/Escape blocked-transition recovery. App-level pause/resume and reset transition behavior is covered. See [verification](phases/GB-05-dmg-audio-and-stable-playback/05-VERIFICATION.md), [validation](phases/GB-05-dmg-audio-and-stable-playback/05-VALIDATION.md), [review](phases/GB-05-dmg-audio-and-stable-playback/05-REVIEW.md), and [security](phases/GB-05-dmg-audio-and-stable-playback/05-SECURITY.md). Physical hotplug and perceptual audio remain unqualified.
**Wave 1**
- [x] 05-01-PLAN.md — original pulse guest through caller PCM and SDL tracer

**Wave 2** *(depends on Wave 1)*
- [x] 05-02-PLAN.md — both pulse channels and divider sequencer

**Wave 3** *(depends on Wave 2)*
- [x] 05-03-PLAN.md — wave, noise and four-channel power matrix

**Wave 4** *(depends on Wave 3)*
- [x] 05-04-PLAN.md — fixed-point resampler, high-pass and bounded PCM API

**Wave 5** *(depends on Wave 4)*
- [x] 05-05-PLAN.md — SPSC/SDL playback, gain and pacing metrics

**Wave 6** *(depends on Wave 5)*
- [x] 05-06-PLAN.md — input ownership and lifecycle recovery

**Wave 7** *(depends on Wave 6)*
- [x] 05-07-PLAN.md — sustained queue evidence and consumer documentation

**UI hint**: yes

### Phase 6: Qualified DMG Release and Consumer Handoff

**Goal**: As a project adopter, I want to download a qualified limited-DMG release, reproduce native integration, and assess its actual compatibility, safety, and performance evidence, so that I can judge whether it fits my project and what its limits are.
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: SHIP-01, SHIP-02, SHIP-03, SHIP-04, SHIP-05, SHIP-06, SHIP-07, SHIP-08
**Success Criteria** (what must be TRUE):

1. Clean relocated packages build/run external C/C++ consumers on the claimed host/compiler matrix without private/SDL dependencies; an adopter can follow current build, ownership/time/input/output, save recovery, support/upgrade/troubleshooting docs and a reproducible Playstead-oriented native example with honest live-integration status. (SHIP-01, SHIP-04)
2. The packaged macOS player passes automated legal-fixture load/input/video/audio/save/exit/reopen smoke; perceptual or device limitations are separately recorded. (SHIP-02)
3. Downloaded release bytes match their source revision/version/digests and include notices and release notes; only verified signing/notarization is claimed. Actual repository evidence covers required PR checks, bot CI, current-revision merge eligibility, release triggering, cache behavior, and failure propagation; stale/skipped lanes or untrusted privileged execution cannot authorize publication. (SHIP-03, SHIP-08)
4. An adopter can inspect a support ledger naming DMG revision, boot profile, mapper scope, corpus revision, executed eligible denominator, failures/exclusions, and known issues, alongside reproducible fixed-workload speed, memory/allocation, trace, build, and CI baselines with output digests, samples, environment, and uncertainty. Budgets follow measured variance; subset pass rates are not all-game compatibility. (SHIP-05, SHIP-06)
5. Maintainers can reproduce bounded loader/battery/API fuzz and boundary-regression results under applicable sanitizers; minimized findings enter fast regression coverage while longer exploration remains separately runnable. (SHIP-07)

**Plans**: 7/7 plans complete in 6 dependency-ordered waves. The 2026-10-10 freshness refresh on `gsd/phase-06-verification-refresh` (cut from `origin/main` `e328b7b` after PR #48 merged) passed 5/5 truths and SHIP-01 through SHIP-08 at `f0acb86`. Gates: Nyquist found one gap and filled it. The candidate verifier now statically requires every `GBB_VERIFIED_OUTPUT_DIR` in `release.yml` to be rooted at runner temp, with mutation and positive self-checks (`551758d`, `320fcc5`). Security closed 18/18 threats. Code review found one warning (a false reject of the unquoted `${{ runner.temp }}` YAML form); it was fixed and the re-review was clean, leaving 0 open dispositions. Regression gate: core 179/179, helper 20/20, player/package verifier 51/51, release-candidate self-test passed. These are local macOS receipts; no hosted CI has run for this revision. The 18-asset v0.1.0 reconciliation and hosted exact-tag platform receipts are historical. The frozen v0.1.0 source still contains the disclosed recursive output-directory deletion path and a checkout-relative output directory; current source fixes and tests both. See [verification](phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-VERIFICATION.md), [validation](phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-VALIDATION.md), [review](phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-REVIEW.md), and [security](phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-SECURITY.md). Signing/notarization, physical hardware, perceptual playback, and live Playstead GB integration are not claimed.
**Wave 1**
- [x] 06-01-PLAN.md — Release-please draft and trusted Linux core candidate
- [x] 06-05-PLAN.md — Loader/battery boundary regression and bounded fuzz

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 06-02-PLAN.md — Downloaded core matrix and macOS player qualification

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 06-04-PLAN.md — Support ledger and reproducible performance evidence

**Wave 4** *(ready after Wave 3 completion)*
- [x] 06-03-PLAN.md — Relocated native C example and adopter documentation

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 06-07-PLAN.md — Pre-tag release notes, legal notices, and API coverage

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 06-06-PLAN.md — Final protected tag, exact-byte release, and handoff

**UI hint**: yes

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Portable Foundation and Original ROM Tracer | 7/5 | Complete    | 2026-10-03 |
| 2. DMG CPU, Bus, and Time | 17/17 | Complete    | 2026-10-07 |
| 3. Visible Interactive DMG | 13/13 | Complete    | 2026-10-09 |
| 4. MBC1 and Safe Battery Continuation | 7/7 | Complete    | 2026-10-08 |
| 5. DMG Audio and Stable Playback | 7/7 | Complete    | 2026-10-09 |
| 6. Qualified DMG Release and Consumer Handoff | 7/7 | Complete    | 2026-10-09 |

## Execution Contract

All **35 active requirements** map exactly once to Phases 1–6 in [REQUIREMENTS.md](REQUIREMENTS.md). The latest OpenGSD freshness gate accepts all six phases, and every CPU-01–05 requirement now has Phase 2 SUMMARY credit. The strict three-source milestone evidence matrix must be rerun by the milestone audit. See [the milestone audit](v0.1-MILESTONE-AUDIT.md) for its historical pre-refresh baseline, per-requirement evidence, metadata gaps, known limits, and route. Earlier local and exact-head evidence remains recorded in phase validation reports, including Phase 4 FIFO hardening. Safety, fixture rights, documentation, install consumers, and release evidence expand as each boundary arrives. Phase 6 qualifies the completed product; it does not postpone basic safety or packaging until the end.

Automate authorized work within each phase, then inspect current verification/release/consumer evidence, update traceability and [lessons](context/LESSONS.md), triage issues/PRs, report limitations and the exact next command, and **stop**. Never auto-advance phases or milestones; keep both auto-advance flags false. Credential, hardware, or perceptual gaps must be recorded honestly with the smallest necessary human action, never converted into passing evidence. Remote/CI setup begins in Phase 1; absent access remains an explicit completion limitation.

All six phases have completed plan execution (56/56 runnable plans); Phase 2 Plan 02-15 remains superseded/non-runnable. The current canonical gate accepts all six phases. The 2026-10-10 strict three-source milestone audit at `f03e9b1` reports `tech_debt`: 35/35 requirements satisfied, 12/12 integration groups and 5/5 E2E flows wired, no blockers ([audit](v0.1-MILESTONE-AUDIT.md)). Earlier Phase 2–6 test, package, release, and exact-head evidence remains in individual validation reports. The admitted corpus remains three source-qualified derived headless reporting closures. No physical hardware, broad compatibility, perceptual output, signing/notarization, or live Playstead GB integration is claimed. Completed workflow stage: **Phase 1 — Portable Foundation and Original ROM Tracer verification freshness refresh** (2026-10-10) passed 21/21 truths and BASE-01 through BASE-08 at `ebce345`; local evidence 179/179 CTest, tracer runner pass, fixture digest match. No hosted CI is claimed for this revision. PR #41 (release 0.1.1) remains open; GitHub reports no checks, so it is not green. Quick task 261010-bz3 then credited CPU-02 (02-16) and CPU-05 (02-16, 02-17). Completed workflow stage: **Phase 2 — DMG CPU, Bus and Time verification freshness refresh** (2026-10-10) passed 5/5 truths and CPU-01–05 at `a9050df`; all six phase reports are fresh. Completed workflow stage: **v0.1 milestone audit** (tech_debt, no blockers). The owner chose to close the audit debt first: Phase 06.1 was inserted (2026-10-10). Next command: `$gsd-plan-phase 06.1`. Stop after each stage; keep the milestone executing until the owner completes it. Do not auto-advance.

### Phase 06.1: Address v0.1 tech debt: CI workflow info items and audio consumer coverage (INSERTED)

**Goal:** Close the non-blocking debt that the [v0.1 milestone audit](v0.1-MILESTONE-AUDIT.md) recorded, without widening any v0.1 claim: resolve or explicitly re-defer the deferred info review items in the CI workflows (Phase 1 `preview.yml` IN-01/IN-02, Phase 2 `ci.yml` IN-01) as one batched workflow change, and extend installed-package audio PCM consumer coverage beyond the relocated C example (C++ consumer and the Windows preview lane). Phase 3 IN-01..03 and Phase 5 IN-01 are triaged as fix-or-re-defer within the same scope.
**Requirements**: none new (hardens AUDIO-02, SHIP-01, BASE-07, BASE-08 CI evidence, plus VIDEO-04, SAVE-03, SHIP-02 player ROM-open and verified-output hardening; all 35 remain mapped to Phases 1–6)
**Depends on:** Phase 6
**Success criteria:**
1. Each audit tech-debt item is fixed with test evidence or re-deferred with a recorded reason in the phase report.
2. An installed-package consumer other than the relocated C example calls the audio PCM API, and that lane runs on Windows as well as Linux/macOS.
3. Workflow edits land in a single batched change; every phase whose verification it makes stale (1, 2, 3, 6 as applicable) is re-verified fresh before the phase closes.
4. Required checks pass on the exact merged head; no hardware or perceptual claim is added.

**Plans:** 4/8 plans executed in 6 waves

Plans:
**Wave 1**
- [x] 06.1-01-PLAN.md — C and C++ installed-consumer `audio_api_smoke()` (wave 1)
- [x] 06.1-02-PLAN.md — P3 IN-01..03 and P5 IN-01: player ROM read split plus `O_NOCTTY`, test helper and inner-withdrawal test, verified-output comment (wave 1)
- [x] 06.1-03-PLAN.md — `.github/scripts/wait-exact-head-ci.py` exact-head gate with `--self-test` (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 06.1-04-PLAN.md — single batched ci.yml + preview.yml commit, PR 1 exact-head merge, hosted readback, debt disposition (wave 2)

**Wave 3** *(blocked on Wave 2 completion)*
- [ ] 06.1-05-PLAN.md — measure staleness; refresh Phases 1–2 (wave 3)

**Wave 4** *(blocked on Wave 3 completion)*
- [ ] 06.1-06-PLAN.md — refresh Phases 3–4 (wave 4)

**Wave 5** *(blocked on Wave 4 completion)*
- [ ] 06.1-07-PLAN.md — refresh Phases 5–6 (wave 5)

**Wave 6** *(blocked on Wave 5 completion)*
- [ ] 06.1-08-PLAN.md — complete debt disposition and STATE route, docs-only PR 2 exact-head merge, freshness on main (wave 6)

**Cross-cutting constraints:**
- wait-exact-head-ci.py --self-test proves: newest same-SHA ci.yml pull_request run by run_number decides; an in-progress newest run or attempt waits; an older success never satisfies a newer failure or pending run; a truncated list (total_count > listed), persistent list/detail attempt mismatch, or deadline fails closed; a terminal failure needs two consecutive polls on the same (id, attempt).
