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

static size_t find_event(const gbb_test_bus_event *events, size_t count,
                         uint16_t address, uint8_t access, size_t start) {
    for (size_t i = start; i < count; ++i)
        if (events[i].address == address && events[i].access == access) return i;
    return count;
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
            0x21,0x00,0xC0, 0x7E,       /* LD A,(C000), long enough for the edge */
            0xF0,0x05, 0xEA,0x00,0xC0, /* record TIMA via WRAM */
            0xF0,0x0F, 0xEA,0x01,0xC0  /* record IF via WRAM */
        };
        gbb_instance *m = load_program(program, sizeof(program));
        REQUIRE(m != NULL);
        gbb_test_bus_event events[32] = {{0}};
        gbb_test_observer_set(m, events, 32);
        gbb_trace_record trace[16] = {{0}};
        gbb_run_result r = gbb_run(m, 400, trace, 16);
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 400);
        size_t count = gbb_test_observer_count(m);
        size_t zero = find_event(events, count, 0xFF05, 1, 0);
        size_t reload = zero < count ? find_event(events, count, 0xFF05, 1, zero + 1) : count;
        size_t interrupt = find_event(events, count, 0xFF0F, 1, 0);
        REQUIRE(zero < count && events[zero].value == 0x00);
        REQUIRE(reload < count && events[reload].value == 0x42);
        REQUIRE(interrupt < count && (events[interrupt].value & 0x04u) != 0);
        REQUIRE(events[reload].time_half_dots == events[zero].time_half_dots + 8u);
        REQUIRE(events[interrupt].time_half_dots >= events[reload].time_half_dots);
        REQUIRE(gbb_peek_ram(m, 0xC000) == 0x42);
        REQUIRE((gbb_peek_ram(m, 0xC001) & 0x04u) != 0);
        gbb_destroy(m);
        PASS("timer_guest_overflow");
    }
    if (strcmp(argv[1], "mid_instruction") == 0) {
        /* The divider edge at 32 half-dots occurs during this 48-half-dot guest instruction. */
        const uint8_t program[] = {
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
        gbb_trace_record trace[16] = {{0}};
        gbb_run_result r = gbb_run(m, 200, trace, 16);
        REQUIRE(r.consumed_half_dots == 200);
        size_t count = gbb_test_observer_count(m);
        size_t overflow = find_event(events, count, 0xFF05, 1, 0);
        size_t read_tima = overflow < count ? find_event(events, count, 0xFF05, 1, overflow + 1) : count;
        REQUIRE(overflow < count && events[overflow].value == 0x00);
        REQUIRE(read_tima < count && events[read_tima].value == 0xFF);
        REQUIRE(gbb_peek_ram(m, 0xC002) == 0xFF);
        gbb_destroy(m);
        PASS("timer_mid_instruction");
    }
    return 2;
}
