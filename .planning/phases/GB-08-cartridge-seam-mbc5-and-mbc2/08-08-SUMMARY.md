---
phase: 08-cartridge-seam-mbc5-and-mbc2
plan: 08
subsystem: testing
tags: [mbc5, fixture, rgbds, ctest, mutation, rumble]
status: complete
requires:
  - phase: 08-cartridge-seam-mbc5-and-mbc2
    provides: 08-03 MBC5 core and gbb_rumble_state, 08-07 hosted rebuild leg and the D-29 finding
provides:
  - fixtures/mbc5-banking original RGBDS 1.0.1 guest with digest, manifest and reproduce script
  - mbc5_banking_guest, mbc5_banking_guest_1b, mbc5_bank_1ff CTests (real CPU and bus path)
  - ninth-bit core mutant against mbc5_bank_1ff with an in-mutant control
  - fixture-repro "Reproduce MBC5 banking fixture bytes" step
affects: [08-09, 08-10, phase-08-verification]
plan_head_before: 391e969f6a7e61d74ff6431abc4f98101ac603dd
plan_head_after: 4a43e37e321e15a2d9bd070fbe1f156989820dea
actuals:
  tokens: 6600
  tasks: 4
  commits: 5
tech-stack:
  added: []
  patterns: ["configure-time exactly-once anchor core mutant targeting an original-fixture case"]
key-files:
  created:
    - fixtures/mbc5-banking/banking.asm
    - fixtures/mbc5-banking/banking.gb
    - fixtures/mbc5-banking/manifest.json
    - fixtures/mbc5-banking/LICENSE.txt
    - tests/scripts/reproduce-mbc5-banking.sh
  modified:
    - tests/test_mbc5.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - .gitattributes
    - .gitignore
    - .github/workflows/fixture-repro.yml
key-decisions:
  - "Harness stamps banks 0x101..0x103 with their low byte on the 8 MiB image so the nine-bit write-order checks stay valid; only C005 discriminates the ninth bit"
  - "Mutant test asserts the specific C005 REQUIRE text (exit 1) so an unrelated failure cannot satisfy it"
requirements-completed: [CART-02]
---

# Phase 8 Plan 08: Original MBC5 banking fixture and ninth-bit mutant Summary

An original 64 KiB MBC5 type $1E guest (RGBDS 1.0.1, byte-reproducible) proves bank 0 in the upper window, both bank-write orders, RAM bank 15 on a non-rumble $1B variant, rumble bit 3 masked from RAM banking with the host-visible line, and bank $1FF on an in-memory 8 MiB image, all through the real CPU and bus; a ninth-bit core mutant is caught by exactly that $1FF case.

## Accomplishments

