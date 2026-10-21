---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 20
subsystem: release-evidence-and-handoff
tags: [exact-head-ci, pull-request, owner-veto, handoff, lessons, fixture-admission, d-28, d-29]
requires:
  - phase: 10-cgb-profile-banking-and-register-visibility
    provides: "plans 10-01..10-19 (profile, banking, visibility matrix, fixtures, Mooneye CGB, benchmark, ADR and guide)"
provides:
  - "Phase 10 evidence head 2fe078e8f08ed98ba0ac0e244971e7c0ead16b1e, exact-head green on all eight required checks and seven fixture-repro jobs"
  - "PR #66 ready for review and OPEN, with the six owner veto items, the D-29 judgement and a requirement-to-evidence table"
  - "LESSONS GB-CGB-001, FUTURE-MILESTONES Phase 10 deferred items, INDEX.md Phase 10 bullet"
  - "STATE.md and .continue-here.md handoff to /gsd-verify-work 10, Phase 11 named and not started"
affects: [11]
actuals:
  tokens: 11000
  tasks: 2
  commits: 4
key-files:
  created:
    - .planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-PR-BODY.md
  modified:
    - .planning/context/LESSONS.md
    - .planning/context/FUTURE-MILESTONES.md
    - .planning/research/INDEX.md
    - .gitignore
    - .github/scripts/verify-test-inventory.sh
    - fixtures/cgb-banking/banking-cgb.gb
    - fixtures/cgb-banking/banking-dmg.gb
    - .planning/STATE.md
    - .planning/.continue-here.md
key-decisions:
  - "The CGB banking ROMs are admitted by explicit .gitignore exceptions like every other fixture; bytes are unchanged and equal the manifest digests"
  - "The CI inventory script mirrors cmake/ExpectedTests.cmake by dropping the bash-only cgb_bench_ab_* controls on MINGW/MSYS/CYGWIN hosts only"
  - "PR #66 stays open; the squash merge waits for /gsd-verify-work 10 at an exact-head green head"
requirements-completed: [CGB-01, CGB-02, CGB-03]
coverage:
  - id: D1
    description: "Immutable Phase 10 boundary snapshots show no removed test-inventory line or baseline change; the evidence snapshot retains the frozen digest and has no active research:10 model-gate tag"
    requirement: "CGB-02"
    verification:
      - kind: other
        ref: "Fixed-boundary check on 5e2b32f16fa705043c5437fb63a08bd83a4d750b and 2fe078e8f08ed98ba0ac0e244971e7c0ead16b1e; see dated command evidence below"
        status: pass
      - kind: other
        ref: "build/measure_core --no-trace fixtures/tracer/tracer.gb; python3 -I tests/scripts/verify-model-gates.py; bash tests/scripts/verify-dmg-baseline.sh"
        status: pass
    human_judgment: false
  - id: D2
    description: "Historical exact-head hosted checks remain green for the original evidence and handoff commits"
    requirement: "CGB-01"
    verification:
      - kind: integration
        ref: "gh run view 38299323863, 38299323969, 38302631119, 38302631195: success on exact historical SHAs 2fe078e and 260a9c"
        status: pass
    human_judgment: false
  - id: D3
    description: "PR #66 retains the six owner-veto items and D-29 judgment; current lifecycle is merged at 783712c"
    requirement: "CGB-03"
    verification:
      - kind: other
        ref: "gh pr view 66 --json state,isDraft,mergedAt,headRefOid,body"
        status: pass
    human_judgment: false
  - id: D4
    description: "The immutable Phase 10 handoff commit names /gsd-verify-work 10 and Phase 11 as not started at that historical boundary"
    verification:
      - kind: other
        ref: "git show 260a9c0:.planning/.continue-here.md"
        status: pass
    human_judgment: false
status: complete
commits: 4
plan_head_before: 0b35006507d356a9fbe8c1e2cf6cdd008d1dccda
plan_head_after: 260a9c0580c76afc31c0bf5be902e51af2f8f1de
duration: 100 min
completed: 2026-10-12
---

# Phase 10 Plan 20: Evidence Head, PR and Handoff Summary

Phase 10 execution is closed with a pushed, exact-head green evidence head, PR #66 ready and left OPEN with all six owner veto items and the D-29 judgement, and a persisted route to `/gsd-verify-work 10`; Phase 11 is named and not started.

`commits: 4` and `plan_head_after` are measured from the plan ledger at the handoff head. The SUMMARY, PR body file, ROADMAP and requirement-state commit follows the handoff head and is not counted.

## Accomplishments

