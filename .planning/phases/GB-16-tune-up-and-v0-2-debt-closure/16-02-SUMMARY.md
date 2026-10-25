---
phase: 16-tune-up-and-v0-2-debt-closure
plan: "02"
subsystem: performance-gate
tags: [cachegrind, perf-gate, ir-proxy, attribution, tune-03, workflow-policy]
requires:
  - phase: 16-01
    provides: tests/cmake/areas.cmake per-area CTest hook and the archived v0.2 phase records
provides:
  - verify-perf-gate.py, a stdlib evaluator with exact-arithmetic Ir, determinism, vacuity, digest and realtime guards, plus the D-17 attribution emitter and recomputing checker
  - perf-gate-v1.txt, the limits file whose header is the gate's limitation note
  - Valgrind-free canned-data CTests (perf_gate_*) over SHA-256-pinned fixtures
  - run-perf-gate.sh with gate, seeded-regression, no-op twin, attribution and attribution-dry-run modes
  - A hosted perf-gate job in ci.yml and release-rehearsal.yml, wired into required-native and judged by the workflow policy
  - perf-attribution.yml, a workflow_dispatch-only read-only measurement job
  - DECISIONS D-107 (per-ROM consumed pin), D-108 (D-19 implementation amendments), D-109 (D-14 realtime floor staging)
affects: [16-03, 16-04, 16-06, 16-07]
actuals:
  tokens: 36400
  tasks: 2
  commits: 2
commits: 2
plan_head_before: 8006d69d267933e597d0907ad672a27a1a52875e
plan_head_after: 30064af010b2c2ae34a7744e2bf7b9b0eb520c81
tech-stack:
  added: []
  patterns:
    - Every limit comparison is integer cross-multiplication or fractions.Fraction; a self-test case that a float comparison would misjudge pins this.
    - Canned fixtures are pinned by a SHA256SUMS manifest whose own digest is pinned in CMake, with a check for extra files.
    - A seeded scratch-tree patch at a whole-line anchor proves the hosted gate fails, and a no-op twin proves it can pass.
key-files:
  created:
    - tests/scripts/verify-perf-gate.py
    - tests/scripts/run-perf-gate.sh
    - tests/baseline/perf-gate-v1.txt
    - tests/cmake/perf.cmake
    - tests/data/perf-gate/
    - .github/workflows/perf-attribution.yml
  modified:
    - tests/cmake/areas.cmake
    - tests/expected-tests.txt
    - .github/workflows/ci.yml
    - .github/workflows/release-rehearsal.yml
    - .github/scripts/verify-workflow-policy.py
    - .planning/context/DECISIONS.md
key-decisions:
  - The visible-demo consumed_half_dots pin is the measured 999992 (D-107); every other limit is as locked in D-14.
  - The realtime floor is staged, with PR A at 2.0 and PR B at max(2.0, 0.6 x receipt multiple) (D-109).
  - The receipt generator and checker share one module with the evaluator so the selection, harness adaptation and privacy rules have a single implementation.
  - The base build in the gate is a git archive of v0.2.0 src and include in a temporary directory, not a git worktree; both leave the real tree untouched.
