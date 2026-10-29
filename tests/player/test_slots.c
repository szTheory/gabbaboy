/* Phase 18 plan 06: the SDL player's slot keys, status line, input re-anchor and help text, driven through
 * the real SDL event queue (push_key_mod + pump_events) with the player's own main.c embedded.
 *
 * This is deliberately a different file from tests/test_slots.c (18-05): that one proves the SDL-free slot
 * engine in the main inventory; this one proves the wiring in the macOS player suite. The slot files go to
 * SDL_GetPrefPath("GabbaBoy","GabbaBoy"), so CTest runs this with HOME and CFFIXED_USER_HOME pointing at a
 * fresh build-tree directory; every case refuses to run when the pref path is not inside it.
 *
 * Usage: test_player_slots <case> [rom]   case: keys | reanchor | status_line | help_text */
#define main gabbaboy_player_embedded_main
#ifndef GBB_PLAYER_MAIN_C
#define GBB_PLAYER_MAIN_C "../../src/player/main.c"
#endif
#include GBB_PLAYER_MAIN_C
#undef main

#include <errno.h>
#include <fcntl.h>
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

/* The state the player must hold right after loading `slot`: the slot itself plus the eight button releases the
 * player queues at max(now, last queued). Built in a scratch instance from the store's own ROM copy, so it is
 * independent of the player's input code. */
static uint8_t *expected_after_load(const fixture *fx, const uint8_t *slot, size_t slot_len, size_t *out_len) {
    gbb_info info;
    memset(&info, 0, sizeof(info));
    info.struct_size = GBB_INFO_SIZE_V1;
    gbb_instance *scratch = NULL;
    if (gbb_get_info(fx->app.machine, &info) != GBB_OK || gbb_create(info.profile, &scratch) != GBB_OK)
        return NULL;
    uint8_t *bytes = NULL;
    gbb_input_clock clock;
    memset(&clock, 0, sizeof(clock));
    clock.struct_size = GBB_INPUT_CLOCK_SIZE_V1;
    if (gbb_load_rom(scratch, fx->app.slots.rom, fx->app.slots.rom_size) == GBB_OK &&
        gbb_load_state(scratch, slot, slot_len) == GBB_OK && gbb_get_input_clock(scratch, &clock) == GBB_OK) {
        const player_slot_reanchor plan = player_slot_plan_reanchor(&clock);
        gbb_input_event releases[PLAYER_INPUT_BUTTON_COUNT];
        for (unsigned button = 0; button < PLAYER_INPUT_BUTTON_COUNT; ++button)
            releases[button] = (gbb_input_event){plan.release_at, GBB_INPUT_BUTTON_RELEASE, (uint8_t)button};
        if (gbb_queue_events(scratch, releases, PLAYER_INPUT_BUTTON_COUNT) == GBB_OK)
            bytes = machine_state(scratch, out_len);
    }
    gbb_destroy(scratch);
    return bytes;
}

/* Redirects stderr into a file so a case can read the lines the player printed. */
static int begin_capture(const char *path) {
    (void)fflush(stderr);
    const int saved = dup(2);
    const int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0600);
    if (saved < 0 || fd < 0 || dup2(fd, 2) < 0) {
        if (fd >= 0) (void)close(fd);
        if (saved >= 0) (void)close(saved);
        return -1;
    }
    (void)close(fd);
    return saved;
}

static void end_capture(int saved) {
    (void)fflush(stderr);
    (void)dup2(saved, 2);
    (void)close(saved);
}

