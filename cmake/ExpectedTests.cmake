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
      installed_consumer_phase2_c installed_consumer_phase2_cpp)
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
      host_cli_stem_refusal)
  endif()
  list(SORT expected_tests)
  if(NOT registered_tests STREQUAL expected_tests)
    message(FATAL_ERROR
      "Registered CTest cases differ from tests/expected-tests.txt.\n"
      "Expected: ${expected_tests}\nRegistered: ${registered_tests}")
  endif()
endfunction()
