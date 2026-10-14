---
phase: 13-cgb-hdma
plan: "07"
subsystem: testing
tags: [cgb, hdma, magentests, provenance, rgbds]
requires:
  - phase: 13-05
    provides: bounded runtime-mask HDMA fault controls
provides:
  - Pinned Magen hblank_vram_dma ROM admission and byte-identical reproduction
  - Source-derived guest map, FF55/HALT, green-screen, and runtime-control oracle
affects: [13-09, CGB-07]
actuals:
  tokens: 12627
  tasks: 2
  commits: 5
commits: 5
plan_head_before: a77a0cc8482664a477057c0b36175751e7eb6dfe
plan_head_after: 75f4547ae58cab700fba83ee5b7385f9aac4751d
tech-stack:
  added: []
  patterns:
    - Verify the original fixture and exact source/tool closure before running its guest oracle
    - Require guest data and display structure before comparing a regression digest
key-files:
  created:
    - fixtures/magentests/hblank_vram_dma.gbc
    - tests/scripts/test_reproduce_magentests.py
    - tests/scripts/test_magentests_hdma_registration.py
  modified:
    - .gitignore
    - fixtures/magentests/manifest.json
    - fixtures/magentests/LICENSE.txt
    - fixtures/magentests/SOURCES.md
    - fixtures/magentests/ELIGIBILITY.md
    - tests/scripts/reproduce-magentests.sh
    - tests/test_magentests.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - Admit only MagenTests release 0.5.0 at the pinned source revision after official release bytes and pinned RGBDS 0.6.1 rebuild match.
  - Derive the exact 12-byte aligned map prefix from the linked source address and FF52 masking, then test visible green pixels before the frame digest.
  - Keep evidence limited to the selected software model and differential ancestry; this plan does not qualify physical CGB-E hardware.
patterns-established:
  - Temporary provenance mutations must be rejected with their named diagnostic while a clean copy passes.
  - Runtime-mask controls are successful only when the positive oracle reports the specific intended data or HALT failure.
requirements-completed: []
coverage:
  - id: D1
    description: The admitted Magen HDMA image, rights/source closure, and RGBDS reproduction match their pinned digests.
    human_judgment: false
    verification:
      - kind: integration
        ref: "bash tests/scripts/reproduce-magentests.sh --self-check && bash tests/scripts/reproduce-magentests.sh --self-test && bash tests/scripts/reproduce-magentests.sh --compare-pinned"
        status: pass
      - kind: unit
        ref: "PYTHONPATH=tests/scripts python3 -m unittest -v test_reproduce_magentests"
        status: pass
  - id: D2
    description: Guest VRAM/status/HALT and fresh source-derived green frames gate the digest; no-transfer, wrong-bank, and wrong-HALT controls fail their intended predicates.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^(magentests_hblank_vram_dma$|cgb_hdma_magen_controls|magentests_.*(digest|repro|manifest)|cgb_hdma_guest_halt$)' --output-on-failure --no-tests=error"
        status: pass
      - kind: unit
        ref: "PYTHONPATH=tests/scripts python3 -m unittest -v test_magentests_hdma_registration"
        status: pass
      - kind: other
        ref: "python3 -c 'from pathlib import Path; lines=Path(\"tests/expected-tests.txt\").read_text().splitlines(); names=(\"magentests_hblank_vram_dma\",\"cgb_hdma_magen_controls\"); counts={n:lines.count(n) for n in names}; print(\"inventory-counts:\", counts); raise SystemExit(0 if all(v==1 for v in counts.values()) else 1)'"
        status: pass
      - kind: other
        ref: "ctest --test-dir build -R '^summary_coverage$' --output-on-failure --no-tests=error"
        status: pass
duration: 20min
completed: 2026-10-14
status: complete
---

# Phase 13 Plan 07: Magen HDMA Admission and Structural Differential Oracle Summary

