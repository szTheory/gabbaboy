if(NOT DEFINED GBB_RUNNER)
  message(FATAL_ERROR "runner help check is missing the executable path")
endif()

execute_process(
  COMMAND "${GBB_RUNNER}" --help
  RESULT_VARIABLE result
  OUTPUT_VARIABLE output
  ERROR_VARIABLE error)
if(NOT result STREQUAL "0")
  message(FATAL_ERROR "runner --help exited ${result}: ${output}${error}")
endif()

set(help_text "${output}${error}")
foreach(expected
    "Usage:"
    "<rom.gb>"
    "--manifest <manifest.json> --case <id> [--profile dmg|cgb] [--receipt]"
    "--manifest <manifest.json> --suite [--profile dmg|cgb] [--receipt]"
    "--profile dmg|cgb"
    "--rom <rom.gb> --save-dir <dir>"
    "--acceptance <cases.txt> (--case <id> | --suite --expect-excluded <n>)"
    "--acceptance <cases.txt> --case <id> --observe")
  string(FIND "${help_text}" "${expected}" found)
  if(found EQUAL -1)
    message(FATAL_ERROR "runner --help is missing '${expected}': ${help_text}")
  endif()
endforeach()
