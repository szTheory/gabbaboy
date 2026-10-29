# Phase 18: host-process contract tests for gabbaboy-runner host mode (HOST-01..03).
#
# Every name registered here must also be listed in tests/expected-tests.txt (append-only). Host mode is
# POSIX-only in v0.3 (D-05), so POSIX-only names are registered inside if(NOT WIN32) and removed from the
# Windows expectation in BOTH cmake/ExpectedTests.cmake and .github/scripts/verify-test-inventory.sh.
# Generated ROMs and save directories live under ${PROJECT_BINARY_DIR}/host-mode; nothing binary is committed.
# New tests keep the base 60 s timeout (D-27).

set(GBB_HOST_MODE_HARNESS "${PROJECT_SOURCE_DIR}/tests/scripts/test_host_mode.py")

# gbb_add_host_mode_test(name scenario): one python3 -I scenario against the real runner process.
function(gbb_add_host_mode_test name scenario)
  add_test(NAME ${name}
    COMMAND "${Python3_EXECUTABLE}" -I "${GBB_HOST_MODE_HARNESS}"
      --runner $<TARGET_FILE:gabbaboy-runner>
      --work "${PROJECT_BINARY_DIR}/host-mode/${name}"
      --scenario ${scenario})
  set_tests_properties(${name} PROPERTIES
    PASS_REGULAR_EXPRESSION "host-mode scenario=${scenario} pass")
endfunction()

if(NOT WIN32)
  gbb_add_host_mode_test(host_continuation continuation)
  gbb_add_host_mode_test(host_rom_max_size rom-max)
  gbb_add_host_mode_test(host_rom_oversize rom-oversize)
  gbb_add_host_mode_test(host_rom_unreadable rom-unreadable)
  gbb_add_host_mode_test(host_cli_stem_refusal stem-refusal)
endif()

# ---- D-07: the stem rule, one CTest per class (portable: no filesystem is touched) ----------------------
# test_host_basename links gabbaboy_host only. It is never built from src/host sources directly, because
# this directory adds src/core to every target's include path and would mask a stray gabbaboy_test.h.
add_executable(test_host_basename "${PROJECT_SOURCE_DIR}/tests/test_host_basename.c")
target_link_libraries(test_host_basename PRIVATE gabbaboy_host)
target_compile_features(test_host_basename PRIVATE c_std_17)
set_target_properties(test_host_basename PROPERTIES C_EXTENSIONS OFF)

foreach(case accepts refuse_empty refuse_leading_dot refuse_control refuse_del refuse_backslash
             refuse_bad_utf8 refuse_too_long)
  add_test(NAME host_stem_${case} COMMAND test_host_basename ${case})
  set_tests_properties(host_stem_${case} PROPERTIES PASS_REGULAR_EXPRESSION "PASS ${case}")
endforeach()

# gbb_host_mutant_library(name source anchor replacement): a copy of gabbaboy_host in which one
# `src/host/<source>` has its single `anchor` replaced. The mutated file is written under
# host-mutants/<name>/ and every other host source is compiled unmodified, so a mutant test can only
# fail because of the one edit. The anchor must occur exactly once, as for gbb_state_refusal_mutant.
function(gbb_host_mutant_library name source anchor replacement)
  set(original "${PROJECT_SOURCE_DIR}/src/host/${source}")
  file(READ "${original}" text)
  string(FIND "${text}" "${anchor}" first)
  string(FIND "${text}" "${anchor}" last REVERSE)
  if(first EQUAL -1 OR NOT first EQUAL last)
    message(FATAL_ERROR
      "Host mutant ${name}: anchor must occur exactly once in ${source} (first=${first}, last=${last})")
  endif()
  string(REPLACE "${anchor}" "${replacement}" text "${text}")
  set(directory "${PROJECT_BINARY_DIR}/host-mutants/${name}")
  file(WRITE "${directory}/${source}" "${text}")

  get_target_property(host_sources gabbaboy_host SOURCES)
  set(sources "")
  foreach(entry IN LISTS host_sources)
    get_filename_component(absolute "${entry}" ABSOLUTE BASE_DIR "${PROJECT_SOURCE_DIR}")
    get_filename_component(file_name "${absolute}" NAME)
    if(file_name STREQUAL "${source}")
      list(APPEND sources "${directory}/${source}")
    else()
      list(APPEND sources "${absolute}")
    endif()
  endforeach()
  add_library(gabbaboy_host_mutant_${name} STATIC ${sources})
  target_include_directories(gabbaboy_host_mutant_${name} PUBLIC
    "${PROJECT_SOURCE_DIR}/src/host" "${PROJECT_SOURCE_DIR}/include")
  target_compile_features(gabbaboy_host_mutant_${name} PUBLIC c_std_17)
  set_target_properties(gabbaboy_host_mutant_${name} PROPERTIES C_EXTENSIONS OFF)
