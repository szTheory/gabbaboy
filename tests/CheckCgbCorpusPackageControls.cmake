cmake_minimum_required(VERSION 3.25)
foreach(required GBB_SCAN_SCRIPT GBB_SOURCE_DIR GBB_BUILD_DIR GBB_MANIFESTS GBB_PATH_LABELS)
  if(NOT DEFINED ${required} OR "${${required}}" STREQUAL "")
    message(FATAL_ERROR "CGB corpus package control is missing ${required}")
  endif()
endforeach()

function(check_renamed_fixture kind source relative)
  set(scan_dir "${GBB_BUILD_DIR}/cgb-corpus-scan-${kind}-control")
  file(REMOVE_RECURSE "${scan_dir}")
  file(MAKE_DIRECTORY "${scan_dir}/share")
  file(COPY_FILE "${GBB_SOURCE_DIR}/${source}" "${scan_dir}/${relative}")
  execute_process(
    COMMAND "${CMAKE_COMMAND}"
      "-DGBB_SCAN_DIR=${scan_dir}"
      "-DGBB_FORBIDDEN_MANIFESTS=${GBB_MANIFESTS}"
      "-DGBB_FORBIDDEN_PATH_LABELS=${GBB_PATH_LABELS}"
      -DGBB_FORBIDDEN_LABEL=cgb-corpus
      -P "${GBB_SCAN_SCRIPT}"
    RESULT_VARIABLE code
    OUTPUT_VARIABLE stdout
    ERROR_VARIABLE stderr)
  set(output "${stdout}${stderr}")
  if(NOT code EQUAL 1 OR NOT output MATCHES "cgb-corpus-installed: share/payload.bin")
    message(FATAL_ERROR "${kind} fixture was not rejected by digest: code=${code} output=${output}")
  endif()
endfunction()

check_renamed_fixture(rom "fixtures/mooneye-cgb/boot_regs-cgb.gb" "share/payload.bin")
check_renamed_fixture(png "fixtures/age/references/m3-bg-lcdc-cgbBCE.png" "share/payload.bin")
message(STATUS "cgb-corpus package controls pass renamed-rom=1 renamed-png=1")
