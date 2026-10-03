# Requirements: GabbaBoy

**Defined:** 2026-10-02
**Core value:** Run Game Boy software faithfully through a deterministic, understandable core that frontends can embed without surprises.
**Active milestone:** v0.1 — limited DMG preview. This milestone does not complete the project's Game Boy Color commitment or promise full DMG compatibility.

## v0.1 requirements

Every requirement below must map to exactly one phase. Completion needs implementation and current evidence, not only a document or proposed test. Cross-cutting safeguards start with their first applicable boundary and expand with it.

### Foundation and real guest execution

- [x] **BASE-01**: A developer can configure, build, test, and install the C17 core and headless runner using documented CMake/Ninja/CTest commands without SDL or network access after explicit dependency preparation.
- [x] **BASE-02**: An integrator can create, reset, run, and destroy independent opaque instances through a documented C API with explicit model, ownership, error, lifetime, and thread-use rules.
- [x] **BASE-03**: A caller can load a supported bounded ROM image and receive an explicit non-destructive error for truncated, oversized, unsupported, or invalid input; unsupported cartridge types are never silently guessed.
- [x] **BASE-04**: A caller can execute a tiny original GB ROM through the real CPU/bus path with a declared opcode subset and bounded run/trace result; unsupported execution is reported explicitly and no synthetic framebuffer substitutes for guest execution.
- [x] **BASE-05**: A maintainer can reproduce each admitted public fixture from a manifest recording source, license/notice, immutable revision or original source, build recipe, digest, model/boot applicability, pass protocol, and timeout.
- [x] **BASE-06**: An external C consumer and C++ consumer can link an installed `GabbaBoy::core`, execute the original tracer, and use the public header without private include paths or frontend dependencies.
- [ ] **BASE-07**: A contributor receives a required CI result that confirms the intended tests actually ran, including loader/lifecycle errors and ASan/UBSan coverage; missing fixtures, missing mandatory cases, failures, and timeouts cannot appear green.
- [ ] **BASE-08**: A contributor can use a documented remote/PR workflow and download a clearly labeled foundation-preview core/runner artifact tied to its source revision, with a basic installation smoke result and honest limitations.

### DMG CPU, bus, and time

- [ ] **CPU-01**: The declared DMG profile executes the documented base and CB SM83 instruction sets with correct tested flag, arithmetic, address, and bus-access timing behavior; illegal opcode behavior is explicit.
- [ ] **CPU-02**: The core produces the expected interrupt entry, EI delay, HALT/HALT-bug, STOP, reset, and deterministic post-boot behavior under model-applicable tests.
- [ ] **CPU-03**: Memory mapping, divider/timer edges and reload races, and disconnected serial behavior match declared DMG evidence at observable access boundaries.
- [ ] **CPU-04**: Equal timestamped inputs and emulated time produce equal supported state/output when execution is partitioned differently; LCD-off, HALT/STOP, lockup, and exhausted output capacity return within the caller's bounded contract.
- [ ] **CPU-05**: A headless run reports pass/fail/timeout/unsupported for an explicitly pinned eligible CPU/timer corpus with expected protocol and model/boot configuration, retaining enough trace evidence to reproduce failures.

### Visible interactive DMG

- [ ] **VIDEO-01**: The declared DMG profile renders background, window, and sprites with LCD/STAT transitions and a dot-sensitive fetch design demonstrated by separate composition and timing cases.
- [ ] **VIDEO-02**: OAM DMA, VRAM/OAM access restrictions, and CPU/PPU/DMA contention produce expected model-specific observable results.
- [ ] **VIDEO-03**: Timestamped joypad transitions affect the guest deterministically, including selection/interrupt behavior; the public API and SDL keyboard path exercise the same input boundary.
- [ ] **VIDEO-04**: A macOS user can launch the optional player, open a supported ROM-only image, play an original or explicitly permissioned interactive GB fixture, resize with correct aspect/integer scaling, pause, reset, and quit with actionable errors.
- [ ] **VIDEO-05**: Automated checks distinguish image composition, raster timing, and scripted gameplay outcomes, and the visible preview clearly identifies still-incomplete audio/persistence support.

