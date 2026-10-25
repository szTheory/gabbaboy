---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 18
subsystem: release-evidence
tags: [evidence-head, ci, pr-ready, durable-memory, handoff]
requires:
  - phase: 09-17
    provides: evidence ledger, contract docs and capability text
provides:
  - "Green exact-head evidence head 04c7759 with all eight required checks and six fixture-repro jobs"
  - "Hosted byte-identical rebuild claim for MagenTests and rtc3test, recorded in the ledger and both SOURCES.md files"
  - "PR #65 ready (not merged) with requirement-to-evidence table and the D-14 and D-15/D-17 owner-veto notes"
  - "Decisions D-063..D-068, lessons GB-CART-008..010, deferred items and the Phase 9 research-index bullet"
  - "STATE.md and .continue-here.md handoff naming /gsd-verify-work 9"
affects: [phase-9-verification]
key-files:
  modified:
    - .planning/context/DECISIONS.md
    - .planning/context/LESSONS.md
    - .planning/context/FUTURE-MILESTONES.md
    - .planning/research/INDEX.md
    - .gitattributes
    - docs/mbc3-rtc-evidence.md
    - fixtures/magentests/SOURCES.md
    - fixtures/rtc3test/SOURCES.md
    - .planning/STATE.md
    - .planning/.continue-here.md
key-decisions:
  - "The byte-identical rebuild claim for MagenTests and rtc3test is made only from the hosted result line (run 38189871131 at fb8972d, repeated at the evidence head)"
  - "The evidence head is the head that carries the claim text (04c7759), so the claim and its proof are read from one green head"
requirements-completed: [CART-04, CART-05, CART-06, RTC-01, RTC-02, RTC-03]
coverage:
  - id: D1
    description: Bounded current local Phase 9 behavior probes
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R '^(rtc_block_roundtrip|rtc_catch_up_.*|rtc_import_never_advances|rtc_block_corruption_matrix|rtc_block_reset_roundtrip|rtc_block_generation|rtc_battery_size_types|catch_up_policy_table|mbc3_rtc_continuation_fixture_digest|continuation_guest_.*|rtc3test_(fixture_digest|basic|range|subsecond|negative_control))$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R '^(loader_(contradiction_mbc[235]|mbc30_variant|type_byte_sweep|bad_checksum)|rtc_mutant_.*)$'"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase3-player/gabbaboy --output-on-failure --no-tests=error -R '^(player_session_v2_.*|player_session_v1_(corpus_load|mbc1_write_identical)|player_session_classification_drift|player_session_rom_cap_8mib|player_continuation_mbc3_.*|player_continuation_mbc2_resume|player_continuation_mbc5_resume|player_session_clock_flag_scope)$'"
        status: pass
      - kind: e2e
        ref: "build/14-refresh-consumers/consumer-c/consumer-c fixtures/tracer/tracer.gb"
        status: pass
      - kind: e2e
        ref: "build/14-refresh-consumers/consumer-cpp/consumer-cpp fixtures/tracer/tracer.gb"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -R '^native_guide_rtc_contract$'"
        status: pass
status: complete
commits: 4
plan_head_before: 6e5303ff0204c17554e3bd884f704f5800c403d0
plan_head_after: 0ca424f89810408101f15d11dd4b0e3601a3882b
actuals:
  tokens: 20000
  tasks: 2
  commits: 4
duration: about 3 h (mostly CI waits)
completed: 2026-10-12
---

# Phase 9 Plan 18: Gates, evidence head, PR ready and handoff Summary

Phase 9 execution closes with a green exact-head evidence head, a ready and still open PR #65 carrying the requirement-to-evidence table and the owner-veto notes, recorded decisions and lessons, and a persisted route to `/gsd-verify-work 9`.

## Heads and runs

| Head | SHA | Run | Result |
|---|---|---|---|
| Evidence head | `04c77596c375a8b186da54c2f7b253c3ef2fcdab` | `ci` https://github.com/szTheory/gabbaboy/actions/runs/38191589574 (pull_request, attempt 1) | all eight required jobs success |
| Evidence head | same | `fixture-repro` https://github.com/szTheory/gabbaboy/actions/runs/38191589599 | six jobs success |
| Evidence head | same | `preview-package-smoke` https://github.com/szTheory/gabbaboy/actions/runs/38191589573 | success on attempt 2 (see deviation 2) |
| Handoff head | `0ca424f89810408101f15d11dd4b0e3601a3882b` | `ci` https://github.com/szTheory/gabbaboy/actions/runs/38193351709 (attempt 1) | all eight required jobs success |
| Handoff head | same | `fixture-repro` https://github.com/szTheory/gabbaboy/actions/runs/38193351705 | success |
| Handoff head | same | `preview-package-smoke` https://github.com/szTheory/gabbaboy/actions/runs/38193351728 | success on attempt 2 |

`wait-exact-head-ci.py` with all eight `--require` options printed `PASS` for both heads. `git diff --name-only 04c7759..0ca424f` lists exactly `.planning/.continue-here.md` and `.planning/STATE.md`.

Evidence-head required checks read from run 38191589574: native-linux-x64 success, native-macos-arm64 success, native-windows-x64 success, linux-asan-ubsan success, cmake-floor-3.25.3 success, player-gate success, macos-player-package success, required-native success. Fixture-repro jobs read from run 38191589599: fixture-repro, mooneye-original-repro, mooneye-candidate-repro, mooneye-mbc-repro, magentests-repro and rtc3test-repro success; `magentests-repro` and `rtc3test-repro` each printed `result=byte-identical`.

