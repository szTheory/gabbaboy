# Phase 10: CGB Profile, Banking and Register Visibility - Context

**Gathered:** 2026-10-12
**Status:** Ready for planning
**Method:** Five advisor researchers ran in parallel. Each worked from several angles (architect, emulator hardware, QA and oracle design, security and bounds, DevOps and CI, release and docs) and ended with an adversarial pass. The areas were:
1. Profile selection and the model/mode query API.
2. CGB-E post-boot state, the register visibility matrix, the KEY0 lock and the model-gate audit.
3. VRAM/WRAM banking, echo RAM, the OAM DMA source by model and DMG byte-identity.
4. The half-dot timeline ADR and the banking-indirection benchmark.
5. A gap sweep for decision points the first four did not cover.

Primary sources read: Mooneye at `31510e12`, covering `boot_regs-cgb`, `boot_hwio-C`, `boot_div-cgbABCDE`, `unused_hwio-C`/`-GS` and `oam_dma/sources-GS`. Pan Docs: Power Up Sequence, CGB Registers and OAM DMA. SameBoy: `Core/memory.c`, `Core/timing.c` and `BootROMs/cgb_boot.asm`. The AGE repo tree. mGBA and Gambatte claims were made from memory and are comparison only.

Per the owner's standing instruction (discuss fan-out, auto-follow), the reconciled recommendations were adopted without asking about each area. Researcher conflicts were reconciled on the evidence: hardware-test evidence beats Pan Docs prose, which beats a single emulator oracle. Where the evidence ran out, the tie went to DMG byte-identity and fail-closed honesty. The resolutions are recorded in the decisions below and in `10-DISCUSSION-LOG.md`. Owner veto points are listed under "Owner veto window".

<domain>
## Phase Boundary

Phase 10 delivers:
- The `GBB_PROFILE_CGB_CPU_E` profile.
- `gbb_probe_rom` and `gbb_get_info`, which report the execution mode (CGB, or DMG-compatibility from `$143` bit 7) and an informational flag for CGB-only ROMs on the DMG profile.
- A post-boot state table per mode, with provenance for each field. The DMG row stays byte-identical.
- The model-gate audit of every DMG-specific branch, in code and docs, enforced by CI.
- A register visibility matrix (DMG, CGB, CGB-compat), with one test per cell and the KEY0 lock.
- VRAM 2x8 KiB and WRAM 8x4 KiB banking, with echo RAM that follows the selected WRAM bank and a model-correct OAM DMA source, verified by original fixtures.
- The half-dot timeline ADR.
- A banking-indirection benchmark against the Phase 7 baseline.

Requirements: CGB-01, CGB-02, CGB-03.

**Not in this phase:**
- Colour PPU, palette RAM behaviour, RGB555 frames, the DMG-compat palette and the player `--model` option: Phase 11.
- KEY1 speed switch, the CGB STOP path and CPU stall: Phase 12.
- HDMA/GDMA: Phase 13.
- CGB-E APU deltas, PCM12/34 (FF76/77), the RP/IR stub, AGE/SameSuite corpus admission and wider Mooneye CGB admission: Phase 14.
- A CGB game, the support ledger release and v0.2.0: Phase 15.
- Any change to DMG-profile behaviour.

</domain>

<decisions>
## Implementation Decisions

### A. Profile selection and the model/mode API (CGB-01)

- **D-01: Selection.** `gbb_create(GBB_PROFILE_CGB_CPU_E, &inst)` is the only selector. `GBB_PROFILE_CGB_CPU_E = 2` is appended to `gbb_profile`. The profile is fixed per instance, so changing it means destroy and create.
  - Execution mode is a property of profile plus `$143`, never a host toggle.
  - `gbb_create` keeps returning `GBB_UNSUPPORTED_PROFILE` for the CGB value until the plan that completes the profile flips it. Header comment "only implemented model is bootless DMG-CPU-B" is updated in that same commit.
  - **Reversibility:** one-way. This is a public enum value.

