#ifndef GABBABOY_PLAYER_INPUT_H
#define GABBABOY_PLAYER_INPUT_H

#include "gabbaboy/gabbaboy.h"

#include <SDL3/SDL.h>

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define PLAYER_INPUT_QUEUE_CAPACITY 64u
#define PLAYER_INPUT_NORMAL_CAPACITY 56u
#define PLAYER_INPUT_BUTTON_COUNT 8u
#define PLAYER_INPUT_GAMEPAD_CAPACITY 4u
#define PLAYER_DMG_HALF_DOT_RATE_HZ UINT64_C(8388608)

typedef struct {
    SDL_JoystickID id;
    uint8_t held_buttons;
    bool active;
} player_input_gamepad_source;

typedef struct {
    uint64_t host_anchor_ns;
    uint64_t guest_anchor_half_dots;
    uint64_t guest_cursor_half_dots;
    gbb_input_event pending[PLAYER_INPUT_QUEUE_CAPACITY];
    size_t pending_count;
    uint8_t keyboard_buttons;
    player_input_gamepad_source gamepads[PLAYER_INPUT_GAMEPAD_CAPACITY];
    uint8_t held_buttons;
    uint8_t release_pending_buttons;
    bool paused;
} player_input_state;

bool player_input_nanoseconds_to_half_dots(uint64_t nanoseconds,
                                           uint64_t *out_half_dots);
bool player_input_half_dots_to_nanoseconds(uint64_t half_dots,
                                           uint64_t *out_nanoseconds);
void player_input_reset(player_input_state *state, uint64_t host_now_ns);
void player_input_reconcile(player_input_state *state,
                            uint64_t guest_cursor_half_dots);
bool player_input_guest_target(const player_input_state *state,
                               uint64_t host_now_ns,
                               uint64_t *out_guest_half_dots);
gbb_error player_input_key(player_input_state *state, gbb_instance *machine,
                           uint64_t host_timestamp_ns, SDL_Scancode scancode,
                           bool pressed, bool repeat);
bool player_input_gamepad_added(player_input_state *state, SDL_JoystickID id);
gbb_error player_input_gamepad_button(player_input_state *state,
                                      gbb_instance *machine,
                                      uint64_t host_timestamp_ns,
                                      SDL_JoystickID id,
                                      SDL_GamepadButton button,
                                      bool pressed);
gbb_error player_input_gamepad_removed(player_input_state *state,
                                       gbb_instance *machine,
                                       uint64_t host_timestamp_ns,
                                       SDL_JoystickID id);
void player_input_pause(player_input_state *state);
bool player_input_resume(player_input_state *state, uint64_t host_now_ns);
gbb_error player_input_focus_gained(player_input_state *state,
                                    gbb_instance *machine,
                                    uint64_t host_timestamp_ns,
                                    uint64_t host_now_ns,
                                    bool intentional_pause);
gbb_error player_input_focus_lost(player_input_state *state,
                                  gbb_instance *machine,
                                  uint64_t host_timestamp_ns);
gbb_error player_input_retry_focus_releases(player_input_state *state,
                                            gbb_instance *machine,
                                            uint64_t host_timestamp_ns);

#endif
