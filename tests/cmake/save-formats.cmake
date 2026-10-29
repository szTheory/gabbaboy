# Phase 18: the published save-format table (HOST-03, D-16, D-19, D-20).
#
# docs/host-contract.json is the machine-readable host contract. The checkers read it and the C sources with
# `git show <rev>:<path>` at the configure-time HEAD, so commit before running them: an uncommitted edit, or a
# configure from before the commit, checks the previous revision. Generated ROMs and save directories live under
# ${PROJECT_BINARY_DIR}/save-formats; nothing binary is committed. Every name registered here must also be listed
# in tests/expected-tests.txt (append-only). The produced-file leg and the shim controls spawn POSIX processes, so
# those names are POSIX-only and are removed from the Windows expectation in BOTH cmake/ExpectedTests.cmake and
# .github/scripts/verify-test-inventory.sh (GB-CGB-007). New tests keep the base 60 s timeout.
#
# This fragment is included before tests/CMakeLists.txt resolves GBB_STATE_SOURCE_REV, so it resolves its own.

execute_process(
  COMMAND git rev-parse HEAD
  WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
  RESULT_VARIABLE GBB_SAVE_FORMATS_REV_RESULT
  OUTPUT_VARIABLE GBB_SAVE_FORMATS_REV
  ERROR_QUIET
  OUTPUT_STRIP_TRAILING_WHITESPACE)
string(LENGTH "${GBB_SAVE_FORMATS_REV}" GBB_SAVE_FORMATS_REV_LENGTH)
if(NOT GBB_SAVE_FORMATS_REV_RESULT EQUAL 0 OR NOT GBB_SAVE_FORMATS_REV_LENGTH EQUAL 40 OR
   NOT GBB_SAVE_FORMATS_REV MATCHES "^[0-9a-f]+$")
  set(GBB_SAVE_FORMATS_REV "unknown")
  message(STATUS "Save-format CTests remain registered with an unresolved revision and will fail closed")
endif()

set(GBB_SAVE_FORMATS_CHECKER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-save-formats.py")
set(GBB_SAVE_FORMATS_WORK "${PROJECT_BINARY_DIR}/save-formats")

# ---- D-02: --print-save-format on the committed fixtures (portable: nothing is created) ------------------
add_test(NAME save_format_print
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--print-save-format;--rom;${PROJECT_SOURCE_DIR}/fixtures/mbc1-continuation/continuation.gb"
    -DGBB_EXPECT_CODE=0
    "-DGBB_EXPECT_REGEX=save_format=gabbaboy-mbc1-sram-8k-v1 bytes=8192"
    "-DGBB_FORBID_REGEX=gbb-host: ready"
    -DGBB_EXPECT_MIN_KEY=bytes -DGBB_EXPECT_MIN_VALUE=8192
    -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
set_tests_properties(save_format_print PROPERTIES TIMEOUT 60)

# A cartridge without a battery prints the sentinel `none`, which is not a save-format id (assumption A5).
add_test(NAME save_format_print_none
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--print-save-format;--rom;${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb"
    -DGBB_EXPECT_CODE=0
    "-DGBB_EXPECT_REGEX=save_format=none bytes=0"
    "-DGBB_FORBID_REGEX=gbb-host: ready"
    -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
set_tests_properties(save_format_print_none PROPERTIES TIMEOUT 60)

# --print-save-format takes no --save-dir or --frames. The grammar is parsed before the Windows gate.
gbb_add_host_grammar_test(host_grammar_print_extra "--print-save-format;--rom;r;--save-dir;d"
  "invalid-arguments: reason=print-save-format-extra")
set_tests_properties(host_grammar_print_extra PROPERTIES TIMEOUT 60)

# ---- D-20: the runner's produced files against the JSON, on both profiles (POSIX-only) --------------------
if(NOT WIN32)
  add_test(NAME save_format_files
    COMMAND "${Python3_EXECUTABLE}" -I "${GBB_SAVE_FORMATS_CHECKER}"
      --check --rev "${GBB_SAVE_FORMATS_REV}" --repo "${PROJECT_SOURCE_DIR}"
      --runner $<TARGET_FILE:gabbaboy-runner> --work "${GBB_SAVE_FORMATS_WORK}")
  set_tests_properties(save_format_files PROPERTIES
    TIMEOUT 60
    PASS_REGULAR_EXPRESSION "save-formats pass rows=16 ids=12 profiles=2 files=32")
endif()

# ---- D-20: completeness in both directions, in process (portable) ---------------------------------------
# test_save_format_completeness enumerates type x RAM code x ROM code through gbb_probe_rom and gbb_battery_size;
# the checker spawns it and holds docs/host-contract.json to its output.
add_executable(test_save_format_completeness "${PROJECT_SOURCE_DIR}/tests/test_save_format_completeness.c")
target_link_libraries(test_save_format_completeness PRIVATE GabbaBoy::core)
target_compile_features(test_save_format_completeness PRIVATE c_std_17)
set_target_properties(test_save_format_completeness PROPERTIES C_EXTENSIONS OFF)
add_test(NAME save_format_completeness
  COMMAND "${Python3_EXECUTABLE}" -I "${GBB_SAVE_FORMATS_CHECKER}"
    --check-completeness --rev "${GBB_SAVE_FORMATS_REV}" --repo "${PROJECT_SOURCE_DIR}"
    --enumerator $<TARGET_FILE:test_save_format_completeness>)
set_tests_properties(save_format_completeness PROPERTIES
  TIMEOUT 60
  PASS_REGULAR_EXPRESSION "save-formats completeness pass rows=16")

# ---- D-19: ids are a published host contract, so the table is append-only against the latest release tag ----
# Needs tags fetched (CI native jobs use fetch-depth 0). No strict tag at all fails; a tag without the file passes
# with baseline=none; once a release carries the file, every row of it must survive unchanged.
add_test(NAME save_format_freeze
  COMMAND "${Python3_EXECUTABLE}" -I "${GBB_SAVE_FORMATS_CHECKER}"
    --freeze --rev "${GBB_SAVE_FORMATS_REV}" --repo "${PROJECT_SOURCE_DIR}")
set_tests_properties(save_format_freeze PROPERTIES
  TIMEOUT 60
  PASS_REGULAR_EXPRESSION "save-formats freeze pass baseline=(none|v[0-9]+\\.[0-9]+\\.[0-9]+)")

# ---- D-16: canonical JSON, the exit-code X-macro and the cadence constants (portable) --------------------
set(GBB_HOST_CONTRACT_CHECKER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-host-contract.py")
add_test(NAME host_contract_json
  COMMAND "${Python3_EXECUTABLE}" -I "${GBB_HOST_CONTRACT_CHECKER}"
    --check --rev "${GBB_SAVE_FORMATS_REV}" --repo "${PROJECT_SOURCE_DIR}")
set_tests_properties(host_contract_json PROPERTIES
  TIMEOUT 60
  PASS_REGULAR_EXPRESSION "host-contract pass exit_codes=4 cadence=6")
