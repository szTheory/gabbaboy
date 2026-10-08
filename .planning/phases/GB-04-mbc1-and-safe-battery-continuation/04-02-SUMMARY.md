---
phase: GB-04-mbc1-and-safe-battery-continuation
plan: 02
subsystem: core-cartridge
tags: [c17, mbc1, bank-mapping, battery-ram, regression]
requires:
  - phase: GB-04-mbc1-and-safe-battery-continuation
    provides: first MBC1 battery path and caller-buffer battery operations
provides:
  - Standard MBC1 ROM/RAM bank mapping and declaration validation
  - Focused 8/32 KiB battery API contract regressions
affects: [mbc1, battery-api, cartridge-loading]

actuals:
  tasks: 2
  commits: 3
key-files:
  created:
    - tests/test_battery.c
  modified:
    - include/gabbaboy/gabbaboy.h
    - src/core/gabbaboy.c
    - tests/test_cartridge.c
    - tests/test_loader.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
requirements-completed: [SAVE-01, SAVE-02]

# Plan 04-02 Summary

## Outcome

The standard MBC1 support envelope now maps ROM and RAM windows for supported cartridge declarations, rejects the recognized alternate-bank MBC1M header pattern, and has focused regressions for mapper behavior and the public battery API contract.

## Commits

1. `3f1821e test(04-02): specify MBC1 bank window mapping`
2. `ed60be1 feat(04-02): map standard MBC1 ROM and RAM banks`
3. `149e6f7 test(04-02): cover battery API safety contract`
4. This summary commit.

## Implementation

- Added support for MBC1 types `$01`, `$02`, and `$03` across declared ROM sizes through 2 MiB, with the documented compatible RAM-size matrix and exact ROM-length validation.
- Implemented low and upper ROM windows, mode-dependent lower-window and RAM-bank behavior, raw low-register zero translation before physical masking, 8 KiB RAM mirroring, 32 KiB RAM banking, RAM-enable gating, and deterministic `$FF` reads when supported MBC1 hardware declares no RAM.
- Added a conservative MBC1M rejection predicate: a matching Nintendo logo, local header checksum, and MBC1 type at bank `$10`. This catches the selected candidate class but can miss multicart patterns outside that predicate and is not a universal classifier.
- Added six named `battery_*` tests for exact 8/32 KiB transfers, canary preservation, invalid arguments and lengths, no-battery cases, reset/replacement lifecycle, and independent instances.
- Kept battery storage instance-owned and caller-buffer based; no dependency was added.

## Test Evidence

- Mapper and loader plan command: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(cartridge_|loader_|bus_)'` — passed, 25/25 selected cases.
- Battery API plan command: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(battery_|instance_lifecycle$|independent_instances$|reset_)'` — passed, 11/11 selected cases.
- `git diff --check` passed.
- Pan Docs, Gekkio's technical reference, and mGBA source were cross-checked for mapper behavior and MBC1M identification. These are documentation/source-model comparisons, not hardware-backed evidence; the selected predicate does not establish detection of every multicart variant.

## Plan Deviations

- The battery API implementation and initial 8 KiB path were completed in Plan 04-01. This plan therefore adds direct contract and lifecycle coverage for the expanded 8/32 KiB path instead of duplicating already-committed implementation. The tests passed against that implementation without requiring a fix.
- The battery task was marked TDD although its implementation preceded this test task. No behavior was reverted to manufacture a red test; the prior plan's implementation was validated directly.

## Requirements and Coverage

- `SAVE-01`: standard MBC1 ROM/RAM mapping and supported declarations are covered by `cartridge_bank_matrix`, `cartridge_ram_banks`, `cartridge_no_ram_reads`, and loader matrix/variant cases.
- `SAVE-02`: exact battery operations, errors, canaries, reset retention, fresh replacement RAM, and instance isolation are covered by the six `battery_*` cases.

## Next

Continue with Plan 04-03, which handles recovery and preservation behavior for invalid player save files.
---
*Phase: GB-04-mbc1-and-safe-battery-continuation*
*Completed: 2026-10-07*

## Self-Check: PASSED

- `tests/test_battery.c` exists, and both task commits are ancestors of the current branch.
- Both plan-level verification commands passed with 25/25 and 11/11 selected cases; `git diff --check` passed.
