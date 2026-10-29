---
phase: "18"
slug: "player-save-slots-and-host-contract"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-28"
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source of the check map: `18-RESEARCH.md` § Validation Architecture (success criterion → automated check → negative control).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | CTest + project C test binaries + Python `-I` checkers/harness + CMake `-P` contract checks |
| **Config file** | `tests/CMakeLists.txt`, `tests/player/CMakeLists.txt`, `tests/expected-tests.txt`, `tests/player/expected-tests.txt` |
| **Quick run command** | `cmake --build --preset phase1 && ctest --preset phase1 -R '^(host_|slot_|save_format_|no_host_clock|runner_help)' --output-on-failure` |
| **Full suite command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` |
| **Estimated runtime** | quick ~30 s; full several minutes (ASan lane ×3 timeouts) |

---

## Sampling Rate

- **After every task commit:** quick `-R` run above plus any touched checker `--self-test`
- **After every plan:** the plan's targeted `-R` area run; the player-slot plan (18-06) ends with one `bash tests/scripts/verify-phase3-player.sh --build-package` (macOS)
- **Phase tail (once, D-105):** full `phase1` suite in 18-09 Task 3
- **Before `/gsd-verify-work`:** full suite green at the exact PR head on all required CI contexts, plus `phase1-asan`, inventory self-test and `tests/scripts/verify-uat-closure.py --self-test`
- **Max feedback latency:** ~60 s for the quick run

Timing note (research finding 2): runner end-to-end tests must not wait out the 3,600-frame RTC cadence; cadence is a pure function covered by synthetic unit tests, and runner tests use one write-driven flush plus the final flush.

---

## Per-Task Verification Map

Filled by the planner from PLAN.md `<automated>` commands; every success criterion row in RESEARCH § "Success Criterion -> Automated Check Map" (1a–1g, 2a–2h, 3a–3f, 4a–4d, X1–X3) must map to at least one task with a negative control.

Shorthand: `B` = `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '<regex>' --output-on-failure --no-tests=error`; `INV` = `bash .github/scripts/verify-test-inventory.sh --self-test`; `PLAYER` = `bash tests/scripts/verify-phase3-player.sh --build-package` (macOS; once per 18-06 as its tail gate); `P` = targeted `cmake --build build/phase3-player/gabbaboy --parallel && ctest --test-dir build/phase3-player/gabbaboy -R '<regex>' --output-on-failure --no-tests=error` after one `PLAYER` build. Exact commands and `<fails_when>` signals are in each PLAN task.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 18-01-T1 | 01 | 1 | HOST-01 | T-18-02, T-18-05 | exact-size O_NOFOLLOW import; atomic publish; no paths in diagnostics | e2e | B `^(host_continuation\|runner_help\|instance_lifecycle)$` + INV | ❌ W0 (created by task) | ⬜ pending |
| 18-01-T2 | 01 | 1 | HOST-01 | T-18-03, T-18-05 | 8 MiB ROM bound at both edges, own token, no allocation above it | e2e | B `^(host_rom_(max_size\|oversize\|unreadable)\|host_continuation)$` + INV | ❌ W0 | ⬜ pending |
| 18-02-T1 | 02 | 2 | HOST-01 | T-18-01 | stem validated never rewritten (one token per input); grammar refusals exit 2 before fs; Windows gate | unit + CLI | B `^(host_stem_.*\|host_grammar_.*\|host_cli_stem_refusal\|host_windows_refusal\|runner_help)$` + INV | ❌ W0 | ⬜ pending |
| 18-02-T2 | 02 | 2 | HOST-01 | T-18-04 | public-API-only host code; dirty-list coverage | other (CMake -P) | B `^(host_api_surface\|host_api_surface_controls\|host_qualified_sources\|host_qualified_sources_control\|no_host_clock\|core_linkage_links)$` + INV | ❌ W0 | ⬜ pending |
| 18-03-T1 | 03 | 3 | PLAY-01 | T-18-06 | struct_size handshake; outputs unchanged on error | unit | B `^input_clock_(handshake\|queue\|after_load)$` | ❌ W0 | ⬜ pending |
| 18-03-T2 | 03 | 3 | PLAY-01 | T-18-06, T-18-07 | mutants killed; consumers use ABI; state bytes unchanged | unit + integration | B `^(input_clock_.*\|state_(format_contract\|portable_pins\|inventory\|globals\|identity\|codec_matrix\|tracer)\|native_guide_.*\|doc_contract_.*\|model_gates.*\|core_linkage_links)$`; installed-consumer command | ❌ W0 | ⬜ pending |
| 18-04-T1 | 04 | 4 | HOST-01 | T-18-11, T-18-12 | mid-run flush; identical image not rewritten; sweep exact prefix after checks | e2e | B `^(host_periodic_flush\|host_first_write\|host_idempotent_rerun\|host_sweep_after_checks\|host_continuation)$` + INV | ❌ W0 | ⬜ pending |
| 18-04-T2 | 04 | 4 | HOST-01 | T-18-10, T-18-12 | per-stage writer faults keep old file; cadence boundaries | unit | B `^(host_cadence_.*\|host_rtc_final_compare\|host_writer_.*\|host_sweep_exact_prefix)$` + INV | ❌ W0 | ⬜ pending |
| 18-04-T3 | 04 | 4 | HOST-01 | T-18-03, T-18-08, T-18-09, T-18-13 | hostile dir/import refused with own token, no mutation; stray no-battery .sav ignored; FIFO/directory --rom refused `rom-not-regular` within 10 s; import-ignoring continuation mutant killed; no shipped seams | e2e + other | B `^(host_savedir_.*\|host_import_.*\|host_no_test_seams_shipped.*\|host_api_surface.*\|host_rom_(fifo\|directory)\|host_continuation_mutant_ignore_import)$` + INV; all 23 names POSIX-only and in both Windows lists (W-1 loop in 18-04 Task 3 acceptance prints nothing) | ❌ W0 | ⬜ pending |
| 18-05-T1 | 05 | 5 | PLAY-01 | T-18-17 | slot names not user-controlled; public-API round trip | integration | B `^(slot_roundtrip\|slot_empty\|host_api_surface)$` + INV | ❌ W0 | ⬜ pending |
| 18-05-T2 | 05 | 5 | PLAY-01 | T-18-14, T-18-15, T-18-16, T-18-18 | scratch validation before any write; refusal touches nothing; preload before live load; rollback; battery guard; 56-event capacity | integration | B `^(slot_(wrong_rom_untouched\|refusal_.*\|undo_.*\|backup_write_failure\|no_undo\|battery_guard\|unsafe_queued_input\|save_failure_keeps_old\|mutant_(undo_before_load\|preload_before_validate\|no_guard\|no_rollback))\|host_api_surface)$` + INV | ❌ W0 | ⬜ pending |
| 18-05-T3 | 05 | 5 | PLAY-01 | T-18-18 | exact messages; key decode; unsafe input refused; post-load A press visible in guest SRAM within one frame (joypad-mirror ROM) | unit + integration | B `^slot_` + INV | ❌ W0 | ⬜ pending |
| 18-06-T1 | 06 | 6 | PLAY-01 | T-18-19 | ⌘S/⌘R guards; slot keys via real event pump | automated_ui | P `^player_slot_keys$` | ❌ W0 | ⬜ pending |
| 18-06-T2 | 06 | 6 | PLAY-01 | T-18-20, T-18-21 | input rebase after load; real key reaches the guest within one frame; status + stderr line | automated_ui | P `^player_slot_(keys\|reanchor\|status_line\|mutant_no_rebase\|mutant_command_guard)$` | ❌ W0 | ⬜ pending |
| 18-06-T3 | 06 | 6 | PLAY-01 | — | help/limitations honest; A2 menu check + control (mandatory) | automated_ui + other | P `^(player_slot_(help_text\|menu_shortcuts\|menu_shortcuts_control)\|player_limitations)$`; B `^(cgb_speed_docs_no_stale_claims.*\|phase8_player_contract.*\|cgb_corpus_claims.*\|cgb_hdma_claims_contract.*)$`; plan tail gate PLAYER once | ❌ W0 | ⬜ pending |
| 18-07-T1 | 07 | 6 | HOST-02 | T-18-22 | handler only stores flag; frame-boundary stop; replay; 2 s ceiling | e2e | B `^(host_signal_term\|host_continuation\|host_periodic_flush\|host_api_surface)$` + INV | ❌ W0 | ⬜ pending |
| 18-07-T2 | 07 | 6 | HOST-02 | T-18-23, T-18-24, T-18-25 | every exit row (read-only row on a per-frame-changing RTC image asserts `reason=final result=failed stage=temp`); storm old-or-new; decoys fail; signals unblocked; only codes 0/1/2 | e2e + unit | fast line: B `^(host_signal_(term\|int\|inherited_ign\|disposition)\|host_exit_(frames_clean\|failure_readonly\|core_stop\|refusal\|table_codes)\|host_run_stop_before_first_frame)$` + INV (10 tests); then storm/decoy line: `ctest --test-dir build -R '^(host_exit_crash_storm\|host_signal_decoy_(no_flush\|partial_frame\|exit0_after_failed_flush\|in_place_write))$' --output-on-failure --no-tests=error` (5 tests); each line has its own `<fails_when>` (W-2) | ❌ W0 | ⬜ pending |
| 18-07-T3 | 07 | 6 | HOST-02 | T-18-26 | no signal code in core | other (CMake -P) | B `^no_host_clock.*$` | ✅ script exists (extended) | ⬜ pending |
| 18-08-T1 | 08 | 7 | HOST-03 | T-18-27, T-18-29 | ids/sizes printed and produced on both profiles ($0F checked by GBRT magic, not SRAM byte 0) | e2e | B `^(save_format_(files\|print\|print_none)\|host_grammar_print_extra\|host_windows_refusal\|host_api_surface\|host_qualified_sources)$` + INV | ❌ W0 | ⬜ pending |
| 18-08-T2 | 08 | 7 | HOST-03 | T-18-27 | completeness both ways; freeze; exit/cadence agree | unit + other | B `^(save_format_(completeness\|freeze)\|host_contract_json)$` | ❌ W0 | ⬜ pending |
| 18-08-T3 | 08 | 7 | HOST-03 | T-18-27, T-18-28 | every drift mode rejected with own code | other (checker self-test) | B `^(save_format_.*\|host_contract_.*\|host_grammar_print_extra)$` + INV | ❌ W0 | ⬜ pending |
| 18-09-T1 | 09 | 8 | HOST-01, HOST-03 | T-18-30 | installed contract byte-identical (seeded drift control); relocated continuation | e2e | install + `GBB_TEST_INSTALL_PREFIX` command in 18-09 Task 1 + INV | ❌ W0 | ⬜ pending |
| 18-09-T2 | 09 | 8 | all | T-18-31, T-18-32 | docs match JSON; one phrase-removed control per doc; no interop/power-loss over-claim; D-19 PLAYSTEAD-CONTRACT.md correction scanned by doc_no_interop_claims (`files=6`) with a seeded original-sentence copy as its control (W-3) | other (doc contract) | B `^(native_guide_(host\|rtc)_contract\|cartridge_guide_slots_contract\|readme_host_mode_contract\|unreleased_host_entries\|doc_contract_.*\|host_contract_.*\|doc_no_interop_claims\|cgb_speed_docs_no_stale_claims.*\|no_phase_paths.*)$` | ❌ W0 | ⬜ pending |
| 18-09-T3 | 09 | 8 | all | — | single phase-tail qualification (read-only for all code); release surfaces unchanged; five discretion choices recorded as new D-NNN rows in DECISIONS.md (`git diff -U0 T^ T -- .planning/context/DECISIONS.md > build/phase18-decisions.diff && grep -c '^+\| D-' build/phase18-decisions.diff` = 5 for task commit T) | integration | full suite + INV + `verify-uat-closure.py --self-test` + workflow/VERSION diff (18-09 Task 3) | ✅ | ⬜ pending |

### Success-criterion rows -> tasks

| RESEARCH row | Task(s) | Negative control |
|---|---|---|
| 1a round trip | 18-05-T1 | stale-snapshot is caught by byte compare |
| 1b refusal untouched | 18-05-T2 | `slot_mutant_undo_before_load`, `slot_mutant_preload_before_validate` |
| 1c message table | 18-05-T3 | `slot_mutant_message_map` |
| 1d undo / guard | 18-05-T2 | `slot_mutant_no_rollback`, `slot_mutant_no_guard` |
| 1e re-anchor / unsafe input | 18-03-T1, 18-05-T2, 18-05-T3, 18-06-T2 | `slot_mutant_plan_ignores_last`, `player_slot_mutant_no_rebase`, `input_clock_mutant_last_is_now`, 60-event capacity case; no-press control row (guest SRAM bit 0 stays set) beside the guest-visible press row (D-26 item 7) |
| 1f key decode | 18-05-T3, 18-06-T1 | `player_slot_mutant_command_guard` |
| 1g getter ABI | 18-03-T2 | `input_clock_mutant_short_size_writes`, `input_clock_consumer_symbols_selftest` |
| 2a atomic writer / continuation | 18-01-T1, 18-04-T2, 18-04-T3 | per-stage faults; `host_signal_decoy_in_place_write`; `host_continuation_mutant_ignore_import` (XFER-002 import-ignoring mutant) |
| 2b basename | 18-02-T1 | `host_stem_mutant_transform` |
| 2c hostile target | 18-04-T3 | `host_import_mutant_follow` |
| 2d import sizes / ROM bound | 18-01-T2, 18-04-T3 | each size row has its own token; `host_rom_max_size` vs `host_rom_oversize`; `host_rom_fifo` / `host_rom_directory` forbid `rom-unreadable` and a 10 s bound catches a blocking reader |
| 2e cadence | 18-04-T2 | `host_cadence_mutant_gt`, `host_cadence_mutant_quiet_off_by_one` |
| 2f save dir | 18-04-T3 | `host_savedir_mutant_mkdir` |
| 2g API-only | 18-02-T2, 18-05-T2 | `host_api_surface_controls` |
| 2h dirty list | 18-02-T2 | `host_qualified_sources_control` |
| 3a SIGTERM | 18-07-T1 | `host_signal_decoy_no_flush` |
| 3b replay | 18-07-T1 | `host_signal_decoy_partial_frame` |
| 3c exit rows | 18-07-T2 | `host_signal_decoy_exit0_after_failed_flush` (the read-only row's image changes every frame, so the final flush always attempts a write), in-place decoy, `host_exit_table_codes` |
| 3d inherited SIG_IGN / SIGPIPE / unblock | 18-07-T2 | disposition case asserts SIG_IGN preserved and TERM/INT/HUP unblocked |
| 3e core no-signal | 18-07-T3 | `no_host_clock_signal_selftest`, `no_host_clock_signal_call_selftest` |
| 3f Windows exemption / Windows build | 18-02-T1 + every POSIX-only registration; Windows build rule in 18-01's execution contract (applied in 18-04, 18-05, 18-07) | `INV` self-test; POSIX leg of `host_windows_refusal`; POSIX-only executables and libraries created only inside `if(NOT WIN32)`; local `-D_WIN32 -fsyntax-only` proxy over `src/host/*.c` and `src/player/slots.c`; the exact-head `native-windows-x64` build is the authoritative check |
| 4a JSON / ids / X-macro | 18-08-T1..T3 | `save_format_controls`, `host_contract_controls` |
| 4b completeness | 18-08-T2 | deleted-row / $10/$05 controls |
| 4c produced files | 18-08-T1 | 1-byte-short, cgb-id and $1A shims |
| 4d freeze | 18-08-T2 | freeze-mismatch and no-tags controls |
| X1 installed smoke | 18-09-T1 | preload $41 -> $42 and 01 -> 02 readback; one-byte-changed installed JSON control |
| X2 docs | 18-09-T2 | four `doc_contract_*_missing_selftest`, `host_contract_docs_control`, seeded interop claim (a PLAYSTEAD-CONTRACT.md copy with the original D-19 sentence re-appended) |
| X3 budget | 18-09-T3 | 45 s local flag; hosted check per GB-CI-012 |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `src/host/*`, `gabbaboy_host` target (include dirs only, no core link), `src/player/slots.c` skeleton
- [ ] `tests/test_host_save_io.c`, `tests/test_host_cadence.c`, `tests/test_slots.c`, core input-clock test
- [ ] `tests/scripts/test_host_signals.py`, `tests/scripts/verify-save-formats.py` (+ `--self-test`)
- [ ] `cmake/CheckHostApiSymbols.cmake`, `cmake/CheckRunnerSourcesQualified.cmake`, extended `cmake/CheckCoreNoHostClock.cmake`
- [ ] `docs/host-contract.json` skeleton; inventory and Windows-exemption edits (`ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None (D-069) | — | A2 (⌘S/⌘L/⌘Z under SDL3's default macOS menu) is covered by the mandatory `player_slot_menu_shortcuts` + control in 18-06-T3; if the macOS lane cannot build the Cocoa menu the executor stops and reports to the owner (no fallback, no manual UAT) | — |

*All phase behaviors have automated verification unless a planner-declared perceptual/hardware limitation is recorded.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
