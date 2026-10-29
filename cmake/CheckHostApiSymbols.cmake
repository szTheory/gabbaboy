# Public-API-only proof for host code (Phase 18, D-04).
#
# The host library (and later the slot library) must reach the core only through the public header.
# Two independent layers:
#
#   object layer  every undefined `gbb_*` symbol of each archive must be a function declared in the public
#                 header. A call to a core test seam (gbb_test_*), an acceptance entry point or anything
#                 else private is therefore undeclared, whatever the source says.
#   source layer  no scanned .c/.h file includes the core test seam header, the acceptance headers or
#                 their private input seam, whatever the include path.
#
# Inputs (all passed with -D):
#   GBB_ARCHIVES       list of static archives to read (required unless GBB_SYMBOLS_FILE is given)
#   GBB_HEADER         the public header declaring the allowed gbb_* functions (required)
#   GBB_SOURCE_DIRS    list of directories whose *.c and *.h files are scanned
#   GBB_SOURCE_FILES   optional list of individual files scanned like the directories, so a later plan can
#                      add src/player/slots.c;src/player/slots.h without editing this script
#   GBB_SYMBOLS_FILE   optional pre-made nm -u listing used instead of reading GBB_ARCHIVES (injection)
#   GBB_NM             optional preferred nm-compatible tool (CMAKE_NM)
#
# Controls mode (GBB_CONTROL_SEAM_ARCHIVE and GBB_CONTROL_INCLUDE_DIR set): runs this script twice more as
# child processes and requires each seeded defect to be rejected for its own reason only.
#
# Failure tokens: host-api-undeclared: <name>, host-api-include: <file>, host-api-tool-missing,
# host-api-symbols-empty, host-api-archive-missing: <path>, host-api-header-missing: <path>.
# Success lines: "host-api pass archives=<n> symbols=<m>" (m counts distinct undefined gbb_* symbols),
# "host-api controls pass controls=2".
cmake_minimum_required(VERSION 3.25)

set(gbb_denied_includes gabbaboy_test.h gbb_accept.h acceptance.h gbb_accept_input.h)

# ---- controls mode -------------------------------------------------------------------------
if(DEFINED GBB_CONTROL_SEAM_ARCHIVE AND NOT "${GBB_CONTROL_SEAM_ARCHIVE}" STREQUAL "")
  foreach(required GBB_CONTROL_INCLUDE_DIR GBB_HEADER GBB_SOURCE_DIRS GBB_ARCHIVES)
    if(NOT DEFINED ${required} OR "${${required}}" STREQUAL "")
      message(FATAL_ERROR "CheckHostApiSymbols.cmake controls mode is missing ${required}")
    endif()
  endforeach()
  set(gbb_common "-DGBB_HEADER=${GBB_HEADER}" "-DGBB_NM=${GBB_NM}")
  # Control (a): an archive that calls a core test seam, with clean sources. Only the symbol layer may fail.
  execute_process(
    COMMAND "${CMAKE_COMMAND}" ${gbb_common} "-DGBB_ARCHIVES=${GBB_CONTROL_SEAM_ARCHIVE}"
      "-DGBB_SOURCE_DIRS=${GBB_SOURCE_DIRS}" -P "${CMAKE_CURRENT_LIST_FILE}"
    RESULT_VARIABLE seam_rc OUTPUT_VARIABLE seam_out ERROR_VARIABLE seam_err)
  set(seam_all "${seam_out}${seam_err}")
  message(STATUS "control seam: rc=${seam_rc}")
  string(REGEX MATCHALL "host-api-undeclared: [A-Za-z0-9_]+" seam_lines "${seam_all}")
  foreach(line IN LISTS seam_lines)
    message(STATUS "${line}")
  endforeach()
  if(seam_rc EQUAL 0 OR
     NOT seam_all MATCHES "host-api-undeclared: gbb_test_force_state_seam_probe" OR
     seam_all MATCHES "host-api-include")
    message(FATAL_ERROR "host-api seam control was not rejected for its own reason (rc=${seam_rc}): ${seam_all}")
  endif()
  # Control (b): the real archives, with a source directory holding a test-seam include. Only the source layer may fail.
  execute_process(
    COMMAND "${CMAKE_COMMAND}" ${gbb_common} "-DGBB_ARCHIVES=${GBB_ARCHIVES}"
      "-DGBB_SOURCE_DIRS=${GBB_CONTROL_INCLUDE_DIR}" -P "${CMAKE_CURRENT_LIST_FILE}"
    RESULT_VARIABLE include_rc OUTPUT_VARIABLE include_out ERROR_VARIABLE include_err)
  set(include_all "${include_out}${include_err}")
  message(STATUS "control include: rc=${include_rc}")
  string(REGEX MATCHALL "host-api-include: [^\n]*" include_lines "${include_all}")
  foreach(line IN LISTS include_lines)
    message(STATUS "${line}")
  endforeach()
  if(include_rc EQUAL 0 OR NOT include_all MATCHES "host-api-include: " OR
     include_all MATCHES "host-api-undeclared")
    message(FATAL_ERROR "host-api include control was not rejected for its own reason (rc=${include_rc}): ${include_all}")
  endif()
  message(STATUS "host-api controls pass controls=2")
  return()
