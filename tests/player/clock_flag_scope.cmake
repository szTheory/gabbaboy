# D-21 scope check for --clock-unix (cmake -P).
#
# Inputs (passed with -D): GBB_PLAYER, GBB_DEMO, GBB_INVALID, GBB_MBC1, GBB_HOME.
#
# The flag pins the host clock for deterministic tests, so it must exist only as an
# explicit argument after the ROM of --battery-smoke-store / --battery-smoke-resume.
# Every other use, and every value that is not a complete base-10 int64, must print the
# usage line and exit 2; one valid battery-smoke use must succeed.
foreach(required GBB_PLAYER GBB_DEMO GBB_INVALID GBB_MBC1 GBB_HOME)
  if(NOT DEFINED ${required} OR "${${required}}" STREQUAL "")
    message(FATAL_ERROR "clock_flag_scope: ${required} is missing")
  endif()
endforeach()

file(REMOVE_RECURSE "${GBB_HOME}")
file(MAKE_DIRECTORY "${GBB_HOME}")
set(ENV{HOME} "${GBB_HOME}")
set(ENV{CFFIXED_USER_HOME} "${GBB_HOME}")

function(expect_usage description)
  execute_process(COMMAND "${GBB_PLAYER}" ${ARGN}
    RESULT_VARIABLE result OUTPUT_VARIABLE output ERROR_VARIABLE error)
  if(NOT result STREQUAL "2" OR NOT "${output}${error}" MATCHES "usage:")
    message(FATAL_ERROR
      "clock_flag_scope: ${description}: expected usage and exit 2, got '${result}'\n${output}${error}")
  endif()
endfunction()

expect_usage("normal play" --clock-unix 5)
expect_usage("--smoke" --smoke --clock-unix 5)
expect_usage("--smoke with ROMs" --smoke "${GBB_DEMO}" "${GBB_INVALID}" --clock-unix 5)
expect_usage("--smoke-package" --smoke-package "${GBB_INVALID}" --clock-unix 5)
expect_usage("--audio-dummy-smoke" --audio-dummy-smoke --clock-unix 5)
expect_usage("non-numeric value" --battery-smoke-store "${GBB_DEMO}" --clock-unix abc)
expect_usage("trailing junk" --battery-smoke-store "${GBB_DEMO}" --clock-unix 12x)
expect_usage("empty value" --battery-smoke-store "${GBB_DEMO}" --clock-unix "")
expect_usage("out of range" --battery-smoke-store "${GBB_DEMO}" --clock-unix 99999999999999999999)
expect_usage("missing value" --battery-smoke-store "${GBB_DEMO}" --clock-unix)
expect_usage("wrong position" --battery-smoke-resume --clock-unix 5 "${GBB_DEMO}")
expect_usage("repeated flag" --battery-smoke-store "${GBB_DEMO}" --clock-unix 5 --clock-unix 6)

execute_process(COMMAND "${GBB_PLAYER}" --battery-smoke-store "${GBB_MBC1}"
    --clock-unix 1700000000
  RESULT_VARIABLE result OUTPUT_VARIABLE output ERROR_VARIABLE error)
if(NOT result STREQUAL "0")
  message(FATAL_ERROR
    "clock_flag_scope: valid battery smoke store exited '${result}'\n${output}${error}")
endif()
execute_process(COMMAND "${GBB_PLAYER}" --battery-smoke-resume "${GBB_MBC1}"
    --clock-unix 1700003661
  RESULT_VARIABLE result OUTPUT_VARIABLE output ERROR_VARIABLE error)
if(NOT result STREQUAL "0")
  message(FATAL_ERROR
    "clock_flag_scope: valid battery smoke resume exited '${result}'\n${output}${error}")
endif()
message(STATUS "clock_flag_scope ok")