**Pinned MagenTests 0.5.0 HDMA bytes and RGBDS rebuild, with guest VRAM/status/HALT predicates and a source-derived green-frame digest.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-10-14T22:03:49Z
- **Completed:** 2026-10-14T22:24:07Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments

- Admitted `hblank_vram_dma.gbc` from MagenTests revision `3f9c090f16e5a721db776febb9ba7d773e1c819c`, release 0.5.0. The file is 32,768 bytes with SHA-256 `e8124ce687d37a2402e20af92af1299610bfbda0871d605084c0bba2bf57135c`; all seven admitted Magen fixtures pass the manifest self-check.
- Recorded the full source/include/tool/license closure and kept the upstream MIT and CC0 notices. The pinned RGBDS 0.6.1 macOS x86-64 archive digest is `65929a5483c89b20955df0d78ceb87744d8ad0cf7c80919f6ee9ef90fc55c08d`. Its source rebuild matched the release bytes for all seven fixtures; no global tool install was used.
- Extended the guest oracle to require FF55 busy then complete, exact VRAM map bytes, HALT with mode-1/64-block second-transfer state, and stable fresh green frames before checking digest `7a137aaa9e15d61c56d78c0c02b507099f29b1ab7bff6cadd5df6980c0c510e0`.
- Added specific no-transfer, wrong-bank, and wrong-HALT runtime controls, manifest/reproduction CTests, and exact inventory entries. Both new CTest names occur exactly once.

## Verification Evidence

- `bash tests/scripts/reproduce-magentests.sh --self-check` passed.
- `bash tests/scripts/reproduce-magentests.sh --self-test` accepted a clean copy and rejected changed release digest, missing row, missing source pin, missing license, and altered build options with their intended diagnostics.
- `bash tests/scripts/reproduce-magentests.sh --compare-pinned` passed the source closure and byte-identical rebuild checks for all seven fixtures.
- Exact Task 2 verification passed: `cmake --preset phase1`, `cmake --build --preset phase1`, required-name JSON enumeration (`missing-required-tests: []`), and the selected CTest group (6/6 passed, including `cgb_hdma_guest_halt`, both Magen admission checks, the guest oracle, and controls).
- The planning coverage contract passed: `ctest --test-dir build -R '^summary_coverage$' --output-on-failure --no-tests=error` (1/1).
- Direct guest evidence: all 1,024 map bytes match the source-derived sequence (12 `$FF` bytes then 1,012 tile-index-1 bytes); the 20-by-18 visible region is uniformly RGB555 green `0x03E0`; FF55 reads show busy then complete; stable generations 16 and 17 match.
- Direct controls reported `no-transfer` as a missing map copy, `wrong-bank` as VRAM bank 1, and `wrong-HALT` as failure to retain the second mode-1 transfer at 64 blocks. None reached digest comparison.
- `PYTHONPATH=tests/scripts python3 -m unittest -v test_reproduce_magentests` and `PYTHONPATH=tests/scripts python3 -m unittest -v test_magentests_hdma_registration` each passed. The pinned provenance and CTest name exact-inventory checks are also registered in CTest/configure.

## Task Commits

| Task | Commit | Purpose |
|---|---|---|
| 1 RED | `3420750` | Added a failing provenance self-test |
| 1 GREEN | `d481d7b` | Admitted the pinned fixture and reproduction metadata |
| 1 correction | `225a260` | Restored the reproducer's executable mode |
| 2 RED | `b79d706` | Added a failing exact CTest inventory test |
| 2 GREEN | `75f4547` | Added the source-derived guest oracle and controls |

## Decisions Made

