#include "input.h"
#include "presentation.h"
#include "session.h"

#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PLAYER_FRAME_WIDTH 160u
#define PLAYER_FRAME_HEIGHT 144u
#define PLAYER_FRAME_HALF_DOTS UINT64_C(140448)
#define PLAYER_MAX_OPERATION_HALF_DOTS UINT64_C(40)
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

typedef struct {
    gbb_instance *machine;
    player_input_state input;
    SDL_Window *window;
    SDL_Surface *surface;
    SDL_Renderer *renderer;
    SDL_Texture *texture;
    SDL_FRect frame_destination;
    char *current_rom_path;
    char status[192];
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
} player;

static bool create_machine(player *app) {
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &app->machine) != GBB_OK) {
        fputs("Could not create the DMG-CPU-B machine\n", stderr);
        return false;
    }
    char error[192];
    if (!player_session_replace_rom(app->machine, &app->current_rom_path,
                                    GABBABOY_PLAYER_DEMO_ROM,
                                    error, sizeof(error))) {
        fprintf(stderr, "Could not load the owned demo ROM: %s\n", error);
        return false;
    }
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
        const gbb_run_result result = gbb_run(app->machine, budget, NULL, 0);
        if (result.consumed_half_dots >
            UINT64_MAX - app->input.guest_cursor_half_dots) {
            fputs("Guest timeline overflow\n", stderr);
            return false;
        }
        player_input_reconcile(&app->input,
            app->input.guest_cursor_half_dots + result.consumed_half_dots);
        if (result.reason != GBB_STOP_BUDGET) {
            fprintf(stderr, "Guest stopped at half-dot %llu (reason %d)\n",
                    (unsigned long long)app->input.guest_cursor_half_dots,
                    (int)result.reason);
            return false;
        }
        if (result.consumed_half_dots == 0) return !finish_target;
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
        "GabbaBoy | %s | %s | %s | \xe2\x8c\x98O Open, \xe2\x8c\x98Q Quit, F1 Help | Audio/saves unavailable",
        short_name, app->user_paused || app->input.paused ? "Paused" : "Running",
        app->status[0] == '\0' ? "Ready" : app->status);
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
        "Pause / resume: Space\nReset current ROM: R\n\n"
        "Status: %.160s\n"
        "Audio and battery-save persistence are not implemented.",
        rom_basename(app->current_rom_path), app->status[0] == '\0' ? "Ready" : app->status);
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
    set_status(app, "Current ROM reset");
}

static bool replace_session_rom(player *app, const char *path) {
    char error[192];
    if (!player_session_replace_rom(app->machine, &app->current_rom_path,
                                    path, error, sizeof(error))) {
        set_status(app, error);
        return false;
    }
    app->user_paused = app->dialog_was_paused;
    player_input_reset(&app->input, SDL_GetTicksNS());
    if (app->user_paused || !app->window_focused || app->dialog_pending)
        player_input_pause(&app->input);
    app->displayed_generation = 0;
    app->needs_redraw = true;
    set_status(app, "ROM loaded; input and display state reset");
    return true;
}

