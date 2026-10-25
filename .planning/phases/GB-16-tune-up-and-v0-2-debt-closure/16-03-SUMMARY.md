---
phase: 16-tune-up-and-v0-2-debt-closure
plan: "03"
subsystem: ci-budget
tags: [test-budget, timeout-ratchet, asan-shard, nightly-asan, stall-replay, tune-04, workflow-policy]
requires:
  - phase: 16-01
    provides: tests/cmake/areas.cmake hook and the no_phase_paths expect_exit registration pattern
  - phase: 16-02
    provides: D-108 (D-19 implementation amendments), the perf-gate job wiring in ci.yml and the policy script
provides:
  - verify-test-budget.py, a per-test TIMEOUT ratchet over ctest json-v1 with a base-commit allowlist comparison and base-commit ref resolution
  - tests/ci/test-budget-allowlist seeded from fresh json-v1 scans (78 rows, 11 of them player_*)
  - A default-budget sweep that gives every untimed test in tests/ and tests/player an explicit 60 s TIMEOUT before sanitizer scaling
  - acceptance_stall_diagnosis as a byte comparison over two parallel single-replay tests, plus acceptance_stall_bounded with a digest-pinned short-budget drop:START case
  - v02_consumer_controls split into _c and _cpp halves
  - nightly-asan.yml (schedule and dispatch, read-only replay job, separate report-red job) judged by check_nightly()
  - Sanitizer timeout policy temp-dir hygiene with an assert-clean mode and a negative control
affects: [16-04, 16-06, 16-07]
actuals:
  tokens: 21805
  tasks: 3
  commits: 4
commits: 4
plan_head_before: 8738d07e61cf50bc3cb297c50b3ebe690112ebbe
plan_head_after: 337c170f7954ae3e5145b329f50cbfbcf6b708c7
tech-stack:
  added: []
  patterns:
    - A static ratchet compares an allowlist with git show of the base commit and resolves every justification at the base only, so a change cannot certify itself.
    - One DIRECTORY TESTS sweep per CMake scope gives untimed tests an explicit base TIMEOUT that the sanitizer scaler then multiplies.
    - A long self-test is partitioned by CTest fixture-style halves, with a guard that fails when a test method is unclassified.
    - A red-report job holds the only write token and has no checkout, so the job that runs tested code stays read-only.
key-files:
  created:
    - tests/scripts/verify-test-budget.py
    - tests/ci/test-budget-allowlist
    - tests/data/stall-bounded-cases.txt
    - .github/workflows/nightly-asan.yml
  modified:
    - tests/CMakeLists.txt
    - tests/player/CMakeLists.txt
    - tests/acceptance/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/scripts/verify-stall-report.py
    - tests/scripts/verify-v02-consumers.py
    - tests/scripts/verify-cgb-corpus-inventory.py
    - tests/check_sanitizer_timeout_policy.cmake
    - .github/scripts/verify-release-gates.sh
    - .github/scripts/verify-workflow-policy.py
    - .github/workflows/ci.yml
    - .gitattributes
key-decisions:
  - The budget checker divides TIMEOUTs by 3 when CMakeCache.txt has GABBABOY_ENABLE_SANITIZERS=ON, so one allowlist serves the normal and the ASan build (the test_budget CTest also runs in the ASan tests shard).
  - A push that creates a branch or tag (all-zero github.event.before) is judged against git merge-base HEAD origin/main; an empty or unresolvable base still fails closed.
  - Every seeded row cites GB-CI-004, which exists at the origin/main base, so first seeding resolves its refs at the base (T-16-08).
  - The v02 consumer split partitions test methods between halves (static controls in both); the driver itself still builds both languages, and a guard fails on any unclassified test.