- **D-02: One sized info struct shared by probe and instance.** Appended exactly as below. Every field is fixed-width so `-fshort-enums` cannot change the layout.
  ```c
  typedef enum { GBB_MODE_NONE = 0, GBB_MODE_DMG = 1, GBB_MODE_CGB = 2, GBB_MODE_CGB_DMG_COMPAT = 3 } gbb_exec_mode;
  typedef enum { GBB_CGB_SUPPORT_NONE = 0, GBB_CGB_SUPPORT_ENHANCED = 1, GBB_CGB_SUPPORT_ONLY = 2,
                 GBB_CGB_SUPPORT_OTHER = 3, GBB_CGB_SUPPORT_PGB = 4 } gbb_cgb_support;
  #define GBB_INFO_HAS_ROM          0x01u
  #define GBB_INFO_CGB_ONLY_ON_DMG  0x02u  /* $C0 ROM on the DMG profile: informational, the load succeeded */
  #define GBB_INFO_HAS_BATTERY      0x04u
  #define GBB_INFO_HAS_RTC          0x08u
  #define GBB_INFO_HAS_RUMBLE       0x10u
  typedef struct {
      uint32_t struct_size;    /* IN: the caller sets sizeof(gbb_info); OUT: the bytes written */
      uint32_t profile;        /* a gbb_profile value */
      uint32_t mode;           /* a gbb_exec_mode value */
      uint32_t flags;          /* GBB_INFO_* */
      uint8_t  cgb_flag;       /* raw $143 */
      uint8_t  cgb_support;    /* a gbb_cgb_support value */
      uint8_t  cartridge_type; /* raw $147 */
      uint8_t  reserved0;      /* always 0 */
      uint32_t rom_size_bytes;
      uint32_t ram_size_bytes; /* cartridge RAM only (MBC2 = 512); excludes the RTC block */
  } gbb_info;
  #define GBB_INFO_SIZE_V1 28u   /* static-asserted equal to sizeof(gbb_info) */
  gbb_error gbb_probe_rom(gbb_profile profile, const uint8_t *rom, size_t rom_size, gbb_info *out_info);
  gbb_error gbb_get_info(const gbb_instance *instance, gbb_info *out_info);
  ```
  - **Reversibility:** one-way. The layout, enum values, flag bits and `struct_size` convention become permanent at v0.2.0. Option B (scalar getters) was rejected because it means more symbols, a second struct and probe/instance divergence.

- **D-03: `$143` mapping.** Hardware decodes CGB mode from bit 7 and PGB mode from bits 2-3. Bit 6 (`$C0`) is a convention that hardware ignores.

  | `$143` | `cgb_support` | DMG profile | CGB profile |
  |---|---|---|---|
  | bit 7 clear | NONE | DMG | CGB_DMG_COMPAT |
  | `$80` | ENHANCED | DMG | CGB |
  | `$C0` | ONLY | DMG + `GBB_INFO_CGB_ONLY_ON_DMG`; loads | CGB |
  | bit 7 set, bits 2-3 clear, not `$80`/`$C0` | OTHER | DMG | CGB |
  | bit 7 set and (bit 2 or bit 3) set | PGB | DMG (DMG ignores `$143`) | **rejected** with appended `GBB_UNSUPPORTED_EXECUTION_MODE` |

  - Reconciled conflict: the API researcher proposed running PGB-flagged ROMs as CGB. The visibility researcher, and PITFALLS V2-06, require rejection. Rejection won, because silently running a mode the hardware would not enter is a false claim.
  - The new error code is appended and is the only new error.
  - No DMG-profile load result changes.
  - Probe on the DMG profile reports `cgb_support = PGB` with no error.

- **D-04: Contract.**
  - Probe runs the same `validate_header` path, in the same order, as `gbb_load_rom`. It allocates nothing, mutates nothing and needs no instance.
  - Every ROM-level error is identical to load on the same profile. All existing header errors are profile-independent. D-03 PGB rejection is the only profile-dependent error.
  - An unknown profile returns `GBB_UNSUPPORTED_PROFILE`, checked first.
  - `GBB_INVALID_ARGUMENT` covers: NULL `out_info`; a NULL ROM with nonzero size; `struct_size < GBB_INFO_SIZE_V1`.
  - The core writes field by field, only within `struct_size`, and sets `struct_size` to the bytes written. A larger caller struct keeps its extra bytes untouched.
  - On error the output is unchanged.
  - `gbb_get_info` with no ROM loaded: `mode = GBB_MODE_NONE`, `flags = 0`, other fields 0.
  - Mode is constant across `gbb_reset`. A failed load leaves the info unchanged, because the mode commits with the ROM swap.
  - On the CGB profile with no ROM, the post-boot table is the compat row.

- **D-05: `gbb_copy_frame` on the CGB profile returns `GBB_UNSUPPORTED_PROFILE`** until Phase 11 defines colour output. It is documented in the header and the guide. Phase 10 oracles are guest-memory and register predicates, never frames. This changes the contract of an existing function only on the new profile.

### B. Post-boot state, provenance and the model-gate audit (CGB-01, CGB-02)

- **D-06: C tables are the single source of truth.**
  - A const `post_boot[]` table of field x {DMG, CGB, COMPAT}. Each cell is `{value, prov, src_id, reason}`, where `prov` is one of `HW_TEST | PANDOCS | ORACLE_SAMEBOY | POLICY | HEADER_DERIVED`. `reset_state` consumes it.
  - A const `io_visibility[]` table (register x column, giving read value, write effect and `IMPL` or `DEFERRED(phase)`). It drives the FF4C-FF7F decode and `read_supported`.
  - `docs/cgb-profile.md` mirrors both tables between markers, with a numbered source list.
  - `test_cgb_tables` diffs code against docs, and fails on any of:
    - a mismatch (negative controls: a mutated doc copy and a mutated table copy);
    - a `POLICY` cell without a reason;
    - any `HW_TEST` cell outside the compat column (no hardware oracle covers CGB mode).
  - A dedicated test pins the DMG column equal to the pre-refactor literals, in addition to the baseline. Docs-only tables (Option B) were rejected because they allow silent doc/code drift (V2-20).
  - **Reversibility:** costly. `reset_state` is the DMG regression hot spot. Keep the refactor in its own commit so a baseline check can bisect it.

