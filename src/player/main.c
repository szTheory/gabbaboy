#include "input.h"
#include "limitations.h"
#include "presentation.h"
#include "session.h"
#include "audio.h"

#include <stdatomic.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <spawn.h>
#include <signal.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define PLAYER_FRAME_WIDTH 160u
#define PLAYER_FRAME_HEIGHT 144u
#define PLAYER_FRAME_HALF_DOTS UINT64_C(140448)
#define PLAYER_MAX_OPERATION_HALF_DOTS UINT64_C(40)
#define PLAYER_BATTERY_SMOKE_HALF_DOTS UINT64_C(200000)
#define PLAYER_TITLE_SIZE 512u

typedef enum {
    PLAYER_DIALOG_SELECTED = 1,
    PLAYER_DIALOG_CANCELLED,
    PLAYER_DIALOG_FAILED,
    PLAYER_DIALOG_TOO_MANY,
    PLAYER_DIALOG_PATH_TOO_LONG,
    PLAYER_DIALOG_OUT_OF_MEMORY
} player_dialog_result_code;

typedef struct {
    player_dialog_result_code code;
    char path[];
} player_dialog_result;

typedef enum {
    PLAYER_TRANSITION_NONE = 0,
    PLAYER_TRANSITION_QUIT,
    PLAYER_TRANSITION_RESET,
    PLAYER_TRANSITION_REPLACE
} player_transition;

typedef struct {
    SDL_JoystickID id;
    SDL_Gamepad *handle;
} player_gamepad;

typedef struct {
    gbb_instance *machine;
    player_audio *audio;
    player_input_state input;
    player_gamepad gamepads[PLAYER_INPUT_GAMEPAD_CAPACITY];
    SDL_Window *window;
    SDL_Surface *surface;
    SDL_Renderer *renderer;
    SDL_Texture *texture;
    SDL_FRect frame_destination;
    char *current_rom_path;
    char *pending_rom_path;
    player_save_identity save_identity;
    player_save_cadence save_cadence;
    int save_lock_fd;
    char status[192];
    char save_status[192];
    char save_error[128];
    Uint32 dialog_event_type;
    uint64_t displayed_generation;
    atomic_bool dialog_callback_done;
    atomic_bool dialog_delivery_failed;
    bool running;
    bool needs_redraw;
    bool suppress_frame;
    bool window_focused;
    bool user_paused;
    bool dialog_pending;
    bool dialog_was_paused;
    bool quit_after_dialog;
    bool save_flush_failed;
    bool save_status_active;
    bool save_retry_required;
    bool skip_final_save;
    bool transition_was_paused;
    player_transition pending_transition;
} player;

extern char **environ;

static void set_status(player *app, const char *status);
static bool attempt_battery_save(player *app, bool show_saved_status);
static void request_quit(player *app);
static void begin_transition(player *app, player_transition transition,
                             const char *replacement_path);
static void destroy_player(player *app);

static bool run_pulse_audio_smoke(player *app, const char *rom_path) {
    size_t rom_size = 0u;
    uint8_t *rom = SDL_LoadFile(rom_path, &rom_size);
    if (rom == NULL || rom_size != 32768u) {
        SDL_free(rom);
        fputs("Could not prepare the authored pulse smoke guest\n", stderr);
        return false;
    }
    static const uint8_t program[] = {
        0x3Eu, 0xF0u, 0xEAu, 0x12u, 0xFFu, /* NR12: DAC on, volume 15 */
        0x3Eu, 0x80u, 0xEAu, 0x11u, 0xFFu, /* NR11: 12.5% duty */
        0x3Eu, 0xF0u, 0xEAu, 0x13u, 0xFFu, /* NR13 frequency */
        0x3Eu, 0x87u, 0xEAu, 0x14u, 0xFFu, /* NR14 trigger */
        0x18u, 0xFEu
    };
    memcpy(rom + 0x100u, program, sizeof(program));
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
    gbb_instance *machine = NULL;
    const bool loaded = gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) == GBB_OK &&
        gbb_load_rom(machine, rom, rom_size) == GBB_OK;
    SDL_free(rom);
    if (!loaded) {
        gbb_destroy(machine);
        fputs("Could not load the authored pulse smoke guest\n", stderr);
        return false;
    }
    gbb_audio_frame frames[512];
    uint64_t elapsed = 0u;
    uint64_t produced = 0u;
    uint64_t nonzero = 0u;
    uint64_t submitted = 0u;
    const uint64_t target = PLAYER_FRAME_HALF_DOTS;
    while (elapsed < target) {
        size_t count = 0u;
        const uint64_t remain = target - elapsed;
        const gbb_run_result result = gbb_run_audio(machine,
            remain + PLAYER_MAX_OPERATION_HALF_DOTS, frames, 512u, &count);
        elapsed += result.consumed_half_dots;
        produced += count;
        for (size_t i = 0u; i < count; ++i)
            if (frames[i].left != 0 || frames[i].right != 0) ++nonzero;
        if (count != 0u && app->audio != NULL) {
            if (!player_audio_submit(app->audio, frames, (unsigned)count)) {
                fputs("Authored pulse PCM could not enter the player ring\n", stderr);
                gbb_destroy(machine);
                return false;
            }
            submitted += count;
        }
        if (result.reason != GBB_STOP_BUDGET && result.reason != GBB_STOP_OUTPUT_FULL) {
            fprintf(stderr, "Pulse smoke guest stopped with reason %d\n", (int)result.reason);
            gbb_destroy(machine);
            return false;
        }
        if (result.consumed_half_dots == 0u && count == 0u) {
            fputs("Pulse smoke guest made no progress\n", stderr);
            gbb_destroy(machine);
            return false;
        }
    }
    gbb_destroy(machine);
    if (produced == 0u || nonzero == 0u ||
        (app->audio != NULL && submitted == 0u)) {
        fputs("Authored pulse guest did not produce nonzero PCM for the SDL adapter\n", stderr);
        return false;
    }
    printf("audio smoke: guest_frames=%llu nonzero_frames=%llu submitted_frames=%llu sink=%s unavailable_discard_frames=%llu underflow_frames=%llu backpressure_events=%llu high_water_frames=%u queued_input_bytes=%llu\n",
        (unsigned long long)produced, (unsigned long long)nonzero,
        (unsigned long long)submitted,
        player_audio_available(app->audio) ? "sdl" : "unavailable",
        (unsigned long long)player_audio_unavailable_frames(app->audio),
        (unsigned long long)(app->audio != NULL ? player_audio_underflow(app->audio) : 0u),
        (unsigned long long)(app->audio != NULL ? player_audio_backpressure_events(app->audio) : 0u),
        app->audio != NULL ? player_audio_high_water(app->audio) : 0u,
        (unsigned long long)player_audio_queued_input_bytes(app->audio));
    return true;
}

static char *duplicate_path(const char *path) {
    const size_t length = strlen(path);
    if (length == SIZE_MAX) return NULL;
    char *copy = malloc(length + 1u);
    if (copy != NULL) memcpy(copy, path, length + 1u);
    return copy;
}

static char *packaged_fixture_path(const char *relative_path) {
    const char *base_path = SDL_GetBasePath();
    if (base_path == NULL) return NULL;
    const size_t base_length = strlen(base_path);
    const bool has_separator = base_length > 0u &&
        (base_path[base_length - 1u] == '/' || base_path[base_length - 1u] == '\\');
    const size_t relative_length = strlen(relative_path);
    const size_t separator_length = has_separator ? 0u : 1u;
    if (base_length > SIZE_MAX - separator_length - relative_length - 1u) return NULL;
    char *candidate = malloc(base_length + separator_length + relative_length + 1u);
    if (candidate == NULL) return NULL;
    memcpy(candidate, base_path, base_length);
    size_t offset = base_length;
    if (!has_separator) candidate[offset++] = '/';
    memcpy(candidate + offset, relative_path, relative_length + 1u);
    FILE *rom = fopen(candidate, "rb");
    if (rom == NULL) {
        free(candidate);
        return NULL;
    }
    fclose(rom);
    return candidate;
}

static char *packaged_demo_rom_path(void) {
    return packaged_fixture_path(
        "../share/gabbaboy/fixtures/visible-demo/demo.gb");
}

static char *packaged_battery_rom_path(void) {
    return packaged_fixture_path(
        "../share/gabbaboy/fixtures/mbc1-continuation/continuation.gb");
}

static char *resolve_demo_rom_path(const char *requested_path,
                                   bool require_packaged_path) {
    if (requested_path != NULL) return duplicate_path(requested_path);
    char *packaged_path = packaged_demo_rom_path();
    if (packaged_path != NULL || require_packaged_path) return packaged_path;
    return duplicate_path(GABBABOY_PLAYER_DEMO_ROM);
}

static bool create_machine(player *app, const char *demo_rom_path) {
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &app->machine) != GBB_OK) {
        fputs("Could not create the DMG-CPU-B machine\n", stderr);
        return false;
    }
    char error[192];
    if (!player_session_replace_rom(app->machine, &app->current_rom_path,
                                    demo_rom_path, &app->save_identity,
                                    error, sizeof(error))) {
        fprintf(stderr, "Could not load the owned demo ROM: %s\n", error);
        return false;
    }
    const player_session_lock_result lock_result = player_session_lock_battery(
        &app->save_identity, &app->save_lock_fd, error, sizeof(error));
    if (lock_result != PLAYER_SESSION_LOCK_ACQUIRED) {
        fprintf(stderr, "Could not open the selected battery session: %s\n", error);
        return false;
    }
    if (!player_session_load_battery(app->machine, &app->save_identity,
                                     error, sizeof(error))) {
        set_status(app, error);
        fprintf(stderr, "Battery save warning: %s\n", error);
    } else if (app->save_identity.battery_backed) {
        set_status(app, "Battery RAM loaded; changes are in memory until saved");
    } else {
        set_status(app, "Ready");
    }
    uint64_t generation = 0u;
    if (app->save_identity.battery_backed &&
        gbb_battery_generation(app->machine, &generation) != GBB_OK)
        generation = app->save_identity.saved_generation;
    player_save_cadence_reset(&app->save_cadence, generation);
    return true;
}

