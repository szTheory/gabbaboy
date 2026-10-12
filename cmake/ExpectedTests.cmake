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
      cgb_bench_ab_missing_field cgb_mooneye_repro_requires_manifest)
  endif()
  list(SORT expected_tests)
  if(NOT registered_tests STREQUAL expected_tests)
    message(FATAL_ERROR
      "Registered CTest cases differ from tests/expected-tests.txt.\n"
      "Expected: ${expected_tests}\nRegistered: ${registered_tests}")
  endif()
endfunction()
