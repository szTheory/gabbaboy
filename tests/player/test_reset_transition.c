#define main gabbaboy_player_embedded_main
#include "../../src/player/main.c"
#undef main

#include <errno.h>
#include <stdlib.h>
#include <unistd.h>

#define CHECK(condition, message) do { \
    if (!(condition)) { \
        fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, message); \
        goto cleanup; \
    } \
} while (0)

int main(void) {
    char root_template[] = "/tmp/gabbaboy-reset-transition-XXXXXX";
    char rom_path[256] = {0};
    char *root = NULL;
    char *save_path = NULL;
    char *verification_rom_path = NULL;
    gbb_instance *verification_machine = NULL;
    player_save_identity identity = {0};
    player_save_identity verification_identity = {0};
    player session = {0};
    bool sdl_initialized = false;
    bool session_started = false;
    bool passed = false;

    if (!SDL_Init(SDL_INIT_EVENTS | SDL_INIT_AUDIO)) {
        fprintf(stderr, "SDL_Init: %s\n", SDL_GetError());
        goto cleanup;
    }
    sdl_initialized = true;
    SDL_SetEventEnabled(SDL_EVENT_AUDIO_DEVICE_ADDED, false);
    SDL_SetEventEnabled(SDL_EVENT_AUDIO_DEVICE_REMOVED, false);
    SDL_SetEventEnabled(SDL_EVENT_WINDOW_FOCUS_LOST, false);
    SDL_SetEventEnabled(SDL_EVENT_WINDOW_FOCUS_GAINED, false);
    SDL_PumpEvents();
    SDL_FlushEvents(SDL_EVENT_FIRST, SDL_EVENT_LAST);

    root = mkdtemp(root_template);
    if (root == NULL) {
        perror("mkdtemp");
        goto cleanup;
    }
    player_session_test_set_pref_path(root);

    if (!write_smoke_rom(rom_path, sizeof(rom_path), &identity)) {
        fputs("Could not create the bounded reset-transition battery ROM\n",
              stderr);
        goto cleanup;
    }
    player_session_remove_battery_file(&identity);

    session_started = true;
    if (!start_smoke_battery_session(&session, rom_path)) goto cleanup;
    session.audio = player_audio_test_create(true);
    if (session.audio == NULL) {
        fputs("Could not create the deterministic test audio ring\n", stderr);
        goto cleanup;
    }
    player_input_reset(&session.input, SDL_GetTicksNS());

    const gbb_run_result initial_run = gbb_run(session.machine, 512u, NULL, 0u);
    uint64_t dirty_generation = 0u;
    CHECK(initial_run.reason == GBB_STOP_HALTED_IDLE,
          "battery guest did not reach its bounded save point");
    CHECK(gbb_battery_generation(session.machine, &dirty_generation) == GBB_OK &&
          dirty_generation > session.save_identity.saved_generation,
          "battery guest did not create unsaved progress");
    uint8_t battery[8192];
    CHECK(gbb_copy_battery(session.machine, battery, sizeof(battery)) == GBB_OK &&
          battery[0] == 0x5Au,
          "battery guest did not write the expected marker");
    player_input_reconcile(&session.input, initial_run.consumed_half_dots);

    CHECK(push_key(&session, SDL_EVENT_KEY_DOWN, SDL_SCANCODE_Z,
                   SDL_GetTicksNS()) && pump_events(&session),
          "app event loop did not accept queued guest input");
    CHECK(session.input.pending_count == 1u &&
          session.input.keyboard_buttons != 0u &&
          session.input.held_buttons != 0u,
          "app event loop did not retain the queued input contribution");

    const gbb_audio_frame queued_audio[] = {
        {101, -101}, {202, -202}, {303, -303}, {404, -404}
    };
    CHECK(player_audio_submit(session.audio, queued_audio,
                              (unsigned)(sizeof(queued_audio) /
                                         sizeof(queued_audio[0]))) &&
          player_audio_test_queued(session.audio) == 4u,
          "test audio ring did not retain the queued PCM frames");

    save_path = player_session_test_battery_file_path(&session.save_identity);
    CHECK(save_path != NULL && access(save_path, F_OK) != 0 && errno == ENOENT,
          "test battery save existed before the reset transition");

    player_session_test_set_fault(PLAYER_SESSION_TEST_FAULT_RENAME);
    CHECK(push_key(&session, SDL_EVENT_KEY_DOWN, SDL_SCANCODE_R,
                   SDL_GetTicksNS()) && pump_events(&session),
          "app event loop did not deliver the normal R-reset action");
    CHECK(session.pending_transition == PLAYER_TRANSITION_RESET &&
          session.save_status_active && session.machine != NULL &&
          session.save_identity.saved_generation == 0u &&
          player_audio_test_queued(session.audio) == 4u &&
          session.input.pending_count == 1u,
          "failed save did not preserve the active session and queued state");
    CHECK(access(save_path, F_OK) != 0 && errno == ENOENT,
          "failed save unexpectedly published a battery file");

    CHECK(push_key(&session, SDL_EVENT_KEY_DOWN, SDL_SCANCODE_ESCAPE,
                   SDL_GetTicksNS()) && pump_events(&session),
          "app event loop did not deliver cancel for the failed save");
    CHECK(session.pending_transition == PLAYER_TRANSITION_NONE &&
          !session.user_paused && !session.input.paused &&
          session.save_identity.saved_generation == 0u &&
          player_audio_test_queued(session.audio) == 4u &&
          session.input.pending_count == 1u &&
          session.input.keyboard_buttons != 0u,
          "cancel did not preserve the unsaved active session and queued state");
    CHECK(access(save_path, F_OK) != 0 && errno == ENOENT,
          "cancel unexpectedly published a battery file");

    CHECK(push_key(&session, SDL_EVENT_KEY_DOWN, SDL_SCANCODE_R,
                   SDL_GetTicksNS()) && pump_events(&session),
          "app event loop did not retry the R-reset transition");
    CHECK(session.pending_transition == PLAYER_TRANSITION_NONE &&
          !session.save_status_active && !session.user_paused &&
          session.save_identity.saved_generation == dirty_generation,
          "successful retry did not save progress before resetting the session");
    CHECK(session.input.pending_count == 0u &&
          session.input.keyboard_buttons == 0u &&
          session.input.held_buttons == 0u &&
          session.input.release_pending_buttons == 0u &&
          session.input.guest_cursor_half_dots == 0u &&
          !session.input.paused,
          "successful reset did not clear the input session");
    CHECK(player_audio_test_queued(session.audio) == 0u &&
          player_audio_flushed_bytes(session.audio) ==
              sizeof(queued_audio),
          "successful reset did not clear and account for queued PCM");
    CHECK(access(save_path, F_OK) == 0,
          "successful retry did not publish the battery save");

    CHECK(run_smoke_battery_guest(&session, true),
          "reset did not restart the guest from the persisted battery branch");

    CHECK(gbb_create(GBB_PROFILE_DMG_CPU_B, &verification_machine) == GBB_OK &&
          verification_machine != NULL,
          "could not create an independent battery verification guest");
    char error[192];
    CHECK(player_session_replace_rom(verification_machine,
                                     &verification_rom_path, rom_path,
                                     &verification_identity,
                                     error, sizeof(error)),
          "could not load the reset-transition verification ROM");
    CHECK(player_session_load_battery(verification_machine,
                                      &verification_identity,
                                      error, sizeof(error)),
          "could not load the battery bytes saved before reset");
    CHECK(gbb_copy_battery(verification_machine, battery, sizeof(battery)) ==
              GBB_OK && battery[0] == 0x5Au,
          "reopened guest did not recover the battery bytes saved before reset");

    passed = true;

cleanup:
    player_session_test_set_fault(PLAYER_SESSION_TEST_FAULT_NONE);
    if (verification_machine != NULL) gbb_destroy(verification_machine);
    free(verification_rom_path);
    if (session_started) {
        session.skip_final_save = true;
        destroy_player(&session);
    }
    if (identity.battery_backed) player_session_remove_battery_file(&identity);
    player_session_test_set_pref_path(NULL);
    free(save_path);
    if (rom_path[0] != '\0') (void)unlink(rom_path);
    if (root != NULL && rmdir(root) != 0) {
        perror("rmdir reset-transition test root");
        passed = false;
    }
    if (sdl_initialized) SDL_Quit();
    if (passed) puts("player reset transition passed: R saved before guest reset; cancel preserved queued input and PCM; retry reset both");
    return passed ? 0 : 1;
}
