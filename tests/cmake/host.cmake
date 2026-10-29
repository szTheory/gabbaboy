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

# ---- D-04: the host library uses only the public API (POSIX-only: Windows host code is the refusal stub) ----
# The object layer reads the undefined gbb_* symbols of the archive with nm and requires each to be declared
# in the public header; the source layer rejects test-seam and acceptance includes. The controls run the same
# script against a seeded seam-calling archive and a seeded include and require each rejection for its own
# reason. Later plans pass more archives and individual files (GBB_SOURCE_FILES) through the same script.
set(GBB_HOST_API_SCRIPT "${PROJECT_SOURCE_DIR}/cmake/CheckHostApiSymbols.cmake")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${GBB_HOST_API_SCRIPT}")
if(NOT WIN32)
  set(GBB_HOST_API_CONTROL_DIR "${PROJECT_BINARY_DIR}/host-api-controls")
  file(MAKE_DIRECTORY "${GBB_HOST_API_CONTROL_DIR}/include-probe")
  file(WRITE "${GBB_HOST_API_CONTROL_DIR}/seam.c"
    "/* Seeded control: calls a core test seam that the public header does not declare. */\n"
    "int gbb_test_force_state_seam_probe(void);\n"
    "int host_api_seam_call(void) { return gbb_test_force_state_seam_probe(); }\n")
  file(WRITE "${GBB_HOST_API_CONTROL_DIR}/include-probe/bad.c"
    "/* Seeded control: includes the core test seam header. */\n"
    "#include \"gabbaboy_test.h\"\n"
    "int host_api_include_probe(void) { return 0; }\n")
  add_library(host_api_seam_mutant STATIC "${GBB_HOST_API_CONTROL_DIR}/seam.c")
  set_target_properties(host_api_seam_mutant PROPERTIES C_EXTENSIONS OFF)

  add_test(NAME host_api_surface
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_ARCHIVES=$<TARGET_FILE:gabbaboy_host>"
      "-DGBB_HEADER=${PROJECT_SOURCE_DIR}/include/gabbaboy/gabbaboy.h"
      "-DGBB_SOURCE_DIRS=${PROJECT_SOURCE_DIR}/src/host"
      "-DGBB_NM=${CMAKE_NM}"
      -P "${GBB_HOST_API_SCRIPT}")
  set_tests_properties(host_api_surface PROPERTIES
    PASS_REGULAR_EXPRESSION "host-api pass archives=1 symbols=[1-9][0-9]*")

  add_test(NAME host_api_surface_controls
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CONTROL_SEAM_ARCHIVE=$<TARGET_FILE:host_api_seam_mutant>"
      "-DGBB_CONTROL_INCLUDE_DIR=${GBB_HOST_API_CONTROL_DIR}/include-probe"
      "-DGBB_ARCHIVES=$<TARGET_FILE:gabbaboy_host>"
      "-DGBB_HEADER=${PROJECT_SOURCE_DIR}/include/gabbaboy/gabbaboy.h"
      "-DGBB_SOURCE_DIRS=${PROJECT_SOURCE_DIR}/src/host"
      "-DGBB_NM=${CMAKE_NM}"
      -P "${GBB_HOST_API_SCRIPT}")
  set_tests_properties(host_api_surface_controls PROPERTIES
    PASS_REGULAR_EXPRESSION "host-api controls pass controls=2")
endif()

# ---- D-04: every runner and host source is in the GBB_BUILD_QUALIFIED dirty list (portable) ----------------
set(GBB_QUALIFIED_SOURCES_SCRIPT "${PROJECT_SOURCE_DIR}/cmake/CheckRunnerSourcesQualified.cmake")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${GBB_QUALIFIED_SOURCES_SCRIPT}")
set(GBB_QUALIFIED_SOURCES
  "$<JOIN:$<TARGET_PROPERTY:gabbaboy-runner,SOURCES>,|>|$<JOIN:$<TARGET_PROPERTY:gabbaboy_runner_support,SOURCES>,|>|$<JOIN:$<TARGET_PROPERTY:gabbaboy_host,SOURCES>,|>|src/host/gbb_host.h")
add_test(NAME host_qualified_sources
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_ROOT_CMAKELISTS=${PROJECT_SOURCE_DIR}/CMakeLists.txt"
    "-DGBB_SOURCES=${GBB_QUALIFIED_SOURCES}"
    -P "${GBB_QUALIFIED_SOURCES_SCRIPT}")
set_tests_properties(host_qualified_sources PROPERTIES
  PASS_REGULAR_EXPRESSION "qualified-sources pass sources=[1-9][0-9]*")
add_test(NAME host_qualified_sources_control
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_ROOT_CMAKELISTS=${PROJECT_SOURCE_DIR}/CMakeLists.txt;-DGBB_SOURCES=${GBB_QUALIFIED_SOURCES}|src/host/unlisted_probe.c;-P;${GBB_QUALIFIED_SOURCES_SCRIPT}"
    -DGBB_EXPECT_CODE=1 "-DGBB_EXPECT_REGEX=runner-source-unqualified: src/host/unlisted_probe.c"
    -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
