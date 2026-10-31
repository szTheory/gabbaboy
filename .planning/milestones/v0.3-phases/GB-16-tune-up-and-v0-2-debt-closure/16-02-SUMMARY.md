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
  - perf-gate-v1.txt, the limits file whose header is the gate's limitation note, with realtime_floor 4.02
  - Valgrind-free canned-data CTests (perf_gate_*) over SHA-256-pinned fixtures
  - perf_attribution and perf_attribution_merges CTests that recompute the committed hosted receipt from git history
  - run-perf-gate.sh with gate, seeded-regression, no-op twin, attribution and attribution-dry-run modes
  - A hosted perf-gate job in ci.yml and release-rehearsal.yml, wired into required-native and judged by the workflow policy
  - perf-attribution.yml, a workflow_dispatch-only read-only measurement job, and the receipt it produced
  - DECISIONS D-107 (per-ROM consumed pin), D-108 (D-19 implementation amendments), D-109 (D-14 realtime floor staging)
affects: [16-03, 16-04, 16-06, 16-07]
actuals:
  tokens: 40000
  tasks: 3
  commits: 2
commits: 2
plan_head_before: 8006d69d267933e597d0907ad672a27a1a52875e
plan_head_after: 87fe4489d888100b86f0cf332a69ae0748d90c4a
tech-stack:
  added: []
  patterns:
    - Every limit comparison is integer cross-multiplication or fractions.Fraction; a self-test case that a float comparison would misjudge pins this.
    - Canned fixtures are pinned by a SHA256SUMS manifest whose own digest is pinned in CMake, with a check for extra files.
    - A seeded scratch-tree patch at a whole-line anchor proves the hosted gate fails, and a no-op twin proves it can pass.
    - A hosted workflow_dispatch artifact is committed byte-for-byte and re-derived from git history by a stdlib checker.
key-files:
  created:
    - tests/scripts/verify-perf-gate.py
    - tests/scripts/run-perf-gate.sh
    - tests/baseline/perf-gate-v1.txt
    - tests/baseline/perf-attribution-v1.json
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
  - The realtime floor is staged, PR A at 2.0 and PR B at max(2.0, 0.6 x receipt multiple) = 4.02 (D-109).
  - The receipt generator and checker share one module with the evaluator so the selection, harness adaptation and privacy rules have a single implementation.
  - The base build in the gate is a git archive of v0.2.0 src and include in a temporary directory, not a git worktree; both leave the real tree untouched.
requirements-completed: [TUNE-03]
coverage:
  - id: T1
    description: "The Ir gate evaluator passes a 1.081 pair and exactly 1.10, fails one Ir above with ir-budget-exceeded, and rejects nondeterministic, vacuous (Ir floor and consumed pin), wrong-digest, below-floor realtime and malformed-limits inputs with their own codes, using exact arithmetic including a float-misjudged case."
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-perf-gate.py --self-test"
        status: pass
      - kind: integration
        ref: "ctest -R '^perf_gate_'"
        status: pass
  - id: T2
    description: "Canned cachegrind and timing fixtures are immutable: a drifted fixture stops CMake configuration and the canned over-limit and under-floor sets fail through the real CLI."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R '^(perf_gate_canned_pass|perf_gate_canned_ir_over_limit|perf_gate_canned_realtime_under_floor|perf_gate_limits_schema)$'"
        status: pass
  - id: T3
    description: "The workflow policy requires perf-gate in required-native needs, its result and the three gate commands in ci.yml and the rehearsal, and judges perf-attribution.yml as dispatch-only and read-only; thirteen new mutations are each rejected."
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --check"
        status: pass
      - kind: unit
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --self-test"
        status: pass
  - id: T4
    description: "The DMG-only adapted harness builds at all 39 selected revisions, from v0.1.0 to HEAD, and reproduces every per-ROM consumed and digest pin, with harness_sha256 equal to the planning-time value."
    human_judgment: false
    verification:
      - kind: integration
        ref: "bash tests/scripts/run-perf-gate.sh --attribution-dry-run"
        status: pass
  - id: T5
    description: "The gate driver, seeded regression, no-op twin and attribution emit and check pipeline work end to end, and the attribution self-test rejects eleven receipt mutations with distinct codes."
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-perf-gate.py --self-test"
        status: pass
  - id: T6
    description: "The hosted perf-gate job concluded success on PR A's exact head with the seeded step rejecting (head Ir 265298354 over v0.2.0 Ir 233589980, ratio 1.135, digest unchanged, 2 iterations per half-dot) and the no-op twin passing at ratios tracer=1.083 libbet=1.081 visible-demo=1.080 with realtime_min=6.665."
    human_judgment: false
    verification:
      - kind: e2e
        ref: "gh run view 40154479138 --job 121052802460 -R szTheory/gabbaboy"
        status: pass
  - id: T7
    description: "TUNE-03: the hosted attribution receipt is committed byte-for-byte and recomputed from git history (39 revisions, 20 merges). The realtime floor is staged per D-109, PR A gating at 2.0 and PR B raising it to 4.02 = floor(0.6 x 6.7027); the evaluator refuses a lower floor. LIM-PERF-REVIEW is closed by citing the receipt."
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-perf-gate.py --check-attribution tests/baseline/perf-attribution-v1.json"
        status: pass
      - kind: integration
        ref: "ctest -R '^perf_(gate|attribution)'"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1"
        status: pass
