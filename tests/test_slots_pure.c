/* Slot message table, key decoder and re-anchor plan (Phase 18, D-21, D-24, D-25).
 *
 * Portable and window-free: no file system, no clock and no instance is touched, so this runs on every
 * platform in the main inventory. The expected strings are written out here, independently of slots.c.
 * Every failing check prints "FAIL <case>: file:line expr" and exits 1, so a mutant engine is told apart
 * from a crash. Unknown case names exit 2.
 *
 * Non-ASCII glyphs are written as UTF-8 byte escapes so the compiler's source charset cannot change them:
 * U+2318 is \xe2\x8c\x98 and U+00B7 would be \xc2\xb7 (the status line joins with it in the player, not
 * here). A literal is closed after an escape that a hex digit could follow, because \x takes every hex
 * digit after it. */
#include "gabbaboy/gabbaboy.h"
#include "slots.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

static const char *g_case = "?";

#define REQUIRE(x) do { if (!(x)) { \
    printf("FAIL %s: %s:%d %s\n", g_case, __FILE__, __LINE__, #x); return 1; \
} } while (0)

static player_slot_result make_result(player_slot_outcome outcome, int error, unsigned slot,
                                      player_slot_source source) {
    player_slot_result result;
    memset(&result, 0, sizeof(result));
    result.outcome = outcome;
    result.error = error;
    result.slot = slot;
    result.source = source;
    return result;
}

/* "<Subject> <phrase>; nothing changed" for a refusal, written out per error class. */
static const char *refusal_phrase(int error) {
    if (error == GBB_STATE_IDENTITY_MISMATCH) return "is from a different game or model";
    if (error == GBB_STATE_UNSUPPORTED_VERSION) return "is from another GabbaBoy version";
    if (error == GBB_STATE_BAD_FORMAT) return "is not a GabbaBoy state";
    if (error == GBB_STATE_SIZE_MISMATCH || error == GBB_STATE_CORRUPT || error == GBB_STATE_INVALID_CONTENT)
        return "is damaged";
    return "could not be loaded";
}

static int expect_message(player_slot_result result, const char *want, int line) {
    char got[200];
    memset(got, 'x', sizeof(got));
    player_slot_format_message(&result, got, sizeof(got));
    if (strcmp(got, want) != 0) {
        printf("FAIL %s: %s:%d message '%s' expected '%s' (outcome %d error %d)\n", g_case, __FILE__, line, got,
               want, (int)result.outcome, result.error);
        return 1;
    }
    return 0;
}

#define EXPECT_MESSAGE(result, want) do { if (expect_message((result), (want), __LINE__) != 0) return 1; } while (0)

