# No-host-clock proof for the portable core (D-13).
#
# The deterministic MBC3 RTC advances only from emulated time, so src/core and the public header
# must not include a host time header or call a host clock, timer, sleep or environment function,
# and the compiled core library must not import one. Host signals are the same kind of ambient
# input (D-18): signal, sigaction, raise, kill, sigprocmask, pthread_sigmask, alarm and setitimer
# are denied at both layers, so process control stays in the host adapter. Two independent layers:
#
#   source layer  every #include is one of <stddef.h> <stdint.h> <stdlib.h> <string.h> or
#                 "gabbaboy/gabbaboy.h", "gabbaboy_test.h" (the internal test-seam header), or
#                 "gbb_accept_input.h" (the private, host-independent acceptance input seam),
#                 and no denied call appears after comments and string
#                 literals are removed. Calls are matched with a left-context class
#                 (^|[^A-Za-z0-9_]) rather than \b, which CMake regular expressions lack.
#   object layer  the undefined symbols of the gabbaboy_core library, read with nm / llvm-nm or
#                 dumpbin /SYMBOLS, must not contain a denied name (after removing __imp_ and
#                 one or two leading underscores). A missing tool fails the test; it is never a
#                 silent pass.
#
# Inputs (all passed with -D):
#   GBB_SOURCE_DIRS     list of directories whose *.c and *.h files are scanned (required)
#   GBB_CORE_LIBRARY    the compiled core library (required unless GBB_SYMBOLS_FILE is given)
#   GBB_NM              optional preferred nm-compatible tool (CMAKE_NM)
#   GBB_LINKER          optional linker path; dumpbin is looked up next to it
#   GBB_C_COMPILER      optional compiler path; dumpbin is also looked up next to it
#   GBB_SYMBOLS_FILE    optional pre-made symbol list used only by the symbol self-test; when set
#                       the source layer is skipped and the object layer reads this file
#
# Failure tokens: no-host-clock-include: <file>, no-host-clock-call: <file>,
# no-host-clock-symbol: <name>, no-host-clock-tool-missing, no-host-clock-symbols-empty.
# Success line: "no-host-clock pass files=<n> symbols=<n> tool=<name>".
cmake_minimum_required(VERSION 3.25)

set(gbb_allowed_includes "<stddef.h>" "<stdint.h>" "<stdlib.h>" "<string.h>"
  "\"gabbaboy/gabbaboy.h\"" "\"gabbaboy_test.h\"" "\"gbb_accept_input.h\"")

# Denied call names (source layer). Anything that reads or waits on host time, or reads the
# ambient environment, would make a replay depend on the machine that runs it.
set(gbb_denied_calls
  time clock clock_gettime gettimeofday timespec_get localtime gmtime mktime difftime
  nanosleep usleep sleep getenv QueryPerformanceCounter QueryPerformanceFrequency
  GetLocalTime mach_absolute_time __rdtsc
  signal sigaction raise kill sigprocmask pthread_sigmask alarm setitimer)
list(JOIN gbb_denied_calls "|" gbb_denied_call_alternatives)
set(gbb_call_regex
  "(^|[^A-Za-z0-9_])(${gbb_denied_call_alternatives}|GetSystemTime[A-Za-z]*|GetTickCount[0-9]*)[ \t]*\\(")

# Denied linked symbol names (object layer).
set(gbb_denied_symbols
  time _time32 _time64 clock clock_gettime gettimeofday timespec_get localtime localtime_r
  localtime_s gmtime gmtime_r mktime difftime nanosleep usleep sleep getenv
  QueryPerformanceCounter GetSystemTimeAsFileTime GetTickCount GetTickCount64 GetLocalTime
  mach_absolute_time __rdtsc
  signal sigaction raise kill sigprocmask pthread_sigmask alarm setitimer)

