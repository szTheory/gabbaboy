---
phase: GB-18-player-save-slots-and-host-contract
plan: "02"
subsystem: host-contract
tags: [host, runner, grammar, hostile-input, api-boundary]
requires:
  - phase: GB-18-player-save-slots-and-host-contract
    provides: "18-01 gabbaboy_host library, D-02 grammar, D-07 stem rule, host_fixture.py and test_host_mode.py"
provides:
  - test_host_basename: D-07 accept table and one refusal case per class, linked against gabbaboy_host
  - gbb_host_mutant_library(): single-anchor mutated copy of a host source built as a sibling static library
  - Eleven host_grammar_* CTests, each pinning its own reason token and forbidding "gbb-host: ready"
  - host_cli_stem_refusal and host_windows_refusal harness scenarios
  - cmake/CheckHostApiSymbols.cmake (public-API-only symbol and include check, with GBB_SOURCE_FILES for later plans)
  - cmake/CheckRunnerSourcesQualified.cmake (dirty-list coverage check)
affects: [18-03, 18-04, 18-05, 18-07, 18-08, 18-09]
actuals:
  tokens: 10724
  tasks: 2
  commits: 3
commits: 3
plan_head_before: ddbdc2c32c3029ea1d6f647c0a850c9227d29a87
plan_head_after: 529298896d348b1b52d58495207a50d927b48ae3
tech-stack:
  added: []
  patterns:
    - Mutant library factory builds a sibling of the real archive from one edited source plus the unmodified rest.
    - A CMake -P checker carries its own controls mode and re-runs itself as a child, so no extra script file is needed.
    - A nested -D list uses "|" as the inner separator so expect_exit.cmake does not split it.
key-files:
  created:
    - tests/test_host_basename.c
    - cmake/CheckHostApiSymbols.cmake
    - cmake/CheckRunnerSourcesQualified.cmake
  modified:
    - tests/cmake/host.cmake
    - tests/scripts/test_host_mode.py
    - tests/expected-tests.txt
    - tests/verify_runner_help.cmake
    - src/runner/main.c
    - cmake/ExpectedTests.cmake
    - .github/scripts/verify-test-inventory.sh
key-decisions:
  - "Empty-value is the one grammar case run by the python harness: CMake drops an empty list element, so '--rom \"\"' cannot be written as a CTest command. It stays portable."
  - "The API-surface controls live in the checker itself (controls mode), not in a new driver file, and each control asserts it was rejected for its own token and not the other layer's."
  - "The include denylist also covers gbb_accept_input.h, the private acceptance input seam, beyond the three headers the plan names."
  - "The qualified-sources list is JOIN-ed with '|' so the control can nest it inside GBB_CMD."
requirements-completed: []
coverage:
  - id: D1
    description: "Every D-02 grammar defect (unknown flag, duplicate, empty value, missing value, equals form, acceptance flag, positional, missing rom, missing save dir, bad profile, bad frames) exits 2 with its own invalid-arguments reason token and never prints gbb-host: ready."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^host_grammar_ (ten expect_exit tests plus host_grammar_empty_value harness scenario)"
        status: pass
  - id: D2
    description: "Every D-07 stem class is its own CTest with its own status and reason token, a refused stem never writes the output buffer, and a transform-instead-of-refuse mutant is killed with the FAIL refuse_backslash line at exit 1."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^host_stem_ (accepts, seven refuse_* classes)"
        status: pass
      - kind: unit
        ref: "ctest -R ^host_stem_mutant_transform$"
        status: pass
  - id: D3
    description: "A hostile --rom basename is refused end to end with its own stem token before any filesystem access, and the save directory listing, mtimes and bytes are unchanged."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^host_cli_stem_refusal$ (tests/scripts/test_host_mode.py --scenario stem-refusal)"
        status: pass
  - id: D4
    description: "The Windows gate (D-05) refuses with windows-unsupported on _WIN32 and does not fire on POSIX, where the identical command exits 0 and writes the .sav."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^host_windows_refusal$ (tests/scripts/test_host_mode.py --scenario platform-gate)"
        status: pass
  - id: D5
    description: "gabbaboy_host reaches the core only through the public header: every undefined gbb_ symbol is declared there and no source includes a test-seam or acceptance header; the seeded seam-calling archive and seeded include are each rejected for their own reason."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^host_api_surface$"
        status: pass
      - kind: integration
        ref: "ctest -R ^host_api_surface_controls$"
        status: pass
  - id: D6
    description: "Every runner and host library source is in the GBB_BUILD_QUALIFIED dirty list; a seeded unlisted source is rejected with runner-source-unqualified."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^host_qualified_sources$"
        status: pass
      - kind: integration
        ref: "ctest -R ^host_qualified_sources_control$"
        status: pass
  - id: D7
    description: "Inventory bookkeeping keeps the three POSIX-only names out of the Windows expectation in both lists, runner_help sees the new host usage line, and existing runner and core linkage behaviour is unchanged."
    human_judgment: false
    verification:
      - kind: other
        ref: "bash .github/scripts/verify-test-inventory.sh --self-test"
        status: pass
      - kind: integration
        ref: "ctest -R ^(runner_help|core_linkage_links|no_host_clock)$"
        status: pass
