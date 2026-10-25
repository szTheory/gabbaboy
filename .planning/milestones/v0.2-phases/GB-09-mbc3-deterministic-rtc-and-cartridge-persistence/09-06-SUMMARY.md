---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 06
subsystem: fixtures
tags: [mbc2, rgbds, continuation-fixture]
requires: []
provides:
  - fixtures/mbc2-continuation original MBC2 nibble continuation guest
  - tests/scripts/reproduce-mbc2-continuation.sh
affects: [09-10, 09-12, 09-16]
tech-stack:
  added: []
  patterns: [mbc1-continuation fixture style, pinned RGBDS 1.0.1 byte-identical rebuild]
key-files:
  created:
    - fixtures/mbc2-continuation/continuation.asm
    - fixtures/mbc2-continuation/continuation.gb
    - fixtures/mbc2-continuation/manifest.json
    - fixtures/mbc2-continuation/LICENSE.txt
    - tests/scripts/reproduce-mbc2-continuation.sh
  modified: []
key-decisions:
  - "Pattern identity check on cells 0-2 (reads $F3 $FA $F1) selects store vs resume; fresh RAM never reads that, so a missing save is observable as C000=$01"
requirements-completed: [CART-06]
coverage:
  - id: D1
    description: "The project-authored MBC2 continuation guest rebuilds byte-identically with pinned RGBDS 1.0.1"
    verification:
      - kind: other
        ref: "Fresh Phase 15.1-11 run with the manifest-pinned RGBDS 1.0.1 archive: tests/scripts/reproduce-mbc2-continuation.sh; result=byte-identical, ROM SHA-256 314e05b419c07f1823983932d4e70ce57f0c366f44ec9ee86baf322f8dad50aa"
        status: pass
    human_judgment: false
duration: 12 min
completed: 2026-10-11
status: complete
commits: 2
plan_head_before: 05be80788ba20b0b9c4b944c09870156fefc4f6b
plan_head_after: b0b51a7a2733ba28ea454aadbcf8f38dc4b2463e
actuals:
  tokens: 6000
  tasks: 2
  commits: 2
---

# Phase 9 Plan 06: MBC2 Continuation Guest Summary

Original MIT MBC2+battery guest (type $06, 32 KiB ROM) that stores a 512-nibble pattern (i*7+3)&$0F on a store run and verifies all cells (upper nibble reads $F) on a resume run, rebuilt byte-identically with RGBDS 1.0.1.

## Accomplishments

- Guest enables RAM via $0A to $0000 (address bit 8 clear). Store run: C000=$01. Resume run: C001=$A5 only if all 512 cells match, then C000=$02.
- Manifest copies the mbc1-continuation build object (only recipe differs); records protocol, missing_save and scope limits.
- Reproduce script prints `result=byte-identical`, verified with the pinned macOS RGBDS 1.0.1 archive (SHA-256 matched).
- ROM SHA-256 `314e05b419c07f1823983932d4e70ce57f0c366f44ec9ee86baf322f8dad50aa`; source SHA-256 `2ad5e7051b7fa42d9f83dbd5a34f76d6918a6a3f98c6c162c25fa4e515741a05`.
- Full phase1 ctest: 329/329 passed. No core change, no CTest names added.
- Guest behavior inside the emulator is not exercised here; Plan 09-12 registers the core runs.

## Task Commits

1. Task 1 (tracer): 45a2735 - fixture. Tracer `<verify>` printed `fixture=ok`; acceptance criteria passed.
2. Task 2: b0b51a7 - reproduction script.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

All five created files exist; commits 45a2735 and b0b51a7 are on the branch.

## Current Verification — 15.1-11

Rebuilt with pinned RGBDS 1.0.1. The result was byte-identical to the committed continuation ROM with the manifest SHA-256; emulator guest behavior remains outside this fixture-rebuild evidence.
