---
phase: 07-dmg-game-acceptance-and-regression-baseline
plan: 15
subsystem: testing
tags: [baseline, ledger, junit, ci, cross-os, exact-head-ci, evid-02]

requires:
  - phase: 07-13
    provides: cmake/VerifyDmgBaseline.cmake comparator (check, print-candidate, junit) and its wrapper
  - phase: 07-14
    provides: packaged player smoke and green macos-player-package evidence
  - phase: 07-03
    provides: D-19(i) outcome (mixer headroom fix, D-027)
  - phase: 07-17
    provides: D-19(ii) outcome (expected guest behaviour, D-028)
provides:
  - tests/baseline/dmg-cpu-b-v1.txt frozen DMG-CPU-B ledger (key<TAB>value, LC_ALL=C sorted, LF)
  - tests/baseline/CHANGES.md approved-change protocol with an empty table
  - CTest dmg_baseline (cmake -P check mode) in the core inventory
  - CI steps printing "baseline status=pass" and checking the JUnit inventory in the three native jobs, plus the player JUnit inventory check in the package script
affects: [07-16, phase 8, phases 11+]

status: complete
actuals:
  tokens: 9000
  tasks: 2
  commits: 4
plan_head_before: 5a55f19ba2e0ec596005af4dbbc55d476b326333
plan_head_after: 6b4ff7c7503eecb0e410acf4eaade85d77444e5d

tech-stack:
  added: []
  patterns:
    - "Ledger body hash covers every non-header line including bench.advisory.*, so advisory lines are provenance that cannot change silently, yet the check never compares their values to a live run"
    - "Wrapper converts every path handed to native cmake with cygpath -m (no-op off Windows)"

key-files:
  created:
    - tests/baseline/dmg-cpu-b-v1.txt
    - tests/baseline/CHANGES.md
  modified:
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - .github/workflows/ci.yml
    - tests/scripts/verify-phase3-player.sh
    - tests/scripts/verify-dmg-baseline.sh

key-decisions:
  - "Ledger header uses model dmg-cpu-b (lowercase) and plain sentences with no semicolons in coverage, because the comparator's header validation and parser require them"
  - "The core JUnit step runs after the existing inventory step with the --installed names present in the CI report, so the installed_* names the ledger freezes are all found (names=258)"

requirements-completed: [EVID-02]

coverage:
  - id: D1
    description: "Frozen DMG-CPU-B ledger committed in a dedicated baseline: commit that touches nothing under src/, after every Phase 7 src/ change"
    requirement: EVID-02
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^dmg_baseline$' passed; git show --name-only HEAD at 42faf9b lists no src/ path"
        status: pass
    human_judgment: false
  - id: D2
    description: "One ledger byte-identical on Linux, macOS and Windows at the exact head, with frozen test names proven run and passing"
    requirement: EVID-02
    verification:
      - kind: integration
        ref: "CI run 38104647567 at 6b4ff7c: 'baseline status=pass' and 'baseline junit=ok inventory=core names=258' in native-linux-x64, native-macos-arm64 and native-windows-x64, 'baseline junit=ok inventory=player names=55' in macos-player-package"
        status: pass
    human_judgment: false
  - id: D3
    description: "Libbet checkpoint frames and the daa LD B,B frame inspected once by the executing agent before the freeze"
    requirement: EVID-02
    verification:
      - kind: other
        ref: "scratch PPM dump, PNG conversion and shade counts recorded below"
        status: pass
    human_judgment: true
    rationale: "Agent inspection establishes only coarse content, not pixel accuracy, palette fidelity or hardware equivalence. The digest is the regression evidence."

duration: 70min
completed: 2026-10-10
---

# Phase 7 Plan 15: DMG-CPU-B Baseline Freeze Summary

**A 313-inventory-name plus 15 Mooneye, 20 acceptance and 2 bench-identity line DMG-CPU-B ledger frozen at 5a55f19 in a src-free `baseline:` commit, checked by the live `dmg_baseline` CTest, and proven `baseline status=pass` on Linux, macOS and Windows at exact head 6b4ff7c.**

## Accomplishments

