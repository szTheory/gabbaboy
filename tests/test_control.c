#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <string.h>

typedef struct {
    uint64_t time_half_dots;
    uint16_t address;
    uint8_t access;
    uint8_t value;
} gbb_test_bus_event;
extern void gbb_test_observer_set(gbb_instance *, gbb_test_bus_event *, size_t);
extern size_t gbb_test_observer_count(const gbb_instance *);

static const char *active_case = "unknown";
#define REQUIRE(x) do { if (!(x)) { \
    printf("TAP version 13\n1..1\nnot ok 1 - %s\n  ---\n  message: \"assertion failed at %s:%d\"\n  ...\n", active_case, __FILE__, __LINE__); \
    return 1; \
} } while (0)

static void make_rom(uint8_t rom[32768], const uint8_t *program, size_t size) {
    memset(rom, 0, 32768);
    memcpy(rom + 0x100, program, size);
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14c; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14d] = checksum;
}

static int interrupt_entry(void) {
    uint8_t rom[32768];
    const uint8_t program[] = {0x3e,0x01,0xea,0xff,0xff,0xea,0x0f,0xff,0xfb,0x00};
    make_rom(rom, program, sizeof(program));
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    gbb_test_bus_event events[8] = {{0}};
    gbb_test_observer_set(m, events, 8);
    gbb_trace_record trace[8] = {{0}};
    gbb_run_result r = gbb_run(m, 96, trace, 8);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 96);
    REQUIRE(trace[4].pc == 0x0109 && trace[4].time_half_dots == 88);
    REQUIRE(gbb_test_observer_count(m) == 2);
    REQUIRE(events[0].time_half_dots == 40 && events[0].address == 0xffff && events[0].value == 1);
    REQUIRE(events[1].time_half_dots == 72 && events[1].address == 0xff0f && events[1].value == 1);
    r = gbb_run(m, 39, trace, 8);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 0 && r.trace_count == 0);
    REQUIRE(gbb_test_observer_count(m) == 2);
    r = gbb_run(m, 40, trace, 8);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 40 && r.trace_count == 0);
    REQUIRE(gbb_test_observer_count(m) == 5);
    REQUIRE(events[2].time_half_dots == 104 && events[2].address == 0xff0f && events[2].value == 0xe0);
    REQUIRE(events[3].time_half_dots == 112 && events[3].address == 0xfffd && events[3].value == 0x01);
    REQUIRE(events[4].time_half_dots == 120 && events[4].address == 0xfffc && events[4].value == 0x0a);
    gbb_destroy(m);
    return 0;
}

static int interrupt_budget(void) { return interrupt_entry(); }

static gbb_instance *make_machine(const uint8_t *program, size_t size) {
    uint8_t rom[32768];
    make_rom(rom, program, size);
    gbb_instance *m = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &m) != GBB_OK || gbb_load_rom(m, rom, sizeof(rom)) != GBB_OK) {
        gbb_destroy(m);
        return NULL;
    }
    return m;
}

