# Phase 18: installed host-mode smoke, host-contract documentation contracts and the interop-claim guard
# (HOST-01..03, PLAY-01; D-16, D-19, D-28, D-29).
#
# Every name registered here must also be listed in tests/expected-tests.txt (append-only). Host mode is
# POSIX-only in v0.3 (D-05), so installed_host_smoke is removed from the Windows expectation in BOTH
# cmake/ExpectedTests.cmake and .github/scripts/verify-test-inventory.sh, and from the no-install-prefix
# expectation beside installed_runner_smoke. Generated ROMs and save directories live under
# ${PROJECT_BINARY_DIR}/host-contract; nothing binary is committed. New tests keep the base 60 s timeout (D-27).
#
# This fragment is included before tests/CMakeLists.txt resolves GBB_TEST_INSTALL_PREFIX_ABSOLUTE, so it
# resolves its own.

set(GBB_HOST_CONTRACT_WORK "${PROJECT_BINARY_DIR}/host-contract")

# ---- D-28: the installed runner from an unrelated working directory (stdlib harness, POSIX only) -----------
if(GBB_TEST_INSTALL_PREFIX AND EXISTS "${GBB_TEST_INSTALL_PREFIX}" AND NOT WIN32)
  get_filename_component(GBB_HOST_CONTRACT_PREFIX
    "${GBB_TEST_INSTALL_PREFIX}" ABSOLUTE BASE_DIR "${PROJECT_BINARY_DIR}")
  add_test(NAME installed_host_smoke
    COMMAND "${Python3_EXECUTABLE}" -I "${PROJECT_SOURCE_DIR}/tests/scripts/test_installed_host.py"
      --prefix "${GBB_HOST_CONTRACT_PREFIX}"
      --work "${GBB_HOST_CONTRACT_WORK}/installed-host"
      --source-contract "${PROJECT_SOURCE_DIR}/docs/host-contract.json")
  set_tests_properties(installed_host_smoke PROPERTIES
    TIMEOUT 60
    PASS_REGULAR_EXPRESSION "installed-host pass continuation=01,02 preload=42 controls=1")
endif()

# ---- D-29: phrase contracts for the host-contract documents, each with a phrase-removed control ----------------
# The phrase checks read the working-tree documents (cmake/VerifyDocContract.cmake). Phrases hold no semicolon
# (it separates list elements), so a sentence that has one is pinned as its halves. The checker modes below read
# the documents with `git show <rev>:<path>` at HEAD as of the run, so commit before running them.

# The revision is the save-format one (tests/cmake/save-formats.cmake, included first): HEAD at run time by default.
set(GBB_HOST_CONTRACT_REV "${GBB_SAVE_FORMATS_REV}")

set(GBB_HOST_CONTRACT_DOC_SCRIPT "${PROJECT_SOURCE_DIR}/cmake/VerifyDocContract.cmake")
set(GBB_HOST_CONTRACT_CHECKER "${PROJECT_SOURCE_DIR}/tests/scripts/verify-host-contract.py")
set(GBB_HOST_CONTRACT_DECLARATIONS
  "${PROJECT_SOURCE_DIR}/include/gabbaboy/gabbaboy.h;${PROJECT_SOURCE_DIR}/examples/relocated-c/CMakeLists.txt")
set(GBB_HOST_CONTRACT_VARIANTS "${GBB_HOST_CONTRACT_WORK}/doc-variants")
file(MAKE_DIRECTORY "${GBB_HOST_CONTRACT_VARIANTS}")

