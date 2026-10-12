set(GBB_TEST_INSTALL_PREFIX "" CACHE PATH "Relocated install prefix used by installed-package smoke tests")
include(${PROJECT_SOURCE_DIR}/cmake/ExpectedTests.cmake)

add_executable(test_api test_api.c)
target_link_libraries(test_api PRIVATE GabbaBoy::core)
target_compile_features(test_api PRIVATE c_std_17)
set_target_properties(test_api PROPERTIES C_EXTENSIONS OFF)
add_test(NAME instance_lifecycle COMMAND test_api instance_lifecycle ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME independent_instances COMMAND test_api independent_instances ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME reset_idempotency COMMAND test_api reset_idempotency ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME run_bounds COMMAND test_api run_bounds ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME trace_capacity COMMAND test_api trace_capacity ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME illegal_lockup_api COMMAND test_api illegal_lockup ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)

find_package(Threads REQUIRED)
add_executable(test_instance_concurrency test_instance_concurrency.c)
target_link_libraries(test_instance_concurrency PRIVATE GabbaBoy::core Threads::Threads)
target_compile_features(test_instance_concurrency PRIVATE c_std_17)
set_target_properties(test_instance_concurrency PROPERTIES C_EXTENSIONS OFF)
add_test(NAME concurrent_independent_instances COMMAND test_instance_concurrency
  ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME cgb_instance_isolation COMMAND test_instance_concurrency
  ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb cgb_instance_isolation)

add_executable(test_cartridge test_cartridge.c)
target_link_libraries(test_cartridge PRIVATE GabbaBoy::core)
target_compile_features(test_cartridge PRIVATE c_std_17)
set_target_properties(test_cartridge PROPERTIES C_EXTENSIONS OFF)
add_test(NAME cartridge_tracer COMMAND test_cartridge cartridge_tracer)
add_test(NAME cartridge_bank_matrix COMMAND test_cartridge cartridge_bank_matrix)
add_test(NAME cartridge_ram_banks COMMAND test_cartridge cartridge_ram_banks)
add_test(NAME cartridge_no_ram_reads COMMAND test_cartridge cartridge_no_ram_reads)

add_executable(test_mbc2 test_mbc2.c)
target_link_libraries(test_mbc2 PRIVATE GabbaBoy::core)
target_compile_features(test_mbc2 PRIVATE c_std_17)
set_target_properties(test_mbc2 PROPERTIES C_EXTENSIONS OFF)
foreach(case tracer header_matrix register_decode ram_echo reset
  battery_image battery_import battery_idempotent battery_errors battery_no_battery
  two_instance_roundtrip)
  add_test(NAME mbc2_${case} COMMAND test_mbc2 mbc2_${case})
endforeach()

add_executable(test_mbc3 test_mbc3.c)
target_link_libraries(test_mbc3 PRIVATE GabbaBoy::core)
target_compile_features(test_mbc3 PRIVATE c_std_17)
set_target_properties(test_mbc3 PROPERTIES C_EXTENSIONS OFF)
foreach(case tracer header_matrix rom_banking ram_banking ram_gate unmapped_select
  absent_ram reset battery_generation)
  add_test(NAME mbc3_${case} COMMAND test_mbc3 mbc3_${case})
endforeach()

add_executable(test_mbc3_rtc test_mbc3_rtc.c)
target_link_libraries(test_mbc3_rtc PRIVATE GabbaBoy::core)
target_compile_features(test_mbc3_rtc PRIVATE c_std_17)
set_target_properties(test_mbc3_rtc PROPERTIES C_EXTENSIONS OFF)
foreach(case tracer gate_and_select load_fresh)
  add_test(NAME rtc_${case} COMMAND test_mbc3_rtc rtc_${case})
endforeach()

# White-box: includes src/core/gabbaboy.c (or a mutant copy named by GBB_CORE_SOURCE_PATH),
# so it must not link the core library (duplicate definitions).
add_executable(test_mbc3_rtc_internal test_mbc3_rtc_internal.c)
target_include_directories(test_mbc3_rtc_internal PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_mbc3_rtc_internal PRIVATE c_std_17)
set_target_properties(test_mbc3_rtc_internal PROPERTIES C_EXTENSIONS OFF)
foreach(case closed_form_differential add_composes rate_exact prescaler_rules write_masks out_of_range_rollover day_carry_sticky halt_freezes latch_edges generation_rules time_near_max reset_rebase slice_invariance cpu_independence)
  add_test(NAME rtc_${case} COMMAND test_mbc3_rtc_internal rtc_${case})
endforeach()

# RTC mutation controls (D-12). Each mutant is a copy of src/core/gabbaboy.c written into the build
# tree with one plausible RTC mistake, built into the white-box test through GBB_CORE_SOURCE_PATH.
# Every anchor is the full tagged statement line from Plan 09-09 and must occur exactly once; the
# mutant must then fail its named original case (exit 1, REQUIRE text) while an unrelated case
# still passes inside the same mutant (exit 0), so a mutant that is merely broken cannot pass.
# GBB_CORE_SOURCE_PATH is the only channel: test_mbc3_rtc_internal.c includes whatever file it names,
# so each mutant executable differs from the real white-box test by that one definition.
# Test-only: nothing here is installed or exported.
set(GBB_RTC_CORE_SOURCE ${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c)
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${GBB_RTC_CORE_SOURCE})
file(READ ${GBB_RTC_CORE_SOURCE} gbb_rtc_core_text)

set(GBB_ANCHOR_SEC_WRITE
  "c->rtc_sub = 0u; /* rtc: a seconds write restarts the sub-second prescaler */")
set(GBB_ANCHOR_OTHER_WRITES
  "if (reg >= 1u && reg <= 3u) c->rtc_sub = sub_before; /* rtc: other register writes keep the prescaler */")
set(GBB_ANCHOR_HALT_TOGGLE
  "if (reg == 4u) c->rtc_sub = sub_before; /* rtc: a halt toggle keeps the prescaler */")
set(GBB_ANCHOR_STORE_S
  "c->rtc_s = (uint8_t)(value & 0x3Fu); /* rtc: out-of-range fields are stored as written */")
set(GBB_ANCHOR_STORE_M "case 1u: c->rtc_m = (uint8_t)(value & 0x3Fu); break;")
set(GBB_ANCHOR_STORE_H "case 2u: c->rtc_h = (uint8_t)(value & 0x1Fu); break;")
set(GBB_ANCHOR_LATCH
  "const int latch_now = c->rtc_latch_prev == 0x00u && value == 0x01u; /* rtc: latch only on 00 then 01 */")

