if(NOT DEFINED GBB_INSTALL_PREFIX)
  message(FATAL_ERROR "GBB_INSTALL_PREFIX is required")
endif()

include(GNUInstallDirs)
set(prefix "${GBB_INSTALL_PREFIX}")
set(header "${prefix}/${CMAKE_INSTALL_INCLUDEDIR}/gabbaboy/gabbaboy.h")
set(runner "${prefix}/${CMAKE_INSTALL_BINDIR}/gabbaboy-runner${CMAKE_EXECUTABLE_SUFFIX}")
set(fixture_dir "${prefix}/${CMAKE_INSTALL_DATADIR}/gabbaboy/fixtures/tracer")
set(package_dir "${prefix}/${CMAKE_INSTALL_LIBDIR}/cmake/GabbaBoy")
foreach(required IN ITEMS
    "${header}"
    "${runner}"
    "${fixture_dir}/tracer.gb"
    "${fixture_dir}/manifest.json"
    "${fixture_dir}/LICENSE.txt"
    "${package_dir}/GabbaBoyTargets.cmake"
    "${package_dir}/GabbaBoyConfig.cmake"
    "${package_dir}/GabbaBoyConfigVersion.cmake")
  if(NOT EXISTS "${required}")
    message(FATAL_ERROR "Installed package is missing: ${required}")
  endif()
endforeach()

file(GLOB_RECURSE metadata_files LIST_DIRECTORIES false "${package_dir}/*")
foreach(metadata IN LISTS metadata_files)
  file(READ "${metadata}" content)
  foreach(private_path IN ITEMS "${CMAKE_SOURCE_DIR}" "${CMAKE_BINARY_DIR}")
    if(NOT private_path STREQUAL "" AND content MATCHES "${private_path}")
      message(FATAL_ERROR "Private source/build path leaked into ${metadata}: ${private_path}")
    endif()
  endforeach()
endforeach()

message(STATUS "Installed GabbaBoy package contents and relocatable metadata verified at ${prefix}")
