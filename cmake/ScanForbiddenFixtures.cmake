# Repository-only policy scan for the sibling Mooneye MBC ROMs (D-31, D-32).
#
# The third-party derivatives under fixtures/mooneye-mbc are repository test fixtures. They must
# never reach an install tree, the extracted preview package or the staged player package. This
# script walks a tree without following symlinks and fails closed on either a path component that
# contains "mooneye" (case-insensitive) or a regular file whose size and SHA-256 equal a manifest
# ROM, so renaming a ROM does not hide it. It uses only primitives available in CMake 3.25.
#
# Inputs (all passed with -D):
#   GBB_SCAN_DIR              tree to scan (required)
#   GBB_FORBIDDEN_MANIFEST    fixtures/mooneye-mbc/manifest.json (required)
#   GBB_EXPECT_FIXTURE_DIRS   optional list of the exact children share/gabbaboy/fixtures must have;
#                             '|' is accepted as the separator because callers pass this inside
#                             another ';'-separated command list
#
# Failure tokens: scan-dir-empty, mooneye-installed: <relative path>, fixture-dirs-mismatch.
cmake_minimum_required(VERSION 3.25)

foreach(required GBB_SCAN_DIR GBB_FORBIDDEN_MANIFEST)
  if(NOT DEFINED ${required} OR "${${required}}" STREQUAL "")
    message(FATAL_ERROR "ScanForbiddenFixtures.cmake is missing ${required}")
  endif()
endforeach()

if(NOT IS_DIRECTORY "${GBB_SCAN_DIR}")
  message(FATAL_ERROR "scan-dir-empty: ${GBB_SCAN_DIR} missing")
endif()
if(NOT EXISTS "${GBB_FORBIDDEN_MANIFEST}")
  message(FATAL_ERROR "forbidden-manifest-missing: ${GBB_FORBIDDEN_MANIFEST}")
endif()

# Collect (size, digest) for every sibling ROM, including the 4 MiB and 8 MiB derivatives.
file(READ "${GBB_FORBIDDEN_MANIFEST}" manifest_text)
string(JSON fixture_count LENGTH "${manifest_text}" fixtures)
if(fixture_count LESS 1)
  message(FATAL_ERROR "forbidden-manifest-empty: ${GBB_FORBIDDEN_MANIFEST}")
endif()
set(forbidden_sizes "")
set(forbidden_digests "")
math(EXPR last_index "${fixture_count} - 1")
foreach(index RANGE ${last_index})
  string(JSON rom_size GET "${manifest_text}" fixtures ${index} size_bytes)
  string(JSON rom_digest GET "${manifest_text}" fixtures ${index} sha256)
  list(APPEND forbidden_sizes "${rom_size}")
  list(APPEND forbidden_digests "${rom_digest}")
endforeach()

file(GLOB_RECURSE scanned_files LIST_DIRECTORIES false RELATIVE "${GBB_SCAN_DIR}" "${GBB_SCAN_DIR}/*")
list(SORT scanned_files)
list(LENGTH scanned_files scanned_count)
if(scanned_count EQUAL 0)
  message(FATAL_ERROR "scan-dir-empty: ${GBB_SCAN_DIR}")
endif()

foreach(relative IN LISTS scanned_files)
  string(TOLOWER "${relative}" lowered)
  if(lowered MATCHES "mooneye")
    message(FATAL_ERROR "mooneye-installed: ${relative}")
  endif()
  set(candidate "${GBB_SCAN_DIR}/${relative}")
  if(IS_SYMLINK "${candidate}")
    continue()
  endif()
  file(SIZE "${candidate}" candidate_size)
  list(FIND forbidden_sizes "${candidate_size}" size_hit)
  if(size_hit EQUAL -1)
    continue()
  endif()
  file(SHA256 "${candidate}" candidate_digest)
  list(FIND forbidden_digests "${candidate_digest}" digest_hit)
  if(NOT digest_hit EQUAL -1)
    message(FATAL_ERROR "mooneye-installed: ${relative}")
  endif()
endforeach()

if(DEFINED GBB_EXPECT_FIXTURE_DIRS AND NOT "${GBB_EXPECT_FIXTURE_DIRS}" STREQUAL "")
  string(REPLACE "|" ";" expected_dirs "${GBB_EXPECT_FIXTURE_DIRS}")
  list(SORT expected_dirs)
  set(fixtures_root "${GBB_SCAN_DIR}/share/gabbaboy/fixtures")
  set(actual_dirs "")
  if(IS_DIRECTORY "${fixtures_root}")
    file(GLOB children LIST_DIRECTORIES true RELATIVE "${fixtures_root}" "${fixtures_root}/*")
    foreach(child IN LISTS children)
      if(IS_DIRECTORY "${fixtures_root}/${child}")
        list(APPEND actual_dirs "${child}")
      endif()
    endforeach()
    list(SORT actual_dirs)
  endif()
  if(NOT "${actual_dirs}" STREQUAL "${expected_dirs}")
    message(FATAL_ERROR "fixture-dirs-mismatch: ${actual_dirs}")
  endif()
endif()

message(STATUS "mooneye-mbc absent from scanned tree files=${scanned_count}")
