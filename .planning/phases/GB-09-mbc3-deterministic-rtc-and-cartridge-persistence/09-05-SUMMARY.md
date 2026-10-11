---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 05
subsystem: fixtures
tags: [mbc3, rtc, rgbds, continuation-fixture]
requires: []
provides:
  - fixtures/mbc3-rtc-continuation original MBC3+RTC continuation guest
  - tests/scripts/reproduce-mbc3-rtc-continuation.sh
affects: [09-10, 09-12, 09-16]
tech-stack:
  added: []
  patterns: [mbc1-continuation fixture style, pinned RGBDS 1.0.1 byte-identical rebuild]
key-files:
  created:
    - fixtures/mbc3-rtc-continuation/continuation.asm
    - fixtures/mbc3-rtc-continuation/continuation.gb
    - fixtures/mbc3-rtc-continuation/manifest.json
    - fixtures/mbc3-rtc-continuation/LICENSE.txt
    - tests/scripts/reproduce-mbc3-rtc-continuation.sh
  modified: []
key-decisions:
  - "Marker bytes are written as hex literals ($52 $54 $43) because RGBDS 1.0.1 warns that string-as-number is obsolete"
requirements-completed: [CART-06, RTC-03]
duration: 20 min
completed: 2026-10-11
status: complete
commits: 2
plan_head_before: aef9430e2345f98e5957ead2a77db34cd31d8b98
plan_head_after: b19cefc062c9c5420aafd22840d327e27daf56db
actuals:
  tokens: 9000
  tasks: 2
  commits: 2
---

# Phase 9 Plan 05: MBC3+RTC Continuation Guest Summary

Original MIT MBC3+timer+battery guest (type $10, 32 KiB ROM, 8 KiB RAM) that sets a mode-selected RTC clock on a store run and latches and publishes it on a resume run, rebuilt byte-identically with RGBDS 1.0.1.

## Accomplishments

- Guest: store branch (marker absent, fresh RAM $FF) writes the clock for mode byte $A010 (normal, halted 12:34:56, or 23:59:50 day 511), the 'RTC' marker, and C000=$01. Resume branch latches ($00 then $01 to $6000), publishes S, M, H, DL, DH at C001-C005, C006=$A5 and C000=$02.
- Manifest copies the mbc1-continuation build object (only recipe differs), records the protocol including missing_save, host_delta_rule and scope limits.
- Reproduce script prints `result=byte-identical`; verified with the macOS RGBDS 1.0.1 archive (SHA-256 matched the manifest pin).
- ROM SHA-256 `2a6e1922440d6af43a21e65bce579f1d0962f891f308afbe2268395fdbd644a9`; source SHA-256 `88097fe7d933d429e59bc1dcf873ea30d556670cc4c7a560330ee9807c16eb20`.
- Full phase1 ctest: 329/329 passed. No core change, no CTest names added.

## Task Commits

1. Task 1 (tracer): dbc1e3f - fixture. Tracer `<verify>` printed `fixture=ok`.
2. Task 2: b19cefc - reproduction script.

## Deviations from Plan

None - plan executed exactly as written. (Hex marker literals instead of character strings, to keep the build warning-free.)

## Known Stubs

None.

## Self-Check: PASSED

All five created files exist; commits dbc1e3f and b19cefc are on the branch.
