# Phase 8: Cartridge Seam, MBC5 and MBC2 - Research

**Researched:** 2026-10-11
**Domain:** Portable-C Game Boy emulator core: cartridge mapper seam, loader bounds, third-party test-ROM admission, install-artifact exclusion
**Confidence:** HIGH for in-repo facts (files opened this session); MEDIUM for hardware semantics (Pan Docs, plus the pinned Mooneye sources); LOW for per-ROM run budgets and CI timing (must be measured at admission)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### A. Mapper seam shape (CART-01)
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

#### B. Proof of no observable DMG change (CART-01)
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

#### C. ROM size bound
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

#### D. MBC5 behaviour (CART-02)
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

#### E. MBC2 behaviour (CART-03), backed by Mooneye at pin `31510e1`
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

#### F. Player behaviour in Phase 8 (protects user data; does not take CART-06)
- **D-22:** Battery cartridge types other than `$03` (`$06`, `$1B`, `$1E`) **run without persistence and say so**:
  - The player keeps `battery_backed=false`, so no save, lock, recovery or temp file is read, renamed, created or written for them.
  - It adds a `battery_unsupported` identity flag, with a visible status ("Battery saving is not supported for this cartridge type yet; progress is not kept") and a stderr warning.
  - `src/player/limitations.h` and `docs/cartridge-and-saves.md` stop claiming "MBC1 only" but state the gap.
  - The v1 envelope still accepts only type `$03` with 8192 or 32768 bytes.
  - A player test asserts that no file appears under the save directory for such a cartridge.
  - Reason: once the core accepts these types, `player_session_identify_rom` (`src/player/session.c:161-170`) would otherwise drop progress silently.

#### G. Mooneye mbc2 and mbc5 derivative admission
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

#### H. The 4 MiB and 8 MiB ROMs: repository and install policy
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

#### I. Original MBC5 fixtures (success criterion 4)
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

### Deferred Ideas (OUT OF SCOPE)

- **Mooneye `emulator-only/mbc1/*` backfill** (13 ROMs; `multicart_rom_8Mb` would be an excluded candidate): the cheapest independent MBC1 oracle. Later sibling-manifest addition (category `mbc1`), Phase 9 or a v0.2 stretch. Add it to `.planning/context/FUTURE-MILESTONES.md` at the Phase 8 boundary update.
- **Split the cartridge section into `src/core/cartridge.c`**: a standalone move task after v0.2, with the six build-site checklist from D-01.
- **Region-decode refactor of `read8`**: with A/B evidence, when CGB banking registers need it.
- **Generalised data-driven suite verifier** (`VerifySuite.cmake`): when a third third-party suite arrives.
- **Player 8 MiB cap, MBC2/MBC5 persistence, envelope widening, `fixtures/mbc2-continuation`**: Phase 9 (CART-06).
- **`gbb_probe_rom` / `gbb_get_cartridge_info`**: CGB phases or SHIP-10.
- **Host haptics for MBC5 rumble**: future (already in REQUIREMENTS future list).
- **Packed 256-byte MBC2 save interop**: only with named fixtures.