duration: 9min
completed: 2026-10-28
status: complete
---

# Phase 18 Plan 02: Host Grammar, Stem and API-Boundary Negatives Summary

**Every D-02 grammar refusal, D-07 stem class and the D-05 Windows gate is a separately named CTest that pins its own reason token, a stem-transform mutant is killed, and two `-P` checkers enforce public-API-only linkage and dirty-list coverage with seeded controls.**

## Performance

- **Duration:** about 9 min
- **Started:** 2026-10-29T03:01:00Z
- **Completed:** 2026-10-29T03:10:00Z
- **Tasks:** 2
- **Files modified:** 10 (3 created, 7 modified, excluding planning files)

## Accomplishments

- `test_host_basename` links `gabbaboy_host` only. Cases `accepts` and `refuse_{empty,leading_dot,control,del,backslash,bad_utf8,too_long}` each assert the exact status, the reason token and an untouched sentinel-filled output buffer. Each input maps to exactly one token under the first-match rule (`dir/` is stem-empty; `.gb` and `..gb` are stem-leading-dot).
- `gbb_host_mutant_library(name source anchor replacement)` requires the anchor exactly once, writes the mutated file under `host-mutants/<name>/` and builds a sibling archive from it plus the unmodified host sources (taken from the real target's `SOURCES`). `host_stem_mutant_transform` rewrites a backslash to `_` and accepts; `refuse_backslash` fails against it with `FAIL refuse_backslash` at exit 1, while the real library prints `PASS refuse_backslash`.
- Ten expect_exit grammar tests plus the harness `grammar-empty-value` scenario: `unknown-flag`, `duplicate-flag`, `empty-value`, `missing-value`, `equals-form`, `acceptance-flag`, `positional`, `missing-rom`, `missing-save-dir`, `bad-profile`, `bad-frames`. `grep -o 'reason=[a-z-]*' tests/cmake/host.cmake | sort | uniq -d` prints nothing.
- `stem-refusal` harness: 12 hostile ROM names in seven classes, created on disk where the filesystem allows (macOS skips the four invalid-UTF-8 names and the stem check still fires first). Each run asserts exit 2, its stem token, no other stem token, and a snapshot of the save directory (names, mtimes, bytes, directory mtime) equal before and after. A pre-existing `keep.sav` makes a rewritten stem or a clobber visible.
- `platform-gate` harness: POSIX asserts exit 0, an existing `continuation.sav` and no `windows-unsupported`; `os.name == "nt"` asserts exit 2, the token and an empty directory.
- `CheckHostApiSymbols.cmake`: undefined `gbb_*` symbols (nm, leading underscore stripped) must be declared in the public header (comments stripped); sources are scanned for `gabbaboy_test.h`, `gbb_accept.h`, `acceptance.h` and `gbb_accept_input.h` includes regardless of path prefix. `GBB_SOURCE_FILES` lets 18-05 add `src/player/slots.c;src/player/slots.h` without editing the script. Current result: `host-api pass archives=1 symbols=8`.
- `CheckRunnerSourcesQualified.cmake`: whole-entry membership against the `git diff --quiet HEAD --` list; current result `qualified-sources pass sources=7`.
- Runner usage gains `--rom <rom.gb> --save-dir <dir> [--profile dmg|cgb] [--frames <n>]`; `runner_help` checks it as a substring only (D-16).

## Task Commits

1. **Task 1: Grammar, stem and Windows-gate negatives** - `2406746` (test, RED: `runner_help` fails on the missing usage line) then `4c4facf` (feat, GREEN: usage line)
2. **Task 2: D-04 API-surface and dirty-list checks with seeded mutants** - `5292988` (test; the checkers and their controls are the deliverable)

**Plan metadata:** recorded in the following docs commit.

## Files Created/Modified

- `tests/test_host_basename.c` - D-07 accept table and refusal classes
- `tests/cmake/host.cmake` - mutant factory, stem, grammar, API-surface and qualified-source registrations
- `tests/scripts/test_host_mode.py` - `stem-refusal`, `platform-gate`, `grammar-empty-value` scenarios
- `cmake/CheckHostApiSymbols.cmake` - symbol and include layers plus controls mode
- `cmake/CheckRunnerSourcesQualified.cmake` - dirty-list coverage
- `src/runner/main.c`, `tests/verify_runner_help.cmake` - host usage line and its substring check
- `tests/expected-tests.txt`, `cmake/ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh` - 26 new names; `host_cli_stem_refusal`, `host_api_surface` and `host_api_surface_controls` removed from both Windows lists

## Decisions Made

- Windows exclusions are exactly the three tests that need POSIX (`host_cli_stem_refusal`, `host_api_surface`, `host_api_surface_controls`). Grammar, stem, mutant, `host_windows_refusal` and both qualified-source tests are portable.
- The control for each checker layer asserts the other layer's token is absent, so a control cannot pass by failing for an unrelated reason.
- Mutant test uses the base 60 s TIMEOUT like every other new test (D-27); all 26 run in well under a second each.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] CMake cannot pass an empty list element**
- **Found during:** Task 1 (registering `host_grammar_empty_value`)
- **Issue:** `execute_process(COMMAND ${GBB_CMD})` drops empty elements (verified: `echo;--rom;;--x` gives `--rom --x`), so `--rom ""` cannot be encoded in the expect_exit command list the plan prescribes.
- **Fix:** Added harness scenario `grammar-empty-value` (three empty-operand shapes, exit 2, `empty-value`, no ready line, working directory untouched) and registered `host_grammar_empty_value` through `gbb_add_host_mode_test`. It is still portable and still a distinct named test with its own token.
- **Files modified:** `tests/scripts/test_host_mode.py`, `tests/cmake/host.cmake`
- **Commit:** `2406746`

