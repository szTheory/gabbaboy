# Phase 8: Cartridge Seam, MBC5 and MBC2 - Context

**Gathered:** 2026-10-11
**Status:** Ready for planning
**Method:** Four advisor researchers ran in parallel, each from several angles and each with an adversarial pass. The areas were: seam and no-change proof, Mooneye admission and 8 MiB policy, MBC2 semantics and battery image, and MBC5, rumble and fixtures. Their recommendations were reconciled into one coherent set. Per the owner's standing instruction (discuss fan-out, auto-follow), the recommendations were adopted without asking about each area. No researcher raised an owner-only question. Where researchers disagreed, the resolution is recorded under each decision and in `08-DISCUSSION-LOG.md`.

<domain>
## Phase Boundary

Move all cartridge behaviour behind one type-table-driven mapper seam (kind, RAM, battery, RTC, rumble) with **no observable DMG change**. Then add MBC5 (`$19-$1E`) and MBC2 (`$05/$06`) so a caller can run them through the existing public API. Requirements: CART-01, CART-02, CART-03.

Delivered evidence:
- The MBC1 suite, the MBC1 battery continuation fixture and the frozen DMG baseline stay byte-identical.
- The pinned Mooneye `mbc5` derivatives pass 8/8 and the `mbc2` derivatives pass 7/7.
- Original MBC5 fixtures cover bank `$1FF`, bank 0 in the upper window, and rumble masking.
- The 8 MiB `rom_64Mb` derivative is proven absent from install and package artifacts.

**Not in this phase:**
- MBC3, the RTC and MBC30 rejection (Phase 9: CART-04, RTC-01).
- The full type x ROM-code x RAM-code x length rejection matrix and fuzz targets on the raised bound (Phase 9: CART-05).
- Player battery persistence for MBC2, MBC3 and MBC5, the save-envelope widening, and the `fixtures/mbc2-continuation` fresh-process fixture (Phase 9: CART-06).
- `gbb_probe_rom` and `gbb_get_cartridge_info` (CGB phases or SHIP-10).
- Host haptics (future).
- The CGB profile and any `$143` handling.
- The Mooneye MBC1 backfill (deferred).

</domain>

<decisions>
## Implementation Decisions

### A. Mapper seam shape (CART-01)
- **D-01:** The seam is a **delimited "Cartridge mapper" section inside `src/core/gabbaboy.c`**. Phase 8 adds no new `.c` or `.h`.
  - Resolution: this overrides `.planning/research/v0.2/ARCHITECTURE.md` §2, which proposed `src/core/cartridge.c`.
  - Reason: `gabbaboy.c` is compiled or text-copied as one translation unit in at least five places:
    - `CMakeLists.txt:23`, plus the dirty-source list at `:69`;
    - the alloc probe at `tests/CMakeLists.txt:71`;
    - `fuzz_core` at `tests/CMakeLists.txt:168`;
    - `tests/scripts/probe-mooneye-candidate.sh:137`;
    - the JOYP core mutant at `tests/acceptance/CMakeLists.txt:287-300`, which text-substitutes `gabbaboy.c` into a single generated `.c`.
  - A second translation unit would silently break or weaken those.
  - A file split is a later, standalone move task with that six-site checklist.
  - **Reversibility:** reversible.
- **D-02:** Mapper state is one `cart_state` sub-struct of fixed-width integers with no pointers.
  - A `cart_kind` enum (`ROM_ONLY, MBC1, MBC2, MBC5`; MBC3 is added in Phase 9) and one `static const` type-table row per accepted cartridge type drive these columns: kind, `ram_window_mapped`, `has_battery`, `has_timer`, `has_rumble`, the maximum ROM-size code, the RAM-size rule, and the maximum ROM byte count.
  - The table is looked up once at load and the kind is stored. Dispatch is `switch (kind)`.
  - No function-pointer vtables: they put an indirect call on the hot read path and are hostile to v0.3 field-by-field serialization.
  - `has_timer` is present but unused until Phase 9.
- **D-03:** In Phase 8 the table drives three things:
  - battery eligibility, replacing `cartridge_type == 0x03u` in `has_battery_ram` (~`gabbaboy.c:1739`) and in the `write8` generation bump (~`:769`);
  - the `A000-BFFF` supported window in `read_supported` (~`:966-969`);
  - `validate_header`.
  - After the seam plan, the literal `cartridge_type == 0x03u` appears nowhere in `src/` (grep-checkable).
