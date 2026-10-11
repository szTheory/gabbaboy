---
phase: GB-08-cartridge-seam-mbc5-and-mbc2
verified: 2026-10-11T00:00:00Z
status: passed
score: 4/4 must-haves verified
covered_files:
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-01-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-01-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-02-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-02-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-03-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-03-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-04-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-04-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-05-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-05-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-06-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-06-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-07-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-07-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-08-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-08-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-09-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-09-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-10-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-10-SUMMARY.md"
  - "fixtures/mbc5-banking/banking.gb"
  - "include/gabbaboy/gabbaboy.h"
  - "src/core/gabbaboy.c"
  - "tests/test_mbc2.c"
  - "tests/test_mbc5.c"
covered_digest: "v3:sha256:db60c009a7d5bb408e512e528de836722ab767a285a711e79e2f93ca69192420"
behavior_unverified: 0
overrides_applied: 0
---

# Phase 8: Cartridge Seam, MBC5 and MBC2 Verification Report

**Phase Goal:** Cartridge behavior lives behind one type-table mapper seam with no observable DMG change, and callers can run MBC5 and MBC2 cartridges.
**Verified:** 2026-10-11 at head 5a30f7f
**Status:** passed
**Re-verification:** No, initial verification

## Goal Achievement

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | MBC1 behind the type-table seam; MBC1 suite, battery continuation fixture and Phase 7 DMG baseline byte-identical | VERIFIED | `cart_type_table[]` and `switch (m->cart.kind)` dispatch in `src/core/gabbaboy.c` lines 44-152, 760-960. I re-ran in `build/`: ctest 320/320 passed, `verify-test-inventory.sh ... --installed` "Verified 320 executed CTest cases; none skipped", `verify-dmg-baseline.sh` prints `baseline changes=ok rows=0`, `baseline status=pass`. The old-vs-new differential harness (`differential/run-differential.sh`, cells=83328 differences=0) was not rerun by me; I accept it as a recorded result at 96d5eec. Only 5a30f7f cmake scan changes and docs came after (see CI note). |
| 2 | MBC5 `$19-$1E`: 9-bit banking incl. bank 0 in the switchable window, ROM to 8 MiB, RAM to 128 KiB, rumble bit masked and host-readable, Mooneye mbc5 8/8 | VERIFIED | Table rows 0x19-0x1E (CART_MBC5, ceiling `GBB_MAX_ROM_SIZE` 8 MiB, RAM rule up to 128 KiB). `mbc5_rom_bank` composes `(hi&1)<<8 | lo` with no 0-to-1 remap. The rumble write path masks the RAM bank to `value & 0x07` and exposes the line through `gbb_rumble_state` (`GBB_NO_RUMBLE` when absent). `mooneye_mbc_required_suite` re-run: `suite categories mbc2=7/7 mbc5=8/8`, all with `status=pass`, `eligible=15 executed=15`. Original tests `mbc5_rom_banking`, `mbc5_ram_banking`, `mbc5_rumble_*`, `mbc5_banking_guest`, `mbc5_bank_1ff` pass. |
| 3 | MBC2 `$05/$06`: bit-8 register decode, 512x4-bit RAM echoed through A000-BFFF with upper nibbles as 1s, 512-byte battery image, Mooneye mbc2 7/7 | VERIFIED | Write path `(address & 0x0100)==0` selects RAM enable, else ROM bank. RAM read `cartridge_ram[address & 0x1FF]`, stored canonical `0xF0 | nibble`. Table rows 0x05/0x06 with `MBC2_RAM_BYTES` 512. Mooneye mbc2=7/7 as above. `tests/test_mbc2.c` runs under ctest. |
| 4 | Original fixtures for MBC5 bank $1FF, bank 0 in upper window and rumble masking pass; 8 MiB `rom_64Mb` kept out of install and package | VERIFIED | `fixtures/mbc5-banking/banking.gb` with tests `mbc5_banking_guest`, `mbc5_banking_guest_1b`, `mbc5_bank_1ff`, and mutants `mbc5_ninth_bit_mutant_bank_1ff` and `..._control_below_100` all pass. I ran `cmake --install` into a scratch prefix: the only `.gb` files installed are tracer, visible-demo and mbc1-continuation; nothing from `mooneye-mbc` and no `rom_64Mb`. Tests `mooneye_mbc_not_installed`, `_selftest`, `_link_selftest`, `_empty`, `libbet_not_installed` pass. |