static int case_message_table(void) {
    /* Outcomes with a fixed text, for every gbb_error value that could ride along. */
    for (int error = GBB_OK; error <= GBB_STATE_INVALID_CONTENT; ++error) {
        EXPECT_MESSAGE(make_result(PLAYER_SLOT_SAVED, error, 4u, PLAYER_SLOT_SOURCE_SLOT), "Saved slot 4");
        EXPECT_MESSAGE(make_result(PLAYER_SLOT_SAVE_FAILED, error, 4u, PLAYER_SLOT_SOURCE_SLOT),
                       "Slot 4 not saved: the file could not be written");
        EXPECT_MESSAGE(make_result(PLAYER_SLOT_LOADED, error, 4u, PLAYER_SLOT_SOURCE_SLOT),
                       "Loaded slot 4 (\xe2\x8c\x98" "Z undoes)");
        EXPECT_MESSAGE(make_result(PLAYER_SLOT_UNDONE, error, 0u, PLAYER_SLOT_SOURCE_UNDO),
                       "Undid the last load (\xe2\x8c\x98" "Z switches back)");
        EXPECT_MESSAGE(make_result(PLAYER_SLOT_EMPTY, error, 4u, PLAYER_SLOT_SOURCE_SLOT),
                       "Slot 4 is empty; nothing changed");
        EXPECT_MESSAGE(make_result(PLAYER_SLOT_NO_UNDO, error, 0u, PLAYER_SLOT_SOURCE_UNDO), "Nothing to undo");
    }

    /* Outcomes that name a subject: Slot N for a slot, The undo backup for the undo source. */
    for (int source = PLAYER_SLOT_SOURCE_SLOT; source <= PLAYER_SLOT_SOURCE_UNDO; ++source) {
        const player_slot_source from = (player_slot_source)source;
        const char *subject = from == PLAYER_SLOT_SOURCE_UNDO ? "The undo backup" : "Slot 4";
        const unsigned slot = from == PLAYER_SLOT_SOURCE_UNDO ? 0u : 4u;
        char want[200];

        (void)snprintf(want, sizeof(want), "%s could not be read; nothing changed", subject);
        EXPECT_MESSAGE(make_result(PLAYER_SLOT_READ_FAILED, GBB_OK, slot, from), want);
        (void)snprintf(want, sizeof(want), "%s contains unsafe queued input; nothing changed", subject);
        EXPECT_MESSAGE(make_result(PLAYER_SLOT_UNSAFE_INPUT, GBB_OK, slot, from), want);
        EXPECT_MESSAGE(make_result(PLAYER_SLOT_BACKUP_FAILED, GBB_OK, slot, from),
                       from == PLAYER_SLOT_SOURCE_UNDO
                           ? "Undo not applied: undo backup failed; nothing changed"
                           : "Slot 4 not loaded: undo backup failed; nothing changed");

        (void)snprintf(want, sizeof(want), "%s could not be fully applied; the game state may have changed", subject);
        EXPECT_MESSAGE(make_result(PLAYER_SLOT_RESTORE_FAILED, GBB_STATE_CORRUPT, slot, from), want);

        /* Every state error code maps to its own class; anything else is "could not be loaded". */
        for (int error = GBB_OK; error <= GBB_STATE_INVALID_CONTENT; ++error) {
            (void)snprintf(want, sizeof(want), "%s %s; nothing changed", subject, refusal_phrase(error));
            EXPECT_MESSAGE(make_result(PLAYER_SLOT_REFUSED, error, slot, from), want);
        }
    }

    /* The literal strings, once, so the helper above cannot drift from the specification. */
    EXPECT_MESSAGE(make_result(PLAYER_SLOT_REFUSED, GBB_STATE_IDENTITY_MISMATCH, 4u, PLAYER_SLOT_SOURCE_SLOT),
                   "Slot 4 is from a different game or model; nothing changed");
    EXPECT_MESSAGE(make_result(PLAYER_SLOT_REFUSED, GBB_STATE_UNSUPPORTED_VERSION, 4u, PLAYER_SLOT_SOURCE_SLOT),
                   "Slot 4 is from another GabbaBoy version; nothing changed");
    EXPECT_MESSAGE(make_result(PLAYER_SLOT_REFUSED, GBB_STATE_BAD_FORMAT, 4u, PLAYER_SLOT_SOURCE_SLOT),
                   "Slot 4 is not a GabbaBoy state; nothing changed");
    EXPECT_MESSAGE(make_result(PLAYER_SLOT_REFUSED, GBB_STATE_CORRUPT, 4u, PLAYER_SLOT_SOURCE_SLOT),
                   "Slot 4 is damaged; nothing changed");
    EXPECT_MESSAGE(make_result(PLAYER_SLOT_REFUSED, GBB_STATE_NO_ROM, 4u, PLAYER_SLOT_SOURCE_SLOT),
                   "Slot 4 could not be loaded; nothing changed");
    EXPECT_MESSAGE(make_result(PLAYER_SLOT_REFUSED, GBB_STATE_IDENTITY_MISMATCH, 0u, PLAYER_SLOT_SOURCE_UNDO),
                   "The undo backup is from a different game or model; nothing changed");

    /* The buffer is always NUL-terminated and never overrun, and an empty buffer is left alone. */
    const player_slot_result saved = make_result(PLAYER_SLOT_SAVED, GBB_OK, 4u, PLAYER_SLOT_SOURCE_SLOT);
    char small[8];
    memset(small, 'x', sizeof(small));
    player_slot_format_message(&saved, small, 5u);
    REQUIRE(strcmp(small, "Save") == 0);
    REQUIRE(small[5] == 'x' && small[6] == 'x' && small[7] == 'x');
    memset(small, 'x', sizeof(small));
    player_slot_format_message(&saved, small, 1u);
    REQUIRE(small[0] == '\0' && small[1] == 'x');
    player_slot_format_message(&saved, small, 0u);
    REQUIRE(small[0] == '\0' && small[1] == 'x');
    player_slot_format_message(&saved, NULL, 8u);
    player_slot_format_message(NULL, small, sizeof(small));
    REQUIRE(small[0] == '\0');

    /* The stderr line (D-25) names the operation, slot, outcome token and gbb_error. */
    char log[160];
    const player_slot_result refused =
        make_result(PLAYER_SLOT_REFUSED, GBB_STATE_IDENTITY_MISMATCH, 4u, PLAYER_SLOT_SOURCE_SLOT);
    player_slot_format_log(&refused, log, sizeof(log));
    REQUIRE(strcmp(log, "gabbaboy-player: slot op=load slot=4 outcome=refused gbb_error=24") == 0);
    player_slot_format_log(&saved, log, sizeof(log));
    REQUIRE(strcmp(log, "gabbaboy-player: slot op=save slot=4 outcome=saved gbb_error=0") == 0);
    const player_slot_result undone = make_result(PLAYER_SLOT_UNDONE, GBB_OK, 0u, PLAYER_SLOT_SOURCE_UNDO);
    player_slot_format_log(&undone, log, sizeof(log));
    REQUIRE(strcmp(log, "gabbaboy-player: slot op=undo slot=0 outcome=undone gbb_error=0") == 0);
    static const struct {
        player_slot_outcome outcome;
        const char *token;
    } tokens[] = {
        {PLAYER_SLOT_SAVE_FAILED, "save-failed"}, {PLAYER_SLOT_LOADED, "loaded"},
        {PLAYER_SLOT_EMPTY, "empty"},             {PLAYER_SLOT_NO_UNDO, "no-undo"},
        {PLAYER_SLOT_READ_FAILED, "read-failed"}, {PLAYER_SLOT_BACKUP_FAILED, "backup-failed"},
        {PLAYER_SLOT_UNSAFE_INPUT, "unsafe-input"}, {PLAYER_SLOT_RESTORE_FAILED, "restore-failed"},
    };
    for (size_t i = 0u; i < sizeof(tokens) / sizeof(tokens[0]); ++i) {
        const player_slot_result one = make_result(tokens[i].outcome, GBB_OK, 2u, PLAYER_SLOT_SOURCE_SLOT);
        char want[160];
        player_slot_format_log(&one, log, sizeof(log));
        (void)snprintf(want, sizeof(want), "outcome=%s gbb_error=0", tokens[i].token);
        REQUIRE(strstr(log, want) != NULL);
    }
    return 0;
}