requirements-completed: []
coverage:
  - id: T1
    description: "The Ir gate evaluator passes a 1.081 pair and exactly 1.10, fails one Ir above with ir-budget-exceeded, and rejects nondeterministic, vacuous (Ir floor and consumed pin), wrong-digest, below-floor realtime and malformed-limits inputs with their own codes, using exact arithmetic including a float-misjudged case."
    requirement: TUNE-03
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-perf-gate.py --self-test"
        status: pass
      - kind: integration
        ref: "ctest -R '^perf_gate_'"
        status: pass
    human_judgment: false
  - id: T2
    description: "Canned cachegrind and timing fixtures are immutable: a drifted fixture stops CMake configuration and the canned over-limit and under-floor sets fail through the real CLI."
    requirement: TUNE-03
    verification:
      - kind: integration
        ref: "ctest -R '^(perf_gate_canned_pass|perf_gate_canned_ir_over_limit|perf_gate_canned_realtime_under_floor|perf_gate_limits_schema)$'"
        status: pass
    human_judgment: false
  - id: T3
    description: "The workflow policy requires perf-gate in required-native needs, its result and the three gate commands in ci.yml and the rehearsal, and judges perf-attribution.yml as dispatch-only and read-only; thirteen new mutations are each rejected."
    requirement: TUNE-03
    verification:
      - kind: unit
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --check"
        status: pass
      - kind: unit
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --self-test"
        status: pass
    human_judgment: false
  - id: T4
    description: "The DMG-only adapted harness builds at all 39 selected revisions, from v0.1.0 to HEAD, and reproduces every per-ROM consumed and digest pin, with harness_sha256 equal to the planning-time value."
    requirement: TUNE-03
    verification:
      - kind: integration
        ref: "bash tests/scripts/run-perf-gate.sh --attribution-dry-run"
        status: pass
    human_judgment: false
  - id: T5
    description: "The gate driver, seeded regression, no-op twin and attribution emit/check pipeline work end to end against a valgrind test double: the seeded patch is rejected with an unchanged digest, the twin passes, a missing valgrind rejects, and the 39-revision receipt passes the recomputing checker; the attribution self-test rejects eleven receipt mutations with distinct codes."
    requirement: TUNE-03
    verification:
      - kind: integration
        ref: "bash tests/scripts/run-perf-gate.sh --seeded-regression with a valgrind test double on PATH (local session, not committed)"
        status: pass
      - kind: unit
        ref: "python3 -I tests/scripts/verify-perf-gate.py --self-test (attribution controls, 33 in total)"
        status: pass
    human_judgment: false
  - id: T6
    description: "The hosted perf-gate job concludes success on the PR head with the seeded step observed rejecting, the seeded iteration count is sized from the first hosted ratio margin, and the hosted Ir margin is confirmed."
    requirement: TUNE-03
    verification: []
    human_judgment: true
    rationale: "Needs a hosted ubuntu-24.04 run with valgrind on an exact PR head. This sandbox is macOS without valgrind, and the orchestrator owns the phase PR."
  - id: T7
    description: "The committed attribution receipt, the perf_attribution CTests, the 20 merge and 39 revision counts, the raised realtime floor and the LIM-PERF-REVIEW closure by citation."
    requirement: TUNE-03
    verification: []
    human_judgment: true
    rationale: "Task 3 is blocked by its precondition: it needs PR A merged, a hosted workflow_dispatch of perf-attribution.yml and its downloaded artifact. The checker, emitter and self-test controls it needs are already in verify-perf-gate.py."
duration: 75min
completed: 2026-10-24
status: partial
---

# Phase 16 Plan 02: Cumulative performance gate Summary

**A cachegrind Ir gate against a same-job v0.2.0 build (limit 1.10, exact arithmetic) with a realtime floor, seeded-regression and no-op-twin controls, a 39-revision attribution pipeline whose dry run passes, and a recomputing receipt checker; tasks 1 and 2 are done, and task 3 (the hosted receipt) is blocked on PR A and a dispatch.**

## Performance

- **Duration:** about 75 min
- **Tasks:** 2 of 3 complete; Task 3 stopped at its precondition
- **Files:** 12 created or modified in the plan's ownership list plus the 62 canned fixtures

## Accomplishments

