foreach(required_var IN ITEMS GBB_SOURCE_DIR GBB_BINARY_DIR GBB_CMAKE_COMMAND GBB_GENERATOR)
  if(NOT DEFINED ${required_var} OR "${${required_var}}" STREQUAL "")
    message(FATAL_ERROR "${required_var} is required")
  endif()
endforeach()
if(NOT DEFINED GBB_EXECUTABLE_SUFFIX)
  message(FATAL_ERROR "GBB_EXECUTABLE_SUFFIX is required")
endif()

get_filename_component(source_dir "${GBB_SOURCE_DIR}" ABSOLUTE)
get_filename_component(binary_dir "${GBB_BINARY_DIR}" ABSOLUTE)
set(smoke_root "${binary_dir}/preview-package-smoke")
set(install_prefix "${smoke_root}/installed-prefix")
set(extract_root "${smoke_root}/extracted")
set(archive "${smoke_root}/installed-prefix.tar.gz")
set(runner_workdir "${smoke_root}/unrelated-working-directory")

file(REMOVE_RECURSE "${smoke_root}")
file(MAKE_DIRECTORY "${smoke_root}" "${extract_root}" "${runner_workdir}")

execute_process(
  COMMAND "${GBB_CMAKE_COMMAND}" --install "${binary_dir}" --prefix "${install_prefix}"
  RESULT_VARIABLE install_result OUTPUT_VARIABLE install_output ERROR_VARIABLE install_error)
if(NOT install_result EQUAL 0)
  message(FATAL_ERROR "Clean package install failed (${install_result}): ${install_output}${install_error}")
endif()

foreach(required IN ITEMS
    "${install_prefix}/include/gabbaboy/gabbaboy.h"
    "${install_prefix}/bin/gabbaboy-runner${GBB_EXECUTABLE_SUFFIX}"
    "${install_prefix}/share/gabbaboy/fixtures/tracer/tracer.gb"
    "${install_prefix}/share/gabbaboy/fixtures/tracer/manifest.json"
    "${install_prefix}/share/gabbaboy/fixtures/tracer/LICENSE.txt"
    "${install_prefix}/share/gabbaboy/fixtures/mbc1-continuation/continuation.asm"
    "${install_prefix}/share/gabbaboy/fixtures/mbc1-continuation/continuation.gb"
    "${install_prefix}/share/gabbaboy/fixtures/mbc1-continuation/manifest.json"
    "${install_prefix}/share/gabbaboy/fixtures/mbc1-continuation/LICENSE.txt")
  if(NOT EXISTS "${required}")
    message(FATAL_ERROR "Clean installed package is missing: ${required}")
  endif()
endforeach()
file(GLOB package_configs LIST_DIRECTORIES false
  "${install_prefix}/*/cmake/GabbaBoy/GabbaBoyConfig.cmake")
if(NOT package_configs)
  message(FATAL_ERROR "Installed package export metadata is missing")
endif()

execute_process(
  COMMAND "${GBB_CMAKE_COMMAND}" -E tar czf "${archive}" -- installed-prefix
  WORKING_DIRECTORY "${smoke_root}"
  RESULT_VARIABLE archive_result OUTPUT_VARIABLE archive_output ERROR_VARIABLE archive_error)
if(NOT archive_result EQUAL 0 OR NOT EXISTS "${archive}")
  message(FATAL_ERROR "Installed package archive failed (${archive_result}): ${archive_output}${archive_error}")
endif()
execute_process(
  COMMAND "${GBB_CMAKE_COMMAND}" -E tar xzf "${archive}"
  WORKING_DIRECTORY "${extract_root}"
  RESULT_VARIABLE extract_result OUTPUT_VARIABLE extract_output ERROR_VARIABLE extract_error)
if(NOT extract_result EQUAL 0)
  message(FATAL_ERROR "Installed package extraction failed (${extract_result}): ${extract_output}${extract_error}")