static bool create_video(player *app, bool hidden) {
    if (hidden) {
        app->surface = SDL_CreateSurface((int)(PLAYER_FRAME_WIDTH * 2u),
                                         (int)(PLAYER_FRAME_HEIGHT * 2u),
                                         SDL_PIXELFORMAT_RGBA32);
        if (app->surface == NULL) {
            fprintf(stderr, "SDL_CreateSurface: %s\n", SDL_GetError());
            return false;
        }
        app->renderer = SDL_CreateSoftwareRenderer(app->surface);
        if (app->renderer == NULL) {
            fprintf(stderr, "SDL_CreateSoftwareRenderer: %s\n", SDL_GetError());
            return false;
        }
    } else {
        app->window = SDL_CreateWindow("GabbaBoy — DMG preview",
                                       (int)(PLAYER_FRAME_WIDTH * 3u),
                                       (int)(PLAYER_FRAME_HEIGHT * 3u),
                                       SDL_WINDOW_HIGH_PIXEL_DENSITY);
        if (app->window == NULL) {
            fprintf(stderr, "SDL_CreateWindow: %s\n", SDL_GetError());
            return false;
        }
        if (!SDL_SetWindowMinimumSize(app->window, (int)PLAYER_FRAME_WIDTH,
                                      (int)PLAYER_FRAME_HEIGHT)) {
            fprintf(stderr, "SDL_SetWindowMinimumSize: %s\n", SDL_GetError());
            return false;
        }
        app->renderer = SDL_CreateRenderer(app->window, NULL);
        if (app->renderer == NULL) {
            fprintf(stderr, "SDL_CreateRenderer: %s\n", SDL_GetError());
            return false;
        }
    }
    if (!SDL_SetRenderLogicalPresentation(app->renderer,
            (int)PLAYER_FRAME_WIDTH, (int)PLAYER_FRAME_HEIGHT,
            SDL_LOGICAL_PRESENTATION_INTEGER_SCALE)) {
        fprintf(stderr, "SDL_SetRenderLogicalPresentation: %s\n", SDL_GetError());
        return false;
    }
    app->texture = SDL_CreateTexture(app->renderer, SDL_PIXELFORMAT_RGBA32,
                                     SDL_TEXTUREACCESS_STREAMING,
                                     (int)PLAYER_FRAME_WIDTH,
                                     (int)PLAYER_FRAME_HEIGHT);
    if (app->texture == NULL) {
        fprintf(stderr, "SDL_CreateTexture: %s\n", SDL_GetError());
        return false;
    }
    if (!SDL_SetTextureScaleMode(app->texture, SDL_SCALEMODE_NEAREST)) {
        fprintf(stderr, "SDL_SetTextureScaleMode: %s\n", SDL_GetError());
        return false;
    }
    return true;
}

static bool advance_to(player *app, uint64_t target_half_dots, bool finish_target) {
    while (app->input.guest_cursor_half_dots < target_half_dots) {
        const uint64_t remaining =
            target_half_dots - app->input.guest_cursor_half_dots;
        const uint64_t budget = finish_target &&
            remaining <= UINT64_MAX - PLAYER_MAX_OPERATION_HALF_DOTS
            ? remaining + PLAYER_MAX_OPERATION_HALF_DOTS : remaining;
        gbb_run_result result;
        if (app->audio != NULL) {
            gbb_audio_frame frames[512];
            unsigned capacity = player_audio_capacity(app->audio);
            if (capacity > 512u) capacity = 512u;
            if (capacity == 0u) {
                player_audio_note_backpressure(app->audio);
                return !finish_target;
            }
            size_t count = 0u;
            result = gbb_run_audio(app->machine, budget, frames, capacity, &count);
            if (count != 0u && !player_audio_submit(app->audio, frames, (unsigned)count)) {
                fputs("Audio producer capacity changed before publication\n", stderr);
                return false;
            }
        } else {
            result = gbb_run(app->machine, budget, NULL, 0);
        }
        if (result.consumed_half_dots >
            UINT64_MAX - app->input.guest_cursor_half_dots) {
            fputs("Guest timeline overflow\n", stderr);
            return false;
        }
        player_input_reconcile(&app->input,
            app->input.guest_cursor_half_dots + result.consumed_half_dots);
        if (result.reason != GBB_STOP_BUDGET && result.reason != GBB_STOP_OUTPUT_FULL) {
            fprintf(stderr, "Guest stopped at half-dot %llu (reason %d)\n",
                    (unsigned long long)app->input.guest_cursor_half_dots,
                    (int)result.reason);
            return false;
        }
        if (result.consumed_half_dots == 0) return !finish_target || result.reason == GBB_STOP_OUTPUT_FULL;
    }
    return true;
}

static bool update_frame(player *app, bool required) {
    uint8_t shades[PLAYER_FRAME_WIDTH * PLAYER_FRAME_HEIGHT];
    gbb_frame_info info;
    const gbb_error result = gbb_copy_frame(app->machine, shades, sizeof(shades),
                                            PLAYER_FRAME_WIDTH, &info);
    if (result == GBB_FRAME_NOT_READY && !required) return true;
    if (result != GBB_OK) {
        fprintf(stderr, "Could not copy completed frame (error %d)\n", (int)result);
        return false;
    }
    if (info.generation == app->displayed_generation) return true;

    static const uint8_t palette[4][4] = {
        {224, 248, 208, 255}, {136, 192, 112, 255},
        {52, 104, 86, 255}, {8, 24, 32, 255}
    };
    uint8_t rgba[PLAYER_FRAME_WIDTH * PLAYER_FRAME_HEIGHT * 4u];
    for (size_t i = 0; i < sizeof(shades); ++i) {
        const unsigned shade = shades[i];
        if (shade > 3u) {
            fputs("Core returned a shade index outside [0,3]\n", stderr);
            return false;
        }
        memcpy(rgba + i * 4u, palette[shade], 4u);
    }
    if (!SDL_UpdateTexture(app->texture, NULL, rgba,
                           (int)(PLAYER_FRAME_WIDTH * 4u))) {
        fprintf(stderr, "SDL_UpdateTexture: %s\n", SDL_GetError());
        return false;
    }
    app->displayed_generation = info.generation;
    app->needs_redraw = true;
    return true;
}

static void recover_input_after_dialog(player *app);

static const char *rom_basename(const char *path) {
    if (path == NULL) return "(none)";
    const char *base = path;
    for (const char *cursor = path; *cursor != '\0'; ++cursor)
        if (*cursor == '/' || *cursor == '\\') base = cursor + 1;
    return base;
}

static size_t utf8_prefix(const char *text, size_t maximum) {
    size_t length = 0;
    while (length < maximum && text[length] != '\0') ++length;
    if (text[length] != '\0')
        while (length > 0 && ((unsigned char)text[length] & 0xc0u) == 0x80u)
            --length;
    return length;
}

static void update_window_title(player *app) {
    if (app->window == NULL) return;
    const char *base = rom_basename(app->current_rom_path);
    char short_name[160];
    const size_t base_length = utf8_prefix(base, sizeof(short_name) - 1u);
    memcpy(short_name, base, base_length);
    short_name[base_length] = '\0';
    char title[PLAYER_TITLE_SIZE];
    (void)snprintf(title, sizeof(title),
        "GabbaBoy | %s | %s | %s | \xe2\x8c\x98O Open, \xe2\x8c\x98Q Quit, F1 Help | %s",
        short_name, app->user_paused || app->input.paused ? "Paused" : "Running",
        app->save_status_active ? app->save_status :
            (app->status[0] == '\0' ? "Ready" : app->status),
        player_audio_available(app->audio) ? "Audio ready" : "Audio unavailable");
    (void)SDL_SetWindowTitle(app->window, title);
}

static void set_status(player *app, const char *status) {
    (void)snprintf(app->status, sizeof(app->status), "%s", status);
    update_window_title(app);
}

static void show_help(player *app) {
    const bool resume_after = !app->user_paused && app->window_focused &&
                              !app->dialog_pending;
    (void)player_input_focus_lost(&app->input, app->machine, SDL_GetTicksNS());
    char message[1024];
    (void)snprintf(message, sizeof(message),
        "Current ROM: %s\n\n"
        "Open ROM: Command-O\nQuit: Command-Q\n"
        "D-pad: arrow keys\nA / B: Z / X\nStart / Select: Return / Right Shift\n"
        "Pause / resume: Space\nVolume down / up: [ / ]\n"
        "Reset current ROM: R\nSave now / retry: S\n\n"
        "A blocked final save offers R to retry, C to continue without saving, or Escape to cancel.\n"
        "Status: %.160s\n"
        "%s",
        rom_basename(app->current_rom_path), app->save_status_active
            ? app->save_status : (app->status[0] == '\0' ? "Ready" : app->status),
        GBB_PLAYER_LIMITATIONS_TEXT);
    if (!SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_INFORMATION,
                                  "GabbaBoy Controls and Limitations",
                                  message, app->window))
        fprintf(stderr, "Could not show player help: %s\n", SDL_GetError());
    if (resume_after) {
        recover_input_after_dialog(app);
        if (!app->user_paused) set_status(app, "Running");
    }
}

