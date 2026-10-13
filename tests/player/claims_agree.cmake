# Cross-surface claim agreement (D-44, V2-29): every phrase of one fixed list must appear verbatim in
# the pinned limitations text, the README and the macOS capability_limits string of preview.yml, and
# every phrase of a shorter list in the Linux string (which has no player). A miss prints
# "claims-disagree PHRASE FILE" and exits 1.
#
# Inputs (-D): PHRASES_FILE (one phrase per line, all surfaces with a player), LINUX_PHRASES_FILE,
# LIMITATIONS, README, PREVIEW_YML.
foreach(required PHRASES_FILE LINUX_PHRASES_FILE LIMITATIONS README PREVIEW_YML)
  if(NOT DEFINED ${required} OR "${${required}}" STREQUAL "")
    message(FATAL_ERROR "claims_agree.cmake is missing ${required}")
  endif()
endforeach()

file(STRINGS "${PHRASES_FILE}" PHRASES)
file(STRINGS "${LINUX_PHRASES_FILE}" LINUX_PHRASES)
if(NOT PHRASES OR NOT LINUX_PHRASES)
  message(FATAL_ERROR "claims_agree.cmake: empty phrase list")
endif()

function(gbb_require_phrases label text)
  foreach(phrase IN LISTS ARGN)
    string(FIND "${text}" "${phrase}" found)
    if(found EQUAL -1)
      message(FATAL_ERROR "claims-disagree ${phrase} ${label}")
    endif()
  endforeach()
endfunction()

file(READ "${LIMITATIONS}" limitations_text)
file(READ "${README}" readme_text)
file(READ "${PREVIEW_YML}" preview_text)

# The two capability_limits values, in file order: Linux first, macOS second.
# The strings contain semicolons, which would split a CMake list; protect them first.
string(REPLACE ";" "<semi>" preview_text "${preview_text}")
string(REGEX MATCHALL "\"capability_limits\": \"[^\"]*\"" limit_lines "${preview_text}")
list(LENGTH limit_lines limit_count)
if(NOT limit_count EQUAL 2)
  message(FATAL_ERROR "claims-disagree capability_limits ${PREVIEW_YML} (found ${limit_count} strings, expected 2)")
endif()
list(GET limit_lines 0 linux_limits)
list(GET limit_lines 1 macos_limits)
if(NOT linux_limits MATCHES "no SDL player")
  message(FATAL_ERROR "claims-disagree no-SDL-player-in-linux-string ${PREVIEW_YML}")
endif()

gbb_require_phrases("${LIMITATIONS}" "${limitations_text}" ${PHRASES})
gbb_require_phrases("${README}" "${readme_text}" ${PHRASES})
gbb_require_phrases("${PREVIEW_YML} (macOS capability_limits)" "${macos_limits}" ${PHRASES})
gbb_require_phrases("${PREVIEW_YML} (Linux capability_limits)" "${linux_limits}" ${LINUX_PHRASES})
