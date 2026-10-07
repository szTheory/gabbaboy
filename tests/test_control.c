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
extern void gbb_test_cpu_snapshot(const gbb_instance *, gbb_trace_record *);

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
    REQUIRE(r.consumed_half_dots == 96 && r.trace_count == 5);
    REQUIRE(t[4].pc == 0x109);
    r = gbb_run(m, 40, t, 8);
    REQUIRE(r.consumed_half_dots == 40 && r.trace_count == 0);
    r = gbb_run(m, 8, t, 8);
    REQUIRE(r.trace_count == 1 && t[0].pc == 0x40 && t[0].b == 1);
    gbb_destroy(m);

    const uint8_t di_program[] = {0x3e,1,0xea,0xff,0xff,0xea,0x0f,0xff,0xfb,0xf3,0x00,0x00};
    m = make_machine(di_program, sizeof(di_program)); REQUIRE(m != NULL);
    r = gbb_run(m, 96, t, 8); REQUIRE(r.consumed_half_dots == 96);
    r = gbb_run(m, 8, t, 8); REQUIRE(r.consumed_half_dots == 8 && r.trace_count == 1 && t[0].pc == 0x10a);
    r = gbb_run(m, 8, t, 8); REQUIRE(r.consumed_half_dots == 8 && r.trace_count == 1 && t[0].pc == 0x10b);
    gbb_destroy(m); return 0;
}

static int interrupt_ei_chain(void) {
    /* IE and IF are armed by t=80. The first EI retires at 88; the
     * second EI retires at 96, when the first enable becomes visible. */
    const uint8_t p[] = {0x3e,1,0xea,0xff,0xff,0xea,0x0f,0xff,0xfb,0xfb,0x00};
    gbb_instance *whole = make_machine(p, sizeof(p)); REQUIRE(whole != NULL);
    gbb_instance *split = make_machine(p, sizeof(p)); REQUIRE(split != NULL);
    gbb_trace_record tw[8] = {{0}}, ts[8] = {{0}}, sw = {0}, ss = {0};
    gbb_run_result r = gbb_run(whole, 136, tw, 8);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 136 && r.trace_count == 5);
    REQUIRE(tw[3].pc == 0x108 && tw[3].time_half_dots == 80);
    REQUIRE(tw[4].pc == 0x109 && tw[4].time_half_dots == 88);
    gbb_test_cpu_snapshot(whole, &sw);
    REQUIRE(sw.pc == 0x40 && sw.sp == 0xfffc && sw.time_half_dots == 136);
    REQUIRE(gbb_peek_ram(whole, 0xfffc) == 0x0a && gbb_peek_ram(whole, 0xfffd) == 0x01);
    r = gbb_run(split, 88, ts, 8);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 88 && r.trace_count == 4);
    r = gbb_run(split, 8, ts + 4, 4);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 8 && r.trace_count == 1);
    r = gbb_run(split, 40, ts + 5, 3);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 40 && r.trace_count == 0);
    gbb_test_cpu_snapshot(split, &ss);
    REQUIRE(memcmp(tw, ts, 5 * sizeof(*tw)) == 0 && memcmp(&sw, &ss, sizeof(sw)) == 0);
    REQUIRE(gbb_peek_ram(split, 0xfffc) == 0x0a && gbb_peek_ram(split, 0xfffd) == 0x01);
    gbb_destroy(whole); gbb_destroy(split);
    return 0;
}

