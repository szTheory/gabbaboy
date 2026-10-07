set(GBB_TEST_INSTALL_PREFIX "" CACHE PATH "Relocated install prefix used by installed-package smoke tests")
include(${PROJECT_SOURCE_DIR}/cmake/ExpectedTests.cmake)

add_executable(test_api test_api.c)
target_link_libraries(test_api PRIVATE GabbaBoy::core)
target_compile_features(test_api PRIVATE c_std_17)
set_target_properties(test_api PROPERTIES C_EXTENSIONS OFF)
add_test(NAME instance_lifecycle COMMAND test_api instance_lifecycle ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME independent_instances COMMAND test_api independent_instances ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME run_bounds COMMAND test_api run_bounds ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME trace_capacity COMMAND test_api trace_capacity ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME illegal_lockup_api COMMAND test_api illegal_lockup ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)

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
foreach(case event_stop_wake event_boundary event_queue_order event_queue_atomic event_partition
             event_deadline_inside event_external_serial_edges event_time_overflow run_output_capacity)
  add_test(NAME ${case} COMMAND test_events ${case})
endforeach()

add_executable(test_loader test_loader.c)
target_link_libraries(test_loader PRIVATE GabbaBoy::core)
target_compile_features(test_loader PRIVATE c_std_17)
set_target_properties(test_loader PROPERTIES C_EXTENSIONS OFF)
foreach(case truncated oversized invalid_header unsupported_cartridge unsupported_rom_size unsupported_declared_size unsupported_ram_size length_mismatch excess_actual null_arguments non_destructive)
  add_test(NAME loader_${case} COMMAND test_loader ${case} ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
endforeach()

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
             ppu_timing_partition)
  add_test(NAME ${case} COMMAND test_ppu ${case})
endforeach()

add_executable(test_dma test_dma.c)
target_link_libraries(test_dma PRIVATE GabbaBoy::core)
target_compile_features(test_dma PRIVATE c_std_17)
set_target_properties(test_dma PROPERTIES C_EXTENSIONS OFF)
foreach(case dma_progress dma_restart dma_source_mapping dma_hram dma_interrupt_stack dma_partition)
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
add_test(NAME mooneye_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyMooneye.cmake)
add_test(NAME mooneye_eligible_inventory
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyMooneye.cmake)

add_executable(test_diagnostics test_diagnostics.c)
target_link_libraries(test_diagnostics PRIVATE GabbaBoy::core)
target_compile_features(test_diagnostics PRIVATE c_std_17)
set_target_properties(test_diagnostics PROPERTIES C_EXTENSIONS OFF)
foreach(case zero exact short null canary)
  add_test(NAME diagnostics_${case} COMMAND test_diagnostics diagnostics_${case})
endforeach()

add_executable(test_runner test_runner.c)
target_link_libraries(test_runner PRIVATE GabbaBoy::core)
target_compile_features(test_runner PRIVATE c_std_17)
set_target_properties(test_runner PROPERTIES C_EXTENSIONS OFF)
foreach(case pass fail wrong_breakpoint timeout unsupported zero_eligible)
  add_test(NAME runner_${case} COMMAND test_runner runner_${case})
endforeach()
add_test(NAME runner_guest_failure
  COMMAND test_runner runner_guest_failure ${PROJECT_SOURCE_DIR}/fixtures/mooneye/daa.gb)
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
set_tests_properties(mooneye_case_daa PROPERTIES PASS_REGULAR_EXPRESSION
  "status=pass.*source_revision=31510e12eea6286d36eea060a6adde755e1067aa.*report_patch_sha256=c3679ab53b59da14a0f6af1fdd552316ba922762c3a91988f7f8ac4440516e5d.*fixture_origin=derived-headless-report-closure upstream_assertions=unchanged.*protocol_stage=callback-then-ld-b-b callback_result=pass callback_pc=0166 result_pc=409a")
set_tests_properties(mooneye_case_tim00 PROPERTIES PASS_REGULAR_EXPRESSION
  "status=pass.*source_revision=31510e12eea6286d36eea060a6adde755e1067aa.*report_patch_sha256=c3679ab53b59da14a0f6af1fdd552316ba922762c3a91988f7f8ac4440516e5d.*fixture_origin=derived-headless-report-closure upstream_assertions=unchanged.*protocol_stage=callback-then-ld-b-b callback_result=pass callback_pc=4000 result_pc=4327")
set_tests_properties(mooneye_case_tim00-div-trigger PROPERTIES PASS_REGULAR_EXPRESSION
  "status=pass.*source_revision=31510e12eea6286d36eea060a6adde755e1067aa.*report_patch_sha256=c3679ab53b59da14a0f6af1fdd552316ba922762c3a91988f7f8ac4440516e5d.*fixture_origin=derived-headless-report-closure upstream_assertions=unchanged.*protocol_stage=callback-then-ld-b-b callback_result=pass callback_pc=4000 result_pc=4327")
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

gabbaboy_verify_registered_tests()
