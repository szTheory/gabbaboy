# Fails unless every Phase 11 public symbol appears in each installed consumer source (D-42).
#
# Inputs (-D): GBB_CONSUMER_SOURCES  comma-separated consumer files to scan
#              GBB_SYMBOLS           comma-separated symbol names
# (commas, so the values survive being nested inside another -P command list)
string(REPLACE "," ";" GBB_CONSUMER_SOURCES "${GBB_CONSUMER_SOURCES}")
string(REPLACE "," ";" GBB_SYMBOLS "${GBB_SYMBOLS}")
foreach(gbb_source IN LISTS GBB_CONSUMER_SOURCES)
  file(READ "${gbb_source}" gbb_consumer_text)
  foreach(gbb_symbol IN LISTS GBB_SYMBOLS)
    string(FIND "${gbb_consumer_text}" "${gbb_symbol}" gbb_at)
    if(gbb_at EQUAL -1)
      message(FATAL_ERROR "consumer-symbol-missing ${gbb_symbol} ${gbb_source}")
    endif()
  endforeach()
endforeach()
message(STATUS "consumer-symbol-coverage pass")