**2. [Rule 1 - Bug] Self-inflicted test input with two tokens**
- **Found during:** Task 1 (first run)
- **Issue:** My second `refuse_backslash` input `dir/..\x.gb` has the stem `..\x`, which the first-match rule classifies as leading-dot, so the case failed with `stem-leading-dot`. The 18-01 code was right; the input was wrong.
- **Fix:** Replaced it with `dir/x\y.gb`. No `src/host/*` change was needed and no 18-01 token defect exists.
- **Commit:** `2406746`

**3. [Process] Controls live in the checker, not a new driver file**
- The plan asks for "a small CMake driver script"; its `files_modified` lists no such file. The driver is the checker's controls mode (re-invoking itself with `-P` as a child), which keeps the declared file set and uses the same code path as the real run. Behaviour matches the plan: two child runs, both required to fail, output `host-api controls pass controls=2`.

**4. [Process] TDD shape for Task 1**
- The accept/refuse tests exercise 18-01's already-correct implementation, so they were green on first run (after fixing deviation 2). The committed RED is `runner_help` failing against the unchanged usage text (`build/18-02-task1-red.log`); the discriminating evidence for the stem tests is the committed transform mutant, which fails exactly as required.

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug), 2 process notes
**Impact on plan:** None on scope. No token defect in 18-01 output; `src/host/*` is unchanged.

## Evidence Recorded for the Acceptance Criteria

- Count: `ctest -N -R '^(host_stem_|host_grammar_|host_cli_stem_refusal$|host_windows_refusal$)'` lists 22 tests.
- Mutant, run directly: `build/tests/test_host_basename_mutant_stem_transform refuse_backslash` prints `refusal mismatch: got=stem-ok(0) expected=stem-backslash(5)` then `FAIL refuse_backslash`, exit 1; the real binary prints `PASS refuse_backslash`.
- Controls log: `host-api-undeclared: gbb_test_force_state_seam_probe` once and `host-api-include: .../include-probe/bad.c (gabbaboy_test.h)` once, then `host-api controls pass controls=2`.
- Dirty-list hand run (scratch copy of CMakeLists.txt with `src/host/host_run.c` removed; log `build/18-02-qualified-hand-run.log`):

  ```
  cmake -DGBB_ROOT_CMAKELISTS=<scratch>/CMakeLists.txt "-DGBB_SOURCES=src/runner/main.c|src/host/host_run.c|src/host/host_basename.c" -P cmake/CheckRunnerSourcesQualified.cmake
  -- runner-source-unqualified: src/host/host_run.c
  CMake Error ... runner sources are missing from the GBB_BUILD_QUALIFIED dirty list   (exit 1)
  ```

  A scratch list holding `a/b_long.c` also rejects `a/b.c`, so membership is by whole entry, not substring.
- Full suite at `5292988` after reconfiguring with `-DGBB_STATE_PIN_BASE_REV=7c1f257dd47fec77380f410b93a488bb1a5695cd`: 1526/1526 passed (1500 from 18-01 plus 26 new). Log: `build/18-02-full-ctest.txt`.

## Issues Encountered

None. The revision-pinned tests were green because the build was reconfigured at the final head before the full run, as 18-01 advised.

## Known Stubs

None.

## Threat Flags

None. T-18-01 (path traversal via `--rom` basename) and T-18-04 (host using core seams) are mitigated as planned; no new surface was added beyond the checkers.

## Next Phase Readiness

- Next plan: 18-03 (it also appends to `tests/expected-tests.txt` and follows this plan). 18-05 can pass `src/player/slots.c;src/player/slots.h` through `CheckHostApiSymbols.cmake` via `GBB_SOURCE_FILES`.
- HOST-01 is still not complete: hostile-file safety (18-04) and closing traceability (18-09) remain.

## Self-Check: PASSED

- FOUND: tests/test_host_basename.c, cmake/CheckHostApiSymbols.cmake, cmake/CheckRunnerSourcesQualified.cmake, tests/cmake/host.cmake, tests/scripts/test_host_mode.py
- FOUND commits: 2406746, 4c4facf, 5292988

---
*Phase: GB-18-player-save-slots-and-host-contract*
*Completed: 2026-10-28*