requirements-completed: ["TUNE-04"]
coverage:
  - id: D1
    description: "The per-test TIMEOUT ratchet fails a test over 60 s without an allowlist row, a test with no TIMEOUT, a test over its ceiling, a stale or expired row, a raised ceiling, an unresolvable or head-only ref and an unreadable base, and passes the exact boundaries; the real 1202-test inventory passes."
    requirement: "TUNE-04"
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-test-budget.py --self-test"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build -R '^test_budget'"
        status: pass
  - id: D2
    description: "Every test in the phase1 build and in a player-enabled build has an explicit TIMEOUT after the default-budget sweep (596 of 1194 and 81 of 98 player tests were untimed before)."
    requirement: "TUNE-04"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build --show-only=json-v1 (zero tests without TIMEOUT in phase1 and in a GABBABOY_BUILD_PLAYER=ON build)"
        status: pass
  - id: D3
    description: "ci.yml native-linux runs the ratchet with --base from the PR base or push parent, and the workflow policy rejects a variant that drops --base."
    requirement: "TUNE-04"
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --self-test"
        status: pass
  - id: D4
    description: "acceptance_stall_diagnosis keeps its frozen name and compares two parallel single-replay tests through the gbb_stall_full fixture; acceptance_stall_bounded replays drop:START at 50561280 half-dots from a SHA-256 pinned case file, still fails with predicate-not-reached and produces a deterministic report and PPM; dmg_baseline is unchanged and green."
    requirement: "TUNE-04"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R '^(acceptance_stall_diagnosis|acceptance_stall_diagnosis_replay_1|acceptance_stall_diagnosis_replay_2|acceptance_stall_bounded|dmg_baseline)$'"
        status: pass
      - kind: unit
        ref: "python3 -I tests/scripts/verify-stall-report.py --self-test"
        status: pass
  - id: D5
    description: "The PR ASan acceptance shard excludes the three full stall tests, its expected-shard slice drops the same names, and the policy and corpus inventory pins carry the exact new lines; two new mutations (shard keeps the full replay, shard excludes the bounded test) are rejected."
    requirement: "TUNE-04"
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --self-test"
        status: pass
      - kind: unit
        ref: "python3 -I tests/scripts/verify-cgb-corpus-inventory.py --ci-contract"
        status: pass
  - id: D6
    description: "v02_consumer_controls is split into v02_consumer_controls_c and v02_consumer_controls_cpp through --consumer, the release-gates required list names both, and a guard rejects an unclassified self-test."
    requirement: "TUNE-04"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R '^v02_consumer_controls_(c|cpp)$'"
        status: pass
      - kind: unit
        ref: "bash .github/scripts/verify-release-gates.sh --self-test"
        status: pass
  - id: D7
    description: "nightly-asan.yml triggers on schedule and workflow_dispatch only; the replay job is read-only with the exact ctest line, and report-red alone holds issues: write with no checkout; check_nightly() rejects an extra trigger, a write permission on the replay job, a checkout in the report job and a dropped ctest filter."
    requirement: "TUNE-04"
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --check"
        status: pass
      - kind: unit
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --self-test"
        status: pass
  - id: D8
    description: "The sanitizer timeout policy sweeps stale probe directories, removes its own on success and keeps it on failure; assert-clean mode passes after a pass and a seeded leftover directory makes it fail."
    requirement: "TUNE-04"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R '^sanitizer_timeout_policy_(selftest|temp_clean|temp_clean_control)$'"
        status: pass
  - id: D9
    description: "The full phase1 CTest suite passes at the final head with no src/ or include/ change and the frozen DMG baseline file untouched."
    requirement: "TUNE-04"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error"
        status: pass
duration: 150min
completed: 2026-10-24
status: complete
---

# Phase 16 Plan 03: CI Budget Ratchet, Stall-Replay Sharding and Nightly ASan Summary

**A static per-test TIMEOUT ratchet over ctest json-v1 (78 seeded rows, base-commit ref resolution), a PR ASan lane that keeps the drop:START negative control on a tenth of the libbet budget while the full replays move to a read-only scheduled nightly lane with a separate red-report job, and temp-dir hygiene with a negative control.**

## Performance

- **Duration:** about 150 min
- **Tasks:** 3 (plus one fix commit)
- **Files:** 16 changed (1004 insertions, 82 deletions)
- **Local-only:** nothing was pushed. The orchestrator owns the PR, the rebase onto main after PR #105, and every hosted item below.

## Fresh json-v1 scan counts

All scans configured into an empty scratch directory at the plan head, before the sweep.

