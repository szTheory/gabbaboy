<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions


### A. Scope, consumers and dependency policy

- **D-01: Carry forward the established machine contract.** Instance-owned portable C17, the D-070 master half-dot timeline, explicit model tags, bounded work/output, transactional failed ROM replacement, and the frozen DMG baseline remain constraints. HDMA is guest hardware behavior behind `gbb_run`/`gbb_run_ex`; callers need no DMA getter, callback, flag, new stop reason, or new ABI field.
- **D-02: Prefer small local code over another dependency.** The owner's preference is “another copy and paste is better than another dep.” Prefer original, direct helpers and modest local duplication over a framework or enlarged dependency tree. Reuse an existing helper when its semantics actually match. Any necessary new dependency needs a concrete capability, total transitive/licensing/maintenance cost, and a simpler alternative comparison; it is permitted when justified. Copied third-party material still needs compatible rights and attribution. This is a durable project default, not a reason to duplicate complex algorithms or import unaudited code.
- **D-03: Preserve whole-instruction public stepping unless research proves a concrete conflict.** The header currently promises full-cost preflight and instruction-boundary traces. There is no resumable instruction cursor. Do not silently return mid-instruction or pretend that facility exists. D-09 is a blocking design-evidence gate before the scheduler mechanism is locked; it is research work, not a request for routine owner verification. Internal names, state layout and plan granularity remain planner discretion.

### B. Register and transfer behavior

- **D-04: Keep guest registers and internal cursors distinct.** Mask source/destination low nibbles; constrain the destination to VRAM. FF51–FF54 remain write-only to the CPU, with deterministic `$FF` reads labeled **POLICY**, not hardware-established readback. Internal cursors advance so repeated DMA operations use the researched continuation behavior. Do not expose internal cursors as readable registers because old milestone prose calls them “live counters.” Update the visibility table, its expectations and docs together; preserve DMG and CGB-compat behavior.
- **D-05: Explicit bounded register state.** FF55 encodes 1–128 blocks of 16 bytes. Track active/waiting/transferring/completed/cancelled states and remaining work without underflow or an unbounded copy loop. Completion reads `$FF`; the active bit and count must be checked through real guest reads. Research fills the complete write-during-active/cancel/restart table; a write latch and an actual transfer counter need not be the same field.
- **D-06: Adopt the precise SameSuite start/cancel cases as software-model behavior.** Both `hdma_lcd_off` and `hdma_mode0` write `$83`, expect one initial block and active read `$02`, cancel with `$00`, then expect `$80`. SameBoy reloads the low-bit count before cancellation and agrees. Adopt that tested sequence, explicitly tagged **UNKNOWN / author-test plus emulator differential** for CGB-E. Pan Docs instead describes retained remaining-length readback and warns against starting in mode 0; retain that contradiction in docs and evidence. Do not claim this settles physical CGB-E behavior, invent `$82` to match prose, or patch an upstream expected result. Research other cancellation values and restart cases rather than generalizing without checking.
- **D-07: Separate the initial kick from ordinary HBlank scheduling.** Support the one-block initial kick in D-06. Subsequent ordinary HBlank blocks require a genuine visible-line mode-0 entry; no VBlank transfers, repeated mode-0 level triggers, or synthetic LCD-off “HBlank.” An LCD-off start must not silently drain all 128 blocks. LCD disable/enable while already armed requires its own researched transition rule and test; do not infer it from the initial-start fixture.

### C. Time, bounded scheduling and bus access

- **D-08: DMA data transfer stays on master time.** The documented nominal block data duration is 64 half-dots at either CPU speed; CPU-side timers/serial/DIV retain Phase 12 scaling while PPU/APU/RTC keep their domains. Research must independently settle startup/teardown, byte or pair cadence, and sampling phase. Do not borrow an extra M-cycle or fit a magic constant to a single ROM. The committed timing discriminator must demonstrate what offsets it detects and disclose any undetected window.
- **D-09: Resolve the in-flight-instruction trap before choosing the implementation.** `advance_devices_to` runs inside CPU bus accesses. A visible HBlank may arrive between a CB memory read/write or the two writes of `LD (a16),SP`. Merely setting a flag lets subsequent accesses escape the steal; synchronously completing DMA can exceed the nominal preflight, audio reserve, or reported consumption. Planning research must compare a pending trigger at an evidenced safe boundary with bounded forecast/reservation or narrowly persisted execution state if necessary. Use a focused scratch prototype and discriminating cases to choose the smallest coherent model. Required invariants are `master_time_delta == consumed_half_dots <= budget`, preserved bus/IRQ order, bounded trace/audio output, and partition equivalence. No source inspected here establishes the exact sub-instruction steal point: label that boundary **UNKNOWN** until justified. Preserve the current public contract where feasible; document any unavoidable semantic change before implementation rather than hiding it in helpers. A generic CPU/event-engine rewrite is not pre-authorized by this uncertainty.
- **D-10: Preserve independently ending stall causes.** Manual HALT, STOP sleep, a speed-switch pause and an HDMA block steal have different rules. Keep speed-switch remainder and DMA progress independently representable, whether separate fields or equivalent composite state. A pending IRQ that ends a speed pause must not erase an HDMA steal; completing DMA must not call speed-only realignment. Serial addition of delays is allowed only if supported by the selected model, not as an accidental result of one exclusive countdown.
- **D-11: Use a narrow transfer access path.** HDMA source dispatch should share reviewed mapper/WRAM storage helpers, while destination writes use the selected VRAM bank through a transfer path. CPU `read8`/`write8` impose CPU lockouts; OAM DMA has a different source envelope. Reusing either wholesale would import unrelated behavior. Avoid a generalized initiator/vtable framework. Define bank sampling and same-half-dot ordering explicitly; preserve existing input/timer/APU/OAM/PPU ordering unless a concrete HDMA collision justifies a documented amendment.

### D. Edges, lifecycle and hostile guests