- **D-04:** The MBC1 rules are encoded as table data **exactly** as they behave today:
  - Type `$01` accepts RAM code `$00` only.
  - Types `$02/$03` accept code `$02`, or code `$03` only when the ROM code is `$04` or lower.
  - Only `$03` is battery-backed.
  - ROM-only accepts only ROM code `$00`.
  - MBC1 accepts ROM codes `$00-$06`.
  - The window is mapped for every MBC1 type, including `$01` with no RAM (reads `$FF`), and for ROM-only only when RAM exists.
  - The MBC1M recognizer (`recognized_mbc1m_candidate`) and `GBB_UNSUPPORTED_CARTRIDGE_VARIANT` are unchanged.
- **D-05:** `validate_header` keeps its current error-precedence order:
  1. `INVALID_ARGUMENT`, `ROM_TRUNCATED` (<`$150`), `ROM_TOO_LARGE`
  2. `UNSUPPORTED_CARTRIDGE`
  3. `UNSUPPORTED_ROM_SIZE`
  4. `UNSUPPORTED_RAM_SIZE`
  5. `TRUNCATED` / `SIZE_MISMATCH`
  6. `INVALID_ROM` (checksum)
  7. `UNSUPPORTED_CARTRIDGE_VARIANT`

  Allocation order stays validate, then allocate, then commit (no partial mutation). Do not move allocation into table code.
- **D-06:** `read8` and `write8` keep their existing branch order. Only the cartridge branches (~`:684-694`, ~`:744-773`) are replaced in place.
  - There is no region-decode refactor of the long `if` chain in Phase 8. It is hot and DMA-gated, and no baseline workload exercises MBC1 reads.
  - That refactor waits until the CGB banking registers force a region split, and then comes with A/B evidence.
- **D-07:** Reset resets mapper registers only (ROM bank, RAM bank, enable, rumble line). It never touches cartridge RAM or `battery_generation`, matching the `gbb_reset` contract.

### B. Proof of no observable DMG change (CART-01)
- **D-08:** The seam lands **first, as its own plan**. MBC5 and MBC2 plans then run in parallel. Their shared edits are type-table rows and enum values, and whichever merges second rebases.
  - MBC5 owns the 8 MiB bound.
  - MBC2 owns the 512-byte built-in-RAM row.
- **D-09:** The seam plan changes **only** `src/core/gabbaboy.c` (plus `.planning/`). `git diff --name-only main...HEAD -- tests fixtures cmake .github CMakeLists.txt` is empty for that plan. These must pass with identical output and no expectation edits:
  - the existing MBC1 tests (`test_cartridge.c`, `test_battery.c`, `test_loader.c`, `test_loader_fuzz.c`);
  - `fixtures/mbc1-continuation`;
  - `dmg_baseline`.
- **D-10:** A one-off old-versus-new differential is recorded in the seam plan's verification section. It is not a permanent test.
  - Build `gabbaboy.c` at `5673bed` and at the seam commit.
  - Compare loader return codes over this grid, with a valid header checksum:
    - type `0..255`;
    - ROM code `0..8`, plus `$52-$54`;
    - RAM code `0..6`;
    - length classes: declared, declared-1, declared+1, and above 2 MiB.
  - Compare MBC1 bank and RAM reads under fixed pseudo-random write sequences to `0000-7FFF` and `A000-BFFF`, including a 512 KiB-or-larger MBC1M-candidate image.
  - The result must be zero differences. Record the input count and a result digest.
- **D-11:** Performance: run `measure_core` before and after the seam as **advisory** evidence, and state that its 32 KiB tracer covers only the ROM-only kind, not MBC1. The frozen `bench.tracer.correctness_digest_fnv1a64` (`4c7a57ff3d50d228`) is a hard byte-identical gate. If `measure_core` regresses beyond its noise, investigate; never edit the ledger.
- **D-12:** Baseline interaction:
  - Phase 8 makes **no `baseline:` commit and no `tests/baseline/CHANGES.md` row**, and `tests/baseline/` is untouched.
  - New CTests are added to `tests/expected-tests.txt` as `+` lines only: `git diff -U0 main...HEAD -- tests/expected-tests.txt` shows no `-` lines.
  - The ledger flags only removed inventory keys (`cmake/VerifyDmgBaseline.cmake:422-431`), and CI's `verify-test-inventory.sh` needs the exact set.
  - No existing CTest name is renamed, split or removed.
  - The JOYP mutant anchor `if ((m->joypad_select & 0x20u) == 0)` still occurs exactly once.
- **D-13:** The MBC5 plan carries the cross-mapper negative control (V2-08). The same write sequence must select different banks on MBC1, MBC5 and MBC2 images. For example, writing `$00` to `$2000` gives bank 1 on MBC1 and bank 0 on MBC5, and MBC2 treats it as RAM-enable, not a bank write.

