if(NOT DEFINED GBB_FILES OR "${GBB_FILES}" STREQUAL "")
  message(FATAL_ERROR "check_no_stale_speed_claims.cmake is missing GBB_FILES")
endif()

set(gbb_stale_needles
  "no double speed"
  "Not implemented: double speed"
  "double-speed clock behavior"
  "no CGB double-speed clock"
  "planned for the CGB phase")
set(gbb_stale_found 0)

foreach(gbb_file IN LISTS GBB_FILES)
  if(NOT EXISTS "${gbb_file}")
    message(FATAL_ERROR "check_no_stale_speed_claims.cmake: missing file ${gbb_file}")
  endif()
  file(READ "${gbb_file}" gbb_text)
  string(REPLACE "\r\n" "\n" gbb_text "${gbb_text}")
  string(REPLACE "\n" " " gbb_flat_text "${gbb_text}")
  foreach(gbb_needle IN LISTS gbb_stale_needles)
    string(FIND "${gbb_flat_text}" "${gbb_needle}" gbb_at)
    if(NOT gbb_at EQUAL -1)
      message(SEND_ERROR "stale-speed-claim: ${gbb_file}: ${gbb_needle}")
      set(gbb_stale_found 1)
    endif()
  endforeach()
endforeach()

if(gbb_stale_found)
  message(FATAL_ERROR "stale-speed-claim")
endif()
message(STATUS "no-stale-speed-claims pass")
