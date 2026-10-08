#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <string.h>

static const char *active_case = "unknown";
#define REQUIRE(x) do { if (!(x)) { \
    printf("TAP version 13\n1..1\nnot ok 1 - %s\n  ---\n  message: assertion failed\n  ...\n", active_case); \
    fflush(stdout); fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

static void make_rom(uint8_t rom[32768], const uint8_t *program, size_t size) {
    memset(rom, 0, 32768);
    memcpy(rom + 0x100, program, size);
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14c; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14d] = checksum;
}

static gbb_instance *load_program(const uint8_t *program, size_t size) {
    uint8_t rom[32768];
    make_rom(rom, program, size);
    gbb_instance *m = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &m) != GBB_OK ||
        gbb_load_rom(m, rom, sizeof(rom)) != GBB_OK) {
        gbb_destroy(m);
        return NULL;
    }
    return m;
}

static size_t build_probe(uint8_t *program, const uint8_t *selections,
                          const uint16_t *destinations, size_t count) {
    size_t n = 0;
    for (size_t i = 0; i < count; ++i) {
        program[n++] = 0x3E; program[n++] = selections[i]; /* LD A,n */
        program[n++] = 0xE0; program[n++] = 0x00;         /* LDH (FF00),A */
        unsigned reads = (selections[i] & 0x20u) == 0 ? 6u :
                         ((selections[i] & 0x10u) == 0 ? 2u : 1u);
        for (unsigned read = 0; read < reads; ++read) {
            program[n++] = 0xF0; program[n++] = 0x00;     /* LDH A,(FF00) */
        }
        program[n++] = 0xEA; program[n++] = (uint8_t)destinations[i];
        program[n++] = (uint8_t)(destinations[i] >> 8);  /* LD (nn),A */
    }
    return n;
}

static uint64_t probe_cost(const uint8_t *selections, size_t count) {
    uint64_t half_dots = 0;
    for (size_t i = 0; i < count; ++i) {
        unsigned reads = (selections[i] & 0x20u) == 0 ? 6u :
                         ((selections[i] & 0x10u) == 0 ? 2u : 1u);
        half_dots += 16u + 24u + (uint64_t)reads * 24u + 32u;
    }
    return half_dots;
}

static int run_exact(gbb_instance *m, uint64_t half_dots) {
    gbb_run_result r = gbb_run(m, half_dots, NULL, 0);
    return r.reason != GBB_STOP_BUDGET || r.consumed_half_dots != half_dots;
}

static uint8_t expected_selected_value(uint8_t selection, uint8_t button) {
    uint8_t low = 0x0F;
    if ((selection & 0x10u) == 0 && button < 4u)
        low = (uint8_t)(low & (uint8_t)~(1u << button));
    if ((selection & 0x20u) == 0 && button >= 4u)
        low = (uint8_t)(low & (uint8_t)~(1u << (button - 4u)));
    return (uint8_t)(0xC0u | selection | low);
}

static int joypad_selection(void) {
    static const uint8_t selections[] = {0x20, 0x10, 0x00, 0x30};
    static const uint16_t destinations[] = {0xC000, 0xC001, 0xC002, 0xC003};
    uint8_t program[64];
    size_t size = build_probe(program, selections, destinations, 4);

    for (uint8_t button = 0; button < 8; ++button) {
        gbb_instance *m = load_program(program, size); REQUIRE(m != NULL);
        const gbb_input_event press = {0, GBB_INPUT_BUTTON_PRESS, button};
        REQUIRE(gbb_queue_events(m, &press, 1) == GBB_OK);
        REQUIRE(run_exact(m, probe_cost(selections, 4)) == 0);
        for (size_t i = 0; i < 4; ++i)
            REQUIRE(gbb_peek_ram(m, destinations[i]) ==
                    expected_selected_value(selections[i], button));
        gbb_destroy(m);
    }

    gbb_instance *all = load_program(program, size); REQUIRE(all != NULL);
    gbb_input_event presses[8];
    for (uint8_t button = 0; button < 8; ++button)
        presses[button] = (gbb_input_event){0, GBB_INPUT_BUTTON_PRESS, button};
    REQUIRE(gbb_queue_events(all, presses, 8) == GBB_OK);
    REQUIRE(run_exact(all, probe_cost(selections, 4)) == 0);
    REQUIRE(gbb_peek_ram(all, 0xC000) == 0xE0);
    REQUIRE(gbb_peek_ram(all, 0xC001) == 0xD0);
    REQUIRE(gbb_peek_ram(all, 0xC002) == 0xC0);
    REQUIRE(gbb_peek_ram(all, 0xC003) == 0xFF);
    gbb_destroy(all);

    const uint8_t one_selection[] = {0x10};
    const uint16_t one_destination[] = {0xC000};
    size = build_probe(program, one_selection, one_destination, 1);
    gbb_instance *first = load_program(program, size); REQUIRE(first != NULL);
    gbb_instance *second = load_program(program, size); REQUIRE(second != NULL);
    const gbb_input_event press_a = {0, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A};
    REQUIRE(gbb_queue_events(first, &press_a, 1) == GBB_OK);
    REQUIRE(run_exact(first, probe_cost(one_selection, 1)) == 0 &&
            run_exact(second, probe_cost(one_selection, 1)) == 0);
    REQUIRE(gbb_peek_ram(first, 0xC000) == 0xDE);
    REQUIRE(gbb_peek_ram(second, 0xC000) == 0xDF);
    gbb_destroy(first); gbb_destroy(second);
    return 0;
}

