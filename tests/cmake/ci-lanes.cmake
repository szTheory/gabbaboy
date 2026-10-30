# Phase 16 plan 04: planning-only CI lane and workflow policy CTests (TUNE-04, D-20..D-22).
#
# The classifier and aggregator controls read only .github/scripts and tests/data, so they carry the planning
# label and run on a configured but unbuilt tree. The workflow policy tests read .github only, so they stay
# unlabelled: the planning lane is for tests that read .planning/ or AGENTS.md.

set(GBB_CLASSIFY_CHANGES "${PROJECT_SOURCE_DIR}/.github/scripts/classify-changes.py")
set(GBB_CHECK_REQUIRED_NATIVE "${PROJECT_SOURCE_DIR}/.github/scripts/check-required-native.py")
set(GBB_WORKFLOW_POLICY "${PROJECT_SOURCE_DIR}/.github/scripts/verify-workflow-policy.py")
set(GBB_WORKFLOW_POLICY_COVERAGE "${PROJECT_SOURCE_DIR}/tests/scripts/verify-workflow-policy-coverage.py")
set(GBB_CLASSIFY_DATA "${PROJECT_SOURCE_DIR}/tests/data/classify-changes")

# Immutable recorded raw diffs: SHA256SUMS lists every fixture and its digest, and the manifest itself is pinned
# here. A drifted, missing or extra file stops configuration. Do not repair a fixture; add a second one.
set(GBB_CLASSIFY_MANIFEST_SHA256 "af528d6b7b2f80a1028644d5f01167bc70ce42b599dbf345a834413dd5cb9bb6")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${GBB_CLASSIFY_DATA}/SHA256SUMS")
file(SHA256 "${GBB_CLASSIFY_DATA}/SHA256SUMS" gbb_classify_manifest_sha256)
if(NOT gbb_classify_manifest_sha256 STREQUAL GBB_CLASSIFY_MANIFEST_SHA256)
  message(FATAL_ERROR "tests/data/classify-changes/SHA256SUMS is immutable test data: its SHA-256 is "
    "${gbb_classify_manifest_sha256}, expected ${GBB_CLASSIFY_MANIFEST_SHA256}.")
endif()
file(STRINGS "${GBB_CLASSIFY_DATA}/SHA256SUMS" gbb_classify_manifest_lines)
set(gbb_classify_listed "")
foreach(gbb_line IN LISTS gbb_classify_manifest_lines)
  if(NOT gbb_line MATCHES "^([0-9a-f]+)  (.+)$")
    message(FATAL_ERROR "tests/data/classify-changes/SHA256SUMS: malformed line '${gbb_line}'")
  endif()
  set(gbb_fixture_hash "${CMAKE_MATCH_1}")
  set(gbb_fixture_name "${CMAKE_MATCH_2}")
  list(APPEND gbb_classify_listed "${gbb_fixture_name}")
  set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${GBB_CLASSIFY_DATA}/${gbb_fixture_name}")
  file(SHA256 "${GBB_CLASSIFY_DATA}/${gbb_fixture_name}" gbb_fixture_actual)
  if(NOT gbb_fixture_actual STREQUAL gbb_fixture_hash)
    message(FATAL_ERROR "tests/data/classify-changes/${gbb_fixture_name} is immutable test data: its SHA-256 is "
      "${gbb_fixture_actual}, expected ${gbb_fixture_hash}.")
  endif()
endforeach()
file(GLOB_RECURSE gbb_classify_present RELATIVE "${GBB_CLASSIFY_DATA}" "${GBB_CLASSIFY_DATA}/*")
list(REMOVE_ITEM gbb_classify_present "SHA256SUMS")
list(SORT gbb_classify_present)
list(SORT gbb_classify_listed)
if(NOT gbb_classify_present STREQUAL gbb_classify_listed)
  message(FATAL_ERROR "tests/data/classify-changes holds files that SHA256SUMS does not list (or the reverse).")
endif()

