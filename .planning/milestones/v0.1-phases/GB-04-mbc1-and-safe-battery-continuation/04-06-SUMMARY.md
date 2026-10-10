---
phase: GB-04-mbc1-and-safe-battery-continuation
plan: 06
subsystem: installed-battery-api-and-package-verification
tags: [MBC1, battery-api, installed-consumers, bounded-fuzz, package-smoke, CI]
requires:
  - phase: GB-04-mbc1-and-safe-battery-continuation
    provides: bounded battery API and original process-continuation fixture
provides:
  - Relocated C and C++ consumer coverage for exact-size battery import/export and failure preservation
  - Deterministic bounded battery/API fuzz case in the fail-closed test inventory
  - Installed and preview packages that carry the licensed continuation fixture and verify its manifest digests
  - Extracted macOS package smoke that resumes fixture progress in a fresh process
  - Pinned RGBDS 1.0.1 fixture-reproduction lane for the MBC1 continuation ROM
affects: [GB-04-07, installed-package, battery-persistence, preview-verification]
actuals:
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns: [relocated-public-API-consumer, deterministic-bounded-fuzz, package-relative-original-fixture]
key-files:
  created:
    - tests/test_battery_fuzz.c
  modified:
    - tests/consumers/c/main.c
    - tests/consumers/cpp/main.cpp
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - .github/workflows/fixture-repro.yml
    - tests/scripts/verify-phase3-player.sh
    - CMakeLists.txt
    - cmake/PreviewPackageSmoke.cmake
    - cmake/VerifyInstalledPackage.cmake
    - src/player/main.c
    - docs/preview.md
requirements-completed: []
coverage:
  - id: D1
    description: Relocated C and C++ consumers exercise the installed battery API, including exact-size transfer, canaries, generation, and rejection without state mutation.
    requirement: SAVE-02
    verification:
      - kind: integration
        ref: "installed_consumer_c; installed_consumer_cpp; tests/scripts/verify-phase2-installed.sh (160/160 relocated installed CTests)"
        status: pass
    human_judgment: false
  - id: D2
    description: A fixed-seed 192-iteration API corpus bounds imported bytes and guest runtime, checking canaries and battery state after rejected operations.
    requirement: SAVE-02
    verification:
      - kind: unit
        ref: "battery_api_fuzz; ctest --preset phase1 --output-on-failure --no-tests=error (155/155)"
        status: pass
    human_judgment: false
  - id: D3
    description: The packaged original MBC1 fixture is checked against source/ROM manifest digests and its installed notice; a new process resumes saved guest progress from the extracted package.
    requirement: SAVE-04
    verification:
      - kind: e2e
        ref: "player_continuation_resume; tests/scripts/verify-phase3-player.sh; committed source 054adf0670395c93c1323fb1d22dee41e568fe6b; 37/37 player tests; package f488e867bf53226888f27a608ea13be2f034f5dd32391e6f08ff04535d91ed3f"
        status: pass
    human_judgment: false
  - id: D4
    description: The project-authored MBC1 fixture reproduces to the checked-in bytes with the pinned macOS RGBDS 1.0.1 archive and SHA-256.
    requirement: SAVE-04
    verification:
      - kind: integration
        ref: "RGBDS 1.0.1 macOS archive SHA-256 2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645; continuation ROM byte-identical"
        status: pass
    human_judgment: false
duration: 10min
completed: 2026-10-08
status: complete
---

# Phase 4 Plan 06: Installed Battery Consumers and Package Continuation

## Outcome

Installed C and C++ consumers now exercise exact-size battery import/export through the public package. A deterministic 192-iteration fuzz case keeps payload and guest-run bounds fixed and checks that rejected imports and ROM replacements preserve battery bytes, output canaries, and generation state. The original continuation fixture and its notice are installed with source/ROM manifest digest checks. The extracted macOS package smoke now confirms that the included MBC1 guest stores progress in one process and resumes it in a fresh process.

