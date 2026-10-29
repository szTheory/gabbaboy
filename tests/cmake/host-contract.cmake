# Phase 18: installed host-mode smoke, host-contract documentation contracts and the interop-claim guard
# (HOST-01..03, PLAY-01; D-16, D-19, D-28, D-29).
#
# Every name registered here must also be listed in tests/expected-tests.txt (append-only). Host mode is
# POSIX-only in v0.3 (D-05), so installed_host_smoke is removed from the Windows expectation in BOTH
# cmake/ExpectedTests.cmake and .github/scripts/verify-test-inventory.sh, and from the no-install-prefix
# expectation beside installed_runner_smoke. Generated ROMs and save directories live under
# ${PROJECT_BINARY_DIR}/host-contract; nothing binary is committed. New tests keep the base 60 s timeout (D-27).
#
# This fragment is included before tests/CMakeLists.txt resolves GBB_TEST_INSTALL_PREFIX_ABSOLUTE, so it
# resolves its own.

set(GBB_HOST_CONTRACT_WORK "${PROJECT_BINARY_DIR}/host-contract")

# ---- D-28: the installed runner from an unrelated working directory (stdlib harness, POSIX only) -----------
if(GBB_TEST_INSTALL_PREFIX AND EXISTS "${GBB_TEST_INSTALL_PREFIX}" AND NOT WIN32)
  get_filename_component(GBB_HOST_CONTRACT_PREFIX
    "${GBB_TEST_INSTALL_PREFIX}" ABSOLUTE BASE_DIR "${PROJECT_BINARY_DIR}")
  add_test(NAME installed_host_smoke
    COMMAND "${Python3_EXECUTABLE}" -I "${PROJECT_SOURCE_DIR}/tests/scripts/test_installed_host.py"
      --prefix "${GBB_HOST_CONTRACT_PREFIX}"
      --work "${GBB_HOST_CONTRACT_WORK}/installed-host"
      --source-contract "${PROJECT_SOURCE_DIR}/docs/host-contract.json")
  set_tests_properties(installed_host_smoke PROPERTIES
    TIMEOUT 60
    PASS_REGULAR_EXPRESSION "installed-host pass continuation=01,02 preload=42 controls=1")
endif()