- **D-12: Address ranges are emulated addresses, never unchecked host pointers.** Cover ROM, cartridge RAM and WRAM sources through established mapping. Research source-window/bank crossings, disabled or absent cartridge RAM, and VRAM/echo/OAM/I/O/HRAM source behavior separately. Unknown hardware “garbage” is not permission to read arbitrary host memory or synthesize a universal byte. Prefer the established fail-closed behavior where evidence runs out; record the exact deterministic stop/prefix-mutation policy before implementation. No peripheral side effects should arise from an accidental CPU I/O read path.
- **D-13: Treat destination overflow as an explicit transition.** No host write may escape the selected 8 KiB bank. Research early termination and FF55/cursor status; current primary documentation leaves overflow register state unresolved. A safe, named policy or unsupported disposition is acceptable for an unqualified case; silent wrap and an unqualified hardware claim are not. Boundary tests must distinguish `$9FF0` from a valid interior destination, and must examine both data and post-transfer state.
- **D-14: Exercise low-power and competing DMA behavior deliberately.** Manual HALT pauses new ordinary HBlank transfers and wake resumes according to the selected rule. Use real guest interrupt dispatch, not a helper invocation. Research already-started blocks, IME on/off, pending IF/IE, STOP sleep, both speed-switch directions/interrupt wake, and OAM DMA overlap. Keep speed-switch behavior qualified until sourced and tested. The old Phase 12 “HBlank across stall” expected-failure pin only writes FF55 after a switch; it does not exercise an armed transfer spanning the pause and cannot be relabeled as that proof.
- **D-15: Lifecycle and resource bounds are acceptance behavior.** Create, reset and successful load clear DMA progress; failed replacement loads preserve the active instance. Test zero/tiny/nonmultiple budgets, bounded audio/trace capacity, independent instances, maximum length, repeated starts/cancels, and near-`UINT64_MAX` time with no partial start on rejected headroom. Transfers must remain bounded with LCD off, a halted CPU or malicious register writes. Persist every remainder needed for equivalent split runs; save-state serialization itself remains v0.3.

### E. Evidence, fixtures and automation

- **D-16: Use a selective hybrid corpus.** The exact SameSuite scope is `dma/gbc_dma_cont`, `dma/gdma_addr_mask`, `dma/hdma_lcd_off`, `dma/hdma_mode0` at `f15645fb049a47ea235f6d2c9a033e72d8087901`, plus original contract fixtures and MagenTests D-17. Do not expand the shorthand `dma/*` into unrelated OAM bus/collision work. SameSuite is not vendored yet; add its manifests, license/notice closure, rebuild recipe, hashes, model/boot labels and executed dispositions before counting it. Existing milestone research accepts the repository X11 license for `include/hexdigits.2bpp` (G7); record that basis and CC0 `hardware.inc`, rather than inventing either a new permission gate or a hardware receipt. Use existing RGBDS 1.0.1 for this subset unless reproducibility contradicts it.
- **D-17: Admit Magen HDMA as new work.** `hblank_vram_dma` is absent from the current six-ROM manifest and reproduction script; an earlier “Admit” recommendation is not an admission receipt. Use 0.5.0/source `3f9c090f16e5a721db776febb9ba7d773e1c819c`, release SHA-256 `e8124ce687d37a2402e20af92af1299610bfbda0871d605084c0bba2bf57135c`, and the pinned MIT/CC0 source closure, verifying the actual release/rebuild equality during admission. Its all-green screen is **SameBoy-assisted differential evidence**, not a CGB-E hardware attestation. Derive a structural all-green/data predicate before pinning a digest; wrong HALT/bank/no-transfer controls must fail for the intended reason.
- **D-18: Preserve Mealybug's rights and revision boundary.** `hdma_timing-C` and `hdma_during_halt-C` at `70e88fb90b59d19dfbb9c3ac36c64105202bb1f4` include the unresolved mgblib font closure (G1). Do not vendor or fetch their bytes into required CI while G1 is open. Reuse the optional local, digest-pinned pattern; report `not-run:rights-gate-G1` when no authorized bytes are available. Any executed result names `target_revision: CGB-C`, remains informational and stays outside the CGB-E denominator. Missing/unadmitted ROMs are not expected failures. AGE presently contributes no admitted HDMA case; its metadata is precedent, not HDMA evidence.
- **D-19: Original guests must cross the real seams.** Exercise programming FF51–FF55, timing/readback, both destination banks, changing source banks between blocks, cancellation/restart and HALT/wake through CPU execution and public runs. Use private observations only to diagnose/compare hidden state. Assert guest-visible predicates and data before regression digests. At least one guest-level discriminator must fail if CPU stealing is omitted; a final image alone cannot prove a stall.
- **D-20: Shift partition, safety and oracle checks left.** Compare uninterrupted and partitioned runs at block start/last byte/end, mode-0 edges, cancel/wake, and speed-pause overlaps at both speeds, including deterministic multi-cut cases. Compare enough hidden state/event timestamps to detect lost remainders, not only final VRAM. Add bounded hostile-register seeds and deterministic fuzz regressions. Target negative controls at no/duplicate transfer, wrong bank/mask/count/cancel, no CPU steal, erroneous speed scaling, HALT gating, lost competing stall and shifted ordering. Reuse runtime-selectable mutants where valid; verify a matching positive control and the intended failure rather than accepting any crash/timeout. A real fuzz campaign is claimed only if run.
- **D-21: Reuse CI where it has recurring value.** Register meaningful checks in existing CTest/native, sanitizer, fixture-reproduction and installed/package lanes. No new service, mandatory emulator executable or separate hosted job is justified yet. Retain exact inventories and fixture/package exclusion checks. Measure added Debug-ASan and mutation-build cost; use bounded critical windows rather than a Cartesian product or huge exhaustive sweep. GB-CI-004's parallelism and timeout contracts remain in force; do not omit failing cases or inflate timeouts without diagnosis.
- **D-22: Zero routine human UAT remains the default.** D-069 and GB-GSD-014..016 apply unchanged. Plans attach executable checks and negative controls to every deliverable, including claim/doc contracts; SUMMARY `coverage:` uses the enforced block schema and `human_judgment: false` for decidable behavior. Reuse completed evidence unless covered inputs change or a concrete regression/contradiction appears. Hardware absence is a qualified limit, not a manual test assigned to the owner. Keep one-off discussion/closure checks local when recurring behavior is already gated in CI.

### F. Consumer proof, claims and stopping

