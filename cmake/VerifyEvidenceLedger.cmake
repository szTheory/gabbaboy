# Evidence-ledger name check (cmake -P).
#
# An evidence ledger cites registered CTest names in the last column of every table under its
# "## Claim table" heading. A renamed or removed test would leave the ledger claiming evidence
# that no longer runs, so every backticked name in that column must appear in one of the exact
# test inventories.
#
# Inputs (passed with -D):
#   GBB_LEDGER       the Markdown ledger to check (required)
#   GBB_INVENTORIES  list of inventory files, one test name per line (required)
#
# Failure tokens: evidence-ledger-unregistered: <name>, evidence-ledger-empty.
# Success line: "evidence-ledger pass names=<n>".
cmake_minimum_required(VERSION 3.25)

foreach(required GBB_LEDGER GBB_INVENTORIES)
  if(NOT DEFINED ${required} OR "${${required}}" STREQUAL "")
    message(FATAL_ERROR "VerifyEvidenceLedger.cmake is missing ${required}")
  endif()
endforeach()

set(gbb_registered "")
foreach(inventory IN LISTS GBB_INVENTORIES)
  file(STRINGS "${inventory}" names)
  list(APPEND gbb_registered ${names})
endforeach()

file(STRINGS "${GBB_LEDGER}" lines)
set(in_claims FALSE)
set(checked 0)
set(failed FALSE)
foreach(line IN LISTS lines)
  if(line MATCHES "^## ")
    if(line STREQUAL "## Claim table")
      set(in_claims TRUE)
    else()
      set(in_claims FALSE)
    endif()
    continue()
  endif()
  if(NOT in_claims OR NOT line MATCHES "^\\|.*\\|[ \t]*$")
    continue()
  endif()
  # Last cell: the text between the final two pipes.
  string(REGEX REPLACE "\\|[ \t]*$" "" row "${line}")
  string(REGEX REPLACE "^.*\\|" "" cell "${row}")
  string(REGEX MATCHALL "`[a-z][a-z0-9_]*`" cited "${cell}")
  foreach(token IN LISTS cited)
    string(REPLACE "`" "" name "${token}")
    math(EXPR checked "${checked} + 1")
    if(NOT name IN_LIST gbb_registered)
      message(STATUS "evidence-ledger-unregistered: ${name}")
      set(failed TRUE)
    endif()
  endforeach()
endforeach()

if(checked EQUAL 0)
  message(FATAL_ERROR "evidence-ledger-empty: ${GBB_LEDGER}")
endif()
if(failed)
  message(FATAL_ERROR "evidence-ledger check failed")
endif()
message(STATUS "evidence-ledger pass names=${checked}")
