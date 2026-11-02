# Phase 21 Plan 03: immutable-source candidate admission contract checks.
include("${PROJECT_SOURCE_DIR}/cmake/ResolveContractRevision.cmake")

set(GBB_CANDIDATE_CHECKER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-cgb-candidates.py")
gbb_resolve_contract_revision(
  "${PROJECT_SOURCE_DIR}" "HEAD" GBB_CANDIDATE_SOURCE_REV GBB_CANDIDATE_SOURCE_STATUS)
if(NOT GBB_CANDIDATE_SOURCE_STATUS STREQUAL "resolved")
  set(GBB_CANDIDATE_SOURCE_REV "unknown")
endif()

add_test(NAME phase21_fixture_admission_contract
  COMMAND ${Python3_EXECUTABLE} -I "${GBB_CANDIDATE_CHECKER}"
          --self-test --repo-root "${PROJECT_SOURCE_DIR}"
          --source-revision "${GBB_CANDIDATE_SOURCE_REV}")
set_tests_properties(phase21_fixture_admission_contract PROPERTIES
  TIMEOUT 120 LABELS planning WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
