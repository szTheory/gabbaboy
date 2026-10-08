file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/expected-tests.txt"
  GABBABOY_PLAYER_EXPECTED_TESTS)
target_compile_definitions(gabbaboy-player-adapter PRIVATE
  GBB_PLAYER_AUDIO_TESTING)
if(NOT GABBABOY_PLAYER_EXPECTED_TESTS)
  message(FATAL_ERROR "The optional player CTest inventory must not be empty")
endif()

foreach(test_name IN LISTS GABBABOY_PLAYER_EXPECTED_TESTS)
  if(test_name MATCHES "^player_audio_(ring|concurrent|pacing|gain|unavailable|lifecycle|device|replacement)$")
    if(NOT TARGET test_player_audio)
      add_executable(test_player_audio test_audio.c)
      target_link_libraries(test_player_audio PRIVATE gabbaboy-player-adapter)
      target_compile_features(test_player_audio PRIVATE c_std_17)
      target_compile_definitions(test_player_audio PRIVATE
        GBB_PLAYER_AUDIO_TESTING)
      set_target_properties(test_player_audio PROPERTIES C_EXTENSIONS OFF)
    endif()
    if(test_name STREQUAL "player_audio_replacement")
      add_test(NAME ${test_name} COMMAND test_player_audio ${test_name}
        ${PROJECT_SOURCE_DIR}/fixtures/visible-demo/demo.gb
        ${CMAKE_CURRENT_BINARY_DIR}/player-audio-replacement-missing.gb)
    else()
      add_test(NAME ${test_name} COMMAND test_player_audio ${test_name})
    endif()
  elseif(test_name MATCHES "^player_input_(time|events|focus|sources|reconnect|focus_audio)$")
    if(NOT TARGET test_player_input)
      add_executable(test_player_input test_input.c)
      target_link_libraries(test_player_input PRIVATE gabbaboy-player-adapter)
      target_compile_features(test_player_input PRIVATE c_std_17)
      set_target_properties(test_player_input PROPERTIES C_EXTENSIONS OFF)
    endif()
    add_test(NAME ${test_name}
      COMMAND test_player_input ${test_name}
        ${PROJECT_SOURCE_DIR}/fixtures/visible-demo/demo.gb)
  elseif(test_name MATCHES "^player_presentation_(native|integer|odd|letterbox|hidpi|resize|undersized|large)$")
    if(NOT TARGET test_player_presentation)
      add_executable(test_player_presentation test_presentation.c)
      target_link_libraries(test_player_presentation PRIVATE gabbaboy-player-adapter)
      target_compile_features(test_player_presentation PRIVATE c_std_17)
      set_target_properties(test_player_presentation PROPERTIES C_EXTENSIONS OFF)
    endif()
    add_test(NAME ${test_name} COMMAND test_player_presentation ${test_name})
  elseif(test_name MATCHES "^player_session_[a-z0-9_]+$")
    if(NOT TARGET test_player_session)
      add_library(gabbaboy-player-session-test STATIC
        "${PROJECT_SOURCE_DIR}/src/player/session.c")
      target_include_directories(gabbaboy-player-session-test PUBLIC
        "${PROJECT_SOURCE_DIR}/src/player")
      target_link_libraries(gabbaboy-player-session-test PUBLIC
        GabbaBoy::core SDL3::SDL3)
      target_compile_features(gabbaboy-player-session-test PUBLIC c_std_17)
      target_compile_definitions(gabbaboy-player-session-test PRIVATE
        GBB_PLAYER_SESSION_TESTING)
      set_target_properties(gabbaboy-player-session-test PROPERTIES
        C_EXTENSIONS OFF)
      add_executable(test_player_session test_session.c)
      target_link_libraries(test_player_session PRIVATE
        gabbaboy-player-session-test)
      target_compile_features(test_player_session PRIVATE c_std_17)
      target_compile_definitions(test_player_session PRIVATE
        GBB_PLAYER_SESSION_TESTING)
      set_target_properties(test_player_session PROPERTIES C_EXTENSIONS OFF)
    endif()
    add_test(NAME ${test_name} COMMAND test_player_session ${test_name}
      ${PROJECT_SOURCE_DIR}/fixtures/visible-demo/demo.gb
      ${CMAKE_CURRENT_BINARY_DIR}/${test_name}-temp.gb
      ${CMAKE_CURRENT_BINARY_DIR}/${test_name}-data)
  elseif(test_name MATCHES "^player_continuation_(resume|missing_save|wrong_rom|mutated_payload)$")
    if(NOT TARGET test_player_continuation)
      add_executable(test_player_continuation test_continuation.c)
      target_link_libraries(test_player_continuation PRIVATE
        gabbaboy-player-session-test)
      target_compile_features(test_player_continuation PRIVATE c_std_17)
      target_compile_definitions(test_player_continuation PRIVATE
        GBB_PLAYER_SESSION_TESTING)
      set_target_properties(test_player_continuation PROPERTIES
        C_EXTENSIONS OFF)
    endif()
    add_test(NAME ${test_name} COMMAND test_player_continuation ${test_name}
      ${PROJECT_SOURCE_DIR}/fixtures/mbc1-continuation/continuation.gb
      ${CMAKE_CURRENT_BINARY_DIR}/${test_name}-data)
  elseif(test_name STREQUAL "player_smoke")
    add_test(NAME player_smoke COMMAND gabbaboy-player --smoke)
  elseif(test_name STREQUAL "player_limitations")
    if(NOT TARGET test_player_limitations)
      add_executable(test_player_limitations test_limitations.c)
      target_include_directories(test_player_limitations PRIVATE
        "${PROJECT_SOURCE_DIR}/src/player")
      target_compile_features(test_player_limitations PRIVATE c_std_17)
      set_target_properties(test_player_limitations PROPERTIES C_EXTENSIONS OFF)
    endif()
    add_test(NAME player_limitations COMMAND test_player_limitations)
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
