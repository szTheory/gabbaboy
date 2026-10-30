# Phase 18: the published save-format table (HOST-03, D-16, D-19, D-20).
#
# docs/host-contract.json is the machine-readable host contract. The checkers read it and the C sources with
# `git show <rev>:<path>` from the immutable commit resolved during configure. Generated ROMs and save directories live under
# ${PROJECT_BINARY_DIR}/save-formats; nothing binary is committed. Every name registered here must also be listed
# in tests/expected-tests.txt (append-only). The produced-file leg and the shim controls spawn POSIX processes, so
# those names are POSIX-only and are removed from the Windows expectation in BOTH cmake/ExpectedTests.cmake and
# .github/scripts/verify-test-inventory.sh (GB-CGB-007). New tests keep the base 60 s timeout.
#
# This fragment is included before tests/CMakeLists.txt resolves GBB_STATE_SOURCE_REV, so it resolves its own.

# The commit the checkers read. Resolve the requested ref once during configure and pass the full SHA to every
# registered checker. This captures the boundary commit so tests cannot read moving HEAD facts at runtime.
set(GBB_SAVE_FORMATS_REV "HEAD" CACHE STRING
  "Revision ref the save-format and host-contract checkers capture at configure time")
set(GBB_SAVE_FORMATS_REV_REQUESTED "${GBB_SAVE_FORMATS_REV}")
set(GBB_CONTRACT_REVISION_RESOLVER "${PROJECT_SOURCE_DIR}/cmake/ResolveContractRevision.cmake")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${GBB_CONTRACT_REVISION_RESOLVER}")
include("${GBB_CONTRACT_REVISION_RESOLVER}")
gbb_resolve_contract_revision(
  "${PROJECT_SOURCE_DIR}"
  "${GBB_SAVE_FORMATS_REV_REQUESTED}"
  GBB_SAVE_FORMATS_REV_RESOLVED
  GBB_SAVE_FORMATS_REV_STATUS)
if(NOT GBB_SAVE_FORMATS_REV_STATUS STREQUAL "resolved")
  set(GBB_SAVE_FORMATS_REV "unknown")
  message(STATUS
    "Save-format CTests remain registered with an unresolved revision ref (${GBB_SAVE_FORMATS_REV_REQUESTED}) and will fail closed")
else()
  set(GBB_SAVE_FORMATS_REV "${GBB_SAVE_FORMATS_REV_RESOLVED}")
  message(STATUS
    "Save-format and host-contract CTests capture immutable revision ${GBB_SAVE_FORMATS_REV} from ${GBB_SAVE_FORMATS_REV_REQUESTED}")
endif()

set(GBB_SAVE_FORMATS_CHECKER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-save-formats.py")
set(GBB_SAVE_FORMATS_WORK "${PROJECT_BINARY_DIR}/save-formats")

# The pass patterns match any positive row, id, file and exit-code count rather than today's numbers (IN-08): the
# save-format table and the exit table are append-only (D-19), so a legitimate appended row must not fail unrelated
# tests. Each checker derives its counts from the JSON it parsed and rejects an empty or drifted table on its own;
# the fixed cadence key set (6) and the two profiles stay pinned.

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
    PASS_REGULAR_EXPRESSION "save-formats pass rows=[1-9][0-9]* ids=[1-9][0-9]* profiles=2 files=[1-9][0-9]*")
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
  PASS_REGULAR_EXPRESSION "save-formats completeness pass rows=[1-9][0-9]*")

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
  PASS_REGULAR_EXPRESSION "host-contract pass exit_codes=[1-9][0-9]* cadence=6")

# ---- D-20: seeded controls, one REJECT code per way the published table can drift ------------------------
# Each control drives the checker's own CLI over a private git repository (and, for the produced-file legs, over a
# generated runner shim with exactly one seeded defect) and must fail for its own named reason. The shim controls
# spawn POSIX processes, so save_format_controls is POSIX-only; host_contract_controls is portable.
if(NOT WIN32)
  add_test(NAME save_format_controls
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${Python3_EXECUTABLE};-I;${GBB_SAVE_FORMATS_CHECKER};--self-test;--rev;${GBB_SAVE_FORMATS_REV};--repo;${PROJECT_SOURCE_DIR}"
      -DGBB_EXPECT_CODE=0
      "-DGBB_EXPECT_REGEX=save-formats self-test pass controls=[0-9]+"
      -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=15
      -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
  set_tests_properties(save_format_controls PROPERTIES TIMEOUT 60)
endif()

add_test(NAME host_contract_controls
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${Python3_EXECUTABLE};-I;${GBB_HOST_CONTRACT_CHECKER};--self-test;--rev;${GBB_SAVE_FORMATS_REV};--repo;${PROJECT_SOURCE_DIR}"
    -DGBB_EXPECT_CODE=0
    "-DGBB_EXPECT_REGEX=host-contract self-test pass controls=[0-9]+"
    -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=5
    -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
set_tests_properties(host_contract_controls PROPERTIES TIMEOUT 60)
