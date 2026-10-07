#include "input.h"

#include <errno.h>
#include <stdio.h>
#include <string.h>

#define PLAYER_FRAME_WIDTH 160u
#define PLAYER_FRAME_HEIGHT 144u
#define PLAYER_FRAME_HALF_DOTS UINT64_C(140448)
#define PLAYER_MAX_OPERATION_HALF_DOTS UINT64_C(40)
#define PLAYER_ROM_SIZE 32768u

typedef struct {
    gbb_instance *machine;
    player_input_state input;
    SDL_Window *window;
    SDL_Surface *surface;
    SDL_Renderer *renderer;
    SDL_Texture *texture;
    uint64_t cursor_half_dots;
    uint64_t displayed_generation;
    bool running;
} player;

static bool read_demo(uint8_t rom[PLAYER_ROM_SIZE]) {
    FILE *file = fopen(GABBABOY_PLAYER_DEMO_ROM, "rb");
    if (file == NULL) {
        fprintf(stderr, "Could not open owned demo ROM: %s\n", strerror(errno));
        return false;
    }
    const size_t count = fread(rom, 1, PLAYER_ROM_SIZE, file);
    const int extra = fgetc(file);
    const bool failed = ferror(file) != 0;
    if (fclose(file) != 0 || failed || count != PLAYER_ROM_SIZE || extra != EOF) {
        fprintf(stderr, "Owned demo ROM must be exactly %u bytes\n", PLAYER_ROM_SIZE);
        return false;
    }
    return true;
}

static bool create_machine(player *app) {
    uint8_t rom[PLAYER_ROM_SIZE];
    if (!read_demo(rom)) return false;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &app->machine) != GBB_OK) {
        fputs("Could not create the DMG-CPU-B machine\n", stderr);
        return false;
    }
    const gbb_error load_result = gbb_load_rom(app->machine, rom, sizeof(rom));
    if (load_result != GBB_OK) {
        fprintf(stderr, "Could not load the owned demo ROM (error %d)\n", (int)load_result);
        return false;
    }
    player_input_reset(&app->input);
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
                                       (int)(PLAYER_FRAME_WIDTH * 2u),
                                       (int)(PLAYER_FRAME_HEIGHT * 2u), 0);
        if (app->window == NULL) {
            fprintf(stderr, "SDL_CreateWindow: %s\n", SDL_GetError());
            return false;
        }
        app->renderer = SDL_CreateRenderer(app->window, NULL);
        if (app->renderer == NULL) {
            fprintf(stderr, "SDL_CreateRenderer: %s\n", SDL_GetError());
            return false;
        }
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

