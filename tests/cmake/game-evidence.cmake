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
  TIMEOUT 60 LABELS planning WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")

add_test(NAME phase21_fixture_admission_controls
  COMMAND ${Python3_EXECUTABLE} -I "${GBB_CANDIDATE_CHECKER}"
          --self-test-controls --repo-root "${PROJECT_SOURCE_DIR}"
          --source-revision "${GBB_CANDIDATE_SOURCE_REV}")
set_tests_properties(phase21_fixture_admission_controls PROPERTIES
  TIMEOUT 60 LABELS planning WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")

set(GBB_GAME_EVIDENCE_CHECKER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-cgb-game-evidence.py")
add_test(NAME phase21_game_evidence
  COMMAND ${Python3_EXECUTABLE} -I "${GBB_GAME_EVIDENCE_CHECKER}"
          --check --runner "$<TARGET_FILE:gabbaboy-runner>"
          --repo-root "${PROJECT_SOURCE_DIR}"
          --source-revision "${GBB_CANDIDATE_SOURCE_REV}"
          --write-evidence "${PROJECT_BINARY_DIR}/phase21-evidence/result.json")
set_tests_properties(phase21_game_evidence PROPERTIES
  TIMEOUT 60 LABELS planning WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")

add_test(NAME phase21_game_evidence_controls
  COMMAND ${Python3_EXECUTABLE} -I "${GBB_GAME_EVIDENCE_CHECKER}"
          --self-test-controls --repo-root "${PROJECT_SOURCE_DIR}"
          --source-revision "${GBB_CANDIDATE_SOURCE_REV}")
set_tests_properties(phase21_game_evidence_controls PROPERTIES
  TIMEOUT 60 LABELS planning WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")

# Phase 21 Plan 06 report intake begins with title, scene, and symptom only.
set(GBB_SCENE_REPORT_CHECKER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-scene-report.py")
add_test(NAME phase21_scene_report_tracer
  COMMAND ${Python3_EXECUTABLE} -I "${GBB_SCENE_REPORT_CHECKER}"
          --self-test intake --repo-root "${PROJECT_SOURCE_DIR}"
          --source-revision "${GBB_CANDIDATE_SOURCE_REV}")
set_tests_properties(phase21_scene_report_tracer PROPERTIES
  TIMEOUT 60 LABELS planning WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")

add_test(NAME phase21_scene_report_controls
  COMMAND ${Python3_EXECUTABLE} -I "${GBB_SCENE_REPORT_CHECKER}"
          --self-test controls --repo-root "${PROJECT_SOURCE_DIR}"
          --source-revision "${GBB_CANDIDATE_SOURCE_REV}")
set_tests_properties(phase21_scene_report_controls PROPERTIES
  TIMEOUT 60 LABELS planning WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")

add_test(NAME phase21_scene_report_contract
  COMMAND ${Python3_EXECUTABLE} -I "${GBB_SCENE_REPORT_CHECKER}"
          --self-test contract --repo-root "${PROJECT_SOURCE_DIR}"
          --source-revision "${GBB_CANDIDATE_SOURCE_REV}")
set_tests_properties(phase21_scene_report_contract PROPERTIES
  TIMEOUT 60 LABELS planning WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
