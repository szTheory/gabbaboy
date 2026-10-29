/* gbb_get_input_clock (Phase 18, D-24): struct_size handshake, queue facts, and the clock a host
 * must re-anchor to after gbb_load_state restored a different time and queue.
 *
 * ROMs are built at run time (ROM-only, a spin loop at $0150); no state bytes are committed. Every
 * failing check prints "FAIL <case>: file:line expr" and exits 1, so a mutant core is told apart from
 * a crash. Unknown case names exit 2. */
#include "gabbaboy/gabbaboy.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SENTINEL 0xA7u
#define FRAME_HALF_DOTS UINT64_C(140448)

static const char *g_case = "?";

#define REQUIRE(x) do { if (!(x)) { \
    printf("FAIL %s: %s:%d %s\n", g_case, __FILE__, __LINE__, #x); return 1; \
} } while (0)

static void fix_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

/* ROM-only 32 KiB image: JP $0150 at the entry point, then JR -2 forever, so the CPU runs without
 * touching any device and every gbb_run call consumes its whole budget. */
static uint8_t *make_rom(size_t *out_size) {
    *out_size = 32768u;
    uint8_t *rom = calloc(*out_size, 1u);
    if (rom == NULL) return NULL;
    rom[0x100u] = 0xC3u;
    rom[0x101u] = 0x50u;
    rom[0x102u] = 0x01u;
    rom[0x150u] = 0x18u;
    rom[0x151u] = 0xFEu;
    fix_checksum(rom);
    return rom;
}

static gbb_instance *new_machine(const uint8_t *rom, size_t rom_size) {
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK) return NULL;
    if (gbb_load_rom(machine, rom, rom_size) != GBB_OK) {
        gbb_destroy(machine);
        return NULL;
    }
    return machine;
}

static void fill_clock(gbb_input_clock *clock, uint32_t size) {
    memset(clock, SENTINEL, sizeof(*clock));
    clock->struct_size = size;
}

static int clock_untouched(const gbb_input_clock *clock, uint32_t size) {
    gbb_input_clock want;
    fill_clock(&want, size);
    return memcmp(clock, &want, sizeof(want)) == 0;
}

static gbb_input_event press(uint64_t at, uint8_t button) {
    gbb_input_event event;
    memset(&event, 0, sizeof(event));
    event.at_half_dots = at;
    event.kind = GBB_INPUT_BUTTON_PRESS;
    event.value = button;
    return event;
}

static gbb_input_event release(uint64_t at, uint8_t button) {
    gbb_input_event event = press(at, button);
    event.kind = GBB_INPUT_BUTTON_RELEASE;
    return event;
}

static int read_clock(const gbb_instance *machine, gbb_input_clock *out) {
    fill_clock(out, GBB_INPUT_CLOCK_SIZE_V1);
    return gbb_get_input_clock(machine, out) == GBB_OK && out->struct_size == GBB_INPUT_CLOCK_SIZE_V1;
}

static int case_handshake(void) {
    size_t rom_size = 0u;
    uint8_t *rom = make_rom(&rom_size);
    REQUIRE(rom != NULL);
    gbb_instance *machine = new_machine(rom, rom_size);
    REQUIRE(machine != NULL);

    /* The layout is the documented 24 bytes. */
    REQUIRE(sizeof(gbb_input_clock) == 24u);
    REQUIRE(GBB_INPUT_CLOCK_SIZE_V1 == 24u);

    /* Too-small sizes are refused and every byte of the caller's struct is left alone. */
    const uint32_t too_small[] = {0u, 1u, 23u};
    for (size_t i = 0u; i < sizeof(too_small) / sizeof(too_small[0]); ++i) {
        gbb_input_clock clock;
        fill_clock(&clock, too_small[i]);
        REQUIRE(gbb_get_input_clock(machine, &clock) == GBB_INVALID_ARGUMENT);
        REQUIRE(clock_untouched(&clock, too_small[i]));
    }

    /* NULL arguments are refused; the one live struct stays untouched. */
    gbb_input_clock clock;
    fill_clock(&clock, GBB_INPUT_CLOCK_SIZE_V1);
    REQUIRE(gbb_get_input_clock(NULL, &clock) == GBB_INVALID_ARGUMENT);
    REQUIRE(clock_untouched(&clock, GBB_INPUT_CLOCK_SIZE_V1));
    REQUIRE(gbb_get_input_clock(machine, NULL) == GBB_INVALID_ARGUMENT);

    /* The exact size succeeds and reports the bytes written. */
    fill_clock(&clock, GBB_INPUT_CLOCK_SIZE_V1);
    REQUIRE(gbb_get_input_clock(machine, &clock) == GBB_OK);
    REQUIRE(clock.struct_size == GBB_INPUT_CLOCK_SIZE_V1);

    /* A larger caller struct keeps its trailing bytes. */
    struct {
        gbb_input_clock clock;
        uint8_t tail[16];
    } big;
    memset(&big, SENTINEL, sizeof(big));
    big.clock.struct_size = (uint32_t)sizeof(big);
    REQUIRE(gbb_get_input_clock(machine, &big.clock) == GBB_OK);
    REQUIRE(big.clock.struct_size == GBB_INPUT_CLOCK_SIZE_V1);
    for (size_t i = 0u; i < sizeof(big.tail); ++i) REQUIRE(big.tail[i] == SENTINEL);

    gbb_destroy(machine);
    free(rom);
    return 0;
}

