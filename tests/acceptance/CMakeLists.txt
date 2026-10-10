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
add_test(NAME acceptance_libbet
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--acceptance;tests/acceptance/cases.txt;--case;libbet;--receipt"
    -DGBB_EXPECT_CODE=0
    "-DGBB_EXPECT_REGEX=acceptance id=libbet status=pass"
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(acceptance_libbet PROPERTIES TIMEOUT 300 WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

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
