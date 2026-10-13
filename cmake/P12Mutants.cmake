# Phase 12 runtime-mask mutant table. Each id owns one or more exact source
# anchors. Keep each anchor and replacement in a separate variable because C
# replacement text may contain semicolons.
set(GBB_P12_MUTANT_IDS 2 3 4 5 7 11 14 15 18 24 25 26)

set(GBB_P12_SITES_2 1)
set(GBB_P12_ANCHOR_2_1 "if (cpu_tick && m->serial_active && (m->serial_control & 1u) != 0 &&")
set(GBB_P12_REPLACEMENT_2_1 "if ((cpu_tick || GBB_P12_MUT(2)) && m->serial_active && (m->serial_control & 1u) != 0 &&")

set(GBB_P12_SITES_4 2)
set(GBB_P12_ANCHOR_4_1 "const uint16_t reset_tap = m->double_speed ? 0x2000u : 0x1000u; /* P12-M4 */")
set(GBB_P12_REPLACEMENT_4_1 "const uint16_t reset_tap = GBB_P12_MUT(4) ? 0x1000u : (m->double_speed ? 0x2000u : 0x1000u); /* P12-M4 */")
set(GBB_P12_ANCHOR_4_2 "const uint16_t tap = m->double_speed ? 0x2000u : 0x1000u; /* P12-M4 */")
set(GBB_P12_REPLACEMENT_4_2 "const uint16_t tap = GBB_P12_MUT(4) ? 0x1000u : (m->double_speed ? 0x2000u : 0x1000u); /* P12-M4 */")

set(GBB_P12_SITES_11 1)
set(GBB_P12_ANCHOR_11_1 "instance->double_speed ^= 1u; /* P12-M11 */")
set(GBB_P12_REPLACEMENT_11_1 "instance->double_speed ^= 1u; /* P12-M11 */\n            if (GBB_P12_MUT(11)) { instance->divider_phase = 0u; instance->serial_edge_remaining = 0u; instance->dma_phase = 0u; instance->timer_reload_remaining = 0u; }")

set(GBB_P12_SITES_14 2)
set(GBB_P12_ANCHOR_14_1 "if (++m->dma_phase < GBB_T_PER_M) return;")
set(GBB_P12_REPLACEMENT_14_1 "if (++m->dma_phase < (GBB_P12_MUT(14) ? GBB_DMA_BYTE_PERIOD_HALF_DOTS : GBB_T_PER_M)) return;")
set(GBB_P12_ANCHOR_14_2 "if (cpu_tick) dma_advance_half_dot(m); /* P12-M14 */")
set(GBB_P12_REPLACEMENT_14_2 "if (cpu_tick || GBB_P12_MUT(14)) dma_advance_half_dot(m); /* P12-M14 */")

set(GBB_P12_SITES_3 1)
set(GBB_P12_ANCHOR_3_1 "const int cpu_tick = m->double_speed || m->divider_phase == 0u; /* P12-M3 */")
set(GBB_P12_REPLACEMENT_3_1 "const int cpu_tick = GBB_P12_MUT(3) ? ((m->time_half_dots & 1u) == 0u) : (m->double_speed || m->divider_phase == 0u); /* P12-M3 */")

set(GBB_P12_SITES_15 1)
set(GBB_P12_ANCHOR_15_1 "m->timer_reload_remaining = 4u; /* P12-M15 */")
set(GBB_P12_REPLACEMENT_15_1 "m->timer_reload_remaining = GBB_P12_MUT(15) ? 8u : 4u; /* P12-M15 */")

set(GBB_P12_SITES_5 1)
set(GBB_P12_ANCHOR_5_1 "instance->cpu_stall_kind = GBB_STALL_SPEED_SWITCH; /* P12-M5 */")
set(GBB_P12_REPLACEMENT_5_1 "instance->cpu_stall_kind = GBB_STALL_SPEED_SWITCH; /* P12-M5 */\n            if (GBB_P12_MUT(5)) instance->stopped = 1;")

set(GBB_P12_SITES_7 1)
set(GBB_P12_ANCHOR_7_1 "advance_devices(instance, step); /* P12-M7 */")
set(GBB_P12_REPLACEMENT_7_1 "if (GBB_P12_MUT(7)) instance->time_half_dots += step; else advance_devices(instance, step);")

set(GBB_P12_SITES_18 3)
set(GBB_P12_ANCHOR_18_1 "return (uint8_t)(d.ticks >> m->double_speed); /* P12-M18 */ /* instruction-cost */")
set(GBB_P12_REPLACEMENT_18_1 "return GBB_P12_MUT(18) ? d.ticks : (uint8_t)(d.ticks >> m->double_speed); /* P12-M18 */ /* instruction-cost */")
set(GBB_P12_ANCHOR_18_2 "advance_devices_to(m, m->instruction_start_half_dots + (offset >> m->double_speed)); /* P12-M18 */ /* bus-read */")
set(GBB_P12_REPLACEMENT_18_2 "advance_devices_to(m, m->instruction_start_half_dots + (GBB_P12_MUT(18) ? offset : (offset >> m->double_speed))); /* P12-M18 */ /* bus-read */")
set(GBB_P12_ANCHOR_18_3 "uint64_t timestamp = m->instruction_start_half_dots + (offset >> m->double_speed); /* P12-M18 */ /* bus-write */")
set(GBB_P12_REPLACEMENT_18_3 "uint64_t timestamp = m->instruction_start_half_dots + (GBB_P12_MUT(18) ? offset : (offset >> m->double_speed)); /* P12-M18 */ /* bus-write */")

set(GBB_P12_SITES_24 1)
set(GBB_P12_ANCHOR_24_1 "m->double_speed = 0u; /* P12-M24 */")
set(GBB_P12_REPLACEMENT_24_1 "if (GBB_P12_MUT(24) && m->time_half_dots != 0u) { /* speed clear omitted */ } else m->double_speed = 0u; /* P12-M24 */")

set(GBB_P12_SITES_25 2)
set(GBB_P12_ANCHOR_25_1 "m->cpu_stall_kind = GBB_STALL_NONE; /* P12-M25 */")
set(GBB_P12_REPLACEMENT_25_1 "if (!GBB_P12_MUT(25)) m->cpu_stall_kind = GBB_STALL_NONE; /* P12-M25 */")
set(GBB_P12_ANCHOR_25_2 "m->cpu_stall_half_dots = 0u; /* P12-M25 */")
set(GBB_P12_REPLACEMENT_25_2 "if (!GBB_P12_MUT(25)) m->cpu_stall_half_dots = 0u; /* P12-M25 */")

set(GBB_P12_SITES_26 1)
set(GBB_P12_ANCHOR_26_1 "m->key1_armed = 0u; /* P12-M26 */")
set(GBB_P12_REPLACEMENT_26_1 "m->key1_armed = GBB_P12_MUT(26) && m->time_half_dots != 0u ? 1u : 0u; /* P12-M26 */")

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
