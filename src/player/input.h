#ifndef GABBABOY_PLAYER_INPUT_H
#define GABBABOY_PLAYER_INPUT_H

#include "gabbaboy/gabbaboy.h"

#include <SDL3/SDL.h>

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    uint8_t held_buttons;
} player_input_state;

void player_input_reset(player_input_state *state);
gbb_error player_input_key(player_input_state *state, gbb_instance *machine,
                           uint64_t at_half_dots, SDL_Scancode scancode,
                           bool pressed, bool repeat);

#endif
