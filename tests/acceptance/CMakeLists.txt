# Pulled in with include() from tests/CMakeLists.txt (not add_subdirectory):
# cmake/ExpectedTests.cmake reads the tests directory's TESTS property only.
add_executable(test_acceptance_lib ${CMAKE_CURRENT_LIST_DIR}/../test_acceptance_lib.c)
target_link_libraries(test_acceptance_lib PRIVATE gabbaboy_accept)
target_compile_features(test_acceptance_lib PRIVATE c_std_17)
set_target_properties(test_acceptance_lib PROPERTIES C_EXTENSIONS OFF)

set(GBB_ACCEPT_LIBBET_ROM ${PROJECT_SOURCE_DIR}/fixtures/libbet/libbet.gb)
set(GBB_ACCEPT_LIBBET_SCRIPT ${CMAKE_CURRENT_LIST_DIR}/inputs/libbet-tutorial.input)

add_test(NAME acceptance_lib_libbet_replay
  COMMAND test_acceptance_lib acceptance_lib_libbet_replay
          ${GBB_ACCEPT_LIBBET_ROM} ${GBB_ACCEPT_LIBBET_SCRIPT})
set_tests_properties(acceptance_lib_libbet_replay PROPERTIES TIMEOUT 300)

foreach(case acceptance_parse_script_bounds acceptance_parse_script_errors)
  add_test(NAME ${case} COMMAND test_acceptance_lib ${case})
  set_tests_properties(${case} PROPERTIES TIMEOUT 30)
endforeach()

add_test(NAME acceptance_predicate_truth_table COMMAND test_acceptance_lib acceptance_predicate_truth_table)
add_test(NAME acceptance_predicate_anchors
  COMMAND test_acceptance_lib acceptance_predicate_anchors ${GBB_ACCEPT_LIBBET_ROM})
set_tests_properties(acceptance_predicate_truth_table acceptance_predicate_anchors PROPERTIES TIMEOUT 30)

