#include "input.h"

#include <stdio.h>
#include <string.h>

static const char *active_case = "unknown";
#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

static gbb_instance *create_empty_machine(void) {
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK) return NULL;
    return machine;
}

static gbb_instance *load_demo(const char *path) {
    uint8_t rom[32768];
    FILE *file = fopen(path, "rb");
    if (file == NULL) return NULL;
    const size_t count = fread(rom, 1, sizeof(rom), file);
    const int extra = fgetc(file);
    const bool failed = ferror(file) != 0;
    if (fclose(file) != 0 || failed || count != sizeof(rom) || extra != EOF)
        return NULL;
    gbb_instance *machine = create_empty_machine();
    if (machine == NULL || gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) {
        gbb_destroy(machine);
        return NULL;
    }
    return machine;
}

static int player_input_time(const char *demo_path) {
    uint64_t value = UINT64_MAX;
    REQUIRE(player_input_nanoseconds_to_half_dots(0, &value) && value == 0);
    REQUIRE(player_input_nanoseconds_to_half_dots(1, &value) && value == 0);
    REQUIRE(player_input_nanoseconds_to_half_dots(125000000, &value) &&
            value == UINT64_C(1048576));
    REQUIRE(player_input_nanoseconds_to_half_dots(1000000000, &value) &&
            value == PLAYER_DMG_HALF_DOT_RATE_HZ);
    REQUIRE(player_input_nanoseconds_to_half_dots(1999999999, &value) &&
            value == PLAYER_DMG_HALF_DOT_RATE_HZ * 2u - 1u);
    REQUIRE(!player_input_nanoseconds_to_half_dots(0, NULL));

    REQUIRE(player_input_half_dots_to_nanoseconds(1, &value) && value == 120);
    REQUIRE(player_input_half_dots_to_nanoseconds(8, &value) && value == 954);
    REQUIRE(player_input_nanoseconds_to_half_dots(value, &value) && value == 8);
    REQUIRE(player_input_half_dots_to_nanoseconds(
                PLAYER_DMG_HALF_DOT_RATE_HZ, &value) && value == 1000000000);
    REQUIRE(!player_input_half_dots_to_nanoseconds(UINT64_MAX, &value));

    player_input_state state;
    player_input_reset(&state, 10000000000u);
    state.guest_anchor_half_dots = 100;
    state.guest_cursor_half_dots = 100;
    uint64_t target = 0;
    REQUIRE(player_input_guest_target(&state, 10125000000u, &target));
    REQUIRE(target == 100u + UINT64_C(1048576));
    player_input_reconcile(&state, 2000000);
    REQUIRE(player_input_guest_target(&state, 10125000000u, &target));
    REQUIRE(target == 2000000);

    state.guest_anchor_half_dots = UINT64_MAX - 1u;
    state.guest_cursor_half_dots = UINT64_MAX - 1u;
    REQUIRE(!player_input_guest_target(&state, 10000001200u, &target));

    gbb_instance *machine = load_demo(demo_path);
    REQUIRE(machine != NULL);
    player_input_reset(&state, 1000);
    REQUIRE(player_input_key(&state, machine, 2000, SDL_SCANCODE_Z, true, false) == GBB_OK);
    REQUIRE(state.pending_count == 1 && state.held_buttons == (1u << GBB_BUTTON_A));
    player_input_pause(&state);
    REQUIRE(player_input_key(&state, machine, 3000, SDL_SCANCODE_X, true, false) == GBB_OK);
    REQUIRE(state.pending_count == 1 && state.held_buttons == (1u << GBB_BUTTON_A));
    player_input_reconcile(&state, 500);
    REQUIRE(player_input_resume(&state, 10000000000u));
    REQUIRE(player_input_guest_target(&state, 10125000000u, &target));
    REQUIRE(target == 500u + UINT64_C(1048576));

    REQUIRE(gbb_reset(machine) == GBB_OK);
    player_input_reset(&state, 9000);
    REQUIRE(state.host_anchor_ns == 9000 && state.guest_anchor_half_dots == 0 &&
            state.guest_cursor_half_dots == 0 && state.pending_count == 0 &&
            state.held_buttons == 0 && state.release_pending_buttons == 0 &&
            !state.paused);
    const gbb_run_result reset_run = gbb_run(machine, 140448, NULL, 0);
    REQUIRE(reset_run.reason == GBB_STOP_BUDGET && reset_run.consumed_half_dots > 0);
    REQUIRE(gbb_peek_ram(machine, 0xC000) == 0);
    gbb_destroy(machine);
    return 0;
}

