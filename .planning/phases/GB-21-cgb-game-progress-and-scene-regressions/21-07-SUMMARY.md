---
phase: GB-21-cgb-game-progress-and-scene-regressions
plan: "07"
subsystem: testing
tags: [CGB, native acceptance, candidate evidence, CTest]
requires:
  - phase: GB-21-cgb-game-progress-and-scene-regressions
    provides: Native CGB progress, ordered fixture-admission records, and scene-report contracts from Plans 21-01 through 21-06.
provides:
  - A source-bound composition checker and mutation controls for the two candidate outcomes, original harness result, and scene-workflow claims.
  - Current Phase 21 outcome documentation, qualification evidence, and an explicit phase-boundary handoff.
affects: [Phase 22 composition evidence, Phase 23 release evidence]
actuals:
  tokens: 38540
  tasks: 2
  commits: 30
tech-stack:
  added: []
  patterns:
    - Compose existing Python-standard-library checkers using one immutable full source revision.
    - Reject unsupported evidence claims with content-caused mutation controls.
key-files:
  created:
    - tests/scripts/verify-cgb-game-evidence.py
    - tests/cmake/game-evidence.cmake
  modified:
    - docs/game-acceptance.md
    - docs/cgb-profile.md
    - docs/support/unreleased.md
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/data/state-forks.json
    - tests/scripts/verify-cgb-candidates.py
    - tests/scripts/verify-cgb-progress.py
    - tests/scripts/verify-fixture-admission.py
    - tests/scripts/verify-scene-report.py
    - .planning/context/LESSONS.md
    - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-VALIDATION.md
    - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-07-REVIEW.md
    - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/deferred-items.md
    - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/.continue-here.md
    - .planning/STATE.md
    - .planning/ROADMAP.md
key-decisions:
  - "Both named candidates remain rights/source-scope no-go outcomes; no license prohibition is inferred."
  - "FIXT-01 remains pending because neither game's build, ROM bytes, cartridge header, or native mode was observed."
  - "The original project-authored CGB ROM is harness evidence only; its repeatable RGB555/PCM digests do not establish accuracy or real-game progress."
  - "Keep both descriptor-less plan prohibitions visible and unresolved as required by the plan."
  - "Windows synthetic controls invoke Python scripts through the active interpreter and query the same CTest configuration they execute."
  - "Normalize Windows CTest command separators before matching synthetic scene source paths, with an explicit mixed-separator control."
  - "Run nested scene CTests with the same explicit Debug configuration used for discovery and retain CTest diagnostics on rejection."
patterns-established:
  - "A result receipt binds candidate facts, harness evidence, runner identity, and documentation to one full source revision."
  - "Claim mutations target each candidate/license statement independently so one valid claim cannot mask an unsupported one."
requirements-completed: [GAME-01, GAME-02, FEED-01]
coverage:
  - id: D1
    description: Source-bound CGB outcome composes current candidate facts and the original harness result, rejecting missing evidence and unsupported game, accuracy, or hardware claims.
    requirement: GAME-02
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_game_evidence(_controls)?$'"
        status: pass
      - kind: other
        ref: "verify-cgb-game-evidence.py --check at source fdd3454a0ee6c2aa37dcd56666e1699c59cb55bf; build/phase21-evidence/result.json"
        status: pass
    human_judgment: false
  - id: D2
    description: Ordered candidate records retain the bounded two-candidate no-go outcome and reject identity, rights-claim, and source-pin mutations.
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission(_contract|_controls)?$'"
        status: pass
    human_judgment: false
  - id: D3
    description: Scene-report documentation preserves independent regression expectations, owner agency, and private-media boundaries.
    requirement: FEED-01
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_scene_report_.*$'"
        status: pass
    human_judgment: false
  - id: D4
    description: The final configured implementation passes the complete registered CTest suite and the fixed test-budget gate.
    requirement: GAME-01
    verification:
      - kind: integration
        ref: "cmake -S . -B build && cmake --build build && ctest --test-dir build --output-on-failure --timeout 60 --parallel 1 — source fdd3454a0ee6c2aa37dcd56666e1699c59cb55bf; 1724/1724 in 1220.71s"
        status: pass
    human_judgment: false
