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
    for (size_t i = 0x134; i <= 0x14c; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
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

static int event_stop_wake(void) {
    const uint8_t p[] = {0x10,0x00,0xF0,0x04,0xEA,0x00,0xC0};
    gbb_instance *m = load_program(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_trace_record trace[2] = {{0}};
    gbb_run_result r = gbb_run(m, 8, trace, 2);
    REQUIRE(r.reason == GBB_STOP_STOPPED && r.consumed_half_dots == 8 && r.trace_count == 1);
    r = gbb_run(m, 0, trace, 2);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 0 && r.trace_count == 0);
    r = gbb_run(m, 24, trace, 2);
    REQUIRE(r.reason == GBB_STOP_STOPPED && r.consumed_half_dots == 24 && r.trace_count == 0);
    const gbb_input_event wake = {44, GBB_INPUT_STOP_WAKE, 1};
    REQUIRE(gbb_queue_events(m, &wake, 1) == GBB_OK);
    r = gbb_run(m, 12, trace, 2);
    REQUIRE(r.reason == GBB_STOP_NO_PROGRESS && r.consumed_half_dots == 12 && r.trace_count == 0);
    r = gbb_run(m, 24, trace, 2);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 24 && r.trace_count == 1);
    r = gbb_run(m, 32, trace, 2);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 32);
    REQUIRE(gbb_peek_ram(m, 0xC000) == 0);
    gbb_destroy(m);
    return 0;
}

static int event_boundary(void) {
    const uint8_t p[] = {0x00};
    gbb_instance *m = load_program(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_run_result r = gbb_run(m, 7, NULL, 0);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 0);
    r = gbb_run(m, 8, NULL, 0);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 8);
    gbb_destroy(m);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    active_case = argv[1];
    if (strcmp(argv[1], "event_stop_wake") == 0) return event_stop_wake();
    if (strcmp(argv[1], "event_boundary") == 0) return event_boundary();
    return 2;
}
