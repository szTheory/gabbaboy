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

static gbb_instance *serial_machine(void) {
    const uint8_t p[] = {
        0x3E,0x00,0xE0,0x01, 0x3E,0x80,0xE0,0x02,
        0xF0,0x01,0xEA,0x00,0xC0, 0xF0,0x02,0xEA,0x01,0xC0,
        0xF0,0x0F,0xEA,0x02,0xC0
    };
    gbb_instance *m = load_program(p, sizeof(p));
    if (m == NULL) return NULL;
    gbb_run_result r = gbb_run(m, 80, NULL, 0);
    if (r.reason != GBB_STOP_BUDGET || r.consumed_half_dots != 80) {
        gbb_destroy(m);
        return NULL;
    }
    return m;
}

static void fill_serial_edges(gbb_input_event edges[8], uint64_t at) {
    static const uint8_t bits[8] = {1,0,1,0,0,1,0,1};
    for (size_t i = 0; i < 8; ++i)
        edges[i] = (gbb_input_event){at, GBB_INPUT_SERIAL_EDGE, bits[i]};
}

static int finish_serial(gbb_instance *m, uint64_t first_budget, int partitioned) {
    gbb_trace_record trace[8] = {{0}};
    if (!partitioned) {
        gbb_run_result r = gbb_run(m, first_budget, trace, 8);
        if (r.reason != GBB_STOP_BUDGET || r.consumed_half_dots != first_budget) return 1;
    } else {
        static const uint64_t parts[] = {24,32,24,32,24,32};
        uint64_t consumed = 0;
        for (size_t i = 0; i < sizeof(parts) / sizeof(parts[0]); ++i) {
            gbb_run_result r = gbb_run(m, parts[i], trace, 8);
            if (r.reason != GBB_STOP_BUDGET || r.consumed_half_dots != parts[i]) return 1;
            consumed += r.consumed_half_dots;
        }
        if (consumed != first_budget) return 1;
    }
    if (gbb_peek_ram(m, 0xC000) != 0xA5 ||
        (gbb_peek_ram(m, 0xC001) & 0x80u) != 0 ||
        (gbb_peek_ram(m, 0xC002) & 0x08u) == 0) return 1;
    return 0;
}

static int event_queue_order(void) {
    gbb_instance *m = serial_machine(); REQUIRE(m != NULL);
    gbb_input_event edges[8]; fill_serial_edges(edges, 80);
    REQUIRE(gbb_queue_events(m, edges, 8) == GBB_OK);
    REQUIRE(finish_serial(m, 168, 0) == 0);
    gbb_destroy(m);
    return 0;
}

static int event_queue_atomic(void) {
    const uint8_t p[] = {0x10,0x00,0x00};
    gbb_instance *m = load_program(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_run_result r = gbb_run(m, 8, NULL, 0);
    REQUIRE(r.reason == GBB_STOP_STOPPED && r.consumed_half_dots == 8);
    const gbb_input_event existing = {40, GBB_INPUT_STOP_WAKE, 1};
    const gbb_input_event descending[] = {
        {20, GBB_INPUT_STOP_WAKE, 1}, {19, GBB_INPUT_STOP_WAKE, 1}
    };
    REQUIRE(gbb_queue_events(m, &existing, 1) == GBB_OK);
    REQUIRE(gbb_queue_events(m, descending, 2) == GBB_INVALID_EVENT);
    REQUIRE(gbb_queue_events(m, NULL, 0) == GBB_OK);
    REQUIRE(gbb_queue_events(m, NULL, 1) == GBB_INVALID_ARGUMENT);
    r = gbb_run(m, 32, NULL, 0);
    REQUIRE(r.reason == GBB_STOP_NO_PROGRESS && r.consumed_half_dots == 32);
    REQUIRE(gbb_reset(m) == GBB_OK);
    r = gbb_run(m, 8, NULL, 0);
    REQUIRE(r.reason == GBB_STOP_STOPPED);
    gbb_input_event batch[64];
    for (size_t i = 0; i < 64; ++i) batch[i] = (gbb_input_event){100, GBB_INPUT_STOP_WAKE, 1};
    REQUIRE(gbb_queue_events(m, batch, 64) == GBB_OK);
    REQUIRE(gbb_queue_events(m, batch, 1) == GBB_EVENT_QUEUE_FULL);
    gbb_destroy(m);
    return 0;
}

static int event_partition(void) {
    gbb_instance *whole = serial_machine(); REQUIRE(whole != NULL);
    gbb_instance *parts = serial_machine(); REQUIRE(parts != NULL);
    gbb_input_event whole_edges[8], part_edges[8];
    fill_serial_edges(whole_edges, 84);
    fill_serial_edges(part_edges, 84);
    REQUIRE(gbb_queue_events(whole, whole_edges, 8) == GBB_OK);
    REQUIRE(gbb_queue_events(parts, part_edges, 8) == GBB_OK);
    gbb_trace_record whole_trace[8] = {{0}}, part_trace[8] = {{0}};
    gbb_run_result r = gbb_run(whole, 168, whole_trace, 8);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 168 && r.trace_count == 6);
    static const uint64_t partitions[] = {24,32,24,32,24,32};
    size_t part_count = 0;
    uint64_t total = 0;
    for (size_t i = 0; i < sizeof(partitions) / sizeof(partitions[0]); ++i) {
        r = gbb_run(parts, partitions[i], part_trace + part_count, 8 - part_count);
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == partitions[i] && r.trace_count == 1);
        part_count += r.trace_count;
        total += r.consumed_half_dots;
    }
    REQUIRE(total == 168 && part_count == 6);
    REQUIRE(memcmp(whole_trace, part_trace, 6 * sizeof(whole_trace[0])) == 0);
    REQUIRE(gbb_peek_ram(whole, 0xC000) == gbb_peek_ram(parts, 0xC000));
    REQUIRE(gbb_peek_ram(whole, 0xC001) == gbb_peek_ram(parts, 0xC001));
    REQUIRE(gbb_peek_ram(whole, 0xC002) == gbb_peek_ram(parts, 0xC002));
    gbb_destroy(whole); gbb_destroy(parts);
    return 0;
}

