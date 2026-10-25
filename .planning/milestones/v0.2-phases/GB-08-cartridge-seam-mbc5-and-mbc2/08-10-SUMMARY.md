---
phase: 08-cartridge-seam-mbc5-and-mbc2
plan: 10
subsystem: release-evidence
tags: [exact-head-ci, privacy-check, pr-readiness, triage, handoff]
requires: [08-09]
provides:
  - "Phase-wide gates and privacy check passed at the evidence head"
  - "Green exact-head evidence head with all eight required jobs and four fixture-repro jobs"
  - "PR #64 marked ready (not draft) with a CART-01/02/03 requirement-to-evidence table"
  - "Handoff route to /gsd-verify-work 8 in STATE.md and .continue-here.md"
affects: [phase 8 verification, phase 9]
key-files:
  created: []
  modified:
    - .planning/STATE.md
    - .planning/.continue-here.md
requirements-completed: [CART-01, CART-02, CART-03]
status: complete
duration: 45 min
completed: 2026-10-11
commits: 0
plan_head_before: a3f27f71c10838e372f27d8c2fcf0070123b0919
plan_head_after: a3f27f71c10838e372f27d8c2fcf0070123b0919
actuals:
  tokens: 9000
  tasks: 2
  commits: 0
coverage:
  - id: D1
    description: "Phase-wide gates (additions-only inventory, frozen paths, no baseline: commits, no 0x03u literal, JOYP and ninth-bit anchors once, baseline status=pass)"
    human_judgment: false
    verification:
      - kind: other
        ref: "python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"
        status: pass
  - id: D2
    description: "Exact-head CI at the evidence head: eight required jobs and four fixture-repro jobs success"
    human_judgment: false
    verification:
      - kind: other
        ref: "python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"
        status: pass
  - id: D3
    description: "Historical PR #64 readiness and open/unmerged receipt retained with its exact producer"
    human_judgment: false
    verification:
      - kind: other
        ref: "python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"
        status: pass
  - id: D4
    description: "Historical phase pause and verification route persisted in STATE and continuation with auto flags false"
    human_judgment: false
    verification:
      - kind: other
        ref: "python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"
        status: pass
  - id: D5
    description: "Historical privacy scan records no personal paths and only the permitted upstream licence address"
    human_judgment: false
    verification:
      - kind: other
        ref: "python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"
        status: pass
  - id: D6
    description: "Historical boundary triage records no open issues and PR64 disposition"
    human_judgment: false
    verification:
      - kind: other
        ref: "python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"
        status: pass
---

# Phase 8 Plan 10: Exact-head evidence, PR readiness and handoff Summary

Phase 8 execution is closed: the evidence head `a3f27f7` passes every phase-wide gate, all eight required CI jobs and all four fixture-reproduction jobs at its exact SHA, PR #64 is ready for review and unmerged, and the route `/gsd-verify-work 8` is persisted.

## Performance

- **Duration:** about 45 min, mostly waiting on hosted CI
- **Tasks:** 2 (Task 1 tracer committed nothing; Task 2 handoff files)
- **Files modified:** 2 tracked handoff files plus this SUMMARY and ROADMAP

## Phase-wide gates (evidence head)

All run at `a3f27f71c10838e372f27d8c2fcf0070123b0919`:

- `git diff -U0 main...HEAD -- tests/expected-tests.txt` has no `-` line (additions only).
- `git diff --quiet main...HEAD -- tests/baseline fixtures/mooneye cmake/VerifyMooneye.cmake tests/scripts/reproduce-mooneye.sh` exits 0.
- `git log main..HEAD --format=%s | grep '^baseline:'` prints nothing.
- `grep -rc 'cartridge_type == 0x03u' src` is 0 in every file.
- `grep -cF 'joypad_select & 0x20u) ==' src/core/gabbaboy.c` prints 1 and `grep -c '& 1u) << 8' src/core/gabbaboy.c` prints 1 (D-29 anchor retained; the ninth-bit mutant CTests are `mbc5_ninth_bit_mutant_bank_1ff` and `mbc5_ninth_bit_mutant_control_below_100`, D-29 amended in 391e969, DECISIONS D-062).
- `bash tests/scripts/verify-dmg-baseline.sh` prints `baseline status=pass`.
- Local: `cmake --preset phase1`, build and full ctest 319/319 passed; `verify-test-inventory.sh build/ctest.xml tests/expected-tests.txt --installed` printed `Verified 319 executed CTest cases; none skipped.` (the default core-only mode reports a mismatch because the installed_* cases ran locally; the plan command omits `--installed`).
- `bash tests/scripts/verify-phase3-player.sh --build-package` passed (package SHA-256 `9623c103...0cc7`).
- `cmake --preset phase1-asan` cannot configure on macOS ("GABBABOY_ENABLE_SANITIZERS is supported only on Linux"). Substitute: a manual local ASan/UBSan build (clang `-fsanitize=address,undefined`, Debug, outside the tree) ran the mbc/cart/battery/save/rom/Mooneye-mbc subset, 76/76 passed. The authoritative sanitizer evidence is the hosted `linux-asan-ubsan` job.

## Privacy check

Over `git diff --name-only --diff-filter=d main...HEAD` excluding planning `*-PLAN.md` (83 files): zero `/(Users|home)/<name>/` matches. One email match: `fixtures/mooneye-mbc/LICENSE.txt:1` (`joonas.javanainen@gmail.com`), the verbatim upstream Mooneye MIT licence text, permitted by the plan. `git ls-files fixtures | grep -E '\.(sym|lnk|log)$'` prints nothing.

