# Phase 13: CGB HDMA - Context

**Gathered:** 2026-10-14
**Status:** Ready for planning; DEEP planning research is still required
**Method:** Owner-delegated fan-out, three independent investigations (hardware behavior, code seams, fixture/evidence admission), parent reconciliation, then one focused adversarial follow-up. All relevant areas were selected under the owner's explicit instruction to synthesize and follow recommendations. No interactive answers or approvals were invented. Stop after this discussion; do not chain into planning or execution.

<domain>
## Phase Boundary

Implement **CGB-07** for the existing bootless CGB-CPU-E software model: general-purpose and HBlank VRAM DMA, CPU stalls, FF55 cancellation/readback, HALT interaction, qualified LCD/source/overflow behavior, transfers of at most 128 blocks, and equivalence across bounded public runs. Use original guest fixtures and the four relevant SameSuite VRAM DMA cases; admit and pass MagenTests `hblank_vram_dma`. Report Mealybug `hdma_*-C` only as informational CGB-C evidence when runnable within its rights restrictions.

Phase 12 merged as PR #68 at `8091fb591de7fb68e666be01d344f5f26ebedc5c`; its implementation and completed UAT are prerequisites already satisfied. Its exact source/test qualifications remain in its own evidence. This discussion implements no DMA and completes no CGB-07 requirement.

No new frontend feature, public DMA-control API, production dependency, general bus framework, broad OAM DMA qualification, Phase 14 timing/APU work, Phase 15 game/release claim, or save-state implementation belongs here. Phase 14 owns CGB mode-3 length/window timing; do not fix that whole subsystem merely to improve an HDMA oracle.
</domain>

<decisions>
## Implementation Decisions

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

### Agent discretion and research stop rule

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
