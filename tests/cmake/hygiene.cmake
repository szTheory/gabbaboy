# Phase 16 plan 05: Phase 8 contract verifiers in CTest and planning hygiene checks (TUNE-02, TUNE-05; D-11, D-12, D-24..D-27).
#
# Every test here reads .planning/ (directly, or through git show at the Phase 8 boundary) and no built artifact, so
# each carries the planning label and runs on a configured but unbuilt tree. Tests run from the source directory because
# the Phase 8 verifiers shell out to git. The boundary is the annotated tag historical/phase-08-boundary (D-12).
#
# WR-02: the tag is mutable, so the plain runs read the clauses from the literal boundary commit (--boundary SHA) and cannot
# follow a retargeted tag, while each *_selftest run resolves the tag itself and fails if it no longer peels to that commit.
# WR-05: plan_cap judges the ROADMAP and plan names of the configure-time HEAD commit with git (--rev), never the working tree.

set(GBB_PHASE8_CLOSURE_CHECKER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-phase8-closure-contract.py")
set(GBB_PHASE8_PLAYER_CHECKER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-phase8-player-contract.py")
set(GBB_PHASE8_BOUNDARY_SHA "96d5eec977bee99a0629499b89c737415e24184c")
execute_process(
  COMMAND git rev-parse HEAD
  WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
  RESULT_VARIABLE GBB_HYGIENE_REV_RESULT
  OUTPUT_VARIABLE GBB_HYGIENE_SOURCE_REV
  ERROR_QUIET
  OUTPUT_STRIP_TRAILING_WHITESPACE)
string(LENGTH "${GBB_HYGIENE_SOURCE_REV}" GBB_HYGIENE_SOURCE_REV_LENGTH)
if(NOT GBB_HYGIENE_REV_RESULT EQUAL 0 OR NOT GBB_HYGIENE_SOURCE_REV_LENGTH EQUAL 40
   OR NOT GBB_HYGIENE_SOURCE_REV MATCHES "^[0-9a-f]+$")
  # plan_cap then fails closed on a revision that is not a full commit id.
  set(GBB_HYGIENE_SOURCE_REV "unknown")
endif()

# gbb_add_hygiene_test(name code regex timeout script [args...]): one python3 -I invocation through expect_exit.cmake,
# run from the source directory. GBB_HYGIENE_EXTRA_ARGS carries any -D options for the assertion script (a parsed
# minimum or a forbidden pattern).
function(gbb_add_hygiene_test name code regex timeout script)
  set(command "${Python3_EXECUTABLE}" -I "${script}" ${ARGN})
  list(JOIN command "$<SEMICOLON>" joined)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${joined}"
      -DGBB_EXPECT_CODE=${code}
      "-DGBB_EXPECT_REGEX=${regex}"
      "-DGBB_WORKDIR=${PROJECT_SOURCE_DIR}"
      ${GBB_HYGIENE_EXTRA_ARGS}
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT ${timeout} LABELS planning)
endfunction()

# TUNE-02: the Phase 8 verifiers' only input is the boundary tag. The plain runs print rejected_controls=0 (closure) so
# only the self-test carries the parsed minimum; a retargeted tag changes the clause results and the control count.
set(GBB_HYGIENE_EXTRA_ARGS)
gbb_add_hygiene_test(phase8_closure_contract 0 "phase8-closure-contract PASS boundary=${GBB_PHASE8_BOUNDARY_SHA}" 60
  "${GBB_PHASE8_CLOSURE_CHECKER}" --boundary "${GBB_PHASE8_BOUNDARY_SHA}")
set(GBB_HYGIENE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=rejected_controls -DGBB_EXPECT_MIN_VALUE=165)
gbb_add_hygiene_test(phase8_closure_contract_selftest 0 "phase8-closure-contract PASS boundary=${GBB_PHASE8_BOUNDARY_SHA}" 60
  "${GBB_PHASE8_CLOSURE_CHECKER}" --self-test)
# A boundary that exists but is the wrong commit is a clause miss; an unreadable revision prints its own message. Each
# test forbids the other class so one cannot pass for the other.
set(GBB_HYGIENE_EXTRA_ARGS "-DGBB_FORBID_REGEX=boundary unreadable|cannot read")
gbb_add_hygiene_test(phase8_closure_contract_wrong_boundary 1 "missing historical clause" 60
  "${GBB_PHASE8_CLOSURE_CHECKER}" --boundary v0.2.0)
set(GBB_HYGIENE_EXTRA_ARGS)
gbb_add_hygiene_test(phase8_player_contract 0 "phase8-player-contract: PASS boundary=${GBB_PHASE8_BOUNDARY_SHA}" 60
  "${GBB_PHASE8_PLAYER_CHECKER}" --boundary "${GBB_PHASE8_BOUNDARY_SHA}")
gbb_add_hygiene_test(phase8_player_contract_selftest 0 "phase8-player-contract self-test: PASS controls=unreadable-boundary,retargeted-tag-x[1-9][0-9]*" 60
  "${GBB_PHASE8_PLAYER_CHECKER}" --self-test)
set(GBB_HYGIENE_EXTRA_ARGS "-DGBB_FORBID_REGEX=boundary unreadable")
gbb_add_hygiene_test(phase8_player_contract_wrong_boundary 1 "phase8-player-contract: FAIL" 60
  "${GBB_PHASE8_PLAYER_CHECKER}" --boundary v0.2.0)
set(GBB_HYGIENE_EXTRA_ARGS)

# TUNE-05 planning hygiene (D-24..D-27). Each check reads one planning file; planning_hygiene_controls drives every rule
# against generated and committed fixtures, so the over-cap, missing-cap, duplicate-id and oversized-STATE controls
# never touch the live files.
set(GBB_PLANNING_HYGIENE_CHECKER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-planning-hygiene.py")
set(GBB_HYGIENE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=phases -DGBB_EXPECT_MIN_VALUE=4)
gbb_add_hygiene_test(plan_cap 0 "plan-cap pass phases=[0-9]+ plans=[0-9]+" 30
  "${GBB_PLANNING_HYGIENE_CHECKER}" --check plan-cap
  --rev "${GBB_HYGIENE_SOURCE_REV}" --repo "${PROJECT_SOURCE_DIR}")
set(GBB_HYGIENE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=ids -DGBB_EXPECT_MIN_VALUE=90)
gbb_add_hygiene_test(lessons_unique_ids 0 "lessons-ids pass ids=[0-9]+" 30
  "${GBB_PLANNING_HYGIENE_CHECKER}" --check lessons-ids --lessons "${PROJECT_SOURCE_DIR}/.planning/context/LESSONS.md")
set(GBB_HYGIENE_EXTRA_ARGS)
gbb_add_hygiene_test(state_size 0 "state-size pass bytes=[0-9]+ lines=[0-9]+" 30
  "${GBB_PLANNING_HYGIENE_CHECKER}" --check state-size --state "${PROJECT_SOURCE_DIR}/.planning/STATE.md")
set(GBB_HYGIENE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=70)
gbb_add_hygiene_test(planning_hygiene_controls 0 "planning-hygiene self-test pass controls=[0-9]+" 30
  "${GBB_PLANNING_HYGIENE_CHECKER}" --self-test)
set(GBB_HYGIENE_EXTRA_ARGS)

# D-27: the corrected Playstead statements stay corrected. It reads PRECEDENT.md, so it carries the planning label.
set(GBB_HYGIENE_EXTRA_ARGS)
gbb_add_hygiene_test(playstead_docs 0 "playstead-docs pass files=3" 30
  "${GBB_PLANNING_HYGIENE_CHECKER}" --check playstead-docs --root "${PROJECT_SOURCE_DIR}")