static int case_queue(void) {
    size_t rom_size = 0u;
    uint8_t *rom = make_rom(&rom_size);
    REQUIRE(rom != NULL);
    gbb_instance *machine = new_machine(rom, rom_size);
    REQUIRE(machine != NULL);

    /* A fresh instance has nothing queued, and the cursor sits at now. */
    gbb_input_clock clock;
    REQUIRE(read_clock(machine, &clock));
    REQUIRE(clock.queued_count == 0u);
    REQUIRE(clock.last_queued_half_dots == clock.now_half_dots);

    /* Run a frame so now is not zero, then re-read. */
    REQUIRE(gbb_run(machine, FRAME_HALF_DOTS, NULL, 0u).reason == GBB_STOP_BUDGET);
    REQUIRE(read_clock(machine, &clock));
    const uint64_t t = clock.now_half_dots;
    REQUIRE(t > 0u); /* a run stops at an instruction boundary, so it may fall just short of the budget */
    REQUIRE(clock.queued_count == 0u);
    REQUIRE(clock.last_queued_half_dots == t);

    /* Three queued events: the count and the last time follow; now does not move. */
    const gbb_input_event events[3] = {press(t + 10u, GBB_BUTTON_A), release(t + 20u, GBB_BUTTON_A),
                                       press(t + 30u, GBB_BUTTON_B)};
    REQUIRE(gbb_queue_events(machine, events, 3u) == GBB_OK);
    REQUIRE(read_clock(machine, &clock));
    REQUIRE(clock.queued_count == 3u);
    REQUIRE(clock.last_queued_half_dots == t + 30u);
    REQUIRE(clock.now_half_dots == t);

    /* The getter is read-only: the saved state is byte-identical after repeated reads. */
    size_t state_size = 0u;
    REQUIRE(gbb_state_size(machine, &state_size) == GBB_OK);
    uint8_t *before = malloc(state_size);
    uint8_t *after = malloc(state_size);
    REQUIRE(before != NULL && after != NULL);
    REQUIRE(gbb_save_state(machine, before, state_size) == GBB_OK);
    REQUIRE(read_clock(machine, &clock));
    REQUIRE(read_clock(machine, &clock));
    REQUIRE(gbb_save_state(machine, after, state_size) == GBB_OK);
    REQUIRE(memcmp(before, after, state_size) == 0);
    free(before);
    free(after);

    /* Once the events are consumed the queue is empty and the cursor is back at now. */
    REQUIRE(gbb_run(machine, FRAME_HALF_DOTS, NULL, 0u).reason == GBB_STOP_BUDGET);
    REQUIRE(read_clock(machine, &clock));
    REQUIRE(clock.queued_count == 0u);
    REQUIRE(clock.now_half_dots > t + 30u);
    REQUIRE(clock.last_queued_half_dots == clock.now_half_dots);

    gbb_destroy(machine);
    free(rom);
    return 0;
}

