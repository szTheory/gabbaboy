---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 07
subsystem: testing
tags: [magentests, mbc3, screen-oracle, install-exclusion]
requires: [09-01, 09-02]
provides:
  - tests/test_magentests.c MagenTests screen oracle with negative control
  - GBB_FORBIDDEN_LABEL parameter in cmake/ScanForbiddenFixtures.cmake
  - seven magentests_ CTests
affects: [09-09]
tech-stack:
  added: []
  patterns: [paired negative control for screen-scraped oracle, digest-based install scan with label]
key-files:
  created:
    - tests/test_magentests.c
  modified:
    - cmake/ScanForbiddenFixtures.cmake
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "Frame budget is 16 frames of 140448 half-dots (past the white frames 1-3); negative control forces [0x149]=0x03 with recomputed header checksum and requires shade 3 on all three ROMs"
  - "GBB_FORBIDDEN_LABEL defaults to mooneye and keeps the mooneye-mbc success line byte-identical; other labels print '<label> absent from scanned tree files=N'"
requirements-completed: [CART-04]
duration: 20 min
completed: 2026-10-11
status: complete
commits: 3
plan_head_before: 3deed152c194cd443d3b598ef17e5141198aa32a
plan_head_after: ebda9341872b35784ccbc5b22102766eaf75ca8b
actuals:
  tokens: 9000
  tasks: 3
  commits: 3
---

# Phase 9 Plan 07: MagenTests Out-of-Bounds SRAM Oracle Summary

MagenTests out-of-bounds SRAM ROMs for MBC1, MBC3 and MBC5 pass a public-API screen oracle (all 23040 pixels at shade 0 after 16 frames) paired with a `$149 = $03` negative control that must show shade 3, and a digest-based install scan proves the ROMs never ship.

## Accomplishments

- Task 1 (tracer, 1334ae3): `test_magentests` on the public API; `magentests_fixture_digest` and `magentests_oob_sram_mbc3` pass on the Plan 09-01 mapper.
- Task 2 (a601b51): `magentests_oob_sram_mbc1`, `_mbc5` and `_negative_control` (all three ROMs with RAM code 0x03 and a recomputed checksum paint shade 3, so a blank or constant frame cannot pass).
- Task 3 (ebda934): `GBB_FORBIDDEN_LABEL` in the scan script; `magentests_not_installed` against the real install tree and `magentests_not_installed_selftest` (renamed ROM caught by digest, token `magentests-installed:`). Existing mooneye scan tests pass unchanged.

## Verification

- Full suite: 336/336 passed; `verify-test-inventory.sh --installed` verified 336 executed cases, none skipped.
- tests/baseline untouched (`git diff --quiet main -- tests/baseline` exits 0); no magentests name in any --observe baseline set.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

Files tests/test_magentests.c and this summary exist; commits 1334ae3, a601b51, ebda934 are on the branch.