# A build-tree copy of a tracked document with one literal replaced. A missing anchor is a configure error, so a
# control can never pass vacuously because the text it removes is gone. Editing the source re-runs configure.
function(gbb_host_contract_variant out_path name source_relative old new)
  set(source "${PROJECT_SOURCE_DIR}/${source_relative}")
  set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${source}")
  file(READ "${source}" contents)
  string(FIND "${contents}" "${old}" at)
  if(at EQUAL -1)
    message(FATAL_ERROR "Control anchor '${old}' is missing from ${source_relative}")
  endif()
  string(REPLACE "${old}" "${new}" contents "${contents}")
  file(WRITE "${GBB_HOST_CONTRACT_VARIANTS}/${name}" "${contents}")
  set(${out_path} "${GBB_HOST_CONTRACT_VARIANTS}/${name}" PARENT_SCOPE)
endfunction()

# gbb_host_contract_doc_test(name doc phrases scope expected_phrase_count): a positive contract and its control.
set(GBB_NATIVE_GUIDE_HOST_PHRASES
  "Run one writer per save directory and ROM stem"
  "a second runner on the same pair is unsupported and its live temporary file may be swept."
  "old-or-new image after process death or a crash"
  "no power-loss guarantee"
  "HOST-01/02 are POSIX-only in v0.3. Windows never generates SIGTERM and TerminateProcess cannot be handled"
  "no console control handler is installed."
  "The runner records no wall-clock time"
  "the game clock advances only while the runner runs."
  "save_format=none marks a cartridge without a battery"
  "it is not a save-format id."
  "`--print-save-format`"
  "32,789"
  "`.gb`, `.gbc`, `.GB`, `.GBC` and `.bin`"
  "deletingPathExtension"
  "16 quiet frames"
  "300 frames plus one write"
  "3,600 frames"
  "`gbb_get_input_clock`"
  "a second signal takes the default action"
  "`SIGTERM` always"
  "`SIGINT` and `SIGHUP` unless they were ignored at start")
list(LENGTH GBB_NATIVE_GUIDE_HOST_PHRASES GBB_NATIVE_GUIDE_HOST_PHRASE_COUNT)
add_test(NAME native_guide_host_contract
  COMMAND ${CMAKE_COMMAND}
    -DGBB_DOC=${PROJECT_SOURCE_DIR}/docs/native-integration.md
    "-DGBB_DECLARATIONS=${GBB_HOST_CONTRACT_DECLARATIONS}"
    "-DGBB_REQUIRED=${GBB_NATIVE_GUIDE_HOST_PHRASES}"
    "-DGBB_SCOPE_START=## Host process contract"
    -DGBB_SCOPE_SECTION=TRUE
    -P ${GBB_HOST_CONTRACT_DOC_SCRIPT})
set_tests_properties(native_guide_host_contract PROPERTIES TIMEOUT 60
  PASS_REGULAR_EXPRESSION "doc-contract pass identifiers=[1-9][0-9]* phrases=${GBB_NATIVE_GUIDE_HOST_PHRASE_COUNT}[^0-9]")

set(GBB_CARTRIDGE_GUIDE_SLOTS_PHRASES
  "Loading a slot also replaces the game's battery save"
  "battery-preload backup file"
  "release-bound slot from any other release"
  "nine numbered machine-state slots"
  "exact battery bytes"
  "never reads or writes a host"
  "swaps the live state with it")
list(LENGTH GBB_CARTRIDGE_GUIDE_SLOTS_PHRASES GBB_CARTRIDGE_GUIDE_SLOTS_PHRASE_COUNT)
add_test(NAME cartridge_guide_slots_contract
  COMMAND ${CMAKE_COMMAND}
    -DGBB_DOC=${PROJECT_SOURCE_DIR}/docs/cartridge-and-saves.md
    "-DGBB_DECLARATIONS=${GBB_HOST_CONTRACT_DECLARATIONS}"
    "-DGBB_REQUIRED=${GBB_CARTRIDGE_GUIDE_SLOTS_PHRASES}"
    "-DGBB_SCOPE_START=## Host raw saves and player state slots"
    -DGBB_SCOPE_SECTION=TRUE
    -P ${GBB_HOST_CONTRACT_DOC_SCRIPT})