static int interrupt_diagnostic_order(void) {
    /* DIV resets at t=144. TAC selects bit 3 at t=184 while low, so its
     * next falling edge overflows TIMA at t=208; reload is at t=216.
     * VBlank IF is pending when EI;NOP retires at t=208, making reload
     * coincide with the entry's IF acknowledgement phase. */
    const uint8_t p[] = {0x3e,1,0xea,0xff,0xff,0xea,0x0f,0xff,
        0x3e,0xff,0xe0,5,0xaf,0xe0,4,0x3e,5,0xe0,7,0xfb,0x00};
    gbb_instance *whole = make_machine(p, sizeof(p)); REQUIRE(whole != NULL);
    gbb_instance *split = make_machine(p, sizeof(p)); REQUIRE(split != NULL);
    gbb_run_result r = gbb_run(whole, 208, NULL, 0);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 208);
    REQUIRE(gbb_run(split, 80, NULL, 0).consumed_half_dots == 80);
    REQUIRE(gbb_run(split, 128, NULL, 0).consumed_half_dots == 128);
    gbb_trace_record before = {0}, after = {0};
    gbb_test_cpu_snapshot(whole, &before);
    REQUIRE(before.time_half_dots == 208 && before.pc == 0x115 && before.sp == 0xfffe);
    gbb_diagnostic_record ew[16] = {{0}}, es[16] = {{0}};
    r = gbb_run_ex(whole, 39, NULL, 0, ew, 16);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 0 && r.diagnostic_count == 0);
    gbb_test_cpu_snapshot(whole, &after);
    REQUIRE(memcmp(&before, &after, sizeof(before)) == 0 && ew[0].kind == 0);
    r = gbb_run_ex(whole, 40, NULL, 0, ew, 16);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 40 && r.diagnostic_count == 6);
    REQUIRE(ew[0].kind == GBB_DIAGNOSTIC_INSTRUCTION && ew[0].time_half_dots == 208);
    REQUIRE(ew[1].kind == GBB_DIAGNOSTIC_TIMER && ew[1].time_half_dots == 216 && ew[1].address == 0xff05);
    REQUIRE(ew[2].kind == GBB_DIAGNOSTIC_BUS_WRITE && ew[2].time_half_dots == 216 && ew[2].address == 0xff0f && ew[2].value == 0xe4);
    REQUIRE(ew[3].kind == GBB_DIAGNOSTIC_BUS_WRITE && ew[3].time_half_dots == 224 && ew[3].address == 0xfffd && ew[3].value == 0x01);
    REQUIRE(ew[4].kind == GBB_DIAGNOSTIC_BUS_WRITE && ew[4].time_half_dots == 232 && ew[4].address == 0xfffc && ew[4].value == 0x15);
    REQUIRE(ew[5].kind == GBB_DIAGNOSTIC_TIMER && ew[5].time_half_dots == 240 && ew[5].address == 0xff05 && ew[5].value == 1);
    for (size_t i = 1; i < r.diagnostic_count; ++i)
        REQUIRE(ew[i - 1].time_half_dots <= ew[i].time_half_dots);
    gbb_test_cpu_snapshot(whole, &after);
    REQUIRE(after.pc == 0x40 && after.sp == 0xfffc && after.time_half_dots == 248);
    REQUIRE(gbb_peek_ram(whole, 0xfffc) == 0x15 && gbb_peek_ram(whole, 0xfffd) == 0x01);
    r = gbb_run_ex(split, 40, NULL, 0, es, 16);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 40 && r.diagnostic_count == 6);
    REQUIRE(memcmp(ew, es, 6 * sizeof(*ew)) == 0);
    gbb_test_cpu_snapshot(split, &before);
    REQUIRE(memcmp(&before, &after, sizeof(before)) == 0);
    gbb_destroy(whole); gbb_destroy(split);
    return 0;
}

static int interrupt_priority(void) {
    const uint8_t p[] = {0x3e,3,0xea,0xff,0xff,0xea,0x0f,0xff,0xfb,0x00};
    uint8_t rom[32768]; make_rom(rom, p, sizeof(p));
    const uint8_t handler[] = {0xfa,0x0f,0xff,0xea,0x00,0xc0,0xd9};
    memcpy(rom + 0x40, handler, sizeof(handler));
    gbb_instance *m = NULL; REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    gbb_test_bus_event e[12] = {{0}}; gbb_test_observer_set(m, e, 12);
    gbb_trace_record t[12] = {{0}};
    gbb_run_result r = gbb_run(m, 96, t, 12); REQUIRE(r.consumed_half_dots == 96);
    r = gbb_run(m, 40, t, 12); REQUIRE(r.consumed_half_dots == 40);
    r = gbb_run(m, 64, t, 12); REQUIRE(r.consumed_half_dots == 64);
    REQUIRE(gbb_peek_ram(m, 0xc000) == 0xe2);
    REQUIRE(t[0].pc == 0x40);
    r = gbb_run(m, 32, t, 12); REQUIRE(r.consumed_half_dots == 32);
    r = gbb_run(m, 40, t, 12); REQUIRE(r.consumed_half_dots == 40);
    r = gbb_run(m, 8, t, 12); REQUIRE(r.trace_count == 1 && t[0].pc == 0x48);
    gbb_destroy(m); return 0;
}