### Cartridge banking and battery continuation

- [ ] **SAVE-01**: The core supports a declared set of standard MBC1 ROM/RAM/battery configurations with tested banking and enable rules, while excluded variants and other mappers produce explicit errors.
- [ ] **SAVE-02**: A frontend can import/export bounded battery data with documented cartridge identity/size rules; malformed imports leave the live state unchanged.
- [ ] **SAVE-03**: The player persists battery data with a documented atomic replacement, recovery, and concurrent-writer policy; failed writes preserve the last good save and report failure visibly.
- [ ] **SAVE-04**: An original GB fixture saves progress, exits, reopens in a fresh instance/process, and resumes behavior that depends on the previous bytes; empty/wrong-save controls prove the continuation oracle is meaningful.

### Sound and stable playback

- [ ] **AUDIO-01**: All four DMG sound channels, register behavior, and divider-driven sequencer produce the expected scoped digital APU results, with analog/revision approximations documented.
- [ ] **AUDIO-02**: A frontend receives deterministic bounded PCM with documented format, sample-rate/resampling policy, buffer lifetime, and backpressure behavior; stepping does not allocate or silently lose required output.
- [ ] **AUDIO-03**: The macOS player provides paced sound and volume control without changing guest clock semantics, with bounded queues and measured underrun/overrun behavior during sustained scripted play.
- [ ] **HOST-01**: Keyboard and basic controller input remain usable across focus loss and disconnect/reconnect; the guest cannot retain a stuck pressed button after a host input reset.
- [ ] **HOST-02**: Pause/resume, reset, ROM replacement, and audio-device transitions follow documented flush/recovery rules without mixing stale video/audio/input/battery state between sessions.

### Qualified release and adoption

- [ ] **SHIP-01**: Clean, relocated release packages build and run external C/C++ consumers on the claimed host/compiler matrix, with no accidental private or SDL dependency in the core export.
- [ ] **SHIP-02**: A packaged macOS player passes an automated load/input/video/audio/save/exit/reopen smoke using legal fixtures, and any remaining perceptual or device limitations are documented separately.
- [ ] **SHIP-03**: The release workflow qualifies the exact downloaded artifact bytes against source revision/version/digests and ships notices and release notes; signing/notarization is claimed only when actually configured and verified.
- [ ] **SHIP-04**: An adopter can follow current build, API ownership/time/input/output, integration, save recovery, support, upgrade, and troubleshooting documentation, including a reproducible Playstead-oriented native consumer example and an honest live-integration status.
- [ ] **SHIP-05**: The release support ledger names the DMG revision, boot profile, mapper scope, corpus revision, executed eligible denominator, failures/exclusions, and known issues; CPU/image pass rates are not presented as all-game compatibility.
- [ ] **SHIP-06**: Reproducible fixed-workload runs establish initial speed, memory/allocation, trace overhead, build, and CI baselines with output digests, samples, environment, and uncertainty; performance budgets follow measured variance and never trade correctness for score.
- [ ] **SHIP-07**: Meaningful loader/battery/API fuzz targets and boundary regressions run under applicable sanitizers with bounded resources; minimized findings join fast regression coverage while longer exploration runs separately.
- [ ] **SHIP-08**: Required PR checks, bot-triggered CI, merge eligibility, release triggering, cache behavior, and failure propagation are exercised on the target repository; no stale revision, skipped required lane, or untrusted privileged execution can authorize publication.

## Next milestone requirements — GB/GBC breadth

These remain project commitments to refine at the next milestone. They are not hidden additions to v0.1, and the next milestone must not start automatically.

