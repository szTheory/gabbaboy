---
phase: 16-tune-up-and-v0-2-debt-closure
plan: "01"
subsystem: test-infrastructure
tags: [archive, phase-path-lint, ctest, tune-01, hdma-lane, summary-coverage]
requires:
  - phase: 15.1-release-hardening-and-milestone-debt-closure
    provides: digest-pinned v0.2 disposition, scope and evidence records that the archive must keep byte-identical
provides:
  - verify-no-phase-paths.py, a count-pinned lint that keeps tracked tests, scripts, docs and workflows out of the live phases directory
  - The v0.2 phase records (578 files) archived under .planning/milestones/v0.2-phases as pure renames
  - Retargeted v0.2 readers with anti-vacuity minimums and a rewrite that rejects missing or escaping legacy paths
  - verify-hdma-lane.py, the HDMA lane checker extracted from the archived Phase 13 closure script
  - GBB_LIVE_PHASES_DIR, GBB_V02_PHASES_DIR and tests/cmake/areas.cmake, the per-area CTest hook for 16-02 to 16-06
affects: [16-02, 16-03, 16-04, 16-05, 16-06, 16-07]
actuals:
  tokens: 10300
  tasks: 3
  commits: 3
commits: 3
plan_head_before: 131d7ae2eabdb9f512582cce5dbd17cbf4b2b7c2
plan_head_after: f12baff8728db0c1f06771344c1d84bab804f09e
tech-stack:
  added: []
  patterns:
    - A lint pins each exception as a (file, max hits, reason) row and fails a row whose observed hits fall below its max.
    - A reader of archived records rewrites embedded legacy paths under the archive and rejects a missing or escaping result, so pinned JSON bytes never change.
key-files:
  created:
    - tests/scripts/verify-no-phase-paths.py
    - tests/scripts/verify-hdma-lane.py
    - tests/cmake/areas.cmake
    - tests/data/closeout-scan-14-uat-review.md
    - .planning/milestones/v0.2-phases/README.md
  modified:
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/scripts/verify-summary-coverage.py
    - tests/scripts/test_hdma_remote_evidence.py
    - tests/scripts/verify-closeout-dispositions.py
    - tests/scripts/verify-closeout-scan.py
    - tests/scripts/verify-historical-limitations.py
    - tests/scripts/test-cgb-red-evidence-privacy.py
    - .planning/milestones/verify-v02-milestone-audit.py
    - .planning/HANDOFF.json
    - .planning/PROJECT.md
    - .planning/MILESTONES.md
    - .gitattributes
key-decisions:
  - The v0.2 records were moved with git mv in one commit together with every reader retarget, so main never held a half-moved tree.
  - Embedded legacy paths in the digest-pinned dispositions JSON are rewritten by stripping the exact legacy prefix and rejoining under the archive; the JSON bytes are untouched.
  - The closeout-scan review seed is a byte copy pinned by SHA-256 (file(SHA256) with FATAL_ERROR on drift), not a read of the archive.
  - summary_coverage keeps its test name and now reads the archive with a 143-file floor; the live sweep is a separate test with no minimum.
requirements-completed: ["TUNE-01"]
coverage:
  - id: D1
    description: "The phase-path lint rejects each forbidden spelling (literal, joined segments, backslash, PROJECT_SOURCE_DIR prefixed) in each scope root, accepts milestone archive links, skips binaries, and fails over-max, stale and reasonless allowlist rows and an unscanned must-scan file."
    requirement: TUNE-01
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-no-phase-paths.py --self-test"
        status: pass
      - kind: integration
        ref: "ctest -R '^no_phase_paths_controls$'"
        status: pass
    human_judgment: false
  - id: D2
    description: "The lint passes on the moved tree with a count-pinned row for every scanned hit, scanning 407 files against a floor of 380."
    requirement: TUNE-01
    verification:
      - kind: integration
        ref: "ctest -R '^no_phase_paths$'"
        status: pass
    human_judgment: false
  - id: D3
    description: "Phases 7 through 15.1 (578 tracked files) are archived under .planning/milestones/v0.2-phases as pure renames, GB-16 stays live, and the v0.2 audit script moved beside the audits."
    requirement: TUNE-01
    verification:
      - kind: other
        ref: "git diff --cached -M100% --name-status shows 578 R100 renames and no modified or deleted archived file"
        status: pass
      - kind: integration
        ref: "ctest -R '^closeout_dispositions_controls$'"
        status: pass
    human_judgment: false
  - id: D4
    description: "Every v0.2 reader reads the archive; the dispositions checker rewrites embedded legacy paths and rejects missing or escaping ones with distinct codes, and the historical glob must match a file."
    requirement: TUNE-01
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-closeout-dispositions.py --self-test"
        status: pass
      - kind: integration
        ref: "ctest -R '^(historical_limitations_controls|cgb_corpus_red_evidence_privacy|uat_closure_controls)$'"
        status: pass
    human_judgment: false
  - id: D5
    description: "verify-summary-coverage.py has no default phases directory and gains --min-files; the v0.2 sweep asserts at least 143 files and an empty directory is rejected."
    requirement: TUNE-01
    verification:
      - kind: integration
        ref: "ctest -R '^(summary_coverage|summary_coverage_live|summary_coverage_empty_dir_rejected|summary_coverage_selftest)$'"
        status: pass
    human_judgment: false
  - id: D6
    description: "The HDMA lane checker lives in tests/scripts without the ASan timeout, parallelism or TIMEOUT assertions, gains a fixture-repro needle control, and the orphaned Node handoff test is gone."
    requirement: TUNE-01
    verification:
      - kind: integration
        ref: "ctest -R '^(cgb_hdma_lane_contract|cgb_hdma_lane_contract_selftest|cgb_hdma_remote_evidence_selftest)$'"
        status: pass
    human_judgment: false
  - id: D7
    description: "The per-area CTest hook is included exactly once before the inventory check and sanitizer scaling, and the full suite including dmg_baseline passes after the move."
    requirement: TUNE-01
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error (1187 of 1187 passed)"
        status: pass
      - kind: integration
        ref: "ctest -R '^dmg_baseline$'"
        status: pass
      - kind: other
        ref: "git diff --quiet merge-base HEAD -- src include"
        status: pass
    human_judgment: false
