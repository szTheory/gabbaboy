#include "input.h"

void player_input_reset(player_input_state *state) {
    if (state != NULL) state->held_buttons = 0;
}

static bool map_scancode(SDL_Scancode scancode, gbb_button *button) {
    if (button == NULL) return false;
    switch (scancode) {
    case SDL_SCANCODE_RIGHT: *button = GBB_BUTTON_RIGHT; return true;
    case SDL_SCANCODE_LEFT: *button = GBB_BUTTON_LEFT; return true;
    case SDL_SCANCODE_UP: *button = GBB_BUTTON_UP; return true;
    case SDL_SCANCODE_DOWN: *button = GBB_BUTTON_DOWN; return true;
    case SDL_SCANCODE_Z: *button = GBB_BUTTON_A; return true;
    case SDL_SCANCODE_X: *button = GBB_BUTTON_B; return true;
    case SDL_SCANCODE_RETURN: *button = GBB_BUTTON_START; return true;
    case SDL_SCANCODE_RSHIFT: *button = GBB_BUTTON_SELECT; return true;
    default: return false;
    }
}

gbb_error player_input_key(player_input_state *state, gbb_instance *machine,
                           uint64_t at_half_dots, SDL_Scancode scancode,
                           bool pressed, bool repeat) {
    if (state == NULL || machine == NULL) return GBB_INVALID_ARGUMENT;
    if (repeat) return GBB_OK;

    gbb_button button;
    if (!map_scancode(scancode, &button)) return GBB_OK;
    const uint8_t mask = (uint8_t)(1u << (unsigned)button);
    const bool was_held = (state->held_buttons & mask) != 0;
    if (was_held == pressed) return GBB_OK;

    const gbb_input_event event = {
        at_half_dots,
        pressed ? GBB_INPUT_BUTTON_PRESS : GBB_INPUT_BUTTON_RELEASE,
        (uint8_t)button
    };
    const gbb_error result = gbb_queue_events(machine, &event, 1);
    if (result != GBB_OK) return result;
    if (pressed) state->held_buttons |= mask;
    else state->held_buttons &= (uint8_t)~mask;
    return GBB_OK;
}
