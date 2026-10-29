/* Phase 18 plan 06: the SDL player's slot keys, status line, input re-anchor and help text, driven through
 * the real SDL event queue (push_key_mod + pump_events) with the player's own main.c embedded.
 *
 * This is deliberately a different file from tests/test_slots.c (18-05): that one proves the SDL-free slot
 * engine in the main inventory; this one proves the wiring in the macOS player suite. The slot files go to
 * SDL_GetPrefPath("GabbaBoy","GabbaBoy"), so CTest runs this with HOME and CFFIXED_USER_HOME pointing at a
 * fresh build-tree directory; every case refuses to run when the pref path is not inside it.
 *
 * Usage: test_player_slots <case> [rom]   case: keys */
#define main gabbaboy_player_embedded_main
#ifndef GBB_PLAYER_MAIN_C
#define GBB_PLAYER_MAIN_C "../../src/player/main.c"
#endif
#include GBB_PLAYER_MAIN_C
#undef main

#include <errno.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>

/* U+2318 PLACE OF INTEREST SIGN as its UTF-8 bytes; the literal is closed after the escape because \x takes
 * every hex digit that follows. */
#define COMMAND_GLYPH "\xe2\x8c\x98"

#define FAIL(...) do { \
    fprintf(stderr, "FAIL %s: ", g_case); \
    fprintf(stderr, __VA_ARGS__); \
    fputc('\n', stderr); \
    return false; \
} while (0)
#define REQUIRE(condition) do { \
    if (!(condition)) FAIL("%s:%d: %s", __FILE__, __LINE__, #condition); \
} while (0)

static const char *g_case = "?";

/* ---- Fixture ------------------------------------------------------------------------------------- */

typedef struct {
    player app;
    char battery_root[64];      /* mkdtemp: the .gbb pref path override */
    char pref[512];             /* SDL_GetPrefPath: where the slot files go */
    char hex[65];
    bool sdl_ready;
    bool session_ready;
} fixture;

static void remove_slot_files(const fixture *fx) {
    if (fx->hex[0] == '\0') return;
    const char *kinds[] = {"slot1", "slot2", "slot3", "slot4", "slot5", "slot6", "slot7", "slot8", "slot9",
                           "undo"};
    for (size_t i = 0; i < sizeof(kinds) / sizeof(kinds[0]); ++i) {
        char path[1024];
        (void)snprintf(path, sizeof(path), "%s%s-dmg-%s.gbbs", fx->pref, fx->hex, kinds[i]);
        (void)unlink(path);
    }
    char path[1024];
    (void)snprintf(path, sizeof(path), "%s%s-dmg-battery-preload.bin", fx->pref, fx->hex);
    (void)unlink(path);
}

static void fx_teardown(fixture *fx) {
    if (fx->session_ready) {
        const player_save_identity identity = fx->app.save_identity;
        fx->app.skip_final_save = true;
        destroy_player(&fx->app);
        if (identity.battery_backed) player_session_remove_battery_file(&identity);
    }
    remove_slot_files(fx);
    player_session_test_set_pref_path(NULL);
    if (fx->battery_root[0] != '\0') (void)rmdir(fx->battery_root);
    if (fx->sdl_ready) SDL_Quit();
}

/* Starts SDL's event queue, isolates the .gbb pref path and loads `rom_path` through the player's own
 * create_machine, which also attaches the slot store. */
