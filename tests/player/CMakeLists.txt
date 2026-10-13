file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/expected-tests.txt"
  GABBABOY_PLAYER_EXPECTED_TESTS)
find_package(Python3 COMPONENTS Interpreter REQUIRED)
target_compile_definitions(gabbaboy-player-adapter PRIVATE
  GBB_PLAYER_AUDIO_TESTING)
if(NOT GABBABOY_PLAYER_EXPECTED_TESTS)
  message(FATAL_ERROR "The optional player CTest inventory must not be empty")
endif()

# Writes a mutated copy of a source file. The anchor must occur exactly once so a refactor cannot
# silently turn a mutant into an unmodified copy that every test would then "detect" or miss.
function(gbb_player_mutate_source input output anchor replacement)
  file(READ "${input}" text)
  string(FIND "${text}" "${anchor}" first)
  string(FIND "${text}" "${anchor}" final REVERSE)
  if(first EQUAL -1 OR NOT first EQUAL final)
    message(FATAL_ERROR "player mutant ${output}: anchor '${anchor}' must occur exactly once in "
      "${input} (first=${first} last=${final})")
  endif()
  string(REPLACE "${anchor}" "${replacement}" text "${text}")
  file(WRITE "${output}" "${text}")
  set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${input}")
endfunction()