static int joypad_queue_atomic(void) {
    const uint8_t selection[] = {0x10};
    const uint16_t destination[] = {0xC000};
    uint8_t probe[32];
    size_t probe_size = build_probe(probe, selection, destination, 1);

    gbb_instance *invalid = load_program(probe, probe_size); REQUIRE(invalid != NULL);
    const gbb_input_event malformed[] = {
        {0, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A},
        {0, GBB_INPUT_BUTTON_PRESS, 8}
    };
    REQUIRE(gbb_queue_events(invalid, malformed, 2) == GBB_INVALID_EVENT);
    REQUIRE(run_exact(invalid, probe_cost(selection, 1)) == 0);
    REQUIRE(gbb_peek_ram(invalid, 0xC000) == 0xDF);
    gbb_destroy(invalid);

    gbb_instance *past = load_program(probe, probe_size); REQUIRE(past != NULL);
    REQUIRE(run_exact(past, 16) == 0);
    const gbb_input_event stale = {0, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A};
    REQUIRE(gbb_queue_events(past, &stale, 1) == GBB_INVALID_EVENT);
    REQUIRE(run_exact(past, probe_cost(selection, 1) - 16u) == 0);
    REQUIRE(gbb_peek_ram(past, 0xC000) == 0xDF);
    gbb_destroy(past);

    uint8_t delayed[256];
    memset(delayed, 0x00, 25); /* 25 NOPs place the probe after half-dot 200. */
    const size_t delayed_probe_size = build_probe(delayed + 25, selection, destination, 1);
    gbb_instance *overflow = load_program(delayed, 25 + delayed_probe_size);
    REQUIRE(overflow != NULL);
    gbb_input_event fill[63];
    for (size_t i = 0; i < 63; ++i)
        fill[i] = (gbb_input_event){200, GBB_INPUT_STOP_WAKE, 1};
    REQUIRE(gbb_queue_events(overflow, fill, 63) == GBB_OK);
    const gbb_input_event too_many[] = {
        {200, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A},
        {200, GBB_INPUT_BUTTON_RELEASE, GBB_BUTTON_A}
    };
    REQUIRE(gbb_queue_events(overflow, too_many, 2) == GBB_EVENT_QUEUE_FULL);
    REQUIRE(run_exact(overflow, 200u + probe_cost(selection, 1)) == 0);
    REQUIRE(gbb_peek_ram(overflow, 0xC000) == 0xDF);
    gbb_destroy(overflow);

    const uint8_t direction[] = {0x20};
    probe_size = build_probe(probe, direction, destination, 1);
    gbb_instance *full = load_program(probe, probe_size); REQUIRE(full != NULL);
    gbb_input_event full_batch[64];
    for (size_t i = 0; i < 64; ++i)
        full_batch[i] = (gbb_input_event){0, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_RIGHT};
    REQUIRE(gbb_queue_events(full, full_batch, 64) == GBB_OK);
    REQUIRE(gbb_queue_events(full, full_batch, 1) == GBB_EVENT_QUEUE_FULL);
    REQUIRE(gbb_reset(full) == GBB_OK);
    REQUIRE(run_exact(full, probe_cost(direction, 1)) == 0);
    REQUIRE(gbb_peek_ram(full, 0xC000) == 0xEF);
    gbb_destroy(full);
    return 0;
}

static int joypad_equal_time(void) {
    const uint8_t selection[] = {0x10};
    const uint16_t destination[] = {0xC000};
    uint8_t program[32];
    const size_t size = build_probe(program, selection, destination, 1);
    gbb_instance *released = load_program(program, size); REQUIRE(released != NULL);
    const gbb_input_event press_then_release[] = {
        {0, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A},
        {0, GBB_INPUT_BUTTON_RELEASE, GBB_BUTTON_A}
    };
    REQUIRE(gbb_queue_events(released, press_then_release, 2) == GBB_OK);
    REQUIRE(run_exact(released, probe_cost(selection, 1)) == 0);
    REQUIRE(gbb_peek_ram(released, 0xC000) == 0xDF);

    gbb_instance *pressed = load_program(program, size); REQUIRE(pressed != NULL);
    const gbb_input_event release_then_press[] = {
        {0, GBB_INPUT_BUTTON_RELEASE, GBB_BUTTON_A},
        {0, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A}
    };
    REQUIRE(gbb_queue_events(pressed, release_then_press, 2) == GBB_OK);
    REQUIRE(run_exact(pressed, probe_cost(selection, 1)) == 0);
    REQUIRE(gbb_peek_ram(pressed, 0xC000) == 0xDE);
    gbb_destroy(released); gbb_destroy(pressed);
    return 0;
}