static bool layout_matches_sdl(player *app) {
    int output_width = 0;
    int output_height = 0;
    if (!SDL_GetRenderOutputSize(app->renderer, &output_width, &output_height)) {
        fprintf(stderr, "SDL_GetRenderOutputSize: %s\n", SDL_GetError());
        return false;
    }
    if (output_width <= 0 || output_height <= 0) {
        app->suppress_frame = true;
        app->needs_redraw = true;
        return true;
    }

    player_presentation_rect expected;
    if (!player_presentation_layout(output_width, output_height, &expected)) {
        if (app->window != NULL) {
            app->suppress_frame = true;
            return true;
        }
        fputs("Offscreen render target is smaller than the native frame\n", stderr);
        return false;
    }
    app->suppress_frame = false;
    SDL_FRect actual;
    if (!SDL_GetRenderLogicalPresentationRect(app->renderer, &actual)) {
        fprintf(stderr, "SDL_GetRenderLogicalPresentationRect: %s\n", SDL_GetError());
        return false;
    }
    const float output_center_x = (float)output_width / 2.0f;
    const float output_center_y = (float)output_height / 2.0f;
    if (actual.w != (float)expected.width || actual.h != (float)expected.height ||
        actual.x + actual.w / 2.0f != output_center_x ||
        actual.y + actual.h / 2.0f != output_center_y) {
        fputs("SDL integer presentation does not match the tested drawable layout\n",
              stderr);
        return false;
    }
    const float logical_scale = (float)expected.scale;
    app->frame_destination = (SDL_FRect){
        ((float)expected.x - actual.x) / logical_scale,
        ((float)expected.y - actual.y) / logical_scale,
        (float)PLAYER_FRAME_WIDTH,
        (float)PLAYER_FRAME_HEIGHT
    };
    return true;
}

static bool draw_frame(player *app) {
    if (!layout_matches_sdl(app)) return false;
    if (app->suppress_frame) return true;
    if (!SDL_SetRenderDrawColor(app->renderer, 8, 24, 32, 255) ||
        !SDL_RenderClear(app->renderer)) {
        fprintf(stderr, "SDL render clear: %s\n", SDL_GetError());
        return false;
    }
    if (app->displayed_generation != 0 &&
        !SDL_RenderTexture(app->renderer, app->texture, NULL,
                           &app->frame_destination)) {
        fprintf(stderr, "SDL_RenderTexture: %s\n", SDL_GetError());
        return false;
    }
    if (!SDL_RenderPresent(app->renderer)) {
        fprintf(stderr, "SDL_RenderPresent: %s\n", SDL_GetError());
        return false;
    }
    app->needs_redraw = false;
    return true;
}

static void recover_input_after_dialog(player *app) {
    if (app->user_paused || !app->window_focused || app->dialog_pending) {
        player_input_pause(&app->input);
        return;
    }
    const gbb_error releases = player_input_retry_focus_releases(
        &app->input, app->machine, SDL_GetTicksNS());
    if (releases != GBB_OK ||
        !player_input_resume(&app->input, SDL_GetTicksNS())) {
        app->user_paused = true;
        set_status(app, "Input remains paused until held-button releases are admitted");
        return;
    }
}

static void reset_session(player *app) {
    if (gbb_reset(app->machine) != GBB_OK) {
        set_status(app, "Reset failed; the current ROM remains loaded");
        return;
    }
    app->user_paused = false;
    player_input_reset(&app->input, SDL_GetTicksNS());
    if (!app->window_focused || app->dialog_pending)
        player_input_pause(&app->input);
    app->displayed_generation = 0;
    app->needs_redraw = true;
    uint64_t generation = 0u;
    if (app->save_identity.battery_backed)
        (void)gbb_battery_generation(app->machine, &generation);
    player_save_cadence_reset(&app->save_cadence, generation);
    set_status(app, app->save_identity.battery_backed
        ? "Current ROM reset; battery RAM remains in memory"
        : "Current ROM reset");
}

static bool same_save_identity(const player_save_identity *left,
                               const player_save_identity *right) {
    return left->battery_backed && right->battery_backed &&
        left->cartridge_type == right->cartridge_type &&
        left->ram_size == right->ram_size &&
        memcmp(left->rom_sha256, right->rom_sha256,
               sizeof(left->rom_sha256)) == 0;
}

static bool replace_session_rom(player *app, const char *path) {
    char error[192];
    gbb_instance *candidate_machine = NULL;
    char *candidate_path = NULL;
    player_save_identity candidate_identity;
    int candidate_lock_fd = -1;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &candidate_machine) != GBB_OK) {
        set_status(app, "Could not stage the selected ROM; current ROM unchanged");
        return false;
    }
    if (!player_session_replace_rom(candidate_machine, &candidate_path, path,
                                    &candidate_identity, error, sizeof(error))) {
        gbb_destroy(candidate_machine);
        set_status(app, error);
        return false;
    }
    const bool reuses_lock = same_save_identity(&app->save_identity,
                                                &candidate_identity);
    if (!reuses_lock) {
        const player_session_lock_result lock_result =
            player_session_lock_battery(&candidate_identity, &candidate_lock_fd,
                                        error, sizeof(error));
        if (lock_result != PLAYER_SESSION_LOCK_ACQUIRED) {
            gbb_destroy(candidate_machine);
            free(candidate_path);
            set_status(app, error);
            return false;
        }
    }
    const bool battery_loaded = player_session_load_battery(
        candidate_machine, &candidate_identity, error, sizeof(error));
    gbb_instance *old_machine = app->machine;
    char *old_path = app->current_rom_path;
    const int old_lock_fd = app->save_lock_fd;
    app->machine = candidate_machine;
    app->current_rom_path = candidate_path;
    app->save_identity = candidate_identity;
    app->save_lock_fd = reuses_lock ? old_lock_fd : candidate_lock_fd;
    if (!reuses_lock) candidate_lock_fd = -1;
    if (old_machine != NULL) gbb_destroy(old_machine);
    free(old_path);
    if (!reuses_lock) {
        int release_fd = old_lock_fd;
        player_session_unlock_battery(&release_fd);
    }
    app->user_paused = app->transition_was_paused;
    player_input_reset(&app->input, SDL_GetTicksNS());
    if (app->user_paused || !app->window_focused)
        player_input_pause(&app->input);
    app->displayed_generation = 0;
    app->needs_redraw = true;
    uint64_t generation = 0u;
    if (app->save_identity.battery_backed)
        (void)gbb_battery_generation(app->machine, &generation);
    player_save_cadence_reset(&app->save_cadence, generation);
    app->save_retry_required = false;
    app->save_status_active = false;
    if (!battery_loaded)
        set_status(app, error);
    else if (app->save_identity.battery_backed)
        set_status(app, "Battery RAM loaded; changes are in memory until saved");
    else
        set_status(app, "ROM loaded; input and display state reset");
    return true;
}

static void finish_transition(player *app, bool continue_without_saving);

static void refresh_save_failure_status(player *app) {
    if (!app->save_status_active) return;
    (void)snprintf(app->save_status, sizeof(app->save_status),
        "Battery save failed: %.88s%s", app->save_error,
        app->pending_transition != PLAYER_TRANSITION_NONE
            ? ". R retry, C continue without saving, Esc cancel"
            : ". Press S to retry");
    update_window_title(app);
}

static bool attempt_battery_save(player *app, bool show_saved_status) {
    if (!app->save_identity.battery_backed) return true;
    char error[192];
    if (!player_session_save_battery(app->machine, &app->save_identity,
                                     error, sizeof(error))) {
        (void)snprintf(app->save_error, sizeof(app->save_error), "%s", error);
        app->save_status_active = true;
        app->save_retry_required = true;
        refresh_save_failure_status(app);
        return false;
    }
    app->save_retry_required = false;
    uint64_t generation = 0u;
    if (gbb_battery_generation(app->machine, &generation) != GBB_OK)
        generation = app->save_identity.saved_generation;
    player_save_cadence_reset(&app->save_cadence, generation);
    app->save_status_active = false;
    app->save_status[0] = '\0';
    if (show_saved_status) set_status(app, "Battery RAM saved to disk");
    else update_window_title(app);
    return true;
}

static void cancel_transition(player *app) {
    (void)player_save_transition_resolve(true, false,
                                        PLAYER_SAVE_TRANSITION_CANCEL);
    app->pending_transition = PLAYER_TRANSITION_NONE;
    free(app->pending_rom_path);
    app->pending_rom_path = NULL;
    app->user_paused = app->transition_was_paused;
    if (app->user_paused || !app->window_focused) player_input_pause(&app->input);
    else recover_input_after_dialog(app);
    set_status(app, "Transition cancelled; current ROM remains active");
    refresh_save_failure_status(app);
}

