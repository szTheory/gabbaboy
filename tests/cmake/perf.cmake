# Phase 16 plan 02: cumulative DMG performance gate (TUNE-03, D-13..D-17).
#
# Every test here is valgrind-free: the evaluator runs on canned cachegrind and timing outputs in
# tests/data/perf-gate/, so these controls run on every platform. The hosted perf-gate job (ci.yml) feeds
# the same evaluator real cachegrind output. No test reads .planning, so none carries the planning label.

set(GBB_PERF_GATE_CHECKER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-perf-gate.py")
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

# The control count is a parsed minimum: adding controls is allowed, dropping one is rejected.
set(GBB_PERF_GATE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=33)
gbb_add_perf_gate_test(perf_gate_controls 0 "perf-gate self-test pass controls=[0-9]+" --self-test)
set(GBB_PERF_GATE_EXTRA_ARGS)

gbb_add_perf_gate_test(perf_gate_canned_pass 0 "perf-gate pass ratios tracer=1[.]081"
  --evaluate --limits "${GBB_PERF_GATE_LIMITS}"
  --base "${GBB_PERF_GATE_DATA}/base" --head "${GBB_PERF_GATE_DATA}/head-pass"
  --realtime "${GBB_PERF_GATE_DATA}/realtime-pass.txt")
gbb_add_perf_gate_test(perf_gate_canned_ir_over_limit 1 "REJECT ir-budget-exceeded"
  --evaluate --limits "${GBB_PERF_GATE_LIMITS}"
  --base "${GBB_PERF_GATE_DATA}/base" --head "${GBB_PERF_GATE_DATA}/head-over")
gbb_add_perf_gate_test(perf_gate_canned_realtime_under_floor 1 "REJECT realtime-below-floor"
  --evaluate --limits "${GBB_PERF_GATE_LIMITS}"
  --base "${GBB_PERF_GATE_DATA}/base" --head "${GBB_PERF_GATE_DATA}/head-pass"
  --realtime "${GBB_PERF_GATE_DATA}/realtime-below-floor.txt")
gbb_add_perf_gate_test(perf_gate_limits_schema 0 "perf-gate limits ok"
  --check-limits "${GBB_PERF_GATE_LIMITS}" --root "${PROJECT_SOURCE_DIR}")
