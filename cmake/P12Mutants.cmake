# Phase 12 runtime-mask mutant table. Each id owns one or more exact source
# anchors. Keep each anchor and replacement in a separate variable because C
# replacement text may contain semicolons.
set(GBB_P12_MUTANT_IDS 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34)

set(GBB_P12_SITES_13 1)
set(GBB_P12_ANCHOR_13_1 "if (instance->cpu_stall_kind == GBB_STALL_SPEED_SWITCH && wake_pending) { /* P12-M13 */")
set(GBB_P12_REPLACEMENT_13_1 "if (!GBB_P12_MUT(13) && instance->cpu_stall_kind == GBB_STALL_SPEED_SWITCH && wake_pending) { /* P12-M13 */")

set(GBB_P12_SITES_16 1)
set(GBB_P12_ANCHOR_16_1 "const int wake_pending =\n                (instance->ie & instance->interrupt_flags & 0x1Fu) != 0; /* P12-M16 */")
set(GBB_P12_REPLACEMENT_16_1 "const int wake_pending = (!GBB_P12_MUT(16) || result.consumed_half_dots == 0u) &&\n                ((instance->ie & instance->interrupt_flags & 0x1Fu) != 0); /* P12-M16 */")

set(GBB_P12_SITES_34 2)
set(GBB_P12_ANCHOR_34_1 "break; /* P12-M34: STOP must not execute RLCA. */")
set(GBB_P12_REPLACEMENT_34_1 "if (!GBB_P12_MUT(34)) break; /* P12-M34: STOP must not execute RLCA. */")
set(GBB_P12_ANCHOR_34_2 "if (instance->ime_delay != 0 && --instance->ime_delay == 0) instance->ime = 1; /* P12-M34 */")
set(GBB_P12_REPLACEMENT_34_2 "if (instance->ime_delay != 0 && --instance->ime_delay == 0) instance->ime = 1; /* P12-M34 */\n        if (GBB_P12_MUT(34) && instance->stop_switch_pending == 4u) instance->ime = 0;")

set(GBB_P12_SITES_23 1)
set(GBB_P12_ANCHOR_23_1 "if (!model_is_cgb(m) || m->exec_mode != GBB_MODE_CGB ||\n        m->double_speed != 0u || (m->time_half_dots & 7u) != 4u) return; /* P12-M23 */")
set(GBB_P12_REPLACEMENT_23_1 "if (GBB_P12_MUT(23) || !model_is_cgb(m) || m->exec_mode != GBB_MODE_CGB ||\n        m->double_speed != 0u || (m->time_half_dots & 7u) != 4u) return; /* P12-M23 */")

set(GBB_P12_SITES_22 1)
set(GBB_P12_ANCHOR_22_1 "if (!state_time_fits(instance->time_half_dots, switch_headroom)) { /* P12-M22 */")
set(GBB_P12_REPLACEMENT_22_1 "if (!GBB_P12_MUT(22) && !state_time_fits(instance->time_half_dots, switch_headroom)) { /* P12-M22 */")

set(GBB_P12_SITES_9 1)
set(GBB_P12_ANCHOR_9_1 "if (budget_half_dots - result.consumed_half_dots < step) return result; /* P12-M9 */")
set(GBB_P12_REPLACEMENT_9_1 "if (!GBB_P12_MUT(9) && budget_half_dots - result.consumed_half_dots < step) return result; /* P12-M9 */")

set(GBB_P12_SITES_8 1)
set(GBB_P12_ANCHOR_8_1 "if (!model_is_cgb(m) || m->exec_mode != GBB_MODE_CGB || !(m->key1_armed & 1u)) /* P12-M8 */")
set(GBB_P12_REPLACEMENT_8_1 "if (!model_is_cgb(m) || (GBB_P12_MUT(8) ? 0 : m->exec_mode != GBB_MODE_CGB) || !(m->key1_armed & 1u)) /* P12-M8 */")