static int player_input_events(const char *demo_path) {
    static const SDL_Scancode keys[PLAYER_INPUT_BUTTON_COUNT] = {
        SDL_SCANCODE_RIGHT, SDL_SCANCODE_LEFT, SDL_SCANCODE_UP, SDL_SCANCODE_DOWN,
        SDL_SCANCODE_Z, SDL_SCANCODE_X, SDL_SCANCODE_RSHIFT, SDL_SCANCODE_RETURN
    };
    gbb_instance *machine = load_demo(demo_path);
    REQUIRE(machine != NULL);
    player_input_state state;
    player_input_reset(&state, 1000000000u);
    for (unsigned button = 0; button < PLAYER_INPUT_BUTTON_COUNT; ++button)
        REQUIRE(player_input_key(&state, machine, 1000000000u, keys[button],
                                true, false) == GBB_OK);
    REQUIRE(state.pending_count == PLAYER_INPUT_BUTTON_COUNT);
    REQUIRE(state.held_buttons == 0xffu);
    for (unsigned button = 0; button < PLAYER_INPUT_BUTTON_COUNT; ++button) {
        REQUIRE(state.pending[button].at_half_dots == 0);
        REQUIRE(state.pending[button].kind == GBB_INPUT_BUTTON_PRESS);
        REQUIRE(state.pending[button].value == button);
    }

    REQUIRE(player_input_key(&state, machine, 1000000000u, SDL_SCANCODE_Z,
                             true, true) == GBB_OK);
    REQUIRE(player_input_key(&state, machine, 1000000000u, SDL_SCANCODE_Z,
                             true, false) == GBB_OK);
    REQUIRE(player_input_key(&state, machine, 1000000000u, SDL_SCANCODE_F1,
                             true, false) == GBB_OK);
    REQUIRE(state.pending_count == PLAYER_INPUT_BUTTON_COUNT);

    const gbb_run_result run = gbb_run(machine, 120, NULL, 0);
    REQUIRE(run.consumed_half_dots > 0 && run.reason == GBB_STOP_BUDGET);
    player_input_reconcile(&state, run.consumed_half_dots);
    REQUIRE(state.pending_count == 0 && state.held_buttons == 0xffu);
    REQUIRE(player_input_key(&state, machine, 999999999u, SDL_SCANCODE_RIGHT,
                             false, false) == GBB_OK);
    REQUIRE(player_input_key(&state, machine, 1000000000u, SDL_SCANCODE_LEFT,
                             false, false) == GBB_OK);
    REQUIRE(state.pending_count == 2);
    REQUIRE(state.pending[0].at_half_dots == run.consumed_half_dots &&
            state.pending[0].value == GBB_BUTTON_RIGHT &&
            state.pending[0].kind == GBB_INPUT_BUTTON_RELEASE);
    REQUIRE(state.pending[1].at_half_dots == run.consumed_half_dots &&
            state.pending[1].value == GBB_BUTTON_LEFT &&
            state.pending[1].kind == GBB_INPUT_BUTTON_RELEASE);

    state.guest_anchor_half_dots = UINT64_MAX - 1u;
    state.guest_cursor_half_dots = UINT64_MAX - 1u;
    REQUIRE(player_input_key(&state, machine, 1000001200u, SDL_SCANCODE_RIGHT,
                             true, false) == GBB_INVALID_EVENT);
    REQUIRE(state.pending_count == 2 && state.held_buttons == 0xfcu);

    gbb_destroy(machine);
    return 0;
}

