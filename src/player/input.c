#include "input.h"

#include <string.h>

#define NANOSECONDS_PER_SECOND UINT64_C(1000000000)

bool player_input_nanoseconds_to_half_dots(uint64_t nanoseconds,
                                           uint64_t *out_half_dots) {
    if (out_half_dots == NULL) return false;
    const uint64_t seconds = nanoseconds / NANOSECONDS_PER_SECOND;
    const uint64_t remainder = nanoseconds % NANOSECONDS_PER_SECOND;
    if (seconds > UINT64_MAX / PLAYER_DMG_HALF_DOT_RATE_HZ) return false;

    const uint64_t whole = seconds * PLAYER_DMG_HALF_DOT_RATE_HZ;
    const uint64_t fractional =
        (remainder * PLAYER_DMG_HALF_DOT_RATE_HZ) / NANOSECONDS_PER_SECOND;
    if (whole > UINT64_MAX - fractional) return false;
    *out_half_dots = whole + fractional;
    return true;
}

bool player_input_half_dots_to_nanoseconds(uint64_t half_dots,
                                           uint64_t *out_nanoseconds) {
    if (out_nanoseconds == NULL) return false;
    const uint64_t seconds = half_dots / PLAYER_DMG_HALF_DOT_RATE_HZ;
    const uint64_t remainder = half_dots % PLAYER_DMG_HALF_DOT_RATE_HZ;
    if (seconds > UINT64_MAX / NANOSECONDS_PER_SECOND) return false;

    const uint64_t whole = seconds * NANOSECONDS_PER_SECOND;
    const uint64_t fractional_numerator = remainder * NANOSECONDS_PER_SECOND;
    uint64_t fractional = fractional_numerator / PLAYER_DMG_HALF_DOT_RATE_HZ;
    if (fractional_numerator % PLAYER_DMG_HALF_DOT_RATE_HZ != 0) ++fractional;
    if (whole > UINT64_MAX - fractional) return false;
    *out_nanoseconds = whole + fractional;
    return true;
}

void player_input_reset(player_input_state *state, uint64_t host_now_ns) {
    if (state == NULL) return;
    memset(state, 0, sizeof(*state));
    state->host_anchor_ns = host_now_ns;
}

void player_input_reconcile(player_input_state *state,
                            uint64_t guest_cursor_half_dots) {
    if (state == NULL || guest_cursor_half_dots < state->guest_cursor_half_dots)
        return;
    state->guest_cursor_half_dots = guest_cursor_half_dots;
    size_t consumed = 0;
    while (consumed < state->pending_count &&
           state->pending[consumed].at_half_dots <= guest_cursor_half_dots)
        ++consumed;
    if (consumed == 0) return;
    const size_t remaining = state->pending_count - consumed;
    memmove(state->pending, state->pending + consumed,
            remaining * sizeof(state->pending[0]));
    state->pending_count = remaining;
}

static bool map_host_time(const player_input_state *state,
                          uint64_t host_now_ns, uint64_t *out_guest_half_dots) {
    if (state == NULL || out_guest_half_dots == NULL) return false;
    const uint64_t elapsed_ns = host_now_ns >= state->host_anchor_ns
        ? host_now_ns - state->host_anchor_ns : 0;
    uint64_t elapsed_half_dots;
    if (!player_input_nanoseconds_to_half_dots(elapsed_ns, &elapsed_half_dots) ||
        state->guest_anchor_half_dots > UINT64_MAX - elapsed_half_dots)
        return false;
    uint64_t mapped = state->guest_anchor_half_dots + elapsed_half_dots;
    if (mapped < state->guest_cursor_half_dots)
        mapped = state->guest_cursor_half_dots;
    *out_guest_half_dots = mapped;
    return true;
}