static player_slot_key_input key(unsigned digit, char letter, bool gui, bool ctrl, bool alt) {
    player_slot_key_input input;
    memset(&input, 0, sizeof(input));
    input.digit = digit;
    input.letter = letter;
    input.gui = gui;
    input.ctrl = ctrl;
    input.alt = alt;
    return input;
}

static int expect_key(player_slot_key_input input, player_slot_key_action want, unsigned want_slot, int line) {
    unsigned slot = 99u;
    const player_slot_key_action got = player_slot_key_decode(&input, &slot);
    if (got != want || (want == PLAYER_SLOT_KEY_SELECT && slot != want_slot)) {
        printf("FAIL %s: %s:%d decoded %d slot %u, expected %d slot %u\n", g_case, __FILE__, line, (int)got, slot,
               (int)want, want_slot);
        return 1;
    }
    return 0;
}

#define EXPECT_KEY(input, want, slot) do { if (expect_key((input), (want), (slot), __LINE__) != 0) return 1; } while (0)

static int case_key_decoder(void) {
    /* Digits 1..9 select, with or without Shift (Right Shift is the Select button); GUI, Ctrl or Alt veto. */
    for (unsigned digit = 1u; digit <= 9u; ++digit) {
        EXPECT_KEY(key(digit, 0, false, false, false), PLAYER_SLOT_KEY_SELECT, digit);
        EXPECT_KEY(key(digit, 0, true, false, false), PLAYER_SLOT_KEY_NONE, 0u);
        EXPECT_KEY(key(digit, 0, false, true, false), PLAYER_SLOT_KEY_NONE, 0u);
        EXPECT_KEY(key(digit, 0, false, false, true), PLAYER_SLOT_KEY_NONE, 0u);
    }
    EXPECT_KEY(key(0u, 0, false, false, false), PLAYER_SLOT_KEY_NONE, 0u); /* 0 is reserved */
    EXPECT_KEY(key(10u, 0, false, false, false), PLAYER_SLOT_KEY_NONE, 0u);

    /* Command-S saves, Command-L loads, Command-Z undoes; the bare letters and Command-R do nothing. */
    EXPECT_KEY(key(0u, 'S', true, false, false), PLAYER_SLOT_KEY_SAVE, 0u);
    EXPECT_KEY(key(0u, 'L', true, false, false), PLAYER_SLOT_KEY_LOAD, 0u);
    EXPECT_KEY(key(0u, 'Z', true, false, false), PLAYER_SLOT_KEY_UNDO, 0u);
    EXPECT_KEY(key(0u, 's', true, false, false), PLAYER_SLOT_KEY_SAVE, 0u);
    EXPECT_KEY(key(0u, 'S', false, false, false), PLAYER_SLOT_KEY_NONE, 0u);
    EXPECT_KEY(key(0u, 'L', false, false, false), PLAYER_SLOT_KEY_NONE, 0u);
    EXPECT_KEY(key(0u, 'Z', false, false, false), PLAYER_SLOT_KEY_NONE, 0u);
    EXPECT_KEY(key(0u, 'R', false, false, false), PLAYER_SLOT_KEY_NONE, 0u);
    EXPECT_KEY(key(0u, 'R', true, false, false), PLAYER_SLOT_KEY_NONE, 0u);
    EXPECT_KEY(key(0u, 'S', true, true, false), PLAYER_SLOT_KEY_NONE, 0u);
    EXPECT_KEY(key(0u, 'S', true, false, true), PLAYER_SLOT_KEY_NONE, 0u);
    EXPECT_KEY(key(0u, 'S', false, true, false), PLAYER_SLOT_KEY_NONE, 0u);

    /* A key repeat or a pending transition, dialog or save-failure prompt ignores every action. */
    player_slot_key_input repeated = key(3u, 0, false, false, false);
    repeated.repeat = true;
    EXPECT_KEY(repeated, PLAYER_SLOT_KEY_NONE, 0u);
    repeated = key(0u, 'S', true, false, false);
    repeated.repeat = true;
    EXPECT_KEY(repeated, PLAYER_SLOT_KEY_NONE, 0u);
    player_slot_key_input blocked = key(3u, 0, false, false, false);
    blocked.blocked = true;
    EXPECT_KEY(blocked, PLAYER_SLOT_KEY_NONE, 0u);
    blocked = key(0u, 'Z', true, false, false);
    blocked.blocked = true;
    EXPECT_KEY(blocked, PLAYER_SLOT_KEY_NONE, 0u);

    /* A NULL input decodes to nothing and a NULL slot pointer is allowed. */
    unsigned slot = 7u;
    REQUIRE(player_slot_key_decode(NULL, &slot) == PLAYER_SLOT_KEY_NONE);
    const player_slot_key_input five = key(5u, 0, false, false, false);
    REQUIRE(player_slot_key_decode(&five, NULL) == PLAYER_SLOT_KEY_SELECT);
    return 0;
}