endif()

if(NOT DEFINED GBB_HEADER OR NOT EXISTS "${GBB_HEADER}")
  message(FATAL_ERROR "host-api-header-missing: '${GBB_HEADER}'")
endif()
if((NOT DEFINED GBB_SOURCE_DIRS OR "${GBB_SOURCE_DIRS}" STREQUAL "") AND
   (NOT DEFINED GBB_SOURCE_FILES OR "${GBB_SOURCE_FILES}" STREQUAL ""))
  message(FATAL_ERROR "CheckHostApiSymbols.cmake is missing GBB_SOURCE_DIRS or GBB_SOURCE_FILES")
endif()

# Removes /* */ and // comments; whichever opener comes first wins, as in the C lexer. Copied from
# CheckCoreNoHostClock.cmake (scripts here stay independent of each other).
function(gbb_strip_comments text out)
  set(result "")
  set(rest "${text}")
  while(TRUE)
    string(FIND "${rest}" "/*" block_open)
    string(FIND "${rest}" "//" line_open)
    if(block_open EQUAL -1 AND line_open EQUAL -1)
      string(APPEND result "${rest}")
      break()
    endif()
    if(NOT line_open EQUAL -1 AND (block_open EQUAL -1 OR line_open LESS block_open))
      string(SUBSTRING "${rest}" 0 ${line_open} head)
      string(APPEND result "${head}")
      string(SUBSTRING "${rest}" ${line_open} -1 after_open)
      string(FIND "${after_open}" "\n" newline)
      if(newline EQUAL -1)
        break()
      endif()
      string(SUBSTRING "${after_open}" ${newline} -1 rest)
      continue()
    endif()
    string(SUBSTRING "${rest}" 0 ${block_open} head)
    string(APPEND result "${head}")
    math(EXPR body_start "${block_open} + 2")
    string(SUBSTRING "${rest}" ${body_start} -1 after_open)
    string(FIND "${after_open}" "*/" close)
    if(close EQUAL -1)
      break()
    endif()
    math(EXPR tail_start "${close} + 2")
    string(SUBSTRING "${after_open}" ${tail_start} -1 rest)
    string(APPEND result " ")
  endwhile()
  set(${out} "${result}" PARENT_SCOPE)
endfunction()

# nm -u output: "file.o:" header lines, then either bare names (Mach-O) or "U name" / "w name".
# Copied from CheckCoreNoHostClock.cmake.
function(gbb_parse_nm listing out)
  string(REPLACE "\r" "" listing "${listing}")
  string(REPLACE "\n" ";" lines "${listing}")
  set(names "")
  foreach(line IN LISTS lines)
    if(line MATCHES "^[ \t]*([Uw][ \t]+)?([^ \t:]+)[ \t]*$")
      list(APPEND names "${CMAKE_MATCH_2}")
    endif()
  endforeach()
  set(${out} "${names}" PARENT_SCOPE)
endfunction()

# Undefined symbol names of one archive, via nm / llvm-nm. A missing tool fails; it is never a silent pass.
function(gbb_read_undefined_symbols archive out)
  if(NOT EXISTS "${archive}")
    message(FATAL_ERROR "host-api-archive-missing: ${archive}")
  endif()
  set(nm_candidates "")
  if(DEFINED GBB_NM AND NOT "${GBB_NM}" STREQUAL "" AND NOT GBB_NM MATCHES "NOTFOUND")
    list(APPEND nm_candidates "${GBB_NM}")
  endif()
  foreach(name nm llvm-nm)
    find_program(gbb_found_${name} NAMES ${name})
    if(gbb_found_${name})
      list(APPEND nm_candidates "${gbb_found_${name}}")
    endif()
  endforeach()
  list(REMOVE_DUPLICATES nm_candidates)
  foreach(nm_tool IN LISTS nm_candidates)
    execute_process(COMMAND "${nm_tool}" -u "${archive}"
      RESULT_VARIABLE rc OUTPUT_VARIABLE listing ERROR_VARIABLE err)
    if(rc EQUAL 0)
      gbb_parse_nm("${listing}" names)
      set(${out} "${names}" PARENT_SCOPE)
      return()
    endif()
  endforeach()
  message(FATAL_ERROR "host-api-tool-missing")