- Inspected the frames once (below), then froze `tests/baseline/dmg-cpu-b-v1.txt` with `frozen_revision` 5a55f19ba2e0ec596005af4dbbc55d476b326333 (ancestor of HEAD, contains all Phase 7 src/ changes including D-027 and the player smoke). Freeze commit 42faf9b touches only the ledger, `CHANGES.md`, `tests/CMakeLists.txt` and `tests/expected-tests.txt`.
- Registered `dmg_baseline` (TIMEOUT 300, `PASS_REGULAR_EXPRESSION "baseline status=pass"`) and added it to `tests/expected-tests.txt`; `inventory.core.dmg_baseline` and `inventory.sha256` therefore include it. Local check output: inventory ok keys=313, mooneye 15, acceptance 20, bench 2, changes rows=0, status=pass.
- `tests/baseline/CHANGES.md` defines the D-34 protocol (dedicated src-free `baseline:` commits, one row per changed line, evidence class and approver, no update mode, Phase 8 and Phases 11+ default to zero changed lines) with an empty table.
- Wired JUnit inventory checks into CI: `verify-dmg-baseline.sh --junit build/ctest.xml --inventory core` in native-linux-x64, native-macos-arm64 and native-windows-x64, and `--inventory player` in `verify-phase3-player.sh` (macos-player-package). No job added, `required-native` unchanged.
- Advisory benchmark record from `measure-release-baseline.sh` (defaults, 2 warm-ups, 10 samples per mode) at 5a55f19: Release, Apple clang 21.0.0, macOS arm64 laptop, tracer workload `original-wram-tracer-1m-half-dots-v1`, digest 4c7a57ff3d50d228. no-trace median 8968500 ns (sd 359430, 95% margin 222777), trace median 9543000 ns (sd 361091, margin 223807). Advisory only: uncontrolled host load, no CPU isolation. Stored as `bench.advisory.*` lines; the check does not compare them.

## D-26 frame inspection (agent inspection, once, before freezing)

Dumped with `gabbaboy-runner --acceptance tests/acceptance/cases.txt --case libbet --observe --dump-checkpoints <scratch>` and `--acceptance tests/acceptance/ldbb-controls.txt --case daa-ldbb ...`; each PPM (160x144) converted to PNG with macOS `sips` in the scratch directory (not committed) and viewed with the Read tool. This is an agent inspection: it establishes only coarse content (screen identity, not blank, not corrupted), not pixel accuracy, palette fidelity or hardware equivalence. The digest, not the inspection, is the regression evidence. No human sign-off is claimed.

| PPM file | Label | Digest | Shade counts (white/light/dark/black) | Observed |
| --- | --- | --- | --- | --- |
| libbet.title.ppm (libbet.title.png) | title | 8097d8c7...5d04778 | 20864 / 0 / 0 / 2176 | Title text "Libbet and the Magic Floor v0.08 (2024-01-xx)", intro paragraph, "Select: demo / Start: play" |
| libbet.play_start.ppm (libbet.play_start.png) | play_start | 3d9c9f27...b361f62 | 18959 / 0 / 0 / 4081 | Two-shade frame with a repeating tile pattern over the right two thirds and a partial black HUD strip reading "Comb" at bottom left; reads as a floor-load or transition frame, not a settled play screen |
| libbet.mid.ppm (libbet.mid.png) | mid | a07a58d6...ad85071 | 9893 / 9656 / 2726 / 765 | Gameplay: dithered grey background, tutorial room sprite, HUD "1 Combo, 50%, 2/04" |
| libbet.hit.ppm (libbet.hit.png) | hit | fb5e3bc3...1c61c | 9887 / 9628 / 2739 / 786 | Same room, HUD "0 Combo, 75%, 3/04" (scored floor progress advanced from mid) |
| daa-ldbb.ldbb.ppm (daa-ldbb.ldbb.png) | ldbb | 29cd364f...873ff | 23040 / 0 / 0 / 0 | Entirely shade 0 (blank white) |

Notes. The play_start frame is a legitimate mid-load capture (requested half-dot 70645344, completed 71336360, between title and gameplay) and is frozen as such; its digest is only a regression marker. The daa LD B,B frame is all shade 0, as an earlier plan had found: it is a low-information regression frame (the Mooneye ROM reports through registers and never draws), so `mooneye.daa.frame` guards "still blank" only, and the `tim00` and `tim00-div-trigger` frames are `not-ready` (LD B,B reached before the first frame completed). Nothing was inconsistent with its label, so no stop-and-investigate was needed. The coverage line labels Libbet frame and PCM digests and Mooneye frame digests as regression class.

