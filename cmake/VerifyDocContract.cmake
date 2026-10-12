# Host-guide contract check (cmake -P).
#
# A host guide restates public-header behavior in prose. Two drifts make it wrong without any
# test failing: a renamed or removed name (API symbol or example configure variable) that the
# guide still uses, and an edit that drops a behavior the header promises. This check catches
# both, so guide adequacy is a CI result rather than a human reading.
#
# Inputs (passed with -D):
#   GBB_DOC           the Markdown guide to check (required)
#   GBB_DECLARATIONS  list of files that declare the names the guide may use: the public header,
#                     plus any example CMakeLists.txt whose configure variables the guide passes
#                     (required)
#   GBB_REQUIRED      list of literal phrases the guide must contain, one per promised behavior
#                     (required; every element nonempty)
#   GBB_SCOPE_START   optional literal that opens the paragraph the phrases must sit in; the
#                     paragraph ends at the next blank line
#
# HTML comments in the guide are ignored. Comments in the declaring files are ignored (C block
# and line comments in .h/.c files, # comments elsewhere), so a name that survives only in a
# comment is undeclared. Every gbb_* and GBB_* identifier in the guide must appear as a whole
# word in a declaring file. Runs of whitespace compare as one space in the guide and phrases.
#
# Failure tokens: doc-contract-undeclared: <identifier>, doc-contract-missing: <phrase>,
# doc-contract-empty, doc-contract-empty-phrase, doc-contract-scope-missing.
# Success line: "doc-contract pass identifiers=<n> phrases=<m>".
cmake_minimum_required(VERSION 3.25)

foreach(required GBB_DOC GBB_DECLARATIONS GBB_REQUIRED)
  if(NOT DEFINED ${required} OR "${${required}}" STREQUAL "")
    message(FATAL_ERROR "VerifyDocContract.cmake is missing ${required}")
  endif()
endforeach()

# Removes every span from <open> to the next <close> (inclusive). An unclosed span runs to the end.
function(gbb_remove_spans text open close out)
  set(result "")
  while(TRUE)
    string(FIND "${text}" "${open}" at)
    if(at EQUAL -1)
      break()
    endif()
    string(SUBSTRING "${text}" 0 ${at} before)
    string(APPEND result "${before} ")
    string(LENGTH "${open}" open_length)
    math(EXPR rest_at "${at} + ${open_length}")
    string(SUBSTRING "${text}" ${rest_at} -1 text)
    string(FIND "${text}" "${close}" end)
    if(end EQUAL -1)
      set(text "")
      break()
    endif()
    string(LENGTH "${close}" close_length)
    math(EXPR rest_at "${end} + ${close_length}")
    string(SUBSTRING "${text}" ${rest_at} -1 text)
  endwhile()
  set(${out} "${result}${text}" PARENT_SCOPE)
endfunction()

# Strips C comments, taking whichever of /* and // comes first so neither hides the other.
function(gbb_strip_c_comments text out)
  set(result "")
  while(TRUE)
    string(FIND "${text}" "/*" block)
    string(FIND "${text}" "//" line)
    if(block EQUAL -1 AND line EQUAL -1)
      break()
    endif()
    if(line EQUAL -1 OR (NOT block EQUAL -1 AND block LESS line))
      set(at ${block})
      set(close "*/")
    else()
      set(at ${line})
      set(close "\n")
    endif()
    string(SUBSTRING "${text}" 0 ${at} before)
    string(APPEND result "${before} ")
    math(EXPR rest_at "${at} + 2")
    string(SUBSTRING "${text}" ${rest_at} -1 text)
    string(FIND "${text}" "${close}" end)
    if(end EQUAL -1)
      set(text "")
      break()
    endif()
    string(LENGTH "${close}" close_length)
    math(EXPR rest_at "${end} + ${close_length}")
    string(SUBSTRING "${text}" ${rest_at} -1 text)
  endwhile()
  set(${out} "${result}${text}" PARENT_SCOPE)
endfunction()

# Collapses ASCII whitespace and UTF-8 no-break spaces (C2 A0) to one space.
function(gbb_collapse_space text out)
  string(ASCII 194 160 nbsp)
  string(REPLACE "${nbsp}" " " text "${text}")
  string(REGEX REPLACE "[ \t\r\n]+" " " text "${text}")
  set(${out} "${text}" PARENT_SCOPE)
endfunction()

file(READ "${GBB_DOC}" raw_doc)
gbb_remove_spans("${raw_doc}" "<!--" "-->" raw_doc)
gbb_collapse_space("${raw_doc}" doc)

set(scope "${doc}")
if(DEFINED GBB_SCOPE_START AND NOT "${GBB_SCOPE_START}" STREQUAL "")
  string(FIND "${raw_doc}" "${GBB_SCOPE_START}" scope_at)
  if(scope_at EQUAL -1)
    message(FATAL_ERROR "doc-contract-scope-missing: ${GBB_SCOPE_START}")
  endif()
  string(SUBSTRING "${raw_doc}" ${scope_at} -1 scope)
  string(REGEX REPLACE "\r\n" "\n" scope "${scope}")
  string(REGEX MATCH "\n[ \t]*\n" blank_line "${scope}")
  if(NOT blank_line STREQUAL "")
    string(FIND "${scope}" "${blank_line}" scope_end)
    string(SUBSTRING "${scope}" 0 ${scope_end} scope)
  endif()
  gbb_collapse_space("${scope}" scope)
endif()

# Pad each file so a name at either end still has a non-identifier neighbor.
set(declared "")
foreach(declaring_file IN LISTS GBB_DECLARATIONS)
  file(READ "${declaring_file}" contents)
  if(declaring_file MATCHES "[.][ch]$")
    gbb_strip_c_comments("${contents}" contents)
  else()
    string(REGEX REPLACE "#[^\n]*" " " contents "${contents}")
  endif()
  string(APPEND declared " ${contents} ")
endforeach()

# The leading group keeps a longer name such as libgbb_x from yielding gbb_x.
string(REGEX MATCHALL "(^|[^A-Za-z0-9_])(gbb|GBB)_[A-Za-z0-9_]+" matches " ${doc}")
set(identifiers "")
foreach(match IN LISTS matches)
  string(REGEX REPLACE "^[^A-Za-z0-9_]" "" match "${match}")
  list(APPEND identifiers "${match}")
endforeach()
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
  gbb_collapse_space("${phrase}" phrase)
  if(phrase STREQUAL "" OR phrase STREQUAL " ")
    message(SEND_ERROR "doc-contract-empty-phrase")
    set(failed TRUE)
    continue()
  endif()
  math(EXPR phrase_count "${phrase_count} + 1")
  string(FIND "${scope}" "${phrase}" at)
  if(at EQUAL -1)
    message(SEND_ERROR "doc-contract-missing: ${phrase}")
    set(failed TRUE)
  endif()
endforeach()

if(failed)
  message(FATAL_ERROR "doc-contract fail: ${GBB_DOC}")
endif()
message(STATUS "doc-contract pass identifiers=${identifier_count} phrases=${phrase_count}")
