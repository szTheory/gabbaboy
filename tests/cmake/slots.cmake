# Phase 18 (D-21..D-26): the SDL-free slot engine, src/player/slots.c.
#
# Every name registered here must also be listed in tests/expected-tests.txt (append-only). New tests keep the
# base 60 s timeout (D-27). test_slots uses the dir-fd writer, mkdtemp, symlink and utimensat, so the executable
# and every variant built from it are created only inside if(NOT WIN32) (checker B-3), and each name it
# registers is removed from the Windows expectation in BOTH cmake/ExpectedTests.cmake and
# .github/scripts/verify-test-inventory.sh. test_slots_pure is portable and runs on Windows.
# Generated ROMs, states and pref directories live under ${PROJECT_BINARY_DIR}/slots-work; nothing binary is
# committed, because state bytes embed the release token.

if(NOT WIN32)
  file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/slots-work")
  add_executable(test_slots "${PROJECT_SOURCE_DIR}/tests/test_slots.c")
  # The test twin of the host library supplies the one-shot writer fault seams; the core arrives once
  # through gabbaboy_accept, which the test also uses for SHA-256 file digests.
  target_link_libraries(test_slots PRIVATE gabbaboy_player_slots gabbaboy_host_testing gabbaboy_accept)
  target_compile_definitions(test_slots PRIVATE GBB_HOST_TESTING)
  target_compile_features(test_slots PRIVATE c_std_17)
  set_target_properties(test_slots PROPERTIES C_EXTENSIONS OFF)

  foreach(case roundtrip empty wrong_rom_untouched
      refusal_dmg_in_cgb refusal_version_token refusal_text_file refusal_flipped_byte refusal_truncated
      refusal_oversize refusal_symlink undo_write_failure backup_write_failure undo_swap no_undo
      battery_guard unsafe_queued_input save_failure_keeps_old)
    add_test(NAME slot_${case} COMMAND test_slots ${case}
      WORKING_DIRECTORY "${PROJECT_BINARY_DIR}/slots-work")
    set_tests_properties(slot_${case} PROPERTIES PASS_REGULAR_EXPRESSION "PASS ${case}")
  endforeach()
endif()