duration: 533min
completed: 2026-11-02
commits: 30
plan_head_before: 9f7bda3787d69f726a7ef2e63fa4b2c65be7ad63
plan_head_after: fdd3454a0ee6c2aa37dcd56666e1699c59cb55bf
status: complete
---

# Phase GB-21 Plan 21-07: Source-Bound Outcome and Qualification Summary

**The final receipt binds a harness-only CGB result and two rights/source-scope no-go outcomes to the reviewed source without implying game progress or license prohibition.**

## Performance

- **Duration:** 533 minutes
- **Started:** 2026-11-02T03:58:54Z
- **Completed:** 2026-11-02
- **Tasks:** 2
- **Files modified:** 17

## Accomplishments

- Added a source-bound outcome composer that reuses the progress, candidate, and scene-report checkers and rejects missing evidence, contradictory candidate claims, and overbroad accuracy, hardware, or game-progress language.
- Recorded the final no-go outcome with its evidence limits. Potion Panic's exact source/component grants and repository/public-CI scope were not established after the creator-linked repository fetch failed. µCity 1.3 source commit `d1880a2a112d7c26f16c0fc06a15b6c32fdc9137` was identified, but the required `source/engine/hardware.inc` has no identified grant or notice. These are unresolved rights/source-scope outcomes, not claims that either license prohibits use.
- Kept both game's build, ROM, digest, cartridge-header and execution facts `not_observed`; no third candidate or fallback fixture/case/input/predicate/notice row was created. `FIXT-01` therefore remains pending.
- Qualified the original authored CGB control at source `66ee663ba8f7a505d67871fab7163b57306d0dd2`. It remains harness-only under model `CGB-CPU-E`, native CGB mode; digest repeatability does not establish game progress, rendering accuracy, physical hardware behavior, perceptual quality, mode-3 timing, or general compatibility.
- Preserved the existing DMG baseline and the scene workflow's independent expectation, owner-agency, and private-media boundaries. Both descriptor-less plan prohibitions remain explicitly unresolved.
- Configured and built the implementation at `fdd3454a0ee6c2aa37dcd56666e1699c59cb55bf`, then passed all 1,724 registered CTests serially in 1,220.71 seconds with the per-test timeout fixed at 60 seconds. `test_budget` passed; no budget baseline refresh or unrelated v0.3 repair was made.
- Closed Windows-only synthetic-control failures found in host diagnostics: normalize CMake and CTest command paths, preserve explicit UTF-8 bytes in pinned fixtures, execute Python test runners through the active interpreter, and inspect CTest in the same Debug configuration used to run it. The mixed-separator control and full local suite pass at the fixed source.
- Produced a source-qualified receipt at `build/phase21-evidence/result.json`; it records `game=not-admitted`, model `CGB-CPU-E`, and mode `cgb`. The independent review is clean at `893ecac8`; executor follow-up review found no new security surface in the Windows fixes. PR #140 remains the authority for exact-head hosted/platform and installed-consumer status; push-event results are diagnostic only.

## Task Commits

Task 1 established the TDD contract and implementation: `cd339510` (test) and `a7e37b6e` (feature). Its isolated pre-GREEN test replay failed at the intended missing-outcome assertion; the recorded target/semantic check passed, and the implementation then passed the contract suite.

Task 2 and attributable follow-up fixes were committed individually:

1. `cd919d63` classify the integrated test correctly.
2. `d9fac798` bind state-fork cases to Phase 21 source.
3. `213c9081` reject contradictory CGB claims.
4. `8a784907` cover candidate rights-claim variants.
5. `1e328e66` reject candidate license overclaims.
6. `063cc849` write evidence under the canonical build path.
7. `2c49bb76` remove redundant per-mutation checker work.
8. `948d414a` allow the primary evidence run during a fallback identity control.
9. `15cb0c31`, `a0a82f99`, `72845e23`, `9a0ab07d`, and `a58c52dd` tighten license-claim negation, repeated-claim isolation, and contrastive claim handling.
10. `cbfda907` qualify evidence checks across platforms.
11. `6d14f9d1` verify the complete CTest inventory.
12. `d066a0fb` preserve spaced dump paths.
13. `3713b8e5` record local qualification evidence.
14. `b8f80f48` accept CRLF admission pins.
15. `893ecac8` reject bare-CR admission pins.
16. `e0b5305d` normalize CMake source paths and preserve exact synthetic pin bytes on Windows.
17. `9bed35ce` invoke Python synthetic runners through the active interpreter and list tests in the matching Debug configuration.
18. `66ee663b` normalize CTest command-path separators and add a Windows mixed-separator synthetic control.
19. `fdd3454a` run the nested scene CTest checks in the same Debug configuration used for discovery and preserve failure output.