static void finish_transition(player *app, bool continue_without_saving) {
    const player_transition transition = app->pending_transition;
    if (transition == PLAYER_TRANSITION_NONE) return;
    if (transition == PLAYER_TRANSITION_QUIT) {
        if (continue_without_saving) app->skip_final_save = true;
        app->pending_transition = PLAYER_TRANSITION_NONE;
        app->running = false;
        return;
    }
    if (transition == PLAYER_TRANSITION_RESET) {
        app->pending_transition = PLAYER_TRANSITION_NONE;
        reset_session(app);
        if (continue_without_saving && app->save_identity.battery_backed) {
            app->save_status_active = true;
            (void)snprintf(app->save_status, sizeof(app->save_status),
                           "Battery RAM remains only in memory; press S to save");
            update_window_title(app);
        }
        return;
    }
    if (transition == PLAYER_TRANSITION_REPLACE) {
        char *replacement_path = app->pending_rom_path;
        app->pending_rom_path = NULL;
        app->pending_transition = PLAYER_TRANSITION_NONE;
        const bool replaced = replace_session_rom(app, replacement_path);
        free(replacement_path);
        if (!replaced) {
            app->pending_transition = PLAYER_TRANSITION_NONE;
            app->user_paused = app->transition_was_paused;
            if (!app->user_paused && app->window_focused)
                recover_input_after_dialog(app);
            else
                player_input_pause(&app->input);
            refresh_save_failure_status(app);
        }
    }
}

static void begin_transition(player *app, player_transition transition,
                             const char *replacement_path) {
    if (app->pending_transition != PLAYER_TRANSITION_NONE) return;
    char *path_copy = NULL;
    if (transition == PLAYER_TRANSITION_REPLACE) {
        path_copy = duplicate_path(replacement_path);
        if (path_copy == NULL) {
            set_status(app, "Could not stage the selected ROM; current ROM unchanged");
            return;
        }
    }
    app->pending_rom_path = path_copy;
    app->pending_transition = transition;
    app->transition_was_paused = transition == PLAYER_TRANSITION_REPLACE
        ? app->dialog_was_paused : app->user_paused;
    app->user_paused = true;
    player_input_pause(&app->input);
    const bool saved = attempt_battery_save(app, false);
    if (player_save_transition_resolve(app->save_identity.battery_backed,
            saved, PLAYER_SAVE_TRANSITION_RETRY) ==
        PLAYER_SAVE_TRANSITION_SAVED) {
        finish_transition(app, false);
        return;
    }
    set_status(app, "Battery save failed; choose retry, continue, or cancel");
    app->save_status_active = true;
    update_window_title(app);
}

static void finish_dialog(player *app, player_dialog_result *result) {
    app->dialog_pending = false;
    const bool quit_after_dialog = app->quit_after_dialog;
    app->quit_after_dialog = false;
    if (quit_after_dialog) {
        free(result);
        request_quit(app);
        return;
    }
    switch (result->code) {
    case PLAYER_DIALOG_SELECTED:
        begin_transition(app, PLAYER_TRANSITION_REPLACE, result->path);
        free(result);
        return;
    case PLAYER_DIALOG_CANCELLED:
        app->user_paused = app->dialog_was_paused;
        set_status(app, "Open cancelled; current ROM unchanged");
        break;
    case PLAYER_DIALOG_TOO_MANY:
        app->user_paused = app->dialog_was_paused;
        set_status(app, "Select one ROM file; current ROM unchanged");
        break;
    case PLAYER_DIALOG_PATH_TOO_LONG:
        app->user_paused = app->dialog_was_paused;
        set_status(app, "ROM path is too long; current ROM unchanged");
        break;
    case PLAYER_DIALOG_OUT_OF_MEMORY:
        app->user_paused = app->dialog_was_paused;
        set_status(app, "Not enough memory to open ROM; current ROM unchanged");
        break;
    default:
        app->user_paused = app->dialog_was_paused;
        set_status(app, "File dialog failed; current ROM unchanged");
        break;
    }
    free(result);
    recover_input_after_dialog(app);
}

static void SDLCALL open_dialog_callback(void *userdata,
                                        const char *const *filelist,
                                        int filter) {
    (void)filter;
    player *app = userdata;
    player_dialog_result_code code = PLAYER_DIALOG_FAILED;
    const char *path = NULL;
    size_t path_length = 0;
    if (filelist != NULL && filelist[0] == NULL) {
        code = PLAYER_DIALOG_CANCELLED;
    } else if (filelist != NULL && filelist[0] != NULL) {
        if (filelist[1] != NULL) {
            code = PLAYER_DIALOG_TOO_MANY;
        } else {
            while (path_length <= PLAYER_SESSION_PATH_LIMIT &&
                   filelist[0][path_length] != '\0') ++path_length;
            if (path_length > PLAYER_SESSION_PATH_LIMIT)
                code = PLAYER_DIALOG_PATH_TOO_LONG;
            else {
                code = PLAYER_DIALOG_SELECTED;
                path = filelist[0];
            }
        }
    }

    const size_t allocation = sizeof(player_dialog_result) +
        (code == PLAYER_DIALOG_SELECTED ? path_length + 1u : 0u);
    player_dialog_result *result = malloc(allocation);
    if (result == NULL) {
        atomic_store_explicit(&app->dialog_delivery_failed, true, memory_order_release);
        atomic_store_explicit(&app->dialog_callback_done, true, memory_order_release);
        return;
    }
    result->code = code;
    if (path != NULL) memcpy(result->path, path, path_length + 1u);

    SDL_Event event;
    SDL_zero(event);
    event.type = app->dialog_event_type;
    event.user.code = (Sint32)code;
    event.user.data1 = result;
    atomic_store_explicit(&app->dialog_callback_done, true, memory_order_release);
    if (!SDL_PushEvent(&event)) {
        free(result);
        atomic_store_explicit(&app->dialog_delivery_failed, true, memory_order_release);
    }
}

static void request_open_rom(player *app) {
    if (app->dialog_pending) return;
    static const SDL_DialogFileFilter filters[] = {
        {"Game Boy ROM images", "gb;gbc"}
    };
    app->dialog_was_paused = app->user_paused || !app->window_focused;
    app->dialog_pending = true;
    const gbb_error release_result = player_input_focus_lost(
        &app->input, app->machine, SDL_GetTicksNS());
    atomic_store_explicit(&app->dialog_callback_done, false, memory_order_relaxed);
    atomic_store_explicit(&app->dialog_delivery_failed, false, memory_order_relaxed);
    set_status(app, release_result == GBB_OK
        ? "Choose one supported Game Boy ROM"
        : "Choose a ROM; held-button release remains pending");
    SDL_ShowOpenFileDialog(open_dialog_callback, app, app->window, filters,
                           (int)(sizeof(filters) / sizeof(filters[0])), NULL, false);
}

static void toggle_pause(player *app) {
    if (!app->user_paused) {
        app->user_paused = true;
        const gbb_error releases = player_input_focus_lost(
            &app->input, app->machine, SDL_GetTicksNS());
        set_status(app, releases == GBB_OK
            ? "Paused; held buttons released"
            : "Paused; held-button release remains pending");
        return;
    }
    app->user_paused = false;
    recover_input_after_dialog(app);
    if (app->user_paused) return;
    set_status(app, "Running");
}

static void request_quit(player *app) {
    if (app->dialog_pending) app->quit_after_dialog = true;
    else begin_transition(app, PLAYER_TRANSITION_QUIT, NULL);
}

static void handle_key(player *app, const SDL_KeyboardEvent *key, bool pressed) {
    if (app->pending_transition != PLAYER_TRANSITION_NONE) {
        if (pressed && !key->repeat) {
            if (key->scancode == SDL_SCANCODE_ESCAPE) {
                cancel_transition(app);
                return;
            }
            if (key->scancode == SDL_SCANCODE_R) {
                const bool saved = attempt_battery_save(app, false);
                if (player_save_transition_resolve(
                        app->save_identity.battery_backed, saved,
                        PLAYER_SAVE_TRANSITION_RETRY) ==
                    PLAYER_SAVE_TRANSITION_SAVED)
                    finish_transition(app, false);
                return;
            }
            if (key->scancode == SDL_SCANCODE_C) {
                if (player_save_transition_resolve(
                        app->save_identity.battery_backed, false,
                        PLAYER_SAVE_TRANSITION_CONTINUE) ==
                    PLAYER_SAVE_TRANSITION_CONTINUE_UNSAVED)
                    finish_transition(app, true);
                return;
            }
        }
        return;
    }
    if (pressed && !key->repeat) {
        const bool command = (key->mod & SDL_KMOD_GUI) != 0;
        if (command && key->key == SDLK_Q) {
            request_quit(app);
            return;
        }
        if (!app->dialog_pending && command && key->key == SDLK_O) {
            request_open_rom(app);
            return;
        }
        if (!app->dialog_pending && key->scancode == SDL_SCANCODE_F1) {
            show_help(app);
            return;
        }
        if (!app->dialog_pending && key->scancode == SDL_SCANCODE_SPACE) {
            toggle_pause(app);
            return;
        }
        if (!app->dialog_pending && (key->scancode == SDL_SCANCODE_LEFTBRACKET ||
                                     key->scancode == SDL_SCANCODE_RIGHTBRACKET)) {
            const int direction = key->scancode == SDL_SCANCODE_RIGHTBRACKET
                ? 1 : -1;
            if (player_audio_adjust_gain(app->audio, direction)) {
                char volume_status[64];
                (void)snprintf(volume_status, sizeof(volume_status),
                    "Volume %u%%", (unsigned)(player_audio_gain(app->audio) * 100.0f));
                set_status(app, volume_status);
            }
            return;
        }
        if (!app->dialog_pending && key->scancode == SDL_SCANCODE_R) {
            begin_transition(app, PLAYER_TRANSITION_RESET, NULL);
            return;
        }
        if (!app->dialog_pending && key->scancode == SDL_SCANCODE_S) {
            if (!app->save_identity.battery_backed)
                set_status(app, "This ROM has no battery-backed RAM");
            else
                (void)attempt_battery_save(app, true);
            return;
        }
    }
    const gbb_error result = player_input_key(&app->input, app->machine,
        key->timestamp, key->scancode, pressed, pressed && key->repeat);
    if (result != GBB_OK) {
        const gbb_error release_result = player_input_focus_lost(
            &app->input, app->machine, key->timestamp);
        app->user_paused = true;
        char status[192];
        (void)snprintf(status, sizeof(status),
            "Input paused after queue error %d; release recovery %s",
            (int)result, release_result == GBB_OK ? "queued" : "pending");
        set_status(app, status);
    }
}

