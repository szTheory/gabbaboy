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
set_target_properties(gabbaboy_core PROPERTIES EXPORT_NAME core)

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
  add_subdirectory(tests)
endif()
