set(GBB_TEST_INSTALL_PREFIX "" CACHE PATH "Relocated install prefix used by installed-package smoke tests")
include(${PROJECT_SOURCE_DIR}/cmake/ExpectedTests.cmake)

add_executable(test_api test_api.c)
target_link_libraries(test_api PRIVATE GabbaBoy::core)
target_compile_features(test_api PRIVATE c_std_17)
set_target_properties(test_api PROPERTIES C_EXTENSIONS OFF)
add_test(NAME instance_lifecycle COMMAND test_api instance_lifecycle ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME independent_instances COMMAND test_api independent_instances ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME reset_idempotency COMMAND test_api reset_idempotency ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME run_bounds COMMAND test_api run_bounds ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME trace_capacity COMMAND test_api trace_capacity ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME illegal_lockup_api COMMAND test_api illegal_lockup ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)

find_package(Threads REQUIRED)
add_executable(test_instance_concurrency test_instance_concurrency.c)
target_link_libraries(test_instance_concurrency PRIVATE GabbaBoy::core Threads::Threads)
target_compile_features(test_instance_concurrency PRIVATE c_std_17)
set_target_properties(test_instance_concurrency PROPERTIES C_EXTENSIONS OFF)
add_test(NAME concurrent_independent_instances COMMAND test_instance_concurrency
  ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)

add_executable(test_cartridge test_cartridge.c)
target_link_libraries(test_cartridge PRIVATE GabbaBoy::core)
target_compile_features(test_cartridge PRIVATE c_std_17)
set_target_properties(test_cartridge PROPERTIES C_EXTENSIONS OFF)
add_test(NAME cartridge_tracer COMMAND test_cartridge cartridge_tracer)
add_test(NAME cartridge_bank_matrix COMMAND test_cartridge cartridge_bank_matrix)
add_test(NAME cartridge_ram_banks COMMAND test_cartridge cartridge_ram_banks)
add_test(NAME cartridge_no_ram_reads COMMAND test_cartridge cartridge_no_ram_reads)

add_executable(test_mbc2 test_mbc2.c)
target_link_libraries(test_mbc2 PRIVATE GabbaBoy::core)
target_compile_features(test_mbc2 PRIVATE c_std_17)
set_target_properties(test_mbc2 PROPERTIES C_EXTENSIONS OFF)
foreach(case tracer header_matrix register_decode ram_echo reset
  battery_image battery_import battery_idempotent battery_errors battery_no_battery
  two_instance_roundtrip)
  add_test(NAME mbc2_${case} COMMAND test_mbc2 mbc2_${case})
endforeach()

add_executable(test_mbc5 test_mbc5.c)
target_link_libraries(test_mbc5 PRIVATE GabbaBoy::core)
target_compile_features(test_mbc5 PRIVATE c_std_17)
set_target_properties(test_mbc5 PROPERTIES C_EXTENSIONS OFF)
foreach(case tracer header_matrix rom_banking ram_enable ram_banking no_ram_window
  battery rom_bound cgb_flag_ignored cross_mapper_control
  rumble_state rumble_errors rumble_reset_load reset_preserves_ram)
  add_test(NAME mbc5_${case} COMMAND test_mbc5 mbc5_${case})
endforeach()

# White-box: the test includes src/core/gabbaboy.c itself, so it must not link
# the core library (duplicate definitions).
add_executable(test_mbc5_internal test_mbc5_internal.c)
target_include_directories(test_mbc5_internal PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_mbc5_internal PRIVATE c_std_17)
set_target_properties(test_mbc5_internal PROPERTIES C_EXTENSIONS OFF)
add_test(NAME mbc5_rumble_saturation COMMAND test_mbc5_internal mbc5_rumble_saturation)

# Original banking guest (D-33): the committed 64 KiB ROM is run through the real CPU and bus.
add_test(NAME mbc5_banking_guest
  COMMAND test_mbc5 mbc5_banking_guest ${PROJECT_SOURCE_DIR}/fixtures/mbc5-banking/banking.gb)
# In-memory variants (never written to disk): $1B non-rumble type, and the 8 MiB bank $1FF inflation.
add_test(NAME mbc5_banking_guest_1b
  COMMAND test_mbc5 mbc5_banking_guest_1b ${PROJECT_SOURCE_DIR}/fixtures/mbc5-banking/banking.gb)
add_test(NAME mbc5_bank_1ff
  COMMAND test_mbc5 mbc5_bank_1ff ${PROJECT_SOURCE_DIR}/fixtures/mbc5-banking/banking.gb)

# Ninth-bit core mutant (D-29, amended): a copy of the core whose MBC5 ROM bank composition keeps
# `& 0u` of the high bank register instead of `& 1u`, so banks $100 and above alias $00-$FF. The
# Mooneye mbc5 harness stops at bank $FF and cannot see this, so the discriminator is the original
# mbc5_bank_1ff case. Same configure-time, exactly-once anchor discipline as the JOYP mutant in
# tests/acceptance; the library and executable are test-only and never installed or exported.
set(GBB_NINTH_SOURCE ${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c)
set(GBB_NINTH_PATTERN "& 1u) << 8")
set(GBB_NINTH_REPLACEMENT "& 0u) << 8")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${GBB_NINTH_SOURCE})
file(READ ${GBB_NINTH_SOURCE} gbb_ninth_core_text)
string(FIND "${gbb_ninth_core_text}" "${GBB_NINTH_PATTERN}" gbb_ninth_first)
string(FIND "${gbb_ninth_core_text}" "${GBB_NINTH_PATTERN}" gbb_ninth_last REVERSE)
if(gbb_ninth_first EQUAL -1 OR NOT gbb_ninth_first EQUAL gbb_ninth_last)
  message(FATAL_ERROR "ninth-bit mutant pattern '${GBB_NINTH_PATTERN}' must occur exactly once in "
    "${GBB_NINTH_SOURCE} (first=${gbb_ninth_first} last=${gbb_ninth_last})")
endif()
# The core text carries semicolons, so it stays quoted and never enters a list operation.
string(REPLACE "${GBB_NINTH_PATTERN}" "${GBB_NINTH_REPLACEMENT}" gbb_ninth_text "${gbb_ninth_core_text}")
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_ninth_bit_mutant.c "${gbb_ninth_text}")

add_library(gabbaboy_core_ninth_bit_mutant STATIC ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_ninth_bit_mutant.c)
target_include_directories(gabbaboy_core_ninth_bit_mutant PUBLIC ${PROJECT_SOURCE_DIR}/include)
target_compile_features(gabbaboy_core_ninth_bit_mutant PUBLIC c_std_17)
set_target_properties(gabbaboy_core_ninth_bit_mutant PROPERTIES C_EXTENSIONS OFF)
target_compile_definitions(gabbaboy_core_ninth_bit_mutant PRIVATE
  GBB_BUILD_REVISION="ninth-bit-mutant" GBB_BUILD_QUALIFIED=0)

add_executable(test_mbc5_ninth_bit_mutant test_mbc5.c)
target_link_libraries(test_mbc5_ninth_bit_mutant PRIVATE gabbaboy_core_ninth_bit_mutant)
target_compile_features(test_mbc5_ninth_bit_mutant PRIVATE c_std_17)
set_target_properties(test_mbc5_ninth_bit_mutant PROPERTIES C_EXTENSIONS OFF)