bool player_input_guest_target(const player_input_state *state,
                               uint64_t host_now_ns,
                               uint64_t *out_guest_half_dots) {
    return map_host_time(state, host_now_ns, out_guest_half_dots);
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

static bool schedule_time(const player_input_state *state,
                          uint64_t host_timestamp_ns,
                          uint64_t *out_guest_half_dots) {
    if (!map_host_time(state, host_timestamp_ns, out_guest_half_dots)) return false;
    if (state->pending_count > 0) {
        const uint64_t last = state->pending[state->pending_count - 1].at_half_dots;
        if (*out_guest_half_dots < last) *out_guest_half_dots = last;
    }
    return true;
}

static bool pending_has_room(const player_input_state *state, size_t count,
                             size_t capacity) {
    return state != NULL && state->pending_count <= capacity &&
           count <= capacity - state->pending_count;
}

static void append_pending(player_input_state *state,
                           const gbb_input_event *events, size_t count) {
    memcpy(state->pending + state->pending_count, events,
           count * sizeof(state->pending[0]));
    state->pending_count += count;
}

gbb_error player_input_key(player_input_state *state, gbb_instance *machine,
                           uint64_t host_timestamp_ns, SDL_Scancode scancode,
                           bool pressed, bool repeat) {
    if (state == NULL || machine == NULL) return GBB_INVALID_ARGUMENT;
    if (repeat || state->paused || state->release_pending_buttons != 0)
        return GBB_OK;

    gbb_button button;
    if (!map_scancode(scancode, &button)) return GBB_OK;
    const uint8_t mask = (uint8_t)(1u << (unsigned)button);
    const bool was_held = (state->held_buttons & mask) != 0;
    if (was_held == pressed) return GBB_OK;
    if (!pending_has_room(state, 1, PLAYER_INPUT_NORMAL_CAPACITY))
        return GBB_EVENT_QUEUE_FULL;

    uint64_t at_half_dots;
    if (!schedule_time(state, host_timestamp_ns, &at_half_dots))
        return GBB_INVALID_EVENT;
    const gbb_input_event event = {
        at_half_dots,
        pressed ? GBB_INPUT_BUTTON_PRESS : GBB_INPUT_BUTTON_RELEASE,
        (uint8_t)button
    };
    const gbb_error result = gbb_queue_events(machine, &event, 1);
    if (result != GBB_OK) return result;
    append_pending(state, &event, 1);
    if (pressed) state->held_buttons |= mask;
    else state->held_buttons &= (uint8_t)~mask;
    return GBB_OK;
}

void player_input_pause(player_input_state *state) {
    if (state != NULL) state->paused = true;
}

bool player_input_resume(player_input_state *state, uint64_t host_now_ns) {
    if (state == NULL || state->release_pending_buttons != 0) return false;
    state->host_anchor_ns = host_now_ns;
    state->guest_anchor_half_dots = state->guest_cursor_half_dots;
    state->paused = false;
    return true;
}

gbb_error player_input_retry_focus_releases(player_input_state *state,
                                            gbb_instance *machine,
                                            uint64_t host_timestamp_ns) {
    if (state == NULL || machine == NULL) return GBB_INVALID_ARGUMENT;
    const uint8_t mask = state->release_pending_buttons;
    if (mask == 0) return GBB_OK;
    if (!state->paused) return GBB_INVALID_EVENT;

    gbb_input_event releases[PLAYER_INPUT_BUTTON_COUNT];
    size_t count = 0;
    for (unsigned button = 0; button < PLAYER_INPUT_BUTTON_COUNT; ++button) {
        if ((mask & (uint8_t)(1u << button)) == 0) continue;
        releases[count++] = (gbb_input_event){
            0, GBB_INPUT_BUTTON_RELEASE, (uint8_t)button
        };
    }
    if (!pending_has_room(state, count, PLAYER_INPUT_QUEUE_CAPACITY))
        return GBB_EVENT_QUEUE_FULL;

    uint64_t at_half_dots;
    if (!schedule_time(state, host_timestamp_ns, &at_half_dots))
        return GBB_INVALID_EVENT;
    for (size_t i = 0; i < count; ++i)
        releases[i].at_half_dots = at_half_dots;

    const gbb_error result = gbb_queue_events(machine, releases, count);
    if (result != GBB_OK) return result;
    append_pending(state, releases, count);
    state->held_buttons &= (uint8_t)~mask;
    state->release_pending_buttons = 0;
    return GBB_OK;
}

gbb_error player_input_focus_lost(player_input_state *state,
                                  gbb_instance *machine,
                                  uint64_t host_timestamp_ns) {
    if (state == NULL || machine == NULL) return GBB_INVALID_ARGUMENT;
    state->paused = true;
    state->release_pending_buttons |= state->held_buttons;
    return player_input_retry_focus_releases(state, machine, host_timestamp_ns);
}