static bool advance_to(player *app, uint64_t target_half_dots) {
    while (app->cursor_half_dots < target_half_dots) {
        const uint64_t remaining = target_half_dots - app->cursor_half_dots;
        const uint64_t budget = remaining > UINT64_MAX - PLAYER_MAX_OPERATION_HALF_DOTS
            ? remaining : remaining + PLAYER_MAX_OPERATION_HALF_DOTS;
        const gbb_run_result result = gbb_run(app->machine, budget, NULL, 0);
        app->cursor_half_dots += result.consumed_half_dots;
        if (result.reason != GBB_STOP_BUDGET || result.consumed_half_dots == 0) {
            fprintf(stderr, "Guest stopped at half-dot %llu (reason %d)\n",
                    (unsigned long long)app->cursor_half_dots, (int)result.reason);
            return false;
        }
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
    return true;
}

static bool draw_frame(player *app) {
    if (!SDL_SetRenderDrawColor(app->renderer, 8, 24, 32, 255) ||
        !SDL_RenderClear(app->renderer)) {
        fprintf(stderr, "SDL render clear: %s\n", SDL_GetError());
        return false;
    }
    if (app->displayed_generation != 0 &&
        !SDL_RenderTexture(app->renderer, app->texture, NULL, NULL)) {
        fprintf(stderr, "SDL_RenderTexture: %s\n", SDL_GetError());
        return false;
    }
    if (!SDL_RenderPresent(app->renderer)) {
        fprintf(stderr, "SDL_RenderPresent: %s\n", SDL_GetError());
        return false;
    }
    return true;
}

static bool handle_event(player *app, const SDL_Event *event) {
    if (event->type == SDL_EVENT_QUIT || event->type == SDL_EVENT_WINDOW_CLOSE_REQUESTED) {
        app->running = false;
        return true;
    }
    if (event->type == SDL_EVENT_KEY_DOWN || event->type == SDL_EVENT_KEY_UP) {
        const bool pressed = event->type == SDL_EVENT_KEY_DOWN;
        const gbb_error result = player_input_key(&app->input, app->machine,
                                                  app->cursor_half_dots,
                                                  event->key.scancode, pressed,
                                                  pressed && event->key.repeat);
        if (result != GBB_OK) {
            fprintf(stderr, "Could not queue keyboard input (error %d)\n", (int)result);
            return false;
        }
    }
    return true;
}

static bool pump_events(player *app) {
    SDL_Event event;
    while (SDL_PollEvent(&event)) {
        if (!handle_event(app, &event)) return false;
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

static bool run_smoke(player *app) {
    if (!push_key(app, SDL_EVENT_KEY_DOWN, SDL_SCANCODE_Z, 1) || !pump_events(app) ||
        !advance_to(app, PLAYER_FRAME_HALF_DOTS) || !update_frame(app, true) ||
        !draw_frame(app)) return false;
    if (gbb_peek_ram(app->machine, 0xC000) != 1) {
        fputs("Injected A press did not reach the visible demo guest result\n", stderr);
        return false;
    }
    if (!push_key(app, SDL_EVENT_KEY_UP, SDL_SCANCODE_Z, 2) || !pump_events(app) ||
        !advance_to(app, PLAYER_FRAME_HALF_DOTS * 2u) || !update_frame(app, true) ||
        !draw_frame(app)) return false;
    if (gbb_peek_ram(app->machine, 0xC001) != 1) {
        fputs("Injected A release did not reach the visible demo guest result\n", stderr);
        return false;
    }
    printf("player smoke passed: frame=%llu A-press=%u A-release=%u\n",
           (unsigned long long)app->displayed_generation,
           (unsigned)gbb_peek_ram(app->machine, 0xC000),
           (unsigned)gbb_peek_ram(app->machine, 0xC001));
    return true;
}

static void destroy_player(player *app) {
    if (app->texture != NULL) SDL_DestroyTexture(app->texture);
    if (app->renderer != NULL) SDL_DestroyRenderer(app->renderer);
    if (app->window != NULL) SDL_DestroyWindow(app->window);
    if (app->surface != NULL) SDL_DestroySurface(app->surface);
    if (app->machine != NULL) gbb_destroy(app->machine);
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
    if (!create_machine(&app)) {
        destroy_player(&app);
        return 1;
    }
    if (!SDL_Init(smoke ? SDL_INIT_EVENTS : SDL_INIT_VIDEO)) {
        fprintf(stderr, "SDL_Init: %s\n", SDL_GetError());
        destroy_player(&app);
        return 1;
    }
    if (!create_video(&app, smoke)) {
        destroy_player(&app);
        SDL_Quit();
        return 1;
    }

    bool passed = true;
    if (smoke) {
        passed = run_smoke(&app);
    } else {
        while (app.running) {
            if (!pump_events(&app)) { passed = false; break; }
            if (!advance_to(&app, app.cursor_half_dots + PLAYER_FRAME_HALF_DOTS) ||
                !update_frame(&app, false) || !draw_frame(&app)) {
                passed = false;
                break;
            }
            SDL_Delay(16);
        }
    }
    destroy_player(&app);
    SDL_Quit();
    return passed ? 0 : 1;
}