static int halt_idle(void) {
    const uint8_t p[] = {0x76,0x04,0x00}; gbb_instance *m = make_machine(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_trace_record t[2] = {{0}}; gbb_run_result r = gbb_run(m, 8, t, 2);
    REQUIRE(r.reason == (gbb_stop_reason)6 && r.consumed_half_dots == 8 && r.trace_count == 1);
    r = gbb_run(m, 16, t, 2); REQUIRE(r.reason == (gbb_stop_reason)6 && r.consumed_half_dots == 16);
    gbb_destroy(m); return 0;
}

static int halt_timer_partition(void) {
    /* TAC bit 5 overflows at t=200 and reloads/raises IF at t=208.
     * HALT starts at t=184, so wake must be sampled before the budget ends. */
    const uint8_t p[] = {0x3e,4,0xea,0xff,0xff,0xaf,0xe0,4,0x3e,0xff,
        0xe0,5,0x3e,6,0xe0,7,0xfb,0x00,0x76};
    uint8_t rom[32768]; make_rom(rom, p, sizeof(p));
    const uint8_t handler[] = {0x3e,0x55,0xea,0x00,0xc0,0x76};
    memcpy(rom + 0x50, handler, sizeof(handler));
    gbb_instance *whole = NULL, *split = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &whole) == GBB_OK);
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &split) == GBB_OK);
    REQUIRE(gbb_load_rom(whole, rom, sizeof(rom)) == GBB_OK);
    REQUIRE(gbb_load_rom(split, rom, sizeof(rom)) == GBB_OK);
    REQUIRE(gbb_run(whole, 184, NULL, 0).consumed_half_dots == 184);
    REQUIRE(gbb_run(split, 184, NULL, 0).consumed_half_dots == 184);
    gbb_trace_record before, after;
    gbb_test_cpu_snapshot(whole, &before);
    gbb_run_result r = gbb_run(whole, 0, NULL, 0);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 0);
    r = gbb_run(whole, 7, NULL, 0);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 0);
    gbb_test_cpu_snapshot(whole, &after); REQUIRE(memcmp(&before, &after, sizeof(before)) == 0);
    gbb_test_bus_event ew[16] = {{0}}, es[16] = {{0}};
    gbb_test_observer_set(whole, ew, 16); gbb_test_observer_set(split, es, 16);
    gbb_trace_record tw[4] = {{0}}, ts[4] = {{0}};
    r = gbb_run(whole, 120, tw, 4);
    REQUIRE(r.reason == GBB_STOP_HALTED_IDLE && r.consumed_half_dots == 120);
    REQUIRE(r.trace_count == 3 && gbb_peek_ram(whole, 0xc000) == 0x55);
    REQUIRE(tw[0].pc == 0x50 && tw[0].time_half_dots == 248);
    r = gbb_run(split, 8, ts, 4);
    REQUIRE(r.reason == GBB_STOP_HALTED_IDLE && r.consumed_half_dots == 8 && r.trace_count == 0);
    r = gbb_run(split, 56, ts, 4);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 56 && r.trace_count == 0);
    r = gbb_run(split, 56, ts, 4);
    REQUIRE(r.reason == GBB_STOP_HALTED_IDLE && r.consumed_half_dots == 56 && r.trace_count == 3);
    REQUIRE(memcmp(tw, ts, 3 * sizeof(*tw)) == 0);
    gbb_test_cpu_snapshot(whole, &before); gbb_test_cpu_snapshot(split, &after);
    REQUIRE(memcmp(&before, &after, sizeof(before)) == 0 && before.time_half_dots == 304);
    REQUIRE(gbb_peek_ram(split, 0xc000) == 0x55);
    REQUIRE(gbb_test_observer_count(whole) == gbb_test_observer_count(split));
    for (size_t i = 0; i < gbb_test_observer_count(whole); ++i) {
        REQUIRE(ew[i].time_half_dots == es[i].time_half_dots && ew[i].address == es[i].address);
        REQUIRE(ew[i].access == es[i].access && ew[i].value == es[i].value);
    }
    gbb_destroy(whole); gbb_destroy(split);
    /* With IME clear, the same timer wake resumes the following instruction
     * without vectoring or consuming the pending interrupt. */
    const uint8_t no_ime[] = {0x3e,4,0xea,0xff,0xff,0xaf,0xe0,4,0x3e,0xff,
        0xe0,5,0x3e,6,0xe0,7,0x00,0x00,0x76,0x3e,0x77,0xea,0x00,0xc0};
    make_rom(rom, no_ime, sizeof(no_ime));
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &whole) == GBB_OK);
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &split) == GBB_OK);
    REQUIRE(gbb_load_rom(whole, rom, sizeof(rom)) == GBB_OK);
    REQUIRE(gbb_load_rom(split, rom, sizeof(rom)) == GBB_OK);
    REQUIRE(gbb_run(whole, 184, NULL, 0).consumed_half_dots == 184);
    REQUIRE(gbb_run(split, 184, NULL, 0).consumed_half_dots == 184);
    r = gbb_run(whole, 72, tw, 4);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 72 && r.trace_count == 2);
    r = gbb_run(split, 24, ts, 4);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 24 && r.trace_count == 0);
    r = gbb_run(split, 48, ts, 4);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 48 && r.trace_count == 2);
    REQUIRE(memcmp(tw, ts, 2 * sizeof(*tw)) == 0);
    gbb_test_cpu_snapshot(whole, &before); gbb_test_cpu_snapshot(split, &after);
    REQUIRE(memcmp(&before, &after, sizeof(before)) == 0 && before.time_half_dots == 256);
    REQUIRE(gbb_peek_ram(whole, 0xc000) == 0x77 && gbb_peek_ram(split, 0xc000) == 0x77);
    gbb_destroy(whole); gbb_destroy(split); return 0;
}

