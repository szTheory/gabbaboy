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
