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
