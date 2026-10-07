# Phase 2: DMG CPU, Bus, and Time - Context

**Gathered:** 2026-10-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the declared bootless DMG-CPU-B profile's documented CPU instruction, interrupt, CPU-visible bus, timer, and disconnected-serial behavior with deterministic, bounded execution. Add reproducible headless qualification for scoped CPU/timer diagnostics. Preserve the Phase 1 public run contract and use emulated time only.

This phase does not deliver visible PPU behavior, rendering, DMA arbitration, SDL input mapping, full joypad selection behavior, CGB execution, boot-ROM execution, general cartridge mapper support, or interactive play. PPU and DMA behavior belong to Phase 3. The Phase 1 tracer remains narrow; its `$A000` fixture RAM behavior is not hardware mapping evidence.

</domain>

<decisions>
## Implementation Decisions

### CPU and interrupt contract
- **D-01:** Implement every documented legal base and CB SM83 opcode for the declared DMG-CPU-B profile, including flag results, arithmetic, address effects, and tested bus-access timing. Cover interrupt entry, delayed EI enable, HALT and HALT-bug behavior, STOP, reset, and deterministic post-boot state as required by CPU-01/CPU-02.
- **D-02:** Treat unused opcodes as the profile's persistent CPU lockup. Surface a distinct bounded `LOCKUP` stop result with the offending opcode and PC; reset clears the lockup. Do not silently execute an illegal opcode as a NOP or conflate it with an unsupported host feature.

### CPU-visible mapping, timer, and serial
- **D-03:** Implement explicit DMG-CPU-B decoding for the declared ROM-only cartridge and supported CPU-visible memory. Keep work RAM at `$C000–$DFFF` and its echo mapping, HRAM, and IE/IF behavior distinct. Do not back `$A000–$BFFF` with invented cartridge RAM for a ROM-only cartridge that declares none. Move the original tracer's write/read protocol to work RAM and retain a clear note that its Phase 1 external-RAM window was fixture policy. Establish exact disconnected/absent-cartridge read values from profile-qualified evidence before encoding them.
- **D-04:** Derive TIMA increments from falling edges of the selected divider signal. Represent DIV/TAC write-induced edges, delayed overflow/reload, timer interrupt, and TIMA/TMA write races as explicit timed state. Qualify these boundaries with focused owned cases and applicable hardware-verifiable tests; do not approximate timer behavior with instruction-counted periods.
- **D-05:** Model a disconnected serial line as pulled high. An internally clocked transfer shifts in high bits and completes with the disconnected-line result; an external-clock transfer remains pending until external edges are supplied. Keep test-result detection in the host runner and preserve guest instruction semantics, including ordinary `LD B,B` execution.
- Keep PPU register/display semantics, CPU access restrictions caused by display modes, and DMA arbitration outside this phase. Do not insert fake PPU values or test shortcuts to make unrelated suites pass.

### Deterministic stepping and bounded outcomes
- **D-06:** Preserve Phase 1 decision D-04: public run calls return only at instruction boundaries and preflight the full next instruction so consumed time never exceeds the caller's half-dot budget. Report an explicit no-progress result if no instruction fits. Do not expose a public mid-instruction yield; model CPU bus phases and device deadlines internally at timed boundaries. This resolves an earlier exploratory suggestion for mid-instruction public progress in favor of the already-locked API contract.
- **D-07:** Define partition equivalence over the same ordered half-dot-timestamped input events and equal actual emulated time consumed at instruction boundaries. Supported machine state and output must match across different caller partitions. Preserve unused requested time in the host caller; never use wall-clock time. Use a fixed-capacity timestamped event boundary for deterministic inputs and DMG STOP wake, while leaving SDL mapping and full JOYP behavior to Phase 3.
- **D-08:** HALT continues eligible devices and advances emulated time. STOP, lockup, no-progress, timeout, unsupported behavior, and exhausted output capacity are distinct bounded outcomes. Wake STOP only through the modeled, profile-supported input event. Output exhaustion must be explicit and must not overwrite caller storage. No LCD/frame helper may be the only progress mechanism.

