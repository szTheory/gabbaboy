---
phase: GB-18-player-save-slots-and-host-contract
verified: 2026-10-29T08:00:00Z
status: human_needed
score: 4/4 must-haves verified
covered_files:
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-01-PLAN.md"
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-01-SUMMARY.md"
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-02-PLAN.md"
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-02-SUMMARY.md"
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-03-PLAN.md"
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-03-SUMMARY.md"
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-04-PLAN.md"
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-04-SUMMARY.md"
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-05-PLAN.md"
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-05-SUMMARY.md"
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-06-PLAN.md"
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-06-SUMMARY.md"
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-07-PLAN.md"
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-07-SUMMARY.md"
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-08-PLAN.md"
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-08-SUMMARY.md"
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-09-PLAN.md"
  - ".planning/phases/GB-18-player-save-slots-and-host-contract/18-09-SUMMARY.md"
  - "CMakeLists.txt"
  - "README.md"
  - "cmake/CheckCoreNoHostClock.cmake"
  - "cmake/CheckHostApiSymbols.cmake"
  - "cmake/CheckRunnerSourcesQualified.cmake"
  - "cmake/VerifyDocContract.cmake"
  - "docs/cartridge-and-saves.md"
  - "docs/host-contract.json"
  - "docs/native-integration.md"
  - "include/gabbaboy/gabbaboy.h"
  - "src/core/gabbaboy.c"
  - "src/host/gbb_host.h"
  - "src/host/host_basename.c"
  - "src/host/host_cadence.c"
  - "src/host/host_exit.h"
  - "src/host/host_run.c"
  - "src/host/host_save_format.c"
  - "src/host/host_save_io.c"
  - "src/host/host_signal.c"
  - "src/player/input.c"
  - "src/player/input.h"
  - "src/player/limitations.h"
  - "src/player/main.c"
  - "src/player/slots.c"
  - "src/player/slots.h"
  - "src/runner/main.c"
  - "tests/cmake/host-contract.cmake"
  - "tests/cmake/host.cmake"
  - "tests/cmake/input-clock.cmake"
  - "tests/cmake/save-formats.cmake"
  - "tests/cmake/slots.cmake"
  - "tests/player/test_menu_shortcuts.c"
  - "tests/player/test_slots.c"
  - "tests/scripts/host_fixture.py"
  - "tests/scripts/test_host_mode.py"
  - "tests/scripts/test_host_signals.py"
  - "tests/scripts/test_installed_host.py"
  - "tests/scripts/verify-host-contract.py"
  - "tests/scripts/verify-no-interop-claims.py"
  - "tests/scripts/verify-save-formats.py"
  - "tests/test_host_basename.c"
  - "tests/test_host_cadence.c"
  - "tests/test_host_run.c"
  - "tests/test_host_save_io.c"
  - "tests/test_input_clock.c"
  - "tests/test_save_format_completeness.c"
  - "tests/test_slots.c"
  - "tests/test_slots_pure.c"
covered_digest: "v4:sha256:23ca698d2c98e7e46b75aae735c5eb1a50eb70d855ac9bd1bc22e76ec3af96e5"
behavior_unverified: 0
overrides_applied: 0
coincidental_reliance_items:
  - truth: "SC-3: a real SIGTERM exits 0 well within 2 s (non-sanitizer lanes)"
    reason: fixture-only
    harden: "The 2 s bound is a wall-clock ceiling measured on whatever machine runs the test (review IN-07); the structural evidence is the boundary-frame replay equality. Keep the replay as the load-bearing check and treat the ceiling as a smoke bound."
human_verification:
  - test: "Owner triage of the 15 open review dispositions in 18-REVIEW-DISPOSITION.md, in particular WR-03 (battery-preload backup overwritten by the first slot load of every later session) and WR-01 (ignored rollback and input-clock results in player_slot_load)"
    expected: "Each finding is marked fixed, skipped or deferred with a reason. Project rule D-102..D-105 says an unresolved correctness finding forces a rescope or the single reserved gap slot 18-10, never a seed. WR-03 is a reachable data-loss path in a documented-but-undesirable edge; WR-01 is not reachable through the public core today."
    why_human: "A disposition is an owner decision. No machine can decide whether a recoverability gap in the battery preload backup is acceptable for v0.3.0."
  - test: "Confirm the PR CI lanes that cannot run locally are green on the exact head: Linux ASan, native Windows (MSVC build of every target plus the Windows exclusion lists), and the hosted macOS player package. Also read hosted per-test times against the 45 s (75% of 60 s) budget."
    expected: "All required checks pass on the exact head revision, with no skipped or stale runs."
    why_human: "These lanes only exist on hosted runners. The verifier ran the full local suite on macOS and cannot observe them. AGENTS.md forbids treating a local pass as proof a remote revision is green."