### C. ROM size bound
- **D-14:** The absolute ceiling becomes **8 MiB**: `GBB_MAX_ROM_SIZE`, changed in the MBC5 plan, not the seam plan.
  - **Every pre-Phase-8 return code for non-MBC5 type bytes is preserved.** A length above 2 MiB returns `GBB_ROM_TOO_LARGE`, exactly as today, unless the type byte is an MBC5 type (`$19-$1E`). Each type row's maximum ROM byte count enforces this.
  - Order of checks:
    1. Length above 8 MiB returns `ROM_TOO_LARGE` before any header-dependent work.
    2. The per-type maximum byte count is checked at the same precedence slot.
  - Per-type maximum ROM-size codes: ROM-only `$00`, MBC1 `$06`, MBC2 `$03`, MBC5 `$08`. Codes above a type's maximum, including `$09+` and `$52-$54`, return `GBB_UNSUPPORTED_ROM_SIZE`.
  - `tests/test_loader_fuzz.c` and `loader_oversized` stay unchanged, because their 2 MiB+1 cases use non-MBC5 headers.
  - New tests: MBC5 `$08` at exactly 8 MiB loads; 8 MiB+1 and `SIZE_MAX` return `ROM_TOO_LARGE`; MBC1 at 2 MiB+1 still returns `ROM_TOO_LARGE` and leaves the previous guest state intact.
  - Resolution: the Mooneye researcher proposed letting oversized MBC1 images shift error class. The seam researcher's stricter "no observable change" was adopted.
  - Update `include/gabbaboy/gabbaboy.h:23` (comment), `docs/cartridge-and-saves.md` and `docs/native-integration.md:59`.
  - Allocation bound: ROM at most 8 MiB plus RAM at most 128 KiB, after validation.
  - **Reversibility:** costly — documented API bound for callers and the player.
- **D-15:** The player's `PLAYER_SESSION_MAX_ROM_SIZE` stays 2 MiB in Phase 8. It rejects larger files with its existing explicit message. Raising it belongs with player mapper support in Phase 9.

### D. MBC5 behaviour (CART-02)
- **D-16:** MBC5 behaviour:
  - **Types:** `$19` (no RAM), `$1A` (RAM), `$1B` (RAM + battery), `$1C` (rumble), `$1D` (rumble + RAM), `$1E` (rumble + RAM + battery).
  - **ROM codes:** `$00-$08`.
  - **RAM codes:** `$00` none, `$02` 8 KiB, `$03` 32 KiB, `$05` 64 KiB, `$04` 128 KiB. `$01` and other codes return `GBB_UNSUPPORTED_RAM_SIZE`. No-RAM types (`$19`, `$1C`) require RAM code `$00`. RAM types require one of the codes above.
  - **ROM banking:**
    - `$2000-$2FFF` sets the low 8 bits.
    - `$3000-$3FFF` sets bit 8 from value bit 0 only.
    - The two registers are independent, so write order is irrelevant and a high-bit write never clears the low byte.
    - Bank = `((hi & 1) << 8) | lo`, masked by `rom_banks - 1`.
    - **Bank 0 is selectable at `$4000-$7FFF`** (no 0->1 remap).
    - `$0000-$3FFF` always reads bank 0.
  - **RAM enable:** `(value & 0x0F) == 0x0A` at `$0000-$1FFF`, identical to MBC1 (`gabbaboy.c:747`). Tests pin `$0A`, `$1A`, `$FA` as enable and `$00`, `$0B`, `$A0` as disable.
  - **RAM bank:** `$4000-$5FFF` sets 4 bits on `$19-$1B` and 3 bits on rumble types `$1C-$1E`, masked by the loaded RAM bank count.
  - **Disabled or absent RAM:** reads `$FF`, writes are ignored.
  - **`$6000-$7FFF`:** writes are ignored.
  - **Load and reset:** ROM bank 1, RAM bank 0, RAM disabled, rumble line off.
  - **Battery types:** `$1B` and `$1E`, through the existing four battery calls. `battery_generation` bumps only on changed RAM bytes, as for MBC1.
  - `$143` is ignored. A `$143=$C0` MBC5 image loads on DMG-CPU-B, and one regression test proves it. The profile is unchanged.
- **D-17:** **Rumble API**:
  - Append `GBB_NO_RUMBLE` after `GBB_FRAME_NOT_READY` (the enum is append-only ABI).
  - Add `gbb_error gbb_rumble_state(const gbb_instance *instance, uint8_t *out_on, uint64_t *out_changes)`:
    - `GBB_INVALID_ARGUMENT` for any NULL.
    - `GBB_NO_RUMBLE` with no ROM or a non-rumble type; outputs are unchanged on any error.
    - `out_on` is bit 3 of the last `$4000-$5FFF` write on `$1C-$1E`, independent of RAM enable.
    - `out_changes` counts line transitions only and saturates at `UINT64_MAX`.
    - `gbb_reset` turns the line off, counting one change if it was on, and otherwise preserves the counter.
    - A successful `gbb_load_rom` zeros both.
  - Hosts sample once per frame; the counter conveys duty-cycle intensity without timestamps.
  - Player and runner do not surface rumble in Phase 8, because haptics are deferred. Docs mention the query.
  - **Reversibility:** costly — published preview ABI: an appended error value and an exported symbol that consumers may link against; removal needs a 0.x breaking-change note.