| Build | Tests | Untimed before sweep | Explicit TIMEOUT above 60 | After sweep untimed |
| --- | --- | --- | --- | --- |
| phase1 (Debug, Ninja) | 1194 | 596 | 65 (4 at 90, 24 at 120, 6 at 180, 5 at 240, 21 at 300, 1 at 400, 2 at 600, 1 at 900, 1 at 1200) | 0 |
| player-enabled (Release, pinned SDL3 prefix) | 1292 (98 player_*) | 81 of the 98 player tests | 11 (8 at 120, 1 at 240, 2 at 300) | 0 (1294 total, 98 player_*) |

The phase1 total is 1194 rather than the planning-time 1183 because 16-02 registered perf_gate_* and perf_attribution* tests. The full suite is now 1202 tests after this plan's additions.

Allowlist: 78 data rows, 67 non-player and 11 player_*. After Task 2 the rows for `acceptance_stall_diagnosis` (now 60 s) and `v02_consumer_controls` were replaced by `acceptance_stall_diagnosis_replay_1`, `_2` (600 s each) and `v02_consumer_controls_c`, `_cpp` (600 s each). Every row cites `GB-CI-004`, expires at project minor 0.4, and resolves at the `711f4fd` base.

## Accomplishments

- **Ratchet (Task 1).** `tests/scripts/verify-test-budget.py` rejects over-budget (including no TIMEOUT), over-ceiling, stale-row, row-expired, ceiling-raised and ref-unresolved, plus malformed and duplicate rows, a vacuous inventory and an unreadable base. Self-test: 34 controls. Real inventory: `test-budget pass tests=1202 allowlisted=78 player_rows_skipped=11`. Run against the base `711f4fd` for both builds.
- **Default budget sweep.** One `DIRECTORY TESTS` sweep in `tests/CMakeLists.txt` (covering the included acceptance scope) and the same sweep in `tests/player/CMakeLists.txt`, each before its `gbb_scale_sanitizer_test_timeouts()` call, with `GBB_DEFAULT_TEST_TIMEOUT_SECONDS` set before `add_subdirectory(player)`. No previously untimed test failed on timeout in the full run.
- **CI step.** `ci.yml` native-linux resolves the base (PR base, push parent, or `git merge-base HEAD origin/main` for an all-zero parent) and runs the checker with `--base "$BUDGET_BASE"`; `CI_BUDGET_COMMANDS` pins the line and a mutation that drops `--base` is rejected.
- **Stall sharding (Task 2).** `verify-stall-report.py` gained `--replay N` and `--compare DIR1 DIR2`. `acceptance_stall_diagnosis_replay_1/_2` set up fixture `gbb_stall_full` (TIMEOUT 600, COST 600), and `acceptance_stall_diagnosis` (TIMEOUT 60) compares them. Measured locally in a Debug build: each full replay about 31 s, the bounded case about 3 s per replay.
- **Bounded PR replay.** `tests/data/stall-bounded-cases.txt` is `cases.txt` line 1 with `budget_half_dots=50561280` (a tenth of 505612800), pinned by SHA-256 `ed65d0082979f5e87260adddcf3b6f2cb1ca93b713400999d71ad8b3e7535f5b` in `tests/acceptance/CMakeLists.txt`. It ends `predicate-not-reached` under `drop:START` with an FF00 write in the report and a 104-record trace, with no `src/` change.
- **Shard lines.** The acceptance shard runs `-R '^acceptance_' -E '^acceptance_stall_diagnosis(_replay_[12])?$'` and its expected slice drops the same names; `CI_SANITIZER_SHARDS`, `verify-cgb-corpus-inventory.py` and the existing acceptance-shard mutation were updated together. The `ci_asan_parallel_*` and `ci_floor_parallel_*` contracts check phrases that did not change, and they pass.
- **Consumer split.** `--self-test --consumer {c,cpp}` runs 11 static controls plus 4 heavy tests per half (15 each, 3 and 4 positives); `verify-release-gates.sh` lists both names and its self-test count says twelve contracts.
- **Nightly (Task 3).** `nightly-asan.yml` (cron `17 3 * * *` and dispatch), `asan-full-replay` (ubuntu-24.04, clang-18, 60 minutes, `ctest --preset phase1-asan --parallel 2 -R '^acceptance_stall_diagnosis(_replay_[12])?$'`) and `report-red` (needs the replay, `if: failure()`, `issues: write` only, no checkout, `gh issue` list/create/comment on one issue titled "nightly-red: asan-full-replay"). The header cites D-108. This closes LIM-ASAN-STALL-TIMING by D-19 (record for 16-06; the green dispatched run is still pending).
- **Hygiene (D-23).** The policy script sweeps stale `sanitizer-timeout-policy-*` siblings, removes its own nonce directory only after the last assertion, and has `GBB_POLICY_MODE=assert-clean`. `sanitizer_timeout_policy_temp_clean` (DEPENDS the selftest) passes, and `sanitizer_timeout_policy_temp_clean_control` proves a seeded leftover directory fails.