static int joypad_partition(void) {
    const uint8_t program[] = {
        0x3E,0x10, 0xE0,0x00,
        0xF0,0x00, 0xF0,0x00, 0xF0,0x00, 0xF0,0x00, 0xF0,0x00, 0xF0,0x00,
        0xEA,0x00,0xC0, 0xF0,0x00, 0xEA,0x01,0xC0
    };
    gbb_instance *whole = load_program(program, sizeof(program)); REQUIRE(whole != NULL);
    gbb_instance *parts = load_program(program, sizeof(program)); REQUIRE(parts != NULL);
    const gbb_input_event whole_events[] = {
        {160, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A},
        {184, GBB_INPUT_BUTTON_RELEASE, GBB_BUTTON_A}
    };
    const gbb_input_event part_events[] = {
        {160, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A},
        {184, GBB_INPUT_BUTTON_RELEASE, GBB_BUTTON_A}
    };
    REQUIRE(gbb_queue_events(whole, whole_events, 2) == GBB_OK);
    REQUIRE(gbb_queue_events(parts, part_events, 2) == GBB_OK);
    REQUIRE(run_exact(whole, 272) == 0);
    static const uint64_t partitions[] = {160, 56, 56};
    for (size_t i = 0; i < sizeof(partitions) / sizeof(partitions[0]); ++i)
        REQUIRE(run_exact(parts, partitions[i]) == 0);
    REQUIRE(gbb_peek_ram(whole, 0xC000) == 0xDE);
    REQUIRE(gbb_peek_ram(whole, 0xC001) == 0xDF);
    REQUIRE(gbb_peek_ram(parts, 0xC000) == gbb_peek_ram(whole, 0xC000));
    REQUIRE(gbb_peek_ram(parts, 0xC001) == gbb_peek_ram(whole, 0xC001));
    gbb_destroy(whole); gbb_destroy(parts);
    return 0;
}

static int joypad_interrupt(void) {
    /* Select each row, then accept an event after the guest write. The guest
       stores FF0F so these assertions observe the public CPU-visible path. */
    for (uint8_t button = 0; button < 8; ++button) {
        uint8_t program[48] = {0x3E, (uint8_t)(button < 4 ? 0x20 : 0x10),
                               0xE0, 0x00};
        size_t n = 4;
        for (unsigned i = 0; i < 12; ++i) program[n++] = 0x00;
        program[n++] = 0xF0; program[n++] = 0x0F;
        program[n++] = 0xEA; program[n++] = 0x00; program[n++] = 0xC0;
        gbb_instance *m = load_program(program, n); REQUIRE(m != NULL);
        const gbb_input_event press = {100, GBB_INPUT_BUTTON_PRESS, button};
        REQUIRE(gbb_queue_events(m, &press, 1) == GBB_OK);
        REQUIRE(run_exact(m, 16u + 24u + 12u * 8u + 24u + 32u) == 0);
        REQUIRE(gbb_peek_ram(m, 0xC000) == 0xF0u);
        gbb_destroy(m);
    }

    /* A press on an unselected row and a release do not request IF.4. */
    const uint8_t program[] = {
        0x3E,0x10, 0xE0,0x00,
        0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
        0xF0,0x0F, 0xEA,0x00,0xC0
    };
    gbb_instance *m = load_program(program, sizeof(program)); REQUIRE(m != NULL);
    const gbb_input_event unselected = {100, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_RIGHT};
    REQUIRE(gbb_queue_events(m, &unselected, 1) == GBB_OK);
    REQUIRE(run_exact(m, 16u + 24u + 12u * 8u + 24u + 32u) == 0);
    REQUIRE(gbb_peek_ram(m, 0xC000) == 0xE0u);
    gbb_destroy(m);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    active_case = argv[1];
    if (strcmp(argv[1], "joypad_selection") == 0) return joypad_selection();
    if (strcmp(argv[1], "joypad_queue_atomic") == 0) return joypad_queue_atomic();
    if (strcmp(argv[1], "joypad_equal_time") == 0) return joypad_equal_time();
    if (strcmp(argv[1], "joypad_partition") == 0) return joypad_partition();
    if (strcmp(argv[1], "joypad_interrupt") == 0) return joypad_interrupt();
    return 2;
}
