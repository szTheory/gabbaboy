---
phase: 08-cartridge-seam-mbc5-and-mbc2
plan: 07
subsystem: testing
tags: [cmake, ctest, redistribution-guard, ci, mooneye, mbc5]
status: partial
requires:
  - phase: 08-cartridge-seam-mbc5-and-mbc2
    provides: 08-04 player seam, 08-06 sibling mooneye-mbc verifier and ctests
provides:
  - cmake/ScanForbiddenFixtures.cmake name+digest scan with planted, empty and dir-list controls
  - extracted-preview-package and player-package scans for the 15 sibling ROMs
  - fixture-repro mooneye-mbc-repro hosted Linux rebuild leg (D-25 recapture)
  - exact-head CI green for plans 08-02..08-07
affects: [08-08, 08-09, 08-10, phase-08-verification]
plan_head_before: 2b5f90aedfed19dc9468e7eba70304661770f53b
plan_head_after: 493f77cab6cfec5248889688039c295b5f2d28da
actuals:
  tokens: 14000
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns: ["CMake -P scan script with expect_exit.cmake fail-closed controls"]
key-files:
  created: [cmake/ScanForbiddenFixtures.cmake]
  modified:
    - cmake/PreviewPackageSmoke.cmake
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/scripts/verify-phase3-player.sh
    - .github/workflows/fixture-repro.yml
    - .gitattributes
key-decisions:
  - "Scan is a CMake script (Open Question 4); expected fixture list stays tracer, visible-demo, mbc1-continuation (Open Question 7)"
  - "Ninth-bit mutant (D-29) NOT landed: measured premise failure, see Blocker"
requirements-completed: []
coverage:
  - id: D1
    description: "Name and digest redistribution guard rejects planted fixtures and wrong fixture lists"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R ^mooneye_mbc_ --output-on-failure"
        status: pass
  - id: D2
    description: "Install and extracted preview/player packaging exclude admitted Mooneye MBC fixtures"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R ^(mooneye_mbc_|preview_package_smoke) --output-on-failure"
        status: pass
  - id: D3
    description: "Historical exact-head Linux rebuild and CI receipts remain attributed to their original producer"
    human_judgment: false
    verification:
      - kind: other
        ref: "python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"
        status: pass
---

# Phase 8 Plan 07: Repository-only scan, hosted rebuild leg, exact-head CI Summary

The 15 sibling Mooneye ROMs are proven absent from the install tree, extracted preview package and player package by a name-and-digest CMake scan with three fail-closed controls, and the hosted Linux rebuild matches all 15 D-25 digests; the D-29 ninth-bit mutant could not be landed because its premise is false.

## Accomplishments

- `cmake/ScanForbiddenFixtures.cmake`: no-symlink-follow walk; fails `mooneye-installed: <rel>` on a path component containing "mooneye" or a size+SHA-256 match to any of the 15 manifest ROMs (4 MiB and 8 MiB included), `scan-dir-empty`, `fixture-dirs-mismatch`. Success prints `mooneye-mbc absent from scanned tree files=<n>`.
- Four new CTests: `mooneye_mbc_not_installed` (real install tree, FIXTURES_REQUIRED libbet_install, exact dirs), `_selftest` (planted renamed mbc5_rom_512kb), `_empty`, `mooneye_mbc_fixture_dirs_selftest`. All pass; extra manual control: renamed `mbc5_rom_64Mb.gb` is detected.
- `preview_package_smoke` now scans the extracted prefix; `verify-phase3-player.sh --build-package` scans the staged player package (reported `files=14`, clean).
- `mooneye-mbc-repro` job added to fixture-repro.yml (no new actions; pinned checkout and upload-artifact only; actionlint clean).

## Blocker: D-29 ninth-bit mutant (not landed)

Implemented as specified (configure-time exactly-once anchor `& 1u) << 8` -> `& 0u) << 8`, never-installed core and runner, 64Mb and 32Mb tests). Observed result: `mooneye_mbc_ninth_bit_mutant_64Mb` reports `status=pass callback_result=pass callback_pc=0216` (exit 0), not fail. The plan forbids accepting a pass, so the tests, targets and inventory lines were removed before commit; the working patch is not committed.

