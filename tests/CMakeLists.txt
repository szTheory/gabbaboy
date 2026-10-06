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
foreach(case wram_guest echo_hram absent_cart preflight)
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
foreach(case call_stack conditional_budget base_matrix illegal_lockup flags_edges timed_access cb_wram cb_budget cb_matrix cb_flags_edges cb_timed_access)
  add_test(NAME cpu_${case} COMMAND test_cpu ${case})
endforeach()

add_executable(test_control test_control.c)
target_link_libraries(test_control PRIVATE GabbaBoy::core)
target_compile_features(test_control PRIVATE c_std_17)
set_target_properties(test_control PROPERTIES C_EXTENSIONS OFF)
add_test(NAME interrupt_entry COMMAND test_control interrupt_entry)
add_test(NAME interrupt_budget COMMAND test_control interrupt_budget)
foreach(case interrupt_ei_delay interrupt_priority halt_idle halt_bug stop_wait reset_profile reset_lockup)
  add_test(NAME ${case} COMMAND test_control ${case})
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
add_test(NAME tracer_smoke COMMAND gabbaboy-runner ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DROM=${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb
    -DMANIFEST=${PROJECT_SOURCE_DIR}/fixtures/tracer/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixture.cmake)
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
  endforeach()
endif()

gabbaboy_verify_registered_tests()