# gbb_add_ci_lane_test(name code regex timeout labels script [args...]): one python3 -I invocation through
# expect_exit.cmake. GBB_CI_LANE_EXTRA_ARGS carries any -D options for the assertion script (a parsed minimum).
function(gbb_add_ci_lane_test name code regex timeout labels script)
  set(command "${Python3_EXECUTABLE}" -I "${script}" ${ARGN})
  list(JOIN command "$<SEMICOLON>" joined)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${joined}"
      -DGBB_EXPECT_CODE=${code}
      "-DGBB_EXPECT_REGEX=${regex}"
      ${GBB_CI_LANE_EXTRA_ARGS}
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT ${timeout})
  if(NOT "${labels}" STREQUAL "")
    set_tests_properties(${name} PROPERTIES LABELS "${labels}")
  endif()
endfunction()

# Each control count is a parsed minimum: adding controls is allowed, dropping one is rejected.
set(GBB_CI_LANE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=40)
gbb_add_ci_lane_test(classify_changes_controls 0 "classify-changes self-test pass controls=[0-9]+" 30 planning
  "${GBB_CLASSIFY_CHANGES}" --self-test)
set(GBB_CI_LANE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=6)
gbb_add_ci_lane_test(required_native_controls 0 "required-native self-test pass controls=[0-9]+" 30 planning
  "${GBB_CHECK_REQUIRED_NATIVE}" --self-test)
# Defect fix: preview.yml's player smoke waits on the exact-head CI run, which a planning-only head skips the player
# package in. The controls prove a planning run excuses exactly that skip and a full run (or any other result) does not.
set(GBB_WAIT_EXACT_HEAD_CI "${PROJECT_SOURCE_DIR}/.github/scripts/wait-exact-head-ci.py")
set(GBB_CI_LANE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=40)
gbb_add_ci_lane_test(wait_exact_head_ci_controls 0 "exact-head gate self-test [^c]+cases[^c]+controls=[0-9]+" 60 planning
  "${GBB_WAIT_EXACT_HEAD_CI}" --self-test)
set(GBB_CI_LANE_EXTRA_ARGS)

# TUNE-04 success criterion 3: a src/ change and a tests/ change offered to the classifier must both come back
# kind=full (with a rename out of src/ and a mixed diff as extra controls); any planning verdict fails the test.
set(GBB_CI_LANE_EXTRA_ARGS "-DGBB_FORBID_REGEX=kind=planning")
gbb_add_ci_lane_test(classify_changes_src_rejected 0 "kind=full" 30 planning
  "${GBB_CLASSIFY_CHANGES}" --from-raw "${GBB_CLASSIFY_DATA}/src-change.raw" "${GBB_CLASSIFY_DATA}/tests-change.raw"
  "${GBB_CLASSIFY_DATA}/rename-out-of-src.raw" "${GBB_CLASSIFY_DATA}/planning-plus-src.raw")
set(GBB_CI_LANE_EXTRA_ARGS)

# D-20/D-21: every workflow-policy control from plans 16-02 to 16-04 is reachable from CTest.
gbb_add_ci_lane_test(workflow_policy_check 0 "PASS: workflow privilege and trust wiring residual_write_jobs=[0-9]+" 60 ""
  "${GBB_WORKFLOW_POLICY}" --check --root "${PROJECT_SOURCE_DIR}")
# The control registry is generated from immutable baseline 70d3e422. Each group emits a fresh completion file only
# after its completed stable IDs equal the registry slice. All groups use the existing exit-plus-marker wrapper and
# retain the unchanged 180-second ceiling. The legacy --self-test with no --group still runs the complete suite.
set(GBB_POLICY_COVERAGE_REV_RESULT "")
# Do not let Git discover an unrelated parent repository when this project is an extracted source archive.
# Ordinary source builds remain configurable without Git; the immutable CTest checker still fails closed if run.
file(REAL_PATH "${PROJECT_SOURCE_DIR}" GBB_POLICY_PROJECT_REAL)
execute_process(COMMAND git -C "${PROJECT_SOURCE_DIR}" rev-parse --show-toplevel
  OUTPUT_VARIABLE GBB_POLICY_GIT_TOP OUTPUT_STRIP_TRAILING_WHITESPACE RESULT_VARIABLE GBB_POLICY_GIT_TOP_RESULT
  ERROR_QUIET)
