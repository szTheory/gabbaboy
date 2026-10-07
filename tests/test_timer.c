#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { printf("not ok 1 - %s\n", #x); fflush(stdout); fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)
#define PASS(name) do { printf("ok 1 - %s\n", name); return 0; } while (0)

typedef struct {
    uint64_t time_half_dots;
    uint16_t address;
    uint8_t access;
    uint8_t value;
} gbb_test_bus_event;

extern void gbb_test_observer_set(gbb_instance *, gbb_test_bus_event *, size_t);
extern size_t gbb_test_observer_count(const gbb_instance *);

static void fix_checksum(uint8_t *rom) {
    uint8_t sum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14D] = sum;
}

static gbb_instance *load_program(const uint8_t *program, size_t length) {
    uint8_t *rom = calloc(1, 32768);
    if (rom == NULL) return NULL;
    memcpy(rom + 0x100, program, length);
    fix_checksum(rom);
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, 32768) != GBB_OK) {
        gbb_destroy(machine);
        machine = NULL;
    }
    free(rom);
    return machine;
}

static gbb_instance *load_long_program(const uint8_t *program, size_t length, size_t prefix) {
    if (prefix > length || prefix + 3u > 0x50u) return NULL;
    uint8_t *rom = calloc(1, 32768);
    if (rom == NULL) return NULL;
    memcpy(rom + 0x100, program, prefix);
    rom[0x100 + prefix] = 0xC3; rom[0x101 + prefix] = 0x50; rom[0x102 + prefix] = 0x01;
    memcpy(rom + 0x150, program + prefix, length - prefix);
    fix_checksum(rom);
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, 32768) != GBB_OK) {
        gbb_destroy(machine); machine = NULL;
    }
    free(rom);
    return machine;
}

static size_t find_event(const gbb_test_bus_event *events, size_t count,
                         uint16_t address, uint8_t access, size_t start) {
    for (size_t i = start; i < count; ++i)
        if (events[i].address == address && events[i].access == access) return i;
    return count;
}

static int timer_selectors(void) {
    static const uint64_t periods[4] = {2048, 32, 128, 512};
    for (unsigned selector = 0; selector < 4; ++selector) {
        uint8_t program[] = {0x3E,0xFF,0xE0,0x05, 0x3E,0xFF,0xE0,0x06,
                             0x3E,0x00,0xE0,0x04, 0x3E,0x04,0xE0,0x07,0x18,0xFE};
        program[13] = (uint8_t)(0x04u | selector);
        gbb_instance *m = load_program(program, sizeof(program)); REQUIRE(m != NULL);
        gbb_test_bus_event events[32] = {{0}}; gbb_test_observer_set(m, events, 32);
        gbb_run_result r = gbb_run(m, periods[selector] * 4u + 256u, NULL, 0);
        REQUIRE(r.reason == GBB_STOP_BUDGET);
        size_t count = gbb_test_observer_count(m), n = 0;
        uint64_t times[4] = {0};
        for (size_t i = 0; i < count && n < 4; ++i)
            if (events[i].address == 0xFF05 && events[i].access == 3 && events[i].value == 0x00) times[n++] = events[i].time_half_dots;
        REQUIRE(n >= 3);
        REQUIRE(times[1] - times[0] == periods[selector]);
        REQUIRE(times[2] - times[1] == periods[selector]);
        gbb_destroy(m);
    }
    return 0;
}