### E. MBC2 behaviour (CART-03), backed by Mooneye at pin `31510e1`
- **D-18:** Register decode:
  - Writes to `$0000-$3FFF` decode by **address bit 8**:
    - Bit 8 clear: RAM enable iff `(v & 0x0F) == 0x0A`. Evidence: `bits_ramg` round 2 writes all 256 values.
    - Bit 8 set: ROM bank = `v & 0x0F`, translated 0->1 **then** masked by bank count. Evidence: `rom_*` expected bank sequence `1 1 2 3 0 1 2 3`.
  - Writes to `$4000-$7FFF` have no effect (`bits_unused`).
  - Reset clears RAM enable and sets bank 1, preserving RAM and generation.
- **D-19:** RAM storage:
  - 512 bytes, stored **canonical as `0xF0 | nibble`** and indexed by `addr & 0x1FF` across `A000-BFFF`.
  - Enabled reads return the stored byte. The upper nibble reads as 1s, per hardware evidence `ram.s` round 6 on a genuine MBC2A.
  - Disabled reads return `$FF`, and writes while disabled are ignored.
  - Tests:
    - all 8192 window addresses against an echo model;
    - write `$A5` reads `$F5`;
    - a table test over every address bit combination of the bit-8 decode, including that `$00` to `$2000` does not change the bank and `$00` to `$2100` selects bank 1.
- **D-20:** Header admission:
  - Types `$05/$06` require RAM code `$00`; any other code returns `GBB_UNSUPPORTED_RAM_SIZE`.
  - ROM codes `$00-$03` (32-256 KiB) are accepted. `$04+` returns `GBB_UNSUPPORTED_ROM_SIZE`.
  - 512 bytes of canonical RAM, initialised to `$FF`, are allocated from the type row, never from `$149`.
  - Type `$05` has live volatile RAM, and all four battery calls return `GBB_NO_BATTERY`.
  - Resolution: FEATURES.md:288 suggested `UNSUPPORTED_CARTRIDGE_VARIANT` for MBC2 oversize. The size-error mapping is used instead, consistent with MBC1. `VARIANT` stays reserved for recognised-but-unsupported wiring.
- **D-21:** Battery image for `$06`:
  - Export: exactly 512 bytes, every upper nibble `$F` (a plain copy of canonical RAM).
  - Import: accepts exactly 512 bytes, otherwise `GBB_BATTERY_SIZE_MISMATCH`, then normalises each byte to `0xF0 | (b & 0x0F)`. Non-canonical files from other emulators are accepted and canonicalised, which is documented.
  - The normalised image is compared with live RAM **before any mutation**. RAM and generation are untouched on any error. Generation bumps once only if the normalised image differs.
  - A guest write bumps generation only when the canonical byte changes. Writing `$A5` onto a `$F5` cell is no bump.
  - Packed 256-byte saves are unsupported and named as such in docs.
  - Update the "raw RAM bytes" wording at `gabbaboy.h:140-148` and in `docs/cartridge-and-saves.md`.
  - **Reversibility:** costly — exported save bytes may be persisted by hosts. Import normalisation means a later fill change would not break loading, but would change exported bytes.

### F. Player behaviour in Phase 8 (protects user data; does not take CART-06)
- **D-22:** Battery cartridge types other than `$03` (`$06`, `$1B`, `$1E`) **run without persistence and say so**:
  - The player keeps `battery_backed=false`, so no save, lock, recovery or temp file is read, renamed, created or written for them.
  - It adds a `battery_unsupported` identity flag, with a visible status ("Battery saving is not supported for this cartridge type yet; progress is not kept") and a stderr warning.
  - `src/player/limitations.h` and `docs/cartridge-and-saves.md` stop claiming "MBC1 only" but state the gap.
  - The v1 envelope still accepts only type `$03` with 8192 or 32768 bytes.
  - A player test asserts that no file appears under the save directory for such a cartridge.
  - Reason: once the core accepts these types, `player_session_identify_rom` (`src/player/session.c:161-170`) would otherwise drop progress silently.