if("${GBB_POLICY_GIT_TOP_RESULT}" STREQUAL "0")
  file(REAL_PATH "${GBB_POLICY_GIT_TOP}" GBB_POLICY_GIT_TOP_REAL)
  if(GBB_POLICY_GIT_TOP_REAL STREQUAL GBB_POLICY_PROJECT_REAL)
    execute_process(COMMAND git -C "${PROJECT_SOURCE_DIR}" rev-parse --verify "HEAD^{commit}"
      OUTPUT_VARIABLE GBB_POLICY_COVERAGE_REV OUTPUT_STRIP_TRAILING_WHITESPACE
      RESULT_VARIABLE GBB_POLICY_COVERAGE_REV_RESULT ERROR_QUIET)
  endif()
endif()
string(LENGTH "${GBB_POLICY_COVERAGE_REV}" GBB_POLICY_COVERAGE_REV_LENGTH)
if(NOT "${GBB_POLICY_COVERAGE_REV_RESULT}" STREQUAL "0"
   OR NOT (GBB_POLICY_COVERAGE_REV_LENGTH EQUAL 40 OR GBB_POLICY_COVERAGE_REV_LENGTH EQUAL 64)
   OR NOT GBB_POLICY_COVERAGE_REV MATCHES "^[0-9a-f]+$")
  set(GBB_POLICY_COVERAGE_REV "unknown")
  message(STATUS "Workflow-policy coverage CTests remain registered with an unresolved revision and will fail closed when invoked")
endif()

set(GBB_CI_LANE_EXTRA_ARGS "-DGBB_EXPECT_FILE=${PROJECT_BINARY_DIR}/workflow-policy-ci.json" -DGBB_EXPECT_FILE_FRESH=TRUE)
gbb_add_ci_lane_test(workflow_policy_group_ci 0 "PASS: workflow policy group ci controls=[0-9]+ ids_sha256=[0-9a-f]+" 180 ""
  "${GBB_WORKFLOW_POLICY}" --self-test --group ci --root "${PROJECT_SOURCE_DIR}"
  --completed-file "${PROJECT_BINARY_DIR}/workflow-policy-ci.json")
set(GBB_CI_LANE_EXTRA_ARGS "-DGBB_EXPECT_FILE=${PROJECT_BINARY_DIR}/workflow-policy-release-jobs.json" -DGBB_EXPECT_FILE_FRESH=TRUE)
gbb_add_ci_lane_test(workflow_policy_group_release_jobs 0 "PASS: workflow policy group release_jobs controls=[0-9]+ ids_sha256=[0-9a-f]+" 180 ""
  "${GBB_WORKFLOW_POLICY}" --self-test --group release_jobs --root "${PROJECT_SOURCE_DIR}"
  --completed-file "${PROJECT_BINARY_DIR}/workflow-policy-release-jobs.json")
set(GBB_CI_LANE_EXTRA_ARGS "-DGBB_EXPECT_FILE=${PROJECT_BINARY_DIR}/workflow-policy-release-support.json" -DGBB_EXPECT_FILE_FRESH=TRUE)
gbb_add_ci_lane_test(workflow_policy_group_release_support 0 "PASS: workflow policy group release_support controls=[0-9]+ ids_sha256=[0-9a-f]+" 180 ""
  "${GBB_WORKFLOW_POLICY}" --self-test --group release_support --root "${PROJECT_SOURCE_DIR}"
  --completed-file "${PROJECT_BINARY_DIR}/workflow-policy-release-support.json")