**Plan commit range:** 30 commits measured from the persisted ledger base `9f7bda3787d69f726a7ef2e63fa4b2c65be7ad63` through `fdd3454a0ee6c2aa37dcd56666e1699c59cb55bf`; the final metadata commit follows this measured endpoint.

## Files Created/Modified

- `tests/scripts/verify-cgb-game-evidence.py` and `tests/cmake/game-evidence.cmake` — compose and register the immutable-source outcome receipt and negative controls.
- `tests/scripts/verify-cgb-candidates.py`, `verify-cgb-progress.py`, `verify-fixture-admission.py`, `verify-scene-report.py`, `tests/CMakeLists.txt`, `tests/expected-tests.txt`, and `tests/data/state-forks.json` — complete platform, source-pin, timing, and test-inventory coverage.
- `docs/game-acceptance.md`, `docs/cgb-profile.md`, and `docs/support/unreleased.md` — state the actual candidate/harness outcome and limits.
- `21-VALIDATION.md`, `21-07-REVIEW.md`, `deferred-items.md`, `.continue-here.md`, and `.planning/context/LESSONS.md` — record local evidence, review, budget resolution, causes, and handoff.
- Windows synthetic-control portability fix: `tests/scripts/verify-scene-report.py`, `verify-fixture-admission.py`, and `verify-cgb-candidates.py`.

## Decisions Made

- Keep Potion Panic and µCity 1.3 as no-go outcomes because repository/public-CI source scope could not be established for the exact candidate inputs. Do not infer that a license prohibits use.
- Do not close `FIXT-01`: the required exact source/build, ROM identity, cartridge header, and CGB execution observations were not produced.
- Preserve the harness-only label and software-model boundary for the original control. Keep physical, perceptual, timing, and broad compatibility questions unqualified.
- Preserve both descriptor-less prohibitions as unresolved statements; the plan does not authorize turning them into automated passes or removing them.
- Resolve the test-budget failure by eliminating unnecessary repeated work in mutation controls. Retain the deterministic 60-second budget, without refreshing its baseline or repairing unrelated v0.3 debt.

## Deviations from Plan

### Auto-fixed Issues

1. **Rule 3 — fixture-admission controls exceeded the 60-second project budget.**
   - **Found during:** Task 2 final qualification.
   - **Issue:** The fixture-admission CTests originally declared 120 and 180 seconds while `test_budget` fixes the project cap at 60 seconds.
   - **Fix:** Removed redundant full-checker work per mutation and retained explicit 60-second limits. The final checks took 3.44 and 18.48 seconds; `test_budget` passed. No timeout or baseline increase.
   - **Files modified:** `tests/scripts/verify-cgb-candidates.py`, `tests/cmake/game-evidence.cmake`.
   - **Commits:** `2c49bb76`, `3713b8e5`.

2. **Rule 1 — fixture-admission test subjects needed immutable identity and platform-safe handling.**
   - **Found during:** Task 2 review and stale hosted-run diagnosis.
   - **Issue:** Phase 21 state-fork cases referenced the wrong source identity; the registered-test comparison was order-sensitive; Windows scene tests omitted Debug configuration; Windows dump parsing truncated paths with spaces; Windows checkout normalized fixture pins to CRLF; and a permissive parser accepted a bare CR.
   - **Fix:** Pinned the intended source, compared the complete test inventory, selected the Debug config, preserved quoted/unquoted spaced paths, accepted only absent/LF/CRLF pin endings, and added a bare-CR negative control. The focused checks and final full suite passed.
   - **Files modified:** `tests/data/state-forks.json`, `tests/CMakeLists.txt`, `tests/expected-tests.txt`, `tests/scripts/verify-cgb-progress.py`, `tests/scripts/verify-fixture-admission.py`, `tests/scripts/verify-scene-report.py`.
   - **Commits:** `d9fac798`, `cbfda907`, `6d14f9d1`, `d066a0fb`, `b8f80f48`, `893ecac8`.