endif()

set(extracted_prefix "${extract_root}/installed-prefix")
execute_process(
  COMMAND "${GBB_CMAKE_COMMAND}"
    "-DGBB_INSTALL_PREFIX=${extracted_prefix}"
    "-DGBB_EXECUTABLE_SUFFIX=${GBB_EXECUTABLE_SUFFIX}"
    "-DGBB_RUNNER_WORKDIR=${runner_workdir}"
    "-DGBB_FORBIDDEN_PATHS=${source_dir};${binary_dir}"
    -P "${source_dir}/cmake/VerifyInstalledPackage.cmake"
  RESULT_VARIABLE runner_result OUTPUT_VARIABLE runner_output ERROR_VARIABLE runner_error)
if(NOT runner_result EQUAL 0)
  message(FATAL_ERROR "Extracted runner/package verification failed (${runner_result}): ${runner_output}${runner_error}")
endif()

foreach(language IN ITEMS c cpp)
  set(consumer_configure_command
    "${GBB_CMAKE_COMMAND}" -S "${source_dir}/tests/consumers/${language}"
    -B "${smoke_root}/consumer-${language}"
    -G "${GBB_GENERATOR}"
    "-DCMAKE_PREFIX_PATH=${extracted_prefix}"
    "-DGBB_TRACER_ROM=${extracted_prefix}/share/gabbaboy/fixtures/tracer/tracer.gb")
  if(DEFINED GBB_SANITIZER_LINK_OPTIONS AND NOT GBB_SANITIZER_LINK_OPTIONS STREQUAL "")
    list(APPEND consumer_configure_command
      "-DCMAKE_EXE_LINKER_FLAGS=${GBB_SANITIZER_LINK_OPTIONS}")
  endif()
  execute_process(
    COMMAND ${consumer_configure_command}
    RESULT_VARIABLE configure_result OUTPUT_VARIABLE configure_output ERROR_VARIABLE configure_error)
  if(NOT configure_result EQUAL 0)
    message(FATAL_ERROR "Extracted ${language} consumer configure failed (${configure_result}): ${configure_output}${configure_error}")
  endif()
  set(build_command "${GBB_CMAKE_COMMAND}" --build "${smoke_root}/consumer-${language}")
  if(DEFINED GBB_CONFIGURATION AND NOT GBB_CONFIGURATION STREQUAL "")
    list(APPEND build_command --config "${GBB_CONFIGURATION}")
  endif()
  execute_process(COMMAND ${build_command}
    RESULT_VARIABLE build_result OUTPUT_VARIABLE build_output ERROR_VARIABLE build_error)
  if(NOT build_result EQUAL 0)
    message(FATAL_ERROR "Extracted ${language} consumer build failed (${build_result}): ${build_output}${build_error}")
  endif()
  set(consumer "${smoke_root}/consumer-${language}/consumer-${language}${GBB_EXECUTABLE_SUFFIX}")
  if(DEFINED GBB_CONFIGURATION AND EXISTS "${smoke_root}/consumer-${language}/${GBB_CONFIGURATION}/consumer-${language}${GBB_EXECUTABLE_SUFFIX}")
    set(consumer "${smoke_root}/consumer-${language}/${GBB_CONFIGURATION}/consumer-${language}${GBB_EXECUTABLE_SUFFIX}")
  endif()
  execute_process(COMMAND "${consumer}" "${extracted_prefix}/share/gabbaboy/fixtures/tracer/tracer.gb"
    RESULT_VARIABLE consumer_result OUTPUT_VARIABLE consumer_output ERROR_VARIABLE consumer_error)
  if(NOT consumer_result EQUAL 0)
    message(FATAL_ERROR "Extracted ${language} consumer failed (${consumer_result}): ${consumer_output}${consumer_error}")
  endif()
endforeach()

message(STATUS "Full installed package archive passed relocation, runner, and external C/C++ consumer smokes: ${archive}")