## Exact-head CI evidence

- Final head 6b4ff7c7503eecb0e410acf4eaade85d77444e5d, run 38104647567 (https://github.com/szTheory/gabbaboy/actions/runs/38104647567), pull_request, attempt 1. `wait-exact-head-ci.py --require` for all eight jobs printed `PASS run_id=38104647567 run_attempt=1`. Jobs all success: native-linux-x64, native-macos-arm64, native-windows-x64, cmake-floor-3.25.3, player-gate, linux-asan-ubsan, macos-player-package, required-native.
- Log lines at that head: native-linux-x64, native-macos-arm64 and native-windows-x64 each print `216/258 Test #216: dmg_baseline ... Passed` (10.44 s, 9.69 s, 7.22 s), `baseline status=pass`, and `baseline junit=ok inventory=core names=258`. macos-player-package prints `baseline junit=ok inventory=player names=55`.
- Fix cycles: 1 of 3 used. The first push (b18fac0, run 38102094077) was green but ctest hides the output of a passing test, so the literal `baseline status=pass` was not in the logs. Added a step running the same check (0d09ead); its first run (38103395151) failed on native-windows-x64 only (see Deviations), fixed in 6b4ff7c, green.

## Deviations from Plan

**1. [Rule 2 - Missing evidence] Extra CI step to print the check line**
- **Found during:** Task 2 (run 38102094077)
- **Issue:** The plan asks to quote `baseline status=pass` from each native log, but CTest output of a passing test is not logged.
- **Fix:** Added a "Print DMG baseline check result" step (`bash tests/scripts/verify-dmg-baseline.sh`) before the JUnit step in the three native jobs. Commit 0d09ead.

**2. [Rule 1 - Bug] Wrapper handed MSYS paths to native cmake on Windows**
- **Found during:** Task 2 (run 38103395151, native-windows-x64)
- **Issue:** Git Bash passed `/d/a/...` style paths, so `EXISTS` failed and the wrapper (from 07-13) reported `observation-failed GBB_RUNNER and GBB_MEASURE must name built executables`. The ctest path was unaffected.
- **Fix:** `native_path()` in `tests/scripts/verify-dmg-baseline.sh` converts via `cygpath -m` when present. Not a per-OS ledger. Commit 6b4ff7c. Local check and junit modes still pass.

**3. [Rule 3 - Format constraint] Ledger header differs textually from the plan**
- The comparator requires `model` to match `^[a-z0-9][a-z0-9-]*$`, so the value is `dmg-cpu-b`, and CMake lists split on semicolons, so the `coverage` sentence uses periods and commas where the plan's text used semicolons. Content is otherwise the plan's text.

**4. Acceptance criterion wording.** `grep -c '^inventory.core.dmg_baseline'` returns 21 because the prefix also matches the 20 `dmg_baseline_*` self-test names; the exact key `inventory.core.dmg_baseline` appears once. `inventory.player.*` count is 55, equal to `tests/player/expected-tests.txt`.

**Total deviations:** 4 (1 missing evidence, 1 bug, 1 format constraint, 1 wording). **Impact:** none on the frozen content.

## Known limitations

- The baseline proves only the listed workloads (see the ledger `coverage` line); it is not hardware evidence or game compatibility. The frame inspection is an agent inspection.
- Two `ci` runs exist at each pushed head (push and pull_request events); the pull_request run was used.
- Benchmark timing is a single-host advisory sample and never gates.
- Requirement EVID-02 is declared by sibling plans in this phase; see STATE for whether it is marked complete.

## Self-Check: PASSED

- Files exist: tests/baseline/dmg-cpu-b-v1.txt, tests/baseline/CHANGES.md.
- Commits in history: 42faf9b, b18fac0, 0d09ead, 6b4ff7c (`git merge-base --is-ancestor` verified below in the final report run).
- `LC_ALL=C sort -c` clean, no `\r`, personal-path regex count 0, `frozen_revision` is an ancestor of HEAD, freeze commit lists no `src/` path.
- Core acceptance greps: ci.yml `--junit build/ctest.xml --inventory core` count 3, verify-phase3-player.sh `--inventory player` count 1.