static player_gamepad *find_player_gamepad(player *app, SDL_JoystickID id) {
    for (unsigned i = 0; i < PLAYER_INPUT_GAMEPAD_CAPACITY; ++i)
        if (app->gamepads[i].handle != NULL && app->gamepads[i].id == id)
            return &app->gamepads[i];
    return NULL;
}

static void handle_gamepad_added(player *app, SDL_JoystickID id) {
    if (id == 0 || find_player_gamepad(app, id) != NULL) return;
    player_gamepad *slot = NULL;
    for (unsigned i = 0; i < PLAYER_INPUT_GAMEPAD_CAPACITY; ++i) {
        if (app->gamepads[i].handle == NULL) {
            slot = &app->gamepads[i];
            break;
        }
    }
    if (slot == NULL) return;
    SDL_Gamepad *handle = SDL_OpenGamepad(id);
    if (handle == NULL) return;
    if (!player_input_gamepad_added(&app->input, id)) {
        SDL_CloseGamepad(handle);
        return;
    }
    *slot = (player_gamepad){id, handle};
}

static void handle_gamepad_removed(player *app, SDL_JoystickID id,
                                   uint64_t timestamp_ns) {
    const gbb_error result = player_input_gamepad_removed(
        &app->input, app->machine, timestamp_ns, id);
    player_gamepad *gamepad = find_player_gamepad(app, id);
    if (gamepad != NULL) {
        SDL_CloseGamepad(gamepad->handle);
        *gamepad = (player_gamepad){0};
    }
    if (result != GBB_OK)
        set_status(app, "Controller removed; its button release is pending");
}

static bool handle_event(player *app, const SDL_Event *event) {
    if (event->type == app->dialog_event_type) {
        player_dialog_result *result = event->user.data1;
        if (result != NULL) finish_dialog(app, result);
        return true;
    }
    if (event->type == SDL_EVENT_QUIT || event->type == SDL_EVENT_WINDOW_CLOSE_REQUESTED) {
        request_quit(app);
        return true;
    }
    if (event->type == SDL_EVENT_WINDOW_EXPOSED ||
        event->type == SDL_EVENT_WINDOW_RESIZED ||
        event->type == SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED ||
        event->type == SDL_EVENT_WINDOW_DISPLAY_SCALE_CHANGED ||
        event->type == SDL_EVENT_WINDOW_DISPLAY_CHANGED) {
        app->needs_redraw = true;
        app->suppress_frame = false;
    }
    if (event->type == SDL_EVENT_KEY_DOWN || event->type == SDL_EVENT_KEY_UP)
        handle_key(app, &event->key, event->type == SDL_EVENT_KEY_DOWN);
    if (event->type == SDL_EVENT_GAMEPAD_ADDED)
        handle_gamepad_added(app, event->gdevice.which);
    if (event->type == SDL_EVENT_GAMEPAD_REMOVED)
        handle_gamepad_removed(app, event->gdevice.which,
                               event->gdevice.timestamp);
    if (event->type == SDL_EVENT_GAMEPAD_BUTTON_DOWN ||
        event->type == SDL_EVENT_GAMEPAD_BUTTON_UP) {
        const gbb_error result = player_input_gamepad_button(
            &app->input, app->machine, event->gbutton.timestamp,
            event->gbutton.which, (SDL_GamepadButton)event->gbutton.button,
            event->type == SDL_EVENT_GAMEPAD_BUTTON_DOWN);
        if (result != GBB_OK) {
            const gbb_error released = player_input_focus_lost(
                &app->input, app->machine, event->gbutton.timestamp);
            app->user_paused = true;
            set_status(app, released == GBB_OK
                ? "Controller input paused after a guest queue error"
                : "Controller input paused; held-button release remains pending");
        }
    }
    if (event->type == SDL_EVENT_WINDOW_FOCUS_LOST) {
        app->window_focused = false;
        const gbb_error result = player_input_focus_lost(&app->input, app->machine,
                                                         event->window.timestamp);
        if (result != GBB_OK)
            set_status(app, "Focus lost; held-button releases remain pending");
        else
            set_status(app, "Focus lost; input paused and held buttons released");
    }
    if (event->type == SDL_EVENT_WINDOW_FOCUS_GAINED) {
        app->window_focused = true;
        const gbb_error result = player_input_focus_gained(
            &app->input, app->machine, event->window.timestamp,
            SDL_GetTicksNS(), app->user_paused || app->dialog_pending);
        if (result != GBB_OK) {
            app->user_paused = true;
            set_status(app, "Input remains paused until held-button releases are admitted");
        } else if (!app->dialog_pending) {
            set_status(app, app->user_paused
                ? "Focus returned; paused by user" : "Running");
        }
    }
    return true;
}

static bool pump_events(player *app) {
    SDL_Event event;
    while (SDL_PollEvent(&event)) {
        if (!handle_event(app, &event)) return false;
    }
    if (app->dialog_pending &&
        atomic_load_explicit(&app->dialog_callback_done, memory_order_acquire) &&
        atomic_load_explicit(&app->dialog_delivery_failed, memory_order_acquire)) {
        app->dialog_pending = false;
        app->user_paused = app->dialog_was_paused;
        set_status(app, "Dialog result could not be queued; current ROM unchanged");
        recover_input_after_dialog(app);
        if (app->quit_after_dialog) {
            app->quit_after_dialog = false;
            request_quit(app);
        }
    }
    return true;
}

static void update_battery_save(player *app) {
    if (!app->save_identity.battery_backed) return;
    uint64_t generation = 0u;
    if (gbb_battery_generation(app->machine, &generation) != GBB_OK) {
        if (!app->save_status_active) {
            (void)snprintf(app->save_status, sizeof(app->save_status),
                           "Could not read battery RAM status");
            app->save_status_active = true;
            app->save_retry_required = true;
            update_window_title(app);
        }
        return;
    }
    const bool was_dirty = app->save_cadence.dirty;
    const bool due = player_save_cadence_observe(&app->save_cadence,
        generation, app->save_identity.saved_generation, SDL_GetTicksNS());
    if (generation != app->save_identity.saved_generation && !was_dirty &&
        !app->save_status_active)
        set_status(app, "Battery RAM changed; progress is in memory until saved");
    if (due && !app->save_retry_required &&
        app->pending_transition == PLAYER_TRANSITION_NONE)
        (void)attempt_battery_save(app, true);
}

static bool push_key(player *app, Uint32 type, SDL_Scancode scancode, Uint64 timestamp) {
    SDL_Event event;
    SDL_zero(event);
    event.type = type;
    event.key.timestamp = timestamp;
    event.key.windowID = app->window != NULL ? SDL_GetWindowID(app->window) : 0;
    event.key.scancode = scancode;
    event.key.down = type == SDL_EVENT_KEY_DOWN;
    event.key.repeat = false;
    return SDL_PushEvent(&event);
}

static bool push_dialog_result(player *app, player_dialog_result_code code,
                               const char *path) {
    size_t path_length = 0;
    if (path != NULL) {
        while (path_length <= PLAYER_SESSION_PATH_LIMIT && path[path_length] != '\0')
            ++path_length;
        if (path_length > PLAYER_SESSION_PATH_LIMIT) return false;
    }
    const size_t allocation = sizeof(player_dialog_result) +
        (path != NULL ? path_length + 1u : 0u);
    player_dialog_result *result = malloc(allocation);
    if (result == NULL) return false;
    result->code = code;
    if (path != NULL) memcpy(result->path, path, path_length + 1u);
    SDL_Event event;
    SDL_zero(event);
    event.type = app->dialog_event_type;
    event.user.code = (Sint32)code;
    event.user.data1 = result;
    if (!SDL_PushEvent(&event)) {
        free(result);
        return false;
    }
    return true;
}