## Exact-head CI evidence

- **Evidence head** `a3f27f71c10838e372f27d8c2fcf0070123b0919` (no fix commits were needed; the head was already pushed, fix cycles used 0 of 3).
- **ci** run 38155767928 (https://github.com/szTheory/gabbaboy/actions/runs/38155767928), pull_request, attempt 1. `wait-exact-head-ci.py` with all eight `--require` options printed `PASS run_id=38155767928 run_attempt=1`. Jobs read from that run: native-linux-x64 success, native-macos-arm64 success, native-windows-x64 success, linux-asan-ubsan success, cmake-floor-3.25.3 success, player-gate success, macos-player-package success, required-native success.
- **fixture-repro** run 38155768038 (https://github.com/szTheory/gabbaboy/actions/runs/38155768038), pull_request: fixture-repro success, mooneye-original-repro success, mooneye-candidate-repro success, mooneye-mbc-repro success.
- `baseline status=pass` printed in the log of all three native jobs.
- `preview-package-smoke` (run 38155767957) is not a required job; it was still running when the required gate passed and is not counted as evidence here.

## Requirement-to-evidence (honest status)

| Requirement | Status | Note |
|---|---|---|
| CART-01 | delivered | Differential `differences=0` (86016, 85344, 83328 cells), frozen digest unchanged, baseline pass. |
| CART-02 | delivered | MBC5 unit cases, Mooneye mbc5 8/8, original fixture, two ninth-bit mutant CTests. 08-07 SUMMARY status is `partial` only because D-29 was amended (mutant realized as two CTests, DECISIONS D-062); the anchor is still required exactly once. |
| CART-03 | delivered | MBC2 unit cases, Mooneye mbc2 7/7, MBC2A caveat stated. |

Documented limits carried into the PR body and handoff: `rom_64Mb` does not exercise banks at or above 256; the 08-04 player status line has no automated UI test; `phase1-asan` cannot configure on macOS so sanitizer evidence is hosted `linux-asan-ubsan` plus manual local builds; no hardware MBC observation, no CGB, player persistence MBC1 only, rumble is a query without haptics.

## PR

PR #64 body replaced with the requirement-to-evidence table, run URLs and limits (ends with the session attribution line) and marked ready with `gh pr ready 64`. `gh pr view 64` read back `isDraft=false state=OPEN headRefOid=a3f27f7...`. Not merged: the owner's pre-authorized squash merge follows `/gsd-verify-work 8`.

## Phase-boundary triage

- `gh issue list --state open`: no open issues (no access failure). Disposition: no action.
- `gh pr list --state open`: one, #64 "Phase 8: Cartridge seam, MBC5 and MBC2" (this phase's PR). Disposition: ready for review and unmerged until verification passes.
- Notes for Phase 9: GitHub source archives include `fixtures/mooneye-mbc` (about 17 MiB of test ROMs, no `export-ignore`); revisit at the release boundary. Player persistence for MBC2/MBC5 is deferred.

## Task Commits

1. **Task 1 (tracer): gates, privacy, evidence head, PR ready, triage** - no tracked change.
2. **Task 2: handoff** - STATE.md and .continue-here.md committed with this SUMMARY and ROADMAP (planning files only).

## Deviations from Plan

**1. [Rule 3 - Format] Wait command options.** The plan's verify commands omit the mandatory `--require` options of `wait-exact-head-ci.py`; all eight were supplied (as in 07-16). The inventory command also needed `--installed` locally.

**2. [Rule 3 - Format] Handoff commit scope.** The close-out order (SUMMARY commit, then STATE, ROADMAP and .continue-here) means commits after the evidence head touch the SUMMARY and ROADMAP.md as well as the two planned files. All of them change only `.planning/` files.

**3. [Rule 3 - Sequencing] Handoff head recorded by addendum.** A commit cannot name its own SHA, so the handoff head's exact-head result is appended below in a final docs-only commit; that final head is read in turn and reported in the completion message.

**4. [Rule 3 - Tooling] ASan preset.** Substituted a manual local sanitizer build on macOS (see above); hosted CI is the evidence.

**Total deviations:** 4 (procedural). **Impact:** none on content.

## Issues Encountered

None.

## Known Stubs

None.

## Threat Flags

None. Planning records only; T-08-36 only exact-head results counted, T-08-37 privacy check clean (one verbatim upstream licence email), T-08-38 no merge and no protection change, T-08-SC no package installs.

## Self-Check: PASSED

- Evidence head `a3f27f7` is an ancestor of HEAD; run 38155767928 and 38155768038 read from that exact SHA.
- `.planning/config.json` keeps `auto_advance` and `_auto_chain_active` false.

## Handoff heads

- **Handoff head** `cea55b28e32f320b14e47d921545e410ab4c5711` (STATE.md, .continue-here.md, ROADMAP.md, REQUIREMENTS.md, state.json and the first version of this SUMMARY; planning files only), ci run 38157465103 (https://github.com/szTheory/gabbaboy/actions/runs/38157465103), pull_request, attempt 1, `wait-exact-head-ci.py` with all eight `--require` options printed `PASS`. Jobs: native-linux-x64 success, native-macos-arm64 success, native-windows-x64 success, linux-asan-ubsan success, cmake-floor-3.25.3 success, player-gate success, macos-player-package success, required-native success. fixture-repro run 38157465090 success.
- `gh pr view 64` read back `state=OPEN isDraft=false headRefOid=cea55b28...` at that head. Not merged.
- This addendum is a further docs-only commit (this SUMMARY only); its own exact-head result is reported in the completion message.
