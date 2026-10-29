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
  gbb_add_host_mode_test(host_periodic_flush periodic-flush)
  gbb_add_host_mode_test(host_first_write first-write)
  gbb_add_host_mode_test(host_idempotent_rerun idempotent-rerun)
  gbb_add_host_mode_test(host_sweep_after_checks sweep)
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
      "-DGBB_ARCHIVES=$<TARGET_FILE:gabbaboy_host>;$<TARGET_FILE:gabbaboy_player_slots>"
      "-DGBB_HEADER=${PROJECT_SOURCE_DIR}/include/gabbaboy/gabbaboy.h"
      "-DGBB_SOURCE_DIRS=${PROJECT_SOURCE_DIR}/src/host"
      "-DGBB_SOURCE_FILES=${PROJECT_SOURCE_DIR}/src/player/slots.c;${PROJECT_SOURCE_DIR}/src/player/slots.h"
      "-DGBB_NM=${CMAKE_NM}"
      -P "${GBB_HOST_API_SCRIPT}")
  set_tests_properties(host_api_surface PROPERTIES
    PASS_REGULAR_EXPRESSION "host-api pass archives=2 symbols=[1-9][0-9]*")

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

# ---- D-11: the pure cadence (portable: no clock, no I/O, no core) --------------------------------------------
add_executable(test_host_cadence "${PROJECT_SOURCE_DIR}/tests/test_host_cadence.c")
target_link_libraries(test_host_cadence PRIVATE gabbaboy_host)
target_compile_features(test_host_cadence PRIVATE c_std_17)
set_target_properties(test_host_cadence PROPERTIES C_EXTENSIONS OFF)
foreach(case quiet age rtc_compare generation_compare retry)
  add_test(NAME host_cadence_${case} COMMAND test_host_cadence ${case})
  set_tests_properties(host_cadence_${case} PROPERTIES PASS_REGULAR_EXPRESSION "PASS ${case}")
endforeach()

