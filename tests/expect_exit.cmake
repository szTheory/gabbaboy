# Exact exit-code assertion for CTest.
#
# Inputs (all passed with -D):
#   GBB_CMD           CMake list: the program, then its arguments
#   GBB_EXPECT_CODE   decimal exit code the program must return
#   GBB_EXPECT_REGEX  regular expression the combined stdout+stderr must match
#   GBB_WORKDIR       optional working directory
#   GBB_FORBID_REGEX  optional regular expression the combined output must NOT match
#   GBB_EXPECT_FILE        optional path that must exist after the run
#   GBB_EXPECT_FILE_SIZE   optional exact byte size of GBB_EXPECT_FILE
#   GBB_EXPECT_FILE_MAX_SIZE optional inclusive upper bound on the byte size of GBB_EXPECT_FILE
#   GBB_EXPECT_FILE_FRESH  when set, GBB_EXPECT_FILE is removed before the run so a stale file cannot pass
#
# A different non-zero code is a failure, so a crash or a changed failure class is never mistaken
# for the expected rejection. A result that is not a number (a signal or "Child aborted") never
# equals a decimal code, so it always fails.
foreach(required GBB_CMD GBB_EXPECT_CODE GBB_EXPECT_REGEX)
  if(NOT DEFINED ${required} OR "${${required}}" STREQUAL "")
    message(FATAL_ERROR "expect_exit.cmake is missing ${required}")
  endif()
endforeach()
if(NOT GBB_EXPECT_CODE MATCHES "^[0-9]+$")
  message(FATAL_ERROR "GBB_EXPECT_CODE must be a decimal exit code, got: ${GBB_EXPECT_CODE}")
endif()

set(gbb_workdir_args "")
if(DEFINED GBB_WORKDIR AND NOT "${GBB_WORKDIR}" STREQUAL "")
  set(gbb_workdir_args WORKING_DIRECTORY "${GBB_WORKDIR}")
endif()
if(DEFINED GBB_EXPECT_FILE AND NOT "${GBB_EXPECT_FILE}" STREQUAL "" AND GBB_EXPECT_FILE_FRESH)
  file(REMOVE "${GBB_EXPECT_FILE}")
endif()
execute_process(COMMAND ${GBB_CMD} ${gbb_workdir_args}
  RESULT_VARIABLE gbb_result OUTPUT_VARIABLE gbb_output ERROR_VARIABLE gbb_error)
set(gbb_combined "${gbb_output}${gbb_error}")

if(NOT gbb_result STREQUAL GBB_EXPECT_CODE)
  message(FATAL_ERROR
    "expected exit code ${GBB_EXPECT_CODE} but the command returned '${gbb_result}'\n"
    "command: ${GBB_CMD}\noutput: ${gbb_combined}")
endif()
if(NOT gbb_combined MATCHES "${GBB_EXPECT_REGEX}")
  message(FATAL_ERROR
    "exit code ${GBB_EXPECT_CODE} was right but the output did not match '${GBB_EXPECT_REGEX}'\n"
    "command: ${GBB_CMD}\noutput: ${gbb_combined}")
endif()
if(DEFINED GBB_FORBID_REGEX AND NOT "${GBB_FORBID_REGEX}" STREQUAL "")
  if(gbb_combined MATCHES "${GBB_FORBID_REGEX}")
    message(FATAL_ERROR
      "output matched the forbidden pattern '${GBB_FORBID_REGEX}'\n"
      "command: ${GBB_CMD}\noutput: ${gbb_combined}")
  endif()
endif()
if(DEFINED GBB_EXPECT_FILE AND NOT "${GBB_EXPECT_FILE}" STREQUAL "")
  if(NOT EXISTS "${GBB_EXPECT_FILE}")
    message(FATAL_ERROR "expected file ${GBB_EXPECT_FILE} was not written\ncommand: ${GBB_CMD}\noutput: ${gbb_combined}")
  endif()
  if(DEFINED GBB_EXPECT_FILE_SIZE AND NOT "${GBB_EXPECT_FILE_SIZE}" STREQUAL "")
    file(SIZE "${GBB_EXPECT_FILE}" gbb_file_size)
    if(NOT gbb_file_size EQUAL GBB_EXPECT_FILE_SIZE)
      message(FATAL_ERROR "${GBB_EXPECT_FILE} is ${gbb_file_size} bytes, expected ${GBB_EXPECT_FILE_SIZE}")
    endif()
  endif()
  if(DEFINED GBB_EXPECT_FILE_MAX_SIZE AND NOT "${GBB_EXPECT_FILE_MAX_SIZE}" STREQUAL "")
    file(SIZE "${GBB_EXPECT_FILE}" gbb_file_size)
    if(gbb_file_size GREATER GBB_EXPECT_FILE_MAX_SIZE)
      message(FATAL_ERROR "${GBB_EXPECT_FILE} is ${gbb_file_size} bytes, more than the ${GBB_EXPECT_FILE_MAX_SIZE} byte cap")
    endif()
  endif()
endif()