- Kept the reproducer's RGBDS archive private to the build cache and verified its digest before use.
- Kept `pending_hblank` diagnostic-only at the final HALT sample. The observed state is halted, mode 1, inactive, and 64 blocks remaining; no HBlank request needs to be pending at that sample.
- Kept the map oracle tied to the linked source layout and FF52 behavior instead of assuming all 1,024 destination bytes are tile index 1.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Restored the source reproducer executable mode.**
- **Found during:** Task 1
- **Issue:** Replacing the shell script through a patch changed its tracked mode from executable to non-executable.
- **Fix:** Restored mode `100755` in a separate correction commit.
- **Files modified:** `tests/scripts/reproduce-magentests.sh`
- **Verification:** The exact self-check, negative-copy self-test, and pinned rebuild commands passed.
- **Committed in:** `225a260`

**2. [Rule 1 - Bug] Corrected the expected source-derived VRAM map prefix.**
- **Found during:** Task 2
- **Issue:** `NewTileMap` links at ROM `$022C`; FF52 masks the low nibble, so transfer begins at `$0220` and copies 12 preceding `$FF` bytes before the 1,012 tile-index-1 bytes.
- **Fix:** Asserted that exact map and documented that the guest's SCX/SCY place the prefix outside the visible viewport.
- **Files modified:** `fixtures/magentests/SOURCES.md`, `fixtures/magentests/ELIGIBILITY.md`, `tests/test_magentests.c`
- **Verification:** Positive map and full-frame green checks passed; wrong-bank and no-transfer controls failed their intended predicates.
- **Committed in:** `75f4547`

**3. [Rule 1 - Bug] Removed an unsupported pending-HBlank requirement from the final HALT assertion.**
- **Found during:** Task 2
- **Issue:** The final sample has no pending HBlank request while the second transfer remains correctly armed in mode 1 with 64 blocks.
- **Fix:** Asserted guest-visible HALT/FF55 plus mode, activity, and remaining-block state; retained pending-HBlank only as diagnostic output.
- **Files modified:** `tests/test_magentests.c`
- **Verification:** The positive HALT assertion passed and the wrong-HALT control failed specifically at that predicate.
- **Committed in:** `75f4547`

**Total deviations:** 3 auto-fixed (Rule 1).
**Impact on plan:** Each correction keeps the fixture oracle source-derived and executable; no core change or scope expansion was needed.

## TDD Gate Compliance

- Task 1 RED evidence: `build/13-07-evidence/task1-red.json`; `gsd_run check tdd-red-evidence` returned `RED_EVIDENCE_OK` because the intended `--self-test` acceptance test failed while that command was not implemented. GREEN passes the clean positive and all five specific provenance mutations.
- Task 2 RED evidence: `build/13-07-evidence/task2-red.json`; the exact-inventory test failed because both planned CTest names were absent. GREEN passes after adding the CMake registrations and inventory entries.
- Both failures were inspected as target-predicate failures; neither came from a missing fixture, crash, timeout, or unrelated test failure.

## Self-Check: PASSED

- All listed fixture, source, test, and summary artifacts exist.
- Task commits `3420750`, `d481d7b`, `225a260`, `b79d706`, and `75f4547` are ancestors of the current plan head.
- The last task commit contains no tracked-file deletions, and the changed implementation files have no TODO/FIXME/placeholder stubs.

## Issues Encountered

No unresolved issues. The harness is software evidence for the selected CGB-E profile; it does not establish physical CGB-E timing or hardware qualification. No new mandatory emulator, CI job, or third-party install fixture was added.

## Next Phase Readiness

Plan 13-07 is complete. Phase 13 remains active, and requirement CGB-07 remains open pending the remaining Phase 13 plans. The completed stage is **Phase 13 Wave 6, plan 13-07 — Magen HDMA admission and structural differential oracle**. Next is **Phase 13 Wave 7, plan 13-09 — Executed SameSuite dispositions and optional CGB-C boundary**. Exact next command: **`/gsd-execute-phase 13 --wave 7`**. Phase 14 remains unstarted; both auto-advance flags remain false.

---
*Phase: 13-cgb-hdma*
*Completed: 2026-10-14*
