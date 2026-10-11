#include "catch_up_policy.h"

#include <stdio.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

static int check(int64_t saved, bool saved_ok, int64_t now, bool now_ok,
                 enum player_catch_up_action action, enum player_catch_up_status status,
                 int64_t delta) {
    const struct player_catch_up_decision d = player_catch_up_policy(saved, saved_ok, now, now_ok);
    REQUIRE(d.action == action);
    REQUIRE(d.status == status);
    REQUIRE(d.delta == delta);
    return 0;
}

static int fmt(enum player_catch_up_status status, int64_t delta, bool carry, bool halted,
               const char *expected) {
    char buf[160];
    player_catch_up_format_status(status, delta, carry, halted, buf, sizeof(buf));
    if (strcmp(buf, expected) != 0) {
        fprintf(stderr, "format mismatch: \"%s\" vs \"%s\"\n", buf, expected);
        return 1;
    }
    return 0;
}

static int table(void) {
    /* D-22 conditions */
    REQUIRE(check(5, false, 10, true, PLAYER_CATCH_UP_NONE, PLAYER_CATCH_UP_STATUS_NO_TIMESTAMP, 0) == 0);
    REQUIRE(check(5, true, 10, false, PLAYER_CATCH_UP_NONE, PLAYER_CATCH_UP_STATUS_CLOCK_UNAVAILABLE, 0) == 0);
    REQUIRE(check(10, true, 5, true, PLAYER_CATCH_UP_NONE, PLAYER_CATCH_UP_STATUS_CLOCK_EARLIER, 0) == 0);
    REQUIRE(check(10, true, 10, true, PLAYER_CATCH_UP_NONE, PLAYER_CATCH_UP_STATUS_NONE, 0) == 0);
    REQUIRE(check(10, true, 15, true, PLAYER_CATCH_UP_APPLY, PLAYER_CATCH_UP_STATUS_ADVANCED, 5) == 0);
    /* invalid saved wins over invalid now */
    REQUIRE(check(5, false, 10, false, PLAYER_CATCH_UP_NONE, PLAYER_CATCH_UP_STATUS_NO_TIMESTAMP, 0) == 0);

    /* extremes in all combinations */
    static const int64_t v[5] = {INT64_MIN, -1, 0, 1, INT64_MAX};
    for (int i = 0; i < 5; ++i) {
        for (int j = 0; j < 5; ++j) {
            const int64_t s = v[i], n = v[j];
            if (n < s) {
                REQUIRE(check(s, true, n, true, PLAYER_CATCH_UP_NONE, PLAYER_CATCH_UP_STATUS_CLOCK_EARLIER, 0) == 0);
            } else if (n == s) {
                REQUIRE(check(s, true, n, true, PLAYER_CATCH_UP_NONE, PLAYER_CATCH_UP_STATUS_NONE, 0) == 0);
            } else {
                const uint64_t diff = (uint64_t)n - (uint64_t)s;
                const int64_t expect = diff > (uint64_t)INT64_MAX ? INT64_MAX : (int64_t)diff;
                REQUIRE(check(s, true, n, true, PLAYER_CATCH_UP_APPLY, PLAYER_CATCH_UP_STATUS_ADVANCED, expect) == 0);
            }
            /* validity flags override values */
            REQUIRE(check(s, false, n, true, PLAYER_CATCH_UP_NONE, PLAYER_CATCH_UP_STATUS_NO_TIMESTAMP, 0) == 0);
            REQUIRE(check(s, true, n, false, PLAYER_CATCH_UP_NONE, PLAYER_CATCH_UP_STATUS_CLOCK_UNAVAILABLE, 0) == 0);
        }
    }
    REQUIRE(check(INT64_MIN, true, INT64_MAX, true, PLAYER_CATCH_UP_APPLY, PLAYER_CATCH_UP_STATUS_ADVANCED, INT64_MAX) == 0);
    REQUIRE(check(-1, true, 1, true, PLAYER_CATCH_UP_APPLY, PLAYER_CATCH_UP_STATUS_ADVANCED, 2) == 0);

    /* formatter */
    const enum player_catch_up_status adv = PLAYER_CATCH_UP_STATUS_ADVANCED;
    REQUIRE(fmt(adv, 0, false, false, "Game clock advanced by 0d 0h 0m 0s") == 0);
    REQUIRE(fmt(adv, 1, false, false, "Game clock advanced by 0d 0h 0m 1s") == 0);
    REQUIRE(fmt(adv, 59, false, false, "Game clock advanced by 0d 0h 0m 59s") == 0);
    REQUIRE(fmt(adv, 3661, false, false, "Game clock advanced by 0d 1h 1m 1s") == 0);
    REQUIRE(fmt(adv, 93784, false, false, "Game clock advanced by 1d 2h 3m 4s") == 0);
    /* INT64_MAX = 106751991167300 d 15 h 30 m 7 s */
    REQUIRE(fmt(adv, INT64_MAX, false, false, "Game clock advanced by 106751991167300d 15h 30m 7s") == 0);
    REQUIRE(fmt(adv, 93784, true, false, "Game clock advanced by 1d 2h 3m 4s (day counter overflowed)") == 0);
    REQUIRE(fmt(adv, 93784, false, true, "Game clock is halted; not advanced.") == 0);
    REQUIRE(fmt(PLAYER_CATCH_UP_STATUS_HALTED, 0, false, false, "Game clock is halted; not advanced.") == 0);
    REQUIRE(fmt(PLAYER_CATCH_UP_STATUS_NO_TIMESTAMP, 0, false, false,
                "Game clock not advanced: the save has no time stamp.") == 0);
    REQUIRE(fmt(PLAYER_CATCH_UP_STATUS_CLOCK_UNAVAILABLE, 0, false, false,
                "Game clock not advanced: the system clock is unavailable.") == 0);
    REQUIRE(fmt(PLAYER_CATCH_UP_STATUS_CLOCK_EARLIER, 0, false, false,
                "Game clock not advanced: the system clock is earlier than the save.") == 0);
    REQUIRE(fmt(PLAYER_CATCH_UP_STATUS_NONE, 0, false, false, "") == 0);

    /* truncation safety */
    char tiny[1] = {'x'};
    player_catch_up_format_status(adv, 5, false, false, tiny, sizeof(tiny));
    REQUIRE(tiny[0] == '\0');
    char small[8];
    memset(small, 'x', sizeof(small));
    player_catch_up_format_status(adv, 93784, true, false, small, sizeof(small));
    REQUIRE(small[7] == '\0' && strlen(small) == 7u);
    player_catch_up_format_status(adv, 5, false, false, NULL, 4u);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "catch_up_policy_table") == 0) return table();
    return 2;
}
