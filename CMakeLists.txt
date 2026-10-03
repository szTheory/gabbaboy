cmake_minimum_required(VERSION 3.25)
project(GabbaBoy VERSION 0.1.0 LANGUAGES C)

include(CTest)
include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

add_library(gabbaboy_core STATIC src/core/gabbaboy.c)
add_library(GabbaBoy::core ALIAS gabbaboy_core)
target_include_directories(gabbaboy_core PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>)
target_compile_features(gabbaboy_core PUBLIC c_std_17)
set_target_properties(gabbaboy_core PROPERTIES C_EXTENSIONS OFF)

add_executable(gabbaboy-runner src/runner/main.c)
target_link_libraries(gabbaboy-runner PRIVATE GabbaBoy::core)
target_compile_features(gabbaboy-runner PRIVATE c_std_17)
set_target_properties(gabbaboy-runner PROPERTIES C_EXTENSIONS OFF)

set(GABBABOY_CMAKE_INSTALL_DIR "${CMAKE_INSTALL_LIBDIR}/cmake/GabbaBoy")
configure_package_config_file(
  cmake/GabbaBoyConfig.cmake.in
  "${CMAKE_CURRENT_BINARY_DIR}/GabbaBoyConfig.cmake"
  INSTALL_DESTINATION "${GABBABOY_CMAKE_INSTALL_DIR}")
write_basic_package_version_file(
  "${CMAKE_CURRENT_BINARY_DIR}/GabbaBoyConfigVersion.cmake"
  VERSION "${PROJECT_VERSION}"
  COMPATIBILITY SameMajorVersion)

install(TARGETS gabbaboy_core
  EXPORT GabbaBoyTargets
  ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}")
install(DIRECTORY include/gabbaboy DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}")
install(TARGETS gabbaboy-runner RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}")
install(FILES
  fixtures/tracer/tracer.gb
  fixtures/tracer/manifest.json
  fixtures/tracer/LICENSE.txt
  DESTINATION "${CMAKE_INSTALL_DATADIR}/gabbaboy/fixtures/tracer")
install(EXPORT GabbaBoyTargets
  FILE GabbaBoyTargets.cmake
  NAMESPACE GabbaBoy::
  DESTINATION "${GABBABOY_CMAKE_INSTALL_DIR}")
install(FILES
  "${CMAKE_CURRENT_BINARY_DIR}/GabbaBoyConfig.cmake"
  "${CMAKE_CURRENT_BINARY_DIR}/GabbaBoyConfigVersion.cmake"
  DESTINATION "${GABBABOY_CMAKE_INSTALL_DIR}")

if(BUILD_TESTING)
  add_executable(test_api tests/test_api.c)
  target_link_libraries(test_api PRIVATE GabbaBoy::core)
  target_compile_features(test_api PRIVATE c_std_17)
  set_target_properties(test_api PROPERTIES C_EXTENSIONS OFF)
  add_test(NAME instance_lifecycle COMMAND test_api instance_lifecycle ${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
  add_test(NAME independent_instances COMMAND test_api independent_instances ${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
  add_test(NAME run_bounds COMMAND test_api run_bounds ${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
  add_test(NAME trace_capacity COMMAND test_api trace_capacity ${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
  add_executable(test_loader tests/test_loader.c)
  target_link_libraries(test_loader PRIVATE GabbaBoy::core)
  target_compile_features(test_loader PRIVATE c_std_17)
  set_target_properties(test_loader PROPERTIES C_EXTENSIONS OFF)
  foreach(case truncated oversized invalid_header unsupported_cartridge unsupported_rom_size unsupported_ram_size length_mismatch excess_actual null_arguments non_destructive)
    add_test(NAME loader_${case} COMMAND test_loader ${case} ${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
  endforeach()
  add_executable(test_tracer tests/test_tracer.c)
  target_link_libraries(test_tracer PRIVATE GabbaBoy::core)
  target_compile_features(test_tracer PRIVATE c_std_17)
  set_target_properties(test_tracer PROPERTIES C_EXTENSIONS OFF)
  foreach(case success failure unsupported timeout trace)
    add_test(NAME tracer_${case} COMMAND test_tracer ${case} ${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
  endforeach()
  add_test(NAME tracer_smoke COMMAND gabbaboy-runner ${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
  add_test(NAME fixture_digest
    COMMAND ${CMAKE_COMMAND}
      -DROM=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tracer/tracer.gb
      -DMANIFEST=${CMAKE_CURRENT_SOURCE_DIR}/fixtures/tracer/manifest.json
      -P ${CMAKE_CURRENT_SOURCE_DIR}/cmake/VerifyFixture.cmake)
endif()
