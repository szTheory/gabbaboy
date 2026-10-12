#ifndef GABBABOY_PLAYER_CATCH_UP_POLICY_H
#define GABBABOY_PLAYER_CATCH_UP_POLICY_H

/* Pure host policy for advancing a timer cartridge's game clock when a save is
 * reopened (D-21, D-22). No SDL, CommonCrypto, POSIX or clock call lives here:
 * the caller supplies both Unix timestamps, so the table is testable on every
 * operating system. */

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

enum player_catch_up_action {
    PLAYER_CATCH_UP_NONE,
    PLAYER_CATCH_UP_APPLY
};

enum player_catch_up_status {
    PLAYER_CATCH_UP_STATUS_NONE,
    PLAYER_CATCH_UP_STATUS_NO_TIMESTAMP,
    PLAYER_CATCH_UP_STATUS_CLOCK_UNAVAILABLE,
    PLAYER_CATCH_UP_STATUS_CLOCK_EARLIER,
    PLAYER_CATCH_UP_STATUS_ADVANCED,
    PLAYER_CATCH_UP_STATUS_HALTED
};

struct player_catch_up_decision {
    enum player_catch_up_action action;
    enum player_catch_up_status status;
    int64_t delta; /* seconds to pass to gbb_rtc_catch_up; 0 unless APPLY */
};

/* A clock earlier than the save never moves the game clock backwards: the
 * decision is NONE. The delta is clamped to INT64_MAX. */
struct player_catch_up_decision player_catch_up_policy(int64_t saved_at, bool saved_valid,
                                                       int64_t now, bool now_valid);

/* Writes the one-line status message (empty for STATUS_NONE). The result is
 * always NUL-terminated when capacity is at least 1 and never overruns. */
void player_catch_up_format_status(enum player_catch_up_status status, int64_t delta,
                                   bool carry_became_set, bool halted,
                                   char *out, size_t capacity);

#endif