Measured cause (not speculation): instrumenting the unmutated core shows the 64Mb guest writes only 257 bank selections (banks 0..255, then bank 1), every `$3000` write is `$FE` (bit 0 clear), and the guest bank loop (`ld a,b; cp 1; ... ld a,c; cp 0`) is byte-identical in all eight mbc5 ROMs and terminates at bc=$0100. Bank >= 256 is never selected, so `rom_64Mb` does not discriminate the ninth bit in this derivative, contradicting the 08-RESEARCH P7/D-29 premise. A control mutant (`return 1u` in the bank helper) fails 64Mb with callback_pc=0175, so the test is otherwise sensitive. Ninth-bit behavior remains covered only by C unit tests (`mbc5_rom_banking`, `mbc5_rom_bound`) and the planned 08-08 fixture. Needs a planner/owner decision: re-point the discriminator to the 08-08 `$1FF` fixture or the unit tests, and correct ROADMAP success wording.

## Exact-head CI (D-30)

Head `493f77cab6cfec5248889688039c295b5f2d28da` (PR #64, draft). `wait-exact-head-ci.py`: PASS run_id=38152853926 (pull_request event, attempt 1).
Jobs: native-linux-x64 success, native-macos-arm64 success, native-windows-x64 success, linux-asan-ubsan success, cmake-floor-3.25.3 success, player-gate success, macos-player-package success, required-native success.
fixture-repro run 38152853896 (pull_request): mooneye-mbc-repro success, mooneye-original-repro success, mooneye-candidate-repro success, fixture-repro success. preview-package-smoke run 38152853893 success.
Hosted Linux rebuild (first head 1f034a7, run 38151282870, ubuntu-22.04, wla-gb 10.7, wlalink 5.22): 15 of 15 `match` lines; all digests equal D-25. D-25 digest claim is therefore supported.

Local: full ctest phase1 313/313 passed; inventory check `--installed` verified 313 cases; DMG baseline pass; `verify-phase3-player.sh --build-package` passed. ASan preset is Linux-only (configure refuses on macOS), so it was proven on hosted CI only.

## Deviations from Plan

**1. [Rule 1 - Bug] Windows CRLF broke parent-reference digest (plan 08-06 test)**
- Found during: Task 3 CI read (first head, native-windows-x64, `mooneye_mbc_fixture_digest`: `parent-reference-digest: ../mooneye/headless-report.patch`)
- Fix: `.gitattributes` `text eol=lf` for fixtures/mooneye/headless-report.patch and font-source.c
- Commit: 493f77c

**2. [Rule 1 - Bug] ASan suite timeout (plan 08-06 test)**
- Found during: Task 3 CI read (linux-asan-ubsan, `mooneye_mbc_required_suite` 30 s timeout; ramg case 15.4 s)
- Fix: suite TIMEOUT 120, case TIMEOUT 60 in tests/CMakeLists.txt
- Commit: 493f77c

**3. [Plan premise failure] Ninth-bit mutant omitted** (see Blocker). One fix-and-push cycle used of three.

**Total deviations:** 2 auto-fixed, 1 unresolved premise failure.

## Commits

- 603a664 feat(08-07): scan install tree and extracted package
- 0cdbf10 test(08-07): scan the staged player package
- 1f034a7 ci(08-07): add mooneye-mbc-repro leg
- 493f77c fix(08-07): eol pin and sanitizer timeouts

## Known Stubs

None.

## Threat Flags

None. T-08-25/26/29 mitigated; T-08-27 not mitigated (no mutant landed); T-08-28 mitigated by the hosted 15/15 match.

## Self-Check: PASSED (with the documented gap)

Files exist: cmake/ScanForbiddenFixtures.cmake, edited cmake/PreviewPackageSmoke.cmake, tests/CMakeLists.txt, tests/scripts/verify-phase3-player.sh, .github/workflows/fixture-repro.yml, .gitattributes. Commits 603a664, 0cdbf10, 1f034a7, 493f77c are ancestors of HEAD. Requirements CART-02 and CART-03 are intentionally NOT marked complete here.