set(GBB_CI_LANE_EXTRA_ARGS "-DGBB_EXPECT_FILE=${PROJECT_BINARY_DIR}/workflow-policy-rehearsal.json" -DGBB_EXPECT_FILE_FRESH=TRUE)
gbb_add_ci_lane_test(workflow_policy_group_rehearsal 0 "PASS: workflow policy group rehearsal controls=[0-9]+ ids_sha256=[0-9a-f]+" 180 ""
  "${GBB_WORKFLOW_POLICY}" --self-test --group rehearsal --root "${PROJECT_SOURCE_DIR}"
  --completed-file "${PROJECT_BINARY_DIR}/workflow-policy-rehearsal.json")
set(GBB_CI_LANE_EXTRA_ARGS "-DGBB_EXPECT_FILE=${PROJECT_BINARY_DIR}/workflow-policy-ledger.json" -DGBB_EXPECT_FILE_FRESH=TRUE)
gbb_add_ci_lane_test(workflow_policy_group_ledger 0 "PASS: workflow policy group ledger controls=[0-9]+ ids_sha256=[0-9a-f]+" 180 ""
  "${GBB_WORKFLOW_POLICY}" --self-test --group ledger --root "${PROJECT_SOURCE_DIR}"
  --completed-file "${PROJECT_BINARY_DIR}/workflow-policy-ledger.json")
set(GBB_CI_LANE_EXTRA_ARGS "-DGBB_EXPECT_FILE=${PROJECT_BINARY_DIR}/workflow-policy-helpers.json" -DGBB_EXPECT_FILE_FRESH=TRUE)
gbb_add_ci_lane_test(workflow_policy_group_helpers 0 "PASS: workflow policy group helpers controls=[0-9]+ ids_sha256=[0-9a-f]+" 180 ""
  "${GBB_WORKFLOW_POLICY}" --self-test --group helpers --root "${PROJECT_SOURCE_DIR}"
  --completed-file "${PROJECT_BINARY_DIR}/workflow-policy-helpers.json")
set(GBB_CI_LANE_EXTRA_ARGS)
gbb_add_ci_lane_test(workflow_policy_coverage 0 "PASS: workflow policy coverage controls=[0-9]+ groups=6 platform=(posix|windows)" 60 ""
  "${GBB_WORKFLOW_POLICY_COVERAGE}" --check --root "${PROJECT_SOURCE_DIR}" --build-dir "${PROJECT_BINARY_DIR}"
  --rev "${GBB_POLICY_COVERAGE_REV}")
gbb_add_ci_lane_test(workflow_policy_coverage_controls 0 "PASS: workflow policy coverage self-test controls=62" 30 ""
  "${GBB_WORKFLOW_POLICY_COVERAGE}" --self-test --root "${PROJECT_SOURCE_DIR}" --rev "${GBB_POLICY_COVERAGE_REV}")
set(GBB_CI_LANE_EXTRA_ARGS)

# D-22 planning-label lint. It reads the configured tree's CTest listing, never a built artifact, so it runs from the
# build directory as its working directory (a path argument under the build dir would be a planning-test-needs-build
# violation of the very rule it enforces) and carries the planning label itself.
set(GBB_PLANNING_LABELS_CHECKER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-planning-labels.py")
set(GBB_CI_LANE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=planning -DGBB_EXPECT_MIN_VALUE=10)
gbb_add_ci_lane_test(planning_labels 0 "planning-labels pass tests=[0-9]+ planning=[0-9]+" 60 planning
  "${GBB_PLANNING_LABELS_CHECKER}" --build-dir .)
set_tests_properties(planning_labels PROPERTIES WORKING_DIRECTORY "${PROJECT_BINARY_DIR}")
set(GBB_CI_LANE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=3)
gbb_add_ci_lane_test(planning_labels_controls 0 "planning-labels self-test pass controls=[0-9]+" 60 planning
  "${GBB_PLANNING_LABELS_CHECKER}" --self-test)
set(GBB_CI_LANE_EXTRA_ARGS)