- **Evaluator (Task 1).** `tests/scripts/verify-perf-gate.py` implements the guards in the order digest, vacuity, determinism, Ir budget, realtime, each with its own REJECT code. The self-test drives the real CLI over fixtures in `tests/data/perf-gate/` and over runtime variants. `perf-gate-v1.txt` carries the limits, the three digest pins and per-ROM consumed pins (1000000, 1000000, 999992), and its header is the limitation note with the blind spots and a guide to each REJECT code. CTest: `perf_gate_controls`, `perf_gate_canned_pass`, `perf_gate_canned_ir_over_limit`, `perf_gate_canned_realtime_under_floor`, `perf_gate_limits_schema`.
- **Decisions.** D-107 records the visible-demo pin: `measure_core --no-trace` printed `consumed_half_dots=999992 stop_reason=0` at both v0.2.0 and the plan base, with the output-line SHA-256 `8d8571749ece4870535d0362299a0b518e19b1c0eb7623f93568f8d476dc3a86` (run-variable fields removed). D-108 records the two D-19 implementation amendments that 16-03 and 16-07 cite. D-109 records the realtime floor staging.
- **Driver and CI (Task 2).** `tests/scripts/run-perf-gate.sh` has the gate, seeded, twin, attribution and dry-run modes. The seeded patch inserts a volatile accumulator loop after the whole-line anchor `static void advance_devices_to(gbb_instance *m, uint64_t target) {` (exactly one match) at 2 iterations per half-dot, which is about 12 Ir. `ci.yml` and `release-rehearsal.yml` gain a read-only `perf-gate` job on ubuntu-24.04. `required-native` lists it, reads `PERF_GATE`, and `CI_REQUIRED_NATIVE_NEEDS` includes it. `perf-attribution.yml` is dispatch-only with `contents: read` and a 150-minute budget.
- **Attribution tooling (Tasks 2 and 3 code).** The DMG-only harness is derived with one anchored replacement. Its SHA-256 matches the planning value `c65f13d3f30acafdf223b25b5e6145b9a86113286a93f4b5032601a19b2b097d`, and the unadapted source digest is `7f7b60d7c0daf5187da7efafb20d048570080d9ba9f3b0b1ca76536e0765d9d2`. The build command is `cc -std=c17 -O3 -DNDEBUG -I$REV/include $HARNESS $REV/src/core/*.c`. The full dry run printed `attribution dry-run pass revisions=39 harness_sha256=c65f13d3f30acafdf223b25b5e6145b9a86113286a93f4b5032601a19b2b097d`. The emitter and the `--check-attribution` checker re-derive merge_set (20), resolution_set (14) and post_v020_set (3) with their own git commands, recompute affects_binary, deltas and raw-row digests, require the warm_up field and re-derive the harness digest.
- **D-17 reading.** merge_set honours "every first-parent merge" literally (20 merges, of which only 261c660 affects the binary at planning time). resolution_set (14 src/include first-parent commits) is the added set that lets the slowdown be assigned to squash-merged phase commits such as Phase 7 (5673bed). The attribution to those commits is not yet made, because the Ir measurements need valgrind.

## Task Commits

1. **Task 1: Ir gate evaluator, limits, fixtures, CTests, decisions** - `4484a81` (test)
2. **Task 2: perf-gate job, driver, dispatch workflow, policy pins, attribution tooling** - `30064af` (ci)
3. **Task 3: receipt, dispatch and raised floor** - not started (precondition unmet, see below)

## Verification Run

- `python3 -I tests/scripts/verify-perf-gate.py --self-test` printed `perf-gate self-test pass controls=33`.
- `ctest -R '^perf_gate_'` passed 5 of 5. The full suite `ctest --preset phase1` passed 1192 of 1192, including the expected-tests inventory.
- `python3 -I .github/scripts/verify-workflow-policy.py --check` passed and `--self-test` printed `negative_controls=177 positive_controls=4`.
- The anchor count is exactly 1, and the dry runs at v0.1.0, HEAD and all 39 revisions passed. `git diff --quiet` of src and include against the plan base holds.
- A negative control for the fixture pin: appending one line to a pinned fixture stopped `cmake --preset phase1` with the immutable-test-data error, and the fixture was restored byte-for-byte.
- A valgrind test double (kept in the session scratch directory, not committed) exercised `--gate`, `--seeded-regression` (rejected with `ir-budget-exceeded`, digest unchanged), `--noop-twin` (passed), the missing-valgrind rejection and `--attribution` with the checker passing 39 revisions and 20 merges on its output. Its Ir values are synthetic and prove the plumbing only.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] DECISIONS titles carry the literal "(Phase 16)" form**
- **Found during:** Task 1 verify
- **Issue:** The verify greps `D-14 realtime floor staging (Phase 16)` and `D-19 implementation amendments (Phase 16)` literally; the first draft put a date inside the parentheses.
- **Fix:** Titles use the exact string and the date follows as a separate sentence.
- **Files modified:** `.planning/context/DECISIONS.md`

