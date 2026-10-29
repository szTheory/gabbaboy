# Phase 18: host-process contract tests for gabbaboy-runner host mode (HOST-01..03).
#
# Every name registered here must also be listed in tests/expected-tests.txt (append-only). Host mode is
# POSIX-only in v0.3 (D-05), so POSIX-only names are registered inside if(NOT WIN32) and removed from the
# Windows expectation in BOTH cmake/ExpectedTests.cmake and .github/scripts/verify-test-inventory.sh.
# Generated ROMs and save directories live under ${PROJECT_BINARY_DIR}/host-mode; nothing binary is committed.
# New tests keep the base 60 s timeout (D-27).

set(GBB_HOST_MODE_HARNESS "${PROJECT_SOURCE_DIR}/tests/scripts/test_host_mode.py")

# gbb_add_host_mode_test(name scenario): one python3 -I scenario against the real runner process.
function(gbb_add_host_mode_test name scenario)
  add_test(NAME ${name}
    COMMAND "${Python3_EXECUTABLE}" -I "${GBB_HOST_MODE_HARNESS}"
      --runner $<TARGET_FILE:gabbaboy-runner>
      --work "${PROJECT_BINARY_DIR}/host-mode/${name}"
      --scenario ${scenario})
  set_tests_properties(${name} PROPERTIES
    PASS_REGULAR_EXPRESSION "host-mode scenario=${scenario} pass")
endfunction()

if(NOT WIN32)
  gbb_add_host_mode_test(host_continuation continuation)
endif()