---

# Phase 18: Player Save Slots and Host Contract Verification Report

**Phase Goal:** Players can save and load numbered state slots in the SDL player without risking the running game, and a host process can drive the runner with a predictable save directory, atomic battery saves, a clean SIGTERM save-and-exit and documented exit codes and save formats.
**Verified:** 2026-10-29
**Status:** human_needed
**Re-verification:** No, initial verification
**Head verified:** 1f749b01fe8ed59c12f0f311657911b1678e60fa (source identical to d3b0f0dd; the two later commits only add the code review records)

## Goal Achievement

The goal is achieved in the codebase. Every roadmap success criterion is backed by code I read and by tests I re-ran, each with a negative control. The status is `human_needed` rather than `passed` for two reasons only. One is an owner decision on open review findings. The other is CI evidence that exists only on hosted runners. Nothing is FAILED.

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Player tests save and load numbered slots through the public API only; a refused, mismatched or wrong-ROM slot leaves the running game byte-identical and shows a clear message | VERIFIED | `src/player/slots.c` `player_slot_load` reads, then validates the bytes in a scratch instance built from the store's own ROM copy (step 1a, `gbb_create`/`gbb_load_rom`/`gbb_load_state`/`gbb_get_input_clock`), and only then snapshots, writes the preload, does the live load and writes the undo file. Every refusal path returns before any write. `tests/test_slots.c` `snap_take`/`snap_equal` compare full state bytes, battery bytes, battery generation and the digests of slot, undo, preload and `.gbb` files. Cases `refusal_dmg_in_cgb`, `wrong_rom_untouched`, `refusal_version_token`, `refusal_text_file`, `refusal_flipped_byte`, `refusal_truncated`, `refusal_oversize` and `refusal_symlink` exercise the refusal classes. The mutants `slot_mutant_undo_before_load` and `slot_mutant_preload_before_validate` fail them. `host_api_surface` (passed) proves `slots.c` uses only declared public `gbb_*` symbols. Player wiring in `src/player/main.c` `handle_slot_key` routes every outcome through `player_slot_format_message` and `set_slot_status` to the title, and a load re-anchors input via `player_input_rebase`. Re-ran `verify-phase3-player.sh --build-package` at HEAD: 106/106 including `player_slot_keys`, `_reanchor`, `_status_line`, `_help_text`, `_mutant_no_rebase`, `_mutant_command_guard`, `_menu_shortcuts` and its control. |
| 2 | Runner `--rom --save-dir` writes raw `{saveDir}/{romBaseName}.sav` through an O_EXCL temp and rename with periodic flushing; separate negatives reject unsanitised basename, symlinked target and wrong import size with no partial mutation | VERIFIED | `src/host/host_save_io.c` `host_save_io_replace`: temp `openat(... O_WRONLY\|O_CREAT\|O_EXCL\|O_NOFOLLOW\|O_CLOEXEC, 0600)` in the save dir, write, one non-retried `fsync` (`F_FULLFSYNC` on Apple), checked `close`, `fstatat(AT_SYMLINK_NOFOLLOW)` that refuses a non-regular target, `renameat`, dir `fsync`; every pre-rename failure unlinks the temp. Reads use `O_NOFOLLOW` plus `S_ISREG` and never size an allocation from `st_size`. `host_cadence.c` and `host_run.c` implement the 16-quiet / 300-age / 3,600-frame cadence. Tests re-run and passing: `host_stem_refuse_*` (7 rows), `host_stem_mutant_transform`, `host_import_exact/zero/short/long/mgba_footer/oversize/bad_rtc/symlink/dangling_symlink/fifo/directory/device`, `host_import_mutant_follow`, `host_writer_fault_*` (7 stages), `host_writer_eio_no_retry`, `host_writer_eexist`, `host_writer_target_not_regular`, `host_periodic_flush`, `host_continuation` and its `ignore_import` mutant, `host_savedir_*`. |
| 3 | A real-signal POSIX test sends SIGTERM and observes finish-frame, flush and exit 0 well within 2 s; a check rejects signal code in the core; every row of the exit-code table is exercised; Windows declared exempt | VERIFIED | `src/host/host_signal.c`: handler body is only `g_host_stop = sig` on a file-static `volatile sig_atomic_t`, `SA_RESTART\|SA_RESETHAND`, TERM/INT/HUP unblocked, SIGPIPE ignored, an inherited `SIG_IGN` is honoured for INT/HUP. `host_run.c` polls the flag at the frame boundary (lines 429-459), then runs the final flush and prints the exit line. `test_host_signals.py` sends real signals to a paced runner; `host_signal_term`, `_int`, `_inherited_ign`, `host_exit_frames_clean`, `_failure_readonly`, `_core_stop`, `_refusal`, `_crash_storm`, `host_signal_disposition`, `host_exit_table_codes` and `host_run_stop_before_first_frame` all passed in my run. The four decoys (`no_flush`, `partial_frame`, `exit0_after_failed_flush`, `in_place_write`) are rejected. `no_host_clock`, `no_host_clock_signal_selftest` and `no_host_clock_signal_call_selftest` pass: the core is checked at source and object layers for signal calls and the seeded controls fail. Windows exemption is declared in the plan, the contract docs and the exclusion lists. |
| 4 | A machine-readable table declares the save-format id and byte size for each cartridge kind (MBC3+RTC 32,789 B) and a CTest checks it against runner-produced files, failing on a seeded size or id mismatch | VERIFIED | `docs/host-contract.json` parsed: 16 `save_formats` rows; `0x10/0x03` is `gabbaboy-mbc3-rtc-sram-32k-v1` at 32,789 B (32,768 + 21); exit codes 0 clean, 1 failure, 2 refusal, none/crash. `save_format_print`, `save_format_print_none`, `save_format_files` (produces files for every row on dmg and cgb), `save_format_completeness`, `save_format_freeze`, `host_contract_json`, `save_format_controls` (all seeded REJECT controls) and `host_contract_controls` passed. The table is installed under `share/gabbaboy/` (`CMakeLists.txt:172`) and compared byte-for-byte by `installed_host_smoke`. |

