---
phase: 07-dmg-game-acceptance-and-regression-baseline
plan: 05
subsystem: testing
tags: [runner, acceptance, case-file, libbet, sha256, heap-rom, ctest]

requires:
  - phase: 07-dmg-game-acceptance-and-regression-baseline
    provides: "Plan 07-02 shared acceptance library (gbb_accept_drive, script parser, predicate, SHA-256) and the Libbet fixture from 07-01"
provides:
  - "gabbaboy_runner_support static library (src/runner/cases.c, acceptance.c), internal and not installed"
  - "Bounded D-20/D-21/D-22/D-28 case-file parser and relative-path validator (src/runner/acceptance.h)"
  - "Runner CLI --acceptance <cases.txt> --case <id> [--receipt] with exit codes 0/1/2/3"
  - "tests/acceptance/cases.txt with the libbet case and the acceptance_libbet CTest"
  - "Heap-backed ROM and manifest buffers on the Mooneye path with unchanged results"
affects: [07-06 digests and parser unit tests, 07-07 applicability, GB-07 baseline]

actuals:
  tokens: 11000
  tasks: 2
  commits: 2

plan_head_before: 6d890377e8b4f33fdffcc70caaa70c73eddb9c82
plan_head_after: b7b13d9efa8e2dc3a8867219a03cbe352a96dc22

tech-stack:
  added: []
  patterns: ["validate every input (script digest and syntax, ROM size and digest, predicate binding and anchors) before creating an instance", "case-file paths resolve against the working directory; acceptance CTests run from the repository root"]

key-files:
  created:
    - src/runner/acceptance.h
    - src/runner/cases.c
    - src/runner/acceptance.c
    - tests/acceptance/cases.txt
  modified:
    - src/runner/main.c
    - tests/test_runner.c
    - CMakeLists.txt
    - tests/CMakeLists.txt
    - tests/acceptance/CMakeLists.txt
    - tests/expected-tests.txt

key-decisions:
  - "The case parser returns a heap gbb_case_list (128 cases about 115 KB) mirroring gbb_accept_script_parse ownership; whole-file limits report line=0"
  - "Frame-digest oracles are parsed and validated here but the run path refuses them with exit 3 reason=unsupported-oracle until the digest plan wires them"
  - "The runner uses tail_half_dots=0: the verdict is T_hit, so no post-hit emulation is spent"
  - "model_pass/model_fail are parsed and checked for overlap only; applicability gating is left to the later plan"

requirements-completed: [GAME-02, EVID-01]

coverage:
  - id: D1
    description: "Libbet acceptance case passes end to end through the runner CLI and the acceptance_libbet CTest"
    requirement: GAME-02
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^acceptance_libbet$'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Bounded case-file parser rejects unknown keys, rtc_policy, rejected oracles, duplicates, bad digests, bad paths, expect_hw_capability other than 0 and model overlap before any case runs"
    requirement: EVID-01
    verification:
      - kind: other
        ref: "ad hoc runner invocations with mutated case lines (each reported invalid-cases: <reason> line=1); dedicated boundary tests arrive in Plan 07-06"
        status: pass
    human_judgment: false
  - id: D3
    description: "Mooneye path holds ROM and manifest buffers on the heap with unchanged runner_*, mooneye_* and tracer_* results"
    requirement: EVID-01
    verification:
      - kind: integration
        ref: "ctest --test-dir build (201 of 201 passed)"
        status: pass
    human_judgment: false

duration: 6min
completed: 2026-10-10
status: complete
---

# Phase 07 Plan 05: Acceptance Runner Entry Point Summary

**Case-file driven `gabbaboy-runner --acceptance` that replays the Libbet tutorial script on the shared stepper and reaches the guest-memory predicate (T_hit 125841408 half-dots), with a bounded parser, digest-checked heap ROM loading and heap-backed Mooneye buffers**

## Performance

- **Duration:** about 6 min (local timestamps; plan start was not recorded with `date`)
- **Completed:** 2026-10-10T23:06:01Z
- **Tasks:** 2
- **Files modified:** 10 (4 created, 6 modified)

## Accomplishments

- `build/gabbaboy-runner --acceptance tests/acceptance/cases.txt --case libbet --receipt` exits 0 and prints `acceptance id=libbet status=pass model=dmg-cpu-b t_hit_half_dots=125841408` (about 2.8 s), plus a `receipt` provenance line with ROM, script and predicate digests.
- Parser enforces the D-21 key whitelist, 64 KiB / 1024 chars per line / 128 cases, strict ASCII (CRLF tolerated), lowercase-hex digests, range-checked numbers, relative-only paths (T-07-05), `expect_hw_capability=0` only, and the D-22 pass/fail overlap rule. Errors read `invalid-cases: <reason> line=<n>` with exit 2.
- Acceptance run checks the script digest, script syntax, ROM size and SHA-256, predicate binding and ROM anchors before `gbb_create` (T-07-08, T-07-09, D-27), then calls `gbb_accept_drive` with the default `gbb_queue_events` delivery and max_batch 64.
- Mooneye `run_one`, `load_case_rom` and the manifest digest check use heap buffers freed on every exit path; the exact 32 KiB check, the pinned `MOONEYE_MANIFEST_SHA256` and the compiled `cases[]` table are untouched (D-20).