# gbb_rtc_mutant(<name> <failing-case> <regex> <control-case> <anchor1> <replacement1> [<anchor2> <replacement2> ...])
# Arguments are read through ARGV so the semicolons in the C text never become list separators.
function(gbb_rtc_mutant name failing_case failing_regex control_case)
  set(text "${gbb_rtc_core_text}")
  math(EXPR last "${ARGC} - 1")
  foreach(i RANGE 4 ${last} 2)
    math(EXPR j "${i} + 1")
    set(anchor "${ARGV${i}}")
    set(replacement "${ARGV${j}}")
    string(FIND "${text}" "${anchor}" first)
    string(FIND "${text}" "${anchor}" final REVERSE)
    if(first EQUAL -1 OR NOT first EQUAL final)
      message(FATAL_ERROR "RTC mutant ${name}: anchor '${anchor}' must occur exactly once in "
        "${GBB_RTC_CORE_SOURCE} (first=${first} last=${final})")
    endif()
    string(REPLACE "${anchor}" "${replacement}" text "${text}")
  endforeach()
  set(source ${CMAKE_CURRENT_BINARY_DIR}/rtc_mutant_${name}.c)
  file(WRITE ${source} "${text}")
  set(target test_rtc_mutant_${name})
  add_executable(${target} test_mbc3_rtc_internal.c)
  target_include_directories(${target} PRIVATE "${PROJECT_SOURCE_DIR}/include")
  target_compile_features(${target} PRIVATE c_std_17)
  set_target_properties(${target} PROPERTIES C_EXTENSIONS OFF)
  # The absolute build-tree path of this mutant's source, quoted for the preprocessor.
  # (GBB_CORE_SOURCE_PATH)
  target_compile_definitions(${target} PRIVATE GBB_CORE_SOURCE_PATH="${source}")
  add_test(NAME rtc_mutant_${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=$<TARGET_FILE:${target}>;${failing_case}"
      -DGBB_EXPECT_CODE=1
      "-DGBB_EXPECT_REGEX=${failing_regex}"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  add_test(NAME rtc_mutant_${name}_control
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=$<TARGET_FILE:${target}>;${control_case}"
      -DGBB_EXPECT_CODE=0
      "-DGBB_EXPECT_REGEX=.*"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
endfunction()

gbb_rtc_mutant(prescaler_kept rtc_prescaler_rules "rreg.m, 0u. == 0u" rtc_write_masks
  "${GBB_ANCHOR_SEC_WRITE}"
  "c->rtc_sub = sub_before; /* mutant: a seconds write keeps the prescaler */")
gbb_rtc_mutant(prescaler_reset_every_write rtc_prescaler_rules "rreg.m, 0u. == 1u" rtc_write_masks
  "${GBB_ANCHOR_OTHER_WRITES}"
  "if (reg >= 1u && reg <= 3u) c->rtc_sub = 0u; /* mutant: M, H and DL writes restart the prescaler */"
  "${GBB_ANCHOR_HALT_TOGGLE}"
  "if (reg == 4u) c->rtc_sub = 0u; /* mutant: a halt toggle restarts the prescaler */")
gbb_rtc_mutant(prescaler_reset_on_halt rtc_prescaler_rules "rreg.m, 0u. == 1u" rtc_write_masks
  "${GBB_ANCHOR_HALT_TOGGLE}"
  "if (reg == 4u) c->rtc_sub = 0u; /* mutant: a halt toggle restarts the prescaler */")
gbb_rtc_mutant(out_of_range_clamped rtc_out_of_range_rollover ".out.[[]1[]] == .5u." rtc_rate_exact
  "${GBB_ANCHOR_STORE_S}"
  "c->rtc_s = (uint8_t)((value & 0x3Fu) > 59u ? 59u : (value & 0x3Fu)); /* mutant: clamp */"
  "${GBB_ANCHOR_STORE_M}"
  "case 1u: c->rtc_m = (uint8_t)((value & 0x3Fu) > 59u ? 59u : (value & 0x3Fu)); break;"
  "${GBB_ANCHOR_STORE_H}"
  "case 2u: c->rtc_h = (uint8_t)((value & 0x1Fu) > 23u ? 23u : (value & 0x1Fu)); break;")
gbb_rtc_mutant(latch_any_write rtc_latch_edges "rreg.m, 0u. == cases.i..expect" rtc_write_masks
  "${GBB_ANCHOR_LATCH}"
  "const int latch_now = 1; /* mutant: latch on any write */")

add_executable(test_rtc_battery test_rtc_battery.c)
target_link_libraries(test_rtc_battery PRIVATE GabbaBoy::core)
target_compile_features(test_rtc_battery PRIVATE c_std_17)
set_target_properties(test_rtc_battery PROPERTIES C_EXTENSIONS OFF)
foreach(case block_roundtrip catch_up_basic catch_up_zero catch_up_negative catch_up_int64_max
  catch_up_halted catch_up_carry_sticky catch_up_composes catch_up_preserves catch_up_errors
  import_never_advances block_corruption_matrix block_reset_roundtrip block_generation
  battery_size_types)
  add_test(NAME rtc_${case} COMMAND test_rtc_battery rtc_${case})
endforeach()

# Pure host policy compiled directly; no player library, SDL or clock (D-21).
add_executable(test_catch_up_policy test_catch_up_policy.c
  "${PROJECT_SOURCE_DIR}/src/player/catch_up_policy.c")
target_include_directories(test_catch_up_policy PRIVATE "${PROJECT_SOURCE_DIR}/src/player")
target_compile_features(test_catch_up_policy PRIVATE c_std_17)
set_target_properties(test_catch_up_policy PROPERTIES C_EXTENSIONS OFF)
add_test(NAME catch_up_policy_table COMMAND test_catch_up_policy catch_up_policy_table)

add_executable(test_mbc5 test_mbc5.c)
target_link_libraries(test_mbc5 PRIVATE GabbaBoy::core)
target_compile_features(test_mbc5 PRIVATE c_std_17)
set_target_properties(test_mbc5 PROPERTIES C_EXTENSIONS OFF)
foreach(case tracer header_matrix rom_banking ram_enable ram_banking no_ram_window
  battery rom_bound cgb_flag_ignored cross_mapper_control
  rumble_state rumble_errors rumble_reset_load reset_preserves_ram)
  add_test(NAME mbc5_${case} COMMAND test_mbc5 mbc5_${case})
endforeach()

# White-box: the test includes src/core/gabbaboy.c itself, so it must not link
# the core library (duplicate definitions).
add_executable(test_mbc5_internal test_mbc5_internal.c)
target_include_directories(test_mbc5_internal PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_mbc5_internal PRIVATE c_std_17)
set_target_properties(test_mbc5_internal PROPERTIES C_EXTENSIONS OFF)
add_test(NAME mbc5_rumble_saturation COMMAND test_mbc5_internal mbc5_rumble_saturation)

# White-box banking checks (D-19): single TU including the core source, so no GabbaBoy::core link.
add_executable(test_banking_internal test_banking_internal.c)
target_include_directories(test_banking_internal PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_banking_internal PRIVATE c_std_17)
set_target_properties(test_banking_internal PROPERTIES C_EXTENSIONS OFF)
foreach(case dmg_flat_reference cgb_diverges_from_flat dmg_bank_pins_after_reset)
  add_test(NAME banking_${case} COMMAND test_banking_internal banking_${case})
endforeach()
# The reshape must not move the DMG correctness digest of the tracer fixture.
add_test(NAME banking_tracer_digest_unchanged
  COMMAND measure_core --no-trace ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
set_tests_properties(banking_tracer_digest_unchanged PROPERTIES
  PASS_REGULAR_EXPRESSION "correctness_digest_fnv1a64=4c7a57ff3d50d228")

# Public-API banking, echo and OAM DMA source cases (Plan 10-12; D-15, D-16, D-17).
add_executable(test_banking test_banking.c)
target_link_libraries(test_banking PRIVATE GabbaBoy::core)
target_compile_features(test_banking PRIVATE c_std_17)
set_target_properties(test_banking PROPERTIES C_EXTENSIONS OFF)
foreach(case dma_wram_bank vbk_independence svbk_readback echo_follows_bank dma_vram_bank
  dma_rom_page dma_high_pages dma_cart_ram dmg_banks_frozen bus_conflict_cgb_pin)
  add_test(NAME banking_${case} COMMAND test_banking ${case})
endforeach()

# Original CGB banking fixture (Plan 10-13; D-18). The guests are checked-in, digest-verified ROMs.
set(GBB_CGB_BANKING_DIR "${PROJECT_SOURCE_DIR}/fixtures/cgb-banking")
add_test(NAME cgb_banking_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DMANIFEST=${GBB_CGB_BANKING_DIR}/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixtureManifest.cmake)
foreach(case cgb_banking_guest_cgb cgb_banking_guest_compat cgb_banking_guest_dmg
  cgb_banking_patched_expected cgb_banking_cgb_on_dmg cgb_banking_skip_svbk)
  add_test(NAME ${case} COMMAND test_banking ${case} ${GBB_CGB_BANKING_DIR})
endforeach()

# Core mutants for the banking cases (D-19). Each is a configure-time copy of the core with one
# exactly-once source anchor rewritten, built as a test-only STATIC library (never installed or
# exported) and linked to its own copy of test_banking. The failing case must exit 1 at its named
# REQUIRE, and an unrelated case must still exit 0 in the same mutant so the mutant is shown to be
# otherwise functional. The anchor is checked forward and in reverse so a drifted core fails the
# configure step instead of silently disabling the control.
set(GBB_BANKING_CORE_SOURCE ${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c)
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${GBB_BANKING_CORE_SOURCE})
file(READ ${GBB_BANKING_CORE_SOURCE} gbb_banking_core_text)
function(gbb_banking_mutant name fail_test control_test anchor replacement failing_case failing_regex control_case)
  string(FIND "${gbb_banking_core_text}" "${anchor}" first)
  string(FIND "${gbb_banking_core_text}" "${anchor}" final REVERSE)
  if(first EQUAL -1 OR NOT first EQUAL final)
    message(FATAL_ERROR "banking mutant ${name}: anchor '${anchor}' must occur exactly once in "
      "${GBB_BANKING_CORE_SOURCE} (first=${first} last=${final})")
  endif()
  # The core text carries semicolons, so it stays quoted and never enters a list operation.
  string(REPLACE "${anchor}" "${replacement}" text "${gbb_banking_core_text}")
  set(source ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_banking_mutant_${name}.c)
  file(WRITE ${source} "${text}")
  set(library gabbaboy_core_banking_mutant_${name})
  add_library(${library} STATIC ${source})
  target_include_directories(${library} PUBLIC ${PROJECT_SOURCE_DIR}/include)
  target_compile_features(${library} PUBLIC c_std_17)
  set_target_properties(${library} PROPERTIES C_EXTENSIONS OFF)
  target_compile_definitions(${library} PRIVATE
    GBB_BUILD_REVISION="banking-mutant-${name}" GBB_BUILD_QUALIFIED=0)
  set(target test_banking_mutant_${name})
  add_executable(${target} test_banking.c)
  target_link_libraries(${target} PRIVATE ${library})
  target_compile_features(${target} PRIVATE c_std_17)
  set_target_properties(${target} PROPERTIES C_EXTENSIONS OFF)
  add_test(NAME ${fail_test}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=$<TARGET_FILE:${target}>;${failing_case}"
      -DGBB_EXPECT_CODE=1
      "-DGBB_EXPECT_REGEX=${failing_regex}"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  add_test(NAME ${control_test}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=$<TARGET_FILE:${target}>;${control_case}"
      -DGBB_EXPECT_CODE=0
      "-DGBB_EXPECT_REGEX=.*"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
endfunction()

# Echo mutant: F000-FDFF ignores SVBK and always lands in bank 1, while D000-DFFF stays banked.
gbb_banking_mutant(echo banking_mutant_echo_ignores_bank banking_mutant_echo_control
  "unsigned bank = offset < GBB_WRAM_BANK_SIZE ? 0u : m->wram_bank;"
  "unsigned bank = offset < GBB_WRAM_BANK_SIZE ? 0u : (address >= 0xF000u ? 1u : m->wram_bank);"
  echo_follows_bank "echo_reads_match" vbk_independence)
# DMA mutant: the CGB OAM DMA D0-DF page reads bank 1 whatever SVBK says; the CPU path is untouched.
gbb_banking_mutant(dma banking_mutant_dma_wrong_bank banking_mutant_dma_control
  "return *wram_byte(m, address);\n        return 0xFFu;"
  "return m->wram[address < 0xD000u ? 0u : 1u][address & (GBB_WRAM_BANK_SIZE - 1u)];\n        return 0xFFu;"
  dma_wram_bank "oam_is_pattern.m, 0x20." svbk_readback)

# Original banking guest (D-33): the committed 64 KiB ROM is run through the real CPU and bus.
add_test(NAME mbc5_banking_guest
  COMMAND test_mbc5 mbc5_banking_guest ${PROJECT_SOURCE_DIR}/fixtures/mbc5-banking/banking.gb)
# In-memory variants (never written to disk): $1B non-rumble type, and the 8 MiB bank $1FF inflation.
add_test(NAME mbc5_banking_guest_1b
  COMMAND test_mbc5 mbc5_banking_guest_1b ${PROJECT_SOURCE_DIR}/fixtures/mbc5-banking/banking.gb)
add_test(NAME mbc5_bank_1ff
  COMMAND test_mbc5 mbc5_bank_1ff ${PROJECT_SOURCE_DIR}/fixtures/mbc5-banking/banking.gb)

# Ninth-bit core mutant (D-29, amended): a copy of the core whose MBC5 ROM bank composition keeps
# `& 0u` of the high bank register instead of `& 1u`, so banks $100 and above alias $00-$FF. The
# Mooneye mbc5 harness stops at bank $FF and cannot see this, so the discriminator is the original
# mbc5_bank_1ff case. Same configure-time, exactly-once anchor discipline as the JOYP mutant in
# tests/acceptance; the library and executable are test-only and never installed or exported.
set(GBB_NINTH_SOURCE ${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c)
set(GBB_NINTH_PATTERN "& 1u) << 8")
set(GBB_NINTH_REPLACEMENT "& 0u) << 8")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${GBB_NINTH_SOURCE})
file(READ ${GBB_NINTH_SOURCE} gbb_ninth_core_text)
string(FIND "${gbb_ninth_core_text}" "${GBB_NINTH_PATTERN}" gbb_ninth_first)
string(FIND "${gbb_ninth_core_text}" "${GBB_NINTH_PATTERN}" gbb_ninth_last REVERSE)
if(gbb_ninth_first EQUAL -1 OR NOT gbb_ninth_first EQUAL gbb_ninth_last)
  message(FATAL_ERROR "ninth-bit mutant pattern '${GBB_NINTH_PATTERN}' must occur exactly once in "
    "${GBB_NINTH_SOURCE} (first=${gbb_ninth_first} last=${gbb_ninth_last})")
endif()
# The core text carries semicolons, so it stays quoted and never enters a list operation.
string(REPLACE "${GBB_NINTH_PATTERN}" "${GBB_NINTH_REPLACEMENT}" gbb_ninth_text "${gbb_ninth_core_text}")
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_ninth_bit_mutant.c "${gbb_ninth_text}")

add_library(gabbaboy_core_ninth_bit_mutant STATIC ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_ninth_bit_mutant.c)
target_include_directories(gabbaboy_core_ninth_bit_mutant PUBLIC ${PROJECT_SOURCE_DIR}/include)
target_compile_features(gabbaboy_core_ninth_bit_mutant PUBLIC c_std_17)
set_target_properties(gabbaboy_core_ninth_bit_mutant PROPERTIES C_EXTENSIONS OFF)
target_compile_definitions(gabbaboy_core_ninth_bit_mutant PRIVATE
  GBB_BUILD_REVISION="ninth-bit-mutant" GBB_BUILD_QUALIFIED=0)

add_executable(test_mbc5_ninth_bit_mutant test_mbc5.c)
target_link_libraries(test_mbc5_ninth_bit_mutant PRIVATE gabbaboy_core_ninth_bit_mutant)
target_compile_features(test_mbc5_ninth_bit_mutant PRIVATE c_std_17)
set_target_properties(test_mbc5_ninth_bit_mutant PROPERTIES C_EXTENSIONS OFF)

# The mutant must be caught at the C005 bank $1FF assertion specifically (exit 1, the REQUIRE text).
add_test(NAME mbc5_ninth_bit_mutant_bank_1ff
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_mbc5_ninth_bit_mutant>;mbc5_bank_1ff;${PROJECT_SOURCE_DIR}/fixtures/mbc5-banking/banking.gb"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=r.3. == 0x01u"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
# In-mutant control: the same guest on its committed 64 KiB image never selects a bank at or above
# $100, so the mutant core still passes it (exit 0), which shows the mutant is not simply broken.
add_test(NAME mbc5_ninth_bit_mutant_control_below_100
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_mbc5_ninth_bit_mutant>;mbc5_banking_guest;${PROJECT_SOURCE_DIR}/fixtures/mbc5-banking/banking.gb"
    -DGBB_EXPECT_CODE=0
    "-DGBB_EXPECT_REGEX=.*"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

# Loader contradiction matrix (CART-05, D-27): independent expected-result oracle, guard instance
# and untouched twin checked after every rejection.
add_executable(test_loader_matrix test_loader_matrix.c)
target_link_libraries(test_loader_matrix PRIVATE GabbaBoy::core)
target_compile_features(test_loader_matrix PRIVATE c_std_17)
set_target_properties(test_loader_matrix PROPERTIES C_EXTENSIONS OFF)
foreach(case contradiction_mbc2 contradiction_mbc3 contradiction_mbc5 mbc30_variant type_byte_sweep bad_checksum)
  add_test(NAME loader_${case} COMMAND test_loader_matrix loader_${case})
endforeach()
add_test(NAME cgb_loader_matrix COMMAND test_loader_matrix cgb_loader_matrix)

add_executable(test_battery test_battery.c)
target_link_libraries(test_battery PRIVATE GabbaBoy::core)
target_compile_features(test_battery PRIVATE c_std_17)
set_target_properties(test_battery PROPERTIES C_EXTENSIONS OFF)
foreach(case roundtrip8 roundtrip32 errors no_battery lifecycle instances)
  add_test(NAME battery_${case} COMMAND test_battery battery_${case})
endforeach()

add_executable(test_battery_fuzz test_battery_fuzz.c)
target_link_libraries(test_battery_fuzz PRIVATE GabbaBoy::core)
target_compile_features(test_battery_fuzz PRIVATE c_std_17)
set_target_properties(test_battery_fuzz PROPERTIES C_EXTENSIONS OFF)
add_test(NAME battery_api_fuzz COMMAND test_battery_fuzz)

add_executable(test_bus test_bus.c)
target_link_libraries(test_bus PRIVATE GabbaBoy::core)
target_compile_features(test_bus PRIVATE c_std_17)
set_target_properties(test_bus PROPERTIES C_EXTENSIONS OFF)
foreach(case wram_guest echo_hram absent_cart preflight unsupported_reads unsupported_stack unsupported_fetch halt_bug_fetch)
  add_test(NAME bus_${case} COMMAND test_bus ${case})
endforeach()

add_executable(test_cgb_visibility test_cgb_visibility.c)
target_link_libraries(test_cgb_visibility PRIVATE GabbaBoy::core)
target_compile_features(test_cgb_visibility PRIVATE c_std_17)
set_target_properties(test_cgb_visibility PROPERTIES C_EXTENSIONS OFF)
foreach(case vbk_tracer svbk_select unmapped_cgb boundaries deferred_stop ie_gate deferred_latch_interrupt
     matrix_compat flip_control matrix_cgb matrix_dmg cross_column_control sweep_control)
  add_test(NAME cgb_visibility_${case} COMMAND test_cgb_visibility ${case})
endforeach()
# Plan 10-11: STOP/KEY1 fail-closed and the KEY0 lock keep their plan-named CTests.
foreach(case stop_armed_cgb stop_unarmed_cgb stop_compat_ignores_key1 stop_dmg_control
     key0_lock_cgb key0_lock_compat key0_lock_cross_column key0_lock_reset_idempotent)
  add_test(NAME cgb_${case} COMMAND test_cgb_visibility ${case})
endforeach()

add_executable(test_cgb_postboot test_cgb_postboot.c)
target_link_libraries(test_cgb_postboot PRIVATE GabbaBoy::core)
target_compile_features(test_cgb_postboot PRIVATE c_std_17)
set_target_properties(test_cgb_postboot PROPERTIES C_EXTENSIONS OFF)
add_test(NAME cgb_postboot_dmg_pin COMMAND test_cgb_postboot dmg_pin)
add_test(NAME cgb_postboot_dmg_pin_checksum_zero COMMAND test_cgb_postboot dmg_pin_checksum_zero)
# Negative controls: one flipped CPU field (F, index 1) and one flipped I/O field
# (NR12, index 10 + 12); each must fail with exit 1 naming the field.
add_test(NAME cgb_postboot_dmg_pin_flipped
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_postboot>;dmg_pin;--flip;1"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=post-boot mismatch: F "
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
add_test(NAME cgb_postboot_dmg_pin_flipped_io
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_postboot>;dmg_pin;--flip;22"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=post-boot mismatch: NR12 "
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

foreach(case cgb_cpu_tracer compat_cpu compat_no_rom compat_title_sum compat_io cgb_io ch1_silent)
  add_test(NAME cgb_postboot_${case} COMMAND test_cgb_postboot ${case})
endforeach()
# White-box: includes src/core/gabbaboy.c itself, so it must not link GabbaBoy::core.
add_executable(test_cgb_postboot_internal test_cgb_postboot_internal.c)
target_include_directories(test_cgb_postboot_internal PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_cgb_postboot_internal PRIVATE c_std_17)
set_target_properties(test_cgb_postboot_internal PROPERTIES C_EXTENSIONS OFF)
foreach(case div_phase_sweep div_compat_default)
  add_test(NAME cgb_postboot_${case} COMMAND test_cgb_postboot_internal ${case})
endforeach()
# A1: the same DIV-phase sweep on the real derived boot_div-cgbABCDE ROM (callback and result PCs from the
# manifest). White-box like the sweep above, so it must not link GabbaBoy::core either.
add_executable(test_mooneye_cgb_div_sweep test_mooneye_cgb_div_sweep.c)
target_include_directories(test_mooneye_cgb_div_sweep PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_mooneye_cgb_div_sweep PRIVATE c_std_17)
set_target_properties(test_mooneye_cgb_div_sweep PROPERTIES C_EXTENSIONS OFF)
add_test(NAME cgb_postboot_div_real_rom_sweep
  COMMAND test_mooneye_cgb_div_sweep ${PROJECT_SOURCE_DIR}/fixtures/mooneye-cgb/boot_div-cgbABCDE.gb 4000 4327)
set_tests_properties(cgb_postboot_div_real_rom_sweep PROPERTIES TIMEOUT 60
  PASS_REGULAR_EXPRESSION "ok 2 - passing set is exactly 0x2678..0x267B for both divider phases")
# Negative control: asserting the window one counter later must fail naming the observed set, so a drifted
# table cell cannot pass silently.
add_test(NAME cgb_postboot_div_real_rom_sweep_shifted
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_mooneye_cgb_div_sweep>;${PROJECT_SOURCE_DIR}/fixtures/mooneye-cgb/boot_div-cgbABCDE.gb;4000;4327;--expect-first;2679"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=passing set mismatch: phase 0 observed mask 0xF00"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(cgb_postboot_div_real_rom_sweep_shifted PROPERTIES TIMEOUT 60)
# Negative controls: a flipped NR52 expectation (index 8) must fail naming the field.
foreach(case compat_io cgb_io)
  add_test(NAME cgb_postboot_${case}_flipped
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=$<TARGET_FILE:test_cgb_postboot>;${case};--flip;8"
      -DGBB_EXPECT_CODE=1
      "-DGBB_EXPECT_REGEX=post-boot mismatch: NR52 "
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
endforeach()

# CGB profile API (CGB-01): probe/info contract, the $143 x profile matrix, the PGB rejection and
# probe/load parity with a skewed-validator negative control.
add_executable(test_cgb_profile test_cgb_profile.c)
target_link_libraries(test_cgb_profile PRIVATE GabbaBoy::core)
target_compile_features(test_cgb_profile PRIVATE c_std_17)
set_target_properties(test_cgb_profile PROPERTIES C_EXTENSIONS OFF)
foreach(case probe_tracer info_no_rom info_after_load info_reset_constant info_failed_load_unchanged
             info_struct_size cgb_only_on_dmg probe_matrix probe_pgb probe_parity profile_unknown
             probe_args profile_create copy_frame_cgb)
  add_test(NAME cgb_${case} COMMAND test_cgb_profile ${case})
endforeach()

add_executable(test_timer test_timer.c)
target_link_libraries(test_timer PRIVATE GabbaBoy::core)
target_compile_features(test_timer PRIVATE c_std_17)
set_target_properties(test_timer PROPERTIES C_EXTENSIONS OFF)
foreach(case guest_overflow mid_instruction selectors div_write tac_write tima_collision tma_collision)
  add_test(NAME timer_${case} COMMAND test_timer ${case})
endforeach()

add_executable(test_audio test_audio.c)
target_link_libraries(test_audio PRIVATE GabbaBoy::core)
target_compile_features(test_audio PRIVATE c_std_17)
set_target_properties(test_audio PROPERTIES C_EXTENSIONS OFF)
foreach(case tracer capacity signal fractional_edges partition filter
             rounding saturation api_edges)
  add_test(NAME audio_${case} COMMAND test_audio audio_${case})
endforeach()

add_library(gabbaboy_core_alloc_probe OBJECT "${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c")
target_include_directories(gabbaboy_core_alloc_probe PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(gabbaboy_core_alloc_probe PRIVATE c_std_17)
target_compile_definitions(gabbaboy_core_alloc_probe PRIVATE
  malloc=gbb_test_malloc calloc=gbb_test_calloc
  realloc=gbb_test_realloc free=gbb_test_free)
set_target_properties(gabbaboy_core_alloc_probe PROPERTIES C_EXTENSIONS OFF)
add_executable(test_audio_no_alloc test_audio_no_alloc.c
  $<TARGET_OBJECTS:gabbaboy_core_alloc_probe>)
target_include_directories(test_audio_no_alloc PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_audio_no_alloc PRIVATE c_std_17)
set_target_properties(test_audio_no_alloc PROPERTIES C_EXTENSIONS OFF)
add_test(NAME audio_no_alloc COMMAND test_audio_no_alloc)

add_executable(test_apu test_apu.c)
target_link_libraries(test_apu PRIVATE GabbaBoy::core)
target_compile_features(test_apu PRIVATE c_std_17)
set_target_properties(test_apu PROPERTIES C_EXTENSIONS OFF)
foreach(case pulse mixer sequencer timeline wave noise envelope sweep power)
  add_test(NAME apu_${case} COMMAND test_apu apu_${case})
endforeach()

add_executable(test_serial test_serial.c)
target_link_libraries(test_serial PRIVATE GabbaBoy::core)
target_compile_features(test_serial PRIVATE c_std_17)
set_target_properties(test_serial PROPERTIES C_EXTENSIONS OFF)
foreach(case internal_disconnected external_pending unqualified_overlap)
  add_test(NAME serial_${case} COMMAND test_serial ${case})
endforeach()

add_executable(test_cpu test_cpu.c)
target_link_libraries(test_cpu PRIVATE GabbaBoy::core)
target_compile_features(test_cpu PRIVATE c_std_17)
set_target_properties(test_cpu PROPERTIES C_EXTENSIONS OFF)
foreach(case call_stack return_phases conditional_budget base_matrix base_semantic_tracer base_conditional_paths base_arithmetic_edges base_address_effects illegal_lockup flags_edges timed_access address_wrap stack_wrap cb_wram cb_budget cb_matrix cb_flags_edges cb_timed_access)
  add_test(NAME cpu_${case} COMMAND test_cpu ${case})
endforeach()

add_executable(test_control test_control.c)
target_link_libraries(test_control PRIVATE GabbaBoy::core)
target_compile_features(test_control PRIVATE c_std_17)
set_target_properties(test_control PROPERTIES C_EXTENSIONS OFF)
add_test(NAME interrupt_entry COMMAND test_control interrupt_entry)
add_test(NAME interrupt_budget COMMAND test_control interrupt_budget)
foreach(case interrupt_ei_delay interrupt_ei_chain interrupt_diagnostic_order interrupt_priority halt_idle halt_timer_partition halt_bug stop_wait reset_profile reset_header_flags reset_lockup)
  add_test(NAME ${case} COMMAND test_control ${case})
endforeach()

add_executable(test_events test_events.c)
target_link_libraries(test_events PRIVATE GabbaBoy::core)
target_compile_features(test_events PRIVATE c_std_17)
set_target_properties(test_events PROPERTIES C_EXTENSIONS OFF)
foreach(case event_stop_wake event_boundary event_queue_order event_queue_atomic event_queue_failure_precedence event_partition
             event_deadline_inside event_external_serial_edges event_time_overflow run_output_capacity)
  add_test(NAME ${case} COMMAND test_events ${case})
endforeach()

add_executable(test_joypad test_joypad.c)
target_link_libraries(test_joypad PRIVATE GabbaBoy::core)
target_compile_features(test_joypad PRIVATE c_std_17)
set_target_properties(test_joypad PROPERTIES C_EXTENSIONS OFF)
foreach(case joypad_selection joypad_queue_atomic joypad_equal_time joypad_partition joypad_interrupt)
  add_test(NAME ${case} COMMAND test_joypad ${case})
endforeach()

add_executable(test_loader test_loader.c)
target_link_libraries(test_loader PRIVATE GabbaBoy::core)
target_compile_features(test_loader PRIVATE c_std_17)
set_target_properties(test_loader PROPERTIES C_EXTENSIONS OFF)
foreach(case truncated oversized invalid_header unsupported_cartridge unsupported_rom_size unsupported_declared_size unsupported_ram_size length_mismatch excess_actual null_arguments non_destructive mbc1_matrix mbc1m_variant)
  add_test(NAME loader_${case} COMMAND test_loader ${case} ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
endforeach()

add_executable(test_loader_fuzz test_loader_fuzz.c)
target_link_libraries(test_loader_fuzz PRIVATE GabbaBoy::core)
target_compile_features(test_loader_fuzz PRIVATE c_std_17)
set_target_properties(test_loader_fuzz PROPERTIES C_EXTENSIONS OFF)
add_test(NAME loader_boundary_fuzz
  COMMAND test_loader_fuzz ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME cgb_loader_fuzz_parity
  COMMAND test_loader_fuzz ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb cgb_loader_fuzz_parity)

add_executable(test_fuzz_core test_fuzz_core.c fuzz_core.c)
target_link_libraries(test_fuzz_core PRIVATE GabbaBoy::core)
target_compile_features(test_fuzz_core PRIVATE c_std_17)
target_compile_definitions(test_fuzz_core PRIVATE GBB_FUZZ_STANDALONE_TEST=1)
set_target_properties(test_fuzz_core PROPERTIES C_EXTENSIONS OFF)
add_test(NAME fuzz_core_regressions COMMAND test_fuzz_core)
add_test(NAME cgb_fuzz_io_regressions COMMAND test_fuzz_core cgb)

if(CMAKE_C_COMPILER_ID MATCHES "Clang")
  include(CheckCSourceCompiles)
  set(_gbb_saved_required_flags "${CMAKE_REQUIRED_FLAGS}")
  set(CMAKE_REQUIRED_FLAGS "${CMAKE_REQUIRED_FLAGS} -fsanitize=fuzzer,address,undefined")
  check_c_source_compiles(
    "#include <stdint.h>\n#include <stddef.h>\nint LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) { (void)data; (void)size; return 0; }"
    GBB_HAS_CLANG_LIBFUZZER_RUNTIME)
  set(CMAKE_REQUIRED_FLAGS "${_gbb_saved_required_flags}")
  unset(_gbb_saved_required_flags)
  if(GBB_HAS_CLANG_LIBFUZZER_RUNTIME)
    add_executable(fuzz_core fuzz_core.c ${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c)
    target_include_directories(fuzz_core PRIVATE ${PROJECT_SOURCE_DIR}/include)
    target_compile_features(fuzz_core PRIVATE c_std_17)
    target_compile_options(fuzz_core PRIVATE -fsanitize=fuzzer,address,undefined -fno-omit-frame-pointer)
    target_link_options(fuzz_core PRIVATE -fsanitize=fuzzer,address,undefined)
    set_target_properties(fuzz_core PROPERTIES C_EXTENSIONS OFF)
    message(STATUS "Bounded compiler-integrated libFuzzer target enabled")
  else()
    message(STATUS "Matching Clang libFuzzer runtime unavailable; deterministic sanitizer regressions remain enabled")
  endif()
endif()

add_executable(test_tracer test_tracer.c)
target_link_libraries(test_tracer PRIVATE GabbaBoy::core)
target_compile_features(test_tracer PRIVATE c_std_17)
set_target_properties(test_tracer PROPERTIES C_EXTENSIONS OFF)
foreach(case success failure unsupported timeout trace)
  add_test(NAME tracer_${case} COMMAND test_tracer ${case} ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
endforeach()
foreach(case frame_composition_tracer joypad_gameplay_tracer)
  add_test(NAME ${case} COMMAND test_tracer ${case} ${PROJECT_SOURCE_DIR}/fixtures/visible-demo/demo.gb)
endforeach()

add_executable(test_ppu test_ppu.c)
target_link_libraries(test_ppu PRIVATE GabbaBoy::core)
target_compile_features(test_ppu PRIVATE c_std_17)
set_target_properties(test_ppu PROPERTIES C_EXTENSIONS OFF)
foreach(case frame_composition_bg frame_composition_window frame_composition_sprites frame_composition_priority
             ppu_timing_modes ppu_timing_stat ppu_timing_lcd ppu_timing_fetch
             ppu_timing_partition frame_copy_failures frame_generation_lifecycle)
  add_test(NAME ${case} COMMAND test_ppu ${case})
endforeach()

add_executable(test_dma test_dma.c)
target_link_libraries(test_dma PRIVATE GabbaBoy::core)
target_compile_features(test_dma PRIVATE c_std_17)
set_target_properties(test_dma PROPERTIES C_EXTENSIONS OFF)
foreach(case dma_progress dma_start dma_restart dma_register_readback dma_source_mapping dma_hram dma_interrupt_stack dma_partition
             dma_vram_lock dma_oam_lock dma_contention dma_ppu_overlap dma_oam_entry39 dma_oam_entry39_reset
             dma_active_mode_matrix dma_ppu_cpu_collision dma_ppu_word_boundaries)
  add_test(NAME ${case} COMMAND test_dma ${case})
endforeach()

add_test(NAME tracer_smoke COMMAND gabbaboy-runner ${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb)
add_test(NAME fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DROM=${PROJECT_SOURCE_DIR}/fixtures/tracer/tracer.gb
    -DMANIFEST=${PROJECT_SOURCE_DIR}/fixtures/tracer/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixture.cmake)
add_test(NAME visible_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DROM=${PROJECT_SOURCE_DIR}/fixtures/visible-demo/demo.gb
    -DMANIFEST=${PROJECT_SOURCE_DIR}/fixtures/visible-demo/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixture.cmake)
add_test(NAME mbc1_continuation_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DROM=${PROJECT_SOURCE_DIR}/fixtures/mbc1-continuation/continuation.gb
    -DMANIFEST=${PROJECT_SOURCE_DIR}/fixtures/mbc1-continuation/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixture.cmake)
add_test(NAME mbc3_rtc_continuation_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DROM=${PROJECT_SOURCE_DIR}/fixtures/mbc3-rtc-continuation/continuation.gb
    -DMANIFEST=${PROJECT_SOURCE_DIR}/fixtures/mbc3-rtc-continuation/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixture.cmake)
add_test(NAME mbc2_continuation_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DROM=${PROJECT_SOURCE_DIR}/fixtures/mbc2-continuation/continuation.gb
    -DMANIFEST=${PROJECT_SOURCE_DIR}/fixtures/mbc2-continuation/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixture.cmake)
add_test(NAME mbc5_continuation_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DROM=${PROJECT_SOURCE_DIR}/fixtures/mbc5-continuation/continuation.gb
    -DMANIFEST=${PROJECT_SOURCE_DIR}/fixtures/mbc5-continuation/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixture.cmake)
# Core-level continuation of the original timer/MBC2/MBC5 guests across fresh instances (D-24).
add_executable(test_continuation_guests test_continuation_guests.c)
target_link_libraries(test_continuation_guests PRIVATE GabbaBoy::core)
target_compile_features(test_continuation_guests PRIVATE c_std_17)
set_target_properties(test_continuation_guests PROPERTIES C_EXTENSIONS OFF)
foreach(guest mbc3_rtc:mbc3-rtc mbc3_rtc_halted:mbc3-rtc mbc3_rtc_carry:mbc3-rtc mbc2:mbc2 mbc5:mbc5)
  string(REPLACE ":" ";" guest_parts "${guest}")
  list(GET guest_parts 0 guest_case)
  list(GET guest_parts 1 guest_dir)
  add_test(NAME continuation_guest_${guest_case}
    COMMAND test_continuation_guests continuation_guest_${guest_case}
      ${PROJECT_SOURCE_DIR}/fixtures/${guest_dir}-continuation/continuation.gb)
endforeach()
add_test(NAME mbc5_banking_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DROM=${PROJECT_SOURCE_DIR}/fixtures/mbc5-banking/banking.gb
    -DMANIFEST=${PROJECT_SOURCE_DIR}/fixtures/mbc5-banking/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixture.cmake)
# MagenTests mbc_oob_sram screen oracle (D-05). Public API only; repository fixtures, never installed.
set(GBB_MAGENTESTS_DIR "${PROJECT_SOURCE_DIR}/fixtures/magentests")
add_executable(test_magentests test_magentests.c)
target_link_libraries(test_magentests PRIVATE GabbaBoy::core)
target_compile_features(test_magentests PRIVATE c_std_17)
set_target_properties(test_magentests PROPERTIES C_EXTENSIONS OFF)
add_test(NAME magentests_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DMANIFEST=${GBB_MAGENTESTS_DIR}/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixtureManifest.cmake)
add_test(NAME magentests_oob_sram_mbc3
  COMMAND test_magentests magentests_oob_sram_mbc3 ${GBB_MAGENTESTS_DIR}/mbc_oob_sram_mbc3.gbc)
add_test(NAME magentests_oob_sram_mbc1
  COMMAND test_magentests magentests_oob_sram_mbc1 ${GBB_MAGENTESTS_DIR}/mbc_oob_sram_mbc1.gbc)
add_test(NAME magentests_oob_sram_mbc5
  COMMAND test_magentests magentests_oob_sram_mbc5 ${GBB_MAGENTESTS_DIR}/mbc_oob_sram_mbc5.gbc)
add_test(NAME magentests_oob_sram_negative_control
  COMMAND test_magentests magentests_oob_sram_negative_control
    ${GBB_MAGENTESTS_DIR}/mbc_oob_sram_mbc1.gbc
    ${GBB_MAGENTESTS_DIR}/mbc_oob_sram_mbc3.gbc
    ${GBB_MAGENTESTS_DIR}/mbc_oob_sram_mbc5.gbc)
# rtc3test v004 screen oracle (D-11). White-box single TU: it includes the core and the acceptance
# sources it needs, so it must not link GabbaBoy::core or gabbaboy_accept (duplicate definitions).
set(GBB_RTC3TEST_DIR "${PROJECT_SOURCE_DIR}/fixtures/rtc3test")
set(GBB_RTC3TEST_CASES "${PROJECT_SOURCE_DIR}/tests/rtc3test")
add_executable(test_rtc3test test_rtc3test.c)
target_include_directories(test_rtc3test PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_rtc3test PRIVATE c_std_17)
set_target_properties(test_rtc3test PROPERTIES C_EXTENSIONS OFF)
add_test(NAME rtc3test_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DMANIFEST=${GBB_RTC3TEST_DIR}/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixtureManifest.cmake)
foreach(suite basic range subsecond)
  add_test(NAME rtc3test_${suite}
    COMMAND test_rtc3test rtc3test_${suite} ${GBB_RTC3TEST_DIR}/rtc3test.gb
      ${GBB_RTC3TEST_CASES}/${suite}.input ${GBB_RTC3TEST_CASES}/expected-${suite}.txt)
  set_tests_properties(rtc3test_${suite} PROPERTIES TIMEOUT 300)
endforeach()
# Negative control: the Basic script with its tap removed must never show the end marker in 60 s.
add_test(NAME rtc3test_negative_control
  COMMAND test_rtc3test rtc3test_negative_control ${GBB_RTC3TEST_DIR}/rtc3test.gb
    ${GBB_RTC3TEST_CASES}/basic.input)
set_tests_properties(rtc3test_negative_control PROPERTIES TIMEOUT 300)
add_test(NAME mooneye_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyMooneye.cmake)
add_test(NAME mooneye_eligible_inventory
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyMooneye.cmake)
# Phase 8 sibling set: mbc2/mbc5 derivatives (D-23, D-24, D-26). Digest, inventory and pc-table modes.
add_test(NAME mooneye_mbc_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MODE=digest
    -DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyMooneyeMbc.cmake)
add_test(NAME mooneye_mbc_eligible_inventory
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MODE=inventory
    -DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyMooneyeMbc.cmake)
add_test(NAME mooneye_mbc_pc_table
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MODE=pc-table
    -DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc
    -DGBB_RUNNER_SOURCE=${PROJECT_SOURCE_DIR}/src/runner/main.c
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyMooneyeMbc.cmake)
# Negative control: a manifest whose first result_pc was changed must fail the pc-table check with exit code 1.
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/mooneye-mbc-tamper")
file(READ "${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc/manifest.json" GBB_MBC_MANIFEST_JSON)
string(JSON GBB_MBC_TAMPERED_JSON SET "${GBB_MBC_MANIFEST_JSON}" fixtures 0 result_pc "\"0x407f\"")
file(WRITE "${PROJECT_BINARY_DIR}/mooneye-mbc-tamper/manifest.json" "${GBB_MBC_TAMPERED_JSON}")
add_test(NAME mooneye_mbc_pc_table_tamper
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_MODE=pc-table;-DGBB_MANIFEST=${PROJECT_BINARY_DIR}/mooneye-mbc-tamper/manifest.json;-DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc;-DGBB_RUNNER_SOURCE=${PROJECT_SOURCE_DIR}/src/runner/main.c;-P;${PROJECT_SOURCE_DIR}/cmake/VerifyMooneyeMbc.cmake"
    -DGBB_EXPECT_CODE=1
    -DGBB_EXPECT_REGEX=pc-table-mismatch
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
# Phase 10 Mooneye CGB derivatives (D-26, names per D-27): digest and inventory modes of the
# fail-closed verifier, plus the pc-table mode that ties the runner's cgb_cases[] to the manifest (Plan 10-16).
add_test(NAME cgb_mooneye_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MODE=digest
    -DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye-cgb
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyMooneyeCgb.cmake)
set_tests_properties(cgb_mooneye_fixture_digest PROPERTIES
  PASS_REGULAR_EXPRESSION "Verified 4 eligible Mooneye-cgb ROM\\(s\\)")
add_test(NAME cgb_mooneye_inventory
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MODE=inventory
    -DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye-cgb
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyMooneyeCgb.cmake)
set_tests_properties(cgb_mooneye_inventory PROPERTIES
  PASS_REGULAR_EXPRESSION "Verified Mooneye-cgb inventory: 4 fixtures")
# Configure-time mutants (exact exit code 1 plus a named token): a flipped ROM digest and a
# duplicated fixture id. Each differs from the committed manifest by exactly one fact.
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/mooneye-cgb-tamper/digest" "${PROJECT_BINARY_DIR}/mooneye-cgb-tamper/dup-id")
file(READ "${PROJECT_SOURCE_DIR}/fixtures/mooneye-cgb/manifest.json" GBB_CGB_MANIFEST_JSON)
string(JSON GBB_CGB_FIRST_DIGEST GET "${GBB_CGB_MANIFEST_JSON}" fixtures 0 sha256)
string(JSON GBB_CGB_FIRST_ID GET "${GBB_CGB_MANIFEST_JSON}" fixtures 0 id)
string(SUBSTRING "${GBB_CGB_FIRST_DIGEST}" 0 1 GBB_CGB_FIRST_NIBBLE)
if(GBB_CGB_FIRST_NIBBLE STREQUAL "0")
  set(GBB_CGB_FLIPPED_NIBBLE "1")
else()
  set(GBB_CGB_FLIPPED_NIBBLE "0")
endif()
string(SUBSTRING "${GBB_CGB_FIRST_DIGEST}" 1 -1 GBB_CGB_DIGEST_TAIL)
string(JSON GBB_CGB_DIGEST_TAMPERED SET "${GBB_CGB_MANIFEST_JSON}" fixtures 0 sha256
  "\"${GBB_CGB_FLIPPED_NIBBLE}${GBB_CGB_DIGEST_TAIL}\"")
file(WRITE "${PROJECT_BINARY_DIR}/mooneye-cgb-tamper/digest/manifest.json" "${GBB_CGB_DIGEST_TAMPERED}")
string(JSON GBB_CGB_DUP_TAMPERED SET "${GBB_CGB_MANIFEST_JSON}" fixtures 1 id "\"${GBB_CGB_FIRST_ID}\"")
file(WRITE "${PROJECT_BINARY_DIR}/mooneye-cgb-tamper/dup-id/manifest.json" "${GBB_CGB_DUP_TAMPERED}")
function(gbb_add_cgb_mooneye_tamper_test name mode manifest regex)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_MODE=${mode};-DGBB_MANIFEST=${manifest};-DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye-cgb;-P;${PROJECT_SOURCE_DIR}/cmake/VerifyMooneyeCgb.cmake"
      -DGBB_EXPECT_CODE=1
      "-DGBB_EXPECT_REGEX=${regex}"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
endfunction()
gbb_add_cgb_mooneye_tamper_test(cgb_mooneye_digest_tamper digest
  "${PROJECT_BINARY_DIR}/mooneye-cgb-tamper/digest/manifest.json" "Fixture mooneye-misc-boot-regs-cgb mismatch")
gbb_add_cgb_mooneye_tamper_test(cgb_mooneye_inventory_tamper inventory
  "${PROJECT_BINARY_DIR}/mooneye-cgb-tamper/dup-id/manifest.json" "Duplicate fixture id: mooneye-misc-boot-regs-cgb")
add_test(NAME cgb_mooneye_pc_table
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MODE=pc-table
    -DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye-cgb
    -DGBB_RUNNER_SOURCE=${PROJECT_SOURCE_DIR}/src/runner/main.c
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyMooneyeCgb.cmake)
set_tests_properties(cgb_mooneye_pc_table PROPERTIES
  PASS_REGULAR_EXPRESSION "Verified pc-table: 4 manifest rows agree with the compiled cgb_cases")
# Negative control: a manifest whose first result_pc was changed must fail the pc-table check, naming the field.
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/mooneye-cgb-tamper/pc")
string(JSON GBB_CGB_PC_TAMPERED SET "${GBB_CGB_MANIFEST_JSON}" fixtures 0 result_pc "\"0x4328\"")
file(WRITE "${PROJECT_BINARY_DIR}/mooneye-cgb-tamper/pc/manifest.json" "${GBB_CGB_PC_TAMPERED}")
add_test(NAME cgb_mooneye_pc_table_tamper
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_MODE=pc-table;-DGBB_MANIFEST=${PROJECT_BINARY_DIR}/mooneye-cgb-tamper/pc/manifest.json;-DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye-cgb;-DGBB_RUNNER_SOURCE=${PROJECT_SOURCE_DIR}/src/runner/main.c;-P;${PROJECT_SOURCE_DIR}/cmake/VerifyMooneyeCgb.cmake"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=pc-table-mismatch: mooneye-misc-boot-regs-cgb result_pc"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
# Negative control (D-28): an edited sibling manifest is refused with invalid-manifest and exactly exit code 2.
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/mooneye-mbc-unknown")
configure_file("${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc/manifest.json"
  "${PROJECT_BINARY_DIR}/mooneye-mbc-unknown/manifest.json" COPYONLY)
file(APPEND "${PROJECT_BINARY_DIR}/mooneye-mbc-unknown/manifest.json" " ")
add_test(NAME mooneye_mbc_unknown_manifest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--manifest;${PROJECT_BINARY_DIR}/mooneye-mbc-unknown/manifest.json;--suite"
    -DGBB_EXPECT_CODE=2
    -DGBB_EXPECT_REGEX=invalid-manifest
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

add_executable(test_diagnostics test_diagnostics.c)
target_link_libraries(test_diagnostics PRIVATE GabbaBoy::core)
target_compile_features(test_diagnostics PRIVATE c_std_17)
set_target_properties(test_diagnostics PROPERTIES C_EXTENSIONS OFF)
foreach(case zero exact short null canary)
  add_test(NAME diagnostics_${case} COMMAND test_diagnostics diagnostics_${case})
endforeach()

add_executable(test_runner test_runner.c)
target_link_libraries(test_runner PRIVATE gabbaboy_runner_support)
target_compile_features(test_runner PRIVATE c_std_17)
set_target_properties(test_runner PROPERTIES C_EXTENSIONS OFF)
add_test(NAME runner_help
  COMMAND ${CMAKE_COMMAND}
    -DGBB_RUNNER=$<TARGET_FILE:gabbaboy-runner>
    -P ${PROJECT_SOURCE_DIR}/tests/verify_runner_help.cmake)
foreach(case pass fail wrong_breakpoint timeout unsupported zero_eligible)
  add_test(NAME runner_${case} COMMAND test_runner runner_${case})
endforeach()
add_test(NAME runner_guest_failure
  COMMAND test_runner runner_guest_failure ${PROJECT_SOURCE_DIR}/fixtures/mooneye/daa.gb)
# D-29: a wrong mapper type byte must turn the admitted MBC5 derivative from pass into something else.
add_test(NAME mooneye_mbc_type_mutation
  COMMAND test_runner mooneye_mbc_type_mutation ${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc/mbc5_rom_512kb.gb)
set_tests_properties(mooneye_mbc_type_mutation PROPERTIES TIMEOUT 30)
# D-26: an expected-unsupported row is met only by a stop at the declared address; a tampered "pass" expectation,
# a wrong address and a passing ROM are all failing statuses (the configure-time copy is made below).
add_test(NAME cgb_mooneye_expected_unsupported_tamper
  COMMAND test_runner cgb_mooneye_expected_unsupported_tamper
    ${PROJECT_BINARY_DIR}/mooneye-cgb-tamper/expect/manifest.json
    ${PROJECT_SOURCE_DIR}/fixtures/mooneye-cgb/manifest.json
    ${PROJECT_SOURCE_DIR}/fixtures/mooneye-cgb)
set_tests_properties(cgb_mooneye_expected_unsupported_tamper PROPERTIES TIMEOUT 30
  PASS_REGULAR_EXPRESSION "control=expected-unsupported-tampered-to-pass.*control=expected-unsupported-wrong-address.*control=expected-unsupported-pass-is-failure")
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/runner-missing-fixture")
configure_file("${PROJECT_SOURCE_DIR}/fixtures/mooneye/manifest.json"
  "${PROJECT_BINARY_DIR}/runner-missing-fixture/manifest.json" COPYONLY)
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/runner-bad-digest")
configure_file("${PROJECT_SOURCE_DIR}/fixtures/mooneye/manifest.json"
  "${PROJECT_BINARY_DIR}/runner-bad-digest/manifest.json" COPYONLY)
string(REPEAT "A" 32768 GBB_INVALID_ROM_BYTES)
file(WRITE "${PROJECT_BINARY_DIR}/runner-bad-digest/daa.gb" "${GBB_INVALID_ROM_BYTES}")
add_test(NAME runner_missing_fixture
  COMMAND ${CMAKE_COMMAND}
    -DGBB_RUNNER=$<TARGET_FILE:gabbaboy-runner>
    -DGBB_MANIFEST=${PROJECT_BINARY_DIR}/runner-missing-fixture/manifest.json
    -DGBB_MODE=missing -P ${PROJECT_SOURCE_DIR}/tests/expect_runner_failure.cmake)
add_test(NAME runner_bad_digest
  COMMAND ${CMAKE_COMMAND}
    -DGBB_RUNNER=$<TARGET_FILE:gabbaboy-runner>
    -DGBB_MANIFEST=${PROJECT_BINARY_DIR}/runner-bad-digest/manifest.json
    -DGBB_MODE=digest -P ${PROJECT_SOURCE_DIR}/tests/expect_runner_failure.cmake)
file(WRITE "${PROJECT_BINARY_DIR}/runner-bad-manifest.json" "{}")
file(READ "${PROJECT_SOURCE_DIR}/fixtures/mooneye/manifest.json" GBB_TAMPERED_MANIFEST)
string(REPLACE "\"model\": \"DMG-CPU-B\"" "\"model\": \"CGB-E\"" GBB_TAMPERED_MANIFEST "${GBB_TAMPERED_MANIFEST}")
string(REPLACE "\"boot\": \"Skipped; bootless DMG-CPU-B profile starts at the cartridge entry point 0x0100.\""
  "\"boot\": \"Booted profile.\"" GBB_TAMPERED_MANIFEST "${GBB_TAMPERED_MANIFEST}")
file(WRITE "${PROJECT_BINARY_DIR}/runner-wrong-metadata.json" "${GBB_TAMPERED_MANIFEST}")
add_test(NAME runner_bad_manifest
  COMMAND ${CMAKE_COMMAND}
    -DGBB_RUNNER=$<TARGET_FILE:gabbaboy-runner>
    -DGBB_MANIFEST=${PROJECT_BINARY_DIR}/runner-bad-manifest.json
    -DGBB_MODE=manifest -P ${PROJECT_SOURCE_DIR}/tests/expect_runner_failure.cmake)
add_test(NAME runner_bad_metadata
  COMMAND ${CMAKE_COMMAND}
    -DGBB_RUNNER=$<TARGET_FILE:gabbaboy-runner>
    -DGBB_MANIFEST=${PROJECT_BINARY_DIR}/runner-wrong-metadata.json
    -DGBB_MODE=manifest -P ${PROJECT_SOURCE_DIR}/tests/expect_runner_failure.cmake)
add_test(NAME mooneye_required_suite
  COMMAND gabbaboy-runner --manifest ${PROJECT_SOURCE_DIR}/fixtures/mooneye/manifest.json --suite --receipt)
foreach(case daa tim00 tim00-div-trigger)
  add_test(NAME mooneye_case_${case}
    COMMAND gabbaboy-runner --manifest ${PROJECT_SOURCE_DIR}/fixtures/mooneye/manifest.json --case ${case} --receipt)
endforeach()
# Bound guest-runner test processes in host wall time as well as emulated half-dots.
# CTest terminates a stalled process and reports a failed case instead of hanging CI.
set_tests_properties(
  tracer_success tracer_failure tracer_unsupported tracer_timeout tracer_trace
  frame_composition_tracer joypad_gameplay_tracer tracer_smoke
  runner_pass runner_help runner_fail runner_wrong_breakpoint runner_timeout runner_unsupported
  runner_zero_eligible runner_guest_failure runner_missing_fixture runner_bad_digest
  runner_bad_manifest runner_bad_metadata
  concurrent_independent_instances cgb_instance_isolation
  mooneye_required_suite mooneye_case_daa mooneye_case_tim00 mooneye_case_tim00-div-trigger
  PROPERTIES TIMEOUT 30)
set_tests_properties(mooneye_case_daa PROPERTIES PASS_REGULAR_EXPRESSION
  "status=pass.*source_revision=31510e12eea6286d36eea060a6adde755e1067aa.*report_patch_sha256=c3679ab53b59da14a0f6af1fdd552316ba922762c3a91988f7f8ac4440516e5d.*fixture_origin=derived-headless-report-closure upstream_assertions=unchanged.*protocol_stage=callback-then-ld-b-b callback_result=pass callback_pc=0166 result_pc=409a")
set_tests_properties(mooneye_case_tim00 PROPERTIES PASS_REGULAR_EXPRESSION
  "status=pass.*source_revision=31510e12eea6286d36eea060a6adde755e1067aa.*report_patch_sha256=c3679ab53b59da14a0f6af1fdd552316ba922762c3a91988f7f8ac4440516e5d.*fixture_origin=derived-headless-report-closure upstream_assertions=unchanged.*protocol_stage=callback-then-ld-b-b callback_result=pass callback_pc=4000 result_pc=4327")
set_tests_properties(mooneye_case_tim00-div-trigger PROPERTIES PASS_REGULAR_EXPRESSION
  "status=pass.*source_revision=31510e12eea6286d36eea060a6adde755e1067aa.*report_patch_sha256=c3679ab53b59da14a0f6af1fdd552316ba922762c3a91988f7f8ac4440516e5d.*fixture_origin=derived-headless-report-closure upstream_assertions=unchanged.*protocol_stage=callback-then-ld-b-b callback_result=pass callback_pc=4000 result_pc=4327")
# Phase 8 sibling suite: the manifest's 15 derivatives, one CTest per alias (callback_pc and result_pc per Pitfall P13).
set(GBB_MBC_MANIFEST ${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc/manifest.json)
add_test(NAME mooneye_mbc_required_suite
  COMMAND gabbaboy-runner --manifest ${GBB_MBC_MANIFEST} --suite --receipt)
# The ASan/UBSan leg runs the 15 cases back to back in about 35 s (hosted Linux), so the suite bound is 120 s.
set_tests_properties(mooneye_mbc_required_suite PROPERTIES TIMEOUT 120 PASS_REGULAR_EXPRESSION
  "suite eligible=15 executed=15 status=pass.*suite categories mbc2=7/7 mbc5=8/8")
set(GBB_MBC_CASES
  mbc2_bits_ramg:01d7:407e mbc2_bits_romb:01c0:407e mbc2_bits_unused:018d:407e mbc2_ram:029c:4071
  mbc2_rom_512kb:0207:4071 mbc2_rom_1Mb:0207:4071 mbc2_rom_2Mb:0207:4071
  mbc5_rom_512kb:0216:4072 mbc5_rom_1Mb:0216:4072 mbc5_rom_2Mb:0216:4072 mbc5_rom_4Mb:0216:4072
  mbc5_rom_8Mb:0216:4072 mbc5_rom_16Mb:0216:4072 mbc5_rom_32Mb:0216:4072 mbc5_rom_64Mb:0216:4072)
foreach(entry IN LISTS GBB_MBC_CASES)
  string(REPLACE ":" ";" parts "${entry}")
  list(GET parts 0 alias)
  list(GET parts 1 callback_pc)
  list(GET parts 2 result_pc)
  add_test(NAME mooneye_mbc_case_${alias}
    COMMAND gabbaboy-runner --manifest ${GBB_MBC_MANIFEST} --case ${alias} --receipt)
  # Unsanitized wall time is at most 1.9 s per case (Plan 08-05); the hosted ASan/UBSan leg measured 15.4 s
  # for mbc2_bits_ramg under parallel load, so the bound is 60 s.
  set_tests_properties(mooneye_mbc_case_${alias} PROPERTIES TIMEOUT 60 PASS_REGULAR_EXPRESSION
    "status=pass.*source_revision=31510e12eea6286d36eea060a6adde755e1067aa.*fixture_origin=derived-headless-report-closure upstream_assertions=unchanged.*protocol_stage=callback-then-ld-b-b callback_result=pass callback_pc=${callback_pc} result_pc=${result_pc}")
endforeach()
# Phase 10 CGB-profile Mooneye derivatives (D-26): the runner's third suite. Each row runs on the CGB-CPU-E
# profile in compat mode and prints its own label; the DMG label must never appear.
set(GBB_CGB_MOONEYE_MANIFEST ${PROJECT_SOURCE_DIR}/fixtures/mooneye-cgb/manifest.json)
add_test(NAME cgb_mooneye_case_boot_regs-cgb
  COMMAND gabbaboy-runner --manifest ${GBB_CGB_MOONEYE_MANIFEST} --case boot_regs-cgb --receipt)
set_tests_properties(cgb_mooneye_case_boot_regs-cgb PROPERTIES TIMEOUT 30
  PASS_REGULAR_EXPRESSION "status=pass.*profile=CGB-CPU-E.*callback_result=pass callback_pc=4000 result_pc=4327"
  FAIL_REGULAR_EXPRESSION "DMG-CPU-B")
add_test(NAME cgb_mooneye_case_boot_div-cgbABCDE
  COMMAND gabbaboy-runner --manifest ${GBB_CGB_MOONEYE_MANIFEST} --case boot_div-cgbABCDE --receipt)
set_tests_properties(cgb_mooneye_case_boot_div-cgbABCDE PROPERTIES TIMEOUT 30
  PASS_REGULAR_EXPRESSION "status=pass.*profile=CGB-CPU-E.*callback_result=pass callback_pc=4000 result_pc=4327"
  FAIL_REGULAR_EXPRESSION "DMG-CPU-B")
# The two staged ROMs stop on the unbuilt FF76 register: the status is expected-unsupported (never pass),
# the stop reason and address are named, and the run exits 0 only on that exact stop.
foreach(alias boot_hwio-C unused_hwio-C)
  add_test(NAME cgb_mooneye_case_${alias}
    COMMAND gabbaboy-runner --manifest ${GBB_CGB_MOONEYE_MANIFEST} --case ${alias} --receipt)
  set_tests_properties(cgb_mooneye_case_${alias} PROPERTIES TIMEOUT 30
    PASS_REGULAR_EXPRESSION "status=expected-unsupported stop=unsupported-bus address=ff76.*profile=CGB-CPU-E"
    FAIL_REGULAR_EXPRESSION "DMG-CPU-B|status=pass|status=unexpected-pass|status=fail")
endforeach()
add_test(NAME cgb_mooneye_required_suite
  COMMAND gabbaboy-runner --manifest ${GBB_CGB_MOONEYE_MANIFEST} --suite --receipt)
set_tests_properties(cgb_mooneye_required_suite PROPERTIES TIMEOUT 30
  PASS_REGULAR_EXPRESSION "suite eligible=4 executed=4 status=pass.*expected-unsupported=2/2"
  FAIL_REGULAR_EXPRESSION "DMG-CPU-B")
# D-25 / D-05: --observe prints the not-applicable token for a CGB row and no DMG-labelled line.
add_test(NAME cgb_mooneye_observe_not_applicable
  COMMAND gabbaboy-runner --manifest ${GBB_CGB_MOONEYE_MANIFEST} --case boot_regs-cgb --observe)
set_tests_properties(cgb_mooneye_observe_not_applicable PROPERTIES TIMEOUT 30
  PASS_REGULAR_EXPRESSION "mooneye[.]boot_regs-cgb[.]frame\tnot-applicable"
  FAIL_REGULAR_EXPRESSION "frame_generation|ldbb_half_dots|not-ready")
# Negative control (D-28): a one-byte-longer manifest is refused with invalid-manifest and exactly exit code 2.
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/mooneye-cgb-unknown")
configure_file("${PROJECT_SOURCE_DIR}/fixtures/mooneye-cgb/manifest.json"
  "${PROJECT_BINARY_DIR}/mooneye-cgb-unknown/manifest.json" COPYONLY)
file(APPEND "${PROJECT_BINARY_DIR}/mooneye-cgb-unknown/manifest.json" " ")
add_test(NAME cgb_mooneye_unknown_manifest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--manifest;${PROJECT_BINARY_DIR}/mooneye-cgb-unknown/manifest.json;--suite"
    -DGBB_EXPECT_CODE=2
    -DGBB_EXPECT_REGEX=invalid-manifest
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
# Negative control: a configure-time copy of the manifest whose boot_hwio-C row says "pass". The raw-SHA gate
# would reject it on the command line, so test_runner reads the row expectation from the copy itself.
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/mooneye-cgb-tamper/expect")
string(JSON GBB_CGB_EXPECT_TAMPERED SET "${GBB_CGB_MANIFEST_JSON}" fixtures 2 expect "\"pass\"")
file(WRITE "${PROJECT_BINARY_DIR}/mooneye-cgb-tamper/expect/manifest.json" "${GBB_CGB_EXPECT_TAMPERED}")
set(GBB_TEST_SANITIZER_LINK_OPTIONS "")
if(GABBABOY_ENABLE_SANITIZERS)
  set(GBB_TEST_SANITIZER_LINK_OPTIONS "-fsanitize=address,undefined")
endif()
add_test(NAME preview_package_smoke
  COMMAND ${CMAKE_COMMAND}
    -DGBB_SOURCE_DIR=${PROJECT_SOURCE_DIR}
    -DGBB_BINARY_DIR=${PROJECT_BINARY_DIR}
    -DGBB_CMAKE_COMMAND=${CMAKE_COMMAND}
    -DGBB_GENERATOR=${CMAKE_GENERATOR}
    -DGBB_EXECUTABLE_SUFFIX=${CMAKE_EXECUTABLE_SUFFIX}
    -DGBB_SANITIZER_LINK_OPTIONS=${GBB_TEST_SANITIZER_LINK_OPTIONS}
    -DGBB_CONFIGURATION=$<CONFIG>
    -P ${PROJECT_SOURCE_DIR}/cmake/PreviewPackageSmoke.cmake)

if(GABBABOY_BUILD_PLAYER)
  add_subdirectory(player)
endif()

if(GBB_TEST_INSTALL_PREFIX AND EXISTS "${GBB_TEST_INSTALL_PREFIX}")
  get_filename_component(GBB_TEST_INSTALL_PREFIX_ABSOLUTE
    "${GBB_TEST_INSTALL_PREFIX}" ABSOLUTE BASE_DIR "${PROJECT_BINARY_DIR}")
  add_test(NAME installed_runner_smoke
    COMMAND ${CMAKE_COMMAND}
      -DGBB_INSTALL_PREFIX=${GBB_TEST_INSTALL_PREFIX_ABSOLUTE}
      -DGBB_EXECUTABLE_SUFFIX=${CMAKE_EXECUTABLE_SUFFIX}
      -DGBB_RUNNER_WORKDIR=${PROJECT_BINARY_DIR}/installed-runner-cwd
      -P ${PROJECT_SOURCE_DIR}/cmake/VerifyInstalledPackage.cmake)
  foreach(language IN ITEMS c cpp)
    add_test(NAME installed_consumer_${language}
      COMMAND ${CMAKE_COMMAND}
        -DGBB_INSTALL_PREFIX=${GBB_TEST_INSTALL_PREFIX_ABSOLUTE}
      -DGBB_CONSUMER_SOURCE=${PROJECT_SOURCE_DIR}/tests/consumers/${language}
      -DGBB_CONSUMER_BINARY=${PROJECT_BINARY_DIR}/consumer-${language}
      -DGBB_LANGUAGE=${language}
      -DGBB_EXECUTABLE_SUFFIX=${CMAKE_EXECUTABLE_SUFFIX}
      -DGBB_CONFIGURATION=$<CONFIG>
      -P ${PROJECT_SOURCE_DIR}/cmake/RunInstalledConsumer.cmake)
    add_test(NAME installed_consumer_phase2_${language}
      COMMAND ${CMAKE_COMMAND}
        -DGBB_INSTALL_PREFIX=${GBB_TEST_INSTALL_PREFIX_ABSOLUTE}
        -DGBB_CONSUMER_SOURCE=${PROJECT_SOURCE_DIR}/tests/consumers/${language}
        -DGBB_CONSUMER_BINARY=${PROJECT_BINARY_DIR}/consumer-phase2-${language}
        -DGBB_LANGUAGE=${language}
        -DGBB_EXECUTABLE_SUFFIX=${CMAKE_EXECUTABLE_SUFFIX}
        -DGBB_CONFIGURATION=$<CONFIG>
        -P ${PROJECT_SOURCE_DIR}/cmake/RunInstalledConsumer.cmake)
  endforeach()
endif()

# Libbet admission (GAME-01, gate G5). The verifier is stdlib-only Python run with -I; every
# negative control goes through expect_exit.cmake so it must exit with exactly the expected code
# and reason, never merely "non-zero".
find_package(Python3 COMPONENTS Interpreter REQUIRED)
set(GBB_LIBBET_VERIFIER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-libbet-admission.py")
set(GBB_LIBBET_MANIFEST "${PROJECT_SOURCE_DIR}/fixtures/libbet/manifest.json")
set(GBB_LIBBET_DIR "${PROJECT_BINARY_DIR}/libbet-admission")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
  "${GBB_LIBBET_MANIFEST}" "${PROJECT_SOURCE_DIR}/fixtures/libbet/libbet.gb")

# add_test with a verifier command line: GBB_CMD travels as a list, so semicolons are spelled
# with $<SEMICOLON> to survive the add_test argument split.
function(gbb_add_expect_exit_test name code regex)
  set(command "${Python3_EXECUTABLE}" -I "${GBB_LIBBET_VERIFIER}" ${ARGN})
  list(JOIN command "$<SEMICOLON>" joined)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${joined}"
      -DGBB_EXPECT_CODE=${code}
      "-DGBB_EXPECT_REGEX=${regex}"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT 30)
endfunction()

# Five mutated manifest copies of the committed manifest. Each differs by one fact; the ROM stays
# the committed one because the verifier resolves rom.path against the repository root.
file(MAKE_DIRECTORY "${GBB_LIBBET_DIR}")
file(READ "${GBB_LIBBET_MANIFEST}" GBB_LIBBET_JSON)
string(JSON GBB_LIBBET_ASSETS_EMPTY SET "${GBB_LIBBET_JSON}" rights embedded_assets "[]")
string(JSON GBB_LIBBET_ASSETS_MISSING REMOVE "${GBB_LIBBET_JSON}" rights embedded_assets 0)
string(JSON GBB_LIBBET_LICENCE_UNKNOWN SET "${GBB_LIBBET_JSON}" rights embedded_assets 0 licence "\"unknown\"")
string(JSON GBB_LIBBET_ROM_DIGEST GET "${GBB_LIBBET_JSON}" rom sha256)
string(SUBSTRING "${GBB_LIBBET_ROM_DIGEST}" 0 1 GBB_LIBBET_FIRST_DIGIT)
string(SUBSTRING "${GBB_LIBBET_ROM_DIGEST}" 1 -1 GBB_LIBBET_DIGEST_REST)
if(GBB_LIBBET_FIRST_DIGIT STREQUAL "0")
  set(GBB_LIBBET_FIRST_DIGIT "1")
else()
  set(GBB_LIBBET_FIRST_DIGIT "0")
endif()
string(JSON GBB_LIBBET_BAD_DIGEST SET "${GBB_LIBBET_JSON}" rom sha256
  "\"${GBB_LIBBET_FIRST_DIGIT}${GBB_LIBBET_DIGEST_REST}\"")
string(JSON GBB_LIBBET_BAD_HEADER SET "${GBB_LIBBET_JSON}" rom header cartridge_type 1)
foreach(mutation IN ITEMS ASSETS_EMPTY ASSETS_MISSING LICENCE_UNKNOWN BAD_DIGEST BAD_HEADER)
  string(TOLOWER "${mutation}" mutation_file)
  file(WRITE "${GBB_LIBBET_DIR}/${mutation_file}.json" "${GBB_LIBBET_${mutation}}\n")
endforeach()

gbb_add_expect_exit_test(libbet_admission_pass 0 "libbet admission verified" --manifest "${GBB_LIBBET_MANIFEST}")
gbb_add_expect_exit_test(libbet_admission_empty_assets 1 "embedded-assets-empty"
  --manifest "${GBB_LIBBET_DIR}/assets_empty.json")
gbb_add_expect_exit_test(libbet_admission_missing_record 1 "embedded-asset-missing"
  --manifest "${GBB_LIBBET_DIR}/assets_missing.json")
gbb_add_expect_exit_test(libbet_admission_unknown_licence 1 "embedded-asset-field-invalid"
  --manifest "${GBB_LIBBET_DIR}/licence_unknown.json")
gbb_add_expect_exit_test(libbet_admission_bad_digest 1 "rom-digest-mismatch"
  --manifest "${GBB_LIBBET_DIR}/bad_digest.json")
gbb_add_expect_exit_test(libbet_admission_bad_header 1 "rom-header-mismatch"
  --manifest "${GBB_LIBBET_DIR}/bad_header.json")
gbb_add_expect_exit_test(libbet_admission_self_test 0 "libbet admission self-test passed" --self-test)
gbb_add_expect_exit_test(libbet_notice 0 "libbet notices and attributes verified"
  --manifest "${GBB_LIBBET_MANIFEST}" --check-notices)

# Redistribution guard: the third-party ROM is a repository test fixture only. Install the build
# into a scratch prefix (distinct from GBB_TEST_INSTALL_PREFIX) and scan it by digest and name.
# The negative control hides the ROM under a neutral name, proving the digest scan itself.
set(GBB_LIBBET_INSTALL_CHECK "${PROJECT_BINARY_DIR}/libbet-install-check")
set(GBB_LIBBET_SCAN_SELFTEST "${PROJECT_BINARY_DIR}/libbet-scan-selftest")
file(MAKE_DIRECTORY "${GBB_LIBBET_SCAN_SELFTEST}/share")
file(COPY_FILE "${PROJECT_SOURCE_DIR}/fixtures/libbet/libbet.gb"
  "${GBB_LIBBET_SCAN_SELFTEST}/share/payload.bin")
add_test(NAME libbet_install_tree
  COMMAND ${CMAKE_COMMAND} --install ${PROJECT_BINARY_DIR} --prefix ${GBB_LIBBET_INSTALL_CHECK})
set_tests_properties(libbet_install_tree PROPERTIES FIXTURES_SETUP libbet_install TIMEOUT 120)
gbb_add_expect_exit_test(libbet_not_installed 0 "libbet absent from scanned tree files=[1-9]"
  --scan-dir "${GBB_LIBBET_INSTALL_CHECK}")
set_tests_properties(libbet_not_installed PROPERTIES FIXTURES_REQUIRED libbet_install)
gbb_add_expect_exit_test(libbet_not_installed_selftest 1 "libbet-installed: share/payload.bin"
  --scan-dir "${GBB_LIBBET_SCAN_SELFTEST}")

# Sibling Mooneye MBC ROM redistribution guard (D-31, D-32). The 15 derivatives, including the
# 4 MiB and 8 MiB ROMs, are repository fixtures only. cmake/ScanForbiddenFixtures.cmake scans the
# same install tree by name and digest and asserts the exact installed fixture directories. The
# four self-tests prove the scan can fail: a renamed ROM, a ROM behind an innocuously named
# symbolic link (a copy where the platform cannot create one), an empty tree and an extra directory.
set(GBB_MBC_SCAN_SCRIPT "${PROJECT_SOURCE_DIR}/cmake/ScanForbiddenFixtures.cmake")
set(GBB_MBC_SCAN_MANIFEST "${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc/manifest.json")
set(GBB_MBC_SCAN_DIRS "tracer|visible-demo|mbc1-continuation")
set(GBB_MBC_SCAN_SELFTEST "${PROJECT_BINARY_DIR}/mooneye-mbc-scan-selftest")
set(GBB_MBC_SCAN_EMPTY "${PROJECT_BINARY_DIR}/mooneye-mbc-scan-empty")
set(GBB_MBC_DIRS_SELFTEST "${PROJECT_BINARY_DIR}/mooneye-mbc-dirs-selftest")
set(GBB_MBC_SCAN_LINK "${PROJECT_BINARY_DIR}/mooneye-mbc-scan-link")
file(MAKE_DIRECTORY "${GBB_MBC_SCAN_SELFTEST}/share" "${GBB_MBC_SCAN_EMPTY}")
file(COPY_FILE "${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc/mbc5_rom_512kb.gb"
  "${GBB_MBC_SCAN_SELFTEST}/share/payload.bin")
file(MAKE_DIRECTORY "${GBB_MBC_SCAN_LINK}/share")
file(REMOVE "${GBB_MBC_SCAN_LINK}/share/innocuous.bin")
# Native separators: a Windows symbolic link whose target uses '/' does not resolve.
file(TO_NATIVE_PATH "${PROJECT_SOURCE_DIR}/fixtures/mooneye-mbc/mbc2_rom_512kb.gb" GBB_MBC_LINK_TARGET)
file(CREATE_LINK "${GBB_MBC_LINK_TARGET}" "${GBB_MBC_SCAN_LINK}/share/innocuous.bin" SYMBOLIC COPY_ON_ERROR)
foreach(dir IN ITEMS tracer visible-demo mbc1-continuation extra)
  file(WRITE "${GBB_MBC_DIRS_SELFTEST}/share/gabbaboy/fixtures/${dir}/marker.txt" "marker\n")
endforeach()
function(gbb_add_mbc_scan_test name code regex scan_dir)
  set(command "${CMAKE_COMMAND}" "-DGBB_SCAN_DIR=${scan_dir}"
    "-DGBB_FORBIDDEN_MANIFEST=${GBB_MBC_SCAN_MANIFEST}" ${ARGN} -P "${GBB_MBC_SCAN_SCRIPT}")
  list(JOIN command "$<SEMICOLON>" joined)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${joined}"
      -DGBB_EXPECT_CODE=${code}
      "-DGBB_EXPECT_REGEX=${regex}"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT 60)
endfunction()
gbb_add_mbc_scan_test(mooneye_mbc_not_installed 0 "mooneye-mbc absent from scanned tree files=[1-9]"
  "${GBB_LIBBET_INSTALL_CHECK}" "-DGBB_EXPECT_FIXTURE_DIRS=${GBB_MBC_SCAN_DIRS}")
set_tests_properties(mooneye_mbc_not_installed PROPERTIES FIXTURES_REQUIRED libbet_install)
gbb_add_mbc_scan_test(mooneye_mbc_not_installed_selftest 1 "mooneye-installed: share/payload.bin"
  "${GBB_MBC_SCAN_SELFTEST}")
gbb_add_mbc_scan_test(mooneye_mbc_not_installed_link_selftest 1 "mooneye-installed: share/innocuous.bin"
  "${GBB_MBC_SCAN_LINK}")
gbb_add_mbc_scan_test(mooneye_mbc_not_installed_empty 1 "scan-dir-empty"
  "${GBB_MBC_SCAN_EMPTY}")
gbb_add_mbc_scan_test(mooneye_mbc_fixture_dirs_selftest 1 "fixture-dirs-mismatch"
  "${GBB_MBC_DIRS_SELFTEST}" "-DGBB_EXPECT_FIXTURE_DIRS=${GBB_MBC_SCAN_DIRS}")

# Mooneye CGB ROM redistribution guard (D-26, T-10-22). The four third-party CGB derivatives are
# repository fixtures only; the same scan runs over the install tree with the CGB manifest's size and
# digest list. The self-test plants one CGB ROM under an innocuous name, so a pass cannot come
# from a scan that never matches by bytes.
set(GBB_CGB_MOONEYE_SCAN_SELFTEST "${PROJECT_BINARY_DIR}/mooneye-cgb-scan-selftest")
file(MAKE_DIRECTORY "${GBB_CGB_MOONEYE_SCAN_SELFTEST}/share")
file(COPY_FILE "${PROJECT_SOURCE_DIR}/fixtures/mooneye-cgb/boot_regs-cgb.gb"
  "${GBB_CGB_MOONEYE_SCAN_SELFTEST}/share/payload.bin")
function(gbb_add_cgb_mooneye_scan_test name code regex scan_dir)
  set(command "${CMAKE_COMMAND}" "-DGBB_SCAN_DIR=${scan_dir}"
    "-DGBB_FORBIDDEN_MANIFEST=${PROJECT_SOURCE_DIR}/fixtures/mooneye-cgb/manifest.json"
    -P "${PROJECT_SOURCE_DIR}/cmake/ScanForbiddenFixtures.cmake")
  list(JOIN command "$<SEMICOLON>" joined)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${joined}"
      -DGBB_EXPECT_CODE=${code}
      "-DGBB_EXPECT_REGEX=${regex}"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT 60)
endfunction()
gbb_add_cgb_mooneye_scan_test(cgb_mooneye_not_installed 0 "mooneye-mbc absent from scanned tree files=[1-9]"
  "${GBB_LIBBET_INSTALL_CHECK}")
set_tests_properties(cgb_mooneye_not_installed PROPERTIES FIXTURES_REQUIRED libbet_install)
gbb_add_cgb_mooneye_scan_test(cgb_mooneye_not_installed_selftest 1 "mooneye-installed: share/payload.bin"
  "${GBB_CGB_MOONEYE_SCAN_SELFTEST}")

# MagenTests redistribution guard (D-06): same scan, label magentests, digest list from its manifest.
# The renamed-copy self-test proves the scan matches by size and digest, not by file name.
set(GBB_MAGENTESTS_SCAN_SELFTEST "${PROJECT_BINARY_DIR}/magentests-scan-selftest")
file(MAKE_DIRECTORY "${GBB_MAGENTESTS_SCAN_SELFTEST}/share")
file(COPY_FILE "${PROJECT_SOURCE_DIR}/fixtures/magentests/mbc_oob_sram_mbc3.gbc"
  "${GBB_MAGENTESTS_SCAN_SELFTEST}/share/payload.bin")
set(GBB_MAGENTESTS_SCAN_ARGS "-DGBB_FORBIDDEN_MANIFEST=${GBB_MAGENTESTS_DIR}/manifest.json"
  -DGBB_FORBIDDEN_LABEL=magentests)
function(gbb_add_magentests_scan_test name code regex scan_dir)
  set(command "${CMAKE_COMMAND}" "-DGBB_SCAN_DIR=${scan_dir}" ${GBB_MAGENTESTS_SCAN_ARGS}
    -P "${GBB_MBC_SCAN_SCRIPT}")
  list(JOIN command "$<SEMICOLON>" joined)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${joined}"
      -DGBB_EXPECT_CODE=${code}
      "-DGBB_EXPECT_REGEX=${regex}"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT 60)
endfunction()
gbb_add_magentests_scan_test(magentests_not_installed 0 "magentests absent from scanned tree files=[1-9]"
  "${GBB_LIBBET_INSTALL_CHECK}")
set_tests_properties(magentests_not_installed PROPERTIES FIXTURES_REQUIRED libbet_install)
gbb_add_magentests_scan_test(magentests_not_installed_selftest 1 "magentests-installed: share/payload.bin"
  "${GBB_MAGENTESTS_SCAN_SELFTEST}")

# EVID-02 baseline comparator self-tests (D-30, D-31, D-34). Each test runs cmake/VerifyDmgBaseline.cmake
# on committed synthetic fixtures (or a generated variant of them) and asserts the exact exit code
# and failure token through expect_exit.cmake; nothing here touches the real ledger.
set(GBB_BASELINE_SCRIPT "${PROJECT_SOURCE_DIR}/cmake/VerifyDmgBaseline.cmake")
set(GBB_BASELINE_SELFTEST "${PROJECT_SOURCE_DIR}/tests/baseline/selftest")
set(GBB_BASELINE_DIR "${PROJECT_BINARY_DIR}/baseline-selftest")
file(MAKE_DIRECTORY "${GBB_BASELINE_DIR}")

function(gbb_add_baseline_test name code regex)
  set(command "${CMAKE_COMMAND}" "-DGBB_SOURCE_DIR=${PROJECT_SOURCE_DIR}" ${ARGN} -P "${GBB_BASELINE_SCRIPT}")
  list(JOIN command "$<SEMICOLON>" joined)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${joined}"
      -DGBB_EXPECT_CODE=${code}
      "-DGBB_EXPECT_REGEX=${regex}"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT 30)
endfunction()

file(READ "${GBB_BASELINE_SELFTEST}/observed.txt" GBB_BASELINE_OBSERVED)
file(READ "${GBB_BASELINE_SELFTEST}/ledger.txt" GBB_BASELINE_LEDGER)
file(READ "${GBB_BASELINE_SELFTEST}/CHANGES.md" GBB_BASELINE_CHANGES_ROW)
# The committed CHANGES fixture carries one row for the recorded-change variant; every other test
# compares against the same table with that row removed.
string(ASCII 10 GBB_NL)
string(REGEX REPLACE "${GBB_NL}[|] acceptance[^${GBB_NL}]*${GBB_NL}?" "${GBB_NL}"
  GBB_BASELINE_CHANGES_EMPTY "${GBB_BASELINE_CHANGES_ROW}")
file(WRITE "${GBB_BASELINE_DIR}/changes_empty.md" "${GBB_BASELINE_CHANGES_EMPTY}")

gbb_add_baseline_test(dmg_baseline_selftest_pass 0 "baseline status=pass"
  -DGBB_MODE=check
  "-DGBB_OBSERVED=${GBB_BASELINE_SELFTEST}/observed.txt"
  "-DGBB_LEDGER=${GBB_BASELINE_SELFTEST}/ledger.txt"
  "-DGBB_CHANGES=${GBB_BASELINE_DIR}/changes_empty.md")

# One generated variant per failure category. Each differs from the committed synthetic fixtures by
# exactly one fact, so the category it names is the only thing that can make the comparator fail.
string(ASCII 9 GBB_TAB)
set(GBB_PCM_OLD "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
set(GBB_PCM_NEW "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
set(GBB_PCM_OTHER "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc")
set(GBB_BASELINE_ROW_TAIL "| synthetic reason | regression fixture (self-test only) | self-test |\n")

function(gbb_baseline_variant name ledger observed changes)
  file(WRITE "${GBB_BASELINE_DIR}/${name}.ledger.txt" "${ledger}")
  file(WRITE "${GBB_BASELINE_DIR}/${name}.observed.txt" "${observed}")
  file(WRITE "${GBB_BASELINE_DIR}/${name}.changes.md" "${changes}")
endfunction()

function(gbb_add_baseline_variant_test name code regex)
  gbb_add_baseline_test(dmg_baseline_${name} ${code} "${regex}"
    -DGBB_MODE=check
    "-DGBB_OBSERVED=${GBB_BASELINE_DIR}/${name}.observed.txt"
    "-DGBB_LEDGER=${GBB_BASELINE_DIR}/${name}.ledger.txt"
    "-DGBB_CHANGES=${GBB_BASELINE_DIR}/${name}.changes.md")
endfunction()

set(GBB_OBS "${GBB_BASELINE_OBSERVED}")
set(GBB_LED "${GBB_BASELINE_LEDGER}")
set(GBB_CHG "${GBB_BASELINE_CHANGES_EMPTY}")
string(REPLACE "${GBB_PCM_OLD}" "${GBB_PCM_NEW}" GBB_OBS_CHANGED "${GBB_OBS}")
string(REPLACE "${GBB_PCM_OLD}" "${GBB_PCM_NEW}" GBB_LED_CHANGED "${GBB_LED}")

# Observation drift: a digest changed, a ledger key vanished, an unknown key appeared, an inventory name left.
gbb_baseline_variant(modified "${GBB_LED}" "${GBB_OBS_CHANGED}" "${GBB_CHG}")
string(REPLACE "mooneye.daa.frame_generation${GBB_TAB}12\n" "" GBB_OBS_MISSING "${GBB_OBS}")
gbb_baseline_variant(missing "${GBB_LED}" "${GBB_OBS_MISSING}" "${GBB_CHG}")
gbb_baseline_variant(extra "${GBB_LED}" "${GBB_OBS}acceptance.libbet.unexpected${GBB_TAB}1\n" "${GBB_CHG}")
string(REPLACE "inventory.core.beta_test${GBB_TAB}frozen\n" "" GBB_OBS_REMOVED "${GBB_OBS}")
gbb_baseline_variant(inventory_removed "${GBB_LED}" "${GBB_OBS_REMOVED}" "${GBB_CHG}")

# Approved-change protocol: the same ledger edit fails without a CHANGES row and passes with it.
gbb_baseline_variant(changes_unrecorded "${GBB_LED_CHANGED}" "${GBB_OBS_CHANGED}" "${GBB_CHG}")
gbb_baseline_variant(changes_recorded "${GBB_LED_CHANGED}" "${GBB_OBS_CHANGED}" "${GBB_BASELINE_CHANGES_ROW}")
gbb_baseline_variant(changes_noop "${GBB_LED}" "${GBB_OBS}"
  "${GBB_CHG}| acceptance.libbet.pcm_sha256 | ${GBB_PCM_OLD} | ${GBB_PCM_OLD} ${GBB_BASELINE_ROW_TAIL}")
gbb_baseline_variant(changes_inconsistent "${GBB_LED}" "${GBB_OBS}"
  "${GBB_CHG}| acceptance.libbet.pcm_sha256 | ${GBB_PCM_OTHER} | ${GBB_PCM_NEW} ${GBB_BASELINE_ROW_TAIL}")

# Ledger shape: ordering, duplicate key, empty ledger, empty section, empty observations, bad line, bad header.
string(REPLACE
  "inventory.core.alpha_test${GBB_TAB}frozen\ninventory.core.beta_test${GBB_TAB}frozen\n"
  "inventory.core.beta_test${GBB_TAB}frozen\ninventory.core.alpha_test${GBB_TAB}frozen\n"
  GBB_LED_UNSORTED "${GBB_LED}")
gbb_baseline_variant(unsorted "${GBB_LED_UNSORTED}" "${GBB_OBS}" "${GBB_CHG}")
string(REPLACE "bench.tracer.workload${GBB_TAB}original-wram-tracer-1m-half-dots-v1\n"
  "bench.tracer.workload${GBB_TAB}original-wram-tracer-1m-half-dots-v1\nbench.tracer.workload${GBB_TAB}original-wram-tracer-1m-half-dots-v1\n"
  GBB_LED_DUPLICATE "${GBB_LED}")
gbb_baseline_variant(duplicate_key "${GBB_LED_DUPLICATE}" "${GBB_OBS}" "${GBB_CHG}")
gbb_baseline_variant(empty "" "${GBB_OBS}" "${GBB_CHG}")
string(REGEX REPLACE "mooneye[.][^${GBB_NL}]*${GBB_NL}" "" GBB_LED_NO_MOONEYE "${GBB_LED}")
gbb_baseline_variant(empty_section "${GBB_LED_NO_MOONEYE}" "${GBB_OBS}" "${GBB_CHG}")
gbb_baseline_variant(empty_observations "${GBB_LED}" "" "${GBB_CHG}")
string(REPLACE "bench.tracer.workload${GBB_TAB}" "bench.tracer${GBB_TAB}workload${GBB_TAB}" GBB_LED_MALFORMED "${GBB_LED}")
gbb_baseline_variant(malformed_line "${GBB_LED_MALFORMED}" "${GBB_OBS}" "${GBB_CHG}")
string(REPLACE "0123456789abcdef0123456789abcdef01234567" "0123456789abcdef0123456789abcdef0123456"
  GBB_LED_HEADER "${GBB_LED}")
gbb_baseline_variant(header_invalid "${GBB_LED_HEADER}" "${GBB_OBS}" "${GBB_CHG}")

gbb_add_baseline_variant_test(changes_recorded 0 "baseline status=pass")
gbb_add_baseline_variant_test(modified 1 "acceptance=fail.*modified")
gbb_add_baseline_variant_test(missing 1 "mooneye=fail.*missing")
gbb_add_baseline_variant_test(extra 1 "acceptance=fail.*extra")
gbb_add_baseline_variant_test(inventory_removed 1 "inventory=fail.*removed")
gbb_add_baseline_variant_test(changes_unrecorded 1 "unrecorded-change")
gbb_add_baseline_variant_test(unsorted 1 "unsorted-ledger")
gbb_add_baseline_variant_test(duplicate_key 1 "duplicate-key")
gbb_add_baseline_variant_test(empty 1 "empty-ledger")
gbb_add_baseline_variant_test(changes_noop 1 "changes-noop")
gbb_add_baseline_variant_test(changes_inconsistent 1 "changes-inconsistent")
gbb_add_baseline_variant_test(empty_section 1 "empty-section")
gbb_add_baseline_variant_test(empty_observations 1 "empty-observations")
gbb_add_baseline_variant_test(malformed_line 1 "malformed-line")
gbb_add_baseline_variant_test(header_invalid 1 "header-invalid")

# JUnit inventory checks run on a synthetic report: every frozen core name must appear as a testcase
# with no skipped, failure or error child. Plan 07-15 applies the same mode to the real CI reports.
file(READ "${GBB_BASELINE_SELFTEST}/junit.xml" GBB_JUNIT)
set(GBB_BETA_CASE "<testcase name=\"beta_test\" classname=\"beta_test\" time=\"0.01\" status=\"run\"/>")
string(REPLACE "  ${GBB_BETA_CASE}\n" "" GBB_JUNIT_MISSING "${GBB_JUNIT}")
string(REPLACE "${GBB_BETA_CASE}"
  "<testcase name=\"beta_test\" classname=\"beta_test\" time=\"0.01\" status=\"notrun\"><skipped/></testcase>"
  GBB_JUNIT_SKIPPED "${GBB_JUNIT}")
string(REPLACE "${GBB_BETA_CASE}"
  "<testcase name=\"beta_test\" classname=\"beta_test\" time=\"0.01\" status=\"fail\"><failure message=\"x\"/></testcase>"
  GBB_JUNIT_FAILED "${GBB_JUNIT}")
file(WRITE "${GBB_BASELINE_DIR}/junit_missing.xml" "${GBB_JUNIT_MISSING}")
file(WRITE "${GBB_BASELINE_DIR}/junit_skipped.xml" "${GBB_JUNIT_SKIPPED}")
file(WRITE "${GBB_BASELINE_DIR}/junit_failed.xml" "${GBB_JUNIT_FAILED}")

function(gbb_add_baseline_junit_test name code regex report)
  gbb_add_baseline_test(dmg_baseline_${name} ${code} "${regex}"
    -DGBB_MODE=junit -DGBB_INVENTORY=core
    "-DGBB_LEDGER=${GBB_BASELINE_SELFTEST}/ledger.txt"
    "-DGBB_JUNIT=${report}")
endfunction()
gbb_add_baseline_junit_test(junit_pass 0 "baseline junit=ok" "${GBB_BASELINE_SELFTEST}/junit.xml")
gbb_add_baseline_junit_test(junit_missing 1 "junit-missing" "${GBB_BASELINE_DIR}/junit_missing.xml")
gbb_add_baseline_junit_test(junit_skipped 1 "junit-skipped" "${GBB_BASELINE_DIR}/junit_skipped.xml")
gbb_add_baseline_junit_test(junit_failed 1 "junit-failed" "${GBB_BASELINE_DIR}/junit_failed.xml")

# The live EVID-02 check (D-31, D-33): recomputes every observation from this build and compares it
# with the frozen tests/baseline/dmg-cpu-b-v1.txt. One ledger serves every OS, so the same test and
# the same expected line run on Linux, macOS and Windows.
add_test(NAME dmg_baseline
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MODE=check
    -DGBB_SOURCE_DIR=${PROJECT_SOURCE_DIR}
    -DGBB_RUNNER=$<TARGET_FILE:gabbaboy-runner>
    -DGBB_MEASURE=$<TARGET_FILE:measure_core>
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyDmgBaseline.cmake)
set_tests_properties(dmg_baseline PROPERTIES TIMEOUT 300
  PASS_REGULAR_EXPRESSION "baseline status=pass")

# include(), not add_subdirectory(): ExpectedTests.cmake reads this directory's TESTS property only.
include(${CMAKE_CURRENT_LIST_DIR}/acceptance/CMakeLists.txt)

# No host clock in the portable core (D-13). The RTC advances only from emulated time, so the
# source layer rejects host time headers and calls in src/core and the public header, and the
# object layer rejects linked clock, sleep and environment symbols in the compiled core library.
# Two negative controls prove the checks can fail: a scratch source with the forbidden header and
# call, and an injected symbol list. Both exit through expect_exit.cmake with the exact code 1.
set(GBB_NO_HOST_CLOCK_SCRIPT "${PROJECT_SOURCE_DIR}/cmake/CheckCoreNoHostClock.cmake")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${GBB_NO_HOST_CLOCK_SCRIPT})
add_test(NAME no_host_clock
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_SOURCE_DIRS=${PROJECT_SOURCE_DIR}/src/core$<SEMICOLON>${PROJECT_SOURCE_DIR}/include/gabbaboy"
    "-DGBB_CORE_LIBRARY=$<TARGET_FILE:gabbaboy_core>"
    "-DGBB_NM=${CMAKE_NM}"
    "-DGBB_LINKER=${CMAKE_LINKER}"
    "-DGBB_C_COMPILER=${CMAKE_C_COMPILER}"
    -P ${GBB_NO_HOST_CLOCK_SCRIPT})

file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/no-host-clock-selftest")
file(WRITE "${PROJECT_BINARY_DIR}/no-host-clock-selftest/bad.c"
  "#include <time.h>\nint host_seconds(void) { return (int)time(NULL); }\n")
add_test(NAME no_host_clock_selftest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_SOURCE_DIRS=${PROJECT_BINARY_DIR}/no-host-clock-selftest;-DGBB_SYMBOLS_FILE=;-P;${GBB_NO_HOST_CLOCK_SCRIPT}"
    -DGBB_EXPECT_CODE=1
    -DGBB_EXPECT_REGEX=no-host-clock-include
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

file(WRITE "${PROJECT_BINARY_DIR}/no-host-clock-selftest/symbols.txt" "_time\n_malloc\n")
add_test(NAME no_host_clock_symbol_selftest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_SYMBOLS_FILE=${PROJECT_BINARY_DIR}/no-host-clock-selftest/symbols.txt;-P;${GBB_NO_HOST_CLOCK_SCRIPT}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=no-host-clock-symbol: time"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

# A "/*" inside a // comment must not hide the code after it from the source layer.
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/no-host-clock-comment-selftest")
file(WRITE "${PROJECT_BINARY_DIR}/no-host-clock-comment-selftest/bad.c"
  "// a line comment that mentions /* must not open a block comment\n"
  "long host_ticks(void) { return (long)clock(); }\n"
  "/* a later block comment */\n")
add_test(NAME no_host_clock_comment_selftest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_SOURCE_DIRS=${PROJECT_BINARY_DIR}/no-host-clock-comment-selftest;-DGBB_SYMBOLS_FILE=;-P;${GBB_NO_HOST_CLOCK_SCRIPT}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=no-host-clock-call: [^\n]*bad[.]c [(]clock[)]"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

# The Phase 9 evidence ledger cites registered test names in its claim tables (T-09-34). A rename
# or removal must fail here rather than leave the ledger claiming evidence that no longer runs.
set(GBB_EVIDENCE_LEDGER_SCRIPT "${PROJECT_SOURCE_DIR}/cmake/VerifyEvidenceLedger.cmake")
set(GBB_EVIDENCE_INVENTORIES
  "${PROJECT_SOURCE_DIR}/tests/expected-tests.txt$<SEMICOLON>${PROJECT_SOURCE_DIR}/tests/player/expected-tests.txt")
add_test(NAME mbc3_rtc_evidence_ledger_names
  COMMAND ${CMAKE_COMMAND}
    -DGBB_LEDGER=${PROJECT_SOURCE_DIR}/docs/mbc3-rtc-evidence.md
    "-DGBB_INVENTORIES=${GBB_EVIDENCE_INVENTORIES}"
    -P ${GBB_EVIDENCE_LEDGER_SCRIPT})
set_tests_properties(mbc3_rtc_evidence_ledger_names PROPERTIES
  PASS_REGULAR_EXPRESSION "evidence-ledger pass names=[1-9]")

file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/evidence-ledger-selftest")
file(WRITE "${PROJECT_BINARY_DIR}/evidence-ledger-selftest/ledger.md"
  "## Claim table\n\n| Claim | Tests |\n|---|---|\n| renamed test | `rtc_latch_edges`, `rtc_no_such_test` |\n")
add_test(NAME mbc3_rtc_evidence_ledger_selftest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_LEDGER=${PROJECT_BINARY_DIR}/evidence-ledger-selftest/ledger.md;-DGBB_INVENTORIES=${PROJECT_SOURCE_DIR}/tests/expected-tests.txt;-P;${GBB_EVIDENCE_LEDGER_SCRIPT}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=evidence-ledger-unregistered: rtc_no_such_test"
    "-DGBB_FORBID_REGEX=unregistered: rtc_latch_edges"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

# The host guide must name only declared symbols and example variables and keep every RTC behavior the header promises
# (catch-up rules, error codes, battery image layout), so its adequacy is a CI result.
set(GBB_DOC_CONTRACT_SCRIPT "${PROJECT_SOURCE_DIR}/cmake/VerifyDocContract.cmake")
set(GBB_NATIVE_GUIDE_RTC_PHRASES
  "`gbb_rtc_catch_up` applies host wall-clock time"
  "(`$0F`, `$10`)"
  "non-negative whole-second elapsed value"
  "once per open"
  "two calls add twice"
  "as an input event"
  "A negative value returns `GBB_INVALID_ARGUMENT` and changes nothing"
  "returns `GBB_NO_RTC`"
  "never advances it"
  "`GBB_RTC_BLOCK_SIZE`-byte clock block"
  "(the block alone for `$0F`)"
  "never reads the host clock")
add_test(NAME native_guide_rtc_contract
  COMMAND ${CMAKE_COMMAND}
    -DGBB_DOC=${PROJECT_SOURCE_DIR}/docs/native-integration.md
    "-DGBB_DECLARATIONS=${PROJECT_SOURCE_DIR}/include/gabbaboy/gabbaboy.h;${PROJECT_SOURCE_DIR}/examples/relocated-c/CMakeLists.txt"
    "-DGBB_REQUIRED=${GBB_NATIVE_GUIDE_RTC_PHRASES}"
    "-DGBB_SCOPE_START=`gbb_rtc_catch_up` applies host wall-clock time"
    -P ${GBB_DOC_CONTRACT_SCRIPT})
set_tests_properties(native_guide_rtc_contract PROPERTIES
  PASS_REGULAR_EXPRESSION "doc-contract pass identifiers=[1-9][0-9]* phrases=12[^0-9]")

file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/doc-contract-selftest")
file(WRITE "${PROJECT_BINARY_DIR}/doc-contract-selftest/guide.md"
  "Call `gbb_rtc_catch_up`, then\n  `gbb_no_such_call` once per\n  open.\n")
add_test(NAME doc_contract_undeclared_selftest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_DOC=${PROJECT_BINARY_DIR}/doc-contract-selftest/guide.md;-DGBB_DECLARATIONS=${PROJECT_SOURCE_DIR}/include/gabbaboy/gabbaboy.h;-DGBB_REQUIRED=once per open;-P;${GBB_DOC_CONTRACT_SCRIPT}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=doc-contract-undeclared: gbb_no_such_call"
    "-DGBB_FORBID_REGEX=undeclared: gbb_rtc_catch_up|doc-contract-missing"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
add_test(NAME doc_contract_missing_selftest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_DOC=${PROJECT_BINARY_DIR}/doc-contract-selftest/guide.md;-DGBB_DECLARATIONS=${PROJECT_SOURCE_DIR}/include/gabbaboy/gabbaboy.h;-DGBB_REQUIRED=two calls add twice;-P;${GBB_DOC_CONTRACT_SCRIPT}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=doc-contract-missing: two calls add twice"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

# Each rule that could pass vacuously has its own failing control.
set(GBB_DOC_SELFTEST "${PROJECT_BINARY_DIR}/doc-contract-selftest")
file(WRITE "${GBB_DOC_SELFTEST}/ghost.h" "/* gbb_ghost_call was renamed */\n// gbb_line_ghost /* still a comment\nint gbb_real_call(void);\n")
file(WRITE "${GBB_DOC_SELFTEST}/comment.md" "Call `gbb_real_call`, not `gbb_line_ghost`.\n")
add_test(NAME doc_contract_comment_only_selftest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_DOC=${GBB_DOC_SELFTEST}/comment.md;-DGBB_DECLARATIONS=${GBB_DOC_SELFTEST}/ghost.h;-DGBB_REQUIRED=Call;-P;${GBB_DOC_CONTRACT_SCRIPT}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=doc-contract-undeclared: gbb_line_ghost"
    "-DGBB_FORBID_REGEX=undeclared: gbb_real_call"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
file(WRITE "${GBB_DOC_SELFTEST}/prefix.md" "Call `gbb_rtc` and `libgbb_ghost_tail`.\n")
add_test(NAME doc_contract_word_boundary_selftest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_DOC=${GBB_DOC_SELFTEST}/prefix.md;-DGBB_DECLARATIONS=${PROJECT_SOURCE_DIR}/include/gabbaboy/gabbaboy.h;-DGBB_REQUIRED=Call;-P;${GBB_DOC_CONTRACT_SCRIPT}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=doc-contract-undeclared: gbb_rtc[^_]"
    "-DGBB_FORBID_REGEX=gbb_ghost_tail"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
add_test(NAME doc_contract_empty_phrase_selftest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_DOC=${GBB_DOC_SELFTEST}/guide.md;-DGBB_DECLARATIONS=${PROJECT_SOURCE_DIR}/include/gabbaboy/gabbaboy.h;-DGBB_REQUIRED=  ;-P;${GBB_DOC_CONTRACT_SCRIPT}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=doc-contract-empty-phrase"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
file(WRITE "${GBB_DOC_SELFTEST}/scope.md" "Call it once per open.\n\nThe `gbb_rtc_catch_up` rule:\n<!-- once per open -->\nsee above.\n")
add_test(NAME doc_contract_scope_selftest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_DOC=${GBB_DOC_SELFTEST}/scope.md;-DGBB_DECLARATIONS=${PROJECT_SOURCE_DIR}/include/gabbaboy/gabbaboy.h;-DGBB_REQUIRED=once per open;-DGBB_SCOPE_START=The `gbb_rtc_catch_up` rule;-P;${GBB_DOC_CONTRACT_SCRIPT}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=doc-contract-missing: once per open"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

# CGB host-guide contract (D-28): the CGB section of the integration guide names only declared symbols
# and keeps each promise the header makes about the info API, PGB rejection, frame copy, banking and
# deferred registers. The missing-phrase selftest proves the check can fail.
set(GBB_NATIVE_GUIDE_CGB_PHRASES
  "sets it to 28"
  "outputs unchanged on error"
  "returns `GBB_UNSUPPORTED_EXECUTION_MODE`"
  "returns `GBB_UNSUPPORTED_PROFILE` on the CGB profile"
  "follows the selected WRAM bank"
  "stop with `GBB_STOP_UNSUPPORTED_BUS`")
list(LENGTH GBB_NATIVE_GUIDE_CGB_PHRASES GBB_NATIVE_GUIDE_CGB_PHRASE_COUNT)
set(GBB_NATIVE_GUIDE_CGB_SCOPE "The CGB-CPU-E profile is selected with")
set(GBB_NATIVE_GUIDE_CGB_DECLS
  "${PROJECT_SOURCE_DIR}/include/gabbaboy/gabbaboy.h;${PROJECT_SOURCE_DIR}/examples/relocated-c/CMakeLists.txt")
add_test(NAME cgb_native_guide_contract
  COMMAND ${CMAKE_COMMAND}
    -DGBB_DOC=${PROJECT_SOURCE_DIR}/docs/native-integration.md
    "-DGBB_DECLARATIONS=${GBB_NATIVE_GUIDE_CGB_DECLS}"
    "-DGBB_REQUIRED=${GBB_NATIVE_GUIDE_CGB_PHRASES}"
    "-DGBB_SCOPE_START=${GBB_NATIVE_GUIDE_CGB_SCOPE}"
    -P ${GBB_DOC_CONTRACT_SCRIPT})
set_tests_properties(cgb_native_guide_contract PROPERTIES
  PASS_REGULAR_EXPRESSION "doc-contract pass identifiers=[1-9][0-9]* phrases=${GBB_NATIVE_GUIDE_CGB_PHRASE_COUNT}[^0-9]")
file(READ "${PROJECT_SOURCE_DIR}/docs/native-integration.md" gbb_cgb_guide_text)
set(gbb_cgb_guide_anchor "outputs unchanged on error")
string(FIND "${gbb_cgb_guide_text}" "${gbb_cgb_guide_anchor}" gbb_cgb_first)
string(FIND "${gbb_cgb_guide_text}" "${gbb_cgb_guide_anchor}" gbb_cgb_last REVERSE)
if(gbb_cgb_first EQUAL -1 OR NOT gbb_cgb_first EQUAL gbb_cgb_last)
  message(FATAL_ERROR "CGB guide selftest anchor '${gbb_cgb_guide_anchor}' must occur exactly once")
endif()
string(REPLACE "${gbb_cgb_guide_anchor}" "outputs kept" gbb_cgb_guide_missing_text "${gbb_cgb_guide_text}")
file(WRITE "${PROJECT_BINARY_DIR}/cgb-guide-selftest/missing.md" "${gbb_cgb_guide_missing_text}")
add_test(NAME cgb_native_guide_contract_missing_selftest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_DOC=${PROJECT_BINARY_DIR}/cgb-guide-selftest/missing.md;-DGBB_DECLARATIONS=${GBB_NATIVE_GUIDE_CGB_DECLS};-DGBB_REQUIRED=outputs unchanged on error;-DGBB_SCOPE_START=${GBB_NATIVE_GUIDE_CGB_SCOPE};-P;${GBB_DOC_CONTRACT_SCRIPT}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=doc-contract-missing: outputs unchanged on error"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

# Half-dot timeline ADR (D-070, D-20, D-21): the doc section may name only macros declared in the core,
# and must keep each rule the ADR states. The static asserts in src/core/gabbaboy.c make the numbers
# compile-time facts; a mutant TU (below) proves they can fail.
set(GBB_ADR_DOC "${PROJECT_SOURCE_DIR}/docs/cgb-profile.md")
set(GBB_ADR_SCOPE_START "The `uint64_t` half-dot master timeline")
set(GBB_ADR_HALF_DOT_PHRASES
  "single clock for normal and double speed"
  "`GBB_MASTER_HALF_DOTS_PER_SECOND` is 2^23"
  "`GBB_HALF_DOTS_PER_T_NORMAL` (2)"
  "`GBB_HALF_DOTS_PER_T_DOUBLE` (1)"
  "`GBB_T_PER_M` (4)"
  "`GBB_HALF_DOTS_PER_DOT` (2)"
  "140448 half-dots"
  "never reads `double_speed`")
list(LENGTH GBB_ADR_HALF_DOT_PHRASES GBB_ADR_HALF_DOT_PHRASE_COUNT)
add_test(NAME cgb_adr_half_dot_contract
  COMMAND ${CMAKE_COMMAND}
    -DGBB_DOC=${GBB_ADR_DOC}
    "-DGBB_DECLARATIONS=${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c;${PROJECT_SOURCE_DIR}/include/gabbaboy/gabbaboy.h"
    "-DGBB_REQUIRED=${GBB_ADR_HALF_DOT_PHRASES}"
    "-DGBB_SCOPE_START=${GBB_ADR_SCOPE_START}"
    -P ${GBB_DOC_CONTRACT_SCRIPT})
set_tests_properties(cgb_adr_half_dot_contract PROPERTIES
  PASS_REGULAR_EXPRESSION "doc-contract pass identifiers=[1-9][0-9]* phrases=${GBB_ADR_HALF_DOT_PHRASE_COUNT}[^0-9]")

# Negative controls for the ADR contract: each doc copy breaks exactly one rule, so a pass cannot come
# from a check that never fails.
file(READ "${GBB_ADR_DOC}" gbb_adr_doc_text)
set(GBB_ADR_SELFTEST_DIR "${PROJECT_BINARY_DIR}/cgb-adr-selftest")
foreach(anchor IN ITEMS "`GBB_T_PER_M` (4)" "single clock for normal and double speed")
  string(FIND "${gbb_adr_doc_text}" "${anchor}" gbb_adr_first)
  string(FIND "${gbb_adr_doc_text}" "${anchor}" gbb_adr_last REVERSE)
  if(gbb_adr_first EQUAL -1 OR NOT gbb_adr_first EQUAL gbb_adr_last)
    message(FATAL_ERROR "ADR selftest anchor '${anchor}' must occur exactly once in ${GBB_ADR_DOC}")
  endif()
endforeach()
string(REPLACE "`GBB_T_PER_M` (4)" "`GBB_NO_SUCH_TIMELINE_MACRO` (4)" gbb_adr_undeclared_text "${gbb_adr_doc_text}")
string(REPLACE "single clock for normal and double speed" "clock" gbb_adr_missing_text "${gbb_adr_doc_text}")
file(WRITE "${GBB_ADR_SELFTEST_DIR}/undeclared.md" "${gbb_adr_undeclared_text}")
file(WRITE "${GBB_ADR_SELFTEST_DIR}/missing.md" "${gbb_adr_missing_text}")
foreach(kind IN ITEMS undeclared missing)
  if(kind STREQUAL "undeclared")
    set(gbb_adr_regex "doc-contract-undeclared: GBB_NO_SUCH_TIMELINE_MACRO")
  else()
    set(gbb_adr_regex "doc-contract-missing: single clock for normal and double speed")
  endif()
  add_test(NAME cgb_adr_half_dot_contract_${kind}_selftest
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_DOC=${GBB_ADR_SELFTEST_DIR}/${kind}.md;-DGBB_DECLARATIONS=${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c;-DGBB_REQUIRED=single clock for normal and double speed;-DGBB_SCOPE_START=${GBB_ADR_SCOPE_START};-P;${GBB_DOC_CONTRACT_SCRIPT}"
      -DGBB_EXPECT_CODE=1
      "-DGBB_EXPECT_REGEX=${gbb_adr_regex}"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
endforeach()

# Static-assert mutant: the core with the double-speed T-cycle changed from 1 to 2 half-dots must fail to
# compile on a "half-dot timeline:" assert. The library is EXCLUDE_FROM_ALL and never installed.
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c)
file(READ ${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c gbb_adr_core_text)
set(gbb_adr_anchor "#define GBB_HALF_DOTS_PER_T_DOUBLE 1u")
string(FIND "${gbb_adr_core_text}" "${gbb_adr_anchor}" gbb_adr_first)
string(FIND "${gbb_adr_core_text}" "${gbb_adr_anchor}" gbb_adr_last REVERSE)
if(gbb_adr_first EQUAL -1 OR NOT gbb_adr_first EQUAL gbb_adr_last)
  message(FATAL_ERROR "ADR mutant anchor '${gbb_adr_anchor}' must occur exactly once in src/core/gabbaboy.c")
endif()
string(REPLACE "${gbb_adr_anchor}" "#define GBB_HALF_DOTS_PER_T_DOUBLE 2u" gbb_adr_mutant_text "${gbb_adr_core_text}")
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_adr_mutant.c "${gbb_adr_mutant_text}")
add_library(gabbaboy_core_adr_mutant STATIC EXCLUDE_FROM_ALL ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_adr_mutant.c)
target_include_directories(gabbaboy_core_adr_mutant PUBLIC ${PROJECT_SOURCE_DIR}/include)
target_compile_features(gabbaboy_core_adr_mutant PUBLIC c_std_17)
set_target_properties(gabbaboy_core_adr_mutant PROPERTIES C_EXTENSIONS OFF)
target_compile_definitions(gabbaboy_core_adr_mutant PRIVATE GBB_BUILD_REVISION="adr-mutant" GBB_BUILD_QUALIFIED=0)
add_test(NAME cgb_adr_half_dot_static_assert_mutant
  COMMAND ${CMAKE_COMMAND} --build ${PROJECT_BINARY_DIR} --target gabbaboy_core_adr_mutant)
set_tests_properties(cgb_adr_half_dot_static_assert_mutant PROPERTIES
  PASS_REGULAR_EXPRESSION "half-dot timeline:" TIMEOUT 180)

# Model-gate scanner (CGB-02, decision D-08). Stdlib-only Python run with -I; every negative
# control goes through expect_exit.cmake so it must fail with exactly the expected reason.
set(GBB_MODEL_GATE_SCANNER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-model-gates.py")
set(GBB_MODEL_GATE_DIR "${PROJECT_BINARY_DIR}/model-gates")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${GBB_MODEL_GATE_SCANNER}")

function(gbb_add_model_gate_test name code regex)
  set(command "${Python3_EXECUTABLE}" -I "${GBB_MODEL_GATE_SCANNER}" ${ARGN})
  list(JOIN command "$<SEMICOLON>" joined)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${joined}"
      -DGBB_EXPECT_CODE=${code}
      "-DGBB_EXPECT_REGEX=${regex}"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT 60)
endfunction()

# Tracer corpus: two tagged functions, a matching doc, and a copy whose GATE-01 class is wrong.
file(MAKE_DIRECTORY "${GBB_MODEL_GATE_DIR}")
set(GBB_MODEL_GATE_TRACER_SOURCE [=[
/* MODEL: BOTH GATE-00 basis="model-neutral function" */
static int neutral(int x) { return x + 1; }

/* MODEL: DMG_ONLY GATE-01 GUARD=model_is_dmg */
static int dmg_only(int model) {
    if (model_is_dmg(model)) return 1;
    return 0;
}
]=])
set(GBB_MODEL_GATE_TRACER_DOC [=[
# Tracer corpus
<!-- model-gates-begin -->
| Gate | Class | Guard | Resolution | Site | Note |
| --- | --- | --- | --- | --- | --- |
| GATE-00 | BOTH | - | basis="model-neutral function" | any | shared |
| GATE-01 | DMG_ONLY | model_is_dmg | - | dmg_only | tracer |
<!-- model-gates-end -->
]=])
string(REPLACE "| GATE-01 | DMG_ONLY |" "| GATE-01 | BOTH |"
  GBB_MODEL_GATE_TRACER_DOC_BAD "${GBB_MODEL_GATE_TRACER_DOC}")
file(WRITE "${GBB_MODEL_GATE_DIR}/tracer.c" "${GBB_MODEL_GATE_TRACER_SOURCE}")
file(WRITE "${GBB_MODEL_GATE_DIR}/tracer.md" "${GBB_MODEL_GATE_TRACER_DOC}")
file(WRITE "${GBB_MODEL_GATE_DIR}/tracer-bad.md" "${GBB_MODEL_GATE_TRACER_DOC_BAD}")

gbb_add_model_gate_test(model_gates_tracer_pass 0 "model-gates pass functions=2"
  --source "${GBB_MODEL_GATE_DIR}/tracer.c" --doc "${GBB_MODEL_GATE_DIR}/tracer.md")
gbb_add_model_gate_test(model_gates_tracer_doc_mismatch 1 "gate-doc-mismatch"
  --source "${GBB_MODEL_GATE_DIR}/tracer.c" --doc "${GBB_MODEL_GATE_DIR}/tracer-bad.md")
# The real core and the real gate table (Plan 10-02): every function and model-differing branch is tagged.
gbb_add_model_gate_test(model_gates 0 "model-gates pass functions=1[2-9][0-9] gates=")
gbb_add_model_gate_test(model_gates_selftest 0
  "model-gates self-test pass mutants=[1-9][0-9]* functions=1[2-9][0-9]" --self-test)

# Real-file negative controls (Plan 10-02). Each mutant is a configure-time copy of the real source or
# doc under build/model-gates/real, with its anchor asserted to occur exactly once (forward and
# REVERSE) so a drifted anchor fails the configure instead of building an unmutated "mutant".
set(GBB_MODEL_GATE_REAL_DIR "${GBB_MODEL_GATE_DIR}/real")
set(GBB_MODEL_GATE_REAL_SOURCE "${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c")
set(GBB_MODEL_GATE_REAL_DOC "${PROJECT_SOURCE_DIR}/docs/model-gates.md")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
  "${GBB_MODEL_GATE_REAL_SOURCE}" "${GBB_MODEL_GATE_REAL_DOC}")
file(MAKE_DIRECTORY "${GBB_MODEL_GATE_REAL_DIR}")
file(READ "${GBB_MODEL_GATE_REAL_SOURCE}" gbb_mg_source)
file(READ "${GBB_MODEL_GATE_REAL_DOC}" gbb_mg_doc)

# (a) The STOP gate tag deleted. The gate number is not part of the anchor so later plans may renumber.
set(GBB_MG_STOP_TAG_REGEX
  "[ ]*/\\* MODEL: UNKNOWN GATE-[0-9][0-9] research:12 -- STOP, including CGB speed switch \\*/\n")
string(REGEX MATCHALL "${GBB_MG_STOP_TAG_REGEX}" gbb_mg_stop_matches "${gbb_mg_source}")
list(LENGTH gbb_mg_stop_matches gbb_mg_stop_count)
if(NOT gbb_mg_stop_count EQUAL 1)
  message(FATAL_ERROR "model-gate mutant: the STOP gate tag must occur exactly once in "
    "${GBB_MODEL_GATE_REAL_SOURCE} (found ${gbb_mg_stop_count})")
endif()
string(REGEX REPLACE "${GBB_MG_STOP_TAG_REGEX}" "" gbb_mg_deleted "${gbb_mg_source}")
file(WRITE "${GBB_MODEL_GATE_REAL_DIR}/deleted-tag.c" "${gbb_mg_deleted}")

# (b) One untagged definition appended to the real source.
file(WRITE "${GBB_MODEL_GATE_REAL_DIR}/untagged-function.c"
  "${gbb_mg_source}\nstatic int gbb_model_gate_probe(void) { return 0; }\n")

# (c) The read8 bus-conflict row claims research:14 instead of the declared expected failure.
set(GBB_MG_ROW_ANCHOR "expected-failure:cgb-separate-buses | read8 |")
string(FIND "${gbb_mg_doc}" "${GBB_MG_ROW_ANCHOR}" gbb_mg_row_first)
string(FIND "${gbb_mg_doc}" "${GBB_MG_ROW_ANCHOR}" gbb_mg_row_last REVERSE)
if(gbb_mg_row_first EQUAL -1 OR NOT gbb_mg_row_first EQUAL gbb_mg_row_last)
  message(FATAL_ERROR "model-gate mutant: '${GBB_MG_ROW_ANCHOR}' must occur exactly once in "
    "${GBB_MODEL_GATE_REAL_DOC} (first=${gbb_mg_row_first} last=${gbb_mg_row_last})")
endif()
string(REPLACE "${GBB_MG_ROW_ANCHOR}" "research:14 | read8 |" gbb_mg_doc_bad "${gbb_mg_doc}")
file(WRITE "${GBB_MODEL_GATE_REAL_DIR}/doc-mismatch.md" "${gbb_mg_doc_bad}")

# A deleted branch tag leaves its doc row without a code tag, so R2 (gate-doc-mismatch) fires first.
gbb_add_model_gate_test(model_gates_real_deleted_tag 1 "gate-doc-mismatch: doc GATE-[0-9][0-9] has no code tag"
  --source "${GBB_MODEL_GATE_REAL_DIR}/deleted-tag.c" --doc "${GBB_MODEL_GATE_REAL_DOC}")
gbb_add_model_gate_test(model_gates_real_untagged_function 1 "gate-untagged-function: gbb_model_gate_probe"
  --source "${GBB_MODEL_GATE_REAL_DIR}/untagged-function.c" --doc "${GBB_MODEL_GATE_REAL_DOC}")
gbb_add_model_gate_test(model_gates_real_doc_mismatch 1 "gate-doc-mismatch"
  --source "${GBB_MODEL_GATE_REAL_SOURCE}" --doc "${GBB_MODEL_GATE_REAL_DIR}/doc-mismatch.md")
# Release mode records that research: items stay open until Phase 14; it becomes a pass gate in Phase 15.
gbb_add_model_gate_test(model_gates_release_blocked 1 "gate-unresolved-unknown"
  --release --source "${GBB_MODEL_GATE_REAL_SOURCE}" --doc "${GBB_MODEL_GATE_REAL_DOC}")

# Post-boot table mirror (D-06): docs/cgb-profile.md must equal post_boot[] and obey the provenance
# rules. White-box like test_mbc5_internal, so it includes the core and must not link it.
add_executable(test_cgb_tables test_cgb_tables.c)
target_include_directories(test_cgb_tables PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_cgb_tables PRIVATE c_std_17)
set_target_properties(test_cgb_tables PROPERTIES C_EXTENSIONS OFF)
set(GBB_CGB_PROFILE_DOC "${PROJECT_SOURCE_DIR}/docs/cgb-profile.md")
add_test(NAME cgb_tables_postboot COMMAND test_cgb_tables postboot "${GBB_CGB_PROFILE_DOC}")
set_tests_properties(cgb_tables_postboot PROPERTIES
  PASS_REGULAR_EXPRESSION "cgb-tables postboot pass rows=[1-9]")
add_test(NAME cgb_tables_postboot_selftest COMMAND test_cgb_tables postboot_selftest "${GBB_CGB_PROFILE_DOC}")
set_tests_properties(cgb_tables_postboot_selftest PROPERTIES
  PASS_REGULAR_EXPRESSION "cgb-tables self-test pass mutants=6")

# Negative control: the real doc with the compat A value changed from $11 to $12 must be rejected.
file(READ "${GBB_CGB_PROFILE_DOC}" gbb_cgb_doc)
set(GBB_CGB_ROW_ANCHOR "| a | COMPAT | $11 |")
string(FIND "${gbb_cgb_doc}" "${GBB_CGB_ROW_ANCHOR}" gbb_cgb_anchor_at)
string(FIND "${gbb_cgb_doc}" "${GBB_CGB_ROW_ANCHOR}" gbb_cgb_anchor_last REVERSE)
if(gbb_cgb_anchor_at EQUAL -1 OR NOT gbb_cgb_anchor_at EQUAL gbb_cgb_anchor_last)
  message(FATAL_ERROR "cgb-tables mutation anchor '${GBB_CGB_ROW_ANCHOR}' must occur exactly once in docs/cgb-profile.md")
endif()
string(REPLACE "${GBB_CGB_ROW_ANCHOR}" "| a | COMPAT | $12 |" gbb_cgb_doc_bad "${gbb_cgb_doc}")
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/cgb-tables")
file(WRITE "${PROJECT_BINARY_DIR}/cgb-tables/mutated-postboot.md" "${gbb_cgb_doc_bad}")
add_test(NAME cgb_tables_postboot_mutated_doc
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_tables>;postboot;${PROJECT_BINARY_DIR}/cgb-tables/mutated-postboot.md"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=cgb-tables mismatch"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

# Register visibility mirror (Plan 10-10, D-06): io_visibility[] against the cgb-io-visibility block.
add_test(NAME cgb_tables_io COMMAND test_cgb_tables io "${GBB_CGB_PROFILE_DOC}")
set_tests_properties(cgb_tables_io PROPERTIES
  PASS_REGULAR_EXPRESSION "cgb-tables io pass rows=[1-9]"
  FAIL_REGULAR_EXPRESSION "cgb-tables mismatch")

# Negative control: the compat FF4F read value changed to $FF in the doc must be rejected.
set(GBB_CGB_IO_ANCHOR "| $FF4F | COMPAT | $FE or bank |")
string(FIND "${gbb_cgb_doc}" "${GBB_CGB_IO_ANCHOR}" gbb_cgb_io_at)
string(FIND "${gbb_cgb_doc}" "${GBB_CGB_IO_ANCHOR}" gbb_cgb_io_last REVERSE)
if(gbb_cgb_io_at EQUAL -1 OR NOT gbb_cgb_io_at EQUAL gbb_cgb_io_last)
  message(FATAL_ERROR "cgb-tables io mutation anchor '${GBB_CGB_IO_ANCHOR}' must occur exactly once in docs/cgb-profile.md")
endif()
string(REPLACE "${GBB_CGB_IO_ANCHOR}" "| $FF4F | COMPAT | $FF |" gbb_cgb_io_doc_bad "${gbb_cgb_doc}")
file(WRITE "${PROJECT_BINARY_DIR}/cgb-tables/mutated-io.md" "${gbb_cgb_io_doc_bad}")
add_test(NAME cgb_tables_io_mutated_doc
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_tables>;io;${PROJECT_BINARY_DIR}/cgb-tables/mutated-io.md"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=cgb-tables mismatch"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

# D-22 advisory A/B benchmark harness (Plan 10-17). Only the digest check and the receipt shape are
# asserted; timing is never a CTest result. bash-only, so absent on Windows.
if(NOT WIN32)
  find_program(GBB_BASH bash REQUIRED)
  set(GBB_AB_SCRIPT "${PROJECT_SOURCE_DIR}/tests/scripts/measure-release-baseline.sh")
  set(GBB_AB_DIR "${PROJECT_BINARY_DIR}/bench-ab")
  file(MAKE_DIRECTORY "${GBB_AB_DIR}")
  add_test(NAME cgb_bench_ab_selftest
    COMMAND "${GBB_BASH}" "${GBB_AB_SCRIPT}" --ab $<TARGET_FILE:measure_core> $<TARGET_FILE:measure_core>
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
  set_tests_properties(cgb_bench_ab_selftest PROPERTIES TIMEOUT 120
    ENVIRONMENT "GBB_RELEASE_MEASURE_SAMPLES=3;GBB_RELEASE_MEASURE_WARMUPS=1;GBB_AB_RECEIPT=${GBB_AB_DIR}/selftest-receipt.json"
    PASS_REGULAR_EXPRESSION "ab pass samples=3")

  # Negative controls: a wrong expected digest and a receipt missing one field must each fail
  # with exactly exit code 1 and their named reason.
  function(gbb_add_bench_ab_control name drop_field digest regex)
    add_test(NAME ${name}
      COMMAND ${CMAKE_COMMAND}
        "-DGBB_CMD=${GBB_BASH}$<SEMICOLON>${GBB_AB_SCRIPT}$<SEMICOLON>--ab$<SEMICOLON>$<TARGET_FILE:measure_core>$<SEMICOLON>$<TARGET_FILE:measure_core>"
        -DGBB_EXPECT_CODE=1
        "-DGBB_EXPECT_REGEX=${regex}"
        "-DGBB_WORKDIR=${PROJECT_SOURCE_DIR}"
        -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
    set_tests_properties(${name} PROPERTIES TIMEOUT 120
      ENVIRONMENT "GBB_RELEASE_MEASURE_SAMPLES=3;GBB_RELEASE_MEASURE_WARMUPS=1;GBB_AB_RECEIPT=${GBB_AB_DIR}/${name}.json;GBB_AB_DROP_FIELD=${drop_field};GBB_AB_EXPECT_DIGEST=${digest}")
  endfunction()
  gbb_add_bench_ab_control(cgb_bench_ab_wrong_digest "" 0000000000000000 "ab-digest-mismatch")
  gbb_add_bench_ab_control(cgb_bench_ab_missing_field uncertainty 4c7a57ff3d50d228
    "ab-receipt-missing: uncertainty")
endif()

gabbaboy_verify_registered_tests()