- **CGB-01**: Add a named CGB silicon profile, native color mode, and DMG compatibility mode with mode-specific boot/register behavior.
- **CGB-02**: Implement CGB CPU speed switching and clock-domain interactions, WRAM/VRAM banking, palettes, sprite priority, and general/HBlank DMA with model-qualified tests.
- **CGB-03**: Ship a downloadable CGB-capable player and headless corpus evidence with legal interactive color fixtures and scoped compatibility claims.
- **CART-01**: Add tested MBC2, MBC3, and MBC5 variants plus host-mediated rumble where applicable; expand the support ledger per controller.
- **RTC-01**: Implement MBC3 RTC latching, halt/carry/day behavior, injected elapsed time, persisted catch-up, and negative/overflow/clock-rollback policy with deterministic checks.
- **STATE-01**: Add transactional versioned native save states covering hidden in-flight CPU/bus/PPU/DMA/APU/timer/cartridge/input state and exact continuation equivalence; preserve good disk battery data under explicit restore policy.
- **INT-01**: Qualify the real Playstead adapter against its current contract and add libretro if its integration value is demonstrated; keep native API semantics intact.

## Later candidates

BESS/save interchange, link cable and deterministic linked execution, SGB/SGB2, MGB/other DMG/CGB revisions, Camera/Printer/IR, MBC7/tilt/HuC controllers, GBS playback, richer debugging, rewind/runahead, web/mobile ports, and measured platform-specific optimizations. Details and triggers: [FUTURE-MILESTONES.md](context/FUTURE-MILESTONES.md).

## Out of scope

| Feature or claim | Reason |
|---|---|
| NES, Neo Geo, or GBA emulation | Different hardware projects; inherited prompt examples do not change GabbaBoy scope. |
| Proprietary boot/game bundles or unlicensed public fixtures | Public automated distribution needs demonstrated rights. |
| Game library service, accounts, remote telemetry backend | Optional frontend/product concerns outside this core's purpose. |
| Universal compatibility or “fastest” branding without scoped evidence | Research and subset pass rates do not establish those claims. |
| Premature JIT, generic plugin/bus frameworks, blanket abstractions | Add complexity only after concrete profiling or integration need. |
| Stable 1.0 API/ABI or long-term snapshot compatibility in v0.1 | Contracts need actual adopter and continuation evidence first. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| BASE-01 | Phase 1 | Complete |
| BASE-02 | Phase 1 | Complete |
| BASE-03 | Phase 1 | Complete |
| BASE-04 | Phase 1 | Complete |
| BASE-05 | Phase 1 | Complete |
| BASE-06 | Phase 1 | Complete |
| BASE-07 | Phase 1 | Pending |
| BASE-08 | Phase 1 | Pending |
| CPU-01 | Phase 2 | Pending |
| CPU-02 | Phase 2 | Pending |
| CPU-03 | Phase 2 | Pending |
| CPU-04 | Phase 2 | Pending |
| CPU-05 | Phase 2 | Pending |
| VIDEO-01 | Phase 3 | Pending |
| VIDEO-02 | Phase 3 | Pending |
| VIDEO-03 | Phase 3 | Pending |
| VIDEO-04 | Phase 3 | Pending |
| VIDEO-05 | Phase 3 | Pending |
| SAVE-01 | Phase 4 | Pending |
| SAVE-02 | Phase 4 | Pending |
| SAVE-03 | Phase 4 | Pending |
| SAVE-04 | Phase 4 | Pending |
| AUDIO-01 | Phase 5 | Pending |
| AUDIO-02 | Phase 5 | Pending |
| AUDIO-03 | Phase 5 | Pending |
| HOST-01 | Phase 5 | Pending |
| HOST-02 | Phase 5 | Pending |
| SHIP-01 | Phase 6 | Pending |
| SHIP-02 | Phase 6 | Pending |
| SHIP-03 | Phase 6 | Pending |
| SHIP-04 | Phase 6 | Pending |
| SHIP-05 | Phase 6 | Pending |
| SHIP-06 | Phase 6 | Pending |
| SHIP-07 | Phase 6 | Pending |
| SHIP-08 | Phase 6 | Pending |

**Active coverage:** 35/35 requirements mapped exactly once; 0 unmapped, 0 duplicates. All remain pending. Next-milestone requirements and later candidates are excluded from active coverage.

---
Last updated: 2026-10-02 after research synthesis; all requirements remain pending.
