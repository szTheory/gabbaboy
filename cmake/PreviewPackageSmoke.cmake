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
set(package_build_dir "${smoke_root}/release-package-build")
set(install_prefix "${smoke_root}/installed-prefix")
set(extract_root "${smoke_root}/extracted")
set(archive "${smoke_root}/installed-prefix.tar.gz")
set(core_inventory "${smoke_root}/core-product-inventory.json")
set(runner_workdir "${smoke_root}/unrelated-working-directory")

file(REMOVE_RECURSE "${smoke_root}")
file(MAKE_DIRECTORY "${smoke_root}" "${extract_root}" "${runner_workdir}")

execute_process(
  COMMAND "${GBB_CMAKE_COMMAND}" -S "${source_dir}" -B "${package_build_dir}"
    -G "${GBB_GENERATOR}" -DBUILD_TESTING=OFF -DCMAKE_BUILD_TYPE=Release
  RESULT_VARIABLE package_configure_result
  OUTPUT_VARIABLE package_configure_output
  ERROR_VARIABLE package_configure_error)
if(NOT package_configure_result EQUAL 0)
  message(FATAL_ERROR
    "Release package configure failed (${package_configure_result}): ${package_configure_output}${package_configure_error}")
endif()
execute_process(
  COMMAND "${GBB_CMAKE_COMMAND}" --build "${package_build_dir}" --target gabbaboy-runner
  RESULT_VARIABLE package_build_result
  OUTPUT_VARIABLE package_build_output
  ERROR_VARIABLE package_build_error)
if(NOT package_build_result EQUAL 0)
  message(FATAL_ERROR
    "Release package build failed (${package_build_result}): ${package_build_output}${package_build_error}")