duration: 30min
completed: 2026-10-24
status: complete
---

# Phase 16 Plan 01: v0.2 archive and phase-path lint Summary

**The 578 v0.2 phase records now live under `.planning/milestones/v0.2-phases` as pure renames, every reader is retargeted with an anti-vacuity floor, and a count-pinned lint (`no_phase_paths`) keeps tracked files from reading the live phases directory.**

## Performance

- **Duration:** about 30 min of wall-clock work, plus a fresh configure, build and full CTest run
- **Tasks:** 3 (one tracer, two auto)
- **Files:** 597 changed in the diff (578 are pure renames), 19 in the plan footprint plus `.gitattributes`

## Accomplishments

- Task 1 (tracer): `verify-no-phase-paths.py` with 17 self-test controls, `GBB_LIVE_PHASES_DIR` and `GBB_V02_PHASES_DIR`, and the one `include()` of `tests/cmake/areas.cmake`, wired end to end through `no_phase_paths_controls`.
- Task 2: `verify-hdma-lane.py` extracted from the archived Phase 13 closure script (3 lane-self-test controls), `phase13-handoff-continuity.test.cjs` deleted, `verify-summary-coverage.py` made default-free with `--min-files`.
- Task 3: the atomic archive move, retargeted readers, pinned minimums, the digest-pinned review seed, `no_phase_paths` registered, and live navigation repointed.

## TUNE-01 interpretation (D-07)

TUNE-01 is read per D-07 (owner-disclosed interpretation, 2026-10-24): no test reads completed-milestone records from the live phases directory, and current-milestone live reads go only through GBB_LIVE_PHASES_DIR, which the lint allowlists.

## Pinned counts (all measured on the tree)

Lint floor: `GBB_EXPECT_MIN_VALUE=380` on `files=`; observed `files=407 allowlisted=6`. Allowlist rows:

| File | Pinned hits | Why |
| --- | --- | --- |
| tests/CMakeLists.txt | 1 | GBB_LIVE_PHASES_DIR definition (D-07) |
| tests/scripts/verify-phase8-closure-contract.py | 1 | PHASE constant for boundary-commit reads (D-06) |
| tests/scripts/verify-closeout-dispositions.py | 1 | legacy-prefix rewrite for archived records |
| tests/scripts/verify-closeout-scan.py | 4 | temp-fixture layout strings |
| tests/data/closeout-scan-14-uat-review.md | 6 | byte copy of the archived 14-UAT-REVIEW.md seed (D-08) |
| tests/scripts/verify-no-phase-paths.py | 12 | the lint's own spelling patterns and self-test fixtures |

Sweep and control minimums:

- `summary_coverage`: v0.2 archive, `--since 9 --min-files 143` and `GBB_EXPECT_MIN_VALUE=143` on `files=`; observed `files=143 entries=546`.
- `summary_coverage_live`: live directory, `--since 16`, no minimum (tolerates zero summaries).
- `summary_coverage_empty_dir_rejected`: `tests/data` with `--min-files 1` must exit 1 with "below minimum".
- `no_phase_paths_controls`: `controls` minimum 12; observed 17.
- `uat_closure_controls`: existing `controls` minimum 21, now on the archived GB-15 directory.
- `closeout_dispositions_controls`: observed `positives=3 rejected_controls=33` (3 new controls for the archive rewrite).
- `cgb_corpus_red_evidence_privacy` fails when any of its five named records is absent; `historical_limitations_controls` now fails when the Phase 12 glob matches nothing.
- `LABELS planning` is set on all of the above, and `ctest -L planning` runs 13 tests, all passing.