static int halt_bug(void) {
    const uint8_t p[] = {0x3e,1,0xea,0xff,0xff,0xea,0x0f,0xff,0x76,0x04,0x00};
    gbb_instance *m = make_machine(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_trace_record t[8] = {{0}}; gbb_run_result r = gbb_run(m, 88, t, 8); REQUIRE(r.consumed_half_dots == 88);
    r = gbb_run(m, 8, t, 2); REQUIRE(r.consumed_half_dots == 8);
    r = gbb_run(m, 8, t, 2); REQUIRE(r.consumed_half_dots == 8 && t[0].pc == 0x109 && t[0].b == 1);
    gbb_destroy(m);
    const uint8_t immediate_program[] = {0x3e,1,0xea,0xff,0xff,0xea,0x0f,0xff,0x76,0x06,0x99,0x00};
    m = make_machine(immediate_program, sizeof(immediate_program)); REQUIRE(m != NULL);
    r = gbb_run(m, 88, t, 8); REQUIRE(r.consumed_half_dots == 88);
    r = gbb_run(m, 16, t, 2); REQUIRE(r.consumed_half_dots == 16);
    r = gbb_run(m, 8, t, 2); REQUIRE(r.trace_count == 1 && t[0].pc == 0x10a && t[0].b == 0x06);
    gbb_destroy(m); return 0;
}

static int stop_wait(void) {
    const uint8_t p[] = {0x10,0x00,0x04}; gbb_instance *m = make_machine(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_trace_record t[2] = {{0}}; gbb_run_result r = gbb_run(m, 8, t, 2);
    REQUIRE(r.reason == (gbb_stop_reason)7 && r.consumed_half_dots == 8 && t[0].pc == 0x100);
    r = gbb_run(m, 64, t, 2); REQUIRE(r.reason == GBB_STOP_STOPPED && r.consumed_half_dots == 64 && r.trace_count == 0);
    gbb_destroy(m); return 0;
}

static int reset_profile(void) {
    const uint8_t p[] = {0x00}; gbb_instance *m = make_machine(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_trace_record t[1] = {{0}}; gbb_run_result r = gbb_run(m, 8, t, 1); REQUIRE(r.consumed_half_dots == 8);
    REQUIRE(gbb_reset(m) == GBB_OK);
    r = gbb_run(m, 8, t, 1);
    REQUIRE(r.consumed_half_dots == 8 && t[0].time_half_dots == 0 && t[0].pc == 0x100 && t[0].sp == 0xfffe && t[0].a == 1 && t[0].f == 0xb0);
    gbb_destroy(m); return 0;
}

static int expect_header_profile(uint8_t checksum, uint8_t expected_f, uint16_t branch_pc) {
    uint8_t rom[32768];
    const uint8_t program[] = {0x38, 0x02, 0x00, 0x00, 0x00}; /* JR C,+2; checksum controls the first branch. */
    make_rom(rom, program, sizeof(program));
    if (checksum == 0) {
        /* With this zero-filled header, title byte E7 balances the 25 checksum steps to exactly zero. */
        rom[0x134] = 0xe7;
        rom[0x14d] = 0;
    }
    REQUIRE(rom[0x14d] == checksum);

    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    gbb_trace_record trace[4] = {{0}};
    gbb_run_result r = gbb_run(m, 32, trace, 4);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 32);
    REQUIRE(r.trace_count >= 2 && trace[0].pc == 0x0100 && trace[0].f == expected_f);
    REQUIRE(trace[1].pc == branch_pc);

    REQUIRE(gbb_reset(m) == GBB_OK);
    r = gbb_run(m, 32, trace, 4);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 32);
    REQUIRE(r.trace_count >= 2 && trace[0].time_half_dots == 0 && trace[0].pc == 0x0100);
    REQUIRE(trace[0].f == expected_f && trace[1].pc == branch_pc);

    gbb_trace_record before = {0}, after = {0};
    gbb_test_cpu_snapshot(m, &before);
    uint8_t invalid_replacement[sizeof(rom)];
    memcpy(invalid_replacement, rom, sizeof(rom));
    invalid_replacement[0x14d] ^= 1u;
    REQUIRE(gbb_load_rom(m, invalid_replacement, sizeof(invalid_replacement)) == GBB_INVALID_ROM);
    gbb_test_cpu_snapshot(m, &after);
    REQUIRE(memcmp(&before, &after, sizeof(before)) == 0);

    REQUIRE(gbb_reset(m) == GBB_OK);
    r = gbb_run(m, 32, trace, 4);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 32);
    REQUIRE(r.trace_count >= 2 && trace[0].f == expected_f && trace[1].pc == branch_pc);
    gbb_destroy(m);
    return 0;
}

static int reset_header_flags(void) {
    REQUIRE(expect_header_profile(0x00, 0x80, 0x0102) == 0);
    REQUIRE(expect_header_profile(0xe7, 0xb0, 0x0104) == 0);
    return 0;
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
    if (strcmp(argv[1], "interrupt_ei_chain") == 0) return interrupt_ei_chain();
    if (strcmp(argv[1], "interrupt_diagnostic_order") == 0) return interrupt_diagnostic_order();
    if (strcmp(argv[1], "interrupt_priority") == 0) return interrupt_priority();
    if (strcmp(argv[1], "halt_idle") == 0) return halt_idle();
    if (strcmp(argv[1], "halt_timer_partition") == 0) return halt_timer_partition();
    if (strcmp(argv[1], "halt_bug") == 0) return halt_bug();
    if (strcmp(argv[1], "stop_wait") == 0) return stop_wait();
    if (strcmp(argv[1], "reset_profile") == 0) return reset_profile();
    if (strcmp(argv[1], "reset_header_flags") == 0) return reset_header_flags();
    if (strcmp(argv[1], "reset_lockup") == 0) return reset_lockup();
    return 2;
}
