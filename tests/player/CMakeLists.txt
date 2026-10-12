file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/expected-tests.txt"
  GABBABOY_PLAYER_EXPECTED_TESTS)
find_package(Python3 COMPONENTS Interpreter REQUIRED)
target_compile_definitions(gabbaboy-player-adapter PRIVATE
  GBB_PLAYER_AUDIO_TESTING)
if(NOT GABBABOY_PLAYER_EXPECTED_TESTS)
  message(FATAL_ERROR "The optional player CTest inventory must not be empty")
endif()

foreach(test_name IN LISTS GABBABOY_PLAYER_EXPECTED_TESTS)
  if(test_name STREQUAL "player_audio_counter_saturation")
    add_executable(test_player_audio_counters test_audio_counters.c)
    target_include_directories(test_player_audio_counters PRIVATE
      "${PROJECT_SOURCE_DIR}/include" "${PROJECT_SOURCE_DIR}/src/player")
    target_link_libraries(test_player_audio_counters PRIVATE SDL3::SDL3)
    target_compile_features(test_player_audio_counters PRIVATE c_std_17)
    target_compile_definitions(test_player_audio_counters PRIVATE
      GBB_PLAYER_AUDIO_TESTING)
    set_target_properties(test_player_audio_counters PROPERTIES
      C_EXTENSIONS OFF)
    add_test(NAME ${test_name} COMMAND test_player_audio_counters)
  elseif(test_name MATCHES "^player_audio_(ring|concurrent|pacing|gain|unavailable|lifecycle|device|replacement)$")
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
  elseif(test_name STREQUAL "player_session_clock_flag_scope")
    # Matched before the generic player_session_ branch: this one drives the real
    # player binary (D-21), not test_player_session.
    add_test(NAME ${test_name} COMMAND ${CMAKE_COMMAND}
      -DGBB_PLAYER=$<TARGET_FILE:gabbaboy-player>
      -DGBB_DEMO=${PROJECT_SOURCE_DIR}/fixtures/visible-demo/demo.gb
      -DGBB_INVALID=${PROJECT_SOURCE_DIR}/fixtures/visible-demo/LICENSE.txt
      -DGBB_MBC1=${PROJECT_SOURCE_DIR}/fixtures/mbc1-continuation/continuation.gb
      -DGBB_HOME=${CMAKE_CURRENT_BINARY_DIR}/clock-flag-scope-home
      -P ${CMAKE_CURRENT_SOURCE_DIR}/clock_flag_scope.cmake)
    set_tests_properties(${test_name} PROPERTIES TIMEOUT 60)
  elseif(test_name MATCHES "^player_session_[a-z0-9_]+$")
    if(NOT TARGET test_player_session)
      add_library(gabbaboy-player-session-test STATIC
        "${PROJECT_SOURCE_DIR}/src/player/session.c"
        "${PROJECT_SOURCE_DIR}/src/player/catch_up_policy.c")
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
      target_sources(test_player_session PRIVATE
        "${PROJECT_SOURCE_DIR}/src/player/audio.c"
        "${PROJECT_SOURCE_DIR}/src/player/input.c"
        "${PROJECT_SOURCE_DIR}/src/player/script_smoke.c")
      target_link_libraries(test_player_session PRIVATE
        gabbaboy-player-session-test gabbaboy_accept)
      target_compile_features(test_player_session PRIVATE c_std_17)
      target_compile_definitions(test_player_session PRIVATE
        GBB_PLAYER_SESSION_TESTING GBB_PLAYER_AUDIO_TESTING)
      set_target_properties(test_player_session PROPERTIES C_EXTENSIONS OFF)
    endif()
    set(player_session_extra "")
    if(test_name MATCHES "^player_session_script_(no_input|invalid)$")
      # The pinned Libbet ROM and the no-input script feed both script controls.
      set(player_session_extra
        ${PROJECT_SOURCE_DIR}/fixtures/libbet/libbet.gb
        ${PROJECT_SOURCE_DIR}/tests/acceptance/inputs/libbet-no-input.input)
    endif()
    if(test_name MATCHES "^player_session_v1_(corpus_load|mbc1_write_identical)$")
      # D-25: the two real v0.1.2 envelopes recorded in the corpus manifest.
      set(player_session_extra ${PROJECT_SOURCE_DIR}/fixtures/save-envelope-v1)
    endif()
    add_test(NAME ${test_name} COMMAND test_player_session ${test_name}
      ${PROJECT_SOURCE_DIR}/fixtures/visible-demo/demo.gb
      ${CMAKE_CURRENT_BINARY_DIR}/${test_name}-temp.gb
      ${CMAKE_CURRENT_BINARY_DIR}/${test_name}-data
      ${player_session_extra})
    if(test_name STREQUAL "player_session_script_no_input")
      set_tests_properties(${test_name} PROPERTIES TIMEOUT 300
        ENVIRONMENT "SDL_AUDIO_DRIVER=dummy")
    endif()
  elseif(test_name MATCHES "^player_continuation_(resume|missing_save|wrong_rom|mutated_payload|mbc3_rtc_(resume|delta|rollback|halted|no_clock)|mbc3_wrong_rom|mbc2_resume|mbc5_resume)$")
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
    # Each scenario names the original fixture whose protocol it drives.
    if(test_name MATCHES "^player_continuation_mbc3_")
      set(player_continuation_rom
        ${PROJECT_SOURCE_DIR}/fixtures/mbc3-rtc-continuation/continuation.gb)
    elseif(test_name STREQUAL "player_continuation_mbc2_resume")
      set(player_continuation_rom
        ${PROJECT_SOURCE_DIR}/fixtures/mbc2-continuation/continuation.gb)
    elseif(test_name STREQUAL "player_continuation_mbc5_resume")
      set(player_continuation_rom
        ${PROJECT_SOURCE_DIR}/fixtures/mbc5-continuation/continuation.gb)
    else()
      set(player_continuation_rom
        ${PROJECT_SOURCE_DIR}/fixtures/mbc1-continuation/continuation.gb)
    endif()
    add_test(NAME ${test_name} COMMAND test_player_continuation ${test_name}
      ${player_continuation_rom}
      ${CMAKE_CURRENT_BINARY_DIR}/${test_name}-data)
  elseif(test_name STREQUAL "player_smoke")
    add_test(NAME player_smoke COMMAND gabbaboy-player --smoke)
    set(player_smoke_home "${CMAKE_CURRENT_BINARY_DIR}/player-smoke-home")
    file(MAKE_DIRECTORY "${player_smoke_home}")
    set_tests_properties(player_smoke PROPERTIES
      ENVIRONMENT "HOME=${player_smoke_home};CFFIXED_USER_HOME=${player_smoke_home}")
  elseif(test_name STREQUAL "player_reset_transition")
    add_executable(test_player_reset_transition
      test_reset_transition.c
      "${PROJECT_SOURCE_DIR}/src/player/audio.c"
      "${PROJECT_SOURCE_DIR}/src/player/input.c"
      "${PROJECT_SOURCE_DIR}/src/player/presentation.c"
      "${PROJECT_SOURCE_DIR}/src/player/script_smoke.c")
    target_link_libraries(test_player_reset_transition PRIVATE
      gabbaboy-player-session-test gabbaboy_accept)
    target_compile_features(test_player_reset_transition PRIVATE c_std_17)
    target_compile_definitions(test_player_reset_transition PRIVATE
      GBB_PLAYER_AUDIO_TESTING GBB_PLAYER_SESSION_TESTING
      GABBABOY_PLAYER_DEMO_ROM="${PROJECT_SOURCE_DIR}/fixtures/visible-demo/demo.gb"
      GABBABOY_PLAYER_INVALID_ROM="${PROJECT_SOURCE_DIR}/fixtures/visible-demo/LICENSE.txt")
    set_target_properties(test_player_reset_transition PROPERTIES
      C_EXTENSIONS OFF)
    add_test(NAME player_reset_transition
      COMMAND test_player_reset_transition)
    set_tests_properties(player_reset_transition PROPERTIES
      ENVIRONMENT "SDL_AUDIO_DRIVER=dummy")
  elseif(test_name MATCHES "^player_script_smoke_surface(_selftest|_main_selftest)?$")
    # D-38: the scripted-smoke diagnostic stays free of environment, network, save writes
    # and persistence. The selftest runs the same check on a copy with an injected getenv
    # call and must fail, so the guard is proven able to catch the thing it forbids.
    set(smoke_surface_script
      "${PROJECT_SOURCE_DIR}/tests/player/verify_script_smoke_surface.cmake")
    set(smoke_surface_args
      -DGBB_SMOKE_H=${PROJECT_SOURCE_DIR}/src/player/script_smoke.h
      -DGBB_PLAYER_MAIN=${PROJECT_SOURCE_DIR}/src/player/main.c)
    if(test_name STREQUAL "player_script_smoke_surface")
      add_test(NAME ${test_name} COMMAND ${CMAKE_COMMAND}
        -DGBB_SMOKE_C=${PROJECT_SOURCE_DIR}/src/player/script_smoke.c
        ${smoke_surface_args} -P "${smoke_surface_script}")
    elseif(test_name STREQUAL "player_script_smoke_surface_main_selftest")
      # The same check on a copy of main.c with a battery save injected into the script section.
      set(injected_main_c "${CMAKE_CURRENT_BINARY_DIR}/main_injected_battery_save.c")
      file(READ "${PROJECT_SOURCE_DIR}/src/player/main.c" real_main_c)
      string(REPLACE "static void script_progress("
        "static bool gbb_selftest_injected(player *app) { return attempt_battery_save(app, false); }\nstatic void script_progress("
        injected_main_text "${real_main_c}")
      if(injected_main_text STREQUAL real_main_c)
        message(FATAL_ERROR "script-smoke-surface main selftest: injection marker not found")
      endif()
      file(WRITE "${injected_main_c}" "${injected_main_text}")
      set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
        "${PROJECT_SOURCE_DIR}/src/player/main.c")
      add_test(NAME ${test_name} COMMAND ${CMAKE_COMMAND}
        -DGBB_CMD=${CMAKE_COMMAND}$<SEMICOLON>-DGBB_SMOKE_C=${PROJECT_SOURCE_DIR}/src/player/script_smoke.c$<SEMICOLON>-DGBB_SMOKE_H=${PROJECT_SOURCE_DIR}/src/player/script_smoke.h$<SEMICOLON>-DGBB_PLAYER_MAIN=${injected_main_c}$<SEMICOLON>-P$<SEMICOLON>${smoke_surface_script}
        -DGBB_EXPECT_CODE=1
        "-DGBB_EXPECT_REGEX=script-smoke-surface: attempt_battery_save in main.c script section"
        -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
    else()
      set(injected_smoke_c
        "${CMAKE_CURRENT_BINARY_DIR}/script_smoke_injected_getenv.c")
      file(READ "${PROJECT_SOURCE_DIR}/src/player/script_smoke.c" real_smoke_c)
      file(WRITE "${injected_smoke_c}"
        "${real_smoke_c}\nstatic const char *gbb_selftest_injected(void) { return getenv(\"GBB_SCRIPT_SELFTEST\"); }\n")
      set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
        "${PROJECT_SOURCE_DIR}/src/player/script_smoke.c")
      add_test(NAME ${test_name} COMMAND ${CMAKE_COMMAND}
        -DGBB_CMD=${CMAKE_COMMAND}$<SEMICOLON>-DGBB_SMOKE_C=${injected_smoke_c}$<SEMICOLON>-DGBB_SMOKE_H=${PROJECT_SOURCE_DIR}/src/player/script_smoke.h$<SEMICOLON>-DGBB_PLAYER_MAIN=${PROJECT_SOURCE_DIR}/src/player/main.c$<SEMICOLON>-P$<SEMICOLON>${smoke_surface_script}
        -DGBB_EXPECT_CODE=1
        "-DGBB_EXPECT_REGEX=script-smoke-surface: getenv"
        -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
    endif()
    set_tests_properties(${test_name} PROPERTIES TIMEOUT 30)
  elseif(test_name STREQUAL "player_limitations")
    if(NOT TARGET test_player_limitations)
      add_executable(test_player_limitations test_limitations.c)
      target_include_directories(test_player_limitations PRIVATE
        "${PROJECT_SOURCE_DIR}/src/player")
      target_compile_features(test_player_limitations PRIVATE c_std_17)
      set_target_properties(test_player_limitations PROPERTIES C_EXTENSIONS OFF)
    endif()
    add_test(NAME player_limitations COMMAND test_player_limitations)
  elseif(test_name STREQUAL "player_verified_output_directory")
    add_test(NAME player_verified_output_directory
      COMMAND "${Python3_EXECUTABLE}"
        "${PROJECT_SOURCE_DIR}/tests/scripts/test_verified_player_output_dir.py")
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