# Runner acceptance case (D-23, D-28): paths in cases.txt resolve against the working directory,
# so every acceptance CTest runs from the repository root.
string(REPEAT "[0-9a-f]" 64 gbb_hex64_re)
add_test(NAME acceptance_libbet
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--acceptance;tests/acceptance/cases.txt;--case;libbet;--receipt"
    -DGBB_EXPECT_CODE=0
    "-DGBB_EXPECT_REGEX=acceptance id=libbet status=pass.*frame_hit=${gbb_hex64_re}.*pcm_sha256=${gbb_hex64_re}"
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(acceptance_libbet PROPERTIES TIMEOUT 300 WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

# --observe prints sorted key<TAB>value lines instead of pass/fail (D-23). CMake regexes have no
# counted repetition, so the 64-digit digest pattern is built by repetition.
add_test(NAME acceptance_libbet_observe
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--acceptance;tests/acceptance/cases.txt;--case;libbet;--observe"
    -DGBB_EXPECT_CODE=0
    "-DGBB_EXPECT_REGEX=acceptance[.]libbet[.]pcm_sha256\t${gbb_hex64_re}"
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(acceptance_libbet_observe PROPERTIES TIMEOUT 300 WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

# A failure directory that is a regular file cannot be probe-written: exit 2 before any guest work.
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/failure-dir-is-a-file "not a directory\n")
add_test(NAME acceptance_failure_dir_unwritable
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--acceptance;tests/acceptance/cases.txt;--case;libbet;--failure-dir;${CMAKE_CURRENT_BINARY_DIR}/failure-dir-is-a-file"
    -DGBB_EXPECT_CODE=2
    "-DGBB_EXPECT_REGEX=reason=failure-dir-unwritable"
    "-DGBB_FORBID_REGEX=status=(pass|fail|unsupported)"
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(acceptance_failure_dir_unwritable PROPERTIES TIMEOUT 30 WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

# Runner-level negative case files (D-28, T-07-34): each is rejected with exact exit 2 and its own
# reason, and the output must carry no pass/fail/unsupported status line, which proves the case was
# rejected before any guest instance existed.
set(GBB_NEGATIVE_DIR ${CMAKE_CURRENT_LIST_DIR}/negative)
# 65537 bytes: one over the 64 KiB case-file cap. Generated so no oversize blob is committed.
string(REPEAT "#" 65537 gbb_oversize_content)
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/oversize-cases.txt "${gbb_oversize_content}")

function(gbb_add_negative name cases_path reason_regex)
  add_test(NAME acceptance_negative_${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--acceptance;${cases_path};--case;libbet"
      -DGBB_EXPECT_CODE=2
      "-DGBB_EXPECT_REGEX=${reason_regex}"
      "-DGBB_FORBID_REGEX=status=(pass|fail|unsupported)"
      -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(acceptance_negative_${name} PROPERTIES TIMEOUT 30 WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})
endfunction()

gbb_add_negative(flipped_digest tests/acceptance/negative/flipped-digest.txt "reason=rom-digest-mismatch")
gbb_add_negative(bad_script tests/acceptance/negative/bad-script.txt "invalid-script: line 3:")
gbb_add_negative(duplicate_id tests/acceptance/negative/duplicate-id.txt "invalid-cases: duplicate-id")
gbb_add_negative(unknown_key tests/acceptance/negative/unknown-key.txt "invalid-cases: unknown-key")
gbb_add_negative(path_traversal tests/acceptance/negative/path-traversal.txt "invalid-cases: bad-path")
gbb_add_negative(altered_input tests/acceptance/negative/altered-input.txt "reason=input-digest-mismatch")
gbb_add_negative(oversize ${CMAKE_CURRENT_BINARY_DIR}/oversize-cases.txt "invalid-cases: file-too-large")

# Case-file parser and path validator boundary matrix (D-21, D-28).
add_executable(test_acceptance_cases ${CMAKE_CURRENT_LIST_DIR}/../test_acceptance_cases.c)
target_link_libraries(test_acceptance_cases PRIVATE gabbaboy_runner_support)
target_compile_features(test_acceptance_cases PRIVATE c_std_17)
set_target_properties(test_acceptance_cases PROPERTIES C_EXTENSIONS OFF)
foreach(case acceptance_parse_cases_bounds acceptance_parse_cases_errors acceptance_parse_paths
             acceptance_unknown_model_refused)
  add_test(NAME ${case} COMMAND test_acceptance_cases ${case})
  set_tests_properties(${case} PROPERTIES TIMEOUT 30)
endforeach()

# Independent stdlib confirmation of the D-24 frame digest, the PPM bytes and the D-16 PCM digest.
add_executable(test_acceptance_digest ${CMAKE_CURRENT_LIST_DIR}/../test_acceptance_digest.c)
target_link_libraries(test_acceptance_digest PRIVATE gabbaboy_accept)
target_compile_features(test_acceptance_digest PRIVATE c_std_17)
set_target_properties(test_acceptance_digest PROPERTIES C_EXTENSIONS OFF)
add_test(NAME acceptance_digest_vectors
  COMMAND ${Python3_EXECUTABLE} -I ${PROJECT_SOURCE_DIR}/tests/scripts/rgb-digest-vector.py
          --check $<TARGET_FILE:test_acceptance_digest>
          --ppm ${CMAKE_CURRENT_BINARY_DIR}/digest-vector.ppm)
set_tests_properties(acceptance_digest_vectors PROPERTIES TIMEOUT 30)
# D-15 / D-43: the GBB-RGB555LE-v1 digest, padding, 0x8000 rejection and channel expansion against Python.
add_test(NAME acceptance_digest_rgb555_vectors
  COMMAND ${Python3_EXECUTABLE} -I ${PROJECT_SOURCE_DIR}/tests/scripts/rgb-digest-vector.py
          --rgb555 --check $<TARGET_FILE:test_acceptance_digest>
          --ppm ${CMAKE_CURRENT_BINARY_DIR}/digest-vector-rgb555.ppm)
set_tests_properties(acceptance_digest_rgb555_vectors PROPERTIES TIMEOUT 30)

# Model applicability and declared-exclusion suite semantics (D-22). Exclusions exit 4 with their own
# reason; the CTest skip-return-code mechanism is never used, so an excluded case can never read as a skip.
function(gbb_add_acceptance_exit name code regex timeout)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;${ARGN}"
      -DGBB_EXPECT_CODE=${code}
      "-DGBB_EXPECT_REGEX=${regex}"
      -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT ${timeout} WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})
endfunction()

set(GBB_CASES tests/acceptance/cases.txt)
set(GBB_SUITE_EXCLUSION tests/acceptance/negative/suite-exclusion.txt)
gbb_add_acceptance_exit(acceptance_libbet_excluded_cgb-cpu-e 4
  "status=excluded reason=unsupported-model" 30
  "--acceptance;${GBB_CASES};--case;libbet;--model;cgb-cpu-e")
gbb_add_acceptance_exit(acceptance_libbet-cgb-only_excluded_dmg-cpu-b 4
  "status=excluded reason=unsupported-model" 30
  "--acceptance;${GBB_SUITE_EXCLUSION};--case;libbet-cgb-only")
gbb_add_acceptance_exit(acceptance_suite 0
  "suite eligible=3 executed=3 excluded=0 xfail=2 status=pass" 300
  "--acceptance;${GBB_CASES};--suite;--expect-excluded;0;--receipt")

# Discrimination controls (GAME-02, D-14). Two separate assertions per control, neither replacing the
# other: the raw verdict (--raw-verdict) must exit 1 with reason=predicate-not-reached, and the D-22
# strict-xfail layer must map exactly that outcome to status=xfail exit 0. Any other reason, or a
# pass (unexpected-pass), would fail the xfail test. The receipt's final_* fields show what state the
# guest reached; SELECT reaches attract mode ($C580=$04) but never the cleared tutorial.
gbb_add_acceptance_exit(acceptance_libbet-no-input_raw 1
  "status=fail model=dmg-cpu-b reason=predicate-not-reached" 300
  "--acceptance;${GBB_CASES};--case;libbet-no-input;--raw-verdict;--receipt")
gbb_add_acceptance_exit(acceptance_libbet-select_raw 1
  "status=fail model=dmg-cpu-b reason=predicate-not-reached.*final_attract=04" 300
  "--acceptance;${GBB_CASES};--case;libbet-select;--raw-verdict;--receipt")
gbb_add_acceptance_exit(acceptance_libbet-no-input 0
  "status=xfail model=dmg-cpu-b reason=predicate-not-reached" 300
  "--acceptance;${GBB_CASES};--case;libbet-no-input;--receipt")
gbb_add_acceptance_exit(acceptance_libbet-select 0
  "status=xfail model=dmg-cpu-b reason=predicate-not-reached.*final_attract=04" 300
  "--acceptance;${GBB_CASES};--case;libbet-select;--receipt")

gbb_add_acceptance_exit(acceptance_suite_declared_exclusion 0
  "suite eligible=1 executed=1 excluded=1 xfail=0 status=pass" 300
  "--acceptance;${GBB_SUITE_EXCLUSION};--suite;--expect-excluded;1")
gbb_add_acceptance_exit(acceptance_suite_undeclared_exclusion 1
  "reason=excluded-count-mismatch expected=0 observed=1" 300
  "--acceptance;${GBB_SUITE_EXCLUSION};--suite;--expect-excluded;0")
gbb_add_acceptance_exit(acceptance_suite_missing_expect_excluded 2
  "reason=expect-excluded-required" 30
  "--acceptance;${GBB_CASES};--suite")
set(GBB_APPLICABILITY tests/acceptance/negative/applicability.txt)
gbb_add_acceptance_exit(acceptance_target_revision_excluded 4
  "status=excluded reason=target-revision" 30
  "--acceptance;${GBB_APPLICABILITY};--case;libbet-rev-x")
gbb_add_acceptance_exit(acceptance_unexpected_pass 1
  "status=unexpected-pass" 300
  "--acceptance;${GBB_APPLICABILITY};--case;libbet-unexpected-pass")
gbb_add_acceptance_exit(acceptance_unknown_model 2
  "reason=unknown-model" 30
  "--acceptance;${GBB_CASES};--case;libbet;--model;z80")
gbb_add_acceptance_exit(acceptance_observe_only_flag 2
  "reason=observe-only-flag" 30
  "--acceptance;${GBB_CASES};--case;libbet;--pcm-digest")
# A parser-valid script denser than the core's 64-event queue (80 one-half-dot taps) used to stop with
# event-delivery-failed (exit 3). Plan 15.1-02 lends the adapter's immutable event span to the core, so the
# same script is now delivered in full: the observation completes and neither delivery nor drive failure
# is reported. The no-refill source mutant, the frozen-baseline comparison and the stale-limit control are
# executed by acceptance_dense_input_controls below, which is what makes this test discriminating.
add_test(NAME acceptance_dense_script_delivered
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--acceptance;${GBB_CASES};--case;libbet;--observe;--input-script;tests/acceptance/inputs/dense-taps.input"
    -DGBB_EXPECT_CODE=0
    "-DGBB_EXPECT_REGEX=acceptance[.]libbet[.]class\tregression"
    "-DGBB_FORBID_REGEX=event-delivery-failed|drive-error|status=(fail|error)"
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
# The dense script is now delivered in full, so this is a full-length observation (107 s under ASan in a quiet
# Linux container), not the quick failure it used to be; a hosted sanitizer runner under parallel load needs far more.
set_tests_properties(acceptance_dense_script_delivered PROPERTIES TIMEOUT 400 COST 400 WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})
add_test(NAME acceptance_dense_input_controls
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${Python3_EXECUTABLE};-I;${PROJECT_SOURCE_DIR}/tests/scripts/verify-dense-input.py;--self-test;--build-dir;${PROJECT_BINARY_DIR}"
    -DGBB_EXPECT_CODE=0
    "-DGBB_EXPECT_REGEX=dense-input status=pass.*dense-input baseline=pass.*documentation-contract=pass stale-limit-control=pass.*failure-diagnostic=pass.*no-refill-mutant=failed-as-expected reason=predicate-not-reached"
    "-DGBB_FORBID_REGEX=no-refill-mutant=passed"
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(acceptance_dense_input_controls PROPERTIES TIMEOUT 600 COST 600 WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

# Private borrowed-span controls from plans 15.1-02 (core fixes 929ce2e and 73d8a53). They drive the
# private run entry points through the real core, so each one is registered here and is paired below with a
# core source mutant that removes exactly the fix it guards.
foreach(gbb_span_case acceptance_drive_dense_queue acceptance_drive_batch_order
    acceptance_drive_stop_guard_failure acceptance_input_span_edges
    acceptance_drive_stop_wake_deadline acceptance_input_span_output_alias
    acceptance_replay_stop_resume_parity acceptance_drive_stop_resume_main)
  add_test(NAME ${gbb_span_case} COMMAND test_acceptance_lib ${gbb_span_case})
  set_tests_properties(${gbb_span_case} PROPERTIES TIMEOUT 60 WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}
    PASS_REGULAR_EXPRESSION "PASS ${gbb_span_case}")
endforeach()

# Each mutant is the real core with one anchored source edit. The core-free helper library comes first and
# the mutant is the only core on the link line (verify-core-linkage.py checks that). The failing run must
# exit 1 with the intended diagnostic; a sibling control on the same executable must still pass, so a
# mutant that simply fails to run cannot satisfy the pair.
set(GBB_SPAN_CORE_PATH "${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${GBB_SPAN_CORE_PATH})
file(READ ${GBB_SPAN_CORE_PATH} gbb_span_core_text)
function(gbb_span_core_mutant name anchor replacement)
  string(FIND "${gbb_span_core_text}" "${anchor}" first)
  string(FIND "${gbb_span_core_text}" "${anchor}" final REVERSE)
  if(first EQUAL -1 OR NOT first EQUAL final)
    message(FATAL_ERROR "span mutant ${name}: anchor must occur exactly once in ${GBB_SPAN_CORE_PATH} "
      "(first=${first} last=${final})")
  endif()
  string(REPLACE "${anchor}" "${replacement}" text "${gbb_span_core_text}")
  set(source ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_span_mutant_${name}.c)
  file(WRITE ${source} "${text}")
  set(library gabbaboy_core_span_mutant_${name})
  add_library(${library} STATIC ${source})
  target_include_directories(${library}
    PUBLIC ${PROJECT_SOURCE_DIR}/include
    PRIVATE ${PROJECT_SOURCE_DIR}/src/core)
  target_compile_features(${library} PUBLIC c_std_17)
  set_target_properties(${library} PROPERTIES C_EXTENSIONS OFF)
  target_compile_definitions(${library} PRIVATE
    GBB_BUILD_REVISION="span-mutant-${name}" GBB_BUILD_QUALIFIED=0)
endfunction()
function(gbb_span_mutant_test target_name driver_source uses_accept fail_test control_test
    failing_case failing_regex control_case)
  add_executable(${target_name} ${driver_source})
  target_compile_features(${target_name} PRIVATE c_std_17)
  set_target_properties(${target_name} PROPERTIES C_EXTENSIONS OFF)
  set(library ${ARGV8})
  set(control_regex ${ARGV9})
  if(uses_accept)
    target_link_libraries(${target_name} PRIVATE gabbaboy_accept_bare ${library})
  else()
    target_link_libraries(${target_name} PRIVATE ${library})
  endif()
  add_test(NAME ${fail_test}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=$<TARGET_FILE:${target_name}>;${failing_case}"
      -DGBB_EXPECT_CODE=1
      "-DGBB_EXPECT_REGEX=${failing_regex}"
      "-DGBB_FORBID_REGEX=PASS ${failing_case}"
      -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  add_test(NAME ${control_test}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=$<TARGET_FILE:${target_name}>;${control_case}"
      -DGBB_EXPECT_CODE=0
      "-DGBB_EXPECT_REGEX=${control_regex}"
      "-DGBB_FORBID_REGEX=not ok"
      -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${fail_test} ${control_test} PROPERTIES TIMEOUT 60)
  # The mutant trips a REQUIRE that returns early without destroying its instance; leak detection stays
  # on for the controls and for every other test.
  set_tests_properties(${fail_test} PROPERTIES ENVIRONMENT "ASAN_OPTIONS=detect_leaks=0")
endfunction()

# 929ce2e/73d8a53: a STOP wake that lands exactly on a private run's deadline reports GBB_STOP_BUDGET only
# while a span is borrowed. Dropping the private result restores the pre-fix classification (stopped).
set(GBB_SPAN_WAKE_ANCHOR "result.reason = instance->accept_input_span != NULL\n                    ? GBB_STOP_BUDGET : GBB_STOP_NO_PROGRESS;")
gbb_span_core_mutant(wake_private_result "${GBB_SPAN_WAKE_ANCHOR}" "result.reason = GBB_STOP_NO_PROGRESS;")
gbb_span_mutant_test(test_acceptance_lib_mutant_wake_private_result
  ${CMAKE_CURRENT_LIST_DIR}/../test_acceptance_lib.c TRUE
  acceptance_drive_mutant_wake_private_result acceptance_drive_mutant_wake_private_result_control
  acceptance_drive_stop_wake_deadline "wake-at-deadline" acceptance_input_span_edges
  gabbaboy_core_span_mutant_wake_private_result "PASS acceptance_input_span_edges")
# The public contract (tests/test_events.c event_stop_wake) keeps GBB_STOP_NO_PROGRESS at the boundary; a
# core that returns the budget result for every caller breaks it and must be caught by that unchanged test.
gbb_span_core_mutant(wake_all_budget "${GBB_SPAN_WAKE_ANCHOR}" "result.reason = GBB_STOP_BUDGET;")
gbb_span_mutant_test(test_events_mutant_wake_all_budget
  ${PROJECT_SOURCE_DIR}/tests/test_events.c FALSE
  event_stop_wake_mutant_all_budget event_stop_wake_mutant_all_budget_control
  event_stop_wake "r[.]reason == GBB_STOP_NO_PROGRESS" event_boundary
  gabbaboy_core_span_mutant_wake_all_budget ".*")
# 929ce2e: borrowed-span outputs must not overlap the span, its events or its cursor. Treating every
# non-null output as disjoint removes the check, and the 10 aliasing calls are then all accepted.
gbb_span_core_mutant(output_alias "    if (span == NULL) return 1;"
  "    if (span == NULL || output != NULL) return 1;")
gbb_span_mutant_test(test_acceptance_lib_mutant_output_alias
  ${CMAKE_CURRENT_LIST_DIR}/../test_acceptance_lib.c TRUE
  acceptance_drive_mutant_output_alias acceptance_drive_mutant_output_alias_control
  acceptance_input_span_output_alias "span-output alias rejected=[0-9]/10" acceptance_input_span_edges
  gabbaboy_core_span_mutant_output_alias "PASS acceptance_input_span_edges")
gbb_add_acceptance_exit(acceptance_suite_invalid_expect_excluded 2
  "reason=invalid-expect-excluded" 30
  "--acceptance;${GBB_CASES};--suite;--expect-excluded;x1")

# LD B,B frame capture controls (EVID-01, D-24, D-26). ldbb-controls.txt may only carry the stdlib
# uniform-3 digest as a reference, so a digest captured from this emulator cannot be committed there
# as an oracle. The check runs at configure time and fails the configure, not a test.
execute_process(
  COMMAND ${Python3_EXECUTABLE} -I ${PROJECT_SOURCE_DIR}/tests/scripts/rgb-digest-vector.py --uniform 3
  OUTPUT_VARIABLE gbb_uniform3_digest RESULT_VARIABLE gbb_uniform3_rc OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT gbb_uniform3_rc EQUAL 0 OR NOT gbb_uniform3_digest MATCHES "^[0-9a-f]+$")
  message(FATAL_ERROR "rgb-digest-vector.py --uniform 3 failed (rc=${gbb_uniform3_rc})")
endif()
set(GBB_LDBB_CONTROLS tests/acceptance/ldbb-controls.txt)
set(GBB_LDBB_CONTROLS_FILE ${PROJECT_SOURCE_DIR}/${GBB_LDBB_CONTROLS})
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${GBB_LDBB_CONTROLS_FILE})
file(STRINGS ${GBB_LDBB_CONTROLS_FILE} gbb_ldbb_lines REGEX "reference_digest=")
set(gbb_ldbb_refs 0)
foreach(gbb_line IN LISTS gbb_ldbb_lines)
  if(gbb_line MATCHES "^#")
    continue()
  endif()
  string(REGEX MATCH "reference_digest=([^ ]*)" gbb_unused "${gbb_line}")
  if(NOT "${CMAKE_MATCH_1}" STREQUAL "${gbb_uniform3_digest}")
    message(FATAL_ERROR "${GBB_LDBB_CONTROLS_FILE}: reference_digest ${CMAKE_MATCH_1} is not the stdlib "
      "rgb-digest-vector.py --uniform 3 digest ${gbb_uniform3_digest} (D-26: no self-captured references)")
  endif()
  math(EXPR gbb_ldbb_refs "${gbb_ldbb_refs} + 1")
endforeach()
if(gbb_ldbb_refs EQUAL 0)
  message(FATAL_ERROR "${GBB_LDBB_CONTROLS_FILE}: no reference_digest found")
endif()

gbb_add_acceptance_exit(acceptance_ldbb_observe_daa 0
  "acceptance[.]daa-ldbb[.]checkpoint[.]ldbb[.]frame\t${gbb_hex64_re}\nacceptance[.]daa-ldbb[.]class\tregression" 30
  "--acceptance;${GBB_LDBB_CONTROLS};--case;daa-ldbb;--observe")

# Control flags do not apply to frame-digest cases and are refused, never silently ignored (WR-04).
gbb_add_acceptance_exit(acceptance_ldbb_mutate_rejected 2
  "reason=mutate-not-applicable" 30
  "--acceptance;${GBB_LDBB_CONTROLS};--case;daa-ldbb;--mutate;drop:START")
gbb_add_acceptance_exit(acceptance_ldbb_raw_verdict_rejected 2
  "reason=mutate-not-applicable" 30
  "--acceptance;${GBB_LDBB_CONTROLS};--case;daa-ldbb;--raw-verdict")

# Image on failure only (EVID-01): a mismatching LD B,B frame writes <failure-dir>/<id>.ppm, a 15-byte
# P6 header plus 160*144*3 pixel bytes. Each failure-writing test owns its directory.
set(GBB_LDBB_FAIL_DIR ${PROJECT_BINARY_DIR}/acceptance-failures/acceptance_ldbb_mismatch_ppm)
file(MAKE_DIRECTORY ${GBB_LDBB_FAIL_DIR})
add_test(NAME acceptance_ldbb_mismatch_ppm
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--acceptance;${GBB_LDBB_CONTROLS};--case;daa-ldbb;--failure-dir;${GBB_LDBB_FAIL_DIR}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=reason=frame-mismatch class=regression observed=${gbb_hex64_re}"
    -DGBB_EXPECT_FILE=${GBB_LDBB_FAIL_DIR}/daa-ldbb.ppm
    -DGBB_EXPECT_FILE_SIZE=69135
    -DGBB_EXPECT_FILE_FRESH=1
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(acceptance_ldbb_mismatch_ppm PROPERTIES TIMEOUT 30 WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

gbb_add_acceptance_exit(acceptance_ldbb_not_ready 1
  "reason=frame-not-ready" 30
  "--acceptance;${GBB_LDBB_CONTROLS};--case;tim00-ldbb")

# Mooneye --observe shares gbb_runner_capture_ldbb; a breakpoint reached before the first completed
# frame is the explicit token not-ready, an observation rather than an error (Open Question 1).
gbb_add_acceptance_exit(acceptance_ldbb_mooneye_observe 0
  "mooneye[.]daa[.]frame\t${gbb_hex64_re}.*mooneye[.]tim00[.]frame\tnot-ready.*mooneye[.]tim00-div-trigger[.]frame\tnot-ready" 60
  "--manifest;fixtures/mooneye/manifest.json;--suite;--observe")

# Dropped-START control (D-14, N3): every START event is removed before the run, so the tutorial can
# never leave the title and the gate must exit 1 with the predicate unreached.
gbb_add_acceptance_exit(acceptance_libbet_drop_start 1
  "reason=predicate-not-reached.*mutate=drop:START" 300
  "--acceptance;${GBB_CASES};--case;libbet;--mutate;drop:START;--receipt")

# SGB tolerance (D-17): Libbet runs detect_sgb on every DMG boot. The receipt of the passing run carries
# the hw_capability value at frame 90 and the number of FF00 reset pulses (a select-bits 00 write
# later followed by a select-bits 11 write) seen by a deterministic diagnostics replay of those 90
# frames, so a detection path that ran and was tolerated is observable rather than assumed.
gbb_add_acceptance_exit(acceptance_sgb_tolerance 0
  "hw_f90=00 sgb_reset_pulses=[1-9]" 300
  "--acceptance;${GBB_CASES};--case;libbet;--receipt")

# Bounded stall report (D-18): a failing run with --failure-dir replays to its final frame window and writes
# <id>.stall.txt (last 4096 trace records, last 64 writes to FF00/FF0F/FFFF/FF40/FF41, an 8-entry PC
# histogram), capped at 65536 bytes. The D-24 failure PPM is written next to it by the same failing run
# (owner amendment of D-18: the cap applies to the text report, plus one 69,135-byte final-frame image).
set(GBB_STALL_FAIL_DIR ${PROJECT_BINARY_DIR}/acceptance-failures/acceptance_stall_diagnosis)
file(MAKE_DIRECTORY ${GBB_STALL_FAIL_DIR})
# Each of the two replays has its own child deadline. Main ran one replay in 529 s on a hosted ASan/UBSan runner;
# on the Phase 15.1 head one replay exceeded 900 s under the sanitizer lane's parallel load (a quiet Linux ASan
# container measured 186 s on main and 204 s here, one sample each). The sanitizer deadline is therefore 1800 s
# and the TIMEOUT property below (scaled by 3 for sanitizers, two replays) leaves room for both; other builds keep 300 s.
set(GBB_STALL_RUNNER_TIMEOUT 300)
if(GABBABOY_ENABLE_SANITIZERS)
  set(GBB_STALL_RUNNER_TIMEOUT 1800)
endif()
add_test(NAME acceptance_stall_diagnosis
  COMMAND ${Python3_EXECUTABLE} -I ${PROJECT_SOURCE_DIR}/tests/scripts/verify-stall-report.py
    --runner-timeout ${GBB_STALL_RUNNER_TIMEOUT}
    --runner $<TARGET_FILE:gabbaboy-runner>
    --cases ${PROJECT_SOURCE_DIR}/${GBB_CASES}
    --workdir ${PROJECT_SOURCE_DIR}
    --failure-dir ${GBB_STALL_FAIL_DIR})
# COST makes a parallel ctest start the longest tests first, so a sanitizer lane with a 45 minute job limit does
# not leave the two stall replays as its tail (they ended the lane at about 41 minutes when they started last).
set_tests_properties(acceptance_stall_diagnosis PROPERTIES TIMEOUT 1200 COST 1200 WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

# Core mutant (D-14): a copy of the core whose JOYP direction/button select test is inverted, built into a
# test-only static library and runner. The source line is the single anchor guaranteed by Plans 07-03 and
# 07-17; if it moves or repeats, configure fails rather than silently building an unmutated "mutant".
# Nothing here is installed, exported or linked into GabbaBoy::core.
set(GBB_MUTANT_SOURCE ${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c)
set(GBB_MUTANT_PATTERN "if ((m->joypad_select & 0x20u) == 0)")
set(GBB_MUTANT_REPLACEMENT "if ((m->joypad_select & 0x20u) != 0)")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${GBB_MUTANT_SOURCE})
file(READ ${GBB_MUTANT_SOURCE} gbb_core_text)
string(FIND "${gbb_core_text}" "${GBB_MUTANT_PATTERN}" gbb_mutant_first)
string(FIND "${gbb_core_text}" "${GBB_MUTANT_PATTERN}" gbb_mutant_last REVERSE)
if(gbb_mutant_first EQUAL -1 OR NOT gbb_mutant_first EQUAL gbb_mutant_last)
  message(FATAL_ERROR "core-mutant pattern '${GBB_MUTANT_PATTERN}' must occur exactly once in "
    "${GBB_MUTANT_SOURCE} (first=${gbb_mutant_first} last=${gbb_mutant_last})")
endif()
# The core text carries semicolons, so it stays quoted and never enters a list operation.
string(REPLACE "${GBB_MUTANT_PATTERN}" "${GBB_MUTANT_REPLACEMENT}" gbb_mutant_text "${gbb_core_text}")
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_joyp_mutant.c "${gbb_mutant_text}")

add_library(gabbaboy_core_joyp_mutant STATIC ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_joyp_mutant.c)
target_include_directories(gabbaboy_core_joyp_mutant PUBLIC ${PROJECT_SOURCE_DIR}/include)
target_compile_features(gabbaboy_core_joyp_mutant PUBLIC c_std_17)
set_target_properties(gabbaboy_core_joyp_mutant PROPERTIES C_EXTENSIONS OFF)
target_compile_definitions(gabbaboy_core_joyp_mutant PRIVATE
  GBB_BUILD_REVISION="joyp-mutant" GBB_BUILD_QUALIFIED=0)

add_executable(gabbaboy-runner-joyp-mutant
  ${PROJECT_SOURCE_DIR}/src/runner/main.c
  ${PROJECT_SOURCE_DIR}/src/runner/cases.c
  ${PROJECT_SOURCE_DIR}/src/runner/acceptance.c
  ${PROJECT_SOURCE_DIR}/src/accept/sha256.c
  ${PROJECT_SOURCE_DIR}/src/accept/input_script.c
  ${PROJECT_SOURCE_DIR}/src/accept/stepper.c
  ${PROJECT_SOURCE_DIR}/src/accept/predicate.c
  ${PROJECT_SOURCE_DIR}/src/accept/digest.c)
target_include_directories(gabbaboy-runner-joyp-mutant PRIVATE
  ${PROJECT_SOURCE_DIR}/src/runner ${PROJECT_SOURCE_DIR}/src/accept)
target_link_libraries(gabbaboy-runner-joyp-mutant PRIVATE gabbaboy_core_joyp_mutant)
target_compile_features(gabbaboy-runner-joyp-mutant PRIVATE c_std_17)
set_target_properties(gabbaboy-runner-joyp-mutant PROPERTIES C_EXTENSIONS OFF)
target_compile_definitions(gabbaboy-runner-joyp-mutant PRIVATE
  GBB_BUILD_REVISION="joyp-mutant" GBB_BUILD_QUALIFIED=0)

add_test(NAME acceptance_core_mutant
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner-joyp-mutant>;--acceptance;${GBB_CASES};--case;libbet;--receipt"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=reason=predicate-not-reached"
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(acceptance_core_mutant PROPERTIES TIMEOUT 300 WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

# Runner model<->profile mapping (D-25, Plan 10-03). One mapping drives the create call and the printed
# label, so a CGB request is excluded or reported under a CGB label and never runs as, or reads as, DMG.
set(GBB_MOONEYE_MANIFEST fixtures/mooneye/manifest.json)
gbb_add_acceptance_exit(cgb_runner_profile_manifest_cgb_excluded 4
  "mooneye.daa status=excluded reason=unsupported-model profile=CGB-CPU-E" 30
  "--manifest;${GBB_MOONEYE_MANIFEST};--case;daa;--receipt;--profile;cgb")
set_tests_properties(cgb_runner_profile_manifest_cgb_excluded PROPERTIES
  FAIL_REGULAR_EXPRESSION "DMG-CPU-B|dmg-cpu-b")
gbb_add_acceptance_exit(cgb_runner_profile_unknown 2 "reason=unknown-profile" 30
  "--manifest;${GBB_MOONEYE_MANIFEST};--case;daa;--profile;gbc")
gbb_add_acceptance_exit(cgb_runner_profile_model_conflict 2 "reason=profile-model-conflict" 30
  "--acceptance;${GBB_CASES};--case;libbet;--profile;dmg;--model;cgb-cpu-e")
gbb_add_acceptance_exit(cgb_runner_profile_acceptance_cgb_excluded 4
  "status=excluded reason=unsupported-model model=cgb-cpu-e" 30
  "--acceptance;${GBB_CASES};--case;libbet;--profile;cgb")
set_tests_properties(cgb_runner_profile_acceptance_cgb_excluded PROPERTIES
  FAIL_REGULAR_EXPRESSION "dmg-cpu-b|DMG-CPU-B")

# DMG output with an explicit --profile dmg is byte-identical to output without it.
add_test(NAME cgb_runner_profile_dmg_identity_mooneye
  COMMAND ${CMAKE_COMMAND}
    -DGBB_RUNNER=$<TARGET_FILE:gabbaboy-runner>
    "-DGBB_ARGS=--manifest;${GBB_MOONEYE_MANIFEST};--suite;--receipt"
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/runner_profile_identity.cmake)
add_test(NAME cgb_runner_profile_dmg_identity_acceptance
  COMMAND ${CMAKE_COMMAND}
    -DGBB_RUNNER=$<TARGET_FILE:gabbaboy-runner>
    "-DGBB_ARGS=--acceptance;${GBB_CASES};--case;libbet;--receipt"
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/runner_profile_identity.cmake)
set_tests_properties(cgb_runner_profile_dmg_identity_mooneye PROPERTIES TIMEOUT 120
  PASS_REGULAR_EXPRESSION "profile-identity pass bytes=[1-9]" WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})
set_tests_properties(cgb_runner_profile_dmg_identity_acceptance PROPERTIES TIMEOUT 300
  PASS_REGULAR_EXPRESSION "profile-identity pass bytes=[1-9]" WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})
# Negative control: the comparison must reject a run pair that is not a clean DMG baseline (the baseline
# run is a CGB-excluded case, exit 4), so the identity script cannot pass vacuously.
add_test(NAME cgb_runner_profile_dmg_identity_negative
  COMMAND ${CMAKE_COMMAND}
    -DGBB_RUNNER=$<TARGET_FILE:gabbaboy-runner>
    "-DGBB_ARGS=--acceptance;${GBB_CASES};--case;libbet;--model;cgb-cpu-e"
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/runner_profile_identity.cmake)
set_tests_properties(cgb_runner_profile_dmg_identity_negative PROPERTIES TIMEOUT 30
  PASS_REGULAR_EXPRESSION "profile-identity-baseline-failed|profile-identity-mismatch" WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})

# --- Phase 11 plan 11-09 begin ---
# CGB frame-digest cases (D-43): the runner reads the RGB555 frame on the CGB profile and prints the
# GBB-RGB555LE-v1 digest under frame555/observed555, never the DMG RGB888 keys. --model cgb-cpu-e and
# --profile cgb select the same run (main.c maps the profile to the model token).
set(GBB_CGB_COLOUR_CASES tests/acceptance/cases-cgb-colour.txt)
gbb_add_acceptance_exit(acceptance_cgb_colour_hblank 0
  "acceptance id=cgb-colour-hblank status=pass model=cgb-cpu-e.*frame555=${gbb_hex64_re}" 60
  "--acceptance;${GBB_CGB_COLOUR_CASES};--case;cgb-colour-hblank;--model;cgb-cpu-e")
gbb_add_acceptance_exit(acceptance_cgb_colour_hblank_profile_flag 0
  "acceptance id=cgb-colour-hblank status=pass model=cgb-cpu-e.*frame555=${gbb_hex64_re}" 60
  "--acceptance;${GBB_CGB_COLOUR_CASES};--case;cgb-colour-hblank;--profile;cgb")
# Controls: the wrong model is excluded, a flipped reference digest fails with an RGB555 failure image,
# and a CGB progress-predicate observation is refused with an explicit reason.
gbb_add_acceptance_exit(acceptance_cgb_colour_excluded_dmg 4
  "status=excluded reason=unsupported-model model=dmg-cpu-b" 30
  "--acceptance;${GBB_CGB_COLOUR_CASES};--case;cgb-colour-hblank;--model;dmg-cpu-b")
set(GBB_CGB_COLOUR_FAIL_DIR ${PROJECT_BINARY_DIR}/acceptance-failures/acceptance_cgb_colour_flipped_ppm)
file(MAKE_DIRECTORY ${GBB_CGB_COLOUR_FAIL_DIR})
add_test(NAME acceptance_cgb_colour_flipped_ppm
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--acceptance;${GBB_CGB_COLOUR_CASES};--case;cgb-colour-hblank-flipped;--model;cgb-cpu-e;--failure-dir;${GBB_CGB_COLOUR_FAIL_DIR}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=reason=frame-mismatch class=regression observed555="
    -DGBB_EXPECT_FILE=${GBB_CGB_COLOUR_FAIL_DIR}/cgb-colour-hblank-flipped.ppm
    -DGBB_EXPECT_FILE_SIZE=69135
    -DGBB_EXPECT_FILE_FRESH=1
    -DGBB_WORKDIR=${PROJECT_SOURCE_DIR}
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(acceptance_cgb_colour_flipped_ppm PROPERTIES TIMEOUT 60 WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})
gbb_add_acceptance_exit(acceptance_cgb_colour_progress_refused 3
  "frame-unsupported-profile" 300
  "--acceptance;${GBB_CGB_COLOUR_CASES};--case;libbet-cgb-progress;--model;cgb-cpu-e")
# --- Phase 11 plan 11-09 end ---
