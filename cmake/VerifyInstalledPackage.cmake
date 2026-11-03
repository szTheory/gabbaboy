if(NOT DEFINED GBB_INSTALL_PREFIX)
  message(FATAL_ERROR "GBB_INSTALL_PREFIX is required")
endif()

if(DEFINED GBB_SOURCE_DIR AND NOT "${GBB_SOURCE_DIR}" STREQUAL "")
  get_filename_component(source_dir "${GBB_SOURCE_DIR}" ABSOLUTE)
else()
  get_filename_component(source_dir "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
endif()
set(fixture_admission_checker "${source_dir}/tests/scripts/verify-fixture-admission.py")
if(NOT EXISTS "${fixture_admission_checker}")
  message(FATAL_ERROR "Fixture admission checker is missing: ${fixture_admission_checker}")
endif()
find_package(Python3 COMPONENTS Interpreter REQUIRED)

get_filename_component(prefix "${GBB_INSTALL_PREFIX}" ABSOLUTE BASE_DIR "${CMAKE_CURRENT_LIST_DIR}/..")
set(product_policy_command
  "${Python3_EXECUTABLE}" -I "${fixture_admission_checker}"
  --check-product-tree "${prefix}" --layout core --repo-root "${source_dir}")
if(DEFINED GBB_WRITE_PRODUCT_INVENTORY AND NOT "${GBB_WRITE_PRODUCT_INVENTORY}" STREQUAL "")
  list(APPEND product_policy_command --write-inventory "${GBB_WRITE_PRODUCT_INVENTORY}")
elseif(DEFINED GBB_PRODUCT_INVENTORY AND NOT "${GBB_PRODUCT_INVENTORY}" STREQUAL "")
  list(APPEND product_policy_command --inventory "${GBB_PRODUCT_INVENTORY}")
endif()
if(DEFINED GBB_NOTICE_SIDECAR AND NOT "${GBB_NOTICE_SIDECAR}" STREQUAL "")
  list(APPEND product_policy_command --notice-sidecar "${GBB_NOTICE_SIDECAR}")
endif()
execute_process(
  COMMAND ${product_policy_command}
  RESULT_VARIABLE product_policy_result
  OUTPUT_VARIABLE product_policy_output
  ERROR_VARIABLE product_policy_error
  OUTPUT_STRIP_TRAILING_WHITESPACE
  ERROR_STRIP_TRAILING_WHITESPACE)
if(NOT product_policy_result EQUAL 0)
  message(FATAL_ERROR
    "Core product policy rejected installed bytes (${product_policy_result}): ${product_policy_error}${product_policy_output}")
endif()
message(STATUS "Core product policy accepted actual installed bytes at ${prefix}")

set(header "${prefix}/include/gabbaboy/gabbaboy.h")
if(NOT DEFINED GBB_EXECUTABLE_SUFFIX)
  message(FATAL_ERROR "GBB_EXECUTABLE_SUFFIX is required")
endif()
set(runner "${prefix}/bin/gabbaboy-runner${GBB_EXECUTABLE_SUFFIX}")
set(fixture_dir "${prefix}/share/gabbaboy/fixtures/tracer")
set(battery_fixture_dir "${prefix}/share/gabbaboy/fixtures/mbc1-continuation")
file(GLOB package_configs LIST_DIRECTORIES false "${prefix}/*/cmake/GabbaBoy/GabbaBoyConfig.cmake")
list(LENGTH package_configs package_config_count)
if(NOT package_config_count EQUAL 1)
  message(FATAL_ERROR "Expected one installed GabbaBoy config under the prefix, found ${package_config_count}")
endif()
get_filename_component(package_dir "${package_configs}" DIRECTORY)
foreach(required IN ITEMS
    "${header}"
    "${runner}"
    "${fixture_dir}/tracer.gb"
    "${fixture_dir}/manifest.json"
    "${fixture_dir}/LICENSE.txt"
    "${battery_fixture_dir}/continuation.asm"
    "${battery_fixture_dir}/continuation.gb"
    "${battery_fixture_dir}/manifest.json"
    "${battery_fixture_dir}/LICENSE.txt"
    "${package_dir}/GabbaBoyTargets.cmake"
    "${package_dir}/GabbaBoyConfig.cmake"
    "${package_dir}/GabbaBoyConfigVersion.cmake")
  if(NOT EXISTS "${required}")
    message(FATAL_ERROR "Installed package is missing: ${required}")
  endif()
endforeach()

file(READ "${battery_fixture_dir}/manifest.json" battery_manifest)
string(JSON battery_rom_digest ERROR_VARIABLE battery_json_error
  GET "${battery_manifest}" sha256)
if(NOT battery_json_error STREQUAL "NOTFOUND")
  message(FATAL_ERROR "Installed battery fixture manifest is invalid: ${battery_json_error}")
endif()
string(JSON battery_source_digest ERROR_VARIABLE battery_source_json_error
  GET "${battery_manifest}" source_sha256)
if(NOT battery_source_json_error STREQUAL "NOTFOUND")
  message(FATAL_ERROR "Installed battery fixture source digest is missing: ${battery_source_json_error}")
endif()
file(SHA256 "${battery_fixture_dir}/continuation.gb" installed_battery_digest)
file(SHA256 "${battery_fixture_dir}/continuation.asm" installed_battery_source_digest)
if(NOT installed_battery_digest STREQUAL battery_rom_digest OR
   NOT installed_battery_source_digest STREQUAL battery_source_digest)
  message(FATAL_ERROR
    "Installed battery fixture digest mismatch: ROM expected ${battery_rom_digest}, got ${installed_battery_digest}; source expected ${battery_source_digest}, got ${installed_battery_source_digest}")
endif()
file(SIZE "${battery_fixture_dir}/continuation.gb" installed_battery_size)
if(NOT installed_battery_size EQUAL 32768)
  message(FATAL_ERROR "Installed battery continuation fixture is not exactly 32 KiB")
endif()

file(GLOB_RECURSE metadata_files LIST_DIRECTORIES false "${package_dir}/*")
set(forbidden_paths "${CMAKE_SOURCE_DIR};${CMAKE_BINARY_DIR}")
if(DEFINED GBB_FORBIDDEN_PATHS)
  list(APPEND forbidden_paths ${GBB_FORBIDDEN_PATHS})
endif()
foreach(metadata IN LISTS metadata_files)
  file(READ "${metadata}" content)
  foreach(private_path IN LISTS forbidden_paths)
    if(NOT private_path STREQUAL "" AND content MATCHES "${private_path}")
      message(FATAL_ERROR "Private source/build path leaked into ${metadata}: ${private_path}")
    endif()
  endforeach()
endforeach()

message(STATUS "Installed GabbaBoy package contents and relocatable metadata verified at ${prefix}")

if(DEFINED GBB_RUNNER_WORKDIR)
  get_filename_component(runner_workdir "${GBB_RUNNER_WORKDIR}" ABSOLUTE BASE_DIR "${CMAKE_CURRENT_LIST_DIR}/..")
  file(MAKE_DIRECTORY "${runner_workdir}")
  execute_process(
    COMMAND "${CMAKE_COMMAND}" -E chdir "${runner_workdir}"
      "${runner}" "${fixture_dir}/tracer.gb"
    RESULT_VARIABLE runner_result
    OUTPUT_VARIABLE runner_output
    ERROR_VARIABLE runner_error)
  if(NOT runner_result EQUAL 0 OR NOT runner_output MATCHES "outcome=pass" OR
     NOT runner_output MATCHES "trace_records=[1-9][0-9]*")
    message(FATAL_ERROR "Installed runner failed from unrelated working directory (${runner_result}): ${runner_output}${runner_error}")
  endif()
  message(STATUS "Installed runner passed with installed fixture from ${runner_workdir}")
endif()
