cmake_minimum_required(VERSION 3.25)
project(GabbaBoy VERSION 0.1.0 LANGUAGES C)

include(CTest)

add_library(gabbaboy_core STATIC src/core/gabbaboy.c)
add_library(GabbaBoy::core ALIAS gabbaboy_core)
target_include_directories(gabbaboy_core PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
target_compile_features(gabbaboy_core PUBLIC c_std_17)
set_target_properties(gabbaboy_core PROPERTIES C_EXTENSIONS OFF)

add_executable(gabbaboy-runner src/runner/main.c)
target_link_libraries(gabbaboy-runner PRIVATE GabbaBoy::core)
target_compile_features(gabbaboy-runner PRIVATE c_std_17)
set_target_properties(gabbaboy-runner PROPERTIES C_EXTENSIONS OFF)

if(BUILD_TESTING)
  add_executable(test_api tests/test_api.c)
  target_link_libraries(test_api PRIVATE GabbaBoy::core)
  target_compile_features(test_api PRIVATE c_std_17)
  set_target_properties(test_api PROPERTIES C_EXTENSIONS OFF)
  add_test(NAME instance_lifecycle COMMAND test_api instance_lifecycle ${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
  add_test(NAME independent_instances COMMAND test_api independent_instances ${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
  add_test(NAME run_bounds COMMAND test_api run_bounds ${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
  add_test(NAME trace_capacity COMMAND test_api trace_capacity ${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
  add_test(NAME tracer_smoke COMMAND gabbaboy-runner ${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
  add_test(NAME fixture_digest
    COMMAND ${CMAKE_COMMAND}
      -DROM=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tracer/tracer.gb
      -DMANIFEST=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tracer/manifest.json
      -P ${CMAKE_CURRENT_SOURCE_DIR}/cmake/VerifyFixture.cmake)
endif()