- **D-23: Demonstrate the unchanged consumer path.** Installed C/C++ consumers should run a small original DMA guest with bounded partitions and a failing twin, without widening the third-party fixture install allow-list. A packaged-player smoke may reuse an original checkout fixture when it proves visible HDMA behavior; extend an existing smoke rather than create another UI flow. Keep guest/consumer safety and oracle checks meaningful; no manual screenshot approval is required.
- **D-24: Change implementation and claims together.** Update the native guide, CGB profile, support/preview docs, README, player help/limitations, workflow package descriptions and claim-contract expectations when HDMA actually lands. Remove only the HDMA limitation established by this phase. Preserve mode-3, APU, hardware and game-compatibility qualifications. Migrate relevant Phase 12 mutation anchors and disposition mirrors atomically, retaining their sensitivity; do not delete controls to make a refactor green.
- **D-25: Stop at the requested stage and keep the route durable.** This invocation completes **Phase 13 discussion** only. Next is **Phase 13: CGB HDMA, planning**, `/gsd-plan-phase 13`, with DEEP research using this context. Do not skip research because discussion browsed sources; no `13-RESEARCH.md` or plan is produced here. Both auto-advance flags stay false. Phase 14: CGB-E Model Qualification and Corpus remains unstarted. A later Phase 13 execution still requires reviewed/tested exact-head PR checks before merge and the normal phase pause.

### the agent's Discretion


Names, helper placement, compact original fixture layout, economical mutant grouping and plan sizing are delegated. D-06 is an adopted model choice, not an unresolved owner question. D-08..D-15 assign concrete technical evidence gaps to planning research. Reopen a locked choice only for a contradictory test/source, failed prototype, changed requirement or owner direction; preserve the old provenance and state the narrow amendment. Stop expanding the decision matrix when another lens adds no new observable behavior, risk or acceptance discriminator. No broad ecosystem/dependency survey or automatic next-stage loop is needed.
</decisions>

<canonical_refs>
## Canonical References

Downstream agents must read these relevant sections before planning/implementation. Paths are repository-relative; external links are pinned primary sources. Milestone research marked `[VERIFY]` remains provisional and does not override this context or current code.

### Scope, memory and prerequisites
- `AGENTS.md` — workflow, bounded core, rights, automation and phase stops.
- `.planning/ROADMAP.md` §Phase 13 and `.planning/REQUIREMENTS.md` CGB-07 — fixed scope and success criteria.
- `.planning/PROJECT.md` — consumer/product boundaries.
- `.planning/context/DECISIONS.md` — D-009, D-015, D-025, D-069..075, D-081..095 and D-096.
- `.planning/context/LESSONS.md` — GB-CI-004, GB-CGB-005/008/009/011, GB-GSD-014..016.
- `.planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-CONTEXT.md` — visibility/banking; `.planning/phases/GB-11-cgb-colour-rendering-and-player-colour/11-CONTEXT.md` — colour/PPU deferral and fixture patterns.
- `.planning/phases/GB-12-cgb-double-speed/12-CONTEXT.md`, `.planning/phases/GB-12-cgb-double-speed/12-RESEARCH.md`, `.planning/phases/GB-12-cgb-double-speed/12-VERIFICATION.md` — clock/stall behavior and qualified evidence; completed UAT is not reopened.
- `.planning/research/v0.2/ARCHITECTURE.md` §HDMA, `.planning/research/v0.2/PITFALLS.md` V2-03/05/21/22, `.planning/research/v0.2/STACK.md`, `.planning/research/v0.2/SUMMARY.md` G1/G7 — earlier hypotheses, pins and rights basis. D-04 supersedes suggestions of CPU-readable live cursors; D-06 supersedes a blanket wait-until-next-HBlank rule for the two start cases. Exact timing and invalid-source fallbacks remain research, not borrowed facts.

### Implementation and recurring contracts
- `src/core/gabbaboy.c`, `include/gabbaboy/gabbaboy.h` — current state, timing and whole-instruction contract.
- `tests/test_dma.c`, `tests/test_cgb_speed_internal.c`, `tests/test_cgb_partition.c`, `tests/test_cgb_visibility.c`, `tests/test_magentests.c`, `tests/fuzz_core.c` — seam, partition and oracle patterns.
- `tests/consumers/c/main.c`, `tests/consumers/cpp/main.cpp`, `tests/CMakeLists.txt`, `tests/expected-tests.txt`, `cmake/P12Mutants.cmake`, `tests/scripts/verify-speed-domains.py` — consumer/inventory/mutation coupling.
- `fixtures/magentests/manifest.json`, `fixtures/magentests/SOURCES.md`, `fixtures/magentests/ELIGIBILITY.md`, `tests/scripts/reproduce-magentests.sh`, `fixtures/age/ELIGIBILITY.md` — actual admission status and reproduction precedent.
- `tests/external/cgb-speed-dispositions.json`, `tests/external/cgb-ppu-dispositions.json`, `docs/model-gates.md`, `docs/cgb-profile.md`, `docs/native-integration.md` — dispositions, model tags, current claims and API contracts.
- `docs/support/unreleased.md`, `docs/preview.md`, `README.md`, `src/player/limitations.h`, `src/player/main.c`, `.github/workflows/ci.yml`, `.github/workflows/fixture-repro.yml`, `.github/workflows/preview.yml`, `cmake/PreviewPackageSmoke.cmake` — delivery and claim surfaces.