- **D-07: Post-boot values.** Use the table drafted by the visibility researcher (`10-DISCUSSION-LOG.md` §B), with these resolutions:
  - Compat row CPU registers: hardware-pinned by Mooneye `boot_regs-cgb`, so `HW_TEST`.
    - A=`$11`, F=`$80`, C=`$00`, D=`$00`, E=`$08`, H=`$00`, L=`$7C`.
    - B and HL take the Nintendo-licensee title-sum branch (B = title sum; HL=`$991A` if B is `$43`/`$58`) per Pan Docs. Pin it with a synthetic-header test; that cell is `PANDOCS`.
  - CGB-mode CPU row: from Pan Docs, `PANDOCS`. A=`$11`, F=`$80`, B=`$00`, C=`$00`, D=`$FF`, E=`$56`, H=`$00`, L=`$0D`.
  - P1 is `$FF` on CGB in both modes. Mooneye `boot_hwio-C` pins compat. The CGB-mode cell comes from the boot ROM flow and is labelled `ORACLE_SAMEBOY`. The DMG cell stays `$CF`.
  - SC: compat `$7E` (HW), CGB `$7F` (PD).
  - DMA FF46: `$00` on CGB (PD).
  - Compat DIV and divider phase: solved from Mooneye `boot_div-cgbABCDE`, then labelled `HW_TEST`. Its applicability is "CGB A-E", not "CGB-E".
  - CGB-mode DIV, LY and STAT: `POLICY` (same phase as compat, LY=0). The note says real hardware varies with the header and held buttons.
  - The DMG header-checksum F branch is `DMG_ONLY`. On CGB, F=`$80` always.
  - Unknown CGB-mode index registers BCPS/OCPS: `$C0` `POLICY [VERIFY]`. Compat `$C8`/`$D0` is HW.
  - VRAM, WRAM and OAM are zero-filled on every profile and bank: `POLICY`, a deterministic choice, consistent with v0.1 D-025.

- **D-08: The model-gate audit is enforced by CI.**
  - **Tag grammar.** `/* MODEL: DMG_ONLY|CGB_ONLY|BOTH|UNKNOWN GATE-NN GUARD=<token> basis=<ref> */`. One goes before every top-level function in `src/core/gabbaboy.c`, and one before each branch whose behaviour differs by model.
  - **Doc.** `docs/model-gates.md` holds one row per GATE id.
  - **Scanner.** `tests/scripts/verify-model-gates.py`, stdlib only, run as `python3 -I`, matching `verify-support-ledger.py`. Its rules:
    - R1: every function is tagged.
    - R2: code and doc are a bijection, with identical tags.
    - R3: `UNKNOWN` needs `research:<phase>` or `expected-failure:<reason>`. Under `--release`, an unresolved `UNKNOWN` fails.
    - R4: `DMG_ONLY` and `CGB_ONLY` need their GUARD token within 12 lines.
    - R5: hazard tokens (FF4x-FF7x literals, `stopped`, `halt_bug`, `dma_`, `apu_power`, `ppu_mode`, `0xFFu` returns) cannot sit under `BOTH` without `basis=`.
  - **Negative controls.** `--self-test` mutants must fail: a deleted tag, a code/doc mismatch, an untagged new function, an `UNKNOWN` without resolution under `--release`, and a `DMG_ONLY` without its guard.
  - It is registered in CTest and in `tests/expected-tests.txt`.
  - **Seed tags:**
    - header-checksum F: `DMG_ONLY`
    - STOP: `UNKNOWN research:12`
    - HALT bug and CPU core: `BOTH basis="no SM83 opcode difference"`
    - STAT-write spurious IRQ: `UNKNOWN research:14`
    - VRAM/OAM lock windows: `UNKNOWN research:11`
    - OAM DMA bus conflict: `DMG_ONLY` in the DMG path, plus a CGB `expected-failure` (D-17)
    - wave RAM aliasing and NR52 power-off: `UNKNOWN research:14`
    - timer/TAC and JOYP IF: `UNKNOWN research:14`
  - The audit was not done in Phase 8, so this phase owns it, as the roadmap says.

### C. Register visibility matrix and KEY0 (CGB-02)

- **D-09: The DMG profile row is unchanged.** FF4C-FF7F (and the other addresses `read_supported` excludes today) keep stopping with `GBB_STOP_UNSUPPORTED_BUS` on the DMG profile. The DMG column of the matrix asserts exactly that.
  - Reconciled conflict: the visibility researcher proposed making DMG FF4C-FF7F read `$FF`. That is hardware-correct per `unused_hwio-GS`, but it changes DMG behaviour, which this phase's goal forbids. It is deferred (see Deferred). `unused_hwio-GS` is not admitted in Phase 10.

