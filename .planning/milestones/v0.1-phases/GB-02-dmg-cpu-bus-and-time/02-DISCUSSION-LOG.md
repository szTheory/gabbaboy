# Phase 2: DMG CPU, Bus, and Time - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `02-CONTEXT.md`; this log preserves the alternatives considered and why the recommendations were selected.

**Date:** 2026-10-06
**Phase:** 2-DMG CPU, Bus, and Time
**Areas discussed:** CPU and interrupt contract; memory map, timer, and serial behavior; deterministic stepping and stop behavior; diagnostic corpus and failure evidence

---

## CPU and interrupt contract

| Decision | Option | Tradeoff considered | Selected |
|---|---|---|---|
| Unused opcodes | Persistent DMG-CPU-B lockup; return a distinct bounded `LOCKUP` result with PC/opcode; reset clears it | Represents the declared CPU profile and keeps the emulator from silently inventing NOP behavior. Requires a distinct result and tests for reset/lockup bounds. | ✓ |
|  | Return `UNSUPPORTED_OPCODE` as an emulator policy | Simple to expose, but conflates an emulated CPU state with host implementation incompleteness and does not model the selected profile. | |
|  | Treat unused opcodes as NOPs | Keeps execution moving, but hides a real model behavior and can make diagnostics falsely pass. | |
| Instruction coverage | All documented legal base and CB instructions, flags, address effects, and tested bus timing; required CPU-02 interrupt, EI, HALT/HALT-bug, STOP, reset, and post-boot behavior | Directly meets CPU-01/CPU-02. More demanding than a partial opcode subset, but partial coverage fails the phase's declared product contract. | ✓ |

**User's choice:** The user explicitly authorized auto-following the synthesized recommendations. The recommended DMG-CPU-B lockup behavior and roadmap-defined instruction/interrupt scope were selected.

