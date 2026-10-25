---
phase: 11-cgb-colour-rendering-and-player-colour
plan: 09
subsystem: acceptance-runner-cgb-digest
tags: [rgb555, runner, frame-digest, d-43, d-15, controls]
requires:
  - phase: 11-cgb-colour-rendering-and-player-colour
    provides: "11-07 gbb_accept_rgb555_* helpers, 11-08 fixtures"
provides:
  - "Runner CGB frame-digest path: RGB555 capture, GBB-RGB555LE-v1 digest, frame555/observed555 keys, RGB555 failure PPM"
  - "tests/acceptance/cases-cgb-colour.txt with cgb-colour-hblank, a flipped-digest control and a CGB progress-refusal control"
  - "rgb-digest-vector.py --rgb555 and acceptance_digest_rgb555_vectors"
affects: [11-10, 11-11]
requirements-completed: []
actuals:
  tokens: 14000
  tasks: 3
  commits: 3
coverage:
  - id: C1
    description: "A CGB frame-digest case runs through the runner on the CGB profile, captures through gbb_copy_frame_rgb555 and prints an RGB555-labelled digest under frame555, identically for --model cgb-cpu-e and --profile cgb"
    requirement: CGB-04
    human_judgment: false
    verification:
      - kind: integration
        ref: "acceptance_cgb_colour_hblank"
        status: pass
      - kind: integration
        ref: "acceptance_cgb_colour_hblank_profile_flag"
        status: pass
  - id: C2
    description: "The CGB runner path can fail and refuse: the wrong model is excluded, a flipped reference digest fails with reason frame-mismatch and a fresh 69135-byte RGB555 PPM, and a CGB progress-predicate run reports frame-unsupported-profile"
    requirement: CGB-04
    human_judgment: false
    verification:
      - kind: integration
        ref: "acceptance_cgb_colour_excluded_dmg"
        status: pass
      - kind: integration
        ref: "acceptance_cgb_colour_flipped_ppm"
        status: pass
      - kind: integration
        ref: "acceptance_cgb_colour_progress_refused"
        status: pass
  - id: C3
    description: "The RGB555 digest, padding independence, 0x8000 rejection with nothing written, channel expansion and PPM bytes agree with an independent Python implementation"
    requirement: CGB-04
    human_judgment: false
    verification:
      - kind: unit
        ref: "acceptance_digest_rgb555_vectors"
        status: pass
      - kind: other
        ref: "python3 -I tests/scripts/rgb-digest-vector.py --rgb555"
        status: pass
  - id: C4
    description: "DMG digest format, receipts and the frozen baseline are byte-identical"
    human_judgment: false
    verification:
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh"
        status: pass
      - kind: unit
        ref: "acceptance_digest_vectors"
        status: pass
status: complete
commits: 3
plan_head_before: 41e9f94697483bcdd580713884b00f8b3e558b56
plan_head_after: bd9b35f2996472af9282f951f3c6599276b333a7
duration: 25 min
completed: 2026-10-12
---

# Phase 11 Plan 09: Runner RGB555 digests for CGB frame cases Summary

The acceptance runner now captures CGB-profile frames through `gbb_copy_frame_rgb555`, digests them under the distinct `GBB-RGB555LE-v1` label and prints them as `frame555` / `observed555`, with controls proving the path can fail and an independent Python vector checking the digest format.

## Accomplishments

- `src/runner/acceptance.c` chooses the store from `gbb_get_info` profile (never a flag). The DMG code path, header label and output text are untouched. `gbb_ldbb_capture` gains append-only `pixels555` and `format` members.
- `cgb-colour-hblank` (frame-digest@t=1535808, the completion of the eleventh frame) passes with `frame555=abb528b8...9546`, the digest already pinned and independently recomputed in 11-07. Both `--model cgb-cpu-e` and `--profile cgb` give the same pass line.
- Controls: `dmg-cpu-b` is excluded (exit 4); the flipped digest exits 1 with `observed555=` and writes a 69135-byte RGB555-expanded PPM; a CGB progress-predicate run exits 3 with `frame-unsupported-profile` instead of silently observing no frames.
- `rgb-digest-vector.py --rgb555` computes the digest, `expand5` table and PPM independently; `acceptance_digest_rgb555_vectors` compares them with the C helpers, including a 400-byte pitch with 0xFFFF padding and a 0x8000 pixel.

## Task Commits

1. Task 1 (tracer): runner CGB frame-digest path and hblank case - `31fa7d2`
2. Task 2: runner controls - `6449ef2`
3. Task 3: independent RGB555 vectors - `bd9b35f`

## Files Created/Modified

- `src/runner/acceptance.c`, `src/runner/acceptance.h` - CGB capture branch, RGB555 failure PPM, explicit refusal
- `tests/acceptance/cases-cgb-colour.txt` (new), `tests/acceptance/CMakeLists.txt`, `tests/expected-tests.txt`
- `tests/scripts/rgb-digest-vector.py`, `tests/test_acceptance_digest.c`

## Decisions Made

- The CGB progress refusal fires on the first observation step rather than at the first completed frame; it is equally explicit and cheaper. The run still consumes its budget before reporting (exit 3, about 4 s).
- `--rgb555` with no further arguments prints the digest; `--rgb555 --check <exe> --ppm <path>` runs the comparison.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Verification

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`: 663/663 passed.
- `bash tests/scripts/verify-dmg-baseline.sh`: baseline status=pass, no extra keys; `git diff` of `tests/acceptance/cases.txt` and `tests/baseline` is empty.
- `phase1-asan` is Linux-only and runs in CI on the pushed branch.

## Known Stubs

None.

## Threat Flags

None. T-11-38 mitigations in place: distinct header and keys, profile-derived store, excluded-model and flipped-digest controls, independent vector.

## Next Phase Readiness

Plan 11-10 can reuse the `cases-cgb-colour.txt` pattern for further CGB frame cases.

## Self-Check: PASSED

Commits 31fa7d2, 6449ef2 and bd9b35f are ancestors of HEAD; `tests/acceptance/cases-cgb-colour.txt` exists.