set(GBB_P12_SITES_10 1)
set(GBB_P12_ANCHOR_10_1 "instance->key1_armed = 0u; /* P12-M10 */")
set(GBB_P12_REPLACEMENT_10_1 "if (!GBB_P12_MUT(10)) instance->key1_armed = 0u; /* P12-M10 */")

set(GBB_P12_SITES_19 1)
set(GBB_P12_ANCHOR_19_1 "const int held = (joypad_value(m) & 0x0Fu) != 0x0Fu; /* P12-M19 */")
set(GBB_P12_REPLACEMENT_19_1 "const int held = GBB_P12_MUT(19) ? 0 : (joypad_value(m) & 0x0Fu) != 0x0Fu; /* P12-M19 */")

set(GBB_P12_SITES_29 1)
set(GBB_P12_ANCHOR_29_1 "? GBB_STOP_SWITCH_COST_HALF_DOTS : 8u), 1};")
set(GBB_P12_REPLACEMENT_29_1 "? (GBB_P12_MUT(29) ? 8u : GBB_STOP_SWITCH_COST_HALF_DOTS) : 8u), 1};")

set(GBB_P12_SITES_30 1)
set(GBB_P12_ANCHOR_30_1 "divider_reset(instance, 0); /* P12-M30 */")
set(GBB_P12_REPLACEMENT_30_1 "divider_reset(instance, GBB_P12_MUT(30) ? 1 : 0); /* P12-M30 */")

set(GBB_P12_SITES_32 1)
set(GBB_P12_ANCHOR_32_1 "if (address == 0xFF4Cu) return; /* D-03: KEY0 never changes speed or mode. P12-M32 */")
set(GBB_P12_REPLACEMENT_32_1 "if (address == 0xFF4Cu) { if (GBB_P12_MUT(32)) m->double_speed ^= 1u; return; } /* D-03: KEY0 never changes speed or mode. P12-M32 */")

set(GBB_P12_SITES_33 1)
set(GBB_P12_ANCHOR_33_1 "m->stop_switch_pending = 4u; /* P12-M33 */")
set(GBB_P12_REPLACEMENT_33_1 "if (!(GBB_P12_MUT(33) && instruction_byte(m, pc, 1) == 0xFFu)) m->stop_switch_pending = 4u; /* P12-M33 */")

set(GBB_P12_SITES_20 1)
set(GBB_P12_ANCHOR_20_1 "const int pending = (m->ie & m->interrupt_flags & 0x1Fu) != 0; /* P12-M20 */")
set(GBB_P12_REPLACEMENT_20_1 "const int pending = GBB_P12_MUT(20) ? 0 : ((m->ie & m->interrupt_flags & 0x1Fu) != 0); /* P12-M20 */")

set(GBB_P12_SITES_27 1)
set(GBB_P12_ANCHOR_27_1 "divider_reset(instance, 1); /* P12-M27 */")
set(GBB_P12_REPLACEMENT_27_1 "if (!GBB_P12_MUT(27)) divider_reset(instance, 1); /* P12-M27 */")

set(GBB_P12_SITES_1 1)
set(GBB_P12_ANCHOR_1_1 "m->ppu_half_phase ^= 1u; /* P12-M1 */")
set(GBB_P12_REPLACEMENT_1_1 "m->ppu_half_phase ^= 1u; /* P12-M1 */\n        if (GBB_P12_MUT(1) && m->double_speed) ppu_advance_dot(m);")

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

set(GBB_P12_SITES_12 1)
set(GBB_P12_ANCHOR_12_1 "const uint64_t secs = (el >> RTC_HALF_DOTS_PER_SECOND_SHIFT) +")
set(GBB_P12_REPLACEMENT_12_1 "const unsigned double_speed = GBB_P12_MUT(12);\n    const uint64_t secs = (el >> (RTC_HALF_DOTS_PER_SECOND_SHIFT + double_speed)) +")