3. **Rule 1 — claim controls needed to distinguish each license statement.**
   - **Found during:** Task 1 integrated mutation testing and review.
   - **Issue:** Generic negation and mixed/repeated candidate statements could obscure a positive overclaim or reject a correctly scoped unresolved statement.
   - **Fix:** Scoped negation and contrastive claim parsing to individual candidate/license statements; added controls for repeated, mixed, and contrastive claims. Independent review closed the resulting findings.
   - **Files modified:** `tests/scripts/verify-cgb-game-evidence.py`.
   - **Commits:** `213c9081`, `8a784907`, `1e328e66`, `15cb0c31`, `a0a82f99`, `72845e23`, `9a0ab07d`, `a58c52dd`.

4. **Rule 1 — source receipt and documentation checks needed canonical, cross-platform identities.**
   - **Found during:** Task 2 CMake-floor/ASan/hosted review.
   - **Issue:** The CMake-floor checker rejected a generated evidence path, integrated output was not canonical under the build tree, and CTest registration/suite results varied by platform.
   - **Fix:** Constrained output to the canonical build evidence directory and qualified registration and result checks across the supported CI runners. No third-party tool or dependency was added.
   - **Files modified:** `tests/scripts/verify-cgb-game-evidence.py`, `tests/cmake/game-evidence.cmake`, `tests/CMakeLists.txt`.
   - **Commits:** `063cc849`, `948d414a`, `cbfda907`, `6d14f9d1`.

5. **Rule 1 — the new lesson identifier collided with an existing ledger entry.**
   - **Found during:** First full CTest run.
   - **Issue:** `lessons_unique_ids` rejected duplicate `GB-CGB-001`.
   - **Fix:** Assigned the new lesson unique ID `GB-CGB-015`; its focused check and final full suite passed.
   - **Files modified:** `.planning/context/LESSONS.md`.
   - **Commit:** `3713b8e5`.

6. **Rule 1 — Windows synthetic controls compared platform-formatted paths and newline-translated pinned bytes.**
   - **Found during:** Exact-source host diagnostic on Windows, after Task 2.
   - **Issue:** CMake writes its cache path with normalized separators; the checker used a byte-for-byte path comparison. Windows `Path.write_text()` also translated synthetic LF text to CRLF before Git's explicit `eol=lf` attribute stored LF, making the current notice differ from its immutable synthetic pin.
   - **Fix:** Compare the configured source path using `os.path.normpath()` and `os.path.normcase()`. Serialize byte-pinned generated manifests/notices with explicit UTF-8 `write_bytes()`.
   - **Files modified:** `tests/scripts/verify-scene-report.py`, `tests/scripts/verify-fixture-admission.py`, `tests/scripts/verify-cgb-candidates.py`.
   - **Commit:** `e0b5305d`.

7. **Rule 1 — Windows synthetic controls assumed scripts were directly executable and queried the wrong CTest configuration.**
   - **Found during:** Exact-source host diagnostic on Windows.
   - **Issue:** A repository-contained `.py` acceptance runner was launched as a native executable, and scene-test inventory lookup inspected the default configuration while execution used `Debug`.
   - **Fix:** Invoke Python scripts through `sys.executable -I` and pass `-C Debug` to the test inventory query.
   - **Files modified:** `tests/scripts/verify-cgb-candidates.py`, `tests/scripts/verify-scene-report.py`.
   - **Commit:** `9bed35ce`.

8. **Rule 1 — Windows CTest command paths used a different separator from `pathlib.Path`.**
   - **Found during:** Exact-source Windows push diagnostic after Task 2.
   - **Issue:** The synthetic scene promotion control rejected its positive CTest command because CTest JSON used forward slashes while the checker constructed a backslash-form Windows path.
   - **Fix:** Normalize both command and expected source tokens with `os.path.normcase()` and slash normalization; add a mixed-separator Windows command control.
   - **Files modified:** `tests/scripts/verify-scene-report.py`.
   - **Commit:** `66ee663b`.

