# Checks how the save-format and host-contract CTests name the commit they read (review WR-04).
#
# A checker that is handed a 40-digit SHA resolved at configure time keeps reading that commit after a later commit,
# until the next configure, while the runner under test is built from the newer tree: a false green or red for the
# wrong revision. The default is therefore the symbolic `HEAD`, which git resolves when each test runs; a full SHA is
# for a deliberate boundary-commit run (-DGBB_SAVE_FORMATS_REV=<sha>), and this script then requires exactly that SHA.
#
# Inputs (all passed with -D):
#   GBB_TESTFILE      the generated CTestTestfile.cmake that holds the add_test lines
#   GBB_TEST_NAMES    CMake list of the tests that take --rev
#   GBB_EXPECT_REV    HEAD, or the full SHA a boundary run pinned
foreach(required GBB_TESTFILE GBB_TEST_NAMES GBB_EXPECT_REV)
  if(NOT DEFINED ${required} OR "${${required}}" STREQUAL "")
    message(FATAL_ERROR "CheckContractRevWiring.cmake is missing ${required}")
  endif()
endforeach()
if(NOT EXISTS "${GBB_TESTFILE}")
  message(FATAL_ERROR "contract-rev-wiring: ${GBB_TESTFILE} does not exist")
endif()
file(READ "${GBB_TESTFILE}" text)

set(checked 0)
foreach(name IN LISTS GBB_TEST_NAMES)
  # Each add_test is one line: add_test("name" "program" ... "--rev" "<rev>" ...). A control packs the command in
  # one -DGBB_CMD argument, where the separators are `\;`, so a non-alphanumeric run separates --rev from its value.
  string(REGEX MATCH "add_test\\(\"${name}\"[^\n]*" line "${text}")
  if("${line}" STREQUAL "")
    message(FATAL_ERROR "contract-rev-wiring: test ${name} is not registered in ${GBB_TESTFILE}")
  endif()
  if(NOT line MATCHES "--rev[^A-Za-z0-9]+([A-Za-z0-9]+)")
    message(FATAL_ERROR "contract-rev-wiring: test ${name} does not pass --rev")
  endif()
  set(rev "${CMAKE_MATCH_1}")
  if(NOT rev STREQUAL GBB_EXPECT_REV)
    message(FATAL_ERROR
      "contract-rev-wiring: test ${name} reads revision ${rev}, expected ${GBB_EXPECT_REV}"
      " (a configure-time SHA goes stale at the next commit)")
  endif()
  math(EXPR checked "${checked} + 1")
endforeach()
message(STATUS "contract-rev-wiring pass tests=${checked} rev=${GBB_EXPECT_REV}")
