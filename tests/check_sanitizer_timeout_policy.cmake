if(NOT DEFINED GBB_SOURCE_DIR OR NOT DEFINED GBB_BINARY_DIR)
  message(FATAL_ERROR "GBB_SOURCE_DIR and GBB_BINARY_DIR are required")
endif()

# Phase 16 D-23: temp hygiene. -DGBB_POLICY_MODE=assert-clean is the sanitizer_timeout_policy_temp_clean test:
# after a passing policy run no sanitizer-timeout-policy-* directory may remain in the build directory.
file(GLOB gbb_policy_siblings LIST_DIRECTORIES true "${GBB_BINARY_DIR}/sanitizer-timeout-policy-*")
if(DEFINED GBB_POLICY_MODE AND GBB_POLICY_MODE STREQUAL "assert-clean")
  if(gbb_policy_siblings)
    message(FATAL_ERROR "Sanitizer timeout policy left temporary directories behind: ${gbb_policy_siblings}")
  endif()
  message(STATUS "sanitizer timeout policy temp clean pass")
  return()
elseif(DEFINED GBB_POLICY_MODE AND NOT GBB_POLICY_MODE STREQUAL "")
  message(FATAL_ERROR "Unknown GBB_POLICY_MODE '${GBB_POLICY_MODE}'")
endif()

# A failed earlier run keeps its directory for diagnosis; the next run sweeps those stale siblings first.
foreach(gbb_policy_stale IN LISTS gbb_policy_siblings)
  file(REMOVE_RECURSE "${gbb_policy_stale}")
endforeach()

string(RANDOM LENGTH 8 ALPHABET 0123456789abcdef gbb_policy_nonce)
set(gbb_policy_root "${GBB_BINARY_DIR}/sanitizer-timeout-policy-${gbb_policy_nonce}")
file(MAKE_DIRECTORY "${gbb_policy_root}")

function(gbb_configure_timeout_policy scenario sanitizers output_var)
  set(gbb_build_dir "${gbb_policy_root}/${scenario}")
  execute_process(
    COMMAND "${CMAKE_COMMAND}"
      -S "${GBB_SOURCE_DIR}/tests/cmake/timeout-policy"
      -B "${gbb_build_dir}"
      "-DGBB_TIMEOUT_HELPER=${GBB_SOURCE_DIR}/cmake/ScaleSanitizerTimeouts.cmake"
      "-DGBB_POLICY_SCENARIO=${scenario}"
      "-DGBB_POLICY_SANITIZERS=${sanitizers}"
    RESULT_VARIABLE gbb_configure_result
    OUTPUT_VARIABLE gbb_configure_output
    ERROR_VARIABLE gbb_configure_error)
  if(NOT gbb_configure_result EQUAL 0)
    message(FATAL_ERROR
      "Timeout policy probe '${scenario}' did not configure:\n"
      "${gbb_configure_output}${gbb_configure_error}")
  endif()
  file(READ "${gbb_build_dir}/timeout-properties.txt" gbb_properties)
  set(${output_var} "${gbb_properties}" PARENT_SCOPE)
endfunction()

function(gbb_expect_timeout properties test_name expected)
  set(gbb_property_line "")
  string(REPLACE "\n" ";" gbb_property_lines "${properties}")
  foreach(gbb_line IN LISTS gbb_property_lines)
    if(gbb_line MATCHES "^${test_name}=")
      set(gbb_property_line "${gbb_line}")
      break()
    endif()
  endforeach()
  if(NOT gbb_property_line STREQUAL "${test_name}=${expected}")
    message(FATAL_ERROR
      "${test_name} expected TIMEOUT ${expected}; observed '${gbb_property_line}'")
  endif()
endfunction()

