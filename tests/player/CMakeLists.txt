file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/expected-tests.txt"
  GABBABOY_PLAYER_EXPECTED_TESTS)
if(NOT GABBABOY_PLAYER_EXPECTED_TESTS)
  message(FATAL_ERROR "The optional player CTest inventory must not be empty")
endif()

foreach(test_name IN LISTS GABBABOY_PLAYER_EXPECTED_TESTS)
  if(test_name MATCHES "^player_input_(time|events|focus)$")
    if(NOT TARGET test_player_input)
      add_executable(test_player_input test_input.c)
      target_link_libraries(test_player_input PRIVATE gabbaboy-player-input)
      target_compile_features(test_player_input PRIVATE c_std_17)
      set_target_properties(test_player_input PROPERTIES C_EXTENSIONS OFF)
    endif()
    add_test(NAME ${test_name}
      COMMAND test_player_input ${test_name}
        ${PROJECT_SOURCE_DIR}/fixtures/visible-demo/demo.gb)
  elseif(test_name STREQUAL "player_smoke")
    add_test(NAME player_smoke COMMAND gabbaboy-player --smoke)
  else()
    message(FATAL_ERROR "Unknown optional player test in inventory: ${test_name}")
  endif()
endforeach()

get_property(registered_player_tests DIRECTORY PROPERTY TESTS)
list(SORT registered_player_tests)
list(SORT GABBABOY_PLAYER_EXPECTED_TESTS)
if(NOT registered_player_tests STREQUAL GABBABOY_PLAYER_EXPECTED_TESTS)
  message(FATAL_ERROR
    "Optional player tests differ from their inventory. Expected: ${GABBABOY_PLAYER_EXPECTED_TESTS}; registered: ${registered_player_tests}")
endif()
