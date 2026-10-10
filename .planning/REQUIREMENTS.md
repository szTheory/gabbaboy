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
- [x] **BASE-07**: A contributor receives a required CI result that confirms the intended tests actually ran, including loader/lifecycle errors and ASan/UBSan coverage; missing fixtures, missing mandatory cases, failures, and timeouts cannot appear green.
- [x] **BASE-08**: A contributor can use a documented remote/PR workflow and download a clearly labeled foundation-preview core/runner artifact tied to its source revision, with a basic installation smoke result and honest limitations.

### DMG CPU, bus, and time

- [x] **CPU-01**: The declared DMG profile executes the documented base and CB SM83 instruction sets with correct tested flag, arithmetic, address, and bus-access timing behavior; illegal opcode behavior is explicit.
- [x] **CPU-02**: The core produces the expected interrupt entry, EI delay, HALT/HALT-bug, STOP, reset, and deterministic post-boot behavior under model-applicable tests.
- [x] **CPU-03**: Memory mapping, divider/timer edges and reload races, and disconnected serial behavior match declared DMG evidence at observable access boundaries.
- [x] **CPU-04**: Equal timestamped inputs and emulated time produce equal supported state/output when execution is partitioned differently; LCD-off, HALT/STOP, lockup, and exhausted output capacity return within the caller's bounded contract.
- [x] **CPU-05**: A headless run reports pass/fail/timeout/unsupported for an explicitly pinned eligible CPU/timer corpus with expected protocol and model/boot configuration, retaining enough trace evidence to reproduce failures.

### Visible interactive DMG

- [x] **VIDEO-01**: The declared DMG profile renders background, window, and sprites with LCD/STAT transitions and a dot-sensitive fetch design demonstrated by separate composition and timing cases.
- [x] **VIDEO-02**: OAM DMA, VRAM/OAM access restrictions, and CPU/PPU/DMA contention produce expected model-specific observable results under the D-025 confidence-qualified software model; exact CPU-B lane/timing and universal revision parity remain unmeasured.
- [x] **VIDEO-03**: Timestamped joypad transitions affect the guest deterministically, including the documented selected falling-edge IF.4 software contract; exact CPU-B pulse qualification/sample phase remain unmeasured.
- [x] **VIDEO-04**: A macOS user can launch the optional player, open a supported ROM-only image, play an original or explicitly permissioned interactive GB fixture, resize with correct aspect/integer scaling, pause, reset, and quit with actionable errors.
- [x] **VIDEO-05**: Automated checks distinguish image composition, raster timing, and scripted gameplay outcomes, and the visible preview accurately describes its supported audio/persistence scope and remaining limitations.

### Cartridge banking and battery continuation

- [x] **SAVE-01**: The core supports a declared set of standard MBC1 ROM/RAM/battery configurations with tested banking and enable rules, while excluded variants and other mappers produce explicit errors.
- [x] **SAVE-02**: A frontend can import/export bounded battery data with documented cartridge identity/size rules; malformed imports leave the live state unchanged.
- [x] **SAVE-03**: The player persists battery data with a documented atomic replacement, recovery, and concurrent-writer policy; failed writes preserve the last good save and report failure visibly.
- [x] **SAVE-04**: An original GB fixture saves progress, exits, reopens in a fresh instance/process, and resumes behavior that depends on the previous bytes; empty/wrong-save controls prove the continuation oracle is meaningful.

### Sound and stable playback

- [x] **AUDIO-01**: All four DMG sound channels, register behavior, and divider-driven sequencer produce the expected scoped digital APU results, with analog/revision approximations documented.
- [x] **AUDIO-02**: A frontend receives deterministic bounded PCM with documented format, sample-rate/resampling policy, buffer lifetime, and backpressure behavior; stepping does not allocate or silently lose required output.
- [x] **AUDIO-03**: The macOS player provides paced sound and volume control without changing guest clock semantics, with bounded queues and measured underrun/overrun behavior during sustained scripted play.
- [x] **HOST-01**: Keyboard and basic controller input remain usable across focus loss and disconnect/reconnect; the guest cannot retain a stuck pressed button after a host input reset.
- [x] **HOST-02**: Pause/resume, reset, ROM replacement, and audio-device transitions follow documented flush/recovery rules without mixing stale video/audio/input/battery state between sessions.

### Qualified release and adoption

