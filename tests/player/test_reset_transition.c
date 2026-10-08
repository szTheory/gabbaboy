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

static bool verify_pause_transition(void) {
    player app = {0};
    gbb_instance *reference = NULL;
    gbb_audio_frame app_before[804] = {{0}};
    gbb_audio_frame reference_before[804] = {{0}};
    gbb_audio_frame app_after[804] = {{0}};
    gbb_audio_frame reference_after[804] = {{0}};
    size_t app_before_count = 0u;
    size_t reference_before_count = 0u;
    size_t app_after_count = 0u;
    size_t reference_after_count = 0u;
    bool passed = false;

    app.save_lock_fd = -1;
    app.running = true;
    app.window_focused = true;
    app.skip_final_save = true;
    app.machine = create_authored_audio_guest(GABBABOY_PLAYER_DEMO_ROM);
    app.audio = player_audio_test_create(true);
    reference = create_authored_audio_guest(GABBABOY_PLAYER_DEMO_ROM);
    if (app.machine == NULL || app.audio == NULL || reference == NULL) {
        fputs("Could not create pause-transition audio guests\n", stderr);
        goto cleanup;
    }
    player_input_reset(&app.input, SDL_GetTicksNS());

    const gbb_run_result app_before_run = gbb_run_audio(
        app.machine, 140448u, app_before, 804u, &app_before_count);
    const gbb_run_result reference_before_run = gbb_run_audio(
        reference, 140448u, reference_before, 804u, &reference_before_count);
    if (app_before_run.reason != GBB_STOP_BUDGET ||
        reference_before_run.reason != GBB_STOP_BUDGET ||
        app_before_run.consumed_half_dots != 140448u ||
        reference_before_run.consumed_half_dots != 140448u ||
        app_before_count == 0u || app_before_count != reference_before_count ||
        memcmp(app_before, reference_before,
               app_before_count * sizeof(app_before[0])) != 0 ||
        !player_audio_submit(app.audio, app_before,
                             (unsigned)app_before_count)) {
        fputs("Could not establish matching active pulse playback before pause\n",
              stderr);
        goto cleanup;
    }
    player_input_reconcile(&app.input, app_before_run.consumed_half_dots);
    const uint64_t paused_guest_cursor = app.input.guest_cursor_half_dots;

    if (!push_key(&app, SDL_EVENT_KEY_DOWN, SDL_SCANCODE_SPACE,
                  SDL_GetTicksNS()) || !pump_events(&app) ||
        !app.user_paused || !app.input.paused ||
        player_audio_test_queued(app.audio) != 0u ||
        player_audio_flushed_bytes(app.audio) !=
            app_before_count * sizeof(app_before[0]) ||
        app.input.guest_cursor_half_dots != paused_guest_cursor) {
        fputs("Space pause did not preserve guest cursor and clear host PCM\n",
              stderr);
        goto cleanup;
    }
    if (!push_key(&app, SDL_EVENT_KEY_DOWN, SDL_SCANCODE_SPACE,
                  SDL_GetTicksNS()) || !pump_events(&app) ||
        app.user_paused || app.input.paused ||
        app.input.guest_cursor_half_dots != paused_guest_cursor) {
        fputs("Space resume did not restore the active input session\n", stderr);
        goto cleanup;
    }

    const gbb_run_result app_after_run = gbb_run_audio(
        app.machine, 140448u, app_after, 804u, &app_after_count);
    const gbb_run_result reference_after_run = gbb_run_audio(
        reference, 140448u, reference_after, 804u, &reference_after_count);
    if (app_after_run.reason != GBB_STOP_BUDGET ||
        reference_after_run.reason != GBB_STOP_BUDGET ||
        app_after_run.consumed_half_dots != reference_after_run.consumed_half_dots ||
        app_after_count != reference_after_count || app_after_count == 0u ||
        memcmp(app_after, reference_after,
               app_after_count * sizeof(app_after[0])) != 0) {
        fputs("Space pause/resume changed the guest APU continuation\n", stderr);
        goto cleanup;
    }
    passed = true;

cleanup:
    destroy_player(&app);
    if (reference != NULL) gbb_destroy(reference);
    return passed;
}

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

    CHECK(verify_pause_transition(),
          "normal Space pause/resume did not preserve APU history and clear PCM");

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
    if (passed) puts("player transitions passed: Space preserved APU history and cleared PCM; R saved before guest reset; cancel preserved queues; retry reset both");
    return passed ? 0 : 1;
}
