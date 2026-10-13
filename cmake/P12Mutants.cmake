# Phase 12 runtime-mask mutant table. Each id owns one or more exact source
# anchors. Keep each anchor and replacement in a separate variable because C
# replacement text may contain semicolons.
set(GBB_P12_MUTANT_IDS 5 7 18)

set(GBB_P12_SITES_5 1)
set(GBB_P12_ANCHOR_5_1 "instance->cpu_stall_kind = GBB_STALL_SPEED_SWITCH; /* P12-M5 */")
set(GBB_P12_REPLACEMENT_5_1 "instance->cpu_stall_kind = GBB_STALL_SPEED_SWITCH; /* P12-M5 */\n            if (GBB_P12_MUT(5)) instance->stopped = 1;")

set(GBB_P12_SITES_7 1)
set(GBB_P12_ANCHOR_7_1 "advance_devices(instance, step); /* P12-M7 */")
set(GBB_P12_REPLACEMENT_7_1 "if (GBB_P12_MUT(7)) instance->time_half_dots += step; else advance_devices(instance, step);")

set(GBB_P12_SITES_18 3)
set(GBB_P12_ANCHOR_18_1 "return (uint8_t)(d.ticks >> m->double_speed);")
set(GBB_P12_REPLACEMENT_18_1 "return GBB_P12_MUT(18) ? d.ticks : (uint8_t)(d.ticks >> m->double_speed);")
set(GBB_P12_ANCHOR_18_2 "advance_devices_to(m, m->instruction_start_half_dots + (offset >> m->double_speed));")
set(GBB_P12_REPLACEMENT_18_2 "advance_devices_to(m, m->instruction_start_half_dots + (GBB_P12_MUT(18) ? offset : (offset >> m->double_speed)));")
set(GBB_P12_ANCHOR_18_3 "uint64_t timestamp = m->instruction_start_half_dots + (offset >> m->double_speed);")
set(GBB_P12_REPLACEMENT_18_3 "uint64_t timestamp = m->instruction_start_half_dots + (GBB_P12_MUT(18) ? offset : (offset >> m->double_speed));")

function(gbb_p12_make_mutant_core out_path default_mask)
  set(core_path "${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c")
  if(ARGC GREATER 2)
    if(NOT ARGV2 STREQUAL "CORE_PATH" OR ARGC LESS 4)
      message(FATAL_ERROR "gbb_p12_make_mutant_core expects optional CORE_PATH <path>")
    endif()
    set(core_path "${ARGV3}")
  endif()
  if(NOT EXISTS "${core_path}")
    message(FATAL_ERROR "p12 mutant core does not exist: ${core_path}")
  endif()
  if(NOT CMAKE_SCRIPT_MODE_FILE)
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${core_path}")
  endif()
  file(READ "${core_path}" core_text)
  foreach(id IN LISTS GBB_P12_MUTANT_IDS)
    set(site_count "${GBB_P12_SITES_${id}}")
    if(NOT site_count MATCHES "^[1-9][0-9]*$")
      message(FATAL_ERROR "p12 mutant M${id}: GBB_P12_SITES_${id} must be a positive integer")
    endif()
    foreach(site RANGE 1 ${site_count})
      set(anchor_var "GBB_P12_ANCHOR_${id}_${site}")
      set(replacement_var "GBB_P12_REPLACEMENT_${id}_${site}")
      if(NOT DEFINED ${anchor_var} OR NOT DEFINED ${replacement_var})
        message(FATAL_ERROR "p12 mutant M${id} site ${site}: anchor or replacement is undefined")
      endif()
      set(anchor "${${anchor_var}}")
      set(replacement "${${replacement_var}}")
      string(FIND "${core_text}" "${anchor}" first)
      string(FIND "${core_text}" "${anchor}" final REVERSE)
      if(first EQUAL -1 OR NOT first EQUAL final)
        message(FATAL_ERROR "p12 mutant M${id} site ${site}: anchor '${anchor}' must occur exactly once in ${core_path} (first=${first} last=${final})")
      endif()
      string(REPLACE "${anchor}" "${replacement}" core_text "${core_text}")
    endforeach()
  endforeach()
  file(WRITE "${out_path}"
    "#include <stdint.h>\n"
    "uint64_t gbb_p12_mutants = ${default_mask};\n"
    "int32_t gbb_p12_stall_offset_t = 0;\n"
    "#define GBB_P12_MUT(n) ((unsigned)((gbb_p12_mutants >> (n)) & 1u))\n"
    "${core_text}\n"
    "void gbb_p12_set_mutants(uint64_t mask) { gbb_p12_mutants = mask; }\n")
endfunction()

function(gbb_p12_mutant_test exe n name case_name regex)
  math(EXPR mask "1 << ${n}" OUTPUT_FORMAT HEXADECIMAL)
  set(test "cgb_speed_mutant_m${n}_${name}")
  add_test(NAME "${test}"
    COMMAND "${CMAKE_COMMAND}"
      "-DGBB_CMD=$<TARGET_FILE:${exe}>;${case_name};--mutants;${mask}"
      -DGBB_EXPECT_CODE=1
      "-DGBB_EXPECT_REGEX=${regex}"
      -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
  set_tests_properties("${test}" PROPERTIES ENVIRONMENT "ASAN_OPTIONS=detect_leaks=0" TIMEOUT 60)
  add_test(NAME "${test}_control"
    COMMAND "${CMAKE_COMMAND}"
      "-DGBB_CMD=$<TARGET_FILE:${exe}>;${case_name};--mutants;0"
      -DGBB_EXPECT_CODE=0
      -DGBB_EXPECT_REGEX=.*
      -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
  set_tests_properties("${test}_control" PROPERTIES TIMEOUT 60)
endfunction()

if(CMAKE_SCRIPT_MODE_FILE STREQUAL CMAKE_CURRENT_LIST_FILE
   AND DEFINED GBB_P12_SCRIPT_CORE AND DEFINED GBB_P12_SCRIPT_OUT)
  gbb_p12_make_mutant_core("${GBB_P12_SCRIPT_OUT}" 0 CORE_PATH "${GBB_P12_SCRIPT_CORE}")
endif()