static gbb_input_clock clock_of(uint64_t now, uint64_t last, uint32_t count) {
    gbb_input_clock clock;
    memset(&clock, 0, sizeof(clock));
    clock.struct_size = GBB_INPUT_CLOCK_SIZE_V1;
    clock.now_half_dots = now;
    clock.last_queued_half_dots = last;
    clock.queued_count = count;
    return clock;
}

static int case_reanchor_plan(void) {
    /* Nothing queued: the cursor and the release time are both now. */
    gbb_input_clock clock = clock_of(1000u, 1000u, 0u);
    player_slot_reanchor plan = player_slot_plan_reanchor(&clock);
    REQUIRE(plan.cursor == 1000u && plan.release_at == 1000u && plan.pending_count == 0u && !plan.unsafe);

    /* A restored queue reaching past now: releases go after the last restored event. */
    clock = clock_of(1000u, 5000u, 3u);
    plan = player_slot_plan_reanchor(&clock);
    REQUIRE(plan.cursor == 1000u && plan.release_at == 5000u && plan.pending_count == 3u && !plan.unsafe);

    /* A last event before now is time-safe and the release time stays at now. */
    clock = clock_of(5000u, 1000u, 0u);
    plan = player_slot_plan_reanchor(&clock);
    REQUIRE(plan.cursor == 5000u && plan.release_at == 5000u && !plan.unsafe);

    /* The time window: exactly one frame per queue slot is safe, one half-dot more is not. */
    const uint64_t window = UINT64_C(140448) * 64u;
    REQUIRE(PLAYER_SLOT_UNSAFE_HALF_DOTS == window);
    clock = clock_of(1000u, 1000u + window, 1u);
    REQUIRE(!player_slot_plan_reanchor(&clock).unsafe);
    clock = clock_of(1000u, 1000u + window + 1u, 1u);
    REQUIRE(player_slot_plan_reanchor(&clock).unsafe);

    /* The count: 56 events leave room for the eight releases in the 64-event queue, 57 do not. */
    clock = clock_of(1000u, 1056u, 56u);
    REQUIRE(!player_slot_plan_reanchor(&clock).unsafe);
    clock = clock_of(1000u, 1057u, 57u);
    REQUIRE(player_slot_plan_reanchor(&clock).unsafe);
    REQUIRE(PLAYER_SLOT_QUEUE_CAPACITY - PLAYER_SLOT_RELEASE_EVENTS == 56u);

    /* A NULL clock plans nothing and is unsafe. */
    REQUIRE(player_slot_plan_reanchor(NULL).unsafe);
    return 0;
}

typedef struct {
    const char *name;
    int (*run)(void);
} slot_case;

static const slot_case g_cases[] = {
    {"message_table", case_message_table},
    {"key_decoder", case_key_decoder},
    {"reanchor_plan", case_reanchor_plan},
};

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: test_slots_pure <case>\n");
        return 2;
    }
    for (size_t i = 0u; i < sizeof(g_cases) / sizeof(g_cases[0]); ++i) {
        if (strcmp(argv[1], g_cases[i].name) != 0) continue;
        g_case = g_cases[i].name;
        const int result = g_cases[i].run();
        if (result == 0) printf("PASS %s\n", g_case);
        return result;
    }
    fprintf(stderr, "unknown case: %s\n", argv[1]);
    return 2;
}