## Task Commits

1. **Task 1: Exercise bounded battery transfer in installed consumers and sanitizers** — `94bbf32` (`test(04-06): cover battery API consumers and bounded fuzz`)
2. **Task 2: Make required CI and fixture/player lanes cover the new save boundary** — `054adf0` (`test(04-06): verify packaged battery continuation and fixture lane`)

## Test Results

- The full phase1 CTest inventory passed **155/155** cases, including `battery_api_fuzz` and installed package smoke.
- The installed-package verifier passed **160/160** relocated CTests and then **155/155** core-only cases; no tests were skipped. Both external C and C++ consumers compiled and ran against the installed package.
- The player verifier passed **37/37** tests and the extracted-byte package smoke at committed source revision `054adf0670395c93c1323fb1d22dee41e568fe6b`. The package SHA-256 was `f488e867bf53226888f27a608ea13be2f034f5dd32391e6f08ff04535d91ed3f`; output confirmed `packaged MBC1 continuation fixture resumed in a fresh process`.
- The pinned RGBDS 1.0.1 macOS archive passed SHA-256 verification (`2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645`) and reproduced source SHA-256 `ad82e0cd51eeb6d536421d20c4a5b88ee0c019a4e699c2c75de077a20c82ba94` and ROM SHA-256 `f89bf3884ff10a702aa117f2963e6fe9ea8aeac3a9bc003f52b6c5ca6abfbbd2` byte-for-byte. The ordinary build continues to use checked-in bytes offline.
- The existing sanitizer job consumes `tests/expected-tests.txt`, so the new fuzz test is part of its required inventory. The sanitizer itself and exact-head hosted CI are still pending the final Phase 4 PR; no local sanitizer pass is claimed on this macOS host.
- The whitespace check passed before the plan commits. No dependency was added.

## Decisions and Evidence Limits

- Keep fuzz deterministic and bounded: 192 iterations, at most 8193 import bytes, and at most 1024 half-dots per guest run. This is a regression corpus, not an unbounded fuzzing campaign.
- Reuse the existing CI test inventory and preview verifier. The CI workflow already runs the listed inventory under ASan/UBSan, and the preview workflow already calls the updated package verifier, so those workflow files needed no edit. The fixture-reproduction workflow was extended to verify and rebuild this fixture with the existing pin.
- This verifies public package behavior and file-backed continuation for the declared software profile. It does not establish physical MBC1/DMG behavior, CGB, RTC, MBC1M, or other mapper support.

## Requirement Traceability

The GSD readiness check returned **0/3** requirements ready to mark complete because SAVE-02, SAVE-03, and SAVE-04 are shared with Plan 04-07. This summary records Plan 04-06 coverage without marking shared requirements complete early.

## User Setup Required

None. The required macOS verification used the pinned temporary RGBDS archive; the Linux sanitizer and exact-head hosted checks will be evaluated against the final Phase 4 revision.

## Next

Continue Phase 4 with Plan 04-07, which publishes the cartridge/save contract and reconciles the final requirement evidence. Exact next command: `$gsd-execute-phase 4`. After Phase 4 verification, stop before Phase 5 — DMG Audio and Stable Playback; its next discussion command is `$gsd-discuss-phase 5`.

---
*Phase: GB-04-mbc1-and-safe-battery-continuation*
*Started: 2026-10-08T04:02:34Z*
*Completed: 2026-10-08T04:12:56Z*

## Self-Check: PASSED

- [x] Relocated C/C++ battery consumers and bounded fuzz passed; installed and core inventories had no skips.
- [x] The committed-revision macOS package carried and resumed the original fixture in a fresh process.
- [x] The pinned RGBDS 1.0.1 macOS archive reproduced the exact source and ROM digests.
- [x] SAVE-02/03/04 remain unmarked until Plan 04-07 completes shared evidence reconciliation.