- `fixtures/mbc5-banking/banking.asm`: WRAM protocol C000 $A5 pass / C001 $EE fail, C002 bank 0 upper window, C003 write orders (including that a high-bit write never clears the low byte and vice versa), C004 RAM banking, C005 bank $1FF (not run unless $0148 = $08).
- Built with RGBDS 1.0.1 taken from the official macOS archive, SHA-256 `2f6f13c6...503645` verified before use. `banking.gb` = 65536 bytes, header $147 $1E, $148 $01, $149 $04, SHA-256 `0b852837522f45fc3486d69d6b406f956d7dcc0f08a0f0ee6e2a2c288cddffef`; source SHA-256 `16bd7c162e5a2e24a8d615ecb684f22a3f3f98d1839bb8b4ccc03a68e2c9bbb6`. `reproduce-mbc5-banking.sh` rebuilds byte-identically (observed `result=byte-identical`).
- Rumble count derivation: the guest's only $4000-$5FFF writes are $00..$07 (bit 3 clear, line off), then $0F (off to on, one transition), then $08 (still on). The test pins on = 1 and changes = 1; no recompute was needed.
- `mbc5_banking_guest_1b` patches $147 to $1B in memory (checksum fixed): C004 passes (bank 15 reached), `gbb_rumble_state` returns GBB_NO_RUMBLE with outputs untouched.
- `mbc5_bank_1ff` inflates to exactly 8 MiB (calloc, freed on every path), patches $148 to $08, stamps $5A at 0x1FF*0x4000+0x1000, fixes the checksum; passes with C002..C005 = $01 and C000 = $A5. Negative control (marker $00) ends with C005 = $FF and C001 = $EE.
- Hosted fixture-repro job: fourth manifest joins the pin cross-check (version, macOS and Linux archive pins) and a new reproduce step reuses the MBC1 environment block. actionlint clean; no new actions. The hosted run is read in Plan 08-09.
- New CTests (6): `mbc5_banking_fixture_digest`, `mbc5_banking_guest`, `mbc5_banking_guest_1b`, `mbc5_bank_1ff`, `mbc5_ninth_bit_mutant_bank_1ff`, `mbc5_ninth_bit_mutant_control_below_100`. Appended only (+ lines); `grep -c '^mbc5_' tests/expected-tests.txt` = 21 (15 from 08-03 plus these 6; the plan's 19 excluded the two mutant tests).

## D-29 ninth-bit mutant (orchestrator amendment)

- **08-07 finding:** the shared upstream Mooneye mbc5 harness loop stops at bank $FF, so `rom_64Mb` never selects banks 256 and above; the ninth-bit mutant passed it (measured by 08-07), and a `return 1u` control mutant failed it. 08-07 therefore did not land the mutant.
- **Landed here** in `tests/CMakeLists.txt`: configure-time anchor `& 1u) << 8` -> `& 0u) << 8` (exactly-once check, FATAL_ERROR otherwise), static `gabbaboy_core_ninth_bit_mutant` library and a separate `test_mbc5_ninth_bit_mutant` executable built from `tests/test_mbc5.c`. Never installed or exported; `src/` unchanged. Generated mutant differs from `src/core/gabbaboy.c` by exactly that one line (diff verified).
- **Measured outcome:** mutant `mbc5_bank_1ff` exits 1 at `tests/test_mbc5.c:932: r[3] == 0x01u` (C005, the $1FF check), while C002..C004 still pass. Mutant control (`mbc5_banking_guest` on the committed 64 KiB image) exits 0. Unmutated `mbc5_bank_1ff` exits 0. Both mutant CTests pass, i.e. the mutant is caught, not accepted.
- `rom_64Mb` remains admitted as the 8 MiB loader and install-policy case only; it is not the ninth-bit discriminator.

## Verification

- `bash tests/scripts/reproduce-mbc5-banking.sh` (RGBDS 1.0.1 on PATH): byte-identical.
- `ctest --test-dir build -R '^mbc5_'`: 19/19 on the pre-mutant head; full local `ctest` (phase1 preset) 319/319 passed; executed set equals `tests/expected-tests.txt` exactly (diff clean, additions only).
- The `phase1-asan` preset refuses to configure on macOS (Linux only, as noted in 08-07). Substitute: `cc -fsanitize=address,undefined` build of `src/core/gabbaboy.c` + `tests/test_mbc5.c`; `mbc5_banking_guest`, `mbc5_banking_guest_1b` and `mbc5_bank_1ff` all exit 0. The hosted linux-asan-ubsan job is read in 08-10.
- Acceptance: `banking.gb` is 65536 bytes with header 1E/01/04; `git check-attr text` reports unset for the ROM; root `CMakeLists.txt` unchanged vs main (not in the install allowlist); the `mooneye-mbc-repro` job is intact; no `uses:` line added.

## Deviations from Plan

**1. [Rule 3 - Blocking] `*.gb` is gitignored repo-wide**
- Found during: Task 1 commit (`git add` refused `banking.gb`; the first commit went through without the ROM)
- Fix: added `!/fixtures/mbc5-banking/banking.gb` to `.gitignore` (same pattern as the other committed fixtures) and committed the ROM in a follow-up commit
- Files modified: `.gitignore`, `fixtures/mbc5-banking/banking.gb`
- Commit: see key commits below

**2. [Plan wording] Test count**
- The plan's "exactly 19 mbc5_ tests" holds before the mutant tests; with the two orchestrator-added mutant tests the count is 21. Not a defect.

**3. [Design note] Harness-stamped banks $101..$103**
- On the 8 MiB image the guest's C003 hi-bit write-order checks select banks $102/$103, which would read zeros. The harness stamps their low bytes (documented in the manifest). C005 remains the only ninth-bit discriminator, confirmed by the mutant run.

**Total deviations:** 1 auto-fixed (Rule 3), 2 notes. **Impact:** none on scope.

## Commits

- 0257b9a feat(08-08): fixture, reproduce script, digest and guest tests
- edd52c1 fix(08-08): gitignore exception and the ROM
- 313db3b test(08-08): 1b variant and bank 1FF registration
- 62ee754 ci(08-08): hosted reproduce step
- 4a43e37 test(08-08): ninth-bit mutant and control

## Known Stubs

None.

## Threat Flags

None. The fixture adds no network, auth or file-access surface; the 8 MiB buffer is a single freed allocation (ASan-equivalent run clean).

## Self-Check: PASSED

Files verified present: banking.asm, banking.gb, manifest.json, LICENSE.txt, reproduce-mbc5-banking.sh. Commits verified as ancestors of HEAD: 0257b9a, 313db3b, 62ee754, 4a43e37 and edd52c1.