9. **Rule 1 — the synthetic scene promotion control listed and executed CTest in different configurations.**
   - **Found during:** Exact-head Windows diagnostic at `e2fbe20c`.
   - **Issue:** Test discovery explicitly selected `Debug`, but the nested execution omitted `-C Debug`; Windows CTest then failed the synthetic positive promotion check.
   - **Fix:** Pass the same `Debug` configuration to the nested run and retain its stdout/stderr in the bounded rejection reason. The three focused scene-report CTests and all 1,724 local CTests pass.
   - **Files modified:** `tests/scripts/verify-scene-report.py`.
   - **Commit:** `fdd3454a`.

**Total deviations:** 9 recorded fixes across the two tasks and hosted diagnostics. **Impact:** Kept the planned evidence scope and project limits; no baseline, timeout budget, dependency, third candidate, or unrelated release debt was added.

## Issues Encountered

- The TDD RED evidence record is a replay of the immutable test-only snapshot because the initial harness output was not retained. The recorded target failed specifically because the candidate-outcome function returned `None`; the semantic assessment ruled out discovery/setup failures. The GREEN implementation passed.
- The plan's example source argument `HEAD` did not always match the runner's build-stamped source after documentation commits. Final receipt uses the full immutable source hash explicitly.
- One earlier full-suite run found the lesson-ID collision; after its fix, the final source run passed completely.
- The first sandbox-restricted final CTest attempt had five unrelated v0.2/performance/release-review controls fail because the sandbox denied writes to `.git/worktrees`; rerunning the same full suite with repository-write permission passed 1724/1724. No timeout or budget was changed.
- The exact-head push diagnostic at `6d552502e3f079565add4fb4fead06cebb19dfb4` failed only `phase21_scene_report_controls`: CTest's Windows command path used different separators from the expected path. That caused Rule 1 fix `66ee663b`.
- A later push diagnostic at `e2fbe20c7763b48314d63c804d52661cc6eb1357` passed native Linux, macOS, sanitizer, CMake-floor, and fixture-reproduction jobs but failed Windows `phase21_scene_report_controls` because nested CTest execution omitted the `Debug` configuration used for discovery. Rule 1 fix `fdd3454a` aligns the two commands; its focused controls and full local suite pass. The final exact-head hosted run remains required.

## Threat and Review Status

- Independent code review at `893ecac8` is clean with zero open findings; see `21-07-REVIEW.md`. Executor follow-up review through `fdd3454a` found no external input, endpoint, or trust-boundary changes.
- Security review closed T-21-15 and T-21-SC. T-21-16 closes only with exact-head hosted and installed-consumer evidence attached to PR #140. T-21-17 is the shared verify-work/closure step.
- The new checker consumes existing CLIs and the Python standard library; it adds no network endpoint or third-party dependency.

## Next Phase Readiness

Plan 21-07 implementation and local qualification are complete. Read hosted native/platform, acceptance, and installed-consumer status from PR #140 and accept evidence only when each check reports the current final head SHA; then the shared `/gsd-verify-work 21` closure completes Phase 21. Phase 22 remains **not started**. After Phase 21 is verified and closed, the owner-selected next phase command is `/gsd-discuss-phase 22` for **Phase 22 — Composition and Microtest Evidence**. Automatic advance remains disabled.

---
*Phase: GB-21-cgb-game-progress-and-scene-regressions*
*Plan: 07*
*Completed: 2026-11-02*

## Self-Check: PASSED

The summary, evidence checker, CMake registration, and source-bound receipt exist. The persisted ledger measures 30 plan commits from `9f7bda3787d69f726a7ef2e63fa4b2c65be7ad63` through `fdd3454a0ee6c2aa37dcd56666e1699c59cb55bf`. That implementation source configured and built, all 1,724 CTests passed in 1,220.71 seconds, the source-bound receipt passes at the same source, and the updated summary/lesson plus Phase 21 focused selection passed 16/16. Exact-head hosted/platform and installed-consumer status is reported by PR #140 at its current head SHA.
