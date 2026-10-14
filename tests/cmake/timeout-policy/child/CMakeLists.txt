gbb_policy_add_test(child_120 120)
gbb_policy_add_test(child_240 240)
gbb_policy_add_test(child_300 300)

# The parent-only control reproduces the missing child-directory pass from WR-02.
if(NOT GBB_POLICY_SCENARIO STREQUAL "parent-only")
  gbb_scale_sanitizer_test_timeouts()
  if(GBB_POLICY_SCENARIO STREQUAL "double")
    gbb_scale_sanitizer_test_timeouts()
  endif()
endif()

foreach(gbb_test IN ITEMS child_120 child_240 child_300)
  get_test_property(${gbb_test} TIMEOUT gbb_timeout)
  file(APPEND "${CMAKE_BINARY_DIR}/timeout-properties.txt" "${gbb_test}=${gbb_timeout}\n")
endforeach()