# gbb_host_cadence_mutant(name anchor replacement case): the cadence test linked against a host library whose
# host_cadence.c has one edit. It must exit 1 with its own `FAIL <case>` line.
function(gbb_host_cadence_mutant name anchor replacement case)
  gbb_host_mutant_library(${name} host_cadence.c "${anchor}" "${replacement}")
  add_executable(test_host_cadence_mutant_${name} "${PROJECT_SOURCE_DIR}/tests/test_host_cadence.c")
  target_link_libraries(test_host_cadence_mutant_${name} PRIVATE gabbaboy_host_mutant_${name})
  target_compile_features(test_host_cadence_mutant_${name} PRIVATE c_std_17)
  set_target_properties(test_host_cadence_mutant_${name} PROPERTIES C_EXTENSIONS OFF)
  add_test(NAME host_cadence_mutant_${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=$<TARGET_FILE:test_host_cadence_mutant_${name}>;${case}"
      -DGBB_EXPECT_CODE=1 "-DGBB_EXPECT_REGEX=FAIL ${case}"
      -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
endfunction()

# `!=` replaced by `>`: a generation that moves backwards is no longer noticed.
gbb_host_cadence_mutant(gt "generation != cadence->observed_generation"
  "generation > cadence->observed_generation" generation_compare)
# `>=` replaced by `>`: the quiet flush fires one frame late.
gbb_host_cadence_mutant(quiet_off_by_one ">= GBB_HOST_QUIET_FRAMES" "> GBB_HOST_QUIET_FRAMES" quiet)

# ---- D-09/D-10: writer fault seams and sweep below the runner (POSIX-only) -----------------------------------
if(NOT WIN32)
  add_executable(test_host_save_io "${PROJECT_SOURCE_DIR}/tests/test_host_save_io.c")
  target_link_libraries(test_host_save_io PRIVATE gabbaboy_host_testing)
  target_compile_definitions(test_host_save_io PRIVATE GBB_HOST_TESTING)
  target_compile_features(test_host_save_io PRIVATE c_std_17)
  set_target_properties(test_host_save_io PROPERTIES C_EXTENSIONS OFF)
  foreach(stage temp write sync close target rename dirsync)
    add_test(NAME host_writer_fault_${stage} COMMAND test_host_save_io fault_${stage})
    set_tests_properties(host_writer_fault_${stage} PROPERTIES PASS_REGULAR_EXPRESSION "PASS fault_${stage}")
  endforeach()
  add_test(NAME host_writer_eio_no_retry COMMAND test_host_save_io eio_no_retry)
  set_tests_properties(host_writer_eio_no_retry PROPERTIES PASS_REGULAR_EXPRESSION "PASS eio_no_retry")
  add_test(NAME host_writer_eexist COMMAND test_host_save_io eexist)
  set_tests_properties(host_writer_eexist PROPERTIES PASS_REGULAR_EXPRESSION "PASS eexist")
  add_test(NAME host_writer_target_not_regular COMMAND test_host_save_io target_not_regular)
  set_tests_properties(host_writer_target_not_regular PROPERTIES PASS_REGULAR_EXPRESSION "PASS target_not_regular")
  add_test(NAME host_sweep_exact_prefix COMMAND test_host_save_io sweep_exact_prefix)
  set_tests_properties(host_sweep_exact_prefix PROPERTIES PASS_REGULAR_EXPRESSION "PASS sweep_exact_prefix")

  gbb_add_host_mode_test(host_rtc_final_compare rtc-final-compare)

  # ---- D-06/D-08/D-30: hostile save-dir, import and --rom shapes through the real runner (POSIX-only: each
  # passes --save-dir, which Windows refuses before any filesystem access, and uses mkfifo/symlink) ----
  gbb_add_host_mode_test(host_savedir_missing savedir-missing)
  gbb_add_host_mode_test(host_savedir_not_directory savedir-not-directory)
  gbb_add_host_mode_test(host_savedir_symlink_path savedir-symlink-path)
  gbb_add_host_mode_test(host_import_exact import-exact)
  gbb_add_host_mode_test(host_import_zero import-zero)
  gbb_add_host_mode_test(host_import_short import-short)
  gbb_add_host_mode_test(host_import_long import-long)
  gbb_add_host_mode_test(host_import_mgba_footer import-mgba-footer)
  gbb_add_host_mode_test(host_import_oversize import-oversize)
  gbb_add_host_mode_test(host_import_bad_rtc import-bad-rtc)
  gbb_add_host_mode_test(host_import_symlink import-symlink)
  gbb_add_host_mode_test(host_import_dangling_symlink import-dangling-symlink)
  gbb_add_host_mode_test(host_import_fifo import-fifo)
  gbb_add_host_mode_test(host_import_directory import-directory)
  gbb_add_host_mode_test(host_import_stray_nobattery import-stray-nobattery)
  gbb_add_host_mode_test(host_rom_fifo rom-fifo)
  gbb_add_host_mode_test(host_rom_directory rom-directory)
  add_test(NAME host_import_device COMMAND test_host_save_io import_device)
  set_tests_properties(host_import_device PROPERTIES PASS_REGULAR_EXPRESSION "PASS import_device")

  # ---- mutant runners (build-tree executables only; nothing mutated is installed) ----
  # gbb_host_mutant_runner(name mutant_library): gabbaboy-runner's main.c linked against a mutant host
  # library instead of gabbaboy_host. The core arrives once, through gabbaboy_runner_support, and it is the
  # NORMAL core: only the host library is mutated. The executable is therefore named `hostvariant`, not
  # `mutant`, because verify-core-linkage.py requires every target named *mutant* to link a mutant core.
  function(gbb_host_mutant_runner name mutant_library)
    add_executable(gabbaboy-runner-hostvariant-${name} "${PROJECT_SOURCE_DIR}/src/runner/main.c")
    target_link_libraries(gabbaboy-runner-hostvariant-${name} PRIVATE gabbaboy_runner_support ${mutant_library})
    target_compile_features(gabbaboy-runner-hostvariant-${name} PRIVATE c_std_17)
    set_target_properties(gabbaboy-runner-hostvariant-${name} PROPERTIES C_EXTENSIONS OFF)
  endfunction()

  # gbb_add_host_mutant_scenario(test runner_target scenario reason): the harness scenario against a mutant
  # runner must exit 1 with its own `FAIL <scenario>: <reason>` line. The reason is part of the pattern, so a
  # harness crash such as a missing runner file ("FAIL <scenario>: FileNotFoundError") cannot satisfy it.
  function(gbb_add_host_mutant_scenario test runner_target scenario reason)
    add_test(NAME ${test}
      COMMAND ${CMAKE_COMMAND}
        "-DGBB_CMD=${Python3_EXECUTABLE};-I;${GBB_HOST_MODE_HARNESS};--runner;$<TARGET_FILE:${runner_target}>;--work;${PROJECT_BINARY_DIR}/host-mode/${test};--scenario;${scenario}"
        -DGBB_EXPECT_CODE=1 "-DGBB_EXPECT_REGEX=FAIL ${scenario}: ${reason}"
        -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
  endfunction()

  # XFER-002 negative: the single import call short-circuits to GBB_OK (0 && x is 0), so the runner never
  # imports and the second process restarts the counter at 01.
  gbb_host_mutant_library(ignore_import host_run.c "gbb_import_battery(" "0 && gbb_import_battery(")
  gbb_host_mutant_runner(ignore_import gabbaboy_host_mutant_ignore_import)
  gbb_add_host_mutant_scenario(host_continuation_mutant_ignore_import
    gabbaboy-runner-hostvariant-ignore_import continuation
    "second run counter is 0x01, expected 0x02")

  # D-06: open_dir first creates the directory, so a missing save dir silently exists.
  gbb_host_mutant_library(mkdir host_save_io.c
    "const int fd = open(path, O_RDONLY | O_DIRECTORY | O_CLOEXEC);"
    "(void)mkdirat(AT_FDCWD, path, 0700);
    const int fd = open(path, O_RDONLY | O_DIRECTORY | O_CLOEXEC);")
  gbb_host_mutant_runner(mkdir gabbaboy_host_mutant_mkdir)
  gbb_add_host_mutant_scenario(host_savedir_mutant_mkdir gabbaboy-runner-hostvariant-mkdir savedir-missing
    "exit 0, expected 2")

  # D-08: the import open follows symlinks, so a link to a valid-size file is accepted.
  gbb_host_mutant_library(follow host_save_io.c "O_RDONLY | O_NOFOLLOW | O_NONBLOCK" "O_RDONLY | O_NONBLOCK")
  gbb_host_mutant_runner(follow gabbaboy_host_mutant_follow)
  gbb_add_host_mutant_scenario(host_import_mutant_follow gabbaboy-runner-hostvariant-follow import-symlink
    "exit [01], expected 2")

  # ---- D-09/T-18-13: no fault seam in any shipped artifact ----
  # The shipped archive and the runner must define no host_save_io_test_ symbol; the same check on the
  # test-seam archive must reject it, so the check cannot pass vacuously.
  add_test(NAME host_no_test_seams_shipped
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_ARCHIVES=$<TARGET_FILE:gabbaboy_host>;$<TARGET_FILE:gabbaboy-runner>"
      "-DGBB_FORBID_DEFINED=host_save_io_test_"
      "-DGBB_HEADER=${PROJECT_SOURCE_DIR}/include/gabbaboy/gabbaboy.h"
      "-DGBB_SOURCE_DIRS=${PROJECT_SOURCE_DIR}/src/host"
      "-DGBB_NM=${CMAKE_NM}"
      -P "${GBB_HOST_API_SCRIPT}")
  set_tests_properties(host_no_test_seams_shipped PROPERTIES PASS_REGULAR_EXPRESSION "host-api pass")
  add_test(NAME host_no_test_seams_shipped_control
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_ARCHIVES=$<TARGET_FILE:gabbaboy_host_testing>;-DGBB_FORBID_DEFINED=host_save_io_test_;-DGBB_HEADER=${PROJECT_SOURCE_DIR}/include/gabbaboy/gabbaboy.h;-DGBB_SOURCE_DIRS=${PROJECT_SOURCE_DIR}/src/host;-DGBB_NM=${CMAKE_NM};-P;${GBB_HOST_API_SCRIPT}"
      -DGBB_EXPECT_CODE=1 "-DGBB_EXPECT_REGEX=host-test-seam-shipped: _?host_save_io_test_fail_next"
      -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
endif()