static bool verify_software_layout(int width, int height) {
    SDL_Surface *surface = SDL_CreateSurface(width, height, SDL_PIXELFORMAT_RGBA32);
    if (surface == NULL) {
        fprintf(stderr, "SDL_CreateSurface for layout check: %s\n", SDL_GetError());
        return false;
    }
    SDL_Renderer *renderer = SDL_CreateSoftwareRenderer(surface);
    if (renderer == NULL) {
        fprintf(stderr, "SDL_CreateSoftwareRenderer for layout check: %s\n", SDL_GetError());
        SDL_DestroySurface(surface);
        return false;
    }
    bool ok = SDL_SetRenderLogicalPresentation(renderer,
        (int)PLAYER_FRAME_WIDTH, (int)PLAYER_FRAME_HEIGHT,
        SDL_LOGICAL_PRESENTATION_INTEGER_SCALE);
    int output_width = 0;
    int output_height = 0;
    player_presentation_rect expected = {0, 0, 0, 0, 0};
    SDL_FRect actual = {-1.0f, -1.0f, -1.0f, -1.0f};
    if (ok) ok = SDL_GetRenderOutputSize(renderer, &output_width, &output_height);
    if (ok) ok = player_presentation_layout(output_width, output_height, &expected);
    if (ok) ok = SDL_GetRenderLogicalPresentationRect(renderer, &actual);
    if (ok) {
        const float scale = (float)expected.scale;
        const float logical_x = ((float)expected.x - actual.x) / scale;
        const float logical_y = ((float)expected.y - actual.y) / scale;
        ok = actual.w == (float)expected.width && actual.h == (float)expected.height &&
             actual.x + actual.w / 2.0f == (float)output_width / 2.0f &&
             actual.y + actual.h / 2.0f == (float)output_height / 2.0f &&
             actual.x + logical_x * scale == (float)expected.x &&
             actual.y + logical_y * scale == (float)expected.y;
        if (ok) {
            uint8_t rgba[160u * 144u * 4u];
            for (size_t pixel = 0; pixel < sizeof(rgba); pixel += 4u) {
                rgba[pixel] = 255;
                rgba[pixel + 1u] = 0;
                rgba[pixel + 2u] = 0;
                rgba[pixel + 3u] = 255;
            }
            SDL_Texture *texture = SDL_CreateTexture(renderer,
                SDL_PIXELFORMAT_RGBA32, SDL_TEXTUREACCESS_STATIC, 160, 144);
            SDL_FRect destination = {logical_x, logical_y, 160.0f, 144.0f};
            ok = texture != NULL &&
                 SDL_SetTextureScaleMode(texture, SDL_SCALEMODE_NEAREST) &&
                 SDL_UpdateTexture(texture, NULL, rgba, 160 * 4) &&
                 SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255) &&
                 SDL_RenderClear(renderer) &&
                 SDL_RenderTexture(renderer, texture, NULL, &destination) &&
                 SDL_RenderPresent(renderer) && SDL_LockSurface(surface);
            if (ok) {
                const int sample_y = expected.y + expected.height / 2;
                const uint8_t *row = (const uint8_t *)surface->pixels +
                    (size_t)sample_y * (size_t)surface->pitch;
                const size_t inside = (size_t)expected.x * 4u;
                ok = row[inside] == 255 && row[inside + 1u] == 0 &&
                     row[inside + 2u] == 0 && row[inside + 3u] == 255;
                if (ok && expected.x > 0)
                    ok = row[inside - 4u] == 0 && row[inside - 1u] == 255;
                const int right = expected.x + expected.width;
                if (ok && right < width) {
                    const size_t outside = (size_t)right * 4u;
                    ok = row[outside] == 0 && row[outside + 3u] == 255;
                }
                if (ok) {
                    const int sample_x = expected.x + expected.width / 2;
                    const size_t column = (size_t)sample_x * 4u;
                    const uint8_t *top = (const uint8_t *)surface->pixels +
                        (size_t)expected.y * (size_t)surface->pitch + column;
                    ok = top[0] == 255 && top[1] == 0 && top[2] == 0 && top[3] == 255;
                    if (ok && expected.y > 0) {
                        const uint8_t *above = top - surface->pitch;
                        ok = above[0] == 0 && above[3] == 255;
                    }
                    const int bottom_y = expected.y + expected.height;
                    if (ok && bottom_y < height) {
                        const uint8_t *below = (const uint8_t *)surface->pixels +
                            (size_t)bottom_y * (size_t)surface->pitch + column;
                        ok = below[0] == 0 && below[3] == 255;
                    }
                }
                SDL_UnlockSurface(surface);
            }
            if (texture != NULL) SDL_DestroyTexture(texture);
        }
    }
    if (!ok)
        fprintf(stderr,
            "SDL integer layout mismatch for %dx%d (output %dx%d, expected %d,%d %dx%d, actual %.2f,%.2f %.2fx%.2f): %s\n",
            width, height, output_width, output_height,
            expected.x, expected.y, expected.width, expected.height,
            actual.x, actual.y, actual.w, actual.h, SDL_GetError());
    SDL_DestroyRenderer(renderer);
    SDL_DestroySurface(surface);
    return ok;
}

static bool verify_software_layouts(void) {
    static const int sizes[][2] = {
        {160, 144}, {327, 299}, {400, 300}, {640, 576}
    };
    for (size_t i = 0; i < sizeof(sizes) / sizeof(sizes[0]); ++i)
        if (!verify_software_layout(sizes[i][0], sizes[i][1])) return false;
    return true;
}

static bool write_smoke_rom(char *out_path, size_t path_capacity,
                            player_save_identity *out_identity) {
    static const uint8_t program[] = {
        0x3E, 0x0A,             /* LD A,$0A: enable cartridge RAM */
        0xEA, 0x00, 0x00,       /* LD ($0000),A */
        0xFA, 0x00, 0xA0,       /* LD A,($A000) */
        0xFE, 0x5A,             /* CP $5A */
        0x28, 0x06,             /* JR Z,success */
        0x3E, 0x5A,             /* first process stores the marker */
        0xEA, 0x00, 0xA0,
        0x76,
        0x3E, 0x01,             /* resumed process reaches success */
        0xEA, 0x00, 0xC0,
        0x76
    };
    uint8_t rom[32768];
    memset(rom, 0, sizeof(rom));
    memcpy(rom + 0x100u, program, sizeof(program));
    rom[0x147u] = 0x03u;
    rom[0x148u] = 0x00u;
    rom[0x149u] = 0x02u;
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
    if (!player_session_identify_rom(rom, sizeof(rom), out_identity)) return false;

    char template_path[] = "/tmp/gabbaboy-battery-smoke-XXXXXX";
    const int fd = mkstemp(template_path);
    if (fd < 0) return false;
    size_t written = 0u;
    while (written < sizeof(rom)) {
        const ssize_t count = write(fd, rom + written, sizeof(rom) - written);
        if (count > 0) written += (size_t)count;
        else if (count < 0 && errno == EINTR) continue;
        else break;
    }
    const int close_result = close(fd);
    if (written != sizeof(rom) || close_result != 0 ||
        strlen(template_path) + 1u > path_capacity) {
        (void)unlink(template_path);
        return false;
    }
    memcpy(out_path, template_path, strlen(template_path) + 1u);
    return true;
}

static bool start_smoke_battery_session(player *app, const char *rom_path) {
    memset(app, 0, sizeof(*app));
    app->save_lock_fd = -1;
    app->running = true;
    app->window_focused = true;
    atomic_init(&app->dialog_callback_done, false);
    atomic_init(&app->dialog_delivery_failed, false);
    return create_machine(app, rom_path);
}

static bool run_smoke_battery_guest(player *app, bool expect_resume) {
    const gbb_run_result result = gbb_run(app->machine, 512u, NULL, 0u);
    if (result.reason != GBB_STOP_HALTED_IDLE) return false;
    return (gbb_peek_ram(app->machine, 0xC000u) == 1u) == expect_resume;
}

static void send_smoke_transition_key(player *app, SDL_Scancode scancode) {
    SDL_KeyboardEvent key;
    SDL_zero(key);
    key.timestamp = SDL_GetTicksNS();
    key.scancode = scancode;
    handle_key(app, &key, true);
}

static bool run_save_transition_smoke(void) {
    char rom_path[256];
    player_save_identity identity;
    if (!write_smoke_rom(rom_path, sizeof(rom_path), &identity)) return false;
    player_session_remove_battery_file(&identity);

    player session;
    bool ok = start_smoke_battery_session(&session, rom_path);
    if (ok) {
        const gbb_run_result result = gbb_run(session.machine, 512u, NULL, 0u);
        ok = result.reason == GBB_STOP_HALTED_IDLE &&
             session.save_identity.saved_generation == 0u;
    }
    if (ok) {
        session.save_identity.persistence_enabled = false;
        begin_transition(&session, PLAYER_TRANSITION_QUIT, NULL);
        ok = session.pending_transition == PLAYER_TRANSITION_QUIT &&
             session.save_status_active &&
             strstr(session.save_status, "R retry") != NULL &&
             strstr(session.save_status, "C continue without saving") != NULL &&
             strstr(session.save_status, "Esc cancel") != NULL;
    }
    if (ok) {
        send_smoke_transition_key(&session, SDL_SCANCODE_ESCAPE);
        ok = session.running &&
             session.pending_transition == PLAYER_TRANSITION_NONE &&
             session.save_status_active &&
             strstr(session.save_status, "Press S to retry") != NULL;
    }
    if (ok) {
        session.save_identity.persistence_enabled = false;
        begin_transition(&session, PLAYER_TRANSITION_QUIT, NULL);
        session.save_identity.persistence_enabled = true;
        send_smoke_transition_key(&session, SDL_SCANCODE_R);
        ok = !session.running &&
             session.pending_transition == PLAYER_TRANSITION_NONE &&
             !session.save_status_active;
    }
    session.skip_final_save = true;
    destroy_player(&session);

    if (ok) ok = start_smoke_battery_session(&session, rom_path) &&
                 run_smoke_battery_guest(&session, true);
    session.skip_final_save = true;
    destroy_player(&session);
    player_session_remove_battery_file(&identity);

    if (ok) ok = start_smoke_battery_session(&session, rom_path);
    if (ok) {
        const gbb_run_result result = gbb_run(session.machine, 512u, NULL, 0u);
        ok = result.reason == GBB_STOP_HALTED_IDLE;
    }
    if (ok) {
        session.save_identity.persistence_enabled = false;
        begin_transition(&session, PLAYER_TRANSITION_QUIT, NULL);
        ok = session.pending_transition == PLAYER_TRANSITION_QUIT &&
             session.save_status_active;
    }
    if (ok) {
        send_smoke_transition_key(&session, SDL_SCANCODE_C);
        ok = !session.running && session.skip_final_save &&
             session.pending_transition == PLAYER_TRANSITION_NONE;
    }
    session.skip_final_save = true;
    destroy_player(&session);

    if (ok) ok = start_smoke_battery_session(&session, rom_path) &&
                 run_smoke_battery_guest(&session, false);
    session.skip_final_save = true;
    destroy_player(&session);
    player_session_remove_battery_file(&identity);
    (void)unlink(rom_path);
    if (!ok) fputs("Battery transition retry/cancel/continue smoke failed\n", stderr);
    return ok;
}