static void finish_dialog(player *app, player_dialog_result *result) {
    app->dialog_pending = false;
    switch (result->code) {
    case PLAYER_DIALOG_SELECTED:
        (void)replace_session_rom(app, result->path);
        break;
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
    if (app->quit_after_dialog) app->running = false;
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
        ? "Choose one 32 KiB ROM-only image"
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
    else app->running = false;
}

static void handle_key(player *app, const SDL_KeyboardEvent *key, bool pressed) {
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
        if (!app->dialog_pending && key->scancode == SDL_SCANCODE_R) {
            reset_session(app);
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
        const gbb_error result = player_input_retry_focus_releases(
            &app->input, app->machine, event->window.timestamp);
        if (result != GBB_OK) {
            app->user_paused = true;
            set_status(app, "Input remains paused until held-button releases are admitted");
        } else if (!app->dialog_pending) {
            if (!app->user_paused &&
                !player_input_resume(&app->input, SDL_GetTicksNS())) {
                app->user_paused = true;
                set_status(app, "Input remains paused until held-button releases are admitted");
            } else {
                set_status(app, app->user_paused
                    ? "Focus returned; paused by user" : "Running");
            }
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
        if (app->quit_after_dialog) app->running = false;
    }
    return true;
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

static bool run_smoke(player *app) {
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
    if (gbb_peek_ram(app->machine, 0xC000) != 1 ||
        gbb_peek_ram(app->machine, 0xC001) != 1) {
        fputs("Injected A transitions did not reach the visible demo guest results\n", stderr);
        return false;
    }
    char *const original_path = app->current_rom_path;
    app->dialog_pending = true;
    app->dialog_was_paused = false;
    player_input_pause(&app->input);
    if (!push_dialog_result(app, PLAYER_DIALOG_SELECTED, GABBABOY_PLAYER_INVALID_ROM) ||
        !pump_events(app) || app->dialog_pending ||
        app->current_rom_path != original_path ||
        gbb_peek_ram(app->machine, 0xC000) != 1 ||
        gbb_peek_ram(app->machine, 0xC001) != 1) {
        fputs("Injected invalid ROM replacement did not preserve the active session\n", stderr);
        return false;
    }

    char *const path_before_success = app->current_rom_path;
    app->dialog_pending = true;
    app->dialog_was_paused = false;
    player_input_pause(&app->input);
    if (!push_dialog_result(app, PLAYER_DIALOG_SELECTED, GABBABOY_PLAYER_DEMO_ROM) ||
        !pump_events(app) || app->dialog_pending ||
        app->current_rom_path == path_before_success ||
        strcmp(app->current_rom_path, GABBABOY_PLAYER_DEMO_ROM) != 0 ||
        gbb_peek_ram(app->machine, 0xC000) != 0 ||
        gbb_peek_ram(app->machine, 0xC001) != 0 ||
        app->input.guest_cursor_half_dots != 0 || app->input.pending_count != 0) {
        fputs("Injected valid ROM replacement did not reset the guest session\n", stderr);
        return false;
    }
    if (!advance_to(app, PLAYER_FRAME_HALF_DOTS, true) ||
        !update_frame(app, true) || !draw_frame(app)) return false;

    printf("player smoke passed: frame=%llu; failed replacement preserved the session and successful replacement reset it\n",
           (unsigned long long)app->displayed_generation);
    return true;
}

static void destroy_player(player *app) {
    if (app->texture != NULL) SDL_DestroyTexture(app->texture);
    if (app->renderer != NULL) SDL_DestroyRenderer(app->renderer);
    if (app->window != NULL) SDL_DestroyWindow(app->window);
    if (app->surface != NULL) SDL_DestroySurface(app->surface);
    if (app->machine != NULL) gbb_destroy(app->machine);
    free(app->current_rom_path);
}

int main(int argc, char **argv) {
    const bool smoke = argc == 2 && strcmp(argv[1], "--smoke") == 0;
    if (argc > 2 || (argc == 2 && !smoke)) {
        fprintf(stderr, "usage: %s [--smoke]\n", argv[0]);
        return 2;
    }

    player app;
    memset(&app, 0, sizeof(app));
    app.running = true;
    app.needs_redraw = true;
    app.window_focused = true;
    atomic_init(&app.dialog_callback_done, false);
    atomic_init(&app.dialog_delivery_failed, false);
    if (!create_machine(&app)) {
        destroy_player(&app);
        return 1;
    }
    if (!SDL_Init(smoke ? SDL_INIT_EVENTS : SDL_INIT_VIDEO)) {
        fprintf(stderr, "SDL_Init: %s\n", SDL_GetError());
        destroy_player(&app);
        return 1;
    }
    app.dialog_event_type = SDL_RegisterEvents(1);
    if (app.dialog_event_type == (Uint32)-1) {
        fprintf(stderr, "SDL_RegisterEvents: %s\n", SDL_GetError());
        destroy_player(&app);
        SDL_Quit();
        return 1;
    }
    if (!create_video(&app, smoke)) {
        destroy_player(&app);
        SDL_Quit();
        return 1;
    }
    player_input_reset(&app.input, SDL_GetTicksNS());
    set_status(&app, "Ready");

    bool passed = true;
    if (smoke) {
        passed = run_smoke(&app);
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
            }
            if (!update_frame(&app, false) ||
                (app.needs_redraw && !draw_frame(&app))) {
                passed = false;
                break;
            }
            SDL_Delay(1);
        }
    }
    destroy_player(&app);
    SDL_Quit();
    return passed ? 0 : 1;
}
