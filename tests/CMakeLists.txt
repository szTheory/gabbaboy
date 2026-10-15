set(GBB_TEST_INSTALL_PREFIX "" CACHE STRING "Relocated install prefix used by installed-package smoke tests")
# PATH cache entries are normalized against CMake's process cwd before project code sees them.
set_property(CACHE GBB_TEST_INSTALL_PREFIX PROPERTY TYPE STRING)
# Resolve relative prefixes against the build tree before optional tests are filtered and
# ExpectedTests.cmake compares the complete registered inventory.
if(GBB_TEST_INSTALL_PREFIX)
  set(GBB_TEST_INSTALL_PREFIX_INPUT "${GBB_TEST_INSTALL_PREFIX}")
  get_filename_component(GBB_TEST_INSTALL_PREFIX_ABSOLUTE
    "${GBB_TEST_INSTALL_PREFIX_INPUT}" ABSOLUTE BASE_DIR "${CMAKE_BINARY_DIR}")
  set(GBB_TEST_INSTALL_PREFIX "${GBB_TEST_INSTALL_PREFIX_ABSOLUTE}")
endif()
include(${PROJECT_SOURCE_DIR}/cmake/ExpectedTests.cmake)
# Internal core test-seam header (src/core/gabbaboy_test.h). Directory-scoped so the mutant copies of
# gabbaboy.c, which are compiled from the build tree, resolve the same include as the real core.
include_directories("${PROJECT_SOURCE_DIR}/src/core")

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
foreach(case vbk_tracer svbk_select unmapped_cgb boundaries deferred_stop ie_gate
     matrix_compat flip_control matrix_cgb matrix_dmg cross_column_control sweep_control)
  add_test(NAME cgb_visibility_${case} COMMAND test_cgb_visibility ${case})
endforeach()
foreach(case ir_tracer ir_controls ir_modes ir_interrupt_continuation)
  add_test(NAME cgb_${case} COMMAND test_cgb_visibility ${case})
endforeach()
add_test(NAME cgb_hdma_visibility COMMAND test_cgb_visibility hdma_visibility)
add_test(NAME cgb_hdma_visibility_controls COMMAND test_cgb_visibility hdma_visibility_controls)
# Plan 10-11: STOP/KEY1 fail-closed and the KEY0 lock keep their plan-named CTests.
foreach(case stop_armed_cgb stop_unarmed_cgb stop_compat_ignores_key1 stop_dmg_control
     key0_lock_cgb key0_lock_compat key0_lock_cross_column key0_lock_reset_idempotent)
  add_test(NAME cgb_${case} COMMAND test_cgb_visibility ${case})
endforeach()

# Phase 13 plan 13-01: private real-transfer seam tracer. This source includes
# the core to place a deterministic PPU collision inside guest instructions.
include(${PROJECT_SOURCE_DIR}/cmake/P13Mutants.cmake)
set(GBB_P13_MUTANT_CORE ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_p13_mutants.c)
gbb_p13_make_mutant_core(${GBB_P13_MUTANT_CORE})
add_library(gabbaboy_core_p13_mutants STATIC ${GBB_P13_MUTANT_CORE})
target_include_directories(gabbaboy_core_p13_mutants PUBLIC "${PROJECT_SOURCE_DIR}/include")
target_compile_features(gabbaboy_core_p13_mutants PUBLIC c_std_17)
target_compile_definitions(gabbaboy_core_p13_mutants PRIVATE
  GBB_BUILD_REVISION="p13-mutants" GBB_BUILD_QUALIFIED=0)
set_target_properties(gabbaboy_core_p13_mutants PROPERTIES C_EXTENSIONS OFF)

add_executable(test_cgb_hdma_internal test_cgb_hdma_internal.c fuzz_core.c)
target_include_directories(test_cgb_hdma_internal PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_cgb_hdma_internal PRIVATE c_std_17)
target_compile_definitions(test_cgb_hdma_internal PRIVATE
  GBB_FUZZ_STANDALONE_TEST=1 GBB_P12_MUTANT_BUILD=1
  "GBB_P12_CORE_SOURCE=\"${GBB_P13_MUTANT_CORE}\""
  GBB_BUILD_REVISION="p13-mutants" GBB_BUILD_QUALIFIED=0)
set_target_properties(test_cgb_hdma_internal PROPERTIES C_EXTENSIONS OFF)
foreach(case ld_sp cb controls partition outputs)
  add_test(NAME cgb_hdma_tracer_${case} COMMAND test_cgb_hdma_internal ${case})
endforeach()
foreach(case state_matrix trigger_matrix trigger_controls timing_policy address_matrix overflow_policy
             lifecycle resource_bounds hostile_seeds)
  add_test(NAME cgb_hdma_${case} COMMAND test_cgb_hdma_internal ${case})
