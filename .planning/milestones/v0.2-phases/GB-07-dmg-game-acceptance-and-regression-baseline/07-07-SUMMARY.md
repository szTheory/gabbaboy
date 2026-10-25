---
phase: 07-dmg-game-acceptance-and-regression-baseline
plan: 07
subsystem: testing
tags: [acceptance, digest, sha256, ppm, pcm, observe, libbet, regression]

requires:
  - phase: 07-03
    provides: D-19(i) mixer fix (D-027); PCM digests are recorded only after it
  - phase: 07-17
    provides: D-19(ii) outcome (D-028); Libbet joypad path unchanged
  - phase: 07-06
    provides: case-file rejection hardening the runner path builds on
provides:
  - Canonical frame digest (GBB-RGB888-v1), PPM writer, PCM digest and window statistics in src/accept/digest.c
  - Libbet run records title/play_start/mid/hit checkpoints, rolling frame digest and whole-stream PCM digest
  - Runner --observe (sorted key<TAB>value), --failure-dir, and observe-only --input-script/--frame-digest-at/--pcm-digest/--dump-checkpoints
  - Independent stdlib digest vector check (acceptance_digest_vectors)
affects: [07-08, 07-09, 07-10, 07-15]

status: complete
actuals:
  tokens: 11800
  tasks: 2
  commits: 4
plan_head_before: b81c2676fb8a22d9339b8ee8260fb306d5ca4e47
plan_head_after: 5cf0f82b9236cba9d25dd87d752f86ada997e2c8

tech-stack:
  added: []
  patterns:
    - "Hash only explicitly serialized buffers (header + RGB bytes, little-endian int16 PCM); binary file modes only"
    - "All run state in one heap run_state per process; callbacks on gbb_accept_drive, no globals"
    - "Hit frame resolved from a 3-frame ring because T_hit is known one boundary late"

key-files:
  created:
    - src/accept/digest.c
    - tests/test_acceptance_digest.c
    - tests/scripts/rgb-digest-vector.py
  modified:
    - src/accept/gbb_accept.h
    - src/runner/acceptance.c
    - src/runner/acceptance.h
    - src/runner/main.c
    - CMakeLists.txt
    - tests/acceptance/CMakeLists.txt
    - tests/expected-tests.txt
    - .planning/context/DECISIONS.md

key-decisions:
  - "D-029: Libbet structure gate is >=2 distinct shades for title/play_start and >=3 for mid/hit, because the pinned title screen is 1-bit text (refines D-25)"
  - "PCM window = stepping calls that start at or after the play_start mark; the run keeps stepping 1 s (GBB_ACCEPT_TAIL_HALF_DOTS) past T_hit so the window ends at T_hit+1 s"

requirements-completed: [GAME-02, EVID-01]

coverage:
  - id: D1
    description: "Canonical RGB frame digest, PPM bytes and LE PCM digest equal an independent python3 -I hashlib computation; invalid shades rejected without output"
    requirement: EVID-01
    verification:
      - kind: unit
        ref: "ctest -R '^acceptance_digest_vectors$' (python3 -I tests/scripts/rgb-digest-vector.py --check build/tests/test_acceptance_digest --ppm build/digest-vector.ppm)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Libbet case records title/play_start/mid/hit frame digests, rolling digest, PCM digest and window statistics, gated by structure and non-silence checks"
    requirement: GAME-02
    verification:
      - kind: integration
        ref: "ctest -R '^acceptance_libbet$' (receipt regex requires frame_hit= and pcm_sha256=)"
        status: pass
    human_judgment: false
  - id: D3
    description: "--observe surface prints sorted key/value observations, deterministic across runs; unwritable failure directory is exit 2 before guest work"
    requirement: EVID-01
    verification:
      - kind: integration
        ref: "ctest -R '^acceptance_(libbet_observe|failure_dir_unwritable)$'"
        status: pass
    human_judgment: false