# Remove /* */ and // comments and string/char literals. Includes are read after the comments are
# removed but before literals are, because "gabbaboy/gabbaboy.h" is itself a string literal.
# Whichever comment opener comes first wins, as in the C lexer: a "/*" inside a // comment must
# not swallow the code that follows it, and a "//" inside a block comment is part of that comment.
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
      break() # an unterminated comment swallows the rest, as the C compiler would reject it
    endif()
    math(EXPR tail_start "${close} + 2")
    string(SUBSTRING "${after_open}" ${tail_start} -1 rest)
    string(APPEND result " ")
  endwhile()
  set(${out} "${result}" PARENT_SCOPE)
endfunction()

function(gbb_strip_literals text out)
  string(REGEX REPLACE "\"([^\"\\\\\n]|\\\\.)*\"" "\"\"" result "${text}")
  string(REGEX REPLACE "'([^'\\\\\n]|\\\\.)*'" "' '" result "${result}")
  set(${out} "${result}" PARENT_SCOPE)
endfunction()

set(gbb_file_count 0)
set(gbb_symbol_count 0)

# ---- source layer --------------------------------------------------------------------------
if(NOT DEFINED GBB_SYMBOLS_FILE OR "${GBB_SYMBOLS_FILE}" STREQUAL "")
  if(NOT DEFINED GBB_SOURCE_DIRS OR "${GBB_SOURCE_DIRS}" STREQUAL "")
    message(FATAL_ERROR "CheckCoreNoHostClock.cmake is missing GBB_SOURCE_DIRS")
  endif()
  set(gbb_failed FALSE)
  foreach(dir IN LISTS GBB_SOURCE_DIRS)
    if(NOT IS_DIRECTORY "${dir}")
      message(FATAL_ERROR "no-host-clock-source-dir-missing: ${dir}")
    endif()
    file(GLOB gbb_files "${dir}/*.c" "${dir}/*.h")
    foreach(file IN LISTS gbb_files)
      math(EXPR gbb_file_count "${gbb_file_count} + 1")
      file(READ "${file}" raw_text)
      gbb_strip_comments("${raw_text}" no_comments)

      string(REGEX MATCHALL "#[ \t]*include[ \t]*(<[^>\n]*>|\"[^\"\n]*\")" includes "${no_comments}")
      foreach(include_line IN LISTS includes)
        string(REGEX REPLACE "^#[ \t]*include[ \t]*" "" header "${include_line}")
        if(NOT header IN_LIST gbb_allowed_includes)
          message(STATUS "no-host-clock-include: ${file} (${header})")
          set(gbb_failed TRUE)
        endif()
      endforeach()

      gbb_strip_literals("${no_comments}" code)
      string(REGEX REPLACE "#[ \t]*include[^\n]*" "" code "${code}")
      if(code MATCHES "${gbb_call_regex}")
        message(STATUS "no-host-clock-call: ${file} (${CMAKE_MATCH_2})")
        set(gbb_failed TRUE)
      endif()
    endforeach()
  endforeach()
  if(gbb_file_count EQUAL 0)
    message(FATAL_ERROR "no-host-clock-source-dir-empty: ${GBB_SOURCE_DIRS}")
  endif()
  if(gbb_failed)
    message(FATAL_ERROR "no-host-clock source layer failed")
  endif()
endif()