static int timer_div_write(void) {
    const uint8_t p[] = {0x3E,0xFF,0xE0,0x05, 0x3E,0x42,0xE0,0x06,
                         0x3E,0x04,0xE0,0x07, 0x3E,0x00,0xE0,0x04,
                         0xF0,0x05,0xEA,0x00,0xC0, 0xF0,0x0F,0xEA,0x01,0xC0};
    gbb_instance *m = load_program(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_test_bus_event e[16] = {{0}}; gbb_test_observer_set(m, e, 16);
    gbb_trace_record t[32] = {{0}}; gbb_run_result r = gbb_run(m, 320, t, 32);
    REQUIRE(r.reason == GBB_STOP_BUDGET);
    size_t n = gbb_test_observer_count(m), div = find_event(e,n,0xFF04,2,0), over = find_event(e,n,0xFF05,3,0);
    REQUIRE(div < n && over < n && e[div].time_half_dots == e[over].time_half_dots);
    REQUIRE((gbb_peek_ram(m,0xC000) == 0x42) && (gbb_peek_ram(m,0xC001) & 4u));
    gbb_destroy(m); return 0;
}

static int timer_tac_write(void) {
    const uint8_t p[] = {0x3E,0xFF,0xE0,0x05, 0x3E,0x42,0xE0,0x06,
                         0x3E,0x04,0xE0,0x07, 0x3E,0x00,0xE0,0x07,
                         0xF0,0x05,0xEA,0x00,0xC0, 0xF0,0x0F,0xEA,0x01,0xC0};
    gbb_instance *m = load_program(p, sizeof(p)); REQUIRE(m != NULL);
    gbb_test_bus_event e[16] = {{0}}; gbb_test_observer_set(m, e, 16);
    gbb_trace_record t[32] = {{0}}; gbb_run_result r = gbb_run(m, 320, t, 32);
    REQUIRE(r.reason == GBB_STOP_BUDGET);
    size_t n = gbb_test_observer_count(m), tac = find_event(e,n,0xFF07,2,3), over = find_event(e,n,0xFF05,3,0);
    REQUIRE(tac < n && over < n && e[tac].time_half_dots == e[over].time_half_dots);
    REQUIRE((gbb_peek_ram(m,0xC000) == 0x42) && (gbb_peek_ram(m,0xC001) & 4u));
    gbb_destroy(m); return 0;
}

static int timer_write_collision(int tma_write) {
    if (tma_write) {
        /* Four bootless guest cases use independently qualified Mooneye outcomes at revision 31510e12eea6286d36eea060a6adde755e1067aa. */
        uint8_t p[256]; size_t used = 0;
        const uint8_t setup[] = {0xF3,0xAF,0x06,0xFE,0x26,0x7F,0xE0,0xFF,0xE0,0x0F,0xE0,0x04,
                                 0x78,0xE0,0x05,0x78,0xE0,0x06,0x3E,0x06,0xE0,0x07};
        memcpy(p, setup, sizeof(setup)); used = sizeof(setup);
        const uint8_t result_regs[] = {0x57,0x5F,0x4F,0x6F};
        for (unsigned variant = 0; variant < 4; ++variant) {
            if (variant == 0) {
                const uint8_t prep[] = {0x78,0xE0,0x04,0x78,0xE0,0x05,0x78,0xE0,0x04};
                memcpy(p + used, prep, sizeof(prep)); used += sizeof(prep);
            } else {
                const uint8_t prep[] = {0x78,0xE0,0x05,0x78,0xE0,0x06,0x78,0xE0,0x04,
                                        0x78,0xE0,0x05,0x78,0xE0,0x04};
                memcpy(p + used, prep, sizeof(prep)); used += sizeof(prep);
            }
            p[used++] = 0x7C; /* LD A,H => 7F */
            /* Align the translated register accesses to the named write phases. */
            static const unsigned delay_nops[4] = {13,13,15,16};
            for (unsigned i = 0; i < delay_nops[variant]; ++i) p[used++] = 0x00;
            p[used++] = 0xE0; p[used++] = 0x06; /* TMA write */
            p[used++] = 0xF0; p[used++] = 0x05; /* TIMA read */
            p[used++] = result_regs[variant];
        }
        const uint8_t store[] = {0x7A,0xEA,0x00,0xC0,0x7B,0xEA,0x01,0xC0,
                                 0x79,0xEA,0x02,0xC0,0x7D,0xEA,0x03,0xC0};
        memcpy(p + used, store, sizeof(store)); used += sizeof(store);
        gbb_instance *m = load_long_program(p, used, 0); REQUIRE(m != NULL);
        gbb_trace_record trace[800] = {{0}};
        gbb_run_result r = gbb_run(m, 6000, trace, 800);
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 6000);
        REQUIRE(gbb_peek_ram(m,0xC000) == 0x7F && gbb_peek_ram(m,0xC001) == 0x7F);
        REQUIRE(gbb_peek_ram(m,0xC002) == 0xFE && gbb_peek_ram(m,0xC003) == 0xFE);
        gbb_destroy(m); return 0;
    }
    uint8_t p[256] = {0x3E,0xFF,0xE0,0x05, 0x3E,0x42,0xE0,0x06,
                      0x3E,0x04,0xE0,0x07};
    size_t used = 12;
    p[used++] = 0x3E;
    p[used++] = tma_write ? 0x7F : 0x99; /* TMA update supplies reload; TIMA write cancels pending reload. */
    size_t nops = tma_write ? 42u : 41u;
    for (size_t i = 0; i < nops; ++i) p[used++] = 0x00;
    p[used++] = 0xE0; p[used++] = tma_write ? 0x06 : 0x05;
    p[used++] = 0xF0; p[used++] = 0x05; p[used++] = 0xEA; p[used++] = 0x00; p[used++] = 0xC0;
    p[used++] = 0xF0; p[used++] = 0x0F; p[used++] = 0xEA; p[used++] = 0x01; p[used++] = 0xC0;
    gbb_instance *m = load_long_program(p, used, 12); REQUIRE(m != NULL);
    gbb_test_bus_event e[16] = {{0}}; gbb_test_observer_set(m, e, 16);
    gbb_trace_record t[128] = {{0}}; gbb_run_result r = gbb_run(m, 900, t, 128);
    REQUIRE(r.reason == GBB_STOP_BUDGET);
    size_t count = gbb_test_observer_count(m), overflow = find_event(e,count,0xFF05,3,0);
    size_t reload = overflow < count ? find_event(e,count,0xFF05,3,overflow+1) : count;
    REQUIRE(overflow < count);
    REQUIRE(reload == count);
    REQUIRE(gbb_peek_ram(m,0xC000) == 0x99 && (gbb_peek_ram(m,0xC001) & 4u) == 0);
    gbb_destroy(m); return 0;
}