**Score:** 4/4 roadmap truths verified; 0 behavior-unverified. The plan-level truths (D-01..D-31 across nine plans) were exercised through the same suites, each with a seeded mutant or control.

### Requirements Coverage

Cross-referenced PLAN `requirements:` frontmatter against `.planning/REQUIREMENTS.md`. All four IDs are claimed by at least one plan; no orphans (REQUIREMENTS.md maps only PLAY-01, HOST-01, HOST-02 and HOST-03 to Phase 18).

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| PLAY-01 | 18-03, 18-05, 18-06, 18-09 | SDL player saves and loads numbered state slots through the public API only | SATISFIED | Truth 1; `gbb_get_input_clock` (18-03) tests `input_clock_*` pass; the player suite is 106/106 |
| HOST-01 | 18-01, 18-02, 18-04, 18-09 | `--rom/--save-dir` writes raw `{saveDir}/{romBaseName}.sav` | SATISFIED | Truth 2 |
| HOST-02 | 18-07, 18-09 | SIGTERM finishes the frame, flushes, exits 0 well within 2 s | SATISFIED | Truth 3 |
| HOST-03 | 18-08, 18-09 | Own save-format ids and sizes in a machine-readable table, CTest-checked against produced files | SATISFIED | Truth 4 |

### Required Artifacts and Wiring

| Artifact | Status | Details |
|----------|--------|---------|
| `src/host/{gbb_host.h,host_run.c,host_save_io.c,host_basename.c,host_cadence.c,host_signal.c,host_exit.h,host_save_format.c}` | VERIFIED | Substantive (2,000+ lines), linked into `gabbaboy-runner` via the `gabbaboy_host` library, public-API-only (`host_api_surface`) |
| `src/player/slots.c`, `slots.h` | VERIFIED | Wired into `src/player/main.c` (`slots_attach`, `handle_slot_key`, `apply_slot_load`) and decoded before the bare R and S branches |
| `src/player/input.c` `player_input_rebase` | VERIFIED | Called from `apply_slot_load`; mutant `player_slot_mutant_no_rebase` fails the suite |
| `include/gabbaboy/gabbaboy.h` `gbb_get_input_clock` | VERIFIED | Only core/API change; state pins unchanged (`state_format_contract` passes); installed C and C++ consumers reference it |
| `docs/host-contract.json` | VERIFIED | Canonical, installed, checked against the C table, the runner and the docs |
| `docs/native-integration.md` "Host process contract" | VERIFIED | Present at line 277; `host_contract_docs` and its drift and missing controls pass |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
|----------|------|--------|-----------|--------|
| Player slot message | `message` | `player_slot_format_message(&result)` from the real `player_slot_load` outcome | Yes | FLOWING |
| `.sav` bytes | exported battery | `gbb_copy_battery` of the live instance, compared with `last_persisted` | Yes | FLOWING |
| `--print-save-format` id and size | `host_save_format.c` rows | Checked against the JSON by `save_format_print` and against produced files by `save_format_files` | Yes | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Host, slot, save-format, input-clock, no-host-clock, doc and summary-coverage suites | `ctest --preset phase1 -R "^(host_\|slot_\|save_format\|installed_host\|input_clock\|no_host_clock\|doc_no_interop\|native_guide_host\|cartridge_guide_slots\|readme_host\|summary_coverage\|state_format_contract\|state_portable)" -j6` | 162/162 passed in 10.9 s | PASS |
| Full suite at final source head | `build/18-gate-ctest-d3b0f0dd.log` (orchestrator-run) | "100% tests passed out of 1650", 0 Failed lines | PASS (not re-run) |
| macOS player suite at HEAD | `bash tests/scripts/verify-phase3-player.sh --build-package` | exit 0, 106/106, extracted-package smoke passed | PASS |
| Phase 18 test time budget | slowest Phase 18 tests in the gate log | `save_format_controls` 9.66 s, `host_exit_crash_storm` 8.67 s, all others under 3 s (well under 45 s) | PASS |