## Task Commits

1. **Task 1: Tracer - Libbet acceptance case through the runner and CTest** - `78e4cb2` (feat)
2. **Task 2: D-27 heap ROM and manifest buffers on the Mooneye path** - `b7b13d9` (refactor)

**Plan metadata:** see the docs commit that follows this summary.

## Verification Run

- Tracer gate (`type="tracer"`, automated-only verify): `cmake --preset phase1 && cmake --build --preset phase1 && ctest -R '^(acceptance_|runner_|mooneye_|tracer_)'` gave 30 of 30 passed; verified end to end before expanding to Task 2.
- Task 2 verify: `ctest -R '^(runner_|mooneye_|tracer_|acceptance_libbet$)'` gave 25 of 25 passed.
- Full suite: `ctest --test-dir build` gave 201 of 201 passed.
- `.github/scripts/verify-test-inventory.sh <junit> tests/expected-tests.txt --installed` printed `Verified 201 executed CTest cases; none skipped.` (`--core-only` differs only because this local build also registers the installed_* tests, which is the expected difference for that mode.)
- Acceptance criteria: `grep -c gbb_accept_drive src/runner/acceptance.c` = 4; `grep -c 'MOONEYE_MANIFEST_SHA256 "98a1799b' src/runner/main.c` = 1; `grep -c '^acceptance_libbet$' tests/expected-tests.txt` = 1; `runner_help` passes; `grep -E -c 'uint8_t (rom|manifest_bytes)\[MAX_'` = 0 for both main.c and test_runner.c.
- Negative spot checks (mutated copies of the case line in the scratchpad): rtc_policy, unknown key, screen-text oracle, duplicate key, `expect_hw_capability=1`, `..` path, model in both lists, uppercase digest, oversize rom_size each reported the expected `invalid-cases: <reason> line=1`; a wrong `input_sha256` reported `input-digest-mismatch`; unknown case id exited 2.

## Files Created/Modified

- `src/runner/acceptance.h` - parser, path validator, file reader and run entry points
- `src/runner/cases.c` - bounded case-file parser
- `src/runner/acceptance.c` - run orchestration on `gbb_accept_drive`, receipts, bounded heap file reader
- `src/runner/main.c` - `--acceptance` dispatch, usage line, heap Mooneye buffers
- `tests/test_runner.c` - heap ROM for the induced guest-failure control
- `tests/acceptance/cases.txt`, `tests/acceptance/CMakeLists.txt`, `tests/expected-tests.txt` - libbet case and `acceptance_libbet`
- `CMakeLists.txt`, `tests/CMakeLists.txt` - `gabbaboy_runner_support` library, runner and test_runner links, build-qualification list

## Decisions Made

See key-decisions. Pre-existing choices followed as specified: case-file paths resolve against the working directory and every acceptance CTest sets `WORKING_DIRECTORY` to the repository root; `expect_hw_capability` is kept but only 0 is accepted (Open Question 4).

## Deviations from Plan

None - plan executed exactly as written. Review note required by Task 2 (RESEARCH Pitfall 1): `tests/scripts/verify-phase2-hosted.sh` line 37 only asserts that the watched paths (`src/runner/main.c`, `tests/test_runner.c`, ...) are committed and clean and that they still exist; both still exist, so the script is unchanged.

## Issues Encountered

None. The runner reached the predicate on the first run with the same budget and script as `acceptance_lib_libbet_replay`, so no wiring difference needed fixing.

## Known Stubs

None. Frame-digest oracles are parsed but deliberately refused at run time (`unsupported-oracle`, exit 3); that is an explicit scope boundary for the digest plan, not a placeholder in the Libbet path.

## Threat Flags

None beyond the plan's threat model; T-07-05, T-07-08 and T-07-09 mitigations are implemented as described. Dedicated boundary tests for the parser and path validator are Plan 07-06's work.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 07-06 can unit-test `gbb_cases_parse` and `gbb_cases_path_valid` directly through `acceptance.h` and add digest oracles through the existing `oracle` field.
- No blockers. `.planning/milestone.lock` remains an untracked pre-existing file and was not staged.

---
*Phase: 07-dmg-game-acceptance-and-regression-baseline*
*Completed: 2026-10-10*

## Self-Check: PASSED

- FOUND: src/runner/acceptance.h, src/runner/cases.c, src/runner/acceptance.c, tests/acceptance/cases.txt
- FOUND commits 78e4cb2 and b7b13d9 (ancestors of HEAD)