static bool run_battery_smoke_guest(player *app, bool resume) {
    if (!app->save_identity.battery_backed ||
        !app->save_identity.persistence_enabled) return false;
    const gbb_run_result result = gbb_run(app->machine,
        PLAYER_BATTERY_SMOKE_HALF_DOTS, NULL, 0u);
    if (result.reason != GBB_STOP_HALTED_IDLE &&
        result.reason != GBB_STOP_BUDGET) {
        fprintf(stderr, "Battery smoke guest stopped with reason %d after %llu half-dots\n",
                (int)result.reason, (unsigned long long)result.consumed_half_dots);
        return false;
    }
    if (!resume) {
        if (app->save_identity.ram_size == 8192u &&
            gbb_peek_ram(app->machine, 0xC002u) == 0xE1u &&
            gbb_peek_ram(app->machine, 0xC000u) != 1u) {
            fputs("Battery fixture did not take its fresh-RAM branch\n", stderr);
            return false;
        }
        uint64_t generation = 0u;
        if (gbb_battery_generation(app->machine, &generation) != GBB_OK ||
            generation == 0u) {
            fputs("Battery smoke guest did not change cartridge RAM\n", stderr);
            return false;
        }
        char error[192];
        if (!player_session_save_battery(app->machine, &app->save_identity,
                                         error, sizeof(error))) {
            fprintf(stderr, "Battery smoke save failed: %s\n", error);
            return false;
        }
        return true;
    }
    const bool continuation_marker =
        gbb_peek_ram(app->machine, 0xC001u) == 0xA5u &&
        gbb_peek_ram(app->machine, 0xC004u) == 1u;
    const bool smoke_rom_marker = gbb_peek_ram(app->machine, 0xC000u) == 1u;
    if (!continuation_marker && !smoke_rom_marker) {
        fputs("Fresh-process guest did not take the persisted-byte success path\n", stderr);
        return false;
    }
    return true;
}

static bool run_battery_child(const char *executable, const char *mode,
                              const char *rom_path) {
    char *const arguments[] = {(char *)executable, (char *)mode,
                               (char *)rom_path, NULL};
    pid_t child = 0;
    const int spawn_result = posix_spawnp(&child, executable, NULL, NULL,
                                          arguments, environ);
    if (spawn_result != 0) {
        fputs("Could not launch the bounded battery smoke child\n", stderr);
        return false;
    }
    struct timespec started;
    if (clock_gettime(CLOCK_MONOTONIC, &started) != 0) {
        (void)kill(child, SIGKILL);
        (void)waitpid(child, NULL, 0);
        return false;
    }
    for (;;) {
        int status = 0;
        const pid_t waited = waitpid(child, &status, WNOHANG);
        if (waited == child) return WIFEXITED(status) && WEXITSTATUS(status) == 0;
        if (waited < 0 && errno != EINTR) return false;
        struct timespec now;
        if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) {
            (void)kill(child, SIGKILL);
            (void)waitpid(child, NULL, 0);
            return false;
        }
        const int64_t elapsed_ns =
            (int64_t)(now.tv_sec - started.tv_sec) * INT64_C(1000000000) +
            (int64_t)now.tv_nsec - (int64_t)started.tv_nsec;
        if (elapsed_ns >= INT64_C(5000000000)) {
            (void)kill(child, SIGKILL);
            (void)waitpid(child, NULL, 0);
            fputs("Battery smoke child exceeded its 5-second process bound\n", stderr);
            return false;
        }
        const struct timespec pause = {0, 10000000};
        while (nanosleep(&pause, NULL) != 0 && errno == EINTR) { }
    }
}

static bool identify_smoke_rom(const char *rom_path,
                               player_save_identity *out_identity) {
    gbb_instance *machine = NULL;
    char *owned_path = NULL;
    char error[192];
    const bool created = gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) == GBB_OK;
    const bool loaded = created && player_session_replace_rom(
        machine, &owned_path, rom_path, out_identity, error, sizeof(error));
    if (machine != NULL) gbb_destroy(machine);
    free(owned_path);
    return loaded && out_identity->battery_backed &&
           out_identity->ram_size == 8192u;
}

static bool run_battery_process_smoke(const char *executable,
                                      const char *fixture_rom_path) {
    char generated_rom_path[128];
    player_save_identity identity;
    const char *rom_path = fixture_rom_path;
    const bool generated_rom = fixture_rom_path == NULL;
    if (generated_rom) {
        if (!write_smoke_rom(generated_rom_path, sizeof(generated_rom_path),
                             &identity)) {
            fputs("Could not create the bounded battery smoke ROM\n", stderr);
            return false;
        }
        rom_path = generated_rom_path;
    } else if (!identify_smoke_rom(rom_path, &identity)) {
        fputs("Packaged battery fixture did not pass bounded cartridge validation\n",
              stderr);
        return false;
    }
    player_session_remove_battery_file(&identity);
    const bool stored = run_battery_child(executable, "--battery-smoke-store",
                                          rom_path);
    const bool resumed = stored && run_battery_child(
        executable, "--battery-smoke-resume", rom_path);
    player_session_remove_battery_file(&identity);
    if (generated_rom) (void)unlink(rom_path);
    if (!stored || !resumed) {
        fputs("Two-process battery continuation smoke failed\n", stderr);
        return false;
    }
    if (!generated_rom)
        puts("packaged MBC1 continuation fixture resumed in a fresh process");
    return true;
}

static bool run_smoke(player *app, const char *demo_rom_path,
                      const char *invalid_rom_path,
                      const char *executable,
                      const char *battery_fixture_path) {
    if (!verify_software_layouts()) return false;
    uint64_t press_ns, release_ns;
    if (!player_input_half_dots_to_nanoseconds(8, &press_ns) ||
        !player_input_half_dots_to_nanoseconds(50008, &release_ns) ||
        app->input.host_anchor_ns > UINT64_MAX - release_ns) {
        fputs("Could not construct finite smoke event timestamps\n", stderr);
        return false;
    }
    const uint64_t press_at = app->input.host_anchor_ns + press_ns;
    const uint64_t release_at = app->input.host_anchor_ns + release_ns;
    if (!push_key(app, SDL_EVENT_KEY_DOWN, SDL_SCANCODE_Z, press_at) ||
        !pump_events(app) ||
        !push_key(app, SDL_EVENT_KEY_UP, SDL_SCANCODE_Z, release_at) ||
        !pump_events(app)) return false;
    if (app->input.pending_count != 2 ||
        app->input.pending[0].at_half_dots != 8 ||
        app->input.pending[1].at_half_dots != 50008) {
        fputs("Injected SDL timestamps did not map to the expected guest half-dots\n", stderr);
        return false;
    }
    if (!advance_to(app, PLAYER_FRAME_HALF_DOTS, true) ||
        !update_frame(app, true) || !draw_frame(app)) return false;
    if (!run_pulse_audio_smoke(app, demo_rom_path)) return false;
    if (gbb_peek_ram(app->machine, 0xC000) != 1 ||
        gbb_peek_ram(app->machine, 0xC001) != 1) {
        fputs("Injected A transitions did not reach the visible demo guest results\n", stderr);
        return false;
    }
    char *const original_path = app->current_rom_path;
    app->dialog_pending = true;
    app->dialog_was_paused = false;
    player_input_pause(&app->input);
    if (!push_dialog_result(app, PLAYER_DIALOG_SELECTED, invalid_rom_path) ||
        !pump_events(app) || app->dialog_pending ||
        app->current_rom_path != original_path ||
        gbb_peek_ram(app->machine, 0xC000) != 1 ||
        gbb_peek_ram(app->machine, 0xC001) != 1) {
        fputs("Injected invalid ROM replacement did not preserve the active session\n", stderr);
        return false;
    }

    char busy_rom_path[256];
    player_save_identity busy_identity;
    if (!write_smoke_rom(busy_rom_path, sizeof(busy_rom_path),
                         &busy_identity)) {
        fputs("Could not create the synthetic lock-conflict ROM\n", stderr);
        return false;
    }
    int busy_lock_fd = -1;
    char lock_error[192];
    const player_session_lock_result lock_result = player_session_lock_battery(
        &busy_identity, &busy_lock_fd, lock_error, sizeof(lock_error));
    if (lock_result != PLAYER_SESSION_LOCK_ACQUIRED) {
        (void)unlink(busy_rom_path);
        fprintf(stderr, "Could not stage the synthetic lock conflict: %s\n",
                lock_error);
        return false;
    }
    gbb_instance *const machine_before_busy_replace = app->machine;
    char *const path_before_busy_replace = app->current_rom_path;
    app->dialog_pending = true;
    app->dialog_was_paused = false;
    player_input_pause(&app->input);
    const bool busy_replace_preserved =
        push_dialog_result(app, PLAYER_DIALOG_SELECTED, busy_rom_path) &&
        pump_events(app) && !app->dialog_pending &&
        app->machine == machine_before_busy_replace &&
        app->current_rom_path == path_before_busy_replace &&
        gbb_peek_ram(app->machine, 0xC000) == 1 &&
        strstr(app->status, "Another GabbaBoy process") != NULL;
    player_session_unlock_battery(&busy_lock_fd);
    player_session_remove_battery_file(&busy_identity);
    (void)unlink(busy_rom_path);
    if (!busy_replace_preserved) {
        fputs("Busy battery replacement did not preserve the active session\n",
              stderr);
        return false;
    }

    char *const path_before_success = app->current_rom_path;
    app->dialog_pending = true;
    app->dialog_was_paused = false;
    player_input_pause(&app->input);
    if (!push_dialog_result(app, PLAYER_DIALOG_SELECTED, demo_rom_path) ||
        !pump_events(app) || app->dialog_pending ||
        app->current_rom_path == path_before_success ||
        strcmp(app->current_rom_path, demo_rom_path) != 0 ||
        gbb_peek_ram(app->machine, 0xC000) != 0 ||
        gbb_peek_ram(app->machine, 0xC001) != 0 ||
        app->input.guest_cursor_half_dots != 0 || app->input.pending_count != 0) {
        fputs("Injected valid ROM replacement did not reset the guest session\n", stderr);
        return false;
    }
    if (!advance_to(app, PLAYER_FRAME_HALF_DOTS, true) ||
        !update_frame(app, true) || !draw_frame(app)) return false;

    if (!run_battery_process_smoke(executable, battery_fixture_path)) return false;
    if (!run_save_transition_smoke()) return false;

    printf("player smoke passed: frame=%llu; replacement lock conflict preserved the session; save retry, cancel, and continue choices passed\n",
           (unsigned long long)app->displayed_generation);
    return true;
}

