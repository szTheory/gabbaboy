# Phase 18 (D-24): gbb_get_input_clock, the one public API addition of the phase.
#
# Every name registered here must also be listed in tests/expected-tests.txt (append-only). New tests keep
# the base 60 s timeout (D-27). The test builds its ROM and states at run time; nothing binary is committed.

add_executable(test_input_clock "${PROJECT_SOURCE_DIR}/tests/test_input_clock.c")
target_link_libraries(test_input_clock PRIVATE GabbaBoy::core)
target_compile_features(test_input_clock PRIVATE c_std_17)
set_target_properties(test_input_clock PROPERTIES C_EXTENSIONS OFF)

foreach(case handshake queue after_load)
  add_test(NAME input_clock_${case} COMMAND test_input_clock ${case})
  set_tests_properties(input_clock_${case} PROPERTIES PASS_REGULAR_EXPRESSION "PASS ${case}")
endforeach()

# gbb_input_clock_mutant(name anchor replacement case): the real core with one edit, built as its own
# static library and linked ALONE into a copy of test_input_clock, so no executable ever links two cores
# (verify-core-linkage.py). The anchor must occur exactly once in src/core/gabbaboy.c. The mutant test must
# exit 1 with "FAIL <case>" (not crash); its _control runs the unmutated test case and must exit 0.
function(gbb_input_clock_mutant name anchor replacement case)
  file(READ "${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c" text)
  string(FIND "${text}" "${anchor}" first)
  string(FIND "${text}" "${anchor}" last REVERSE)
  if(first EQUAL -1 OR NOT first EQUAL last)
    message(FATAL_ERROR
      "Input clock mutant ${name}: anchor must occur exactly once (first=${first}, last=${last})")
  endif()
  string(REPLACE "${anchor}" "${replacement}" text "${text}")
  set(directory "${PROJECT_BINARY_DIR}/input-clock-mutants/${name}")
  file(WRITE "${directory}/gabbaboy.c" "${text}")

  add_library(gabbaboy_input_clock_mutant_core_${name} STATIC "${directory}/gabbaboy.c")
  target_include_directories(gabbaboy_input_clock_mutant_core_${name} PUBLIC
    "${PROJECT_SOURCE_DIR}/include" PRIVATE "${PROJECT_SOURCE_DIR}/src/core")
  target_compile_features(gabbaboy_input_clock_mutant_core_${name} PUBLIC c_std_17)
  set_target_properties(gabbaboy_input_clock_mutant_core_${name} PROPERTIES C_EXTENSIONS OFF)

  add_executable(test_input_clock_mutant_${name} "${PROJECT_SOURCE_DIR}/tests/test_input_clock.c")
  target_link_libraries(test_input_clock_mutant_${name} PRIVATE gabbaboy_input_clock_mutant_core_${name})
  target_compile_features(test_input_clock_mutant_${name} PRIVATE c_std_17)
  set_target_properties(test_input_clock_mutant_${name} PROPERTIES C_EXTENSIONS OFF)

  add_test(NAME input_clock_mutant_${name}
    COMMAND ${CMAKE_COMMAND} "-DGBB_CMD=$<TARGET_FILE:test_input_clock_mutant_${name}>;${case}"
      -DGBB_EXPECT_CODE=1 "-DGBB_EXPECT_REGEX=FAIL ${case}"
      -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
  add_test(NAME input_clock_mutant_${name}_control
    COMMAND ${CMAKE_COMMAND} "-DGBB_CMD=$<TARGET_FILE:test_input_clock>;${case}"
      -DGBB_EXPECT_CODE=0 "-DGBB_EXPECT_REGEX=PASS ${case}"
      -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
endfunction()

# The struct_size guard removed: a too-small caller struct is written instead of refused.
gbb_input_clock_mutant(short_size_writes
  [=[out->struct_size < GBB_INPUT_CLOCK_SIZE_V1]=]
  [=[0]=]
  handshake)
# The cursor always reports now: a host re-anchoring to it would queue before already queued events.
gbb_input_clock_mutant(last_is_now
  [=[out->last_queued_half_dots = last;]=]
  [=[out->last_queued_half_dots = instance->time_half_dots;]=]
  queue)

# Both installed consumers (C and C++) name and call the getter and its type and size macro. The selftest
# runs the same check over a build-tree copy of the C consumer with the call renamed away.
set(GBB_INPUT_CLOCK_CONSUMER_SYMBOLS "gbb_get_input_clock,gbb_input_clock,GBB_INPUT_CLOCK_SIZE_V1")
add_test(NAME input_clock_consumer_symbols
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CONSUMER_SOURCES=${PROJECT_SOURCE_DIR}/tests/consumers/c/main.c,${PROJECT_SOURCE_DIR}/tests/consumers/cpp/main.cpp"
    "-DGBB_SYMBOLS=${GBB_INPUT_CLOCK_CONSUMER_SYMBOLS}"
    -P "${PROJECT_SOURCE_DIR}/tests/cgb_consumer_symbol_coverage.cmake")
set_tests_properties(input_clock_consumer_symbols PROPERTIES
  PASS_REGULAR_EXPRESSION "consumer-symbol-coverage pass")
# The copy is made at configure time, so an edit to the consumer must re-run configure or the selftest
# would keep checking a stale copy.
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${PROJECT_SOURCE_DIR}/tests/consumers/c/main.c")
file(READ "${PROJECT_SOURCE_DIR}/tests/consumers/c/main.c" gbb_input_clock_consumer_text)
string(REPLACE "gbb_get_input_clock" "gbb_removed_symbol" gbb_input_clock_consumer_missing
  "${gbb_input_clock_consumer_text}")
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/input-clock-consumer-selftest")
file(WRITE "${PROJECT_BINARY_DIR}/input-clock-consumer-selftest/main.c" "${gbb_input_clock_consumer_missing}")
add_test(NAME input_clock_consumer_symbols_selftest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_CONSUMER_SOURCES=${PROJECT_BINARY_DIR}/input-clock-consumer-selftest/main.c;-DGBB_SYMBOLS=${GBB_INPUT_CLOCK_CONSUMER_SYMBOLS};-P;${PROJECT_SOURCE_DIR}/tests/cgb_consumer_symbol_coverage.cmake"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=consumer-symbol-missing gbb_get_input_clock"
    -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