### G. Mooneye mbc2 and mbc5 derivative admission
- **D-23:** Admit the 15 derivatives in a **new sibling `fixtures/mooneye-mbc/`** with its own manifest: categories `mbc2` (7) and `mbc5` (8), plus `required_roms`.
  - `fixtures/mooneye/`, its pinned manifest digest, `pre-admission-baseline.json`, `reproduce-mooneye.sh`'s three-case identity, `VerifyMooneye.cmake`'s `cpu`/`timer` categories, and every `mooneye.*` ledger line stay unchanged.
  - Mooneye-mbc results are **not** added to the baseline `--observe` set in Phase 8.
- **D-24:** Recipe:
  - Mooneye `31510e12eea6286d36eea060a6adde755e1067aa` (tree `2b8c52424a49a2a7466cf631fd8992c53d0de2fa`).
  - WLA-DX `91c52b1f4ef3cc8ba3c0638f7536539579af6a9f`, `wla-gb -I common`, `wlalink -nS -d -S`.
  - The parent's `headless-report.patch` (applied with `patch --batch --fuzz=0 -p1`) and the parent's zero-font replacement from `font-source.c`.
  - The sibling manifest **references** the parent patch, font source and builder pin by relative path plus SHA-256, verified at configure or test time, rather than copying them.
  - The MIT `LICENSE.txt` is copied, because the notice must travel with redistributed ROMs.
  - New `SOURCES.md` and `ELIGIBILITY.md` cover the mbc2/mbc5 source closure (`common/harness/mbc{2,5}_rom.s`, `common.s`, `common/lib`).
  - If a patch variant proves necessary (see D-27), it is sibling-owned, digest-pinned and changes no assertion code.
- **D-25:** Indicative digests are Darwin/arm64 scratch rebuilds from the pinned recipe. **Recapture at admission and match on hosted Linux before claiming them.**
  - `mbc2_bits_ramg` `7eb87a09e2214693d978b754957f6dc09f79095fb1bbca7089c9ca7e563115ae`
  - `mbc2_bits_romb` `f382f82c0025093b52575bcd35715131b681392f28a81d88180db973b5ff8090`
  - `mbc2_bits_unused` `d33bed573c162b3384048dddc10c3b0d0d89dbb9023d1608cd70286988c0fa77`
  - `mbc2_ram` `5b82d04e284a0c396271e4df0d345c7383d1c86467675a272d9a4e286f790f13`
  - `mbc2_rom_512kb` `4c7a8a58e3bf5a45afb71b079aead912f336a13972ff93b59f964bedbc87fda5`
  - `mbc2_rom_1Mb` `7eba692d8f426d1b6187095a9c14a99ef5ea80534d996949bca8bf0bd9e77cc3`
  - `mbc2_rom_2Mb` `32530509d8182718b005e183259cb6eaeeb7db15c6b634ebdc362016591dadec`
  - `mbc5_rom_512kb` `701cce7a923f2291756c364ad587b0f3a1ca3c12ed904e61323614ce6ddddc0b`
  - `mbc5_rom_1Mb` `9d9d21129bfc91b5c22d9d6a30a08bdee309786ad21532cb8817e19295fffe69`
  - `mbc5_rom_2Mb` `5a152aa873f104f6acf865f642b1cf86abc5f2cceea81118f238794aaf9f70ab`
  - `mbc5_rom_4Mb` `4173c92d61533ed5f3cdd8f2ca83d3701ca042b28bceeed1021a79065368fa86`
  - `mbc5_rom_8Mb` `176cd6f9a16519ba30f7d0cec3d46226ef304f3ad54e41d6d23974a03e6157a1`
  - `mbc5_rom_16Mb` `65602bf590e9c2f5d22e3db3597c95d763a8fe562556bac9c8a82baf3ed3a59e`
  - `mbc5_rom_32Mb` `f37b1e7af46d69e5c42df0e7e421e306b48b6c6e789cb35e091e41c0fe67e668` (4 MiB)
  - `mbc5_rom_64Mb` `f1148d3cc631e330b991b3f34d728de5b3789b00b80b9778fb08a9bbb59efef7` (8 MiB)
- **D-26:** The pass oracle is unchanged from v0.1 (`src/runner/main.c:127-153`):
  - Pass: LD B,B (`$40`) at the per-ROM `result_pc`, B/C/D/E/H/L = `03 05 08 0d 15 22`, with the pass callback PC seen first.
  - Fail: six `$42` bytes with the fail callback PC.
  - Anything else is `unsupported`.
  - Each case has a finite budget **measured at admission**, not estimated.
  - Per-ROM `result_pc`, `pass_callback_pc` and `fail_callback_pc` come from the linker `.sym` and appear in both the manifest and the compiled table. A CTest asserts the two agree.
  - Do not route these ROMs through `--acceptance`, which rejects `fibonacci-ldbb` by design.
  - The receipt reports `mbc2=7/7 mbc5=8/8` and eligible = executed = 15. A missing or extra ROM fails verification.