set(GBB_P12_SITES_14 2)
set(GBB_P12_ANCHOR_14_1 "if (++m->dma_phase < GBB_T_PER_M) return;")
set(GBB_P12_REPLACEMENT_14_1 "if (++m->dma_phase < (GBB_P12_MUT(14) ? GBB_DMA_BYTE_PERIOD_HALF_DOTS : GBB_T_PER_M)) return;")
set(GBB_P12_ANCHOR_14_2 "if (cpu_tick) dma_advance_half_dot(m); /* P12-M14 */")
set(GBB_P12_REPLACEMENT_14_2 "if (cpu_tick || GBB_P12_MUT(14)) dma_advance_half_dot(m); /* P12-M14 */")

set(GBB_P12_SITES_17 1)
set(GBB_P12_ANCHOR_17_1 "if (pulse->timer > 1u) --pulse->timer; /* P12-M17 */")
set(GBB_P12_REPLACEMENT_17_1 "if (GBB_P12_MUT(17) && m->double_speed && pulse->timer > 1u) --pulse->timer;\n                if (pulse->timer > 1u) --pulse->timer; /* P12-M17 */")

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

set(GBB_P12_SITES_6 1)
set(GBB_P12_ANCHOR_6_1 "instance->cpu_stall_half_dots = GBB_SPEED_SWITCH_STALL_T *\n                    (instance->double_speed ? GBB_HALF_DOTS_PER_T_DOUBLE : GBB_HALF_DOTS_PER_T_NORMAL); /* P12-M6 */")
set(GBB_P12_REPLACEMENT_6_1 "instance->cpu_stall_half_dots = (uint32_t)(((int64_t)GBB_SPEED_SWITCH_STALL_T +\n                    (GBB_P12_MUT(6) ? (int64_t)GBB_T_PER_M : 0) -\n                    (GBB_P12_MUT(21) ? (int64_t)GBB_T_PER_M : 0) +\n                    (GBB_P12_MUT(31) ? (int64_t)gbb_p12_stall_offset_t : 0)) *\n                    (instance->double_speed ? GBB_HALF_DOTS_PER_T_DOUBLE : GBB_HALF_DOTS_PER_T_NORMAL)) +\n                    (GBB_P12_MUT(28) ? 1u : 0u); /* P12-M6 */")
set(GBB_P12_SITES_21 1)
set(GBB_P12_ANCHOR_21_1 "(GBB_P12_MUT(21) ? (int64_t)GBB_T_PER_M : 0)")
set(GBB_P12_REPLACEMENT_21_1 "(GBB_P12_MUT(21) ? (int64_t)GBB_T_PER_M : 0)")
set(GBB_P12_SITES_28 1)
set(GBB_P12_ANCHOR_28_1 "(GBB_P12_MUT(28) ? 1u : 0u)")
set(GBB_P12_REPLACEMENT_28_1 "(GBB_P12_MUT(28) && instance->double_speed ? 1u : 0u)")
set(GBB_P12_SITES_31 1)
set(GBB_P12_ANCHOR_31_1 "(GBB_P12_MUT(31) ? (int64_t)gbb_p12_stall_offset_t : 0)")
set(GBB_P12_REPLACEMENT_31_1 "(GBB_P12_MUT(31) ? (int64_t)gbb_p12_stall_offset_t : 0)")

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

function(gbb_p12_require_unique_anchor core_text anchor label source_path)
  string(FIND "${core_text}" "${anchor}" first)
  string(FIND "${core_text}" "${anchor}" final REVERSE)
  if(first EQUAL -1 OR NOT first EQUAL final)
    message(FATAL_ERROR "${label}: anchor '${anchor}' must occur exactly once in ${source_path} (first=${first} last=${final})")
  endif()
endfunction()

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
      gbb_p12_require_unique_anchor("${core_text}" "${anchor}"
        "p12 mutant M${id} site ${site}" "${core_path}")
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