- **D-10: CGB columns.** Rule: implement a cell when its hardware semantics are pure register storage or a constant read, pinned by HW/PD, and need no later subsystem. Otherwise the cell is `DEFERRED(n)`, which fails closed with `GBB_STOP_UNSUPPORTED_BUS` on the access. A guest that reaches unbuilt hardware stops visibly and never passes by accident.

  | Register | CGB mode | CGB-compat |
  |---|---|---|
  | FF4C KEY0 | reads `$FF`, writes ignored (locked) | reads `$FF`, writes ignored (locked) |
  | FF4D KEY1 | reads `$7E \| armed`; bit 0 stored. STOP while armed is `DEFERRED(12)` | `$FF` / ignored |
  | FF4F VBK | `$FE \| bank`; bit 0 selects the bank | `$FE` / ignored |
  | FF51-54 HDMA1-4 | reads `$FF`; writes accepted, no observable state | `$FF` / ignored |
  | FF55 HDMA5 | write `DEFERRED(13)`; read `$FF` | `$FF` / ignored |
  | FF56 RP | `DEFERRED(14)` | `$FF` / ignored |
  | FF68/FF6A BCPS/OCPS | index plus auto-increment bit, bit 6 reads 1; stored | `$C8`/`$D0` initial; stored |
  | FF69/FF6B BCPD/OCPD | `DEFERRED(11)` | `$FF` / ignored, no increment |
  | FF6C OPRI | `DEFERRED(11)` | `$FF` / ignored |
  | FF70 SVBK | `$F8 \| bank`; `v & 7`, 0 maps to 1 | `$FF` / ignored |
  | FF72, FF73 | R/W, init `$00` | R/W, init `$00` |
  | FF74 | R/W, init `$00` | `$FF` / ignored |
  | FF75 | bits 4-6 R/W, reads `$8F \| bits` | bits 4-6 R/W |
  | FF76, FF77 | `DEFERRED(14)` | `DEFERRED(14)` |
  | Other unused IO in FF00-FF7F | `$FF` / ignored | `$FF` / ignored |

  - Reconciled conflict on VBK in compat: the banking researcher and the V2-07 reading of Pan Docs said `$FF`. Mooneye `boot_hwio-C` (hardware) expects `$FE`, and SameBoy agrees. The hardware test wins.
  - Reconciled conflict on RP and OPRI: the visibility researcher proposed storing them. RP's CGB-E value is disputed (Pan Docs `$3E` vs SameBoy-implied `$2E`, no hardware oracle), and OPRI's effect belongs to Phase 11. Both are `DEFERRED` rather than invented.
  - **Reversibility:** reversible. Each `DEFERRED` cell flips to `IMPL` in its owning phase, which updates its test.

- **D-11: Cell tests.** `tests/test_cgb_visibility.c` is table-driven: `{profile, $143, addr, read0, w1, read1, w2, read2, IMPL|DEFERRED(n), src}`.
  - The guest is an original synthetic ROM that stores LDH results in HRAM, following the `tests/test_bus.c` pattern, and runs through the public API. `DEFERRED` cells assert the stop reason and address.
  - Negative controls:
    - flipping one expected byte must fail;
    - for every cell that differs between columns, running the same program in the other column must differ;
    - a sweep of FF00-FF7F finds a row for every address, and deleting a row fails.

- **D-12: KEY0 lock.** Mode is fixed at load (and at `gbb_reset`, which re-reads the header like a reboot). KEY0 is never guest-writable after hand-off.
  - In both CGB columns, the test writes `$00`, `$04`, `$80` and `$C0` to FF4C and expects a read of `$FF`. A behavioural probe follows: in compat, VBK=1 still reads `$FE`; in CGB mode the bank switch works. `gbb_get_info` mode is unchanged.
  - MagenTests `key0_lock_after_boot` stays skipped, per SUMMARY.

### D. Banking, echo and OAM DMA source (CGB-03)

- **D-13: Storage.** `uint8_t vram[2][8192]`, `uint8_t wram[8][4096]`, plus `vram_bank` and `wram_bank` in the instance (+32 KiB).
  - DMG pins `wram_bank = 1` and `vram_bank = 0`, so C000-DFFF is `wram[0]` then `wram[1]`: exactly the old contiguous layout, with no per-access profile branch.
  - Every `sizeof(m->vram)` and `m->vram[...]`/`m->wram[...]` site is rewritten: `read8`, `write8`, `dma_source_read`, the PPU fetch, `gbb_peek_ram` and `reset_state`.
  - Flat arrays with offsets (Option B) were rejected because they allow cross-bank PPU reads (V2-21) and silently double `sizeof` bounds.
  - **Reversibility:** costly. This touches every RAM access site.

- **D-14: The PPU reads `vram[0]` explicitly this phase,** never `vram_bank`, until Phase 11 adds attributes. `cpu_vram_access_allowed` stays a single mode-3 gate in front of both banks.