duration: 75min
completed: 2026-10-10
---

# Phase 7 Plan 07: Canonical frame and PCM digests, --observe surface Summary

**The Libbet acceptance case now records four checkpoint frame digests, a rolling digest over every completed frame and a whole-stream PCM digest (all over explicitly serialized bytes), gates on structure and non-silence, and exposes everything through a sorted `--observe` surface; the digest definitions are confirmed by an independent stdlib python computation.**

## Performance

- **Tasks:** 2 (Task 1 tracer, Task 2 TDD-flagged auto)
- **Files:** 3 created, 8 modified
- **Commits:** 4 (RED test, tracer GREEN, vector test, decision record) plus the SUMMARY/state commit

## Accomplishments

- `src/accept/digest.c`: `GBB_ACCEPT_RGB_HEADER` ("GBB-RGB888-v1 160x144\n", length by `sizeof - 1`), `gbb_accept_rgb_digest` (+ `_bin`), `gbb_accept_write_ppm` (`wb`, checks every fwrite/fclose, nothing created for an invalid shade), `gbb_accept_frame_distinct_shades`, `gbb_accept_pcm_digest_*` (L low, L high, R low, R high via `uint16_t`), `gbb_accept_pcm_stats_*` with `GBB_ACCEPT_PCM_MIN_PEAK_TO_PEAK` 2048 and `GBB_ACCEPT_PCM_MIN_CHANGES` 4800.
- Runner (`src/runner/acceptance.c`): after-step callback copies the frame and tracks `gbb_frame_info.generation` (delta 1 = new frame; larger = `frame-skipped`, exit 3); boundary callback learns T_hit and resolves the hit frame from a 3-frame ring; a pending checkpoint at run end is `checkpoint-not-ready` (never a zero frame); `checkpoint-structure` and `pcm-silent` gates; receipt gains `frame_<label>`, `frame_rolling`, `pcm_sha256` and the four window statistics.
- `--failure-dir` probe-writes `.gbb-write-probe` before guest work (`failure-dir-unwritable`, exit 2) and writes `<id>.ppm` of the newest frame on any exit-1 outcome (verified with a short-budget scratch case file: `predicate-not-reached`, valid P6 header). `--observe` plus `--input-script`, `--frame-digest-at`, `--pcm-digest`, `--dump-checkpoints`; the observe-only flags are rejected without `--observe` (pulled forward from Plan 07-08, exit 2).
- Observed Libbet values (DMG-CPU-B software model, regression class, after the D-027 mixer fix): T_hit 125841408 half-dots; frame digests title `8097d8c7...`, play_start `3d9c9f27...`, mid `a07a58d6...`, hit `fb5e3bc3...`; rolling `3c08f4dc...`; PCM `3d051cb0...`; window peak-to-peak 20290 on each channel, 164822 changes each (thresholds 2048 / 4800 met). Two consecutive `--observe` runs are byte-identical.
- Independent check: `rgb-digest-vector.py` rebuilds the synthetic frame (shade = (x + 2y) % 4, stored at padded pitch with invalid padding bytes), PPM bytes and PCM vector (-1,258),(32767,-32768),(0,1) with hashlib and matches the C helper exactly.

## TDD Gate Compliance

- **RED (Task 1):** `e64b522` registered the tests first. Run result before implementation: `acceptance_libbet` failed on the planned assertion (receipt lacked `frame_hit=`/`pcm_sha256=`), `acceptance_libbet_observe` and `acceptance_failure_dir_unwritable` exited 2 with `invalid-arguments` (unknown flags). Semantic assessment: the target tests ran and failed for the planned reason (missing behavior), no setup or syntax fault.
- **GREEN (Task 1):** `80fa32d`; the three target tests pass.
- **Task 2 RED not observable:** the plan orders `digest.c` (Task 1) before the vector test, so the vector test passed on its first run (unexpected green, investigated: the implementation already existed). Substitute evidence: three scratch mutations of `digest.c` (shade map 170 to 171, PCM low byte replaced by high byte, header length minus 2) each made `acceptance_digest_vectors` fail with the specific mismatch; the file was restored with `git checkout -- src/accept/digest.c`. Commit `5f16ffb` is therefore a `test(...)` commit with no separate `feat`. REFACTOR: none.