# The mutant must be caught at the C005 bank $1FF assertion specifically (exit 1, the REQUIRE text).
add_test(NAME mbc5_ninth_bit_mutant_bank_1ff
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_mbc5_ninth_bit_mutant>;mbc5_bank_1ff;${PROJECT_SOURCE_DIR}/fixtures/mbc5-banking/banking.gb"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=r.3. == 0x01u"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
# In-mutant control: the same guest on its committed 64 KiB image never selects a bank at or above
# $100, so the mutant core still passes it (exit 0), which shows the mutant is not simply broken.
add_test(NAME mbc5_ninth_bit_mutant_control_below_100
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_mbc5_ninth_bit_mutant>;mbc5_banking_guest;${PROJECT_SOURCE_DIR}/fixtures/mbc5-banking/banking.gb"
    -DGBB_EXPECT_CODE=0
    "-DGBB_EXPECT_REGEX=.*"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

add_executable(test_battery test_battery.c)
target_link_libraries(test_battery PRIVATE GabbaBoy::core)
target_compile_features(test_battery PRIVATE c_std_17)
set_target_properties(test_battery PROPERTIES C_EXTENSIONS OFF)
foreach(case roundtrip8 roundtrip32 errors no_battery lifecycle instances)
  add_test(NAME battery_${case} COMMAND test_battery battery_${case})
endforeach()

add_executable(test_battery_fuzz test_battery_fuzz.c)
target_link_libraries(test_battery_fuzz PRIVATE GabbaBoy::core)
target_compile_features(test_battery_fuzz PRIVATE c_std_17)
set_target_properties(test_battery_fuzz PROPERTIES C_EXTENSIONS OFF)
add_test(NAME battery_api_fuzz COMMAND test_battery_fuzz)

add_executable(test_bus test_bus.c)
target_link_libraries(test_bus PRIVATE GabbaBoy::core)
target_compile_features(test_bus PRIVATE c_std_17)
set_target_properties(test_bus PROPERTIES C_EXTENSIONS OFF)
foreach(case wram_guest echo_hram absent_cart preflight unsupported_reads unsupported_stack unsupported_fetch halt_bug_fetch)
  add_test(NAME bus_${case} COMMAND test_bus ${case})
endforeach()

add_executable(test_timer test_timer.c)
target_link_libraries(test_timer PRIVATE GabbaBoy::core)
target_compile_features(test_timer PRIVATE c_std_17)
set_target_properties(test_timer PROPERTIES C_EXTENSIONS OFF)
foreach(case guest_overflow mid_instruction selectors div_write tac_write tima_collision tma_collision)
  add_test(NAME timer_${case} COMMAND test_timer ${case})
endforeach()

add_executable(test_audio test_audio.c)
target_link_libraries(test_audio PRIVATE GabbaBoy::core)
target_compile_features(test_audio PRIVATE c_std_17)
set_target_properties(test_audio PROPERTIES C_EXTENSIONS OFF)
foreach(case tracer capacity signal fractional_edges partition filter
             rounding saturation api_edges)
  add_test(NAME audio_${case} COMMAND test_audio audio_${case})
endforeach()

add_library(gabbaboy_core_alloc_probe OBJECT "${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c")
target_include_directories(gabbaboy_core_alloc_probe PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(gabbaboy_core_alloc_probe PRIVATE c_std_17)
target_compile_definitions(gabbaboy_core_alloc_probe PRIVATE
  malloc=gbb_test_malloc calloc=gbb_test_calloc
  realloc=gbb_test_realloc free=gbb_test_free)
set_target_properties(gabbaboy_core_alloc_probe PROPERTIES C_EXTENSIONS OFF)
add_executable(test_audio_no_alloc test_audio_no_alloc.c
  $<TARGET_OBJECTS:gabbaboy_core_alloc_probe>)
target_include_directories(test_audio_no_alloc PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_audio_no_alloc PRIVATE c_std_17)
set_target_properties(test_audio_no_alloc PROPERTIES C_EXTENSIONS OFF)
add_test(NAME audio_no_alloc COMMAND test_audio_no_alloc)

add_executable(test_apu test_apu.c)
target_link_libraries(test_apu PRIVATE GabbaBoy::core)
target_compile_features(test_apu PRIVATE c_std_17)
set_target_properties(test_apu PROPERTIES C_EXTENSIONS OFF)
foreach(case pulse mixer sequencer timeline wave noise envelope sweep power)
  add_test(NAME apu_${case} COMMAND test_apu apu_${case})
endforeach()

add_executable(test_serial test_serial.c)
target_link_libraries(test_serial PRIVATE GabbaBoy::core)
target_compile_features(test_serial PRIVATE c_std_17)
set_target_properties(test_serial PROPERTIES C_EXTENSIONS OFF)
foreach(case internal_disconnected external_pending unqualified_overlap)
  add_test(NAME serial_${case} COMMAND test_serial ${case})
endforeach()

add_executable(test_cpu test_cpu.c)
target_link_libraries(test_cpu PRIVATE GabbaBoy::core)
target_compile_features(test_cpu PRIVATE c_std_17)
set_target_properties(test_cpu PROPERTIES C_EXTENSIONS OFF)
foreach(case call_stack return_phases conditional_budget base_matrix base_semantic_tracer base_conditional_paths base_arithmetic_edges base_address_effects illegal_lockup flags_edges timed_access address_wrap stack_wrap cb_wram cb_budget cb_matrix cb_flags_edges cb_timed_access)
  add_test(NAME cpu_${case} COMMAND test_cpu ${case})
endforeach()

add_executable(test_control test_control.c)
target_link_libraries(test_control PRIVATE GabbaBoy::core)
target_compile_features(test_control PRIVATE c_std_17)
set_target_properties(test_control PROPERTIES C_EXTENSIONS OFF)
add_test(NAME interrupt_entry COMMAND test_control interrupt_entry)
add_test(NAME interrupt_budget COMMAND test_control interrupt_budget)
foreach(case interrupt_ei_delay interrupt_ei_chain interrupt_diagnostic_order interrupt_priority halt_idle halt_timer_partition halt_bug stop_wait reset_profile reset_header_flags reset_lockup)
  add_test(NAME ${case} COMMAND test_control ${case})
endforeach()

add_executable(test_events test_events.c)
target_link_libraries(test_events PRIVATE GabbaBoy::core)
target_compile_features(test_events PRIVATE c_std_17)
set_target_properties(test_events PROPERTIES C_EXTENSIONS OFF)
foreach(case event_stop_wake event_boundary event_queue_order event_queue_atomic event_queue_failure_precedence event_partition
             event_deadline_inside event_external_serial_edges event_time_overflow run_output_capacity)
  add_test(NAME ${case} COMMAND test_events ${case})
endforeach()

add_executable(test_joypad test_joypad.c)
target_link_libraries(test_joypad PRIVATE GabbaBoy::core)
target_compile_features(test_joypad PRIVATE c_std_17)
set_target_properties(test_joypad PROPERTIES C_EXTENSIONS OFF)
foreach(case joypad_selection joypad_queue_atomic joypad_equal_time joypad_partition joypad_interrupt)
  add_test(NAME ${case} COMMAND test_joypad ${case})
endforeach()

add_executable(test_loader test_loader.c)
target_link_libraries(test_loader PRIVATE GabbaBoy::core)
target_compile_features(test_loader PRIVATE c_std_17)
set_target_properties(test_loader PROPERTIES C_EXTENSIONS OFF)
foreach(case truncated oversized invalid_header unsupported_cartridge unsupported_rom_size unsupported_declared_size unsupported_ram_size length_mismatch excess_actual null_arguments non_destructive mbc1_matrix mbc1m_variant)
  add_test(NAME loader_${case} COMMAND test_loader ${case} ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
endforeach()

add_executable(test_loader_fuzz test_loader_fuzz.c)
target_link_libraries(test_loader_fuzz PRIVATE GabbaBoy::core)
target_compile_features(test_loader_fuzz PRIVATE c_std_17)
set_target_properties(test_loader_fuzz PROPERTIES C_EXTENSIONS OFF)
add_test(NAME loader_boundary_fuzz
  COMMAND test_loader_fuzz ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)

add_executable(test_fuzz_core test_fuzz_core.c fuzz_core.c)
target_link_libraries(test_fuzz_core PRIVATE GabbaBoy::core)
target_compile_features(test_fuzz_core PRIVATE c_std_17)
target_compile_definitions(test_fuzz_core PRIVATE GBB_FUZZ_STANDALONE_TEST=1)
set_target_properties(test_fuzz_core PROPERTIES C_EXTENSIONS OFF)
add_test(NAME fuzz_core_regressions COMMAND test_fuzz_core)

if(CMAKE_C_COMPILER_ID MATCHES "Clang")
  include(CheckCSourceCompiles)
  set(_gbb_saved_required_flags "${CMAKE_REQUIRED_FLAGS}")
  set(CMAKE_REQUIRED_FLAGS "${CMAKE_REQUIRED_FLAGS} -fsanitize=fuzzer,address,undefined")
  check_c_source_compiles(
    "#include <stdint.h>\n#include <stddef.h>\nint LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) { (void)data; (void)size; return 0; }"
    GBB_HAS_CLANG_LIBFUZZER_RUNTIME)
  set(CMAKE_REQUIRED_FLAGS "${_gbb_saved_required_flags}")
  unset(_gbb_saved_required_flags)
  if(GBB_HAS_CLANG_LIBFUZZER_RUNTIME)
    add_executable(fuzz_core fuzz_core.c ${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c)
    target_include_directories(fuzz_core PRIVATE ${PROJECT_SOURCE_DIR}/include)
    target_compile_features(fuzz_core PRIVATE c_std_17)
    target_compile_options(fuzz_core PRIVATE -fsanitize=fuzzer,address,undefined -fno-omit-frame-pointer)
    target_link_options(fuzz_core PRIVATE -fsanitize=fuzzer,address,undefined)
    set_target_properties(fuzz_core PROPERTIES C_EXTENSIONS OFF)
    message(STATUS "Bounded compiler-integrated libFuzzer target enabled")
  else()
    message(STATUS "Matching Clang libFuzzer runtime unavailable; deterministic sanitizer regressions remain enabled")
  endif()
endif()

add_executable(test_tracer test_tracer.c)
target_link_libraries(test_tracer PRIVATE GabbaBoy::core)
target_compile_features(test_tracer PRIVATE c_std_17)
set_target_properties(test_tracer PROPERTIES C_EXTENSIONS OFF)
foreach(case success failure unsupported timeout trace)
  add_test(NAME tracer_${case} COMMAND test_tracer ${case} ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
endforeach()
foreach(case frame_composition_tracer joypad_gameplay_tracer)
  add_test(NAME ${case} COMMAND test_tracer ${case} ${PROJECT_SOURCE_DIR}/fixtures/visible-demo/demo.gb)
endforeach()

add_executable(test_ppu test_ppu.c)
target_link_libraries(test_ppu PRIVATE GabbaBoy::core)
target_compile_features(test_ppu PRIVATE c_std_17)
set_target_properties(test_ppu PROPERTIES C_EXTENSIONS OFF)
foreach(case frame_composition_bg frame_composition_window frame_composition_sprites frame_composition_priority
             ppu_timing_modes ppu_timing_stat ppu_timing_lcd ppu_timing_fetch
             ppu_timing_partition frame_copy_failures frame_generation_lifecycle)
  add_test(NAME ${case} COMMAND test_ppu ${case})
endforeach()

add_executable(test_dma test_dma.c)
target_link_libraries(test_dma PRIVATE GabbaBoy::core)
target_compile_features(test_dma PRIVATE c_std_17)
set_target_properties(test_dma PROPERTIES C_EXTENSIONS OFF)
foreach(case dma_progress dma_start dma_restart dma_register_readback dma_source_mapping dma_hram dma_interrupt_stack dma_partition
             dma_vram_lock dma_oam_lock dma_contention dma_ppu_overlap dma_oam_entry39 dma_oam_entry39_reset
             dma_active_mode_matrix dma_ppu_cpu_collision dma_ppu_word_boundaries)
  add_test(NAME ${case} COMMAND test_dma ${case})
endforeach()

add_test(NAME tracer_smoke COMMAND gabbaboy-runner ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DROM=${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb
    -DMANIFEST=${PROJECT_SOURCE_DIR}/fixtures/tracer/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixture.cmake)
add_test(NAME visible_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DROM=${PROJECT_SOURCE_DIR}/fixtures/visible-demo/demo.gb
    -DMANIFEST=${PROJECT_SOURCE_DIR}/fixtures/visible-demo/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixture.cmake)
add_test(NAME mbc1_continuation_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DROM=${PROJECT_SOURCE_DIR}/fixtures/mbc1-continuation/continuation.gb
    -DMANIFEST=${PROJECT_SOURCE_DIR}/fixtures/mbc1-continuation/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixture.cmake)
add_test(NAME mbc5_banking_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DROM=${PROJECT_SOURCE_DIR}/fixtures/mbc5-banking/banking.gb
    -DMANIFEST=${PROJECT_SOURCE_DIR}/fixtures/mbc5-banking/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixture.cmake)
add_test(NAME mooneye_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyMooneye.cmake)
add_test(NAME mooneye_eligible_inventory
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyMooneye.cmake)
# Phase 8 sibling set: mbc2/mbc5 derivatives (D-23, D-24, D-26). Digest, inventory and pc-table modes.
add_test(NAME mooneye_mbc_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MODE=digest
    -DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyMooneyeMbc.cmake)
add_test(NAME mooneye_mbc_eligible_inventory
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MODE=inventory
    -DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyMooneyeMbc.cmake)
add_test(NAME mooneye_mbc_pc_table
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MODE=pc-table
    -DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc
    -DGBB_RUNNER_SOURCE=${PROJECT_SOURCE_DIR}/src/runner/main.c
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyMooneyeMbc.cmake)
# Negative control: a manifest whose first result_pc was changed must fail the pc-table check with exit code 1.
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/mooneye-mbc-tamper")
file(READ "${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc/manifest.json" GBB_MBC_MANIFEST_JSON)
string(JSON GBB_MBC_TAMPERED_JSON SET "${GBB_MBC_MANIFEST_JSON}" fixtures 0 result_pc "\"0x407f\"")
file(WRITE "${PROJECT_BINARY_DIR}/mooneye-mbc-tamper/manifest.json" "${GBB_MBC_TAMPERED_JSON}")
add_test(NAME mooneye_mbc_pc_table_tamper
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_MODE=pc-table;-DGBB_MANIFEST=${PROJECT_BINARY_DIR}/mooneye-mbc-tamper/manifest.json;-DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc;-DGBB_RUNNER_SOURCE=${PROJECT_SOURCE_DIR}/src/runner/main.c;-P;${PROJECT_SOURCE_DIR}/cmake/VerifyMooneyeMbc.cmake"
    -DGBB_EXPECT_CODE=1
    -DGBB_EXPECT_REGEX=pc-table-mismatch
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
# Negative control (D-28): an edited sibling manifest is refused with invalid-manifest and exactly exit code 2.
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/mooneye-mbc-unknown")
configure_file("${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc/manifest.json"
  "${PROJECT_BINARY_DIR}/mooneye-mbc-unknown/manifest.json" COPYONLY)
file(APPEND "${PROJECT_BINARY_DIR}/mooneye-mbc-unknown/manifest.json" " ")
add_test(NAME mooneye_mbc_unknown_manifest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--manifest;${PROJECT_BINARY_DIR}/mooneye-mbc-unknown/manifest.json;--suite"
    -DGBB_EXPECT_CODE=2
    -DGBB_EXPECT_REGEX=invalid-manifest
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

add_executable(test_diagnostics test_diagnostics.c)
target_link_libraries(test_diagnostics PRIVATE GabbaBoy::core)
target_compile_features(test_diagnostics PRIVATE c_std_17)
set_target_properties(test_diagnostics PROPERTIES C_EXTENSIONS OFF)
foreach(case zero exact short null canary)
  add_test(NAME diagnostics_${case} COMMAND test_diagnostics diagnostics_${case})
endforeach()

add_executable(test_runner test_runner.c)
target_link_libraries(test_runner PRIVATE gabbaboy_runner_support)
target_compile_features(test_runner PRIVATE c_std_17)
set_target_properties(test_runner PROPERTIES C_EXTENSIONS OFF)
add_test(NAME runner_help
  COMMAND ${CMAKE_COMMAND}
    -DGBB_RUNNER=$<TARGET_FILE:gabbaboy-runner>
    -P ${PROJECT_SOURCE_DIR}/tests/verify_runner_help.cmake)
foreach(case pass fail wrong_breakpoint timeout unsupported zero_eligible)
  add_test(NAME runner_${case} COMMAND test_runner runner_${case})
endforeach()
add_test(NAME runner_guest_failure
  COMMAND test_runner runner_guest_failure ${PROJECT_SOURCE_DIR}/fixtures/mooneye/daa.gb)
# D-29: a wrong mapper type byte must turn the admitted MBC5 derivative from pass into something else.
add_test(NAME mooneye_mbc_type_mutation
  COMMAND test_runner mooneye_mbc_type_mutation ${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc/mbc5_rom_512kb.gb)
set_tests_properties(mooneye_mbc_type_mutation PROPERTIES TIMEOUT 30)
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/runner-missing-fixture")
configure_file("${PROJECT_SOURCE_DIR}/fixtures/mooneye/manifest.json"
  "${PROJECT_BINARY_DIR}/runner-missing-fixture/manifest.json" COPYONLY)
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/runner-bad-digest")
configure_file("${PROJECT_SOURCE_DIR}/fixtures/mooneye/manifest.json"
  "${PROJECT_BINARY_DIR}/runner-bad-digest/manifest.json" COPYONLY)
string(REPEAT "A" 32768 GBB_INVALID_ROM_BYTES)
file(WRITE "${PROJECT_BINARY_DIR}/runner-bad-digest/daa.gb" "${GBB_INVALID_ROM_BYTES}")
add_test(NAME runner_missing_fixture
  COMMAND ${CMAKE_COMMAND}
    -DGBB_RUNNER=$<TARGET_FILE:gabbaboy-runner>
    -DGBB_MANIFEST=${PROJECT_BINARY_DIR}/runner-missing-fixture/manifest.json
    -DGBB_MODE=missing -P ${PROJECT_SOURCE_DIR}/tests/expect_runner_failure.cmake)
add_test(NAME runner_bad_digest
  COMMAND ${CMAKE_COMMAND}
    -DGBB_RUNNER=$<TARGET_FILE:gabbaboy-runner>
    -DGBB_MANIFEST=${PROJECT_BINARY_DIR}/runner-bad-digest/manifest.json
    -DGBB_MODE=digest -P ${PROJECT_SOURCE_DIR}/tests/expect_runner_failure.cmake)
file(WRITE "${PROJECT_BINARY_DIR}/runner-bad-manifest.json" "{}")
file(READ "${PROJECT_SOURCE_DIR}/fixtures/mooneye/manifest.json" GBB_TAMPERED_MANIFEST)
string(REPLACE "\"model\": \"DMG-CPU-B\"" "\"model\": \"CGB-E\"" GBB_TAMPERED_MANIFEST "${GBB_TAMPERED_MANIFEST}")
string(REPLACE "\"boot\": \"Skipped; bootless DMG-CPU-B profile starts at the cartridge entry point 0x0100.\""
  "\"boot\": \"Booted profile.\"" GBB_TAMPERED_MANIFEST "${GBB_TAMPERED_MANIFEST}")
file(WRITE "${PROJECT_BINARY_DIR}/runner-wrong-metadata.json" "${GBB_TAMPERED_MANIFEST}")
add_test(NAME runner_bad_manifest
  COMMAND ${CMAKE_COMMAND}
    -DGBB_RUNNER=$<TARGET_FILE:gabbaboy-runner>
    -DGBB_MANIFEST=${PROJECT_BINARY_DIR}/runner-bad-manifest.json
    -DGBB_MODE=manifest -P ${PROJECT_SOURCE_DIR}/tests/expect_runner_failure.cmake)
add_test(NAME runner_bad_metadata
  COMMAND ${CMAKE_COMMAND}
    -DGBB_RUNNER=$<TARGET_FILE:gabbaboy-runner>
    -DGBB_MANIFEST=${PROJECT_BINARY_DIR}/runner-wrong-metadata.json
    -DGBB_MODE=manifest -P ${PROJECT_SOURCE_DIR}/tests/expect_runner_failure.cmake)
add_test(NAME mooneye_required_suite
  COMMAND gabbaboy-runner --manifest ${PROJECT_SOURCE_DIR}/fixtures/mooneye/manifest.json --suite --receipt)
foreach(case daa tim00 tim00-div-trigger)
  add_test(NAME mooneye_case_${case}
    COMMAND gabbaboy-runner --manifest ${PROJECT_SOURCE_DIR}/fixtures/mooneye/manifest.json --case ${case} --receipt)
endforeach()
# Bound guest-runner test processes in host wall time as well as emulated half-dots.
# CTest terminates a stalled process and reports a failed case instead of hanging CI.
set_tests_properties(
  tracer_success tracer_failure tracer_unsupported tracer_timeout tracer_trace
  frame_composition_tracer joypad_gameplay_tracer tracer_smoke
  runner_pass runner_help runner_fail runner_wrong_breakpoint runner_timeout runner_unsupported
  runner_zero_eligible runner_guest_failure runner_missing_fixture runner_bad_digest
  runner_bad_manifest runner_bad_metadata
  concurrent_independent_instances
  mooneye_required_suite mooneye_case_daa mooneye_case_tim00 mooneye_case_tim00-div-trigger
  PROPERTIES TIMEOUT 30)
set_tests_properties(mooneye_case_daa PROPERTIES PASS_REGULAR_EXPRESSION
  "status=pass.*source_revision=31510e12eea6286d36eea060a6adde755e1067aa.*report_patch_sha256=c3679ab53b59da14a0f6af1fdd552316ba922762c3a91988f7f8ac4440516e5d.*fixture_origin=derived-headless-report-closure upstream_assertions=unchanged.*protocol_stage=callback-then-ld-b-b callback_result=pass callback_pc=0166 result_pc=409a")
set_tests_properties(mooneye_case_tim00 PROPERTIES PASS_REGULAR_EXPRESSION
  "status=pass.*source_revision=31510e12eea6286d36eea060a6adde755e1067aa.*report_patch_sha256=c3679ab53b59da14a0f6af1fdd552316ba922762c3a91988f7f8ac4440516e5d.*fixture_origin=derived-headless-report-closure upstream_assertions=unchanged.*protocol_stage=callback-then-ld-b-b callback_result=pass callback_pc=4000 result_pc=4327")
set_tests_properties(mooneye_case_tim00-div-trigger PROPERTIES PASS_REGULAR_EXPRESSION
  "status=pass.*source_revision=31510e12eea6286d36eea060a6adde755e1067aa.*report_patch_sha256=c3679ab53b59da14a0f6af1fdd552316ba922762c3a91988f7f8ac4440516e5d.*fixture_origin=derived-headless-report-closure upstream_assertions=unchanged.*protocol_stage=callback-then-ld-b-b callback_result=pass callback_pc=4000 result_pc=4327")
# Phase 8 sibling suite: the manifest's 15 derivatives, one CTest per alias (callback_pc and result_pc per Pitfall P13).
set(GBB_MBC_MANIFEST ${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc/manifest.json)
add_test(NAME mooneye_mbc_required_suite
  COMMAND gabbaboy-runner --manifest ${GBB_MBC_MANIFEST} --suite --receipt)
# The ASan/UBSan leg runs the 15 cases back to back in about 35 s (hosted Linux), so the suite bound is 120 s.
set_tests_properties(mooneye_mbc_required_suite PROPERTIES TIMEOUT 120 PASS_REGULAR_EXPRESSION
  "suite eligible=15 executed=15 status=pass.*suite categories mbc2=7/7 mbc5=8/8")
set(GBB_MBC_CASES
  mbc2_bits_ramg:01d7:407e mbc2_bits_romb:01c0:407e mbc2_bits_unused:018d:407e mbc2_ram:029c:4071
  mbc2_rom_512kb:0207:4071 mbc2_rom_1Mb:0207:4071 mbc2_rom_2Mb:0207:4071
  mbc5_rom_512kb:0216:4072 mbc5_rom_1Mb:0216:4072 mbc5_rom_2Mb:0216:4072 mbc5_rom_4Mb:0216:4072
  mbc5_rom_8Mb:0216:4072 mbc5_rom_16Mb:0216:4072 mbc5_rom_32Mb:0216:4072 mbc5_rom_64Mb:0216:4072)
foreach(entry IN LISTS GBB_MBC_CASES)
  string(REPLACE ":" ";" parts "${entry}")
  list(GET parts 0 alias)
  list(GET parts 1 callback_pc)
  list(GET parts 2 result_pc)
  add_test(NAME mooneye_mbc_case_${alias}
    COMMAND gabbaboy-runner --manifest ${GBB_MBC_MANIFEST} --case ${alias} --receipt)
  # Unsanitized wall time is at most 1.9 s per case (Plan 08-05); the hosted ASan/UBSan leg measured 15.4 s
  # for mbc2_bits_ramg under parallel load, so the bound is 60 s.
  set_tests_properties(mooneye_mbc_case_${alias} PROPERTIES TIMEOUT 60 PASS_REGULAR_EXPRESSION
    "status=pass.*source_revision=31510e12eea6286d36eea060a6adde755e1067aa.*fixture_origin=derived-headless-report-closure upstream_assertions=unchanged.*protocol_stage=callback-then-ld-b-b callback_result=pass callback_pc=${callback_pc} result_pc=${result_pc}")
endforeach()
set(GBB_TEST_SANITIZER_LINK_OPTIONS "")
if(GABBABOY_ENABLE_SANITIZERS)
  set(GBB_TEST_SANITIZER_LINK_OPTIONS "-fsanitize=address,undefined")
endif()
add_test(NAME preview_package_smoke
  COMMAND ${CMAKE_COMMAND}
    -DGBB_SOURCE_DIR=${PROJECT_SOURCE_DIR}
    -DGBB_BINARY_DIR=${PROJECT_BINARY_DIR}
    -DGBB_CMAKE_COMMAND=${CMAKE_COMMAND}
    -DGBB_GENERATOR=${CMAKE_GENERATOR}
    -DGBB_EXECUTABLE_SUFFIX=${CMAKE_EXECUTABLE_SUFFIX}
    -DGBB_SANITIZER_LINK_OPTIONS=${GBB_TEST_SANITIZER_LINK_OPTIONS}
    -DGBB_CONFIGURATION=$<CONFIG>
    -P ${PROJECT_SOURCE_DIR}/cmake/PreviewPackageSmoke.cmake)

if(GABBABOY_BUILD_PLAYER)
  add_subdirectory(player)
endif()

if(GBB_TEST_INSTALL_PREFIX AND EXISTS "${GBB_TEST_INSTALL_PREFIX}")
  get_filename_component(GBB_TEST_INSTALL_PREFIX_ABSOLUTE
    "${GBB_TEST_INSTALL_PREFIX}" ABSOLUTE BASE_DIR "${PROJECT_BINARY_DIR}")
  add_test(NAME installed_runner_smoke
    COMMAND ${CMAKE_COMMAND}
      -DGBB_INSTALL_PREFIX=${GBB_TEST_INSTALL_PREFIX_ABSOLUTE}
      -DGBB_EXECUTABLE_SUFFIX=${CMAKE_EXECUTABLE_SUFFIX}
      -DGBB_RUNNER_WORKDIR=${PROJECT_BINARY_DIR}/installed-runner-cwd
      -P ${PROJECT_SOURCE_DIR}/cmake/VerifyInstalledPackage.cmake)
  foreach(language IN ITEMS c cpp)
    add_test(NAME installed_consumer_${language}
      COMMAND ${CMAKE_COMMAND}
        -DGBB_INSTALL_PREFIX=${GBB_TEST_INSTALL_PREFIX_ABSOLUTE}
      -DGBB_CONSUMER_SOURCE=${PROJECT_SOURCE_DIR}/tests/consumers/${language}
      -DGBB_CONSUMER_BINARY=${PROJECT_BINARY_DIR}/consumer-${language}
      -DGBB_LANGUAGE=${language}
      -DGBB_EXECUTABLE_SUFFIX=${CMAKE_EXECUTABLE_SUFFIX}
      -DGBB_CONFIGURATION=$<CONFIG>
      -P ${PROJECT_SOURCE_DIR}/cmake/RunInstalledConsumer.cmake)
    add_test(NAME installed_consumer_phase2_${language}
      COMMAND ${CMAKE_COMMAND}
        -DGBB_INSTALL_PREFIX=${GBB_TEST_INSTALL_PREFIX_ABSOLUTE}
        -DGBB_CONSUMER_SOURCE=${PROJECT_SOURCE_DIR}/tests/consumers/${language}
        -DGBB_CONSUMER_BINARY=${PROJECT_BINARY_DIR}/consumer-phase2-${language}
        -DGBB_LANGUAGE=${language}
        -DGBB_EXECUTABLE_SUFFIX=${CMAKE_EXECUTABLE_SUFFIX}
        -DGBB_CONFIGURATION=$<CONFIG>
        -P ${PROJECT_SOURCE_DIR}/cmake/RunInstalledConsumer.cmake)
  endforeach()
endif()

# Libbet admission (GAME-01, gate G5). The verifier is stdlib-only Python run with -I; every
# negative control goes through expect_exit.cmake so it must exit with exactly the expected code
# and reason, never merely "non-zero".
find_package(Python3 COMPONENTS Interpreter REQUIRED)
set(GBB_LIBBET_VERIFIER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-libbet-admission.py")
set(GBB_LIBBET_MANIFEST "${PROJECT_SOURCE_DIR}/fixtures/libbet/manifest.json")
set(GBB_LIBBET_DIR "${PROJECT_BINARY_DIR}/libbet-admission")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
  "${GBB_LIBBET_MANIFEST}" "${PROJECT_SOURCE_DIR}/fixtures/libbet/libbet.gb")

# add_test with a verifier command line: GBB_CMD travels as a list, so semicolons are spelled
# with $<SEMICOLON> to survive the add_test argument split.
function(gbb_add_expect_exit_test name code regex)
  set(command "${Python3_EXECUTABLE}" -I "${GBB_LIBBET_VERIFIER}" ${ARGN})
  list(JOIN command "$<SEMICOLON>" joined)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${joined}"
      -DGBB_EXPECT_CODE=${code}
      "-DGBB_EXPECT_REGEX=${regex}"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT 30)
endfunction()

# Five mutated manifest copies of the committed manifest. Each differs by one fact; the ROM stays
# the committed one because the verifier resolves rom.path against the repository root.
file(MAKE_DIRECTORY "${GBB_LIBBET_DIR}")
file(READ "${GBB_LIBBET_MANIFEST}" GBB_LIBBET_JSON)
string(JSON GBB_LIBBET_ASSETS_EMPTY SET "${GBB_LIBBET_JSON}" rights embedded_assets "[]")
string(JSON GBB_LIBBET_ASSETS_MISSING REMOVE "${GBB_LIBBET_JSON}" rights embedded_assets 0)
string(JSON GBB_LIBBET_LICENCE_UNKNOWN SET "${GBB_LIBBET_JSON}" rights embedded_assets 0 licence "\"unknown\"")
string(JSON GBB_LIBBET_ROM_DIGEST GET "${GBB_LIBBET_JSON}" rom sha256)
string(SUBSTRING "${GBB_LIBBET_ROM_DIGEST}" 0 1 GBB_LIBBET_FIRST_DIGIT)
string(SUBSTRING "${GBB_LIBBET_ROM_DIGEST}" 1 -1 GBB_LIBBET_DIGEST_REST)
if(GBB_LIBBET_FIRST_DIGIT STREQUAL "0")
  set(GBB_LIBBET_FIRST_DIGIT "1")
else()
  set(GBB_LIBBET_FIRST_DIGIT "0")
endif()
string(JSON GBB_LIBBET_BAD_DIGEST SET "${GBB_LIBBET_JSON}" rom sha256
  "\"${GBB_LIBBET_FIRST_DIGIT}${GBB_LIBBET_DIGEST_REST}\"")
string(JSON GBB_LIBBET_BAD_HEADER SET "${GBB_LIBBET_JSON}" rom header cartridge_type 1)
foreach(mutation IN ITEMS ASSETS_EMPTY ASSETS_MISSING LICENCE_UNKNOWN BAD_DIGEST BAD_HEADER)
  string(TOLOWER "${mutation}" mutation_file)
  file(WRITE "${GBB_LIBBET_DIR}/${mutation_file}.json" "${GBB_LIBBET_${mutation}}\n")
endforeach()

gbb_add_expect_exit_test(libbet_admission_pass 0 "libbet admission verified" --manifest "${GBB_LIBBET_MANIFEST}")
gbb_add_expect_exit_test(libbet_admission_empty_assets 1 "embedded-assets-empty"
  --manifest "${GBB_LIBBET_DIR}/assets_empty.json")
gbb_add_expect_exit_test(libbet_admission_missing_record 1 "embedded-asset-missing"
  --manifest "${GBB_LIBBET_DIR}/assets_missing.json")
gbb_add_expect_exit_test(libbet_admission_unknown_licence 1 "embedded-asset-field-invalid"
  --manifest "${GBB_LIBBET_DIR}/licence_unknown.json")
gbb_add_expect_exit_test(libbet_admission_bad_digest 1 "rom-digest-mismatch"
  --manifest "${GBB_LIBBET_DIR}/bad_digest.json")
gbb_add_expect_exit_test(libbet_admission_bad_header 1 "rom-header-mismatch"
  --manifest "${GBB_LIBBET_DIR}/bad_header.json")
gbb_add_expect_exit_test(libbet_admission_self_test 0 "libbet admission self-test passed" --self-test)
gbb_add_expect_exit_test(libbet_notice 0 "libbet notices and attributes verified"
  --manifest "${GBB_LIBBET_MANIFEST}" --check-notices)

# Redistribution guard: the third-party ROM is a repository test fixture only. Install the build
# into a scratch prefix (distinct from GBB_TEST_INSTALL_PREFIX) and scan it by digest and name.
# The negative control hides the ROM under a neutral name, proving the digest scan itself.
set(GBB_LIBBET_INSTALL_CHECK "${PROJECT_BINARY_DIR}/libbet-install-check")
set(GBB_LIBBET_SCAN_SELFTEST "${PROJECT_BINARY_DIR}/libbet-scan-selftest")
file(MAKE_DIRECTORY "${GBB_LIBBET_SCAN_SELFTEST}/share")
file(COPY_FILE "${PROJECT_SOURCE_DIR}/fixtures/libbet/libbet.gb"
  "${GBB_LIBBET_SCAN_SELFTEST}/share/payload.bin")
add_test(NAME libbet_install_tree
  COMMAND ${CMAKE_COMMAND} --install ${PROJECT_BINARY_DIR} --prefix ${GBB_LIBBET_INSTALL_CHECK})
set_tests_properties(libbet_install_tree PROPERTIES FIXTURES_SETUP libbet_install TIMEOUT 120)
gbb_add_expect_exit_test(libbet_not_installed 0 "libbet absent from scanned tree files=[1-9]"
  --scan-dir "${GBB_LIBBET_INSTALL_CHECK}")
set_tests_properties(libbet_not_installed PROPERTIES FIXTURES_REQUIRED libbet_install)
gbb_add_expect_exit_test(libbet_not_installed_selftest 1 "libbet-installed: share/payload.bin"
  --scan-dir "${GBB_LIBBET_SCAN_SELFTEST}")

# Sibling Mooneye MBC ROM redistribution guard (D-31, D-32). The 15 derivatives, including the
# 4 MiB and 8 MiB ROMs, are repository fixtures only. cmake/ScanForbiddenFixtures.cmake scans the
# same install tree by name and digest and asserts the exact installed fixture directories. The
# three self-tests prove the scan can fail: a renamed ROM, an empty tree and an extra directory.
set(GBB_MBC_SCAN_SCRIPT "${PROJECT_SOURCE_DIR}/cmake/ScanForbiddenFixtures.cmake")
set(GBB_MBC_SCAN_MANIFEST "${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc/manifest.json")
set(GBB_MBC_SCAN_DIRS "tracer|visible-demo|mbc1-continuation")
set(GBB_MBC_SCAN_SELFTEST "${PROJECT_BINARY_DIR}/mooneye-mbc-scan-selftest")
set(GBB_MBC_SCAN_EMPTY "${PROJECT_BINARY_DIR}/mooneye-mbc-scan-empty")
set(GBB_MBC_DIRS_SELFTEST "${PROJECT_BINARY_DIR}/mooneye-mbc-dirs-selftest")
file(MAKE_DIRECTORY "${GBB_MBC_SCAN_SELFTEST}/share" "${GBB_MBC_SCAN_EMPTY}")
file(COPY_FILE "${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc/mbc5_rom_512kb.gb"
  "${GBB_MBC_SCAN_SELFTEST}/share/payload.bin")
foreach(dir IN ITEMS tracer visible-demo mbc1-continuation extra)
  file(WRITE "${GBB_MBC_DIRS_SELFTEST}/share/gabbaboy/fixtures/${dir}/marker.txt" "marker\n")
endforeach()
function(gbb_add_mbc_scan_test name code regex scan_dir)
  set(command "${CMAKE_COMMAND}" "-DGBB_SCAN_DIR=${scan_dir}"
    "-DGBB_FORBIDDEN_MANIFEST=${GBB_MBC_SCAN_MANIFEST}" ${ARGN} -P "${GBB_MBC_SCAN_SCRIPT}")
  list(JOIN command "$<SEMICOLON>" joined)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${joined}"
      -DGBB_EXPECT_CODE=${code}
      "-DGBB_EXPECT_REGEX=${regex}"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT 60)
endfunction()
gbb_add_mbc_scan_test(mooneye_mbc_not_installed 0 "mooneye-mbc absent from scanned tree files=[1-9]"
  "${GBB_LIBBET_INSTALL_CHECK}" "-DGBB_EXPECT_FIXTURE_DIRS=${GBB_MBC_SCAN_DIRS}")
set_tests_properties(mooneye_mbc_not_installed PROPERTIES FIXTURES_REQUIRED libbet_install)
gbb_add_mbc_scan_test(mooneye_mbc_not_installed_selftest 1 "mooneye-installed: share/payload.bin"
  "${GBB_MBC_SCAN_SELFTEST}")
gbb_add_mbc_scan_test(mooneye_mbc_not_installed_empty 1 "scan-dir-empty"
  "${GBB_MBC_SCAN_EMPTY}")
gbb_add_mbc_scan_test(mooneye_mbc_fixture_dirs_selftest 1 "fixture-dirs-mismatch"
  "${GBB_MBC_DIRS_SELFTEST}" "-DGBB_EXPECT_FIXTURE_DIRS=${GBB_MBC_SCAN_DIRS}")

# EVID-02 baseline comparator self-tests (D-30, D-31, D-34). Each test runs cmake/VerifyDmgBaseline.cmake
# on committed synthetic fixtures (or a generated variant of them) and asserts the exact exit code
# and failure token through expect_exit.cmake; nothing here touches the real ledger.
set(GBB_BASELINE_SCRIPT "${PROJECT_SOURCE_DIR}/cmake/VerifyDmgBaseline.cmake")
set(GBB_BASELINE_SELFTEST "${PROJECT_SOURCE_DIR}/tests/baseline/selftest")
set(GBB_BASELINE_DIR "${PROJECT_BINARY_DIR}/baseline-selftest")
file(MAKE_DIRECTORY "${GBB_BASELINE_DIR}")

function(gbb_add_baseline_test name code regex)
  set(command "${CMAKE_COMMAND}" "-DGBB_SOURCE_DIR=${PROJECT_SOURCE_DIR}" ${ARGN} -P "${GBB_BASELINE_SCRIPT}")
  list(JOIN command "$<SEMICOLON>" joined)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${joined}"
      -DGBB_EXPECT_CODE=${code}
      "-DGBB_EXPECT_REGEX=${regex}"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT 30)
endfunction()

file(READ "${GBB_BASELINE_SELFTEST}/observed.txt" GBB_BASELINE_OBSERVED)
file(READ "${GBB_BASELINE_SELFTEST}/ledger.txt" GBB_BASELINE_LEDGER)
file(READ "${GBB_BASELINE_SELFTEST}/CHANGES.md" GBB_BASELINE_CHANGES_ROW)
# The committed CHANGES fixture carries one row for the recorded-change variant; every other test
# compares against the same table with that row removed.
string(ASCII 10 GBB_NL)
string(REGEX REPLACE "${GBB_NL}[|] acceptance[^${GBB_NL}]*${GBB_NL}?" "${GBB_NL}"
  GBB_BASELINE_CHANGES_EMPTY "${GBB_BASELINE_CHANGES_ROW}")
file(WRITE "${GBB_BASELINE_DIR}/changes_empty.md" "${GBB_BASELINE_CHANGES_EMPTY}")

gbb_add_baseline_test(dmg_baseline_selftest_pass 0 "baseline status=pass"
  -DGBB_MODE=check
  "-DGBB_OBSERVED=${GBB_BASELINE_SELFTEST}/observed.txt"
  "-DGBB_LEDGER=${GBB_BASELINE_SELFTEST}/ledger.txt"
  "-DGBB_CHANGES=${GBB_BASELINE_DIR}/changes_empty.md")

# One generated variant per failure category. Each differs from the committed synthetic fixtures by
# exactly one fact, so the category it names is the only thing that can make the comparator fail.
string(ASCII 9 GBB_TAB)
set(GBB_PCM_OLD "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
set(GBB_PCM_NEW "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
set(GBB_PCM_OTHER "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc")
set(GBB_BASELINE_ROW_TAIL "| synthetic reason | regression fixture (self-test only) | self-test |\n")

function(gbb_baseline_variant name ledger observed changes)
  file(WRITE "${GBB_BASELINE_DIR}/${name}.ledger.txt" "${ledger}")
  file(WRITE "${GBB_BASELINE_DIR}/${name}.observed.txt" "${observed}")
  file(WRITE "${GBB_BASELINE_DIR}/${name}.changes.md" "${changes}")
endfunction()

function(gbb_add_baseline_variant_test name code regex)
  gbb_add_baseline_test(dmg_baseline_${name} ${code} "${regex}"
    -DGBB_MODE=check
    "-DGBB_OBSERVED=${GBB_BASELINE_DIR}/${name}.observed.txt"
    "-DGBB_LEDGER=${GBB_BASELINE_DIR}/${name}.ledger.txt"
    "-DGBB_CHANGES=${GBB_BASELINE_DIR}/${name}.changes.md")
endfunction()

set(GBB_OBS "${GBB_BASELINE_OBSERVED}")
set(GBB_LED "${GBB_BASELINE_LEDGER}")
set(GBB_CHG "${GBB_BASELINE_CHANGES_EMPTY}")
string(REPLACE "${GBB_PCM_OLD}" "${GBB_PCM_NEW}" GBB_OBS_CHANGED "${GBB_OBS}")
string(REPLACE "${GBB_PCM_OLD}" "${GBB_PCM_NEW}" GBB_LED_CHANGED "${GBB_LED}")

# Observation drift: a digest changed, a ledger key vanished, an unknown key appeared, an inventory name left.
gbb_baseline_variant(modified "${GBB_LED}" "${GBB_OBS_CHANGED}" "${GBB_CHG}")
string(REPLACE "mooneye.daa.frame_generation${GBB_TAB}12\n" "" GBB_OBS_MISSING "${GBB_OBS}")
gbb_baseline_variant(missing "${GBB_LED}" "${GBB_OBS_MISSING}" "${GBB_CHG}")
gbb_baseline_variant(extra "${GBB_LED}" "${GBB_OBS}acceptance.libbet.unexpected${GBB_TAB}1\n" "${GBB_CHG}")
string(REPLACE "inventory.core.beta_test${GBB_TAB}frozen\n" "" GBB_OBS_REMOVED "${GBB_OBS}")
gbb_baseline_variant(inventory_removed "${GBB_LED}" "${GBB_OBS_REMOVED}" "${GBB_CHG}")

# Approved-change protocol: the same ledger edit fails without a CHANGES row and passes with it.
gbb_baseline_variant(changes_unrecorded "${GBB_LED_CHANGED}" "${GBB_OBS_CHANGED}" "${GBB_CHG}")
gbb_baseline_variant(changes_recorded "${GBB_LED_CHANGED}" "${GBB_OBS_CHANGED}" "${GBB_BASELINE_CHANGES_ROW}")
gbb_baseline_variant(changes_noop "${GBB_LED}" "${GBB_OBS}"
  "${GBB_CHG}| acceptance.libbet.pcm_sha256 | ${GBB_PCM_OLD} | ${GBB_PCM_OLD} ${GBB_BASELINE_ROW_TAIL}")
gbb_baseline_variant(changes_inconsistent "${GBB_LED}" "${GBB_OBS}"
  "${GBB_CHG}| acceptance.libbet.pcm_sha256 | ${GBB_PCM_OTHER} | ${GBB_PCM_NEW} ${GBB_BASELINE_ROW_TAIL}")

# Ledger shape: ordering, duplicate key, empty ledger, empty section, empty observations, bad line, bad header.
string(REPLACE
  "inventory.core.alpha_test${GBB_TAB}frozen\ninventory.core.beta_test${GBB_TAB}frozen\n"
  "inventory.core.beta_test${GBB_TAB}frozen\ninventory.core.alpha_test${GBB_TAB}frozen\n"
  GBB_LED_UNSORTED "${GBB_LED}")
gbb_baseline_variant(unsorted "${GBB_LED_UNSORTED}" "${GBB_OBS}" "${GBB_CHG}")
string(REPLACE "bench.tracer.workload${GBB_TAB}original-wram-tracer-1m-half-dots-v1\n"
  "bench.tracer.workload${GBB_TAB}original-wram-tracer-1m-half-dots-v1\nbench.tracer.workload${GBB_TAB}original-wram-tracer-1m-half-dots-v1\n"
  GBB_LED_DUPLICATE "${GBB_LED}")
gbb_baseline_variant(duplicate_key "${GBB_LED_DUPLICATE}" "${GBB_OBS}" "${GBB_CHG}")
gbb_baseline_variant(empty "" "${GBB_OBS}" "${GBB_CHG}")
string(REGEX REPLACE "mooneye[.][^${GBB_NL}]*${GBB_NL}" "" GBB_LED_NO_MOONEYE "${GBB_LED}")
gbb_baseline_variant(empty_section "${GBB_LED_NO_MOONEYE}" "${GBB_OBS}" "${GBB_CHG}")
gbb_baseline_variant(empty_observations "${GBB_LED}" "" "${GBB_CHG}")
string(REPLACE "bench.tracer.workload${GBB_TAB}" "bench.tracer${GBB_TAB}workload${GBB_TAB}" GBB_LED_MALFORMED "${GBB_LED}")
gbb_baseline_variant(malformed_line "${GBB_LED_MALFORMED}" "${GBB_OBS}" "${GBB_CHG}")
string(REPLACE "0123456789abcdef0123456789abcdef01234567" "0123456789abcdef0123456789abcdef0123456"
  GBB_LED_HEADER "${GBB_LED}")
gbb_baseline_variant(header_invalid "${GBB_LED_HEADER}" "${GBB_OBS}" "${GBB_CHG}")

gbb_add_baseline_variant_test(changes_recorded 0 "baseline status=pass")
gbb_add_baseline_variant_test(modified 1 "acceptance=fail.*modified")
gbb_add_baseline_variant_test(missing 1 "mooneye=fail.*missing")
gbb_add_baseline_variant_test(extra 1 "acceptance=fail.*extra")
gbb_add_baseline_variant_test(inventory_removed 1 "inventory=fail.*removed")
gbb_add_baseline_variant_test(changes_unrecorded 1 "unrecorded-change")
gbb_add_baseline_variant_test(unsorted 1 "unsorted-ledger")
gbb_add_baseline_variant_test(duplicate_key 1 "duplicate-key")
gbb_add_baseline_variant_test(empty 1 "empty-ledger")
gbb_add_baseline_variant_test(changes_noop 1 "changes-noop")
gbb_add_baseline_variant_test(changes_inconsistent 1 "changes-inconsistent")
gbb_add_baseline_variant_test(empty_section 1 "empty-section")
gbb_add_baseline_variant_test(empty_observations 1 "empty-observations")
gbb_add_baseline_variant_test(malformed_line 1 "malformed-line")
gbb_add_baseline_variant_test(header_invalid 1 "header-invalid")

# JUnit inventory checks run on a synthetic report: every frozen core name must appear as a testcase
# with no skipped, failure or error child. Plan 07-15 applies the same mode to the real CI reports.
file(READ "${GBB_BASELINE_SELFTEST}/junit.xml" GBB_JUNIT)
set(GBB_BETA_CASE "<testcase name=\"beta_test\" classname=\"beta_test\" time=\"0.01\" status=\"run\"/>")
string(REPLACE "  ${GBB_BETA_CASE}\n" "" GBB_JUNIT_MISSING "${GBB_JUNIT}")
string(REPLACE "${GBB_BETA_CASE}"
  "<testcase name=\"beta_test\" classname=\"beta_test\" time=\"0.01\" status=\"notrun\"><skipped/></testcase>"
  GBB_JUNIT_SKIPPED "${GBB_JUNIT}")
string(REPLACE "${GBB_BETA_CASE}"
  "<testcase name=\"beta_test\" classname=\"beta_test\" time=\"0.01\" status=\"fail\"><failure message=\"x\"/></testcase>"
  GBB_JUNIT_FAILED "${GBB_JUNIT}")
file(WRITE "${GBB_BASELINE_DIR}/junit_missing.xml" "${GBB_JUNIT_MISSING}")
file(WRITE "${GBB_BASELINE_DIR}/junit_skipped.xml" "${GBB_JUNIT_SKIPPED}")
file(WRITE "${GBB_BASELINE_DIR}/junit_failed.xml" "${GBB_JUNIT_FAILED}")

function(gbb_add_baseline_junit_test name code regex report)
  gbb_add_baseline_test(dmg_baseline_${name} ${code} "${regex}"
    -DGBB_MODE=junit -DGBB_INVENTORY=core
    "-DGBB_LEDGER=${GBB_BASELINE_SELFTEST}/ledger.txt"
    "-DGBB_JUNIT=${report}")
endfunction()
gbb_add_baseline_junit_test(junit_pass 0 "baseline junit=ok" "${GBB_BASELINE_SELFTEST}/junit.xml")
gbb_add_baseline_junit_test(junit_missing 1 "junit-missing" "${GBB_BASELINE_DIR}/junit_missing.xml")
gbb_add_baseline_junit_test(junit_skipped 1 "junit-skipped" "${GBB_BASELINE_DIR}/junit_skipped.xml")
gbb_add_baseline_junit_test(junit_failed 1 "junit-failed" "${GBB_BASELINE_DIR}/junit_failed.xml")

# The live EVID-02 check (D-31, D-33): recomputes every observation from this build and compares it
# with the frozen tests/baseline/dmg-cpu-b-v1.txt. One ledger serves every OS, so the same test and
# the same expected line run on Linux, macOS and Windows.
add_test(NAME dmg_baseline
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MODE=check
    -DGBB_SOURCE_DIR=${PROJECT_SOURCE_DIR}
    -DGBB_RUNNER=$<TARGET_FILE:gabbaboy-runner>
    -DGBB_MEASURE=$<TARGET_FILE:measure_core>
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyDmgBaseline.cmake)
set_tests_properties(dmg_baseline PROPERTIES TIMEOUT 300
  PASS_REGULAR_EXPRESSION "baseline status=pass")

# include(), not add_subdirectory(): ExpectedTests.cmake reads this directory's TESTS property only.
include(${CMAKE_CURRENT_LIST_DIR}/acceptance/CMakeLists.txt)

gabbaboy_verify_registered_tests()
