# Resolve a revision input to an immutable commit id before registering boundary CTests.
#
# The save-format and host-contract test commands read files with `git show`, so they must all
# capture the same point-in-time commit. A symbolic HEAD is accepted as the input, then resolved
# once during CMake configuration. If the requested ref cannot be resolved, callers receive the
# fail-closed `unknown` value and their registered checks reject it.
function(gbb_resolve_contract_revision source_dir requested out_revision out_status)
  set(resolved "")
  execute_process(
    COMMAND git rev-parse --verify --quiet "${requested}^{commit}"
    WORKING_DIRECTORY "${source_dir}"
    RESULT_VARIABLE result
    OUTPUT_VARIABLE resolved
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET)
  string(LENGTH "${resolved}" resolved_length)
  if("${result}" STREQUAL "0" AND resolved_length EQUAL 40 AND resolved MATCHES "^[0-9a-f]+$")
    set(${out_revision} "${resolved}" PARENT_SCOPE)
    set(${out_status} "resolved" PARENT_SCOPE)
  else()
    set(${out_revision} "unknown" PARENT_SCOPE)
    set(${out_status} "unreadable" PARENT_SCOPE)
  endif()
endfunction()

# Script mode provides direct positive and negative CTest controls for the exact resolver used
# during project configuration. Include mode only defines the function above.
if(DEFINED GBB_RESOLVE_CONTRACT_REVISION_EXPECT)
  foreach(required GBB_RESOLVE_CONTRACT_REVISION_SOURCE GBB_RESOLVE_CONTRACT_REVISION_REF)
    if(NOT DEFINED ${required} OR "${${required}}" STREQUAL "")
      message(FATAL_ERROR "contract-revision: missing ${required}")
    endif()
  endforeach()
  gbb_resolve_contract_revision(
    "${GBB_RESOLVE_CONTRACT_REVISION_SOURCE}"
    "${GBB_RESOLVE_CONTRACT_REVISION_REF}"
    resolved_revision
    resolve_status)
  if(GBB_RESOLVE_CONTRACT_REVISION_EXPECT STREQUAL "resolved")
    if(NOT resolve_status STREQUAL "resolved")
      message(FATAL_ERROR "contract-revision: expected a resolvable ref, got ${resolve_status}")
    endif()
    message(STATUS
      "contract-revision pass input=${GBB_RESOLVE_CONTRACT_REVISION_REF} rev=${resolved_revision}")
  elseif(GBB_RESOLVE_CONTRACT_REVISION_EXPECT STREQUAL "unreadable")
    if(NOT resolve_status STREQUAL "unreadable" OR NOT resolved_revision STREQUAL "unknown")
      message(FATAL_ERROR "contract-revision: unreadable ref did not fail closed")
    endif()
    message(STATUS "contract-revision reject reason=unreadable")
  else()
    message(FATAL_ERROR
      "contract-revision: unsupported expectation ${GBB_RESOLVE_CONTRACT_REVISION_EXPECT}")
  endif()
endif()
