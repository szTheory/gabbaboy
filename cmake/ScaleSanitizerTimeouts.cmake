# Test properties are directory-scoped at the CMake 3.25 floor. Call this once after the
# final registration in each test directory, including optional child directories.
function(gbb_scale_sanitizer_test_timeouts)
  if(NOT GABBABOY_ENABLE_SANITIZERS)
    return()
  endif()

  get_property(gbb_registered_tests DIRECTORY PROPERTY TESTS)
  foreach(gbb_test IN LISTS gbb_registered_tests)
    get_test_property(${gbb_test} TIMEOUT gbb_timeout)
    if(gbb_timeout)
      math(EXPR gbb_timeout "${gbb_timeout} * 3")
      set_tests_properties(${gbb_test} PROPERTIES TIMEOUT ${gbb_timeout})
    endif()
  endforeach()
endfunction()
