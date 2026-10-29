# API Coverage — host OS and SDL3 surfaces used by Phase 18

Full coverage by default over the external API surface Phase 18 actually calls. The detector reported `detected:true` because the phase defines and documents an API (the host contract and `gbb_get_input_clock`), but those are GabbaBoy's own interfaces, not an external integration. The external surfaces are the POSIX file and signal calls in `src/host/` and the SDL3 event, window and menu calls in `src/player/`. No network service, third-party web API or credential is involved.

| capability | decision | reason |
|---|---|---|
| POSIX no-follow file I/O (openat, fstatat, renameat, unlinkat) | INTEGRATE | Atomic battery replace and import: `host_writer_fault_*`, `host_writer_eexist`, `host_writer_target_not_regular`, `host_import_*`, control `host_import_mutant_follow` |
| Durability (`fsync` on file and directory, `F_FULLFSYNC` on Apple) | INTEGRATE | One non-retried sync; an EIO fails the flush. Covered by `host_writer_eio_no_retry` and the fault stages. The directory-sync asymmetry on macOS is documented (IN-09) |
| Directory enumeration (`opendir`/`readdir`) for the stale-temp sweep | INTEGRATE | Sweep names are collected before unlinking, at most 64 per pass. Covered by `host_sweep_batches` with the `host_writer_mutant_sweep_single_pass` control |
| Signal disposition (sigaction, sigprocmask, SIGPIPE, inherited SIG_IGN) | INTEGRATE | The handler only sets a `volatile sig_atomic_t` flag. Covered by real-signal tests `host_signal_term/int/inherited_ign`, `host_signal_disposition` and four decoys |
| Monotonic clock for pacing (`clock_gettime(CLOCK_MONOTONIC)`) | INTEGRATE | A clock failure stops the run with exit 1 and `reason=pacing` (IN-06). Covered by `host_exit_pacing_unavailable` with the `host_signal_decoy_pacing_ignored` control |
| Process exit codes | INTEGRATE | The documented table in `docs/host-contract.json` matches `src/host/host_exit.h`. Covered by `host_exit_table_codes` and the contract checkers |
| SDL3 keyboard events, key modifiers and event pump | INTEGRATE | Slot keys and command guards. Covered by `player_slot_keys` through the real SDL event queue, with the `player_slot_mutant_command_guard` control |
| SDL3 window title (slot status line) | INTEGRATE | Covered by `player_slot_status_line` |
| SDL3 macOS main menu (Cocoa key equivalents) | INTEGRATE | No menu item may consume Command-S/L/Z. Covered by `player_slot_menu_shortcuts` and its seeded-conflict control |
| Windows file and signal APIs | OPT-OUT | Host mode is POSIX-only in v0.3 (D-05). Windows is declared exempt and the Windows test expectations exclude the host tests |
| SDL3 audio, gamepad, file dialogs and other subsystems | OPT-OUT | Phase 18 adds nothing to them. Existing player coverage from earlier phases is unchanged |
| Third-party emulator save formats (mGBA/VBA-M/BGB RTC footers, BESS) | OPT-OUT | Not interop claims in v0.3. Parked as RM-021/RM-022 and guarded by the no-interop-claims scan (WR-06) |