- [x] **SHIP-01**: Clean, relocated release packages build and run external C/C++ consumers on the claimed host/compiler matrix, with no accidental private or SDL dependency in the core export.
- [x] **SHIP-02**: A packaged macOS player passes an automated load/input/video/audio/save/exit/reopen smoke using legal fixtures, and any remaining perceptual or device limitations are documented separately.
- [x] **SHIP-03**: The release workflow qualifies the exact downloaded artifact bytes against source revision/version/digests and ships notices and release notes; signing/notarization is claimed only when actually configured and verified.
- [x] **SHIP-04**: An adopter can follow current build, API ownership/time/input/output, integration, save recovery, support, upgrade, and troubleshooting documentation, including a reproducible Playstead-oriented native consumer example and an honest live-integration status.
- [x] **SHIP-05**: The release support ledger names the DMG revision, boot profile, mapper scope, corpus revision, executed eligible denominator, failures/exclusions, and known issues; CPU/image pass rates are not presented as all-game compatibility.
- [x] **SHIP-06**: Reproducible fixed-workload runs establish initial speed, memory/allocation, trace overhead, build, and CI baselines with output digests, samples, environment, and uncertainty; performance budgets follow measured variance and never trade correctness for score.
- [x] **SHIP-07**: Meaningful loader/battery/API fuzz targets and boundary regressions run under applicable sanitizers with bounded resources; minimized findings join fast regression coverage while longer exploration runs separately.
- [x] **SHIP-08**: Required PR checks, bot-triggered CI, merge eligibility, release triggering, cache behavior, and failure propagation are exercised on the target repository; no stale revision, skipped required lane, or untrusted privileged execution can authorize publication.

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
| BASE-01 | Phase 1 | Complete — canonical verification passed 5/5; see [verification](phases/GB-01-portable-foundation-and-original-rom-tracer/01-VERIFICATION.md) |
| BASE-02 | Phase 1 | Complete — canonical verification passed 5/5; see [verification](phases/GB-01-portable-foundation-and-original-rom-tracer/01-VERIFICATION.md) |
| BASE-03 | Phase 1 | Complete — canonical verification passed 5/5; see [verification](phases/GB-01-portable-foundation-and-original-rom-tracer/01-VERIFICATION.md) |
| BASE-04 | Phase 1 | Complete — canonical verification passed 5/5; see [verification](phases/GB-01-portable-foundation-and-original-rom-tracer/01-VERIFICATION.md) |
| BASE-05 | Phase 1 | Complete — canonical verification passed 5/5; see [verification](phases/GB-01-portable-foundation-and-original-rom-tracer/01-VERIFICATION.md) |
| BASE-06 | Phase 1 | Complete — canonical verification passed 5/5; see [verification](phases/GB-01-portable-foundation-and-original-rom-tracer/01-VERIFICATION.md) |
| BASE-07 | Phase 1 | Complete — canonical verification passed 5/5; see [verification](phases/GB-01-portable-foundation-and-original-rom-tracer/01-VERIFICATION.md) |
| BASE-08 | Phase 1 | Complete — exact PR #35 required checks and package evidence verified; see [verification](phases/GB-01-portable-foundation-and-original-rom-tracer/01-VERIFICATION.md) |
| CPU-01 | Phase 2 | Complete — canonical verification passed 5/5; see [verification](phases/GB-02-dmg-cpu-bus-and-time/02-VERIFICATION.md) |
| CPU-02 | Phase 2 | Complete — canonical verification passed 5/5; see [verification](phases/GB-02-dmg-cpu-bus-and-time/02-VERIFICATION.md) |
| CPU-03 | Phase 2 | Complete — canonical verification passed 5/5; see [verification](phases/GB-02-dmg-cpu-bus-and-time/02-VERIFICATION.md) |
| CPU-04 | Phase 2 | Complete — canonical verification passed 5/5; see [verification](phases/GB-02-dmg-cpu-bus-and-time/02-VERIFICATION.md) |
| CPU-05 | Phase 2 | Complete — canonical verification passed 5/5; see [verification](phases/GB-02-dmg-cpu-bus-and-time/02-VERIFICATION.md) |
| VIDEO-01 | Phase 3 | Complete — canonical verification passed 5/5; composition and raster timing are covered by current tests; see [verification](phases/GB-03-visible-interactive-dmg/03-VERIFICATION.md) |
| VIDEO-02 | Phase 3 | Complete under D-025 software model — physical CPU-B timing/lane behavior remains unclaimed; see [verification](phases/GB-03-visible-interactive-dmg/03-VERIFICATION.md) |
| VIDEO-03 | Phase 3 | Complete under the selected falling-edge software contract — exact CPU-B pulse/sample timing remains unmeasured; see [verification](phases/GB-03-visible-interactive-dmg/03-VERIFICATION.md) |
| VIDEO-04 | Phase 3 | Complete — package smoke and current packaged-window Z press/release UAT passed; see [verification](phases/GB-03-visible-interactive-dmg/03-VERIFICATION.md) and [UAT](phases/GB-03-visible-interactive-dmg/03-UAT.md) |
| VIDEO-05 | Phase 3 | Complete — evidence classes and preview limitations are covered; see [verification](phases/GB-03-visible-interactive-dmg/03-VERIFICATION.md) |
| SAVE-01 | Phase 4 | Complete — canonical verification passed 7/7 truths; FIFO hardening passed exact-head hosted CI; see [verification](phases/GB-04-mbc1-and-safe-battery-continuation/04-VERIFICATION.md) and [validation](phases/GB-04-mbc1-and-safe-battery-continuation/04-VALIDATION.md) |
| SAVE-02 | Phase 4 | Complete — bounded transfer and non-mutation behavior verified; see [verification](phases/GB-04-mbc1-and-safe-battery-continuation/04-VERIFICATION.md) |
| SAVE-03 | Phase 4 | Complete — atomic persistence, recovery, locks, transitions, and FIFO replacement failure verified locally and on exact-head hosted CI; see [verification](phases/GB-04-mbc1-and-safe-battery-continuation/04-VERIFICATION.md) and [validation](phases/GB-04-mbc1-and-safe-battery-continuation/04-VALIDATION.md) |
| SAVE-04 | Phase 4 | Complete — fresh-process continuation and negative controls verified; see [verification](phases/GB-04-mbc1-and-safe-battery-continuation/04-VERIFICATION.md) |
| AUDIO-01 | Phase 5 | Complete |
| AUDIO-02 | Phase 5 | Complete |
| AUDIO-03 | Phase 5 | Complete |
| HOST-01 | Phase 5 | Complete |
| HOST-02 | Phase 5 | Complete |
| SHIP-01 | Phase 6 | Complete — relocated C/C++ consumers passed on the claimed package matrix; see [verification](phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-VERIFICATION.md) |
| SHIP-02 | Phase 6 | Complete — packaged macOS scripted player smoke passed; physical/perceptual behavior remains unqualified |
| SHIP-03 | Phase 6 | Complete — published v0.1.0 inventory reconciled 18/18 assets to source and digests |
| SHIP-04 | Phase 6 | Complete — adopter docs and relocated Playstead-oriented example verified; no live GB adapter is claimed |
| SHIP-05 | Phase 6 | Complete — versioned support ledger and source-bound sidecar verified |
| SHIP-06 | Phase 6 | Complete — measured performance receipt verified; budgets remain advisory |
| SHIP-07 | Phase 6 | Complete |
| SHIP-08 | Phase 6 | Complete — exact-head/release gates and publication-order negatives verified |
| CGB-01 | Next milestone | Deferred |
| CGB-02 | Next milestone | Deferred |
| CGB-03 | Next milestone | Deferred |
| CART-01 | Next milestone | Deferred |
| RTC-01 | Next milestone | Deferred |
| STATE-01 | Next milestone | Deferred |
| INT-01 | Next milestone | Deferred |

**Active coverage:** All 35 active requirements are mapped exactly once and appear in their phase verification reports. The strict three-source matrix score of 15/35 is historical and predates the Phase 3 and Phase 5 refreshes. Current OpenGSD freshness status accepts all six phases (refreshed 2026-10-10), and Phase 2 SUMMARY metadata credits every CPU-01–05 requirement (quick task 261010-bz3). The traceability checkboxes retain prior implementation completion; the milestone audit must recompute the matrix. No active requirement is orphaned; next-milestone items remain excluded.

**Next-milestone traceability:** 7/7 GB/GBC breadth commitments are mapped to the next milestone and remain outside the active v0.1 count.

---
Last updated: 2026-10-09 after the Phase 5 canonical verification refresh. The 15/35 strict three-source score is historical; refresh Phase 3 and Phase 6, reconcile Phase 2 SUMMARY metadata, then recompute.
