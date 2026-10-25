# Phase 10: CGB Profile, Banking and Register Visibility - Research

**Researched:** 2026-10-12
**Domain:** Original portable C Game Boy core: second hardware profile (CGB-CPU-E), banked VRAM/WRAM, model-gated I/O visibility, fixtures and CI evidence. No new third-party packages.
**Confidence:** HIGH for codebase sites, test infrastructure and the Mooneye/SameBoy facts read this session; MEDIUM for CGB hardware values that no hardware oracle covers (they are `POLICY`/`ORACLE_SAMEBOY` by D-06).

Provenance tags: `[VERIFIED: path:line]` = I opened the file with Read this session and quote the value verbatim; `[CITED: url]` = external primary source fetched this session; `[ASSUMED]` = training knowledge or inference, needs confirmation. In-repo line numbers are at HEAD `d34bc38`; `src/` equals Phase 9 head `d7e2e0a` (only docs commits since).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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

### Deferred Ideas (OUT OF SCOPE)

- DMG-profile FF4C-FF7F reading `$FF` per `unused_hwio-GS`, and admitting that ROM: hardware-correct but a DMG behaviour change. Candidate for Phase 14 qualification, with an explicit baseline `CHANGES.md` entry.
- The CGB CPU/DMA separate-bus conflict model (D-17).
- DMG OAM DMA sources at E0-FF and ROM (SameBoy mirrors them; D-024's gap), as a separate change if reopened.
- RP/IR (`$3E` vs `$2E`) and FF76/77: Phase 14.
- The CGB STOP path, KEY1 switch and stall: Phase 12. HDMA: Phase 13. Palettes, OPRI and colour output: Phase 11.
- A deterministic instruction-count benchmark proxy: only if timing proves untrustworthy.
- AGE `ly-cgbE` and `lcd-align-ly-cgbE` to replace the LY/STAT `POLICY` cells: Phase 14.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CGB-01 | Select `GBB_PROFILE_CGB_CPU_E`, probe a ROM, query model and execution mode (`$143` bit 7); CGB-only ROMs load on DMG with a flag; mode-specific post-boot state with provenance | Sections "Code-site map" A/B, "Post-boot state", "Mooneye admissions"; D-02..D-07 implementation detail; Corrections C1, C6, C13 |
| CGB-02 | Every DMG-specific behaviour audited and tagged by model; register visibility matrix has a test per cell; KEY0 locked after boot | "Model-gate candidate inventory", "Register visibility implementation", "Validation Architecture"; Corrections C2, C3, C4, C10 |
| CGB-03 | Bank VRAM (2x8 KiB) and WRAM (8x4 KiB) with correct echo RAM and OAM DMA source behaviour | "Banking, echo and OAM DMA", fixture design, metamorphic test; Corrections C7, C8 |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- Original portable C core, explicit ownership/error behaviour, bounded public operations, no hidden globals; host timing/filesystem/UI stay in adapters. [VERIFIED: AGENTS.md "Engineering rules"]
- **Stop after each phase; never auto-advance.** Keep `workflow.auto_advance` and `workflow._auto_chain_active` false. Handoff names the stage/phase completed, the next phase by number/title and one copy-paste GSD command. [VERIFIED: AGENTS.md "Workflow contract"]
- D-069: every deliverable gets an automated check with a negative control; `/gsd-verify-work` needs zero human checkpoints by default. [VERIFIED: AGENTS.md; DECISIONS D-069]
- Phase branch + PR; squash merge only when exact-head CI is green (owner memory `squash-merge-phase-prs`); never trust a stale/skipped run. Public API append-only; update source, API docs, examples, tests and limitation notes together.
- Guard ROM/save/state boundaries against overflow and partial mutation; explicit portable serialisation (no raw struct dumps). No Nintendo boot ROMs, no commercial/private fixtures; every third-party fixture needs documented redistribution rights and a digest.
- Hardware-backed vs differential-oracle vs regression vs private observations are separate evidence classes; declare model applicability and expected failures. Never present another emulator's value as hardware truth.
- Owner preferences: copy small code over adding dependencies (flat dep tree, stdlib-only Python run as `python3 -I`); prefer primary sources (Pan Docs, Mooneye sources, SameBoy/Gambatte as oracles only).
- Privacy-safe Git author; no home paths/emails/machine identifiers in public artifacts (so the benchmark receipt must not record `$HOME` paths or usernames).

## Summary

Phase 10 is mostly a disciplined refactor of one 2,843-line translation unit (`src/core/gabbaboy.c`) plus an audit scanner, a table-driven register matrix, two fixtures, one benchmark A/B mode and a lot of CI wiring. The locked decisions (D-01..D-29) are implementable as written, and the existing repo already has almost every pattern needed: `test_bus.c` synthetic-ROM-in-HRAM, `expect_exit.cmake` + `--self-test` Python verifiers (`verify-libbet-admission.py` is the right precedent for the model-gate scanner, not `verify-support-ledger.py`), configure-time core-mutant tests (ninth-bit / RTC), `VerifyDocContract.cmake`, sibling-suite Mooneye admission by manifest SHA, and a frozen DMG ledger whose inventory check is remove-only (adding tests is safe).

Research found **thirteen places where CONTEXT's assumptions are incomplete or wrong in a plan-affecting way** (Corrections C1-C13 below). The two most important: (1) D-26's staging of `boot_hwio-C` and `unused_hwio-C` as "stop at FF76" cannot hold with the D-07 post-boot table as drafted. `boot_hwio-C` compares IF (`$E1`), NR11/NR12/NR50/NR51/NR52 (`$BF/$F3/$77/$F3/$F1`) long before FF76, and `unused_hwio-C` requires IE bits 5-7 to be stored (it fails at the IE row, ~25 rows before FF76). The CGB column therefore needs extra post-boot cells and an IE-upper-bits model gate, or those two ROMs fail instead of stopping. (2) DEFERRED *writes* cannot be pre-flighted by the existing read-side `read_supported`; they need a post-instruction latch (the existing `serial_unsupported` pattern).

**Primary recommendation:** Keep the CONTEXT wave order, but (a) put the DMG literal pin test and the model-gate scanner first, (b) extend the CGB post-boot table to every register `boot_hwio-C` reads (IF, NR10-NR52 subset, plus those already drafted), (c) store IE bits 5-7 on the CGB profile only behind a model gate, (d) implement DEFERRED writes with a generalised `bus_unsupported` latch, and (e) solve the compat DIV phase now: any counter value 0x2678..0x267B (either half-dot phase) satisfies `boot_div-cgbABCDE` (verified by a scratch sweep, below); use `0x2678`.

## Corrections and gaps found in CONTEXT (read first)

| # | Finding | Evidence | Impact |
|---|---------|----------|--------|
| C1 | **D-07 post-boot table is missing registers that `boot_hwio-C` checks before FF76.** The ROM loops FF00..FF7F and jumps to `mismatch` on the first differing checked byte. Expected rows include IF `$E1`, NR11 `$BF`, NR12 `$F3`, NR50 `$77`, NR51 `$F3`, NR52 `$F1`. The core's DMG reset leaves IF=0 (reads `$E0`), NR12 envelope 0, `apu_nr50=0`, `apu_nr51=0xFF`, NR52 reads `$F0`. | `hwio_data` rows quoted below; `gabbaboy.c:643` `m->interrupt_flags = 0;`, `:651` `m->apu_nr50 = 0u; m->apu_nr51 = 0xFFu; m->apu_power = 1u;` | CGB compat column needs ~6 extra cells (IF, ch1 duty/envelope/enabled, NR50, NR51). DMG column must keep its literals. Without them `boot_hwio-C` reports FAIL (`d=$42`), not a stop at FF76. |
| C2 | **`unused_hwio-C` fails at the IE row unless IE bits 5-7 are stored.** Its test list contains `test IE %11100000 %00000000 %00000000` and `test IE %11100000 %11100000 %11100000`. Core: `write8` stores `ie = value & 0x1F`, `read8` returns `0xE0 | ie`. | Mooneye `acceptance/bits/unused_hwio-GS.s:108-109` has the same two lines (hardware-verified DMG pass in the GS file), so real DMG also stores them; DMG stays frozen by D-09/D-19 but CGB must store them. | New model gate "IE bits 5-7": DMG keeps read-as-1 (documented policy divergence), CGB profile stores `value & 0xFF`. Add a DMG baseline-neutrality test. Alternative: drop `unused_hwio-C` from Phase 10 (owner call; see Open Questions). |
| C3 | **"Reaching FF76 proves FF00-FF75 passed" is true for `boot_hwio-C` (sequential loop over every address) but false for `unused_hwio-C`.** Its `test_unmapped` rows ($FF03, $FF08-$FF0E, $FF15, $FF1F, $FF27-29, $FF4C-4E, $FF50-67, $FF69, $FF6B-71, $FF74, $FF78-7F) come *after* the FF76/FF77 rows. | Test order read from `misc/bits/unused_hwio-C.s` (below) | The unmapped-cell claims must rest on `test_cgb_visibility` sweeps (D-11), not on the Mooneye stop. Document the narrower claim in `fixtures/mooneye-cgb/ELIGIBILITY.md`. |
| C4 | **On DMG, writes to FF4F/FF70 etc. are silently ignored, not "fail closed".** `write8` has no `else` that stops; only *reads* are pre-flighted by `read_supported`. | `gabbaboy.c:1313-1317` (last `else if` branches, no default) | D-19(3)'s exclusion rationale is imprecise; the metamorphic test may include or exclude FF4F/FF70 *writes* on DMG (include them: they must be no-ops, which is a stronger DMG-identity check). Reads of FF4F/FF70 on DMG still stop `UNSUPPORTED_BUS`. |
| C5 | `_Static_assert` **does have precedent** in the repo (D-21 says none). | `src/runner/acceptance.c:675` `_Static_assert(GBB_LDBB_FRAME_BYTES == GBB_ACCEPT_FRAME_SHADE_BYTES, "frame buffer size");`, `src/player/audio.c:15,17`; acceptance.c is compiled in the Windows CI leg | No toolchain risk. Put header-size assertions in `gabbaboy.c` (C only); a header assertion would need `static_assert` for C++ consumers. |
| C6 | **DMG post-boot P1 is `$FF` in the core, not `$CF`.** `joypad_select = 0x30`, no buttons, so `joypad_value` = `0xC0|0x30|0x0F`. Pan Docs says `$CF`. Several other DMG literals also differ from Pan Docs (IF `$E0` vs `$E1`, NR50/51/52, STAT `$86` vs `$85`, OBP0/1 `$FF`). | `gabbaboy.c:720` `m->joypad_select = 0x30;`, `:729-735` `joypad_value`; Pan Docs table [CITED: gbdev.io/pandocs/Power_Up_Sequence.html] | D-06's "DMG column equals pre-refactor literals" must record the *implemented* value with provenance `POLICY` and a `diverges-from-pandocs` note, not the Pan Docs value. Do not "fix" them (D-19). |
| C7 | **SVBK read-back is the raw 3-bit value in SameBoy** (write 0 reads `$F8`, effective bank 1). | SameBoy `Core/memory.c` @ master `c71f110e` (2026-10-11): write `gb->cgb_ram_bank = value & 0x7; if (!gb->cgb_ram_bank) { gb->cgb_ram_bank++; } gb->io_registers[GB_IO_SVBK] = value \| ~0x7;`, read `return gb->io_registers[GB_IO_SVBK];` | Store `svbk` raw (3 bits) plus effective bank; read `0xF8 \| svbk`. Label the cell `ORACLE_SAMEBOY`. Fixture cell (b) must expect `$F8` after writing 0. |
| C8 | **Other tests reach into `m->vram`/`m->wram` by field name.** `tests/test_rtc3test.c:19` `#include "../src/core/gabbaboy.c"` and `:109` `return &m->vram[MAP_BASE + row * 32u + col];`; `test_mbc5_internal.c:1` and `test_mbc3_rtc_internal.c:8` also include the core. | grep + Read | Changing `vram` to `[2][8192]` breaks `test_rtc3test.c:109` (becomes `m->vram[0][...]`). Include in the array-reshape plan's file list. Also `sizeof(m->vram)` at `gabbaboy.c:1437` doubles silently (see Pitfalls). |
| C9 | Local `rgbasm` is **v1.0.4**; all fixture scripts require **v1.0.1** and exit otherwise. | `rgbasm --version`; `reproduce-mbc5-banking.sh` tool check | Executors must fetch the pinned macOS archive (manifest: `rgbds-macos.zip`, sha256 `2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645`) into a temp dir and put it first on `PATH`; the `cgb-banking` manifest reuses the same pin. |
| C10 | **DEFERRED writes need a latch.** `instruction_reads_supported` (`:2385`) only inspects read operands; stores (`LDH (a8),A`, `LD (a16),A`, `LD (C),A`, `LD (HL),r`, pushes) are never pre-checked. The only existing precedent is `serial_unsupported` (`:346` field, `:1212`/`:1217` set, `:2766-2770` reported after `execute`). | Read | Generalise to a `bus_unsupported` latch recording the address; DEFERRED reads keep stopping atomically via `read_supported`; DEFERRED writes stop *after* the instruction retires with the write dropped. Document this asymmetry in `docs/cgb-profile.md`. |
| C11 | The Mooneye runner is **C-table-driven**: suites are admitted by SHA-256 of the raw manifest (`main.c:103-106`), per-ROM pass/fail callback PCs come from a linker `.sym` via `reproduce-mooneye-mbc.sh --facts`, and `category_names[2]={"mbc2","mbc5"}` is hard-coded (`main.c:393`). The `--facts` extractor requires **exactly one `quit_ok`** per test; `boot_regs-cgb` and `boot_div-cgbABCDE` end in `quit_check_asserts` (single shared callback, like `tim00`: pass_cb == fail_cb). | `main.c:51-106`, `reproduce-mooneye-mbc.sh:46-67`; both CGB sources read | A third sibling suite means: new manifest + `MOONEYE_CGB_MANIFEST_SHA256`, new `cgb_cases[]` rows between `gbb:cgb-rows-begin/end`, a `fixture_case.profile` + `expect_unsupported_bus` field, a CGB verifier copied from `VerifyMooneyeMbc.cmake`, and a facts path that handles assert-style ROMs (copy the parent's approach, not the mbc script's). This is the largest single item in Wave 4. |
| C12 | The benchmark workload is tiny: tracer 1M half-dots, baseline `median_core_ns` **8,968,500** (sd 359,430, n=10, no-trace). | `tests/baseline/dmg-cpu-b-v1.txt` `bench.advisory.no_trace.*` | Per-sample noise is ~4%; a +3% effect needs paired interleaving (D-22 already) and n=30. Do not tighten the +5% review trigger. |
| C13 | **Compat DIV phase is solvable now.** Writing an equivalent original guest (27 NOPs, LDH DIV, push; 57/56/57/57/58 NOP groups) and sweeping `divider_counter` in a scratch copy of the core: exactly `0x2678`..`0x267B`, with either `divider_phase`, produce `B..L = 27 28 28 29 2A 2C`. | Scratch sweep this session (output: `pass d0=0x2678 phase=0/1` ... `0x267b`; `total passing ... 8`) | Use `divider_counter=0x2678`, `div=0x26`, `divider_phase=0` for the compat column, provenance `HW_TEST` (applicability "CGB A-E"). Re-run the sweep against the real derived ROM before freezing (the real ROM adds no code before the first NOP per `common.s`, but confirm). DMG literal is `divider_counter = 0xAB00u` (`:647`). |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Profile/mode derivation, post-boot tables, banking, register decode, OAM DMA source | Core library (`gabbaboy.c`) | none | Hardware-visible state; single TU, no host dependency |
| `--profile`/`--model` selection, receipt labels | Runner adapter (`src/runner`) | Core API | Host policy; core only receives `gbb_profile` |
| Player profile choice | Player adapter (`select_profile` seam) | none | Stays DMG-only; Phase 11 adds `--model` |
| Model-gate scanner, bench A/B, fixture reproduction | Test/CI tooling (stdlib Python, CMake `-P`, bash) | none | No runtime dependency; CI-only |

## Standard Stack

No new third-party packages. [VERIFIED: owner preference file `prefer-copy-over-dependency`; D-06/D-08/D-22 specify stdlib-only]

| Tool | Version in use | Purpose | Status |
|------|---------------|---------|--------|
| C17, `c_std_17`, extensions off | Apple clang 21.0.0 local; GCC/Clang Linux, MSVC Windows in CI | Core | `[VERIFIED: CMakeLists.txt:23-26]` |
| CMake / CTest | 4.4.3 local; floor 3.25.3 CI leg | Build, tests, `-P` verifiers | `[VERIFIED: cmake --version]` |
| Python 3 stdlib, run as `python3 -I` / `${Python3_EXECUTABLE} -I` | 3.14.4 local | `verify-model-gates.py`, bench A/B | tests/CMakeLists.txt:740 already does `find_package(Python3 COMPONENTS Interpreter REQUIRED)` |
| RGBDS | **v1.0.1 pinned** (local 1.0.4, see C9) | `fixtures/cgb-banking` | `[VERIFIED: fixtures/mbc5-banking/manifest.json]` |
| WLA-DX 10.7 (`91c52b1f...`), `jq`, `curl`, `patch` | built by script from pinned source | Mooneye CGB derivatives | `[VERIFIED: fixtures/mooneye/manifest.json builder block]`; `wla-gb` not installed locally (script builds it) |

### Package Legitimacy Audit

| Package | Registry | Verdict | Disposition |
|---------|----------|---------|-------------|
| (none) | - | - | Phase installs no external packages; `gsd-tools query package-legitimacy check` not applicable. RGBDS and WLA-DX are existing digest-pinned build tools. |

**Packages removed due to SLOP:** none. **Flagged SUS:** none.

## Code-site map (current HEAD)

### A. Public header `include/gabbaboy/gabbaboy.h`
- `:13-15` `typedef enum { GBB_PROFILE_DMG_CPU_B = 1 } gbb_profile;` -> append `GBB_PROFILE_CGB_CPU_E = 2`.
- `:17-40` `gbb_error`, last value `GBB_NO_RTC` (line 39, value 19). Append `GBB_UNSUPPORTED_EXECUTION_MODE` (=20); keep the trailing-comment style. Fix the comma on line 39.
- `:126-129` comment "The only implemented model is bootless DMG-CPU-B deterministic post-boot." must change in the commit that flips create (D-01).
- `:144-149` loader doc says "the CGB flag at $143 is ignored on the DMG-CPU-B profile" (still true; add the CGB-profile sentence).
- `:246-248` `gbb_copy_frame` doc: add D-05. `:287-290` `gbb_peek_ram` doc: say "follows the selected WRAM bank".
- New: `gbb_exec_mode`, `gbb_cgb_support`, `GBB_INFO_*`, `gbb_info`, `GBB_INFO_SIZE_V1`, `gbb_probe_rom`, `gbb_get_info` (D-02 verbatim). Layout check: 4 x u32 (16) + 4 x u8 (4) + 2 x u32 (8) = 28, no padding. Assert `sizeof(gbb_info) == GBB_INFO_SIZE_V1` in `gabbaboy.c`.
- Every `GBB_*`/`gbb_*` identifier used in `docs/native-integration.md` must be a real declaration (comments are stripped by `VerifyDocContract.cmake`), so `GBB_INFO_*` must be `#define`s, not comment-only.

### B. Core `src/core/gabbaboy.c`

| Site | Lines | Change |
|------|-------|--------|
| Defines | 6-19 | Add `GBB_VRAM_BANKS 2u`, `GBB_WRAM_BANKS 8u`, bank sizes; named timeline macros for the ADR (see "D-070 verification") |
| `struct gbb_instance` | 277-372; `wram[8192]` :284, `vram[8192]` :286, `serial_unsupported` :346 | `vram[2][8192]`, `wram[8][4096]`; add `profile`, `exec_mode`, `vram_bank`, `wram_bank` (effective 1..7), `svbk` (raw), CGB IO latches (key1 bit0, bcps/ocps, ff72..ff75), generalised `bus_unsupported` + address. `gbb_create` uses `calloc` (:2082) so **every new field is 0 until `reset_state` sets it**; `wram_bank` must be set to 1 there |
| `reset_state` | 632-727 | Consume `post_boot[]` (D-06). `memset(m->wram/vram...)` at :678/:680 already clear whole arrays (`sizeof` correct). DMG F branch :635. Reset must clear banks, latches |
| `cpu_vram_access_allowed` / `cpu_oam_access_allowed` | 747/751 | Unchanged (single gate in front of both VRAM banks, D-14) |
| `read8` | 812-949 | :813-814 DMA conflict; :854-867 PPU regs; :868-869 IF/IE; :870-871 VRAM `m->vram[address - 0x8000]` -> `m->vram[m->vram_bank][...]`; :874-944 cartridge; :945-946 WRAM + echo; :947 HRAM; :948 `return 0xFF`. Insert `if (address >= 0xFF4Cu && address <= 0xFF7Fu) return io_read_cgb(m, address);` after :867 (DMG path returns `0xFF` exactly as the fall-through does today) |
| `write8` | 990-1318 | :991-992 DMA conflict; :1065-1067 VRAM; :1313-1314 IF/IE; :1315-1316 WRAM + echo; add `FF4C..FF7F` branch before :1313 (DMG: no-op); IE branch gains the CGB model gate |
| `read_supported` | 1331-1349 | Becomes profile-aware (`m` is already a parameter and may be `NULL`); CGB adds FF03, FF08-FF0E, FF15, FF1F, FF27-FF2F (these are *unmapped-reads-`$FF`* cells) and FF4C-FF75 except DEFERRED cells |
| PPU VRAM reads | 1409-1410 (`ppu_tile_color`), 1437-1438 (`ppu_background_color`, bound `sizeof(m->vram)`) | `m->vram[0]` and `sizeof(m->vram[0])` (D-14). Objects reach VRAM only through `ppu_tile_color` (`:1473-1510`) |
| `dma_source_read` | 1724-1732 | DMG branch byte-identical; add CGB branch (D-16). Factor the cartridge switch of `read8` (:874-944) into `cart_read(m, address)` and call it from both |
| `dma_advance_half_dot` | 1744-1758 | Unchanged this phase (period macro `GBB_DMA_BYTE_PERIOD_HALF_DOTS 8u`, :12) |
| `gbb_copy_frame` | 1944-1972 | After argument validation (:1947-1962), before `frame_generation == 0` (:1963): `if (instance->profile == GBB_PROFILE_CGB_CPU_E) return GBB_UNSUPPORTED_PROFILE;` |
| `validate_header` | 2006-2076 | Add `profile` parameter and fill new `cartridge_info` fields (`cgb_flag`, `cgb_support`); put the PGB rejection **last** (after :2065) so every existing error keeps precedence and probe/load parity is trivial |
| `gbb_create` | 2078-2087 | :2081 `if (profile != GBB_PROFILE_DMG_CPU_B) return GBB_UNSUPPORTED_PROFILE;` -> switch; store `profile`; `reset_state` |
| `gbb_reset` | 2097-2111 | No change to mode (stored at load); `reset_state` re-applies the table |
| `gbb_load_rom` | 2113-2146 | Commit `exec_mode` with the ROM swap (after :2132-2135 allocations succeed, before `reset_state`) |
| `instruction_reads_supported` | 2385-2415 | Unchanged logic; DEFERRED reads flow through `read_supported` |
| STOP | `execute` :2574 `case 0x10: m->pc=(uint16_t)(pc+2); m->stopped=1; break;`; run loop :2650-2674, :2758-2765 | CGB + KEY1 armed -> do not set `stopped`; set latch (D-23) |
| Post-execute reporting | 2766-2770 | Replace `serial_unsupported` check with `bus_unsupported` (keep behaviour for serial) |
| `gbb_peek_ram` | 2837-2843 | `:2839` `instance->wram[address - 0xC000]` etc. -> bank-aware helper shared with `read8`/`write8` |

### C. Runner and acceptance
- `src/runner/main.c`: `gbb_create(GBB_PROFILE_DMG_CPU_B` at :214 (`run_guest`), :241 (`observe_case`), :295 (`run_original_tracer`); label literals `profile=DMG-CPU-B` at :266, :280, :303; option parsing :355 (`--model`), :373 (model validation), :382 (non-acceptance rejects `--model`). `suites[]` :103-106; `fixture_case` struct :32-49.
- `src/runner/acceptance.c`: create sites :381, :829, :1008; `model=dmg-cpu-b` literals :336, :341, :776, :794, :839, :889, :892, :1051, :1111, :1116, :1149, :1155, :1161, :1166; default model :1186; the rejection to remove :1196-1198 (`if (strcmp(model, "dmg-cpu-b") != 0) { printf("... reason=unsupported-profile model=%s\n" ...`). Frame uses: :153 and :686 (`gbb_copy_frame`) must tolerate `GBB_UNSUPPORTED_PROFILE` on the CGB profile.
- `src/runner/cases.c:325-327` `gbb_case_model_known` already accepts `cgb-cpu-e`. `acceptance.h:94-95,136-138,156` comments say "only dmg-cpu-b can execute".
- Frozen test `acceptance_libbet_excluded_cgb-cpu-e` (`tests/acceptance/CMakeLists.txt:125-127`, name is in the frozen ledger) runs `--case libbet --model cgb-cpu-e` against `model_pass=dmg-cpu-b`; applicability excludes it **before** the :1196 check, so its expected output `status=excluded reason=unsupported-model` is unaffected. Keep this ordering.
- `--profile dmg|cgb` (D-25): `--model` already exists in acceptance mode only. Implement `--profile` as sugar mapped through the single `model <-> profile` function (`dmg`->`dmg-cpu-b`, `cgb`->`cgb-cpu-e`) and allow it in the manifest/tracer modes (currently `main.c:382` rejects model flags outside acceptance). Do not create a second selector.
- Player: six `gbb_create(GBB_PROFILE_DMG_CPU_B` sites (`src/player/main.c:150,500,919,1718,1964,2202`). Create's signature is unchanged, so no compile change is required; the optional `select_profile()` seam is a one-function replacement. Player tests are macOS-only builds.

## System Architecture (data flow)

```
host --gbb_probe_rom(profile, rom, size, &info)--> validate_header(profile) --no alloc--> gbb_info
host --gbb_create(profile)--> instance{profile, exec_mode=NONE} --reset_state(post_boot[profile,mode=compat])
host --gbb_load_rom--> validate_header(profile) --ok--> copy ROM, derive exec_mode($143, profile)
                                        --> commit with swap --> reset_state(post_boot[profile,mode])
guest CPU --read8/write8--> addr class:
   0000-7FFF/A000-BFFF --> cart_read()/mapper (shared by CPU and OAM DMA)
   8000-9FFF           --> cpu_vram_access_allowed --> vram[vram_bank]     (PPU reads vram[0] only)
   C000-CFFF,E000-EFFF --> wram[0]
   D000-DFFF,F000-FDFF --> wram[wram_bank]    (DMG pins wram_bank=1, vram_bank=0)
   FF4C-FF7F           --> io_visibility[] (DMG: ignore/stop) | CGB-compat | CGB
   DEFERRED cell       --> read: read_supported=false -> GBB_STOP_UNSUPPORTED_BUS (atomic)
                           write: bus_unsupported latch -> stop after instruction
OAM DMA byte --> dma_source_read(profile): DMG frozen envelope | CGB: cart/VRAM/WRAM-bank/E0-FF=$FF
```

## Model-gate candidate inventory (D-08)

**R1 scale:** the file has **126** top-level function definitions (counted with a brace-depth scan this session; includes 9 `gbb_test_*` seams and one-liners like `static uint16_t hl(...) { ... }`). Scanner must handle multi-line parameter lists (e.g. `gbb_copy_battery`, `gbb_queue_events`). Recommended id policy: **branch-level gates get unique `GATE-NN`; function-level tags on model-neutral functions share `GATE-00` with a mandatory `basis=`** (keeps the doc bijection at ~60 rows instead of ~190). Scanner R1 must accept `GATE-00` only with `BOTH` + `basis=`.

Candidate branch-level gates (line numbers at HEAD; final numbering is Claude's discretion):

| Cand. | Site | Behaviour | Proposed tag |
|-------|------|-----------|--------------|
| G01 | `reset_state` :635 | F from header checksum (`0xB0`/`0x80`) | `DMG_ONLY` GUARD=`model_is_dmg` (CGB F=`$80` always) |
| G02 | :634,636-638 | A/BC/DE/HL/PC/SP literals | table-driven; `BOTH` per column |
| G03 | :639,647 | DIV `0xAB`, `divider_counter 0xAB00` | `UNKNOWN research:14` for CGB-mode, `HW_TEST` compat (C13) |
| G04 | :643 | IF = 0 | DMG literal; CGB `$01` (C1) |
| G05 | :641 | `serial_control = 0x7Eu` | compat `$7E`, CGB `$7F` |
| G06 | :667 | `dma_register = 0xFFu` | DMG `$FF`, CGB `$00` |
| G07 | :710,715-717 | LCDC `0x91`, BGP `0xFC`, OBP `0xFF` | same both; OBP uninit per Pan Docs |
| G08 | :648-653 | APU zero state, `nr50=0`, `nr51=0xFF` | CGB cells needed (C1); `UNKNOWN research:14` |
| G09 | :720 | `joypad_select = 0x30` | `BOTH` (reads `$FF`; C6) |
| G10 | :686-689 | `ppu_mode=2`, `ly=0`, `stat=0` | `UNKNOWN research:11` (LY/STAT policy) |
| G11 | :678-681 | RAM zero fill | `BOTH` basis=POLICY D-025 |
| G12 | `read8` :813-814, `write8` :991-992 | OAM-DMA CPU bus conflict | tag `UNKNOWN expected-failure:cgb-separate-buses` (D-17 keeps the DMG rule on CGB, so `DMG_ONLY` + guard would be false; R4 would reject) |
| G13 | :821, :1219 | SC read mask `0x7E`, write mask `0x81` | `UNKNOWN research:14` (CGB SC bit 1 fast clock is not modelled; gap not listed in D-10) |
| G14 | :822-853, :840-845, :1231-1236 | APU read masks, wave RAM aliasing | `UNKNOWN research:14` |
| G15 | :855-857 | STAT read | `BOTH` basis |
| G16 | :854, :1146-1171 | LCDC (bit 0 meaning differs on CGB), LCD on/off timing | `UNKNOWN research:11` |
| G17 | :948 + new | FF4C-FF7F decode | `CGB_ONLY` GUARD=`model_is_cgb` |
| G18 | :747, :871, :1066 | VRAM CPU gate | `UNKNOWN research:11` |
| G19 | :751, :873, :1069 | OAM CPU gate | `UNKNOWN research:11` |
| G20 | :874-944 | cartridge read | `BOTH` basis=cartridge side |
| G21 | :945-946, :1315-1316, :2839-2840 | WRAM/echo through bank | `BOTH` basis="DMG pins wram_bank=1" |
| G22 | :868-869, :1314 | IE/IF masks | **new CGB gate for IE bits 5-7 (C2)**; IF read mask `0xE0` `BOTH` |
| G23 | :1172-1175, :604-617 | STAT write spurious IRQ | `UNKNOWN research:14` (seed) |
| G24 | :1141-1145, :741-745, :1373-1384 | JOYP write/IF/events | `UNKNOWN research:14` (seed) |
| G25 | :1183-1187, :1724-1758 | DMA register restart, source map, byte period | source map: `DMG_ONLY` DMG path + CGB branch `CGB_ONLY`; period `UNKNOWN research:12` |
| G26 | :1193-1198, :1852-1860 | DIV write / APU frame sequencer tap (bit 12) | `UNKNOWN research:12` (tap moves at double speed) |
| G27 | :1199-1210, :960-988, :1831-1840 | TIMA/TMA/TAC/reload | `UNKNOWN research:14` (seed) |
| G28 | :1211-1226, :1841-1851 | Serial | `UNKNOWN research:14` |
| G29 | :1227-1312, :794-804, :1760-1826, :1861-1909 | NR52/APU writes, power-off, sequencer | `UNKNOWN research:14` |
| G30 | :19, :414-418 | `GBB_AUDIO_HPF_Q15 32648` (DMG capacitor constant) | `UNKNOWN research:14` (CGB HPF differs) |
| G31 | :1331-1349 | `read_supported` allow-list | `CGB_ONLY` branch for CGB widening |
| G32 | FEA0-FEFF (excluded by :1332) | Unusable region | `UNKNOWN research:14`; stays fail-closed on both |
| G33 | :1397-1440, :1450-1530 | tile/map fetch (VRAM bank 0 only), object X-priority (:1495) , DMG palette shade (:1515-1531) | `UNKNOWN research:11` (attributes, OPRI) |
| G34 | :1532-1722 | PPU fetcher/transfer timing | `UNKNOWN research:11` |
| G35 | :1944-1972 | `gbb_copy_frame` DMG shade output | `DMG_ONLY` GUARD=`model_is_dmg` + CGB `UNSUPPORTED_PROFILE` |
| G36 | :2006-2076 | header validation | `BOTH` basis (D-24); PGB reject `CGB_ONLY` |
| G37 | :2078-2087 | profile validation | `BOTH` |
| G38 | :2574, :2650-2674, :2758-2765 | STOP (incl. DIV reset on STOP :2759-2762) | `UNKNOWN research:12` (seed) |
| G39 | :2519-2523, :1389, :2550, :2561, :2636-2641, :2744-2753 | HALT / halt bug | `BOTH` basis="no SM83 opcode difference" (seed) |
| G40 | :2315-2318, :2329-2374, :2605-2622 | opcode decode, lockup on illegal ops, interrupt entry | `BOTH` basis="no SM83 opcode difference" |
| G41 | :2837-2843 | peek | `BOTH` basis |

Existing code that must not collide with the scanner or the configure-time mutants: JOYP mutant needs the text `if ((m->joypad_select & 0x20u) == 0)` to occur exactly once (`tests/acceptance/CMakeLists.txt:288`); ninth-bit needs `& 1u) << 8` exactly once (`tests/CMakeLists.txt:209`); seven RTC anchors (`:81-91`). Never quote those strings in tags or comments, and do not duplicate them while refactoring.

## Post-boot state (D-06/D-07 implementation detail)

**DMG literals to pin (pre-refactor, `[VERIFIED: gabbaboy.c:634-727]`):** `m->a = 0x01;` F = `m->rom != NULL && m->rom_size > 0x14Du && m->rom[0x14Du] != 0 ? 0xB0u : 0x80u`; `b=0x00; c=0x13; d=0x00; e=0xD8; h=0x01; l=0x4D; pc=0x0100; sp=0xFFFE; div=0xAB; stat=0; tima=tma=tac=0; serial_data=0; serial_control=0x7Eu; ie=0; interrupt_flags=0; ime=0; divider_phase=0; divider_counter=0xAB00u; apu_nr50=0u; apu_nr51=0xFFu; apu_power=1u; dma_register=0xFFu; lcdc=0x91; bgp=0xFC; obp0=obp1=0xFF; wy=wx=scx=scy=lyc=0; ly=0; ppu_mode=2; joypad_select=0x30; joypad_buttons=0`. The pin test should read these through the public API (CPU regs via trace/`gbb_test_cpu_snapshot`, IO via a synthetic guest that stores LDH reads in HRAM) and compare against a literal array typed independently of the table.

**What `boot_hwio-C` reads in compat mode (hardware oracle), quoted from `misc/boot_hwio-C.s` @ `31510e12`:**

```
;   mask bits  values                                   address of first byte
.db %11110111, $FF, $00, $7E, $FF, $FF, $00, $00, $F8 ; $FF00
.db %11111111, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $E1 ; $FF08
.db %11111111, $80, $BF, $F3, $FF, $BF, $FF, $3F, $00 ; $FF10
.db %11111111, $FF, $BF, $7F, $FF, $9F, $FF, $BF, $FF ; $FF18
.db %11111111, $FF, $00, $00, $BF, $77, $F3, $F1, $FF ; $FF20
.db %00110101, $FF, $FF, $00, $00, $FF, $00, $00, $FC ; $FF40
.db %00111111, $00, $00, $00, $00, $FF, $FF, $FF, $FE ; $FF48
.db %11111111, $C8, $FF, $D0, $FF, $FF, $FF, $FF, $FF ; $FF68
.db %11111111, $FF, $FF, $00, $00, $FF, $8F, $00, $00 ; $FF70
```
(first value of each row is the mask byte; the eight values follow; rows FF28, FF30-FF3F (mask 0), FF50-FF67 and FF78 not shown are `$FF`/unchecked.) The read loop uses `ld a,(hl)` from `$FF00` upward, so each address from FF00 to FF75 must be *readable* (not stop) on the CGB profile, and checked bytes must match.

Delta of the CGB compat column over today's DMG literals that this forces (each becomes a table cell with provenance `HW_TEST`, src `Mooneye boot_hwio-C`):

| Field | DMG literal | Compat requirement | Note |
|-------|-------------|--------------------|------|
| IF | 0 (reads `$E0`) | `$E1` (flag bit 0 set) | |
| NR11 duty | 0 (reads `$3F`) | reads `$BF` (`duty_length` top bits `10`) | |
| NR12 envelope | 0 | `$F3` | |
| NR50 / NR51 | `0` / `0xFF` | `$77` / `$F3` | |
| NR52 | reads `$F0` | `$F1` (ch1 bit) | needs `apu_pulse[0].enabled=1`; to keep output silent set `volume=0` (policy) and a valid `timer`/`frequency`; record as `POLICY` with reason "Pan Docs/hwio-C require the status bit; no boot chime is synthesised" |
| SC | `0x7E` stored | reads `$7E` | CGB mode `$7F` (Pan Docs) |
| FF4C/FF4D/FF4E | n/a | `$FF` | |
| FF4F | n/a | `$FE` | |
| FF68 / FF6A | n/a | `$C8` / `$D0`, bit 6 always reads 1 | read = stored `\| 0x40` |
| FF72 FF73 FF74 FF75 | n/a | `$00 $00 $FF $8F` | FF74 `$FF` in compat, R/W in CGB mode (D-10) |

Compat CPU row (hardware, `misc/boot_regs-cgb.s`): `assert_a $11  assert_f $80  assert_b $00  assert_c $00  assert_d $00  assert_e $08  assert_h $00  assert_l $7C` and SP `$FFFE` (`EXPECTED_SP $FFFE`). The ROM header uses licensee `.licenseecodenew "ZZ"`, so it takes the non-Nintendo branch (B=0, HL=`$007C`), exactly D-07's `PANDOCS` branch cell; add the synthetic-header test for B = title sum and HL = `$991A` (B `$43`/`$58`) [CITED: gbdev.io/pandocs/Power_Up_Sequence.html notes 1-2: "If the old licensee code is $01, or it is $33 and the new licensee code is "01", B is the sum of all 16 title bytes"; "If B is $43 or $58 on CGB ... HL is $991A. Otherwise HL is $007C."]. Title bytes are `$134..$143` inclusive (16 bytes).

CGB-mode CPU row from Pan Docs (A `$11`, F `$80`, B/C `$00`, D `$FF`, E `$56`, H `$00`, L `$0D`) [CITED: same page]; no hardware oracle, so `PANDOCS`. The `HW_TEST` rule in D-06 ("never outside compat") holds.

**Compat DIV (`boot_div-cgbABCDE`):** assertions `assert_b $27 assert_c $28 assert_d $28 assert_e $29 assert_h $2a assert_l $2c` after `nops 27`, `LDH DIV`, 57/56/57/57/58 NOP groups. Solution derived analytically and confirmed by scratch sweep: counter at entry in `0x2678..0x267B` (read happens 34 M-cycles = 136 T after entry; DIV page `0x27` needs offset 0..3 after the page boundary). Canonical choice `0x2678` ("immediately after DIV has incremented", the test's own comment).

## Register visibility implementation (D-09..D-12)

- `io_visibility[]` row shape suggestion: `{addr, {dmg: IGNORE_STOP}, {cgb: kind, read_value/ mask, write_effect, impl|deferred(n)}, {compat: ...}, src}` with kinds `CONST_FF`, `STORE_MASK(mask_or)`, `BANK`, `DEFERRED`. Sweep FF00-FF7F must find a row for every address (the control "deleting a row fails" needs a total table; include rows for addresses that are handled by existing code paths with `kind=EXISTING`).
- **KEY0 (FF4C):** read `$FF`, write ignored in both CGB columns; there is no boot-time writable window to model (mode is fixed at load). SameBoy confirms boot-only writability (`if (GB_is_cgb(gb) && !gb->boot_rom_finished)`) [CITED: SameBoy Core/memory.c @ c71f110e].
- **VBK (FF4F):** read `0xFE | vram_bank` in both CGB columns (SameBoy `return gb->cgb_vram_bank | ~0x1;` for any CGB hardware; matches `hwio-C` `$FE`); write takes effect only in `exec_mode == GBB_MODE_CGB` (SameBoy `if (!gb->cgb_mode) return;`).
- **SVBK (FF70):** compat reads `$FF`, ignores writes; CGB reads `0xF8 | svbk_raw`, writes store `value & 7` raw and set effective bank (`0 -> 1`) (C7).
- **KEY1 (FF4D):** CGB `0x7E | armed`; compat `$FF`, write ignored (SameBoy `if (!gb->cgb_mode) return;`). STOP with `armed` -> latch (D-23).
- **BCPS/OCPS:** read `stored | 0x40` (SameBoy `| 0x40`); compat initial `$C8`/`$D0`, CGB-mode initial `$C0` `POLICY [VERIFY]`. BCPD/OCPD: compat `$FF`/ignored (no auto-increment), CGB mode `DEFERRED(11)`. OPRI: compat `$FF`, CGB mode `DEFERRED(11)`.
- **HDMA1-4** `$FF` read, write accepted and dropped; **HDMA5** write `DEFERRED(13)`, read `$FF`. **RP** CGB mode `DEFERRED(14)`; compat `$FF`. **FF76/FF77** `DEFERRED(14)` both columns (reads stop at preflight; writes latch).
- **Read-preflight rule for DEFERRED reads:** `read_supported` must return false for a DEFERRED read address in the active column. The existing `instruction_reads_supported` already covers `LD A,(a16)`, `LDH`, `LD A,(C)`, `(HL)` forms, stack pops and CB `(HL)`. It also checks the opcode/operand bytes themselves via `read_supported(m, instruction_address(...))`, so a ROM placed so that code straddles a DEFERRED address stops too.
- **Latch semantics (C10):** `bus_unsupported` set in `write8` for DEFERRED writes and CGB `STOP` with KEY1 armed; checked right after `execute()` where `serial_unsupported` is checked today (:2766-2770); cleared in `reset_state`. Interrupt-entry pushes (:2611-2622) can also hit it; the post-check still reports it on the next instruction boundary, and the fuzz invariant ("works or stops UNSUPPORTED_BUS") holds.
- **Test seam for "stop reason and address" (D-11):** `gbb_run_result` carries no address for UNSUPPORTED_BUS. Add a non-header `gbb_test_last_unsupported_address(const gbb_instance*)` in the same style as `gbb_test_observer_*` (tests declare it `extern`; nothing in CMake or CI scans exported symbols, `grep gbb_test` in `cmake/ .github/ tests/scripts/` is empty), or assert via one-cell-per-run guest layout plus trace PC. Keep it out of the public header (D-19 "must not become public ABI").
- **IE (C2):** gate `ie` storage: `write8` `:1314` `m->ie = (uint8_t)(value & 0x1Fu)` becomes mask `model_is_cgb(m) ? 0xFFu : 0x1Fu`; `read8` `:869` `0xE0 | ie` becomes `0xE0 | ie` for DMG, `ie` for CGB (CGB stores all 8 bits, reads them back). Interrupt logic already masks with `0x1Fu` (`pending_interrupt` :2606). Hardware evidence: `unused_hwio-C` (hardware pass: CGB, AGB, AGS) and `unused_hwio-GS`.

## Banking, echo and OAM DMA (D-13..D-19)

- Address helpers (suggested, static inline, DMG-hot): `wram_index(m, a)`: `a in C000-CFFF -> wram[0][a-C000]`, `D000-DFFF -> wram[m->wram_bank][a-D000]`, `E000-EFFF -> wram[0][a-E000]`, `F000-FDFF -> wram[m->wram_bank][a-F000]`. One helper used by `read8`, `write8`, `gbb_peek_ram`. On DMG `wram_bank == 1`, so D000+ equals the old flat `wram[0x1000..0x1FFF]`, and F000-FDFF equals old `wram[0x1000..0x1DFF]` (the old echo `address - 0xE000` maps F000 to index 0x1000: identical).
- `dma_source_read` CGB mapping per D-16 (pages 00-7F and A0-BF through the extracted `cart_read`, 80-9F `vram[vram_bank]`, C0-CF `wram[0]`, D0-DF `wram[wram_bank]`, E0-FF `$FF`). SameBoy's `GB_dma_run` agrees: sources `< 0xE000` use the normal memory map, `>= 0xE000` on CGB write `0xFF` to OAM, on DMG read `src & ~0x2000` [CITED: SameBoy Core/memory.c @ c71f110e]; label `ORACLE_SAMEBOY`. DMG frozen by `test_dma.c:329-340` (`unmapped_pages {0x00, 0xA0, 0xBF, 0xE0, 0xFE}`).
- `dma_source_read` is `const` and called per DMA byte; adding a `m->profile` branch there costs nothing on the DMG CPU path.
- Fixture `fixtures/cgb-banking/` design notes: one `.asm`, two ROMs (`rgbfix -c` => `$143=$80`; plain => `$00`); a third negative-control variant is made in memory by the test. Guest picks the model from the entry A register (DMG profile A=`$01`, CGB profiles A=`$11`, `reset_state`) and mode from its own `$143` byte. Results at C000.. (bank 0 WRAM) read with `gbb_peek_ram`. Two ROMs ⇒ the manifest needs a `fixtures[]` array so `cmake/VerifyFixtureManifest.cmake` (fixtures[] `file`/`size_bytes`/`sha256`) works alongside top-level fields like `mbc5-banking/manifest.json`; `VerifyFixture.cmake` takes a single ROM + manifest and is only usable per-ROM. The LCD must be off for OAM/VRAM readback (guest writes FF40=0 as `banking.asm` does).
- Metamorphic test `banking_dmg_flat_reference`: implement as a **white-box** test that includes `src/core/gabbaboy.c` (like `test_mbc5_internal.c`) and drives `read8`/`write8` directly with LCD off and a fixed-seed PRNG against a flat 8 KiB WRAM + 8 KiB VRAM reference, asserting `vram_bank == 0 && wram_bank == 1` after each step. Control: same sequence on the CGB profile with SVBK/VBK writes must diverge. For the fuzz-step invariant (D-19(4)) in `fuzz_core.c` (public API only) use a `gbb_test_bank_state(const gbb_instance*, uint8_t *vram, uint8_t *wram)` seam.
- Core-mutant controls in the existing style (configure-time exactly-once anchor, `file(READ)/string(REPLACE)`): e.g. echo ignores bank (`F000..` uses `wram[1]`), DMA reads `wram[1]` for D0-DF; each must fail one named `banking_*` case while an unrelated case passes in the mutant (see `mbc5_ninth_bit_mutant_*` at `tests/CMakeLists.txt:209-250`).

## Save-state / serialization (item 5)

There is **no save-state or serialization API**: the only persistence is battery RAM + RTC block (`gbb_copy_battery`/`gbb_import_battery`, header :159-186), and `grep -n -i 'wram\|vram'` over `src/player src/accept src/runner` finds only `gbb_peek_ram` calls. No versioning work is needed (D-19 last paragraph confirmed). Player continuation tests persist cartridge RAM only.

## Mooneye admissions (item 6)

Source files, all at pinned `31510e12eea6286d36eea060a6adde755e1067aa` (fetched raw this session): `misc/boot_regs-cgb.s`, `misc/boot_div-cgbABCDE.s`, `misc/boot_hwio-C.s`, `misc/bits/unused_hwio-C.s`.
- **Verified results headers:** `boot_regs-cgb` "pass: CGB"; `boot_div-cgbABCDE` "pass: CGB ABCDE; fail: ... CGB 0"; `boot_hwio-C` and `unused_hwio-C` "pass: CGB, AGB, AGS". MIT, same notice as parent.
- **Compat mode:** none of the four defines `CART_CGB` (grep of `CART_`/`define` over the four files returns only `EXPECTED_SP`), and `common.s` selects `.romdmg` unless `CART_CGB` is defined, so `$143 = $00` (CGB-profile compat mode). The [VERIFY] in D-26 is satisfied for all four.
- **Needs same headless patch + zero font** as the parent (`fixtures/mooneye/headless-report.patch`, sha `c3679ab5...`); the `common.s` of these files is the same file. Confirm the patch applies with `--fuzz=0` (reproduce script uses `patch --batch --fuzz=0 -p1`); the failure path of `boot_hwio-C`/`unused_hwio-C` calls `print_hex8`/`print_string`/`print_newline`, which the patch keeps.
- **Expected outcomes under D-26 after fixes C1+C2:** `boot_regs-cgb` PASS; `boot_div-cgbABCDE` PASS (C13); `boot_hwio-C` runs the full FF00-FF75 compare then `ld a,(hl)` with HL=`$FF76` -> `UNSUPPORTED_BUS` (read address FF76; last recorded bus read is FF75 in the diagnostics ring); `unused_hwio-C` passes all rows through `$FF75`, then `ld ($FF00+C),a` writes FF76 (latch) / reads FF76 (stop). Without C1/C2 both report FAIL instead.
- **Runner row fields to add** (`fixture_case`, `main.c:32-49`): `profile` (GBB_PROFILE_CGB_CPU_E), `expect_stop` (`NONE` | `UNSUPPORTED_BUS`), and for unsupported-bus rows the expected last-read address. `unsupported_core_stop()` (:150-155) currently maps every non-budget stop to the generic status `unsupported`; the new rows need an `expected-unsupported` status that exits 0 only for the declared stop and reports `unexpected-pass`/`fail` otherwise.
- **Hash gate:** raw manifest SHA is compared in `manifest_suite()` (`main.c:114-118`); `VerifyMooneyeMbc.cmake` parses `gbb:mbc-rows-begin/end` against the manifest (rename `gbb:cgb-rows-*` in the CGB copy). `ScanForbiddenFixtures.cmake` and install scans must learn the new directory name (Phase 8 did this for `mooneye-mbc`; copy that change).
- **Frame observation:** `--observe` on Mooneye rows calls `gbb_runner_capture_ldbb` (frame digest); on the CGB profile `gbb_copy_frame` returns `GBB_UNSUPPORTED_PROFILE`. Print `mooneye.<alias>.frame\tnot-applicable` (or skip) for CGB rows instead of a `runner-error`. These lines must not enter the DMG baseline (`baseline` compares only `mooneye.daa/tim00/...` keys).
- **Rights:** same MIT + font-replacement path as `fixtures/mooneye-mbc/` (copy `LICENSE.txt`, `FONT-LICENSE.txt`, `SOURCES.md` pattern, `ELIGIBILITY.md`); no boot ROM involved (these tests check state the boot ROM would leave; the core supplies it by policy).

## Test infrastructure hooks (item 4)

| New artifact | Hook / pattern to copy | Registration |
|--------------|-----------------------|--------------|
| `tests/test_cgb_tables.c` | `test_bus.c` style `REQUIRE`; docs diff reads `docs/cgb-profile.md` between markers; mutated doc copy and mutated table copy via `file(WRITE)` in CMake (`doc-contract-selftest` pattern, tests/CMakeLists.txt ~1130) | `add_executable`, `add_test(NAME cgb_tables_*)`; name in `tests/expected-tests.txt`; must be added **before** `gabbaboy_verify_registered_tests()` (last line of tests/CMakeLists.txt) |
| `tests/test_cgb_visibility.c` | `test_bus.c` `load_program`: 32 KiB zero ROM, program at `$100`, `rom[0x134]=0xe7` + `fix_checksum`, set `rom[0x143]` for CGB flag then recompute checksum | one test per column + sweep + two controls |
| `tests/scripts/verify-model-gates.py` | `verify-libbet-admission.py` + `gbb_add_expect_exit_test` (`tests/CMakeLists.txt:749-759`): `${Python3_EXECUTABLE} -I script`, `--self-test`, exit code + regex via `tests/expect_exit.cmake` | `model_gates`, `model_gates_selftest`, per-mutant tests; also a CI step line is optional |
| `docs/model-gates.md`, `docs/cgb-profile.md` | `VerifyDocContract.cmake` for prose that restates API (`native_guide_rtc_contract` pattern) | `native_guide_cgb_contract` + selftests; ADR text tie (D-21) is a second contract call |
| `fixtures/cgb-banking/` | `fixtures/mbc5-banking/` (manifest, LICENSE.txt, `reproduce-mbc5-banking.sh` embedded Python checks, fixture-repro.yml step at `fixture-repro.yml` ~l.115-122) | `cgb_banking_fixture_digest` (`VerifyFixtureManifest.cmake`), `cgb_banking_guest_*`; add reproduce step in `fixture-repro.yml` |
| `fixtures/mooneye-cgb/` | `fixtures/mooneye-mbc/` complete copy pattern (C11 above) | `mooneye_cgb_*` tests; `fixture-repro.yml` leg like `mooneye-mbc-repro`; local `jq` is present |
| Bench A/B | `tests/scripts/measure-release-baseline.sh` (single bash wrapper + embedded Python); currently accepts only `[--self-test]` (`[[ $# -eq 0 ]]` check after the flag) | `--ab <base-measure_core> <head-measure_core>`; CTest self-test uses the same binary twice |
| Fuzz/loader parameterisation | `tests/fuzz_core.c`, `test_loader_matrix.c` (oracle `expected_result()`), `test_loader_fuzz.c`; `run-bounded-fuzz.sh --self-test` greps constants (`FUZZ_INPUT_LIMIT 65536u`, `FUZZ_OPERATION_LIMIT 16u`, `FUZZ_RUN_LIMIT UINT64_C(2048)`) and CTest names (`loader_boundary_fuzz`, `battery_api_fuzz`, `fuzz_core_regressions`) | keep those literals and names |
| Consumers | `tests/consumers/c/main.c` and `cpp/main.cpp` (8 `GBB_PROFILE_DMG_CPU_B` sites each) | add `cgb_api_smoke`; the GSD api-coverage gate (`workflow.api_coverage_gate`) is a workflow gate, not a repo script, and is satisfied by tests/consumers calling every new symbol |
| Windows/ASan/CMake-floor legs | All run `ctest` over the full registered set; the ASan job runs the same inventory (`ci.yml` "linux-sanitizers"); the Windows leg runs `verify-test-inventory.sh --installed` | nothing extra if tests are portable (no POSIX-only calls, `Python3_EXECUTABLE` not literal `python3`) |

**Frozen-ledger facts (D-19):** `tests/baseline/dmg-cpu-b-v1.txt` has 314 `inventory.*` lines and the check fails only on **removed** frozen names (`findings_inventory "removed:..."`, `cmake/VerifyDmgBaseline.cmake:422-431`); added tests are free. Keys `acceptance.*`, `mooneye.*`, `bench.*` compare exactly; new tests must not add `mooneye.*`/`acceptance.*` keys (`extra:` finding at :447-452). `CHANGES.md` default is zero rows. Run `bash tests/scripts/verify-dmg-baseline.sh` after each wave.

**Instance size:** calloc'd opaque struct, `wram` 8,192 -> 32,768 and `vram` 8,192 -> 16,384 bytes (+32 KiB); no caller can stack-allocate it (opaque), but white-box tests that `#include` the core and copy a `gbb_instance` by value, if any, must be checked (none found by grep for `sizeof(gbb_instance)`).

## Benchmark mechanics (item 7)

- Workload fixed: `tests/measure_core.c` (unchanged between `5a55f19` and `d7e2e0a`; `git diff --stat` empty) runs `fixtures/tracer/tracer.gb` for 1,000,000 half-dots and prints `correctness_digest_fnv1a64=...`; the frozen digest is `4c7a57ff3d50d228` (`bench.tracer.correctness_digest_fnv1a64` in the ledger). `guest_digest` hashes `gbb_peek_ram` C000-DFFF and FF80-FFFE, so peek semantics on DMG must stay byte-identical.
- Build old revisions in worktrees outside the repo: `git worktree add <scratch>/base 5a55f19ba2e0ec596005af4dbbc55d476b326333`, same for `d7e2e0a`; `cmake -S <wt> -B <wt>/b -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON` then `cmake --build <wt>/b --target measure_core`. Remove worktrees after (`git worktree remove`). `AGENTS.md` demands revision, build, hardware, workload, model, digest, warm-up, samples and uncertainty in the receipt; omit `$HOME`/user names (record `uname -sm`, compiler string, `sysctl machdep.cpu.brand_string` is a hardware class, not a machine identifier).
- A/B mode in the Python heredoc: strictly interleaved `base, head` pairs (swap order each pair to cancel position bias is cheap and recommended; D-22 says strictly interleaved), per-pair ratio `t_head/t_base`, median/min/sd and `1.96*sd/sqrt(n)` as percent; "noise" label under 3%; review trigger median ratio > 1.05 and lower bound > 1.0. Every sample parses the `mode=... correctness_digest_fnv1a64=...` line like the existing loop (lines ~"fields = dict(...)") and requires equality with `4c7a57ff3d50d228` for both builds.
- CTest self-test: `--ab $<TARGET_FILE:measure_core> $<TARGET_FILE:measure_core>` with `GBB_RELEASE_MEASURE_SAMPLES=3`, `WARMUPS=1`, writes the JSON receipt to the build dir and validates the field list. Negative controls (separate tests through `expect_exit.cmake`): an `--expect-digest` override (or env) with a wrong digest must exit non-zero with a named reason; a built-in `--self-test-drop-field <name>` run must fail the receipt validator. Never assert timing.
- Existing script constraints: sample count 3..30, warmups 1..20, total timeout 30..3600 s, per-command timeout 1..300 s; at ~10 ms per run 30 pairs x 3 builds is far below the limits. The script requires a clean-or-dirty tree state record (`source_tree_state`).

## D-070 ADR verification (item 8 support)

- `GBB_AUDIO_CLOCK_HALF_DOTS UINT64_C(8388608)` (:15) already is 2^23; `RTC_HALF_DOTS_PER_SECOND_SHIFT 23u` (:178). Add named `GBB_DOTS_PER_LINE 456u`, `GBB_LINES_PER_FRAME 154u` and **replace the literals `455u` (:1678) and `154u` (:1686)** in `ppu_advance_dot` with them (`455u` -> `GBB_DOTS_PER_LINE - 1u`), otherwise the static assert is decoupled from the code that uses the numbers. Then `_Static_assert(GBB_DOTS_PER_LINE * GBB_LINES_PER_FRAME * 2u == 140448u, ...)` (456 x 154 = 70,224 dots; Pan Docs frame length).
- Remaining asserts: `GBB_DMA_BYTE_PERIOD_HALF_DOTS == 4u * GBB_HALF_DOTS_PER_T_NORMAL`, T per M = 4, `GBB_HALF_DOTS_PER_T_NORMAL == 2u`, `GBB_HALF_DOTS_PER_T_DOUBLE == 1u`, `RTC shift == 23`, `GBB_MASTER_HALF_DOTS_PER_SECOND == (1u << 23)`. The DMG diff is macro substitution only; the baseline run proves it.
- `VerifyDocContract.cmake` ties ADR prose to symbol names: the contract scans a doc for `gbb_*`/`GBB_*` identifiers declared in the listed files, so the ADR text (in DECISIONS.md or a short section of `docs/cgb-profile.md`) can be checked with `GBB_DECLARATIONS=.../src/core/gabbaboy.c` (it strips C comments, so macro names must be real `#define`s) plus required phrases; negative selftests copy the Phase 9 `doc_contract_*_selftest` set.
- DECISIONS row shape: `| D-070 | Phase 10 D-20/D-21 (2026-10-12): ... **Adopted** | rationale | plans; files |`. Next free id is D-070 (`D-069` is the last row at DECISIONS.md:77).

## Common Pitfalls

1. **calloc zero state.** `gbb_create` uses `calloc` (:2082); a forgotten `m->wram_bank = 1` in `reset_state` maps D000-DFFF onto C000-CFFF on DMG and silently changes output. The flat-reference test must be the first DMG test in the array commit.
2. **`sizeof(m->vram)` doubling** at :1437 (`if (map_address >= sizeof(m->vram)) return 0;`). Replace with `sizeof(m->vram[0])` in the same commit as the reshape; add a grep-based check in the array plan's verify step (no remaining `sizeof(m->vram)`/`sizeof(m->wram)` except the two `memset`s).
3. **Partial mutation on failed load.** Commit `exec_mode` only after both allocations succeed (:2118-2128), alongside the ROM swap (:2130-2137). Probe never allocates.
4. **Probe/load parity drift.** Keep one `validate_header(profile, ...)`; add the parity test over the loader-matrix and fuzz corpora with a deliberately skewed probe as the negative control (D-27).
5. **DEFERRED asymmetry** (C10): reads atomic, writes post-instruction. Test cells must not assume the destination register is unchanged after a deferred *write*; they only assert reason + that the write did not take effect.
6. **D-05 ordering:** `gbb_copy_frame` CGB check goes after argument validation so invalid args are still `GBB_INVALID_ARGUMENT` on both profiles.
7. **Frozen inventory names:** `acceptance_libbet_excluded_cgb-cpu-e` must keep its meaning (excluded, exit 4). Renaming or removing it fails the baseline.
8. **Registered-test equality:** `gabbaboy_verify_registered_tests()` fails configure if CTest names differ from `tests/expected-tests.txt` (it sorts both). Every new test (including selftests and mutants) must be listed in the same commit, and the installed-consumer names stay in the exclusion list logic.
9. **Atomic ROM-size claim in header** for `gbb_info.rom_size_bytes`: `uint32_t` holds 8 MiB; assert `rom_size <= UINT32_MAX` is moot but keep the cast explicit.
10. **Scanner false negatives.** R1 must count multi-line function signatures; verify the scanner's count equals the independently counted 126 (plus new functions) in `--self-test`, and make the "untagged new function" mutant append a function to a copy of the real source rather than a toy file.
11. **Doc-contract identifier strictness.** Any `gbb_`/`GBB_` token in `docs/native-integration.md`, including in prose like "`GBB_INFO_*`", must exist whole-word in a declaring file or the contract fails (`doc-contract-undeclared`).
12. **SVBK raw vs effective** (C7) and **VBK compat read `$FE`** (hwio-C beats Pan Docs prose, per CONTEXT).
13. **Hot path:** put the new CGB I/O decode behind the `FF4C-FF7F` range test so DMG pays one comparison only for addresses that previously fell through. Verify with the advisory bench; do not add `profile` branches inside `read8`'s VRAM/WRAM paths.
14. **Windows:** no POSIX in new tests; `python3` literal must not appear in CTest commands (use `${Python3_EXECUTABLE}`); bench self-test must not require `taskset`/`/proc`.
15. **Git hygiene for fixtures:** new ROM files are binary; `.gitattributes` exists (check it marks `*.gb`/`*.gbc` binary before committing).

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---------|-------------|-------------|-----|
| Doc/code drift for tables | Ad hoc greps | `test_cgb_tables` diff between markers + mutated copies | D-06; pattern in doc-contract selftests |
| Prose-to-API contract | Manual review | `VerifyDocContract.cmake` | D-069 |
| Python verifier harness | New framework | `verify-libbet-admission.py` shape + `expect_exit.cmake` | Already portable to 3 OSes |
| Fixture digest check | New script | `VerifyFixture.cmake` / `VerifyFixtureManifest.cmake` | Existing |
| Mooneye derivation | New build flow | `reproduce-mooneye*.sh` + `headless-report.patch` + `font-source.c` | Rights and determinism already solved |
| Bench stats | New lib | existing `sample_summary()` pattern in `measure-release-baseline.sh` | stdlib `statistics` |
| Core mutants | Custom harness | configure-time `file(READ)/string(REPLACE)` mutant (tests/CMakeLists.txt:209-250) | Exactly-once anchor discipline exists |

## Code Examples

Post-boot cell shape (suggested; names are discretionary):

```c
/* Source: designed for D-06; values from boot_hwio-C / boot_regs-cgb quoted above. */
typedef enum { PROV_HW_TEST, PROV_PANDOCS, PROV_ORACLE_SAMEBOY, PROV_POLICY, PROV_HEADER_DERIVED } post_boot_prov;
typedef struct { uint16_t value; uint8_t prov; uint8_t src_id; const char *reason; } post_boot_cell;
typedef struct { const char *field; post_boot_cell dmg, cgb, compat; } post_boot_row;
```

Deferred-write latch (generalising the serial precedent):

```c
/* Source: gabbaboy.c:1212 / :2766-2770 pattern (serial_unsupported). */
#define BUS_UNSUPPORTED(m, a) do { (m)->bus_unsupported = 1; (m)->bus_unsupported_address = (a); } while (0)
/* in the post-execute block */
if (instance->bus_unsupported) { instance->bus_unsupported = 0; result.reason = GBB_STOP_UNSUPPORTED_BUS; return result; }
```

Test-ROM construction for visibility cells (from `tests/test_bus.c`, quoted): `rom[0x134] = 0xe7; fix_checksum(rom);` with zero ROM (checksum then wraps to 0). For a CGB-flag ROM set `rom[0x143]` first, then recompute (`fix_checksum` loops 0x134..0x14C).

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Pan Docs prose generalisation for compat VBK (`$FF`) | Hardware test `boot_hwio-C` expects `$FE`; SameBoy agrees | CONTEXT already resolved; keep |
| Real DMG IE bits 5-7 read-as-1 in this core | Hardware stores them (`unused_hwio-GS`/`-C`) | Gate (C2) rather than fix DMG |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| cmake / ninja | build, tests | yes | 4.4.3 / present | - |
| clang (Apple 21.0.0) | build | yes | 21.0.0 | CI covers GCC/MSVC |
| python3 | scanner, bench | yes | 3.14.4 | - |
| rgbasm/rgblink/rgbfix **v1.0.1** | `cgb-banking` ROM build | **no (1.0.4 installed)** | 1.0.4 | download pinned `rgbds-macos.zip` (sha in manifest) to a temp dir; CI job downloads the pinned Linux archive |
| wla-gb 10.7 / wlalink 5.22 | Mooneye CGB derivatives | no | - | `reproduce-mooneye-cgb.sh` builds pinned WLA-DX from `vhelin/wla-dx@91c52b1f` (needs network + cmake) |
| jq, curl, patch, shasum | repro scripts | yes (jq/curl/shasum present; `patch` standard) | - | - |
| git worktree | bench A/B | yes | - | - |
| valgrind | not required | no | - | none needed (owner: no new tooling) |
| libFuzzer runtime | optional fuzz | probed by `run-bounded-fuzz.sh --self-test` | - | deterministic regressions |

**Missing with no fallback:** none. **Missing with fallback:** RGBDS 1.0.1, WLA-DX (both scripted).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | CTest over C executables with `REQUIRE` macros and TAP-ish output; CMake `-P` verifiers; stdlib Python verifiers with `--self-test` |
| Config file | `CMakePresets.json` presets `phase1`, `phase1-asan`, `cmake-3.25.3`; `workflow.test_command` = `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` |
| Quick run command | `ctest --preset phase1 -R '^(cgb_\|banking_\|model_gates\|mooneye_cgb_\|bench_ab)'` |
| Full suite command | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` then `bash tests/scripts/verify-dmg-baseline.sh` |

### Phase Requirements -> Test Map

| Req / Decision | Behavior | Test Type | Automated Command | File Exists? | Negative control |
|----------------|----------|-----------|-------------------|--------------|------------------|
| CGB-01 / D-01 | create CGB; unknown profile (0, 3, 255) -> `GBB_UNSUPPORTED_PROFILE`; NULL out | unit | `ctest -R '^cgb_profile_'` | no Wave 0 | create with profile 3 must fail |
| CGB-01 / D-02..D-04 | probe/get_info matrix `$143 in {00,80,C0,81,84,88,FF}` x both profiles; `struct_size` 0/27/28/larger; error parity; failed load keeps info; mode constant over reset; no-ROM mode NONE | unit | `ctest -R '^cgb_(probe\|info)_'` | no Wave 0 | skewed probe (parity), shrunk struct, flipped expected enum |
| CGB-01 / D-03 | PGB `$143` (bit 7 + bit 2 or 3) rejected on CGB, loads on DMG, probe on DMG reports PGB | unit | `ctest -R '^cgb_probe_pgb'` | no Wave 0 | same ROM on DMG must not reject |
| CGB-01 / D-05 | `gbb_copy_frame` on CGB -> `GBB_UNSUPPORTED_PROFILE`; invalid args still `INVALID_ARGUMENT` | unit | `ctest -R '^cgb_copy_frame'` | no Wave 0 | DMG profile same call succeeds |
| CGB-01 / D-06 | code table == `docs/cgb-profile.md` markers; POLICY has reason; no HW_TEST outside compat | unit + CMake | `ctest -R '^cgb_tables'` | no Wave 0 | mutated doc, mutated table, reasonless POLICY, HW_TEST in CGB column |
| CGB-01 / D-06,D-19 | DMG column equals pre-refactor literals | unit | `ctest -R '^cgb_postboot_dmg_pin'` + `verify-dmg-baseline.sh` | no Wave 0 | flip one literal in the test copy |
| CGB-01 / D-07 | compat/CGB CPU rows, title-sum B/HL, DIV phase, hwio compare | unit (public API, synthetic ROMs) | `ctest -R '^cgb_postboot_'` | no Wave 0 | header with licensee `$01` changes B; counter 0x2677 must fail the DIV guest |
| CGB-02 / D-08 | scanner R1-R5 on the real source and docs | script | `ctest -R '^model_gates'` | no Wave 0 | 5 mutants: deleted tag, code/doc mismatch, untagged new function, unresolved UNKNOWN under `--release`, DMG_ONLY without guard |
| CGB-02 / D-09..D-11 | per-cell matrix, sweep FF00-FF7F, DEFERRED stops | unit | `ctest -R '^cgb_visibility_'` | no Wave 0 | flip an expected byte; run cell in other column; delete a row |
| CGB-02 / D-12 | KEY0 writes `$00,$04,$80,$C0` read `$FF`; VBK probe in compat vs CGB; mode unchanged | unit | `ctest -R '^cgb_key0_lock'` | no Wave 0 | allow KEY0 write in a core mutant (optional) |
| CGB-02 / D-23 | STOP with KEY1 armed on CGB -> `UNSUPPORTED_BUS`, never `STOPPED`; unarmed STOP uses shared path | unit | `ctest -R '^cgb_stop_'` | no Wave 0 | DMG profile same program stops with `STOPPED` |
| CGB-03 / D-13..D-15 | flat reference on DMG; invariants; CGB divergence | white-box | `ctest -R '^banking_dmg_'` | no Wave 0 | CGB profile with banking writes must diverge |
| CGB-03 / D-15,D-16 | VBK/SVBK banks, echo follows bank, E000-EFFF mirrors bank 0, DMA sources by model | unit | `ctest -R '^banking_'` | no Wave 0 | core mutants: echo ignores bank, DMA wrong bank |
| CGB-03 / D-18 | original fixture (CGB, compat, DMG, CGB-only-on-DMG) | fixture | `ctest -R '^cgb_banking_'` | no Wave 0 | patched expected value -> `$EE`; DMG run of CGB build fails exactly CGB cells; SVBK-skip variant detected |
| D-19 | ledger recompute byte-identical; existing suites unchanged | baseline | `bash tests/scripts/verify-dmg-baseline.sh` | yes | existing comparator selftests |
| D-20/D-21 | ADR static asserts and doc tie | compile + CMake | `ctest -R '^adr_half_dot'` | no Wave 0 | doc missing a symbol; static assert broken in a copy (compile-fail test) |
| D-22 | A/B receipt + digest | script | `ctest -R '^bench_ab'` | no Wave 0 | wrong digest, missing field |
| D-25 | runner `--profile`, no DMG label on CGB, DMG lines unchanged | runner | `ctest -R '^runner_(profile\|model)'` + baseline | no Wave 0 | CGB case on DMG run -> `excluded`; grep CGB output for `dmg-cpu-b` must be empty |
| D-26 | Mooneye CGB admissions | runner/verifier | `ctest -R '^mooneye_cgb_'` | no Wave 0 | tampered ROM digest; pc-table tamper; expected-unsupported row that actually passes -> fail |
| D-27 | fuzz/loader on both profiles; CGB random-IO fuzz; consumers | fuzz/unit | `ctest -R '^(loader_\|battery_api_fuzz\|fuzz_core_regressions\|installed_consumer)'` + ASan preset | partially | skewed probe |
| D-28 | docs contract | CMake | `ctest -R '^native_guide_cgb_contract'` | no Wave 0 | missing phrase / undeclared identifier selftests |

### Sampling Rate
- **Per task commit:** the narrow `ctest -R` for the touched area plus `verify-dmg-baseline.sh` after any task that edits `gabbaboy.c`.
- **Per wave merge:** full suite on `phase1`, then `phase1-asan` for core-touching waves; baseline.
- **Phase gate:** full suite green on all legs at the exact PR head (macOS, Linux, Windows, ASan, CMake-floor), baseline `status=pass`, fixture-repro `result=byte-identical` read at the evidence head (LESSONS GB-CART-010).

### Wave 0 Gaps
- [ ] `tests/test_cgb_tables.c`, `tests/test_cgb_visibility.c`, `tests/test_cgb_profile.c` (probe/info/create), `tests/test_banking.c` (public) and `tests/test_banking_internal.c` (white-box, includes core)
- [ ] `tests/scripts/verify-model-gates.py` with `--self-test` and mutant fixtures under the build tree
- [ ] `docs/cgb-profile.md` and `docs/model-gates.md` skeletons with table markers so code-vs-doc tests have a counterpart
- [ ] `fixtures/cgb-banking/` (asm, two ROMs, manifest, LICENSE, reproduce script) and `fixtures/mooneye-cgb/`
- [ ] Bench A/B mode and its CTest hooks
- [ ] Add all new names to `tests/expected-tests.txt` (and sanitizer lists if any, none found beyond the shared inventory)

## Security Domain

`security_enforcement` is enabled in `.planning/config.json` (ASVS level 1, block on high).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2/V3/V4 Auth, session, access | no | Library has no identities or sessions |
| V5 Input Validation | yes | `gbb_info` argument validation (NULL, `struct_size < GBB_INFO_SIZE_V1`, NULL ROM with non-zero size), header validation order, bank index masking (`vram_bank` 0..1, `wram_bank` 1..7 by `& 7` with 0 -> 1) before array indexing, fuzz under ASan/UBSan |
| V6 Cryptography | no | SHA-256 only for fixture digests (existing `sha256.c`/`cmake file(SHA256)`) |
| V12 Files/resources | yes (CI) | Fixture reproduction runs untrusted downloaded archives only in temp dirs outside the repo (existing scripts refuse in-tree output via `outside_repo`) |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Out-of-bounds bank index (guest writes SVBK/VBK) | Tampering | mask then clamp at write time; arrays sized exactly; fuzz random FF4F/FF70 writes on CGB profile |
| Caller-supplied `struct_size` larger/smaller than ABI | Tampering/Info disclosure | write field by field only within `struct_size`; never read beyond; preserve caller's extra bytes; `struct_size` OUT = bytes written |
| Probe with huge `rom_size` | DoS | probe reuses the existing ceiling check first (`size > ceiling` before other work, :2014-2016); allocates nothing |
| Partial mutation on failed load | Tampering | commit mode with ROM swap only after allocations |
| Receipt/doc leaks (paths, user names) | Information disclosure | strip `$HOME`, usernames from bench receipt; scan new fixtures for forbidden content with `ScanForbiddenFixtures.cmake` |
| Slopsquatted/new dependency | Tampering | none added; pinned digests only |

## Recommended plan/wave split (sized for executor context)

`gabbaboy.c` is ~40K tokens; give each plan an explicit line-range reading list. Keep arrays and visibility changes in separate commits, and the `reset_state` table refactor in its own commit (D-06).

| Wave | Plan | Scope (files) | Notes |
|------|------|---------------|-------|
| 1 | 10-01 | `tests/scripts/verify-model-gates.py` + selftest mutants + CTest registration; `docs/model-gates.md` skeleton | Test-first (scanner red against untagged core). Independent of core edits |
| 1 | 10-02 | Tag all 126 functions + ~40 branch gates in `gabbaboy.c` (comments only), fill `docs/model-gates.md`, scanner green, `--release` unresolved-UNKNOWN control | Mechanical; baseline must be identical (comment-only diff); do **not** touch anchor lines |
| 1 | 10-03 | Runner/acceptance model threading + `--profile` + removal of the :1196 rejection (create still returns UNSUPPORTED for CGB until 10-06) | Parallel with 10-02 (disjoint files: `src/runner/*`, `tests/acceptance`); output byte-identical for DMG |
| 2 | 10-04 | DMG literal pin test + `post_boot[]` refactor (own commit, bisectable) with DMG column only | Pin test lands before the refactor |
| 2 | 10-05 | Header API (enums, `gbb_info`, `gbb_probe_rom`, `gbb_get_info`, error code), `validate_header(profile)`, instance `profile`/`exec_mode`, probe/info/parity tests, docs/native-integration.md API section + doc contract | `gbb_create` still rejects CGB |
| 2 | 10-06 | CGB columns of `post_boot[]` (incl. C1 cells), `docs/cgb-profile.md` mirror + `test_cgb_tables`, `gbb_copy_frame` D-05, **flip `gbb_create` for CGB** | See Open Question 1 on flip timing; header comment updated in the same commit |
| 3 | 10-07 | Array reshape + helpers + `gbb_peek_ram`/PPU/`dma_source_read`/`reset_state` sites + `test_rtc3test.c:109` fix + white-box flat-reference test + baseline | DMG-identical refactor; no CGB behaviour yet |
| 3 | 10-08 | CGB bank decode (VBK/SVBK), echo, `cart_read` extraction + CGB OAM DMA sources, `banking_*` tests + core mutants | |
| 3 | 10-09 | `fixtures/cgb-banking` + digest/guest tests + `fixture-repro.yml` step | Needs pinned RGBDS (C9); parallel with 10-10 |
| 3 | 10-10 | Bench A/B + self-test + evidence run + `10-BENCH.md` | Needs 10-07 merged; evidence run after the bank code is final |
| 4 | 10-11 | `io_visibility[]`, `read_supported` widening, IE gate, `bus_unsupported` latch, KEY0/KEY1/STOP, `test_cgb_visibility`, `test_cgb_tables` extension | Highest bug risk for DMG identity: review `read_supported` diff against baseline |
| 4 | 10-12 | `fixtures/mooneye-cgb` suite (sources, scripts, manifest, verifier, runner rows/fields, CI leg, expected-tests) | Largest tooling item; can start after 10-06 for boot_regs/div and finish after 10-11 for hwio/unused |
| 5 | 10-13 | Fuzz/loader/consumers on both profiles, runner negative controls, docs (`native-integration.md`, `support/unreleased.md`), D-070 + static asserts + doc contract, LESSONS entry, final baseline/ledger check | Close-out; no new core features |

Parallelism: 10-02 || 10-03; 10-09 || 10-10; 10-12 first half || 10-11. All other plans serialise on `gabbaboy.c`/`tests/CMakeLists.txt`/`tests/expected-tests.txt` edits (merge-conflict hot spots: append new tests in a clearly delimited block per plan).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The real Mooneye ROM adds no instructions before the first `nops 27` (so `0x2678` holds for the real ROM, not just my equivalent guest) | Post-boot / C13 | Re-run the sweep on the derived ROM; adjust the cell |
| A2 | Setting `apu_pulse[0].enabled=1` with `volume=0` and a valid timer yields NR52 `$F1` without audible output or timer overflow anomalies | Post-boot delta | Audio digest on CGB profile affected only; DMG untouched; test |
| A3 | `headless-report.patch` applies `--fuzz=0` to the four `misc` tests (they share `common/`) | Mooneye | Need a sibling patch (the mbc script has a hook for one) |
| A4 | Flipping `gbb_create` at the end of Wave 2 satisfies D-01's "the plan that completes the profile" | Plan split | Owner may prefer a later flip; costs white-box-only CGB tests earlier |
| A5 | `.gitattributes` handles new `.gbc`/`.gb` binaries | Pitfall 15 | Line-ending corruption of ROM bytes; check before commit |
| A6 | CGB `FEA0-FEFF` should remain fail-closed on both profiles this phase | Gate G32 | Not covered by D-10; owner could want `$FF`/ignored |
| A7 | SameBoy master at `c71f110e` equals the revision CONTEXT read for these cells | C7, visibility | Low; labels are `ORACLE_SAMEBOY` not hardware |

## Open Questions

1. **When to flip `gbb_create` for CGB?** D-01 says "until the plan that completes the profile". Recommendation: end of Wave 2 (10-06), because every later wave's public-API test needs a CGB instance and the phase PR is a single merge. Alternative: white-box-only until Wave 4 (costly).
2. **IE bits 5-7 on CGB (C2):** gate them on the CGB profile (recommended), or drop `unused_hwio-C` from Phase 10 admission? Recommending the gate keeps both ROMs; it adds one more documented DMG-vs-hardware divergence to the veto list.
3. **CGB ch1 post-boot state (C1):** accept the silent-enabled-channel policy (A2) or keep NR52 `$F0` and downgrade `boot_hwio-C` to a documented expected failure (it would then fail at FF26 instead of stopping at FF76)? Recommending the policy cell.
4. **Gate-id scheme:** `GATE-00` shared id for model-neutral function tags (recommended) vs unique ids for all ~190 tags.
5. **Atomicity of DEFERRED writes:** latch (recommended) vs extending the preflight to all store forms.

## Sources

### Primary (HIGH)
- Repository files read this session: `include/gabbaboy/gabbaboy.h` (all), `src/core/gabbaboy.c` (lines 1-420, 420-565, 560-1450, 1450-1530, 1700-1790, 1827-1915, 1930-2425, 2500-2600, 2605-2843), `src/runner/main.c` (all), `src/runner/acceptance.c` (1176-1282 plus grep of all sites), `tests/CMakeLists.txt` (1-260, 460-500, 735-800, 1060-1194), `tests/test_bus.c` (1-140), `tests/baseline/*`, `cmake/VerifyDmgBaseline.cmake` (395-470), `cmake/VerifyDocContract.cmake` (1-80), `cmake/ExpectedTests.cmake`, `tests/scripts/measure-release-baseline.sh`, `tests/measure_core.c`, fixtures `mbc5-banking`, `mooneye`, `mooneye-mbc` manifests.
- Mooneye Test Suite @ `31510e12eea6286d36eea060a6adde755e1067aa` raw files: `misc/boot_regs-cgb.s`, `misc/boot_div-cgbABCDE.s`, `misc/boot_hwio-C.s`, `misc/bits/unused_hwio-C.s`, `acceptance/bits/unused_hwio-GS.s`, `common/common.s`, `Makefile`.
- [Pan Docs Power Up Sequence](https://gbdev.io/pandocs/Power_Up_Sequence.html) (CPU register and hardware register tables, notes 1-2).
- SameBoy `Core/memory.c` @ `c71f110eb1b1e87914fddd9c0e68712dddce787d` (2026-10-11): SVBK/VBK/KEY0/KEY1/BGPI/OPRI read-write paths and `GB_dma_run`.

### Secondary (MEDIUM)
- [Microsoft: C11 and C17 support in MSVC](https://devblogs.microsoft.com/cppblog/c11-and-c17-standard-support-arriving-in-msvc/) (C11/C17 modes since VS 2019 16.8; repo already uses `_Static_assert` under MSVC).

### Tertiary (LOW)
- Scratch experiments (not committed): DIV sweep in the session scratchpad using an original RGBDS guest; results quoted in C13.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, no new packages, all tools already pinned and read.
- Architecture / code sites: HIGH, every line number was read from the current file.
- Mooneye expectations: HIGH for the quoted ROM sources; MEDIUM for "stops at FF76" until the derived ROMs run (A1-A3).
- Pitfalls: HIGH for repo-mechanical ones, MEDIUM for hardware-value ones.

**Research date:** 2026-10-12
**Valid until:** 2026-11-11 for repo facts (stable until the next `gabbaboy.c` edit); SameBoy/Pan Docs facts are 30-day.