static int timer_tima_reload_cycle_write(void) {
    uint8_t p[128] = {0x3E,0xFF,0xE0,0x05, 0x3E,0x42,0xE0,0x06,
                      0x3E,0x04,0xE0,0x07};
    size_t used = 12;
    p[used++] = 0x3E; p[used++] = 0x99;
    for (unsigned i = 0; i < 42; ++i) p[used++] = 0x00;
    p[used++] = 0xE0; p[used++] = 0x05; /* same timestamp as the reload deadline */
    const uint8_t tail[] = {0xF0,0x05,0xEA,0x00,0xC0,0xF0,0x0F,0xEA,0x01,0xC0};
    memcpy(p + used,tail,sizeof(tail)); used += sizeof(tail);
    gbb_instance *m = load_long_program(p,used,12); REQUIRE(m != NULL);
    gbb_test_bus_event e[16] = {{0}}; gbb_test_observer_set(m,e,16);
    gbb_run_result r = gbb_run(m,900,NULL,0); REQUIRE(r.reason == GBB_STOP_BUDGET);
    size_t count = gbb_test_observer_count(m), overflow = find_event(e,count,0xFF05,3,0);
    size_t reload = overflow < count ? find_event(e,count,0xFF05,3,overflow+1) : count;
    REQUIRE(overflow < count && reload < count && e[reload].time_half_dots == e[overflow].time_half_dots + 8u);
    REQUIRE(gbb_peek_ram(m,0xC000) == 0x42 && (gbb_peek_ram(m,0xC001) & 4u));
    gbb_destroy(m); return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    printf("1..1\n");
    if (strcmp(argv[1], "guest_overflow") == 0) {
        /* Configure overflow to occur on a falling edge while a multi-cycle guest instruction runs. */
        const uint8_t program[] = {
            0x3E,0x42, 0xE0,0x06,       /* TMA=42 */
            0x3E,0xFF, 0xE0,0x05,       /* TIMA=FF */
            0x3E,0x05, 0xE0,0x07,       /* TAC: enabled, divider bit 3 */
            0x00,                       /* place the overflow between setup and timed reads */
            0xF0,0x05, 0xEA,0x00,0xC0, /* record post-reload TIMA via WRAM */
            0xF0,0x05, 0xEA,0x01,0xC0, /* record reloaded TIMA via WRAM */
            0xF0,0x0F, 0xEA,0x02,0xC0  /* record timer IF via WRAM */
        };
        gbb_instance *m = load_program(program, sizeof(program));
        REQUIRE(m != NULL);
        gbb_test_bus_event events[32] = {{0}};
        gbb_test_observer_set(m, events, 32);
        gbb_trace_record trace[80] = {{0}};
        gbb_run_result r = gbb_run(m, 400, trace, 80);
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 400);
        size_t count = gbb_test_observer_count(m);
        size_t zero = find_event(events, count, 0xFF05, 3, 0);
        size_t reload = zero < count ? find_event(events, count, 0xFF05, 3, zero + 1) : count;
        size_t interrupt = find_event(events, count, 0xFF0F, 3, 0);
        REQUIRE(zero < count && events[zero].value == 0x00);
        REQUIRE(reload < count && events[reload].value == 0x42);
        REQUIRE(interrupt < count && (events[interrupt].value & 0x04u) != 0);
        REQUIRE(events[reload].time_half_dots == events[zero].time_half_dots + 8u);
        REQUIRE(events[interrupt].time_half_dots >= events[reload].time_half_dots);
        REQUIRE(gbb_peek_ram(m, 0xC000) == 0x42);
        REQUIRE(gbb_peek_ram(m, 0xC001) == 0x44);
        REQUIRE((gbb_peek_ram(m, 0xC002) & 0x04u) != 0);
        gbb_destroy(m);
        PASS("timer_guest_overflow");
    }
    if (strcmp(argv[1], "mid_instruction") == 0) {
        /* Overflow and reload fall between the start and later bus phases of LD (a16),SP. */
        const uint8_t program[] = {
            0x3E,0x65, 0xE0,0x06,       /* TMA=65 */
            0x3E,0xFF, 0xE0,0x05,       /* TIMA=FF */
            0x3E,0x05, 0xE0,0x07,       /* TAC enabled, bit 3 */
            0x08,0x00,0xC0,              /* LD (C000),SP: timed bus writes around internal phases */
            0xF0,0x05, 0xEA,0x02,0xC0,
            0xF0,0x0F, 0xEA,0x03,0xC0
        };
        gbb_instance *m = load_program(program, sizeof(program));
        REQUIRE(m != NULL);
        gbb_test_bus_event events[24] = {{0}};
        gbb_test_observer_set(m, events, 24);
        gbb_trace_record trace[80] = {{0}};
        gbb_run_result r = gbb_run(m, 240, trace, 80);
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 240);
        size_t count = gbb_test_observer_count(m);
        size_t overflow = find_event(events, count, 0xFF05, 3, 0);
        size_t reload = overflow < count ? find_event(events, count, 0xFF05, 3, overflow + 1) : count;
        size_t write_inside = find_event(events, count, 0xC000, 2, 0);
        REQUIRE(overflow < count && reload < count && events[reload].time_half_dots == events[overflow].time_half_dots + 8u);
        REQUIRE(write_inside < count && events[write_inside].time_half_dots >= events[overflow].time_half_dots + 8u);
        REQUIRE(gbb_peek_ram(m, 0xC002) == 0x66);
        gbb_destroy(m);
        PASS("timer_mid_instruction");
    }
    if (strcmp(argv[1], "selectors") == 0) { REQUIRE(timer_selectors() == 0); PASS("timer_selectors"); }
    if (strcmp(argv[1], "div_write") == 0) { REQUIRE(timer_div_write() == 0); PASS("timer_div_write"); }
    if (strcmp(argv[1], "tac_write") == 0) { REQUIRE(timer_tac_write() == 0); PASS("timer_tac_write"); }
    if (strcmp(argv[1], "tima_collision") == 0) { REQUIRE(timer_write_collision(0) == 0); REQUIRE(timer_tima_reload_cycle_write() == 0); PASS("timer_tima_collision"); }
    if (strcmp(argv[1], "tma_collision") == 0) { REQUIRE(timer_write_collision(1) == 0); PASS("timer_tma_collision"); }
    return 2;
}