### Diagnostic corpus and failure evidence
- **D-09:** Combine project-owned CPU/bus/timer cases with a curated, pinned subset of Mooneye hardware-verifiable acceptance tests. Admit each upstream case only after review for DMG-CPU-B and bootless-profile applicability. Exclude emulator-only, manual-only, PPU-dependent, boot-ROM-dependent, and revision-inapplicable cases from this phase's eligible denominator. Do not add Blargg fixtures unless redistribution rights are established for each asset.
- **D-10:** Check required ROM fixture bytes into the repository so normal qualification is offline. For every admitted case record immutable upstream revision, exact source path, license/notice, ROM digest, model and boot applicability, oracle class, expected protocol, and emulated-time budget. The runner may implement documented Mooneye breakpoint/register or serial protocols without changing core guest semantics. Missing required fixtures fail the gate.
- **D-11:** Distinguish `pass`, `fail`, `timeout`, and `unsupported`. Retain a bounded reproducible failure receipt with suite/test identity, fixture digest, exact core/runner revision, profile, boot mode, protocol, actual ticks, and eligible/executed denominator, plus recent instruction and bus/timer events. Keep core diagnostics structured, caller-owned, bounded, and unformatted; format them in the host runner.
- **D-12:** Apply the owner's dependency preference: favor small direct code and a flat dependency tree; another small copy of straightforward code is preferable to a new dependency when it avoids unnecessary abstraction. Add a dependency only when the phase has a concrete need that outweighs its security, maintenance, and supply-chain cost. Do not add a test framework or network fetch as a requirement for ordinary tests.

### the agent's Discretion
- Choose internal CPU/bus data structures and task decomposition during research and planning, provided they preserve the decisions above, the existing public API contract, explicit ownership, bounded operations, and portable C17.
- Select individual Mooneye cases only after checking the exact upstream revision, license, protocol, and model/boot applicability; no case is automatically eligible merely because it is named by an upstream suite.
- Add focused owned tests where upstream coverage is missing, using independent expected values and clearly identified oracle classes.
- Use the smallest practical fixed-capacity event and trace structures. Avoid a generic event framework unless evidence shows the domain needs one.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product scope and requirements
- `.planning/PROJECT.md` — product identity, supported platform, and core value.
- `.planning/REQUIREMENTS.md` — CPU-01 through CPU-05 acceptance requirements and traceability.
- `.planning/ROADMAP.md` §Phase 2 — phase goal, success criteria, and Phase 3 boundary.
- `.planning/context/DECISIONS.md` — adopted architecture, profile, validation, and evidence decisions, especially D-008, D-009, D-011, D-013, D-015, and D-021.
- `.planning/context/BRIEF.md` — owner priorities and project constraints.

### Prior phase contract and verified limitations
- `.planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-CONTEXT.md` — locked public run contract D-04, caller-owned bounded trace D-05, instance ownership D-06, dependency preference, and original tracer protocol.
- `.planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-VERIFICATION.md` — Phase 1 evidence and explicit limitation that `$A000` tracer RAM is fixture policy, not hardware-qualified cartridge mapping.
- `.planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-RESEARCH.md` — Phase 1 architecture and fixture decisions that carry forward.
- `.planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-VALIDATION.md` — prior validation classification and evidence boundaries.

### Project research
- `.planning/research/INDEX.md` — research navigation and topic ownership.
- `.planning/research/SUMMARY.md` — synthesized project research and roadmap implications.
- `.planning/research/ARCHITECTURE.md` — portable core and adapter boundaries.
- `.planning/research/HARDWARE-AND-VALIDATION.md` — model qualification, bootless profile, and evidence strategy.
- `.planning/research/PITFALLS.md` — emulation and validation failure modes.
- `.planning/research/STACK.md` — selected C/build/test stack and dependency constraints.

### Implementation surfaces inspected
- `include/gabbaboy/gabbaboy.h` — public model and bounded execution API.
- `src/core/gabbaboy.c` — current core, CPU, memory, and run behavior to extend.
- `tests/test_api.c`, `tests/test_tracer.c`, `tests/CMakeLists.txt`, and `tests/expected-tests.txt` — current API and original tracer test patterns and inventory.
- `fixtures/tracer/tracer.asm` and `fixtures/tracer/manifest.json` — original fixture behavior, protocol, and provenance; update its scratch-memory address when hardware mapping is implemented.