duration: 90min
completed: 2026-10-24
status: complete
---

# Phase 16 Plan 02: Cumulative performance gate Summary

**A cachegrind Ir gate against a same-job v0.2.0 build (limit 1.10, exact arithmetic) with a realtime floor of 4.02, seeded-regression and no-op-twin controls proven on hosted CI, and a hosted 39-revision attribution receipt, recomputed from git history in CTest, that assigns 65% of the v0.1.0 to v0.2.0 Ir growth to Phase 7 (5673bed) and closes LIM-PERF-REVIEW.**

## Performance

- **Duration:** about 90 min across the original run and this continuation
- **Tasks:** 3 of 3 complete
- **Files:** 13 created or modified in the plan's ownership list plus the 62 canned fixtures

## Accomplishments

- **Evaluator (Task 1).** `tests/scripts/verify-perf-gate.py` implements the guards in the order digest, vacuity, determinism, Ir budget, realtime, each with its own REJECT code. The self-test drives the real CLI over fixtures in `tests/data/perf-gate/` and over runtime variants. `perf-gate-v1.txt` carries the limits, the three digest pins and per-ROM consumed pins (1000000, 1000000, 999992), and its header is the limitation note with the blind spots and a guide to each REJECT code. CTest: `perf_gate_controls`, `perf_gate_canned_pass`, `perf_gate_canned_ir_over_limit`, `perf_gate_canned_realtime_under_floor`, `perf_gate_limits_schema`.
- **Decisions.** D-107 records the visible-demo pin: `measure_core --no-trace` printed `consumed_half_dots=999992 stop_reason=0` at both v0.2.0 and the plan base, with the output-line SHA-256 `8d8571749ece4870535d0362299a0b518e19b1c0eb7623f93568f8d476dc3a86` (run-variable fields removed). D-108 records the two D-19 implementation amendments that 16-03 and 16-07 cite. D-109 records the realtime floor staging.
- **Driver and CI (Task 2).** `tests/scripts/run-perf-gate.sh` has the gate, seeded, twin, attribution and dry-run modes. The seeded patch inserts a volatile accumulator loop after the whole-line anchor `static void advance_devices_to(gbb_instance *m, uint64_t target) {` (exactly one match) at 2 iterations per half-dot, about 12 Ir. `ci.yml` and `release-rehearsal.yml` gain a read-only `perf-gate` job on ubuntu-24.04. `required-native` lists it, reads `PERF_GATE`, and `CI_REQUIRED_NATIVE_NEEDS` includes it. `perf-attribution.yml` is dispatch-only with `contents: read` and a 150-minute budget.
- **Hosted gate evidence.** On PR A's exact head (5d26b7e) perf-gate job run 40154479138 (job 121052802460; companion run 40154476158) logged `REJECT ir-budget-exceeded: tracer: head Ir 265298354 over v0.2.0 Ir 233589980 is ratio 1.135` with the digest unchanged ("iterations per half-dot: 2" kept, so no re-sizing was needed), the no-op twin passing at `ratios tracer=1.083 libbet=1.081 visible-demo=1.080`, and `realtime_min=6.665`. All 40 checks, including required-native, were green. PR A was squash-merged as 711f4fd.
- **Attribution receipt (Task 3).** The orchestrator dispatched `perf-attribution.yml` on main 711f4fd: run 40156286321, conclusion success, artifact `perf-attribution-receipt-40156286321-1`. It is committed byte-for-byte as `tests/baseline/perf-attribution-v1.json` (43919 bytes, SHA-256 `6f0da7c7e3850c3ea15536accd081d9676b4da6398913187e37da33f4d501067`). Hosted build: `cc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`, `valgrind-3.22.0`, runner image `ubuntu24-20261023.334.3`, Linux x86_64 4 vCPU. Harness: `harness_source_sha256 7f7b60d7c0daf5187da7efafb20d048570080d9ba9f3b0b1ca76536e0765d9d2`, `harness_sha256 c65f13d3f30acafdf223b25b5e6145b9a86113286a93f4b5032601a19b2b097d`, `build_command cc -std=c17 -O3 -DNDEBUG -I$REV/include $HARNESS $REV/src/core/*.c`. The dry run on main printed `attribution dry-run pass revisions=39 harness_sha256=c65f13d3...2b097d`. Both Ir repeats agreed at every revision (`ir_repeat_spread` 0) and the digests were constant, so there was no stop condition.
- **Checker and CTests.** `--check-attribution` printed `perf-attribution pass revisions=39 merges=20`. `perf_attribution` (min `revisions` 39) and `perf_attribution_merges` (min `merges` 20) are registered in `tests/cmake/perf.cmake` and `tests/expected-tests.txt`. They need full history and the v0.1.0 and v0.2.0 tags. The self-test already carried the eleven mutation controls and the floor-refusal control from the earlier run (33 controls), so `perf_gate_controls` keeps its minimum of 33.
- **Realtime floor.** The hosted multiple is 30517578125/4552850688 = 6.7027 (nine samples per ROM, one discarded warm-up; tracer is the fastest ROM at about 16.64 ms per 1,000,000 half-dots). Staging per D-109: PR A gated at `realtime_floor=2.0`; PR B raises it to max(2.0, 0.6 x 6.7027) = 4.02 (rounded down to two decimals). The hosted PR A realtime_min of 6.665 clears 4.02. The evaluator refuses a floor below the receipt rule when the receipt sits beside the limits file.
- **Attribution findings (D-17).** Largest v0.1.0 to v0.2.0 Ir delta: `5673bed` (Phase 7, DMG game acceptance and regression baseline, #63) adds 32,000,000 Ir to each of the three ROMs, 95,999,744 in total. The v0.1.0 to v0.2.0 growth per ROM is libbet 49,226,780, tracer 47,742,217 and visible-demo 49,541,485 (146,510,482 in total), so Phase 7 carries about 65% of it. This confirms the "Phase 7 carries most of the growth" statement in the plan. The remainder is spread over `8091fb5` (27.3M, summed over the ROMs), `70c441b` (Phase 11 CGB, 14.6M), `3012e8f` (8.5M), `30230b2` (2.3M) and small others, with `261c660` (CGB DMA, the only merge that touches the binary) at -3.1M. Post-v0.2.0 growth is 19,421,815 (libbet), 19,416,680 (tracer) and 19,412,263 (visible-demo), almost entirely from `09805f3` (58.3M in total); `2d25a47` and `79e20f3` add no measured delta. The audio-mix divide-by-16 cause is recorded as a hypothesis, not an established fact. LIM-PERF-REVIEW is closed by citing this receipt (`closes: [LIM-PERF-REVIEW]`); no performance fix lands in Phase 16 (D-13).
- **D-17 reading.** merge_set honours "every first-parent merge" literally (20 merges, of which only 261c660 affects the binary). resolution_set (14 src/include first-parent commits) is the added set that lets the slowdown be assigned to squash-merged phase commits such as Phase 7.

## Task Commits

1. **Task 1: Ir gate evaluator, limits, fixtures, CTests, decisions** - `4484a81` (test), merged in squash 711f4fd
2. **Task 2: perf-gate job, driver, dispatch workflow, policy pins, attribution tooling** - `30064af` (ci), merged in squash 711f4fd
3. **CI fixes on PR A** - `e719aa7` (perf-gate fixtures `eol=lf` for Windows), `5d26b7e` (fuzz harness CGB unarmed STOP), merged in squash 711f4fd
4. **Task 3: receipt, CTests, raised floor** - `87fe448` (perf)

`commits: 2` is measured with `git rev-list --count 8006d69..HEAD` on the main line (the PR A squash 711f4fd and the Task 3 commit); the four PR A commits above were squashed into 711f4fd.

## Verification Run

- `python3 -I tests/scripts/verify-perf-gate.py --self-test` printed `perf-gate self-test pass controls=33`.
- `python3 -I tests/scripts/verify-perf-gate.py --check-attribution tests/baseline/perf-attribution-v1.json` printed `perf-attribution pass revisions=39 merges=20`.
- `python3 -I .github/scripts/verify-workflow-policy.py --self-test` printed `negative_controls=177 positive_controls=4`.
- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` passed 1194 of 1194 (the earlier 1192 plus the two attribution tests); `ctest -R '^perf_'` passed 7 of 7.
- `git diff --quiet 711f4fd HEAD -- src include` holds.
- Hosted evidence for PR A is recorded above. PR B's hosted run is the orchestrator's delivery.

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

**4. [Rule 3 - Blocking] Perf-gate fixtures needed LF endings on Windows**
- **Found during:** PR A hosted CI
- **Issue:** The native-windows-x64 job checked the canned fixtures out with CRLF, so the pinned SHA-256 values drifted.
- **Fix:** `.gitattributes` marks the fixtures `eol=lf`.
- **Commit:** `e719aa7` (squashed into 711f4fd)

**5. [Rule 1 - Bug] Fuzz harness failed on an unarmed CGB STOP (pre-existing, tests/ only)**
- **Found during:** PR A hosted explore run 40151212480
- **Issue:** Speed scenario 7 of the fuzz harness issued STOP on CGB without arming a speed switch, which the core handles as a stop; the harness expectation was wrong.
- **Fix:** The harness handles the unarmed CGB STOP case. No src/ change.
- **Commit:** `5d26b7e` (squashed into 711f4fd)

**Other departures.** The gate builds the v0.2.0 base from `git archive` into a temporary directory instead of `git worktree`, with the same isolation. The attribution emitter, checker and their self-test controls were written in the first run so the pipeline could be tested end to end, so Task 3 here added only data, CTests and the floor. The `perf_gate_controls` minimum was not raised further because the 33 controls already include the ten attribution controls. The 4.02 floor is in the limits-file header with its derivation. Branch, PR and merge delivery belong to the orchestrator.

**Total deviations:** 5 auto-fixed (2 Rule 1, 3 Rule 3), 3 noted departures. **Impact:** none on the contract.

## Known Stubs

None.

## Threat Flags

None. The new workflow surface (`perf-attribution.yml`, the `perf-gate` jobs) is read-only, uses pinned actions and is covered by the policy mutations (T-16-05). The receipt passed the privacy rules (T-16-06): hardware class only.

## Next

Phase 16 plan 16-03. The next plan by number does not depend on the receipt. Deliver PR B (Task 3 plus this SUMMARY) and merge it after exact-head required checks pass.

## Self-Check: PASSED

- Files exist: `tests/baseline/perf-attribution-v1.json`, `tests/scripts/verify-perf-gate.py`, `tests/scripts/run-perf-gate.sh`, `tests/baseline/perf-gate-v1.txt`, `tests/cmake/perf.cmake`, `.github/workflows/perf-attribution.yml`.
- Commits: `711f4fd` (squash of tasks 1-2 and the CI fixes) and `87fe448` are ancestors of HEAD; the original task SHAs live inside the squash.
- Task 3 acceptance commands passed (check-attribution, self-test, ctest, src/include diff).