static bool fx_setup(fixture *fx, const char *rom_path) {
    memset(fx, 0, sizeof(*fx));
    if (!SDL_Init(SDL_INIT_EVENTS | SDL_INIT_AUDIO)) FAIL("SDL_Init: %s", SDL_GetError());
    fx->sdl_ready = true;
    SDL_SetEventEnabled(SDL_EVENT_AUDIO_DEVICE_ADDED, false);
    SDL_SetEventEnabled(SDL_EVENT_AUDIO_DEVICE_REMOVED, false);
    SDL_SetEventEnabled(SDL_EVENT_WINDOW_FOCUS_LOST, false);
    SDL_SetEventEnabled(SDL_EVENT_WINDOW_FOCUS_GAINED, false);
    SDL_PumpEvents();
    SDL_FlushEvents(SDL_EVENT_FIRST, SDL_EVENT_LAST);

    /* The slot files must land in the isolated HOME, never in the developer's real Application Support. */
    char *pref = SDL_GetPrefPath("GabbaBoy", "GabbaBoy");
    const char *home = getenv("CFFIXED_USER_HOME");
    if (pref == NULL || home == NULL || home[0] == '\0' || strncmp(pref, home, strlen(home)) != 0) {
        const bool null_pref = pref == NULL;
        SDL_free(pref);
        FAIL("slot pref path is not inside CFFIXED_USER_HOME (pref=%s)", null_pref ? "(null)" : "set");
    }
    (void)snprintf(fx->pref, sizeof(fx->pref), "%s", pref);
    SDL_free(pref);

    (void)snprintf(fx->battery_root, sizeof(fx->battery_root), "/tmp/gabbaboy-slots-XXXXXX");
    if (mkdtemp(fx->battery_root) == NULL) FAIL("mkdtemp: %s", strerror(errno));
    player_session_test_set_pref_path(fx->battery_root);

    fx->session_ready = true;
    if (!start_smoke_battery_session(&fx->app, rom_path)) FAIL("could not start the battery session");
    player_input_reset(&fx->app.input, SDL_GetTicksNS());
    static const char digits[] = "0123456789abcdef";
    for (size_t i = 0; i < 32u; ++i) {
        fx->hex[2u * i] = digits[fx->app.save_identity.rom_sha256[i] >> 4];
        fx->hex[2u * i + 1u] = digits[fx->app.save_identity.rom_sha256[i] & 0x0Fu];
    }
    fx->hex[64] = '\0';
    remove_slot_files(fx);
    char *battery = player_session_test_battery_file_path(&fx->app.save_identity);
    if (battery != NULL) {
        (void)unlink(battery);
        free(battery);
    }
    return true;
}

/* ---- Helpers --------------------------------------------------------------------------------------- */

static bool run_frames(player *app, unsigned frames) {
    for (unsigned i = 0; i < frames; ++i)
        if (!advance_to(app, app->input.guest_cursor_half_dots + PLAYER_FRAME_HALF_DOTS, false)) return false;
    return true;
}

static bool key(player *app, Uint32 type, SDL_Scancode scancode, SDL_Keycode keycode, SDL_Keymod mod,
                bool repeat) {
    return push_key_mod(app, type, scancode, keycode, mod, repeat, SDL_GetTicksNS()) && pump_events(app);
}

static bool key_down(player *app, SDL_Scancode scancode, SDL_Keycode keycode, SDL_Keymod mod) {
    return key(app, SDL_EVENT_KEY_DOWN, scancode, keycode, mod, false);
}

static bool press_digit(player *app, unsigned digit, SDL_Keymod mod) {
    return key_down(app, (SDL_Scancode)(SDL_SCANCODE_1 + (digit - 1u)), (SDL_Keycode)('0' + digit), mod);
}

static bool slot_path(const fixture *fx, const char *kind, char out[1024]) {
    const int length = snprintf(out, 1024, "%s%s-dmg-%s.gbbs", fx->pref, fx->hex, kind);
    return length > 0 && length < 1024;
}

static bool file_exists(const char *path) {
    struct stat info;
    return stat(path, &info) == 0;
}

/* Reads a whole file the test wrote; the caller frees. NULL when it does not exist. */
static uint8_t *read_all(const char *path, size_t *out_len) {
    FILE *file = fopen(path, "rb");
    if (file == NULL) return NULL;
    if (fseek(file, 0, SEEK_END) != 0) { (void)fclose(file); return NULL; }
    const long size = ftell(file);
    if (size < 0 || fseek(file, 0, SEEK_SET) != 0) { (void)fclose(file); return NULL; }
    uint8_t *bytes = malloc((size_t)size + 1u);
    if (bytes == NULL || fread(bytes, 1u, (size_t)size, file) != (size_t)size) {
        free(bytes);
        (void)fclose(file);
        return NULL;
    }
    (void)fclose(file);
    *out_len = (size_t)size;
    return bytes;
}

static uint8_t *machine_state(const gbb_instance *machine, size_t *out_len) {
    size_t size = 0u;
    if (gbb_state_size(machine, &size) != GBB_OK) return NULL;
    uint8_t *bytes = malloc(size);
    if (bytes == NULL) return NULL;
    if (gbb_save_state(machine, bytes, size) != GBB_OK) {
        free(bytes);
        return NULL;
    }
    *out_len = size;
    return bytes;
}