static void destroy_player(player *app) {
    for (unsigned i = 0; i < PLAYER_INPUT_GAMEPAD_CAPACITY; ++i) {
        if (app->gamepads[i].handle != NULL)
            SDL_CloseGamepad(app->gamepads[i].handle);
        app->gamepads[i] = (player_gamepad){0};
    }
    if (app->machine != NULL && app->save_identity.battery_backed &&
        !app->skip_final_save) {
        if (!attempt_battery_save(app, false)) {
            fprintf(stderr, "Battery save failed at exit: %s\n",
                    app->save_status);
            app->save_flush_failed = true;
        }
    }
    if (app->texture != NULL) SDL_DestroyTexture(app->texture);
    if (app->renderer != NULL) SDL_DestroyRenderer(app->renderer);
    if (app->window != NULL) SDL_DestroyWindow(app->window);
    if (app->surface != NULL) SDL_DestroySurface(app->surface);
    if (app->machine != NULL) gbb_destroy(app->machine);
    player_session_unlock_battery(&app->save_lock_fd);
    player_audio_destroy(app->audio);
    free(app->current_rom_path);
    free(app->pending_rom_path);
    app->texture = NULL;
    app->renderer = NULL;
    app->window = NULL;
    app->surface = NULL;
    app->machine = NULL;
    app->current_rom_path = NULL;
    app->pending_rom_path = NULL;
}

int main(int argc, char **argv) {
    const bool smoke = argc >= 2 && strcmp(argv[1], "--smoke") == 0;
    const bool package_smoke = argc == 3 &&
                               strcmp(argv[1], "--smoke-package") == 0;
    const bool battery_store = argc == 3 &&
                               strcmp(argv[1], "--battery-smoke-store") == 0;
    const bool battery_resume = argc == 3 &&
                                strcmp(argv[1], "--battery-smoke-resume") == 0;
    const bool battery_smoke = battery_store || battery_resume;
    if ((smoke && argc != 2 && argc != 4) ||
        (package_smoke && argc != 3) ||
        (battery_smoke && argc != 3) ||
        (!smoke && !package_smoke && !battery_smoke && argc > 1)) {
        fprintf(stderr, "usage: %s [--smoke [demo-rom invalid-rom] | --smoke-package invalid-rom]\n",
                argv[0]);
        return 2;
    }
    const char *requested_demo_rom = battery_smoke ? argv[2] :
        (smoke && argc == 4 ? argv[2] : NULL);
    const char *invalid_rom = smoke && argc == 4 ? argv[3] :
        (package_smoke ? argv[2] : GABBABOY_PLAYER_INVALID_ROM);

    player app;
    memset(&app, 0, sizeof(app));
    app.save_lock_fd = -1;
    app.running = true;
    app.needs_redraw = true;
    app.window_focused = true;
    atomic_init(&app.dialog_callback_done, false);
    atomic_init(&app.dialog_delivery_failed, false);
    if (!SDL_Init((smoke || package_smoke || battery_smoke)
                      ? SDL_INIT_EVENTS | SDL_INIT_AUDIO
                      : SDL_INIT_VIDEO | SDL_INIT_AUDIO | SDL_INIT_GAMEPAD)) {
        fprintf(stderr, "SDL_Init: %s\n", SDL_GetError());
        return 1;
    }
    app.audio = player_audio_create();
    if (app.audio == NULL || !player_audio_available(app.audio)) {
        set_status(&app,
            "Audio unavailable; PCM is discarded and counted without a queue");
        fputs("Audio unavailable; PCM is discarded and counted without a queue\n",
              stderr);
    }
    char *demo_rom_path = resolve_demo_rom_path(requested_demo_rom,
                                                 package_smoke);
    if (demo_rom_path == NULL) {
        fputs("Could not resolve the packaged demo ROM\n", stderr);
        SDL_Quit();
        return 1;
    }
    char *battery_fixture_path = package_smoke
        ? packaged_battery_rom_path() : NULL;
    if (package_smoke && battery_fixture_path == NULL) {
        fputs("Could not resolve the packaged MBC1 continuation fixture\n", stderr);
        free(demo_rom_path);
        SDL_Quit();
        return 1;
    }
    if (!create_machine(&app, demo_rom_path)) {
        destroy_player(&app);
        free(battery_fixture_path);
        free(demo_rom_path);
        SDL_Quit();
        return 1;
    }
    app.dialog_event_type = SDL_RegisterEvents(1);
    if (app.dialog_event_type == (Uint32)-1) {
        fprintf(stderr, "SDL_RegisterEvents: %s\n", SDL_GetError());
        destroy_player(&app);
        free(battery_fixture_path);
        free(demo_rom_path);
        SDL_Quit();
        return 1;
    }
    if (battery_smoke) {
        const bool battery_passed = !app.save_flush_failed &&
            run_battery_smoke_guest(&app, battery_resume);
        if (!battery_passed && app.save_identity.battery_backed &&
            !app.save_identity.persistence_enabled)
            fputs("Battery smoke could not load a clean save state\n", stderr);
        destroy_player(&app);
        free(battery_fixture_path);
        free(demo_rom_path);
        SDL_Quit();
        return battery_passed && !app.save_flush_failed ? 0 : 1;
    }
    if (!create_video(&app, smoke || package_smoke)) {
        destroy_player(&app);
        free(battery_fixture_path);
        free(demo_rom_path);
        SDL_Quit();
        return 1;
    }
    player_input_reset(&app.input, SDL_GetTicksNS());
    if (app.status[0] == '\0') set_status(&app, "Ready");
    else update_window_title(&app);

    bool passed = true;
    if (smoke || package_smoke) {
        passed = run_smoke(&app, demo_rom_path, invalid_rom, argv[0],
                           battery_fixture_path);
    } else {
        while (app.running) {
            if (!pump_events(&app)) { passed = false; break; }
            if (!app.running) break;
            uint64_t target_half_dots;
            if (!app.input.paused &&
                !player_input_guest_target(&app.input, SDL_GetTicksNS(),
                                           &target_half_dots)) {
                player_input_pause(&app.input);
                fputs("Input paused because the host clock exceeds the guest timeline.\n",
                      stderr);
            }
            if (!app.input.paused) {
                const uint64_t cursor = app.input.guest_cursor_half_dots;
                const uint64_t bounded_target = cursor >
                    UINT64_MAX - PLAYER_FRAME_HALF_DOTS
                    ? UINT64_MAX : cursor + PLAYER_FRAME_HALF_DOTS;
                if (target_half_dots > bounded_target)
                    target_half_dots = bounded_target;
                if (!advance_to(&app, target_half_dots, false)) {
                    passed = false;
                    break;
                }
                if (app.input.release_pending_buttons != 0u) {
                    const gbb_error retried = player_input_retry_focus_releases(
                        &app.input, app.machine, SDL_GetTicksNS());
                    if (retried != GBB_OK && retried != GBB_EVENT_QUEUE_FULL) {
                        player_input_pause(&app.input);
                        app.user_paused = true;
                        set_status(&app, "Input paused while a release could not be queued");
                    }
                }
            }
            update_battery_save(&app);
            if (!update_frame(&app, false) ||
                (app.needs_redraw && !draw_frame(&app))) {
                passed = false;
                break;
            }
            SDL_Delay(1);
        }
    }
    destroy_player(&app);
    free(battery_fixture_path);
    free(demo_rom_path);
    SDL_Quit();
    return passed && !app.save_flush_failed ? 0 : 1;
}