set_tests_properties(cartridge_guide_slots_contract PROPERTIES TIMEOUT 60
  PASS_REGULAR_EXPRESSION "doc-contract pass identifiers=[1-9][0-9]* phrases=${GBB_CARTRIDGE_GUIDE_SLOTS_PHRASE_COUNT}[^0-9]")

set(GBB_README_HOST_PHRASES
  "Host mode is a headless conformance adapter, not a play surface."
  "--print-save-format"
  "--save-dir"
  "records no wall-clock time"
  "`share/gabbaboy/host-contract.json`")
list(LENGTH GBB_README_HOST_PHRASES GBB_README_HOST_PHRASE_COUNT)
add_test(NAME readme_host_mode_contract
  COMMAND ${CMAKE_COMMAND}
    -DGBB_DOC=${PROJECT_SOURCE_DIR}/README.md
    "-DGBB_DECLARATIONS=${GBB_HOST_CONTRACT_DECLARATIONS}"
    "-DGBB_REQUIRED=${GBB_README_HOST_PHRASES}"
    "-DGBB_SCOPE_START=## Host mode (headless)"
    -DGBB_SCOPE_SECTION=TRUE
    -P ${GBB_HOST_CONTRACT_DOC_SCRIPT})
set_tests_properties(readme_host_mode_contract PROPERTIES TIMEOUT 60
  PASS_REGULAR_EXPRESSION "doc-contract pass identifiers=[1-9][0-9]* phrases=${GBB_README_HOST_PHRASE_COUNT}[^0-9]")

# gbb_host_contract_missing_control(name source_relative phrase scope_start): a copy without one pinned phrase must
# fail with exactly `doc-contract-missing: <phrase>`.
function(gbb_host_contract_missing_control name source_relative phrase scope_start)
  gbb_host_contract_variant(variant "${name}.md" "${source_relative}" "${phrase}" "")
  set(command "${CMAKE_COMMAND};-DGBB_DOC=${variant};-DGBB_DECLARATIONS=${GBB_HOST_CONTRACT_DECLARATIONS};-DGBB_REQUIRED=${phrase}")
  if(NOT "${scope_start}" STREQUAL "")
    string(APPEND command ";-DGBB_SCOPE_START=${scope_start};-DGBB_SCOPE_SECTION=TRUE")
  endif()
  string(APPEND command ";-P;${GBB_HOST_CONTRACT_DOC_SCRIPT}")
  # CMake wraps a long error message at a word boundary, so any run of non-alphanumerics (a space, or a newline and
  # its indent) between two words of the phrase matches.
  string(REPLACE " " "[^A-Za-z0-9]+" phrase_regex "${phrase}")
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${command}"
      -DGBB_EXPECT_CODE=1
      "-DGBB_EXPECT_REGEX=doc-contract-missing:[^A-Za-z0-9]+${phrase_regex}"
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT 60)
endfunction()

gbb_host_contract_missing_control(doc_contract_host_missing_selftest
  docs/native-integration.md "no power-loss guarantee" "## Host process contract")
gbb_host_contract_missing_control(doc_contract_readme_host_missing_selftest
  README.md "Host mode is a headless conformance adapter, not a play surface." "## Host mode (headless)")
gbb_host_contract_missing_control(doc_contract_cartridge_slots_missing_selftest
  docs/cartridge-and-saves.md "Loading a slot also replaces the game's battery save"
  "## Host raw saves and player state slots")
# ---- D-29: the published tables against docs/host-contract.json ------------------------------------------------
add_test(NAME host_contract_docs
  COMMAND "${Python3_EXECUTABLE}" -I "${GBB_HOST_CONTRACT_CHECKER}"
    --docs --rev "${GBB_HOST_CONTRACT_REV}" --repo "${PROJECT_SOURCE_DIR}")
set_tests_properties(host_contract_docs PROPERTIES TIMEOUT 60
  PASS_REGULAR_EXPRESSION "host-contract docs pass exit_rows=[1-9][0-9]* format_rows=[1-9][0-9]*")