- **D-27:** First admission task: run the real ROMs as soon as MBC5 and MBC2 exist.
  - The patch's print pointer at WRAM `$c000` coincides with the harness `wram.functions $c000` copy. By inspection the pass path looks safe, and failure would show as timeout or `unsupported`, never a false pass.
  - If the pass path is corrupted, apply the D-24 sibling patch variant.
- **D-28:** Runner changes:
  - Replace the single compiled `cases[]` and `MOONEYE_MANIFEST_SHA256` with a small `suite_def` list `{manifest sha256, cases, count}`, selected by the SHA-256 of `--manifest`. An unknown digest fails `invalid-manifest` (fail closed).
  - Replace the fixed `MAX_ROM 32768` and the `n != MAX_ROM` check with a per-case `size_bytes`. Allocate `size_bytes + 1`, capped by `GBB_CASES_MAX_ROM_BYTES` (8 MiB).
  - Per-case CTests mirror `mooneye_case_*`, plus one suite CTest, all appended to `expected-tests.txt`.
  - The existing three-case Mooneye path must keep identical output.
- **D-29:** Negative controls:
  - A mutated copy of one mbc5 ROM (type byte changed to MBC1, checksum fixed) must not report pass.
  - If the seam exposes the ROM-bank write cleanly, add a test-only core mutant (same configure-time, never-installed pattern as D-046) that drops the ninth bank bit. It must fail `rom_64Mb` while `rom_32Mb` passes, which proves `rom_64Mb` is the discriminator. The anchor must occur exactly once.
- **D-30:** Evidence class: author-attested hardware results (flash cart with a genuine MBC5 or MBC2A chip), executed on the bootless DMG-CPU-B profile.
  - There is no model-specific claim and no CGB claim, and the results are never presented as game compatibility.
  - The MBC2A variant caveat is recorded.
  - The hosted, non-required `fixture-repro.yml` leg is extended to rebuild and compare the sibling set.

### H. The 4 MiB and 8 MiB ROMs: repository and install policy
- **D-31:** `rom_32Mb` (4 MiB) and `rom_64Mb` (8 MiB) are **committed raw**.
  - Not regenerated at build time, which would need network and a toolchain in ordinary CTest. Not compressed in-tree. Not Git LFS.
  - Measured cost: about 13 KiB in a git pack for both, and about 17 MiB of checkout disk per OS for all 15.
  - `.gitattributes`: `fixtures/mooneye-mbc/*.gb binary`, `fixtures/mooneye-mbc/manifest.json -text`, and `text eol=lf` for digested md/txt/json files.
  - Add a third-party notices row.
- **D-32:** Install and package exclusion is proven, not assumed. The `install(FILES …)` allowlist (`CMakeLists.txt:120-140`) already excludes the sibling directory. Add a scan script in the style of the libbet scan:
  - It runs against the install tree used by `libbet_install` (`FIXTURES_REQUIRED`) and against the extracted preview package prefix in `PreviewPackageSmoke`.
  - It fails on any installed file whose size and SHA-256 match a sibling-manifest ROM, or any path containing `mooneye`.
  - It prints a file count and fails on an empty tree.
  - A self-test plants a small ROM and expects exit 1.
  - It also asserts the installed `share/gabbaboy/fixtures` directory list is exactly `tracer`, `visible-demo`, `mbc1-continuation`.

### I. Original MBC5 fixtures (success criterion 4)
- **D-33:** Add an original, project-authored guest `fixtures/mbc5-banking/`:
  - Contents: `.asm`, `.gb` of 64 KiB or less, `manifest.json`, `LICENSE.txt`. Built with RGBDS 1.0.1 like `fixtures/mbc1-continuation`, and reproducible in the existing `fixture-repro.yml` RGBDS 1.0.1 leg.
  - It reports through WRAM markers, as `continuation.asm` does: `C000=$A5` pass, `C001=$EE` fail, plus one result byte per sub-check. It is read by a C test through `gbb_peek_ram`.
  - Sub-checks:
    - bank 0 in the upper window;
    - low-byte-then-high-bit and high-bit-then-low-byte orders;
    - RAM bank 15 on a non-rumble 128 KiB type;
    - rumble bit 3 masked from RAM banking on `$1E`, with `gbb_rumble_state` observed by the C test.
  - The `$1FF` case: `tests/test_mbc5.c` inflates the guest to 8 MiB in memory. It patches header code `$08`, writes a marker in bank `$1FF`, fixes the checksum and frees the buffer. The guest reads the marker through the real CPU and bus path.
  - The manifest states that the `$1FF` marker is harness-supplied, and that the evidence class is "original software fixture plus synthetic oracle, not hardware evidence". It also states: no CGB, no physical rumble, no MBC5 hardware observation.
  - No committed original ROM exceeds 64 KiB.
  - Install policy mirrors mbc1-continuation, so only small files are installed. If installed, the D-32 scan's allowed fixture list is updated in the same plan.
  - **Planner's choice:** whether this fixture is installed. Default: not installed, which leaves the D-32 list unchanged.
