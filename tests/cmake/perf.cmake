# Phase 16 plan 02: cumulative DMG performance gate (TUNE-03, D-13..D-17).
#
# Every test here is valgrind-free: the evaluator runs on canned cachegrind and timing outputs in
# tests/data/perf-gate/, so these controls run on every platform. The hosted perf-gate job (ci.yml) feeds
# the same evaluator real cachegrind output. No test reads .planning, so none carries the planning label.

set(GBB_PERF_GATE_CHECKER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-perf-gate.py")
set(GBB_PERF_RECEIPT_CHECKER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-v02-performance.py")
set(GBB_PERF_GATE_LIMITS "${PROJECT_SOURCE_DIR}/tests/baseline/perf-gate-v1.txt")
set(GBB_PERF_GATE_DATA "${PROJECT_SOURCE_DIR}/tests/data/perf-gate")

# Immutable canned fixtures: SHA256SUMS lists every fixture file and its digest, and the manifest itself is
# pinned here. A drifted, missing or extra file stops configuration. Do not repair a fixture; fix the
# checker or add a second fixture.
set(GBB_PERF_GATE_MANIFEST_SHA256 "6093608a220b121aedbc6fb420b61e3285b3feec7b5649430a0433e8d7d67d46")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${GBB_PERF_GATE_DATA}/SHA256SUMS")
file(SHA256 "${GBB_PERF_GATE_DATA}/SHA256SUMS" gbb_perf_gate_manifest_sha256)
if(NOT gbb_perf_gate_manifest_sha256 STREQUAL GBB_PERF_GATE_MANIFEST_SHA256)
  message(FATAL_ERROR "tests/data/perf-gate/SHA256SUMS is immutable test data: its SHA-256 is "
    "${gbb_perf_gate_manifest_sha256}, expected ${GBB_PERF_GATE_MANIFEST_SHA256}.")
endif()
file(STRINGS "${GBB_PERF_GATE_DATA}/SHA256SUMS" gbb_perf_gate_manifest_lines)
set(gbb_perf_gate_listed "")
foreach(gbb_line IN LISTS gbb_perf_gate_manifest_lines)
  if(NOT gbb_line MATCHES "^([0-9a-f]+)  (.+)$")
    message(FATAL_ERROR "tests/data/perf-gate/SHA256SUMS: malformed line '${gbb_line}'")
  endif()
  set(gbb_fixture_hash "${CMAKE_MATCH_1}")
  set(gbb_fixture_name "${CMAKE_MATCH_2}")
  list(APPEND gbb_perf_gate_listed "${gbb_fixture_name}")
  set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${GBB_PERF_GATE_DATA}/${gbb_fixture_name}")
  file(SHA256 "${GBB_PERF_GATE_DATA}/${gbb_fixture_name}" gbb_fixture_actual)
  if(NOT gbb_fixture_actual STREQUAL gbb_fixture_hash)
    message(FATAL_ERROR "tests/data/perf-gate/${gbb_fixture_name} is immutable test data: its SHA-256 is "
      "${gbb_fixture_actual}, expected ${gbb_fixture_hash}.")
  endif()
endforeach()
file(GLOB_RECURSE gbb_perf_gate_present RELATIVE "${GBB_PERF_GATE_DATA}" "${GBB_PERF_GATE_DATA}/*")
list(REMOVE_ITEM gbb_perf_gate_present "SHA256SUMS")
list(SORT gbb_perf_gate_present)
list(SORT gbb_perf_gate_listed)
if(NOT gbb_perf_gate_present STREQUAL gbb_perf_gate_listed)
  message(FATAL_ERROR "tests/data/perf-gate holds files that SHA256SUMS does not list (or the reverse).")
endif()

function(gbb_add_perf_gate_test name code regex)
  set(command "${Python3_EXECUTABLE}" -I "${GBB_PERF_GATE_CHECKER}" ${ARGN})
  list(JOIN command "$<SEMICOLON>" joined)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${joined}"
      -DGBB_EXPECT_CODE=${code}
      "-DGBB_EXPECT_REGEX=${regex}"
      ${GBB_PERF_GATE_EXTRA_ARGS}
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT 60)
endfunction()

function(gbb_add_perf_receipt_test name regex argument min_controls)
  set(command "${Python3_EXECUTABLE}" -I "${GBB_PERF_RECEIPT_CHECKER}" ${argument})
  list(JOIN command "$<SEMICOLON>" joined)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${joined}"
      -DGBB_EXPECT_CODE=0
      "-DGBB_EXPECT_REGEX=${regex}"
      -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=${min_controls}
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  # Both controls measure about 7 s locally, inside the base 60 s budget (verify-test-budget.py).
  set_tests_properties(${name} PROPERTIES TIMEOUT 60)
endfunction()

# The control count is a parsed minimum: adding controls is allowed, dropping one is rejected.
set(GBB_PERF_GATE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=34)
gbb_add_perf_gate_test(perf_gate_controls 0 "perf-gate self-test pass controls=[0-9]+" --self-test)
set(GBB_PERF_GATE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=6)
gbb_add_perf_gate_test(perf_gate_receipt_controls 0 "perf-gate receipt self-test pass controls=[0-9]+"
  --self-test-receipt)
set(GBB_PERF_GATE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=4)
add_test(NAME perf_gate_retry_controls
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=bash;${PROJECT_SOURCE_DIR}/tests/scripts/run-perf-gate.sh;--self-test-retry"
    -DGBB_EXPECT_CODE=0
    "-DGBB_EXPECT_REGEX=perf-gate retry controls pass controls=[0-9]+"
    ${GBB_PERF_GATE_EXTRA_ARGS}
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(perf_gate_retry_controls PROPERTIES TIMEOUT 60)
set(GBB_PERF_GATE_EXTRA_ARGS)

gbb_add_perf_gate_test(perf_gate_canned_pass 0 "perf-gate pass ratios tracer=1[.]081"
  --evaluate --limits "${GBB_PERF_GATE_LIMITS}"
  --base "${GBB_PERF_GATE_DATA}/base" --head "${GBB_PERF_GATE_DATA}/head-pass"
  --realtime "${GBB_PERF_GATE_DATA}/realtime-pass.txt"
  --base-rev 947d6a9d177af6c04a5f9ea6abcc2c470ab9be57)
gbb_add_perf_gate_test(perf_gate_canned_ir_over_limit 1 "REJECT ir-budget-exceeded"
  --evaluate --limits "${GBB_PERF_GATE_LIMITS}"
  --base "${GBB_PERF_GATE_DATA}/base" --head "${GBB_PERF_GATE_DATA}/head-over"
  --base-rev 947d6a9d177af6c04a5f9ea6abcc2c470ab9be57)
gbb_add_perf_gate_test(perf_gate_canned_realtime_under_floor 1 "REJECT realtime-below-floor"
  --evaluate --limits "${GBB_PERF_GATE_LIMITS}"
  --base "${GBB_PERF_GATE_DATA}/base" --head "${GBB_PERF_GATE_DATA}/head-pass"
  --realtime "${GBB_PERF_GATE_DATA}/realtime-below-floor.txt"
  --base-rev 947d6a9d177af6c04a5f9ea6abcc2c470ab9be57)
gbb_add_perf_gate_test(perf_gate_limits_schema 0 "perf-gate limits ok"
  --check-limits "${GBB_PERF_GATE_LIMITS}" --root "${PROJECT_SOURCE_DIR}"
  --base-rev 947d6a9d177af6c04a5f9ea6abcc2c470ab9be57)
set(GBB_PERF_GATE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=5)
gbb_add_perf_gate_test(perf_limit_ratchet 0 "perf-gate limit-ratchet self-test pass controls=[0-9]+"
  --self-test-limit-ratchet)
set(GBB_PERF_GATE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=3)
gbb_add_perf_gate_test(perf_repeat_controls 0 "perf-gate repeat-controls self-test pass controls=[0-9]+"
  --self-test-repeat-controls)
set(GBB_PERF_GATE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=2)
gbb_add_perf_gate_test(perf_exception_measurement 0 "perf-gate exception-measurement self-test pass controls=[0-9]+"
  --self-test-exception-measurement)
set(GBB_PERF_GATE_EXTRA_ARGS)

# D-17 attribution receipt (Task 3): the committed hosted receipt is re-derived from git history, so these two
# controls need the full history and the v0.1.0 and v0.2.0 tags. The minimums are parsed keys of the one
# "perf-attribution pass revisions=N merges=M" line.
set(GBB_PERF_GATE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=revisions -DGBB_EXPECT_MIN_VALUE=39)
gbb_add_perf_gate_test(perf_attribution 0 "perf-attribution pass revisions=[0-9]+ merges=[0-9]+"
  --check-attribution "${PROJECT_SOURCE_DIR}/tests/baseline/perf-attribution-v1.json" --repo "${PROJECT_SOURCE_DIR}")
set(GBB_PERF_GATE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=merges -DGBB_EXPECT_MIN_VALUE=20)
gbb_add_perf_gate_test(perf_attribution_merges 0 "perf-attribution pass revisions=[0-9]+ merges=[0-9]+"
  --check-attribution "${PROJECT_SOURCE_DIR}/tests/baseline/perf-attribution-v1.json" --repo "${PROJECT_SOURCE_DIR}")
set(GBB_PERF_GATE_EXTRA_ARGS)

# These exercise the actual paired-receipt producer with stubbed measurement executables, then
# pass its receipt through the production verifier and reuse function. No wall-clock threshold is asserted.
# The producer fixture is a shell-script cmake and measurement binary, so both cases skip on Windows (GB-CI-011);
# they are not registered there, as the lifecycle pair is not, because a skipped case is not a pass (WR-B03). The
# control count is the number of refusals the case asserted, a parsed minimum.
if(NOT WIN32)
  gbb_add_perf_receipt_test(perf_advisory_pipeline "advisory pipeline self-test pass controls=[0-9]+"
    --self-test-advisory-pipeline 1)
  gbb_add_perf_receipt_test(perf_advisory_controls "advisory controls self-test pass controls=[0-9]+"
    --self-test-advisory-controls 4)
endif()