## Deviations from Plan

**1. [Rule 1 - Bug] D-25 "at least 3 distinct shades" is impossible for the pinned title and play_start frames**
- **Found during:** Task 1 (first full Libbet run failed `checkpoint-structure`)
- **Issue:** Inspected the `--dump-checkpoints` PPMs: title is 1-bit text (shades 0 and 255), play_start is a 2-shade transition frame; mid and hit have 4 shades. A literal 3-shade rule fails correct output.
- **Fix:** `MIN_CHECKPOINT_SHADES_SCREEN` 2 (title, play_start, other labels) and `MIN_CHECKPOINT_SHADES_GAMEPLAY` 3 (mid, hit); `hit != title` unchanged. Recorded as D-029 in DECISIONS.md. Moving script marks was rejected (changes the pinned input digest).
- **Files modified:** src/runner/acceptance.c, .planning/context/DECISIONS.md
- **Commits:** 80fa32d, 5cf0f82

**2. [Rule 3 - Blocking] Plan acceptance path for the digest helper binary**
- The criterion names `build/test_acceptance_digest`; the binary is `build/tests/test_acceptance_digest`. The criterion was run with the real path and exits 0.

**3. [Rule 2 - Missing critical] Rejecting observe-only flags without --observe**
- Plan assigns this to 07-08, but silently ignoring `--input-script` and friends would let a non-pinned script run in a normal-looking invocation, so main.c rejects them now (exit 2, `invalid-arguments`). Plan 07-08 can add its own test.

**Total deviations:** 3 (1 bug, 1 blocking path correction, 1 pulled-forward safety). **Impact:** none on scope; D-025 gate semantics refined with evidence.

## Verification Run

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^acceptance_(libbet|libbet_observe|failure_dir_unwritable)$' --output-on-failure --no-tests=error`: 3/3 pass.
- `ctest --test-dir build -R '^acceptance_digest_vectors$'`: pass; `python3 -I tests/scripts/rgb-digest-vector.py --check build/tests/test_acceptance_digest --ppm build/digest-vector.ppm` exit 0; `--uniform 0` prints 64 hex digits.
- Serial and `ctest -j4 -R '^acceptance_'` pass sets identical (19 tests each); full `ctest -j4` 214/214 pass (inventory check at configure passed).
- Acceptance greps: header literal count 1 in gbb_accept.h; `sizeof(GBB_ACCEPT_RGB_HEADER) - 1u` present in digest.c; `fopen(..., "r|w|a")` count 0 in src/accept and src/runner.

## Known Stubs

None.

## Threat Flags

None. Output paths are the validated case id plus a fixed suffix inside a probe-checked directory (T-07-16); digests hash explicit buffers (T-07-17); the case file is opened `rb` only in every mode (T-07-18).

## Next Phase Readiness

Plan 07-08 can add its own rejection tests for the observe-only flags (already enforced) and the baseline can consume the `--observe` keys. Plan 07-15 can use `--dump-checkpoints` for the D-26 one-time inspection (title/play_start/mid/hit PPMs were already viewed here for the title, play_start and hit frames; the D-26 record itself remains Plan 07-15's job).

## Self-Check: PASSED

- Created files present: src/accept/digest.c, tests/test_acceptance_digest.c, tests/scripts/rgb-digest-vector.py.
- Commits e64b522, 80fa32d, 5f16ffb, 5cf0f82 are ancestors of HEAD; `commits: 4` measured from the ledger (SUMMARY commit follows).
