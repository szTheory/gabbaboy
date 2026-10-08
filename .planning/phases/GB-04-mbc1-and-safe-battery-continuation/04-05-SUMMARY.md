---
phase: GB-04-mbc1-and-safe-battery-continuation
plan: 05
subsystem: battery-continuation-fixture
tags: [MBC1, battery-save, RGBDS, subprocess, fixture-provenance]
requires:
  - phase: GB-04-mbc1-and-safe-battery-continuation
    provides: MBC1 battery API and player save lifecycle
provides:
  - Original licensed MBC1 battery-continuation fixture with exact RGBDS reproduction
  - Separate-process guest resume test with missing, wrong-ROM, and altered-payload controls
  - Offline CTest fixture digest check and explicitly admitted fixture ROM
affects: [GB-04-06, GB-04-07, battery-persistence, player-save-verification]
actuals:
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns: [pinned-source-to-ROM reproduction, content-addressed save-key assertion, bounded fresh-process oracle]
key-files:
  created:
    - fixtures/mbc1-continuation/continuation.asm
    - fixtures/mbc1-continuation/continuation.gb
    - fixtures/mbc1-continuation/LICENSE.txt
    - fixtures/mbc1-continuation/manifest.json
    - tests/scripts/reproduce-mbc1-continuation.sh
    - tests/player/test_continuation.c
  modified:
    - .gitignore
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/player/CMakeLists.txt
    - tests/player/expected-tests.txt
requirements-completed: []
coverage:
  - id: D1
    description: Pinned RGBDS 1.0.1 reproduces the project-authored type $03 fixture byte-for-byte; rights, digest, bootless profile applicability, protocol, and scope limits are recorded.
    requirement: SAVE-04
    verification:
      - kind: integration
        ref: "bash tests/scripts/reproduce-mbc1-continuation.sh with the pinned RGBDS archive"
        status: pass
      - kind: unit
        ref: "mbc1_continuation_fixture_digest; ctest --preset phase1"
        status: pass
    human_judgment: false
  - id: D2
    description: A fresh child process reaches guest success only after importing the prior process's saved tuple; missing save, wrong-ROM identity, and changed payload have separate asserted outcomes.
    requirement: SAVE-04
    verification:
      - kind: integration
        ref: "player_continuation_resume; player_continuation_missing_save; player_continuation_wrong_rom; player_continuation_mutated_payload"
        status: pass
      - kind: e2e
        ref: "bash tests/scripts/verify-phase3-player.sh (37/37 player CTests and extracted package smoke)"
        status: pass
    human_judgment: false
  - id: D3
    description: The continuation harness independently derives the save key, validates recovery bytes and guest markers, and bounds subprocess execution; no physical-hardware claim is made.
    requirement: SAVE-03
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh; source revision a6d06b0cd4c4ff601570745a22c2feaa1213d59b"
        status: pass
    human_judgment: false
duration: 7min
completed: 2026-10-08
status: complete
---

# Phase 4 Plan 05: Reproducible Battery Continuation Fixture

## Outcome

An original MBC1 battery ROM now demonstrates guest progress surviving a real process boundary. The first process writes a three-byte progress tuple to battery RAM and saves it; a second fresh process imports the tuple and reaches a distinct guest success marker. Independent missing-save, wrong-ROM-envelope, and modified-payload cases take the empty/rejection path.

The fixture is project-authored, MIT-licensed, 32 KiB, and declares standard MBC1 type `$03` with 8 KiB battery RAM. Its manifest records source and ROM digests, RGBDS 1.0.1 archive pins, build recipe, bootless DMG-CPU-B applicability, expected protocol, timeout, and software-only scope. The reproduction script checks all of those records and fails on any byte difference. Ordinary tests consume the checked-in, digest-verified bytes offline.

## Task Commits

1. **Task 1: Author and reproduce the battery-dependent MBC1 guest program** — `fb0d247` (`feat(04-05): add reproducible battery continuation fixture`)
2. **Task 2: Assert fresh-process guest success and independent negative controls** — `a6d06b0` (`test(04-05): verify fresh-process battery continuation controls`)

## Test Results

- The pinned RGBDS 1.0.1 reproduction passed with the macOS archive SHA-256 `2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645`. Source SHA-256: `ad82e0cd51eeb6d536421d20c4a5b88ee0c019a4e699c2c75de077a20c82ba94`; ROM SHA-256: `f89bf3884ff10a702aa117f2963e6fe9ea8aeac3a9bc003f52b6c5ca6abfbbd2`.
- `ctest --preset phase1 --output-on-failure --no-tests=error` passed **154/154** tests, including `mbc1_continuation_fixture_digest`.
- The command using `bash` and `tests/scripts/verify-phase3-player.sh` passed **37/37** optional player tests and the extracted-package smoke at source revision `a6d06b0cd4c4ff601570745a22c2feaa1213d59b`. Package SHA-256: `6a0d54abe29decdbe4902119d925385b22acdbee819726b8faeb03417ff358d2`; SDL license receipt SHA-256: `1c040b8271b37e5076359f8fd54240e371114112924d2df81ef87c7d6a1dfdfd`.
- The four named continuation cases each use a bounded subprocess and isolated temporary preferences directory. The resume case checks guest WRAM markers after save import; the wrong-ROM case seeds the variant's independently computed save key with the original valid envelope and verifies warning plus exact recovery preservation; the altered-payload case verifies rejection and preserved bytes.
- `git diff --check` passed. The task commits contain only the planned fixture/test files and the narrow `.gitignore` allowlist for this permissioned public ROM.

## Decisions and Evidence Limits

- Keep the source and expected ROM in the repository, pin RGBDS 1.0.1 and both platform archive digests, and keep routine tests offline.
- Derive the variant's content-addressed save path independently in the harness so an adapter filename regression cannot make the wrong-ROM control pass accidentally.
- This demonstrates file-backed software continuation for the declared bootless DMG-CPU-B model. It does not demonstrate physical MBC1/DMG behavior, boot-ROM behavior, CGB, RTC, MBC1M, or other mapper behavior.
- The manifest's CRC/checksum language describes accidental-corruption detection, not authentication.

## Plan Deviation

The repository ignores `*.gb` and requires permissioned public fixtures to be explicitly admitted. Added one `.gitignore` exception for `fixtures/mbc1-continuation/continuation.gb`; no broader ignore behavior changed.

## Requirement Traceability

The GSD readiness check returned **0/2** requirements ready at this plan because SAVE-03 and SAVE-04 are shared with Plans 04-06/04-07. This summary records this plan's coverage without prematurely marking either phase requirement complete.

## User Setup Required

None. No physical hardware, commercial ROM, private data, or external service was used.

## Next

Continue Phase 4 with Plan 04-06, which owns relocated C/C++ battery consumers, fuzz/sanitizer coverage, CI inventory, and package verification. Keep Phase 4 active until Plan 04-07 and the phase evidence closeout are complete; then stop at the phase boundary.

---
*Phase: GB-04-mbc1-and-safe-battery-continuation*
*Started: 2026-10-08T03:53:22Z*
*Completed: 2026-10-08T04:00:47Z*

## Self-Check: PASSED

- [x] Fixture source, notice, manifest, and checked-in bytes agree with pinned RGBDS reproduction.
- [x] Core CTest passed 154/154 and the committed-revision player verifier passed 37/37 plus package smoke.
- [x] All four fresh-process continuation scenarios passed with bounded runtime and distinct control outcomes.
- [x] The plan's SAVE-03/SAVE-04 coverage is recorded; neither shared requirement was marked complete before remaining plans.