# A mutant gabbaboy-player built from main.c and colour.c, either of which may be a mutated copy.
function(gbb_player_mutant_binary target main_source colour_source)
  add_executable(${target} "${main_source}" "${colour_source}")
  target_include_directories(${target} PRIVATE "${PROJECT_SOURCE_DIR}/src/player")
  target_link_libraries(${target} PRIVATE ${ARGN} gabbaboy-player-adapter SDL3::SDL3)
  target_compile_features(${target} PRIVATE c_std_17)
  target_compile_definitions(${target} PRIVATE
    GABBABOY_PLAYER_DEMO_ROM=\"${PROJECT_SOURCE_DIR}/fixtures/visible-demo/demo.gb\"
    GABBABOY_PLAYER_INVALID_ROM=\"${PROJECT_SOURCE_DIR}/fixtures/visible-demo/LICENSE.txt\")
  set_target_properties(${target} PROPERTIES C_EXTENSIONS OFF)
endfunction()

# D-30: the pinned SHA-256 of the 160x144 RGBA buffer the player uploads for colour-attr.gb after
# 30 frames. The close-out plan re-runs the player suite at the merged head, so a later core
# change cannot leave this pin stale unnoticed.
set(GBB_PLAYER_CGB_RGBA_SHA "8633f67ec1a9009a3597ad0260c24c5a75940d5f76301427d92435c0d769a6c4")
set(GBB_PLAYER_CGB_ROM "${PROJECT_SOURCE_DIR}/fixtures/cgb-colour/colour-attr.gb")
set(GBB_PLAYER_CGB_SPEED_RGBA_SHA "b53366fee4959a4220b6380816c20b1f2f74ba4ed0608adda0e3afc34c4a13e7")
set(GBB_PLAYER_CGB_SPEED_ROM "${PROJECT_SOURCE_DIR}/fixtures/cgb-speed/speed.gb")
set(GBB_PLAYER_CGB_SMOKE_SCRIPT "${CMAKE_CURRENT_SOURCE_DIR}/cgb_smoke.cmake")
set(GBB_PLAYER_CGB_HOME "${CMAKE_CURRENT_BINARY_DIR}/player-cgb-home")
file(MAKE_DIRECTORY "${GBB_PLAYER_CGB_HOME}")

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
  elseif(test_name MATCHES "^player_cgb_")
    # D-30: CGB colour presentation. The smoke and CLI checks drive the real player with the dummy
    # SDL audio driver and an isolated HOME; nothing is written outside the build tree.
    set(cgb_env "SDL_AUDIO_DRIVER=dummy;HOME=${GBB_PLAYER_CGB_HOME};CFFIXED_USER_HOME=${GBB_PLAYER_CGB_HOME}")
    set(cgb_smoke_args
      -DGBB_ROM=${GBB_PLAYER_CGB_ROM}
      -DGBB_DEMO=${PROJECT_SOURCE_DIR}/fixtures/visible-demo/demo.gb
      -DGBB_EXPECT_RGBA_SHA=${GBB_PLAYER_CGB_RGBA_SHA})
    set(cgb_speed_smoke_args
      -DGBB_ROM=${GBB_PLAYER_CGB_SPEED_ROM}
      -DGBB_EXPECT_RGBA_SHA=${GBB_PLAYER_CGB_SPEED_RGBA_SHA})
    if(test_name STREQUAL "player_cgb_speed_smoke")
      add_test(NAME ${test_name} COMMAND ${CMAKE_COMMAND}
        -DGBB_CHECK=speed -DGBB_PLAYER=$<TARGET_FILE:gabbaboy-player> ${cgb_speed_smoke_args}
        -P "${GBB_PLAYER_CGB_SMOKE_SCRIPT}")
      set_tests_properties(${test_name} PROPERTIES TIMEOUT 120 ENVIRONMENT "${cgb_env}")
    elseif(test_name STREQUAL "player_cgb_speed_smoke_wrong_sha")
      string(SUBSTRING "${GBB_PLAYER_CGB_SPEED_RGBA_SHA}" 0 1 first_sha_digit)
      if(first_sha_digit STREQUAL "0")
        set(wrong_sha_digit "1")
      else()
        set(wrong_sha_digit "0")
      endif()
      string(SUBSTRING "${GBB_PLAYER_CGB_SPEED_RGBA_SHA}" 1 -1 remaining_sha_digits)
      set(wrong_sha "${wrong_sha_digit}${remaining_sha_digits}")
      add_test(NAME ${test_name} COMMAND ${CMAKE_COMMAND}
        "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_CHECK=speed;-DGBB_PLAYER=$<TARGET_FILE:gabbaboy-player>;-DGBB_ROM=${GBB_PLAYER_CGB_SPEED_ROM};-DGBB_EXPECT_RGBA_SHA=${wrong_sha};-P;${GBB_PLAYER_CGB_SMOKE_SCRIPT}"
        -DGBB_EXPECT_CODE=1 "-DGBB_EXPECT_REGEX=cgb speed smoke: RGBA buffer digest"
        -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
      set_tests_properties(${test_name} PROPERTIES TIMEOUT 120 ENVIRONMENT "${cgb_env}")
    elseif(test_name STREQUAL "player_cgb_speed_smoke_mutant_ppu_follows_cpu")
      # Fifth public-player core mutant build; the default mask selects M1 (1 << 1).
      include("${PROJECT_SOURCE_DIR}/cmake/P12Mutants.cmake")
      set(mutant_core_source "${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_core_p12_mutant_m1.c")
      gbb_p12_make_mutant_core("${mutant_core_source}" 2)
      add_library(gabbaboy-player-mutant-core-m1 STATIC "${mutant_core_source}")
      target_include_directories(gabbaboy-player-mutant-core-m1 PRIVATE
        "${PROJECT_SOURCE_DIR}/include")
      target_compile_features(gabbaboy-player-mutant-core-m1 PRIVATE c_std_17)
      set_target_properties(gabbaboy-player-mutant-core-m1 PROPERTIES C_EXTENSIONS OFF)
      set(mutant_player gabbaboy-player-mutant-ppu-follows-cpu)
      gbb_player_mutant_binary(${mutant_player}
        "${PROJECT_SOURCE_DIR}/src/player/main.c"
        "${PROJECT_SOURCE_DIR}/src/player/colour.c"
        gabbaboy-player-mutant-core-m1)
      add_test(NAME ${test_name} COMMAND ${CMAKE_COMMAND}
        "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_CHECK=speed;-DGBB_PLAYER=$<TARGET_FILE:${mutant_player}>;-DGBB_ROM=${GBB_PLAYER_CGB_SPEED_ROM};-DGBB_EXPECT_RGBA_SHA=${GBB_PLAYER_CGB_SPEED_RGBA_SHA};-P;${GBB_PLAYER_CGB_SMOKE_SCRIPT}"
        -DGBB_EXPECT_CODE=1 "-DGBB_EXPECT_REGEX=cgb speed smoke: RGBA buffer digest"
        -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
      set_tests_properties(${test_name} PROPERTIES TIMEOUT 120 ENVIRONMENT "${cgb_env}")
    elseif(test_name STREQUAL "player_cgb_smoke")
      add_test(NAME ${test_name} COMMAND ${CMAKE_COMMAND}
        -DGBB_CHECK=smoke -DGBB_PLAYER=$<TARGET_FILE:gabbaboy-player> ${cgb_smoke_args}
        -P "${GBB_PLAYER_CGB_SMOKE_SCRIPT}")
      set_tests_properties(${test_name} PROPERTIES TIMEOUT 120 ENVIRONMENT "${cgb_env}")
    elseif(test_name STREQUAL "player_cgb_cli")
      add_test(NAME ${test_name} COMMAND ${CMAKE_COMMAND}
        -DGBB_CHECK=cli -DGBB_PLAYER=$<TARGET_FILE:gabbaboy-player> ${cgb_smoke_args}
        -P "${GBB_PLAYER_CGB_SMOKE_SCRIPT}")
      set_tests_properties(${test_name} PROPERTIES TIMEOUT 240 ENVIRONMENT "${cgb_env}")
    elseif(test_name STREQUAL "player_cgb_model_auto_smoke")
      # --model auto with the demo and invalid ROMs must behave exactly like player_smoke: the
      # invalid replacement fails its probe and the running session stays intact.
      add_test(NAME ${test_name} COMMAND gabbaboy-player --model auto --smoke)
      set_tests_properties(${test_name} PROPERTIES TIMEOUT 300 ENVIRONMENT "${cgb_env}")
    elseif(test_name MATCHES "^player_cgb_(expand|title_token|expand_mutant_rb_swap)$")
      set(colour_source "${PROJECT_SOURCE_DIR}/src/player/colour.c")
      if(test_name STREQUAL "player_cgb_expand_mutant_rb_swap")
        # Swap the red and blue extraction, through a marker so the two replacements cannot collide.
        set(colour_source "${CMAKE_CURRENT_BINARY_DIR}/colour_mutant_rb_swap.c")
        gbb_player_mutate_source("${PROJECT_SOURCE_DIR}/src/player/colour.c"
          "${CMAKE_CURRENT_BINARY_DIR}/colour_mutant_rb_swap_step.c"
          "out[0] = gbb_accept_expand5(value & 31u);"
          "out[0] = gbb_accept_expand5(GBB_SWAP_BLUE);")
        gbb_player_mutate_source("${CMAKE_CURRENT_BINARY_DIR}/colour_mutant_rb_swap_step.c"
          "${CMAKE_CURRENT_BINARY_DIR}/colour_mutant_rb_swap_step2.c"
          "out[2] = gbb_accept_expand5((value >> 10) & 31u);"
          "out[2] = gbb_accept_expand5(value & 31u);")
        gbb_player_mutate_source("${CMAKE_CURRENT_BINARY_DIR}/colour_mutant_rb_swap_step2.c"
          "${colour_source}" "GBB_SWAP_BLUE" "(value >> 10) & 31u")
      endif()
      set(colour_target test_player_colour)
      if(test_name STREQUAL "player_cgb_expand_mutant_rb_swap")
        set(colour_target test_player_colour_mutant_rb_swap)
      endif()
      if(NOT TARGET ${colour_target})
        add_executable(${colour_target} test_colour.c "${colour_source}")
        target_include_directories(${colour_target} PRIVATE "${PROJECT_SOURCE_DIR}/src/player")
        target_link_libraries(${colour_target} PRIVATE GabbaBoy::core gabbaboy_accept)
        target_compile_features(${colour_target} PRIVATE c_std_17)
        set_target_properties(${colour_target} PROPERTIES C_EXTENSIONS OFF)
      endif()
      if(test_name STREQUAL "player_cgb_expand_mutant_rb_swap")
        add_test(NAME ${test_name} COMMAND ${CMAKE_COMMAND}
          "-DGBB_CMD=$<TARGET_FILE:${colour_target}>;${test_name}"
          -DGBB_EXPECT_CODE=1 "-DGBB_EXPECT_REGEX=test_colour[.]c:[0-9]+: "
          -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
      else()
        add_test(NAME ${test_name} COMMAND ${colour_target} ${test_name})
      endif()
    elseif(test_name STREQUAL "player_cgb_smoke_mutant_rb_swap" OR
           test_name STREQUAL "player_cgb_smoke_mutant_dmg_path")
      if(test_name STREQUAL "player_cgb_smoke_mutant_rb_swap")
        set(mutant_main "${PROJECT_SOURCE_DIR}/src/player/main.c")
        set(mutant_colour "${CMAKE_CURRENT_BINARY_DIR}/colour_smoke_mutant_rb_swap.c")
        gbb_player_mutate_source("${PROJECT_SOURCE_DIR}/src/player/colour.c"
          "${CMAKE_CURRENT_BINARY_DIR}/colour_smoke_mutant_rb_swap_step.c"
          "out[0] = gbb_accept_expand5(value & 31u);"
          "out[0] = gbb_accept_expand5(GBB_SWAP_BLUE);")
        gbb_player_mutate_source("${CMAKE_CURRENT_BINARY_DIR}/colour_smoke_mutant_rb_swap_step.c"
          "${CMAKE_CURRENT_BINARY_DIR}/colour_smoke_mutant_rb_swap_step2.c"
          "out[2] = gbb_accept_expand5((value >> 10) & 31u);"
          "out[2] = gbb_accept_expand5(value & 31u);")
        gbb_player_mutate_source("${CMAKE_CURRENT_BINARY_DIR}/colour_smoke_mutant_rb_swap_step2.c"
          "${mutant_colour}" "GBB_SWAP_BLUE" "(value >> 10) & 31u")
        set(mutant_target gabbaboy-player-mutant-rb-swap)
      else()
        # update_frame forced onto the DMG path: the CGB profile then rejects gbb_copy_frame.
        set(mutant_main "${CMAKE_CURRENT_BINARY_DIR}/main_mutant_dmg_path.c")
        set(mutant_colour "${PROJECT_SOURCE_DIR}/src/player/colour.c")
        gbb_player_mutate_source("${PROJECT_SOURCE_DIR}/src/player/main.c" "${mutant_main}"
          "if (machine_info.profile == GBB_PROFILE_CGB_CPU_E)"
          "if (machine_info.profile == GBB_PROFILE_CGB_CPU_E && 0)")
        set(mutant_target gabbaboy-player-mutant-dmg-path)
      endif()
      gbb_player_mutant_binary(${mutant_target} "${mutant_main}" "${mutant_colour}")
      add_test(NAME ${test_name} COMMAND ${CMAKE_COMMAND}
        "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_CHECK=smoke;-DGBB_PLAYER=$<TARGET_FILE:${mutant_target}>;-DGBB_ROM=${GBB_PLAYER_CGB_ROM};-DGBB_EXPECT_RGBA_SHA=${GBB_PLAYER_CGB_RGBA_SHA};-P;${GBB_PLAYER_CGB_SMOKE_SCRIPT}"
        -DGBB_EXPECT_CODE=1 "-DGBB_EXPECT_REGEX=cgb smoke: "
        -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
      set_tests_properties(${test_name} PROPERTIES TIMEOUT 120 ENVIRONMENT "${cgb_env}")
    elseif(test_name STREQUAL "player_cgb_model_mutant_ignores_flag")
      # test_session built against a copy of session.c whose select_profile ignores the model:
      # player_session_model_select must then fail.
      set(mutant_session "${CMAKE_CURRENT_BINARY_DIR}/session_mutant_ignores_flag.c")
      gbb_player_mutate_source("${PROJECT_SOURCE_DIR}/src/player/session.c" "${mutant_session}"
        "const bool use_cgb = model_wants_cgb(model, cgb_info.cgb_flag);"
        "const bool use_cgb = false;")
      add_library(gabbaboy-player-session-mutant STATIC
        "${mutant_session}" "${PROJECT_SOURCE_DIR}/src/player/catch_up_policy.c")
      target_include_directories(gabbaboy-player-session-mutant PUBLIC
        "${PROJECT_SOURCE_DIR}/src/player")
      target_link_libraries(gabbaboy-player-session-mutant PUBLIC GabbaBoy::core SDL3::SDL3)
      target_compile_features(gabbaboy-player-session-mutant PUBLIC c_std_17)
      target_compile_definitions(gabbaboy-player-session-mutant PRIVATE GBB_PLAYER_SESSION_TESTING)
      set_target_properties(gabbaboy-player-session-mutant PROPERTIES C_EXTENSIONS OFF)
      add_executable(test_player_session_mutant_ignores_flag test_session.c
        "${PROJECT_SOURCE_DIR}/src/player/audio.c"
        "${PROJECT_SOURCE_DIR}/src/player/input.c"
        "${PROJECT_SOURCE_DIR}/src/player/script_smoke.c")
      target_link_libraries(test_player_session_mutant_ignores_flag PRIVATE
        gabbaboy-player-session-mutant gabbaboy_accept)
      target_compile_features(test_player_session_mutant_ignores_flag PRIVATE c_std_17)
      target_compile_definitions(test_player_session_mutant_ignores_flag PRIVATE
        GBB_PLAYER_SESSION_TESTING GBB_PLAYER_AUDIO_TESTING)
      set_target_properties(test_player_session_mutant_ignores_flag PROPERTIES C_EXTENSIONS OFF)
      add_test(NAME ${test_name} COMMAND ${CMAKE_COMMAND}
        "-DGBB_CMD=$<TARGET_FILE:test_player_session_mutant_ignores_flag>;player_session_model_select;${PROJECT_SOURCE_DIR}/fixtures/visible-demo/demo.gb;${CMAKE_CURRENT_BINARY_DIR}/${test_name}-temp.gb;${CMAKE_CURRENT_BINARY_DIR}/${test_name}-data"
        -DGBB_EXPECT_CODE=1 "-DGBB_EXPECT_REGEX=test_session[.]c:[0-9]+: "
        -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
      # The mutant trips a REQUIRE that returns early without destroying its temporary files or any
      # instance; under phase1-asan LeakSanitizer would replace the expected exit 1 with its own
      # code, so leak detection is off for this deliberately failing run only.
      set_tests_properties(${test_name} PROPERTIES ENVIRONMENT "ASAN_OPTIONS=detect_leaks=0")
    else()
      message(FATAL_ERROR "Unknown player_cgb_ test in inventory: ${test_name}")
    endif()
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
      "${PROJECT_SOURCE_DIR}/src/player/colour.c"
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
  elseif(test_name MATCHES "^player_claims_agree(_mutated)?$")
    # D-44: one phrase list must read the same on every player-facing claim surface.
    # Phrase lists live in files (one phrase per line) so they survive the nested list that
    # expect_exit.cmake passes to the mutated run; the phrases themselves contain '|'.
    set(claims_phrases_file "${CMAKE_CURRENT_BINARY_DIR}/claims_phrases.txt")
    set(claims_linux_phrases_file "${CMAKE_CURRENT_BINARY_DIR}/claims_linux_phrases.txt")
    file(WRITE "${claims_phrases_file}"
      "no colour correction\nDMG APU model\n--model auto|dmg|cgb\nno palette flag\nCGB double speed is implemented\nCGB mode-3 timing\n")
    file(WRITE "${claims_linux_phrases_file}" "no colour correction\nCGB double speed is implemented\nCGB mode-3 timing\n")
    set(claims_script "${CMAKE_CURRENT_SOURCE_DIR}/claims_agree.cmake")
    set(claims_args
      "-DPHRASES_FILE=${claims_phrases_file}" "-DLINUX_PHRASES_FILE=${claims_linux_phrases_file}"
      "-DLIMITATIONS=${PROJECT_SOURCE_DIR}/src/player/limitations.h"
      "-DPREVIEW_YML=${PROJECT_SOURCE_DIR}/.github/workflows/preview.yml")
    if(test_name STREQUAL "player_claims_agree")
      add_test(NAME ${test_name} COMMAND ${CMAKE_COMMAND} ${claims_args}
        "-DREADME=${PROJECT_SOURCE_DIR}/README.md" -P "${claims_script}")
    else()
      # Negative control: a README copy that drops the first phrase must be caught.
      set(mutated_readme "${CMAKE_CURRENT_BINARY_DIR}/README_claims_mutated.md")
      gbb_player_mutate_source("${PROJECT_SOURCE_DIR}/README.md" "${mutated_readme}"
        "no colour correction" "DROPPED")
      set(claims_cmd ${CMAKE_COMMAND} ${claims_args} "-DREADME=${mutated_readme}" -P "${claims_script}")
      string(REPLACE ";" "$<SEMICOLON>" claims_cmd_arg "${claims_cmd}")
      add_test(NAME ${test_name} COMMAND ${CMAKE_COMMAND}
        "-DGBB_CMD=${claims_cmd_arg}"
        -DGBB_EXPECT_CODE=1 "-DGBB_EXPECT_REGEX=claims-disagree no colour correction "
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