## Task Commits

| Task | Commit | Title |
| --- | --- | --- |
| 1 | 9f543a1 | test(16-03): add per-test TIMEOUT ratchet with default budget sweep and base-pinned CI step |
| 2 | 4f34258 | ci(16-03): shard the stall replay, add the bounded PR replay and split consumer controls |
| 3 | 3ae31ca | ci(16-03): add nightly full ASan stall replay with a separate red report job and temp-dir hygiene |
| fix | 337c170 | test(16-03): restore core_linkage arguments and keep budget fixtures off the live phases path |

Base used for local ratchet runs: `--base 711f4fd` (the origin/main commit PR #105 sits on). The first-seeding case applies: the allowlist is absent at that base, and all 78 refs resolved there.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] --ctest edit reached core_linkage registrations**
- **Found during:** full CTest after Task 3
- **Issue:** adding `--ctest ${CMAKE_CTEST_COMMAND}` to the test_budget registration by string replacement also rewrote the two `core_linkage_*` registrations, whose script rejects `--ctest`.
- **Fix:** restored those two lines; `core_linkage_links` and `_controls` pass.
- **Commit:** 337c170

**2. [Rule 1 - Bug] Fixture paths tripped the phase-path lint**
- **Found during:** full CTest after Task 3
- **Issue:** the budget self-test fixtures spelled the live phases directory, which `no_phase_paths` rejects.
- **Fix:** fixtures use the accepted archived-milestone spelling; the lint passes with its allowlist unchanged.
- **Commit:** 337c170

**3. [Rule 2 - Missing critical] All-zero push parent**
- **Found during:** Task 1 (CI step)
- **Issue:** the plan fails closed on an all-zero `github.event.before`. ci.yml also triggers on `push`, so every first push of a new branch or tag would turn red and the duplicate check name could confuse the required-check gate.
- **Fix:** an all-zero parent resolves to `git merge-base HEAD origin/main`; an empty or unresolvable base still fails (`git cat-file -e` under errexit, then the checker's own base-unreadable rejection).
- **Commit:** 9f543a1

**4. [Rule 2 - Missing critical] .gitattributes rule for the new digest-pinned file**
- **Issue:** a hosted Windows checkout would convert `tests/data/stall-bounded-cases.txt` to CRLF and break its SHA-256 pin (lesson from an earlier wave). `.gitattributes` is outside `files_modified`.
- **Fix:** added `tests/data/stall-bounded-cases.txt text eol=lf`.
- **Commit:** 4f34258

**5. [Rule 2 - Missing critical] Sanitizer scale in the budget checker**
- **Issue:** `test_budget` also runs in the ASan tests shard where TIMEOUTs are scaled by 3, which would read as over budget.
- **Fix:** the checker divides by 3 when `GABBABOY_ENABLE_SANITIZERS` is ON in the cache. This is unit-tested only: ASan configuration is Linux-only and could not be exercised on this macOS host, so the hosted ASan tests shard is the real check.
- **Commit:** 9f543a1

**6. Added tests and a policy mutation beyond the plan list**
- `sanitizer_timeout_policy_temp_clean_control` (negative control for the assert-clean mode) and the matching expected-tests names; the plan's 15-file scope grew by `.gitattributes` and one more registration only.

**7. Consumer split is by test method, not by driver language**
- The plan's wording ("one language's relocated build") would need the verifier driver to restrict languages, which would weaken the real qualification path. The halves partition the self-test methods instead; both halves still build both languages inside the driver. The split cuts wall-clock because each half is about half the heavy tests (local: 24 s and 30 s in parallel, against 50 s serial).

**Total deviations:** 7 (2 bug fixes, 3 missing-critical additions, 2 interpretation notes). **Impact:** none on the plan's intent; the CI step and sanitizer scale are the two pieces whose real behavior only hosted runs can confirm.

## Known Stubs

None.

## Pending hosted follow-ups (orchestrator)

Nothing below is claimed as done.

1. **Rebase and PR.** After PR #105 squash-merges, rebase these four commits plus the SUMMARY/state commits onto main and open the 16-03 PR. Titles use test/ci/chore/docs only (D-03). Note: `ci.yml` was edited by 16-02 and 16-03; expect conflicts only if #105 changed the same hunks.
2. **PR exact-head required checks all green.** Look specifically at:
   - native-linux: step "Resolve the per-test budget base commit" (output `base=` is the PR base SHA) and step "Check per-test TIMEOUT budgets against the base allowlist" printing `test-budget pass tests=... allowlisted=78 player_rows_skipped=11`; the full CTest stream must also pass `test_budget`, `test_budget_controls`, `acceptance_stall_diagnosis*`, `v02_consumer_controls_c/cpp`, `sanitizer_timeout_policy_temp_clean*`, and the inventory check must accept the expected-tests changes.
   - native-macos and native-windows: the same CTest names in their inventories; Windows must pass the SHA-256 pin of `tests/data/stall-bounded-cases.txt` (the new `text eol=lf` rule) and the budget tests (the new tests are not in the Windows exclusion list, so they must run there).
   - linux-sanitizers-tests: `test_budget` under the x3 sanitizer scale (this is the first real exercise of the scale branch), plus `sanitizer_timeout_policy_*`.
   - linux-sanitizers-acceptance: it must finish inside its 45 minute limit with `acceptance_stall_bounded` passing and no `acceptance_stall_diagnosis*` in the run; record its duration (the old p50 was 25.4 of 45 minutes).
   - Policy/judge: the workflow policy job must accept `nightly-asan.yml`.
3. **Land nightly-asan.yml on main first** (D-02a), then dispatch once: `gh workflow run nightly-asan.yml --ref main`. Record the run id and a success conclusion; the replay job must pass `acceptance_stall_diagnosis_replay_1/_2` and `acceptance_stall_diagnosis` under ASan, and `report-red` must be skipped. If it goes red, expect an issue titled "nightly-red: asan-full-replay" and read the replay log.
4. **Record a main ci run id after the shard change** for 16-04's timeout ledger (ASan acceptance job duration and test durations).
5. **Hosted-only unknowns to read:** whether the single-replay TIMEOUT 600 (x3 under ASan, with the 1800 s child deadline) holds under parallel ASan load; the two consumer halves' durations; and that a first push of a new branch (all-zero parent) resolves the merge base.

Recorded for 16-06: LIM-ASAN-STALL-TIMING is closed by D-19 with D-108's amendment, conditional on item 3 above.

## Next Phase Readiness

16-04 needs the post-shard main ci run id from item 4. 16-07 needs the green dispatched nightly-asan run from item 3, and its release-time dispatch uses `--ref rehearsal/v0.2.1` per D-108.

## Self-Check: PASSED

- Created files exist: `tests/scripts/verify-test-budget.py`, `tests/ci/test-budget-allowlist`, `tests/data/stall-bounded-cases.txt`, `.github/workflows/nightly-asan.yml`.
- Commits 9f543a1, 4f34258, 3ae31ca and 337c170 are ancestors of HEAD.
- `git diff --quiet 711f4fd HEAD -- src include tests/baseline/dmg-cpu-b-v1.txt` holds.
- Workflow policy `--check` and `--self-test` (184 negative controls), `verify-test-budget.py --self-test` (34 controls), `verify-stall-report.py --self-test`, `verify-release-gates.sh --self-test`, and the full `ctest --preset phase1` (1202 of 1202) pass at 337c170.