static bool machine_now(const gbb_instance *machine, uint64_t *out_now) {
    gbb_input_clock clock;
    memset(&clock, 0, sizeof(clock));
    clock.struct_size = GBB_INPUT_CLOCK_SIZE_V1;
    if (gbb_get_input_clock(machine, &clock) != GBB_OK) return false;
    *out_now = clock.now_half_dots;
    return true;
}

static char *battery_file(const fixture *fx) {
    return player_session_test_battery_file_path(&fx->app.save_identity);
}

/* ---- Case: keys ------------------------------------------------------------------------------------ */

static bool case_keys_body(fixture *fx) {
    player *app = &fx->app;
    char slot3[1024];
    char slot6[1024];
    REQUIRE(slot_path(fx, "slot3", slot3) && slot_path(fx, "slot6", slot6));
    char *gbb = battery_file(fx);
    REQUIRE(gbb != NULL);
    REQUIRE(app->slots_ready && app->selected_slot == 1u);
    REQUIRE(run_frames(app, 3u));

    /* Digit keys select; Shift is allowed, Ctrl, Alt and the Command key veto. */
    REQUIRE(press_digit(app, 3u, SDL_KMOD_NONE));
    REQUIRE(app->selected_slot == 3u);
    REQUIRE(strcmp(app->status, "Slot 3 selected: empty") == 0);
    REQUIRE(press_digit(app, 2u, SDL_KMOD_LSHIFT));
    REQUIRE(app->selected_slot == 2u);
    REQUIRE(press_digit(app, 7u, SDL_KMOD_LCTRL));
    REQUIRE(press_digit(app, 7u, SDL_KMOD_LALT));
    REQUIRE(press_digit(app, 7u, SDL_KMOD_LGUI));
    REQUIRE(app->selected_slot == 2u);
    REQUIRE(press_digit(app, 3u, SDL_KMOD_NONE));
    REQUIRE(app->selected_slot == 3u);

    /* Command-S saves the slot and does not save the battery. */
    REQUIRE(!file_exists(gbb));
    uint64_t saved_at = 0u;
    REQUIRE(machine_now(app->machine, &saved_at));
    REQUIRE(key_down(app, SDL_SCANCODE_S, SDLK_S, SDL_KMOD_LGUI));
    REQUIRE(strcmp(app->status, "Saved slot 3") == 0);
    REQUIRE(file_exists(slot3));
    REQUIRE(!file_exists(gbb));
    size_t slot_len = 0u;
    uint8_t *slot_bytes = read_all(slot3, &slot_len);
    size_t live_len = 0u;
    uint8_t *live = machine_state(app->machine, &live_len);
    REQUIRE(slot_bytes != NULL && live != NULL && slot_len == live_len && memcmp(slot_bytes, live, live_len) == 0);
    free(live);

    /* Command-L restores exactly the slot. */
    REQUIRE(run_frames(app, 5u));
    uint64_t later = 0u;
    REQUIRE(machine_now(app->machine, &later) && later > saved_at);
    REQUIRE(key_down(app, SDL_SCANCODE_L, SDLK_L, SDL_KMOD_LGUI));
    REQUIRE(strcmp(app->status, "Loaded slot 3 (" COMMAND_GLYPH "Z undoes)") == 0);
    live = machine_state(app->machine, &live_len);
    REQUIRE(live != NULL && live_len == slot_len && memcmp(slot_bytes, live, live_len) == 0);
    free(live);
    free(slot_bytes);
    uint64_t restored = 0u;
    REQUIRE(machine_now(app->machine, &restored) && restored == saved_at);

    /* Command-Z swaps back; the later Z key-up is harmless. */
    REQUIRE(key_down(app, SDL_SCANCODE_Z, SDLK_Z, SDL_KMOD_LGUI));
    REQUIRE(strcmp(app->status, "Undid the last load (" COMMAND_GLYPH "Z switches back)") == 0);
    uint64_t undone = 0u;
    REQUIRE(machine_now(app->machine, &undone) && undone == later);
    REQUIRE(key(app, SDL_EVENT_KEY_UP, SDL_SCANCODE_Z, SDLK_Z, SDL_KMOD_NONE, false));
    REQUIRE(strstr(app->status, "Input paused") == NULL && !app->user_paused);
    REQUIRE(app->input.keyboard_buttons == 0u);

    /* Command-R does not reset: the guest clock survives and no battery save happened. */
    REQUIRE(key_down(app, SDL_SCANCODE_R, SDLK_R, SDL_KMOD_LGUI));
    uint64_t after_reset_key = 0u;
    REQUIRE(machine_now(app->machine, &after_reset_key) && after_reset_key == undone);
    REQUIRE(app->pending_transition == PLAYER_TRANSITION_NONE);
    REQUIRE(strstr(app->status, "reset") == NULL);
    REQUIRE(!file_exists(gbb));

    /* Repeats, a pending transition and a pending dialog change nothing. */
    REQUIRE(press_digit(app, 6u, SDL_KMOD_NONE));
    REQUIRE(app->selected_slot == 6u);
    char status_before[sizeof(app->status)];
    (void)snprintf(status_before, sizeof(status_before), "%s", app->status);
    REQUIRE(key(app, SDL_EVENT_KEY_DOWN, SDL_SCANCODE_S, SDLK_S, SDL_KMOD_LGUI, true));
    REQUIRE(!file_exists(slot6) && strcmp(app->status, status_before) == 0);
    app->pending_transition = PLAYER_TRANSITION_RESET;
    REQUIRE(key_down(app, SDL_SCANCODE_S, SDLK_S, SDL_KMOD_LGUI));
    REQUIRE(press_digit(app, 5u, SDL_KMOD_NONE));
    app->pending_transition = PLAYER_TRANSITION_NONE;
    REQUIRE(!file_exists(slot6) && app->selected_slot == 6u && strcmp(app->status, status_before) == 0);
    app->dialog_pending = true;
    REQUIRE(key_down(app, SDL_SCANCODE_S, SDLK_S, SDL_KMOD_LGUI));
    REQUIRE(press_digit(app, 5u, SDL_KMOD_NONE));
    app->dialog_pending = false;
    REQUIRE(!file_exists(slot6) && app->selected_slot == 6u && strcmp(app->status, status_before) == 0);

    /* Slot keys work while paused, and a load keeps the pause. */
    REQUIRE(press_digit(app, 3u, SDL_KMOD_NONE));
    REQUIRE(key_down(app, SDL_SCANCODE_SPACE, SDLK_SPACE, SDL_KMOD_NONE));
    REQUIRE(app->user_paused && app->input.paused);
    REQUIRE(key_down(app, SDL_SCANCODE_L, SDLK_L, SDL_KMOD_LGUI));
    REQUIRE(strcmp(app->status, "Loaded slot 3 (" COMMAND_GLYPH "Z undoes)") == 0);
    REQUIRE(app->user_paused && app->input.paused);
    REQUIRE(key_down(app, SDL_SCANCODE_SPACE, SDLK_SPACE, SDL_KMOD_NONE));
    REQUIRE(!app->user_paused && !app->input.paused);

    /* A bare S still saves the battery, and a bare R still resets the game. */
    REQUIRE(run_frames(app, 2u));
    REQUIRE(!file_exists(gbb));
    REQUIRE(key_down(app, SDL_SCANCODE_S, SDLK_S, SDL_KMOD_NONE));
    REQUIRE(file_exists(gbb));
    REQUIRE(key_down(app, SDL_SCANCODE_R, SDLK_R, SDL_KMOD_NONE));
    REQUIRE(strncmp(app->status, "Current ROM reset", 17u) == 0);
    uint64_t after_reset = 0u;
    REQUIRE(machine_now(app->machine, &after_reset) && after_reset == 0u);
    free(gbb);
    return true;
}

static bool case_keys(const char *rom_path) {
    fixture fx;
    const bool ok = fx_setup(&fx, rom_path) && case_keys_body(&fx);
    fx_teardown(&fx);
    return ok;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fputs("usage: test_player_slots <case> [rom]\n", stderr);
        return 2;
    }
    g_case = argv[1];
    const char *rom = argc >= 3 ? argv[2] : NULL;
    bool ok = false;
    if (strcmp(g_case, "keys") == 0 && rom != NULL) ok = case_keys(rom);
    else {
        fprintf(stderr, "unknown case or missing rom: %s\n", g_case);
        return 2;
    }
    if (ok) printf("PASS %s\n", g_case);
    return ok ? 0 : 1;
}