static int player_input_focus(const char *demo_path) {
    static const SDL_Scancode keys[PLAYER_INPUT_BUTTON_COUNT] = {
        SDL_SCANCODE_RIGHT, SDL_SCANCODE_LEFT, SDL_SCANCODE_UP, SDL_SCANCODE_DOWN,
        SDL_SCANCODE_Z, SDL_SCANCODE_X, SDL_SCANCODE_RSHIFT, SDL_SCANCODE_RETURN
    };
    gbb_instance *machine = create_empty_machine();
    REQUIRE(machine != NULL);
    player_input_state state;
    player_input_reset(&state, 5000000000u);
    for (unsigned button = 0; button < PLAYER_INPUT_BUTTON_COUNT; ++button)
        REQUIRE(player_input_key(&state, machine, 5000000000u, keys[button],
                                true, false) == GBB_OK);
    for (unsigned event = 0; event < 48; ++event)
        REQUIRE(player_input_key(&state, machine,
                                5000000000u + (uint64_t)(event + 1u) * 954u,
                                SDL_SCANCODE_RIGHT, (event & 1u) != 0,
                                false) == GBB_OK);
    REQUIRE(state.pending_count == PLAYER_INPUT_NORMAL_CAPACITY);
    REQUIRE(state.held_buttons == 0xffu);
    REQUIRE(player_input_key(&state, machine, 5000100000u, SDL_SCANCODE_Z,
                             false, false) == GBB_EVENT_QUEUE_FULL);
    REQUIRE(state.pending_count == PLAYER_INPUT_NORMAL_CAPACITY &&
            state.held_buttons == 0xffu);

    REQUIRE(player_input_focus_lost(&state, machine, 5000200000u) == GBB_OK);
    REQUIRE(state.paused && state.pending_count == PLAYER_INPUT_QUEUE_CAPACITY);
    REQUIRE(state.held_buttons == 0 && state.release_pending_buttons == 0);
    for (unsigned button = 0; button < PLAYER_INPUT_BUTTON_COUNT; ++button) {
        const gbb_input_event *event = &state.pending[PLAYER_INPUT_NORMAL_CAPACITY + button];
        REQUIRE(event->kind == GBB_INPUT_BUTTON_RELEASE && event->value == button);
    }
    REQUIRE(player_input_key(&state, machine, 5000300000u, SDL_SCANCODE_Z,
                             true, false) == GBB_OK);
    REQUIRE(state.pending_count == PLAYER_INPUT_QUEUE_CAPACITY && state.held_buttons == 0);
    REQUIRE(player_input_resume(&state, 5000400000u));
    REQUIRE(!state.paused);
    gbb_destroy(machine);

    machine = load_demo(demo_path);
    REQUIRE(machine != NULL);
    player_input_reset(&state, 0);
    REQUIRE(player_input_key(&state, machine, 0, SDL_SCANCODE_Z, true, false) == GBB_OK);
    gbb_input_event fill[PLAYER_INPUT_QUEUE_CAPACITY - 1u];
    for (size_t i = 0; i < sizeof(fill) / sizeof(fill[0]); ++i)
        fill[i] = (gbb_input_event){0, GBB_INPUT_STOP_WAKE, 1};
    REQUIRE(gbb_queue_events(machine, fill,
                             sizeof(fill) / sizeof(fill[0])) == GBB_OK);
    REQUIRE(player_input_focus_lost(&state, machine, 0) == GBB_EVENT_QUEUE_FULL);
    REQUIRE(state.paused && state.release_pending_buttons ==
            (1u << GBB_BUTTON_A) && state.held_buttons == (1u << GBB_BUTTON_A));
    REQUIRE(!player_input_resume(&state, 1000));

    const gbb_run_result run = gbb_run(machine, 200, NULL, 0);
    REQUIRE(run.consumed_half_dots > 0 && run.reason == GBB_STOP_BUDGET);
    player_input_reconcile(&state, run.consumed_half_dots);
    REQUIRE(player_input_retry_focus_releases(&state, machine, 0) == GBB_OK);
    REQUIRE(state.paused && state.release_pending_buttons == 0 &&
            state.held_buttons == 0 && state.pending_count == 1);
    REQUIRE(state.pending[0].kind == GBB_INPUT_BUTTON_RELEASE &&
            state.pending[0].value == GBB_BUTTON_A &&
            state.pending[0].at_half_dots == state.guest_cursor_half_dots);
    REQUIRE(player_input_resume(&state, 1000000));
    REQUIRE(!state.paused && state.host_anchor_ns == 1000000 &&
            state.guest_anchor_half_dots == state.guest_cursor_half_dots);
    gbb_destroy(machine);
    return 0;
}