### External primary sources inspected, read rather than copied
- [Pan Docs CGB registers at 0191af06ac49661587dcde3d57a241a626b8df75](https://github.com/gbdev/pandocs/blob/0191af06ac49661587dcde3d57a241a626b8df75/src/CGB_Registers.md) — masks, block rate, ordinary HBlank/HALT and documented uncertainties.
- [SameBoy memory.c at 26a56bd6a122a6318a456abd80558408742d5adf](https://github.com/LIJI32/SameBoy/blob/26a56bd6a122a6318a456abd80558408742d5adf/Core/memory.c), [display.c](https://github.com/LIJI32/SameBoy/blob/26a56bd6a122a6318a456abd80558408742d5adf/Core/display.c), [sm83_cpu.c](https://github.com/LIJI32/SameBoy/blob/26a56bd6a122a6318a456abd80558408742d5adf/Core/sm83_cpu.c) — selected differential model and scheduling comparison, not silicon proof.
- [SameSuite DMA at f15645fb049a47ea235f6d2c9a033e72d8087901](https://github.com/LIJI32/SameSuite/tree/f15645fb049a47ea235f6d2c9a033e72d8087901/dma), especially [hdma_lcd_off.asm](https://github.com/LIJI32/SameSuite/blob/f15645fb049a47ea235f6d2c9a033e72d8087901/dma/hdma_lcd_off.asm) and [hdma_mode0.asm](https://github.com/LIJI32/SameSuite/blob/f15645fb049a47ea235f6d2c9a033e72d8087901/dma/hdma_mode0.asm) — exact expected sequences.
- [MagenTests HDMA at 3f9c090f16e5a721db776febb9ba7d773e1c819c](https://github.com/alloncm/MagenTests/tree/3f9c090f16e5a721db776febb9ba7d773e1c819c/src/hblank_vram_dma) and [author README](https://github.com/alloncm/MagenTests/blob/3f9c090f16e5a721db776febb9ba7d773e1c819c/README.md) — guest initialization, screen result and oracle ancestry.
- [Mealybug DMA at 70e88fb90b59d19dfbb9c3ac36c64105202bb1f4](https://github.com/mattcurrie/mealybug-tearoom-tests/tree/70e88fb90b59d19dfbb9c3ac36c64105202bb1f4/src/dma), mgblib submodule `1d9045a4b4cbd1ec5223e672a1cef965e9fcd194` — CGB-C scope and G1 limitation, no bytes admitted.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable assets and patterns
- `advance_devices_to` owns master time, input/device ordering and audio capacity; the current speed-stall branch bounds work but contains switch-specific wake/realignment assumptions.
- `dma_source_read`, `cart_read` and `wram_byte` demonstrate storage dispatch; HDMA needs its own access semantics, not the CPU lockouts or the entire OAM source map.
- `tests/test_dma.c` compares full/split transfers including event timestamps and exact PPU/CPU collisions; `tests/test_cgb_partition.c` compares hidden state; the fuzz harness checks time conservation and budgets.
- Existing fixtures, structural Magen pixel predicates, mutation helpers, installed consumers, exact CTest inventories and package exclusion scans already support the proposed checks.

### Integration points and traps
- State/reset: add integer DMA progress beside instance-owned speed/DMA state; reset/create/successful load and failed-load preservation all matter.
- Registers: FF51–54 are presently inert; FF55 reads `$FF` and CGB writes fail closed. `io_visibility`, its mirror and model-gate records must evolve together.
- Genuine visible HBlank is the mode 3→0 path in `ppu_transfer_dot`; `ppu_set_mode(0)` is also called for LCD-off and is insufficient as an unqualified trigger.
- Timed CPU bus operations call `advance_devices_to` during synchronous `execute`; there is no existing instruction-resume state. Nominal cost is currently `uint8_t` and accounted after execution; widened/reserved transfer time must not truncate into that cost.
- The one exclusive `cpu_stall_kind` and countdown cannot by themselves preserve overlapping independently wakeable causes. Speed-only realignment on generic completion is a specific regression risk.
- `cmake/P12Mutants.cmake` requires unique anchors. `verify-speed-domains.py` forbids speed reads in PPU/APU/RTC functions: preserve the separation or amend a proven, narrow contract; do not disable the scan.
</code_context>

<specifics>
## Specific Ideas

Treat a block steal like a persisted device transaction: retain progress and event order across calls, while keeping the native API predictable. Useful discriminators include HBlank between the two `LD (a16),SP` writes, cancel `$00` after active `$02`, the last VRAM block, HALT spanning several HBlanks, and IRQ wake during a speed pause with DMA pending. These are investigation/acceptance examples, not a prewritten implementation plan.

Breadth was limited to relevant hats: emulator/hardware timing, C ownership/security, graphics/PPU ordering, native consumers/product claims, fixture rights, QA/oracle independence, DevOps cost and maintainability. Web UI, distributed infrastructure and unrelated language ecosystems add no requirement here.
</specifics>

<deferred>
## Deferred Ideas

- Phase 14: CGB mode-3/window and APU/I/O qualification, broad CGB-E corpus, existing STOP/OAM and separate-bus gaps unless a narrow HDMA prerequisite is demonstrated.
- Phase 15: rights-clear CGB game acceptance, broader support ledger and release.
- v0.3: transactional serialization of in-flight DMA/CPU state and Playstead integration.
- Future demonstrated host need: DMA inspection UI/getter, generic scheduler/bus abstraction, additional silicon profiles.
- G1 rights closure: only revisit on new rights evidence; no external message is authorized by this discussion.
</deferred>

---
*Phase: 13-CGB HDMA*
*Context gathered: 2026-10-14*

### Deferred Ideas (OUT OF SCOPE)


- Phase 14: CGB mode-3/window and APU/I/O qualification, broad CGB-E corpus, existing STOP/OAM and separate-bus gaps unless a narrow HDMA prerequisite is demonstrated.
- Phase 15: rights-clear CGB game acceptance, broader support ledger and release.
- v0.3: transactional serialization of in-flight DMA/CPU state and Playstead integration.
- Future demonstrated host need: DMA inspection UI/getter, generic scheduler/bus abstraction, additional silicon profiles.
- G1 rights closure: only revisit on new rights evidence; no external message is authorized by this discussion.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|---|---|---|
| CGB-07 | CGB software can use general-purpose and HBlank VRAM DMA with CPU stall, cancel, HDMA5 readback and HALT interaction, bounded per run. | Existing synchronous CPU/PPU seam and a reproducible D09 probe; implementation-ready pending-trigger policy, source-backed state table and test architecture. Physical timing remains unknown. |
</phase_requirements>

# Phase 13: CGB HDMA — Research

**Researched:** 2026-10-14
**Domain:** Portable C17 Game Boy Color CPU, PPU and VRAM DMA scheduling
**Confidence:** HIGH for repository seams and prototype observations; MEDIUM for pinned docs and author-test behavior; LOW / UNKNOWN for CGB-E sub-instruction timing and unresolved hardware edges.

## Summary

Keep HDMA inside the current public run path with bounded instance-owned state, preserving whole-instruction preflight and instruction-boundary traces. The PPU advances inside synchronous CPU bus operations, so HBlank may begin before a later bus access in the same instruction. A focused prototype demonstrates that seam in two real instructions and has matched no-edge controls. It does not implement a scheduler or measure hardware.

**Primary recommendation:** latch one eligible visible HBlank transition during execution, then service its steal at the next whole-instruction safe boundary. Keep DMA progress independent of speed-switch/manual low-power state and do not add a resumable CPU cursor or public DMA API. This boundary is a software POLICY approximation. The first implementation tracer must execute a real transfer through that choice and prove time conservation, output bounds, guest-visible order and split-run equivalence before broader implementation work.

No production source, fixtures, plan, STATE, or config was changed. No Phase 13 DMA test was run. Phase 12 remains closed.

## Project Constraints (from AGENTS.md)

- Support Game Boy and Game Boy Color only; preserve the original portable C core, instance ownership, explicit failure behavior and bounded public operations.
- Keep host timing, filesystem, UI, audio devices and environment configuration in adapters. Prefer small direct code and require evidence before performance complexity.
- Guard guest-controlled address, size, time, allocation and work boundaries against overflow, truncation and partial mutation; do not serialize raw C structs.
- Qualify tests by evidence type and model applicability. Third-party fixtures need rights and digests. Do not add ROMs or private data prohibited by the project.
- Every deliverable needs automated verification and a negative control. Routine verify-work UAT should require zero human checkpoints; use the enforced SUMMARY coverage block schema.
- Use installed OpenGSD, keep auto-advance flags false, and stop at this phase handoff. Parent owns commit and next planning stage.
- Update product/support claims alongside implementation and never assert CGB-E physical measurements without hardware evidence.

## Architectural Responsibility Map

| Capability | Primary tier | Secondary tier | Rationale |
|---|---|---|---|
| FF51–FF55 transfer state and CPU stalls | Portable C core | — | Guest behavior belongs behind the existing run API. |
| HBlank trigger and VRAM write | Core PPU/device scheduler | CPU core | PPU supplies the trigger; transfer consumes master time and writes selected VRAM. |
| Source map and overflow safety | Core mapper/storage | — | Use emulated address ranges and established storage mapping, not host pointers or CPU I/O side effects. |
| Guest fixtures/oracles | Native test and fixture layer | Core | Tests must execute guest code and assert guest-visible effects. |
| Installed consumers and support claims | Package tests/docs | Core | Preserve public ABI and state evidence limits accurately. |

## Standard Stack

| Component | Current evidence | Planned use |
|---|---|---|
| Portable C core | C17, existing implementation | DMA state, registers, access path and scheduling; no new production dependency. |
| CMake/Ninja/CTest | Existing presets and test registrations | Native, sanitizer, fixture and consumer validation. |
| RGBDS | Context pins 1.0.1 for SameSuite | Reproduce selected guest fixtures. Local rgbasm is 1.0.4, so use an isolated pinned tool instead. |

Environment probes found CMake 4.4.3, Ninja 1.13.2, Apple clang/clang++ 21.0.1, Python 3.14.4 and RGBDS 1.0.4. SameBoy and mGBA executables were not found on PATH. These observations do not establish supported versions. Do not install globals or add dependencies.

Alternatives: a generalized bus initiator/vtable, public DMA getters/callbacks, a resumable instruction cursor, a new CI job or mandatory emulator dependency are not warranted by current evidence. Revisit only if the first tracer falsifies the narrow policy or measured recurring value justifies added infrastructure.

## Architecture Patterns

### Bounded state and time domains

The core state currently quotes “uint8_t double_speed, cpu_stall_kind, stop_switch_pending;” and “uint32_t cpu_stall_half_dots;”; there is no HDMA state. [VERIFIED: src/core/gabbaboy.c:349-354.] Add explicit bounded transfer progress, separate guest register latches from internal cursors, and keep DMA remaining time distinct from speed-switch pause state.

The public header promises “Runs whole supported instructions”, says an instruction is “preflighted and won't start unless its full cost fits”, and traces “at instruction boundaries”. [VERIFIED: include/gabbaboy/gabbaboy.h:262-282.] Preserve this public behavior where feasible.

The core clock comments give normal T cycle as 2 master half-dots, double-speed T cycle as 1, and PPU dot as 2 half-dots. [VERIFIED: src/core/gabbaboy.c:18-35; source comments/constants inspected in this run.] Pan Docs documents 8 normal M-cycles or 16 double-speed fast M-cycles per 16-byte block; at the core clock this yields nominal 64 half-dots of data time in either speed. Startup, teardown, exact byte cadence and sample phase remain separate questions. [CITED: [Pan Docs CGB registers, pinned revision](https://github.com/gbdev/pandocs/blob/0191af06ac49661587dcde3d57a241a626b8df75/src/CGB_Registers.md).]

Timed bus reads call advance_devices_to from the CPU executor. LD (a16),SP writes at offsets 24 and 32; its decoded cost is 40. CB RLC (HL) accesses memory at offsets 16 and 24. [VERIFIED: src/core/gabbaboy.c:1713-1717, 3634, 3736-3756, 3866-3868; quotes include “advance_devices_to(m, m->instruction_start_half_dots + (offset >> m->double_speed))”, “{3,40,1}”, and bus writes at 24u / 32u.] Thus a visible PPU edge can fall between accesses before the run loop accounts the instruction cost.

### D09 probe: actual observation vs arithmetic candidates

Source-only scratch artifact: [13-D09-boundary-prototype.c](13-D09-boundary-prototype.c), SHA-256 e7edf9b8e1ac610c30fa0e2f5880d86b2f5a6c67eb01809c26606d73c76abfe3. It includes the real private core implementation, seeds synthetic private PPU state and calls the real gbb_run. From repository root:

~~~sh
mkdir -p /tmp/gb13-research-final
cc -std=c17 -Iinclude -Isrc/core .planning/phases/GB-13-cgb-hdma/13-D09-boundary-prototype.c -o /tmp/gb13-research-final/13-D09-boundary-prototype
/tmp/gb13-research-final/13-D09-boundary-prototype
~~~

Observed output:

~~~text
case=LD_a16_SP negative=0 budget=40 consumed=40 master_delta=40 edge=26 accesses=@24:C000,@32:C001
case=LD_a16_SP negative=1 budget=40 consumed=40 master_delta=40 edge=none accesses=@24:C000,@32:C001
case=CB_RLC_HL negative=0 budget=32 consumed=32 master_delta=32 edge=18 accesses=@16:C000,@24:C000
case=CB_RLC_HL negative=1 budget=32 consumed=32 master_delta=32 edge=none accesses=@16:C000,@24:C000
~~~

This is real seam evidence: a mode-3-to-0 event lands between the two real LD writes and between the CB memory read/write. Matched controls disable the FIFO event; both accesses remain and the edge disappears. It proves the trap exists in current synchronous execution, not which sub-instruction point CGB-E steals. It is not a DMA run or hardware measurement.

The scratch program also prints candidate timeline arithmetic, **not executed schedulers**:

- Pending-boundary model: LD finishes at 40, then block [40,104); CB finishes at 32, then block [32,96).
- Hypothetical cursor model: LD edge 26, block [26,90), second write at 96, finish 104; CB edge 18, block [18,82), resumed write at 88, finish 96.
- Reservation alone preserves late accesses; reserving instruction cost plus 64 leaves the existing budget-sized call with no progress.

Planning choice: use pending edge plus safe whole-instruction service first. In the first implementation tracer, execute a real transfer through the chosen branch with a matched no-trigger/no-transfer control; assert master_time_delta == consumed_half_dots <= budget, data and CPU/event order, bounded trace/audio output, and uninterrupted/partitioned equivalence. If it fails, reopen D09 narrowly before broader work. Do not cite arithmetic as a run or present the safe boundary as silicon timing.

## Source-backed state and policy table

| Area | Evidence | Research finding and planning treatment |
|---|---|---|
| Register dispatch | Current IO rows are “[0x51] = { IOC(DMG_STOP), IOC(CONST_FF), IOC(CONST_FF), IOS_PANDOCS }” through the same exact FF52–FF54 rows; FF55 is “[0x55] = { IOC(DMG_STOP), IOC_DEF(DEFERRED_W, 13), IOC(CONST_FF), IOS_PANDOCS }”. [VERIFIED: src/core/gabbaboy.c:1225-1229.] | Add CGB guest paths and update visibility/docs; preserve DMG and compatibility behavior. |
| Lifecycle | Reset clears OAM DMA/HALT/STOP/speed fields. [VERIFIED: src/core/gabbaboy.c:1417-1431; quoted assignments include cpu_stall_kind = 0u and cpu_stall_half_dots = 0u.] | Reset/new instance/successful load clear DMA; failed replacement preserves state. |
| Visible trigger | LCDC-off and visible mode-3 completion both call ppu_set_mode(m, 0); line setup distinguishes VBlank. [VERIFIED: src/core/gabbaboy.c:1932-1945, 2627-2636, 2718-2735; quote: “ppu_set_mode(m, 0)”.] | Distinguish the D-06 one-block initial kick from genuine visible 3→0 entry; no mode-0 level, VBlank, repeated or synthetic LCD-off trigger. Disable/enable while armed needs a test and declared policy. |
| Master ordering | advance_devices_to owns timeline; OAM DMA advances on cpu_tick before phase/PPU advancement. [VERIFIED: src/core/gabbaboy.c:2864-2956; quote: “if (cpu_tick) dma_advance_half_dot(m);”.] | HDMA uses master time. Preserve existing order absent a discriminating collision; same-half-dot arbitration stays UNKNOWN/POLICY. |
| Budget accounting | Whole-instruction run preflights cost then executes and adds nominal cost. [VERIFIED: src/core/gabbaboy.c:4138-4173; quote: “if (cost > budget_half_dots-result.consumed_half_dots) return result;”.] | Widen combined cost arithmetic; prevent extra DMA time from exceeding budget/audio/trace bounds or truncating nominal narrow cost. |
| Count/duration | Pan Docs: FF55 low 7 bits encode count minus one, each block is 16 bytes; nominal duration maps to 64 half-dots at either speed under core clock. [CITED: pinned Pan Docs above.] | Bound to 1..128 blocks; independently derive start/teardown/cadence. Do not call docs a CGB-E measurement. |
| FF55 write/read state matrix | Idle write bit 7 clear = GDMA; idle bit 7 set = HDMA request. The adopted initial-start cases write $83, read active $02 after the first block, then write $00 and read $80. Completion reads $FF per docs. During active HBlank, other low values and bit-7-set restart are not settled: SameBoy reloads the step count before its active-cancel branch; Pan Docs does not define active restart. Active GDMA writes are not covered by the selected SameSuite cases. [CITED: D-05/D-06 and pinned SameSuite, SameBoy, Pan Docs.] | Keep a complete explicit table in implementation tests: idle start (both modes), active GDMA write, active HBlank cancel $00, active HBlank cancel with other low values, active HBlank bit-7-set rewrite/restart, completion. Only the exact $83/$02/$00/$80 adopted sequence is locked model behavior; remaining cells are UNKNOWN until policy is selected and tested. Never imply the table is physically resolved. |
| Source map and invalid reads | Pan Docs names ROM $0000-$7FF0, cartridge RAM $A000-$BFF0 and WRAM $C000-$DFF0 source windows, ignores low source/destination nibbles, permits VRAM destinations $8000-$9FF0 and describes VRAM/echo/OAM/FEXX/I/O/HRAM source behavior as garbage or untested. OAM dma_source_read has a different envelope. [CITED: Pan Docs; VERIFIED: inspected core mapping helper.] | Map each source byte through a narrow storage path; test bank crossing and source bank changes between blocks. Prevalidate a whole 16-byte block; fail closed for unknown windows without CPU IO side effects or host OOB. Record exact prefix/status policy before implementation. |
| Destination boundary | Pan Docs says overflow stops prematurely but register state is unknown. Destination $9FF0 is a valid final block start; next cursor exceeds bank. [CITED: Pan Docs.] | No host escape. Preserve completed valid prefix; explicitly choose/test overflow status and cursor policy; no silent wrap or hardware claim. |
| Bank sampling | Pinned SameBoy samples VBK per block; it is emulator evidence, not physical evidence. [CITED: pinned SameBoy memory.c.] | Test per-block sampling as selected-model POLICY. No source here settles sample edge or same-half-dot PPU/OAM interaction. |
| HALT/STOP/speed/OAM | Pan Docs says ordinary HBlank blocks pause while manually HALTed; Magen author guest expects HALT to defer a later transfer. STOP freezes the PPU in the current project model; speed-switch pause advances master/PPU time. Core state has one existing speed stall kind/countdown (quoted above). SameBoy gates ordinary scheduling while halted/stopped and executes its block synchronously before opcode. | Distinguish (1) manual HALT: CPU halted, new ordinary HBlank admission paused until a real wake; (2) STOP: CPU/PPU sleep behavior follows existing STOP contract, armed request/remainder persists; (3) speed-switch pause: CPU pause can end on IRQ while PPU/master time progresses; keep its remainder separate from HDMA; (4) GDMA full CPU steal and (5) HDMA wait-between-blocks plus block steal. Whether a block progresses through switch pause and exact STOP/restart interaction remain POLICY/UNKNOWN. Test wake, both speed directions, STOP and OAM overlap; do not reuse Phase12 switch fixture as proof. |
| Evidence/fixture status | Four SameSuite cases authorized: dma/gbc_dma_cont, dma/gdma_addr_mask, dma/hdma_lcd_off, dma/hdma_mode0. Magen hblank_vram_dma is absent from existing six-ROM manifest. Mealybug G1 closure is unresolved and target is CGB-C. [CITED: pinned source references in CONTEXT.] | Admit only these approved sources after license/notice closure, digest, pinned RGBDS and reproducible equality. Magen is SameBoy-assisted differential, not hardware. Mealybug stays optional informational and reports not-run:rights-gate-G1 absent authorized bytes. |

## Don't Hand-Roll

| Problem | Avoid | Use |
|---|---|---|
| CPU lockouts/peripheral side effects | Reusing CPU read/write semantics wholesale | Narrow HDMA storage-source and VRAM-destination helpers. |
| Generic scheduler | Bus initiator framework or event-engine rewrite | Small explicit HDMA state and pending HBlank latch. |
| Invalid source behavior | Host pointer arithmetic or fabricated universal byte | Emulated-range checks and documented fail-closed policy. |
| Transfer safety | Guest-trusted loops and unchecked address/time math | 1..128 bounded work, checked headroom and block prevalidation. |
| Oracle confidence | Treating emulator/screenshot as hardware | Label hardware, author-test, differential, metamorphic and POLICY evidence separately. |

## Common Pitfalls

- LCD-off also sets mode 0; do not use every mode-0 call as ordinary HBlank.
- A synchronous callback can overrun instruction preflight, caller budget or reserved audio/trace output.
- Do not truncate instruction-plus-DMA cost or conflate DMA countdown with speed-switch wake/re-alignment.
- Invalid source policy must not partially mutate an accidental prefix unless that is deliberate and tested.
- Final image alone cannot establish guest data, CPU steal, register status or event order.
- Missing/unadmitted ROMs are not expected failures. Phase12 UAT is already closed; do not reopen it.

## Validation Architecture

Nyquist validation is enabled in .planning/config.json. No Phase13 HDMA test or fixture ran during research. Existing presets provide native Debug and sanitizer lanes. Exact full command from AGENTS.md: “cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error”. Preset source also includes the phase1 and phase1-asan names. [VERIFIED: CMakePresets.json:5-20, tests/CMakeLists.txt:1578.]

### Requirement-to-test map

| Req | Test behavior | Type | Status |
|---|---|---|---|
| CGB-07 | Real guest GDMA validates 16-byte data, status, CPU steal and 64-half-dot data at both speeds | Integration | First tracer needed |
| CGB-07 | Initial HBlank kick; genuine visible 3→0; no repeated, VBlank or synthetic LCD-off trigger | Integration plus negative control | Not implemented |
| CGB-07 | Chosen pending-boundary DMA path, matched no-trigger control, conservation, order, audio/trace bounds and partition equivalence | Integration | Mandatory first tracer |
| CGB-07 | HALT across HBlanks, real IRQ wake, STOP, both speed-switch directions, independent remainders | Guest integration/metamorphic | Not implemented |
| CGB-07 | $9FF0 final block, overflow/status policy, masks, source endpoints/cross-bank/disabled RAM, VBK sampling | Unit plus guest | Not implemented |
| CGB-07 | Four SameSuite cases plus admitted Magen case and structural data/pixel predicate | Differential fixture | Admission pending |
| CGB-07 | Installed C and C++ consumer run an original DMA guest with a failing twin; fixture excluded from install allow-list | Consumer integration | Harnesses exist; HDMA scenario absent |
| CGB-07 | Model/support docs and claim contracts have positive and mutated negative checks | Automated contract | Existing contracts need HDMA update |

Negative controls must fail for the intended reason: no transfer, missing/duplicate steal, wrong count/mask/source or destination bank, bad cancel/status, HBlank while halted, VBlank/LCD-off trigger, lost independent speed stall, shifted order and split-run remainder loss. Pair each mutant with a positive control; a crash or timeout alone is not evidence.

Use existing CTest/native, sanitizer, fixture-reproduction and installed-consumer lanes. Measure Debug-ASan and mutation-build cost against GB-CI-004 before considering new jobs. Update exact test inventory and package exclusions. No framework/dependency/config gap requires Wave 0. SUMMARY coverage must use block schema with id, description, human_judgment, verification items of kind unit/integration/e2e/automated_ui/other, ref and status: pass; no flow entries, ctest kind or inline comments.

## Security Domain

Security enforcement is on and ASVS level 1 is configured. Relevant risks are guest-controlled bounds and integer overflow: validate FF51–FF55-derived addresses/counts, time addition, block boundary and output capacity before mutation. OWASP ASVS v5 includes integer-overflow and input-validation controls. [CITED: [OWASP ASVS 5.0](https://github.com/OWASP/ASVS/tree/master/5.0).]

| Category | Applies | Control |
|---|---|---|
| Input validation | Yes | Validate guest addresses/counts and checked time/work arithmetic. |
| Integer overflow | Yes | Check transfer cursor, time headroom and combined budget before mutation. |
| Authentication/session/access control/cryptography | No | No such surface in this core feature. |
| Resource bounds | Yes | Bound transfer work, trace and audio output. |

## Assumptions Log

| # | Claim | Risk if wrong |
|---|---|---|
| A1 | Next whole-instruction boundary is a coherent initial software policy. | The real-transfer tracer may violate order or budget; do not lock plan beyond tracer until it passes. |
| A2 | Per-block VBK sampling is acceptable as initial model policy. | Between-block guest changes may need a different behavior; not hardware-backed. |
| A3 | Rejecting unknown-source blocks before byte mutation is the safest default. | It is a policy, not documented hardware behavior; document prefix/status. |

## Open Questions — planning dispositions

Every question has a planning disposition below. Selected software policy resolves implementation direction only; residual physical UNKNOWNs remain claim limits, with no owner UAT or hardware receipt implied. The first real-transfer tracer is pending actual execution.

| Question | Disposition | Plan and executable discriminator | Residual uncertainty |
|---|---|---|---|
| Q1: Does the first real transfer tracer preserve the public API while meeting conservation, order, output and partition invariants? | EXECUTION GATE: candidate pending-boundary policy latches a visible edge, completes late accesses, then admits DMA before IRQ dispatch or the next opcode. Expansion is blocked until real-transfer evidence passes. | 13-01 Task1: cgb_hdma_tracer_ld_sp, cgb_hdma_tracer_cb, controls, partition and outputs; both speeds, real FF51–55 writes, data/order/time/output predicates. Failure halts Task2 and all dependent plans and reopens only D-09 against the counterexample. Scratch arithmetic does not satisfy this gate. | Actual transfer has not run; physical CGB-E sub-instruction steal point remains UNKNOWN even after a software-model pass. |
| Q2: What are physical CGB-E sub-instruction steal timing, overflow FF55 status, other active-write/cancel cases and same-half-dot collision semantics? | SELECTED POLICY plus physical UNKNOWN: pending instruction boundary; legal9FF0 block then abort at widenedA000 with inactive remaining-count status; cancel with80 bitwise-OR low7, active bit7 rewrite replaces work without kick, active FF51–54/GDMA writes ignored; OAM before HDMA before PPU, per-block VBK. D-06 remains exact83/02/00/80 with the Pan Docs contradiction retained. | 13-01 seam gate; 13-02 state/address/overflow matrices and controls; 13-03 OAM-order/competing-stall controls; 13-05 matching mutation pairs. | These deterministic choices do not establish physical status/arbitration/timing. Author tests and emulator differential retain their stated provenance. |
| Q3: What startup/teardown and per-byte cadence accompany nominal64-half-dot block data? | SELECTED POLICY: sixteen byte commits at elapsed4,8,...64 master half-dots at either speed, startup/teardown0, storage sampled at commit and VBK at block admission. Nominal64 is sourced; cadence/sampling/extra overhead are unmeasured. | 13-01 real-transfer conservation; 13-02 cgb_hdma_timing_policy and controls; 13-05 signed-offset seam reports detected offsets±1,±2,±4,±8 and any blind window. | Physical cadence/startup/teardown/sampling remain UNKNOWN; sensitivity is software-test evidence, not silicon proof. |
| Q4: Which narrow behavior is required across STOP, speed-switch pause, LCD disable/enable and OAM overlap? | SELECTED POLICY: STOP freezes and preserves progress; speed pause and DMA advance concurrently with independent residuals/wake; admitted block finishes across HALT; LCD disable clears unadmitted edge but retains armed request, enable waits for a genuine visible3→0; OAM retains its prior ordering and advances before HDMA. | 13-02 trigger matrix/LCD controls; 13-03 stop_policy, competing_stalls and oam_order with controls and actual IRQ wake; 13-04 critical-cut partition/lifecycle checks; 13-05 lost-stall/order mutants. | Physical collision and speed-switch qualifications remain UNKNOWN/POLICY. No Phase14 timing/APU expansion is authorized. |

## Sources

### Repository artifacts read

AGENTS.md; .planning/STATE.md; .planning/PROJECT.md; .planning/research/SUMMARY.md; .planning/REQUIREMENTS.md CGB-07; .planning/ROADMAP.md Phase13; full 13-CONTEXT.md; core/header, CMake presets and test patterns cited above. OpenGSD runtime identity reported @opengsd/gsd-core version 1.16.0; phase init reports context present, research absent and output directory .planning/phases/GB-13-cgb-hdma.

Scratch source: .planning/phases/GB-13-cgb-hdma/13-D09-boundary-prototype.c; executable was built and run under /tmp, not the repository.

### Pinned external references

- [Pan Docs CGB registers, pinned revision](https://github.com/gbdev/pandocs/blob/0191af06ac49661587dcde3d57a241a626b8df75/src/CGB_Registers.md) — masks, ranges, nominal rate, HALT and documented uncertainties.
- [SameBoy memory.c](https://github.com/LIJI32/SameBoy/blob/26a56bd6a122a6318a456abd80558408742d5adf/Core/memory.c), [display.c](https://github.com/LIJI32/SameBoy/blob/26a56bd6a122a6318a456abd80558408742d5adf/Core/display.c), [sm83_cpu.c](https://github.com/LIJI32/SameBoy/blob/26a56bd6a122a6318a456abd80558408742d5adf/Core/sm83_cpu.c) — emulator differential only.
- [SameSuite DMA subset](https://github.com/LIJI32/SameSuite/tree/f15645fb049a47ea235f6d2c9a033e72d8087901/dma) — author tests, not CGB-E measurement.
- [MagenTests HDMA source](https://github.com/alloncm/MagenTests/tree/3f9c090f16e5a721db776febb9ba7d773e1c819c/src/hblank_vram_dma) — author test and admission target.
- [Mealybug DMA](https://github.com/mattcurrie/mealybug-tearoom-tests/tree/70e88fb90b59d19dfbb9c3ac36c64105202bb1f4/src/dma) — CGB-C informational only; G1 remains unresolved.
- [OWASP ASVS 5.0](https://github.com/OWASP/ASVS/tree/master/5.0) — input validation and integer overflow categories.

## Metadata

- Repository seams and prototype observations: HIGH; direct source and run.
- Pinned docs, fixture author expectations and SameBoy behavior: MEDIUM; no hardware measurement.
- CGB-E timing and unresolved status/collision behavior: LOW / UNKNOWN.
- Research date: 2026-10-14. Re-run source probe if CPU/PPU advancement changes.