### Probe Execution

No `probe-*.sh` scripts are declared or present for this phase. Step 7c does not apply.

### Anti-Patterns Found

None. No `TBD`, `FIXME`, `XXX`, `TODO` or `HACK` markers in the Phase 18 source, scripts or tests. `git status` shows only the owner's uncommitted `.planning/config.json`, which I did not touch.

### Code Review Assessment (18-REVIEW.md: 0 critical, 6 warnings, 9 info, all disposition `open`)

I read the cited code for the two findings the orchestrator asked about.

- **WR-01 (ignored rollback and clock results)** is confirmed at `src/player/slots.c:239` and `:250`. It does not undermine the must-have. The refusal path that SC-1 names (refused, mismatched or wrong-ROM slot) returns at step 1 or 1a, before any live change, so the byte-identical guarantee holds. The ignored calls are on later paths. `gbb_load_state` of a snapshot taken from the same instance moments earlier fails only on allocation failure, and `gbb_get_input_clock` cannot fail with a non-NULL instance and a `struct_size` of 24, both of which the code guarantees. This is real but latent hardening. The gap is that "nothing changed" is asserted without checking the rollback result.
- **WR-03 (preload backup overwritten at the first load of each session)** is confirmed by reading `battery_differs_from_guard`: `guard_valid` is false at every `player_slot_store_init`, so the first load of any new session rewrites the preload file with the then-current battery. The behaviour matches the D-23 text ("or this is the session's first load"), and the help text promises only that loading "replaces the game's battery save". It does not touch the running game, so SC-1 and the goal clause "without risking the running game" hold. It does mean the one backup of the player's original in-game save can be destroyed by a later session. No test spans two store initialisations. This is a design-level recoverability gap in a safety feature, so it is the finding most worth an explicit owner decision.
- **WR-02, WR-04, WR-05, WR-06 and the IN items** are robustness or test-infrastructure weaknesses. WR-04 is worth knowing about: the save-format and contract checkers resolve HEAD at configure time. The configure for the gate ran at d3b0f0dd and `docs/host-contract.json` has not changed since, so the evidence above is not stale. WR-05 (replacing a `.sav` resets its mode to 0600) is undocumented in `docs/native-integration.md` (no mention of 0600 or permissions) and affects a supervisor running under a different uid.

None of the fifteen findings makes a roadmap truth FAILED. The disposition file still reads `open` for all fifteen, so the triage that D-102..D-105 requires has not happened.

### Human Verification Required

#### 1. Review-finding disposition (owner decision)

**Test:** Mark each of the 15 findings in `18-REVIEW-DISPOSITION.md` as fixed, skipped or deferred. Decide specifically whether WR-03 and WR-01 are fixed in the reserved gap slot 18-10 or accepted for v0.3.0 and recorded as a limitation.
**Expected:** No `open` row remains before Phase 19 starts. An accepted WR-03 is written into the player limitation text or the slot docs, since a hidden loss of the preload backup is a claim gap.
**Why human:** A disposition is an owner decision. Whether a recoverability gap in the preload backup is acceptable is not machine-decidable.

#### 2. Hosted CI on the exact head

**Test:** Confirm the Linux ASan lane, the native Windows lane (MSVC compile of every target and the Windows exclusion lists) and the hosted macOS player-package lane are green on the exact PR head, and read hosted per-test times against the 45 s budget.
**Expected:** Every required check passes on the exact head with no skipped or stale runs.
**Why human:** Those lanes only exist on hosted runners. A local macOS pass is not proof for another platform or revision.

### Gaps Summary

There are no gaps in the delivered behaviour. All four success criteria and all four requirement IDs are backed by implementation I read and tests I re-ran at the final source head. The negative controls, mutants and decoys are wired into CTest and reject their seeded defects. The phase cannot be called `passed` until the owner records dispositions for the open review findings (WR-03 first) and the hosted exact-head CI lanes are observed green. Neither is a missing deliverable.

---

_Verified: 2026-10-29_
_Verifier: Claude (gsd-verifier)_