endfunction()

# ---- declared names ------------------------------------------------------------------------
file(READ "${GBB_HEADER}" header_raw)
gbb_strip_comments("${header_raw}" header_text)
string(REGEX MATCHALL "(^|[^A-Za-z0-9_])gbb_[a-z0-9_]+[ \t\n]*[(]" prototypes "${header_text}")
set(gbb_declared "")
foreach(prototype IN LISTS prototypes)
  string(REGEX MATCH "gbb_[a-z0-9_]+" name "${prototype}")
  list(APPEND gbb_declared "${name}")
endforeach()
list(REMOVE_DUPLICATES gbb_declared)
list(LENGTH gbb_declared declared_count)
if(declared_count EQUAL 0)
  message(FATAL_ERROR "host-api-header-missing: no gbb_ prototypes found in ${GBB_HEADER}")
endif()

# ---- object layer --------------------------------------------------------------------------
set(gbb_failed FALSE)
set(gbb_archive_count 0)
set(gbb_total_symbols 0)
set(gbb_seen_symbols "")
set(gbb_all_symbols "")
if(DEFINED GBB_SYMBOLS_FILE AND NOT "${GBB_SYMBOLS_FILE}" STREQUAL "")
  file(READ "${GBB_SYMBOLS_FILE}" listing)
  gbb_parse_nm("${listing}" gbb_all_symbols)
  set(gbb_archive_count 1)
else()
  if(NOT DEFINED GBB_ARCHIVES OR "${GBB_ARCHIVES}" STREQUAL "")
    message(FATAL_ERROR "CheckHostApiSymbols.cmake is missing GBB_ARCHIVES")
  endif()
  foreach(archive IN LISTS GBB_ARCHIVES)
    math(EXPR gbb_archive_count "${gbb_archive_count} + 1")
    gbb_read_undefined_symbols("${archive}" names)
    list(APPEND gbb_all_symbols ${names})
  endforeach()
endif()

foreach(symbol IN LISTS gbb_all_symbols)
  math(EXPR gbb_total_symbols "${gbb_total_symbols} + 1")
  # Mach-O prefixes C symbols with one underscore; strip it before judging the name.
  string(REGEX REPLACE "^_" "" bare "${symbol}")
  if(NOT bare MATCHES "^gbb_")
    continue()
  endif()
  if(bare IN_LIST gbb_seen_symbols)
    continue()
  endif()
  list(APPEND gbb_seen_symbols "${bare}")
  if(NOT bare IN_LIST gbb_declared)
    message(STATUS "host-api-undeclared: ${bare}")
    set(gbb_failed TRUE)
  endif()
endforeach()
# Any real archive imports libc symbols, so an empty listing means the tool or the parser read nothing.
if(gbb_total_symbols EQUAL 0)
  message(FATAL_ERROR "host-api-symbols-empty")
endif()

# ---- source layer --------------------------------------------------------------------------
set(gbb_scan_files "")
foreach(dir IN LISTS GBB_SOURCE_DIRS)
  if(NOT IS_DIRECTORY "${dir}")
    message(FATAL_ERROR "host-api-source-dir-missing: ${dir}")
  endif()
  file(GLOB dir_files "${dir}/*.c" "${dir}/*.h")
  list(APPEND gbb_scan_files ${dir_files})
endforeach()
foreach(file IN LISTS GBB_SOURCE_FILES)
  if(NOT EXISTS "${file}")
    message(FATAL_ERROR "host-api-source-file-missing: ${file}")
  endif()
  list(APPEND gbb_scan_files "${file}")
endforeach()
if(NOT gbb_scan_files)
  message(FATAL_ERROR "host-api-source-empty: ${GBB_SOURCE_DIRS}")
endif()
foreach(file IN LISTS gbb_scan_files)
  file(READ "${file}" raw_text)
  gbb_strip_comments("${raw_text}" no_comments)
  string(REGEX MATCHALL "#[ \t]*include[ \t]*[<\"][^>\"\n]*[>\"]" includes "${no_comments}")
  foreach(include_line IN LISTS includes)
    string(REGEX REPLACE "^#[ \t]*include[ \t]*[<\"]([^>\"]*)[>\"]$" "\\1" header "${include_line}")
    get_filename_component(header_name "${header}" NAME)
    if(header_name IN_LIST gbb_denied_includes)
      message(STATUS "host-api-include: ${file} (${header})")
      set(gbb_failed TRUE)
    endif()
  endforeach()
endforeach()

if(gbb_failed)
  message(FATAL_ERROR "host-api surface check failed")
endif()
list(LENGTH gbb_seen_symbols gbb_seen_count)
message(STATUS "host-api pass archives=${gbb_archive_count} symbols=${gbb_seen_count}")