**Score:** 4/4 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `src/core/gabbaboy.c` mapper section | VERIFIED | Substantive and wired into read8/write8, loader, reset, battery export/import |
| `include/gabbaboy/gabbaboy.h` | VERIFIED | `gbb_rumble_state`, `GBB_NO_RUMBLE`, type-aware `GBB_ROM_TOO_LARGE` documented |
| `tests/test_mbc2.c`, `tests/test_mbc5.c`, `tests/test_mbc5_internal.c` | VERIFIED | Registered in ctest and in `tests/expected-tests.txt` (inventory check passes) |
| `fixtures/mbc5-banking/`, `fixtures/mooneye-mbc/` | VERIFIED | Present with LICENSE, manifest and SOURCES/ELIGIBILITY; digests checked by `mooneye_mbc_*` tests |
| `cmake/VerifyMooneyeMbc.cmake`, `cmake/ScanForbiddenFixtures.cmake` | VERIFIED | Exercised by 27 `mooneye_mbc*` tests passing |
| Player integration (`src/player/*`) | VERIFIED | Player suite and test_session additions covered by the 320-test run |

### Key Link Verification

| From | To | Status | Details |
|------|----|--------|---------|
| Loader | `cart_type_table` row lookup | WIRED | `cart_row_for_type` used at load; `cart.kind`, battery, rumble set from row (lines ~1850-1950) |
| bus read/write | mapper dispatch | WIRED | `switch (m->cart.kind)` in ROM, RAM read and write paths |
| Core | host rumble | WIRED | `gbb_rumble_state` reads `cart.rumble_on` and `rumble_changes`, reset on load |
| Runner | Mooneye multi-suite | WIRED | `mooneye_mbc_required_suite` executes 15 of 15 cases |

### Behavioral Spot-Checks and Probe Execution

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full suite | `ctest` in `build/` | 320/320 passed | PASS |
| Test inventory | `verify-test-inventory.sh build/ctest.xml tests/expected-tests.txt --installed` | 320 executed, none skipped | PASS |
| DMG baseline | `bash tests/scripts/verify-dmg-baseline.sh` | `baseline status=pass`, changes rows=0 | PASS |
| Mooneye mbc | `ctest -R mooneye_mbc_required_suite -V` | mbc2=7/7, mbc5=8/8 | PASS |
| Install exclusion | `cmake --install` to scratch prefix, find `*.gb` | no mooneye-mbc or 64Mb files | PASS |

### Data-Flow Trace (Level 4)

Not applicable beyond the core: no dynamic UI data. Battery data flows from mapper writes to `battery_generation` and the exported image (verified by MBC2/MBC5 battery tests in the passing suite).

### Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
|-------------|--------------|--------|----------|
| CART-01 | 08-01, 08-09, 08-10 | SATISFIED | Truth 1; REQUIREMENTS.md marks Complete |
| CART-02 | 08-03, 08-04, 08-05, 08-06, 08-07, 08-08, 08-09, 08-10 | SATISFIED | Truths 2 and 4 |
| CART-03 | 08-02, 08-04, 08-05, 08-06, 08-07, 08-09, 08-10 | SATISFIED | Truth 3 |

All three IDs appear in the PLAN frontmatter and in REQUIREMENTS.md (lines 21-23, traceability rows 88-90 mapped to Phase 8). No orphaned Phase 8 requirements: CART-04..06 are mapped to Phase 9.

### Anti-Patterns Found

None blocking. I found no TBD/FIXME/XXX markers in the mapper section I read. WR-02 from code review is deferred to Phase 9 per 08-REVIEW-DISPOSITION.md (it is outside this phase's goal); IN-02 and IN-03 were skipped as informational.

### Recorded Limitations (not gaps)

- Upstream Mooneye `rom_64Mb` never selects banks >= 256 (D-29 amendment / D-062). The ninth-bit behavior is proven by the original `mbc5_bank_1ff` fixture test and the two mutant tests, which satisfies SC 4. The 08-07 SUMMARY "partial" status reflects only this.
- The 08-04 player status line has no automated UI test (the session-level behavior is tested in `test_session.c`). This is a presentation limit, not a goal truth.
- The `phase1-asan` preset is Linux-only; the sanitizer evidence is the hosted `linux-asan-ubsan` CI job.
- Differential run and CI at 96d5eec were taken from the orchestrator's record, not rerun by me.
- CI for the current head 5a30f7f is PENDING at time of verification; the orchestrator will confirm. The commits after 96d5eec are a cmake forbidden-fixture scan fix (follow file symlinks), its self-test, and docs. Their local tests pass.

### Human Verification Required

None. No perceptual, hardware or credential limitation applies to this phase's goal.

### Gaps Summary

No gaps. The mapper seam, MBC2 and MBC5 are implemented and wired in `src/core/gabbaboy.c`, and the evidence I re-ran locally agrees with the claims. The remaining item is the exact-head CI result for 5a30f7f, which should be green before the PR is merged.

---

_Verified: 2026-10-11_
_Verifier: Claude (gsd-verifier)_
