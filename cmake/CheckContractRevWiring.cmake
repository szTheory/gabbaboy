# Checks that the save-format and host-contract CTests all name the same immutable commit captured at configure time.
# CMake resolves the default symbolic `HEAD` (or an explicit revision ref) once before registering these tests, so a
# boundary test reads exactly the commit that existed when it was configured.
#
# Inputs (all passed with -D):
#   GBB_TESTFILE      the generated CTestTestfile.cmake that holds the add_test lines
#   GBB_TEST_NAMES    CMake list of the tests that take --rev
#   GBB_EXPECT_REV    the full SHA resolved during CMake configuration
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
  # Each add_test is one line: add_test(<name> "program" ... "--rev" "<rev>" ...). CMake 3.x (the 3.25.3 floor and
  # the hosted runners) writes the name as a bracket argument ([=[name]=]), CMake 4 quotes it, and a bare name is
  # accepted too. The name must end at a quote, a bracket or a space, so host_contract_docs never matches the add_test
  # line of host_contract_docs_control.
  # A control packs the command in one -DGBB_CMD argument, where the separators are `\;`, so a non-alphanumeric run
  # separates --rev from its value.
  string(REGEX MATCH "add_test\\((\"|\\[=*\\[)?${name}(\"|\\]=*\\]|[ \t])[^\n]*" line "${text}")
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
      " (all boundary tests must read the captured configure-time commit)")
  endif()
  math(EXPR checked "${checked} + 1")
endforeach()
message(STATUS "contract-rev-wiring pass tests=${checked} rev=${GBB_EXPECT_REV}")
