# Phase 13 uses one test-only core source with bounded runtime mask bits.  The
# P12 generator remains the authority for its inherited anchors and globals.
if(NOT DEFINED PROJECT_SOURCE_DIR)
  get_filename_component(PROJECT_SOURCE_DIR "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
endif()
include("${PROJECT_SOURCE_DIR}/cmake/P12Mutants.cmake")

set(GBB_P13_ANCHOR_TAGS
  P13-05-M01 P13-05-M02 P13-05-M03 P13-05-M04 P13-05-M05 P13-05-M06 P13-05-M07
  P13-05-M08 P13-05-M09 P13-05-M10 P13-05-M11 P13-05-M12 P13-05-M13 P13-05-M14)
set(GBB_P13_MUTANT_BITS
  no_steal=40 no_copy=41 duplicate_copy=42 wrong_vbk=43
  unmasked_address=44 wrong_count=45 wrong_cancel=46 speed_scaled=47
  halt_admission=48 false_trigger=49 lost_dma_irq=50 dma_realign=51
  shifted_order=52 lost_phase=53)

function(gbb_p13_make_mutant_core out_path)
  set(core_path "${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c")
  if(ARGC GREATER 1)
    if(NOT ARGV1 STREQUAL "CORE_PATH" OR ARGC LESS 3)
      message(FATAL_ERROR "gbb_p13_make_mutant_core expects optional CORE_PATH <path>")
    endif()
    set(core_path "${ARGV2}")
  endif()
  if(NOT EXISTS "${core_path}")
    message(FATAL_ERROR "p13 mutant core does not exist: ${core_path}")
  endif()
  set(p12_base "${out_path}.p12-base.c")
  gbb_p12_make_mutant_core("${p12_base}" 0 CORE_PATH "${core_path}")
  file(READ "${p12_base}" core_text)
  foreach(tag IN LISTS GBB_P13_ANCHOR_TAGS)
    gbb_p12_require_unique_anchor("${core_text}" "${tag}" "p13 mutant ${tag}" "${core_path}")
  endforeach()
  file(WRITE "${out_path}"
    "#include <stdint.h>\n"
    "int32_t gbb_p13_duration_offset = 0;\n"
    "#define GBB_P13_MUT(n) ((unsigned)((gbb_p12_mutants >> (n)) & 1u))\n"
    "#define GBB_P13_DURATION_OFFSET gbb_p13_duration_offset\n"
    "${core_text}\n"
    "void gbb_p13_set_duration_offset(int32_t offset) {\n"
    "  if (offset >= -8 && offset <= 8) gbb_p13_duration_offset = offset;\n"
    "}\n")
endfunction()

function(gbb_p13_mutant_test exe suffix bit case_name regex)
  math(EXPR mask "1 << ${bit}" OUTPUT_FORMAT HEXADECIMAL)
  set(test "cgb_hdma_mutant_${suffix}")
  add_test(NAME "${test}"
    COMMAND "${CMAKE_COMMAND}"
      "-DGBB_CMD=$<TARGET_FILE:${exe}>;${case_name};--mutants;${mask}"
      -DGBB_EXPECT_CODE=1
      "-DGBB_EXPECT_REGEX=${regex}"
      -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
  set_tests_properties("${test}" PROPERTIES TIMEOUT 60 ENVIRONMENT "ASAN_OPTIONS=detect_leaks=0")
  add_test(NAME "${test}_control"
    COMMAND "${CMAKE_COMMAND}"
      "-DGBB_CMD=$<TARGET_FILE:${exe}>;${case_name};--mutants;0"
      -DGBB_EXPECT_CODE=0
      "-DGBB_EXPECT_REGEX=cgb-hdma .* pass"
      -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
  set_tests_properties("${test}_control" PROPERTIES TIMEOUT 60)
endfunction()

function(gbb_p13_anchor_guard)
  set(source "${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c")
  if(DEFINED GBB_P13_GUARD_DIR AND NOT "${GBB_P13_GUARD_DIR}" STREQUAL "")
    set(guard_dir "${GBB_P13_GUARD_DIR}")
  else()
    set(guard_dir "${CMAKE_CURRENT_BINARY_DIR}")
  endif()
  file(READ "${source}" fixture_text)
  foreach(kind duplicate missing)
    set(fixture "${guard_dir}/p13-anchor-${kind}.c")
    set(output "${guard_dir}/p13-anchor-${kind}-output.c")
    set(text "${fixture_text}")
    if(kind STREQUAL "duplicate")
      string(APPEND text "\n/* P13-05-M01 duplicate-anchor fixture */\n")
    else()
      string(REPLACE "P13-05-M01" "P13-05-MX01" text "${text}")
    endif()
    file(WRITE "${fixture}" "${text}")
    execute_process(COMMAND "${CMAKE_COMMAND}"
        "-DGBB_P13_SCRIPT_CORE=${fixture}" "-DGBB_P13_SCRIPT_OUT=${output}"
        -P "${CMAKE_CURRENT_FUNCTION_LIST_FILE}"
      RESULT_VARIABLE result OUTPUT_VARIABLE stdout ERROR_VARIABLE stderr)
    set(combined "${stdout}${stderr}")
    if(result EQUAL 0 OR NOT combined MATCHES "p13 mutant P13-05-M01: anchor.*must occur exactly once")
      message(FATAL_ERROR "P13 ${kind} anchor was not rejected before compile: result=${result}; output=${combined}")
    endif()
  endforeach()
endfunction()

if(DEFINED GBB_P13_SCRIPT_ANCHOR_GUARD)
  gbb_p13_anchor_guard()
  return()
endif()

if(DEFINED GBB_P13_SCRIPT_CORE AND DEFINED GBB_P13_SCRIPT_OUT)
  gbb_p13_make_mutant_core("${GBB_P13_SCRIPT_OUT}" CORE_PATH "${GBB_P13_SCRIPT_CORE}")
endif()
