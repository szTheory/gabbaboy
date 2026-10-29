# Phase 18 (D-21..D-26): the SDL-free slot engine, src/player/slots.c.
#
# Every name registered here must also be listed in tests/expected-tests.txt (append-only). New tests keep the
# base 60 s timeout (D-27). test_slots uses the dir-fd writer, mkdtemp, symlink and utimensat, so the executable
# and every variant built from it are created only inside if(NOT WIN32) (checker B-3), and each name it
# registers is removed from the Windows expectation in BOTH cmake/ExpectedTests.cmake and
# .github/scripts/verify-test-inventory.sh. test_slots_pure is portable and runs on Windows.
# Generated ROMs, states and pref directories live under ${PROJECT_BINARY_DIR}/slots-work; nothing binary is
# committed, because state bytes embed the release token.

# gbb_slots_mutant(name anchor replacement case regex [PURE]): src/player/slots.c with one edit, built as its
# own library and linked into a copy of test_slots (or of test_slots_pure with PURE). The anchor must occur
# exactly once. The variant must exit 1 with its own `FAIL <case>` line, so a crash cannot satisfy it. The
# executable is named `variant`, not `mutant`, because verify-core-linkage.py requires every target named
# *mutant* that links the acceptance helpers to carry a mutant core, and only the slot engine is mutated here.
function(gbb_slots_mutant name anchor replacement case regex)
  # The optional sixth argument PURE builds the variant from test_slots_pure.c instead of test_slots.c.
  set(pure FALSE)
  if("${ARGV5}" STREQUAL "PURE")
    set(pure TRUE)
  endif()
  file(READ "${PROJECT_SOURCE_DIR}/src/player/slots.c" text)
  string(FIND "${text}" "${anchor}" first)
  string(FIND "${text}" "${anchor}" last REVERSE)
  if(first EQUAL -1 OR NOT first EQUAL last)
    message(FATAL_ERROR
      "Slots mutant ${name}: anchor must occur exactly once in slots.c (first=${first}, last=${last})")
  endif()
  string(REPLACE "${anchor}" "${replacement}" text "${text}")
  set(directory "${PROJECT_BINARY_DIR}/slots-mutants/${name}")
  file(WRITE "${directory}/slots.c" "${text}")

  add_library(gabbaboy_player_slots_variant_${name} STATIC "${directory}/slots.c")
  target_include_directories(gabbaboy_player_slots_variant_${name} PUBLIC
    "${PROJECT_SOURCE_DIR}/src/player" "${PROJECT_SOURCE_DIR}/src/host" "${PROJECT_SOURCE_DIR}/include")
  target_compile_features(gabbaboy_player_slots_variant_${name} PUBLIC c_std_17)
  set_target_properties(gabbaboy_player_slots_variant_${name} PROPERTIES C_EXTENSIONS OFF)

  if(pure)
    # Portable: the pure tables run on Windows too, so this variant has no POSIX dependency.
    add_executable(test_slots_pure_variant_${name} "${PROJECT_SOURCE_DIR}/tests/test_slots_pure.c")
    target_link_libraries(test_slots_pure_variant_${name} PRIVATE
      gabbaboy_player_slots_variant_${name} gabbaboy_host GabbaBoy::core)
    set(variant_target test_slots_pure_variant_${name})
    set(variant_workdir "${PROJECT_BINARY_DIR}")
  else()
    add_executable(test_slots_variant_${name} "${PROJECT_SOURCE_DIR}/tests/test_slots.c")
    target_link_libraries(test_slots_variant_${name} PRIVATE
      gabbaboy_player_slots_variant_${name} gabbaboy_host_testing gabbaboy_accept)
    target_compile_definitions(test_slots_variant_${name} PRIVATE GBB_HOST_TESTING)
    set(variant_target test_slots_variant_${name})
    set(variant_workdir "${PROJECT_BINARY_DIR}/slots-work")
  endif()
  target_compile_features(${variant_target} PRIVATE c_std_17)
  set_target_properties(${variant_target} PROPERTIES C_EXTENSIONS OFF)

  add_test(NAME slot_mutant_${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=$<TARGET_FILE:${variant_target}>;${case}"
      "-DGBB_WORKDIR=${variant_workdir}"
      -DGBB_EXPECT_CODE=1 "-DGBB_EXPECT_REGEX=${regex}"
      -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
endfunction()

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
      battery_guard unsafe_queued_input save_failure_keeps_old reanchor_later reanchor_earlier
      select_message)
    add_test(NAME slot_${case} COMMAND test_slots ${case}
      WORKING_DIRECTORY "${PROJECT_BINARY_DIR}/slots-work")
    set_tests_properties(slot_${case} PROPERTIES PASS_REGULAR_EXPRESSION "PASS ${case}")
  endforeach()

  # D-26 item 11: the undo snapshot is written before the slot is validated, so a refused slot leaves an undo file.
  gbb_slots_mutant(undo_before_load
    [=[/* Step 1a: validate in a scratch instance]=]
    [=[{
        uint8_t *early = malloc(state_size);
        if (early != NULL && gbb_save_state(instance, early, state_size) == GBB_OK)
            (void)host_save_io_replace(store->dirfd, undo_name, early, state_size);
        free(early);
    }
    /* Step 1a: validate in a scratch instance]=]
    refusal_flipped_byte "FAIL refusal_flipped_byte")
  # Checker W-5: the battery preload is written before the slot is validated, so a refused first load
  # still creates a preload file.
  gbb_slots_mutant(preload_before_validate
    [=[/* Step 1a: validate in a scratch instance]=]
    [=[{
        size_t early_size = 0u;
        if (gbb_battery_size(instance, &early_size) == GBB_OK && early_size > 0u) {
            uint8_t *early = malloc(early_size);
            if (early != NULL && gbb_copy_battery(instance, early, early_size) == GBB_OK)
                (void)host_save_io_replace(store->dirfd, preload_name, early, early_size);
            free(early);
        }
    }
    /* Step 1a: validate in a scratch instance]=]
    refusal_flipped_byte "FAIL refusal_flipped_byte")
  # D-23 step 3 removed: the in-game battery is never backed up.
  gbb_slots_mutant(no_guard
    [=[const bool needs_preload = battery_differs_from_guard(store, battery, battery_size);]=]
    [=[const bool needs_preload = false;]=]
    battery_guard "FAIL battery_guard")
  # D-23 step 5: a failed undo write no longer rolls the machine back.
  gbb_slots_mutant(no_rollback
    [=[(void)gbb_load_state(instance, snapshot, state_size);]=]
    [=[(void)0;]=]
    undo_write_failure "FAIL undo_write_failure")

  # D-24: the plan ignores the restored queue, so the press is queued at now, which precedes the last
  # restored event and is refused.
  gbb_slots_mutant(plan_ignores_last
    [=[plan.release_at = clock->last_queued_half_dots > clock->now_half_dots ? clock->last_queued_half_dots : clock->now_half_dots;]=]
    [=[plan.release_at = clock->now_half_dots;]=]
    reanchor_earlier "FAIL reanchor_earlier")
endif()

# ---- Portable: the message table, key decoder and re-anchor plan (also built and run on Windows) -------------
add_executable(test_slots_pure "${PROJECT_SOURCE_DIR}/tests/test_slots_pure.c")
target_link_libraries(test_slots_pure PRIVATE gabbaboy_player_slots gabbaboy_host GabbaBoy::core)
target_compile_features(test_slots_pure PRIVATE c_std_17)
set_target_properties(test_slots_pure PROPERTIES C_EXTENSIONS OFF)
foreach(case message_table key_decoder reanchor_plan)
  add_test(NAME slot_${case} COMMAND test_slots_pure ${case})
  set_tests_properties(slot_${case} PROPERTIES PASS_REGULAR_EXPRESSION "PASS ${case}")
endforeach()

# D-26 item 10: GBB_STATE_UNSUPPORTED_VERSION is mapped to the damaged text; the table must notice.
gbb_slots_mutant(message_map
  [=[return "is from another GabbaBoy version";]=]
  [=[return "is damaged";]=]
  message_table "FAIL message_table" PURE)
