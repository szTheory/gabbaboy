foreach(required_var IN ITEMS GBB_INSTALL_PREFIX GBB_CONSUMER_SOURCE GBB_CONSUMER_BINARY GBB_LANGUAGE)
  if(NOT DEFINED ${required_var})
    message(FATAL_ERROR "${required_var} is required")
  endif()
endforeach()

set(fixture "${GBB_INSTALL_PREFIX}/share/gabbaboy/fixtures/tracer/tracer.gb")
if(NOT EXISTS "${fixture}")
  message(FATAL_ERROR "Installed tracer fixture is missing: ${fixture}")
endif()

execute_process(
  COMMAND "${CMAKE_COMMAND}" -S "${GBB_CONSUMER_SOURCE}" -B "${GBB_CONSUMER_BINARY}"
    "-DCMAKE_PREFIX_PATH=${GBB_INSTALL_PREFIX}" "-DGBB_TRACER_ROM=${fixture}"
  RESULT_VARIABLE configure_result OUTPUT_VARIABLE configure_output ERROR_VARIABLE configure_error)
if(NOT configure_result EQUAL 0)
  message(FATAL_ERROR "${GBB_LANGUAGE} consumer configure failed (${configure_result}): ${configure_output}${configure_error}")
endif()

set(build_command "${CMAKE_COMMAND}" --build "${GBB_CONSUMER_BINARY}")
if(DEFINED GBB_CONFIGURATION AND NOT GBB_CONFIGURATION STREQUAL "")
  list(APPEND build_command --config "${GBB_CONFIGURATION}")
endif()
execute_process(COMMAND ${build_command}
  RESULT_VARIABLE build_result OUTPUT_VARIABLE build_output ERROR_VARIABLE build_error)
if(NOT build_result EQUAL 0)
  message(FATAL_ERROR "${GBB_LANGUAGE} consumer build failed (${build_result}): ${build_output}${build_error}")
endif()

set(consumer_executable "${GBB_CONSUMER_BINARY}/consumer-${GBB_LANGUAGE}${CMAKE_EXECUTABLE_SUFFIX}")
if(DEFINED GBB_CONFIGURATION AND NOT GBB_CONFIGURATION STREQUAL "")
  set(configuration_executable "${GBB_CONSUMER_BINARY}/${GBB_CONFIGURATION}/consumer-${GBB_LANGUAGE}${CMAKE_EXECUTABLE_SUFFIX}")
  if(EXISTS "${configuration_executable}")
    set(consumer_executable "${configuration_executable}")
  endif()
endif()
if(NOT EXISTS "${consumer_executable}")
  message(FATAL_ERROR "Built consumer executable is missing: ${consumer_executable}")
endif()
execute_process(COMMAND "${consumer_executable}" "${fixture}"
  RESULT_VARIABLE run_result OUTPUT_VARIABLE run_output ERROR_VARIABLE run_error)
if(NOT run_result EQUAL 0)
  message(FATAL_ERROR "${GBB_LANGUAGE} consumer failed (${run_result}): ${run_output}${run_error}")
endif()
message(STATUS "Installed ${GBB_LANGUAGE} consumer passed: ${run_output}")
