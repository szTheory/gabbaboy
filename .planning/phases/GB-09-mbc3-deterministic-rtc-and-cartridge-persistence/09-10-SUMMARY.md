---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 10
subsystem: fixtures
tags: [mbc5, continuation-fixture, rgbds, fixture-repro, ci]
requires: [09-05, 09-06, 09-08]
provides:
  - fixtures/mbc5-continuation original MBC5 128 KiB continuation guest
  - tests/scripts/reproduce-mbc5-continuation.sh
  - fixture-repro pin check and byte-identical rebuild for the MBC3+RTC, MBC2 and MBC5 guests
affects: [09-12, 09-16]
tech-stack:
  added: []
  patterns: [mbc3-rtc-continuation fixture style, pinned RGBDS 1.0.1 byte-identical rebuild]
key-files:
  created:
    - fixtures/mbc5-continuation/continuation.asm
    - fixtures/mbc5-continuation/continuation.gb
    - fixtures/mbc5-continuation/manifest.json
    - fixtures/mbc5-continuation/LICENSE.txt
    - tests/scripts/reproduce-mbc5-continuation.sh
  modified:
    - .github/workflows/fixture-repro.yml
    - .gitignore
key-decisions:
  - "Markers are hex literals ($47 $42 $35) as in the RTC guest, avoiding the RGBDS 1.0.1 string-as-number warning"
requirements-completed: [CART-06, RTC-03]
duration: 25 min
completed: 2026-10-11
status: complete
commits: 2
plan_head_before: 8f7a4a42d000d973fe2dd2c661344265942731d2
plan_head_after: 28bb5b0bc72be81d86aa165b525dd53968bad88c
actuals:
  tokens: 9000
  tasks: 2
  commits: 2
coverage:
  - id: D1
    description: "MBC2, MBC3+RTC and MBC5 continuation ROMs rebuild byte-identically from project-owned sources with the pinned RGBDS version"
    verification:
      - kind: integration
        ref: "bash tests/scripts/reproduce-mbc2-continuation.sh && bash tests/scripts/reproduce-mbc3-rtc-continuation.sh && bash tests/scripts/reproduce-mbc5-continuation.sh with RGBDS 1.0.1 on PATH"
        status: pass
    human_judgment: false
---

# Phase 9 Plan 10: MBC5 Continuation Guest and Hosted Fixture Reproduction Summary

Original MIT MBC5+RAM+battery guest (type $1B, 32 KiB ROM, 128 KiB RAM) storing 'GB5' markers in RAM banks 0 and 15, rebuilt byte-identically with RGBDS 1.0.1, and all three continuation guests (MBC3+RTC, MBC2, MBC5) wired into the hosted fixture-repro pin check and rebuild.

## Accomplishments

- Guest: store branch (bank 0 marker absent; fresh RAM reads $FF) writes `G B 5 $00` at bank 0 $A000 and `G B 5 $0F` at bank 15 $A000 and sets C000=$01. Resume branch verifies both markers, sets C001=$A5 and C000=$02. A missing or rejected save is therefore observable as C000=$01.
- Manifest copies the mbc1-continuation build object (only recipe differs), notes that 128 KiB RAM exercises the maximum envelope v2 size, and records scope limits. ROM SHA-256 `34e80d0c4a0c1edb6d8b2a2cda31e9f0cdcc672aa9579f86a9ec5a328aaca667`; source SHA-256 `b56718d60e3b0d0b73fa53581a54cb7541d1c2e37b9c651b3c018c409d92892d`.
- Built with the macOS RGBDS 1.0.1 archive (SHA-256 verified against the manifest pin), never the local 1.0.4. The reproduce script prints `result=byte-identical`; so do the MBC3+RTC and MBC2 scripts.
- fixture-repro: the pin-consistency python now loads the three guest manifests and fails with a named message on any version, macOS archive pair or Linux archive pair drift (verified by executing the extracted python locally). Three new steps run the three reproduce scripts with GBB_RGBDS_ARCHIVE and GBB_RGBDS_ARCHIVE_SHA256. magentests-repro and rtc3test-repro are untouched. actionlint is clean.
- Full phase1 ctest 356/356 passed; verify-test-inventory passed (356 executed, none skipped). No CTest names added.

## Task Commits

1. Task 1 (tracer): 5f9f866 - guest, manifest, license, reproduce script. Tracer verify printed `result=byte-identical` and `header=ok`.
2. Task 2: 28bb5b0 - fixture-repro pin check and steps.

## Deviations from Plan

**1. [Rule 3 - Blocking] MBC2 and MBC3+RTC continuation ROMs were untracked**
- **Found during:** Task 1
- **Issue:** `.gitignore` excludes `*.gb` and had no exceptions for fixtures/mbc2-continuation/continuation.gb or fixtures/mbc3-rtc-continuation/continuation.gb, so Plans 09-05/09-06 committed their sources and manifests but not the ROMs. The hosted rebuild step compares against the checked-in ROM, so it would have failed on a clean checkout.
- **Fix:** Added per-file exceptions for the mbc2, mbc3-rtc and mbc5 continuation ROMs and committed the two missing ROMs (byte-identical to rebuilds, digests match their manifests).
- **Files modified:** .gitignore, fixtures/mbc2-continuation/continuation.gb, fixtures/mbc3-rtc-continuation/continuation.gb
- **Commit:** 5f9f866

**Total deviations:** 1 auto-fixed (1 blocking). **Impact:** necessary for the hosted reproduction to pass; no scope change.

## Known Stubs

None.

## Notes

- Workflow edits cannot run locally. Hosted CI proof of the new fixture-repro steps comes with the next push (not pushed by this plan).
- The guest's runtime behavior (store then resume across processes) is exercised by Plan 09-12; this plan proves only the byte-identical build and header.

## Self-Check: PASSED

Files exist (mbc5-continuation asm/gb/manifest/LICENSE, reproduce script); commits 5f9f866 and 28bb5b0 are on the branch; acceptance criteria and plan verification re-run and passing.

## Fresh Focused Evidence (15.1-12)

- Re-ran all three continuation reproduction scripts with RGBDS 1.0.1 from the previously SHA-verified tool archive. Each printed `result=byte-identical`; rebuilt ROM digests were MBC2 `314e05b419c07f1823983932d4e70ce57f0c366f44ec9ee86baf322f8dad50aa`, MBC3+RTC `2a6e1922440d6af43a21e65bce579f1d0962f891f308afbe2268395fdbd644a9`, and MBC5 `34e80d0c4a0c1edb6d8b2a2cda31e9f0cdcc672aa9579f86a9ec5a328aaca667`.
- The original hosted fixture-reproduction workflow claim remains attached to its recorded producer and was not re-run here.
