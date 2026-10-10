# Pulled in with include() from tests/CMakeLists.txt (not add_subdirectory):
# cmake/ExpectedTests.cmake reads the tests directory's TESTS property only.
add_executable(test_acceptance_lib ${CMAKE_CURRENT_LIST_DIR}/../test_acceptance_lib.c)
target_link_libraries(test_acceptance_lib PRIVATE gabbaboy_accept)
target_compile_features(test_acceptance_lib PRIVATE c_std_17)
set_target_properties(test_acceptance_lib PROPERTIES C_EXTENSIONS OFF)

set(GBB_ACCEPT_LIBBET_ROM ${PROJECT_SOURCE_DIR}/fixtures/libbet/libbet.gb)
set(GBB_ACCEPT_LIBBET_SCRIPT ${CMAKE_CURRENT_LIST_DIR}/inputs/libbet-tutorial.input)

add_test(NAME acceptance_lib_libbet_replay
  COMMAND test_acceptance_lib acceptance_lib_libbet_replay
          ${GBB_ACCEPT_LIBBET_ROM} ${GBB_ACCEPT_LIBBET_SCRIPT})
set_tests_properties(acceptance_lib_libbet_replay PROPERTIES TIMEOUT 300)

foreach(case acceptance_parse_script_bounds acceptance_parse_script_errors)
  add_test(NAME ${case} COMMAND test_acceptance_lib ${case})
  set_tests_properties(${case} PROPERTIES TIMEOUT 30)
endforeach()

add_test(NAME acceptance_predicate_truth_table COMMAND test_acceptance_lib acceptance_predicate_truth_table)
add_test(NAME acceptance_predicate_anchors
  COMMAND test_acceptance_lib acceptance_predicate_anchors ${GBB_ACCEPT_LIBBET_ROM})
set_tests_properties(acceptance_predicate_truth_table acceptance_predicate_anchors PROPERTIES TIMEOUT 30)

