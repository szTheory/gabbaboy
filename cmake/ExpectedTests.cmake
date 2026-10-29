file(STRINGS "${PROJECT_SOURCE_DIR}/tests/expected-tests.txt"
  GABBABOY_EXPECTED_TESTS)
if(NOT GABBABOY_EXPECTED_TESTS)
  message(FATAL_ERROR "The required CTest inventory must not be empty")
endif()

function(gabbaboy_verify_registered_tests)
  get_property(registered_tests DIRECTORY PROPERTY TESTS)
  list(SORT registered_tests)
  set(expected_tests "${GABBABOY_EXPECTED_TESTS}")
  if(NOT GBB_TEST_INSTALL_PREFIX OR NOT EXISTS "${GBB_TEST_INSTALL_PREFIX}")
    list(REMOVE_ITEM expected_tests
      installed_runner_smoke installed_consumer_c installed_consumer_cpp
      installed_consumer_phase2_c installed_consumer_phase2_cpp installed_host_smoke)
  endif()
  if(WIN32)
    # The A/B benchmark harness is a bash script (Plan 10-17).
    list(REMOVE_ITEM expected_tests cgb_bench_ab_selftest cgb_bench_ab_wrong_digest
      cgb_bench_ab_missing_field cgb_bench_ab_missing_elapsed cgb_mooneye_repro_requires_manifest
      cgb_colour_repro_tool_failure cgb_colour_repro_missing_pin
      cgb_speed_repro_tool_failure cgb_speed_repro_missing_pin
      age_repro_selfcheck age_repro_selfcheck_tampered age_repro_compare_tampered
      core_linkage_links core_linkage_controls
      release_lifecycle_replay release_lifecycle_controls
      perf_advisory_pipeline perf_advisory_controls
      host_continuation host_rom_max_size host_rom_oversize host_rom_unreadable
      host_cli_stem_refusal host_api_surface host_api_surface_controls
      host_periodic_flush
      host_first_write
      host_idempotent_rerun
      host_sweep_after_checks
      host_writer_fault_temp
      host_writer_fault_write
      host_writer_fault_sync
      host_writer_fault_close
      host_writer_fault_target
      host_writer_fault_rename
      host_writer_fault_dirsync
      host_writer_eio_no_retry
      host_writer_eexist
      host_writer_target_not_regular
      host_sweep_exact_prefix
      host_rtc_final_compare
      host_savedir_missing
      host_savedir_not_directory
      host_savedir_symlink_path
      host_import_exact
      host_import_zero
      host_import_short
      host_import_long
      host_import_mgba_footer
      host_import_oversize
      host_import_bad_rtc
      host_import_symlink
      host_import_dangling_symlink
      host_import_fifo
      host_import_directory
      host_import_stray_nobattery
      host_import_device
      host_rom_fifo
      host_rom_directory
      host_savedir_mutant_mkdir
      host_import_mutant_follow
      host_continuation_mutant_ignore_import
      host_no_test_seams_shipped
      host_no_test_seams_shipped_control
      slot_roundtrip
      slot_empty
      slot_wrong_rom_untouched
      slot_refusal_dmg_in_cgb
      slot_refusal_version_token
      slot_refusal_text_file
      slot_refusal_flipped_byte
      slot_refusal_truncated
      slot_refusal_oversize
      slot_refusal_symlink
      slot_undo_write_failure
      slot_backup_write_failure
      slot_undo_swap
      slot_no_undo
      slot_battery_guard
      slot_unsafe_queued_input
      slot_save_failure_keeps_old
      slot_mutant_undo_before_load
      slot_mutant_preload_before_validate
      slot_mutant_no_guard
      slot_mutant_no_rollback
      slot_fault_rollback_refused
      slot_mutant_rollback_ignored
      slot_fault_clock_unreadable
      slot_mutant_clock_ignored
      slot_reanchor_later
      slot_reanchor_earlier
      slot_select_message
      slot_mutant_plan_ignores_last
      host_signal_term
      host_signal_int
      host_signal_inherited_ign
      host_exit_frames_clean
      host_exit_failure_readonly
      host_exit_core_stop
      host_exit_refusal
      host_exit_crash_storm
      host_signal_disposition
      host_exit_table_codes
      host_run_stop_before_first_frame
      host_signal_decoy_no_flush
      host_signal_decoy_partial_frame
      host_signal_decoy_exit0_after_failed_flush
      host_signal_decoy_in_place_write
      host_no_test_seams_shipped_run_control
      save_format_files
      save_format_controls
      installed_host_smoke)
  endif()
  list(SORT expected_tests)
  if(NOT registered_tests STREQUAL expected_tests)
    message(FATAL_ERROR
      "Registered CTest cases differ from tests/expected-tests.txt.\n"
      "Expected: ${expected_tests}\nRegistered: ${registered_tests}")
  endif()
endfunction()