### Primary technical and corpus references
- [RGBDS 1.0.1 SM83 opcode reference](https://rgbds.gbdev.io/docs/v1.0.1/gbz80.7) — opcode encodings, flags, and timing reference.
- [Pan Docs CPU comparison](https://gbdev.io/pandocs/CPU_Comparison_with_Z80.html) — Game Boy-specific CPU differences, including unused-opcode behavior.
- [Pan Docs Memory Map](https://gbdev.io/pandocs/Memory_Map.html) — address-space regions and echo mapping.
- [Pan Docs Timer and Divider Registers](https://gbdev.io/pandocs/Timer_and_Divider_Registers.html) — divider selection, edge behavior, and TIMA reload considerations.
- [Pan Docs Serial Data Transfer](https://gbdev.io/pandocs/Serial_Data_Transfer_%28Link_Cable%29.html) — disconnected line and internal/external clock behavior.
- [Game Boy: Complete Technical Reference, revision 184 (April 2026)](https://gekkio.fi/files/gb-docs/gbctr.pdf) — hardware-oriented cross-check for timing and model behavior.
- [Mooneye Test Suite](https://github.com/Gekkio/mooneye-test-suite) and its [MIT license](https://github.com/Gekkio/mooneye-test-suite/blob/main/LICENSE) — candidate hardware-verifiable acceptance tests and fixture rights; pin an immutable commit and review every admitted case before use.
- [Mooneye Game Boy test harness inventory](https://github.com/Gekkio/mooneye-gb/blob/master/core/tests/mooneye_suite.rs) — protocol and named-test discovery only; resolve immutable revisions and applicability in Phase 2 research.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/core/gabbaboy.c`: the existing instance-owned core is the implementation base; preserve its explicit result/error handling and bounded operations while replacing incomplete CPU and address/timing behavior.
- `include/gabbaboy/gabbaboy.h`: public C17 API and opaque instance boundary. The existing `gbb_run` instruction-boundary preflight/no-overshoot behavior is locked by Phase 1 D-04.
- `tests/test_api.c` and `tests/test_tracer.c`: existing caller-owned output, bounds, lifecycle, and guest protocol test patterns can be extended with independently expected CPU, bus, timer, and partition cases.
- `fixtures/tracer/`: an original licensed project fixture with provenance and a host-observed result protocol; move its scratch check into work RAM as the actual map is introduced.

### Established Patterns
- Portable C17, explicit instance ownership, no hidden globals or callbacks, caller-owned bounded buffers, structured statuses, and host-side formatting are established constraints.
- Normal build and tests are offline after explicit fixture preparation; existing fixtures are tracked and digest-verified.
- The declared profile is bootless DMG-CPU-B. CPU-CGB-E is a later named profile, not an implicit extension of this phase.
- Phase 1's public run method only stops at instruction boundaries, preflights complete instruction cost, and may return zero progress if the next instruction does not fit.

### Integration Points
- Extend the core's instruction execution and bus read/write paths so CPU bus phases, timer edges, serial transfer, interrupt state, and timestamped input events share one deterministic half-dot timeline.
- Extend the public bounded result and diagnostics only as required to report lockup, no-progress, STOP, timeout, unsupported cases, and output exhaustion without introducing unbounded work or hidden host services.
- Extend CTest and the headless runner for owned microcases and eligible pinned ROMs; keep ROM protocol interpretation, receipt formatting, and fixture metadata in host-side test code.
- Update the tracer's `$A000` scratch access when explicit ROM-only mapping lands; do not infer external cartridge RAM from the current fixture behavior.

</code_context>

<specifics>
## Specific Ideas

- Use real timed CPU bus phases and explicit device deadlines while keeping public results at instruction boundaries.
- Check the actual DMG-CPU-B memory behavior before choosing exact read values for unimplemented cartridge space.
- Treat Mooneye as a curated oracle: its acceptance cases, emulator-only cases, model-specific variants, and protocols are distinct evidence classes.
- Capture enough bounded recent CPU/bus/timer state for replay and diagnosis without allocating or formatting inside the core.
- Apply the owner's preference for a smaller, flatter dependency tree in every implementation choice.

</specifics>

<deferred>
## Deferred Ideas

### Reviewed Todos (not folded)
No phase-matching todos were present.

### Later-phase boundaries
- PPU mode behavior, rendering, display access restrictions, DMA arbitration, SDL key mapping, and full JOYP semantics remain in Phase 3.
- CPU-CGB-E, boot-ROM execution, additional cartridge mappers, and broader hardware families remain outside Phase 2.

</deferred>

---

*Phase: 2-DMG CPU, Bus, and Time*
*Context gathered: 2026-10-06*