# Runner acceptance case (D-23, D-28): paths in cases.txt resolve against the working directory,
# so every acceptance CTest runs from the repository root.
string(REPEAT "[0-9a-f]" 64 gbb_hex64_re)
add_test(NAME acceptance_libbet
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--acceptance;tests/acceptance/cases.txt;--case;libbet;--receipt"
    -DGBB_EXPECT_CODE=0
    "-DGBB_EXPECT_REGEX=acceptance id=libbet status=pass.*frame_hit=${gbb_hex64_re}.*pcm_sha256=${gbb_hex64_re}"
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(acceptance_libbet PROPERTIES TIMEOUT 300 WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

# --observe prints sorted key<TAB>value lines instead of pass/fail (D-23). CMake regexes have no
# counted repetition, so the 64-digit digest pattern is built by repetition.
add_test(NAME acceptance_libbet_observe
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--acceptance;tests/acceptance/cases.txt;--case;libbet;--observe"
    -DGBB_EXPECT_CODE=0
    "-DGBB_EXPECT_REGEX=acceptance[.]libbet[.]pcm_sha256\t${gbb_hex64_re}"
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(acceptance_libbet_observe PROPERTIES TIMEOUT 300 WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

# A failure directory that is a regular file cannot be probe-written: exit 2 before any guest work.
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/failure-dir-is-a-file "not a directory\n")
add_test(NAME acceptance_failure_dir_unwritable
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--acceptance;tests/acceptance/cases.txt;--case;libbet;--failure-dir;${CMAKE_CURRENT_BINARY_DIR}/failure-dir-is-a-file"
    -DGBB_EXPECT_CODE=2
    "-DGBB_EXPECT_REGEX=reason=failure-dir-unwritable"
    "-DGBB_FORBID_REGEX=status=(pass|fail|unsupported)"
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(acceptance_failure_dir_unwritable PROPERTIES TIMEOUT 30 WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

# Runner-level negative case files (D-28, T-07-34): each is rejected with exact exit 2 and its own
# reason, and the output must carry no pass/fail/unsupported status line, which proves the case was
# rejected before any guest instance existed.
set(GBB_NEGATIVE_DIR ${CMAKE_CURRENT_LIST_DIR}/negative)
# 65537 bytes: one over the 64 KiB case-file cap. Generated so no oversize blob is committed.
string(REPEAT "#" 65537 gbb_oversize_content)
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/oversize-cases.txt "${gbb_oversize_content}")

function(gbb_add_negative name cases_path reason_regex)
  add_test(NAME acceptance_negative_${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--acceptance;${cases_path};--case;libbet"
      -DGBB_EXPECT_CODE=2
      "-DGBB_EXPECT_REGEX=${reason_regex}"
      "-DGBB_FORBID_REGEX=status=(pass|fail|unsupported)"
      -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(acceptance_negative_${name} PROPERTIES TIMEOUT 30 WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})
endfunction()

gbb_add_negative(flipped_digest tests/acceptance/negative/flipped-digest.txt "reason=rom-digest-mismatch")
gbb_add_negative(bad_script tests/acceptance/negative/bad-script.txt "invalid-script: line 3:")
gbb_add_negative(duplicate_id tests/acceptance/negative/duplicate-id.txt "invalid-cases: duplicate-id")
gbb_add_negative(unknown_key tests/acceptance/negative/unknown-key.txt "invalid-cases: unknown-key")
gbb_add_negative(path_traversal tests/acceptance/negative/path-traversal.txt "invalid-cases: bad-path")
gbb_add_negative(altered_input tests/acceptance/negative/altered-input.txt "reason=input-digest-mismatch")
gbb_add_negative(oversize ${CMAKE_CURRENT_BINARY_DIR}/oversize-cases.txt "invalid-cases: file-too-large")

# Case-file parser and path validator boundary matrix (D-21, D-28).
add_executable(test_acceptance_cases ${CMAKE_CURRENT_LIST_DIR}/../test_acceptance_cases.c)
target_link_libraries(test_acceptance_cases PRIVATE gabbaboy_runner_support)
target_compile_features(test_acceptance_cases PRIVATE c_std_17)
set_target_properties(test_acceptance_cases PROPERTIES C_EXTENSIONS OFF)
foreach(case acceptance_parse_cases_bounds acceptance_parse_cases_errors acceptance_parse_paths)
  add_test(NAME ${case} COMMAND test_acceptance_cases ${case})
  set_tests_properties(${case} PROPERTIES TIMEOUT 30)
endforeach()

# Independent stdlib confirmation of the D-24 frame digest, the PPM bytes and the D-16 PCM digest.
add_executable(test_acceptance_digest ${CMAKE_CURRENT_LIST_DIR}/../test_acceptance_digest.c)
target_link_libraries(test_acceptance_digest PRIVATE gabbaboy_accept)
target_compile_features(test_acceptance_digest PRIVATE c_std_17)
set_target_properties(test_acceptance_digest PROPERTIES C_EXTENSIONS OFF)
add_test(NAME acceptance_digest_vectors
  COMMAND ${Python3_EXECUTABLE} -I ${PROJECT_SOURCE_DIR}/tests/scripts/rgb-digest-vector.py
          --check $<TARGET_FILE:test_acceptance_digest>
          --ppm ${CMAKE_CURRENT_BINARY_DIR}/digest-vector.ppm)
set_tests_properties(acceptance_digest_vectors PROPERTIES TIMEOUT 30)

# Model applicability and declared-exclusion suite semantics (D-22). Exclusions exit 4 with their own
# reason; the CTest skip-return-code mechanism is never used, so an excluded case can never read as a skip.
function(gbb_add_acceptance_exit name code regex timeout)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;${ARGN}"
      -DGBB_EXPECT_CODE=${code}
      "-DGBB_EXPECT_REGEX=${regex}"
      -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT ${timeout} WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})
endfunction()

set(GBB_CASES tests/acceptance/cases.txt)
set(GBB_SUITE_EXCLUSION tests/acceptance/negative/suite-exclusion.txt)
gbb_add_acceptance_exit(acceptance_libbet_excluded_cgb-cpu-e 4
  "status=excluded reason=unsupported-model" 30
  "--acceptance;${GBB_CASES};--case;libbet;--model;cgb-cpu-e")
gbb_add_acceptance_exit(acceptance_libbet-cgb-only_excluded_dmg-cpu-b 4
  "status=excluded reason=unsupported-model" 30
  "--acceptance;${GBB_SUITE_EXCLUSION};--case;libbet-cgb-only")
gbb_add_acceptance_exit(acceptance_suite 0
  "suite eligible=1 executed=1 excluded=0 xfail=0 status=pass" 300
  "--acceptance;${GBB_CASES};--suite;--expect-excluded;0;--receipt")
gbb_add_acceptance_exit(acceptance_suite_declared_exclusion 0
  "suite eligible=1 executed=1 excluded=1 xfail=0 status=pass" 300
  "--acceptance;${GBB_SUITE_EXCLUSION};--suite;--expect-excluded;1")
gbb_add_acceptance_exit(acceptance_suite_undeclared_exclusion 1
  "reason=excluded-count-mismatch expected=0 observed=1" 300
  "--acceptance;${GBB_SUITE_EXCLUSION};--suite;--expect-excluded;0")
gbb_add_acceptance_exit(acceptance_suite_missing_expect_excluded 2
  "reason=expect-excluded-required" 30
  "--acceptance;${GBB_CASES};--suite")
set(GBB_APPLICABILITY tests/acceptance/negative/applicability.txt)
gbb_add_acceptance_exit(acceptance_target_revision_excluded 4
  "status=excluded reason=target-revision" 30
  "--acceptance;${GBB_APPLICABILITY};--case;libbet-rev-x")
gbb_add_acceptance_exit(acceptance_unexpected_pass 1
  "status=unexpected-pass" 300
  "--acceptance;${GBB_APPLICABILITY};--case;libbet-unexpected-pass")
gbb_add_acceptance_exit(acceptance_unknown_model 2
  "reason=unknown-model" 30
  "--acceptance;${GBB_CASES};--case;libbet;--model;z80")
gbb_add_acceptance_exit(acceptance_observe_only_flag 2
  "reason=observe-only-flag" 30
  "--acceptance;${GBB_CASES};--case;libbet;--pcm-digest")
gbb_add_acceptance_exit(acceptance_suite_invalid_expect_excluded 2
  "reason=invalid-expect-excluded" 30
  "--acceptance;${GBB_CASES};--suite;--expect-excluded;x1")

# LD B,B frame capture controls (EVID-01, D-24, D-26). ldbb-controls.txt may only carry the stdlib
# uniform-3 digest as a reference, so a digest captured from this emulator cannot be committed there
# as an oracle. The check runs at configure time and fails the configure, not a test.
execute_process(
  COMMAND ${Python3_EXECUTABLE} -I ${PROJECT_SOURCE_DIR}/tests/scripts/rgb-digest-vector.py --uniform 3
  OUTPUT_VARIABLE gbb_uniform3_digest RESULT_VARIABLE gbb_uniform3_rc OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT gbb_uniform3_rc EQUAL 0 OR NOT gbb_uniform3_digest MATCHES "^[0-9a-f]+$")
  message(FATAL_ERROR "rgb-digest-vector.py --uniform 3 failed (rc=${gbb_uniform3_rc})")
endif()
set(GBB_LDBB_CONTROLS tests/acceptance/ldbb-controls.txt)
set(GBB_LDBB_CONTROLS_FILE ${PROJECT_SOURCE_DIR}/${GBB_LDBB_CONTROLS})
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${GBB_LDBB_CONTROLS_FILE})
file(STRINGS ${GBB_LDBB_CONTROLS_FILE} gbb_ldbb_lines REGEX "reference_digest=")
set(gbb_ldbb_refs 0)
foreach(gbb_line IN LISTS gbb_ldbb_lines)
  if(gbb_line MATCHES "^#")
    continue()
  endif()
  string(REGEX MATCH "reference_digest=([^ ]*)" gbb_unused "${gbb_line}")
  if(NOT "${CMAKE_MATCH_1}" STREQUAL "${gbb_uniform3_digest}")
    message(FATAL_ERROR "${GBB_LDBB_CONTROLS_FILE}: reference_digest ${CMAKE_MATCH_1} is not the stdlib "
      "rgb-digest-vector.py --uniform 3 digest ${gbb_uniform3_digest} (D-26: no self-captured references)")
  endif()
  math(EXPR gbb_ldbb_refs "${gbb_ldbb_refs} + 1")
endforeach()
if(gbb_ldbb_refs EQUAL 0)
  message(FATAL_ERROR "${GBB_LDBB_CONTROLS_FILE}: no reference_digest found")
endif()

gbb_add_acceptance_exit(acceptance_ldbb_observe_daa 0
  "acceptance[.]daa-ldbb[.]checkpoint[.]ldbb[.]frame\t${gbb_hex64_re}\nacceptance[.]daa-ldbb[.]class\tregression" 30
  "--acceptance;${GBB_LDBB_CONTROLS};--case;daa-ldbb;--observe")