static int event_deadline_inside(void) {
    gbb_instance *m = serial_machine(); REQUIRE(m != NULL);
    gbb_input_event edges[8]; fill_serial_edges(edges, 84);
    REQUIRE(gbb_queue_events(m, edges, 8) == GBB_OK);
    REQUIRE(finish_serial(m, 168, 0) == 0);
    gbb_destroy(m);
    return 0;
}

static int event_external_serial_edges(void) {
    gbb_instance *m = serial_machine(); REQUIRE(m != NULL);
    gbb_input_event edges[8];
    fill_serial_edges(edges, 80);
    for (size_t i = 0; i < 8; ++i) edges[i].at_half_dots += i;
    REQUIRE(gbb_queue_events(m, edges, 8) == GBB_OK);
    REQUIRE(finish_serial(m, 168, 0) == 0);
    gbb_destroy(m);
    return 0;
}

static int event_time_overflow(void) {
    const uint8_t p[] = {0x10,0x00,0xF0,0x04};
    gbb_instance *m = load_program(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_run_result r = gbb_run(m, 8, NULL, 0);
    REQUIRE(r.reason == GBB_STOP_STOPPED);
    const gbb_input_event wake = {UINT64_MAX, GBB_INPUT_STOP_WAKE, 1};
    REQUIRE(gbb_queue_events(m, &wake, 1) == GBB_OK);
    r = gbb_run(m, UINT64_MAX - 8u, NULL, 0);
    REQUIRE(r.reason == GBB_STOP_NO_PROGRESS && r.consumed_half_dots == UINT64_MAX - 8u);
    const gbb_input_event past = {UINT64_MAX - 1u, GBB_INPUT_SERIAL_EDGE, 1};
    REQUIRE(gbb_queue_events(m, &past, 1) == GBB_INVALID_EVENT);
    r = gbb_run(m, 32, NULL, 0);
    REQUIRE(r.reason == GBB_STOP_INVALID_STATE && r.consumed_half_dots == 0);
    gbb_destroy(m);
    return 0;
}

static int run_output_capacity(void) {
    const uint8_t p[] = {0x00,0x00,0x00};
    gbb_instance *m = load_program(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_trace_record trace[2] = {{0}};
    trace[1].pc = 0xBEEF;
    gbb_run_result r = gbb_run(m, 64, trace, 1);
    REQUIRE(r.reason == GBB_STOP_OUTPUT_FULL && r.trace_count == 1 && r.consumed_half_dots == 8);
    REQUIRE(trace[1].pc == 0xBEEF);
    r = gbb_run(m, 8, trace, 1);
    REQUIRE(r.trace_count == 1 && trace[0].pc == 0x101);
    gbb_destroy(m);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    active_case = argv[1];
    if (strcmp(argv[1], "event_stop_wake") == 0) return event_stop_wake();
    if (strcmp(argv[1], "event_boundary") == 0) return event_boundary();
    if (strcmp(argv[1], "event_queue_order") == 0) return event_queue_order();
    if (strcmp(argv[1], "event_queue_atomic") == 0) return event_queue_atomic();
    if (strcmp(argv[1], "event_partition") == 0) return event_partition();
    if (strcmp(argv[1], "event_deadline_inside") == 0) return event_deadline_inside();
    if (strcmp(argv[1], "event_external_serial_edges") == 0) return event_external_serial_edges();
    if (strcmp(argv[1], "event_time_overflow") == 0) return event_time_overflow();
    if (strcmp(argv[1], "run_output_capacity") == 0) return run_output_capacity();
    return 2;
}