## D-10 rows

`git grep -n 15.1-VALIDATION -- tests .github` returns no hits, so no CTest reads the archived 15.1 validation file. Rows 34-1, 34-2, 35-2, 35-3, 36-1, 36-2 and 36-3 go to the 16-06 disposition record as superseded by the Phase 16 archive. No archived file was edited.

## Verification

- `python3 -I tests/scripts/verify-no-phase-paths.py --check` passes (`files=407 allowlisted=6`); `--self-test` passes (`controls=17`); `python3 -O` is refused.
- Fresh configure, build and full `ctest --preset phase1`: 1187 of 1187 passed, including `dmg_baseline` with no changed rows.
- `git diff -M100%` shows 578 `R100` renames and no modified or deleted archived file; `git diff --quiet <merge base> HEAD -- src include` holds (D-04).
- `python3 .planning/milestones/verify-v02-milestone-audit.py --self-test` still reconciles after the move (26 controls).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Moved audit script resolved the wrong repository root**
- **Found during:** Task 3
- **Issue:** `.planning/milestones/verify-v02-milestone-audit.py` derived `ROOT` with `parent.parent`, which is `.planning/` after the move.
- **Fix:** `ROOT = Path(__file__).resolve().parents[2]`; the script is no longer a pure rename (R099) and its self-test passes.
- **Files modified:** .planning/milestones/verify-v02-milestone-audit.py
- **Commit:** f12baff

**2. [Rule 2 - Missing critical] Digest-pinned seed needed a line-ending attribute**
- **Found during:** Task 3
- **Issue:** the SHA-256 pin on `tests/data/closeout-scan-14-uat-review.md` would drift on a Windows checkout without an eol attribute.
- **Fix:** `.gitattributes` gains `tests/data/closeout-scan-14-uat-review.md text eol=lf`, matching the existing malformed-summary fixture.
- **Files modified:** .gitattributes
- **Commit:** f12baff

**3. [Rule 1 - Bug] `--phases-dir` could not be required unconditionally**
- **Found during:** Task 2
- **Issue:** `--file` and `--self-test` runs (the invalid-fixture CTests and the archived HDMA closure check) never sweep a directory.
- **Fix:** the flag is required only for a sweep (argparse error, exit 2); the single success line is unchanged.
- **Files modified:** tests/scripts/verify-summary-coverage.py
- **Commit:** 1e4a105

**4. [Rule 3 - Blocking] Historical-limitations self-test fixture carried a live-path string**
- **Found during:** Task 3
- **Issue:** a synthetic changed-path value spelled the live directory only to start with `.planning/`.
- **Fix:** it now spells the archive path, which keeps the same prefix behavior and removes an allowlist row.
- **Files modified:** tests/scripts/verify-historical-limitations.py
- **Commit:** f12baff

**Total deviations:** 4 auto-fixed (1 bug, 1 missing critical, 2 blocking). **Impact:** none on scope; all stay inside the plan's files plus `.gitattributes`.

The plan said to work on a branch cut from main (`gsd/phase-16-01-archive`). The executor instructions fixed the branch to `gsd/phase-16-tune-up-and-v0-2-debt-closure`, so all commits are on that branch and no PR was opened here.

## Deferred Issues

`python3 -I tests/scripts/verify-closeout-scan.py --self-test` reports 1 failure and 1 error (the installed OpenGSD runtime does not return the review row the test expects). The same result occurs on the pre-move tree at `131d7ae`, so it is not caused by this plan. No CTest runs this script, and the seed it reads is now the pinned copy. Logged in `deferred-items.md` in this phase directory.

## Known Stubs

None.

## Threat Flags

None. The only new trust-boundary logic is the legacy-path rewrite (T-16-02), which strips the exact prefix, rejects `..` and absolute tails, and rejects a missing rewritten file with `archived-record-missing`; three self-test controls prove each rejection.

## Self-Check: PASSED

- Created files exist: `tests/scripts/verify-no-phase-paths.py`, `tests/scripts/verify-hdma-lane.py`, `tests/cmake/areas.cmake`, `tests/data/closeout-scan-14-uat-review.md`, `.planning/milestones/v0.2-phases/README.md`.
- Task commits `654018b`, `1e4a105` and `f12baff` are ancestors of HEAD.
- Plan verification commands for all three tasks and the wave-level full suite ran and passed.