`no_host_clock` (with its two self-tests) passed on native-linux-x64, native-macos-arm64, native-windows-x64, linux-asan-ubsan and cmake-floor-3.25.3. `baseline status=pass` printed on the three native jobs.

## Accomplishments

- **Phase-wide gates** (against the current `origin/main`; the local `main` ref was stale): no `-` line in `tests/expected-tests.txt`; the only `-` line in `tests/player/expected-tests.txt` is `player_session_battery_unsupported`; `tests/baseline` unchanged; `correctness_digest_fnv1a64=4c7a57ff3d50d228`; `baseline status=pass`; the four `FUZZ_` literals unchanged. Local CTest 401/401 and `verify-test-inventory.sh ... --installed` verified 401; `verify-phase3-player.sh --build-package` passed.
- **Privacy:** across the 117 files changed since `origin/main` (PLAN files excluded) there is no home path and no non-noreply email; no `.sym`, `.lnk` or `.log` fixture is tracked. (Against the stale local `main` the only email hits were the verbatim upstream licence line in `fixtures/mooneye-mbc/LICENSE.txt` and one quotation of it in the Phase 8 summary; both are already on `origin/main`.)
- **Durable memory:** D-063..D-068 (signed catch-up, unified battery image and 21-byte block, envelope v1/v2 split and `-cart-` name, reopen policy, D-26 placement, no-host-clock proof); GB-CART-008..010; the Phase 9 deferred list (BGB/VBA-M footer adapter, Mealybug `mbc3_rtc` after G1, gbclock after G3, CGB double-speed RTC in Phase 11, paused-time recovery, `gbb_probe_rom` `has_rtc`); a Phase 9 bullet in the research index (links verified).
- **PR #65:** body replaced with the requirement-to-evidence table, run URLs, limits, the D-14 and D-15/D-17 owner-veto notes, the D-26 placement deviation and the attribution line; marked ready; state OPEN, not merged. Triage: no open issues; the only open PR is #65.
- **Handoff:** STATE.md and `.continue-here.md` name the completed stage, the evidence head and run, `/gsd-verify-work 9` as the single next command and Phase 10 as the following (not started) phase. `workflow.auto_advance` and `workflow._auto_chain_active` are false.

## Deviations from Plan

**1. [Rule 1 - Bug] Windows CRLF broke the digested rtc3test text.** At the first push (`c81e8e0`) `native-windows-x64` failed `rtc3test_fixture_digest`, `rtc3test_basic`, `rtc3test_range`, `rtc3test_subsecond` and `rtc3test_negative_control`: the checkout converted `tests.md` and the `.input` scripts to CRLF, changing their digests. `.gitattributes` now pins the rtc3test fixture text and `tests/rtc3test/**` to LF and the ROM to `-text` (commit `fb8972d`, fix cycle 1 of 3). No test was weakened.

**2. [Rule 3 - Blocking] `preview-package-smoke` deadline.** At both heads the workflow's own 1500 s exact-head wait expired before the Windows leg finished (`exact-head-ci: FAIL deadline reached`), so the job failed with no product defect. I re-ran the failed jobs (attempt 2) and both succeeded. The workflow is not one of the eight required checks; the timeout is worth raising before the next release.

**3. [Rule 3 - Ordering] The evidence head carries the claim text.** The first green head (`fb8972d`, run 38189871149, fixture-repro run 38189871131) showed `result=byte-identical`; the ledger and both `SOURCES.md` files were then updated (`04c7759`) and the evidence head was re-read there, so the claim and its proof come from one green head.

**4. [Format] Wait command options.** The plan's wait command omits the mandatory `--require` options; all eight were supplied.

**5. Local `main` was stale.** The plan's `git diff main...HEAD` gates were run against `origin/main` (which includes the squash-merged Phase 8); against the stale local ref the player-inventory gate printed no `-` line.

**6. `advance-plan` not run.** `state.advance-plan` declines while the plan has no SUMMARY, and the plan forbids rewriting STATE.md after the handoff head, so STATE.md position text was set by hand; `record-metric` was run.

## Known Stubs

None.

## Threat Flags

None. T-09-36 is mitigated by reading only exact-head results (the stale local `main` and the deadline failures were not counted as green), T-09-37 by the privacy scan and a PR-body scan, T-09-38 by not merging and not touching branch protection.

## Fresh Focused Evidence (15.1-12)

- Reused existing build outputs. Current focused selections passed: core RTC/continuation/rtc3test 27/27 (54.71 seconds), loader/RTC mutants 16/16 (1.17 seconds), player persistence/continuation 22/22 (1.43 seconds), and native-guide contract 1/1. Existing C and C++ consumer binaries both exited successfully against `fixtures/tracer/tracer.gb`.
- Three pinned RGBDS 1.0.1 continuation fixture reproductions each printed `result=byte-identical`; their digests are recorded in the fresh evidence for Plan 15.1-12's Phase 9 summaries 10–14. The archive SHA-256 was verified before use.
- The hosted exact-head CI, fixture-reproduction runs, preview package job, PR #65 state, full 401-case suite, and live source-bound support-ledger self-test were not revalidated. They remain historical producer claims. The point-in-time boundary at commit `0ca424f89810408101f15d11dd4b0e3601a3882b` recorded `/gsd-verify-work 9` as the next command in its STATE and continuation note; this statement does not assert a current route or ancestry. Current CI/PR state is unknown.

## Self-Check: PASSED

Commits `c81e8e0`, `fb8972d`, `04c7759` and `0ca424f` are ancestors of HEAD; the PR head equals `0ca424f` at the time of writing; PR #65 is OPEN and not a draft; the stash count is still 1.