- Recorded LESSONS GB-CGB-001 (runner `model=dmg-cpu-b` literals: 17 sites in `acceptance.c` and 3 profile-constant sites in `main.c` on main, 5 and 1 now; remedy and `cgb_runner_profile_*` verification), the Phase 10 deferred items in FUTURE-MILESTONES, and the Phase 10 bullet in `research/INDEX.md` (links resolve, evidence classes stated).
- Ran the phase-wide gates and privacy check; all passed (see Evidence).
- Found and fixed two CI defects exposed by the first push (see Deviations), obtained the exact-head green evidence head, and published the PR body (`10-PR-BODY.md`).
- Persisted the handoff in STATE.md and `.continue-here.md` and verified the handoff head exact-head green.

## Evidence

Evidence head `2fe078e8f08ed98ba0ac0e244971e7c0ead16b1e`, read from that exact SHA (pull_request-event runs).

Required `ci` run 38299323863 (https://github.com/szTheory/gabbaboy/actions/runs/38299323863):

| Job | Result |
|---|---|
| native-linux-x64 | success |
| native-macos-arm64 | success |
| native-windows-x64 | success |
| linux-asan-ubsan | success |
| cmake-floor-3.25.3 | success |
| player-gate | success |
| macos-player-package | success |
| required-native | success |

`fixture-repro` run 38299323969 (https://github.com/szTheory/gabbaboy/actions/runs/38299323969):

| Job | Result |
|---|---|
| fixture-repro | success; CGB banking `result=byte-identical roms=2` |
| mooneye-original-repro | success |
| mooneye-candidate-repro | success |
| mooneye-mbc-repro | success |
| magentests-repro | success |
| rtc3test-repro | success |
| mooneye-cgb-repro | success; `result=byte-identical roms=4` |

`no_host_clock` passed on the hosted sanitizer leg. `preview-package-smoke` (also a required PR check) is covered under Deviations.

Handoff head `260a9c0580c76afc31c0bf5be902e51af2f8f1de` (`git diff --name-only 2fe078e..260a9c0` lists exactly `.planning/.continue-here.md` and `.planning/STATE.md`): `wait-exact-head-ci.py` with all eight `--require` options printed `PASS run_id=38302631119` (https://github.com/szTheory/gabbaboy/actions/runs/38302631119); `fixture-repro` run 38302631195 all seven jobs success. `gh pr view 66` reported OPEN, not draft, head 260a9c0.

Local (author host, loaded, load average about 10): 537/537 CTest at the evidence head with `verify-test-inventory.sh ... --installed` reporting 537 executed, none skipped; `tests/scripts/verify-phase3-player.sh --build-package` passed (SDL 3.4.18); `baseline status=pass`; `correctness_digest_fnv1a64=4c7a57ff3d50d228`; `model-gates pass functions=147 gates=76 unknown=40`; no removed line in `tests/expected-tests.txt`; `tests/baseline` unchanged; no `research:10` tag line (the only text match is prose in `docs/model-gates.md`). No local test timed out.

The `phase1-asan` preset cannot be configured on this macOS host (`GABBABOY_ENABLE_SANITIZERS is supported only on Linux`); no local ASan pass is claimed. The hosted `linux-asan-ubsan` exact-head job is the sanitizer evidence.

Privacy check over the 84 files changed since main (PLAN files excluded): no `/Users/` or `/home/` path; the single email hit is the verbatim upstream licence line in `fixtures/mooneye-cgb/LICENSE.txt`; no `.sym`, `.lnk` or `.log` under `fixtures`; no boot ROM tracked.

Triage: `gh issue list --state open` returned no open issues; `gh pr list --state open` returned only PR #66 itself. No access failure.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] CGB banking ROMs matched the `*.gb` ignore rule**
- **Found during:** Task 1 (first push; push-event `fixture-repro` failed with `FileNotFoundError: .../fixtures/cgb-banking/banking-cgb.gb`)
- **Issue:** `banking-cgb.gb` and `banking-dmg.gb` existed on disk but were never committed, so a clean checkout lacked them. Local tests passed only because the files were present. This is the failure GB-FIXTURE already warns about.
- **Fix:** Added explicit `!/fixtures/cgb-banking/...` exceptions to `.gitignore` and committed the two ROMs. Their SHA-256 values equal `fixtures/cgb-banking/manifest.json`; the exact-head rebuild printed `result=byte-identical roms=2`, so no committed bytes were altered.
- **Files modified:** `.gitignore`, `fixtures/cgb-banking/banking-cgb.gb`, `fixtures/cgb-banking/banking-dmg.gb`
- **Commit:** d407042

**2. [Rule 3 - Blocking] Windows inventory check expected the bash-only benchmark controls**
- **Found during:** Task 1 (`native-windows-x64`: 534 executed versus 537 required; `cgb_bench_ab_*` missing)
- **Issue:** `cmake/ExpectedTests.cmake` omits `cgb_bench_ab_*` under `WIN32` but `.github/scripts/verify-test-inventory.sh` did not.
- **Fix:** The script drops those three names on MINGW/MSYS/CYGWIN hosts only. Verified with a `uname` shim reporting MINGW: a report without the three tests passes; on this macOS host the same report fails as before, and the full 537-case report passes.
- **Files modified:** `.github/scripts/verify-test-inventory.sh`
- **Commit:** 2fe078e

**3. [CI timing, not a code defect] `preview-package-smoke` failed on its first run at both heads**
- **Found during:** Task 1 and Task 2 verification
- **Issue:** `installed-package-smoke-linux-x64` waits at most 1500 s for the `ci` run's `required-native`; the `linux-asan-ubsan` leg took 27 to 29 minutes on hosted runners, so the wait expired before `ci` finished (the log reads "No completed successful pull-request CI run ... appeared within 25 minutes" while `ci` was still in_progress). `ci` itself was green.
- **Fix:** None to code. After `ci` had completed successfully for each exact SHA, the failed jobs were re-run (`gh run rerun --failed` on runs 38299323803 for the evidence head and 38302631133 for the handoff head); both runs then concluded success (installed-package-smoke-linux-x64, installed-package-smoke-macos-arm64, player-package-smoke-macos and preview-package-smoke all success). Not counted against the 3 fix-and-push bound. The 1500 s deadline versus the sanitizer leg duration remains a latent flake for the owner to tune.

**4. [Process] Commit attribution trailer**
- The first task commit (4640a9d) carries the trailer `Co-Authored-By: Claude Opus 5.5` from the dispatch notes; later commits use the session attribution `Claude Sonnet 5.5`. Already pushed, not rewritten.

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking), 1 CI timing rerun, 1 process note. **Impact:** two fix-and-push cycles of the allowed three; no committed fixture bytes changed other than admitting the two previously untracked ROMs.

## Authentication Gates

None.

## Known Stubs

None added by this plan.

## Threat Flags

None. The plan changed only records, a `.gitignore` admission, one CI script and two fixture ROMs already described by their manifest.

## Owner Items

The six veto items, the +5% benchmark result (the review trigger fired: about +6 to 7 percent against the Phase 7 baseline, advisory, measured on a loaded host, 10-BENCH.md) and the D-29 judgement are in PR #66 and `10-PR-BODY.md`. PR #66 is not merged; branch protection was not touched; `workflow.auto_advance` and `workflow._auto_chain_active` remain false; Phase 11 was not started.

CGB-01..03 are not marked complete in `REQUIREMENTS.md`: the plan does not ask for it and `/gsd-verify-work 10` decides.

## Next

Phase 10 verification. Next command in fresh context: `/gsd-verify-work 10`. Following phase (named, not started): Phase 11 - CGB Colour Rendering and Player Colour.

## Self-Check: PASSED

## 15.1-19 Fresh Applicability Evidence

Historical boundary checks used immutable commits. Comparing `tests/expected-tests.txt` and `tests/baseline` between Phase 10 start `5e2b32f16fa705043c5437fb63a08bd83a4d750b` and exact evidence head `2fe078e8f08ed98ba0ac0e244971e7c0ead16b1e` found no removed expected-test lines and identical baseline trees. At that evidence commit, active `research:10` model-gate tags were absent from the core and model-gate table. This avoids using current routes or current ancestry to make a historical claim. The check was an inline Python assertion over `git show` blobs at those exact commits; no live branch diff was used.

On 2026-10-21, the current tracer workload printed `correctness_digest_fnv1a64=4c7a57ff3d50d228`; `verify-model-gates.py` passed with the current 196 functions, 100 gates, and 34 unknowns; and `verify-dmg-baseline.sh` passed with zero changed rows. Those counts are current-source evidence and do not replace the earlier recorded counts in this summary.

Read-only hosted re-queries confirmed runs 38299323863 and 38299323969 succeeded on exact SHA `2fe078e8f08ed98ba0ac0e244971e7c0ead16b1e`, while runs 38302631119 and 38302631195 succeeded on exact SHA `260a9c0580c76afc31c0bf5be902e51af2f8f1de`. PR #66 is now merged at `783712c3b3f27933210b4ade2035613e9aa840f2` (2026-10-13); its current body retains the six owner-veto items and D-29 judgment. The original handoff at `260a9c0` still names exactly `/gsd-verify-work 10` and Phase 11 as not started at that historical point. Neither historical route is asserted as the current next step.