static int interrupt_ei_delay(void) {
    const uint8_t p[] = {0x3e,1,0xea,0xff,0xff,0xea,0x0f,0xff,0xfb,0x04,0x00};
    gbb_instance *m = make_machine(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_trace_record t[8] = {{0}};
    gbb_run_result r = gbb_run(m, 96, t, 8);
    REQUIRE(r.consumed_half_dots == 96 && r.trace_count == 6);
    REQUIRE(t[5].pc == 0x10a && t[5].b == 1);
    r = gbb_run(m, 40, t, 8);
    REQUIRE(r.consumed_half_dots == 40 && r.trace_count == 0);
    r = gbb_run(m, 8, t, 8);
    REQUIRE(r.trace_count == 1 && t[0].pc == 0x40);
    gbb_destroy(m); return 0;
}

static int interrupt_priority(void) {
    const uint8_t p[] = {0x3e,3,0xea,0xff,0xff,0xea,0x0f,0xff,0xfb,0x00};
    gbb_instance *m = make_machine(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_test_bus_event e[12] = {{0}}; gbb_test_observer_set(m, e, 12);
    gbb_trace_record t[12] = {{0}};
    gbb_run_result r = gbb_run(m, 96, t, 12); REQUIRE(r.consumed_half_dots == 96);
    r = gbb_run(m, 40, t, 12); REQUIRE(r.consumed_half_dots == 40);
    r = gbb_run(m, 64, t, 12); REQUIRE(r.consumed_half_dots == 64);
    REQUIRE(gbb_peek_ram(m, 0xc000) == 0xe2);
    REQUIRE(t[0].pc == 0x40);
    gbb_destroy(m); return 0;
}

static int halt_idle(void) {
    const uint8_t p[] = {0x76,0x04,0x00}; gbb_instance *m = make_machine(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_trace_record t[2] = {{0}}; gbb_run_result r = gbb_run(m, 8, t, 2);
    REQUIRE(r.reason == (gbb_stop_reason)6 && r.consumed_half_dots == 8 && r.trace_count == 1);
    r = gbb_run(m, 16, t, 2); REQUIRE(r.reason == (gbb_stop_reason)6 && r.consumed_half_dots == 16);
    gbb_destroy(m); return 0;
}

static int halt_bug(void) {
    const uint8_t p[] = {0x3e,1,0xea,0xff,0xff,0xea,0x0f,0xff,0x76,0x04,0x00};
    gbb_instance *m = make_machine(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_trace_record t[2] = {{0}}; gbb_run_result r = gbb_run(m, 88, t, 2); REQUIRE(r.consumed_half_dots == 88);
    r = gbb_run(m, 8, t, 2); REQUIRE(r.consumed_half_dots == 8);
    r = gbb_run(m, 8, t, 2); REQUIRE(r.consumed_half_dots == 8 && t[0].pc == 0x109 && t[0].b == 1);
    gbb_destroy(m); return 0;
}

static int stop_wait(void) {
    const uint8_t p[] = {0x10,0x00,0x04}; gbb_instance *m = make_machine(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_trace_record t[2] = {{0}}; gbb_run_result r = gbb_run(m, 8, t, 2);
    REQUIRE(r.reason == (gbb_stop_reason)7 && r.consumed_half_dots == 8 && t[0].pc == 0x100);
    r = gbb_run(m, 64, t, 2); REQUIRE(r.reason == (gbb_stop_reason)7 && r.consumed_half_dots == 0 && r.trace_count == 0);
    gbb_destroy(m); return 0;
}

static int reset_profile(void) {
    const uint8_t p[] = {0x00}; gbb_instance *m = make_machine(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_trace_record t[1] = {{0}}; gbb_run_result r = gbb_run(m, 8, t, 1); REQUIRE(r.consumed_half_dots == 8);
    REQUIRE(gbb_reset(m) == GBB_OK);
    r = gbb_run(m, 8, t, 1);
    REQUIRE(r.consumed_half_dots == 8 && t[0].time_half_dots == 0 && t[0].pc == 0x100 && t[0].sp == 0xfffe && t[0].a == 1 && t[0].f == 0x80);
    gbb_destroy(m); return 0;
}

static int reset_lockup(void) {
    const uint8_t p[] = {0xd3,0x00}; gbb_instance *m = make_machine(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_run_result r = gbb_run(m, 8, NULL, 0); REQUIRE(r.reason == GBB_STOP_LOCKUP);
    REQUIRE(gbb_reset(m) == GBB_OK);
    r = gbb_run(m, 8, NULL, 0); REQUIRE(r.reason == GBB_STOP_LOCKUP && r.lockup_pc == 0x100 && r.lockup_opcode == 0xd3);
    gbb_destroy(m); return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    active_case = argv[1];
    if (strcmp(argv[1], "interrupt_entry") == 0) return interrupt_entry();
    if (strcmp(argv[1], "interrupt_budget") == 0) return interrupt_budget();
    if (strcmp(argv[1], "interrupt_ei_delay") == 0) return interrupt_ei_delay();
    if (strcmp(argv[1], "interrupt_priority") == 0) return interrupt_priority();
    if (strcmp(argv[1], "halt_idle") == 0) return halt_idle();
    if (strcmp(argv[1], "halt_bug") == 0) return halt_bug();
    if (strcmp(argv[1], "stop_wait") == 0) return stop_wait();
    if (strcmp(argv[1], "reset_profile") == 0) return reset_profile();
    if (strcmp(argv[1], "reset_lockup") == 0) return reset_lockup();
    return 2;
}