# ---- object layer --------------------------------------------------------------------------
# Returns the undefined symbol names of the library in `out` and the tool label in `tool_out`.
function(gbb_read_undefined_symbols out tool_out)
  set(names "")
  if(DEFINED GBB_SYMBOLS_FILE AND NOT "${GBB_SYMBOLS_FILE}" STREQUAL "")
    file(READ "${GBB_SYMBOLS_FILE}" listing)
    set(tool "symbols-file")
    gbb_parse_nm("${listing}" names)
    set(${out} "${names}" PARENT_SCOPE)
    set(${tool_out} "${tool}" PARENT_SCOPE)
    return()
  endif()
  if(NOT DEFINED GBB_CORE_LIBRARY OR NOT EXISTS "${GBB_CORE_LIBRARY}")
    message(FATAL_ERROR "no-host-clock-library-missing: '${GBB_CORE_LIBRARY}'")
  endif()

  # nm-style tools first: the configured CMAKE_NM, then nm, then llvm-nm.
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
    execute_process(COMMAND "${nm_tool}" -u "${GBB_CORE_LIBRARY}"
      RESULT_VARIABLE rc OUTPUT_VARIABLE listing ERROR_VARIABLE err)
    if(rc EQUAL 0)
      gbb_parse_nm("${listing}" names)
      get_filename_component(tool_name "${nm_tool}" NAME_WE)
      set(${out} "${names}" PARENT_SCOPE)
      set(${tool_out} "${tool_name}" PARENT_SCOPE)
      return()
    endif()
  endforeach()

  # dumpbin /SYMBOLS for MSVC import and static libraries, found next to the linker or compiler.
  set(dumpbin_hints "")
  foreach(tool_path IN ITEMS "${GBB_LINKER}" "${GBB_C_COMPILER}")
    if(NOT "${tool_path}" STREQUAL "")
      get_filename_component(tool_dir "${tool_path}" DIRECTORY)
      list(APPEND dumpbin_hints "${tool_dir}")
    endif()
  endforeach()
  find_program(gbb_found_dumpbin NAMES dumpbin HINTS ${dumpbin_hints})
  if(gbb_found_dumpbin)
    execute_process(COMMAND "${gbb_found_dumpbin}" /NOLOGO /SYMBOLS "${GBB_CORE_LIBRARY}"
      RESULT_VARIABLE rc OUTPUT_VARIABLE listing ERROR_VARIABLE err)
    if(rc EQUAL 0)
      set(names "")
      string(REPLACE "\r" "" listing "${listing}")
      string(REGEX MATCHALL "UNDEF[^|\n]*External[ \t]*\\|[ \t]*[^ \t\n]+" undefined "${listing}")
      foreach(entry IN LISTS undefined)
        string(REGEX REPLACE "^.*\\|[ \t]*" "" symbol "${entry}")
        list(APPEND names "${symbol}")
      endforeach()
      set(${out} "${names}" PARENT_SCOPE)
      set(${tool_out} "dumpbin" PARENT_SCOPE)
      return()
    endif()
  endif()
  message(FATAL_ERROR "no-host-clock-tool-missing")
endfunction()

# nm -u output: "file.o:" header lines, then either bare names (Mach-O) or "U name" / "w name".
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

gbb_read_undefined_symbols(gbb_symbols gbb_tool)
set(gbb_symbol_failed FALSE)
foreach(symbol IN LISTS gbb_symbols)
  math(EXPR gbb_symbol_count "${gbb_symbol_count} + 1")
  # Candidates: the raw name, without __imp_, and without one or two leading underscores.
  set(candidates "${symbol}")
  string(REGEX REPLACE "^__imp_" "" bare "${symbol}")
  list(APPEND candidates "${bare}")
  string(REGEX REPLACE "^_" "" one "${bare}")
  list(APPEND candidates "${one}")
  string(REGEX REPLACE "^_" "" two "${one}")
  list(APPEND candidates "${two}")
  foreach(candidate IN LISTS candidates)
    if(candidate IN_LIST gbb_denied_symbols)
      message(STATUS "no-host-clock-symbol: ${candidate}")
      set(gbb_symbol_failed TRUE)
      break()
    endif()
  endforeach()
endforeach()
if(gbb_symbol_failed)
  message(FATAL_ERROR "no-host-clock object layer failed")
endif()
# Any real core library imports at least memcpy or malloc, so an empty listing means the tool or
# the parser read nothing; that must fail rather than pass the object layer vacuously.
if(gbb_symbol_count EQUAL 0)
  message(FATAL_ERROR "no-host-clock-symbols-empty: ${gbb_tool}")
endif()

message(STATUS "no-host-clock pass files=${gbb_file_count} symbols=${gbb_symbol_count} tool=${gbb_tool}")
