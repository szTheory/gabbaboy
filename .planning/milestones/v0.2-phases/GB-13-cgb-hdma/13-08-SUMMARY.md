---
phase: 13-cgb-hdma
plan: "08"
subsystem: testing
tags: [cgb, hdma, rgbds, sdl3]
requires:
  - phase: 13-03
    provides: bounded public fixture execution harness
provides:
  - Original source-authored CGB HBlank-DMA guest with guest pass/fail markers and a no-transfer control
  - Structural RGB555 predicates for the unchanged player smoke path
  - Pinned RGBDS reproduction and fixture-repro workflow checks
affects: [phase13-05, phase13-07, phase13-09]
actuals:
  tokens: 11902
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - Source-derived tile predicates are checked before frame digests
    - Original fixture and no-transfer twin share a pinned reproduction recipe
key-files:
  created:
    - fixtures/cgb-hdma/hblank.asm
    - fixtures/cgb-hdma/hblank.gb
    - fixtures/cgb-hdma/manifest.json
    - fixtures/cgb-hdma/LICENSE.txt
    - tests/scripts/reproduce-cgb-hdma.sh
  modified:
    - tests/test_cgb_hdma.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/player/cgb_smoke.cmake
    - tests/player/CMakeLists.txt
    - tests/player/expected-tests.txt
    - .github/workflows/fixture-repro.yml
key-decisions:
  - Keep guest marker and FF55 state assertions in the headless public-API harness; player smoke verifies the same guest's visible source-derived pixels through the unchanged player path.
  - Keep the LCD active from the bootless CGB profile so the existing one-frame player smoke can capture a completed frame without adding player behavior.
  - Keep CGB-07 open for Phase 13 closeout and later evidence plans.
patterns-established:
  - Validate literal guest state and source-derived color structure before checking a pinned digest.
  - A no-transfer twin is a behavioral negative control with its own expected failure frame and exact guest failure stage.
requirements-completed: []
task_commits:
  - task: 1
    name: Original guest and public fixture predicate
    commits:
      - 758fe69
      - af88ae4
  - task: 2
    name: Existing player smoke and fixture-repro integration
    commits:
      - e50c43a
      - eb87c27
plan_head_before: 247ee2be14bcdd9344ae4419d755116fd4cd4b1a
plan_head_after: eb87c27fb2abfa380342579b6f20eb6398faa30b
ending_sha: eb87c27fb2abfa380342579b6f20eb6398faa30b
duration: 18min
completed: 2026-10-14
status: complete
coverage:
  - id: D1
    description: Original CGB guest reports successful banked HBlank transfers and source-derived RGB555 pixels, while the no-transfer twin records its named failure markers and white frame.
    verification:
      - kind: integration
        ref: "build/tests/test_cgb_hdma --fixture fixtures/cgb-hdma/hblank.gb --check-controls"
        status: pass
      - kind: other
        ref: "bash tests/scripts/reproduce-cgb-hdma.sh --self-check && bash tests/scripts/reproduce-cgb-hdma.sh --self-test"
        status: pass
      - kind: integration
        ref: "GBB_RGBDS_ARCHIVE=build/13-08-rgbds/rgbds-macos.zip GBB_RGBDS_ARCHIVE_SHA256=2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645 bash tests/scripts/reproduce-cgb-hdma.sh --compare-pinned"
        status: pass
    human_judgment: false
  - id: D2
    description: The unchanged player path checks 40 source-derived quadrant samples for both the original guest and its no-transfer failure twin before comparing RGBA digests.
    verification:
      - kind: integration
        ref: "ctest --test-dir build-player --show-only=json-v1 | python3 -c 'import json,sys; names={t[\"name\"] for t in json.load(sys.stdin)[\"tests\"]}; required={\"player_cgb_hdma_smoke\",\"player_cgb_hdma_smoke_no_transfer\"}; missing=required-names; print(\"missing-required-tests:\",sorted(missing)); sys.exit(bool(missing))'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build-player -R '^player_cgb_hdma_smoke' --output-on-failure --no-tests=error"
        status: pass
      - kind: integration
        ref: "Run hdma-positive predicate against the generated no-transfer ROM; rejected with 'hdma distinct colours 1, expected 4' before digest comparison."
        status: pass
    human_judgment: false
  - id: D3
    description: The existing fixture-repro job runs the pinned original guest rebuild and its provenance and negative controls without changing the job set or fixture allow-list.
    verification:
      - kind: other
        ref: "python3 -c 'import yaml; yaml.safe_load(open(\".github/workflows/fixture-repro.yml\"))'"
        status: pass
      - kind: integration
        ref: "RGBDS 1.0.1 --self-check, --self-test, and --compare-pinned passed locally with the official macOS archive SHA-256 pin."
        status: pass
    human_judgment: false
---

# Phase 13 Plan 08: Original visible DMA guest and existing player smoke Summary

**An original 32 KiB CGB guest now demonstrates two CPU-programmed one-block HBlank transfers with checked guest state and four source-derived colors, and the existing player path verifies the same image.**

## Performance

- **Duration:** 18 minutes
- **Started:** 2026-10-14T21:22:46Z
- **Completed:** 2026-10-14T21:40:14Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments

- Added the MIT-licensed project-original `hblank.asm` and reproduced `hblank.gb` with isolated RGBDS 1.0.1. The source, ROM, archive, recipe, and source data are pinned in the manifest.
- The guest starts two separate CPU writes through FF51-55, selects VBK0 and VBK1, checks active/completed FF55 values and all transferred tile bytes, then stores C000=A5. Its exact FF55 sequence is 00/FF/00/FF. The no-transfer twin stores C000=EE, C001=FF, C005=01 and renders white.
- Extended the public headless fixture harness with exact full-frame quadrant predicates, and the existing player smoke with 40 per-frame structural checks before digest comparison. The same no-transfer ROM is rejected by the positive player predicate before its digest.
- Added the reproduction checks to the existing `fixture-repro` job. No job, package dependency, third-party fixture, or installed fixture allow-list was added.

## Task Commits

| Task | Name | Commits |
| --- | --- | --- |
| 1 | Original guest and public fixture predicate | `758fe69`, `af88ae4` |
| 2 | Existing player smoke and fixture-repro integration | `e50c43a`, `eb87c27` |

The TDD RED receipts are `build/13-08-task1-red.xml` and `build/13-08-task1-red-evidence.json` (task 1), and `build-player/13-08-task2-red.xml` and `build-player/13-08-task2-red-evidence.json` (task 2). Both evidence checks returned `RED_EVIDENCE_OK`; semantic inspection confirmed the task-specific guest-marker and source-pattern assertions failed before implementation. The source implementation is bounded by ending SHA `eb87c27fb2abfa380342579b6f20eb6398faa30b`.

Machine-readable references to the same task commits above:

1. **Task 1: Recorded execution commits** — `758fe69`, `af88ae4`.
2. **Task 2: Recorded execution commits** — `e50c43a`, `eb87c27`.

## TDD Gate Compliance

Both plan tasks were marked `tdd="true"` and used separate RED and GREEN commits. Task 1's persisted failing CTest report exposed the inherited fixture's missing pass marker before the original guest was added. Task 2's persisted player report failed the structural image predicate against the prior per-line fixture (`144 distinct colours, expected 2`) before switching the player smoke to the original guest. The OpenGSD red-evidence classifier returned `RED_EVIDENCE_OK` for each report, and both predicates passed after their respective implementation commits.

## Files Created/Modified

- `fixtures/cgb-hdma/hblank.asm`, `hblank.gb`, `manifest.json`, and `LICENSE.txt` define the original guest, source-derived pixels, provenance, and rights.
- `tests/scripts/reproduce-cgb-hdma.sh` validates source, ROM, tile data, RGBDS pin, checksummed no-transfer construction, and byte-identical reproduction.
- `tests/test_cgb_hdma.c` runs the original and no-transfer ROMs through the public API and checks guest markers, status bytes, and all 160×144 RGB555 pixels.
- `tests/player/cgb_smoke.cmake`, `tests/player/CMakeLists.txt`, and `tests/player/expected-tests.txt` register the positive and no-transfer player smokes.
- `.github/workflows/fixture-repro.yml` adds the original fixture's three reproduction checks to its existing job.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt`, and `.gitignore` wire the headless test and fixture binary into their existing inventories and fixture allow-list.

## Decisions Made

The player API does not expose guest WRAM markers, so the headless harness owns CPU marker and transfer status assertions. The player uses the same checked-in guest and verifies the source-derived output through the existing `--smoke-colour` frame path. This is software automation using SDL's dummy audio driver; it is not a hardware or perceptual display claim.

The source keeps the LCD active from the bootless profile and relies on the documented zeroed tile/map state for its white failure control. This lets the existing one-frame player smoke capture a completed frame without changing the player or adding another UI path.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Missing prerequisite contract] Extended the existing public fixture harness with structural marker and pixel checks.**

- **Found during:** Task 1
- **Issue:** The inherited `--fixture` path did not yet assert this plan's original guest markers and source-derived tile pattern. Its RED run against the earlier per-line fixture failed with `fixture guest marker expected=A5 actual=00`.
- **Fix:** Added exact C000-C005 assertions, complete RGB555 frame checks, and the named no-transfer failure predicate to the existing harness. The parent authorized this narrow prerequisite fix and expanded file ownership; it touched no core or unrelated UI code.
- **Files modified:** `tests/test_cgb_hdma.c`, `tests/CMakeLists.txt`, `tests/expected-tests.txt`
- **Verification:** `build/tests/test_cgb_hdma --fixture fixtures/cgb-hdma/hblank.gb --check-controls` passes for the original guest and rejects the no-transfer twin at stage 1.
- **Committed in:** `af88ae4` and `eb87c27`

**Total deviations:** 1 Rule 3 prerequisite fix. **Impact:** Necessary to prove the plan's existing public-harness acceptance; scope remained within the fixture and test registrations.

## Issues Encountered

- The system SDL3 was 3.4.10, while this player build requires 3.4.18. Reused the project's existing `build/phase3-player/prefix` cache; no install or dependency change was made.
- The reproduction script's default user-cache location was outside the writable project. Ran `--compare-pinned` with the already verified archive path and its digest set in the supported environment variables.

## User Setup Required

None. No hardware, credentials, or additional package installation is required.

## Next Phase Readiness

Phase 13 plan 13-08 is complete. Next is Phase 13 wave 5 plan 13-05, Bounded runtime mutation sensitivity and inherited anchors, via `/gsd-execute-phase 13 --wave 5`. CGB-07 remains open for Phase 13 closeout. Phase 14, CGB-E Model Qualification and Corpus, remains unstarted. Both workflow auto-advance flags remain false.

## Self-Check: PASSED

All five required fixture/script files exist, all four task commits are ancestors of the current implementation head, and `summary_coverage` passes for the new block.

---
*Phase: 13-cgb-hdma*
*Completed: 2026-10-14*