function(gbb_check_scaled_policy properties output_var)
  set(gbb_policy_matches TRUE)
  foreach(gbb_case IN ITEMS "initial_120=360" "age_240=720" "partition_60=180" "late_120=360"
      "child_120=360" "child_240=720" "child_300=900")
    string(REPLACE "=" ";" gbb_pair "${gbb_case}")
    list(GET gbb_pair 0 gbb_name)
    list(GET gbb_pair 1 gbb_expected)
    set(gbb_line "")
    string(REPLACE "\n" ";" gbb_property_lines "${properties}")
    foreach(gbb_candidate IN LISTS gbb_property_lines)
      if(gbb_candidate MATCHES "^${gbb_name}=")
        set(gbb_line "${gbb_candidate}")
        break()
      endif()
    endforeach()
    if(NOT gbb_line STREQUAL "${gbb_name}=${gbb_expected}")
      set(gbb_policy_matches FALSE)
    endif()
  endforeach()
  set(${output_var} "${gbb_policy_matches}" PARENT_SCOPE)
endfunction()

gbb_configure_timeout_policy(normal OFF gbb_normal_properties)
gbb_expect_timeout("${gbb_normal_properties}" initial_120 120)
gbb_expect_timeout("${gbb_normal_properties}" age_240 240)
gbb_expect_timeout("${gbb_normal_properties}" partition_60 60)
gbb_expect_timeout("${gbb_normal_properties}" late_120 120)
gbb_expect_timeout("${gbb_normal_properties}" child_120 120)
gbb_expect_timeout("${gbb_normal_properties}" child_240 240)
gbb_expect_timeout("${gbb_normal_properties}" child_300 300)

gbb_configure_timeout_policy(complete ON gbb_scaled_properties)
gbb_expect_timeout("${gbb_scaled_properties}" initial_120 360)
gbb_expect_timeout("${gbb_scaled_properties}" age_240 720)
gbb_expect_timeout("${gbb_scaled_properties}" partition_60 180)
gbb_expect_timeout("${gbb_scaled_properties}" late_120 360)
gbb_expect_timeout("${gbb_scaled_properties}" child_120 360)
gbb_expect_timeout("${gbb_scaled_properties}" child_240 720)
gbb_expect_timeout("${gbb_scaled_properties}" child_300 900)

# Negative control: the review's early snapshot leaves the late registration at its normal limit.
gbb_configure_timeout_policy(early ON gbb_early_properties)
gbb_check_scaled_policy("${gbb_early_properties}" gbb_early_matches)
if(gbb_early_matches)
  message(FATAL_ERROR "Early-scaler negative control unexpectedly met the complete policy")
endif()
gbb_expect_timeout("${gbb_early_properties}" late_120 120)

# Negative control: calling the shared pass twice multiplies limits twice.
gbb_configure_timeout_policy(double ON gbb_double_properties)
gbb_check_scaled_policy("${gbb_double_properties}" gbb_double_matches)
if(gbb_double_matches)
  message(FATAL_ERROR "Double-scaler negative control unexpectedly met the complete policy")
endif()
gbb_expect_timeout("${gbb_double_properties}" initial_120 1080)
gbb_expect_timeout("${gbb_double_properties}" child_120 1080)

# Negative control: the parent's complete pass leaves a child's tests untouched.
gbb_configure_timeout_policy(parent-only ON gbb_parent_only_properties)
gbb_check_scaled_policy("${gbb_parent_only_properties}" gbb_parent_only_matches)
if(gbb_parent_only_matches)
  message(FATAL_ERROR "Parent-only negative control unexpectedly met the complete policy")
endif()
gbb_expect_timeout("${gbb_parent_only_properties}" initial_120 360)
gbb_expect_timeout("${gbb_parent_only_properties}" child_120 120)
gbb_expect_timeout("${gbb_parent_only_properties}" child_240 240)
gbb_expect_timeout("${gbb_parent_only_properties}" child_300 300)

# Every assertion above raises FATAL_ERROR on failure, which keeps this directory for diagnosis. Reaching here
# means the policy passed, so remove the probe build trees.
file(REMOVE_RECURSE "${gbb_policy_root}")

message(STATUS "sanitizer timeout policy pass normal=unchanged scaled=120:360,240:720,60:180 child=120:360,240:720,300:900 early-scaler=detected double-scaler=detected parent-only=detected")