- **D-15: Address map.**

  | Range | Maps to |
  |---|---|
  | C000-CFFF | `wram[0]` |
  | D000-DFFF | `wram[wram_bank]` |
  | E000-EFFF | `wram[0]` |
  | F000-FDFF | `wram[wram_bank]` |
  | 8000-9FFF | `vram[vram_bank]` |

  VBK/SVBK writes are decoded only in CGB mode. On DMG and compat they are ignored, so the banks never move there. `gbb_peek_ram` keeps its signature and follows the current bank; on DMG its bytes are identical to today.

- **D-16: OAM DMA source by model.**
  - DMG profile: frozen, every page unchanged (D-024's envelope, including `$FF` for ROM, cart RAM and E0-FF).
  - CGB profile, both modes:
    - pages 00-7F (ROM) and A0-BF (cart RAM) read through the cartridge seam (PD/OR `[VERIFY]`);
    - 80-9F reads `vram[vram_bank]`;
    - C0-CF reads `wram[0]`;
    - D0-DF reads `wram[wram_bank]`;
    - E0-FF reads `$FF` (SameBoy CGB, `[VERIFY]` for CGB-E specifically).
  - All `[VERIFY]` cells are labelled `PANDOCS` or `ORACLE_SAMEBOY` in `docs/cgb-profile.md`, never hardware.

- **D-17: CGB CPU-side DMA bus conflict** (separate buses on CGB). Keep the DMG "HRAM only during DMA" rule on CGB in Phase 10. Record it as a named expected failure in `docs/model-gates.md` and the limitations. A real CGB bus-conflict model needs its own oracle and is deferred.

- **D-18: Original fixture `fixtures/cgb-banking/`.** MIT and RGBDS 1.0.1. The layout follows `fixtures/mbc5-banking/`: source and ROM sha256, build recipe, protocol, scope limits and a `fixture-repro` leg.
  - One source with two builds: `rgbfix -c` gives `$143=$80`, and plain `rgbfix` gives `$00`.
  - The guest branches on the A register at entry and reports a model-specific verdict at C000 (`$A5` pass / `$EE` fail), with result bytes from C002 in bank-0 WRAM, read through `gbb_peek_ram`.
  - Cells:
    - (a) VBK read-back and bank independence at 8000 and 9800;
    - (b) SVBK 0..7 read-back, with a per-bank D000 marker;
    - (c) echo: F000+n written in bank k is read at D000+n, and E000 mirrors C000;
    - (d) DMA from D0 under banks 2 and 3, from 80 under VBK 0 and 1, from E0/FE giving `$FF`, and from page 00 matching ROM;
    - (e) DMG-profile and compat runs assert ignored writes and the read values in D-10.
  - Negative controls:
    - (i) an in-memory patch of an expected value must produce `$EE`;
    - (ii) the CGB build on the DMG profile fails exactly the CGB-only cells;
    - (iii) a variant ROM that skips the SVBK write must be detected.

- **D-19: DMG byte-identity gate,** run at every wave:
  - (1) `tests/baseline/dmg-cpu-b-v1.txt` is recomputed at head and must be identical. Zero ledger lines change, as `tests/baseline/CHANGES.md` already requires for later phases.
  - (2) The existing bus, DMA, PPU and acceptance suites pass unchanged.
  - (3) New metamorphic test `banking_dmg_flat_reference`: a seeded random access sequence on the DMG profile (FF4F/FF70 writes are excluded on DMG because they fail closed per D-09; C000-FDFF and 8000-9FFF accesses are included) must match a flat 8 KiB reference model written inside the test. Negative control: the CGB profile with banking writes must diverge.
  - (4) A DMG-profile assertion after each fuzz step: `vram_bank == 0` and `wram_bank == 1`.
  - No persistent format contains WRAM or VRAM, so no migration is needed. The bank-peek test hook must stay internal and must not become public ABI.

### E. Half-dot timeline ADR and the benchmark (success criterion 4)

- **D-20: ADR `D-070` in `.planning/context/DECISIONS.md`.**
  - The D-009 `uint64_t` half-dot master timeline is the single clock for normal and double speed.
  - A CPU T-cycle is 2 half-dots normal and 1 half-dot double, so an M-cycle is 8 or 4.
  - A PPU dot is 2 half-dots. APU, HDMA and RTC are constant in master time.
  - Only CPU-side devices scale (timer/DIV, serial, OAM-DMA byte period, TIMA reload) through `cpu_ticks(t) = t >> double_speed`, at three choke points: `instruction_cost`, the `bus_read`/`bus_write` offset, and the interrupt/halt literals.
  - Each device keeps its own remainder and phase across a switch, including `divider_phase`. The switch stall is a named constant in master half-dots. The RTC stays at 2^23 half-dots/s and never reads `double_speed`.
  - Rejected: a quarter-dot unit (no finer hardware period exists, and it would rebaseline DMG) and a speed multiplier (V2-03).
  - Open `[VERIFY]` items for Phase 12: DIV/APU phase at the switch, and whether the stall counts in pre- or post-switch M-cycles.
  - SameBoy uses the same 8 MHz-unit model.

- **D-21: The ADR is verifiable now.**
  - A `_Static_assert` block with named constants in `gabbaboy.c`:
    - `GBB_MASTER_HALF_DOTS_PER_SECOND == 1u<<23`;
    - half-dots per T-cycle are 2 normal and 1 double;
    - 4 T-cycles make an M-cycle in both modes;
    - a dot is 2 half-dots;
    - the RTC shift is 23;
    - `70224*2 == 140448` half-dots per frame.
  - Confirm the C17 build accepts `_Static_assert`; there is no existing precedent.
  - A `cmake/VerifyDocContract.cmake` check ties the ADR text to those symbols, with negative selftests (the Phase 9 pattern).
  - Runtime behavioural invariants arrive with Phase 12.

- **D-22: The benchmark is advisory, never a CI timing gate** (D-016, D-032, no flaky CI).
  - Extend `tests/scripts/measure-release-baseline.sh` with an `--ab <base-build> <head-build>` mode.
    - Strictly interleaved pairs, `GBB_RELEASE_MEASURE_SAMPLES=30`, `WARMUPS=3`.
    - Workload `original-wram-tracer-1m-half-dots-v1`, DMG-CPU-B, `--no-trace`.
  - Three builds:
    - frozen baseline `5a55f19` (the headline comparison);
    - Phase 9 head `d7e2e0a` (attributes the delta to banking rather than the cartridge work);
    - Phase 10 head.
  - Report the per-pair `t_head/t_base` median, min-of-n, sd and the 1.96·sd/√n margin as percentages. Deltas under about 3% are reported as noise.
  - **Review trigger** (not a gate): median ratio > 1.05 and lower margin bound > 1.0. If it fires, the owner decides under D-016 whether to optimise.
  - Results go to `.planning/phases/GB-10-*/10-BENCH.md` plus a JSON receipt carrying revision, build, hardware, workload, model, output digest, warm-up, samples and uncertainty.
  - `tests/baseline/dmg-cpu-b-v1.txt` is not edited; there are no `bench.banking.*` lines.
  - **Automated part:** a CTest self-test runs the A/B mode with 3 samples on a tiny budget. It asserts both builds produce `correctness_digest_fnv1a64` equal to the ledger's `4c7a57ff3d50d228`, and that the receipt has every field. Negative controls: a mutated digest and a receipt missing a field must fail. Timing is never asserted. The evidence run is on the baseline's macOS arm64 class; hosted timings are labelled non-comparable.

### F. Cross-cutting (gap sweep)

- **D-23: STOP and HALT.** The shared DMG STOP/HALT path is kept and tagged (D-08). KEY1 arming is stored (D-10), but STOP while armed on the CGB profile fails closed (`DEFERRED(12)`), never entering DMG STOP sleep. STOP without arming on CGB uses the shared path, recorded as `UNKNOWN research:12`.

- **D-24: Header, logo and checksum validation is unchanged and profile-independent.** No CGB boot-ROM logo-check variant is modelled; this is project policy, documented.

- **D-25: Runner.**
  - Add `--profile dmg|cgb` (default `dmg`). Map model to profile in one function, replacing the hard-coded `profile=DMG-CPU-B` and `model=dmg-cpu-b` strings in `src/runner/main.c` and `src/runner/acceptance.c`. Remove the `unsupported-profile` rejection for `cgb-cpu-e` in `acceptance.c`.
  - DMG output lines stay byte-identical (baseline-checked).
  - Negative controls: a CGB case on a DMG run is `excluded`; a CGB run never prints a DMG label.
  - No new manifest fields: reuse `model_pass`, `model_fail` and `target_revision`. Frame-digest predicates are not applicable on the CGB profile (D-05).
  - The player keeps the DMG default and gets only the minimal compile changes. Its `select_profile` seam is a single function that Phase 11's `--model` uses.

- **D-26: Third-party fixtures this phase.** These are Mooneye derivatives with the existing zero-byte font replacement (G6) and headless patch, in a sibling manifest next to `fixtures/mooneye/`, with digests, `model_pass` and `target_revision`.
  - `misc/boot_regs-cgb`: admitted as a compat-row pass.
  - `misc/boot_div-cgbABCDE`: admitted as a pass, with `target_revision` CGB-A..E. CGB-E is never claimed beyond that.
  - `misc/boot_hwio-C` and `misc/bits/unused_hwio-C`: staged as `expected-unsupported`. They must stop at FF76 with `GBB_STOP_UNSUPPORTED_BUS`; reaching FF76 proves FF00-FF75 passed. They flip to pass in Phase 14.
  - `[VERIFY]` before admission: each ROM builds with a non-CGB `$143`, and the probe script passes.
  - Not admitted: `unused_hwio-GS` (D-09), `oam_dma/sources-GS` (DMG-only), `boot_*-cgb0` and `-A` (unsupported steppings), AGE and SameSuite (Phase 14).

- **D-27: Coverage.**
  - Fuzz, loader-matrix and loader-fuzz drivers are parameterised over both profiles. Header cases: `$143 ∈ {00, 80, C0, 81, 84, 88, FF}` x both profiles.
  - A CGB-profile `gbb_run` fuzz over random I/O writes asserts each access works or stops `UNSUPPORTED_BUS`, under ASan/UBSan.
  - Probe/load error parity runs over the loader matrix and fuzz corpus. A deliberately skewed probe must fail.
  - `struct_size` cases: 0, too small, equal, and larger with extra bytes preserved.
  - C and C++ installed consumers exercise create-CGB, probe, `get_info` and the CGB-only-on-DMG flag, so the api-coverage gate sees every new symbol.
  - New test names use the `cgb_`, `banking_` and `model_gates` prefixes. `tests/expected-tests.txt` and the sanitizer lists are updated in the same PR, and Windows legs are included.

- **D-28: Docs in the same PR.**
  - `docs/native-integration.md`: the new API, profile, modes, the D-05 caveat, PGB rejection and the limitations section.
  - `docs/cgb-profile.md` (D-06) and `docs/model-gates.md` (D-08).
  - `docs/support/unreleased.md`: a CGB-CPU-E row scoped to "profile, banking and register visibility, original fixtures plus admitted Mooneye boot ROMs", with no game and no colour claim.
  - `CHANGELOG` via release-please.
  - DECISIONS D-070 (and D-071+ for any further adopted decisions).
  - A LESSONS entry on the runner's hard-coded `model=dmg-cpu-b`, with cause, evidence, remedy, applicability and verification.

- **D-29: Public API escalation judgement.** The additions are:
  - one profile value, two enums, five flag bits, one struct, two functions and one error code, all appended;
  - one existing-function change, scoped to the new profile (D-05).

  No existing call changes on `GBB_PROFILE_DMG_CPU_B`. As with Phase 9 D-17, this is treated as an append-only addition and auto-followed. The owner may veto before the phase PR merges.

### Claude's Discretion
- Internal helper names, exact `GATE-NN` numbering, the doc table markup format and the fixture guest's internal layout.
- Plan split. Suggested waves:
  1. Model-gate tags, scanner and docs, plus runner model threading with negative controls.
  2. Profile, probe, info and the post-boot table refactor (DMG pin test first).
  3. Bank arrays and indirection, echo, OAM DMA by model, `fixtures/cgb-banking`, the metamorphic test and the benchmark.
  4. The visibility matrix, `DEFERRED` cells, KEY0 lock and the Mooneye admissions.
  5. Fuzz, consumers, api-coverage, inventory, docs, ledger and the D-070 ADR with its static asserts.
  - Run the DMG baseline after each wave. Keep the arrays and the visibility changes in separate commits.

</decisions>

<owner_veto_window>
## Owner veto window (auto-followed; veto before the phase PR merges)

1. The `gbb_info` ABI (D-02): struct layout, the `struct_size` convention (new to this header) and the enum and flag values.
2. PGB-flagged ROMs rejected on the CGB profile with the new `GBB_UNSUPPORTED_EXECUTION_MODE` (D-03).
3. `gbb_copy_frame` on the CGB profile returns `GBB_UNSUPPORTED_PROFILE` until Phase 11 (D-05).
4. DMG FF4C-FF7F stays fail-closed rather than becoming hardware-correct `$FF` (D-09). This keeps DMG byte-identical, and the hardware fix is deferred.
5. Benchmark review trigger at +5% median DMG no-trace (D-22).

</owner_veto_window>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and requirements
- `.planning/ROADMAP.md` §Phase 10: goal, four success criteria, research flag Moderate. §Phases 11-14 give the owning phase of every `DEFERRED(n)` cell.
- `.planning/REQUIREMENTS.md`: CGB-01, CGB-02, CGB-03.
- `.planning/context/DECISIONS.md`:
  - D-008 (profile name), D-009 (half-dot timeline), D-016 (profile before performance);
  - D-024 (DMG DMA source envelope), D-025 (deterministic RAM fill);
  - D-026 (single CGB revision; CGB-only on DMG loads with flag);
  - D-030/D-031/D-032/D-038 (baseline ledger and advisory bench);
  - D-069 (zero manual UAT; every check automated with a negative control).
- `AGENTS.md`: append-only API, update docs, tests and limitations together, fixture rights and digests, no boot ROMs, stop after phase.

### v0.2 research
- `.planning/research/v0.2/SUMMARY.md`: P6 deliverables, Conflicts #5/#6/#12/#14, open items for DIV/LY/STAT and compat readability.
- `.planning/research/v0.2/ARCHITECTURE.md`: §3 timing domains, the bus and banked arrays, and the public API sketch (superseded in shape by D-02).
- `.planning/research/v0.2/PITFALLS.md`: V2-01, V2-02, V2-03, V2-06, V2-07, V2-20, V2-21.
- `.planning/research/v0.2/FEATURES.md`: CGB register and post-boot sections.

### Prior phase decisions and evidence
- `.planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-CONTEXT.md` D-30/D-31: the baseline ledger and its frozen rules.
- `tests/baseline/dmg-cpu-b-v1.txt`, `tests/baseline/CHANGES.md`: zero DMG ledger lines change.
- `.planning/phases/GB-09-mbc3-deterministic-rtc-and-cartridge-persistence/09-CONTEXT.md` D-14..D-18: the append-only API escalation precedent.
- `cmake/VerifyDocContract.cmake`: the doc-contract pattern reused for D-21.
- `fixtures/mbc5-banking/`, `fixtures/mooneye/` (manifest and `ELIGIBILITY.md`): fixture admission patterns.
- `tests/scripts/verify-support-ledger.py`: the stdlib `python3 -I` scanner pattern for D-08.
- `tests/scripts/measure-release-baseline.sh`, `tests/measure_core.c`: the benchmark harness for D-22.

### External primary sources
- Mooneye test suite at `31510e12`: `misc/boot_regs-cgb.s`, `misc/boot_hwio-C.s`, `misc/boot_div-cgbABCDE.s`, `misc/bits/unused_hwio-C.s`, `acceptance/bits/unused_hwio-GS.s`, `acceptance/oam_dma/sources-GS.s`.
- Pan Docs: https://gbdev.io/pandocs/Power_Up_Sequence.html, https://gbdev.io/pandocs/CGB_Registers.html, https://gbdev.io/pandocs/OAM_DMA_Transfer.html
- SameBoy `Core/memory.c`, `Core/timing.c`, `BootROMs/cgb_boot.asm`: a differential oracle only, never hardware evidence.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `reset_state` (`src/core/gabbaboy.c:632`): becomes the post-boot-table consumer (D-06).
- `read_supported` (`:1331`): the fail-closed allow-list; `io_visibility[]` drives the FF4C-FF7F part.
- `cpu_vram_access_allowed` (`:747`), `read8` VRAM path (`:871`), `write8` (`:990`), `dma_source_read`, PPU fetch: the banking rewrite sites (D-13/D-14).
- `validate_header` (`:2006`), `gbb_create` (`:2078`), `gbb_reset` (`:2097`), `gbb_load_rom` (`:2113`), `gbb_copy_frame` (`:1944`): API integration (D-01..D-05).
- `src/runner/main.c` (hard-coded `profile=DMG-CPU-B` at lines 266, 280, 303), `src/runner/acceptance.c` (`model=dmg-cpu-b` strings and the cgb rejection near line 1196), `src/runner/cases.c` (`gbb_case_model_known` already accepts `cgb-cpu-e`).
- `tests/test_bus.c`: the synthetic-ROM HRAM-result pattern for the cell tests.
- `tests/fuzz_core.c`, `tests/test_loader_matrix.c`, `tests/test_loader_fuzz.c`: to parameterise over profiles.
- `tests/consumers/{c,cpp}`: installed consumers for the api-coverage gate.

### Established Patterns
- Enum plus `switch`, plain-integer sub-structs, no vtables, single TU.
- Append-only public API, auto-followed with an owner veto (Phase 8 rumble, Phase 9 D-17).
- Exact test inventory, sanitizer leg and Windows legs. `fixture-repro` workflow for original and derived fixtures.
- Evidence classes are labelled; another emulator's values are never presented as hardware truth.

### Integration Points
- Core: `src/core/gabbaboy.c`, `include/gabbaboy/gabbaboy.h`.
- Runner and acceptance: `src/runner/*`, `src/accept/*`. Player: compile-only changes plus the `select_profile` seam.
- CI: `.github/workflows/ci.yml` (scanner, cell tests, baseline), `fixture-repro.yml` (`cgb-banking` and Mooneye CGB derivatives).

</code_context>

<specifics>
## Specific Ideas

- "Another copy and paste is better than another dep" (owner): the scanner is stdlib Python, the benchmark extends the existing script, and no valgrind or other new tooling is added.
- Zero manual verification (D-069): every decision above names its automated check and negative control.

</specifics>

<deferred>
## Deferred Ideas

- DMG-profile FF4C-FF7F reading `$FF` per `unused_hwio-GS`, and admitting that ROM: hardware-correct but a DMG behaviour change. Candidate for Phase 14 qualification, with an explicit baseline `CHANGES.md` entry.
- The CGB CPU/DMA separate-bus conflict model (D-17).
- DMG OAM DMA sources at E0-FF and ROM (SameBoy mirrors them; D-024's gap), as a separate change if reopened.
- RP/IR (`$3E` vs `$2E`) and FF76/77: Phase 14.
- The CGB STOP path, KEY1 switch and stall: Phase 12. HDMA: Phase 13. Palettes, OPRI and colour output: Phase 11.
- A deterministic instruction-count benchmark proxy: only if timing proves untrustworthy.
- AGE `ly-cgbE` and `lcd-align-ly-cgbE` to replace the LY/STAT `POLICY` cells: Phase 14.

</deferred>

---

*Phase: 10-CGB Profile, Banking and Register Visibility*
