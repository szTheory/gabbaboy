# Dirty-list coverage for the qualified-build stamp (Phase 18, D-04).
#
# CMakeLists.txt marks a build "qualified" only when `git diff --quiet HEAD -- <files>` is clean, so a source
# that is missing from that list can be edited without the build ever reporting itself dirty. This check
# requires every source of the runner and the host library to appear in the list.
#
# Inputs (all passed with -D):
#   GBB_ROOT_CMAKELISTS  path of the root CMakeLists.txt whose dirty list is read (required)
#   GBB_SOURCES          project-relative (or absolute) source paths that must be listed, separated by ';'
#                        or '|' ('|' survives being nested in another -D list, as expect_exit.cmake needs)
#
# Failure token: runner-source-unqualified: <path>. Success line: "qualified-sources pass sources=<n>".
cmake_minimum_required(VERSION 3.25)

foreach(required GBB_ROOT_CMAKELISTS GBB_SOURCES)
  if(NOT DEFINED ${required} OR "${${required}}" STREQUAL "")
    message(FATAL_ERROR "CheckRunnerSourcesQualified.cmake is missing ${required}")
  endif()
endforeach()
if(NOT EXISTS "${GBB_ROOT_CMAKELISTS}")
  message(FATAL_ERROR "qualified-sources-cmakelists-missing: ${GBB_ROOT_CMAKELISTS}")
endif()
get_filename_component(gbb_root "${GBB_ROOT_CMAKELISTS}" DIRECTORY)

# The file list is everything between `git diff --quiet HEAD --` and the following WORKING_DIRECTORY.
file(READ "${GBB_ROOT_CMAKELISTS}" gbb_text)
string(REGEX MATCH "git diff --quiet HEAD --([^)]*)WORKING_DIRECTORY" gbb_dirty_command "${gbb_text}")
if("${gbb_dirty_command}" STREQUAL "")
  message(FATAL_ERROR "qualified-sources-dirty-list-missing: no `git diff --quiet HEAD --` command in ${GBB_ROOT_CMAKELISTS}")
endif()
string(STRIP "${CMAKE_MATCH_1}" gbb_dirty_text)
string(REGEX REPLACE "[ \t\r\n]+" ";" gbb_dirty_list "${gbb_dirty_text}")
if(NOT gbb_dirty_list)
  message(FATAL_ERROR "qualified-sources-dirty-list-empty")
endif()

string(REPLACE "|" ";" gbb_sources "${GBB_SOURCES}")
set(gbb_failed FALSE)
set(gbb_count 0)
foreach(source IN LISTS gbb_sources)
  if(source STREQUAL "")
    continue()
  endif()
  if(IS_ABSOLUTE "${source}")
    file(RELATIVE_PATH source "${gbb_root}" "${source}")
  endif()
  math(EXPR gbb_count "${gbb_count} + 1")
  # Whole-entry membership, never a substring: `src/host/host_run.c` must not be satisfied by a longer name.
  if(NOT source IN_LIST gbb_dirty_list)
    message(STATUS "runner-source-unqualified: ${source}")
    set(gbb_failed TRUE)
  endif()
endforeach()
if(gbb_count EQUAL 0)
  message(FATAL_ERROR "qualified-sources-none-checked")
endif()
if(gbb_failed)
  message(FATAL_ERROR "runner sources are missing from the GBB_BUILD_QUALIFIED dirty list")
endif()
message(STATUS "qualified-sources pass sources=${gbb_count}")
