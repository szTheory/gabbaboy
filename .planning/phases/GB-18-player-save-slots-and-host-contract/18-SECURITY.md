---
phase: "18"
slug: "player-save-slots-and-host-contract"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-29"
---

# Phase 18 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

`gsd-security-auditor` audited the plan-time threat register (plans 18-01..18-09: T-18-01..32 and T-18-SC) at head `b7a44637`. Its source is identical to code head `70a29b29`, which includes review-fix rounds 1 and 2. The auditor checked every mitigation against the current code, not the plan-time code, and re-ran the matching tests without rebuilding:
- `build`: the host, slot, save-format, contract, interop, installed-host, no-host-clock and input-clock selection passed 176/176, and the native-guide, doc-contract and core-linkage selection passed 13/13.
- `build-player`: the slot and input-rebase selection passed 10/10.

Each named CTest is in `tests/expected-tests.txt` or `tests/player/expected-tests.txt`. Every mitigation that has a mutant or decoy control rejects the seeded defect.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Supervisor → runner argv | `--rom`, `--save-dir`, `--frames`, `--profile` from an untrusted host process | Paths, basename stem, counts |
| Save directory → runner | An existing `.sav`, stale temps and hostile entries (symlink, FIFO, device, directory) | Raw battery bytes, RTC block |
| Runner → save directory | Atomic battery publish and the stale-temp sweep | Temp file, rename, directory sync |
| Signals → runner | TERM, INT, HUP and SIGPIPE from the supervisor or terminal | Signal number only (a `sig_atomic_t` flag) |
| Slot files → player | Slot, undo, preload and battery-guard files in the per-user prefs directory | Serialized state bytes |
| Keyboard → player | Slot chords through the SDL and Cocoa event path | Key and modifier events |
| Repository → installed package | `docs/host-contract.json` and the guides shipped with the prefix | Exit codes, save-format table |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-18-01 | Tampering | host_stem (path traversal via --rom) | high | mitigate | Last-component stem refusing empty, leading dot, control, DEL, `\`, bad UTF-8 and >200 B, copied unmodified (`host_basename.c:39-63`); `/` refused at replace (`host_save_io.c:193`). `host_stem_refuse_*`, `host_stem_mutant_transform`, `host_cli_stem_refusal` | closed |
| T-18-02 | Tampering | host_save_io_read_exact | high | mitigate | dirfd + `O_NOFOLLOW`/`O_NONBLOCK`, `S_ISREG`, exact size before read, read <= want+1, dev/inode re-check (`host_save_io.c:58-93`); refusal exits 2 before frame 1. `host_import_*` | closed |
| T-18-03 | Denial of service | bounded ROM reader / save cap | medium | mitigate | `O_NONBLOCK`, regular-file check and 8 MiB cap before allocation (`host_run.c:134-145`, `:383-388`). `host_rom_max_size`, `host_rom_oversize`, `host_rom_fifo`, `host_rom_directory`, `host_import_oversize` | closed |
| T-18-04 | Elevation of privilege | gabbaboy_host using core seams | medium | mitigate | Public-symbol and dirty-list checks. `host_api_surface(_controls)`, `host_qualified_sources(_control)` | closed |
| T-18-05 | Information disclosure | gbb-host diagnostics | low | mitigate | Tokens only, never paths (`host_run.c:189-191`, `:339-346`); harness `forbid_work_path` | closed |
| T-18-06 | Tampering | gbb_get_input_clock out-pointer | medium | mitigate | `struct_size` checked before any write, static-asserted size (`gabbaboy.c:475`, `:5462-5473`). `input_clock_handshake`, `input_clock_mutant_short_size_writes(_control)` | closed |
| T-18-07 | Information disclosure | public header | low | mitigate | Three fields only (`gabbaboy.h:398-403`); `doc-contract-undeclared`. `native_guide_*`, `doc_contract_undeclared_selftest` | closed |
| T-18-08 | Tampering | import via symlink / TOCTOU swap | high | mitigate | One dirfd, `O_NOFOLLOW`, dev/inode re-check. `host_import_symlink`, `host_import_dangling_symlink`, `host_import_mutant_follow`, `host_savedir_symlink_path` | closed |
| T-18-09 | Denial of service | FIFO, device or oversized .sav | high | mitigate | `O_NONBLOCK`, `S_ISREG`, exact size; no-battery carts never open a `.sav` (`host_run.c:379-382`). `host_import_fifo/directory/device/oversize/stray_nobattery`, `host_rom_fifo/directory` | closed |
| T-18-10 | Tampering | torn .sav on write failure | high | mitigate | `O_EXCL`/`O_NOFOLLOW` temp, write loop, one non-retried sync, checked close, target check, `renameat`, temp unlink on failure, dir sync (`host_save_io.c:157-263`). `host_writer_fault_*` (7 stages), `host_writer_eio_no_retry`, `host_writer_target_not_regular` | closed |
| T-18-11 | Tampering | stale-temp sweep | medium | mitigate | Exact `.<stem>.sav.tmp-` prefix, no-follow unlink, names collected first, bounded passes, runs after all refusals (`host_save_io.c:284-309`, `host_run.c:414-416`). `host_sweep_exact_prefix`, `host_sweep_after_checks`, `host_sweep_batches`, `host_writer_mutant_sweep_single_pass` | closed |
| T-18-12 | Repudiation | missed flush | medium | mitigate | 16/300/3,600 cadence with retry (`host_cadence.c:27-63`, `host_run.c:452-466`). `host_cadence_*`, two cadence mutants, `host_periodic_flush` | closed |
| T-18-13 | Elevation of privilege | fault seams in shipped binary | medium | mitigate | Seams only under `GBB_HOST_TESTING`, a never-installed target; shipped archive/runner symbol scan. `host_no_test_seams_shipped(_control)` | closed |
| T-18-14 | Tampering | crafted slot file | high | mitigate | Bounded no-follow regular read, scratch-instance validation before any write (`slots.c:240-267`). `slot_refusal_*` (7), `slot_wrong_rom_untouched` | closed |
| T-18-15 | Denial of service | oversized slot file | medium | mitigate | Allocation and read capped at `state_size + 1`, never from `st_size`. `slot_refusal_oversize` | closed |
| T-18-16 | Tampering | loss of in-game battery save on load | high | mitigate | Validate → preload backup → live load → undo, with rollback and `RESTORE_FAILED`; guard kept across sessions (`slots.c:170-307`). `slot_battery_guard(_sessions)`, `slot_guard_write_failure`, four slot mutants, `slot_fault_rollback_refused` | closed |
| T-18-17 | Tampering | slot file-name injection | medium | mitigate | Names from hex digest, `dmg`/`cgb` and slot 1..9 only (`slots.c:49-126`). `slot_select_message`, `slot_key_decoder` | closed |
| T-18-18 | Denial of service | far-future or full restored input queue | low | mitigate | Refuse > 140,448×64 half-dots ahead or > 56 events before any write (`slots.c:38-43`, `:263-266`). `slot_unsafe_queued_input`, `slot_reanchor_plan` | closed |
| T-18-19 | Tampering | Command chords overwriting battery / resetting | medium | mitigate | Slot keys decoded first; bare R/S require no Command (`main.c:1556-1593`). `player_slot_keys`, `player_slot_mutant_command_guard` | closed |
| T-18-20 | Denial of service | stuck input after load | medium | mitigate | Cursor set directly, releases pending, pause on unsafe rebase (`input.c:73-105`, `main.c:1465`). `player_slot_reanchor`, `player_slot_mutant_no_rebase`, `slot_reanchor_*`, `player_input_rebase_guard`, `player_input_mutant_rebase_silent` | closed |
| T-18-21 | Repudiation | silent slot failure | low | mitigate | Status message plus stderr line with `gbb_error` for every save, load and undo (`main.c:1506-1510`, `slots.c:479-502`). `player_slot_status_line`, `slot_message_table` | closed |
| T-18-22 | Tampering | non-async-signal-safe handler | high | mitigate | Handler only stores a `volatile sig_atomic_t` (`host_signal.c:22-35`); polled at frame boundaries. `host_signal_term/int/disposition` | closed |
| T-18-23 | Tampering | torn .sav on SIGKILL | high | mitigate | Same atomic publish as T-18-10. `host_exit_crash_storm`, `host_signal_decoy_in_place_write` | closed |
| T-18-24 | Repudiation | exit 0 hiding failed final flush | high | mitigate | Failed final flush returns exit 1 (`host_run.c:486-508`). `host_exit_failure_readonly`, `host_signal_decoy_exit0_after_failed_flush` | closed |
| T-18-25 | Elevation of privilege | crash/test hook in shipped runner | medium | mitigate | Hook only under `GBB_HOST_TESTING`; `host_run_test_` symbol scan. `host_no_test_seams_shipped(_run_control)` | closed |
| T-18-26 | Tampering | signal code in the core | medium | mitigate | Source and symbol deny lists (`CheckCoreNoHostClock.cmake:43`, `:54`) with seeded strict-C17 controls. `no_host_clock`, `no_host_clock_signal(_call)_selftest` | closed |
| T-18-27 | Tampering | save-format id/size drift after release | high | mitigate | Id grammar and append-only freeze against the latest `v*` tag (`verify-save-formats.py`). `save_format_freeze/files/completeness/controls`, `contract_rev_wiring(+controls)` | closed |
| T-18-28 | Spoofing | false interop claim | medium | mitigate | Exact-size gate refuses the 32,816 B mGBA footer file. `host_import_mgba_footer`, `doc_no_interop_claims` | closed |
| T-18-29 | Denial of service | hostile ROM via --print-save-format | low | mitigate | Same capped regular-file ROM reader; no directory opened (`host_run.c:208-241`). `save_format_print(_none)`, `host_grammar_print_extra` | closed |
| T-18-30 | Tampering | installed contract differs from source | medium | mitigate | Byte comparison plus seeded drift control (`test_installed_host.py:83-103`). `installed_host_smoke` | closed |
| T-18-31 | Spoofing | docs over-claiming interop or durability | medium | mitigate | Hardened interop scan (WR-06) plus phrase contracts. `doc_no_interop_claims`, `host_contract_docs(_control, _missing_control)`, `host_contract_json` | closed |
| T-18-32 | Information disclosure | personal paths in docs or receipts | low | mitigate | No `/Users/` or `/home/` path in README or docs at HEAD; diagnostics print tokens only | closed |
| T-18-SC | Tampering | npm/pip/cargo installs | high | accept | No package installed; stdlib Python and CMake only (AR-18-01) | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

### Surface added after planning (review fixes)

The review fixes added surface that no SUMMARY flag lists. Each piece reuses the hardened primitives above, so none is counted toward `threats_open`:
- **WR-02, slot-store temp sweep:** removes no-follow `.tmp-` names inside the digest-prefixed namespace, at most 32 per attach (`slots.c:80-104`). Its match is broader than T-18-11's exact host prefix but stays inside the store's own name space.
- **WR-03, battery guard file:** read through `host_save_io_read_exact` and written through the atomic writer.
- **WR-05, mode preservation:** `fchmod` carries an existing regular target's mode over to the temp file (`host_save_io.c:203-219`).
- **Player ROM re-read:** `slots_attach` re-reads the ROM no-follow, regular-file only, capped at 8 MiB + 1, and checks its digest (`main.c:1424-1428`).

Advisory, non-blocking:
- **T-18-17:** no test calls the save and load entry points directly with slot 0 or 10. Both go through the tested `build_name` check.
- **T-18-21:** slot selection, and a slot key pressed while slots are unavailable, set a status message without a per-event `gbb_error` line. Neither is a save, load or undo, and the unavailable state is logged once at attach.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-18-01 | T-18-SC | Phase 18 installs no npm, pip or cargo package. Comparing `f4082a65` with HEAD shows no package manifest, CI workflow, FetchContent, ExternalProject or new `find_package` change, and every added Python import is from the standard library. The risk is accepted at plan time in all nine plans and re-checked at audit. | plan-time disposition (18-01..18-09), re-verified by gsd-security-auditor | 2026-10-29 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-29 | 33 | 33 | 0 | gsd-security-auditor (ASVS L1, block_on high) at `b7a44637` |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-29