**Notes:** The CPU specialist cross-checked opcode coverage and illegal behavior against the [RGBDS opcode reference](https://rgbds.gbdev.io/docs/v1.0.1/gbz80.7), [Pan Docs CPU comparison](https://gbdev.io/pandocs/CPU_Comparison_with_Z80.html), and the April 2026 [Game Boy Complete Technical Reference](https://gekkio.fi/files/gb-docs/gbctr.pdf). The correctness lens favors architectural behavior with explicit model qualification; the API/operations lens requires a bounded, observable stop result; the test lens calls for explicit reset and lockup cases. A silent-NOP fallback is the main adversarial footgun.

## Memory map, timer, and serial behavior

| Decision | Option | Tradeoff considered | Selected |
|---|---|---|---|
| DMG mapping | Explicit profile-qualified CPU map for the declared ROM-only cartridge; WRAM at `$C000–$DFFF` with echo, distinct HRAM/IE/IF; no invented cartridge RAM; repair tracer scratch use | Requires correcting a fixture and establishing absent-space values from evidence. It avoids turning emulator-owned Phase 1 test policy into a false hardware claim. | ✓ |
|  | Retain fixture-specific `$A000` backing as general map | Avoids changing the tracer immediately, but a ROM-only header declares no external RAM and the existing behavior is explicitly unqualified. It would encode a known test shortcut as hardware. | |
|  | Other owner specification | No alternative owner mapping requirement was supplied. | |
| DIV/TIMA | Divider-selected falling edges, DIV/TAC-induced edges, explicit overflow/reload/IF and TIMA/TMA-write race state | More precise state and focused test burden; supports CPU-visible access timing and known timer edge cases. | ✓ |
|  | Instruction-counted periodic increment | Small implementation, but wrong when divider writes or bus-phase ordering alter edges. | |
|  | Other owner specification | No alternative timer contract was supplied. | |
| Disconnected serial | Internal-clock transfers shift in pulled-high bits and complete; external-clock transfers wait for external edges; runner owns pass/fail protocol | Models line/clock behavior without adding host I/O. The runner protocol remains separate from guest instruction semantics. | ✓ |
|  | Complete every transfer immediately using a runner shortcut | Easier ROM protocol detection, but can fake guest-visible behavior and erase clock/timing distinctions. | |
|  | Other owner specification | No alternative disconnected-link behavior was supplied. | |

**User's choice:** The user explicitly authorized auto-following recommendations. The evidence-qualified map, edge-driven timer, and line-aware disconnected serial decisions were selected.

**Notes:** Bus/timer research emphasized the hardware model and CPU-visible access boundaries; the firmware/fixture lens identified the tracer's `$A000` accesses as incompatible with its ROM-only header. `01-VERIFICATION.md` already labels that behavior fixture policy. The safest correction is to use WRAM for tracer scratch, not preserve invented external RAM. The exact read behavior for cartridge space must follow evidence rather than an assumed `0xFF`. Timer research favors explicit timed overflow/reload state over instruction-counted shortcuts. For serial, guest behavior and host test protocol stay separate. The core remains free of host callbacks and I/O.

Primary references: [Pan Docs Memory Map](https://gbdev.io/pandocs/Memory_Map.html), [Pan Docs Timer and Divider Registers](https://gbdev.io/pandocs/Timer_and_Divider_Registers.html), [Pan Docs Serial Data Transfer](https://gbdev.io/pandocs/Serial_Data_Transfer_%28Link_Cable%29.html), and the [Game Boy Complete Technical Reference](https://gekkio.fi/files/gb-docs/gbctr.pdf).

## Deterministic stepping and stop behavior

| Decision | Option | Tradeoff considered | Selected |
|---|---|---|---|
| Run-call boundaries | Preserve Phase 1 D-04: instruction-boundary returns, whole-next-instruction preflight, no budget overrun, explicit no-progress result | Keeps the published bounded API coherent; callers may need to carry requested budget that was not consumed. Fine CPU bus timing must be internal. | ✓ |
|  | Expose resumable mid-instruction progress | Could consume smaller time slices and expose bus-level progress, but would change the Phase 1 public contract and expose partial instruction state to every caller. | |
|  | Other owner specification | No replacement API contract was requested. | |
| Partition equivalence | Same ordered half-dot timestamped inputs and equal actual consumed emulated time at instruction boundaries | Matches CPU-04 while respecting indivisible public instruction boundaries. Requires timestamped events and careful host budget accounting. | ✓ |
|  | Same call chunk sizes only | Easier comparison, but it does not verify equivalent execution under different partitions as CPU-04 requires. | |
|  | Other owner specification | No alternative determinism criterion was supplied. | |
| Idle, STOP, lockup, and output exhaustion | Distinct bounded states/results; HALT advances eligible devices/time; STOP wakes on modeled DMG event; output capacity is explicit and non-overwriting | Requires separate state transitions and results, but callers can distinguish guest behavior from timeout, no progress, and host output limits. | ✓ |
|  | Treat every idle state as timeout | Simpler runner, but conflates legal guest states and can produce false test failures or unbounded polling. | |
|  | Other owner specification | No alternative stop behavior was supplied. | |

**User's choice:** The user explicitly authorized auto-following recommendations. The already-locked Phase 1 contract wins over an earlier exploratory mid-instruction suggestion; the CPU specialist's internal timed-phase recommendation is retained.

**Notes:** The determinism/bounds specialist considered public progress options, and the API compatibility lens rejected changing D-04. The architectural compromise is internal timed bus phases and device deadlines with public instruction-boundary returns. The input boundary is limited to the fixed-capacity timestamped events needed for partition invariance and STOP wake; full JOYP and SDL behavior remain Phase 3. Host wall time is not emulated time. Anti-patterns to guard against include overrun to avoid zero progress, hidden host-clock dependence, treating HALT as a timeout, and output truncation/overwrite.

## Diagnostic corpus and failure evidence

| Decision | Option | Tradeoff considered | Selected |
|---|---|---|---|
| CPU/timer corpus | Owned independent microcases plus a pinned, curated Mooneye hardware-verifiable acceptance subset, admitted per DMG-CPU-B/bootless applicability | Stronger oracle diversity and hardware grounding, with curation and fixture maintenance cost. | ✓ |
|  | Owned cases only | Keeps licensing and fixture surface small, but gives less independent hardware qualification. | |
|  | Broad upstream fetch during test runs | Reduces repository fixture bytes, but adds network instability, supply-chain exposure, and non-reproducible inputs to routine tests. | |
|  | Other owner specification | No alternative corpus was required. | |
| Fixture/protocol | Vendored exact bytes for offline use with immutable source revision, path, notice, digest, model/boot profile, oracle class, protocol, and emulated timeout | Adds reviewed data to the repository; provides stable, auditable, network-independent qualification. `LD B,B` remains normal guest execution. | ✓ |
|  | Download pinned bytes during tests | Smaller checkout, but tests now require a network and external availability. | |
|  | Other owner specification | No alternative fixture policy was supplied. | |
| Failure evidence | Separate pass/fail/timeout/unsupported plus a bounded receipt with provenance, profile, protocol, ticks, denominator, and recent CPU/bus/timer events | Uses bounded storage and extra metadata, but makes failures reproducible without core allocation or formatting. | ✓ |
|  | Final status and PC only | Lowest implementation cost, but often insufficient to identify timing/order failures or reproduce an upstream case. | |
|  | Other owner specification | No alternative evidence policy was supplied. | |

**User's choice:** The user explicitly authorized auto-following recommendations. Select only case-reviewed Mooneye hardware-verifiable tests and authored independent microcases; vendor approved bytes and preserve bounded failure evidence.

**Notes:** The corpus/trace specialist distinguished Mooneye acceptance tests from emulator-only, manual, revision-specific, and protocol-dependent cases. The corpus security/maintenance lens requires an immutable revision, digest, rights notice, offline operation, and no unnecessary dependency or test framework. The oracle lens excludes PPU/boot-ROM tests from Phase 2's denominator and treats each case's model applicability explicitly. Blargg assets remain excluded until redistribution rights are established. The host runner may observe the documented Mooneye protocol; core instruction semantics are never patched to satisfy a harness. The immutable commit and exact eligible case list are research/planning inputs and must be resolved before fixture admission.

Primary references: [Mooneye Test Suite](https://github.com/Gekkio/mooneye-test-suite), its [MIT license](https://github.com/Gekkio/mooneye-test-suite/blob/main/LICENSE), and the candidate [Mooneye Game Boy test inventory](https://github.com/Gekkio/mooneye-gb/blob/master/core/tests/mooneye_suite.rs). The upstream inventory is discovery material, not a substitute for pinning and per-case review.

## Cross-cutting adversarial synthesis

Four independent specialist passes covered CPU semantics; memory map/timer/serial; deterministic stepping/bounds; and corpus/trace. The synthesis also used API compatibility, hardware qualification, test-oracle quality, portability, security/supply-chain, operations, and maintainer lenses:

- **Hardware and CPU accuracy:** qualify claims to the named DMG-CPU-B profile and applicable revision; do not generalize from a tracer or emulator-only tests.
- **Public API and integrator experience:** preserve D-04, make zero progress and guest stop states explicit, keep data caller-owned, and avoid hidden callbacks, formatting, or allocations.
- **Architecture and timing:** keep CPU/bus/device time on one half-dot timeline, represent timer races explicitly, and avoid a generic event framework without evidence.
- **Testing and reproducibility:** combine independent expected values with a narrowly eligible external oracle; compare actual consumed time; preserve protocol and fixture provenance in failures.
- **Security and maintenance:** vendor only licensed, reviewed assets; hash them; avoid runtime downloads and needless dependencies; fail closed for missing required fixture inputs.
- **Scope and product:** keep this phase headless and CPU/bus/time-focused. Rendering, DMA, broader controls, CGB, and boot ROM work stay on their roadmap boundaries.

The recurring footguns were silent illegal-opcode NOPs, invented `$A000` RAM, instruction-counted timers, serial shortcuts that change guest results, run-budget overruns, hidden wall-clock behavior, false corpus passes through test-specific core hacks, and diagnostic output that allocates or loses the earliest useful trace.

## the agent's Discretion

Internal C data structures, CPU implementation organization, and test decomposition remain open for Phase 2 research and planning. Recommendations must follow the established portable C17/instance-owned/bounded pattern and the user's preference for a smaller dependency tree. Individual upstream cases require explicit rights and model/boot/protocol review before being included.

## Deferred Ideas

- PPU rendering, display access restrictions, DMA, full JOYP selection, SDL mapping, and interactive play: Phase 3.
- CGB profile, boot-ROM execution, further mapper support, and broader hardware revisions: later phase/milestone scope.
- Blargg corpus assets: defer pending per-asset redistribution-rights evidence.