static int case_after_load(void) {
    size_t rom_size = 0u;
    uint8_t *rom = make_rom(&rom_size);
    REQUIRE(rom != NULL);
    gbb_instance *a = new_machine(rom, rom_size);
    gbb_instance *b = new_machine(rom, rom_size);
    REQUIRE(a != NULL && b != NULL);

    /* S_early: time T1 with two events still queued. */
    gbb_input_clock clock;
    REQUIRE(gbb_run(a, FRAME_HALF_DOTS, NULL, 0u).reason == GBB_STOP_BUDGET);
    REQUIRE(read_clock(a, &clock));
    const uint64_t t1 = clock.now_half_dots;
    const gbb_input_event early_events[2] = {press(t1 + 1000u, GBB_BUTTON_A),
                                             release(t1 + 2000u, GBB_BUTTON_A)};
    REQUIRE(gbb_queue_events(a, early_events, 2u) == GBB_OK);
    size_t state_size = 0u;
    REQUIRE(gbb_state_size(a, &state_size) == GBB_OK);
    uint8_t *early = malloc(state_size);
    uint8_t *late = malloc(state_size);
    REQUIRE(early != NULL && late != NULL);
    REQUIRE(gbb_save_state(a, early, state_size) == GBB_OK);

    /* S_late: 600 frames later; the queued events were consumed. */
    REQUIRE(gbb_run(a, 600u * FRAME_HALF_DOTS, NULL, 0u).reason == GBB_STOP_BUDGET);
    REQUIRE(read_clock(a, &clock));
    const uint64_t t2 = clock.now_half_dots;
    REQUIRE(t2 > t1 + 599u * FRAME_HALF_DOTS);
    REQUIRE(clock.queued_count == 0u);
    size_t late_size = 0u;
    REQUIRE(gbb_state_size(a, &late_size) == GBB_OK);
    REQUIRE(late_size == state_size);
    REQUIRE(gbb_save_state(a, late, late_size) == GBB_OK);

    /* Later-time load: b sits at T1 with the early queue, then S_late arrives. */
    REQUIRE(gbb_load_state(b, early, state_size) == GBB_OK);
    REQUIRE(read_clock(b, &clock));
    REQUIRE(clock.now_half_dots == t1);
    REQUIRE(clock.queued_count == 2u);
    REQUIRE(clock.last_queued_half_dots == t1 + 2000u);
    REQUIRE(gbb_load_state(b, late, state_size) == GBB_OK);
    REQUIRE(read_clock(b, &clock));
    REQUIRE(clock.now_half_dots == t2);
    REQUIRE(clock.queued_count == 0u);
    REQUIRE(clock.last_queued_half_dots == t2);
    {
        /* The stale pre-load cursor (the early queue's last time) is refused; max(now, last) is not. */
        const gbb_input_event stale = press(t1 + 2000u, GBB_BUTTON_B);
        const gbb_input_event stale_now = press(t1, GBB_BUTTON_B);
        REQUIRE(gbb_queue_events(b, &stale, 1u) == GBB_INVALID_EVENT);
        REQUIRE(gbb_queue_events(b, &stale_now, 1u) == GBB_INVALID_EVENT);
        uint64_t anchor = clock.now_half_dots > clock.last_queued_half_dots ? clock.now_half_dots
                                                                            : clock.last_queued_half_dots;
        const gbb_input_event fresh = press(anchor, GBB_BUTTON_B);
        REQUIRE(gbb_queue_events(b, &fresh, 1u) == GBB_OK);
        REQUIRE(read_clock(b, &clock));
        REQUIRE(clock.queued_count == 1u);
        REQUIRE(clock.last_queued_half_dots == anchor);
    }

    /* Earlier-time load: a sits at T2 with an empty queue, then S_early arrives. */
    REQUIRE(gbb_load_state(a, early, state_size) == GBB_OK);
    REQUIRE(read_clock(a, &clock));
    REQUIRE(clock.now_half_dots == t1);
    REQUIRE(clock.queued_count == 2u);
    REQUIRE(clock.last_queued_half_dots == t1 + 2000u);
    {
        /* An event before the restored queue's last time is unordered; at max(now, last) it is accepted. */
        const gbb_input_event unordered = press(t1 + 1999u, GBB_BUTTON_B);
        REQUIRE(gbb_queue_events(a, &unordered, 1u) == GBB_INVALID_EVENT);
        uint64_t anchor = clock.now_half_dots > clock.last_queued_half_dots ? clock.now_half_dots
                                                                            : clock.last_queued_half_dots;
        const gbb_input_event fresh = press(anchor, GBB_BUTTON_B);
        REQUIRE(gbb_queue_events(a, &fresh, 1u) == GBB_OK);
        REQUIRE(read_clock(a, &clock));
        REQUIRE(clock.queued_count == 3u);
        REQUIRE(clock.last_queued_half_dots == anchor);
    }

    free(early);
    free(late);
    gbb_destroy(a);
    gbb_destroy(b);
    free(rom);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: test_input_clock <handshake|queue|after_load>\n");
        return 2;
    }
    g_case = argv[1];
    int failed;
    if (strcmp(argv[1], "handshake") == 0) failed = case_handshake();
    else if (strcmp(argv[1], "queue") == 0) failed = case_queue();
    else if (strcmp(argv[1], "after_load") == 0) failed = case_after_load();
    else {
        fprintf(stderr, "unknown case: %s\n", argv[1]);
        return 2;
    }
    if (failed) return 1;
    printf("PASS %s\n", argv[1]);
    return 0;
}