endforeach()
add_test(NAME cgb_hdma_timing_sensitivity COMMAND test_cgb_hdma_internal timing_sensitivity)
foreach(case lifecycle resource_bounds hostile_seeds)
  add_test(NAME cgb_hdma_${case}_controls
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=$<TARGET_FILE:test_cgb_hdma_internal>;${case}_controls"
      -DGBB_EXPECT_CODE=1
      -DGBB_EXPECT_REGEX=hdma-${case}-control-detected
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
endforeach()
add_test(NAME cgb_hdma_state_matrix_controls
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_hdma_internal>;state_matrix;--flip-cancel"
    -DGBB_EXPECT_CODE=1
    -DGBB_EXPECT_REGEX=guest\ cancel\ readback\ expected=80\ actual=81
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
add_test(NAME cgb_hdma_timing_policy_controls
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_hdma_internal>;timing_flip"
    -DGBB_EXPECT_CODE=1
    -DGBB_EXPECT_REGEX=timing\ policy:\ byte\ 0\ committed\ early
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
add_test(NAME cgb_hdma_trigger_matrix_controls
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_hdma_internal>;trigger_flip"
    -DGBB_EXPECT_CODE=1
    -DGBB_EXPECT_REGEX=trigger\ matrix:\ injected\ repeated-mode\ event\ detected
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
add_test(NAME cgb_hdma_address_matrix_controls
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_hdma_internal>;address_flip"
    -DGBB_EXPECT_CODE=1
    -DGBB_EXPECT_REGEX=address\ matrix:\ invalid-block\ byte\ mutated
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
add_test(NAME cgb_hdma_overflow_policy_controls
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_hdma_internal>;overflow_flip"
    -DGBB_EXPECT_CODE=1
    -DGBB_EXPECT_REGEX=overflow\ policy:\ cursor\ wrapped
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

# Public-API guest wake/steal cases use original inline CGB ROMs and the installed core API.
add_executable(test_cgb_hdma test_cgb_hdma.c)
target_link_libraries(test_cgb_hdma PRIVATE gabbaboy_core_p13_mutants)
target_compile_features(test_cgb_hdma PRIVATE c_std_17)
target_compile_definitions(test_cgb_hdma PRIVATE GBB_P12_MUTANT_BUILD=1)
set_target_properties(test_cgb_hdma PROPERTIES
  C_EXTENSIONS OFF RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}")
add_test(NAME cgb_hdma_guest_halt COMMAND test_cgb_hdma guest_halt)
add_test(NAME cgb_hdma_guest_steal COMMAND test_cgb_hdma guest_steal)
add_test(NAME cgb_hdma_guest_controls COMMAND test_cgb_hdma guest_controls)
add_test(NAME cgb_hdma_guest_banks COMMAND test_cgb_hdma guest_banks)
# Plan 13-08 Task 1: the public API must execute the original CPU-programmed
# HBlank DMA guest and verify its own marker and source-derived RGB555 frame.
add_test(NAME cgb_hdma_original_fixture COMMAND test_cgb_hdma --fixture
  ${PROJECT_SOURCE_DIR}/fixtures/cgb-hdma/hblank.gb --check-controls)

# Reuses the explicit private-state hash from the speed-switch partition tests.
add_executable(test_cgb_hdma_partition test_cgb_hdma_partition.c)
target_include_directories(test_cgb_hdma_partition PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_cgb_hdma_partition PRIVATE c_std_17)
target_compile_definitions(test_cgb_hdma_partition PRIVATE
  GBB_P12_MUTANT_BUILD=1
  "GBB_P12_CORE_SOURCE=\"${GBB_P13_MUTANT_CORE}\""
  GBB_BUILD_REVISION="p13-mutants" GBB_BUILD_QUALIFIED=0)
set_target_properties(test_cgb_hdma_partition PROPERTIES C_EXTENSIONS OFF)
add_test(NAME cgb_hdma_partition_midbyte COMMAND test_cgb_hdma_partition midbyte)
add_test(NAME cgb_hdma_partition_windows COMMAND test_cgb_hdma_partition windows)
add_test(NAME cgb_hdma_partition_multicut COMMAND test_cgb_hdma_partition multicut)
add_test(NAME cgb_hdma_partition_outputs COMMAND test_cgb_hdma_partition outputs)
add_test(NAME cgb_hdma_partition_lost_remainder_control
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_hdma_partition>;lost_remainder_control"
    -DGBB_EXPECT_CODE=1
    -DGBB_EXPECT_REGEX=hdma-partition-control-detected
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
add_test(NAME cgb_hdma_partition_order_control
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_hdma_partition>;order_control"
    -DGBB_EXPECT_CODE=1
    -DGBB_EXPECT_REGEX=hdma-partition-control-detected
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)


# Plan 13-03 reserves Task 2's exact tests before that harness expands.
foreach(case competing_stalls stop_policy oam_order)
  add_test(NAME cgb_hdma_${case} COMMAND test_cgb_hdma_internal ${case})
  add_test(NAME cgb_hdma_${case}_controls COMMAND test_cgb_hdma_internal ${case}_controls)
endforeach()

# Preserve the Phase 13-03 compatibility names while routing both through the
# single shared runtime-mask core introduced by this plan.
math(EXPR GBB_P13_NO_STEAL_MASK "1 << 40" OUTPUT_FORMAT HEXADECIMAL)
add_test(NAME cgb_hdma_guest_steal_no_steal_mutant
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_hdma>;guest_steal;--mutants;${GBB_P13_NO_STEAL_MASK}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=guest steal: CPU timing predicate"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
add_test(NAME cgb_hdma_guest_steal_no_steal_control
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_hdma>;guest_steal_data;--mutants;0"
    -DGBB_EXPECT_CODE=0
    -DGBB_EXPECT_REGEX=.*
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

# Reserve every narrow Phase 13 source mutation and mask-zero twin here so the
# inventory has one owner before the case predicates arrive in plan 13-05 Task 2.
gbb_p13_mutant_test(test_cgb_hdma no_steal 40 guest_steal "guest steal: CPU timing predicate")
gbb_p13_mutant_test(test_cgb_hdma_internal no_copy 41 mutant_no_copy "hdma mutant no_copy detected")
gbb_p13_mutant_test(test_cgb_hdma_internal duplicate_copy 42 mutant_duplicate_copy "hdma mutant duplicate_copy detected")
gbb_p13_mutant_test(test_cgb_hdma_internal wrong_vbk 43 mutant_wrong_vbk "hdma mutant wrong_vbk detected")
gbb_p13_mutant_test(test_cgb_hdma_internal unmasked_address 44 mutant_unmasked_address "hdma mutant unmasked_address detected")
gbb_p13_mutant_test(test_cgb_hdma_internal wrong_count 45 mutant_wrong_count "hdma mutant wrong_count detected")
gbb_p13_mutant_test(test_cgb_hdma_internal wrong_cancel 46 mutant_wrong_cancel "hdma mutant wrong_cancel detected")
gbb_p13_mutant_test(test_cgb_hdma_internal speed_scaled 47 timing_policy "timing policy: byte")
gbb_p13_mutant_test(test_cgb_hdma_internal halt_admission 48 mutant_halt_admission "hdma mutant halt_admission detected")
gbb_p13_mutant_test(test_cgb_hdma_internal false_trigger 49 mutant_false_trigger "hdma mutant false_trigger detected")
gbb_p13_mutant_test(test_cgb_hdma_internal lost_dma_irq 50 mutant_lost_dma_irq "hdma mutant lost_dma_irq detected")
gbb_p13_mutant_test(test_cgb_hdma_internal dma_realign 51 mutant_dma_realign "hdma mutant dma_realign detected")
gbb_p13_mutant_test(test_cgb_hdma_internal shifted_order 52 mutant_shifted_order "hdma mutant shifted_order detected")
gbb_p13_mutant_test(test_cgb_hdma_partition lost_phase 53 mutant_lost_phase "hdma mutant lost_phase detected")
add_test(NAME cgb_hdma_mutant_anchor_guard
  COMMAND ${CMAKE_COMMAND} -DGBB_P13_SCRIPT_ANCHOR_GUARD=1
    "-DGBB_P13_GUARD_DIR=${CMAKE_CURRENT_BINARY_DIR}"
    -P ${PROJECT_SOURCE_DIR}/cmake/P13Mutants.cmake)

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

# Phase 14 plans 14-01/14-03: CGB guests sample digital PCM and CH3 fetch state through the timed bus path.
add_executable(test_cgb_apu test_cgb_apu.c)
target_link_libraries(test_cgb_apu PRIVATE GabbaBoy::core)
target_compile_features(test_cgb_apu PRIVATE c_std_17)
set_target_properties(test_cgb_apu PROPERTIES C_EXTENSIONS OFF)
add_test(NAME cgb_apu_wave_latch COMMAND test_cgb_apu cgb_apu_wave_latch)
add_test(NAME cgb_apu_wave_fetch COMMAND test_cgb_apu cgb_apu_wave_fetch)
add_test(NAME cgb_apu_power COMMAND test_cgb_apu cgb_apu_power)
add_test(NAME cgb_apu_off_writes COMMAND test_cgb_apu cgb_apu_off_writes)
add_test(NAME cgb_apu_wave_access COMMAND test_cgb_apu cgb_apu_wave_access)
add_test(NAME cgb_apu_div_stop COMMAND test_cgb_apu cgb_apu_div_stop)
add_test(NAME cgb_apu_transition_controls COMMAND test_cgb_apu cgb_apu_transition_controls)
add_test(NAME cgb_apu_trigger_length_sweep COMMAND test_cgb_apu cgb_apu_trigger_length_sweep)
add_test(NAME cgb_apu_output_pressure COMMAND test_cgb_apu cgb_apu_output_pressure)
add_test(NAME cgb_pcm_tracer COMMAND test_cgb_apu cgb_pcm_tracer)
foreach(case channels power_dac readonly host_invariance controls)
  add_test(NAME cgb_pcm_${case} COMMAND test_cgb_apu cgb_pcm_${case})
endforeach()

# Phase 14 plan 14-04: deterministic bounded hostile APU inputs use the same offline fuzz adapter.
add_executable(test_cgb_apu_hostile test_cgb_apu.c fuzz_core.c)
target_link_libraries(test_cgb_apu_hostile PRIVATE GabbaBoy::core)
target_compile_features(test_cgb_apu_hostile PRIVATE c_std_17)
target_compile_definitions(test_cgb_apu_hostile PRIVATE
  GBB_FUZZ_STANDALONE_TEST=1 GBB_CGB_APU_HOSTILE_TEST=1)
set_target_properties(test_cgb_apu_hostile PROPERTIES C_EXTENSIONS OFF)
add_test(NAME cgb_apu_hostile_seeds
  COMMAND test_cgb_apu_hostile cgb_apu_hostile_seeds)

# Compile-time-only mutant core: production instances have no runtime mutation selector or state.
add_library(gabbaboy_core_cgb_pcm_nibble_mutant STATIC ${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c)
target_include_directories(gabbaboy_core_cgb_pcm_nibble_mutant PUBLIC "${PROJECT_SOURCE_DIR}/include")
target_compile_features(gabbaboy_core_cgb_pcm_nibble_mutant PRIVATE c_std_17)
target_compile_definitions(gabbaboy_core_cgb_pcm_nibble_mutant PRIVATE GBB_TEST_CGB_PCM_SWAP_NIBBLES=1)
set_target_properties(gabbaboy_core_cgb_pcm_nibble_mutant PROPERTIES C_EXTENSIONS OFF)
add_executable(test_cgb_apu_nibble_mutant test_cgb_apu.c)
target_link_libraries(test_cgb_apu_nibble_mutant PRIVATE gabbaboy_core_cgb_pcm_nibble_mutant)
target_compile_features(test_cgb_apu_nibble_mutant PRIVATE c_std_17)
target_compile_definitions(test_cgb_apu_nibble_mutant PRIVATE GBB_CGB_APU_CONTROL_MUTANT=1)
set_target_properties(test_cgb_apu_nibble_mutant PROPERTIES C_EXTENSIONS OFF)
add_test(NAME cgb_pcm_tracer_control COMMAND test_cgb_apu_nibble_mutant cgb_pcm_tracer_control)

# Negative controls are separate compile-time cores: no production runtime selector or API.
foreach(kind routing writable)
  add_library(gabbaboy_core_cgb_pcm_${kind}_mutant STATIC ${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c)
  target_include_directories(gabbaboy_core_cgb_pcm_${kind}_mutant PUBLIC "${PROJECT_SOURCE_DIR}/include")
  target_compile_features(gabbaboy_core_cgb_pcm_${kind}_mutant PRIVATE c_std_17)
  set_target_properties(gabbaboy_core_cgb_pcm_${kind}_mutant PROPERTIES C_EXTENSIONS OFF)
  add_executable(test_cgb_apu_${kind}_mutant test_cgb_apu.c)
  target_link_libraries(test_cgb_apu_${kind}_mutant PRIVATE gabbaboy_core_cgb_pcm_${kind}_mutant)
  target_compile_features(test_cgb_apu_${kind}_mutant PRIVATE c_std_17)
  set_target_properties(test_cgb_apu_${kind}_mutant PROPERTIES C_EXTENSIONS OFF)
endforeach()
target_compile_definitions(gabbaboy_core_cgb_pcm_routing_mutant PRIVATE GBB_TEST_CGB_PCM_ROUTING_COUPLED=1)
target_compile_definitions(test_cgb_apu_routing_mutant PRIVATE GBB_CGB_APU_CONTROL_MUTANT=2)
add_test(NAME cgb_pcm_routing_control COMMAND test_cgb_apu_routing_mutant cgb_pcm_controls)
target_compile_definitions(gabbaboy_core_cgb_pcm_writable_mutant PRIVATE GBB_TEST_CGB_PCM_WRITABLE=1)
target_compile_definitions(test_cgb_apu_writable_mutant PRIVATE GBB_CGB_APU_CONTROL_MUTANT=3)
add_test(NAME cgb_pcm_writable_control COMMAND test_cgb_apu_writable_mutant cgb_pcm_controls)

add_library(gabbaboy_core_cgb_apu_direct_ram_mutant STATIC ${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c)
target_include_directories(gabbaboy_core_cgb_apu_direct_ram_mutant PUBLIC "${PROJECT_SOURCE_DIR}/include")
target_compile_features(gabbaboy_core_cgb_apu_direct_ram_mutant PRIVATE c_std_17)
target_compile_definitions(gabbaboy_core_cgb_apu_direct_ram_mutant PRIVATE GBB_TEST_CGB_APU_DIRECT_RAM=1)
set_target_properties(gabbaboy_core_cgb_apu_direct_ram_mutant PROPERTIES C_EXTENSIONS OFF)
add_executable(test_cgb_apu_direct_ram_mutant test_cgb_apu.c)
target_link_libraries(test_cgb_apu_direct_ram_mutant PRIVATE gabbaboy_core_cgb_apu_direct_ram_mutant)
target_compile_features(test_cgb_apu_direct_ram_mutant PRIVATE c_std_17)
target_compile_definitions(test_cgb_apu_direct_ram_mutant PRIVATE GBB_CGB_APU_CONTROL_MUTANT=4)
set_target_properties(test_cgb_apu_direct_ram_mutant PROPERTIES C_EXTENSIONS OFF)
add_test(NAME cgb_apu_wave_direct_ram_control COMMAND test_cgb_apu_direct_ram_mutant cgb_apu_wave_direct_ram_control)

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
add_test(NAME cgb_fuzz_profile_select COMMAND test_fuzz_core cgb_profile_select)
add_test(NAME cgb_fuzz_palette_regressions COMMAND test_fuzz_core cgb_palette)
add_test(NAME cgb_fuzz_speed_regressions COMMAND test_fuzz_core cgb_speed)
set_tests_properties(cgb_fuzz_speed_regressions PROPERTIES TIMEOUT 60)

# Invert only the speed harness's guest KEY1 consistency oracle. The speed seed must make it fail,
# while an existing CGB seed that never selects cgb_speed stays quiet in the same executable.
add_executable(test_fuzz_core_speed_oracle_mutant test_fuzz_core.c fuzz_core.c)
target_link_libraries(test_fuzz_core_speed_oracle_mutant PRIVATE GabbaBoy::core)
target_compile_features(test_fuzz_core_speed_oracle_mutant PRIVATE c_std_17)
target_compile_definitions(test_fuzz_core_speed_oracle_mutant PRIVATE
  GBB_FUZZ_STANDALONE_TEST=1 GBB_FUZZ_SPEED_ORACLE_INVERTED=1)
set_target_properties(test_fuzz_core_speed_oracle_mutant PROPERTIES C_EXTENSIONS OFF)
add_test(NAME cgb_fuzz_speed_oracle_mutant
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_fuzz_core_speed_oracle_mutant>;cgb_speed"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=KEY1 consistency oracle inverted"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
add_test(NAME cgb_fuzz_speed_oracle_mutant_control
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_fuzz_core_speed_oracle_mutant>;cgb"
    -DGBB_EXPECT_CODE=0
    "-DGBB_EXPECT_REGEX=.*"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(cgb_fuzz_speed_oracle_mutant PROPERTIES ENVIRONMENT "ASAN_OPTIONS=detect_leaks=0")

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
target_link_libraries(test_magentests PRIVATE gabbaboy_accept)
target_compile_features(test_magentests PRIVATE c_std_17)
set_target_properties(test_magentests PROPERTIES C_EXTENSIONS OFF)
add_test(NAME magentests_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DMANIFEST=${GBB_MAGENTESTS_DIR}/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixtureManifest.cmake)
add_test(NAME magentests_manifest_self_check
  COMMAND bash ${PROJECT_SOURCE_DIR}/tests/scripts/reproduce-magentests.sh --self-check)
add_test(NAME magentests_repro_self_test
  COMMAND bash ${PROJECT_SOURCE_DIR}/tests/scripts/reproduce-magentests.sh --self-test)
add_test(NAME magentests_oob_sram_mbc3
  COMMAND test_magentests magentests_oob_sram_mbc3 ${GBB_MAGENTESTS_DIR}/mbc_oob_sram_mbc3.gbc)
add_test(NAME magentests_oob_sram_mbc1
  COMMAND test_magentests magentests_oob_sram_mbc1 ${GBB_MAGENTESTS_DIR}/mbc_oob_sram_mbc1.gbc)
add_test(NAME magentests_oob_sram_mbc5
  COMMAND test_magentests magentests_oob_sram_mbc5 ${GBB_MAGENTESTS_DIR}/mbc_oob_sram_mbc5.gbc)
add_test(NAME magentests_cgb_ppu_disabled_state
  COMMAND test_magentests magentests_cgb_ppu_disabled_state ${GBB_MAGENTESTS_DIR}/ppu_disabled_state.gbc)
add_test(NAME magentests_cgb_ppu_disabled_state_compat
  COMMAND test_magentests magentests_cgb_ppu_disabled_state_compat ${GBB_MAGENTESTS_DIR}/ppu_disabled_state.gbc)
add_test(NAME magentests_cgb_oam_internal_priority
  COMMAND test_magentests magentests_cgb_oam_internal_priority ${GBB_MAGENTESTS_DIR}/oam_internal_priority.gbc)
add_test(NAME magentests_cgb_bg_oam_priority
  COMMAND test_magentests magentests_cgb_bg_oam_priority ${GBB_MAGENTESTS_DIR}/bg_oam_priority.gbc)
add_test(NAME magentests_oob_sram_negative_control
  COMMAND test_magentests magentests_oob_sram_negative_control
    ${GBB_MAGENTESTS_DIR}/mbc_oob_sram_mbc1.gbc
    ${GBB_MAGENTESTS_DIR}/mbc_oob_sram_mbc3.gbc
    ${GBB_MAGENTESTS_DIR}/mbc_oob_sram_mbc5.gbc)
# Phase 13 D-17/D-19/D-21/D-22: source-derived Magen HDMA guest evidence and
# runtime-mask controls. This in-tree target includes the P13 mutant core TU;
# no test core behavior or public API changes are required.
add_executable(test_magentests_hdma test_magentests.c
  ${PROJECT_SOURCE_DIR}/src/accept/sha256.c
  ${PROJECT_SOURCE_DIR}/src/accept/digest.c)
target_include_directories(test_magentests_hdma PRIVATE
  "${PROJECT_SOURCE_DIR}/include" "${PROJECT_SOURCE_DIR}/src/accept")
target_compile_features(test_magentests_hdma PRIVATE c_std_17)
target_compile_definitions(test_magentests_hdma PRIVATE
  GBB_P12_MUTANT_BUILD=1
  "GBB_P13_CORE_SOURCE=\"${GBB_P13_MUTANT_CORE}\""
  GBB_BUILD_REVISION="p13-mutants" GBB_BUILD_QUALIFIED=0)
set_target_properties(test_magentests_hdma PROPERTIES C_EXTENSIONS OFF)
add_test(NAME magentests_hblank_vram_dma
  COMMAND test_magentests_hdma magentests_hblank_vram_dma
    ${GBB_MAGENTESTS_DIR}/hblank_vram_dma.gbc)
add_test(NAME cgb_hdma_magen_controls
  COMMAND test_magentests_hdma cgb_hdma_magen_controls
    ${GBB_MAGENTESTS_DIR}/hblank_vram_dma.gbc)
set_tests_properties(magentests_hblank_vram_dma cgb_hdma_magen_controls PROPERTIES TIMEOUT 60)

# Phase 13 plan 13-09: run the exact admitted SameSuite DMA ROMs on the selected
# CGB-CPU-E software model, with byte/status predicates and bounded test seams.
add_executable(test_samesuite_hdma test_samesuite_hdma.c)
target_include_directories(test_samesuite_hdma PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_samesuite_hdma PRIVATE c_std_17)
target_compile_definitions(test_samesuite_hdma PRIVATE
  "GBB_P13_CORE_SOURCE=\"${GBB_P13_MUTANT_CORE}\""
  GBB_BUILD_REVISION="p13-mutants" GBB_BUILD_QUALIFIED=0)
set_target_properties(test_samesuite_hdma PROPERTIES C_EXTENSIONS OFF)
set(GBB_SAMESUITE_DIR "${PROJECT_SOURCE_DIR}/fixtures/samesuite")
add_test(NAME samesuite_hdma_gbc_dma_cont
  COMMAND test_samesuite_hdma gbc_dma_cont "${GBB_SAMESUITE_DIR}/gbc_dma_cont.gb")
add_test(NAME samesuite_hdma_gdma_addr_mask
  COMMAND test_samesuite_hdma gdma_addr_mask "${GBB_SAMESUITE_DIR}/gdma_addr_mask.gb")
add_test(NAME samesuite_hdma_hdma_lcd_off
  COMMAND test_samesuite_hdma hdma_lcd_off "${GBB_SAMESUITE_DIR}/hdma_lcd_off.gb")
add_test(NAME samesuite_hdma_hdma_mode0
  COMMAND test_samesuite_hdma hdma_mode0 "${GBB_SAMESUITE_DIR}/hdma_mode0.gb")
set_tests_properties(samesuite_hdma_gbc_dma_cont samesuite_hdma_gdma_addr_mask
  samesuite_hdma_hdma_lcd_off samesuite_hdma_hdma_mode0 PROPERTIES TIMEOUT 60)
add_test(NAME samesuite_hdma_gbc_dma_cont_control
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_samesuite_hdma>;gbc_dma_cont;${GBB_SAMESUITE_DIR}/gbc_dma_cont.gb;--mutants;0x20000000000"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=samesuite-hdma guest-result: expected pass sentinel"
    -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
set_tests_properties(samesuite_hdma_gbc_dma_cont_control PROPERTIES TIMEOUT 60)
add_test(NAME samesuite_hdma_gbc_dma_cont_corrupted_result_control
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_samesuite_hdma>;gbc_dma_cont;${GBB_SAMESUITE_DIR}/gbc_dma_cont.gb;--corrupt-result"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=samesuite-hdma data: corrupted-result mismatch"
    -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
set_tests_properties(samesuite_hdma_gbc_dma_cont_corrupted_result_control PROPERTIES TIMEOUT 60)

find_package(Python3 COMPONENTS Interpreter REQUIRED)
set(GBB_CGB_HDMA_DISPOSITIONS_VERIFIER
  "${PROJECT_SOURCE_DIR}/tests/scripts/verify-cgb-hdma-dispositions.py")
add_test(NAME cgb_hdma_dispositions
  COMMAND "${Python3_EXECUTABLE}" -I "${GBB_CGB_HDMA_DISPOSITIONS_VERIFIER}" --complete)
set_tests_properties(cgb_hdma_dispositions PROPERTIES TIMEOUT 30
  PASS_REGULAR_EXPRESSION "cgb-hdma-dispositions pass")
add_test(NAME cgb_hdma_dispositions_selftest
  COMMAND "${Python3_EXECUTABLE}" -I "${GBB_CGB_HDMA_DISPOSITIONS_VERIFIER}" --self-test)
set_tests_properties(cgb_hdma_dispositions_selftest PROPERTIES TIMEOUT 30
  PASS_REGULAR_EXPRESSION "cgb-hdma-dispositions self-test pass")

# Plan 13-12 keeps recurring claim, inventory and receipt-shape contracts Python-only so the
# native and sanitizer lanes do not depend on Node or the local OpenGSD runtime.
set(GBB_CGB_HDMA_CLAIMS_VERIFIER
  "${PROJECT_SOURCE_DIR}/tests/scripts/verify-cgb-hdma-claims.py")
set(GBB_HDMA_CLOSURE_CHECKER
  "${PROJECT_SOURCE_DIR}/.planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py")
set(GBB_HDMA_REMOTE_EVIDENCE_TEST
  "${PROJECT_SOURCE_DIR}/tests/scripts/test_hdma_remote_evidence.py")
add_test(NAME cgb_hdma_claims_contract
  COMMAND "${Python3_EXECUTABLE}" -I "${GBB_CGB_HDMA_CLAIMS_VERIFIER}")
add_test(NAME cgb_hdma_claims_contract_native
  COMMAND "${Python3_EXECUTABLE}" -I "${GBB_CGB_HDMA_CLAIMS_VERIFIER}" --native-player)
add_test(NAME cgb_hdma_claims_contract_selftest
  COMMAND "${Python3_EXECUTABLE}" -I "${GBB_CGB_HDMA_CLAIMS_VERIFIER}" --self-test)
add_test(NAME cgb_hdma_lane_contract
  COMMAND "${Python3_EXECUTABLE}" -I "${GBB_HDMA_CLOSURE_CHECKER}" --lane)
add_test(NAME cgb_hdma_lane_contract_selftest
  COMMAND "${Python3_EXECUTABLE}" -I "${GBB_HDMA_CLOSURE_CHECKER}" --lane-self-test)
add_test(NAME cgb_hdma_remote_evidence_selftest
  COMMAND "${Python3_EXECUTABLE}" -I "${GBB_HDMA_REMOTE_EVIDENCE_TEST}")
set_tests_properties(
  cgb_hdma_claims_contract cgb_hdma_claims_contract_native
  cgb_hdma_claims_contract_selftest cgb_hdma_lane_contract
  cgb_hdma_lane_contract_selftest cgb_hdma_remote_evidence_selftest PROPERTIES TIMEOUT 30)
find_program(GBB_SAMESUITE_REPRO_BASH bash REQUIRED)
add_test(NAME samesuite_repro_selfcheck
  COMMAND "${GBB_SAMESUITE_REPRO_BASH}" "${PROJECT_SOURCE_DIR}/tests/scripts/reproduce-samesuite.sh" --self-test)
set_tests_properties(samesuite_repro_selfcheck PROPERTIES
  TIMEOUT 30
  ENVIRONMENT "GBB_SAMESUITE_BASH=${GBB_SAMESUITE_REPRO_BASH}")

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
# RED: this binding test must reject the stale four-row inventory until Phase 14 expands it to nine.
add_test(NAME cgb_corpus_mooneye_controls
  COMMAND ${CMAKE_COMMAND}
    -DGBB_MODE=inventory
    -DGBB_MOONEYE_DIR=${PROJECT_SOURCE_DIR}/fixtures/mooneye-cgb
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyMooneyeCgb.cmake)
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
# Phase 14: the author pass assertion remains separate from the exact current software xfail; a tampered pass
# disposition, changed fail callback, stale unsupported stop and passing guest all remain failing controls.
add_test(NAME cgb_mooneye_expected_disposition_controls
  COMMAND test_runner cgb_mooneye_expected_disposition_controls
    ${PROJECT_BINARY_DIR}/mooneye-cgb-tamper/expect/manifest.json
    ${PROJECT_SOURCE_DIR}/fixtures/mooneye-cgb/manifest.json
    ${PROJECT_SOURCE_DIR}/fixtures/mooneye-cgb)
set_tests_properties(cgb_mooneye_expected_disposition_controls PROPERTIES TIMEOUT 30
  PASS_REGULAR_EXPRESSION "observed=fail alias=boot_hwio-C callback_result=fail callback_pc=01f5 result_pc=4067.*observed=fail alias=unused_hwio-C callback_result=fail callback_pc=1a31 result_pc=4070.*control=exact-failure-disposition alias=boot_hwio-C.*control=exact-failure-disposition alias=unused_hwio-C.*control=xfail-tampered-to-pass.*control=stale-unsupported-disposition.*control=expected-failure-wrong-callback.*control=expected-failure-pass-is-failure")
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
# These rows retain the upstream pass assertion. The current software observation is a fail at the exact
# listed fail callback and LD B,B result; the runner reports status=xfail, never status=pass.
foreach(alias boot_hwio-C unused_hwio-C)
  add_test(NAME cgb_mooneye_case_${alias}
    COMMAND gabbaboy-runner --manifest ${GBB_CGB_MOONEYE_MANIFEST} --case ${alias} --receipt)
  set_tests_properties(cgb_mooneye_case_${alias} PROPERTIES TIMEOUT 30
    PASS_REGULAR_EXPRESSION "author_expect=pass observed_disposition=expected-failure status=xfail observed=fail reason=declared-failure-signature callback_result=fail callback_pc=(01f5|1a31) result_pc=(4067|4070).*profile=CGB-CPU-E"
    FAIL_REGULAR_EXPRESSION "DMG-CPU-B|status=pass|status=unexpected-pass|status=unexpected-failure")
endforeach()
add_test(NAME cgb_mooneye_required_suite
  COMMAND gabbaboy-runner --manifest ${GBB_CGB_MOONEYE_MANIFEST} --suite --receipt)
set_tests_properties(cgb_mooneye_required_suite PROPERTIES TIMEOUT 30
  PASS_REGULAR_EXPRESSION "suite eligible=4 executed=4 status=pass-with-expected-failure.*suite categories post-boot-registers=1/1 post-boot-div=1/1 post-boot-hwio=0/1 post-boot-hwio.expected-failure=1 unused-hwio=0/1 unused-hwio.expected-failure=1.*expected-failure=2/2"
  FAIL_REGULAR_EXPRESSION "DMG-CPU-B|post-boot-hwio=1/1|unused-hwio=1/1")
# D-25 / D-05: --observe prints the not-applicable token for a CGB row and no DMG-labelled line.
add_test(NAME cgb_mooneye_observe_not_applicable
  COMMAND gabbaboy-runner --manifest ${GBB_CGB_MOONEYE_MANIFEST} --case boot_regs-cgb --observe)
set_tests_properties(cgb_mooneye_observe_not_applicable PROPERTIES TIMEOUT 30
  PASS_REGULAR_EXPRESSION "mooneye[.]boot_regs-cgb[.]frame\tnot-applicable"
  FAIL_REGULAR_EXPRESSION "frame_generation|ldbb_half_dots|not-ready")
# WR-03: reproduce-mooneye-cgb.sh --compare refuses a fixture directory without its manifest before any
# network work (offline; bash-only).
if(NOT WIN32)
  find_program(GBB_BASH_REPRO bash REQUIRED)
  add_test(NAME cgb_mooneye_repro_requires_manifest
    COMMAND "${GBB_BASH_REPRO}" ${PROJECT_SOURCE_DIR}/tests/scripts/test-reproduce-mooneye-cgb-guard.sh ${PROJECT_SOURCE_DIR})
  set_tests_properties(cgb_mooneye_repro_requires_manifest PROPERTIES TIMEOUT 60
    PASS_REGULAR_EXPRESSION "reproduce-mooneye-cgb guard ok")
endif()
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
string(JSON GBB_CGB_EXPECT_TAMPERED SET "${GBB_CGB_MANIFEST_JSON}" fixtures 2 observed_disposition "\"pass\"")
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

# CGB DMA package boundary: keep the author-test ROMs and MagenTests differential guest
# repository-only, including renamed copies. The two self-tests use the opposite single
# manifest as the baseline so they fail until the scanner consumes the complete digest set.
set(GBB_CGB_HDMA_SCAN_MANIFESTS
  "${PROJECT_SOURCE_DIR}/fixtures/samesuite/manifest.json|${GBB_MAGENTESTS_DIR}/manifest.json")
set(GBB_CGB_HDMA_SCAN_PATH_LABELS "samesuite|magentests|mealybug")
set(GBB_CGB_HDMA_SCAN_SELFTEST_SAMESUITE "${PROJECT_BINARY_DIR}/cgb-hdma-scan-samesuite-selftest")
set(GBB_CGB_HDMA_SCAN_SELFTEST_MAGEN "${PROJECT_BINARY_DIR}/cgb-hdma-scan-magentests-selftest")
set(GBB_CGB_HDMA_SCAN_SELFTEST_DIRECTORY "${PROJECT_BINARY_DIR}/cgb-hdma-scan-directory-selftest")
file(MAKE_DIRECTORY "${GBB_CGB_HDMA_SCAN_SELFTEST_SAMESUITE}/share"
  "${GBB_CGB_HDMA_SCAN_SELFTEST_MAGEN}/share"
  "${GBB_CGB_HDMA_SCAN_SELFTEST_DIRECTORY}/share/SameSuite")
file(COPY_FILE "${PROJECT_SOURCE_DIR}/fixtures/samesuite/gbc_dma_cont.gb"
  "${GBB_CGB_HDMA_SCAN_SELFTEST_SAMESUITE}/share/renamed-payload.bin")
file(COPY_FILE "${GBB_MAGENTESTS_DIR}/hblank_vram_dma.gbc"
  "${GBB_CGB_HDMA_SCAN_SELFTEST_MAGEN}/share/renamed-payload.bin")
file(WRITE "${GBB_CGB_HDMA_SCAN_SELFTEST_DIRECTORY}/share/SameSuite/marker.txt" "marker\n")
function(gbb_add_cgb_hdma_scan_test name code regex scan_dir baseline_manifest)
  set(command "${CMAKE_COMMAND}" "-DGBB_SCAN_DIR=${scan_dir}"
    "-DGBB_FORBIDDEN_MANIFEST=${baseline_manifest}"
    "-DGBB_FORBIDDEN_MANIFESTS=${GBB_CGB_HDMA_SCAN_MANIFESTS}"
    "-DGBB_FORBIDDEN_PATH_LABELS=${GBB_CGB_HDMA_SCAN_PATH_LABELS}"
    -DGBB_FORBIDDEN_LABEL=cgb-hdma
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
gbb_add_cgb_hdma_scan_test(cgb_hdma_not_installed 0
  "cgb-hdma absent from scanned tree files=[1-9]" "${GBB_LIBBET_INSTALL_CHECK}"
  "${PROJECT_SOURCE_DIR}/fixtures/samesuite/manifest.json")
set_tests_properties(cgb_hdma_not_installed PROPERTIES FIXTURES_REQUIRED libbet_install)
gbb_add_cgb_hdma_scan_test(cgb_hdma_not_installed_selftest 1
  "cgb-hdma-installed: share/renamed-payload.bin" "${GBB_CGB_HDMA_SCAN_SELFTEST_MAGEN}"
  "${PROJECT_SOURCE_DIR}/fixtures/samesuite/manifest.json")
gbb_add_cgb_hdma_scan_test(cgb_hdma_not_installed_samesuite_selftest 1
  "cgb-hdma-installed: share/renamed-payload.bin" "${GBB_CGB_HDMA_SCAN_SELFTEST_SAMESUITE}"
  "${GBB_MAGENTESTS_DIR}/manifest.json")
gbb_add_cgb_hdma_scan_test(cgb_hdma_not_installed_directory_selftest 1
  "cgb-hdma-installed: share/SameSuite/marker.txt" "${GBB_CGB_HDMA_SCAN_SELFTEST_DIRECTORY}"
  "${PROJECT_SOURCE_DIR}/fixtures/samesuite/manifest.json")

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

# Hosted ASan runs the whole suite under one 30-minute job timeout; serially it used about 20
# minutes and timed out on a slow runner (LESSONS GB-CI-004). The contract keeps the ASan ctest
# step parallel. The workflow declares its own identifiers, so only the scoped phrase is checked.
set(GBB_CI_WORKFLOW "${PROJECT_SOURCE_DIR}/.github/workflows/ci.yml")
set(GBB_CI_ASAN_PHRASE "ctest --preset phase1-asan --parallel 4")
add_test(NAME ci_asan_parallel_contract
  COMMAND ${CMAKE_COMMAND}
    -DGBB_DOC=${GBB_CI_WORKFLOW}
    -DGBB_DECLARATIONS=${GBB_CI_WORKFLOW}
    "-DGBB_REQUIRED=${GBB_CI_ASAN_PHRASE}"
    "-DGBB_SCOPE_START=name: linux-asan-ubsan"
    -P ${GBB_DOC_CONTRACT_SCRIPT})
set_tests_properties(ci_asan_parallel_contract PROPERTIES
  PASS_REGULAR_EXPRESSION "doc-contract pass identifiers=[0-9]+ phrases=1[^0-9]")
file(READ "${GBB_CI_WORKFLOW}" GBB_CI_WORKFLOW_TEXT)
string(REPLACE "phase1-asan --parallel 4" "phase1-asan" GBB_CI_WORKFLOW_SERIAL "${GBB_CI_WORKFLOW_TEXT}")
file(WRITE "${GBB_DOC_SELFTEST}/ci-serial.yml" "${GBB_CI_WORKFLOW_SERIAL}")
add_test(NAME ci_asan_parallel_serial_selftest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_DOC=${GBB_DOC_SELFTEST}/ci-serial.yml;-DGBB_DECLARATIONS=${GBB_DOC_SELFTEST}/ci-serial.yml;-DGBB_REQUIRED=${GBB_CI_ASAN_PHRASE};-DGBB_SCOPE_START=name: linux-asan-ubsan;-P;${GBB_DOC_CONTRACT_SCRIPT}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=doc-contract-missing: ctest --preset phase1-asan --parallel 4"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${GBB_CI_WORKFLOW}")

# CGB host-guide contract (D-28): the CGB section of the integration guide names only declared symbols
# and keeps each promise the header makes about the info API, PGB rejection, frame copy, banking and
# deferred registers. The missing-phrase selftest proves the check can fail.
set(GBB_NATIVE_GUIDE_CGB_PHRASES
  "sets it to 28"
  "outputs unchanged on error"
  "returns `GBB_UNSUPPORTED_EXECUTION_MODE`"
  "returns `GBB_UNSUPPORTED_PROFILE` on the CGB profile"
  "follows the selected WRAM bank"
  "stop with `GBB_STOP_UNSUPPORTED_BUS`"
  "bit 15 is rejected, not masked"
  "a set never recolours a completed frame"
  "minimum pitch is 320 bytes"
  "master half-dots at both speeds")
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
  "[ ]*/\\* MODEL: UNKNOWN GATE-62 research:14 -- STOP on the DMG, compat and unarmed paths \\*/\n")
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

# Plan SUMMARY coverage blocks (DECISIONS D-069, LESSONS GB-GSD-015): from Phase 11 on, every
# entry must be in the GSD classifier's block schema and auto-passable, so /gsd-verify-work never
# hands an automated deliverable to the owner. Phases 9-10 used a rejected shape; Phase 10 is the
# negative control.
set(GBB_SUMMARY_COVERAGE_CHECKER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-summary-coverage.py")
function(gbb_add_summary_coverage_test name code regex)
  set(command "${Python3_EXECUTABLE}" -I "${GBB_SUMMARY_COVERAGE_CHECKER}"
    --phases-dir "${PROJECT_SOURCE_DIR}/.planning/phases" ${ARGN})
  list(JOIN command "$<SEMICOLON>" joined)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${joined}"
      -DGBB_EXPECT_CODE=${code}
      "-DGBB_EXPECT_REGEX=${regex}"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT 60)
endfunction()
gbb_add_summary_coverage_test(summary_coverage_selftest 0 "summary-coverage self-test pass mutants=1[2-9]" --self-test)
gbb_add_summary_coverage_test(summary_coverage 0 "summary-coverage pass files=[0-9]+" --since 11)
gbb_add_summary_coverage_test(summary_coverage_phase10_rejected 1
  "summary-coverage-invalid: 10-01-SUMMARY.md: flow-style-not-supported" --since 10)

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
  PASS_REGULAR_EXPRESSION "cgb-tables self-test pass mutants=14")

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
      ENVIRONMENT "GBB_RELEASE_MEASURE_SAMPLES=3;GBB_RELEASE_MEASURE_WARMUPS=1;GBB_AB_TEST_HOOKS=1;GBB_AB_RECEIPT=${GBB_AB_DIR}/${name}.json;GBB_AB_DROP_FIELD=${drop_field};GBB_AB_EXPECT_DIGEST=${digest}")
  endfunction()
  gbb_add_bench_ab_control(cgb_bench_ab_wrong_digest "" 0000000000000000 "ab-digest-mismatch")
  gbb_add_bench_ab_control(cgb_bench_ab_missing_field uncertainty 4c7a57ff3d50d228
    "ab-receipt-missing: uncertainty")
  # IN-03: a measure binary whose mode= line has no elapsed_ns is a named error, not a KeyError traceback.
  add_test(NAME cgb_bench_ab_missing_elapsed
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${GBB_BASH}$<SEMICOLON>${GBB_AB_SCRIPT}$<SEMICOLON>--ab$<SEMICOLON>${PROJECT_SOURCE_DIR}/tests/scripts/ab-stub-no-elapsed.sh$<SEMICOLON>${PROJECT_SOURCE_DIR}/tests/scripts/ab-stub-no-elapsed.sh"
      -DGBB_EXPECT_CODE=1
      "-DGBB_EXPECT_REGEX=ab-field-missing: base elapsed_ns=absent"
      "-DGBB_FORBID_REGEX=Traceback|KeyError"
      "-DGBB_WORKDIR=${PROJECT_SOURCE_DIR}"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(cgb_bench_ab_missing_elapsed PROPERTIES TIMEOUT 120
    ENVIRONMENT "GBB_RELEASE_MEASURE_SAMPLES=3;GBB_RELEASE_MEASURE_WARMUPS=1;GBB_AB_RECEIPT=${GBB_AB_DIR}/missing-elapsed.json")
endif()

# --- Phase 11 plan 11-01 begin ---
# Colour tests (D-25, D-35 stage 1). The white-box driver includes the core (or, in a mutant, a
# build-tree copy named by GBB_COLOUR_CORE_SOURCE) and must not link GabbaBoy::core.
add_executable(test_cgb_colour_internal test_cgb_colour_internal.c)
target_include_directories(test_cgb_colour_internal PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_cgb_colour_internal PRIVATE c_std_17)
set_target_properties(test_cgb_colour_internal PROPERTIES C_EXTENSIONS OFF)
add_test(NAME cgb_dmg_identity_shade_pin
  COMMAND test_cgb_colour_internal cgb_dmg_identity_shade_pin ${PROJECT_SOURCE_DIR}/fixtures)
set_tests_properties(cgb_dmg_identity_shade_pin PROPERTIES
  PASS_REGULAR_EXPRESSION "cgb-colour-internal cgb_dmg_identity_shade_pin pass")

add_executable(test_cgb_colour test_cgb_colour.c)
target_link_libraries(test_cgb_colour PRIVATE gabbaboy_accept)
target_compile_features(test_cgb_colour PRIVATE c_std_17)
set_target_properties(test_cgb_colour PROPERTIES C_EXTENSIONS OFF)
add_test(NAME cgb_colour_copy_frame_unsupported COMMAND test_cgb_colour cgb_colour_copy_frame_unsupported)

# Generalised colour mutant harness. Like gbb_banking_mutant, but it reads the core text itself and
# supports a white-box test source (compiled with the mutated copy as the included core through
# GBB_COLOUR_CORE_SOURCE) or a public test source (linked to a STATIC mutant library). The anchor
# must occur exactly once, checked forward and in reverse, so a drifted core stops configure.
# failing_case and control_case are the full argument lists for the test executable.
set(GBB_COLOUR_CORE_SOURCE_PATH ${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c)
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${GBB_COLOUR_CORE_SOURCE_PATH})
file(READ ${GBB_COLOUR_CORE_SOURCE_PATH} gbb_colour_core_text)
function(gbb_colour_mutant name test_source fail_test control_test anchor replacement failing_case failing_regex control_case)
  string(FIND "${gbb_colour_core_text}" "${anchor}" first)
  string(FIND "${gbb_colour_core_text}" "${anchor}" final REVERSE)
  if(first EQUAL -1 OR NOT first EQUAL final)
    message(FATAL_ERROR "colour mutant ${name}: anchor '${anchor}' must occur exactly once in "
      "${GBB_COLOUR_CORE_SOURCE_PATH} (first=${first} last=${final})")
  endif()
  string(REPLACE "${anchor}" "${replacement}" text "${gbb_colour_core_text}")
  set(source ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_colour_mutant_${name}.c)
  file(WRITE ${source} "${text}")
  set(target test_cgb_colour_mutant_${name})
  if(test_source STREQUAL "test_cgb_colour_internal.c")
    add_executable(${target} ${test_source})
    target_include_directories(${target} PRIVATE ${PROJECT_SOURCE_DIR}/include)
    target_compile_definitions(${target} PRIVATE
      "GBB_COLOUR_CORE_SOURCE=\"${source}\""
      GBB_BUILD_REVISION="colour-mutant-${name}" GBB_BUILD_QUALIFIED=0)
  else()
    set(library gabbaboy_core_colour_mutant_${name})
    add_library(${library} STATIC ${source})
    target_include_directories(${library} PUBLIC ${PROJECT_SOURCE_DIR}/include)
    target_compile_features(${library} PUBLIC c_std_17)
    set_target_properties(${library} PROPERTIES C_EXTENSIONS OFF)
    target_compile_definitions(${library} PRIVATE
      GBB_BUILD_REVISION="colour-mutant-${name}" GBB_BUILD_QUALIFIED=0)
    add_executable(${target} ${test_source})
    # The acceptance helpers come after the mutant so every core symbol resolves to the mutated copy.
    target_link_libraries(${target} PRIVATE ${library} gabbaboy_accept)
  endif()
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
  # The mutant is meant to trip a REQUIRE, and REQUIRE returns early without destroying the
  # instance. Under phase1-asan, LeakSanitizer would then replace the expected exit 1 with its own
  # code, so leak detection is off for this deliberately failing run only. Controls and every other
  # test keep leak checking.
  set_tests_properties(${fail_test} PROPERTIES ENVIRONMENT "ASAN_OPTIONS=detect_leaks=0")
endfunction()

# Harness proof: flipping the low bit of the DMG BG shade must trip the shade-identity pin.
gbb_colour_mutant(shade_flip test_cgb_colour_internal.c
  cgb_dmg_identity_mutant_shade_flip cgb_dmg_identity_mutant_shade_flip_control
  "return ppu_palette_shade(m->bgp, background);"
  "return (uint8_t)(ppu_palette_shade(m->bgp, background) ^ 1u);"
  "cgb_dmg_identity_shade_pin;${PROJECT_SOURCE_DIR}/fixtures" "observed"
  cgb_colour_internal_harness_alive)
# Priority truth table (D-22, GB-CPU-002): an independent stdlib oracle written from Pan Docs.
set(GBB_PRIORITY_TRUTH_GEN "${PROJECT_SOURCE_DIR}/tests/scripts/gen-cgb-priority-truth.py")
set(GBB_PRIORITY_TRUTH_INC "${PROJECT_SOURCE_DIR}/tests/data/cgb-priority-truth.inc")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
  "${GBB_PRIORITY_TRUTH_GEN}" "${GBB_PRIORITY_TRUTH_INC}")
target_sources(test_cgb_colour_internal PRIVATE "${GBB_PRIORITY_TRUTH_INC}")
set_source_files_properties("${GBB_PRIORITY_TRUTH_INC}" PROPERTIES HEADER_FILE_ONLY TRUE)
add_test(NAME cgb_priority_truth_regen
  COMMAND ${Python3_EXECUTABLE} -I ${GBB_PRIORITY_TRUTH_GEN} --check ${GBB_PRIORITY_TRUTH_INC})
set_tests_properties(cgb_priority_truth_regen PROPERTIES
  PASS_REGULAR_EXPRESSION "check pass rows=6144")
add_test(NAME cgb_priority_truth_selftest
  COMMAND ${Python3_EXECUTABLE} -I ${GBB_PRIORITY_TRUTH_GEN} --self-test)
set_tests_properties(cgb_priority_truth_selftest PROPERTIES
  PASS_REGULAR_EXPRESSION "self-test pass inputs=9")
# A configure-time copy with the first row's expect_layer altered must fail the regenerate check.
file(READ "${GBB_PRIORITY_TRUTH_INC}" gbb_priority_truth_text)
set(gbb_priority_first_row "{0,0,0,0,0,0,0,0,0,0,0},")
string(REPLACE "${gbb_priority_first_row}" "{0,0,0,0,0,0,0,0,0,1,0}," gbb_priority_mutated
  "${gbb_priority_truth_text}")
if(gbb_priority_mutated STREQUAL gbb_priority_truth_text)
  message(FATAL_ERROR "priority truth mutant: first row '${gbb_priority_first_row}' not found in "
    "${GBB_PRIORITY_TRUTH_INC}")
endif()
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/cgb-priority-truth-mutated.inc" "${gbb_priority_mutated}")
add_test(NAME cgb_priority_truth_regen_mutated
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${Python3_EXECUTABLE}$<SEMICOLON>-I$<SEMICOLON>${GBB_PRIORITY_TRUTH_GEN}$<SEMICOLON>--check$<SEMICOLON>${CMAKE_CURRENT_BINARY_DIR}/cgb-priority-truth-mutated.inc"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=cgb-priority-truth mismatch"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
add_test(NAME cgb_priority_table_shape COMMAND test_cgb_colour_internal cgb_priority_table_shape)
set_tests_properties(cgb_priority_table_shape PROPERTIES
  PASS_REGULAR_EXPRESSION "cgb_priority_table_shape pass")
# --- Phase 11 plan 11-01 end ---

# --- Phase 11 plan 11-02 begin ---
# Palette RAM and OPRI ports (D-08, D-10 to D-14). White-box cases drive read8/write8 directly.
foreach(gbb_palette_case
    palette_cram_bg_autoinc palette_cram_bg_readback palette_cram_bg_blocked_write
    palette_cram_bg_blocked_read palette_cram_lockout_lcd_off palette_cram_obj_autoinc
    palette_cram_compat_ports palette_opri_cgb palette_opri_compat cgb_postboot_cram_white
    cgb_postboot_vram1_zero)
  add_test(NAME ${gbb_palette_case} COMMAND test_cgb_colour_internal ${gbb_palette_case})
  set_tests_properties(${gbb_palette_case} PROPERTIES
    PASS_REGULAR_EXPRESSION "cgb-colour-internal ${gbb_palette_case} pass")
endforeach()
# Negative controls for the palette ports (D-11, D-12). Each mutant rewrites one statement of the
# core in a build-tree copy; the named case must exit 1 on the REQUIRE that guards that rule, and
# a case the mutant does not touch must still exit 0.
gbb_colour_mutant(palette_blocked_no_increment test_cgb_colour_internal.c
  palette_mutant_blocked_no_increment palette_mutant_blocked_no_increment_control
  "if ((*index_reg & 0x80u) != 0u) *index_reg ="
  "if (allowed && (*index_reg & 0x80u) != 0u) *index_reg ="
  "palette_cram_bg_blocked_write" "0xC6u"
  palette_cram_bg_autoinc)
gbb_colour_mutant(palette_read_increments test_cgb_colour_internal.c
  palette_mutant_read_increments palette_mutant_read_increments_control
  "case IO_BCPD: return cram_data_read(m->bcps, m->bg_cram, cpu_cram_access_allowed(m));"
  "case IO_BCPD: { const uint8_t mutant_byte = cram_data_read(m->bcps, m->bg_cram, cpu_cram_access_allowed(m)); if ((m->bcps & 0x80u) != 0u) ((gbb_instance *)m)->bcps = (uint8_t)(0x80u | ((m->bcps + 1u) & 0x3Fu)); return mutant_byte; }"
  "palette_cram_bg_readback" "read8.m, BCPD. == 0x6Bu"
  palette_cram_obj_autoinc)
gbb_colour_mutant(palette_lock_always_allowed test_cgb_colour_internal.c
  palette_mutant_lock_always_allowed palette_mutant_lock_always_allowed_control
  "edge offsets unresearched (D-12) */"
  "edge offsets unresearched (D-12) */ return 1;"
  "palette_cram_bg_blocked_write" "bg_cram.5. == 0x34u"
  palette_cram_bg_autoinc)
gbb_colour_mutant(palette_lock_ignores_lcd_off test_cgb_colour_internal.c
  palette_mutant_lock_ignores_lcd_off palette_mutant_lock_ignores_lcd_off_control
  "edge offsets unresearched (D-12) */"
  "edge offsets unresearched (D-12) */ return m->ppu_mode != 3u;"
  "palette_cram_lockout_lcd_off" "bg_cram.0. == 0x12u"
  palette_cram_bg_autoinc)
# --- Phase 11 plan 11-02 end ---

# --- Phase 11 plan 11-03 begin ---
# CGB-mode rendering (D-01 to D-09): white-box cases set VRAM, OAM and CRAM, run frames and read rgb_completed.
foreach(gbb_rgb_case
    cgb_rgb_store_bg_palette cgb_rgb_store_shade_untouched cgb_rgb_store_lcd_off
    cgb_rgb_store_reset cgb_rgb_store_bit15_masked
    cgb_attr_palette cgb_attr_bank cgb_attr_xflip cgb_attr_yflip cgb_attr_bit4_ignored
    cgb_attr_bg_priority cgb_attr_lcdc0_bg_drawn cgb_attr_window_same_fetch
    cgb_attr_window_lcdc0_clear cgb_attr_obj_bank_palette cgb_attr_obj_oam_order
    cgb_attr_vbk_not_read)
  add_test(NAME ${gbb_rgb_case} COMMAND test_cgb_colour_internal ${gbb_rgb_case})
  set_tests_properties(${gbb_rgb_case} PROPERTIES
    PASS_REGULAR_EXPRESSION "cgb-colour-internal ${gbb_rgb_case} pass")
endforeach()
add_test(NAME cgb_rgb_store_dmg_untouched
  COMMAND test_cgb_colour_internal cgb_rgb_store_dmg_untouched ${PROJECT_SOURCE_DIR}/fixtures)
set_tests_properties(cgb_rgb_store_dmg_untouched PROPERTIES
  PASS_REGULAR_EXPRESSION "cgb-colour-internal cgb_rgb_store_dmg_untouched pass")
# A colour path that also writes the shade store must be caught (D-25).
gbb_colour_mutant(colour_writes_shade test_cgb_colour_internal.c
  cgb_dmg_identity_mutant_colour_writes_shade cgb_dmg_identity_mutant_colour_writes_shade_control
  "m->rgb_working[pixel_at] = ppu_pixel_cgb(m, fetched_slot);"
  "m->rgb_working[pixel_at] = ppu_pixel_cgb(m, fetched_slot); m->frame_working[pixel_at] = 1u;"
  "cgb_rgb_store_shade_untouched" "frame_working"
  cgb_rgb_store_bg_palette)
# --- Phase 11 plan 11-03 end ---

# --- Phase 11 plan 11-04 begin ---
# Compat rendering (D-17, D-18, D-39): DMG software on the CGB profile through the instance compat palette.
foreach(gbb_compat_case
    cgb_compat_internal_default cgb_compat_internal_bg cgb_compat_internal_obj_sets
    cgb_compat_internal_attr_ignored cgb_compat_internal_lcdc0 cgb_compat_internal_x_order
    cgb_compat_internal_live_config)
  add_test(NAME ${gbb_compat_case} COMMAND test_cgb_colour_internal ${gbb_compat_case})
  set_tests_properties(${gbb_compat_case} PROPERTIES
    PASS_REGULAR_EXPRESSION "cgb-colour-internal ${gbb_compat_case} pass")
endforeach()
# --- Phase 11 plan 11-04 end ---

# --- Phase 11 plan 11-05 begin ---
# Priority truth table and attribute mutants (D-22, D-06 to D-08, D-39). Tests only: no core edit.
add_test(NAME cgb_priority_truth_table COMMAND test_cgb_colour_internal cgb_priority_truth_table)
set_tests_properties(cgb_priority_truth_table PROPERTIES
  PASS_REGULAR_EXPRESSION "cgb-colour-internal cgb_priority_truth_table pass rows=6144")
add_test(NAME cgb_priority_truth_frames COMMAND test_cgb_colour_internal cgb_priority_truth_frames)
set_tests_properties(cgb_priority_truth_frames PROPERTIES
  PASS_REGULAR_EXPRESSION "cgb-colour-internal cgb_priority_truth_frames pass sampled=")
add_test(NAME cgb_priority_opri_no_effect COMMAND test_cgb_colour_internal cgb_priority_opri_no_effect)
set_tests_properties(cgb_priority_opri_no_effect PROPERTIES
  PASS_REGULAR_EXPRESSION "cgb-colour-internal cgb_priority_opri_no_effect pass rows=6144")
gbb_colour_mutant(priority_ignore_bg_attr7 test_cgb_colour_internal.c
  cgb_priority_mutant_ignore_bg_attr7 cgb_priority_mutant_ignore_bg_attr7_control
  "((obj_attr | bg_attr) & 0x80u)"
  "((obj_attr) & 0x80u)"
  "cgb_priority_truth_table" "truth mismatch row="
  cgb_colour_internal_harness_alive)
gbb_colour_mutant(priority_ignore_obj_attr7 test_cgb_colour_internal.c
  cgb_priority_mutant_ignore_obj_attr7 cgb_priority_mutant_ignore_obj_attr7_control
  "((obj_attr | bg_attr) & 0x80u)"
  "((bg_attr) & 0x80u)"
  "cgb_priority_truth_table" "truth mismatch row="
  cgb_colour_internal_harness_alive)
gbb_colour_mutant(priority_lcdc0_inverted test_cgb_colour_internal.c
  cgb_priority_mutant_lcdc0_inverted cgb_priority_mutant_lcdc0_inverted_control
  "if ((lcdc & 0x01u) == 0) return CGB_LAYER_OBJ;"
  "if ((lcdc & 0x01u) != 0) return CGB_LAYER_OBJ;"
  "cgb_priority_truth_table" "truth mismatch row="
  cgb_colour_internal_harness_alive)
gbb_colour_mutant(priority_no_index0_rule test_cgb_colour_internal.c
  cgb_priority_mutant_no_index0_rule cgb_priority_mutant_no_index0_rule_control
  "    if (bg_index == 0u) return CGB_LAYER_OBJ;\n"
  ""
  "cgb_priority_truth_table" "truth mismatch row="
  cgb_colour_internal_harness_alive)
gbb_colour_mutant(priority_cgb_x_order test_cgb_colour_internal.c
  cgb_priority_mutant_cgb_x_order cgb_priority_mutant_cgb_x_order_control
  "int opaque = ppu_cgb_object(m, x, &object, &object_attr);"
  "int opaque = ppu_object_color(m, x, &object, &object_attr);"
  "cgb_priority_truth_table" "truth mismatch row="
  cgb_colour_internal_harness_alive)
gbb_colour_mutant(priority_compat_lcdc0_ignored test_cgb_colour_internal.c
  cgb_priority_mutant_compat_lcdc0_ignored cgb_priority_mutant_compat_lcdc0_ignored_control
  "static uint16_t ppu_pixel_compat(gbb_instance *m, unsigned x) {\n    uint8_t background = (m->lcdc & 0x01u) != 0 ?"
  "static uint16_t ppu_pixel_compat(gbb_instance *m, unsigned x) {\n    uint8_t background = 1 ?"
  "cgb_priority_truth_table" "truth mismatch row="
  cgb_colour_internal_harness_alive)
gbb_colour_mutant(priority_compat_bg_set_for_objects test_cgb_colour_internal.c
  cgb_priority_mutant_compat_bg_set_for_objects cgb_priority_mutant_compat_bg_set_for_objects_control
  "return ppu_compat_resolve(m, 1u + ((attributes >> 4) & 1u), ppu_palette_shade(palette, object));"
  "return ppu_compat_resolve(m, 0u, ppu_palette_shade(palette, object));"
  "cgb_priority_truth_table" "truth mismatch row="
  cgb_colour_internal_harness_alive)
gbb_colour_mutant(priority_opri_live test_cgb_colour_internal.c
  cgb_priority_mutant_opri_live cgb_priority_mutant_opri_live_control
  "int opaque = ppu_cgb_object(m, x, &object, &object_attr);"
  "int opaque = (m->opri & 1u) ? ppu_object_color(m, x, &object, &object_attr) : ppu_cgb_object(m, x, &object, &object_attr);"
  "cgb_priority_opri_no_effect" "truth mismatch row="
  cgb_colour_internal_harness_alive)
gbb_colour_mutant(attr_ignore_bank test_cgb_colour_internal.c
  cgb_attr_mutant_ignore_bank cgb_attr_mutant_ignore_bank_control
  "return ppu_cgb_tile_color(m, tile, (attributes >> 3) & 1u, row, column, 0);"
  "return ppu_cgb_tile_color(m, tile, 0u, row, column, 0);"
  "cgb_attr_bank" "px[(]m, 0, 0[)] == bgcol[(]0, 3[)]"
  cgb_colour_internal_harness_alive)
gbb_colour_mutant(attr_swap_flips test_cgb_colour_internal.c
  cgb_attr_mutant_swap_flips cgb_attr_mutant_swap_flips_control
  "if ((attributes & 0x40u) != 0) row = 7u - row;\n    if ((attributes & 0x20u) != 0) column = 7u - column;"
  "if ((attributes & 0x20u) != 0) row = 7u - row;\n    if ((attributes & 0x40u) != 0) column = 7u - column;"
  "cgb_attr_xflip" "px[(]m, 8, 3[)] == bgcol[(]0, 0[)]"
  cgb_colour_internal_harness_alive)
gbb_colour_mutant(attr_reads_vbk test_cgb_colour_internal.c
  cgb_attr_mutant_reads_vbk cgb_attr_mutant_reads_vbk_control
  "return ppu_cgb_tile_color(m, tile, (attributes >> 3) & 1u, row, column, 0);"
  "return ppu_cgb_tile_color(m, tile, m->vram_bank & 1u, row, column, 0);"
  "cgb_attr_vbk_not_read" "memcmp"
  cgb_colour_internal_harness_alive)
gbb_colour_mutant(attr_obj_bank_ignored test_cgb_colour_internal.c
  cgb_attr_mutant_obj_bank_ignored cgb_attr_mutant_obj_bank_ignored_control
  "ppu_cgb_tile_color(m, (uint8_t)tile, (attrs >> 3) & 1u,"
  "ppu_cgb_tile_color(m, (uint8_t)tile, 0u,"
  "cgb_attr_obj_bank_palette" "seen[[]0[]] == objcol[(]3, 3[)]"
  cgb_colour_internal_harness_alive)
# --- Phase 11 plan 11-05 end ---

# --- Phase 11 plan 11-06 begin ---
# Public colour ABI (D-15, D-17a, D-42): gbb_copy_frame_rgb555 and the compat palette.
foreach(gbb_rgb555_case cgb_rgb555_args cgb_rgb555_dmg_profile cgb_rgb555_not_ready
    cgb_rgb555_both_modes cgb_rgb555_lcd_off)
  add_test(NAME ${gbb_rgb555_case} COMMAND test_cgb_colour ${gbb_rgb555_case})
  set_tests_properties(${gbb_rgb555_case} PROPERTIES PASS_REGULAR_EXPRESSION "ok 1 - ${gbb_rgb555_case}")
endforeach()
# Skewed validator: the profile test moved ahead of the argument checks must fail the argument matrix.
gbb_colour_mutant(rgb555_skewed_validator test_cgb_colour.c
  cgb_rgb555_mutant_skewed_validator cgb_rgb555_mutant_skewed_validator_control
  "    const size_t row_bytes = (size_t)GBB_FRAME_WIDTH * 2u;\n"
  "    const size_t row_bytes = (size_t)GBB_FRAME_WIDTH * 2u;\n    if (instance != NULL && !model_is_cgb(instance)) return GBB_UNSUPPORTED_PROFILE;\n"
  "cgb_rgb555_args" "not ok"
  cgb_rgb555_both_modes)
foreach(gbb_palette_api_case palette_compat_api_default palette_compat_api_roundtrip
    palette_compat_api_reject palette_compat_api_get_reject palette_compat_api_larger
    palette_compat_api_survives palette_compat_effect_next_frame)
  add_test(NAME ${gbb_palette_api_case} COMMAND test_cgb_colour ${gbb_palette_api_case})
  set_tests_properties(${gbb_palette_api_case} PROPERTIES PASS_REGULAR_EXPRESSION "ok 1 - ${gbb_palette_api_case}")
endforeach()
# Masking bit 15 instead of rejecting it must fail the rejection case.
gbb_colour_mutant(palette_mask_bit15 test_cgb_colour.c
  palette_compat_mutant_mask_bit15 palette_compat_mutant_mask_bit15_control
  "if (((palette->bg[i] | palette->obj0[i] | palette->obj1[i]) & 0x8000u) != 0u)\n            return GBB_INVALID_ARGUMENT;"
  "(void)i;"
  "palette_compat_api_reject" "not ok"
  palette_compat_api_default)
# The default palette block in the doc must equal the code table and the rule.
add_test(NAME cgb_tables_compat_palette COMMAND test_cgb_tables compat_palette "${GBB_CGB_PROFILE_DOC}")
set_tests_properties(cgb_tables_compat_palette PROPERTIES
  PASS_REGULAR_EXPRESSION "cgb-tables compat_palette pass rows=3")
set(GBB_COMPAT_PALETTE_ANCHOR "| OBJ1 | $639F |")
string(FIND "${gbb_cgb_doc}" "${GBB_COMPAT_PALETTE_ANCHOR}" gbb_cp_at)
string(FIND "${gbb_cgb_doc}" "${GBB_COMPAT_PALETTE_ANCHOR}" gbb_cp_last REVERSE)
if(gbb_cp_at EQUAL -1 OR NOT gbb_cp_at EQUAL gbb_cp_last)
  message(FATAL_ERROR "compat palette mutation anchor '${GBB_COMPAT_PALETTE_ANCHOR}' must occur exactly once in docs/cgb-profile.md")
endif()
string(REPLACE "${GBB_COMPAT_PALETTE_ANCHOR}" "| OBJ1 | $639E |" gbb_cp_doc_bad "${gbb_cgb_doc}")
file(WRITE "${PROJECT_BINARY_DIR}/cgb-tables/mutated-compat-palette.md" "${gbb_cp_doc_bad}")
add_test(NAME cgb_tables_compat_palette_mutated_doc
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_tables>;compat_palette;${PROJECT_BINARY_DIR}/cgb-tables/mutated-compat-palette.md"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=cgb-tables mismatch"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
# Every Phase 11 public symbol is called by both installed consumers (D-42).
set(GBB_PHASE11_CONSUMER_SYMBOLS
  "gbb_copy_frame_rgb555,gbb_set_compat_palette,gbb_get_compat_palette,GBB_COMPAT_PALETTE_SIZE_V1")
add_test(NAME cgb_consumer_symbol_coverage
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CONSUMER_SOURCES=${PROJECT_SOURCE_DIR}/tests/consumers/c/main.c,${PROJECT_SOURCE_DIR}/tests/consumers/cpp/main.cpp"
    "-DGBB_SYMBOLS=${GBB_PHASE11_CONSUMER_SYMBOLS}"
    -P ${PROJECT_SOURCE_DIR}/tests/cgb_consumer_symbol_coverage.cmake)
set_tests_properties(cgb_consumer_symbol_coverage PROPERTIES
  PASS_REGULAR_EXPRESSION "consumer-symbol-coverage pass")
file(READ "${PROJECT_SOURCE_DIR}/tests/consumers/c/main.c" gbb_consumer_c_text)
string(REPLACE "gbb_get_compat_palette" "gbb_removed_symbol" gbb_consumer_c_missing "${gbb_consumer_c_text}")
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/consumer-symbol-selftest")
file(WRITE "${PROJECT_BINARY_DIR}/consumer-symbol-selftest/main.c" "${gbb_consumer_c_missing}")
add_test(NAME cgb_consumer_symbol_coverage_selftest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_CONSUMER_SOURCES=${PROJECT_BINARY_DIR}/consumer-symbol-selftest/main.c;-DGBB_SYMBOLS=${GBB_PHASE11_CONSUMER_SYMBOLS};-P;${PROJECT_SOURCE_DIR}/tests/cgb_consumer_symbol_coverage.cmake"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=consumer-symbol-missing gbb_get_compat_palette"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
# --- Phase 11 plan 11-06 end ---

# --- Phase 11 plan 11-07 begin ---
# Original per-line colour fixture (D-23 item 4): a guest rewrites BG colour 0 in each HBlank, so
# every row of the public RGB555 frame must carry its own colour. The pinned rebuild is
# tests/scripts/reproduce-cgb-colour.sh, run by the fixture-repro workflow.
set(GBB_CGB_COLOUR_DIR "${PROJECT_SOURCE_DIR}/fixtures/cgb-colour")
add_test(NAME cgb_colour_fixture_digest
  COMMAND ${CMAKE_COMMAND}
    -DMANIFEST=${GBB_CGB_COLOUR_DIR}/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixtureManifest.cmake)
add_test(NAME cgb_colour_hblank_rows COMMAND test_cgb_colour cgb_colour_hblank_rows ${GBB_CGB_COLOUR_DIR})
set_tests_properties(cgb_colour_hblank_rows PROPERTIES PASS_REGULAR_EXPRESSION "ok 1 - cgb_colour_hblank_rows")
# Resolve-time control: serving the whole frame from one CRAM snapshot (taken at the first pixel of
# line 0, as a copy-time resolve would) must fail the per-row predicate.
gbb_colour_mutant(frame_resolve test_cgb_colour.c
  cgb_colour_mutant_frame_resolve cgb_colour_mutant_frame_resolve_control
  "    return cram_colour(m->bg_cram, bg_attr & 7u, bg_index);\n"
  "    static uint8_t gbb_frame_cram_snapshot[64];\n    if (m->ly == 0 && x == 0u) memcpy(gbb_frame_cram_snapshot, m->bg_cram, sizeof(gbb_frame_cram_snapshot));\n    return cram_colour(gbb_frame_cram_snapshot, bg_attr & 7u, bg_index);\n"
  "cgb_colour_hblank_rows;${GBB_CGB_COLOUR_DIR}" "row [0-9]+ is not uniform"
  cgb_rgb555_both_modes)
# --- Phase 11 plan 11-07 end ---

# --- Phase 11 plan 11-08 begin ---
# Remaining original colour fixtures (D-23): attribute bits and LCDC.0 priority first; each case
# checks its literal structural predicate before the frame digest is compared.
foreach(gbb_colour_fixture_case cgb_colour_attr cgb_colour_lcdc0 cgb_colour_guest_cram
    palette_compat_mapping cgb_colour_lcd_off)
  add_test(NAME ${gbb_colour_fixture_case} COMMAND test_cgb_colour ${gbb_colour_fixture_case} ${GBB_CGB_COLOUR_DIR})
  set_tests_properties(${gbb_colour_fixture_case} PROPERTIES
    PASS_REGULAR_EXPRESSION "ok 1 - ${gbb_colour_fixture_case}")
endforeach()
add_test(NAME cgb_rgb_store_lcdoff_fixture
  COMMAND test_cgb_colour_internal cgb_rgb_store_lcdoff_fixture ${PROJECT_SOURCE_DIR}/fixtures)
set_tests_properties(cgb_rgb_store_lcdoff_fixture PROPERTIES
  PASS_REGULAR_EXPRESSION "cgb-colour-internal cgb_rgb_store_lcdoff_fixture pass")
# Port-semantics control (D-11): a blocked palette write that stops advancing the index must make
# the CRAM guest report a failed cell. The control runs a fixture that only writes with the LCD off.
gbb_colour_mutant(guest_cram_blocked_no_increment test_cgb_colour.c
  cgb_colour_guest_cram_mutant_blocked_no_increment cgb_colour_guest_cram_mutant_blocked_no_increment_control
  "if ((*index_reg & 0x80u) != 0u) *index_reg ="
  "if (allowed && (*index_reg & 0x80u) != 0u) *index_reg ="
  "cgb_colour_guest_cram;${GBB_CGB_COLOUR_DIR}" "C00"
  "cgb_colour_attr;${GBB_CGB_COLOUR_DIR}")
# --- Phase 11 plan 11-08 end ---

# --- Phase 11 plan 11-10 begin ---
# MagenTests CGB PPU ROMs (D-21): colour mutants of the public test_magentests.c driver. The
# failing run is a REQUIRE-style early return, handled by gbb_colour_mutant (leak detection off).
# ppu_disabled_state needs STAT mode 0 with the LCD off; skipping the mode-0 transition leaves the
# guest in mode 1 and it paints the failure red.
gbb_colour_mutant(magentests_lcd_off_no_mode0 test_magentests.c
  magentests_cgb_mutant_lcd_off_no_mode0 magentests_cgb_mutant_lcd_off_no_mode0_control
  "            ppu_set_mode(m, 0);\n            m->ppu_selected_object_count = 0;"
  "            m->ppu_selected_object_count = 0;"
  "magentests_cgb_ppu_disabled_state;${GBB_MAGENTESTS_DIR}/ppu_disabled_state.gbc" "magentests_cgb_ppu_disabled_state: pixel 0,0 expected 0x03E0 got 0x001F"
  "magentests_oob_sram_mbc1;${GBB_MAGENTESTS_DIR}/mbc_oob_sram_mbc1.gbc")
# WR-01: the compat variant must also see the guest's STAT verdict (BGP 0x00 pass vs 0x0C fail maps
# colour index 1 to shade 0 vs shade 3). Same mutant, compat case.
gbb_colour_mutant(magentests_lcd_off_no_mode0_compat test_magentests.c
  magentests_cgb_mutant_lcd_off_no_mode0_compat magentests_cgb_mutant_lcd_off_no_mode0_compat_control
  "            ppu_set_mode(m, 0);\n            m->ppu_selected_object_count = 0;"
  "            m->ppu_selected_object_count = 0;"
  "magentests_cgb_ppu_disabled_state_compat;${GBB_MAGENTESTS_DIR}/ppu_disabled_state.gbc" "magentests_cgb_ppu_disabled_state_compat: pixel 0,0 expected"
  "magentests_oob_sram_mbc1;${GBB_MAGENTESTS_DIR}/mbc_oob_sram_mbc1.gbc")
# Object colours resolved from BG CRAM instead of object CRAM must turn the green and red
# triangles of oam_internal_priority into the BG white (RESEARCH Correction 4: this ROM's objects
# never share an opaque pixel, so X ordering is not its control; ordering stays in the truth table).
gbb_colour_mutant(magentests_obj_from_bg_cram test_magentests.c
  magentests_cgb_mutant_obj_from_bg_cram magentests_cgb_mutant_obj_from_bg_cram_control
  "return cram_colour(m->obj_cram, object_attr & 7u, object);"
  "return cram_colour(m->bg_cram, object_attr & 7u, object);"
  "magentests_cgb_oam_internal_priority;${GBB_MAGENTESTS_DIR}/oam_internal_priority.gbc" "magentests_cgb_oam_internal_priority: pixel [0-9]+,[0-9]+ expected 0x"
  "magentests_oob_sram_mbc1;${GBB_MAGENTESTS_DIR}/mbc_oob_sram_mbc1.gbc")
# An inverted LCDC.0 test in the composer must break the per-band priority layout of bg_oam_priority.
gbb_colour_mutant(magentests_lcdc0_inverted test_magentests.c
  magentests_cgb_mutant_lcdc0_inverted magentests_cgb_mutant_lcdc0_inverted_control
  "if ((lcdc & 0x01u) == 0) return CGB_LAYER_OBJ;"
  "if ((lcdc & 0x01u) != 0) return CGB_LAYER_OBJ;"
  "magentests_cgb_bg_oam_priority;${GBB_MAGENTESTS_DIR}/bg_oam_priority.gbc" "magentests_cgb_bg_oam_priority: pixel [0-9]+,[0-9]+ expected 0x"
  "magentests_oob_sram_mbc1;${GBB_MAGENTESTS_DIR}/mbc_oob_sram_mbc1.gbc")
# --- Phase 11 plan 11-10 end ---

# --- Phase 11 plan 11-11 begin ---
# External CGB PPU suites recorded but not run (D-09, D-20): an offline verifier of the disposition
# record, its docs mirror and the tracked file list. No ROM bytes, no network.
set(GBB_EXT_DISPOSITIONS_RECORD "${PROJECT_SOURCE_DIR}/tests/external/cgb-ppu-dispositions.json")
set(GBB_EXT_DISPOSITIONS_VERIFIER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-external-dispositions.py")
add_test(NAME cgb_external_dispositions
  COMMAND "${Python3_EXECUTABLE}" -I "${GBB_EXT_DISPOSITIONS_VERIFIER}"
    --record "${GBB_EXT_DISPOSITIONS_RECORD}" --doc "${GBB_CGB_PROFILE_DOC}" --repo-root "${PROJECT_SOURCE_DIR}")
set_tests_properties(cgb_external_dispositions PROPERTIES
  PASS_REGULAR_EXPRESSION "external-dispositions pass age=6" TIMEOUT 30)
# Negative control: one AGE reason changed in a configure-time copy must be rejected.
file(READ "${GBB_EXT_DISPOSITIONS_RECORD}" gbb_ext_record)
set(GBB_EXT_REASON_ANCHOR "\"src/m3-bg-lcdc/m3-bg-lcdc-cgbBCE.png\",\n          \"disposition\": \"expected-unsupported\",\n          \"reason\": \"mode-3-pixel-timing\"")
string(FIND "${gbb_ext_record}" "${GBB_EXT_REASON_ANCHOR}" gbb_ext_at)
string(FIND "${gbb_ext_record}" "${GBB_EXT_REASON_ANCHOR}" gbb_ext_last REVERSE)
if(gbb_ext_at EQUAL -1 OR NOT gbb_ext_at EQUAL gbb_ext_last)
  message(FATAL_ERROR "external disposition mutation anchor must occur exactly once in cgb-ppu-dispositions.json")
endif()
string(REPLACE "${GBB_EXT_REASON_ANCHOR}"
  "\"src/m3-bg-lcdc/m3-bg-lcdc-cgbBCE.png\",\n          \"disposition\": \"expected-unsupported\",\n          \"reason\": \"timing-not-needed\""
  gbb_ext_record_bad "${gbb_ext_record}")
file(WRITE "${PROJECT_BINARY_DIR}/external-dispositions/mutated.json" "${gbb_ext_record_bad}")
add_test(NAME cgb_external_dispositions_mutated
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${Python3_EXECUTABLE};-I;${GBB_EXT_DISPOSITIONS_VERIFIER};--record;${PROJECT_BINARY_DIR}/external-dispositions/mutated.json;--doc;${GBB_CGB_PROFILE_DOC};--repo-root;${PROJECT_SOURCE_DIR}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=disposition-mismatch"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
# Negative control: an image fixture cannot be marked executed by an external disposition scan.
file(READ "${PROJECT_SOURCE_DIR}/fixtures/age/manifest.json" gbb_ext_age_manifest)
string(JSON gbb_ext_age_fixture_count LENGTH "${gbb_ext_age_manifest}" fixtures)
math(EXPR gbb_ext_age_fixture_last "${gbb_ext_age_fixture_count} - 1")
set(gbb_ext_pending_image_found OFF)
foreach(gbb_ext_age_index RANGE 0 ${gbb_ext_age_fixture_last})
  string(JSON gbb_ext_age_file GET "${gbb_ext_age_manifest}" fixtures ${gbb_ext_age_index} file)
  if(gbb_ext_age_file STREQUAL "m3-bg-lcdc-cgbBCE.gb")
    set(gbb_ext_pending_image_found ON)
    string(JSON gbb_ext_age_manifest_pending_bad SET "${gbb_ext_age_manifest}"
      fixtures ${gbb_ext_age_index} qualification_status "\"pass\"")
  endif()
endforeach()
if(NOT gbb_ext_pending_image_found)
  message(FATAL_ERROR "external disposition pending-image control could not find its AGE manifest entry")
endif()
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/external-dispositions")
file(WRITE "${PROJECT_BINARY_DIR}/external-dispositions/image-pending-mutated.json"
  "${gbb_ext_age_manifest_pending_bad}")
add_test(NAME cgb_external_dispositions_image_pending
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${Python3_EXECUTABLE};-I;${GBB_EXT_DISPOSITIONS_VERIFIER};--record;${GBB_EXT_DISPOSITIONS_RECORD};--doc;${GBB_CGB_PROFILE_DOC};--repo-root;${PROJECT_SOURCE_DIR};--age-manifest;${PROJECT_BINARY_DIR}/external-dispositions/image-pending-mutated.json"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=disposition-mismatch age-image-pending"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
# Optional acid2 local runner (D-24): required CI runs synthetic self-tests only, never an acid2 file.
set(GBB_ACID2_LOCAL "${PROJECT_SOURCE_DIR}/tests/scripts/run-acid2-local.py")
add_test(NAME cgb_acid2_local_selftest COMMAND "${Python3_EXECUTABLE}" -I "${GBB_ACID2_LOCAL}" --self-test)
set_tests_properties(cgb_acid2_local_selftest PROPERTIES
  PASS_REGULAR_EXPRESSION "self-test pass checks=5" TIMEOUT 30)
# The repository LICENSE is not a pinned ROM, so the runner must refuse it before running anything.
add_test(NAME cgb_acid2_local_refuses_unpinned
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${Python3_EXECUTABLE};-I;${GBB_ACID2_LOCAL};--rom;${PROJECT_SOURCE_DIR}/LICENSE;--reference;${PROJECT_SOURCE_DIR}/LICENSE;--runner;$<TARGET_FILE:gabbaboy-runner>;--rom-kind;cgb-acid2"
    -DGBB_EXPECT_CODE=2
    "-DGBB_EXPECT_REGEX=acid2 refused"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
# WR-02: a manifest the harness cannot use is a harness error (exit 3), never "frames differ" (1).
file(WRITE "${PROJECT_BINARY_DIR}/acid2-bad-manifest.json" "{\"kinds\": {}}")
add_test(NAME cgb_acid2_local_bad_manifest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${Python3_EXECUTABLE};-I;${GBB_ACID2_LOCAL};--rom;${PROJECT_SOURCE_DIR}/LICENSE;--reference;${PROJECT_SOURCE_DIR}/LICENSE;--runner;$<TARGET_FILE:gabbaboy-runner>;--rom-kind;cgb-acid2;--manifest;${PROJECT_BINARY_DIR}/acid2-bad-manifest.json"
    -DGBB_EXPECT_CODE=3
    "-DGBB_EXPECT_REGEX=acid2 error: manifest unusable"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
# WR-03: the colour fixture reproduction script must report harness failures as result=error.
if(NOT WIN32)
  find_program(GBB_BASH_CGB_REPRO bash REQUIRED)
  foreach(gbb_repro_case tool_failure missing_pin)
    string(REPLACE "_" "-" gbb_repro_arg "${gbb_repro_case}")
    add_test(NAME cgb_colour_repro_${gbb_repro_case}
      COMMAND ${GBB_BASH_CGB_REPRO} ${PROJECT_SOURCE_DIR}/tests/scripts/test-reproduce-cgb-colour.sh ${gbb_repro_arg})
    set_tests_properties(cgb_colour_repro_${gbb_repro_case} PROPERTIES TIMEOUT 60)
  endforeach()
endif()
# --- Phase 11 plan 11-11 end ---

# --- Phase 11 plan 11-14 begin ---
# D-34: the bit-15 invariant must be able to fail. The mutant core drops the 0x7FFF resolve mask in
# cram_colour, so a guest CRAM word of $FFFF reaches the frame with bit 15 set. The same executable
# stays quiet on seeds that never write such a word, so the failure belongs to the removed mask.
set(GBB_FUZZ_MASK_ANCHOR "return (uint16_t)((cram[at] | (cram[at + 1u] << 8)) & 0x7FFFu);")
string(FIND "${gbb_colour_core_text}" "${GBB_FUZZ_MASK_ANCHOR}" gbb_fuzz_mask_first)
string(FIND "${gbb_colour_core_text}" "${GBB_FUZZ_MASK_ANCHOR}" gbb_fuzz_mask_last REVERSE)
if(gbb_fuzz_mask_first EQUAL -1 OR NOT gbb_fuzz_mask_first EQUAL gbb_fuzz_mask_last)
  message(FATAL_ERROR "fuzz mask mutant: anchor must occur exactly once in src/core/gabbaboy.c")
endif()
string(REPLACE "${GBB_FUZZ_MASK_ANCHOR}" "return (uint16_t)(cram[at] | (cram[at + 1u] << 8));"
  gbb_fuzz_mask_text "${gbb_colour_core_text}")
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_fuzz_mutant_no_mask.c "${gbb_fuzz_mask_text}")
add_library(gabbaboy_core_fuzz_mutant_no_mask STATIC
  ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_fuzz_mutant_no_mask.c)
target_include_directories(gabbaboy_core_fuzz_mutant_no_mask PUBLIC ${PROJECT_SOURCE_DIR}/include)
target_compile_features(gabbaboy_core_fuzz_mutant_no_mask PUBLIC c_std_17)
set_target_properties(gabbaboy_core_fuzz_mutant_no_mask PROPERTIES C_EXTENSIONS OFF)
target_compile_definitions(gabbaboy_core_fuzz_mutant_no_mask PRIVATE
  GBB_BUILD_REVISION="fuzz-mutant-no-mask" GBB_BUILD_QUALIFIED=0)
add_executable(test_fuzz_core_mutant_no_mask test_fuzz_core.c fuzz_core.c)
target_link_libraries(test_fuzz_core_mutant_no_mask PRIVATE gabbaboy_core_fuzz_mutant_no_mask)
target_compile_features(test_fuzz_core_mutant_no_mask PRIVATE c_std_17)
target_compile_definitions(test_fuzz_core_mutant_no_mask PRIVATE GBB_FUZZ_STANDALONE_TEST=1)
set_target_properties(test_fuzz_core_mutant_no_mask PROPERTIES C_EXTENSIONS OFF)
add_test(NAME cgb_fuzz_palette_mutant_no_mask
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_fuzz_core_mutant_no_mask>;cgb_palette"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=pixel above 0x7FFF"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
add_test(NAME cgb_fuzz_palette_mutant_no_mask_control
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_fuzz_core_mutant_no_mask>;cgb_palette_plain"
    -DGBB_EXPECT_CODE=0
    "-DGBB_EXPECT_REGEX=.*"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
# The mutant is meant to trip an invariant and may leave the instance undestroyed on the failing
# path; leak detection is off for this deliberately failing run only (precedent: commit 361256d).
set_tests_properties(cgb_fuzz_palette_mutant_no_mask PROPERTIES ENVIRONMENT "ASAN_OPTIONS=detect_leaks=0")
# D-32: no Phase 11 owner tag may remain in the gate table or the core. The control reverts one row.
add_test(NAME model_gates_no_phase11_rows
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_FILES=${PROJECT_SOURCE_DIR}/docs/model-gates.md;${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c"
    -P ${PROJECT_SOURCE_DIR}/tests/check_no_phase11_rows.cmake)
set_tests_properties(model_gates_no_phase11_rows PROPERTIES
  PASS_REGULAR_EXPRESSION "no-phase11-rows pass" TIMEOUT 30)
file(READ "${PROJECT_SOURCE_DIR}/docs/model-gates.md" gbb_p11_doc)
set(GBB_P11_ROW_ANCHOR "| GATE-50 | UNKNOWN | - | research:14 |")
string(FIND "${gbb_p11_doc}" "${GBB_P11_ROW_ANCHOR}" gbb_p11_first)
string(FIND "${gbb_p11_doc}" "${GBB_P11_ROW_ANCHOR}" gbb_p11_last REVERSE)
if(gbb_p11_first EQUAL -1 OR NOT gbb_p11_first EQUAL gbb_p11_last)
  message(FATAL_ERROR "phase-11 row mutant: '${GBB_P11_ROW_ANCHOR}' must occur exactly once in docs/model-gates.md")
endif()
string(REPLACE "${GBB_P11_ROW_ANCHOR}" "| GATE-50 | UNKNOWN | - | research:11 |" gbb_p11_doc_bad "${gbb_p11_doc}")
file(WRITE "${GBB_MODEL_GATE_DIR}/phase11-row-mutated.md" "${gbb_p11_doc_bad}")
add_test(NAME model_gates_no_phase11_rows_mutated_doc
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_FILES=${GBB_MODEL_GATE_DIR}/phase11-row-mutated.md;-P;${PROJECT_SOURCE_DIR}/tests/check_no_phase11_rows.cmake"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=phase-11-row-open"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
# The CGB colour workload form of measure_core (D-33): it must create the CGB profile and report it.
add_test(NAME cgb_measure_core_cgb_profile
  COMMAND measure_core --no-trace --profile cgb ${PROJECT_SOURCE_DIR}/fixtures/cgb-colour/colour-attr.gb)
set_tests_properties(cgb_measure_core_cgb_profile PROPERTIES
  PASS_REGULAR_EXPRESSION "correctness_digest_fnv1a64=[0-9a-f]+ profile=cgb-cpu-e")
# Negative control: a genuinely unknown profile name is a usage error (exit 2), not a silent DMG run.
# (dmg is a plausible valid name that measure_core merely does not accept; it is not the unknown case.)
add_test(NAME cgb_measure_core_unknown_profile
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:measure_core>;--no-trace;--profile;bogus;${PROJECT_SOURCE_DIR}/fixtures/cgb-colour/colour-attr.gb"
    -DGBB_EXPECT_CODE=2
    "-DGBB_EXPECT_REGEX=usage: measure_core"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
# --- Phase 11 plan 11-14 end ---

# --- Phase 12 plan 12-08 begin ---
# No current double-speed gate may remain owned by research:12.
add_test(NAME model_gates_no_phase12_rows
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_FILES=${PROJECT_SOURCE_DIR}/docs/model-gates.md;${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c"
    -P ${PROJECT_SOURCE_DIR}/tests/check_no_phase12_rows.cmake)
set_tests_properties(model_gates_no_phase12_rows PROPERTIES
  PASS_REGULAR_EXPRESSION "no-phase12-rows pass" TIMEOUT 30)
file(READ "${PROJECT_SOURCE_DIR}/docs/model-gates.md" gbb_p12_doc)
set(GBB_P12_ROW_ANCHOR "| GATE-54 | UNKNOWN | - | research:14 |")
string(FIND "${gbb_p12_doc}" "${GBB_P12_ROW_ANCHOR}" gbb_p12_first)
string(FIND "${gbb_p12_doc}" "${GBB_P12_ROW_ANCHOR}" gbb_p12_last REVERSE)
if(gbb_p12_first EQUAL -1 OR NOT gbb_p12_first EQUAL gbb_p12_last)
  message(FATAL_ERROR "phase-12 row mutant: '${GBB_P12_ROW_ANCHOR}' must occur exactly once in docs/model-gates.md")
endif()
string(REPLACE "${GBB_P12_ROW_ANCHOR}" "| GATE-54 | UNKNOWN | - | research:12 |" gbb_p12_doc_bad "${gbb_p12_doc}")
file(WRITE "${GBB_MODEL_GATE_DIR}/phase12-row-mutated.md" "${gbb_p12_doc_bad}")
add_test(NAME model_gates_no_phase12_rows_mutated_doc
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_FILES=${GBB_MODEL_GATE_DIR}/phase12-row-mutated.md;-P;${PROJECT_SOURCE_DIR}/tests/check_no_phase12_rows.cmake"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=phase-12-row-open"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

# Plan 12-08 recorded the derivation before the first AGE run; plan 12-09 now pins its committed-core window.
file(STRINGS "${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c" GBB_P12_STALL_DEFINE
  REGEX "^#define GBB_SPEED_SWITCH_STALL_T 0x[0-9A-Fa-f]+u$")
list(LENGTH GBB_P12_STALL_DEFINE GBB_P12_STALL_DEFINE_COUNT)
if(NOT GBB_P12_STALL_DEFINE_COUNT EQUAL 1)
  message(FATAL_ERROR "GBB_SPEED_SWITCH_STALL_T must have exactly one hexadecimal definition")
endif()
list(GET GBB_P12_STALL_DEFINE 0 GBB_P12_STALL_DEFINE_LINE)
string(REGEX MATCH "0x[0-9A-Fa-f]+" GBB_P12_STALL_T_HEX "${GBB_P12_STALL_DEFINE_LINE}")
if(NOT GBB_P12_STALL_T_HEX)
  message(FATAL_ERROR "GBB_SPEED_SWITCH_STALL_T could not be parsed from its source definition")
endif()
math(EXPR GBB_P12_STALL_T_VALUE "${GBB_P12_STALL_T_HEX}")
math(EXPR GBB_P12_STALL_HALF_DOTS_DOUBLE "${GBB_P12_STALL_T_VALUE} * 1")
math(EXPR GBB_P12_STALL_HALF_DOTS_NORMAL "${GBB_P12_STALL_T_VALUE} * 2")

set(GBB_SPEED_PROFILE_DOC "${PROJECT_SOURCE_DIR}/docs/cgb-profile.md")
set(GBB_SPEED_PROFILE_SCOPE_START
  "Measured window. On committed core revision")
set(GBB_SPEED_PROFILE_DECLARATIONS
  "${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c;${PROJECT_SOURCE_DIR}/include/gabbaboy/gabbaboy.h")
set(GBB_SPEED_PROFILE_REQUIRED
  "GBB_SPEED_SWITCH_STALL_T"
  "destination speed"
  "minus the 4 T"
  "2050"
  "spsw-div"
  "${GBB_P12_STALL_T_HEX}"
  "${GBB_P12_STALL_HALF_DOTS_DOUBLE}"
  "${GBB_P12_STALL_HALF_DOTS_NORMAL}"
  "age_stall_window")
list(LENGTH GBB_SPEED_PROFILE_REQUIRED GBB_SPEED_PROFILE_PHRASE_COUNT)
add_test(NAME cgb_speed_profile_contract
  COMMAND ${CMAKE_COMMAND}
    -DGBB_DOC=${GBB_SPEED_PROFILE_DOC}
    "-DGBB_DECLARATIONS=${GBB_SPEED_PROFILE_DECLARATIONS}"
    "-DGBB_REQUIRED=${GBB_SPEED_PROFILE_REQUIRED}"
    "-DGBB_SCOPE_START=${GBB_SPEED_PROFILE_SCOPE_START}"
    -P ${GBB_DOC_CONTRACT_SCRIPT})
set_tests_properties(cgb_speed_profile_contract PROPERTIES
  PASS_REGULAR_EXPRESSION "doc-contract pass identifiers=[1-9][0-9]* phrases=${GBB_SPEED_PROFILE_PHRASE_COUNT}[^0-9]")

# Negative control: the same guide and declarations reject an extra absent phrase.
set(GBB_SPEED_PROFILE_MISSING_PHRASE "committed-core AGE window recorded")
string(REPLACE ";" "\\;" GBB_SPEED_PROFILE_DECLARATIONS_ESCAPED "${GBB_SPEED_PROFILE_DECLARATIONS}")
add_test(NAME cgb_speed_profile_contract_missing_selftest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_DOC=${GBB_SPEED_PROFILE_DOC};-DGBB_DECLARATIONS=${GBB_SPEED_PROFILE_DECLARATIONS_ESCAPED};-DGBB_REQUIRED=${GBB_SPEED_PROFILE_MISSING_PHRASE};-DGBB_SCOPE_START=${GBB_SPEED_PROFILE_SCOPE_START};-P;${GBB_DOC_CONTRACT_SCRIPT}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=doc-contract-missing: ${GBB_SPEED_PROFILE_MISSING_PHRASE}"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
# --- Phase 12 plan 12-08 end ---

# --- Phase 12 plan 12-01 begin ---
# Pre-change CGB speed identities; this source includes the core and must not link it.
add_executable(test_cgb_speed_internal test_cgb_speed_internal.c)
target_include_directories(test_cgb_speed_internal PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_cgb_speed_internal PRIVATE c_std_17)
set_target_properties(test_cgb_speed_internal PROPERTIES C_EXTENSIONS OFF)
add_test(NAME cgb_speed_identity_pin
  COMMAND test_cgb_speed_internal cgb_speed_identity_pin ${PROJECT_SOURCE_DIR}/fixtures)
set_tests_properties(cgb_speed_identity_pin PROPERTIES TIMEOUT 60)
add_test(NAME cgb_speed_identity_pin_flipped
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_speed_internal>;cgb_speed_identity_pin;${PROJECT_SOURCE_DIR}/fixtures;--flip"
    -DGBB_EXPECT_CODE=1
    -DGBB_EXPECT_REGEX=observed
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(cgb_speed_identity_pin_flipped PROPERTIES
  ENVIRONMENT "ASAN_OPTIONS=detect_leaks=0" TIMEOUT 60)
add_test(NAME cgb_speed_internal_harness_alive
  COMMAND test_cgb_speed_internal cgb_speed_internal_harness_alive)
add_test(NAME cgb_speed_tracer_switch
  COMMAND test_cgb_speed_internal cgb_speed_tracer_switch)
set_tests_properties(cgb_speed_tracer_switch PROPERTIES TIMEOUT 60)
# --- Phase 12 plan 12-01 end ---

# --- Phase 12 plan 12-03 begin ---
include(${PROJECT_SOURCE_DIR}/cmake/P12Mutants.cmake)
set(GBB_P12_MUTANT_CORE ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_p12_mutants.c)
gbb_p12_make_mutant_core(${GBB_P12_MUTANT_CORE} 0)
add_executable(test_cgb_speed_internal_p12 test_cgb_speed_internal.c)
target_include_directories(test_cgb_speed_internal_p12 PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_cgb_speed_internal_p12 PRIVATE c_std_17)
target_compile_definitions(test_cgb_speed_internal_p12 PRIVATE
  "GBB_P12_CORE_SOURCE=\"${GBB_P12_MUTANT_CORE}\""
  GBB_P12_MUTANT_BUILD=1 GBB_BUILD_REVISION="p12-mutant" GBB_BUILD_QUALIFIED=0)
set_target_properties(test_cgb_speed_internal_p12 PROPERTIES C_EXTENSIONS OFF)
# --- Phase 12 plan 12-17 begin ---
add_test(NAME cgb_speed_xfail_pause_ppu_output
  COMMAND test_cgb_speed_internal_p12 cgb_speed_xfail_pause_ppu_output)
set_tests_properties(cgb_speed_xfail_pause_ppu_output PROPERTIES TIMEOUT 60)
gbb_p12_mutant_test(test_cgb_speed_internal_p12 7 xfail_ppu
  cgb_speed_xfail_pause_ppu_output "frame differs")
add_test(NAME cgb_speed_xfail_dma_restart
  COMMAND test_cgb_speed_internal_p12 cgb_speed_xfail_dma_restart)
set_tests_properties(cgb_speed_xfail_dma_restart PROPERTIES TIMEOUT 60)
gbb_p12_mutant_test(test_cgb_speed_internal_p12 14 xfail_dma_restart
  cgb_speed_xfail_dma_restart "observed dma")
add_test(NAME cgb_speed_xfail_hdma_fails_closed
  COMMAND test_cgb_speed_internal_p12 cgb_speed_xfail_hdma_fails_closed)
set_tests_properties(cgb_speed_xfail_hdma_fails_closed PROPERTIES TIMEOUT 60)
add_test(NAME cgb_speed_xfail_hdma_fails_closed_negative
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_speed_internal_p12>;cgb_speed_xfail_hdma_fails_closed;--write-ff54"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=hdma-ff54-targeted-negative"
    -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
set_tests_properties(cgb_speed_xfail_hdma_fails_closed_negative PROPERTIES TIMEOUT 60)
add_test(NAME cgb_speed_xfail_stop_oam_unchanged
  COMMAND test_cgb_speed_internal_p12 cgb_speed_xfail_stop_oam_unchanged)
set_tests_properties(cgb_speed_xfail_stop_oam_unchanged PROPERTIES TIMEOUT 60)
add_test(NAME cgb_speed_xfail_stop_oam_unchanged_negative
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_speed_internal_p12>;cgb_speed_xfail_stop_oam_unchanged;--poke-oam"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=OAM changed"
    -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
set_tests_properties(cgb_speed_xfail_stop_oam_unchanged_negative PROPERTIES TIMEOUT 60)
set(GBB_SPEED_DISPOSITIONS_RECORD
  "${PROJECT_SOURCE_DIR}/tests/external/cgb-speed-dispositions.json")
set(GBB_SPEED_DISPOSITIONS_VERIFIER
  "${PROJECT_SOURCE_DIR}/tests/scripts/verify-cgb-speed-dispositions.py")
add_test(NAME cgb_speed_dispositions
  COMMAND "${Python3_EXECUTABLE}" -I "${GBB_SPEED_DISPOSITIONS_VERIFIER}")
set_tests_properties(cgb_speed_dispositions PROPERTIES
  PASS_REGULAR_EXPRESSION "cgb-speed-dispositions pass rows=" TIMEOUT 30)
file(READ "${GBB_SPEED_DISPOSITIONS_RECORD}" gbb_speed_dispositions_record)
set(gbb_speed_pinned_anchor "\"pinned_by\": \"cgb_speed_xfail_pause_ppu_output\"")
string(FIND "${gbb_speed_dispositions_record}" "${gbb_speed_pinned_anchor}" gbb_speed_pin_at)
string(FIND "${gbb_speed_dispositions_record}" "${gbb_speed_pinned_anchor}" gbb_speed_pin_last REVERSE)
if(gbb_speed_pin_at EQUAL -1 OR NOT gbb_speed_pin_at EQUAL gbb_speed_pin_last)
  message(FATAL_ERROR "speed disposition pinned_by mutation anchor must occur exactly once")
endif()
string(REPLACE "${gbb_speed_pinned_anchor}"
  "\"pinned_by\": \"cgb_speed_no_such_test\""
  gbb_speed_dispositions_missing_pin "${gbb_speed_dispositions_record}")
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/cgb-speed-dispositions")
file(WRITE "${PROJECT_BINARY_DIR}/cgb-speed-dispositions/pinned-by-missing.json"
  "${gbb_speed_dispositions_missing_pin}")
add_test(NAME cgb_speed_dispositions_pinned_by_missing
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${Python3_EXECUTABLE};-I;${GBB_SPEED_DISPOSITIONS_VERIFIER};--record;${PROJECT_BINARY_DIR}/cgb-speed-dispositions/pinned-by-missing.json"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=disposition-mismatch pinned_by"
    -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
set_tests_properties(cgb_speed_dispositions_pinned_by_missing PROPERTIES TIMEOUT 30)
# Negative control: changing one documented reason in a configure-time copy must be rejected.
set(gbb_speed_reason_anchor "\"reason\": \"expected-failure:speed-switch-pause-ppu-output\"")
string(FIND "${gbb_speed_dispositions_record}" "${gbb_speed_reason_anchor}" gbb_speed_reason_at)
string(FIND "${gbb_speed_dispositions_record}" "${gbb_speed_reason_anchor}" gbb_speed_reason_last REVERSE)
if(gbb_speed_reason_at EQUAL -1 OR NOT gbb_speed_reason_at EQUAL gbb_speed_reason_last)
  message(FATAL_ERROR "speed disposition reason mutation anchor must occur exactly once")
endif()
string(REPLACE "${gbb_speed_reason_anchor}"
  "\"reason\": \"expected-failure:wrong-speed-switch-pause-reason\""
  gbb_speed_dispositions_mutated "${gbb_speed_dispositions_record}")
file(WRITE "${PROJECT_BINARY_DIR}/cgb-speed-dispositions/reason-mutated.json"
  "${gbb_speed_dispositions_mutated}")
add_test(NAME cgb_speed_dispositions_mutated
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${Python3_EXECUTABLE};-I;${GBB_SPEED_DISPOSITIONS_VERIFIER};--record;${PROJECT_BINARY_DIR}/cgb-speed-dispositions/reason-mutated.json"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=disposition-mismatch"
    -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
set_tests_properties(cgb_speed_dispositions_mutated PROPERTIES TIMEOUT 30)
# Negative control: keep the precise independent thirteen-case row set closed to extras.
set(gbb_speed_case_anchor "\"case\": \"spsw-div-cgbBCE\"")
string(FIND "${gbb_speed_dispositions_record}" "${gbb_speed_case_anchor}" gbb_speed_case_at)
string(FIND "${gbb_speed_dispositions_record}" "${gbb_speed_case_anchor}" gbb_speed_case_last REVERSE)
if(gbb_speed_case_at EQUAL -1 OR NOT gbb_speed_case_at EQUAL gbb_speed_case_last)
  message(FATAL_ERROR "speed disposition AGE case mutation anchor must occur exactly once")
endif()
string(REPLACE "${gbb_speed_case_anchor}"
  "\"case\": \"spsw-div-cgbBCE-extra\""
  gbb_speed_dispositions_extra_age_case "${gbb_speed_dispositions_record}")
file(WRITE "${PROJECT_BINARY_DIR}/cgb-speed-dispositions/age-case-set-mutated.json"
  "${gbb_speed_dispositions_extra_age_case}")
add_test(NAME cgb_speed_dispositions_age_case_set_mutated
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${Python3_EXECUTABLE};-I;${GBB_SPEED_DISPOSITIONS_VERIFIER};--record;${PROJECT_BINARY_DIR}/cgb-speed-dispositions/age-case-set-mutated.json"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=disposition-mismatch age-case-set"
    -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
set_tests_properties(cgb_speed_dispositions_age_case_set_mutated PROPERTIES TIMEOUT 30)
# --- Phase 12 plan 12-17 end ---
gbb_p12_mutant_test(test_cgb_speed_internal_p12 5 stall_sets_stopped
  cgb_speed_tracer_switch "stopped|GBB_STOP_STOPPED")
add_test(NAME cgb_speed_stop_cases COMMAND test_cgb_speed_internal_p12 cgb_speed_stop_cases)
set_tests_properties(cgb_speed_stop_cases PROPERTIES TIMEOUT 60)
gbb_p12_mutant_test(test_cgb_speed_internal_p12 34 stop_falls_into_rlca
  cgb_speed_stop_cases "machine->pc == 0x101u")
add_test(NAME cgb_speed_stop_guest_timer_irq COMMAND test_cgb_speed_internal_p12 cgb_speed_stop_guest_timer_irq)
set_tests_properties(cgb_speed_stop_guest_timer_irq PROPERTIES TIMEOUT 60)
gbb_p12_mutant_test(test_cgb_speed_internal_p12 20 guest_timer_pending_ignored
  cgb_speed_stop_guest_timer_irq "cpu_stall_kind|m->wram")
foreach(stop_case IN ITEMS cgb_speed_stop_operand cgb_speed_stop_prefetch_ff04
    cgb_speed_stop_cost cgb_speed_dmg_unarmed_unchanged cgb_speed_key1_readback
    cgb_speed_key0_no_switch)
  add_test(NAME ${stop_case} COMMAND test_cgb_speed_internal_p12 ${stop_case})
  set_tests_properties(${stop_case} PROPERTIES TIMEOUT 60)
endforeach()
add_test(NAME cgb_speed_stop_prefetch_ff04_negative
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_speed_internal_p12>;cgb_speed_stop_prefetch_ff04;--ff04-wrong-byte"
    -DGBB_EXPECT_CODE=1 -DGBB_EXPECT_REGEX=double_speed
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(cgb_speed_stop_prefetch_ff04_negative PROPERTIES TIMEOUT 60)
gbb_p12_mutant_test(test_cgb_speed_internal_p12 20 pending_ignored
  cgb_speed_stop_cases "stop_case")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 27 divider_reset_omitted
  cgb_speed_stop_cases "divider_counter")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 8 speed_gate_removed
  cgb_speed_dmg_unarmed_unchanged "run.reason == GBB_STOP_STOPPED")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 10 key1_arm_not_cleared
  cgb_speed_key1_readback "0xFF4Du")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 19 held_predicate_ignored
  cgb_speed_stop_cases "stop_case")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 29 switch_cost_one_m
  cgb_speed_stop_cost "GBB_STOP_SWITCH_COST_HALF_DOTS")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 30 dmg_stop_apu_edge
  cgb_speed_dmg_unarmed_unchanged "apu_sequencer_step == 3u")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 32 key0_toggles_speed
  cgb_speed_key0_no_switch "m->double_speed == 0u")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 33 operand_changes_switch
  cgb_speed_stop_operand "a->time_half_dots == b->time_half_dots")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 7 devices_frozen
  cgb_speed_tracer_switch "divider_counter != 0u")
add_test(NAME cgb_speed_cpu_ticks COMMAND test_cgb_speed_internal_p12 cgb_speed_cpu_ticks)
set_tests_properties(cgb_speed_cpu_ticks PROPERTIES TIMEOUT 60)
add_test(NAME cgb_speed_timer_scaling COMMAND test_cgb_speed_internal_p12 cgb_speed_timer_scaling)
set_tests_properties(cgb_speed_timer_scaling PROPERTIES TIMEOUT 60)
add_test(NAME cgb_speed_serial_scaling COMMAND test_cgb_speed_internal_p12 cgb_speed_serial_scaling)
add_test(NAME cgb_speed_dma_scaling COMMAND test_cgb_speed_internal_p12 cgb_speed_dma_scaling)
add_test(NAME cgb_speed_apu_tap COMMAND test_cgb_speed_internal_p12 cgb_speed_apu_tap)
add_test(NAME cgb_speed_remainder_across_switch COMMAND test_cgb_speed_internal_p12 cgb_speed_remainder_across_switch)
add_test(NAME cgb_speed_ppu_apu_rtc_unscaled
  COMMAND test_cgb_speed_internal_p12 cgb_speed_ppu_apu_rtc_unscaled)
set_tests_properties(cgb_speed_serial_scaling cgb_speed_dma_scaling cgb_speed_apu_tap
  cgb_speed_remainder_across_switch cgb_speed_ppu_apu_rtc_unscaled PROPERTIES TIMEOUT 60)
gbb_p12_mutant_test(test_cgb_speed_internal_p12 2 serial_unscaled
  cgb_speed_serial_scaling "machine->serial_active")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 4 apu_tap_unscaled
  cgb_speed_apu_tap "volume == 9u|apu_sequencer_step == 4u")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 11 remainder_dropped_at_switch
  cgb_speed_remainder_across_switch "serial_edge_remaining >|dma_phase >|timer_reload_remaining ==")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 14 dma_unscaled
  cgb_speed_dma_scaling "!machine->dma_active")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 15 timer_reload_half_dot_units_switch
  cgb_speed_remainder_across_switch "timer_reload_remaining == 4u")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 1 ppu_scaled
  cgb_speed_ppu_apu_rtc_unscaled "machine->ly == 1u|frame_generation ==")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 12 rtc_scaled
  cgb_speed_ppu_apu_rtc_unscaled "rtc_l")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 17 apu_channels_scaled
  cgb_speed_ppu_apu_rtc_unscaled "timer == 90u")

add_test(NAME cgb_speed_domains_scan
  COMMAND ${Python3_EXECUTABLE} -I
    ${PROJECT_SOURCE_DIR}/tests/scripts/verify-speed-domains.py
    ${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c)
set_tests_properties(cgb_speed_domains_scan PROPERTIES
  PASS_REGULAR_EXPRESSION "speed-domains pass functions=[1-9]" TIMEOUT 30)
set(GBB_P12_SPEED_DOMAIN_MUTANT_CORE "${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_p12_speed_domain_mutant.c")
file(READ "${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c" gbb_p12_speed_domain_text)
set(gbb_p12_speed_domain_anchor "static void ppu_advance_dot(gbb_instance *m) {")
string(FIND "${gbb_p12_speed_domain_text}" "${gbb_p12_speed_domain_anchor}" gbb_p12_speed_domain_first)
string(FIND "${gbb_p12_speed_domain_text}" "${gbb_p12_speed_domain_anchor}" gbb_p12_speed_domain_last REVERSE)
if(gbb_p12_speed_domain_first EQUAL -1 OR NOT gbb_p12_speed_domain_first EQUAL gbb_p12_speed_domain_last)
  message(FATAL_ERROR "speed-domain negative control needs one ppu_ function anchor")
endif()
string(REPLACE "${gbb_p12_speed_domain_anchor}"
  "${gbb_p12_speed_domain_anchor}\n    (void)m->double_speed;"
  gbb_p12_speed_domain_text "${gbb_p12_speed_domain_text}")
file(WRITE "${GBB_P12_SPEED_DOMAIN_MUTANT_CORE}" "${gbb_p12_speed_domain_text}")
add_test(NAME cgb_speed_domains_scan_mutated
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${Python3_EXECUTABLE};-I;${PROJECT_SOURCE_DIR}/tests/scripts/verify-speed-domains.py;${GBB_P12_SPEED_DOMAIN_MUTANT_CORE}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=speed-domain-violation ppu_advance_dot"
    -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
set_tests_properties(cgb_speed_domains_scan_mutated PROPERTIES TIMEOUT 30)
gbb_p12_mutant_test(test_cgb_speed_internal_p12 3 timer_unscaled
  cgb_speed_timer_scaling "tima_delta|div_delta")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 15 timer_reload_half_dot_units
  cgb_speed_timer_scaling "timer_reload_remaining == 4u")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 18 cost_unscaled
  cgb_speed_cpu_ticks "d.ticks / 2u")
add_test(NAME cgb_speed_reset_double_speed COMMAND test_cgb_speed_internal_p12 cgb_speed_reset_double_speed)
add_test(NAME cgb_speed_reset_stall COMMAND test_cgb_speed_internal_p12 cgb_speed_reset_stall)
add_test(NAME cgb_speed_reset_key1 COMMAND test_cgb_speed_internal_p12 cgb_speed_reset_key1)
set_tests_properties(cgb_speed_reset_double_speed cgb_speed_reset_stall cgb_speed_reset_key1 PROPERTIES TIMEOUT 60)
gbb_p12_mutant_test(test_cgb_speed_internal_p12 24 reset_retains_double_speed
  cgb_speed_reset_double_speed "double_speed == 0u")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 25 reset_retains_stall
  cgb_speed_reset_stall "cpu_stall_kind == GBB_STALL_NONE")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 26 reset_retains_key1_arm
  cgb_speed_reset_key1 "key1_armed == 0u")

# Mutant core build 1 of the D-25 ceiling of 6. Duplicate one anchor in a build-tree copy;
# script-mode generation must reject it rather than silently producing a partial mutant.
set(GBB_P12_ANCHOR_GUARD_CORE "${CMAKE_CURRENT_BINARY_DIR}/p12-anchor-guard-core.c")
file(READ "${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c" gbb_p12_anchor_guard_text)
set(gbb_p12_anchor_guard_line "instance->cpu_stall_kind = GBB_STALL_SPEED_SWITCH; /* P12-M5 */")
string(FIND "${gbb_p12_anchor_guard_text}" "${gbb_p12_anchor_guard_line}" gbb_p12_anchor_guard_pos)
if(gbb_p12_anchor_guard_pos EQUAL -1)
  message(FATAL_ERROR "missing P12-M5 anchor for negative control")
endif()
string(REPLACE "${gbb_p12_anchor_guard_line}"
  "${gbb_p12_anchor_guard_line}\n            ${gbb_p12_anchor_guard_line}"
  gbb_p12_anchor_guard_text "${gbb_p12_anchor_guard_text}")
file(WRITE "${GBB_P12_ANCHOR_GUARD_CORE}" "${gbb_p12_anchor_guard_text}")
add_test(NAME cgb_speed_mutant_anchor_guard
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_P12_SCRIPT_CORE=${GBB_P12_ANCHOR_GUARD_CORE};-DGBB_P12_SCRIPT_OUT=${CMAKE_CURRENT_BINARY_DIR}/anchor-guard.c;-P;${PROJECT_SOURCE_DIR}/cmake/P12Mutants.cmake"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=must occur exactly once"
    -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
set_tests_properties(cgb_speed_mutant_anchor_guard PROPERTIES TIMEOUT 30)

# Static assert mutant is mutant core build 2 of at most 6. The offset is additive so it
# remains invalid when the M-aligned plan 12-09 stall constant is re-pinned.
set(GBB_P12_STALL_ASSERT_SOURCE "${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_p12_stall_assert.c")
file(READ "${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c" gbb_p12_stall_assert_text)
set(gbb_p12_stall_assert_anchor "#define GBB_SPEED_SWITCH_STALL_T ")
string(FIND "${gbb_p12_stall_assert_text}" "${gbb_p12_stall_assert_anchor}" gbb_p12_stall_assert_first)
string(FIND "${gbb_p12_stall_assert_text}" "${gbb_p12_stall_assert_anchor}" gbb_p12_stall_assert_last REVERSE)
if(gbb_p12_stall_assert_first EQUAL -1 OR NOT gbb_p12_stall_assert_first EQUAL gbb_p12_stall_assert_last)
  message(FATAL_ERROR "P12 stall static assert anchor must occur exactly once")
endif()
string(REPLACE "${gbb_p12_stall_assert_anchor}" "#define GBB_SPEED_SWITCH_STALL_T 2u + "
  gbb_p12_stall_assert_text "${gbb_p12_stall_assert_text}")
file(WRITE "${GBB_P12_STALL_ASSERT_SOURCE}" "${gbb_p12_stall_assert_text}")
add_library(gabbaboy_core_p12_stall_assert_mutant STATIC EXCLUDE_FROM_ALL
  "${GBB_P12_STALL_ASSERT_SOURCE}")
target_include_directories(gabbaboy_core_p12_stall_assert_mutant PUBLIC "${PROJECT_SOURCE_DIR}/include")
target_compile_features(gabbaboy_core_p12_stall_assert_mutant PUBLIC c_std_17)
set_target_properties(gabbaboy_core_p12_stall_assert_mutant PROPERTIES C_EXTENSIONS OFF)
target_compile_definitions(gabbaboy_core_p12_stall_assert_mutant PRIVATE
  GBB_BUILD_REVISION="p12-stall-assert-mutant" GBB_BUILD_QUALIFIED=0)
add_test(NAME cgb_speed_stall_static_assert_mutant
  COMMAND ${CMAKE_COMMAND} --build ${PROJECT_BINARY_DIR} --target gabbaboy_core_p12_stall_assert_mutant)
set_tests_properties(cgb_speed_stall_static_assert_mutant PROPERTIES
  PASS_REGULAR_EXPRESSION "half-dot timeline:" TIMEOUT 180)
# --- Phase 12 plan 12-03 end ---

# --- Phase 12 plan 12-07 begin ---
add_test(NAME cgb_speed_wake_ime_on
  COMMAND test_cgb_speed_internal_p12 cgb_speed_wake_ime_on)
set_tests_properties(cgb_speed_wake_ime_on PROPERTIES TIMEOUT 60)
foreach(wake_case IN ITEMS cgb_speed_wake_ime_off cgb_speed_ei_stop
    cgb_speed_wake_m_boundary cgb_speed_realign)
  add_test(NAME ${wake_case} COMMAND test_cgb_speed_internal_p12 ${wake_case})
  set_tests_properties(${wake_case} PROPERTIES TIMEOUT 60)
endforeach()
foreach(stall_case IN ITEMS cgb_speed_stall_length cgb_speed_budget_semantics
    cgb_speed_never_stopped cgb_speed_stall_devices_advance cgb_speed_headroom)
  add_test(NAME ${stall_case} COMMAND test_cgb_speed_internal_p12 ${stall_case})
  set_tests_properties(${stall_case} PROPERTIES TIMEOUT 60)
endforeach()
gbb_p12_mutant_test(test_cgb_speed_internal_p12 13 wake_ime_on_ignored
  cgb_speed_wake_ime_on "run.reason == GBB_STOP_TRACE_FULL|run.trace_count == 1u|stall_end >= machine->timer_reloaded_at")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 16 wake_ime_on_per_call
  cgb_speed_wake_ime_on "run.reason == GBB_STOP_TRACE_FULL|run.trace_count == 1u|stall_end >= machine->timer_reloaded_at")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 13 wake_ime_off_ignored
  cgb_speed_wake_ime_off "timer_reloaded_at > stall_start|machine->b == 1u")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 16 wake_sampled_per_call
  cgb_speed_wake_m_boundary "machine->b == 1u|machine->cpu_stall_kind")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 23 realignment_omitted
  cgb_speed_realign "GBB_STALL_SWITCH_REALIGN|cpu_stall_half_dots == 4u")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 34 ei_delay_not_retired
  cgb_speed_ei_stop "machine->ime == 1")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 6 stall_one_m_long
  cgb_speed_stall_length "expected_stall|trace\[0\]\.time_half_dots|cpu_stall_kind")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 21 stall_one_m_short
  cgb_speed_stall_length "expected_stall|trace\[0\]\.time_half_dots|cpu_stall_kind")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 28 stall_one_half_dot_long
  cgb_speed_stall_length "expected_stall|trace\[0\]\.time_half_dots|cpu_stall_kind")
add_test(NAME cgb_speed_m28_normal_unchanged
  COMMAND test_cgb_speed_internal_p12 cgb_speed_m28_normal_unchanged --mutants 0x10000000)
set_tests_properties(cgb_speed_m28_normal_unchanged PROPERTIES TIMEOUT 60)
add_test(NAME cgb_speed_m28_normal_unchanged_control
  COMMAND test_cgb_speed_internal_p12 cgb_speed_m28_normal_unchanged --mutants 0)
set_tests_properties(cgb_speed_m28_normal_unchanged_control PROPERTIES TIMEOUT 60)
gbb_p12_mutant_test(test_cgb_speed_internal_p12 9 stall_budget_unbounded
  cgb_speed_budget_semantics "run\.consumed_half_dots == expected_consumed|run\.consumed_half_dots <= budget")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 22 switch_headroom_omitted
  cgb_speed_headroom "GBB_STOP_INVALID_STATE|memcmp")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 5 stall_sets_stopped_never
  cgb_speed_never_stopped "GBB_STOP_STOPPED|machine->stopped")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 7 devices_frozen_never
  cgb_speed_never_stopped "divider_counter != divider_before")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 5 stall_sets_stopped_devices
  cgb_speed_stall_devices_advance "GBB_STOP_BUDGET")
gbb_p12_mutant_test(test_cgb_speed_internal_p12 7 devices_frozen_devices
  cgb_speed_stall_devices_advance "machine->ly >= 143u|machine->tima != initial_tima")
add_test(NAME cgb_speed_mutant_m31_stall_offset_noop
  COMMAND test_cgb_speed_internal_p12 cgb_speed_stall_length --mutants 0x80000000)
set_tests_properties(cgb_speed_mutant_m31_stall_offset_noop PROPERTIES TIMEOUT 60)
# --- Phase 12 plan 12-07 end ---

# --- Phase 12 plan 12-09 begin ---
add_executable(test_age test_age.c)
target_include_directories(test_age PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_link_libraries(test_age PRIVATE GabbaBoy::core gabbaboy_accept)
target_compile_features(test_age PRIVATE c_std_17)
set_target_properties(test_age PROPERTIES C_EXTENSIONS OFF)

set(GBB_AGE_MANIFEST "${PROJECT_SOURCE_DIR}/fixtures/age/manifest.json")
file(READ "${GBB_AGE_MANIFEST}" GBB_AGE_MANIFEST_JSON)
include("${PROJECT_SOURCE_DIR}/cmake/AgeFixtureProtocol.cmake")
gbb_validate_age_fixture_protocol("${GBB_AGE_MANIFEST_JSON}"
  GBB_AGE_ROW_FIXTURE_INDICES GBB_AGE_PENDING_IMAGE_FIXTURE_INDICES)
string(JSON GBB_AGE_FIXTURE_COUNT LENGTH "${GBB_AGE_MANIFEST_JSON}" fixtures)
math(EXPR GBB_AGE_FIXTURE_LAST "${GBB_AGE_FIXTURE_COUNT} - 1")
message(STATUS "AGE fixture protocol pass row-oracle=13 image-pending=6")
set(GBB_AGE_SPSW_FOUND OFF)
foreach(GBB_AGE_FIXTURE_INDEX IN LISTS GBB_AGE_ROW_FIXTURE_INDICES)
  string(JSON GBB_AGE_FIXTURE_FILE GET "${GBB_AGE_MANIFEST_JSON}" fixtures ${GBB_AGE_FIXTURE_INDEX} file)
  if("${GBB_AGE_FIXTURE_FILE}" STREQUAL "spsw-div-cgbBCE.gb")
    set(GBB_AGE_SPSW_FOUND ON)
    string(JSON GBB_AGE_SPSW_RESULTS GET "${GBB_AGE_MANIFEST_JSON}" fixtures ${GBB_AGE_FIXTURE_INDEX} test_results_address)
    string(JSON GBB_AGE_SPSW_EXPECTED GET "${GBB_AGE_MANIFEST_JSON}" fixtures ${GBB_AGE_FIXTURE_INDEX} expected_address)
    string(JSON GBB_AGE_SPSW_ROWS GET "${GBB_AGE_MANIFEST_JSON}" fixtures ${GBB_AGE_FIXTURE_INDEX} rows)
    string(JSON GBB_AGE_SPSW_BUDGET GET "${GBB_AGE_MANIFEST_JSON}" fixtures ${GBB_AGE_FIXTURE_INDEX} budget_half_dots)
  endif()
endforeach()
if(NOT GBB_AGE_SPSW_FOUND OR NOT DEFINED GBB_AGE_SPSW_BUDGET)
  message(FATAL_ERROR "AGE manifest must define spsw-div-cgbBCE and its measured budget")
endif()
string(REPLACE "$" "0x" GBB_AGE_SPSW_RESULTS_HEX "${GBB_AGE_SPSW_RESULTS}")
string(REPLACE "$" "0x" GBB_AGE_SPSW_EXPECTED_HEX "${GBB_AGE_SPSW_EXPECTED}")
set(GBB_AGE_SPSW_ROM "${PROJECT_SOURCE_DIR}/fixtures/age/spsw-div-cgbBCE.gb")
set(GBB_AGE_TIMEOUT_CONTROL_TIMEOUT 30)
set(GBB_AGE_STALL_WINDOW_TIMEOUT 240)
# Negative control: one half-dot cannot reach an executed verdict and must report timeout distinctly.
add_test(NAME age_spsw_div_cgbBCE_timeout
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_age>;${GBB_AGE_SPSW_ROM};${GBB_AGE_SPSW_RESULTS_HEX};${GBB_AGE_SPSW_EXPECTED_HEX};${GBB_AGE_SPSW_ROWS};1;--verdict"
    -DGBB_EXPECT_CODE=3
    "-DGBB_EXPECT_REGEX=age-timeout half_dots="
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(age_spsw_div_cgbBCE_timeout PROPERTIES TIMEOUT ${GBB_AGE_TIMEOUT_CONTROL_TIMEOUT})

# Mutant core build 3 of at most 6; the later AGE disposition and sensitivity plans reuse this library.
set(GBB_P12_PUBLIC_MUTANT_CORE "${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_p12_public_mutants.c")
gbb_p12_make_mutant_core("${GBB_P12_PUBLIC_MUTANT_CORE}" 0)
add_library(gabbaboy_core_p12_mutants STATIC "${GBB_P12_PUBLIC_MUTANT_CORE}")
target_include_directories(gabbaboy_core_p12_mutants
  PUBLIC "${PROJECT_SOURCE_DIR}/include"
  PRIVATE "${PROJECT_SOURCE_DIR}/src/core")
target_compile_features(gabbaboy_core_p12_mutants PUBLIC c_std_17)
set_target_properties(gabbaboy_core_p12_mutants PROPERTIES C_EXTENSIONS OFF)
target_compile_definitions(gabbaboy_core_p12_mutants PRIVATE
  GBB_BUILD_REVISION="p12-public-mutant-3" GBB_BUILD_QUALIFIED=0)

add_executable(test_age_p12 test_age.c)
target_include_directories(test_age_p12 PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_features(test_age_p12 PRIVATE c_std_17)
target_compile_definitions(test_age_p12 PRIVATE GBB_AGE_P12=1)
target_link_libraries(test_age_p12 PRIVATE gabbaboy_core_p12_mutants gabbaboy_accept)
set_target_properties(test_age_p12 PROPERTIES C_EXTENSIONS OFF)

# The measured committed-core bounds drive the four-point boundary assertion below.
set(GBB_P12_AGE_STALL_WINDOW "0x20004;0x20007")
list(GET GBB_P12_AGE_STALL_WINDOW 0 GBB_P12_AGE_STALL_WINDOW_LO)
list(GET GBB_P12_AGE_STALL_WINDOW 1 GBB_P12_AGE_STALL_WINDOW_HI)
add_test(NAME age_stall_window
  COMMAND test_age_p12 "${GBB_AGE_SPSW_ROM}" "${GBB_AGE_SPSW_RESULTS_HEX}"
    "${GBB_AGE_SPSW_EXPECTED_HEX}" "${GBB_AGE_SPSW_ROWS}"
    "${GBB_AGE_SPSW_BUDGET}" --stall-window "${GBB_P12_STALL_T_HEX}"
    "${GBB_P12_AGE_STALL_WINDOW_LO}" "${GBB_P12_AGE_STALL_WINDOW_HI}")
set_tests_properties(age_stall_window PROPERTIES
  PASS_REGULAR_EXPRESSION "age-stall-window pass window=\\[${GBB_P12_AGE_STALL_WINDOW_LO},${GBB_P12_AGE_STALL_WINDOW_HI}\\] constant=${GBB_P12_STALL_T_HEX}"
  TIMEOUT ${GBB_AGE_STALL_WINDOW_TIMEOUT})
# --- Phase 12 plan 12-09 end ---

# --- Phase 12 plan 12-16 begin ---
# The disposition rows pin committed-core results; the manifest supplies bounded run layouts.
set(GBB_AGE_DISPOSITIONS_FILE "${PROJECT_SOURCE_DIR}/tests/external/cgb-speed-dispositions.json")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
  "${GBB_AGE_MANIFEST}" "${GBB_AGE_DISPOSITIONS_FILE}")
file(READ "${GBB_AGE_DISPOSITIONS_FILE}" GBB_AGE_DISPOSITIONS_JSON)
string(JSON GBB_AGE_DISPOSITIONS_SCHEMA GET "${GBB_AGE_DISPOSITIONS_JSON}" schema)
if(NOT GBB_AGE_DISPOSITIONS_SCHEMA STREQUAL "gabbaboy-external-dispositions-v1")
  message(FATAL_ERROR "AGE dispositions have an unsupported schema")
endif()
string(JSON GBB_AGE_DISPOSITION_SUITE_COUNT LENGTH "${GBB_AGE_DISPOSITIONS_JSON}" suites)
set(GBB_AGE_DISPOSITION_SUITE_FOUND OFF)
foreach(GBB_AGE_DISPOSITION_SUITE_INDEX RANGE 0 ${GBB_AGE_DISPOSITION_SUITE_COUNT})
  if(GBB_AGE_DISPOSITION_SUITE_INDEX LESS GBB_AGE_DISPOSITION_SUITE_COUNT)
    string(JSON GBB_AGE_DISPOSITION_SUITE_NAME GET "${GBB_AGE_DISPOSITIONS_JSON}"
      suites ${GBB_AGE_DISPOSITION_SUITE_INDEX} suite)
    if(GBB_AGE_DISPOSITION_SUITE_NAME STREQUAL "age-test-roms")
      set(GBB_AGE_DISPOSITION_SUITE_FOUND ON)
      string(JSON GBB_AGE_DISPOSITION_ROW_COUNT LENGTH "${GBB_AGE_DISPOSITIONS_JSON}"
        suites ${GBB_AGE_DISPOSITION_SUITE_INDEX} rows)
      math(EXPR GBB_AGE_DISPOSITION_ROW_LAST "${GBB_AGE_DISPOSITION_ROW_COUNT} - 1")
      foreach(GBB_AGE_DISPOSITION_ROW_INDEX RANGE 0 ${GBB_AGE_DISPOSITION_ROW_LAST})
        string(JSON GBB_AGE_CASE GET "${GBB_AGE_DISPOSITIONS_JSON}"
          suites ${GBB_AGE_DISPOSITION_SUITE_INDEX} rows ${GBB_AGE_DISPOSITION_ROW_INDEX} case)
        string(JSON GBB_AGE_DISPOSITION GET "${GBB_AGE_DISPOSITIONS_JSON}"
          suites ${GBB_AGE_DISPOSITION_SUITE_INDEX} rows ${GBB_AGE_DISPOSITION_ROW_INDEX} disposition)
        if(GBB_AGE_DISPOSITION STREQUAL "digest-only")
          continue()
        endif()
        string(JSON GBB_AGE_SIGNATURE GET "${GBB_AGE_DISPOSITIONS_JSON}"
          suites ${GBB_AGE_DISPOSITION_SUITE_INDEX} rows ${GBB_AGE_DISPOSITION_ROW_INDEX} signature_sha256)
        string(JSON GBB_AGE_ROW_MASK GET "${GBB_AGE_DISPOSITIONS_JSON}"
          suites ${GBB_AGE_DISPOSITION_SUITE_INDEX} rows ${GBB_AGE_DISPOSITION_ROW_INDEX} row_mask)

        set(GBB_AGE_CASE_FILE "${GBB_AGE_CASE}.gb")
        set(GBB_AGE_CASE_FOUND OFF)
        foreach(GBB_AGE_CASE_FIXTURE_INDEX IN LISTS GBB_AGE_ROW_FIXTURE_INDICES)
          string(JSON GBB_AGE_FIXTURE_FILE GET "${GBB_AGE_MANIFEST_JSON}"
            fixtures ${GBB_AGE_CASE_FIXTURE_INDEX} file)
          if(GBB_AGE_FIXTURE_FILE STREQUAL GBB_AGE_CASE_FILE)
            set(GBB_AGE_CASE_FOUND ON)
            string(JSON GBB_AGE_CASE_RESULTS GET "${GBB_AGE_MANIFEST_JSON}"
              fixtures ${GBB_AGE_CASE_FIXTURE_INDEX} test_results_address)
            string(JSON GBB_AGE_CASE_EXPECTED GET "${GBB_AGE_MANIFEST_JSON}"
              fixtures ${GBB_AGE_CASE_FIXTURE_INDEX} expected_address)
            string(JSON GBB_AGE_CASE_ROWS GET "${GBB_AGE_MANIFEST_JSON}"
              fixtures ${GBB_AGE_CASE_FIXTURE_INDEX} rows)
            string(JSON GBB_AGE_CASE_BUDGET GET "${GBB_AGE_MANIFEST_JSON}"
              fixtures ${GBB_AGE_CASE_FIXTURE_INDEX} budget_half_dots)
          endif()
        endforeach()
        if(NOT GBB_AGE_CASE_FOUND OR GBB_AGE_CASE_BUDGET LESS 1)
          message(FATAL_ERROR "AGE disposition ${GBB_AGE_CASE} lacks a manifest fixture or budget")
        endif()
        if(NOT GBB_AGE_DISPOSITION STREQUAL "pass" AND
           NOT GBB_AGE_DISPOSITION STREQUAL "expected-failure")
          message(FATAL_ERROR "AGE disposition ${GBB_AGE_CASE} is not runnable: ${GBB_AGE_DISPOSITION}")
        endif()

        string(REPLACE "$" "0x" GBB_AGE_CASE_RESULTS_HEX "${GBB_AGE_CASE_RESULTS}")
        string(REPLACE "$" "0x" GBB_AGE_CASE_EXPECTED_HEX "${GBB_AGE_CASE_EXPECTED}")
        string(REPLACE "-" "_" GBB_AGE_CASE_CTEST "${GBB_AGE_CASE}")
        set(GBB_AGE_CASE_TEST "age_${GBB_AGE_CASE_CTEST}")
        set(GBB_AGE_CASE_TIMEOUT 120)
        set(GBB_AGE_DISPOSITION_ARGS "${GBB_AGE_DISPOSITION}")
        set(GBB_AGE_EXPECTED_VERDICT "pass")
        if(GBB_AGE_DISPOSITION STREQUAL "expected-failure")
          list(APPEND GBB_AGE_DISPOSITION_ARGS "${GBB_AGE_SIGNATURE}" "${GBB_AGE_ROW_MASK}")
          set(GBB_AGE_EXPECTED_VERDICT "fail")
        endif()
        add_test(NAME ${GBB_AGE_CASE_TEST}
          COMMAND test_age "${PROJECT_SOURCE_DIR}/fixtures/age/${GBB_AGE_CASE_FILE}"
            "${GBB_AGE_CASE_RESULTS_HEX}" "${GBB_AGE_CASE_EXPECTED_HEX}"
            "${GBB_AGE_CASE_ROWS}" "${GBB_AGE_CASE_BUDGET}"
            --check-disposition ${GBB_AGE_DISPOSITION_ARGS})
        set_tests_properties(${GBB_AGE_CASE_TEST} PROPERTIES TIMEOUT ${GBB_AGE_CASE_TIMEOUT}
          PASS_REGULAR_EXPRESSION "age verdict=${GBB_AGE_EXPECTED_VERDICT}")
      endforeach()
    endif()
  endif()
endforeach()
if(NOT GBB_AGE_DISPOSITION_SUITE_FOUND OR GBB_AGE_DISPOSITION_ROW_COUNT LESS 1)
  message(FATAL_ERROR "AGE dispositions must contain non-empty age-test-roms rows")
endif()

# D-21 sensitivity tests run every admitted AGE fixture and compare its clean and mutant results.
set(GBB_AGE_SENSITIVITY_ENTRIES)
foreach(GBB_AGE_SENSITIVITY_INDEX IN LISTS GBB_AGE_ROW_FIXTURE_INDICES)
  string(JSON GBB_AGE_SENSITIVITY_FILE GET "${GBB_AGE_MANIFEST_JSON}"
    fixtures ${GBB_AGE_SENSITIVITY_INDEX} file)
  string(JSON GBB_AGE_SENSITIVITY_RESULTS GET "${GBB_AGE_MANIFEST_JSON}"
    fixtures ${GBB_AGE_SENSITIVITY_INDEX} test_results_address)
  string(JSON GBB_AGE_SENSITIVITY_EXPECTED GET "${GBB_AGE_MANIFEST_JSON}"
    fixtures ${GBB_AGE_SENSITIVITY_INDEX} expected_address)
  string(JSON GBB_AGE_SENSITIVITY_ROWS GET "${GBB_AGE_MANIFEST_JSON}"
    fixtures ${GBB_AGE_SENSITIVITY_INDEX} rows)
  string(JSON GBB_AGE_SENSITIVITY_BUDGET GET "${GBB_AGE_MANIFEST_JSON}"
    fixtures ${GBB_AGE_SENSITIVITY_INDEX} budget_half_dots)
  string(REGEX REPLACE "[.]gb$" "" GBB_AGE_SENSITIVITY_CASE "${GBB_AGE_SENSITIVITY_FILE}")
  string(REPLACE "$" "0x" GBB_AGE_SENSITIVITY_RESULTS "${GBB_AGE_SENSITIVITY_RESULTS}")
  string(REPLACE "$" "0x" GBB_AGE_SENSITIVITY_EXPECTED "${GBB_AGE_SENSITIVITY_EXPECTED}")
  list(APPEND GBB_AGE_SENSITIVITY_ENTRIES
    "${GBB_AGE_SENSITIVITY_CASE}|${GBB_AGE_SENSITIVITY_RESULTS}|${GBB_AGE_SENSITIVITY_EXPECTED}|${GBB_AGE_SENSITIVITY_ROWS}|${GBB_AGE_SENSITIVITY_BUDGET}")
endforeach()
list(JOIN GBB_AGE_SENSITIVITY_ENTRIES ";" GBB_AGE_SENSITIVITY_ENTRIES_TEXT)
set(GBB_AGE_SENSITIVITY_SCRIPT_DIR "${PROJECT_BINARY_DIR}/age-sensitivity")
file(MAKE_DIRECTORY "${GBB_AGE_SENSITIVITY_SCRIPT_DIR}")
set(GBB_AGE_SENSITIVITY_SCRIPT "${GBB_AGE_SENSITIVITY_SCRIPT_DIR}/run.cmake")
file(WRITE "${GBB_AGE_SENSITIVITY_SCRIPT}"
  "set(GBB_AGE_SENSITIVITY_ENTRIES [==[${GBB_AGE_SENSITIVITY_ENTRIES_TEXT}]==])\n")
file(APPEND "${GBB_AGE_SENSITIVITY_SCRIPT}" [=[
foreach(GBB_ENTRY IN LISTS GBB_AGE_SENSITIVITY_ENTRIES)
  string(REPLACE "|" ";" GBB_FIELDS "${GBB_ENTRY}")
  list(GET GBB_FIELDS 0 GBB_CASE)
  list(GET GBB_FIELDS 1 GBB_RESULTS)
  list(GET GBB_FIELDS 2 GBB_EXPECTED)
  list(GET GBB_FIELDS 3 GBB_ROWS)
  list(GET GBB_FIELDS 4 GBB_BUDGET)
  execute_process(
    COMMAND "${GBB_AGE_SENSITIVITY_EXECUTABLE}"
      "${GBB_AGE_SENSITIVITY_ROOT}/${GBB_CASE}.gb"
      "${GBB_RESULTS}" "${GBB_EXPECTED}" "${GBB_ROWS}" "${GBB_BUDGET}"
      --sensitivity "${GBB_AGE_SENSITIVITY_MASK}" "${GBB_AGE_SENSITIVITY_JSON}"
    RESULT_VARIABLE GBB_RESULT OUTPUT_VARIABLE GBB_OUTPUT ERROR_VARIABLE GBB_ERROR)
  if(NOT GBB_RESULT EQUAL 0)
    message(FATAL_ERROR "age-sensitivity mismatch mutant=${GBB_AGE_SENSITIVITY_MUTANT} case=${GBB_CASE}\n${GBB_OUTPUT}${GBB_ERROR}")
  endif()
endforeach()
message(STATUS "age-sensitivity-sweep pass mutant=${GBB_AGE_SENSITIVITY_MUTANT} fixtures=13")
]=])
foreach(GBB_AGE_SENSITIVITY_MUTANT IN ITEMS M6 M21 M28 M27)
  if(GBB_AGE_SENSITIVITY_MUTANT STREQUAL "M6")
    set(GBB_AGE_SENSITIVITY_MASK "0x40")
  elseif(GBB_AGE_SENSITIVITY_MUTANT STREQUAL "M21")
    set(GBB_AGE_SENSITIVITY_MASK "0x200000")
  elseif(GBB_AGE_SENSITIVITY_MUTANT STREQUAL "M28")
    set(GBB_AGE_SENSITIVITY_MASK "0x10000000")
  else()
    set(GBB_AGE_SENSITIVITY_MASK "0x8000000")
  endif()
  string(TOLOWER "${GBB_AGE_SENSITIVITY_MUTANT}" GBB_AGE_SENSITIVITY_TEST_SUFFIX)
  add_test(NAME age_sensitivity_${GBB_AGE_SENSITIVITY_TEST_SUFFIX}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_AGE_SENSITIVITY_EXECUTABLE=$<TARGET_FILE:test_age_p12>"
      "-DGBB_AGE_SENSITIVITY_ROOT=${PROJECT_SOURCE_DIR}/fixtures/age"
      "-DGBB_AGE_SENSITIVITY_JSON=${GBB_AGE_DISPOSITIONS_FILE}"
      "-DGBB_AGE_SENSITIVITY_MASK=${GBB_AGE_SENSITIVITY_MASK}"
      "-DGBB_AGE_SENSITIVITY_MUTANT=${GBB_AGE_SENSITIVITY_MUTANT}"
      -P "${GBB_AGE_SENSITIVITY_SCRIPT}")
  set_tests_properties(age_sensitivity_${GBB_AGE_SENSITIVITY_TEST_SUFFIX} PROPERTIES
    PASS_REGULAR_EXPRESSION "age-sensitivity-sweep pass mutant=${GBB_AGE_SENSITIVITY_MUTANT} fixtures=13"
    TIMEOUT 240)
endforeach()

# A deliberately wrong M28 reference proves the new mode rejects altered coverage.
set(gbb_age_m28_reference_anchor "\"mutant\": \"M28\",\n            \"description\": \"add one half-dot to the stall when switching to double speed\",\n            \"discriminating_cases\": [\n              \"spsw-mode0-cgbBCE\"")
string(FIND "${GBB_AGE_DISPOSITIONS_JSON}" "${gbb_age_m28_reference_anchor}" gbb_age_m28_anchor_at)
string(FIND "${GBB_AGE_DISPOSITIONS_JSON}" "${gbb_age_m28_reference_anchor}" gbb_age_m28_anchor_last REVERSE)
if(gbb_age_m28_anchor_at EQUAL -1 OR NOT gbb_age_m28_anchor_at EQUAL gbb_age_m28_anchor_last)
  message(FATAL_ERROR "AGE M28 sensitivity negative-control anchor must occur exactly once")
endif()
string(REPLACE "${gbb_age_m28_reference_anchor}"
  "\"mutant\": \"M28\",\n            \"description\": \"add one half-dot to the stall when switching to double speed\",\n            \"discriminating_cases\": []"
  gbb_age_m28_reference_mutated "${GBB_AGE_DISPOSITIONS_JSON}")
set(GBB_AGE_M28_MUTATED_JSON "${GBB_AGE_SENSITIVITY_SCRIPT_DIR}/m28-mutated.json")
file(WRITE "${GBB_AGE_M28_MUTATED_JSON}" "${gbb_age_m28_reference_mutated}")
add_test(NAME age_sensitivity_m28_reference_mutated
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_age_p12>;${PROJECT_SOURCE_DIR}/fixtures/age/spsw-mode0-cgbBCE.gb;0xC000;0x144A;15;4000000;--sensitivity;0x10000000;${GBB_AGE_M28_MUTATED_JSON}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=age-sensitivity mismatch"
    -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
set_tests_properties(age_sensitivity_m28_reference_mutated PROPERTIES TIMEOUT 60)

# AGE fixture integrity and redistribution guards (D-19, T-12-20). The digest
# mutation proves the manifest verifier rejects a changed pin; the install scan
# and renamed-copy control prevent repository-only ROMs from entering packages.
add_test(NAME age_fixture_digest
  COMMAND ${CMAKE_COMMAND} -DMANIFEST=${GBB_AGE_MANIFEST}
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixtureManifest.cmake)

string(JSON GBB_AGE_TAMPERED_DIGEST GET "${GBB_AGE_MANIFEST_JSON}" fixtures 0 sha256)
string(SUBSTRING "${GBB_AGE_TAMPERED_DIGEST}" 0 1 GBB_AGE_TAMPERED_FIRST)
string(SUBSTRING "${GBB_AGE_TAMPERED_DIGEST}" 1 63 GBB_AGE_TAMPERED_REST)
if(GBB_AGE_TAMPERED_FIRST STREQUAL "0")
  set(GBB_AGE_TAMPERED_FIRST "1")
else()
  set(GBB_AGE_TAMPERED_FIRST "0")
endif()
set(GBB_AGE_TAMPERED_DIGEST "${GBB_AGE_TAMPERED_FIRST}${GBB_AGE_TAMPERED_REST}")
string(JSON GBB_AGE_TAMPERED_MANIFEST SET "${GBB_AGE_MANIFEST_JSON}"
  fixtures 0 sha256 "\"${GBB_AGE_TAMPERED_DIGEST}\"")
set(GBB_AGE_TAMPERED_MANIFEST_FILE "${PROJECT_BINARY_DIR}/age-tampered/manifest.json")
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/age-tampered")
file(COPY_FILE "${PROJECT_SOURCE_DIR}/fixtures/age/spsw-div-cgbBCE.gb"
  "${PROJECT_BINARY_DIR}/age-tampered/spsw-div-cgbBCE.gb")
file(WRITE "${GBB_AGE_TAMPERED_MANIFEST_FILE}" "${GBB_AGE_TAMPERED_MANIFEST}")
add_test(NAME age_fixture_digest_tampered
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DMANIFEST=${GBB_AGE_TAMPERED_MANIFEST_FILE};-P;${PROJECT_SOURCE_DIR}/cmake/VerifyFixtureManifest.cmake"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=fixture-digest-mismatch: spsw-div-cgbBCE[.]gb"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)

set(GBB_AGE_SCAN_SELFTEST "${PROJECT_BINARY_DIR}/age-scan-selftest")
file(MAKE_DIRECTORY "${GBB_AGE_SCAN_SELFTEST}/share")
file(COPY_FILE "${PROJECT_SOURCE_DIR}/fixtures/age/spsw-div-cgbBCE.gb"
  "${GBB_AGE_SCAN_SELFTEST}/share/payload.bin")
set(GBB_AGE_SCAN_ARGS "-DGBB_FORBIDDEN_MANIFEST=${GBB_AGE_MANIFEST}"
  -DGBB_FORBIDDEN_LABEL=fixtures/age)
function(gbb_add_age_scan_test name code regex scan_dir)
  set(command "${CMAKE_COMMAND}" "-DGBB_SCAN_DIR=${scan_dir}" ${GBB_AGE_SCAN_ARGS}
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
gbb_add_age_scan_test(age_not_installed 0 "fixtures/age absent from scanned tree files=[1-9]"
  "${GBB_LIBBET_INSTALL_CHECK}")
set_tests_properties(age_not_installed PROPERTIES FIXTURES_REQUIRED libbet_install)
gbb_add_age_scan_test(age_not_installed_selftest 1 "fixtures/age-installed: share/payload[.]bin"
  "${GBB_AGE_SCAN_SELFTEST}")

if(NOT WIN32)
  find_program(GBB_BASH_AGE_REPRO bash REQUIRED)
  add_test(NAME age_repro_selfcheck
    COMMAND "${GBB_BASH_AGE_REPRO}" "${PROJECT_SOURCE_DIR}/tests/scripts/reproduce-age.sh" --self-check)
  set_tests_properties(age_repro_selfcheck PROPERTIES TIMEOUT 30
    PASS_REGULAR_EXPRESSION "self-check=pass")
  add_test(NAME age_repro_selfcheck_tampered
    COMMAND "${GBB_BASH_AGE_REPRO}" "${PROJECT_SOURCE_DIR}/tests/scripts/test-reproduce-age.sh" selfcheck-tampered)
  set_tests_properties(age_repro_selfcheck_tampered PROPERTIES TIMEOUT 60
    PASS_REGULAR_EXPRESSION "reproduce-age negative control selfcheck-tampered ok")
  add_test(NAME age_repro_compare_tampered
    COMMAND "${GBB_BASH_AGE_REPRO}" "${PROJECT_SOURCE_DIR}/tests/scripts/test-reproduce-age.sh" compare-tampered)
  set_tests_properties(age_repro_compare_tampered PROPERTIES TIMEOUT 60
    PASS_REGULAR_EXPRESSION "reproduce-age negative control compare-tampered ok")
endif()

# Unknown manifest protocols must fail closed before row metadata can be consumed.
string(JSON GBB_AGE_UNKNOWN_CLASS_MANIFEST SET "${GBB_AGE_MANIFEST_JSON}"
  fixtures 0 fixture_class "\"age-unknown-protocol\"")
set(GBB_AGE_UNKNOWN_CLASS_MANIFEST_FILE "${PROJECT_BINARY_DIR}/age-unknown-class/manifest.json")
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/age-unknown-class")
file(WRITE "${GBB_AGE_UNKNOWN_CLASS_MANIFEST_FILE}" "${GBB_AGE_UNKNOWN_CLASS_MANIFEST}")
add_test(NAME age_manifest_unknown_class
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DMANIFEST=${GBB_AGE_UNKNOWN_CLASS_MANIFEST_FILE};-P;${PROJECT_SOURCE_DIR}/tests/scripts/check-age-fixture-protocol.cmake"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=age-fixture-protocol: unsupported fixture_class age-unknown-protocol"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(age_manifest_unknown_class PROPERTIES TIMEOUT 30)
# --- Phase 12 plan 12-16 end ---

# --- Phase 12 plan 12-10 begin ---
# Original project-authored CGB speed probes (D-22); the expectations are generated only from
# documented clock units, and this driver observes the guest solely through the public API.
set(GBB_CGB_SPEED_DIR "${PROJECT_SOURCE_DIR}/fixtures/cgb-speed")
add_executable(test_cgb_speed_fixture test_cgb_speed_fixture.c)
target_include_directories(test_cgb_speed_fixture PRIVATE "${PROJECT_SOURCE_DIR}/src/accept")
target_link_libraries(test_cgb_speed_fixture PRIVATE GabbaBoy::core gabbaboy_accept)
target_compile_features(test_cgb_speed_fixture PRIVATE c_std_17)
set_target_properties(test_cgb_speed_fixture PROPERTIES C_EXTENSIONS OFF)
add_test(NAME cgb_speed_fixture_digest
  COMMAND ${CMAKE_COMMAND} -DMANIFEST=${GBB_CGB_SPEED_DIR}/manifest.json
    -P ${PROJECT_SOURCE_DIR}/cmake/VerifyFixtureManifest.cmake)
add_test(NAME cgb_speed_expectations_derive
  COMMAND ${Python3_EXECUTABLE} -I ${PROJECT_SOURCE_DIR}/tests/scripts/derive-cgb-speed-expectations.py
    --check ${PROJECT_SOURCE_DIR}/tests/data/cgb-speed-expectations.txt)
set_tests_properties(cgb_speed_expectations_derive PROPERTIES
  PASS_REGULAR_EXPRESSION "cgb-speed-expectations check pass")
add_test(NAME cgb_speed_fixture_probes
  COMMAND test_cgb_speed_fixture probes ${GBB_CGB_SPEED_DIR}/speed.gb
    ${PROJECT_SOURCE_DIR}/tests/data/cgb-speed-expectations.txt)
set_tests_properties(cgb_speed_fixture_probes PROPERTIES
  PASS_REGULAR_EXPRESSION "cgb-speed-fixture probes pass checks=" TIMEOUT 60)

# A configure-time out-of-range edit must be caught by the independent host verdict.
set(GBB_CGB_SPEED_TAMPERED_TABLE "${PROJECT_BINARY_DIR}/cgb-speed/tampered-expectations.txt")
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/cgb-speed")
file(READ "${PROJECT_SOURCE_DIR}/tests/data/cgb-speed-expectations.txt" gbb_cgb_speed_expectations)
string(FIND "${gbb_cgb_speed_expectations}" "tima 0 26 31" gbb_cgb_speed_tima_anchor)
if(gbb_cgb_speed_tima_anchor EQUAL -1)
  message(FATAL_ERROR "cgb-speed expectation tamper anchor is missing")
endif()
string(REPLACE "tima 0 26 31" "tima 0 200 201" gbb_cgb_speed_expectations_bad
  "${gbb_cgb_speed_expectations}")
file(WRITE "${GBB_CGB_SPEED_TAMPERED_TABLE}" "${gbb_cgb_speed_expectations_bad}")
add_test(NAME cgb_speed_expectations_tampered
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_speed_fixture>;probes;${GBB_CGB_SPEED_DIR}/speed.gb;${GBB_CGB_SPEED_TAMPERED_TABLE}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=cgb-speed-fixture verdict-fail tima 0"
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(cgb_speed_expectations_tampered PROPERTIES TIMEOUT 60)

# The wrong speed ratio is derived afresh at test time, then must disagree with the clean ROM.
set(GBB_CGB_SPEED_FACTOR3_SCRIPT "${PROJECT_BINARY_DIR}/cgb-speed/factor3.cmake")
file(WRITE "${GBB_CGB_SPEED_FACTOR3_SCRIPT}" [=[
execute_process(COMMAND "${PYTHON}" -I "${DERIVER}" --write "${OUTPUT}" --speed-factor 3
  RESULT_VARIABLE derive_result OUTPUT_VARIABLE derive_out ERROR_VARIABLE derive_err)
if(NOT derive_result EQUAL 0)
  message(FATAL_ERROR "factor-3 derivation failed: ${derive_out}${derive_err}")
endif()
execute_process(COMMAND "${TEST_EXE}" probes "${ROM}" "${OUTPUT}"
  RESULT_VARIABLE test_result OUTPUT_VARIABLE test_out ERROR_VARIABLE test_err)
if(test_result EQUAL 0 OR NOT "${test_out}${test_err}" MATCHES "cgb-speed-fixture verdict-fail")
  message(FATAL_ERROR "factor-3 negative control did not reject the clean core: ${test_out}${test_err}")
endif()
message("cgb-speed-expectations factor3 reject pass")
]=])
add_test(NAME cgb_speed_expectations_factor3
  COMMAND ${CMAKE_COMMAND}
    "-DPYTHON=${Python3_EXECUTABLE}"
    "-DDERIVER=${PROJECT_SOURCE_DIR}/tests/scripts/derive-cgb-speed-expectations.py"
    "-DOUTPUT=${PROJECT_BINARY_DIR}/cgb-speed/factor3-expectations.txt"
    "-DTEST_EXE=$<TARGET_FILE:test_cgb_speed_fixture>"
    "-DROM=${GBB_CGB_SPEED_DIR}/speed.gb"
    -P "${GBB_CGB_SPEED_FACTOR3_SCRIPT}")
set_tests_properties(cgb_speed_expectations_factor3 PROPERTIES
  PASS_REGULAR_EXPRESSION "cgb-speed-expectations factor3 reject pass" TIMEOUT 60)

# Core-level fixture identities use only the public API; mutant code is generated in the build tree.
add_executable(test_cgb_speed_fixture_p12 test_cgb_speed_fixture.c)
target_include_directories(test_cgb_speed_fixture_p12 PRIVATE
  "${PROJECT_SOURCE_DIR}/include" "${PROJECT_SOURCE_DIR}/src/accept")
target_compile_features(test_cgb_speed_fixture_p12 PRIVATE c_std_17)
target_compile_definitions(test_cgb_speed_fixture_p12 PRIVATE GBB_P12_PUBLIC_MUTANT=1)
target_link_libraries(test_cgb_speed_fixture_p12 PRIVATE
  gabbaboy_core_p12_mutants gabbaboy_accept)
set_target_properties(test_cgb_speed_fixture_p12 PROPERTIES C_EXTENSIONS OFF)

add_test(NAME cgb_speed_fixture_audio_digest
  COMMAND test_cgb_speed_fixture audio "${GBB_CGB_SPEED_DIR}/speed.gb")
add_test(NAME cgb_speed_fixture_frame_digest
  COMMAND test_cgb_speed_fixture frame "${GBB_CGB_SPEED_DIR}/speed.gb")
set_tests_properties(cgb_speed_fixture_audio_digest cgb_speed_fixture_frame_digest
  PROPERTIES TIMEOUT 60)

add_test(NAME cgb_speed_fixture_audio_digest_mutant_m17
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_speed_fixture_p12>;audio;${GBB_CGB_SPEED_DIR}/speed.gb;--mutants;131072"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=cgb-speed-fixture audio-digest mismatch observed audio"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
add_test(NAME cgb_speed_fixture_audio_digest_mutant_m17_control
  COMMAND test_cgb_speed_fixture_p12 audio "${GBB_CGB_SPEED_DIR}/speed.gb" --mutants 0)
add_test(NAME cgb_speed_fixture_frame_digest_mutant_m1
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_speed_fixture_p12>;frame;${GBB_CGB_SPEED_DIR}/speed.gb;--mutants;2"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=cgb-speed-fixture frame-digest mismatch observed frame"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
add_test(NAME cgb_speed_fixture_frame_digest_mutant_m1_control
  COMMAND test_cgb_speed_fixture_p12 frame "${GBB_CGB_SPEED_DIR}/speed.gb" --mutants 0)
set_tests_properties(
  cgb_speed_fixture_audio_digest_mutant_m17
  cgb_speed_fixture_audio_digest_mutant_m17_control
  cgb_speed_fixture_frame_digest_mutant_m1
  cgb_speed_fixture_frame_digest_mutant_m1_control
  PROPERTIES TIMEOUT 60)
# --- Phase 12 plan 12-10 end ---

# --- Phase 12 plan 12-11 begin ---
# Hostile STOP decision-table cases run from a separate original ROM. The selector is patched
# only in a private in-memory copy by the public-API test driver.
add_test(NAME cgb_speed_fixture_hostile
  COMMAND test_cgb_speed_fixture hostile ${GBB_CGB_SPEED_DIR}/speed-hostile.gb
    ${PROJECT_SOURCE_DIR}/tests/data/cgb-speed-expectations.txt)
set_tests_properties(cgb_speed_fixture_hostile PROPERTIES
  PASS_REGULAR_EXPRESSION "cgb-speed-fixture hostile pass entries=10" TIMEOUT 60)

# A hostile outcome is independently checked by the public-API selector driver.
set(GBB_CGB_SPEED_HOSTILE_TAMPERED_TABLE
  "${PROJECT_BINARY_DIR}/cgb-speed/hostile-tampered-expectations.txt")
file(READ "${PROJECT_SOURCE_DIR}/tests/data/cgb-speed-expectations.txt"
  gbb_cgb_speed_hostile_expectations)
string(FIND "${gbb_cgb_speed_hostile_expectations}" "hostile-key1-after 4 127 127"
  gbb_cgb_speed_hostile_anchor)
string(FIND "${gbb_cgb_speed_hostile_expectations}" "hostile-key1-after 4 127 127"
  gbb_cgb_speed_hostile_anchor_last REVERSE)
if(gbb_cgb_speed_hostile_anchor EQUAL -1 OR
   NOT gbb_cgb_speed_hostile_anchor EQUAL gbb_cgb_speed_hostile_anchor_last)
  message(FATAL_ERROR "hostile expectation tamper anchor must occur exactly once")
endif()
string(REPLACE "hostile-key1-after 4 127 127" "hostile-key1-after 4 254 254"
  gbb_cgb_speed_hostile_expectations_bad "${gbb_cgb_speed_hostile_expectations}")
file(WRITE "${GBB_CGB_SPEED_HOSTILE_TAMPERED_TABLE}"
  "${gbb_cgb_speed_hostile_expectations_bad}")
add_test(NAME cgb_speed_expectations_hostile_tampered
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_speed_fixture>;hostile;${GBB_CGB_SPEED_DIR}/speed-hostile.gb;${GBB_CGB_SPEED_HOSTILE_TAMPERED_TABLE}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=cgb-speed-fixture verdict-fail hostile-4 hostile-key1-after"
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(cgb_speed_expectations_hostile_tampered PROPERTIES TIMEOUT 60)
# --- Phase 12 plan 12-11 end ---

# --- Phase 12 plan 12-13 begin ---
# Offline controls prove manifest-driven fixture rebuild errors stay distinct from byte differences.
if(NOT WIN32)
  find_program(GBB_BASH_CGB_REPRO bash REQUIRED)
  foreach(gbb_repro_case tool_failure missing_pin)
    string(REPLACE "_" "-" gbb_repro_arg "${gbb_repro_case}")
    add_test(NAME cgb_speed_repro_${gbb_repro_case}
      COMMAND ${GBB_BASH_CGB_REPRO} ${PROJECT_SOURCE_DIR}/tests/scripts/test-reproduce-cgb-speed.sh ${gbb_repro_arg})
    set_tests_properties(cgb_speed_repro_${gbb_repro_case} PROPERTIES TIMEOUT 60)
  endforeach()
endif()
# --- Phase 12 plan 12-13 end ---

# --- Phase 12 plan 12-14 begin ---
set(GBB_P12_PARTITION_MUTANT_CORE "${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_p12_partition_mutants.c")
gbb_p12_make_mutant_core("${GBB_P12_PARTITION_MUTANT_CORE}" 0)
add_executable(test_cgb_partition test_cgb_partition.c)
target_include_directories(test_cgb_partition PRIVATE
  "${PROJECT_SOURCE_DIR}/include" "${PROJECT_SOURCE_DIR}/src/core")
target_compile_features(test_cgb_partition PRIVATE c_std_17)
target_compile_definitions(test_cgb_partition PRIVATE
  "GBB_PARTITION_CASE_HALF_DOT_CAP=6000000")
set_target_properties(test_cgb_partition PROPERTIES C_EXTENSIONS OFF)

add_executable(test_cgb_partition_p12 test_cgb_partition.c)
target_include_directories(test_cgb_partition_p12 PRIVATE
  "${PROJECT_SOURCE_DIR}/include" "${PROJECT_SOURCE_DIR}/src/core")
target_compile_features(test_cgb_partition_p12 PRIVATE c_std_17)
target_compile_definitions(test_cgb_partition_p12 PRIVATE
  "GBB_P12_CORE_SOURCE=\"${GBB_P12_PARTITION_MUTANT_CORE}\""
  GBB_P12_MUTANT_BUILD=1 GBB_BUILD_REVISION="p12-partition-mutant" GBB_BUILD_QUALIFIED=0
  "GBB_PARTITION_CASE_HALF_DOT_CAP=6000000")
set_target_properties(test_cgb_partition_p12 PROPERTIES C_EXTENSIONS OFF)

add_test(NAME cgb_partition_stall_start_window
  COMMAND test_cgb_partition cgb_partition_stall_start_window)
add_test(NAME cgb_partition_hostile_irq_in_stall
  COMMAND test_cgb_partition cgb_partition_hostile_irq_in_stall)
add_test(NAME cgb_partition_mutant_m16
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_cgb_partition_p12>;cgb_partition_hostile_irq_in_stall;--mutants;65536"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=partition-mismatch scenario=cgb_partition_hostile_irq_in_stall"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
add_test(NAME cgb_partition_mutant_m16_control
  COMMAND test_cgb_partition_p12 cgb_partition_hostile_irq_in_stall --mutants 0)
# Fresh local Darwin arm64 Debug CTest -V -j1 wall seconds: start .11, hostile
# IRQ .11, mutant/control .09/.10, snapshot .01, real ends .11/.12, seeded end
# .10, interior .03, multicut .43, budget .01, pending .55, held .11, LCD-off
# .11, back-to-back .22, chained .52, joypad/digest sensitivities .02/.02.
# These are local CTest timings, not an ASan benchmark. The 6,000,000 half-dot
# cap uses 12-RESEARCH.md's prior ~92 ns/hd ad-hoc -O0 ASan measurement; it was
# not re-measured in this run. Largest observed case: multicut, 2,187,264 hd,
# 0.43 s local Debug; each CTest retains TIMEOUT 60 for sanitizer headroom.
foreach(gbb_partition_case IN ITEMS
    cgb_apu_lifecycle
    cgb_apu_lifecycle_controls
    cgb_apu_partition_fetch
    cgb_apu_partition_speed
    cgb_apu_partition_controls
    cgb_partition_snapshot_fidelity
    cgb_partition_stall_end_window_to_double
    cgb_partition_stall_end_window_to_normal
    cgb_partition_stall_end_window_seeded
    cgb_partition_interior_points
    cgb_partition_seeded_multicut
    cgb_partition_zero_and_subquantum
    cgb_partition_pending_at_stop
    cgb_partition_held_button
    cgb_partition_lcd_off
    cgb_partition_back_to_back
    cgb_partition_chained
    cgb_partition_sensitivity_joypad_shift
    cgb_partition_sensitivity_digest_input)
  add_test(NAME ${gbb_partition_case} COMMAND test_cgb_partition ${gbb_partition_case})
endforeach()
set_tests_properties(
  cgb_apu_partition_fetch
  cgb_apu_partition_speed
  cgb_apu_partition_controls
  cgb_partition_stall_start_window
  cgb_partition_hostile_irq_in_stall
  cgb_partition_mutant_m16
  cgb_partition_mutant_m16_control
  cgb_partition_snapshot_fidelity
  cgb_partition_stall_end_window_to_double
  cgb_partition_stall_end_window_to_normal
  cgb_partition_stall_end_window_seeded
  cgb_partition_interior_points
  cgb_partition_seeded_multicut
  cgb_partition_zero_and_subquantum
  cgb_partition_pending_at_stop
  cgb_partition_held_button
  cgb_partition_lcd_off
  cgb_partition_back_to_back
  cgb_partition_chained
  cgb_partition_sensitivity_joypad_shift
  cgb_partition_sensitivity_digest_input
  PROPERTIES TIMEOUT 60)
# --- Phase 12 plan 12-14 end ---

# --- Phase 12 plan 12-18 begin ---
set(GBB_SPEED_DOC_FILES
  "${PROJECT_SOURCE_DIR}/docs/native-integration.md"
  "${PROJECT_SOURCE_DIR}/docs/support/unreleased.md"
  "${PROJECT_SOURCE_DIR}/docs/preview.md"
  "${PROJECT_SOURCE_DIR}/docs/cartridge-and-saves.md"
  "${PROJECT_SOURCE_DIR}/docs/mbc3-rtc-evidence.md"
  "${PROJECT_SOURCE_DIR}/README.md"
  "${PROJECT_SOURCE_DIR}/src/player/limitations.h")
add_test(NAME cgb_speed_docs_no_stale_claims
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_FILES=${GBB_SPEED_DOC_FILES}"
    -P "${PROJECT_SOURCE_DIR}/tests/check_no_stale_speed_claims.cmake")
set_tests_properties(cgb_speed_docs_no_stale_claims PROPERTIES
  PASS_REGULAR_EXPRESSION "no-stale-speed-claims pass" TIMEOUT 30)

set(GBB_SPEED_DOC_SELFTEST_DIR "${PROJECT_BINARY_DIR}/cgb-speed-doc-selftest")
file(MAKE_DIRECTORY "${GBB_SPEED_DOC_SELFTEST_DIR}")
file(READ "${PROJECT_SOURCE_DIR}/docs/preview.md" gbb_speed_preview_text)
string(APPEND gbb_speed_preview_text "\nno double speed\n")
set(GBB_SPEED_DOC_MUTATED_PREVIEW "${GBB_SPEED_DOC_SELFTEST_DIR}/preview.md")
file(WRITE "${GBB_SPEED_DOC_MUTATED_PREVIEW}" "${gbb_speed_preview_text}")
add_test(NAME cgb_speed_docs_no_stale_claims_mutated
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_FILES=${GBB_SPEED_DOC_MUTATED_PREVIEW};-P;${PROJECT_SOURCE_DIR}/tests/check_no_stale_speed_claims.cmake"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=stale-speed-claim"
    -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
set_tests_properties(cgb_speed_docs_no_stale_claims_mutated PROPERTIES TIMEOUT 30)
# --- Phase 12 plan 12-18 end ---

# Configure-only regression for the shared sanitizer timeout policy. This is last so adding a
# test after the scaler cannot silently escape the policy pass.
add_test(NAME sanitizer_timeout_policy_selftest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_SOURCE_DIR=${PROJECT_SOURCE_DIR}"
    "-DGBB_BINARY_DIR=${PROJECT_BINARY_DIR}"
    -P "${PROJECT_SOURCE_DIR}/tests/check_sanitizer_timeout_policy.cmake")
set_tests_properties(sanitizer_timeout_policy_selftest PROPERTIES TIMEOUT 30)

gabbaboy_verify_registered_tests()

# Per-test TIMEOUTs are normal-build limits. Debug ASan/UBSan runs the same work several times
# slower, and the whole-run acceptance and RTC cases reached their 300 s limits on a slow hosted
# runner (LESSONS GB-CI-004). Apply one shared multiplier after every test registration.
include("${PROJECT_SOURCE_DIR}/cmake/ScaleSanitizerTimeouts.cmake")
gbb_scale_sanitizer_test_timeouts()

if(GABBABOY_ENABLE_SANITIZERS)
  foreach(gbb_timeout_case IN ITEMS
      "age_spsw_div_cgbBCE=360"
      "age_spsw_div_cgbBCE_timeout=90"
      "age_stall_window=720"
      "age_sensitivity_m6=720"
      "age_sensitivity_m28_reference_mutated=180"
      "cgb_partition_stall_start_window=180")
    string(REPLACE "=" ";" gbb_timeout_pair "${gbb_timeout_case}")
    list(GET gbb_timeout_pair 0 gbb_timeout_test)
    list(GET gbb_timeout_pair 1 gbb_timeout_expected)
    get_test_property(${gbb_timeout_test} TIMEOUT gbb_timeout_actual)
    if(NOT "${gbb_timeout_actual}" STREQUAL "${gbb_timeout_expected}")
      message(FATAL_ERROR
        "Sanitizer timeout policy: ${gbb_timeout_test} expected ${gbb_timeout_expected}, "
        "got ${gbb_timeout_actual}")
    endif()
  endforeach()
endif()
