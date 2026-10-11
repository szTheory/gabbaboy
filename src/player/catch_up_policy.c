#include "catch_up_policy.h"

#include <stdio.h>

struct player_catch_up_decision player_catch_up_policy(int64_t saved_at, bool saved_valid,
                                                       int64_t now, bool now_valid) {
    struct player_catch_up_decision d = {PLAYER_CATCH_UP_NONE, PLAYER_CATCH_UP_STATUS_NONE, 0};
    if (!saved_valid) {
        d.status = PLAYER_CATCH_UP_STATUS_NO_TIMESTAMP;
        return d;
    }
    if (!now_valid) {
        d.status = PLAYER_CATCH_UP_STATUS_CLOCK_UNAVAILABLE;
        return d;
    }
    if (now < saved_at) {
        d.status = PLAYER_CATCH_UP_STATUS_CLOCK_EARLIER;
        return d;
    }
    if (now == saved_at) return d;
    /* now > saved_at, so the unsigned difference is exact (at most 2^64 - 1)
     * even when the signed one would overflow. */
    const uint64_t diff = (uint64_t)now - (uint64_t)saved_at;
    d.action = PLAYER_CATCH_UP_APPLY;
    d.status = PLAYER_CATCH_UP_STATUS_ADVANCED;
    d.delta = diff > (uint64_t)INT64_MAX ? INT64_MAX : (int64_t)diff;
    return d;
}

void player_catch_up_format_status(enum player_catch_up_status status, int64_t delta,
                                   bool carry_became_set, bool halted,
                                   char *out, size_t capacity) {
    if (out == NULL || capacity == 0u) return;
    out[0] = '\0';
    switch (status) {
    case PLAYER_CATCH_UP_STATUS_NO_TIMESTAMP:
        snprintf(out, capacity, "Game clock not advanced: the save has no time stamp.");
        return;
    case PLAYER_CATCH_UP_STATUS_CLOCK_UNAVAILABLE:
        snprintf(out, capacity, "Game clock not advanced: the system clock is unavailable.");
        return;
    case PLAYER_CATCH_UP_STATUS_CLOCK_EARLIER:
        snprintf(out, capacity, "Game clock not advanced: the system clock is earlier than the save.");
        return;
    case PLAYER_CATCH_UP_STATUS_HALTED:
        snprintf(out, capacity, "Game clock is halted; not advanced.");
        return;
    case PLAYER_CATCH_UP_STATUS_ADVANCED:
        break;
    default:
        return;
    }
    if (halted) {
        snprintf(out, capacity, "Game clock is halted; not advanced.");
        return;
    }
    const uint64_t total = delta < 0 ? 0u : (uint64_t)delta;
    const unsigned long long days = total / 86400u;
    const unsigned hours = (unsigned)(total % 86400u / 3600u);
    const unsigned minutes = (unsigned)(total % 3600u / 60u);
    const unsigned seconds = (unsigned)(total % 60u);
    snprintf(out, capacity, "Game clock advanced by %llud %uh %um %us%s", days, hours, minutes,
             seconds, carry_became_set ? " (day counter overflowed)" : "");
}