# A copy whose 32,789 cell says 32,816 must be rejected as drift; a copy whose save-format table lost its header
# row must be rejected as missing. Each is its own failure code, so neither can mask the other.
gbb_host_contract_variant(GBB_HOST_CONTRACT_DRIFT_GUIDE "native-guide-drift.md"
  docs/native-integration.md "| 32,789 |" "| 32,816 |")
add_test(NAME host_contract_docs_control
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${Python3_EXECUTABLE};-I;${GBB_HOST_CONTRACT_CHECKER};--docs;--rev;${GBB_HOST_CONTRACT_REV};--repo;${PROJECT_SOURCE_DIR};--docs-file;${GBB_HOST_CONTRACT_DRIFT_GUIDE}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=REJECT doc-table-drift"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(host_contract_docs_control PROPERTIES TIMEOUT 60)

gbb_host_contract_variant(GBB_HOST_CONTRACT_HEADERLESS_GUIDE "native-guide-headerless.md"
  docs/native-integration.md "| Type | RAM code | Id | Bytes |" "| Kind | RAM code | Id | Bytes |")
add_test(NAME host_contract_docs_missing_control
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${Python3_EXECUTABLE};-I;${GBB_HOST_CONTRACT_CHECKER};--docs;--rev;${GBB_HOST_CONTRACT_REV};--repo;${PROJECT_SOURCE_DIR};--docs-file;${GBB_HOST_CONTRACT_HEADERLESS_GUIDE}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=REJECT doc-table-missing"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(host_contract_docs_missing_control PROPERTIES TIMEOUT 60)

# ---- D-19: no emulator-interoperability claim in the published text, with a seeded control ---------------------
# The scan reads .planning/research/v0.3/PLAYSTEAD-CONTRACT.md, so the test carries the `planning` label: a
# planning-only change must still run it (tests/scripts/verify-planning-labels.py). It names no build path.
add_test(NAME doc_no_interop_claims
  COMMAND "${Python3_EXECUTABLE}" -I "${PROJECT_SOURCE_DIR}/tests/scripts/verify-no-interop-claims.py"
    --rev "${GBB_HOST_CONTRACT_REV}" --repo "${PROJECT_SOURCE_DIR}")
set_tests_properties(doc_no_interop_claims PROPERTIES TIMEOUT 60 LABELS planning
  PASS_REGULAR_EXPRESSION "no-interop-claims pass files=6 controls=10")

# ---- WR-04: the checkers name HEAD, never a configure-time SHA ---------------------------------------------------
# The registered commands are read back from the generated CTestTestfile.cmake. The control hands the same script a
# file whose save_format_files line carries a 40-digit SHA (the pre-fix wiring) and a file with a test missing; each
# must be rejected for its own reason, so the wiring check cannot pass by reading nothing.
set(GBB_REV_WIRING_TESTS save_format_completeness save_format_freeze host_contract_json host_contract_controls
  host_contract_docs host_contract_docs_control host_contract_docs_missing_control doc_no_interop_claims)
if(NOT WIN32)
  list(APPEND GBB_REV_WIRING_TESTS save_format_files save_format_controls)
endif()
set(GBB_REV_WIRING_SCRIPT "${PROJECT_SOURCE_DIR}/cmake/CheckContractRevWiring.cmake")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${GBB_REV_WIRING_SCRIPT}")
set(GBB_REV_WIRING_DIR "${PROJECT_BINARY_DIR}/contract-rev-wiring")
file(MAKE_DIRECTORY "${GBB_REV_WIRING_DIR}")
file(WRITE "${GBB_REV_WIRING_DIR}/stale-sha-CTestTestfile.cmake"
  "add_test(\"save_format_files\" \"python3\" \"-I\" \"c.py\" \"--check\" \"--rev\" "
  "\"8014d1a824ba92d47b31943270f0fa99b97ce329\" \"--repo\" \"r\")\n")
file(WRITE "${GBB_REV_WIRING_DIR}/missing-CTestTestfile.cmake"
  "add_test(\"other_test\" \"python3\" \"--rev\" \"HEAD\")\n")
# CMake 3.x (the 3.25.3 floor and the hosted runners) writes the test name as a bracket argument, [=[name]=], and the
# local CMake 4 quotes it, so without these files only CI saw the other form; a bare name is covered as well. bare-prefix registers only a longer name
# that starts with save_format_files, which must still count as missing.
file(WRITE "${GBB_REV_WIRING_DIR}/bare-CTestTestfile.cmake"
  "add_test(save_format_files \"python3\" \"-I\" \"c.py\" \"--check\" \"--rev\" \"HEAD\" \"--repo\" \"r\")\n"
  "add_test([=[save_format_controls]=] \"python3\" \"--rev\" \"HEAD\")\n")
file(WRITE "${GBB_REV_WIRING_DIR}/bare-prefix-CTestTestfile.cmake"
  "add_test(save_format_files_extra \"python3\" \"--rev\" \"HEAD\")\n")
add_test(NAME contract_rev_wiring
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_TESTFILE=${CMAKE_CURRENT_BINARY_DIR}/CTestTestfile.cmake"
    "-DGBB_TEST_NAMES=${GBB_REV_WIRING_TESTS}"
    "-DGBB_EXPECT_REV=${GBB_SAVE_FORMATS_REV}"
    -P "${GBB_REV_WIRING_SCRIPT}")
set_tests_properties(contract_rev_wiring PROPERTIES TIMEOUT 60
  PASS_REGULAR_EXPRESSION "contract-rev-wiring pass tests=[0-9]+ rev=")
add_test(NAME contract_rev_wiring_stale_control
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_TESTFILE=${GBB_REV_WIRING_DIR}/stale-sha-CTestTestfile.cmake;-DGBB_TEST_NAMES=save_format_files;-DGBB_EXPECT_REV=HEAD;-P;${GBB_REV_WIRING_SCRIPT}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=reads revision[ \n]+8014d1a824ba92d47b31943270f0fa99b97ce329"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(contract_rev_wiring_stale_control PROPERTIES TIMEOUT 60)
add_test(NAME contract_rev_wiring_missing_control
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_TESTFILE=${GBB_REV_WIRING_DIR}/missing-CTestTestfile.cmake;-DGBB_TEST_NAMES=save_format_files;-DGBB_EXPECT_REV=HEAD;-P;${GBB_REV_WIRING_SCRIPT}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=test save_format_files is not registered"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(contract_rev_wiring_missing_control PROPERTIES TIMEOUT 60)
add_test(NAME contract_rev_wiring_bare_form
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_TESTFILE=${GBB_REV_WIRING_DIR}/bare-CTestTestfile.cmake"
    "-DGBB_TEST_NAMES=save_format_files;save_format_controls"
    -DGBB_EXPECT_REV=HEAD
    -P "${GBB_REV_WIRING_SCRIPT}")
set_tests_properties(contract_rev_wiring_bare_form PROPERTIES TIMEOUT 60
  PASS_REGULAR_EXPRESSION "contract-rev-wiring pass tests=2 rev=HEAD")
add_test(NAME contract_rev_wiring_bare_prefix_control
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_TESTFILE=${GBB_REV_WIRING_DIR}/bare-prefix-CTestTestfile.cmake;-DGBB_TEST_NAMES=save_format_files;-DGBB_EXPECT_REV=HEAD;-P;${GBB_REV_WIRING_SCRIPT}"
    -DGBB_EXPECT_CODE=1
    "-DGBB_EXPECT_REGEX=test save_format_files is not registered"
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(contract_rev_wiring_bare_prefix_control PROPERTIES TIMEOUT 60)