static bool file_contains(const char *path, const char *needle) {
    size_t length = 0u;
    uint8_t *bytes = read_all(path, &length);
    if (bytes == NULL) return false;
    bytes[length] = '\0';
    const bool found = strstr((const char *)bytes, needle) != NULL;
    free(bytes);
    return found;
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

    /* Command-L restores exactly the slot, plus the eight releases the player queues after a load. */
    REQUIRE(run_frames(app, 5u));
    uint64_t later = 0u;
    REQUIRE(machine_now(app->machine, &later) && later > saved_at);
    REQUIRE(key_down(app, SDL_SCANCODE_L, SDLK_L, SDL_KMOD_LGUI));
    REQUIRE(strcmp(app->status, "Loaded slot 3 (" COMMAND_GLYPH "Z undoes)") == 0);
    live = machine_state(app->machine, &live_len);
    size_t expected_len = 0u;
    uint8_t *expected = expected_after_load(fx, slot_bytes, slot_len, &expected_len);
    REQUIRE(live != NULL && expected != NULL && live_len == expected_len && memcmp(expected, live, live_len) == 0);
    free(expected);
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

/* ---- Case: reanchor ------------------------------------------------------------------------------- */

static void fix_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

/* The joypad mirror: an MBC1+RAM+battery ($03/$02) cartridge whose program enables RAM and then loops
 *   ld a,$10 / ldh ($00),a / ldh a,($00) / ld ($A000),a / jr loop
 * so SRAM byte 0 mirrors the action-button nibble of P1 (bit 0 = A, 0 = pressed). gbb_copy_battery then shows
 * what the guest saw, which makes "the key reaches the guest" an observation, not an inference. Same program as
 * the 18-05 engine test, written out here because the two files are separate suites. */
static bool write_joypad_rom(char *out_path, size_t capacity) {
    static const uint8_t program[] = {
        0x3E, 0x0A,             /* ld a,$0A      */
        0xEA, 0x00, 0x00,       /* ld ($0000),a  : enable cartridge RAM */
        0x3E, 0x10,             /* loop: ld a,$10  : select the action buttons (bit 5 low) */
        0xE0, 0x00,             /* ldh ($00),a   */
        0xF0, 0x00,             /* ldh a,($00)   */
        0xEA, 0x00, 0xA0,       /* ld ($A000),a  */
        0x18, 0xF5,             /* jr loop       */
    };
    uint8_t rom[32768];
    memset(rom, 0, sizeof(rom));
    rom[0x100u] = 0xC3u;        /* jp $0150 */
    rom[0x101u] = 0x50u;
    rom[0x102u] = 0x01u;
    rom[0x134u] = 'J';
    rom[0x147u] = 0x03u;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x02u;
    memcpy(rom + 0x150u, program, sizeof(program));
    fix_checksum(rom);
    char path[] = "/tmp/gabbaboy-slots-joypad-XXXXXX";
    const int fd = mkstemp(path);
    if (fd < 0 || strlen(path) + 1u > capacity) return false;
    const ssize_t written = write(fd, rom, sizeof(rom));
    if (close(fd) != 0 || written != (ssize_t)sizeof(rom)) {
        (void)unlink(path);
        return false;
    }
    memcpy(out_path, path, strlen(path) + 1u);
    return true;
}

/* 1 when the guest sees A released (bit 0 of the mirrored P1 nibble set), 0 when pressed, -1 on error. */
static int guest_sees_a_released(const player *app) {
    uint8_t battery[8192];
    if (gbb_copy_battery(app->machine, battery, sizeof(battery)) != GBB_OK) return -1;
    return (battery[0] & 0x01u) != 0u ? 1 : 0;
}

/* The SDL timestamp of a key pressed 8 half-dots after the player's cursor, the way the smoke mode times its
 * keys: it maps back to cursor + 8, so a correct anchor schedules it inside the next frame. */
static Uint64 key_timestamp(const player *app) {
    uint64_t elapsed_ns = 0u;
    if (app->input.guest_cursor_half_dots < app->input.guest_anchor_half_dots ||
        !player_input_half_dots_to_nanoseconds(
            app->input.guest_cursor_half_dots - app->input.guest_anchor_half_dots + 8u, &elapsed_ns))
        return 0u;
    return app->input.host_anchor_ns + elapsed_ns;
}

static bool z_event(player *app, Uint32 type) {
    return push_key_mod(app, type, SDL_SCANCODE_Z, SDLK_Z, SDL_KMOD_NONE, false, key_timestamp(app)) &&
           pump_events(app);
}

/* The shared body of the earlier-time and later-time loads. The player has just loaded a slot whose time is
 * `want_now`: its input must be re-anchored there, no key may be left held, a fresh Z press must be accepted and
 * must reach the guest within one frame of its scheduled time, and the same load without the press (the control,
 * observed first) must keep A released. */
static bool check_reanchored_input(fixture *fx, uint64_t want_now, const char *label) {
    player *app = &fx->app;
    gbb_input_clock clock;
    memset(&clock, 0, sizeof(clock));
    clock.struct_size = GBB_INPUT_CLOCK_SIZE_V1;
    REQUIRE(gbb_get_input_clock(app->machine, &clock) == GBB_OK);
    if (clock.now_half_dots != want_now) FAIL("%s: loaded time %llu, wanted %llu", label,
                                              (unsigned long long)clock.now_half_dots,
                                              (unsigned long long)want_now);
    /* Cursor and anchor sit at the restored time, nothing is held, and the eight releases are queued. */
    REQUIRE(app->input.guest_cursor_half_dots == want_now && app->input.guest_anchor_half_dots == want_now);
    REQUIRE(app->input.keyboard_buttons == 0u && app->input.held_buttons == 0u &&
            app->input.release_pending_buttons == 0u);
    REQUIRE(app->input.pending_count == PLAYER_INPUT_BUTTON_COUNT && clock.queued_count == PLAYER_INPUT_BUTTON_COUNT);

    /* The control: one frame with no key, A stays released. */
    REQUIRE(run_frames(app, 1u));
    REQUIRE(guest_sees_a_released(app) == 1);

    const bool paused_before = app->user_paused;
    REQUIRE(z_event(app, SDL_EVENT_KEY_DOWN));
    REQUIRE(strstr(app->status, "Input paused after queue error") == NULL);
    REQUIRE(app->user_paused == paused_before);
    memset(&clock, 0, sizeof(clock));
    clock.struct_size = GBB_INPUT_CLOCK_SIZE_V1;
    REQUIRE(gbb_get_input_clock(app->machine, &clock) == GBB_OK);
    REQUIRE(clock.queued_count == 1u);
    if (clock.last_queued_half_dots - clock.now_half_dots > PLAYER_FRAME_HALF_DOTS)
        FAIL("%s: the press is scheduled %llu half-dots ahead, more than one frame", label,
             (unsigned long long)(clock.last_queued_half_dots - clock.now_half_dots));

    /* Run until a frame after the press's time; the guest must see A pressed by then. */
    const uint64_t press_at = clock.last_queued_half_dots;
    for (unsigned frames = 0u; frames < 4u && clock.now_half_dots < press_at + PLAYER_FRAME_HALF_DOTS; ++frames) {
        REQUIRE(run_frames(app, 1u));
        REQUIRE(gbb_get_input_clock(app->machine, &clock) == GBB_OK);
    }
    REQUIRE(clock.now_half_dots >= press_at + PLAYER_FRAME_HALF_DOTS);
    if (guest_sees_a_released(app) != 0) FAIL("%s: the guest never saw the A press", label);
    return true;
}

static bool case_reanchor_body(fixture *fx) {
    player *app = &fx->app;
    REQUIRE(run_frames(app, 3u));
    REQUIRE(press_digit(app, 2u, SDL_KMOD_NONE));
    uint64_t t1 = 0u;
    REQUIRE(machine_now(app->machine, &t1));
    REQUIRE(key_down(app, SDL_SCANCODE_S, SDLK_S, SDL_KMOD_LGUI));
    REQUIRE(strcmp(app->status, "Saved slot 2") == 0);

    REQUIRE(run_frames(app, 600u));
    REQUIRE(press_digit(app, 4u, SDL_KMOD_NONE));
    uint64_t t2 = 0u;
    REQUIRE(machine_now(app->machine, &t2) && t2 > t1);
    REQUIRE(key_down(app, SDL_SCANCODE_S, SDLK_S, SDL_KMOD_LGUI));
    REQUIRE(strcmp(app->status, "Saved slot 4") == 0);

    /* Earlier-time load: the player's cursor is far ahead of the restored machine. */
    REQUIRE(press_digit(app, 2u, SDL_KMOD_NONE));
    REQUIRE(key_down(app, SDL_SCANCODE_L, SDLK_L, SDL_KMOD_LGUI));
    REQUIRE(strncmp(app->status, "Loaded slot 2", 13u) == 0);
    REQUIRE(check_reanchored_input(fx, t1, "earlier-time"));

    /* Z is still held when a later-time state loads: the load must let go of it. */
    REQUIRE(press_digit(app, 4u, SDL_KMOD_NONE));
    REQUIRE(app->input.keyboard_buttons != 0u);
    REQUIRE(key_down(app, SDL_SCANCODE_L, SDLK_L, SDL_KMOD_LGUI));
    REQUIRE(strncmp(app->status, "Loaded slot 4", 13u) == 0);
    REQUIRE(check_reanchored_input(fx, t2, "later-time"));
    return true;
}

static bool case_reanchor(void) {
    char rom_path[128];
    if (!write_joypad_rom(rom_path, sizeof(rom_path))) FAIL("could not write the joypad-mirror ROM");
    fixture fx;
    const bool ok = fx_setup(&fx, rom_path) && case_reanchor_body(&fx);
    fx_teardown(&fx);
    (void)unlink(rom_path);
    return ok;
}

/* ---- Case: status_line ----------------------------------------------------------------------------- */

static bool case_status_line_body(fixture *fx) {
    player *app = &fx->app;
    char title[PLAYER_TITLE_SIZE];
    char capture[256];
    (void)snprintf(capture, sizeof(capture), "%s/stderr.txt", fx->battery_root);
    REQUIRE(run_frames(app, 2u));

    /* Without a battery-save failure the slot message is the whole status. */
    REQUIRE(press_digit(app, 2u, SDL_KMOD_NONE));
    REQUIRE(key_down(app, SDL_SCANCODE_S, SDLK_S, SDL_KMOD_LGUI));
    format_window_title(app, title, sizeof(title));
    REQUIRE(strstr(title, " | Saved slot 2 | ") != NULL);

    /* With one, the title status is `<save_status> · <slot message>` and the log line carries the gbb_error. */
    app->save_status_active = true;
    (void)snprintf(app->save_status, sizeof(app->save_status), "Battery save failed");
    const int saved = begin_capture(capture);
    REQUIRE(saved >= 0);
    const bool pressed = key_down(app, SDL_SCANCODE_S, SDLK_S, SDL_KMOD_LGUI);
    end_capture(saved);
    REQUIRE(pressed);
    format_window_title(app, title, sizeof(title));
    REQUIRE(strstr(title, " | Battery save failed \xc2\xb7 Saved slot 2 | ") != NULL);
    REQUIRE(file_contains(capture, "gabbaboy-player: slot op=save slot=2 outcome=saved gbb_error=0\n"));

    /* Any later status replaces the slot message. */
    set_status(app, "Running");
    format_window_title(app, title, sizeof(title));
    REQUIRE(strstr(title, " | Battery save failed | ") != NULL && strstr(title, "\xc2\xb7") == NULL);

    /* A load clears the audio backlog, redraws and restarts the .gbb cadence, and keeps the pause. */
    REQUIRE(run_frames(app, 1u));
    app->audio = player_audio_test_create(true);
    REQUIRE(app->audio != NULL);
    static const gbb_audio_frame queued[] = {{1, -1}, {2, -2}, {3, -3}, {4, -4}};
    REQUIRE(player_audio_submit(app->audio, queued, 4u) && player_audio_test_queued(app->audio) == 4u);
    app->needs_redraw = false;
    app->displayed_generation = 77u;
    app->save_cadence = (player_save_cadence){99u, 5u, 6u, true};
    const bool user_paused_before = app->user_paused;
    const int saved_load = begin_capture(capture);
    REQUIRE(saved_load >= 0);
    const bool loaded = key_down(app, SDL_SCANCODE_L, SDLK_L, SDL_KMOD_LGUI);
    end_capture(saved_load);
    REQUIRE(loaded);
    REQUIRE(file_contains(capture, "gabbaboy-player: slot op=load slot=2 outcome=loaded gbb_error=0\n"));
    REQUIRE(player_audio_test_queued(app->audio) == 0u &&
            player_audio_flushed_bytes(app->audio) == sizeof(queued));
    REQUIRE(app->needs_redraw && app->displayed_generation == 0u);
    uint64_t generation = 0u;
    REQUIRE(gbb_battery_generation(app->machine, &generation) == GBB_OK);
    REQUIRE(!app->save_cadence.dirty && app->save_cadence.observed_generation == generation);
    REQUIRE(app->user_paused == user_paused_before);

    /* The loaded battery differs from the last .gbb save; the "Battery RAM changed" hint must not wipe the
     * message the player has just been shown. */
    REQUIRE(generation != app->save_identity.saved_generation);
    update_battery_save(app);
    format_window_title(app, title, sizeof(title));
    REQUIRE(strstr(title, "Battery save failed \xc2\xb7 Loaded slot 2 (" COMMAND_GLYPH "Z undoes)") != NULL);
    (void)unlink(capture);
    return true;
}

static bool case_status_line(const char *rom_path) {
    fixture fx;
    const bool ok = fx_setup(&fx, rom_path) && case_status_line_body(&fx);
    fx_teardown(&fx);
    return ok;
}

/* ---- Case: help_text ------------------------------------------------------------------------------- */

static size_t count_occurrences(const char *text, const char *needle) {
    size_t count = 0u;
    for (const char *at = strstr(text, needle); at != NULL; at = strstr(at + strlen(needle), needle)) ++count;
    return count;
}

static bool case_help_text_body(fixture *fx) {
    char message[4096];
    const int written = format_help_message(&fx->app, message, sizeof(message));
    REQUIRE(written > 0 && (size_t)written < sizeof(message));
    REQUIRE(strstr(message, "Select state slot: 1-9\n") != NULL);
    REQUIRE(strstr(message, "Save state to slot: Command-S\n") != NULL);
    REQUIRE(strstr(message, "Load state from slot: Command-L\n") != NULL);
    REQUIRE(strstr(message, "Undo last load: Command-Z\n") != NULL);
    REQUIRE(count_occurrences(message,
        "Saving replaces the slot. Loading also replaces the game's battery save; "
        COMMAND_GLYPH "Z undoes the last load.") == 1u);
    /* The prior help lines survive, and the limitations text ends the message. */
    REQUIRE(strstr(message, "Reset current ROM: R\n") != NULL);
    REQUIRE(strstr(message, "hidden in fullscreen and is not announced by VoiceOver.") != NULL);
    return true;
}

static bool case_help_text(const char *rom_path) {
    fixture fx;
    const bool ok = fx_setup(&fx, rom_path) && case_help_text_body(&fx);
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
    else if (strcmp(g_case, "reanchor") == 0) ok = case_reanchor();
    else if (strcmp(g_case, "status_line") == 0 && rom != NULL) ok = case_status_line(rom);
    else if (strcmp(g_case, "help_text") == 0 && rom != NULL) ok = case_help_text(rom);
    else {
        fprintf(stderr, "unknown case or missing rom: %s\n", g_case);
        return 2;
    }
    if (ok) printf("PASS %s\n", g_case);
    return ok ? 0 : 1;
}
