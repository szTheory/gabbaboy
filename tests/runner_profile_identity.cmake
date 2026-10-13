# DMG byte-identity control for the runner --profile option (D-25, D-19).
#
# Inputs (all passed with -D):
#   GBB_RUNNER   path to gabbaboy-runner
#   GBB_ARGS     CMake list: the arguments of a DMG run without --profile
#   GBB_WORKDIR  working directory (cases.txt paths resolve against it)
#
# Runs the runner twice, once with GBB_ARGS and once with GBB_ARGS plus "--profile dmg", and fails
# unless stdout, stderr and the exit code are all byte-equal and non-empty. The explicit flag must
# be a pure no-op for DMG, otherwise the existing evidence would silently change meaning.
foreach(required GBB_RUNNER GBB_ARGS GBB_WORKDIR)
  if(NOT DEFINED ${required} OR "${${required}}" STREQUAL "")
    message(FATAL_ERROR "runner_profile_identity.cmake is missing ${required}")
  endif()
endforeach()

execute_process(COMMAND "${GBB_RUNNER}" ${GBB_ARGS}
  WORKING_DIRECTORY "${GBB_WORKDIR}"
  RESULT_VARIABLE plain_result OUTPUT_VARIABLE plain_out ERROR_VARIABLE plain_err)
execute_process(COMMAND "${GBB_RUNNER}" ${GBB_ARGS} --profile dmg
  WORKING_DIRECTORY "${GBB_WORKDIR}"
  RESULT_VARIABLE flag_result OUTPUT_VARIABLE flag_out ERROR_VARIABLE flag_err)

if(NOT plain_result STREQUAL "0")
  message(FATAL_ERROR "profile-identity-baseline-failed: plain run exited '${plain_result}'\n${plain_out}${plain_err}")
endif()
if(NOT plain_result STREQUAL flag_result)
  message(FATAL_ERROR "profile-identity-mismatch: exit '${plain_result}' vs '${flag_result}'")
endif()
if(NOT plain_out STREQUAL flag_out OR NOT plain_err STREQUAL flag_err)
  message(FATAL_ERROR "profile-identity-mismatch: output differs with --profile dmg\n--- plain\n${plain_out}${plain_err}\n--- flag\n${flag_out}${flag_err}")
endif()
string(LENGTH "${plain_out}${plain_err}" bytes)
if(bytes EQUAL 0)
  message(FATAL_ERROR "profile-identity-empty: nothing to compare")
endif()
message("profile-identity pass bytes=${bytes}")