static int player_input_sources(const char *demo_path) {
    gbb_instance *machine = load_demo(demo_path);
    REQUIRE(machine != NULL);
    player_input_state state;
    player_input_reset(&state, 1000u);
    REQUIRE(player_input_gamepad_added(&state, 11u));
    REQUIRE(player_input_gamepad_added(&state, 22u));
    REQUIRE(player_input_key(&state, machine, 1000u, SDL_SCANCODE_Z,
                            true, false) == GBB_OK);
    REQUIRE(player_input_gamepad_button(&state, machine, 1000u, 11u,
            SDL_GAMEPAD_BUTTON_SOUTH, true) == GBB_OK);
    REQUIRE(player_input_gamepad_button(&state, machine, 1000u, 11u,
            SDL_GAMEPAD_BUTTON_DPAD_RIGHT, true) == GBB_OK);
    REQUIRE(player_input_gamepad_button(&state, machine, 1000u, 22u,
            SDL_GAMEPAD_BUTTON_DPAD_DOWN, true) == GBB_OK);
    REQUIRE(state.held_buttons == ((1u << GBB_BUTTON_A) |
            (1u << GBB_BUTTON_RIGHT) | (1u << GBB_BUTTON_DOWN)));
    REQUIRE(player_input_gamepad_removed(&state, machine, 1000u, 11u) == GBB_OK);
    REQUIRE(state.held_buttons == ((1u << GBB_BUTTON_A) |
            (1u << GBB_BUTTON_DOWN)));
    REQUIRE(state.pending_count == 4u);
    REQUIRE(state.pending[3].kind == GBB_INPUT_BUTTON_RELEASE &&
            state.pending[3].value == GBB_BUTTON_RIGHT);
    REQUIRE(player_input_key(&state, machine, 1000u, SDL_SCANCODE_Z,
                            false, false) == GBB_OK);
    REQUIRE(state.held_buttons == (1u << GBB_BUTTON_DOWN));
    REQUIRE(player_input_gamepad_removed(&state, machine, 1000u, 22u) == GBB_OK);
    REQUIRE(state.held_buttons == 0u);
    gbb_destroy(machine);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 3) return 2;
    active_case = argv[1];
    puts("TAP version 13");
    puts("1..1");
    fflush(stdout);
    int result = 2;
    if (strcmp(active_case, "player_input_time") == 0)
        result = player_input_time(argv[2]);
    else if (strcmp(active_case, "player_input_events") == 0)
        result = player_input_events(argv[2]);
    else if (strcmp(active_case, "player_input_focus") == 0)
        result = player_input_focus(argv[2]);
    else if (strcmp(active_case, "player_input_sources") == 0)
        result = player_input_sources(argv[2]);
    printf("%s 1 - %s\n", result == 0 ? "ok" : "not ok", active_case);
    return result;
}