- **D-34:** C unit tests on synthetic in-memory ROMs (`tests/test_mbc5.c`, `tests/test_mbc2.c`) cover the edge cases:
  - bank masking and one-over reads;
  - `$0A/$1A/$00/$0B` enable;
  - the rumble counter, reset and load semantics;
  - the MBC2 echo, nibble and import-normalisation rules;
  - a two-instance 512-byte MBC2 round trip (write via guest, copy, import into a fresh instance, guest reads back);
  - the header rows for `$05/$06/$19-$1E`.

  MBC2 needs no assembled original fixture in Phase 8. Mooneye covers it 7/7, and the authored `fixtures/mbc2-continuation` belongs with CART-06 in Phase 9.

### Claude's Discretion
- Exact field, enum and helper names inside the cartridge section; the table row layout.
- How plans split the Mooneye-mbc admission versus mapper implementation, provided the seam plan is first and pure (D-08, D-09).
- The scan script's language (CMake script versus `python3 -I`), following the closest existing pattern.
- Whether the D-29 ninth-bit core mutant is feasible cleanly. If the anchor cannot be made unique without contorting the code, record why and keep the type-byte mutation control.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and requirements
- `.planning/ROADMAP.md` §"Phase 8: Cartridge Seam, MBC5 and MBC2": goal, four success criteria, plan ordering note.
- `.planning/REQUIREMENTS.md`: CART-01, CART-02, CART-03 (and CART-04..06 to avoid taking Phase 9 scope); Out of Scope table (MBC30, MBC1M, unlicensed fixtures).
- `AGENTS.md`: workflow, evidence and fixture-rights rules.

### Prior decisions and evidence policy
- `.planning/context/DECISIONS.md`: D-010 (copied ROM ownership), D-011 (battery vs snapshots, host owns files), D-025 (confidence-qualified models), D-041 (declared denominators), D-046 (core-mutant contract).
- `docs/game-acceptance.md` §"Using the baseline in later phases": zero changed ledger lines, change protocol.
- `tests/baseline/CHANGES.md`, `tests/baseline/dmg-cpu-b-v1.txt`, `cmake/VerifyDmgBaseline.cmake`, `tests/scripts/verify-dmg-baseline.sh`: frozen DMG baseline and inventory rules.

### v0.2 research (background; the decisions above override where they differ)
- `.planning/research/v0.2/ARCHITECTURE.md` §"Current-source facts", §2 "Cartridge mapper dispatch", §8 "Battery file format", §"Anti-patterns". D-01 overrides its `cartridge.c` proposal.
- `.planning/research/v0.2/PITFALLS.md` V2-08 (MBC1 path reuse), V2-09 (MBC5 ROM bank), V2-10 (MBC5 RAM/rumble), V2-11 (MBC2), V2-12 (header lies), V2-17 (fixture licensing).
- `.planning/research/v0.2/FEATURES.md` §2 MBC2, §4 MBC5, API table.
- `.planning/research/v0.2/STACK.md` §"A. Cartridge mappers", "Fixture payload size", indicative derivative digests.

### Code and fixtures
- `src/core/gabbaboy.c`: MBC1 helpers (~412-442), `read8`/`write8` cartridge branches (~684-694, ~744-775), `read_supported` (~960-970), `validate_header`/`gbb_load_rom` (~1615-1735), battery API (~1737-1790).
- `include/gabbaboy/gabbaboy.h`: `gbb_error` enum (append-only), battery API docs (~140-157).
- `docs/cartridge-and-saves.md`, `docs/native-integration.md`, `docs/mbc1-evidence.md`.
- `src/runner/main.c` (Mooneye table, oracle 127-153, `MAX_ROM`), `src/runner/cases.c`, `src/runner/acceptance.h`.
- `src/player/session.c` (identify ROM 158-171, max ROM 19), `src/player/main.c`, `src/player/limitations.h`.
- `fixtures/mooneye/*` (manifest, SOURCES, ELIGIBILITY, patch, font-source.c), `fixtures/mbc1-continuation/*`, `fixtures/libbet/*` (scan precedent).
- `tests/test_cartridge.c`, `tests/test_battery.c`, `tests/test_loader.c`, `tests/test_loader_fuzz.c`, `tests/measure_core.c`, `tests/CMakeLists.txt`, `tests/acceptance/CMakeLists.txt` (mutant 287-300), `tests/expected-tests.txt`, `.github/scripts/verify-test-inventory.sh`, `tests/scripts/reproduce-mooneye.sh`, `tests/scripts/verify-libbet-admission.py` (scan pattern), `cmake/VerifyMooneye.cmake`.
- `CMakeLists.txt` (core source 23, dirty list 69, install allowlist 120-140), `.gitattributes`, `.github/workflows/ci.yml`, `.github/workflows/fixture-repro.yml`.