**2. [Rule 1 - Bug] Self-test floor control used the wrong consumed pin**
- **Found during:** Task 1
- **Issue:** The exact-at-floor realtime case computed its floor from 1000000 half-dots, but visible-demo consumes 999992, so it fell below the floor.
- **Fix:** The floor is built from the tightest ROM (999992).

**3. [Rule 3 - Blocking] The seeded marker needed an attribute**
- **Found during:** local test-double run
- **Issue:** The compiler folded the marker string away, so the double could not recognise the patched binary.
- **Fix:** `__attribute__((used))` on the marker. The hosted Ir comparison does not depend on it.

**Other departures.** The gate builds the v0.2.0 base from `git archive` into a temporary directory instead of `git worktree`, with the same isolation. The attribution emitter, checker and their self-test controls were written in this run (Task 3's code) so the pipeline could be tested end to end; Task 3's data, CTests and floor raise were not. The branch and PR delivery (PR A, PR B) belong to the orchestrator and were not created.

**Total deviations:** 3 auto-fixed, 2 noted departures. **Impact:** none on the contract.

## Blocked: Task 3 and hosted evidence

Task 3 carries `precondition: PR A merged, perf-attribution.yml on main, dry run prints revisions=39`. PR A is not merged, and a hosted dispatch needs valgrind on a Linux runner, so the precondition is unmet and the task was not started. The dry-run half of the precondition already holds locally. Still needed, in order:

1. Open PR A from Tasks 1 and 2, let required checks pass on its exact head, confirm the hosted `perf-gate` log shows the seeded step rejecting, then record the run id and, if the margin demands, re-size `GBB_SEED_ITERS_PER_HALF_DOT` (the default of 2 is an estimate, since Ir per half-dot could not be measured here).
2. Merge PR A, then run `gh workflow run perf-attribution.yml --ref main`, wait for success and download the artifact.
3. Commit the artifact byte-for-byte as `tests/baseline/perf-attribution-v1.json`. Stop and report if any repeat differs or any digest changes.
4. Run `--check-attribution` on it. Register `perf_attribution` (min `revisions` 39) and `perf_attribution_merges` (min `merges` 20) in `tests/cmake/perf.cmake` and `tests/expected-tests.txt`. Raise `realtime_floor` to max(2.0, 0.6 x the receipt multiple) rounded down to two decimals; the evaluator already refuses a lower floor whenever the receipt sits beside the limits file. Record the receipt SHA-256, the run ids, the gcc and valgrind versions and the realtime floor in this SUMMARY, and cite the receipt to close LIM-PERF-REVIEW.

## Known Stubs

None.

## Threat Flags

None. The new workflow surface (`perf-attribution.yml`, the `perf-gate` jobs) is read-only, uses pinned actions and is covered by the policy mutations above (T-16-05).

## Next

Execute Task 3 once PR A is merged and the dispatch has run. The next plan by number, 16-03, does not depend on the receipt.

## Self-Check: PASSED

- Files exist: `tests/scripts/verify-perf-gate.py`, `tests/scripts/run-perf-gate.sh`, `tests/baseline/perf-gate-v1.txt`, `tests/cmake/perf.cmake`, `tests/data/perf-gate/SHA256SUMS`, `.github/workflows/perf-attribution.yml`.
- Commits `4484a81` and `30064af` are ancestors of HEAD.
- The tasks completed here (1 and 2) passed their acceptance commands; Task 3 and the hosted acceptance are open and recorded above, not claimed.
