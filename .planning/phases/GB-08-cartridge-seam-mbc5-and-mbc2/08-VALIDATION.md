---
phase: "8"
slug: "cartridge-seam-mbc5-and-mbc2"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-11"
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `08-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | CTest over in-repo C test executables (`REQUIRE`), `cmake -P` scripts, `expect_exit.cmake` exact-exit controls; no new dependency |
| **Config file** | `tests/CMakeLists.txt`, `tests/acceptance/CMakeLists.txt`, `tests/player/CMakeLists.txt`; inventories `tests/expected-tests.txt`, `tests/player/expected-tests.txt` |
| **Quick run command** | `cmake --build build && ctest --test-dir build -R '^(cartridge_|battery_|loader_|mbc1_continuation|mbc5_|mbc2_)' --output-on-failure` |
| **Full suite command** | `ctest --test-dir build --output-on-failure --no-tests=error --output-junit ctest.xml && bash .github/scripts/verify-test-inventory.sh build/ctest.xml tests/expected-tests.txt --installed` |
| **Estimated runtime** | quick: seconds; full: several minutes (Debug), longer under ASan |

---

## Sampling Rate

- **After every task commit:** quick run command plus the new test names the task touched
- **After every plan wave:** full suite, `bash tests/scripts/verify-dmg-baseline.sh`, and the ASan preset
- **Before `/gsd-verify-work`:** exact-head CI green on all required jobs, including the hosted fixture-repro sibling leg
- **Max feedback latency:** ~60 seconds for the quick command

---

## Per-Task Verification Map

Requirement-level checks V-01..V-27 from RESEARCH; plan and task IDs are bound by the planner in each PLAN.md `<verify>` block.

| Check | Plan | Wave | Requirement | Threat Ref | Behavior | Test Type | Automated Command | File Exists | Status |
|-------|------|------|-------------|------------|----------|-----------|-------------------|-------------|--------|
| V-01 | planner-assigned | — | CART-01 | see RESEARCH threat input | Seam plan touches only `gabbaboy.c` + `.planning/` | repo check | `test -z "$(git diff --name-only main...HEAD -- tests fixtures cmake .github CMakeLists.txt)"`; fails when non-empty | ❌ W0 | ⬜ pending |
| V-02 | planner-assigned | — | CART-01 | see RESEARCH threat input | Existing MBC1/loader/battery suites unchanged | ctest | `ctest --test-dir build -R '^(cartridge_\ | ❌ W0 | ⬜ pending |
| V-03 | planner-assigned | — | CART-01 | see RESEARCH threat input | Continuation fixture + DMG baseline byte-identical | ctest | `ctest --test-dir build -R '^(mbc1_continuation_fixture_digest\ | ❌ W0 | ⬜ pending |
| V-04 | planner-assigned | — | CART-01 | see RESEARCH threat input | `cartridge_type == 0x03u` gone; JOYP anchor still unique | grep | `! git grep -n 'cartridge_type == 0x03u' -- src` and `test "$(grep -c 'joypad_select & 0x20u) == 0' src/core/gabbaboy.c)" = 1`; configure also hard-fails on a non-unique anchor | ✅ | ⬜ pending |
| V-05 | planner-assigned | — | CART-01 | see RESEARCH threat input | Old-vs-new loader and MBC1 read differential, zero differences | one-off harness (not committed) | build `gabbaboy.c` at `5673bed` and at the seam commit into two executables, run the 86,016-cell grid plus seeded MBC1 write/read sequences incl. a >=512 KiB MBC1M-candidate image, `diff` the output; record count and digest in the plan verification section | ❌ W0 | ⬜ pending |
| V-06 | planner-assigned | — | CART-01 | see RESEARCH threat input | `measure_core` digest unchanged; speed advisory | run | `build/measure_core --no-trace fixtures/tracer/tracer.gb` shows `correctness_digest_fnv1a64=4c7a57ff3d50d228`; hard gate on the digest only | ✅ | ⬜ pending |
| V-07 | planner-assigned | — | CART-02 | see RESEARCH threat input | Header rows `$19-$1E`: ROM codes `$00-$08`, RAM codes, rejections | ctest | `ctest -R '^mbc5_header_matrix$'` (new `tests/test_mbc5.c`) | ❌ W0 | ⬜ pending |
| V-08 | planner-assigned | — | CART-02 | see RESEARCH threat input | 9-bit banking, order independence, masking, bank 0 at `$4000`, `$0000` always bank 0 | ctest | `ctest -R '^mbc5_rom_banking$'` | ❌ W0 | ⬜ pending |
| V-09 | planner-assigned | — | CART-02 | see RESEARCH threat input | RAM enable pins (`$0A,$1A,$FA` on; `$00,$0B,$A0` off), RAM bank mask, `$FF` when disabled/absent, `$6000-$7FFF` ignored | ctest | `ctest -R '^mbc5_ram_'` | ❌ W0 | ⬜ pending |
| V-10 | planner-assigned | — | CART-02 | see RESEARCH threat input | Rumble state, counter saturation, reset/load semantics, `GBB_NO_RUMBLE`, NULL args, outputs unchanged on error | ctest | `ctest -R '^mbc5_rumble_'` | ❌ W0 | ⬜ pending |
| V-11 | planner-assigned | — | CART-02 | see RESEARCH threat input | 8 MiB bound: exactly 8 MiB loads, 8 MiB+1 and `SIZE_MAX` return `ROM_TOO_LARGE`, MBC1 at 2 MiB+1 still `ROM_TOO_LARGE` with state intact | ctest | `ctest -R '^(mbc5_rom_bound\ | ❌ W0 | ⬜ pending |
| V-12 | planner-assigned | — | CART-02 | see RESEARCH threat input | `$143=$C0` MBC5 image loads on DMG-CPU-B | ctest | `ctest -R '^mbc5_cgb_flag_ignored$'` | ❌ W0 | ⬜ pending |
| V-13 | planner-assigned | — | CART-02 | see RESEARCH threat input | Cross-mapper negative control (same write sequence selects different banks on MBC1/MBC5/MBC2) | ctest | `ctest -R '^mbc5_cross_mapper_control$'` | ❌ W0 | ⬜ pending |
| V-14 | planner-assigned | — | CART-02 | see RESEARCH threat input | Mooneye mbc5 8/8 | ctest | `ctest -R '^mooneye_mbc_case_mbc5_'` and the suite line `mbc2=7/7 mbc5=8/8`, eligible = executed = 15 | ❌ W0 | ⬜ pending |
| V-15 | planner-assigned | — | CART-02 | see RESEARCH threat input | Original fixture: bank 0 in upper window, both write orders, RAM bank 15 non-rumble 128 KiB, rumble masking on `$1E` | ctest | `ctest -R '^(mbc5_banking_fixture_digest\ | ❌ W0 | ⬜ pending |
| V-16 | planner-assigned | — | CART-02 | see RESEARCH threat input | Bank `$1FF` via in-memory 8 MiB inflation | ctest | `ctest -R '^mbc5_bank_1ff$'` | ❌ W0 | ⬜ pending |
| V-17 | planner-assigned | — | CART-03 | see RESEARCH threat input | Header rows `$05/$06`: RAM code `$00` only, ROM `$00-$03`, 512-byte RAM from row | ctest | `ctest -R '^mbc2_header_matrix$'` | ❌ W0 | ⬜ pending |
| V-18 | planner-assigned | — | CART-03 | see RESEARCH threat input | Bit-8 decode table over address bits, `$00` to `$2000` leaves bank, `$00` to `$2100` selects bank 1, `$4000-$7FFF` no effect, 0-to-1 then mask | ctest | `ctest -R '^mbc2_register_decode$'` | ❌ W0 | ⬜ pending |
| V-19 | planner-assigned | — | CART-03 | see RESEARCH threat input | RAM echo over all 8192 window addresses, `$A5` reads `$F5`, disabled reads `$FF`, writes ignored | ctest | `ctest -R '^mbc2_ram_echo$'` | ❌ W0 | ⬜ pending |
| V-20 | planner-assigned | — | CART-03 | see RESEARCH threat input | Battery image: exactly 512 bytes, all upper nibbles `$F`; `$05` returns `GBB_NO_BATTERY` on all four calls; import size mismatch, normalisation, generation bump once, unchanged-write no bump, no mutation on error | ctest | `ctest -R '^mbc2_battery_'` | ❌ W0 | ⬜ pending |
| V-21 | planner-assigned | — | CART-03 | see RESEARCH threat input | Two-instance round trip (guest write, copy, import into fresh instance, guest reads back) | ctest | `ctest -R '^mbc2_two_instance_roundtrip$'` | ❌ W0 | ⬜ pending |
| V-22 | planner-assigned | — | CART-03 | see RESEARCH threat input | Mooneye mbc2 7/7 | ctest | `ctest -R '^mooneye_mbc_case_mbc2_'` | ❌ W0 | ⬜ pending |
| V-23 | planner-assigned | — | SC-4 | see RESEARCH threat input | Sibling manifest digests, sizes, rights, parent-pin references, PC table agreement | ctest | `ctest -R '^mooneye_mbc_(fixture_digest\ | ❌ W0 | ⬜ pending |
| V-24 | planner-assigned | — | SC-4 | see RESEARCH threat input | Negative controls: type-byte mutation not a pass; unknown manifest digest fails closed; ninth-bit mutant fails `rom_64Mb` and passes `rom_32Mb` | ctest | `ctest -R '^mooneye_mbc_(type_mutation\ | ❌ W0 | ⬜ pending |
| V-25 | planner-assigned | — | SC-4 | see RESEARCH threat input | `rom_64Mb` and siblings absent from install tree and extracted package; allowed fixture directories exactly `tracer`, `visible-demo`, `mbc1-continuation`; empty tree fails; planted ROM fails | ctest | `ctest -R '^(mooneye_mbc_not_installed\ | ❌ W0 | ⬜ pending |
| V-26 | planner-assigned | — | — | see RESEARCH threat input | Player: `$06/$1B/$1E` run without persistence and create no files | ctest (player build) | `ctest --test-dir build-player -R '^(player_session_battery_unsupported\ | ❌ W0 | ⬜ pending |
| V-27 | planner-assigned | — | — | see RESEARCH threat input | Inventory: only `+` lines in `tests/expected-tests.txt` | repo check | `git diff -U0 main...HEAD -- tests/expected-tests.txt \ | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky.* Inside the table `\|` stands for a regex `|`.

---

## Wave 0 Requirements

- [ ] `tests/test_mbc5.c`, `tests/test_mbc2.c` with `add_test` blocks and `+` lines in `tests/expected-tests.txt`
- [ ] `fixtures/mbc5-banking/*` and its reproduction script
- [ ] `fixtures/mooneye-mbc/*`, reproduction script, sibling verifier
- [ ] Runner `suite_def` and per-case sizes; budgets measured at admission
- [ ] Forbidden-fixture scan for install tree and extracted package, with planted-payload self-test
- [ ] Scratch old-vs-new differential harness (not committed; result recorded in the seam plan)
- [ ] Ninth-bit mutant build targets

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