endfunction()

# The transform mutant: a backslash is rewritten to `_` and the stem is accepted instead of refused.
# refuse_backslash must fail with its own FAIL line (exit 1), not crash.
gbb_host_mutant_library(stem_transform host_basename.c
  [=[for (size_t i = 0u; i < len; ++i) if (comp[i] == '\\') return HOST_STEM_BACKSLASH;]=]
  [=[for (size_t i = 0u; i < len; ++i) if (comp[i] == '\\') {
        const size_t n = len < cap ? len : cap - 1u;
        for (size_t k = 0u; k < n; ++k) out[k] = comp[k] == '\\' ? '_' : (char)comp[k];
        out[n] = '\0';
        return HOST_STEM_OK;
    }]=])
add_executable(test_host_basename_mutant_stem_transform "${PROJECT_SOURCE_DIR}/tests/test_host_basename.c")
target_link_libraries(test_host_basename_mutant_stem_transform PRIVATE gabbaboy_host_mutant_stem_transform)
target_compile_features(test_host_basename_mutant_stem_transform PRIVATE c_std_17)
set_target_properties(test_host_basename_mutant_stem_transform PROPERTIES C_EXTENSIONS OFF)
add_test(NAME host_stem_mutant_transform
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:test_host_basename_mutant_stem_transform>;refuse_backslash"
    -DGBB_EXPECT_CODE=1 "-DGBB_EXPECT_REGEX=FAIL refuse_backslash"
    -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")

# ---- D-02: the grammar, one CTest per token (portable: the grammar is parsed before the Windows gate) ----
# Operands are placeholders; no refusal here may reach the filesystem. Each test pins its own token and
# forbids `gbb-host: ready`, so a refusal can neither be reported under another token nor start a run.
function(gbb_add_host_grammar_test name arguments expected)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;${arguments}"
      -DGBB_EXPECT_CODE=2 "-DGBB_EXPECT_REGEX=${expected}" "-DGBB_FORBID_REGEX=gbb-host: ready"
      -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
endfunction()

gbb_add_host_grammar_test(host_grammar_unknown_flag "--rom;r;--save-dir;d;--bogus"
  "invalid-arguments: reason=unknown-flag")
gbb_add_host_grammar_test(host_grammar_duplicate "--rom;a;--rom;b;--save-dir;d"
  "invalid-arguments: reason=duplicate-flag")
gbb_add_host_grammar_test(host_grammar_missing_value "--save-dir;d;--rom"
  "invalid-arguments: reason=missing-value")
gbb_add_host_grammar_test(host_grammar_equals_form "--rom=r;--save-dir;d"
  "invalid-arguments: reason=equals-form")
gbb_add_host_grammar_test(host_grammar_acceptance_flag "--rom;r;--save-dir;d;--suite"
  "invalid-arguments: reason=acceptance-flag")
gbb_add_host_grammar_test(host_grammar_positional "--rom;r;--save-dir;d;extra"
  "invalid-arguments: reason=positional")
gbb_add_host_grammar_test(host_grammar_missing_rom "--save-dir;d;--frames;1"
  "invalid-arguments: reason=missing-rom")
gbb_add_host_grammar_test(host_grammar_missing_save_dir "--rom;r;--frames;1"
  "invalid-arguments: reason=missing-save-dir")
gbb_add_host_grammar_test(host_grammar_bad_profile "--rom;r;--save-dir;d;--profile;gba"
  "invalid-arguments: reason=bad-profile")
gbb_add_host_grammar_test(host_grammar_bad_frames "--rom;r;--save-dir;d;--frames;0"
  "invalid-arguments: reason=bad-frames")

# CMake drops an empty list element, so `--rom ""` cannot be written as a CTest command list. The empty
# operand is passed by the python harness instead; the test is still portable.
gbb_add_host_mode_test(host_grammar_empty_value grammar-empty-value)

# The Windows gate (D-05) is registered on every platform: it must fire on Windows and must not on POSIX.
gbb_add_host_mode_test(host_windows_refusal platform-gate)