</deferred>
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CART-01 | Cartridge behavior sits behind a type-table-driven mapper seam (kind, RAM, battery, RTC, rumble) with no observable change: MBC1 suite, battery continuation fixture, DMG baseline byte-identical | "Current-source map" (exact functions and lines to replace), "Seam table" (rows that encode today's MBC1 rules), Pitfalls P1-P6, Validation rows V-01..V-06 (purity diff, grep gates, old-vs-new differential, `measure_core` digest) |
| CART-02 | MBC5 (`$19-$1E`), 9-bit ROM banking incl. bank 0 in the switchable window, ROM to 8 MiB, RAM to 128 KiB, rumble bit masked and host-readable, Mooneye mbc5 8/8 | "MBC5 behavior notes", 8 MiB bound rule (P3), rumble API, 15-ROM fact table (mbc5 rows), `fixtures/mbc5-banking` design, ninth-bit mutant design, Validation rows V-07..V-16 |
| CART-03 | MBC2 (`$05/$06`), address-bit-8 decode, 512x4-bit RAM echoed through `A000-BFFF`, upper nibbles read 1s, 512-byte battery image, Mooneye mbc2 7/7 | "MBC2 behavior notes", battery import normalisation, 15-ROM fact table (mbc2 rows), Validation rows V-17..V-24 |
</phase_requirements>

## Summary

The seam is a mechanical, single-translation-unit refactor of roughly 150 lines in `src/core/gabbaboy.c`. Every MBC1 touch point is enumerated below with line numbers; the literal `cartridge_type == 0x03u` appears exactly twice (`:769`, `:1739`). The hard parts are not the mapper logic. They are (1) preserving every pre-Phase-8 loader return code while the absolute ceiling rises from 2 MiB to 8 MiB (the early `ROM_TOO_LARGE` check must become type-aware, and the ceiling for non-MBC5 types must stay 2 MiB, not the per-kind declared maximum; see P3), (2) the runner refactor, because `tests/test_runner.c` `#include`s `src/runner/main.c` directly and uses `cases[]`, `MAX_ROM`, `MOONEYE_PATCH_SHA256` and `fixture_case` field names (a sixth single-TU consumer that D-01's list does not name), and (3) proving the 8 MiB ROM and its siblings never reach an install tree or package, where the libbet precedent only scans the install tree and not the extracted preview package.

All 15 Mooneye derivatives in the scratch rebuild reproduce the D-25 indicative digests (recomputed this session: 15 of 15 match, every file length equals `32768 << header-code`, every header checksum is valid). Header bytes, `LD B,B` result addresses and pass/fail callback addresses are tabulated below. Two findings change the runner design: the mbc2 ROMs have several distinct fail callbacks (up to 6 for `mbc2_ram`), so a single `fail_callback_pc` per case cannot name them all (Open Question 1), and the pass callback for the `mbc5_rom_*` and `mbc2_rom_*` ROMs sits at a ROM-bank-0 address even though the code that reaches it runs from WRAM at `$C000`, so D-27's WRAM-collision concern does not touch the pass path by inspection (still to be confirmed by a real run).

Recommended plan shape (planner owns the final split; D-08 fixes only "seam first, MBC5 and MBC2 then parallel"): Plan A seam (only `gabbaboy.c` plus `.planning/`); Wave 2 in parallel: Plan B MBC5 core + 8 MiB bound + rumble API + tests, Plan C MBC2 core + tests; Wave 3 in parallel: Plan D Mooneye-mbc admission (sibling dir, runner `suite_def`, verifiers, CTests, notices, install-scan, ninth-bit mutant, hosted repro leg), Plan E `fixtures/mbc5-banking` + in-memory `$1FF` test, Plan F player `battery_unsupported`. D, E and F need B and C merged because they exercise real MBC5/MBC2 cartridges.

**Primary recommendation:** Land the seam as a pure `gabbaboy.c` diff proven by the old-versus-new differential (86,016 loader cells plus MBC1 read sequences, zero differences), keep the early size check as `size > (row-lookup says MBC5 ? 8 MiB : 2 MiB)` at the existing precedence slot, and treat every runner and install-scan change as additive with the three existing Mooneye cases producing byte-identical output.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Cartridge header admission, size bounds, error precedence | Core (`validate_header`, type table) | Public header comments and docs | Loader contract is part of the C API; no host involvement |
| ROM/RAM banking, RAM enable, rumble line | Core (cartridge section of `gabbaboy.c`) | Public API (`gbb_rumble_state`) | Hardware mapper behavior; hosts only observe |
| Battery image bytes (incl. MBC2 512-byte canonical form) | Core (4 battery calls) | Host owns files (D-011) | Core stays filesystem-free |
| Persistence status and "runs without persistence" message | Player adapter (`session.c`, `main.c`, `limitations.h`) | Docs | Host UI and file policy never enter the core |
| Mooneye-mbc suite selection, oracle, budgets | Runner adapter (`src/runner/main.c`) | Fixture manifest (`fixtures/mooneye-mbc/`) | Oracle lives in the runner; manifest pins data |
| Fixture admission (digests, rights, PCs) | CMake verification scripts and C test | `.gitattributes`, notices | Fail-closed pre-flight, no network |
| Install/package exclusion of 4/8 MiB ROMs | CMake install allowlist + scan script | `PreviewPackageSmoke.cmake`, CTest fixtures | Proven by scanning, not assumed |
| Fixture reproduction on Linux | Hosted, non-required `fixture-repro.yml` | Local container | Recaptures indicative digests |

## Standard Stack

No new libraries. This phase adds C to the existing core, CMake/CTest registration, small Python 3 `-I` or CMake-script verifiers, and pinned build tools used only for fixture authoring.

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| C17, `C_EXTENSIONS OFF` | project | Core, tests, runner | Existing contract [VERIFIED: CMakeLists.txt `set_target_properties(gabbaboy_core PROPERTIES C_EXTENSIONS OFF)`] |
| CMake / CTest | floor 3.25 (`cmake_minimum_required(VERSION 3.25)`); CI floor job 3.25.3; local 4.4.3 | Build, test registration | New scripts must avoid post-3.25 features [VERIFIED: CMakeLists.txt:1, local `cmake --version`] |
| RGBDS | **1.0.1 exactly** for fixture authoring | Build `fixtures/mbc5-banking` | Every fixture script rejects any other version [VERIFIED: tests/scripts/reproduce-mbc1-continuation.sh `[[ "$version_line" == "$tool v1.0.1" ]]`] |
| WLA-DX | 10.7, rev `91c52b1f4ef3cc8ba3c0638f7536539579af6a9f`, archive SHA-256 `24a95d77a79feeb70d1de87d66749c006e37337308ce9c00e44efac4c46ab976` | Mooneye derivative rebuild | [VERIFIED: fixtures/mooneye/manifest.json `builder`] |
| Mooneye test suite | rev `31510e12eea6286d36eea060a6adde755e1067aa`, tree `2b8c52424a49a2a7466cf631fd8992c53d0de2fa` | Source of the 15 ROMs | [VERIFIED: scratch checkout `git rev-parse HEAD` and `HEAD^{tree}` this session] |

### Supporting
| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| Python 3 stdlib, run as `python3 -I` | local 3.14.4 | Verifier/self-test scripts | Only if the closest precedent (libbet) is followed; a pure CMake script is the alternative (see Open Question 4) |
| jq | 1.7.1 local | `reproduce-mooneye.sh` reads the manifest with `jq` | Reproduction scripts only; never in ordinary CTest |
| `patch --batch --fuzz=0 -p1` | system | Apply `headless-report.patch` | Reproduction only |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw 4/8 MiB ROMs committed | Build-time regeneration, Git LFS, in-tree compression | Rejected by D-31 (needs network and toolchain in ordinary CTest). Measured cost is small: zlib-9 of the 4 MiB ROM is 6,171 bytes, of the 8 MiB ROM 11,640 bytes, all 15 together about 32.7 KiB (zlib level 6); checkout size of all 15 is 17,563,648 bytes [VERIFIED: python zlib and file sizes this session] |
| New `src/core/cartridge.c` | Delimited section in `gabbaboy.c` | D-01 overrides ARCHITECTURE.md §2 |

**Installation:** nothing to install for ordinary builds. Fixture authoring needs the pinned RGBDS 1.0.1 archive (macOS `rgbds-macos.zip` SHA-256 `2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645`; Linux `rgbds-linux-x86_64.tar.xz` SHA-256 `80a5cad8dae27e24e46a93041352c47cadbc165103983f41c2b3082c42f6dad9`) downloaded from the `gbdev/rgbds` v1.0.1 release and SHA-verified, exactly as `fixture-repro.yml` does [VERIFIED: fixtures/mbc1-continuation/manifest.json `build`]. The machine's Homebrew RGBDS is 1.0.4 and must not be used for committed bytes [VERIFIED: `rgbasm --version` this session].

**Version verification:** no registry packages are involved; versions above are read from pinned manifests.

## Package Legitimacy Audit

No external registry packages (npm, PyPI, crates) are installed or recommended by this phase, so the `package-legitimacy` seam was not run. The only third-party inputs are build tools and test ROM sources pinned by Git revision, tree and archive SHA-256 (RGBDS, WLA-DX, Mooneye), which the existing fixture scripts already verify.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| (none) | - | - | - | - | n/a | n/a |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Current-source map (the seam extraction checklist)

All lines are in `src/core/gabbaboy.c` and were read this session.

| What | Lines | Verbatim anchor | Seam action |
|------|-------|-----------------|-------------|
| `cartridge_info` | 44-47 | `uint8_t type; size_t ram_size;` | Extend with the resolved table row data (kind, flags, RAM size); stays a plain struct |
| Instance mapper fields | 56-61 | `uint8_t cartridge_type; uint8_t mbc1_rom_bank_low; uint8_t mbc1_rom_bank_high; uint8_t mbc1_mode; int mbc1_ram_enabled;` | Fold into one `cart_state` sub-struct of fixed-width integers (D-02). `battery_generation`, `cartridge_ram`, `cartridge_ram_size`, `rom`, `rom_size` stay as instance fields |
| ROM ceiling | 410 | `#define GBB_MAX_ROM_SIZE ((size_t)2u * 1024u * 1024u)` | Unchanged in the seam plan. The MBC5 plan raises the absolute ceiling (D-14) |
| MBC1 helpers | 412-436 | `cartridge_is_mbc1`, `mbc1_rom_bank_mask`, `mbc1_rom_bank`, `mbc1_ram_offset` | Become the MBC1 case of the section; logic untouched |
| Mapper reset | 438-442 (inside `reset_state`) | `m->mbc1_rom_bank_low = 1u; m->mbc1_rom_bank_high = 0u; m->mbc1_mode = 0u; m->mbc1_ram_enabled = 0;` | Replace by one `mapper_reset()` call. `reset_state` is also called from `gbb_create` (rom NULL, kind zero) and `gbb_load_rom`, so it must be safe on an unloaded instance |
| `read8` ROM | 683-689 | `if (m->rom == NULL \|\| address >= m->rom_size) return 0xFFu; if (!cartridge_is_mbc1(m)) return m->rom[address];` | `switch (kind)`; ROM-only returns `m->rom[address]` after the same guards |
| `read8` RAM window | 690-695 | `if (m->mbc1_ram_enabled && m->cartridge_ram != NULL && m->cartridge_ram_size != 0u) return m->cartridge_ram[mbc1_ram_offset(m, address)]; return 0xFFu;` | `switch (kind)`; disabled or absent returns `0xFFu` |
| `write8` mapper | 744-755 | `if (cartridge_is_mbc1(m)) { if (address < 0x2000u) m->mbc1_ram_enabled = (value & 0x0Fu) == 0x0Au; else if (address < 0x4000u) ... & 0x1Fu ... & 0x03u ... & 0x01u` | `switch (kind)` |
| `write8` RAM + generation | 762-774 | `if (m->cartridge_type == 0x03u && m->battery_generation != UINT64_MAX) ++m->battery_generation;` | Replace the type literal with the stored `has_battery` flag |
| `read_supported` window | 965-969 | `(address >= 0xA000 && address <= 0xBFFF && m != NULL && ((m->cartridge_ram != NULL && m->cartridge_ram_size != 0u) \|\| cartridge_is_mbc1(m)))` | Replace `cartridge_is_mbc1(m)` with the stored `ram_window_mapped` flag; keep the RAM-present term so behavior is identical |
| `recognized_mbc1m_candidate` | 1620-1638 | unchanged | Unchanged (D-04) |
| `validate_header` | 1640-1680 | see "Header validation order" | Rewrite as table lookups with identical precedence |
| `gbb_load_rom` | 1707-1735 | validate, `malloc(rom_size)`, `memcpy`, optional RAM `malloc` + `memset(new_ram, 0xFF, info.ram_size)`, free old, commit, `instance->cartridge_type = info.type;`, `reset_state(instance);` | Commit the mapper sub-struct here. Keep validate-then-allocate-then-commit (D-05) |
| `has_battery_ram` | 1737-1742 | `instance->cartridge_type == 0x03u &&` | Replace with the stored `has_battery` flag |
| Battery calls | 1744-1779 | `gbb_battery_size/copy/import/generation` | Unchanged in the seam; the MBC2 plan special-cases import normalisation |
| JOYP mutant anchor | 540 | `if ((m->joypad_select & 0x20u) == 0)` | Occurs exactly once now [VERIFIED: `grep -c` returned 1]; must stay once |

Other facts the planner needs:

- OAM DMA never reads the cartridge. `dma_source_read` (`:1358-1365`) returns `0xFFu` for everything except `8000-9FFF` and `C000-DFFF`. `gbb_peek_ram` serves only WRAM and HRAM (`:2305-2311`). So the seam has no DMA or peek site, and the guest must read ROM and cartridge RAM through the CPU in every mapper test (or the host test reads battery bytes through `gbb_copy_battery`).
- `reset_state` already runs inside `gbb_load_rom`, after the cartridge fields are committed. To meet D-17 ("a successful `gbb_load_rom` zeros both" rumble line and counter, and `gbb_reset` counts one change if the line was on), clear the whole `cart_state` before the commit's `reset_state`, and make `gbb_reset` (not `reset_state`) the only path that records the line-off transition. A shared `reset_state` that records a transition would count a spurious change on load.
- Single-TU sites that compile or text-copy `gabbaboy.c` (D-01 lists five): `CMakeLists.txt:23` (`add_library(gabbaboy_core STATIC src/core/gabbaboy.c)`) and the dirty-source list at `:69`; alloc probe `tests/CMakeLists.txt:71` (`add_library(gabbaboy_core_alloc_probe OBJECT "${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c")` with `malloc=gbb_test_malloc ...` defines); `fuzz_core` `tests/CMakeLists.txt:168`; `tests/scripts/probe-mooneye-candidate.sh:137`; JOYP mutant `tests/acceptance/CMakeLists.txt:287-300`. **A sixth, runner-side site:** `tests/test_runner.c:6-8` does `#define main gbb_runner_program_main` / `#include "../src/runner/main.c"` and then uses `cases[0..2]`, `MAX_ROM`, `MOONEYE_SOURCE_REVISION`, `MOONEYE_PATCH_SHA256`, `fixture_case`, `run_guest(&cases[0], ...)`, `protocol_status`, `budget_status`, `unsupported_core_stop`, `suite_counts_valid`, `hash_matches`, `read_bounded` [VERIFIED: tests/test_runner.c read this session]. Runner changes must keep those identifiers or update `test_runner.c` in the same plan. The mutant runner (`gabbaboy-runner-joyp-mutant`, `tests/acceptance/CMakeLists.txt:309-321`) lists `src/runner/main.c`, `cases.c`, `acceptance.c` and the `src/accept/*.c` files explicitly, so a new runner `.c` would have to be added there and to the dirty list in `CMakeLists.txt:69`. Keep the runner change inside `main.c` (D-28 already implies this).

### Header validation order today, and the target precedence

Today (`:1640-1680`, read this session):

```
if (rom == NULL || size == 0) return GBB_INVALID_ARGUMENT;
if (size < 0x150) return GBB_ROM_TRUNCATED;
if (size > GBB_MAX_ROM_SIZE) return GBB_ROM_TOO_LARGE;
... is_mbc1 = type >= 0x01u && type <= 0x03u;
if (type != 0x00u && !is_mbc1) return GBB_UNSUPPORTED_CARTRIDGE;
if ((!is_mbc1 && rom_size_code != 0u) || (is_mbc1 && rom_size_code > 0x06u)) return GBB_UNSUPPORTED_ROM_SIZE;
RAM rule (type 0/1: code != 0 -> UNSUPPORTED_RAM_SIZE; 2/3: code 2 -> 8192; code 3 and rom code <= 4 -> 32768; else UNSUPPORTED_RAM_SIZE)
declared = (size_t)32768u << rom_size_code;
if (size < declared) return GBB_ROM_TRUNCATED;
if (size != declared) return GBB_ROM_SIZE_MISMATCH;
header checksum over 0x134..0x14C vs rom[0x14D] -> GBB_INVALID_ROM
if (is_mbc1 && declared >= 512u * 1024u && recognized_mbc1m_candidate(rom, size)) return GBB_UNSUPPORTED_CARTRIDGE_VARIANT;
```

Target (D-05, D-14, D-20): same order, with two table-driven changes. Step 3 becomes "ceiling = row says MBC5 ? 8 MiB : 2 MiB (also 2 MiB when the type byte has no row); `size > ceiling` returns `ROM_TOO_LARGE`" using `rom[0x147]`, which is safe because `size >= 0x150` was just established. Steps 4-5 consult the row: no row means `UNSUPPORTED_CARTRIDGE`; `rom_size_code > row.max_rom_code` means `UNSUPPORTED_ROM_SIZE` **before** the `32768u << code` shift (the current code never shifts an out-of-range code; a table version must keep that ordering).

## MBC5 and MBC2 behavior notes (what the planner needs beyond the locked decisions)

- **Mooneye MBC5 harness probes order independence and masking.** `switch_bank` writes the low byte to `ROMB0` then writes `b | %11111110` to `ROMB1` ("set high bits to expose bugs"), so only value bit 0 may reach bit 8; the test also asserts `$0000-$0001` reads as zero (bank 0 always at `$0000`) and compares `$4000-$4001` against an expected-bank word table (`expected_banks`, 512 entries for `rom_64Mb`) [VERIFIED: scratch `mt/common/harness/mbc5_rom.s`]. The expected table is the bank number for in-range banks and the masked bank for smaller ROMs.
- **Pan Docs agree with D-16** on MBC5: `2000-2FFF` low 8 bits, `3000-3FFF` the 9th bit, bank 0 selectable at `4000-7FFF` ("Writing 0 will indeed give bank 0 on MBC5, unlike other MBCs"), RAM bank `$00-$0F`, bit 3 of the RAM bank register drives the motor on rumble carts, and real MBCs enable RAM for any value whose low nibble is `$A` [CITED: https://gbdev.io/pandocs/MBC5.html]. Pan Docs advise against relying on the low-nibble rule; D-16 adopts it and pins `$0A`, `$1A`, `$FA` as enable and `$00`, `$0B`, `$A0` as disable.
- **Pan Docs agree with D-18** on MBC2: address bit 8 selects RAM enable (clear) or ROM bank (set), RAM enable iff low 4 bits are `$A`, ROM bank is the low 4 bits with 0 becoming 1, only the bottom 9 address bits index the 512 half-bytes so access repeats, and the upper 4 bits are "undefined" in hardware docs [CITED: https://gbdev.io/pandocs/MBC2.html]. The `$F` upper-nibble rule is D-19's choice, backed by Mooneye `ram.s` round 6 on a genuine MBC2A, not by Pan Docs.
- **MBC2 ROM bank translate-then-mask:** with a 4-bank ROM (the `mbc2_rom_512kb` derivative, 64 KiB) writes of 0..7 must produce banks `1 1 2 3 0 1 2 3`, which is `(v & 0x0F)` translated 0 to 1 and then masked by `banks - 1` (D-18).
- **Rumble types with 128 KiB RAM:** the 3-bit RAM-bank mask on `$1C-$1E` makes banks 8-15 unreachable even if the header declares 128 KiB (D-16 accepts that header). Tests should assert that `$0F` written to `$4000-$5FFF` on a `$1E`/128 KiB image selects bank 7 and turns the line on.
- **No-RAM MBC5 types (`$19`, `$1C`):** D-16 says absent RAM reads `$FF`. For `read_supported` this means the `A000-BFFF` window must be mapped for every MBC5 row, exactly as it is for MBC1 `$01` today (otherwise a guest read there stops with `GBB_STOP_UNSUPPORTED_BUS`). This is the planner-visible consequence of D-03's `ram_window_mapped` column; it is a recommendation on the table cell, not a locked decision (A4).

## Seam table (rows that reproduce today's behavior and add the new ones)

Derived from D-04, D-14, D-16, D-20. `early ceiling` is the value used by the early `ROM_TOO_LARGE` check (P3); it is **not** the per-kind declared maximum.

| Type | Kind | Window mapped | Battery | Rumble | Max ROM code | RAM rule | Early ceiling |
|------|------|---------------|---------|--------|--------------|----------|---------------|
| `$00` | ROM_ONLY | no (only if RAM present, which never happens) | no | no | `$00` | code `$00` only | 2 MiB |
| `$01` | MBC1 | yes | no | no | `$06` | code `$00` only | 2 MiB |
| `$02` | MBC1 | yes | no | no | `$06` | `$02` (8 KiB) or `$03` (32 KiB) only if ROM code <= `$04` | 2 MiB |
| `$03` | MBC1 | yes | yes | no | `$06` | same as `$02` | 2 MiB |
| `$05` | MBC2 | yes | no | no | `$03` | code `$00` only; 512 bytes built in | 2 MiB |
| `$06` | MBC2 | yes | yes | no | `$03` | code `$00` only; 512 bytes built in | 2 MiB |
| `$19` | MBC5 | yes | no | no | `$08` | code `$00` only | 8 MiB |
| `$1A` | MBC5 | yes | no | no | `$08` | `$02` 8 KiB, `$03` 32 KiB, `$05` 64 KiB, `$04` 128 KiB | 8 MiB |
| `$1B` | MBC5 | yes | yes | no | `$08` | same as `$1A` | 8 MiB |
| `$1C` | MBC5 | yes | no | yes | `$08` | code `$00` only | 8 MiB |
| `$1D` | MBC5 | yes | no | yes | `$08` | same as `$1A` | 8 MiB |
| `$1E` | MBC5 | yes | yes | yes | `$08` | same as `$1A` | 8 MiB |
| all others | none | n/a | n/a | n/a | n/a | `GBB_UNSUPPORTED_CARTRIDGE` | 2 MiB |

`has_timer` stays 0 everywhere in Phase 8 (D-02). Type `$04`, `$07+` (other than the rows above), `$0F-$13` (MBC3, Phase 9) stay `GBB_UNSUPPORTED_CARTRIDGE`; `tests/test_loader.c` uses type `4` for `unsupported_cartridge` and `non_destructive`, so those tests keep passing.

## Architecture Patterns

### System Architecture Diagram

```
 host ROM bytes (caller-owned, size n)
        |
        v
 gbb_load_rom --> validate_header(rom, n)  [no allocation, no mutation]
        |             1 NULL/0  -> INVALID_ARGUMENT
        |             2 n<0x150 -> ROM_TRUNCATED
        |             3 n > ceiling(row(rom[0x147])) -> ROM_TOO_LARGE   (2 MiB, or 8 MiB for MBC5 rows)
        |             4 no row -> UNSUPPORTED_CARTRIDGE
        |             5 rom code > row max -> UNSUPPORTED_ROM_SIZE   (before the shift)
        |             6 RAM rule fails -> UNSUPPORTED_RAM_SIZE
        |             7 n < declared -> ROM_TRUNCATED ; n != declared -> ROM_SIZE_MISMATCH
        |             8 header checksum -> INVALID_ROM
        |             9 MBC1M candidate -> UNSUPPORTED_CARTRIDGE_VARIANT
        v
   allocate copy + RAM (RAM size from row: MBC2 = 512 fixed, never $149) --> commit --> cart_state{kind,flags}
        |                                                                          |
        |   guest CPU fetch/read/write ---> read8/write8 ---> switch(kind)         |
        |        0000-7FFF  ROM banks / mapper registers                           |
        |        A000-BFFF  RAM window (per kind)                                  |
        v                                                                          v
  battery calls (size/copy/import/generation)                       gbb_rumble_state (MBC5 rumble rows)
        |
        v
  host: files, persistence policy, haptics (not the core)

 runner: --manifest <file> --suite|--case
        bytes -> SHA-256 -> suite_def{manifest sha, cases[], count}   (unknown digest: invalid-manifest)
        per case: read size_bytes+1, size check, SHA-256 check, gbb_load_rom, gbb_run_ex chunks,
                  trace watches pass_callback_pc, then LD B,B at result_pc with B..L = 03 05 08 0d 15 22
```

### Recommended structure (no new files in `src/`)

```
src/core/gabbaboy.c            # delimited "Cartridge mapper" section (D-01)
include/gabbaboy/gabbaboy.h    # GBB_NO_RUMBLE, gbb_rumble_state, comment updates (MBC5 plan)
src/runner/main.c              # suite_def, per-case size_bytes (Mooneye-mbc plan)
src/player/{session.[ch],main.c,limitations.h}   # battery_unsupported (player plan)
fixtures/mooneye-mbc/          # 15 .gb, manifest.json, LICENSE.txt (+FONT-LICENSE.txt), SOURCES.md, ELIGIBILITY.md
fixtures/mbc5-banking/         # banking.asm, banking.gb (<=64 KiB), manifest.json, LICENSE.txt
tests/test_mbc5.c, tests/test_mbc2.c
tests/scripts/reproduce-mooneye-mbc.sh, tests/scripts/reproduce-mbc5-banking.sh
cmake/VerifyMooneyeMbc.cmake, cmake/ScanForbiddenFixtures.cmake (or Python equivalents)
```

### Pattern 1: one section, `switch (kind)`, flags copied into `cart_state` at load
**What:** Look up the row once in `validate_header`, copy kind and flags into plain integers, dispatch with `switch`. **When:** all cartridge decisions in `read8`, `write8`, `read_supported`, `has_battery_ram`, reset, load. Illustrative skeleton only; names are the executor's (Claude's Discretion):

```c
/* illustrative; values come from D-02/D-04/D-16/D-18 above */
typedef enum { CART_ROM_ONLY = 0, CART_MBC1, CART_MBC2, CART_MBC5 } cart_kind;
typedef struct {
    uint8_t kind, has_battery, has_rumble, ram_window_mapped;
    uint8_t rom_bank_lo, rom_bank_hi, ram_bank, ram_enabled, rumble_on, mbc1_mode;
    uint64_t rumble_changes;
} cart_state;
```

`CART_ROM_ONLY = 0` matters: `gbb_create` uses `calloc`, so a zeroed instance must behave as today's `cartridge_type == 0`.

### Pattern 2: MBC5 ROM bank as two independent registers
**What:** keep `lo` (`$2000-$2FFF`, 8 bits) and `hi` (`$3000-$3FFF`, value bit 0 only) as separate bytes; compute `(((size_t)(hi & 1u)) << 8 | lo) & (rom_banks - 1)`; no 0-to-1 remap; `$0000-$3FFF` always bank 0. Never fold the two writes into one 16-bit store (write order would then matter).

### Pattern 3: MBC2 decode by address bit 8, canonical RAM `0xF0 | nibble`
**What:** for `address < 0x4000`, `(address & 0x0100) == 0` selects RAM enable `(v & 0x0F) == 0x0A`, otherwise ROM bank `v & 0x0F`, 0 becomes 1, then mask by `banks - 1`. `$4000-$7FFF` writes do nothing. RAM index `address & 0x1FF`; store `0xF0u | (value & 0x0Fu)`; bump `battery_generation` only if the stored byte changed. This differs from MBC1's `address < 0x2000` split; copying MBC1's range test into MBC2 would pass `bits_ramg` round 1 but fail `bits_romb`.

### Pattern 4: all-or-nothing import for MBC2 (D-21)
Compute whether `0xF0 | (b & 0x0F)` differs from live RAM for any of the 512 bytes first; only if so, copy the normalised bytes and bump the generation once. Order of checks stays: NULL arguments, `NO_BATTERY`, `BATTERY_SIZE_MISMATCH` (size must be exactly 512), then compare/commit.

### Pattern 5: runner `suite_def` selected by manifest digest, fail closed
Add `size_bytes` to `fixture_case` (set to `MAX_ROM` for the three existing rows so `test_runner.c` still compiles), add `mbc_cases[]`, and replace `manifest_valid`'s single-digest compare by a lookup over `{manifest_sha256, cases, count}`. `MOONEYE_MANIFEST_SHA256` is used at `src/runner/main.c:71` (`manifest_bytes_valid`) and in the two receipt `printf`s in `run_one` (`:217`, `:232`) [VERIFIED: grep this session]; replace those uses with the selected suite's digest so the existing path prints identical bytes (the three `PASS_REGULAR_EXPRESSION` CTests at `tests/CMakeLists.txt:308-312` pin those strings).

### Anti-Patterns to Avoid
- **Function-pointer vtables or a second `.c`:** rejected by D-01/D-02 and breaks the six single-TU sites.
- **Moving allocation into table code or allocating before all validation:** breaks "failed replacement leaves the instance unchanged" (tests `loader_non_destructive`, `loader_mbc1m_variant`, `loader_boundary_fuzz`).
- **Using the per-kind declared maximum as the early ceiling:** changes return codes for ROM-only and MBC2 images between 32 KiB and 2 MiB (P3).
- **Reordering the `read8` `if` chain or splitting regions:** D-06 forbids it in this phase; no baseline workload exercises MBC1 reads, so a regression there would be invisible to the baseline.
- **Editing any `tests/baseline/` file or adding a `baseline:` commit:** D-12.
- **Committing `.sym`, `.lnk` or `.log` build products:** the scratch ones embed absolute local paths (for example the `wla symbolic information for "/private/tmp/..."` header), which violates the privacy rule in AGENTS.md. Only extract PCs into the manifest.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SHA-256 in tests/scripts | a new hash routine | `src/accept/sha256.c` (`gbb_accept_sha256_hex`) in C; `file(SHA256 ...)` in CMake; `hashlib` in verifiers | Already present and exercised |
| JSON manifest parsing in CMake | regex over JSON | `string(JSON ...)` as `VerifyMooneye.cmake` does | Floor 3.25 supports it |
| Exact-exit-code negative controls | ad-hoc `|| true` | `tests/expect_exit.cmake` (`GBB_CMD`, `GBB_EXPECT_CODE`, `GBB_EXPECT_REGEX`) | A crash or changed failure class can never pass as the expected rejection |
| Planted-payload scan self-test | hand-checked output | copy the libbet pattern (`libbet_not_installed`, `libbet_not_installed_selftest`) | Proves the scan can fail |
| Header checksum helper in tests | include a shared test lib | copy the 6-line `fix_checksum` already duplicated in `test_cartridge.c`, `test_battery.c`, `test_loader_fuzz.c` | Matches the project's copy-over-dependency preference |
| Core mutant | editing the core in place | text-substitute into a generated `.c` at configure time, exactly-once anchor, never installed (D-046 pattern) | Already proven by the JOYP mutant |
| Mooneye ROM generation | hand-assembled substitutes | the pinned WLA-DX recipe (`wla-gb -I common`, `wlalink -nS -d -S`) | Digest-pinned provenance |
| 8 MiB fixture on disk | committing a generated 8 MiB original | inflate in memory in `tests/test_mbc5.c` (D-33) | Keeps committed originals <= 64 KiB |

**Key insight:** every piece of machinery this phase needs (digest-pinned manifests, planted-payload scans, core mutants, exact-exit negative controls, inventory registration) exists in the repo. Copy and adapt; do not generalise.

## Runtime State Inventory

The seam is a refactor of runtime behavior, so each category is answered explicitly.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Player save files: v1 envelope `GBBBSAVE`, cartridge type byte `$03` only, RAM length 8192 or 32768 (`src/player/session.h`, `session.c:158-171`). MBC1 files must load unchanged | None for existing files. D-22 stops the player from creating any file for `$06/$1B/$1E`, so no new on-disk state exists in Phase 8 |
| Live service config | None. No external service references cartridge types | None, verified by repository search of `.github/` and docs |
| OS-registered state | None | None |
| Secrets/env vars | None; no secrets involved in this phase | None |
| Build artifacts | Existing build trees (`build/`, `build-asan/`, `build-player/`) hold stale test binaries after `gabbaboy.c` changes; `fixtures/mooneye/candidate-digests.json` records parent candidates and must not change | Rebuild; do not touch `fixtures/mooneye/` (D-23) |

## Common Pitfalls

### P1: MBC1 behaviour drifts while moving to the table
**What goes wrong:** MBC1 `$01` (no RAM) stops mapping `A000-BFFF`, or `$02` with RAM code `$03` is accepted above 512 KiB.
**Why:** the current RAM rule is a four-way `if` that looks like data but has an ROM-code interaction. **Avoid:** encode the interaction as a row field (`ram32_max_rom_code = $04`), and keep the grid differential (D-10). **Warning sign:** `loader_mbc1_matrix` or `cartridge_no_ram_reads` fails.

### P2: `read_supported` fail-closed window
**What goes wrong:** an MBC5 no-RAM or MBC2 cartridge stops with `GBB_STOP_UNSUPPORTED_BUS` on its first `A000` access. **Avoid:** every new row sets `ram_window_mapped`; test with a guest read from `A000` on `$19`.

### P3: The early size check must keep a 2 MiB ceiling for every non-MBC5 type
**What goes wrong:** using `row.max_rom_bytes` (the per-kind declared maximum, for example 32 KiB for ROM-only) as the early ceiling turns today's `ROM_SIZE_MISMATCH` or `UNSUPPORTED_ROM_SIZE` for a 1 MiB ROM-only image into `ROM_TOO_LARGE`. **Why:** today the check is a flat `size > 2 MiB` before any header work. **Avoid:** ceiling = 8 MiB only when `rom[0x147]` has an MBC5 row, else 2 MiB, for no-row types too. **Verify:** the grid differential's "declared+1" and "above 2 MiB" classes; `loader_oversized` (8 MiB + 1, type `$00`, expects `GBB_ROM_TOO_LARGE`), `loader_boundary_fuzz` (2 MiB + 1 and `SIZE_MAX` with type `$01`, expect `ROM_TOO_LARGE` and an intact instance).

### P4: Shifting before range-checking the ROM code
`declared = (size_t)32768u << rom_size_code` with an unchecked code (`$52-$54`, `$FF`) is undefined or overflows on 32-bit `size_t`. Check `rom_size_code > row.max_rom_code` first. The grid includes codes `$52-$54` for exactly this.

### P5: Reset must not zero cartridge RAM or the generation, and must not count a rumble change on load
`reset_state` runs on create, reset and load. Use a separate `gbb_reset`-only step for the "line was on, now off" transition (D-17), and clear the counter on load only after the new cartridge is committed.

### P6: Allocation and partial mutation
Keep validate, allocate, commit. For MBC2 the 512-byte RAM comes from the row, not `$149`; a header lie (`$149 != 0`) is rejected earlier, so no allocation depends on an untrusted size.

### P7: MBC5 ninth bit
Write `$3000-$3FFF` stores `value & 1` only. The harness writes `b | 0xFE`; an implementation storing `value & 0x01` is right, one storing `value` or `value & 0x03` fails `rom_64Mb` (and only `rom_64Mb`, because `rom_32Mb` masks bit 8 away: 256 banks, mask `0xFF`). That is why `rom_64Mb` is the discriminator.

### P8: MBC5 bank 0 at `$4000` and the 0-to-1 remap
Do not reuse the MBC1 helper. D-13's cross-mapper control (`$00` written to `$2000`: bank 1 on MBC1, bank 0 on MBC5, a RAM-enable write on MBC2) catches accidental reuse.

### P9: Rumble bit lives in the RAM-bank register on rumble types
On `$1C-$1E` mask the RAM bank with `0x07`, track bit 3 as the line, and update the line on every `$4000-$5FFF` write regardless of RAM enable. On `$19-$1B` the mask is `0x0F` and there is no line (`gbb_rumble_state` returns `GBB_NO_RUMBLE`).

### P10: `GBB_NO_RUMBLE` placement
Append after `GBB_FRAME_NOT_READY`. By count (`GBB_OK` is 0, then 17 further enumerators through `GBB_FRAME_NOT_READY`) `GBB_FRAME_NOT_READY` is 17 and `GBB_NO_RUMBLE` becomes 18 [VERIFIED: include/gabbaboy/gabbaboy.h:18-35 read this session]. No consumer, player or runner code switches exhaustively over `gbb_error` with a missing-case diagnostic (no `-Wall/-Werror` in any CMake file), so the addition cannot break builds; `src/player/session.c:56-76` uses `default:`.

### P11: Runner receipt bytes must not change for the three existing cases
The `mooneye_case_*` CTests match long `PASS_REGULAR_EXPRESSION`s and `dmg_baseline` consumes `--manifest fixtures/mooneye/manifest.json --suite --observe` output. Only the manifest-digest selection and size handling may change.

### P12: The mbc2 ROMs have several fail callbacks
`mbc2_bits_ramg` has four fail sites, `mbc2_bits_romb` two, `mbc2_ram` six. See the fact table and Open Question 1.

### P13: `quit` result address differs per ROM family
`quit@serial_dump` (the first `LD B,B`) is `$407E` in `mbc2_bits_*`, `$4071` in `mbc2_ram` and `mbc2_rom_*`, `$4072` in `mbc5_rom_*`. A copied PC from the parent (`$409A`, `$4327`) will silently never match and produce `unsupported`, not a false pass.

### P14: `.gitattributes` and Windows
`fixtures/mooneye/manifest.json -text` exists because the runner admits the manifest by SHA-256 of its raw bytes. The sibling manifest needs the same, the 15 `.gb` files need binary treatment, and every digested text file needs `text eol=lf` (D-31). Without it a Windows `autocrlf` checkout changes the manifest digest and every `mooneye_mbc_*` test fails only on Windows. `ci.yml` already has a Windows "Capture exact Windows manifest bytes" step for the parent manifest; extend `tests/scripts/inspect-windows-manifest.sh` coverage only if the planner wants parity evidence.

### P15: Test names that start with `installed_` are filtered
`cmake/ExpectedTests.cmake` and `verify-test-inventory.sh --core-only` drop `installed_*` names. Name the install-scan tests `mooneye_mbc_not_installed...`, not `installed_...`.

### P16: Parallel plans collide on shared lists
`tests/expected-tests.txt` is compared as a sorted set, so file order is irrelevant: put each plan's names in a separate block. The same applies to `tests/CMakeLists.txt`. Each `add_test` must have a matching `expected-tests.txt` line in the same commit or configure fails at `gabbaboy_verify_registered_tests()`.

### P17: The CMake floor
New CMake scripts run on CMake 3.25.3 in CI (`cmake-floor-3-25-3`). Use `file(SIZE)`, `file(SHA256)`, `string(JSON)`, `cmake_path`, `file(COPY_FILE)` (3.21); avoid anything newer.

### P18: RGBDS pin
Local Homebrew RGBDS is 1.0.4. Committed `fixtures/mbc5-banking/banking.gb` must come from 1.0.1, otherwise the hosted `fixture-repro` leg fails. `rgbfix -f hg -p 0 -m 0x1E -r 4` sets `$147=$1E`, `$149=$04` (checked with local 1.0.4: `1e 00 04`) [VERIFIED: local run this session; confirm with 1.0.1].

### P19: In-memory `$1FF` inflation must fix three things
Header code `$148 = $08`, header checksum `0x14D` over `0x134..0x14C`, and total length `8 MiB` exactly (`32768 << 8`). Forgetting the checksum yields `INVALID_ROM`; forgetting the length yields `ROM_TRUNCATED`.

### P20: Absolute paths in repro outputs
`reproduce-mooneye-mbc.sh` must write evidence to a temp directory and commit only the ROMs and manifest; never the `.sym`, `.lnk`, `.log` files.

### P21: CI timing and memory
Eight 8 MiB `malloc`/`memcpy` pairs per process are trivial, but ASan doubles memory for the 8 MiB buffers; both are far below runner limits. Per-ROM budgets are unknown until measured (A2). Keep `TIMEOUT 30` like the parent cases unless the measured `mbc2_ram` run needs more.

### P22: The player's explicit 2 MiB message
`PLAYER_SESSION_MAX_ROM_SIZE` stays 2 MiB (D-15). Do not edit `read_rom_file` or the `rom_error` text for `GBB_ROM_TOO_LARGE`; tests `player_session_*` and `tests/player/test_session.c:133-138` pin the "2 MiB read bound" wording.

## Code Examples

### Today's MBC1 RAM-write path (the only literal to replace)
```c
/* Source: src/core/gabbaboy.c:762-774 */
else if (address >= 0xA000u && address <= 0xBFFFu) {
    if (m->mbc1_ram_enabled && m->cartridge_ram != NULL &&
        m->cartridge_ram_size != 0u) {
        const size_t offset = mbc1_ram_offset(m, address);
        const uint8_t previous = m->cartridge_ram[offset];
        if (previous != value) {
            m->cartridge_ram[offset] = value;
            if (m->cartridge_type == 0x03u &&
                m->battery_generation != UINT64_MAX)
                ++m->battery_generation;
        }
    }
}
```

### Mooneye MBC5 bank switch (why the ninth bit must be `value & 1`)
```asm
; Source: mooneye-test-suite 31510e1 common/harness/mbc5_rom.s
switch_bank:
  ld a, c
  ld (ROMB0), a
  ld a, b
  or %11111110 ; set high bits to expose bugs
  ld (ROMB1), a
  ret
```

### Configure-time exactly-once anchor (copy for the ninth-bit mutant, D-29)
```cmake
# Source: tests/acceptance/CMakeLists.txt:287-300
string(FIND "${gbb_core_text}" "${GBB_MUTANT_PATTERN}" gbb_mutant_first)
string(FIND "${gbb_core_text}" "${GBB_MUTANT_PATTERN}" gbb_mutant_last REVERSE)
if(gbb_mutant_first EQUAL -1 OR NOT gbb_mutant_first EQUAL gbb_mutant_last)
  message(FATAL_ERROR "core-mutant pattern '${GBB_MUTANT_PATTERN}' must occur exactly once in ...")
endif()
```
For the ninth-bit mutant, write the bank composition in one helper on a single line so a pattern such as the `& 1u) << 8` shift expression occurs once, replace `& 1u` with `& 0u`, build a second generated `.c` and a second runner executable (a copy of the JOYP mutant's source list), and add two CTests: sibling `--case mbc5_rom_64Mb` must not pass, `--case mbc5_rom_32Mb` must pass. This is feasible because MBC1's helper uses `<< 5`, so the pattern is unique (A6).

### Registration idiom
```cmake
# Source: tests/CMakeLists.txt (loader block)
foreach(case truncated oversized ... mbc1_matrix mbc1m_variant)
  add_test(NAME loader_${case} COMMAND test_loader ${case} ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
endforeach()
```
and the same names appended to `tests/expected-tests.txt`.

## Mooneye derivative fact table (indicative: Darwin/arm64 scratch rebuild; recapture on hosted Linux per D-25)

Source: the discuss-phase scratch rebuilds (`research-08/out/*.gb|*.sym`, not committed) and the pinned checkout `mt/`, processed with `scratchpad/tools/facts.py` and `chk.py`. All 15 SHA-256 values equal the D-25 list; each file length equals `32768 << $148`; each header checksum validates; title bytes are `mooneye-gb test`. `result_pc` is the label `quit@serial_dump`; the byte at that offset is `$40` (`LD B,B`) in all 15 ROMs. The second `LD B,B` at `quit@halt` is never the first one reached. Pass/fail callbacks are the `quit_inline` labels (the pass one follows `quit_ok`).

| Alias (ROM) | Bytes | `$147/$148/$149` | `result_pc` | `pass_callback_pc` | fail callback PCs |
|-------------|-------|------------------|-------------|--------------------|-------------------|
| `mbc2_bits_ramg` | 32,768 | `06/00/00` | `407e` | `01d7` | `0218 0255 029c 02c1` |
| `mbc2_bits_romb` | 65,536 | `06/01/00` | `407e` | `01c0` | `0174 01f8` |
| `mbc2_bits_unused` | 262,144 | `06/03/00` | `407e` | `018d` | `01cc` |
| `mbc2_ram` | 32,768 | `06/00/00` | `4071` | `029c` | `06f8 0719 073a 075b 077c 079d` |
| `mbc2_rom_512kb` | 65,536 | `05/01/00` | `4071` | `0207` | `0175` |
| `mbc2_rom_1Mb` | 131,072 | `05/02/00` | `4071` | `0207` | `0175` |
| `mbc2_rom_2Mb` | 262,144 | `05/03/00` | `4071` | `0207` | `0175` |
| `mbc5_rom_512kb` | 65,536 | `19/01/00` | `4072` | `0216` | `0175` |
| `mbc5_rom_1Mb` | 131,072 | `19/02/00` | `4072` | `0216` | `0175` |
| `mbc5_rom_2Mb` | 262,144 | `19/03/00` | `4072` | `0216` | `0175` |
| `mbc5_rom_4Mb` | 524,288 | `19/04/00` | `4072` | `0216` | `0175` |
| `mbc5_rom_8Mb` | 1,048,576 | `19/05/00` | `4072` | `0216` | `0175` |
| `mbc5_rom_16Mb` | 2,097,152 | `19/06/00` | `4072` | `0216` | `0175` |
| `mbc5_rom_32Mb` | 4,194,304 | `19/07/00` | `4072` | `0216` | `0175` |
| `mbc5_rom_64Mb` | 8,388,608 | `19/08/00` | `4072` | `0216` | `0175` |

SHA-256 values are exactly the 15 listed in D-25 above (not repeated to avoid drift; `chk.py` printed `True` for all 15).

Consequences:
- The header declares **no cartridge RAM** for every mbc5 derivative (`$19`, RAM code `0`), and the mbc2 ROMs use RAM code `0` as the loader (D-20) requires. None of the 15 exercises the 5-bit/9-bit RAM paths of MBC5 or rumble; those rest on `test_mbc5.c` and `fixtures/mbc5-banking`.
- MBC2 header ROM codes are `$00-$03` only, matching D-20's accepted range.
- Pass mechanism (D-26, unchanged oracle): the runner records the pass callback PC when it appears in the trace, and calls the run a pass only when the first `LD B,B` at `result_pc` has `B,C,D,E,H,L = 03 05 08 0d 15 22`. The harness `quit` routine loads those registers in `@success` and `0x42` in `@failure` before `magic_breakpoint` (`ld b, b`) [VERIFIED: scratch `mt/common/lib/quit.s`, `mt/common/macros.s`].
- The mbc5 pass callback executes from ROM bank 0 (`$0216`) even though `run_test_suite` itself runs from WRAM `$C000`: `quit_inline` loads the label's ROM address into `HL`, and `quit` returns into it. The patch's print pointer `ld hl, $c000` therefore overwrites the WRAM copy only after control has left it. This supports D-27's "pass path looks safe" but is still an inspection claim until the real run (A7).
- Budgets: the parent's `daa` budget is 2,000,000 half-dots against a measured 1,804,576 to `LD B,B` (`mooneye.daa.ldbb_half_dots` in `tests/baseline/dmg-cpu-b-v1.txt`). For the 15 new ROMs run each once with a very large budget after MBC5/MBC2 land, record the half-dot count at `LD B,B`, then set `budget` to a round multiple of it (suggest at least 2x; the planner records the multiplier) and store it in both manifest and table.

## Player facts (D-22)

- `PLAYER_SESSION_MAX_ROM_SIZE` is `(2u * 1024u * 1024u)` (`session.c:19`); `PLAYER_SESSION_MAX_RAM_SIZE` is `32768u`; save envelope max is `51 + 32768`.
- Battery gate: `player_session_identify_rom` (`session.c:158-173`) sets `battery_backed = rom[0x147u] == 0x03u && out_identity->ram_size != 0u` and `persistence_enabled = battery_backed`. Every later file operation (`battery_file_path`, load/save/lock at `session.c:247, 444, 664, 732`) returns early when `battery_backed` is false. D-22's approach (keep `battery_backed=false`, add a separate flag) therefore guarantees no save, lock, recovery or temp file for `$06/$1B/$1E`.
- Add `bool battery_unsupported` to `player_save_identity` (`session.h`). Tests build it with `player_save_identity identity = {0};`, so a new field is source-compatible.
- Status messages: after load the startup path (`main.c:~511-520`, status string at `:516`) chooses between "Battery RAM loaded; changes are in memory until saved" (when `battery_backed`) and "Ready"; the ROM-replacement path (`main.c:~950-965`, status string at `:960`) chooses between that and "ROM loaded; input and display state reset". Add a `battery_unsupported` branch in both, set the status to the D-22 text, and `fprintf(stderr, ...)` the warning.
- Text pins that must change together: `src/player/limitations.h` (`GBB_PLAYER_LIMITATIONS_TEXT` currently says "Battery saves support standard MBC1 type $03 with 8 or 32 KiB RAM.") and the byte-for-byte copy in `tests/player/test_limitations.c`; `README.md:6`, `docs/preview.md:3, 63`, `docs/cartridge-and-saves.md`.
- Player CTests are only registered with `-DGABBABOY_BUILD_PLAYER=ON` (macOS, SDL3 3.4.18 exact) from `tests/player/expected-tests.txt`; the `player_session_[a-z0-9_]+` pattern routes any new `player_session_*` name to `test_player_session`, whose `main` dispatches on the name inside `tests/player/test_session.c`. A new name (suggest `player_session_battery_unsupported`) needs a case there and a line in `tests/player/expected-tests.txt`. The test should load an in-memory ROM of type `$1B`/`$06`/`$1E`, call `player_session_replace_rom`, assert `battery_backed==false && battery_unsupported==true`, call load/save/lock, and assert the test preference directory stays empty.

## Test infrastructure facts

- **Registration:** `tests/CMakeLists.txt` uses `add_executable` + `foreach(case ...) add_test(NAME prefix_${case} COMMAND exe prefix_${case})`; `tests/expected-tests.txt` (261 lines at HEAD) must equal the registered set (except `installed_*` when no install prefix); `.github/scripts/verify-test-inventory.sh` compares the JUnit report to that file, failing on any skipped, failed, missing or extra case [VERIFIED: cmake/ExpectedTests.cmake, verify-test-inventory.sh].
- **Baseline ledger:** `tests/baseline/dmg-cpu-b-v1.txt` holds 314 `inventory.*` lines (core and player) plus `mooneye.*`, `acceptance.*`, `bench.*` sections. `cmake/VerifyDmgBaseline.cmake:422-431` flags only **removed** inventory keys; `:439-443` flags `extra:` only for the `mooneye`, `acceptance` and `bench` sections. Consequences: appended CTest names are safe; any new `mooneye.*` observation line would fail the check, so the sibling suite must not be added to the `--observe` set or to `gbb_collect_live` (D-23).
- **Frozen digest:** `bench.tracer.correctness_digest_fnv1a64 4c7a57ff3d50d228` [VERIFIED: tests/baseline/dmg-cpu-b-v1.txt:36]. `measure_core` usage: `measure_core (--trace|--no-trace) <rom>`; the baseline runs `measure_core --no-trace fixtures/tracer/tracer.gb` and parses `correctness_digest_fnv1a64=` and `workload=`. It reads at most 32,768 bytes (`MAX_ROM_BYTES 32768u`), so it exercises the ROM-only kind only (D-11).
- **Runner CLI:** `--manifest <file> (--case <id> | --suite) [--receipt] [--observe]`. `main()` rejects unknown flags with `invalid-arguments`; an unmatched manifest digest prints `invalid-manifest` and returns 2 (`runner_bad_manifest` expects that for `{}`).
- **Install-exclusion precedent:** `libbet_install_tree` (`FIXTURES_SETUP libbet_install`) installs into `${PROJECT_BINARY_DIR}/libbet-install-check`; `libbet_not_installed` (`FIXTURES_REQUIRED libbet_install`) runs `verify-libbet-admission.py --scan-dir`, which fails on any path component containing `libbet` (case-insensitive) or any file with size 32,768 and the ROM SHA-256, and on an empty tree; `libbet_not_installed_selftest` scans a planted `share/payload.bin` copy and expects exit 1 with `libbet-installed: share/payload.bin` [VERIFIED: tests/CMakeLists.txt, verify-libbet-admission.py:339-367, 700-715]. **Gap:** nothing scans the **extracted preview package**: `cmake/PreviewPackageSmoke.cmake` installs, tars (`installed-prefix.tar.gz`), extracts, and checks only that required files exist. D-32's second scan target therefore needs a new step inside that script. Because it is a `cmake -P` script with no Python path variable, implement the scan as a CMake script (usable from `expect_exit.cmake` for the CTests and `include()`d or `execute_process`ed from `PreviewPackageSmoke.cmake`), or pass `-DGBB_PYTHON=${Python3_EXECUTABLE}` into that test's command line.
- **Install allowlist:** `CMakeLists.txt:120-140` installs only `fixtures/tracer`, `fixtures/visible-demo`, `fixtures/mbc1-continuation` (plus `include`, `bin`, `lib`); the deterministic archive step walks only `bin include lib share` of the stage [VERIFIED: CMakeLists.txt, .github/scripts/create-deterministic-archive.py]. GitHub's automatic "Source code" archives are outside this control and will contain the 17 MiB sibling directory (Open Question 3).
- **Hosted repro:** `fixture-repro.yml` (non-required) has `fixture-repro` (RGBDS 1.0.1 pinned via manifests: it cross-checks `visible-demo`, `tracer` and `mbc1-continuation` build pins in an inline Python block, then runs `reproduce-visible-demo.sh` and `reproduce-mbc1-continuation.sh`), `mooneye-original-repro`, and `mooneye-candidate-repro` (stages parent provenance files and runs `reproduce-mooneye.sh --candidate-compare fixtures/mooneye`). `reproduce-mooneye.sh` hard-requires `$fixture_dir == $repo_root/fixtures/mooneye` and the three parent ROM names, so the sibling needs its own script (copy and adapt, per the copy-over-dependency preference). Add a sibling leg and a `mbc5-banking` step in the same non-required workflow; keep the pin-consistency Python block in step with a fourth manifest.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| cmake / ctest | all builds | yes | 4.4.3 (floor job 3.25.3 in CI) | - |
| C compiler (Apple clang) | build | yes | 21.0.0 | - |
| python3 | verifiers | yes | 3.14.4 | CMake script verifier |
| RGBDS 1.0.1 | `fixtures/mbc5-banking` authoring | **no** (1.0.4 installed) | 1.0.4 | download the SHA-pinned v1.0.1 release archive (network, as `fixture-repro.yml` does) |
| WLA-DX 10.7 rev `91c52b1...` | rebuilding Mooneye derivatives | **no** (`wla-gb` not on PATH; scratch `research-08/wla` has source only, not built here) | - | build from the pinned archive via the reproduce script (git + cmake + network) |
| jq, patch, curl, tar, unzip | repro scripts | yes | jq 1.7.1 | - |
| docker CLI | local Linux digest recapture | CLI present (29.5.2); daemon state not verified | - | hosted `fixture-repro.yml` leg (non-required) on the PR head |
| gh | PR/CI evidence | yes | 2.101.0 | - |
| SDL3 3.4.18 | player tests only | assumed present via `build-player/` (not verified) | - | skip player build locally; macOS hosted lane covers it |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** RGBDS 1.0.1 and WLA-DX need network access for the pinned downloads; D-25 requires the Linux recapture before any digest is claimed.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `cartridge_type` range checks scattered through the core | One type table drives header admission, window mapping, battery eligibility | This phase (D-02/D-03) | Phase 9 adds MBC3 as one row plus a case |
| Single compiled Mooneye table keyed by one manifest digest | `suite_def` list keyed by manifest SHA-256 | This phase (D-28) | A third suite later needs a row, not a rewrite |
| Hardware references call MBC2 upper nibbles "undefined" | Evidence-backed `$F` fill (Mooneye `ram.s` round 6, genuine MBC2A) | Mooneye pin `31510e1` | Export bytes are canonical `0xF0 | nibble` |

**Deprecated/outdated:** `.planning/research/v0.2/ARCHITECTURE.md` §2's `src/core/cartridge.c` proposal (overridden by D-01). The Game Boy Complete Technical Reference (gb-ctr) wording on the MBC5 RAM-gate register was not fetched this session (A3).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Hosted Linux rebuild reproduces the Darwin digests and PCs byte-for-byte | Fact table | A different digest means `fixtures/mooneye-mbc` bytes or the recipe need revisiting; D-25 already gates the claim on this |
| A2 | Each Mooneye-mbc ROM finishes well inside a 30 s CTest timeout and a modest half-dot budget | Pitfall P21, fact table | A larger `mbc2_ram` run needs a longer `TIMEOUT` or budget |
| A3 | gb-ctr (not fetched) does not contradict the Pan Docs low-nibble RAM-enable rule for MBC5 | MBC5 notes | Tests pin `$1A/$FA` as enable; a stricter real chip would make those two pins wrong (no Mooneye ROM tests MBC5 RAMG) |
| A4 | Map `A000-BFFF` for every MBC5 row, including no-RAM `$19/$1C` | Seam table | Otherwise a guest read there raises `UNSUPPORTED_BUS`; low risk, table cell is Claude's Discretion |
| A5 | Docker daemon is running locally for an optional Linux recapture | Environment | Use the hosted workflow instead |
| A6 | A unique single-line anchor for the ninth-bit mutant is achievable without contorting the helper | Code Examples | D-29 allows falling back to the type-byte mutation control only |
| A7 | The mbc5/mbc2 pass paths survive the headless patch unmodified (no sibling patch variant needed) | Fact table | If the real run shows `unsupported`/timeout, apply D-24's digest-pinned sibling patch variant |
| A8 | `rgbfix` 1.0.1 accepts `-m 0x1E -r 4` identically to 1.0.4 | Pitfall P18 | Build the fixture with 1.0.1 and read back header bytes before committing |
| A9 | The SDL3 player build is available locally | Environment | Player test runs on the macOS hosted lane only |

## Open Questions (RESOLVED)

All seven were resolved at planning with the recommended option; each item names the plan that records the decision.

1. **Fail-callback multiplicity in the runner oracle**
   - Known: D-26 keeps the oracle (pass needs the pass callback PC seen first; fail is six `$42` plus "the fail callback PC"). The table above shows 1 fail site for 11 ROMs, 2 for `mbc2_bits_romb`, 4 for `mbc2_bits_ramg`, 6 for `mbc2_ram`.
   - Unclear: whether the compiled row holds one fail PC (other fail sites report `unsupported`, exit 3, still not a pass) or a short bounded list.
   - Recommendation: a bounded array of up to 6 fail PCs per row (a few lines in `protocol_status`), so a real failure reports `status=fail` with the exact callback; keep `fail_callback_pc` as the field `test_runner.c` reads for the three parent rows.
   - RESOLVED: bounded `fail_callback_pcs` array of up to 6 with a count; scalar kept for the parent rows (Plan 08-05).

2. **Per-ROM budgets** are measured at admission after MBC5/MBC2 exist (D-26); record method, host and multiplier in `ELIGIBILITY.md`.
   - RESOLVED: measured half-dots at LD B,B times 2, rounded up to the next 100000, recorded in ELIGIBILITY.md (Plans 08-05, 08-06).

3. **GitHub auto-generated source archives** will include the sibling directory (about 17 MiB raw, about 33 KiB compressed). `export-ignore` in `.gitattributes` could exclude it but may interact with `.github/scripts/verify-release-source-proof.py` (no `export-ignore` is used anywhere today). Recommendation: do not add it in Phase 8; record the fact in `docs/` and revisit at the release boundary.
   - RESOLVED: no `export-ignore` in Phase 8; the fact is documented (Plan 08-09).

4. **Scan implementation language:** Python `-I` (copy of the libbet scan; needs `GBB_PYTHON` plumbing into `PreviewPackageSmoke.cmake`) versus CMake script (works unchanged inside `cmake -P`). Recommendation: CMake script, because both call sites are CMake and CMake 3.25 has every needed primitive. This is Claude's Discretion per CONTEXT.
   - RESOLVED: CMake script hooked into `PreviewPackageSmoke.cmake` (Plan 08-07).

5. **Sibling VerifyMooneye variant:** `cmake/VerifyMooneye.cmake` hard-codes categories `cpu`/`timer`, pins suite and builder revisions and requires `required_roms == eligible ROMs`. D-23 forbids changing it, so create `cmake/VerifyMooneyeMbc.cmake` as an adapted copy (categories `mbc2` count 7, `mbc5` count 8, parent-reference SHA checks for the patch, `font-source.c` and builder pin).
   - RESOLVED: adapted copy `cmake/VerifyMooneyeMbc.cmake` (Plan 08-06).

6. **Manifest-versus-compiled PC agreement test (D-26):** `test_runner.c` already includes `main.c`, so a C test can read `mbc_cases[]`; it then needs a tiny purpose-built extractor for `"result_pc"` strings in the sibling manifest (safe because the manifest is SHA-pinned). The alternative is a CMake regex over the `main.c` table text. Either satisfies D-26; pick one and keep the table one-row-per-line.
   - RESOLVED: CMake regex in `VerifyMooneyeMbc.cmake` pc-table mode with a tamper control (Plan 08-06).

7. **Whether `fixtures/mbc5-banking` is installed:** default not installed (D-33), leaving the D-32 allowed-directory list at `tracer`, `visible-demo`, `mbc1-continuation`.
   - RESOLVED: not installed; allowed directories stay `tracer`, `visible-demo`, `mbc1-continuation` (Plans 08-07, 08-08).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | CTest driving standalone C executables with a local `REQUIRE(x)` macro (no unit framework), CMake `-P` scripts, and `expect_exit.cmake` for exact-exit negative controls |
| Config file | `tests/CMakeLists.txt`, `tests/acceptance/CMakeLists.txt`, `tests/player/CMakeLists.txt`; inventory in `tests/expected-tests.txt` and `tests/player/expected-tests.txt` |
| Quick run command | `cmake --build build && ctest --test-dir build -R '^(cartridge_\|battery_\|loader_\|mbc1_continuation)' --output-on-failure` (runs in seconds) |
| Full suite command | `ctest --test-dir build --output-on-failure --no-tests=error --output-junit ctest.xml && bash .github/scripts/verify-test-inventory.sh build/ctest.xml tests/expected-tests.txt --installed` |

### Phase Requirements to Test Map
Test names for new tests are proposals; the planner may rename them, but each must be appended to `tests/expected-tests.txt` as a `+` line (D-12).

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| V-01 CART-01 | Seam plan touches only `gabbaboy.c` + `.planning/` | repo check | `test -z "$(git diff --name-only main...HEAD -- tests fixtures cmake .github CMakeLists.txt)"`; fails when non-empty | script in plan verification |
| V-02 CART-01 | Existing MBC1/loader/battery suites unchanged | ctest | `ctest --test-dir build -R '^(cartridge_\|battery_\|loader_)'` (fails on any regression) | yes |
| V-03 CART-01 | Continuation fixture + DMG baseline byte-identical | ctest | `ctest --test-dir build -R '^(mbc1_continuation_fixture_digest\|dmg_baseline)$'`; `bash tests/scripts/verify-dmg-baseline.sh` prints `baseline status=pass` | yes |
| V-04 CART-01 | `cartridge_type == 0x03u` gone; JOYP anchor still unique | grep | `! git grep -n 'cartridge_type == 0x03u' -- src` and `test "$(grep -c 'joypad_select & 0x20u) == 0' src/core/gabbaboy.c)" = 1`; configure also hard-fails on a non-unique anchor | yes |
| V-05 CART-01 | Old-vs-new loader and MBC1 read differential, zero differences | one-off harness (not committed) | build `gabbaboy.c` at `5673bed` and at the seam commit into two executables, run the 86,016-cell grid plus seeded MBC1 write/read sequences incl. a >=512 KiB MBC1M-candidate image, `diff` the output; record count and digest in the plan verification section | Wave 0 (scratch harness) |
| V-06 CART-01 | `measure_core` digest unchanged; speed advisory | run | `build/measure_core --no-trace fixtures/tracer/tracer.gb` shows `correctness_digest_fnv1a64=4c7a57ff3d50d228`; hard gate on the digest only | yes |
| V-07 CART-02 | Header rows `$19-$1E`: ROM codes `$00-$08`, RAM codes, rejections | ctest | `ctest -R '^mbc5_header_matrix$'` (new `tests/test_mbc5.c`) | Wave 0 |
| V-08 CART-02 | 9-bit banking, order independence, masking, bank 0 at `$4000`, `$0000` always bank 0 | ctest | `ctest -R '^mbc5_rom_banking$'` | Wave 0 |
| V-09 CART-02 | RAM enable pins (`$0A,$1A,$FA` on; `$00,$0B,$A0` off), RAM bank mask, `$FF` when disabled/absent, `$6000-$7FFF` ignored | ctest | `ctest -R '^mbc5_ram_'` | Wave 0 |
| V-10 CART-02 | Rumble state, counter saturation, reset/load semantics, `GBB_NO_RUMBLE`, NULL args, outputs unchanged on error | ctest | `ctest -R '^mbc5_rumble_'` | Wave 0 |
| V-11 CART-02 | 8 MiB bound: exactly 8 MiB loads, 8 MiB+1 and `SIZE_MAX` return `ROM_TOO_LARGE`, MBC1 at 2 MiB+1 still `ROM_TOO_LARGE` with state intact | ctest | `ctest -R '^(mbc5_rom_bound\|loader_oversized\|loader_boundary_fuzz)$'` | Wave 0 + existing |
| V-12 CART-02 | `$143=$C0` MBC5 image loads on DMG-CPU-B | ctest | `ctest -R '^mbc5_cgb_flag_ignored$'` | Wave 0 |
| V-13 CART-02 | Cross-mapper negative control (same write sequence selects different banks on MBC1/MBC5/MBC2) | ctest | `ctest -R '^mbc5_cross_mapper_control$'` | Wave 0 |
| V-14 CART-02 | Mooneye mbc5 8/8 | ctest | `ctest -R '^mooneye_mbc_case_mbc5_'` and the suite line `mbc2=7/7 mbc5=8/8`, eligible = executed = 15 | Wave 0 |
| V-15 CART-02 | Original fixture: bank 0 in upper window, both write orders, RAM bank 15 non-rumble 128 KiB, rumble masking on `$1E` | ctest | `ctest -R '^(mbc5_banking_fixture_digest\|mbc5_banking_guest)$'` | Wave 0 |
| V-16 CART-02 | Bank `$1FF` via in-memory 8 MiB inflation | ctest | `ctest -R '^mbc5_bank_1ff$'` | Wave 0 |
| V-17 CART-03 | Header rows `$05/$06`: RAM code `$00` only, ROM `$00-$03`, 512-byte RAM from row | ctest | `ctest -R '^mbc2_header_matrix$'` | Wave 0 |
| V-18 CART-03 | Bit-8 decode table over address bits, `$00` to `$2000` leaves bank, `$00` to `$2100` selects bank 1, `$4000-$7FFF` no effect, 0-to-1 then mask | ctest | `ctest -R '^mbc2_register_decode$'` | Wave 0 |
| V-19 CART-03 | RAM echo over all 8192 window addresses, `$A5` reads `$F5`, disabled reads `$FF`, writes ignored | ctest | `ctest -R '^mbc2_ram_echo$'` | Wave 0 |
| V-20 CART-03 | Battery image: exactly 512 bytes, all upper nibbles `$F`; `$05` returns `GBB_NO_BATTERY` on all four calls; import size mismatch, normalisation, generation bump once, unchanged-write no bump, no mutation on error | ctest | `ctest -R '^mbc2_battery_'` | Wave 0 |
| V-21 CART-03 | Two-instance round trip (guest write, copy, import into fresh instance, guest reads back) | ctest | `ctest -R '^mbc2_two_instance_roundtrip$'` | Wave 0 |
| V-22 CART-03 | Mooneye mbc2 7/7 | ctest | `ctest -R '^mooneye_mbc_case_mbc2_'` | Wave 0 |
| V-23 SC-4 | Sibling manifest digests, sizes, rights, parent-pin references, PC table agreement | ctest | `ctest -R '^mooneye_mbc_(fixture_digest\|eligible_inventory\|pc_table)$'` | Wave 0 |
| V-24 SC-4 | Negative controls: type-byte mutation not a pass; unknown manifest digest fails closed; ninth-bit mutant fails `rom_64Mb` and passes `rom_32Mb` | ctest | `ctest -R '^mooneye_mbc_(type_mutation\|unknown_manifest\|ninth_bit_mutant_)'` | Wave 0 |
| V-25 SC-4 | `rom_64Mb` and siblings absent from install tree and extracted package; allowed fixture directories exactly `tracer`, `visible-demo`, `mbc1-continuation`; empty tree fails; planted ROM fails | ctest | `ctest -R '^(mooneye_mbc_not_installed\|mooneye_mbc_not_installed_selftest\|preview_package_smoke)$'` | Wave 0 |
| V-26 | Player: `$06/$1B/$1E` run without persistence and create no files | ctest (player build) | `ctest --test-dir build-player -R '^(player_session_battery_unsupported\|player_limitations)$'` | Wave 0 |
| V-27 | Inventory: only `+` lines in `tests/expected-tests.txt` | repo check | `git diff -U0 main...HEAD -- tests/expected-tests.txt \| grep -E '^-[^-]'` prints nothing | script in plan verification |

Note: inside the table above a literal `|` regex alternation is written `\|` only to keep the Markdown table intact; use a plain `|` in the actual `ctest -R` and `grep -E` commands. Each "fails when" direction: V-01 fails on any non-empty path list; V-02/V-03/V-06 fail on any changed result or digest; V-04 fails on a surviving literal or a non-unique anchor (configure error); V-05 fails on any non-zero diff; V-07..V-22 fail on any wrong return code, bank, byte, counter or generation; V-24 and V-25 are negative controls and fail if the mutated or planted input is accepted.

### Sampling Rate
- **Per task commit:** the quick run command (MBC1 and loader suites) plus the new test names the task touched.
- **Per wave merge:** the full suite command, `bash tests/scripts/verify-dmg-baseline.sh`, and the ASan preset (`cmake --preset phase1-asan` then `ctest --preset phase1-asan`).
- **Phase gate:** exact-head CI green on native-linux, native-macos, native-windows, linux-asan-ubsan, cmake-floor-3.25.3 and the macOS player lane, with the hosted `fixture-repro` sibling leg matching the committed digests, before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `tests/test_mbc5.c`, `tests/test_mbc2.c` plus their `add_executable`/`add_test` blocks and `expected-tests.txt` lines.
- [ ] `fixtures/mbc5-banking/*` and `tests/scripts/reproduce-mbc5-banking.sh`.
- [ ] `fixtures/mooneye-mbc/*`, `tests/scripts/reproduce-mooneye-mbc.sh`, `cmake/VerifyMooneyeMbc.cmake`.
- [ ] Runner `suite_def` and per-case `size_bytes`; budgets measured.
- [ ] `cmake/ScanForbiddenFixtures.cmake` (or Python) and the `PreviewPackageSmoke.cmake` hook.
- [ ] Scratch old-vs-new differential harness (kept out of the repository; result digest recorded in the seam plan verification).
- [ ] Ninth-bit mutant build targets in `tests/acceptance/CMakeLists.txt` (or a sibling include).
- [ ] No new framework install is needed.

## Security Domain

`security_enforcement` is absent in `.planning/config.json`, so this section applies. Level: ASVS L1, block on high.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | - (no identity surface) |
| V3 Session Management | no | - |
| V4 Access Control | no | - |
| V5 Input Validation | yes | Bounded, table-driven header validation before any allocation; exact-size battery import; digest-pinned manifests; per-case `size_bytes` bound in the runner |
| V6 Cryptography | limited | SHA-256 used only as an integrity digest via existing `src/accept/sha256.c` / `file(SHA256)`; never hand-roll |
| V8 Data Protection | limited | Player must not create save/lock/recovery files for unsupported battery types (D-22); no personal paths in committed artifacts |
| V10 Malicious Code / V14 Supply chain and configuration | yes | Tools pinned by revision, tree and archive digest; hosted reproduction; no new dependencies or Actions |
| V12 Files and Resources | yes | Fixed ceilings (8 MiB ROM, 128 KiB RAM), `locate_rom` path handling, install allowlist plus scan, `.gitattributes` binary treatment |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Hostile ROM header (type/size/RAM code lies) driving an out-of-bounds read or an oversized allocation | Tampering, DoS | Row lookup, `rom_size_code > row.max` before the shift, declared-length equality, RAM size from the row (MBC2) or from a closed code list; allocation only after all checks; maximum allocation 8 MiB + 128 KiB |
| 32-bit `size_t` overflow in `bank * 0x4000 + offset` or `32768u << code` | Tampering | Bank masked by `rom_banks - 1`; code range-checked first; keep the `offset < m->rom_size` guard in the read path |
| Out-of-range cartridge RAM index (`bank * 0x2000 + addr`, MBC2 `addr & 0x1FF`) | Tampering | Bank masked by `ram_banks - 1`; MBC2 index masked to 9 bits; MBC5 8 KiB image has a single bank |
| Malformed save import: wrong length, non-canonical MBC2 nibbles, partial mutation | Tampering | Exact length (512 for MBC2) before touching RAM; normalise and compare first; all-or-nothing commit; generation bumps once |
| Counter overflow (`rumble_changes`, `battery_generation`) | Tampering | Saturate at `UINT64_MAX` |
| Fixture admission: substituted or unlicensed ROM | Spoofing, Tampering | Per-ROM SHA-256 and size in a SHA-pinned manifest, parent patch/font/builder referenced by digest, MIT `LICENSE.txt` copied, third-party notices row, hosted rebuild |
| Manifest path traversal (`rom` field) | Tampering | Compiled table supplies names and sizes; verifier rejects `/`, `\\` and `..` as `VerifyMooneye.cmake` does |
| 4/8 MiB third-party ROMs leaking into install or package artifacts | Information disclosure (redistribution scope), DoS (package bloat) | Install allowlist plus digest and path scan on the install tree and the extracted package; planted-payload self-test; directory list exact |
| Personal paths or machine identifiers in fixtures (`.sym`, `.lnk`, `.log`) | Information disclosure | Commit only ROMs, manifest and notices; verify no `/Users/` or `/private/tmp/` strings in committed text |
| Unknown or unsupported suite manifest accepted by the runner | Spoofing | Selection by exact manifest SHA-256; unknown digest returns `invalid-manifest` (fail closed) |
| Silent data loss: player discarding progress for newly accepted battery types | Repudiation (user data) | `battery_unsupported` status and stderr warning; no file created; `battery_backed` stays false |

### Threat-model input for the planner's `<threat_model>` blocks (trust boundaries)

1. **ROM header parse** (`validate_header`, untrusted bytes from a host): threats T-8-01 oversize/overflow, T-8-02 header lies per cartridge type, T-8-03 partial mutation on failure. Mitigations: see rows above. Severity high if any path reads or allocates before validation completes.
2. **Mapper register and RAM window** (guest-controlled writes): T-8-04 bank index out of range, T-8-05 MBC2 index/echo, T-8-06 rumble bit confusing RAM bank. Mitigation: masks plus tests V-08/V-09/V-18/V-19. High if an unmasked index is possible.
3. **Save import** (`gbb_import_battery`, host-supplied bytes): T-8-07 size/normalisation/partial write. High if RAM is modified before full validation.
4. **Fixture admission** (third-party ROMs and tools): T-8-08 provenance/rights, T-8-09 digest drift between Darwin and Linux, T-8-10 path privacy. Medium; block until hosted match recorded.
5. **Install and package artifacts**: T-8-11 forbidden ROM shipped, T-8-12 stale allowlist. High because it is a rights and size boundary; mitigated by V-25.
6. **Runner manifest/oracle**: T-8-13 false pass (type-mutated or wrong-PC ROM), T-8-14 unknown manifest accepted. Medium; mitigated by V-24.
7. **Player data protection**: T-8-15 progress silently dropped, T-8-16 file written for an unsupported cartridge. Medium; mitigated by V-26.

## Sources

### Primary (HIGH confidence)
- Repository files opened this session: `src/core/gabbaboy.c` (lines 30-60, 400-470, 535-545, 675-700, 740-775, 950-980, 1350-1380, 1600-1790, 2300-2311), `include/gabbaboy/gabbaboy.h` (1-80, 125-200), `CMakeLists.txt`, `tests/CMakeLists.txt`, `tests/acceptance/CMakeLists.txt:270-333`, `tests/test_loader.c`, `tests/test_loader_fuzz.c`, `tests/test_cartridge.c`, `tests/test_battery.c`, `tests/test_runner.c`, `tests/measure_core.c`, `src/runner/main.c`, `src/runner/acceptance.h`, `src/player/{session.c,session.h,limitations.h}`, `src/player/main.c` (selected ranges), `cmake/{ExpectedTests,VerifyDmgBaseline,VerifyMooneye,PreviewPackageSmoke}.cmake`, `tests/expect_exit.cmake`, `tests/expect_runner_failure.cmake`, `tests/scripts/{reproduce-mooneye,reproduce-mbc1-continuation,verify-libbet-admission}.*`, `.github/workflows/{ci,fixture-repro,preview}.yml`, `.github/scripts/{verify-test-inventory.sh,create-deterministic-archive.py}`, `fixtures/mooneye/*`, `fixtures/mbc1-continuation/*`, `.gitattributes`, `THIRD_PARTY_NOTICES.md`, `docs/{cartridge-and-saves,native-integration,game-acceptance}.md`, `README.md`, `docs/preview.md`.
- Pinned Mooneye checkout and rebuilt derivatives in the discuss-phase scratchpad (`research-08/mt`, `research-08/out`), verified by recomputation with `python3 -I` scripts under `scratchpad/tools/`.
- Pan Docs MBC5 and MBC2 pages (gbdev.io/pandocs).

### Secondary (MEDIUM confidence)
- Web search confirming Pan Docs' low-nibble RAM-enable statement for MBC5 and the rumble-bit location.

### Tertiary (LOW confidence)
- None used for decisions; gb-ctr MBC5 RAMG wording not fetched (A3).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, all items pinned in repository manifests.
- Architecture and source map: HIGH, line-level reads this session.
- Hardware semantics: MEDIUM, Pan Docs plus Mooneye source; the MBC2 `$F` fill and MBC5 RAM-gate nibble rule rest on D-decisions and Pan Docs, not on a second hardware reference.
- Pitfalls: HIGH for repository-structure pitfalls (verified by reading), MEDIUM for budgets and timing.

**Research date:** 2026-10-11
**Valid until:** 2026-11-10 (stable; revisit if the Mooneye pin, RGBDS pin or CI runner images change)
