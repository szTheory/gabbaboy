# Host-guide contract check (cmake -P).
#
# A host guide restates public-header behavior in prose. Two drifts make it wrong without any
# test failing: a renamed or removed name (API symbol or example configure variable) that the
# guide still uses, and an edit that drops a behavior the header promises. This check catches
# both, so guide adequacy is a CI result rather than a human reading.
#
# Inputs (passed with -D):
#   GBB_DOC       the Markdown guide to check (required)
#   GBB_DECLARATIONS  list of files that declare the names the guide may use: the public header,
#                 plus any example CMakeLists.txt whose configure variables the guide passes
#                 (required)
#   GBB_REQUIRED  list of literal phrases the guide must contain, one per promised behavior
#                 (required, nonempty); runs of whitespace in the guide compare as one space
#
# Every gbb_* and GBB_* identifier in the guide must appear as a whole word in a declaring file.
#
# Failure tokens: doc-contract-undeclared: <identifier>, doc-contract-missing: <phrase>,
# doc-contract-empty.
# Success line: "doc-contract pass identifiers=<n> phrases=<m>".
cmake_minimum_required(VERSION 3.25)

foreach(required GBB_DOC GBB_DECLARATIONS GBB_REQUIRED)
  if(NOT DEFINED ${required} OR "${${required}}" STREQUAL "")
    message(FATAL_ERROR "VerifyDocContract.cmake is missing ${required}")
  endif()
endforeach()

file(READ "${GBB_DOC}" doc)
# Collapse whitespace so rewrapping a paragraph never breaks a phrase match.
string(REGEX REPLACE "[ \t\r\n]+" " " doc "${doc}")
# Pad each file so a name at either end still has a non-identifier neighbor.
set(declared "")
foreach(declaring_file IN LISTS GBB_DECLARATIONS)
  file(READ "${declaring_file}" contents)
  string(APPEND declared " ${contents} ")
endforeach()

string(REGEX MATCHALL "(gbb|GBB)_[A-Za-z0-9_]+" identifiers "${doc}")
list(REMOVE_DUPLICATES identifiers)
list(LENGTH identifiers identifier_count)
if(identifier_count EQUAL 0)
  message(FATAL_ERROR "doc-contract-empty: ${GBB_DOC}")
endif()

set(failed FALSE)
foreach(identifier IN LISTS identifiers)
  if(NOT declared MATCHES "[^A-Za-z0-9_]${identifier}[^A-Za-z0-9_]")
    message(SEND_ERROR "doc-contract-undeclared: ${identifier}")
    set(failed TRUE)
  endif()
endforeach()

set(phrase_count 0)
foreach(phrase IN LISTS GBB_REQUIRED)
  math(EXPR phrase_count "${phrase_count} + 1")
  string(FIND "${doc}" "${phrase}" at)
  if(at EQUAL -1)
    message(SEND_ERROR "doc-contract-missing: ${phrase}")
    set(failed TRUE)
  endif()
endforeach()

if(failed)
  message(FATAL_ERROR "doc-contract fail: ${GBB_DOC}")
endif()
message(STATUS "doc-contract pass identifiers=${identifier_count} phrases=${phrase_count}")
