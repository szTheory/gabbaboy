cmake_minimum_required(VERSION 3.25)
project(GabbaBoy VERSION 0.1.2 LANGUAGES C) # x-release-please-version

option(GABBABOY_ENABLE_SANITIZERS
  "Enable AddressSanitizer and UndefinedBehaviorSanitizer on Linux" OFF)
if(GABBABOY_ENABLE_SANITIZERS)
  if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
    message(FATAL_ERROR "GABBABOY_ENABLE_SANITIZERS is supported only on Linux")
  endif()
  if(NOT CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    message(FATAL_ERROR "GABBABOY_ENABLE_SANITIZERS requires GCC or Clang")
  endif()
  add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer)
  add_link_options(-fsanitize=address,undefined)
endif()

option(GABBABOY_BUILD_PLAYER "Build the optional SDL3 player" OFF)

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

# Shared acceptance library (runner and player smoke). Internal: never installed or exported.
add_library(gabbaboy_accept STATIC
  src/accept/sha256.c
  src/accept/input_script.c
  src/accept/stepper.c
  src/accept/predicate.c)
target_include_directories(gabbaboy_accept PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/src/accept")
target_link_libraries(gabbaboy_accept PUBLIC GabbaBoy::core)
target_compile_features(gabbaboy_accept PUBLIC c_std_17)
set_target_properties(gabbaboy_accept PROPERTIES C_EXTENSIONS OFF)

add_executable(gabbaboy-runner src/runner/main.c)
target_link_libraries(gabbaboy-runner PRIVATE gabbaboy_accept)
target_compile_features(gabbaboy-runner PRIVATE c_std_17)
set_target_properties(gabbaboy-runner PROPERTIES C_EXTENSIONS OFF)

execute_process(COMMAND git rev-parse --verify HEAD
  WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
  OUTPUT_VARIABLE GABBABOY_BUILD_REVISION OUTPUT_STRIP_TRAILING_WHITESPACE
  RESULT_VARIABLE GABBABOY_GIT_RESULT ERROR_QUIET)
string(LENGTH "${GABBABOY_BUILD_REVISION}" GABBABOY_BUILD_REVISION_LENGTH)
if(NOT GABBABOY_GIT_RESULT EQUAL 0 OR
   NOT GABBABOY_BUILD_REVISION MATCHES "^[0-9a-fA-F]+$" OR
   GABBABOY_BUILD_REVISION_LENGTH LESS 40 OR GABBABOY_BUILD_REVISION_LENGTH GREATER 64)
  set(GABBABOY_BUILD_REVISION "unknown")
  set(GABBABOY_BUILD_QUALIFIED 0)
else()
  execute_process(COMMAND git diff --quiet HEAD -- CMakeLists.txt include/gabbaboy/gabbaboy.h src/core/gabbaboy.c src/runner/main.c
    src/accept/gbb_accept.h src/accept/sha256.c src/accept/input_script.c src/accept/stepper.c src/accept/predicate.c
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}" RESULT_VARIABLE GABBABOY_SOURCE_DIRTY ERROR_QUIET)
  if(GABBABOY_SOURCE_DIRTY EQUAL 0)
    set(GABBABOY_BUILD_QUALIFIED 1)
  else()
    set(GABBABOY_BUILD_QUALIFIED 0)
  endif()
endif()
target_compile_definitions(gabbaboy_core PRIVATE
  GBB_BUILD_REVISION="${GABBABOY_BUILD_REVISION}"
  GBB_BUILD_QUALIFIED=${GABBABOY_BUILD_QUALIFIED})
target_compile_definitions(gabbaboy-runner PRIVATE
  GBB_BUILD_REVISION="${GABBABOY_BUILD_REVISION}"
  GBB_BUILD_QUALIFIED=${GABBABOY_BUILD_QUALIFIED})

if(GABBABOY_BUILD_PLAYER)
  find_package(SDL3 3.4.18 EXACT CONFIG REQUIRED)

  add_library(gabbaboy-player-adapter STATIC
    src/player/audio.c
    src/player/input.c
    src/player/presentation.c
    src/player/session.c)
  target_include_directories(gabbaboy-player-adapter PUBLIC
    "${PROJECT_SOURCE_DIR}/src/player")
  target_link_libraries(gabbaboy-player-adapter PUBLIC GabbaBoy::core SDL3::SDL3)
  target_compile_features(gabbaboy-player-adapter PUBLIC c_std_17)
  set_target_properties(gabbaboy-player-adapter PROPERTIES C_EXTENSIONS OFF)

  add_executable(gabbaboy-player src/player/main.c)
  target_link_libraries(gabbaboy-player PRIVATE gabbaboy-player-adapter SDL3::SDL3)
  target_compile_features(gabbaboy-player PRIVATE c_std_17)
  target_compile_definitions(gabbaboy-player PRIVATE
    GABBABOY_PLAYER_DEMO_ROM=\"${PROJECT_SOURCE_DIR}/fixtures/visible-demo/demo.gb\"
    GABBABOY_PLAYER_INVALID_ROM=\"${PROJECT_SOURCE_DIR}/fixtures/visible-demo/LICENSE.txt\")
  set_target_properties(gabbaboy-player PROPERTIES C_EXTENSIONS OFF)
endif()

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
install(FILES
  fixtures/visible-demo/demo.gb
  fixtures/visible-demo/manifest.json
  fixtures/visible-demo/LICENSE.txt
  DESTINATION "${CMAKE_INSTALL_DATADIR}/gabbaboy/fixtures/visible-demo")
install(FILES
  fixtures/mbc1-continuation/continuation.asm
  fixtures/mbc1-continuation/continuation.gb
  fixtures/mbc1-continuation/manifest.json
  fixtures/mbc1-continuation/LICENSE.txt
  DESTINATION "${CMAKE_INSTALL_DATADIR}/gabbaboy/fixtures/mbc1-continuation")
install(EXPORT GabbaBoyTargets
  FILE GabbaBoyTargets.cmake
  NAMESPACE GabbaBoy::
  DESTINATION "${GABBABOY_CMAKE_INSTALL_DIR}")
install(FILES
  "${CMAKE_CURRENT_BINARY_DIR}/GabbaBoyConfig.cmake"
  "${CMAKE_CURRENT_BINARY_DIR}/GabbaBoyConfigVersion.cmake"
  DESTINATION "${GABBABOY_CMAKE_INSTALL_DIR}")

if(BUILD_TESTING)
  add_executable(measure_core tests/measure_core.c)
  target_link_libraries(measure_core PRIVATE GabbaBoy::core)
  target_compile_features(measure_core PRIVATE c_std_17)
  set_target_properties(measure_core PROPERTIES C_EXTENSIONS OFF)
  if(WIN32)
    target_link_libraries(measure_core PRIVATE Psapi)
  endif()
  add_subdirectory(tests)
endif()