### External primary sources
- Pan Docs MBC5, MBC2 and Cartridge Header pages (gbdev/pandocs).
- Mooneye test suite `emulator-only/mbc2/*.s`, `emulator-only/mbc5/*.s`, `common/harness/mbc{2,5}_rom.s` at `31510e12eea6286d36eea060a6adde755e1067aa`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- MBC1 helpers and `cartridge_info` from `validate_header`: become the MBC1 row and case of the seam.
- The Mooneye register-signature oracle (`src/runner/main.c:127-153`): reused unchanged for 15 more cases.
- Derivative recipe (`headless-report.patch`, `font-source.c`, WLA-DX pin, `reproduce-mooneye.sh`): research verified that all 28 `emulator-only/mbc{1,2,5}` sources build and the patch applies.
- `fixtures/mbc1-continuation` WRAM-marker reporting, and its manifest and RGBDS 1.0.1 build: the template for `fixtures/mbc5-banking`.
- Libbet install-scan and planted-payload self-test pattern (`libbet_not_installed`, `verify-libbet-admission.py:354`): the template for D-32.
- Core-mutant configure pattern (D-046, `tests/acceptance/CMakeLists.txt:287-300`): the template for D-29.
- Runner already allows 8 MiB ROMs (`GBB_CASES_MAX_ROM_BYTES`, `src/runner/acceptance.h:29`).

### Established Patterns
- Append-only `gbb_error` enum. On error, outputs are unchanged (`gbb_battery_generation` convention).
- Validate, then allocate, then commit; no partial mutation; bounded inputs.
- `read_supported` is a fail-closed allow-list: new cartridge windows must be added deliberately.
- Third-party fixtures: pinned commit + tree, manifest with per-ROM SHA-256, LICENSE travels with ROMs, `.gitattributes` binary/-text, hosted non-required reproduction.
- CI requires an exact executed-vs-expected CTest set.

### Integration Points
- `src/core/gabbaboy.c` cartridge branches, `validate_header`, battery API, reset.
- `include/gabbaboy/gabbaboy.h`: `GBB_NO_RUMBLE`, `gbb_rumble_state`, comment updates.
- `src/runner/main.c`: suite selection by manifest digest, per-case sizes and PCs.
- `src/player/session.c`, `main.c`, `limitations.h`: the `battery_unsupported` status.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt`, `.gitattributes`, `fixture-repro.yml`, third-party notices, docs.

</code_context>

<specifics>
## Specific Ideas

- The "no observable change" claim is backed by a recorded old-versus-new loader and MBC1 differential (D-10), not only by tests passing.
- `rom_64Mb` is the only proof of the ninth bank bit. It is admitted and never dropped.
- Indicative digests are not claims until recaptured at admission and matched on hosted Linux.

</specifics>

<deferred>
## Deferred Ideas

- **Mooneye `emulator-only/mbc1/*` backfill** (13 ROMs; `multicart_rom_8Mb` would be an excluded candidate): the cheapest independent MBC1 oracle. Later sibling-manifest addition (category `mbc1`), Phase 9 or a v0.2 stretch. Add it to `.planning/context/FUTURE-MILESTONES.md` at the Phase 8 boundary update.
- **Split the cartridge section into `src/core/cartridge.c`**: a standalone move task after v0.2, with the six build-site checklist from D-01.
- **Region-decode refactor of `read8`**: with A/B evidence, when CGB banking registers need it.
- **Generalised data-driven suite verifier** (`VerifySuite.cmake`): when a third third-party suite arrives.
- **Player 8 MiB cap, MBC2/MBC5 persistence, envelope widening, `fixtures/mbc2-continuation`**: Phase 9 (CART-06).
- **`gbb_probe_rom` / `gbb_get_cartridge_info`**: CGB phases or SHIP-10.
- **Host haptics for MBC5 rumble**: future (already in REQUIREMENTS future list).
- **Packed 256-byte MBC2 save interop**: only with named fixtures.

</deferred>

---

*Phase: 08-cartridge-seam-mbc5-and-mbc2*
*Context gathered: 2026-10-11*