endif()
execute_process(
  COMMAND "${GBB_CMAKE_COMMAND}" --install "${package_build_dir}" --prefix "${install_prefix}"
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
    "${install_prefix}/share/gabbaboy/fixtures/visible-demo/demo.gb"
    "${install_prefix}/share/gabbaboy/fixtures/visible-demo/manifest.json"
    "${install_prefix}/share/gabbaboy/fixtures/visible-demo/LICENSE.txt"
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

# Validate the producer's actual install tree before packaging it. The inventory is a
# temporary identity check for extraction, not an alternate product-policy source.
execute_process(
  COMMAND "${GBB_CMAKE_COMMAND}"
    "-DGBB_SOURCE_DIR=${source_dir}"
    "-DGBB_INSTALL_PREFIX=${install_prefix}"
    "-DGBB_EXECUTABLE_SUFFIX=${GBB_EXECUTABLE_SUFFIX}"
    "-DGBB_WRITE_PRODUCT_INVENTORY=${core_inventory}"
    -P "${source_dir}/cmake/VerifyInstalledPackage.cmake"
  RESULT_VARIABLE stage_policy_result
  OUTPUT_VARIABLE stage_policy_output
  ERROR_VARIABLE stage_policy_error)
if(NOT stage_policy_result EQUAL 0)
  message(FATAL_ERROR
    "Installed package stage failed exact product policy (${stage_policy_result}): ${stage_policy_output}${stage_policy_error}")
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
# This control exercises the production installed-package verifier with a real staged tree.
# Keep the mutation isolated: no planted bytes may reach the consumer smoke below.
set(product_policy_control_root "${smoke_root}/product-policy-control")
set(product_policy_control_prefix "${product_policy_control_root}/installed-prefix")
file(REMOVE_RECURSE "${product_policy_control_root}")
file(MAKE_DIRECTORY "${product_policy_control_root}")
file(COPY "${extracted_prefix}" DESTINATION "${product_policy_control_root}")
set(product_policy_control_payload
  "${product_policy_control_prefix}/share/gabbaboy/fixtures/tracer/renamed-control")
file(COPY_FILE "${source_dir}/fixtures/mooneye-cgb/boot_regs-cgb.gb"
  "${product_policy_control_payload}")
execute_process(
  COMMAND "${GBB_CMAKE_COMMAND}"
    "-DGBB_INSTALL_PREFIX=${product_policy_control_prefix}"
    "-DGBB_EXECUTABLE_SUFFIX=${GBB_EXECUTABLE_SUFFIX}"
    "-DGBB_SOURCE_DIR=${source_dir}"
    -P "${source_dir}/cmake/VerifyInstalledPackage.cmake"
  RESULT_VARIABLE product_policy_control_result
  OUTPUT_VARIABLE product_policy_control_output
  ERROR_VARIABLE product_policy_control_error)
file(REMOVE_RECURSE "${product_policy_control_root}")
if(product_policy_control_result EQUAL 0 OR
   NOT "${product_policy_control_output}${product_policy_control_error}" MATCHES "product-fixture-leak")
  message(FATAL_ERROR
    "Installed-package verifier did not reject renamed fixture bytes for the expected policy reason (${product_policy_control_result}): ${product_policy_control_output}${product_policy_control_error}")
endif()
message(STATUS "Installed-package verifier rejected renamed fixture bytes before consumers")

# D-32 / T-10-22: Mooneye MBC and CGB ROMs are repository fixtures only; prove they are absent from the
# extracted package by name and digest, and that the installed fixture set is exactly as expected.
set(mooneye_scan_command "${GBB_CMAKE_COMMAND}"
    "-DGBB_SCAN_DIR=${extracted_prefix}"
    "-DGBB_FORBIDDEN_MANIFESTS=${source_dir}/fixtures/mooneye-mbc/manifest.json|${source_dir}/fixtures/mooneye-cgb/manifest.json"
    "-DGBB_EXPECT_FIXTURE_DIRS=tracer|visible-demo|mbc1-continuation"
    -P "${source_dir}/cmake/ScanForbiddenFixtures.cmake")
execute_process(
  COMMAND ${mooneye_scan_command}
  RESULT_VARIABLE scan_result OUTPUT_VARIABLE scan_output ERROR_VARIABLE scan_error)
if(NOT scan_result EQUAL 0 OR NOT "${scan_output}${scan_error}" MATCHES "files=")
  message(FATAL_ERROR "Extracted package forbidden-fixture scan failed (${scan_result}): ${scan_output}${scan_error}")
endif()
# Exercise the exact preview scan with renamed CGB bytes outside the fixture directory allowlist.
# Remove the planted file before any consumer executes, even if the control fails.
set(cgb_scan_control "${extracted_prefix}/share/payload.bin")
file(COPY_FILE "${source_dir}/fixtures/mooneye-cgb/boot_regs-cgb.gb" "${cgb_scan_control}")
execute_process(
  COMMAND ${mooneye_scan_command}
  RESULT_VARIABLE cgb_control_result OUTPUT_VARIABLE cgb_control_output ERROR_VARIABLE cgb_control_error)
file(REMOVE "${cgb_scan_control}")
if(cgb_control_result EQUAL 0 OR
   NOT "${cgb_control_output}${cgb_control_error}" MATCHES "mooneye-installed: share/payload.bin")
  message(FATAL_ERROR "Extracted package renamed CGB fixture control failed (${cgb_control_result}): ${cgb_control_output}${cgb_control_error}")
endif()
message(STATUS "Extracted package renamed CGB fixture rejected by digest")
execute_process(
  COMMAND "${GBB_CMAKE_COMMAND}"
    "-DGBB_SCAN_DIR=${extracted_prefix}"
    "-DGBB_FORBIDDEN_MANIFESTS=${source_dir}/fixtures/samesuite/manifest.json|${source_dir}/fixtures/magentests/manifest.json"
    -DGBB_FORBIDDEN_LABEL=cgb-hdma
    -DGBB_FORBIDDEN_PATH_LABELS=samesuite|magentests|mealybug
    -DGBB_EXPECT_FIXTURE_DIRS=tracer|visible-demo|mbc1-continuation
    -P "${source_dir}/cmake/ScanForbiddenFixtures.cmake"
  RESULT_VARIABLE cgb_hdma_scan_result
  OUTPUT_VARIABLE cgb_hdma_scan_output ERROR_VARIABLE cgb_hdma_scan_error)
if(NOT cgb_hdma_scan_result EQUAL 0 OR
   NOT "${cgb_hdma_scan_output}${cgb_hdma_scan_error}" MATCHES "cgb-hdma absent from scanned tree files=")
  message(FATAL_ERROR "Extracted package CGB-HDMA forbidden-fixture scan failed (${cgb_hdma_scan_result}): ${cgb_hdma_scan_output}${cgb_hdma_scan_error}")
endif()
execute_process(
  COMMAND "${GBB_CMAKE_COMMAND}"
    "-DGBB_SOURCE_DIR=${source_dir}"
    "-DGBB_INSTALL_PREFIX=${extracted_prefix}"
    "-DGBB_EXECUTABLE_SUFFIX=${GBB_EXECUTABLE_SUFFIX}"
    "-DGBB_PRODUCT_INVENTORY=${core_inventory}"
    "-DGBB_RUNNER_WORKDIR=${runner_workdir}"
    "-DGBB_FORBIDDEN_PATHS=${source_dir};${binary_dir};${package_build_dir}"
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

set(example_configure_command
  "${GBB_CMAKE_COMMAND}" -S "${source_dir}/examples/relocated-c"
  -B "${smoke_root}/consumer-relocated-c"
  -G "${GBB_GENERATOR}"
  "-DCMAKE_PREFIX_PATH=${extracted_prefix}"
  "-DGBB_ROM_PATH=${extracted_prefix}/share/gabbaboy/fixtures/visible-demo/demo.gb"
  "-DGBB_BATTERY_ROM_PATH=${extracted_prefix}/share/gabbaboy/fixtures/mbc1-continuation/continuation.gb")
if(DEFINED GBB_SANITIZER_LINK_OPTIONS AND NOT GBB_SANITIZER_LINK_OPTIONS STREQUAL "")
  list(APPEND example_configure_command
    "-DCMAKE_EXE_LINKER_FLAGS=${GBB_SANITIZER_LINK_OPTIONS}")
endif()
execute_process(COMMAND ${example_configure_command}
  RESULT_VARIABLE example_configure_result OUTPUT_VARIABLE example_configure_output ERROR_VARIABLE example_configure_error)
if(NOT example_configure_result EQUAL 0)
  message(FATAL_ERROR "Relocated C example configure failed (${example_configure_result}): ${example_configure_output}${example_configure_error}")
endif()
set(example_build_command "${GBB_CMAKE_COMMAND}" --build "${smoke_root}/consumer-relocated-c")
if(DEFINED GBB_CONFIGURATION AND NOT GBB_CONFIGURATION STREQUAL "")
  list(APPEND example_build_command --config "${GBB_CONFIGURATION}")
endif()
execute_process(COMMAND ${example_build_command}
  RESULT_VARIABLE example_build_result OUTPUT_VARIABLE example_build_output ERROR_VARIABLE example_build_error)
if(NOT example_build_result EQUAL 0)
  message(FATAL_ERROR "Relocated C example build failed (${example_build_result}): ${example_build_output}${example_build_error}")
endif()
set(example_executable "${smoke_root}/consumer-relocated-c/relocated-c${GBB_EXECUTABLE_SUFFIX}")
if(DEFINED GBB_CONFIGURATION AND EXISTS "${smoke_root}/consumer-relocated-c/${GBB_CONFIGURATION}/relocated-c${GBB_EXECUTABLE_SUFFIX}")
  set(example_executable "${smoke_root}/consumer-relocated-c/${GBB_CONFIGURATION}/relocated-c${GBB_EXECUTABLE_SUFFIX}")
endif()
foreach(run_index RANGE 1 2)
  execute_process(COMMAND "${example_executable}"
    "${extracted_prefix}/share/gabbaboy/fixtures/visible-demo/demo.gb"
    "${extracted_prefix}/share/gabbaboy/fixtures/mbc1-continuation/continuation.gb"
    "${runner_workdir}/example-battery.sav"
    WORKING_DIRECTORY "${runner_workdir}"
    RESULT_VARIABLE example_result OUTPUT_VARIABLE example_output ERROR_VARIABLE example_error)
  if(NOT example_result EQUAL 0)
    message(FATAL_ERROR "Relocated C example run ${run_index} failed (${example_result}): ${example_output}${example_error}")
  endif()
endforeach()
if(NOT EXISTS "${runner_workdir}/example-battery.sav")
  message(FATAL_ERROR "Relocated C example did not export its host battery file")
endif()

message(STATUS "Full installed package archive passed relocation, runner, and external C/C++ consumer smokes: ${archive}")
